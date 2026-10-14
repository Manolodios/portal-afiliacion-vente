# -*- coding: utf-8 -*-
"""Detaca funciones que existen en el archivo pero que nunca llegan a existir
en el navegador.

El sintoma es desconcertante: los botones estan en el HTML, la funcion esta
escrita a unas lineas mas abajo... y al pulsar sale
"copyAffiliationCode is not a function". No hay error de sintaxis ni aviso en
la consola.

La causa habitual es una linea duplicada que abre un bloque sin cerrarlo: todo
el codigo que queda despues acaba dentro de esa funcion y solo se crea cuando
se llama. Aqui se detectan las dos señales:

  1. Sentencias "window.X =" duplicadas de forma consecutiva.
  2. Asignaciones de window.* que caen dentro del cuerpo de otra funcion
     (llaves sin cerrar desde la linea anterior).

    python tools/verificar_alcance.py
"""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()
ls = html.split('\n')

fallos = 0

# --- 1. duplicados consecutivos --------------------------------------------
print('=== asignaciones window.* duplicadas seguidas ===')
pat_asig = re.compile(r'^\s*window\.(\w+)\s*=\s*(async\s+)?function')
prev = None
for i, l in enumerate(ls, 1):
    m = pat_asig.match(l)
    if m and prev and prev[1] == m.group(1) and prev[0] == i - 1:
        print('  FALLO  lineas %d y %d declaran window.%s' % (prev[0], i, m.group(1)))
        print('         la primera abre un bloque sin cerrar: lo que sigue queda')
        print('         dentro de esa funcion y nunca se ejecuta al cargar.')
        fallos += 1
    prev = (i, m.group(1)) if m else None
if not fallos:
    print('  ninguna')

# --- 2. asignaciones window.* dentro de una funcion -------------------------
print()
print('=== asignaciones window.* anidadas en otra funcion ===')


def sin_cadenas(l):
    dentro = False
    esc = False
    salida = []
    i = 0
    while i < len(l):
        ch = l[i]
        if esc:
            esc = False
            i += 1
            continue
        if ch == '\\':
            esc = True
            i += 1
            continue
        if ch in '"\'':
            dentro = not dentro
            i += 1
            continue
        if dentro:
            i += 1
            continue
        # Comentarios de linea
        if ch == '/' and i + 1 < len(l) and l[i + 1] == '/':
            break
        salida.append(ch)
        i += 1
    return ''.join(salida)


# Se ignoran los bloques <script ...>...</script> por separado.
bloques = []
for m in re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.S):
    bloques.append((html[:m.start()].count('\n') + 1, m.group(2)))

niveles = {}
for ini, cuerpo in bloques:
    nivel = 0
    for j, l in enumerate(cuerpo.split('\n')):
        limpio = sin_cadenas(l)
        # Plantillas de texto: se ignoran para no contar sus llaves.
        limpio = re.sub(r'`[^`]*`', '', limpio)
        delta = limpio.count('{') - limpio.count('}')
        niveles[ini + j] = nivel
        nivel += delta

anidados = []
for j, l in enumerate(html.split('\n'), 1):
    m = pat_asig.match(l)
    if m and niveles.get(j, 0) > 0:
        anidados.append((j, m.group(1), niveles[j]))

if anidados:
    for j, nombre, n in anidados[:20]:
        print('  FALLO  L%-5d window.%-24s esta %d nivel(es) dentro de otro bloque'
              % (j, nombre, n))
        print('         solo existira si se llama a esa funcion.')
    fallos += len(anidados)
else:
    print('  ninguna')

print()
if fallos:
    print('%d problema(s). Botones que parecen existir pero no existen.' % fallos)
    raise SystemExit(1)
print('Todo correcto: todo lo que el HTML llama existe al cargar la pagina.')