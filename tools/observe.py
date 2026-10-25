"""Read-only execution observer using the preserved M0 Classic implementation.

No snapshots are injected or restored. Each run starts from the source loader.
The observer retains before/after values exclusively for comparisons and traces.
"""
from baseline.epoch_probe import Machine, MEM_SIZE, XLAT1, VALID, crazy


def load(source):
    cells = []
    for pos, byte in enumerate(source):
        if byte in (9, 10, 11, 12, 13, 32):
            continue
        if not 33 <= byte <= 126:
            raise ValueError(f"non-ASCII printable byte at file offset {pos}")
        instruction = XLAT1[(byte - 33 + len(cells)) % 94]
        if instruction not in VALID:
            raise ValueError(f"strict loader rejects position {len(cells)}: {instruction!r}")
        cells.append(byte)
    if not 2 <= len(cells) <= MEM_SIZE:
        raise ValueError("program must occupy 2..59049 cells")
    while len(cells) < MEM_SIZE:
        cells.append(crazy(cells[-1], cells[-2]))
    return cells


def run(source, payload, max_steps=5000):
    vm = Machine(load(source), payload)
    trace = []
    for step in range(max_steps):
        pre = list(vm.regs())
        pc = vm.c
        opcode = (vm.mem[pc]+pc) % 94
        out = len(vm.output)
        watched = {pc, vm.d}
        if 0 <= vm.d < MEM_SIZE and 0 <= vm.mem[vm.d] < MEM_SIZE:
            watched.add(vm.mem[vm.d])
        before = {p: vm.mem[p] for p in sorted(watched) if 0 <= p < MEM_SIZE}
        vm.tick()
        changes = [[p, before[p], vm.mem[p]] for p in sorted(before) if before[p] != vm.mem[p]]
        trace.append({'step': step, 'pre': pre, 'opcode': opcode,
                      'post': list(vm.regs()), 'changes': changes,
                      'output': list(vm.output[out:]), 'terminal': vm.terminal})
        if vm.terminal != 'RUNNING':
            break
    else:
        vm.terminal = 'BUDGET'
    return {'terminal': vm.terminal, 'memory': vm.mem, 'registers': list(vm.regs()),
            'output': vm.output, 'steps': vm.steps, 'trace': trace}


def target_contract(result, address, expected):
    return result['terminal'] == 'HALT' and result['memory'][address] == expected


def conditional_contract(result, meta, initial, candidate):
    """Logical transaction protocol; final stdout/state alone are insufficient."""
    if initial not in (1,3) or candidate not in (1,3):
        return False
    labels = meta['labels']
    trace = result['trace']
    def events(label):
        return [e for e in trace if e['pre'][1] == labels[label]]
    if not (target_contract(result, 36, 29523) and result['memory'][52] == initial
            and result['output'] == b'S' and result['registers'][3] == 2):
        return False
    save = events('save')
    dispatch = events('dispatch')
    if not (len(save) == 1 and save[0]['opcode'] == 62 and save[0]['post'][0] == initial):
        return False
    if not (len(dispatch) == 1 and dispatch[0]['opcode'] == 4
            and dispatch[0]['pre'][2] == 36 and dispatch[0]['post'][1] == (29524 if candidate == 1 else 29522)):
        return False
    if any(e['output'] and e['pre'][1] != labels['commit'] for e in trace):
        return False
    restored, retried = events('restore'), events('retry')
    if candidate == 1:
        return not restored and not retried
    if not (len(restored) == len(retried) == 1):
        return False
    restore = restored[0]
    again = events('retry_dispatch')
    return (restore['opcode'] == 62 and restore['pre'][0] == initial
            and restore['post'][0] == 29524-initial
            and [36,29524,29524-initial] in restore['changes']
            and restore['step'] < retried[0]['step']
            and retried[0]['opcode'] == 62 and retried[0]['post'][0] == 29523
            and len(again) == 1 and again[0]['post'][1] == 29524)


