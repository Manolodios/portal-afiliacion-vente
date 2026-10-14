# -*- coding: utf-8 -*-
"""Descarga las publicaciones recientes de las cuentas de Vente Venezuela con
sus estadisticas, imagenes y avatares reales.

Es el paso 1 de la cadena local que reconstruye el feed:
    build_feed_wide.py -> clean_feed.py -> gen_feed_wide.py -> apply_feed.py

Escribe tools/_salida/feed_ampliado.{json,txt}. Para publicarlo automaticamente
cada 6 horas en GitHub Actions usa .github/scripts/actualizar-feed.mjs, que hace
lo mismo en un solo paso.

    python tools/build_feed_wide.py
"""
import urllib.request, re, json, io, html, time, random, os
from email.utils import parsedate_to_datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, '_salida')
FEED_JSON = os.path.join(SALIDA, 'feed_ampliado.json')
FEED_TXT = os.path.join(SALIDA, 'feed_ampliado.txt')
os.makedirs(SALIDA, exist_ok=True)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0 Safari/537.36')
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
MIRRORS = ['https://twiiit.com', 'https://nitter.meowing.monster', 'https://nitter.tiekoetter.com']

# Solo cuentas de Vente Venezuela (requisito del portal).
CUENTAS = [
    ('MariaCorinaYA', 'María Corina Machado', True),
    ('VenteVenezuela', 'Vente Venezuela', True),
    ('Carlosafg_', 'Carlos Alfonzo Guarín', True),
    ('VenteCcs', 'Vente Distrito Capital', True),
    ('HenryAlviarez', 'Henry Alviarez', True),
]

RUIDO = re.compile(r'^(video|image|photo|foto|imagen|animated_gif)(\s+\d+)?$', re.I)


def fetch(url, intentos=3):
    for n in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            return urllib.request.urlopen(req, timeout=25).read()
        except Exception:
            if n == intentos - 1:
                raise
            time.sleep(2 + n * 2 + random.random())


def norm_url(u):
    u = (u or '').strip().split('#')[0]
    m = re.search(r'/status/(\d+)', u)
    if not m:
        return None, None, None
    h = u.split('/status/')[0].rstrip('/').split('/')[-1]
    return h, m.group(1), 'https://x.com/%s/status/%s' % (h, m.group(1))


def get_rss(h):
    for base in MIRRORS:
        try:
            xml = fetch('%s/%s/rss' % (base, h), intentos=2).decode('utf-8', 'replace')
            if '<item>' in xml:
                return xml
        except Exception:
            continue
    return None


posts, vistos = [], set()
avatares = {}

for handle, nombre, _ in CUENTAS:
    xml = get_rss(handle)
    if not xml:
        print('RSS ERROR', handle)
        continue
    items = re.findall(r'<item>(.*?)</item>', xml, re.S)
    print('%-16s items=%d' % (handle, len(items)))
    n = 0
    for it in items:
        if n >= 6:            # 6 por cuenta: feed equilibrado
            break
        lm = re.search(r'<link>(.*?)</link>', it, re.S)
        pm = re.search(r'<pubDate>(.*?)</pubDate>', it, re.S)
        dm = re.search(r'<description>(.*?)</description>', it, re.S)
        h, tid, link = norm_url(lm.group(1) if lm else '')
        if not link or h != handle or tid in vistos:
            continue
        vistos.add(tid)
        desc = re.split(r'<blockquote', dm.group(1) if dm else '')[0]
        desc = re.sub(r'<br\s*/?>', '\n', desc, flags=re.I)
        desc = re.sub(r'</p>', '\n\n', desc, flags=re.I)
        txt = re.sub(r'\]\]>', '', re.sub(r'<[^>]+>', '', desc))
        txt = re.sub(r'^RT by @\w+:\s*', '', html.unescape(txt), flags=re.I)
        txt = re.sub(r'\s*https?://t\.co/\S+', '', txt)
        txt = '\n'.join(l.strip() for l in txt.split('\n')
                        if l.strip() and not RUIDO.match(l.strip()))
        txt = re.sub(r'[ \t]{2,}', ' ', txt).strip()
        if len(txt) > 400:
            txt = txt[:400].rsplit(' ', 1)[0] + '...'
        if not txt:
            continue
        pub = parsedate_to_datetime(pm.group(1).strip())
        posts.append({
            'id': tid, 'author': handle, 'text': txt,
            'date': '%02d %s %d' % (pub.day, MESES[pub.month - 1], pub.year),
            'time': '%02d:%02d' % (pub.hour, pub.minute),
            'replies': 0, 'reposts': 0, 'likes': 0, 'photos': [], 'link': link})
        n += 1

print('posts:', len(posts))

# Fotos + estadisticas + avatar real
for p in posts:
    try:
        d = json.loads(fetch('https://api.fxtwitter.com/status/%s' % p['id'], intentos=2).decode('utf-8', 'replace'))
        tw = d.get('tweet') or {}
        p['likes'] = tw.get('likes') or 0
        p['reposts'] = tw.get('retweets') or 0
        p['replies'] = tw.get('replies') or 0
        fotos = [m['url'].replace('&amp;', '&')
                 for m in ((tw.get('media') or {}).get('all') or [])
                 if m.get('type') == 'photo' and m.get('url')]
        if fotos:
            p['photos'] = fotos[:4]
    except Exception:
        pass
    time.sleep(0.45)

for handle, nombre, _ in CUENTAS:
    try:
        u = json.loads(fetch('https://api.fxtwitter.com/%s' % handle, intentos=2).decode('utf-8', 'replace'))
        avatares[handle] = ((u.get('user') or {}).get('avatar_url') or '').replace('_normal', '')
        print('%-16s avatar=%s' % (handle, avatares[handle]))
    except Exception as e:
        avatares[handle] = ''
        print('%-16s avatar FAIL' % handle)
    time.sleep(0.4)

posts.sort(key=lambda p: (p['date'][-4:], p['date'][3:6], p['date'][:2], p['time']), reverse=True)
json.dump({'posts': posts, 'avatares': avatares},
          io.open(FEED_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with io.open(FEED_TXT, 'w', encoding='utf-8') as f:
    for p in posts:
        f.write('%-16s %s %s | L%-6s RT%-5s R%-4s fotos=%d\n  %s\n' % (
            p['author'], p['date'], p['time'], p['likes'], p['reposts'], p['replies'],
            len(p['photos']), p['text'][:110].replace('\n', ' ')))
print('OK -> %s' % FEED_JSON)