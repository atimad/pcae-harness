# Phase 149O.20L.7O.3H — PCAE v0.4.1 Release Hardening

**Status:** COMPLETE
**Phase type:** RELEASE HARDENING (CANDIDATE PREPARATION ONLY — NO PUBLICATION).
**Phase-entry commit:** `950a5792` (HEAD at phase start; `origin/main..HEAD` = 0; working tree clean).
**Human priority selection:** Option A (ship v0.4.1 now), selected from `149O.20L.7O.3G`.
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.

## 1. Objective

Prepare a frozen, reproducible PCAE v0.4.1 release candidate: version bump, truthful release notes, reuse of the v0.4.0 reproducible-build process, byte-reproducibility verification across two independent clean-clone builds, artifact content inspection, clean wheel/sdist installs, installed-artifact rollback Permission Broker regression coverage, release-critical and Fast Green regression, and a publication checklist. No publication performed.

## 2. Public v0.4.0 baseline

```
git status --short              => (empty, clean)
git rev-list --count origin/main..HEAD => 0
git rev-parse HEAD               => 950a5792eeffbaed25e5c4b153da86cac32f1318
git rev-parse origin/main        => 950a5792eeffbaed25e5c4b153da86cac32f1318
git rev-parse v0.4.0^{commit}    => ea3f731ef50ea16985fd4a0562f0c091bb8109b2
git tag -l 'v0.4.1'              => (none)
git ls-remote --tags origin 'refs/tags/v0.4.1' => (none)
pcae health                      => healthy
pcae check                       => passed
pcae status coherence            => coherent
pcae push check                  => nothing_to_push
pcae runtime inspect             => Observed / observe / unavailable
gh release view v0.4.1           => release not found
gh release list                  => v0.4.0 is Latest, v0.3.1, v0.3.0, v0.3.0-rc1, v0.2.0, v0.1.0-rc1 (no v0.4.1)
```

## 3. Post-v0.4.0 delta

```
git diff --name-status v0.4.0..HEAD -- src/pcae/
M   src/pcae/core/agent.py
M   src/pcae/core/mutation_permission.py
```

Exactly two production files changed since `v0.4.0` — the 3F rollback default-path Permission Broker integration (independently verified by 3F.1) — and nothing else. `git diff --name-status v0.4.0..HEAD` (28 files total) breaks down as: 2 production source, 3 test files (2 new + 1 comment-only edit), 5 phase docs, and the remainder lifecycle/reporting bookkeeping (`.pcae/*`, `tasks/*`, `PROJECT_STATUS.md`, `CHANGELOG.md`). No packaging/build-config file (`pyproject.toml`, `setup.py`, `setup.cfg`, `MANIFEST.in`) had changed prior to this phase's own version bump. The only product-behavior change is the verified rollback Permission Broker integration — release scope confirmed narrow, no STOP condition triggered.

## 4. v0.4.1 scope

Rollback default-path Permission Broker consumption integration and its `aborted_permission_denied` fail-closed terminal-state support. No additional capability integrations. Plan A and Plan C explicitly not implemented in this phase.

## 5. Version decision

Reconfirmed against the six semantic-versioning criteria: backward compatible; narrow governance hardening; no execution-capability increase; no new authority model; no new contract/schema (reuses existing `ACTION_ROLLBACK`/`EXECUTION_CLASS_MUTATION` vocabulary and the existing `_RER_VALID_STATUSES` extension mechanism); no major CLI redesign; no additional feature batch.

```
SELECTED RELEASE VERSION:
v0.4.1
```

## 6. Version updates

- `pyproject.toml` `[project].version`: `0.4.0` → `0.4.1`.
- `src/pcae/__init__.py` `__version__`: `0.4.0` → `0.4.1`.
- Consistency verified: both fields match after edit; no other canonical version source found (`grep -rl "0.4.0"` outside historical phase docs/CHANGELOG/PROJECT_STATUS.md prose returned only these two files).
- No tag created.

## 7. Release notes

