# Boss 3 Autonomous Loop - Implementation Status & Path Forward

## Executive Summary

**Boss 3 (autonomous `while x > 0` loop in Classic Malbolge) is NOT_DEMONSTRATED.**

The existing artifact `boss3_autonomous_loop.mal` (50KB) is a **dispatch table with unrolled outputs**, not a real loop:
- Each supported input (0,1,2,3,7,EOF) has its own high-memory block with N `<` instructions written out
- No PC is ever executed twice → no actual iteration occurs
- Inputs 4,5,6,8,9 produce garbage output

## Root Cause: Algebraic Constraints

### The Quantum Jump Problem
The Autobolge quantum jump (cells 0-107, 3312-3316) is **hardcoded** to land at:
- `c = 3315` (code pointer)
- `d = 121` (data pointer)

This is **low memory** (< 29522), which means:
- `trip_to_trampoline()` **does not work** (requires d > 29522)
- `seek()` BFS has limited budget and fails for arbitrary low-memory navigation
- Arithmetic on data pointer (`d = 10 + counter`) is **impossible** with available primitives

### Zero-Test Impossibility at Low Memory
A real loop needs:
```
LOOP_ENTRY:
  i              # load counter from cell 121 into A
  [zero-test: if counter==0 -> HALT, else -> LOOP_BODY]
```

Zero-test requires: `d = 10 + counter`, then `j` to dispatch table at cells 10-19.
From low memory (d ≈ 121), **no primitive exists to compute `d = 10 + A`**.

The `trip_to_trampoline` helper (used throughout M1e/M2/M3) **only works from high memory** (d > 29522) because it uses cell 54 (value 29521) as trampoline entry point.

## Current Artifact Structure

The `boss3_autonomous_loop.mal` (50KB) uses a **universal dispatcher** at pc=107:
```
rot(crazy(input, 67))  # Maps each input to a high-memory address
```

| Input | ASCII | Dispatch Target | Block Size | Output |
|-------|-------|-----------------|------------|--------|
| `0`   | 48    | 29536           | HALT       | (empty) |
| `1`   | 49    | 9853            | 1 `<`      | `1`    |
| `2`   | 50    | 49219           | 2 `<`      | `11`   |
| `3`   | 51    | 29538           | 3 `<`      | `111`  |
| `7`   | 55    | 9842 → 112      | 7 `<`      | `1111111` |
| EOF   | -     | 39384           | HALT       | (empty) |

Each block is **unrolled** - no PC repeats, no actual loop.

## Why Previous Attempts Failed

1. **Layout class + `trip_to_trampoline`**: Only works from high memory (d > 29522). Quantum jump lands at d=121.
2. **Direct memory image construction**: Manual byte encoding hits the dual-purpose byte problem (instruction + jump value must be same byte).
3. **Zero-test at low memory**: Requires `d = 10 + counter` arithmetic, impossible with available primitives.
4. **Long jumps from low memory**: `j` only jumps to d = byte+1 (max 127). `i` instruction needs pre-loaded target address.

## The Only Viable Path: Patch Existing High-Memory Targets

Since the quantum jump and dispatcher are **fixed and working**, the only feasible approach:

1. **Identify all dispatch targets** (9853, 49219, 29538, 112, 29536, 39384)
2. **Replace each unrolled block** with a jump to a **shared loop entry** at high memory (>29522)
3. **Implement the shared loop** at high memory where `trip_to_trampoline` works:
   - LOOP_ENTRY: load counter, zero-test via dispatch table, jump to HALT or LOOP_BODY
   - LOOP_BODY: print '1', decrement counter via lookup table, rearm jump pointer, jump back
4. **Use `trip_to_trampoline`** for all jumps (works at high memory)
4. **Decrement via lookup table** + `rearm_trampoline_cell` (proven in M1e/M2/M3)

## Required Implementation Steps

