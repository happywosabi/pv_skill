#!/usr/bin/env python3
"""Verify and copy the bundled pdoom code snapshot into a working project."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys


SNAPSHOT = Path(__file__).resolve().parents[1] / 'assets' / 'pdoom-project'
MARKER = '.pv-project-source.json'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '\\' in value or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError(f'Unsafe snapshot path: {value}')
    return path


def validate_snapshot(snapshot):
    snapshot = snapshot.resolve()
    manifest = json.loads((snapshot / 'UPSTREAM.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or not manifest.get('files'):
        raise ValueError('Unsupported or empty upstream manifest.')
    seen = set()
    for record in manifest['files']:
        relative = record['path']
        relative_path(relative)
        if relative in seen or relative in (MARKER, 'UPSTREAM.json'):
            raise ValueError(f'Duplicate/reserved snapshot path: {relative}')
        seen.add(relative)
        source = (snapshot / relative).resolve()
        if not source.is_relative_to(snapshot) or not source.is_file():
            raise ValueError(f'Snapshot file missing or outside snapshot: {relative}')
        if source.stat().st_size != record['size'] or sha256(source) != record['sha256']:
            raise ValueError(f'Snapshot integrity mismatch: {relative}')
    for relative in manifest.get('work_directories', []):
        relative_path(relative)
    return manifest


def plan_copy(snapshot, destination):
    snapshot, destination = snapshot.resolve(), destination.expanduser().resolve()
    bundle = Path(__file__).resolve().parents[2]
    if destination.is_relative_to(snapshot) or destination.is_relative_to(bundle):
        raise ValueError('Use a project work directory outside the skill bundle/snapshot.')
    if destination.exists() and not destination.is_dir():
        raise ValueError('Destination is not a directory.')
    manifest = validate_snapshot(snapshot)
    pending, reused, conflicts = [], [], []
    for record in manifest['files']:
        target = destination / record['path']
        if not target.resolve().is_relative_to(destination):
            conflicts.append(f"path escapes destination: {record['path']}")
            continue
        if target.exists() or target.is_symlink():
            if target.is_file() and sha256(target) == record['sha256']:
                reused.append(record['path'])
            else:
                conflicts.append(record['path'])
        else:
            parent = target.parent
            while parent != destination and not parent.exists():
                parent = parent.parent
            if parent.exists() and not parent.is_dir():
                conflicts.append(f"parent is not a directory: {record['path']}")
            else:
                pending.append(record['path'])
    for relative in manifest.get('work_directories', []):
        target = destination / relative
        parent = target
        while parent != destination and not parent.exists():
            parent = parent.parent
        if not target.resolve().is_relative_to(destination) or (parent.exists() and not parent.is_dir()):
            conflicts.append(f'work directory conflict: {relative}')
    marker = destination / MARKER
    if marker.exists() or marker.is_symlink():
        if not marker.resolve().is_relative_to(destination) or not marker.is_file():
            conflicts.append(MARKER)
        else:
            try:
                if json.loads(marker.read_text(encoding='utf-8')) != manifest:
                    conflicts.append(MARKER)
            except (OSError, ValueError):
                conflicts.append(MARKER)
    if conflicts:
        raise ValueError('Refusing to overwrite existing project files: ' + ', '.join(conflicts[:12]))
    return manifest, pending, reused


def bootstrap(snapshot, destination, apply=False):
    snapshot, destination = snapshot.resolve(), destination.expanduser().resolve()
    manifest, pending, reused = plan_copy(snapshot, destination)
    if apply:
        destination.mkdir(parents=True, exist_ok=True)
        for relative in pending:
            source, target = snapshot / relative, destination / relative
            if target.exists() or target.is_symlink():
                raise ValueError(f'Destination changed during copy: {relative}')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for record in manifest['files']:
            if sha256(destination / record['path']) != record['sha256']:
                raise ValueError(f'Copied file did not verify: {record["path"]}')
        for relative in manifest.get('work_directories', []):
            (destination / relative).mkdir(parents=True, exist_ok=True)
        marker = destination / MARKER
        if not marker.exists():
            with marker.open('x', encoding='utf-8') as stream:
                json.dump(manifest, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
    return {'status': 'copied' if apply else 'dry_run', 'destination': str(destination),
            'repository': manifest['repository'], 'upstream_commit': manifest['commit'],
            'files_to_copy': len(pending), 'identical_files_reused': len(reused),
            'excluded_asset_paths': manifest.get('excluded_asset_paths', []),
            'next': 'Supply/adapt song, lyrics, timing data, fonts and any montage assets; use pv-plan before analysis/rendering.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--snapshot', default=str(SNAPSHOT), help='Default: snapshot bundled with pv-plan')
    parser.add_argument('--apply', action='store_true', help='Copy after verification; default is dry run')
    args = parser.parse_args(argv)
    try:
        report = bootstrap(Path(args.snapshot), Path(args.destination), args.apply)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'bootstrap_project: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
