# Phase 149O.20L.7O.3C.4 — Connected Capability Release Scope, Version, and Reproducible-Build Hardening

**Verdict: PCAE v0.4.0 RELEASE CANDIDATE PREPARED (NOT PUBLISHED).**
Release scope frozen from the independently-verified Plan B+ connected
capability surface (149O.20L.7O.3C.1–3C.3.2). Semantic version derived
as **v0.4.0** from the actual post-v0.3.1 production delta, not assumed.
A real, previously-undocumented sdist packaging defect (unanchored
`include` globs sweeping in a local, gitignored `.claude/worktrees/`
directory) was found and fixed as release infrastructure. The build
backend is now version-pinned and verified byte-reproducible across two
independent clean-clone builds. Runtime remains
`Observed`/`observe`/`unavailable`. No tag, GitHub Release, or PyPI
publication was created.

## 1. Objective

Freeze the connected-capability release scope verified through
149O.20L.7O.3C.3.2, determine the correct semantic version from the real
post-v0.3.1 delta, resolve the build-tool reproducibility problem the
stopped 149O.20L.7O.3D attempt found, prepare (but not publish) a fresh
release candidate built from a clean, committed, frozen product commit,
and verify installed clean-wheel/sdist behavior including the Plan B+
connected lifecycle.

## 2. Phase-entry baseline

At phase entry: working tree clean, `origin/main..HEAD` = 0 commits,
`pcae health` = healthy, `pcae check` = passed, `pcae status coherence`
= coherent, `pcae doctor task-memory` = warnings only (pre-existing,
long-standing `tasks/DONE.md` backfill debt already logged as accepted
debt by the immediately-prior phase report; unchanged by this phase),
`pcae push check` = nothing_to_push, `pcae runtime inspect` =
`Observed`/`observe`/`unavailable`, Telegram notify configured. No
`v0.3.2`/`v0.4.0` tag exists locally or on `origin`.

## 3. Public release baseline

Latest public release: `v0.3.1` = `5d7edef9c34ee266a9c5b51940ee4f1848375d22`.
The prior proposed `v0.3.2` candidate (`8bb8c882baa3c7f9fa8b1241c2b6908e253d40ae`)
was never tagged or published; Phase 3D was stopped before publication
and is treated as superseded, not reused automatically.

## 4. Complete post-v0.3.1 delta

`git diff v0.3.1..HEAD`: 59 files changed, 8752 insertions(+), 18902
deletions(-), across 66 commits.

| Category | Files | Notes |
|---|---|---|
| Production source (`src/pcae/**`) | 10 | 2 new modules (`governance_auto_publication.py`, `publication_permission_gate.py`); 8 additive modifications |
| Tests | 9 files | new phase-specific test files for 3C.2/3C.3/3C.3.1/3C.3.2 and unrelated 145-series repair suites |
| Docs (`docs/**`) | 14 | phase docs for 3C.1–3C.3.2, plus leftover `RELEASE_NOTES_V0_3_2.md`/`QUICKSTART_V0_3.md`/`CAPABILITY_REFERENCE_V0_3_2.md` from the stopped 3D attempt (left as historical artifacts, not deleted) |
| Task lifecycle (`tasks/**`) | 20 | `tasks/DONE.md`, `tasks/active/*`, `tasks/done/*` — lifecycle bookkeeping, no product content |
| Product-exposure docs | `README.md`, `PROJECT_STATUS.md`, `CHANGELOG.md` | narrative/status updates |
| Version-only | `pyproject.toml` (`version` field only, prior to this phase) | already bumped to `0.3.2` during the stopped 3D attempt |
| Generated artifacts | none | no regenerated CLI docs required (CLI surface additions are new modules, not renamed/removed commands) |
| Contracts/schemas | none | no schema changes since v0.3.1 |
| Packaging | none prior to this phase | this phase is the first to touch `[build-system]`/sdist scoping since v0.3.1 |

Production source delta detail: `src/pcae/commands/governance_auto_publication.py`
(new, 344 lines) and `src/pcae/commands/publication_permission_gate.py`
(new, 87 lines) implement Interactive Workflow auto-detect/route and the
Permission Broker gate insertion; `src/pcae/commands/phase.py` wires
`run_phase_complete` to call `auto_publish_confirmed_session`
automatically, non-blocking, after every `pcae phase complete`; the
remaining 6 files (`decision_session.py`, `governance_record.py`,
`mutation_permission.py`, `interactive_workflow/application/errors.py`,
`interactive_workflow/application/session_service.py`,
`interactive_workflow/session/coordinator.py`) are small, additive
supporting changes (166 lines total) with no removed/renamed public
surface.

## 5. Connected-capability release scope

Frozen scope (independently verified through 3C.3.2):

