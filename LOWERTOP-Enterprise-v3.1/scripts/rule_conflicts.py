#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
from pathlib import Path
import sys

try:
    from common import load_yaml, parse_rule, read_rules
except ModuleNotFoundError:
    kernel_scripts = Path(__file__).resolve().parents[2] / "LOWERTOP-Enterprise-v3.0-RC3" / "scripts"
    sys.path.insert(0, str(kernel_scripts))
    from common import load_yaml, parse_rule, read_rules

DOMAIN_KINDS = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
IP_KINDS = {"IP-CIDR", "IP-CIDR6"}


def suffix_match(domain: str, suffix: str) -> bool:
    domain = domain.lower().strip(".")
    suffix = suffix.lower().strip(".")
    return domain == suffix or domain.endswith("." + suffix)


def overlap(a: list[str], b: list[str]) -> tuple[bool, str | None]:
    ka, kb = a[0], b[0]
    if ka in DOMAIN_KINDS and kb in DOMAIN_KINDS:
        va, vb = a[1].lower(), b[1].lower()
        if ka == kb == "DOMAIN":
            return (va == vb, "exact-domain" if va == vb else None)
        if ka == "DOMAIN" and kb == "DOMAIN-SUFFIX":
            hit = suffix_match(va, vb); return hit, "domain-in-suffix" if hit else None
        if ka == "DOMAIN-SUFFIX" and kb == "DOMAIN":
            hit = suffix_match(vb, va); return hit, "domain-in-suffix" if hit else None
        if ka == kb == "DOMAIN-SUFFIX":
            hit = suffix_match(va, vb) or suffix_match(vb, va); return hit, "suffix-overlap" if hit else None
        if ka == "DOMAIN-KEYWORD" and kb == "DOMAIN-KEYWORD":
            hit = va in vb or vb in va; return hit, "keyword-overlap" if hit else None
        if ka == "DOMAIN-KEYWORD":
            hit = va in vb; return hit, "keyword-target" if hit else None
        if kb == "DOMAIN-KEYWORD":
            hit = vb in va; return hit, "keyword-target" if hit else None
    if ka in IP_KINDS and kb in IP_KINDS:
        try:
            na = ipaddress.ip_network(a[1], strict=False)
            nb = ipaddress.ip_network(b[1], strict=False)
        except ValueError:
            return False, None
        hit = na.version == nb.version and na.overlaps(nb)
        return hit, "cidr-overlap" if hit else None
    return False, None


def parse_config(path: Path, cache_dir: Path, online_ready: bool) -> list[dict]:
    rules: list[dict] = []
    source = "config"
    in_rules = False
    order = 0
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
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
        if parts[0] == "RULE-SET":
            if not online_ready:
                continue
            cache = cache_dir / f"{source}.list"
            if not cache.exists():
                raise FileNotFoundError(f"缺少远程规则缓存：{cache}")
            policy = parts[2]
            for remote_lineno, remote_raw, remote_parts in read_rules(cache, allow_unknown=True):
                order += 1
                rules.append({"order": order, "source": source, "policy": policy, "line": remote_lineno, "raw": remote_raw, "parts": remote_parts})
            continue
        order += 1
        policy = parts[-2] if parts[-1].lower() == "no-resolve" else parts[-1]
        rules.append({"order": order, "source": source if parts[0] != "FINAL" else "FINAL", "policy": policy, "line": lineno, "raw": line, "parts": parts})
    return rules


def candidate_overlaps(rules: list[dict]):
    """Yield semantic overlaps without comparing every CIDR to every rule."""
    domains = [rule for rule in rules if rule["parts"][0] in DOMAIN_KINDS]
    for index, first in enumerate(domains):
        for second in domains[index + 1:]:
            if first["policy"] == second["policy"]:
                continue
            hit, reason = overlap(first["parts"], second["parts"])
            if hit and reason:
                yield first, second, reason

    for version in (4, 6):
        intervals = []
        for rule in rules:
            if rule["parts"][0] not in IP_KINDS:
                continue
            try:
                network = ipaddress.ip_network(rule["parts"][1], strict=False)
            except ValueError:
                continue
            if network.version == version:
                intervals.append((int(network.network_address), int(network.broadcast_address), rule))
        intervals.sort(key=lambda item: (item[0], item[1]))
        active: list[tuple[int, int, dict]] = []
        for start, end, current in intervals:
            active = [item for item in active if item[1] >= start]
            for _old_start, _old_end, previous in active:
                if previous["policy"] == current["policy"]:
                    continue
                first, second = (previous, current) if previous["order"] < current["order"] else (current, previous)
                yield first, second, "cidr-overlap"
            active.append((start, end, current))


