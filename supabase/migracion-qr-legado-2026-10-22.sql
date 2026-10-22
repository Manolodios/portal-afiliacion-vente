-- Compatibilidad con los QR del formato anterior · 22 de octubre de 2026
--
-- Los QR generados antes del cambio llevan el numero de tarjeta
-- (VV-XXXX-XXXX). Para que sigan verificando sin reabrir la enumeracion:
--   * solo se aceptan para credenciales creadas antes del corte;
--   * cada intento cuenta en intentos_verificacion;
--   * hay un tope por IP y otro global por hora.
-- El QR nuevo (codigo de 8 caracteres) no pasa por esta ruta ni cuenta.

begin;

create table if not exists public.intentos_verificacion (
  id bigserial primary key,
  clave text not null,
  creada_en timestamptz not null default now()
);

create index if not exists idx_intentos_verificacion_clave
  on public.intentos_verificacion (clave, creada_en desc);

alter table public.intentos_verificacion enable row level security;
revoke all on public.intentos_verificacion from anon, authenticated;
revoke all on sequence public.intentos_verificacion_id_seq from anon, authenticated;

create or replace function public.verificar_credencial_codigo(p_codigo text)
 returns jsonb
 language plpgsql
 security definer
 set search_path to ''
as $function$
declare
    v_txt text := upper(btrim(coalesce(p_codigo, '')));
    v_row public.credenciales_qr;
    v_afiliado public.afiliados;
    v_legacy boolean := false;
    v_ip text;
    v_clave text := 'global';
    v_intentos integer;
    v_global integer;
begin
    if v_txt ~ '^VV-[0-9]{4}-[0-9]{4}$' then
        v_legacy := true;

        begin
            v_ip := (current_setting('request.headers', true)::jsonb ->> 'x-forwarded-for');
        exception when others then
            v_ip := null;
        end;
        v_ip := nullif(btrim(split_part(coalesce(v_ip, ''), ',', 1)), '');

        if v_ip is not null then
            v_clave := md5(v_ip);
            select count(*) into v_intentos
              from public.intentos_verificacion
             where clave = v_clave
               and creada_en > now() - interval '1 hour';
            if v_intentos >= 30 then
                return jsonb_build_object('valida', false,
                    'error', 'Demasiados intentos. Espera unos minutos.');
            end if;
        end if;

        select count(*) into v_global
          from public.intentos_verificacion
         where creada_en > now() - interval '1 hour';
        if v_global >= 600 then
            return jsonb_build_object('valida', false,
                'error', 'Demasiados intentos. Espera unos minutos.');
        end if;

        insert into public.intentos_verificacion (clave) values (v_clave);

        if random() < 0.01 then
            delete from public.intentos_verificacion
             where creada_en < now() - interval '1 day';
        end if;

        -- Solo credenciales anteriores al corte: las nuevas ya no usan
        -- el numero de tarjeta como llave.
        select * into v_row
          from public.credenciales_qr
         where codigo_tarjeta = v_txt
           and creada_en < timestamptz '2026-10-22 16:46:00+00'
         limit 1;

    else
        select * into v_row
          from public.credenciales_qr
         where codigo = v_txt
         limit 1;
    end if;

    if not found then
        return jsonb_build_object('valida', false, 'error', 'Código no encontrado');
    end if;
    if v_row.revocada then
        return jsonb_build_object('valida', false, 'error', 'Credencial revocada');
    end if;
    if v_row.expira_en is not null and v_row.expira_en < now() then
        return jsonb_build_object('valida', false, 'error', 'Credencial expirada');
    end if;

    select a.* into v_afiliado
      from public.afiliados a
     where a.id = v_row.afiliado_id;
    if not found then
        return jsonb_build_object('valida', false, 'error', 'Afiliado no encontrado');
    end if;

    return jsonb_build_object(
        'valida', true,
        'codigo', v_row.codigo,
        'codigo_tarjeta', v_row.codigo_tarjeta,
        'legacy', v_legacy,
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

grant execute on function public.verificar_credencial_codigo(text) to anon, authenticated;

commit;
