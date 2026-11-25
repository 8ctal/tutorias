# Estado de verificación — 20 de octubre de 2026

| Comprobación | Resultado |
|---|---|
| Firmware PlatformIO / ESP32 | Compilación correcta; RAM 21 976 bytes (6,7 %), programa 303 669 bytes (23,2 %) con diagnóstico, modo MPU compatible y eventos BUTTON |
| Binarios Wokwi | `.pio/build/esp32dev/firmware.bin` y `firmware.elf` generados |
| Java Swing, compatibilidad Java 25 | Compilación correcta con el JDK 27 instalado |
| Prueba de interpretación en Swing | Correcta: temperatura, distancia, ejes distintos, botón, sensores ausentes y líneas inválidas |
| Diagrama Wokwi | `wokwi-cli lint diagram.json` terminó con código 0, sin errores; dos mensajes informativos sobre tipos de piezas en su catálogo |
| Puente Python e interfaz Java | Prueba de integración correcta con datos del ESP32 simulado: Wokwi → RFC2217 → Python → TCP → etiquetas Swing |
| Escenario Wokwi | Ejecutado correctamente: temperatura 22 → 35 °C, aceleración X 0 → 9,807 m/s² y pulsador presionado/liberado |
| Inspección visual del simulador | Pendiente; no hay superficie de automatización de VS Code disponible en esta sesión |
| Hardware real | Java conectado a COM3. Distancia responde; temperatura recuperada; acelerómetro entrega tres ejes con ID 0x72; pulsador pendiente de corregir |

El firmware y la interfaz compilan y se verificaron las lecturas del circuito simulado. La prueba de integración confirmó en Swing temperatura de 22 °C, distancia de 75,63 cm (deslizador a 75 cm), aceleración X/Y de 0 y Z de 9,81 m/s², y pulsador libre. El montaje físico sigue pendiente. El token CI se cargó desde la variable de usuario de Windows, sin mostrarlo ni copiarlo al proyecto.

## Prueba física de la placa aislada — 21 de octubre de 2026

Windows reconoce `Silicon Labs CP210x USB to UART Bridge (COM3)`, VID/PID `10C4:EA60`, sin errores. La carga del firmware mediante `scripts/upload.ps1 -Port COM3` terminó correctamente, con verificación de hash. La placa se identificó como ESP32-D0WD-V3, revisión v3.1.

La lectura a 115200 baudios confirmó `INFO,READY` y tres líneas `DATA1,-9999.00,-1.00,-9999.000,-9999.000,-9999.000,0`. Estas lecturas son coherentes con el ESP32 desconectado de todos los sensores; no constituyen una prueba de los módulos físicos. Registro: `tools/hardware-isolated.log`. Se cerró el puerto después de la comprobación para dejarlo disponible a Java.

Se regeneraron el HTML, Markdown, JSON y los tres planos principales con las cinco resistencias de 2 kΩ. Se comprobaron las posiciones libres, enlaces y sintaxis SVG, y se revisaron visualmente los tres PNG. Los 21 cables conservan sus posiciones.

La compilación emitió avisos de bibliotecas externas OneWire y esptool; no impidieron generar el firmware. Se probaron tanto muestras sintéticas del protocolo DATA1 como datos reales del simulador. Las etiquetas Swing se verificaron por programa, sin inspección visual de la ventana. Registros: `tools/wokwi-serial.log` y `tools/wokwi-integration.log`.

## Adaptación con resistencias de 2 kΩ

Se actualizó `diagram.json` para representar cinco resistencias físicas de 2 kΩ: dos en paralelo para el tramo superior del divisor (equivalente 1 kΩ), una de 2 kΩ a GND y dos en serie como pull-up de temperatura (equivalente 4 kΩ). El escenario `scripts/test-wokwi.ps1` volvió a pasar completo con este circuito. El firmware y los 21 cables del montaje real se mantienen.

`scripts/render-2k.py` comprueba los equivalentes, el divisor nominal de 3,333 V, la corriente del pull-up y que no se dupliquen agujeros entre cables y resistencias. Se revisó visualmente `docs/montaje/04-resistencias-2k.png`. La simulación digital no sustituye comprobar valores, tolerancias y voltajes del montaje físico. Instrucciones: `docs/montaje/SOLO-2K.md`.

## Circuito conectado y Java — 21 de octubre de 2026

La lectura de ocho muestras en COM3 confirmó temperatura entre 26,12 y 26,19 °C y distancia cambiante entre 35,76 y 161,24 cm. Una captura posterior confirmó aproximadamente 26,3 °C y distancia de 3,89–5,80 cm al acercar la mano, con retorno a unos 161 cm. Se guardaron `tools/hardware-connected.log`, `tools/hardware-connected.json` y `tools/hardware-diagnostic.log`.

