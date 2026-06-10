# Stage 4: Graph Assembly

Wires agents and nodes into a LangGraph workflow using GraphBuilder.

## 4.1 The complete graph pattern

In `usecases/<name>/ai_agents/graph.py`:

```python
from __future__ import annotations

from typing import Any

from ai_agents_core.orchestration import (
    GraphBuilder, END,
    BaseWorkflowState,
    BATCH_POLICY, CONSERVATIVE_POLICY, FAST_FAIL_POLICY,
)

# Import agents (AuGENTAgent instances used as nodes)
from .agents.agent_one import AgentOne
from .agents.agent_two import AgentTwo

# Import node functions (pure async functions)
from .nodes.node_one import node_one
from .nodes.node_two import node_two


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class <PascalCaseName>State(BaseWorkflowState, total=False):
    """<UseCase> workflow state."""
    task: str
    # ... use-case fields (defined in Stage 2)


# ---------------------------------------------------------------------------
# Router functions (pure — no LLM, no I/O)
# ---------------------------------------------------------------------------

def _route_after_agent(state: dict) -> str:
    """Route based on agent result."""
    status = state.get("status", "")
    if status == "continue":
        return "agent_two"
    return "done"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph():
    # 1. Instantiate agents
    agent_one = AgentOne()
    agent_two = AgentTwo()

    # 2. Create builder with use-case state
    builder = GraphBuilder(<PascalCaseName>State)

    # 3. Register nodes with appropriate policies
    #    BATCH_POLICY: batch processing, data transformation, storage
    #    CONSERVATIVE_POLICY: LLM calls, external APIs
    #    FAST_FAIL_POLICY: health checks, validation, fast reads
    builder.add_node("node_one",  node_one,  policy=BATCH_POLICY)
    builder.add_node("agent_one", agent_one, policy=CONSERVATIVE_POLICY)
    builder.add_node("agent_two", agent_two, policy=CONSERVATIVE_POLICY)
    builder.add_node("node_two",  node_two,  policy=BATCH_POLICY)

    # 4. Define entry point
    builder.set_entry("node_one")

    # 5. Add linear edges
    builder.add_edge("node_one", "agent_one")

    # 6. Add conditional edges (branching)
    builder.add_conditional_edge(
        "agent_one",
        router_fn=_route_after_agent,
        routing_map={
            "agent_two": "agent_two",
            "done": END,
        },
    )

    # 7. Terminal edge
    builder.add_edge("agent_two", END)

    # 8. Compile and return
    return builder.compile()
```

## 4.2 Policy selection guide

| Agent/Node type | Policy | Why |
|----------------|--------|-----|
| LLM agents | `CONSERVATIVE_POLICY` | 5 retries, 60s timeout — reliability critical |
| External API calls | `CONSERVATIVE_POLICY` | Same reasoning |
| Batch transforms | `BATCH_POLICY` | 3 retries, 120s timeout, 10 concurrency |
| Storage writes | `BATCH_POLICY` | Bulk operations benefit from concurrency |
| Validation/checks | `FAST_FAIL_POLICY` | No retry, 5s timeout — failures are expected |
| Simple computation | `FAST_FAIL_POLICY` | Deterministic, shouldn't fail |

## 4.3 Graph topology patterns

### Linear pipeline
```python
builder.add_node("A", fn_a)
builder.add_node("B", fn_b)
builder.add_node("C", fn_c)
builder.set_entry("A")
builder.add_edge("A", "B")
builder.add_edge("B", "C")
builder.add_edge("C", END)
```

### Branching (conditional)
```python
builder.add_conditional_edge(
    "classifier",
    router_fn=_route_by_classification,
    routing_map={
        "path_a": "agent_a",
        "path_b": "agent_b",
        "discard": END,
    },
)
```

### Loop (re-iterate)
```python
builder.add_conditional_edge(
    "analyser",
    router_fn=_route_after_analysis,
    routing_map={
        "enrich": "context_collector",  # back-edge
        "done": "next_node",
    },
)
```
Use a counter (`iteration_count`) in state to prevent infinite loops. The router
checks the counter and returns `"done"` when the limit is reached.

## 4.4 Router function rules

Router functions MUST be pure:
- **No LLM calls** — if you need LLM to decide routing, create an agent node that
  sets a field, then use a simple router reading that field
- **No I/O** — no filesystem, network, database calls
- **No side effects** — read-only on state
- **Return a string** — must be a key present in `routing_map`
- **Deterministic** — same state always produces same route

```python
# GOOD — pure, reads state, returns string
def _route(state: dict) -> str:
    return "path_a" if state.get("score", 0) > 0.5 else "path_b"

# BAD — calls LLM
def _route(state: dict) -> str:
    llm = LLM()  # NO!
    return llm.decide(state)

# BAD — has side effects
def _route(state: dict) -> str:
    write_to_file(state)  # NO!
    return "next"
```

## 4.5 Node naming rules

- Node names are `snake_case`: `"event_detector"`, `"insight_generator"`
- Names must be unique within a graph — `GraphBuilder` raises `GraphBuildError` on duplicates
- Node names appear in logs, metrics, and event bus — use descriptive names
- Convention: agent nodes use the agent name, function nodes describe the action

## Verification checklist

- [ ] `build_graph()` returns `builder.compile()`
- [ ] All nodes are registered before edges reference them
- [ ] Every path through the graph reaches `END`
- [ ] No orphaned nodes (unreachable from entry)
- [ ] Router functions are pure — verified no LLM/I/O/side effects
- [ ] Router `routing_map` keys match actual node names or `END`
- [ ] Loop edges have a termination condition (iteration counter)
- [ ] LLM agents use `CONSERVATIVE_POLICY`
- [ ] State import uses the TypedDict defined in this file
- [ ] `END` imported from `ai_agents_core.orchestration`, not LangGraph
