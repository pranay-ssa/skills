# ArchMap Visual Specification

This document strictly defines the styling and visual rules for the ArchMap SVG output.

## 1. Dynamic Data-Flow Animation (Moving Arrows)
To simulate data velocity (data flowing through the connections), all active edges must use CSS `stroke-dasharray` and a CSS animation loop for `stroke-dashoffset`.

### CSS Implementation
Include the following in your HTML `<style>` block:

```css
/* Apply this to SVG path elements representing data connections */
.flowing-data-edge {
  stroke-dasharray: 10 10;
  animation: dataFlow 0.8s linear infinite;
  fill: none;
  stroke: #4F46E5; /* Indigo/purple for active data */
  stroke-width: 3px;
}

@keyframes dataFlow {
  from { stroke-dashoffset: 20; }
  to { stroke-dashoffset: 0; }
}
```

## 2. Shape and Color Hierarchies
Nodes must visually communicate their exact operational tier:

| Component Type | Color Theme | Shape | Example Roles |
| --- | --- | --- | --- |
| Standard Logic | `#1E293B` (Slate) | Rectangle with rounded corners (rx=4) | Controllers, local scripts, processing handlers |
| AI / LLM Agent | `#312E81` (Indigo) | Rectangle with rounded corners (rx=6) | LLM-backed agents, prompt-driven nodes |
| External / API | `#0D9488` (Teal) | Rectangle with sharp corners | Public APIs, External integrations, CDN hooks |
| Storage / DB | `#0F172A` (Dark Blue) | Cylinder geometry (or `<ellipse>` capped rectangle) | Database targets, local storage, object buckets |
| Entry Point | `#16A34A` (Green) | Rectangle with thick dashed border | API Routes, WebSocket listeners |
| Framework / Platform | `#1D2D44` (Navy) bg + `#4D9EFF` (Blue) border | Rectangle with rounded corners (rx=4) | Platform/engine modules the target imports (e.g. `ai_agents_core.*`). Rendered in the top framework tier, visually distinct from both slate use-case nodes and indigo AI agents. |

## 3. Node Hover Effect (Nice to Have)

> **This is an optional enhancement.** The baseline spec only requires a `cursor: pointer` on nodes. The glow effect below improves perceived interactivity and is recommended when the output is destined for a dashboard or presentation context.

Instead of scaling nodes on hover (which can cause layout jitter in dense graphs), use a **color-matched `drop-shadow` glow** that reads the node's own border stroke color at runtime. This means each operational tier glows in its own color automatically — no hardcoded per-node CSS needed.

### Tier-to-Glow Color Reference

| Component Type | Border Stroke | Glow Color |
| --- | --- | --- |
| Standard Logic | `#475569` | Cool slate |
| AI / LLM Agent | `#6366F1` | Indigo / violet |
| External / API / Delivery | `#14B8A6` | Teal |
| Storage / DB | `#334155` | Dark slate |
| Entry Point | `#16A34A` | Green |
| Framework / Platform | `#4D9EFF` | Blue |

## 3b. Cross-Tier Edge Color Coding

When a target depends on a framework/platform package (auto-discovered per `SKILL.md`), the dashed animated edges linking each framework module to the target nodes that import it are color-coded by the framework subsystem.

**Do NOT hardcode subsystem names** (those are platform-specific). Instead, derive them:

1. Parse each framework import (e.g. `from ai_agents_core.orchestration.orchestrator import Orchestrator`).
2. Extract the **second-level package segment** — the token immediately after the platform root. This is the subsystem key.
   - `ai_agents_core.orchestration.*` → subsystem = `orchestration`
   - `ai_agents_core.guardrails.*` → subsystem = `guardrails`
   - `company_platform.data.*` → subsystem = `data`
