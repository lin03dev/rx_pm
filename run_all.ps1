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

function Get-PythonVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$Arguments = @()
    )

    try {
        $version = & $Command @Arguments -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -eq 0) {
            return $version.Trim()
        }
    }
    catch {
        return $null
    }

    return $null
}

function Get-Python310Command {
    $candidates = @(
        @{ Display = 'py -3.10'; Command = 'py'; Arguments = @('-3.10') },
        @{ Display = 'python'; Command = 'python'; Arguments = @() },
        @{ Display = 'python3'; Command = 'python3'; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        $version = Get-PythonVersion -Command $candidate.Command -Arguments $candidate.Arguments
        if ($version -eq '3.10') {
            return $candidate
        }
    }

    throw @"
Python 3.10 was not found.

Install it with:
  py install 3.10

Or activate an existing Python 3.10 environment, then run:
  .\run_all.ps1
"@
}

function Test-LocalDatabases {
    Invoke-PythonStep @('.\scripts\check_databases.py')
}

Write-Host "==============================================="
Write-Host "  UNIFIED REPORTING SYSTEM - COMPLETE RUN"
Write-Host "===============================================`n"

$venvActivationPath = ".\venv\Scripts\Activate.ps1"

if (-not (Test-Path -Path $venvActivationPath)) {
    Write-Host "Creating virtual environment..."
    $python310 = Get-Python310Command
    Write-Host "Using Python 3.10 from $($python310.Display)"
    & $python310.Command @($python310.Arguments + @('-m', 'venv', 'venv'))
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment with $($python310.Display)"
    }
}

Write-Host "Activating virtual environment..."
if (-not (Test-Path -Path $venvActivationPath)) {
    throw "Virtual environment activation script was not found at $venvActivationPath"
}
. $venvActivationPath

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
