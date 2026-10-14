# -*- coding: utf-8 -*-
"""Genera los bloques JS del feed ampliado: FEED_POSTS y LEADERS.

Es el paso 3 de la cadena local. Escribe tools/_salida/nuevo_feed.js, que
despues aplica apply_feed.py sobre index.html.

    python tools/gen_feed_wide.py
"""
import json, io, re, os

AQUI = os.path.dirname(os.path.abspath(__file__))
FEED_JSON = os.path.join(AQUI, '_salida', 'feed_ampliado.json')
SALIDA = os.path.join(AQUI, '_salida', 'nuevo_feed.js')

d = json.load(io.open(FEED_JSON, encoding='utf-8'))
posts, avatares = d['posts'], d['avatares']

LEADERS = [
    ('MariaCorinaYA', 'María Corina Machado', 'Presidente de Vente Venezuela', True),
    ('VenteVenezuela', 'Vente Venezuela', 'Vente Venezuela', True),
    ('Carlosafg_', 'Carlos Alfonzo Guarín', 'Coordinador Nacional de Defensa', True),
    ('VenteCcs', 'Vente Distrito Capital', 'Vente Distrito Capital', True),
    ('HenryAlviarez', 'Henry Alviarez', 'Coordinador Zulia', True),
]

COMUNIDAD = '''        const COMUNIDAD = [
            { handle: "vente_", label: "Comunidad Vente" },
            { handle: "caja", label: "Caja de Pandora" }
        ];'''


def esc(t):
    t = t.replace('\\', '\\\\').replace('"', '\\"')
    return re.sub(r'\n+', '\\\\n', t)


out = []
out.append('        const FEED_POSTS = [')
prev = None
for i, p in enumerate(posts):
    if p['author'] != prev:
        nombre = next((n for h, n, _, _ in LEADERS if h == p['author']), p['author'])
        out.append('            // %s' % nombre)
        prev = p['author']
    fotos = ', '.join('"%s"' % u.replace('&', '&amp;') for u in p['photos'])
    out.append('            { id: "%s", author: "%s", text: "%s", date: "%s", time: "%s", '
               'replies: %d, reposts: %d, likes: %d, photos: [%s], link: "%s" }%s'
               % (p['id'], p['author'], esc(p['text']), p['date'], p['time'],
                  p['replies'], p['reposts'], p['likes'], fotos, p['link'],
                  ',' if i < len(posts) - 1 else ''))
out.append('        ];')
out.append('')
out.append('        const LEADERS = [')
for i, (h, nombre, rol, ver) in enumerate(LEADERS):
    av = avatares.get(h) or 'assets/avatar-marcorina.jpg'
    out.append('            { handle: "%s", name: "%s", avatar: "%s", verified: %s, party: "%s" }%s'
               % (h, nombre, av, 'true' if ver else 'false', rol,
                  ',' if i < len(LEADERS) - 1 else ''))
out.append('        ];')

texto = '\n'.join(out)
io.open(SALIDA, 'w', encoding='utf-8', newline='\n').write(texto)
print('posts:', len(posts), 'leaders:', len(LEADERS), 'chars:', len(texto))