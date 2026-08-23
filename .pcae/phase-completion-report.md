# Phase 149O.20L.7O.2U.4 Complete — Deny/Allow Demo and Quick-Start Documentation

**Verdict: A — v0.3 ALLOW/DENY REFERENCE WORKFLOW DEMONSTRATED,
QUICKSTART REPRODUCIBLE, READY FOR 149O.20L.7O.2U.5.** No production
source modified. No frozen contract modified. No demo-only bypass added.

Built a disposable local demo repository (real `git init` + `pcae init`
+ a task scoped only to `src/app.py`) and exercised the real,
unmodified 2U.2/2U.3 intake and promotion code end-to-end — no mocks.

**ALLOW**: an in-scope proposal submitted through the real
`scripts/claude_code_intake_adapter.py` (real script; deterministic
fixture content, explicitly not presented as live Claude Code output)
was accepted, created an ECP, was reviewed via the existing unmodified
`pcae promotion-review create --promotion-authorized` boundary, and
`pcae promote` wrote the approved file into the demo repository's
working tree — verified by direct file read, not command output alone.

**DENY**: a structurally/hash/repo/base-valid proposal targeting an
out-of-scope path (`README.md`) through the identical adapter path was
rejected with `out_of_scope_path:README.md` — confirmed via a direct,
isolated `pcae intake create` exit-code check (**1**) — produced no
ECP, and left the target file unchanged.

**Quickstart**: wrote `docs/QUICKSTART_V0_3.md` (13-section structure)
and independently verified it via a second, empty-start clean-room
repository executing every documented command verbatim end-to-end —
reproduced identically.

**Acceptance harness**: added
`tests/test_phase_149o_20l_7o_2u_4_allow_deny_demo_acceptance.py`
(3 tests) against production `pcae.core.intake`/`pcae.core.agent` code
— not a duplicate of 2U.2's 24-case or 2U.3's 116-case suites.

**Regression**: 2U.2 (24/24) and 2U.3 (116/116) suites re-run clean.
Focused downstream regression (task-scope/ECP/promotion-review/
promotion/rollback): 846 passed, 21 failed/2 errored — all pre-existing
HATP/HMIC rollback-contract byte-identity tests, unrelated to intake;
this phase touched zero files those tests inspect. Full repository-wide
`fast_green`: an initial unfiltered run reported 337 failed / 8689
passed / 5 skipped / 9 errors, with every failing/erroring node ID
grepped for `intake|ecp|promot|reference_adapter|2u_2|2u_3|2u_4` — zero
matches. A deselected re-run excluding those 346 pre-existing IDs plus 2
deterministic push/working-tree-state tests (which fail only while this
phase's own commits are uncommitted/unpushed — `test_head_equals_origin_main`,
`test_working_tree_clean_for_pcae_directory`) reports **0 failed, 8687
passed, 5 skipped**.

**Findings documented, none repaired** (per phase directive): init
scaffolding shows as out-of-scope in `pcae health` immediately after
`pcae init` (Observation); proposal content requires a separate file
(Non-Blocking); long copy-pasted IDs between commands (Non-Blocking).
Carried forward, unrepaired: incomplete Windows-backslash path-admission
check; repo-fingerprint collision on byte-identical genesis commits —
both release-implication-assessed in the full report, not silently
dropped.

**v0.3 headline claims** checked against the demonstration and
attributed to their specific mechanism (task-scope gating → the DENY
result directly; completion-claim validation against real repo state →
intake's repo/base/hash binding *plus* `pcae promote`'s divergence
check, not intake alone; audit trail → the captured intake/ECP/EPR/PER
evidence chain).

No production code or frozen-contract file modified this phase. No
HATP/WebAuthn/FIDO2/DeepSeek/Codex work. No release tag. No raw/force
git push. No demo-only bypass. Runtime posture unchanged
(`Observed`/`observe`/`execution_unavailable`).

Full text:
`docs/PHASE_149O_20L_7O_2U_4_DENY_ALLOW_DEMO_AND_QUICK_START_DOCUMENTATION.md`.

Recommended next: **149O.20L.7O.2U.5 — v0.3 Release Candidate
Preparation** (already frozen by the 2U release plan).
