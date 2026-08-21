# Phase 149O.20L.7O.2N.12 — HRWP-001 v1.1 `protocol_name` Closed-Vocabulary Clarification, Independent Verification

## Scope

Independent verification of Phase 149O.20L.7O.2N.11's HRWP-001 v1.0 → v1.1
in-place repair of `HRWP-REQ-019`, closing (pending this verification)
NBF-149O.20L.7O.2N.8-1. Verification only: no contract amendment, no
`_PROTOCOL_VALUES` change, no implementation, no hardware, no protected
state, no redeployment.

## 1. Entering state

- True phase-entry commit (immediately pre-2N.11, canonical-sync commit
  of Phase 149O.20L.7O.2N.10): `e7451333f1697267b4d000c492e65fec267111f0`.
- HEAD entering this phase: `158f3de3a4e005ef0f597f8d8016d03bc1656ddd`
  (Phase 149O.20L.7O.2N.11's own final commit).
- HRWP-001: v1.1. HRAC-001: v1.0, unchanged. HSCE-001: v1.3, unchanged.
  HHCE-001: v1.1, unchanged.
- Production `protocol_name` validation: closed vocabulary,
  `{"FIDO2", "PIV"}`. Remote-WebAuthn value not yet implemented.

## 2. Fixed historical checkpoint (pre-2N.11, `e7451333`)

Independently re-derived from `git show e7451333:<path>`, not from 2N.11's
own report:

- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` at that
  commit: `**Version:** 1.0`; `HRWP-REQ-019` read (verbatim fragment)
  "...requiring no schema widening" — the exact inaccurate v1.0 claim.
- `src/pcae/core/hatp_hardware_credentials.py` at that commit already
  contained `_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` and
  `if protocol_name not in _PROTOCOL_VALUES: raise
  HATPHardwareCredentialStoreMalformedError(...)`. `"WEBAUTHN"` did not
  appear anywhere in that file at that commit.

This independently reproduces the original contradiction: v1.0's
requirement text asserted no schema-widening work was needed at all,
while production already enforced a closed allowlist that would reject
a real `protocol_name="WEBAUTHN"` record. Confirmed by direct diff
against a fixed git blob, not by trusting 2N.11's prose.

## 3. Current contract checkpoint (HEAD)

- `**Version:** 1.1` present.
- `**HRWP-REQ-019 (revised, v1.1 ...)` present — same requirement
  identity, revised in place.
- Requirement numbering independently re-extracted by regex over the
  live file: `HRWP-REQ-001`..`HRWP-REQ-068`, sequential, no gap, no
  duplicate. Count unchanged at 68.

## 4. Primary production source — exact current `_PROTOCOL_VALUES`

`src/pcae/core/hatp_hardware_credentials.py:56`:
`_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})`, enforced at
`_parse_credential` (line 224-225): `if protocol_name not in
_PROTOCOL_VALUES: raise HATPHardwareCredentialStoreMalformedError(...)`.
Unchanged since the fixed checkpoint. `"WEBAUTHN"` is not a member.

## 5. Closed-vocabulary enforcement — mechanically proven

Fresh disposable tests (this phase's own test file, not 2N.11's) call
`_parse_credential_registry_document({"credentials": [{...,
"protocol_name": "WEBAUTHN", ...}]})` directly and assert
`HATPHardwareCredentialStoreMalformedError` is raised
(`test_unknown_protocol_name_mechanically_rejected_by_registry_parser`).
The same document with `protocol_name` = `"FIDO2"` or `"PIV"` parses
successfully (`test_known_protocol_names_still_accepted_by_registry_parser`).
Fail-closed, mechanically confirmed, not asserted from prose.

## 6. Structural schema re-derivation

`dataclasses.fields(HardwareCredentialRecord)` independently enumerated:
exactly `{signer_key_id, provider_profile, protocol_name, algorithm,
public_key, status, revoked_at}` — the same 7 fields HHCE-001 v1.1
already defines. No new field is required to represent
`protocol_name="WEBAUTHN"` / `provider_profile=
HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"`: both existing string-typed
fields can carry the new values once the closed-vocabulary gates
described below are widened. **Candidate B confirmed independently**
(only a new permitted *value*, not a new field).

## 7. `HRWP-REQ-019` text — verified

