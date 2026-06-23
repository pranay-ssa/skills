#!/usr/bin/env bash
# Eval runner for the augent-architecture-viz skill.
#
# Usage:
#   bash evals/run.sh                    # Run all prompts
#   bash evals/run.sh --subset           # Run critical prompts only (faster)
#   bash evals/run.sh --id explicit-01   # Run a single prompt
#   bash evals/run.sh --cli claude       # Use specific CLI (opencode or claude)
#   bash evals/run.sh --skip-llm         # Skip LLM rubric grading
#
# Requires: opencode or claude CLI, python >= 3.10, node >= 18

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMPTS_CSV="$SCRIPT_DIR/prompts.csv"
RESULTS_BASE="$SCRIPT_DIR/results"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="$RESULTS_BASE/$TIMESTAMP"

# CLI flags
SUBSET=false
SINGLE_ID=""
SKIP_LLM=false
CLI="${EVAL_CLI:-opencode}"
MAX_BUDGET="${EVAL_MAX_BUDGET:-2.00}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --subset) SUBSET=true; shift ;;
    --id) SINGLE_ID="$2"; shift 2 ;;
    --skip-llm) SKIP_LLM=true; shift ;;
    --cli) CLI="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

SUBSET_IDS="explicit-default explicit-framework explicit-bare negative-refactor edge-vague"

mkdir -p "$RESULTS_DIR"
ln -sfn "$TIMESTAMP" "$RESULTS_BASE/latest" 2>/dev/null || true

echo "=== AuGENT Architecture Viz Skill Eval ==="
echo "Timestamp:  $TIMESTAMP"
echo "CLI:        $CLI"
echo "Results:    $RESULTS_DIR"
echo ""

# Verify CLI availability
if ! command -v "$CLI" &>/dev/null; then
  echo "Error: CLI '$CLI' not found. Install it or use --cli to specify another."
  exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

