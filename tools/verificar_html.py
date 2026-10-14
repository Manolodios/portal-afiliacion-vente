# -*- coding: utf-8 -*-
"""Analiza el HTML del perfil: busca <div> dentro de <p>, que es HTML invalido,
y mide el desbalance de divs del documento.

Un <div> dentro de un <p> hace que el navegador cierre el <p> antes de tiempo:
el bloque que aparentemente estaba dentro del parrafo queda como hermano. Por eso
cualquier textContent sobre ese <p> se lleva por delante lo que hubiera debajo.
"""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()

# ---------------------------------------------------------------- bloque perfil
i = html.find('id="profileViewBio"')
ini_p = html.rfind('<p', 0, i)
fin_p = html.find('</p>', i) + 4
seg = html[ini_p:fin_p]

print('=== <p id="profileViewBio"> (linea %d) ==='
      % (html[:i].count('\n') + 1))
ab = len(re.findall(r'<div\b', seg, re.I))
ce = len(re.findall(r'</div>', seg, re.I))
print('  div abiertos : %d' % ab)
print('  div cerrados : %d' % ce)
print('  <div> dentro de <p>: %s' % ('SI, HTML invalido' if ab else 'no'))

if ab:
    print()
    print('  El navegador cierra el <p> antes del <div>. Consecuencia:')
    print('  estas lineas borran la tarjeta de credencial al ejecutarse:')
    for n, linea in enumerate(html.splitlines(), 1):
        if 'profileViewBio' in linea and 'textContent' in linea:
            print('    L%d: %s' % (n, linea.strip()[:88]))

# ------------------------------------------------------------ desbalance global
print()
print('=== desbalance de divs en todo el documento ===')
todo = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.I)
todo = re.sub(r'<!--[\s\S]*?-->', '', todo)
ab = len(re.findall(r'<div\b', todo, re.I))
ce = len(re.findall(r'</div>', todo, re.I))
print('  div abiertos : %d' % ab)
print('  div cerrados : %d' % ce)
print('  diferencia   : %+d' % (ab - ce))
if ab != ce:
    print('  (HTML5 tolera el desbalance: el navegador anade lo que falte)')