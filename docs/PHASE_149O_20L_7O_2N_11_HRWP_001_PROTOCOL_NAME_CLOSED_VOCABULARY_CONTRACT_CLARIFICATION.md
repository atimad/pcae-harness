# Phase 149O.20L.7O.2N.11 — HRWP-001 protocol_name Closed-Vocabulary Contract Clarification

## Verdict

```
HRWP protocol_name CLOSED-VOCABULARY CONTRADICTION REPAIRED
— STRUCTURAL SCHEMA STILL UNCHANGED
— ADDITIVE VOCABULARY IMPLEMENTATION REQUIREMENT MADE EXPLICIT
— INDEPENDENT VERIFICATION PENDING
— NO PRODUCTION CHANGE
```

## True phase-entry commit

`e7451333` — Phase 149O.20L.7O.2N.10: sync canonical phase-completion-report.md/metadata.json to this phase (HEAD at phase start, `main`, clean, nothing_to_push).

## Original finding

Phase 149O.20L.7O.2N.8's independent verification of HRWP-001 found a Non-Blocking finding: HRWP-REQ-019 v1.0 stated `protocol_name = "WEBAUTHN"` requires "no schema widening," relying on HHCE-REQ-002's comment that `protocol_name` is "a plain string field, not a closed enum in code." That reliance was inaccurate — `hatp_hardware_credentials.py::_parse_credential` enforces a closed `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` allowlist. Phase 149O.20L.7O.2N.10's independent verification of HRAC-001 independently reconfirmed this finding (its own §44/HRAC-REQ-066) and confirmed it does not block HRAC-001's internal coherence, since HRAC-001's signer-resolution reuse never reads `protocol_name`.

## Primary-source re-derivation this phase

Read directly, not trusted from prior phases' summary prose:

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001 v1.0, full text)
- `src/pcae/core/hatp_hardware_credentials.py` (full file)
- `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001 v1.1, §5/§30 read in depth)
- `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001, confirmed unamended-by-this-phase)
- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001 v1.0, §44/§47/HRAC-REQ-066/069/074 read in depth)
- `docs/PHASE_149O_20L_7O_2N_8_HRWP_001_INDEPENDENT_VERIFICATION.md` (the finding's original text, for exact wording, not trusted as authoritative over the source read above)

## Exact current closed vocabulary (§4/§13 of the governing prompt)

`hatp_hardware_credentials.py:56`: `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})`.

**Parser enforcement:** `_parse_credential` (`hatp_hardware_credentials.py:224-225`): `if protocol_name not in _PROTOCOL_VALUES: raise HATPHardwareCredentialStoreMalformedError(f"invalid protocol_name: {protocol_name!r}")`.

**Validation path:** every credential record parsed via `_parse_credential_registry_document` → `_parse_credential` — the sole parse path used by the read-only `HATPHardwareCredentialStore._load_registry`; no separate/relaxed parse path exists in this module.

**Failure behavior for unknown values:** `HATPHardwareCredentialStoreMalformedError` raised, document rejected wholesale (`_load_registry` never partially accepts a malformed document) — fail-closed, not skip-and-continue.

Confirmed empirically (test `test_production_protocol_values_still_exactly_fido2_piv_no_implementation_here`) and matches Phase 149O.20L.7O.2N.8's own finding text; not inferred from test fixtures alone — read directly from the module source.

## HardwareCredentialRecord structural-schema result

Confirmed NO new field is required. `HardwareCredentialRecord`'s existing fields (`signer_key_id`, `provider_profile`, `protocol_name`, `algorithm`, `public_key`, `status`, `revoked_at`) already represent every fact HRWP-REQ-018 names for a remote-WebAuthn registration response: `signer_key_id` ← WebAuthn `credential.id`; `public_key` ← CBOR COSE_Key bytes from `attestationObject`; `algorithm` ← negotiated COSE algorithm; `provider_profile` ← `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`; `protocol_name` ← `"WEBAUTHN"` (vocabulary-gated, this phase's subject); `status`/`revoked_at` ← existing lifecycle fields, unchanged semantics. `SignerRecord` and `DeploymentBinding` (`hatp_bootstrap.py`) likewise need no new field (HRWP-REQ-057/058, re-confirmed, unchanged by this phase). This narrow repair remains sufficient — §5 of the governing prompt's "if a new field is actually required, STOP" condition does not trigger.