The revised requirement's body was independently re-extracted (not
copied from 2N.11's own summary) and confirmed to state, distinctly and
without blurring: (a) "no `HardwareCredentialRecord` **structural**
schema widening" (unchanged claim); (b) an "**additive closed-vocabulary
widening**" of `_PROTOCOL_VALUES` is separately required; (c) a record
with `protocol_name="WEBAUTHN"` "is therefore rejected as malformed
... by current production" until that widening occurs. No sentence in
the revised text is ambiguous between "no schema change" and "no
parser/vocabulary change" — the two claims are named and separated
explicitly.

## 8. Fail-closed requirement — verified

The revised text explicitly states the closed-vocabulary discipline
"is itself a security property ... and SHALL NOT be relaxed to an open
string merely to avoid this future edit." No recommendation anywhere in
the current contract text proposes converting `protocol_name` to an
unvalidated open string. Unknown values remain rejected both before and
after the future widening — confirmed structurally (§5 above) and by
contract text.

## 9. Exact future value

`HRWP-REQ-019`: `protocol_name` **SHALL be `"WEBAUTHN"`** — all-caps,
exact spelling, matching the existing all-caps convention
(`"FIDO2" | "PIV"`). Confirmed by direct read of the current requirement
text, not from 2N.11's report summary (which also said `WEBAUTHN`, and
independently matches).

## 10. `protocol_name` vs `provider_profile`

Independently reconstructed from source and contract text:
`protocol_name` (`hatp_hardware_credentials.py`) is the underlying
credential/protocol-family discriminator (`"FIDO2"`, `"PIV"`, future
`"WEBAUTHN"`) — a data field on `HardwareCredentialRecord`, gated by
`_PROTOCOL_VALUES` at the registry-parser layer. `provider_profile` is
PCAE's ceremony/provider-routing semantics
(`HATP_HARDWARE_PROVIDER_V1`, future
`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN`) — a separate field on the
same record, consulted by `Fido2HardwareProvider.verify()`'s own
`record.provider_profile != provider_profile` fail-closed check and by
`create_production_hardware_provider()`'s factory dispatch (§11 below).
HRWP-001 does not conflate the two: `HRWP-REQ-007/008` (provider_profile)
and `HRWP-REQ-019` (protocol_name) are separate requirements, each with
its own frozen value. For remote WebAuthn, both differ from the local
raw-FIDO path (`"WEBAUTHN"` vs `"FIDO2"`;
`HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` vs
`HATP_HARDWARE_PROVIDER_V1`).

## 11. `provider_profile` vocabulary — NEW FINDING, non-blocking

**NBF-149O.20L.7O.2N.12-1 (Non-Blocking).** Independent inspection of
`src/pcae/core/hatp_providers.py` found `provider_profile` is *also*
a closed production vocabulary — at a different enforcement layer than
`protocol_name`'s:

```python
_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)
...
def create_production_hardware_provider(provider_profile: str, ...):
    if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES:
        raise HATPProviderUnavailableError(...)
```

Mechanically confirmed this phase
(`test_create_production_hardware_provider_rejects_remote_webauthn_profile_today`):
calling `create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")`
raises `HATPProviderUnavailableError` today. Separately,
`HardwareCredentialRecord`'s own registry parser does **not** close
`provider_profile` — it only requires a non-empty string
(`hatp_hardware_credentials.py:222-223`), independently confirmed by
`test_hardware_credential_record_own_provider_profile_field_is_not_closed_at_parse_time`
(a record with `provider_profile="HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"`
parses successfully). So: the *record* can already carry the new
`provider_profile` value once persisted, but the *factory* that
constructs a live provider instance for verification/signing cannot
select it.

This is **not omitted from HRWP-001's contract text** — `HRWP-REQ-006`
already states the factory "is NOT amended by this contract" and that
"a future implementation phase MUST decide ... whether remote-WebAuthn
provider selection is added to that factory's existing
`provider_profile`-string dispatch" — but HRWP-001's §45 v1.1 repair's
"Implementation prerequisite frozen by this repair" paragraph names only
the `_PROTOCOL_VALUES` widening, not this second, independent closed
allowlist. Both gates must be additively widened (or otherwise
addressed by the future dispatch decision HRWP-REQ-006 already defers)
before a real remote-WebAuthn provider can be produced and used, not
just `_PROTOCOL_VALUES` alone. This does not block NBF-149O.20L.7O.2N.8-1's
own closure (that finding is scoped to `protocol_name`/schema-shape
specifically, and HRWP-REQ-006 already named the factory-dispatch
question as future-phase-scoped) — it is a distinct, narrower
observation for the next implementation-scoping phase's awareness, not
a contradiction in current contract text.

