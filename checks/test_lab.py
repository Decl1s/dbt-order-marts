"""Контракт безопасной мастерской без mock-подмены SQL. Настоящий dbt — в smoke."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', ROOT / 'scripts/lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class LabTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ['dbt_project.yml', 'profiles/profiles.yml', 'scripts/lab.py', 'models/a.sql']:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('synthetic')

    def test_prepare_refuses_overwrite(self):
        lab.prepare(self.root)
        p = self.root / 'workspace/seeds/raw_orders.csv'
        p.write_text('моя учебная правка')
        with self.assertRaises(FileExistsError):
            lab.prepare(self.root)
        self.assertEqual(p.read_text(), 'моя учебная правка')

    def test_generator_reproducible(self):
        lab.prepare(self.root)
        actual = (self.root / 'workspace/seeds/raw_refunds.csv').read_text()
        self.assertEqual(actual.count('O0001'), 2)
        self.assertIn('R0001,O0001,2000', actual)

    def test_missing_and_extra_inputs_rejected(self):
        with self.assertRaises(ValueError):
            lab.fingerprint(self.root)
        lab.prepare(self.root)
        (self.root / 'workspace/seeds/extra.csv').write_text('x')
        with self.assertRaises(ValueError):
            lab.fingerprint(self.root)

    def test_large_input_rejected(self):
        lab.prepare(self.root)
        (self.root / 'workspace/seeds/raw_orders.csv').write_bytes(b'x' * 1_000_001)
        with self.assertRaises(ValueError):
            lab.fingerprint(self.root)

    def test_fingerprint_changes_with_sql_and_csv(self):
        lab.prepare(self.root)
        before = lab.fingerprint(self.root)
        p = self.root / 'models/a.sql'
        p.write_text('changed')
        self.assertNotEqual(before, lab.fingerprint(self.root))
        before = lab.fingerprint(self.root)
        p = self.root / 'workspace/seeds/raw_refunds.csv'
        p.write_text(p.read_text() + '\n')
        self.assertNotEqual(before, lab.fingerprint(self.root))

    def test_report_rejects_failed_build(self):
        lab.prepare(self.root)
        lab.save_state(self.root, {'status': 'failed'})
        with self.assertRaises(ValueError):
            lab.report(self.root)

    def test_report_rejects_stale_input(self):
        lab.prepare(self.root)
        lab.save_state(self.root, {'status': 'success', 'fingerprint': lab.fingerprint(self.root), 'report': {'net_cents': 77000}})
        self.assertEqual(lab.report(self.root)['net_cents'], 77000)
        (self.root / 'models/a.sql').write_text('changed')
        with self.assertRaises(ValueError):
            lab.report(self.root)

    def test_build_records_failed_before_query(self):
        lab.prepare(self.root)
        with patch.object(lab.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['dbt'])):
            with self.assertRaises(subprocess.CalledProcessError):
                lab.build(self.root)
        state = json.loads((self.root / 'workspace/last_build.json').read_text())
        self.assertEqual(state['status'], 'failed')

    def test_invalid_case_does_not_create_input(self):
        with self.assertRaises(ValueError):
            lab.prepare(self.root, 'unknown')
        self.assertFalse((self.root / 'workspace/seeds').exists())


if __name__ == '__main__':
    unittest.main()
