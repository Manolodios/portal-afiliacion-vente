# Guía de pruebas del portal

Para el seeing. Son 6 pruebas, de la más importante a la menos. No hace falta hacerlas
todas seguidas: haz una, me cuentas, y seguimos.

**Regla de oro**: si algo no sale como dice aquí, no lo intentes arreglar ni lo repitas
diez veces. Cópiame el mensaje que salga y pásamelo. Eso me basta para localizarlo.

---

## PRUEBA 1 · Notificaciones push

**Es la más importante.** Es lo único que nunca se ha visto funcionar de verdad.

**Necesitas dos cosas a la vez:**

- Un móvil y un ordenador, **o**
- Dos ventanas del navegador (una normal y otra de incógnito)

> **Por qué**: si mandas la notificación y miras la misma pestaña, Chrome **no la
> muestra**. No es un fallo, es así. Por eso hacen falta dos sitios distintos.

### Pasos

1. En el **dispositivo A**, entra al portal con tu cuenta y ve a tu panel.
2. Abajo, debajo de "Guardar PDF", pulsa el botón gris **"Activar notificaciones"**.
3. El navegador te pide permiso. Pulsa **Permitir**.
4. El botón debe ponerse **verde** y decir **"Notificaciones activadas"**.
5. Ve al **dispositivo B**, entra como admin y pulsa la **campana ámbar** arriba.
6. Escribe un título y un mensaje, y pulsa **"Enviar notificación"**.

### Qué debe pasar

- En el dispositivo B: un aviso verde que dice **"Notificacion enviada a 1 afiliados"**.
- En el dispositivo A: **te salta una notificación en el escritorio** con tu título y
  tu mensaje.

### Si falla, dime exactamente esto

| Lo que ves | Lo que significa |
|---|---|
| El botón se queda **gris** | No se suscribió. Dime si salió algún aviso rojo |
| El botón se pone **rojo** | El permiso está bloqueado en el navegador |
| "Enviada a **0** afiliados" | El paso 2 no funcionó. Repítelo y dime qué salió |
| **Nada llega** al dispositivo A | Dime si el paso 4 se puso verde y si el 6 dijo "1 afiliados" |

**Lo más útil que me puedes dar**: el número que sale en "enviada a **N** afiliados".

---

## PRUEBA 2 · Registro con correo

Usa un correo tuyo de verdad, o uno nuevo que crees para esto.

1. Abre el portal y pulsa **"Entrar"** (arriba a la derecha).
2. Pulsa la pestaña **"Crear cuenta"**.
3. Rellena Correo, Contraseña y Repetir contraseña.
4. Resuelve el captcha y pulsa **"Crear cuenta"**.

### Qué debe pasar

- Sale una pantalla que dice que revises tu correo, con **tu dirección escrita**.
- Te llega un correo de confirmación. Al abrirlo, una página dice
  **"Ya estás verificado"**.
- Vuelves al portal, entras, y aparece **"Completa tu ficha"** con los campos:

  Nombre · Apellido · Tipo de documento · Cédula · Fecha de nacimiento ·
  Estado · Municipio · Parroquia · las 5 áreas de colaboración

- Rellenas todo, eliges al menos **un área**, y guardas.
- Entras a tu panel con tu tarjeta de credencial.

### Si falla, dime esto

- **En qué paso exacto** te quedaste (número).
- El **texto literal del aviso** que salga.
- Si fue al guardar la ficha: qué campos dejaste **vacíos** a propósito.

---

## PRUEBA 3 · Registro con Google

Es la que dio problemas, así que interesa mucho.

1. Abre el portal en una **ventana de incógnito** (para que no uses tu sesión).
2. Pulsa **"Entrar"** → **"Continuar con Google"**.
3. Elige una cuenta de Google.

### Qué debe pasar

- Vuelves al portal ya dentro.
- Si tu cuenta de Google **no** tiene nombre y apellido completos, debe salirte un
  aviso amarillo diciendo que **completes tu apellido**.
- La ficha aparece con tu nombre ya rellenado si Google lo dio.

### Si falla, dime esto

- Si te devolvió al portal o te dejó en una página de Google.
- Si la ficha apareció vacía, a medias, o no apareció.
- El texto literal de cualquier aviso.

> **Nota**: si usas una cuenta de Google normal (con nombre y apellido puestos),
> probablemente no veas ningún aviso. Eso es **correcto**, no un fallo.

---

## PRUEBA 4 · La credencial y el QR

1. En tu panel, mira la tarjeta oscura de la credencial.
2. Debe tener tu **nombre**, tu **cédula**, el **ID único** (formato `VV-0000-0000`) y
   el **código QR** a la derecha.
3. Pulsa **"Compartir Credencial"** → debe decir que se copió.
4. Pulsa **"Guardar PDF"** → debe descargarse un archivo.
5. **Apunta el ID único** y escanea el QR con la cámara del móvil.

### Qué debe pasar

- El QR abre una página que muestra **tu nombre y si la credencial es válida**.
- No hace falta tener sesión abierta: cualquiera puede escanearlo.

### Si falla, dime esto

- El **ID único** que te salió (formato `VV-0000-0000`).
- Si el QR no abre, o si abre pero dice que **no es válida**.

---

## PRUEBA 5 · Panel de admin

1. Entra con tu cuenta de `yhojansuarez@gmail.com`.
2. Debe aparecer la **campana ámbar** ("Notificar afiliados") arriba.
3. Pruébala: elige un estado, escribe algo, envía.

### Qué debe pasar

- Sale el aviso con el número de afiliados a los que se envió.
- Si no hay nadie suscrito en ese estado, debe decir **"Sin destinatarios"** — eso es
  correcto, no un fallo.

---

## PRUEBA 6 · El portal en general

Un recorrido rápido del sitio público, sin sesión:

- **Inicio**: se ve la portada y el feed de publicaciones carga (tarda unos segundos).
- **Temas**: salen las etiquetas. *(Ojo: aquí hay un fallo conocido — algunas salen
  repetidas, como `#SetTheDate` tres veces. Ya lo sé, no hace falta que lo reportes.)*
- **Líderes**: aparecen las fuentes de Vente.
- **FAQ** y **Principios**: las secciones de la portada tienen texto.
- Míralo también en el **móvil**: el menú debe abrirse bien.

---

## Cómo contarme un fallo

Cuanto más concreto, mejor. Con esto me sobra:

1. **Qué prueba** estabas haciendo (el número).
2. **Qué pulsaste** justo antes.
3. **Qué esperabas** que pasara.
4. **Qué pasó en realidad**.
5. **El texto literal** del aviso, copiado tal cual.
6. Si puedes, una **captura de pantalla**.

### Si sale un aviso raro o el botón no hace nada

Esto me ayuda mucho y son 10 segundos:

1. Pulsa **F12** en el teclado (se abre un panel).
2. Arriba, pulsa la pestaña **"Console"**.
3. Copia lo que haya en rojo y pásamelo.

No pasa nada por lo que veas ahí: no rompes nada, solo estás mirando.

---

## Lo que ya sé que está mal

No hace falta que lo reportes, ya está apuntado:

- **Temas repetidos**: `#SetTheDate` sale tres veces y `#SetTheDat` tiene una errata
  (esa última es un error de quien escribió el tuit, no nuestro).
- **El feed se paró unas horas** el 18 de octubre porque un validador rechazó una
  tanda. Se recuperó solo.
- **Lara y Táchira sin parroquias** en el buscador. No hay fuente oficial.
