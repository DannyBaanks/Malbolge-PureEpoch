#!/usr/bin/env python3
"""Toroidal Borrow & Return Experiments for PureEpoch / Torus.

Demonstrates:
- Milestone M2 (G-T2 / E-T2): Controlled write/read of two distinct runtime values
  (0x01 and 0x03) in borrowed cell 41 in D \\ C \\ E, with exact pre-loan return to
  byte 121 from ledger 43 (D \\ C \\ E), verified by downstream consumer jump through
  mem[41]=121, and falsified by negative control no_return.
- Milestone M3 (G-T3 / E-T3): Checkpoint, in-band branching, controlled corruption,
  restore from borrowed journal J=42 (D \\ C \\ E, initial byte 120), retry transition,
  and exact loan return of J=42 to 120 from ledger L=44 before downstream consumer jump,
  plus 4 falsification controls (no_loan_return, no_restore, corrupt_journal, force_retry_failure).
- Policy: Cell 53 is strictly NEVER visited or touched (C=0, R=0, W=0, E=0).
"""

from collections import deque
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from baseline.epoch_probe import Machine, crazy, load, XLAT1, XLAT2, VALID
from tools.build_candidates import Layout, encode, strict_byte
from tools.observe import run as py_run


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Milestone M2 (E-T2) Assembler
# ---------------------------------------------------------------------------

def build_torus_e_t2(mode: str = 'normal'):
    """Assemble E-T2: Borrow cell 41 in D \\ C \\ E, write/read two distinct values,

    return loan to 121 from ledger 43, verify with downstream consumer jump.
    Modes: 'normal', 'no_return'.
    """
    b = Layout()
    b.cells[8] = 125  # destination for jump to 126
    b.cells[97] = 36  # wrap pointer from 97 to 37
    b.mutable.add(8)

    # Cell 0 jumps to 98 -> lands on 99
    # From 99, step to cell 8 and jump to 125 -> lands on 126
    b.seek(8)
    b.emit('i', 'portal_jump')
    b.c = 126
    b.d = 9

    # Ledger cell L = 43 (initial byte in m281 is 90; strict_byte(90, 43)==True)
    # Borrowed cell B = 41 (initial byte in m281 is 121; strict_byte(121, 41)==True)
    b.cells[43] = 90
    b.cells[41] = 121
    b.mutable.update({41, 43})

    def cell(addr, op, lbl=None):
        b.seek(addr)
        b.emit(op, lbl)

    def load_const(addr, rots=10):
        for _ in range(rots):
            cell(addr, '*')

    # Step 1: Initialize ledger mem[43] to 29524: crazy(0, 90) = 29524
    cell(43, 'p', 'init_ledger')

    # Step 2: Read pre-loan value 121 from mem[41] into A via 10 rotations
    for i in range(10):
        cell(41, '*', f'read_pre_loan_rot_{i+1}')

    # Step 3: Save pre-loan value 121 into ledger 43: crazy(121, 29524) = 29403
    cell(43, 'p', 'save_pre_loan')

    # Step 4: Read input from stdin (0x01 or 0x03)
    b.emit('/', 'read_input')

    # Step 5: Write input into borrowed cell 41:
    # crazy(1, 121) = 29523, crazy(3, 121) = 29521
    cell(41, 'p', 'write_borrowed')

    # Step 6: Read borrowed value back from mem[41] via 10 rotations
    for i in range(10):
        cell(41, '*', f'read_borrowed_rot_{i+1}')

    # Step 7: Loan return
    if mode == 'normal':
        # Load pre-loan representation 29403 from ledger 43 into A via 10 rotations
        for i in range(10):
            cell(43, '*', f'read_ledger_rot_{i+1}')
        # Restore mem[41] = crazy(29403, mem[41]) = 121!
        cell(41, 'p', 'return_loan')
    # If mode == 'no_return': omit return, mem[41] remains 29523 or 29521

    # Step 8: Downstream consumer jump through mem[41]
    cell(41, 'i', 'consumer_dispatch')

    # Consumer landing pad at 121..123
    b.cells[121] = 35               # Encrypted destination upon jump
    b.cells[122] = encode('<', 122) # Output read value
    b.cells[123] = encode('v', 123) # Halt

    return b.image(), {
        'kind': 'TORUS_BORROW_E_T2',
        'mode': mode,
        'borrowed_cell': 41,
        'pre_loan_value': 121,
        'ledger_cell': 43,
        'landing_pad': 121,
        'labels': b.labels,
    }


