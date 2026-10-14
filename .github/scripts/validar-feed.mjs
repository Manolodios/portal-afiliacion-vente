// Comprueba que index.html sigue siendo valido tras actualizar el feed.
// Sale con codigo 1 si algo quedo roto, para que el workflow no publique.
import fs from 'node:fs';

const html = fs.readFileSync('index.html', 'utf8');
let fallos = 0;
const ok = (c, m) => { console.log((c ? 'OK   ' : 'FALLO') + ' ' + m); if (!c) fallos++; };

// 1. Estructura basica
ok(html.includes('<!DOCTYPE html>'), 'el documento existe');
ok(html.includes('const FEED_POSTS = ['), 'FEED_POSTS declarado');

// 2. Se ejecuta el script del feed en un contexto minimo (jsdom con
//    runScripts:'outside-only' no corre los scripts en linea).
const scripts = [...html.matchAll(/<script(?![^>]*type="module")[^>]*>([\s\S]*?)<\/script>/g)]
    .map(m => m[1]);
const fuente = scripts.find(s => s.includes('const FEED_POSTS = ['));
ok(!!fuente, 'el bloque de script del feed esta presente');

const ctx = {};
globalThis.window = globalThis;
globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
globalThis.document = { getElementById: () => null, querySelectorAll: () => [] };
// navigator ya existe en Node 22 y es de solo lectura: no se intenta asignar.
try {
    new Function('exports', fuente + `
        exports.FEED_POSTS = FEED_POSTS;
        exports.LEADERS = LEADERS;
        exports.TOPICS_BASE = TOPICS_BASE;
        exports.topicsEfectivos = topicsEfectivos;
        exports.escapeHtml = escapeHtml;
        exports.urlSegura = urlSegura;
    `)(ctx);
    ok(true, 'el script del feed se ejecuta sin errores');
} catch (e) {
    ok(false, 'el script del feed se ejecuta sin errores: ' + e.message);
}

const posts = ctx.FEED_POSTS || [];
ok(Array.isArray(posts), 'FEED_POSTS es un array');
ok(posts.length > 0, 'hay publicaciones (' + posts.length + ')');
ok(Array.isArray(ctx.LEADERS), 'LEADERS es un array');
ok(Array.isArray(ctx.TOPICS_BASE), 'TOPICS_BASE es un array');
ok(typeof ctx.topicsEfectivos === 'function', 'topicsEfectivos disponible');

// 3. Cada publicacion es coherente
let mal = 0, conFoto = 0, conLikes = 0;
for (const p of posts) {
    if (!/^\d+$/.test(p.id)) mal++;
    if (!p.link.endsWith('/' + p.id)) mal++;
    if (!/^https:\/\/x\.com\/[A-Za-z0-9_]+\/status\/\d+$/.test(p.link)) mal++;
    if (!p.text || p.text.length < 20) mal++;
    if (/\]\]>|\n\s*(Video|Image)\s*\n/.test(p.text)) mal++;
    if ((p.photos || []).some(u => !u.startsWith('http'))) mal++;
    if (p.photos && p.photos.length) conFoto++;
    if (p.likes > 0) conLikes++;
    if (!(ctx.LEADERS || []).some(l => l.handle === p.author)) mal++;  // autor sin avatar
}
ok(mal === 0, 'todas las publicaciones son coherentes' + (mal ? ' (' + mal + ' fallos)' : ''));
ok(conFoto > 0, 'hay publicaciones con imagen (' + conFoto + ')');
ok(conLikes > 0, 'hay estadisticas reales (' + conLikes + ')');

// 4. Temas: ninguno vacio
const temas = typeof ctx.topicsEfectivos === 'function' ? ctx.topicsEfectivos() : [];
ok(temas.length > 0, 'hay temas visibles (' + temas.length + ')');
ok(temas.every(t => t.count > 0), 'ningun tema vacio');

// 5. El resto del portal sigue en pie
for (const [marcador, nombre] of [
    ['INITIAL_SESSION', 'login con INITIAL_SESSION'],
    ['exchangeCodeForSession', 'canje PKCE'],
    ['profileViewLinkText', 'parroquia en el perfil'],
    ['ocultarSplash', 'ocultar splash'],
    ['renderLeadersGrid', 'render de leaders'],
    ['renderTopicsList', 'render de topics'],
]) {
    ok(html.includes(marcador), nombre);
}

if (fallos) {
    console.error(`\n${fallos} comprobaciones fallidas. No se publica.`);
    process.exit(1);
}
console.log('\nTodo correcto.');