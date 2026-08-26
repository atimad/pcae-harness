# Phase 149O.20L.7O.3O — PCAE v0.4.3 Release Hardening

**Status: RELEASE-CANDIDATE PREPARATION ONLY. NO PUBLICATION PERFORMED.**

## 1. Objective

Prepare a frozen, independently-verified `v0.4.3` release candidate
implementing the human-selected **RELEASE NOW** decision from
`149O.20L.7O.3N`/`3N.1`: ship `3M`'s already-verified rollback
evidence-visibility enhancement as a narrow patch release. This phase
does not implement new rollback preparation automation, does not
change Permission Broker behavior, does not implement true RI-backed
reasoning, and does not publish (no tag, no GitHub Release, no PyPI
upload).

## 2. v0.4.2 baseline

Verified at phase entry:

- `git status --short`: clean.
- `git rev-list --count origin/main..HEAD`: `0`.
- `HEAD` == `origin/main` == `674dc8a30cd9a634d6356dae4297c187df4f22e9`.
- `v0.4.2^{commit}` == `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`,
  unchanged.
- No local or remote `v0.4.3` tag existed.
- `pcae health`: healthy. `pcae check`: passed. `pcae status
  coherence`: coherent. `pcae doctor task-memory`: warnings only
  (pre-existing historical `tasks/DONE.md` sync-debt, unrelated to this
  phase — carried forward, not repaired). `pcae push check`: nothing to
  push (clean, `Mode: nothing_to_push`). `pcae runtime inspect`:
  `Observed` / `observe` / `unavailable`, registry empty, 0 plugins, 0
  capabilities. Telegram notify sink: configured, enabled, ready.

## 3. Post-v0.4.2 delta

`git diff --name-status v0.4.2..HEAD` at phase entry showed 39 files
changed, of which exactly **two** touched production source
(`git diff v0.4.2..HEAD -- src/pcae`):

- `M src/pcae/commands/agent.py` — `run_rollback` CLI printing gains
  `file_plan`/`divergence_check` lines on relevant terminal paths.
- `M src/pcae/core/agent.py` — `build_rollback_execution` computes
  `_evidence_summary = {"file_plan": file_plan, "divergence_check":
  divergence}` once (evidence already computed unconditionally) and
  merges it, additively, into the divergence-conflict,
  HATP_MANDATORY-denial, Permission-Broker-denial, and final
  success/partial/failure result dictionaries; the dry-run branch gains
  `file_plan` in its own pre-existing dict.

Both changes are exactly `149O.20L.7O.3M`'s evidence-visibility
integration. All other changed files were: new test modules (`3M`,
`3M.1`), phase/reporting docs, `PROJECT_STATUS.md`/`CHANGELOG.md`
status metadata, `.pcae/fast-green-attribution/*.json` evidence
artifacts, and task-lifecycle files. This confirms the only intended
post-`v0.4.2` product behavior change is the `3M` rollback
evidence-visibility enhancement — no other product behavior change
exists, so no scope reassessment or STOP was required.

## 4. Corrected rollback evidence semantics

Per `149O.20L.7O.3M.1`'s independent verification (re-affirmed, not
re-litigated, in this phase): rollback's `file_plan` and
`divergence_check` evidence was **already** computed unconditionally
for every non-early-error invocation of `build_rollback_execution`,
**already** internally consumed to gate every rollback outcome
(divergence-conflict short-circuit, HATP/PB denial paths), and
**already** persisted verbatim in the canonical
`RollbackExecutionRecord`, before `3M` existed. `3M`'s only change was
adding that already-computed, already-consumed evidence to the
*returned*/printed result of `pcae rollback`, which previously required
a separate `pcae rollback-execution show <rer_id>` call to see. Manual
dry-run was never, and is not now, a prerequisite for a real rollback.
Human rollback trigger, Permission Broker sequencing, and HATP
semantics are all pre-existing and unchanged.

## 5. Release scope

