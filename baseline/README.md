# Malbolge Pure Epoch Lab — M0

**Goal:** build the smallest observable evidence base for *in-language* self-recovery.

This experiment observes **unmodified Classic Malbolge execution** of the
strict-valid, 90-byte Truth Machine reproduced in BolgeForge. It records
full-state cycle evidence, mutation footprint and an untouched memory interval.

**The Python observer is NOT a runtime supervisor.** It never restores,
re-synthesizes or feeds state back to the running Malbolge target. The
negative control deliberately corrupts a cell in a separate test copy to
show what the source *does not* repair.

## Run

Python 3.10+ with only the standard library:

```sh
cd malbolge_epoch_lab
python3 -m unittest -v test_epoch_probe.py
python3 epoch_probe.py truth_machine_classic_90b.mal > report.json
```

To verify the original claim separately with the real repository's strict
oracle, use BolgeForge's `make` and `tools/prove_truth_machine.py`.

The included 90-byte truth-machine source is by **Weird Glyphs** and licensed
CC BY-SA 4.0; see `ATTRIBUTION.md`. Its original published provenance is in
`BolgeForge/docs/provenance/truth_machine_90b.json`. The Python probe code is
new measurement tooling, not part of the target program.

## Gates

- G0: strict Classic loader accepts the actual 90-byte source.
- G1: exact repeated `(a,c,d,input_cursor)` and **all 59,049 memory cells**.
- G2: epoch emits nonempty output while preserving full VM state cycle.
- G3: observed mutation footprint / largest untouched contiguous interval,
  **without asserting access protection or irrelevance**.
- G4: injected corruption in a never-touched region **must not** magically
  recover. The negative result prevents conflating repetition with repair.

## Not demonstrated

No autonomous checkpoints, conditional rollback, runtime synthesis,
self-correcting branches, protected reserved memory or commercial cryptographic
capabilities. `COMPOSE_M1.md` defines the next falsifiable, pure-Malbolge gate.

Boundary: Python/Zig/C are allowed as offline assemblers and observers. If
any of them performs a transition, recovery, writeback or runtime repair,
that experiment does **not** demonstrate autonomous pure-Malbolge rollback.
