# AuGENT Architecture Viz Quality Rubric

Grade each dimension on a 1-5 scale.

## Visual Structure

| Score | Criteria |
|-------|----------|
| 5 | Framework layer shows all 5 columns (Orchestration, Agents, Guardrails, LLM Service, Observability) with correct modules. Use case pipeline in topological order with correct branching. Both layers stacked vertically. |
| 3 | Framework or use case layer present but missing some columns or incorrect node ordering. |
| 1 | Only one layer present. Missing major modules. Wrong visual arrangement. |

## Self-Containment

| Score | Criteria |
|-------|----------|
| 5 | Fully self-contained HTML. No external CDN/URL references. No `<link>` or `<script src>`. No external images. Works when double-clicked. |
| 3 | Mostly self-contained but has minor external references. |
| 1 | Depends on CDN, external resources, or requires a server. |

## Color & Theme

| Score | Criteria |
|-------|----------|
| 5 | Dark engineering theme applied consistently: `#0B0E14` background, `#131720` surfaces, `#4D9EFF` accent. Monospace font. No emojis. |
| 3 | Dark theme present but colors not matching spec or minor color inconsistencies. |
| 1 | Wrong theme (light mode, wrong colors, or missing theme entirely). |

## Interactivity

| Score | Criteria |
|-------|----------|
| 5 | Zoom via scroll (toward cursor), pan via drag. Search/filter input functional. Collapsible sidebar with legend + detail panel. Node selection reveals connected edges. |
| 3 | Some interactivity present but missing key features (search, sidebar, edge visibility). |
| 1 | No interactivity. Static image or non-functional controls. |

## Edge Routing & Legend

| Score | Criteria |
|-------|----------|
| 5 | Edges use smart routing with face-to-face ports. Different edge styles (solid, dashed, dotted) visually distinct. Legend shows both color and style indicators (badges). Arrowheads are not crooked. |
| 3 | Edges present but basic routing or missing style differentiation. Legend shows colors but not styles. |
| 1 | Crooked arrowheads. No legend. Edge styles indistinguishable. |

## Risk Level Coding

| Score | Criteria |
|-------|----------|
| 5 | Nodes color-coded by risk level (green=stable, yellow=degraded, red=experimental/broken). Colors meaningful and consistent across layers. Legend maps colors to risk levels. |
| 3 | Risk colors present but inconsistent or missing some levels. |
| 1 | No risk-level color coding on nodes. |

## Pass Criteria
- Overall score >= 3
- No individual dimension below 2
- Self-Containment must be >= 3 (HTML must work offline)
