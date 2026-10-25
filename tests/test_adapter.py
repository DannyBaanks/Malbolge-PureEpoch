import unittest
from pathlib import Path
from tools import build_candidates


class OfflineAdapter(unittest.TestCase):
    def api(self):
        try:
            from tools import autobolge_adapter
        except ImportError:
            self.fail('offline Autobolge bridge missing')
        return autobolge_adapter

    def test_eof_semantic_difference_is_exposed(self):
        result = self.api().eof_probe()
        self.assertEqual(result['strict']['a'], 59048)
        self.assertEqual(result['strict']['terminal'], 'HALT')
        self.assertEqual(result['autobolge']['a'], 0)
        self.assertEqual(result['autobolge']['reason'], 'StopReason.INPUT_UNDERFLOW')

    def test_real_autobolge_encoder_and_anchor_match_supported_strict_run(self):
        result = self.api().bridge(b'\x03\x03')
        self.assertTrue(result['same_source'])
        self.assertTrue(result['strict_state_parity'])
        self.assertEqual(result['anchor_at_restore']['target_value'], 29521)
        self.assertEqual(result['anchor_at_restore']['journal_value'], 3)


if __name__ == '__main__':
    unittest.main()
