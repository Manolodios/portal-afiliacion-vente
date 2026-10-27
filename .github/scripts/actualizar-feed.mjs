// Descarga publicaciones recientes de las cuentas de Vente Venezuela y
// reescribe SOLO el array FEED_POSTS de index.html.
//
// No se toca el resto del archivo: se busca el bloque delimitado por
// "const FEED_POSTS = [" y su cierre "        ];" y se sustituye. Si el bloque
// no aparece o el archivo no queda con la misma estructura, no se escribe nada
// (el workflow termina sin cambios y el portal sigue con el feed anterior).
import fs from 'node:fs';

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    + '(KHTML, like Gecko) Chrome/125.0 Safari/537.36';

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const DIAS_MAX = 45;           // publications mas antiguas que se conservan
const POR_CUENTA = 6;
const MAX_POSTS = 40;

// Cuentas de Vente Venezuela. Se agregar o quitan aqui.
const CUENTAS = [
    ['MariaCorinaYA', 'María Corina Machado', 'Presidente de Vente Venezuela'],
    ['VenteVenezuela', 'Vente Venezuela', 'Vente Venezuela'],
    ['Carlosafg_', 'Carlos Alfonzo Guarín', 'Coordinador Nacional de Defensa'],
    ['VenteCcs', 'Vente Distrito Capital', 'Vente Distrito Capital'],
    ['HenryAlviarez', 'Henry Alviarez', 'Coordinador Zulia'],
];

// Instancias Nitter que sirven el RSS. Se prueban en cascada.
const MIRRORS = [
    'https://twiiit.com',
    'https://nitter.meowing.monster',
    'https://nitter.tiekoetter.com',
    'https://nitter.privacydev.net',
    'https://nitter.esmailelbob.xyz',
];

const RUIDO = /^(video|image|photo|foto|imagen|animated_gif)(\s+\d+)?$/i;

function pause(ms) { return new Promise(r => setTimeout(r, ms)); }

