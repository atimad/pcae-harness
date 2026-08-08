# Phase 149O.16.1 — Publication Coordinator Python 3.9/3.10 Timestamp Compatibility Repair

## Phase Type

NARROW PRODUCTION REPAIR. Repairs exactly one pre-existing, unrelated
prerequisite defect (`149O.12B-Obs-PY39-1`) identified as a non-blocking
finding during 149O.16's HMRC-001 independent verification. Does not
implement HMRC-001, modify any frozen contract (HMRC-001, HSCE-001,
HATP-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001), or touch Permission
Broker / rollback dispatch / signing semantics / Class-B provisioning /
HATP activation.

## Baseline

- Latest completed phase entering 149O.16.1: **149O.16** — HATP
  Mandatory Production Consumption Contract Independent Verification
  (commits `84cddf90`, `742f65f8`, `08b4faef`, `0cec4e0b`, `44c3d024`).
- Repo clean; `origin/main..HEAD` = 0 at phase start.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: pre-existing warnings only (7
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, unrelated, not remediated here — outside allowed-file scope).
  `pcae push check`: clean (nothing to push). `pcae runtime inspect`:
  Observed / observe / unavailable. `pcae notify status`: Telegram
  configured/enabled/ready.
- HMRC-001 v1.0 verdict entering this phase: VERIFIED WITH NON-BLOCKING
  FINDINGS — CONFORMS. Implementation readiness: READY FOR
  IMPLEMENTATION PLANNING. HATP production: NOT READY. Runtime:
  Observed / observe / unavailable.

## Finding Reconstruction

`pcae.governance.publication.coordinator._parse_timestamp` (Phase 144C)
called bare `datetime.fromisoformat(value)` with no normalization of a
trailing UTC `"Z"` designator. `datetime.fromisoformat` only began
accepting a trailing `"Z"` in Python 3.11 (CPython bpo-41762). On this
repository's minimum-supported Python 3.9/3.10, any canonical
`..._chgr_timestamp`-style value ending in `"Z"` passed into this
function raised `ValueError`, which both call sites in
`_validate_authorization_freshness` map to `StaleAuthorizationError` —
so a syntactically valid, freshly-authorized publication would be
refused as if it were stale, on 3.9/3.10 only. This blocks fresh CHGR
Decision / RAE Binding creation via the publication coordinator on
those runtimes, a prerequisite for future HMRC mandatory-consumption
implementation and verification work.

The defect predates HMRC-001, is outside HSCE-001 semantics, and does
not invalidate HMRC-001's own verified conformance.

## Supported Python Range

`pyproject.toml`: `requires-python = ">=3.9"`. Python 3.9 and 3.10
remain supported; the repair is required.

## Affected Function / Callers

- Affected: `pcae.governance.publication.coordinator._parse_timestamp`
  (`src/pcae/governance/publication/coordinator.py`).
- Direct callers: `PublicationCoordinator._validate_authorization_freshness`
  (two call sites: `package.built_at`, `event.invoked_at`), both already
  wrapped in `try/except ValueError → StaleAuthorizationError` — this
  repair changes no error-mapping behavior, only which inputs reach that
  `except` clause.
- No other production parser in the repository shares this defect:
  `pcae.core.rollback_approval_evidence._parse_iso_timestamp` already
  normalizes terminal `"Z"` (the existing safe precedent this repair
  mirrors). No other `datetime.fromisoformat` call site in `src/pcae/`
  parses externally-supplied ISO-8601 timestamps that may end in `"Z"`
  without existing normalization (verified by direct inspection of the
  publication and RAE modules; not broadened based on grep alone).

## Pre-Repair Reproduction

This environment's interpreter is Python 3.14.5; no Python 3.9 or 3.10
interpreter was available (`pyenv`, `/opt/homebrew/bin/python3.9`,
`/opt/homebrew/bin/python3.10` all absent). `datetime.fromisoformat`
accepts `"Z"` directly on 3.14, so a live 3.9/3.10 failure could not be
triggered in this environment. The defect is instead confirmed by:

- direct source inspection of the pre-repair function (bare
  `fromisoformat(value)`, no `"Z"` handling);
- the documented, version-gated CPython stdlib change (3.11+ only);
- this repository's own pre-existing, independently-written test-layer
  workaround fixtures (`tests/test_hatp_signing_ceremony.py`,
  `tests/test_phase_149o_12c_hsce_attack_matrix.py`,
  `tests/test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py`),
  each of which pre-dates this phase and documents having reproduced the
  failure on the repository's `.venv` (pinned to 3.9-range) before this
  repair existed.

