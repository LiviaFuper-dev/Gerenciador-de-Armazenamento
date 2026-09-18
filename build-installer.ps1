param(
    [switch]$IncludeSecret
)

$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectDir

$compilerCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $compiler) {
    throw "Inno Setup 6 não encontrado. Instale-o antes de criar o instalador."
}

if (-not (Test-Path -LiteralPath "dist\GerenciadorDeArmazenamento.exe" -PathType Leaf)) {
    throw "Executável não encontrado. Execute .\build.ps1 primeiro."
}

$version = & ".\.venv\Scripts\python.exe" -c "from storage_manager import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0 -or -not $version) {
    throw "Não foi possível determinar a versão do aplicativo."
}

$outputName = "GerenciadorDeArmazenamento-v$version-windows-setup"
$arguments = @(
    "/DMyAppVersion=$version",
    "/DOutputBaseFilename=$outputName"
)

if ($IncludeSecret) {
    if (-not (Test-Path -LiteralPath "client_secret.json" -PathType Leaf)) {
        throw "client_secret.json não encontrado para o instalador interno."
    }
    $outputName = "GerenciadorDeArmazenamento-v$version-interno-setup"
    $arguments[1] = "/DOutputBaseFilename=$outputName"
    $arguments += "/DIncludeSecret=1"
}

$arguments += "installer.iss"
& $compiler @arguments
if ($LASTEXITCODE -ne 0) {
    throw "O Inno Setup não conseguiu gerar o instalador."
}

Write-Host "Instalador criado em dist\$outputName.exe"