Los ejes del MPU6050 permanecen en -9999. Se añadió un diagnóstico de arranque que recorre las direcciones I²C y lee WHO_AM_I en 0x68/0x69 si hay respuesta. En el montaje real informa `INFO,I2C,DEVICES=0` y `ERROR,MPU6050_NO_DETECTADO`: no se trata de un MPU detectado en una dirección alternativa. La revisión física de alimentación, GND, SDA, SCL y AD0 queda pendiente. El LED del módulo no verifica la conexión I²C.

Se compiló y cargó este firmware con verificación de hash. La prueba Java de interpretación y el escenario Wokwi completo volvieron a pasar; en Wokwi el diagnóstico sí detectó 0x68 y WHO_AM_I=0x68.

Se añadió el argumento opcional `--port COM3` para conectar automáticamente la ventana Swing al puerto físico. La aplicación se inició y su registro `tools/java-hardware-live.log` confirmó la recepción de muestras reales con temperatura y distancia válidas. Java queda abierto en COM3. El puerto debe liberarse cerrando la ventana antes de otra carga o prueba por terminal. No se verificó visualmente la ventana mediante automatización; se confirmó su título de proceso y el flujo de recepción del programa.

El pulsador estuvo en estado 0 (LIBRE) durante las capturas iniciales; se solicitó repetir la pulsación con Java leyendo de forma continua antes de atribuirlo a un fallo de cableado.

### Observación continua y pulsador

En la lectura continua de Java, el sensor de temperatura dejó de producir valores válidos y pasó a -9999, mientras la distancia siguió llegando. Por tanto, la lectura térmica fue intermitente y todavía no está validada como estable. El usuario confirmó que la casilla del pulsador permanece en LIBRE durante una pulsación prolongada. Se solicitó una prueba de puente momentáneo entre A20 y J20 de la pequeña para distinguir los contactos del pulsador de su ruta de señal y tierra; el resultado está pendiente. No se ha concluido que el módulo MPU o la sonda estén dañados: la revisión de conexiones y alimentación continúa pendiente.

### Acelerómetro compatible 0x72 y respuesta del botón

Tras volver a comprobar el circuito, la temperatura se recuperó (aproximadamente 27 °C). El nuevo escaneo detectó un dispositivo en 0x68 y WHO_AM_I=0x72, aunque el escaneo anterior no encontraba ninguno. El código de Adafruit instalado rechaza explícitamente cualquier ID distinto de 0x68. La presencia I²C y el ID no estándar se registraron en `tools/hardware-mpu-retry.log`.

Se implementó una ruta específica para 0x72, sin modificar los archivos de la biblioteca: tres relecturas de identidad, activación, configuración de ±4 g y verificación de registros antes de aceptar el modo compatible. Se verifican las transacciones y el número de bytes leídos. Si falla la lectura, se informa como inválida y se reintenta. Para ID 0x68 se mantiene la biblioteca Adafruit. Se admiten direcciones 0x68 y 0x69.

Con este firmware cargado y verificado en COM3 se recibieron muestras como `DATA1,26.44,160.23,-6.829,-6.595,0.079,0`. El registro `tools/hardware-compatible72.log` contiene las muestras y la identificación compatible. Java volvió a abrirse en COM3 y recibió los tres ejes; registro `tools/java-hardware-fixed.log`. Esto confirma la lectura real, no una calibración ni la identidad exacta del fabricante.

Se añadieron eventos `BUTTON,0/1` tras el antirrebote y su interpretación inmediata en Java. La prueba Java cubre ambos eventos y volvió a pasar. El escenario Wokwi completo también pasó con la ruta Adafruit y los eventos de botón. La prueba física del pulsador sigue pendiente: se solicitó mover temporalmente el extremo del cable 20 desde P:A20 a G:D6 (GND) para comprobar el cable y GPIO27, manteniendo el otro extremo en D27. Después debe volver a A20.

### Cambios posteriores en el cableado físico

El usuario confirmó que unir directamente D27 con GND del ESP32 sí produjo PULSADO; se retiró durante esa prueba la tierra de los sensores y sus lecturas se perdieron. Esto verifica la entrada GPIO27 y la respuesta de Java, pero no verifica el cable 20 ni la distribución de GND de la protoboard.

Después de restaurar conexiones y probar otro puente A20–J20, el usuario informó que el botón seguía libre y el acelerómetro volvió a perder sus lecturas. El registro de Java confirma temperatura y distancia válidas, GPIO27 alto y reintentos sin respuesta del MPU en 0x68/0x69. La pérdida actual no demuestra daño del sensor: anteriormente se configuró y leyó su ID 0x72 correctamente. Hace falta inspeccionar fotografías del montaje actual (las disponibles solo muestran piezas sueltas), conexiones de GND y contactos. No se ha cambiado nuevamente el firmware ni se ha concluido una avería física.