async function get(url, intentos = 3) {
    for (let n = 0; n < intentos; n++) {
        try {
            const res = await fetch(url, {
                headers: { 'User-Agent': UA, 'Accept': 'application/rss+xml, application/xml, text/xml' },
                signal: AbortSignal.timeout(25000),
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return await res.text();
        } catch (e) {
            if (n === intentos - 1) throw e;
            await pause(2000 + n * 2000 + Math.random() * 1000);
        }
    }
}

function normUrl(u) {
    u = String(u || '').trim().split('#')[0];
    const m = u.match(/\/status\/(\d+)/);
    if (!m) return null;
    const handle = u.split('/status/')[0].replace(/^https?:\/\/[^/]+\//, '').replace(/\/$/, '');
    return { handle, id: m[1], link: `https://x.com/${handle}/status/${m[1]}` };
}

function limpiar(desc) {
    let t = String(desc || '').split('<blockquote')[0];
    t = t.replace(/<br\s*\/?>/gi, '\n').replace(/<\/p>/gi, '\n\n');
    t = t.replace(/<[^>]+>/g, '');
    t = t.replace(/\]{2,}>?/g, '');
    t = t.replace(/\s*https?:\/\/t\.co\/\S+/g, '');
    t = t.replace(/^RT by @\w+:\s*/i, '');
    t = t.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    return t.split('\n').map(l => l.trim())
        .filter(l => l && !RUIDO.test(l))
        .join('\n').replace(/[ \t]{2,}/g, ' ').trim();
}

async function rssDe(handle) {
    for (const base of MIRRORS) {
        try {
            const xml = await get(`${base}/${handle}/rss`, 2);
            if (xml.includes('<item>')) return xml;
        } catch { /* siguiente espejo */ }
    }
    return null;
}

async function api(path) {
    try {
        const txt = await get(`https://api.fxtwitter.com/${path}`, 2);
        return JSON.parse(txt);
    } catch { return null; }
}

// ---------------------------------------------------------------- descarga
const posts = [];
const avatares = {};
const vistos = new Set();
const corte = Date.now() - DIAS_MAX * 86400000;

for (const [handle, nombre, rol] of CUENTAS) {
    const xml = await rssDe(handle);
    if (!xml) { console.log(`[feed] ${handle}: sin RSS`); continue; }

    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].map(m => m[1]);
    console.log(`[feed] ${handle}: ${items.length} items`);

    let n = 0;
    for (const it of items) {
        if (n >= POR_CUENTA) break;
        const lm = it.match(/<link>([\s\S]*?)<\/link>/);
        const pm = it.match(/<pubDate>([\s\S]*?)<\/pubDate>/);
        const dm = it.match(/<description>([\s\S]*?)<\/description>/);
        const u = lm ? normUrl(lm[1]) : null;
        if (!u || u.handle !== handle || vistos.has(u.id)) continue;

        const fecha = pm ? new Date(pm[1].trim()) : null;
        if (!fecha || isNaN(fecha) || fecha.getTime() < corte) continue;

        let texto = limpiar(dm ? dm[1] : '');
        if (/^RT @\w+/.test(texto)) continue;       // retweets
        if (/^\d+\/\d+\s/.test(texto)) continue;     // fragmentos de hilo
        if (texto.length < 25) continue;
        if (texto.length > 400) texto = texto.slice(0, 400).replace(/\s\S*$/, '') + '...';

        vistos.add(u.id);
        posts.push({
            id: u.id, author: handle, text: texto,
            date: `${String(fecha.getUTCDate()).padStart(2, '0')} ${MESES[fecha.getUTCMonth()]} ${fecha.getUTCFullYear()}`,
            time: `${String(fecha.getUTCHours()).padStart(2, '0')}:${String(fecha.getUTCMinutes()).padStart(2, '0')}`,
            replies: 0, reposts: 0, likes: 0, photos: [], link: u.link,
        });
        n++;
    }
}

// Fotos, estadisticas reales y avatares reales (api.fxtwitter.com)
for (const p of posts) {
    const d = await api(`status/${p.id}`);
    const tw = (d && d.tweet) || {};
    p.likes = tw.likes || 0;
    p.reposts = tw.retweets || 0;
    p.replies = tw.replies || 0;
    const fotos = (((tw.media || {}).all) || [])
        .filter(m => m.type === 'photo' && m.url).slice(0, 4)
        .map(m => m.url.replace(/&amp;/g, '&'));
    if (fotos.length) p.photos = fotos;
    await pause(400);
}

for (const [handle] of CUENTAS) {
    const u = await api(handle);
    const url = ((u && u.user) || {}).avatar_url || '';
    avatares[handle] = url ? url.replace('_normal', '') : 'assets/avatar-marcorina.jpg';
    await pause(300);
}

if (!posts.length) {
    console.log('[feed] No se obtuvo ninguna publicacion. No se modifica index.html.');
    process.exit(0);
}

posts.sort((a, b) => (b.date + b.time).localeCompare(a.date + a.time));
const finales = posts.slice(0, MAX_POSTS);
console.log(`[feed] ${finales.length} publicaciones, ${finales.filter(p => p.photos.length).length} con foto`);

// ---------------------------------------------------------------- escritura
const ruta = 'index.html';
let html = fs.readFileSync(ruta, 'utf8');

const ini = html.indexOf('        // === FEED: publicaciones reales');
const arr = html.indexOf('const FEED_POSTS = [');
const cierre = html.indexOf('        ];', arr);
if (arr < 0 || cierre < 0) {
    console.error('[feed] No se encontro el bloque FEED_POSTS. Abortando sin cambios.');
    process.exit(1);
}
const desde = ini >= 0 && ini < arr ? ini : html.lastIndexOf('        //', arr);
if (desde < 0) {
    console.error('[feed] No se encontro el comentario del bloque. Abortando.');
    process.exit(1);
}

const esc = t => String(t).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n+/g, '\\n');

