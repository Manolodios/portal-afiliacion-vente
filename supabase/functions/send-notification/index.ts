import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { webPush } from "https://deno.land/x/web_push@0.1.0/mod.ts";

// Configuración VAPID (generar con: npx web-push generate-vapid-keys)
// VAPID_PUBLIC_KEY y VAPID_PRIVATE_KEY van en secrets de Supabase
const VAPID_PUBLIC_KEY = Deno.env.get("VAPID_PUBLIC_KEY")!;
const VAPID_PRIVATE_KEY = Deno.env.get("VAPID_PRIVATE_KEY")!;
const VAPID_SUBJECT = "mailto:yhojansuarez@gmail.com";

webPush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SERVICE_ROLE_KEY")!;

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

interface NotificationPayload {
  notificacion_id: string;
  titulo: string;
  cuerpo: string;
  // Segmentación
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
  // Primero obtenemos los user_ids que cumplen la segmentación
  let query = supabase.from("afiliados").select("id");
  if (seg.estado) query = query.eq("estado", seg.estado);
  if (seg.municipio) query = query.eq("municipio", seg.municipio);
  if (seg.parroquia) query = query.eq("parroquia", seg.parroquia);
  if (seg.area) query = query.contains("areas", [seg.area]);
  // rol se ignora aquí porque solo tenemos 'afiliado' en la tabla afiliados

  const { data: afiliados, error: afError } = await query;
  if (afError) throw new Error(`Error consultando afiliados: ${afError.message}`);

  const userIds = afiliados.map((a: any) => a.id);
  if (userIds.length === 0) return [];

  // Ahora suscripciones push activas de esos usuarios
  const { data: subs, error: subError } = await supabase
    .from("push_subscriptions")
    .select("endpoint, p256dh, auth, user_id")
    .in("user_id", userIds)
    .eq("activa", true);

  if (subError) throw new Error(`Error consultando suscripciones: ${subError.message}`);
  return subs || [];
}

async function sendPush(sub: PushSubscriptionRow, payload: { title: string; body: string; icon?: string; data?: any }) {
  try {
    await webPush.sendNotification(
      {
        endpoint: sub.endpoint,
        keys: { p256dh: sub.p256dh, auth: sub.auth },
      },
      JSON.stringify(payload)
    );
    return { ok: true, user_id: sub.user_id };
  } catch (e: any) {
    // 410 = subscription expired, 404 = endpoint not found
    if (e.statusCode === 410 || e.statusCode === 404) {
      // Marcar como inactiva para limpieza posterior
      return { ok: false, user_id: sub.user_id, expired: true, error: e.message };
    }
    return { ok: false, user_id: sub.user_id, error: e.message };
  }
}

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders });
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return new Response("Unauthorized", { status: 401, headers: corsHeaders });

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
    global: { headers: { Authorization: authHeader } },
  });

  // Verificar que el caller es admin
  const { data: { user } } = await supabase.auth.getUser();
  if (!user || user.email !== "yhojansuarez@gmail.com") {
    return new Response(JSON.stringify({ error: "Solo admin" }), { status: 403, headers: corsHeaders });
  }

  const body: NotificationPayload = await req.json();
  const { notificacion_id, titulo, cuerpo, estado, municipio, parroquia, area, rol } = body;

  if (!notificacion_id || !titulo || !cuerpo) {
    return new Response(JSON.stringify({ error: "Faltan campos obligatorios" }), { status: 400, headers: corsHeaders });
  }

  try {
    // Obtener suscripciones segmentadas
    const subs = await getSegmentedSubscriptions(supabase, { estado, municipio, parroquia, area, rol });

    if (subs.length === 0) {
      await supabase.from("notificaciones").update({
        estado_envio: "completado",
        total_destinatarios: 0,
        enviados_ok: 0,
        fallidos: 0,
      }).eq("id", notificacion_id);
      return new Response(JSON.stringify({ ok: true, message: "Sin destinatarios en ese segmento" }), { headers: corsHeaders });
    }

    // Actualizar estado a "enviando"
    await supabase.from("notificaciones").update({ estado_envio: "enviando", total_destinatarios: subs.length }).eq("id", notificacion_id);

    const pushPayload = {
      title: titulo,
      body: cuerpo,
      icon: "/assets/202605201779298032-logo-vente-cabimas-actualizado-04-2026-at-3x.png",
      badge: "/assets/badge-72x72.png",
      data: { notificacion_id, url: "/" },
      actions: [{ action: "abrir", title: "Abrir" }],
      requireInteraction: true,
    };

    let ok = 0, fail = 0, expired = 0;
    const batchSize = 50; // evitar rate limits
    for (let i = 0; i < subs.length; i += batchSize) {
      const batch = subs.slice(i, i + batchSize);
      const results = await Promise.all(batch.map(s => sendPush(s, pushPayload)));
      for (const r of results) {
        if (r.ok) ok++;
        else if (r.expired) { expired++; fail++; }
        else fail++;
      }
      // Pequeña pausa entre batches
      if (i + batchSize < subs.length) await new Promise(r => setTimeout(r, 200));
    }

    // Limpiar suscripciones expiradas
    if (expired > 0) {
      const expiredEndpoints = subs.filter((_, idx) => {
        // Esto es aproximado; en producción haríamos tracking preciso
        return false;
      }).map(s => s.endpoint);
      // Nota: la limpieza real se hace en el cliente al recibir pushsubscriptionchange
    }

    await supabase.from("notificaciones").update({
      estado_envio: "completado",
      enviados_ok: ok,
      fallidos: fail,
    }).eq("id", notificacion_id);

    return new Response(JSON.stringify({ ok: true, enviados: ok, fallidos, total: subs.length }), { headers: corsHeaders });
  } catch (e: any) {
    await supabase.from("notificaciones").update({ estado_envio: "fallido" }).eq("id", notificacion_id);
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
  }
});