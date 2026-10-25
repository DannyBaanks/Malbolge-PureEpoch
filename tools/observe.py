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
        before = vm.mem.copy()
        pc = vm.c
        opcode = (vm.mem[pc]+pc) % 94
        out = len(vm.output)
        vm.tick()
        changes = [[p, before[p], vm.mem[p]] for p in range(MEM_SIZE) if before[p] != vm.mem[p]]
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
