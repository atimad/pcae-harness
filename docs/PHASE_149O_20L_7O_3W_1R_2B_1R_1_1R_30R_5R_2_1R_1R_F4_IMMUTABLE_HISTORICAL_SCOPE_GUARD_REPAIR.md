# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R

## F-4 Immutable Historical-Scope Guard Repair

## Verdict

**REPAIR COMPLETE. F-4: REPAIRED; FRESH INDEPENDENT VERIFICATION PENDING. F-5:
OPEN / UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 v1.0 accepts the exact phase identifier above. It is the direct
repair-suffix successor of the completed BLOCKED `.30R.5R.2.1R.1` phase; no
identifier discrepancy was found.

## Immutable lineage and scope evidence

- `P = 00c077f6ff3389a8c91d503fb5341ec72775f8e0` — finalized F-3 repair.
- `V = R0 = 3fbc12d7ad671ed6c9348cb29ffb5c2d35447e5f` — finalized BLOCKED
  predecessor and this repair's entry.
- `a727dbf4f160f904836905d3cb4adeba91953676` — finalized `.30R.4R`
  contract-reconciliation head and immutable lower bound.
- `5b6b4013a69ffcb366209b12c495571917bb5ccc` — finalized `.30R.4R.1`
  implementation head and immutable upper bound. Its committed historical
  completion metadata identifies phase `.30R.4R.1`, status `completed`, and
  entry `a727dbf4`; Git proves a linear five-commit phase interval.

## F-4 reconstruction and repair

The retained node
`test_35_no_production_or_script_implementation_changed` combined two diffs
whose upper bound was live `HEAD` (one explicit and one implicit). Its intended
semantic invariant was narrower: `.30R.4R.1` added or changed only its exact
eight enumerated helper/launcher/admin/verifier files after finalized
`.30R.4R`. Later legitimate CTAP2 work therefore became a false violation.

The minimum repair adds the immutable `.30R.4R.1` finalized object and changes
both source-scope reads to the exact `a727dbf4..5b6b4013` range. The expected
set remains exact and unchanged. Git independently derives exactly those eight
files. An injected `src/pcae/unauthorized.py` member still fails the subset
assertion. Current and future descendants cannot change either fixed Git tree,
so no successor allowlist, phase-prefix rule, wildcard, glob, or `fnmatch` is
needed.

## Verification

- Exact owner suite plus fresh 43-case repair suite: **85 passed**.
- `.30R.5R.2` predecessor + F-3 repair + latest IV evidence + fresh repair:
  **214 passed**.
- Broad presentation/RHAMP/FIDO2/PAWA/PPA/verifier/Gate sweep: **1,312 passed,
  3 failed, 1 skipped, 1 intentionally deselected historical finding node**.
  All three failures reproduce identically at immutable `R0`: two historical
  `object.__new__` adversarial finding demonstrations and one historical HMIC
  moving-digest assertion. They are pre-existing and not F-4 attributable.
- The preserved historical `.30R.5R.2.1` F-3 demonstration remains 84 pass / 1
  expected obsolete finding node at current history; its historical BLOCKED
  verdict is unchanged.
- No existing test definition was removed or renamed; no skip, skipif,
  `pytest.skip`, xfail, wildcard, glob, or `fnmatch` broadening was introduced.
- Production source, scripts, `pyproject.toml`, and normative contracts are
  byte-unchanged from `R0`.

## Required separations

F-5 remains read-only and untouched: the platform-fixed production protected
root `/Library/Application Support/PCAE/HPAC/protected-root` remains absent.
No helper was installed or configured and no generation was created. No human
APPROVE/REJECT, YubiKey touch/PIN, real presentation, assertion, evidence,
PRODUCTION principal, or Gate 5 certification occurred.

H-1 historical real-hardware verification, H-2 software IV, F-2 software IV,
and F-3 independent verification remain preserved. FIDO2/YubiKey and local TTY
remain supported profiles, not exclusive/global requirements. Mechanism-neutral
human authentication and protected approval, including a mobile-only profile,
remain open future architecture.

Runtime remains `not_implemented / Observed / observe / unavailable`, zero
plugins/capabilities, and first external effect absent. N-16-6 and N-16-7 are
untouched. N-16-5 remains NOT CLOSED.

## Sequenced successors — derived, not begun

1. `.30R.5R.2.1R.1R.1` — Independent Verification of the F-4 Immutable
   Historical-Scope Guard Repair.
2. `.30R.5R.2.1R.1R.2` — Governed Production Protected-Root and
   Protected-Presentation Helper Deployment Preparation.
3. `.30R.5R.2.1R.1R.2.1` — Independent Verification of Production Helper
   Installation and Current-Generation Trust State.
4. `.30R.5R.2.1R.1R.3` — Final Real Protected-Presentation Human Election and
   Presentation-Bound N-16-5 Certification and Closure.

Each requires separate human authorization. None was started.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
