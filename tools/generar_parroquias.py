# -*- coding: utf-8 -*-
"""Descarga la lista real de parroquias por estado y genera la tabla para Supabase.

Fuente: anexos de "Parroquias de Venezuela" (Wikipedia en espanol), que
reproducen la division territorial oficial.

El formato de los anexos es una lista donde el nombre de la parroquia aparece
como alias de un enlace wiki:

    # [[Parroquia Isla de Toas (...) | Parroquia Isla de Toas,]] El Toro (Parroquia Capital)

Es decir, en el enlace va la PARROQUIA y despues, fuera del enlace, la capital.
Un parser ingenuo se queda con las dos cosas pegadas y produce basura como
"Isla de Toas, El Toro (Parroquia Capital)". Este lo separa.

    python tools/generar_parroquias.py

Escribe tools/_salida/parroquias.json
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

# Estados que ofrece el formulario de afiliacion.
ESTADOS = ['Distrito Capital', 'Anzoategui', 'Carabobo',
           'Lara', 'Miranda', 'Tachira', 'Zulia']

ESPERADO = {
    'Distrito Capital': 22, 'Anzoategui': 57, 'Carabobo': 38,
    'Lara': 57, 'Miranda': 155, 'Tachira': 66, 'Zulia': 110,
}


def pedir(params, intentos=4):
    url = API + '?' + urllib.parse.urlencode(params)
    for n in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            return json.loads(urllib.request.urlopen(req, timeout=45).read())
        except Exception:
            if n == intentos - 1:
                raise
            time.sleep(8 * (n + 1))


def wikitext(titulo):
    d = pedir({'action': 'parse', 'page': titulo, 'prop': 'wikitext',
               'format': 'json', 'formatversion': '2'})
    return None if 'error' in d else d['parse']['wikitext']


def buscar_anexo(estado):
    """Devuelve el titulo del anexo de parroquias de ese estado."""
    candidatos = ['Anexo:Parroquias del estado %s' % estado,
                  'Anexo:Parroquias del %s' % estado]
    if estado == 'Distrito Capital':
        candidatos.insert(0, 'Anexo:Parroquias del Distrito Capital')
    for c in candidatos:
        try:
            d = pedir({'action': 'query', 'titles': c, 'format': 'json'})
            paginas = d.get('query', {}).get('pages', {})
            for v in paginas.values():
                if 'missing' not in v:
                    return c
        except Exception:
            pass
        time.sleep(2)
    # Ultimo recurso: buscar por prefijo
    try:
        d = pedir({'action': 'query', 'list': 'search',
                   'srsearch': 'intitle:Parroquias %s' % estado,
                   'srlimit': '8', 'format': 'json'})
        for x in d['query']['search']:
            if x['title'].startswith('Anexo:Parroquias'):
                return x['title']
    except Exception:
        pass
    return None


def quitar_enlaces(t):
    """[[destino|alias]] -> alias. [[destino]] -> destino."""
    def sub(m):
        partes = m.group(1).split('|')
        return partes[-1].strip()
    return re.sub(r'\[\[([^\]]+)\]\]', sub, t)


def limpiar(t):
    t = re.sub(r'<ref[^>]*?/>', '', t, flags=re.S | re.I)
    t = re.sub(r'<ref[^>]*?>.*?</ref>', '', t, flags=re.S | re.I)
    for _ in range(5):
        n = re.sub(r'\{\{[^{}]*\}\}', '', t, flags=re.S)
        if n == t:
            break
        t = n
    t = quitar_enlaces(t)
    t = re.sub(r"'''?", '', t)
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ', t).strip()


RUIDO_TITULO = ('ancho', 'añadido', 'imagen', 'mapa', 'notas', 'referencias')


def es_ruido(s):
    b = s.strip().lower()
    return any(b.startswith(r) for r in RUIDO_TITULO) or len(b) < 3


def nombre_municipio(crudo):
    """'=== [[Municipio Baralt (Zulia, Venezuela)|Municipio Baralt]] (Capital: X) ==='
       -> 'Baralt'
       '=== Municipio Almirante Padilla (Capital: El Toro) ===' -> 'Almirante Padilla'"""
    t = limpiar(crudo)
    t = re.sub(r'\(Capital:.*?\)', '', t, flags=re.I)
    t = re.sub(r'\(.*?\)', '', t)
    t = t.strip().rstrip('=')
    t = re.sub(r'^Municipio\s+', '', t, flags=re.I).strip()
    return t


def nombre_parroquia(crudo):
    """'# [[Parroquia Isla de Toas (...)|Parroquia Isla de Toas,]] El Toro (Parroquia Capital)'
       -> 'Isla de Toas'
    Si el nombre no esta en el alias, se descarta lo que quede tras el cierre."""
    # El nombre de la parroquia es el alias del primer enlace.
    m = re.search(r'\[\[[^\]]*\|([^\]]*)\]\]', crudo)
    if m:
        cand = m.group(1)
    else:
        # Sin enlace: se quita la viñeta y el '(Parroquia Capital)'.
        cand = re.sub(r'^\s*[*:;#]+\s*', '', crudo)
        cand = re.sub(r'\(Parroquia Capital\)', '', cand, flags=re.I)
        cand = re.sub(r'\s+', ' ', cand).strip()
    cand = cand.strip().strip(',').strip()
    cand = re.sub(r'^Parroquia\s+', '', cand, flags=re.I)
    return cand.strip().strip(',').strip()


def cuenta_del_anexo(wt):
    """El propio anexo dice cuantas parroquias tiene el estado. Es mas fiable
    que una tabla resumen externa: el de Miranda, por ejemplo, aclara que tiene
    54 y no las 155 de la tabla, que estaba desactualizada."""
    m = re.search(r'por\s+(\d+)\s+\[\[?[^\]]*parroquias', wt, flags=re.I)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s+parroquias', wt, flags=re.I)
    return int(m.group(1)) if m else None


def parsear(wt):
    out = {}
    actual = None
    for linea in wt.split('\n'):
        cruda = linea.strip()
        if not cruda:
            continue

        # Encabezado de municipio: === ... ===
        m = re.match(r'^=+\s*(.+?)\s*=+$', cruda)
        if m:
            nombre = nombre_municipio(m.group(1))
            actual = nombre if nombre and not es_ruido(nombre) else None
            continue

        # Linea de parroquia
        if re.match(r'^[*:;#]+\s', cruda) or cruda.startswith('|'):
            if actual is None:
                continue
            # Solo la parte anterior al primer "]]" puede contener el nombre.
            corte = cruda
            fin = corte.find(']]')
            if fin > 0:
                corte = corte[:fin + 2]
            nombre = nombre_parroquia(corte)
            if nombre and not es_ruido(nombre) and len(nombre) <= 55:
                out.setdefault(actual, [])
                if nombre.lower() not in [x.lower() for x in out[actual]]:
                    out[actual].append(nombre)
    return out


resultado = {}
informe = []

for estado in ESTADOS:
    titulo = buscar_anexo(estado)
    if not titulo:
        informe.append((estado, 0, ESPERADO[estado], 'SIN ANEXO'))
        print('%-18s NO SE ENCONTRO EL ANEXO' % estado)
        continue
    wt = wikitext(titulo)
    if not wt:
        informe.append((estado, 0, ESPERADO[estado], 'SIN PAGINA'))
        continue
    datos = parsear(wt)
    total = sum(len(v) for v in datos.values())
    # La cifra buena es la que declara el propio anexo.
    esp = cuenta_del_anexo(wt) or ESPERADO[estado]
    if total == esp:
        marca = 'OK'
    elif abs(total - esp) <= 2:
        marca = 'REVISAR'
    else:
        marca = 'FALLO'
    informe.append((estado, total, esp, marca))
    resultado[estado] = [{'m': m, 'p': p} for m in sorted(datos) for p in datos[m]]
    print('%-18s %4d / %4d  %2d municipios  %s   [%s]'
          % (estado, total, esp, len(datos), marca, titulo))
    time.sleep(2)

json.dump(resultado, io.open(os.path.join(SALIDA, 'parroquias.json'), 'w',
                             encoding='utf-8'), ensure_ascii=False, indent=1)

print()
print('=== resumen ===')
tot = 0
for e, t, x, ok in informe:
    print('  %-18s %4d / %4d  %s' % (e, t, x, ok))
    tot += t
print('  %-18s %4d parroquias' % ('TOTAL', tot))

# Muestra de control: si hay basura como "X, Y (Parroquia Capital)" se ve.
print()
print('=== control de calidad (5 primeras de cada estado) ===')
for e, items in resultado.items():
    print('  %s:' % e)
    for it in items[:5]:
        marca = '  <-- REVISAR' if re.search(r'\(Parroquia Capital\)|,\s*\w.*,', it['p']) else ''
        print('     %-22s | %s%s' % (it['m'], it['p'], marca))