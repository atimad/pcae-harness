# Phase 149O.19.5A — HMIC Certification Data Models + Canonical Parsing

**Status:** IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
**Wave:** A of 5 (149O.19.5A–E) under HMIC-001 v1.0
**Selected source of ownership:** `docs/PHASE_149O_19_4_HATP_MANDATORY_
INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md` §9.3

---

## 1. Baseline

- Latest completed phase: 149O.19.4 (HMIC-001 v1.0 implementation plan),
  commit `5e491c5a`, pushed, `origin/main..HEAD` = 0.
- HMIC-001 v1.0: VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS.
  Implementation plan: COMPLETE — READY FOR BOUNDED IMPLEMENTATION.
  Traceability: 144/144 requirements, 12/12 CIVC invariants, 32/32
  attacks mapped to a production owner/test owner/wave.
- `mandatory_consumption_implementation_independently_verified = False`
  (`hatp_mandatory_cutover.py:842-853`): unchanged by this phase.
- No certification implementation existed anywhere in `src/pcae/**`
  before this phase (confirmed by repository grep at initial inspection).
- Initial inspection confirmed: repo clean, `origin/main..HEAD = 0`,
  `pcae health` healthy, `pcae check` passed, `pcae status coherence`
  coherent, `pcae doctor task-memory` pre-existing warnings only
  (`tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, outside its allowed-file scope, not remediated here), `pcae
  push check` clean, `pcae runtime inspect` Observed/observe/unavailable,
  `pcae notify status` Telegram configured/enabled/ready, `pcae
  phase-report show --latest` and `pcae phase-report reconcile
  --phase-id 149O.19.4` both confirmed 149O.19.4 completed/complete with
  no mutation.

## 2. Stop Condition W-1 (Restated, Not Crossed)

149O.19.4 §10.3 froze a hard sequencing gate: the future HMIC validator
module must eventually join HMIC-001's frozen 22-file implementation-
identity set via a dedicated v1.1 contract amendment (independently
verified) before Wave F may wire it into the readiness ceiling. This
phase (Wave A) builds no validator, no wiring, and no admin writer; the
new module has zero effect on real readiness (nothing calls it). W-1 is
preserved unconditionally by this phase — see §9 (No-Go Confirmations).

## 3. Wave-A Requirement Ownership (Restated From 149O.19.4 §6)

| HMIC-REQ | Subject | Implemented by |
|---|---|---|
| 007 | Frozen terminology (Certification, CertificationRecord, Active-Certification Pointer, ...) | Module/class docstrings |
| 009 | Semantic walls not collapsed | Module docstring; no derived validity field anywhere |
| 010 | No `VALID_WITH_WARNING`/partial-credit status | `CertificationStatus` (exactly 9 members) |
| 024 | Certification model: append-only records + separate pointer file | `CertificationsDocument` / `CertificationBindingsDocument` |
| 029 | No signature field in v1.0 | `CertificationRecord` has no signature field |
| 031–035 | `CertificationRecord` closed schema, `status`/`revoked_at` consistency, immutability | `parse_certification_record`, `CertificationRecord` |
| 036–037 | `CertificationBinding` closed schema, exact-ID pointer | `parse_certification_binding`, `CertificationBinding` |
| 041–042 | Canonical serialization (`indent=2, sort_keys=True` + `\n`, UTF-8) | `canonical_serialize` |
| 071, 073 | `verification_record_digest`/descriptive phase ID, evidentiary only | Schema field only, no authority use |
| 106–108 | Closed 9-value Validation Status vocabulary + binary readiness mapping | `CertificationStatus`, `certification_status_satisfies_readiness` |
| 122–124 | No PB/RAE/capability construction anywhere in this wave | No such import exists in the module |
| 130–131, 133 | Audit-metadata-only fields, no secret material | Schema field set (§11 of the contract) has no secret-shaped field |
| 140 | Unknown future schema version fails closed | `_require_schema_version` |

Requirements 038–069 (identity derivation), 076–133-adjacent
store/admin/validation requirements, and 114–127 (Wave F wiring) are
explicitly **not** implemented this phase — they remain owned by Waves
B–F per 149O.19.4 §6/§9.3, unchanged.

## 4. Production Module

`src/pcae/core/hatp_mandatory_certification.py` (NEW, sole production
file this phase). Public surface:

- **Types:** `CertificationStatus` (9-value enum), `CertificationRecord`,
  `CertificationBinding`, `CertificationsDocument`,
  `CertificationBindingsDocument`.
- **Errors:** `HATPMandatoryCertificationError`,
  `CertificationMalformedError`.
- **Parsers:** `parse_certification_record`, `parse_certification_binding`,
  `parse_certifications_document`, `parse_certification_bindings_document`,
  `parse_certifications_document_from_bytes`,
  `parse_certification_bindings_document_from_bytes`.
- **Serializers:** `certification_record_to_document`,
  `certification_binding_to_document`,
  `certifications_document_to_document`,
  `certification_bindings_document_to_document`, `canonical_serialize`,
  `canonicalize_certifications_document`,
  `canonicalize_certification_bindings_document`.
- **Readiness helper:** `certification_status_satisfies_readiness`.

No filesystem I/O, no Git access, no network access, no hardware access.
The only `pcae.core` import is `repository_identity.
is_valid_repository_instance_id` (a pure format check, no authority
claim, no I/O — the identical narrow dependency
`human_approval_trusted_provenance.py`/`hatp_signed_evidence.py` already
take on the same function).

## 5. Model Inventory and Exact Field Sets

**`CertificationRecord`** (HMIC-REQ-032, 11 fields, `revoked_at`
present iff `status == "revoked"`): `certification_id`,
`repository_instance_id`, `canonical_deployment_root`,
`implementation_commit`, `implementation_scope_digest`,
`contract_versions`, `verification_record_digest`, `certified_at`,
`certified_by`, `status`, `revoked_at`.

**`CertificationBinding`** (HMIC-REQ-036, 3 fields, `active_certification_id`
optional): `repository_instance_id`, `canonical_deployment_root`,
`active_certification_id`.

**`CertificationsDocument`** / **`CertificationBindingsDocument`**
(whole-file wrappers, HMIC-REQ-025/031/036): `schema_version` (strict
positive int, currently `1`) + the entry list, each parsed via the
per-record/per-binding parser above with duplicate-key
(`certification_id` / `(repository_instance_id,
canonical_deployment_root)`) rejection at the document layer.

No convenience or derived field (`approved`, `allowed`, `trusted`,
`valid`, `executed`, `capable`, `ready`) exists on any type — mechanically
confirmed by `test_parsing_success_never_implies_validity`.

## 6. Immutability

`CertificationRecord`/`CertificationBinding`/`CertificationsDocument`/
`CertificationBindingsDocument` are `dataclass(frozen=True)` on every
field, including `status`/`revoked_at`. `contract_versions` is wrapped in
`types.MappingProxyType` in `__post_init__` (mirrors
`delivery_receipt.py`'s existing deep-immutability pattern) so the nested
mapping cannot be mutated in place even though the outer object is
frozen. HMIC-REQ-035's "every field but `status`/`revoked_at` immutable"
carve-out describes *storage-level* field mutation performed by a future
Wave C admin-tool write (a fresh atomic rewrite with those two keys
changed and every other byte identical) — not in-place Python attribute
mutation. No field of any type in this module is ever mutated in place.

## 7. Strict Parsing

- **Closed schema:** unknown top-level/per-record/per-binding fields
  rejected; missing required fields rejected (`revoked_at`/
  `active_certification_id` are the only fields legitimately absent).
- **Duplicate JSON keys:** rejected at any nesting level
  (`_load_json_no_duplicate_keys`, `object_pairs_hook`-based, mirrors
  `hatp_mandatory_cutover.py`'s identical helper).
- **Type strictness:** `bool` never satisfies an `int` field (Python's
  `bool`-is-`int`-subclass pitfall explicitly guarded);
  string-vs-number, `None`-vs-missing all rejected structurally by
  `isinstance` checks.
- **Version strictness:** document-level `schema_version` is a strict
  positive integer; only `1` is currently supported; any other value
  (including `True`) fails closed.
- **Identifier grammars:** `certification_id` /
  `implementation_scope_digest` / `verification_record_digest` /
  `active_certification_id` — lowercase 64-hex SHA-256
  (`^[0-9a-f]{64}$`, fullmatch); `implementation_commit` — 40- or
  64-hex lowercase Git SHA (mirrors
  `human_approval_trusted_provenance.py::_COMMIT_SHA_RE` exactly);
  `repository_instance_id` — UUID4 via the reused
  `repository_identity.is_valid_repository_instance_id` (accepts an
  uppercase lexical variant and retains it verbatim — the existing
  function's own documented behavior, not re-derived here);
  `canonical_deployment_root` — non-empty string only, no
  interpretation, no trim, no case-fold (it is legitimately path-shaped
  since it is `hatp_bootstrap.py::resolve_canonical_deployment_root`'s
  own output; the "no path-like ID" grammar of HMIC-REQ-055 applies to
  hash/UUID identifiers, not to this field, mirroring
  `hatp_bootstrap.py`'s own `_require_nonempty_str` treatment of the
  identical field).
- **Timestamp grammar:** `_TIMESTAMP_PATTERN =
  ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`, fully anchored,
  reused verbatim from `hatp_mandatory_cutover.py::_TIMESTAMP_PATTERN`,
  plus a `datetime.fromisoformat` calendar-validity check. Rejects: double
  `Z`, lowercase `z`, `Z+00:00`, garbage-before-offset, missing timezone,
  leading/trailing whitespace, invalid calendar dates. **Named residual
  behavior** (inherited verbatim from the reused precedent, not a new
  defect): on this interpreter, `datetime.fromisoformat` accepts only
  exactly-3-digit or exactly-6-digit fractional seconds, even though the
  lexical grammar admits 1–6 digits; 1/2/4/5-digit fractions are lexically
  well-formed but rejected by the calendar check. Covered explicitly by
  `test_certified_at_rejects_non_three_non_six_digit_fractions`.

## 8. Canonical Serialization

`canonical_serialize(document) -> bytes` = `json.dumps(document,
indent=2, sort_keys=True, allow_nan=False) + "\n"`, UTF-8 encoded —
identical to `hatp_mandatory_cutover.py::_atomic_write_json`'s
convention (HMIC-REQ-041/042), including its default (non-`ensure_ascii
=False`) Unicode-escaping behavior. `allow_nan=False` is an additive
hardening of HMIC-REQ-027's "strict JSON numeric domain" rule on the
write path, matching the equivalent `parse_constant` guard already
enforced on the read path.

- **Golden bytes:** asserted exactly (`test_canonical_serialize_exact_
  bytes_golden`, `test_canonical_serialize_key_order_always_sorted`).
- **Roundtrip:** `parse(canonical_bytes(model)) == model` and
  `canonicalize(parse(valid_noncanonical_input)) == canonical_bytes`,
  both asserted for `CertificationRecord`/`CertificationsDocument`/
  `CertificationBindingsDocument`.
- **Unicode:** default `ensure_ascii=True` escaping confirmed byte-exact
  (`café` → `café`), no normalization.
- **Numbers:** `NaN`/`Infinity`/`-Infinity` rejected on both the read
  path (`_load_json_no_duplicate_keys`) and the write path
  (`canonical_serialize`).

## 9. No-Go Confirmations

- No production source outside the one new module was modified:
  `git diff --name-only 484b1a97..HEAD -- src/pcae/` = exactly
  `src/pcae/core/hatp_mandatory_certification.py` (addition, not
  modification — confirmed via `git diff --name-status`).
- HMIC-001, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001,
  and PBPC-001 all remain byte-unchanged (`git diff --stat` empty for
  each).
- `hatp_mandatory_cutover.py` remains byte-unchanged; the hard-coded
  `mandatory_consumption_implementation_independently_verified = False`
  ceiling is untouched.
- The new module is never imported by `hatp_mandatory_cutover.py` (or
  any other existing production file), and imports no filesystem, Git,
  hardware, PB, RAE, agent, or CLI module itself.
- No certification artifact, active-certification pointer, or revocation
  record was created; no `certifications.json`/`certification-
  bindings.json` exists anywhere in the repository.
- No Cutover Record or activation marker was created or modified. No
  real `HATP_MANDATORY` activation occurred. No Class-B provisioning
  occurred. No Permission Broker behavior changed. `POL-005` remained
  unchanged. No `COMP-002` capability was implemented.
- No ordinary `pcae` CLI change; no `commands/agent.py`/`agent.py`
  change; no admin writer script exists.
- W-1 remains mandatory before any future readiness integration (Wave
  F); this phase does not begin, and could not begin, that gate.

## 10. Future HMIC Implementation Source Paths (W-1 Traceability)

`src/pcae/core/hatp_mandatory_certification.py` is **not** currently a
member of HMIC-001's 22-file frozen implementation-identity set
(HMIC-REQ-050). Per 149O.19.4 §10.3, this file (and whatever Wave D adds
to it as the validator function) will require a dedicated HMIC-001 v1.1
contract amendment, independently verified, before Wave F may wire its
future validator into the readiness ceiling. This phase does not claim,
imply, or perform that amendment.

## 11. Tests

- `tests/test_hatp_mandatory_certification_models.py` — 205 tests:
  schema closure (unknown/missing/duplicate/wrong-type/bool-version),
  identifier grammar attack matrix (path traversal, case, non-hex,
  Unicode homoglyph, NUL), timestamp grammar attack matrix (CPython
  3.9-specific cases), canonical serialization golden bytes + roundtrip
  + Unicode + NaN/Infinity rejection, immutability, structural equality,
  `CertificationStatus` vocabulary + readiness mapping, no-side-effects
  import check.
- `tests/test_phase_149o_19_5a_hmic_certification_models_canonical_
  parsing.py` — phase-boundary verification: production file allowlist,
  contract byte-identity (all 8 bound contracts), hard-coded-`False`
  byte-stability, W-1 no-wiring check, dependency closure, no
  certification state created, `CertificationStatus` vocabulary,
  mechanical Wave-A requirement-ID citation coverage, no import side
  effects, neighboring-module import smoke.

Both new test modules were added to `tests/conftest.py`'s
`FAST_GREEN_MODULES` (pure, deterministic, no filesystem/Git/network/
hardware I/O).

## 12. Regression

- `hatp_mandatory_cutover.py`, `repository_identity.py`,
  `human_approval_trusted_provenance.py` and their existing test suites
  are unaffected (byte-unchanged; import smoke confirmed in the phase
  test module).
- Fast Green: see phase-completion report for the exact passed/failed/
  skipped counts recorded at commit time.

## 13. Implementation Verdict

```
HMIC CERTIFICATION DATA MODELS + CANONICAL PARSING: IMPLEMENTED
— READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
```

## 14. Recommended Next Phase

149O.19.5B — HMIC Implementation + Contract Identity Derivation (Wave B:
`_FROZEN_AUTHORITY_BEARING_FILES` literal constant, repository/deployment/
commit/implementation-scope-digest/contract-version derivation). Not
pre-authorized by this phase; still no certification persistence, no
validator, no writer, no readiness integration.

## 15. Status Restatement (Unchanged By This Phase)

B-149O.19.3-1: INDEPENDENTLY CONFIRMED CLOSED (unchanged). B-149O-1..4:
INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED (unchanged). HATP
production: **NOT READY**. Runtime: **Observed / observe / unavailable**.
