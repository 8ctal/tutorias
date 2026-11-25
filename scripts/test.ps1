$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  & javac --release 25 -encoding UTF-8 -cp 'java-swing/target/classes;tools/jSerialComm-2.11.4.jar' -d java-swing/target/test-classes java-swing/src/test/java/com/ejemplo/monitor/MonitorSmokeTest.java
  if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de la prueba' }
  & java --enable-native-access=ALL-UNNAMED -cp 'java-swing/target/classes;java-swing/target/test-classes;tools/jSerialComm-2.11.4.jar' com.ejemplo.monitor.MonitorSmokeTest
  if ($LASTEXITCODE -ne 0) { throw 'Falló la prueba Java' }
  & .\tools\wokwi-cli.exe lint diagram.json
  if ($LASTEXITCODE -ne 0) { throw 'Falló la validación del diagrama' }
} finally { Pop-Location }
