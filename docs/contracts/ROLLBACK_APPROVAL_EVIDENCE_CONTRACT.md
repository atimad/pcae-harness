# Rollback Approval Evidence Contract

## Contract identity and status

**Contract:** RAE-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149I — Rollback Approval Evidence Contract Freeze
**Depends on:** CHGR-001 v1.0 (`CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`,
unamended), IWC-001 v1.2 (`INTERACTIVE_WORKFLOW_CONTRACT.md`, unamended),
PEC-001 (`PUBLICATION_EXECUTION_CONTRACT.md`, unamended), RWMPC-001 v1.0
(`REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`, unamended),
PBPA-001 v1.0 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
unamended), PBPC-001 v1.2 (`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`,
unamended)
**Structural precedent (non-normative):** TAMC-001 / TAMPC-001
`human_authorization` record shape — reused for structural inspiration
only, per CHGR-001 §19.1's wall (§5 below); never composed, subclassed,
or wrapped.
**Architecture basis:** `docs/PHASE_149H_ROLLBACK_APPROVAL_EVIDENCE_ARCHITECTURE.md`.
Where this contract's independent reconstruction diverges from 149H's
prose, this contract is normative; every such divergence is recorded
explicitly at the point it occurs.

RAE-001 v1.0 is the sole normative contract answering: what exact
canonical evidence proves that a trusted human authority approved one
specific rollback operation, how that evidence is authenticated,
provenanced, bound, and kept fresh, and under what exact conditions
trusted PCAE integration code may derive `approval_present=True` from
it. It is additive to CHGR-001, IWC-001, PEC-001, RWMPC-001, PBPA-001,
and PBPC-001 — it amends none of them, and none of them require
amendment to be consumed by this contract (§17).

This is contract text only. It defines a decision template shape and a
new, dedicated binding-record field table as normative prose; it does
not author a JSON Schema file, does not implement a validator, does not
wire AG3/AG5 to the Permission Broker, and does not set
`approval_present=True` anywhere in production. It grants no runtime,
lifecycle, or execution capability.

Runtime posture, unaffected by this contract:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## 0. Normative Language

`SHALL`, `SHALL NOT`, `MAY`, and `MUST NOT` are used per RFC 2119
throughout this contract, matching CHGR-001 §0 and RWMPC-001's own
convention.

## 1. Purpose

`AG3` (`execute_rollback`, `src/pcae/core/agent.py`) and `AG5`
(`build_rollback_execution`, `src/pcae/core/agent.py`) are the
repository's two `EXECUTION_CLASS_ROLLBACK` mutation sites. RWMPC-001
RWMPC-REQ-027 recorded, as a BLOCKING finding, that a truthful
`PermissionBrokerRequest` for either site necessarily carries
`approval_present=False` today, because **no trusted, authenticated,
provenance-bound approval evidence source exists in this repository**.
`POL-004` (`MissingHumanApprovalRule`) is not defective, the Permission
Broker is not defective, and RWMPC-001's rollback classification is not
defective — the missing capability is a source of evidence from which
`approval_present=True` can be truthfully derived. This contract
supplies that source, as contract text, so a future, separately
governed implementation phase can build it without semantic
reinterpretation.

## 2. Scope

In scope: the evidence model, trust model, terminology, artifact
shapes, operation-binding rules, freshness/revocation/replay rules, and
`approval_present` derivation rule for rollback approval at AG3 and AG5.

Out of scope (§21, Non-Goals): rollback production implementation, AG3/AG5
Permission Broker wiring, Permission Broker policy changes, PBPA/PBPC
amendment, IWC semantic change, AESIC semantic change, TAM authority-family
composition, Prompt Generation/Dispatch, runtime activation, and TK1-TK3
coverage.

## 3. Definitions

The following terms are normative for this contract and SHALL be used
with exactly the meaning given here. Terms already defined by CHGR-001
§2 (Human Governance Act, Canonical Human Governance Record, Decision
Template, Decision Subject, Human Decision, Confirmation, Publication,
Supersession, Revocation, Suspension, Assurance Level, Interactive
Decision Session) are adopted unchanged and are not redefined below.

- **Rollback Operation** — one specific, bounded mutation-reversal
  attempt at AG3 or AG5, identified by the operation-identity fields
  §10 defines for that site. Two invocations of the same CLI command
  with different targets are two different Rollback Operations.
- **Approver** — the eligible human authority named or described by the
  `rollback-approval` Decision Template's `eligible_authority` field
  (§7), who performs the Human Decision this contract concerns.
- **Approval Authority** — the fact that a given Approver is eligible,
  under the governing Decision Template, to approve rollback; distinct
  from, and required in addition to, the fact that the Approver actually
  approved a specific Rollback Operation (§7.2).
- **Rollback Approval Decision** — a published `human_governance_record`
  (+ its three CHGR-001 companion artifacts), produced through the
  unamended CHGR-001/IWC-001/PEC-001 pipeline against the `rollback-
  approval` Decision Template (§7), whose `selected_option_id` is
  `approve_rollback` or `deny_rollback`. This is the Human Decision
  layer.
- **Rollback Approval Binding** — the new, dedicated record type this
  contract defines (§8), that references exactly one Rollback Approval
  Decision and structurally binds it to exactly one Rollback Operation.
  This is the operation-binding layer CHGR alone does not supply.
- **Rollback Approval Evidence** — the conjunction of one valid Rollback
  Approval Decision and one valid Rollback Approval Binding that
  together satisfy §13's derivation rule for a specific Rollback
  Operation. "Evidence" always means this pair, never either artifact
  alone.
- **Evidence Validator** — the future, dedicated component (§12) that is
  the sole authority permitted to resolve Rollback Approval Evidence and
  derive `approval_present`.
- **Evidence Consumer** — the future AG3/AG5 request-construction code
  path that supplies an explicit evidence reference to the Evidence
  Validator and receives back a derived `approval_present` value; it
  never performs trust evaluation itself (§12).

## 4. Semantic Layers

This contract preserves, as a load-bearing distinction, that the
following are never the same fact:

```
human authority (Approval Authority, §3)
        != human approval decision (Rollback Approval Decision, §3)
                != approval evidence (Rollback Approval Evidence, §3)
                        != Permission Broker permission (approval_present, POL-004, ALLOW/DENY/HUMAN_REVIEW)
                                != execution capability (Runtime state: Observed / observe / unavailable)
                                        != rollback execution (AG3/AG5, unimplemented)
```

Satisfying an earlier layer never implies satisfying a later one. A
valid Approver with Approval Authority who has not confirmed a decision
supplies no evidence (§3→§3 gap). Valid Rollback Approval Evidence
supplies exactly one request fact (`approval_present=True`) and does not
itself force an `ALLOW` decision, since other applicable policies still
run (§4→ Permission Broker gap, restated at §16). A Permission Broker
`ALLOW` does not itself execute anything, since AG3/AG5 remain
unimplemented (final gap, restated at §23).

## 5. CHGR Trust Substrate and the CHGR/TAM Wall

**RAE-REQ-001.** This contract's trust substrate is CHGR-001, unamended,
consumed only through its existing Decision Template extension point
(CHGR-001 §6). No CHGR-001 schema, requirement, or lifecycle rule is
modified, narrowed, or reinterpreted by this contract.

