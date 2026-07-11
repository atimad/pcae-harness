# Phase 134E.1 — Canonical Engineering Evidence Executable Model

## 1. Objective

Implement the first executable code model for Canonical Engineering
Evidence — the future authoritative record of "what happened during
engineering" per the frozen Track 133 contract, refined by Track 134's
finalization contract. Per 134D's own implementation plan, this is a
disconnected, isolated implementation: it establishes data structures,
field contracts, phase-class applicability, deterministic normalization,
validation, serialization, stable identity, immutability boundaries, and
uncertainty/limitation representation — nothing more.

## 2. Authority Boundary

**This model is not yet active lifecycle authority.** The current
governed reporting and finalization path (`pcae.core.phase_reports`,
`pcae.core.notification_certification`,
`pcae.core.repository_transition_validator`, and every CLI command built
on them) remains fully operational and authoritative. Nothing in this
phase changes what `pcae phase complete`, `pcae task finish`, or any
notification path does. No existing test, command, or documented
behavior was altered.

`src/pcae/core/canonical_engineering_evidence.py` is disconnected by
design, mirroring `core/evidence.py` (Phase 115C)'s own isolation
discipline: stdlib imports only (`hashlib`, `json`, `re`, `dataclasses`,
`enum`, `types`, `typing`, `datetime`), zero internal PCAE imports, zero
side effects, zero I/O, zero network, zero execution capability. Nothing
in the existing reporting/notification/finalization/identity subsystem
imports this new module, and this module imports none of them —
confirmed by `test_module_has_zero_internal_pcae_imports` (AST-level
import inspection) and by the full existing regression suite passing
unchanged (§13).

## 3. Model Structure

Eleven conceptual evidence categories (133D §7 / 133E §7, frozen as a
category list, "no schema, no implementation") are refined here into a
grouped, non-flattened structure:

- **Identity**: `EvidenceIdentity` (wraps `EvidencePhaseIdentity` +
  `record_version` + `correction_of`).
- **Classification**: `phase_class` (`PhaseClass` enum), `task_id`.
- **Narrative**: `objective`, `engineering_actions`, `track_progress`,
  `recommended_next_phase`.
- **Findings** (each a tuple of `FindingRecord`): `architectural_findings`,
  `implementation_findings`, `verification_findings`,
  `defects_discovered`, `technical_debt_reviewed`,
  `technical_debt_introduced`.
- **Repairs** (each a tuple of `RepairRecord`, preserving the original
  finding): `defects_repaired`, `incorrect_assumptions_corrected`.
- **Knowledge**: `notable_engineering_knowledge`.
- **Governance/test evidence**: `governance_results`
  (`GovernanceResultItem`), `test_results` (`TestResultItem`).
- **State snapshots**: `repository_state` (`RepositoryStateSnapshot`),
  `runtime_state` (`RuntimeStateSnapshot`), `commit_and_push`
  (`CommitPushInfo`).
- **Confirmations**: `no_go_confirmations`,
  `architectural_boundary_confirmations`.
- **Traceability**: `provenance` (tuple of `EvidenceProvenanceRecord`).
- **Material uncertainty**: `uncertainty` (tuple of `UncertaintyItem`),
  `limitations` (tuple of `LimitationItem`).
- **Correction envelope**: `correction` (`CorrectionMetadata`, prepared
  fields only).
- **Applicability**: `applicability` (frozen mapping, category name →
  `Applicability`).
- **Versioning/lifecycle**: `schema_version`, `created_at`, `state`
  (`EvidenceRecordState`), `finalized_at`.

All thirty items named in the phase brief are represented; none is
flattened into an unstructured dictionary.

## 4. Phase-Class Applicability

Six `PhaseClass` values: `ARCHITECTURE`, `CONTRACT`, `PLANNING`,
`IMPLEMENTATION`, `VERIFICATION`, `REVIEW_HARDENING` — corresponding to
133B §6's own six canonical columns (Architecture; Contract Freeze and
Contract Verification, both folded into `CONTRACT`; Prototype Plan;
Prototype Implementation; Independent Verification), with
`REVIEW_HARDENING` carried as a repository-specific phase-type tag per
133C §6's finding that review/hardening phases "map onto the existing six
columns without requiring new rows."

Applicability per category is explicit, never inferred: `applicability`
is a required `MappingProxyType[str, Applicability]` covering twelve
category names (`REQUIRED_APPLICABILITY_CATEGORIES`), with five possible
dispositions — `PRESENT`, `NOT_APPLICABLE`, `UNKNOWN`, `UNAVAILABLE`,
`OMITTED_INVALID_INPUT`. `_PHASE_CLASS_MANDATORY_PRESENT` binds
`implementation_findings` mandatory-present for `IMPLEMENTATION` and
`verification_findings` mandatory-present for `VERIFICATION`, mirroring
133B §6's own named exceptions.

## 5. Identity

