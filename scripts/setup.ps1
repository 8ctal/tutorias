$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  if (!(Test-Path .venv\Scripts\python.exe)) { & python -m venv .venv }
  & .\.venv\Scripts\python.exe -m pip install platformio==6.2.0 pyserial==3.5
  if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación Python' }
  New-Item -ItemType Directory -Force tools | Out-Null
  if (!(Test-Path tools\wokwi-cli.exe)) {
    Invoke-WebRequest https://github.com/wokwi/wokwi-cli/releases/download/v0.29.0/wokwi-cli-win-x64.exe -OutFile tools\wokwi-cli.exe
  }
  if (!(Test-Path tools\jSerialComm-2.11.4.jar)) {
    Invoke-WebRequest https://repo.maven.apache.org/maven2/com/fazecast/jSerialComm/2.11.4/jSerialComm-2.11.4.jar -OutFile tools\jSerialComm-2.11.4.jar
  }
  & "$PSScriptRoot/build.ps1"
} finally { Pop-Location }
