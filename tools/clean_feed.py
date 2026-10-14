# -*- coding: utf-8 -*-
"""Limpia el feed ampliado: fuera retweets, hilos sueltos y posts rancios.

Es el paso 2 de la cadena local. Reescribe tools/_salida/feed_ampliado.json.

    python tools/clean_feed.py
"""
import json, io, datetime, re, os

AQUI = os.path.dirname(os.path.abspath(__file__))
FEED_JSON = os.path.join(AQUI, '_salida', 'feed_ampliado.json')

d = json.load(io.open(FEED_JSON, encoding='utf-8'))
posts, avatares = d['posts'], d['avatares']
MES = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
       'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}

hoy = datetime.date(2026, 10, 14)
corte = hoy - datetime.timedelta(days=45)
print('corte:', corte)

mant = []
for p in posts:
    dia, mes, anio = p['date'].split()
    f = datetime.date(int(anio), MES[mes.lower()], int(dia))
    if f < corte:
        continue
    t = p['text'].strip()
    if re.match(r'^RT @\w+', t):                 # retweet
        continue
    if re.match(r'^\d+/\d+\s', t):               # fragmento de hilo sin el 1
        continue
    if len(t) < 25:
        continue
    mant.append(p)

print('antes:', len(posts), '-> despues:', len(mant))
for p in mant:
    print('  %-16s %s  L%-6s fotos=%d' % (p['author'], p['date'], p['likes'], len(p['photos'])))

# Avatar de respaldo si la API fallo
for h in ('MariaCorinaYA', 'VenteVenezuela', 'Carlosafg_', 'VenteCcs', 'HenryAlviarez'):
    if not avatares.get(h):
        avatares[h] = 'assets/avatar-marcorina.jpg'
        print('avatar fallback:', h)

d['posts'] = mant
json.dump(d, io.open(FEED_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('con foto:', sum(1 for p in mant if p['photos']),
      '| con likes:', sum(1 for p in mant if p['likes']))