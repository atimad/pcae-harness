# Phase 136U Complete — Notification/Marker/Receipt Authority Binding Schema Independent Verification

## Phase identity

- Phase ID: `136U`
- Status: completed
- Classification: independent verification (Stage 3 Companion Executable Schema, contract Group 10: `NotificationAuthorityBinding`, `MarkerAuthorityBinding`, `FinalizationReceiptAuthorityBinding`)
- Report completeness: complete

## Scope

Independently re-derive, and attempt to falsify, every material claim made
by Phase 136T about Implementation Group 10. Do not trust 136T's own tests,
prose, field interpretation, graph analysis, fixtures, or finding
dispositions. Bounded to independent verification only; no Group 11+
implementation.

## Summary

Independently re-derived §9, §16, §31, §32, §33, and §46 directly from the
frozen contract text (not from 136T's own summary). Confirmed Group 9's
schema-less exclusion (§46's own text assigns zero schema files to it).
Confirmed the exact Group 10 inventory
(`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, no extras, no early Group 11
resource). Confirmed Group 10's prerequisites are Group 1
(manifest-declared) plus Group 2/PFN-001 (conceptual vocabulary only, never
a manifest `$ref`) — not the full 1-9 conceptual chain.

Recomputed all 21 manifest `file_digest` values byte-for-byte against
actual file bytes on disk: zero mismatches. Confirmed the registry's 22
resources are exactly the 21 manifest entries plus `manifest.schema.json`
itself (architecturally expected, not an unexplained gap).

Reconstructed and adversarially attacked all three field tables (§31/32/33)
field-by-field, including every conditional branch: notification
`delivery_state`'s three branches (`not_dispatched`/`already_dispatched`/
`payload_conflict`), marker `duplicate_of`'s `state == "conflict"`
condition, and the receipt schema's finalized-state bundle. Independently
re-derived — not merely restated — that §16's explicit `if`/`then` governs
over §33's summary "yes" column for the receipt schema's
`marker_reference`/`publication_evidence_reference` fields, the same
specific-table-over-summary-text resolution rule already established by
136N/136P precedent. Independently re-assessed and confirmed all six of
136T's disclosed discrepancies (`NON-BLOCKING-136T-1` through `-6`) and one
deferred gap (`DEFERRED-136T-1`, `staleness_check`).

Confirmed `authority_role: "authoritative"` is locally forbidden on all
three schemas, with no case-variant, `is_authoritative`-forcing, or
`_extensions`-smuggling bypass found. Confirmed the Tier 2 `_extensions`
boundary on all three schemas (nested structure, non-string values, wrong
key names, and scalar/null `_extensions` all rejected). Rebuilt four
independent graphs ($ref/manifest dependency, record identity, record
digest, sibling independence) from scratch across all 21 Group 1–10
resources: acyclic, no Group 10 sibling cycle, all three siblings
independently creatable with no forced ordering. Confirmed
atomic-completeness detection at the manifest layer (a partial Group 10
manifest fails `ManifestIntegrityError`).

Built a fresh wheel and sdist, installed into an isolated venv created
outside the repository checkout, and exercised offline validation
(registry construction, manifest verification, valid/invalid records for
all three families) with `socket.socket`/`socket.create_connection`
monkeypatched to raise — zero network calls, both in-repo and from the
isolated install. Confirmed via `git grep` that zero runtime source files
outside `schema_resources/` reference any Group 10 family, and that no
dispatcher/marker-writer/receipt-writer/authority-resolver module exists at
any plausible path.

**Found and repaired one genuine, reproducible Blocking defect
(`BLOCKING-136U-1`).** `tests/test_cltr_cutover_136n_authorization_and_candidate.py`
and `tests/test_cltr_cutover_136r_recovery_schema.py` each carried a
separately hardcoded `forbidden_stems` guard-test tuple that 136T's own
Group 10 migration correctly updated in `LATER_GROUP_RECORD_FILES` but
missed in this second, independent copy — the two lists silently
desynchronized within 136T's own commit. This caused both guard tests to
fail deterministically (confirmed single-threaded, not a parallel-execution
race, reproducing every run) against 136T's own final, unmodified-since
tree — directly contradicting 136T's own claimed "1609/1609" combined-suite
baseline. Repaired by deriving both `forbidden_stems` tuples from
`LATER_GROUP_RECORD_FILES` directly, structurally preventing this class of
desync from recurring for any future group. No production schema,
manifest, or shared-definition file was touched by the repair.

## Evidence and validation

- Independent focused test suite (freshly authored, no import of 136T's
  helpers): 155 passed, 0 failed, 1 skipped
  (`tests/test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py`).
- Combined Groups 1-10 + `schema_runtime` + 136U suite: 1764 passed, 0
  failed, 1 skipped post-repair (1762 passed, 2 failed pre-repair).
- Fast Green: 4391 passed, matching 136T's own count exactly, zero
  regressions.
- Full unmarked suite, fresh run on the clean, fully-committed post-repair
  tree: 21820 passed, 22 failed, 1 skipped. Zero of the 22 failures touch
  `cltr_cutover`/`schema_runtime`/manifest/packaging (grep-confirmed). 21
  exactly match 136T's own previously-disclosed baseline categories; 1
  additional node (`test_risk_register.py::test_risk_register_no_repository_files_created`)
  independently re-run in isolation and passed 1/1 — the same
  pre-existing parallel-execution git-status race category
  (`NON-BLOCKING-136Q-1`/`-136S-2`/`-136T-7`).
- Manifest: independently recomputed all 21 `file_digest` values against
  actual file bytes, zero mismatches; `load_and_verify_manifest` confirms
  two-way completeness; a tampered digest and a partial Group 10 manifest
  were both independently confirmed to raise `ManifestIntegrityError`.
- Dependency graphs: four independent graphs rebuilt from scratch — no
  cycle; no Group 10 sibling references another, directly or transitively.
- Packaging: fresh wheel and sdist independently built and inspected; both
  contain exactly 22 `cltr_cutover` schema files (14 records + 7 shared +
  `manifest.schema.json`), no Group 9/11 file. Installed wheel into an
  isolated venv outside the repository checkout and independently validated
  valid and invalid records for all three Group 10 families entirely
  offline.
- No-network: `socket.socket`/`socket.create_connection` monkeypatched to
  raise during registry construction and validation, in-repo and from the
  isolated installed wheel — zero calls recorded.
- No-runtime-binding/no-authority/no-execution: `git grep` confirms zero
  references to any Group 10 family outside `schema_resources/`; no
  `.pcae/cltr-authority/` directory exists; `pcae runtime inspect`
  reconfirmed `Observed`/`observe`/`unavailable`.
- `pcae health`, `pcae check`, `pcae status coherence`,
  `pcae doctor task-memory` all passed/clean before finalization.

## Findings

Independently reviewed and re-confirmed all fourteen inherited findings
(`NON-BLOCKING-136M-1` through `-4`, `NON-BLOCKING-136N-7`,
`NON-BLOCKING-136P-1`/`-2`, `NON-BLOCKING-136Q-1`,
`NON-BLOCKING-136R-1` through `-4`, `NON-BLOCKING-136S-2`,
`NON-BLOCKING-136T-1` through `-7`, `DEFERRED-136T-1`) — none converted to
Blocking beyond the one repaired this phase, none amplified.

One new Blocking finding, found and repaired this phase (full text in
`docs/PHASE_136_NOTIFICATION_MARKER_RECEIPT_AUTHORITY_BINDING_SCHEMA_INDEPENDENT_VERIFICATION.md`
§18):

- `BLOCKING-136U-1`: stale, hardcoded scope-guard filename lists in
  136N's and 136R's test files, desynchronized from
  `LATER_GROUP_RECORD_FILES` by 136T's own Group 10 migration, causing
  two deterministic (non-race) regression failures. **Repaired** this
  phase; regression-tested; verdict: fixed.

Zero unresolved `BLOCKING` findings remain.

## Safety and no-go confirmation

- Legacy lifecycle remains the sole production authority. CLTR remains
  derivative.
- 136U independently verified executable-schema Implementation Group 10:
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`, and
  `FinalizationReceiptAuthorityBinding`.
- The frozen contract assigns no executable schema file to Group 9, so no
  Group 9 schema was required or implemented.
- The three Group 10 schemas remain descriptive authority bindings only.
- No runtime notification dispatch, marker creation, receipt creation,
  compatibility resolution, historical-authority resolution, publication,
  recovery, or authority transition was introduced.
- All three Group 10 schemas locally forbid an authoritative authority role
  where required by the frozen contract.
- Tier 2 extension behavior remains confined to the explicit `_extensions`
  boundary.
- Schema validity does not establish that a notification was delivered, a
  marker exists, a receipt is final, an external effect occurred, an
  identity exists, a staleness claim is true, or a binding is operationally
  authoritative.
- No Group 11 schema, `CompatibilityState`, `HistoricalAuthorityReference`
  schema, derived view, Stage 3 typed model, or broad cross-record semantic
  validator was implemented.
- No cryptographic verification, runtime evaluator, resolver, coordinator,
  authority-state persistence, or authority pointer was implemented or
  changed.
- No runtime Group 10 object was created or persisted. No authority epoch
  changed. No CLTR authority was created. No legacy authority was demoted.
  No legacy authority was retired.
- No production lifecycle behavior changed. No execution capability was
  introduced.
- Runtime remains Observed, maximum capability remains observe, and
  execution availability remains unavailable.
- One bounded repair (`BLOCKING-136U-1`) was made to two pre-existing test
  files to fix a stale scope-guard regression left by 136T's own Group 10
  migration; no production schema, manifest, or runtime source file was
  touched by that repair.

## Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR NEXT EXECUTABLE-SCHEMA
GROUP.** Legacy lifecycle remains the sole production authority; CLTR
remains derivative; runtime remains Observed / observe / execution
unavailable. One Blocking defect was independently discovered and repaired
within this phase's bounded scope; zero unresolved Blocking findings
remain.

## Recommended next phase

**136V — Compatibility/Quarantine Schema Implementation (Implementation
Group 11).** Section 46's 11-row table assigns `compatibility_state.schema.json`
(depends only on Group 1) and `quarantine_record.schema.json` (depends on
Groups 2–8) to Group 11 — the final executable-schema implementation group
per that table. Exact field tables (§34, §30) and prerequisites were not
re-derived by this phase (out of 136U's bounded scope) and must be
independently re-derived at the start of that phase, not assumed from this
report. Phase 136U does not begin that implementation.
