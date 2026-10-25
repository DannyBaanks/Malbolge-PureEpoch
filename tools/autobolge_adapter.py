"""Minimal OFFLINE encoder/trace/anchor bridge and M3 bounded proposal validator,
never a runtime supervisor.

This invokes the real Autobolge encoder/TraceExpander and validates every generated
candidate strictly from zero under Classic/BolgeForge rules; no process of observation
rewrites the VM or resumes a Python snapshot as execution truth.
"""
from pathlib import Path
import hashlib
import json
import sys

from tools.build_candidates import build_conditional, build_m3, strict_byte
from tools.observe import m3_contract, run
from tools.oracles import raw_reference, validate_parity, verify

ROOT = Path(__file__).resolve().parents[1]
AUTO = ROOT / 'vendor/autobolge'

VALID_OP_CHARS = ('j', 'i', '*', 'p', '<', '/', 'v', 'o')


def modules():
    if not AUTO.exists():
        raise RuntimeError('Pinned Autobolge vendor snapshot is missing; see README.md')
    if str(AUTO) not in sys.path:
        sys.path.insert(0, str(AUTO))
    from relational.classic import ClassicDebugger
    from relational.anchors import EpochAnchorV1
    from relational.trace import verify_trace, replay_trace
    from relational.synthesizer import char_for
    return ClassicDebugger, EpochAnchorV1, verify_trace, replay_trace, char_for


def frontier_modules():
    modules()
    from relational.frontier import Proposal, TraceExpander
    return Proposal, TraceExpander


def eof_probe():
    Debugger, _, _, _, _ = modules()
    source = b'uP'  # '/' at zero, 'v' at one; two strict-valid bytes
    strict = run(source, b'')
    dbg = Debugger(source.decode('ascii'), '', 10)
    while not dbg.is_stopped and dbg.step_count < 10:
        dbg.step()
    return {
        'source_hex': source.hex(),
        'payload_hex': '',
        'strict': {
            'a': strict['registers'][0],
            'c': strict['registers'][1],
            'd': strict['registers'][2],
            'terminal': strict['terminal'],
            'trace': strict['trace'],
        },
        'autobolge': {
            'a': dbg.a,
            'c': dbg.c,
            'd': dbg.d,
            'reason': dbg.get_state().stop_reason,
            'steps': dbg.step_count,
        },
    }


def semantic_probes():
    Debugger, _, _, _, _ = modules()
    enc_src = bytes.fromhex('2750')
    enc_strict = raw_reference(enc_src, b'', 10)
    enc_obs = run(enc_src, b'', 10)
    enc_dbg = Debugger(enc_src.decode('latin1'), '', 10)
    while not enc_dbg.is_stopped and enc_dbg.step_count < 10:
        enc_dbg.step()

    ldr_src = bytes.fromhex('af50')
    ldr_strict = raw_reference(ldr_src, b'', 10)
    try:
        ldr_obs = run(ldr_src, b'', 10)
        ldr_obs_info = {'terminal': ldr_obs['terminal']}
    except ValueError as err:
        ldr_obs_info = {'rejected': str(err)}
    ldr_dbg = Debugger(ldr_src.decode('latin1'), '', 10)
    while not ldr_dbg.is_stopped and ldr_dbg.step_count < 10:
        ldr_dbg.step()

    return {
        'invalid_encryption': {
            'source_hex': enc_src.hex(),
            'strict_returncode': enc_strict.returncode,
            'strict_stderr': enc_strict.stderr.decode('latin1').strip(),
            'observer': {
                'a': enc_obs['registers'][0],
                'c': enc_obs['registers'][1],
                'd': enc_obs['registers'][2],
                'terminal': enc_obs['terminal'],
            },
            'autobolge': {
                'a': enc_dbg.a,
                'c': enc_dbg.c,
                'd': enc_dbg.d,
                'reason': enc_dbg.get_state().stop_reason,
                'steps': enc_dbg.step_count,
            },
        },
        'non_ascii_loader': {
            'source_hex': ldr_src.hex(),
            'strict_returncode': ldr_strict.returncode,
            'strict_stderr': ldr_strict.stderr.decode('latin1').strip(),
            'observer': ldr_obs_info,
            'autobolge': {
                'a': ldr_dbg.a,
                'c': ldr_dbg.c,
                'd': ldr_dbg.d,
                'reason': ldr_dbg.get_state().stop_reason,
                'steps': ldr_dbg.step_count,
            },
        },
    }


