# Phase 149O.20L.7O.3L — PCAE v0.4.2 Release Hardening

**Status: RELEASE-CANDIDATE PREPARATION ONLY. NO PUBLICATION PERFORMED.**

## 1. Objective

Prepare a frozen, independently-verified `v0.4.2` release candidate
implementing the human-selected Option B from `149O.20L.7O.3K`: ship
`3J`'s already-verified, attachment-only Repository Intelligence
integration as a narrow patch release, with release language that
draws the AUTOMATIC RI CONTEXT ATTACHMENT vs. TRUE RI-BACKED ADVISORY
REASONING distinction exactly. This phase does not implement true
reasoning consumption, does not repair finding F1, does not modify
`AdvisoryProvider`, and does not publish (no tag, no GitHub Release,
no PyPI upload).

## 2. v0.4.1 baseline

Verified at phase entry:

- `git status --short`: clean.
- `git rev-list --count origin/main..HEAD`: `0`.
- `HEAD` == `origin/main` == `f21431fab1d1c9c8eead953c4767e481e8c678ef`.
- `v0.4.1^{commit}` == `9869cb65d890b70d8649ddd4216ffda4e7d98df5`, unchanged.
- No local or remote `v0.4.2` tag existed.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: warnings only (pre-existing
  `tasks/DONE.md` sync-debt, unrelated to this phase).
- `pcae push check`: reported a stale/missing canonical phase report
  relative to the completed `149O.20L.7O.3K` task — expected pre-phase
  state, resolved by this phase's own canonical report at completion.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`,
  registry empty, 0 plugins.
- Telegram notify sink: configured, enabled, ready.

## 3. Post-v0.4.1 delta

`git diff --name-status v0.4.1..HEAD` (pre-phase, at phase entry) showed
26 files changed (19 added, 6 modified, 1 renamed), of which exactly
**one** touched production source:

- `M src/pcae/core/advisory.py` — the `149O.20L.7O.3J` change: adds
  `_gather_repository_intelligence_context()` and wires it, additively,
  into `build_advisory()`'s output envelope as
  `repository_intelligence_context`. Never read by
  `permission_broker`/`mutation_permission`; never influences
  `broker_decision`/`advisory_decision`; fails soft on missing/invalid
  snapshot.

All other changed files were: new test modules (3J, 3J.1), phase/
reporting docs, `PROJECT_STATUS.md`/`CHANGELOG.md` status metadata, and
task-lifecycle files. This confirms the only intended post-v0.4.1
product behavior change is the `3J` Advisory Mode RI-context
attachment — no other product behavior change exists, so no scope
reassessment was required.

## 4. Release scope

Narrow patch release: automatic Repository Intelligence context
attachment for Advisory Mode. No authority change, no execution-
capability change, no schema/contract redesign, no true reasoning
consumer, no new CLI conceptual workflow.

## 5. Attachment-vs-reasoning distinction

`repository_intelligence_context` is an additive, informational-only
output field. It is never consumed by `build_advisory`'s decision
logic. `broker_decision`, `advisory_decision`, all `would_*` fields,
`hard_block_present`, `authorization_granted`, and `execution_authorized`
are computed identically regardless of whether Repository Intelligence
is present, absent, malformed, or stale (empirically verified in
Section 26). TRUE RI-BACKED ADVISORY REASONING remains **not
implemented**; the 122A-scoped reasoning consumer, the mock-only/
disconnected `AdvisoryProvider` framework, and the required 115W
contract amendment are all unchanged and out of scope for this phase.

## 6. Version decision

`v0.4.2` (patch-level), per this project's established semantic-version
criteria: additive output field, backward compatible, no authority
change, no execution-capability change, no contract/schema redesign,
no true reasoning consumer, no new CLI conceptual workflow, and
independently verified in `149O.20L.7O.3J.1`. Consistent with the `3K`
recommendation (Option B).

## 7. Version changes

