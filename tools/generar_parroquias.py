# -*- coding: utf-8 -*-
"""Descarga la lista real de parroquias por estado desde los anexos de
Wikipedia en espanol y genera el archivo JS que usa el portal.

Los anexos reproducen la division territorial oficial (Ley Organica del Poder
Publico Municipal). Los recuentos se contrastan con la tabla resumen de
"Parroquias de Venezuela"; si un estado queda muy por debajo de lo esperado se
marca como REVISAR en vez de darse por bueno.

    python tools/generar_parroquias.py

Escribe tools/_salida/parroquias.js con esta forma:

    const PARROQUIAS_POR_ESTADO = {
      "Zulia": [{ m: "Cabimas", p: "Ambrosio" }, ...],
      ...
    };
"""
import io
import json
import os
import re
import time
import urllib.request
import urllib.parse

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, '_salida')
os.makedirs(SALIDA, exist_ok=True)

API = 'https://es.wikipedia.org/w/api.php'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')

# Solo los estados que ofrece el formulario de afiliacion. "Otro" se queda
# fuera a proposito: no hay parroquias que ofrecer para el.
ESTADOS = [
    'Distrito Capital', 'Anzoategui', 'Carabobo',
    'Lara', 'Miranda', 'Tachira', 'Zulia',
]

# Recuento oficial esperado (tabla resumen de "Parroquias de Venezuela").
ESPERADO = {
    'Distrito Capital': 22, 'Anzoategui': 57, 'Carabobo': 38,
    'Lara': 57, 'Miranda': 155, 'Tachira': 66, 'Zulia': 110,
}


def pedir(params):
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def wikitext(titulo):
    datos = pedir({'action': 'parse', 'page': titulo,
                   'prop': 'wikitext', 'format': 'json', 'formatversion': '2'})
    if 'error' in datos:
        return None
    return datos['parse']['wikitext']


def limpiar(t):
    """Quita referencias, plantillas y marcado wiki."""
    t = re.sub(r'<ref[^>]*?/>', '', t, flags=re.S | re.I)
    t = re.sub(r'<ref[^>]*?>.*?</ref>', '', t, flags=re.S | re.I)
    for _ in range(5):
        nuevo = re.sub(r'\{\{[^{}]*\}\}', '', t, flags=re.S)
        if nuevo == t:
            break
        t = nuevo
    t = re.sub(r"'''?", '', t)
    t = re.sub(r'\[\[([^]|]*\|)?([^]]*)\]\]', r'\2', t)
    t = re.sub(r'<[^>]+>', '', t)
    return t.strip()


def nombre_de_parroquia(s):
    s = s.strip()
    s = re.sub(r'^(Parroquia|parroquia)\s+', '', s)
    return s.strip()


RUIDO = ('ancho', 'añadido', 'anadido', 'imagen', 'mapa', 'notas',
         'municipality', 'municipios', 'ver ', '-plantilla')


def es_ruido(s):
    b = s.strip().lower()
    return any(b.startswith(r) or b == r for r in RUIDO)


