/**
 * Servidor HTTP y WebSocket de la demostración.
 * La explicación completa de cada elemento está en SERVER-DOCUMENTATION.md.
 */

// Lee el archivo HTML como un flujo, sin cargarlo completo en memoria.
import { createReadStream } from "node:fs";
// Consulta información de archivos usando la API asíncrona de Node.js.
import { stat } from "node:fs/promises";
// Crea el servidor HTTP que también utilizará WebSocket.
import { createServer } from "node:http";
// Obtiene extensiones y construye rutas independientes del sistema operativo.
import { resolve } from "node:path";
// Convierte URLs de módulos ES en rutas normales del sistema.
import { fileURLToPath } from "node:url";
// Importa el servidor WebSocket y la constante que representa una conexión abierta.
import { WebSocketServer, WebSocket } from "ws";
import { attachWokwi } from "./wokwi.js";

// Puerto común para HTTP y WebSocket.
const PORT = 13000;
// Solo se aceptan conexiones desde el equipo local.
const HOST = "127.0.0.1";
// Obtiene la carpeta donde está este archivo server.js.
const SERVER_DIRECTORY = fileURLToPath(new URL(".", import.meta.url));
// Cada ruta sirve un archivo fijo de esta carpeta.
const assets = new Map([
  ["/", ["index.html", "text/html"]],
  ["/index.html", ["index.html", "text/html"]],
  ["/dashboard", ["dashboard.html", "text/html"]],
  ["/dashboard.css", ["dashboard.css", "text/css"]],
  ["/dashboard.js", ["dashboard.js", "text/javascript"]],
  ["/readings.js", ["readings.js", "text/javascript"]],
]);

const httpServer = createServer(async (request, response) => {
  const asset = assets.get(request.url);
  if (request.method !== "GET" || !asset) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Recurso no encontrado");
    return;
  }

  const [file, contentType] = asset;
  const path = resolve(SERVER_DIRECTORY, file);
  try {
    const fileInfo = await stat(path);
    response.writeHead(200, {
      "Content-Length": fileInfo.size,
      "Content-Type": contentType + "; charset=utf-8",
    });
    const stream = createReadStream(path);
    stream.on("error", (error) => response.destroy(error));
    stream.pipe(response);
  } catch (error) {
    console.error("No se pudo servir el archivo:", error);
    response.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("No se pudo cargar el archivo");
  }
});

const wokwiServer = attachWokwi(httpServer);
const webSocketServer = new WebSocketServer({ noServer: true });
httpServer.on("upgrade", (request, socket, head) => {
  if (request.url === "/wokwi") return;
  if (request.url !== "/") {
    socket.end("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n");
    return;
  }
  webSocketServer.handleUpgrade(request, socket, head, (client) => {
    webSocketServer.emit("connection", client, request);
  });
});

// Ejecuta esta función cada vez que un navegador abre una conexión WebSocket.
webSocketServer.on("connection", (client, request) => {
  // Obtiene la dirección del cliente para facilitar el diagnóstico en la terminal.
  const remoteAddress = request.socket.remoteAddress ?? "desconocido";
  // Informa de una nueva conexión.
  console.log(`Cliente conectado: ${remoteAddress}`);

  // Envía un mensaje inicial solo al cliente recién conectado.
  client.send(
    // Convierte el objeto JavaScript en texto JSON para transportarlo por WebSocket.
    JSON.stringify({
      // Identifica este mensaje como saludo inicial.
      type: "welcome",
      // Texto que el cliente mostrará en su consola.
      message: "Conexión establecida con el servidor WebSocket.",
      // Número de clientes conectados en este momento.
      clients: webSocketServer.clients.size,
    }),
  );

  // Escucha mensajes de texto o binarios enviados por este cliente.
  client.on("message", (data, isBinary) => {
    // Convierte cualquier entrada a texto UTF-8 para mantener un protocolo sencillo.
    const message = isBinary ? data.toString("utf8") : data.toString();
    // Prepara un mensaje JSON que se compartirá con todos los clientes.
    const payload = JSON.stringify({
      // Identifica este mensaje como contenido enviado por un cliente.
      type: "message",
      // Conserva el texto recibido.
      message,
      // Incluye el número actual de conexiones.
      clients: webSocketServer.clients.size,
    });

    // Recorre todas las conexiones conocidas por el servidor.
    for (const connectedClient of webSocketServer.clients) {
      // Solo intenta enviar a conexiones que todavía están abiertas.
      if (connectedClient.readyState === WebSocket.OPEN) {
        // Retransmite el mensaje, incluido al cliente que lo originó.
        connectedClient.send(payload);
      }
    }
  });

  // Informa cuando el cliente cierra voluntariamente o pierde la conexión.
  client.on("close", () => {
    // Registra qué cliente abandonó la sesión.
    console.log(`Cliente desconectado: ${remoteAddress}`);
  });

  // Captura errores asociados a esta conexión concreta.
  client.on("error", (error) => {
    // Muestra el mensaje técnico sin detener las conexiones restantes.
    console.error(`Error del cliente ${remoteAddress}:`, error.message);
  });
});

// Comienza a escuchar peticiones HTTP y conexiones WebSocket.
httpServer.listen(PORT, HOST, () => {
  // Muestra la dirección para abrir el cliente en un navegador.
  console.log(`Dashboard: http://${HOST}:${PORT}/dashboard`);
  console.log(`Cliente HTTP: http://${HOST}:${PORT}`);
  // Muestra la dirección que deben usar los clientes WebSocket.
  console.log(`Servidor WebSocket: ws://${HOST}:${PORT}`);
});

/**
 * Cierra las conexiones antes de terminar el proceso.
 * Esto evita dejar sockets abiertos al detener Node.js con Ctrl+C.
 *
 * @param {string} signal Nombre de la señal que solicitó el cierre.
 */
function shutdown(signal) {
  // Informa de que comenzó el cierre ordenado.
  console.log(`\n${signal}: cerrando servidor...`);
  // Recorre las conexiones activas.
  for (const client of [...webSocketServer.clients, ...wokwiServer.clients]) {
    // Cierra cada conexión con el código estándar de servidor detenido.
    client.close(1001, "Servidor detenido");
  }
  // Espera a que el servidor HTTP termine de cerrar sus recursos.
  httpServer.close(() => process.exit(0));
}

// Ejecuta shutdown una sola vez cuando el usuario presiona Ctrl+C.
process.once("SIGINT", () => shutdown("SIGINT"));
// Ejecuta shutdown una sola vez cuando el sistema solicita terminar el proceso.
process.once("SIGTERM", () => shutdown("SIGTERM"));