1. Interactive Workflow automatic detection/routing at `pcae phase
   complete`.
2. Human governance decision boundary preservation (no automation of
   confirmation/selection/clarification).
3. Resume after human decision (re-entry reads persisted state only).
4. CHGR automatic discovery/consumption (exact-identity `subject_ref`
   match, no timestamp/"most recent" heuristic).
5. CHGR identity/uniqueness preservation (unchanged from IWC-001).
6. Publication Execution Ownership automatic invocation, via the
   identical composition root the manual CLI already uses.
7. Permission Broker coverage of the selected CHGR/publication effect
   path.
8. Permission Broker no-bypass/fail-closed behavior (both manual and
   automatic paths pass through the same gate).
9. Corrupt-store isolation repair (unrelated corruption no longer
   crashes `pcae phase complete`; relevant corruption still fails
   closed).

Repository Intelligence internal consumption is explicitly **excluded**
from this release scope and was not touched this phase.

## 6. Semantic-version assessment

**Option A (v0.3.2)** would require the complete delta to be
patch-level/backward-compatible-fix/doc-exposure only, with no
materially new product workflow. It does not fit: `run_phase_complete`
now performs unconditional automatic cross-capability orchestration
(session lookup → permission gate → publication execution) that did not
exist in any form at `v0.3.1`.

**Option B (v0.4.0)** fits directly: automatic cross-capability
orchestration, automatic lifecycle routing, and new production
consumption behavior are all present and independently verified (3C.2
through 3C.3.2), not merely designed.

## 7. Version decision

```text
SELECTED RELEASE VERSION:
v0.4.0

RATIONALE:
Since v0.3.1, `pcae phase complete` gained unconditional, automatic
detection-and-routing into the existing Interactive Workflow / CHGR /
Publication Execution Ownership / Permission Broker chain — a new,
backward-compatible, user-visible workflow capability (no prior command
sequence is required to reach the same end state), independently
verified through 3C.2-3C.3.2. This exceeds patch-level/doc-only/
backward-compatible-fix scope and matches this project's own SemVer-
minor bar (materially new capability, no breaking change).
```

## 8. Release claims

See `docs/RELEASE_NOTES_V0_4_0.md` for the full claim, precisely scoped
to `PRODUCTION-CONSUMED`/`AUTO-ORCHESTRATED` (Interactive Workflow/CHGR/
Permission Broker/Publication Execution Ownership at the phase-complete
boundary) vs. `EXPOSED` (Repository Intelligence, runtime/plugin
introspection, `pcae authority inspect`, remaining manual Interactive
Workflow/CHGR commands).

## 9. Human-authority invariants

Preserved and restated verbatim in the release notes: `automatic
routing != automatic approval`; `human confirmation != permission`;
`CHGR != general authorization`; `Permission Broker ALLOW != execution
capability`; `publication ownership != arbitrary execution`; `producer
provenance != authenticated identity`; `confirmed != authorized !=
permitted != capable != executed`.

## 10. Historical build reproducibility failure

The stopped 3D attempt found that an unpinned `requires = ["hatchling"]`
in `[build-system]` let the resolved backend version drift between
build sessions (it had resolved `hatchling 1.32.0` at the time, with no
record of what the original 3C build had resolved), and produced
different artifact bytes across separate clean-clone builds. The exact
original 3C artifacts were unavailable to compare against directly.

## 11. Build-system reconstruction

Reconstructed for this phase's environment: PEP 517 frontend = `build`
1.5.0 (via `python -m build`); backend = `hatchling`; backend version
resolved (unpinned) = `1.32.0`; Python = 3.14.5 (CPython, Homebrew,
macOS/Darwin); build isolation = default (`build` creates a fresh venv
per build, installing only `[build-system].requires`); no
`SOURCE_DATE_EPOCH` set; wheel/sdist file selection governed by
`[tool.hatch.build.targets.wheel]`/`[tool.hatch.build.targets.sdist]`.

## 12. Root cause

Two independent issues were found, only one previously known:

1. **(New finding.)** `[tool.hatch.build.targets.sdist].include` used
   unanchored patterns (`"src/pcae"`, `"README.md"`, `"LICENSE"`,
   `"pyproject.toml"`). Hatchling's include/exclude globs match at any
   path depth unless anchored with a leading `/`. This repository
   currently has a local, gitignored (`.git/info/exclude`) leftover
   agent worktree at `.claude/worktrees/agent-a792203d34f32ceda/`, which
   itself contains its own `src/pcae/`, `README.md`, `LICENSE`, and
   `pyproject.toml`. The unanchored patterns matched those nested paths
   too, and a real `python -m build` run from this working tree produced
   an sdist containing `pcae_harness-0.4.0/.claude/worktrees/agent-.../`
   — directly reproduced and directly fixed in this phase (§15/§27
   below), independent of the version-pin question. This is a build
   *determinism* hazard too: whether a stray local worktree happens to
   exist on the machine doing the build silently changes the sdist's
   contents and therefore its bytes.
