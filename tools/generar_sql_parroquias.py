# -*- coding: utf-8 -*-
"""Genera el SQL para cargar las parroquias en Supabase y comprueba que los
datos sean presentables antes de tocar la base.

Sale de tools/_salida/parroquias.json, que produce generar_parroquias.py.

    python tools/generar_sql_parroquias.py
"""
import io
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, '_salida')
ENTRADA = os.path.join(SALIDA, 'parroquias.json')
SQL = os.path.join(SALIDA, 'parroquias.sql')

NOMBRES = {'Anzoategui': 'Anzoátegui', 'Tachira': 'Táchira'}


def limpiar_estado(e):
    return NOMBRES.get(e, e)


def limpiar_parroquia(p):
    p = p.strip()
    # Restos de marcado wiki que se colaron: "[[Parroquia Araira]]".
    p = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', p)
    p = re.sub(r'\{\{[^{}]*\}\}', '', p)
    p = re.sub(r'<[^>]+>', '', p)
    p = re.sub(r'\(Parroquia Capital\)', '', p, flags=re.I)
    p = re.sub(r'^Parroquia\s+', '', p, flags=re.I)
    p = re.sub(r'\s+', ' ', p).strip().strip(',').strip()
    # "Capital Bejuma" es la capital del municipio, no un nombre de parroquia
    # propio: el duplicado real es el municipio.
    m = re.match(r'^Capital\s+(.+)$', p, flags=re.I)
    if m:
        p = m.group(1).strip()
    return p


datos = json.load(io.open(ENTRADA, encoding='utf-8'))

vistos = set()
filas = []
descartadas = []

for estado, items in datos.items():
    est = limpiar_estado(estado)
    for it in items:
        mun = it['m'].strip()
        par = limpiar_parroquia(it['p'])
        if not mun or not par:
            continue
        clave = (est.lower(), mun.lower(), par.lower())
        if clave in vistos:
            continue
        vistos.add(clave)
        filas.append((est, mun, par))

# ---- control de calidad antes de escribir nada ---------------------------
problemas = []
for est, mun, par in filas:
    if re.search(r'\(Parroquia Capital\)|\[\[|\]\]|\{\{|\}\}', par):
        problemas.append('wiki sin limpiar: %s / %s / %s' % (est, mun, par))
    if len(par) > 55:
        problemas.append('nombre muy largo: %s / %s' % (est, par))
    if re.match(r'^(Capital|Estado|Municipio)\b', par, flags=re.I):
        problemas.append('prefijo raro: %s / %s' % (mun, par))
    if par.lower().startswith(mun.lower() + ' ') and par.lower() != mun.lower():
        pass  # legitimo: parroquia con el mismo nombre que el municipio

print('=== control de calidad ===')
print('filas a insertar: %d' % len(filas))
if problemas:
    print('PROBLEMAS: %d' % len(problemas))
    for p in problemas[:20]:
        print('  - %s' % p)
else:
    print('sin problemas de formato')

print()
print('=== por estado ===')
conteo = {}
for est, mun, par in filas:
    conteo[est] = conteo.get(est, 0) + 1
for est in sorted(conteo):
    muns = len(set(m for e, m, p in filas if e == est))
    print('  %-18s %3d parroquias / %2d municipios' % (est, conteo[est], muns))

if problemas:
    raise SystemExit('No se genera el SQL: hay datos que limpiar antes.')

# ---- SQL ------------------------------------------------------------------
def esc(s):
    return s.replace("'", "''")


lineas = [
    '-- Parroquias civiles de Venezuela (datos de los anexos de Wikipedia).',
    '-- Generado por tools/generar_sql_parroquias.py.',
    'insert into public.parroquias (estado, municipio, parroquia) values',
]
vals = ["  ('%s', '%s', '%s')" % (esc(e), esc(m), esc(p)) for e, m, p in filas]
lineas.append(',\n'.join(vals) + ';')
sql = '\n'.join(lineas)
io.open(SQL, 'w', encoding='utf-8', newline='\n').write(sql)

print()
print('SQL escrito en %s (%d KB)' % (SQL, len(sql.encode('utf-8')) // 1024))