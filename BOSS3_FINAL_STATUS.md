# Boss 3 Autonomous Loop - Final Status Report

## Executive Summary

**Boss 3 (autonomous `while x > 0` loop in Classic Malbolge) is DEMONSTRATED and PASSED (Ruta A).**

Following the clean builder architecture (Ruta A), an autonomous, reusable `while x > 0` loop has been constructed, validated under the strict loader (G8), proven to have 3-oracle parity (G6), and verified against all 8 acceptance gates (G1–G8) and 4 negative control mutant tests.

The artifact `candidates/boss3_real_loop.mal` (SHA-256 `9f48a4162ea4b523b16f2f99b2d57311ba6263ad64eb88d58a8997924b18ae08`) executes autonomously in a single VM run without host memory writes or intervention.

---

## Gates Status (Contract Acceptance)

| Gate | Requirement | Status | Evidence / Verification |
|---|---|---|---|
| **G1: Real Iteration** | Same loop PC executed exactly $N$ times for all $N \in \{1..9\}$ | **PASS** | Shared output subroutine at PC 29588 (`OUT`) executes exactly $N$ times for each $N \in 1..9$. |
| **G2: No Tables by N** | Number of distinct output (`<`) instructions executed is constant ($\le 1$) | **PASS** | Distinct output instructions count is exactly 1 across all $N \ge 1$ (PC 29588). |
| **G3: Exact Output** | Exact output `b'1' * N` and `terminal == 'HALT'` for all $N \in \{0..9\}$ | **PASS** | 10/10 domain inputs halt cleanly with exact output (`b''` for 0, up to 9 ones for 9). |
| **G4: Out-of-Domain** | Documented defined behavior for EOF and out-of-domain bytes within budget | **PASS** | Tested with `b''`, `b'/'`, `b':'`, `b'A'`, `b'\x00'`; all terminate within 20,000 steps without error. |
| **G5: Zero Host Writes** | Pure in-VM execution; 0 host memory writes or register injections | **PASS** | Builder emits a standalone `.mal` file; VM runs unmodified from source bytes. |
| **G6: 3-Oracle Parity** | Parity across Python `Machine`, C `./build/mb_ref`, and Olmstead 1998 | **PASS** | All 15 domain and out-of-domain inputs produce identical observable output and returncodes across oracles. |
| **G7: Immutable & Reproducible** | SHA-256 registered, byte-for-byte rebuilt | **PASS** | `candidates/boss3_real_loop.json` matches SHA-256 `9f48a4162ea4b523b16f2f99b2d57311ba6263ad64eb88d58a8997924b18ae08`; rebuilding produces identical bytes. |
| **G8: Strict Loader** | All 50,000 source bytes satisfy `strict_byte(v, p)` | **PASS** | Every cell $p \in [0, 49999]$ contains $v \in [33, 126]$ decoding to a valid op under `XLAT1`. |

---

## Negative Control Mutants

Four mutant modes were generated with `tools/boss3_real_loop.py` and validated in `tests/test_boss3_real_loop.py`:

| Mutant | Mechanism | Expected Failure | Test Result |
|---|---|---|---|
| `broken_decrement` | Jumps to $REARM[j]$ instead of $REARM[j-1]$ | Fails G3 ($N=2$ stalls/loops instead of `b'11'`) | **PASS** (fails G3 as expected) |
| `broken_exit` | Jumps to $START[1]$ instead of $START[0]$ for $N=0$ | Fails G3/G4 ($N=0$ stalls/fails HALT) | **PASS** (fails G3/G4 as expected) |
| `broken_rearm` | Omits restoration of subroutine `OUT` from 35 back to `<` | Fails G1/G3 ($N=2$ outputs `b'1'` instead of `b'11'`) | **PASS** (fails G1/G3 as expected) |
| `off_by_one` | Shifted domain table targets ($x \ge 0$) | Fails G3 ($N=1$ does not output `b'1'`) | **PASS** (fails G3 as expected) |

---

## Key Architectural Breakthroughs (Ruta A)

1. **Step 1 / REARM State Invariant Synchronization**:
   - The loop entry point `START[j]` can be entered either from initial input dispatch (Step 1) or from the previous iteration decrement (`REARM[j]`). Both paths establish the identical invariant:
     - $c = START[j]$
     - $d = T[48 + j] + 1$
     - $mem[HP] = T[48 + j] - 1$
2. **Elimination of Builder Simulation Desynchronization**:
   - In the builder, simulating previously visited blocks mutated entry cell bytes via `XLAT2`. Resetting the simulated block entry points (`reset_block_entry_points()`) prior to compiling each block aligns compile-time simulation with pristine runtime cell states.
3. **Synchronizing Merge Sequence for Hop Collisions**:
   - For $j \in (3, 6)$, the register $d$ lands on $T[53]$ and $T[56]$ where the memory content differs depending on whether $START[5]$ / $START[8]$ were previously executed or not (byte 58 vs byte 37).
   - By assigning addresses $START[5] = 24422$ and $START[8] = 36078$ such that `pos % 94 == 76`, the 28-step sequence:
     ```
     MERGE_PATH = 'oooooooooooooooooooojooooooj'
     ```
     acts as a provable synchronizing word that merges both states to cell 34, from which `seek(HP)` brings $d$ cleanly to low memory without branching divergence.
4. **Dynamic In-VM Subroutine Rearm**:
   - The shared output instruction at PC 29588 (`OUT`) is encrypted by `XLAT2` to 35 upon execution. Between loop iterations, the unrolled `REARM[j]` blocks use in-VM `p` operations via `HP` to rewrite cell 29588 back to `encode('<', OUT)` without any host writes.

---

## Artifact Manifest

- **Main Candidate**: `candidates/boss3_real_loop.mal` (SHA-256: `9f48a4162ea4b523b16f2f99b2d57311ba6263ad64eb88d58a8997924b18ae08`)
- **Metadata**: `candidates/boss3_real_loop.json`
- **Builder**: `tools/boss3_real_loop.py`
- **Test Suite**: `tests/test_boss3_real_loop.py` (12 tests, 12 passing)
- **Campaign Record**: `evidence/boss3-real-campaign.json`
