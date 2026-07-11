# Phase 134E.6 — Delivery Pipeline Generalization

## 1. Objective

Implement a deterministic, transport-neutral Delivery Pipeline that
accepts a verified `RenderingResult` (134E.5, independently verified
and repaired by 134E.5V) and prepares or executes delivery through
explicitly registered delivery adapters, without changing the rendered
engineering content. This phase implements only the generic pipeline —
not the durable External Delivery Receipt model, and not a replacement
for current production notification delivery.

## 2. Architectural Position

```
Canonical Engineering Evidence
        |
        v
Evidence Extraction
        |
        v
Derived Evidence Views
        |
        v
RenderingResult
        |
        v
Delivery Pipeline                    <- this phase
        |
        v
Delivery Adapter
        |
        v
Adapter Delivery Outcome
        |
        v
External Delivery Receipt Model      (134E.7, not implemented)
```

The Delivery Pipeline consumes only a validated `RenderingResult`. It
never imports the canonical evidence model, the extraction layer, or
either derived-view composition module beneath it — confirmed by a
dedicated source-line import scan
(`test_no_evidence_or_view_imports_in_generic_core`).

## 3. Authority Boundary

The Delivery Pipeline is operational infrastructure only. It never
becomes engineering evidence authority, report-content authority,
phase identity authority, phase completion authority, repository-state
authority, runtime-state authority, or durable receipt authority. The
`RenderingResult` defines the exact content to deliver; the pipeline
may adapt packaging to transport constraints (inline vs. attachment vs.
multipart) but never changes informational content — enforced by the
content-preservation check every `DeliveryPlan` must pass before it can
exist (`plan_delivery()` raises rather than returning an
incompletely-representing plan).

## 4. Current Lifecycle Inactivity

The new pipeline remains completely inactive. Confirmed by: a fresh
full-tree source scan finding zero references to
`pcae.core.delivery_pipeline` anywhere outside its own module and test
files (`test_no_consumer_references_delivery_pipeline_yet`); direct
source inspection confirming `pcae.core.notifications`,
`pcae.core.phase_reports`, and `pcae.core.notification_certification`
contain no reference to `delivery_pipeline`
(`test_current_notification_behavior_unchanged`,
`test_current_report_generation_unchanged`,
`test_current_pfn001_behavior_unchanged`). The genuine terminal report
for this phase is delivered through the existing, unmodified production
notification path — not through this new pipeline.

## 5. DeliveryRequest

`DeliveryRequest` is the deterministic input to planning: logical
delivery identity, phase identity, rendering view identity/digest,
renderer identity/version, media type, complete rendered content,
content size, destination classification, adapter identity/version,
delivery purpose, synthetic/test classification, requested delivery
mode, policy version, uncertainty/limitation presence indicators, and
request diagnostics. Contains **no secrets** — credentials and
concrete destination values belong to adapter configuration, resolved
through the existing neutral configuration boundary, never serialized
here (`test_destination_classification_no_secrets`,
`test_plan_contains_no_secrets`).

## 6. Logical Delivery Identity

`compute_logical_delivery_id(phase_id, rendering_digest, purpose,
destination, adapter_id, policy_version)` is a deterministic SHA-256
over exactly those six governed inputs — never a random UUID, attempt
number, retry timestamp, process identity, model identity, or
transport response ID. Because `rendering_digest` is one of the inputs,
a changed rendering under otherwise-identical governed inputs always
produces a **different** logical delivery identity by construction —
"changed content under the same logical identity" is structurally
unreachable, not merely checked after the fact
(`test_different_rendering_changes_logical_identity`,
`test_changed_content_retry_rejected`). Retries preserve the identical
logical delivery identity (`test_retry_preserves_logical_identity`).

## 7. Delivery Purposes

`DeliveryPurpose`: `operator_terminal_report`, `canonical_phase_report`,
`correction_notice`, `live_integration_test`, `milestone_delivery` —
exactly the purposes current Track 134 design requires, deliberately
not a broad arbitrary messaging platform.

