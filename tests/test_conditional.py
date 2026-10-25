import unittest
from tools import build_candidates, observe


class ConditionalRecovery(unittest.TestCase):
    def api(self):
        self.assertTrue(hasattr(build_candidates, 'build_conditional'), 'conditional Classic candidate missing')
        return build_candidates.build_conditional

    def test_same_artifact_commits_or_restores_then_retries(self):
        build = self.api()
        source, meta = build()
        for initial in [1, 3]:
            for candidate in [1, 3]:
                with self.subTest(initial=initial, candidate=candidate):
                    result = observe.run(source, bytes([initial, candidate]))
                    self.assertTrue(observe.conditional_contract(result, meta, initial, candidate))
                    self.assertEqual(result['terminal'], 'HALT')
                    self.assertEqual(result['output'], b'S')
                    self.assertEqual(result['memory'][36], 29523)
                    pcs = [e['pre'][1] for e in result['trace']]
                    self.assertEqual(pcs.count(meta['labels']['restore']), 0 if candidate == 1 else 1)
                    self.assertEqual(pcs.count(meta['labels']['retry']), 0 if candidate == 1 else 1)

    def test_wrong_saved_state_is_rejected_even_if_retry_commits(self):
        build = self.api()
        for mode in ['no_save', 'corrupt_journal', 'no_restore']:
            source, meta = build(mode)
            result = observe.run(source, b'\x03\x03')
            self.assertFalse(observe.conditional_contract(result, meta, 3, 3), mode)

    def test_disabled_recovery_and_broken_return_do_not_pass(self):
        build = self.api()
        for mode in ['no_recovery', 'broken_return', 'early_halt']:
            source, meta = build(mode)
            result = observe.run(source, b'\x01\x03')
            self.assertFalse(observe.conditional_contract(result, meta, 1, 3), mode)

    def test_forced_second_failure_is_not_silently_rescued(self):
        build = self.api()
        source, meta = build('force_retry_failure')
        result = observe.run(source, b'\x03\x03', 1000)
        self.assertFalse(observe.conditional_contract(result, meta, 3, 3))

    def test_positive_case_has_no_output_before_commit(self):
        build = self.api()
        source, meta = build()
        result = observe.run(source, b'\x03\x03')
        emissions = [e for e in result['trace'] if e['output']]
        self.assertEqual(len(emissions), 1)
        self.assertEqual(emissions[0]['pre'][1], 29524)

    def test_all_four_cases_match_strict_c_and_original_olmstead(self):
        from tools.oracles import verify
        source, _ = self.api()()
        for payload in [b'\x01\x01', b'\x01\x03', b'\x03\x01', b'\x03\x03']:
            with self.subTest(payload=payload):
                report = verify(source, payload)
                for key in ['trace_equal', 'memory_equal', 'registers_equal', 'terminal_equal', 'outputs_equal']:
                    self.assertTrue(report[key], key)
                self.assertEqual(report['reference_returncode'], 0)
                self.assertEqual(report['original_returncode'], 0)


if __name__ == '__main__':
    unittest.main()
