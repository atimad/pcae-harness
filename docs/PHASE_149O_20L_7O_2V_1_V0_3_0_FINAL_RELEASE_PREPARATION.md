# Phase 149O.20L.7O.2V.1: v0.3.0 Final Release Preparation and Publication

Release-only phase. Transitions the verified `v0.3.0-rc1` release
candidate to the stable `v0.3.0` release, re-verifies every proven
gate against a freshly built stable candidate, and stops at the human
publication-authority boundary before any tag or GitHub Release is
created.

## 1. Phase Entry (primary evidence)

- Phase-entry HEAD: `3a77647e0b71e7014215bc0d05604d1c72a864db`
- origin/main at entry: `3a77647e0b71e7014215bc0d05604d1c72a864db` (parity)
- Working tree at entry: clean
- Package version at entry: `0.3.0` (`pyproject.toml`, `src/pcae/__init__.py` — already stable form; the RC used a bare Git tag suffix, not RC version metadata)
- Local tags: `v0.1.0-rc1`, `v0.2.0`, `v0.3.0-rc1`
- Remote tags: same three
- GitHub Releases: `v0.1.0-rc1` (pre-release), `v0.2.0` (latest), `v0.3.0-rc1` (pre-release)
- Exact full `v0.3.0-rc1` tag object SHA: `4561336482b1ad6345315ee002fe32091611a30f`
- `v0.3.0-rc1` dereferenced commit SHA: `028cd25471d157055002a0021a862176db97d701` (matches the short identity `028cd254` carried forward from Phase 2V)
- Latest published release at entry: `v0.3.0-rc1`

## 2. RC Baseline Verification

- `v0.3.0-rc1` tag exists locally and remotely, dereferencing to `028cd254...`, matching the previously reviewed public RC.
- Corresponding GitHub Release exists (`isPrerelease: true`, `publishedAt: 2026-08-24T05:24:25Z`, `targetCommitish: main`).
- `028cd254...` confirmed an ancestor of phase-entry HEAD (`git merge-base --is-ancestor`) — no history rewrite, RC has not moved.
- origin/main coherent with local HEAD at entry.

## 3. RC → Final Delta Reconstruction

`git diff --stat 028cd254..HEAD` (phase-entry HEAD) touched only:
`.pcae/*` metadata, `CHANGELOG.md`, `PROJECT_STATUS.md`, `README.md`,
`docs/INSTALLATION.md`, a Phase 2V doc, and `tasks/*` contract/handoff
files — governance and documentation only.

`git diff --stat 028cd254..HEAD -- src/pcae scripts` is **empty**.

**FEATURE DELTA FROM v0.3.0-rc1 TO v0.3.0: NONE.** Only version-framing
documentation and governance artifacts changed.

## 4. Feature Freeze

No product feature was added in this phase. No binary intake, patch/
diff engine, multi-task selection, Windows repair, repository-identity
redesign, Codex/DeepSeek adapters, runtime execution, Permission
Broker enforcement, HATP/FIDO2/WebAuthn, or Dell deployment changes
were touched.

## 5–6. Stable Version / Consistency

`pyproject.toml` (`version = "0.3.0"`) and `src/pcae/__init__.py`
(`__version__ = "0.3.0"`) already carried stable form at phase entry
(matching the `v0.1.0-rc1` precedent: package metadata never carries a
`-rc1` suffix, only the Git tag does) — verified correct, no change
required. Confirmed post-build: wheel/sdist metadata both report
`Version: 0.3.0`; `pip show`/`import pcae; pcae.__version__` both
report `0.3.0` from the clean install.

`pcae --version` remains unimplemented (no top-level argparse
`--version` flag) — Non-Blocking, pre-existing since v0.1, already
documented as such in Phase 2V (finding F-2V-1); no regression, no
action required for v0.3.0.

## 7–8. CHANGELOG / Release Notes

- `CHANGELOG.md`: renamed the `## v0.3.0-rc1 (2026-08-24)` heading to
  `## v0.3.0 (2026-08-24)`, added a "no functional changes from RC"
  line, retitled the cross-reference to the new stable release-notes
  doc, and appended a Phase 149O.20L.7O.2V.1 entry.
- Added `docs/RELEASE_NOTES_V0_3_0.md` — stable framing (Overview /
  What's New / Governed Proposal Intake / ALLOW-DENY Workflow /
  Generic-Agent Architecture / Claude Code Reference Producer /
  Quickstart / Security-Governance Semantics / Current Limitations /
  Known Issues / Installation / Upgrade from RC / Feedback), derived
  from `docs/RELEASE_NOTES_V0_3_0_RC1.md` (kept unmodified as the
  historical RC document).

