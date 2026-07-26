# Phase 145G.3 — Decision-Session Identity-Bound Resumption Contract and Implementation Repair

## Status

Complete. Runtime unchanged: Observed / observe / unavailable. No
execution capability added.

## Objective

Close Blocking finding **F-145G.2V-1**, disclosed by Phase 145G.2V's
independent verification: no command in the `decision-session` family
(`select`, `confirm`, `preview`, `clarify`, `cancel`, and — this phase's
own re-derivation additionally confirmed — `evidence`/`readiness`)
enforced IWC-REQ-022/IWC-REQ-151's requirement that a session in
`Created` through `AwaitingConfirmation` be resumed only by the identity
bound to it at creation.

## Authorization

Phase 145G.3 only. Not 145G.3V, not 145H, not any later phase.

## Independent Re-Derivation (before implementation)

Confirmed by direct source inspection, not by trusting Phase 145G.2V's
own report as proof:

1. **Commands that resume an existing session:** every mutating
   `decision-session` command — `evidence`, `select`, `clarify`,
   `preview`, `confirm`, `cancel`, `readiness` — loads a persisted
   `Session` via `SessionApplicationService.load_session` before acting.
   `create` establishes a binding rather than resuming one; `status` is
   read-only.
2. **Commands that validated identity before this phase:** none. Every
   one of the seven mutating methods in
   `src/pcae/interactive_workflow/application/session_service.py`
   followed the identical pattern `session = self.load_session(session_id)`
   → state-precondition check → domain logic, with no identity comparison
   anywhere in between.
3. **Layer of the defect:** application layer
   (`SessionApplicationService`) and, for `readiness` specifically, a
   second, distinct instance inside
   `PublicationApplicationService.ensure_readiness_package`'s own
   idempotent-by-key cache-hit branch (a second `readiness` call against
   an already-pending package never re-loaded or re-checked the session
   at all — an identity mismatch could otherwise present as an idempotent
   success). The CLI layer (`pcae.commands.decision_session`) had no
   identity-shaped input at all beyond `create`'s `--owner-id` and
   `governance-record publish`'s unrelated `--operator-id`. The domain
   layer (`Session`) already had the right persisted field
   (`owner_identity`) and needed no change.
4. **Intended ownership:** `SessionApplicationService`, immediately after
   `load_session`, before any state-precondition check or idempotent
   early-return — so every mutating method gets the check for free
   through one shared helper, and a mismatched identity can never slip
   through an idempotent code path.
5. **Existing identity infrastructure:** none reusable without crossing
   an architecture boundary. `pcae.cltr.authority.identity.PrincipalIdentifier`
   exists but sits outside `interactive_workflow`'s policy-authorized
   dependency edges (`.pcae/policy.toml`'s `[architecture.rules]`:
   `interactive_workflow = ["interactive_workflow", "governance"]`, no
   `cltr` edge). Reusing it would have required a policy amendment; this
   phase's own scope is narrow enough (`str == str` comparison against an
   already-persisted field) that no such amendment was needed or made.

## Contract Repair

