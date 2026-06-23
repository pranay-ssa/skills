# Eval runner for the augent-architecture-viz skill (PowerShell)
#
# Usage:
#   .\evals\run.ps1                          # Run all prompts
#   .\evals\run.ps1 -Subset                  # Run critical prompts only
#   .\evals\run.ps1 -Id explicit-default     # Run a single prompt
#   .\evals\run.ps1 -SkipLLM                 # Skip LLM rubric grading
#
# Requires: opencode CLI, python >= 3.10, node >= 18

param(
  [switch]$Subset,
  [string]$Id = "",
  [switch]$SkipLLM,
  [string]$Cli = "opencode",
  [string]$MaxBudget = "2.00"
)

$ScriptDir = Split-Path -Parent $PSCommandPath
$SkillDir = Split-Path -Parent $ScriptDir
$PromptsCsv = Join-Path $ScriptDir "prompts.csv"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ResultsDir = Join-Path $ScriptDir "results" $Timestamp
$null = New-Item -ItemType Directory -Path $ResultsDir -Force

$SubsetIds = @("explicit-default", "explicit-framework", "explicit-bare", "negative-refactor", "edge-vague")

Write-Host "=== AuGENT Architecture Viz Skill Eval ===" -ForegroundColor Cyan
Write-Host "Timestamp:  $Timestamp"
Write-Host "CLI:        $Cli"
Write-Host "Results:    $ResultsDir"
Write-Host ""

# Check CLI availability
if (!(Get-Command $Cli -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: CLI '$Cli' not found" -ForegroundColor Red
  exit 1
}

# Parse prompts CSV
$prompts = Get-Content $PromptsCsv | Where-Object {
  $_ -notmatch '^\s*#' -and $_ -notmatch '^id,' -and $_.Trim() -ne ''
}

foreach ($line in $prompts) {
  $parts = $line -split ','
  $id = $parts[0].Trim()
  $expectTrigger = $parts[1].Trim()
  $expectedType = $parts[2].Trim()
  $prompt = ($line -replace "^$id,$expectTrigger,$expectedType,", "").Trim('"')

  # Filtering
  if ($Id -and $id -ne $Id) { continue }
  if ($Subset -and $SubsetIds -notcontains $id) { continue }

  Write-Host "--- [$id] ---" -ForegroundColor Yellow
  Write-Host "  Prompt:      $prompt"
  Write-Host "  Expect:      trigger=$expectTrigger type=$expectedType"

  $PromptDir = Join-Path $ResultsDir $id
  $null = New-Item -ItemType Directory -Path $PromptDir -Force

  # Create temp working directory
  $WorkDir = Join-Path $env:TEMP "viz-eval-$([System.IO.Path]::GetRandomFileName())"
  $null = New-Item -ItemType Directory -Path $WorkDir -Force

  # Install skill files
  $null = New-Item -ItemType Directory -Path "$WorkDir\.claude\skills\augent-architecture-viz" -Force
  Copy-Item "$SkillDir\*" "$WorkDir\.claude\skills\augent-architecture-viz\" -Recurse -Force
  $null = New-Item -ItemType Directory -Path "$WorkDir\.config\opencode\skills\augent-architecture-viz" -Force
  Copy-Item "$SkillDir\*" "$WorkDir\.config\opencode\skills\augent-architecture-viz\" -Recurse -Force

  # Create project context
@"
# AuGENT Platform Project
This is the AuGENT Enterprise AI Platform project.
usecases/usecase2/ has: event_detector, trigger_classifier, novelty_classifier, orch_router
ai_agents_core/ has: Orchestration, Agents, Guardrails, LLM Service, Observability
"@ | Out-File -FilePath "$WorkDir\AGENTS.md" -Encoding UTF8

  $StartMarker = "$WorkDir\.eval-start-marker"
  $null > $StartMarker

  Write-Host "  Running $Cli ..."
  Push-Location $WorkDir
  try {
    if ($Cli -eq "opencode") {
      # opencode CLI headless mode ($prompt) | opencode --stdin --headless
      $prompt | & $Cli --stdin --headless 2>"$PromptDir\stderr.log" | Out-File "$PromptDir\output.txt"
    } else {
      # claude CLI
      $prompt | & $Cli -p $prompt --output-format json --dangerously-skip-permissions --max-budget-usd $MaxBudget --no-session-persistence 2>"$PromptDir\stderr.log" | Out-File "$PromptDir\output.json"
    }
  }
  finally {
    Pop-Location
  }

  # Check for generated HTML files
  $htmlFiles = Get-ChildItem -Path $WorkDir -Recurse -Filter "*.html" | Where-Object { $_.LastWriteTime -gt (Get-Item $StartMarker).LastWriteTime }
  $generatedHtml = $htmlFiles.Count -gt 0

  if ($generatedHtml) {
    foreach ($htmlFile in $htmlFiles) {
      Copy-Item $htmlFile.FullName "$PromptDir\"
    }

    # Run deterministic grader
    $latestHtml = Get-ChildItem -Path $PromptDir -Filter "*.html" | Where-Object { $_.Name -notlike "seed-*" } | Select-Object -First 1
    if ($latestHtml) {
      Write-Host "  Running deterministic grader ..."
      $detResult = python "$SkillDir\scripts\grade_viz.py" $latestHtml.FullName 2>&1
      $detResult | Out-File "$PromptDir\deterministic.json"
      try {
        $detObj = $detResult | ConvertFrom-Json
        Write-Host "    Passed: $($detObj.passed) / $($detObj.total)"
      } catch {}
    }

    # Run LLM rubric grader (if not skipped)
    if (-not $SkipLLM -and (Get-Command node -ErrorAction SilentlyContinue)) {
      Write-Host "  Running LLM rubric grader ..."
      node "$ScriptDir\graders\llm-rubric.mjs" $latestHtml.FullName "$PromptDir\llm-grade.json" 2>$null
    }
  }

  # Handle negative case
  if ($expectTrigger -eq "false") {
    if ($generatedHtml) {
      Write-Host "  FAIL: Negative case should NOT have triggered but produced HTML" -ForegroundColor Red
      @'{"expect_trigger": false, "triggered": true, "passed": false}'@ | Out-File "$PromptDir\deterministic.json"
    } else {
      Write-Host "  PASS: Negative case correctly did not trigger" -ForegroundColor Green
      @'{"expect_trigger": false, "triggered": false, "passed": true}'@ | Out-File "$PromptDir\deterministic.json"
    }
  }

  # Handle positive case that should have triggered
  if ($expectTrigger -eq "true" -and -not $generatedHtml) {
    Write-Host "  FAIL: Positive case should have triggered but no HTML generated" -ForegroundColor Red
  }

  # Cleanup
  Remove-Item -Path $WorkDir -Recurse -Force -ErrorAction SilentlyContinue

  Write-Host "  Done."
  Write-Host ""
}

# Generate summary report
Write-Host "=== Generating Report ===" -ForegroundColor Cyan
if (Get-Command node -ErrorAction SilentlyContinue) {
  node "$ScriptDir\report.mjs" $ResultsDir 2>$null
} else {
  Write-Host "  Skipping report (node not found). Results in: $ResultsDir"
}

Write-Host ""
Write-Host "Results saved to: $ResultsDir" -ForegroundColor Green
