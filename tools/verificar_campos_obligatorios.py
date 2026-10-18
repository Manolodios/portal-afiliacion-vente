# -*- coding: utf-8 -*-
"""Compara los campos del formulario de ficha con las columnas NOT NULL de la
tabla afiliados.

Si el formulario deja un campo opcional y la base de datos lo exige, el INSERT
falla cuando el usuario lo deja vacio, con un error que el formulario no sabe
explicar. Eso es lo que hace que "no se puede registrar".

    python tools/verificar_campos_obligatorios.py
"""
import io
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

html = io.open(INDEX, encoding='utf-8').read()

i = html.find('id="form-onboarding"')
if i < 0:
    raise SystemExit('No se encontro el formulario de ficha')
seg = html[i:i + 6000]

campos = {}
for m in re.finditer(r'<(input|select)[^>]*id="(ob-[a-z0-9-]+)"[^>]*>', seg):
    tag = m.group(0)
    cid = m.group(2)
    tipo = re.search(r'type="([^"]+)"', tag)
    campos[cid] = {
        'obligatorio': 'required' in tag,
        'tipo': tipo.group(1) if tipo else 'select',
    }

# A que columna va cada campo del formulario.
COLUMNA = {
    'ob-nombre': 'nombre',
    'ob-apellido': 'apellido',
    'ob-tipo': 'tipo_documento',
    'ob-cedula': 'cedula',
    'ob-fnac': 'fecha_nacimiento',
    'ob-municipio': 'municipio',
    'ob-estado': 'estado',
    'ob-parroquia': 'parroquia',
}

# Columnas NOT NULL de public.afiliados (a 15/10/2026).
NO_NULOS = {
    'id': 'lo pone el cliente',
    'nombre': 'Google o el formulario',
    'apellido': 'Google o el formulario',
    'tipo_documento': 'select con valor por defecto',
    'cedula': 'el formulario',
    'email': 'viene de Supabase',
    'fecha_nacimiento': 'el formulario',
    'residencia': "el codigo pone 'Venezuela'",
    'color_acentu': 'default de la tabla: sky',
}

print('=== campos del formulario de ficha ===')
print('  %-16s %-9s %s' % ('campo', 'tipo', 'obligatorio'))
for cid, info in campos.items():
    print('  %-16s %-9s %s' % (cid, info['tipo'], 'SI' if info['obligatorio'] else 'NO'))

print()
print('=== campos que la base exige (NOT NULL) y el formulario NO pide ===')
problemas = []
for col, origen in NO_NULOS.items():
    if col == 'id' or col in ('email', 'residencia', 'color_acentu'):
        continue
    cid = next((k for k, v in COLUMNA.items() if v == col), None)
    if not cid:
        continue
    if not campos.get(cid, {}).get('obligatorio'):
        problemas.append((col, cid, origen))

if problemas:
    for col, cid, origen in problemas:
        print('  FALLO  %-18s campo %-14s es opcional en el formulario' % (col, cid))
        print('         y NOT NULL en la base. Si el usuario lo deja vacio,')
        print('         el INSERT falla y el alta se queda a medias.')
else:
    print('  ninguno')

print()
if problemas:
    print('%d campo(s) que pueden romper el alta.' % len(problemas))
    raise SystemExit(1)
print('El formulario cubre todo lo que la base exige.')