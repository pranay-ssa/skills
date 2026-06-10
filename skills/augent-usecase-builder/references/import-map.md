# Import Map — AuGENT v0.1.0

> Every import path verified against `ai_agents_core/` as of 2026-06-08.
> **Never guess an import path.** Use this map.

---

## Orchestration (use these from `ai_agents_core.orchestration`)

```python
# Core builders — these are the most-used imports
from ai_agents_core.orchestration import GraphBuilder, END, Orchestrator

# State
from ai_agents_core.orchestration import (
    BaseWorkflowState, CycleState, FailureType,
    WorkflowError, DeadLetterItem,
)

# Policies
from ai_agents_core.orchestration import (
    NodePolicy, RetryPolicy, TimeoutPolicy, CircuitBreakerPolicy,
    BackoffStrategy,
    CONSERVATIVE_POLICY, FAST_FAIL_POLICY, BATCH_POLICY,
)

# Event bus
from ai_agents_core.orchestration import EventBus, EventType, WorkflowEvent

# Middleware (rarely needed by use cases)
from ai_agents_core.orchestration import NodeMiddleware, MiddlewareChain

# Circuit breaker (for monitoring/testing)
from ai_agents_core.orchestration import CircuitBreaker, CircuitState

# Checkpointing (for state persistence)
from ai_agents_core.orchestration import (
    PostgresCheckpointConfig, create_checkpointer, create_sync_checkpointer,
)

# Internal — exposed for extension, not needed for normal use
from ai_agents_core.orchestration import (
    classify_failure, execute_with_retry, classify_cycle, run_with_cycle_guard,
)

# Exceptions
from ai_agents_core.orchestration import (
    OrchestrationError, CycleAlreadyRunningError, CircuitOpenError,
    NodeTimeoutError, MaxRetriesExhaustedError, GraphBuildError,
)
```

## Agents

```python
from ai_agents_core.agents import AuGENTAgent
from ai_agents_core.agents import AgentExecutor       # advanced use
from ai_agents_core.agents import AgentRequest, AgentResponse
from ai_agents_core.agents import AgentRegistry
```

## LLM

```python
from ai_agents_core.llm import LLMService
from ai_agents_core.llm import LLMMessage, LLMRequest, LLMResponse
```

**Additional LLM modules (use only if needed):**
```python
from ai_agents_core.llm.azure_openai_client import AzureOpenAIClient
from ai_agents_core.llm.openrouter_client import OpenRouterClient
from ai_agents_core.llm.base import BaseLLMClient
from ai_agents_core.llm.model_catalog import MODEL_CATALOG
from ai_agents_core.llm.prompt_manager import PromptManager
from ai_agents_core.llm.structured import build_json_schema_response_format
from ai_agents_core.llm.validators import ResponseValidator
from ai_agents_core.llm.exceptions import (
    LLMAuthenticationError, LLMBadRequestError, LLMRateLimitError,
    LLMTimeoutError, LLMProviderDownError, LLMError, LLMRetryableError,
)
```

## Guardrails

```python
from ai_agents_core.guardrails import (
    InputGuardrail,
    SchemaRegistry,
    OutputValidator,
    ContentSafetyClient,
)

# Models (return types)
from ai_agents_core.guardrails import (
    SanitisedMessage, ValidationResult, ContentSafetyResult,
)

# Exceptions
from ai_agents_core.guardrails import (
    GuardrailsError,
    InputValidationError,
    SchemaValidationError,
    ContentSafetyError,
    ContentSafetyUnavailableError,
)
```

## Logging

```python
from ai_agents_core.logging import setup_logging, get_logger
from ai_agents_core.logging import set_trace_context, clear_trace_context
```

## Observability

```python
from ai_agents_core.observability.adapters import EventBusAdapter
```

## Tools

```python
from ai_agents_core.tools import BaseTool, tool_repo
```

## Database

```python
from ai_agents_core.db import BaseEntity, BaseRepository, FilterCondition
```

---

## Import rules — DO NOT use these

```python
# WRONG — do not import from LangGraph directly
from langgraph.graph import END
# CORRECT
from ai_agents_core.orchestration import END

# WRONG — do not import from orchestration sub-modules directly
from ai_agents_core.orchestration.graph_builder import GraphBuilder
# CORRECT (use the public API)
from ai_agents_core.orchestration import GraphBuilder

# WRONG — do not import NodeExecutor directly
from ai_agents_core.orchestration.node_executor import NodeExecutor
# CORRECT — GraphBuilder handles NodeExecutor wrapping automatically

# WRONG — do not import LangChain/LangGraph directly in agent code
from langchain_openai import ChatOpenAI
# CORRECT — use LLMService
from ai_agents_core.llm import LLMService
```