def parsear(wt):
    """Devuelve {municipio: [parroquias]} a partir del wikitext del anexo."""
    municipios = {}
    actual = 'General'

    def agregar(mun, valores):
        if not mun or es_ruido(mun):
            return
        lst = municipios.setdefault(mun, [])
        for v in valores:
            if v and not es_ruido(v):
                lst.append(v)

    for linea in wt.split('\n'):
        cruda = linea.strip()
        if not cruda:
            continue

        # Titulo de seccion: = Municipio Cabimas =  o  == Cabimas ==
        m = re.match(r'^=+\s*(.+?)\s*=+$', cruda)
        if m:
            nombre = nombre_de_parroquia(limpiar(m.group(1)))
            actual = re.sub(r'^Municipio\s+', '', nombre, flags=re.I).strip() or 'General'
            municipios.setdefault(actual, [])
            continue

        # Fila de tabla: | municipio || parroquia || parroquia ...
        if cruda.startswith('|') and not cruda.startswith('|-') and not cruda.startswith('|}'):
            crudas = cruda.strip('|').split('||')
            celdas = [nombre_de_parroquia(limpiar(c)) for c in crudas]
            celdas = [c for c in celdas if c and c not in ('-', '—', 'municipalities')]
            if not celdas:
                continue
            agregar(celdas[0], celdas[1:])
            continue

        # Lista con vinetas o numeracion: * Ambrosio
        m = re.match(r'^[*:;#]+\s*(.+)$', cruda)
        if m:
            agregar(actual, [nombre_de_parroquia(limpiar(m.group(1)))])
            continue

    # Deduplicar y descartar valores que no son nombres de parroquia.
    limpio = {}
    for mun, vals in municipios.items():
        visto = set()
        out = []
        for v in vals:
            if len(v) > 55 or es_ruido(v):
                continue
            clave = v.lower()
            if clave in visto:
                continue
            visto.add(clave)
            out.append(v)
        if out:
            limpio[mun] = out
    return limpio


def titulo_anexo(estado):
    if estado == 'Distrito Capital':
        return 'Anexo:Parroquias del Distrito Capital'
    return 'Anexo:Parroquias del estado %s' % estado


resultado = {}
informe = []

for estado in ESTADOS:
    wt = wikitext(titulo_anexo(estado))
    if not wt:
        informe.append((estado, 0, ESPERADO[estado], 'SIN PAGINA'))
        print('%-18s SIN PAGINA' % estado)
        continue

    datos = parsear(wt)
    total = sum(len(v) for v in datos.values())
    esperado = ESPERADO[estado]
    marca = 'OK' if total >= esperado * 0.9 else ('REVISAR' if total >= esperado * 0.7 else 'FALLO')

    informe.append((estado, total, esperado, marca))
    resultado[estado] = [{'m': m, 'p': p}
                         for m in sorted(datos)
                         for p in datos[m]]
    print('%-18s %4d parroquias / %3d municipios   esperado %3d   %s'
          % (estado, total, len(datos), esperado, marca))
    time.sleep(1)


def nombre_visible(estado):
    """Zulia, Táchira... la clave interna es sin acentos."""
    return {'Anzoategui': 'Anzoátegui', 'Tachira': 'Táchira'}.get(estado, estado)


lineas = [
    '// Parroquias civiles de Venezuela, por estado y municipio.',
    '// Fuente: anexos de "Parroquias de Venezuela" (Wikipedia en espanol),',
    '// que reproducen la division territorial oficial.',
    '// Generado por tools/generar_parroquias.py el ' + time.strftime('%Y-%m-%d') + '.',
    '// El formulario de afiliacion filtra por este mapa, asi que nunca se',
    '// ofrecen parroquias de un estado que no sea el elegido.',
    'const PARROQUIAS_POR_ESTADO = {',
]
for estado, items in resultado.items():
    lineas.append('    "%s": [' % nombre_visible(estado))
    for it in items:
        mun = it['m'].replace('"', "'").replace('\n', ' ')
        par = it['p'].replace('"', "'").replace('\n', ' ')
        lineas.append('        { m: "%s", p: "%s" },' % (mun, par))
    lineas.append('    ],')
lineas.append('};')

ruta_js = os.path.join(SALIDA, 'parroquias.js')
io.open(ruta_js, 'w', encoding='utf-8', newline='\n').write('\n'.join(lineas))
json.dump(resultado, io.open(os.path.join(SALIDA, 'parroquias.json'), 'w',
                             encoding='utf-8'), ensure_ascii=False, indent=1)

print()
print('=== resumen ===')
total = 0
fallos = 0
for estado, t, e, ok in informe:
    print('  %-18s %4d / %4d   %s' % (estado, t, e, ok))
    total += t
    if ok == 'FALLO':
        fallos += 1
print('  %-18s %4d parroquias' % ('TOTAL', total))
print()
print('escrito %s' % ruta_js)
if fallos:
    print('ATENCION: %d estados con datos incompletos.' % fallos)