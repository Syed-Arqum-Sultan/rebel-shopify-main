# Create/update tools/photo_pipeline/.venv and install requirements into it.
# Usage (from repo root): powershell -ExecutionPolicy Bypass -File tools/photo_pipeline/install.ps1
$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
$Req = Join-Path $Here "requirements.txt"
$Venv = Join-Path $Here ".venv"
$VenvPy = Join-Path $Venv "Scripts\python.exe"

function Find-BasePython {
    foreach ($name in @("python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -notmatch "WindowsApps") {
            return $cmd.Source
        }
    }
    $local = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path $local) {
        $p = Get-ChildItem -Path $local -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^Python3\d+$' } |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($p) {
            $exe = Join-Path $p.FullName "python.exe"
            if (Test-Path $exe) { return $exe }
        }
    }
    return $null
}

$py = Find-BasePython
if (-not $py) {
    Write-Host "Python 3 was not found. Install with: winget install -e --id Python.Python.3.12" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $VenvPy)) {
    Write-Host "Creating venv at $Venv ..."
    & $py -m venv $Venv
}

Write-Host "Using venv: $VenvPy"
& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r $Req
Write-Host "Done. From repo root run:" -ForegroundColor Green
Write-Host ('  "{0}" -m tools.photo_pipeline.cli --input <dir> --output <dir> --preset tools/photo_pipeline/config/preset_pdp_dark.json' -f $VenvPy)
