#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

try:
    from .common import load_yaml
except ImportError:
    from common import load_yaml


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--out-dir', default='dist')
    parser.add_argument('--repository', default='Dream230-1/ShuntRules')
    parser.add_argument('--source-ref', default=os.getenv('GITHUB_SHA'))
    parser.add_argument('--project-path')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = load_yaml(root / 'manifest.yaml')
    version = manifest['meta']['version']
    source_ref = args.source_ref
    if not source_ref or not re.fullmatch(r'[0-9a-f]{40}', source_ref):
        raise SystemExit('--source-ref 必须为 40 位 Git Commit SHA，以保证发布链接不可变')
    project_path = args.project_path or manifest['meta'].get('project_path')
    if not project_path:
        raise SystemExit('manifest.meta.project_path 缺失')

    release_root = root / args.out_dir / version
    if release_root.exists():
        shutil.rmtree(release_root)
    for directory in ('direct', 'modular', 'experimental', 'rules', 'reports'):
        (release_root / directory).mkdir(parents=True, exist_ok=True)

    py = sys.executable
    generator = str(root / 'scripts/generate.py')
    run([py, generator, '--root', str(root), '--profile', 'all-release', '--mode', 'inline', '--out-dir', str(release_root / 'direct')])
    base_url = f'https://raw.githubusercontent.com/{args.repository}/{source_ref}/{project_path}'
    run([py, generator, '--root', str(root), '--profile', 'all-release', '--mode', 'remote', '--base-url', base_url, '--out-dir', str(release_root / 'modular')])
    run([py, generator, '--root', str(root), '--profile', 'ipv6_svcb_experimental', '--mode', 'inline', '--out-dir', str(release_root / 'experimental')])
    run([py, generator, '--root', str(root), '--profile', 'ipv6_svcb_experimental', '--mode', 'remote', '--base-url', base_url, '--out-dir', str(release_root / 'experimental')])

    for path in (root / 'rules').glob('*.list'):
        shutil.copy2(path, release_root / 'rules' / path.name)
    for name in ('manifest.yaml', 'README.md', 'CHANGELOG.md', 'TEST-MATRIX.md'):
        shutil.copy2(root / name, release_root / name)
    for path in (root / 'reports').glob('*.json'):
        shutil.copy2(path, release_root / 'reports' / path.name)

    files = sorted(p for p in release_root.rglob('*') if p.is_file() and p.name != 'CHECKSUMS.sha256')
    checksum_lines = [f'{sha256(path)}  {path.relative_to(release_root).as_posix()}' for path in files]
    (release_root / 'CHECKSUMS.sha256').write_text('\n'.join(checksum_lines) + '\n', encoding='utf-8')
    release = {
        'version': version,
        'status': 'release-candidate',
        'source_repository': args.repository,
        'source_commit': source_ref,
        'project_path': project_path,
        'recommended_profile': 'performance',
        'raw_rules_base_url': base_url + '/rules',
        'files': [{'path': p.relative_to(release_root).as_posix(), 'sha256': sha256(p)} for p in files],
    }
    (release_root / 'release.json').write_text(json.dumps(release, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'release_dir': str(release_root), 'source_commit': source_ref, 'file_count': len(files) + 2}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