`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
(IWPC-001) revised v1.2 → v1.3, additively, in §34: a new required
`--as-identity` argument on every mutating `decision-session` command's
IWPC-REQ (IWPC-REQ-016/017/018/020/023/025, and IWPC-REQ-192 for
`select`, superseding IWPC-REQ-195's now-corrected "no separate identity
input" text in place); a new closed-taxonomy `error_type`,
`identity_binding_mismatch`, and a new exit-code class, `6` (§9
IWPC-REQ-050/051, §19.1 IWPC-REQ-134); `create`/`status` explicitly
unaffected, with `status`'s own disclosed reasoning stated in place
(IWPC-REQ-022). No existing requirement narrowed, removed, or
renumbered. IWC-001 was not modified — IWC-REQ-022/IWC-REQ-151 already
fully specify the requirement this revision enforces; the gap was
entirely a missing CLI/application enforcement point in IWPC-001's own
implementation, not a semantic gap in IWC-001.

## Identity Model

Four distinct concepts, not merged:

- **Identity claim** — the caller-supplied `--as-identity` string. Never
  authenticated; structurally validated only (non-empty, ≤512 characters,
  no control characters — IWPC-REQ-007's "collect and validate structural
  completeness" allowance).
- **Identity binding** — `Session.owner_identity`, written exactly once
  at `create`, never mutated by any later transition (`with_state`/
  `with_decision_capture` both already copied it unchanged; this phase
  changed neither method).
- **Identity verification** — exact-string equality between the claim and
  the binding, performed exactly once, by
  `SessionApplicationService._require_bound_identity`. No case-folding,
  no whitespace normalization, no prefix/partial matching — a near-miss
  claim is a mismatch, never silently coerced into a match.
- **Identity authorization** — out of scope, unchanged. This phase
  performs no authority-evaluation policy (IWPC-REQ-003/009 remain
  untouched); it is a structural-equality gate, not an authorization
  decision.

`confirmation identity` (the `--statement` confirmer), `publication
operator`/`publication authorizer` (`governance-record publish`'s
`--operator-id`), and `runtime agent identity` (`claude-local`, the
`.pcae/agent-locks` lock owner) are pre-existing, unrelated identity
surfaces this phase does not touch, widen, or conflate with the session
owner binding.

## Identity Claim Channel

Exactly one: `--as-identity`, an explicit CLI argument. Never inferred
from OS username, git config, shell user, agent id, lifecycle lock,
Telegram, environment variables, or hostname — confirmed by this phase's
own adversarial tests (simulated `USER=mallory`/`GIT_AUTHOR_NAME=mallory`
environment has no effect on the outcome; only the explicit claim does).

## Identity Enforcement Scope

Re-derived, not assumed:

- **Enforced:** `evidence`, `select`, `clarify`, `preview`, `confirm`,
  `cancel`, `readiness` — every one of these continues a session's
  workflow (or, for `readiness`, gates progress toward publication).
- **Not enforced:** `status` — read-only observation of already-persisted,
  non-secret state; IWC-REQ-022/151 govern *resumption*, not observation,
  and IWC-001's own W5 security scenario ("a different identity resumes
  someone else's in-progress session") concerns an actor *acting* on a
  session. `create` is not enforced either — it establishes the binding,
  it does not resume one.

## Validation Ownership

Exactly one owner: `SessionApplicationService._require_bound_identity`
(and its public wrapper, `require_bound_identity`, reused by
`PublicationApplicationService.ensure_readiness_package` so `readiness`'s
own idempotent-by-key cache-hit path does not silently skip the check).
The CLI (`pcae.commands.decision_session`) validates structural
completeness only (`_require_identity_claim`) and never compares against
`owner_identity`; the domain layer (`Session`) is not involved (it holds
the already-persisted field, nothing more); persistence is unmodified.

## Failure Semantics

| Case | Layer | `error_type` | Exit code |
|---|---|---|---|
| Missing `--as-identity` | CLI (structural) | `invalid_request` | 1 |
| Malformed claim (empty after strip, >512 chars, control characters) | CLI (structural) | `invalid_request` | 1 |
| Well-formed claim, does not equal `owner_identity` | Application (`SessionIdentityMismatchApplicationError`) | `identity_binding_mismatch` | 6 |
| Session not found | Application (checked first, inside `load_session`) | `session_not_found` | 1 |
| Corrupted/missing persisted `owner_identity` | Application (pre-existing `Session.__post_init__`/`SessionStoreCorruptError` path, unchanged) | `persistence_corrupt` | 1 |

Session-not-found is always checked before identity, since
`require_bound_identity` calls `load_session` first — a nonexistent
session never leaks whether a claim would have matched. Fail-closed
throughout: no case defaults to acceptance.

## Persistence

Unchanged. `owner_identity` was already persisted (`serialization/
schema.py`); no new field was added, since the claim is compared, never
stored a second time. An older session missing `owner_identity` already
fails to load via `Session.__post_init__`'s existing non-emptiness check
— this phase added no new persistence-layer behavior to preserve.

## CLI

`_require_identity_claim` (transport-only, structural). Threads
`args.as_identity` through to the corresponding
`SessionApplicationService`/`PublicationApplicationService` call. Never
compares identities, never inspects persistence, never bypasses the
application layer.

## Read-Only Commands

`status` explicitly determined not to require enforcement (see
"Identity Enforcement Scope" above); documented in-code and in the
contract (IWPC-REQ-022).

## Replay

Verified: identical caller (succeeds, repeatably where the underlying
operation is itself idempotent); different caller (rejected, every
command); missing caller (rejected — argparse `required=True`); malformed
caller (rejected, `invalid_request`); `cancel` against an already-
`Cancelled` session with a mismatched claim (rejected, not an idempotent
success); `readiness` against an already-pending package with a
mismatched claim (rejected, not a transparent cache-hit). No case turns
an identity mismatch into an idempotent success.

## End-to-End

`tests/test_phase_145g3_decision_session_identity_binding.py::
test_owner_reaches_publication_impostor_is_rejected_at_every_step`: a
genuine, real-handler-invocation `create → evidence → select → preview →
confirm → readiness` chain for the true owner (`alice`) succeeds at every
step; the identical sequence attempted with a mismatched claim
(`mallory`) is rejected, deterministically, at every single step, and
never mutates the session (confirmed separately by
`test_confirm_rejects_mismatched_identity`, which asserts the session
remains `AwaitingConfirmation`, not `Confirmed`, after the impostor's
rejected attempt).

## Security Tests

`tests/test_phase_145g3_decision_session_identity_binding.py` (25 tests):
missing claim, malformed claim (control characters, oversized), mismatched
claim, exact-match success, case sensitivity (rejects `"Alice"` against
`owner_identity="alice"`), whitespace non-normalization (rejects `" alice "`),
unicode identity (`"étienne"`, accepted and compared exactly), replay
against `cancel`'s and `readiness`'s idempotent paths, session-not-found
precedence over identity mismatch, `status`/`create` unaffected, and a
direct `SessionApplicationService` call bypassing the CLI entirely
(`SessionIdentityMismatchApplicationError` raised independent of any CLI
structural check).

Three pre-existing files updated in place because they encoded the
now-closed vulnerability as expected/passing behavior (Phase 145G.2V's
own adversarial reproduction tests):
`tests/test_phase_145g2v_independent_verification_partial.py`'s
`test_select_command_has_no_identity_flag_in_parser` →
`test_select_command_has_identity_flag_in_parser` (now asserts exactly
one identity flag exists); `test_select_succeeds_regardless_of_os_environment_identity`
→ `test_select_rejects_mismatched_identity_regardless_of_os_environment`
(now asserts rejection, with OS environment confirmed still irrelevant);
`test_confirm_and_cancel_also_accept_no_identity_input` →
`test_confirm_and_cancel_also_reject_mismatched_identity`. Each retains
its original docstring's finding-history context, updated to state what
it now verifies instead.

## Dependency Boundaries

CLI → Application → Domain → Persistence, unchanged direction. No new
shortcut, no new reverse dependency, no `interactive_workflow` → `cltr`
edge added (the existing `.pcae/policy.toml` boundary and its AST-based
forbidden-import tests, `tests/test_phase_145g_decision_session_cli.py`
and siblings, pass unmodified).

## Documentation

Updated: this report; `docs/contracts/
INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md` (§34,
v1.2 → v1.3); `docs/COMMANDS.md` and its generator template
(`src/pcae/core/docs.py`, kept byte-identical via `pcae docs commands
--force`); `PROJECT_STATUS.md`; `tasks/TODO.md` (Known Issues entry for
F-145G.2V-1 closed); `CHANGELOG.md`.

## Regression

- New: `tests/test_phase_145g3_decision_session_identity_binding.py` — 25/25 passed.
- `tests/test_phase_145g2v_independent_verification.py` — 19/19 passed (updated in place: real-subprocess CLI calls to mutating commands now supply `--as-identity`).
- `tests/test_phase_145g2v_independent_verification_partial.py` — 32/32 passed (three tests rewritten per "Security Tests" above; direct `select_decision` calls updated to pass `caller_identity`).
- `tests/test_phase_145g2_decision_selection_cli_repair.py` — 28/28 passed.
- `tests/test_phase_145g1_decision_session_cli_repair.py` — 44/44 passed.
- `tests/test_phase_145g_decision_session_cli.py` — 37/37 passed (taxonomy/exit-code-range assertions extended to include `identity_binding_mismatch`/6).
- Broader `interactive_workflow`/`decision_session`/`145g`/`publication`/`governance_record`-scoped selection (`pytest -k "interactive_workflow or decision_session or publication or 145g or governance_record"`): 939 passed, 1 skipped, 4 failed; the 4 failures are the same pre-existing wheel/sdist packaging failures already disclosed by prior phases (`test_136ah_wheel_contains_publication_module_no_later_family`, `test_136ah_sdist_includes_publication_module`, and their 136ai counterparts), independently reproduced as failing identically against unmodified `main` before this phase's changes — not caused or affected by this repair.
- `fast_green` (4391 tests): 4391/4391 passed, unaffected.

## Governance Validation

`pcae runtime inspect`: Observed / observe / unavailable, unchanged.
Repository clean before and after (only this phase's own tracked changes
present). No execution capability added; no background worker added; no
remote transport added; no publication-ownership or CHGR-ownership
change; no workflow redesign.

## Exit Criteria

All met: F-145G.2V-1 independently reproduced (re-confirmed absent before
repair) and now independently reproduced closed (present after repair,
adversarially tested); contract repaired (IWPC-001 v1.2 → v1.3, §34);
identity claim channel explicitly defined (`--as-identity`, sole
channel); identity ownership explicitly defined
(`SessionApplicationService`, sole comparison owner); every required
resumed command enforces identity; validation exists exactly once per
call; CLI remains transport-only; persistence unchanged; genuine
CLI-only owner flow succeeds; the same flow with incorrect identity
fails deterministically at every step; replay respects identity,
including both idempotent-early-return paths; dependency boundaries
intact; regression suite passes; runtime remains Observed / observe /
unavailable; no execution capability added; F-145G.2V-1 explicitly
closed; no Blocking findings remain from this phase's own scope.

## Recommended Next Phase (not authorized)

**145G.3V — Decision-Session Identity-Bound Resumption Independent
Verification.** This report does not authorize 145G.3V, 145H, or any
later phase.