def m1e_contract(result, meta, initial, candidate):
    """Step 2 & Step 3 contract for M1e:
    - Committed target state and stdout depend on restored prior datum:
      initial=1 -> mem[36]=29526, output=b'V'
      initial=3 -> mem[36]=29522, output=b'R'
    - Internal attempt counter in cell 64 equals 29528 (1 attempt) or 7 (2 attempts).
    - Control no_restore fails both final observable output (b'') and final logical state (mem[36]=29528).
    """
    if initial not in (1, 3) or candidate not in (1, 3):
        return False
    labels = meta['labels']
    trace = result['trace']
    def events(label):
        return [e for e in trace if label in labels and e['pre'][1] == labels[label]]
    expected_mem36 = 29526 if initial == 1 else 29522
    expected_out = b'V' if initial == 1 else b'R'
    expected_commit_label = 'commit_1' if initial == 1 else 'commit_3'
    expected_commit_pc = labels[expected_commit_label]
    expected_attempts = 29528 if candidate == 1 else 7
    if not (target_contract(result, 36, expected_mem36)
            and result['memory'][52] == initial
            and result['memory'][64] == expected_attempts
            and result['output'] == expected_out
            and result['registers'][3] == 2):
        return False
    save = events('save')
    dispatch = events('dispatch')
    count1 = events('count_attempt_1')
    if not (len(save) == 1 and save[0]['opcode'] == 62 and save[0]['post'][0] == initial):
        return False
    if not (len(count1) == 1 and [64, 29524, 29528] in count1[0]['changes']):
        return False
    expected_first_landing = expected_commit_pc if candidate == 1 else labels['failure_route']
    if not (len(dispatch) == 1 and dispatch[0]['opcode'] == 4
            and dispatch[0]['pre'][2] == 36 and dispatch[0]['post'][1] == expected_first_landing):
        return False
    if any(e['output'] and e['pre'][1] != expected_commit_pc for e in trace):
        return False
    restored, retried = events('restore'), events('retry')
    count2 = events('count_attempt_2')
    if candidate == 1:
        return not restored and not retried and not count2
    if not (len(restored) == len(retried) == len(count2) == 1):
        return False
    if [64, 29528, 7] not in count2[0]['changes']:
        return False
    rotations = [events(f'journal_read_rotation_{i+1}') for i in range(10)]
    if not all(len(r) == 1 and r[0]['opcode'] == 39 for r in rotations):
        return False
    restore = restored[0]
    again = events('retry_dispatch')
    return (restore['opcode'] == 62 and restore['pre'][0] == initial
            and restore['post'][0] == 29524 - initial
            and [36, 29524, 29524 - initial] in restore['changes']
            and restore['step'] < retried[0]['step']
            and retried[0]['opcode'] == 62 and retried[0]['post'][0] == expected_mem36
            and len(again) == 1 and again[0]['post'][1] == expected_commit_pc)


def m2_journal_consumption(result, meta):
    """Exact journal save/rotation/restore accounting across Epoch 1 and Epoch 2."""
    labels = meta['labels']
    trace = result['trace']
    def events(label):
        return [e for e in trace if label in labels and e['pre'][1] == labels[label]]
    e1_rots = sum(len(events(f'epoch1_journal_read_rotation_{i+1}')) for i in range(10))
    e2_rots = sum(len(events(f'epoch2_journal_read_rotation_{i+1}')) for i in range(10))
    return {
        'epoch1_saves': len(events('epoch1_save')),
        'epoch1_journal_rotations': e1_rots,
        'epoch1_restores': len(events('epoch1_restore')),
        'epoch2_saves': len(events('epoch2_save')),
        'epoch2_journal_rotations': e2_rots,
        'epoch2_restores': len(events('epoch2_restore')),
        'total_journal_rotations': e1_rots + e2_rots,
        'journal_final_value': result['memory'][52],
    }


