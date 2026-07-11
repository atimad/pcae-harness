# Phase 134E.7 — External Delivery Receipt Model

## 1. Objective

Implement a deterministic, durable, transport-neutral External
Delivery Receipt model that records one logical delivery, its physical
attempts, per-unit outcomes, retries, partial delivery, authorization
outcomes, adapter references, destination classification, traceability
to the rendered artifact, and correction/supersession relationships,
answering: *what delivery was intended, what physical attempts
occurred, what succeeded, what failed, and what is the authoritative
delivery state?* This phase implements only the generic receipt
model — not final lifecycle integration (134E.10), not PFN-001
integration, and not a replacement for current production notification
records.

## 2. Architectural Position

```
Canonical Engineering Evidence
        |
        v
Derived Evidence Views
        |
        v
RenderingResult
        |
        v
Delivery Pipeline
        |
        v
DeliveryExecutionResult
        |
        v
External Delivery Receipt Model      <- this phase
        |
        v
Final Lifecycle Integration          (134E.10, not implemented)
```

`src/pcae/core/delivery_receipt.py` imports only from
`pcae.core.delivery_pipeline` (`DeliveryExecutionResult`,
`DeliveryPlan`, `DeliveryRequest`, `DeliveryOutcome`,
`RetryRecommendation`, `get_adapter`) plus stdlib. It never imports the
canonical evidence model, the extraction layer, either derived-view
composition module, or the rendering layer directly — confirmed by a
dedicated source-line import scan
(`test_90_receipt_is_not_engineering_evidence_authority`,
`test_92_receipt_is_not_report_content_authority`).

## 3. Authority Boundary

External Delivery Receipts are authoritative only for delivery history
and delivery state. They are never authoritative for engineering
facts, report content, repository state, runtime state, phase
identity, phase completion, architectural findings, test results, or
governance results. Canonical Engineering Evidence remains
authoritative for what happened during engineering; `RenderingResult`
remains authoritative for the exact artifact presented for delivery;
the receipt records only what happened during delivery.

## 4. Current Lifecycle Inactivity

Nothing in the current governed reporting/finalization/notification
path imports or calls into this module — confirmed by a fresh
full-tree source scan
(`test_100_no_active_lifecycle_integration`). No production receipt
artifact is created by this phase; every persistence test targets a
`tmp_path`. The genuine terminal report for 134E.7 continues through
the existing governed production notification path.

## 5. Receipt Model

`ExternalDeliveryReceipt` (frozen dataclass) carries: `receipt_id`,
`receipt_version`, `logical_delivery_id`, `phase_id`,
`delivery_purpose`, `rendering_view_id`, `rendering_digest`,
`renderer_id`, `renderer_version`, `adapter_id`, `adapter_version`,
`destination_classification`, `safe_destination_alias`,
`policy_version`, `delivery_mode`, `logical_state`, an ordered tuple of
`attempts`, aggregate unit counts (`total_planned_units`,
`attempted_unit_count`, `delivered_unit_count`, `failed_unit_count`,
`pending_unit_count`, `retryable_failed_unit_count`,
`non_retryable_failed_unit_count`, `ambiguous_unit_count`),
`partial_delivery`, `retry_pending`, `operator_completeness`,
`first_attempt_at`/`latest_attempt_at`/`finalized_at`, `finalized`,
`diagnostics`, `uncertainty`, `limitations`, `correction`,
`provenance`, `authorization_evidence`, and `receipt_digest`. No bot
tokens, API keys, webhook URLs, or raw environment values ever appear
in any field — confirmed by dedicated tests
(`test_54_secret_exclusion`, `test_94_no_adapter_credentials_
persisted`, `test_95_no_concrete_secret_destination_persisted`).

## 6. Receipt Identity

