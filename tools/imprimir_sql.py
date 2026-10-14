# -*- coding: utf-8 -*-
"""Imprime el SQL de carga por bloques, listo para copiar.

    python tools/imprimir_sql.py [n]

Imprime un solo bloque (1..4) para no saturar la salida. Cada bloque es un
insert independiente y se puede aplicar por separado.
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, '_salida', 'parroquias.json')

NOMBRES = {'Anzoategui': 'Anzoátegui', 'Tachira': 'Táchira'}
BLOQUES = 4


def limpiar(p):
    p = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', p)
    p = re.sub(r'\{\{[^{}]*\}\}', '', p)
    p = re.sub(r'<[^>]+>', '', p)
    p = re.sub(r'\(Parroquia Capital\)', '', p, flags=re.I)
    p = re.sub(r'^Parroquia\s+', '', p, flags=re.I)
    p = re.sub(r'\s+', ' ', p).strip().strip(',').strip()
    m = re.match(r'^Capital\s+(.+)$', p, flags=re.I)
    return m.group(1).strip() if m else p


def comilla(s):
    return "'" + s.replace("'", "''") + "'"


def filas():
    datos = json.load(io.open(ENTRADA, encoding='utf-8'))
    vistos, out = set(), []
    for estado, items in datos.items():
        for it in items:
            mun = it['m'].strip()
            par = limpiar(it['p'])
            if not mun or not par:
                continue
            clave = (estado.lower(), mun.lower(), par.lower())
            if clave in vistos:
                continue
            vistos.add(clave)
            out.append((NOMBRES.get(estado, estado), mun, par))
    return out


f = filas()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
tam = (len(f) + BLOQUES - 1) // BLOQUES
trozo = f[(n - 1) * tam:n * tam]

print('insert into public.parroquias (estado, municipio, parroquia) values')
print(',\n'.join('  (%s, %s, %s)' % (comilla(a), comilla(b), comilla(c))
                 for a, b, c in trozo) + ';')
print()
print('-- bloque %d de %d (%d filas, %d en total)' % (n, BLOQUES, len(trozo), len(f)))