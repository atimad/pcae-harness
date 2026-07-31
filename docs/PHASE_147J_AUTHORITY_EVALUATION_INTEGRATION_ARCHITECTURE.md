# Phase 147J: Authority Evaluation Integration Architecture

**Phase ID:** 147J
**Mode:** Architecture (architecture only — no implementation, no contract amendments, no schema changes, no runtime changes)
**Baseline:** Phase 147J.0 (Authority Evaluation Integration Prerequisite Decision Architecture)
**Date:** 2026-07-31

---

## Authorization

Phases 147G (Core Implementation), 147H (Independent Implementation Verification), 147I (Operational Readiness Assessment), and 147J.0 (Integration Prerequisite Decision Architecture) are complete. 147J.0 resolved every architectural prerequisite this phase depends on: `claimed_identity` owner → `Session.owner_identity`; Decision Template resolution → a dedicated resolution capability; `evidence_kind` compatibility → no incompatibility exists; two-stage evaluation → required, Stage 2 supersedes Stage 1; preferred orchestration → a dedicated Authority Evaluation Service. This phase is authorized to define the complete integration architecture built on those four resolved decisions. This phase remains architecture-only throughout: no `src/pcae/**` change, no contract amendment, no schema change, no runtime change, no lifecycle change, no test change.

### Bootstrap

```
pcae session bootstrap --agent-id claude-code --sync-lock
  -> healthy; agent lock held by claude-code; latest completed phase 147J.0;
     recommended next: 147J (this phase); readiness "blocked" only because the
     post-147J.0 idle placeholder task was still active — the expected
     pre-phase-start state
pcae check              -> passed
pcae health              -> healthy; all required files present; policy valid; git clean
pcae doctor task-memory  -> clean, no inconsistencies
pcae runtime inspect     -> Runtime state Observed; Execution capability unavailable;
                            Registry status empty; Plugin count 0; Governance posture
                            non-executing (unchanged from 147J.0)
pcae push check          -> nothing_to_push, health healthy, check passed
```

Confirmed: repository clean; branch synchronized (0 ahead / 0 behind `origin/main`); no other active governed phase; runtime unchanged (Observed / observe / unavailable). The idle placeholder task (`20260731-0155-idle-awaiting-next-governed-phase-post-147j-0`) was closed and a governed task contract (`tasks/active/20260731-0212-phase-147j-authority-evaluation-integration-architecture.md`) opened, scoped to this report plus ordinary task/phase bookkeeping files only. PROJECT_STATUS.md is treated as authoritative background per standing rule; the phase prompt supersedes it where they might conflict (none found).

Research for this phase re-reads, directly, the actual `pcae.authority_evaluation` package (`src/pcae/authority_evaluation/{models,registry,evaluation,errors,serialization}.py`), the actual Interactive Workflow / Publication Handoff / Publication Coordinator / CHGR-record-construction code (`src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`), and 147J.0's own already-cited contract text (AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001) — not a re-derivation of 147J.0's decisions, which this phase treats as fixed inputs.

---

## 1. Executive Summary

This phase defines the complete integration architecture for a **dedicated Authority Evaluation Service (AES)** — the orchestration component selected by 147J.0 §10/§11 — that connects the verified, standalone `pcae.authority_evaluation` package to the rest of PCAE's governed decision-publication pipeline without modifying that package, without modifying any existing contract, and without modifying any existing schema.

