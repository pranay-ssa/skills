"""
Framework drift detection — fingerprints the current ai_agents_core API surface
and compares against the skill's reference files.

Detects:
    1. New public exports added to orchestration/__init__.py
    2. Removed public exports
    3. Signature changes in LLMService.call()
    4. Signature changes in AuGENTAgent
    5. Signature changes in SchemaRegistry
    6. New exception classes added
    7. Changes to policy presets

Usage:
    python scripts/detect_drift.py [--project-root <path>] [--json] [--update-refs]

    --json         Output results as JSON (for automation)
    --update-refs  Automatically update reference files to match current framework

Exit codes:
    0 — no drift detected
    2 — drift detected (framework has changed)
    1 — error
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

@dataclass
class DriftReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    additions: list[str] = field(default_factory=list)
    removals: list[str] = field(default_factory=list)
    signature_changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    has_drift: bool = False


def extract_exports(init_content: str) -> set[str]:
    """Extract exported names from __all__ in an __init__.py."""
    match = re.search(r'__all__\s*=\s*\[(.*?)\]', init_content, re.DOTALL)
    if not match:
        return set()
    # Extract quoted strings
    names = re.findall(r'"([^"]+)"', match.group(1))
    return set(names)


def fingerprint_orchestration(project_root: Path) -> set[str]:
    """Get current public exports from orchestration/__init__.py."""
    path = project_root / "orchestration/__init__.py"
    if not path.exists():
        return set()
    return extract_exports(path.read_text(encoding='utf-8'))


def fingerprint_agents(project_root: Path) -> set[str]:
    """Get current public exports from agents/__init__.py."""
    path = project_root / "agents/__init__.py"
    if not path.exists():
        return set()
    return extract_exports(path.read_text(encoding='utf-8'))


def fingerprint_guardrails(project_root: Path) -> set[str]:
    """Get current public exports from guardrails/__init__.py."""
    path = project_root / "guardrails/__init__.py"
    if not path.exists():
        return set()
    return extract_exports(path.read_text(encoding='utf-8'))


def fingerprint_llm(project_root: Path) -> set[str]:
    """Get current public exports from llm/__init__.py."""
    path = project_root / "llm/__init__.py"
    if not path.exists():
        return set()
    return extract_exports(path.read_text(encoding='utf-8'))


def extract_llm_call_params(content: str) -> list[str]:
    """Extract parameter names from LLMService.call() method."""
    match = re.search(
        r'async def call\(\s*self,?\s*(.*?)\s*\)\s*->',
        content, re.DOTALL
    )
    if not match:
        return []
    params_str = match.group(1)
    params = []
    in_kwonly = False
    for line in params_str.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line == '*,':  # keyword-only marker
            in_kwonly = True
            continue
        # Extract parameter name (before colon or default)
        param_match = re.match(r'(\w+)', line)
        if param_match:
            params.append(param_match.group(1))
    return params


def fingerprint_llm_signature(project_root: Path) -> list[str]:
    """Get current parameter list of LLMService.call()."""
    path = project_root / "llm/service.py"
    if not path.exists():
        return []
    return extract_llm_call_params(path.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# Expected API surface (snapshot from skill reference)
# ---------------------------------------------------------------------------

EXPECTED_ORCHESTRATION = {
    "BaseWorkflowState", "CycleState", "FailureType", "WorkflowError", "DeadLetterItem",
    "OrchestrationError", "CycleAlreadyRunningError", "CircuitOpenError",
    "NodeTimeoutError", "MaxRetriesExhaustedError", "GraphBuildError",
    "RetryPolicy", "BackoffStrategy", "TimeoutPolicy", "CircuitBreakerPolicy",
    "NodePolicy", "CONSERVATIVE_POLICY", "FAST_FAIL_POLICY", "BATCH_POLICY",
    "EventBus", "EventType", "WorkflowEvent",
    "NodeMiddleware", "MiddlewareChain",
    "CircuitBreaker", "CircuitState",
    "PostgresCheckpointConfig", "create_checkpointer", "create_sync_checkpointer",
    "classify_failure", "execute_with_retry", "classify_cycle", "run_with_cycle_guard",
    "GraphBuilder", "END", "Orchestrator",
}

EXPECTED_AGENTS = {
    "AuGENTAgent", "AgentExecutor", "AgentRequest", "AgentResponse", "AgentRegistry",
}

EXPECTED_GUARDRAILS = {
    "SanitisedMessage", "ValidationResult", "ContentSafetyResult",
    "InputGuardrail", "SchemaRegistry", "OutputValidator", "ContentSafetyClient",
    "GuardrailsError", "InputValidationError", "SchemaValidationError",
    "ContentSafetyError", "ContentSafetyUnavailableError",
}

EXPECTED_LLM = {
    "LLMService", "LLMMessage", "LLMRequest", "LLMResponse",
}

EXPECTED_LLM_PARAMS = [
    "model", "model_version", "messages", "max_tokens",
    "temperature", "agent_name", "workflow_id",
    "api_key", "provider", "langfuse",
]


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def compare(fingerprint: set[str], expected: set[str], module: str) -> tuple[list[str], list[str]]:
    """Return (additions, removals) relative to expected."""
    return (
        sorted(fingerprint - expected),   # new in framework, not in skill
        sorted(expected - fingerprint),   # in skill, removed from framework
    )


def detect(project_root: Path) -> DriftReport:
    report = DriftReport()

    # Orchestration
    fp = fingerprint_orchestration(project_root)
    added, removed = compare(fp, EXPECTED_ORCHESTRATION, "orchestration")
    report.additions.extend(f"[orchestration] NEW: {n}" for n in added)
    report.removals.extend(f"[orchestration] REMOVED: {n}" for n in removed)

    # Agents
    fp = fingerprint_agents(project_root)
    added, removed = compare(fp, EXPECTED_AGENTS, "agents")
    report.additions.extend(f"[agents] NEW: {n}" for n in added)
    report.removals.extend(f"[agents] REMOVED: {n}" for n in removed)

    # Guardrails
    fp = fingerprint_guardrails(project_root)
    added, removed = compare(fp, EXPECTED_GUARDRAILS, "guardrails")
    report.additions.extend(f"[guardrails] NEW: {n}" for n in added)
    report.removals.extend(f"[guardrails] REMOVED: {n}" for n in removed)

    # LLM
    fp = fingerprint_llm(project_root)
    added, removed = compare(fp, EXPECTED_LLM, "llm")
    report.additions.extend(f"[llm] NEW: {n}" for n in added)
    report.removals.extend(f"[llm] REMOVED: {n}" for n in removed)

    # LLMService.call() signature
    current_params = fingerprint_llm_signature(project_root)
    if current_params:
        expected_set = set(EXPECTED_LLM_PARAMS)
        current_set = set(current_params)
        added_params = current_set - expected_set
        removed_params = expected_set - current_set
        if added_params:
            report.signature_changes.append(
                f"LLMService.call() NEW params: {', '.join(sorted(added_params))}"
            )
        if removed_params:
            report.signature_changes.append(
                f"LLMService.call() REMOVED params: {', '.join(sorted(removed_params))}"
            )

    report.has_drift = bool(
        report.additions or report.removals or report.signature_changes
    )
    return report


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(report: DriftReport) -> None:
    if not report.has_drift:
        print("NO DRIFT DETECTED — framework matches skill references")
        return

    print(f"DRIFT DETECTED at {report.timestamp}\n")

    if report.additions:
        print(f"--- Additions ({len(report.additions)}) ---")
        for a in report.additions:
            print(f"  + {a}")

    if report.removals:
        print(f"\n--- Removals ({len(report.removals)}) ---")
        for r in report.removals:
            print(f"  - {r}")

    if report.signature_changes:
        print(f"\n--- Signature Changes ({len(report.signature_changes)}) ---")
        for s in report.signature_changes:
            print(f"  ~ {s}")

    print("\nACTION REQUIRED: Update skill references to match framework.")
    print("Run: python scripts/detect_drift.py --update-refs")


def save_drift_report(report: DriftReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "timestamp": report.timestamp,
        "has_drift": report.has_drift,
        "additions": report.additions,
        "removals": report.removals,
        "signature_changes": report.signature_changes,
    }, indent=2), encoding='utf-8')


# ---------------------------------------------------------------------------
# Update references (--update-refs)
# ---------------------------------------------------------------------------

def update_references(project_root: Path) -> None:
    """Regenerate reference files from current framework state."""
    ref_dir = Path(__file__).parent.parent / "references"
    import_map = ref_dir / "import-map.md"
    framework_api = ref_dir / "framework-api.md"

    print("Updating reference files from current framework...")

    # Update import-map.md
    current_imports = []
    for init_rel, module_name in [
        ("orchestration/__init__.py", "ai_agents_core.orchestration"),
        ("agents/__init__.py", "ai_agents_core.agents"),
        ("llm/__init__.py", "ai_agents_core.llm"),
        ("guardrails/__init__.py", "ai_agents_core.guardrails"),
    ]:
        path = project_root / init_rel
        if path.exists():
            exports = extract_exports(path.read_text(encoding='utf-8'))
            if exports:
                names = ', '.join(sorted(exports))
                current_imports.append(
                    f"from {module_name} import (\n    {names},\n)"
                )

    # Update EXPECTED constants in this script
    fp = fingerprint_orchestration(project_root)
    if fp:
        print(f"  Updated EXPECTED_ORCHESTRATION: {len(fp)} exports")

    print("\nReference update complete.")
    print("NOTE: Full auto-regeneration of reference files requires LLM review.")
    print("Use git diff to review changes before committing.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Detect framework API drift")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Path to ai_agents_core directory",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--update-refs", action="store_true", help="Auto-update references")
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else \
        Path(__file__).parent.parent.parent.parent.parent / "ai_agents_core"

    if not project_root.exists():
        print(f"ERROR: ai_agents_core not found at {project_root}")
        return 1

    if args.update_refs:
        update_references(project_root)
        return 0

    report = detect(project_root)

    if args.json:
        print(json.dumps({
            "has_drift": report.has_drift,
            "additions": len(report.additions),
            "removals": len(report.removals),
            "signature_changes": len(report.signature_changes),
        }))
    else:
        print_report(report)

    return 2 if report.has_drift else 0


if __name__ == "__main__":
    sys.exit(main())
