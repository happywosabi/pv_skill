#!/usr/bin/env python3
"""Prepare the missing calibrated 16k mono Whisper input without double trimming."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile


def store_wav(y, rate, target, replace=False):
    import numpy as np
    import soundfile as sf

    if rate != 16000 or y.ndim != 1 or not y.size or not np.isfinite(y).all():
        raise ValueError('Expected finite, nonempty 16k mono samples from common.load_stem.')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        old, old_rate = sf.read(target, dtype='float32')
        if old_rate == rate and old.shape == y.shape and np.allclose(old, y, atol=1e-7, rtol=0):
            return 'reused'
        if not replace:
            raise ValueError('Existing vocal input differs; verify its provenance then use --replace to regenerate.')
    descriptor, temporary_name = tempfile.mkstemp(prefix='.vocals16k-', suffix='.wav', dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        sf.write(temporary, y, rate, format='WAV', subtype='FLOAT')
        check, check_rate = sf.read(temporary, dtype='float32')
        if check_rate != rate or check.shape != y.shape or not np.allclose(check, y, atol=1e-7, rtol=0):
            raise ValueError('Prepared WAV did not round-trip correctly.')
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return 'written'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--replace', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(args.root).expanduser().resolve()
        analysis = root / 'analysis'
        if not (analysis / 'common.py').is_file():
            raise ValueError('No project analysis/common.py at --root.')
        sys.path.insert(0, str(analysis))
        common = importlib.import_module('common')  # Cache setup happens before model/audio imports.
        y, rate = common.load_stem('vocals', sr=16000)
        target = (common.WORK / 'vocals16k.wav').resolve()
        if not target.is_relative_to(root):
            raise ValueError('common.WORK output is outside project root.')
        result = store_wav(y, rate, target, replace=args.replace)
        print(json.dumps({'status': result, 'path': str(target), 'sample_rate': rate,
                          'channels': 1, 'samples': len(y), 'duration': len(y) / rate,
                          'calibration': 'applied only by common.load_stem'}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        print(f'prepare_vocal: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
