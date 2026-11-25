import { createConnection } from "node:net";
import { WebSocket, WebSocketServer } from "ws";

/** Adaptador de solo lectura del puente TCP de Wokwi al navegador. */
export function attachWokwi(server) {
  const websocket = new WebSocketServer({ noServer: true });
  let activeClient;

  server.on("upgrade", (request, socket, head) => {
    if (request.url !== "/wokwi") return;
    if (request.headers.origin !== "http://127.0.0.1:13000") {
      socket.end("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n");
      return;
    }
    websocket.handleUpgrade(request, socket, head, (client) => {
      client.on("error", () => client.terminate());
      const send = (event) => {
        if (client.readyState === WebSocket.OPEN) client.send(JSON.stringify(event));
      };
      if (activeClient) {
        send({ type: "error", message: "Ya hay un dashboard conectado a Wokwi." });
        client.close();
        return;
      }
      activeClient = client;
      const tcp = createConnection({ host: "127.0.0.1", port: 4001 });
      tcp.setEncoding("utf8");
      tcp.setTimeout(3000, () => tcp.destroy(new Error("Tiempo de conexión agotado")));
      tcp.on("connect", () => tcp.setTimeout(0));
      // El puente TCP puede aceptar antes de enlazar con el simulador.
      // La primera línea confirma que ya hay datos de Wokwi.
      let receiving = false;
      tcp.on("data", (text) => {
        if (!receiving) send({ type: "connected" });
        receiving = true;
        send({ type: "serial", text });
      });
      const firstData = setTimeout(() => {
        if (!receiving) tcp.destroy(new Error("El puente no envió datos"));
      }, 8000);
      tcp.on("error", (error) => {
        send({ type: "error", message: `Wokwi: ${error.message}. Inicia el simulador y scripts/bridge.py, y desconecta Swing.` });
      });
      tcp.on("close", () => {
        clearTimeout(firstData);
        if (!receiving && client.readyState === WebSocket.OPEN) {
          send({ type: "error", message: "Comprueba que Wokwi esté visible y que el puente esté disponible." });
        }
        client.close();
      });
      client.on("close", () => {
        activeClient = undefined;
        tcp.destroy();
      });
    });
  });

  return websocket;
}
