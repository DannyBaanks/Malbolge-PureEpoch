"""Offline construction only. Every byte is valid at its actual Classic address."""
from pathlib import Path
import json
from collections import deque

from baseline.epoch_probe import XLAT1, XLAT2, VALID, crazy


def encode(op, position):
    return 33 + (XLAT1.index(op) - position) % 94


def strict_byte(value, position):
    return 33 <= value <= 126 and XLAT1[(value - 33 + position) % 94] in VALID


def build_reversible(rotations=10, initial=37):
    """A selected data cell, nine/ten rotations, output, HALT. No journal."""
    if rotations < 1 or rotations > 10 or not strict_byte(initial, 96):
        raise ValueError('unsupported bounded rotation case')
    cells = [encode('o', p) for p in range(98)]
    cells[0] = encode('j', 0)       # d=41 after this instruction
    cells[21] = encode('j', 21)     # mem[61]=95 => d=96
    cells[61] = 95
    cells[96] = initial
    cells[97] = 95                 # return d from 97 to 96
    for i in range(rotations):
        cells[22 + 2*i] = encode('*', 22 + 2*i)
        if i < rotations-1:
            cells[23 + 2*i] = encode('j', 23 + 2*i)
    end = 22 + 2*(rotations-1)
    cells[end+1] = encode('<', end+1)
    cells[end+2] = encode('v', end+2)
    return bytes(cells), {'kind': 'REVERSIBLE', 'target': 96, 'initial': initial,
                          'rotations': rotations, 'first_mutation_pc': 22,
                          'last_rotation_pc': end, 'halt_pc': end+2}


class Layout:
    """Straight-line code at 99+, ordinary pointer steering in low memory."""
    def __init__(self, encoder=encode):
        self.encoder = encoder
        self.cells = {0: encoder('i', 0), 98: encoder('o', 98), 36: 81, 52: 81}
        self.mutable = {36, 52}
        self.c = 99
        self.d = 1
        self.labels = {}

    def emit(self, op, label=None):
        if label:
            self.labels[label] = self.c
        self.cells[self.c] = self.encoder(op, self.c)
        self.c += 1
        if op != 'v':
            self.d += 1

    def seek(self, target):
        """Emit only o/j. Never patches state while the artifact executes."""
        queue = deque([(self.d, [])])
        seen = set()
        path = None
        while queue:
            d, route = queue.popleft()
            if d == target:
                path = route
                break
            if d in seen or not 1 <= d < 98:
                continue
            seen.add(d)
            if d not in self.mutable:
                ptr = target-1
                if strict_byte(ptr, d) and (d not in self.cells or self.cells[d] == ptr):
                    queue.appendleft((target, route+[('j', d, ptr)]))
                elif d in self.cells:
                    dest = self.cells[d]+1
                    if 1 <= dest < 98:
                        queue.append((dest, route+[('j', d, self.cells[d])]))
            queue.append((d+1, route+[('o', d, None)]))
        if path is None:
            raise ValueError('low-memory steering budget exhausted')
        for op, address, value in path:
            if op == 'j':
                self.cells[address] = value
                self.emit('j')
                self.d = value+1
            else:
                self.emit('o')

    def image(self):
        cells = [self.cells.get(p, self.encoder('o', p)) for p in range(max(self.cells)+1)]
        if not all(strict_byte(v, p) for p, v in enumerate(cells)):
            raise ValueError('builder produced an invalid loader byte')
        return bytes(cells)


def build_checkpoint(mode='normal'):
    """Save complement-01 representation in cell 52; clobber and restore 36.

    Supported stdin examples are 01 00 and 03 00. The second ordinary input
    supplies zero to the destructive operation. Neither input restores memory.
    There is no validity test or conditional recovery in this candidate.
    """
    if mode not in {'normal', 'no_save', 'corrupt_journal', 'early_halt', 'output_impostor'}:
        raise ValueError(mode)
    b = Layout()
    b.seek(52)
    b.emit('p', 'initialize_journal')  # crazy(0,81)=29524 (ten 1 trits)
    b.emit('/', 'read_initial')
    b.seek(36)
    b.emit('p', 'initialize_target')   # values 29523 or 29521 at runtime
    b.seek(52)
    b.emit('o' if mode == 'no_save' else 'p', 'save')
    b.emit('/', 'read_clobber_operand')
    b.seek(36)
    b.emit('p', 'clobber')             # operand zero makes target 29524
    if mode == 'early_halt':
        b.emit('v', 'early_halt')
        return b.image(), {'kind': 'CHECKPOINT_CONTROL', 'mode': mode, 'labels': b.labels, 'target': 36, 'journal': 52}
    if mode == 'corrupt_journal':
        b.seek(52)
        b.emit('*', 'damage_journal')
    for i in range(10):
        b.seek(52)
        b.emit('*', f'journal_read_rotation_{i+1}')
    b.seek(36)
    b.emit('p', 'restore')             # crazy(saved,29524)=prior target
    b.emit('<', 'emit_committed_value')
    if mode == 'output_impostor':
        b.seek(36)
        b.emit('*', 'post_output_damage')
    b.emit('v', 'halt')
    return b.image(), {'kind': 'CHECKPOINT', 'mode': mode, 'labels': b.labels, 'target': 36, 'journal': 52}


