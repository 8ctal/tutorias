$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  & .\.venv\Scripts\python.exe -m platformio run
  if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación ESP32' }
  New-Item -ItemType Directory -Force java-swing\target\classes | Out-Null
  & javac --release 25 -encoding UTF-8 -cp tools\jSerialComm-2.11.4.jar -d java-swing\target\classes java-swing\src\main\java\com\ejemplo\monitor\MonitorSensoresApp.java
  if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación Java' }
} finally { Pop-Location }
