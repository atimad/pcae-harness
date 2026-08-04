# Phase 149H — Rollback Approval Evidence Architecture

Architecture-only phase. No production source, Permission Broker policy, or
frozen contract was modified. AG3/AG5 remain unimplemented. This document
defines the architecture that a future, narrowly-scoped contract-freeze
phase (recommended: 149I) will normatively freeze, and that a still-later
implementation phase will build.

## 1. Current Rollback Blocker

The truthful `PermissionBrokerRequest` for either rollback site
(`action_type="rollback"`, `execution_class="rollback"`) carries
`approval_present=False`, `simulation_only=True`. `POL-004`
(`MissingHumanApprovalRule`, `src/pcae/core/permission_broker_foundation.py:449-486`)
is applicable to `EXECUTION_CLASS_ROLLBACK` and resolves this to
`HUMAN_REVIEW`:

```python
class MissingHumanApprovalRule(PolicyRule):
    policy_id = "POL-004"
    applicable_execution_classes = frozenset({
        EXECUTION_CLASS_SHELL, EXECUTION_CLASS_BACKEND,
        EXECUTION_CLASS_ADAPTER, EXECUTION_CLASS_ROLLBACK,
    })
    def evaluate(self, request):
        if request.approval_present:
            return _not_triggered(self.policy_id)
        return PolicyResult(..., decision=DECISION_HUMAN_REVIEW,
                             decision_reason="missing_human_approval", ...)
```

A hypothetical `approval_present=True` request resolves to `ALLOW` (subject
to no other rule blocking). RWMPC-001 itself already recorded this as a
named BLOCKING finding, not a new observation of this phase:

> RWMPC-REQ-027 (BLOCKING): "Rollback-class Permission Broker coverage
> (AG3, AG5) is NOT SATISFIABLE under this contract until a future,
> narrowly scoped phase defines a legitimate `approval_present=True`
> evidence source." (`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md:353-367`)

The blocker is therefore **not** rollback policy semantics (POL-004's logic
is correct and stays unchanged) but the **absence of a trusted,
authenticated, provenance-bound approval evidence source**. That absence is
what this phase resolves architecturally.

## 2. AG3 / AG5 Semantics (Independently Reconstructed)

| | AG3 | AG5 |
|---|---|---|
| Function | `execute_rollback(root, job_id)` — `src/pcae/core/agent.py:5234` | `build_rollback_execution(root, per_id, dry_run=False)` — `src/pcae/core/agent.py:93895` |
| CLI | `pcae remote rollback execute JOB_ID` | `pcae rollback --per-id PER_ID [--dry-run]` |
| Mechanism | `git revert --no-edit <original_commit_sha>` | Direct file `write`/`unlink` restoring `before_content`/`before_hash` from a `PromotionExecutionRecord` (PER) |
| Target identity | `job_id` + `original_commit_sha`, resolved via `build_rollback_review`; requires clean tree, original commit reachable from `HEAD` | `per_id` (deriving `ecp_id`), gated on `PER.status in {"completed","partial"}` and `PER.rollback_payload_available=True` |
| Per-file integrity | N/A (whole-commit revert) | Already-hashed per-file `before_hash`/`after_hash` on the PER |
| Status | Unimplemented, blocked (RWMPC Wave-1 explicitly excludes it — `src/pcae/core/mutation_permission.py:31-32`) | Unimplemented, blocked, same reason |

**149D clarification reconfirmed:** AG5 is "a **separate, explicitly-invoked,
standalone command**... not an automatic in-band recovery triggered when
`build_promotion_execution`'s per-file loop hits a failure"
(`docs/PHASE_149D_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT_INDEPENDENT_VERIFICATION.md:92-122`).
Neither AG3 nor AG5 is an automatic compensating-recovery path; both are
explicit, human/agent-invoked commands. No third automatic recovery path
was found in this phase's inspection. Approval architecture below therefore
targets explicit rollback commands only (item 69/70 of the phase prompt);
no hypothetical automatic-recovery governance is designed.

AG3 and AG5 have different rollback-target identities (commit SHA vs.
PER/ECP identity) but the same operation *shape* — one specific, bounded
mutation reversal, invoked once, against one specific prior state. Both can
share **one** approval evidence architecture provided the binding record's
`target_reference` is a family-locked reference whose concrete family
differs per site (a commit/job reference for AG3, a PER/ECP reference for
AG5) rather than a fixed field shape. This mirrors how the existing Typed
Authority Model's `human_authorization` record already handles varying
target families via `target_reference` (§5.2 below).

## 3. Existing Approval-Shaped Legacy Flags — Independently Re-Checked

All of the following were independently re-confirmed as **not** trusted
approval evidence, matching prior phases' classification (RWMPC-001 §11/§21,
`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md:318-334,589-596`):

