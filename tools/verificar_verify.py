# -*- coding: utf-8 -*-
"""Extrae el <script type="module"> de verify.html y lo pasa por node --check.

Es un modulo ES, asi que se comprueba como .mjs. Sirve para cazar sintaxis de
TypeScript escrita en un script normal: los navegadores no compilan TypeScript y
fallan en silencio, sin mensaje en la consola.

    python tools/verificar_verify.py
"""
import io
import os
import re
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
VERIFY = os.path.join(RAIZ, 'verify.html')
SALIDA = os.path.join(AQUI, '_salida', 'verify_mod.mjs')
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)

html = io.open(VERIFY, encoding='utf-8').read()

m = re.search(r'<script type="module">(.*?)</script>', html, re.S)
if not m:
    print('FALLO: verify.html no tiene ningun <script type="module">')
    raise SystemExit(1)

codigo = m.group(1)
io.open(SALIDA, 'w', encoding='utf-8', newline='\n').write(codigo)
print('modulo extraido: %d caracteres' % len(codigo))

# Sintaxis de TypeScript que un navegador no ejecuta.
PATRONES = [
    (r'\)\s*:\s*(string|number|boolean|any|void|unknown|never)\b', 'anotacion de tipo en parametro'),
    (r'^\s*(async\s+)?function\s+\w+\s*\([^)]*:\s*\w+', 'anotacion de tipo en parametro'),
    (r'\b(const|let|var)\s+\w+\s*:\s*\w+\s*=', 'anotacion de tipo en variable'),
    (r'\)\s*:\s*[\w\[\]<>]+\s*\{', 'tipo de retorno'),
    (r'\.getContext\([^)]*\)\s*!', 'operador de no-nulo (!) de TypeScript'),
    (r'\bas\s+\w+\b', 'asercion "as" de TypeScript'),
]

fallos = 0
for patron, nombre in PATRONES:
    hits = re.findall(patron, codigo, re.M)
    if hits:
        fallos += len(hits)
        print('FALLO  %s: %d' % (nombre, len(hits)))
    else:
        print('OK     %s' % nombre)

print()
print('--- node --check ---')
res = subprocess.run(['node', '--check', SALIDA], capture_output=True, text=True)
if res.returncode != 0:
    print(res.stderr[:900])
    fallos += 1
else:
    print('OK     el modulo es JavaScript valido')

print()
if fallos:
    print('%d problema(s). verify.html fallaria en silencio en el navegador.' % fallos)
    raise SystemExit(1)
print('Todo correcto.')