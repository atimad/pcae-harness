# Phase 149O.20L.7O.3C.3.2 Complete — Auto-Publish Corrupt-Store Repair Independent Verification

**Verdict: `B-149O.20L.7O.3C.3-1` CLOSED. HISTORICAL CRASH INDEPENDENTLY
REPRODUCED FROM REAL PRE-REPAIR SOURCE. UNRELATED CORRUPT SESSION
ISOLATED (NO CRASH). RELEVANT CORRUPT SESSION FAILS CLOSED
(`application_error`, no fabricated absence). PLAN B+ INDEPENDENTLY
VERIFIED. DUPLICATE-`subject_ref` REMAINS NON-BLOCKING/ACCEPTED-DEBT,
INDEPENDENTLY RE-DERIVED FROM THE PRIMARY-SOURCE CONTRACT. ZERO
PRODUCTION SOURCE MODIFIED. RUNTIME: Observed / observe / unavailable.
RELEASE: STILL STOPPED — RECOMMENDS 149O.20L.7O.3C.4.**

## Summary

Independently verifies (does not trust) 3C.3.1's repair of BLOCKING
finding `B-149O.20L.7O.3C.3-1`. Per the governing brief's methodology
("re-derive, reproduce, attack — do not trust"), this phase wrote a
brand-new, 29-test suite (`tests/test_phase_149o_20l_7o_3c_3_2_
auto_publish_corrupt_store_repair_independent_verification.py`) that
imports no fixture or test function from 3C.3.1's own suite.

**Historical crash — independently reproduced from real source, not
text/`git show` comparison:** a disposable `git worktree` was checked
out at the fixed pre-repair commit (`2fd7fe3a`), and the literal
installed `pcae phase complete` CLI entry point was executed against it
(via `PYTHONPATH` pointing at the worktree's `src`, no third-party
dependency differing between the two commits) with a fresh isolated
fixture repository and an unrelated corrupted Interactive Workflow
session file. Result: exit code 1, a genuine, full Python traceback
terminating in `SessionStoreCorruptError`, tracing exactly through
`run_phase_complete` → `auto_publish_confirmed_session` →
`find_confirmed_session` → `find_session_by_subject_ref` →
`SessionCoordinator.load_session` → `FilesystemSessionRepository.load`.
The identical fixture, run against current repaired `HEAD`, completes
cleanly: exit 0, disclosed `application_error` outcome, `Phase
complete.` printed.

**Independent re-derivation of unrelated-vs-relevant corruption
semantics:** direct reading of `FilesystemSessionRepository._unwrap`
confirms every malformed-record shape (invalid JSON, truncated JSON, an
empty file, a bare scalar, a JSON array, a missing-field object, a wrong
schema version, a mismatched session id) collapses to the same
`SessionStoreCorruptError` — there is no finer corruption taxonomy for
the repaired scan loop to use. The verification suite proves the actual
rule directly: a genuinely readable match for the requested subject
wins unconditionally, regardless of corruption elsewhere, ordering, or
record count; absent such a match, *any* corruption anywhere in the
store — including a record independently confirmed to have no possible
relationship to the requested subject — fails closed identically to
genuinely relevant corruption. This is recorded as a documentation-
precision finding (not blocking, no repair needed): the guarantee this
repair actually provides is "no crash, ever" and "a real match is never
shadowed," not "corruption is correctly attributed to the right
subject before failing closed" — which architecturally cannot be true,
since identity recovery requires successful parsing.

**Duplicate-`subject_ref` — independently re-adjudicated from the
primary-source contract**, not by re-trusting 3C.3's prior report:
`SessionApplicationService.create_session`/`FilesystemSessionRepository.
create` enforce uniqueness only on the generated `session_id`
(`uuid4`); nothing anywhere in the frozen IWC-001-layer contract rejects,
warns on, or detects a second session sharing an existing `subject_ref`
— directly demonstrated by a fresh test creating two such sessions
successfully. **Verdict: NON-BLOCKING / ACCEPTED-DEBT**, unrepaired,
consistent with (and independently confirming) 3C.3/3C.3.1's carried-
forward disposition.

**Production source modified: NONE.** This phase's only source changes
are the new independent test file, this phase's own document, and
lifecycle/metadata files.

**Tests:** 29 new, fresh (`tests/test_phase_149o_20l_7o_3c_3_2_...py`),
all passing. Regression evidence: 3C.3.1's own 14-test suite, 3C.3's own
15/22-test suites, 3C.2's 22-test suite — all re-run clean (87+ passing).
A broader sweep (`test_permission_broker*.py`, `test_chgr*.py`,
`test_phase_report*.py` — 1427 tests) passes except 2 pre-existing,
unrelated `python -m build` wheel-packaging failures, independently
reconfirmed identical via `git stash` A/B at current `HEAD`.

**Fast Green:** full-suite `pytest -m fast_green -q` at current repaired
`HEAD`: 338 failed / 8689 passed / 5 skipped / 9 errors (raw,
undeselected). All 347 failing/erroring nodeids were inspected by file
name: every one is confined to the pre-existing, host-specific
HATP/HMIC/Class-B/repository-identity/HBDC-bound-contract-identity test
cluster this project has long carried forward (unrelated by construction
— this phase's diff touches zero `src/pcae/**` files — and unrelated by
inspection — zero nodeids reference `interactive_workflow`,
`session_service`, `governance_auto_publication`, `phase.py`,
`publication_service`, or `chgr`). Deselecting exactly those 347 nodeids
produces a fully clean run: **0 failed, 8689 passed, 5 skipped, 28133
deselected.** Zero attributable regressions.

**Runtime:** `Observed`/`observe`/`unavailable`, unchanged before and
after this phase's work.

**Release:** v0.3.2 remains **NOT RELEASED**. No tag, GitHub Release,
artifact upload, PyPI publication, or version change occurred. The
unpinned-`hatchling` reproducible-build issue remains open, carried
forward unmodified. The article track remains stopped;
`~/repos/pcae-deepseek-research` was not inspected, modified, or
imported from.

**`B-149O.20L.7O.3C.3-1`: CLOSED. PLAN B+ CAPABILITY CONSUMPTION:
INDEPENDENTLY VERIFIED.** Recommended next phase:
`149O.20L.7O.3C.4 — Connected Capability Release Scope, Version, and
Reproducible-Build Hardening`.

See `docs/PHASE_149O_20L_7O_3C_3_2_AUTO_PUBLISH_CORRUPT_STORE_REPAIR_INDEPENDENT_VERIFICATION.md`
for the full methodology and section-by-section evidence (§1–§47 of the
governing brief).