| Flag / function | File:line | Classification |
|---|---|---|
| `approve_rollback(root, job_id)` (mutates `job["rollback_approval_state"]`) | `src/pcae/core/agent.py:5146` | **No actor parameter at all.** Bare state-flag toggle, no identity/reason field. `pcae remote rollback approve JOB_ID` has no `--approved-by`/`--operator-id`/`--as-identity` flag (`src/pcae/cli.py:4142-4156`). |
| `change_approval_state` (`approve_file_changes`/`deny_file_changes`) | `src/pcae/core/agent.py:4465,4514` | Same shape: no actor parameter, mutable JSON dict key, freely overwritable. |
| `--promotion-authorized`, `--reviewed-by` | `src/pcae/cli.py:2896,2922` | Unauthenticated CLI self-declaration; no identity binding. |
| `--approve-keep`, `--approved-by`, `--reason` | `src/pcae/cli.py:8885-8887` | "Strongest legacy candidate" (named, structured flags) — still an unauthenticated self-declaration; nothing verifies the caller's claimed identity. |
| `--approved-by`/`--reason` (other sites: captured-output, backend-output-adoption, lifecycle approve-gate, task-package) | `src/pcae/cli.py:2395,8393,8544,8727,8780,8833,10406`; `src/pcae/lifecycle.py:468,475` | Same: bare `argparse` strings, no identity-provider cross-check anywhere in the codebase. |
| `task health/check pass` | N/A | Process-hygiene signal, not a decision about a specific rollback; explicitly excluded by RWMPC-REQ-023 (below). |

No new legacy flag was found beyond those already catalogued. None is
promoted to approval evidence by this architecture; none is deprecated
either (they remain whatever legacy/advisory function they already serve).

## 4. Existing Human-Governance Artifact Inventory

### 4.1 Canonical Human Governance Record (CHGR-001 v1.0, FROZEN)

A bundle of four schema-conformant artifacts
(`src/pcae/schema_resources/chgr/records/`), produced atomically by
`build_publication_record()` (`src/pcae/governance/publication/record.py:147-301`)
via the sole write path `PublicationCoordinator.execute()`
(`src/pcae/governance/publication/coordinator.py:115-211`), reached only
through `pcae governance-record publish <package-id> --operator-id <id>`
(`src/pcae/commands/governance_record.py:204-253`).

| Property | Value |
|---|---|
| Human-origin guarantee | **Self-declared only.** `operator_id`/`owner_identity` are bare CLI strings, checked only for non-emptiness. No OS/identity-provider check anywhere in the codebase. |
| Identity representation | `decision_maker_identity_evidence{evidence_kind, identifier, captured_at}`. Only `L0 (typed_confirmation_only)` is ever actually populated by production code; `L1 (os_authenticated_user)` is an accepted enum value with **no code that performs real OS authentication**. |
| Signature/authentication | None. SHA-256 **content-integrity** digests only (`governance_record_integrity`); explicitly "Digest validity never establishes authority." |
| Scope binding | `decision_subject` (free text) + `template_ref{template_id, version}`. **No structural operation-ID/target-reference field.** |
| Status lifecycle | 8 states (`draft`…`invalidated`), but **no transition command is implemented**; every real record is born `published`. |
| Freshness/expiry | None on the CHGR record itself. (Freshness *is* checked one layer below, on the `PublicationAuthorizationEvent` vs. `PublicationReadinessPackage` pairing, but that is authorization freshness, not record freshness.) |
| Revocation | `revocation_ref` field + `revoked` lifecycle state exist in schema; **no writer/command implemented**. |
| Consumption | The underlying `package_id` is single-use, replay-guarded (`PublicationCoordinator._check_replay`, `FileExistsError`-guarded atomic commit). The published CHGR record itself is durable/reusable-by-citation once it exists. |
| Own classification | Deliberately **not** pinned to one label. Umbrella term "Human Governance Act" spans authority election, governance approval, authorization decision, risk acceptance, revocation, etc. — the concrete semantics live in the bound **Decision Template**, not in a fixed CHGR type tag. What the schema concretely *evidences* is a **CONFIRMATION** act (`confirmation_statement`) of a selection from a closed option set defined by the template. |

