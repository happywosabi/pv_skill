#!/usr/bin/env python3
"""Install the complete PV skill bundle, refusing to overwrite different skills."""
import argparse
import filecmp
import os
from pathlib import Path
import shutil
import sys
import tempfile


def identical(source, target):
    if not target.is_dir() or target.is_symlink():
        return False
    source_files = {p.relative_to(source) for p in source.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts}
    target_files = {p.relative_to(target) for p in target.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts}
    return source_files == target_files and all(filecmp.cmp(source / p, target / p, shallow=False)
                                               for p in source_files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(Path(__file__).resolve().parents[2]))
    default_home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    parser.add_argument('--dest', default=str(default_home / 'skills'))
    parser.add_argument('--apply', action='store_true', help='Apply after conflict preflight; default is dry run')
    args = parser.parse_args()
    staging = None
    try:
        source, destination = Path(args.source).resolve(), Path(args.dest).expanduser().resolve()
        folders = sorted(p for p in source.glob('pv-*') if (p / 'SKILL.md').is_file())
        if not folders or not (source / 'pv-plan/SKILL.md').is_file():
            raise ValueError('No complete PV bundle at --source.')
        if destination == source or destination.is_relative_to(source):
            raise ValueError('Install destination must be outside the source bundle.')
        pending = []
        for folder in folders:
            target = destination / folder.name
            if target.exists() or target.is_symlink():
                if not identical(folder, target):
                    raise ValueError(f'Refusing to overwrite different existing skill: {target}')
            else:
                pending.append(folder)
        print(f'{len(folders)} skills; {len(pending)} new, {len(folders)-len(pending)} identical; destination {destination}')
        if not args.apply:
            print('Dry run only. Use --apply within the authorized filesystem permissions.')
            return 0
        destination.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='.pv-install-', dir=destination))
        for folder in pending:
            shutil.copytree(folder, staging / folder.name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in pending:
            target = destination / folder.name
            if target.exists() or target.is_symlink():
                raise ValueError(f'Destination appeared during installation: {target}')
            (staging / folder.name).rename(target)
        print(f'Installed {len(pending)} skills without changing existing different skills.')
        return 0
    except (OSError, ValueError) as exc:
        print(f'install: {exc}', file=sys.stderr)
        return 2
    finally:
        if staging and staging.exists():
            shutil.rmtree(staging)


if __name__ == '__main__':
    sys.exit(main())