const lineas = [
    '        // === FEED: publicaciones reales y recientes ===',
    `        // Actualizado automaticamente el ${new Date().toISOString().slice(0, 10)} desde las`,
    '        // cuentas oficiales de Vente Venezuela, con estadisticas e imagenes reales.',
    '        // El RSS en vivo (RSS_FEEDS) se antepone a estas: el feed se actualiza solo.',
    '        const FEED_POSTS = [',
];
let previo = null;
finales.forEach((p, i) => {
    if (p.author !== previo) {
        lineas.push(`            // ${(CUENTAS.find(c => c[0] === p.author) || [, p.author])[1]}`);
        previo = p.author;
    }
    const fotos = p.photos.map(u => `"${u.replace(/&/g, '&amp;')}"`).join(', ');
    lineas.push(
        `            { id: "${p.id}", author: "${p.author}", text: "${esc(p.text)}", `
        + `date: "${p.date}", time: "${p.time}", replies: ${p.replies}, reposts: ${p.reposts}, `
        + `likes: ${p.likes}, photos: [${fotos}], link: "${p.link}" }${i < finales.length - 1 ? ',' : ''}`);
});
lineas.push('        ];');

html = html.slice(0, desde) + lineas.join('\n') + html.slice(cierre + '        ];'.length);

// LEADERS: se refrescan los avatares, se conserva el orden y los nombres.
const li = html.indexOf('        const LEADERS = [');
const lc = html.indexOf('        ];', li);
if (li >= 0 && lc >= 0) {
    const leaders = CUENTAS.map(([h, nombre, rol], i) => {
        const av = avatares[h] || 'assets/avatar-marcorina.jpg';
        return `            { handle: "${h}", name: "${nombre}", avatar: "${av}", verified: true, party: "${rol}" }`
            + (i < CUENTAS.length - 1 ? ',' : '');
    });
    // Se limpian TODOS los comentarios seguidos que haya justo antes de
// `const LEADERS = [`: si no, cada corrida anade otro y el archivo crece
// sin limite (4 lineas por dia). Los indices se vuelven a buscar tras cada
// recorte: `lc` queda obsoleto en cuanto se acorta el prefijo.
const CAB = '        const LEADERS = [';
const CIERRE = '\n        ];';
for (let guarda = 0; guarda < 50; guarda++) {
    const pos = html.indexOf(CAB);
    if (pos < 0) break;
    const inicioLinea = html.lastIndexOf('\n', pos - 1) + 1;   // de la linea CAB
    if (inicioLinea <= 0) break;
    const finPrevia = inicioLinea - 1;                          // fin de la linea anterior
    const inicioPrevia = html.lastIndexOf('\n', finPrevia - 1) + 1;
    if (!html.slice(inicioPrevia, finPrevia + 1).trim().startsWith('//')) break;
    html = html.slice(0, inicioPrevia) + html.slice(inicioLinea);
}
const li2 = html.indexOf(CAB);
const lc2 = html.indexOf(CIERRE, li2);
if (li2 >= 0 && lc2 >= 0) {
    html = html.slice(0, li2) + '        // Líderes y cuentas de Vente Venezuela\n' + CAB + '\n'
        + leaders.join('\n') + CIERRE + html.slice(lc2 + CIERRE.length);
}
}

fs.writeFileSync(ruta, html, 'utf8');
console.log(`[feed] index.html actualizado (${html.length} bytes)`);

// ------------------------------------------------------------- feed.json
// La misma lista en un archivo aparte. index.html solo se puede actualizar
// recargando, pero una pestaña ya abierta puede pedir feed.json cada cierto
// tiempo (mismo origen, sin CORS) y mostrar las publicaciones nuevas sin que
// el usuario tenga que refrescar. Sin marca de tiempo: si no hay posts nuevos
// el archivo no cambia y el workflow no hace commit.
fs.writeFileSync('feed.json', JSON.stringify({ posts: finales }, null, 2) + '\n', 'utf8');
console.log(`[feed] feed.json actualizado (${finales.length} publicaciones)`);