## 8. Destination Classifications

`DestinationClassification`: `production_operator`, `integration_test`,
`synthetic_recording`, `disabled`, `future_governed` — safe
classifications only, never a concrete channel ID, email address, or
webhook URL. Concrete destinations remain entirely inside adapter
configuration.

## 9. Adapter Contract

`AdapterCapabilities` declares: adapter ID, adapter version, supported
media types, supported delivery modes, maximum inline payload size,
attachment support, `represents_external_delivery` (the authorization
trigger), `safe_destination_alias`, and `always_disabled`.
`DeliveryAdapter` pairs capabilities with a deterministic
`deliver_fn: DeliveryUnit -> AdapterUnitOutcome`. Adapters never select
evidence, compose a view, render a report, summarize content, remove
sections, alter findings, change completeness, or strengthen
classifications — structurally guaranteed by the contract itself: a
`DeliveryUnit` carries only already-rendered text and metadata, nothing
an adapter could use to re-derive or alter engineering meaning.

## 10. Adapter Registry

`_ADAPTER_REGISTRY: dict[str, DeliveryAdapter]` — a small explicit
dict, not a plugin framework, mirroring the identical fail-closed
convention the extraction profile registry and `rendering.
register_renderer()` already established: a differing re-registration
under an existing `adapter_id` raises
(`test_duplicate_adapter_registration_rejected`); an identical
re-registration is a harmless no-op; registration order never affects
selection (`test_adapter_registration_order_independence`); future
adapter registration never alters an existing adapter's behavior
(`test_future_adapter_registration_does_not_alter_existing_behavior`).

## 11. Initial Isolated Adapters

**Recording adapter** (`recording_v1`) — no external I/O; records every
delivered unit in an in-memory, test-inspectable log
(`get_recording_log()`/`clear_recording_log()`); supports inline and
attachment modes; deterministic; the default adapter for all ordinary
tests. **Null/disabled adapter** (`null_v1`) — performs no delivery;
`always_disabled=True` short-circuits both planning (bypassing ordinary
mode-selection, since no content will ever actually be sent) and
execution (always returns `DISABLED_BY_POLICY`, never pretends
success). No Telegram compatibility wrapper was implemented — 134D was
not found to explicitly assign this to 134E.6, and building one would
risk conflating this phase's generic architecture with Telegram-specific
concerns; deferred to a future phase if a concrete need emerges.

## 12. Delivery Modes

`DeliveryMode`: `inline`, `attachment`, `multipart_inline`,
`overview_plus_attachment` (reserved, never selected — see Section 22),
`disabled`. Mode selection (`_select_mode`) is purely deterministic
from content size, adapter capabilities, and policy — never model
judgment. An explicitly `requested_mode` on the request, if given and
supported by the adapter, is honored verbatim; otherwise the algorithm
tries inline, then attachment, then multipart, in that fixed order,
raising if none is available (never silently falling back to a
truncated or status-only message).

## 13. Content Packaging

The pipeline packages the complete `RenderingResult.rendered_content`
verbatim — one inline artifact, one attachment, or deterministic
ordered segments. It never creates a new summary; no separate overview
renderer exists in this phase (Section 22), so `overview_plus_
attachment` is defined but never chosen.

## 14. Channel-Limit Handling

`_select_mode` detects when inline content exceeds `min(policy.
inline_size_threshold, adapter.max_inline_bytes)` and falls through to
attachment, then multipart, per policy. If no complete mode is
available, `plan_delivery()` raises — it never truncates, sends only a
final segment, drops sections, or silently downgrades to a status-only
message (`test_no_complete_mode_available_fails_closed`,
`test_no_truncation_ever`).

## 15. Deterministic Segmentation