The AES sits *beside* Interactive Workflow and Publication, never inside either. It is the sole reader of `Session.owner_identity` (as `claimed_identity`), the sole resolver of Decision Templates and the sole caller of `AuthorityRegistry.resolve()`, and the sole invoker of `evaluate()`. It runs at two timing points — Stage 1 (advisory, at or before Confirmation) and Stage 2 (fresh, immediately before CHGR construction, outside the Publication Coordinator's exactly-once transaction) — producing an immutable, schema-versioned **Authority Evaluation Record (AER)** for Stage 2 only, referenced (never embedded) from a future `PublicationReadinessPackage` field via this codebase's existing `{record_id, record_digest, record_family}` sibling-reference pattern (already used identically by every CHGR artifact cross-reference in `governance/publication/record.py`).

Nothing this phase designs requires amending AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, or CHGR-001. `authority_basis_claimed` (CHGR-001 §10/§11), currently and correctly left unpopulated with a disclosed limitation because "no Decision Template model exists anywhere in this repository carrying an `eligible_authority` field" (`governance/publication/record.py:41-53`), is exactly the gap the AES's Stage 2 `citation_text` output fills — via PEC-REQ-115's already-frozen "MAY construct this field where the package's template citation resolves to that text" clause, which requires no amendment to become populated, only a resolved citation to consume.

**Overall verdict (§20 below): AUTHORITY EVALUATION INTEGRATION ARCHITECTURE COMPLETE.** No architectural blocker remains. §19 recommends 147K (Contract Freeze) as the next phase, not authorized by this document.

---

## 2. Objectives

Per the authorizing prompt: design (never implement) the complete architecture integrating `src/pcae/authority_evaluation/` into PCAE — system context, the Authority Evaluation Service, Decision Template resolution, the Authority Registry boundary, the two-stage evaluation lifecycle, the end-to-end sequence, persistence, replay, failure ownership, outcome consumption, schema impact, integration boundaries, security architecture, observability, future contracts, an implementation roadmap, and an integration-readiness verdict. No production code, no contract, no schema is touched; only `docs/PHASE_147J_AUTHORITY_EVALUATION_INTEGRATION_ARCHITECTURE.md` and ordinary task/phase bookkeeping files change.

---

## 3. Architectural Principles

Every decision below is checked against these invariants, each already established by 147G–147J.0 and the frozen contracts they verified:

| # | Invariant | Source | How this architecture preserves it |
|---|---|---|---|
| 1 | Evaluator remains pure | AEMIC-REQ-074/075/076 (`evaluation.py:57-58`: "total, non-raising for every well-formed input... deterministic... side-effect free") | AES calls `evaluate()` unmodified, passing pre-resolved arguments; no wrapper adds I/O inside the call |
| 2 | Evaluator remains deterministic | AEMIC-REQ-075/105 | Same |
| 3 | Evaluator never resolves Registry | AEMIC-REQ-073/077 (`evaluation.py:3-8`) | AES resolves the Registry *before* calling `evaluate()`, passing `declaration` as an already-resolved argument, exactly as `evaluate()`'s own signature requires |
| 4 | Evaluator never authorizes | AEMIC-REQ-107 (`evaluation.py:59-61`) | AES's own public contract (§5) states outcomes are disclosures, never permissions; no consumer named in §13 is permitted to branch pipeline control flow on an outcome |
| 5 | Evaluator never mutates lifecycle state | AEM-001 §D-6 scope; 147I §10/§11 | AES has no write access to `Session`, `SessionState`, or any state-machine transition; it only *reads* `Session.owner_identity`, `template_ref`, `template_version` |
| 6 | Disclosure-only semantics preserved | AEM-REQ-003/037 | §16 (Security Architecture) and §13 (Outcome Consumption) both restate and enforce this at every consumer boundary |
| 7 | Orchestration owns lifecycle | IWC-001's `SessionState`/state-machine ownership | AES is a peer of, not a replacement for, the Interactive Workflow state machine; it never transitions a session |
| 8 | Registry owns lookup | AEM-001 §4.5, `registry.py:17-24` | The `AuthorityRegistry` ABC's one-method shape is unmodified (§7); AES is its sole caller, never its implementer of business logic beyond storage |
| 9 | Session owns identity | IWC-REQ-036/037 | AES reads `Session.owner_identity`; it never collects, verifies, or stores a competing identity value |
| 10 | Publication Coordinator remains publication-only | PEC-REQ-115/116, `coordinator.py:16-27` (explicit exclusion of `interactive_workflow.session/orchestration/evidence/clarification/preview/confirmation` imports) | AES's Stage 2 output is consumed by the Coordinator only as a citation value already resolved before the Coordinator's transaction begins — never as a resolution the Coordinator itself performs |
| 11 | Interactive Workflow remains interaction-only | 147J.0 §3.2/§10 (Strategy B rejected) | AES reads Session state; Interactive Workflow never imports or calls the AES's evaluation logic as part of its own transition logic |

---

## 4. Complete System Context

### 4.1 Context diagram

```
                     ┌─────────────────────────┐
                     │   Interactive Workflow   │
                     │  (Session, Confirmation, │
                     │   State Machine)         │
                     └────────────┬─────────────┘
                                  │ reads: owner_identity, template_ref,
                                  │        template_version, SessionState
                                  │ (read-only; AES never writes back)
                                  ▼
                     ┌─────────────────────────┐
                     │ Authority Evaluation     │◄──── invoked at Stage 1
                     │ Service (AES)            │      (advisory) and Stage 2
                     │  - sole orchestrator     │      (fresh, pre-CHGR)
                     └────────────┬─────────────┘
                                  │ resolves, in order:
                                  ▼
                     ┌─────────────────────────┐
                     │ Decision Template &      │
                     │ Declaration Resolution   │  (internal AES collaborator,
                     │  (co-located, §6)        │   not a separately callable
                     └────────────┬─────────────┘   public component — 147J.0 §4.3)
                                  │ resolves declaration via
                                  ▼
                     ┌─────────────────────────┐
                     │  Authority Registry      │
                     │  (abstract boundary;     │
                     │   concrete impl. is a    │
                     │   future, separate phase)│
                     └────────────┬─────────────┘
                                  │ AuthorityRegistry.resolve(template_ref, template_version)
                                  ▼
                     ┌─────────────────────────┐
                     │  Authority Evaluator     │
                     │  (pure evaluate(),       │
                     │   unmodified since 147H) │
                     └────────────┬─────────────┘
                                  │ returns
                                  ▼
                     ┌─────────────────────────┐
                     │ AuthorityEvaluationOutcome│  (in-memory; persisted only
                     │  (Stage 1 or Stage 2)    │   as part of the AER, §10, at
                     └────────────┬─────────────┘   Stage 2)
                                  │ Stage 2 outcome only, cited verbatim
                                  ▼
                     ┌─────────────────────────┐
                     │      Readiness           │  (PublicationReadinessPackage;
                     │ (PublicationHandoff)     │   gains one new reference field,
                     └────────────┬─────────────┘   §14, in a future contract phase)
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │      Publication          │  (PublicationCoordinator;
                     │ (Coordinator, PEC-001)    │   citation-only consumption,
                     └────────────┬─────────────┘   PEC-REQ-115)
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │         CHGR              │  (authority_basis_claimed
                     │ (build_publication_record)│   now populatable — §14)
                     └───────────────────────────┘
```

### 4.2 Ownership / data-flow / control-flow / responsibility boundaries

| Boundary | Ownership | Data flow | Control flow | Responsibility |
|---|---|---|---|---|
| Interactive Workflow → AES | Interactive Workflow owns `Session`; AES owns nothing of Workflow's | `Session.owner_identity`, `template_ref`, `template_version`, `SessionState` flow **out** of Workflow, read-only | AES is *invoked by* a caller that already holds a `Session` reference (see §8.2 for exactly who); Workflow never calls into AES as part of its own state-machine transition logic | Workflow: identity/session lifecycle. AES: evaluation only |
| AES → Decision Template & Declaration Resolution | AES owns this capability outright (internal, not a separate component) | `(template_ref, template_version)` in; `(EligibleAuthorityDeclaration, citation_text)` out | Synchronous, within AES's own call | Single-resolution-point discipline (147J.0 §4.3) |
| Resolution → Authority Registry | Registry owns lookup; Resolution owns *when* to call it | `(template_ref, template_version)` in; `Optional[EligibleAuthorityDeclaration]` out | Resolution calls `Registry.resolve()` synchronously, at most once per stage per evaluation attempt | Registry: storage/lookup only, never orchestration (§7) |
| AES → Evaluator | AES owns invocation; Evaluator owns evaluation logic | Seven parameters in (per `evaluate()`'s signature); one `AuthorityEvaluationOutcome` out | Synchronous, pure, no I/O inside the call | Evaluator: pure disclosure computation only (§3 invariants 1-4) |
| AES → Readiness / Publication / CHGR | AES owns the outcome/AER; Readiness/Publication/CHGR own citation-only consumption | Stage 2's `citation_text` flows forward, verbatim, as far as CHGR's `authority_basis_claimed` | AES never calls Publication or CHGR construction directly; it produces an artifact these components *read*, on their own schedule, under their own contracts | AES: disclosure production. Publication/CHGR: citation-only consumption (PEC-REQ-115) |

---

## 5. Authority Evaluation Service

### 5.1 Responsibilities

1. Read `claimed_identity` from `Session.owner_identity` (never re-derive, never independently collect — 147J.0 §3.3).
2. Resolve, exactly once per evaluation attempt, the Decision Template document identified by `(template_ref, template_version)`, deriving both `citation_text` (verbatim `eligible_authority`) and the `AuthorityRegistry`-resolved `declaration` from that single resolved document (147J.0 §4.3).
3. Invoke `evaluate()` (unmodified) at Stage 1 (advisory) and Stage 2 (fresh, pre-CHGR), per the two-stage timing 147J.0 §6.2 fixed.
4. Produce and, for Stage 2 only, persist an immutable **Authority Evaluation Record (AER)** wrapping the `AuthorityEvaluationOutcome` plus stage/replay metadata (§10).
5. Expose its own outcomes for read-only consumption by Readiness/Publication/CHGR/diagnostics — never push, never gate (§13, §16).

### 5.2 Inputs

| Input | Source | Owner (per 147J.0 §9) |
|---|---|---|
| `template_ref` | `Session.template_ref` | Session (originates) |
| `template_version` | `Session.template_version` | Session (originates) |
| `claimed_identity` | `Session.owner_identity` | Session |
| `declaration` | Registry, via Resolution | Registry (§7) |
| `citation_text` | Resolved Decision Template's `eligible_authority` | Resolution (§6) |
| `evaluated_at` | AES's own clock, at each stage's invocation | AES |
| `evaluator_version` | `pcae.authority_evaluation.models.EVALUATOR_VERSION` | The `authority_evaluation` package |
| stage identifier (`stage_1` / `stage_2`) | The caller of AES (§8.2 names who, at each stage) | AES's own invocation context |

### 5.3 Outputs

- One `AuthorityEvaluationOutcome` per invocation (in-memory always; §3 invariant 4 forbids any consumer from treating this as a permission).
- For Stage 2 only: one persisted, immutable **Authority Evaluation Record** (§10), referenceable via `{record_id, record_digest, record_family="authority_evaluation_record"}`.
- Diagnostics/log events (§17) for every resolution attempt, Registry call, and evaluation, whether the outcome is ELIGIBLE, INELIGIBLE, or INDETERMINATE.

### 5.4 Dependencies

`pcae.authority_evaluation` (unmodified: `models`, `registry` ABC, `evaluation.evaluate`, `errors`, `serialization`), a concrete `AuthorityRegistry` (future phase, §7), a Decision Template resolution mechanism (internal to AES, §6), read access to `Session` (via whichever caller already holds the session — AES never queries a Session store directly; see §8.2), and its own new AER storage (§10, following the `cltr/persistence.py` / `governance/publication/storage.py` atomic-write precedent).

### 5.5 Error ownership

AES owns translating every failure from its collaborators into one of its own named outcomes (never a bare `Exception`, mirroring `authority_evaluation/errors.py`'s own discipline):

- A `AuthorityRegistryUnavailableError`/`AuthorityRegistryCorruptError` from the Registry is caught by AES and surfaced as an **AES-owned** `AuthorityEvaluationServiceRegistryUnavailable`/`...RegistryCorrupt` condition (§12) — never silently swallowed, never retried transparently without disclosure.
- A missing/malformed Decision Template from Resolution is surfaced as an **AES-owned** `DecisionTemplateResolutionFailed` condition, distinct from any Registry condition (§12).
- Any `AuthorityEvaluationError` subclass raised by `evaluate()` itself (e.g. `MissingCitationTextError`, `TemplateIdentityMismatchError`) propagates through AES unchanged in type — AES adds no new wrapping around the evaluator's own, already-precise exception taxonomy (`errors.py:1-18`'s own two-family discipline is preserved, not re-invented).

### 5.6 Lifecycle

AES is **stateless between invocations** apart from the durable AER store it delegates all persistence to (mirroring `PublicationCoordinator`'s own "stateless apart from the durable store" design, `coordinator.py:76-81`). It holds no in-memory session cache, no Registry cache beyond what a future concrete Registry implementation itself may choose to cache internally (§7), and no cross-invocation mutable state. Each `evaluate_stage_1(...)` / `evaluate_stage_2(...)` call is a self-contained, independently-replayable unit of work.

### 5.7 Replay behavior

See §11 in full. Summary: because `evaluate()` is deterministic and AES adds no hidden state, any AES invocation may be safely repeated from the same inputs and will produce the same `AuthorityEvaluationOutcome` (modulo `evaluated_at`, which is metadata, not an evaluation input `evaluate()` itself branches on). Stage 2's AER write uses the same `O_CREAT | O_EXCL` idempotency-marker pattern as `PublicationRecordStore.commit_publication` (`storage.py:8-16`) so a concurrent duplicate Stage 2 attempt for the same package is detected, not silently double-written.

### 5.8 Transaction span

AES's own work (resolution + evaluation + AER write) is its own, independent unit — it is never nested inside the Publication Coordinator's `execute()` transaction (§3 invariant 10; PEC-001's explicit import-exclusion list, `coordinator.py:16-19`), and it never nests Interactive Workflow's own session-transition transaction inside itself. Stage 2 must complete (successfully or with a disclosed failure) *before* the Coordinator's `execute()` is invoked; AES's own write to the AER store is a separate atomic operation from the Coordinator's own atomic CHGR write.

### 5.9 Idempotency expectations

- Stage 1: no persistence, so idempotency is definitionally free — repeating Stage 1 simply recomputes the same advisory outcome (§11).
- Stage 2: idempotent per `package_id` (mirroring `PublicationRecordStore`'s `is_published(package_id)` check, `coordinator.py:235-241`) — a second Stage 2 attempt for the same readiness package either (a) returns the already-persisted AER unchanged if evaluation inputs are unchanged, or (b) is refused/superseded per §11's restart matrix if inputs changed, never silently overwritten.

### 5.10 Construction rules

AES is constructed with exactly two collaborators, both injectable (mirroring `PublicationCoordinator.__init__`'s `store`/`handoff` injection pattern, `coordinator.py:83-89`): a concrete `AuthorityRegistry` implementation, and an AER store. No global singleton, no ambient configuration lookup, no implicit Session store access — every input AES needs is passed explicitly by its caller (§8.2).

### 5.11 Public interface (shape only — no implementation)

```
class AuthorityEvaluationService:
    def __init__(self, registry: AuthorityRegistry, aer_store: AuthorityEvaluationRecordStore) -> None: ...

    def evaluate_stage_1(
        self, *, template_ref: str, template_version: str, claimed_identity: str,
    ) -> AuthorityEvaluationOutcome: ...
        # advisory only; never persisted; caller decides how/whether to surface it

    def evaluate_stage_2(
        self, *, template_ref: str, template_version: str, claimed_identity: str,
        package_id: str,
    ) -> AuthorityEvaluationRecord: ...
        # fresh resolution + evaluation; persists and returns an immutable AER
```

Both methods raise the error taxonomy of §5.5/§12, never a bare exception; neither method accepts a `declaration` or `citation_text` argument from its caller — both are always resolved internally, per-invocation, by AES itself (this is the single-resolution-point guarantee 147J.0 §4.3 requires).

### 5.12 Internal collaborators

The Decision Template & Declaration Resolution capability (§6) and the concrete `AuthorityRegistry` (§7) are AES's only internal collaborators. Neither is separately publicly callable by any other PCAE component — both are constructor-injected into, and used exclusively by, AES (closing the "caller-fabricated-declaration threat" 147I §28 flagged, per 147J.0 §8's ownership statement).

### 5.13 Why AES, not Interactive Workflow or Publication Coordinator

Restating and extending 147J.0 §10's comparison, grounded in this phase's own code reading:

- **Not Interactive Workflow:** Session already owns Confirmation, Evidence, Clarification, and Audit (`src/pcae/interactive_workflow/{confirmation,evidence,clarification,audit}/`); adding Registry/template-resolution access would widen its blast radius, and — concretely — `IWC-REQ-026` (`Reaching Confirmed SHALL NEVER, by itself, prove... eligible authority`) means Confirmation's own code path is precisely the place a future maintainer could accidentally wire an evaluation outcome into a transition guard without a dedicated component boundary preventing it.
- **Not Publication Coordinator:** `coordinator.py:16-19`'s own docstring explicitly enumerates the modules it deliberately never imports (`session`, `orchestration`, `evidence`, `clarification`, `preview`, `confirmation`) — evaluation-time Registry/template resolution is exactly this same category of "independent judgment" PEC-REQ-116 already forecloses from the Coordinator. Placing AES logic inside the Coordinator would require nesting resolution inside its exactly-once `execute()` transaction (§5.8), which would also complicate the Coordinator's already-precise failure/rollback model (`coordinator.py:130-211`) with a second, unrelated failure class.
- **AES is architecturally the only place with no other responsibility to blur evaluation into** — its sole job is: read identity, resolve template, resolve declaration, evaluate, persist (Stage 2 only), expose. This is exactly the same isolation property `pcae.authority_evaluation` itself already has (147H's verified purity), extended one layer outward.

---

## 6. Decision Template Resolution Capability

Per 147J.0 §4.3, this is **not** a separately callable public component — it is an internal capability of AES, exercised on every `evaluate_stage_1`/`evaluate_stage_2` call.

### 6.1 Resolution inputs

`(template_ref, template_version)`, read by AES from `Session` (§5.2) — Resolution itself accepts no other input; it never independently discovers a template outside the pair supplied.

### 6.2 Resolution outputs

Exactly two values, derived from **one** resolved Decision Template document (never two independent reads — this is the single-copy-propagation guarantee 147J.0 §4.3 requires):

1. `citation_text` — the resolved document's own `eligible_authority` field, copied verbatim.
2. The `EligibleAuthorityDeclaration` that `AuthorityRegistry.resolve()` returns for the same `(template_ref, template_version)` pair — under the preferred Option C (schema-artifact-backed Registry, §7), this is literally the same read as (1); under Option B (a hypothetical independent filesystem store), this is a second, separate read the Resolution capability performs against separate storage.

### 6.3 Template identity, citation, and declaration ownership

- **Template identity** (`template_id`/`version` inside the resolved document) is owned by whoever authors/versions Decision Templates (a governance-authoring act, out of scope for this phase and for AES itself — AES only *reads* already-authored templates).
- **Citation ownership**: the resolved document's `eligible_authority` field is the sole source of `citation_text`; Resolution never summarizes, truncates, or re-derives it (mirroring AEMIC-REQ-019's "sourced by the caller, verbatim... never evaluated, interpreted, or verified by this package").
- **Declaration ownership**: the Registry (§7) — Resolution consumes, never constructs, an `EligibleAuthorityDeclaration`.

### 6.4 Failure model

| Condition | Owner exception (AES-level, §12) |
|---|---|
| No template document exists for `(template_ref, template_version)` | `DecisionTemplateNotFoundError` |
| Template document exists but fails schema validation (reusing the CLI's existing `template-inspect`/`verify --related` structural check, `governance/verification.py:596-614` — not new validation logic) | `DecisionTemplateMalformedError` |
| Template document exists, validates, but its `eligible_authority` field resolves to an empty/whitespace-only string | `DecisionTemplateCitationEmptyError` |
| Registry lookup for the same pair fails | Propagated as the Registry's own §7 failure classification, not conflated with a template-resolution failure |

### 6.5 Cache policy

**No caching across evaluation attempts.** Every Stage 1 and every Stage 2 call re-resolves from scratch. This is a deliberate simplicity choice consistent with 147J.0 §6.2's "Stage 2 always reads the Registry's *current* state at Stage 2 time, never a cached Stage 1 read" — extending the same no-cache discipline to template resolution avoids a second, harder-to-reason-about staleness class alongside the Registry's own. A future concrete `AuthorityRegistry` implementation *may* cache internally (§7), but Resolution itself, and AES's use of it, never assumes or relies on that.

### 6.6 Determinism

Resolution is a pure function of `(template_ref, template_version, <current on-disk template state>)` — deterministic *given* fixed storage content at read time, exactly matching `AuthorityRegistry.resolve()`'s own contractual determinism (`registry.py:26-34`).

### 6.7 Versioning

`template_version` is part of the resolution key, not a separate concern — resolution never resolves "the latest version" implicitly; it always resolves the exact `(template_ref, template_version)` pair Session carries. Template supersession (`supersession_rules` in the schema) governs *authoring-time* validity, not *resolution-time* behavior — resolving an explicitly-superseded-but-still-on-disk version is not this phase's concern to forbid; that is future contract work (§18 item 3).

### 6.8 Retry semantics

Resolution performs no internal retry — a single filesystem read (or equivalent), once, per call. Retry, if ever needed, is AES's caller's responsibility (e.g. a CLI layer retrying a failed Stage 2 attempt as a whole), never something Resolution itself hides.

### 6.9 Interaction with Registry

Resolution is the Registry's only caller (§5.12), and calls it exactly once per stage per evaluation attempt, always after (or as part of the same read as) deriving `citation_text`, never before confirming the template document itself resolved.

### 6.10 Why resolution must precede evaluation

`evaluate()` accepts `declaration` and `citation_text` as already-resolved parameters and performs no I/O of its own (AEMIC-REQ-076/077, `evaluation.py:3-8`) — this is not a design preference this phase could override even if desired; it is a structural fact about the already-verified, unmodified evaluator. Resolution is therefore, definitionally, a pre-evaluation, caller-side step — this phase's "before evaluator" placement (147J.0 §4.2) is the only lawful placement class, not one of several equally valid options.

---

## 7. Authority Registry Boundary

Architecture only, restated and extended from 147J.0 §8 — no implementation.

### 7.1 Abstract responsibilities

Exactly the one `resolve(template_ref, template_version) -> Optional[EligibleAuthorityDeclaration]` method already frozen by AEM-001 §4.5 and `registry.py:17-24`. No `create`/`persist`/`delete`/`list`/`enumerate` method is added by this phase, and none should ever be added to this ABC (AEMIC-REQ-042) — a future write path, if one is ever needed, belongs on a separate authoring-side interface, not on `AuthorityRegistry`.

### 7.2 Lookup API expectations

Pure function of its two inputs at any fixed point in time (AEMIC-REQ-043); returns `None`, never raises, for "no Declaration exists" (AEMIC-REQ-044) — this is an ordinary, expected outcome, not an error condition.

### 7.3 Failure classifications

Exactly two, already named and unmodified: `AuthorityRegistryUnavailableError` (storage could not be consulted at all) and `AuthorityRegistryCorruptError` (storage answered but the record is structurally malformed or a duplicate/conflict was detected) — AEM-001 §11.3 already warns against conflating either with a legitimate `None` return (INDETERMINATE downstream).

### 7.4 Identity model

Keyed by `(template_ref, template_version)` exactly, no first-match-among-duplicates resolution (AEMIC-REQ-045).

### 7.5 Version semantics

Each `(template_ref, template_version)` pair identifies at most one Declaration; version is part of the lookup key, not resolved implicitly to "latest."

### 7.6 Duplicate behavior

A future concrete implementation MUST raise `AuthorityRegistryCorruptError` on detecting two conflicting Declarations for the same key rather than silently picking one (AEMIC-REQ-045/048).

### 7.7 Restart behavior

Read-mostly, filesystem-backed (§7.9) storage is inherently restart-durable with no in-memory-only state to lose; a concrete implementation's own internal cache (if any) must be safe to cold-start with an empty cache and repopulate lazily.

### 7.8 Offline behavior

If the Registry's storage is entirely unavailable (e.g. missing directory, permission failure), `resolve()` raises `AuthorityRegistryUnavailableError` — AES's own error ownership (§5.5) translates this into a disclosed, non-gating failure, never a silent `None`.

### 7.9 Immutability expectations

Once written, a Declaration record is never mutated in place — a new template version gets a new Declaration keyed by the new `(template_ref, template_version)` pair; this mirrors both existing house precedents this codebase already has for durable records (`cltr/persistence.py`'s content-addressed store, `governance/publication/storage.py`'s write-once `records/<record_id>.json`).

### 7.10 Authority source expectations

Per 147J.0 §4.3/§8's preferred **Option C (schema-artifact-backed)**: the concrete Registry resolves from the *same* canonical Decision Template document Resolution (§6) reads its `eligible_authority` citation from — not an independently-authored, potentially-divergent store. This is the structural guarantee that keeps `citation_text` and `declaration` from ever silently drifting apart for a well-formed template (147J.0 §4.3).

### 7.11 Repository interaction

None. Per `governance_record_provenance`'s own already-disclosed limitation (`record.py:193-198`: `"repository_provenance.available is false"`), the Registry (like the rest of this pipeline) performs no git/repository read — Decision Templates are ordinary on-disk artifacts under `.pcae`'s own storage tree (or an equivalent future location), not git-history-derived.

### 7.12 Why Registry remains outside the evaluator

Structural, not stylistic: `evaluate()` has no I/O of any kind (AEMIC-REQ-073/076/077) — the Registry's entire reason to exist as a *separate* abstraction is to be the one place, outside the evaluator, where "resolve a Declaration" is a named, testable, independently-swappable operation (in-memory fake for tests today, filesystem-backed for real tomorrow) without the evaluator's own purity guarantee ever being put at risk by a storage change.

---

## 8. Two-Stage Evaluation Lifecycle

### 8.1 Stage 1 — Advisory evaluation

- **Timing:** at or before Confirmation (`SessionState.AWAITING_CONFIRMATION` → `CONFIRMED`), consistent with IWC-REQ-026's own framing of Confirmation as non-authoritative.
- **Ownership:** invoked by AES's caller (§8.2) — never by Interactive Workflow's own transition logic, and never automatically triggered *by* a `SessionState` transition (that would risk exactly the gating-confusion 147J.0 §3.2/§10 flags for Strategy B).
- **Replay:** trivial — Stage 1 has no persisted state; repeating it simply recomputes.
- **Persistence:** none — Stage 1's outcome is ephemeral, at most surfaced as advisory Session or Preview *display* state (never a `Session` field, never a governance artifact), consistent with 147I's disclosure-only framing.
- **Staleness:** Stage 1 is *definitionally* stale by the time Publication occurs (§6.1/§6.2 of 147J.0, grounded in IWPC-REQ-144/147's "not authority-relevant" characterization of everything upstream of Publication's commit point) — this is expected, disclosed behavior, never treated as a defect.
- **Supersession:** Stage 1 is unconditionally superseded by Stage 2 for citation purposes (§8.3).

### 8.2 Who invokes each stage

Since AES's caller must already hold the Session (§5.2), and Interactive Workflow itself must never call into AES as part of its own transition logic (§3 invariant 11, §5.13), the invoking caller at each stage is a component **above** both Interactive Workflow and Publication — the same caller-side layer that already orchestrates the interactive-workflow → publication-handoff → publication-execution sequence today (the CLI/application layer, e.g. `interactive_workflow/application/{session_service,publication_service}.py`, which is already the layer that sequences these steps without being *inside* either Session or the Coordinator). This phase names this requirement — an above-both orchestrating caller invokes AES at each stage — as an architectural constraint on any future 147K contract; it does not select the exact call site inside `application/` (that is 147K's contract-freeze-level decision, §18 item 1).

### 8.3 Stage 2 — Publication freshness evaluation

- **Timing:** immediately before CHGR construction (`build_publication_record`), and strictly outside the Publication Coordinator's own `execute()` transaction (§5.8) — the Coordinator's caller runs Stage 2, obtains the AER's `citation_text`, and only then invokes `Coordinator.execute()` with a readiness package whose (future, §14) AER-reference field is already populated.
- **Ownership:** AES exclusively (§5.13) — never the Coordinator itself, preserving PEC-REQ-115/116.
- **Replay:** Since `evaluate()` is deterministic and side-effect-free, Stage 2 is safely replayable from persisted inputs; a retried Publication attempt (per IWPC-001 §20's replay-protection classification) may legitimately trigger a fresh Stage 2 recomputation — tolerated and disclosed as expected, never treated as an error (147J.0 §6.2; full replay matrix, §11).
- **Persistence:** Stage 2's inputs and outcome are persisted together as one immutable AER (§10).
- **Outcome supersedes Stage 1:** unconditionally, for citation purposes — only Stage 2's `citation_text` is ever cited into `authority_basis_claimed`. Stage 1 exists solely to inform the human decision-maker earlier in the workflow.

### 8.4 Duplicate publication / publication retry

If a Publication Execution attempt is retried after a failure that occurred *before* the Coordinator's atomic write (e.g. a network-adjacent failure in whatever future transport layer exists), a fresh Stage 2 attempt for the same `package_id` is expected — AES's Stage 2 idempotency (§5.9) governs whether that fresh attempt reuses the already-persisted AER or produces a new one, per §11's restart matrix.

### 8.5 Why Stage 2 must replace, never merge, Stage 1

Merging would require defining a reconciliation rule for disagreement between two evaluations of possibly-different underlying data (a Registry or template update between stages) — exactly the "silently resolved in the record's favor" outcome CHGR-REQ-097 forbids ("Any gap between valid human action and eligibility under the applicable governing authority model SHALL be surfaced, never silently resolved"). A strict, unconditional replace-not-merge rule has no reconciliation logic to get wrong, and any Stage-1/Stage-2 disagreement is surfaced as a disclosed fact (§8.6/§16), never quietly averaged, voted, or overridden by whichever stage a future maintainer happened to trust more.

### 8.6 Stage 1/Stage 2 disagreement disclosure

Architecture-level requirement only (147J.0 §12 item 4 left the exact UX open, correctly, for this phase): the AER (§10) MUST carry a `stage_1_outcome_ref` field alongside its own Stage 2 outcome whenever a Stage 1 evaluation for the same `package_id`/session preceded it, so that a disagreement is *structurally visible* (two outcomes, both retrievable, never one silently discarded) even before any future presentation-layer work decides how to *display* that disagreement to a human. This is an architecture decision (the AER's shape must support disclosure); the presentation mechanism itself remains future, separately governed UX/contract work (§18).

---

## 9. End-to-End Lifecycle

### 9.1 Sequence diagram

```
Human      Session       AES        Resolution    Registry    Evaluator   Readiness   Publication   CHGR
 |            |            |             |            |            |          |            |          |
 |--create--->|            |             |            |            |          |            |          |
 |  (owner_identity bound, IWC-REQ-036)  |             |            |          |            |          |
 |            |            |             |            |            |          |            |          |
 |  ... Evidence / Clarification / Decision selection (unchanged, out of AES's scope) ...   |          |
 |            |            |             |            |            |          |            |          |
 |            |<--(above-both caller reads Session: owner_identity, template_ref/version)---|          |
 |            |            |             |            |            |          |            |          |
 |            |  Stage 1 evaluate_stage_1(...)         |            |          |            |          |
 |            |----------->|             |            |            |          |            |          |
 |            |            |--resolve--->|            |            |          |            |          |
 |            |            |             |--resolve()->|            |          |            |          |
 |            |            |             |<--Optional[Declaration]--|          |            |          |
 |            |            |<--(declaration, citation_text)---------|          |            |          |
 |            |            |--evaluate()------------------------->  |          |            |          |
 |            |            |<--AuthorityEvaluationOutcome (Stage 1)-|          |            |          |
 |            |    (advisory outcome surfaced to human; NOT persisted)        |            |          |
 |            |            |             |            |            |          |            |          |
 |--confirm-->|            |             |            |            |          |            |          |
 |  (SessionState -> Confirmed, IWC-001; unaffected by AES)         |          |            |          |
 |            |            |             |            |            |          |            |          |
 |            |  PublicationHandoff.build_package(...) [unmodified]-|--------->|            |          |
 |            |            |             |            |            |          |            |          |
 |            |  Stage 2 evaluate_stage_2(..., package_id)          |          |            |          |
 |            |----------->|             |            |            |          |            |          |
 |            |            |--resolve(FRESH)--------->|            |          |            |          |
 |            |            |             |--resolve()->|            |          |            |          |
 |            |            |             |<--Optional[Declaration]--|          |            |          |
 |            |            |--evaluate()------------------------->  |          |            |          |
 |            |            |<--AuthorityEvaluationOutcome (Stage 2)-|          |            |          |
 |            |            |--persist AER (O_CREAT|O_EXCL by package_id)------>|            |          |
 |            |            |<--AuthorityEvaluationRecord (with citation_text)--|            |          |
 |            |            |             |            |            |  (AER ref attached to readiness   |
 |            |            |             |            |            |   package — future field, §14)    |
 |            |            |             |            |            |          |            |          |
 |--authorize (operator_id)-------------------------------------------------->|----------->|          |
 |            |            |             |            |            |          |  Coordinator.execute() |
 |            |            |             |            |            |          |  (PEC-REQ-051 order,    |
 |            |            |             |            |            |          |   unmodified)           |
 |            |            |             |            |            |          |            |--build-->|
 |            |            |             |            |            |          |            | authority_basis_claimed
 |            |            |             |            |            |          |            | = AER.citation_text  |
 |            |            |             |            |            |          |            |  (PEC-REQ-115, MAY,  |
 |            |            |             |            |            |          |            |   now resolvable)    |
 |<-----------------------------------------------------------------------------------------CHGR published---------|
```

### 9.2 Human confirmation, replay, restart in the sequence

- **Human confirmation** occurs exactly once, at `decision-session confirm` (unmodified) — Stage 1 precedes it (advisory only, never gating it), Stage 2 follows it (never re-triggers or invalidates it).
- **Replay:** a retried Stage 2 call (e.g. because a prior Publication attempt failed downstream) is idempotent per `package_id` (§5.9); a retried Publication Coordinator `execute()` call is unaffected in its own idempotency (`_check_replay`, `coordinator.py:235-241`) — the two idempotency mechanisms are independent and never interfere.
- **Restart:** since neither Session, Registry, nor the AER store hold any AES-owned in-memory-only state (§5.6), a process restart at any point in this sequence loses no AES-relevant state beyond what §11's restart matrix already accounts for.

---

## 10. Persistence Architecture

### 10.1 What persists

- **Authority Evaluation Record (AER)** — one per Stage 2 evaluation attempt, keyed by `package_id`. Wraps: the `AuthorityEvaluationOutcome` (already-immutable per `models.py:98-152`), `stage="stage_2"`, `package_id`, an optional `stage_1_outcome_ref` (§8.6), and a `record_digest` (mirroring every other durable artifact in this codebase, e.g. `body1["record_digest"] = compute_record_digest(body1)` in `record.py:180`).
- The Declaration and resolved-template content that fed a given AER are **not** separately persisted by AES — the AER's own `outcome.declaration_ref` (already a field on `AuthorityEvaluationOutcome`, `models.py:115`) and `citation_text` are sufficient provenance; the source Declaration/template themselves are the Registry's own durable state (§7.9), not AES's to duplicate.

### 10.2 What is recomputed

- Every Stage 1 outcome (never persisted at all, §8.1).
- A duplicate Stage 2 attempt for a `package_id` with **unchanged** inputs recomputes and finds the already-persisted AER unchanged (idempotent no-op); with **changed** inputs, §11's restart matrix governs.

### 10.3 What is immutable

The AER itself, once written — following every other durable-record precedent in this codebase (CHGR artifacts, `PublicationRecordStore`'s `records/<record_id>.json`) — is never mutated in place; a changed evaluation produces a new AER (with a new `record_id`), never an edit to an old one.

### 10.4 What receives identifiers

Each AER receives its own `record_id` (e.g. `aer-<uuid4hex>`, mirroring `chgr-<uuid4hex>`/`pubexec-<uuid4hex>` naming in `record.py:87-88`/`coordinator.py:130`).

### 10.5 What receives digests

Each AER receives a `record_digest` computed the same way every other durable record in this codebase computes one (`compute_record_digest`, already used identically for all four CHGR artifact families).

### 10.6 What is Session state

Nothing new — `Session.owner_identity`/`template_ref`/`template_version` are read, not added to (§3 invariant 9, §5.2). No Stage 1 or Stage 2 outcome, and no AER reference, is ever written back onto `Session` or `SessionState`.

### 10.7 What belongs in Readiness

A **new, additive reference field** on a future `PublicationReadinessPackage` (§14) — `authority_evaluation_ref: Optional[{record_id, record_digest, record_family}]` — populated by whichever component builds the readiness package (today: `PublicationHandoff.build_package`, or its future caller) *after* Stage 2 has produced an AER. This mirrors every other existing readiness-package reference field exactly (`evidence_refs`, `clarification_refs`, `audit_refs`, `preview_id`/`preview_digest`, `confirmation_request_id`/`confirmation_response_id` — all references, never payload copies, `publication_handoff/models.py:79-104`).

### 10.8 What belongs in CHGR

Only `citation_text`, flowed forward as `authority_basis_claimed` (§13, §14) — never the full AER, never the Declaration, never `declaration_ref`. CHGR's own `governance_record_provenance` artifact could, in a *future*, separately governed contract amendment, additionally carry an `authority_evaluation_ref` citing the AER itself (§18 item 6) — this phase does not decide that; it only notes the field would be additive and schema-optional, consistent with CHGR-001 v1.2's own existing "schema-optional, `limitations`-disclosed-when-absent" pattern for `authority_basis_claimed` (CHGR-REQ-207/208).

### 10.9 What remains transient

Stage 1 outcomes (§8.1); AES's own internal resolution intermediate state (the resolved Decision Template document object itself, once `citation_text`/`declaration` are extracted); any in-flight, not-yet-persisted Stage 2 attempt.

### 10.10 No schemas introduced

Per the No-Go Boundary (§15/§21 of the prompt), this phase describes the AER's *shape* in prose (§10.1) but defines no JSON Schema file, no dataclass, no `src/pcae/**` change — the AER's concrete schema is 147K's (Contract Freeze) work, not this phase's.

---

## 11. Replay Architecture

### 11.1 Replay guarantees

Because `evaluate()` is total, deterministic, and side-effect-free (AEMIC-REQ-074/075/076), and because AES itself holds no hidden state (§5.6), **every** AES invocation is safely repeatable from its own recorded inputs — the only question replay architecture must answer is *what happens to already-persisted output* when a repeat occurs, not whether recomputation itself is safe.

### 11.2 Restart matrix

| Restart point | Stage 1 effect | Stage 2 effect |
|---|---|---|
| Before Stage 1 | No effect — Stage 1 simply runs (or doesn't) whenever its caller next invokes it | N/A |
| After Stage 1, before Confirmation | Stage 1's outcome is lost (never persisted, §8.1) — expected; a fresh Stage 1 recomputation on resumption is equivalent, since Stage 1 is advisory-only and carries no commitment | N/A |
| Before Stage 2 | N/A | Stage 2 has not yet run; resumes normally, reading current Registry/template state |
| After Stage 2, before Publication authorization | N/A | AER already durably persisted (§10.3); resumption reads the existing AER via `package_id`, never recomputes unless explicitly asked to |
| After Publication authorization, before Coordinator commit | N/A | AER unaffected — it was already durable before this point; a retried Coordinator `execute()` uses the already-persisted AER's `citation_text` unchanged |
| After Coordinator commit (CHGR exists) | N/A | AER remains as the durable, immutable record of what was cited; never re-evaluated post-publication (mirrors `_check_replay`'s own "already consumed... refusing as Replay" discipline, `coordinator.py:235-241`) |
| Publication retry (Coordinator-level, distinct from AES-level) | N/A | Coordinator's own `_check_replay` (unmodified) refuses a second publish for an already-published `package_id` regardless of AES/AER state — AES's replay guarantees never override Publication's own, separately-owned replay protection |
| Duplicate confirmation | N/A (Confirmation itself is IWC-001's own replay-protected concern, unaffected by AES) | N/A |
| Duplicate readiness (a second `build_package` call for the same session/transition) | N/A | If a second readiness package is built, it may cite a *new* Stage 2 AER (a fresh `package_id`) — AES does not itself deduplicate across distinct `package_id`s; that is Readiness's own concern (unmodified by this phase) |
| Duplicate publication attempt | N/A | Governed by the Coordinator's own idempotency marker (`published/<package_id>.json`, `storage.py:8-16`), unaffected by AES |
| Registry evolution (Declaration changed between Stage 1 and a later Stage 2, or between two Stage 2 attempts) | N/A | Each Stage 2 attempt always reads the Registry's *current* state (§6.5's no-cache policy) — a changed Declaration produces a genuinely different, freshly-computed outcome, disclosed as such (§8.5/§8.6), never silently reconciled with an earlier attempt |
| Decision Template evolution (citation text changed) | N/A | Same — Stage 2 always re-resolves the template fresh; a changed `eligible_authority` text produces a new `citation_text` in the new AER |
| Citation evolution | N/A | Subsumed by "Decision Template evolution" above — citation text is derived from the template, not tracked independently |

---

## 12. Failure Ownership

Complete matrix — every failure type names origin, owner, recovery owner, user-visible owner, logging owner, retry owner.

| Failure type | Origin | Owner | Recovery owner | User-visible owner | Logging owner | Retry owner |
|---|---|---|---|---|---|---|
| Registry unavailable | Registry's storage layer | AES (translates to a disclosed AES-level condition, §5.5) | Whoever operates the Registry's storage (future, out of this phase's scope) | AES's caller (§8.2) surfaces the disclosed failure to the human | AES (every Registry call attempt, success or failure, §17) | AES's caller decides whether/when to retry — AES itself performs no silent retry (§6.8) |
| Template missing (`DecisionTemplateNotFoundError`, §6.4) | Resolution (inside AES) | AES | Whoever authors Decision Templates (governance-authoring act, out of scope) | AES's caller | AES | AES's caller |
| Citation mismatch (n/a as a distinct condition — see "Template identity mismatch" below) | — | — | — | — | — | — |
| Identity mismatch (`TemplateIdentityMismatchError`, from `evaluate()` itself) | Evaluator (unmodified, `evaluation.py:96-100`) | Evaluator raises; AES propagates unchanged (§5.5) | AES's caller — indicates Resolution supplied a Declaration whose own identity disagrees with the evaluation's `(template_ref, template_version)`, a Resolution-internal-consistency bug, never a normal runtime condition | AES's caller | AES (logs the propagated exception verbatim) | Not retryable without fixing Resolution's own internal consistency — this is a programming-error-class failure, not a transient one |
| Duplicate declaration (`AuthorityRegistryCorruptError` for a duplicate) | Registry's storage layer | AES translates (§5.5), same as "Registry unavailable" row | Whoever authors/writes Declarations (future Registry-implementation phase's write-path owner) | AES's caller | AES | Not retryable until the underlying duplicate is repaired at the storage layer |
| Serialization failure (AER `to_payload`-equivalent, future) | AES's own AER serialization (§10, future 147K contract) | AES | AES (a serialization defect is AES's own bug to fix) | AES's caller | AES | Not retryable without a code fix |
| Restart inconsistency | N/A — §11's restart matrix shows no inconsistency class exists by design (every restart point has a defined, safe resumption) | — | — | — | — | — |
| Publication supersession (Stage 2 outcome differs from Stage 1) | Expected behavior, not a failure (§8.5) | AES (produces the disagreement-visible AER, §8.6) | N/A — not an error condition | AES's caller (future UX, §18 item 4) | AES (both outcomes logged, §17) | N/A |
| Stale advisory outcome (Stage 1 no longer matches Stage 2) | Expected behavior, not a failure (§8.1/§8.5) | Same as above | N/A | Same as above | Same as above | N/A |
| Missing citation text at evaluator level (`MissingCitationTextError`) | Evaluator (unmodified) — only reachable if Resolution supplies `citation_text=None` while `evaluation_result` computes to `ELIGIBLE`, which per §6.4 should already have been refused earlier as `DecisionTemplateCitationEmptyError` | Evaluator raises; AES propagates | Indicates a Resolution-internal-consistency gap between §6.4's own empty-citation check and what it actually passed to `evaluate()` — a Resolution bug | AES's caller | AES | Not retryable without a Resolution code fix |
| AER write failure (disk-level, mirrors `PublicationStorageError`) | AES's own AER store (§10) | AES | Operator (disk/permissions issue) | AES's caller | AES | AES's caller may retry the whole Stage 2 call — the AER write is atomic (temp file + fsync + `os.replace`, §5.7), so a failed write leaves no partial artifact to clean up, mirroring `_write_atomic_json`'s own guarantee (`storage.py:38-52`) |

---

## 13. Evaluation Outcome Consumption

### 13.1 Per-consumer architecture

| Consumer | How it uses `AuthorityEvaluationOutcome` | Explicitly prohibited |
|---|---|---|
| Interactive Workflow (advisory, Stage 1) | Reads the outcome to *display* to the human before Confirmation — e.g. "advisory: this identity does not appear in the declared eligible set for this template" | Never gates, blocks, or auto-selects a transition based on the outcome (§3 invariant 6; AEM-REQ-003/037) |
| Readiness (`PublicationReadinessPackage`, future field §14) | Carries a reference (`{record_id, record_digest, record_family}`) to the Stage 2 AER — never the outcome payload inline | Never treats the reference's mere presence as proof of readiness completeness beyond what `PublicationHandoff.is_ready`/`validate_completeness` (unmodified) already require |
| Publication (Coordinator) | Reads only `AER.outcome.citation_text` (via the readiness package's reference), cites it verbatim into `authority_basis_claimed`, per PEC-REQ-115's already-frozen "MAY... never from an independent judgment" | Never reads `evaluation_result`, `declaration_ref`, or any other AER field as a gating input to `execute()`'s own validation sequence (§5's `_validate_*` steps, unmodified) |
| CHGR (`build_publication_record`) | `authority_basis_claimed = citation_text` when present; `limitations` entry disclosing its absence otherwise (already-existing mechanism, `record.py:248-253`, simply now sometimes populated instead of always absent) | Never derives `assurance_level` (a distinct, `evidence_kind`-sourced field, §5 of 147J.0) from any AES output — the two remain independent per Decision C |
| Future reporting / audit / inspection / diagnostics | Read-only queries against the AER store (§17) | Never a write path — reporting/audit/inspection are exclusively read consumers |

### 13.2 Explicit prohibition (restated per prompt §13)

`AuthorityEvaluationOutcome` and the AER that wraps it are never, under this architecture, treated as: an authorization, a permission, an execution trigger, or a policy decision — unless a future contract explicitly amends AEM-001/AEMIC-001/PEC-001/CHGR-001 to grant that meaning, which no phase to date (147G-147J.0) has done and this phase does not propose.

---

## 14. Schema Impact Assessment

No schema is modified by this phase. Impact matrix for *future* phases:

| Area | Required future amendment | Optional | No-change | Rationale / migration implication |
|---|---|---|---|---|
| Session | No | No | **Yes** | AES only reads existing `owner_identity`/`template_ref`/`template_version`; no new field needed (147J.0 §3.3) |
| Readiness (`PublicationReadinessPackage`) | **Yes** — one new, additive, optional `authority_evaluation_ref` field (§10.7) | — | — | Additive-only; existing fields (`evidence_refs`, etc.) are unaffected; a package built by *old* code (without the field) remains valid — the field should be optional at the dataclass level, defaulting to `None`, so no existing caller of `PublicationHandoff.build_package` breaks. Migration: none needed for existing persisted packages, since none currently carry evaluation data to migrate |
| Publication (`PublicationAuthorizationEvent`, Coordinator internals) | No | Optional — the Coordinator's `_PROHIBITED_PACKAGE_FIELDS` set (`coordinator.py:54-62`) may eventually need review to confirm `authority_evaluation_ref` is *not* added to that prohibited list (it is a citation reference, not a `chgr_id`/`publication_state`/`publication_result`/`authority_token`/`execution_state` — none of which it resembles) | — | No structural change to the Coordinator's own validation/execution logic — it already treats readiness-package fields opaquely except for the specific prohibited set |
| CHGR (`human_governance_record` schema) | No | **Yes** — `authority_basis_claimed` already exists as an optional field (CHGR-REQ-207/208); this phase's integration lets it be *populated* rather than requiring a new field | — | Zero schema change: the field, its optionality, and its `limitations`-disclosure-when-absent rule are all already frozen in CHGR-001 v1.2 |
| Decision Templates | No | No | **Yes** | The existing `decision_template.schema.json` (`eligible_authority`, etc.) is already sufficient for Resolution to read from; no new field needed |
| Authority declarations | **Yes** (future, separate Registry-implementation phase) | — | — | A concrete `AuthorityRegistry` needs an on-disk storage schema for `EligibleAuthorityDeclaration` — but per Option C (§7.10), this may be *derived from* the existing Decision Template schema rather than requiring an independent new schema, minimizing new-schema surface |
| Governance records (provenance) | No | **Yes** — `governance_record_provenance` could, in a future contract amendment, gain an `authority_evaluation_ref` citing the AER directly (§10.8) | — | Purely additive if ever adopted; not required for `authority_basis_claimed` population, which needs only the citation *text*, already flowing without this optional addition |

---

## 15. Integration Boundaries

### 15.1 Strict prohibitions (restated verbatim per prompt §15)

- **Interactive Workflow SHALL NOT** evaluate authority. (Enforced architecturally: Session/Confirmation/state-machine code never imports or calls AES; AES is invoked by a caller *above* Workflow, §8.2, never *by* Workflow itself.)
- **Publication Coordinator SHALL NOT** resolve authority. (Enforced: the Coordinator's own explicit import-exclusion list, `coordinator.py:16-19`, already forecloses this; this architecture adds no import from `coordinator.py` to AES or Resolution.)
- **Evaluator SHALL NOT** resolve Registry. (Already true and unmodified, AEMIC-REQ-073/077; this phase changes nothing about `evaluation.py`.)
- **Registry SHALL NOT** orchestrate lifecycle. (Enforced: `AuthorityRegistry`'s one-method ABC shape is unmodified, §7.1; it has no awareness of `SessionState`, Publication, or CHGR.)
- **Authority Evaluation Service SHALL** coordinate all integration. (§5 defines AES as the sole orchestrator of identity-read, resolution, evaluation, and AER production.)

### 15.2 Responsibility matrix

| Component | Evaluate authority | Resolve Registry | Resolve Decision Template | Own `claimed_identity` | Own lifecycle transitions | Cite into CHGR |
|---|---|---|---|---|---|---|
| Interactive Workflow | No | No | No | No (reads only) — owns the *source field*, `owner_identity`, but never itself performs evaluation | **Yes** | No |
| AES | **Yes** | No (delegates to Registry) | **Yes** (internally, §6) | No (reads only) | No | No (produces the citation; does not itself write CHGR) |
| Decision Template & Declaration Resolution (internal to AES) | No | No (delegates to Registry) | **Yes** | No | No | No |
| Authority Registry | No | **Yes** (is the lookup) | No | No | No | No |
| Evaluator (`evaluate()`) | **Yes** (is the evaluation) | No | No | No | No | No |
| Readiness | No | No | No | No | No (reads `SessionState` as of build time only) | No (carries a reference only) |
| Publication Coordinator | No | No | No | No | No | **Yes** (citation-only, PEC-REQ-115) |
| CHGR construction | No | No | No | No | No | **Yes** (is the citation target) |

---

## 16. Security Architecture

| Threat | Architectural mitigation |
|---|---|
| Tampering (AER modified post-write) | AER is immutable once written (§10.3), digest-covered (§10.5) exactly like every other durable record in this codebase; a future verification-layer check (mirroring `verify --related`) can detect a digest mismatch, though — consistent with `references.schema.json`'s existing documented discipline (`record.py:34-38`) — digest *matching* is a verification-layer responsibility, not a schema/write-time guarantee |
| Stale evaluations | Structurally addressed by the two-stage model itself (§8) — Stage 2 always supersedes Stage 1, and Stage 2 always re-resolves fresh (§6.5's no-cache policy); "staleness" is a disclosed, expected property of Stage 1, never silently treated as current |
| Citation substitution (a different template's citation attached to this evaluation) | Prevented structurally by `evaluate()`'s own `TemplateIdentityMismatchError` check (`evaluation.py:91-100`, unmodified) — Resolution's derived `declaration` must agree with the evaluation's own `(template_ref, template_version)`, or evaluation refuses before producing an outcome |
| Registry poisoning (a forged Declaration inserted into storage) | Out of AES's own control surface — this is squarely a future Registry-implementation phase's write-path security concern (§7.9's immutability + a future authoring-side access-control mechanism, not designed here); AES itself never writes Declarations, closing the "AES as an attack vector for Registry poisoning" class entirely |
| Identity substitution (a caller passing a `claimed_identity` other than the bound session's own) | Prevented structurally: AES's public interface (§5.11) requires the caller to supply `claimed_identity`, but the *architectural rule* (§5.2, §8.2) is that the only lawful caller-side source is `Session.owner_identity`, itself already protected from post-creation substitution by IWC-REQ-037 ("a resumption request from an identity other than the one bound at creation SHALL be rejected"); a future 147K contract should make this a structural parameter (deriving `claimed_identity` from a `Session` object AES itself reads, rather than accepting it as a bare string a caller could substitute) — flagged here as a contract-freeze-level hardening recommendation, not implemented by this phase |
| Template substitution (a caller supplying a `template_ref`/`template_version` other than the session's bound pair) | Same mitigation shape as identity substitution — a future 147K contract should have AES read `template_ref`/`template_version` directly from the same `Session` object it reads `owner_identity` from, rather than accepting them as independent caller-supplied strings, closing this substitution class by construction |
| Cross-session reuse (an AER from one session's evaluation cited into a different session's CHGR) | Prevented structurally: the AER is keyed by `package_id` (§10.1), which is itself unique per readiness package per session (`PublicationReadinessPackage.package_id`, already validated non-empty, `publication_handoff/models.py:108-109`); the readiness package's own `authority_evaluation_ref` (§10.7) can only be populated with the AER produced *for that specific `package_id`*, and the Coordinator's own package-identity validation (`_validate_authorization_applicability`, `coordinator.py:258-266`) already refuses a package/event mismatch, an analogous check a future 147K contract should extend to AER/package binding |
| Replay attacks (reusing an old, valid AER to publish a second time) | Prevented by the Coordinator's own, already-existing replay protection (`_check_replay`, `is_published(package_id)`), entirely independent of and unaffected by AES — a stale-but-valid AER cannot cause a second CHGR to be published, because the Coordinator refuses any second `execute()` for an already-published `package_id` regardless of what evaluation data accompanies it |
| Evaluation reuse (citing a Stage 1 outcome as if it were Stage 2) | Prevented structurally: only the AER (Stage-2-only, §8.3) carries a `citation_text` eligible for CHGR consumption (§13.1); Stage 1 outcomes are never persisted (§8.1) and therefore have no `record_id`/`record_digest` a readiness package could even reference |
| Duplicate publication | Governed entirely by the Coordinator's own existing idempotency marker (§11's restart matrix row), unaffected by AES |
| Authority confusion (mistaking a disclosed evaluation for a granted authorization) | The whole-architecture discipline of §3 invariant 6, §13.2's explicit prohibition, and every component's own naming (`AuthorityEvaluationOutcome`, never `AuthorityGrant`/`AuthorizationDecision`) — no field, method, or component name introduced by this phase could be mistaken for an authorization primitive, matching AEM-001 §8's own disclosure-only naming discipline |

---

## 17. Observability

| Concern | Architecture |
|---|---|
| Logs | AES logs every resolution attempt (success/failure), every Registry call (success/failure, with the specific exception class per §12), and every `evaluate()` invocation's outcome (`ELIGIBLE`/`INELIGIBLE`/`INDETERMINATE`) at both stages — mirroring the granularity `PublicationCoordinator._record_attempt` already applies to every publication attempt, accepted or refused (`coordinator.py:314-350`) |
| Traces | Each AES invocation carries its own `attempt_id`-equivalent (an evaluation identifier, §17 "evaluation identifiers" below), letting a Stage 1 and its corresponding later Stage 2 be correlated without conflating them (they remain structurally distinct per §8.6) |
| Diagnostics | A read-only diagnostic query surface (mirroring `pcae runtime inspect`'s own read-only posture) over the AER store — "show me every Stage 2 evaluation for package X," "show me every INELIGIBLE outcome in the last N attempts" — is future implementation work (147K+), but this phase requires the AER's shape (§10.1) to make such queries possible without any additional derived index |
| Inspection | Same surface as Diagnostics — no separate mechanism |
| Audit | The AER *is* AES's audit trail for evaluation (mirroring how `attempts/<attempt_id>.json` is the Coordinator's own audit trail, structurally separate from CHGR provenance per PEC-REQ-107) — a future 147K contract should require every Stage 2 attempt, successful or refused, to be durably recorded, not only successful ones (mirroring the Coordinator's own "every attempt -- accepted or refused -- is durably recorded" discipline, `coordinator.py:13-14`) |
| Phase reporting | This document itself, plus the No-Go Confirmation (§21) and standard phase-completion metadata — no new phase-reporting mechanism is introduced |
| Correlation identifiers | `package_id` is the primary cross-component correlation key already used throughout Publication (§10.1, §16); AES's own `record_id` is secondary, scoped to the AER itself |
| Evaluation identifiers | A future 147K contract should define an `evaluation_id` (or reuse `record_id` for Stage 2, and a separate ephemeral identifier for Stage 1's in-memory-only outcome) distinct from `package_id`, so multiple evaluation attempts against the same package (e.g. a repeated Stage 2 after a Registry update) remain individually distinguishable |
| Registry diagnostics | A concrete Registry implementation's own read-count/failure-count instrumentation is that future phase's concern; this phase requires only that `AuthorityRegistryUnavailableError`/`AuthorityRegistryCorruptError` remain distinguishable in whatever logging AES performs (§7.3, §12) |
| Service diagnostics | AES's own health (e.g. "is my Registry reachable") is a future implementation concern; this phase notes it should follow the same `pcae runtime inspect`/`pcae health` read-only, non-mutating pattern already established for every other governance-surface diagnostic in this codebase |

All of the above preserve disclosure-only semantics: every observability surface is read-only, none is a control surface, and none exposes a mechanism by which an observer could cause AES to skip resolution, skip evaluation, or fabricate an outcome.

---

## 18. Future Contracts

| # | Contract | Purpose | Scope | Dependencies | Required verification | Implementation prerequisites |
|---|---|---|---|---|---|---|
| 1 | **Authority Evaluation Service Contract** (new, e.g. AESIC-001) | Freeze AES's public interface (§5.11), error taxonomy (§5.5/§12), lifecycle (§5.6-§5.9), and the caller-side rule that `claimed_identity`/`template_ref`/`template_version` MUST be read from a `Session` object AES itself accepts (§16's substitution-hardening recommendation) | AES only — not Resolution or Registry individually | AEM-001, AEMIC-001 (both unmodified, referenced), IWC-001 (`Session` shape), this document | Independent Contract Verification (mirroring 147H's role for AEMIC-001) | 147J.0 + this phase's decisions frozen unchanged |
| 2 | **Decision Template Resolution Contract** (could be a section of #1, or standalone) | Freeze §6's resolution inputs/outputs/failure model/cache policy as binding requirements | Resolution capability only | Decision Template JSON Schema (unmodified), AuthorityRegistry ABC | Same | §6's architecture unchanged from this phase |
| 3 | **Authority Registry Implementation Contract** (new, e.g. AR-001 or a Registry-specific implementation contract) | Freeze the concrete Registry's storage layout, Option-C schema-artifact binding, duplicate-detection mechanics, and the exact digest/provenance scheme for citation-provenance binding (147I §15) | Concrete `AuthorityRegistry` subclass only — the ABC itself (AEM-001 §4.5) is not touched | AEM-001 §4.5 (ABC shape, frozen, unmodified), §7 of this document | Independent Implementation Verification | Contract #1 frozen (Registry is AES's sole internal collaborator) |
| 4 | **Evaluation Persistence Contract** | Freeze the AER's exact schema (§10.1's prose shape, made concrete), digest scheme, and storage layout (mirroring `governance/publication/storage.py`'s pattern) | AER only | Contract #1 | Independent Contract Verification + schema-conformance tests (mirroring CHGR's own `validate_chgr_artifact` gate) | Contract #1 frozen |
| 5 | **Evaluation Replay Contract** | Freeze §11's restart/replay matrix as binding requirements, including the idempotency-marker mechanics for Stage 2 (§5.9) | Replay behavior only | Contracts #1, #4 | Independent Contract Verification | Contracts #1, #4 frozen |
| 6 | **Schema amendments** (additive only, per §14) | `PublicationReadinessPackage.authority_evaluation_ref` (required — §14); optionally `governance_record_provenance.authority_evaluation_ref` (§10.8, optional) | IWC-001 (readiness package shape), possibly CHGR-001 | This document's §14 impact matrix | Independent Contract Verification, backward-compatibility check (existing packages without the field remain valid) | Contract #4 frozen (need the AER's final shape to write a correct reference) |

---

## 19. Future Implementation Roadmap

```
Architecture (this phase, 147J)
      │
      ▼
Contract Freeze (147K) — freezes Contracts #1-#6 above (§18), remains
      │                   contract-only, no implementation
      ▼
Independent Contract Verification — a dedicated verification phase (mirroring
      │                              147H's role for AEMIC-001), confirms the
      │                              frozen contracts are internally consistent,
      │                              consistent with AEM-001/AEMIC-001/IWC-001/
      │                              PEC-001/CHGR-001, and implementable
      ▼
Implementation — builds AES, Resolution, the concrete Registry (Option C),
      │           and AER storage, per the frozen contracts; no architectural
      │           decision-making, only construction against an already-frozen
      │           spec (mirroring 147G's role for AEMIC-001 itself)
      ▼
Independent Implementation Verification — mirrors 147H's own role: confirms
      │                                    the built implementation actually
      │                                    conforms to the frozen contracts,
      │                                    with independent test coverage
      ▼
Operational Readiness — mirrors 147I's own role: confirms the implementation
      │                   is ready for real integration use (not merely
      │                   "tests pass"), surfaces any remaining architectural
      │                   or operational gaps before certification
      ▼
Integration Certification — a final phase confirming the full, wired
                             AES → Resolution → Registry → Evaluator → AER →
                             Readiness → Publication → CHGR path functions
                             end-to-end against real (not merely unit-tested)
                             Decision Templates and Declarations
```

**Justification for this ordering:** it is the exact same seven-stage discipline this repository already used for the standalone evaluator itself (147F-series architecture → 147G implementation → 147H independent implementation verification → 147I operational readiness), simply repeated one layer outward for the *integration* surface, with an added Contract Freeze + Contract Verification pair up front (mirroring how AEM-001/AEMIC-001 themselves were frozen and verified *before* 147G's implementation began) — because integration touches more components (AES, Resolution, Registry, and eventually a readiness-package field) than the standalone evaluator did, freezing the contract surface before implementation begins is proportionately more important here, not less.

---

## 20. Integration Readiness Assessment

### 20.1 Resolved risks

- Orchestration ownership ambiguity (147I §31 item 3, 147J.0's own open work) — resolved: AES, unambiguously (§5.13).
- `claimed_identity`/citation/declaration single-source-of-truth risk (147I §13's "necessary future contract rule") — resolved architecturally: single-resolution-point discipline (§6.2) with a structural rather than merely disciplinary guarantee under Option C.
- Two-stage timing/supersession ambiguity (147I §29) — resolved: Stage 2 unconditionally supersedes Stage 1, with a structural disagreement-visibility requirement (§8.6).
- Contract-amendment risk — resolved: this architecture requires zero amendments to AEM-001/AEMIC-001/IWC-001/IWPC-001/PEC-001/CHGR-001 (§1, §14).

### 20.2 Remaining risks

- The exact AER schema/digest scheme is not yet frozen (deferred to 147K by design, §10.10, §18 item 4) — not a blocker, since this phase specifies its required shape in enough detail (§10.1) for 147K to freeze without re-deriving architecture.
- The exact call site inside `application/{session_service,publication_service}.py` that invokes AES at each stage is named as a requirement (§8.2: "an above-both orchestrating caller") but not pinned to a specific function — appropriately left to 147K's contract-freeze granularity, not this phase's.

### 20.3 Deferred risks

- Concrete Registry implementation security (Registry poisoning mitigation, §16) — explicitly deferred to a future Registry-implementation phase's own write-path design, as 147J.0 §8 already anticipated.
- Identity/template substitution hardening (§16) — flagged as a recommendation for 147K's contract (AES should read `claimed_identity`/`template_ref`/`template_version` from a `Session` object it accepts, not from bare caller-supplied strings) rather than resolved here, since it is a contract-shape decision, not an architecture-boundary decision.

### 20.4 Non-blocking observations

1. §8.2's "above-both orchestrating caller" requirement should be made explicit and testable in 147K (e.g. an architectural test asserting neither `interactive_workflow/session/**` nor `governance/publication/coordinator.py` imports AES), mirroring the AST-based import-exclusion tests this codebase already uses for IWC-001/PEC-001 boundaries.
2. The AER's `stage_1_outcome_ref` field (§8.6) is a *should*, not a strict *must*, at the architecture level — 147K should decide whether it is mandatory-when-a-Stage-1-outcome-exists or always-optional.
3. Observability instrumentation (§17) is described only at the level of "what must be loggable," not a concrete logging schema — appropriate for an architecture phase, but 147K should decide whether observability requirements belong in Contract #1 or a separate operational contract.

### 20.5 Blocking issues

**None.**

---

## 21. No-Go Boundary Confirmation

Per the authorizing prompt's explicit No-Go Boundary (§21): `src/pcae/**` was not modified. No schema was modified. No contract was modified. No test was modified. No Registry was implemented. No Authority Evaluation Service was implemented. No orchestration was implemented. No replay mechanism was implemented. No persistence mechanism was implemented. Runtime was not modified (`pcae runtime inspect` output unchanged: Observed / observe / unavailable). No plugin was modified. No lifecycle code was modified. CHGR construction code was not modified. Publication code was not modified. Interactive Workflow code was not modified. Only `docs/PHASE_147J_AUTHORITY_EVALUATION_INTEGRATION_ARCHITECTURE.md` plus ordinary task/phase bookkeeping files (`tasks/active/**`, `tasks/done/**`, `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`, `.pcae/phase-reports/**`) changed throughout this phase, confirmed by `git status --short` at finalization (§23).

---

## 22. Overall Verdict

**AUTHORITY EVALUATION INTEGRATION ARCHITECTURE COMPLETE.**

Every element required for completion is present: complete orchestration architecture (§5), complete Registry boundary (§7), complete lifecycle integration (§8, §9), complete replay architecture (§11), complete persistence architecture (§10), complete failure ownership (§12), complete security architecture (§16), complete integration boundaries (§15), complete roadmap (§19), and no unresolved architectural blocker (§20.5: none). The "with observations" qualifier was considered and rejected: §20's three non-blocking observations are ordinary next-phase refinements (mirroring 147J.0's own "with observations" items, none of which blocked 147J from starting), not architectural gaps in this document itself.

---

## 23. Recommended Next Phase

**147K — Authority Evaluation Integration Contract Freeze.** That phase shall freeze the complete integration architecture defined here, including: the Authority Evaluation Service contract (§5, §18 item 1), the Decision Template Resolution contract (§6, §18 item 2), the Registry interaction contract (§7, §18 item 3), lifecycle sequencing (§8, §9), replay semantics (§11, §18 item 5), the persistence model (§10, §18 item 4), failure ownership (§12), schema interaction rules (§14, §18 item 6), and disclosure-only consumption rules (§13). It shall remain contract-only — no implementation, exactly mirroring how AEM-001/AEMIC-001 were themselves frozen before 147G's implementation began.

**This recommendation is not an authorization.**

---

## Diagrams index (per prompt §22 requirement)

- **Component diagram:** §4.1
- **Sequence diagram:** §9.1
- **Responsibility matrix:** §15.2
- **Ownership matrix:** §9's per-boundary table (§4.2) and §5.2's input-ownership table
- **Persistence matrix:** §10 (prose-structured; §10.1-§10.9 each answer one persistence question per the prompt's own enumeration)
- **Replay matrix:** §11.2
- **Failure matrix:** §12
- **Contract dependency graph:** §18 (table) and §19 (roadmap diagram, which is also the dependency ordering)
