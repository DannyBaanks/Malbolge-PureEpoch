"""Offline construction only. Every byte is valid at its actual Classic address."""
from pathlib import Path
import json
from collections import deque

from baseline.epoch_probe import XLAT1, VALID


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


def main():
    root = Path(__file__).resolve().parents[1]
    builders = {'m1a_rot10': lambda: build_reversible(),
                'm1a_rot9_negative': lambda: build_reversible(9)}
    builders.update({f'm1b_{mode}': lambda m=mode: build_checkpoint(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'early_halt', 'output_impostor']})
    builders.update({f'm1c_{mode}': lambda m=mode: build_conditional(m)
                     for mode in ['normal', 'no_save', 'corrupt_journal', 'no_restore', 'no_recovery', 'broken_return', 'early_halt', 'force_retry_failure']})
    for name, builder in builders.items():
        source, meta = builder()
        (root/'candidates'/f'{name}.mal').write_bytes(source)
        (root/'candidates'/f'{name}.json').write_text(json.dumps(meta, indent=2)+'\n')
        print(name, len(source), meta)


if __name__ == '__main__':
    main()
