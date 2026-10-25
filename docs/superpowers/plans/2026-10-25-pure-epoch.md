# Pure Epoch implementation plan

> Execute inline using superpowers:executing-plans; independently review the completed experiment before reporting.

**Goal:** find the smallest reproducible pure Classic internal recovery property without conflating reversibility, checkpoint, conditional rollback or retry.

**Architecture:** a new standalone lab on `codex/pure-epoch-m1`; immutable copies of supplied M0; offline strict-address assembler; Python observer plus unchanged strict C oracle and original Olmstead interpreter. Additive C instrumentation exports full step transitions and final memory for state parity. Toroidal investigation owns only `torus/`.

**Tech stack:** Python 3 standard library, gcc, existing Autobolge/BolgeForge sources pinned by commit.

**Spec:** `COMPOSE_SOL.md` and the supplied toroidal addendum.

## Constraints

- Runtime starts from the `.mal` source and ordinary stdin, once. No host writes or snapshot resume.
- Preserve certified artifacts, historical reports, and original repository worktrees.
- Every claim receives DEMONSTRATED, INFERRED, NOT_DEMONSTRATED or DESTROYED.
- M2 is gated by M1c/M1d. An offline integration is never runtime synthesis.
- Research budget: constructive trials first; at most 128 bounded journal/layout trials, 5,000 instructions per small candidate. No unbounded exhaustive search.

## Review focus

- A correct output with a wrong final target must fail the state contract.
- Journal corruption must change recovery; predetermined rotations alone do not establish checkpoint use.
- EOF, loader and encryption divergence must be explicit, including upstream tests.
- Trace instrumentation must be observational; unchanged C and original Olmstead must reproduce outputs.
- Physical code/journal changes are not full-state rollback; target logical equivalence is explicitly scoped.

## Tasks

### 1. Baseline and source freeze

- [x] Read complete compose and all seven M0 files; reproduce M0 before lab creation.
- [x] Record original git status and commits, compare remote heads, create an isolated laboratory.
- [ ] Save baseline reproduction, source/binary hashes and raw upstream regression logs.

### 2. Strict constructive candidates and verification

Files: `tools/build_candidates.py`, `tools/observe.py`, `tests/test_candidates.py`, `candidates/*.mal`, additive C observer under `tools/`.

Interfaces: `build_reversible(rotations=10, initial=37) -> (bytes, metadata)`; `build_checkpoint(mode='normal') -> (bytes, metadata)`; `observe.run(source, payload, max_steps=5000) -> dict` including full final memory and per-step changes.

- [ ] Write behavioral tests first: ten rotations restore cell 96 to 37, nine fail; a saved journal recovers target cell 36 for two inputs, corrupt/remove journal fails; output-only impostor fails state checks.
- [ ] Observe RED, implement offline assembly and observational execution, observe GREEN.
- [ ] Compile unchanged C and original Olmstead; add observational C trace/dump; compare traces, complete final memory, stdout and stop reasons.
- [ ] Attempt a bounded conditional route/retry only after checkpoint evidence. Preserve candidate failures; do not weaken gates.

### 3. Evidence, addendum, review

- [ ] Generate raw traces, hashes, manifests, measurements, exact reproduction commands, failures, results, verdict and next compose.
- [ ] Integrate toroidal evidence separately; no rollback claims from access projections.
- [ ] Run complete lab suite, review through a fresh subagent, address substantive findings with regressions.
- [ ] Commit the standalone lab and report achieved gates, exclusions and next experiment.
