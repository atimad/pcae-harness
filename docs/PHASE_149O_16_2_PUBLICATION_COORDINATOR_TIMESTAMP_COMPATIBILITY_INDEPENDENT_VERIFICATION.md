# Phase 149O.16.2 — Publication Coordinator Timestamp Compatibility Independent Verification

## Phase Type

INDEPENDENT VERIFICATION ONLY. Independently determines whether 149O.16.1
correctly repaired the Python 3.9/3.10 compatibility defect
(`149O.12B-Obs-PY39-1`) in
`pcae.governance.publication.coordinator._parse_timestamp`. Modifies no
production source, no contract, no rollback/Permission Broker behavior.
Adds exactly one new test file and this document.

## Baseline

- Latest completed phase entering 149O.16.2: **149O.16.1** — Publication
  Coordinator Python 3.9/3.10 Timestamp Compatibility Repair (commits
  `56d1ca73`, `341cb1d7`, `a6eafcb8`, `5b9e78f1`, `2e2b366e`).
- Repo clean; `origin/main..HEAD` = 0 at phase start.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: pre-existing warnings only (7
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this
  phase, unrelated, not remediated here). `pcae push check`: clean
  (nothing to push). `pcae runtime inspect`: Observed / observe /
  unavailable. `pcae notify status`: Telegram configured/enabled/ready.
- HMRC-001 v1.0 entering this phase: VERIFIED WITH NON-BLOCKING FINDINGS
  — CONFORMS. HATP production: NOT READY.

## Supported Python Range (Reconfirmed)

