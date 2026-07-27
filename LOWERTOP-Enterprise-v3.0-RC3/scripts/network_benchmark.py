#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

import requests

try:
    from .common import load_yaml
except ImportError:
    from common import load_yaml


def run_one(session: requests.Session, item: dict, repeats: int) -> dict:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        try:
            response = session.get(
                item['url'], timeout=item.get('timeout', 12), allow_redirects=False,
                stream=True, headers={'User-Agent': 'LOWERTOP-v3-benchmark/1.0'},
            )
            next(response.iter_content(chunk_size=1024), b'')
            elapsed = round((time.perf_counter() - started) * 1000, 1)
            samples.append({'ok': True, 'latency_ms': elapsed, 'status': response.status_code, 'location': response.headers.get('Location')})
        except Exception as exc:
            samples.append({'ok': False, 'latency_ms': round((time.perf_counter() - started) * 1000, 1), 'error': str(exc)})
    good = [s['latency_ms'] for s in samples if s['ok']]
    return {
        'id': item['id'], 'url': item['url'], 'policy': item.get('policy'),
        'summary': {
            'attempts': len(samples), 'successes': len(good),
            'median_ms': round(statistics.median(good), 1) if good else None,
            'min_ms': min(good) if good else None,
            'max_ms': max(good) if good else None,
        },
        'samples': samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--proxy', help='例如 socks5h://127.0.0.1:7221')
    parser.add_argument('--repeats', type=int)
    parser.add_argument('--json-out', default='reports/network-benchmark.json')
    parser.add_argument('--fail-on-total-failure', action='store_true')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = load_yaml(root / 'manifest.yaml')
    settings = manifest.get('benchmark', {})
    repeats = args.repeats or int(settings.get('repeats', 3))
    session = requests.Session()
    if args.proxy:
        session.proxies.update({'http': args.proxy, 'https': args.proxy})
    results = [run_one(session, item, repeats) for item in settings.get('endpoints', [])]
    total_failures = [item for item in results if item['summary']['successes'] == 0]
    ok = not (args.fail_on_total_failure and total_failures)
    report = {
        'ok': ok,
        'proxy': args.proxy,
        'repeats': repeats,
        'summary': {'endpoints': len(results), 'total_failures': len(total_failures)},
        'results': results,
        'note': '公共 CI Runner 的绝对延迟不代表 iPhone 实际速度；本报告用于同环境下比较版本或代理路径。requests 不提供 HTTP/3 协商确认。',
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
