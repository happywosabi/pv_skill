#!/usr/bin/env python3
"""Read-only PV inspection and evidence-based workflow state, using stdlib only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile


MANIFEST = Path(__file__).resolve().parents[1] / 'references' / 'workflow.json'
STATUSES = {'pending', 'in_progress', 'needs_input', 'failed', 'done'}


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def find_root(value=None):
    start = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    candidates = [start] if value else [start, *start.parents]
    for candidate in candidates:
        if (candidate / 'app').is_dir() and (candidate / 'analysis').is_dir():
            return candidate
    raise ValueError('Cannot locate PV root containing app/ and analysis/; provide --root.')


def under_root(root, value):
    path = Path(value).expanduser()
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Workflow outputs/evidence must stay inside project root: {value}')
    return path


def input_path(root, value):
    if not value:
        return None
    path = Path(value).expanduser()
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def fingerprint(path):
    if not path.is_file():
        return {'exists': False}
    stat = path.stat()
    digest = hashlib.sha256()
    sampled = stat.st_size > 64 * 1024 * 1024
    with path.open('rb') as stream:
        if sampled:
            digest.update(str(stat.st_size).encode())
            digest.update(stream.read(1024 * 1024))
            stream.seek(max(0, stat.st_size - 1024 * 1024))
            digest.update(stream.read(1024 * 1024))
        else:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
    value = {'exists': True, 'size': stat.st_size, 'sha256': digest.hexdigest(), 'sampled': sampled}
    if sampled:
        value['mtime_ns'] = stat.st_mtime_ns
    return value


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def manifest():
    doc = json.loads(MANIFEST.read_text(encoding='utf-8'))
    ids = [stage['id'] for stage in doc['stages']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate stage IDs in manifest.')
    known = set(ids)
    for stage in doc['stages']:
        if set(stage['dependencies']) - known:
            raise ValueError(f"Unknown dependency for {stage['id']}")
    by_id = {stage['id']: stage for stage in doc['stages']}
    visiting, visited = set(), set()

    def visit(step):
        if step in visiting:
            raise ValueError('Dependency cycle in manifest.')
        if step in visited:
            return
        visiting.add(step)
        for parent in by_id[step]['dependencies']:
            visit(parent)
        visiting.remove(step)
        visited.add(step)

    for step in ids:
        visit(step)
    return doc, by_id


def state_path(root, job):
    if not job or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', job):
        raise ValueError('--job must be a simple 1-64 character name (letters/digits/_/-).')
    return under_root(root, f'out/pv/{job}/workflow.json')


def atomic_json(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                         prefix='.workflow-', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(doc, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        temporary.replace(path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def load_state(root, job, by_id):
    path = state_path(root, job)
    doc = json.loads(path.read_text(encoding='utf-8'))
    if doc.get('schema_version') != 1 or doc.get('root') != str(root) or doc.get('job') != job:
        raise ValueError('State identity/version mismatch; use the original root/job or a new task.')
    if set(doc.get('active', [])) - set(by_id):
        raise ValueError('State references unknown skills.')
    if set(doc.get('stages', {})) != set(doc['active']):
        raise ValueError('State stages and active stages differ.')
    if any(record.get('status') not in STATUSES for record in doc['stages'].values()):
        raise ValueError('Invalid stage status.')
    return path, doc


def snapshot(root, stage, brief):
    result = {}
    for pattern in stage['watch']:
        if pattern == '@brief':
            result[pattern] = canonical_hash(brief)
        elif pattern in ('@audio', '@lyrics'):
            path = input_path(root, brief.get(pattern[1:]))
            result[pattern] = {'path': str(path) if path else None,
                               'fingerprint': fingerprint(path) if path else {'exists': False}}
        else:
            paths = sorted(path for path in root.glob(pattern) if path.is_file())
            result[pattern] = {str(path.relative_to(root)): fingerprint(path) for path in paths}
    return result


def dependency_token(record):
    return canonical_hash({key: record.get(key) for key in
                           ('evidence', 'watch_snapshot', 'dependency_snapshot')})


def effective_states(root, doc, by_id):
    active = set(doc['active'])
    result = {}

    def check(step):
        if step in result:
            return result[step]
        record = doc['stages'][step]
        status = record['status']
        causes = []
        parents = [parent for parent in by_id[step]['dependencies'] if parent in active]
        parent_states = {parent: check(parent)['status'] for parent in parents}
        if status == 'done':
            if record.get('watch_snapshot') != snapshot(root, by_id[step], doc['brief']):
                causes.append('watched inputs changed')
            evidence = record.get('evidence', {})
            if not evidence:
                causes.append('no recorded evidence')
            for relative, recorded in evidence.items():
                if fingerprint(under_root(root, relative)) != recorded:
                    causes.append(f'evidence changed/missing: {relative}')
            for parent in parents:
                if parent_states[parent] != 'done':
                    causes.append(f'dependency not verified: {parent}')
                elif record.get('dependency_snapshot', {}).get(parent) != dependency_token(doc['stages'][parent]):
                    causes.append(f'dependency evidence changed: {parent}')
            if causes:
                status = 'stale'
        result[step] = {'status': status, 'recorded_status': record['status'],
                        'causes': causes, 'dependencies': parent_states}
        return result[step]

    for step in doc['active']:
        check(step)
    return result


def summarize(root, doc, by_id):
    states = effective_states(root, doc, by_id)
    ready, waiting, humans = [], [], []
    for step in doc['active']:
        current = states[step]
        record = doc['stages'][step]
        if current['status'] == 'done':
            continue
        if current['status'] == 'needs_input':
            humans.append({'skill': step, 'reason': record.get('reason', ''),
                           'action': record.get('human_action', '')})
        elif all(status == 'done' for status in current['dependencies'].values()):
            ready.append(step)
        else:
            waiting.append(step)
    return {'job': doc['job'], 'mode': doc['mode'], 'root': str(root),
            'brief': doc['brief'], 'complete': all(x['status'] == 'done' for x in states.values()),
            'ready': ready, 'next_skill': ready[0] if ready else None,
            'human_actions': humans, 'waiting_for_dependencies': waiting, 'stages': states}


def run_command(args, timeout=8):
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return {'returncode': proc.returncode, 'stdout': proc.stdout.strip(),
                'stderr': proc.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'error': str(exc)}


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_timing(root):
    errors, counts = [], {}
    audio_path, lyrics_path = root / 'data/audio.json', root / 'data/lyrics.json'
    if not audio_path.is_file() or not lyrics_path.is_file():
        return {'valid': False, 'errors': ['formal audio.json or lyrics.json missing']}
    try:
        audio, lyrics = read_json(audio_path), read_json(lyrics_path)
        duration, fps = audio['duration'], audio['fps']
        if not finite_number(duration) or duration <= 0 or not finite_number(fps) or fps <= 0:
            raise ValueError('invalid duration/fps')
        if not finite_number(audio.get('bpm')) or audio['bpm'] <= 0:
            errors.append('invalid bpm')
        for key in ('beats', 'downbeats'):
            values = audio[key]
            if not values or any(not finite_number(x) or not 0 <= x <= duration for x in values):
                errors.append(f'{key}: missing/nonfinite/out-of-range')
            elif any(a >= b for a, b in zip(values, values[1:])):
                errors.append(f'{key}: not increasing')
            counts[key] = len(values)
        for key in ('rms', 'low', 'mid', 'high', 'vocal', 'drums', 'bass', 'other'):
            values = audio.get('features', {}).get(key, audio.get(key, []))
            if abs(len(values) - math.ceil(duration * fps)) > 1:
                errors.append(f'{key}: wrong envelope length')
            if any(not finite_number(x) or not 0 <= x <= 1 for x in values):
                errors.append(f'{key}: invalid envelope value')
        previous_end = 0
        for section in audio['sections']:
            start, end = section['start'], section['end']
            if not all(finite_number(x) for x in (start, end)) or not 0 <= start < end <= duration:
                errors.append('invalid section span')
            elif start < previous_end - 1e-6:
                errors.append('sections overlap/out of order')
            previous_end = end
        for key in ('kick', 'snare', 'hat', 'vocal'):
            previous = -1
            for event in audio.get('onsets', {}).get(key, []):
                time, strength = event
                if not all(finite_number(x) for x in event) or not 0 <= time <= duration or not 0 <= strength <= 1:
                    errors.append(f'{key}: invalid onset')
                elif time < previous:
                    errors.append(f'{key}: onsets out of order')
                previous = time
        words = [word for line in lyrics['lines'] for word in line['words']]
        previous_end = 0
        for index, word in enumerate(words):
            start, end = word['start'], word['end']
            if not isinstance(word['w'], str) or not word['w']:
                errors.append(f'word {index}: empty/non-string token')
            if not all(finite_number(x) for x in (start, end)) or not 0 <= start < end <= duration:
                errors.append(f'word {index}: invalid span')
                continue
            if start < previous_end - 1e-6:
                errors.append(f'word {index}: overlap/out of order')
            previous_end = end
            syllable_end = start
            for a, b in word.get('syl', []):
                if not all(finite_number(x) for x in (a, b)) or not start <= a < b <= end or a < syllable_end - 1e-6:
                    errors.append(f'word {index}: invalid syllables')
                syllable_end = b
            if 'conf' in word and (not finite_number(word['conf']) or not 0 <= word['conf'] <= 1):
                errors.append(f'word {index}: invalid confidence')
        for index, line in enumerate(lyrics['lines']):
            if not line['words'] or not isinstance(line['text'], str):
                errors.append(f'line {index}: missing words/text')
                continue
            if abs(line['start'] - line['words'][0]['start']) > 0.002 or abs(line['end'] - line['words'][-1]['end']) > 0.002:
                errors.append(f'line {index}: boundaries do not match words')
            if line['text'].split() != [word['w'] for word in line['words']]:
                errors.append(f'line {index}: text/tokens mismatch')
        counts.update(duration=duration, fps=fps, lines=len(lyrics['lines']), words=len(words))
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        errors.append(f'malformed timing JSON: {exc}')
    return {'valid': not errors, 'errors': errors, 'counts': counts,
            'scope': 'structural checks only; song identity, listening and visual sync require review'}


def inspect(root, audio_value='audio/pdoom.mp3', lyrics_value='lyrics/lyrics.src.js'):
    audio = input_path(root, audio_value)
    lyrics = input_path(root, lyrics_value)
    media = {'path': str(audio) if audio else None, 'exists': bool(audio and audio.is_file())}
    if media['exists'] and shutil.which('ffprobe'):
        probe = run_command(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(audio)])
        if probe.get('returncode') == 0:
            try:
                media['probe'] = json.loads(probe['stdout'])
            except ValueError:
                media['error'] = 'ffprobe returned invalid JSON'
        else:
            media['error'] = probe
    elif media['exists']:
        media['unverified'] = 'ffprobe unavailable'
    lyric_info = {'path': str(lyrics) if lyrics else None, 'exists': bool(lyrics and lyrics.is_file())}
    if lyric_info['exists']:
        try:
            text = lyrics.read_text(encoding='utf-8')
            rows = json.loads(text[text.index('['):text.rindex(']') + 1])
            if not rows or any(len(row) != 3 or not all(finite_number(x) for x in row[:2])
                               or not 0 <= row[0] < row[1] or not isinstance(row[2], str)
                               or not row[2].strip() for row in rows):
                raise ValueError('expected nonempty [start,end,text] rows')
            lyric_info['valid'] = True
            lyric_info['lines'] = len(rows)
        except (OSError, ValueError, TypeError, IndexError) as exc:
            lyric_info.update(valid=False, error=str(exc))
    tools = {}
    for name in ('python3', 'uv', 'bun', 'ffmpeg', 'ffprobe', 'google-chrome', 'chromium'):
        tools[name] = shutil.which(name)
    paths = ['analysis/.venv/pyvenv.cfg', 'app/node_modules', 'analysis/.cache',
             'analysis/stems', 'analysis/work', 'docs/TREATMENT.md', 'app/src/timeline.ts']
    source_snapshot = None
    marker = root / '.pv-project-source.json'
    if marker.is_file():
        try:
            source = read_json(marker)
            missing = []
            for relative in source.get('excluded_asset_paths', []):
                path = Path(relative)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Invalid reference asset path in project marker.')
                if not (root / path).exists():
                    missing.append(relative)
            source_snapshot = {'repository': source.get('repository'), 'commit': source.get('commit'),
                               'bundled_code_files': len(source.get('files', [])),
                               'missing_reference_assets': missing,
                               'scope': 'Reference assets omitted from template; required assets depend on the adapted project.'}
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            source_snapshot = {'error': str(exc)}
    return {'root': str(root), 'platform': platform.system(), 'architecture': platform.machine(),
            'audio': media, 'lyrics': lyric_info, 'tools': tools,
            'free_disk_bytes': shutil.disk_usage(root).free,
            'artifacts': {path: (root / path).exists() for path in paths},
            'source_snapshot': source_snapshot,
            'timing': check_timing(root),
            'montage_images': len(list((root / 'app/public/plates').glob('fig*.jpg'))),
            'note': 'Existence is not stage completion; no packages/models installed by inspect.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'catalog', 'init', 'status', 'configure',
                                            'mark', 'finish', 'enable', 'reopen'])
    parser.add_argument('--root')
    parser.add_argument('--job')
    parser.add_argument('--mode')
    parser.add_argument('--audio')
    parser.add_argument('--lyrics')
    parser.add_argument('--language', default='unknown')
    parser.add_argument('--brief', help='JSON object merged into brief')
    parser.add_argument('--step')
    parser.add_argument('--status', choices=sorted(STATUSES - {'done'}))
    parser.add_argument('--reason', default='')
    parser.add_argument('--human', default='')
    parser.add_argument('--evidence', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        catalog, by_id = manifest()
        if args.command == 'catalog':
            emit(catalog)
            return 0
        root = find_root(args.root)
        if args.command == 'inspect':
            if args.job:
                _, existing = load_state(root, args.job, by_id)
                audio = args.audio or existing['brief'].get('audio')
                lyrics = args.lyrics or existing['brief'].get('lyrics')
            else:
                audio = args.audio or 'audio/pdoom.mp3'
                lyrics = args.lyrics or 'lyrics/lyrics.src.js'
            emit(inspect(root, audio, lyrics))
            return 0
        if args.command == 'init':
            path = state_path(root, args.job)
            if path.exists():
                raise ValueError('Task already exists; use status/configure or a new job, never overwrite.')
            if args.mode not in catalog['modes']:
                raise ValueError('--mode must be one of: ' + ', '.join(catalog['modes']))
            brief = {'audio': args.audio or ('audio/pdoom.mp3' if args.mode != 'new-song' else None),
                     'lyrics': args.lyrics or ('lyrics/lyrics.src.js' if args.mode != 'new-song' else None),
                     'language': args.language, 'target': {'width': 1920, 'height': 1080, 'fps': 60},
                     'target_assumption': '1080p60 until user requirements specify otherwise'}
            if args.brief:
                extra = read_json(input_path(root, args.brief))
                if not isinstance(extra, dict):
                    raise ValueError('brief must be a JSON object')
                brief.update(extra)
            active = [stage['id'] for stage in catalog['stages'] if args.mode in stage['modes']]
            doc = {'schema_version': 1, 'root': str(root), 'job': args.job, 'mode': args.mode,
                   'brief': brief, 'active': active,
                   'stages': {step: {'status': 'pending'} for step in active}}
            atomic_json(path, doc)
            emit(summarize(root, doc, by_id))
            return 0
        path, doc = load_state(root, args.job, by_id)
        if args.command == 'status':
            emit(summarize(root, doc, by_id))
            return 0
        if args.command == 'configure':
            if not args.brief:
                raise ValueError('configure needs --brief JSON file')
            extra = read_json(input_path(root, args.brief))
            if not isinstance(extra, dict):
                raise ValueError('brief must be a JSON object')
            doc['brief'].update(extra)
        else:
            if args.step not in by_id:
                raise ValueError('Unknown --step; see catalog.')
            if args.command == 'enable':
                if args.step not in doc['active']:
                    selected = set(doc['active']) | {args.step}
                    doc['active'] = [stage['id'] for stage in catalog['stages'] if stage['id'] in selected]
                    doc['stages'][args.step] = {'status': 'pending'}
            else:
                if args.step not in doc['active']:
                    raise ValueError('Stage not active in this task; enable it if actually required.')
                record = doc['stages'][args.step]
                if args.command in ('mark', 'reopen'):
                    target = 'pending' if args.command == 'reopen' else args.status
                    if not target:
                        raise ValueError('mark needs --status')
                    if target == 'needs_input' and not args.human:
                        raise ValueError('needs_input requires a concrete --human action')
                    record.update(status=target, reason=args.reason, human_action=args.human)
                elif args.command == 'finish':
                    current = effective_states(root, doc, by_id)[args.step]
                    unfinished = [step for step, status in current['dependencies'].items() if status != 'done']
                    if unfinished:
                        raise ValueError('Unverified dependencies: ' + ', '.join(unfinished))
                    if not args.evidence:
                        raise ValueError('finish requires actual --evidence files, not just a status change')
                    if args.step == 'pv-input-check':
                        audio = input_path(root, doc['brief'].get('audio'))
                        lyrics = input_path(root, doc['brief'].get('lyrics'))
                        if not audio or not audio.is_file() or audio.stat().st_size == 0:
                            raise ValueError('Input check cannot complete without a real, nonempty audio file.')
                        if not doc['brief'].get('instrumental') and (not lyrics or not lyrics.is_file() or lyrics.stat().st_size == 0):
                            raise ValueError('Input check needs lyrics or an explicit instrumental requirement.')
                    evidence = {}
                    for value in args.evidence:
                        artifact = under_root(root, value)
                        if not artifact.is_file() or artifact.stat().st_size == 0:
                            raise ValueError(f'Evidence missing or empty: {value}')
                        if artifact == path:
                            raise ValueError('workflow.json cannot be its own evidence')
                        if artifact.suffix == '.json':
                            canonical_hash(read_json(artifact))
                        evidence[str(artifact.relative_to(root))] = fingerprint(artifact)
                    parents = current['dependencies']
                    record.update(status='done', reason=args.reason, human_action='', evidence=evidence,
                                  watch_snapshot=snapshot(root, by_id[args.step], doc['brief']),
                                  dependency_snapshot={parent: dependency_token(doc['stages'][parent]) for parent in parents})
        atomic_json(path, doc)
        emit(summarize(root, doc, by_id))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'workflow: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