`compute_receipt_id(logical_delivery_id, receipt_version)` hashes a
canonical JSON array (`json.dumps([logical_delivery_id,
receipt_version])`) — never a delimiter-joined string, avoiding the
exact class of ambiguity 134E.6V found and repaired in
`compute_logical_delivery_id`. Receipt identity is deterministic from
governed identity inputs only, never from mutable attempt state
(`test_2_receipt_identity_determinism`,
`test_3_receipt_identity_ambiguity_resistance`). Receipt identity,
logical delivery identity, physical attempt identity
(`compute_attempt_id`), adapter response identifiers, and
correction/supersession identity (`correcting_receipt_id`) are all
kept structurally distinct.

## 7. Physical Attempts

`DeliveryAttemptRecord` carries attempt identity, logical delivery
identity, attempt sequence, plan digest, rendering digest, adapter
identity/version, destination classification, policy version,
requested/attempted unit ID lists, per-unit outcomes, overall outcome,
retryable flag, timestamps, `retry_of`/`retry_reason`, diagnostics,
uncertainty, limitations, and an attempt digest. `build_attempt()`
constructs one from a validated `DeliveryExecutionResult`/
`DeliveryPlan`/`DeliveryRequest` triple, failing closed on any
cross-input identity or rendering-digest mismatch.

## 8. Attempt Sequence

Attempt sequence starts at 1 and must increment by exactly one from
the previous attempt — both duplicate and missing-intermediate
sequence numbers are rejected
(`test_8_duplicate_attempt_sequence_rejected`,
`test_9_missing_attempt_sequence_rejected`). A later attempt cannot
start before the previous attempt completed (timestamp monotonicity is
checked via `datetime.fromisoformat` comparison). Ordering never
depends on filesystem order — attempts are always an explicit ordered
tuple embedded in the receipt.

## 9. Per-Unit Outcomes

`UnitOutcomeRecord` preserves unit identity, order, mode, content
hash, attempted flag, outcome (`delivered`/`failed`/`ambiguous`/
`not_attempted`), retryability, adapter response reference, error
classification, a redacted diagnostic summary, and per-unit
uncertainty/limitations. Full rendered content is never persisted
redundantly — `rendering_digest` plus each unit's `content_hash`
provide traceability without duplicating content.

## 10. Logical Delivery State

`LogicalDeliveryState` enumerates `pending`, `delivered`,
`partially_delivered`, `failed_retryable`, `failed_non_retryable`,
`blocked_by_authorization`, `disabled_by_policy`, `invalid`,
`superseded`, `corrected`. State is derived deterministically
(`_derive_logical_state`) from aggregate unit counts and the latest
attempt's overall outcome — never manually asserted independently. A
receipt never classifies partial, blocked, disabled, failed, or
unknown as delivered — `delivered` requires every planned unit
delivered (`test_11_delivered_aggregate` through `test_20_blocked_not_
delivered`).

## 11. Aggregate Derivation

`_aggregate()` computes last-attempt-wins per-unit state
(`_latest_unit_states`) across the full attempt history: a unit
delivered on a later retry is counted once as delivered, while earlier
failed attempts remain fully visible in attempt history
(`test_31_successful_unit_not_double_counted`,
`test_32_failed_then_successful_unit_aggregate`). Total planned units
is fixed at receipt-open time from the original full plan, never
recomputed from a later (necessarily smaller) retry plan.

## 12. Logical Versus Physical Exactly-Once

This module guarantees **logical** exactly-once: one logical delivery
identity maps to exactly one receipt lineage (via `compute_receipt_
id`) and one final logical state. It makes **no** claim of physical
exactly-once delivery — calling `execute_delivery()` twice against the
identical plan independently executes the adapter twice
(`test_23_physical_exactly_once_not_claimed`); physical attempts are
recorded individually, never collapsed into a single "it happened
once" claim.

## 13. Ambiguous Outcomes

`build_attempt(..., ambiguous_unit_ids=...)` lets a caller with
adapter-specific knowledge (e.g. a timeout that may have completed the
external side effect before failing) mark specific units as ambiguous
rather than failed — `execute_delivery()` itself has no ambiguous
vocabulary, so this distinction is made only at the receipt layer,
never invented inside the generic pipeline
(`test_21_ambiguous_outcome`, `test_22_ambiguous_side_effect_
uncertainty`). Ambiguous units are never automatically retried and
never force-classified as delivered or failed without evidence;
`pending_retry_unit_ids()` deliberately excludes ambiguous units.

