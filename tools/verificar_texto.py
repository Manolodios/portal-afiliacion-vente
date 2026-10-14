# -*- coding: utf-8 -*-
"""Busca texto sospechoso en el feed: signos de interrogacion sueltos,
caracteres de reemplazo (U+FFFD) y restos de marcado de Twitter."""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()
ini = html.find('const FEED_POSTS = [')
bloque = html[ini:html.find('\n        ];', ini)]

print('U+FFFD (caracter de reemplazo) en index.html:', html.count(chr(0xFFFD)))

REGLAS = [
    (r'\?{2,}', 'interrogaciones sueltas'),
    (r'\]\]>', 'resto de CDATA ]]>'),
    (r'(?im)^\s*(video|image|foto)\s*$', 'linea de ruido multimedia'),
    (r'&(amp|lt|gt|quot);', 'entidad HTML sin decodificar'),
    (r't\.co/', 'enlace corto sin quitar'),
    (r'RT by @', 'prefijo de retweet sin quitar'),
]

fallos = 0
for patron, nombre in REGLAS:
    hits = re.findall(patron, bloque)
    if hits:
        fallos += len(hits)
        print('FALLO  %s: %d' % (nombre, len(hits)))
        for m in re.finditer(patron, bloque):
            ini_p = max(0, m.start() - 60)
            print('        ...%s...' % bloque[ini_p:m.end() + 60].replace('\n', ' '))
    else:
        print('OK     %s' % nombre)

print()
print('Sospechosos: %d' % fallos)