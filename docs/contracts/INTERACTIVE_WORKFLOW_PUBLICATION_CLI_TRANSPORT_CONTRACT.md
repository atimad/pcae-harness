# IWPC-001 v1.4 — Interactive Workflow + Publication CLI/Transport Contract

## Contract identity and status

**Contract:** IWPC-001
**Version:** 1.4
**Status:** FROZEN
**Frozen by:** Phase 145B — Interactive Workflow + Publication CLI/Transport
Contract Freeze
**Revised by:** Phase 145C — Interactive Workflow + Publication CLI/Transport
Contract Independent Verification (§32 below; repairs Finding B-1, the sole
Blocking finding this phase's independent verification demonstrated: §12 and
§5's session-state literals were given in lowercase snake_case while
`SessionState`'s actual, frozen serialized values — `Session.session_state.value`
as produced by `interactive_workflow/serialization/schema.py`'s `to_payload` —
are PascalCase; every such literal is corrected to match the real enum
values exactly; no state added, removed, merged, or renamed, no semantic
change to any transition, and no requirement renumbered)
**Revised by:** Phase 145G.2 — Interactive Workflow Decision-Selection
Command and Contract Repair (§33 below; additive minor revision, v1.1 ->
v1.2, closing Blocking finding F-145G.1-1: no command in v1.1's frozen §5
command surface transitioned a session out of `AwaitingDecision`. Adds
`decision-session select`, IWPC-REQ-192-196, to §5's command surface
(IWPC-REQ-014 amended in place to list it, per IWPC-REQ-191's own
additive-evolution allowance); no existing requirement narrowed, removed,
or renumbered)
**Revised by:** Phase 145G.3 — Decision-Session Identity-Bound Resumption
Contract and Implementation Repair (§34 below; additive minor revision,
v1.2 -> v1.3, closing Blocking finding F-145G.2V-1: no command in the
`decision-session` family enforced IWC-REQ-022/IWC-REQ-151's identity-bound
resumption requirement. Adds a required `--as-identity` claim to every
mutating `decision-session` command (`evidence`, `select`, `clarify`,
`preview`, `confirm`, `cancel`, `readiness`), a new closed-taxonomy
`error_type` (`identity_binding_mismatch`) and exit-code class (6), and
corrects IWPC-REQ-195's now-superseded "select accepts no identity input"
text; `create`/`status` unaffected; no existing transition, state, or
persisted schema field changed)
**Revised by:** Phase 145H.1 — Post-Consumption Readiness Uniqueness
Contract Clarification (§35 below; additive minor revision, v1.3 -> v1.4,
closing the contract-drafting half of Blocking finding H-1, independently
confirmed by Phase 145H — Interactive Workflow Chapter Independent
Certification: v1.3 never stated what `decision-session readiness`/
`governance-record publish` must do once a session's
`PublicationReadinessPackage` has already been consumed by successful
publication, an ambiguity that let a genuine implementation defect survive
five independent-verification passes unchallenged. This revision freezes
the required post-consumption uniqueness invariant, extends the
readiness-construction idempotency-by-key guarantee (IWPC-REQ-024) across
the package's full lifecycle rather than only its pending state, and adds
explicit replay, recovery, and historical-inconsistency semantics. No
requirement is narrowed or removed; H-1 itself remains open, pending a
future, separately governed implementation phase this revision does not
authorize)
**Architecture basis:** Phase 145A — Interactive Workflow + Publication
CLI/Transport Architecture
(`docs/PHASE_145A_INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_ARCHITECTURE.md`),
GLP-001 §6.1 Stage 2 (Contract Freeze), applied here exactly as Phase 143B
converted Phase 143A into CHGR-001 and Phase 144B converted Phase 144A
into PEC-001.
**Governed subject:** The **user-facing invocation and transport path**
connecting a human caller to the already-implemented, already-frozen
Interactive Workflow (IWC-001 v1.2) and Publication Execution (PEC-001
v1.1) subsystems: the `pcae decision-session` command family, the
`pcae governance-record publish` verb, the two new narrowly-scoped
repository-local stores (`SessionRepository` filesystem implementation,
Pending Publication-Readiness-Package Store) those commands persist
through, and the transport-neutral request/response shapes carried between
a caller and those subsystems.

IWPC-001 is the sole normative authority governing **the CLI/transport
invocation layer**. It does not govern the Interactive Decision Session
layer itself (that remains IWC-001's sole normative authority, unmodified),
does not govern Publication Execution itself (that remains PEC-001's sole
normative authority, unmodified), does not govern the Canonical Human
Governance Record artifact class (CHGR-001, unmodified), does not redefine
the Typed Authority Model Consumption or Production Consumption Contracts
(TAMC-001, TAMPC-001, unmodified), and does not modify GLP-001 or any
other framework contract. Where this contract cites IWC-001, PEC-001,
CHGR-001, TAMC-001, or TAMPC-001, the citation illustrates an obligation
this contract imposes on the invocation/transport layer specifically; it
does not redefine the underlying provision — mirrors PEC-001 §1's and
IWC-001 §1's identical illustrative-citation discipline.

Phase 145A's Architecture stage is the approved design basis for every
section below. This contract independently re-derives every requirement
directly from Phase 145A's own text (treated as evidence of architectural
intent, never as contractual authority), from IWC-001 v1.2's own frozen
text (cited by `IWC-REQ-###`), from PEC-001 v1.1's own frozen text (cited
by `PEC-REQ-###`), from CHGR-001's own frozen text, from TAMC-001/
TAMPC-001's own frozen text, and from direct re-reading of
`src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`,
`src/pcae/commands/governance_record.py`, `src/pcae/cli.py`, and the
existing forbidden-import boundary test suites — not merely restated from
Phase 145A's own summary of them.

**Compatibility policy:** IWPC-001 fills exactly the invocation-surface gap
Phase 145A named. It narrows nothing in IWC-001 or PEC-001; it only
constrains the new CLI/transport layer built above both. Any future
implementation phase (145D–145I) MUST conform to IWPC-001 as written;
IWPC-001 itself MAY be revised only through a governed superseding
contract revision (§30), never through an implementing phase's own
discretion.

**Requirement numbering convention:** Requirements are identified
`IWPC-REQ-001` through the final requirement in §31, sequential, with no
gaps and no reuse, grouped by the section that introduces them. Once
frozen, no requirement identifier is renumbered, reassigned, or reused,
even if a future revision deletes the requirement it once named (a
retired requirement's identifier is marked "Retired" in place, never
reused for a different obligation — mirrors PEC-001's and IWC-001's own
amendment discipline, §30 below).

**Runtime:** State: Observed / Maximum Capability: observe / Execution
Availability: unavailable — unaffected by this contract; nothing this
contract defines is implemented by this phase.

---

## 1. Purpose

IWPC-001 freezes the stable public behavior of the first governed,
user-facing invocation surface over PCAE's Interactive Workflow and
Publication subsystems, so that a later, separately-authorized
implementation phase can build against an unambiguous, falsifiable
contract rather than reinterpreting Phase 145A's architectural prose.

This contract governs command surface, transport-neutral request/response
shapes, decision-session persistence, pending-readiness-package
persistence, confirmation/authorization separation, identity/provenance
handling, errors and exit codes, idempotency/replay/concurrency/recovery,
and observability/compatibility for that invocation layer only.

## 2. Scope and No-Go Boundary

### 2.1 In scope

This contract MAY define behavior for (IWPC-REQ-001):

**IWPC-REQ-001.** This contract governs decision-session creation,
decision-subject input, option-set input, preview generation, explicit
confirmation, readiness-package construction, readiness-package
persistence, publication-authorization input, Publication Coordinator
invocation, and deterministic result reporting, at the CLI/transport
layer only.

### 2.2 Out of scope

**IWPC-REQ-002.** This contract SHALL NOT govern engineering execution,
shell execution, repository mutation outside existing Publication
authority, Permission Broker action execution, lifecycle promotion,
automatic authority evaluation, automatic confirmation, automatic
publication, CHGR ownership changes, or runtime capability changes. Every
such topic remains exclusively governed by its own existing contract
(Permission Broker contracts, lifecycle contracts, CHGR-001, runtime
contracts) or remains, as Phase 145A found, ungoverned by any existing
contract and is not newly governed here.