`pyproject.toml`: `requires-python = ">=3.9"` (independently re-read, not
copied from 149O.16.1's report). Python 3.9/3.10 remain supported.

## Current Interpreter (Reconfirmed, and a Correction to 149O.16.1)

**149O.16.1's own report recorded only Python 3.14.5 as available in its
session and stated no 3.9/3.10 interpreter existed locally.** This phase
independently reconfirms the interpreter and finds that claim was an
artifact of *how* the session was invoked, not a fact about the
environment:

- `/opt/homebrew/bin/python3.14` → Python 3.14.5 (present; likely first
  on an interactive shell's `PATH`).
- `/usr/bin/python3` (Apple Command Line Tools) → **Python 3.9.6**.
- This repository's own `.venv` (`pyvenv.cfg`: `home =
  /Library/Developer/CommandLineTools/usr/bin`, `version = 3.9.6`) is
  built on that same **Python 3.9.6** interpreter.

Every command in this verification (`pytest`, the new independent test
file, the full regression sweep below) ran under `.venv` — i.e., under
real CPython 3.9.6, not a simulation. `python3.10` is not installed
anywhere on this machine (confirmed: `which python3.10` → not found), so
Python 3.10 empirical coverage remains **NOT EMPIRICALLY VERIFIED ON
PYTHON 3.10 IN THIS ENVIRONMENT** — but Python 3.9 empirical coverage,
which 149O.16.1 stated was entirely unavailable, is now genuine, not
structural.

## Pre-Repair Source Reconstruction (from Git History)

`git show 44c3d024:src/pcae/governance/publication/coordinator.py`
(the commit immediately preceding 149O.16.1) shows:

```python
def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
```

No `endswith` check, no `"Z"` literal — confirmed independently from Git
history, not trusted from 149O.16.1's own report.

## Repaired Source Reconstruction (Current HEAD, Direct Inspection)

```python
def _parse_timestamp(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
```

Confirmed via `inspect.getsource` in the new test suite — terminal-`Z`-only
normalization, no wholesale `.replace("Z", ...)`, no new dependency.

## Production Diff (Independently Reconstructed)

`git diff 44c3d024 HEAD -- src/pcae/` shows exactly one file:
`src/pcae/governance/publication/coordinator.py`. The hunk is exactly one
removed line (`parsed = datetime.fromisoformat(value)`) and two added
code lines (the normalization + the same `fromisoformat` call against
`text`), plus a four-line explanatory comment. Classification:

| Hunk | Class |
|---|---|
| `text = value[:-1] + "+00:00" if value.endswith("Z") else value` | Z_SUFFIX_COMPATIBILITY |
| `parsed = datetime.fromisoformat(text)` | Z_SUFFIX_COMPATIBILITY |
| Explanatory comment | COMMENT/DOCSTRING |

`UNRELATED = 0`.

## Safe Precedent

`pcae.core.rollback_approval_evidence._parse_iso_timestamp` contains the
identical normalization line:
`text = value[:-1] + "+00:00" if value.endswith("Z") else value`
— confirmed by direct source inspection (`inspect.getsource`), not by
assuming textual identity was required. Semantic parity confirmed.

## Direct Parser Verification (Real Function, No Monkeypatch)

All of the following were exercised against the real, unpatched
`pcae.governance.publication.coordinator._parse_timestamp` under CPython
3.9.6:

| Case | Result |
|---|---|
| Terminal uppercase `Z` (`...56Z`) | Accepted; `tzinfo` is UTC |
| `Z` vs. `+00:00` for the same instant | Identical parsed `datetime`, identical `utcoffset()` |
| Fractional seconds + `Z` (`.123Z`, `.123456Z`) | Fraction preserved exactly, no truncation |
| Non-UTC offset (`+02:00`) | Unchanged; not forced to UTC; same instant as UTC equivalent |
| `+00:00` input | Unchanged; `isoformat()` round-trips exactly, no double suffix |
| Lowercase `z` | Still rejected (`ValueError`) — intentionally unchanged |
| `Z` + trailing garbage (`Zfoo`, `Z `) | Still rejected |
| Interior `Z` (not terminal) | Still rejected — normalization is `endswith`-gated only |
| Empty / malformed / out-of-range values | Still rejected (`ValueError`) |
| Naive timestamp (no offset) | Still coerced to UTC via the pre-existing, untouched `parsed.replace(tzinfo=timezone.utc)` line |
| Error type for all invalid inputs | `ValueError` throughout, unchanged |

## Real `PublicationCoordinator` / Fresh CHGR / RAE Path (No Monkeypatch)

- `PublicationCoordinator.authorize` → `execute` exercised directly with
  real `Z`-suffixed `built_at`/`invoked_at` — `PublicationExecutionResult.
  success` is `True`.
- The identical path with `+00:00`-suffixed timestamps (the
  already-accepted pre-repair case) also succeeds, confirming no
  authority-semantic change for already-accepted input.
- **`pcae.core.rollback_approval_evidence.create_rollback_approval_decision`
  — the sole real production entry point for CHGR Decision creation —
  always builds its `built_at` via `chgr_envelope.chgr_timestamp(...)`,
  which always emits a `Z`-suffixed string.** This means every real call
  to this function was broken on Python 3.9/3.10 before 149O.16.1, not
  merely a contrived test input. Exercised directly here (no monkeypatch):
  succeeds, and `create_rollback_approval_binding` was then exercised
  against the resulting Decision reference (real AG3 Binding), confirming
  the coordinator no longer prevents fresh governance-state creation.

## Historical Monkeypatch Inventory

Three pre-existing test-only fixtures monkeypatch
`coordinator._parse_timestamp` to a Z-tolerant version:
`test_hatp_signing_ceremony.py`, `test_phase_149o_12c_hsce_attack_matrix.py`,
`test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py`.
All three remain, unremoved (out of this phase's scope — verification
only). The new independent verification test file
(`test_phase_149o_16_2_...py`) imports none of them and exercises the
real production function directly, proving the repair itself — not the
fixtures — is what makes Z-suffixed input work.

## Updated Historical Test Audit

- `test_phase_149o_12b_hatp_signing_ceremony_implementation.py`: its
  `_EXPECTED_PRODUCTION_FILES` allowlist gained exactly
  `src/pcae/governance/publication/coordinator.py` and nothing else —
  confirmed by direct diff inspection, no broad wildcard.
- `test_phase_149o_13_...py`: its defect-reproduction test was updated to
  record the repaired status rather than deleted; confirmed no unrelated
  assertion in that file was weakened (full file still 100% passing
  except the one pre-existing, environment-assumption failure below).

## Regression Results

All run under `.venv` (CPython 3.9.6):

| Suite | Result |
|---|---|
| New independent verification file (33 tests) | 33 passed |
| HATP signing ceremony + 149O.12B/12C/13/15/16 + 149O.16.1's own file | 294 passed, 2 failed (both pre-existing, see below) |
| Publication / rollback-approval-evidence / CHGR / report-trust (`-k` sweep, 1400+ tests) | 1400 passed, 1 skipped, 6 failed (all pre-existing, see below) |
| Repository-wide Fast Green (`-m fast_green`) | 5177 passed, 2 failed, 1 skipped |

### Pre-Existing Failures (Confirmed Unrelated to This Phase)

Each of the following was reproduced identically with this phase's new
test file stashed out (`git stash -u`), proving none is a regression
introduced by 149O.16.1 or 149O.16.2:

1. `test_phase_149o_13_...py::test_python39_z_suffix_defect_repaired_by_149o_16_1`
   — asserts `sys.version_info >= (3, 11)`, an environmental assumption
   from when this suite was authored under a 3.14 interpreter; now
   genuinely false under CPython 3.9.6. Pre-existing test fragility
   **unmasked** by this phase's discovery that `.venv` is actually 3.9.6
   — not a defect in the repair itself (all of that same file's other
   tests, including the repaired-behavior assertions, pass).
2. `test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py::
   test_no_production_source_modified_this_phase` — asserts no
   `src/pcae/` file changed since **149O.16's** own phase-entry commit;
   149O.16.1 (a later, separate phase) legitimately changed
   `coordinator.py` afterward. Expected staleness of a phase-scoped
   assertion, not a regression.
3. `test_cltr_authority_136ah_publication.py` /
   `test_cltr_authority_136ai_publication_independent.py` (wheel-packaging
   checks) and four tests in
   `test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`
   (a known, pre-existing CHGR/publication-receipt forgery finding,
   B-149M-2-class, unrelated to timestamp parsing) — all fail identically
   with or without this phase's changes.

### Non-Blocking Finding: Pre-Existing Python 3.9 `fromisoformat` Quirk

Independently discovered by this phase (not documented by 149O.16.1):
on CPython 3.9.6, `datetime.fromisoformat` silently ignores any single
stray character immediately preceding an otherwise-valid `+00:00` offset
(e.g. `"...56X+00:00"` parses successfully). Because the repair
unconditionally strips exactly one trailing `"Z"`, a malformed
double-`Z` input (`"...56ZZ"`) normalizes to `"...56Z+00:00"`, which this
same stdlib quirk then accepts — whereas the pre-repair bare
`fromisoformat("...56ZZ")` call correctly raised `ValueError`.

This is **not** a defect specific to 149O.16.1's repair: the identical
"safe precedent" it deliberately mirrors,
`rollback_approval_evidence._parse_iso_timestamp`, exhibits the exact
same behavior for the exact same input, and has done so since before
this phase (untouched by 149O.16.1). It also does not reproduce on
Python 3.14 (`fromisoformat` there correctly rejects both forms),
confirming it is a Python-3.9-only CPython stdlib interaction, not a
logic defect in either module's normalization line. Disposition:
**pre-existing, repository-wide, non-blocking environmental finding** —
out of scope for a narrow follow-up repair to 149O.16.1 specifically,
since fixing it in `coordinator._parse_timestamp` alone without also
fixing the already-shipped precedent it mirrors would create the two
functions' first behavioral divergence. Recommended narrow follow-up (not
performed in this verification-only phase): a single shared, stricter
`Z`-suffix normalization helper for both call sites, if this repository
chooses to close the quirk.

## Scope Boundaries Confirmed

- `git diff --name-status 44c3d024..HEAD -- src/pcae/` limited to
  `coordinator.py` only, throughout 149O.16.1; this phase (149O.16.2)
  adds zero production files.
- Byte-identity confirmed via `git diff --stat` against the phase-start
  commit for: `HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`,
  `HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
  `ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`,
  `REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`,
  `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
  `PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`,
  `HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001) — all
  empty diffs.
- `hatp_signing_ceremony.py`, `hatp_ag_authority.py`, `hatp_signed_evidence.py`,
  `hatp_evidence_store.py`, `agent.py`, `commands/agent.py` — all empty
  diffs since the phase-start commit.
- No `permission_broker`-named production file touched. No `cutover`
  string introduced anywhere in the `src/pcae/` diff. No new production
  files added.

## Verification Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — PUBLICATION COORDINATOR
TIMESTAMP COMPATIBILITY REPAIR CONFORMS.**

## Finding Disposition

- `149O.12B-Obs-PY39-1`: **INDEPENDENTLY CONFIRMED RESOLVED** — proven by
  direct source inspection *and* live execution under the repository's
  actual Python 3.9.6 `.venv` (not merely structural reasoning; this
  phase corrects 149O.16.1's belief that no such interpreter was
  available).
- Historical monkeypatch fixtures (3): **NON-BLOCKING CLEANUP DEBT**,
  unremoved, harmlessly idempotent.
- Pre-existing double-`Z`/stray-character `fromisoformat` quirk on Python
  3.9 (shared with the safe precedent): **NON-BLOCKING, PRE-EXISTING,
  ENVIRONMENTAL** — not introduced by this repair.
- No further timestamp prerequisite remains for HMRC implementation
  planning.

## Recommended Next Phase

**149O.17 — HATP Mandatory Production Consumption Implementation Plan.**

## Unchanged Facts

B-149O-1..4 remain INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED. HMRC-001 v1.0 remains
VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS (byte-unchanged). HATP
production remains NOT READY. Runtime remains Observed / observe /
unavailable.
