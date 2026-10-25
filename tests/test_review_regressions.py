"""Regressions for the independent review: oracle stops and reproducibility."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import oracles, autobolge_adapter

ROOT = Path(__file__).resolve().parents[1]


class ReviewRegressions(unittest.TestCase):
    def test_nonzero_independent_halt_cannot_be_certified(self):
        self.assertTrue(hasattr(oracles, 'validate_parity'), 'stop-aware certification gate missing')
        report = {k:True for k in ['trace_equal','memory_equal','registers_equal','terminal_equal','outputs_equal']}
        report.update(terminal='HALT', reference_returncode=0, instrumented_returncode=0, original_returncode=0)
        self.assertTrue(oracles.validate_parity(report))
        for field in ['reference_returncode','instrumented_returncode','original_returncode']:
            bad = dict(report, **{field:3})
            self.assertFalse(oracles.validate_parity(bad), field)
        bounded = dict(report, terminal='BUDGET', reference_returncode=2, instrumented_returncode=2, original_returncode=None)
        self.assertTrue(oracles.validate_parity(bounded))

    def test_vt_and_ff_are_classic_loader_whitespace(self):
        for prefix in [b'\x0b',b'\x0c']:
            with self.subTest(prefix=prefix):
                try:
                    report = oracles.verify(prefix+b'uP', b'')
                except ValueError as error:
                    self.fail(f'valid Classic whitespace rejected by observer: {error}')
                self.assertTrue(oracles.validate_parity(report))
                self.assertEqual(report['registers'][0], 59048)

    def test_loader_and_encryption_divergences_are_reproduced(self):
        self.assertTrue(hasattr(autobolge_adapter, 'semantic_probes'), 'loader/encryption probes missing')
        cases = autobolge_adapter.semantic_probes()
        enc = cases['invalid_encryption']
        self.assertEqual(enc['source_hex'],'2750')
        self.assertEqual(enc['strict_returncode'],3)
        self.assertIn('INVALID_ENCRYPTION',enc['strict_stderr'])
        self.assertEqual(enc['observer']['terminal'],'STALL')
        self.assertEqual(enc['autobolge']['reason'],'StopReason.TERMINATED')
        self.assertEqual(enc['autobolge']['a'],13)
        loader = cases['non_ascii_loader']
        self.assertEqual(loader['source_hex'],'af50')
        self.assertEqual(loader['strict_returncode'],1)
        self.assertEqual(loader['autobolge']['reason'],'StopReason.TERMINATED')

    def test_documented_collection_runs_without_zig_or_source_clones(self):
        with tempfile.TemporaryDirectory() as folder:
            lab = Path(folder)/'lab'
            lab.mkdir()
            for directory in ['baseline','tools','vendor','build']:
                shutil.copytree(ROOT/directory,lab/directory,ignore=shutil.ignore_patterns('__pycache__'))
            (lab/'candidates').mkdir()
            (lab/'evidence').mkdir()
            for name in ['initial_state.json','report-reproduced.json']:
                shutil.copy2(ROOT/'evidence'/name,lab/'evidence'/name)
            binpath = Path(folder)/'bin'
            binpath.mkdir()
            (binpath/'gcc').symlink_to(shutil.which('gcc'))
            env = dict(os.environ,PATH=str(binpath))
            result = subprocess.run([sys.executable,'-B','-m','tools.collect_evidence'],cwd=lab,
                                    env=env,capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,result.stderr[-3000:])
            self.assertTrue((lab/'evidence/manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