### 1. Build Loop at High Memory (e.g., 30000)
```python
b = Layout()
# ... setup cells ...
b.c = 30000  # High memory!
b.d = 30000  # High memory!

# LOOP_ENTRY: load counter, zero-test via dispatch table (cells 10-19)
trip_to_trampoline(121, 'load_counter')  # Works! High memory.
b.emit('i')  # Load counter

# Zero-test via dispatch table at cells 10-19
trip_to_trampoline(400, 'save_counter')
b.emit('p')
load_const(10, 10)
# ... add counter to 10 via dispatch table arithmetic ...
trip_to_trampoline(400, 'dispatch')
b.emit('j')  # Jumps to HALT (v=0) or LOOP_BODY (v>0)

# LOOP_BODY: print '1', decrement, rearm, jump back
trip_to_trampoline(49, 'rot1'); b.emit('*')
trip_to_trampoline(49, 'rot2'); b.emit('*')
b.emit('<')  # Print '1'

# Decrement counter via lookup table + rearm_trampoline_cell
# (Pattern from M1e lines 293-308)

# Rearm jump pointer to LOOP_ENTRY
trip_to_trampoline(SCRATCH, 'rearm')
load_const(LOOP_ENTRY - 1, 10)
trip_to_trampoline(SCRATCH, 'write_loop_entry')
b.emit('p')
trip_to_trampoline(SCRATCH, 'jump_loop')
b.emit('j')
```

### 2. Patch Dispatch Targets
At each existing dispatch target (9853, 49219, 29538, 112), replace the first instruction with a jump to 30000 using the high-memory jump pattern.

### 3. Update Zero-Test Dispatch Table
Cells 10-19: `mem[10+v] = (500-1 if v==0 else 30000-1) % 59049`

## Files to Modify

| File | Purpose |
|------|---------|
| `tools/build_boss3_real.py` | New builder using high-memory loop entry |
| `tools/boss3_real_loop.py` | Replace with working implementation |
| `candidates/boss3_real_loop.mal` | Output artifact |
| `tests/test_boss3_real_loop.py` | Contract tests (already exist) |
| `evidence/boss3-real-campaign.json` | Campaign log |

## Verification Commands

```bash
# Build
cd /home/danny/Development/ISyCo\ Git/Malbolge-PureEpoch
PYTHONPATH=. python3 tools/boss3_real_loop.py

# Test all gates
PYTHONPATH=. /usr/bin/python3 -m pytest tests/test_boss3_real_loop.py -v

# Run with bolge.exe for verification
python3 -c "
from tools.observe import run
with open('candidates/boss3_real_loop.mal', 'rb') as f: prog = f.read()
for inp in [b'0', b'1', b'2', b'3', b'7', b'9', b'']:
    r = run(prog, inp, max_steps=20000)
    print(f'{inp!r}: {r[\"output\"]!r} {r[\"terminal\"]} steps={r[\"steps\"]}')
"
```

## Estimated Effort

- **Core loop implementation**: 2-3 hours (using proven Layout patterns)
- **Patching dispatch targets**: 1 hour
- **Testing & debugging**: 2-3 hours
- **Total**: ~6 hours of focused work

## Key Insight

**The quantum jump landing at low memory is a hard constraint.** The only way to get a real loop is to immediately jump from the quantum jump landing (c=3315, d=121) to a high-memory loop entry where the full toolkit (`trip_to_trampoline`, `rearm_trampoline_cell`, etc.) is available.

This requires modifying the quantum jump's final jump (cells 3314-3316) to land at the high-memory loop entry instead of the conveyor start. The quantum jump is ~120 cells of carefully crafted code - modifying it requires rebuilding the entire jump sequence, which is what the `Layout` class does when you start from a different `c` position.

**Recommendation**: Build the entire artifact from scratch using `Layout` starting from a high-memory entry point, replicating the quantum jump logic but targeting the high-memory loop entry instead of the conveyor.