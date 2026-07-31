param(
  [string]$ImagePath = ".\selfie_auth.jpg",
  [string]$OutputZip = ".\smartselfie_register.zip",
  [switch]$CopyBase64ToClipboard = $true
)

$ErrorActionPreference = "Stop"

$templatePath = "docs/smile-id/templates/smartselfie-auth.info.json"
if (-not (Test-Path -LiteralPath $templatePath)) {
  throw "Template introuvable: $templatePath"
}

if (-not (Test-Path -LiteralPath $ImagePath)) {
  throw "Image introuvable: $ImagePath"
}

$workDir = Join-Path $env:TEMP ("smartselfie_register_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workDir | Out-Null

try {
  Copy-Item -LiteralPath $templatePath -Destination (Join-Path $workDir "info.json") -Force
  Copy-Item -LiteralPath $ImagePath -Destination (Join-Path $workDir "selfie_auth.jpg") -Force

  if (Test-Path -LiteralPath $OutputZip) {
    Remove-Item -LiteralPath $OutputZip -Force
  }

  Compress-Archive -Path (Join-Path $workDir "*") -DestinationPath $OutputZip -Force

  $zipBytes = [System.IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $OutputZip))
  $zipBase64 = [System.Convert]::ToBase64String($zipBytes)

  if ($CopyBase64ToClipboard) {
    $zipBase64 | Set-Clipboard
  }

  Write-Host "ZIP genere: $OutputZip"
  Write-Host "Image source: $ImagePath"
  if ($CopyBase64ToClipboard) {
    Write-Host "Base64 copiee dans le presse-papiers (variable Postman: zipBase64)."
  } else {
    Write-Host "Base64:"
    Write-Output $zipBase64
  }
} finally {
  if (Test-Path -LiteralPath $workDir) {
    Remove-Item -LiteralPath $workDir -Recurse -Force
  }
}
