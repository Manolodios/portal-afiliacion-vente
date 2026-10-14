# -*- coding: utf-8 -*-
"""Segunda fuente de parroquias: la tabla de municipios.

Para los estados sin anexo propio, la pagina "Anexo:Municipios del estado X"
trae una tabla con columnas:

    | [[Municipio Anaco|Anaco]] || [[Anaco (Ciudad)|Anaco]] || Anaco, Buena Vista y San Joaquín || 140.563 hab. || ...

La tercera celda es la lista COMPLETA de parroquias del municipio, separada por
comas y por " y ". No hay que deducir nada: basta con partir esa celda.

    python tools/generar_parroquias_municipios.py
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
UA = 'Mozilla/5.0 (herramientas/1.0)'

ESTADOS = ['Anzoategui', 'Lara', 'Tachira']
NOMBRES = {'Anzoategui': 'Anzoátegui', 'Tachira': 'Táchira'}

RUIDO = re.compile(r'hab\.?$|km|\[Archivo|\.svg|\{\{|\}\}|bgcolor|colspan|rowspan', re.I)


def pedir(params, intentos=4):
    url = API + '?' + urllib.parse.urlencode(params)
    for n in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            return json.loads(urllib.request.urlopen(req, timeout=45).read())
        except Exception:
            if n == intentos - 1:
                raise
            time.sleep(6 * (n + 1))


def wikitext(t):
    d = pedir({'action': 'parse', 'page': t, 'prop': 'wikitext',
               'format': 'json', 'formatversion': '2'})
    return None if 'error' in d else d['parse']['wikitext']


def limpiar(t):
    t = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', t)
    t = re.sub(r'<ref[^>]*?/>', '', t, flags=re.S | re.I)
    t = re.sub(r'<ref[^>]*?>.*?</ref>', '', t, flags=re.S | re.I)
    for _ in range(5):
        n = re.sub(r'\{\{[^{}]*\}\}', '', t, flags=re.S)
        if n == t:
            break
        t = n
    t = re.sub(r"'''?", '', t)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def partir_parroquias(celda):
    """'Anaco, Buena Vista y San Joaquín' -> las tres."""
    c = limpiar(celda)
    if not c or RUIDO.search(c):
        return []
    # Se parte por comas y por la conjuncion " y ".
    trozos = re.split(r'\s*,?\s+y\s+|,\s*', c)
    out = []
    for t in trozos:
        t = t.strip().strip('.').strip()
        if not t or RUIDO.search(t):
            continue
        if len(t) < 3 or len(t) > 45:
            continue
        if not re.search(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]', t):
            continue
        out.append(t)
    return out


def extraer(wt):
    out = {}
    for linea in wt.split('\n'):
        if not linea.strip().startswith('|'):
            continue
        if '||' not in linea:
            continue
        celdas = [c.strip() for c in linea.strip().strip('|').split('||')]
        if len(celdas) < 3:
            continue
        # La primera celda suele ser el rotulo de fila; el municipio es la
        # primera que parece un nombre propio, y las parroquias la siguiente
        # que contiene separadores.
        nombres = [limpiar(c) for c in celdas]
        municipio = None
        for n in nombres:
            if n and not RUIDO.search(n) and 'bgcolor' not in n:
                municipio = n
                break
        if not municipio or not re.match(r'^[A-ZÁÉÍÓÚÑ]', municipio):
            continue
        # Filas de leyenda o de encabezado de la tabla, que se colan como si
        # fueran municipios (p.ej. "Estado Anzoategui" con la fila del titulo).
        if re.match(r'^(Estado|Municipio|Entidad|Provincia)\b', municipio, flags=re.I):
            continue
        if len(municipio.split()) > 4:
            continue
        # La celda de parroquias: la que mas nombres produce.
        mejor, cuantos = [], 0
        for c in celdas:
            pq = partir_parroquias(c)
            if len(pq) > cuantos:
                mejor, cuantos = pq, len(pq)
        if cuantos:
            out.setdefault(municipio, [])
            for p in mejor:
                if p.lower() not in [x.lower() for x in out[municipio]]:
                    out[municipio].append(p)
    return out


resultado = {}
for estado in ESTADOS:
    titulo = 'Anexo:Municipios del estado %s' % NOMBRES.get(estado, estado)
    wt = wikitext(titulo)
    if not wt:
        print('%-12s NO EXISTE' % estado)
        continue
    datos = extraer(wt)
    total = sum(len(v) for v in datos.values())
    print('%-12s %3d parroquias en %2d municipios' % (estado, total, len(datos)))
    for mun, pq in list(datos.items())[:4]:
        print('      %-20s %s' % (mun, ', '.join(pq[:6])))
    resultado[NOMBRES.get(estado, estado)] = [
        {'m': mun, 'p': p} for mun in sorted(datos) for p in datos[mun]]
    time.sleep(3)

json.dump(resultado, io.open(os.path.join(SALIDA, 'parroquias_municipios.json'), 'w',
                             encoding='utf-8'), ensure_ascii=False, indent=1)
print()
print('total:', sum(len(v) for v in resultado.values()))