## protocol_name vs. provider_profile

`provider_profile` identifies the PCAE provider/ceremony-semantics profile — the field a verifier uses to route a stored record to the correct provider implementation and evidence parser (HRWP-REQ-007/008, unchanged: frozen value `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`, an **open** string field at the registry layer — no `_PROVIDER_PROFILE_VALUES` allowlist exists in `hatp_hardware_credentials.py`). `protocol_name` identifies the hardware/WebAuthn protocol family at the record level — currently a **closed**, code-enforced two-member vocabulary (`"FIDO2" | "PIV"`). These are distinct claims at distinct enforcement layers; this phase's repair narrows itself to correcting only the `protocol_name` claim, leaving the `provider_profile` claim (already accurate) untouched.

## Exact contract correction

`docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md`, `HRWP-REQ-019`, revised in place (same requirement identity, no renumbering — mirrors HHCE-001 v1.1's own §30 precedent):

- Preserves: `provider_profile` SHALL be `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`; `protocol_name` SHALL be `"WEBAUTHN"`, a new value alongside `"FIDO2" | "PIV"`.
- Preserves, restated explicitly: no `HardwareCredentialRecord` structural schema widening required.
- Corrects: production's `_PROTOCOL_VALUES` is a closed frozenset enforced in code, not an open string field — a real `protocol_name="WEBAUTHN"` record is rejected (`HATPHardwareCredentialStoreMalformedError`) by current production until `_PROTOCOL_VALUES` is additively widened. This is a narrow, one-line code change confined to that frozenset, not a structural schema change, and not a security-property weakening — unknown `protocol_name` values remain rejected fail-closed both before and after that future widening.
- A new §45 ("v1.1 Repair") documents the finding, the correction, the version consequence, and downstream-contract impact, mirroring HHCE-001 v1.1 §30's structure.

Structural schema and closed vocabulary are stated as two distinct, non-conflated claims in the revised text.

## HRWP version consequence

**v1.0 → v1.1.** A normative requirement's text changed (`HRWP-REQ-019`), so per this repository's established convention (HHCE-001 v1.0→v1.1 for its own §30 in-place `HHCE-REQ-002` revision; HPSE-001 v1.0→v1.1 for its own in-place revisions) this is the smallest justified version change. No other requirement's text changed. No requirement added, removed, or renumbered; the requirement count remains 68 (`HRWP-REQ-001`..`HRWP-REQ-068`, confirmed by test).

## HRAC-001 impact

**No amendment, no version bump.** Independently re-checked this phase: HRAC-001 v1.0's own §44/HRAC-REQ-066 already described this exact finding accurately as "carried forward, not resolved," and already stated HRAC-001's own signer-resolution reuse (§9) never reads `protocol_name` at all — this repair does not change any claim HRAC-001 itself makes about HRWP-001. HRAC-001 remains v1.0, unmodified by this phase (confirmed by test).

## HSCE impact

**No amendment, no version bump.** HSCE-001 was already unamended by HRWP-001 v1.0 and remains unamended by this repair; nothing in HSCE-001's own text made the corrected claim, and HSCE-001 is not touched by this phase (confirmed unmodified in the diff below).

## HHCE impact

**No amendment, no version bump.** `HHCE-REQ-002`'s own text ("a plain string field, not a closed enum in code") is accurate on its own terms as a description of `HardwareCredentialRecord`'s dataclass field type annotation (`protocol_name: str`) — the dataclass field itself carries no `Enum`/`Literal` type restriction. The closed-vocabulary enforcement HRWP-REQ-019 needed to account for lives one layer down, in the *parser* (`_parse_credential`'s `if protocol_name not in _PROTOCOL_VALUES` check) — a distinct claim from the dataclass field's own type that HHCE-REQ-002 never made and never contradicted. HRWP-REQ-019 v1.0 over-read HHCE-REQ-002's narrower claim; HHCE-001's own text is not inaccurate and requires no amendment. HHCE-001 remains v1.1, unmodified by this phase (confirmed by test).

## Future implementation value/string

`"WEBAUTHN"` — the exact literal HRWP-REQ-019 already names, unchanged by this repair. Implementation prerequisite frozen (not performed this phase): add exactly this one value to `_PROTOCOL_VALUES` in `hatp_hardware_credentials.py`, plus focused tests confirming the widened set accepts `"WEBAUTHN"` and continues to reject any other unknown value.

## Fail-closed unknown-value behavior

Preserved and restated explicitly in the revised `HRWP-REQ-019`: `protocol_name` remains a closed vocabulary before and after the future widening — a genuinely new future value is accepted only once explicitly added to `_PROTOCOL_VALUES`; any other unrecognized value continues to be rejected fail-closed. This repair does not relax `protocol_name` to an open string to avoid the future one-line edit — the contract text explicitly forbids that shortcut (§13 of the governing prompt, restated in the revised requirement text).

## Historical record compatibility

Unaffected. This phase makes no production or schema change; existing `HardwareCredentialRecord`s using `protocol_name in {"FIDO2", "PIV"}` are untouched. No migration, no rewrite, no default reinterpretation — none is implied by a contract-text-only change with zero production diff.

## Mixed local/remote credential compatibility

Confirmed conceptually unaffected by this repair: `_parse_credential_registry_document` already parses an arbitrary-length JSON array into `Dict[str, HardwareCredentialRecord]` keyed by `signer_key_id` (HRWP-REQ-011, re-confirmed, unmodified). Once `_PROTOCOL_VALUES` is eventually widened (future phase, not this one), local FIDO2 (`protocol_name="FIDO2"`) and remote-WebAuthn (`protocol_name="WEBAUTHN"`) records can coexist in the same registry under the same `Principal`/multi-`SignerRecord` model (HRWP-REQ-012/059), distinguished by `protocol_name`/`provider_profile` exactly as this repair's §6 clarification states.

## Local FIDO2 preservation

Untouched. `hatp_fido2_provider.py` is not read-for-modification this phase and is not in the task's allowed-file list; only `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` and test files were edited.

## No production change — proof

```
$ git diff --stat <phase-entry-commit>..HEAD -- src/pcae/ scripts/
(no output — zero files changed under src/pcae/ or scripts/)
```

Only `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (the contract under repair), one new test file, three pre-existing test files updated to reflect the in-place `HRWP-REQ-019` heading-format/version change (not a behavioral test change — see below), plus this report and standard task-lifecycle/status files, were modified.

**Why three pre-existing test files needed a small edit:** `test_phase_149o_20l_7o_2n_8_hrwp_001_independent_verification.py`'s numbering-completeness regex required exact `**HRWP-REQ-019.**` formatting; it was widened to also accept the in-place-revision heading form `**HRWP-REQ-019 (revised, v1.1 ...).**` — the identical style HHCE-REQ-002 v1.1 already established as this repository's precedent for an in-place requirement revision. `test_phase_149o_20l_7o_2n_7_...` and `test_phase_149o_20l_7o_2n_9_...` each pinned `"**Version:** 1.0"` for HRWP-001 as a point-in-time non-regression check at the phase that first froze/read it; both were updated to stop pinning a version number this phase legitimately supersedes, while keeping every other assertion (contract identity, FROZEN status, requirement count) unchanged. No test's assertion about HRWP-001's *substantive* claims was weakened.

## Focused tests

New: `tests/test_phase_149o_20l_7o_2n_11_hrwp_001_protocol_name_vocabulary_repair.py`, 13 tests — version bump, in-place revision identity/numbering, corrected closed-vocabulary text, preserved schema-shape/vocabulary distinction, unchanged structural-schema claims elsewhere, presence and content of the new §45 repair section, requirement-count note, production `_PROTOCOL_VALUES` still unimplemented this phase, and non-amendment of HRAC-001/HSCE-001/HHCE-001. All 13 pass standalone.

Updated: 3 pre-existing test files (see above), all pass after the update.

Combined targeted run (`test_phase_149o_20l_7o_2n_{7,8,9,10,11}_*.py`): 83 passed.

## Fast Green

Raw, unfiltered: `pytest -m fast_green -q` → 352 failed, 8679 passed, 4 skipped, 9 errors, 27124 deselected (568s).

A/B stash comparison performed (`git stash push -u`, re-run, `git stash pop`, re-run):
- **Baseline** (this phase's changes stashed out): 341 failed, 8690 passed, 4 skipped, 9 errors, 27113 deselected — matches Phase 149O.20L.7O.2N.8's own reported baseline exactly.
- **With this phase's changes**: 352 failed (+11), 8679 passed (−11), same 9 errors, same 4 skipped.
- **Exact diff of the two `FAILED` node-ID sets:** 11 tests fail only with this phase's changes present; 0 tests that failed in baseline are fixed; 0 unrelated tests flip either direction. All 11 new failures are the same single self-check class, spread across 8 pre-existing test files from prior phases (149O.14, 149O.19.5E.4, 149O.1G, 149O.20A, 149O.20C ×2, 149O.20H, 149O.20K.1, 149O.20L.7D.9, 149O.20L.7D.10, 149O.20L.7E) — each is a "this phase's own git status/diff under `src/pcae`/`docs/contracts` is empty" defensive non-regression check, written by a *different, earlier* phase to assert its own working tree was clean at the time it ran. Every one of them fails only because `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` is this phase's own legitimate, still-uncommitted diff at the moment `pytest -m fast_green` was run pre-commit — not a defect these tests found in this phase's work, and not touching any file those tests actually own. They check `git status`/`git diff` at test-run time, not a fixed content hash, so they self-resolve once this phase's changes are committed (the working tree returns to clean under `docs/contracts` again, since this repair's own commit *is* the new committed state those checks compare against).

Attributable failure count this phase: **0** (11 explained self-resolving artifacts of an uncommitted diff, 341 pre-existing/unrelated, both fully accounted for).

## Finding status

`protocol_name` closed-vocabulary contradiction: **REPAIRED — INDEPENDENT VERIFICATION PENDING.** Not marked independently closed by this phase.

## RP-ID/TLS prerequisite (carried forward, not touched this phase)

Unchanged from HRWP-001 §12/§14/§27/§31 and HRAC-001 §74: RP-ID/origin/HTTPS deployment-infrastructure architecture selection remains an independently-orderable prerequisite, with no ordering dependency on this repair. Not performed, provisioned, or decided in this phase.

## Runtime

Unchanged (Observed) — no HATP activation, no redeployment, no HMIC-001 change, no credential/assertion created, no hardware touched.

## No-Go confirmation

No implementation. No protocol value, provider, request store, WebAuthn server/client added to production. No DNS/certificates provisioned. No hardware touched. No credentials/assertions created. No HMIC-001 change. No redeployment. No certification modified. No protected records created. No HATP activation. No PB/runtime change.

## Recommended next phase

A narrow independent verification phase for this HRWP-001 v1.1 correction (mirrors the 2N.7→2N.8, 2N.9→2N.10 freeze-then-verify precedent). After that verification closes NBF-149O.20L.7O.2N.8-1, two independently-orderable prerequisites remain before any remote-WebAuthn provider/server implementation may begin: (1) `protocol_name` vocabulary implementation (widen `_PROTOCOL_VALUES` to include `"WEBAUTHN"`, plus tests); (2) RP-ID/origin/HTTPS infrastructure architecture selection (HRWP-REQ-027/031, unresolved by any contract to date).