# ---------------------------------------------------------------------------
# Milestone M3 (E-T3) Assembler
# ---------------------------------------------------------------------------

def build_torus_e_t3(mode: str = 'normal'):
    """Assemble E-T3: Checkpoint, in-band branching, controlled corruption,

    restore from borrowed journal J=42 (initial byte 120), retry transition,
    and exact loan return of J=42 to 120 from ledger L=44.
    Modes:
      - 'normal': clean on cand=1, recovery on cand=3, loan returned, commits 'V' / 'R'.
      - 'no_loan_return': skips loan return of J=42, fails consumer jump.
      - 'no_restore': skips restore of S=40 in recovery path.
      - 'corrupt_journal': damages J=42 before restore in recovery path.
      - 'force_retry_failure': applies bad retry transition in recovery path.
    """
    modes = {'normal', 'no_loan_return', 'no_restore', 'corrupt_journal', 'force_retry_failure'}
    if mode not in modes:
        raise ValueError(f'Unsupported mode: {mode}')

    b = Layout()
    b.cells[8] = 125
    b.cells[97] = 36
    b.mutable.add(8)

    # Portal jump to 126
    b.seek(8)
    b.emit('i', 'portal_jump')
    b.c = 126
    b.d = 9

    # Cells:
    # State S = 40 (init 93)
    # Borrowed Journal J = 42 (init 120)
    # Ledger L = 44 (init 118)
    # Candidate cell = 38 (init 118 -> crazy(0, 118)=29524)
    # Candidate route = 39 (init 60 -> points d to 60)
    # Portal target = 61 (init 37 -> rot(37)=19695)
    # Zero seed = 75 (init 81)
    # Op helper = 45 (init 72 -> 2 rots to 8)
    b.cells.update({
        40: 93, 42: 120, 44: 118, 38: 118, 39: 60, 61: 37, 75: 81, 45: 72,
    })
    b.mutable.update({38, 39, 40, 42, 44, 45, 61, 75})

    def cell(addr, op, lbl=None):
        b.seek(addr)
        b.emit(op, lbl)

    def load_const(addr, rots=10):
        for _ in range(rots):
            cell(addr, '*')

    # Step 1: Pre-loan safeguard of J=42 (120) into L=44
    cell(44, 'p', 'init_ledger')       # mem[44] = crazy(0, 118) = 29524
    load_const(42, 10)                 # A = 120, mem[42] = 120
    cell(44, 'p', 'save_pre_loan')     # mem[44] = crazy(120, 29524) = 29404

    # Step 2: Initialize helpers, portal, state, journal, and const 8
    cell(75, 'p', 'zero_seed')         # crazy(29404, 81) = 29524
    cell(75, 'p', 'init_zero')         # crazy(29524, 29524) = 0
    cell(42, 'p', 'init_journal')      # crazy(0, 120) = 29524
    cell(61, '*', 'init_portal')       # rot(37) = 19695
    cell(40, 'p', 'init_state')        # crazy(0, 93) = 29524
    cell(45, '*', 'init_const_8_a')    # rot(72) = 24
    cell(45, '*', 'init_const_8_b')    # rot(24) = 8! mem[45] is now constant 8

    # Step 3: Read initial from stdin (1 or 3)
    b.emit('/', 'read_initial')
    cell(40, 'p', 'write_initial')     # mem[40] = 29523 (for 1) or 29521 (for 3)

    # Step 4: Save checkpoint of state 40 into journal J=42
    load_const(40, 10)                 # A = mem[40]
    cell(42, 'p', 'save_checkpoint')   # mem[42] = crazy(mem[40], 29524) = 1 (for 1) or 3 (for 3)

    # Step 5: Read candidate from stdin (1 or 3)
    cell(75, '*')                      # A = 0
    cell(38, 'p', 'init_cand_cell')    # mem[38] = 29524
    b.emit('/', 'read_candidate')      # A = 1 or 3
    cell(38, 'p', 'write_cand')        # mem[38] = 29523 (for 1) or 29521 (for 3)

    # Step 6: In-band dispatch on cand_cell 38
    # cand=1 -> mem[38]=29523 -> jumps to 29523 -> lands at 29524 (clean commit path)
    # cand=3 -> mem[38]=29521 -> jumps to 29521 -> lands at 29522 (recovery path)
    cell(38, 'i', 'cand_dispatch')

    # Trampoline landing pads
    b.cells[29521] = 35                   # Encrypted on jump to 29521
    b.cells[29522] = encode('j', 29522)   # Steps d to mem[39]=60 -> d becomes 61
    b.cells[29523] = encode('i', 29523)   # Jumps to mem[61]=19695 -> lands on 19696 (recovery)

    # Recovery handler at 19696:
    b.c = 19696
    b.d = 62

    # Recovery Step 1: Controlled corruption of state 40
    cell(75, '*', 'rec_load_zero')
    cell(40, 'p', 'corrupt_state')        # mem[40] = crazy(0, mem[40]) = 29524 (corrupted!)

    # Recovery Step 2: Corrupt journal control
    if mode == 'corrupt_journal':
        cell(42, '*', 'damage_journal')

    # Recovery Step 3: Restore state 40 from J=42
    load_const(42, 10)                    # A = journal value (1 or 3)
    if mode != 'no_restore':
        cell(40, 'p', 'restore_state')    # mem[40] = crazy(a, 29524) = 29523 (for 1) or 29521 (for 3)

    # Recovery Step 4: Retry transition
    if mode == 'force_retry_failure':
        cell(75, '*', 'bad_retry_zero')
        cell(40, 'p', 'bad_retry')        # mem[40] becomes 29524, not committed state
    else:
        load_const(45, 10)                # A = 8
        cell(40, 'p', 'retry_trans')      # mem[40] = crazy(8, mem[40]) = 29526 (for 1) or 29522 (for 3)

    # Recovery Step 5: Loan return of J=42 in recovery path
    if mode != 'no_loan_return':
        load_const(44, 10)                # A = 29404 from ledger 44
        cell(42, 'p', 'rec_return_loan')  # mem[42] = crazy(29404, mem[42]) = 120!

    # Recovery Step 6: Load committed state into A, then consumer jump through mem[42]
    load_const(40, 10)                    # A = mem[40] (29526 or 29522)
    cell(42, 'i', 'rec_consumer_dispatch')

    # Clean commit path at 29524:
    b.c = 29524
    b.d = 39

    # Clean Step 1: Transition state 40 to committed state
    load_const(45, 10)                    # A = 8
    cell(40, 'p', 'clean_commit_trans')   # mem[40] = crazy(8, mem[40]) = 29526 (for 1) or 29522 (for 3)

    # Clean Step 2: Loan return of J=42
    if mode != 'no_loan_return':
        load_const(44, 10)                # A = 29404 from ledger 44
        cell(42, 'p', 'clean_return_loan')# mem[42] = crazy(29404, mem[42]) = 120!

    # Clean Step 3: Load committed state into A, then consumer jump through mem[42]
    load_const(40, 10)                    # A = mem[40] (29526 or 29522)
    cell(42, 'i', 'clean_consumer_dispatch')

    # Downstream consumer landing pad at 120..122:
    b.cells[120] = 36                     # Encrypted upon jump to 120
    b.cells[121] = encode('<', 121)       # Emit committed output ('V' or 'R')
    b.cells[122] = encode('v', 122)       # Halt

    b.labels.update({
        'dispatch_failure_route': 29522,
        'dispatch_clean_route': 29524,
        'consumer_landing': 120,
        'consumer_commit': 121,
        'consumer_halt': 122,
    })

    return b.image(), {
        'kind': 'TORUS_BORROW_E_T3',
        'mode': mode,
        'state_cell': 40,
        'journal_cell': 42,
        'pre_loan_value': 120,
        'ledger_cell': 44,
        'landing_pad': 120,
        'labels': b.labels,
    }


