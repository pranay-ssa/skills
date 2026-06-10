# Stage 3: Agents

Builds agent classes (LLM agents) and node functions (deterministic nodes).

## 3.1 LLM Agent — the standard pattern

Every LLM-calling agent follows this exact pattern:

```python
from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field

from ai_agents_core.agents import AuGENTAgent
from ai_agents_core.llm import LLMService
from ai_agents_core.logging import get_logger

# Side-effect import for schema registration
from usecases.<name>.ai_agents.models import <AgentName>Output  # noqa: F401

logger = get_logger("usecase.<name>.<agent_name>")


class <AgentName>Agent(AuGENTAgent):
    agent_name = "<agent_name>"
    capability = "fast_general"  # or "reasoning" for complex tasks

    def __init__(self):
        super().__init__()
        self.llm_service = LLMService()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        # Or: os.getenv("OPENAI_API_KEY", "")

    async def _execute(self, state: dict) -> dict:
        workflow_id = state.get("workflow_id", "unknown")

        # 1. Build prompt from state
        system_prompt = """You are a ..."""
        user_prompt = self._build_user_prompt(state)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 2. Call LLM via platform service
        response = await self.llm_service.call(
            model="openai/gpt-4o",               # or "gpt-4o"
            model_version="2024-08-06",          # MUST be pinned
            messages=messages,
            max_tokens=2000,
            temperature=0.3,
            agent_name=self.agent_name,
            workflow_id=workflow_id,
            api_key=self.api_key,
            provider="openrouter",               # or "openai", "azure-openai"
        )

        # 3. Parse LLM response into dict
        output = self._parse_response(response.content)

        logger.info(
            "[%s] %s completed — confidence=%s items=%d",
            workflow_id, self.agent_name,
            output.get("confidence", "unknown"),
            output.get("items_processed", 0),
        )

        return output

    def _build_user_prompt(self, state: dict) -> str:
        """Build the user prompt from state fields."""
        # Extract relevant fields from state
        return f"Task: {state.get('task', '')}"

    def _parse_response(self, content: str) -> dict:
        """Parse LLM text response into a dict matching output schema."""
        # If response contains JSON, extract and parse it
        try:
            # Try to find JSON block
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "{" in content:
                json_str = content[content.index("{"):content.rindex("}") + 1]
            else:
                json_str = content
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            return {"status": "parse_failed", "raw_output": content}
```

## 3.2 Deterministic node — the standard pattern

Non-LLM nodes are plain async functions:

```python
from __future__ import annotations

from typing import Any


async def <node_name>(state: dict) -> dict:
    """
    Deterministic node: <description>.
    No LLM calls, no I/O side effects beyond reading state.
    """
    # Read from state
    task = state.get("task", "")
    items = state.get("items", [])

    # Pure computation
    result = ...  # your logic here

    # Return partial state update
    return {
        "<result_field>": result,
        "items_processed": len(items),
    }
```

**Rules for deterministic nodes:**
- Must be `async def (state: dict) -> dict`
- Read from state, compute, return partial update
- No LLM calls — use an agent class for that
- No I/O side effects (filesystem, network) — use tools for that
- Router functions follow the same pattern but return `str` instead of `dict`

## 3.3 Router function pattern

Used with `GraphBuilder.add_conditional_edge()`:

```python
def router_fn(state: dict) -> str:
    """
    Pure router: no LLM, no I/O, no side effects.
    Returns a key from the routing_map.
    """
    field = state.get("some_field", "default")
    if field == "case_a":
        return "node_a"
    elif field == "case_b":
        return "node_b"
    return "fallback_node"
```

## 3.4 Agent composition rules

- **One agent = one file** under `ai_agents/agents/`
- Agent file name: `snake_case.py` matching the class name (e.g., `insight_generator.py`
  contains `InsightGeneratorAgent`)
- Each agent file imports its output schema for side effects
- Agent `__init__` sets `self.llm_service = LLMService()` and reads API key from env
- Never hardcode API keys
- Always pass `workflow_id` to `LLMService.call()`

## 3.5 Handling LLM failures

The `AuGENTAgent.run()` method handles:
- Input guardrail failures (Layer 1) — raises `InputValidationError` before `_execute()`
- Output validation failures (Layer 2) — raises `SchemaValidationError` after `_execute()`
- Content safety failures (Layer 3) — handled by `LLMService.call()` internally

The `NodeExecutor` wrapping handles:
- Retry on transient failures (up to policy's `max_attempts`)
- Circuit breaker (trips after threshold failures)
- Timeout enforcement

Agents DO NOT need to implement retry logic themselves. The platform handles it.

## Verification checklist

- [ ] Each LLM agent extends `AuGENTAgent` with `agent_name` set
- [ ] `agent_name` matches the schema registration string exactly
- [ ] `_execute()` returns a `dict` (partial state update)
- [ ] `LLMService.call()` receives `api_key`, `workflow_id`, `model_version`
- [ ] Model versions are pinned (date string, not floating)
- [ ] No hardcoded API keys — all from environment
- [ ] Deterministic nodes are plain `async def` functions, no class needed
- [ ] Router functions are pure: no LLM, no I/O, no side effects
- [ ] Imports use paths from `references/import-map.md`
