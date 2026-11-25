param([Parameter(Mandatory=$true)][ValidatePattern('^COM\d+$')][string]$Port)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  & .\.venv\Scripts\python.exe -m platformio run -t upload --upload-port $Port
  if ($LASTEXITCODE -ne 0) { throw 'Falló la carga al ESP32' }
} finally { Pop-Location }
