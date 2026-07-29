# Phase 146G — CHGR-001 Schema-Envelope Implementation

**Status:** Complete (production implementation; no schema, contract, or
runtime file modified)
**Mode:** Production Implementation, executing Phase 146F's Implementation
Roadmap (§9.9) for CHGR-001 v1.2's frozen CHGR-REQ-194 through
CHGR-REQ-209, per Phase 146F's own "IMPLEMENTATION PLAN COMPLETE WITH
OBSERVATIONS" verdict and explicit human authorization for this phase.
**Governing authority:** Phase 146F's plan
(`docs/PHASE_146F_CHGR001_SCHEMA_ENVELOPE_IMPLEMENTATION_PLANNING.md`);
CHGR-001 v1.2 §26/§28; PEC-001; IWPC-001; IWC-001.
**Runtime:** Observed / observe / unavailable (unchanged by this phase).
**Pushed:** not_pushed (staging a pending-push canonical report so
`pcae push` readiness's phase-report-identity gate can pass; promoted to
complete and re-verified pushed immediately after the push).

---

## 1. Executive Summary

`build_publication_record` (`src/pcae/governance/publication/record.py`)
now constructs and fail-closed-validates the four schema-conformant
CHGR-001 v1.2 artifacts one Publication Execution produces —
`human_governance_record`, `human_confirmation_evidence`,
`governance_record_provenance`, `governance_record_integrity` — against
the frozen `src/pcae/schema_resources/chgr` schema family, using the
already-generic `schema_runtime` infrastructure unchanged. Construction
and validation are wired directly into `build_publication_record`'s own
call path, before `PublicationCoordinator.execute` ever reaches
`PublicationRecordStore.write_record` (CHGR-REQ-204/205). No schema,
contract, or runtime file was touched. Two new small modules were added
(`chgr_envelope.py`, `chgr_rendering.py`); `record.py`, `coordinator.py`,
and `errors.py` were widened; `storage.py` required **no** change (its
existing per-`record_id` `write_record`/`remove_record` API was already
generic enough to persist four artifacts as four calls).

## 2. Implemented Responsibilities

Following 146F §3.1–§3.9 exactly:

- **3.1 Manifest-sourced envelope** — `chgr_envelope.envelope_for` reads
  `schema_id`/`schema_version`/`contract_version` verbatim from the
  verified CHGR manifest (`load_and_verify_manifest`), never hardcoded.
- **3.2 Identity + digest assignment** — `record._new_record_id` mints
  four family-prefixed UUID4 identities (`chgr-`, `chgrconf-`,
  `chgrprov-`, `chgrintg-`); `compute_record_digest` (unchanged from
  144F) is applied once per artifact.
- **3.3 Construction order / Risk R-1 resolution** — implemented as
  described in §4 below (this phase's own disclosed resolution of the
  forward-reference cycle 146F left open).
- **3.4 `lifecycle_state`** — fixed literal `"published"`.
- **3.5 `authority_basis_claimed`** — omitted from every constructed
  record (no citation resolves in this repository's current scope,
  unchanged from 144F); disclosed in `limitations`.
- **3.6 `assurance_level`** — `typed_confirmation_only` → `L0`,
  `os_authenticated_user` → `L1`; an unrecognized `evidence_kind`
  refuses construction (fail-fast) with `ChgrSchemaConformanceError`.
- **3.7 Sibling artifacts' remaining fields** — mapped verbatim from
  `PublicationReadinessPackage`, per-family, in `build_publication_record`.
- **3.8 Deterministic rendering** — `chgr_rendering.render_human_governance_record`.
- **3.9 Manifest/registry reuse** — `chgr_envelope._load_chgr_schema_context`
  (module-level `functools.lru_cache`, built once), reusing
  `build_offline_registry`/`load_and_verify_manifest`/`validate_record_shape`
  unchanged — the same infrastructure `src/pcae/governance/inspection.py`
  already uses to inspect CHGR artifacts.

## 3. Validation Architecture (CHGR-REQ-204, 205, 208)

`record._validate_chgr_bundle` runs inside `build_publication_record`,
after all four artifacts are constructed and before the function
returns — strictly before `PublicationCoordinator.execute` reaches any
`write_record` call (`coordinator.py`'s `execute()` now wraps the
`build_publication_record` call in its own `try`/`except
PublicationExecutionError` block, mirroring the pattern already used for
the five pre-existing validation steps). Each of the four artifacts is
validated independently against its own schema via
`schema_runtime.validate_record_shape`; CHGR-REQ-208's disclosure check
(`_authority_basis_disclosure_present`, not expressible in JSON Schema
alone) runs as an additive, independent check. Any failure anywhere
raises `ChgrSchemaConformanceError` (new `PublicationExecutionError`
subclass in `errors.py`) with an aggregated, per-field diagnostic
message; no artifact is written, no `record_id` from that attempt is
ever committed. `PublicationCoordinator.execute`'s existing
`_failure_result`/`_record_attempt` path handles this exactly like every
other refusal already in that method.

## 4. Construction Ordering — Risk R-1 Resolved