def build_conditional(mode='normal', encoder=encode):
    """Finite-domain internal validity dispatch, saved-state recovery and retry.

    stdin = [initial selector 1|3, candidate operand 1|3]. Invariant: cell 36
    must equal 29523. Classic i dispatches on the computed cell itself: 29521
    reaches recovery at 29522; 29523 reaches commit at 29524. Recovery reads
    the journal, restores prior logical state, constructs operand one using
    four rotations of 81, and repeats the crazy transition once.
    """
    if mode not in {'normal', 'no_save', 'corrupt_journal', 'no_restore',
                    'no_recovery', 'broken_return', 'early_halt', 'force_retry_failure'}:
        raise ValueError(mode)
    b = Layout(encoder)
    b.cells.update({37: 61, 62: 37, 75: 81, 81: 81})
    b.mutable.update({62, 75, 81})

    def cell(address, op, label=None):
        b.seek(address)
        b.emit(op, label)

    cell(75, 'p', 'zero_seed_to_ones')
    cell(75, 'p', 'initialize_zero')
    cell(52, 'p', 'initialize_journal')
    cell(62, '*', 'initialize_recovery_portal')   # rot(37)=19695
    b.emit('/', 'read_initial')
    cell(36, 'p', 'initialize_target')
    cell(52, 'o' if mode == 'no_save' else 'p', 'save')
    cell(75, '*', 'load_zero')
    cell(36, 'p', 'clobber')
    b.emit('/', 'read_candidate')
    cell(36, 'p', 'transition')
    cell(36, 'i', 'dispatch')

    b.cells[29522] = encoder('v' if mode == 'no_recovery' else 'j', 29522)
    b.cells[29523] = encoder('v' if mode == 'broken_return' else 'i', 29523)
    b.cells[29524] = encoder('<', 29524)
    b.cells[29525] = encoder('v', 29525)
    b.labels.update({'failure_route': 29522, 'recovery_jump': 29523, 'commit': 29524, 'halt': 29525})

    # These are compiler coordinates for the known runtime portal landing;
    # neither register assignment is ever performed on a running machine.
    b.c, b.d = 19696, 63
    if mode == 'early_halt':
        b.emit('v', 'early_halt')
    cell(75, '*', 'recovery_load_zero')
    cell(36, 'p', 'recovery_reset_target')
    if mode == 'corrupt_journal':
        cell(52, '*', 'damage_journal')
    for i in range(10):
        cell(52, '*', f'journal_read_rotation_{i+1}')
    cell(36, 'o' if mode == 'no_restore' else 'p', 'restore')
    for i in range(3 if mode == 'force_retry_failure' else 4):
        cell(81, '*', f'construct_retry_operand_{i+1}')
    cell(36, 'p', 'retry')
    cell(36, 'i', 'retry_dispatch')
    return b.image(), {'kind': 'BOUNDED_CONDITIONAL_RECOVERY_RETRY', 'mode': mode,
                       'labels': b.labels, 'target': 36, 'journal': 52,
                       'zero_cell': 75, 'operand_cell': 81, 'portal_cell': 62,
                       'domain': {'initial': [1, 3], 'candidate': [1, 3]},
                       'invariant': 'mem[36] == 29523', 'max_attempts_on_domain': 2}


