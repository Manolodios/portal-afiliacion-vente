# Portal de Afiliación — Vente Cabimas

🌐 **Página en vivo:** https://manolodios.github.io/portal-afiliacion-vente/

Prototipo de afiliación anónimo para el partido Vente Venezuela.

## Verificación de correo

- Al registrarte recibes un correo de confirmación.
- El enlace te lleva a `verify.html`, que muestra "Ya estás verificado — ya puedes cerrar esta página".
- Si ves 404 o "enlace inválido", pide un nuevo correo desde el portal.

## Desarrollo local

Abrir con un servidor local (ej. Live Server en VS Code) apuntando a la raíz del repo.

## Feed de publicaciones

El feed muestra publicaciones reales de las cuentas oficiales de Vente Venezuela,
con sus fotos y cifras (likes, retweets) obtenidas de `api.fxtwitter.com`. En vivo se
actualiza por RSS mediante mirrors de Nitter; Twitter ya no ofrece RSS y RSSHub.app
retiró las rutas de Twitter.

Para reconstruirlo a mano, las herramientas están en [`tools/`](tools/README.md):

```bash
python tools/build_feed_wide.py
python tools/clean_feed.py
python tools/gen_feed_wide.py
python tools/apply_feed.py
node .github/scripts/validar-feed.mjs
```

En producción lo hace solo GitHub Actions cada 6 horas con
`.github/scripts/actualizar-feed.mjs`.

Antes de dar por buenos los datos, `tools/verificar_fechas.py` comprueba que la fecha
de cada publicación cuadra con su id de snowflake (que codifica el instante real del
post) y `tools/verificar_texto.py` busca restos de Twitter y HTML sin decodificar.

## Notificaciones push

`sw.js` es el service worker del portal. Se registra desde `index.html` con la ruta
**relativa** `sw.js`, no con `/sw.js`: el portal vive en `/portal-afiliacion-vente/`
en GitHub Pages, así que una ruta absoluta pedía `manolodios.github.io/sw.js` y
devolvía 404 sin que se notara (el fallo se tragaba un `.catch`).

Dentro del worker, `BASE` se calcula desde `self.location` y todas las rutas de
iconos y enlaces cuelgan de ahí, por el mismo motivo.

El worker **no cachea nada**: no escucha el evento `fetch`. Es deliberado, para que
activarlo no pueda servir una versión vieja de `index.html`.

### Estado: falta un paso, en el panel de Supabase

| Pieza | Estado |
|---|---|
| `sw.js` registrado | ✅ |
| Botón de suscripción en el panel del afiliado | ✅ |
| Suscripción guardada vía `upsert_push_subscription` | ✅ |
| Función `send-notification` desplegada | ✅ (activa, `verify_jwt: true`) |
| Claves VAPID en los secretos de Supabase | ⬜ **pendiente** |

Para terminar: en Supabase → **Edge Functions → send-notification → Secrets**, añadir
`VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY`. Los valores están en `.env.vapid`
(ignorado por git). Sin ellos la función responde con un error explícito que lo dice,
en vez de fallar en silencio.

Después, un afiliado abre su panel, pulsa **Activar notificaciones** y acepta el
permiso; queda suscrito y la notificación del seeing le llega.

Las claves se generaron con `npx web-push generate-vapid-keys`. La **privada** no
debe salir nunca de los secretos de Supabase ni del archivo local.

## Stack

- HTML + Tailwind CSS (CDN)
- Supabase Auth + tabla `afiliados`