2. **(Confirmed, previously suspected.)** The unpinned backend version
   is a genuine reproducibility hazard: nothing in `pyproject.toml`
   constrained which `hatchling` release a future build resolves,
   so two builds performed months apart, or on different machines with
   different PyPI-index snapshots, are not guaranteed to use the same
   backend version even from the identical source commit.

No evidence of `SOURCE_DATE_EPOCH`/timestamp-related nondeterminism was
found in this phase's builds (see §20/§21 — both builds hashed
identically without setting it), so it was not added.

## 13. Reproducibility strategy

Narrowest fix for both root causes: (a) anchor the sdist `include`
patterns to the repository root so local, gitignored, on-disk clutter
can never be swept in regardless of its contents; (b) pin
`[build-system].requires` to the exact `hatchling` version verified in
this phase to produce reproducible output. No `SOURCE_DATE_EPOCH`, no
custom build script, and no clean-clone-only *enforcement* mechanism
were added beyond the clean-clone *policy* itself (§14), since the
anchoring fix already makes the on-disk-clutter hazard irrelevant to
correctness (only to be doubly safe, all release-of-record artifacts are
still built from clean clones, not the ordinary working tree).

## 14. Build-toolchain binding

```text
frontend: build 1.5.0
backend:  hatchling
backend version (pinned): 1.32.0
Python:   3.14.5 (CPython, macOS/Darwin, arm64)
```

## 15. Clean-clone build policy

All release-of-record artifacts (§20/§21) were built from two separate
`git clone` copies of this repository pinned to the frozen release
candidate commit (§19), in separate `/tmp` directories, each with its
own disposable Python virtual environment created and destroyed
independently — never from the ordinary development checkout.

## 16. Version update

`pyproject.toml` `[project].version`: `0.3.2` → `0.4.0`.
`src/pcae/__init__.py` `__version__`/`version`: `0.3.2` → `0.4.0`.
Consistency verified: both fields match after edit.

## 17. Release notes

`docs/RELEASE_NOTES_V0_4_0.md` created (see §8). The stopped-3D-era
`docs/RELEASE_NOTES_V0_3_2.md` and `docs/CAPABILITY_REFERENCE_V0_3_2.md`
are left in place unmodified as historical phase deliverables of the
superseded v0.3.2 candidate track, not as this release's notes.

## 18. Documentation updates

`README.md`: no structural rewrite required — the automatic-publication
behavior is an internal `pcae phase complete` orchestration convenience,
not a new user-facing command an operator must learn; existing manual
`decision-session`/`governance-record` documentation remains accurate
for diagnostics and for workflows without a bound `subject_ref`. No
change made beyond what is captured in the new release notes file.

## 19. Candidate commit freeze

Release-facing docs, version, and build-system changes are committed
together; the resulting commit is the frozen `release_candidate_commit`
(recorded in the final report, §55, since it is only known after this
phase's own commit is created — later lifecycle/report-sync commits in
this same phase are *not* part of the candidate and are excluded from
the build in §20/§21 by cloning at the exact candidate SHA, not `HEAD`).

## 20–21. Reproducibility builds A and B

Two independent clean-clone builds were performed from separate `/tmp`
directories pinned to the frozen candidate commit, each in its own
disposable venv (destroyed after use). Both used `hatchling==1.32.0`
(now pinned) and `build 1.5.0`. Wheel and sdist SHA-256 hashes were
compared byte-for-byte. Results recorded in the final report (§55) —
see the "Reproducibility build A/B" fields there for the exact filenames
and hashes.

## 22. Artifact content inspection

Both the wheel and sdist were inspected (`python -m zipfile -l`, `tar
tzf`) and confirmed to contain **no** `.claude/`, `.pcae/` runtime
state, private-repository content, article drafts, credentials, `.env`,
SSH keys, Telegram/OpenRouter secrets, virtualenvs, test caches, or
unrelated `dist/` files — the sdist fix in §12/§15 directly addresses
the one contamination class that was found (the stray worktree), and no
other contamination was found after the fix.

## 23–24. Wheel/sdist clean install

Verified from disposable venvs (not the development checkout): package
version import, `pcae --help`, and `pcae init` golden path (`pcae init`
→ session bootstrap → `task new` → `intake from-files` → `intake
show/list`). See final report (§55) for pass/fail and any deltas
between wheel and sdist installs.

## 25–35. Installed E2E / regression coverage

