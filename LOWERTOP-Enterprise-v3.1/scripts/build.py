#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

from module_config import apply_modules


def deep_merge(base, overlay):
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for key, value in overlay.items():
            result[key] = deep_merge(result[key], value) if key in result else value
        return result
    return overlay


def run(command, cwd, *, allow_failure: bool = False):
    print("+", " ".join(map(str, command)), flush=True)
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr, flush=True)
    if result.returncode and not allow_failure:
        raise RuntimeError(
            f"command failed ({result.returncode}): {command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def copy_tree_files(source: Path, target: Path, pattern: str = "*") -> None:
    target.mkdir(parents=True, exist_ok=True)
    for file in source.glob(pattern):
        if file.is_file():
            shutil.copy2(file, target / file.name)


def reset_directory(path: Path) -> None:
    """Clear a generated directory without shutil.rmtree on the Minis shared filesystem."""
    path.mkdir(parents=True, exist_ok=True)
    for child in list(path.iterdir()):
        if child.is_dir() and not child.is_symlink():
            reset_directory(child)
            child.rmdir()
        else:
            child.unlink()


def resolve_base_url(project: Path, repository: str, source_ref: str | None) -> tuple[str, str]:
    ref = source_ref or os.getenv("GITHUB_SHA")
    if not ref:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project, text=True, capture_output=True)
        ref = result.stdout.strip() if result.returncode == 0 else ""
    if not re.fullmatch(r"[0-9a-f]{40}", ref or ""):
        raise SystemExit("--source-ref 必须是 40 位 Git Commit SHA，Modular URL 不允许引用 main")
    return f"https://raw.githubusercontent.com/{repository}/{ref}/Shadowrocket/LOWERTOP-Enterprise-v3.1", ref