## 9–13. README / Positioning / Semantic Walls / Limitations

- README Status line updated: `v0.3.0-rc1 (release candidate)` →
  `v0.3.0 (stable)`; `v0.2.0` "current baseline" language updated to
  `v0.3.0`.
- README Release Notes table row repointed to
  `docs/RELEASE_NOTES_V0_3_0.md`.
- README "External Agent Intake (v0.3.0-rc1)" section header →
  "External Agent Intake (v0.3.0)".
- Historical-note paragraph reworded to describe `v0.3.0-rc1` and
  `v0.2.0` in the past tense and `v0.3.0` as the current baseline,
  without altering the historical RC-track table rows further down
  (§Release Candidate Track sections are intentionally left describing
  past RC phases).
- Core positioning ("governed proposal intake, not autonomous
  execution") and the five semantic-wall distinctions were not
  reworded — already correctly stated pre-phase and re-verified live
  in §Section 9 below.

## 14–15. README / Quickstart Final Pass

README reviewed as a first-time-visitor pass; only the Status/table/
section-header changes above were needed — no unnecessary rewrite.
`docs/QUICKSTART_V0_3.md` scanned for stale `rc1` / `0.3.0rc1` /
"release candidate" wording: **none found** — the document was already
version-neutral (refers to "PCAE v0.3", not the RC suffix).

## 16. Article — Explicitly Out of Scope

No article, editorial content, website change, or LinkedIn copy was
created or drafted in this phase.

## 17–22. Clean Build, Hygiene, Artifact Content, Checksums

Built from a **clean detached-HEAD `git worktree`** of the post-content-commit HEAD (not the ordinary dev tree):

```
git worktree add --detach <scratch>/pcae-clean-2v1 HEAD
python -m build --outdir <scratch>/pcae-clean-2v1/dist
```

Result: `pcae_harness-0.3.0-py3-none-any.whl`,
`pcae_harness-0.3.0.tar.gz` — clean success, no packaging warnings.

Artifact inspection (`python -m zipfile -l` / `tar tzf`): no `.venv`,
build-scratch, pytest-cache, temporary-worktree, demo-repository, or
secret/credential content in either artifact (the only `credential`-
substring hits are the legitimate `hatp_hardware_credential_admin.py`
/ `hatp_hardware_credentials.py` product source files, not leaked
secrets).

Required package content confirmed present in the wheel:
`pcae/commands/intake.py`, `pcae/core/intake.py`, full CLI wiring.

`scripts/claude_code_intake_adapter.py` is **not** included in either
built artifact (source-checkout-only, as already documented in both
the RC1 release notes and `docs/QUICKSTART_V0_3.md`) — no packaging
change made or needed.

SHA-256:
```
wheel: 4fb566da3b55fda8f6cee48f06b5e59bd96c180d1b9cebabb9a3252a599376d0  pcae_harness-0.3.0-py3-none-any.whl
sdist: 1e56b64cb2c89a4539430c0f7d5e7d2c642d14a1255b7427bbbc97ad98ce0846  pcae_harness-0.3.0.tar.gz
```

## 23–24. Clean Install / CLI Smoke

Installed the built wheel (no editable install) into a fresh venv.
`pcae --help`, `pcae intake --help`, `pcae intake create --help`,
`pcae intake show --help`, `pcae intake list --help` all PASS.
`pip show pcae-harness` and `import pcae; pcae.__version__` both
report `0.3.0`. (`pcae --version` non-implementation: see §5–6.)
Source install (`pip install -e .`) is the same documented path used
throughout this phase's dev-tree work and was already exercised; not
re-run a second time as a distinct method.

## 25–26. ALLOW / DENY — Stable Package

Both run against the clean stable-wheel install, in a disposable
repository, via the documented reference adapter (no mocks):

- **ALLOW**: `pcae init` → `pcae task new --allowed-file src/app.py` →
  adapter submits `src/app.py:modify:...` → `accepted: true`, `ecp_id`
  populated, `execution_allowed: false` → `pcae promotion-review
  create --promotion-authorized` → `pcae promote --dry-run` (preview,
  `would_block: false`) → `pcae promote` → `promoted: true`, file
  written only to the approved path, `git_commit_forbidden: True`.
- **DENY**: same task, adapter submits `README.md:modify:...`
  (out-of-scope) → `accepted: false`, `rejection_reasons:
  ["out_of_scope_path:README.md"]`, `ecp_id: null`, `README.md`
  unmodified on disk, rejection visible via `pcae intake list`.

## 27–28. Claude Reference Path / Generic Producer

- **Claude reference adapter**: exercised via
  `scripts/claude_code_intake_adapter.py` for both the ALLOW and DENY
  cases above — deterministic translation, no live Claude session
  required or used.
  - LIVE CLAUDE GENERATION: not exercised
  - REFERENCE ADAPTER SCRIPT: PASS
  - GENERIC PCAE INTAKE: PASS
- **Generic producer path**: hand-built the raw JSON contract from
  `docs/QUICKSTART_V0_3.md`'s Appendix (no adapter, no Claude Code
  involved), independently computed `repo_fingerprint` and
  `content_hash_after`, submitted via `pcae intake create
  --candidate-file ... --json` against the clean stable install →
  `accepted: true`. Confirms the contract is genuinely
  producer-agnostic, not merely adapter-shaped.

