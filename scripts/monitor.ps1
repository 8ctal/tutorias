param([ValidatePattern('^COM\d+$')][string]$Port)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  $monitorArgs = @()
  if ($Port) { $monitorArgs = @('--port', $Port) }
  & java --enable-native-access=ALL-UNNAMED -cp 'java-swing/target/classes;tools/jSerialComm-2.11.4.jar' com.ejemplo.monitor.MonitorSensoresApp @monitorArgs
} finally { Pop-Location }