Narrow patch release: rollback evidence visibility only.
OBSERVABILITY / DEBUGGABILITY / USABILITY HARDENING. Not new rollback
preparation automation, not new readiness, not new authority, not new
Permission Broker behavior, not new execution capability.

## 6. Version

`v0.4.3` (patch-level), per this project's established
semantic-version criteria: additive output field, backward compatible,
no authority-model change, no execution-capability change, no
Permission Broker semantics change, no contract/schema redesign, no
new conceptual CLI workflow.

- `pyproject.toml`: `version = "0.4.2"` → `"0.4.3"`.
- `src/pcae/__init__.py`: `__version__ = "0.4.2"` → `"0.4.3"`.
- No other canonical version source found (`PROJECT_STATUS.md`/
  `CHANGELOG.md` `0.4.2` references are historical phase narration,
  intentionally left unmodified).

## 7. Release notes

`docs/RELEASE_NOTES_V0_4_3.md` created. Theme: Rollback Evidence
Visibility. States: rollback commands now surface the already-computed
file plan and divergence evidence in terminal output (including
divergence-conflict, HATP_MANDATORY denial, Permission Broker denial,
and final success/partial/failure paths); explicitly states rollback
preparation was **already automatic before v0.4.3** and this release's
change is evidence surfacing / observability only; states evidence
never authorizes rollback; Permission Broker, HATP, human trigger, and
runtime are all unchanged; dry-run remains optional, not a
prerequisite.

## 8. Documentation audit

Searched `README.md` and `QUICKSTART_V0_3.md` for "prerequisite",
"must run", "before rolling back"/"before rollback", and "dry-run"
occurrences. No instance claims manual dry-run is mandatory before a
real rollback; all existing dry-run references describe it as an
optional preview flag. No incorrect wording found; no correction
required. Historical phase reports (`3M`, `3M.1`, `3N`, `3N.1`, etc.)
were not rewritten.

## 9. Build infrastructure

Reused unmodified: `[build-system].requires = ["hatchling==1.32.0"]`;
`[tool.hatch.build.targets.sdist]` root-anchored `include` patterns
(`/src/pcae`, `/README.md`, `/LICENSE`, `/pyproject.toml`). No build
infrastructure changes were required or made.

## 10. Candidate

`release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6`
(`pcae commit implementation`, committing `pyproject.toml`,
`src/pcae/__init__.py`, `docs/RELEASE_NOTES_V0_4_3.md`, and the active
task contract). `git diff 63580893b1de4782a694ab802ff7bdebdf29b0e6..HEAD
-- src/pcae pyproject.toml docs/RELEASE_NOTES_V0_4_3.md` remained empty
through phase completion (verified before `phase complete`).

## 11. Build provenance

