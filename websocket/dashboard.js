import { lineReceiver, parseReading } from "./readings.js";

const byId = (id) => document.getElementById(id);
const status = byId("status");
const log = byId("log");
const usb = byId("usb");
const wokwi = byId("wokwi");
const disconnect = byId("disconnect");
const messages = [];
let stopConnection;

function setState(state, label) {
  status.dataset.state = state;
  status.textContent = label;
  usb.disabled = state !== "idle" || !navigator.serial;
  wokwi.disabled = state !== "idle";
  disconnect.disabled = state !== "connected";
}

function appendLog(message) {
  messages.push(message);
  if (messages.length > 500) messages.shift();
  log.textContent = messages.join("\n");
  log.scrollTop = log.scrollHeight;
}

function receiveLine(line) {
  appendLog(`ESP32> ${line}`);
  const reading = parseReading(line);
  if (!reading) {
    appendLog("Línea DATA1 inválida.");
    return;
  }
  for (const [id, value] of Object.entries(reading)) byId(id).textContent = value;
}

function finish() {
  stopConnection = undefined;
  setState("idle", "Desconectado");
}

usb.addEventListener("click", async () => {
  setState("connecting", "Seleccionando puerto…");
  let port;
  let opened = false;
  let reader;
  let stopping = false;
  try {
    port = await navigator.serial.requestPort();
    await port.open({ baudRate: 115200 });
    opened = true;
    reader = port.readable.getReader();
    stopConnection = async () => {
      stopping = true;
      setState("connecting", "Desconectando…");
      await reader.cancel();
    };
    const decoder = new TextDecoder();
    const receive = lineReceiver(receiveLine);
    setState("connected", "USB conectado");
    appendLog("Puerto USB abierto a 115200 baudios.");
    while (!stopping) {
      const { done, value } = await reader.read();
      if (done) break;
      receive(decoder.decode(value, { stream: true }));
    }
  } catch (error) {
    if (!stopping && error.name !== "NotFoundError") {
      appendLog(`USB: ${error.message}. Comprueba que el puerto esté libre.`);
    }
  } finally {
    reader?.releaseLock();
    if (opened) {
      try { await port.close(); } catch (error) {
        if (port.connected) appendLog(`USB: ${error.message}`);
      }
      appendLog("Conexión USB cerrada.");
    }
    finish();
  }
});

wokwi.addEventListener("click", () => {
  setState("connecting", "Conectando a Wokwi…");
  const socket = new WebSocket(`ws://${location.host}/wokwi`);
  const receive = lineReceiver(receiveLine);
  stopConnection = () => {
    setState("connecting", "Desconectando…");
    socket.close();
  };
  socket.addEventListener("message", ({ data }) => {
    const event = JSON.parse(data);
    if (event.type === "connected") {
      setState("connected", "Wokwi conectado");
      appendLog("Conectado al puente de Wokwi.");
    } else if (event.type === "serial") {
      receive(event.text);
    } else if (event.type === "error") {
      appendLog(event.message);
    }
  });
  socket.addEventListener("error", () => appendLog("Wokwi: no se pudo comunicar con el servidor local."));
  socket.addEventListener("close", () => {
    appendLog("Conexión Wokwi cerrada.");
    finish();
  });
});

disconnect.addEventListener("click", async () => {
  try { await stopConnection?.(); } catch (error) { appendLog(error.message); }
});
byId("clear").addEventListener("click", () => {
  messages.length = 0;
  log.textContent = "Consola vacía.";
});
finish();
if (!navigator.serial) appendLog("Abre esta dirección en Chrome de escritorio para conectar por USB.");