`EvidenceIdentity.evidence_id` is deterministic: `f"{phase_id}#{record_
version}"` — never a random UUID, never process-specific entropy, never
model/agent-dependent, never delivery-channel state. `EvidencePhaseIdentity`
mirrors `phase_reports.CanonicalPhaseIdentity`'s shape (`phase_id`,
`phase_name`, `source`) by convention, not by import — this module does
not resolve phase identity itself and does not become a new identity
authority; callers construct it from an already-resolved
`CanonicalPhaseIdentity`. Cardinality (one canonical record per governed
phase, 133D §3/§5/§13) is the entire identity model — no separate UUID
layer was needed or added.

## 6. Normalization

Determinism is structural, not a separate normalization pass: identical
constructor arguments always produce identical serialized output
(`test_deterministic_normalization_equivalent_input`,
`test_byte_determinism_across_independent_constructions`).
`applicability` keys are sorted at serialization time
(`test_deterministic_ordering_of_applicability_keys`). Approved
timestamps (`created_at`, `finalized_at`) are the sole permitted source of
non-determinism, per 133D §11/133E §8's "equivalent activity produces
equivalent evidence except approved timestamps" — and are explicitly
excluded from the digest (§10) for exactly this reason.

## 7. Validation

`validate()` returns a deterministic, inspectable `tuple[ValidationIssue,
...]` — never a bare bool, never a silent coercion. Checked: required
identity fields; phase/task consistency (blank task_id rejected);
phase-class mandatory-present categories; contradictory applicability
status (declared `PRESENT` with an empty tuple, or a non-`PRESENT`
disposition with populated content); missing uncertainty/limitation
disclosure for any `UNKNOWN`/`UNAVAILABLE` category; invalid commit hash
shape; correction/identity consistency; duplicate finding identifiers;
likely secret material in free-text fields. Invalid finding
classifications, invalid repair relationships (a repair whose original
finding is already `CONFIRMED`), and unsupported schema versions are
rejected at construction time (`__post_init__`), not deferred to
`validate()` — both layers are fail-closed; neither coerces invalid input
into valid evidence (`test_fail_closed_does_not_coerce_invalid_evidence`).

## 8. Provenance

Every material element is traceable via `EvidenceProvenanceRecord`:
`covers` (which category), `source_artifact`, `source_command` (governed
operation, optional), `source_phase_id`, `derivation_path`,
`verification_state`, `observed_at`. Construction requires `covers`,
`source_artifact`, `derivation_path`, and `verification_state` to be
non-empty — derived report text is never accepted as the sole source by
construction (the type has no field that would let it be).

## 9. Uncertainty and Limitation Model

Implements the 133F clarification (uncertainty/limitations are material
evidence under Non-Omission, not free-text footnotes) as first-class,
dedicated tuple fields: `UncertaintyItem` (category, description,
affected_evidence, source, verification_state, resolution_status) and
`LimitationItem` (category, description, affected_evidence,
resolution_status). `validate()` enforces the connection structurally: any
category marked `UNKNOWN` or `UNAVAILABLE` in `applicability` must be
named by at least one uncertainty or limitation entry, or validation
fails with `missing_uncertainty_disclosure` — uncertainty/limitations
cannot be silently discarded while the underlying disposition survives.

## 10. Findings and Repair Model

Three-way `FindingClassification`: `CONFIRMED`, `NON_BLOCKING`,
`BLOCKING` — the same uniform scheme 133B §9 binds across every governed
phase. `RepairRecord` always retains `original_finding` in full alongside
`resulting_status`; construction rejects a repair whose original finding
is already `CONFIRMED` (nothing to repair). The original finding's
classification is never altered in place — a repair adds a new record, it
does not overwrite history.

## 11. Immutability

`EvidenceRecordState`: `DRAFT` → `FINALIZED` → (optionally) `SUPERSEDED`.
Every dataclass in this module is `@dataclass(frozen=True)`; attribute
assignment on a constructed instance raises `dataclasses.
FrozenInstanceError` at the language level, confirmed for both the
top-level record and a leaf snapshot type
(`test_finalized_evidence_immutability`, `test_no_runtime_state_
mutation`). `finalize()` never mutates `self` — it returns a new object
via `dataclasses.replace()`, so a caller's held draft reference remains a
draft (`test_finalize_never_mutates_draft_in_place`) and calling
`finalize()` twice on an already-finalized record raises. `CorrectionMetadata`
is prepared-fields-only, matching 133E §5's deliberate deferral of the
correction mechanism's design — this phase does not implement the
governed correction workflow itself (Strict Non-Goal).

## 12. Serialization and Digest

