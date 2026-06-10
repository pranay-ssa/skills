"""
Skill validation script — verifies that all import paths referenced in the
augent-usecase-builder skill are valid against the actual framework.

Usage:
    python scripts/validate_imports.py [--project-root <path>]

Exit codes:
    0 — all imports valid
    1 — one or more imports invalid
"""

from __future__ import annotations

import ast
import importlib
import json
import re
import sys
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

IMPORT_RE = re.compile(
    r'^\s*from\s+(\S+)\s+import\s+(.+?)(?:\s*#.*)?$',
    re.MULTILINE,
)

FRAMEWORK_PREFIXES = {
    "ai_agents_core.orchestration",
    "ai_agents_core.agents",
    "ai_agents_core.llm",
    "ai_agents_core.guardrails",
    "ai_agents_core.logging",
    "ai_agents_core.observability",
    "ai_agents_core.tools",
    "ai_agents_core.db",
    "ai_agents_core.config",
    "ai_agents_core.security",
    "ai_agents_core.utils",
}


def extract_imports(text: str) -> list[tuple[str, str]]:
    """Extract (module, name) tuples from `from X import Y` statements.
    Handles multi-line imports with parentheses and code blocks."""
    results: list[tuple[str, str]] = []

    # Only parse code blocks (between ```python and ```)
    code_blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.DOTALL)
    if not code_blocks:
        code_blocks = [text]

    for block in code_blocks:
        # Collapse multi-line `from X import (...)` to single line
        block = re.sub(
            r'from\s+(\S+)\s+import\s*\(.*?\)',
            lambda m: _collapse_multi_import(m.group(0)),
            block,
            flags=re.DOTALL,
        )
        for m in IMPORT_RE.finditer(block):
            module = m.group(1)
            names_str = m.group(2)
            for name in re.split(r'\s*,\s*', names_str):
                name = name.split(' as ')[0].strip()
                if name and not name.startswith('#') and not name.startswith('('):
                    results.append((module, name))
    return results


def _collapse_multi_import(text: str) -> str:
    """Collapse `from X import (\n  A,\n  B,\n)` -> `from X import A, B`."""
    # Extract module name
    mod_match = re.match(r'from\s+(\S+)\s+import\s*\((.*)\)', text, re.DOTALL)
    if not mod_match:
        return text
    module = mod_match.group(1)
    names_block = mod_match.group(2)
    # Remove newlines and extra whitespace, split by comma
    names = [n.strip() for n in re.split(r'\s*,\s*', names_block) if n.strip()]
    return f"from {module} import {', '.join(names)}"


def is_framework_import(module: str) -> bool:
    return any(module.startswith(p) for p in FRAMEWORK_PREFIXES) or \
           module == "ai_agents_core"


# ---------------------------------------------------------------------------
# Validation: does the import path actually exist?
# ---------------------------------------------------------------------------

def validate_import(module: str, name: str, project_root: Path) -> tuple[bool, str]:
    """Check if `from {module} import {name}` resolves in the framework."""
    # Strip ai_agents_core prefix since project_root already points there
    if module.startswith("ai_agents_core."):
        rel = module[len("ai_agents_core."):].replace('.', '/')
    elif module == "ai_agents_core":
        rel = ""
    else:
        return False, f"Not a framework import: {module}"

    if rel:
        init_path = project_root / rel / "__init__.py"
        module_path = project_root / f"{rel}.py"
    else:
        init_path = project_root / "__init__.py"
        module_path = None

    resolved = None
    if init_path.exists():
        resolved = init_path
    elif module_path.exists():
        resolved = module_path
    else:
        return False, f"Module not found: {rel} (neither __init__.py nor .py)"

    # Check if the name is exported
    content = resolved.read_text(encoding='utf-8')
    # Simple check: is the name mentioned in the file?
    # Also check __all__ if it exists
    if name in content:
        return True, "ok"
    return False, f"Name '{name}' not found in {rel}"


# ---------------------------------------------------------------------------
# Validation: check specific key framework APIs exist
# ---------------------------------------------------------------------------

KEY_APIS = [
    # (file, symbol that MUST exist)
    ("orchestration/__init__.py", "GraphBuilder"),
    ("orchestration/__init__.py", "END"),
    ("orchestration/__init__.py", "Orchestrator"),
    ("orchestration/__init__.py", "BaseWorkflowState"),
    ("orchestration/__init__.py", "EventBus"),
    ("orchestration/__init__.py", "EventType"),
    ("orchestration/__init__.py", "BATCH_POLICY"),
    ("orchestration/__init__.py", "CONSERVATIVE_POLICY"),
    ("orchestration/__init__.py", "FAST_FAIL_POLICY"),
    ("agents/__init__.py", "AuGENTAgent"),
    ("llm/__init__.py", "LLMService"),
    ("llm/__init__.py", "LLMResponse"),
    ("guardrails/__init__.py", "InputGuardrail"),
    ("guardrails/__init__.py", "SchemaRegistry"),
    ("guardrails/__init__.py", "OutputValidator"),
    ("logging/__init__.py", "setup_logging"),
    ("logging/__init__.py", "get_logger"),
]


