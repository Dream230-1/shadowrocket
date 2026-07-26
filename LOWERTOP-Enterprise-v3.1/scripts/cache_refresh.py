#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

import requests
import yaml


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_name(url: str) -> str:
    parsed = urlsplit(url)
    base = Path(parsed.path).name or "resource"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    return f"{hashlib.sha256(url.encode()).hexdigest()[:16]}-{safe}"


def load_index(path: Path) -> dict:
    if not path.exists():
        return {"schema": 1, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"schema": 1, "entries": {}}
    except (ValueError, OSError):
        return {"schema": 1, "entries": {}}


def main() -> None:
    parser = argparse.ArgumentParser(description="ETag/Last-Modified conditional cache for pinned remote rules")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--json-out", default="reports/cache-refresh.json")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    cache_dir = Path(args.cache_dir).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    index_path = cache_dir / "index.json"
    index = load_index(index_path)
    entries = index.setdefault("entries", {})
    session = requests.Session()
    results = []

    meta = manifest["meta"]
    base = f'https://raw.githubusercontent.com/{meta["upstream_repo"]}/{meta["upstream_commit"]}'
    for item in manifest.get("remote_rulesets", []):
        url = f'{base}/{item["path"]}'
        cache_path = cache_dir / f'{item["name"]}.list'
        old = entries.get(url, {})
        result = {"name": item["name"], "url": url, "cache_file": str(cache_path), "ok": False}
        if args.offline:
            if cache_path.exists():
                content = cache_path.read_bytes()
                result.update({"ok": True, "status": "offline-hit", "bytes": len(content), "sha256": sha256(content)})
            else:
                result.update({"status": "offline-miss", "error": "cache file missing"})
            results.append(result)
            continue

        headers = {"User-Agent": "LOWERTOP-v31-cache/1.0"}
        if old.get("etag"):
            headers["If-None-Match"] = old["etag"]
        if old.get("last_modified"):
            headers["If-Modified-Since"] = old["last_modified"]
        try:
            response = session.get(url, headers=headers, timeout=90)
            if response.status_code == 304:
                if not cache_path.exists():
                    raise RuntimeError("server returned 304 but local cache is missing")
                content = cache_path.read_bytes()
                status = "not-modified"
            else:
                response.raise_for_status()
                content = response.content
                if content[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
                    raise ValueError("remote resource returned HTML")
                temp = cache_path.with_suffix(cache_path.suffix + ".tmp")
                temp.write_bytes(content)
                temp.replace(cache_path)
                status = "updated" if old else "miss"
            digest = sha256(content)
            entries[url] = {
                "name": item["name"], "cache_file": str(cache_path), "etag": response.headers.get("ETag") or old.get("etag"),
                "last_modified": response.headers.get("Last-Modified") or old.get("last_modified"), "sha256": digest, "bytes": len(content),
            }
            result.update({"ok": True, "status": status, "http_status": response.status_code, "bytes": len(content), "sha256": digest,
                           "etag_present": bool(entries[url].get("etag")), "last_modified_present": bool(entries[url].get("last_modified"))})
        except Exception as exc:
            if cache_path.exists():
                content = cache_path.read_bytes()
                result.update({"ok": True, "status": "stale-if-error", "warning": str(exc), "bytes": len(content), "sha256": sha256(content)})
            else:
                result.update({"status": "error", "error": str(exc)})
        results.append(result)

    failures = [item for item in results if not item["ok"]]
    if not args.offline:
        index["upstream_commit"] = meta["upstream_commit"]
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status_counts = {}
    for item in results:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    report = {"ok": not failures, "offline": args.offline, "cache_dir": str(cache_dir), "summary": {"resources": len(results), "failed": len(failures), "statuses": status_counts}, "results": results, "failures": failures}
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