def bridge(payload):
    Debugger, Anchor, verify_trace, replay_trace, char_for = modules()
    source, meta = build_conditional(encoder=char_for)
    native, _ = build_conditional()
    strict = run(source, payload)
    trace = []
    dbg = Debugger(source.decode('ascii'), payload.decode('latin1'), 5000, trace=trace)
    anchor = None
    while not dbg.is_stopped and dbg.step_count < 5000:
        pre_c = dbg.c
        dbg.step()
        if pre_c == meta['labels']['restore']:
            saved = Anchor.from_debugger(dbg, trace)
            anchor = {
                'digest': saved.digest(),
                'memory_root': saved.memory_root,
                'target_value': saved.memory[36],
                'journal_value': saved.memory[52],
                'pc': saved.pc,
                'a': saved.a,
                'd': saved.d,
                'step': saved.step,
            }
    verify_trace(trace)
    replay_trace(source.decode('ascii'), payload.decode('latin1'), trace, 5000)
    return {
        'same_source': source == native,
        'source_sha256': hashlib.sha256(source).hexdigest(),
        'strict_state_parity': (
            list(dbg.memory) == strict['memory']
            and [dbg.a, dbg.c, dbg.d] == strict['registers'][:3]
            and dbg.output.encode('latin1') == strict['output']
        ),
        'anchor_at_restore': anchor,
        'autobolge_steps_including_halt': dbg.step_count,
        'scope': 'offline encoding and observational anchors only; no relational proposal search, JIT, or snapshot resume',
    }


def validate_strict_source(source: bytes) -> dict:
    """BolgeForge / Classic strict source validator: ASCII 33..126 and legal XLAT1 decode at every address."""
    if not (2 <= len(source) <= 59049):
        return {'valid': False, 'reason': 'invalid_length', 'first_bad_pos': 0}
    for pos, b in enumerate(source):
        if not strict_byte(b, pos):
            return {'valid': False, 'reason': 'strict_loader_rejected', 'first_bad_pos': pos, 'bad_byte': b}
    return {'valid': True, 'reason': None, 'first_bad_pos': None}


def evaluate_m3_candidate(source: bytes, meta: dict, family: str, slot: str, proposed_op: str, proposal_index: int) -> dict:
    """Validate one proposed M3 source from zero against strict loader + positive/negative/EOF gates."""
    sha = hashlib.sha256(source).hexdigest()
    loader_check = validate_strict_source(source)
    if not loader_check['valid']:
        ref = raw_reference(source[:min(len(source), 120)], b'\x01\x01\x01\x01', 50)
        return {
            'proposal_id': proposal_index,
            'family': family,
            'slot': slot,
            'proposed_op': proposed_op,
            'source_sha256': sha,
            'accepted': False,
            'rejection_gate': 'strict_loader_gate',
            'rejection_detail': loader_check,
            'c_reference_returncode': ref.returncode,
        }

    # Gate 1: Positive 3-epoch clean & rollback trajectories within 10,000 steps
    positive_cases = [
        (b'\x01\x01\x01\x01', 1, 1, 1, 1),
        (b'\x01\x03\x01\x03', 1, 3, 1, 3),
        (b'\x01\x03\x03\x03', 1, 3, 3, 3),
        (b'\x03\x03\x03\x03', 3, 3, 3, 3),
    ]
    max_steps_observed = 0
    for payload, init, c1, c2, c3 in positive_cases:
        obs = run(source, payload, max_steps=10000)
        max_steps_observed = max(max_steps_observed, obs['steps'])
        if not m3_contract(obs, meta, init, c1, c2, c3):
            gate = {
                'epoch3_save': 'no_save_or_checkpoint_gate',
                'epoch3_restore': 'no_restore_gate',
                'epoch3_retry_dispatch': 'broken_return_gate',
                'epoch3_damage_journal': 'corrupt_journal_gate',
                'epoch3_retry_const_op': 'repeated_failure_gate',
                'epoch3_post_output_op': 'output_impostor_gate',
            }.get(slot, 'positive_3epoch_contract_gate')
            return {
                'proposal_id': proposal_index,
                'family': family,
                'slot': slot,
                'proposed_op': proposed_op,
                'source_sha256': sha,
                'accepted': False,
                'rejection_gate': gate,
                'failed_payload_hex': payload.hex(),
                'terminal': obs['terminal'],
                'steps': obs['steps'],
                'output_hex': obs['output'].hex(),
                'final_mem36': obs['memory'][36],
            }

    # Gate 2: Distinct EOF gate (3-byte payload b'\x01\x01\x01' hits Classic EOF=59048 on Epoch 3 candidate read)
    eof_obs = run(source, b'\x01\x01\x01', max_steps=10000)
    max_steps_observed = max(max_steps_observed, eof_obs['steps'])
    if not m3_contract(eof_obs, meta, 1, 1, 1, 59048, expected_reads=3):
        return {
            'proposal_id': proposal_index,
            'family': family,
            'slot': slot,
            'proposed_op': proposed_op,
            'source_sha256': sha,
            'accepted': False,
            'rejection_gate': 'distinct_eof_gate',
            'failed_payload_hex': '010101',
            'terminal': eof_obs['terminal'],
            'steps': eof_obs['steps'],
            'output_hex': eof_obs['output'].hex(),
            'final_mem36': eof_obs['memory'][36],
        }

    return {
        'proposal_id': proposal_index,
        'family': family,
        'slot': slot,
        'proposed_op': proposed_op,
        'source_sha256': sha,
        'accepted': True,
        'rejection_gate': None,
        'max_steps_observed': max_steps_observed,
    }


