-- Esquema de perfiles de afiliados para Supabase.
-- Ejecuta este archivo completo en Supabase > SQL Editor > New query.

create table if not exists public.afiliados (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null,
  apellido text not null,
  tipo_documento text not null,
  cedula text not null unique,
  email text not null unique,
  fecha_nacimiento date not null,
  residencia text not null,
  estado text,
  municipio text,
  pais text,
  areas text[] not null default '{}',
  created_at timestamptz not null default now()
);

alter table public.afiliados enable row level security;

-- Elimina las políticas anteriores con estos nombres para que el script
-- pueda ejecutarse de nuevo sin errores de "policy already exists".
drop policy if exists "Cada afiliado puede crear su perfil" on public.afiliados;
drop policy if exists "Cada afiliado puede consultar su perfil" on public.afiliados;
drop policy if exists "Cada afiliado puede actualizar su perfil" on public.afiliados;

create policy "Cada afiliado puede crear su perfil"
on public.afiliados
for insert
to authenticated
with check (auth.uid() = id);

create policy "Cada afiliado puede consultar su perfil"
on public.afiliados
for select
to authenticated
using (auth.uid() = id);

create policy "Cada afiliado puede actualizar su perfil"
on public.afiliados
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

-- Permisos explícitos para el cliente Supabase con sesión iniciada.
grant usage on schema public to authenticated;
grant select, insert, update on table public.afiliados to authenticated;
