# -*- coding: utf-8 -*-
"""Sustituye los bloques FEED_POSTS y LEADERS de index.html por los generados
en tools/_salida/nuevo_feed.js.

Es el paso final de la cadena local:
    build_feed_wide.py -> clean_feed.py -> gen_feed_wide.py -> apply_feed.py

Solo toca esos dos bloques. Si no se localizan, aborta sin escribir nada: es
preferible dejar el feed anterior a dejar el portal a medias.

    python tools/apply_feed.py
"""
import io
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)                    # raiz del repositorio
INDEX = os.path.join(RAIZ, 'index.html')
NUEVO = os.path.join(AQUI, '_salida', 'nuevo_feed.js')


def bloque(html, inicio, fin):
    """Devuelve (desde, hasta) del bloque que empieza en `inicio` y acaba en
    su cierre `fin`, o (-1, -1) si no aparece."""
    i = html.find(inicio)
    if i < 0:
        return -1, -1
    j = html.find(fin, html.find('[', i))
    if j < 0:
        return -1, -1
    return i, j + len(fin)


def recortar_comentarios(html, cabecera):
    """Elimina las lineas de comentario seguidas que preceden a `cabecera`.
    El generador las va anadiendo en cada corrida y sin esto el archivo crece
    sin limite."""
    cab = cabecera.rstrip('[').rstrip()
    while True:
        pos = html.find(cab)
        if pos < 0:
            break
        ini = html.rfind('\n', 0, pos) + 1
        if ini <= 0:
            break
        fin_previa = ini - 1
        ini_previa = html.rfind('\n', 0, fin_previa) + 1
        if not html[ini_previa:fin_previa].strip().startswith('//'):
            break
        html = html[:ini_previa] + html[ini:]
    return html


if not os.path.isfile(NUEVO):
    raise SystemExit('Falta %s. Ejecuta antes gen_feed_wide.py.' % NUEVO)

nuevo = io.open(NUEVO, encoding='utf-8').read()
html = io.open(INDEX, encoding='utf-8').read()
orig = len(html)

# ------------------------------------------------------------------ LEADERS
i, j = bloque(html, '        const LEADERS = [', '\n        ];')
if i < 0:
    raise SystemExit('No se encontro el bloque LEADERS. Abortando sin cambios.')
ini_feed_nuevo = nuevo.find('        const LEADERS = [')
if ini_feed_nuevo < 0:
    raise SystemExit('nuevo_feed.js no trae LEADERS. Abortando sin cambios.')
fin_feed_nuevo = nuevo.find('\n        ];', ini_feed_nuevo)
leaders = nuevo[ini_feed_nuevo:fin_feed_nuevo + len('\n        ];')]

html = html[:i] + leaders + html[j:]
html = recortar_comentarios(html, '        const LEADERS = [')
html = html.replace('        const LEADERS = [',
                    '        // Líderes y cuentas de Vente Venezuela\n        const LEADERS = [', 1)
print('LEADERS actualizado (%d cuentas)' % leaders.count('{ handle:'))

# --------------------------------------------------------------- FEED_POSTS
i, j = bloque(html, '        const FEED_POSTS = [', '\n        ];')
if i < 0:
    raise SystemExit('No se encontro el bloque FEED_POSTS. Abortando sin cambios.')
ini_feed_nuevo = nuevo.find('        const FEED_POSTS = [')
if ini_feed_nuevo < 0:
    raise SystemExit('nuevo_feed.js no trae FEED_POSTS. Abortando sin cambios.')
fin_feed_nuevo = nuevo.find('\n        ];', ini_feed_nuevo)
feed = nuevo[ini_feed_nuevo:fin_feed_nuevo + len('\n        ];')]

html = html[:i] + feed + html[j:]
# Sin este recorte el comentario anterior se conserva y cada corrida anade otro
# mas: el archivo crecia 197 bytes por ejecucion y acumulaba cabeceras.
html = recortar_comentarios(html, '        const FEED_POSTS = [')
html = html.replace('        const FEED_POSTS = [',
                    '        // === FEED: publicaciones reales y recientes ===\n'
                    '        // Generado por tools/ (build_feed_wide.py). El RSS en vivo\n'
                    '        // (RSS_FEEDS) se antepone a estas: el feed se actualiza solo.\n'
                    '        const FEED_POSTS = [', 1)
print('FEED_POSTS actualizado (%d publicaciones)' % feed.count('{ id:'))

# --- comprobaciones minimas antes de escribir -------------------------------
if 'const LEADERS' not in html or 'const FEED_POSTS' not in html:
    raise SystemExit('El resultado quedo incompleto. Abortando sin cambios.')
if html.count('        ];') < 2:
    raise SystemExit('Cierres de array inesperados. Abortando sin cambios.')

io.open(INDEX, 'w', encoding='utf-8', newline='').write(html)
print('index.html: %d -> %d bytes' % (orig, len(html)))