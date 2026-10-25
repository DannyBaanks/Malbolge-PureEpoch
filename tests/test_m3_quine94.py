import hashlib
import unittest
from pathlib import Path

from tools.autobolge_adapter import m3_proposal_campaign
from tools.build_candidates import build_m3, trampoline_rearm_analysis
from tools.observe import m3_contract, m3_journal_consumption, run
from tools.oracles import validate_parity, verify
from tools.quine_94_probe import (
    build_94_cell_probe,
    period2_strict_loader_wall,
    quine_94_bounds_and_roundtrip,
    xlat2_cycle_decomposition,
)

ROOT = Path(__file__).resolve().parents[1]


class TestQuine94AndM3(unittest.TestCase):
    def test_prior_milestones_preserved(self):
        m1c_sha = hashlib.sha256((ROOT / 'candidates/m1c_normal.mal').read_bytes()).hexdigest()
        m1e_sha = hashlib.sha256((ROOT / 'candidates/m1e_normal.mal').read_bytes()).hexdigest()
        m2_sha = hashlib.sha256((ROOT / 'candidates/m2_normal.mal').read_bytes()).hexdigest()
        self.assertEqual(m1c_sha, '17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985')
        self.assertEqual(m1e_sha, 'dc9ed4d81ef7200d5b5e1dc2c3f161bd4b01be39b58ca43bc87db410461e9f53')
        self.assertEqual(m2_sha, '3ec16fd60b5298a83f30dddf340bdc962a6fe981c4a05379c446bcb92a8748d6')

    def test_xlat2_and_period2_wall_in_94(self):
        decomp = xlat2_cycle_decomposition()
        self.assertEqual(decomp['cycle_lengths'], [68, 9, 6, 5, 4, 2])
        self.assertEqual(decomp['fixed_points_period_1'], [])
        self.assertEqual(decomp['period_2_cycle']['chars'], 'FJ')

        wall = period2_strict_loader_wall()
        self.assertEqual(wall['block_size'], 94)
        self.assertEqual(wall['f_legal_count'], 8)
        self.assertEqual(wall['j_legal_count'], 8)
        self.assertEqual(wall['both_legal_count'], 0)
        self.assertEqual(wall['neither_legal_count'], 78)

    def test_94_cell_ceiling_probe_and_synthetic_period1_theorem(self):
        probe = build_94_cell_probe()
        self.assertEqual(len(probe), 94)
        obs = run(probe, b'')
        self.assertEqual(obs['terminal'], 'HALT')
        self.assertEqual(obs['memory'][81], 81)
        report = verify(probe, b'', budget=5000)
        self.assertTrue(validate_parity(report))

        full = quine_94_bounds_and_roundtrip()
        self.assertEqual(full['synthetic_period1_roundtrip_theorem']['verified_pos_op_pairs'], 752)
        self.assertTrue(full['synthetic_period1_roundtrip_theorem']['all_verified'])

    def test_trampoline_rearm_includes_epoch3_entries(self):
        analysis = trampoline_rearm_analysis()
        self.assertEqual(len(analysis['entries']), 20)
        names = {e['name'] for e in analysis['entries']}
        self.assertIn('epoch3_entry_prelanding', names)
        self.assertIn('epoch3_portal_prelanding', names)
        self.assertIn('epoch3_reject_prelanding', names)

    def test_m3_three_epoch_positive_and_eof_trajectories(self):
        source, meta = build_m3('normal')
        for init in (1, 3):
            for c1, c2, c3 in [(1, 1, 1), (3, 1, 1), (1, 3, 1), (1, 1, 3), (3, 3, 3)]:
                payload = bytes([init, c1, c2, c3])
                obs = run(source, payload, max_steps=10000)
                self.assertTrue(m3_contract(obs, meta, init, c1, c2, c3))
                jc = m3_journal_consumption(obs, meta)
                self.assertEqual(jc['epoch1_journal_rotations'], 0 if c1 == 1 else 10)
                self.assertEqual(jc['epoch2_journal_rotations'], 0 if c2 == 1 else 10)
                self.assertEqual(jc['epoch3_journal_rotations'], 0 if c3 == 1 else 10)

            eof_payload = bytes([init, 1, 1])
            eof_obs = run(source, eof_payload, max_steps=10000)
            self.assertTrue(m3_contract(eof_obs, meta, init, 1, 1, 59048, expected_reads=3))
            eof_jc = m3_journal_consumption(eof_obs, meta)
            self.assertEqual(eof_jc['epoch3_restores'], 1)
            self.assertEqual(eof_jc['epoch3_journal_rotations'], 10)

        rep = verify(source, b'\x01\x03\x03\x03', budget=10000)
        self.assertTrue(validate_parity(rep))

    def test_m3_negative_controls_fail_contract(self):
        for mode in ['no_save', 'corrupt_journal', 'no_restore', 'broken_rearm', 'broken_return', 'force_retry_failure', 'output_impostor']:
            source, meta = build_m3(mode)
            for init in (1, 3):
                obs = run(source, bytes([init, 3, 3, 3]), max_steps=10000)
                self.assertFalse(m3_contract(obs, meta, init, 3, 3, 3), f'{mode} unexpectedly passed')
                if mode == 'force_retry_failure':
                    self.assertEqual(obs['terminal'], 'HALT')
                    self.assertEqual(obs['registers'][1], meta['labels']['epoch3_reject_halt'])
                    self.assertEqual(obs['output'], b'VV' if init == 1 else b'RR')

        eof_src, eof_meta = build_m3('eof_unmasked')
        for init in (1, 3):
            obs = run(eof_src, bytes([init, 1, 1]), max_steps=10000)
            self.assertFalse(m3_contract(obs, eof_meta, init, 1, 1, 59048, expected_reads=3))

    def test_m3_bounded_proposal_campaign(self):
        report = m3_proposal_campaign()
        self.assertEqual(report['total_candidates_evaluated'], 64)
        self.assertLessEqual(report['total_candidates_evaluated'], report['budget_max_candidates'])
        self.assertEqual(report['accepted_count'], 8)
        self.assertEqual(report['rejected_count'], 56)
        self.assertEqual(len(report['unique_accepted_sha256']), 1)
        self.assertTrue(report['autobolge_encoder_matches_native'])
        self.assertTrue(report['canonical_m3_oracle_parity']['triple_rollback_01030303']['parity_ok'])
        self.assertTrue(report['canonical_m3_oracle_parity']['eof_recovery_010101']['parity_ok'])
        gates = report['rejection_breakdown_by_gate']
        for required_gate in [
            'strict_loader_gate',
            'no_save_or_checkpoint_gate',
            'no_restore_gate',
            'broken_return_gate',
            'corrupt_journal_gate',
            'repeated_failure_gate',
            'output_impostor_gate',
            'distinct_eof_gate',
        ]:
            self.assertIn(required_gate, gates)


if __name__ == '__main__':
    unittest.main()