3. Group nodes by their subsystem key, then assign each **unique subsystem** a color from a fixed 8-color LUT, cycling if more than 8 groups exist. This ensures the skill works on any platform without prior knowledge of its internal package structure.
4. If a subsystem produces a single node AND its semantic role (inferred from the import's consumer) matches another group, it MAY be merged into that group for visual economy (e.g. a single observability adapter node can live in a cross-cutting group).

| Palette Index | Edge Color | Typical semantics (for label hint, NOT a hard rule) |
| --- | --- | --- |
| 0 | `#6366F1` (Indigo) | Orchestration, workflow, state machines |
| 1 | `#EF4444` (Red) | Validation, guardrails, security |
| 2 | `#F59E0B` (Amber) | LLM, AI models, inference |
| 3 | `#10B981` (Emerald) | Observability, telemetry, adapters |
| 4 | `#64748B` (Slate) | Logging, diagnostics |
| 5 | `#334155` (Dark slate) | Storage, database, persistence |
| 6 | `#8B5CF6` (Violet) | Reserved (falls outside common groups) |
| 7 | `#EC4899` (Pink) | Reserved (falls outside common groups) |

**Example (AuGENT):** the platform root is `ai_agents_core`. The second-level segments are `orchestration`, `guardrails`, `llm`, `observability`, `logging`, `db`. These map to palette indices 0–5 respectively. The resulting edges use the corresponding colors from the LUT above. This is the application of a generic rule, not hardcoded platform knowledge.

Cross-tier edges are hidden by default (same §4 rule) and revealed on click: clicking a target node lights its framework dependencies; clicking a framework node lights all its consumers (blast radius).

### JavaScript Implementation

Attach `mouseenter` / `mouseleave` listeners after the SVG is in the DOM. Read the stroke from the first child shape so the color always matches the node's tier automatically:

```js
document.querySelectorAll('.node').forEach(node => {
  node.addEventListener('mouseenter', () => {
    const shape = node.querySelector('rect, ellipse, circle, path');
    const color = shape ? (shape.getAttribute('stroke') || '#6366F1') : '#6366F1';
    node.style.filter = `drop-shadow(0 0 8px ${color}) drop-shadow(0 0 3px ${color})`;
  });
  node.addEventListener('mouseleave', () => {
    // Keep glow alive if node is in selected/active state
    if (!node.classList.contains('active')) {
      node.style.filter = 'none';
    }
  });
});
```

> Do NOT use `transform: scale()` for hover. It causes layout reflow in large SVGs and can shift nearby edges.

## 4. Pure SVG Rules & Edge Routing
- Do NOT use `<foreignObject>` for generic node rendering unless absolutely necessary. Stick to pure `<rect>`, `<text>`, and `<path>`.
- **Hidden by Default (STRICT):** ALL edges — both the faint structural `.static-edge` layer AND the animated `.flowing-data-edge` layer, AND any cross-tier `.framework-edge` layer — must be `opacity: 0` on initial render. Do NOT leave a static skeleton visible. At rest the graph shows ONLY nodes. Edges appear exclusively when a connected node is clicked. This is non-negotiable; a always-on skeleton violates the spec.
- **No `transform` on nodes:** The `.node` selector MUST NOT carry `transition: transform ...` or any `transform: scale()` on hover. Hover feedback is delivered solely via the JavaScript color-matched `drop-shadow` injection (see §3). A `transform` transition in `.node` is a spec violation even if unused — remove it.
- **Edge Routing Rules:**
  - **Same row connections (Right→Left):** Use L-shaped orthogonal lines.
  - **Cross-row connections (Bottom→Top or Top→Bottom):** Use L-shaped drop elbows.
- **CRITICAL - Arrowhead Fix**: For paths with elbows or curves, the final path segment entering the destination port MUST be a straight line (`L`) and not a bezier curve (`C`) to prevent the SVG arrow marker (`marker-end`) from rendering tilted or crooked. 
  - *Bad:* `M x1,y1 C x1,midY x2,midY x2,y2`
  - *Good:* `M x1,y1 L x1,dropY L x2,dropY L x2,y2`

## 5. Legend Bar (non-negotiable position)

The legend MUST be a **bottom-left collapsible bar** (see `html-skeleton.md` point 7 for the pill + expand-on-hover CSS).

## 6. Framework Category Group Labels

When grouping framework modules into visual categories (orchestration, LLM, guardrails, etc.), render each category label as an SVG `<text>` element in the matching subsystem color at `font-size="13"` bold, positioned just above the dashed group box (`y="42"` for a box whose top edge is at `y="50"`). These labels are larger than node text so they are immediately scannable without zoom.
