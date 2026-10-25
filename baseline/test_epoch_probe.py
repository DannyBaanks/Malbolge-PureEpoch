"""Finite experiment assertions. Run: python3 -m unittest -v test_epoch_probe.py"""
import hashlib
from pathlib import Path
import unittest

from epoch_probe import analyze, load

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "truth_machine_classic_90b.mal"
PUBLISHED_SHA256 = "1e34e2afd1fc645dadac1f1aac0fe2348ff469878cc3da396a6a1e7bad2a4417"

class PureEpochProbeTests(unittest.TestCase):
    def test_authentic_source(self):
        raw = SOURCE.read_bytes()
        self.assertEqual(len(raw), 90)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PUBLISHED_SHA256)
        self.assertEqual(len(load(raw)), 59049)

    def test_cycle_positive(self):
        result = analyze(SOURCE.read_bytes(), b'1')
        self.assertEqual(result['verdict'], 'DEMONSTRATED_CYCLE')
        self.assertEqual(result['cycle']['period'], 408)
        self.assertGreater(result['cycle']['modified_cell_count'], 0)
        self.assertEqual(result['cycle']['modified_cell_count'], result['cycle']['modified_cells_returned_to_anchor'])
        self.assertEqual(result['cycle']['output_growth'], 17)
        self.assertEqual(result['cycle']['output_during_cycle'], (b'1'*17).hex())
        self.assertEqual(result['cycle']['end_step'], 1408)

    def test_negative_external_fault_is_not_repaired(self):
        result = analyze(SOURCE.read_bytes(), b'1')
        neg = result['negative_control']
        self.assertIsNotNone(neg)
        self.assertFalse(neg['cell_restored_by_malbolge'])
        self.assertFalse(neg['full_anchor_state_restored'])

    def test_zero_branch_halts_not_cycle(self):
        result = analyze(SOURCE.read_bytes(), b'0', warmup=0, max_steps=100)
        self.assertEqual(result['status'], 'HALT')
        self.assertEqual(result['verdict'], 'NOT_DEMONSTRATED')

    def test_loader_rejects_corrupt_header(self):
        with self.assertRaises(ValueError):
            load(b'AA')

if __name__ == '__main__': unittest.main()
