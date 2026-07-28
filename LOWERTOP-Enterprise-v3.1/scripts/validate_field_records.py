#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys

import yaml


REQUIRED_MODULES = {
    "apple-weather-qweather",
}


def iso(value):
    if isinstance(value, dt.datetime):
        return value
    if not value:
        return None
    return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def version_marker(root: Path) -> tuple[str, str]:
    release = yaml.safe_load((root / "config" / "release.yaml").read_text(encoding="utf-8")) or {}
    version = str(release.get("meta", {}).get("version", "unknown"))
    suffix = version.split("-", 1)[1].upper() if "-" in version else version.upper()
    return version, suffix


def configuration_text(data: dict) -> str:
    return json.dumps(data.get("configuration", ""), ensure_ascii=False, sort_keys=True)


def is_current(data: dict, marker: str) -> bool:
    return marker in configuration_text(data).upper()


def check_device(path: Path, marker: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    applicable = is_current(data, marker)
    if not applicable:
        return {
            "file": str(path), "kind": "device", "ok": True, "applicable": False,
            "environment": data.get("environment"), "note": f"record does not target {marker}",
        }
    errors = []
    required = ("record_id", "environment", "source_commit", "configuration", "device", "result")
    for key in required:
        if not data.get(key):
            errors.append(f"missing {key}")
    if data.get("status") != "complete":
        errors.append("status must be complete")
    if data.get("result") not in {"pass", "fail"}:
        errors.append("result must be pass or fail")
    return {
        "file": str(path), "kind": "device", "ok": not errors, "applicable": True,
        "environment": data.get("environment"), "result": data.get("result"), "errors": errors,
    }


def check_adblock(path: Path, marker: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    applicable = is_current(data, marker)
    if not applicable:
        return {
            "file": str(path), "kind": "adblock", "ok": True, "applicable": False,
            "note": f"record does not target {marker}",
        }
    errors = []
    start, end = iso(data.get("started_at")), iso(data.get("ended_at"))
    duration = (end - start).total_seconds() / 3600 if start and end else 0
    minimum = max(72.0, float(data.get("minimum_required_hours", 72)))
    if data.get("status") != "complete":
        errors.append("status must be complete")
    if duration < minimum:
        errors.append(f"duration {duration:.2f}h is below {minimum:.2f}h")
    summary = data.get("summary", {})
    if summary.get("p0", 0) or summary.get("p1", 0):
        errors.append("P0/P1 incidents must be zero")
    if summary.get("unresolved", 0):
        errors.append("unresolved incidents must be zero")
    if summary.get("conclusion") not in {"pass", "fail"}:
        errors.append("summary.conclusion must be pass or fail")
    return {
        "file": str(path), "kind": "adblock", "ok": not errors, "applicable": True,
        "duration_hours": round(duration, 2), "minimum_required_hours": minimum, "errors": errors,
    }


def check_module(path: Path, marker: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    module_id = str(data.get("module_id", "")).strip()
    applicable = is_current(data, marker)
    if not applicable:
        return {
            "file": str(path), "kind": "module", "module_id": module_id,
            "ok": True, "applicable": False, "note": f"record does not target {marker}",
        }
    errors = []
    for key in ("record_id", "module_id", "source_commit", "configuration", "module_file", "result", "checks"):
        if not data.get(key):
            errors.append(f"missing {key}")
    if module_id not in REQUIRED_MODULES:
        errors.append(f"unknown module_id: {module_id}")
    if data.get("status") != "complete":
        errors.append("status must be complete")
    if data.get("result") not in {"pass", "fail"}:
        errors.append("result must be pass or fail")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
    elif any(not isinstance(item, dict) or item.get("result") not in {"pass", "fail"} for item in checks):
        errors.append("every check must contain result=pass or fail")
    return {
        "file": str(path), "kind": "module", "module_id": module_id,
        "ok": not errors, "applicable": True, "result": data.get("result"), "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="reports/field-validation.json")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    version, marker = version_marker(root)

    device = [p for p in (root / "validation/device").glob("**/*.yaml") if "TEMPLATE" not in p.name]
    adblock = [p for p in (root / "validation/adblock").glob("*.yaml") if "TEMPLATE" not in p.name]
    modules = [p for p in (root / "validation/modules").glob("*.yaml") if "TEMPLATE" not in p.name]

    results = (
        [check_device(p, marker) for p in device]
        + [check_adblock(p, marker) for p in adblock]
        + [check_module(p, marker) for p in modules]
    )
    applicable = [item for item in results if item.get("applicable")]
    errors = [item for item in applicable if not item["ok"]]

    environments = {
        item.get("environment") for item in applicable
        if item["kind"] == "device" and item.get("ok") and item.get("result") == "pass"
    }
    missing = sorted({"wifi", "cellular", "switching"} - environments)

    current_adblock = [item for item in applicable if item["kind"] == "adblock" and item.get("ok")]
    if not current_adblock:
        missing.append("adblock-72h")

    passed_modules = {
        item.get("module_id") for item in applicable
        if item["kind"] == "module" and item.get("ok") and item.get("result") == "pass"
    }
    missing.extend(f"module:{module_id}" for module_id in sorted(REQUIRED_MODULES - passed_modules))

    ok = not errors and (not args.require_complete or not missing)
    report = {
        "ok": ok,
        "version": version,
        "version_marker": marker,
        "require_complete": args.require_complete,
        "summary": {
            "records": len(results),
            "applicable": len(applicable),
            "stale": len(results) - len(applicable),
            "invalid": len(errors),
        },
        "missing_evidence": missing,
        "results": results,
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
