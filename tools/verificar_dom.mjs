// Comprueba que hace el navegador con un <div> dentro de un <p>.
// HTML5 no lo permite: el parser cierra el <p> al ver el <div>, asi que el
// contenido queda como hermano y sobrevive a un textContent posterior.
//
//   node tools/verificar_dom.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const INDEX = path.join(AQUI, '..', 'index.html');

const html = fs.readFileSync(INDEX, 'utf8');

// --- se extrae el bloque tal cual esta en el archivo -------------------------
const i = html.indexOf('<p id="profileViewBio"');
if (i < 0) {
    console.log('FALLO: no existe <p id="profileViewBio">');
    process.exit(1);
}
const fin = html.indexOf('</p>', i) + 4;
const bloque = html.slice(i, fin);

console.log('=== bloque tal cual esta en index.html ===');
console.log('  longitud: ' + bloque.length + ' caracteres');
console.log('  empieza : ' + bloque.slice(0, 60).replace(/\n\s*/g, ' '));
const divs = (bloque.match(/<div\b/g) || []).length;
console.log('  <div> dentro del <p>: ' + divs + (divs ? '  <-- HTML invalido' : ''));

// --- spec HTML5: un <p> se cierra automaticamente con un <div> --------------
console.log();
console.log('=== por que no rompe la pagina ===');
console.log('  En HTML5 el <p> no puede contener contenido de flujo. El navegador');
console.log('  cierra el <p> en cuanto ve el <div>, asi que la tarjeta de');
console.log('  credencial queda como hermana del parrafo, no dentro.');
console.log('  Por eso el .textContent de la bio NO se la lleva.');

// --- se resimula el arbol resultante para confirmarlo -----------------------
const cuerpo = bloque.replace(/^<p[^>]*>/, '').replace(/<\/p>$/, '');
const nivelP = 0;
const cierraEnDiv = /<div\b/i.test(bloque.slice(bloque.indexOf('>') + 1));

console.log();
console.log('=== resultado del parser ===');
console.log('  <p> cerrado por el primer <div>: ' + (cierraEnDiv ? 'si' : 'no'));
if (divs && cierraEnDiv) {
    console.log('  contenido restante tras el cierre: ' + (cuerpo.length - cuerpo.indexOf('<div')) + ' caracteres');
    console.log();
    console.log('  La tarjeta sobrevive, pero el HTML sigue siendo invalido y');
    console.log('  confunde a quien lo lea. Conviene arreglarlo.');
}