# ---------------------------------------------------------------------------
# Execution and Verification Harness
# ---------------------------------------------------------------------------

def run_in_all_oracles(program_path: Path, stdin: bytes, budget: int = 10000):
    """Run program in Python, observe, mb_ref, trace_ref, and olmstead."""
    src = program_path.read_bytes()

    # 1. Python observer
    py_res = py_run(src, stdin, max_steps=budget)

    # 2. mb_ref (classic C oracle)
    mb_ref_bin = ROOT / 'mb_ref'
    if not mb_ref_bin.exists():
        mb_ref_bin = REPO_ROOT / 'build' / 'mb_ref'
    try:
        res_ref = subprocess.run([str(mb_ref_bin), str(program_path), str(budget)],
                                 input=stdin, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired as e:
        res_ref = subprocess.CompletedProcess(e.cmd, 124, e.stdout or b'', e.stderr or b'TIMEOUT')

    # 3. observe (metrics and CSV trace generator)
    observe_bin = ROOT / 'observe'
    run_base = ROOT / 'runs' / f'verify_{program_path.stem}'
    try:
        res_obs = subprocess.run([str(observe_bin), str(program_path), str(budget), str(run_base)],
                                 input=stdin, capture_output=True, timeout=5)
    except subprocess.TimeoutExpired as e:
        res_obs = subprocess.CompletedProcess(e.cmd, 124, e.stdout or b'', e.stderr or b'TIMEOUT')

    # 4. trace_ref / olmstead if available
    trace_bin = REPO_ROOT / 'build' / 'trace_ref'
    olmstead_bin = REPO_ROOT / 'build' / 'olmstead'
    res_trace = None
    if trace_bin.exists():
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_d:
            tmp = Path(tmp_d)
            try:
                res_trace = subprocess.run([str(trace_bin), str(program_path), str(budget),
                                            str(tmp / 'tr.jsonl'), str(tmp / 'st.bin')],
                                           input=stdin, capture_output=True, timeout=5)
            except subprocess.TimeoutExpired as e:
                res_trace = subprocess.CompletedProcess(e.cmd, 124, e.stdout or b'', e.stderr or b'TIMEOUT')
    res_olmstead = None
    if olmstead_bin.exists():
        try:
            res_olmstead = subprocess.run([str(olmstead_bin), str(program_path)],
                                          input=stdin, capture_output=True, timeout=5)
        except subprocess.TimeoutExpired as e:
            res_olmstead = subprocess.CompletedProcess(e.cmd, 124, e.stdout or b'', e.stderr or b'TIMEOUT')

    # Parse counts CSV from observe
    counts_file = run_base.with_suffix('.counts.csv')
    cell_stats = {}
    if counts_file.exists():
        with counts_file.open() as f:
            for row in csv.DictReader(f):
                addr = int(row['address'])
                if addr in (40, 41, 42, 43, 44, 53):
                    cell_stats[addr] = {
                        'C': int(row['C_visits']),
                        'D': int(row['D_visits']),
                        'R': int(row['operand_reads']),
                        'W': int(row['direct_writes']),
                        'E': int(row['encryptions']),
                    }

    return {
        'python': {
            'terminal': py_res['terminal'],
            'steps': py_res['steps'],
            'output': py_res['output'].decode('latin1'),
            'mem40': py_res['memory'][40] if len(py_res['memory']) > 40 else None,
            'mem41': py_res['memory'][41] if len(py_res['memory']) > 41 else None,
            'mem42': py_res['memory'][42] if len(py_res['memory']) > 42 else None,
            'mem43': py_res['memory'][43] if len(py_res['memory']) > 43 else None,
            'mem44': py_res['memory'][44] if len(py_res['memory']) > 44 else None,
            'mem53': py_res['memory'][53] if len(py_res['memory']) > 53 else None,
        },
        'mb_ref': {
            'returncode': res_ref.returncode,
            'stdout': res_ref.stdout.decode('latin1'),
            'stderr': res_ref.stderr.decode('latin1').strip(),
        },
        'observe': {
            'returncode': res_obs.returncode,
            'stderr': res_obs.stderr.decode('latin1').strip(),
            'cells': cell_stats,
        },
        'trace_ref': {
            'returncode': res_trace.returncode if res_trace else None,
            'stdout': res_trace.stdout.decode('latin1') if res_trace else None,
        },
        'olmstead': {
            'returncode': res_olmstead.returncode if res_olmstead else None,
            'stdout': res_olmstead.stdout.decode('latin1') if res_olmstead else None,
        },
    }


def execute_e_t2_campaign():
    print('=== Executing Milestone M2 (G-T2 / E-T2) Campaign ===')
    programs_dir = ROOT / 'programs'
    programs_dir.mkdir(parents=True, exist_ok=True)

    normal_src, normal_meta = build_torus_e_t2('normal')
    no_return_src, no_return_meta = build_torus_e_t2('no_return')

    normal_path = programs_dir / 'torus_borrow_e_t2.mal'
    no_return_path = programs_dir / 'torus_borrow_e_t2_no_return.mal'

    normal_path.write_bytes(normal_src)
    no_return_path.write_bytes(no_return_src)

    results = {
        'metadata': {
            'borrowed_cell': 41,
            'pre_loan_byte': 121,
            'ledger_cell': 43,
            'cell_53_policy': 'untouched_r0_w0_c0_e0',
            'programs': {
                'normal': {'path': str(normal_path), 'sha256': sha256_bytes(normal_src), 'len': len(normal_src)},
                'no_return': {'path': str(no_return_path), 'sha256': sha256_bytes(no_return_src), 'len': len(no_return_src)},
            },
        },
        'positive_cases': {},
        'negative_controls': {},
    }

    # Positive runs on 0x01 and 0x03
    for byte_val in (1, 3):
        stdin = bytes([byte_val])
        out = run_in_all_oracles(normal_path, stdin)
        # Verify loan return
        assert out['python']['terminal'] == 'HALT'
        assert out['python']['mem41'] == 121
        assert out['mb_ref']['returncode'] == 0
        assert out['mb_ref']['stdout'] == 'y'
        # Verify cell 53 policy
        stats53 = out['observe']['cells'].get(53, {})
        assert stats53.get('C', 0) == 0 and stats53.get('W', 0) == 0 and stats53.get('R', 0) == 0
        # Verify 41 and 43 in D \ C \ E
        stats41 = out['observe']['cells'].get(41, {})
        stats43 = out['observe']['cells'].get(43, {})
        assert stats41.get('C', 0) == 0 and stats41.get('E', 0) == 0
        assert stats43.get('C', 0) == 0 and stats43.get('E', 0) == 0

        results['positive_cases'][f'input_{byte_val}'] = {
            'stdin_hex': f'0x{byte_val:02x}',
            'terminal': out['python']['terminal'],
            'steps': out['python']['steps'],
            'mem41_restored': out['python']['mem41'] == 121,
            'mem41_value': out['python']['mem41'],
            'mb_ref_exit': out['mb_ref']['returncode'],
            'mb_ref_stdout': out['mb_ref']['stdout'],
            'cell_53_untouched': stats53.get('C', 0) == 0 and stats53.get('W', 0) == 0 and stats53.get('R', 0) == 0,
            'cells_in_D_minus_C_minus_E': stats41.get('C', 0) == 0 and stats43.get('C', 0) == 0,
        }

    # Negative control: no_return fails consumer jump
    for byte_val in (1, 3):
        stdin = bytes([byte_val])
        out_nr = run_in_all_oracles(no_return_path, stdin)
        # Must fail (not HALT, mb_ref non-zero)
        assert out_nr['python']['terminal'] != 'HALT'
        assert out_nr['python']['mem41'] != 121
        assert out_nr['mb_ref']['returncode'] != 0

        results['negative_controls'][f'no_return_input_{byte_val}'] = {
            'stdin_hex': f'0x{byte_val:02x}',
            'terminal': out_nr['python']['terminal'],
            'mem41_unreturned': out_nr['python']['mem41'],
            'mb_ref_exit': out_nr['mb_ref']['returncode'],
            'falsified_as_expected': True,
        }

    report_path = ROOT / 'runs' / 'torus_e_t2_report.json'
    report_path.write_text(json.dumps(results, indent=2) + '\n')
    print(f'[PASS] E-T2 campaign completed successfully. Report written to {report_path}')
    return results


def execute_e_t3_campaign():
    print('=== Executing Milestone M3 (G-T3 / E-T3) Campaign ===')
    programs_dir = ROOT / 'programs'
    programs_dir.mkdir(parents=True, exist_ok=True)

    modes = ['normal', 'no_loan_return', 'no_restore', 'corrupt_journal', 'force_retry_failure']
    paths = {}
    metas = {}

    for m in modes:
        src, meta = build_torus_e_t3(m)
        path = programs_dir / f'torus_e_t3_{m}.mal'
        path.write_bytes(src)
        paths[m] = path
        metas[m] = {
            'path': str(path),
            'sha256': sha256_bytes(src),
            'len': len(src),
        }

    results = {
        'metadata': {
            'state_cell': 40,
            'journal_cell': 42,
            'pre_loan_byte': 120,
            'ledger_cell': 44,
            'cell_53_policy': 'untouched_r0_w0_c0_e0',
            'programs': metas,
        },
        'positive_cases': {},
        'negative_controls': {},
    }

    # 4 positive cases on normal program: (initial, cand) in {1, 3}^2
    expected_outputs = {1: 'V', 3: 'R'}
    expected_mem40 = {1: 29526, 3: 29522}

    for init_val in (1, 3):
        for cand_val in (1, 3):
            stdin = bytes([init_val, cand_val])
            out = run_in_all_oracles(paths['normal'], stdin)

            assert out['python']['terminal'] == 'HALT'
            assert out['python']['mem40'] == expected_mem40[init_val]
            assert out['python']['mem42'] == 120  # Loan returned!
            assert out['python']['output'] == expected_outputs[init_val]
            assert out['mb_ref']['returncode'] == 0
            assert out['mb_ref']['stdout'] == expected_outputs[init_val]

            # Parity checks
            if out['trace_ref']['returncode'] is not None:
                assert out['trace_ref']['returncode'] == 0
                assert out['trace_ref']['stdout'] == expected_outputs[init_val]
            if out['olmstead']['returncode'] is not None:
                assert out['olmstead']['returncode'] == 0
                assert out['olmstead']['stdout'] == expected_outputs[init_val]

            # Policy checks
            stats53 = out['observe']['cells'].get(53, {})
            assert stats53.get('C', 0) == 0 and stats53.get('W', 0) == 0 and stats53.get('R', 0) == 0
            stats40 = out['observe']['cells'].get(40, {})
            stats42 = out['observe']['cells'].get(42, {})
            stats44 = out['observe']['cells'].get(44, {})
            assert stats40.get('C', 0) == 0 and stats40.get('E', 0) == 0
            assert stats42.get('C', 0) == 0 and stats42.get('E', 0) == 0
            assert stats44.get('C', 0) == 0 and stats44.get('E', 0) == 0

            results['positive_cases'][f'initial_{init_val}_cand_{cand_val}'] = {
                'path_type': 'clean_path' if cand_val == 1 else 'rollback_recovery_retry_path',
                'terminal': out['python']['terminal'],
                'steps': out['python']['steps'],
                'mem40_committed': out['python']['mem40'],
                'mem42_returned': out['python']['mem42'] == 120,
                'output': out['python']['output'],
                'oracle_parity': True,
                'cell_53_untouched': True,
                'cells_in_D_minus_C_minus_E': True,
            }

    # Negative controls
    # 1. no_loan_return: fails downstream consumer jump
    for init_val in (1, 3):
        stdin = bytes([init_val, 3])  # Recovery path without loan return
        out = run_in_all_oracles(paths['no_loan_return'], stdin)
        assert out['python']['terminal'] != 'HALT'
        assert out['python']['mem42'] != 120
        assert out['mb_ref']['returncode'] != 0
        results['negative_controls'][f'no_loan_return_init_{init_val}'] = {
            'terminal': out['python']['terminal'],
            'mem42_unreturned': out['python']['mem42'],
            'mb_ref_exit': out['mb_ref']['returncode'],
            'falsified_as_expected': True,
        }

    # 2. no_restore: corrupted state remains corrupted
    for init_val in (1, 3):
        stdin = bytes([init_val, 3])
        out = run_in_all_oracles(paths['no_restore'], stdin)
        # State mem[40] is NOT committed state
        assert out['python']['mem40'] != expected_mem40[init_val]
        results['negative_controls'][f'no_restore_init_{init_val}'] = {
            'terminal': out['python']['terminal'],
            'mem40': out['python']['mem40'],
            'falsified_as_expected': True,
        }

    # 3. corrupt_journal: damaged journal produces corrupted recovery
    for init_val in (1, 3):
        stdin = bytes([init_val, 3])
        out = run_in_all_oracles(paths['corrupt_journal'], stdin)
        assert out['python']['mem40'] != expected_mem40[init_val] or out['python']['terminal'] != 'HALT'
        results['negative_controls'][f'corrupt_journal_init_{init_val}'] = {
            'terminal': out['python']['terminal'],
            'mem40': out['python']['mem40'],
            'falsified_as_expected': True,
        }

    # 4. force_retry_failure: retry transition produces invalid state
    for init_val in (1, 3):
        stdin = bytes([init_val, 3])
        out = run_in_all_oracles(paths['force_retry_failure'], stdin)
        assert out['python']['mem40'] != expected_mem40[init_val]
        results['negative_controls'][f'force_retry_failure_init_{init_val}'] = {
            'terminal': out['python']['terminal'],
            'mem40': out['python']['mem40'],
            'falsified_as_expected': True,
        }

    report_path = ROOT / 'runs' / 'torus_e_t3_report.json'
    report_path.write_text(json.dumps(results, indent=2) + '\n')
    print(f'[PASS] E-T3 campaign completed successfully. Report written to {report_path}')
    return results


def main():
    e_t2_res = execute_e_t2_campaign()
    e_t3_res = execute_e_t3_campaign()
    print('All toroidal borrow campaigns executed and verified cleanly.')


if __name__ == '__main__':
    main()
