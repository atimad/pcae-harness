# Phase 145A — Interactive Workflow + Publication CLI / Transport Architecture

## 0. Status and Scope

**Status:** Architecture only. No implementation. No contract revision.
No CHGR created. No lifecycle authority invoked. No production code,
contract, or schema in this repository was modified by this phase.

**Runtime posture before and after this phase (unchanged):** `pcae
runtime inspect` — State: `Observed`, Maximum capability: `observe`,
Execution availability: `unavailable`. Nothing in this document touches
a code path capable of altering that posture; the architecture proposed
below only adds an invocation surface over already-implemented,
already-frozen governance logic that writes exactly one kind of artifact
(a publication record) and otherwise performs no execution.

This document answers the question 144H (§10, §15), 144I (§14), and
144J (§12) each independently, unchangedly recommended as this
project's next step: **what is the smallest safe invocation architecture
that makes the already-implemented Interactive Workflow (IWC-001 v1.2)
and Publication (PEC-001 v1.1) pipeline reachable by a human, without
adding execution capability?** It does not implement that architecture.
Phase 145B (named in §18, not authorized here) would be the earliest
point implementation could begin, and only after the additional
governed steps §18 identifies.

---

## 1. Method

Read in full: `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`
(IWC-001 v1.2), `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`
(PEC-001 v1.1), `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
(CHGR-001), `docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
(TAMC-001), `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
(TAMPC-001), `docs/PHASE_144H_PUBLICATION_CHAPTER_RETROSPECTIVE_SYSTEM_EXECUTION_READINESS_ASSESSMENT_AND_ROADMAP_REBASELINE.md`,
`docs/PHASE_144I_STRATEGIC_ROADMAP_AND_STATUS_SYNCHRONIZATION.md`,
`docs/PHASE_144J_STRATEGIC_METADATA_SYNCHRONIZATION_AND_GENERATOR_ALIGNMENT.md`,
and `docs/PHASE_144A_PUBLICATION_EXECUTION_OWNERSHIP_ARCHITECTURE.md`
(the direct structural and substantive precedent for this document —
144A resolved *ownership* of Publication Execution; this phase resolves
*invocation* of the whole pipeline, Interactive Workflow included, which
144A's own scope explicitly excluded). Cross-checked every claim about
current implementation against source: `src/pcae/interactive_workflow/**`
(session/coordinator.py, orchestration/coordinator.py,
orchestration/models.py, publication_handoff/handoff.py,
publication_handoff/models.py, models/session.py,
persistence/repository.py), `src/pcae/governance/publication/**`
(coordinator.py, storage.py, models.py, record.py, errors.py),
`src/pcae/cli.py` (10,738 lines — subparser wiring conventions),
`src/pcae/commands/governance_record.py`, `src/pcae/commands/session.py`,
`src/pcae/commands/notifications.py`, `src/pcae/commands/advisory.py`,
`src/pcae/core/permission_broker_foundation.py`, and the forbidden-import
boundary tests (`tests/test_phase_144c_publication_coordinator.py`,
`tests/test_iwc_143o_session_coordination_publication_handoff.py`,
`tests/test_chgr_phase_separation.py`). The existing implementation is
treated as evidence of what exists, never as authority for what a CLI
should be permitted to do.

---

## 2. Current-State Invocation Gap Analysis (Governing Facts)

1. **Both subsystems are fully implemented and independently verified as
   libraries; neither has a CLI entry point.** `grep -rn
   "interactive_workflow" src/pcae/cli.py` and `grep -rn
   "PublicationCoordinator\|publication_handoff\|PublicationReadinessPackage"
   src/pcae/cli.py src/pcae/commands/*.py` all return zero matches,
   independently re-confirmed this phase and consistent with 144H's
   identical finding. 144H's own classification stands unchanged: both
   subsystems are **"Complete (as a library); Missing (as an execution
   surface)."**

2. **`SessionCoordinator.perform_publication` is a permanent
   `NotImplementedError`**, by design, not by omission
   (`session/coordinator.py:226-251`). Its docstring states there is "no
   scope under which this method could ever legitimately return normally
   on this class" — IWC-001 §18.4 (IWC-REQ-171) leaves Publication
   Handoff *execution* ownership an explicitly open question for a
   future, separately governed phase, and 144A/PEC-001 answered that
   question for the *Publication act itself* (§8) by giving it to a new,
   external `PublicationCoordinator` — never by teaching
   `SessionCoordinator` to call it. This is a hard architectural
   constraint on this phase: nothing proposed below may route publication
   through `SessionCoordinator`.

3. **`PublicationHandoff` (the class that builds a
   `PublicationReadinessPackage`) is stateless and already usable
   end-to-end** given a `Confirmed` `Session`, a complete
   `OrchestrationState`, and the referenced Evidence/Clarification/Audit/
   Preview/Confirmation artifacts (`publication_handoff/handoff.py:50-180`).
   It fails closed (`PublicationHandoffIncompleteError`) unless every
   cross-reference matches and the session is genuinely `Confirmed`. It
   never publishes, notifies, creates a CHGR, or invokes a lifecycle
   command — "those methods do not exist here" (module docstring).

4. **`PublicationCoordinator.authorize()`/`.execute()` are fully
   implemented and PEC-001-conformant**, but nothing calls them outside
   tests (`governance/publication/coordinator.py:91-197`).
   `authorize()`'s own docstring states plainly that it does not itself
   constitute a Publication Authorization Event — that requires "an
   explicit, human-operated invocation of a dedicated CLI command, which
   this phase [144C] does not implement — no CLI is in scope for 144C."
   `execute()` enforces PEC-001's fixed order (replay check → package
   validation → authorization applicability → authorization freshness →
   atomic write → idempotency-marker commit → attempt audit) and writes
   to `.pcae/publication-execution/{records,published,attempts}/` —
   **a directory distinct from `.pcae/governance-records/`**, which the
   Interactive Workflow's own `SessionRepository` interface is
   independently forbidden from touching
   (`CHGR_STORAGE_PREFIX`, `persistence/repository.py`).

5. **No `SessionRepository` implementation exists in production code.**
   The interface (`persistence/repository.py`) is deliberately
   interface-only — "that choice is deliberately deferred past Phase
   143K" (module docstring) — and the only concrete implementations
   anywhere in the repository are two test fakes
   (`tests/test_iwc_143k_session_infrastructure.py:295,325`). This means
   an Interactive Decision Session today has **no durable state across
   process invocations**: a CLI command that creates a session in one
   process cannot be resumed by a second, separate invocation until a
   concrete `SessionRepository` is built. This is a precondition gap
   this architecture must explicitly account for (§11), not a detail a
   future implementation phase can silently improvise.

6. **No storage location exists for a built-but-unpublished
   `PublicationReadinessPackage`.** `PublicationHandoff.serialize`/
   `deserialize` exist (`serialization/publication_handoff_schema.py`),
   but nothing in production code calls them to persist a package
   anywhere. If package construction and Publication Authorization are
   two separate CLI invocations (as PEC-REQ-034 requires — see §4/§9),
   the package must be durable somewhere between them. This is a second,
   distinct persistence gap from (5) and must not be conflated with it
   or with `PublicationCoordinator`'s own `.pcae/publication-execution/`
   store, which holds only *already-published* records, replay markers,
   and attempt audit trails — never a pending, unauthorized package.

7. **The single most directly load-bearing sentence in the whole
   contract corpus for this phase is PEC-REQ-034**: "The Publication
   Authorization Event SHALL originate from an explicit, human-operated
   invocation of a dedicated CLI command (e.g., `pcae governance-record
   publish <package-id>`), ratifying Phase 144A §5's Model 2 as the
   minimum viable authority boundary." This does not merely permit a CLI
   design choice — it is the ratified contract text a Publication-side
   CLI must implement to. No comparably specific sentence exists for the
   Interactive-Workflow-facing (session/decision) side; IWC-001 §16
   (Transport Independence) deliberately leaves that side's concrete
   surface unspecified, "a CLI ... implementation concern for the
   phase(s) that eventually build a specific transport, not this
   contract's concern" (IWC-001 §16.1, restated at IWC-REQ-155).

8. **The Permission Broker (`permission_broker_foundation.py`) is not,
   and cannot yet be, a gate in front of either subsystem.** Every
   decision it returns — including `ALLOW` — carries
   `implementation_status="execution_unavailable"` (module-level
   invariant, `PermissionBroker.evaluate`, line 727-728), because
   `COMP-002` (the execution boundary) does not exist. Its known action
   vocabulary (`KNOWN_ACTION_TYPES`) has no `publication` or
   `interactive_workflow` entry. Routing a new command through it today
   would produce, at best, an advisory simulation-only decision with no
   binding effect — worth exposing for observability (§16), never
   presented as a gate.

9. **The strongest in-repository CLI-design precedent for "connect a
   thin CLI layer to an already-frozen, already-implemented governance
   artifact without reimplementing its logic" is
   `src/pcae/commands/governance_record.py`** (143E/143F): its own
   docstring states it "implements only the CLI layer ... All business
   logic lives in [the inspection/verification] modules and is not
   duplicated here," and it is explicitly documented as read-only today,
   "no `create`/`confirm`/`publish` command ... and none is planned for
   this increment" — i.e., this repository already anticipated that a
   `publish` verb would eventually be added to this exact command family,
   just not yet.

---

## 3. Central Architectural Question — Answer

**What is the smallest safe invocation architecture that makes the
already implemented Interactive Workflow and Publication pipeline
reachable by a user, while preserving all existing authority, lifecycle,
publication, and runtime boundaries?**

It is a **two-command-family CLI surface** with no new application-
service layer, no new persistence authority beyond two narrowly-scoped,
non-authoritative session/package stores, and no gate collapsing:

- A new top-level command family, `pcae decision-session`, whose verbs
  are a **thin, 1:1 wrapper over `SessionCoordinator` +
  `WorkflowOrchestrator` + `PublicationHandoff`**, covering session
  creation through Confirmation and (mechanically, not
  discretionarily) Publication Readiness Package construction. This
  command family owns **invocation, interaction, and confirmation**. It
  never authorizes and never publishes.

- One new verb, `publish`, added to the **existing**
  `pcae governance-record` command family exactly as PEC-REQ-034 names
  it, a thin wrapper over `PublicationCoordinator.authorize()` +
  `.execute()`. This verb owns **authorization and publication**. It
  never interacts with a human decision, never displays or collects a
  Preview, never touches `interactive_workflow` internals.

These two families are invoked as two, temporally and procedurally
separate human acts — never chained automatically, never triggerable
by a single flag — which is the CLI-level realization of PEC-REQ-011/012
("no automatic publication ... reaching Confirmed is necessary but never
sufficient to publish") and of IWC-001's five-state-class separation
(§11.1). **Invocation** is "a CLI process starts and a subcommand
executes" — authority-neutral by construction (no subcommand's mere
existence or successful parse implies any governance fact).
**Interaction** is the human-facing exchange of Decision Subject,
options, evidence, and clarification that `decision-session` stages
mediate, verbatim-delegated to already-frozen IWC-001 machinery.
**Confirmation** is IWC-001's own non-defaultable act (§7, §10.7),
performed inside `decision-session confirm` and never elsewhere.
**Authorization** is PEC-001's own distinct act (§6), performed only by
running `governance-record publish` and never inferable from
Confirmation, package readiness, or CLI argument presence alone
(PEC-REQ-092). **Publication** is `PublicationCoordinator.execute()`'s
atomic write, already fully implemented, invoked only as a direct
consequence of a successful Authorization Event. **Execution** — in the
sense this repository reserves the word for (shell/backend/repository-
mutation capability governed by the Permission Broker and Runtime
Enforcement chapters) — is untouched by any of this: Publication writes
exactly one append-only, schema-shaped JSON record under
`.pcae/publication-execution/`, invokes no shell, no adapter, no backend,
and changes no runtime capability flag.

---

## 4. Invocation Model Evaluation

### Model A — Single Composite CLI Command

One command owns session creation through Publication, end to end.

- **Usability:** highest — one command to learn.
- **Ownership clarity:** poor — the same process, and plausibly the same
  function, would hold both the Confirmation act and (if it also
  published) the Authorization Event, which directly violates
  PEC-REQ-011/012 and IWC-001's insistence that these facts never be
  substitutable (§11.1, IWC-REQ-113/114). Even if implemented as two
  sequential internal steps inside one command invocation, a single
  `pcae decide` process reaching Confirmation and then immediately
  publishing collapses "the user confirmed" and "an authorized principal
  separately authorized publication" into one human act — exactly the
  A8 adversarial scenario ("CLI invocation treated as a standing
  authorization grant") PEC-REQ-092 exists to foreclose.
- **Interruption recovery:** poor — a long single-process flow spanning
  evidence review, clarification, and Preview confirmation is fragile to
  interruption (terminal closed, session timeout) with no defined resume
  point short of restarting from `Created`.
- **Auditability:** poor — collapses two contractually distinct human
  acts into one audit event, undermining CHGR-001 §10's "who/how/what-
  presented/what-selected/exact-preview-verbatim/when" provenance
  granularity.
- **Coupling:** high — a single command module would need direct
  knowledge of both `interactive_workflow` and `governance.publication`
  internals, in tension with the forbidden-import boundary tests (§15).

**Rejected.** Merging Confirmation and Authorization into one invocation
is not a usability trade-off this architecture is free to make — it is
foreclosed by contract text (PEC-REQ-011/012/092, IWC-001 §11.1).

### Model B — Staged CLI Commands

Separate commands for session creation, preview, confirmation,
readiness-package creation, authorization, and publication (six or more
discrete verbs).

- **Explicitness:** highest — every governance-relevant transition is
  its own auditable CLI invocation.
- **Resumability:** good, contingent entirely on a durable
  `SessionRepository` existing (§2.5) — without it, every command after
  the first would need to re-derive full session state from an argument
  the operator would have to re-supply by hand, which is unworkable.
- **Persistence requirements:** highest of any model — a session file
  update on every single verb, six or more times per decision.
- **Stale-artifact risk:** meaningfully higher — six separately-timed
  artifacts (session-after-evidence, session-after-clarification,
  session-after-preview, session-after-confirmation, standalone
  readiness package, authorization event) each need their own staleness/
  freshness checks; PEC-001 §6 already defines one such check
  (`_validate_authorization_freshness`) for exactly one boundary
  (package vs. authorization) — Model B would need to either invent
  several more or accept looser staleness guarantees at the others.
- **Operational complexity:** highest — an operator must remember and
  correctly sequence six-plus commands per decision, with more
  opportunities to invoke the wrong one out of order (mitigated only by
  `WorkflowOrchestrator`'s own `_require_next` stage-ordering guard,
  which would reject an out-of-order call, but only after the operator
  has already spent the effort of a wrong invocation).

**Rejected as the outer shape**, but not wasted: Model B's per-stage
explicitness is exactly right *inside* the Interactive-Workflow side
(evidence → clarification → preview → confirmation legitimately are, and
should remain, separately callable — see §6), it is simply wrong to
extend it across the Confirmation/Authorization boundary, where a
different model is contractually required (Model C, below).

### Model C — Hybrid Command Flow

One Interactive Workflow command flow (which may itself be internally
staged, per Model B's insight) followed by a distinct Publication
command.

- **Preserves the confirmation/readiness/authorization distinction
  exactly as PEC-REQ-034 requires**, at the one boundary where the
  contract text is unambiguous: `decision-session` culminates in
  Confirmation + (mechanical) readiness-package construction;
  `governance-record publish` is the sole Authorization Event source.
- **Matches the existing precedent** almost exactly: 144A already
  evaluated and PEC-001 already froze this precise division at the
  Publication boundary (PEC-REQ-034/036); this phase's only extension is
  applying the same "thin CLI, dedicated coordinator class" discipline
  to the Interactive-Workflow-facing side, which had no prior CLI
  architecture at all.
- **Bounded persistence:** exactly two narrowly-scoped stores are needed
  (a session store, a pending-readiness-package store — §11), not six.
- **Operational complexity:** moderate — an operator runs a bounded,
  ordered sequence of `decision-session` subcommands (itself internally
  guarded by `WorkflowOrchestrator`'s stage-ordering) to reach a
  `package_id`, then a single, separately-invoked `publish` command.

**Selected** (elaborated in §5–§9).

### Model D — Transport-Neutral Application Service

A new application-service boundary, callable by CLI, a future local API,
a future UI, or automation adapters — CLI becomes one thin adapter over
that service rather than talking to `SessionCoordinator`/
`WorkflowOrchestrator`/`PublicationHandoff`/`PublicationCoordinator`
directly.

- IWC-001 §16 (Transport Independence) already requires the *contract*
  to be transport-neutral, and it already is — every requirement in
  IWC-001 is written in terms of session state and human acts, never CLI
  syntax. That neutrality is a property of the **contract and the
  existing subsystem classes**, not something a new service layer would
  add.
- The four classes this phase would wire a CLI to
  (`SessionCoordinator`, `WorkflowOrchestrator`, `PublicationHandoff`,
  `PublicationCoordinator`) are **already** transport-agnostic — none of
  them imports `argparse`, reads `sys.argv`, or performs any CLI-specific
  I/O. They already *are* the application boundary Model D proposes to
  build again above them.
- Introducing a new service layer today would have exactly one consumer
  (the CLI itself, since no second transport is being built in this
  phase or authorized for a future one), which is the textbook case of
  premature abstraction this phase's own scope boundary warns against
  ("Balance future extensibility against premature abstraction").
  A wrapper with one caller adds an indirection cost (a fifth layer to
  reason about, test, and keep in sync with the four real subsystems) for
  zero present benefit.
- It would also risk becoming a **second, informal, unauthorized**
  boundary athwart the existing forbidden-import tests (§15) — those
  tests scope exactly which packages `governance/publication/**` and
  `interactive_workflow/**` may import; a new service module sitting
  "above" both would need its own governed boundary contract to avoid
  quietly becoming the place logic actually lives (the same anti-pattern
  144A's own Option D1 rejected for folding Publication logic into the
  CLI layer, generalized one layer up).

**Rejected for now, not permanently.** If a second transport (a local
API, a TUI, a future UI) is ever separately, governedly authorized, the
four existing subsystem classes' own transport-neutral public APIs
(`SessionCoordinator`, `WorkflowOrchestrator`, `PublicationHandoff`,
`PublicationCoordinator`) are already sufficient extraction points for
that future work — a thin CLI adapter and a thin future-transport
adapter could both call them directly with no shared service layer
required, exactly as `governance_record.py`'s existing "CLI wires,
business logic lives elsewhere" discipline already demonstrates. Should
a second transport ever need logic beyond what those four classes
expose, *that* would be the governed trigger to introduce a Model-D-style
service boundary — not a name for something to build speculatively now.

---

## 5. Selected Architecture

Model C (Hybrid), realized as:

```text
Human operator
    │
    │  pcae decision-session create / evidence / clarify / preview / confirm
    ▼
┌─────────────────────────────────────────────────────────────┐
│  CLI adapter: src/pcae/commands/decision_session.py (new)   │
│  thin: argparse → bounded I/O → delegate → render → exit code│
└───────────────┬───────────────────────────────────────────--┘
                │ calls directly, no new layer between
                ▼
  SessionCoordinator → WorkflowOrchestrator → (7 collaborators,
  each already implemented: evidence/clarification/preview/
  confirmation/audit/state_machine/persistence)
                │
                │  on reaching Confirmed: PublicationHandoff.build_package()
                ▼
     PublicationReadinessPackage  ──serialize──▶  new pending-package
                                                    store (§11)
                                                        │
                                                        │ package_id printed
                                                        │ to operator
                                                        ▼
Human operator (separate act, may be a different
process, session, or even different authorized principal)
    │
    │  pcae governance-record publish <package-id> --operator-id <id>
    ▼
┌─────────────────────────────────────────────────────────────┐
│ CLI adapter: extends existing src/pcae/commands/             │
│ governance_record.py with run_governance_record_publish      │
└───────────────┬───────────────────────────────────────────--┘
                │ calls directly, no new layer
                ▼
     PublicationCoordinator.authorize() → .execute()
                │
                ▼
      .pcae/publication-execution/{records,published,attempts}/
      (already implemented, unchanged by this phase)
```

No new application-service class. No new dependency on the Permission
Broker as a gate (it remains reachable only in its existing advisory
capacity — §16). No change to `SessionCoordinator.perform_publication`
(still permanently `NotImplementedError` — publication never routes
through it). No new import from `governance/publication/**` into any
`interactive_workflow` submodule, or vice versa, beyond the one already-
permitted `PublicationHandoff`/`PublicationReadinessPackage` coupling
(§15).

---

## 6. CLI Command Architecture

### 6.1 Command hierarchy and names

```
pcae decision-session create      --template-ref <id> --subject-ref <id> --owner-id <id> [--json]
pcae decision-session evidence    <session-id> --declare <evidence-id> [--declare <evidence-id> ...] [--json]
pcae decision-session clarify     <session-id> --question <text> --answer <text> [--json]
pcae decision-session preview     <session-id> [--json]
pcae decision-session confirm     <session-id> --preview-digest <digest> --statement <text> [--json]
pcae decision-session status      <session-id> [--json]
pcae decision-session cancel      <session-id> --reason <text> [--json]

pcae governance-record publish    <package-id> --operator-id <id> [--json]
```

`decision-session` is a deliberately new top-level noun, not a
`session`-family subcommand — `pcae session` already means the
PCAE-agent-workflow bootstrap/handoff snapshot (`.pcae/session.json`,
`src/pcae/commands/session.py`), a structurally unrelated concept (agent
lock/task/provenance state, not a governed human decision). Reusing
`session` for both would violate IWC-001 §11.1's own insistence that
distinct state classes never share a name a reader could conflate.
`publish` is added to the existing `governance-record` family exactly as
PEC-REQ-034 names it, not as a new top-level noun, since it operates on
the same conceptual artifact family (`governance-record inspect`/
`verify` already read CHGR-shaped output; `publish` is the first command
in that family that writes one).

### 6.2 Arguments, input sources, output formats

- Every leaf command accepts `--json` (boolean, `action="store_true"`),
  following the universal convention already used throughout
  `src/pcae/cli.py`: a single dict payload, `json.dumps(data, indent=2,
  sort_keys=True)` when set, else a fixed-field-order human-readable
  rendering — no new output-formatting abstraction introduced,
  consistent with every existing command in this repository.
- `--template-ref`/`--subject-ref`/`--owner-id` on `create`: required,
  no defaults — nothing about template or subject selection may be
  inferred (IWC-REQ-051).
- `evidence --declare`: repeatable flag, one evidence-id reference per
  occurrence — never a bulk/glob argument, so each declared item is
  individually traceable in the audit trail.
- `preview`: no mutating arguments; always renders and prints the exact,
  full current Preview content to stdout (or the `--json` payload's
  `preview_content` field) — **never gated behind a flag that could
  suppress it**, directly enforcing IWC-REQ-112/CHGR-REQ-065 ("No
  command interface SHALL provide a flag or mode that skips displaying
  the exact Preview content before Confirmation"). This holds in both
  human and `--json` modes: JSON mode still includes the full
  `preview_content`/`preview_digest` fields, so an automation adapter
  consuming JSON output has still been shown, structurally, the exact
  content — it cannot request a "skip preview" mode because no such flag
  exists on this command at all.
- `confirm --preview-digest <digest> --statement <text>`: **both
  required, no default.** The command fails closed
  (`ConfirmationDigestMismatchError` → exit 3, see §12) unless
  `--preview-digest` matches the session's current, live Preview Digest
  exactly (re-fetched server-side, never trusted from the argument alone
  — the argument is an assertion the operator must have actually seen
  the right content, checked against ground truth, not a bypass).
  `--statement` carries the non-passive acknowledgement text
  (IWC-REQ-102/103, CHGR-REQ-063-066) — an empty or default value is
  rejected, never silently accepted.
- `publish <package-id> --operator-id <id>`: both required. No `--force`,
  no `--skip-checks` flag of any kind exists on this command — PEC-001's
  fixed validation order (§2.4) always runs in full.

### 6.3 Exit codes

Extends, rather than replaces, this repository's existing `0`=success /
`1`=handled-failure convention with a small number of additional
stable, documented non-zero codes specific to this command family only
(existing commands elsewhere in the CLI are unaffected):

| Code | Meaning | Example |
|---|---|---|
| 0 | Success | Session created; preview shown; package built and printed; publication succeeded |
| 1 | Generic handled domain failure | Malformed template-ref; unknown session-id |
| 2 | Out-of-sequence stage | `confirm` called before `preview`; `WorkflowOrchestrator`'s `_require_next` rejection |
| 3 | Confirmation binding failure | `--preview-digest` does not match current live digest — stale or wrong content |
| 4 | Replay / already-consumed | `publish` invoked twice on the same `package-id` (`AuthorizationReplayError`) |
| 5 | Stale authorization | `publish` invoked with an authorization timestamp older than the package's `built_at` (`StaleAuthorizationError`) |

This mirrors, at the CLI layer, distinctions PEC-001's own error
hierarchy (§12) already makes at the library layer — no new error
taxonomy is invented, the CLI only assigns stable exit codes to
already-existing exception types.

### 6.4 Interactive vs. non-interactive, machine-readable mode

Every command is fully non-interactive-capable (all inputs are flags, no
required stdin prompt) — this is deliberate: it makes automation-adapter
use possible (Compatibility §6.5 below) without requiring a TTY, while
never weakening the Preview-before-Confirmation requirement (§6.2,
`preview`'s output is unconditional regardless of interactivity).
`--json` is the machine-readable mode; the same command, same exit code,
same underlying validation runs whether or not `--json` is passed — JSON
is a rendering choice, never a different code path (matching
`governance_record.py`'s existing pattern exactly).

### 6.5 Dry-run / preview semantics

`decision-session preview` **is** the contract-mandated preview step,
not a CLI dry-run convenience — it has no side effect on session state
beyond advancing the orchestration stage counter (`stage_preview_construction`/
`stage_preview_validation`, already implemented,
`orchestration/coordinator.py:230-280`) and is safe to invoke multiple
times (idempotent — it always renders the current live content, never
mutates decision data). No separate "`--dry-run`" flag is introduced
anywhere in this family: `publish` either fully succeeds or fully fails
per PEC-001's atomic-write discipline (§13); there is no partial or
speculative publish to preview.

---

## 7. Transport Contract Architecture

### 7.1 Request/response objects, serialization

No new serialization format is introduced. Every `decision-session`
subcommand's request is exactly its parsed `argparse.Namespace`
(unchanged repository convention); every response is exactly the
already-existing dataclass each underlying method already returns
(`Session`, `OrchestrationState`, `Preview`, `ConfirmationResponse`,
`PublicationReadinessPackage`, `PublicationAuthorizationEvent`,
`PublicationExecutionResult`), rendered via each artifact's own
already-implemented `serialization/*_schema.py` `to_payload()`
converter for `--json` mode, or a fixed-field human-readable formatter
for text mode — the same pattern `governance_record.py` already uses.
**No new schema is authored by this phase**; every artifact this CLI
would ever emit already has a frozen `to_payload`/`from_payload` pair
(§2, precedent items). This is a direct consequence of the "thin CLI"
discipline (§5): a transport layer with no logic of its own has no data
shapes of its own to invent.

### 7.2 Versioning

Every emitted payload already carries the artifact's own
`schema_version` field (`Session.schema_version`,
`OrchestrationState.schema_version`,
`PublicationReadinessPackage.schema_version`, etc.) — the CLI adds no
version field of its own and performs no version translation; it is a
pure pass-through. A future schema-version bump to any of these
dataclasses is entirely a matter for that dataclass's own governed
amendment process (IWC-001 §17, PEC-001's own revision discipline),
invisible to this CLI layer, which never branches on version number.

### 7.3 Validation

All validation is delegated — the CLI performs only argparse-level type/
presence checks (a string is present, a flag was set) and one bounded-
read check on any file-path argument (mirroring
`governance_record.py`'s `_read_artifact`, §2 item 9); every
governance-meaningful validation (state legality, digest match, package
completeness, authorization freshness) is performed exclusively by the
already-implemented subsystem classes. The CLI never re-implements or
duplicates a check any of the four subsystem classes already performs —
this is the same discipline `governance_record.py`'s own docstring
states explicitly.

### 7.4 Error envelopes

`--json` mode on any command that ends in a handled failure emits a
single fixed-shape error object:

```json
{
  "status": "error",
  "error_type": "<snake_case_category>",
  "message": "<safe, human-readable summary, no raw stack trace, no internal path>",
  "session_id": "<if applicable>",
  "package_id": "<if applicable>"
}
```

`error_type` is drawn from a small, stable, closed vocabulary mapped
1:1 from existing exception classes (`SessionNotFoundError`→
`session_not_found`, `PublicationHandoffIncompleteError`→
`readiness_incomplete`, `AuthorizationReplayError`→
`authorization_replay`, `StaleAuthorizationError`→
`stale_authorization`, `MissingAuthorizationError`→
`missing_authorization`, `InvalidAuthorizationError`→
`invalid_authorization`, `InvalidPublicationPackageError`→
`invalid_package`, plus a generic `domain_error` catch-all) — never a
raw Python exception class name or traceback, satisfying the Security
Assessment's redaction requirement (§14).

### 7.5 Provenance retention, correlation identifiers

Every `decision-session` command's response includes the session's own
`session_id` (`CDS-<uuid4>`, already IWC-001-structural); every
`governance-record publish` response includes `package_id` and, on
success, the newly-minted `record_id` (`chgr-<uuid4>`, already
PEC-001-structural). No new correlation-id scheme is introduced — the
existing identifiers are already sufficient to correlate a CLI
invocation's output with the durable artifact it produced or consumed,
and every artifact already carries the provenance fields CHGR-001 §10
requires (verbatim decision content, preview content, confirmation
statement/timestamp — carried since Phase 144E/144F, §2 item 3's
package fields).

### 7.6 Retry semantics, idempotency, interruption handling

See §13 (dedicated section) — governed entirely by the already-
implemented idempotency/replay machinery in
`PublicationCoordinator.execute()` (PEC-REQ-007/008/051) and, on the
session side, by the new session-store's own read-modify-write
discipline (§11). No new retry logic is introduced at the CLI layer; a
failed CLI invocation is simply re-run by the operator, and the
underlying subsystem's own idempotency guarantees determine whether the
retry is safe (it always is, by construction — replay is explicitly
detected and rejected, never silently re-applied).

### 7.7 Artifact transport: in-memory, file, or lifecycle-owned?

Neither. **Two new, narrowly-scoped, non-authoritative filesystem stores
are introduced** (§11) — this is an explicit, justified exception to
"do not introduce a new persistence authority without explicit
justification," because:

- No existing persistence authority fits: `.pcae/governance-records/` is
  reserved for records the Interactive Workflow's own `SessionRepository`
  interface is contractually forbidden to write to
  (`CHGR_STORAGE_PREFIX`); `.pcae/publication-execution/` is reserved,
  by `PublicationCoordinator`'s own design, for already-published
  records, replay markers, and attempt audits — never a pending,
  unauthorized session or package.
- Both new stores hold **data, not authority** — a session file records
  "what was entered so far," never "what is authorized"; a pending-
  package file records "what a Confirmed session produced," never "what
  may be published." Neither store's presence, format, or content
  establishes any governance fact by itself (consistent with CHGR-001
  §11's "authority derives solely from the valid human governance act,"
  never from storage location or presence).
- Both already have a designed, currently-unimplemented interface point
  to satisfy: the session store implements the existing
  `SessionRepository` ABC (§2 item 5) rather than inventing a new
  interface; the pending-package store is new (no such interface
  existed before this phase, because nothing needed to persist a
  `PublicationReadinessPackage` before this phase's CLI would need to)
  but is scoped to exactly one artifact type with the same
  serialize/deserialize pair `PublicationHandoff` already exposes.

---

## 8. Orchestration Ownership Matrix

| Responsibility | Owner | Notes |
|---|---|---|
| Session initialization | `SessionCoordinator.create_session` | Unchanged; CLI supplies owner/template/subject refs only |
| Decision-input collection (evidence declaration) | `WorkflowOrchestrator.stage_evidence_availability` via `EvidenceCoordinator` | CLI passes declared evidence-id list through unmodified |
| Clarification lifecycle | `WorkflowOrchestrator.stage_clarification_lifecycle` via `ClarificationController` | CLI passes question/answer text through unmodified |
| Option-set validation | `WorkflowOrchestrator` + `Preview` builder (rejects if options are missing/malformed) | CLI never inspects or edits the option set |
| Preview generation | `WorkflowOrchestrator.stage_preview_construction`/`stage_preview_validation` via `PreviewBuilder` | CLI only renders the returned `Preview` object; builds nothing |
| Confirmation collection | `WorkflowOrchestrator.stage_confirmation_request`/`stage_confirmation_validation` via `ConfirmationController` | CLI supplies digest + statement; controller performs the binding check |
| Readiness-package construction | `PublicationHandoff.build_package` | Invoked once, automatically, by the CLI adapter immediately after a successful `stage_confirmation_validation` — mechanical, not discretionary (§3); never re-invoked for the same session |
| Authorization-event acceptance | `PublicationCoordinator.authorize` | Invoked only by `governance-record publish`; never by any `decision-session` command |
| Publication invocation | `PublicationCoordinator.execute` | Same command, immediately following a successful `authorize` call, within one process |
| Publication-result presentation | CLI adapter (`governance_record.py`'s existing rendering pattern) | Pure rendering of `PublicationExecutionResult`; no new logic |
| Interruption recovery | New session store (read-modify-write; §11) | A session/orchestration state is always in exactly one of the ten/eight defined states on disk; recovery = re-run `decision-session status <id>` and resume from the returned `next_stage` |
| Replay detection | `PublicationCoordinator._check_replay` (publication side); new session store's own package-consumed marker (readiness side, §11/§13) | Both already-atomic or newly-specified as atomic; no new detection logic invented beyond what §13 specifies |
| Retry coordination | Operator, via CLI re-invocation | No automatic retry anywhere in this architecture (consistent with "no automatic publication," PEC-REQ-011) |

No responsibility above has more than one authoritative owner, and every
owner is either an already-existing class (unchanged) or a narrowly new
store described fully in §11 — no responsibility is left ambiguously
shared between the CLI adapter and a subsystem class.

---

## 9. Confirmation and Authorization Separation Analysis

The chain this architecture must demonstrate, restated from the
governing prompt:

```text
Confirmation ≠ Publication readiness ≠ Authorization ≠ Publication ≠ Engineering execution
```

- **The user saw the preview:** enforced structurally, not by
  convention — `decision-session confirm` requires `--preview-digest`
  to match the session's live digest (§6.2); the *only* way to obtain a
  valid, current digest is to have run `decision-session preview`,
  which unconditionally prints the exact content (§6.2, §6.5). There is
  no path to a valid digest that does not pass through seeing the
  content.
- **The user confirmed the represented decision:** `ConfirmationController`
  (already implemented, IWC-001 §10.7-conformant) validates the
  `--statement` is a genuine, non-default, non-empty acknowledgement
  bound to that exact digest — the CLI adds no independent confirmation
  logic, it only transports the operator's input to the existing
  validator.
- **A readiness package was constructed:** automatic and mechanical
  immediately after Confirmation succeeds (§8) — this is *readiness*,
  never *authorization* (PEC-REQ-002/009/028); the CLI's own output at
  this point explicitly states, in both text and `--json` modes, that
  the package is **not yet published and requires a separate `publish`
  invocation** (§16 disclosure requirement).
- **An authorized principal separately authorized publication:**
  `governance-record publish` is a structurally separate command
  (different top-level noun, `governance-record` not
  `decision-session`), requiring its own `--operator-id`, invocable in
  a different process, at a different time, by a different person than
  whoever ran `decision-session confirm` — nothing in this architecture
  requires or even checks that the same identity performed both acts
  (§10). This is the literal CLI-level realization of PEC-REQ-004's
  "explicit human-operated invocation of a dedicated CLI command."
- **Only then may the Publication Coordinator publish:**
  `PublicationCoordinator.execute()` structurally requires a non-None
  `PublicationAuthorizationEvent` (`MissingAuthorizationError` if
  absent, §2 item 4) — there is no code path in this architecture that
  reaches `execute()` without first constructing that event via
  `authorize()`, itself only reachable through the `publish` command.

**Architectures that could accidentally collapse these steps, and why
each is excluded:**

- A `decision-session confirm --publish` flag (Model A's flaw,
  reintroduced narrowly): excluded by design — no such flag exists on
  `confirm` (§6.2); the only flags `confirm` accepts are
  `--preview-digest`/`--statement`.
- A `publish` command that defaults `--operator-id` to the CLI's
  ambient identity (OS user, git config) when omitted: excluded — both
  `publish`'s arguments are required with no default (§6.2), consistent
  with PEC-REQ-045/046 ("Authorization SHALL NEVER be synthesized by
  software").
- A pending-package store keyed such that the *most recently confirmed*
  package is published if no `--package-id` is given: excluded —
  `publish` always requires an explicit `<package-id>` positional
  argument naming exactly one package (mirroring PEC-REQ-040, "an
  Authorization Event names exactly one package — never a class, batch,
  or future set").
- A CI/automation wrapper script that runs `decision-session confirm`
  immediately followed by `governance-record publish` in the same
  invocation: this is explicitly out of scope for this architecture to
  prevent at the OS level (a shell script can always chain two
  commands), but the architecture ensures it can never be *silent* or
  *implicit* — both commands still individually require their own
  distinct, explicit arguments and both still individually appear in
  the audit trail as two separate acts (§16); no single-flag shortcut
  exists inside the CLI itself to make such chaining easier than typing
  both commands out.

---

## 10. Identity and Authority Input Model

| Identity role | Where it enters | Same as another role? | Who validates structure | Who evaluates authority | Who merely transports |
|---|---|---|---|---|---|
| Decision-maker identity | `decision-session create --owner-id` | May coincide with confirmer (usually does — same operator runs the session) | `SessionCoordinator.create_session` (non-empty, well-formed) | **Nobody, by design** — see below | CLI |
| Confirmer identity | Implicit: whoever's terminal/process runs `decision-session confirm` | Same session owner, enforced structurally (`session/identity.py` — only the identity bound at creation may resume/act on a session, IWC-REQ-036/037) | `SessionCoordinator`'s ownership-binding check | Nobody | CLI |
| Authorizing principal | `governance-record publish --operator-id` | **Must remain logically distinct from decision-maker/confirmer** — nothing enforces they differ, but nothing conflates them either; the architecture treats them as independent inputs on independent commands | `PublicationCoordinator.authorize` (non-empty `operator_id`) | Nobody | CLI |
| Caller/transport identity | OS process owner, shell environment | Structurally unrelated to any of the above — never read by any command in this family | N/A | N/A | N/A (not collected at all) |
| Authority-basis evidence | `decision_maker_identity_evidence` field, already present on `PublicationReadinessPackage` (from IWC-001 §26/Phase 144E) | Carried verbatim from whatever the session captured | `PublicationHandoff.build_package`'s completeness check (presence only) | **Nobody** — see below | CLI (pass-through only, never generated) |

**Critical, explicit finding:** this architecture, like every contract
governing it, **validates structure but never evaluates authority in
the sense of "was this person actually entitled to make this decision."**
CHGR-001 §17 (CHGR-REQ-149, restated by PEC-REQ-032) is unambiguous: "No
agent, including one producing a future implementation of this contract,
may treat this contract or any implementation of it as self-authorizing
that agent to mint, confirm, or publish a CHGR on a human's behalf" — and
no existing component (`TemplateDefinition` or any decision-template
model) carries an `eligible_authority` field to check against in the
first place (independently confirmed: `record.py`'s own
`build_publication_record` leaves `authority_basis_claimed`
unpopulated, self-disclosed as a `limitations` field). **This CLI
architecture must not, and does not, invent an authority-evaluation
step that does not exist upstream** — `--operator-id` and `--owner-id`
are captured, structurally validated (non-empty, well-formed), and
transported into provenance; they are never checked against a role,
permission list, or eligibility rule, because no governed contract in
this repository defines one yet. Any future work to add real authority
*evaluation* (as opposed to identity *capture*) would be a new,
separately governed contract extension — explicitly out of this phase's
scope and not silently assumed by any command name or flag here.

No CLI flag or authenticated transport identity may by itself establish
governance authority beyond what IWC-001/CHGR-001/PEC-001 already
define an act (Confirmation, Authorization) as establishing — this
architecture adds no new authority source.

---

## 11. Session and State Model

**Two new, narrowly-scoped stores; no lifecycle-owned session state; no
fully-in-memory operation** (a CLI process exits between an operator's
own real-world thinking/decision time — evidence review, clarification,
reading the Preview — so in-memory-only is not viable for this
transport, unlike, say, a single long-running TUI process might allow).

### 11.1 Decision Session Store

- **Implements the existing `SessionRepository` ABC** (§2 item 5) —
  fills the interface gap, invents no new one. Concrete backend:
  filesystem JSON, one file per session, under a new path
  `.pcae/decision-sessions/<session_id>.json`, distinct from both
  `.pcae/governance-records/` (forbidden to `SessionRepository` by its
  own interface contract) and `.pcae/publication-execution/`
  (Publication Coordinator's own store).
- Each write is atomic (temp file + `os.replace`, matching
  `PublicationRecordStore`'s own already-proven pattern in
  `storage.py:42-56` — reused as precedent, not imported directly, to
  avoid a cross-package dependency the boundary tests would flag, §15).
- Content is exactly the `Session` + `OrchestrationState` dataclasses'
  own `to_payload()` output (§7.1) — the store holds serialized
  artifacts, never re-derives or duplicates their fields.
- **Ownership/ACL enforcement remains entirely `SessionCoordinator`'s
  job** (already implemented, `session/identity.py`) — the store itself
  performs no identity check; it is pure at-rest data.

### 11.2 Pending Publication-Readiness-Package Store

- New (no existing interface to fill — §2 item 6), but minimal: one file
  per package under `.pcae/decision-sessions/pending-packages/<package_id>.json`,
  written once by the `decision-session confirm` CLI adapter immediately
  after a successful `PublicationHandoff.build_package` call, using
  `PublicationHandoff`'s own already-implemented `serialize()`.
- Read once by `governance-record publish`, which — on successful
  publication — **moves (not copies) the file to a `consumed/`
  subdirectory** rather than deleting it, so a duplicate `publish`
  invocation against the same `package-id` still finds *something*
  (allowing a clear "already published, see record `<record_id>`"
  message, §13) instead of a bare "not found," and so the pending store
  never silently loses the record of what a Confirmed session actually
  produced, satisfying CHGR-001 §10's provenance-retention spirit even
  before the record reaches `.pcae/publication-execution/`.
- Holds no authority — see §7.7's justification.

### 11.3 Interruption, restart, stale-session detection

- Interruption at any point before Confirmed: the session file on disk
  reflects the last successfully completed stage; `decision-session
  status <id>` reads it back and reports `next_stage` (from
  `OrchestrationState.next_stage`, already implemented) — resumption is
  simply invoking the next appropriate subcommand.
- No time-based expiry is introduced by this architecture — IWC-001's
  own `Expired` terminal state (§4.4) already exists as a defined exit;
  this CLI does not add a second, competing staleness mechanism. A
  session's staleness is a governance fact the existing state machine
  already owns, not something new for the CLI layer to compute.
- **Duplicate confirmation:** `WorkflowOrchestrator`'s
  `stage_confirmation_validation` is itself a `_require_next`-gated,
  single-shot stage — a second `confirm` invocation on an
  already-`Confirmed` session is rejected at the orchestration layer
  (exit code 2, §6.3), not newly handled by the CLI.
- **Replay:** see §13.
- **Concurrent invocation:** two processes racing to write the same
  session file — mitigated by the same atomic-write discipline as
  `PublicationRecordStore` (§11.1); a losing writer's `os.replace` still
  succeeds atomically but may overwrite a concurrent legitimate update.
  This is an accepted, disclosed limitation (not a new one this phase
  introduces — `SessionRepository`'s own interface, unread by this
  research as offering any locking primitive, does not promise
  cross-process mutual exclusion; a future hardening phase could add a
  file lock, named in §18 as a candidate, not solved here).
- **Abandoned sessions, cleanup:** no automatic cleanup is introduced —
  consistent with "no automatic" anything in this architecture; an
  operator-run `decision-session cancel <id>` transitions explicitly to
  `Cancelled` (already a defined terminal state); files for terminal
  sessions are retained indefinitely (matching this repository's general
  append-only-audit posture, e.g. `PublicationRecordStore`'s own
  `attempts/` directory), with pruning (if ever needed) left to a future,
  separately justified housekeeping phase.

### 11.4 Minimality check

This is the minimum state model that makes Model C possible at all: one
store for "what a human has entered so far, across possibly-many CLI
invocations, before Confirmation" (unavoidable, since a durable
`SessionRepository` was already a designed-but-unfilled gap this
architecture must fill to be usable at all) and one store for "what a
Confirmed session produced, before a separate human authorizes it"
(unavoidable given PEC-REQ-034's requirement that Confirmation and
Authorization be two separate CLI invocations, possibly in two separate
processes). No third store, cache, or index is introduced.

---

## 12. Error Model

| Failure | Detected by | Exit code | User-facing message shape | Machine-readable `error_type` |
|---|---|---|---|---|
| Malformed input (bad flag value/type) | argparse | 2 (argparse's own convention, unchanged) | argparse's standard usage error | N/A — argparse never reaches JSON rendering |
| Missing decision subject / template ref | `SessionCoordinator.create_session` (already validates non-empty) | 1 | "template-ref/subject-ref required and must be non-empty" | `invalid_session_input` |
| Invalid option sets | `Preview` builder (already implemented) | 1 | Delegated message from existing validator | `invalid_option_set` |
| Preview-generation failure | `PreviewBuilder` (already implemented) | 1 | Delegated | `preview_generation_failed` |
| Confirmation mismatch (digest doesn't match live Preview) | New: `decision-session confirm` adapter compares argument to live digest before calling `ConfirmationController` | 3 | "the preview you confirmed does not match the session's current content — re-run `preview` and confirm the current digest" | `confirmation_digest_mismatch` |
| Missing provenance (required package field absent) | `PublicationHandoff.validate_completeness` (already implemented) | 1 | Delegated | `readiness_incomplete` |
| Stale readiness package | `PublicationCoordinator._validate_authorization_freshness` (already implemented) | 5 | Delegated | `stale_authorization` |
| Invalid authorization (wrong package_id) | `PublicationCoordinator._validate_authorization_applicability` (already implemented) | 1 | Delegated | `invalid_authorization` |
| Authorization mismatch / missing | `PublicationCoordinator._validate_authorization_presence` (already implemented) | 1 | Delegated | `missing_authorization` |
| Publication conflict / duplicate publication | `PublicationCoordinator._check_replay` (already implemented) | 4 | "package `<id>` was already published as record `<record_id>` — see `.pcae/publication-execution/records/<record_id>.json`" (record_id read from the moved `consumed/` pending-package marker, §11.2) | `authorization_replay` |
| Interrupted publication (partial write) | `PublicationCoordinator`'s own atomic rollback (`PublicationRollbackError`, already implemented) | 1 | Delegated | `publication_rollback_failed` |
| Unsupported versions | Each artifact's own `from_payload`/deserialize (already implemented, raises `*SerializationError`) | 1 | Delegated | `unsupported_schema_version` |
| Internal subsystem failure (unexpected exception) | CLI adapter's own outermost catch | 1 | Generic safe message, **never** the raw exception string or traceback | `internal_error` |

**Sensitive-data redaction:** no error path in this table ever includes
a raw file-system path outside `.pcae/`, a raw Python traceback, or any
field not already present in the relevant dataclass's own `to_payload()`
— consistent with `governance_record.py`'s existing bounded-read/no-
raw-exception convention. No error message ever includes another
session's or another package's content (each error is scoped to exactly
the `session_id`/`package_id` the failing command targeted).

Errors never leak authority-bearing material (no error path returns an
`--operator-id`, `--owner-id`, or `--preview-digest` from a *different*
record than the one the failing command targeted) and never permit
fallback publication (every failure in the `publish` path is terminal
for that invocation — there is no "publish anyway" flag, degraded mode,
or retry-with-relaxed-checks option anywhere in this architecture).

---

## 13. Idempotency and Replay Model

- **Preview is fully reproducible and idempotent**: re-running
  `decision-session preview <id>` any number of times before
  Confirmation returns the same content for the same underlying session
  state and advances no additional stage beyond the first call
  (`stage_preview_construction`/`_validation` are themselves
  `_require_next`-gated single-shot advances, but *calling the CLI
  command* multiple times before Confirmation is safe — a second
  invocation after the stage already advanced simply re-renders the
  already-built `Preview` object rather than erroring, since re-display
  is never harmful and IWC-001 nowhere prohibits re-viewing).
- **Confirmation is single-use**: enforced by `WorkflowOrchestrator`'s
  stage-ordering guard (already implemented) — a second `confirm`
  invocation on an already-`Confirmed` session returns exit code 2
  (out-of-sequence), never re-confirms or silently no-ops.
- **A readiness package is replayable for *inspection*, never for
  re-construction**: `decision-session confirm`'s automatic
  package-build step (§8) runs exactly once per session (a `Confirmed`
  session's orchestration state is itself terminal for that stage); a
  package, once built and stored (§11.2), can be read/shown again (a
  future `decision-session show-package <package-id>` read-only verb
  would be a natural, low-risk addition — not required by this
  architecture, noted only as compatible with it) but is never rebuilt.
- **How authorization binds to the package**: `PublicationAuthorizationEvent.package_id`
  must exactly match the package being executed
  (`_validate_authorization_applicability`, already implemented) —
  the CLI does nothing beyond passing the operator's `<package-id>`
  argument straight through; no binding logic is added at the CLI layer.
- **How publication retries operate**: there is no dedicated "retry"
  command. A failed `publish` invocation (for any reason in §12's table
  except replay) may simply be re-run by the operator with corrected
  arguments; because `_check_replay` runs first, before any write
  (§2 item 4), a retry after a genuine failure (nothing was written) is
  always safe, and a retry after a genuine success is always rejected
  as a replay (exit code 4) rather than silently re-publishing or
  producing a second record.
- **How duplicate publication is detected**: `PublicationRecordStore.is_published`
  + the atomic `O_CREAT|O_EXCL` idempotency marker (already implemented,
  `storage.py`) — this is the single source of truth; the CLI adds no
  second, competing duplicate-detection mechanism (e.g., it does not
  itself check whether the pending-package file has already moved to
  `consumed/` as its *primary* duplicate check — that check exists only
  to produce a *friendlier error message*, §12's replay row; the
  authoritative check remains `PublicationCoordinator`'s own).
- **How successful prior publication is reported**: `publish`'s response
  on a replay always includes the original `record_id` (read from the
  `consumed/` pending-package marker written at first success, §11.2),
  so an operator re-running the same command by mistake is told exactly
  where the already-published record lives, never left with a bare
  failure.

This architecture introduces **zero new idempotency or replay logic** at
the publication boundary — it is a pure pass-through to
`PublicationCoordinator`'s already-PEC-001-conformant, already-verified
(144D) machinery. The only new idempotency-adjacent behavior is the
pending-package store's move-not-delete convention (§11.2), which exists
solely to improve the *error message*, never to alter the *authoritative
decision* of whether a publish succeeds.

---

## 14. Security Assessment

| Risk | Assessment | Mitigation |
|---|---|---|
| CLI argument leakage (shell history, `ps`) | `--preview-digest`, `--statement`, `--operator-id` are not secrets — they are governance-evidentiary text, already designed to be retained verbatim in provenance (CHGR-001 §10). No credential or token is ever passed as a CLI argument anywhere in this architecture (there is no `--token`/`--password`/`--api-key` flag on any command in this family). | No mitigation needed beyond what already applies — nothing sensitive is present |
| Shell history exposure | Same as above — nothing secret is ever an argument | N/A |
| Environment-variable leakage | This architecture defines no new environment variable | N/A |
| Temporary-file leakage | Both new stores use atomic temp-file-then-rename writes (matching `storage.py`'s proven pattern) within `.pcae/`, never `/tmp` or a world-readable location; no plaintext secret is ever written by either store (none of the fields they hold are secrets) | Reuse of the existing atomic-write pattern; no new temp-file location |
| Unauthorized artifact substitution | An operator could hand-edit a `.pcae/decision-sessions/pending-packages/<id>.json` file before running `publish` | `PublicationCoordinator._validate_package` (already implemented) re-validates every required field and re-checks `PublicationHandoff.validate_completeness` before any write — a tampered package that fails completeness is rejected; a tampered package that still passes completeness (e.g., an altered `rationale_text`) would publish tampered *content*, which is a pre-existing risk of the already-frozen package format, not one this CLI introduces or could fully close (the same risk exists if a future non-CLI transport wrote the same file) — disclosed here as a residual risk inherent to any file-based handoff, not unique to this architecture |
| Forged identity evidence | `--owner-id`/`--operator-id` are self-asserted strings with no authentication behind them (§10) | Explicitly disclosed, not silently accepted as strong identity — §10's finding that this repository has no authority-evaluation contract yet applies with full force; this architecture neither worsens nor solves that gap, and states so plainly rather than implying a false guarantee |
| Stale artifact reuse | Addressed structurally: Preview-digest binding (Confirmation side, §9) and `_validate_authorization_freshness` (Authorization side, already implemented) both fail closed on staleness | No new mechanism needed — reuse of existing checks |
| TOCTOU between confirmation and publication | The window between `decision-session confirm` (readiness) and `governance-record publish` (authorization) is unbounded by design (they are deliberately separate human acts, §9) — during that window, nothing about the underlying `Session` can change (it is already terminal/`Confirmed`, and no command in this architecture ever mutates a terminal session), so there is no TOCTOU on the *decision content* itself; the only thing that can happen in that window is a second, distinct confirmed session producing a *different* package, which is a different governance act entirely, not a race on the same one | Terminal-session immutability (already IWC-001-guaranteed) closes this for the decision content; no new lock is needed because nothing mutable is shared across the window |
| Confused-deputy behavior | The `publish` command could in principle be run by an operator who never saw the original Preview | This is an accepted consequence of PEC-REQ-034's explicit design (Authorization and Confirmation are allowed, even expected, to be performed by different or the same principal, §10) — not a defect this architecture introduces; PEC-001 itself treats this as the ratified minimum viable authority boundary (Model 2), with a stronger Model 3 (delegated, independently verifiable authorization token) named as a future, not-yet-adopted hardening extension (§2 item 7's citation of PEC-REQ-045/046) |
| Transport impersonation | No network transport exists in this architecture (CLI only, local process, local filesystem) — no impersonation surface beyond OS-level process/file permissions, unchanged from every other command already in this CLI | N/A beyond existing OS-level trust boundary |
| Unsafe non-interactive use | A fully-scripted sequence of `decision-session` + `publish` commands with hard-coded arguments could technically automate a "human" decision end to end | Not preventable at the CLI-argument level (§9's disclosed limitation) — the architecture's only lever here is that every command still requires explicit, individually-supplied evidentiary text (a `--statement`, a matching `--preview-digest`, a distinct `--operator-id`) rather than a single opaque "yes" flag, so a script author must still explicitly fabricate each piece of evidentiary content rather than being handed a shortcut; genuine prevention of unsafe automation is a governance/process matter (who is permitted to script this), not something a CLI's own argument shape can enforce, and this document does not claim otherwise |

No broad secret-management subsystem is proposed — nothing in this
architecture handles a credential, token, or secret of any kind.

---

## 15. Boundary and Dependency Analysis

```text
pcae.cli (argparse wiring)
   │
   ├──▶ pcae.commands.decision_session (new, thin)
   │        │
   │        ├──▶ pcae.interactive_workflow.session.SessionCoordinator
   │        ├──▶ pcae.interactive_workflow.orchestration.WorkflowOrchestrator
   │        ├──▶ pcae.interactive_workflow.publication_handoff.PublicationHandoff
   │        └──▶ pcae.interactive_workflow.persistence.SessionRepository
   │                   ▲
   │                   └── new concrete filesystem implementation (§11.1),
   │                       living in pcae.commands.decision_session or a
   │                       small sibling module — never inside
   │                       interactive_workflow.persistence itself, which
   │                       stays interface-only per its own existing design
   │
   └──▶ pcae.commands.governance_record (existing, extended with `publish`)
            │
            └──▶ pcae.governance.publication.PublicationCoordinator
                     │
                     └──▶ pcae.interactive_workflow.publication_handoff
                            .PublicationReadinessPackage  (data type only —
                            the one coupling PEC-001 already permits,
                            §2 item 4, unchanged by this phase)
```

Verified against the governing constraints:

- **CLI/transport depends on stable public application boundaries**:
  yes — every arrow above targets an already-existing public class
  method (`create_session`, `build_orchestrator`, `stage_*`,
  `build_package`, `authorize`, `execute`), none reaches into a
  private/underscore-prefixed method.
- **`PublicationCoordinator` does not import Interactive Workflow
  internals**: unchanged — this phase adds no new import to
  `governance/publication/**` beyond what already exists
  (`publication_handoff` only); the forbidden-import test
  (`test_phase_144c_publication_coordinator.py:340-391`) continues to
  pass unmodified.
- **Interactive Workflow does not acquire publication authority**:
  unchanged — `SessionCoordinator`/`WorkflowOrchestrator` gain no new
  method, and specifically never gain `publish`/`authorize`/`execute`
  (the forbidden-method-name check in
  `test_iwc_143o_session_coordination_publication_handoff.py:366-367`
  continues to pass unmodified — this architecture's new
  `decision_session.py` CLI module lives outside
  `interactive_workflow/**` entirely, so it is not even in that test's
  scope, and it never adds such a method to any class inside that
  package).
- **CHGR writing remains owned by Publication**: unchanged — the only
  code path that ever calls `PublicationCoordinator.execute()` is
  `governance-record publish`; `decision-session` never writes to
  `.pcae/publication-execution/` or `.pcae/governance-records/`.
- **Lifecycle authority remains unchanged**: neither new command touches
  `src/pcae/lifecycle.py` or the PCAE phase/task lifecycle tree — PEC-001
  §4 (PEC-REQ-018-020) already required this of the Coordinator itself;
  this phase adds no new coupling.
- **Permission Broker is not bypassed**: it was never in the path to
  begin with for either subsystem (§2 item 8) — this architecture does
  not add a false gate that only *appears* to check it; §16 addresses
  how it can be surfaced honestly, as advisory-only, without pretending
  to gate anything.
  it changes nothing about runtime capability, and neither new command
  reads or writes any runtime-capability flag.

**New dependencies this implementation would require, minimized:**

1. A new `pcae.commands.decision_session` module (CLI wiring only).
2. A new concrete filesystem `SessionRepository` implementation (fills
   an existing, designed-but-empty interface — not a new dependency
   surface, a completion of one already declared).
3. A new, small pending-package store module (new, but minimal — one
   serialize/one deserialize/one move-to-consumed operation, all reusing
   existing `PublicationHandoff.serialize`/`deserialize`).
4. One new argparse subparser tree (`decision-session`) and one new leaf
   subparser (`governance-record publish`) in `cli.py`.

No new third-party dependency, no new schema file, no new top-level
package beyond `pcae.commands.decision_session`.

---

## 16. Operational Observability

Non-authoritative operational output only — never a second source of
governance truth (per the governing prompt's own explicit instruction).

- **Session identifier** (`CDS-<uuid4>`): printed on every
  `decision-session` command's output, human and `--json`.
- **Request identifier**: not separately introduced — the combination of
  `session_id` + the CLI's own process-local invocation is sufficient
  for this single-transport architecture; a dedicated request-id would
  only earn its keep once a second, concurrent transport exists (Model D
  territory, §4, explicitly deferred).
- **Readiness-package identifier** (`package_id`): printed by
  `decision-session confirm` on success, and required as the sole
  positional argument to `publish`.
- **Authorization identifier**: `PublicationAuthorizationEvent` does not
  currently expose a separate public identifier beyond
  `operator_id`+`package_id`+`invoked_at` (already implemented,
  `models.py:35-52`) — this architecture surfaces exactly those three
  fields in `publish`'s output, inventing no new one.
- **Publication-attempt identifier**: already implemented
  (`PublicationCoordinator._record_attempt`, §2 item 4) — `publish`'s
  output surfaces whatever attempt-record path/id the Coordinator's own
  audit trail already produces; no duplicate is created.
- **Result status**: `success`/`failure` plus, on failure, the
  `error_type` from §12's table.
- **Safe diagnostics**: the `--json` error envelope (§7.4) only — never
  a raw traceback.
- **Advisory-only Permission Broker surfacing** (optional, non-gating):
  `decision-session`/`publish` commands MAY, purely for operator
  visibility, construct a `PermissionBrokerRequest` for the nearest
  matching existing action type and print its (necessarily
  `execution_unavailable`-flagged) decision alongside the real result —
  clearly labeled "advisory, not a gate" — giving early, honest visibility
  into what a future, separately-authorized execution boundary might
  decide, without ever implying today's decision depended on it. This is
  explicitly optional and cosmetic; omitting it changes no correctness
  property of this architecture.

**Distinguishing logs from audit evidence from canonical governance
records:** operational stdout/stderr from these CLI commands is a
convenience for the operator in the moment — it is never re-read by any
other command as a source of truth. Audit evidence is whatever
`AuditRecorder`/`PublicationCoordinator._record_attempt` already
durably persist (unchanged, already-governed). The canonical governance
record is, and remains, exactly the CHGR-shaped record
`PublicationCoordinator.execute()` writes to
`.pcae/publication-execution/records/`. This three-way distinction is
not new to this phase — it already exists in the underlying subsystems;
this architecture is careful not to blur it by, for instance, having a
CLI command's own printed summary become something a later command
reads back as ground truth (every "read back" in this architecture reads
the actual artifact file, never a log line).

---

## 17. Execution-Distance Update

Restating 144H's own framework (§3 there), updated for what this
phase's eventual implementation (not authorized here) would change:

| Layer | Before 145A implementation | After 145A implementation (hypothetical) |
|---|---|---|
| User-facing governance invocation (reach the Interactive Workflow/Publication pipeline at all) | **Impossible** — no CLI exists | **Possible** — this is exactly what §5's architecture, once implemented, would unlock |
| Publication capability (produce a canonical CHGR from a real human decision) | Exists as a library, unreachable | Reachable, still exactly as governed by PEC-001 today — no change to *what* Publication does, only to *whether a human can trigger it* |
| Repository-change execution (shell commands, source mutation, backend invocation) | Unavailable (`Observed`/`observe`/`unavailable`) | **Still unavailable, unchanged** — nothing in this architecture touches `src/pcae/runtime/`, the Permission Broker's `COMP-002`, or any execution-enablement flag |
| Execution authorization | Does not exist as a concept in this codebase yet (Permission Broker is advisory-only, `COMP-002` unimplemented, §2 item 8) | **Unchanged** — a Publication Authorization Event (PEC-001) is a governance-record authorization, structurally and namespace-distinct from an *execution* authorization; this phase does not conflate them and implementing it would not create the latter |
| Execution coordination | Does not exist | Unchanged |
| Rollback | Exists only for Publication's own atomic-write failure path (`PublicationRollbackError`, already implemented) — never a rollback of an *executed change*, since none can occur | Unchanged |
| Recovery | Exists only as interruption/resume of a Decision Session (§11.3) | Unchanged in kind, newly *reachable* by a human via CLI |
| Runtime enforcement | Not implemented (Runtime Enforcement chapters, 102-104, remain architecture/prototype only per prior phases) | Unchanged |

**Explicit statement, as the governing prompt requires:** implementing
this architecture would make governed *decision-making and publication*
usable by a human for the first time. It would **not** make PCAE
execution-capable in any sense — it adds no shell mediation, no backend
invocation, no repository-mutation capability beyond the one, single,
already-governed write Publication already performs (an immutable
record under `.pcae/publication-execution/`). The distance from "a human
can publish a governance decision" to "PCAE can perform governed
engineering execution" is not shortened by this phase in any respect
beyond making the former possible — every other execution-readiness gap
144H (§3-§9) previously identified (Permission Broker `COMP-002`-`COMP-010`
unimplemented, no real backend invocation, no shell mediation, no
runtime enforcement) remains exactly as far away as before this phase.

---

## 18. Recommended Future Phase Sequence

This document does not authorize any of the following. Each is named
only as the bounded, dependency-ordered sequence this architecture, if
adopted, would justify:

1. **145B — Interactive Workflow + Publication CLI/Transport Contract
   Freeze.** Freeze this document's decisions (command names, argument
   shapes, exit-code table, error taxonomy, the two new store formats,
   the `SessionRepository` concrete-implementation interface contract)
   into a versioned contract, the same discipline PEC-001/IWC-001
   themselves went through before implementation (144B's own precedent).
2. **145C — Independent Contract Verification.** Adversarial
   re-derivation of 145B against this document and the five governing
   contracts, the same discipline 144D applied to PEC-001.
3. **145D — `SessionRepository` Concrete Implementation.** The narrowly
   -scoped filesystem store (§11.1) alone, independently verified before
   any CLI wiring depends on it — this is the one genuinely new piece of
   logic (as opposed to thin wiring) this architecture requires, and
   deserves its own focused implementation/verification pair.
4. **145E — Pending-Package Store Implementation.** The second new store
   (§11.2), equally narrow, independently verified.
5. **145F — `decision-session` CLI Adapter Implementation.** Thin wiring
   only, per §6/§8, against the frozen 145B contract.
6. **145G — `governance-record publish` CLI Adapter Implementation.**
   Thin wiring only, per §6/§9, against the frozen 145B contract.
7. **145H — Independent Implementation Verification.** End-to-end
   adversarial verification of 145D-145G together (the same "prototype
   review and hardening" pattern this project has used repeatedly, e.g.
   for Repository Intelligence and Historical Memory), including a live
   run of the forbidden-import and forbidden-method-name boundary tests
   (§15) to confirm none regressed.
8. **145I — Operational Pilot.** A small number of real, disclosed,
   observed decision-session-to-publication runs against this
   repository's own governance process, evaluated for whether the
   CLI's ergonomics and error messages hold up under genuine use before
   any broader adoption recommendation is made.

---

## 19. Findings Register

| ID | Classification | Finding |
|---|---|---|
| F-145A-1 | Observation | Both Interactive Workflow and Publication are fully implemented, contract-frozen, and independently verified libraries with zero CLI reachability — independently re-confirmed this phase, unchanged from 144H. |
| F-145A-2 | Blocking (for implementation, not for this architecture) | No concrete `SessionRepository` implementation exists; any staged, multi-invocation CLI over Interactive Workflow requires one before it can function at all. Named as 145D. |
| F-145A-3 | Blocking (for implementation, not for this architecture) | No storage location exists for a built-but-unpublished `PublicationReadinessPackage`; PEC-REQ-034's required two-command separation cannot function without one. Named as 145E. |
| F-145A-4 | Non-Blocking | This repository has no authority-*evaluation* contract (only authority-*capture*) for either decision-maker or authorizing-operator identity (§10); this architecture correctly does not invent one, but any future claim that this CLI "checks who is allowed to decide/authorize" would be false and must not be made. |
| F-145A-5 | Non-Blocking | Concurrent-write races on the new session store are not fully mutual-exclusion-safe (§11.3) — acceptable for a single-operator CLI tool at this stage, disclosed as a residual risk for a future hardening phase, not silently ignored. |
| F-145A-6 | Non-Blocking | An unauthenticated, hand-edited pending-package file could carry tampered (but structurally complete) content into Publication (§14) — an inherent risk of any file-based handoff, not unique to or worsened by this architecture, and not solvable without a broader integrity/signing mechanism this phase does not propose. |
| F-145A-7 | Deferred | A transport-neutral application-service layer (Model D) is not justified today (single transport, one caller) but the four existing subsystem classes already provide sufficient extraction points should a second transport ever be separately authorized (§4). |
| F-145A-8 | Deferred | Whether a future Model 3 (delegated, independently verifiable Publication authorization token, per PEC-001 §6's own named-but-unadopted extension) should replace or supplement the CLI-operator-invocation model (Model 2) this architecture assumes is explicitly out of scope — PEC-001 itself defers it. |

No finding in this register identifies a concrete architectural
contradiction that prevents a safe invocation path — none is classified
Blocking against the *architecture itself*; F-145A-2 and F-145A-3 are
blocking only against skipping straight to a CLI implementation without
first building the two stores this document already specifies, which
§18's sequence accounts for.

---

## 20. Executive Summary

Interactive Workflow (IWC-001 v1.2) and Publication (PEC-001 v1.1) are
both fully implemented, contract-frozen, and independently verified —
and, until this phase, entirely unreachable by any human, a gap 144H,
144I, and 144J each independently and unchangedly named as this
project's highest-leverage, lowest-risk next step. This phase answers
how to close that gap without weakening any existing boundary: a
two-command-family CLI (`pcae decision-session` for invocation,
interaction, and Confirmation; `pcae governance-record publish`,
exactly as PEC-REQ-034 already names it, for Authorization and
Publication), each a thin wrapper delegating to already-implemented,
already-governed subsystem classes, connected by two new, narrowly
justified, non-authoritative filesystem stores that fill interface gaps
this repository had already designed but not yet filled. No new
application-service layer, no new authority source, no new execution
capability, and no change to runtime posture are introduced. The two
genuinely new pieces of logic this architecture requires — a concrete
`SessionRepository` and a pending-package store — are small, bounded,
and sequenced ahead of any CLI wiring in the recommended future phase
sequence (§18), which this document does not authorize. Implementing
this architecture would convert governed human decision-making and
publication from something verified-but-unusable into something a
human can actually do; it would not, in any respect, shorten this
project's remaining distance to governed engineering execution.

---

## Validation

Run this phase, confirmed clean:

- `pcae check` — passed
- `pcae health` — healthy
- `pcae doctor` (execution-chain, task-memory, git-lock, test-run, hooks) — clean
- `pcae push readiness` / `pcae push check` — ready
- `pcae runtime inspect` — State: `Observed`, Maximum capability:
  `observe`, Execution availability: `unavailable` (unchanged before and
  after)
- Existing Interactive Workflow test suites (143K-143P series) — unaffected, not modified
- Existing Publication test suites (144C/144D/144F/144G series) — unaffected, not modified
- Forbidden-import boundary tests
  (`test_phase_144c_publication_coordinator.py`,
  `test_iwc_143o_session_coordination_publication_handoff.py`,
  `test_chgr_phase_separation.py`) — unaffected, not modified; this
  document's architecture is designed to keep every one of them passing
  unmodified if implemented
- `fast_green` marker group — unaffected, not modified

No production code, contract, or schema was changed by this phase; the
above commands were run to confirm the repository's existing governed
state before and after authoring this document, not to validate new
code (none exists yet).

---

## Explicit No-Go Confirmation

This phase implemented no CLI command, no transport adapter, and no
production code. It modified no existing contract, created no execution
capability, enabled no Permission Broker execution, changed no lifecycle
authority, changed no publication authority, changed no CHGR ownership,
merged no confirmation/authorization boundary, added no automatic
authorization or publication, added no shell or repository execution,
changed no runtime state or capability, and rewrote no historical phase
report. Runtime remains `Observed` / `observe` / `unavailable`.

## Recommended Next Phase

Per §18: **145B — Interactive Workflow + Publication CLI/Transport
Contract Freeze**, freezing this document's command architecture,
transport contract, and store formats into a versioned contract before
any implementation begins. This recommendation does not authorize 145B.