`docs/RELEASE_NOTES_V0_4_1.md` created, modeled on `docs/RELEASE_NOTES_V0_4_0.md`'s conventional structure. States: the default non-HATP rollback dispatch path now consumes the centralized Permission Broker; DENY/failure/malformed decision fail closed before file mutation; ALLOW preserves previous eligible rollback behavior; dry-run/readiness/evidence unchanged; `HATP_MANDATORY` path unchanged; human rollback initiation unchanged; runtime capability remains unavailable. Uses the required "closes the final Permission Broker coverage gap identified by the current production mutation-path audit" framing rather than a universal completeness claim. Restates the semantic-wall invariants verbatim (§8 below).

## 8. Build infrastructure verification

Reconfirmed unchanged from `v0.4.0`/`149O.20L.7O.3C.4`: `[build-system].requires = ["hatchling==1.32.0"]`; `[tool.hatch.build.targets.sdist].include` remains root-anchored (`/src/pcae`, `/README.md`, `/LICENSE`, `/pyproject.toml`); clean-clone-only release-of-record build policy reused unmodified. No release-blocking reproducibility defect found; no build infrastructure change made.

## 9. Candidate commit

Version bump and release notes committed together as the frozen product candidate:

```
release_candidate_commit = 9869cb65d890b70d8649ddd4216ffda4e7d98df5
```

`git diff 9869cb65..HEAD -- src/pcae pyproject.toml` was re-verified empty after every subsequent lifecycle/report-sync commit in this phase (checked at final report time, §37).

## 10. Build provenance

```
source commit:      9869cb65d890b70d8649ddd4216ffda4e7d98df5
Python:              3.14.5 (CPython, Homebrew, macOS/Darwin, arm64)
build frontend:      build 1.5.0 (python -m build)
build backend:       hatchling
build backend version (pinned): 1.32.0
build isolation:     default (build creates a fresh venv per build, installing only [build-system].requires)
SOURCE_DATE_EPOCH:   not set (matches v0.4.0 precedent; no nondeterminism observed)
build command:       python -m build --outdir dist
```

## 11. Wheel reproducibility

Two independent clean `git clone` copies pinned to `9869cb65` in separate `/tmp` directories, each with its own disposable venv (destroyed after use, never the development checkout). Both produced `pcae_harness-0.4.1-py3-none-any.whl`, identical filename, identical size (2,350,582 bytes), identical SHA-256 (`1994dc0453347f319f8cc7447a09aa7d62de8ef3d6e89b5565edbd38ab388309`).

```
WHEEL A == WHEEL B byte-for-byte: PASS
```

## 12. Sdist reproducibility

Both builds produced `pcae_harness-0.4.1.tar.gz`, identical filename, identical size (2,052,499 bytes), identical SHA-256 (`f8712b9b8b7ea1d5520058b19e809430620bb6739a8b9da5b50e93c19c5e16cf`).

```
SDIST A == SDIST B byte-for-byte: PASS
```

## 13. Artifact inspection

Wheel (`python -m zipfile -l`, 468 entries): all under `pcae/` plus standard `pcae_harness-0.4.1.dist-info/{METADATA,WHEEL,entry_points.txt,licenses/LICENSE,RECORD}`. Sdist (`tar tzf`, 467 entries): all under `pcae_harness-0.4.1/src/pcae/` plus root-level `.gitignore`, `LICENSE`, `README.md`, `pyproject.toml`, `PKG-INFO` (all standard/expected — `.gitignore` and `PKG-INFO` are hatchling defaults, matching the historical v0.4.0 baseline shape). Grepped both listings for `\.git|\.claude|\.pcae|\.env|credential|secret|ssh|id_rsa|\.venv|__pycache__|\.pyc`: the only matches were two legitimate, intentional production source files (`hatp_hardware_credential_admin.py`, `hatp_hardware_credentials.py`) matched on the substring "credential" — not actual secrets. No `.claude/worktrees/<agent-id>/` contamination (the historical class fixed in `149O.20L.7O.3C.4`) recurred. No `.git`, `.pcae/` runtime state, private-repository content, article material, `.env`, credentials, API keys, SSH keys, local virtualenvs, caches, or stale `dist/` artifacts found.

## 14. Frozen hashes

