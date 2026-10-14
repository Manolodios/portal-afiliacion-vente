# -*- coding: utf-8 -*-
"""Valida cada bloque <script> de index.html por separado.

Concatenarlos todos en un archivo esconde el origen del fallo: si un bloque
tiene una llave de mas, el error sale en la linea del archivo pegado pero no
se sabe cual era. Aqui cada bloque va a su propio archivo y se puede leer el
mensaje tal cual.

    python tools/verificar_bloques.py
"""
import io
import os
import re
import subprocess
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')
SALIDA = os.path.join(AQUI, '_salida')

html = io.open(INDEX, encoding='utf-8').read()

bloques = []
for m in re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.S):
    attrs = m.group(1)
    tipo = (re.search(r'type="([^"]+)"', attrs) or [None, ''])[1] or 'classic'
    src = (re.search(r'src="([^"]+)"', attrs) or [None, ''])[1]
    ini = html[:m.start()].count('\n') + 1
    bloques.append({
        'tipo': tipo, 'src': src, 'ini': ini,
        'cuerpo': m.group(2),
        'largo': len(m.group(2)),
    })

print('=== %d bloques de script ===' % len(bloques))
fallos = 0

for i, b in enumerate(bloques):
    if b['src']:
        print('  %2d) L%-6d externo   %s' % (i, b['ini'], b['src'][:60]))
        continue
    if not b['cuerpo'].strip():
        print('  %2d) L%-6d vacio' % (i, b['ini']))
        continue

    # Cada bloque va envuelto para poder comprobarlo como unidad independiente.
    tmp = os.path.join(SALIDA, 'bloque_%02d.js' % i)
    io.open(tmp, 'w', encoding='utf-8', newline='\n').write(b['cuerpo'])
    res = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)

    if res.returncode == 0:
        print('  %2d) L%-6d OK       %6d chars  (%s)'
              % (i, b['ini'], b['largo'], b['tipo']))
    else:
        fallos += 1
        err = res.stderr.strip().split('\n')
        print('  %2d) L%-6d FALLO   %6d chars  (%s)' % (i, b['ini'], b['largo'], b['tipo']))
        for linea in err[:6]:
            print('         ' + linea.strip()[:110])

        # Se localize la linea exacta dentro del bloque.
        m = re.search(r':(\d+)$', err[-1].strip()) if err else None
        if m:
            n = int(m.group(1))
            lineas = b['cuerpo'].split('\n')
            ini_real = b['ini'] + n - 1
            print('         linea %d del bloque = linea %d de index.html:' % (n, ini_real))
            for k in range(max(0, n - 4), min(len(lineas), n + 2)):
                marca = '>>>' if k == n - 1 else '   '
                print('         %s %5d  %s' % (marca, b['ini'] + k,
                                                lineas[k].strip()[:95]))

print()
if fallos:
    print('%d bloque(s) con error de sintaxis.' % fallos)
    raise SystemExit(1)
print('Todos los bloques son JavaScript valido.')