## 14. Retry Lineage

`append_attempt()` structurally rejects changed rendering/destination/
adapter/purpose/policy under the same lineage: `compute_logical_
delivery_id` already includes all of those fields, so any change
produces a different `logical_delivery_id`, caught as "different
logical delivery" before any content-level check runs
(`test_27_changed_rendering_retry_rejected` through `test_30_changed_
purpose_retry_rejected`). A retry attempt references its predecessor
via `retry_of`, carries an optional `retry_reason`, and never changes
`logical_delivery_id` or `rendering_digest`.

## 15. Correction and Supersession

`CorrectionRecord` carries `original_receipt_id`, `reason`,
`correcting_receipt_id`, `direction` (`corrects`/`supersedes`),
`affected_logical_delivery_id`, and `operator_followup_occurred`. It
fails closed on self-reference (`original_receipt_id ==
correcting_receipt_id`) at construction time
(`test_43_correction_cycle_rejected`). `apply_correction()` only
operates on a finalized receipt, requires the correction to reference
that exact receipt, and rejects reapplying a correction to an
already-corrected receipt — which also structurally prevents two-hop
cycles (`test_44_supersession_cycle_rejected`). Correction/supersession
identity is explicitly distinct from receipt identity: the corrected
value's `receipt_id` becomes `correction.correcting_receipt_id`,
never colliding with the original. The original receipt object is
never mutated (`test_45_original_receipt_preserved`) — it is a frozen
dataclass, and persistence stores the corrected value as a purely
additive overlay (`DeliveryReceiptStore.save_correction`), the
original primary file untouched, matching the phase's own "without
implementing full lifecycle orchestration" boundary.

## 16. Receipt Finalization

A receipt may be finalized when: delivered completely; failed
non-retryably; blocked/disabled with no permitted retry; superseded/
corrected; or explicitly, governedly closed with disclosed ambiguity.
A retryable failure or unresolved ambiguity blocks `finalize_
receipt()` unless the caller passes `force_close=True` with an
explicit `close_reason`, which is recorded in the receipt's
diagnostics (`test_35_retryable_receipt_not_final`). Finalized
receipts are immutable — `finalize_receipt()`/`append_attempt()` both
raise on an already-finalized receipt (`test_39_finalized_receipt_
immutable`).

## 17. Immutability

All dataclasses (`UnitOutcomeRecord`, `DeliveryAttemptRecord`,
`CorrectionRecord`, `ExternalDeliveryReceipt`) are `frozen=True`.
Nested mutable containers are additionally wrapped:
`provenance`/`authorization_evidence` become `MappingProxyType` views
in `__post_init__`, so even nested dict mutation is rejected, not just
top-level attribute assignment — deep immutability, not merely a
frozen outer shell (`test_40_deep_immutability`). Corrections create
new values via `apply_correction()`; they never mutate a finalized
receipt.

## 18. Persistence

`DeliveryReceiptStore` is the smallest durable, file-backed
persistence layer consistent with existing PCAE atomic-write/digest-
verification conventions (mirroring `shell_gate.persist_audit_record`/
`verify_audit_records`, Phase 93C). Writes go to a temp file then
`os.replace()` — never a partial file at the final path
(`test_69_atomic_write`, `test_70_interrupted_write_recovery_or_
failure`). `save()` fails closed on: an already-finalized primary
record (`test_71_no_silent_overwrite`), a receipt-identity mismatch
under the same logical delivery (`test_72_duplicate_receipt_
persistence_rejection`), a fewer-attempts stale write
(`test_75_stale_write_detection`), and an optional
`expected_previous_digest` mismatch for basic optimistic concurrency
(`test_74_concurrent_append_behavior`). `load()` verifies the receipt
digest and schema version on every read, raising on corruption or an
unsupported version (`test_76_digest_validation_on_load`,
`test_77_corrupt_receipt_rejected`, `test_78_unsupported_version_
rejected`).

