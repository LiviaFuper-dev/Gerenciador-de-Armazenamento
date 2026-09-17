$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDir

if (-not (Test-Path -LiteralPath ".venv")) {
    py -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --windowed `
    --name "GerenciadorDeArmazenamento" `
    --icon "assets\app_icon.ico" `
    --add-data "app_config.json;." `
    --collect-data googleapiclient `
    main.py

Copy-Item -LiteralPath "app_config.json" -Destination "dist\GerenciadorDeArmazenamento\app_config.json" -Force
if (Test-Path -LiteralPath "client_secret.json") {
    Copy-Item -LiteralPath "client_secret.json" -Destination "dist\GerenciadorDeArmazenamento\client_secret.json" -Force
} else {
    Write-Warning "client_secret.json não encontrado; a autenticação Google não funcionará nesta compilação."
}
$distAssets = "dist\GerenciadorDeArmazenamento\assets"
New-Item -ItemType Directory -Force -Path $distAssets | Out-Null
Copy-Item -LiteralPath "assets\app_icon.png" -Destination $distAssets -Force
Copy-Item -LiteralPath "assets\app_icon.ico" -Destination $distAssets -Force
Write-Host "Executável criado em dist\GerenciadorDeArmazenamento\GerenciadorDeArmazenamento.exe"
