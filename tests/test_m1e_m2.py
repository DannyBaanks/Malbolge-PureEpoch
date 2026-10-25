"""Tests for NEXT_COMPOSE Steps 1-4: trampoline rearm, M1e, attempt counter, and M2."""
import hashlib
import unittest

from tools import build_candidates, observe
from tools.oracles import verify, validate_parity


class M1eAndM2(unittest.TestCase):
    def test_m1c_normal_sha256_preserved(self):
        source, _ = build_candidates.build_conditional('normal')
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            '17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985',
        )

    def test_step1_trampoline_and_portal_post_encryption_rearm_analysis(self):
        analysis = build_candidates.trampoline_rearm_analysis()
        self.assertEqual(analysis['schema'], 'pure-epoch-trampoline-rearm/v1')
        self.assertGreaterEqual(len(analysis['entries']), 17)
        by_name = {e['name']: e for e in analysis['entries']}
        self.assertEqual(by_name['failure_route']['pre_byte'], 125)
        self.assertEqual(by_name['failure_route']['post_xlat2_byte'], 105)
        self.assertEqual(by_name['failure_route']['rearm_sequence_from_post'][-1]['mem_after'], 125)
        self.assertEqual(by_name['recovery_jump']['pre_byte'], 88)
        self.assertEqual(by_name['recovery_jump']['post_xlat2_byte'], 47)
        self.assertEqual(by_name['recovery_jump']['rearm_sequence_from_post'][-1]['mem_after'], 88)

    def test_step2_m1e_prior_dependent_commit_and_no_restore_fails_final_state_and_output(self):
        source, meta = build_candidates.build_m1e('normal')
        for initial, expected_mem36, expected_out in [(1, 29526, b'V'), (3, 29522, b'R')]:
            for candidate in [1, 3]:
                with self.subTest(initial=initial, candidate=candidate):
                    result = observe.run(source, bytes([initial, candidate]), 5000)
                    self.assertTrue(observe.m1e_contract(result, meta, initial, candidate))
                    self.assertEqual(result['terminal'], 'HALT')
                    self.assertEqual(result['memory'][36], expected_mem36)
                    self.assertEqual(result['output'], expected_out)
                    self.assertEqual(result['memory'][52], initial)
                    self.assertEqual(result['memory'][64], 29528 if candidate == 1 else 7)

        # Step 2 requirement: no_restore must fail BOTH final observable output AND final logical state
        no_restore_src, no_restore_meta = build_candidates.build_m1e('no_restore')
        for initial, expected_mem36, expected_out in [(1, 29526, b'V'), (3, 29522, b'R')]:
            with self.subTest(control='no_restore', initial=initial):
                result = observe.run(no_restore_src, bytes([initial, 3]), 5000)
                self.assertFalse(observe.m1e_contract(result, no_restore_meta, initial, 3))
                self.assertNotEqual(result['output'], expected_out)
                self.assertEqual(result['output'], b'')
                self.assertNotEqual(result['memory'][36], expected_mem36)
                self.assertEqual(result['memory'][36], 29528)

    def test_step3_m1e_attempt_counter_explicit_reject_halt_and_preserved_stall_control(self):
        reject_src, reject_meta = build_candidates.build_m1e('force_retry_failure')
        for initial in [1, 3]:
            result = observe.run(reject_src, bytes([initial, 3]), 5000)
            self.assertFalse(observe.m1e_contract(result, reject_meta, initial, 3))
            self.assertEqual(result['terminal'], 'HALT')
            self.assertEqual(result['output'], b'')
            self.assertEqual(result['memory'][36], 29524)
            self.assertEqual(result['memory'][64], 7)
            self.assertEqual(result['trace'][-1]['pre'][1], reject_meta['labels']['reject_halt'])

        stall_src, stall_meta = build_candidates.build_m1e('force_retry_stall')
        for initial in [1, 3]:
            result = observe.run(stall_src, bytes([initial, 3]), 5000)
            self.assertFalse(observe.m1e_contract(result, stall_meta, initial, 3))
            self.assertEqual(result['terminal'], 'STALL')
            self.assertEqual(result['output'], b'')
            self.assertEqual(result['memory'][64], 7)

        for mode in ['no_save', 'corrupt_journal', 'no_recovery', 'broken_return', 'early_halt', 'output_impostor']:
            ctrl_src, ctrl_meta = build_candidates.build_m1e(mode)
            for initial in [1, 3]:
                result = observe.run(ctrl_src, bytes([initial, 3]), 5000)
                self.assertFalse(observe.m1e_contract(result, ctrl_meta, initial, 3), (mode, initial))

    def test_step4_m2_two_epochs_all_trajectories_and_controls(self):
        source, meta = build_candidates.build_m2('normal')
        for initial, expected_mem36, expected_out in [(1, 29526, b'VV'), (3, 29522, b'RR')]:
            for cand1, cand2, expected_rots in [
                (1, 1, 0),
                (3, 1, 10),
                (1, 3, 10),
                (3, 3, 20),
            ]:
                with self.subTest(initial=initial, cand1=cand1, cand2=cand2):
                    result = observe.run(source, bytes([initial, cand1, cand2]), 10000)
                    self.assertTrue(observe.m2_contract(result, meta, initial, cand1, cand2))
                    self.assertEqual(result['terminal'], 'HALT')
                    self.assertEqual(result['memory'][36], expected_mem36)
                    self.assertEqual(result['output'], expected_out)
                    self.assertEqual(result['memory'][52], initial)
                    jc = observe.m2_journal_consumption(result, meta)
                    self.assertEqual(jc['total_journal_rotations'], expected_rots)

        for mode in ['no_save', 'corrupt_journal', 'no_restore', 'broken_rearm', 'force_retry_failure', 'output_impostor']:
            ctrl_src, ctrl_meta = build_candidates.build_m2(mode)
            for initial in [1, 3]:
                with self.subTest(mode=mode, initial=initial):
                    result = observe.run(ctrl_src, bytes([initial, 3, 3]), 10000)
                    self.assertFalse(observe.m2_contract(result, ctrl_meta, initial, 3, 3))

    def test_m1e_and_m2_match_three_standalone_oracles(self):
        s1e, _ = build_candidates.build_m1e('normal')
        for payload in [b'\x01\x01', b'\x01\x03', b'\x03\x01', b'\x03\x03']:
            with self.subTest(candidate='m1e_normal', payload=payload):
                report = verify(s1e, payload, 5000)
                self.assertTrue(validate_parity(report), report)

        s2, _ = build_candidates.build_m2('normal')
        for initial in [1, 3]:
            for cand1 in [1, 3]:
                for cand2 in [1, 3]:
                    payload = bytes([initial, cand1, cand2])
                    with self.subTest(candidate='m2_normal', payload=payload):
                        report = verify(s2, payload, 10000)
                        self.assertTrue(validate_parity(report), report)


if __name__ == '__main__':
    unittest.main()
