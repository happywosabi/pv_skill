"""Observable project-copy, provenance and source-integrity behavior."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location('bootstrap_project', Path(__file__).with_name('bootstrap_project.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pv-bootstrap-')
        self.root = Path(self.temporary.name)
        self.snapshot = self.root / 'snapshot'
        self.destination = self.root / 'project'
        self.snapshot.mkdir()
        records = []
        for relative, content in {'analysis/common.py': b'ROOT = 1\n',
                                  'app/scripts/render.ts': b'export {};\n',
                                  'LICENSE': b'Upstream MIT notice\n'}.items():
            path = self.snapshot / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            records.append({'path': relative, 'sha256': hashlib.sha256(content).hexdigest(), 'size': len(content)})
        self.manifest = {'schema_version': 1, 'repository': 'https://github.com/mexicat/pdoom-video',
                         'commit': 'test-commit', 'files': records, 'excluded_asset_paths': ['audio/pdoom.mp3']}
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        (self.snapshot / 'UPSTREAM.json').write_text(json.dumps(self.manifest))

    def test_dry_run_creates_nothing(self):
        result = helper.bootstrap(self.snapshot, self.destination)
        self.assertEqual(result['status'], 'dry_run')
        self.assertEqual(result['files_to_copy'], 3)
        self.assertFalse(self.destination.exists())

    def test_copy_preserves_paths_bytes_and_upstream_notice(self):
        helper.bootstrap(self.snapshot, self.destination, apply=True)
        for record in self.manifest['files']:
            self.assertEqual((self.destination / record['path']).read_bytes(),
                             (self.snapshot / record['path']).read_bytes())
        marker = json.loads((self.destination / helper.MARKER).read_text())
        self.assertEqual(marker['commit'], 'test-commit')
        self.assertFalse((self.destination / 'audio/pdoom.mp3').exists())

    def test_identical_repeat_is_idempotent(self):
        helper.bootstrap(self.snapshot, self.destination, apply=True)
        before = (self.destination / 'analysis/common.py').stat().st_mtime_ns
        result = helper.bootstrap(self.snapshot, self.destination, apply=True)
        self.assertEqual(result['files_to_copy'], 0)
        self.assertEqual(result['identical_files_reused'], 3)
        self.assertEqual((self.destination / 'analysis/common.py').stat().st_mtime_ns, before)

    def test_conflict_refuses_before_any_other_files_are_copied(self):
        path = self.destination / 'app/scripts/render.ts'
        path.parent.mkdir(parents=True)
        path.write_text('user implementation')
        with self.assertRaises(ValueError):
            helper.bootstrap(self.snapshot, self.destination, apply=True)
        self.assertEqual(path.read_text(), 'user implementation')
        self.assertFalse((self.destination / 'analysis').exists())

    def test_corrupt_source_cannot_be_copied(self):
        (self.snapshot / 'analysis/common.py').write_text('changed')
        with self.assertRaises(ValueError):
            helper.bootstrap(self.snapshot, self.destination, apply=True)
        self.assertFalse(self.destination.exists())

    def test_manifest_path_traversal_and_duplicates_are_rejected(self):
        for relative in ('../outside.py', '/outside.py', 'analysis/../outside.py', 'analysis/common.py'):
            with self.subTest(relative=relative):
                self.manifest['files'].append({'path': relative, 'size': 1, 'sha256': 'invalid'})
                self.write_manifest()
                with self.assertRaises(ValueError):
                    helper.bootstrap(self.snapshot, self.destination, apply=True)
                self.manifest['files'].pop()

    def test_copy_into_skill_bundle_is_rejected(self):
        with self.assertRaises(ValueError):
            helper.bootstrap(self.snapshot, Path(__file__).resolve().parents[2] / 'work', apply=True)

    def test_existing_unrelated_assets_are_preserved(self):
        asset = self.destination / 'audio/song.wav'
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b'user song')
        helper.bootstrap(self.snapshot, self.destination, apply=True)
        self.assertEqual(asset.read_bytes(), b'user song')

    def test_work_directory_parent_conflict_is_caught_before_copy(self):
        self.manifest['work_directories'] = ['app/public/fonts/src']
        self.write_manifest()
        path = self.destination / 'app/public'
        path.parent.mkdir(parents=True)
        path.write_text('existing file')
        with self.assertRaises(ValueError):
            helper.bootstrap(self.snapshot, self.destination, apply=True)
        self.assertEqual(path.read_text(), 'existing file')
        self.assertFalse((self.destination / 'analysis').exists())


if __name__ == '__main__':
    unittest.main()