## 29. Quickstart Clean-Room Validation

Executed the full `docs/QUICKSTART_V0_3.md` sequence (§3–§12) from
fresh temporary repositories against the clean stable wheel install,
with no shell-history assumptions and no pre-existing PCAE task state:
init → task new → task show → adapter submit (allow) → intake show/
list → adapter submit (deny) → promotion-review create → promote
--dry-run → promote → audit trail inspection. **PASS**, end to end.

## 30. Time to First Governed Proposal

The ~5-minute positioning remains reasonable — the measured clean-room
flow above (install already done via wheel; init through first
`accepted: true` intake) took well under 5 minutes of command
execution. No documentation change needed.

## 31. Support Matrix (frozen)

```
MACOS:    Verified — clean wheel install, ALLOW, DENY, Claude
          reference adapter, generic producer, and full quickstart
          flow all exercised and passed on this host in this phase.
LINUX:    Expected — POSIX-general code path, not independently
          re-run on a Linux host in this phase (carried from Phase 2V).
WINDOWS:  Documented, Non-Blocking gap in the intake path's absolute-
          path admission check for pure-backslash paths; not claimed
          for this feature; backstopped by independent task-scope
          check.
PYTHON:   >=3.9 per pyproject.toml; exercised on 3.14 in this phase.
INPUT:    text / content_after MVP (no diff/patch, no binary).
TASK MODEL: current active governed task (single-task scope).
AGENT INTEGRATION: generic intake + Claude Code reference producer.
GENERAL RUNTIME EXECUTION: not enabled.
```

## 32–34. Test Suites / Structured Fast Green

- `tests/test_phase_149o_20l_7o_2u_2*.py`, `..._2u_3*.py`,
  `..._2u_4*.py` (intake implementation, independent verification,
  ALLOW/DENY acceptance harness): **143 passed, 0 failed.**
- `python -m pytest -n auto -m fast_green` (whole-repo structured-
  attribution sweep): **8689 passed, 337 failed, 5 skipped, 9 errors**
  — numerically identical to the Phase 2V RC-time sweep. All 337
  failures + 9 errors remain confined to the same pre-existing,
  host-state-bound `test_phase_149o_20l_7o_2n_*` /
  `test_phase_149o_20l_class_b_*` / `test_phase_149o_20e_*` HATP/HMIC/
  Class-B debt already carried forward as non-blocking historical
  debt, unrelated to intake/task-scope/promotion by file/module name.
- `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`:
  failed once under full-suite parallel load (subprocess timeout),
  passed cleanly in two subsequent isolated re-runs (`1 passed` each)
  — the same order-dependent flake documented at RC time, not a real
  defect.

**ATTRIBUTABLE FAILURES: 0.**

## 35–36. Private Content / DeepSeek Isolation

- Scanned the candidate tree and both built artifacts for secrets,
  credentials, private-host material, personal scratch data, and
  inappropriate absolute local paths: clean. The only
  `credential`/`BEGIN...KEY` pattern hits are legitimate HATP hardware-
  credential-admin source and the shell-gate secret-pattern denylist
  itself (matches its own literal pattern strings), not leaked
  secrets.
- `~/repos/pcae-deepseek-research` was **not inspected** at any point
  in this phase. `deepseek` mentions found in this repository's own
  tracked tree are pre-existing historical task/phase documents about
  an internal DeepSeek *runtime-adapter design concept* (Phases 74r/
  74s/74t/74w/95b), unrelated to and not sourced from the private
  research repository — no import or reliance on that repository
  occurred.

## 37–38. Release Notes Fact-Check / Feature Delta

Every material claim in `docs/RELEASE_NOTES_V0_3_0.md` traces to
shipped code (`pcae intake`, promotion/review chain), the documented
quickstart workflow, or the verified ALLOW/DENY/generic-producer runs
above; no unsupported claims added.

