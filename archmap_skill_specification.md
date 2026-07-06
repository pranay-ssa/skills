# Blueprint & Technical Specification: Autonomous Architecture Visualizer (ArchMap)

This comprehensive technical blueprint consolidates all decoded insights, system mechanics, UX quirks, and implementation strategies required to build an automated, interactive GitHub repository data-flow visualizer.

---

## 1. Core Vision & Functional Overview
The application (**ArchMap**) accepts a public or private GitHub repository URL and automatically parses, analyzes, and visualizes how data chronologically moves through the ecosystem. 

Unlike traditional visualizers that merely render a static directory file-tree structure, this system focuses entirely on **dynamic data tracking**—tracing input entry points, middleware transformations, and system outputs.

### Comprehensive System Prompt
To build or generate this skill within an AI agent or code-generation framework, use the following comprehensive prompt:

```text
Build a web application called ArchMap that takes a GitHub repository URL and visualizes its architecture and data-flow paths.

Backend Specifications:
1. Create a secure endpoint accepting a GitHub repository URL.
2. Implement a lightweight ingestion pipeline that fetches the repository's file structure and isolates critical configuration/entry files (e.g., package.json, requirements.txt, route controllers).
3. Send this isolated structural context to an LLM (e.g., Claude 3.5 Sonnet) instructing it to trace the data pipeline.
4. Enforce a strict structured output format containing valid Mermaid.js flowchart code alongside brief architectural metadata for discovered components.

Frontend Specifications:
1. Build a sleek landing page featuring a prominent central input field for the GitHub repository URL.
2. Include an informative loading sequence demonstrating progress updates (e.g., "Cloning Repo...", "Analyzing Codebase Flow...").
3. Implement a split-screen workspace dashboard:
   - Left Panel: An interactive canvas rendering zoomable, pannable diagrams driven by the generated Mermaid.js code.
   - Right Panel: A context-sensitive sidebar that updates with granular module information, specific file paths, and system descriptions when a user clicks any diagram node.
4. Provide immediate actionable utility buttons: "Export as PNG" and "Copy Mermaid Code" with automatic clipboard confirmations.
```

---

## 2. End-to-End System Architecture

The application pipeline operates through four discrete processing layers:

```
[GitHub Repository URL]
         │
         ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 1. Ingestion & Filtering Layer                          │
 │    • Pulls file trees via GitHub API / shallow clone    │
 │    • Discards non-essential assets                      │
 └───────────────────────┬─────────────────────────────────┘
                         │
                         ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 2. LLM Processing & Inference Layer                     │
 │    • Evaluates data entry points & dependencies         │
 │    • Evaluates data transformation handlers             │
 └───────────────────────┬─────────────────────────────────┘
                         │
                         ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 3. Translation Layer (Text-to-Diagram Syntax)           │
 │    • Converts code insights into structural string data │
 │    • Outputs Markdown-compatible Mermaid.js syntax      │
 └───────────────────────┬─────────────────────────────────┘
                         │
                         ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 4. UI Canvas Rendering Layer                             │
 │    • Generates interactive, zoomable workspace nodes     │
 │    • Injects CSS stroke animation to visualize movement  │
 └─────────────────────────────────────────────────────────┘
```

### Layer Details:
1. **Ingestion & Filtering Layer:** Avoids token overflow and excessive API costs by skipping asset files (images, SVGs, style sheets). It isolates configurations, routing manifests, and major functional controllers to map out the application's skeletal framework.
2. **LLM Inference Layer:** Instructs the language model to trace data step-by-step:
   * **Entry Points:** API routes, local file readers, hardware inputs, WebSockets.
   * **Processing Layers:** Middleware filters, authentication gates, normalizers, parsers.
   * **Storage/Exit Points:** Database integrations, cloud object storage, external API webhooks, or final frontend state frames.
3. **Translation Layer:** Restricts LLM output to clean string-based flowcharts (`graph LR` or `graph TD`), eliminating the need for complex, native image rendering computations on the server.
4. **UI Canvas Layer:** Injects the flowchart string directly into a browser-based parser (such as `mermaid.js` or `react-flow`) to draw the vector network natively.

---

## 3. Advanced UX Quirks & Interactive Mechanics

To replicate the premium, responsive feel observed in high-end platform implementations (such as Emergent), incorporate these four key UI mechanics:

### I. Dynamic Data-Flow Animations (The "Moving Arrows" Effect)
Connections between architectural nodes must not remain static. True data velocity is simulated by running continuous animated pulses along connection paths. This is achieved via **SVG Dash Array Manipulation**.

#### Implementation Strategy:
When the frontend component renders the diagram, it targets the generated SVG path links and shifts their dash offsets via a continuous CSS linear animation loop.

* **CSS Architecture:**
  ```css
  /* Apply this class to your canvas connectors or Mermaid link styles */
  .flowing-data-edge {
    stroke-dasharray: 10 10;                /* 10px dash line, 10px whitespace gap */
    animation: dataFlow 0.8s linear infinite; /* Drives continuous progression */
  }

  @keyframes dataFlow {
    from {
      stroke-dashoffset: 20;
    }
    to {
      stroke-dashoffset: 0;
    }
  }
  ```

### II. Contextual Color-Coding & Shape Hierarchies
Nodes are stylized to visually indicate their exact operational tier within seconds:
* **Blue / Slate Nodes:** Standard system files, local script components, and processing scripts.
* **Green / Teal Accents:** External integrations, public APIs, or remote Content Delivery Networks (CDNs).
* **Cylinder Geometry:** Exclusively reserved for data persistence layers, local storage systems, database targets, or disk drives.

### III. Perspective Workspace Depth
To eliminate flat web layouts, the background matrix uses a subtle parallax blueprint grid. As users hover or navigate across the canvas workspace, a low-intensity 3D perspective translation shifts the grid alignment to add spatial depth.

### IV. One-Click Documentation Loop
Once rendering completes, present a highly visible notification banner stating: `✓ Mermaid copied — paste into your README`. This streamlines the development cycle, letting engineers instantly bring their production documentation up to date.

---

## 4. Frontend Component Layout & Code Strategy

### Split-Screen Dashboard Layout
Organize your workspace interface using a linear, accessible dual-panel design:

#### 1. Interactive Left Canvas Component
Renders the visual nodes. If utilizing open-source canvas solutions like **React Flow**, map custom edge components directly to the SVG stroke animation logic:
```jsx
export function CustomFlowingEdge({ id, sourceX, sourceY, targetX, targetY }) {
  // Compute linear path coordinates between components
  const edgePath = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`; 
  
  return (
    <path
      id={id}
      className="flowing-data-edge" /* Binds the animation loop */
      d={edgePath}
      fill="none"
      stroke="#4F46E5"               /* Indigo/purple accent data line */
      strokeWidth={3}
    />
  );
}
```

#### 2. Contextual Right Sidebar Component
Listens for click triggers targeting canvas items. Upon selection, the panel dynamically parses the structured metadata object provided by your backend pipeline:
* **Header:** Component Name (e.g., `CookieJar` or `SessionLoader`) paired with an identifier tag (*Service, Module, External API*).
* **File Path Location:** A precise index tracker link (e.g., `src/requests/cookies.py`).
* **Role Summary:** A human-readable text block summarizing the block's programmatic obligations.