#!/usr/bin/env python3
"""Self-review script: reads feedback, analyses routing gaps, generates recommendations."""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import subprocess
import sys

import yaml


def load_feedback(root: Path) -> list[dict]:
    items = []
    for path in sorted(glob.glob(str(root / "feedback" / "*.yaml"))):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if data:
            items.append({"file": str(path), "data": data})
    return items


def analyze_regression_cases(root: Path) -> list[dict]:
    """Check if any feedback item should become a permanent regression case."""
    from regression_v31 import load_kernel_module
    kernel = root.parent / "LOWERTOP-Enterprise-v3.0-RC3"
    regression = load_kernel_module(kernel / "scripts" / "regression.py")
    config = root / "build" / "LOWERTOP-Enterprise-v3.1-RC2-Performance-Direct.conf"
    if not config.exists():
        return [{"error": "config not built yet"}]
    rules, _ = regression.compile_config(config, root / ".cache/remote-rules", online=True)
    suggestions = []
    for item in load_feedback(root):
        data = item["data"]
        domain = next(iter(data.get("domain_or_domains", [])), None)
        if not domain:
            continue
        test_case = {
            "name": f'FEEDBACK-{data.get("feedback_id", "unknown")}',
            "host": domain,
            "expected_policy": data.get("matched_policy", "PROXY"),
        }
        hit = regression.first_match(rules, test_case)
        if hit is None:
            suggestions.append({"feedback": data["feedback_id"], "issue": "no match", "host": domain})
        elif hit.policy != test_case["expected_policy"]:
            suggestions.append({"feedback": data["feedback_id"], "issue": f'routed to {hit.policy} but expected {test_case["expected_policy"]}', "host": domain, "actual_rule": hit.raw})
        elif data.get("auto_analysis", {}).get("routing") == "correct":
            pass  # routing is fine, no regression needed
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Self-review: feedback → analysis → recommendations")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="reports/self-review.json")
    parser.add_argument("--markdown-out", default="reports/self-review.md")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    feedback = load_feedback(root)
    suggestions = analyze_regression_cases(root)
    report = {
        "ok": True,
        "feedback_count": len(feedback),
        "suggestions": suggestions,
        "feedback": [f["data"].get("feedback_id", f["file"]) for f in feedback],
    }
    markdown = f"""# Self-Review Report

- Feedback entries: {len(feedback)}
- Suggestions: {len(suggestions)}

## Suggestions

"""
    for s in suggestions:
        markdown += f"- **{s.get('feedback', '?')}**: {s['issue']} at `{s.get('host', '?')}`"
        if s.get("actual_rule"):
            markdown += f" (matched: `{s['actual_rule']}`)"
        markdown += "\n"

    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / args.markdown_out).write_text(markdown, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