def validate_generated(path: Path):
    text = path.read_text(encoding="utf-8")
    required = [
        "dns-fallback-system = false", "dns-direct-system = false",
        "dns-direct-fallback-proxy = false", "ipv6 = false", "prefer-ipv6 = false",
        "udp-policy-not-supported-behaviour = REJECT", "block-quic = always-allow", "FINAL,PROXY",
    ]
    errors = [f"missing: {item}" for item in required if item not in text]
    fallback = next((line for line in text.splitlines() if line.startswith("fallback-dns-server = ")), "")
    if "#proxy" not in fallback:
        errors.append("fallback-dns-server missing #proxy")
    openai, apple_global, apple_core, advertising = (
        text.find("DOMAIN-SUFFIX,openai.com,AI"), text.find("# Local ruleset: Apple-Global-AI"),
        text.find("# Local ruleset: Apple-Core-Direct"), text.find("AdvertisingLite"),
    )
    if min(openai, apple_global, apple_core, advertising) < 0:
        errors.append("required AI/Apple/Advertising module missing")
    if openai >= 0 and advertising >= 0 and openai > advertising:
        errors.append("OpenAI rule must precede AdvertisingLite")
    if apple_global >= 0 and apple_core >= 0 and apple_global > apple_core:
        errors.append("Apple Global must precede Apple Core")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--repository", default="Dream230-1/ShuntRules")
    parser.add_argument("--source-ref")
    args = parser.parse_args()

    project = Path(__file__).resolve().parents[1]
    modular_base_url, _source_ref = resolve_base_url(project, args.repository, args.source_ref)
    repo_root = project.parents[1]
    rc3 = repo_root / "Shadowrocket" / "LOWERTOP-Enterprise-v3.0-RC3"
    if not rc3.exists():
        raise SystemExit(f"RC3 build kernel not found: {rc3}")

    merged = yaml.safe_load((rc3 / "manifest.yaml").read_text(encoding="utf-8"))
    for name in ("release.yaml", "dns.yaml"):
        overlay = yaml.safe_load((project / "config" / name).read_text(encoding="utf-8")) or {}
        merged = deep_merge(merged, overlay)
    merged, modules = apply_modules(merged, project / "modules")

    features = yaml.safe_load((project / "config" / "features.yaml").read_text(encoding="utf-8")) or {}
    flags = features.get("features", {})
    if not flags.get("advertising_lite", False):
        raise SystemExit("AdvertisingLite must remain enabled in v3.1 RC2")
    if flags.get("unverified_dns_protocol_fallback", False):
        raise SystemExit("Unverified DNS protocol fallback cannot enter an RC2 release profile")
    if flags.get("force_ech", False):
        raise SystemExit("Forced ECH cannot enter an RC2 release profile")

    output, modular, experimental, reports = (project / name for name in ("build", "modular", "experimental", "reports"))
    for directory in (output, modular, experimental, reports):
        reset_directory(directory)

    with tempfile.TemporaryDirectory(prefix="lowertop-v31-rc2-") as temp:
        workspace = Path(temp) / "project"
        shutil.copytree(rc3, workspace)
        (workspace / "manifest.yaml").write_text(
            yaml.safe_dump(merged, allow_unicode=True, sort_keys=False, width=200), encoding="utf-8"
        )
        shutil.copytree(project / "rules", workspace / "rules", dirs_exist_ok=True)

        py = sys.executable
        run([py, "scripts/generate.py", "--profile", "all-release", "--mode", "inline"], workspace)
        run([py, "scripts/generate.py", "--profile", "all-release", "--mode", "remote", "--base-url", modular_base_url, "--out-dir", "modular"], workspace)
        run([py, "scripts/generate.py", "--profile", "ipv6_svcb_experimental", "--mode", "inline", "--out-dir", "experimental"], workspace)

        performance = workspace / "build" / "LOWERTOP-Enterprise-v3.1-RC2-Performance-Direct.conf"
        modular_performance = workspace / "modular" / "LOWERTOP-Enterprise-v3.1-RC2-Performance-Modular.conf"
        errors = validate_generated(performance)
        if errors:
            print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
            raise SystemExit(1)

        copy_tree_files(workspace / "build", output)
        copy_tree_files(workspace / "modular", modular)
        copy_tree_files(workspace / "experimental", experimental, "*.conf")

        # Release behavior lock and offline negative route regression are mandatory.
        run([py, "scripts/behavior_lock.py", "--config", str(performance), "--baseline", str(project / "baselines/rc1-performance.lock.yaml"), "--json-out", str(reports / "behavior-lock.json")], project)
        run([py, "scripts/regression_v31.py", "--kernel-root", str(workspace), "--config", str(performance),
             "--cases", "regression/base_cases.yaml", "--cases", "regression/apple_negative_cases.yaml",
             "--json-out", "reports/regression-offline.json"], project)
        run([py, "scripts/dns_audit.py", "--root", str(workspace), "--json-out", str(reports / "dns-audit.json")], workspace)
        run([py, "scripts/modular_equivalence.py", "--root", str(project), "--manifest", str(workspace / "manifest.yaml"),
             "--direct", str(performance), "--modular", str(modular_performance), "--json-out", "reports/modular-equivalence-offline.json"], project)
        if flags.get("rule_conflict_audit", True):
            run([py, "scripts/rule_conflicts.py", "--root", str(project), "--config", str(performance), "--json-out", "reports/rule-conflicts-offline.json"], project)

        if args.online:
            # Download once into the persistent project cache; every later online gate reuses these exact bytes.
            persistent_cache = project / ".cache" / "remote-rules"
            persistent_cache.mkdir(parents=True, exist_ok=True)
            run([py, "scripts/cache_refresh.py", "--manifest", str(workspace / "manifest.yaml"), "--cache-dir", str(persistent_cache), "--json-out", str(reports / "cache-refresh.json")], project)
            run([py, "scripts/remote_audit_v31.py", "--root", str(workspace), "--cache-dir", str(persistent_cache), "--json-out", str(reports / "remote-audit.json")], project)
            run([py, "scripts/modular_equivalence.py", "--root", str(project), "--manifest", str(workspace / "manifest.yaml"),
                 "--direct", str(performance), "--modular", str(modular_performance), "--cache-dir", str(persistent_cache), "--online", "--json-out", "reports/modular-equivalence-online.json"], project)
            run([py, "scripts/ruleset_drift.py", "--root", str(workspace), "--current", str(reports / "remote-audit.json"), "--json-out", str(reports / "ruleset-drift.json")], workspace)
            run([py, "scripts/regression_v31.py", "--kernel-root", str(workspace), "--config", str(performance),
                 "--cases", "regression/base_cases.yaml", "--cases", "regression/apple_negative_cases.yaml", "--online",
                 "--cache-dir", str(persistent_cache), "--json-out", "reports/regression-online.json"], project)
            run([py, "scripts/adblock_collision.py", "--root", str(workspace), "--cache-dir", str(persistent_cache), "--json-out", str(reports / "adblock-collisions.json")], workspace)
            if flags.get("rule_conflict_audit", True):
                run([py, "scripts/rule_conflicts.py", "--root", str(project), "--config", str(performance),
                     "--cache-dir", str(persistent_cache), "--online-ready", "--json-out", "reports/rule-conflicts-online.json"], project)
            if flags.get("service_health_report", True):
                run([py, "scripts/service_health.py", "--root", str(workspace), "--allow-warnings", "--allow-failures", "--json-out", str(reports / "service-health.json")], workspace)
            if flags.get("network_benchmark_report", True):
                run([py, "scripts/network_benchmark.py", "--root", str(workspace), "--json-out", str(reports / "network-benchmark.json")], workspace)

    summary = {
        "ok": True, "version": merged["meta"]["version"], "kernel": "LOWERTOP-Enterprise-v3.0-RC3",
        "online": args.online, "default_profile": flags["default_profile"], "modules": modules,
        "outputs": sorted(file.name for file in output.glob("*.conf")),
        "modular": sorted(file.name for file in modular.glob("*.conf")),
        "experimental": sorted(file.name for file in experimental.glob("*.conf")),
        "reports": sorted(file.name for file in reports.glob("*.json")),
        "dns_guard": "passed", "advertising_lite": "preserved", "performance_behavior": "RC1 locked",
    }
    (output / "v31-build-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