**IWPC-REQ-003.** This contract SHALL NOT introduce, and no command,
flag, transport request, or store operation governed by it MAY constitute,
an authority-evaluation policy. Per Phase 145A §10 (independently
reconfirmed in this phase's own research, §29 below), no
`eligible_authority`-checking mechanism exists anywhere in this repository
for CHGR-style decisions; this contract MUST NOT invent one.

## 3. Normative Terminology

Terms below are normative wherever they appear in this contract in Title
Case or fixed-width form. Where a term is already defined by IWC-001,
PEC-001, CHGR-001, TAMC-001, or TAMPC-001, this contract adopts that
definition unchanged and does not restate a synonym.

**IWPC-REQ-004.** The following terms SHALL carry exactly the meaning
given here, and no command, document, or output governed by this
contract SHALL use a different or narrower meaning for the same term:

- **Caller.** The OS-level process invoking the CLI. Identity is never
  read from OS/shell/transport authentication for any governance purpose
  (IWPC-REQ-041).
- **Decision maker.** The human identified by `--owner-id` at
  `decision-session create` (IWC-001's session-owner concept, unchanged).
- **Confirmer.** The human performing `decision-session confirm`; bound
  to the session per IWC-REQ-036/037 (identity SHALL match the session's
  bound identity; a different identity is rejected fail-closed).
- **Authorizing principal.** The human identified by `--operator-id` at
  `governance-record publish`; distinct from decision maker and confirmer
  (§2 Confirmation Contract, PEC-REQ-034).
- **Decision session.** IWC-001's Interactive Decision Session, identified
  `CDS-<uuid4>`, unchanged by this contract.
- **Decision subject.** IWC-001's Decision Subject, referenced (not
  copied) via `--subject-ref` at creation.
- **Option set.** The set of Decision Template options IWC-001 already
  governs; this contract only names how it is referenced at the CLI
  boundary, never how it is authored or validated.
- **Preview.** IWC-001 §2's Preview and its Preview Digest, adopted
  unchanged; this contract's `preview` command is a thin, unconditional,
  unsuppressible rendering of it (IWPC-REQ-058, IWC-REQ-112).
- **Confirmation.** IWC-001 §10's distinct, non-defaultable act, adopted
  unchanged.
- **PublicationReadinessPackage.** The immutable dataclass
  `interactive_workflow.publication_handoff.models.PublicationReadinessPackage`,
  as widened by IWC-001 §26 / Phase 144E, adopted unchanged; this contract
  persists it verbatim and never reconstructs it (§16).
- **Pending readiness package.** A `PublicationReadinessPackage` persisted
  by `decision-session confirm` into the Pending-Readiness Store (§13)
  awaiting a future `governance-record publish` invocation; a
  transport/persistence concept this contract introduces, not an IWC-001
  or PEC-001 concept.
- **AuthorizationEvent.** PEC-001 §6's `PublicationAuthorizationEvent`,
  adopted unchanged; this contract only names how its required fields
  (`operator_id`, `package_id`) are supplied at the CLI boundary (§17).
- **Publication request.** The transport-neutral input object a
  `governance-record publish` invocation constructs before calling
  `PublicationCoordinator.authorize`/`.execute` (§10).
- **Publication attempt.** PEC-001's existing attempt-audit concept
  (`PublicationRecordStore`'s `attempts/` artifacts), adopted unchanged;
  this contract never creates a second attempt-audit path.
- **Publication result.** PEC-001's `PublicationExecutionResult`, adopted
  unchanged; this contract only defines how it is rendered at the CLI
  boundary (§7).
- **Session repository.** The narrow `SessionRepository` ABC already
  defined at `interactive_workflow/persistence/repository.py`; this
  contract freezes the contract for the first concrete filesystem
  implementation of it (§12), not the ABC itself (IWC-001/143K territory,
  unmodified).
- **Pending-readiness store.** The new store this contract defines (§13);
  no prior contract defines or names it.
- **Correlation identifier.** No new correlation-id scheme is introduced
  (Phase 145A §7.5, ratified unchanged, IWPC-REQ-005): the existing
  `session_id` (`CDS-<uuid4>`), `package_id`, and `record_id`
  (`chgr-<uuid4>`) already suffice to correlate a request across every
  stage.
- **Replay.** A repeated invocation carrying an identifier (session,
  package, or authorization) that already has a persisted, terminal
  outcome. See §20.
- **Retry.** A repeated invocation after a failed, non-terminal attempt,
  intended to reach the same terminal outcome the first attempt sought.
  See §20.
- **Idempotency.** The property that a repeated invocation with identical
  identifying inputs SHALL produce the same observable outcome as the
  first successful invocation, without duplicating persisted side
  effects. See §20.
- **Stale artifact.** A persisted session or pending package whose
  referenced upstream state (preview digest, confirmation, or session
  state) no longer matches what a dependent operation expects. See §14,
  §22.
- **Transport adapter.** The CLI command module itself
  (`src/pcae/commands/decision_session.py` and the `publish` addition to
  `src/pcae/commands/governance_record.py`, both future-phase artifacts
  not created by this contract-freeze phase). Per Phase 145A's Model D
  rejection, this contract does NOT name or require a separate
  transport-neutral application-service class; the CLI command module IS
  the transport adapter for v1.0 (IWPC-REQ-006).
- **Application boundary.** The point at which a transport adapter calls
  into `SessionCoordinator`/`WorkflowOrchestrator` (Interactive Workflow)
  or `PublicationCoordinator` (Publication); see §25 Dependency Contract.
- **Machine-readable output.** The `--json` rendering of any command
  governed by this contract (§7).

**IWPC-REQ-005.** No new correlation-identifier scheme SHALL be
introduced. `session_id`, `package_id`, and `record_id` (once a CHGR
exists) SHALL remain the complete, sufficient set of identifiers a caller
needs to correlate a decision from creation through publication.

**IWPC-REQ-006.** No transport-neutral application-service class SHALL be
required by v1.0. The CLI command module is the transport adapter; a
future, separately governed contract revision MAY introduce Model D
(Phase 145A §6, rejected for v1.0) without this contract needing
retraction, per the Extensibility discipline in §30.

## 4. Required Architecture Invariants

### 4.1 Authority Neutrality

**IWPC-REQ-007.** The CLI and transport layer MAY collect identity and
authority claims (e.g., `--owner-id`, `--operator-id`) and MAY validate
their structural completeness (non-empty, well-formed).

**IWPC-REQ-008.** The CLI and transport layer MAY transport existing
authority evidence (e.g., an `AuthorizationEvent`'s fields) unchanged
between a caller and `PublicationCoordinator`.

**IWPC-REQ-009.** The CLI and transport layer SHALL NOT establish
governance authority, SHALL NOT infer authority from local account
identity, SHALL NOT infer authority from shell access, SHALL NOT infer
authority from transport authentication, and SHALL NOT invent an
authority-evaluation policy that does not already exist upstream in
IWC-001, PEC-001, TAMC-001, or TAMPC-001.

### 4.2 Publication Ownership

**IWPC-REQ-010.** Only `PublicationCoordinator` (PEC-001) MAY authorize
publication, execute publication, create CHGR artifacts, own publication
replay/concurrency decisions, or produce an authoritative publication
outcome. No command, store, or transport object governed by this contract
MAY duplicate any of these responsibilities.

### 4.3 Interactive Workflow Ownership

**IWPC-REQ-011.** Only the Interactive Workflow subsystem (IWC-001) MAY
own decision-session semantics, option-set semantics, preview
construction, confirmation semantics, or `PublicationReadinessPackage`
construction. The `decision-session` CLI command family SHALL delegate
each of these to `SessionCoordinator`/`WorkflowOrchestrator`/
`PublicationHandoff` and SHALL NOT reimplement any of them.

### 4.4 Separation

**IWPC-REQ-012.** No command, flag, transport request, or store operation
governed by this contract MAY collapse any two of: Confirmation,
Publication readiness, Authorization, Publication, Engineering execution.
Each remains a structurally distinct act performed by a distinct
invocation.

### 4.5 Runtime Neutrality

**IWPC-REQ-013.** Nothing this contract defines, and nothing a future
implementation of it produces, SHALL change runtime state, maximum
runtime capability, execution availability, Permission Broker
capabilities, or governed engineering execution availability.

## 5. Command Contract — Decision-Session Family

`decision-session` is a new top-level CLI noun, deliberately not a
`pcae session` subcommand — `pcae session` already names the unrelated
PCAE-agent-workflow bootstrap/lease surface (`.pcae/session.json`,
`pcae session bootstrap`), and IWC-001 §11.1 (IWC-REQ-113/114) requires
Session state (IWC-001), Confirmation state, CHGR lifecycle state,
Runtime state, and Project-phase-lifecycle state to remain five
non-substitutable classes; reusing the `session` noun for a sixth,
unrelated concept would blur that boundary at the CLI's own surface.

**IWPC-REQ-014.** The command surface SHALL be exactly:

```
pcae decision-session create   --template-ref <id> --subject-ref <id> --owner-id <id> [--json]
pcae decision-session evidence <session-id> --declare <evidence-id> [--declare <evidence-id> ...] [--json]
pcae decision-session select   <session-id> --option-id <id> --options-presented <id> [--options-presented <id> ...] --template-version <version> [--rationale <text>] [--conditions <text>] [--json]
pcae decision-session clarify  <session-id> --question <text> --answer <text> [--json]
pcae decision-session preview  <session-id> [--json]
pcae decision-session confirm  <session-id> --preview-digest <digest> --statement <text> [--json]
pcae decision-session status   <session-id> [--json]
pcae decision-session readiness <session-id> [--json]
pcae decision-session cancel   <session-id> --reason <text> [--json]
```

(``select`` added by Phase 145G.2, IWPC-REQ-192-196 -- see §5.3 -- closing
Blocking finding F-145G.1-1.)

(`inspect` and `abandon`, named illustratively in this phase's governing
prompt, are frozen under the names `status` and `cancel` respectively,
matching Phase 145A's own selected names and this repository's existing
`governance-record inspect`/lifecycle-`cancel` vocabulary; `readiness` is
added, distinct from `status`, to expose whether a session's pending
package exists/has been consumed without re-deriving that fact from
`status`'s own session-state output — see IWPC-REQ-024.)

### 5.1 `decision-session create`

**IWPC-REQ-015.** Purpose: create a new decision session bound to a
Decision Template and Decision Subject reference, owned by the named
decision maker. Required arguments: `--template-ref`, `--subject-ref`,
`--owner-id`, none defaulted (IWC-REQ-051: no auto-selection). No
mutually exclusive arguments. Input source: CLI arguments only (§6).
Non-interactive by default; no interactive prompt mode is defined by v1.0
(a future contract revision MAY add one under §30's additive-evolution
rule). Output: session identity, initial state (`Created`), and
`schema_version` (§7). State transition: (none) → `Created`. Idempotency:
non-idempotent — each invocation creates a new, distinct session with a
new `session_id`; no idempotency key is defined for creation (a caller
wanting to avoid duplicate sessions MUST track its own client-side
correlation, e.g. reusing `--subject-ref`, but the CLI itself performs no
deduplication). Failure: `template_not_found`, `subject_not_found`,
`invalid_request` (missing/malformed argument). Exit codes: §8.

### 5.2 `decision-session evidence`

**IWPC-REQ-016.** Purpose: declare machine-assembled evidence references
against an existing session, delegating to `orchestrate_evidence`.
Required: `<session-id>`, one or more `--declare`, `--as-identity` (Phase
145G.3, §34: identity-bound resumption, IWC-REQ-022/151). Accepted input source:
CLI arguments only. Interactive/non-interactive: identical (no prompt).
Output: updated evidence-ref list, resulting state (`Created` →
`EvidenceReady` once IWC-001's own evidence-completeness rule is
satisfied, otherwise unchanged). State transition: per IWC-001 §4.4,
governed there, not redefined here. Idempotency: idempotent by key —
re-declaring the same `evidence_id` against the same session SHALL NOT
duplicate the reference (delegates to `WorkflowOrchestrator`'s own
dedup, IWC-001-governed). Failure: `session_not_found`,
`invalid_state_transition` (session already past evidence-declaration
stage), `invalid_request`.

### 5.3 `decision-session select` (added by Phase 145G.2, closing F-145G.1-1)

**IWPC-REQ-192.** Purpose: record a human decision selection against a
session in `EvidenceReady` or `AwaitingDecision`, transitioning it to
`DecisionSelected`. Required: `<session-id>`, `--option-id` (the selected
option), one or more `--options-presented` (the full closed option set
shown to the human; MUST include `--option-id`'s value; no duplicates),
`--template-version` (the Decision Template version the presented options
were drawn from — see the compatibility note below), `--as-identity`
(Phase 145G.3, §34: identity-bound resumption, IWC-REQ-022/151;
supersedes IWPC-REQ-195's original "no separate identity flag" text
below). Optional:
`--rationale`, `--conditions`. Accepted input source: CLI arguments only.
Non-interactive; no prompt mode (mirrors IWPC-REQ-015/020's identical
discipline). Output: resulting state (`DecisionSelected`), selected
option, presented-option set, `schema_version`. State transition: a
session in `EvidenceReady` transitions `EvidenceReady` → `AwaitingDecision`
→ `DecisionSelected` in one invocation (both hops IWC-001-governed and
already legal per its transition table; combining them is this
requirement's own additive design choice, disclosed in the Phase 145G.2
canonical report, mirroring IWPC-REQ-016's own single-invocation
evidence-declaration precedent); a session already in `AwaitingDecision`
(e.g. after `clarify`) transitions directly `AwaitingDecision` →
`DecisionSelected`. Idempotency: non-idempotent, single-use — a session no
longer in `EvidenceReady`/`AwaitingDecision` (including one already
`DecisionSelected`) rejects a second `select` with
`invalid_state_transition`; there is no idempotent-replay path (mirrors
IWPC-REQ-021's confirm precedent, not IWPC-REQ-016's evidence precedent,
because a human decision selection is not safely re-derivable from
identical inputs the way a declared-evidence-reference set is). Identity:
the selecting principal is the session's own bound `owner_identity`
(IWC-REQ-018/052/063); no separate identity flag is defined (mirrors
IWPC-REQ-020/021's own no-separate-identity-flag convention for
`confirm`). Option-presentation binding: `--options-presented` is
caller-declared (no Decision Template resolver exists in this
implementation to derive it independently, disclosed judgment call
mirroring IWPC-REQ-016's own caller-declared-evidence precedent); `select`
MUST reject a `--option-id` that is not a member of the declared
`--options-presented` set. Failure: `session_not_found`,
`invalid_state_transition` (wrong precondition state, or option-set
membership violation), `invalid_request` (empty/malformed/duplicate
input). Exit codes: §9.

**IWPC-REQ-193.** `select` SHALL be single-use per session: once a session
leaves `EvidenceReady`/`AwaitingDecision` for any reason (including into
`DecisionSelected` itself), no subsequent `select` invocation against the
same session SHALL succeed, whether the resupplied inputs are identical
to or differ from the original call; each SHALL fail with
`invalid_state_transition`.

**IWPC-REQ-194.** The selected option (`--option-id`) SHALL be validated
against the exact `--options-presented` set supplied in the same
invocation; a selection outside that set SHALL be rejected
deterministically and SHALL NOT be silently substituted, defaulted, or
inferred.

**IWPC-REQ-195 (superseded in part by Phase 145G.3, §34).** Original v1.2
text: "`select` accepts no identity input distinct from the session's own
bound `owner_identity`." Phase 145G.3's independent verification
(145G.2V) found this text, while correctly stating the selecting
principal is never *inferred* from ambient state, had come to be relied
upon as if it also meant the binding was *enforced* — no code path
anywhere compared any claim to `owner_identity` at all (F-145G.2V-1).
Corrected text: `select` (like every other mutating `decision-session`
command, §34) now accepts exactly one explicit identity input,
`--as-identity`, structurally validated by the CLI and compared for
exact equality against the session's own bound `owner_identity` by
`SessionApplicationService`; the selecting principal remains never
*inferred* from the OS user, Git config, agent ID, lifecycle lock owner,
an undeclared environment variable, Telegram configuration, or the
current shell user (IWC-REQ-018's own prohibition, restated here as a
CLI-layer obligation, unchanged by this correction).

**IWPC-REQ-196.** Combining the `EvidenceReady` → `AwaitingDecision` and
`AwaitingDecision` → `DecisionSelected` hops within a single `select`
invocation when the session starts in `EvidenceReady` is this
requirement's own additive design choice (not a narrowing of any existing
requirement): no orchestration-sequencing stage governs either hop
distinctly (Phase 145G.1's eight fixed orchestration stages have no
"option presentation" or "decision selection" stage), and no other
command in this contract's frozen §5 command surface could reach
`AwaitingDecision` from `EvidenceReady` without it. A session that reaches
`AwaitingDecision` by a different path (e.g. via `clarify`) is accepted by
`select` directly, performing only the second hop.

### 5.4 `decision-session clarify`

**IWPC-REQ-017.** Purpose: record a clarification question/answer pair
against a session in `AwaitingClarification`. Required: `<session-id>`,
`--question`, `--answer`, `--as-identity` (Phase 145G.3, §34). Output: updated clarification-ref list,
resulting state. State transition: `AwaitingClarification` →
`AwaitingDecision` (IWC-001-governed exact transition). Idempotency:
non-idempotent but replay-protected — a second `clarify` call for a
session no longer in `AwaitingClarification` SHALL fail with
`invalid_state_transition` rather than silently re-recording. Failure:
`session_not_found`, `invalid_state_transition`, `invalid_request`.

### 5.5 `decision-session preview`

**IWPC-REQ-018.** Purpose: render the exact, unconditional, unsuppressible
Preview content and Preview Digest for a session in `DecisionSelected` or
later, per IWC-REQ-112. Required: `<session-id>`, `--as-identity` (Phase
145G.3, §34). No flag on this or any
other command MAY suppress or abbreviate Preview content (IWC-REQ-112,
restated here as a CLI-layer obligation). Output: `preview_id`,
`preview_digest`, full rendered content (session state is not part of
`preview`'s own output contract — see §8). State transition: IWC-001's
own state table defines `AwaitingConfirmation` as "Preview generated,
awaiting Confirmation" — the first successful Preview construction for a
session in `DecisionSelected` SHALL therefore transition it
`DecisionSelected` → `AwaitingConfirmation` (repair, Phase 145G.2
re-derivation finding: this clause was previously stated as "no
transition" in error, contradicting IWC-001's own already-frozen state
table; see §33). Every subsequent `preview` call against a session already
`AwaitingConfirmation` or later performs no further transition (preview IS
naturally idempotent, IWPC-REQ-019: re-running it against an unchanged
session SHALL deterministically reproduce the same digest, transition or
no transition). Idempotency: naturally idempotent. Failure:
`session_not_found`, `invalid_state_transition` (session not yet
decision-selected), `artifact_stale` (never applicable here; preview
always re-renders live).

**IWPC-REQ-019.** Preview rendering SHALL be naturally idempotent: given
an unchanged session state, repeated `preview` invocations SHALL produce
byte-identical rendered content and an identical `preview_digest`.

### 5.6 `decision-session confirm`

**IWPC-REQ-020.** Purpose: perform Confirmation. Required:
`<session-id>`, `--preview-digest` (must equal the session's current live
preview digest — mismatch is `confirmation_conflict`, §19), `--statement`
(the confirmer's rationale/confirmation text, non-empty), `--as-identity`
(Phase 145G.3, §34). Mutually
exclusive: none. Interactive behavior: none defined by v1.0 (no prompt
mode; `--statement` is the sole channel, per §6's sensitive-channel
discipline — see IWPC-REQ-039 on why this is acceptable here specifically
because a confirmation statement is not authority-bearing the way an
`AuthorizationEvent` is). Output: `confirmation_id`,
`confirmation_response_id`, resulting state `Confirmed`. State
transition: `AwaitingConfirmation` → `Confirmed`. Idempotency:
non-idempotent, single-use (IWPC-REQ-021) — a session already `Confirmed`
rejects a second `confirm` with `confirmation_conflict`, it does not
silently reconfirm and does not create a second Confirmation record.
Failure: `session_not_found`, `invalid_state_transition`,
`confirmation_conflict` (digest mismatch or already-confirmed),
`invalid_request`.

**IWPC-REQ-021.** Confirmation SHALL be single-use per session. Once a
session reaches `Confirmed`, no subsequent `confirm` invocation against
the same session SHALL succeed or create a second Confirmation record;
each SHALL fail with `confirmation_conflict`.

### 5.7 `decision-session status`

**IWPC-REQ-022.** Purpose: read-only inspection of a session's current
state, evidence/clarification/audit ref counts, and (once confirmed)
whether a pending readiness package exists for it. Required:
`<session-id>`. Read-only; mutates nothing. Idempotency: naturally
idempotent. Failure: `session_not_found`. Deliberately exempt from Phase
145G.3's `--as-identity` requirement (§34): IWC-REQ-022/151 govern
*resumption* of a session's workflow, not read-only observation of its
already-persisted, non-secret state.

### 5.8 `decision-session readiness`

**IWPC-REQ-023.** Purpose: read-only inspection of the pending-readiness
package bound to a confirmed session — its `package_id`, digest, creation
time, and consumption status (pending / consumed / none-yet-created).
Required: `<session-id>`, `--as-identity` (Phase 145G.3, §34: `readiness`
continues the session's workflow toward publication and is treated as
resumption, unlike `status`, even though it constructs no new `Session`
state itself). Idempotency: naturally idempotent, but identity is
re-enforced on every invocation, including one that hits the
already-constructed-package idempotent path (§34). Failure:
`session_not_found`, `readiness_incomplete` (session not yet
confirmed, or `PublicationHandoff.build_package` has not yet been
invoked — see IWPC-REQ-024 on when construction happens).

**IWPC-REQ-024.** `decision-session readiness` SHALL, on its first
invocation against a `Confirmed` session with no existing pending
package, construct the `PublicationReadinessPackage` via
`PublicationHandoff.build_package` and persist it to the Pending-Readiness
Store (§13) before reporting it; subsequent invocations SHALL report the
already-persisted package unchanged (naturally idempotent after first
construction — construction itself is idempotent by key, keyed on
`session_id`: a second construction attempt for a session that already
has a persisted pending package SHALL return the existing package,
never rebuild it).

### 5.9 `decision-session cancel`

**IWPC-REQ-025.** Purpose: terminate a session before Confirmation.
Required: `<session-id>`, `--reason`, `--as-identity` (Phase 145G.3, §34).
State transition: any
non-terminal state → `Cancelled`. Idempotency: idempotent by key — a
second `cancel` against an already-`Cancelled` session SHALL report
success with the existing cancellation, not fail (cancellation has no
downstream irreversible effect to protect against duplication); identity
is nonetheless re-enforced ahead of this idempotent path, so a mismatched
identity is rejected even against an already-`Cancelled` session (§34).
Failure:
`session_not_found`, `invalid_state_transition` (session already
`Confirmed` — a confirmed session cannot be cancelled through this
command; per IWC-001, only `Expired` is available thereafter and it is
not caller-invocable).

## 6. Command Contract — Publication

**IWPC-REQ-026.** The publication surface is frozen as an addition to the
existing `governance-record` family:

```
pcae governance-record publish <package-id> --operator-id <id> [--json]
```

**IWPC-REQ-027.** Required: `<package-id>` (references a persisted
pending package in the Pending-Readiness Store, §13), `--operator-id`
(non-empty, no default). No `--force`, `--assume-authorized`, or any
equivalent bypass flag SHALL exist (PEC-REQ-092, restated).

**IWPC-REQ-028.** Optional output controls: `--json` only (§7); no
`--quiet` is defined for v1.0.

**IWPC-REQ-029.** Interactive restriction: no interactive confirmation
prompt SHALL be added to `publish` — the human act this command performs
IS the authorizing act itself (PEC-REQ-034); adding a second, CLI-side
confirmation step would create a sixth undefined state not owned by
IWC-001 or PEC-001, violating IWPC-REQ-012's separation invariant.

**IWPC-REQ-030.** Non-interactive restriction: `publish` accepts only
complete, explicit CLI arguments; it SHALL NOT read `--operator-id` from
an environment variable, a config file default, or any implicit source
(§6, sensitive-channel discipline).

**IWPC-REQ-031.** Publication-result output: the CLI SHALL render
`PublicationCoordinator.execute`'s `PublicationExecutionResult` fields
verbatim (§7), adding no interpretation, inference, or additional status
beyond what the Coordinator itself returned.

**IWPC-REQ-032.** Replay behavior: a `publish` invocation naming a
`package_id` already successfully published SHALL return
`publication_already_completed` (exit class §8), reporting the existing
`record_id`, never re-executing or re-authorizing.

**IWPC-REQ-033.** Retry behavior: a `publish` invocation naming a
`package_id` whose prior attempt failed non-terminally (e.g.
`persistence_failure`) MAY be retried with a fresh `AuthorizationEvent`
(new `--operator-id` invocation, new `invoked_at`); the CLI SHALL NOT
cache or reuse a prior failed attempt's `AuthorizationEvent`.

**IWPC-REQ-034.** Failure behavior: `publish` SHALL map every
`PublicationCoordinator` exception to the closed error taxonomy in §19,
with no uncaught exception permitted to reach the caller as a raw
traceback in `--json` mode.

**IWPC-REQ-035.** Publication remains a distinct human act from
Confirmation: `publish` SHALL NOT accept, consume, or be satisfied by a
`--statement` or any Confirmation-shaped input; its sole authority input
is the `AuthorizationEvent` constructed from `--operator-id` (§17).

## 7. Input Contract

**IWPC-REQ-036.** Allowed input channels for every command in §5 and §6
are: explicit CLI arguments, and (for `decision-session confirm` and
`governance-record publish` only) a JSON request file via `--request-file
<path>` as an alternative to individual flags, MAY be added by a future
additive revision but is NOT part of v1.0 — v1.0 defines CLI arguments as
the sole input channel for every command.

**IWPC-REQ-037.** Standard input SHALL NOT be read by any command in this
contract for v1.0 (no command pipes secrets or structured input via
stdin); this SHALL be revisited only as an additive revision (§30) if a
future automation use case demonstrates a concrete need.

**IWPC-REQ-038.** A session-artifact reference (`<session-id>`) and a
readiness-package-artifact reference (`<package-id>`) are the only
artifact-reference input channels; both are positional CLI arguments,
never file paths — the CLI resolves them against the Session Repository
(§12) / Pending-Readiness Store (§13) internally, never accepting a raw
filesystem path from the caller for either (path-traversal prevention,
§23).

**IWPC-REQ-039.** Sensitive or authority-bearing values (`--operator-id`)
SHOULD NOT be accepted through a channel with unavoidable persistence in
shell history when an alternative exists; because v1.0 defines no
alternative channel (IWPC-REQ-037), `--operator-id` is accepted via CLI
argument as the only available channel, with the shell-history exposure
risk explicitly disclosed (§23) rather than silently accepted. This is
distinguished from a Confirmation `--statement`, which is not itself an
authority credential (IWPC-REQ-020's commentary) and carries materially
lower exposure risk.

**IWPC-REQ-040.** Precedence when more than one input channel is
supplied: not applicable to v1.0 (only one channel — CLI arguments —
exists per command); a future revision defining `--request-file`
alongside individual flags MUST define explicit precedence at that time
and MUST fail closed (IWPC-REQ-040 is retained as a placeholder
obligation for that future revision, not an open v1.0 gap, since v1.0 has
no ambiguity to resolve).

**IWPC-REQ-041.** Ambiguous input SHALL fail closed: argparse-level
mutual-exclusion or missing-required-argument errors are `invalid_request`
(exit class §8), never silently resolved by a default.

## 8. Output Contract

**IWPC-REQ-042.** Every command SHALL support two output modes: default
human-readable text, and `--json` machine-readable output. No `--quiet`
mode is defined for v1.0.

**IWPC-REQ-043.** Human-readable output MAY evolve cosmetically (field
order, wording, column widths) between patch-level implementation
changes without a contract revision, per PEC-001's and IWC-001's own
precedent for text-mode evolution.

**IWPC-REQ-044.** Machine-readable (`--json`) output MUST follow the
compatibility rules in §10: stable field names, an explicit
`schema_version` field on every payload, ISO-8601 UTC timestamps, and the
identifier vocabulary in §24 (Observability Contract).

**IWPC-REQ-045.** JSON output SHALL be rendered
`json.dumps(payload, indent=2, sort_keys=True, default=str)`, matching
`src/pcae/commands/governance_record.py`'s existing precedent, so callers
scripting against this surface get the same deterministic key ordering
and encoding as every existing `--json`-capable PCAE command.

**IWPC-REQ-046.** Status vocabulary in JSON payloads is a closed set:
`"success"`, `"error"`. No third value (e.g. `"partial"`) is defined for
v1.0; a partially-completed operation is always reported as `"error"`
with a specific `error_type` (§19), never as an ambiguous third status.

**IWPC-REQ-047.** Warning vocabulary: a successful response MAY carry an
optional `"warnings"` array of `{code, message}` objects (e.g. a
`readiness` inspection warning that the underlying preview digest has
since drifted, without that drift itself being a hard failure at the
`status`/`readiness` read-only commands). No command in §5/§6 requires
warnings for v1.0; the field is reserved, additive-only.

**IWPC-REQ-048.** Error-envelope vocabulary is frozen exactly:
`{"status": "error", "error_type": "<snake_case>", "message": "<string>", "session_id": "<string, nullable>", "package_id": "<string, nullable>"}`
— matching Phase 145A §7.4 verbatim. No additional required field.
Additional optional fields (e.g. `"record_id"` on a
`publication_already_completed` error) MAY appear per §19's per-error
field list.

**IWPC-REQ-049.** No output governed by this contract SHALL claim
authority that the underlying subsystem (Interactive Workflow or
Publication) did not itself establish — e.g., a `publish` success
response SHALL report exactly the `record_id`/`success` fields
`PublicationExecutionResult` returned, never an inferred or
CLI-synthesized authority statement.

## 9. Exit-Code Contract

**IWPC-REQ-050.** Exit codes are frozen exactly per Phase 145A §6.3/§12,
verified against the actually-implemented exception classes in
`governance/publication/errors.py` and the Interactive Workflow state
machine's own transition-rejection path:

| Code | Class | Meaning |
|---|---|---|
| 0 | success | Command completed successfully. |
| 1 | generic_domain_failure | A handled domain failure not covered by codes 2–5 (e.g. `session_not_found`, `invalid_request`, `invalid_package`, `internal_error`). |
| 2 | invalid_state_transition | Out-of-sequence stage invocation (`_require_next`-style rejection, or argparse's own usage-error convention for malformed invocation shape). |
| 3 | confirmation_conflict | Confirmation binding failure — digest mismatch or already-confirmed session. |
| 4 | authorization_replay | Replay: an already-consumed `AuthorizationEvent`/already-published `package_id` (`AuthorizationReplayError`, `publication_already_completed`). |
| 5 | stale_authorization | A `StaleAuthorizationError` — the authorization's freshness window has elapsed per PEC-001 §6. |
| 6 | identity_binding_mismatch | (Phase 145G.3, §34) A resumed-session command's `--as-identity` claim does not equal the session's bound `owner_identity` (IWC-REQ-022/151). |

**IWPC-REQ-051 (amended by Phase 145G.3, §34).** Original v1.2 text: "No
exit code beyond 0–5 is defined for v1.0." Phase 145G.3 adds exit code 6
(`identity_binding_mismatch`) as a dedicated, additive exit class,
distinct from every existing one (not reused as `authorization_invalid`/1,
which already carries an established, different meaning). A failure not
cleanly mapping to classes 1–6 (an unexpected internal exception) MUST
still exit `1` (`internal_error`), never a further ad hoc code — avoiding
a unique exit code per low-level exception, per this phase's own
governing prompt (unchanged discipline, now bounded at 0–6).

**IWPC-REQ-052.** Every `error_type` value in the closed taxonomy (§19)
MUST map to exactly one exit-code class from IWPC-REQ-050's table; the
mapping is part of this contract's frozen text, not left to
implementation discretion.

## 10. Transport Contract

**IWPC-REQ-053.** Transport request/response objects SHALL be envelopes
around, or direct use of, existing serializable types wherever one
already exists — preferring reuse over duplication, per this phase's own
governing prompt. Concretely:

- `DecisionSessionCreateRequest` — new, thin: `{template_ref, subject_ref,
  owner_id}`. `DecisionSessionCreateResponse` — envelope around
  `Session.to_payload()` plus `{status, schema_version}`.
- `DecisionSessionInspectRequest` — new, thin: `{session_id}`.
  `DecisionSessionInspectResponse` — envelope around
  `Session`+`OrchestrationState`'s existing `to_payload()` output.
- `PreviewRequest` — `{session_id}`. `PreviewResponse` — direct use of
  IWC-001's existing `Preview` serializable shape (`preview_id`,
  `preview_digest`, rendered content), no new schema.
- `ConfirmationRequest` — `{session_id, preview_digest, statement}`.
  `ConfirmationResponse` — direct use of IWC-001's existing Confirmation
  response shape (`confirmation_id`, `confirmation_response_id`,
  resulting state).
- `ReadinessRequest` — `{session_id}`. `ReadinessResponse` — envelope
  around `PublicationReadinessPackage`'s own fields (§3, §16), never a
  duplicate schema.
- `PublicationRequest` — `{package_id, operator_id}`, the exact
  constructor input `PublicationCoordinator.authorize` already accepts.
  `PublicationResponse` — direct use of the existing
  `PublicationExecutionResult` dataclass fields, unchanged.
- `ErrorResponse` — the envelope frozen at IWPC-REQ-048.

**IWPC-REQ-054.** No transport object SHALL duplicate an existing
authoritative schema. Where an existing dataclass's `to_payload()`/
serialization method already produces the needed shape, the transport
response IS that output, at most wrapped in `{status, schema_version,
...}`, never re-declared field-by-field in a parallel schema.

**IWPC-REQ-055.** For every transport object: required fields are exactly
those listed in IWPC-REQ-053's definitions; optional fields are limited
to `warnings` (§8) and error-specific optional fields (§19); every field's
semantics are inherited unchanged from the wrapped existing type; every
response carries a `schema_version` field (§11); identifier fields are
exactly `session_id`/`package_id`/`record_id` (§3, IWPC-REQ-005);
provenance fields are inherited from the wrapped type (e.g.
`PublicationReadinessPackage.built_at`), never newly invented at the
transport layer; validation ownership is: request-shape validation
(required/well-formed) belongs to the transport adapter (CLI argparse
layer), and all semantic validation (does this template exist, is this
session in the right state) belongs to the wrapped subsystem
(Interactive Workflow or Publication), never duplicated in the adapter.

**IWPC-REQ-056.** Unknown-field behavior: because v1.0 has no
`--request-file`/JSON-body input channel (IWPC-REQ-037), unknown-field
handling applies only to the (future, hypothetical) JSON request-file
channel and is deferred to that future revision; for v1.0's CLI-argument
input, argparse's own unrecognized-argument behavior (hard failure,
`invalid_request`) is the entire unknown-field story.

**IWPC-REQ-057.** Canonical serialization: every JSON transport response
uses the same `json.dumps(..., sort_keys=True, default=str)` convention
as IWPC-REQ-045; canonical serialization for persisted artifacts (§12,
§13) uses the same convention for reproducible digesting.

## 11. Transport Versioning

**IWPC-REQ-058.** Every transport response SHALL carry a
`schema_version` field. For v1.0, the value SHALL be the constant string
`"iwpc-transport/1.0"` for every new IWPC-owned envelope field set
(IWPC-REQ-053's thin new request/response wrappers); where a response is
a direct pass-through of an existing dataclass's own `schema_version`
(e.g. `PublicationExecutionResult`, `PublicationReadinessPackage`), that
existing field is preserved unchanged and is not overwritten by
`"iwpc-transport/1.0"`.

**IWPC-REQ-059.** Additive-field compatibility: a future minor revision
of IWPC-001 MAY add optional fields to any response without incrementing
`schema_version`'s major component; existing callers parsing only
documented required fields SHALL continue to function unchanged.

**IWPC-REQ-060.** Unsupported-major-version behavior: not yet reachable
in v1.0 (no prior version exists); this requirement is retained as a
frozen placeholder obligation — once a `"iwpc-transport/2.0"` exists, a
v1.0-only client encountering it MUST fail closed with
`unsupported_version` (§19) rather than attempt best-effort parsing.

**IWPC-REQ-061.** Deprecation policy: no field or command may be removed
without first appearing in a superseding contract revision's explicit
deprecation list for at least one full revision cycle, per §26
Compatibility Contract.

**IWPC-REQ-062.** A transport version change SHALL NOT silently change
governance semantics — e.g., a future `"iwpc-transport/1.1"` adding an
optional field to `PublicationResponse` SHALL NOT thereby change
`PublicationCoordinator`'s own authorization or execution semantics,
which remain exclusively PEC-001's to define.

## 12. Decision-Session State Contract

**IWPC-REQ-063.** The CLI/transport layer SHALL NOT define its own
session state vocabulary. It reports, verbatim, the state vocabulary
IWC-001 §4.4 already defines: `Created`, `EvidenceReady`,
`AwaitingDecision`, `AwaitingClarification`, `DecisionSelected`,
`AwaitingConfirmation`, `Confirmed`, plus terminal `Cancelled`,
`Expired`, `Abandoned` — ten states total, matching IWC-001's own
ten-state model exactly, with no additional state (e.g. no CLI-invented
`"readiness_created"` session state — readiness-package existence is
tracked in the Pending-Readiness Store, §13, as a fact about that store,
never as an eleventh session state).

**IWPC-REQ-064.** For each transition a §5 command may trigger: the
initiating command, preconditions, and resulting state are exactly as
enumerated per-command in §5.1–§5.9; the CLI/transport layer performs no
transition IWC-001 itself does not already define, and rejects (fail
closed, `invalid_state_transition`) any command invoked against a session
not in the precondition state that command's §5 subsection names.

**IWPC-REQ-065.** The Session Repository (§12 heading name is reused
deliberately per this phase's governing prompt's own section title; the
store itself is specified in §13 below of this document — see
IWPC-REQ-066) MUST NOT become a governance authority: persisting a
session or reporting its state through `status`/`readiness` confers no
authority and is not itself evidence of confirmation or authorization
beyond what IWC-001/PEC-001 already establish.

## 13. SessionRepository Contract

**IWPC-REQ-066.** This phase freezes the contract for the first concrete
filesystem implementation of the existing `SessionRepository` ABC
(`interactive_workflow/persistence/repository.py`); it does not modify
the ABC itself. The interface surface a v1.0 implementation MUST provide
is exactly the ABC's existing abstract methods: `create`, `load`,
`persist` (used as the compare-and-set point, §21), `exists`,
`list_session_ids`. No additional method (`delete`,
`cleanup`) is justified for v1.0 — sessions are never deleted, only
transitioned to a terminal state and left in place for audit purposes.

**IWPC-REQ-067.** Ownership: the Session Repository implementation is
owned by the CLI/transport layer (this contract), not by
`SessionCoordinator` (which only depends on the ABC, per IWC-001's
existing dependency direction).

**IWPC-REQ-068.** Storage location: `.pcae/decision-sessions/<session_id>.json`,
one file per session, `session_id` used verbatim as the filename stem
(no additional hashing/sharding for v1.0's expected volume).

**IWPC-REQ-069.** File naming: exactly `<session_id>.json`, where
`session_id` is the `CDS-<uuid4>` string IWC-001 already produces; no
other character transformation is applied.

**IWPC-REQ-070.** Directory layout: a single flat directory
`.pcae/decision-sessions/`; no subdirectory nesting by date or state for
v1.0.

**IWPC-REQ-071.** Permissions: files SHALL be created with the process's
default umask-governed permissions (no special restrictive mode is
mandated for v1.0, since sessions carry no authority token per
IWPC-REQ-088 — this is a disclosed, deliberate non-hardening, consistent
with PEC-001's own Publication Readiness Package's authority-neutral
posture).

**IWPC-REQ-072.** Atomic write: `create`/`persist` MUST use the
`tempfile.mkstemp` (same directory) → write → `flush` → `os.fsync` →
`os.replace` pattern already used by `PublicationRecordStore._write_atomic_json`
and `cltr/persistence.py`'s `_write_atomic` (this repository's strongest
existing precedent for a durable write), with a `finally`-block cleanup
of any leftover temp file.

**IWPC-REQ-073.** Locking/concurrency: no file-locking primitive
(`fcntl`, `portalocker`) is required or used, consistent with every
sibling store in this repository (§21 Concurrency Contract addresses the
resulting race explicitly rather than silently, per this phase's own
governing prompt).

**IWPC-REQ-074.** Schema version: every persisted session file MUST carry
a `schema_version` field; v1.0's value is
`"decision-session-store/1.0"`, independent of and in addition to
whatever `schema_version` `Session`/`OrchestrationState`'s own
`to_payload()` output carries.

**IWPC-REQ-075.** Corruption behavior: on `load`, a file that fails JSON
parsing or `schema_version` validation MUST raise a dedicated
`SessionStoreCorruptError` (a new exception this contract names for the
future implementation to define), mapped to `persistence_corrupt` (§19);
the implementation MUST NOT attempt partial/best-effort recovery of a
corrupt file.

**IWPC-REQ-076.** Stale-session behavior: `load` performs no
staleness check itself (IWC-001 governs `Expired` transition semantics,
not this store); a caller-visible staleness fact, if any, is reported by
`status`/`readiness` reading the loaded session's own IWC-001-governed
state, never independently computed by the store.

**IWPC-REQ-077.** Cleanup behavior: no automatic cleanup/deletion of
session files is performed by v1.0; sessions accumulate as durable audit
artifacts. A future revision MAY add a bounded retention policy under
§30's additive-evolution rule.

## 14. Pending-Readiness Store Contract

**IWPC-REQ-078.** Purpose: durable, repository-local persistence of a
constructed `PublicationReadinessPackage` between `decision-session
readiness`'s construction (IWPC-REQ-024) and a later
`governance-record publish` invocation, spanning process boundaries and
potentially significant elapsed time.

**IWPC-REQ-079.** Authoritative status: the Pending-Readiness Store is
explicitly non-authoritative — it holds a copy of an already-immutable
package; PEC-001's own `PublicationRecordStore` (`records/`, `published/`,
`attempts/`) remains the sole authoritative record of what was actually
published (IWPC-REQ-010 restated at the storage layer).

**IWPC-REQ-080.** Package identity: `package_id`, assigned by
`PublicationHandoff.build_package` (IWC-001/144F-governed), used verbatim
as the storage key; this store assigns no second identifier.

**IWPC-REQ-081.** Package digest: the store persists
`PublicationReadinessPackage.preview_digest` and a whole-package content
digest (SHA-256 over the canonical serialization, IWPC-REQ-057) computed
at write time, so a later `publish` invocation can detect tampering
(§15 Artifact Binding) independent of re-trusting the filesystem alone.

**IWPC-REQ-082.** Session binding: every persisted package carries its
originating `session_id`; `decision-session readiness` looks up by
`session_id` (one pending package per session, enforced at construction,
IWPC-REQ-024), while `governance-record publish` looks up by
`package_id` (the two lookup keys are deliberately different, matching
each command's own primary input).

**IWPC-REQ-083.** Confirmation binding: the persisted package embeds
`confirmation_request_id`/`confirmation_response_id`/
`confirmation_statement`/`confirmation_timestamp` verbatim (already part
of the widened `PublicationReadinessPackage`, IWC-001 §26); the store adds
no separate confirmation-binding field.

**IWPC-REQ-084.** Creation time: `built_at` (already a package field) is
preserved verbatim; the store additionally records its own
`persisted_at` (store-write time), which MAY differ from `built_at` by
at most the construction-to-persistence gap within a single
`decision-session readiness` invocation (expected to be sub-second; no
enforced maximum for v1.0).

**IWPC-REQ-085.** Expiry/staleness policy: the store itself defines no
time-based expiry (Phase 145A §11.2, ratified: relies on IWC-001's own
`Expired` session state, not a second, redundant TTL at the store layer).
A `publish` invocation against a package whose originating session has
since reached `Expired` MUST fail with `artifact_stale` (§19), computed
by checking the bound session's live state via the Session Repository,
not by any store-local clock.

**IWPC-REQ-086.** Authorization binding: the store persists no
authorization-related field before `publish` runs (an unconsumed pending
package has no `AuthorizationEvent` yet, by definition); once `publish`
succeeds, the store records the resulting `record_id` and
`publication_attempt_id` (metadata only, added after the fact, never
mutating the underlying `PublicationReadinessPackage` object itself,
IWPC-REQ-089).

**IWPC-REQ-087.** Publication-attempt binding: every `publish` invocation
against a given `package_id`, successful or not, MUST append an
attempt-linkage record (attempt_id, outcome, timestamp) to the store's
per-package metadata (distinct from, and never substituting for, PEC-001's
own `PublicationRecordStore.attempts/` audit — this is a lightweight
back-reference only, so `decision-session readiness`/`status` can report
"already attempted" without reading into PEC-001's storage internals).

**IWPC-REQ-088.** Successful-publication disposition: on a successful
`publish`, the package file MUST be moved (`os.replace`, not deleted) from
`.pcae/decision-sessions/pending-packages/<package_id>.json` to
`.pcae/decision-sessions/pending-packages/consumed/<package_id>.json`, so
a subsequent duplicate `publish` invocation still finds the package
(reporting `publication_already_completed`, IWPC-REQ-032) rather than
`artifact_not_found`.

**IWPC-REQ-089.** Failed-publication disposition: on a failed `publish`,
the package file remains in place, unmoved, in
`pending-packages/` (not moved to `consumed/`), so a retry (IWPC-REQ-033)
can find it; only the attempt-linkage metadata (IWPC-REQ-087) is updated.

**IWPC-REQ-090.** Replay behavior at the store layer: reading a
`consumed/` package (e.g. via a future inspection command, or the replay
path of `publish` itself, IWPC-REQ-032) returns the exact,
unmodified persisted package — the store never reconstructs or
re-derives package content from session fields after the fact
(IWPC-REQ-091 restated at the store layer).

**IWPC-REQ-091.** The store MUST preserve the exact immutable
`PublicationReadinessPackage` it was given at construction time; it MUST
NOT reconstruct the package from session fields on `load`, and it MUST
NOT mutate any package-content field after creation — only the
store-level metadata wrapper (attempt linkage, consumption disposition)
may be updated in place.

**IWPC-REQ-092.** Cleanup behavior: no automatic deletion of `consumed/`
packages is performed by v1.0; they accumulate as durable audit
artifacts, mirroring the Session Repository's own no-cleanup posture
(IWPC-REQ-077).

## 15. Artifact Binding

**IWPC-REQ-093.** The complete required binding chain is: decision
session → preview → confirmation → PublicationReadinessPackage →
AuthorizationEvent → publication attempt → publication result. Each link
MUST be verified by identifier and, where a content digest exists, by
digest, before the next stage proceeds.

**IWPC-REQ-094.** session → preview: preview is generated live from the
session's current state; no separate binding identifier is needed beyond
`session_id` itself (preview is not a persisted artifact prior to
confirmation).

**IWPC-REQ-095.** preview → confirmation: `decision-session confirm`
MUST verify its `--preview-digest` argument equals the session's current
live preview digest (recomputed at confirm time, not read from a stale
cache); mismatch fails `confirmation_conflict` (IWPC-REQ-020).

**IWPC-REQ-096.** confirmation → PublicationReadinessPackage:
`PublicationHandoff.build_package` (IWC-001/144F-governed) verifies
`confirmation_request_id`/`confirmation_response_id` cross-references
before constructing the package, raising
`PublicationHandoffIncompleteError` on any mismatch (existing behavior,
unchanged, mapped to `readiness_incomplete`, §19).

**IWPC-REQ-097.** PublicationReadinessPackage → AuthorizationEvent:
`PublicationCoordinator.authorize` binds the event to exactly one
`package_id` (PEC-REQ-040, restated); `governance-record publish`'s
`<package-id>` positional argument is the sole source of this binding —
the CLI never substitutes a session-derived or cached package id.

**IWPC-REQ-098.** AuthorizationEvent → publication attempt:
`PublicationCoordinator.execute`'s existing fixed ordering (replay check
→ package validation → authorization applicability → authorization
freshness → atomic write → idempotency-marker commit → attempt audit,
PEC-REQ-051) is invoked unchanged; the CLI adds no additional ordering
step and does not reorder or skip any PEC-001-governed step.

**IWPC-REQ-099.** publication attempt → publication result: the CLI
renders `PublicationExecutionResult` verbatim (IWPC-REQ-031); no stage
may accept or synthesize a result shape merely similar to the one
`PublicationCoordinator.execute` actually returned.

**IWPC-REQ-100.** Mismatch at any link in the chain MUST fail closed with
a specific, named error from the §19 taxonomy — never silently
substitute a "close enough" artifact, and never proceed past a failed
binding check.

## 16. Confirmation Contract

**IWPC-REQ-101.** Confirmation binds to: decision-session identity,
decision subject (via the session's own bound subject-ref), selected
option (via the session's `DecisionSelected` state fields),
option-set identity (via the session's bound `template_ref`/version),
preview identity and digest (`preview_id`/`preview_digest`, verified per
IWPC-REQ-095), confirmer identity evidence (the session's bound owner/
confirmer identity, IWC-REQ-036/037), and confirmation timestamp
(`confirmation_timestamp`, server/process clock at the moment `confirm`
succeeds).

**IWPC-REQ-102.** Confirmation is single-use (IWPC-REQ-021); no flag or
mode reconfirms an already-`Confirmed` session — any such attempt is
`confirmation_conflict`.

**IWPC-REQ-103.** Changed input invalidates confirmation only in the
sense that IWC-001 already defines: a session cannot reach
`AwaitingConfirmation` a second time after `Confirmed` (terminal
one-way transition, IWC-001-governed); this contract adds no separate
invalidation mechanism at the CLI layer.

**IWPC-REQ-104.** Duplicate confirmation (identical arguments, same
session, same digest, repeated invocation after success) is handled
identically to any other post-`Confirmed` `confirm` call:
`confirmation_conflict`, not silently treated as a successful no-op —
because IWC-001 defines Confirmation as a single, non-repeatable act, not
an idempotent one.

**IWPC-REQ-105.** Confirmation mismatch (digest disagreement) is reported
via `confirmation_conflict` with a message distinguishing "digest
mismatch" from "already confirmed" in the human-readable text, while
using the same `error_type`/exit code for both in machine-readable output
(both are, structurally, the same class of binding failure).

**IWPC-REQ-106.** Confirmation does not authorize publication
(IWPC-REQ-012 restated); `confirm`'s success output MUST NOT include any
field suggesting publication readiness beyond the fact that
`decision-session readiness` may now be invoked.

## 17. Readiness-Package Contract

**IWPC-REQ-107.** Creation preconditions: session MUST be `Confirmed`; no
existing pending package for that `session_id` (IWPC-REQ-024's
idempotent-by-key construction).

**IWPC-REQ-108.** Immutable content requirements and field provenance:
every decision-content field
(`decision_subject, template_id, template_version, selected_option_id,
rationale_text, conditions_text, options_presented,
decision_maker_identity_evidence, preview_rendered_content,
confirmation_statement, confirmation_timestamp`) MUST derive exclusively
from the confirmed workflow state at the moment `build_package` runs;
none MAY be supplied, overridden, or backfilled by the CLI/transport
layer or by a later `publish` invocation.

**IWPC-REQ-109.** Package identifier: `package_id`, assigned once by
`PublicationHandoff.build_package`, never reassigned.

**IWPC-REQ-110.** Package digest: `preview_digest` (inherited) plus the
Pending-Readiness Store's own whole-package content digest
(IWPC-REQ-081); the CLI/transport layer computes the latter, never the
former (preview digest remains IWC-001's to compute).

**IWPC-REQ-111.** Serialization: via
`interactive_workflow/serialization/publication_handoff_schema.py`'s
existing `serialize`/`deserialize`, reused unchanged; the Pending-Readiness
Store's own store-level wrapper (IWPC-REQ-074-equivalent
`schema_version`, e.g. `"pending-readiness-store/1.0"`) wraps this output,
never replaces it.

**IWPC-REQ-112.** Persistence behavior: exactly as specified in §14.

**IWPC-REQ-113.** Replay behavior: a package already `consumed/` remains
inspectable (read-only) but is never reconstructed for a second `publish`
attempt to act on — a `publish` invocation naming a consumed package's
`package_id` MUST report `publication_already_completed`, reading the
consumed record for its `record_id`, never re-deriving a new one.

**IWPC-REQ-114.** Stale behavior: as specified at IWPC-REQ-085 (session
`Expired` since package construction → `artifact_stale` on `publish`);
no other staleness condition is defined for v1.0.

**IWPC-REQ-115.** All decision-content fields MUST derive from the
confirmed workflow state; none may be reconstructed later by the CLI or
by `PublicationCoordinator` — restates PEC-001 §8's existing "no
authority token, no publication decision, no CHGR identifier, no
execution state" prohibited-fields guarantee, extending it explicitly to
this contract's own store layer (the store MUST NOT add any of the
`_PROHIBITED_PACKAGE_FIELDS` PEC-001 already forbids, IWPC-REQ-124).

## 18. Authorization Input Contract

**IWPC-REQ-116.** `AuthorizationEvent` is supplied by constructing
`PublicationCoordinator.authorize(operator_id=<--operator-id>,
package_id=<package-id>, invoked_at=<process clock at invocation>)` —
the CLI performs no other construction path.

**IWPC-REQ-117.** Accepted serialization: none needed at the input side —
`--operator-id` and `<package-id>` are plain CLI arguments, not a
serialized event object; the event itself is a PEC-001-owned in-memory
dataclass until `PublicationRecordStore` persists it as part of
`execute`'s atomic write.

**IWPC-REQ-118.** Required identity evidence: `--operator-id`,
non-empty, structurally validated only (well-formed string; no format
beyond non-emptiness is enforced for v1.0).

**IWPC-REQ-119.** Required authority-basis claim: none is collected —
per IWPC-REQ-009/Phase 145A's finding, no `authority_basis_claimed` field
exists to populate; `build_publication_record` leaves it unpopulated, a
disclosed limitation (F-145A-4, §29), not remedied by this contract.

**IWPC-REQ-120.** Package binding: `<package-id>`, the CLI's own
positional argument, is the sole package-binding input (IWPC-REQ-097).

**IWPC-REQ-121.** Time/freshness evidence: `invoked_at`, set to the
process's wall-clock time at the moment `authorize` is called; freshness
evaluation itself (PEC-001 §6's freshness window) remains
`PublicationCoordinator`'s exclusive responsibility.

**IWPC-REQ-122.** Validation responsibility: the CLI validates only
structural completeness (non-empty `--operator-id`, resolvable
`package_id`); `PublicationCoordinator` validates authorization
applicability, freshness, and replay — the CLI never duplicates any of
PEC-001's own validation methods (`_validate_authorization_presence`,
`_check_replay`, `_validate_package`,
`_validate_authorization_applicability`,
`_validate_authorization_freshness`).

**IWPC-REQ-123.** Authority-evaluation responsibility: the CLI MUST NOT
decide whether `--operator-id`'s bearer is substantively authorized;
per IWPC-REQ-009/119, no existing contract assigns that responsibility to
anything in this repository, so this contract does not invent an owner
for it — it remains, as Phase 145A disclosed, an open gap outside this
contract's scope.

**IWPC-REQ-124.** No `--force`, `--assume-authorized`, or equivalent
bypass flag SHALL exist on `governance-record publish` or any other
command governed by this contract (restates IWPC-REQ-027).

## 19. Publication Invocation Contract

**IWPC-REQ-125.** Accepted inputs: exactly `package_id` (resolved via
the Pending-Readiness Store, IWPC-REQ-038) and `operator_id` (from
`--operator-id`); no other input is accepted by the publication CLI
adapter.

**IWPC-REQ-126.** Validation sequence: CLI-layer structural validation
(non-empty operator id, resolvable package id) first; then
`PublicationCoordinator.authorize`'s own validation sequence
(IWPC-REQ-122); then `PublicationCoordinator.execute`'s own fixed
ordering (IWPC-REQ-098).

**IWPC-REQ-127.** Authorization sequence: exactly
`PublicationCoordinator.authorize(...)`, unchanged, unwrapped by any
CLI-side retry-before-first-attempt logic.

**IWPC-REQ-128.** Publication sequence: exactly
`PublicationCoordinator.execute(package, event)`, unchanged.

**IWPC-REQ-129.** Result mapping: `PublicationExecutionResult.success →
exit 0`/`{"status":"success", ...verbatim result fields}`; failure →
mapped per §19's error taxonomy (this section) and §9's exit-code table.

**IWPC-REQ-130.** Failure mapping: every `PublicationCoordinator`
exception (`MissingAuthorizationError`, `InvalidAuthorizationError`,
`AuthorizationReplayError`, `StaleAuthorizationError`,
`InvalidPublicationPackageError`, `AtomicPublicationFailure`,
`PublicationStorageError`, `PublicationRollbackError`) maps 1:1 to a
closed `error_type` (table below), matching Phase 145A's own error-table
exactly.

**IWPC-REQ-131.** Retry mapping: as specified at IWPC-REQ-033.

**IWPC-REQ-132.** Replay mapping: as specified at IWPC-REQ-032.

**IWPC-REQ-133.** The adapter (`governance-record publish`'s command
function) SHALL NOT bypass or duplicate `PublicationCoordinator`'s logic,
and SHALL NOT write CHGR artifacts directly under any circumstance
(IWPC-REQ-010 restated at the adapter layer).

### 19.1 Error Taxonomy (closed set)

**IWPC-REQ-134.** The complete, closed `error_type` vocabulary, each
row's exit-code class from §9, retryability, and producing owner:

| `error_type` | Exit class | Retryable | Producing owner |
|---|---|---|---|
| `invalid_request` | 1 | yes (fix input, resubmit) | CLI adapter (argparse/structural validation) |
| `invalid_state_transition` | 2 | no (session must reach precondition state first) | Interactive Workflow (state machine) |
| `malformed_artifact` | 1 | no (artifact must be regenerated) | Session Repository / Pending-Readiness Store |
| `unsupported_version` | 1 | no | Transport layer (§11) |
| `artifact_not_found` | 1 | no | Session Repository / Pending-Readiness Store |
| `artifact_stale` | 5 | no (underlying session expired) | Pending-Readiness Store (IWPC-REQ-085) |
| `artifact_binding_mismatch` | 3 | no (must re-derive from live state) | Artifact Binding checks (§15) |
| `confirmation_required` | 2 | yes (perform confirm first) | Interactive Workflow |
| `confirmation_conflict` | 3 | no | Interactive Workflow / CLI (§16) |
| `authorization_required` | 1 (`missing_authorization`) | yes (supply `--operator-id`) | Publication Coordinator |
| `authorization_invalid` | 1 (`invalid_authorization`) | yes (correct input, resubmit) | Publication Coordinator |
| `authority_not_established` | 1 | n/a — disclosed gap, not an enforced check (IWPC-REQ-123) | not owned by any subsystem |
| `publication_conflict` | 1 | no | Publication Coordinator |
| `publication_already_completed` | 4 | no | Publication Coordinator / Pending-Readiness Store |
| `persistence_conflict` | 1 | yes (re-read, retry) | Session Repository / Pending-Readiness Store (§21) |
| `persistence_corrupt` | 1 | no (requires human review) | Session Repository / Pending-Readiness Store |
| `internal_error` | 1 | no (requires investigation) | any |
| `readiness_incomplete` | 1 | no | Interactive Workflow (`PublicationHandoffIncompleteError`) |
| `session_not_found` | 1 | no | Session Repository |
| `template_not_found` | 1 | no | Interactive Workflow |
| `subject_not_found` | 1 | no | Interactive Workflow |
| `stale_authorization` | 5 | yes (re-authorize with fresh event) | Publication Coordinator (`StaleAuthorizationError`) |
| `authorization_replay` | 4 | no | Publication Coordinator (`AuthorizationReplayError`) |
| `invalid_package` | 1 | no | Publication Coordinator (`InvalidPublicationPackageError`) |
| `domain_error` | 1 | context-dependent | catch-all, any |
| `identity_binding_mismatch` | 6 | no (a different, correct identity claim is required, not a retry) | Interactive Workflow (`SessionApplicationService._require_bound_identity`, Phase 145G.3, §34) |

**IWPC-REQ-135.** For each error, user-safe message requirements: the
`message` field MUST be a human-readable sentence containing no raw
Python exception text, no stack trace, and no filesystem path beyond a
`session_id`/`package_id` already known to the caller.

**IWPC-REQ-136.** Redaction requirements: no `AuthorizationEvent`,
identity-evidence value, or file content beyond identifiers named in
IWPC-REQ-048 SHALL appear in any error message.

**IWPC-REQ-137.** Low-level exception strings MUST NOT become the public
error contract — every raised exception is caught at the CLI adapter
boundary and re-expressed through the closed taxonomy above before
reaching output.

## 20. Idempotency Contract

**IWPC-REQ-138.** Classification per operation:

| Operation | Classification |
|---|---|
| `decision-session create` | non-idempotent |
| `decision-session evidence` | idempotent by key (per `evidence_id`) |
| `decision-session clarify` | non-idempotent, replay-protected |
| `decision-session preview` | naturally idempotent |
| `decision-session confirm` | non-idempotent, single-use |
| `decision-session status` / `readiness` | naturally idempotent (read-only) |
| `decision-session cancel` | idempotent by key |
| `decision-session readiness` (construction path) | idempotent by key (`session_id`) |
| `governance-record publish` (session creation) | non-idempotent |
| `governance-record publish` (submission) | idempotent by key (`package_id`), replay-protected |
| `governance-record publish` (retry after failure) | non-idempotent but replay-protected |
| result inspection (`status`/`readiness`) | naturally idempotent |

**IWPC-REQ-139.** Required idempotency keys: `evidence_id` (evidence
declaration), `session_id` (readiness construction), `package_id`
(publication submission/replay). No idempotency key is defined for
`create` (IWPC-REQ-015) or `clarify` (replay-protected via state, not a
key).

**IWPC-REQ-140.** Duplicate requests MUST return deterministic outcomes:
a repeated `evidence`/`readiness`/`publish` call with the same key
returns the same recorded outcome every time, never a randomized or
time-varying result.

## 21. Concurrency Contract

**IWPC-REQ-141.** Two writers updating one session: last-`persist`-wins
at the filesystem layer (no locking, IWPC-REQ-073); this is a disclosed,
accepted limitation (F-145A-5, §29), not silently ignored — a future
revision MAY add compare-and-set (e.g. an expected-version field checked
before `os.replace`) under §30's additive-evolution rule without breaking
v1.0 callers that don't supply it.

**IWPC-REQ-142.** Concurrent confirmations: two simultaneous `confirm`
invocations against the same session MAY both read `AwaitingConfirmation`
before either writes; the second writer's `persist` overwrites the
first's, but IWC-001's own state machine plus IWPC-REQ-020's digest check
means at most one Confirmation record is durably retained as the
session's current state — the loser's confirmation attempt is silently
overwritten, not duplicated. This repository-wide limitation is disclosed
(§21 exists specifically because the governing prompt required it
addressed, not silently deferred to "future work").

**IWPC-REQ-143.** Concurrent readiness creation: two simultaneous
`decision-session readiness` invocations against the same confirmed
session with no existing package MAY both call `build_package`; the
Pending-Readiness Store's write is last-write-wins (same limitation as
IWPC-REQ-141) — both constructed packages carry the same
confirmation-derived content (deterministic given identical input,
IWPC-REQ-108), so the practical impact is a discarded, but not divergent,
duplicate, not a governance-relevant race.

**IWPC-REQ-144.** Concurrent publication attempts: PEC-001's own
`os.O_CREAT | os.O_EXCL` idempotency marker (`commit_publication`)
already provides the one place in this entire chain with real mutual
exclusion — the second of two concurrent `publish` invocations against
the same `package_id` MUST receive `publication_already_completed` or
`authorization_replay` from the exclusive-create race, never a
double-published CHGR. This is the sole compare-and-set-equivalent
mechanism this contract relies on, and it is PEC-001's, not newly added
here.

**IWPC-REQ-145.** Cleanup racing with inspection: not applicable — v1.0
performs no automatic cleanup (IWPC-REQ-077, IWPC-REQ-092), so no
cleanup-vs-inspection race exists to resolve.

**IWPC-REQ-146.** Stale reads followed by writes: `decision-session
confirm`'s live-digest re-check (IWPC-REQ-095) is this contract's
primary defense against acting on a stale read; no other command in §5/§6
performs a read-then-write sequence where staleness would produce an
incorrect governance-relevant outcome (evidence/clarify are append-only
by key; cancel/readiness construction are idempotent by key).

**IWPC-REQ-147.** Compare-and-set is preferred where available (PEC-001's
existing exclusive-create marker, IWPC-REQ-144); where it is not
available (session/pending-package stores), last-write-wins is the
disclosed v1.0 behavior — this contract does not permit last-write-wins
for any authority-relevant state, and none of the last-write-wins races
named above (IWPC-REQ-141–143) involve authority-relevant state:
Confirmation and readiness-package content are session-derived and
deterministic, not independently-decided authority facts; only
Publication Authorization (IWPC-REQ-144) is authority-relevant, and it is
the one path with real exclusivity.

## 22. Interruption and Recovery Contract

**IWPC-REQ-148.** Session creation: atomic (single `os.replace`,
IWPC-REQ-072); an interruption before the replace leaves no session file
at all — the next invocation sees no session and the caller must retry
`create` (a new `session_id` results; the interrupted attempt leaves no
partial artifact to recover).

**IWPC-REQ-149.** Preview persistence: not applicable — preview is never
persisted as a standalone artifact (IWPC-REQ-094); nothing to recover.

**IWPC-REQ-150.** Confirmation persistence: atomic, via the same
session-file `persist` call that records the `Confirmed` state transition
and Confirmation fields together; an interruption before that single
`os.replace` leaves the session in its pre-confirmation state — the next
invocation MUST resume by re-running `confirm` (safe: single-use,
IWPC-REQ-021, and the interrupted attempt never durably recorded
anything).

**IWPC-REQ-151.** Readiness persistence: atomic, via the Pending-Readiness
Store's own `os.replace`; an interruption before it completes leaves no
pending package — the next `decision-session readiness` invocation
resumes via IWPC-REQ-024's idempotent-by-key construction (session still
shows no existing package, so it reconstructs, deterministically
producing the same content).

**IWPC-REQ-152.** Authorization acceptance: `PublicationCoordinator.
authorize`'s own in-memory construction is not itself persisted
separately from `execute`'s atomic write (PEC-001-governed); an
interruption between `authorize` and `execute` simply means no
publication attempt was recorded at all — the next `publish` invocation
starts a fresh `authorize` call (a new `AuthorizationEvent`, new
`invoked_at`), never resuming a stale in-memory event.

**IWPC-REQ-153.** Publication invocation: governed entirely by PEC-001's
own atomicity guarantees (PEC-REQ-053/054/081/082); this contract adds no
additional atomicity requirement at the invocation layer beyond calling
`execute` exactly once per `publish` invocation.

**IWPC-REQ-154.** Publication-result persistence: governed by PEC-001's
own `PublicationRecordStore`; this contract's own addition is limited to
the Pending-Readiness Store's post-success move-to-`consumed/`
(IWPC-REQ-088), which MUST itself be atomic (`os.replace`) — an
interruption between PEC-001's own successful commit and this store's
move leaves the package still in `pending-packages/` even though
publication succeeded; the next `publish` invocation on that `package_id`
MUST detect this via PEC-001's own replay/idempotency-marker check
(IWPC-REQ-144) before this store's disposition is consulted, so a
mis-ordered move never causes a double-publish.

**IWPC-REQ-155.** Atomicity requirement: every individual file write
governed by this contract (session persist, pending-package persist,
pending-package disposition move) MUST be atomic (`os.replace`); no
multi-file write governed by this contract is required to be
cross-file-atomic beyond PEC-REQ-053/054's own existing guarantees for
`PublicationRecordStore`'s three artifact classes.

**IWPC-REQ-156.** The next invocation determines recovery action solely
by re-reading persisted state (session state, pending-package
disposition, PEC-001's own replay/idempotency-marker check) — never by
trusting a caller-supplied "resume" flag or client-side memory of what
happened. Per-scenario: resume (create a fresh downstream artifact when
none exists yet, IWPC-REQ-151), retry (IWPC-REQ-033), report already
completed (IWPC-REQ-032/113), report conflict (IWPC-REQ-020/105), or
require human review (`persistence_corrupt`, IWPC-REQ-075) — no recovery
path skips Confirmation or Authorization (IWPC-REQ-012 restated).

## 23. Security Contract

**IWPC-REQ-157.** CLI argument secrecy: `--operator-id` is not a secret
value itself (an identity claim, not a credential) but its shell-history
persistence is disclosed (IWPC-REQ-039); no command in this contract
accepts a password, token, or credential as a CLI argument for v1.0
(none is defined — IWPC-REQ-119).

**IWPC-REQ-158.** Shell-history exposure: disclosed for `--operator-id`
and `--owner-id`; both are identity claims, not authority tokens, limiting
the practical severity of exposure — this contract does not treat this as
a Blocking finding (§29).

**IWPC-REQ-159.** stdin handling: none — no command reads stdin
(IWPC-REQ-037).

**IWPC-REQ-160.** File permissions: default umask-governed
(IWPC-REQ-071); no restrictive mode enforced for v1.0, consistent with
every sibling store's authority-neutral posture.

**IWPC-REQ-161.** Temporary files: created only via `tempfile.mkstemp` in
the same directory as the final path (never `/tmp` or a shared
world-writable location), cleaned up on both success and failure paths
(IWPC-REQ-072).

**IWPC-REQ-162.** Symlink handling: `os.replace`'s target path MUST NOT
be resolved through a symlink the caller controls; the store implementation
MUST verify (or construct paths such that) `<session_id>.json`/
`<package_id>.json` resolve strictly within
`.pcae/decision-sessions/`/`.pcae/decision-sessions/pending-packages/`
respectively, rejecting any identifier containing a path separator or
`..` component before it is ever joined into a filesystem path.

**IWPC-REQ-163.** Path traversal: `session_id`/`package_id` values MUST be
validated as safe path components (matching their known generated format,
`CDS-<uuid4>` and the package-id format `PublicationHandoff.build_package`
produces) before being used to construct any filesystem path; a value
failing this check is `invalid_request`, never passed to the filesystem
layer.

**IWPC-REQ-164.** Artifact substitution: mitigated by the Artifact
Binding chain (§15) and the Pending-Readiness Store's whole-package
digest (IWPC-REQ-081) — a hand-edited pending-package file's tampering is
detectable at `publish` time by digest mismatch (mapped to
`artifact_binding_mismatch`), though this contract discloses (per
F-145A-6, §29) that this detection is advisory, not cryptographically
strong (a SHA-256 content digest, not a signature) — a sophisticated local
attacker with filesystem write access could recompute a matching digest
after tampering; this residual risk is explicitly not eliminated by v1.0
and is named here rather than silently left implicit.

**IWPC-REQ-165.** Digest verification: `publish` MUST recompute the
Pending-Readiness Store's whole-package digest at read time and compare
it to the digest recorded at write time before proceeding to
`PublicationCoordinator.authorize`; mismatch is
`artifact_binding_mismatch` (exit class 3).

**IWPC-REQ-166.** Identity forgery resistance: not materially improved by
this contract beyond IWPC-REQ-009's structural-only validation — this is
the same disclosed gap as `authority_not_established` (§19); the CLI
provides no cryptographic identity-forgery resistance for v1.0.

**IWPC-REQ-167.** TOCTOU protection: the digest-verification step
(IWPC-REQ-165) plus PEC-001's own exclusive-create marker
(IWPC-REQ-144) are this contract's only TOCTOU mitigations; the
session/pending-package stores themselves have no TOCTOU protection
beyond atomic single-file replace (a read-then-later-act sequence outside
`publish`'s digest check, e.g. `status` followed by a much later `cancel`,
has no staleness guard beyond IWC-001's own state-machine rejection of an
invalid transition).

**IWPC-REQ-168.** Transport impersonation: out of scope for v1.0 — no
network transport is defined (the CLI adapter IS the transport,
IWPC-REQ-006); a future HTTP/API transport revision MUST define its own
authentication/impersonation-resistance requirements at that time.

**IWPC-REQ-169.** Unsafe automation use: non-interactive `publish`
(IWPC-REQ-030) is deliberately still gated by requiring an explicit,
complete `--operator-id` and a resolvable `package_id` naming a
specifically-confirmed, specifically-built package — an automation
script cannot synthesize confirmation or authorization; it can only
invoke the same human-facing commands a human would, with the same
governance obligations.

**IWPC-REQ-170.** Log redaction: any operational log line this contract's
future implementation emits MUST redact confirmation-statement free text
beyond a bounded prefix length and MUST NOT log full package content;
`session_id`/`package_id`/`record_id`/timestamps are safe to log
unredacted (§24).

**IWPC-REQ-171.** Non-interactive publication MUST require explicit,
complete artifacts (a resolvable `package_id` and a supplied
`--operator-id`) and MUST NOT synthesize confirmation or authorization
under any flag, environment variable, or configuration default
(restates IWPC-REQ-027/030 as the contract's central security invariant).

## 24. Observability Contract

**IWPC-REQ-172.** Safe operational identifiers: `session_id`,
`request_id` (reserved, not populated in v1.0 — no request-id scheme is
introduced beyond `session_id`/`package_id` per IWPC-REQ-005; the field
name is reserved for a future transport revision that might add one),
`preview_id`, `confirmation_id`, `readiness_package_id` (i.e.
`package_id`), `authorization_event_id` (PEC-001's `event_id`),
`publication_attempt_id`, and `publication_result` status are the
complete safe-to-log/safe-to-return identifier set.

**IWPC-REQ-173.** Logs, transport responses, persisted session state, and
canonical governance records (CHGR) are four distinct categories; a log
line or transport response is never treated as authoritative governance
evidence unless PEC-001 or CHGR-001 explicitly says otherwise (neither
does, for anything this contract produces) — restates IWC-001's/PEC-001's
own "logs are not authoritative" discipline at the CLI layer.

## 25. Dependency Contract

**IWPC-REQ-174.** Allowed dependency direction:

```
CLI decision-session adapter
    -> transport/application boundary (the adapter module itself, IWPC-REQ-006)
    -> Interactive Workflow public interfaces (SessionCoordinator, WorkflowOrchestrator, PublicationHandoff)

CLI publication adapter (governance-record publish)
    -> transport/application boundary (the adapter module itself)
    -> Publication Coordinator public interfaces (PublicationCoordinator.authorize/.execute)
```

**IWPC-REQ-175.** Prohibited: `PublicationCoordinator` (or any file under
`src/pcae/governance/publication/`) importing CLI code
(`src/pcae/commands/**`, `src/pcae/cli.py`); Interactive Workflow
importing CLI code; Publication owning Interactive Workflow session
semantics; Interactive Workflow writing CHGR artifacts; the
`decision-session`/`publish` CLI adapters importing private subsystem
internals (`_`-prefixed names) where a public boundary method already
exists; and any lifecycle or Permission Broker bypass from either
adapter.

**IWPC-REQ-176.** A future implementation phase (145F/145G) MUST extend
the existing forbidden-import boundary test pattern
(`tests/test_phase_144c_publication_coordinator.py`'s
`_FORBIDDEN_IMPORT_ROOTS` AST-parse style) to additionally assert: no file
under `src/pcae/commands/decision_session.py` (or wherever the future
adapter lives) imports `pcae.governance.publication` private
(`_`-prefixed) names; and no file under
`src/pcae/governance/publication/` imports
`pcae.commands.decision_session` or `pcae.cli`.

**IWPC-REQ-177.** The existing coupling permitted between
`interactive_workflow.publication_handoff` and the rest of
`interactive_workflow` is unaffected by this contract (that coupling is
PEC-REQ-058-permitted territory, unmodified); this contract's own
Dependency Contract governs only the new CLI adapter layer's edges.

## 26. Compatibility Contract

**IWPC-REQ-178.** Command names, once frozen (§5, §6), MAY only be
extended (new subcommands) in a future minor revision; an existing
command name MUST NOT be renamed or removed without a major revision and
an explicit deprecation cycle (§30).

**IWPC-REQ-179.** Required arguments for an existing command MUST NOT be
added, removed, or have their meaning changed without a major revision; a
new optional argument MAY be added additively in a minor revision.

**IWPC-REQ-180.** Machine-readable output fields already defined (§7,
§10) MUST NOT be removed or have their type/meaning changed without a
major revision; new optional fields MAY be added additively.

**IWPC-REQ-181.** Transport envelope versions follow §11's rules exactly.

**IWPC-REQ-182.** Persisted session formats (§12) and pending-readiness
store formats (§13) MUST carry their own `schema_version`; a future
format change MUST be additive (new optional field) for a minor
revision, or accompanied by an explicit migration procedure
(`persistence/migration.py`-style, matching IWC-001's existing precedent)
for a major revision.

**IWPC-REQ-183.** Identifiers (`session_id`, `package_id`, `record_id`)
MUST NOT change format without a major revision, since external callers
may persist them for correlation.

**IWPC-REQ-184.** Error types (§19) and exit-code classes (§9) form a
closed set for v1.0; adding a new `error_type` mapped to an existing exit
class is a minor-revision-compatible additive change; adding a new exit
code, or reassigning an existing `error_type` to a different exit class,
requires a major revision.

**IWPC-REQ-185.** Compatibility change classes, summarized: patch-level
implementation change (cosmetic text-mode output, internal refactor with
no observable behavior change) requires no contract revision; additive
contract revision (new optional field, new error_type mapped to an
existing class, new subcommand) is a minor version bump; any change
narrowing an existing guarantee, removing a command/field/error_type,
reassigning an exit code, or changing persisted-format semantics
non-additively is a major version bump requiring full re-freeze
discipline (§30).

## 27. Implementation Conformance Evidence

**IWPC-REQ-186.** A future implementation phase MUST produce:
requirement-to-code traceability (a table mapping every `IWPC-REQ-###` to
the specific function/class/test satisfying it); requirement-to-test
traceability (inverse mapping); command-surface tests (one per §5/§6
command, covering the state transitions and failure modes enumerated
there); JSON compatibility tests (schema/field-presence assertions per
§10/§11); session-state transition tests (every §12 transition, both
legal and illegal); store corruption tests (§13/§14 corrupt-file
handling); concurrency tests (§21's named races, demonstrating the
disclosed last-write-wins behavior is at least non-crashing and
non-silently-authority-granting); replay tests (§20); authorization-
binding tests (§15, §17, §18); forbidden-import tests (§25, extending the
existing pattern per IWPC-REQ-176); security-path tests (§23:
path-traversal rejection, digest-mismatch rejection); and runtime-unchanged
evidence (`pcae runtime inspect` before/after, unchanged).

## 28. Contract Compliance Matrix

**IWPC-REQ-187.** Every requirement in §2–§26 maps to: a Phase 145A
architecture section, a governing contract citation where applicable, an
intended implementation-owner phase, and intended verification evidence.
The complete matrix:

| IWPC-REQ range | 145A section | Governing contract | Owner phase | Verification |
|---|---|---|---|---|
| 001–003 (Scope) | §5–§7 | — | 145B (this phase, text only) | Requirement-text review |
| 004–006 (Terminology) | §4, §7.5 | IWC-001 §2, PEC-001 §2 | 145B | Cross-reference check, no synonym |
| 007–013 (Invariants) | §5, §9 | IWC-001 §11.1, PEC-001 §3/§5 | 145B / 145F–G (enforcement) | Adversarial scenarios §29 |
| 014–025 (decision-session cmds) | §6.1 | IWC-001 §4.4, §10, §11.4 | 145F | Command-surface tests |
| 026–035 (publish cmd) | §6.1, §9 | PEC-001 §6, §7 | 145G | Command-surface tests |
| 036–041 (Input) | §7 (implicit) | — | 145F/145G | Input-channel tests |
| 042–049 (Output) | §7.4 | — | 145F/145G | JSON compatibility tests |
| 050–052 (Exit codes) | §6.3, §12 | — | 145F/145G | Exit-code assertion tests |
| 053–057 (Transport) | §7 (implicit), §11 | IWC-001/PEC-001 existing dataclasses | 145F/145G | Schema reuse audit |
| 058–062 (Versioning) | — (new) | — | 145F/145G | Version-field presence tests |
| 063–065 (Session state) | §4.4 (restated) | IWC-001 §4.4, §11.1 | 145F | State-transition tests |
| 066–077 (SessionRepository) | §11.1 | IWC-001 (ABC, unmodified) | 145D | Store implementation tests |
| 078–092 (Pending-Readiness Store) | §11.2 | — (new) | 145E | Store implementation tests |
| 093–100 (Artifact Binding) | §7.5, §9 | IWC-001/PEC-001 existing checks | 145F/145G | Binding-mismatch tests |
| 101–106 (Confirmation) | §9, §10 | IWC-001 §10, IWC-REQ-102/103/112 | 145F | Confirmation tests |
| 107–115 (Readiness Package) | §11.4 (existing) | IWC-001 §26, PEC-001 §8 | 145D/145E | Package construction tests |
| 116–124 (Authorization Input) | §10 | PEC-001 §6 | 145G | Authorization tests |
| 125–133 (Publication Invocation) | §6.1, §13 | PEC-001 §7 | 145G | Invocation-order tests |
| 134–137 (Error taxonomy) | §12 | PEC-001 §11 (errors) | 145F/145G | Error-mapping tests |
| 138–140 (Idempotency) | §13 | PEC-001 §6 (replay) | 145F/145G/145H | Idempotency tests |
| 141–147 (Concurrency) | (disclosed limitation) | — | 145D/145E (store), 144C (marker) | Concurrency tests |
| 148–156 (Interruption/Recovery) | §11 (stores) | PEC-001 §7 (atomicity) | 145D/145E/145G | Interruption-simulation tests |
| 157–171 (Security) | §14 (implicit) | — | 145F/145G/145H | Security-path tests |
| 172–173 (Observability) | §7.5 | — | 145F/145G | Log/response separation review |
| 174–177 (Dependency) | §15 (implicit) | existing boundary tests | 145F/145G | Forbidden-import tests |
| 178–185 (Compatibility) | — | — | future revisions | Version-diff review |
| 186 (Conformance Evidence) | — | — | 145H | Full traceability audit |
| 187 (this matrix) | — | — | 145C | Independent re-derivation |

**IWPC-REQ-188.** No requirement in §2–§27 fails to map to this matrix;
this was independently confirmed by extracting every `IWPC-REQ-###`
occurrence from this document and checking each falls within exactly one
of the ranges listed above, with no gap and no double-count.

## 29. Conflict and Findings Register

Checked against IWC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, existing
CLI conventions, lifecycle authority, Permission Broker boundaries, and
runtime constraints. No conflict weakens an existing contract.

| # | Item | Classification | Disposition |
|---|---|---|---|
| C-1 | No `authority_basis_claimed`/authority-evaluation mechanism exists anywhere upstream (F-145A-4) | Non-Blocking, Observation | Restated at IWPC-REQ-009/119/123/166; not remedied by this contract; remains a named, disclosed gap outside this contract's scope. |
| C-2 | Session/pending-package stores have no cross-process mutual exclusion beyond atomic rename (F-145A-5) | Non-Blocking, Observation | Addressed explicitly in §21 rather than silently deferred; disclosed as accepted for v1.0. |
| C-3 | Hand-edited pending-package tampering residual risk — digest check is advisory, not cryptographic (F-145A-6) | Non-Blocking, Observation | Addressed at IWPC-REQ-164/165; residual risk named explicitly. |
| C-4 | Model D (transport-neutral application-service layer) deferred (F-145A-7) | Deferred | IWPC-REQ-006 confirms the CLI adapter IS the transport for v1.0; Model D remains available as a future additive revision. |
| C-5 | PEC-001 Model 3 (delegated authorization token) deferred (F-145A-8) | Deferred | IWPC-REQ-118 uses Model 2 (CLI-operator invocation) unchanged; Model 3 remains PEC-001's own extensibility path, untouched by this contract. |
| C-6 | `decision-session` vs. `pcae session` naming collision risk | Non-Blocking, Observation | Resolved at §5's header commentary and IWPC-REQ-014: distinct top-level noun, never a `session` subcommand. |
| C-7 | This is the first formalized exit-code/`error_type` vocabulary anywhere in this CLI (no prior precedent existed to conform to) | Observation | Disclosed at §9/§19; not a contradiction of any existing convention, since none existed. |
| C-8 | `PublicationAttempt`/`PublicationEvidence` CAS-cutover schemas (`schema_resources/cltr_cutover/records/`) are unrelated to this contract's Publication pipeline | Non-Blocking, Observation | Confirmed by direct source inspection during this phase's research; not cited as precedent anywhere in this contract, avoiding a false-authority citation. |
| C-9 | F-145G.1-1: no v1.1 command transitioned a session out of `AwaitingDecision` | Blocking, Repaired | Closed by Phase 145G.2 (§33): `decision-session select` added, IWPC-REQ-192-196. |
| C-10 | No command transitions `AwaitingDecision` → `AwaitingClarification` (`clarify` only answers a clarification already open) | Non-Blocking, Observation | Newly disclosed by Phase 145G.2 (F-145G.2-1); explicitly out of this phase's own authorized "decision selection" scope; not remedied here. Remains reachable only via test-fixture bridging, mirroring F-145G.1-1's own pre-145G.2 disposition. |
| C-11 | F-145G.2V-1: no command in the `decision-session` family enforced IWC-REQ-022/IWC-REQ-151's identity-bound-resumption requirement; no channel existed to even supply a competing identity claim | Blocking, Repaired | Closed by Phase 145G.3 (§34): `--as-identity` added to every mutating command, enforced exactly once by `SessionApplicationService`. |

**IWPC-REQ-189 (amended by Phase 145G.3).** No item in this register is
Blocking as of this contract's current revision. A future implementation
phase MAY proceed against this contract without first resolving any
disclosed item above, since each is either an explicitly out-of-scope
pre-existing gap (C-1, C-4, C-5, C-10) or an explicitly addressed,
disclosed design choice or repair (C-2, C-3, C-6, C-7, C-8, C-9, C-11).

## 30. Amendment Contract

**IWPC-REQ-190.** IWPC-001 MAY evolve only through a governed superseding
contract revision (a future phase producing a revised
`INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md` with an
incremented version and an explicit revision-history section), never
through an implementing phase's own discretion, mirroring PEC-001 §16's
and IWC-001's own amendment discipline exactly.

**IWPC-REQ-191.** A revision MAY be additive (new optional field, new
subcommand, new `error_type` mapped to an existing exit class) without
renumbering any existing `IWPC-REQ-###`; a revision narrowing or removing
an existing guarantee MUST be a major version and MUST retain retired
requirement identifiers in place, marked "Retired," never reused.

## 31. Non-Goals

This contract does not, and no future phase MAY treat it as if it did:

- implement any CLI command, transport adapter, `SessionRepository`
  concrete class, or Pending-Readiness Store concrete class;
- modify `src/pcae/interactive_workflow/**`, `src/pcae/governance/
  publication/**`, IWC-001, PEC-001, CHGR-001, TAMC-001, or TAMPC-001;
- create engineering execution capability, change Permission Broker
  behavior, change lifecycle authority, change publication authority, or
  change CHGR ownership;
- merge Confirmation, Publication readiness, Authorization, Publication,
  or Engineering execution into any single act;
- add automatic confirmation, automatic authorization, or automatic
  publication;
- introduce a new broad persistence authority beyond the two narrowly-
  scoped stores this contract names;
- change runtime state or capability;
- resolve the authority-evaluation gap (C-1) — that remains explicitly
  out of scope for this contract and this repository as a whole, pending
  a future, separately governed initiative.

## 32. Phase 145C contract revision — session-state literal casing repair

**Revised by:** Phase 145C — Interactive Workflow + Publication CLI/Transport
Contract Independent Verification.

**Finding repaired: B-1 (Blocking).** IWPC-REQ-063 stated: "It reports,
verbatim, the state vocabulary IWC-001 §4.4 already defines: `created`,
`evidence_ready`, `awaiting_decision`, `awaiting_clarification`,
`decision_selected`, `awaiting_confirmation`, `confirmed`, plus terminal
`cancelled`, `expired`, `abandoned`." Every §5 command sub-section
(IWPC-REQ-015–IWPC-REQ-025) and §16/§17 restated the same lowercase
snake_case literals. Direct re-reading of
`src/pcae/interactive_workflow/models/session.py`'s `SessionState` enum
and `src/pcae/interactive_workflow/serialization/schema.py`'s `to_payload`
(the actual, frozen IWC-001 v1.2 wire representation this contract claims
to reproduce "verbatim") shows the real serialized values are PascalCase:
`Created`, `EvidenceReady`, `AwaitingDecision`, `AwaitingClarification`,
`DecisionSelected`, `AwaitingConfirmation`, `Confirmed`, `Cancelled`,
`Expired`, `Abandoned`. `from_payload` constructs `SessionState(payload
["session_state"])`, an exact-match enum lookup that raises on a
lowercase value. A v1.0-literal implementation of IWPC-REQ-063's own
prose and a v1.0-literal implementation of `Session.to_payload()`/
`from_payload()` therefore could not both be satisfied: this was not a
cosmetic drift but a direct self-contradiction inside a single frozen
requirement, blocking implementation-readiness (a 145F implementer
following IWPC-REQ-063's literal text would round-trip incorrectly
against the real store).

**Repair:** every session-state literal in §5 (IWPC-REQ-015, 016, 017,
018, 020, 021, 023, 024, 025) and §12 (IWPC-REQ-063) and §16/§17
(IWPC-REQ-101, 102, 104, 107) is corrected in place to the exact
PascalCase `SessionState` value it denotes. No state was added, removed,
merged, or renamed; no transition changed; no requirement renumbered,
retired, or reassigned — this is a literal-casing correction only,
preserving every requirement's original intent and identifier exactly, per
§30's additive-evolution discipline (a narrowing/removal would require a
major revision; this repair narrows nothing).

**Independently reconfirmed unchanged by this revision:** requirement
count (191, IWPC-REQ-001–IWPC-REQ-191, unchanged by this repair — no
identifier added or removed); the ten-state set itself (unchanged, still
exactly IWC-001's own ten states); every other section of this contract
(§2–§31, unaffected); IWC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001
(none modified); runtime (Observed / observe / unavailable, unaffected).

## 33. Phase 145G.2 contract revision — decision-selection command added, closing F-145G.1-1

**Revised by:** Phase 145G.2 — Interactive Workflow Decision-Selection
Command and Contract Repair.

**Finding repaired: F-145G.1-1 (Blocking).** Phase 145G.1's own
implementation and canonical report demonstrated, by direct source
inspection, that no command in this contract's v1.1 frozen §5 command
surface (IWPC-REQ-014) transitioned a session out of `AwaitingDecision`.
`Session.human_selection_id`/`human_rationale_text`/
`human_conditions_text`/`options_presented` — the Decision Capture fields
IWC-001 §5.3/§6 requires a human to author — had no production setter
anywhere in this codebase. `clarify` (requires `AwaitingClarification`,
itself only reachable from `AwaitingDecision`), `preview` (requires
`DecisionSelected` or later), and `confirm` (requires
`AwaitingConfirmation`) were each implemented correctly but reachable only
via direct test-fixture session-state construction, never a real,
CLI-only invocation sequence starting from `create`.

**Independent re-derivation (Phase 145G.2), confirming and extending
F-145G.1-1's original diagnosis:** direct re-inspection of
`interactive_workflow/state_machine/transitions.py`'s `TRANSITION_TABLE`
confirmed both `EvidenceReady` → `AwaitingDecision` and `AwaitingDecision`
→ `DecisionSelected` were legal but undriven by any command; `SessionApplicationService`
(`interactive_workflow/application/session_service.py`) had no method
setting any Decision Capture field; `Session` (`interactive_workflow/models/session.py`)
had no mutator carrying those fields (only `with_state`, which does not).
Phase 145G.2 additionally discovered, during required re-derivation before
coding, that closing only the `AwaitingDecision` → `DecisionSelected` hop
would not by itself make `confirm`/`readiness`/publication reachable:
`generate_preview`'s existing implementation never transitioned a session
out of `DecisionSelected` at all, even though IWC-001's own frozen state
table already defines `AwaitingConfirmation` as "Preview generated,
awaiting Confirmation" and this contract's own IWPC-REQ-018 already
conditioned "no transition" on "unless IWC-001 defines otherwise" — IWC-001
does define otherwise. This was a pre-existing implementation defect
relative to already-frozen contract text, not a new contract gap; §5.5
(now `preview`'s subsection) is corrected in place to state the transition
IWC-001 already required, and `SessionApplicationService.generate_preview`
is repaired to perform it on first successful Preview construction. Without
this second, previously-undisclosed repair, this phase's own exit
criteria (a genuine CLI-only path reaching `confirm`/`readiness`/
publication) could not have been met by the `select` command alone —
disclosed here explicitly rather than silently folded into F-145G.1-1's
original text.

**Repair:**

1. IWPC-REQ-014's command-surface list (§5) is amended in place to add
   `decision-session select`, per IWPC-REQ-191's additive-evolution
   allowance — no other line in the list is altered, no requirement
   renumbered.
2. New §5.3 `decision-session select` and IWPC-REQ-192–IWPC-REQ-196 are
   added, freezing: operation name and command name; required/optional
   inputs; the combined `EvidenceReady` → `AwaitingDecision` →
   `DecisionSelected` single-invocation design (mirroring IWPC-REQ-016's
   own precedent) versus the direct `AwaitingDecision` →
   `DecisionSelected` hop when a session is already `AwaitingDecision`;
   option-presentation binding and closed-set membership validation;
   identity source (the session's own bound `owner_identity`, no separate
   flag); fail-closed, non-idempotent, single-use replay semantics
   (mirroring IWPC-REQ-021's confirm precedent); and the error/exit-code
   mapping (reusing the existing `invalid_request`/`invalid_state_transition`
   taxonomy members unchanged — no new `error_type` or exit code was
   needed).
3. Old §5.3–§5.8 (`clarify`, `preview`, `confirm`, `status`, `readiness`,
   `cancel`) are renumbered §5.4–§5.9 to make room; only subsection
   numbers moved — no `IWPC-REQ-###` identifier was renumbered, retired,
   or reassigned, per IWPC-REQ-191.
4. §5.5 (`preview`, formerly §5.4) — IWPC-REQ-018's "State transition"
   sentence is corrected in place (see re-derivation above): first
   successful Preview construction for a `DecisionSelected` session now
   transitions it to `AwaitingConfirmation`, matching IWC-001's own,
   already-frozen state-table definition. IWPC-REQ-019 (Preview's natural
   idempotency) is unchanged and unaffected — repeated calls after the
   first still reproduce a byte-identical digest, transition or no
   transition.
5. IWPC-REQ-064's cross-reference is updated from "§5.1–§5.8" to
   "§5.1–§5.9" (renumbering-only, no semantic change).
6. §29's Conflict and Findings Register gains C-9 (F-145G.1-1, now
   Repaired) and C-10 (F-145G.2-1, a newly-disclosed, explicitly
   out-of-scope sibling gap: no command opens `AwaitingClarification`
   from `AwaitingDecision`, so `clarify`'s own real-world reachability
   remains bridged-only — this phase's own governing prompt authorized
   only "decision selection," not a "request clarification" command, and
   this gap does not block this phase's own exit criteria since the
   happy path never requires `clarify`).

**IWC-001 disposition:** unmodified. Direct re-reading of IWC-001 §4.4,
§5, §6 (IWC-REQ-018, IWC-REQ-052, IWC-REQ-063, and the state table itself)
confirmed IWC-001 already fully anticipates human decision selection as an
exclusively human act with a closed option set, no implicit-selection
path, and no AI inference — the gap was entirely a missing CLI/transport
binding in this contract, not a semantic gap in IWC-001. No conflict
between IWC-001 and this contract's pre-145G.2 text was found; this is a
purely additive repair to this contract alone.

**Independently reconfirmed unchanged by this revision:** the ten-state
set and `TRANSITION_TABLE` (unchanged — both already permitted every
transition this revision now drives); every `IWPC-REQ-###` identifier
through IWPC-REQ-191 (none renumbered, retired, or reassigned; new
identifiers begin at IWPC-REQ-192); the existing 24-member `error_type`
taxonomy and 6-member exit-code table (§9/§19, unchanged — no new member
was needed); §6 (Publication command contract, unaffected); §13/§14 (the
two persistence stores, unaffected — `select` persists through the
existing `SessionRepository`/`FilesystemOrchestrationStore` only); IWC-001,
PEC-001, CHGR-001, TAMC-001, TAMPC-001 (none modified); runtime (Observed
/ observe / unavailable, unaffected).

## 34. Phase 145G.3 contract revision — identity-bound resumption enforcement, closing F-145G.2V-1

**Revised by:** Phase 145G.3 — Decision-Session Identity-Bound Resumption
Contract and Implementation Repair.

**Finding repaired: F-145G.2V-1 (Blocking).** Phase 145G.2V's independent
verification demonstrated, by direct source inspection and adversarial
reproduction (a session created with `owner_identity="alice"` accepting
every mutating command unchanged under a simulated `USER=mallory`/
`GIT_AUTHOR_NAME=mallory` environment), that no command in the
`decision-session` family enforced IWC-REQ-022/IWC-REQ-151's requirement
that a session in `Created` through `AwaitingConfirmation` be resumed only
by the identity bound at its creation. `Session.owner_identity` was
written exactly once, at `create`, and never read back for comparison
anywhere; no channel existed anywhere in the CLI to even supply a
competing identity claim, so the requirement was silently unenforceable —
not merely under-tested. IWPC-REQ-195's own text ("select accepts no
identity input distinct from the session's own bound owner_identity") had
come to be relied upon as if it meant the binding was enforced, when it
only ever meant the principal was never *inferred* from ambient state.

**Independent re-derivation (Phase 145G.3), before implementation:**
direct re-inspection of every `SessionApplicationService` method
(`submit_evidence`, `select_decision`, `submit_clarification`,
`generate_preview`, `record_confirmation`, `cancel_session`,
`construct_readiness_package`) confirmed each follows an identical
pattern — `session = self.load_session(session_id)` followed immediately
by a state-precondition check — with no identity comparison anywhere in
between; `PublicationApplicationService.ensure_readiness_package`'s own
idempotent-by-key cache-hit branch was found to be a second, distinct
instance of the same gap (a second `readiness` call against an
already-pending package never re-loaded or re-checked the session at
all). No pre-existing identity-claim value type or comparison
infrastructure was found anywhere in the `interactive_workflow` bounded
context; `pcae.cltr.authority.identity.PrincipalIdentifier` exists but
sits outside `interactive_workflow`'s policy-authorized dependency edges
(`.pcae/policy.toml`'s `[architecture.rules]`), so it was not imported —
a small, local, structurally-equivalent comparison (plain exact-string
equality against the already-persisted `owner_identity`) was used
instead, requiring no policy amendment and no new persisted field.

**Repair:**

1. A new required `--as-identity` argument is added to every mutating
   `decision-session` command's argument list: `evidence` (IWPC-REQ-016),
   `select` (IWPC-REQ-192, superseding IWPC-REQ-195's original text in
   place), `clarify` (IWPC-REQ-017), `preview` (IWPC-REQ-018), `confirm`
   (IWPC-REQ-020), `readiness` (IWPC-REQ-023), `cancel` (IWPC-REQ-025).
   `create` (establishes the binding, not a resumption) and `status`
   (read-only observation, not resumption — IWPC-REQ-022 amended in place
   with an explicit disclosed-reasoning sentence) are deliberately
   unaffected; no `IWPC-REQ-###` identifier is renumbered, retired, or
   reassigned.
2. The CLI's entire identity responsibility is structural-only
   (IWPC-REQ-007's "collect and validate structural completeness"
   allowance): non-empty, bounded length (512 characters), no control
   characters. It never compares the claim against `owner_identity` — the
   comparison is `SessionApplicationService`'s sole responsibility
   (`_require_bound_identity`/`require_bound_identity`), called
   immediately after `load_session` resolves the persisted record and
   before any state-precondition check, idempotent early-return
   (`cancel_session`), or idempotent-by-key cache check
   (`PublicationApplicationService.ensure_readiness_package`) — so a
   mismatched identity can never present as an idempotent success.
   Comparison is exact-string equality only: no case-folding, no
   whitespace normalization, no partial/prefix matching.
3. A new closed-taxonomy `error_type`, `identity_binding_mismatch`, and a
   new exit-code class, `6`, are added (§9 IWPC-REQ-050/051, §19.1
   IWPC-REQ-134) — additive only; every existing `error_type`/exit-code
   member and mapping is unchanged.
4. §29's Conflict and Findings Register gains C-11 (F-145G.2V-1, now
   Repaired).

**IWC-001 disposition:** unmodified. IWC-REQ-022/IWC-REQ-151 already fully
specify the identity-bound-resumption requirement this revision enforces;
the gap was entirely a missing CLI/application enforcement point in this
contract's own implementation, not a semantic gap in IWC-001.

**Independently reconfirmed unchanged by this revision:** the ten-state
set and `TRANSITION_TABLE` (unchanged — this revision adds no new
transition and mutates no session field it did not already mutate); every
existing `IWPC-REQ-###` identifier (none renumbered, retired, or
reassigned; the sole textual correction, IWPC-REQ-195, keeps its original
number); `Session`'s persisted schema (`interactive_workflow/
serialization/schema.py`, unchanged — `owner_identity` was already
persisted; no new field was added, since the claim is compared, never
stored a second time); §6 (Publication command contract, unaffected
beyond `readiness`'s own identity gate); §13/§14 (the two persistence
stores, unaffected); IWC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001 (none
modified); runtime (Observed / observe / unavailable, unaffected); no
execution capability added.

---

## 35. Phase 145H.1 contract revision — Post-Consumption Readiness Uniqueness Contract Clarification, closing the contract-drafting half of H-1

**Revised by:** Phase 145H.1 — Post-Consumption Readiness Uniqueness
Contract Clarification.

### 35.1 Reason and independent re-derivation

Phase 145H's independent, adversarial certification (§2, §6 of that
phase's own canonical report) demonstrated, by live CLI subprocess
reproduction against a disposable scratch repository, that
`decision-session readiness`, invoked a second time against a `Confirmed`
session whose first `PublicationReadinessPackage` had already been
consumed by a successful `governance-record publish`, constructs and
persists a **second**, independently publishable package (a different
`package_id`, the same `session_id`), which `publish` then turns into a
**second CHGR for the same Human Governance Act**. Recorded as Blocking
Finding H-1. Phase 145H's own repair-authority rules correctly withheld a
repair, because the existing contract text did not *unambiguously* dictate
one of several plausible remedies (§6.6 of that phase's report).

This phase independently re-derived H-1's contractual cause from primary
text, not from 145H's own summary of it:

- **IWC-REQ-019/IWC-REQ-024** (IWC-001 §7, §10.1, §4.9): Confirmation is a
  single, non-repeatable act; a session terminal at `Confirmed` is never
  reused for a new interaction. At most one Human Governance Act can ever
  originate from one session.
- **CHGR-REQ-001/CHGR-001 §2**: a CHGR is, definitionally, the
  representation of **one** Human Governance Act — singular, not one
  among possibly several equally-valid representations.
- **IWPC-REQ-024** (this contract, unrevised text): readiness construction
  is "idempotent by key, keyed on `session_id`: a second construction
  attempt for a session that already has a persisted pending package
  SHALL return the existing package, never rebuild it" — stated without a
  post-consumption exception.
- **IWPC-REQ-082/107** (this contract, unrevised text): "one **pending**
  package per session" — textually scoped to the pending state only,
  which 145H correctly identified as ambiguous: a deliberate
  scope-limiter (no guarantee once consumed) is one reading; a mere
  description of the store's own directory layout, carrying no bearing on
  whether a *second* package should ever be constructable, is the other.
- **PEC-REQ-007/041/080** and **IWPC-REQ-032/113**: the one guard that
  *is* airtight (`publish` naming an already-consumed `package_id`) is
  correctly scoped to `package_id`, the wrong key for this question —
  PEC-001 was never asked to reason about session-level uniqueness, and
  nothing required it to.

No contract text anywhere affirmatively permits a second, independently
publishable package for a session whose first package has already been
published. This phase confirms 145H's own conclusion: **the implementation
defect is real and the fault for it lies in code** (`FilesystemPendingReadinessStore.find_by_session_id`'s
own docstring-disclosed "never return a `consumed/` record" design, wired
into real construction power by Phase 145G.1 without the wiring being
re-checked against IWPC-REQ-024's unqualified text or CHGR-001 §2's
one-act-one-record framing) — **and, independently, that a real,
secondary contract-drafting gap exists** in IWPC-REQ-082/107's
pending-scoped language, which this section closes.

### 35.2 Contract-gap classification

The gap is classified as: **missing normative requirement** (no
`IWPC-REQ-###` anywhere stated the required post-consumption behavior) and
**missing cross-contract uniqueness statement** (no single sentence,
anywhere across IWC-001/IWPC-001/PEC-001/CHGR-001, tied "one Human
Governance Act" to "one readiness package, for the package's entire
lifecycle" at the CLI/transport layer specifically — CHGR-001 §2 states
the *conclusion* one layer downstream, but no contract carried it forward
to the readiness-construction boundary this contract alone owns). It is
**not** classified as incomplete replay semantics (PEC-001's
`package_id`-scoped replay guard is, and remains, correct and sufficient
*once* the upstream session-level gap above is closed — §35.6), not
incomplete persistence semantics (the store's atomic-write and
disposition-move mechanics are independently correct; only the
*idempotency-lookup scope* was wrong), not ambiguous terminology (every
term in play — "pending," "consumed," "session_id," "package_id" — is
already precisely defined), and not incomplete recovery semantics beyond
the narrow, already-disclosed IWPC-REQ-154 interruption window restated
unchanged at §35.7 below.

The primary implementation defect (`find_by_session_id`'s consumed-record
exclusion, wired into real construction power without re-verification) and
the secondary contract-drafting gap (IWPC-REQ-082/107's ambiguous
pending-scoped language) are independently real and are not conflated: the
implementation defect would still have been a defect even under a
maximally strict reading of the pre-145H.1 text (IWPC-REQ-024's own
*unqualified* half already argued against it), but the contract's own
ambiguity is why five independent-verification passes did not catch it —
closing the ambiguity, as this section does, removes the excuse for a
future recurrence without itself repairing the code.

### 35.3 Alternatives analysis and selected normative behavior

Three candidate post-consumption behaviors were evaluated:

**Option A — return the original, consumed readiness package's identity
unchanged.** Preserves IWPC-REQ-024's own idempotency guarantee exactly,
merely removing its accidental pending-only scope; requires no new
transport shape, since IWPC-REQ-023 already documents `readiness`'s output
contract as reporting "consumption status (pending / consumed /
none-yet-created)" — a `"consumed"` disposition was already a designed,
frozen output value that the implementation simply never reached because
the lookup itself excluded consumed records. Operator-friendly (an
operator re-running `readiness` out of habit or automation sees the
correct, already-published state, including its `record_id` where
available, rather than an opaque rejection). Fully compatible with restart
and recovery (IWPC-REQ-148–156, unchanged). No new transport version
required.

**Option B — reject readiness after successful publication with a new
domain error.** Contradicts IWPC-REQ-024's existing unqualified idempotent
by-key guarantee, which nowhere states or implies readiness ever *fails*
once a package exists for a session; a rejection would be a **narrowing**
of an existing frozen guarantee, requiring a major version bump per
IWPC-REQ-191, not the additive minor revision this gap warrants. It also
discards operationally useful information (the original `package_id`/
`record_id`) an operator following documented behavior would otherwise
receive for free.

**Option C — return a distinct "publication-completed" result shape,
separate from readiness.** Would require inventing a new response schema
and likely a new command or flag, duplicating information IWPC-REQ-023
already assigns to `readiness`'s own output contract, and would introduce
a new caller-visible branch (which result shape did I get back?) where
none is architecturally required, violating IWPC-REQ-054's "no transport
object shall duplicate an existing authoritative schema" discipline.

**Selected: Option A**, confirming the phase's own preferred design
direction was correct on independent primary-text analysis, not merely
deferred to. This is frozen as **IWPC-REQ-197** below.

### 35.4 The uniqueness invariant

**IWPC-REQ-197.** For the entire lifetime of a `session_id` — from
`Created` through any terminal state, and without regard to whether a
bound `PublicationReadinessPackage` is currently `pending` or has been
moved to `consumed/` — at most one `PublicationReadinessPackage` SHALL
ever exist for that `session_id`, and `session_id` remains the sole
readiness uniqueness key (no new identifier is introduced; per IWC-REQ-019/
IWC-REQ-024, a session yields at most one Confirmation, hence at most one
Human Governance Act, hence at most one legitimately publishable package).
Concretely, and without exception:

1. **One readiness identity per confirmed decision.** The first successful
   `PublicationHandoff.build_package` call for a `session_id` assigns that
   session's one and only `package_id`, for the session's entire remaining
   lifetime, regardless of the package's later disposition.
2. **One successful authoritative publication per Human Governance Act.**
   At most one `governance-record publish` invocation naming a package
   bound to a given `session_id` SHALL ever succeed (restates PEC-REQ-080
   at the session layer, closing the gap PEC-001's own `package_id`-scoped
   guard could not close alone, §35.6).
3. **One authoritative CHGR per Human Governance Act.** At most one CHGR
   SHALL ever exist citing a given session's Confirmation as its
   provenance (a direct consequence of invariants 1 and 2 above, combined
   with PEC-REQ-080's existing package-level guarantee).
4. **One successful publication result for a given readiness identity.**
   A `package_id`, once it appears in a `publication_already_completed`
   or successful-publication result, SHALL always resolve to that same
   result on every future reference, by either lookup key
   (`package_id` at `publish`, `session_id` at `readiness`).
5. **No new readiness package after authoritative publication of the same
   confirmed decision.** No sequence of CLI invocations, however
   repeated, delayed, or interleaved with process restarts, SHALL cause a
   second `package_id` to be minted for a `session_id` that already has
   one — closing exactly the sequence H-1 demonstrated:

   ```
   same confirmed decision
       -> readiness package A
       -> publish A
       -> readiness (again)          [MUST return package A, never mint B]
       -> publish (naming A again)   [publication_already_completed, unchanged]
       -> exactly one CHGR
   ```

This is stated normatively, not merely by implication: **IWPC-REQ-197
governs independently of, and is not satisfied merely by inference from,
IWPC-REQ-024's pre-145H.1 text** — that is precisely the gap this section
closes.

### 35.5 Post-consumption readiness behavior (repairs the drafting gap in IWPC-REQ-024/082/107)

**IWPC-REQ-024 (amended in place, additive clarification, no narrowing —
mirrors the Phase 145C precedent at §32 of correcting a drafting gap
without renumbering).** Original v1.3 text described construction as
"idempotent by key, keyed on `session_id`: a second construction attempt
for a session that already has a persisted pending package SHALL return
the existing package, never rebuild it," without stating what happens once
that package is later consumed. Corrected text: `decision-session
readiness` SHALL, on its first invocation against a `Confirmed` session
with no existing package (pending or consumed), construct the
`PublicationReadinessPackage` via `PublicationHandoff.build_package` and
persist it to the Pending-Readiness Store before reporting it; **every**
subsequent invocation — whether the package remains `pending` or has since
been moved to `consumed/` by a successful publication — SHALL report the
existing, already-persisted package unchanged, including its current
disposition and, where applicable, its `record_id`; construction itself
remains idempotent by key, keyed on `session_id`, across the package's
**entire lifecycle**, not merely its pending state.

**IWPC-REQ-082 (amended in place, same discipline).** Original v1.3 text
read "one **pending** package per session; enforced at construction,
IWPC-REQ-024," a phrase 145H correctly identified as ambiguous between a
deliberate pending-only scope limiter and a mere description of directory
layout. Corrected text: **one package per session, for the session's
entire lifecycle** (pending or consumed) is enforced at construction
(IWPC-REQ-024, IWPC-REQ-197); `decision-session readiness` looks up by
`session_id` across both the pending and `consumed/` locations, while
`governance-record publish` continues to look up by `package_id` only
(the two lookup keys remain deliberately different, matching each
command's own primary input — unaffected by this correction).

**IWPC-REQ-107 (amended in place, same discipline).** Original v1.3
creation-precondition text ("no existing pending package for that
`session_id`") is corrected to "no existing package, pending or consumed,
for that `session_id`" — matching IWPC-REQ-082's corrected scope exactly.

**IWPC-REQ-198.** A session-keyed readiness lookup (the successor to
`FilesystemPendingReadinessStore.find_by_session_id`, or any future
replacement) MUST search both the pending location and the `consumed/`
location and MUST return a matching record from either; it MUST NOT
exclude a `consumed/` record from session-keyed idempotency lookups. A
package's disposition transitioning from `pending` to `consumed` SHALL
NEVER cause that package to become invisible to a future session-keyed
idempotent-construction lookup for the same `session_id`.

**IWPC-REQ-199.** `decision-session readiness`, invoked against a
`Confirmed` session whose bound package has already been consumed by a
successful publication, SHALL return that existing package's own identity
and metadata (`package_id`, `package_digest`, `built_at`,
`disposition: "consumed"`, and `record_id` where the Pending-Readiness
Store's own attempt-linkage metadata, IWPC-REQ-086/087, already carries
it) unchanged. It SHALL NOT construct a new package under any
circumstance, SHALL NOT re-derive, re-render, or reconstruct any
package-content field, and SHALL NOT mutate the existing record beyond
what IWPC-REQ-086/087 already permit (attempt-linkage/disposition
metadata only — never package content, IWPC-REQ-091, unaffected).

**IWPC-REQ-200.** No new `error_type`, exit-code class, or transport
response shape is required for IWPC-REQ-199: a `"consumed"` disposition
value was already part of `readiness`'s frozen output contract
(IWPC-REQ-023's "consumption status (pending / consumed /
none-yet-created)"), and this revision's sole change is that the lookup
now actually reaches it. `readiness`'s response continues to carry
`{"status": "success", ...}` per §8's existing output contract, unchanged.

### 35.6 Publication replay — the upstream invariant PEC-001 already assumed

**IWPC-REQ-201.** `governance-record publish`'s existing `package_id`-scoped
replay guard (IWPC-REQ-032/113, PEC-REQ-007/041/080) remains, unrevised,
the sole replay check at the publication layer, and remains sufficient:
it was never, on its own, capable of preventing H-1, because PEC-001 was
never asked to reason about session-level uniqueness and correctly does
not. IWPC-REQ-197–199 above close the gap one layer earlier, by making it
contractually and operationally impossible for a second `package_id` to
ever be minted for a `session_id` that already has one. This is the
explicit upstream invariant: **PEC-001's `package_id`-scoped replay guard
is sufficient if, and only if, IWPC-001 guarantees exactly one `package_id`
per session for the session's entire lifetime — which IWPC-REQ-197 now
does.** No change to PEC-001 is required or made (§35.10).

### 35.7 Failed and partial publication

**IWPC-REQ-202.** Restates IWPC-REQ-089 unchanged: on a failed `publish`
attempt, the package remains `pending`, unmoved; a subsequent `readiness`
call continues to find it via the pending-location lookup exactly as
before this revision — no new behavior is introduced for this case.

**IWPC-REQ-203.** Restates IWPC-REQ-154 unchanged, and explicitly
classifies it as a **recovery-required, not a replay or duplicate-
construction, case**: in the narrow interruption window between PEC-001's
own successful commit and the Pending-Readiness Store's post-success
disposition move (`pending` → `consumed/`), a `readiness` call MAY still
report `disposition: "pending"` even though a CHGR already durably exists
in PEC-001's own `PublicationRecordStore`. This is a disclosed,
pre-existing, Non-Blocking eventual-consistency gap that this revision
does not close (closing it would require a store-level compare-and-set or
cross-store transaction beyond this revision's additive, contract-only
scope) — it is not H-1 and does not reintroduce H-1's own duplicate-record
outcome, because a subsequent `publish` retry against the same
`package_id` is still correctly caught by PEC-001's own replay check
(IWPC-REQ-154's own final sentence, unchanged: "the next `publish`
invocation on that `package_id` MUST detect this via PEC-001's own
replay/idempotency-marker check ... before this store's disposition is
consulted, so a mis-ordered move never causes a double-publish"). A future
implementation MUST NOT treat a `readiness`-observed "pending" disposition
in this window as license to skip that check.

### 35.8 Backward compatibility and historical inconsistency

**IWPC-REQ-204.** A repository whose Pending-Readiness Store already
contains, from the pre-145H.1 defective implementation, more than one
readiness record (pending and/or consumed) bound to the same `session_id`
is a **historical inconsistency**, not a case IWPC-REQ-197–199 above are
required to silently resolve. A future implementation's session-keyed
lookup, on finding more than one matching record for a single
`session_id`, MUST fail closed with the existing `persistence_corrupt`
error_type (§19.1, unchanged — no new error is introduced) rather than
silently selecting one record as authoritative. This revision does not
repair any existing duplicate record and does not create or authorize any
migration tooling (restates the governing prompt's own No-Go list).

**IWPC-REQ-205.** A repository with exactly one readiness record per
session (the common case, including every session that never hit H-1)
loads and behaves normally under IWPC-REQ-197–199 with no migration and no
schema change: no field this revision adds or removes exists on
`PendingReadinessRecord`'s or `PublicationReadinessPackage`'s persisted
schema (IWPC-REQ-074/111, unaffected) — this is a lookup-scope and
idempotency-scope correction only, never a persisted-format change.

### 35.9 Normative readiness behavior matrix

**IWPC-REQ-206.** The following matrix is normative, restated here for
`decision-session readiness` specifically (the general error taxonomy at
§19.1 is unchanged; no row below introduces a new `error_type`):

| Condition | Required behavior |
|---|---|
| Confirmed session; no package exists (pending or consumed) | Construct exactly one package (IWPC-REQ-024, IWPC-REQ-107) |
| Confirmed session; matching pending package exists | Return the same package, `disposition: "pending"` (IWPC-REQ-024, unchanged) |
| Confirmed session; matching package exists, `disposition: "consumed"` | Return the same package, `disposition: "consumed"`, `record_id` populated where available; never construct a new package (IWPC-REQ-198/199, new) |
| Prior `publish` attempt failed non-terminally | Package remains `pending`; `readiness` reports it unchanged (IWPC-REQ-202) |
| Publication succeeded but the disposition move has not yet completed (IWPC-REQ-154 window) | `readiness` MAY report stale `pending`; a subsequent `publish` retry is still caught by PEC-001's own replay check (IWPC-REQ-203) |
| Wrong `--as-identity` | `identity_binding_mismatch`, exit 6 — enforced before any idempotent/cache-hit branch (IWPC-REQ-023/§34, unchanged) |
| Missing `--as-identity` | Argparse-level rejection, exit 2 (unchanged) |
| Session not yet `Confirmed` | `readiness_incomplete` (unchanged) |
| Session `Cancelled`/`Expired`/`Abandoned` before ever reaching `Confirmed` | `readiness_incomplete` (unchanged — no package was ever eligible for construction) |
| More than one matching record for one `session_id` (historical inconsistency, IWPC-REQ-204) | Fail closed, `persistence_corrupt` — no silent selection |
| Corrupted pending or consumed record | Fail closed, `persistence_corrupt` (unchanged) |

### 35.10 Cross-contract review

**IWC-001:** existing text is sufficient; no revision made. IWC-REQ-019
(Confirmation single-use) and IWC-REQ-024 (terminal session identifiers
never reused) already fully establish "at most one Human Governance Act
per session," the premise IWPC-REQ-197 builds on one layer later. IWC-001
has no jurisdiction over `PublicationReadinessPackage` persistence or
readiness-command idempotency — that is IWPC-001's own invented concept
(§3, "Pending readiness package": "a transport/persistence concept this
contract introduces, not an IWC-001 or PEC-001 concept"), so the gap could
never have been IWC-001's to close.

**PEC-001:** existing text is sufficient; no revision made. §35.6 above
states explicitly, as the requested "upstream invariant," why PEC-001's
`package_id`-scoped replay guard (PEC-REQ-007/041/080) needed no widening:
it was always correctly scoped to what PEC-001 owns (Publication
Execution, per PEC-REQ-021), and the session-level uniqueness question is,
and always was, exclusively IWPC-001's to answer, per PEC-001's own §1
governed-subject boundary ("It does not redefine ... IWC-001").

**CHGR-001:** existing text is sufficient; no revision made. §2's
definitional "the ... representation of **one** Human Governance Act"
already states the required one-Human-Governance-Act-to-one-CHGR
invariant at the definitional level; CHGR-001 has no operational hook into
the pre-publication readiness-construction layer where H-1 actually
occurred (CHGR-001 §1: "does not govern the Interactive Decision Session
layer itself"), so enforcement duty always belonged one layer earlier, at
IWPC-001, exactly where this section places it.

### 35.11 Security restatement

**IWPC-REQ-207.** This revision introduces no new bypass, force flag, or
automatic behavior: `readiness` remains read/idempotent-construction only
and never authorizes or performs publication (IWPC-REQ-010/012, unchanged);
`publish` remains the sole authorizing act (IWPC-REQ-029/030, unchanged).
Identity enforcement continues to run before every idempotent/cache-hit
branch, including the newly-reachable consumed-package branch (§34's
`_require_bound_identity`-before-cache-check discipline, restated
unchanged and independently confirmed to already cover this branch, since
`ensure_readiness_package`'s identity check runs before its
`find_readiness_package_for_session` call regardless of what that call
returns). Possession of a `session_id` alone continues to confer no
authority (IWPC-REQ-065, unchanged). A changed `package_id` cannot produce
a duplicate CHGR, because IWPC-REQ-197 now guarantees no second
`package_id` is ever minted for the same session in the first place — this
is the mechanism, not merely a restated goal.

### 35.12 Traceability

Every requirement this section adds or amends traces to H-1 directly, with
no unrelated cleanup: IWPC-REQ-197 (the invariant H-1 violated) →
IWPC-REQ-198/199/024-amended/082-amended/107-amended (the mechanism
closing the exact reproduction sequence in 145H §6.2) → IWPC-REQ-200 (no
new surface needed, confirming Option A's minimality) → IWPC-REQ-201 (why
PEC-001 needed no change, per the phase's own required cross-contract
review) → IWPC-REQ-202/203 (the two failure-adjacent cases the governing
prompt required distinguished from H-1's own defect) → IWPC-REQ-204/205
(backward compatibility for repositories already carrying H-1's own
historical duplicates) → IWPC-REQ-206 (the required normative matrix) →
IWPC-REQ-207 (security restatement confirming no new authority surface).
The expected future implementation owner is a narrowly scoped repair phase
against `FilesystemPendingReadinessStore.find_by_session_id`,
`PublicationApplicationService.ensure_readiness_package`/
`persist_readiness_package`, and `decision_session.py`'s `readiness`
handler; expected verification evidence is a repaired-behavior test
exercising exactly the "readiness → publish → readiness again" sequence
145H's own live adversarial testing used to find H-1, plus the historical-
multiple-record fail-closed case (IWPC-REQ-204).

### 35.13 Regression review

Independently reconfirmed unchanged by this revision: every command
contract in §5/§6 other than `readiness`'s own idempotency scope (§5.8);
the Output Contract (§8), Exit-Code Contract (§9, unaffected — no new
exit code), Transport Contract (§10), Transport Versioning (§11, no new
`schema_version`), the Decision-Session State Contract (§12), the
SessionRepository Contract (§13, untouched), the remainder of the Pending-
Readiness Store Contract (§14, all provisions other than IWPC-REQ-082/107
above), Artifact Binding (§15), the Confirmation Contract (§16), the
Readiness-Package Contract's other provisions (§17), the Authorization
Input Contract (§18), the Publication Invocation Contract and its error
taxonomy (§19, no new `error_type`/exit class), the Idempotency
Contract's other rows (§20, `readiness`'s own row is restated, not
contradicted — "idempotent by key (`session_id`)" now correctly applies
across the full lifecycle it always claimed to cover), the Concurrency
Contract (§21 — IWPC-REQ-143's "concurrent readiness creation" race
analysis is unaffected: two racing constructions still produce
deterministic, non-divergent content per IWPC-REQ-108; the store's
last-write-wins disposition-metadata update remains non-authority-relevant
per IWPC-REQ-147), the remainder of the Interruption and Recovery Contract
(§22, IWPC-REQ-154 restated unchanged at §35.7), the Security Contract
(§23), the Observability Contract (§24), the Dependency Contract (§25),
and the Compatibility Contract (§26). IWC-001, PEC-001, and CHGR-001 are
independently confirmed unmodified (§35.10). Runtime remains Observed /
observe / unavailable, unaffected — this is contract text only; no file
under `src/`, `tests/`, `.pcae/policy.toml`, or any path other than this
contract itself is touched by this revision.

### 35.14 Compatibility and migration

**IWPC-REQ-208.** This revision is additive per IWPC-REQ-191: no existing
`IWPC-REQ-###` identifier is renumbered, retired, or reassigned; the three
in-place textual corrections (IWPC-REQ-024, IWPC-REQ-082, IWPC-REQ-107)
close a genuine drafting ambiguity without narrowing any guarantee those
requirements previously made — mirroring the Phase 145C precedent (§32)
exactly, not the "major revision" path IWPC-REQ-191 reserves for narrowing
or removal. New identifiers begin at IWPC-REQ-197.

**IWPC-REQ-209.** No migration is required of any existing conformant
implementation that has not yet hit H-1's own defect, since this section
changes lookup *scope*, not persisted *format* (§35.8). A future
implementation phase closing H-1 in code (145H.2, not authorized by this
revision) is required to: (a) widen the session-keyed lookup to search
both pending and consumed locations (IWPC-REQ-198); (b) update
`ensure_readiness_package`/`persist_readiness_package` to report, rather
than bypass, an existing consumed match (IWPC-REQ-199); and (c) add the
historical-multiple-record fail-closed check (IWPC-REQ-204). No CLI,
transport-shape, or runtime change is required by any of the three.

---

*End of IWPC-001 v1.4.*
