# Stage 2: State TypedDict and Pydantic Schemas

Defines the workflow state shape and output validation contracts.

## 2.1 Define the state TypedDict

In `usecases/<name>/ai_agents/graph.py`:

```python
from __future__ import annotations

from typing import Any
from ai_agents_core.orchestration import BaseWorkflowState


class <PascalCaseName>State(BaseWorkflowState, total=False):
    """<UseCase> workflow state."""
    # Input
    task: str

    # Add use-case-specific fields here
    # Use flat structure — no nested TypedDicts
    # Type as list[dict], dict[str, Any], str, int, float, bool

    # Example fields:
    # items: list[dict]
    # result_text: str
    # confidence: float
    # status: str
```

**Rules:**
- Class name: `<PascalCaseName>State` (e.g., `MarketInsightState`)
- Extends `BaseWorkflowState` with `total=False`
- All fields are optional (TypedDict default with `total=False`)
- No nested TypedDicts — use `dict` or `list[dict]` for complex structures
- Never redefine `workflow_id`, `cycle_state`, `errors`, etc. — they come from base

## 2.2 Define Pydantic output schemas

In `usecases/<name>/ai_agents/models.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Literal

from ai_agents_core.guardrails import SchemaRegistry


@SchemaRegistry.register_schema("<agent_name>")
class <AgentName>Output(BaseModel):
    """Output schema for <AgentName> agent."""
    # Define fields that the agent's _execute() returns
    # Every field is REQUIRED unless has a default

    status: str
    # ... use-case-specific fields
```

**Rules:**
- One output class per agent that produces structured output
- Use `@SchemaRegistry.register_schema("agent_name")` decorator — the string must
  exactly match the `agent_name` class attribute on the agent
- Field names use `snake_case`
- Use `Literal["val1", "val2"]` for constrained string fields
- Use `Field(default=...)` for optional fields
- Import `SchemaRegistry` from `ai_agents_core.guardrails`, not from sub-module

**Example — a complete `models.py`:**

```python
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Literal

from ai_agents_core.guardrails import SchemaRegistry


@SchemaRegistry.register_schema("insight_generator")
class InsightGeneratorOutput(BaseModel):
    insight_text: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    confidence: Literal["high", "medium", "low"]
    sources: list[dict[str, Any]] = Field(default_factory=list)
    status: str
```

## 2.3 Schema import side-effects

Agent files must import the output schemas to trigger the `@SchemaRegistry.register_schema`
decorator at module load time. The standard pattern:

```python
# In each agent file:
from usecases.<name>.ai_agents.models import <AgentName>Output  # noqa: F401
```

The `# noqa: F401` suppresses the "unused import" lint warning since the import
is for side effects only.

Alternatively, import all schemas in `ai_agents/__init__.py`:

```python
# ai_agents/__init__.py
from __future__ import annotations
from usecases.<name>.ai_agents.models import (  # noqa: F401
    Agent1Output,
    Agent2Output,
)
```

## Verification checklist

- [ ] State TypedDict extends `BaseWorkflowState` with `total=False`
- [ ] State has no nested TypedDicts (flat design)
- [ ] Each agent has a corresponding Pydantic output schema
- [ ] `@SchemaRegistry.register_schema("name")` uses exact `agent_name` string
- [ ] All imports use paths verified in `references/import-map.md`
- [ ] Schema files import from `ai_agents_core.guardrails`, not sub-modules