`_segment_content()` splits on exact character offsets guaranteeing
`"".join(segments) == content` always — never approximate,
never lossy. Splits occur at the last newline before the byte
threshold where one exists (never mid-line except when a single line
itself exceeds the threshold, which remains fully deterministic).
Every `DeliveryUnit` carries `index`, `total`, the plan's own
`logical_delivery_id`, and a content hash — full reconstruction and
traceability on every segment
(`test_deterministic_segment_boundaries_and_order`,
`test_segment_reconstruction_equals_source`,
`test_segment_traceability`).

## 16. Attachment Handling

Attachment units derive their content directly from `RenderingResult.
rendered_content` (never a separate file read); filenames are
deterministic (`{logical_delivery_id[:16]}.{extension}`, extension
derived from media type); content hash is SHA-256 of the exact
attachment text. No temporary files, no filesystem writes, no
repository mutation anywhere in the module — confirmed via a
`monkeypatch`-forced `open()` failure across full plan+execute cycles
(`test_no_filesystem_network_side_effects`).

## 17. Delivery Policy

`DeliveryPolicy`: `policy_version`, `inline_size_threshold`,
`allow_attachment`, `allow_multipart`, `allow_overview_plus_attachment`.
`DEFAULT_POLICY` uses an 8000-byte inline threshold (comfortably
covering typical PCAE phase report sizes while still small enough to
exercise attachment/multipart fallback under a tightened test policy).
Policy never governs evidence inclusion — only packaging. Equivalent
request + adapter capabilities + policy always produce the identical
plan (`test_policy_determinism_same_plan`).

## 18. Delivery Plan

`DeliveryPlan`: logical delivery identity, adapter identity/version,
destination classification, selected mode, ordered units, policy
version, `content_preserved` (always `True` for any plan that exists —
`plan_delivery()` raises rather than returning a plan that fails this
check), diagnostics, and rendering traceability. Fully inspectable
before execution; contains no adapter secrets
(`test_plan_contains_no_secrets`,
`test_plan_contains_no_concrete_destination_secret`).

## 19. Delivery Execution

`execute_delivery(plan, *, authorized=None)`: verifies adapter
identity/version (via `get_adapter`), checks `always_disabled` first
(short-circuits to `DISABLED_BY_POLICY`), then checks external-delivery
authorization for adapters declaring `represents_external_delivery=True`
(reusing `pcae.core.notifications._external_delivery_authorized()` —
never a duplicated gate), executes units in the plan's own fixed order,
normalizes outcomes, and never mutates the plan or regenerates it.
`authorized` may be overridden only by tests exercising the
authorization boundary deterministically; ordinary calls consult the
real, governed gate.

## 20. Delivery Execution Result

`DeliveryExecutionResult`: logical delivery identity, adapter
identity/version, destination classification, selected mode, requested/
attempted/delivered/failed unit counts, per-unit outcomes, overall
outcome, `partial` indicator, retry recommendation, diagnostics,
rendering identity/digest, and policy version — an in-memory structure
explicitly shaped to be directly consumable by a future 134E.7 receipt
model (`test_execution_result_suitable_for_future_receipt_persistence`),
without itself persisting anything (`test_no_durable_receipt_
persistence_yet`).

## 21. Outcome Vocabulary

`DeliveryOutcome`: `delivered`, `failed`, `partially_delivered`,
`disabled_by_policy`, `blocked_by_authorization`, `invalid_plan`,
`unsupported`. `disabled`/`blocked`/partial are never conflated with
`delivered` — each has its own distinct branch in the outcome
computation, verified directly (`test_disabled_is_not_delivered`,
`test_blocked_by_authorization_result`,
`test_partial_is_not_delivered`).

## 22. Exactly-Once Logical Semantics and Retry

Retries never create a new logical delivery identity, never duplicate
logical completion, and never silently re-send content under a changed
rendering (Section 6). `plan_retry(plan, previous_result)` builds a
retry plan covering only previously-failed units, fails closed if
`previous_result` belongs to a different logical delivery, and fails
closed if there is nothing to retry. Successful units are never resent
by default (`test_successful_units_not_resent_by_default`). Durable
retry history remains 134E.7's concern; this phase's retry planning is
purely in-memory and stateless beyond the caller-supplied plan/result
pair.