def trampoline_rearm_analysis():
    """Step 1: Export exact pre/post-XLAT2 bytes for i/j trampolines and portals,
    and verify offline the in-VM crazy rearm sequences.
    """
    specs = [
        {'name': 'm1c_failure_prelanding', 'pos': 29521, 'op': 'o', 'role': 'encrypted by dispatch(i) when mem[36]=29521'},
        {'name': 'm1c_failure_route', 'pos': 29522, 'op': 'j', 'role': 'encrypted when executing j at 29522'},
        {'name': 'm1c_recovery_jump', 'pos': 29523, 'op': 'i', 'role': 'jump instruction i; encrypts portal pre-landing mem[19695]'},
        {'name': 'm1c_portal_prelanding', 'pos': 19695, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=19695'},
        {'name': 'commit_3', 'pos': 29523, 'op': '<', 'role': 'encrypted when executing < for init=3 commit'},
        {'name': 'halt_3', 'pos': 29524, 'op': 'v', 'role': 'encrypted by dispatch(i) when mem[36]=29524 (failure)'},
        {'name': 'continue_3', 'pos': 29524, 'op': 'i', 'role': 'epoch1 continuation jump for init=3; encrypted by dispatch(i) on failure'},
        {'name': 'failure_route', 'pos': 29525, 'op': 'j', 'role': 'encrypted when executing j at 29525'},
        {'name': 'recovery_jump', 'pos': 29526, 'op': 'i', 'role': 'encrypted by dispatch(i) when mem[36]=29526 (init=1 commit)'},
        {'name': 'commit_1', 'pos': 29527, 'op': '<', 'role': 'encrypted when executing < for init=1 commit'},
        {'name': 'halt_1', 'pos': 29528, 'op': 'v', 'role': 'halt for init=1 commit'},
        {'name': 'continue_1', 'pos': 29528, 'op': 'i', 'role': 'epoch1 continuation jump for init=1'},
        {'name': 'epoch1_portal_prelanding', 'pos': 19695, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=19695'},
        {'name': 'epoch1_reject_prelanding', 'pos': 6565, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=6565'},
        {'name': 'epoch2_entry_prelanding', 'pos': 39397, 'op': 'o', 'role': 'encrypted by continue_1/continue_3(i) when mem[38]=39397'},
        {'name': 'epoch2_portal_prelanding', 'pos': 49208, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=49208'},
        {'name': 'epoch2_reject_prelanding', 'pos': 55768, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=55768'},
        {'name': 'epoch3_entry_prelanding', 'pos': 32815, 'op': 'o', 'role': 'encrypted by continue_1/continue_3(i) when mem[38]=32815'},
        {'name': 'epoch3_portal_prelanding', 'pos': 9815, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=9815'},
        {'name': 'epoch3_reject_prelanding', 'pos': 42637, 'op': 'o', 'role': 'encrypted by recovery_jump(i) when mem[62]=42637'},
    ]
    records = []
    for item in specs:
        pos = item['pos']
        op = item['op']
        pre = encode(op, pos)
        post = ord(XLAT2[pre - 33])
        post_decoded = XLAT1[(post - 33 + pos) % 94]
        x_const = crazy(pre, 29524)
        for start_val in (post, pre):
            s1 = crazy(29524, start_val)
            s2 = crazy(80, s1)
            s3 = crazy(0, s2)
            s4 = crazy(x_const, s3)
            if s3 != 29524 or s4 != pre:
                raise ValueError(f'rearm verification failed at {pos}')
        records.append({
            **item,
            'pre_byte': pre,
            'pre_char': chr(pre),
            'post_xlat2_byte': post,
            'post_xlat2_char': chr(post),
            'post_xlat2_decoded_op': post_decoded,
            'rearm_constant_x': x_const,
            'rearm_sequence_from_post': [
                {'op': 'p', 'a_in': 29524, 'mem_before': post, 'mem_after': crazy(29524, post)},
                {'op': 'p', 'a_in': 80, 'mem_before': crazy(29524, post), 'mem_after': crazy(80, crazy(29524, post))},
                {'op': 'p', 'a_in': 0, 'mem_before': crazy(80, crazy(29524, post)), 'mem_after': 29524},
                {'op': 'p', 'a_in': x_const, 'mem_before': 29524, 'mem_after': pre},
            ],
        })
    return {
        'schema': 'pure-epoch-trampoline-rearm/v1',
        'universal_ascii_reset_identity': 'crazy(0, crazy(80, crazy(29524, y))) == 29524 for all y in 0..161',
        'post_write_scratch_reset_identity': 'crazy(0, crazy(B, crazy(B, 29524))) == 29524 for all B in 0..59048',
        'entries': records,
    }


def _emit_helpers(b):
    def cell(address, op, label=None):
        b.seek(address)
        b.emit(op, label)

    def load_const(address, rot_count=10):
        for _ in range(rot_count):
            cell(address, '*')

    def trip_to_trampoline(pos, label=None):
        """With desired operand already in A, jump d via 54 (mem[54]=29521 -> d=29522),
        step o to pos, execute p, step o to 29530, execute j (mem[29530]=48 -> d=49).
        """
        cell(54, 'j')
        b.d = 29522
        while b.d < pos:
            b.emit('o')
        b.emit('p', label)
        while b.d < 29530:
            b.emit('o')
        b.emit('j')
        b.d = 49

    def reset_scratch_cell(addr):
        """Reset scratch cell (52, 53, 64, 80, 94) to 29524 regardless of prior {0,1,2} trits in 0..3."""
        cell(81, '*')
        cell(addr, 'p')
        load_const(76, 10)
        cell(addr, 'p')
        cell(75, '*')
        cell(addr, 'p')

    def rearm_trampoline_cell(pos, byte_cell_addr, label_prefix):
        """Rearm mem[pos] in-VM to mem[byte_cell_addr] from any ASCII byte (pre or post XLAT2).
        Preserves mem[53] == 29524 on exit using crazy(0, crazy(B, crazy(B, 29524))) == 29524.
        """
        cell(81, '*')
        trip_to_trampoline(pos, f'{label_prefix}_reset_s1')
        load_const(76, 10)
        trip_to_trampoline(pos, f'{label_prefix}_reset_s2')
        cell(75, '*')
        trip_to_trampoline(pos, f'{label_prefix}_reset_s3')
        load_const(byte_cell_addr, 10)
        cell(53, 'p')
        trip_to_trampoline(pos, f'{label_prefix}_write_byte')
        cell(53, 'p')
        cell(75, '*')
        cell(53, 'p')

    def eval_candidate_to_op(prefix):
        """Transform candidate in A (1 or 3) into op in A (8 for valid=1, 0 for invalid=3).
        Requires mem[53] == 29524 before reading candidate into A.
        """
        cell(53, 'p', f'{prefix}_cand_complement')
        load_const(84, 10)
        cell(53, 'p')
        load_const(80, 10)
        cell(53, 'p')
        reset_scratch_cell(94)
        load_const(53, 10)
        cell(94, 'p')
        cell(75, '*')
        cell(94, 'p')
        cell(53, '*')
        cell(94, 'p')
        cell(75, '*')
        cell(94, 'p')
        reset_scratch_cell(53)
        load_const(94, 10)
        cell(53, 'p', f'{prefix}_eval_op')

    return cell, load_const, reset_scratch_cell, trip_to_trampoline, rearm_trampoline_cell, eval_candidate_to_op


def build_m1e(mode='normal', encoder=encode):
    """Step 2 & Step 3: Prior-datum-dependent commit (1->29526/'V', 3->29522/'R'),
    in-VM trampoline rearm, internal finite attempt counter (cell 64), and explicit
    reject HALT on repeated retry failure (preserving STALL as a separate negative control).
    """
    modes = {
        'normal', 'no_save', 'corrupt_journal', 'no_restore',
        'no_recovery', 'broken_return', 'early_halt', 'output_impostor',
        'force_retry_failure', 'force_retry_stall',
    }
    if mode not in modes:
        raise ValueError(mode)
    b = Layout(encoder)
    b.cells.update({
        37: 61, 38: 61, 46: 35, 50: 125, 53: 81, 54: 108, 60: 73, 62: 37, 63: 35, 64: 111,
        75: 81, 76: 80, 79: 54, 80: 54, 81: 81, 84: 72, 94: 81, 97: 36,
        29530: 48,
    })
    b.mutable.update({38, 50, 53, 54, 60, 62, 64, 75, 76, 79, 80, 81, 84, 94})
    cell, load_const, reset_scratch_cell, trip_to_trampoline, rearm_trampoline_cell, eval_candidate_to_op = _emit_helpers(b)

    cell(75, 'p', 'zero_seed_to_ones')
    cell(75, 'p', 'initialize_zero')
    cell(53, 'p')
    cell(75, '*')
    cell(54, 'p')
    load_const(81, 3)
    cell(54, 'p', 'initialize_tramp_ptr')
    cell(75, '*')
    cell(81, 'p', 'initialize_ones')
    cell(75, '*')
    cell(52, 'p', 'initialize_journal')
    cell(75, '*')
    cell(64, 'p', 'initialize_attempt_counter')
    reset_scratch_cell(80)
    load_const(79, 3)
    cell(80, 'p', 'initialize_c29525')
    load_const(84, 2)
    cell(62, '*', 'initialize_recovery_portal')

    cell(75, '*')
    cell(36, 'p', 'preclear_target')
    b.emit('/', 'read_initial')
    cell(36, 'p', 'initialize_target')
    cell(52, 'o' if mode == 'no_save' else 'p', 'save')

    load_const(84, 10)
    cell(64, 'p', 'count_attempt_1')
    reset_scratch_cell(53)
    b.emit('/', 'read_candidate')
    eval_candidate_to_op('attempt1')
    cell(36, 'p', 'transition')
    cell(36, 'i', 'dispatch')

    b.cells[29521] = encoder('v', 29521)
    b.cells[29523] = encoder('<', 29523)
    b.cells[29524] = encoder('v', 29524)
    b.cells[29525] = encoder('v' if mode == 'no_recovery' else 'j', 29525)
    b.cells[29526] = encoder('v' if mode == 'broken_return' else 'i', 29526)
    b.cells[29527] = encoder('<', 29527)
    b.cells[29528] = encoder('v', 29528)
    b.cells[29529] = encoder('v', 29529)
    b.labels.update({
        'no_save_reject': 29521,
        'commit_3': 29523,
        'halt_3': 29524,
        'failure_route': 29525,
        'recovery_jump': 29526,
        'commit_1': 29527,
        'halt_1': 29528,
        'no_restore_reject': 29529,
        'reject_halt': 6566,
    })
    b.cells[6566] = encoder('v', 6566)

    b.c, b.d = 19696, 63
    if mode == 'early_halt':
        b.emit('v', 'early_halt')
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'count_attempt_2')
    if mode != 'force_retry_stall':
        cell(62, '*', 'arm_reject_portal')
        rearm_trampoline_cell(29524, 60, 'rearm_halt3')
        rearm_trampoline_cell(29525, 50, 'rearm_failure_route')
    else:
        rearm_trampoline_cell(29524, 60, 'rearm_halt3')

    cell(75, '*', 'recovery_load_zero')
    cell(36, 'p', 'recovery_reset_target')
    if mode == 'corrupt_journal':
        cell(52, '*', 'damage_journal')
    for i in range(10):
        cell(52, '*', f'journal_read_rotation_{i+1}')
    cell(36, 'o' if mode == 'no_restore' else 'p', 'restore')

    if mode in {'force_retry_failure', 'force_retry_stall'}:
        cell(75, '*', 'construct_retry_operand_fail')
    else:
        load_const(84, 10)
    cell(36, 'p', 'retry')
    if mode == 'output_impostor':
        b.emit('<', 'impostor_output')
        cell(36, '*', 'post_output_damage')
        b.emit('v', 'impostor_halt')
    else:
        cell(36, 'i', 'retry_dispatch')

    return b.image(), {
        'kind': 'PRIOR_DEPENDENT_RECOVERY_M1E',
        'mode': mode,
        'labels': b.labels,
        'target': 36,
        'journal': 52,
        'zero_cell': 75,
        'portal_cell': 62,
        'attempt_counter_cell': 64,
        'domain': {'initial': [1, 3], 'candidate': [1, 3]},
        'committed_state_by_initial': {'1': {'mem36': 29526, 'output': 'V'}, '3': {'mem36': 29522, 'output': 'R'}},
        'max_attempts_on_domain': 2,
    }


def build_m2(mode='normal', encoder=encode):
    """Step 4: Two-epoch composition in a single Classic Malbolge process.
    stdin = [initial selector 1|3, epoch1 candidate 1|3, epoch2 candidate 1|3].
    """
    modes = {
        'normal', 'no_save', 'corrupt_journal', 'no_restore',
        'broken_rearm', 'force_retry_failure', 'output_impostor',
    }
    if mode not in modes:
        raise ValueError(mode)
    b = Layout(encoder)
    b.cells.update({
        37: 61, 38: 95, 41: 92, 43: 90, 45: 88, 46: 35, 48: 69, 50: 125,
        53: 81, 54: 108, 60: 73, 62: 37, 63: 35, 64: 111,
        75: 81, 76: 80, 79: 54, 80: 54, 81: 81, 84: 72, 94: 81, 97: 36,
        29530: 48,
    })
    b.mutable.update({38, 41, 43, 45, 48, 50, 53, 54, 60, 62, 64, 75, 76, 79, 80, 81, 84, 94})
    cell, load_const, reset_scratch_cell, trip_to_trampoline, rearm_trampoline_cell, eval_candidate_to_op = _emit_helpers(b)

    cell(75, 'p', 'zero_seed_to_ones')
    cell(75, 'p', 'initialize_zero')
    cell(53, 'p')
    cell(75, '*')
    cell(54, 'p')
    load_const(81, 3)
    cell(54, 'p', 'initialize_tramp_ptr')
    cell(75, '*')
    cell(81, 'p', 'initialize_ones')
    cell(75, '*')
    cell(52, 'p', 'initialize_journal')
    cell(75, '*')
    cell(64, 'p', 'initialize_attempt_counter')
    reset_scratch_cell(80)
    load_const(79, 3)
    cell(80, 'p', 'initialize_c29525')
    load_const(84, 2)
    cell(62, '*', 'initialize_recovery_portal')
    cell(38, '*', 'initialize_epoch2_portal')

    # ================= EPOCH 1 =================
    cell(75, '*')
    cell(36, 'p', 'epoch1_preclear_target')
    b.emit('/', 'read_initial')
    cell(36, 'p', 'epoch1_initialize_target')
    cell(52, 'p', 'epoch1_save')

    load_const(84, 10)
    cell(64, 'p', 'epoch1_count_attempt_1')
    reset_scratch_cell(53)
    b.emit('/', 'read_candidate_1')
    eval_candidate_to_op('epoch1_attempt1')
    cell(36, 'p', 'epoch1_transition')
    cell(36, 'i', 'epoch1_dispatch')

    b.cells[29521] = encoder('v', 29521)
    b.cells[29523] = encoder('<', 29523)
    b.cells[29524] = encoder('i', 29524)
    b.cells[29525] = encoder('j', 29525)
    b.cells[29526] = encoder('i', 29526)
    b.cells[29527] = encoder('<', 29527)
    b.cells[29528] = encoder('i', 29528)
    b.cells[29529] = encoder('v', 29529)
    b.cells[6566] = encoder('v', 6566)
    b.cells[55769] = encoder('v', 55769)
    b.labels.update({
        'no_save_reject': 29521,
        'commit_3': 29523,
        'continue_or_halt_3': 29524,
        'failure_route': 29525,
        'recovery_jump': 29526,
        'commit_1': 29527,
        'continue_or_halt_1': 29528,
        'no_restore_reject': 29529,
        'epoch1_reject_halt': 6566,
        'epoch2_reject_halt': 55769,
        'epoch1_recovery_entry': 19696,
        'epoch2_entry': 39398,
        'epoch2_recovery_entry': 49209,
    })

    # ================= EPOCH 1 RECOVERY (c = 19696, d = 63) =================
    b.c, b.d = 19696, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'epoch1_count_attempt_2')
    cell(62, '*', 'epoch1_arm_reject_portal')
    rearm_trampoline_cell(29524, 43, 'epoch1_rearm_continue3')
    rearm_trampoline_cell(29525, 50, 'epoch1_rearm_failure_route')

    cell(75, '*', 'epoch1_recovery_load_zero')
    cell(36, 'p', 'epoch1_recovery_reset_target')
    for i in range(10):
        cell(52, '*', f'epoch1_journal_read_rotation_{i+1}')
    cell(36, 'p', 'epoch1_restore')
    load_const(84, 10)
    cell(36, 'p', 'epoch1_retry')
    cell(36, 'i', 'epoch1_retry_dispatch')

    # ================= EPOCH 2 CONTINUATION (c = 39398, d = 39) =================
    b.c, b.d = 39398, 39
    reset_scratch_cell(53)
    if mode != 'broken_rearm':
        rearm_trampoline_cell(29523, 41, 'epoch2_rearm_commit3')
        rearm_trampoline_cell(29524, 60, 'epoch2_rearm_halt3')
        rearm_trampoline_cell(29525, 50, 'epoch2_rearm_failure_route')
        rearm_trampoline_cell(29526, 45, 'epoch2_rearm_recovery_jump')
        rearm_trampoline_cell(29527, 45, 'epoch2_rearm_commit1')
        rearm_trampoline_cell(29528, 48, 'epoch2_rearm_halt1')

    cell(75, '*')
    cell(62, 'p', 'epoch2_reset_portal')
    load_const(84, 10)
    cell(62, 'p')
    cell(62, '*', 'epoch2_initialize_recovery_portal')

    reset_scratch_cell(52)
    load_const(84, 10)
    cell(36, 'p', 'epoch2_prepare_target')
    cell(52, 'o' if mode == 'no_save' else 'p', 'epoch2_save')

    reset_scratch_cell(64)
    load_const(84, 10)
    cell(64, 'p', 'epoch2_count_attempt_1')

    reset_scratch_cell(53)
    b.emit('/', 'read_candidate_2')
    eval_candidate_to_op('epoch2_attempt1')
    cell(36, 'p', 'epoch2_transition')
    cell(36, 'i', 'epoch2_dispatch')

    # ================= EPOCH 2 RECOVERY (c = 49209, d = 63) =================
    b.c, b.d = 49209, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'epoch2_count_attempt_2')
    cell(62, '*', 'epoch2_arm_reject_portal')
    rearm_trampoline_cell(29524, 60, 'epoch2_recovery_rearm_halt3')
    rearm_trampoline_cell(29525, 50, 'epoch2_recovery_rearm_failure_route')

    cell(75, '*', 'epoch2_recovery_load_zero')
    cell(36, 'p', 'epoch2_recovery_reset_target')
    if mode == 'corrupt_journal':
        cell(52, '*', 'epoch2_damage_journal')
    for i in range(10):
        cell(52, '*', f'epoch2_journal_read_rotation_{i+1}')
    cell(36, 'o' if mode == 'no_restore' else 'p', 'epoch2_restore')

    if mode == 'force_retry_failure':
        cell(75, '*', 'epoch2_construct_retry_operand_fail')
    else:
        load_const(84, 10)
    cell(36, 'p', 'epoch2_retry')
    if mode == 'output_impostor':
        b.emit('<', 'epoch2_impostor_output')
        cell(36, '*', 'epoch2_post_output_damage')
        b.emit('v', 'epoch2_impostor_halt')
    else:
        cell(36, 'i', 'epoch2_retry_dispatch')

    return b.image(), {
        'kind': 'TWO_EPOCH_CONTINUATION_M2',
        'mode': mode,
        'labels': b.labels,
        'target': 36,
        'journal': 52,
        'zero_cell': 75,
        'portal_cell': 62,
        'epoch2_portal_cell': 38,
        'attempt_counter_cell': 64,
        'domain': {'initial': [1, 3], 'candidate_1': [1, 3], 'candidate_2': [1, 3]},
        'committed_state_by_initial': {'1': {'mem36': 29526, 'output': 'VV'}, '3': {'mem36': 29522, 'output': 'RR'}},
        'epochs': 2,
        'max_attempts_per_epoch': 2,
    }


def build_m3(mode='normal', encoder=encode, slot_overrides=None):
    """Step 5: Three-epoch roundtrip + rollback composition in a single Classic Malbolge process.
    Reuses the 1x94 (0..93) low-memory dispatch/state core across 3 consecutive epochs via
    in-VM 4-step crazy trampoline rearming, portal rotation, and EOF-masked candidate evaluation.
    stdin = [initial selector 1|3, epoch1 candidate 1|3, epoch2 candidate 1|3, epoch3 candidate 1|3].
    """
    modes = {
        'normal', 'no_save', 'corrupt_journal', 'no_restore',
        'broken_rearm', 'broken_return', 'force_retry_failure',
        'output_impostor', 'eof_unmasked',
    }
    if mode not in modes:
        raise ValueError(mode)
    overrides = dict(slot_overrides or {})
    b = Layout(encoder)
    b.cells.update({
        37: 61, 38: 95, 41: 92, 43: 90, 45: 88, 46: 35, 47: 86, 48: 69, 50: 125,
        53: 81, 54: 108, 60: 73, 62: 37, 63: 35, 64: 111,
        75: 81, 76: 80, 79: 54, 80: 54, 81: 81, 84: 72, 94: 81, 97: 36,
        29530: 48,
    })
    b.mutable.update({38, 41, 43, 45, 47, 48, 50, 53, 54, 60, 62, 64, 75, 76, 79, 80, 81, 84, 94})
    cell, load_const, reset_scratch_cell, trip_to_trampoline, rearm_trampoline_cell, eval_candidate_to_op = _emit_helpers(b)

    def zero_scratch_53(slot_name):
        reset_scratch_cell(53)
        if mode != 'eof_unmasked':
            cell(81, '*')
            cell(53, overrides.get(slot_name, 'p'), slot_name)

    cell(75, 'p', 'zero_seed_to_ones')
    cell(75, 'p', 'initialize_zero')
    cell(53, 'p')
    cell(75, '*')
    cell(54, 'p')
    load_const(81, 3)
    cell(54, 'p', 'initialize_tramp_ptr')
    cell(75, '*')
    cell(81, 'p', 'initialize_ones')
    cell(75, '*')
    cell(52, 'p', 'initialize_journal')
    cell(75, '*')
    cell(64, 'p', 'initialize_attempt_counter')
    reset_scratch_cell(80)
    load_const(79, 3)
    cell(80, 'p', 'initialize_c29525')
    load_const(84, 2)
    cell(62, '*', 'initialize_recovery_portal')
    cell(38, '*', 'initialize_epoch2_portal')

    # ================= EPOCH 1 =================
    cell(75, '*')
    cell(36, 'p', 'epoch1_preclear_target')
    b.emit('/', 'read_initial')
    cell(36, 'p', 'epoch1_initialize_target')
    cell(52, 'p', 'epoch1_save')

    load_const(84, 10)
    cell(64, 'p', 'epoch1_count_attempt_1')
    zero_scratch_53('epoch1_eof_mask')
    b.emit('/', 'read_candidate_1')
    eval_candidate_to_op('epoch1_attempt1')
    cell(36, 'p', 'epoch1_transition')
    cell(36, 'i', 'epoch1_dispatch')

    b.cells[29521] = encoder('v', 29521)
    b.cells[29523] = encoder('<', 29523)
    b.cells[29524] = encoder('i', 29524)
    b.cells[29525] = encoder('j', 29525)
    b.cells[29526] = encoder('i', 29526)
    b.cells[29527] = encoder('<', 29527)
    b.cells[29528] = encoder('i', 29528)
    b.cells[29529] = encoder('v', 29529)
    b.cells[6566] = encoder('v', 6566)
    b.cells[55769] = encoder('v', 55769)
    b.cells[42638] = encoder('v', 42638)
    b.labels.update({
        'no_save_reject': 29521,
        'commit_3': 29523,
        'continue_or_halt_3': 29524,
        'failure_route': 29525,
        'recovery_jump': 29526,
        'commit_1': 29527,
        'continue_or_halt_1': 29528,
        'no_restore_reject': 29529,
        'epoch1_reject_halt': 6566,
        'epoch2_reject_halt': 55769,
        'epoch3_reject_halt': 42638,
        'epoch1_recovery_entry': 19696,
        'epoch2_entry': 39398,
        'epoch2_recovery_entry': 49209,
        'epoch3_entry': 32816,
        'epoch3_recovery_entry': 9816,
    })

    # ================= EPOCH 1 RECOVERY (c = 19696, d = 63) =================
    b.c, b.d = 19696, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'epoch1_count_attempt_2')
    cell(62, '*', 'epoch1_arm_reject_portal')
    rearm_trampoline_cell(29524, 43, 'epoch1_rearm_continue3')
    rearm_trampoline_cell(29525, 50, 'epoch1_rearm_failure_route')

    cell(75, '*', 'epoch1_recovery_load_zero')
    cell(36, 'p', 'epoch1_recovery_reset_target')
    for i in range(10):
        cell(52, '*', f'epoch1_journal_read_rotation_{i+1}')
    cell(36, 'p', 'epoch1_restore')
    load_const(84, 10)
    cell(36, 'p', 'epoch1_retry')
    cell(36, 'i', 'epoch1_retry_dispatch')

    # ================= EPOCH 2 CONTINUATION (c = 39398, d = 39) =================
    b.c, b.d = 39398, 39
    reset_scratch_cell(53)
    rearm_trampoline_cell(29523, 41, 'epoch2_rearm_commit3')
    rearm_trampoline_cell(29524, 43, 'epoch2_rearm_continue3')
    rearm_trampoline_cell(29525, 50, 'epoch2_rearm_failure_route')
    rearm_trampoline_cell(29526, 45, 'epoch2_rearm_recovery_jump')
    rearm_trampoline_cell(29527, 45, 'epoch2_rearm_commit1')
    rearm_trampoline_cell(29528, 47, 'epoch2_rearm_continue1')

    cell(38, '*', 'epoch2_advance_to_epoch3_portal')
    cell(75, '*')
    cell(62, 'p', 'epoch2_reset_portal')
    load_const(84, 10)
    cell(62, 'p')
    cell(62, '*', 'epoch2_initialize_recovery_portal')

    reset_scratch_cell(52)
    load_const(84, 10)
    cell(36, 'p', 'epoch2_prepare_target')
    cell(52, 'p', 'epoch2_save')

    reset_scratch_cell(64)
    load_const(84, 10)
    cell(64, 'p', 'epoch2_count_attempt_1')

    zero_scratch_53('epoch2_eof_mask')
    b.emit('/', 'read_candidate_2')
    eval_candidate_to_op('epoch2_attempt1')
    cell(36, 'p', 'epoch2_transition')
    cell(36, 'i', 'epoch2_dispatch')

    # ================= EPOCH 2 RECOVERY (c = 49209, d = 63) =================
    b.c, b.d = 49209, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'epoch2_count_attempt_2')
    cell(62, '*', 'epoch2_arm_reject_portal')
    rearm_trampoline_cell(29524, 43, 'epoch2_recovery_rearm_continue3')
    rearm_trampoline_cell(29525, 50, 'epoch2_recovery_rearm_failure_route')

    cell(75, '*', 'epoch2_recovery_load_zero')
    cell(36, 'p', 'epoch2_recovery_reset_target')
    for i in range(10):
        cell(52, '*', f'epoch2_journal_read_rotation_{i+1}')
    cell(36, 'p', 'epoch2_restore')
    load_const(84, 10)
    cell(36, 'p', 'epoch2_retry')
    cell(36, 'i', 'epoch2_retry_dispatch')

    # ================= EPOCH 3 CONTINUATION (c = 32816, d = 39) =================
    b.c, b.d = 32816, 39
    reset_scratch_cell(53)
    if mode != 'broken_rearm':
        rearm_trampoline_cell(29523, 41, 'epoch3_rearm_commit3')
        rearm_trampoline_cell(29524, 60, 'epoch3_rearm_halt3')
        rearm_trampoline_cell(29525, 50, 'epoch3_rearm_failure_route')
        rearm_trampoline_cell(29526, 45, 'epoch3_rearm_recovery_jump')
        rearm_trampoline_cell(29527, 45, 'epoch3_rearm_commit1')
        rearm_trampoline_cell(29528, 48, 'epoch3_rearm_halt1')

    for _ in range(8):
        cell(62, '*')
    reset_scratch_cell(62)
    load_const(45, 10)
    cell(62, 'p')
    cell(62, '*', 'epoch3_initialize_recovery_portal')

    reset_scratch_cell(52)
    load_const(84, 10)
    cell(36, 'p', 'epoch3_prepare_target')
    save_op = overrides.get('epoch3_save', 'o' if mode == 'no_save' else 'p')
    cell(52, save_op, 'epoch3_save')

    reset_scratch_cell(64)
    load_const(84, 10)
    cell(64, 'p', 'epoch3_count_attempt_1')

    zero_scratch_53('epoch3_eof_mask')
    b.emit('/', 'read_candidate_3')
    eval_candidate_to_op('epoch3_attempt1')
    cell(36, 'p', 'epoch3_transition')
    cell(36, 'i', 'epoch3_dispatch')

    # ================= EPOCH 3 RECOVERY (c = 9816, d = 63) =================
    b.c, b.d = 9816, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'epoch3_count_attempt_2')
    cell(62, '*', 'epoch3_arm_reject_portal')
    rearm_trampoline_cell(29524, 60, 'epoch3_recovery_rearm_halt3')
    rearm_trampoline_cell(29525, 50, 'epoch3_recovery_rearm_failure_route')

    cell(75, '*', 'epoch3_recovery_load_zero')
    cell(36, 'p', 'epoch3_recovery_reset_target')
    if mode == 'corrupt_journal' or 'epoch3_damage_journal' in overrides:
        cell(52, overrides.get('epoch3_damage_journal', '*'), 'epoch3_damage_journal')
    for i in range(10):
        cell(52, '*', f'epoch3_journal_read_rotation_{i+1}')
    restore_op = overrides.get('epoch3_restore', 'o' if mode == 'no_restore' else 'p')
    cell(36, restore_op, 'epoch3_restore')

    if mode == 'force_retry_failure':
        cell(75, '*', 'epoch3_construct_retry_operand_fail')
    elif 'epoch3_retry_const_op' in overrides:
        cell(75, overrides['epoch3_retry_const_op'], 'epoch3_construct_retry_operand_override')
    else:
        load_const(84, 10)
    cell(36, 'p', 'epoch3_retry')
    if mode == 'output_impostor' or 'epoch3_post_output_op' in overrides:
        b.emit('<', 'epoch3_impostor_output')
        cell(36, overrides.get('epoch3_post_output_op', '*'), 'epoch3_post_output_damage')
        b.emit('v', 'epoch3_impostor_halt')
    else:
        dispatch_op = overrides.get('epoch3_retry_dispatch', 'v' if mode == 'broken_return' else 'i')
        cell(36, dispatch_op, 'epoch3_retry_dispatch')

    return b.image(), {
        'kind': 'THREE_EPOCH_ROUNDTRIP_M3',
        'mode': mode,
        'labels': b.labels,
        'target': 36,
        'journal': 52,
        'zero_cell': 75,
        'portal_cell': 62,
        'continuation_portal_cell': 38,
        'attempt_counter_cell': 64,
        'low_memory_1x94_core': [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 36, 37, 38, 41, 42, 43, 45, 46, 47, 48, 50, 52, 53, 54, 60, 62, 63, 64, 70, 74, 75, 76, 77, 79, 80, 81, 84],
        'domain': {'initial': [1, 3], 'candidate_1': [1, 3], 'candidate_2': [1, 3], 'candidate_3': [1, 3]},
        'committed_state_by_initial': {'1': {'mem36': 29526, 'output': 'VVV'}, '3': {'mem36': 29522, 'output': 'RRR'}},
        'epochs': 3,
        'max_attempts_per_epoch': 2,
    }


