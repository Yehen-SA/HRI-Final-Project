# Build the Windows .exe into exe_build\, using PyInstaller.
#
# Run on Windows (needs uv: https://docs.astral.sh/uv/), from PowerShell:
#
#     powershell -ExecutionPolicy Bypass -File build_exe.ps1
#
# The repo lives in WSL, and building straight from \\wsl$ is slow and unreliable, so this
# copies python_build\ to a temporary Windows folder, builds there, and copies the .exe back
# into exe_build\. Nothing is deleted; existing files are overwritten.

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Here "python_build"
$Work = Join-Path $env:TEMP "hri_breakout_exe_build"
$Output = Join-Path $Here "exe_build"

Write-Host "Copying the game to $Work ..."
# robocopy: /E copies subfolders; /XD skips these folders. Exit codes below 8 mean success.
robocopy $Source $Work /E /NFL /NDL /NJH /NJS /XD .venv logs __pycache__ .voice_cache .pytest_cache .ruff_cache tests | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Copying failed (robocopy exit code $LASTEXITCODE)" }

Push-Location $Work
try {
    Write-Host "Building with PyInstaller (the first run downloads Python packages) ..."
    uv run --no-dev --with pyinstaller pyinstaller --noconfirm --onefile --windowed `
        --name HRI_Breakout --paths src --add-data "assets;assets" src/main.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit code $LASTEXITCODE)" }
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $Output | Out-Null
Copy-Item (Join-Path $Work "dist\HRI_Breakout.exe") $Output -Force
Write-Host ""
Write-Host "Done: $Output\HRI_Breakout.exe"
Write-Host "Send subjects that file plus the instructions in exe_build\README.md."
Write-Host "Their results go in a logs folder next to the exe."
