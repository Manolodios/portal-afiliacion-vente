/**
 * Configuración de Tailwind CSS para el portal (build estático).
 *
 * El portal usa Tailwind compilado (no el Play CDN) para:
 *  - eliminar el aviso "cdn.tailwindcss.com no debe usarse en producción"
 *  - evitar el parpadeo de estilos al cargar
 *  - no depender de un CDN en tiempo de ejecución
 *
 * Para regenerar assets/tailwind.css después de cambiar clases en index.html:
 *
 *    npx tailwindcss -c tailwind.config.js -i tailwind.src.css -o assets/tailwind.css
 *
 * (en Windows con PowerShell: npx.cmd ...)
 *
 * Nota: sin --minify a propósito. El minificador convierte rgb() a hsla() con
 * porcentajes redondeados y eso desplaza algunos colores 1/255. Con --minify el
 * CSS baja a 36 KB en vez de 51 KB, pero deja de ser pixel idéntico al diseño
 * original. Si algún día se quiere minificar, verificar los colores después.
 */
module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      colors: {
        vente: {
          cyan: '#00A8E8', hover: '#0090C8', navy: '#0A192F',
          dark: '#030811', light: '#F4F9FC', accent: '#00E5FF'
        }
      }
    }
  }
};
