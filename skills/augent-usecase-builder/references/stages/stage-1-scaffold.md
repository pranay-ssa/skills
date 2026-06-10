# Stage 1: Scaffold

Creates the directory tree and configuration files for a new use case.

## 1.1 Confirm the use case name

Ask the user for the use case name. This becomes:
- Directory: `usecases/<name>/`
- Package: `usecases.<name>`
- Log file: `<name>_YYYY-MM-DD.log`
- Python package for agents: `usecases/<name>/ai_agents/`

Name must be `snake_case`, all lowercase, no special characters except underscore.

## 1.2 Create the directory structure

```
usecases/<name>/
├── __init__.py
├── pyproject.toml
├── ai_agents/
│   ├── __init__.py          # can be empty or minimal
│   ├── agents/
│   │   └── __init__.py
│   ├── nodes/
│   │   └── __init__.py
│   ├── .env                 # template, NOT committed
│   ├── .env.example         # committed template without secrets
│   ├── graph.py             # created in Stage 2/4
│   ├── models.py            # created in Stage 2
│   └── main.py              # created in Stage 5
├── tests/
│   ├── __init__.py
│   └── conftest.py
└── logs/                    # gitignored, created at runtime
```

## 1.3 Write `__init__.py` files

Minimal content:

```python
from __future__ import annotations
```

The `ai_agents/__init__.py` can be empty. Do NOT create a namespace package that
re-exports everything — keep it minimal.

## 1.4 Write `pyproject.toml`

```toml
[project]
name = "<usecase_name>"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = ["ai_agents_core"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["ai_agents"]

[tool.uv.sources]
ai_agents_core = { path = "../../ai_agents_core", editable = true }

[tool.uv]
dev-dependencies = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = [".."]
timeout = 30

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
```

Replace `<usecase_name>` with the actual name.

## 1.5 Write `.env.example`

```env
# LLM Provider
OPENROUTER_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Azure (for Content Safety, Cosmos DB, etc.)
AZURE_CONTENT_SAFETY_ENDPOINT=
AZURE_CONTENT_SAFETY_KEY=

# Langfuse (optional tracing)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=

# Framework config
GUARDRAILS_MAX_SYSTEM_LENGTH=15000
GUARDRAILS_MAX_USER_LENGTH=5000
```

The actual `.env` should be in `.gitignore` and never committed.

## 1.6 Run `uv sync`

After creating `pyproject.toml`, run:

```bash
uv sync
```

This creates `uv.lock` and the virtual environment.

## 1.7 Write `tests/conftest.py`

```python
from __future__ import annotations

import pytest
from typing import Any


@pytest.fixture
def make_state() -> dict[str, Any]:
    """Return a minimal BaseWorkflowState-compatible dict for tests."""
    return {
        "workflow_id": "test-wf-001",
        "cycle_state": "RUNNING",
        "retry_counts": {},
        "errors": [],
        "dead_letters": [],
        "items_processed": 0,
        "items_discarded": 0,
        "metadata": {},
        "task": "test task",
    }
```

## Verification checklist

- [ ] Directory structure matches the template above
- [ ] `pyproject.toml` has `ai_agents_core` as editable source
- [ ] `.env.example` exists with all required variables
- [ ] `.env` is in `.gitignore`
- [ ] `uv sync` runs without errors
- [ ] `conftest.py` provides a `make_state` fixture
