# -*- coding: utf-8 -*-
"""Comprueba que cuentas tienen RSS utilizable en las instancias de Nitter.

Diagnostico para decidir a quien anadir al feed antes de tocar nada. Los RSS de
Twitter solo se sirven desde mirrors de Nitter y se caen con frecuencia, asi
que conviene tener una lista de cuentas candidatas probadas.

Escribe tools/_salida/cuentas.txt.

    python tools/test_cuentas.py
"""
import urllib.request, re, time, random, io, os

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, '_salida', 'cuentas.txt')
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')
CUENTAS = ['ConVzlaComando', 'EdmundoGU', 'MariaCorinaYA', 'VenteVenezuela',
           'VenteCcs', 'Carlosafg_', 'MariaOropeza13', 'GPPantalamos',
           'vente_cabimas', 'HenryAlviarez']
MIRRORS = ['https://twiiit.com', 'https://nitter.meowing.monster',
           'https://nitter.tiekoetter.com']

out = io.open(SALIDA, 'w', encoding='utf-8')

for h in CUENTAS:
    ok = None
    for base in MIRRORS:
        try:
            req = urllib.request.Request('%s/%s/rss' % (base, h),
                                         headers={'User-Agent': UA})
            xml = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'replace')
            n = len(re.findall(r'<item>', xml))
            if n:
                # fecha del primer item
                m = re.search(r'<pubDate>(.*?)</pubDate>', xml, re.S)
                ok = (base, n, m.group(1).strip() if m else '?')
                break
        except Exception:
            continue
    out.write('%-20s %s\n' % (h, ok if ok else 'SIN RSS'))
    print(h, ok)
    time.sleep(1 + random.random())

out.close()