## 12. Duplicated-vocabulary search — NEW FINDING, non-blocking

**NBF-149O.20L.7O.2N.12-2 (Non-Blocking).** A full-tree search
(`grep -rn` over `src/pcae` and `scripts`) for `protocol_name` /
`FIDO2`/`PIV` literal checks found a **second, independent, hardcoded
closed-vocabulary enforcement point**, separate from
`hatp_hardware_credentials.py::_PROTOCOL_VALUES`:

`src/pcae/core/hatp_hardware_credential_admin.py:171-172`
(`_validate_enrollment_evidence`, part of the `register_credential`
enrollment-evidence validation path):

```python
if protocol_name not in ("FIDO2", "PIV"):
    raise CredentialEvidenceMalformedError(
        f"evidence.protocol_name must be 'FIDO2' or 'PIV', got {protocol_name!r}")
```

Mechanically confirmed
(`test_admin_enrollment_validator_rejects_webauthn_protocol_name_today`):
constructing a `CredentialEnrollmentEvidence` with
`protocol_name="WEBAUTHN"` and calling `_validate_enrollment_evidence`
raises `CredentialEvidenceMalformedError` today, independently of and
in addition to the registry-parser's own `_PROTOCOL_VALUES` rejection.
This is a **hardcoded literal tuple**, not derived from or imported from
`hatp_hardware_credentials._PROTOCOL_VALUES` — the two closed sets are
maintained independently in source and could, in principle, drift apart
if only one were widened.

**Implementation-delta consequence:** §45's "Implementation prerequisite"
paragraph names a "narrow, one-line" change confined to
`_PROTOCOL_VALUES` in `hatp_hardware_credentials.py`. That is accurate
for the **registry-parser/read path**, but the full implementation delta
for a durably-**enrollable** `protocol_name="WEBAUTHN"` record is at
minimum **two files**: `hatp_hardware_credentials.py`'s
`_PROTOCOL_VALUES` (read/parse path) and
`hatp_hardware_credential_admin.py`'s hardcoded `("FIDO2", "PIV")` tuple
(the enrollment-evidence write/validate path) — both must be widened in
lockstep, or enrollment evidence bearing `protocol_name="WEBAUTHN"`
would be rejected at the admin-validation layer even after
`_PROTOCOL_VALUES` alone was widened. This does not block
NBF-149O.20L.7O.2N.8-1's closure (the finding under verification is
about the schema-shape/vocabulary distinction, which remains correct),
but it means HRWP-001 §45's implementation-prerequisite text is
**narrower than the actual implementation delta** and should be
corrected in a future narrow repair before implementation begins,
mirroring this same repair-then-reverify discipline.

## 13. HRWP version evolution and version history

v1.0 → v1.1 is the smallest justified version bump under this
repository's precedent (a normative requirement's text changed;
compare HHCE-001 v1.0→v1.1, HPSE-001 v1.0→v1.1) — independently
confirmed consistent, not merely asserted. §45's version-history
narrative accurately distinguishes the v1.0 claim (quoted, named
inaccurate) from the v1.1 corrected claim (quoted, named accurate) —
the original text is not silently rewritten to appear as if the
contradiction never existed; §45 preserves and quotes the original
wording precisely as the record of what was wrong.

## 14. Downstream contract compatibility

- **HRAC-001** (v1.0, unchanged): its own `§44`/`HRAC-REQ-066` already
  names this exact finding as "carried forward, not resolved," and
  states its signer-resolution reuse never reads `protocol_name`.
  Independently re-read this phase — accurate, unchanged, no amendment
  required.
- **HSCE-001** (v1.3, unchanged): never made the corrected claim; no
  semantic signing-ceremony impact from a text-only HRWP-001 revision.
- **HHCE-001** (v1.1, unchanged): `HHCE-REQ-002`'s "plain string field,
  not a closed enum in code" comment is a true statement about the
  dataclass field's own Python type annotation (`str`), distinct from
  the closed-enum enforcement that lives in the *parser*
  (`_parse_credential`). No HHCE-001 text is inaccurate.
