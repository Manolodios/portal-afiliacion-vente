# -*- coding: utf-8 -*-
"""Comprueba que todos los recursos externos que referencia index.html
responden 200: scripts, hojas de estilo, CDN.

Un 404 aqui no rompe la pagina de forma visible: solo ensucia la consola y
deja la parte afectada sin estilo o sin funcionar.
"""
import io
import os
import re
import urllib.request
import urllib.error

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')

html = io.open(INDEX, encoding='utf-8').read()

recursos = set()
recursos |= set(re.findall(r'src="([^"]+)"', html))
recursos |= set(re.findall(r"src='([^']+)'", html))
recursos |= set(re.findall(r'href="([^"]+\.(?:js|mjs))"', html))
recursos |= set(re.findall(r"href='([^']+\.(?:js|mjs))'", html))

BASE = 'https://manolodios.github.io/portal-afiliacion-vente/'

malos = []


def es_plantilla(r):
    """Un ${...} es una interpolacion de JavaScript, no una URL: no se pide."""
    return '${' in r or '+ dataUrl' in r or r.startswith("' +")


print('=== recursos referenciados (%d) ===' % len(recursos))
for r in sorted(recursos):
    if r.startswith('#') or r.startswith('data:') or es_plantilla(r):
        continue
    url = r if r.startswith('http') else BASE + r.lstrip('./')
    if not url.startswith('http'):
        print('  local (no se comprueba): %s' % r)
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA}, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=25)
        print('  %-3s  %s' % (resp.status, r[:95]))
        if resp.status >= 400:
            malos.append((r, resp.status))
    except urllib.error.HTTPError as e:
        print('  %-3s  %s' % (e.code, r[:95]))
        malos.append((r, e.code))
    except Exception as e:
        print('  ERR  %s  (%s)' % (r[:80], e))

print()
if malos:
    print('FALLAN %d recursos:' % len(malos))
    for r, c in malos:
        print('  %s  ->  %s' % (c, r))
else:
    print('OK: todos los recursos responden.')
raise SystemExit(1 if malos else 0)