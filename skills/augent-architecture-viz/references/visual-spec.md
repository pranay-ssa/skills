# Visual Specification

## Spacing Rules

| Constant | Value | Meaning |
|---|---|---|
| SVG width | 2700 | Total horizontal room |
| SVG height | 1200 | Total vertical room |
| Node width | 210 | Per-node block width |
| Node height | 48 | Per-node block height |
| Vertical gap (within column) | 16 | Between nodes in same column |
| Column X step | 280 | Horizontal step between columns |
| Col Start (Routing Lane) | 120 | Left padding before first column |

## Styling Rules

- **Global Font**: `'JetBrains Mono', Consolas, 'Courier New', monospace` for `html,body`
- **Sidebar Legibility**: Base text `13px`, headings `13px`, sub-labels `12px`, tiny UI `11px`. Never use `9px` or `10px`.
- **Node Text Clipping**: Use a true SVG `<clipPath>` for text inside each node, with `textLength` compression.
- **Node Sub-labels**: Display `cls` (e.g., "Agent", "Node", "Router") directly under the main label, smaller font, reduced opacity.
- **Dark Engineering Theme**: `#0B0E14` background, `#131720` surfaces, `#4D9EFF` accent.
- No emojis. No external fonts. No external images.

## Name Shortening

Names longer than ~18 characters MUST be shortened:

| Long name | Short |
|---|---|
| `trigger_classifier` | `trigger_class.` |
| `novelty_classifier` | `novelty_class.` |
| `context_collector` | `context_coll.` |
| `portfolio_mapper` | `portfolio_map.` |
| `InputGuardrail` | `InputGuard` |
| `OutputValidator` | `OutputValid.` |
| `ContentSafetyClient` | `ContentSafety` |
| `SchemaRegistry` | `SchemaReg.` |
| `LangfuseExporter` | `LangfuseExp.` |

## Risk Color Scheme

Apply to every node border + dark fill tint:

| Level | Border color | Fill tint | Use for |
|---|---|---|---|
| God Module | `#F44` | `#2A1010` | NodeExecutor, LLMService, AuGENTAgent, EventBus |
| High Coupling | `#F80` | `#2A1A08` | Orchestrator, GraphBuilder, OutputValidator |
| Ext Dependency | `#FC0` | `#2A2A08` | InputGuard, ContentSafety, AzureOpenAI, LangfuseExp. |
| Extension Pt | `#4F4` | `#0A2A0A` | All use case nodes |
| Stable | `#888` | `#1A1D22` | Config, AgentExecutor, Metrics, SchemaReg. |

## Edge Types

| Type | Color | Style | Use for |
|---|---|---|---|
| Orchestration | `#0BF` | solid 2px | Orchestrator -> GraphBuilder, NodeExecutor -> Agent |
| Guardrail | `#F80` | dashed 6,3 1.8px | InputGuard -> OutputValid -> ContentSafety |
| Data | `#4F4` | dashed 5,3 1.5px | Agent -> LLMService, Agent -> Tool |
| Dependency | `#888` | solid 1.2px | Import / subclass relationships |
| Event | `#F0F` | solid 1.5px | Module -> EventBus |
| Pipeline | `#4D9EFF` | solid 2px | Use case node-to-node flow |

## Port Selection Rules

> Pick the port pair where each node uses the side physically facing the other node.

Three sub-rules in priority order:
1. **Face-to-face** — source uses the port whose face points toward the target; target uses the port whose face points toward the source
2. **Least congested side** — if two port pairs give equal distance, pick the side with fewer existing edges
3. **Natural entry direction** — arrowhead must arrive in line with the port axis

### Port Decision Table

| Situation | From port | To port | Visual result |
|---|---|---|---|
| Same column, source above target | `bottom` | `top` | Straight vertical line downward |
| Same column, source below target (same layer) | `left` | `left` | Left-side arc curves outside column |
| Different columns, horizontal dominant | `right` | `left` | S-curve going sideways |
| Different columns, narrow gap + large dy | `bottom` | `top` | Bottom-to-top S-curve |
| Different columns, vertical dominant | `bottom` | `top` | S-curve going up/down |

**Layer boundary override**: Any connection crossing the framework-to-UC layer boundary flows downward.

## Edge Routing Helpers

| Helper | Ports | When to use |
|---|---|---|
| `smartEdge` | auto | Default. Picks best port pair, applies narrow-gap override. |
| `nodeEdge` | right->left | Explicit horizontal S-curve within same layer. |
| `rtEdge` | right->top | Cross-layer, target is right-and-below source. |
| `leftArc` | left->left | Same-column connections to avoid crossing other vertical lines. |
| `drawEdge(...,'v')` | any->any vertical | Manual vertical-tangent curve when you know exact ports. |