- **HPSE-001/HBDC-001**: neither `Principal`/`SignerRecord` nor
  `DeploymentBinding` schemas were inspected as depending on a closed
  protocol vocabulary in any way requiring amendment; `SignerRecord`'s
  own `provider_profile: str` field is unvalidated at that layer,
  identically in kind to `HardwareCredentialRecord`'s (§11 above) — no
  HPSE-001/HBDC-001 amendment implied by this repair.

`git diff e7451333..HEAD` for
`docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`,
`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`, and
`docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`
independently confirmed empty (mechanically, via git, not via report
trust).

## 15. Historical record and mixed local/remote compatibility

Fresh disposable tests confirm: (a) all pre-existing protocol values
(`FIDO2`, `PIV`) continue to parse identically after this contract-text
repair (no migration implied, none performed); (b) the registry parser
already supports multiple simultaneous `HardwareCredentialRecord`s keyed
by distinct `signer_key_id`, including one carrying
`provider_profile=HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` alongside
one carrying `HATP_HARDWARE_PROVIDER_V1` — no field collision, no
singleton assumption, confirmed mechanically, not merely by reading
`HRWP-REQ-011/012`'s prose.

## 16. Stale-text sweep

A sweep of the current (post-§45) normative body — i.e. everything
before the `## 45. v1.1 Repair` section — for "no schema" / "no
vocabulary change" phrasing found no current normative contradiction:
the two remaining "no schema change" occurrences (`HRWP-REQ-011/012`)
concern the registry's *array-cardinality* schema (supporting an
arbitrary number of records) and `SignerRecord`'s own multiplicity, not
`protocol_name`'s vocabulary — correctly scoped, unrelated to the
repaired claim. The one occurrence of "requiring no schema widening"
that exists in the file appears only inside §45's own historical
quotation of the retracted v1.0 text, clearly marked as historical.
Mechanically confirmed via
`test_no_stale_current_normative_no_vocabulary_change_claim`.

## 17. Implementation gates — enrollment vs assertion

**Enrollment/registration gate:** `HardwareCredentialRecord` persistence
of a real `protocol_name="WEBAUTHN"` record would fail at (at least) two
independent points today: the admin enrollment-evidence validator
(`hatp_hardware_credential_admin.py:171-172`, §12 above) and, even if
that were bypassed, the registry-parser's own read-back verification
(`hatp_hardware_credentials.py::_parse_credential`, §5 above) — `register_credential`'s
own read-back-and-verify step (HHCE-REQ discipline) reuses the same
parser. **Assertion/signing gate:** a signing ceremony against an
already-enrolled remote-WebAuthn credential would separately require
`create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")`
to succeed, which it does not today (§11 above) — a distinct gate from
enrollment, confirming HRWP-REQ-048(ii)'s own scoping that assertion has
its own prerequisites beyond enrollment.

## 18. Finding disposition

**NBF-149O.20L.7O.2N.8-1: INDEPENDENTLY CONFIRMED CLOSED** at the HRWP
contract / production-vocabulary requirement boundary. All five closure
criteria (§37 of the governing prompt) independently satisfied:

1. Original contradiction independently reproduced from the fixed
   pre-2N.11 checkpoint (§2).
2. Revised text correctly and unambiguously distinguishes structural
   shape from closed vocabulary (§6-8).
3. Exact future implementation requirement stated explicitly (§9, §12).
4. Unknown protocols remain fail-closed, mechanically proven, both
   before and after any future widening (§5, §8).
5. No new *schema-shape* gap discovered (§6) — but two new
   *implementation-scope* findings were discovered (§11, §12),
   non-blocking to this specific finding's closure, carried forward for
   the next scoping phase.
6. Downstream contracts remain coherent (§14).

Production does not now support remote WebAuthn — it does not, and this
report makes no such claim.

## 19. New findings (carried forward, not repaired this phase)

- **NBF-149O.20L.7O.2N.12-1**: `provider_profile`'s own closed
  production allowlist (`hatp_providers.py::_PRODUCTION_HARDWARE_PROVIDER_PROFILES`)
  also excludes `HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` and is not
  named in HRWP-001 §45's implementation-prerequisite list (though
  `HRWP-REQ-006` already flags the factory-dispatch question generally).
