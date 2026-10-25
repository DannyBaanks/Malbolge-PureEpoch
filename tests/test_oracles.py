import unittest
from tools.build_candidates import build_checkpoint


class OracleParity(unittest.TestCase):
    def test_independent_runs_agree_on_every_transition_and_full_memory(self):
        try:
            from tools.oracles import verify
        except ImportError:
            self.fail('independent oracle verification not implemented')
        source, _ = build_checkpoint()
        for payload in [b'\x01\x00', b'\x03\x00']:
            report = verify(source, payload)
            self.assertTrue(report['trace_equal'])
            self.assertTrue(report['memory_equal'])
            self.assertTrue(report['registers_equal'])
            self.assertTrue(report['outputs_equal'])
            self.assertEqual(report['reference_returncode'], 0)
            self.assertEqual(report['original_returncode'], 0)

    def test_strict_loader_rejection_is_not_certified(self):
        try:
            from tools.oracles import raw_reference
        except ImportError:
            self.fail('strict C oracle not implemented')
        result = raw_reference(b'AA', b'')
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'INVALID_OPCODE', result.stderr)


if __name__ == '__main__':
    unittest.main()