**RAE-REQ-002.** CHGR-001 is independently confirmed, from direct
re-reading of CHGR-001 §1-§13, to actually guarantee: human authorship
of substantive selections (§4, INV-1/INV-2); no inferred consent
(INV-3); a bounded, closed-option interactive workflow (§5); a distinct
Confirmation act separate from any earlier step (§7); atomic Publication
assigning stable canonical identity (§8-§9); provenance sufficient to
reconstruct what was presented, selected, and confirmed, including the
exact preview content and a content-integrity digest (§10); and
immutability of a published record's substantive fields, correctable
only through supersession (§13.3). This contract claims no CHGR
guarantee beyond this list. In particular, CHGR-001 does **not**
guarantee: that the decision-maker held authority to decide (§11, INV-8);
cryptographic signing (§12 — assurance levels L2-L5 are open extension
points, not implemented); or any structural operation-reference field on
`human_governance_record` itself (`decision_subject` is free text —
149H §6.1, independently re-confirmed by direct reading of
`human_governance_record.schema.json`, which has no `record_family`-typed
operation-reference field). This last gap is exactly what the Rollback
Approval Binding record (§8) exists to close.

**RAE-REQ-003.** Per CHGR-001 §19.1 and TAMC-REQ-024/TAMC-REQ-025/
TAMC-REQ-036 (independently re-read from `TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
lines 209-284), the Stage 3 Typed Authority Model family and CHGR SHALL
NOT be composed, subclassed, or wrapped as one authority family. The
Rollback Approval Binding record defined by this contract SHALL NOT be a
Typed Authority Model `human_authorization` artifact, SHALL NOT be
stored under `src/pcae/schema_resources/cltr_cutover/**`, and SHALL NOT
declare `record_type: human_authorization` or any TAM `record_family`
value. It MAY reuse structural field concepts (a family-locked operation
reference, an `expires_at` freshness field, a `state` enum, conditional
`revocation_metadata`/`use_binding`, a `replay_binding` token) where
compatible, per §8 below, but SHALL have independent, rollback-specific
semantics, its own record type name, and its own schema identity.

**RAE-REQ-004.** This contract's own relationship to the Typed Authority
Model is exactly: structural inspiration for the Rollback Approval
Binding record's field shape (RAE-REQ-003), and nothing else. No field,
requirement, or lifecycle rule of this contract is a normative dependency
on TAMC-001 or TAMPC-001; both remain unamended and unconsulted at
validation time (§17).

## 6. Human Principal, Identity, and Approval Authority

**RAE-REQ-005.** This repository has no OS-level, cryptographic, or
identity-provider authentication anywhere in its human-governance stack
today (independently re-confirmed: CHGR `assurance_level` L1
`os_authenticated_user` is an accepted schema enum value with no
supporting implementation; TAM `human_authorization.principal` is
documented as "does not verify... against any identity provider"). The
trust model this contract adopts, stated exactly and without
overstatement:

> The repository currently trusts the local CLI operator who can invoke
> a governed command against this checkout, identified only by a
> self-declared string captured through CHGR-001's Confirmation ritual.
> No stronger assurance exists anywhere in this codebase today.

**RAE-REQ-006.** A Rollback Approval Decision's `decision_maker_identity_evidence`
SHALL be captured at whatever `assurance_level` the CHGR pipeline
actually achieves at Confirmation time (today, `L0` — typed confirmation
only). This contract SHALL NOT claim, require, or fabricate a stronger
assurance level than what actually occurred (CHGR-001 §12, restated).

**RAE-REQ-007.** A claimed name or identity string supplied through a
CLI flag (e.g. a hypothetical `--approved-by Alice`) is NOT authenticated
approver identity and SHALL NOT be treated as such, unless it is the
`decision_maker_identity_evidence` of an actually-published CHGR record
reached through the full CHGR-001 Confirmation → Publication ritual.
Self-declared text supplied directly to a rollback command, outside that
ritual, carries zero trust under this contract (§14 threat #1).

**RAE-REQ-008.** Two distinct facts, both required, per §3's Approver /
Approval Authority definitions:

1. **Approval Authority** — the acting Approver matches the
   `rollback-approval` Decision Template's `eligible_authority` field
   (§7). No authority registry exists in this repository today; for the
   current single-operator local trust model, `eligible_authority` is
   expressed as descriptive text ("the human operator of this governed
   checkout"), matching RAE-REQ-005's honest ceiling. This is recorded
   as a STRATEGIC_GAP (§19), not fabricated as a stronger guarantee.
2. **Approval Event** — the Approver actually made the recorded Human
   Decision, evidenced by a published Rollback Approval Decision (§3).

A trusted Approval Event from an actor who is not, per the template's
`eligible_authority`, an eligible Approver is insufficient Rollback
Approval Evidence, even though CHGR-001's own schema cannot mechanically
enforce `eligible_authority` today (no registry exists to check against —
this is a manual/organizational control at present, disclosed honestly).

**RAE-REQ-009.** This repository has no technical privilege separation
between an agent process and a human operator; both reach the same CLI.
This contract's evidence model structurally prevents an agent from
**fabricating the shape** of approval evidence (§14 threat #2), but
cannot prevent an agent from **operating the CLI as the human** — a
pre-existing, already-accepted repository-wide limitation (PEC-REQ-034/046
"Model 2"), not created or worsened by this contract. Recorded as a
STRATEGIC_GAP (§19).

**RAE-REQ-010.** This contract's field shapes (`eligible_authority` as
descriptive text today, `decision_maker_identity_evidence` at its actual
assurance level) allow a future stronger identity-provider integration to
populate the same fields more strongly without redesigning this
contract's structure (149H §6.2's "future multi-user compatibility"
criterion, adopted unchanged).

## 7. Rollback Approval Decision (Decision Template)

**RAE-REQ-011.** This contract freezes a new CHGR-001 Decision Template,
`template_id = "rollback-approval"`, `version = "1.0.0"`, authored
against CHGR-001's existing, unamended `decision_template.schema.json`
shape. No CHGR-001 amendment is required or performed to introduce it.

**RAE-REQ-012.** The template's frozen field values:

| Field | Frozen value |
|---|---|
| `authoritative_basis` | `["RAE-001 Sec.7", "RWMPC-001 RWMPC-REQ-027"]` |
| `eligible_authority` | `"The human operator of this governed repository checkout, per RAE-001 Sec.6 Sec.8's trust model. No stronger authority-registry check exists today."` |
| `subject_binding_rule` | `"One instance per rollback attempt. decision_subject SHALL name the concrete Rollback Operation reference (AG3: job_id + original_commit_sha; AG5: per_id + ecp_id), never a generic phrase such as 'rollback approval'."` |
| `options` | Exactly two: `approve_rollback`, `deny_rollback` (RAE-REQ-013 below) |
| `required_fields` | `["decision_subject"]` |
| `optional_fields` | `["rationale", "conditions"]` |
| `confirmation_method` | `["L0"]` (repository ceiling per RAE-REQ-005; extensible without redesign per RAE-REQ-010) |
| `expiry_rule` | `"The Rollback Approval Decision itself does not expire; the Rollback Approval Binding record's own expires_at (Sec.9) is the operative freshness mechanism (Sec.11)."` |
| `supersession_rules` | `"A later, published Rollback Approval Decision for the same decision_subject supersedes an earlier one for evidence-resolution purposes; the earlier record's own CHGR lifecycle state is unaffected (CHGR-001 Sec.13.3) — supersession is enforced at the Binding-record layer (Sec.11), not by mutating the Decision record."` |
| `revocation_rules` | `"Revocation of a Rollback Approval Decision is expressed at the Binding-record layer (Sec.11) via state=revoked; CHGR-001's own revoked lifecycle state has no production writer today (149H Sec.18 NON-BLOCKING) and is not relied upon by this contract."` |
| `status` | `active` |

**RAE-REQ-013.** The two frozen options, with mandatory
`consequence_text`/`non_effect_text` per CHGR-001's existing schema:

- `approve_rollback` — `consequence_text`: "Records a human approval of
  the named Rollback Operation. This selection, combined with a valid
  Rollback Approval Binding record referencing it, may allow a future
  rollback request's `approval_present` to resolve `True`."
  `non_effect_text`: "Approval alone does not execute, schedule, or
  guarantee any rollback. Execution remains gated by the Permission
  Broker (POL-001 through POL-007), by RWMPC-001's live freshness
  re-check, and by AG3/AG5 remaining unimplemented today. This selection
  performs no repository mutation."
- `deny_rollback` — `consequence_text`: "Records a human refusal of the
  named Rollback Operation. A Rollback Approval Binding record MAY
  reference this decision to document the refusal for audit purposes."
  `non_effect_text`: "This selection performs no repository mutation and
  does not, by itself, block any future distinct rollback attempt against
  a different Rollback Operation reference."

**RAE-REQ-014.** No CLI flag, function argument, environment variable, or
other caller-declared value SHALL ever substitute for the two options
above by being interpreted as though it produced a published Rollback
Approval Decision. Only an actual `human_governance_record` published
against `rollback-approval`/`1.0.0` with `selected_option_id =
approve_rollback` qualifies (§14 threat #1).

**RAE-REQ-015.** A human decision of `APPROVE` (`approve_rollback`) or
`DENY`/`REJECT` (`deny_rollback`) is not, and SHALL NOT be conflated
with, a Permission Broker `ALLOW`/`DENY`/`HUMAN_REVIEW` decision. Broker
vocabulary and human-decision vocabulary are kept structurally distinct
per §4's semantic-layer separation. `approve_rollback` contributes
exactly one Permission Broker request fact
(`approval_present`, §13) and never itself resolves a broker decision.

## 8. Rollback Approval Binding — Field Table

**RAE-REQ-016.** This contract freezes a new, dedicated record type,
`rollback_approval_binding`, structurally modeled on (never composed
with) the Typed Authority Model `human_authorization` shape per
RAE-REQ-003/RAE-REQ-004. It is not a CHGR-001 record family and is not
stored under `src/pcae/schema_resources/chgr/**` or
`src/pcae/schema_resources/cltr_cutover/**`; a future implementation
phase defines its own dedicated schema namespace (e.g.
`src/pcae/schema_resources/rollback_approval/records/rollback_approval_binding.schema.json`),
not authored by this contract-only phase.

**RAE-REQ-017.** Frozen field table (types are conceptual/normative;
exact JSON Schema is a future implementation-phase artifact, per
149H §9's own "not frozen" caveat, now resolved to "frozen at the
field-name/semantics level, schema syntax deferred"):

| Field | Type | Required | Semantics |
|---|---|---|---|
| `evidence_id` | string, canonical identifier, assigned only at creation | Always | Stable identity of this Binding record for its lifetime (mirrors CHGR-001 §9's canonical-identity discipline). Never itself establishes authority. |
| `governance_record_reference` | `{record_id, record_digest}` of a `human_governance_record` | Always | Family-locked reference to the specific published Rollback Approval Decision (§7) this evidence anchors to. RAE-REQ-018 governs matching. |
| `rollback_site` | enum `AG3` \| `AG5` | Always | Which rollback mechanism this evidence targets; the two are structurally similar but not identical (149H §2), and this field prevents conflating them. |
| `rollback_operation_reference` | family-locked, per `rollback_site` (§10) | Always | The concrete Rollback Operation identity this evidence binds to. RAE-REQ-024/RAE-REQ-025 govern exact-match validation. |
| `task_id` | string, optional | Conditional | Present iff the Rollback Operation is task-scoped (per the active governed task at approval time); §11.3 governs binding semantics. |
| `repository_state_binding` | `{head_commit_sha, branch}` | Always | Repository state captured at approval time (§11.2) — distinct from RWMPC's own live execution-time freshness re-check. |
| `created_at` | timestamp | Always | Audit metadata (§13). |
| `expires_at` | timestamp | Always | Mandatory freshness window (§13); RAE-REQ-034 fixes the duration. |
| `state` | enum `issued` \| `used` \| `revoked` \| `expired` | Always | Mirrors `human_authorization.state` (structural reuse only, RAE-REQ-003). |
| `revocation_metadata` | `{revoked_at, revoked_by, reason_code}` | Conditional: required iff `state=revoked`, forbidden otherwise | Mirrors `human_authorization.revocation_metadata` shape. |
| `use_binding` | reference to the consuming rollback attempt's own outcome record | Conditional: required iff `state=used`, forbidden otherwise | §16 governs the exact transition point into `used`. |
| `replay_binding` | opaque one-time-use token reference | Always | §16 replay-prevention mechanism. |
| `decision` | enum `APPROVE` \| `DENY`, denormalized from `governance_record_reference`'s `selected_option_id` | Always | Convenience denormalization only; the Decision record (§7) remains the sole authoritative source — an inconsistency between this field and the referenced record's actual `selected_option_id` is a validation-layer failure (§12), never resolved in the Binding record's favor. |

**RAE-REQ-018.** `governance_record_reference` SHALL exactly match an
actually-published `human_governance_record` whose `template_ref`
resolves to `rollback-approval`/`1.0.0` (§7) and whose
`record_digest` matches the referenced record's current content-integrity
digest. A reference to a non-existent, unpublished, digest-mismatched, or
wrong-template record is invalid evidence (§12, §14 threat #10).

**RAE-REQ-019.** A single Rollback Approval Decision (§7) MAY be
referenced by at most one Rollback Approval Binding whose `state` is
`issued` or `used` at a time; a decision generically titled "approve
rollback" with no Binding referencing a specific operation is not, by
itself, Rollback Approval Evidence for any operation (§14 threat #18,
149H §16 "no blanket approve-all-rollbacks option"). A DENY decision
(`deny_rollback`) MAY also be referenced by a Binding record for audit
purposes; such a Binding's `decision` field SHALL be `DENY`, and RAE-REQ-030
governs its effect on `approval_present`.

## 9. Rollback Operation Identity

**RAE-REQ-020.** For AG3 (`execute_rollback`), the Rollback Operation
identity is the pair `{job_id, original_commit_sha}`, independently
re-derived from `build_rollback_review`'s own resolution requirement that
`original_commit_sha` be reachable from `HEAD` against a clean tree
(149H §2). Both fields are required in `rollback_operation_reference`
when `rollback_site=AG3`.

**RAE-REQ-021.** For AG5 (`build_rollback_execution`), the Rollback
Operation identity is the pair `{per_id, ecp_id}` — `per_id` naming the
`PromotionExecutionRecord` being restored, `ecp_id` the derived execution
context, per `build_rollback_execution`'s own signature (149H §2). Both
fields are required in `rollback_operation_reference` when
`rollback_site=AG5`.

**RAE-REQ-022.** `rollback_operation_reference` is family-locked per
`rollback_site` (AG3 uses the `{job_id, original_commit_sha}` shape; AG5
uses the `{per_id, ecp_id}` shape) — mirroring how
`human_authorization.target_reference` is family-locked per target type
(RAE-REQ-003 structural reuse). Neither shape is valid for the other
site; a mismatched shape is a schema-validation failure, not a
scope-validation failure.

**RAE-REQ-023.** One evidence contract (this contract) serves both AG3
and AG5, sharing all fields of §8's table except `rollback_operation_reference`'s
concrete family, per RAE-REQ-022. This resolves 149H §14's "common
approval model" question in favor of one shared contract with two
explicit, family-locked profiles (§10, §11 below), not two separate
contracts.

**RAE-REQ-024 (Wrong-target prevention).** Approval whose
`rollback_operation_reference` names Rollback Operation A SHALL NOT be
treated as valid evidence for Rollback Operation B, even where A and B
share a `rollback_site`, a `task_id`, or any other non-identity field.
The Evidence Validator (§12) SHALL perform exact, non-fuzzy matching
between the live rollback attempt's own operation identity (job_id +
original_commit_sha for AG3; per_id + ecp_id for AG5) and the Binding
record's `rollback_operation_reference` (§14 threat #7).

**RAE-REQ-025 (Wrong-payload prevention).** If the underlying rollback
payload identity changes after a Binding record is issued — for AG3, a
different `original_commit_sha` is now the applicable revert target; for
AG5, the referenced PER's `before_hash`/`after_hash` set changes — the
existing Binding record's `rollback_operation_reference` no longer
exactly matches, and evidence resolution SHALL fail per RAE-REQ-024. No
"equivalent regeneration" exception is defined by this contract; a new
Rollback Approval Decision and Binding are required for a changed
payload.

## 10. AG3 and AG5 Profiles

### 10.1 AG3 profile

**RAE-REQ-026.** For `rollback_site=AG3`, the Binding record SHALL
record: the caller (from `decision_maker_identity_evidence` on the
referenced Decision record — the Approver, never the rollback command's
own invoking process); `rollback_operation_reference = {job_id,
original_commit_sha}`; the rollback target (the commit `original_commit_sha`
reverts); the mechanism (`git revert --no-edit <original_commit_sha>`,
disclosed for reviewability per §15); and `repository_state_binding`
captured at approval time. AG3's mechanical precondition checks (clean
tree, `original_commit_sha` reachable from `HEAD`) remain AG3's own
existing responsibility, unchanged by this contract, and are re-verified
live at execution time regardless of evidence validity (§11.2).

### 10.2 AG5 profile

**RAE-REQ-027.** For `rollback_site=AG5`, the Binding record SHALL
record: the caller (same rule as RAE-REQ-026); `rollback_operation_reference
= {per_id, ecp_id}`; the rollback target (the file set the referenced
`PromotionExecutionRecord`'s `before_content`/`before_hash` restores);
the mechanism (direct file `write`/`unlink`, disclosed per §15); and
`repository_state_binding` captured at approval time. AG5's own
mechanical gating (`PER.status in {"completed","partial"}`,
`PER.rollback_payload_available=True`) remains AG5's own existing
responsibility, unchanged by this contract.

**RAE-REQ-028.** AG3 and AG5 do not share all fields (149H §12
independently reconfirmed this); this contract does not force artificial
field parity between the two profiles beyond the shared `rollback_site`-
locking discipline of §8-§9.

**RAE-REQ-029.** AG5 is reconfirmed, per 149D
(`docs/PHASE_149D_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT_INDEPENDENT_VERIFICATION.md:92-122`)
and 149H §2, to be a separate, explicitly-invoked, standalone command —
never an automatic in-band recovery path triggered by a promotion-execution
failure. This contract's evidence model targets explicit, human/agent-invoked
AG3/AG5 commands only; no automatic-recovery governance is defined, since
no automatic-recovery path exists to govern.

## 11. Operation, Task, Branch, and Repository-State Binding

**RAE-REQ-030.** Approval is task-bound where the Rollback Operation
itself originates in an active task context: `task_id` (§8) SHALL be
populated from the active governed task at approval time when one
exists, never inferred later or backfilled after the fact. Where no
active task exists at approval time, `task_id` is correctly absent, not
fabricated.

**RAE-REQ-031.** No separate phase-identity field is required beyond
`rollback_operation_reference` and `task_id`: `job_id`/`per_id` already
uniquely bind the operation, and duplicating phase identity on top would
add no additional structural guarantee (149H §14 item 29's
"do not duplicate if operation ID already uniquely binds it," resolved
here in favor of no duplication).

**RAE-REQ-032.** No explicit branch-binding field is required beyond
`repository_state_binding.branch` (§8): a rollback approved while on
branch A whose evidence is later evaluated against branch B fails
`repository_state_binding` staleness (RAE-REQ-033) without requiring a
separate normative branch field, since `repository_state_binding` already
captures branch identity at approval time.

**RAE-REQ-033 (Two-layer state binding, §4-style separation).**
`repository_state_binding` (§8) is captured **at approval time** as part
of the evidence and represents "the repository state the human reviewed
when approving" — it is distinct from RWMPC-001's own live,
execution-time freshness re-check of current `HEAD`, which remains
RWMPC's own existing, unduplicated responsibility. If live `HEAD`/branch
at the moment a rollback is actually attempted no longer matches the
evidence's `repository_state_binding`, the evidence is stale per §13 and
validation fails closed — but this contract does not perform, duplicate,
or replace RWMPC's own live freshness check; the two checks operate at
different layers and both apply independently.

## 12. Evidence Validator

**RAE-REQ-034.** A future, dedicated component — conceptually
`RollbackApprovalEvidenceValidator`, owned by core governance
infrastructure, not implemented by this contract-only phase — is the
sole component permitted to resolve Rollback Approval Evidence and derive
`approval_present`. Its conceptual interface:

```
resolve_rollback_approval_evidence(operation_context) -> ValidatedEvidence | None
```

**RAE-REQ-035.** Validation inputs are limited to: the live rollback
attempt's own operation context (site, operation-identity fields, current
task, current repository state); the explicitly-supplied evidence
reference (an `evidence_id`, never a "most recent" lookup, per RAE-REQ-041);
the referenced Rollback Approval Binding record; the referenced Rollback
Approval Decision record; and current canonical governance state needed
to check supersession/revocation. AESIC output is never a validation
input (§18).

**RAE-REQ-036.** Validation result is a structured outcome, one of:
`VALID`, `MISSING`, `INVALID`, `STALE`, `REVOKED`, `UNAUTHORIZED_APPROVER`,
`WRONG_SCOPE`, `SUPERSEDED`. This vocabulary is kept structurally distinct
from Permission Broker decision vocabulary (`ALLOW`/`DENY`/`HUMAN_REVIEW`)
per §4; a `VALID` validation result is an input fact to §13's derivation
rule, never itself a Permission Broker decision.

**RAE-REQ-037.** The Evidence Consumer (the future AG3/AG5 request-
construction code path) SHALL NOT perform trust evaluation itself. It
supplies only the evidence reference and the live operation context; the
Evidence Validator alone decides validity.

## 13. `approval_present` Derivation

**RAE-REQ-038 (Central derivation rule).**

```
approval_present = True
    IFF ALL of:
      (a) a Rollback Approval Binding record exists, matching the
          explicitly supplied evidence_id (no "latest" lookup, RAE-REQ-041)
      (b) that Binding record's governance_record_reference resolves to
          an actually-published human_governance_record whose template_ref
          is rollback-approval/1.0.0 (RAE-REQ-018)
      (c) that referenced Decision record's selected_option_id is
          approve_rollback (RAE-REQ-013, RAE-REQ-015)
      (d) the Decision record's decision_maker_identity_evidence
          identifies an Approver matching the template's
          eligible_authority (RAE-REQ-008)
      (e) the Binding record's rollback_operation_reference exactly
          matches the live rollback attempt's own operation identity
          (RAE-REQ-024)
      (f) the Binding record's state is issued (not used, revoked, or
          expired) (RAE-REQ-016, Sec.16)
      (g) the Binding record's expires_at has not passed and
          repository_state_binding still matches live state, or the
          live-state mismatch is limited to the distinct RWMPC live
          freshness layer per RAE-REQ-033 (Sec.14)
      (h) no later, published Rollback Approval Binding referencing the
          same rollback_operation_reference supersedes this one (Sec.15)
      (i) the Decision and Binding records' own content-integrity
          digests are valid (CHGR-001 Sec.10, restated at Sec.17)

approval_present = False
    OTHERWISE, including on any Evidence Validator internal error
    (fail-closed, RAE-REQ-042)
```

**RAE-REQ-039.** `approval_present=True` is never set by any CLI flag,
caller-supplied boolean, or agent-authored claim directly; it is always
the return value of the Evidence Validator's own evaluation of RAE-REQ-038.
This restates and specializes RWMPC-001 RWMPC-REQ-022's "agent requests
mutation != agent grants permission" for the rollback-approval evidence
layer specifically.

**RAE-REQ-040 (Approval is not permission).** `approve_rollback` !=
Permission Broker `ALLOW`. A `True` `approval_present` supplies exactly
one `PermissionBrokerRequest` field; POL-001 (active task), POL-003
(missing evidence), POL-006/POL-007 (unknown capability), and POL-005
(execution disabled, unconditionally triggered while `simulation_only`
is `False`) all continue to apply independently and may still resolve
`DENY` or `HUMAN_REVIEW` even where `approval_present=True` (149H §14,
restated).

**RAE-REQ-041 (No "latest approval" resolution).** The Evidence
Validator SHALL NOT select a Rollback Approval Binding merely because it
is the most recent Binding for a task, operator, or repository. Every
resolution requires an explicit `evidence_id` reference supplied by the
Evidence Consumer, matched exactly; ambiguous "use the latest" resolution
is forbidden (149H §12, RWMPC-001-style discipline).

**RAE-REQ-042 (Fail-closed on validator error).** If the Evidence
Validator itself errors during resolution (malformed record, unreadable
storage, schema-validation exception, or any other internal failure),
`approval_present=False` SHALL result, or resolution SHALL abort before
any `PermissionBrokerRequest` is constructed. In either case, zero
rollback mutation occurs.

## 14. Freshness

**RAE-REQ-043.** `expires_at` (§8) is mandatory on every Rollback
Approval Binding record. This contract adopts, as the frozen freshness
window, the same 24-hour duration `human_authorization.expires_at`
already establishes as repository precedent for exactly this kind of
operation-bound approval evidence (structural reuse per RAE-REQ-003,
never an arbitrarily invented duration). A future contract amendment MAY
revise this duration; this contract does not pre-authorize such a
revision.

**RAE-REQ-044.** Evidence additionally becomes stale, independent of
`expires_at`, if: `repository_state_binding` no longer matches live state
at evaluation time (RAE-REQ-033, subject to RWMPC's own separate live
check); or a superseding Rollback Approval Binding exists for the same
`rollback_operation_reference` (§15).

**RAE-REQ-045.** `created_at` and `issued_at`-equivalent timestamps on
both the Decision and Binding records are audit metadata; they are never
independently compared to derive validity beyond `expires_at`'s own
explicit check (RAE-REQ-043). No additional, undisclosed TTL is invented
from timestamp presence alone (149H §10, restated).

## 15. Revocation and Supersession

**RAE-REQ-046.** A Rollback Approval Binding record MAY transition to
`state=revoked`, with mandatory `revocation_metadata{revoked_at,
revoked_by, reason_code}` (§8), by an eligible Approval Authority (§7.2).
A revoked Binding record SHALL NEVER resolve `approval_present=True` for
any Rollback Operation (RAE-REQ-038(f)), enforced by the Evidence
Validator, never by trusting the caller.

**RAE-REQ-047.** A later, published Rollback Approval Binding record
referencing the same `rollback_operation_reference` supersedes an earlier
one for evidence-resolution purposes (RAE-REQ-038(h)); the earlier
record's own `state` field is not required to change for supersession to
take effect — the Evidence Validator SHALL prefer the latest non-revoked,
non-expired Binding for a given operation reference when more than one
exists, but SHALL still require an explicit `evidence_id` match per
RAE-REQ-041 (supersession governs which record is *authoritative* for an
operation reference; it does not create an implicit "latest" lookup
path).

**RAE-REQ-048.** This contract does not rely on CHGR-001's own `revoked`
lifecycle state, which has no production writer today (149H §18
NON-BLOCKING, independently re-confirmed). Revocation and supersession of
Rollback Approval Evidence are expressed entirely at the Binding-record
layer (§8), independent of that CHGR gap.

## 16. Replay Prevention and Single-Use Semantics

**RAE-REQ-049.** The underlying Rollback Approval Decision's own CHGR
publication is already package-id replay-guarded by PEC-001's atomic
commit path (`FileExistsError`-guarded, per 149H §4.1) — the same
governance act cannot be re-published under a new identity.

**RAE-REQ-050.** In addition, the Binding record's own `state: issued ->
used` transition, together with `replay_binding` (a one-time-use token
reference, mirroring `human_authorization.replay_binding`'s shape per
RAE-REQ-003), prevents the same evidence being presented twice to the
Evidence Validator for two distinct successful mutation attempts, even
where the underlying rollback attempt is mechanically retried.

**RAE-REQ-051 (Single-use is not blanket-invented).** Single-use applies
at the level of RAE-REQ-050's `state`/`replay_binding` mechanism; this
contract does not additionally invent single-use at the Decision-record
layer, since RAE-REQ-024's exact operation-identity binding already
prevents the same evidence being misapplied to a different operation
(item 37 of the governing phase prompt, answered specifically: exact
operation/state binding is the primary defense; `state`/`replay_binding`
is the secondary, execution-outcome-scoped defense).

**RAE-REQ-052 (Failed-execution retry).** If AG3/AG5's own mechanical
execution step (`git revert`, or the file `write`/`unlink` sequence)
fails before any actual mutation completes — not an approval failure, a
mechanical failure — with the exact same operation identity and
unchanged `repository_state_binding`, and the Binding record has not yet
transitioned to `used`, the same evidence MAY be presented again for a
retry attempt. A future implementation phase SHALL wire the exact
transition point into `used` to occur only on RWMPC-confirmed successful
mutation, not on Permission Broker `ALLOW` alone, so a purely mechanical
failure does not burn single-use evidence for no reason. This contract
freezes the requirement; it does not freeze the exact state-machine
wiring code.

**RAE-REQ-053 (Fresh broker evaluation on retry).** Even where the same
Rollback Approval Evidence remains valid across a retry (RAE-REQ-052), the
retry SHALL construct a fresh `PermissionBrokerRequest` and undergo a
fresh Permission Broker evaluation. No prior broker `ALLOW` decision is
ever reused across attempts (RWMPC-001's own existing per-attempt request
convention, restated here for the rollback-approval layer specifically).

## 17. Artifact Provenance and Integrity

**RAE-REQ-054.** The Rollback Approval Decision's provenance and
integrity are entirely inherited from CHGR-001 §10 (provenance) — no
parallel hashing or provenance mechanism is invented for the Decision
layer.

**RAE-REQ-055.** The Rollback Approval Binding record SHALL carry its
own content-integrity digest (structurally analogous to CHGR-001's
`governance_record_integrity`, computed over the Binding record's own
canonical bytes), so that `governance_record_reference` (§8) binds to a
specific, tamper-evident Decision record, and the Binding record itself
is independently tamper-evident to any future evidence consumer. No
cryptographic signing is required (matching CHGR-001 §12's ceiling); this
mirrors, not duplicates, CHGR's existing digest discipline.

**RAE-REQ-056.** Rollback Approval Decision and Binding records SHALL be
stored under canonical governance-artifact locations owned by core
governance infrastructure, not an arbitrary caller-specified file path.
The exact namespace (e.g. a sibling of `.pcae/governance-records/`
scoped to rollback-approval bindings) is a future implementation-phase
decision; this contract freezes only that storage is canonical and
non-arbitrary, never freely relocatable by a rollback command's own
caller-supplied path argument.

**RAE-REQ-057.** Once created, a Rollback Approval Binding record's
target/operation fields (`governance_record_reference`,
`rollback_site`, `rollback_operation_reference`, `task_id`,
`repository_state_binding`) SHALL NOT be edited in place. A change
requires a new Binding record (RAE-REQ-047's supersession path), never an
in-place mutation (CHGR-001 §13.3 immutability discipline, restated for
the Binding layer).

## 18. IWC and AESIC Exclusion

**RAE-REQ-058.** Interactive Workflow Confirmation MAY transport and
present the interactive session through which a Rollback Approval
Decision's Confirmation step (§7) occurs, exactly as it already does for
every other CHGR Decision Template — no IWC semantic change is required
or performed. IWC's own confirmation artifact
(`ConfirmationRequest`/`ConfirmationResponse`) is never itself Rollback
Approval Evidence; only the resulting **published CHGR record** (§7) is
(IWC-001 §1, RWMPC-REQ-023, both restated and upheld unchanged).

**RAE-REQ-059.** Authority Evaluation / AESIC results SHALL NOT
constitute, contribute to, or be consulted by the Evidence Validator's
derivation of Rollback Approval Evidence or `approval_present`
(AEM-REQ-003, RWMPC-REQ-023, both restated and upheld unchanged). AESIC
output MAY be cited as advisory context surfaced to the Approver during
the interactive session (§7's disclosed rollback target/scope, per §15
below), never as approval itself.

## 19. Legacy Flag Exclusion

**RAE-REQ-060.** The following inputs are explicitly frozen as
non-evidence, independently reconfirmed from 149H §3 / RWMPC-001 §11:
`--promotion-authorized`, `--reviewed-by`, `approve_rollback(root,
job_id)` (the existing bare state-flag function,
`src/pcae/core/agent.py:5146` — not to be confused with this contract's
`approve_rollback` Decision Template option, §7), `change_approval_state`,
`--approve-keep`, `--approved-by`, `--reason`. None of these establishes
Rollback Approval Evidence under this contract. A future implementation
phase MAY repurpose one of these as a mere lookup/transport parameter
that names a canonical `evidence_id` to resolve (e.g. reusing
`--approved-by`'s CLI slot to carry an evidence reference string) —
but the flag itself, and any value it carries, never itself establishes
approval; only the Evidence Validator's resolution of the referenced
canonical evidence does (RAE-REQ-038).

## 20. Human Review Presentation

**RAE-REQ-061.** The interactive session presenting the `rollback-approval`
Decision Template (§7) to the Approver SHALL disclose, at minimum, the
rollback target (site-specific per §10), the affected scope (files for
AG5, the reverted commit for AG3), the current task/phase context if any
(RAE-REQ-030), and current repository context (`repository_state_binding`,
§8) — rendered into the template's `consequence_text` per CHGR-001 §5's
existing disclosure discipline. AESIC output MAY be included as advisory
context in this presentation (§18), never as the approval decision
itself. No blanket "approve all rollbacks for this task" option exists;
the template's closed two-option set (§7) and the Binding record's
mandatory per-operation reference (§8-§9) structurally forbid it.

## 21. Failure Semantics and HUMAN_REVIEW Workflow

**RAE-REQ-062.** Missing evidence (no `evidence_id` supplied, or the
referenced Binding record does not exist) resolves `approval_present=False`,
which POL-004 resolves to `HUMAN_REVIEW` exactly as it does today for a
missing flag — zero rollback mutation.

**RAE-REQ-063.** Invalid evidence (any RAE-REQ-038 condition unmet) SHALL
NEVER resolve `approval_present=True`, regardless of how many conditions
are satisfied; the derivation rule is a strict conjunction (§13), not a
majority or best-effort evaluation.

**RAE-REQ-064.** Evidence validation failure (RAE-REQ-042) is a rollback
decision-consumption/input failure, not a Permission Broker policy
failure; it is attributed to evidence resolution, never miscategorized as
a POL-004 defect.

**RAE-REQ-065 (Flow).**

```
rollback intent constructed
        |
operation identity determined (job_id+commit for AG3, per_id+ecp_id for AG5)
        |
explicit evidence_id supplied (no implicit "latest" lookup, RAE-REQ-041)
        |
Evidence Validator resolves + validates (RAE-REQ-034-RAE-REQ-042)
        |
approval_present = True/False derived (RAE-REQ-038)
        |
PermissionBrokerRequest constructed fresh
        |
POL-001..POL-007 evaluation (unchanged)
```

`HUMAN_REVIEW` continues to mean exactly what it means today: the current
request lacks sufficient approval evidence — never an instruction for the
Permission Broker itself to go collect approval. The Permission Broker
remains a pure decision boundary; no interactive behavior is added to it
(RAE-REQ-066). After a human creates valid evidence, a **fresh** attempt
constructs a **new** request; there is no in-place mutation of a prior
`HUMAN_REVIEW` decision (149H §14, restated).

**RAE-REQ-066 (Broker remains non-interactive).** No approval-collection
capability is added to the Permission Broker Foundation by this contract.
The Permission Broker continues to evaluate pre-constructed request
fields only.

**RAE-REQ-067 (No automatic evidence creation).** A rollback command that
receives `HUMAN_REVIEW` SHALL NOT automatically create, self-issue, or
self-confirm a Rollback Approval Decision or Binding record on that
attempt's own behalf. At most, a future UX MAY initiate a separate,
distinct human interactive session (§7's own workflow) — never an
in-band auto-approval.

**RAE-REQ-068 (Rejection handling).** Where the Approver selects
`deny_rollback` (§7), `approval_present=False` is sufficient to represent
the refusal for Permission Broker purposes; this contract does not
overload the `approval_present` boolean with a distinct "explicitly
denied" signal for broker consumption, but the underlying published
`deny_rollback` Decision record remains available, undestroyed, and
citable for audit purposes distinct from the boolean itself.

## 22. Threat Model

| # | Threat | Contractual control |
|---|---|---|
| 1 | Self-declared CLI approval flag | RAE-REQ-007, RAE-REQ-014, RAE-REQ-039 — no flag can set `approval_present` |
| 2 | Agent-generated fake approval JSON | RAE-REQ-018 — evidence must anchor to an actually-published CHGR record via digest match |
| 3 | Forged actor identity | RAE-REQ-005/RAE-REQ-006 — not solved beyond repository ceiling; disclosed STRATEGIC_GAP (§19), not hidden |
| 4 | Unauthorized actor (no Approval Authority) | RAE-REQ-008(1), RAE-REQ-038(d) |
| 5 | Stale approval | RAE-REQ-043-RAE-REQ-045, RAE-REQ-038(g) |
| 6 | Approval replay | RAE-REQ-049-RAE-REQ-051 |
| 7 | Wrong rollback target | RAE-REQ-024, RAE-REQ-038(e) |
| 8 | Changed payload | RAE-REQ-025 |
| 9 | Changed task/phase | RAE-REQ-030, RAE-REQ-033 (state-binding staleness) |
| 10 | Tampered record | RAE-REQ-018 (digest match), RAE-REQ-055, RAE-REQ-038(i) |
| 11 | Latest-record mis-selection | RAE-REQ-041 — no "latest" lookup |
| 12 | Confirmation-as-approval | RAE-REQ-058 — structurally impossible; only a published Decision record qualifies |
| 13 | AESIC-as-approval | RAE-REQ-059 |
| 14 | Illegal CHGR/TAM composition | RAE-REQ-003, RAE-REQ-004 |
| 15 | Same broker decision reused after approval appears | RAE-REQ-053 — always a fresh broker request |
| 16 | Generic task-level approval reused broadly | RAE-REQ-019, RAE-REQ-061 (no blanket option) |
| 17 | Evidence validator internal failure | RAE-REQ-042 — fail closed |
| 18 | Structurally valid but noncanonical record | RAE-REQ-018, RAE-REQ-056 (canonical storage only) |
| 19 | Revoked approval reuse | RAE-REQ-046, RAE-REQ-038(f) |
| 20 | Superseded approval reuse | RAE-REQ-047, RAE-REQ-038(h) |

## 23. Satisfiability Matrix

**RAE-REQ-069.** Conceptual truthful requests, traced against the
current, unmodified `permission_broker_foundation.py` policy registry
(no code executed, matching RWMPC-001's own tracing methodology):

| Scenario | Evidence valid? | `approval_present` | POL-004 result | POL-005 result (`simulation_only=True`) | Rollback allowed to dispatch? |
|---|---|---|---|---|---|
| No evidence reference supplied | N/A | `False` | `HUMAN_REVIEW` | not triggered | No |
| Malformed/unreadable Binding record | Validator errors, fail-closed | `False` | `HUMAN_REVIEW` | not triggered | No |
| Wrong-target evidence (RAE-REQ-024 mismatch) | `WRONG_SCOPE` | `False` | `HUMAN_REVIEW` | not triggered | No |
| Unauthorized approver (fails `eligible_authority`) | `UNAUTHORIZED_APPROVER` | `False` | `HUMAN_REVIEW` | not triggered | No |
| Revoked evidence | `REVOKED` | `False` | `HUMAN_REVIEW` | not triggered | No |
| Stale (`expires_at` passed or `repository_state_binding` mismatch) | `STALE` | `False` | `HUMAN_REVIEW` | not triggered | No |
| Superseded evidence | `SUPERSEDED` | `False` | `HUMAN_REVIEW` | not triggered | No |
| Valid `approve_rollback` evidence, exact operation match, unexpired, unrevoked | `VALID` | `True` | not triggered | not triggered (still `simulation_only`) | **Yes, subject to POL-001/POL-003/POL-006/POL-007 and RWMPC live freshness — a `PermissionBrokerRequest` with `approval_present=True, execution_class=EXECUTION_CLASS_ROLLBACK, simulation_only=True` and otherwise-valid fields resolves `ALLOW`, independently traced against `MissingHumanApprovalRule` (POL-004, not triggered when `approval_present` is true) and `ExecutionDisabledRule` (POL-005, not triggered while `simulation_only=True`)** |
| Valid evidence, but a different applicable policy independently triggers (e.g. POL-001 no active task) | `VALID` | `True` | not triggered | not triggered | **No — a different policy denies/reviews; RAE-REQ-040 confirmed: approval is not permission** |

**RAE-REQ-070 (Live Foundation satisfiability, item 69).** This trace
independently reconfirms 149H's claim: a conceptual, otherwise-valid
`PermissionBrokerRequest` with `approval_present=True`,
`execution_class=EXECUTION_CLASS_ROLLBACK`, `simulation_only=True`
resolves `ALLOW` under the current, unmodified Foundation — demonstrating
that this contract's evidence model supplies exactly the input fact
RWMPC-REQ-027 identified as missing. No real rollback execution occurred
or is authorized by this trace; it is a conceptual policy-registry
evaluation only, matching RWMPC-001 §12's own methodology.

## 24. Compatibility Confirmations

**RAE-REQ-071.** RWMPC-001 v1.0 requires no amendment: RWMPC-REQ-017
already states, generically, that `approval_present` must reflect a real
evidence source, naming no specific artifact; this contract satisfies
that requirement without changing RWMPC-001's wording (§23 confirms
satisfiability).

**RAE-REQ-072.** PBPA-001 v1.0 requires no amendment: POL-004's
applicability and resolution logic (`src/pcae/core/permission_broker_foundation.py:449-486`)
are unchanged; this contract supplies evidence, never modifies policy.

**RAE-REQ-073.** PBPC-001 v1.2 requires no amendment: it is push-specific
and unrelated to rollback-class coverage.

**RAE-REQ-074.** CHGR-001 v1.0 requires no amendment: consumed only
through its existing Decision Template extension point (§7); no schema
or contract-text change.

**RAE-REQ-075.** IWC-001 v1.2 requires no amendment: consumed as
transport only (§18).

**RAE-REQ-076.** PEC-001 requires no amendment: consumed as the
publication mechanism only (§17), matching Publication Execution's own
"Model 2" v1.0 scope; this contract does not adopt PEC-001's named
"Model 3" hardening option.

**RAE-REQ-077.** TAMC-001/TAMPC-001 require no amendment and are not
composed with (§5); their own frozen wall with CHGR is upheld unchanged.

**RAE-REQ-078.** AESIC-001/AEM-001 require no amendment; disclosure-only
boundary upheld unchanged (§18).

## 25. Governance Responsibility

| Responsibility | Owner | Basis |
|---|---|---|
| `rollback-approval` Decision Template authorship/versioning | Implementer-class role performing governed template-authoring work (CHGR-001 §20 pattern) | §7 |
| Rollback Approval Binding schema authorship | Implementer-class role, future implementation phase | §8 |
| Interactive presentation | PCAE tooling, strictly bounded per CHGR-001 §4 | §7, §20 |
| Human selection (Approval Authority + Approval Event) | The eligible Approver §7's template names | §6, §7 |
| Confirmation, Publication | CHGR-001's existing, unamended pipeline | §5, §7 |
| Rollback Approval Binding creation | The same human-governance pipeline (§7), never a new parallel command family | §26 |
| Evidence Validator implementation and ownership | Core governance infrastructure (future implementation phase) | §12 |
| Verification | Independent Contract Verifier / Independent Implementation Verifier (existing roles) | throughout |
| Runtime consumption | Not yet assigned — remains an explicitly open question, matching CHGR-001 §20.5's own unresolved status | §12 |

## 26. Approval Creation Boundary

**RAE-REQ-079.** The architectural owner of Rollback Approval Decision
creation is the existing Interactive Workflow + Publication pipeline
consuming the `rollback-approval` Decision Template (§7) — not a new,
parallel command family. A future implementation phase MAY add a thin,
dedicated CLI convenience wrapper (e.g. `pcae rollback approve`), which
SHALL route through the full Confirmation → Publication ritual plus the
Binding-record creation step (§8), never a shortcut that toggles a
boolean directly.

**RAE-REQ-080.** No CLI is implemented by this contract-only phase.

## 27. Non-Goals

This contract explicitly excludes, and none of the following is
authorized, implemented, or amended by Phase 149I:

- Rollback production implementation (AG3/AG5 remain unimplemented).
- AG3/AG5 Permission Broker wiring.
- Permission Broker policy changes (POL-001 through POL-007 unchanged;
  no POL-008+ added).
- PBPA-001, PBPC-001 amendment.
- IWC-001, AESIC-001/AEM-001, TAMC-001/TAMPC-001, CHGR-001, PEC-001
  amendment.
- Composition of CHGR and TAM authority families.
- Prompt Generation or Prompt Dispatch capability.
- Runtime activation of any kind.
- TK1/TK2/TK3 lifecycle-internal coverage.
- Authoring an actual JSON Schema file for `rollback_approval_binding`
  (field names/types are frozen as normative prose in §8; schema syntax
  is a future implementation-phase artifact).

## 28. Findings

- **STRATEGIC_GAP** (carried forward from 149H §18, unchanged by this
  contract) — No stronger-than-self-declared human identity substrate
  exists anywhere in this repository. Rollback approval inherits, and
  does not attempt to paper over, this ceiling (RAE-REQ-005, RAE-REQ-006).
- **STRATEGIC_GAP** (carried forward from 149H §18, unchanged) — No
  technical privilege separation between an agent process and a human
  operator exists. This contract prevents evidence fabrication but cannot
  prevent operator impersonation at the OS level (RAE-REQ-009).
- **OBSERVATION** (carried forward from 149H §18, unchanged) — No
  existing approval-authority registry exists; `eligible_authority` is
  descriptive text, matching the single-operator local trust model
  (RAE-REQ-008(1)).
- **NON-BLOCKING** (carried forward from 149H §18, unchanged) — CHGR's
  own `revoked` lifecycle state has no production writer; this contract's
  revocation mechanism (§15) is independent of that gap (RAE-REQ-048).
- **OBSERVATION** — RWMPC-001, PBPA-001, PBPC-001 all require no
  amendment to consume this contract (§24); no clarification phase is
  needed for any of the three.
- **OBSERVATION** — This contract fixes the freshness window at 24 hours
  (RAE-REQ-043) by direct structural reuse of `human_authorization`'s own
  precedent; a future phase MAY revisit this duration through a
  dedicated amendment, but no BLOCKING gap results from fixing it now,
  since RAE-REQ-057's immutability discipline lets any future duration
  change apply only to newly issued Binding records.

No BLOCKING finding is raised. Every Blocking-condition category
identified by the governing phase prompt (§29 below) was independently
checked and found resolved by this contract's own text.

## 29. Blocking-Condition Check

Independently checked against the governing phase prompt's own Blocking
condition list:

| Blocking condition | Resolved? | Where |
|---|---|---|
| No trustworthy approver identity source | Resolved to repository's honest ceiling (self-declared, CHGR-anchored); disclosed as STRATEGIC_GAP, not fabricated stronger — not Blocking, since the contract does not overclaim | §6 |
| No authority source | Resolved via `eligible_authority` descriptive-text mechanism, disclosed as OBSERVATION not Blocking (matches the single-operator trust model this repository already relies on elsewhere, e.g. PEC-001 Model 2) | §6, §8 |
| No operation binding | Resolved — `rollback_operation_reference`, family-locked per site | §9, §10 |
| No provenance guarantee | Resolved — inherited from CHGR-001 §10 plus §17's own digest discipline | §17 |
| CHGR cannot legally host rollback approval semantics | False — CHGR-001 §6's Decision Template extension point is exactly designed for this; independently re-confirmed by direct schema reading (§7) | §7 |
| Record can be self-created by agent and trusted | False — RAE-REQ-018 requires anchoring to an actually-published CHGR record through the real Confirmation→Publication ritual; a hand-authored record fails digest/reference validation | §8, §22 threat #2 |
| RWMPC incompatible | False — §23/§24 independently trace satisfiability with no RWMPC-001 wording change required | §23, §24 |

No condition in this list is unresolved. This contract is FROZEN v1.0.

## 30. Versioning

**RAE-REQ-081.** This contract is versioned `1.0`, frozen only because
every Blocking trust question identified by the governing phase prompt
(§29) is resolved above. A future amendment (e.g. to revise the freshness
window, RAE-REQ-043, or to add a stronger identity-provider integration,
RAE-REQ-010) SHALL proceed through a governed contract-amendment phase,
never through silent reinterpretation of this text.

## 31. Contract Freeze Verdict

```
ROLLBACK APPROVAL EVIDENCE CONTRACT (RAE-001) v1.0 FROZEN
```

## 32. Rollback Readiness Status

```
ROLLBACK APPROVAL ARCHITECTURE:      DEFINED (Phase 149H)
ROLLBACK APPROVAL CONTRACT:          FROZEN (Phase 149I, this contract)
ROLLBACK APPROVAL IMPLEMENTATION:    NOT IMPLEMENTED
AG3 / AG5:                           STILL UNIMPLEMENTED
```

This contract's freeze does not imply rollback coverage exists. No
Decision Template is authored in production, no Binding-record schema
file exists, no Evidence Validator exists, and no CLI surface exists —
those are future, separately governed implementation-phase artifacts.

## 33. Recommended Next Phase

```
149J — Rollback Approval Evidence Contract Independent Verification
```

The independent verifier SHALL attack, at minimum: the trust source
(§6), identity model (§6), authority model (§7-§8), operation binding
(§9-§11), provenance (§17), replay/single-use (§16), revocation/
supersession (§15), the `approval_present` derivation rule (§13), the
CHGR/TAM wall (§5), the IWC/AESIC exclusion (§18), RWMPC/PBPA/PBPC
compatibility (§24), and the live Foundation satisfiability claim (§23).
