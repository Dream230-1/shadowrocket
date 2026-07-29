#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re


SHA40 = re.compile(r"^[0-9a-f]{40}$")


def transform(text: str, source_commit: str) -> tuple[str, int]:
    if not SHA40.fullmatch(source_commit):
        raise ValueError("source commit must be a 40-character lowercase Git SHA")

    source_rules = 0
    converted_rules = 0
    output: list[str] = []
    inserted_commit = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("#!desc="):
            line = re.sub(r"\s+Upstream:[0-9a-f]{40}\b", "", line)
            line = f"{line} Upstream:{source_commit}"
            inserted_commit = True

        if line and not line.lstrip().startswith("#") and "," in line:
            source_rules += 1
            parts = line.split(",")
            policy_indexes = [index for index, value in enumerate(parts) if value.strip() == "PROXY"]
            if policy_indexes:
                policy_index = policy_indexes[-1]
                parts[policy_index] = parts[policy_index].replace("PROXY", "AI")
                line = ",".join(parts)
            if any(value.strip() == "PROXY" for value in line.split(",")):
                raise ValueError(f"unconverted PROXY policy: {raw}")
            if any(value.strip() == "AI" for value in line.split(",")):
                converted_rules += 1
        output.append(line)

    if not inserted_commit:
        insert_at = next(
            (index + 1 for index, line in enumerate(output) if line.startswith("#!name=")),
            0,
        )
        output.insert(insert_at, f"#!desc=Upstream:{source_commit}")

    if source_rules == 0:
        raise ValueError("upstream proxy module contains no rules")
    if converted_rules != source_rules:
        raise ValueError(
            f"rule preservation failed: source={source_rules}, AI={converted_rules}"
        )
    return "\n".join(output) + "\n", source_rules


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preserve GMOogway proxy_list and retarget every policy to AI"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    rendered, count = transform(source.read_text(encoding="utf-8"), args.source_commit)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"proxy module preserved: {count} rules, all policies=AI")


if __name__ == "__main__":
    main()
