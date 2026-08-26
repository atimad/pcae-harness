# Phase 149O.20L.7O.3O.1 — PCAE v0.4.3 Public Release

**Status: PUBLICATION READY. NO PUBLICATION PERFORMED. HUMAN
PUBLICATION AUTHORIZATION REQUIRED AND ABSENT.**

## 1. Objective

Independently re-verify `149O.20L.7O.3O`'s frozen `v0.4.3` release
candidate for public-release readiness (build reproducibility,
version, isolation, regressions, rollback-evidence smokes, release
notes truth), then STOP at the explicit human-authorization checkpoint
before any irreversible publication action. This phase is
publication-only: no engineering, no repair-and-publish (per governing
brief §46).

## 2. Phase-entry commit

`674dc8a30cd9a634d6356dae4297c187df4f22e9` was the pre-`3O` baseline;
this phase began at `51111c84be3abcd44c61ccc396e64a12be1eca70` (post
`3O`/`3N.2`).

## 3. Baseline verification (step 1)

- `git status --short`: clean.
- `git status --branch --short`: `## main...origin/main`.
- `git rev-list --count origin/main..HEAD`: `0`.
- `HEAD` == `origin/main` == `51111c84be3abcd44c61ccc396e64a12be1eca70`.
- `v0.4.2^{commit}` == `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`,
  unchanged.
- No local `v0.4.3` tag. No remote `v0.4.3` tag
  (`git ls-remote --tags origin 'refs/tags/v0.4.3'` empty).
- `pcae health`: healthy. `pcae check`: passed. `pcae status
  coherence`: coherent. `pcae doctor task-memory`: warnings limited to
  pre-existing historical `tasks/DONE.md` sync debt (unrelated,
  carried forward, not repaired — same class of debt disclosed in
  every recent phase report). `pcae push check`: `Mode:
  nothing_to_push`. `pcae runtime inspect`: `Observed` / `observe` /
  `unavailable`. Telegram: configured, enabled, ready.
- No existing `v0.4.3` GitHub Release (not queried publicly this
  phase since no publication action is authorized; local/remote tag
  absence is the binding invariant checked).

All invariants held. No STOP required at this gate.

## 4. Release candidate (step 2)

`release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6`,
independently confirmed via `git rev-parse 63580893` and `git show -s`
against the `3O` canonical phase document
(`docs/PHASE_149O_20L_7O_3O_PCAE_V0_4_3_RELEASE_HARDENING.md`), not
solely the governing-brief summary. Commit message: "Phase
149O.20L.7O.3O: version bump 0.4.2 -> 0.4.3 and release notes
(rollback evidence visibility)".

## 5. Candidate-to-HEAD drift (step 3)

`git diff --name-status 63580893..HEAD`: 11 files changed — all
`.pcae/phase-completion-{metadata.json,report.md}`,
`.pcae/fast-green-attribution/*.json`, `CHANGELOG.md`,
`PROJECT_STATUS.md`, `docs/PHASE_149O_20L_7O_3{N_2,O}_*.md`,
`tasks/active/*`, `tasks/done/*` — i.e. `3N.2`'s later
docs/status/task-lifecycle work, exactly as the governing brief
anticipated.

`git diff 63580893..HEAD -- src/pcae pyproject.toml
docs/RELEASE_NOTES_V0_4_3.md`: **empty**. Zero release-facing product
drift. **PASS.**

## 6. Version (step 4)

`pyproject.toml` line 13: `version = "0.4.3"`.
`src/pcae/__init__.py` line 5: `__version__ = "0.4.3"`. No version
edits made this phase. **PASS.**

## 7. v0.4.2 isolation (step 5)

`v0.4.2` is an annotated tag object; `git rev-parse v0.4.2^{commit}`
== `bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`, unchanged from `3O`'s
own record. No local mutation of the tag was performed or possible
without an explicit tag-overwrite command, which was not issued.
**PASS.**

## 8. Frozen build evidence recovered (steps 6-10)

`3O`'s exact frozen wheel/sdist bytes were still present on local disk
(a separate session's scratchpad, `release-3o/clone-a` and
`clone-b`, produced by two independent `git clone --no-local` builds
pinned to the candidate commit). Recomputed hashes independently this
phase:

- `pcae_harness-0.4.3-py3-none-any.whl` — 2,352,742 bytes —
  `sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4`
  — exact match to `3O`'s frozen record, both clones, byte-identical
  (`cmp`).
- `pcae_harness-0.4.3.tar.gz` — 2,054,469 bytes —
  `sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276`
  — exact match, both clones, byte-identical (`cmp`).

