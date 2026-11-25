$ErrorActionPreference = 'Stop'
if (!$env:WOKWI_CLI_TOKEN) {
  $env:WOKWI_CLI_TOKEN = [Environment]::GetEnvironmentVariable('WOKWI_CLI_TOKEN', 'User')
}
if (!$env:WOKWI_CLI_TOKEN) { throw 'Configure primero el token con scripts/set-wokwi-token.ps1' }
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  & .\tools\wokwi-cli.exe . --scenario scenarios/sensors.yaml --timeout 30000 --serial-log-file tools\wokwi-serial.log
  if ($LASTEXITCODE -ne 0) { throw "La prueba Wokwi terminó con código $LASTEXITCODE" }
} finally { Pop-Location }