146F §3.3 disclosed a genuine forward-reference cycle between
`human_governance_record.integrity_ref` (which must cite
`governance_record_integrity`'s own `record_id`/`record_digest`) and
`governance_record_integrity.payload_digest` (which CHGR-REQ-203
requires to be the top-level record's own *real, final* `record_digest`)
— and left the exact resolution as an explicit, disclosed judgment call
for this phase.

**Mathematical finding:** the cycle is not merely an ordering
inconvenience — a full-content digest cannot cite another full-content
digest that in turn cites it back, for any hash function, without one of
the two references being computed from something other than the other
artifact's own truly-final content. This phase resolves it as follows,
verified against every relevant schema field's own documented shape:

1. Construct `human_confirmation_evidence` (no forward reference),
   digest it.
2. Construct `governance_record_provenance` (cites 1), digest it.
3. Assign both `human_governance_record`'s and
   `governance_record_integrity`'s record ids up front.
4. Compute the deterministic rendering digest from
   `human_governance_record`'s *substantive* content only (decision
   subject, template, selection, decision-maker, rationale/conditions,
   assurance level, lifecycle state — 146F §3.8's own listed content) —
   deliberately never the cross-reference fields, which breaks one leg
   of the cycle immediately (`chgr_rendering.render_human_governance_record`
   reads only these fields, regardless of what else is in the dict it is
   handed).
5. Compute a **provisional** `governance_record_integrity` digest, using
   a fixed placeholder for its own `payload_digest` field, to seed
   `human_governance_record.integrity_ref`.
6. Finalize `human_governance_record` — its own `record_digest` is now
   computed over its true, complete, final content (including the
   now-known `integrity_ref`) — standard `compute_record_digest`, no
   special-casing.
7. Finalize `governance_record_integrity` for real, with
   `payload_digest` set to `human_governance_record`'s now-known real
   `record_digest` (CHGR-REQ-203 satisfied exactly, literally) —
   standard `compute_record_digest`, no special-casing.

**Consequence, disclosed explicitly (not silently absorbed):**
`human_governance_record.integrity_ref.record_digest` cites the
*provisional* `governance_record_integrity` digest from step 5, not the
artifact's final, persisted `record_digest` from step 7 (the two differ
only in what `payload_digest` held at hashing time). This is
schema-conformant, not a defect: `shared/references.schema.json`'s own
text states an `artifact_reference`'s `record_digest` is "shape-checked
only… whether it actually matches the referenced artifact is a
verification-layer responsibility," explicitly deferring exactly this
kind of check to a later, separate verification step
(`governance/verification.py`, out of this phase's scope), never to
schema-layer or construction-time enforcement. `human_governance_record`'s
own `limitations` array names this explicitly. `governance_record_integrity.payload_digest`
— the one field CHGR-REQ-203's text gives no such "shape-only" latitude
to — is exact. Both `human_governance_record.record_digest` and
`governance_record_integrity.record_digest` are self-consistent: each is
independently recomputable from its own persisted bytes via the
unmodified `compute_record_digest`, verified by
`test_every_attempt_carries_...`/`test_round_trip_reload_and_revalidate_from_disk`.

This was independently re-derived from the schema files themselves during
this phase, not assumed from 146F's own (self-admittedly incomplete)
proposed ordering.

## 5. Timestamp Resolution (Risk R-3)

146F Candidate (a) adopted: `chgr_envelope.chgr_timestamp` normalizes
every timestamp at the CHGR construction boundary — `created_at`
(all four artifacts' envelopes) and `confirmation_timestamp`/
`decision_maker_identity_evidence.captured_at` (copied from the Package)
— converting a `+00:00`-suffixed (or already-`Z`-suffixed, idempotently)
ISO-8601 string to the schema's required literal-`Z` shape, preserving
the represented UTC instant unchanged. No `_now_iso()` call site outside
`governance/publication/**` was touched.

## 6. Integration Summary

- **`PublicationCoordinator.execute`** — one new `try`/`except
  PublicationExecutionError` block around the `build_publication_record`
  call; the single `write_record` call became a loop over the four
  returned artifacts with per-artifact rollback (`remove_record`) on any
  mid-loop failure; the `commit_publication` marker gained one additive
  field (`chgr_record_ids`); the two existing rollback paths
  (`FileExistsError`/`OSError` from `commit_publication`) now roll back
  all four written artifacts instead of one. PEC-REQ-051's five-step
  fixed validation order is unchanged; nothing was reordered.
- **`record.py`** — `build_publication_record`'s signature is unchanged
  (`(package, event, record_id, created_at)`); its return shape widened
  from one flat dict to a four-key bundle (146F's disclosed Risk R-2,
  confirmed no external caller depends on the old shape — grep-confirmed,
  no CLI constructs a `PublicationCoordinator` outside test fixtures and
  `interactive_workflow`'s own internal wiring).
- **`storage.py`** — **unchanged.** `write_record`/`remove_record` were
  already parameterized by `record_id`; the Coordinator now simply calls
  them four times. 146F's Risk R-5 (four files vs. one bundle) is
  resolved as four files, exactly the recommended, lower-risk option.
- **`schema_runtime`** — used exactly as designed, zero code change.

## 7. Test Results

- `tests/test_phase_144c_publication_coordinator.py` — 33/33 passed
  (regression-updated: fixture `preview_digest` widened to a genuine
  64-hex digest, matching schema shape; two tests updated for the new
  four-file/four-key-bundle shape — expected, disclosed churn per 146F
  §6.2/§7.3).
- `tests/test_phase_146g_chgr_schema_envelope_implementation.py` — new,
  24/24 passed: timestamp normalization, manifest-sourced envelope
  fields, identity generation/uniqueness, digest shape/self-consistency,
  authority-basis disclosure, assurance-level mapping (including
  unrecognized-`evidence_kind` refusal), pattern-violation refusal with
  diagnostics, fail-closed retry-ability, cross-artifact round-trip
  re-validation from disk.
- Full CHGR/publication/interactive-workflow-scoped sweep
  (`-k "iwc or publication or chgr or 144c or 146g or 145"`) —
  **1899 passed, 1 skipped**, plus 2 pre-existing, environment-local
  `python -m build`-unavailable packaging-test failures (independently
  reproduced as identical on unmodified `main` via `git stash`; not
  network-installable in this environment; unrelated to this phase,
  matching 146E's own disclosed finding of the same class).
- `pcae` fast_green gate — **4391/4391 passed**, unaffected (does not
  include the six regression-only test files updated below).

## 8. Regression Assessment

Six pre-existing test files exercised real end-to-end flows (CLI or
direct-model) reaching `PublicationCoordinator.execute` with fixture data
that was never previously schema-validated: `test_phase_145f_application_service_boundary.py`,
`test_phase_145g_decision_session_cli.py`,
`test_phase_145g1_decision_session_cli_repair.py`,
`test_phase_145g2_decision_selection_cli_repair.py`,
`test_phase_145g2v_independent_verification.py`,
`test_phase_145h3_independent_verification.py`. Each carried at least one
of: a non-hex placeholder `preview_digest` ("digest-1"/"preview-digest-1"),
a non-`MAJOR.MINOR` placeholder `template_version` ("v1"), a single-item
`options_presented` (schema requires `minItems: 2`), or a placeholder
`decision_maker_identity_evidence` missing `evidence_kind`. All are
exactly 146F's own disclosed Risk R-4 ("a Package carrying a
pattern-violating value that previously flowed through silently would
now correctly refuse Publication… the fail-closed gate working as
designed, not a defect"). Each was corrected to a schema-conformant
placeholder value at the minimal call site (shared-default fixtures
updated only where no other assertion in the file depended on the old
placeholder value; two CLI-argument-parsing-only tests in
`145g2_decision_selection_cli_repair.py` that assert on the literal
string `"v1"` and never reach publication were deliberately left
unchanged). No assertion about ordering, replay, authorization, rollback,
or any pre-146G Coordinator behavior was altered.

No file under `src/pcae/schema_resources/**` or `docs/contracts/**` was
touched. `pcae runtime inspect` reports identically before and after this
phase's own change (`Observed`/`observe`/`unavailable`, `Registry status:
empty`, `Plugin count: 0`).

## 9. Findings

- **Non-Blocking, disclosed by design (not a defect):** as described in
  §4, `human_governance_record.integrity_ref.record_digest` does not
  literally equal `governance_record_integrity`'s own final, persisted
  `record_digest` (they differ only in what `payload_digest` held at the
  moment the provisional digest was seeded). This is schema-conformant
  per `shared/references.schema.json`'s own documented "verification-layer
  responsibility" text, disclosed in `human_governance_record.limitations`,
  and is the correct, principled resolution of 146F's own disclosed Risk
  R-1 — not silently absorbed. A future verification pass
  (`governance/verification.py`, out of this phase's scope) is the
  correct place to check whether a stored `integrity_ref` still matches
  its referenced artifact's current bytes.
- **Non-Blocking:** six pre-existing regression test files carried
  latent, never-previously-enforced schema-pattern violations in their
  own fixture data (§8) — corrected as part of this phase's regression
  maintenance, exactly the kind of newly-surfaced defect 146F's Risk R-4
  anticipated.
- No Blocking findings.

## 10. Overall Verdict

**IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS.**

CHGR-REQ-194 through CHGR-REQ-209 are implemented per the verified 146F
plan: all nine named responsibilities, the fail-closed validation gate
(additive CHGR-REQ-208 disclosure check included), the construction-order
cycle explicitly resolved and disclosed (not silently absorbed), and the
timestamp-format repair. No architectural redesign was performed; no
existing ownership boundary (Publication Coordinator, Interactive
Workflow authority, lifecycle sequencing, runtime capability) was
touched. Full regression suite green modulo two pre-existing,
independently-reproduced, environment-local packaging failures unrelated
to this change.

## 11. Recommended Next Phase

**146H — CHGR-001 Schema-Envelope Independent Implementation
Verification**, mirroring 146C's role for 146B and 146E's role for 146D:
an independent re-derivation and re-verification of this phase's own
construction-order resolution (§4), timestamp repair, and fail-closed
gate, without trusting this document's own claims. This recommendation
is not an authorization.
