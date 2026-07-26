# Phase 145G.2V — Interactive Workflow Decision-Selection Contract and Implementation Independent Verification

**Status:** Complete (Independent Verification phase only; no production
code modified; no runtime-capability change).
**Verdict:** **NOT VERIFIED — BLOCKING FINDINGS.**
**Mode:** Independent, adversarial verification of Phase 145G.2's
contract revision (IWPC-001 v1.1 → v1.2) and implementation
(`decision-session select`, `preview`'s `AwaitingConfirmation` repair),
per this phase's own governing prompt. Phase 145G.2's own report, tests,
and conclusions were treated as evidence only, never as authority; every
finding below was independently re-derived from contract text, git
history, and direct source inspection first.
**Governing authority:** IWPC-001 v1.2, IWC-001 v1.2, PEC-001 v1.1,
CHGR-001, PROJECT_STATUS.md.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Repair authority exercised:** None. One Blocking finding was
independently confirmed (identity-binding enforcement, below); per this
phase's own Repair Authority section, it requires design judgment (how a
caller should even supply a competing identity claim, since no
`--identity`-shaped flag exists anywhere in the `decision-session`
command family today) and is therefore **not** repaired in this phase.
This phase adds only two new test files and this report; no file under
`src/` was touched.

---

## 0. Method Statement

Two independent research passes were run in parallel, each re-deriving
expected behavior from contract text and source before consulting Phase
145G.2's own report or running its tests:

- **Pass A** — IWPC-001 v1.1→v1.2 diff (via `git log`/`git show` against
  the real pre-145G.2 commit, not the prose changelog), F-145G.1-1
  reproduction, state-machine adversarial testing across all ten
  `SessionState` values, identity/authority verification, option-binding
  verification, replay/mutation verification.
- **Pass B** — persistence/corruption verification, application-layer
  (`SessionApplicationService`) verification, CLI-adapter verification
  (exit codes, traceback leakage, bypass flags), preview-transition
  before/after verification via git history, a genuine subprocess-separated
  CLI-only end-to-end reproduction, security/adversarial tests, AST-level
  dependency-boundary verification, and full regression.

Both passes wrote fresh adversarial tests exercising the real CLI and
application-service boundary — never internal monkeypatching, never
direct `Session` construction in a non-terminal state — and ran them
against the actual repository. All new tests were independently
re-executed by the orchestrating process after both passes reported
(51/51 passed). Findings below cite `file:line` evidence, not the
phase's own summary.

New test files, left in place under `tests/`:

- `tests/test_phase_145g2v_independent_verification_partial.py` (32
  tests — contract diff / state-machine / identity / option-binding /
  replay)
- `tests/test_phase_145g2v_independent_verification.py` (19 tests —
  persistence tamper / restart-safety / genuine subprocess e2e /
  security / CLI surface)

---

## 1. Independent IWPC-001 v1.1 → v1.2 Semantic Diff

Verified via `git show <pre-145G.2 commit>:docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
diffed against the current file (not the file's own prose "Revised by"
note, which was treated as a claim to verify, not evidence):

- `IWPC-REQ-014`'s command list (§5) amended **in place**: a `select`
  line inserted between `evidence` and `clarify`; every other line
  byte-identical.
- New §5.3 added, containing five new sequential requirements:
  `IWPC-REQ-192` (full `select` spec — preconditions, required/optional
  arguments, output, transition, idempotency, identity, option-binding,
  failure modes), `IWPC-REQ-193` (single-use replay rejection),
  `IWPC-REQ-194` (option-membership validation), `IWPC-REQ-195`
  (no-separate-identity-flag rule), `IWPC-REQ-196` (single-invocation
  two-hop design justification).
- Old §5.3–§5.8 renumbered §5.4–§5.9 — **subsection numbers only**;
  every `IWPC-REQ-###` identifier (017 through 025) is unchanged,
  unrenumbered, and unreused; confirmed no gap and no reuse across the
  full requirement set.
- `IWPC-REQ-018`'s "State transition" clause text changed in place (the
  `preview`→`AwaitingConfirmation` repair — see §6 below) plus
  `IWPC-REQ-064`'s cross-reference range updated `§5.1–§5.8`→`§5.1–§5.9`.