`reproducibility: PASS` (independently reconfirmed, not merely
re-cited). No rebuild fallback (step 8) was needed since exact `3O`
bytes were recovered and verified.

Independent re-scan of both artifacts (step 9) for `.git/`,
`.claude/worktrees`, `deepseek`, `.env`, `credential`, `.key`,
`__pycache__`, `.venv`: only the same two false-positive legitimate
source filenames `3O` itself found
(`hatp_hardware_credential_admin.py`, `hatp_hardware_credentials.py`,
substring match on "credential", not secret material). No
contamination. **PASS.**

Frozen publication tuple (step 10):

```
release_version: v0.4.3
release_candidate_commit: 63580893b1de4782a694ab802ff7bdebdf29b0e6
wheel: pcae_harness-0.4.3-py3-none-any.whl / 2,352,742 bytes /
  sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4
sdist: pcae_harness-0.4.3.tar.gz / 2,054,469 bytes /
  sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276
reproducibility: PASS
```

## 9. Pre-publication wheel install (step 11)

Fresh venv, frozen wheel installed alone. `import pcae;
pcae.__version__ == "0.4.3"` — confirmed. Golden path in a disposable
`git init`-ed directory: `pcae init` → `pcae session bootstrap
--agent-id smoke-301-wheel` → `pcae task new` (with an explicit
`--allowed-file` scope) → `pcae intake from-files` → `ACCEPTED`,
`execution_allowed: False`, `promotion_executed: False` →
`pcae intake list` shows the candidate. **PASS.**

## 10. Pre-publication sdist install (step 12)

Separate fresh venv, frozen sdist installed alone. Same version check
and equivalent golden path repeated independently: `ACCEPTED`,
`execution_allowed: False`, `promotion_executed: False`. **PASS.**

## 11. Rollback evidence visibility smoke (steps 13-19)

Reused `3O`'s own fixture-construction script
(`wheel_rollback_smoke.py`, same PER/ECP construction pattern as the
`3M.1` independent suite) and re-ran it fresh against the installed
wheel's real `pcae` CLI executable (subprocess, not in-process):

- **Dry-run**: `rc=0`, `DRY RUN` present, `file_plan` present, no
  `AUTHORIZED` claim.
- **Real rollback, no prior dry-run** (mandatory, step 14): `rc=0`,
  `COMPLETED`, `divergence_check` present, target file removed (real
  effect occurred with zero prior `--dry-run` call).
- **Divergence**: `rc=1`, `file_plan`/`divergence_check` present,
  `execution_allowed: false`, target file unchanged (effect stopped
  before any write).

Evidence/persistence consistency (step 15) and evidence non-authority
(step 16) are covered by the source-tree `3M.1` suite (re-run in
Section 12) which asserts surfaced-result evidence equals the
persisted `RollbackExecutionRecord` for every terminal outcome, and
that clean evidence plus Permission Broker `DENY` still yields zero
mutation. Human trigger (step 17): every invocation was an explicit
CLI command; no automatic trigger exists. HATP isolation (step 18):
`HATP_MANDATORY` semantics untouched — only evidence visibility
differs, per Section 12. Runtime invariant (step 19): `pcae runtime
inspect` before and after this smoke: `Observed` / `observe` /
`unavailable`, unchanged. **PASS.**

## 12. Regression suites (steps 20-25, 34-35)

Ran on current `HEAD` (`51111c84`) source tree:

- `test_phase_149o_20l_7o_3f_rollback_permission_broker_default_path.py`
  + `..._3f_1_independent_rollback_permission_verification.py`
  (Permission Broker regression, step 22).
- `..._3j_ri_advisory_production_consumption.py` +
  `..._3j_1_independent_ri_advisory_consumption_verification.py` (RI
  regression, step 20).
- `..._3c_2_governed_capability_consumption_integration.py` (Plan B+
  regression, step 21).
- `..._3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py` +
  `..._3c_3_2_..._independent_verification.py` (corrupt-store
  regression, step 23).
- `..._2x_codex_ox_agent_registration.py` (intake/Codex-Ox
  regression, step 24).
- `..._3m_rollback_readiness_evidence_automatic_consumption.py` +
  `..._3m_1_independent_rollback_readiness_evidence_consumption_
  verification.py`.

Combined: **212 passed, 2 failed**. Both failures are the identical
`rg`-tooling-gap tests `3O` already disclosed (`FileNotFoundError: No
such file or directory: 'rg'` — this sandbox lacks a real `ripgrep`
binary on `PATH`; only an interactive-shell alias exists). Same two
tests, same root cause, same non-attributable classification as `3O`'s
own Fast Green run. **ACCEPTED-DEBT, not a regression.**

