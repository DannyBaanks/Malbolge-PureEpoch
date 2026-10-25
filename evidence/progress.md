# Pure Epoch experiment ledger

Spec: COMPOSE_SOL.md. Plan: docs/superpowers/plans/2026-10-25-pure-epoch.md.

M0 reproduced before any file creation: 5/5; exact 408/17 cycle, negative fault persists.
Ruling: use a standalone isolated laboratory rather than a worktree — explicitly permitted by the user; original worktrees contain unrelated untracked research.
Ruling: preserve extracted M0 verbatim — original ZIP was not present in supplied attachment/search locations.
Ruling: clone remote heads separately and record local commits too — the remote heads differ from the local worktrees, and neither is silently substituted for the other.
Pre-flight: assembler emits bytes/metadata; observer consumes only bytes/stdin; independent C consumes the same exact artifact. Observer state is never fed into runtime.

Task 1: complete — baseline hashes and JSON identical; original local states preserved; remote clones separately pinned.
Task 2: complete — RED logs captured before each implementation; 16 lab tests GREEN. M1a/b and bounded conditional restore/retry implemented; 19 raw cases have transition and full-memory parity.
Ruling: use a closed two-value indirect dispatch and one corrected unrolled transition — this yields a small executable property; it does not establish a general comparator, reusable continuation or exhaustion handler.
Ruling: verify restore as an intermediate logical protocol — the fixed committed result can be reached by skipping it, so final stdout/target alone cannot certify the recovery claim. Both this limitation and the no_restore falsification are explicit in RESULTS.md.
Ruling: preserve the standalone branch without merging/pushing — the user requested an isolated experiment and immutable certified baselines; this new lab has no upstream integration target.
Task 3: evidence complete, final fresh-context review completed and regressions resolved (20/20 lab tests, 5/5 M0 baseline tests, 6/6 torus tests GREEN; `evidence/review-red.txt` and `evidence/review-green.txt` preserved). Toroidal agent stayed under its 400M-instruction cap and delivered six passing small tests; raw long runs will not be repeated.
Final source audit: original Autobolge advanced concurrently to dcfcd6fff0e40001ae686432d60a77434834e0b6 and is clean. No writes by this experiment there; pinned vendor/clones remain unchanged. Original BolgeForge and original M0 match initial state/hashes. No reset attempted.
