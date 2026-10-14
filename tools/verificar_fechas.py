# -*- coding: utf-8 -*-
"""Comprueba que la fecha de cada publicacion del feed corresponde realmente
a su id de snowflake de Twitter: (id >> 22) + 1288834974657 = fecha UTC.

Es la prueba de que los posts no estan inventados: si alguien escribiera una
fecha a mano que no cuadra con el id, aqui se veria.

    python tools/verificar_fechas.py
"""
import io
import os
import re
import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
         'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

html = io.open(INDEX, encoding='utf-8').read()
ini = html.find('const FEED_POSTS = [')
bloque = html[ini:html.find('\n        ];', ini)]

POSTS = re.compile(
    r'\{ id: "(\d+)", author: "(\w+)", text: ".*?", '
    r'date: "(\d\d) (\w{3}) (\d{4})", time: "(\d\d):(\d\d)", '
    r'replies: (\d+), reposts: (\d+), likes: (\d+)')

fallos = 0
vistos = POSTS.findall(bloque)
print('publicaciones encontradas: %d' % len(vistos))

for pid, autor, dia, mes, anio, hh, mm, repl, rt, likes in vistos:
    ts = ((int(pid) >> 22) + 1288834974657) / 1000.0
    real = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)

    esperado_dia = '%02d' % real.day
    esperado_mes = MESES[real.month - 1]
    esperado_anio = str(real.year)
    esperado_hora = '%02d' % real.hour
    esperado_min = '%02d' % real.minute

    coincide = (dia == esperado_dia and mes == esperado_mes
                and anio == esperado_anio
                and hh == esperado_hora and mm == esperado_min)
    if not coincide:
        fallos += 1

    print('  %-16s %s %s  %s:%s UTC  L%-6s %s'
          % (autor, esperado_dia, esperado_mes + ' ' + esperado_anio,
             esperado_hora, esperado_min, likes,
             '' if coincide else '  <-- DESCUADRE (dice %s/%s/%s %s:%s)'
             % (dia, mes, anio, hh, mm)))

    if not (pid.isdigit() and len(pid) >= 18):
        fallos += 1
        print('      id invalido')

if not vistos:
    print('No se encontro ninguna publicacion: revisa el bloque FEED_POSTS.')
    raise SystemExit(1)

print()
if fallos:
    print('%d publicaciones con la fecha descuadrada respecto al id.' % fallos)
    raise SystemExit(1)
print('Todas las fechas cuadran con el id de snowflake. Datos autenticos.')