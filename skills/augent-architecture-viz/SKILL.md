---
name: augent-architecture-viz
description: >
  Generates a single self-contained interactive HTML file visualizing the AuGENT Enterprise AI
  Platform as a clickable node graph — framework layer (ai_agents_core) stacked above a use
  case pipeline with risk-level color coding, hidden edges, zoom/pan, and a collapsible sidebar.

  EXPLICIT TRIGGER — always activate when prompt starts with or contains "$viz":
  - "$viz show usecase2 architecture"
  - "$viz framework only"
  - "$viz custom pipeline for document-intelligence"

  IMPLICIT TRIGGER — activate on any of these patterns:
  - "show me the architecture", "render the platform diagram", "architecture explorer"
  - "draw a flow diagram for [usecase X]", "how do the components connect"
  - "visualize the platform", "explore the framework structure"
  - "show the pipeline", "diagram the graph", "map the modules"
  - Any request to visualize, map, diagram, render, draw, or explore AuGENT architecture

  When triggered, ALWAYS generate the visualization HTML — never respond with just text.
  If "$viz" is used with no topic, generate the default usecase2 visualization.
compatibility: Designed for Claude Code, opencode, and compatible AI coding agents. Output is a self-contained HTML file — no server, no build step, works in any browser.
allowed-tools: Bash Read Write Glob Grep Task
metadata:
  author: AuGENT Platform Team
  version: "1.2"
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
- Use the `$viz` prefix for explicit activation (skill triggers unconditionally)

Do NOT use this skill for:
- Editing the framework code itself (use `augent-usecase-builder`)
- Generating use cases from scratch (use `augent-usecase-builder`)
- Documentation prose (write markdown instead)
- General codebase analysis unrelated to architecture visualization

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

Use `nodeEdge(fromId, toId, color, width, dash, type)` for same-row
connections (right→left ports, horizontal lines).

Use `drawEdgeCore(fromId, toId, fromPort, toPort, color, width, dash, type)`
for cross-row connections (bottom→top or top→bottom ports). The `drawEdgeCore`
function handles four routing cases:

| Case | Ports | Path type | Arrowheads |
|------|-------|-----------|------------|
| Same row | right→left | L-shaped orthogonal | Perfect |
| Cross-row | bottom→top | L-shaped drop elbow | Perfect |
| Side arc | left→left | 14px legs + curve | OK (arrows on straight legs) |
| Down-then-left | bottom→left (dy>50) | L-shaped elbow | Perfect |
| Fallback | any | Straight line | Perfect |

**CRITICAL**: All arrowheads use only `L` (straight line) segments for the
final path. Never use `C` (cubic Bezier) for the last segment — the tangent at
Bezier endpoints causes tilted/crooked arrowheads in browser SVG renderers.
The fix is to replace `C` with orthogonal `L`:
```
Bad:  M x1,y1 C x1,midY x2,midY x2,y2    ← crooked arrowheads
Good: M x1,y1 L x1,dropY L x2,dropY L x2,y2  ← perfect
```

See `references/visual-spec.md` for the port decision table and
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

## Quality Checklist

Before finishing, verify EVERY item:
- [ ] HTML is fully self-contained — no `<link>`, no `<script src>`, no `<img src="http...">`
- [ ] SVG has correct viewBox (`0 0 2700 1200`) and explicit width/height
- [ ] Dark engineering theme applied: `#0B0E14` bg, `#4D9EFF` accent, monospace font
- [ ] Framework layer shows 5 columns: Orchestration, Agents, Guardrails, LLM Service, Observability
- [ ] Use case layer shows pipeline nodes in topological order with correct branching
- [ ] Hidden edges — not all visible at once, revealed on node selection
- [ ] Zoom/pan implemented (scroll to zoom toward cursor, drag to pan)
- [ ] Search/filter input present and functional
- [ ] Collapsible sidebar with legend and detail panel on node click
- [ ] Zero emoji characters anywhere in the HTML
- [ ] No Mermaid, D3, Cytoscape, or external libraries — pure SVG + JS
- [ ] No `api_core/` modules shown unless user explicitly asked
- [ ] Output works when double-clicked (no server, no build step)
- [ ] Handoff message given to user with file path and interaction model

## Problems Encountered & Solutions

### Problem: Crooked Arrowheads on Curved/Bezier Edges
- **Problem encountered**: SVG marker arrows (`marker-end`) on cubic Bezier curves in `drawEdgeCore` connecting nodes across different rows (bottom→top, right→left) appear tilted or crooked in browser renderers. The tangent at Bezier endpoint rarely aligns with the arrow direction.
- **Affected routing cases in `drawEdgeCore`**: `right→left` (same-row curves) and `bottom→top` (cross-row branches like orch_router → context_coll/portfolio_map).
- **How it was fixed**: Replaced `C` (cubic Bezier) commands with orthogonal `L` (line) segments in both routing cases:
  ```
  // OLD (crooked):
  path = "M p1.x,p1.y C p1.x,midY p2.x,midY p2.x,p2.y"
  // NEW (perfect):
  path = "M p1.x,p1.y L p1.x,dropY L p2.x,dropY L p2.x,p2.y"
  ```
  Since the final path segment is always a straight `L` entering the destination port, the SVG arrow marker calculates a perfectly straight tangent.

### Problem: Legend Shows Only Color Blocks, Not Line Styles
- **Problem encountered**: The side panel legend displays edge types as plain color blocks (`<div class="swatch">`), making it impossible to distinguish solid vs dashed vs dotted edges. For example, a yellow dashed confirmation branch and a green solid development branch both appear as simple colored rectangles. Missing edge types (development, confirmation) also not shown.
- **How it was fixed**: Replaced `.swatch` divs with inline `<svg>` elements that render actual lines matching the edge style (stroke color, stroke-width, stroke-dasharray). Added missing legend entries for Development (green solid) and Confirmation (yellow dashed). Each legend item now shows the exact line style used in the diagram.

### Problem: Zoom Fit Ignores Sidebar State
- **Problem encountered**: When clicking "Fit" or toggling the sidebar, the diagram fits to `container.clientWidth` (always 100% viewport width). The sidebar overlays the right 320px, so the centered diagram gets hidden behind the sidebar when open. When sidebar is collapsed, the fit doesn't reclaim the available space.
- **How it was fixed**: In `fitView()`, subtracted `sidebar.offsetWidth` from `container.clientWidth` when sidebar is open. The sidebar toggle timeout increased from 300ms to 350ms to wait for CSS `transition: width 0.25s` to complete before recalculating.

