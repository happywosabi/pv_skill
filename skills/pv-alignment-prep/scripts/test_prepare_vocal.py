"""Real WAV round-trip and overwrite behavior; requires numpy and soundfile."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf


spec = importlib.util.spec_from_file_location('prepare_vocal', Path(__file__).with_name('prepare_vocal.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class PrepareVocalTests(unittest.TestCase):
    def test_round_trip_and_reuse_without_reapplying_calibration(self):
        with tempfile.TemporaryDirectory(prefix='pv-vocal-test-') as name:
            target = Path(name) / 'work/vocals16k.wav'
            samples = np.sin(np.arange(1600) * 0.1).astype(np.float32) * 0.25
            self.assertEqual(helper.store_wav(samples, 16000, target), 'written')
            result, rate = sf.read(target, dtype='float32')
            self.assertEqual(rate, 16000)
            np.testing.assert_array_equal(result, samples)
            before = target.stat().st_mtime_ns
            self.assertEqual(helper.store_wav(samples, 16000, target), 'reused')
            self.assertEqual(target.stat().st_mtime_ns, before)

    def test_different_existing_input_is_preserved_until_explicit_replace(self):
        with tempfile.TemporaryDirectory(prefix='pv-vocal-test-') as name:
            target = Path(name) / 'vocals16k.wav'
            original = np.full(100, 0.1, dtype=np.float32)
            replacement = np.full(200, 0.2, dtype=np.float32)
            helper.store_wav(original, 16000, target)
            with self.assertRaises(ValueError):
                helper.store_wav(replacement, 16000, target)
            result, _ = sf.read(target, dtype='float32')
            np.testing.assert_array_equal(result, original)
            self.assertEqual(helper.store_wav(replacement, 16000, target, replace=True), 'written')
            result, _ = sf.read(target, dtype='float32')
            np.testing.assert_array_equal(result, replacement)

    def test_wrong_rate_stereo_nan_and_empty_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='pv-vocal-test-') as name:
            target = Path(name) / 'vocals16k.wav'
            for samples, rate in [(np.zeros(100), 44100), (np.zeros((100, 2)), 16000),
                                  (np.array([float('nan')]), 16000), (np.array([]), 16000)]:
                with self.subTest(rate=rate, shape=samples.shape):
                    with self.assertRaises(ValueError):
                        helper.store_wav(samples, rate, target)
            self.assertFalse(target.exists())

    def test_cli_uses_project_calibration_exactly_once(self):
        with tempfile.TemporaryDirectory(prefix='pv-vocal-cli-') as name:
            root = Path(name)
            analysis = root / 'analysis'
            analysis.mkdir()
            samples = np.linspace(-0.25, 0.25, 1600, dtype=np.float32)
            sf.write(analysis / 'vocals.wav', samples, 16000, subtype='FLOAT')
            (analysis / 'common.py').write_text(
                "from pathlib import Path\n"
                "ROOT = Path(__file__).resolve().parent\n"
                "WORK = ROOT / 'work'\n"
                "def load_stem(name, sr):\n"
                "    import soundfile as sf\n"
                "    y, rate = sf.read(ROOT / 'vocals.wav', dtype='float32')\n"
                "    assert name == 'vocals' and sr == rate == 16000\n"
                "    return y[7:], rate\n"
            )
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_vocal.py')),
                                     '--root', str(root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['samples'], len(samples) - 7)
            generated, rate = sf.read(analysis / 'work/vocals16k.wav', dtype='float32')
            self.assertEqual(rate, 16000)
            np.testing.assert_array_equal(generated, samples[7:])


if __name__ == '__main__':
    unittest.main()
