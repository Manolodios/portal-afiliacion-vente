import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
// La version anterior importaba deno.land/x/web_push, que ya no existe
// (404): deno.land/x fue retirado. npm:web-push es la misma libreria, servida
// por el gestor de paquetes de Deno, y es la que se usa ahora.
import webpush from "npm:web-push@3.6.7";

// Configuracion VAPID (generada con: npx web-push generate-vapid-keys).
// Las claves van en los secretos de Supabase, nunca en el codigo.
const VAPID_PUBLIC_KEY = Deno.env.get("VAPID_PUBLIC_KEY");
const VAPID_PRIVATE_KEY = Deno.env.get("VAPID_PRIVATE_KEY");
const VAPID_SUBJECT = "mailto:yhojansuarez@gmail.com";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SERVICE_ROLE_KEY")!;

const ADMIN_EMAIL = "yhojansuarez@gmail.com";

// Solo admin puede lanzar notificaciones.
let vapidListo = false;
function usarVapid(): string | null {
  if (vapidListo) return null;
  if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
    return "Faltan los secretos VAPID_PUBLIC_KEY y VAPID_PRIVATE_KEY en Supabase.";
  }
  webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);
  vapidListo = true;
  return null;
}

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

interface NotificationPayload {
  notificacion_id: string;
  titulo: string;
  cuerpo: string;
  // Segmentacion
  estado?: string;
  municipio?: string;
  parroquia?: string;
  area?: string;
  rol?: string;
}

interface PushSubscriptionRow {
  endpoint: string;
  p256dh: string;
  auth: string;
  user_id: string;
}

async function getSegmentedSubscriptions(
  supabase: any,
  seg: { estado?: string; municipio?: string; parroquia?: string; area?: string; rol?: string }
): Promise<PushSubscriptionRow[]> {
  let query = supabase.from("afiliados").select("id");
  if (seg.estado) query = query.eq("estado", seg.estado);
  if (seg.municipio) query = query.eq("municipio", seg.municipio);
  if (seg.parroquia) query = query.eq("parroquia", seg.parroquia);
  if (seg.area) query = query.contains("areas", [seg.area]);
  // 'rol' se ignora: en la tabla afiliados solo existe el rol de afiliado.

  const { data: afiliados, error: afError } = await query;
  if (afError) throw new Error(`Error consultando afiliados: ${afError.message}`);

  const userIds = (afiliados || []).map((a: any) => a.id);
  if (userIds.length === 0) return [];

  const { data: subs, error: subError } = await supabase
    .from("push_subscriptions")
    .select("endpoint, p256dh, auth, user_id")
    .in("user_id", userIds)
    .eq("activa", true);

  if (subError) throw new Error(`Error consultando suscripciones: ${subError.message}`);
  return subs || [];
}

// Devuelve 'expirada' cuando el push service ya no acepta ese endpoint, para
// poder borrarlo y no reintentar envios muertos en cada notificacion.
async function sendPush(
  sub: PushSubscriptionRow,
  payload: { title: string; body: string; data?: any }
): Promise<{ ok: boolean; user_id: string; expirada?: boolean; error?: string }> {
  try {
    await webpush.sendNotification(
      { endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } },
      JSON.stringify(payload)
    );
    return { ok: true, user_id: sub.user_id };
  } catch (e: any) {
    const status = e?.statusCode ?? e?.status;
    if (status === 404 || status === 410) {
      return { ok: false, user_id: sub.user_id, expirada: true, error: String(e?.message || e) };
    }
    return { ok: false, user_id: sub.user_id, error: String(e?.message || e) };
  }
}

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) {
    return new Response("Unauthorized", { status: 401, headers: corsHeaders });
  }

  const faltaVapid = usarVapid();
  if (faltaVapid) {
    return new Response(JSON.stringify({ error: faltaVapid }), { status: 500, headers: corsHeaders });
  }

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    global: { headers: { Authorization: authHeader } },
  });

  const { data: { user } } = await supabase.auth.getUser();
  if (!user || user.email !== ADMIN_EMAIL) {
    return new Response(JSON.stringify({ error: "Solo admin" }), { status: 403, headers: corsHeaders });
  }

  let body: NotificationPayload;
  try {
    body = await req.json();
  } catch {
    return new Response(
      JSON.stringify({ error: "Cuerpo JSON invalido" }),
      { status: 400, headers: corsHeaders }
    );
  }

  const { notificacion_id, titulo, cuerpo, estado, municipio, parroquia, area, rol } = body;
  if (!notificacion_id || !titulo || !cuerpo) {
    return new Response(
      JSON.stringify({ error: "Faltan campos obligatorios" }),
      { status: 400, headers: corsHeaders }
    );
  }

  const marcar = async (cambios: Record<string, unknown>) => {
    if (!notificacion_id) return;
    await supabase.from("notificaciones").update(cambios).eq("id", notificacion_id);
  };

  try {
    const subs = await getSegmentedSubscriptions(supabase, { estado, municipio, parroquia, area, rol });

    if (subs.length === 0) {
      await marcar({
        estado_envio: "completado",
        total_destinatarios: 0,
        enviados_ok: 0,
        fallidos: 0,
      });
      return new Response(
        JSON.stringify({ ok: true, message: "Sin destinatarios en ese segmento" }),
        { headers: corsHeaders }
      );
    }

    await marcar({ estado_envio: "enviando", total_destinatarios: subs.length });

    // No se mandan icon ni badge: el service worker los resuelve con su BASE,
    // que es la unica parte que sabe que el portal vive en un subdirectorio de
    // GitHub Pages. Si se mandaran aqui, serian rutas absolutas que darian 404.
    const pushPayload = {
      title: titulo,
      body: cuerpo,
      data: { notificacion_id, url: "/" },
      actions: [{ action: "abrir", title: "Abrir" }],
      requireInteraction: true,
    };

    let ok = 0;
    let fail = 0;
    const expiradas: string[] = [];
    const BATCH = 50; // para no comerse el limite de peticiones

    for (let i = 0; i < subs.length; i += BATCH) {
      const batch = subs.slice(i, i + BATCH);
      const results = await Promise.all(batch.map((s) => sendPush(s, pushPayload)));
      for (const r of results) {
        if (r.ok) ok++;
        else {
          fail++;
          if (r.expirada) expiradas.push(r.user_id);
        }
      }
      if (i + BATCH < subs.length) await new Promise((r) => setTimeout(r, 200));
    }

    // Los endpoints que el navegador ya no reconoce (410 Gone) se eliminan.
    // Antes este bloque no hacia nada: se recolectaban y se descartaban, y las
    // suscripciones muertas se reintentaban en cada notificacion para siempre.
    let limpiadas = 0;
    for (const userId of Array.from(new Set(expiradas))) {
      const { error } = await supabase
        .from("push_subscriptions")
        .delete()
        .eq("user_id", userId);
      if (!error) limpiadas++;
    }

    await marcar({ estado_envio: "completado", enviados_ok: ok, fallidos: fail });

    return new Response(
      JSON.stringify({ ok: true, enviados: ok, fallidos: fail, total: subs.length, limpiadas }),
      { headers: corsHeaders }
    );
  } catch (e: any) {
    await marcar({ estado_envio: "fallido" });
    return new Response(JSON.stringify({ error: String(e?.message || e) }), {
      status: 500,
      headers: corsHeaders,
    });
  }
});