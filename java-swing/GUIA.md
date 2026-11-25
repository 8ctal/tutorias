# Cómo funciona el monitor Java Swing

1. **Abrir la ventana.** `main` valida el argumento opcional `--port COM3` y crea la aplicación en el hilo de eventos de Swing (EDT). El constructor arma la vista y enumera los puertos. El argumento selecciona y abre el puerto al arrancar.
2. **Conectar por USB.** `connectToSelectedPort` configura el puerto a 115200 baudios, 8 bits, sin paridad y un bit de parada. jSerialComm entrega bytes al listener. El listener une los fragmentos hasta el salto de línea y descarta líneas mayores de 512 caracteres.
3. **Conectar a Wokwi.** `connectSimulation` crea un socket y arranca un hilo lector. `readSimulation` conecta con el puente en `127.0.0.1:4001` y lee texto UTF-8 línea por línea. El hilo de Swing sigue disponible mientras espera datos.
4. **Interpretar una línea.** Ambos modos llaman a `processLine` en el EDT. Cada línea aparece en la consola. Una muestra `DATA1` trae temperatura, distancia, tres ejes de aceleración y pulsador. Las lecturas inválidas de temperatura o aceleración se muestran como `--` y una distancia negativa como `Sin eco`. Un evento `BUTTON,0` o `BUTTON,1` cambia solo la tarjeta del pulsador de inmediato.
5. **Cerrar la conexión.** `disconnect` invalida primero la conexión actual, libera el puerto o el socket y habilita los botones de conexión. Cualquier lectura en cola de esa sesión se descarta en el EDT.

## Ejemplo

Para `DATA1,22.50,75.25,1.250,2.500,9.807,0`, la ventana muestra 22.50 °C, 75.25 cm, 1.25, 2.50 y 9.81 m/s², y el pulsador en LIBRE. Si la siguiente línea es `BUTTON,1`, el pulsador pasa a PULSADO y las otras lecturas se conservan.

Desde la raíz del proyecto, ejecuta `powershell -ExecutionPolicy Bypass -File scripts/monitor.ps1` para abrir Swing. El script de compilación es `scripts/build.ps1` y el de pruebas es `scripts/test.ps1`.
