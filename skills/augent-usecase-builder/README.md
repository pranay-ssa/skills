# AuGENT Use Case Builder

Installable skill for building production-ready use cases on the AuGENT Enterprise AI Platform.

## Install

```bash
npx skills add https://github.com/pranay-ssa/skills --skill augent-usecase-builder
```

## What it does

This skill generates complete, platform-compatible AuGENT use cases from a description.
It knows every framework API, import path, convention, and integration point — so you
don't need to.

## Prerequisites

- AuGENT framework repo cloned locally (`ai_agents_core/`)
- Python 3.12+, `uv` package manager
- The framework must be at a known path — pass it to validation scripts:

```bash
python scripts/validate_imports.py --project-root /path/to/ai_agents_core
python scripts/detect_drift.py --project-root /path/to/ai_agents_core
```

## Health check before building

Always verify the skill is in sync with your framework version:

```bash
python scripts/detect_drift.py --project-root <path-to-ai_agents_core>
python scripts/validate_imports.py --project-root <path-to-ai_agents_core>
```

If drift is detected, the framework has changed since this skill was published.
Check the [augent-skills releases](https://github.com/nagaraju-ssa/augent-skills/releases)
for an updated version, or update the references manually.

## Versioning

This skill tracks the AuGENT framework version it was built against.
Check the `framework-api.md` reference for the version stamp.

| Skill version | Framework version |
|--------------|-------------------|
| current      | v0.1.0 (2026-06-08) |

## Structure

```
augent-usecase-builder/
├── SKILL.md                       # Main orchestrator (122 lines)
├── references/
│   ├── framework-api.md           # Full platform API reference
│   ├── import-map.md              # 86 verified import paths
│   ├── update-pipeline.md         # How drift detection works
│   └── stages/                    # 5 build stage guides
├── scripts/
│   ├── detect_drift.py            # Fingerprint framework vs expected
│   ├── validate_imports.py        # Verify all imports exist
│   └── skill-check.ps1            # One-command health check
└── evals/
    └── evals.json                 # 5 test cases
```

## Relationship to framework repo

This skill is developed alongside the AuGENT framework, where automated drift detection
keeps it in sync. This repo (`pranay-ssa/skills`, branch `augent-skills`) is the
**distribution mirror** — updated when the framework changes.