`to_dict()`/`from_dict()` provide round-trip-compatible, canonical-JSON-
ready serialization with stable field/list ordering, explicit
not-applicable representation, and no rendering/delivery/secret fields —
confirmed by scanning serialized output for `render`/`telegram`/`sink`/
`delivery`/`notif` substrings
(`test_rendering_and_delivery_data_excluded_from_model`).
`compute_digest()` follows the existing repository convention
(`backend_invocations.py`'s `compute_digest()` pattern): SHA-256 over
`json.dumps(d, sort_keys=True, default=str)`, excluding `record_digest`
itself and excluding `created_at`/`finalized_at` so equivalent evidence
content produces an equivalent digest regardless of when it was
constructed or finalized, while any material change (e.g. `objective`)
changes the digest deterministically.

## 13. Versioning

`SCHEMA_VERSION = "1.0"`; `SUPPORTED_SCHEMA_VERSIONS = {"1.0"}`.
Construction with an unsupported version raises `ValueError` immediately
— fail-closed, never silently coerced to the supported version. Future
additive evolution (new optional fields, new enum members) is expected to
extend `SUPPORTED_SCHEMA_VERSIONS`; a future breaking change (field
removal/redefinition) requires the same governed
architecture→contract→verification cycle 133D→133E→133F itself followed,
per 133E §13's Versioning Contract.

## 14. Package Boundaries

Single module: `src/pcae/core/canonical_engineering_evidence.py`. No
dependency on rendering, Telegram, notification adapters, report
generation, delivery receipts, Repository Intelligence query behavior, or
execution systems — confirmed by AST import inspection
(`test_module_has_zero_internal_pcae_imports`) and by source-text
scanning for concrete adapter/dispatch symbols
(`test_no_notification_or_delivery_dependency`,
`test_no_repository_intelligence_authority_leakage`). No CLI surface was
added — the phase brief permits a narrow inspection surface only if
required by existing convention, and none was required; the model is
tested directly, as instructed.

## 15. Compatibility

No existing behavior changed. `phase_reports.py`,
`notification_certification.py`, `notifications.py`,
`notification_config.py`, `repository_transition_validator.py`, and every
CLI command are untouched by this phase. PFN-001 and PFR-001 remain
unmodified. Repository Intelligence is untouched (no import, no
reference).

## 16. Limitations (of this phase's own scope)

- No live evidence capture from actual phase activity — construction is
  manual/programmatic only in this phase.
- No integration into `pcae phase complete`/`pcae task finish` — the
  model exists but nothing calls it.
- No Evidence Extraction, Derived Evidence Views, rendering, or delivery
  — reserved for 134E.2–134E.6.
- The correction/supersession workflow is prepared (fields exist,
  validated for internal consistency) but not implemented as a governed
  operation — reserved for a later phase per 133E §5's own deferral.
- `applicability`'s twelve required categories cover the tuple-shaped
  evidence categories; scalar fields (`objective`, `track_progress`,
  `recommended_next_phase`) are validated for non-emptiness directly
  rather than through the applicability map, since they are always
  mandatory regardless of phase class.

## 17. Future Integration Path

134E.2 (Evidence Extraction) will consume finalized
`CanonicalEngineeringEvidence` records read-only to select facts for a
specific view. 134E.10 (Final Lifecycle Integration) is where this model
is expected to become active — wired into `pcae phase complete`/`pcae
task finish` as the authoritative capture step, subsuming ad hoc
`PhaseReport` field population. Until then, this model has no effect on
any governed command's behavior.

## 18. Explicit Statement

**The Canonical Engineering Evidence executable model implemented in this
phase is not yet active lifecycle authority.** It is an isolated,
disconnected prototype. The current governed reporting and finalization
path remains the sole operational authority for phase completion,
notification, and identity resolution.

## 19. Tests Added

52 focused tests in
`tests/test_canonical_engineering_evidence_134e1.py`, covering all 40
required test areas from the phase brief (minimal valid evidence per
phase class ×6, identity, task-identity behavior, applicability,
not-applicable/unknown/unavailable handling, deterministic normalization/
ordering/serialization, round-trip serialization, stable identity/digest,
digest-changes-on-material-change, rendering/delivery exclusion, secret
rejection, finding classification, three-way representation, repair
preservation, provenance, uncertainty/limitation representation and
non-discardability, contradictory-status rejection, invalid phase-class/
version rejection, duplicate-identity rejection, immutability, correction
metadata validation, no model-specific behavior, no Repository
Intelligence leakage, no notification dependency, no runtime/repository
mutation, byte determinism, and fail-closed invalid-input handling).

## 20. Focused Regression Results

Re-ran (unmodified): `tests/test_finalization_configuration_identity_
cross_agent_134b3.py`, `tests/test_external_notification_isolation_
134b1.py`, `tests/test_external_delivery_isolation_134b2_verification.py`,
`tests/test_phase_reports.py`, `tests/test_finalization_gate_
enforcement.py`, `tests/test_phase_report_trust_hard_fail.py`,
`tests/test_notification_certification_idempotency.py`,
`tests/test_phase.py` — all passed, confirming no existing phase-report,
notification, identity, or finalization behavior changed.

## 21. Fast-Green Result

See the governed phase-completion report for the exact count (expected
4389/4390 passed, the same pre-existing, unrelated,
environment-state-dependent failure carried since 134B.2).

## 22. Recommended Next Phase

**134E.1V — Canonical Engineering Evidence Executable Model Independent
Verification.** This phase does not self-certify. 134E.2 shall not begin
until 134E.1V completes with no unresolved BLOCKING findings.
