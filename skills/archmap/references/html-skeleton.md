# ArchMap HTML Layout & Skeleton

This document provides the foundational HTML and JavaScript structure for the generated ArchMap visualizer.

## Split-Screen Dashboard Layout
The application must use a dual-panel design:
- **Left Panel (Canvas):** Takes up the majority of the screen and renders the interactive SVG graph.
- **Right Panel (Context Sidebar):** A fixed-width sidebar (e.g., 350px) that appears or updates when a node is clicked.

### HTML Structure Example
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ArchMap Data-Flow Visualizer</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #0B0E14;
      color: #E2E8F0;
      font-family: monospace;
      overflow: hidden;
      display: flex;
      height: 100vh;
    }
    #canvas-container {
      flex: 1;
      position: relative;
      cursor: grab;
    }
    #sidebar {
      width: 350px;
      background-color: #131720;
      border-left: 1px solid #1E293B;
      padding: 20px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      transform: translateX(100%); /* Hidden by default */
      transition: transform 0.3s ease;
      position: absolute;
      right: 0;
      top: 0;
      height: 100%;
    }
    #sidebar.open {
      transform: translateX(0);
      position: relative;
    }
    /* SVG Styling */
    svg {
      width: 100%;
      height: 100%;
    }
    .node { cursor: pointer; }
    
    /* Flowing Edge from visual-spec.md */
    .flowing-data-edge {
      stroke-dasharray: 10 10;
      animation: dataFlow 0.8s linear infinite;
      fill: none;
      stroke: #4F46E5;
      stroke-width: 3px;
    }
    @keyframes dataFlow {
      from { stroke-dashoffset: 20; }
      to { stroke-dashoffset: 0; }
    }
  </style>
</head>
<body>

  <!-- Left Canvas -->
  <div id="canvas-container">
    <svg id="archmap-svg" viewBox="0 0 2000 1200">
      <defs>
        <!-- Arrowhead Marker -->
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#4F46E5" />
        </marker>
      </defs>
      
      <!-- Graph Group for Zoom/Pan -->
      <g id="graph-group">
        <!-- AGENT INJECTS NODES AND EDGES HERE -->
      </g>
    </svg>
  </div>

  <!-- Right Context Sidebar -->
  <div id="sidebar">
    <h2 id="sidebar-title">Component Name</h2>
    <div style="font-size: 12px; color: #4D9EFF; margin-bottom: 15px;" id="sidebar-type">Component Type</div>
    
    <div style="margin-bottom: 10px; color: #94A3B8;">
      <strong>File Path:</strong><br>
      <span id="sidebar-path">src/path/to/file.py</span>
    </div>

    <div style="margin-bottom: 20px; color: #CBD5E1;">
      <strong>Role Summary:</strong><br>
      <p id="sidebar-role">Description of what this block does, generated from graphify knowledge graph.</p>
    </div>
    
    <button onclick="closeSidebar()" style="padding: 10px; background: #1E293B; color: white; border: none; cursor: pointer;">Close</button>
  </div>

  <script>
    // 1. Sidebar Interaction & Edge Illuminator
    // ALL edges (static + dynamic + cross-tier framework) start at opacity:0.
    // Clicking a node resets every edge to 0, then lights only those touching the node.
    const sidebar = document.getElementById('sidebar');
    let selectedNodeId = null;

    function selectNode(id, type, path, role) {
      // (a) clear active markers
      document.querySelectorAll('.node').forEach(n => n.classList.remove('active'));
      const clicked = document.getElementById('node-' + id);
      if (clicked) clicked.classList.add('active');

      // (b) RESET EVERY EDGE — static, flowing, AND cross-tier framework edges — to 0
      document.querySelectorAll('.static-edge, .dynamic-edge, .framework-edge').forEach(edge => {
        edge.style.opacity = '0';
      });

      // (c) light only edges whose data-from OR data-to matches this node.
      //     For a use-case node this reveals its pipeline neighbours AND its framework deps.
      //     For a framework node this reveals its full consumer set (blast radius).
      document.querySelectorAll(`[data-from="${id}"], [data-to="${id}"]`).forEach(edge => {
        edge.style.opacity = '1';
      });

      // (d) update + open sidebar
      document.getElementById('sidebar-title').innerText = id;
      document.getElementById('sidebar-type').innerText = type;
      document.getElementById('sidebar-path').innerText = path;
      document.getElementById('sidebar-role').innerText = role;
      sidebar.classList.add('open');
      selectedNodeId = id;
    }

    function closeSidebar() {
      sidebar.classList.remove('open');
      document.querySelectorAll('.node').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.static-edge, .dynamic-edge, .framework-edge').forEach(edge => {
        edge.style.opacity = '0';
      });
      selectedNodeId = null;
    }

    // Attach click listeners to nodes:
    //   onclick="selectNode('<id>', '<type>', '<path>', '<role>')"
    // or bind dynamically. Every edge must carry data-from / data-to so the illuminator works.

    // 2. Zoom & Pan Logic
    const svg = document.getElementById('archmap-svg');
    const graphGroup = document.getElementById('graph-group');
    let isPanning = false, startPoint = {x:0,y:0}, endPoint = {x:0,y:0};
    let scale = 1, viewBox = {x:0,y:0,w:2000,h:1200};

    svg.addEventListener('mousedown', (e) => {
      isPanning = true;
      startPoint = {x: e.clientX, y: e.clientY};
    });
    
    svg.addEventListener('mousemove', (e) => {
      if (!isPanning) return;
      endPoint = {x: e.clientX, y: e.clientY};
      let dx = (startPoint.x - endPoint.x) * (viewBox.w / svg.clientWidth);
      let dy = (startPoint.y - endPoint.y) * (viewBox.h / svg.clientHeight);
      viewBox.x += dx;
      viewBox.y += dy;
      svg.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
      startPoint = {x: e.clientX, y: e.clientY};
    });

    svg.addEventListener('mouseup', () => { isPanning = false; });
    svg.addEventListener('mouseleave', () => { isPanning = false; });

    svg.addEventListener('wheel', (e) => {
      e.preventDefault();
      let zoomFactor = 1.05;
      let sign = Math.sign(e.deltaY);
      let zoom = sign > 0 ? zoomFactor : 1/zoomFactor;
      
      let mx = e.offsetX * (viewBox.w / svg.clientWidth);
      let my = e.offsetY * (viewBox.h / svg.clientHeight);
      
      viewBox.x = viewBox.x + mx - mx * zoom;
      viewBox.y = viewBox.y + my - my * zoom;
      viewBox.w *= zoom;
      viewBox.h *= zoom;
      svg.setAttribute('viewBox', `${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`);
    });
  </script>
