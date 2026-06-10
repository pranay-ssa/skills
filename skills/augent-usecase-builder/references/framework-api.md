# Framework API Reference — AuGENT v0.1.0

> Snapshot of the `ai_agents_core` public API surface as of 2026-06-08.
> Read this before designing any use case. It describes what the platform provides
> so you never reinvent or bypass framework abstractions.

---

## Table of Contents

1. [Orchestration Engine](#orchestration-engine)
2. [Agent Base Class](#agent-base-class)
3. [LLM Service](#llm-service)
4. [Guardrails System](#guardrails-system)
5. [Observability](#observability)
6. [Logging](#logging)
7. [Policies (Retry, Timeout, CircuitBreaker)](#policies)
8. [State and Enums](#state-and-enums)
9. [Tools](#tools)
10. [Database (DAL)](#database-dal)
11. [Config](#config)

---

## Orchestration Engine

### GraphBuilder (`ai_agents_core.orchestration.graph_builder`)

Fluent builder for LangGraph StateGraphs. Every node is transparently wrapped in
`NodeExecutor` — agents remain plain async functions.

```python
from ai_agents_core.orchestration import GraphBuilder, END

graph = (
    GraphBuilder(MyUseCaseState)
    .add_node("fetch",   fetch_fn,   policy=BATCH_POLICY)
    .add_node("process", process_fn, policy=CONSERVATIVE_POLICY)
    .set_entry("fetch")
    .add_edge("fetch", "process")
    .add_edge("process", END)
    .compile()
)
```

**Methods:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `add_node` | `(name: str, fn: Callable, policy?: NodePolicy) -> self` | `fn` must be `async (state: dict) -> dict`. Raises `GraphBuildError` on duplicate name. |
| `set_entry` | `(node: str) -> self` | Must be a registered node name. |
| `add_edge` | `(from: str, to: str \| END) -> self` | Deterministic edge. `to` can be `END`. |
| `add_bidirectional_edge` | `(from: str, to: str) -> self` | Two-way edge. |
| `add_conditional_edge` | `(from: str, router_fn: Callable, routing_map: dict) -> self` | `router_fn(state) -> str` must be pure (no LLM, no I/O). Returns key from `routing_map` → next node. |
| `compile` | `(checkpointer?: Any) -> compiled_graph` | Returns runnable LangGraph graph. |
| `set_middleware` | `(chain: MiddlewareChain) -> self` | Must be called before `add_node` for those nodes. |

### Orchestrator (`ai_agents_core.orchestration.orchestrator`)

Generic, use-case-agnostic workflow execution engine.

```python
from ai_agents_core.orchestration import Orchestrator

orchestrator = Orchestrator(
    graph=compiled_graph,
    checkpointer=None,           # optional PostgresSaver
    event_bus=None,              # optional EventBus
    workflow_timeout_s=3600,     # optional hard timeout
)
result = await orchestrator.run(initial_input={"my_field": "value"})
print(result["cycle_state"])   # SUCCESSFUL / DEGRADED / FAILED
```

**Key behavior:**
- Generates UUID4 `workflow_id` if not provided
- Merges `initial_input` into `BaseWorkflowState` defaults
- Wraps execution in `CycleGuard` (process-level lock, one workflow at a time)
- Emits lifecycle events: `WORKFLOW_STARTED`, `WORKFLOW_COMPLETED`/`WORKFLOW_FAILED`, `CYCLE_SKIPPED`
- Classifies final `cycle_state` via `classify_cycle()`
- Supports resume via `orchestrator.resume(workflow_id)` if checkpointer configured

### EventBus (`ai_agents_core.orchestration.event_bus`)

Decoupled pub/sub for orchestration lifecycle events.

```python
from ai_agents_core.orchestration import EventBus, EventType, WorkflowEvent

bus = EventBus()
await bus.subscribe(EventType.WORKFLOW_COMPLETED, my_handler)
# Handler: async def my_handler(event: WorkflowEvent) -> None
```

**Event types:** `WORKFLOW_STARTED`, `WORKFLOW_COMPLETED`, `WORKFLOW_FAILED`, `CYCLE_SKIPPED`,
`AGENT_STARTED`, `AGENT_COMPLETED`, `AGENT_FAILED`, `RETRY_ATTEMPTED`,
`CONTENT_SAFETY_BLOCK`, `LLM_STARTED`, `LLM_COMPLETED`, `LLM_FAILED`

---

## Agent Base Class

### AuGENTAgent (`ai_agents_core.agents.base`)

Abstract base for all agents. Subclasses implement `_execute()`. The base class
automatically enforces 3-layer guardrails.

```python
from ai_agents_core.agents import AuGENTAgent

class MyAgent(AuGENTAgent):
    agent_name = "my_agent"       # Must match SchemaRegistry name
    capability = "fast_general"

    def __init__(self):
        super().__init__()        # Sets up InputGuardrail + OutputValidator

    async def _execute(self, state: dict) -> dict:
        # Domain logic here
        return {"result": "done"}
```

**Execution flow (in `AuGENTAgent.run()`):**
1. **Layer 1 (Input Guardrail):** Extracts messages from state, runs `InputGuardrail.sanitise()`
2. **Core execution:** Calls `_execute(state)` — your code
3. **Layer 2 (Output Validation):** Calls `OutputValidator.validate()` against registered schema
4. **Logging:** Logs agent execution with duration and success/failure

**Key constraints:**
- `agent_name` must match the name in `@SchemaRegistry.register_schema()`
- `_execute()` returns a dict (partial state update) — never mutates state in place
- If `state` has `"messages"` key, those messages are sanitised before reaching `_execute()`
- If `state` has `"task"` but no `"messages"`, a user-role message is auto-created

### AgentRegistry (`ai_agents_core.agents.registry`)

Central registry for agent lookup by name and capability.

---

## LLM Service

### LLMService (`ai_agents_core.llm.service`)

Platform-standard entry point for all LLM interactions. Enforces model pinning.

```python
from ai_agents_core.llm import LLMService

llm = LLMService()
response = await llm.call(
    model="gpt-4o",
    model_version="2024-08-06",       # PINNED — required (Rule 7)
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=1000,
    temperature=0.2,
    agent_name="my_agent",
    workflow_id="uuid-here",
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="openai",                 # "openai", "azure-openai", "openrouter"
    langfuse=None,                     # optional Langfuse instance
)
# response.content  -> str
# response.metadata -> dict (includes usage, latency, etc.)
```

**What LLMService.call() does internally:**
1. Validates `model_version` is provided (raises `ValueError` if missing)
2. For OpenRouter: validates model name includes date suffix (e.g., `-2024-08-06`)
3. Applies Layer 1 (InputGuardrail) — sanitises messages before LLM
4. Constructs `LLMRequest`, sets API key, emits `LLM_STARTED` event
5. Calls provider via `registry.get(provider).generate(request)`
6. Emits `LLM_COMPLETED` or `LLM_FAILED` events
7. Applies Layer 3 (ContentSafety) on output
8. Logs token usage

**Provider support:**
- `"openai"` — OpenAI API
- `"azure-openai"` — Azure OpenAI (Entra ID / Managed Identity)
- `"openrouter"` — OpenRouter (model name must include version date)

**Response type:** `LLMResponse` — a Pydantic model with:
- `content: str` — the LLM output text
- `provider: str` — which provider was used
- `model: str` — full model identifier
- `metadata: dict` — includes `usage` (prompt_tokens, completion_tokens)

### LLMRequest / LLMResponse (`ai_agents_core.llm.schemas`)

Data models for LLM interactions.

```python
from ai_agents_core.llm import LLMMessage, LLMRequest, LLMResponse
```

---

## Guardrails System

Three strictly segregated layers protect every agent call.

### Layer 1: InputGuardrail (`ai_agents_core.guardrails.input`)

Sanitises inputs before LLM. Enforces role separation.

```python
from ai_agents_core.guardrails import InputGuardrail

guard = InputGuardrail()
sanitised = guard.sanitise(messages, workflow_id, agent_name)
# Returns list[SanitisedMessage]
# Raises InputValidationError on injection detection
```

**What it does:**
1. **Role enforcement:** Only `system`, `user`, `context` allowed. Unknown roles → coerced to `context`.
2. **Injection detection:** Scans user/context content for known patterns. Raises `InputValidationError`.
3. **Length truncation:** System max 15000, user max 5000, context max 20000 chars (configurable via env).
4. **Control character stripping:** Null bytes, unprintable chars removed.
5. **HTML entity decoding:** `&amp;` → `&`, etc.

### Layer 2: SchemaRegistry + OutputValidator (`ai_agents_core.guardrails.output`)

Validates agent output against registered Pydantic schemas.

```python
from ai_agents_core.guardrails import SchemaRegistry, OutputValidator
from pydantic import BaseModel

@SchemaRegistry.register_schema("my_agent")
class MyAgentOutput(BaseModel):
    result: str
    confidence: float
```

**SchemaRegistry API:**
- `SchemaRegistry.register(agent_name, schema_cls)` — register a schema
- `SchemaRegistry.register_schema("name")` — class decorator
- `SchemaRegistry.get(agent_name) -> type[BaseModel] | None`
- `SchemaRegistry.clear()` — reset (testing only)

**OutputValidator:**
- `validate(agent_name, output: dict, workflow_id) -> ValidationResult`
- Raises `SchemaValidationError` if validation fails or agent not registered

### Layer 3: ContentSafetyClient (`ai_agents_core.guardrails.content_safety`)

Azure Content Safety API integration. All AI-generated text must pass before storage.

```python
from ai_agents_core.guardrails import ContentSafetyClient

client = ContentSafetyClient()
result = await client.check(text, agent_name, workflow_id)
# result.passed -> bool
# Raises ContentSafetyError, ContentSafetyUnavailableError on failure
```

### Guardrail Exceptions

All guardrail exceptions inherit from `GuardrailsError`:
- `InputValidationError` — Layer 1 failure (prompt injection)
- `SchemaValidationError` — Layer 2 failure (output doesn't match schema)
- `ContentSafetyError` — Layer 3 failure (content blocked)
- `ContentSafetyUnavailableError` — Content Safety API unreachable

---

## Observability

### Langfuse Integration (`ai_agents_core.observability`)

The platform provides tracing via Langfuse. Use cases should not call Langfuse directly.

```python
from ai_agents_core.observability.adapters import EventBusAdapter
```

EventBusAdapter bridges orchestration events to Langfuse traces automatically.

### Correlation Context (`ai_agents_core.observability.context`)

```python
from ai_agents_core.observability.context import set_correlation_id, get_correlation_id
```

### Metrics (`ai_agents_core.observability.metrics`)

```python
from ai_agents_core.observability.metrics import MetricsCollector, WorkflowMetrics
```

---

## Logging

### Setup and Usage (`ai_agents_core.logging`)

```python
from ai_agents_core.logging import setup_logging, get_logger

# Call ONCE at top of main.py, before any framework imports
setup_logging(usecase_name="my_usecase")

# Get logger anywhere
logger = get_logger("usecase.my_usecase.agent_name")
logger.info("message", extra={"workflow_id": wf_id})
```

**Naming convention:**
- `augent.orchestrator` — Orchestration
- `augent.llm` — LLM calls
- `augent.agents.<name>` — Agent-specific
- `augent.guardrails` — Guardrail events
- `<usecase_name>.<module>` — Use-case logs

### Trace Context (`ai_agents_core.logging.context`)

```python
from ai_agents_core.logging import set_trace_context, clear_trace_context

set_trace_context(workflow_id="uuid", node_name="analyser")
clear_trace_context()
```

---

## Policies

### NodePolicy (`ai_agents_core.orchestration.policies`)

Aggregated policy bundle passed to `GraphBuilder.add_node()`.

```python
from ai_agents_core.orchestration import (
    NodePolicy, RetryPolicy, TimeoutPolicy, CircuitBreakerPolicy,
    BackoffStrategy,
    CONSERVATIVE_POLICY, FAST_FAIL_POLICY, BATCH_POLICY,
)
```

**Preset policies:**

| Preset | Retries | Timeout | Concurrency | Use for |
|--------|---------|---------|-------------|---------|
| `CONSERVATIVE_POLICY` | 5 (exp, 2s base) | 60s | 5 | External API, LLM calls |
| `FAST_FAIL_POLICY` | 1 (no retry) | 5s | unlimited | Health checks, validation |
| `BATCH_POLICY` | 3 (exp, 1s base) | 120s | 10 | Batch processing, storage writes |

**Custom policy:**
```python
my_policy = NodePolicy(
    retry=RetryPolicy(
        max_attempts=3,
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        base_delay_s=1.0,
    ),
    timeout=TimeoutPolicy(node_timeout_s=30.0),
    circuit_breaker=CircuitBreakerPolicy(failure_threshold=5),
    concurrency=3,
)
```

### RetryPolicy
- `max_attempts: int = 3` — total attempts (1 = no retry)
- `backoff_strategy: BackoffStrategy` — FIXED, LINEAR, or EXPONENTIAL
- `base_delay_s: float = 1.0`
- `max_delay_s: float = 30.0` — hard cap
- `jitter: bool = True` — ±25% random jitter

### CircuitBreakerPolicy
- `failure_threshold: int = 5` — consecutive failures to trip
- `recovery_timeout_s: float = 60.0` — wait before probing
- `success_threshold: int = 2` — successes to reset

---

## State and Enums

### BaseWorkflowState (`ai_agents_core.orchestration.state`)

Base TypedDict all use-case states must extend.

```python
from ai_agents_core.orchestration import BaseWorkflowState

class MyState(BaseWorkflowState, total=False):
    task: str
    result: str
    # ... use-case fields
```

**Base fields (from `BaseWorkflowState`):**
| Field | Type | Description |
|-------|------|-------------|
| `workflow_id` | `str` | UUID — propagated everywhere |
| `cycle_state` | `CycleState` | Set by Orchestrator only |
| `retry_counts` | `dict[str, int]` | Per-node attempt counters |
| `errors` | `list[WorkflowError]` | Append-only error log |
| `dead_letters` | `list[DeadLetterItem]` | Permanently discarded items |
| `items_processed` | `int` | Successful commits this run |
| `items_discarded` | `int` | Permanent discards this run |
| `metadata` | `dict[str, Any]` | Arbitrary pass-through |

### CycleState Enum
- `PENDING` — created, not started
- `RUNNING` — executing
- `SUCCESSFUL` — all nodes passed, zero discards
- `DEGRADED` — partial success, some failures
- `FAILED` — zero processed or critical failure
- `CANCELLED` — externally cancelled

### FailureType Enum
- `SYSTEM_ERROR` — infra/transient
- `CONTENT_QUALITY_FAILURE` — validation failed
- `CIRCUIT_OPEN` — breaker tripped
- `TIMEOUT` — time budget exceeded
- `CANCELLED` — externally cancelled

### Orchestration Exceptions
- `OrchestrationError` — base
- `CircuitOpenError` — breaker open
- `NodeTimeoutError` — node timed out
- `MaxRetriesExhaustedError` — all retries consumed
- `GraphBuildError` — invalid topology
- `CycleAlreadyRunningError` — concurrent cycle blocked

---

## Tools

### BaseTool + ToolRepository (`ai_agents_core.tools`)

```python
from ai_agents_core.tools import BaseTool, tool_repo

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"

    async def execute(self, **kwargs) -> dict:
        return {"result": "done"}
```

---

## Config

### Framework Config (`ai_agents_core.config.framework_config`)

Loads framework-level `.env` configuration. Use-case config merges on top.

```python
from ai_agents_core.config.framework_config import FrameworkConfig

config = FrameworkConfig()
langfuse_config = config.get_langfuse()
```

---

## Database (DAL)

### BaseRepository + BaseEntity (`ai_agents_core.db`)

```python
from ai_agents_core.db import BaseRepository, BaseEntity, FilterCondition
```

### CosmosDB (`ai_agents_core.db.cosmos`)

```python
from ai_agents_core.db.cosmos import CosmosRepository, CosmosDBConfig
```
