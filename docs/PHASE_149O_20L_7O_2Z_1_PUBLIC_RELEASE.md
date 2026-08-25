# Phase 149O.20L.7O.2Z.1 — PCAE v0.3.1 Public Release

**Status:** COMPLETE
**Type:** Publication (no engineering, no source changes)
**Human publication authorization:** confirmed explicitly by the repository
owner in-session before any irreversible action was taken.

## 1. Purpose

Publish the exact, independently pre-publication-verified PCAE v0.3.1
release candidate established by Phase 149O.20L.7O.2Z. No feature work,
no opportunistic repairs, no architecture changes, no documentation
redesign.

## 2. Release-Candidate Commit Binding

```
release_candidate_commit = 5d7edef9c34ee266a9c5b51940ee4f1848375d22
```

Phase 2Z's own `.pcae/phase-completion-metadata.json` names this commit
as the exact source the wheel/sdist evidence was built from. The four
commits after it on `main` (`4d21747a`, `8999d714`, `9151bcd0`,
`36d12608`) were independently re-verified this phase (and again
immediately before tagging) to touch only
docs/CHANGELOG/PROJECT_STATUS/`.pcae/*` bookkeeping — `git diff
5d7edef9..HEAD -- src/pcae pyproject.toml` is empty at every check
point. `v0.3.1` is tagged at `5d7edef9`, not at `HEAD`, by design — the
tag binds to the verified product commit, not to later phase-report
finalization commits (this phase's own included).

## 3. Pre-Publication Verification (this phase, before authorization)

Performed in PRE-PUBLICATION VERIFICATION MODE ONLY, before human
authorization was given:

- `HEAD == origin/main`, `origin/main..HEAD = 0`, clean tree, zero
  `src/pcae/**`/`pyproject.toml` diff between `5d7edef9` and HEAD.
- Original Phase 2Z wheel/sdist no longer existed (built into a
  disposable directory, confirmed via 2Z's own metadata). Rebuilt from
  `5d7edef9` in an isolated `git worktree` + fresh venv (Python 3.14.5,
  `build` 1.5.0, hatchling backend).
- **Wheel** rebuild: byte-identical to 2Z's original recorded artifact
  — SHA-256 `a459617fdaf2d6424123852c84c8c7abf6e238224827196a37d1e346cf74dad6`,
  2,338,452 bytes.
- **Sdist** rebuild: differs from 2Z's original recorded checksum
  (`a4e644b5.../2,066,901 bytes`, artifact no longer recoverable to
  compare directly) but is **internally reproducible** — a second
  independent build (Build B) from the same commit/environment/command
  produced byte-identical output to Build A: SHA-256
  `9d61147efa1f1fc2f96dc52366d884bbfa50f9d87d1af6e5d88f0ec4f8514084`,
  2,053,935 bytes. Human explicitly authorized treating this rebuild as
  the authoritative artifact set (Path B) rather than chasing the
  original bytes.
- Content/security scan of both archives: zero matches for
  `deepseek-research|article|secret|.env$|telegram|openrouter|id_rsa|/Users/|\.git/`.
- Fresh disposable-venv installs of both wheel and sdist: version
  `0.3.1`, CLI/import OK, full golden path (`pcae init` → `session
  bootstrap` → `task new` → `intake from-files` → `intake show/list`)
  passing identically on both.
- Codex-Ox smoke (wheel + sdist, separate fresh repos): bootstrap
  succeeds, intake provenance literal `codex-ox`, `execution_allowed:
  False`/`promotion_executed: False`, no subprocess/network call.
- No-lock smoke (wheel + sdist): explicit `--producer` accepted without
  bootstrap; no producer + no lock cleanly rejected
  (`no_active_agent_lock_and_no_explicit_producer_supplied`), never
  silently substituted.
- Malformed-lock regression matrix (9 cases: valid, malformed JSON,
  truncated JSON, JSON root = list/string/number/null, missing
  `agent_id`, absent file) against both `session bootstrap` and `intake
  from-files` on the frozen wheel: zero uncontrolled tracebacks in any
  case; malformed/wrong-type JSON produces clean
  `malformed_agent_lock:<reason>` rejections; no case elevated
  authority.
- Producer authority non-flow: `claude-local`, `codex-ox`, and an
  arbitrary custom producer all yield `execution_allowed=False`;
  out-of-scope file submission cleanly rejected
  (`out_of_scope_path:...`); no way to pass authority-bearing fields as
  input.
- Empty-agent-ID debt reconfirmed accepted, non-authorizing, unchanged.
- Release regression: `test_phase_149o_20l_7o_2z_release_candidate.py`
  + `test_phase_149o_20l_7o_2y_release_hardening.py` — 31 passed;
  2X/2X.1/2W/2W.1 — 109 passed; 2U.2-4 (reference adapter + allow/deny
  demo) — 150 passed; `test_agent.py` + `test_session.py` — **4381
  passed, 0 failed** (750.62s), matching 2Z's baseline exactly.
- Resource-sensitive tests re-isolated under low load: both
  `test_show_after_create` node IDs pass; the "concurrent-load
  artifact" (`TestBackendReviewReject::test_reject_updates_latest`)
  passes cleanly alone; the "expected until-push guard"
  (`test_head_equals_origin_main`) now **passes**, confirming it
  resolved once `HEAD == origin/main`; `TestAuditPersistence::
  test_audit_verify_cli` still times out (15.11s vs. 15s, 200,987+
  accumulated audit records) — reconfirmed unrelated to this phase's
  diff (`20bbda98` touches no shell-gate/audit files) —
  **ACCEPTED-DEBT**.
- Task-memory debt: exactly 129 warnings, unchanged, repository-
  maintainer-only — **ACCEPTED-DEBT**.
- Governance checks: `pcae health` healthy, `pcae check` passed, `pcae
  status coherence` coherent, `pcae push check` nothing to push, `pcae
  runtime inspect` → Observed/observe/unavailable.
- Documentation truth: `docs/RELEASE_NOTES_V0_3_1.md` explicitly
  disclaims Codex-Ox execution / OpenRouter transport. Quickstart's
  golden path is the packaged `pcae intake from-files`, verified
  working from both frozen installs.
- Stable-release isolation: `v0.3.0` → `738a81553128665a9c206f3ce33c931dc9089a6c`,
  unchanged; no local/remote `v0.3.1` tag; no `v0.3.1` GitHub Release
  existed yet; PyPI/article untouched.

**Result at that point: BLOCKING = 0, MUST-FIX = 0. Reported
PUBLICATION READY — FINAL HUMAN AUTHORIZATION REQUIRED and stopped.**

## 4. Human Publication Authorization

The repository owner explicitly authorized, in-session, publication of
v0.3.1 from the frozen release-candidate source commit `5d7edef9`,
scoped precisely to: annotated-tag creation and push, GitHub Release
creation, attachment of the frozen wheel/sdist, checksum verification,
tag-target verification, Latest/stable verification, and
post-publication install/workflow smoke. PyPI, v0.3.0 modification,
artifact substitution, source-code changes, force-push, history
rewrite, `--no-verify`, article work, and Codex/Ox execution
integration were explicitly excluded. The accepted non-blocking debt
(empty `agent_id`, task-memory warnings, shell-gate audit-verify
timeout) was explicitly reaffirmed as accepted for this release.

## 5. Final Pre-Tag Invariant Recheck

Immediately before the first irreversible action, every invariant was
re-verified against the frozen pre-publication evidence: `HEAD ==
origin/main == 36d12608...`, `origin/main..HEAD = 0`, clean tree, zero
`src/pcae/**`/`pyproject.toml` diff `5d7edef9..HEAD`, version `0.3.1`
in both sources, no existing `v0.3.1` tag/release, `v0.3.0` unchanged.
No discrepancy found.

The original build worktree/artifacts from the pre-authorization pass
had already been deleted (worktree cleanup); the wheel/sdist were
rebuilt a **third** independent time from `5d7edef9` in a fresh
worktree/venv immediately before use, producing byte-identical output
to both prior builds (same two SHA-256 values as above) — the process
is proven deterministic across three independent runs.

## 6. Publication

Followed the only established release mechanism for this repository
(no `pcae`-governed tag/release automation exists — confirmed in
`docs/PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md`
§30, and matches the exact `git tag -a` + `git push origin <tag>` +
`gh release create` pattern used for v0.1.0-rc1/v0.2.0/v0.3.0):

1. `git tag -a v0.3.1 5d7edef9 -m "PCAE v0.3.1"` — annotated tag,
   pointing exactly at the release-candidate commit (not HEAD).
   Verified locally: `git rev-parse v0.3.1^{commit}` ==
   `5d7edef9c34ee266a9c5b51940ee4f1848375d22`.
2. `git push origin v0.3.1` — no force, no overwrite (tag did not
   previously exist locally or remotely). Verified via `git ls-remote
   --tags origin 'refs/tags/v0.3.1^{}'` (peeled/dereferenced ref) ==
   `5d7edef9c34ee266a9c5b51940ee4f1848375d22`. Local tag commit == remote
   tag commit == release-candidate commit.
3. `gh release create v0.3.1 <wheel> <sdist> --title "PCAE v0.3.1"
   --notes-file docs/RELEASE_NOTES_V0_3_1.md --latest` — created at
   https://github.com/atimad/pcae-harness/releases/tag/v0.3.1.
4. Verified via `gh release view v0.3.1 --json ...`: `isDraft: false`,
   `isPrerelease: false`, `targetCommitish: main`, both assets'
   server-reported `digest` fields match the frozen checksums exactly.
5. Downloaded both assets fresh via `gh release download` and
   recomputed SHA-256 locally — identical to the frozen values and to
   the server-reported digests.
6. `gh release list` confirms v0.3.1 is now the `Latest` release;
   v0.3.0 is still present, unmodified, no longer marked Latest (normal
   GitHub semantics — exactly one release can hold that label).

## 7. Post-Publication Verification

- Fresh disposable venv, wheel installed **only from the downloaded
  public GitHub Release asset** (not the local build): version
  `0.3.1`, import/CLI OK, `pcae init` → `session bootstrap` →
  `intake from-files` (ACCEPTED, `execution_allowed: False`) →
  `intake list` (producer `claude-local`/`agent_lock`) — PASS.
- Codex-Ox bootstrap from the same public wheel install, separate
  fresh repo: succeeds, provenance literal `codex-ox` — PASS.
- Fresh disposable venv, sdist installed only from the downloaded
  public asset: version `0.3.1`, same golden path, same no-lock
  behavior (explicit-producer accepted; no-producer/no-lock cleanly
  rejected) — PASS, identical to wheel.
- No external AI/model-service or Codex/OpenRouter call at any point
  in this phase.

## 8. Final Governance State

```
pcae health              → healthy
pcae check                → passed
pcae status coherence     → coherent, nothing_to_push
pcae push check           → nothing to push
pcae runtime inspect      → Runtime state: Observed
                             Execution capability: unavailable
                             Maximum plugin capability: observe
                             Governance posture: non-executing
v0.3.0 tag                → 738a81553128665a9c206f3ce33c931dc9089a6c (unchanged)
v0.3.1 tag                → 5d7edef9c34ee266a9c5b51940ee4f1848375d22 (verified)
```

## 9. Accepted Non-Blocking Debt (unchanged, reconfirmed, not repaired)

- Empty `agent_id` descriptive-provenance weakness — non-authorizing.
- `tasks/DONE.md` historical sync warnings — 129, repository-
  maintainer-only.
- `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` —
  resource-sensitive subprocess timeout against a very large
  accumulated local audit corpus (200,987+ records), unrelated to this
  or the 2Z product diff.

## 10. Explicit Out-of-Scope Confirmation

Not performed, per the authorization boundary: PyPI publication;
modification or movement of the v0.3.0 tag/release; artifact
substitution after publication began; source-code changes; force push;
history rewrite; `--no-verify`; article modification or publication;
Codex/Ox/OpenRouter execution integration; runtime capability changes;
HATP/FIDO2/WebAuthn or Dell deployment work.

## 11. Final Verdict

```
PCAE v0.3.1:
PUBLICLY RELEASED
TAG:
VERIFIED (local == remote == release-candidate commit 5d7edef9)
RELEASE-CANDIDATE COMMIT BINDING:
VERIFIED
WHEEL:
PUBLISHED AND CHECKSUM-VERIFIED (a459617f...4dad6, 2,338,452 bytes)
SDIST:
PUBLISHED AND CHECKSUM-VERIFIED (9d61147e...14084, 2,053,935 bytes)
POST-PUBLICATION INSTALL:
PASS (wheel and sdist, from public GitHub Release assets)
GITHUB RELEASE:
PUBLISHED — https://github.com/atimad/pcae-harness/releases/tag/v0.3.1
LATEST/STABLE:
VERIFIED
PYPI:
NOT PUBLISHED
ARTICLE:
UNPUBLISHED
RUNTIME:
Observed / observe / unavailable
RELEASE STATUS:
COMPLETE
```

## 12. Recommended Next Action

Do not immediately begin another engineering phase. Recommended:
**Post-v0.3.1 Article Reassessment and Rewrite** — a discussion phase,
not automatically a PCAE code phase, to reassess the unpublished
article draft against the exact v0.3.1 released capability set before
any decision to rewrite or publish it.
