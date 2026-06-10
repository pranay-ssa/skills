#!/usr/bin/env pwsh
<#
.SYNOPSIS
  One-command skill health check + sync. Run from project root.

.DESCRIPTION
  Usage:
    .\skill-create\augent-usecase-builder\scripts\skill-check.ps1           # check only
    .\skill-create\augent-usecase-builder\scripts\skill-check.ps1 --install # install git hooks
    .\skill-create\augent-usecase-builder\scripts\skill-check.ps1 --sync    # report drift for manual fix
#>

param(
    [switch]$Install,
    [switch]$Sync
)

$ErrorActionPreference = "Continue"
$SKILL = "$PSScriptRoot\.."
$CORE  = "$PSScriptRoot\..\..\..\ai_agents_core"

function Write-Banner($text) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

# ---- Install mode ----
if ($Install) {
    Write-Banner "Installing git hooks"
    git config core.hooksPath .githooks
    Write-Host "Hooks installed. Pre-commit will now auto-check for framework drift." -ForegroundColor Green
    Write-Host "Hooks directory: $(git rev-parse --show-toplevel)\.githooks" -ForegroundColor Gray
    exit 0
}

# ---- Sync (report) mode ----
if ($Sync) {
    Write-Banner "Detecting framework drift"
    & python "$SKILL\scripts\detect_drift.py" --project-root "$CORE"
    $exit = $LASTEXITCODE
    if ($exit -eq 2) {
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Read the changed framework files"
        Write-Host "  2. Update: references/framework-api.md"
        Write-Host "  3. Update: references/import-map.md"
        Write-Host "  4. Update: scripts/detect_drift.py (EXPECTED_* sets)"
        Write-Host "  5. Re-run: .\skill-check.ps1 --check"
    }
    exit $exit
}

# ---- Default: full health check ----
Write-Banner "Skill Health Check"

Write-Host "[1/3] Drift detection" -ForegroundColor Gray
& python "$SKILL\scripts\detect_drift.py" --project-root "$CORE"
$driftOk = ($LASTEXITCODE -eq 0)

Write-Host "[2/3] Import validation" -ForegroundColor Gray
& python "$SKILL\scripts\validate_imports.py" --project-root "$CORE"
$importsOk = ($LASTEXITCODE -eq 0)

Write-Host "[3/3] Hook status" -ForegroundColor Gray
$hooksPath = git config core.hooksPath
if ($hooksPath) {
    Write-Host "  ACTIVE: hooks path = $hooksPath" -ForegroundColor Green
} else {
    Write-Host "  INACTIVE: no hooks configured. Run: .\skill-check.ps1 --install" -ForegroundColor Yellow
}

# Summary
Write-Host ""
if ($driftOk -and $importsOk) {
    Write-Host "HEALTH: PASS" -ForegroundColor Green
    Write-Host "  Framework matches skill references. Import map valid." -ForegroundColor Green
    Write-Host "  Ready to use the augent-usecase-builder skill." -ForegroundColor Green
    exit 0
} else {
    Write-Host "HEALTH: FAIL" -ForegroundColor Red
    if (-not $driftOk) { Write-Host "  Framework API has drifted from skill references." -ForegroundColor Red }
    if (-not $importsOk) { Write-Host "  Import map has stale paths." -ForegroundColor Red }
    Write-Host "  Run: .\skill-check.ps1 --sync for details." -ForegroundColor Yellow
    exit 1
}
