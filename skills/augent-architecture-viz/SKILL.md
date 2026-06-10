---
name: augent-architecture-viz
description: >
  Generate a single self-contained interactive HTML architecture visualization for the
  AuGENT Enterprise AI Platform, showing the framework layer (ai_agents_core) and a use
  case layer stacked vertically with clickable nodes, risk-level color coding, and
  connection arrows. Use whenever the user asks to visualize, map, diagram, render, draw,
  or explore the AuGENT architecture, framework internals, use case pipelines, or how a
  specific use case connects to the platform — even if the user just says "show me the
  architecture", "draw a flow diagram for usecase X", "how do the components connect",
  "render the platform diagram", "explore the framework structure", "architecture
  explorer", or "visualize the platform". Triggers on any architecture/flow/diagram
  request related to AuGENT.
---

# AuGENT Architecture Visualizer

Generates a single self-contained HTML file that visualizes the AuGENT platform
as an interactive, clickable node graph. Two layers stacked vertically: the
**framework** (ai_agents_core) on top and the **use case** pipeline on bottom.

The output is one HTML file the user can open in any browser. No CDN, no
network calls, no build step.

## When to use this skill

Use this skill when the user wants to:
- See how the AuGENT framework and a specific use case fit together
- Walk a new team member through the platform structure visually
- Demo the platform to stakeholders and need a single shareable artifact
- Explore module connections and risk levels of a use case
- Replace a static slide or PDF diagram with something interactive

Do NOT use this skill for:
- Editing the framework code itself (use `augent-usecase-builder`)
- Generating use cases from scratch (use `augent-usecase-builder`)
- Documentation prose (write markdown instead)

## Inputs

The skill needs three things before generating:

1. **Use case name** — which `usecases/<name>/` to visualize. Default: `usecase2`.
2. **Use case flow** — the ordered list of nodes/agents in the pipeline and any
   conditional branches. Read from `usecases/<name>/graph.py` and the `nodes/`
   and `agents/` directories. If the flow is unclear, ask the user.
3. **Framework subset** — which `ai_agents_core` packages to show. Default
   includes only the packages actually used by the use case (no `api_core`).

If the user does not specify a use case, default to `usecase2` and proceed.
If the user says "just show me the framework", skip the use case layer and
emit only the framework.

## Output contract

Produce the complete HTML as inline text in your response. Do NOT say "I'll
create a file" or reference a path — output the raw HTML code directly so the
user can copy-paste it. Save to a path only if the user explicitly asks.

The HTML MUST:
- Be self-contained — inline CSS, inline JS, no `<link>` or external `<script src>`.
- Render correctly when double-clicked (no server, no build).
- Use a dark engineering theme: `#0B0E14` background, `#131720` surfaces,
  `#4D9EFF` accent, system monospace font.
- No emojis. No external fonts. No external images.

## Required visual structure

Two horizontal sections stacked vertically inside one SVG canvas. Full spacing,
styling, risk color, and edge type specifications are in
[visual-spec.md](references/visual-spec.md). The implementation skeleton and
framework/UC layouts are in [html-skeleton.md](references/html-skeleton.md).

1. **Framework layer (top)**: 5 horizontal columns — Orchestration, Agents,
   Guardrails, LLM Service, Observability. Each column contains its modules as
   vertically-stacked nodes with risk-level color coding.
2. **Use case layer (bottom)**: Pipeline nodes in topological order. For
   usecase2 (default), two rows with a router node branching to development
   (green curve) and confirmation (yellow dashed) paths.

Detailed interactivity behavior (click, edge visibility, zoom/pan, search,
sidebar) is in [interactivity.md](references/interactivity.md).

## Edge routing

Use `smartEdge(fromId, toId, ...)` as default — it auto-selects face-to-face
ports, applies narrow-gap overrides, and picks the correct arrowhead
orientation. See `references/visual-spec.md` for the port decision table and
the five manual override helpers (`leftArc`, `rtEdge`, `nodeEdge`, `drawEdge`).

## Handoff contract

After generating, tell the user:
- The exact file path
- That it is self-contained (open in any browser, no server needed)
- The keyboard/mouse interaction model
- That they can request a different use case, different framework subset, or
  adjustments to spacing/colors and you will regenerate

## What NOT to do

- No Mermaid, Cytoscape, D3, or any external library. Pure SVG + JS.
- No edges that all appear at once. Hidden-by-default.
- No node names overflowing their blocks.
- No `api_core/` modules unless the user asks.
- No emojis anywhere in the HTML.
- No CDN fonts or images.
- No `<iframe>`, `<embed>`, or `<object>`.
- No build step. Output must work when double-clicked.

## Quick regeneration

For a different use case: update `ucNodes` array and column headers. Keep the
framework section unchanged. See `references/html-skeleton.md` for the
framework column layout and default usecase2 node arrangement.