def m3_proposal_campaign():
    """Step 5 offline campaign: bounded Autobolge proposal family (64 <= 128 candidates, <= 10,000 steps)
    validated strictly from zero by BolgeForge/Classic rules and standalone C oracles.
    """
    Debugger, Anchor, verify_trace, replay_trace, char_for = modules()
    Proposal, TraceExpander = frontier_modules()

    base_source, base_meta = build_m3('normal', encoder=char_for)
    native_source, _ = build_m3('normal')

    # 1. Inspect TraceExpander behavior on an M3 EpochAnchorV1 at epoch3_restore
    trace = []
    dbg = Debugger(base_source.decode('ascii'), '\x01\x01\x01\x03', 10000, trace=trace)
    restore_anchor = None
    while not dbg.is_stopped and dbg.step_count < 10000:
        pre_c = dbg.c
        dbg.step()
        if pre_c == base_meta['labels']['epoch3_restore']:
            restore_anchor = Anchor.from_debugger(dbg, trace)
    verify_trace(trace)
    expander = TraceExpander(max_steps=10000)
    raw_expansion = expander.expand(restore_anchor, b'VVV', budget=16)

    # 2. Compare Autobolge vs strict Classic on 3-byte EOF payload b'\x01\x01\x01'
    eof_strict = run(base_source, b'\x01\x01\x01', max_steps=10000)
    eof_dbg = Debugger(base_source.decode('ascii'), '\x01\x01\x01', 10000)
    while not eof_dbg.is_stopped and eof_dbg.step_count < 10000:
        eof_dbg.step()

    # 3. Generate bounded 64-candidate proposal family (8 slot families x 8 proposals = 64 <= 128 budget)
    proposals = []
    pid = 0

    slot_families = [
        ('F1_epoch3_save', 'epoch3_save', VALID_OP_CHARS),
        ('F2_epoch3_restore', 'epoch3_restore', VALID_OP_CHARS),
        ('F3_epoch3_retry_dispatch', 'epoch3_retry_dispatch', VALID_OP_CHARS),
        ('F4_epoch3_eof_mask', 'epoch3_eof_mask', VALID_OP_CHARS),
        ('F5_epoch3_damage_journal', 'epoch3_damage_journal', (None, 'j', 'i', '*', 'p', '<', '/', 'v')),
        ('F6_epoch3_retry_operand', 'epoch3_retry_const_op', (None, 'j', 'i', '*', 'p', '<', '/', 'v')),
        ('F7_epoch3_post_output_impostor', 'epoch3_post_output_op', (None, 'j', 'i', '*', 'p', '<', '/', 'v')),
    ]

    for fam_name, slot_name, op_choices in slot_families:
        for op in op_choices:
            pid += 1
            overrides = {} if op is None else {slot_name: op}
            cand_src, cand_meta = build_m3('normal', encoder=char_for, slot_overrides=overrides)
            label_op = 'NONE_CLEAN' if op is None else op
            proposals.append(evaluate_m3_candidate(cand_src, cand_meta, fam_name, slot_name, label_op, pid))

    # Family 8: 8 strict-loader boundary proposals (1 clean + 7 illegal period-2 F/J or non-ASCII mutations)
    f8_mutations = [
        ('NONE_CLEAN', None, None),
        ('period2_F_at_pos0', 0, ord('F')),
        ('period2_J_at_pos0', 0, ord('J')),
        ('period2_F_at_pos36', 36, ord('F')),
        ('period2_J_at_pos36', 36, ord('J')),
        ('period2_F_at_pos52', 52, ord('F')),
        ('non_ascii_0xaf_at_pos10', 10, 0xAF),
        ('invalid_decode_at_pos98', 98, ord('!')),
    ]
    for label_op, mut_pos, mut_byte in f8_mutations:
        pid += 1
        mut_src = bytearray(base_source)
        if mut_pos is not None:
            mut_src[mut_pos] = mut_byte
        proposals.append(evaluate_m3_candidate(bytes(mut_src), base_meta, 'F8_strict_loader_boundary', 'raw_byte', label_op, pid))

    accepted = [p for p in proposals if p['accepted']]
    rejected = [p for p in proposals if not p['accepted']]
    rejection_counts = {}
    for r in rejected:
        gate = r['rejection_gate']
        rejection_counts[gate] = rejection_counts.get(gate, 0) + 1

    # Verify standalone C oracle parity for the canonical accepted M3 source
    c_parity_clean = verify(base_source, b'\x01\x03\x03\x03', budget=10000)
    c_parity_eof = verify(base_source, b'\x01\x01\x01', budget=10000)

    return {
        'schema': 'pure-epoch-m3-proposal-campaign/v1',
        'budget_max_candidates': 128,
        'budget_max_steps_per_candidate': 10000,
        'total_candidates_evaluated': len(proposals),
        'accepted_count': len(accepted),
        'rejected_count': len(rejected),
        'unique_accepted_sha256': sorted({p['source_sha256'] for p in accepted}),
        'canonical_m3_sha256': hashlib.sha256(base_source).hexdigest(),
        'autobolge_encoder_matches_native': base_source == native_source,
        'rejection_breakdown_by_gate': rejection_counts,
        'discrepancies_recorded': {
            'trace_expander_snapshot_vs_from_zero': {
                'anchor_digest': restore_anchor.digest(),
                'raw_expander_proposals': len(raw_expansion.proposals),
                'raw_expander_prunes': len(raw_expansion.prunes),
                'finding': (
                    'TraceExpander._valid_extensions proposes single-byte extensions at len(anchor.program), '
                    'while EpochAnchorV1.restore() resumes the mutated in-memory snapshot in Python without '
                    're-running the strict Classic loader from step 0.'
                ),
            },
            'm3_eof_3byte_payload_discrepancy': {
                'payload_hex': '010101',
                'strict_classic': {
                    'terminal': eof_strict['terminal'],
                    'steps': eof_strict['steps'],
                    'output': eof_strict['output'].decode('latin1'),
                    'final_mem36': eof_strict['memory'][36],
                    'epoch3_restores': int(m3_contract(eof_strict, base_meta, 1, 1, 1, 59048, expected_reads=3)),
                },
                'autobolge_debugger': {
                    'stop_reason': eof_dbg.get_state().stop_reason,
                    'steps': eof_dbg.step_count,
                    'output': eof_dbg.output,
                    'final_mem36': eof_dbg.memory[36],
                },
            },
        },
        'canonical_m3_oracle_parity': {
            'triple_rollback_01030303': {
                'parity_ok': validate_parity(c_parity_clean),
                'steps': c_parity_clean['steps_excluding_halt'],
                'output_hex': c_parity_clean['output_hex'],
            },
            'eof_recovery_010101': {
                'parity_ok': validate_parity(c_parity_eof),
                'steps': c_parity_eof['steps_excluding_halt'],
                'output_hex': c_parity_eof['output_hex'],
            },
        },
        'proposals': proposals,
    }


if __name__ == '__main__':
    m3_report = m3_proposal_campaign()
    (ROOT / 'evidence/m3-proposals.json').write_text(json.dumps(m3_report, indent=2) + '\n')
    dest = ROOT / 'evidence/autobolge-bridge.json'
    dest.write_text(
        json.dumps(
            {
                'eof_difference': eof_probe(),
                'semantic_probes': semantic_probes(),
                'cases': [bridge(p) for p in [b'\x01\x03', b'\x03\x03']],
                'm3_campaign_summary': {
                    k: v for k, v in m3_report.items() if k != 'proposals'
                },
            },
            indent=2,
        )
        + '\n'
    )
    print(dest, 'accepted:', m3_report['accepted_count'], 'rejected:', m3_report['rejected_count'])
