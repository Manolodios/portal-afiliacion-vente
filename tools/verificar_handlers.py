# -*- coding: utf-8 -*-
"""Comprueba que todas las funciones llamadas desde el HTML existan en el JS.

Los atributos onclick="algo(...)" se resuelven al hacer clic. Si la funcion no
esta definida en ningun script, el navegador lanza
"ReferenceError: algo is not defined" y el boton no hace nada: un fallo que no
se ve hasta que se pulsa.
"""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()

EVENTOS = r'on(?:click|input|change|submit|load|focus|blur|error|keyup|keydown)='
llamadas = set(re.findall(EVENTOS + r'"([a-zA-Z_$][\w$]*)\s*\(', html))
llamadas |= set(re.findall(EVENTOS + r"'([a-zA-Z_$][\w$]*)\s*\(", html))

DEFINIDA = (
    r'function\s+{n}\b'
    r'|window\.{n}\s*='
    r'|(?:const|let|var)\s+{n}\s*='
    r'|\b{n}\s*=\s*(?:async\s*)?(?:function|\()'
)


def definida(n):
    patron = DEFINIDA.format(n=re.escape(n))
    return re.search(patron, html) is not None


faltan = [n for n in sorted(llamadas) if not definida(n)]

print('=== manejadores en el HTML ===')
print('  funciones llamadas desde atributos: %d' % len(llamadas))
print('  definidas en el JS              : %d' % (len(llamadas) - len(faltan)))
print()

if faltan:
    print('  FALTAN:')
    for n in faltan:
        print('    - %s()   -> ReferenceError al pulsar' % n)
else:
    print('  OK: todas las funciones del HTML existen en el JS.')

print()
print('=== funciones definidas y nunca llamadas (codigo muerto) ===')
defs = set(re.findall(r'(?:async\s+)?function\s+([a-zA-Z_$][\w$]*)', html))
huerfanas = []
for n in sorted(defs):
    usos = len(re.findall(r'\b' + re.escape(n) + r'\s*\(', html))
    if usos <= 1:
        huerfanas.append(n)
if huerfanas:
    for n in huerfanas:
        print('    - %s()' % n)
else:
    print('  ninguna')

print()
total = len(faltan) + len(huerfanas)
print('Incidencias: %d' % total)
raise SystemExit(1 if faltan else 0)