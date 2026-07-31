# Templates Smile ID `info.json`

Ces templates servent pour le flux REST `upload-url + ZIP`.

## Fichiers

- `biometric-kyc-ng-nin_v2.info.json`
- `smartselfie-auth.info.json`
- `document-verification-cg.info.json`

## A quoi ca sert

- Ce fichier decrit les metadonnees KYC (`id_info`) et les images (`images`) que Smile ID doit traiter.
- Il doit etre place a la racine du ZIP avec les images referencees par `file_name`.

## Utilisation (manuel, pas automatique)

1. Appeler `POST /kyc/biometric/upload-url` (ou smartselfie upload-url) pour obtenir `upload_url`.
2. Preparer un dossier:
   - `info.json` (copie du template adapte)
   - les images `.jpg` referencees dans `images[].file_name`
3. Compresser en `.zip` (sans sous-dossier superflu).
4. Encoder le ZIP en base64.
5. Appeler `POST /kyc/biometric/upload-zip` ou `POST /kyc/smartselfie/upload-zip`.

## Script PowerShell (sandbox Biometric)

Ce script cree un ZIP Biometric propre (avec `info.json` a la racine) puis calcule la base64 pour Postman.

```powershell
# Depuis la racine du projet
$workDir = "biometric-sandbox"
$zipPath = "biometric_kyc_ng_nin_v2.zip"

New-Item -ItemType Directory -Force -Path $workDir | Out-Null
Copy-Item "docs/smile-id/templates/biometric-kyc-ng-nin_v2.info.json" "$workDir/info.json" -Force

# Ajoute ici tes images reelles correspondant aux noms attendus par info.json
# Exemple:
# Copy-Item "selfie_auth.jpg" "$workDir/selfie.jpg" -Force
# Copy-Item "liveness_1.jpg" "$workDir/liveness_1.jpg" -Force
# ...

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$workDir/*" -DestinationPath $zipPath -Force

$zipBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $zipPath))
$zipBase64 = [System.Convert]::ToBase64String($zipBytes)
$zipBase64 | Set-Clipboard

Write-Host "ZIP cree: $zipPath"
Write-Host "zipBase64 copie dans le presse-papiers."
```

Utilisation Postman:

1. Coller la base64 dans la variable `zipBase64Biometric`.
2. Appeler `POST /kyc/biometric/upload-url`.
3. Copier `upload.upload_url` dans `biometricUploadUrl`.
4. Copier `jobId` dans `biometricJobId`.
5. Appeler `POST /kyc/biometric/upload-zip`.
6. Appeler `POST /kyc/utils/job-status` avec `jobType = "1"`.

## Image types recommandes ici (SDK Smile Identity Core)

- `0` : selfie image file (`.jpg` / `.png`)
- `1` : ID card front image file
- `4` : liveness image file
- `5` : ID card back image file

Important:
- Si tu utilises `file_name`, utilise les image types `*_FILE` (0/1/4/5).
- Si tu utilises `image` en base64, utilise les image types `*_BASE64` (2/3/6/7).