- Findings register gains one closed entry (F-145G.1-1) and one new,
  disclosed, deliberately-not-closed entry (F-145G.2-1, the
  `AwaitingDecision`→`AwaitingClarification` gap, out of scope by the
  phase's own governing prompt).
- No other section altered. This is a legitimate additive minor
  revision: no existing requirement was narrowed, removed, or given
  conflicting semantics; no state-table, error-mapping, identity rule,
  or replay rule elsewhere in the document was disturbed.

**Verdict on this part: sound.** The contract-diff mechanics of Phase
145G.2 are exactly as claimed.

## 2. Independent F-145G.1-1 Reproduction

Confirmed both halves independently, not from the phase's own narrative:

- **Pre-repair defect, reproduced from source history** (`git show` of
  the commit that completed Phase 145G.1): `session.py` provided no
  Decision-Capture mutator beyond bare state transition; the application
  service had no `select_decision` method; the CLI had no `select`
  handler. Grepping that historical revision confirms no production
  code path anywhere set `human_selection_id`/`human_rationale_text`/
  `human_conditions_text`/`options_presented` outside test fixtures —
  matching the original F-145G.1-1 disclosure.
- **Current repair is a real, reachable production path**, confirmed by
  direct citation: `src/pcae/interactive_workflow/models/session.py:136-189`
  (`with_decision_capture`), `src/pcae/interactive_workflow/application/session_service.py:525-650`
  (`select_decision`), `src/pcae/commands/decision_session.py:446-492`
  (`run_decision_session_select`), wired at `src/pcae/cli.py:10704-10721`.
  A genuine subprocess-separated, CLI-only run (§7 below) exercises this
  path end to end.
- The **second, previously undisclosed defect** Phase 145G.2 itself
  found and repaired — `generate_preview` never transitioning
  `DecisionSelected`→`AwaitingConfirmation` — is independently confirmed
  real: the pre-145G.2 `generate_preview` persisted an orchestration
  record but never invoked the transition engine or `persist_session`;
  the current version does, at `session_service.py:767-780`, on first
  successful construction only, and is idempotent on repeat calls.

**Verdict: F-145G.1-1 is genuinely closed**, and the preview-transition
repair is real and correctly scoped (§6 below has the adversarial
detail).

## 3. State-Machine Verification

Fresh, parametrized adversarial tests were run against the real CLI/
application boundary from every one of the ten `SessionState` values
(not just the two named in the contract): `select` succeeds only from
`EvidenceReady` and `AwaitingDecision`; fails closed with
`invalid_state_transition` from `Created`, `AwaitingClarification`,
`DecisionSelected`, `AwaitingConfirmation`, `Confirmed`, `Cancelled`,
`Expired`, `Abandoned` — 10/10 as contract-required. A second `select`
against an already-`DecisionSelected` session is rejected (no
last-write-wins path — see §6). `preview`'s new transition was
independently confirmed idempotent and correctly gated on
`DecisionSelected` as precondition.

**Verdict: sound**, no defect found.

## 4. Identity and Authority Verification — Blocking Finding

This is this phase's central, most consequential finding, and it is
**not** the finding Phase 145G.2's own report addressed.

IWC-001 v1.2 contains two explicit, frozen `SHALL`-level requirements
governing exactly this concern:

> **IWC-REQ-022.** A Decision Session in `Created` through
> `AwaitingConfirmation` MAY be resumed only by the identity bound at
> creation.

> **IWC-REQ-151.** A Decision Session implementation SHALL prevent
> resumption by an identity other than the one bound at creation.

IWPC-REQ-195 (new, Phase 145G.2) states: *"`select` accepts no identity
input distinct from the session's own bound `owner_identity`... the
selecting principal is never inferred from the OS user, Git config,
agent ID, lifecycle lock owner, an undeclared environment variable,
Telegram configuration, or the current shell user."* This phrasing
presents the session's bound `owner_identity` as an already-enforced
binding that `select` merely inherits.

**Independent grep of the entire `interactive_workflow` command surface
finds no enforcement of this anywhere** — not for `select`, and not for
any sibling command (`confirm`, `preview`, `clarify`, `cancel`):

- `owner_identity` is written exactly once, at session creation
  (`session_service.py:315-325`), and is never read back for comparison
  against a caller anywhere else in the codebase.
- No `--identity`/`--principal`/`--as`-shaped flag exists on `select`
  or any other `decision-session` subcommand — confirmed directly
  against the argparse registration at `src/pcae/cli.py:10704-10721`
  (spot-checked independently by the orchestrating process, not only
  the research pass): the only identity-shaped flag anywhere in the
  `decision-session` family is `--owner-id`, accepted once, at `create`,
  only.
- No `getpass`/`os.environ`/`getuser`/git-config read exists in
  `session_service.py`, `decision_session.py`, or `cli.py`'s
  decision-session handlers.
- Adversarially confirmed: a session created with `owner_id="alice"`
  accepts `select` (and every other mutating command) unchanged when
  the invoking process's environment simulates an entirely different
  operator (`USER=mallory`, `GIT_AUTHOR_NAME=mallory`) — there is
  nothing in the code path capable of noticing the difference, because
  there is no channel through which a competing identity claim could
  even be supplied, let alone rejected.

**This is a genuine contract/implementation disagreement**: IWC-REQ-022
and IWC-REQ-151 are explicit, mechanically simple obligations (a
structural-equality check against a claimed identity — the kind of
check IWPC-REQ-007's Authority Neutrality clause explicitly permits:
*"The CLI and transport layer MAY collect identity and authority claims
... and MAY validate their structural completeness"*), not an
authority-evaluation policy of the kind IWPC-REQ-003/IWPC-REQ-009
deliberately and correctly decline to invent. The gap is not that PCAE
lacks real authentication (that absence is already disclosed
elsewhere, e.g. IWPC-REQ-003's `eligible_authority` disclosure, and is
not this finding); the gap is that **no mechanism exists to even accept
a claimed identity for resumption at all**, so IWC-REQ-022/151's
narrower, already-scoped resumption-binding requirement is silently
unenforceable for every command in the family — `select` included.

This finding **predates Phase 145G.2** — the identical gap already
existed for `confirm`, `preview`, `clarify`, and `cancel` before this
phase. Phase 145G.2 did not introduce it, but it did extend the same
unenforced pattern to a new, irreversible, state-mutating command
(`select`) while its own IWPC-REQ-195 commentary characterizes the
absence of a separate identity flag as "mirroring `confirm`'s own
precedent" — describing the gap's shape without disclosing that the
underlying `IWC-REQ-022`/`IWC-REQ-151` requirements remain unenforced
by any command in the family, `select` newly included. Per this
verification phase's own governing rules, an authority/identity defect
of this kind may not be downgraded to Non-Blocking regardless of which
phase originally introduced it.

**Classification: Blocking.** Repair is explicitly out of this phase's
authority: closing it requires a design decision (what identity-claim
channel to add, and to how many commands) this phase's governing prompt
forbids inventing. Recommended as a separately authorized, narrowly
scoped future repair phase (see §12).

## 5. Option-Presentation Binding Verification

Fresh adversarial tests confirm:

- Selected-option-not-in-presented-set, duplicate presented IDs (at the
  CLI layer), and empty presented list all fail closed with
  `invalid_request`/`invalid_state_transition` as required.
- Option-membership (`IWPC-REQ-194`'s core rule) **is** domain-enforced:
  calling `SessionApplicationService.select_decision` directly,
  bypassing the CLI entirely, still rejects an out-of-set option
  (`InvalidSelectionError` at `session_service.py:600-604`).
- **Validation-ownership gap (Non-Blocking):** duplicate-ID rejection
  and non-empty `--template-version` are enforced **only** at the CLI
  argparse layer (`decision_session.py:453-465`). Calling
  `select_decision` directly with a duplicated `options_presented`
  tuple, or an empty `template_version`, succeeds and persists the bad
  value verbatim — confirmed by direct test. This is currently
  unreachable in production (v1.0 defines the CLI as the sole input
  channel, IWPC-REQ-036/006), so it is not presently exploitable, but
  it is a real defense-in-depth gap relative to IWPC-REQ-055's own
  stated principle that semantic validation must live in the wrapped
  subsystem rather than the adapter. Recorded as Non-Blocking,
  not deferred out of the record.
- Cross-session option substitution succeeds silently (no Decision
  Template resolver exists to detect it) — this matches IWPC-REQ-192's
  own disclosed judgment call and is not a new defect.

## 6. Replay and Mutation Verification

No last-write-wins path exists. The single-use state-precondition guard
(`session_service.py:585-593`) is checked before any mutation, so a
rejected replay never reaches `with_decision_capture` — confirmed the
original `human_selection_id`/`human_rationale_text` are byte-identical
after a rejected conflicting replay attempt. Replay is rejected
identically after `preview`, `confirm`, `readiness`, and `cancel`.
Persisted `options_presented` tampered directly on disk is not
re-validated at read time by `status`/`preview` — a latent gap, but not
contract-violating, since no requirement mandates read-time
re-validation of stored fields (see §7 for the related persistence
finding).

## 7. Persistence and Corruption Verification

- Atomic write confirmed: `tempfile.mkstemp` (same directory) → write →
  `flush` → `os.fsync` → `os.replace`, `finally`-block temp-file cleanup
  — `src/pcae/interactive_workflow/persistence/filesystem_repository.py:183-200`.
- Corruption handling confirmed: non-dict payload, wrong
  `schema_version`, mismatched wrapper/nested `session_id`, malformed
  nested payload, and invalid JSON/UTF-8 all raise
  `SessionStoreCorruptError` deterministically
  (`filesystem_repository.py:146-233`) — never best-effort recovery.
  Confirmed by direct test: five tamper scenarios, all rejected.
- Restart-safety confirmed: a fresh `FilesystemSessionRepository`
  instance (no shared object graph) reloading a selected session
  reproduces state/selection/options/template-version exactly.
- **Non-Blocking gap found:** `Session.__post_init__`
  (`src/pcae/interactive_workflow/models/session.py:102-131`) has no
  cross-field invariant check that `session_state == DecisionSelected`
  (or later) implies non-null `human_selection_id`. A session file
  hand-edited to that inconsistent shape loads and is served by
  `status` without complaint. No CLI-only production path was found
  that reaches this inconsistent state — it requires editing the
  persisted file directly, outside every governed boundary — so this
  is recorded Non-Blocking, not Deferred.

## 8. Application-Layer Verification

`select_decision`'s operation order is: load session → state
precondition → option-membership validation → transition(s) via
`TransitionEngine` → `with_decision_capture` → persist orchestration
record → persist session. Confirmed it never constructs readiness or
calls publication. **Layering-debt observation (Non-Blocking):**
`select_decision`/`generate_preview` construct `TransitionEngine()` and
manage transition-sequence bookkeeping directly inside the application
service rather than through a domain-owned sequencing object — a
pre-existing pattern matching `submit_clarification`'s identical style,
not introduced by 145G.2.

## 9. CLI Verification

Exit-code mapping (IWPC-REQ-050) verified against directly triggered
failures: `invalid_request`→1, `session_not_found`→1,
`invalid_state_transition`→2, `readiness_incomplete`→1 (correctly
bucketed as generic domain failure, not one of the named 2–5 classes).
No raw traceback or stack trace reaches stdout/stderr in `--json` mode
under any adversarial input tried (path-traversal-shaped session/package
IDs, missing required arguments, duplicate `--options-presented`) —
`run_with_error_mapping` catches uniformly. No `--force`/`--bypass`/
hidden flag exists anywhere in the `decision-session` or
`governance-record publish` argparse surface (confirmed by both a
programmatic scan and direct `grep` of `cli.py`).

## 10. Preview-Transition Verification

Independently confirmed via git history that the pre-145G.2
`generate_preview` truly performed no transition (matching the phase's
own disclosed defect narrative — not merely trusted). Current behavior:
transitions `DecisionSelected`→`AwaitingConfirmation` on first
successful construction only; idempotent (byte-identical digest) on
repeat calls; `confirm` against a session that never had a successful
`preview` fails closed (`invalid_state_transition`) — confirmation
without a valid preview is not reachable.

## 11. Genuine CLI-Only End-to-End Reproduction

A strictly stronger reproduction than Phase 145G.2's own end-to-end test
(which calls handler functions in-process): real `python -m pcae ...`
**subprocesses**, one fresh OS process per step, isolated `tmp_path`
working directory, no shared object graph, no direct construction, no
monkeypatching. Full chain executed and verified:

`create` → `evidence --declare ev-1 --declare ev-2` → `preview`
(correctly fails, exit 2, not yet selected) → `select` → `preview`
(succeeds, state → `AwaitingConfirmation`) → `preview` again (idempotent
digest) → `confirm --preview-digest <digest> --statement ...` (state →
`Confirmed`) → `readiness` (package constructed, disposition `pending`)
→ `governance-record publish <package-id> --operator-id ...` (success,
`record_id` starts `chgr-`).

**Verdict: genuinely CLI-only reachable end to end. No gap found.**

## 12. Security/Adversarial, Dependency-Boundary, and Regression Results

- Security/adversarial: path-traversal-shaped session/package IDs,
  nonexistent well-formed IDs, confirm-without-preview,
  readiness-without-confirmation, duplicate/out-of-set options — all
  rejected correctly, no leak. Path-like `option_id` values are
  accepted, correctly — `option_id` is opaque data, never resolved as a
  filesystem path (only `session_id`/`package_id` map to paths, and
  those are validated).
- Dependency boundary: clean. `decision_session.py` imports
  `SessionCoordinator`/`FilesystemSessionRepository`/
  `PublicationCoordinator`/`FilesystemPendingReadinessStore` only inside
  the single documented composition root
  (`build_application_context()`); every handler reaches them
  exclusively through the application-service boundary. No violation
  found by direct AST-level re-grep.
- Regression: `test_phase_145g2_decision_selection_cli_repair.py` (28),
  all `test_phase_145{d,e,f,g}*.py` (322), a broad
  `interactive_workflow`/`decision_session`/145-scoped selection (324),
  and `fast_green` (4391) — all passed, zero failures, no regressions
  independently reproduced.

---

## 13. Findings Register

| ID | Severity | Summary |
|---|---|---|
| F-145G.2V-1 | **Blocking** | No code path in the `decision-session` command family (`select` newly included) enforces IWC-REQ-022/IWC-REQ-151's identity-bound-resumption requirement; no channel exists to even supply a competing identity claim. Predates 145G.2; not disclosed against these two specific requirements by any prior phase's own report. |
| F-145G.2V-2 | Non-Blocking | Duplicate-option and empty-`template-version` rejection are CLI-argparse-only, not domain-re-validated; unreachable in production today (CLI is the sole v1.0 input channel) but a defense-in-depth gap. |
| F-145G.2V-3 | Non-Blocking | No cross-field invariant on deserialization ties `session_state` to `human_selection_id`'s presence; only reachable via direct file tampering outside every governed boundary. |
| F-145G.2V-4 | Non-Blocking | `select_decision`/`generate_preview` perform transition-sequencing bookkeeping inside the application service rather than a domain-owned sequencer (pre-existing pattern, not introduced here). |
| F-145G.1-1 | Closed | Confirmed genuinely closed — real production path from `EvidenceReady`/`AwaitingDecision` to `DecisionSelected` exists and is CLI-reachable end to end. |
| F-145G.2-1 | Deferred (unchanged) | `AwaitingDecision`→`AwaitingClarification` reachability gap, already disclosed by 145G.2 as out of its own scope; independently confirmed still open, correctly out of this verification phase's own repair authority. |

## 14. Explicit Verdict on F-145G.1-1 Closure

**F-145G.1-1 is confirmed closed.** The `select` command provides a
real, adversarially-tested, subprocess-reproducible production path out
of `AwaitingDecision`, and the sibling `preview`-transition repair makes
the full `create → select → preview → confirm → readiness → publish`
chain genuinely reachable through production CLI commands alone.

## 15. Overall Verdict

**NOT VERIFIED — BLOCKING FINDINGS.**

F-145G.1-1's own closure is independently confirmed sound, and every
mechanism Phase 145G.2 itself built (contract diff, state machine,
option-membership binding, replay protection, persistence, CLI
adapter, preview-transition repair, end-to-end reachability) passed
adversarial re-verification without a new defect of its own. This
phase's Blocking finding (F-145G.2V-1) is a pre-existing, systemic gap
this phase's own governing rules forbid downgrading regardless of
which prior phase introduced it, and regardless of it not being the
finding this phase was originally scoped to check. Per this phase's
own exit criteria, no Blocking finding may remain open for a `VERIFIED`
verdict; one does.

## 16. Recommendation (not authorized to begin)

A narrowly scoped future repair phase should design and add an
identity-claim channel (e.g., a `--as-identity`/`--principal` flag
accepted by every `decision-session` mutating command, structurally
compared against the session's bound `owner_identity`, per
IWPC-REQ-007's already-permitted "collect and validate structural
completeness" allowance — never an authority-evaluation policy) closing
F-145G.2V-1 for `select` and its siblings together, since they share one
root cause. This recommendation does not authorize that phase, 145G.3,
or 145H to begin.
