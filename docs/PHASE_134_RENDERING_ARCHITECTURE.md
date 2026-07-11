# Phase 134E.5 — Rendering Architecture

## 1. Objective

Implement a deterministic, reusable, transport-independent Rendering
layer for the verified structured derived views (134E.3's Phase Report
View, 134E.4's Operator Report View). Rendering transforms these views
into presentation formats — Markdown, plain text, canonical JSON —
without changing evidence meaning: it never selects evidence, composes
new evidence, summarizes independently, infers missing facts,
strengthens conclusions, silently omits material content, decides
delivery strategy, or knows about any communication channel.

## 2. Architectural Position

```
Canonical Engineering Evidence
        |
        v
Evidence Extraction
        |
        v
Derived Evidence View Composition (134E.3, 134E.4)
        |
        v
Rendering                             <- this phase
        |
        v
Delivery Pipeline                     (134E.6, not implemented)
        |
        v
Delivery Adapters                     (not implemented)
```

Rendering consumes a verified structured view; it does not consume
Canonical Engineering Evidence directly, does not invoke Evidence
Extraction, does not recompose a view, does not inspect delivery
configuration, and does not know the destination channel.

## 3. Authority Boundary

Canonical Engineering Evidence remains the only future authoritative
engineering record; structured views remain derivative; rendered
output is a **presentation artifact only**. It never becomes canonical
evidence authority, independent report authority, phase identity
authority, finalization authority, notification authority, delivery
receipt authority, or repository-state authority. The active report
and notification lifecycle remains completely unchanged — confirmed by
fresh full-tree source scans finding zero references to
`pcae.core.rendering` anywhere outside its own module and test files.

## 4. Renderer Responsibilities

The renderer maps structured sections into a presentation format,
applies headings/labels/deterministic spacing/escaping, preserves
stable ordering, represents applicability/completeness/findings/
repairs/uncertainty/limitations/disclosures, and emits rendering
diagnostics. It never selects or removes engineering facts, decides
what is important, reorders evidence by channel preference, collapses
findings/repair history, converts limitations into ordinary notes,
infers summaries, derives next-phase recommendations, or suppresses
incomplete/invalid states.

## 5. Renderer Input Contract

`render(view, source, renderer_id)` is the sole entry point. It
validates: exact view type (via `isinstance`); the renderer's declared
`accepted_view_types`; that `source.source_evidence_id` matches
`view.source_evidence_id`; that `source.compute_digest()` matches
`view.source_extraction_digest` (the forged-input guard); view
completeness (rejects `INVALID`); decision completeness for Operator
Reports (rejects `INVALID`); exact section inventory and order (against
the frozen `PFR_SECTION_ORDER`/`OPERATOR_SECTION_ORDER` tuples); and
duplicate section identity. A missing source identity/digest, wrong
view type, forged/mismatched source, or invalid section
inventory/order all fail closed with a `ValueError`.

**Design decision — why `render()` takes both `view` and `source`**:
134E.3/134E.4 deliberately designed their section models as
*references* (category name, requirement level, applicability, finding
classifications) rather than copies of canonical content, to avoid
unnecessary duplication — independently confirmed correct, not a
defect, by 134E.3V/134E.4V. A renderer consuming only the view
therefore cannot reproduce actual field content (objective text,
finding descriptions, governance status strings). To produce
genuinely content-rich output while remaining fail-closed against
forged input, `render()` accepts the originating `ExtractionResult` as
a second argument and verifies it against the view's own recorded
digest before using it purely as a value-resolution source — no
category-to-section assignment, completeness computation, or
profile-rule evaluation runs; this is not "recomposing a view."

## 6. Renderer Registry

`_RENDERER_REGISTRY: dict[str, RendererDescriptor]` — a small explicit
dict, not a plugin framework, mirroring `evidence_extraction.py`'s own
`_PROFILE_REGISTRY` convention exactly. `register_renderer()` is
fail-closed against silent overwrite (a differing re-registration under
an existing `renderer_id` raises; an identical re-registration is a
harmless no-op). `RendererDescriptor` carries `renderer_id`,
`renderer_version`, `accepted_view_types`, `media_type`, and a
deterministic `render_fn`. Six renderers are registered at module load:

| Renderer ID | View type | Media type |
|---|---|---|
| `phase_report_markdown_v1` | Phase Report View | `text/markdown` |
| `phase_report_plain_text_v1` | Phase Report View | `text/plain` |
| `phase_report_json_v1` | Phase Report View | `application/json` |
| `operator_report_markdown_v1` | Operator Report View | `text/markdown` |
| `operator_report_plain_text_v1` | Operator Report View | `text/plain` |
| `operator_report_json_v1` | Operator Report View | `application/json` |

Registration order has no effect on output (each renderer's own
behavior is fixed at construction time); future renderers can be added
without modifying either view model.

## 7. Supported Formats

**Markdown** — required for canonical stored reports, operator-readable
reports, future attached documents, GitHub-friendly output.
**Plain text** — required for terminal display, restricted channels,
diagnostics, fallback presentation; preserves the identical evidence
content as Markdown, only formatting differs. **Canonical JSON** —
required for deterministic structured interchange, future delivery
adapters, audit/validation, round-trip verification; wraps the view's
own `to_dict()` output plus a `resolved_sections` array (primary
category values resolved from `source`) and renderer metadata, rather
than inventing a second canonical representation.

**HTML was not implemented.** No current implementation plan or
repository convention directly justifies it in this phase — the three
formats above already cover every named consumer (stored reports,
terminal/diagnostics, structured interchange); HTML remains available
to a future phase if a concrete consumer emerges.

## 8. Phase Report Rendering

All thirteen PFR-001 sections render in exact order (`PFR_SECTION_
ORDER`). Every section is visible regardless of applicability
(`materially_populated`, `not_applicable`, `unavailable_with_
disclosure`, `incomplete`, `invalid`) — none are silently hidden.
Findings preserve their exact classifications; repairs preserve both
original and post-repair classification; warnings/failures render
verbatim; uncertainty/limitations/filtering disclosures render
prominently at both per-section and report-level scope; provenance
categories remain listed; report completeness renders exactly as
composed.

## 9. Operator Report Rendering

All twelve verified Operator Report sections render in their fixed
order (`OPERATOR_SECTION_ORDER`). Output is mobile-readable (compact
per-line structure) yet rich in engineering detail (full resolved
values, not just category names) — mobile-readable never means
minimal, and no material content is truncated. Outcome, key
decisions/changes, defects/repairs, unresolved findings, technical
debt, architectural significance, boundaries, tests/governance,
repository/runtime state, next-phase readiness, notable knowledge, and
uncertainty/limitations are all prominently and separately surfaced,
one section each.

## 10. Content Preservation

Each render function returns the set of primary categories it
successfully resolved a value for. `render()` compares this against
every `is_primary=True` category the view itself declares
(`_required_primary_categories(view)`); any gap produces a `blocking`
`content_preservation_failure` diagnostic and downgrades rendering
completeness. **A category is counted as preserved only once its
concrete value has actually been resolved and written** — a bare
category-name label with no resolvable value never satisfies
preservation (a genuine gap found and fixed during this phase's own
development, before any test asserted the wrong behavior: see Section
20). This accounting is bookkeeping, not heuristic content selection —
every render function already knows exactly which categories it wrote.

## 11. Non-Omission

No renderer silently omits material view content. If a format cannot
represent an element natively (none of the three implemented formats
currently hits this case, since all three can represent every field
type the view models carry), the contract requires: a deterministic
fallback representation, a disclosed representation limitation, full
content preservation, and a rendering-completeness downgrade if
required. The content-preservation mechanism (Section 10) is the
enforcement point.

## 12. Non-Strengthening

Rendering preserves exact structured meaning. `_stringify_value()`
performs a lossless textual projection of already-known structured
types (dataclass `to_dict()`, tuples, plain strings) — it never
substitutes, merges, or reinterprets a classification, status, or
completeness value. Verified directly: BLOCKING/NON_BLOCKING
classifications, `"warning"`/`"failed"` status strings, `not_pushed`/
dirty-repository state, and `"blocked pending resolution"`-style
next-phase text all survive rendering byte-for-byte in their
structured form.

## 13. Rendering Completeness

`RenderingCompleteness` (COMPLETE / COMPLETE_WITH_LIMITATIONS /
INCOMPLETE / INVALID) is computed as a floor derived from the source
view's own `completeness` (never upgraded — `_worse()` is a pure
total-order comparison, the identical convention 134E.3/134E.4
established), further downgraded by `_worse()` if content preservation
fails. For Operator Report rendering, the floor additionally accounts
for `view.decision_completeness` — rendering completeness can never
exceed either dimension.

