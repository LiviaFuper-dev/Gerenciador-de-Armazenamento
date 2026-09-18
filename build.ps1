$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDir

if (-not (Test-Path -LiteralPath ".venv")) {
    py -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar o pip." }
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependências." }
& ".\.venv\Scripts\python.exe" -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam; o executável não será gerado." }
Remove-Item -LiteralPath "dist\GerenciadorDeArmazenamento" -Recurse -Force -ErrorAction SilentlyContinue
& ".\.venv\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "GerenciadorDeArmazenamento" `
    --icon "assets\app_icon.ico" `
    --add-data "app_config.json;." `
    --add-data "assets\app_icon.png;assets" `
    --add-data "assets\app_icon.ico;assets" `
    --collect-data googleapiclient `
    main.py
if ($LASTEXITCODE -ne 0) { throw "O PyInstaller não conseguiu gerar o executável." }

Write-Host "Executável criado em dist\GerenciadorDeArmazenamento.exe"
Write-Warning "Distribua client_secret.json separadamente e coloque-o ao lado do executável."
