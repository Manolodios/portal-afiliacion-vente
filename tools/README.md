# tools/

Utilidades para reconstruir el feed de publicaciones del portal.

## Cadena principal (reconstruir el feed a mano)

Se ejecuta en orden, desde la raíz del repositorio:

```bash
python tools/build_feed_wide.py   # descarga RSS de las cuentas + fotos y estadisticas
python tools/clean_feed.py        # fuera retweets, hilos sueltos y posts de mas de 45 dias
python tools/gen_feed_wide.py     # genera el bloque JS (tools/_salida/nuevo_feed.js)
python tools/apply_feed.py        # lo sustituye en index.html
node .github/scripts/validar-feed.mjs   # comprueba que el portal sigue en pie
```

Los pasos son **idempotentes**: repetirlos sin datos nuevos no cambia el archivo.
`apply_feed.py` aborta sin escribir nada si no encuentra los bloques, para no
dejar el portal a medias.

## Diagnóstico

```bash
python tools/verificar_fechas.py  # comprueba que cada fecha cuadra con su id de snowflake
python tools/verificar_texto.py   # busca restos de Twitter, HTML sin decodificar y ruido
python tools/extract_all.py       # extrae los <script> a un .js para pasarlo por node --check
python tools/test_cuentas.py      # prueba que cuentas tienen RSS utilizable en Nitter
```

`verificar_fechas.py` es la prueba de que los posts no están inventados: en Twitter
el id es un *snowflake* que codifica el instante exacto (`(id >> 22) + 1288834974657`
= fecha UTC). Si alguien escribiera una fecha a mano que no cuadrase con el id, saldría
como descuadre.

## Automatización

Para producción no hace falta esta cadena: GitHub Actions ejecuta
`.github/scripts/actualizar-feed.mjs` cada 6 horas, que hace todo en un solo
paso y valida antes de publicar. Estos scripts sirven para trabajar en local,
depurar y ver el feed antes de subirlo.

## Notas

- Los datos vienen de mirrors de **Nitter** (`twiiit.com`, `nitter.meowing.monster`,
  etc.). Se caen con frecuencia, por eso se prueban en cascada. Twitter ya no
  ofrece RSS y RSSHub.app retirado las rutas de Twitter.
- Las fotos y las cifras (likes, retweets, respuestas) salen de `api.fxtwitter.com`,
  que es publica y no necesita clave.
- Los avatares se resuelven en la misma API; si falla se usa `assets/avatar-marcorina.jpg`.
- Solo se incluyen cuentas de **Vente Venezuela**. El portal es de ese partido.
- `_salida/` es material de trabajo y no se sube a git.