- Source commit: `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
- Python: 3.14.5 (both build environments).
- Frontend: `build` 1.2.2 (PEP 517 isolated build).
- Backend: `hatchling` 1.32.0 (pinned, matches `[build-system].requires`).
- Build command: `python -m build --outdir dist` (each clone, its own
  fresh venv with only `build==1.2.2`/`hatchling==1.32.0` installed).
- Environment controls: two independent `git clone --no-local` clones
  of the candidate-commit worktree, each checked out to
  `63580893b1de4782a694ab802ff7bdebdf29b0e6` in detached HEAD, each
  built in its own fresh Python venv, no shared build cache.

## 12. Wheel reproducibility

`pcae_harness-0.4.3-py3-none-any.whl` — identical filename, identical
size (2,352,742 bytes), identical SHA-256
(`e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4`)
across both clones; `cmp` byte-for-byte identical. **PASS.**

## 13. Sdist reproducibility

`pcae_harness-0.4.3.tar.gz` — identical filename, identical size
(2,054,469 bytes), identical SHA-256
(`8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276`)
across both clones; `cmp` byte-for-byte identical. **PASS.**

## 14. Artifact inspection

Inspected wheel (`unzip -l`) and sdist (`tar tzf`) listings, plus a
targeted grep for `.git/`, `.claude/worktrees`, `.env`, `credential`,
`.key`, `__pycache__`, `.venv`, and `deepseek` (private-research
repository marker). The only matches were legitimate source filenames
(`hatp_hardware_credential_admin.py`, `hatp_hardware_credentials.py`) —
false positives on the substring "credential", not secret material. No
`.git`, no `.claude/worktrees`, no private-research/article content, no
`.env`, no credentials/API keys/SSH keys, no virtual environments, no
caches, no stale `dist` files. Sdist contains only `src/pcae/**`,
`README.md`, `LICENSE`, `pyproject.toml`, and packaging metadata, per
the anchored `include` patterns. Wheel contains only the `pcae` package
(467 files) plus standard `dist-info` metadata. **PASS.**

## 15. Frozen hashes

- `release_version`: `v0.4.3`
- `release_candidate_commit`: `63580893b1de4782a694ab802ff7bdebdf29b0e6`
- `wheel`: `pcae_harness-0.4.3-py3-none-any.whl` / 2,352,742 bytes /
  `sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4`
- `sdist`: `pcae_harness-0.4.3.tar.gz` / 2,054,469 bytes /
  `sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276`
- `reproducibility`: **PASS**

## 16. Wheel install

Installed the frozen wheel alone into a fresh venv. Verified `import
pcae; pcae.__version__ == "0.4.3"` and the `pcae` CLI entry point
works (subcommand listing renders). Golden path exercised in a
disposable `git init`-ed directory: `pcae init` → `pcae session
bootstrap --agent-id smoke-wheel` → `pcae task new` → `pcae intake
from-files` (candidate `ACCEPTED`, `execution_allowed: False`,
`promotion_executed: False`) → `pcae intake list`/`pcae intake show`
(candidate visible, `validation_outcome: accepted`,
`integrity_verified: True`). **PASS.**

## 17. Sdist install

Installed the frozen sdist alone into a separate fresh venv. Verified
`import pcae; pcae.__version__ == "0.4.3"`. Ran the equivalent golden
path (`pcae init` → `session bootstrap` → `task new` → `intake
from-files` → `intake list`) in a second disposable directory; intake
candidate `ACCEPTED`, same evidence-only invariants held. **PASS.**

## 18. Evidence-visibility smoke

Using the installed **wheel's** own `pcae` executable (not
in-process), constructed disposable PER/ECP fixtures via
`agent.store_execution_change_package`/`store_promotion_execution_record`
(the same construction pattern `3M.1`'s independent suite uses) in
three disposable repositories and invoked the real CLI as a subprocess:

- **Dry-run** (`pcae rollback --per-id per-a --dry-run`): `rc=0`,
  output contains `Rollback: DRY RUN`, `file_plan:`, no `AUTHORIZED`
  claim.
- **Real rollback, no prior dry-run, ALLOW path**
  (`pcae rollback --per-id per-b`): `rc=0`, output contains `Rollback:
  COMPLETED`, `divergence_check:`, `b.txt: success`; target file
  removed (real effect occurred).
- **Divergence** (`pcae rollback --per-id per-c --json`, file tampered
  out-of-band before rollback): `rc=1`, JSON payload contains
  `file_plan` and `divergence_check` (`blocking: true`,
  `blocking_paths: ["c.txt"]`), `execution_allowed: false`; target file
  content unchanged (effect stopped before any write).

All three confirm file-plan/divergence-evidence visibility on the
installed artifact. **PASS.**

## 19. Result/persistence consistency

Covered by the source-tree `3M.1` independent suite (re-run this
phase, Section 34): `test_completed_result_evidence_equals_persisted_
record`, `test_failed_final_result_surfaces_evidence_equal_to_
persisted_record`, `test_partial_final_result_surfaces_evidence_equal_
to_persisted_record`, and `test_divergence_surfaces_evidence_equal_to_
persisted_and_bypasses_broker` all assert the surfaced result evidence
equals the corresponding field on the persisted `RollbackExecutionRecord`
for every terminal outcome. All passed. **PASS.**

## 20. Divergence

Section 18's Scenario C (installed wheel) and the source-tree suite's
`test_divergence_surfaces_evidence_equal_to_persisted_and_bypasses_
broker` both confirm: effect stops (`execution_allowed: false`, target
file untouched), evidence (`file_plan`, `divergence_check`) is visible,
and no authority implication is made. **PASS.**

## 21. Permission Broker DENY

Covered by the source-tree suite's
`test_clean_evidence_plus_permission_broker_deny_is_non_authoritative`
and `test_json_output_is_additive_and_truthful_on_denial`: forced DENY
produces zero mutation (target file still exists), evidence
(`file_plan`, `divergence_check`) remains visible in the JSON payload,
and evidence does not override the denial (`execution_allowed: false`,
`error: rollback_permission_denied`). **PASS.**

## 22. ALLOW path

Section 18's Scenario B (installed wheel, real CLI, no prior dry-run)
and the source-tree suite's
`test_current_real_rollback_needs_no_prior_dry_run_and_surfaces_
evidence` both confirm: evidence visible, existing effect semantics
(`Rollback: COMPLETED`, file removed, `file_results` outcomes)
unchanged from pre-`3M`/pre-`3O` behavior. **PASS.**

## 23. HATP_MANDATORY regression

Covered by the source-tree suite's
`test_hatp_denial_surfaces_same_evidence_and_never_calls_default_
adapter`: HATP_MANDATORY denial path behavior is unchanged; evidence
visibility on that path is additive only; the default (non-HATP)
adapter is never called on the HATP-mandatory path. **PASS.**

## 24. Dry-run

`pcae rollback --dry-run` remains fully functional and read-only
(Section 18 Scenario A; source-tree
`test_pre_3m_dry_run_is_optional_read_only_diagnostics`,
`test_current_dry_run_is_read_only_and_persists_no_rer`). No claim or
implementation anywhere states or implies dry-run is required before a
real rollback — confirmed both by the documentation audit (Section 8)
and by the passing "no prior dry-run" tests (Sections 18, 22). **PASS.**

## 25. Real rollback without prior dry-run

Section 18 Scenario B is exactly this: a mandatory installed-artifact
smoke exercising a real rollback with zero prior `--dry-run` call.
Evidence was computed and surfaced, Permission Broker gating occurred
normally (ALLOW, no forced denial in this scenario), and no missing
prerequisite was encountered. Cross-verified against the source-tree
`test_literal_cli_real_call_without_prior_dry_run_surfaces_final_
evidence`. **PASS.**

## 26. Human-trigger invariant

Every rollback invocation in this phase's smoke testing was an
explicit CLI command (`pcae rollback --per-id ...`); no code path in
`_evidence_summary`/`build_rollback_execution` or the CLI wrapper
triggers a rollback automatically. Source-tree
`test_only_production_cli_calls_ag5_and_human_boundary_is_explicit`
independently confirms `_RER_GOVERNANCE_BOUNDARIES["automatic_
rollback_allowed"] is False` and `["rollback_requires_explicit_human_
command"] is True` (manually re-verified via direct import when the
test's own `rg`-shellout dependency was unavailable in this sandbox —
see Section 33). **PASS.**

## 27. Evidence non-authority

Section 20 (Divergence) and Section 21 (PB DENY) both demonstrate:
clean evidence plus a blocking condition (divergence conflict or
Permission Broker DENY) still produces zero mutation; evidence being
available never itself generates authorization
(`execution_allowed: false` in every non-completed-success payload
observed this phase). **PASS.**

## 28. Runtime

`pcae runtime inspect` run before and after all rollback smoke testing
in this phase: `Runtime state: Observed`, `Maximum plugin capability:
observe`, `Execution capability: unavailable`, registry empty, 0
plugins — unchanged throughout. **PASS.**

## 29. Permission Broker regressions

Ran the representative suites:
`tests/test_phase_149o_20l_7o_3f_rollback_permission_broker_default_
path.py` (rollback PB) and
`tests/test_phase_149o_20l_7o_3f_1_independent_rollback_permission_
verification.py` (independent rollback PB verification) — 40/40
passed. No push/publication Permission Broker source changed this
phase (Section 3), so no separate push/publication PB suite regression
was expected or found. **PASS.**

## 30. RI regression (v0.4.2 RI attachment)

Ran the representative `3J`/`3J.1` suites:
`tests/test_phase_149o_20l_7o_3j_ri_advisory_production_consumption.py`
and
`tests/test_phase_149o_20l_7o_3j_1_independent_ri_advisory_consumption_
verification.py` — 46/46 passed. No source overlap with this phase's
two touched rollback files, as expected. **PASS.**

## 31. Plan B+ regression

Ran the representative
`tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_
integration.py` (Interactive-Workflow-auto-detect connected-governance
suite) — 22/22 passed. **PASS.**

## 32. Corrupt-store regression

Ran the representative
`tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_
closed_repair.py` and
`tests/test_phase_149o_20l_7o_3c_3_2_auto_publish_corrupt_store_repair_
independent_verification.py` — 43/43 passed. Previously closed defect
remains closed. **PASS.**

## 33. Intake/Codex-Ox

Ran `tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py`
(19/19 passed) plus the installed wheel/sdist golden-path `intake
from-files`/`intake list`/`intake show` exercises (Sections 16-17).
**PASS.**

## 34. 3M tests

Ran `tests/test_phase_149o_20l_7o_3m_rollback_readiness_evidence_
automatic_consumption.py` in full: 18/18 passed. **PASS.**

## 35. 3M.1 tests

Ran `tests/test_phase_149o_20l_7o_3m_1_independent_rollback_readiness_
evidence_consumption_verification.py` in full: 24/26 passed, 2 failed
with `FileNotFoundError: [Errno 2] No such file or directory: 'rg'`
(`test_only_production_cli_calls_ag5_and_human_boundary_is_explicit`,
`test_result_field_consumers_have_no_strict_rollback_key_set_
assumption`). Root cause: this sandbox has only an interactive-shell
`rg` function (aliased to the Claude Code binary), not a real
`ripgrep` binary on `PATH` reachable by a Python subprocess — confirmed
absent via `command -v rg`/filesystem search across `/opt/homebrew`,
`/usr/local`. Both tests' assertions were manually re-verified via
equivalent `grep`/direct-import checks (Sections 26, 33 for the first;
the second's underlying `grep -rnE` query independently returned zero
`rollback`-related `result.keys() ==` lines). Classification:
**environment tooling gap, not an attributable regression** —
consistent with `3M`'s own precedent (Fast Green narrative, Section
26A) of classifying environment-induced test-infrastructure failures
separately from functional regressions. The automated Fast Green
attribution run (Section 36) independently confirms this: it classifies
both as **pre-existing** (present identically on the pre-phase
baseline commit, which also lacks a real `rg` binary in this
environment), not attributable. Not repaired this phase (out of scope
— environment tooling, not product code).

## 36. Fast Green

`pcae phase fast-green-attribution --phase-id 149O.20L.7O.3O
--pushed-status not_pushed`:

- Baseline: `674dc8a30cd9a634d6356dae4297c187df4f22e9` (parent of this
  phase's oldest attributed commit).
- Candidate: `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
- Raw failures: 351 (342 failed / 9 errors).
- Attributable: **0**.
- Pre-existing: 350 (includes the two `rg`-tooling-gap tests from
  Section 35, correctly bucketed as present identically in both
  baseline and candidate).
- Environment: 0 (tool's own automatic classification; separately,
  this phase's manual investigation in Section 35 independently
  confirms the same two tests are environment-caused).
- Expected artifacts: 1.
- **Verdict: PASS.**

Full evidence artifact:
`.pcae/fast-green-attribution/e9f97517666d5746d9e6b1a0a3ec65eb44d87e0f385606818d585755eacb97de.json`.

## 37. Infrastructure debt

Carried forward unrepaired, per governing brief instruction:
**FAST GREEN PUSH-STATE ATTRIBUTION mutable/self-referential
pushed-status classification is NON-BLOCKING INFRASTRUCTURE DEBT.**
Not repaired in this release-hardening phase.

## 38. Blocker table

| Item | Classification |
| --- | --- |
| `rg`-tooling-gap in 2 `3M.1` tests (Section 35) | ACCEPTED-DEBT (environment, not product; independently confirmed non-attributable by Fast Green) |
| Fast Green push-state attribution self-referential debt (Section 37) | ACCEPTED-DEBT (carried forward, out of scope) |
| F1 (foreign-RI-snapshot-via-symlink), F2 (AdvisoryProvider scope), Decision-Evaluation explanation surfacing gap | DEFERRED (unrelated to this phase's rollback-evidence scope; carried from `3K`/`3L`/`3N.1`) |

**BLOCKING = 0. MUST-FIX = 0.**

## 39. Stable-release isolation

`v0.4.2^{commit}` == `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`
(unchanged from phase entry). `v0.4.1^{commit}` ==
`9869cb65d890b70d8649ddd4216ffda4e7d98df5` (unchanged). `git tag -l
'v0.4.*'` lists only `v0.4.0`, `v0.4.1`, `v0.4.2` — no `v0.4.3` tag
exists. **PASS.**

## 40. Mature-capability-program closure status

`149O.20L.7O.3N.1` reconfirmed: **MATURE CAPABILITY CONSUMPTION
PROGRAM: CURRENTLY EXHAUSTED AT S/M SCOPE.** This phase's `3M`
evidence-visibility release does not reopen that program — it ships
work already completed and independently verified prior to `3N`/`3N.1`,
it does not perform new S/M-scope consumption investigation, and it
adds no new consumer wiring.

## 41. Publication checklist

```
release: v0.4.3
candidate: 63580893b1de4782a694ab802ff7bdebdf29b0e6
wheel: pcae_harness-0.4.3-py3-none-any.whl / 2,352,742 bytes /
  sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4
sdist: pcae_harness-0.4.3.tar.gz / 2,054,469 bytes /
  sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276
release notes: docs/RELEASE_NOTES_V0_4_3.md
tag target: candidate (63580893b1de4782a694ab802ff7bdebdf29b0e6)
GitHub Latest: intended
PyPI: separately unauthorized
human publication authorization: required
```

Publication (tag push, GitHub Release creation, artifact upload) was
**NOT PERFORMED** in this phase.

## 42. Final verdict

```
PCAE v0.4.3 RELEASE CANDIDATE: VERIFIED
RELEASE THEME: ROLLBACK EVIDENCE VISIBILITY
ROLLBACK PREPARATION: ALREADY AUTOMATIC BEFORE v0.4.3
v0.4.3 CHANGE: EVIDENCE SURFACING / OBSERVABILITY
FILE PLAN: VISIBLE
DIVERGENCE EVIDENCE: VISIBLE
PERMISSION BROKER: UNCHANGED
HUMAN AUTHORITY: UNCHANGED
HATP: UNCHANGED
RUNTIME: Observed / observe / unavailable
BUILD REPRODUCIBILITY: VERIFIED
WHEEL: VERIFIED
SDIST: VERIFIED
ATTRIBUTABLE REGRESSIONS: 0
BLOCKING: 0
MUST-FIX: 0
MATURE S/M CONSUMPTION PROGRAM: EXHAUSTED
PUBLICATION: NOT PERFORMED
```

Recommended next phase: **149O.20L.7O.3O.1 — PCAE v0.4.3 Public
Release** (publication-only; requires explicit human authorization
before tag push, GitHub Release creation, or artifact upload; PyPI
remains separately unauthorized). After successful `v0.4.3`
publication, recommend a fresh read-only **Post-Consumption Strategic
Runtime / Provider Architecture Reassessment** (purpose: determine the
next major PCAE chapter, investigate replaceable runtime/provider
integration, preserve PCAE as governed control plane; no execution
activation in the reassessment itself; true RI reasoning remains a
separate L-scale contract/provider effort). The private research
repository (`~/repos/pcae-deepseek-research`) was not inspected,
modified, or relied upon; the article remains STOPPED.