def main():
    root = Path(__file__).resolve().parents[1]
    builders = {'m1a_rot10': lambda: build_reversible(),
                'm1a_rot9_negative': lambda: build_reversible(9)}
    builders.update({f'm1b_{mode}': lambda m=mode: build_checkpoint(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'early_halt', 'output_impostor']})
    builders.update({f'm1c_{mode}': lambda m=mode: build_conditional(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'no_restore', 'no_recovery', 'broken_return', 'early_halt', 'force_retry_failure']})
    builders.update({f'm1e_{mode}': lambda m=mode: build_m1e(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'no_restore', 'no_recovery', 'broken_return', 'early_halt', 'output_impostor', 'force_retry_failure', 'force_retry_stall']})
    builders.update({f'm2_{mode}': lambda m=mode: build_m2(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'no_restore', 'broken_rearm', 'force_retry_failure', 'output_impostor']})
    builders.update({f'm3_{mode}': lambda m=mode: build_m3(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'no_restore', 'broken_rearm', 'broken_return', 'force_retry_failure', 'output_impostor', 'eof_unmasked']})
    for name, builder in builders.items():
        source, meta = builder()
        (root/'candidates'/f'{name}.mal').write_bytes(source)
        (root/'candidates'/f'{name}.json').write_text(json.dumps(meta, indent=2)+'\n')
        print(name, len(source), meta)


if __name__ == '__main__':
    main()
