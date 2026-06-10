# Interactivity Specification

## Node Click Behavior

- Highlight selected node with blue border + glow
- Reveal only its directly connected edges (others stay hidden)
- Dim all non-connected nodes to 12% opacity
- Populate right sidebar with: name, class, column, risk badge, role description, outgoing edges list, incoming edges list (each clickable to navigate)

## Edge Visibility

- **All edges are hidden by default** (`opacity: 0`). The diagram starts clean.
- On node selection, edges incident to the selected node become fully visible (opacity 0.5).
- Edges directly touching the selected node get a glow (drop-shadow) + thicker stroke (3.5px).
- Edges between second-degree neighbors become faint (opacity 0.15).
- Non-relevant edges drop to 3% opacity.

## Navigation Controls

- **Scroll wheel**: zoom in/out (anchored to cursor)
- **Right-click + drag**: pan
- **Left-click**: select node / deselect if same node clicked again
- **Left-click on empty canvas**: deselect everything

## Search Box

- A search input box positioned absolute over the top-left of the canvas.
- Typing filters nodes by matching text against label, class, role, and column.
- Unmatched nodes get `.dimmed` class.

## Sidebar (right side, 320px wide)

Sections from top to bottom:
1. **Zoom & Navigation** — `+`, `-`, `%` label, `Fit` button. Hint: "Scroll: zoom | Right-drag: pan | Click: details"
2. **Risk Levels** — swatch grid: God Module, High Coupling, Ext Dependency, Extension Pt, Stable
3. **Edges** — swatches: Orchestration, Guardrail, Data, Dependency, Event, Pipeline
4. **Use Case Pipeline** — short prose summary of the use case flow
5. **Detail** — populated only when a node is selected, with incoming/outgoing edge lists using `->` and `<-` arrows

## Collapsible Sidebar

- Hamburger button (top-right corner of canvas, three horizontal bars) toggles sidebar open/closed
- When closed, sidebar width transitions to 0 with smooth 0.25s transition
- Trigger `fitView()` 300ms after toggle so canvas re-centers

## Zoom-to-Fit

```js
function fitView() {
  const wrap = document.getElementById('canvas-wrap');
  const bw = wrap.clientWidth, bh = wrap.clientHeight;
  const sab = document.getElementById('sidebar');
  const aw = bw - (sab ? sab.clientWidth : 0);
  const s = Math.min(aw / W, bh / H);
  scale = s;
  vx = (aw - W * s) / 2;
  vy = (bh - H * s) / 2;
  applyT();
}
```

Called once on load via `window.load` + double `requestAnimationFrame` so `wrap.clientWidth` is measured after flex layout has fully painted.