def conflict_record(earlier: dict, later: dict, reason: str, approved: dict) -> dict:
    semantic_earlier = ",".join(earlier["parts"][:2])
    semantic_later = ",".join(later["parts"][:2])
    key = f'{earlier["source"]}:{semantic_earlier}|{later["source"]}:{semantic_later}'
    return {
        "key": key,
        "reason": reason,
        "severity": "high" if reason in {"exact-domain", "domain-in-suffix", "cidr-overlap"} else "medium",
        "approved": key in approved,
        "approval": approved.get(key),
        "winner": {k: earlier[k] for k in ("source", "policy", "order", "line", "raw")},
        "shadowed": {k: later[k] for k in ("source", "policy", "order", "line", "raw")},
    }


def load_timed_entries(items: list[dict], today: dt.date) -> tuple[list[dict], list[dict]]:
    valid, expired = [], []
    for item in items:
        expiry_value = item.get("expires")
        try:
            expiry = expiry_value if isinstance(expiry_value, dt.date) else dt.date.fromisoformat(str(expiry_value))
        except (TypeError, ValueError):
            expired.append({**item, "error": "invalid expires date"})
            continue
        if expiry < today:
            expired.append(item)
        else:
            valid.append(item)
    return valid, expired


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-policy semantic conflict and shadow audit")
    parser.add_argument("--config", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--cache-dir", default=".cache/remote-rules")
    parser.add_argument("--allowlist", default="config/conflict-allowlist.yaml")
    parser.add_argument("--risk-policy", default="config/conflict-risk-policy.yaml")
    parser.add_argument("--online-ready", action="store_true")
    parser.add_argument("--json-out", default="reports/rule-conflicts.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    rules = parse_config(config_path, Path(args.cache_dir).resolve() if Path(args.cache_dir).is_absolute() else root / args.cache_dir, args.online_ready)
    allow_path = root / args.allowlist
    allow_data = load_yaml(allow_path) if allow_path.exists() else {"approved": []}
    risk_path = root / args.risk_policy
    risk_data = load_yaml(risk_path) if risk_path.exists() else {"classifications": []}
    today = dt.date.today()
    valid_approvals, expired_approvals = load_timed_entries(allow_data.get("approved", []), today)
    valid_classifications, expired_classifications = load_timed_entries(risk_data.get("classifications", []), today)
    approved = {item["key"]: item for item in valid_approvals}
    classifications = {
        (item["winner_source"], item["shadowed_source"], item["reason"]): item
        for item in valid_classifications
    }
    conflicts = [conflict_record(first, second, reason, approved) for first, second, reason in candidate_overlaps(rules)]
    for item in conflicts:
        classification = classifications.get((item["winner"]["source"], item["shadowed"]["source"], item["reason"]))
        if classification:
            item["default_severity"] = item["severity"]
            item["severity"] = classification["severity"]
            item["classification"] = classification
    classification_counts: dict[tuple[str, str, str], int] = {}
    for item in conflicts:
        if item.get("classification"):
            key = (item["winner"]["source"], item["shadowed"]["source"], item["reason"])
            classification_counts[key] = classification_counts.get(key, 0) + 1
    classification_violations = []
    if args.online_ready:
        for key, classification in classifications.items():
            count = classification_counts.get(key, 0)
            minimum = int(classification.get("min_matches", 1))
            maximum = int(classification.get("max_matches", minimum))
            if not minimum <= count <= maximum:
                classification_violations.append({"classification": classification, "actual_matches": count, "expected_range": [minimum, maximum]})
    unapproved_high = [item for item in conflicts if item["severity"] == "high" and not item["approved"]]
    stale_approvals = sorted(set(approved) - {item["key"] for item in conflicts})
    used_classifications = {(item["winner"]["source"], item["shadowed"]["source"], item["reason"]) for item in conflicts if item.get("classification")}
    stale_classifications = [item for key, item in classifications.items() if key not in used_classifications]
    report = {
        "ok": not unapproved_high and not expired_approvals and not expired_classifications and not classification_violations,
        "config": args.config,
        "scope": "All loaded DOMAIN/DOMAIN-SUFFIX/DOMAIN-KEYWORD/IP-CIDR/IP-CIDR6 rules across different policies.",
        "summary": {"compiled_rules": len(rules), "conflicts": len(conflicts), "unapproved_high": len(unapproved_high), "stale_approvals": len(stale_approvals), "expired_approvals": len(expired_approvals), "expired_classifications": len(expired_classifications), "classification_violations": len(classification_violations)},
        "unapproved_high": unapproved_high[:300],
        "conflicts": conflicts[:1000],
        "stale_approvals": stale_approvals,
        "expired_approvals": expired_approvals,
        "stale_classifications": stale_classifications,
        "expired_classifications": expired_classifications,
        "classification_violations": classification_violations,
    }
    output = root / args.json_out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
