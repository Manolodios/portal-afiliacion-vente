# -*- coding: utf-8 -*-
"""Dice a que bloque <script> pertenece cada linea de index.html y si el
bloque esta dentro de una funcion o condicion que pueda no ejecutarse.

Sirve para casos como "la funcion esta escrita en el archivo pero no existe en
el navegador": casi siempre significa que el codigo cae dentro de un bloque que
no llega a ejecutarse.
"""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()

patron = re.compile(r'<script([^>]*)>', re.I)
bloques = []
for m in patron.finditer(html):
    fin = html.find('</script>', m.end())
    if fin < 0:
        continue
    inicio_linea = html[:m.start()].count('\n') + 1
    bloques.append({
        'tipo': (re.search(r'type="([^"]+)"', m.group(1)) or [None, ''])[1] or 'clásico',
        'src': (re.search(r'src="([^"]+)"', m.group(1)) or [None, ''])[1],
        'ini': inicio_linea,
        'fin': html[:fin].count('\n') + 1,
        'largo': fin - m.end(),
        'cuerpo': html[m.end():fin],
    })

print('=== bloques de script ===')
for i, b in enumerate(bloques):
    print('  %d) lineas %5d-%-5d  tipo=%-8s  %5d chars  src=%s'
          % (i, b['ini'], b['fin'], b['tipo'], b['largo'], b['src'] or '-'))

INTERESANTES = [
    ('window.toggleCredential', 'boton del ojo'),
    ('window.copyAffiliationCode', 'boton Compartir'),
    ('window.downloadCredential', 'boton Guardar PDF'),
    ('window.adminSaveUser', 'boton Guardar cambios (admin)'),
    ('window.mostrarMiCredencial', 'QR de la credencial'),
    ('window.buscarMunicipio', 'cascada municipio'),
]

print()
print('=== donde vive cada funcion ===')
for marca, nombre in INTERESANTES:
    pos = html.find(marca)
    if pos < 0:
        print('  %-26s NO APARECE en el archivo' % nombre)
        continue
    linea = html[:pos].count('\n') + 1
    b = next((x for x in bloques if x['ini'] <= linea <= x['fin']), None)
    if b is None:
        print('  %-26s linea %d  (fuera de todo script)' % (nombre, linea))
        continue
    # Se mira si dentro de ese bloque la linea cae tras un "if (" sin cerrar.
    trozo = b['cuerpo'][:html[:pos].count('\n') - b['ini'] + 1]
    nivel_if = trozo.count('{') - trozo.count('}')
    print('  %-26s linea %5d  bloque %d (%s)  llaves netas=%+d'
          % (nombre, linea, bloques.index(b), b['tipo'], nivel_if))