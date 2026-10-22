// Service Worker del portal Vente Venezuela.
//
// Solo se encarga de las notificaciones push. NO cachea nada: no escucha el
// evento 'fetch' a proposito, para que activating el worker no pueda servir
// una version vieja de index.html a la gente que ya tiene la pagina abierta.
//
// BASE se calcula desde la propia ubicacion del worker, que es la carpeta del
// portal en GitHub Pages (/portal-afiliacion-vente/). Si se escribieran rutas
// como '/assets/logo.svg' los iconos darian 404, porque en ese hosting el
// portal no vive en la raiz del dominio sino en una subcarpeta.

var BASE = new URL('./', self.location.href).href;
var ICONO = BASE + 'assets/202605201779298032-logo-vente-cabimas-actualizado-04-2026-at-3x.png';
var BADGE = BASE + 'assets/logo-vente-cabimas.svg';

self.addEventListener('install', function (event) {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim());
});

// Convierte la URL que venga en la notificacion en algo navegable dentro del
// portal. Acepta '/', 'feed', '?v=feed' o una URL completa ya correcta.
function resolverDestino(bruto) {
  var u = String(bruto || '').trim();
  if (!u) return BASE;
  if (u.indexOf(BASE) === 0) return u;          // ya viene resuelta
  if (u.charAt(0) === '/') u = u.slice(1);      // '/algo' -> 'algo'

  var destino;
  try {
    destino = new URL(u, BASE);
  } catch (e) {
    return BASE;
  }

  // Solo se navega dentro del portal. Asi una notificacion manipulada no
  // puede abrir un dominio externo (phishing) al pulsarla.
  if (destino.origin !== new URL(BASE).origin) return BASE;
  if (destino.href.indexOf(BASE) !== 0) return BASE;
  return destino.href;
}

self.addEventListener('push', function (event) {
  if (!event.data) return;

  var payload = {};
  try {
    payload = event.data.json() || {};
  } catch (e) {
    // El push no venia en JSON: se usa el texto tal cual.
    payload = { title: 'Vente Venezuela', body: event.data.text() };
  }

  var opciones = {
    body: payload.body || payload.cuerpo || '',
    icon: payload.icon || ICONO,
    badge: payload.badge || BADGE,
    tag: payload.notificacion_id || 'notificacion',
    data: {
      notificacion_id: payload.notificacion_id || null,
      url: resolverDestino(payload.data && payload.data.url)
    },
    actions: payload.actions || [{ action: 'abrir', title: 'Abrir portal' }],
    requireInteraction: true
  };

  event.waitUntil(self.registration.showNotification(
    payload.title || payload.titulo || 'Vente Venezuela',
    opciones
  ));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();

  var datos = event.notification.data || {};
  var destino = resolverDestino(datos.url);

  // El boton "Abrir portal" siempre lleva a la pagina principal; si no, al
  // destino que traia la notificacion. Si ya hay una pestaña del portal
  // abierta se enfoca en vez de abrir otra.
  if (event.action === 'abrir') destino = BASE;

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (lista) {
      for (var i = 0; i < lista.length; i++) {
        if (lista[i].url.indexOf(BASE) === 0 && 'focus' in lista[i]) {
          lista[i].focus();
          if (destino !== BASE) lista[i].navigate(destino);
          return null;
        }
      }
      return self.clients.openWindow(destino);
    }).catch(function () {
      return self.clients.openWindow(BASE);
    })
  );
});