"""Deterministic HTML output checker for the augent-architecture-viz skill.

Usage:
  python scripts/grade_viz.py <path-to-output.html> [--assertions <path-to-assertions.json>]

Returns JSON grading results to stdout:
  {"passed": 3, "failed": 1, "results": [...]}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def check_self_contained(html: str) -> dict:
    """Check no external CDN/URL references."""
    patterns = [
        (r'<link[^>]+href\s*=\s*["\']https?://', "No external <link> with http(s):// href"),
        (r'<script[^>]+src\s*=\s*["\']https?://', "No external <script> with http(s):// src"),
        (r'<img[^>]+src\s*=\s*["\']https?://', "No external <img> with http(s):// src"),
        (r'<iframe', "No iframe elements"),
        (r'<embed', "No embed elements"),
        (r'<object', "No object elements"),
    ]
    results = []
    for pattern, desc in patterns:
        passed = not re.search(pattern, html, re.IGNORECASE)
        results.append({"assertion": desc, "passed": passed})
    return {"group": "self-contained", "results": results}


def check_svg_structure(html: str) -> dict:
    """Check SVG element with correct dimensions."""
    results = []
    # SVG element present
    has_svg = bool(re.search(r'<svg[^>]*>', html, re.IGNORECASE))
    results.append({"assertion": "Contains SVG element", "passed": has_svg})

    # Correct viewBox dimensions
    viewbox_match = re.search(r'viewBox\s*=\s*["\']0\s+0\s+2700\s+1200["\']', html)
    results.append({
        "assertion": 'SVG has viewBox="0 0 2700 1200"',
        "passed": bool(viewbox_match),
    })

    # Has width/height attributes (not just viewBox)
    width_match = re.search(r'<svg[^>]*width\s*=\s*["\']\d+', html, re.IGNORECASE)
    height_match = re.search(r'<svg[^>]*height\s*=\s*["\']\d+', html, re.IGNORECASE)
    results.append({
        "assertion": "SVG has explicit width and height attributes",
        "passed": bool(width_match and height_match),
    })

    # Has <defs> with markers
    has_defs = bool(re.search(r'<defs>', html))
    results.append({"assertion": "SVG contains <defs> element", "passed": has_defs})

    # Has grid pattern
    has_grid = bool(re.search(r'<pattern[^>]*id\s*=\s*["\']grid["\']', html))
    results.append({"assertion": "SVG contains grid pattern", "passed": has_grid})

    return {"group": "svg-structure", "results": results}


def check_dark_theme(html: str) -> dict:
    """Check dark engineering theme colors."""
    results = []
    # Background color
    has_bg = bool(re.search(r'#[0O]B[0O]E14', html, re.IGNORECASE))
    results.append({
        "assertion": "Uses dark background #0B0E14",
        "passed": has_bg,
    })
    # Surface color
    has_surface = bool(re.search(r'#131720', html))
    results.append({
        "assertion": "Uses surface color #131720",
        "passed": has_surface,
    })
    # Accent color
    has_accent = bool(re.search(r'#4D9EFF', html))
    results.append({
        "assertion": "Uses accent color #4D9EFF",
        "passed": has_accent,
    })
    # Monospace font
    font_set = "JetBrains Mono" in html or "monospace" in html.lower()
    results.append({
        "assertion": "Uses monospace font family",
        "passed": font_set,
    })
    return {"group": "dark-theme", "results": results}


def check_framework_nodes(html: str) -> dict:
    """Check required framework module names are present."""
    required = [
        "Orchestrator",
        "GraphBuilder",
        "NodeExecutor",
        "AuGENTAgent",
        "AgentExecutor",
        "LLMService",
        "EventBus",
    ]
    results = []
    for name in required:
        # Check in text content of SVG (tspan, text, or id attributes)
        found = name.lower() in html.lower()
        results.append({
            "assertion": f"Framework node '{name}' present",
            "passed": found,
        })
    return {"group": "framework-nodes", "results": results}


def check_usecase2_nodes(html: str) -> dict:
    """Check default usecase2 pipeline nodes (when applicable)."""
    required = [
        "event_detector",
        "trigger_class",
        "novelty_class",
        "orch_router",
        "context_coll",
        "analyser",
        "portfolio_map",
        "summary_agent",
        "distributor",
    ]
    results = []
    for name in required:
        found = name.lower() in html.lower()
        results.append({
            "assertion": f"Use case node '{name}' present",
            "passed": found,
        })
    return {"group": "usecase-nodes", "results": results}


def check_interactivity(html: str) -> dict:
    """Check interactive JavaScript elements."""
    results = []
    # Has script block
    has_script = bool(re.search(r'<script[^>]*>', html))
    results.append({
        "assertion": "Contains JavaScript <script> block",
        "passed": has_script,
    })
    # Zoom/pan functionality
    has_zoom = "scale" in html and ("transform" in html or "translate" in html)
    results.append({
        "assertion": "Contains zoom/pan javascript logic",
        "passed": has_zoom,
    })
    # Search box
    has_search = "search" in html.lower() and "input" in html.lower()
    results.append({
        "assertion": "Contains search/filter input",
        "passed": has_search,
    })
    # Sidebar
    has_sidebar = "sidebar" in html.lower()
    results.append({
        "assertion": "Contains sidebar element",
        "passed": has_sidebar,
    })
    return {"group": "interactivity", "results": results}


def check_no_emojis(html: str) -> dict:
    """Check no emoji characters (excluding UI symbols like trigrams, arrows)."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U00002702-\U000027BF"  # dingbats (narrower range, excludes misc)
        "\U000024C2-\U000024C2"  # circled M only
        "]+",
        re.UNICODE,
    )
    has_emojis = bool(emoji_pattern.search(html))
    return {
        "group": "no-emojis",
        "results": [
            {"assertion": "No emoji characters in HTML", "passed": not has_emojis}
        ],
    }


def check_inline_css_js(html: str) -> dict:
    """Check CSS and JS are inline (no external files)."""
    results = []
    has_style = bool(re.search(r'<style[^>]*>', html))
    results.append({
        "assertion": "Contains inline <style> block",
        "passed": has_style,
    })
    no_external_css = not re.search(r'<link[^>]+rel\s*=\s*["\']stylesheet["\']', html)
    results.append({
        "assertion": "No external CSS stylesheets",
        "passed": no_external_css,
    })
    no_external_js = not re.search(
        r'<script[^>]+src\s*=\s*["\']', html
    )
    results.append({
        "assertion": "No external JavaScript files",
        "passed": no_external_js,
    })
    return {"group": "inline-css-js", "results": results}


ALL_CHECKS = [
    check_self_contained,
    check_svg_structure,
    check_dark_theme,
    check_inline_css_js,
    check_no_emojis,
    check_interactivity,
    check_framework_nodes,
    check_usecase2_nodes,
]


def grade_html(filepath: str) -> dict:
    """Run all checks against an HTML file."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}", "passed": 0, "failed": 0, "total": 0, "results": []}

    html = path.read_text(encoding="utf-8")
    all_results = []
    passed = 0
    failed = 0

    for check_fn in ALL_CHECKS:
        group = check_fn(html)
        all_results.append(group)
        for r in group["results"]:
            if r["passed"]:
                passed += 1
            else:
                failed += 1

    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "pass_rate": round(passed / (passed + failed) * 100, 1) if (passed + failed) > 0 else 0,
        "results": all_results,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python grade_viz.py <html-file>"}))
        sys.exit(1)

    result = grade_html(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("failed", 0) == 0 else 1)