Prompt/bootstrap regression (step 25): `pcae session bootstrap` was
run repeatedly this phase (Section 3, and via the fresh-venv golden
paths in Sections 9-10) and produces its deterministic prompt/
instruction output every time; no provider dispatch occurred; runtime
remained `unavailable` throughout. **PASS.**

## 13. Release notes truth audit (step 26)

`docs/RELEASE_NOTES_V0_4_3.md` reviewed in full. States "Rollback
preparation was already automatic before v0.4.3" and "this release's
change is evidence surfacing / observability only"; explicitly denies
new automation, new authority, new Permission Broker semantics, and
any prompt-generation-integration claim. Wording matches required
semantics exactly. **PASS.**

## 14. Mature-capability audit state (step 27)

```
MATURE S/M CAPABILITY CONSUMPTION PROGRAM:
EXHAUSTED AFTER BOTTOM-UP AUDIT
```

Scope-honesty caveat preserved: `149O.20L.7O.3N.2`'s audit did not
literally field-by-field inspect every typed result across all 416
files; this is a bottom-up discovery result, not a claim of
mathematical completeness.

## 15. Final blocker gate (step 28)

| Item | Classification |
| --- | --- |
| `rg`-tooling-gap, 2 tests (Section 12) | ACCEPTED-DEBT (environment, not product; identical to `3O`'s own disclosed classification) |
| Fast Green push-state attribution self-referential debt | ACCEPTED-DEBT (carried forward from `3O`, out of scope) |
| `tasks/DONE.md` sync debt (doctor task-memory warnings) | ACCEPTED-DEBT (pre-existing, historical, unrelated to release content) |
| F1/F2/Decision-Evaluation explanation gap | DEFERRED (unrelated to this phase's publication-readiness scope) |

**BLOCKING = 0. MUST-FIX = 0.**

## 16. Final repository sanity (step 29)

`git status --short`: clean. `HEAD` == `origin/main` ==
`51111c84be3abcd44c61ccc396e64a12be1eca70`. `git rev-list --count
origin/main..HEAD`: `0`. Candidate drift re-confirmed empty for
release-facing paths (Section 5, re-run identical result at this
gate). **PASS.**

## 17. Human authorization checkpoint (step 30)

No explicit human authorization to publish PCAE `v0.4.3` was present
in the active session. The governing phase-directive prompt itself
explicitly states it is not authorization. Per the governing brief:
**STOP. Do nothing irreversible.** Steps 31-45 (tag creation, tag
push, GitHub Release creation, artifact upload, public verification)
were **not performed**.

## 18. Verdict

```
PCAE v0.4.3:
PUBLICATION READY
RELEASE THEME:
ROLLBACK EVIDENCE VISIBILITY
RELEASE CANDIDATE:
63580893b1de4782a694ab802ff7bdebdf29b0e6
BUILD REPRODUCIBILITY:
VERIFIED
ROLLBACK EVIDENCE VISIBILITY:
VERIFIED
MATURE S/M CONSUMPTION PROGRAM:
EXHAUSTED AFTER BOTTOM-UP AUDIT
BLOCKING:
0
MUST-FIX:
0
RUNTIME:
Observed / observe / unavailable
HUMAN PUBLICATION AUTHORIZATION:
REQUIRED
```

## 19. Tag/candidate distinction (step 47)

```
release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6
tagged_commit = <not created this phase — authorization absent>
later 3N.2 / 3O.1 reporting commits = not tag target
```

## 20. PyPI / Article boundaries (steps 44-45)

`PyPI: NOT PUBLISHED` (no PyPI action performed or authorized).
`Article: STOPPED` (not read, not modified, not resumed this phase).
`~/repos/pcae-deepseek-research` was not inspected, modified, or
imported from.

## 21. Post-verification governance (step 48)

Re-run after all checks (Section 16 covers the git-state half); `pcae
health`/`pcae check`/`pcae status coherence`/`pcae doctor
task-memory`/`pcae push check`/`pcae runtime inspect`/`pcae notify
status` all re-confirmed in the same states reported in Section 3,
after this phase's docs/task-lifecycle-only changes are committed and
pushed (see canonical phase-completion report for the exact post-push
values).

## 22. Recommended next phase

None initiated automatically, per the governing brief. Awaiting
explicit human publication authorization for `149O.20L.7O.3O.1`'s
remaining steps (31-45), or a human decision to hold `v0.4.3`
publication further.