- **NBF-149O.20L.7O.2N.12-2**: A second, independent, hardcoded
  `("FIDO2", "PIV")` closed-vocabulary check exists in
  `hatp_hardware_credential_admin.py`'s enrollment-evidence validator,
  not named by HRWP-001 §45's "one-line, one-file" implementation-delta
  claim. The real minimum implementation delta is at least two files.

Neither finding blocks NBF-149O.20L.7O.2N.8-1's closure; both should be
folded into HRWP-001's next narrow repair (or the implementation
phase's own scoping) before that implementation phase claims a complete
delta.

## 20. Overall verdict

**B — VERIFIED WITH NON-BLOCKING FINDINGS — FINDING CLOSED.**

HRWP-001 v1.1 `protocol_name` CLOSED-VOCABULARY CLARIFICATION —
INDEPENDENTLY VERIFIED. NBF-149O.20L.7O.2N.8-1 — INDEPENDENTLY CONFIRMED
CLOSED. `HardwareCredentialRecord` structural schema: UNCHANGED. Remote
WebAuthn `protocol_name` implementation: STILL REQUIRED (now known to
span at least two files, per NBF-149O.20L.7O.2N.12-2, plus the
`provider_profile` factory gate per NBF-149O.20L.7O.2N.12-1). Unknown
`protocol_name` values: FAIL-CLOSED. No production change this phase.

## 21. Recommended next phase

Two independently-orderable prerequisites remain before remote-WebAuthn
server/provider implementation may begin:

1. The narrow, deterministic production vocabulary implementation
   (`_PROTOCOL_VALUES` **and** the admin-module's duplicated tuple,
   per NBF-149O.20L.7O.2N.12-2, **and** the `provider_profile` factory
   allowlist or its dispatch resolution, per NBF-149O.20L.7O.2N.12-1) —
   now a slightly broader but still small and deterministic scope than
   2N.11's report described.
2. RP-ID/origin/HTTPS infrastructure architecture selection
   (HRWP-REQ-027/031, independent of #1).

No ordering dependency exists between the RP-ID/TLS infrastructure
decision and the vocabulary/provider-dispatch implementation — both
were independently confirmed free of a literal-value or code
dependency on each other. Recommendation (mirroring the governing
prompt's own default): perform the small, deterministic vocabulary/
provider-dispatch implementation next (item 1, its own narrowly-scoped
phase, independently verified), then address the wider RP-ID/TLS
infrastructure decision (item 2). Do not begin remote-WebAuthn server/
provider implementation until item 1 is itself independently verified.

## 22. Independent test suite

`tests/test_phase_149o_20l_7o_2n_12_hrwp_001_protocol_name_vocabulary_repair_independent_verification.py`
— 24 tests, freshly authored (not copied from 2N.11's own test file),
all passing. Covers: fixed v1.0 contradiction (2 tests), current v1.1
wording (2), requirement numbering, current `_PROTOCOL_VALUES` exact
set, unknown/known value rejection/acceptance (mechanical), structural
schema fields, `HRWP-REQ-019` structural-vs-vocabulary distinction,
exact future value, fail-closed no-relaxation claim,
`protocol_name`/`provider_profile` distinction, `provider_profile`
factory closed-allowlist finding (2 tests), duplicated-vocabulary
finding (2 tests), no production change (2 tests, git-diff-based),
historical compatibility, mixed local/remote representability, stale
current-text sweep, HRAC-001 accuracy, version-history distinction.

## 23. Fast Green

`python -m pytest -m fast_green -q` run this phase; raw outcome and any
attributable-regression analysis reported separately in the canonical
completion report/metadata (§ per this repository's own
"no nonzero failure count without a clean deselected re-run" discipline).
No production behavior changed by this phase; any pre-existing failures
are, by construction (zero `src/pcae`/`scripts` diff this phase), not
attributable to it.

## 24. No real effect

No Dell connection. No hardware. No WebAuthn ceremony. No protected-state
write. No DNS/TLS. Verification, source-reading, and disposable
in-memory tests only.

## 25. Commits and push

See `.pcae/phase-completion-metadata.json` for `phase_commits`,
`origin_main_head`, and push state, finalized via the standard governed
`pcae phase complete` / `pcae push` sequence.
