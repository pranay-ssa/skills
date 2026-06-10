# Skill Update Pipeline

How to keep `augent-usecase-builder` in sync with the AuGENT framework.

## Architecture

```
                         ┌─────────────────────┐
                         │  ai_agents_core/     │
                         │  (framework source)  │
                         └──────────┬──────────┘
                                    │ changes
                                    ▼
                    ┌───────────────────────────────┐
                    │  scripts/detect_drift.py       │
                    │  Fingerprints API surface,     │
                    │  compares against skill refs   │
                    └───────────┬───────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Drift detected?      │
                    └───────────┬───────────┘
                     No         │        Yes
                     ▼          │         ▼
                  Done      ┌───┴──────────────────────┐
                            │ 1. Review drift report     │
                            │ 2. Update reference files  │
                            │ 3. Update stage guides     │
                            │ 4. Run validate_imports    │
                            │ 5. Run graphify update     │
                            └───────────────────────────┘
```

## Pipeline Stages

### Stage A: Detection (automatic)

Run drift detection before every skill use:

```bash
# From skill directory
python scripts/detect_drift.py

# JSON output (for CI/CD)
python scripts/detect_drift.py --json

# From project root, pointing at framework
python skill-create/augent-usecase-builder/scripts/detect_drift.py \
  --project-root ai_agents_core
```

**What it checks:**
- Public exports in `orchestration/__init__.py` vs expected set
- Public exports in `agents/__init__.py` vs expected set
- Public exports in `guardrails/__init__.py` vs expected set
- Public exports in `llm/__init__.py` vs expected set
- `LLMService.call()` parameter list vs expected list

**Exit codes:**
- `0` — no drift, skill is current
- `2` — drift detected, action needed
- `1` — error (framework not found)

### Stage B: Validation (automatic)

After detection passes:

```bash
python scripts/validate_imports.py
```

**What it checks:**
- Every import path in `references/import-map.md` exists in framework
- Every `KEY_APIS` symbol exists in expected file
- `LLMService.call()` has required parameters
- `AuGENTAgent` has `_execute()` and `run()` methods
- `SchemaRegistry` has `register()`, `register_schema()`, `get()` methods

### Stage C: Resolution (manual with tool assistance)

When drift is detected:

1. **Review the drift report** — understand what changed
2. **Read the changed framework files** to understand new APIs
3. **Update skill reference files:**
   - `references/framework-api.md` — add new APIs, remove deprecated
   - `references/import-map.md` — update import paths
   - `references/stages/*.md` — update examples if patterns changed
4. **Update expected sets in `detect_drift.py`:**
   - `EXPECTED_ORCHESTRATION`, `EXPECTED_AGENTS`, `EXPECTED_GUARDRAILS`, `EXPECTED_LLM`
   - `EXPECTED_LLM_PARAMS`
5. **Re-run validation** to confirm fixes
6. **Run graphify** to update knowledge graph:
   ```bash
   cd <project-root>
   graphify update .
   ```

### Stage D: Integration (CI/CD-ready)

For automated pipelines, add to CI:

```yaml
# .github/workflows/skill-check.yml (example)
name: Skill Sync Check
on:
  push:
    paths:
      - 'ai_agents_core/**'
  pull_request:
    paths:
      - 'ai_agents_core/**'

jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Detect framework drift
        run: |
          python skill-create/augent-usecase-builder/scripts/detect_drift.py --json
          # Exit code 2 = drift, fails the check
```

## Manual Triggers

The SKILL.md already includes pre-build drift checks. The user can also trigger manually:

| Trigger | Command |
|---------|---------|
| Check drift | `python scripts/detect_drift.py` |
| Validate imports | `python scripts/validate_imports.py` |
| Full health check | Both above, sequentially |
| Update references | `python scripts/detect_drift.py --update-refs` (partial) |

## Framework Change Categories

| Change Type | Impact on Skill | Action |
|------------|----------------|--------|
| New export added to `__init__.py` | Low — new feature | Add to import-map, document in framework-api |
| Export removed from `__init__.py` | High — breaking | Flag, update all stage guides |
| New parameter on `LLMService.call()` | Medium — optional | Add to reference, update Stage 3 |
| Removed parameter | High — breaking | Update all agent code examples |
| New exception class | Low | Add to import-map, document |
| Policy preset changed | Medium | Update Stage 4 examples |
| `AuGENTAgent` base class changed | High — breaking | Update Stage 3, all agent examples |

## File Ownership

```
augent-usecase-builder/
├── SKILL.md                    # Manual update on workflow changes
├── scripts/
│   ├── validate_imports.py     # Update KEY_APIS list when new APIs added
│   └── detect_drift.py         # Update EXPECTED_* sets after framework changes
├── references/
│   ├── framework-api.md        # Manual update — comprehensive docs
│   ├── import-map.md           # Semi-auto — validates against framework
│   └── stages/*.md             # Manual update — pattern guides
└── evals/
    └── evals.json              # Manual update — new test patterns
```