Extensibility point directly relevant to this phase: `decision_template.schema.json`
already defines, per template, `eligible_authority` ("who may make this
decision... never a generic role lookup"), `expiry_rule`, `revocation_rules`,
`supersession_rules`, and a closed `options[]` set with mandatory
`consequence_text`/`non_effect_text`. **A new Decision Template can be
authored today without amending CHGR-001** — this is precisely the
extension mechanism CHGR-001 was designed to support (CHGR-001 §6,
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`).

### 4.2 Typed Authority Model — `human_authorization` (136 series, TAMC-001/TAMPC-001, FROZEN)

A structurally closer match for operation-bound, expiring, revocable,
single-use approval — but scoped to a **different subsystem** (CLTR
migration/"cutover" tooling, `src/pcae/cltr/authority/`) and **explicitly,
contractually walled off from CHGR**:

> CHGR-001 §19.1: "the Stage 3 Typed Authority Model family SHALL remain a
> wholly separate artifact family from CHGR, never composed, subclassed, or
> wrapped... Reusing or composing CHGR on Typed Authority Model schemas
> would either require stripping TAMC-001's explicit 'never establishes
> authority' disclaimer... or would create a confusing dependency."
> (`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md:612-644`)

> TAMC-REQ-024/025/036: "Never establish, activate, transfer, select, or
> revoke authority... Never infer authority, authorization, approval,
> certification... from record existence, validity, content, or location."

`human_authorization`'s schema shape (`src/pcae/schema_resources/cltr_cutover/records/human_authorization.schema.json`)
is nonetheless the best *structural template* in the repository for what
rollback approval needs: `request_reference`/`readiness_reference`/`target_reference`
(three required, family-locked references — strict single-operation
binding), `expires_at` (mandatory 24h freshness window), `state`
(`issued`/`used`/`revoked`/`expired`), `replay_binding` (one-time-use
token), `revocation_metadata` (conditionally required), `use_binding`
(conditionally required, points to the consuming record). Its own
`authority_disclosure.is_authoritative` field is a hard `const: false` —
even this family refuses to claim it *is* authority by existing.

**Conclusion:** reuse this family's *shape*, not the family itself — a new,
independent schema/contract is required for rollback, not a cutover-scoped
one, and not a composition with CHGR (both moves are independently
forbidden by frozen contract text).

### 4.3 Interactive Workflow Confirmation (IWC-001 v1.2, FROZEN)

Confirmation records (`ConfirmationRequest`/`ConfirmationResponse`,
`src/pcae/interactive_workflow/confirmation/models.py:54-112`) are frozen,
digest-bound to an exact Preview, single-use (replay-detected), and
immutable — but the contract is explicit and repeated that confirmation is
not approval:

> IWC-001 §1: "The workflow itself SHALL NEVER create authority. Authority
> derives only from the confirmed Human Governance Act that Publication
> (CHGR-001 §8) converts into a published CHGR."
>
> RWMPC-001 RWMPC-REQ-023: "**Confirmation is not approval.** Interactive
> Workflow Confirmation, task-finish health/check validation, and any other
> process-hygiene confirmation artifact SHALL NOT populate
> `approval_present`, regardless of which operation needs approval.
> Authority Evaluation / AESIC results SHALL NOT be treated as permission
> or approval evidence — AESIC remains disclosure-only."

IWC is therefore the **transport** a human uses to reach a decision inside
a session (`pcae decision-session confirm`), never itself the evidence.
Actor identity in IWC is likewise entirely self-declared
(`Session.owner_identity = args.owner_id`, exact-string compared, never
authenticated).

### 4.4 Publication Execution Ownership (PEC-001, FROZEN)

`PublicationAuthorizationEvent` (`src/pcae/governance/publication/models.py:36-52`)
is the audit record of "an operator invoked the publish command now" —
`operator_id`, `package_id`, `invoked_at`. It is deliberately narrow:

> PEC-REQ-018/021: "The Publication Coordinator SHALL be a component
> external to `src/pcae/interactive_workflow/**`... external to
> `src/pcae/cltr/**`... sole responsibility SHALL be... to perform CHGR-001
> §8's atomic write." (`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md:215-240`)

It adopts, explicitly, "Model 2 (CLI-operator invocation)" as *sufficient
for v1.0*, naming a stronger "Model 3 (a separate, typed, CHGR-scoped
authorization artifact, independently verifiable and independently
revocable)" as a permitted future hardening extension, not a v1.0
requirement (PEC-REQ-034/046). This repository's own already-frozen
contract has therefore already anticipated exactly the kind of artifact
this phase is asked to design — for publication, not yet for rollback.

### 4.5 Authority Evaluation / AESIC (AEM-001/AESIC-001, FROZEN)

Disclosure-only by explicit, repeated contract text:

> AEM-REQ-003: "evaluate-and-disclose only: it MAY NOT block, gate,
> suppress, delay, or otherwise condition Confirmation, Readiness
> construction, Authorization, or Publication on its outcome."

AESIC populates only CHGR's `authority_basis_claimed` **citation** field
(itself explicitly named a *claim*, never a verified grant). It never
touches `approval_present` and RWMPC-REQ-023 explicitly forecloses using it
as rollback approval evidence. **AESIC is not a candidate.**

## 5. Approval Evidence Candidate Matrix

| Candidate | Human-authenticated? | Operation-bound? | Explicit approval semantics? | Reusable for rollback (as-is)? |
|---|---|---|---|---|
| `--approve-keep`/`--approved-by`/`--reason` and other legacy flags | No — self-declared string | No | No — bare flag | No |
| `approve_rollback` / `change_approval_state` | No — no actor field at all | Weak (job_id string only, no target/state binding) | No — bare toggle | No |
| Interactive Workflow Confirmation | No — self-declared, exact-string compared | Yes (preview-digest bound) but contract forbids approval reuse | Explicitly **not** approval (RWMPC-REQ-023) | No |
| Authority Evaluation / AESIC | N/A | N/A | Explicitly disclosure-only | No |
| CHGR (`human_governance_record`), unamended, generic template | Self-declared (same ceiling as everything else) | No structural operation-reference field; `decision_subject` is free text | Yes, if bound to an approval-shaped Decision Template — CHGR is decision-content-agnostic | Partial — good for identity/confirmation/publication/integrity substrate, insufficient alone for structural operation binding, freshness, revocation, single-use |
| Typed Authority Model `human_authorization` | Self-declared (`principal`, "does not verify... against any identity provider") | Yes — strict, family-locked triad | Explicitly **not** authoritative by its own schema (`is_authoritative: const false`) and contractually walled off from CHGR/rollback use | No — wrong subsystem, contractually forbidden to compose with CHGR, scoped to "cutover" |
| **New, rollback-scoped companion record, anchored to a CHGR publication** | Self-declared (repository-wide ceiling; disclosed honestly, not hidden) | Yes — structural, by design | Yes — dedicated Decision Template + dedicated binding schema | **Yes — this phase's selected model** |

## 6. Selected Architecture

```
SELECTED ROLLBACK APPROVAL EVIDENCE ARCHITECTURE:
  Canonical Human Governance Record trust substrate (CHGR-001, unamended)
  + a new "Rollback Approval" Decision Template (CHGR-001 §6 extension point — no CHGR-001 amendment required)
  + a new, dedicated Rollback Approval Binding record (new schema/contract, structurally modeled on the
    Typed Authority Model's human_authorization shape, but independent of that family per the existing wall)
  + operation-bound validation performed by a future, dedicated evidence validator
  + a derived, non-caller-settable approval_present boolean
```

This is Model B ("extend the canonical human-governance model with a
rollback approval type") from the required comparison, and matches the
phase prompt's own item 27/75 preferred shape almost exactly: "canonical
human-governance record substrate + rollback-specific approval record type
+ operation-bound approval validation + derived approval_present."

### 6.1 Why not the other models

- **Model A (reuse CHGR unchanged):** Rejected as sufficient on its own.
  CHGR gives real, valuable properties (human-declared-identity capture
  through a rigorous Confirmation ritual, immutability, replay-guarded
  publication, content-integrity digests) but has **no structural
  operation-reference field** — `decision_subject` is free text, not a
  family-locked reference. Relying on free text for "this approval applies
  to exactly this rollback attempt, this target, this repo state" would be
  a stringly-typed convention, not an enforceable binding — precisely the
  kind of weak binding the phase prompt (items 16, 32-34) requires be
  avoided.
- **Model C (wholly new, unanchored artifact):** Rejected as the
  *primary* design, because it would duplicate governance infrastructure
  CHGR already solved (identity capture, confirmation ritual, publication
  atomicity, replay guard, content integrity) — a needless parallel trust
  system. Adopted instead as a *narrow addition*: the new binding record
  supplies only the structural fields CHGR lacks (operation reference,
  freshness, revocation, single-use), while the identity/confirmation/
  publication/integrity properties are inherited by anchoring the binding
  record to a specific CHGR `record_id`+`record_digest`.
- **Model D (ephemeral interactive approval only):** Rejected. IWC's own
  contract already forbids this (RWMPC-REQ-023); no durable, replay-safe,
  auditable evidence would result.
- **Reusing Typed Authority Model's `human_authorization` directly:**
  Rejected — contractually forbidden (CHGR-001 §19.1, TAMC-REQ-024/025/036)
  and scoped to a different subsystem (migration "cutover" attempts, not
  repository rollback). Its *shape* is reused as a design template; the
  family itself is not.

### 6.2 Scoring against required criteria

| Criterion | Assessment |
|---|---|
| Trust provenance | Inherits CHGR's existing, already-frozen Confirmation → Publication pipeline (best available in repo) |
| Semantic correctness | New Decision Template makes the recorded Human Governance Act explicitly an approval-type decision, not a relabeled confirmation |
| Operation binding | New, structural, family-locked reference fields (not present in CHGR alone) |
| Reuse of existing governance | Maximizes reuse: zero CHGR-001 amendment; one new Decision Template (already-supported mechanism); one new, narrow binding contract |
| Auditability | Inherits CHGR's immutability + content-integrity digesting; binding record itself schema-validated and referenced by ID+digest |
| Revocation/supersession support | New binding record borrows the `human_authorization` shape's proven `state`/`revocation_metadata` pattern (CHGR's own revocation path is unimplemented) |
| Implementation boundedness | Two new artifacts (template + binding schema), no changes to POL-004, RWMPC-001, PBPA-001, PBPC-001, Runtime, or rollback code |
| Future multi-user compatibility | `eligible_authority`/`principal`-shaped fields kept as descriptive text today (matching repo's actual trust ceiling), not hard-wired to a single username string — a future identity-provider integration can populate the same field more strongly without a redesign |

## 7. Trust Model

### 7.1 Human identity (items 11, 38-41)

The repository has **no OS-level, cryptographic, or identity-provider
authentication anywhere in its human-governance stack** — this is true of
CHGR, IWC, Publication Execution, and the Typed Authority Model alike, not
a rollback-specific gap. `os_authenticated_user` (CHGR L1) is a schema
enum value with no supporting implementation; `human_authorization`'s
`principal` field is explicitly documented as unverified against any
identity provider. The most honest statement of the repository's actual
trust model:

> **The repository currently trusts the local CLI operator who can invoke
> a governed command against this checkout, identified only by a
> self-declared string. No stronger assurance exists anywhere in this
> codebase today.**

The rollback approval architecture **does not invent a stronger
guarantee than this.** It does not attempt OS-user binding, does not
attempt cryptographic signing (CHGR L2-L5 remain unimplemented
extension points, consistent with repository convention), and does not
fabricate identity assurance the repository cannot currently back. The
binding record's `approver_identity` field is defined at the same
assurance ceiling as CHGR's own `decision_maker_identity_evidence` — an
explicit, honest limitation, not a hidden one.

### 7.2 Approval authority vs. approval event (item 12, 55-57)

Two distinct facts, both required:

1. **Actor is authorized to approve rollback** — expressed via the
   Decision Template's `eligible_authority` field (already a supported,
   required field on every CHGR Decision Template: "who may make this
   decision, named or described specifically... never a generic role
   lookup"). No separate authority *registry* exists in the repository
   today, and none is invented here: for a single-operator local trust
   model, `eligible_authority` is expressed as descriptive text (e.g. "the
   human operator of this governed checkout"), matching §7.1's honest
   ceiling. This is flagged as a STRATEGIC_GAP (§11) for future
   multi-user hardening, not fabricated now.
2. **Actor approved this specific rollback** — the recorded Human
   Governance Act itself (an `APPROVE_ROLLBACK`/`DENY_ROLLBACK`-shaped
   option selection inside the new Decision Template), evidenced by a
   published CHGR record.

A trusted approval event from an actor who does not match
`eligible_authority` is insufficient — both facts are required, matching
item 12 exactly.

### 7.3 Privilege separation (item 57) and self-approval / agent-forgery threats (items 22, 56)

The repository has **no technical privilege separation between an agent
process and a human operator** — both reach the same CLI. This is an
existing, already-accepted limitation of every human-governance mechanism
in this codebase (Publication Execution's own contract, PEC-REQ-034/046,
explicitly names this as "Model 2," accepted as sufficient for v1.0). This
architecture inherits, rather than worsens, that limitation: it structurally
prevents an agent from **fabricating** the *shape* of approval evidence (a
raw JSON blob with `approved: true` is never accepted — only a schema-
validated record anchored to an actually-published CHGR record, produced
through the full Confirmation → Publication ritual, is), but it cannot
prevent an agent from **operating the CLI as if it were the human**, because
no part of this repository can prevent that today. This gap is recorded
honestly as a STRATEGIC_GAP finding (§11), not concealed and not solved by
this architecture.

## 8. Approval Event Model

New Decision Template, `rollback-approval` (name illustrative; exact
`template_id` frozen in a future contract phase), authored using CHGR-001's
existing, unamended `decision_template.schema.json` shape:

- `options`: a closed set including at minimum `approve_rollback` and
  `deny_rollback` (each with mandatory `consequence_text`/`non_effect_text`
  per existing schema requirements — e.g. `approve_rollback`'s
  `non_effect_text` states plainly that approval alone does not execute
  anything; execution remains gated by the Permission Broker and RWMPC
  freshness).
- `eligible_authority`: descriptive text per §7.2.
- `expiry_rule`: references the binding record's `expires_at` (§9) as the
  operative mechanism — the template's own field documents the *rule*,
  the binding record enforces it.
- `revocation_rules`: references the binding record's `state`/
  `revocation_metadata` (§10) as the operative mechanism.
- `subject_binding_rule`: "one instance per rollback attempt; `decision_subject`
  SHALL name the concrete rollback operation reference (job_id or PER id),
  never a generic 'rollback approval'."

A human governance act against this template, confirmed and published
through the existing, unamended IWC → CHGR pipeline, produces one
`human_governance_record` (+ its 3 companion artifacts) exactly as
Publication Execution already does for every other decision class. No new
capability is added to CHGR, IWC, or Publication Execution — this is
consumption of an existing extension point.

## 9. Rollback Operation Binding

The new **Rollback Approval Binding** record (new schema/contract; not
built in this phase) references the published CHGR record and adds the
structural fields CHGR itself does not carry:

Conceptual fields (not frozen — a future contract phase freezes the exact
schema; listed here to state the architecture, per item 28's explicit
allowance):

- `evidence_id`
- `governance_record_reference` — family-locked reference to the specific
  `human_governance_record.record_id` + `record_digest` that is this
  evidence's human-origin proof (anchors §7-§8 above)
- `rollback_site` — `AG3` or `AG5` (the two are structurally similar but
  not identical; keeping this explicit avoids conflating their differing
  target-identity shapes)
- `rollback_operation_reference` — for AG3: `{job_id, original_commit_sha}`;
  for AG5: `{per_id, ecp_id}` — family-locked per site, mirroring how
  `human_authorization.target_reference` is family-locked per target type
- `task_id` — bound if the rollback is task-scoped (per item 45; derived
  from the active governed task at approval time, not inferred later)
- `repository_state_binding` — `{head_commit_sha, branch}` captured at
  approval time (§12)
- `created_at` / `expires_at` — mandatory freshness window, mirroring
  `human_authorization`'s mandatory `expires_at` (no arbitrary invented
  duration; a future contract phase derives the window from existing
  governance conventions rather than this document picking one)
- `state` — `issued` / `used` / `revoked` / `expired`, mirroring
  `human_authorization`'s proven enum
- `revocation_metadata` — conditionally required iff `state=revoked`
- `use_binding` — conditionally required iff `state=used`; points to the
  consuming rollback attempt's own outcome record
- `replay_binding` — one-time-use token, preventing replay per §14

### 9.1 Target binding (item 16)

Approval for rollback target A must never permit rollback target B. The
binding record's `rollback_operation_reference` is a required, family-locked
field — a validator (§13) rejects evidence whose reference does not
exactly match the live rollback attempt's own `job_id`/`original_commit_sha`
(AG3) or `per_id`/`ecp_id` (AG5). No fuzzy or partial matching, mirroring
IWC's own exact-digest-match discipline.

### 9.2 Repository-state binding (items 17, 48-49)

`repository_state_binding` is captured **at approval time** as part of the
evidence (this is distinct from RWMPC's own operation-freshness check,
which re-observes live `HEAD` at execution time — item 49's required
separation). If current `HEAD`/branch at the moment a rollback is actually
attempted no longer matches the evidence's `repository_state_binding`, the
evidence is stale (§10) and validation fails closed — but the *live*
freshness re-check remains RWMPC's own existing responsibility, not
duplicated here. This keeps "approval evidence valid" and "broker decision
still fresh" as the two distinct concerns item 49 requires.

## 10. Freshness, Revocation, Single-Use (items 18-21, 50-52)

- **Freshness:** `expires_at`, mandatory, mirroring the one existing
  precedent in this repository for exactly this kind of evidence
  (`human_authorization.expires_at`). No arbitrary wall-clock rule is
  invented beyond following that existing precedent's *shape*; the exact
  duration is a normative decision for the future contract-freeze phase.
  Evidence additionally becomes stale if `repository_state_binding` no
  longer matches live state at evaluation time, or if a
  `predecessor_record_id`/superseding evidence record exists.
- **Revocation:** `state=revoked` + `revocation_metadata`, again mirroring
  `human_authorization`'s already-proven pattern (a pattern CHGR's own
  `revoked` lifecycle state has never had a writer for). A revoked record
  must never resolve to `approval_present=True` — enforced by the
  validator (§13), not by trusting the caller.
- **Single-use:** the phase prompt's "approval for one rollback attempt ≠
  reusable approval" (item 20) is satisfied by two layers: (a) the
  underlying CHGR publication is already package-id replay-guarded, so the
  same *governance act* cannot be re-published; (b) the binding record's
  own `state: issued → used` transition plus `replay_binding` token
  prevents the same evidence being presented twice to the validator, even
  if the rollback attempt itself is retried mechanically after a failure.
- **Failed rollback after `ALLOW` (item 52):** if the mechanical rollback
  execution fails (not the approval, the `git revert`/file-restore step
  itself) with the exact same operation identity and unchanged repository
  state, the evidence's `state` need not have transitioned to `used` if no
  actual mutation occurred — a future implementation phase defines the
  exact transition point (e.g., transition to `used` only on RWMPC-confirmed
  successful mutation, not on broker `ALLOW` alone) so that a purely
  mechanical failure does not burn single-use evidence for no reason. This
  phase records the requirement, not the exact state-machine wiring.

## 11. Threat Model (item 71)

| # | Threat | Mitigation in this architecture |
|---|---|---|
| 1 | CLI self-declaration (`--approved`-shaped flag) | No CLI flag can set `approval_present`; only a resolved, validated evidence record can (§13) |
| 2 | Agent-generated fake approval JSON | Evidence must be a schema-validated record anchored to an actually-published CHGR record produced through the real Confirmation→Publication pipeline; a hand-written JSON blob fails schema/reference validation |
| 3 | Forged approver identity | Not solved beyond the repository's existing ceiling (§7.1/§7.3) — disclosed as a STRATEGIC_GAP, not hidden |
| 4 | Stale approval replay | `expires_at` + `repository_state_binding` staleness check (§10) |
| 5 | Approval for wrong rollback target | Family-locked `rollback_operation_reference`, exact match required (§9.1) |
| 6 | Approval reused after repo state changes | `repository_state_binding` staleness (§9.2) plus RWMPC's own independent live freshness re-check |
| 7 | Revoked approval use | `state=revoked` fails validation (§10) |
| 8 | Confirmation treated as approval | Structurally impossible — IWC confirmation is the *transport* into a session; only a *published, approval-templated* CHGR record can back evidence (§4.3, RWMPC-REQ-023 upheld unchanged) |
| 9 | AESIC treated as approval | AESIC is never consulted by the validator; disclosure-only boundary upheld unchanged (§4.5) |
| 10 | Approval artifact tampering | Inherits CHGR's content-integrity digesting (`governance_record_integrity`) plus the binding record's own digest |
| 11 | Broad task-level approval reused across operations | Rejected by design — `subject_binding_rule` requires one instance per rollback attempt (§8); `rollback_operation_reference` is operation-specific, not task-generic |
| 12 | Approval obtained by unauthorized principal | `eligible_authority` check (§7.2) — recorded as a required, currently-descriptive-text check; STRATEGIC_GAP that no registry enforces it mechanically today |
| 13 | Evidence lookup choosing wrong record | No "latest approval" lookup (§12) — explicit reference only |
| 14 | Approval created after broker evaluation, injected into the same stale decision | Broker requests are always freshly constructed per attempt (existing Permission Broker convention); a new approval cannot retroactively rewrite a prior `HUMAN_REVIEW` decision — the next attempt re-evaluates from scratch (§14) |

## 12. Evidence Lookup — No "Latest Approval" (items 32-33)

The rollback command supplies an **explicit evidence reference** (e.g. an
`--approval-evidence-id` naming the binding record, or an equivalent
canonical operation-linkage the future implementation defines) rather than
the validator scanning for "the most recent approval." This directly
satisfies item 33: "latest approval record must not automatically apply
unless it is explicitly operation-bound" — here it is always explicitly
operation-bound by construction (§9.1), so there is no ambiguous "latest"
concept to begin with.

## 13. Approval Evidence Validation Ownership (item 31) and Derived Boolean (items 30, 78-80)

A future, dedicated **rollback approval evidence validator**, owned by core
governance infrastructure (not implemented in this phase), is the sole
component permitted to derive `approval_present`:

```
resolve_rollback_approval_evidence(operation_context) -> ValidApprovalEvidence | None
```

Frozen rule:

```
approval_present =
    validated_evidence is not None
```

No direct CLI boolean controls it (item 78). Validation fails closed on any
of: missing, malformed, untrusted (not anchored to a real published CHGR
record), wrong scope, wrong target, stale, revoked, or superseded evidence
— in every one of those cases `approval_present=False`, and POL-004
resolves to `HUMAN_REVIEW` exactly as it does today for a missing flag
(item 79). If the evidence-resolution system itself errors, it fails
closed — no approval (item 80). The caller/agent constructing the rollback
request never performs this trust judgment itself (item 31) — it only
supplies the evidence reference; the validator alone decides.

## 14. Flow (item 34) and HUMAN_REVIEW Meaning (item 35-36)

```
rollback intent constructed
        |
operation identity determined (job_id+commit for AG3, per_id+ecp_id for AG5)
        |
explicit approval-evidence reference supplied (no implicit "latest" lookup)
        |
evidence resolved + validated (authenticity/authority/scope/freshness/revocation)
        |
approval_present = True/False derived
        |
PermissionBrokerRequest constructed fresh
        |
POL-004 / broker evaluation (unchanged)
```

`HUMAN_REVIEW` continues to mean exactly what it means today: *the current
request lacks sufficient approval evidence* — never an instruction for the
broker itself to go collect approval (POL-004's own comment already states
this: "the human's approval is the resolution, not an override"). The
Permission Broker remains a pure decision boundary; no interactive behavior
is added to it (item 82). After a human creates valid evidence, a **fresh**
attempt constructs a **new** request — there is no in-place mutation of a
prior `HUMAN_REVIEW` decision (item 36, item 14 of the threat model).

Even with valid evidence, `approval_present=True` does not force `ALLOW`
(item 53) — other applicable policies still run; evidence supplies exactly
one request fact and never selects which policies apply (item 54).

## 15. Approval Creation Boundary (item 37)

The architectural owner of rollback-approval creation is the **existing
Interactive Workflow + Publication pipeline**, consuming the new Decision
Template (§8) — not a new, parallel command family. A future implementation
phase may add a thin, dedicated CLI convenience wrapper (e.g. a
`pcae rollback approve` alias), but per item 66 it "must create canonical
evidence rather than simply toggle a boolean" — i.e., any such command is
required to route through the real Confirmation→Publication ritual plus
the new binding-record creation step, never a shortcut. No CLI is
implemented in this phase.

## 16. Reviewability and Specificity (items 67-68)

Because rollback approval flows through the existing Preview/Confirmation
machinery, the human necessarily sees the same class of disclosed content
IWC already requires before any Confirmation is possible (exact preview
content, consequence/non-effect text per option) — for the rollback
template this concretely means the disclosed rollback target, affected
scope, and current state must be renderable into the Decision Template's
`consequence_text`. No blanket "approve all rollbacks for task" option
exists — the template's closed option set and the binding record's
mandatory per-operation reference structurally forbid it (item 68).

## 17. Relationship to Frozen Contracts

- **RWMPC-001 (v1.0, unamended):** RWMPC-REQ-017 already states, generically,
  that "`approval_present` must reflect a real evidence source (Section 11)"
  — it names no specific artifact. This architecture satisfies that
  requirement without requiring any RWMPC-001 wording change (item 88). No
  RWMPC amendment is recommended.
- **PBPA-001 (v1.0, unamended):** POL-004's applicability and resolution
  logic are untouched; this architecture supplies evidence, never modifies
  policy (item 83, 84).
- **PBPC-001 (v1.2, unamended):** push-specific; unrelated (item 63).
- **CHGR-001 (v1.0, unamended):** consumed via its existing Decision
  Template extension point only; no schema or contract text changes.
- **IWC-001 (v1.2, unamended):** consumed as transport only, unchanged.
- **PEC-001 (unamended):** consumed as the publication mechanism only,
  unchanged; this phase does not adopt PEC-001's named "Model 3" hardening
  option, but records it as a related, not-yet-pursued option (§18).
- **TAMC-001/TAMPC-001 (unamended):** explicitly not reused/composed, per
  their own frozen wall with CHGR (§4.2). No amendment, no violation.
- **AESIC-001/AEM-001 (unamended):** disclosure-only boundary upheld
  unchanged; not consulted by the new validator.

## 18. Findings

- **STRATEGIC_GAP** — No stronger-than-self-declared human identity
  substrate exists anywhere in this repository (CHGR, IWC, Publication
  Execution, and Typed Authority Model all share this ceiling). Rollback
  approval inherits, and does not attempt to paper over, this ceiling.
  Already implicitly accepted by PEC-001's own "Model 2 sufficient for
  v1.0" judgment call; this phase reconfirms it applies identically to
  rollback.
- **STRATEGIC_GAP** — No technical privilege separation between an agent
  process and a human operator exists in this repository; an agent that
  can reach the CLI can operate any human-facing command, including a
  future rollback-approval command. This architecture prevents *evidence
  fabrication* (schema/anchor validation) but cannot prevent *operator
  impersonation* at the OS level. Not solved in this phase; not solvable
  without infrastructure this repository does not have today.
- **OBSERVATION** — No existing "approval authority registry" (who is
  eligible to approve rollback) exists. `eligible_authority` is expressed
  as descriptive text on the Decision Template, matching the single-
  operator local trust model already implicit elsewhere in this
  repository. A future multi-user hardening phase may need a real
  registry; not required for the current threat model.
- **NON-BLOCKING** — CHGR's own `revoked` lifecycle state and
  `governance_record_lifecycle_event` family have no production writer.
  The new binding record's revocation mechanism (§10) is independent of
  that gap (it does not depend on CHGR's own revocation machinery), so
  this does not block the selected architecture, but is worth closing in
  a future CHGR-adjacent phase.
- **DEFERRED** — Exact binding-record schema field names/types, the exact
  Decision Template `template_id`/options wording, and the exact
  freshness-window duration are intentionally left to the next,
  narrower contract-freeze phase (item 60 forbids freezing a schema in an
  architecture phase).
- **OBSERVATION** — RWMPC-001, PBPA-001, PBPC-001 all require no amendment
  to consume this architecture (§17); no clarification phase is needed for
  any of the three at this time.

No BLOCKING finding was raised against the architecture's own
selectability — a concrete, single architecture was reached (below).
The two STRATEGIC_GAP findings are pre-existing, repository-wide trust-
ceiling facts inherited from already-frozen contracts, not new blockers
this phase introduces or could resolve.

## 19. Architecture Verdict

```
ROLLBACK APPROVAL EVIDENCE ARCHITECTURE DEFINED
```

## 20. Rollback Readiness

```
ROLLBACK PERMISSION IMPLEMENTATION:
NOT YET READY
```

Architecture definition alone is not implementation readiness. No binding
record schema exists yet, no Decision Template is authored yet, no
validator exists yet, and no CLI surface exists yet — this phase defined
the shape and rationale, not the artifacts themselves.

## 21. Implementation Dependency Map

```
Rollback Approval Binding Contract/Schema Freeze (recommended: 149I)
        |
Independent verification of 149I
        |
Rollback Approval Evidence implementation (Decision Template authoring +
binding-record read/write path + validator)
        |
Independent verification
        |
Rollback RWMPC implementation plan (AG3/AG5-specific PermissionBrokerRequest wiring)
        |
AG3/AG5 implementation
        |
Independent verification
```

No phase beyond 149H is pre-authorized by this document.

## 22. Recommended Next Phase

```
149I — Rollback Approval Evidence Contract Freeze
```

Scope: freeze the binding-record schema (§9), the Decision Template
(§8), and the exact validator interface (§13) as normative contract text —
no CHGR-001, RWMPC-001, PBPA-001, or PBPC-001 amendment, no rollback code,
no Permission Broker change. A dedicated CHGR-extension or human-identity-
trust phase is not required first: this phase found the existing CHGR
Decision Template mechanism and the existing repository-wide self-declared-
identity ceiling both sufficient to proceed to a contract freeze, with the
two STRATEGIC_GAP findings carried forward as disclosed limitations rather
than blockers.

## 23. Governance Boundary Confirmations

- RWMPC-001 v1.0 remains unchanged.
- PBPC-001 v1.2 remains unchanged.
- PBPA-001 v1.0 remains unchanged.
- No production source (`src/pcae/**`) was modified by Phase 149H.
- No rollback Permission Broker consumer was implemented.
- AG3 and AG5 remain unimplemented.
- No `approval_present=True` production value was introduced.
- No approval was fabricated.
- No self-declared CLI flag was treated as trusted approval.
- Interactive Workflow Confirmation remains distinct from approval.
- Authority Evaluation / AESIC remains disclosure-only.
- No POL-001..012 meaning was changed. No POL-013+ was added.
- No Runtime Enforcement behavior was changed.
- No Prompt Generation or Prompt Dispatch capability was implemented.
- No agent invocation capability was implemented.
- TK1, TK2, and TK3 remain explicitly deferred.
- Runtime remains Observed, maximum capability remains observe, execution
  availability remains unavailable.