# Parse CSV: skip comment lines (#) and header
while IFS=, read -r id expect_trigger expected_type prompt; do
  # Skip comments and header
  [[ "$id" =~ ^#.*$ ]] && continue
  [[ "$id" == "id" ]] && continue
  [[ -z "$id" ]] && continue

  # Strip surrounding quotes from prompt
  prompt="${prompt%\"}"
  prompt="${prompt#\"}"

  # Filter by --subset or --id
  if [[ -n "$SINGLE_ID" && "$id" != "$SINGLE_ID" ]]; then
    continue
  fi
  if [[ "$SUBSET" == "true" ]]; then
    if ! echo "$SUBSET_IDS" | grep -qw "$id"; then
      continue
    fi
  fi

  echo "--- [$id] ---"
  echo "  Prompt:      $prompt"
  echo "  Expect:      trigger=$expect_trigger type=$expected_type"

  PROMPT_DIR="$RESULTS_DIR/$id"
  mkdir -p "$PROMPT_DIR"

  # Create temp working directory with skill installed
  WORK_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'viz-eval-XXXX')

  # Copy skill files and install where the agent can find them
  mkdir -p "$WORK_DIR/.claude/skills"
  cp -R "$SKILL_DIR" "$WORK_DIR/.claude/skills/augent-architecture-viz"
  # Also install for opencode
  mkdir -p "$WORK_DIR/.config/opencode/skills"
  cp -R "$SKILL_DIR" "$WORK_DIR/.config/opencode/skills/augent-architecture-viz"

  # Create a simple project context so the agent knows it's in AuGENT
  cat > "$WORK_DIR/AGENTS.md" << 'AGENTS'
# AuGENT Platform Project

This is the AuGENT Enterprise AI Platform project.

```
usecases/usecase2/    -- Default use case with event_detector, trigger_classifier,
                         novelty_classifier, orch_router (branches to development
                         and confirmation paths), context_collector, analyser,
                         portfolio_mapper, summary_agent, distributor
ai_agents_core/       -- Framework: Orchestration, Agents, Guardrails, LLM Service,
                         Observability
```
AGENTS

  # Create a marker file to detect newly created files
  touch "$WORK_DIR/.eval-start-marker"

  # Run the CLI with the prompt
  echo "  Running $CLI ..."

  if [[ "$CLI" == "opencode" ]]; then
    # opencode CLI expects different flags
    (cd "$WORK_DIR" && echo "$prompt" | "$CLI" --stdin \
      --model "kimi-k2.5:cloud" \
      --headless \
      < /dev/null \
      > "$PROMPT_DIR/output.txt" 2>"$PROMPT_DIR/stderr.log") || true
  else
    # claude CLI
    (cd "$WORK_DIR" && echo "$prompt" | "$CLI" -p "$prompt" \
      --output-format json \
      --dangerously-skip-permissions \
      --max-budget-usd "$MAX_BUDGET" \
      --no-session-persistence \
      < /dev/null \
      > "$PROMPT_DIR/output.json" 2>"$PROMPT_DIR/stderr.log") || true
  fi

  # Check if any HTML was generated
  HTML_FILES=$(find "$WORK_DIR" -maxdepth 3 -name "*.html" -newer "$WORK_DIR/.eval-start-marker" 2>/dev/null || true)
  GENERATED_HTML=false

  if [[ -n "$HTML_FILES" ]]; then
    GENERATED_HTML=true
    echo "$HTML_FILES" | while read -r html_file; do
      cp "$html_file" "$PROMPT_DIR/"
      echo "  Found HTML: $html_file"
    done

    # Run deterministic grader (grade_viz.py)
    LATEST_HTML=$(find "$PROMPT_DIR" -name "*.html" -not -name "seed-*" | head -1)
    if [[ -n "$LATEST_HTML" ]]; then
      echo "  Running deterministic grader ..."
      python "$SKILL_DIR/scripts/grade_viz.py" "$LATEST_HTML" > "$PROMPT_DIR/deterministic.json" 2>&1 || true
      DET_RESULT=$(cat "$PROMPT_DIR/deterministic.json")
      echo "    Passed: $(echo "$DET_RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('passed',0))" 2>/dev/null || echo '?') / $(echo "$DET_RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null || echo '?')"
    fi

    # Run LLM rubric grader (if not skipped)
    if [[ "$SKIP_LLM" != "true" ]]; then
      if command -v node &>/dev/null; then
        echo "  Running LLM rubric grader ..."
        node "$SCRIPT_DIR/graders/llm-rubric.mjs" "$LATEST_HTML" "$PROMPT_DIR/llm-grade.json" > /dev/null 2>&1 || true
      else
        echo "  Skipping LLM grader (node not found)"
      fi
    fi
  else
    echo "  No HTML files generated."
  fi

  # Handle negative case: should NOT trigger
  if [[ "$expect_trigger" == "false" ]]; then
    if [[ "$GENERATED_HTML" == "true" ]]; then
      echo "  FAIL: Negative case should NOT have triggered but produced HTML"
      echo '{"expect_trigger": false, "triggered": true, "passed": false}' > "$PROMPT_DIR/deterministic.json"
    else
      echo "  PASS: Negative case correctly did not trigger"
      echo '{"expect_trigger": false, "triggered": false, "passed": true}' > "$PROMPT_DIR/deterministic.json"
    fi
  fi

  # Handle positive case: should have triggered
  if [[ "$expect_trigger" == "true" && "$GENERATED_HTML" == "false" ]]; then
    echo "  FAIL: Positive case should have triggered but no HTML generated"
  fi

  # Cleanup
  rm -rf "$WORK_DIR"

  echo "  Done."
  echo ""
done < "$PROMPTS_CSV"

# Generate summary report
echo "=== Generating Report ==="
if command -v node &>/dev/null; then
  node "$SCRIPT_DIR/report.mjs" "$RESULTS_DIR" || true
else
  echo "  Skipping report (node not found). Results in: $RESULTS_DIR"
fi

echo ""
echo "Results saved to: $RESULTS_DIR"
