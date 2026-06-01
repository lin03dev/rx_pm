<#
.SYNOPSIS
    Run the full rx_pm generation pipeline on Windows.
#>

Set-StrictMode -Version Latest

$ErrorActionPreference = 'Stop'

function Invoke-PythonStep {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: python $($Arguments -join ' ')"
    }
}

function Test-LocalDatabases {
    Invoke-PythonStep @('.\scripts\check_databases.py')
}

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
Invoke-PythonStep @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-PythonStep @('-m', 'pip', 'install', '-r', 'requirements.txt')
Write-Host "Dependencies installed`n"

Write-Host "-------------------------------------------------"
Write-Host "STEP 1: Checking local PostgreSQL databases"
Write-Host "-------------------------------------------------"
Test-LocalDatabases
Write-Host "Database preflight complete`n"

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
Invoke-PythonStep @('.\scripts\generate_templates.py')
Write-Host "Templates generated`n"

Write-Host "-------------------------------------------------"
Write-Host "STEP 4: Generating AG_Dev Reports -> output/reports/AG/"
Write-Host "-------------------------------------------------"
Invoke-PythonStep @('.\run.py', '--report', 'consolidated', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'bible-completion', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'obs-completion', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'literature-completion', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'grammar-completion', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'ag-drafting', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'user', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'individual', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'worklog', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'user-activity', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'user-assignments', '--database', 'AG_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'literature-genre', '--database', 'AG_Dev', '--format', 'excel')

Write-Host "-------------------------------------------------"
Write-Host "STEP 5: Generating LMS Reports -> output/reports/LMS/"
Write-Host "-------------------------------------------------"
Invoke-PythonStep @('.\scripts\generate_lms_templates.py')
Invoke-PythonStep @('.\scripts\generate_lms_batch_reports.py')
Invoke-PythonStep @('.\run.py', '--report', 'lms', '--database', 'Telios_LMS_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'lms-comprehensive', '--database', 'Telios_LMS_Dev', '--format', 'excel')

Write-Host "-------------------------------------------------"
Write-Host "STEP 6: Generating Telios GeoJSON Reports -> output/reports/LMS/"
Write-Host "-------------------------------------------------"
Invoke-PythonStep @('.\run.py', '--report', 'telios-geojson', '--database', 'Telios_LMS_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'telios-geojson-data', '--database', 'Telios_LMS_Dev', '--format', 'excel')

Write-Host "-------------------------------------------------"
Write-Host "STEP 7: Generating Language Survey Reports and Templates"
Write-Host "-------------------------------------------------"
Invoke-PythonStep @('.\run.py', '--report', 'language-survey', '--database', 'Telios_LMS_Dev', '--format', 'excel')
Invoke-PythonStep @('.\run.py', '--report', 'language-dashboard', '--database', 'Telios_LMS_Dev', '--format', 'excel')
Invoke-PythonStep @('.\scripts\generate_cluster_template.py')
Invoke-PythonStep @('.\scripts\generate_dynamic_language_templates.py')
Invoke-PythonStep @('.\scripts\generate_language_uploader_template.py')
Invoke-PythonStep @('.\scripts\generate_dynamic_workbook.py')

Write-Host "-------------------------------------------------"
Write-Host "GENERATION COMPLETE!"
Write-Host "-------------------------------------------------`n"

Write-Host "All tasks completed successfully!"
