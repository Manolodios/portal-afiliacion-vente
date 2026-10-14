# -*- coding: utf-8 -*-
"""Extrae los <script> clasicos de index.html a un unico archivo para poder
pasarlo por `node --check` (Node no lee HTML, asi que no puede validar el
sintaxis del JavaScript incrustado).

Cada script se envuelve en una funcion para que sus `const` no colisionen entre
si. Los scripts de tipo `module` se omiten: usan import/export.

    python tools/extract_all.py
    node --check tools/_salida/check_all.js
"""
import re
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')
SALIDA = os.path.join(AQUI, '_salida', 'check_all.js')
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)

html = open(INDEX, encoding='utf-8').read()
scripts = re.findall(r'<script(?![^>]*type="module")[^>]*>(.*?)</script>', html, re.S)
print('scripts clasicos:', len(scripts))

open(SALIDA, 'w', encoding='utf-8', newline='\n').write(
    '\n;\n'.join('async function __w%d__(){\n%s\n}' % (i, s) for i, s in enumerate(scripts))
)
print('escrito %s' % SALIDA)