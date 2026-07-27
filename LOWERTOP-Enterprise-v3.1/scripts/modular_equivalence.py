#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from common import load_yaml, parse_rule
except ModuleNotFoundError:
    kernel_scripts = Path(__file__).resolve().parents[2] / "LOWERTOP-Enterprise-v3.0-RC3" / "scripts"
    sys.path.insert(0, str(kernel_scripts))
    from common import load_yaml, parse_rule


def canonical(parts: list[str], default_policy: str | None = None) -> str:
    if parts[0] == "FINAL":
        return ",".join(parts)
    if default_policy is None:
        policy_index = -2 if parts[-1].lower() == "no-resolve" else -1
        policy = parts[policy_index]
        body = parts[:policy_index] + parts[policy_index + 1:]
    else:
        policy = default_policy
        body = list(parts)
    if body and body[-1].lower() == "no-resolve":
        return ",".join(body[:-1] + [policy, body[-1]])
    return ",".join(body + [policy])


def compile_config(path: Path, root: Path, manifest: dict, cache_dir: Path, online: bool) -> tuple[list[str], list[str]]:
    local_names = {item["name"]: item for item in manifest.get("local_rulesets", [])}
    remote_names = {item["name"]: item for item in manifest.get("remote_rulesets", [])}
    output, skipped = [], []
    in_rules = False
    source = "config"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "[Rule]":
            in_rules = True; continue
        if in_rules and line.startswith("[") and line.endswith("]"):
            break
        if not in_rules or not line:
            continue
        if line.startswith("#"):
            if line.startswith("# Local ruleset:"):
                source = line.removeprefix("# Local ruleset:").strip().split(" → ", 1)[0]
            elif line.startswith("# Remote ruleset:"):
                source = line.removeprefix("# Remote ruleset:").strip().split(" → ", 1)[0]
            elif line.startswith("# Inline rule:"):
                source = "Inline rule"
            continue
        parts = parse_rule(line, allow_unknown=True)
        if not parts:
            continue
        if parts[0] != "RULE-SET":
            output.append(",".join(parts))
            continue
        policy = parts[2]
        if source in local_names:
            rules_path = root / local_names[source]["file"]
        elif source in remote_names:
            if not online:
                skipped.append(source); continue
            rules_path = cache_dir / f"{source}.list"
        else:
            raise ValueError(f"无法识别 RULE-SET 来源：{source}")
        if not rules_path.exists():
            raise FileNotFoundError(f"规则文件不存在：{rules_path}")
        for rule_raw in rules_path.read_text(encoding="utf-8").splitlines():
            remote_parts = parse_rule(rule_raw, allow_unknown=True)
            if remote_parts:
                output.append(canonical(remote_parts, policy))
    return output, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand Direct and Modular configs and compare route semantics")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--direct", required=True)
    parser.add_argument("--modular", required=True)
    parser.add_argument("--cache-dir", default=".cache/remote-rules")
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--json-out", default="reports/modular-equivalence.json")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest = load_yaml(Path(args.manifest).resolve())
    cache = Path(args.cache_dir)
    if not cache.is_absolute(): cache = root / cache
    direct, direct_skipped = compile_config(Path(args.direct).resolve(), root, manifest, cache, args.online)
    modular, modular_skipped = compile_config(Path(args.modular).resolve(), root, manifest, cache, args.online)
    differences = []
    for index in range(max(len(direct), len(modular))):
        left = direct[index] if index < len(direct) else "<missing>"
        right = modular[index] if index < len(modular) else "<missing>"
        if left != right:
            differences.append({"index": index, "direct": left, "modular": right})
            if len(differences) >= 100: break
    report = {
        "ok": not differences and direct_skipped == modular_skipped,
        "mode": "online" if args.online else "offline",
        "direct": args.direct, "modular": args.modular,
        "summary": {"direct_rules": len(direct), "modular_rules": len(modular), "differences": len(differences), "skipped_remote_rulesets": len(direct_skipped)},
        "direct_skipped": direct_skipped, "modular_skipped": modular_skipped, "differences": differences,
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__": main()
