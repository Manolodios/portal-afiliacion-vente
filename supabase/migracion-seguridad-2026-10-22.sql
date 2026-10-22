-- Endurecimiento de seguridad · 22 de octubre de 2026
--
-- Corrige los hallazgos de la auditoría:
--   1. Revocar una credencial era inútil: el propio afiliado podía
--      reactivarla con crear_mi_credencial() o con un UPDATE directo.
--   2. El afiliado podía escribir su propia fila de credenciales_qr.
--   6. El "admin" de credenciales y notificaciones se decidía por un
--      correo editable en afiliados, no por app_metadata.role.
--   7. anon/authenticated tenían ALL sobre las tablas (incluido TRUNCATE).
--
-- No cambia nada visible para el usuario: el alta, el panel y el QR
-- siguen funcionando igual.

begin;

-- ---------------------------------------------------------------------------
-- 1 y 2. credenciales_qr: el afiliado solo LEE. Escribe la función.
-- ---------------------------------------------------------------------------
-- Antes esta política era FOR ALL: el dueño podía hacer INSERT, UPDATE y
-- DELETE sobre su fila. Con un UPDATE se deshacía una revocación.
drop policy if exists cred_own on public.credenciales_qr;
create policy cred_own on public.credenciales_qr
  for select to authenticated
  using (afiliado_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 6. El administrador se decide por app_metadata.role, igual que en
--    afiliados_select_admin, get_all_afiliados y borrar_fotos_afiliado.
--    app_metadata solo lo puede escribir el servidor (service_role).
-- ---------------------------------------------------------------------------
drop policy if exists cred_admin_all on public.credenciales_qr;
create policy cred_admin_all on public.credenciales_qr
  for all to authenticated
  using (((auth.jwt() -> 'app_metadata'::text) ->> 'role'::text) = 'admin'::text)
  with check (((auth.jwt() -> 'app_metadata'::text) ->> 'role'::text) = 'admin'::text);

drop policy if exists notif_admin_all on public.notificaciones;
create policy notif_admin_all on public.notificaciones
  for all to authenticated
  using (((auth.jwt() -> 'app_metadata'::text) ->> 'role'::text) = 'admin'::text)
  with check (((auth.jwt() -> 'app_metadata'::text) ->> 'role'::text) = 'admin'::text);

-- ---------------------------------------------------------------------------
-- 1. crear_mi_credencial() ya no puede resucitar una credencial revocada.
--    Solo el administrador puede levantarla (UPDATE en la tabla).
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

    -- Una credencial revocada no se regenera sola. Sin esto bastaba con
    -- llamar a esta función para deshacer la revocación.
    if exists (select 1 from public.credenciales_qr
               where afiliado_id = mi_id and revocada) then
        return jsonb_build_object('ok', false, 'error', 'Credencial revocada');
    end if;

    v_codigo := public.gen_codigo_credencial();

    -- Mismo cálculo que codigoDesdeUUID() del portal.
    v_tarjeta := 'VV-' ||
        lpad(((('x' || substr(replace(mi_id::text,'-',''),1,4))::bit(16)::int % 10000))::text,4,'0') || '-' ||
        lpad(((('x' || substr(replace(mi_id::text,'-',''),5,4))::bit(16)::int % 10000))::text,4,'0');

    v_hash := encode(sha256((mi_id || '|' || v_codigo || '|' || extract(epoch from now())::text)::bytea), 'hex');

    insert into public.credenciales_qr (afiliado_id, codigo, codigo_tarjeta, payload_hash)
    values (mi_id, v_codigo, v_tarjeta, v_hash)
    on conflict (afiliado_id) do update set
        codigo         = excluded.codigo,
        codigo_tarjeta = excluded.codigo_tarjeta,
        payload_hash   = excluded.payload_hash,
        actualizada_en = now()
        -- `revocada` NO se toca a propósito.
    returning * into v_row;

    return jsonb_build_object('ok', true, 'credencial', jsonb_build_object(
        'id', v_row.id,
        'codigo', v_row.codigo,
        'codigo_tarjeta', v_row.codigo_tarjeta,
        'expira_en', v_row.expira_en,
        'url_verificacion',
          'https://manolodios.github.io/portal-afiliacion-vente/verify.html?c=' || v_row.codigo_tarjeta
    ));
end;
$function$;

-- ---------------------------------------------------------------------------
-- 6. El correo y la cédula son la identidad de la ficha: un afiliado no
--    puede cambiarlos. El administrador y el SQL directo sí.
--    (El formulario de perfil nunca envía estas dos columnas; el alta las
--    envía con su valor actual, así que el trigger no la estorba.)
-- ---------------------------------------------------------------------------
create or replace function public.proteger_identidad()
 returns trigger
 language plpgsql
 set search_path to ''
as $function$
declare
    v_jwt jsonb := auth.jwt();
begin
    if new.email is not distinct from old.email
       and new.cedula is not distinct from old.cedula then
        return new;
    end if;

    -- Sin JWT (SQL directo / panel de Supabase) o service_role: se permite.
    if v_jwt is null or (v_jwt ->> 'role') = 'service_role' then
        return new;
    end if;

    -- El administrador puede corregir la identidad.
    if (v_jwt -> 'app_metadata' ->> 'role') = 'admin' then
        return new;
    end if;

    raise exception 'El correo y la cedula no se pueden cambiar desde la cuenta.'
        using errcode = '42501';
end;
$function$;

drop trigger if exists trg_proteger_identidad on public.afiliados;
create trigger trg_proteger_identidad
  before update on public.afiliados
  for each row execute function public.proteger_identidad();

-- ---------------------------------------------------------------------------
-- 7. Permisos mínimos.
--    anon solo necesita leer parroquias (para el buscador del alta).
--    authenticated no necesita TRUNCATE, TRIGGER ni REFERENCES.
-- ---------------------------------------------------------------------------
revoke all on public.afiliados          from anon;
revoke all on public.credenciales_qr    from anon;
revoke all on public.notificaciones     from anon;
revoke all on public.push_subscriptions from anon;
revoke all on public.parroquias         from anon;
grant select on public.parroquias to anon;

revoke truncate, trigger, references on public.afiliados          from authenticated;
revoke truncate, trigger, references on public.credenciales_qr    from authenticated;
revoke truncate, trigger, references on public.notificaciones     from authenticated;
revoke truncate, trigger, references on public.push_subscriptions from authenticated;
revoke truncate, trigger, references on public.parroquias         from authenticated;

-- parroquias es un catálogo: solo lectura desde la aplicación.
revoke insert, update, delete on public.parroquias from authenticated;

commit;