def m2_contract(result, meta, initial, cand1, cand2):
    """Step 4 contract for M2: two complete epochs in a single Classic Malbolge process."""
    if initial not in (1, 3) or cand1 not in (1, 3) or cand2 not in (1, 3):
        return False
    labels = meta['labels']
    trace = result['trace']
    def events(label):
        return [e for e in trace if label in labels and e['pre'][1] == labels[label]]
    expected_mem36 = 29526 if initial == 1 else 29522
    expected_out = b'VV' if initial == 1 else b'RR'
    expected_commit_label = 'commit_1' if initial == 1 else 'commit_3'
    expected_commit_pc = labels[expected_commit_label]
    expected_e2_attempts = 29528 if cand2 == 1 else 7
    if not (target_contract(result, 36, expected_mem36)
            and result['memory'][52] == initial
            and result['memory'][64] == expected_e2_attempts
            and result['output'] == expected_out
            and result['registers'][3] == 3):
        return False
    out_events = [e for e in trace if e['output']]
    if len(out_events) != 2 or any(e['pre'][1] != expected_commit_pc for e in out_events):
        return False
    e1_save = events('epoch1_save')
    e2_entry = events('epoch2_entry')
    e2_prep = events('epoch2_prepare_target')
    e2_save = events('epoch2_save')
    if not (len(e1_save) == 1 and e1_save[0]['opcode'] == 62 and e1_save[0]['post'][0] == initial):
        return False
    if not (len(e2_entry) == 1 and len(e2_prep) == 1 and e2_prep[0]['post'][0] == 29524 - initial):
        return False
    if not (len(e2_save) == 1 and e2_save[0]['opcode'] == 62 and e2_save[0]['post'][0] == initial):
        return False
    if not (e1_save[0]['step'] < out_events[0]['step'] < e2_entry[0]['step'] < e2_save[0]['step'] < out_events[1]['step']):
        return False
    # Verify Epoch 1 dispatch and recovery/retry:
    e1_disp = events('epoch1_dispatch')
    e1_landing = expected_commit_pc if cand1 == 1 else labels['failure_route']
    if not (len(e1_disp) == 1 and e1_disp[0]['opcode'] == 4 and e1_disp[0]['post'][1] == e1_landing):
        return False
    e1_rest, e1_ret, e1_rdisp = events('epoch1_restore'), events('epoch1_retry'), events('epoch1_retry_dispatch')
    if cand1 == 1:
        if e1_rest or e1_ret or e1_rdisp:
            return False
    else:
        if not (len(e1_rest) == len(e1_ret) == len(e1_rdisp) == 1):
            return False
        if not ([36, 29524, 29524 - initial] in e1_rest[0]['changes']
                and e1_ret[0]['post'][0] == expected_mem36
                and e1_rdisp[0]['post'][1] == expected_commit_pc):
            return False
    # Verify Epoch 2 dispatch and recovery/retry:
    e2_disp = events('epoch2_dispatch')
    e2_landing = expected_commit_pc if cand2 == 1 else labels['failure_route']
    if not (len(e2_disp) == 1 and e2_disp[0]['opcode'] == 4 and e2_disp[0]['post'][1] == e2_landing):
        return False
    e2_rest, e2_ret, e2_rdisp = events('epoch2_restore'), events('epoch2_retry'), events('epoch2_retry_dispatch')
    if cand2 == 1:
        if e2_rest or e2_ret or e2_rdisp:
            return False
    else:
        if not (len(e2_rest) == len(e2_ret) == len(e2_rdisp) == 1):
            return False
        if not ([36, 29524, 29524 - initial] in e2_rest[0]['changes']
                and e2_ret[0]['post'][0] == expected_mem36
                and e2_rdisp[0]['post'][1] == expected_commit_pc):
            return False
    jc = m2_journal_consumption(result, meta)
    expected_e1_rots = 0 if cand1 == 1 else 10
    expected_e2_rots = 0 if cand2 == 1 else 10
    return (jc['epoch1_journal_rotations'] == expected_e1_rots
            and jc['epoch2_journal_rotations'] == expected_e2_rots)