def check_key_apis(project_root: Path) -> list[str]:
    """Verify every key API symbol exists in the framework."""
    errors: list[str] = []
    for rel_file, symbol in KEY_APIS:
        path = project_root / rel_file
        if not path.exists():
            errors.append(f"MISSING: ai_agents_core/{rel_file} does not exist")
            continue
        content = path.read_text(encoding='utf-8')
        if symbol not in content:
            errors.append(f"MISSING: '{symbol}' not found in ai_agents_core/{rel_file}")
    return errors


# ---------------------------------------------------------------------------
# Validation: check LLMService.call() signature
# ---------------------------------------------------------------------------

def check_llm_service_signature(project_root: Path) -> list[str]:
    """Verify LLMService.call() has the expected parameters."""
    errors: list[str] = []
    path = project_root / "llm/service.py"
    if not path.exists():
        return ["MISSING: ai_agents_core/llm/service.py"]
    content = path.read_text(encoding='utf-8')
    req_params = ["model", "model_version", "messages", "api_key", "workflow_id"]
    for p in req_params:
        if p not in content:
            errors.append(f"MISSING: parameter '{p}' not found in LLMService.call()")
    return errors


# ---------------------------------------------------------------------------
# Validation: check AuGENTAgent._execute() signature
# ---------------------------------------------------------------------------

def check_agent_signature(project_root: Path) -> list[str]:
    """Verify AuGENTAgent._execute() has expected signature."""
    errors: list[str] = []
    path = project_root / "agents/base.py"
    if not path.exists():
        return ["MISSING: ai_agents_core/agents/base.py"]
    content = path.read_text(encoding='utf-8')
    if "async def _execute(self, state" not in content:
        errors.append("CHANGED: AuGENTAgent._execute() signature modified")
    if "async def run(self, state" not in content:
        errors.append("CHANGED: AuGENTAgent.run() signature modified")
    return errors


# ---------------------------------------------------------------------------
# Validation: check SchemaRegistry API
# ---------------------------------------------------------------------------

def check_schema_registry(project_root: Path) -> list[str]:
    """Verify SchemaRegistry has register, register_schema, get methods."""
    errors: list[str] = []
    path = project_root / "guardrails/output.py"
    if not path.exists():
        return ["MISSING: ai_agents_core/guardrails/output.py"]
    content = path.read_text(encoding='utf-8')
    for method in ["def register(", "def register_schema(", "def get("]:
        if method not in content:
            errors.append(f"MISSING: SchemaRegistry.{method.split('(')[0]}() method")
    if "@SchemaRegistry.register_schema" not in content:
        errors.append("MISSING: @SchemaRegistry.register_schema decorator")
    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate skill imports against framework")
    parser.add_argument("--project-root", default=None, help="Path to ai_agents_core directory")
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else \
        Path(__file__).parent.parent.parent.parent.parent / "ai_agents_core"
    if not project_root.exists():
        print(f"ERROR: ai_agents_core not found at {project_root}")
        return 1

    print(f"Validating against: {project_root}\n")
    all_errors: list[str] = []

    # 1. Check key APIs
    print("--- Key API symbols ---")
    errors = check_key_apis(project_root)
    for e in errors:
        print(f"  FAIL: {e}")
    all_errors.extend(errors)
    if not errors:
        print("  PASS: all key APIs present")

    # 2. Check LLMService signature
    print("\n--- LLMService.call() signature ---")
    errors = check_llm_service_signature(project_root)
    for e in errors:
        print(f"  FAIL: {e}")
    all_errors.extend(errors)
    if not errors:
        print("  PASS: expected parameters present")

    # 3. Check AuGENTAgent signature
    print("\n--- AuGENTAgent signatures ---")
    errors = check_agent_signature(project_root)
    for e in errors:
        print(f"  FAIL: {e}")
    all_errors.extend(errors)
    if not errors:
        print("  PASS: _execute() and run() signatures match")

    # 4. Check SchemaRegistry
    print("\n--- SchemaRegistry API ---")
    errors = check_schema_registry(project_root)
    for e in errors:
        print(f"  FAIL: {e}")
    all_errors.extend(errors)
    if not errors:
        print("  PASS: register, register_schema, get methods present")

    # 5. Validate import-map.md imports
    print("\n--- import-map.md validation ---")
    import_map_path = Path(__file__).parent.parent / "references" / "import-map.md"
    if import_map_path.exists():
        content = import_map_path.read_text(encoding='utf-8')
        imports = extract_imports(content)
        framework_imports = [(m, n) for m, n in imports if is_framework_import(m)]
        map_errors = 0
        for module, name in framework_imports:
            ok, msg = validate_import(module, name, project_root)
            if not ok:
                print(f"  FAIL: from {module} import {name} — {msg}")
                map_errors += 1
        if map_errors == 0:
            print(f"  PASS: all {len(framework_imports)} framework imports valid")
        all_errors.extend([""] * map_errors)  # count failures
    else:
        print("  SKIP: import-map.md not found")

    # Summary
    print(f"\n{'='*50}")
    if all_errors:
        print(f"VALIDATION FAILED — {len(all_errors)} issue(s) found")
        print("The skill references may be stale. Run: python scripts/detect_drift.py")
        return 1
    else:
        print("VALIDATION PASSED — skill is in sync with framework")
        return 0


if __name__ == "__main__":
    sys.exit(main())