## 19. Storage Layout

```
<root>/receipts/<logical_delivery_id>/receipt.json
<root>/corrections/<original_receipt_id>/<correcting_receipt_id>.json
```

Grouped by logical delivery identity — never an adapter-specific
directory such as `telegram/` (`test_80_transport_neutral_storage_
layout`, `test_81_no_telegram_directory_naming`). `DEFAULT_RECEIPT_
STORE_ROOT = ".pcae/delivery-receipts"` is documented as the eventual
production convention only — nothing in this phase instantiates a
store against it (`test_106_no_repository_mutation_in_ordinary_
tests`); `.pcae/.gitignore` was updated to add `delivery-receipts/`
alongside the existing `phase-reports/`/`notifications/` ephemeral
entries so a future phase's real usage remains untracked, matching
128A's own naming-consistency finding (this phase deliberately does
**not** introduce a third synonym alongside RKS/HM's `snapshots/` and
DKG's `graphs/` — `receipts` is a genuinely new noun, not another
alias for the same "point-in-time capture" concept).

## 20. Atomicity/Concurrency

Two writers: the second's `save()` either succeeds as a legitimate
append (more attempts than stored) or is rejected as stale (fewer
attempts, or an `expected_previous_digest` mismatch). A finalized
record can never be silently overwritten by a second writer regardless
of digest checks. No distributed coordination is introduced — this is
intentionally the smallest mechanism sufficient for single-repository,
single-process governed use, matching the phase's own "do not
overbuild distributed coordination" instruction.

## 21. Serialization/Digest

`to_dict()`/`_receipt_from_dict()` round-trip losslessly
(`test_47_round_trip_serialization`) with stable field ordering via
`json.dumps(..., sort_keys=True)`. `receipt_digest` is a SHA-256 over
the full receipt dict with only `receipt_digest` itself excluded —
changing attempt history, uncertainty, limitations, or correction
metadata all change the digest (`test_50_digest_changes_with_new_
attempt` through `test_53_digest_changes_with_correction`).
`attempt_digest` is computed identically, excluding only
`attempt_digest` itself. Timestamps are included in both digests (they
are material state, not incidental formatting) — supplying identical
timestamps across two otherwise-identical builds yields identical
digests (`test_97_unknown_future_agent_independence`).

## 22. Diagnostic Redaction

Addresses 134E.6V's NON-BLOCKING observation directly. `_sanitize_
diagnostic()` recognizes the exact normalized shape `execute_
delivery()` produces for adapter exceptions (`"adapter raised
<ExceptionType>: <message>"`) and persists only a class-derived
category plus a bounded (200-char), pattern-redacted message — never
the raw exception text (`test_55_adapter_exception_diagnostic_
redaction`). Bounded, explicit-pattern redaction (bot-token shapes,
`PCAE_*_TOKEN=` assignments, `Authorization: Bearer` headers, any
`https?://` URL, generic `key=`/`secret=`/`password=` assignments) —
not a universal secret scanner, per the phase's own instruction — reusing
the same convention already established by `canonical_engineering_
evidence._contains_likely_secret` and `shell_gate._redact_command_text`
(`test_56_authorization_header_redaction`).

## 23. Destination Privacy

Only `safe_destination_alias` (already governed by `AdapterCapabilities`
in the delivery pipeline) is ever persisted — never a raw channel ID,
email address, or webhook URL (`test_57_destination_privacy`,
`test_58_safe_destination_alias`).

## 24. Provenance

Every receipt traces to phase identity, rendering identity/digest,
delivery request logical identity, plan digest, adapter identity/
version, and policy version via the `provenance` mapping
(`test_59_provenance`). No secret ever appears as provenance.

## 25. Authorization Evidence

`authorization_evidence` records whether the adapter represents
external delivery, whether authorization was required, the
authorization outcome (`not_required`/`authorized`/`denied`),
synthetic/production destination classification, policy version, and a
denial reason code where applicable (`test_60_authorization_
evidence`) — never a token or authorization header.

