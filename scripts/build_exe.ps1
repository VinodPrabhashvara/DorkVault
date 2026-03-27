param(
    [switch]$Clean,
    [switch]$SkipInstall,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$specPath = Join-Path $projectRoot "DorkVault.spec"
$buildDir = Join-Path $projectRoot "build"
$distDir = Join-Path $projectRoot "dist"

Set-Location $projectRoot

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv with Python 3.12..."
    py -3.12 -m venv .venv
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment creation failed. Ensure Python 3.12 is available via the py launcher."
}

if (-not (Test-Path $specPath)) {
    throw "PyInstaller spec file not found: $specPath"
}

if ($Clean) {
    foreach ($targetPath in @($buildDir, $distDir)) {
        if (Test-Path $targetPath) {
            Remove-Item -LiteralPath $targetPath -Recurse -Force
        }
    }
}

if (-not $SkipInstall) {
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
    & $venvPython -m pip install -e .
}

if (-not $SkipTests) {
    & $venvPython -m pytest
}

& $venvPython -m PyInstaller --noconfirm --clean $specPath

Write-Host "Build complete. Check the dist\\DorkVault directory."
