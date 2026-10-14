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

## Stack

- HTML + Tailwind CSS (CDN)
- Supabase Auth + tabla `afiliados`
