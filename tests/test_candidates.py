"""Behavioral gates: fail on missing recovery or output-only impostors."""
import unittest


class Candidates(unittest.TestCase):
    def api(self):
        try:
            from tools import build_candidates, observe
        except ImportError:
            self.fail('offline assembler and observer not implemented')
        return build_candidates, observe

    def test_ten_rotations_restore_selected_cell_and_halt(self):
        build, observer = self.api()
        source, _ = build.build_reversible()
        result = observer.run(source, b'')
        self.assertEqual(result['terminal'], 'HALT')
        self.assertEqual(result['memory'][96], 37)
        self.assertEqual(result['output'], b'%')
        changes = [v for e in result['trace'] for v in e['changes'] if v[0] == 96]
        self.assertEqual(len(changes), 10)
        self.assertEqual(changes[0], [96, 37, 19695])
        self.assertEqual(changes[-1][2], 37)

    def test_nine_rotations_are_not_a_restore(self):
        build, observer = self.api()
        source, _ = build.build_reversible(rotations=9)
        result = observer.run(source, b'')
        self.assertEqual(result['terminal'], 'HALT')
        self.assertNotEqual(result['memory'][96], 37)

    def test_journal_restores_two_different_runtime_values(self):
        build, observer = self.api()
        source, _ = build.build_checkpoint()
        for payload, value, journal, output in [(b'\x01\x00', 29523, 1, b'S'), (b'\x03\x00', 29521, 3, b'Q')]:
            with self.subTest(payload=payload):
                result = observer.run(source, payload)
                self.assertEqual(result['terminal'], 'HALT')
                self.assertEqual(result['memory'][36], value)
                self.assertEqual(result['memory'][52], journal)
                self.assertEqual(result['output'], output)
                target_writes = [v for e in result['trace'] for v in e['changes'] if v[0] == 36]
                self.assertEqual([v[2] for v in target_writes], [value, 29524, value])

    def test_missing_or_corrupted_journal_destroys_restore(self):
        build, observer = self.api()
        for mode in ['no_save', 'corrupt_journal', 'early_halt']:
            source, _ = build.build_checkpoint(mode)
            result = observer.run(source, b'\x01\x00')
            self.assertFalse(observer.target_contract(result, 36, 29523), mode)

    def test_output_only_impostor_is_rejected_by_memory_contract(self):
        build, observer = self.api()
        source, _ = build.build_checkpoint('output_impostor')
        result = observer.run(source, b'\x01\x00')
        self.assertEqual(result['terminal'], 'HALT')
        self.assertEqual(result['output'], b'S')
        self.assertFalse(observer.target_contract(result, 36, 29523))

    def test_budget_does_not_become_a_pass(self):
        build, observer = self.api()
        source, _ = build.build_checkpoint()
        result = observer.run(source, b'\x01\x00', max_steps=1)
        self.assertEqual(result['terminal'], 'BUDGET')
        self.assertFalse(observer.target_contract(result, 36, 29523))


if __name__ == '__main__':
    unittest.main()
