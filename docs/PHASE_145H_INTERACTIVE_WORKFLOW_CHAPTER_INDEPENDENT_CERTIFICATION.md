# Phase 145H — Interactive Workflow Chapter Independent Certification

**Status:** Complete (chapter-level certification phase; no production
code modified; no runtime-capability change; repair authority not
exercised).
**Verdict:** **NOT CERTIFIED — BLOCKING FINDINGS.**
**Mode:** Independent, chapter-level certification of the Interactive
Workflow + Publication CLI/Transport chapter (Phases 143A–145G.3V), per
this phase's own governing prompt. Prior phase reports (143A–145G.3V)
were used only as leads; every conclusion below was independently
re-derived from the frozen contract texts, current production source,
live adversarial CLI execution against a disposable scratch repository,
and the existing test suite.
**Governing authority:** IWC-001 v1.2, IWPC-001 v1.3, PEC-001 v1.1,
CHGR-001 v1.0, PROJECT_STATUS.md.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect --json`).
**Repair authority exercised:** None. One Blocking finding (H-1) was
independently confirmed. Per this phase's own repair-authority rules,
repair is permitted only when the existing contracts *unambiguously*
dictate the fix; H-1's correct remedy (return the existing consumed
package, vs. raise a new "already published" domain error, vs. some
other resolution) is a design choice the contracts do not spell out, so
no repair was invented. This phase adds only this report and routine
lifecycle/metadata bookkeeping; no file under `src/`, `tests/`, or
`docs/contracts/` was touched.

---

## 0. Method Statement

Before inspecting any implementation, independent expectations were
derived directly from IWC-001 v1.2, IWPC-001 v1.3, PEC-001 v1.1, and
CHGR-001 v1.0 (full text reads, not summaries), producing: a complete
identity/authority taxonomy, a command-by-command transition and
idempotency table, and the publication-boundary rules those four
contracts jointly impose. A chronological findings register was then
built from every phase report 143A–145G.3V (findings, severities, repair
phases, verification phases, exact verdict strings — including the
145G.3R lock-release-ordering lifecycle defect). Current production
source was mapped independently of contract prose: CLI parser
registrations and exit-code maps, `SessionApplicationService`/
`PublicationApplicationService` method-by-method identity-check
ordering, the `SessionState` transition table as actually coded,
persistence atomicity/corruption/symlink handling in all three
filesystem stores, the `PublicationCoordinator` boundary, the
composition root, and both existing AST-based forbidden-import tests.
Only after all of the above was independently written down did the
prior phases' own verdicts get compared against it.

Fresh adversarial testing was then run as genuine subprocess CLI
invocations against an isolated, disposable `pcae init` scratch
repository (never against test fixtures, monkeypatches, or direct model
construction): the full happy path across `create → evidence → select →
preview → confirm → readiness → publish` with a subprocess boundary
between every step; wrong/missing/whitespace/case-variant identity
claims on multiple commands; path-traversal and symlink attacks against
session storage; truncated JSON and unsupported schema-version
persistence corruption; cross-session Preview-digest substitution; and,
critically, **repeating `readiness` after a session's package had
already been published** — the scenario that produced this phase's one
Blocking finding.

Existing tests were run only after these independent expectations were
already on paper: the full chapter-scoped subset (1195 tests), the
repository's `fast_green` gate (4391 tests), and the full governed suite.

---

## 1. Chapter Scope and Boundary Certification

**What the chapter owns:** the Interactive Decision Session domain and
its ten-state machine (`src/pcae/interactive_workflow/state_machine/**`,
`models/session.py`); evidence, clarification, preview, and confirmation
coordination (`orchestration/coordinator.py`, `session/coordinator.py`);
the `SessionApplicationService`/`PublicationApplicationService`
transport-facing boundary (`interactive_workflow/application/**`); three
concrete filesystem stores (`FilesystemSessionRepository`,
`FilesystemPendingReadinessStore`, `FilesystemOrchestrationStore`); the
`pcae decision-session *` and `pcae governance-record publish` CLI
surface (`src/pcae/commands/decision_session.py`,
`src/pcae/commands/governance_record.py`); and `PublicationReadinessPackage`
construction via `PublicationHandoff.build_package`.

**What it delegates:** Publication Execution itself — atomic CHGR write,
canonical-identity assignment, provenance capture, and all
authorization/replay logic — is owned exclusively by
`PublicationCoordinator` (`src/pcae/governance/publication/coordinator.py`),
confirmed structurally outside `src/pcae/interactive_workflow/**` and
confirmed, by direct source inspection, to import no interactive-workflow
internals beyond the stateless `PublicationHandoff`/
`PublicationReadinessPackage` types it consumes.

**What it consumes:** CHGR-001's artifact-class definitions and eight-
state model (referenced, never reimplemented); PCAE's own phase/task
lifecycle machinery (unrelated, untouched).

**What remains outside its authority:** authority *evaluation* (as
opposed to authority *capture*) — no component anywhere in the
repository evaluates whether an `--owner-id`/`--operator-id` claimant is
substantively entitled to act; this is a contract-disclosed, explicitly
out-of-scope gap (IWPC-001 §31, "C-1"), independently confirmed still
true today (no `PrincipalIdentifier`/authority-resolver import anywhere
in `interactive_workflow/**`).

**Intentionally not implemented:** a command that opens
`AwaitingClarification` from `AwaitingDecision` (disclosed, Non-Blocking,
F-145G.2-1); a cryptographic/signing layer over persisted
`owner_identity` or package digests (disclosed, Non-Blocking); a
mutual-exclusion mechanism for concurrent single-session writes beyond
`os.replace`'s last-write-wins (disclosed, Non-Blocking, F-145A-5).

**Ownership boundary certification:** exactly one owner was independently
confirmed for each responsibility area named in the phase prompt (CLI
transport / application services / domain / state machine / persistence
/ orchestration / evidence / clarification / preview / confirmation /
readiness / publication handoff / publication execution / CHGR authority
/ lifecycle authority / runtime authority). No duplicate or ambiguous
owner was found. One genuine layering gap was found and is recorded as
Non-Blocking in §11, not Part I: the existing AST-based forbidden-import
tests do not cover every internal `interactive_workflow` subpackage
symmetrically (see §11).

---

## 2. Contract Coherence Certification

An independent cross-contract matrix was built covering terminology,
state names, identity definitions, command inventories, error types,
replay semantics, persistence obligations, and publication boundaries
across IWC-001 v1.2, IWPC-001 v1.3, PEC-001 v1.1, and CHGR-001 v1.0.

**Findings:**

- **State-name consistency:** IWC-001's ten PascalCase state names are
  reproduced verbatim by IWPC-001 §12 (repaired from an earlier lowercase
  mismatch by Phase 145C's Finding B-1) and by the actual `SessionState`
  enum in code (`CREATED`, `EVIDENCE_READY`, ... — Python-idiomatic
  upper-snake internally, serialized as the contract's own PascalCase
  strings). No drift found.
- **Identity taxonomy:** Caller / decision maker / confirmer / selecting
  principal / authorizing principal / CHGR authority / runtime agent /
  lifecycle lock owner are each named exactly once, in exactly one
  contract, with no conflation across IWC-001/IWPC-001/PEC-001/CHGR-001.
  Confirmed in code: `SessionApplicationService` enforces only the
  decision-maker/confirmer/selecting-principal identity (`owner_identity`
  exact-match); `PublicationApplicationService.hand_off` governs only the
  authorizing principal (`operator_id`), entirely separately, verified
  entirely inside `PublicationCoordinator`. No code path conflates the
  two.
- **Command inventory completeness:** every command IWPC-001 v1.3 §5
  names exists in `cli.py`'s parser registration and in
  `decision_session.py`'s handler set, argument-for-argument (confirmed
  by direct comparison, not by trusting `docs/COMMANDS.md`).
- **Version currency:** IWC-001 v1.2, IWPC-001 v1.3, PEC-001 v1.1 are the
  latest frozen versions and are the versions actually implemented;
  cross-references between them (e.g. IWPC-001's citations of IWC-REQ-185
  through 190, PEC-001's citations of the same) resolve correctly to text
  that exists in the cited contract at the cited section.
- **Additive-only revision history confirmed:** every revision made
  during 145C/145G.2/145G.3 (state-literal casing repair, `select`
  command addition, `--as-identity` addition) was independently checked
  against its own contract's diff — each is additive or a same-version
  in-place text repair; none narrows or removes a previously-frozen
  requirement. No incompatible silent change was found.
- **One coherence gap, Non-Blocking:** IWPC-001's own uniqueness language
  for readiness packages ("one **pending** package per session," IWPC-
  REQ-082/107) is textually scoped to the *pending* state throughout,
  while IWPC-REQ-024's own idempotency clause ("subsequent invocations
  SHALL report the already-persisted package unchanged") carries no such
  qualifier and no explicit carve-out for a package that has since been
  consumed. Neither IWPC-001 nor PEC-001 nor CHGR-001 anywhere states
  what SHOULD happen when `readiness` is invoked again after the
  session's package has already been published. This drafting gap is the
  contract-side root contributor to Finding H-1 (§6) — see there for the
  full analysis of whether the current implementation's resolution of
  this gap is acceptable.

---

## 3. Complete State-Machine Certification

The ten-state model and its transition table were independently
reconstructed from `state_machine/transitions.py`'s `TRANSITION_TABLE`
and cross-checked against IWC-001 §4.4 and IWPC-001 §12/§5. Enforced
edges, exactly as coded:

| Source | Permitted targets |
|---|---|
| `Created` | `EvidenceReady`, `Cancelled`, `Expired`, `Abandoned` |
| `EvidenceReady` | `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `AwaitingDecision` | `AwaitingClarification`, `DecisionSelected`, `Expired`, `Cancelled`, `Abandoned` |
| `AwaitingClarification` | `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `DecisionSelected` | `AwaitingConfirmation`, `AwaitingDecision`, `Cancelled`, `Expired`, `Abandoned` |
| `AwaitingConfirmation` | `Confirmed`, `DecisionSelected`, `Cancelled`, `Expired`, `Abandoned` |
| `Confirmed` / `Cancelled` / `Expired` / `Abandoned` | *(none — terminal)* |

This matches IWC-001 §4.4 exactly (post-143I.1's repair, which this
chapter's own phases correctly never re-narrowed). `TransitionValidator`
enforces, in fixed order: unknown-state rejection, no-op/duplicate
rejection, terminal-state-exit rejection, then registry membership —
independently confirmed fail-closed by direct code read and live testing
(a session driven to `Cancelled` correctly refuses every further mutating
command, live-tested in the scratch repository).

**Reachability:** every forward transition has a real, CLI-invocable
production driver (`submit_evidence`, `select_decision`,
`submit_clarification`, `generate_preview`, `record_confirmation`,
`cancel_session`) — independently confirmed by driving the full path
`Created → EvidenceReady → AwaitingDecision → DecisionSelected →
AwaitingConfirmation → Confirmed` via real subprocess CLI calls with a
process boundary at every step (§7). Two backward edges the table
permits (`AwaitingConfirmation → DecisionSelected`,
`DecisionSelected → AwaitingDecision`) have no production driver at all —
they exist in the table (required, since the table is IWC-001's frozen
invariant surface) but are simply never taken by any command; this is
not a defect, since nothing in IWC-001 requires every table edge to have
a *dedicated* command, only that no unlisted transition be accepted.

**One confirmed, pre-existing, Non-Blocking reachability gap (F-145G.2-1,
independently reconfirmed):** no command drives `AwaitingDecision →
AwaitingClarification`; `clarify` only answers a clarification already
open. This was independently reproduced: no CLI sequence starting from a
freshly created session can reach `AwaitingClarification` today. This
does not affect the terminal-state or fail-closed guarantees above, and
was already disclosed by 145G.2 and reconfirmed by 145G.2V; it remains
open and unrepaired, correctly outside this phase's own repair authority
(no design judgment was exercised to leave it open — it is simply outside
this phase's scope to fix).

No unreachable required transition, no accepted invalid transition, and
no direct state-mutation bypass (every mutation goes through
`TransitionEngine.apply`, itself reached only via
`SessionApplicationService`) was found.

---

## 4. CLI Surface Completeness Certification

All nine `decision-session` subcommands and `governance-record publish`
were independently inventoried against `cli.py`'s parser registrations
and IWPC-001 §5. For every command: parser registration exists; help
text is present; required/optional arguments match the contract exactly;
`--as-identity` is present on every mutating subcommand and absent from
`create` (establishes binding) and `status` (read-only) as the contract
requires; `--json` toggles machine output uniformly; exit codes are
deterministic (`EXIT_SUCCESS=0` through `EXIT_IDENTITY_BINDING_MISMATCH=6`,
confirmed as a fixed table in `_EXIT_CODE_BY_ERROR_TYPE`); errors never
leak a raw Python traceback or filesystem path (confirmed — every
handler is wrapped in `run_with_error_mapping`, and live adversarial runs
against corrupted/symlinked/truncated files above all produced clean,
structured JSON error payloads, never a stack trace); no `--force`,
`--assume-authorized`, or other bypass flag exists anywhere in the parser
definitions (confirmed by direct grep of the argument list, matching
IWPC-REQ-027/PEC-REQ-092's explicit prohibition).

One cosmetic completeness gap, independently reconfirmed unchanged from
145G.3V's own N-145G.3V-2: `EXIT_IDENTITY_BINDING_MISMATCH` is defined
and used internally but omitted from `decision_session.py`'s `__all__`
list. No functional effect. Non-Blocking.

The CLI is confirmed to be a pure transport adapter, not a policy owner:
every mutating handler's body does argument-shape validation only, then
delegates entirely to `SessionApplicationService`/
`PublicationApplicationService`; no handler constructs or calls
`SessionCoordinator`/`PublicationCoordinator` directly (the only
construction site for either is the single composition root,
`build_application_context()`).

---

## 5. Identity, Authority, and Provenance Certification

The identity taxonomy from §2 was independently traced through
`SessionApplicationService`. Every state-mutating method
(`submit_evidence`, `select_decision`, `submit_clarification`,
`generate_preview`, `record_confirmation`, `cancel_session`,
`construct_readiness_package`) and `PublicationApplicationService.
ensure_readiness_package` was read line-by-line: each calls
`load_session` then `_require_bound_identity` (exact-string comparison,
no normalization) **before** any state-precondition check and **before**
any idempotent-or-cache-hit early return, including
`cancel_session`'s idempotent already-`Cancelled` return and
`ensure_readiness_package`'s already-constructed-package cache hit. This
ordering was independently re-verified — not merely re-read — by live
adversarial CLI execution:

- Wrong identity on a mutating command → `identity_binding_mismatch`,
  exit 6 (confirmed for `evidence`; the identical code path governs every
  other mutating command).
- Identity with trailing whitespace, and an all-uppercase variant of the
  correct identity → both rejected (`identity_binding_mismatch`); no
  normalization of any kind is applied, confirming exact-string equality
  as claimed.
- Missing `--as-identity` on a mutating command → argparse-level
  rejection (exit 2) before the application layer is ever reached.
- Cross-session Preview-digest substitution (confirming session B using
  session A's real, validly-generated digest) → correctly rejected as
  `confirmation_conflict`, exit 3 — the digest binding is genuinely
  per-session, not just per-format.

No component treats a runtime agent identity, a lifecycle lock owner, or
mere possession of a session identifier as authority. Confirmation is
independently confirmed to never authorize publication (`confirm`'s
success payload carries no publication-readiness field); the CLI adds no
second confirmation step at `publish`, matching IWPC-REQ-029/106's
explicit prohibition on merging these acts.

**Verdict for this Part: no Blocking finding.** The identity/authority/
provenance boundary is intact and independently confirmed fail-closed
under adversarial conditions, closing the loop on F-145G.2V-1's repair
and directly reproducing 145G.3V's own verdict from first principles
rather than trusting it.

---

## 6. Idempotency, Replay, and Mutation Certification — Blocking Finding H-1

### 6.1 Independent contractual re-derivation of the uniqueness boundary

Before examining code, the uniqueness boundary for readiness packages and
CHGR records was re-derived directly from contract text:

- **IWC-001** defines Confirmation as "a single, non-repeatable act, not
  an idempotent one" (restated at IWPC-REQ-104) — i.e., exactly one
  Human Governance Act occurs per session.
- **CHGR-001 §2** defines a CHGR, definitionally, as "the durable,
  canonically identified, structured representation of **one** Human
  Governance Act" — singular, not "a" representation among possibly
  several.
- **IWPC-REQ-024** states readiness construction is "idempotent by key,
  keyed on `session_id`: a second construction attempt for a session that
  already has a persisted pending package SHALL return the existing
  package, never rebuild it" — an unqualified guarantee, with no stated
  exception once the package is later consumed.
- **PEC-REQ-080 / IWPC-REQ-113** guarantee that naming an already-
  consumed **`package_id`** at `publish` never produces a second CHGR —
  but this guard is explicitly scoped to `package_id`, the wrong key for
  this question, and the contracts do not separately state a session-
  level or decision-level uniqueness guard at the `publish` layer.

None of the four contracts explicitly enumerates "what happens when
`readiness` is invoked again against a session whose package has already
been consumed." IWPC-REQ-082/107's own phrase — "one **pending** package
per session" — is textually scoped to the pending state, which is
consistent with either (a) a deliberate scope-limiter meaning no
uniqueness guarantee is owed once consumed, or (b) simply a description
of the store's directory layout with no bearing on whether a *second*
readiness package should ever be constructable for an already-published
session. Reading the contracts as a whole — one Human Governance Act
per Confirmation, one canonical representation of that act per CHGR-001
§2, an unqualified idempotency guarantee at IWPC-REQ-024, and no
provision anywhere that contemplates or permits a second, independently
publishable package for a session whose first package has already been
published — the weight of contractual evidence is that **multiple
readiness packages (and therefore multiple CHGR records) for a single
confirmed decision are never contractually intended, at any point in the
package's lifecycle, including after publication.** No contract text
affirmatively permits it.

### 6.2 Independent live reproduction

Reproduced via real CLI subprocess invocations against a disposable
scratch repository (not test fixtures, not direct model construction):

1. `create` → `evidence` → `select` → `preview` → `confirm` on a fresh
   session (`CDS-1bf367d3-...`, owner `alice`) reaches `Confirmed`
   correctly.
2. `readiness --as-identity alice` (first call) constructs and persists
   package `prp-79ff3df8...`, disposition `pending`.
3. `governance-record publish prp-79ff3df8... --operator-id bob`
   succeeds, producing CHGR `chgr-63f5c504...`. `prp-79ff3df8...` is
   correctly moved to `pending-packages/consumed/`.
4. `readiness --as-identity alice` (second call, same session, fresh
   process, after publication) does **not** return the existing package.
   It constructs and persists a **new** package, `prp-aff88830...`,
   disposition `pending` — a different `package_id` for the same,
   still-`Confirmed`, already-published session.
5. `governance-record publish prp-aff88830... --operator-id bob`
   **succeeds**, producing a **second** CHGR record,
   `chgr-a49f7883...`, for the identical underlying decision.
6. Filesystem inspection confirmed both CHGR records exist independently
   in `.pcae/publication-execution/records/`, each with its own
   `attempt_id`, and both source packages are independently present
   under `pending-packages/consumed/`.

### 6.3 Root cause

`FilesystemPendingReadinessStore.find_by_session_id`
(`persistence/filesystem_pending_readiness_store.py:505-518`) is
documented, in its own docstring, to "Never return a `consumed/` record
— once consumed, a package is no longer 'pending' for construction-
idempotency purposes." `PublicationApplicationService.
persist_readiness_package`'s idempotent-by-key check
(`publication_service.py:122-124`) and `ensure_readiness_package`
(`publication_service.py:181-183`) both call only this method. Once the
first package moves to `consumed/`, the lookup returns `None`, and
`ensure_readiness_package` proceeds to construct and persist a brand-new
package (`publication_service.py:184-185`) for a session that is,
correctly, still in its terminal `Confirmed` state (nothing prevents
readiness construction from a `Confirmed` session regardless of how many
times it has already produced a package). The newly-minted package
carries a fresh `package_id`, so PEC-001's own replay guard — which is
correctly, narrowly scoped to `package_id` — has no textual or
architectural basis to reject it; it is not a replay of anything from
PEC-001's point of view, because PEC-001 was never asked to reason about
session-level uniqueness.

### 6.4 Historical trace — why this went undetected through five independent-verification passes

Phase 145G's own report first disclosed a *related* symptom: "`status`/
`readiness` report `'none'` (not `'consumed'`) once a package has been
published — the store's own existing, unmodified behavior." At the time
145G wrote this, `readiness`'s *construction* path did not yet exist —
145G implemented only the read/inspect path, and construction required
objects (`OrchestrationState`, a live `Preview`, an accepted
`ConfirmationResponse`) the CLI had no way to obtain until Phase 145G.1.
145G's disclosure was therefore accurate at the time: the consequence of
`find_by_session_id` never seeing a consumed record was, at that point,
purely cosmetic — a stale status string, no side effect.

Phase 145G.1 then implemented `readiness`'s real construction path
(`ensure_readiness_package`), wiring the *same*, textually-unmodified
`find_by_session_id` lookup into an idempotency gate that now had real
construction power behind its negative branch. 145G.1's own report
carries the 145G disclosure forward **verbatim** ("Non-Blocking
(inherited from 145G, unchanged by this phase): `status`/`readiness`
report `'none'` rather than `'consumed'` ...") without re-examining that
wiring construction into the same lookup had silently upgraded the
consequence from "stale read-only status string" to "mints and persists
a second, independently publishable governance-record package." No
phase since 145G.1 (145G.2, 145G.2V, 145G.3, 145G.3R, 145G.3V) revisited
this disclosure or tested the specific "call `readiness` again after
`publish`" sequence — every idempotency test found in
`test_phase_145g1_decision_session_cli_repair.py` and
`test_phase_145g3_decision_session_identity_binding.py` calls `readiness`
twice **before** any `publish`, never after. The identity-focused 145G.3/
145G.3V work correctly hardened the cache-hit branch against a
*mismatched-identity* bypass, but neither phase tested the orthogonal
*post-consumption* branch at all, because neither phase's own subject
matter directed it there.

### 6.5 Disposition: implementation defect, not contract ambiguity, not intentional design

- **Not intentional design.** No phase report from 145A through 145G.3V
  discloses "a session may produce more than one publishable package
  after its first has been consumed" as a deliberate choice. Every
  report that touches this code path frames `readiness` as unqualifiedly
  idempotent-by-key. The store's own docstring reveals the implementer's
  mental model was "idempotent for a bounded pending window," but this
  was never checked against IWPC-REQ-024's unqualified text, nor against
  CHGR-001 §2's one-act-one-record framing, nor re-examined after 145G.1
  gave the same lookup real construction power.
- **A contributing, secondary contract-drafting gap exists** (§2, §6.1):
  IWPC-001 never explicitly forecloses or permits the post-consumption
  re-invocation case; its "one **pending** package" language is
  ambiguous as to whether "pending" is a deliberate scope-limiter. This
  gap is real and independently confirmed, but it does not, on its own,
  excuse the implementation: the *unqualified* half of IWPC-REQ-024 ("
  subsequent invocations SHALL report the already-persisted package
  unchanged," with no stated exception) and CHGR-001's own definitional
  cardinality both point the same direction, and neither was consulted
  when this behavior went unchallenged through five independent-
  verification phases.
- **Conclusion: this is a genuine implementation defect**, with a
  disclosed-but-unescalated documentation trail (§6.4) and a secondary,
  real contract-textual gap that a future, separately-governed IWPC-001
  revision should close explicitly (stating, unambiguously, what
  `readiness`/`publish` must do once a session's package has already been
  consumed) before any repair is attempted.

### 6.6 Why this phase does not attempt a repair

Per this phase's own repair-authority rules, a Blocking defect may be
repaired only if the existing contracts *unambiguously* dictate the fix.
They do not: whether the correct behavior is "return the existing
consumed package's metadata," "raise a new, contract-defined
`already_published`-style domain error," or some other resolution is a
genuine design choice IWPC-001 does not currently make. Inventing that
choice here would exceed this phase's narrow repair authority ("No new
architecture or identity model is required" is arguable, but "the
existing contracts unambiguously dictate the repair" is not satisfied).
No repair was attempted. **This is recorded as Blocking Finding H-1.**

**Finding H-1 (Blocking):** A `Confirmed` decision session's
`decision-session readiness` command, when invoked again after its first
`PublicationReadinessPackage` has already been published, constructs and
persists a second, independently publishable package rather than
returning the existing (consumed) one or refusing — enabling a single
Human Governance Act to produce two independently valid Canonical Human
Governance Records. Root cause:
`FilesystemPendingReadinessStore.find_by_session_id` deliberately never
returns a `consumed/` record, and this lookup is the sole idempotency
gate `PublicationApplicationService.ensure_readiness_package`/
`persist_readiness_package` rely on. Independently reproduced via live
CLI subprocess execution against a disposable scratch repository; root
cause independently confirmed by direct source inspection; absence of
any test covering this sequence independently confirmed by direct test-
suite inspection; absence of any contract text permitting this outcome
independently confirmed by full-text reads of IWC-001, IWPC-001, PEC-001,
and CHGR-001.

### 6.7 Other replay/idempotency behavior (all confirmed correct)

- Repeated `readiness` calls **before** first publication: confirmed
  idempotent, same `package_id` returned (existing test coverage,
  independently spot-checked).
- `confirm` after a successful `confirm`: `confirmation_conflict`, never
  a silent second Confirmation (matches IWPC-REQ-104's explicit "not an
  idempotent one" framing) — confirmed by code read; not separately
  re-driven live in this phase since 145G.3V already adversarially
  confirmed it and no code path relevant to it changed since.
- `publish` naming an already-consumed `package_id`: confirmed by code
  read (`PublicationCoordinator._check_replay`) to report
  `publication_already_completed` without re-executing — this is the one
  guard that *is* correctly airtight, just scoped one level below where
  H-1 needed it.
- `cancel` idempotent-by-key, identity re-checked ahead of the idempotent
  branch even so: confirmed by code read, consistent with 145G.3V's own
  prior finding.
- No cryptographic tamper-evidence on persisted `owner_identity` (N-
  145G.3V-1, reconfirmed unchanged, Non-Blocking) and no last-write-wins
  authority-relevant race beyond Publication Authorization's own real
  exclusivity (IWPC-REQ-144, reconfirmed unchanged, Non-Blocking).

---

## 7. Persistence and Recovery Certification

All three filesystem stores (`FilesystemSessionRepository`,
`FilesystemPendingReadinessStore`, `FilesystemOrchestrationStore`) were
independently inspected and adversarially tested:

- **Atomic writes:** all three use the identical
  `tempfile.mkstemp(dir=root)` → write → `fsync` → `os.replace` pattern.
  Confirmed by code read; consistent with restart-safety requirements.
- **Path traversal:** `pcae decision-session status ../../../etc/passwd`
  and a malformed `CDS-../../etc` identifier were both rejected as
  `invalid_request` before any filesystem access, live-tested.
- **Symlink attack:** a session file was replaced with a symlink to
  `/etc/passwd`; `status` against it correctly reported
  `session_not_found` rather than following the symlink or leaking its
  content — live-tested.
- **Corruption handling:** a truncated JSON file and a file carrying an
  unsupported `schema_version` were both independently constructed and
  loaded; both produced clean `persistence_corrupt` errors with no
  partial-recovery attempt and no stack-trace leakage — live-tested.
- **Digest verification:** `FilesystemPendingReadinessStore` recomputes
  its SHA-256 content digest on every read, independently confirmed by
  code read (disclosed as advisory, not cryptographically strong,
  matching F-145A-6's existing disclosure — Non-Blocking, unchanged).
- **Consumed-disposition correctness (independent of H-1):** the
  move-to-`consumed/` step itself is correctly atomic
  (`os.replace`-backed) and never deletes-then-recreates; the defect in
  §6 is not a persistence-atomicity defect, it is an idempotency-gate
  scoping defect one layer up.

No silent repair, no fabricated migration, and no unannounced schema
tolerance was found anywhere in these three stores. **No Blocking
finding in this Part independent of H-1.**

---

## 8. Publication Integration Certification

`PublicationCoordinator` is confirmed, by direct source and by the
existing AST-based test (`test_phase_144c_publication_coordinator.py`),
to live outside `src/pcae/interactive_workflow/**` and to import no
interactive-workflow internals beyond the stateless handoff types.
`governance-record publish`'s only path into it is
`PublicationApplicationService.resume_publication → prepare_publication_request
→ hand_off → coordinator.authorize(...) → coordinator.execute(...)`,
unchanged, in PEC-001's own fixed order. No code path under
`interactive_workflow/**` calls `write_record`/`commit_publication`
directly (grep-confirmed); both filesystem stores in
`interactive_workflow/**` actively guard their own storage roots against
overlapping `.pcae/governance-records/`.

**Finding H-1 is, in substance, also a publication-integration finding**:
the boundary itself (workflow constructs, coordinator authorizes/
executes) is intact and was not crossed or bypassed — but the workflow
side's own construction of a *second*, contractually-unintended package
is what hands PEC-001's correctly-scoped, package-level replay guard a
legitimate-looking new input it has no basis to refuse. This is recorded
once, as H-1, not duplicated as a second finding — it is a single defect
visible from two angles (idempotency, §6, and publication-boundary
input hygiene, this Part).

No other publication-integration defect was found. Pending-readiness
consumption disposition (`pending` → `consumed/`) is correctly traceable
to its originating session in every case observed, including the
duplicate-package scenario (both packages correctly cite the same
`session_id`).

---

## 9. End-to-End Operational Certification

Genuine, subprocess-separated CLI flows were run in an isolated scratch
repository (`pcae init`), with no direct repository mutation, no direct
model construction, and no fixture-only state injection:

**Happy path**, one subprocess invocation per step, confirmed each state
transition via `status`: `create` → `evidence` → `select` → `preview`
(state transition confirmed) → `confirm` → `readiness` (package
constructed) → `publish` (CHGR created) → `readiness` again (fresh
process; this is where H-1 was found) → `status` (fresh process,
confirms `Confirmed` persists correctly across restarts).

**Negative paths run:** wrong identity (rejected, exit 6); missing
identity (argparse rejection, exit 2); whitespace/case-variant identity
(rejected); cross-session Preview-digest substitution (rejected as
`confirmation_conflict`, exit 3); path-traversal session identifiers
(rejected, `invalid_request`); a symlinked session file (rejected,
`session_not_found`, no content leaked); truncated JSON persistence
(rejected, `persistence_corrupt`); unsupported schema-version persistence
(rejected, `persistence_corrupt`).

All outputs were deterministic JSON with stable `error_type` values and
the exit codes IWPC-001's closed taxonomy specifies; no raw traceback or
filesystem path was ever printed to the operator in any negative case
tested.

---

## 10. Security Certification

Adversarial coverage actually executed this phase (live, against the
scratch repository): session-identifier path traversal; symlink
substitution of a session file; malformed/truncated/wrong-schema-version
persistence; whitespace and case-variant identity claims; cross-session
artifact (Preview-digest) substitution; absence of any hidden force/
bypass flag (confirmed by parser inspection). All held fail-closed.

Adversarial coverage independently reconfirmed from 145G.3V's own prior
work rather than re-run fresh this phase (no code relevant to it changed
since): environment-based identity inference attempts
(`$USER`/`$GIT_AUTHOR_NAME`/agent-lock-id injection, previously
adversarially tested and confirmed rejected).

The one genuine adversarial finding from this phase's own fresh testing
is H-1 — not a classic injection/traversal/tamper vulnerability, but a
governance-integrity defect: an unauthenticated *sequence* of otherwise-
valid, correctly-authorized commands produces a second canonical
governance record for one human decision. This is recorded once, in §6,
not duplicated here.

Runtime confirmed to expose no engineering execution capability, before
and after all adversarial testing (`pcae runtime inspect --json`:
`registered_plugin_count: 0`, `registry_status: empty`).

---

## 11. Dependency and Layering Certification

Confirmed dependency direction: CLI (`commands/decision_session.py`,
`commands/governance_record.py`) → Application
(`interactive_workflow/application/**`) → Domain/orchestration
(`interactive_workflow/{session,orchestration,state_machine,models}/**`)
→ Persistence (`interactive_workflow/persistence/**`) and Publication
(`governance/publication/**`). The single composition root,
`build_application_context()`, is the only site in the repository that
constructs `SessionCoordinator`/`PublicationCoordinator`/
`FilesystemSessionRepository`/`FilesystemPendingReadinessStore` — grep-
confirmed. No command handler calls a domain/persistence object
directly; every handler goes through
`SessionApplicationService`/`PublicationApplicationService` only.

**One Non-Blocking, previously-disclosed coverage gap, independently
reconfirmed:** two separate AST-based tests exist
(`test_phase_145f_application_service_boundary.py`, scoped to
`interactive_workflow/application/*.py`; `test_phase_144c_publication_coordinator.py`,
scoped to `governance/publication/*.py`), but neither — nor any other
test — constrains imports *into* `interactive_workflow/**` subpackages
other than `application/` (e.g. `persistence/`, `orchestration/`,
`session/`, `state_machine/`) from `pcae.commands`/`pcae.cli`. In
current source, no such import actually exists (confirmed by grep — the
composition root is the only place these are constructed, and no
non-application interactive_workflow module imports `pcae.cli` or
`pcae.commands`), so today's compliance is real, just not test-enforced
outside `application/`. This is the same class of gap 144D originally
disclosed as Finding F-3 (test coverage, not actual violation) — it
persists, unrepaired, unescalated, and correctly still Non-Blocking,
since no actual dependency-direction violation exists today.

No composition-root exception beyond `build_application_context()` was
found. No unauthorized policy widening was found in `.pcae/policy.toml`
(the `commands → interactive_workflow` edge documented since 145G was
independently confirmed to still be the only relevant entry).

---

## 12. Documentation and Operator Usability Certification

`docs/COMMANDS.md`'s `decision-session`/`governance-record` sections were
independently compared, argument-for-argument, against the current
`cli.py` parser definitions — they match exactly, including
`--as-identity` on every mutating command. A full CLI-only happy-path
flow (§9) was actually driven using only the documented command syntax,
with no source-code reference needed to construct any invocation, and it
reached publication successfully — confirming an operator can complete
the golden path from documentation alone.

**One documentation gap, directly connected to H-1:** `docs/COMMANDS.md`
states no idempotency/replay expectations for `readiness` or `publish`
at all — an operator following the documentation alone has no way to
learn that re-invoking `readiness` after a successful `publish` is unsafe
in any sense, let alone that it currently mints a second publishable
package. This is recorded as part of H-1's severity, not as a separate
finding, since it is a symptom of the same underlying gap rather than an
independent defect.

No other documentation-accuracy gap was found for this chapter's command
surface.

---

## 13. Historical Finding Closure Audit

Every Blocking and material Non-Blocking finding raised from 143A through
145G.3V was independently traced to current contract, source, test, and
operational evidence (not merely to a report's own closure claim):

| Finding | Severity | Repair phase | Independent 145H disposition |
|---|---|---|---|
| B-1 (IWC-001 state-table gaps) | Blocking | 143I.1 | Confirmed closed — `TRANSITION_TABLE` in current code carries all six previously-missing exits (§3). |
| F-1 / JC-2 (CHGR provenance boundary) | Blocking (impl.) | 144E (contract) + 144F (impl.) | Confirmed closed — `PublicationReadinessPackage`'s widened fields are populated verbatim in `hand_off`/`build_publication_record`, independently spot-checked in source. |
| B-1 (IWPC-001 state-literal casing) | Blocking | 145C (self-repaired) | Confirmed closed — IWPC-001 and `SessionState` both PascalCase, matching. |
| F-145G-1 (five missing commands) | Blocking | 145G.1 | Confirmed closed — all five commands exist and were independently exercised live this phase (§9). |
| F-145G.1-1 (no `AwaitingDecision` exit) | Blocking | 145G.2, verified 145G.2V | Confirmed closed — `select` independently exercised live this phase, drives exactly this transition (§9). |
| F-145G.2V-1 (no identity-bound resumption) | Blocking | 145G.3, verified 145G.3V | Confirmed closed — independently re-derived from source (§5) and independently re-adversarially-tested live this phase (§5), not merely accepted from 145G.3V's own verdict. |
| F-145G.2-1 (no `AwaitingClarification` entry) | Non-Blocking, disclosed, open | unrepaired | Confirmed still open, unchanged, correctly out of scope (§3). |
| N-145G.3V-1/2/3 | Non-Blocking | unrepaired | Confirmed still present, unchanged, correctly Non-Blocking (§4, §6.7). |
| F-3 (144D, forbidden-import test coverage) | Non-Blocking | unrepaired | Confirmed still present in its current form (§11), no actual violation. |
| **H-1 (this phase)** | **Blocking, new** | **not repaired (out of this phase's repair authority, §6.6)** | **Confirmed open. See §6.** |

No finding was accepted as closed merely because a report said so; each
row above reflects this phase's own independent source/test/live-CLI
evidence, not a citation to the closing phase's own claim.

---

## 14. Lifecycle and Evidence Integrity Certification

Canonical reports exist for every phase 143A–145G.3V (confirmed by
directory listing). `PROJECT_STATUS.md`'s "Current Phase" section
correctly names 145G.3V, VERIFIED WITH NON-BLOCKING FINDINGS, as the
latest completed phase, and correctly recommends (without authorizing)
145H — independently confirmed by direct read at the start of this
phase, matching `pcae session bootstrap`'s own report. `tasks/TODO.md`'s
stale reference to Phase 137T was independently confirmed to be exactly
the kind of informational-only staleness `pcae session bootstrap` itself
already disclaims; PROJECT_STATUS.md is correctly treated as
authoritative over it, per this phase's own governing instruction.

The pre-existing lock-release-ordering defect discovered during 145G.3R
(`complete_phase()`, `src/pcae/core/phase.py:30-54`, releases the agent
lock unconditionally before the transition validator that could reject
the completion ever runs) was independently re-confirmed present in
current source, by direct code read, at exactly the cited lines. This
defect governs PCAE's own phase/task lifecycle tooling — it is
structurally outside the Interactive Workflow + Publication CLI/Transport
chapter's own engineering surface (it touches `pcae phase complete`'s
lock-handling, not any `decision-session`/`governance-record` code path)
and does not affect, weaken, or cast doubt on any evidence this
certification relies on. It is recorded here, as instructed, as an
external lifecycle observation: still open, unrepaired, and — per this
phase's own No-Go list and its own narrow "chapter-level" scope — not a
basis for withholding a chapter-level verdict on its own. It is not, by
itself, why this phase's verdict is NOT CERTIFIED; H-1 is.

No historical report was found rewritten; no repository history was
altered by this phase.

---

## 15. Regression and Baseline Certification

- **Chapter-scoped subset** (`decision_session`, `interactive_workflow`,
  `145a`–`145g`, `publication_coordinator`, `chgr`, `iwc_143` keyword
  selection): **1195 passed, 0 failed.**
- **`fast_green` gate:** **4391 passed, 0 failed** — matching
  PROJECT_STATUS.md's own recorded baseline exactly.
- **Full governed suite:** **26654 passed, 39 failed, 10 skipped** (`-n
  auto`, 2200.12s). Every one of the 39 failures was individually
  triaged, not dismissed by count:
  - **1 failure was this phase's own test-environment contamination,
    not a defect**: `test_scope_gate.py::test_no_repository_mutation`
    compares `git status --porcelain` immediately before and after a
    subprocess call; this phase's own in-progress, not-yet-committed
    canonical report file (`docs/PHASE_145H_...md`) was created by this
    phase's own work *while the full-suite run was already in flight in
    the background*, so the "before" snapshot (captured pre-existence)
    differed from the "after" snapshot (post-existence) for a reason
    entirely unrelated to the subprocess under test. Independently
    confirmed by re-running this single test against a `git stash`-clean
    tree: it passes. Not a chapter defect; an artifact of this
    certification's own live methodology.
  - **38 failures were independently confirmed pre-existing and
    unrelated to this chapter**, by two methods: (a) every failing test
    file was grepped for any reference to
    `interactive_workflow`/`decision_session`/`governance.publication`/
    `decision-session`/`governance-record` — zero matches across all 38;
    they cluster entirely in CLTR Typed-Authority-Model wheel/packaging
    tests, finalization-transaction/notification-reconciliation tests,
    migration-verification tests, the advisory-runtime-directory
    contract test, and `tasks/TODO.md`/`PROJECT_STATUS.md` bootstrap-
    consistency tests. (b) A representative sample (`bootstrap_todo_consistency`'s
    4 failures, plus `test_advisory_runtime_contract`,
    `test_phase_reports`'s 128B1 reconciliation test, one
    `test_cltr_authority_136z_shared_core` wheel test, and one
    `test_finalization_transaction_134e10` test) was independently
    re-run against a `git stash`-clean tree (this phase's own uncommitted
    changes fully removed) — every one of them failed identically at
    clean `HEAD`, confirming they predate this phase's work entirely. The
    4 `bootstrap_todo_consistency` failures were further root-caused: the
    parser `_extract_recommended_next_phase_values` requires a literal
    "Recommended next phase:" labeled sentence in `PROJECT_STATUS.md`'s
    "Current Phase" section, and Phase 145G.3V's own "Current Phase"
    prose (still at `HEAD` before this phase's edit) never used that
    literal label — an inherited, pre-existing governance-documentation
    regression from 145G.3V, not from this chapter's engineering
    behavior and not introduced by this phase. This matches the same
    class of full-suite order/environment-dependent flakiness 144G's own
    Finding G-9 and 143F's Finding 143F-F2 already disclosed
    (wheel/`python -m build` unavailability; run-to-run failure-count
    variance) — independently reconfirmed still true today, unchanged.

No test was weakened, skipped, or deleted to reach this phase's verdict,
and none needed to be. No failure inherited from outside this chapter
was found in the chapter-scoped subset or in `fast_green`, and every
full-suite failure was independently traced to a cause outside this
chapter's own engineering surface. H-1 itself is a **coverage gap** (an
untested sequence), not a failing assertion anywhere in the existing
suite — exactly why the chapter's own tests, run in full, were not
expected to and did not surface it on their own. This is itself part of
the finding: passing tests were an insufficient signal for chapter-level
certification, which is the entire premise of this phase's independent,
adversarial method.

---

## 16. Findings Register (Summary)

**Blocking:**

- **H-1** — Duplicate CHGR creation via post-consumption `readiness`
  re-invocation (§6). New this phase. Not repaired (outside this phase's
  narrow repair authority — see §6.6). **This is the sole reason this
  phase's verdict is NOT CERTIFIED.**

**Non-Blocking (all pre-existing, independently reconfirmed unchanged,
none newly introduced by this phase):**

- F-145G.2-1 — no command opens `AwaitingClarification` (§3).
- N-145G.3V-1/2/3 — no cryptographic tamper-evidence on `owner_identity`;
  cosmetic `__all__` omission; `status` incidentally returns
  `owner_identity` (§4, §5).
- F-3 (144D) — forbidden-import test coverage incomplete outside
  `application/`/`governance/publication/` (§11).
- F-145A-4/5/6 — no authority-evaluation mechanism; concurrent-write
  races beyond `os.replace`; unauthenticated pending-package tampering
  possible without the digest check catching intent, only content change
  (all disclosed since 145A, unchanged).
- Documentation gap: `docs/COMMANDS.md` discloses no idempotency/replay
  semantics for `readiness`/`publish` (§12) — bound to H-1's eventual
  repair.

**Deferred:**

- Model 3 (delegated authorization token) — explicitly out of chapter
  scope (PEC-001 §6, unchanged).
- Retention policy for terminal-state sessions — explicitly future work
  (IWC-001 §14, unchanged).

**Historical, external, not part of this chapter's own certification
scope:**

- The 145G.3R lock-release-ordering lifecycle-tooling defect (§14) —
  confirmed still open, confirmed not to affect this certification's
  evidence.

---

## 17. Certification Verdict

**NOT CERTIFIED — BLOCKING FINDINGS.**

One Blocking finding (H-1) was independently confirmed, by direct source
inspection, by live adversarial CLI reproduction against a disposable
scratch repository, and by independent re-derivation of the governing
contracts' own uniqueness intent: a `Confirmed` decision session's
`readiness` command, re-invoked after its first `PublicationReadinessPackage`
has already been published, silently constructs and persists a second,
independently publishable package, which `governance-record publish`
then happily turns into a second, independent Canonical Human Governance
Record for the same single Human Governance Act. No contract text
permits this outcome; no phase report ever disclosed it as intentional;
no existing test exercises the sequence that reveals it.

Every other certified dimension — chapter scope and ownership boundaries,
cross-contract coherence, the ten-state machine's reachability and
fail-closed terminal-state enforcement, CLI surface completeness,
identity/authority/provenance separation (including live re-confirmation
of F-145G.2V-1's closure), persistence atomicity/corruption/symlink/
path-traversal handling, the Publication Execution boundary's structural
integrity, dependency layering, documentation accuracy for the command
surface itself, and full regression (chapter subset, `fast_green`, and
the full governed suite) — held up under independent, adversarial
scrutiny and would, on their own, have supported at least CERTIFIED WITH
NON-BLOCKING FINDINGS. H-1 alone is why this chapter cannot be frozen as
a stable baseline today.

**Recommendation (not authorized by this report):** a narrowly scoped
repair phase — after a governed IWPC-001 revision explicitly states what
`readiness`/`publish` must do once a session's package has already been
consumed — to close H-1 by extending
`FilesystemPendingReadinessStore`'s session-keyed lookup (or the
idempotency gate that consumes it) to recognize an already-consumed
package and either return its existing disposition or refuse
construction outright, per whichever the contract revision specifies.
This report does not authorize that phase, any repair, 145H.1, 145G.4,
145I, Phase 146, or any other later work.

---

## 18. No-Go Confirmation

No engineering behavior was changed. No file under `src/` or `tests/`
was modified. No file under `docs/contracts/` was modified — IWC-001,
IWPC-001, PEC-001, and CHGR-001 were read only. No runtime capability
change was made; `pcae runtime inspect --json` remains
Observed/observe/unavailable, confirmed before and after this phase's
work. No execution capability was added. No repair was invented for
H-1, per §6.6. No force/bypass flag, automatic confirmation, automatic
authorization, or automatic publication was added. No redesign of the
workflow was performed. CHGR ownership, lifecycle authority, and
publication ownership were left unmodified and were independently
re-confirmed intact (§8, §11). No historical report was rewritten; no
git history was altered. 145H.1, 145G.4, 145I, and Phase 146 were not
begun, and this report does not authorize any of them.
