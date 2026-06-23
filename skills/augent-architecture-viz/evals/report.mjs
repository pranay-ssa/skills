#!/usr/bin/env node
/**
 * Generates a summary report from eval results.
 *
 * Usage:
 *   node report.mjs <results-dir>
 *
 * Reads all prompt subdirectories, collects deterministic.json and llm-grade.json,
 * and produces summary.json.
 */

import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const [, , resultsDir] = process.argv;

if (!resultsDir) {
  console.error("Usage: node report.mjs <results-dir>");
  process.exit(1);
}

const promptDirs = readdirSync(resultsDir, { withFileTypes: true })
  .filter((d) => d.isDirectory())
  .map((d) => d.name)
  .filter((name) => !name.startsWith("."))
  .sort();

const results = [];

for (const promptId of promptDirs) {
  const promptDir = join(resultsDir, promptId);

  // Read deterministic grader results
  let deterministic = null;
  const detPath = join(promptDir, "deterministic.json");
  if (existsSync(detPath)) {
    try {
      deterministic = JSON.parse(readFileSync(detPath, "utf8"));
    } catch {
      deterministic = { error: "Failed to parse" };
    }
  }

  // Read LLM rubric results
  let llmGrade = null;
  const llmPath = join(promptDir, "llm-grade.json");
  if (existsSync(llmPath)) {
    try {
      llmGrade = JSON.parse(readFileSync(llmPath, "utf8"));
    } catch {
      llmGrade = { error: "Failed to parse" };
    }
  }

  // Check for generated HTML
  const htmlFiles = readdirSync(promptDir).filter(
    (f) => f.endsWith(".html") && !f.startsWith("seed-")
  );

  results.push({
    promptId,
    htmlGenerated: htmlFiles.length > 0,
    htmlFiles,
    deterministic,
    llmGrade,
    passed: deterministic?.passed !== false,
  });
}

// Compute statistics
const total = results.length;
const withHtml = results.filter((r) => r.htmlGenerated).length;
const detPassed = results.filter((r) => r.deterministic?.passed !== false).length;
const llmPassed = results.filter((r) => r.llmGrade?.passed !== false).length;

// Collect LLM scores
const llmScores = results
  .filter((r) => r.llmGrade?.overall != null)
  .map((r) => r.llmGrade.overall);
const avgLlmScore = llmScores.length > 0
  ? +(llmScores.reduce((a, b) => a + b, 0) / llmScores.length).toFixed(2)
  : null;

// Collect deterministic scores
const detScores = results
  .filter((r) => r.deterministic?.score != null)
  .map((r) => r.deterministic.score);
const avgDetScore = detScores.length > 0
  ? +(detScores.reduce((a, b) => a + b, 0) / detScores.length).toFixed(2)
  : null;

const summary = {
  timestamp: resultsDir.split(/[/\\]/).pop(),
  total,
  htmlGenerated: withHtml,
  htmlGenerationRate: total > 0 ? +((withHtml / total) * 100).toFixed(1) : 0,
  deterministicPassed: detPassed,
  llmPassed,
  averageLlmScore: avgLlmScore,
  averageDeterministicScore: avgDetScore,
  results,
};

// Generate a human-readable breakdown
const failedPrompts = results.filter(
  (r) => !r.htmlGenerated || r.deterministic?.failed > 0
);

const reportText = [
  "=".repeat(60),
  "  AuGENT Architecture Viz Skill Eval Summary",
  "=".repeat(60),
  "",
  `  Timestamp:     ${summary.timestamp}`,
  `  Total prompts: ${total}`,
  `  HTML generated: ${withHtml}/${total} (${summary.htmlGenerationRate}%)`,
  `  Det. passed:   ${detPassed}/${total}`,
  `  Avg LLM score: ${avgLlmScore ?? "N/A"}`,
  "",
  ...(failedPrompts.length > 0
    ? [
        "  FAILED PROMPTS:",
        ...failedPrompts.map((r) =>
          [
            `    - ${r.promptId}`,
            r.htmlGenerated ? "" : "      No HTML generated",
            r.deterministic?.failed > 0
              ? `      ${r.deterministic.failed} check(s) failed`
              : "",
          ]
            .filter(Boolean)
            .join("\n")
        ),
        "",
      ]
    : ["  All prompts passed!", ""]),
  "=".repeat(60),
].join("\n");

// Write summary
writeFileSync(
  join(resultsDir, "summary.json"),
  JSON.stringify(summary, null, 2)
);

console.log(reportText);