**FEATURE DELTA FROM v0.3.0-rc1 TO v0.3.0: NONE** — only version-
framing documentation changed (§3).

## 39. Tag / Release Absence (pre-mutation and re-verified)

- Local tag `v0.3.0`: ABSENT (both checked at phase entry and again
  after all content commits).
- Remote tag `v0.3.0`: ABSENT.
- GitHub Release `v0.3.0`: ABSENT (`gh release view v0.3.0` → "release
  not found").

## 40–43. Content Commits, Push, Candidate Freeze

Governed commits (via `pcae commit implementation`, no raw `git
commit`):

- `0a562517` — finalize stable v0.3.0 CHANGELOG/README/release-notes
- `71c65f16` — open task contract for v0.3.0 final release preparation

Pushed via `pcae push` (governed, no raw `git push`) to bring
`origin/main == HEAD` with a clean working tree.

**FINAL_STABLE_CANDIDATE_SHA: `<see phase-completion metadata / final
push confirmation for the exact literal value — recorded at the point
of push, no further content commit occurs after this line>`**

No commit occurred after the candidate SHA was frozen.

## 44. Final Release Gate

```
STABLE VERSION:                0.3.0
FINAL STABLE CANDIDATE SHA:    (frozen post-push HEAD; see push confirmation)
FEATURE DELTA FROM RC:         NONE
WHEEL:                         PASS
SDIST:                         PASS
WHEEL SHA256:                  4fb566da3b55fda8f6cee48f06b5e59bd96c180d1b9cebabb9a3252a599376d0
SDIST SHA256:                  1e56b64cb2c89a4539430c0f7d5e7d2c642d14a1255b7427bbbc97ad98ce0846
CLEAN INSTALL:                 PASS
CLI:                           PASS
ALLOW:                         PASS
DENY:                          PASS
CLAUDE REFERENCE PATH:         PASS
GENERIC PRODUCER:               PASS
QUICKSTART:                    PASS
STRUCTURED FAST GREEN:         PASS
ATTRIBUTABLE FAILURES:         0
PRIVATE CONTENT CHECK:         PASS
DOCS:                          PASS
FINAL RELEASE BLOCKERS:        0
TAG:                           ABSENT
GITHUB RELEASE:                ABSENT
WORKING TREE:                  CLEAN
ORIGIN PARITY:                 YES
RECOMMENDATION:                GO
```

## 45. Publication Stop

RECOMMENDATION = GO, FINAL RELEASE BLOCKERS = 0, working tree clean,
origin/main == HEAD. Per phase instructions, this phase stops here and
does not create the `v0.3.0` tag or GitHub Release. Publication
authorization must be requested from the human separately, quoting the
exact frozen `FINAL_STABLE_CANDIDATE_SHA`.

## 55. No-Go / Forbidden Actions Confirmation

None of the forbidden actions (product features, Windows repair,
fingerprint redesign, binary/multi-task support, Codex/DeepSeek
integration, DeepSeek-repo inspection, runtime execution activation,
Permission Broker enforcement, HATP/FIDO2/WebAuthn resumption, Dell
mutation, PyPI publication, article/social drafting, tag/release
creation, force-push, raw git push, history rewrite) were taken in
this phase.

## 56. Findings

| ID | Finding | Class | Notes |
|----|---------|-------|-------|
| F-2V1-1 | `pcae --version` not implemented | Non-Blocking | Pre-existing since v0.1 (carried from Phase 2V's F-2V-1); no action for v0.3.0 |
| F-2V1-2 | Windows-path admission gap in intake absolute-path check | Non-Blocking | Carried forward unchanged from Phase 2V; no behavior change, documentation does not overclaim Windows support |
| F-2V1-3 | Repository-fingerprint is content-bound, not location-bound | Non-Blocking | Carried forward unchanged from Phase 2V; documentation proportional, no cryptographic-uniqueness claim made |
| F-2V1-4 | 337 pre-existing HATP/HMIC/Class-B `fast_green` failures + 9 errors | Non-Blocking | Numerically identical to Phase 2V RC-time sweep; unrelated to intake/task-scope/promotion by file/module name |
| F-2V1-5 | `test_shell_gate.py::test_audit_verify_cli` order-dependent flake | Observation | Fails only under full-suite parallel load; passes cleanly in isolation; same as documented at RC time |

## 61. Next Phase

After successful stable publication (pending explicit human
authorization), the recommended next phase is
**149O.20L.7O.2V.2 — v0.3.0 Release Article Draft and Editorial Review
Preparation** — a local-only, non-repository-publishing phase per its
own scope definition. Not begun in this phase.
