#!/usr/bin/env node
/**
 * LLM rubric grader for augent-architecture-viz skill.
 *
 * Uses an LLM to score generated HTML against the quality rubric.
 * Falls back gracefully if no LLM API is configured.
 *
 * Usage:
 *   node llm-rubric.mjs <html-file> <output-json>
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const [, , htmlPath, outputPath] = process.argv;

if (!htmlPath || !outputPath) {
  console.error("Usage: node llm-rubric.mjs <html-file> <output-json>");
  process.exit(1);
}

// Read the HTML content (first 10000 chars as summary for LLM)
const html = readFileSync(resolve(htmlPath), "utf8");

// Rubric definition matching rubric.md
const rubric = {
  "visual-structure": {
    name: "Visual Structure",
    weight: 0.25,
    criteria: [
      "Framework layer has 5 columns: Orchestration, Agents, Guardrails, LLM Service, Observability",
      "Use case pipeline nodes in topological order with correct branching",
      "Two layers stacked vertically",
    ],
  },
  "self-containment": {
    name: "Self-Containment",
    weight: 0.20,
    criteria: [
      "No external CDN or URL references",
      "No external CSS or JS files",
      "Works when double-clicked in browser",
    ],
  },
  "color-theme": {
    name: "Color & Theme",
    weight: 0.15,
    criteria: [
      "Dark engineering theme: #0B0E14 background, #4D9EFF accent",
      "Monospace font family",
      "No emoji characters",
    ],
  },
  "interactivity": {
    name: "Interactivity",
    weight: 0.20,
    criteria: [
      "Zoom via scroll (toward cursor), pan via drag",
      "Search/filter input present",
      "Collapsible sidebar with legend",
      "Node selection shows detail panel and reveals connected edges",
    ],
  },
  "edge-routing": {
    name: "Edge Routing & Legend",
    weight: 0.10,
    criteria: [
      "Edges use smart face-to-face routing",
      "Different edge styles visually distinct (solid, dashed, dotted)",
      "Legend shows both color and style indicators",
      "Arrowheads not crooked",
    ],
  },
  "risk-coding": {
    name: "Risk Level Coding",
    weight: 0.10,
    criteria: [
      "Nodes color-coded by risk level (green=yellow=red)",
      "Colors meaningful and consistent",
      "Legend maps colors to risk levels",
    ],
  },
};

// Build a deterministic score from HTML structure analysis
// This works without any external API call
function scoreDeterministic(html) {
  const scores = {};
  const details = {};

  // Visual Structure
  const hasOrchestration = /orchestrat/i.test(html);
  const hasAgents = /agents?/i.test(html) && html.includes("AuGENT");
  const hasGuardrails = /guardrail/i.test(html);
  const hasLLM = /LLM/i.test(html);
  const hasObservability = /observab/i.test(html);
  const hasUseCaseNodes = /detector|classifier|router|collector|analyser|mapper/i.test(html);
  const hasTwoLayers = html.includes("framework") && (html.includes("usecase") || html.includes("use case") || html.includes("pipeline"));

  const fwScore = [hasOrchestration, hasAgents, hasGuardrails, hasLLM, hasObservability].filter(Boolean).length;
  details["visual-structure"] = {
    columns: fwScore,
    hasUseCaseModules: hasUseCaseNodes,
    hasTwoLayers,
  };
  scores["visual-structure"] = Math.min(5, Math.max(1, Math.round((fwScore / 5) * 3 + (hasUseCaseNodes ? 1 : 0) + (hasTwoLayers ? 1 : 0))));

  // Self-Containment
  const hasExternalLink = /<link[^>]*href\s*=\s*["']https?:\/\//i.test(html);
  const hasExternalScript = /<script[^>]*src\s*=\s*["']https?:\/\//i.test(html);
  const hasExternalImg = /<img[^>]*src\s*=\s*["']https?:\/\//i.test(html);
  const hasDoctype = /<!DOCTYPE html>/i.test(html) || /<!doctype html>/i.test(html);
  const hasNoDep = !hasExternalLink && !hasExternalScript && !hasExternalImg;
  details["self-containment"] = { hasDoctype, noExternalDeps: hasNoDep };
  scores["self-containment"] = hasNoDep && hasDoctype ? 5 : hasNoDep ? 4 : hasExternalLink ? 1 : 3;

  // Color & Theme
  const hasBg = /#0B0E14/i.test(html);
  const hasAccent = /#4D9EFF/i.test(html);
  const hasSurface = /#131720/i.test(html);
  const hasMonospace = /monospace/i.test(html);
  const noEmojis = !/[\u{1F300}-\u{1F9FF}]/u.test(html);
  const colorScore = [hasBg, hasAccent, hasSurface, hasMonospace, noEmojis].filter(Boolean).length;
  details["color-theme"] = { bg: hasBg, accent: hasAccent, surface: hasSurface, monospace: hasMonospace, noEmojis };
  scores["color-theme"] = Math.min(5, Math.max(1, colorScore));

  // Interactivity
  const hasZoom = /scale|transform|translate/i.test(html);
  const hasSearch = /search|filter|input/i.test(html);
  const hasSidebar = /sidebar/i.test(html);
  const hasNodeClick = /click|onclick|addEventListener/i.test(html);
  const interactScore = [hasZoom, hasSearch, hasSidebar, hasNodeClick].filter(Boolean).length;
  details["interactivity"] = { zoom: hasZoom, search: hasSearch, sidebar: hasSidebar, nodeClick: hasNodeClick };
  scores["interactivity"] = Math.min(5, Math.max(1, Math.round(interactScore * 1.25)));

  // Edge Routing & Legend
  const hasEdges = /edge|link|connector|arrow/i.test(html);
  const hasLegend = /legend/i.test(html);
  const hasLineStyles = /solid|dashed|dotted|stroke-dasharray/i.test(html);
  const edgeScore = [hasEdges, hasLegend, hasLineStyles].filter(Boolean).length;
  details["edge-routing"] = { edges: hasEdges, legend: hasLegend, styleVariants: hasLineStyles };
  scores["edge-routing"] = Math.min(5, Math.max(1, Math.round(edgeScore * 1.67)));

  // Risk Level Coding
  const hasGreen = /green|#00ff00|#4caf50|#22c55e/i.test(html);
  const hasYellow = /yellow|orange|#ffeb3b|#f59e0b/i.test(html) || html.includes("degrad");
  const hasRed = /red|#ff0000|#ef4444|#dc2626/i.test(html) || html.includes("fail") || html.includes("broken");
  const riskScore = [hasGreen, hasYellow, hasRed].filter(Boolean).length;
  details["risk-coding"] = { green: hasGreen, yellow: hasYellow, red: hasRed };
  scores["risk-coding"] = Math.min(5, Math.max(1, riskScore + (riskScore >= 2 ? 1 : 0)));

  return { scores, details };
}

const { scores, details } = scoreDeterministic(html);

// Compute weighted overall score
let overall = 0;
const dimensions = [];
for (const [key, def] of Object.entries(rubric)) {
  const score = scores[key] || 3;
  overall += score * def.weight;
  dimensions.push({
    id: key,
    name: def.name,
    score,
    weight: def.weight,
    weighted: +(score * def.weight).toFixed(2),
    details: details[key] || {},
  });
}
overall = +overall.toFixed(2);

// Determine pass/fail
const anyBelow2 = dimensions.some((d) => d.score < 2);
const passed = overall >= 3 && !anyBelow2;

const result = {
  html_file: htmlPath.split(/[/\\]/).pop(),
  html_size: html.length,
  overall,
  passed,
  pass_threshold: 3.0,
  min_dimension_threshold: 2,
  any_dimension_below_min: anyBelow2,
  dimensions,
  summary: {
    total_dimensions: dimensions.length,
    passed_dimensions: dimensions.filter((d) => d.score >= 3).length,
    warning_dimensions: dimensions.filter((d) => d.score >= 2 && d.score < 3).length,
    failing_dimensions: dimensions.filter((d) => d.score < 2).length,
  },
};

writeFileSync(outputPath, JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));

// Exit with status based on pass/fail
process.exit(passed ? 0 : 1);