- `pyproject.toml`: `version = "0.4.1"` → `"0.4.2"`.
- `src/pcae/__init__.py`: `__version__ = "0.4.1"` → `"0.4.2"`.
- No other canonical version source found (`PROJECT_STATUS.md`/
  `CHANGELOG.md` `0.4.1` references are historical phase narration,
  intentionally left unmodified per the "do not rewrite historical
  phase reports" instruction).

## 8. Release notes

`docs/RELEASE_NOTES_V0_4_2.md` created. States: `pcae advisory check`
now automatically attaches available Repository Intelligence context;
context includes existing provenance (`context_metadata`) and
limitations (`limitation_bundle`, including a new
`possibly_stale_snapshot` entry); manual `pcae advisory-context build`
is no longer a prerequisite merely to obtain RI context in Advisory
Mode output; acquisition is read-only; missing/invalid RI degrades
truthfully; existing Advisory authority/decision fields are unchanged;
Permission Broker is unaffected; runtime remains non-executing. Uses
"AUTOMATIC RI CONTEXT ATTACHMENT" terminology throughout and explicitly
states true RI-backed Advisory reasoning is NOT IMPLEMENTED/deferred.

## 9. F1 disposition

F1 (a foreign RI snapshot at the canonical `.pcae/repository-intelligence`
path via filesystem symlink can be consumed; requires pre-existing
filesystem write access to the target repo's `.pcae` tree) is carried
forward unrepaired. Classification: **F1: NON-BLOCKING FOR
ATTACHMENT-ONLY v0.4.2 / MUST-REPAIR BEFORE TRUE RI REASONING
CONSUMPTION.** Disclosed in the phase document and release-hardening
accepted-debt; not separately called out in end-user release notes
beyond the existing non-authority framing, since the attached context
carries no authority regardless of its provenance.

## 10. F2 disposition

F2 (`3J` integrates Advisory Mode attachment only; the differently-
scoped 122A `AdvisoryProvider`/`AdvisoryContextPackage` reasoning
framework remains untouched/mock-only) carried forward as accurate,
documented, non-blocking classification. Not a release defect given
accurate documentation (Sections 5, 8).

## 11. Documentation audit

Searched `README.md` and non-historical `docs/*.md` for
"RI-backed", "reasons over RI", "drives Advisory", "affects Advisory
recommendation" wording. No overclaiming instances found outside this
phase's own careful negations. `README.md`'s Repository Intelligence
entry does not currently describe the Advisory attachment behavior at
all (accurate, if incomplete) and was left unmodified — no incorrect
wording to remove. Historical phase reports (`3J`, `3J.1`, `3K`) were
not rewritten.

## 12. Build infrastructure

Reused unmodified: `[build-system].requires = ["hatchling==1.32.0"]`;
`[tool.hatch.build.targets.sdist]` root-anchored `include` patterns
(`/src/pcae`, `/README.md`, `/LICENSE`, `/pyproject.toml`). No build
infrastructure changes were required or made.

## 13. Candidate commit

`release_candidate_commit = bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`
(`pcae commit implementation`, committing `pyproject.toml`,
`src/pcae/__init__.py`, `docs/RELEASE_NOTES_V0_4_2.md`, and the active
task contract). `git diff bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4..HEAD
-- src/pcae pyproject.toml docs/RELEASE_NOTES_V0_4_2.md` remained empty
through phase completion (verified before `phase complete`).

## 14. Build provenance

- Source commit: `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`.
- Python: 3.14.5 (both build environments).
- Frontend: `build` 1.2.2 (PEP 517 isolated build).
- Backend: `hatchling` 1.32.0 (pinned, matches `[build-system].requires`).
- Build command: `python -m build --outdir dist` (each clone, its own
  fresh venv with only `build==1.2.2`/`hatchling==1.32.0` installed).
- Environment controls: two independent `git clone --no-local` clones
  of the candidate-commit worktree, each checked out to
  `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4` in detached HEAD, each
  built in its own fresh Python venv, no shared build cache.

## 15. Wheel reproducibility

`pcae_harness-0.4.2-py3-none-any.whl` — identical filename, identical
size (2,352,007 bytes), identical SHA-256
(`20fce764abe4bebc36c831f11c286db16c516b289e966838c4169c10294b60b4`)
across both clones; `cmp` byte-for-byte identical. **PASS.**

## 16. Sdist reproducibility

`pcae_harness-0.4.2.tar.gz` — identical filename, identical size
(2,053,704 bytes), identical SHA-256
(`19f6372447d8a65bf804c41c7ef7fdca501b58d33ec66b5b9365abc2982f0455`)
across both clones; `cmp` byte-for-byte identical. **PASS.**

## 17. Artifact inspection

Inspected wheel (`unzip -l`) and sdist (`tar tzf`) listings. No `.git`,
no `.claude/worktrees`, no private-research/article content, no `.env`,
no credentials/API keys/SSH keys, no virtual environments, no caches,
no stale `dist` files. Sdist contains only `src/pcae/**`, `README.md`,
`LICENSE`, `pyproject.toml`, and packaging metadata, per the anchored
`include` patterns. Wheel contains only the `pcae` package plus
standard `dist-info` metadata.

## 18. Frozen hashes

- `release_version`: `v0.4.2`
- `release_candidate_commit`: `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`
- `wheel`: `pcae_harness-0.4.2-py3-none-any.whl` / 2,352,007 bytes /
  `sha256:20fce764abe4bebc36c831f11c286db16c516b289e966838c4169c10294b60b4`
- `sdist`: `pcae_harness-0.4.2.tar.gz` / 2,053,704 bytes /
  `sha256:19f6372447d8a65bf804c41c7ef7fdca501b58d33ec66b5b9365abc2982f0455`
- `reproducibility`: **PASS**

## 19. Wheel install

Installed the frozen wheel alone into a fresh venv. Verified
`import pcae; pcae.__version__ == "0.4.2"` and `pcae --help` works.
Ran `pcae init` in a disposable directory (golden path start); ran
`pcae repository-intelligence snapshot generate` against a disposable
clone of the candidate-commit tree (needed for a valid architectural
layout) and `pcae advisory check` against it — see Sections 21-25.

## 20. Sdist install

Installed the frozen sdist alone into a separate fresh venv. Verified
`import pcae; pcae.__version__ == "0.4.2"` and `pcae --help` works.
Behavior agrees with the wheel install (same version, same CLI surface;
`pcae advisory context build` verified working from this install in
Section 28).

## 21. RI attachment smoke (installed, release-defining)

In a disposable clone of the candidate-commit tree: generated a valid
Repository Intelligence snapshot via `pcae repository-intelligence
snapshot generate` (existing supported mechanism). Ran `pcae advisory
check -c "git status" --json` from the **installed wheel**, without
running `pcae advisory-context build` first. Result: `
repository_intelligence_context.available == true`, with
`context_metadata`/`source_artifact` provenance and a non-empty
`limitation_bundle` present. No manual context-build CLI prerequisite.
**PASS.**

## 22. Installed missing-RI smoke

In a disposable clone with no Repository Intelligence snapshot present
(temporarily removed the pre-existing tracked `.pcae/repository-
intelligence/` directory), ran `pcae advisory check` from the installed
wheel. Result: `repository_intelligence_context.available == false`,
`unavailable_reason == "no_repository_intelligence_snapshot_found"`, no
traceback, exit succeeded. `broker_decision`/`advisory_decision`/all
`would_*` fields identical to the RI-present case (Section 26).
**PASS.**

## 23. Installed malformed-RI smoke

Wrote a representative malformed `latest.json`
(`{"not": "a valid snapshot", "garbage": true}`) at the canonical path.
Ran `pcae advisory check` from the installed wheel. Result:
`repository_intelligence_context.available == false`,
`unavailable_reason == "repository_intelligence_context_build_failed"`,
`unavailable_detail == "snapshot_identity is missing or invalid"`, no
traceback, no fabricated valid context. **PASS.**

## 24. Installed stale-RI smoke

The disposable clone's pre-existing snapshot recorded
`repository_commit: 0eedb51dd5fa15abdfbda69ba00f9fe902bffadc`, which
differs from that clone's current `HEAD`
(`bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`). Advisory check output
carried an added `limitation_type: "possibly_stale_snapshot"` entry
naming both commits. Authority fields unchanged from the fresh-snapshot
case (Section 26). **PASS.**

## 25. Read-only proof

Captured `sha256` of `.pcae/repository-intelligence/latest.json`
immediately before and immediately after an installed `pcae advisory
check` invocation on the same disposable clone: identical hash
(`a6732dac81fbf189b68fc5f8c09b0fb190b5787ba78c76d487de38875f5ea3ed`)
before and after. No project-source modification; no RI snapshot
regeneration; no RI artifact write/update from the new acquisition
path. **PASS.**

## 26. Authority non-flow

Compared full advisory-check JSON output with RI absent vs. RI present
on structurally equivalent invocations (`pcae advisory check -c "git
status"`). `broker_decision`, `advisory_decision`,
`would_allow_read_only`, `would_allow_governed_preflight_only`,
`would_require_active_task`, `would_require_preflight`,
`would_require_human_review`, `would_require_more_evidence`,
`would_block`, `would_deny`, `hard_block_present`,
`authorization_granted`, `execution_authorized`, `command_executed`,
`enforcement_applied` were all identical across both conditions.
**VERIFIED.**

## 27. Permission Broker isolation

The `repository_intelligence_context` acquisition path in
`core/advisory.py` is called only from `build_advisory()`, downstream
of and structurally independent from `permission_broker`/
`mutation_permission` evaluation (Section 26's identical authority
fields across RI-present/absent conditions is direct evidence of this
isolation for Advisory Mode). No `push`/`promote`/`rollback` Permission
Broker code path reads `repository_intelligence_context` or any
Repository Intelligence artifact — confirmed by source inspection
(`git diff v0.4.1..HEAD -- src/pcae` touches only `core/advisory.py`).

## 28. Manual CLI compatibility

Ran `pcae advisory context build --snapshot
.pcae/repository-intelligence/latest.json --capability git_status
--json` from the installed wheel: produced a context package with the
same shape as before this release (unchanged). Manual CLI path is
unaffected by the automatic-attachment addition.

## 29. Advisory regressions

The 3J/3J.1 focused and independent suites (Sections 31-32) exercise
the existing Advisory Mode test corpus's additive-field expectations;
no existing strict-consumer test was found to break on the new
`repository_intelligence_context` field (additive dict key).

## 30. RI regressions

No Repository Intelligence persistence/query/schema-compatibility
code was modified this phase (`git diff v0.4.1..HEAD -- src/pcae`
shows only `core/advisory.py` changed); RI's own test suites are
unaffected by definition of an unmodified subsystem.

## 31. 3J tests

`tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py`
— 3J's own focused integration suite, run as regression evidence
against the candidate commit. Result recorded in the canonical report
(Section 36 basis).

## 32. 3J.1 tests

`tests/test_phase_149o_20l_7o_3j_1_independent_ri_advisory_consumption_verification.py`
— 3J.1's complete independent verification suite (28 tests, 0 shared
code with 3J's own tests per 3J.1's own record), run unweakened as
strong release evidence against the candidate commit.

## 33. v0.4.1 regressions

Representative existing release-critical surfaces (Permission Broker
integration, rollback default path, `pcae runtime inspect`, `pcae
authority inspect`) were exercised indirectly via Fast Green
(Section 35) rather than individually redesigned, per the phase
instruction to reuse existing coverage.

## 34. Runtime

`pcae runtime inspect` from the installed wheel, both immediately
before and immediately after the installed RI Advisory smoke tests
(Sections 21-25): `Runtime state: Observed`, `Execution capability:
unavailable`, `Maximum plugin capability: observe`, registry empty, 0
plugins — unchanged in both readings.

## 35. Fast Green

`python -m pytest -m "fast_green" -n auto -q` run against both the
frozen candidate-commit tree and an independent clone pinned to the
pre-phase baseline commit (`f21431fab1d1c9c8eead953c4767e481e8c678ef`),
with matching cwd/rootdir in both runs (a cwd/rootdir mismatch in an
earlier, discarded attempt was found to produce spurious pass/fail
results for a small number of cwd-resolving self-referential tests —
corrected before recording these numbers):

- Baseline: 336 failed, 8567 passed, 11 skipped, 13 errors.
- Candidate: 335 failed, 8568 passed, 11 skipped, 13 errors.

Node-ID-level diff: exactly one candidate-only failure —
`tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main`,
a self-referential tripwire that fails whenever local `HEAD` is ahead
of `origin/main` (true for any unpushed governed commit) and resolves
on push — not caused by any source change. Two baseline-only failures
(`test_no_hhce_writer_module_exists_anywhere_in_src_or_scripts`,
`test_verify_detects_tampered_record`) were investigated and are
pre-existing run-to-run non-determinism unrelated to this phase's
change, not evidence of a regression fix. All remaining ~335 failures
are identical, pre-existing, self-referential "byte/contract unchanged
since phase entry" tripwires from dozens of earlier, unrelated phases
(HATP/HMIC/Class-B contract-identity and production-scope-drift
guards) that are structurally guaranteed to fail once HEAD moves past
their own phase-entry snapshot point, independent of this phase's
change (confirmed identical failure set, one member investigated in
depth: `test_non_member_control_perturbation_does_not_change_digest`,
whose "paths.py is a non-frozen control file" assumption became stale
once a later, unrelated phase added `core/paths.py` to the frozen
30+-file authority set — present in both baseline and candidate,
unrelated to `core/advisory.py`).

**Attributable regressions: 0.**

## 36. Blocker table

| Item | Classification |
| --- | --- |
| F1 (symlink/provenance hardening before true reasoning) | DEFERRED |
| True RI-backed Advisory reasoning consumption | DEFERRED |
| 115W contract amendment for `AdvisoryContextPackage` RI integration | DEFERRED |
| Real (non-mock) `AdvisoryProvider` production connection | DEFERRED |
| Candidate A (rollback readiness/evidence) | DEFERRED (next priority) |
| Candidate B (runtime preflight) | DEFERRED |
| Pre-existing `tasks/DONE.md` task-memory sync-debt | ACCEPTED-DEBT (unrelated, pre-existing) |

BLOCKING = 0. MUST-FIX = 0, contingent on the Fast Green attributable-
regression result recorded in the canonical report.

## 37. Deferred true-reasoning work

True RI-backed Advisory reasoning consumption; F1 repair; 115W
contract amendment; real `AdvisoryProvider` production connection —
all explicitly out of scope for `v0.4.2` and unaddressed by this
phase, per the `3K` decision and this phase's own constraints.

## 38. Candidate A next

After successful `v0.4.2` publication (not performed in this phase),
the next strategic implementation priority is Candidate A — rollback
readiness/evidence automatic generation/consumption — freshly bounded
per `3I`'s finding that readiness itself is not currently implemented,
dry-run evidence exists, and the work is S-M/LOW-risk, not pure wiring.
Not implemented in this phase.

## 39. Publication checklist

- Release version: `v0.4.2`
- Candidate: `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`
- Wheel: `pcae_harness-0.4.2-py3-none-any.whl` /
  `sha256:20fce764abe4bebc36c831f11c286db16c516b289e966838c4169c10294b60b4`
- Sdist: `pcae_harness-0.4.2.tar.gz` /
  `sha256:19f6372447d8a65bf804c41c7ef7fdca501b58d33ec66b5b9365abc2982f0455`
- Release notes: `docs/RELEASE_NOTES_V0_4_2.md`
- Tag target: candidate commit above
- GitHub Latest: intended (not performed)
- PyPI: not authorized unless separately approved
- Human publication authorization: **required**, not obtained in this
  phase

## 40. Final verdict

```
PCAE v0.4.2 RELEASE CANDIDATE: VERIFIED
RELEASE THEME: REPOSITORY INTELLIGENCE CONTEXT ATTACHMENT FOR ADVISORY MODE
ADVISORY MODE: AUTOMATICALLY ATTACHES AVAILABLE RI CONTEXT
MANUAL CONTEXT-BUILD CLI PREREQUISITE: NONE
TRUE RI-BACKED ADVISORY REASONING: NOT IMPLEMENTED / EXPLICITLY DEFERRED
RI ACQUISITION: READ-ONLY
FAIL-SOFT: VERIFIED
PROVENANCE: PRESERVED
LIMITATIONS: PRESERVED
AUTHORITY NON-FLOW: VERIFIED
PERMISSION BROKER: UNAFFECTED
MODEL/NETWORK EXPANSION: NONE
BUILD REPRODUCIBILITY: VERIFIED
WHEEL: VERIFIED
SDIST: VERIFIED
ATTRIBUTABLE REGRESSIONS: 0
BLOCKING: 0
MUST-FIX: 0
RUNTIME: Observed / observe / unavailable
PUBLICATION: NOT PERFORMED
```

Recommended next phase: `149O.20L.7O.3L.1` — PCAE v0.4.2 Public
Release. Publication-only; requires explicit human authorization
before tag push / GitHub Release creation / artifact upload. PyPI
remains separately unauthorized. Not begun.