## 26. Operator Completeness

`OperatorCompletenessState` (`complete`/`partial`/`unknown`/`invalid`)
is distinct from unit delivery counts: `complete` only when logical
state is `delivered` (every unit delivered); `unknown` for unresolved
ambiguity or a still-pending receipt; `invalid` for an invalid plan/
outcome; `partial` for every other definite-but-incomplete state
(`partially_delivered`, `failed_retryable`, `failed_non_retryable`,
`blocked_by_authorization`, `disabled_by_policy`, `superseded`,
`corrected`). Multipart-missing-segment and attachment-envelope-
success-with-attachment-failure scenarios both correctly resolve to
`partial`, never `complete` (`test_65_attachment_envelope_success_
with_attachment_failure`, `test_66_multipart_missing_segment`).

## 27. PFN-001 Readiness

The receipt model is capable of later supporting PFN-001 decisions —
`delivered`, a durable `failed_non_retryable` record, `retry_pending`,
and `correction_required` (via `correction`) are all independently
representable (`test_108_durable_failure_state_representable` through
`test_110_correction_required_state_representable`). No PFN-001
integration is implemented; the module contains no call into
`pcae.core.notifications`' dispatch path, and `notifications.py` itself
carries zero reference to `delivery_receipt`
(`test_101_current_telegram_unchanged`, `test_102_current_pfn001_
unchanged`).

## 28. Inspection API

A narrow, read-only surface: `validate_receipt_digest()`,
`pending_retry_unit_ids()`, `DeliveryReceiptStore.load()`/
`list_attempts()`/`list_corrections()`. No dashboard, network API, or
CLI was added, per the phase's own instruction to add one only if
repository conventions require it (none do for this phase's scope).

## 29. Validation/Failure

Fails closed for: missing/mismatched logical delivery identity across
inputs, mismatched rendering digest, unsupported schema version,
duplicate receipt identity, duplicate/missing/out-of-order attempt
sequence, an attempt from a different logical delivery, changed
rendering/destination/adapter/purpose/policy under retry, mutation of
a finalized receipt, a correction/supersession cycle, a stale/
overwrite persistence write, digest mismatch, and corrupted storage.
Every failure is a deterministic `ValueError`/`FileNotFoundError` with
a specific, matchable message.

## 30. Transport Independence

Source-text scan (AST docstring-stripped, per the false-positive
lesson from 134E.5/134E.6) confirms zero Telegram/email/Slack/Teams/
Discord-specific import or branch anywhere in `delivery_receipt.py`
(`test_99_transport_independent_core`). Adapter-specific response
references are already normalized upstream by the delivery pipeline
(`adapter_response_ref` is an opaque string); this module never
branches on their shape.

## 31. Model/Agent Independence

No agent- or model-identity parameter exists anywhere in this module's
public signatures (`test_96_agent_model_independence`). Equivalent
delivery execution history produces byte-identical receipts regardless
of which agent invoked the pipeline (`test_97_unknown_future_agent_
independence`).

## 32. Limitations

This phase does not implement: full correction/supersession lifecycle
orchestration (only the additive record + cycle-rejection primitives);
distributed/multi-process locking beyond optimistic-concurrency digest
checks; a production CLI; a universal secret scanner (bounded,
explicit-pattern redaction only); or any store instantiated against
`DEFAULT_RECEIPT_STORE_ROOT` in production. These are explicitly
out of scope per this phase's own non-goals, not oversights.

## 33. Future Lifecycle Integration

134E.10 (Final Lifecycle Integration, not yet scheduled) is expected to
wire this receipt model into PFN-001 decision-making and the governed
finalization path. `ExternalDeliveryReceipt.to_dict()` already exposes
every field such integration would need (`logical_state`,
`receipt_digest`, `operator_completeness`, `retry_pending`) without
further transformation (`test_107_receipt_suitable_for_134e10_
integration`). No such wiring exists yet; the module remains fully
isolated (Section 4).
