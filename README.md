# Monitor multisensor ESP32

Un ESP32 mide temperatura, distancia, aceleración en tres ejes y el estado de un pulsador. Las lecturas se pueden ver en una aplicación Java Swing o en un dashboard web. Puedes usar una placa física o simular el circuito en Wokwi.

## 1. Instala los requisitos

La guía usa Windows x64 y PowerShell. Instala estas herramientas y abre una terminal nueva para que tome los cambios de PATH.

| Herramienta | Cuándo se necesita | Comprueba con |
|---|---|---|
| Git para Windows | Para clonar el repositorio | `git --version` |
| Python 3.12 | Para PlatformIO y el puente Wokwi. Durante la instalación, agrega Python al PATH | `python --version` |
| JDK 25 o posterior | Para compilar y ejecutar Swing. Agrega el directorio bin del JDK al PATH | `java -version` y `javac -version` |
| VS Code y la extensión Wokwi | Para simular sin una placa física. Activa el acceso a Wokwi en la extensión | `code --version` |
| Node.js 22, pnpm 10 y Chrome de escritorio | Para el dashboard web. Instala pnpm con `npm install -g pnpm@10.0.0` | `node --version` y `pnpm --version` |

La primera instalación necesita internet para descargar las dependencias. Maven es opcional.

## 2. Clona y compila

Ejecuta los comandos desde PowerShell. La URL SSH requiere una clave registrada en GitHub y acceso al repositorio.

```powershell
git clone git@github.com:8ctal/proyecto_poo_final.git
cd proyecto_poo_final
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

El instalador crea `.venv`, instala PlatformIO 6.2.0 y pyserial 3.5, descarga Wokwi CLI 0.29.0 y jSerialComm 2.11.4 en `tools/` y compila el firmware y Swing. PlatformIO descarga Arduino para ESP32 y las bibliotecas declaradas en [platformio.ini](platformio.ini). El firmware queda en `.pio/build/esp32dev/firmware.bin` y las clases Java en `java-swing/target/classes`.

Después de modificar el código, recompila desde la raíz.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

## 3. Ejecuta con Wokwi

1. Abre la carpeta con `code .`. Instala la extensión con `code --install-extension wokwi.wokwi-vscode` si hace falta.
2. En VS Code, pulsa **F1** y selecciona **Wokwi: Start Simulator**. En la consola del simulador deben aparecer `INFO,READY` y líneas `DATA1`.
3. Cambia la temperatura, la distancia o los ejes haciendo clic en los sensores del circuito. Mantén presionado el pulsador durante un segundo para verlo también en las muestras periódicas.
4. Mantén activo el simulador y ejecuta el puente en una terminal desde la raíz.

   ```powershell
   .\.venv\Scripts\python.exe scripts/bridge.py
   ```

5. En otra terminal, inicia Swing y pulsa **Wokwi**. Si prefieres el navegador, inicia el dashboard como se indica más abajo y pulsa **Wokwi** allí.

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/monitor.ps1
   ```

Wokwi usa RFC2217 en `127.0.0.1:4000`. El puente expone las lecturas en `127.0.0.1:4001` y admite un cliente a la vez. Si ves una conexión rechazada, comprueba que el simulador y el puente sigan en ejecución y vuelve a conectar.

## 4. Ejecuta con una placa física

Necesitas un ESP32 DevKit, un sensor de temperatura DS18x20 de tres hilos, un MPU6050 o módulo compatible, un HC-SR04, un pulsador, dos protoboards, cables de conexión, cinco resistencias de 2 kΩ para el montaje actual y un cable USB de datos.

1. Con la placa desconectada, arma el circuito según la [guía ilustrada](docs/montaje/index.html) y el [montaje con cinco resistencias de 2 kΩ](docs/montaje/SOLO-2K.md). El HC-SR04 usa alimentación de 5 V y un divisor entre ECHO y GPIO19. Une las tierras de todos los módulos y verifica el pinout del sensor de temperatura antes de alimentar.
2. Conecta la placa por USB e identifica el puerto. Si no aparece, identifica el chip USB–serie de tu placa e instala su controlador oficial.

   ```powershell
   .\.venv\Scripts\python.exe -m serial.tools.list_ports
   ```

3. Cierra los monitores serie que estén usando el puerto y sube el firmware. Cambia `COM5` por el puerto identificado.

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/upload.ps1 -Port COM5
   ```

4. Inicia Swing con el mismo puerto. También puedes abrirlo sin `-Port` y usar **Buscar puertos** y **Conectar**.

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/monitor.ps1 -Port COM5
   ```

El puerto funciona a 115200 baudios y solo puede ocuparlo un monitor a la vez. Para usar el dashboard por USB, desconecta Swing y selecciona **Conectar por USB** en Chrome. USB lee el puerto directamente.

## 5. Abre el dashboard web

Desde la raíz del repositorio, instala las dependencias y arranca el servidor.

```powershell
pnpm --dir websocket install --frozen-lockfile
pnpm --dir websocket start
```

Abre el [dashboard local](http://127.0.0.1:13000/dashboard) en Chrome de escritorio. Para hardware selecciona **Conectar por USB** y elige el puerto en Chrome. Para simulación mantén abiertos Wokwi y el puente Python, luego selecciona **Wokwi**. Usa **Desconectar** antes de cambiar de cliente. La [demostración WebSocket](http://127.0.0.1:13000/) está disponible en la raíz del servidor.

## Pruebas

Después de compilar, ejecuta la prueba Java y la validación del diagrama.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
```

Para ejecutar el escenario automatizado de Wokwi, genera un token en el [panel de Wokwi CI](https://wokwi.com/dashboard/ci). El primer script solicita el token con entrada oculta y lo guarda en el entorno del usuario de Windows. El segundo ejecuta el escenario de temperatura, aceleración y pulsador. Comprueba el ultrasónico manualmente desde el simulador.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/set-wokwi-token.ps1
powershell -ExecutionPolicy Bypass -File scripts/test-wokwi.ps1
```

## Protocolo serie

```text
DATA1,temperatura_C,distancia_cm,ax_m_s2,ay_m_s2,az_m_s2,boton
DATA1,22.00,75.00,0.000,0.000,9.807,0
```

El pulsador vale 1 cuando está presionado y 0 cuando está libre. El firmware también emite `BUTTON,1` o `BUTTON,0` al cambiar el estado. El valor `-9999` indica una lectura inválida y una distancia de `-1` indica ausencia de eco.

## Código, bibliotecas y documentación

- Firmware y dependencias Arduino en [src/main.cpp](src/main.cpp) y [platformio.ini](platformio.ini). El circuito de simulación está en [diagram.json](diagram.json).
- Monitor Swing en [java-swing/](java-swing/), con [guía](java-swing/GUIA.md) y jSerialComm declarado también en [pom.xml](java-swing/pom.xml).
- Dashboard en [websocket/](websocket/), con `ws` fijado por [pnpm-lock.yaml](websocket/pnpm-lock.yaml) y [documentación del servidor](websocket/SERVER-DOCUMENTATION.md).
- [Guía de montaje](docs/montaje/MONTAJE.md), [validación y observaciones de hardware](VALIDACION.md), [diapositivas PowerPoint](Monitor%20de%20sensores%20ESP32.pptx), [presentación web](docs/presentacion/index.html) y [guion](docs/presentacion/GUION.md).