This is a source-compatible repair based on documented stdlib behavior;
direct empirical Python 3.9/3.10 runtime verification was unavailable in
this environment. Same limitation applies to Python 3.10.

## Existing Safe Precedent

`src/pcae/core/rollback_approval_evidence.py::_parse_iso_timestamp`:

```python
text = value[:-1] + "+00:00" if value.endswith("Z") else value
parsed = datetime.fromisoformat(text)
```

## Selected Repair

`_parse_timestamp` now normalizes a terminal `"Z"` to `"+00:00"`
immediately before `datetime.fromisoformat`, identically to the RAE
precedent above:

```python
def _parse_timestamp(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
```

No wholesale parser replacement, no new dependency, no new timestamp
format, no change to canonical serialization or `_now_iso()`.

## Semantic Boundaries Confirmed

- **Terminal `"Z"` only**: `value.endswith("Z")` — an interior `"Z"`
  elsewhere in the string is never touched.
- **Case sensitivity**: only uppercase `"Z"` is normalized; a lowercase
  `"z"` remains rejected (`ValueError`), matching the canonical producer
  format and the RAE precedent's own domain.
- **Existing `"+00:00"` / offset input**: unchanged — `endswith("Z")` is
  `False`, so the string passes through untouched; no double
  normalization.
- **Non-UTC offset input** (e.g. `...+02:00`): unchanged — never matches
  `endswith("Z")`; retains its own offset, never converted to UTC.
- **Fractional seconds** (`...56.123Z`): normalized the same way;
  `fromisoformat` parses the fractional component unchanged.
- **Invalid inputs** (empty string, non-ISO text, double timezone
  suffix, lowercase `z`, malformed date/time components): all still
  raise `ValueError` — the parser is not made more permissive.
- **Naive timestamps** (no timezone): unchanged — still accepted and
  coerced to UTC exactly as before (`parsed.tzinfo is None` branch,
  untouched by this repair).
- **Error type**: unchanged — `ValueError` propagates identically to
  both call sites' existing `except ValueError` handling.

## CHGR Decision / RAE Binding Path

`PublicationCoordinator.authorize()` → `PublicationCoordinator.execute()`
→ `_validate_authorization_freshness()` → `_parse_timestamp()` on both
`package.built_at` and `event.invoked_at`. A new regression test
(`test_chgr_publication_with_z_suffixed_timestamps_succeeds`) exercises
this exact path end-to-end with real `"Z"`-suffixed timestamps on both
fields and confirms `PublicationExecutionResult.success is True` — no
monkeypatch, real production `_parse_timestamp`. RAE Binding creation
(`rollback_approval_evidence.py`) was not touched by this repair (its
own parser already handled `"Z"` correctly) and is unaffected.

## Production Diff Classification

Single production file changed: `src/pcae/governance/publication/coordinator.py`.
Single hunk inside `_parse_timestamp`: one new comment (rationale) plus
the one-line `"Z"` → `"+00:00"` normalization before the existing
`fromisoformat` call. Classification: `Z_SUFFIX_COMPATIBILITY` = 1,
`COMMENT/DOCSTRING` = 0 (comment is part of the same hunk),
`UNRELATED` = 0.

## Historical Test-Only Monkeypatch Workaround

Three pre-existing test files carried an identical autouse `monkeypatch`
fixture patching `coordinator._parse_timestamp` with a `"Z"`-tolerant
replacement, to let their own CHGR/RAE fixtures run on Python 3.9 before
this repair existed:

- `tests/test_hatp_signing_ceremony.py`
- `tests/test_phase_149o_12c_hsce_attack_matrix.py`
- `tests/test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py`

These fixtures are **retained**, not removed, in this phase — they are
now harmlessly idempotent (the monkeypatch replacement is
behaviorally identical to the now-repaired production function) and
their removal is not necessary to prove repair consumption. This
phase's own new test file
(`tests/test_phase_149o_16_1_publication_coordinator_timestamp_compatibility_repair.py`)
exercises the real, unpatched production `_parse_timestamp` directly,
with no monkeypatch, proving the repair independently of those
fixtures. `tests/test_phase_149o_13_...py`'s own
`test_python39_z_suffix_defect_independently_reproduced` test asserted
the *pre-repair* source shape (`"fromisoformat(value)" in source`,
`"endswith" not in source`) as its reproduction evidence; since that
assertion is now false by construction (the repair changed the source
it inspects), it was updated in place
(`test_python39_z_suffix_defect_repaired_by_149o_16_1`) to assert the
*repaired* source shape and to call the real production function
directly — same 149O.5-F-3 "update in place, never delete" convention
already used elsewhere in this repository's phase-scoped test suites.

