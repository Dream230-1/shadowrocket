#!/usr/bin/env python3
"""Convert Shadowrocket-style modules into memory-efficient Stash rule providers."""

from __future__ import annotations

import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

IP_TYPES = {"IP-CIDR", "IP-CIDR6"}
POLICIES = {
    "DIRECT",
    "PROXY",
    "REJECT",
    "REJECT-DROP",
    "REJECT-DICT",
    "REJECT-ARRAY",
    "REJECT-200",
    "REJECT-IMG",
    "REJECT-TINYGIF",
    "REJECT-NO-DROP",
}


def unique(items: Iterable[str]) -> list[str]:
    return list(OrderedDict.fromkeys(items))


def parse_rule(line: str) -> tuple[str, str, list[str]] | None:
    try:
        fields = next(csv.reader([line], skipinitialspace=True))
    except csv.Error:
        return None

    fields = [field.strip() for field in fields]
    if len(fields) < 3:
        return None

    rule_type = fields[0].upper()
    value = fields[1]
    extras = fields[2:]
    policy_index = next(
        (index for index, field in enumerate(extras) if field.upper() in POLICIES),
        None,
    )
    if policy_index is None:
        return None

    extras = extras[:policy_index] + extras[policy_index + 1 :]
    return rule_type, value, extras


def convert(input_path: Path) -> dict[str, list[str]]:
    domain: list[str] = []
    ipcidr: list[str] = []
    classical: list[str] = []

    for raw_line in input_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue

        parsed = parse_rule(line)
        if parsed is None:
            continue

        rule_type, value, extras = parsed
        if rule_type == "DOMAIN":
            domain.append(value)
        elif rule_type == "DOMAIN-SUFFIX":
            domain.append(f"+.{value.lstrip('.')}")
        elif rule_type in IP_TYPES:
            ipcidr.append(value)
        else:
            classical.append(",".join([rule_type, value, *extras]))

    return {
        "domain": unique(domain),
        "ipcidr": unique(ipcidr),
        "classical": unique(classical),
    }


def write_yaml(path: Path, payload: list[str], source_sha: str, source_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Source: GMOogway/shadowrocket-rules@{source_sha}",
        f"# Input: {source_name}",
        f"# Rules: {len(payload)}",
    ]
    if payload:
        lines.append("payload:")
        lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in payload)
    else:
        lines.append("payload: []")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("reject_module", type=Path)
    parser.add_argument("direct_module", type=Path)
    parser.add_argument("proxy_module", type=Path)
    args = parser.parse_args()

    inputs = {
        "reject": args.reject_module,
        "direct": args.direct_module,
        "proxy": args.proxy_module,
    }
    for name, input_path in inputs.items():
        converted = convert(input_path)
        for behavior, payload in converted.items():
            output = args.output_dir / f"gmoogway-{name}-{behavior}.yaml"
            write_yaml(output, payload, args.source_commit, input_path.name)
            print(f"{output}: {len(payload)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
