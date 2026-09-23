-- Trigger automático para crear el perfil de afiliado al crear un usuario en auth.users.
-- Pégalo en Supabase > SQL Editor > New query.

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.afiliados (
    id,
    nombre,
    apellido,
    tipo_documento,
    cedula,
    email,
    fecha_nacimiento,
    residencia,
    estado,
    municipio,
    pais,
    areas
  )
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'nombre', ''),
    coalesce(new.raw_user_meta_data->>'apellido', ''),
    coalesce(new.raw_user_meta_data->>'tipo_documento', 'V'),
    coalesce(new.raw_user_meta_data->>'cedula', ''),
    new.email,
    coalesce((new.raw_user_meta_data->>'fecha_nacimiento')::date, current_date),
    coalesce(new.raw_user_meta_data->>'residencia', 'venezuela'),
    new.raw_user_meta_data->>'estado',
    new.raw_user_meta_data->>'municipio',
    coalesce(new.raw_user_meta_data->>'pais', 'Venezuela'),
    coalesce((new.raw_user_meta_data->'areas')::text[], '{}')
  )
  on conflict (id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute procedure public.handle_new_user();