## 23. Partial Delivery

`DeliveryExecutionResult.partial` is explicit and distinct from
`overall_outcome == DELIVERED`; `unit_outcomes` records exactly which
units succeeded/failed; `retry_recommendation` states whether retry is
sensible. A partial delivery is never represented as delivered
(`test_partial_is_not_delivered`, `test_partial_delivery_result`).

## 24. External Delivery Authorization

Reused directly from `pcae.core.notifications._external_delivery_
authorized()` — not reimplemented, not duplicated. Any adapter
declaring `represents_external_delivery=True` is gated by this exact
function at execution time; adapters not so declared (recording, null)
never consult it at all. Production notification configuration alone
(e.g. a bot token present in the environment) is insufficient without
`PCAE_NOTIFY_ENABLED` — independently re-confirmed by calling the real
function directly (`test_production_config_alone_insufficient_in_
test`). Future adapters inherit this protection automatically, purely
by declaring the capability flag — there is no alternate code path in
`execute_delivery()` that skips the check
(`test_future_adapter_inherits_isolation`,
`test_direct_external_adapter_cannot_bypass_gate`).

## 25. Automatic Configuration Resolution

The pipeline itself never reads adapter configuration directly — it
consults only the existing authorization gate; concrete adapter
configuration (tokens, destinations) is entirely the adapter
implementation's own concern, resolved through whatever neutral
boundary that adapter chooses to use. `delivery_pipeline.py` imports no
configuration-resolution module and contains no shell-sourcing logic
(`test_automatic_configuration_resolution_compatibility`,
`test_no_shell_source_dependency`).

## 26. Test Isolation

All 105 focused tests use the recording or null adapters, or a
locally-defined synthetic adapter with `represents_external_delivery`
explicitly set for authorization-boundary testing — no ordinary test
reaches any real external transport. Subprocess/cross-process tests
independently re-import the module fresh and confirm the recording
adapter remains the non-external default
(`test_subprocess_test_isolation`).

## 27. Non-Omission

Every `DeliveryPlan` reconstructs to exactly `request.rendered_content`
— sections, findings, repairs, uncertainty, limitations, disclosures,
provenance, repository/runtime state, next-phase blockers, and
traceability all travel inside that single content string, verbatim,
with no separate extraction or filtering step anywhere in this module.
Packaging constraints (segmentation, attachment) never override this —
`plan_delivery()` raises rather than ever producing an
incompletely-representing plan.

## 28. Non-Strengthening

The pipeline and adapter outcomes never change rendered meaning: no
code path in `delivery_pipeline.py` inspects or rewrites the content
string for status words; `DeliveryPlan` carries no `completeness` field
of its own that could diverge from the source `RenderingResult`'s
completeness (verified structurally,
`test_non_strengthening_incomplete_rendering_remains_incomplete`);
failed/partial/blocked outcomes are never reclassified as delivered.

## 29. Transport Independence

Core delivery planning contains no Slack/Teams/Discord/email/SMS/
Telegram-specific behavior — verified via an AST-based scan that strips
docstrings before checking for channel-name substrings (avoiding the
docstring-prose false-positive class 134E.2's own test suite first
documented) and a dedicated import-line scan confirming no Telegram
import (`test_transport_neutral_core`,
`test_no_telegram_specific_branch`). Adapters declare only generic
capability metadata (max inline bytes, attachment support, supported
modes/media types) — all channel-specific logic, if any, belongs
entirely inside a future adapter implementation, not this core module.

## 30. Package Boundaries

