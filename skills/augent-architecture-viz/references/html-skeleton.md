# HTML Implementation Skeleton

A working HTML has these moving parts in this order:

1. Flexbox layout: `#app { display: flex; width: 100%; height: 100%; }` with `#canvas-wrap { flex: 1; position: relative; overflow: hidden; }` and `#sidebar { width: 320px; z-index: 10; }`.
2. SVG element inside `#canvas-wrap` with `xmlns`, `viewBox="0 0 2700 1200"`, AND explicit `width="2700"` and `height="1200"` attributes. (CRITICAL: Without width/height, browser scale transforms break).
3. `<defs>` with markers (one per edge color), a grid pattern, and `<clipPath>` for nodes.
4. Background grid rect.
5. Title and subtitle text.
6. Framework section background rect + heading + column sub-headings.
7. Framework nodes (use `drawNode(x, y, id, label, cls, risk, col, role)`).
8. Framework internal edges (use `drawEdge`/`smartEdge`/`leftArc`/`rtEdge`/`nodeEdge`).
9. Divider line + "USE CASE LAYER" heading.
10. Use case section background + column sub-headings.
11. Use case nodes (row 1 + row 2).
12. Use case pipeline edges (row 1 sequential, row 2 sequential, conditional branches).
13. Framework-to-use case dependency edges (drawn but hidden).
14. CSS rule: `.edge-group .edge-path { opacity: 0; }` — hides all edges by default.
15. Zoom/pan/selection/search JS handlers.
16. Sidebar HTML + toggle button + handlers.
17. `fitView()` called once on load via `window.load` + double `requestAnimationFrame`.

## Code Rules

- One function per concern: `drawNode`, `drawEdge`, `smartEdge`, `nodeEdge`, `rtEdge`, `leftArc`, `nodePort`, `fitView`, `selectNode`, `deselectAll`.
- A global `allNodes[]` and `allEdges[]` array — every node/edge registers itself there on creation.
- Use `setAttribute` for SVG attributes, not inline style strings.
- Use `createElementNS('http://www.w3.org/2000/svg', tag)` for every SVG element.
- Use vanilla JS, no framework (no React, Vue, D3, Mermaid, Cytoscape).
- One `<style>` block in `<head>`, one `<script>` block at the end of `<body>`.
- All edges hidden by default (`opacity: 0`). Selection toggles `.visible`/`.highlighted`/`.dimmed`.

## Framework Layout (Top Section)

5 columns:

| Column | Modules |
|---|---|
| Orchestration | Orchestrator, GraphBuilder, NodeExecutor |
| Agents | AuGENTAgent, AgentExecutor |
| Guardrails | InputGuard, OutputValid., ContentSafety, SchemaReg. |
| LLM Service | LLMService, AzureOpenAI |
| Observability | EventBus, LangfuseExp., Metrics |

## Default Usecase2 Layout (Bottom Section)

```
row 1: event_detector -> trigger_classifier -> novelty_classifier -> orch_router
row 2: context_coll. -> analyser -> portfolio_map. -> summary_agent -> distributor
```

Green curved path from `orch_router` down to `context_coll.` (development branch).
Yellow dashed path straight to `portfolio_map.` (confirmation branch).

## What NOT to Include

- No `api_core/` modules unless user asks.
- No Mermaid, Cytoscape, D3, or any external library.
- No `<link>` or external `<script src>`.
- No `<iframe>`, `<embed>`, or `<object>`.
- No CDN fonts or images.
- No emojis anywhere in the HTML.
- No build step — output must work when double-clicked.
