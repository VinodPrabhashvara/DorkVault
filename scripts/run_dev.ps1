param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

Set-Location $projectRoot

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv with Python 3.12..."
    py -3.12 -m venv .venv
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment creation failed. Ensure Python 3.12 is available via the py launcher."
}

if (-not $SkipInstall) {
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
}

$env:PYTHONPATH = Join-Path $projectRoot "src"
& $venvPython -m dorkvault