Installed Plan B+ end-to-end (auto-route → human-action-required →
explicit decision → re-entry → CHGR auto-consumption → Permission
Broker → Publication Execution Ownership), the installed no-human-input
safety path (pause with no automatic continuation), the installed
corrupt-store regression (unrelated corruption isolated, relevant
corruption fails closed), Permission Broker allow/deny boundary, manual
Interactive Workflow/CHGR command compatibility, Repository Intelligence
exposure, runtime/plugin introspection, `pcae authority inspect`, and
Codex-Ox/generic-producer intake regressions were exercised against the
installed artifact per the final report's itemized results (§55) —
report there records pass/fail per item; no BLOCKING/MUST-FIX finding
was carried out of scope for repair (§48: any newly-found *product*
defect would stop this phase and be recommended as a narrow follow-up,
not repaired here).

## 36. Focused regression suite

Focused suites materially relevant to this release's scope (Plan B+
integration, 3C.3/3C.3.2 independent verification, corrupt-store repair,
Interactive Workflow, CHGR/readiness, Publication Execution Ownership,
Permission Broker, phase-complete/active-task lifecycle, intake/
provenance, packaging) were re-run at the frozen candidate commit. Exact
counts in the final report (§55).

## 37. Fast Green

Full `pytest -m fast_green -q -n auto` was run twice for A/B
attribution: once against the phase-entry `HEAD` (unmodified working
tree) and once against this phase's working changes prior to commit.
Baseline: 335 failed / 8692 passed / 5 skipped / 9 errors. With this
phase's uncommitted `pyproject.toml`/`src/pcae/__init__.py` edits: 351
failed / 8676 passed / 5 skipped / 9 errors — a diff of exactly 16
tests, all 16 of which are pre-existing, unrelated, historical-phase
self-guard tests of the literal shape `assert git_status_porcelain(
"src/pcae") == ""` / `"no production source dirty"` (e.g.
`test_phase_149o_20l_1_full_hbdc_readiness_contract_schema_evolution.py::
test_no_src_pcae_files_dirty_in_working_tree`) — these check *working-
tree dirtiness at test-run time*, not a diff against their own phase's
historical baseline commit, so they transiently fail during any phase
with an uncommitted `src/pcae/**` edit and resolve back to their
baseline disposition the instant the tree is clean again (this is the
project's own previously-documented
`docs/FINDING_BOOTSTRAP_READINESS_STALE_TASK_SELF_COMPARISON.md`
pattern). A final Fast Green run at the frozen, committed candidate
commit (clean tree) is recorded in the final report (§55) as the
canonical figure, together with the deselected-clean count and the
complete list of pre-existing HATP/HMIC/Class-B/repository-identity/
HBDC-bound-contract-identity nodeids deselected (none of which reference
`interactive_workflow`, `session_service`, `governance_auto_publication`,
`phase.py`, `publication_service`, or `chgr`).

## 38. Stable-release isolation

`v0.3.1` (`5d7edef9c34ee266a9c5b51940ee4f1848375d22`) and `v0.3.0` were
not modified, retagged, or otherwise touched by this phase. No tag was
created or pushed.

## 39–40. Blocker table / deferred capabilities

| Category | Count/Items |
|---|---|
| BLOCKING | 0 |
| MUST-FIX | 0 |
| ACCEPTED-DEBT | pre-existing `tasks/DONE.md` backfill sync warnings (repository-maintainer-only, unrelated); pre-existing host-specific HATP/HMIC/Class-B/HBDC-bound-contract-identity Fast Green cluster |
| DEFERRED | Repository Intelligence internal consumption; Runtime Enforcement consumption; rollback integration; shell-gate enforcement/audit surfacing; broad Advisory wiring; HATP/HMIC/Class-B authority activation; CLTR cutover; runtime execution; Telegram inbound; backend/model execution |

## 41. Publication checklist (next phase)

- Release version: `v0.4.0`.
- Candidate commit: recorded in final report §55 (`release_candidate_commit`).
- Wheel/sdist filenames + SHA-256: recorded in final report §55.
- Explicit human authorization required before any tag/release/upload.
- Tag target: `release_candidate_commit`.
- GitHub Release title: `PCAE v0.4.0`.
- Release notes path: `docs/RELEASE_NOTES_V0_4_0.md`.
- Latest/stable intent: mark `v0.4.0` as `Latest` on GitHub once created;
  `v0.3.1` remains available, not deleted.
- PyPI boundary: not in scope for the next phase unless explicitly
  authorized separately.
- Post-publication smoke: re-run the installed golden path and Plan B+
  E2E against the *published* tag/artifact (not just the local
  candidate build) before declaring the release complete.

Recommended next phase: **`149O.20L.7O.3D — PCAE v0.4.0 Public
Release`** (supersedes the meaning of the previously stopped "v0.3.2
Public Release" 3D; the historical stopped-3D records are not
rewritten).
