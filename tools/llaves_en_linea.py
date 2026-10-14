# -*- coding: utf-8 -*-
"""Cuenta llaves en una linea concreta de index.html para saber si cae dentro
de una funcion o bloque que no se haya cerrado.

    python tools/llaves_en_linea.py 3409
"""
import io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
html = io.open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()

objetivo = int(sys.argv[1]) if len(sys.argv) > 1 else 3409
ls = html.split('\n')

nivel = 0
for i, l in enumerate(ls[:objetivo], 1):
    dentro_cadena = False
    esc = ''
    limpio = []
    for ch in l:
        if esc:
            limpio.append(' ')
            esc = ''
            continue
        if ch == '\\':
            esc = ch
            limpio.append(' ')
            continue
        if ch in '"\'':
            dentro_cadena = not dentro_cadena
            limpio.append(' ')
            continue
        if dentro_cadena:
            limpio.append(' ')
            continue
        limpio.append(ch)
    limpio = ''.join(limpio)
    nivel += limpio.count('{') - limpio.count('}')
    if limpio.lstrip().startswith('//'):
        continue

# Se imprime el contexto con el nivel de llaves en cada linea clave
print('=== contexto alrededor de la linea %d ===' % objetivo)
nivel = 0
for i, l in enumerate(ls, 1):
    dentro_cadena = False
    esc = ''
    limpio = []
    for ch in l:
        if esc:
            esc = ''
            continue
        if ch == '\\':
            esc = ch
            continue
        if ch in '"\'':
            dentro_cadena = not dentro_cadena
            continue
        limpio.append(ch)
    limpio = ''.join(limpio)
    delta = limpio.count('{') - limpio.count('}')
    if objetivo - 60 <= i <= objetivo + 12:
        marca = '>>>' if i == objetivo else '   '
        print('%s %5d  nivel=%+d  %s' % (marca, i, nivel, l.strip()[:95]))
    nivel += delta