</body>
</html>
```

## Agent Injection Instructions
1. Inject all node `<g>` elements and connection `<path>` elements into `<g id="graph-group">`.
2. Ensure every node has an `onclick` attribute binding it to `selectNode()` with its respective metadata extracted from the `graphify` knowledge graph.
3. Apply `.flowing-data-edge` (alias `.dynamic-edge`) to in-tier pipeline connections that represent active data flows.
4. **Two-tier layout when a framework dependency exists.** If the target imports a platform/framework package (auto-discovered per `SKILL.md`), render TWO horizontal bands inside one viewBox:
   - **Top band (~200px):** framework modules as `.framework-node` nodes (navy `#1D2D44` + blue `#4D9EFF` border), laid out left→right.
   - **Bottom band:** the target's own pipeline (shifted down by ~200px + gap to clear the top band).
   - Connect them with `.framework-edge` dashed paths carrying `data-from="<framework_node_id>"` / `data-to="<usecase_node_id>"`, stroke colored by subsystem per `visual-spec.md §3b`. These edges start at `opacity:0`.
5. **Edge data attributes are mandatory.** Every `<path>` (static, dynamic, AND framework) must carry `data-from` and `data-to` matching the node `id`s (the `id` passed to `selectNode`, i.e. the part after `node-`). The illuminator selects edges purely by these attributes.
6. Click semantics: clicking a use-case node lights its pipeline neighbours AND its framework deps; clicking a framework node lights every use-case node that imports it (blast radius). Sidebar for a framework node lists its module path + the consumers.
7. **Legend as a collapsible bottom-left bar.** Do NOT place the legend where it overlaps diagram nodes or the sidebar. Render it as a small "LEGEND" pill pinned to the bottom-left corner. On hover, the full legend expands horizontally to the right, revealing three internal vertical blocks:
   - **Framework Tier** — the platform module box (navy + blue border).
   - **Use-Case Tier** — one entry per node shape/color (Standard Logic, AI/LLM Agent, External/API, Storage/DB, Entry Point).
   - **Cross-Tier Edges** — one entry per active subsystem color (a dashed line sample + label). If no framework tier is present this block is omitted.
   The legend CSS must use:
   - `.legend` — `position: absolute; bottom: 12px; left: 12px; display: flex; flex-direction: row; align-items: flex-start`.
   - `.legend-pill` — the always-visible compact tab (small text, dark bg, thin border).
   - `.legend-blocks` — `max-width: 0; opacity: 0; overflow: hidden` with `transition` on max-width/opacity/padding/margin.
   - `.legend:hover .legend-blocks` — `max-width: 800px; opacity: 1; padding: 10px 16px; margin-left: 8px; border-color: #1E293B`.
8. **Zoom controls at top-left.** The zoom (+ / - / reset) buttons are pinned `position: absolute; top: 20px; left: 20px`. This is the natural location above the diagram content — users scan top→bottom.
9. **Font.** Use `font-family: 'JetBrains Mono', monospace` throughout (body, sidebar, legend, all inline styles). Set `font-size: 14px` on `<body>` as the base. SVG node text must use `font-size="13"` (pipeline/agent nodes), `font-size="12"` (DB cylinders), and `font-size="11"` (END terminal). Sidebar: title `19px`, type/label `12px`, value `14px`. Legend: pill `11px`, block titles `10px`.
10. **Framework category group labels** (ORCHESTRATION, LLM, GUARDRAILS, etc.) must be `font-size="13"` bold in their matching subsystem color at `y="42"` — large enough to be legible at a glance, sitting just above their dashed group boxes.
