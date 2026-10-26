-- El correo vuelve a requerir confirmacion · 26 de octubre de 2026
--
-- El trigger autoconfirm_email marcaba email_confirmed_at en el mismo
-- instante del alta, asi que cualquiera podia registrarse con un correo
-- ajeno. La configuracion de Auth ya tiene mailer_autoconfirm = false:
-- basta con quitar el trigger para que Supabase envie el enlace.
--
-- Requisito: SMTP configurado en el panel (Authentication > SMTP). Con el
-- mailer de prueba de Supabase el envio esta limitado y no sirve para
-- produccion.

drop trigger if exists autoconfirm_email on auth.users;
drop function if exists public.autoconfirm_email();
