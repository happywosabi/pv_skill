"""Behavioral checks for resumability, stale evidence and bounded installation."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pv_workflow', HERE / 'workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pv-workflow-')
        self.root = Path(self.temporary.name)
        for directory in ('app', 'analysis', 'audio', 'lyrics', 'data'):
            (self.root / directory).mkdir()
        with wave.open(str(self.root / 'audio/song.wav'), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(16000)
            stream.writeframes(b'\x00\x00' * 32000)
        (self.root / 'lyrics/song.src.js').write_text('const LY = [[0, 1, "la"]];', encoding='utf-8')

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, command, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = workflow.main([command, '--root', str(self.root), '--job', 'test', *args])
        value = json.loads(output.getvalue()) if output.getvalue().strip() else None
        return code, value, errors.getvalue()

    def init(self, mode='existing-render', inputs=True):
        args = ['--mode', mode]
        if inputs:
            args += ['--audio', 'audio/song.wav', '--lyrics', 'lyrics/song.src.js']
        code, _, error = self.run_cli('init', *args)
        self.assertEqual(code, 0, error)

    def evidence(self, name):
        path = self.root / f'{name}.md'
        path.write_text(f'Actual test evidence for {name}.', encoding='utf-8')
        return path.name

    def finish(self, step):
        code, result, error = self.run_cli('finish', '--step', step, '--evidence', self.evidence(step))
        self.assertEqual(code, 0, error)
        return result

    def test_render_mode_skips_analysis_models(self):
        self.init()
        _, state, _ = self.run_cli('status')
        self.assertNotIn('pv-python-setup', state['stages'])
        self.assertNotIn('pv-model-setup', state['stages'])
        self.assertIn('pv-input-check', state['ready'])
        self.assertIn('pv-environment-check', state['ready'])

    def test_analysis_mode_skips_video_and_finishes_at_timing_review(self):
        self.init('repair-analysis')
        _, state, _ = self.run_cli('status')
        self.assertNotIn('pv-export', state['stages'])
        self.assertNotIn('pv-renderer-setup', state['stages'])
        self.assertIn('pv-timing-review', state['stages'])

    def test_missing_new_song_does_not_reuse_original_inputs(self):
        self.init('new-song', inputs=False)
        code, result, _ = self.run_cli('inspect')
        self.assertEqual(code, 0)
        self.assertFalse(result['audio']['exists'])
        self.assertIsNone(result['audio']['path'])
        code, _, error = self.run_cli('finish', '--step', 'pv-input-check', '--evidence', self.evidence('input'))
        self.assertEqual(code, 2)
        self.assertIn('audio file', error)

    def test_finish_refuses_dependency_and_missing_evidence(self):
        self.init()
        code, _, error = self.run_cli('finish', '--step', 'pv-export', '--evidence', self.evidence('export'))
        self.assertEqual(code, 2)
        self.assertIn('dependencies', error)
        code, _, error = self.run_cli('finish', '--step', 'pv-input-check')
        self.assertEqual(code, 2)
        self.assertIn('evidence', error)

    def test_input_change_invalidates_completed_downstream(self):
        self.init()
        self.finish('pv-input-check')
        self.finish('pv-environment-check')
        self.finish('pv-runtime-setup')
        self.finish('pv-renderer-setup')
        self.finish('pv-preview-review')
        (self.root / 'audio/song.wav').write_bytes(b'different song')
        _, state, _ = self.run_cli('status')
        self.assertEqual(state['stages']['pv-input-check']['status'], 'stale')
        self.assertEqual(state['stages']['pv-preview-review']['status'], 'stale')
        self.assertFalse(state['complete'])

    def test_deleted_evidence_invalidates_and_status_is_read_only(self):
        self.init()
        self.finish('pv-input-check')
        path = self.root / 'out/pv/test/workflow.json'
        before = path.read_bytes()
        (self.root / 'pv-input-check.md').unlink()
        _, state, _ = self.run_cli('status')
        self.assertEqual(state['stages']['pv-input-check']['status'], 'stale')
        self.assertEqual(path.read_bytes(), before)

    def test_waiting_for_human_does_not_block_independent_environment_work(self):
        self.init('new-song')
        code, _, _ = self.run_cli('mark', '--step', 'pv-input-check', '--status', 'needs_input',
                                  '--reason', 'Wrong lyric version', '--human', 'Provide matching lyrics')
        self.assertEqual(code, 0)
        _, state, _ = self.run_cli('status')
        self.assertNotIn('pv-input-check', state['ready'])
        self.assertIn('pv-environment-check', state['ready'])
        self.assertEqual(state['human_actions'][0]['action'], 'Provide matching lyrics')

    def test_reopen_invalidates_dependency_even_without_file_change(self):
        self.init()
        self.finish('pv-environment-check')
        self.finish('pv-runtime-setup')
        self.run_cli('reopen', '--step', 'pv-environment-check', '--reason', 'Moved to another machine')
        _, state, _ = self.run_cli('status')
        self.assertEqual(state['stages']['pv-runtime-setup']['status'], 'stale')

    def test_changed_brief_invalidates_source_decisions(self):
        self.init()
        self.finish('pv-input-check')
        brief = self.root / 'brief.json'
        brief.write_text(json.dumps({'target': {'width': 3840, 'height': 2160, 'fps': 60}}))
        self.run_cli('configure', '--brief', str(brief))
        _, state, _ = self.run_cli('status')
        self.assertEqual(state['stages']['pv-input-check']['status'], 'stale')

    def test_optional_repair_can_be_enabled_and_unknown_skill_is_rejected(self):
        self.init()
        code, state, error = self.run_cli('enable', '--step', 'pv-renderer-repair')
        self.assertEqual(code, 0, error)
        self.assertIn('pv-renderer-repair', state['stages'])
        code, _, _ = self.run_cli('enable', '--step', 'not-a-skill')
        self.assertEqual(code, 2)

    def test_task_and_evidence_paths_cannot_escape_root(self):
        with self.assertRaises(ValueError):
            workflow.state_path(self.root, '../escape')
        self.init()
        code, _, error = self.run_cli('finish', '--step', 'pv-environment-check', '--evidence', '/etc/passwd')
        self.assertEqual(code, 2)
        self.assertIn('inside project root', error)

    def test_init_never_overwrites_existing_task(self):
        self.init()
        code, _, error = self.run_cli('init', '--mode', 'new-song')
        self.assertEqual(code, 2)
        self.assertIn('already exists', error)

    def test_source_lyric_js_is_parsed_without_execution(self):
        path = self.root / 'lyrics/song.src.js'
        path.write_text('throw new Error("must not execute"); const LY = [[0, 1, "la"]];')
        result = workflow.inspect(self.root, 'audio/song.wav', 'lyrics/song.src.js')
        self.assertTrue(result['lyrics']['valid'])
        self.assertEqual(result['lyrics']['lines'], 1)

    def test_timing_nan_and_wrong_envelope_are_rejected(self):
        audio = {'duration': 2, 'fps': 1, 'bpm': 120, 'beats': [0, 1], 'downbeats': [0],
                 'sections': [{'name': 'verse', 'start': 0, 'end': 2}], 'onsets': {}}
        for key in ('rms', 'low', 'mid', 'high', 'vocal', 'drums', 'bass', 'other'):
            audio[key] = [0.2, 0.3]
        lyrics = {'lines': [{'text': 'la', 'start': 0, 'end': 1,
                             'words': [{'w': 'la', 'start': 0, 'end': 1}]}]}
        (self.root / 'data/audio.json').write_text(json.dumps(audio))
        (self.root / 'data/lyrics.json').write_text(json.dumps(lyrics))
        self.assertTrue(workflow.check_timing(self.root)['valid'])
        audio['rms'] = [float('nan')]
        audio['low'] = []
        (self.root / 'data/audio.json').write_text(json.dumps(audio))
        self.assertFalse(workflow.check_timing(self.root)['valid'])


class InstallerTests(unittest.TestCase):
    def test_full_preflight_refuses_conflict_without_installing_other_skills(self):
        with tempfile.TemporaryDirectory(prefix='pv-install-test-') as name:
            root = Path(name)
            source, dest = root / 'source', root / 'dest'
            for skill in ('pv-plan', 'pv-input-check'):
                path = source / skill
                path.mkdir(parents=True)
                (path / 'SKILL.md').write_text('source')
            conflict = dest / 'pv-plan'
            conflict.mkdir(parents=True)
            (conflict / 'SKILL.md').write_text('user-owned')
            result = subprocess.run([sys.executable, str(HERE / 'install.py'), '--source', str(source),
                                     '--dest', str(dest), '--apply'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual((conflict / 'SKILL.md').read_text(), 'user-owned')
            self.assertFalse((dest / 'pv-input-check').exists())

    def test_install_and_idempotent_reinstall(self):
        with tempfile.TemporaryDirectory(prefix='pv-install-test-') as name:
            root = Path(name)
            source, dest = root / 'source', root / 'dest'
            path = source / 'pv-plan'
            path.mkdir(parents=True)
            (path / 'SKILL.md').write_text('source')
            args = [sys.executable, str(HERE / 'install.py'), '--source', str(source), '--dest', str(dest), '--apply']
            first = subprocess.run(args, capture_output=True, text=True)
            second = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn('0 new', second.stdout)


if __name__ == '__main__':
    unittest.main()
