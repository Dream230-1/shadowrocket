from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


KINDS = {"local", "remote"}


def load_modules(directory: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in sorted(directory.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        module = data.get("module")
        if not isinstance(module, dict):
            raise ValueError(f"模块文件缺少 module 对象：{path}")
        module_id = str(module.get("id", "")).strip()
        if not module_id:
            raise ValueError(f"模块缺少 id：{path}")
        if module_id in seen_ids:
            raise ValueError(f"模块 id 重复：{module_id}")
        seen_ids.add(module_id)
        module["_file"] = str(path)
        modules.append(module)
    if not modules:
        raise ValueError(f"未发现模块声明：{directory}")
    return modules


def apply_modules(manifest: dict[str, Any], directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    modules = load_modules(directory)
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    expected: set[tuple[str, str]] = set()
    for kind, key in (("local", "local_rulesets"), ("remote", "remote_rulesets")):
        for item in manifest.get(key, []):
            identity = (kind, item["name"])
            if identity in lookup:
                raise ValueError(f"规则集重复：{kind}/{item['name']}")
            lookup[identity] = item
            expected.add(identity)

    assembled: dict[str, list[dict[str, Any]]] = {"local": [], "remote": []}
    claimed: dict[tuple[str, str], str] = {}
    summary: list[dict[str, Any]] = []
    for module in modules:
        enabled = bool(module.get("enabled", True))
        entries = module.get("rulesets", []) or []
        if not isinstance(entries, list):
            raise ValueError(f"模块 {module['id']} 的 rulesets 必须是数组")
        names: list[str] = []
        for ref in entries:
            if not isinstance(ref, dict):
                raise ValueError(f"模块 {module['id']} 包含无效规则引用")
            kind = ref.get("kind")
            name = ref.get("name")
            if kind not in KINDS or not name:
                raise ValueError(f"模块 {module['id']} 规则引用必须包含 kind(local/remote) 与 name")
            identity = (kind, name)
            if identity in claimed:
                raise ValueError(f"规则集 {kind}/{name} 同时属于 {claimed[identity]} 与 {module['id']}")
            source = lookup.get(identity)
            if source is None:
                raise ValueError(f"模块 {module['id']} 引用了不存在的规则集：{kind}/{name}")
            for field in ("policy", "stage"):
                if field in ref and ref[field] != source.get(field):
                    raise ValueError(
                        f"模块 {module['id']} 的 {name}.{field}={ref[field]!r} "
                        f"与行为基线 {source.get(field)!r} 不一致"
                    )
            claimed[identity] = module["id"]
            names.append(f"{kind}/{name}")
            if enabled:
                assembled[kind].append(dict(source))
        summary.append({
            "id": module["id"],
            "enabled": enabled,
            "description": module.get("description", ""),
            "rulesets": names,
        })

    missing = sorted(expected - set(claimed))
    if missing:
        rendered = ", ".join(f"{kind}/{name}" for kind, name in missing)
        raise ValueError(f"以下规则集未归属任何模块：{rendered}")

    manifest["local_rulesets"] = assembled["local"]
    manifest["remote_rulesets"] = assembled["remote"]
    manifest["modules"] = summary
    return manifest, summary
