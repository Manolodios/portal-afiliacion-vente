# -*- coding: utf-8 -*-
"""Inyecta el JavaScript de la cascada estado -> municipio -> parroquia.

Los campos consultan la tabla public.parroquias de Supabase, de modo que:
  - el usuario siempre ve solo lo que corresponde a lo que ya eligio;
  - anadir una parroquia en la base la hace aparecer sin tocar el portal.

Se escribe en un archivo aparte para poder reinyectarlo si hay que volver
atras, sin editar a mano un bloque de 200 lineas dentro del HTML.
"""
import io
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

MARCA_INI = '// ===== CASCADA ESTADO / MUNICIPIO / PARROQUIA ====='
MARCA_FIN = '// ===== FIN CASCADA ====='

CODIGO = r'''// ===== CASCADA ESTADO / MUNICIPIO / PARROQUIA =====
        // Los tres campos se encadenan: al elegir el estado solo se ofrecen sus
        // municipios, y al elegir el municipio solo sus parroquias. Los nombres
        // vienen de la tabla public.parroquias, asi que corregir o anadir una
        // parroquia en la base la hace aparecer aqui sin desplegar nada.
        //
        // Si el estado elegido no tiene datos cargados, el campo de municipio
        // avisa y deja escribir a mano. Nunca se bloquea el alta por esto.

        const cascada = {
            cliente: null,
            municipiosEstado: new Set(),
            municipio: '',
            // Evita disparar consultas si el usuario escribe muy rapido.
            relojMun: null,
            relojPar: null
        };

        function clienteSupabase() {
            if (cascada.cliente) return cascada.cliente;
            for (const c of [window.SupabaseAPI, window.supabase]) {
                if (c && typeof c.from === 'function') { cascada.cliente = c; return c; }
            }
            return null;
        }

        function lista(id) {
            const el = document.getElementById(id);
            return el ? el : null;
        }

        function cerrarLista(id) {
            const l = lista(id);
            if (l) { l.classList.add('hidden'); l.innerHTML = ''; }
        }

        function pintarSugerencias(id, texto, alElegir, max) {
            const l = lista(id);
            if (!l) return;
            l.innerHTML = '';
            if (!texto.length) { l.classList.add('hidden'); return; }

            if (max === 0) {
                l.classList.remove('hidden');
                l.innerHTML = '<div class="px-3 py-2 text-[11px] text-slate-400">'
                            + '¿No está la tuya? Escríbela tal cual.</div>';
                return;
            }

            l.classList.remove('hidden');
            max.forEach(function (item) {
                const b = document.createElement('button');
                b.type = 'button';
                b.className = 'block w-full text-left px-3 py-2 text-sm text-white hover:bg-sky-600/30 transition';
                b.textContent = item.etiqueta;
                b.addEventListener('mousedown', function (ev) {
                    ev.preventDefault();
                    alElegir(item.valor, item.etiqueta);
                });
                l.appendChild(b);
            });
        }

        function nota(id, texto) {
            const n = lista(id);
            if (!n) return;
            if (!texto) { n.classList.add('hidden'); n.textContent = ''; return; }
            n.classList.remove('hidden');
            n.textContent = texto;
        }

        // --- MUNICIPIO -------------------------------------------------------
        window.buscarMunicipio = function (texto) {
            clearTimeout(cascada.relojMun);
            const estado = (document.getElementById('ob-estado') || {}).value || '';
            const campo = document.getElementById('ob-municipio');
            const parq = document.getElementById('ob-parroquia');

            cascada.relojMun = setTimeout(async function () {
                cerrarLista('ob-municipio-lista');
                nota('ob-municipio-nota', '');

                // Sin estado no se puede filtrar. Se espera.
                if (!estado) {
                    if (parq) parq.disabled = true;
                    return;
                }

                const c = clienteSupabase();
                if (!c) {
                    if (parq) parq.disabled = true;
                    nota('ob-municipio-nota', 'No se pudo consultar la lista; escribe el municipio.');
                    return;
                }

                // Cuando el estado no tiene datos cargados se avisa, pero se
                // deja escribir: es preferible un dato aproximado a perder el
                // alta de una persona.
                if (cascada.municipiosEstado.has(estado)) {
                    if (parq) parq.disabled = true;
                } else {
                    const res = await c.from('parroquias')
                        .select('municipio').eq('estado', estado).limit(400);
                    const listaMun = Array.from(new Set((res.data || []).map(m => m.municipio)))
                        .sort();
                    if (listaMun.length) {
                        cascada.municipiosEstado.add(estado);
                    } else if (!cascada.municipiosEstado.has('__visto__' + estado)) {
                        cascada.municipiosEstado.add('__visto__' + estado);
                        nota('ob-municipio-nota',
                             'Todavía no tenemos el listado de ' + estado + '. Escribe el municipio.');
                        if (parq) parq.disabled = false;
                        return;
                    }
                }

                if (parq) parq.disabled = false;

                const q = (texto || '').trim().toLowerCase();
                let muns = await c.from('parroquias')
                    .select('municipio').eq('estado', estado).limit(400);
                let nombres = Array.from(new Set((muns.data || []).map(m => m.municipio))).sort();
                if (q) nombres = nombres.filter(m => m.toLowerCase().indexOf(q) >= 0);

                pintarSugerencias('ob-municipio-lista', texto || '', function (valor, etiqueta) {
                    campo.value = valor;
                    cascada.municipio = valor;
                    cerrarLista('ob-municipio-lista');
                    nota('ob-municipio-nota', '');
                    const p = document.getElementById('ob-parroquia');
                    if (p) { p.disabled = false; p.value = ''; }
                    buscarParroquia('');
                }, nombres.slice(0, 40));
            }, 180);
        };

        // --- PARROQUIA -------------------------------------------------------
        window.buscarParroquia = function (texto) {
            clearTimeout(cascada.relojPar);
            cascada.relojPar = setTimeout(async function () {
                cerrarLista('ob-parroquia-lista');
                nota('ob-parroquia-nota', '');
                const municipio = (cascada.municipio || '').trim();
                if (!municipio) {
                    nota('ob-parroquia-nota', 'Elige primero el municipio.');
                    return;
                }
                const c = clienteSupabase();
                if (!c) return;
                const q = (texto || '').trim();
                const res = await c.from('parroquias')
                    .select('parroquia').eq('municipio', municipio).limit(400);
                let nombres = Array.from(new Set((res.data || []).map(p => p.parroquia)))
                    .sort();
                if (q) nombres = nombres.filter(p => p.toLowerCase().indexOf(q.toLowerCase()) >= 0);
                if (!nombres.length && q) {
                    nota('ob-parroquia-nota',
                         '¿No está la tuya? Escríbela tal cual y la catalogamos después.');
                }
                pintarSugerencias('ob-parroquia-lista', texto || '', function (valor) {
                    const campo = document.getElementById('ob-parroquia');
                    if (campo) campo.value = valor;
                    cerrarLista('ob-parroquia-lista');
                    nota('ob-parroquia-nota', '');
                }, nombres.slice(0, 40));
            }, 180);
        };

        // Cambiar de estado reinicia el municipio y su parroquia.
        window.reiniciarUbicacion = function () {
            cascada.municipio = '';
            cascada.municipiosEstado.clear();
            const m = document.getElementById('ob-municipio');
            const p = document.getElementById('ob-parroquia');
            if (m) { m.value = ''; m.setAttribute('placeholder', 'Escribe para buscar'); }
            if (p) { p.value = ''; p.disabled = true; p.setAttribute('placeholder', 'Primero elige el municipio'); }
            cerrarLista('ob-municipio-lista');
            cerrarLista('ob-parroquia-lista');
            nota('ob-municipio-nota', '');
            nota('ob-parroquia-nota', '');
        };

        document.addEventListener('click', function (ev) {
            const t = ev.target;
            if (!t.closest || t.closest('#ob-municipio-lista') || t.closest('#ob-parroquia-lista')) return;
            if (t.id !== 'ob-municipio' && t.id !== 'ob-parroquia') {
                cerrarLista('ob-municipio-lista');
                cerrarLista('ob-parroquia-lista');
            }
        });

        window.sincronizarUbicacion = function () {
            // Al reabrir la ficha con datos ya guardados, el municipio se pone
            // directo y la parroquia solo sugiere, no obliga a teclear.
            const m = document.getElementById('ob-municipio');
            const p = document.getElementById('ob-parroquia');
            if (!m || !p) return;
            const municipio = m.value ? m.value.trim() : '';
            const parroquia = p.value ? p.value.trim() : '';
            if (municipio) {
                cascada.municipio = municipio;
                p.disabled = false;
                if (parroquia) p.value = parroquia;
            } else {
                p.disabled = true;
            }
        };
        // ===== FIN CASCADA ====='''

html = io.open(INDEX, encoding='utf-8').read()

if MARCA_INI in html:
    i = html.find(MARCA_INI)
    j = html.find(MARCA_FIN, i) + len(MARCA_FIN)
    html = html[:i] + CODIGO + html[j:]
    print('bloque anterior reemplazado')
else:
    # Se inserta antes de la seccion de la credencial, que ya esta marcada.
    ancla = '        // ===== CREDENCIAL QR ====='
    if ancla not in html:
        raise SystemExit('No se encontro el punto de insercion.')
    html = html.replace(ancla, CODIGO + '\n\n' + ancla, 1)
    print('bloque insertado')

# El select de estado dispara el reinicio.
viejo = '              <option value="Otro">Otro</option>\n            </select>'
nuevo = ('              <option value="Otro">Otro</option>\n'
         '            </select>')
if viejo in html and 'onchange="reiniciarUbicacion()"' not in html:
    html = html.replace(
        '<select id="ob-estado" class=',
        '<select id="ob-estado" onchange="reiniciarUbicacion()" class=', 1)
    print('el select de estado reinicia la cascada')

io.open(INDEX, 'w', encoding='utf-8', newline='').write(html)
print('index.html actualizado')