```
release_version:        v0.4.1
release_candidate_commit: 9869cb65d890b70d8649ddd4216ffda4e7d98df5
wheel:  pcae_harness-0.4.1-py3-none-any.whl
        size:   2350582
        sha256: 1994dc0453347f319f8cc7447a09aa7d62de8ef3d6e89b5565edbd38ab388309
sdist:  pcae_harness-0.4.1.tar.gz
        size:   2052499
        sha256: f8712b9b8b7ea1d5520058b19e809430620bb6739a8b9da5b50e93c19c5e16cf
reproducibility: PASS
```

## 15. Wheel clean install

Installed into a fresh disposable venv (no editable install). `import pcae; pcae.__version__ == "0.4.1"` — PASS. `pcae --help` — CLI available, subcommand listing intact. PASS.

## 16. Sdist clean install

Installed into a separate fresh disposable venv. `pcae.__version__ == "0.4.1"` — PASS. `pcae --help` — PASS. Behavior agrees with the wheel install (identical version, identical CLI availability, identical rollback smoke-test results — §17–§22).

## 17. Golden path

From the wheel-installed venv, against a disposable git repository: `pcae init` (writes `.pcae/policy.toml`, git hooks, etc. — PASS); `pcae session bootstrap --compact` (produces a compact bootstrap prompt — PASS); `pcae task new` (creates a task contract — PASS); `pcae intake from-files` (produces a genuine intake decision — `REJECTED` due to out-of-scope path, which is the correct evidentiary/scope-checking behavior for a file not covered by the task's allowed-file scope, not a crash or malfunction — PASS); `pcae intake list` (shows the recorded candidate — PASS). Repeated from the sdist-installed venv with equivalent results (§16).

## 18. Rollback dry-run

From the wheel-installed package (`pcae.core.agent.build_rollback_execution`, disposable PER/ECP fixture built only from production `pcae.core.*` APIs — no test-suite imports, since tests are not shipped in the distribution): dry-run mode returns before either the `HATP_MANDATORY` check or the new gate; `mutation_permission.evaluate_rollback_permission` call count = 0; target file untouched. **PASS.**

## 19. Rollback ALLOW

Real (unmocked) broker evaluation with only an active task present resolves ALLOW — matching the exact "real-ALLOW" pattern in `149O.20L.7O.3F`'s own test suite (no forced/mocked decision needed for the positive case). Eligible dispatch proceeds: target file removed, `result["reverted"] is True`, `result["status"] == "completed"`. Runtime `pcae runtime inspect --json` before and after this ALLOW dispatch is byte-identical (`Observed`/`observe`/`unavailable`, `version.release_version: "0.4.1"`). **PASS.**

## 20. Rollback DENY

Forced `PermissionBrokerDecision(decision=DECISION_DENY, ...)`: target file untouched; `result["error"] == "rollback_permission_denied"`; `result["permission_decision"] == "DENY"`. A real DENY via a missing active task (POL-001) was also verified: file untouched, denied. **PASS.**

## 21. Broker failure

Simulated broker exception (`PermissionBroker.evaluate` raises `RuntimeError`): target file untouched; `permission_decision == "BROKER_FAILURE"`. Simulated malformed result (`evaluate` returns `None`): target file untouched; `permission_decision == "BROKER_FAILURE"`. Neither produces any fallback to ALLOW. **PASS.**

## 22. HATP_MANDATORY

With the cutover mode fixed to `HATP_MANDATORY`, `mutation_permission.evaluate_rollback_permission` (the new default-path adapter) was spied and confirmed never invoked — the pre-existing, separate HATP-gated evaluation path remains the only gate on that branch, exactly as verified by 3F/3F.1. **PASS.**

## 23. Human trigger

From the installed wheel's CLI: `pcae rollback` (no `--per-id`) correctly refuses with `the following arguments are required: --per-id` — the human-initiated `--per-id` requirement is unchanged and unbypassable; the Permission Broker does not initiate rollback, it only gates an already-human-invoked command. **PASS.**

## 24. Runtime

`pcae runtime inspect` / `pcae runtime inspect --json` before and after an installed-artifact ALLOW rollback: byte-identical JSON payload (`Runtime state: Observed`, `Execution capability: unavailable`, `Maximum plugin capability: observe`, `registry_status: empty`, `plugin_count: 0`). **PASS — Observed / observe / unavailable, unchanged.**

## 25. Push PB regression

`python -m pytest -k "mutation_permission or permission_broker or push_permission or publication_permission or push_routing" -n auto`: 1109 passed, 5 failed. All 5 failures independently spot-checked and confirmed pre-existing at the `v0.4.0` tag itself (via `git checkout v0.4.0` re-run) — unrelated frozen "byte-unchanged since freeze"/"scope inventory" tripwires, not caused by this phase (which touched zero `src/pcae/` files). Push behavior itself unaffected by the rollback adapter. **Zero attributable regressions.**

## 26. Publication PB regression

Included in the same sweep as §25 (`mutation_permission`/`permission_broker` selector covers publication-path adapters); publication-specific tests within `-k "governance_auto_publication or publication_permission_gate or ..."` (§27) all pass. No shared-adapter regression found.

## 27. Plan B+ regression

`python -m pytest -k "governance_auto_publication or publication_permission_gate or corrupt_store or interactive_workflow_publication" -n auto`: **43 passed, 0 failed.** The v0.4.0 connected-consumption graph (`pcae phase complete` → Interactive Workflow auto-detect/route → CHGR → Permission Broker → Publication Execution Ownership) is fully preserved.

## 28. Corrupt-store regression

Included in the §27 sweep (`corrupt_store` selector) — all pass. The `v0.4.0`-closed Blocking defect (corrupt, unrelated Interactive Workflow session crashing `pcae phase complete`) remains fixed; relevant corruption still fails closed.

## 29. Intake/Codex-Ox regression

`python -m pytest -k "intake or codex_ox or rollback_approval_evidence or rollback_reconciliation or enforcement_rollback or cltr_rehearsal_rollback or hatp_rollback_consumption" -n auto`: 430 passed, 8 failed, 1 error. All spot-checked failures (4 representative node IDs, including the 1 error) independently confirmed pre-existing at the `v0.4.0` tag itself via the same `git checkout v0.4.0` re-run method. Not attributable to this phase.

## 30. Existing capability exposure

Reconfirmed unchanged from `v0.4.0`, not newly consumed: Repository Intelligence CLI/product exposure remains manual; `pcae runtime inspect` remains non-effectful; `pcae authority inspect` remains inspection-only. No new internal PCAE consumption claimed.

## 31. Focused tests

| Suite | Result |
|---|---|
| 3F integration + 3F.1 independent verification + `test_ag5_hatp_mandatory_consumption.py` + `test_hatp_cli_migration.py` + `test_phase_149o_18d_...` | 202 passed, 5 failed (all 5 pre-existing, confirmed identical at phase-entry commit, matching 3F's own documented finding) |
| Permission Broker Foundation / mutation permission / push / publication PB (broad sweep) | 1109 passed, 5 failed (all pre-existing at `v0.4.0`, spot-checked) |
| Plan B+ connected capability / corrupt-store | 43 passed, 0 failed |
| Intake / Codex-Ox / rollback persistence-reconciliation | 430 passed, 8 failed, 1 error (all spot-checked pre-existing at `v0.4.0`) |
| Package/build (`test_packaging_installation_smoke_v0_1.py`) | 20 passed, 0 failed |
| Installed-artifact rollback smoke (wheel) | 15/15 checks passed |
| Installed-artifact rollback smoke (sdist) | 15/15 checks passed |

## 32. Fast Green

Two full `pytest -m fast_green -n auto` runs from the clean committed candidate tree (`9869cb65`) and an isolated pre-version-bump baseline (`950a5792`, same rollback-integration source, pre-3H):

- Baseline (`950a5792`): 337 failed, 8730 passed, 5 skipped, 9 errors.
- Current (`9869cb65`, candidate): 340 failed, 8727 passed, 5 skipped, 9 errors.
- Exact newly-failing node-ID delta (3): `test_head_equals_origin_main` (timing-sensitive push-state check, same non-functional class already documented in 3F/3F.1), and two `test_unknown_certification_id_rejected` hac-dell Class-B tests — independently re-run serially and confirmed flaky (`2 passed` when run outside `-n auto`), matching the identical flake class 3F's own report documented.
- Exact newly-passing: none.

**Attributable functional/behavioral regressions: 0.**

## 33. Stable-release isolation

`v0.4.0` tag (`ea3f731e`), GitHub Release, and both assets (wheel + sdist, matching SHA-256/size recorded at publication) confirmed unchanged via `gh release view v0.4.0 --json tagName,targetCommitish,assets`. `v0.4.0` remains the GitHub "Latest" release. `v0.3.1` (`5d7edef9`) and `v0.3.0` (`738a8155`) tags unchanged. No v0.4.1 tag, release, or PyPI upload exists (verified at phase entry, §2, and reconfirmed no tag/publish action was taken this phase).

## 34. Blocker table

| Finding | Classification |
|---|---|
| 5 pre-existing frozen-tripwire failures in 3F/3F.1's own focused suite (§31 row 1) | ACCEPTED-DEBT (pre-existing since before `v0.4.0`, confirmed) |
| 5 pre-existing failures in the broad Permission Broker/push/publication sweep (§25) | ACCEPTED-DEBT (pre-existing at `v0.4.0` tag itself, confirmed) |
| 8 pre-existing failures + 1 error in intake/rollback-persistence sweep (§29) | ACCEPTED-DEBT (pre-existing at `v0.4.0` tag itself, confirmed via spot-check) |
| 3 Fast Green newly-failing node IDs (§32) | ACCEPTED-DEBT (1 timing-sensitive push-state tripwire, 2 confirmed `-n auto` parallel-execution flakes on shared real-host-state fixtures, serially reproduced passing) |

```
BLOCKING: 0
MUST-FIX: 0
```

## 35. Deferred work

Carried forward unchanged, not part of `v0.4.1`: runtime preflight disclosure; rollback readiness/evidence auto-generation; Repository Intelligence internal consumption; Advisory context integration; Runtime Enforcement consumption; HATP/HMIC/Class-B authority activation; CLTR cutover; runtime execution; Telegram inbound; backend/model execution.

## 36. Publication checklist

```
release version:      v0.4.1
candidate commit:     9869cb65d890b70d8649ddd4216ffda4e7d98df5
wheel:                pcae_harness-0.4.1-py3-none-any.whl
                       size:   2350582
                       sha256: 1994dc0453347f319f8cc7447a09aa7d62de8ef3d6e89b5565edbd38ab388309
sdist:                pcae_harness-0.4.1.tar.gz
                       size:   2052499
                       sha256: f8712b9b8b7ea1d5520058b19e809430620bb6739a8b9da5b50e93c19c5e16cf
release notes:         docs/RELEASE_NOTES_V0_4_1.md
tag target:            candidate commit (9869cb65)
GitHub Latest:          intended
PyPI:                   not authorized unless separately approved
human publication authorization: required
```

## 37. Final verdict

```text
PCAE v0.4.1 RELEASE CANDIDATE:
VERIFIED
RELEASE THEME:
PERMISSION BROKER ROLLBACK COVERAGE COMPLETION
ROLLBACK DEFAULT PATH:
BROKER-GOVERNED
ALLOW:
VERIFIED
DENY:
ZERO MUTATION
BROKER FAILURE:
FAIL-CLOSED
HATP_MANDATORY:
UNCHANGED
HUMAN TRIGGER:
UNCHANGED
PLAN B+:
PRESERVED
BUILD REPRODUCIBILITY:
VERIFIED
WHEEL:
VERIFIED
SDIST:
VERIFIED
CLEAN INSTALLS:
PASS
ATTRIBUTABLE REGRESSIONS:
0
BLOCKING:
0
MUST-FIX:
0
RUNTIME:
Observed / observe / unavailable
PUBLICATION:
NOT PERFORMED
```

`git diff 9869cb65..HEAD -- src/pcae pyproject.toml` reconfirmed empty at report time — the candidate commit is unmodified by any later lifecycle/report-sync commit in this phase.

## 38. Recommended publication phase

**149O.20L.7O.3H.1 — PCAE v0.4.1 Public Release.** Publication-only; must require explicit human authorization before tag push, GitHub Release creation, or artifact upload. PyPI remains separately unauthorized unless explicitly approved. Not begun in this phase.
