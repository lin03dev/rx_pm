<#
.SYNOPSIS
    Run the full rx_pm generation pipeline on Windows.
#>

Set-StrictMode -Version Latest

$ErrorActionPreference = 'Stop'

Write-Host "==============================================="
Write-Host "  UNIFIED REPORTING SYSTEM - COMPLETE RUN"
Write-Host "===============================================`n"

if (-not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..."
    py -3.10 -m venv venv
}

Write-Host "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Write-Host "Dependencies installed`n"

Write-Host "-------------------------------------------------"
Write-Host "STEP 2: Setting up directories"
Write-Host "-------------------------------------------------"

$dirs = @(
    'output\\reports\\AG',
    'output\\reports\\LMS',
    'output\\reports\\Telios',
    'output\\reports\\Language',
    'output\\templates\\AG',
    'output\\templates\\LMS',
    'output\\templates\\Telios',
    'output\\templates\\Language'
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}
Write-Host "Directories created`n"

Write-Host "-------------------------------------------------"
Write-Host "STEP 3: Generating Excel templates"
Write-Host "-------------------------------------------------"
python .\scripts\generate_templates.py
Write-Host "Templates generated`n"

Write-Host "-------------------------------------------------"
Write-Host "STEP 4: Generating AG_Dev Reports -> output/reports/AG/"
Write-Host "-------------------------------------------------"
python .\run.py --report consolidated --database AG_Dev --format excel
python .\run.py --report bible-completion --database AG_Dev --format excel
python .\run.py --report obs-completion --database AG_Dev --format excel
python .\run.py --report literature-completion --database AG_Dev --format excel
python .\run.py --report grammar-completion --database AG_Dev --format excel
python .\run.py --report ag-drafting --database AG_Dev --format excel
python .\run.py --report user --database AG_Dev --format excel
python .\run.py --report worklog --database AG_Dev --format excel

Write-Host "-------------------------------------------------"
Write-Host "STEP 5: Generating LMS Reports -> output/reports/LMS/"
Write-Host "-------------------------------------------------"
python .\scripts\generate_lms_templates.py
python .\scripts\generate_lms_batch_reports.py
python .\run.py --report lms --database Telios_LMS_Dev --format excel

Write-Host "-------------------------------------------------"
Write-Host "STEP 6: Generating Language Survey Templates -> output/templates/Language/"
Write-Host "-------------------------------------------------"
python .\scripts\generate_cluster_template.py
python .\scripts\generate_dynamic_language_templates.py
python .\scripts\generate_language_uploader_template.py
python .\scripts\generate_dynamic_workbook.py

Write-Host "-------------------------------------------------"
Write-Host "GENERATION COMPLETE!"
Write-Host "-------------------------------------------------`n"

Write-Host "All tasks completed successfully!"
