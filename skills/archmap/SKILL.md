---
name: archmap
description: >
  Generates a single self-contained interactive HTML file visualizing any codebase's architecture and data flow.
  Leverages the output of `graphify` (knowledge graph) to efficiently map component connections.
  Outputs a split-screen dashboard with dynamic CSS-animated SVG data flows and a rich contextual sidebar.

  EXPLICIT TRIGGER — always activate when prompt starts with or contains "$archmap":
  - "$archmap show architecture"
  - "$archmap map the pipeline"
  - "$archmap visualize the repo"

  IMPLICIT TRIGGER — activate on:
  - "generate an archmap"
  - "visualize this project using graphify data"

  When triggered, ALWAYS generate the visualization HTML — never respond with just text.
compatibility: Designed for any codebase. Works in any browser (self-contained HTML, no external CDNs/libraries).
allowed-tools: Bash Read Write Glob Grep Task
metadata:
  author: ArchMap Generalized Visualizer
  version: "2.0"
---

# ArchMap Data-Flow Visualizer

Generates a single self-contained HTML file that visualizes a codebase as an interactive, clickable node graph mapping how data moves through the system.

The output is **one HTML file** the user can open in any browser. No CDN, no network calls, no build step.

## How to use this skill

Use this skill when the user wants to visualize any repository's architecture efficiently.
Instead of crawling and reading all source code files (which is slow and token-expensive), this skill **relies on `graphify`** data.

### Step 1: Ingestion & Knowledge Graph (Token Efficient)
1. Locate the output of the `graphify` tool in the workspace (e.g., `graph.json` / `knowledge-graph.json`, `graphify-out/`, or related structural files created by `graphify update .`).
2. Read these pre-computed graph files to extract the entry points, components, database targets, and data flow connections. Do not manually read application code unless necessary to fill gaps.
3. **Field → attribute mapping.** Map graphify fields directly onto the HTML; do not re-derive by reading source:
   - node `id` / label → `<text>` element label AND the `selectNode(id, ...)` argument.
   - node `type` / kind → SVG shape + color tier per `references/visual-spec.md §2` (Standard Logic=rect, AI/LLM=indigo rect, External=teal rect, Storage=cylinder, Entry=green dashed rect).
   - node file path → sidebar "Source Path".
   - node role/summary → sidebar "Functional Role".
   - edge `source`/`target` → path `data-from`/`data-to` (mandatory on every edge).

### Step 2: Framework-Tier Auto-Discovery (Generic)
If the target codebase imports a shared platform/framework package, surface it as a second visual tier — do NOT omit it.

1. Detect the framework package by scanning the target's imports for a recurring `from <pkg>.*` / `import <pkg>` root that is NOT the target itself and NOT a third-party lib (e.g. a use case importing `ai_agents_core.*`, a service importing `company_platform.*`). One framework root per generation.
2. Group every imported framework submodule by subsystem and render each as a `.framework-node` in the top band (navy `#1D2D44` + blue `#4D9EFF` border). Record which target file imports which submodule.
3. Emit `.framework-edge` dashed paths from each framework module to the target nodes that import it, color-coded by the second-level package segment (the subsystem key) using the palette LUT in `references/visual-spec.md §3b`.
4. Side effects of discovery become sidebar content: a framework node's sidebar lists its module path + every consumer; a target node's sidebar may list the framework modules it depends on.
5. No framework import found → skip this step silently; produce a single-tier graph (still fully spec-compliant).

### Step 3: Generating the Visualization
You must generate a split-screen dashboard (Left: Canvas, Right: Sidebar).
- The canvas must use **pure SVG** and JavaScript (no Mermaid.js, D3, or Cytoscape).
- You MUST implement the "Moving Arrows" dynamic data flow effect using SVG `stroke-dasharray` and CSS animation loops.

## Output contract

Produce the complete HTML as inline text in your response. Do NOT say "I'll create a file" or reference a path — output the raw HTML code directly so the user can copy-paste it. Save to a path only if the user explicitly asks.

The HTML MUST:
- Be self-contained — inline CSS, inline JS, no `<link>` or external `<script src>`.
- Render correctly when double-clicked (no server, no build).
- Use a dark engineering theme: `#0B0E14` background, `#131720` surfaces, `#4D9EFF` accent, system monospace font.
- No emojis. No external fonts. No external images.

## Required Visual Structure
The layout and interaction logic are strictly defined in the reference files. Before generating the HTML, you MUST read:
1. `references/visual-spec.md` - Details the CSS animation for data flow (`stroke-dashoffset`), node shapes, and color coding.
2. `references/html-skeleton.md` - Details the split-screen layout and sidebar metadata binding.

## Handoff contract
After generating, tell the user:
- That the visualization is self-contained.
- The interaction model (pan, zoom, sidebar clicks).
- That it successfully utilized `graphify` data for efficiency.

## Conformance Checklist (non-negotiable)
Before declaring done, verify the generated HTML against `references/visual-spec.md`:
- [ ] **All edges hidden by default.** `.static-edge`, `.flowing-data-edge`/`.dynamic-edge`, AND `.framework-edge` all start at `opacity: 0`. No always-on skeleton. Edges appear only via `selectNode()` illumination.
- [ ] **No `transform` on `.node`.** No `transition: transform ...`, no `transform: scale()` hover. Hover uses JS `drop-shadow` only.
- [ ] **Orthogonal routing.** Every `<path>` uses straight `L` segments; the final segment entering a port is a straight `L`, never a bezier `C` (prevents tilted arrowheads).
- [ ] **Mandatory edge data attributes.** Every edge carries `data-from` + `data-to` matching node `id`s.
- [ ] **`selectNode()` resets all edges first**, then lights `[data-from=id]` + `[data-to=id]`.
- [ ] **Framework tier present** when a framework import root exists; cross-tier edges color-coded by subsystem.
- [ ] Self-contained: inline CSS/JS, no `<link>`, no external `<script src>`, no CDN, renders on double-click.
