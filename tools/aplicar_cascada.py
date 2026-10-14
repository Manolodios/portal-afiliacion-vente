# -*- coding: utf-8 -*-
"""Sustituye el <select> fijo de parroquia por el buscador en cascada.

Se usa desde la linea de comandos porque el HTML lleva comillas y parentesis
que PowerShell intenta interpretar.
"""
import io
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
INDEX = os.path.join(RAIZ, 'index.html')

NUEVO = '''        <div class="relative">
          <label for="ob-parroquia" class="block text-[10px] sm:text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Parroquia</label>
          <input type="text" id="ob-parroquia" placeholder="Primero elige el municipio"
                 autocomplete="off" role="combobox" aria-expanded="false" aria-autocomplete="list"
                 class="w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-vente-cyan"
                 oninput="buscarParroquia(this.value)" onfocus="buscarParroquia(this.value)" disabled>
          <div id="ob-parroquia-lista" class="hidden absolute z-50 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 shadow-xl"></div>
          <p id="ob-parroquia-nota" class="hidden mt-1 text-[11px] text-amber-400"></p>
        </div>'''.split('\n')

ls = io.open(INDEX, encoding='utf-8').read().split('\n')

inicio = next((i for i, l in enumerate(ls) if 'for="ob-parroquia"' in l), None)
if inicio is None:
    raise SystemExit('No se encontro la etiqueta de la parroquia.')

fin = next((j for j in range(inicio, len(ls)) if '</select>' in ls[j]), None)
if fin is None:
    raise SystemExit('El <select> de parroquia no cierra.')

print('reemplazando lineas %d..%d (%d lineas)' % (inicio + 1, fin + 1, fin - inicio + 1))
ls[inicio:fin + 1] = NUEVO
io.open(INDEX, 'w', encoding='utf-8', newline='').write('\n'.join(ls))
print('hecho')