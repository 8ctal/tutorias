# Documentación completa del servidor WebSocket y su cliente

Este documento explica [server.js](./server.js) y
[index.html](./index.html) desde cero. El servidor usa Node.js y la biblioteca
[`ws`](https://github.com/websockets/ws). Su objetivo es servir el cliente web
y permitir que varios navegadores intercambien mensajes en tiempo real.

El dashboard de sensores está en `/dashboard`. Para USB usa Web Serial. Para Wokwi,
`wokwi.js` enlaza el WebSocket `/wokwi` con el puente TCP local en el puerto 4001.
Las secciones siguientes describen la demostración de mensajería disponible en `/`.

## 1. Qué hace el programa

El programa ejecuta dos servicios sobre el mismo puerto:

| Servicio | Dirección | Función |
| --- | --- | --- |
| HTTP | `http://127.0.0.1:13000` | Entrega `index.html` |
| WebSocket | `ws://127.0.0.1:13000` | Mantiene conexiones en tiempo real |

Cuando un cliente se conecta, recibe un saludo. Cuando envía un mensaje, el
servidor lo retransmite a todos los clientes que siguen conectados.

## 2. Requisitos y ejecución

Se necesita Node.js y pnpm. Desde la carpeta `websocket`:

```powershell
corepack pnpm install
corepack pnpm start
```

Para desarrollo, `dev` reinicia Node.js cuando cambia el servidor:

```powershell
corepack pnpm dev
```

Después se abre `http://127.0.0.1:13000` en el navegador.

## 3. Módulos importados

### `createReadStream`

Proviene de `node:fs`. Lee `index.html` por partes. Un flujo (`stream`) es
preferible a leer todo el archivo de una sola vez porque usa memoria de forma
progresiva.

### `stat`

Proviene de `node:fs/promises`. Consulta metadatos del archivo, especialmente su
tamaño. Se usa para completar el encabezado HTTP `Content-Length`.

### `createServer`

Proviene de `node:http`. Crea el servidor HTTP y proporciona los objetos
`request` y `response` para cada petición.

### `extname` y `resolve`

Provienen de `node:path`:

- `extname` obtiene la extensión, por ejemplo `.html`.
- `resolve` construye una ruta absoluta correctamente.

### `fileURLToPath`

Proviene de `node:url`. Los módulos ES usan `import.meta.url`, que es una URL.
Esta función la convierte en una ruta que el sistema de archivos de Windows
puede utilizar.

### `WebSocketServer` y `WebSocket`

Los exporta la dependencia `ws`:

- `WebSocketServer` administra las conexiones.
- `WebSocket.OPEN` permite comprobar si una conexión está lista para recibir
  datos.

## 4. Constantes

### `PORT`

```js
const PORT = 13000;
```

Define el único puerto utilizado por HTTP y WebSocket. `const` significa que la
referencia no se reasigna durante la ejecución.

### `HOST`

```js
const HOST = "127.0.0.1";
```

Limita el servidor al equipo local. Por eso otros dispositivos de la red no
pueden conectarse directamente. Para un servidor accesible en la red local
podría utilizarse `0.0.0.0`, pero eso debe hacerse conscientemente.

### `SERVER_DIRECTORY`

```js
const SERVER_DIRECTORY = fileURLToPath(new URL(".", import.meta.url));
```

Calcula la carpeta donde está `server.js`. No depende de la carpeta desde la que
se ejecutó el comando.

- `import.meta.url` identifica este módulo.
- `new URL(".", ...)` obtiene su carpeta.
- `fileURLToPath` transforma la URL en una ruta del sistema.

### `CLIENT_FILE`

```js
const CLIENT_FILE = resolve(SERVER_DIRECTORY, "index.html");
```

Construye la ruta absoluta al archivo que se va a servir. Usar una ruta fija
evita aceptar nombres de archivos proporcionados por el navegador.

### `contentTypes`

```js
const contentTypes = {
  ".html": "text/html; charset=utf-8",
};
```

Es un objeto de consulta: dada una extensión, devuelve el tipo MIME que debe
enviarse en `Content-Type`. El navegador necesita este dato para interpretar
correctamente el contenido.

## 5. Servidor HTTP

### Creación de `httpServer`

```js
const httpServer = createServer(async (request, response) => {
  // ...
});
```

`createServer` recibe una función que se ejecuta por cada petición. La función
es `async` porque necesita esperar a `stat`.

#### `request`

Representa la petición entrante. Las propiedades utilizadas son:

- `request.method`: método HTTP, por ejemplo `GET`.
- `request.url`: ruta solicitada.

#### `response`

Permite construir la respuesta:

- `writeHead`: envía estado y encabezados.
- `end`: envía texto y finaliza.
- `pipe`: conecta un flujo de lectura con la respuesta.

### `isAllowedRequest`

```js
const isAllowedRequest =
  request.method === "GET" &&
  (request.url === "/" || request.url === "/index.html");
```

Es un booleano. Solo es `true` para las dos rutas permitidas y el método
`GET`. Separar esta condición hace más legible la validación.

### Respuesta 404

Si `isAllowedRequest` es `false`, el servidor:

1. Envía el estado `404`.
2. Indica que la respuesta es texto UTF-8.
3. Envía `Recurso no encontrado`.
4. Ejecuta `return` para salir de la función.

El `return` es importante: evita que una petición inválida continúe hasta la
lectura del archivo.

### Bloque `try`

```js
const fileInfo = await stat(CLIENT_FILE);
```

Comprueba que `index.html` exista y obtiene sus metadatos. `await` pausa esta
función hasta recibir el resultado sin bloquear todo Node.js.

Después se envía el estado `200`, que significa que la petición fue correcta.
`fileInfo.size` se usa como tamaño de la respuesta.

```js
contentTypes[extname(CLIENT_FILE)] ?? "application/octet-stream"
```

Busca el tipo MIME de la extensión. `??` usa el tipo genérico únicamente si no
hay una entrada para esa extensión.

### Flujo del archivo

```js
createReadStream(CLIENT_FILE).pipe(response);
```

`createReadStream` abre el archivo como flujo y `pipe` envía cada parte al
navegador. Cuando termina el archivo, la respuesta queda completada.

### Bloque `catch`

Captura problemas como un archivo inexistente o sin permisos:

- `console.error` conserva el detalle para quien ejecuta el servidor.
- El navegador recibe estado `500`.
- El mensaje público evita exponer detalles internos del sistema.

## 6. Servidor WebSocket

### `webSocketServer`

```js
const webSocketServer = new WebSocketServer({ server: httpServer });
```

Le indica a `ws` que use el servidor HTTP existente. Así no hace falta abrir
otro puerto. El objeto mantiene el conjunto `webSocketServer.clients`.

### Evento `connection`

```js
webSocketServer.on("connection", (client, request) => {
  // ...
});
```

Se dispara una vez por cada conexión WebSocket aceptada:

- `client` representa ese navegador.
- `request` es la petición HTTP inicial que solicitó actualizarse a WebSocket.

### `remoteAddress`

```js
const remoteAddress = request.socket.remoteAddress ?? "desconocido";
```

Guarda la dirección del cliente para los mensajes de diagnóstico. Si Node.js
no proporciona una dirección, se usa el texto `desconocido`.

### Mensaje de bienvenida

```js
client.send(JSON.stringify({ ... }));
```

`send` transmite datos al cliente. WebSocket transmite texto o binarios, por
eso `JSON.stringify` convierte el objeto JavaScript en texto JSON.

El objeto contiene:

- `type`: clasifica el mensaje como `welcome`.
- `message`: texto que puede mostrar la interfaz.
- `clients`: cantidad actual de conexiones.

### Evento `message`

Se dispara cuando ese cliente envía datos:

```js
client.on("message", (data, isBinary) => {
  // ...
});
```

#### `data` e `isBinary`

- `data` contiene el mensaje recibido.
- `isBinary` indica si llegó como datos binarios.

El código convierte ambos casos a texto UTF-8:

```js
const message = isBinary ? data.toString("utf8") : data.toString();
```

El operador ternario elige una de las dos expresiones según `isBinary`.

#### `payload`

Es el mensaje que se retransmite. Tiene `type: "message"`, el texto recibido y
la cantidad de clientes conectados.

#### Bucle de retransmisión

```js
for (const connectedClient of webSocketServer.clients) {
  if (connectedClient.readyState === WebSocket.OPEN) {
    connectedClient.send(payload);
  }
}
```

El `for...of` visita cada conexión. La comprobación `readyState` evita intentar
enviar a un cliente que ya está cerrándose o cerrado. El mensaje se envía
también al cliente que lo originó.

### Evento `close`

Se ejecuta cuando la conexión termina. Solo registra la desconexión; no necesita
eliminar manualmente el cliente porque `ws` lo retira de su colección.

### Evento `error`

Registra errores de una conexión específica. El servidor no se detiene ni cierra
las demás conexiones por un error aislado.

## 7. Inicio del servidor

```js
httpServer.listen(PORT, HOST, () => {
  // ...
});
```

`listen` empieza a escuchar en `127.0.0.1:13000`. La función callback se ejecuta
cuando el puerto ya está disponible y muestra las dos direcciones útiles.

## 8. Apagado ordenado

### Función `shutdown`

```js
function shutdown(signal) {
  // ...
}
```

Recibe el nombre de la señal que provocó el cierre:

1. Informa en la terminal qué señal llegó.
2. Recorre los clientes activos.
3. Cierra cada conexión con código `1001`, que indica que el servidor se va.
4. Cierra el servidor HTTP.
5. Cuando termina el cierre, ejecuta `process.exit(0)`.

Cerrar explícitamente las conexiones evita dejar recursos abiertos.

### `SIGINT` y `SIGTERM`

```js
process.once("SIGINT", () => shutdown("SIGINT"));
process.once("SIGTERM", () => shutdown("SIGTERM"));
```

- `SIGINT` normalmente se produce al pulsar `Ctrl+C`.
- `SIGTERM` normalmente lo envía el sistema o una herramienta de ejecución.

`once` garantiza que cada señal active el manejador una sola vez.

## 9. Formato de mensajes

Mensaje de bienvenida:

```json
{
  "type": "welcome",
  "message": "Conexión establecida con el servidor WebSocket.",
  "clients": 1
}
```

Mensaje retransmitido:

```json
{
  "type": "message",
  "message": "Hola",
  "clients": 1
}
```

## 10. Flujo completo

1. `pnpm start` ejecuta `node server.js`.
2. Node.js importa los módulos.
3. Se calcula la ruta absoluta de `index.html`.
4. Se crea el servidor HTTP.
5. `ws` se conecta al servidor HTTP.
6. `listen` abre el puerto `13000`.
7. El navegador solicita `/` y recibe `index.html`.
8. El navegador abre `ws://127.0.0.1:13000`.
9. El servidor envía el saludo.
10. El navegador envía un texto.
11. El servidor crea el JSON y lo envía a todos los clientes abiertos.
12. Al pulsar `Ctrl+C`, se cierran las conexiones y el servidor termina.

## 11. Cliente `index.html`

El cliente es una página HTML autocontenida: no necesita frameworks ni
dependencias adicionales. Está formada por tres partes:

1. HTML: define los controles que ve el usuario.
2. CSS: define colores, tamaños, espacios y estados visuales.
3. JavaScript: abre la conexión, envía mensajes y actualiza la interfaz.

Los comentarios dentro del archivo explican cada línea relevante. Las secciones
siguientes explican el propósito de cada elemento con más contexto.

### Estructura HTML

#### `<!DOCTYPE html>`

Indica al navegador que debe interpretar el documento usando HTML5.

#### `<html lang="es">`

Es el elemento raíz de la página. `lang="es"` informa que el contenido está en
español y ayuda a lectores de pantalla y buscadores.

#### `<head>`

Contiene información que configura el documento, pero que normalmente no se
muestra dentro de la página:

- `meta charset="UTF-8"` permite tildes, ñ y otros caracteres.
- `meta viewport` adapta la escala a teléfonos y tabletas.
- `meta description` describe la página.
- `title` define el texto de la pestaña.
- `style` contiene los estilos CSS.

#### `<body>` y `<main>`

`body` contiene todo lo visible. `main` agrupa el contenido principal y usa la
clase `container` para aplicar el panel central.

#### Título

```html
<h1>Cliente WebSocket</h1>
```

`h1` es el título principal de la interfaz.

#### Campo `server`

```html
<input id="server" type="url" ...>
```

Permite escribir la dirección del servidor:

- `id="server"` permite encontrarlo desde JavaScript.
- `type="url"` comunica que contiene una dirección.
- `value` aporta el valor inicial.
- `placeholder` muestra un ejemplo cuando está vacío.
- `autocomplete="url"` permite al navegador sugerir direcciones conocidas.

#### Botones de conexión

Los botones tienen `type="button"` para que no intenten enviar un formulario.

- `connectBtn` inicia `connectSocket`.
- `disconnectBtn` inicia `disconnectSocket`.
- `disabled` desactiva Desconectar hasta tener una conexión.

Las clases `connect` y `disconnect` solo controlan sus colores.

#### Indicador `status`

```html
<div id="status" role="status" aria-live="polite">
```

Muestra `Desconectado`, `Conectando`, `Conectado` o `Error`. `role="status"` y
`aria-live="polite"` permiten que las tecnologías de asistencia anuncien
cambios sin interrumpir bruscamente al usuario.

#### Campo `message`

Es el campo de texto que se limpia después de un envío. Su `id` lo conecta con
`messageInput`.

#### Botón `sendBtn`

Ejecuta `sendMessage`. Empieza desactivado y se habilita en el evento `open`.

#### Consola `messages`

```html
<div id="messages" role="log" aria-live="polite"></div>
```

Es el contenedor donde `logMessage` crea un `div` por cada evento. `role="log"`
describe que contiene una secuencia de mensajes.

#### Botón `clearBtn`

Elimina el contenido de la consola mediante `replaceChildren()`, sin recargar la
página ni cerrar la conexión.

### Estilos CSS

#### `:root`

Define la fuente global y solicita un tema claro.

#### `body`

Define el fondo, elimina el margen predeterminado y agrega espacio alrededor del
panel.

#### `.container`

Limita el ancho a `700px`, centra el panel, agrega fondo, espacio interior,
bordes redondeados y sombra.

#### `label`, `input` y `button`

Establecen una disposición legible y consistente:

- Las etiquetas ocupan una línea y usan negrita.
- Los campos ocupan todo el ancho disponible.
- Los botones comparten espaciado, tipografía y bordes redondeados.
- `button:disabled` comunica visualmente que un control no está disponible.

#### Clases de botones

`.connect`, `.disconnect`, `.send` y `.clear` asignan colores distintos para
identificar visualmente cada acción.

#### `#status`

Es el panel cuyo fondo cambia desde JavaScript para distinguir estados.

#### `#messages`

Crea una consola de altura fija con desplazamiento vertical. `white-space:
pre-wrap` conserva saltos de línea y `overflow-wrap: anywhere` evita que un
mensaje muy largo rompa el diseño.

#### `.received`, `.sent` y `.system`

Colorean mensajes recibidos, enviados y eventos informativos respectivamente.

### Variables JavaScript

#### `defaultServerUrl`

`websocketProtocol` elige `wss` cuando la página usa HTTPS y `ws` en cualquier
otro caso. Después `defaultServerUrl` construye una dirección usando el mismo
host y puerto desde el que se sirvió la página. Si la página se abrió
directamente desde un archivo y no existe host, usa `127.0.0.1:13000`.

#### `socket`

Empieza como `null` porque no hay conexión. Después contiene el objeto
`WebSocket` actual.

#### Referencias del DOM

Las constantes `serverInput`, `messageInput`, `statusDiv`, `messagesDiv`,
`connectBtn`, `disconnectBtn` y `sendBtn` guardan referencias a elementos HTML.
`document.getElementById` busca cada elemento por su `id`, evitando buscarlo
repetidamente.

### Ajuste automático de la dirección

Cuando la página viene de `http:` o `https:`, el código conserva el host y
puerto actuales y configura el campo automáticamente con `ws:` o `wss:`.

### Función `logMessage`

```js
function logMessage(message, type = "system")
```

Recibe el texto y una clase visual. Sus pasos son:

1. Crea un elemento `div`.
2. Asigna la clase `system`, `sent` o `received`.
3. Añade la hora actual con `toLocaleTimeString`.
4. Usa `textContent`, que trata el mensaje como texto y evita interpretar HTML.
5. Inserta la línea en `messagesDiv`.
6. Desplaza la consola hasta el último mensaje.

### Función `setConnectionState`

```js
function setConnectionState(state, background = "#eee")
```

Actualiza el texto del estado y su color de fondo. El segundo parámetro tiene un
valor por defecto para que los estados normales no necesiten especificarlo.

### Función `connectSocket`

Es la función principal de conexión:

1. Lee y limpia la URL.
2. Comprueba con una expresión regular que empiece por `ws://` o `wss://`.
3. Evita abrir otra conexión si ya hay una conectándose o abierta.
4. Crea `new WebSocket(url)`.
5. Desactiva temporalmente Conectar.
6. Registra los eventos `open`, `message`, `error` y `close`.

#### Evento `open`

Se ejecuta cuando la conexión ya está lista. Cambia el estado a Conectado,
habilita Desconectar y Enviar, y registra el éxito.

#### Evento `message`

Recibe `data` del servidor. Primero intenta `JSON.parse` porque el servidor
envía objetos JSON. Si el mensaje no es JSON válido, el bloque `catch` muestra
el texto original.

#### Evento `error`

Registra un aviso general. El navegador no siempre proporciona detalles seguros
o útiles, por lo que la aplicación no los muestra.

#### Evento `close`

Muestra `event.code`, vuelve a habilitar Conectar, deshabilita los controles que
requieren conexión y muestra `event.reason` si existe.

#### `try/catch`

Captura errores inmediatos producidos al crear la conexión, restaura el botón
Conectar y muestra el mensaje disponible en `error.message`.

### Función `sendMessage`

Lee el campo, elimina espacios y verifica que WebSocket esté en estado `OPEN`.
No envía cadenas vacías. Cuando el envío es válido:

1. Ejecuta `socket.send(message)`.
2. Muestra el mensaje localmente con clase `sent`.
3. Limpia el campo.
4. Devuelve el foco al campo.

### Función `disconnectSocket`

Comprueba que exista una conexión abierta o conectándose y llama a
`socket.close(1000, ...)`. El código `1000` representa una desconexión normal
solicitada por el cliente.

### Eventos de la interfaz

Estas líneas conectan controles con funciones:

```js
connectBtn.addEventListener("click", connectSocket);
disconnectBtn.addEventListener("click", disconnectSocket);
sendBtn.addEventListener("click", sendMessage);
```

El último listener escucha `keydown` en `messageInput` y llama a `sendMessage`
cuando `event.key` es `Enter`, permitiendo enviar sin usar el ratón.

## 12. Recorrido de una interacción

1. El navegador carga el HTML y crea los elementos del DOM.
2. JavaScript guarda sus referencias y configura la URL.
3. El usuario pulsa **Conectar**.
4. `connectSocket` crea el objeto WebSocket.
5. El evento `open` habilita Enviar.
6. El usuario escribe y pulsa **Enviar** o `Enter`.
7. `sendMessage` manda el texto al servidor.
8. El servidor retransmite JSON.
9. El evento `message` analiza el JSON.
10. `logMessage` añade la respuesta a la consola.
