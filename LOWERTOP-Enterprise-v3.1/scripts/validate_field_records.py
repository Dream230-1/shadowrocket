#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys

import yaml


def iso(value):
    if isinstance(value, dt.datetime):
        return value
    if not value:
        return None
    return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def check_device(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = []
    required = ("record_id", "environment", "source_commit", "configuration", "device", "result")
    for key in required:
        if not data.get(key): errors.append(f"missing {key}")
    if data.get("status") != "complete": errors.append("status must be complete")
    if data.get("result") not in {"pass", "fail"}: errors.append("result must be pass or fail")
    return {"file": str(path), "kind": "device", "ok": not errors, "errors": errors}


def check_adblock(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = []
    start, end = iso(data.get("started_at")), iso(data.get("ended_at"))
    duration = (end - start).total_seconds() / 3600 if start and end else 0
    minimum = float(data.get("minimum_required_hours", 72))
    if data.get("status") != "complete": errors.append("status must be complete")
    if duration < minimum: errors.append(f"duration {duration:.2f}h is below {minimum:.2f}h")
    summary = data.get("summary", {})
    if summary.get("p0", 0) or summary.get("p1", 0): errors.append("P0/P1 incidents must be zero")
    if summary.get("unresolved", 0): errors.append("unresolved incidents must be zero")
    if summary.get("conclusion") not in {"pass", "fail"}: errors.append("summary.conclusion must be pass or fail")
    return {"file": str(path), "kind": "adblock", "ok": not errors, "duration_hours": round(duration, 2), "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="reports/field-validation.json")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    device = [p for p in (root / "validation/device").glob("**/*.yaml") if "TEMPLATE" not in p.name]
    adblock = [p for p in (root / "validation/adblock").glob("*.yaml") if "TEMPLATE" not in p.name]
    results = [check_device(p) for p in device] + [check_adblock(p) for p in adblock]
    environments = set()
    for path in device:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("status") == "complete" and data.get("result") == "pass": environments.add(data.get("environment"))
    missing = sorted({"wifi", "cellular", "switching"} - environments)
    errors = [item for item in results if not item["ok"]]
    if not adblock: missing.append("adblock-72h")
    ok = not errors and (not args.require_complete or not missing)
    report = {"ok": ok, "require_complete": args.require_complete, "summary": {"records": len(results), "invalid": len(errors)}, "missing_evidence": missing, "results": results}
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__": main()