## Regressions Required by This Repair

Two other pre-existing phase-scoped tests asserted a fixed
production-file allowlist / byte-unchanged boundary that did not yet
include `coordinator.py`, since no prior phase had touched it:

- `tests/test_phase_149o_12b_hatp_signing_ceremony_implementation.py::TestProductionFileAllowlist`
  (`_EXPECTED_PRODUCTION_FILES`, cumulative diff since the 149O.12A
  baseline commit) — updated to add
  `src/pcae/governance/publication/coordinator.py`, with a docstring
  note following the exact same 149O.12C/149O.5-F-3 precedent already
  documented in that file for widening this allowlist when a later,
  separately-authorized phase legitimately touches a new production
  file.
- `tests/test_phase_149o_1g_hatp_proof_models_canonical_serialization.py::test_only_expected_production_files_changed`
  and
  `tests/test_phase_149o_14_hatp_ag3_ag5_mandatory_production_consumption_architecture.py::TestNoProductionSourceModified`
  both diff against **`HEAD`** (working tree vs. last commit) rather
  than a fixed historical baseline; they report a "failure" only while
  this phase's own commit is not yet made, and resolve to a clean pass
  once this phase's production change is committed (`git diff HEAD`
  and `git status --porcelain` both go clean against the new HEAD). No
  edit to either file was required or made.

## Test Results

- **Direct parser tests** (12, new file, no monkeypatch): terminal `"Z"`
  accepted; `"Z"` and `"+00:00"` produce an identical instant; existing
  `"+00:00"` input unchanged; fractional-second `"Z"` accepted;
  non-UTC offset unchanged and not converted; lowercase `"z"` still
  rejected; empty/malformed/double-timezone-suffix inputs still
  rejected; production-source shape assertion; real CHGR path
  end-to-end success. **12/12 passed.**
- **Pre-repair attribution**: `git stash` of the production change
  reproduces one new-test failure
  (`test_production_diff_is_terminal_z_normalization_only`, a
  source-shape assertion) and leaves the rest passing on this 3.14
  interpreter (expected — 3.14 already accepts `"Z"` natively; the
  source-shape assertion is the attribution proof available in this
  environment). Repair restored; full new suite green again.
- **Targeted regression** (144C, HATP signing ceremony, 149O.12B,
  149O.12C, 149O.13, 149O.15, 149O.16, this phase's new file): **254
  passed, 2 skipped**, zero failures.
- **Fast Green** (`pytest -m fast_green -k 149o`, excluding the
  pre-existing fido2-dependent collection error): **256 passed, 2
  skipped** after this phase's own commit (the two `HEAD`-diff-based
  allowlist tests above pass once committed; see above).

## No-Go Confirmations

- Only `src/pcae/governance/publication/coordinator.py` was modified in
  `src/pcae/**`; `git diff --name-only -- src/pcae/` against the
  phase-entering commit shows exactly this one file.
- HMRC-001, HSCE-001, HATP-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001
  all remain byte-unchanged.
- No HMRC-001 implementation was started. No Cutover Record was
  created. No AG3/AG5 mandatory-consumption wiring was added. No
  rollback dispatch, Permission Broker, or POL-005 behavior changed.
  No COMP-002 capability was implemented. No Class-B provisioning
  occurred. No HATP production activation occurred.
- B-149O-1..4 remain INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED, unchanged by this
  phase.
- HATP production remains NOT READY. Runtime remains Observed /
  observe / unavailable.

## Finding Disposition

`149O.12B-Obs-PY39-1`: entering status OPEN / PRE-EXISTING. Resulting
status: **REPAIRED AT IMPLEMENTATION LEVEL — PENDING INDEPENDENT
VERIFICATION** (a separate 149O.16.2 verification phase is recommended
below, per this repository's Chapter 149 separate-verification
convention; no direct precedent was found for combining a compatibility
repair and its independent verification into a single phase).

## Repair Verdict

**PUBLICATION TIMESTAMP PYTHON 3.9/3.10 COMPATIBILITY: REPAIRED — READY
FOR INDEPENDENT VERIFICATION.**

## Recommended Next Phase

**149O.16.2 — Publication Coordinator Timestamp Compatibility
Independent Verification** — independently reproduce the pre-repair
defect, confirm terminal-`"Z"` handling, confirm `"+00:00"`/offset
non-regression, exercise a fresh CHGR Decision / RAE Binding path, and
verify no unrelated production changes, before proceeding to **149O.17
— HATP Mandatory Production Consumption Implementation Plan**.
