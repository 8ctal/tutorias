/** Reúne fragmentos USB o TCP hasta recibir un salto de línea. */
export function lineReceiver(onLine) {
  let partial = "";
  let overflow = false;
  return (chunk) => {
    for (const char of chunk) {
      if (char === "\n") {
        const line = partial.trim();
        if (!overflow && line) onLine(line);
        partial = "";
        overflow = false;
      } else if (char !== "\r" && !overflow) {
        if (partial.length === 512) overflow = true;
        else partial += char;
      }
    }
  };
}

function format(value) {
  return Number.isFinite(value) && value > -1000 ? value.toFixed(2) : "—";
}

export function parseReading(line) {
  if (line === "BUTTON,0" || line === "BUTTON,1") {
    return { button: line.endsWith("1") ? "PULSADO" : "LIBRE" };
  }
  const fields = line.split(",");
  if (fields[0] !== "DATA1") return {};
  if (fields.length !== 7 || !/^[01]$/.test(fields[6])) return null;
  const numbers = fields.slice(1, 6).map((field) =>
    /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(field) ? Number(field) : NaN);
  if (numbers.some((value) => !Number.isFinite(value))) return null;
  const [temperature, distance, ax, ay, az] = numbers;
  return {
    temperature: format(temperature),
    distance: distance < 0 ? "Sin eco" : format(distance),
    ax: format(ax),
    ay: format(ay),
    az: format(az),
    button: fields[6] === "1" ? "PULSADO" : "LIBRE",
  };
}
