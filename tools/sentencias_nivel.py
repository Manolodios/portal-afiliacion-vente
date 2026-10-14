# -*- coding: utf-8 -*-
"""Lista las sentencias de nivel superior de un bloque de script, ignorando
cadenas y comentarios.

Sirve para localizar la linea que puede estar lanzando una excepcion e
impidiendo que se ejecuten las siguientes: si una asignacion de window.X queda
"sin ejecutar" en el navegador pero esta escrita en el archivo, casi siempre
hay un throw antes.
"""
import io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
html = io.open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()

ini = int(sys.argv[1]) if len(sys.argv) > 1 else 3120
fin = int(sys.argv[2]) if len(sys.argv) > 2 else 3410
NIVEL = int(sys.argv[3]) if len(sys.argv) > 3 else 1

ls = html.split('\n')


def sin_cadenas(l):
    dentro = False
    esc = False
    salida = []
    for ch in l:
        if esc:
            salida.append(' ')
            esc = False
            continue
        if ch == '\\':
            salida.append(' ')
            esc = True
            continue
        if ch in '"\'':
            dentro = not dentro
            salida.append(' ')
            continue
        salida.append(' ' if dentro else ch)
    return ''.join(salida)


nivel = 0
print('=== sentencias de nivel %d entre %d y %d ===' % (NIVEL, ini, fin))
for i, l in enumerate(ls, 1):
    limpio = sin_cadenas(l)
    # Los comentarios de linea se dejan fuera del conteo.
    corte = limpio.find('//')
    if corte >= 0 and limpio[:corte].count('"') == 0:
        limpio = limpio[:corte]
    delta = limpio.count('{') - limpio.count('}')
    aqui = nivel
    nivel += delta
    if not (ini <= i <= fin):
        continue
    t = l.strip()
    if not t or t.startswith('//') or t.startswith('/*') or t.startswith('*'):
        continue
    if aqui == NIVEL:
        print('%5d  %s' % (i, t[:105]))