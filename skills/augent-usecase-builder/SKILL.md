---
name: augent-usecase-builder
description: >
  Build production-ready AuGENT use cases from scratch. Use when the user wants to create
  a new AI use case on the AuGENT platform — including agents, graphs, schemas, APIs,
  and orchestration. Handles all platform integration so the caller never needs to know
  framework internals. Triggers on: "create use case", "new usecase", "build agent",
  "setup orchestration", "scaffold AuGENT", "add use case to platform", or any request
  to build AI agents/graphs/workflows within the AuGENT project.
---

# AuGENT Use Case Builder

Builds complete, platform-compatible AuGENT use cases. The caller describes what the
use case should do; this skill generates all the code with correct imports, conventions,
and integration points — as if written by the platform team.

## When to use this skill

Use this skill whenever the user wants to:
- Create a new use case from scratch
- Add agents to an existing use case
- Define a new LangGraph workflow on the platform
- Extend a use case with new nodes, schemas, or API endpoints
- Refactor a use case to match framework conventions

Do NOT use this skill for:
- Modifying the framework itself (`ai_agents_core/`)
- General Python questions unrelated to AuGENT

## Before you build — health check (MANDATORY)

Before generating any use-case code, verify the skill is in sync with the framework:

```bash
# From wherever the skill is installed:
python scripts/validate_imports.py --project-root <path-to-ai_agents_core>
python scripts/detect_drift.py --project-root <path-to-ai_agents_core>
```

If both pass, the skill matches the framework. If drift is detected, the framework
has changed — update the skill references before building. See `references/update-pipeline.md`.

**If you are developing the framework itself** (working inside the augent monorepo),
install the git hook so this runs automatically on every commit:

```bash
.\skill-check.ps1 --install
```

```powershell
.\skill-create\augent-usecase-builder\scripts\skill-check.ps1 --install
```

**The update pipeline** (automated + manual layers):

```
    GitHub Actions CI          Pre-commit hook            Manual
  ┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────────┐
  │ PR touches             │ │ git commit with        │ │ .\skill-check          │
  │ ai_agents_core/        │ │ framework changes      │ │ .ps1 --sync            │
  │            │           │ │            │           │ │            │           │
  │            ▼           │ │            ▼           │ │            ▼           │
  │ detect_drift.py        │ │ detect_drift.py        │ │ reports what drifted   │
  │ validate_imports.py    │ │ validate_imports.py    │ │ and what to fix        │
  │            │           │ │            │           │ │                        │
  │            ▼           │ │            ▼           │ │                        │
  │ pass = merge PR        │ │ pass = accept commit   │ │                        │
  │ fail = block PR        │ │ fail = block commit    │ │                        │
  └────────────────────────┘ └────────────────────────┘ └────────────────────────┘
```

## How this skill works

The skill is organized into **five build stages**. Each stage has a dedicated reference
guide under `references/stages/`. The SKILL.md you are reading now provides the
orchestration workflow — what to do, in what order, and which reference to consult.

```
augent-usecase-builder/
├── SKILL.md                          # <-- you are here (orchestration)
├── references/
│   ├── framework-api.md              # Complete framework reference
│   ├── import-map.md                 # Every import path verified against core
│   └── stages/
│       ├── stage-1-scaffold.md       # Directory structure + pyproject.toml
│       ├── stage-2-state-schemas.md  # State TypedDict + Pydantic models
│       ├── stage-3-agents.md         # AuGENTAgent subclasses + LLM calls
│       ├── stage-4-graph.md          # GraphBuilder + node wiring
│       └── stage-5-entrypoint.md     # main.py + Orchestrator wiring
└── evals/
    └── evals.json                    # Test cases for this skill
```

## The build sequence

Always follow the stages in order. Each stage produces files consumed by the next.

| Stage | What it produces | Key reference |
|-------|-----------------|---------------|
| 1. Scaffold | Directory tree, pyproject.toml, .env template | `references/stages/stage-1-scaffold.md` |
| 2. State + Schemas | `models.py` (Pydantic + SchemaRegistry), `graph.py` (TypedDict) | `references/stages/stage-2-state-schemas.md` |
| 3. Agents | Agent classes in `ai_agents/agents/` | `references/stages/stage-3-agents.md` |
| 4. Graph | `graph.py` complete with GraphBuilder wiring | `references/stages/stage-4-graph.md` |
| 5. Entry Point | `main.py`, `api/` if needed | `references/stages/stage-5-entrypoint.md` |

