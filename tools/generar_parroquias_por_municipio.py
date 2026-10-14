# -*- coding: utf-8 -*-
"""Tercera fuente: la seccion "== Parroquias ==" de cada articulo de municipio.

Ultima fuente disponible para Lara y Tachira, cuyos anexos no traen la columna
de parroquias. Cada articulo de municipio ("Municipio Torres (Lara)") tiene una
seccion que enlaza a cada una de sus parroquias:

    == Parroquias ==
    * [[Parroquia Altagracia (Lara)|Parroquia Altagracia]]
    * [[Parroquia Antonio Diaz (Lara)|Parroquia Antonio Diaz]]
    ...

Se toma el texto de la seccion y se limpian las notas entre parentesis, que son
desambiguadores ("Chiquinquirá (Torres)" -> "Chiquinquirá").

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

# Estados sin anexo de parroquias, con los municipios que declaran Wikipedia.
ESTADOS = {
    'Lara': {
        'Andrés Eloy Blanco': 14, 'Jiménez': 11, 'Morán': 14, 'Palavecino': 14,
        'Torres': 18, 'Urdaneta': 20, 'Jiménez': 11,
    },
    'Táchira': {},
}

# Se pide la lista de municipios al propio estado para no fijarlos a mano.
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


def seccion_parroquias(wt):
    """Devuelve el texto entre '== Parroquias ==' y el siguiente encabezado."""
    m = re.search(r'==+\s*Parroquias\s*==+', wt, flags=re.I)
    if not m:
        return None
    resto = wt[m.end():]
    fin = re.search(r'\n==[^=]', resto)
    return resto[:fin.start()] if fin else resto


def nombres_de_parroquias(texto):
    out = []
    for linea in texto.split('\n'):
        l = linea.strip()
        if not l:
            continue
        if not re.match(r'^[*:;#]|^\[\[', l):
            continue
        # Cada vineta trae uno o mas enlaces a parroquias.
        for m in re.finditer(r'\[\[([^\]]*)\]\]', l):
            partes = m.group(1).split('|')
            etiqueta = partes[-1]
            etiqueta = re.sub(r'\s*\([^)]*\)', '', etiqueta)   # quita (Torres)
            etiqueta = re.sub(r'^Parroquia\s+', '', etiqueta, flags=re.I)
            etiqueta = etiqueta.strip().strip('.').strip()
            if not etiqueta:
                continue
            if 2 < len(etiqueta) < 55 and re.search(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]', etiqueta):
                out.append(etiqueta)
    vistos, res = set(), []
    for p in out:
        if p.lower() not in vistos:
            vistos.add(p.lower())
            res.append(p)
    return res


def municipios_del_estado(estado):
    """Busca 'Municipio X (Estado)' en Wikipedia."""
    d = pedir({'action': 'query', 'list': 'search',
               'srsearch': 'intitle:Municipio %s' % estado,
               'srlimit': '40', 'format': 'json'})
    nombres = []
    for x in d['query']['search']:
        t = x['title']
        m = re.match(r'^Municipio (.+?) \(%s\)$' % re.escape(estado), t)
        if m:
            nombres.append(m.group(1))
    return sorted(set(nombres))


resultado = {}
for estado in ESTADOS:
    muns = municipios_del_estado(estado)
    print('=== %s: %d municipios encontrados' % (estado, len(muns)))
    filas = []
    for mun in muns:
        wt = wikitext('Municipio %s (%s)' % (mun, estado))
        if not wt:
            time.sleep(1)
            continue
        sec = seccion_parroquias(wt)
        pq = nombres_de_parroquias(sec) if sec else []
        if pq:
            filas.append({'m': mun, 'p': p} for p in pq)
            print('   %-24s %2d  %s' % (mun, len(pq), ', '.join(pq[:4])))
        else:
            print('   %-24s SIN SECCION' % mun)
        time.sleep(2)
    items = [x for f in filas for x in f]
    print('   -> %d parroquias' % len(items))
    resultado[estado] = items

json.dump(resultado, io.open(os.path.join(SALIDA, 'parroquias_por_municipio.json'), 'w',
                             encoding='utf-8'), ensure_ascii=False, indent=1)
print()
for e, v in resultado.items():
    print('%s: %d parroquias en %d municipios' % (e, len(v), len(set(x['m'] for x in v))))