## 14. Escaping and Safety

`_escape_markdown()` escapes Markdown metacharacters
(`` \`*_{}[]()#+-.!|>~ ``) and neutralizes embedded triple-backtick
sequences (zero-width-joining the backtick run) so embedded content
cannot terminate the outer document structure — content remains fully
present, only its fence-breaking capability is disabled.
`_escape_plain_text()` replaces ASCII control characters (except
newline/tab) with a visible `\xNN` escape so no content silently
disappears from terminal/log display; newlines are preserved verbatim
so multiline evidence remains multiline. Neither escaping function
truncates or judges content — verified against Unicode, long strings,
multiline text, and metacharacter-heavy strings.

## 15. Secret Exclusion

Secret rejection belongs entirely upstream: `CanonicalEngineeringEvidence.
validate()` already rejects secret-shaped free-text content
(`_contains_likely_secret()`, Telegram-token- and `PCAE_*_TOKEN`-shaped
patterns) at finalization time, before a view can even be composed.
Rendering implements **no additional broad secret scanner** — adding
one here would duplicate an existing, already-governed control and
risk drifting out of sync with it. Confirmed directly: a record
containing a Telegram-bot-token-shaped string cannot even be
constructed via `_minimal_complete_evidence()`.

## 16. Stable Ordering

Rendering never reprioritizes sections, reorders findings/tests/
commits/uncertainty/limitations/disclosures differently by format, or
depends on dictionary/registration order. Section order is always the
view's own frozen tuple; item order within a section is always the
view's own `evidence_groups` tuple order (already fixed at composition
time). Equivalent views render byte-identically for the same renderer/
version, verified in-process and across a fresh subprocess.

## 17. No Channel-Specific Behavior

The renderer contains no knowledge of Telegram, Slack, Teams, Discord,
email, SMS, push payload limits, retries, delivery destinations, or
delivery receipts — confirmed by source-line import scans and a
textual scan for channel-name tokens across the Markdown render
functions. Channel-specific adaptation is explicitly deferred to
134E.6.

## 18. No Delivery Splitting

No message chunking, attachment decisions, or channel-limit
segmentation is implemented — confirmed by source-text scans for
`chunk`/`split_message`/`message_limit`/`attachment` tokens, none
found. A renderer produces exactly one complete presentation artifact;
future delivery logic may split or attach that artifact while
preserving its identity and completeness, but that logic does not
exist in this module.

## 19. Traceability

Every `RenderingResult` carries `source_view_id`, `source_view_
version`, `source_view_digest`, `source_evidence_id`, `source_record_
digest`, `profile_id`, `profile_version`, `renderer_id`, and
`renderer_version` as structured metadata fields — available regardless
of format. Markdown/plain-text renderers additionally embed a visible
traceability footer (`source evidence`, `extraction profile`, `view
id`, `view digest`) directly in the rendered content itself, so
traceability survives even if only the raw text is later consumed
without its metadata wrapper.

## 20. Self-Found and Repaired Defect (during this phase's own
development, before any test was written)

**Content-preservation accounting counted an unresolved primary
category as "preserved."** The original render implementations
recorded a category as content-preserved (`rendered_categories.add(...)`)
immediately upon encountering a primary `EvidenceGroupRef`, before
checking whether the corresponding value could actually be resolved
from `source`. A category whose value could not be resolved (e.g. a
source/view mismatch scenario) would still be marked "preserved" merely
because its *label* was printed — silently defeating the entire
purpose of the accounting mechanism. Found via direct construction of
a source with a category removed, before any regression test asserted
the (wrong) behavior. Fixed in all three affected render functions
(Markdown, Phase Report JSON, Operator Report JSON) by moving the
`rendered_categories.add(...)` call inside the `if item is not None:`
branch, so only genuinely resolved values count. Regression:
`test_missing_content_detected`.

## 21. Determinism

Verified across: repeated in-process rendering (byte-identical output
and digest); a fresh subprocess re-derivation
(`test_cross_process_determinism`); newline stability (no `\r`
anywhere); and zero dependency on agent/model identity, transport, or
environment configuration — `render()`'s signature has exactly three
parameters (`view`, `source`, `renderer_id`), none of which admit such
state. No current timestamp is ever injected (confirmed by regex scan
for ISO-8601 datetime patterns in rendered output).

## 22. Validation and Failure

Fail-closed for: unsupported renderer, wrong view type, forged/
mismatched source (evidence ID or digest), missing source identity/
digest, invalid (INVALID-completeness) view, invalid section
order/inventory, and empty successful render. Content-preservation
failure and completeness are surfaced as inspectable diagnostics plus
a downgraded `RenderingCompleteness`, never as a silent pass — matching
the identical fail-closed-vs-inspectable-diagnostic split 134E.1-134E.4
established.

## 23. Package Boundaries

`pcae.core.rendering` imports `pcae.core.phase_report_view`,
`pcae.core.operator_report_view`, and
`pcae.core.evidence_extraction` (`ExtractionResult`,
`SelectedEvidenceItem`), plus stdlib (`hashlib`, `json`, `re`,
`dataclasses`, `enum`, `typing`). It does not import notification
dispatch, delivery adapters, Telegram, external configuration,
filesystem, network, Repository Intelligence, or execution systems.
Verified by dedicated source-scan tests and a fresh full-tree scan
confirming zero other files in `src/` reference `pcae.core.rendering`.
This phase also updated the pre-existing isolation scans in
`test_evidence_extraction_134e2v_verification.py`,
`test_phase_report_view_134e3.py`,
`test_phase_report_view_134e3v_verification.py`, and
`test_operator_report_view_134e4.py` to admit `rendering.py` as the
next expected, still-isolated consumer — the identical, pre-declared
narrowing pattern 134E.3 and 134E.4 each already applied to their own
predecessors' isolation tests.

## 24. Lifecycle Inactivity

Rendering is not invoked by current canonical report generation,
current Telegram payload construction, or phase finalization; it does
not write rendered artifacts into current latest-report paths; it is
not invoked from notification code; and no CLI integration was added.
All testing uses isolated model/view fixtures constructed directly in
tests — no filesystem or network access anywhere in the module,
confirmed by a `monkeypatch`-forced `open()` failure test.

## 25. Limitations

- **HTML is not implemented** (Section 7) — deferred until a concrete
  consumer justifies it.
- **No dedicated renderer-version-mismatch parameter exists** on
  `render()` — renderer version is fixed at registration time; a
  future phase could add explicit version pinning if a caller needs to
  target a specific historical renderer version.
- **Rendering cannot represent content a format genuinely cannot hold**
  — not currently reachable (all three formats can represent every
  field type the view models carry), but the Non-Omission fallback
  contract (Section 11) exists for if this changes.
- **No delivery integration** — this phase is presentation-only; 134E.6
  must implement the delivery pipeline and channel-specific adapters
  that consume `RenderingResult.rendered_content`/`media_type`.

## 26. Future Delivery Integration

A future 134E.6 Delivery Pipeline can consume `RenderingResult` output
directly: `rendered_content` (the complete presentation artifact),
`media_type` (to select a compatible delivery channel), and the full
traceability metadata (to construct delivery receipts referencing the
exact source evidence/view/renderer). Delivery may split, attach, or
otherwise adapt the artifact for a specific channel while preserving
its identity and completeness — none of that logic exists in this
module by design.

## 27. Explicit Statement: Rendering Remains Inactive and
Delivery-Independent

No rendered artifact produced by this module is written to any file,
delivered to any notification sink, or consulted by any currently
active PCAE governance path. Confirmed by fresh full-tree source scans
across all consumers this and prior phases established
(`test_no_consumer_references_rendering_yet`,
`test_current_report_generation_remains_unchanged`,
`test_current_notification_behavior_remains_unchanged`).

## 28. Test Results

- New focused suite: 97 passed (all 96 required areas).
- Combined regression suite (evidence model, extraction, Phase Report
  View, Operator Report View, phase-identity repair, phase_reports,
  finalization-gate, trust-hard-fail, certification-idempotency,
  134B.1-134B.3, phase, rendering): 1222 passed.
- Fast-green: 4390 passed, 0 failed this run.
- `compileall`: passed.

## 29. Governance Results

- `pcae_health`: healthy.
- `pcae_check`: passed.
- `pcae_doctor_task_memory`: clean.
- `pcae_push_check`: clean.
- `telegram_runtime`: configured and enabled for governed production
  finalization, resolved automatically without shell sourcing.
- `pcae_runtime_inspect`: Observed, observe, execution unavailable.

## 30. No-Go Confirmation

No activation of Canonical Engineering Evidence, no live evidence
capture, no replacement of current report generation, no change to
current notification payloads, no delivery adapters, no Telegram-
specific formatting, no message splitting, no attachment policy, no
External Delivery Receipts, no Architecture Status repair, no final
lifecycle integration, no PFN-001/PFR-001 change, no Repository
Intelligence change, no 134E.5V work, and no execution capability were
implemented. No raw git commit/push, `--no-verify`, or force push was
used.

## 31. Readiness Assessment

Rendering Architecture is implemented, self-tested (97 focused tests
covering registry, all six format/view-type combinations, content
preservation, Non-Omission, Non-Strengthening, escaping, determinism,
and validation/failure), and integrated into the existing regression
posture (1222 combined tests passing; fast-green 4390/4390). It remains
fully isolated from active lifecycle authority. **It has not been
independently verified by a dedicated adversarial verification phase**
— that is 134E.5V's job, not this phase's own self-certification.

Recommended next phase: **134E.5V — Rendering Architecture Independent
Verification.**
