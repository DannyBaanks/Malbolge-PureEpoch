# Compose — M1: Autonomous rollback gate in pure Classic Malbolge

## Objective

Use `DannyBaanks/Autobolge` and `DannyBaanks/BolgeForge` to synthesize **one
strict-valid Classic Malbolge artifact** that contains all runtime machinery
needed for a *bounded* in-program save / corrupt / conditional restore / retry.

- Compiler/generator/verifier: may be external tools at build/test time.
- Target execution: **must use unmodified Classic Malbolge**, without any
  external state injection, snapshot-based resume, host-driven epochs, output
  substitution, invented opcodes, custom VM opcodes or hidden repair.
- Any verifier/instrumentation is observational: it cannot affect execution.

## Grounded starting point

- Autobolge `ROADMAP.md`: F0–F7 completed; external `EpochAnchorV1`, per-step
  traces, replay, causal-memory tests and Zig/Python parity controls already
  exist. These prove **external reproducibility**, not in-VM autonomy.
- BolgeForge `artifacts/truth_machine_classic_90b.mal`: strict-valid; its
  registers + all 59049 memory cells repeat after 408 instructions while
  producing 17 `1` bytes. Original by Weird Glyphs, CC BY-SA 4.0.
- M0 local probe: 408-step exact cycle reproduced and an injected persistent
  fault was **not** autonomously restored (negative result).
- BolgeForge `artifacts/cat_compact.mal`: 7972 cells with a verified internal
  handoff, but no claimed autonomous rollback.

## Important conceptual boundary

A cycle returning to its old state is **not** a rollback triggered by failure.
A tape region observed untouched is **not** reserved/protected memory.
A state captured in Python/Zig is **not** a Malbolge internal checkpoint.

## Build sequence

### M1a — Reversible cell subroutine

Find/construct a strict-valid Malbolge routine that uses original opcodes
(e.g., rotations and data-pointer steering) to mutate one selected cell then
restore its original value while control continues. Verify entire VM state,
not only emitted output. Record touched addresses and actual instruction count.

### M1b — In-program saved checkpoint

Require a source-program cell or data location whose previous value is
preserved **inside** Malbolge, then modified and restored from that saved
representation. Do not accept a verifier copying the prior value back.

### M1c — Conditional failure branch and retry

Candidate checks a bounded invariant internally. Valid candidate commits;
invalid candidate branches to a recovery region, restores the pre-attempt
values, and retries a corrected case. It must visibly produce distinct
commit and rollback traces under at least two input cases, without host
altering its registers or memory.

### M1d — Limited fault test

Inject an error via **ordinary program input** or code-internal candidate
choice rather than an out-of-band VM memory patch. Artificial fault injection
may be used additionally as a negative test but never as the successful
runtime recovery mechanism.

## Measurement and gates

- Strict Olmstead loader accepts source on its real load addresses.
- Both strict oracle C (`mb_ref`) and an independent mirror reproduce output,
  stop reason, and deterministic register/memory checkpoints (account for
  documented differences in EOF semantics before claiming parity).
- Recovery is demonstrated at **actual Malbolge instruction addresses**.
- Check the complete `(a,c,d,59049 memory cells,input cursor,output)` context
  as appropriate. Output already emitted cannot be rolled back: use a commit
  barrier if effects must be transactional.
- Prove parent/candidate state isolation if claiming two memory banks.
- Publish exact source bytes, hashes, transcript, trace hashes, CLI commands,
  machine semantic version and source commit IDs.
- Negative controls: remove recovery branch; corrupt journal; force
  repeated failure; exhaust budget; destroy return path. No PASS if silent
  host intervention rescues a case.
- No unbounded self-repair, cryptographic security, VDF, JIT speed, or
  commercial capability is asserted from these bounded tests.

## Required result classification

`DEMONSTRATED`: tests prove a scoped claim with raw artifact + independent
verification. `INFERRED`: a reasonable interpretation not fully established.
`NOT_DEMONSTRATED`: missing evidence. `DESTROYED`: a claim contradicted by a
control. Report failures and limitations, including possibility of a no-go.

## Stop conditions

Stop and report `NOT_DEMONSTRATED` if no strict-valid candidate exists within
budget, if the recovery depends on a host API or if output-only equality hides
different memory. Do not quietly weaken the pure-Malbolge criterion.
