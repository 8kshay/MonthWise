# Builds dist\Monthwise.exe (a single file that runs on any 64-bit Windows PC, no Python needed).
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".venv\Scripts\python.exe"

& $python -m unittest discover -s tests -t .
if ($LASTEXITCODE -ne 0) { throw "Tests failed; not building." }

& $python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name Monthwise `
    --icon "$PSScriptRoot\assets\monthwise.ico" `
    --add-data "$PSScriptRoot\assets\monthwise.ico;assets" `
    --add-data "$PSScriptRoot\assets\monthwise.png;assets" `
    --collect-data sv_ttk `
    --specpath build `
    main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

Write-Host "Built: $PSScriptRoot\dist\Monthwise.exe"
