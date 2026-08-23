# Phase 149O.20L.7O.2U.2 Complete — Reference Adapter Implementation

Implemented the generic diff/JSON reference-adapter intake contract
frozen in Phase 149O.20L.7O.2U.1, re-derived from that canonical report
and from direct reads of current production source
(`execution-activation`/ECP/`promotion-review`/`promote` in
`src/pcae/cli.py` and `src/pcae/core/agent.py`, task-scope primitives in
`src/pcae/core/check.py`) — not from summary prose.

**Built**: `pcae intake create/show/list`
(`src/pcae/core/intake.py`, `src/pcae/commands/intake.py`, `cli.py`
wiring), a tamper-evident intake-record store, and the thin,
non-normative Claude Code reference adapter
(`scripts/claude_code_intake_adapter.py`).

**Contract concretizations this phase** (all consistent with 2U.1's
frozen constraints, documented in the phase doc §2): `content_after`
(full text) replaces 2U.1's ambiguous diff-or-content sketch, avoiding a
diff-application attack surface; `repo_binding` (repo_fingerprint +
base_commit ancestry) was added as the concrete mechanism for the
repo/base-commit binding requirement; `candidate_id` was added as a
required, content-independent identifier so ID-collision detection is
meaningful; task binding is scoped to the currently active task only
(more conservative than 2U.1's looser "active or recently-closed"
prose).

**Hard invariant enforced and tested**: `received != validated !=
authorized != permitted != promoted != executed`. Accepted candidates
become ordinary `ExecutionChangePackage` records via the *existing*
`store_execution_change_package()` — the unmodified
`promotion-review`/`promote`/`rollback` chain governs them identically
to a sandboxed-execution ECP. `execution_allowed`/`promotion_executed`
are hardcoded `False` on every artifact this module produces; no
producer-supplied field — including forged `promotion_authorized`,
`approved`, `executed`, or `execution_allowed` fields at any nesting
level — is ever read into an authority-bearing field. Verified directly
in `build_promotion_review()`'s source (its `promotion_authorized`
field is computed only from that command's own `--promotion-authorized`
CLI flag) and by a dedicated parametrized test.

**Adversarial test matrix (24 cases, all pass)**: valid allow; out-of-
scope deny; hash mismatch; invalid/missing base commit; base commit not
an ancestor of HEAD; repo-binding mismatch; malformed candidate; unknown
schema version; four forged-authority-field variants; four path-
traversal/absolute-path variants; ID-collision-conflicting-content;
ID-collision-idempotent-replay; stored-artifact-tamper-detected;
task-not-active; delete-with-content-hash; Claude adapter positive;
Claude adapter malformed-negative; Claude adapter cannot-bypass-checks.

**Regression verification**: 4370 existing downstream tests spanning
execution/ECP/promotion/rollback/task-scope/mutation-permission/
artifact-integrity — 4370 passed, 0 failed, zero regression to the
unmodified chain this phase reuses.

**Fast Green — attribution-aware, A/B-verified**: a controlled fast_green
subset initially showed 17 more failures with uncommitted changes
present than a stashed pre-phase baseline; all 17 were of the form "no
`src/pcae`/`scripts` files dirty in working tree" — diagnosed as
working-tree-dirtiness artifacts, not defects. After this phase's own
implementation commit (tree clean), the identical subset reproduces the
exact pre-existing baseline: 268 failed, 9 errors, sorted failure-ID
list byte-identical to the stashed baseline (confirmed via `diff`, exit
code 0) — zero attributable regressions.

**HMIC/trust-scope reassessment**: confirmed via grep that HMIC governs
HATP credential/identity certification specifically (every genuine
reference is scoped to `hatp_*.py`); `pcae.core.intake` carries no
HATP-relevant trust boundary, so no HMIC registration applies — an
explicit reassessment, not a silent omission.

No production code was modified outside the four new/modified files
listed above. No HATP/WebAuthn/FIDO2/DeepSeek/Codex work. No release
tag. No raw/force git push. No Permission Broker enforcement added.
Runtime posture unchanged (`Observed`/`observe`/`execution_unavailable`).
**This phase does not claim independent verification — that is 2U.3's
job.**

Full text:
`docs/PHASE_149O_20L_7O_2U_2_REFERENCE_ADAPTER_IMPLEMENTATION.md`.

Recommended next: 149O.20L.7O.2U.3 — Reference Adapter Independent
Verification.
