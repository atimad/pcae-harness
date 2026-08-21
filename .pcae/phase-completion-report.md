# Phase 149O.20L.7O.2N.11 Completion Report

**Verdict:** HRWP protocol_name CLOSED-VOCABULARY CONTRADICTION
REPAIRED — STRUCTURAL SCHEMA STILL UNCHANGED — ADDITIVE VOCABULARY
IMPLEMENTATION REQUIREMENT MADE EXPLICIT — INDEPENDENT VERIFICATION
PENDING — NO PRODUCTION CHANGE.
See `docs/PHASE_149O_20L_7O_2N_11_HRWP_001_PROTOCOL_NAME_CLOSED_VOCABULARY_CONTRACT_CLARIFICATION.md`
for the full phase report.

Narrow, contract-text-only repair phase, following Phase
149O.20L.7O.2N.10's own recommendation. Repairs NBF-149O.20L.7O.2N.8-1
(found by Phase 149O.20L.7O.2N.8's independent verification of HRWP-001,
independently reconfirmed by Phase 149O.20L.7O.2N.10's independent
verification of HRAC-001): `HRWP-REQ-019` v1.0 claimed
`protocol_name = "WEBAUTHN"` requires no schema widening at all, relying
on HHCE-REQ-002's description of `protocol_name` as "a plain string
field, not a closed enum in code." That reliance was inaccurate:
`hatp_hardware_credentials.py::_parse_credential` enforces `protocol_name`
against a closed `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})`
allowlist in code — confirmed again this phase by direct source read.

**Correction made:** `HRWP-REQ-019` revised in place (same requirement
identity, no renumbering — mirrors HHCE-001 v1.1's own §30 precedent for
an in-place text-only revision). The revised text preserves the
accurate claim (no `HardwareCredentialRecord` structural schema
widening required) while correcting the inaccurate one: an **additive
closed-vocabulary widening** of `_PROTOCOL_VALUES` (a narrow, one-line
future code change) is required before a real `protocol_name="WEBAUTHN"`
record can be durably enrolled. HRWP-001 bumped v1.0 → v1.1 (a
requirement's text changed, mirroring this repository's HHCE-001/
HPSE-001 v1.0→v1.1 precedent). No other requirement's text changed; no
requirement added, removed, or renumbered — requirement count unchanged
at 68 (`HRWP-REQ-001`..`HRWP-REQ-068`).

**Downstream impact, independently checked this phase:** HRAC-001
requires no amendment or version bump (its own §44/HRAC-REQ-066 already
described this finding accurately as carried-forward, and its
signer-resolution reuse never reads `protocol_name`). HSCE-001 requires
no amendment (was already unamended by HRWP-001, remains so). HHCE-001
requires no amendment (`HHCE-REQ-002`'s dataclass-field-type claim is
accurate on its own terms; HRWP-REQ-019 v1.0 over-read it, not the
reverse).

**No production change:** `git diff --stat <phase-entry-commit>..HEAD --
src/pcae/ scripts/` returns empty. Only `docs/contracts/
HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (the contract under repair),
one new test file, and three pre-existing HRWP test files (updated
only for the in-place-revision heading/version format, not weakened
substantively) were modified, plus this report and standard
task-lifecycle/status files.

Testing: a new disposable file,
`tests/test_phase_149o_20l_7o_2n_11_hrwp_001_protocol_name_vocabulary_repair.py`
(13 tests, all passing) — version bump, in-place-revision identity,
corrected closed-vocabulary text, preserved schema-shape/vocabulary
distinction, the new §45 repair section's content, requirement-count
note, production `_PROTOCOL_VALUES` still unimplemented this phase, and
non-amendment of HRAC-001/HSCE-001/HHCE-001. Combined with the three
updated pre-existing files, 83 tests pass across the HRWP/HRAC phase
family.

**Fast Green, A/B-attributed:** raw `pytest -m fast_green -q` shows 352
failed/8679 passed with this phase's changes present, vs. 341 failed/
8690 passed with them stashed out (exact match to Phase
149O.20L.7O.2N.8's own reported baseline). The exact 11-test diff
between the two `FAILED` sets is entirely one self-check class —
pre-existing "working tree under `src/pcae`/`docs/contracts` is clean"
non-regression assertions written by 8 different earlier phases —
tripped only because this phase's own contract-text diff is legitimately
uncommitted at test-run time; they check live `git status`/`git diff`,
not a fixed hash, and self-resolve once this phase's changes are
committed. Attributable regression count this phase: **0**.

**No implementation.** No protocol value, provider, request store,
WebAuthn server/client code added to production. No `_PROTOCOL_VALUES`
change. No DNS/certificates provisioned. No hardware touched. No
credentials/assertions created. No HMIC-001 change. No redeployment. No
certification modified. No protected records created. No HATP
activation. No PB/runtime change.

Next phase: a narrow independent verification phase for this HRWP-001
v1.1 correction, mirroring the 2N.7→2N.8 and 2N.9→2N.10 freeze-then-
verify precedent. After that verification closes NBF-149O.20L.7O.2N.8-1,
two independently-orderable prerequisites remain before any
remote-WebAuthn provider/server implementation may begin: (1)
`protocol_name` vocabulary implementation; (2) RP-ID/origin/HTTPS
infrastructure architecture selection.