## Pre-build checklist (run before writing any file)

Before starting Stage 1, always do this:

1. **Read the framework API reference** — `references/framework-api.md` — to understand
   what the platform provides. Critical before designing any agent or graph.
2. **Read the import map** — `references/import-map.md` — so every import you write
   is verified against the actual framework. Never guess an import path.
3. **Identify the use case name** — confirm with the user. This determines the
   directory name (`usecases/<name>/`) and Python package name.
4. **Identify agents and their sequence** — list every agent/node the use case needs,
   whether it calls LLM or is deterministic, and how they connect.

## How to run each stage

For each stage, read the corresponding stage guide in `references/stages/`, then
produce the files. After completing each stage, verify:

1. All imports use paths from `references/import-map.md` (no guessed paths)
2. `workflow_id` propagates through every agent and LLM call
3. All agent classes extend `AuGENTAgent` with `agent_name` set
4. All output schemas are registered via `@SchemaRegistry.register_schema()`
5. Graph nodes are plain `async def (state: dict) -> dict` (no framework code needed
   inside agents — the platform wraps them)
6. Router functions are pure: no LLM, no I/O, no side effects

## Non-negotiable rules (applied at every stage)

These are platform invariants. Violating any of them means the use case will not
integrate:

### State and workflow
- State must extend `BaseWorkflowState` via TypedDict multiple inheritance
- Use `total=False` so all fields are optional
- `workflow_id` is always `state.get("workflow_id", "unknown")`
- Never modify `cycle_state` in agent code — it belongs to the Orchestrator

### Agents
- `agent_name` class attribute must match the name passed to `@SchemaRegistry.register_schema()`
- `_execute(self, state: dict) -> dict` — returns a partial state update dict
- LLM calls go through `LLMService.call()` — never call OpenAI/LangChain directly
- `api_key` and `workflow_id` are REQUIRED parameters on every `LLMService.call()`
- Model versions must be PINNED (e.g., `"2024-08-06"`) — no floating references

### Imports
- Use-case code imports from `ai_agents_core.orchestration` (public API), not from
  sub-modules directly
- `END` comes from `ai_agents_core.orchestration.graph_builder`, not from LangGraph
- `SchemaRegistry` comes from `ai_agents_core.guardrails.output`

### Directory structure
- Use-case code lives under `usecases/<name>/`, never under `ai_agents_core/`
- Agent classes go in `usecases/<name>/ai_agents/agents/`
- Non-LLM node functions go in `usecases/<name>/ai_agents/nodes/`
- Pydantic schemas and state TypedDict go at `usecases/<name>/ai_agents/models.py`
  and `usecases/<name>/ai_agents/graph.py`

### Configuration
- `pyproject.toml` must declare `ai_agents_core` as editable dependency via
  `[tool.uv.sources]` pointing to `../../ai_agents_core`
- API keys come from environment (`.env`), never hardcoded
- `setup_logging(usecase_name="...")` must be called before any framework import
  at the top of `main.py`

## Framework version awareness

This skill embeds knowledge of the AuGENT framework `v0.1.0` (current as of
2026-06-08). The reference files in `references/` are snapshots of the framework
API surface.

### Detecting drift

Before starting any build, verify the framework has not changed by checking:
- `ai_agents_core/orchestration/__init__.py` — any new exports?
- `ai_agents_core/llm/service.py` — `LLMService.call()` signature unchanged?
- `ai_agents_core/agents/base.py` — `AuGENTAgent.run()` and `_execute()` unchanged?
- `ai_agents_core/guardrails/output.py` — `SchemaRegistry` API unchanged?

If any of these have changed, flag it to the user and update the reference files
before proceeding. The import map (`references/import-map.md`) is your source of
truth for what currently exists.

### Updating the skill

After framework changes are detected and understood:
1. Update `references/framework-api.md` with new/changed APIs
2. Update `references/import-map.md` with correct import paths
3. Update the affected stage guides
4. Run `graphify update .` from the project root to update the knowledge graph

## Output format

When the environment supports file writes (agent context), create the actual files
under `usecases/<name>/` as described in each stage guide.

When the environment does NOT support file writes (chat-only context), output all
code inline in your response. Use markdown code blocks labeled with the file path:

```python
# usecases/<name>/ai_agents/agents/my_agent.py
class MyAgent(AuGENTAgent):
    ...
```

Never just say "I'll create the files" without providing the actual code. The user
must be able to copy-paste every file from your response.