`delivery_pipeline.py` imports `pcae.core.rendering`
(`RenderingResult`) and `pcae.core.notifications`
(`_external_delivery_authorized`), plus stdlib
(`hashlib`, `json`, `dataclasses`, `enum`, `typing`). It does not
import the canonical evidence model, extraction layer, either derived
view, Repository Intelligence, or execution systems
(`test_no_evidence_or_view_imports_in_generic_core`). This phase
updated the pre-existing isolation scans in `test_rendering_134e5.py`
and `test_rendering_134e5v_verification.py` to admit
`delivery_pipeline.py` as the next expected, still-isolated consumer —
the identical, pre-declared narrowing pattern every prior 134E.x phase
already applied to its own predecessor's isolation tests.

## 31. Validation and Failure

Fail-closed for: invalid/empty `RenderingResult`, unsupported
media type, unknown adapter, "no complete delivery mode available",
content-preservation failure (defensive, structurally unreachable but
still checked), and an unsupported requested mode. Returns normally
(never raises) for ordinary execution outcomes — `disabled`, `blocked`,
`failed`, `partial`, and `delivered` are all inspectable results, never
hidden behind an exception.

## 32. Future Receipt Integration

`DeliveryExecutionResult` is deliberately shaped as the direct input to
a future 134E.7 durable External Delivery Receipt model — every field
a receipt would need (logical identity, adapter identity, outcome,
per-unit results, rendering traceability, retry recommendation) already
exists in-memory. This phase persists none of it.

## 33. Limitations

- **No Telegram compatibility adapter** — deferred; 134D was not found
  to explicitly assign it to this phase.
- **`overview_plus_attachment` is defined but never selected** — no
  governed overview-generating renderer exists yet; wiring one in is
  explicitly out of scope for composing new summaries inside this
  module.
- **Retry planning is stateless** — it operates only on a caller-
  supplied `(plan, previous_result)` pair; durable retry history and
  automatic scheduling belong to 134E.7.
- **No durable receipt persistence** — `DeliveryExecutionResult` is
  in-memory only, by design.

## 34. Explicit Statement: Pipeline Remains Inactive

No delivery plan or execution result produced by this module is
consulted by `pcae phase complete`, current report promotion, or any
currently active notification path. Confirmed by a fresh full-tree
source scan finding zero references to `pcae.core.delivery_pipeline`
outside its own module and test files.

## 35. Test Results

- New focused suite: 105 passed (all 105 required areas).
- Combined regression suite (evidence model, extraction, both view
  compositions, rendering, phase-identity repair, phase_reports,
  finalization-gate, notification/Telegram, 134B.1-134B.3, phase,
  delivery pipeline): 1436 passed.
- Fast-green: 4390 passed, 0 failed this run.
- `compileall`: passed.

## 36. Governance Results

- `pcae_health`: healthy.
- `pcae_check`: passed.
- `pcae_doctor_task_memory`: clean.
- `pcae_push_check`: clean.
- `telegram_runtime`: configured and enabled for governed production
  finalization, resolved automatically without shell sourcing.
- `pcae_runtime_inspect`: Observed, observe, execution unavailable.

## 37. No-Go Confirmation

No activation of Canonical Engineering Evidence, no live evidence
capture, no replacement of current report generation, no replacement
of current notification dispatch, no routing of production Telegram
through the new pipeline, no durable External Delivery Receipt model,
no Architecture Status repair, no final lifecycle integration, no
PFN-001/PFR-001 change, no Repository Intelligence change, no 134E.6V
work, and no execution capability were implemented. No raw git
commit/push, `--no-verify`, or force push was used.

## 38. Readiness Assessment

Delivery Pipeline Generalization is implemented, self-tested (105
focused tests covering request/identity/purpose/destination, adapter
registry, all delivery modes, segmentation, execution, retry, partial
delivery, authorization, transport independence, and validation/
failure), and integrated into the existing regression posture (1436
combined tests passing; fast-green 4390/4390). It remains fully
isolated from active lifecycle authority. **It has not been
independently verified by a dedicated adversarial verification phase**
— that is 134E.6V's job, not this phase's own self-certification.

Recommended next phase: **134E.6V — Delivery Pipeline Generalization
Independent Verification.**
