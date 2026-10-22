-- Verificación por código largo + límite de altas · 22 de octubre de 2026
--
-- Cierra el hallazgo 3 (la verificación pública se podía enumerar con el
-- número de tarjeta: 10^8 combinaciones) y suaviza el 5 (el tope global de
-- 10 altas por hora permitía bloquear el registro de todo el mundo).
--
-- El QR pasa a llevar el código interno de 8 caracteres (32^8 combinaciones).
-- El número de tarjeta se sigue mostrando en la credencial como identificador,
-- pero ya no sirve como llave pública.

begin;

-- ---------------------------------------------------------------------------
-- 3. Solo se verifica con el código interno.
-- ---------------------------------------------------------------------------
create or replace function public.verificar_credencial_codigo(p_codigo text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
    v_row public.credenciales_qr;
    v_afiliado public.afiliados;
begin
    select * into v_row
      from public.credenciales_qr
     where codigo = upper(btrim(p_codigo))
     limit 1;

    if not found then
        return jsonb_build_object('valida', false, 'error', 'Código no encontrado');
    end if;
    if v_row.revocada then
        return jsonb_build_object('valida', false, 'error', 'Credencial revocada');
    end if;
    if v_row.expira_en is not null and v_row.expira_en < now() then
        return jsonb_build_object('valida', false, 'error', 'Credencial expirada');
    end if;

    select a.* into v_afiliado from public.afiliados a where a.id = v_row.afiliado_id;
    if not found then
        return jsonb_build_object('valida', false, 'error', 'Afiliado no encontrado');
    end if;

    return jsonb_build_object(
        'valida', true,
        'codigo', v_row.codigo,
        'codigo_tarjeta', v_row.codigo_tarjeta,
        'afiliado', jsonb_build_object(
            'nombre_completo', trim(coalesce(v_afiliado.nombre,'') || ' ' || coalesce(v_afiliado.apellido,'')),
            'estado', v_afiliado.estado,
            'municipio', v_afiliado.municipio,
            'parroquia', v_afiliado.parroquia,
            'areas', v_afiliado.areas,
            'foto', v_afiliado.foto,
            'color_acentu', v_afiliado.color_acentu,
            'fecha_afiliacion', v_afiliado.created_at
        )
    );
end;
$function$;

-- ---------------------------------------------------------------------------
-- El código de verificación es estable: si la credencial ya existe, no se
-- regenera. Así un QR ya compartido o impreso sigue funcionando.
-- ---------------------------------------------------------------------------
create or replace function public.crear_mi_credencial()
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
    mi_id uuid := auth.uid();
    v_codigo text;
    v_tarjeta text;
    v_hash text;
    v_row public.credenciales_qr;
begin
    if not exists (select 1 from public.afiliados
                   where id = mi_id and nombre is not null and cedula is not null) then
        return jsonb_build_object('ok', false, 'error', 'Ficha incompleta');
    end if;

    if exists (select 1 from public.credenciales_qr
               where afiliado_id = mi_id and revocada) then
        return jsonb_build_object('ok', false, 'error', 'Credencial revocada');
    end if;

    v_codigo := public.gen_codigo_credencial();

    v_tarjeta := 'VV-' ||
        lpad(((('x' || substr(replace(mi_id::text,'-',''),1,4))::bit(16)::int % 10000))::text,4,'0') || '-' ||
        lpad(((('x' || substr(replace(mi_id::text,'-',''),5,4))::bit(16)::int % 10000))::text,4,'0');

    v_hash := encode(sha256((mi_id || '|' || v_codigo || '|' || extract(epoch from now())::text)::bytea), 'hex');

    insert into public.credenciales_qr (afiliado_id, codigo, codigo_tarjeta, payload_hash)
    values (mi_id, v_codigo, v_tarjeta, v_hash)
    on conflict (afiliado_id) do update set
        codigo_tarjeta = excluded.codigo_tarjeta,
        actualizada_en = now()
    returning * into v_row;

    return jsonb_build_object('ok', true, 'credencial', jsonb_build_object(
        'id', v_row.id,
        'codigo', v_row.codigo,
        'codigo_tarjeta', v_row.codigo_tarjeta,
        'expira_en', v_row.expira_en,
        'url_verificacion',
          'https://manolodios.github.io/portal-afiliacion-vente/verify.html?c=' || v_row.codigo
    ));
end;
$function$;

create or replace function public.obtener_mi_credencial()
 returns jsonb
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare
    mi_id uuid := auth.uid();
    v_row public.credenciales_qr;
begin
    select * into v_row from public.credenciales_qr
     where afiliado_id = mi_id and not revocada;
    if not found then
        return jsonb_build_object('ok', false, 'error', 'Sin credencial');
    end if;
    return jsonb_build_object('ok', true, 'credencial', jsonb_build_object(
        'id', v_row.id,
        'codigo', v_row.codigo,
        'codigo_tarjeta', v_row.codigo_tarjeta,
        'expira_en', v_row.expira_en,
        'url_verificacion',
          'https://manolodios.github.io/portal-afiliacion-vente/verify.html?c=' || v_row.codigo
    ));
end;
$function$;

-- ---------------------------------------------------------------------------
-- 5. El tope global de 10/hora era un interruptor de apagado: 10 cuentas
--    basura bloqueaban el registro de todos. Se sube a un rango de campaña.
-- ---------------------------------------------------------------------------
update public.config_registros
   set max_por_hora = 50, max_por_dia = 500
 where clave = 'global';

commit;
