# Guion de exposición: ESP32 y Java Swing

La presentación contiene 19 diapositivas. Duración orientativa: 15–20 minutos. Abre index.html, navega con las flechas y usa N para consultar las notas. F activa pantalla completa. El botón PDF / Imprimir permite guardar las diapositivas desde el navegador; elige orientación horizontal, gráficos de fondo y sin encabezados ni pies de página. Las imágenes están incorporadas: el HTML funciona sin conexión.

## 1. Monitor multisensor con ESP32 y Java

Presentar el objetivo: adquirir medidas del circuito y convertirlas en información visible mediante una aplicación Java. El firmware del ESP32 está escrito en C++, mientras que el programa de escritorio está escrito en Java. No se mide humedad.

## 2. Qué hace el sistema

Explicar la separación de responsabilidades. El MPU-6050 dispone de más capacidades, pero este programa transmite solo aceleración. El puente Python es necesario para la ruta del simulador, no para USB real.

## 3. Conexiones del circuito

Reutilización del plano docs/montaje/01-conexiones.png. Señalar GPIO4 para temperatura, GPIO21/22 para I2C, GPIO18/19 para ultrasonido y GPIO27 para el botón. Las etiquetas de pines determinan las conexiones.

## 4. Pines y alimentación

Fuente: docs/montaje/MONTAJE.md y src/main.cpp. El firmware convierte LOW en botón presionado y transmite 1. El antirrebote es de 30 ms. Revisar los contactos reales del pulsador por continuidad antes de alimentar.

## 5. Distribución en la protoboard grande

Fuente: docs/montaje/02-protoboard-grande.png. G1, G2 y siguientes son grupos contados desde el extremo izquierdo según la guía, no necesariamente la numeración impresa. Se usa A–E y no se usan carriles laterales. El ESP32 y los módulos quedan fuera de las rejillas.

## 6. Divisor de ECHO y pulsador

Fuente: docs/montaje/03-protoboard-pequena.png. Dos resistencias de 2 kΩ en paralelo forman el tramo superior de 1 kΩ. R2 de 2 kΩ conecta el nodo GPIO19 a GND. Los contactos del botón deben pertenecer a lados eléctricamente distintos.

## 7. Adaptación con cinco resistencias de 2 kΩ

Fuente: docs/montaje/SOLO-2K.md y 04-resistencias-2k.png. ECHO no va directo al ESP32. El adaptador térmico puede incorporar pull-up: la guía indica cómo comprobarlo. Estos son valores nominales, la simulación digital no verifica las tolerancias ni el voltaje físico.

## 8. El contrato de datos entre ESP32 y Java

Fuentes: Serial.printf en src/main.cpp y processLine en MonitorSensoresApp.java. DATA1 diferencia este protocolo de la versión anterior DATA. La línea mostrada coincide con las medidas registradas en la integración simulada.

## 9. Estructura de la aplicación Java

Extracto abreviado de la clase real. Explicar que final conserva la referencia, pero una JLabel sigue siendo modificable con setText. volatile facilita visibilidad entre hilos, pero no vuelve atómicas las operaciones compuestas. Los componentes Swing se deben modificar en su hilo de eventos.

## 10. Interfaz gráfica y eventos

Fuente: constructor y buildUi de MonitorSensoresApp.java. Explicar programación dirigida por eventos: el programa reacciona a clics y a datos entrantes. metricPanel reutiliza la construcción de cada indicador, valueLabel unifica el formato.

## 11. Conexión USB con jSerialComm

Fuente: connectToSelectedPort y refreshPorts. Fragmento abreviado con comentario explicativo. El firmware usa la misma velocidad. Cerrar otros monitores serie para evitar que ocupen el puerto. PortOption conserva el objeto SerialPort y su nombre, y sobreescribe toString para mostrar una descripción útil en el JComboBox.

## 12. Recepción: reconstruir líneas completas

Fuente: serialEvent dentro de connectToSelectedPort. El bucle está dentro de synchronized(partialLine). b & 0xFF interpreta el byte sin signo. El protocolo usa caracteres ASCII, por lo que este tratamiento basta para sus campos. El límite de 512 evita crecimiento indefinido de una línea sin terminador. Esta lógica acumula fragmentos y separa varias líneas recibidas juntas.

## 13. processLine(): validar y convertir

Fuente: processLine. El fragmento termina antes de actualizar Swing y muestra el inicio del bloque try. La comprobación de formato no valida todos los rangos físicos ni exige que el botón sea exclusivamente 0 o 1: el programa interpreta exactamente 1 como pulsado. Presentarlo como validación del formato, no como validación exhaustiva.

## 14. Hilos: actualización segura de Swing

Fuente: processLine y main. También main crea la ventana mediante invokeLater. Explicar que bloquear el EDT con lecturas impediría responder a los clics o repintar. Cada eje usa su propia variable, evitando repetir accidentalmente la misma lectura.

## 15. Errores de sensores y formato visible

Fuente: formatValue, processLine y appendConsole. La comparación <= -1000 detecta el centinela -9999 y otros valores fuera de ese umbral. El formato usa punto decimal para ser consistente. El historial elimina las primeras 101 líneas al superar el límite, según getLineEndOffset(100). No se añade ninguna persistencia en disco.

## 16. Simulación: TCP sin bloquear la ventana

Fuente: connectSimulation, scripts/bridge.py y README.md. El fragmento está dentro de un Thread daemon con try/catch/finally. El timeout de 3000 ms se aplica a la conexión, no a todas las lecturas posteriores. El puente escucha solo en 127.0.0.1 y admite un monitor conectado.

## 17. Desconexión y liberación de recursos

Fuente: disconnect, constructor y finally de connectSimulation. Extracto inicial de disconnect. El finally compara connectionGeneration con attempt antes de programar la desconexión. Explicar la importancia de cerrar recursos para permitir futuras conexiones y la carga del firmware.

## 18. Pruebas y estado real del proyecto

Fuentes: VALIDACION.md, README.md y MonitorSmokeTest.java. Son resultados previamente documentados, no pruebas nuevas ejecutadas al crear esta presentación. La prueba de integración revisó etiquetas por programa, sin inspección visual de la ventana. El escenario Wokwi comprobó temperatura 22 a 35 °C, aceleración X y pulsador.

## 19. Demostración y aporte de Java

Para USB real se selecciona el COM y se pulsa Conectar, sin puente Python. No presentar sensores físicos como probados mientras siga pendiente la prueba completa. Cerrar recordando que el circuito produce datos y Java les da estructura y una interfaz comprensible. Si se pierde conexión con Wokwi, revisar que el simulador esté activo y el puente iniciado.

## Fuentes locales

- `src/main.cpp`
- `java-swing/src/main/java/com/ejemplo/monitor/MonitorSensoresApp.java`
- `java-swing/src/test/java/com/ejemplo/monitor/MonitorSmokeTest.java`
- `docs/montaje/MONTAJE.md` y `SOLO-2K.md`
- Planos `docs/montaje/01-conexiones.png` a `04-resistencias-2k.png`
- `README.md` y `VALIDACION.md`

Los fragmentos de código conservan el comportamiento del original; algunas diapositivas omiten líneas para facilitar la explicación. Los resultados de pruebas corresponden al estado documentado del proyecto al 21 de octubre de 2026.