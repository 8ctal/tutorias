$ErrorActionPreference = 'Stop'
$secureToken = Read-Host 'Token de https://wokwi.com/dashboard/ci (entrada oculta)' -AsSecureString
$tokenValue = [System.Net.NetworkCredential]::new('', $secureToken).Password
try {
  if ([string]::IsNullOrWhiteSpace($tokenValue)) { throw 'El token está vacío' }
  [Environment]::SetEnvironmentVariable('WOKWI_CLI_TOKEN', $tokenValue, 'User')
  $env:WOKWI_CLI_TOKEN = $tokenValue
  Write-Host 'Token configurado en las variables de usuario de Windows. No se guardó en el proyecto.'
} finally {
  $tokenValue = $null
  $secureToken.Dispose()
}
