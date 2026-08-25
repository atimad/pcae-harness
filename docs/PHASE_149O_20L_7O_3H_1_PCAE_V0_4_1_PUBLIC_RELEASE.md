# Phase 149O.20L.7O.3H.1 — PCAE v0.4.1 Public Release

## 1. Scope

Publication-only phase. The only production-behavior change since
public `v0.4.0` — Permission Broker consumption on the default
non-`HATP_MANDATORY` rollback dispatch path — was already
independently verified in `149O.20L.7O.3F`/`3F.1` and frozen into a
reproducible release candidate in `149O.20L.7O.3H`. This phase
performed no source changes, no version changes, and no build
configuration changes. Its only job: independently re-verify the
frozen 3H candidate, then — under explicit human authorization present
in the active session — publish it.

## 2. Release candidate

`release_candidate_commit = 9869cb65d890b70d8649ddd4216ffda4e7d98df5`
(full SHA independently derived via `git rev-parse 9869cb65`, cross-
checked against the 3H canonical report, candidate metadata, and
`docs/RELEASE_NOTES_V0_4_1.md`).

Phase-entry `HEAD` (`7eaaee1a4f2c35a7b04c218d31288eb90cf0f198`) contains
only 3H's own lifecycle/reporting commits since the candidate
(`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-
report.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, task-lifecycle files,
`docs/PHASE_149O_20L_7O_3H_...md`). `git diff 9869cb65..HEAD -- src/pcae
pyproject.toml docs/RELEASE_NOTES_V0_4_1.md` returned empty — zero
release-facing drift. `tagged_commit == release_candidate_commit`
(verified below).

## 3. Version

`pyproject.toml` and `src/pcae/__init__.py` both read `0.4.1`. No
version change made this phase (none permitted).

## 4. v0.4.0 isolation

`v0.4.0` tag object `cfe83c74a8ac8b6966a5e1a9fc5aa8d6e7229f52` peels to
commit `ea3f731ef50ea16985fd4a0562f0c091bb8109b2`, unchanged locally
and on `origin`. `gh release view v0.4.0` confirmed the GitHub Release
unchanged (both assets present, matching size). `v0.3.1`/`v0.3.0`
untouched (not independently re-inspected this phase; no operation in
this phase could have touched them).

## 5. Build reproducibility (independent rebuild — frozen bytes did not
survive between 3H and 3H.1)

3H's own wheel/sdist bytes were not preserved on disk (built in
disposable `/tmp` venvs, destroyed after use, per its own documented
process). Rebuilt via the same fallback path 3H itself used: two
independent fresh `git clone` copies pinned to `release_candidate_commit`,
each with its own disposable venv, `hatchling==1.32.0`, `build==1.5.0`,
Python 3.14.5, `python -m build --outdir dist`.

- wheel: `pcae_harness-0.4.1-py3-none-any.whl`, 2,350,582 bytes,
  SHA-256 `1994dc0453347f319f8cc7447a09aa7d62de8ef3d6e89b5565edbd38ab388309`
- sdist: `pcae_harness-0.4.1.tar.gz`, 2,052,499 bytes,
  SHA-256 `f8712b9b8b7ea1d5520058b19e809430620bb6739a8b9da5b50e93c19c5e16cf`

Build A == Build B byte-for-byte (`cmp`, both artifacts). Both hashes
exactly match the frozen 3H canonical-report record. **Reproducibility:
PASS.**

## 6. Artifact content inspection

Wheel: 468 entries. Sdist: 467 entries. Both match 3H's documented
shape exactly. Grepped both listings for
`\.git|\.claude|\.pcae|\.env|secret|ssh|id_rsa|\.venv|__pycache__|
\.pyc|credential`: only two legitimate production source files
matched on the substring "credential" (`hatp_hardware_credential_admin.py`,
`hatp_hardware_credentials.py`) — not secrets. No contamination found.

## 7. Pre-publication install verification

Installed the freshly rebuilt wheel and sdist into separate fresh
disposable venvs (no local source on path):
- `pcae.__version__ == "0.4.1"` — PASS (both)
- `pcae --help` — PASS (both)
- Golden path (`pcae init` → `session bootstrap --compact` → `task
  new` → `intake from-files` → `intake list`): all commands ran and
  produced genuine, correctly-reasoned decisions (evidentiary
  rejections on malformed/no-lock intake specs, matching the exact
  non-crashing PASS pattern 3H itself documented) — no crash on either
  install.

## 8. Pre-publication rollback Permission Broker smoke (installed
artifact, production-API-only, no test-suite imports)

3H's original installed-artifact smoke script was not preserved (ad
hoc, not committed). Reconstructed equivalent coverage as a standalone
script built only from `pcae.core.paths`, `pcae.core.tasks`,
`pcae.core.agent`, `pcae.core.mutation_permission`, and
`pcae.core.permission_broker_foundation` — the same production APIs
3H's own methodology used (`store_execution_change_package`,
`store_promotion_execution_record`, `create_task_contract`,
`build_rollback_execution`) — never importing anything under `tests/`.
Run against both the wheel- and sdist-installed packages, identically:

| Check | Wheel | Sdist |
|---|---|---|
| dry-run: zero broker calls, zero mutation, `execution_allowed=False` | PASS | PASS |
| real ALLOW: `status=completed`, `reverted=True`, file removed | PASS | PASS |
| runtime byte-identical (`pcae runtime inspect --json`) before/after ALLOW | PASS | PASS |
| missing-active-task DENY (POL-001): zero mutation | PASS | PASS |
| forced DENY: `error=rollback_permission_denied`, zero mutation | PASS | PASS |
| broker failure (raised exception): `permission_decision=BROKER_FAILURE`, zero mutation | PASS | PASS |
| malformed broker result (`None`): `permission_decision=BROKER_FAILURE`, zero mutation | PASS | PASS |
| `HATP_MANDATORY` mode: new default-path adapter never invoked (0 calls) | PASS | PASS |
| human trigger: `pcae rollback` (no `--per-id`) refuses via argparse | PASS | PASS |
| dry-run readiness unaffected by missing active task | PASS | PASS |

**19/19 checks passed identically on both installs.**

## 9. Source-level regression sweeps (byte-identical source to the
verified candidate; run at phase-entry `HEAD`)

- Permission Broker broad sweep: 1109 passed, 5 failed — all 5 by
  name identical to 3H's own documented pre-existing tripwires
  (`test_rae_permission_broker_and_agent_do_not_reference_wave5`,
  `test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`,
  `test_no_permission_broker_request_construction_uses_approval_present_true`,
  `test_permission_broker_consumer_scope_inventory`,
  `test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`).
- Plan B+ / corrupt-store: 43 passed, 0 failed — exact match.
- Intake / Codex-Ox / rollback-persistence: 430 passed, 8 failed,
  1 error — exact match to 3H's documented set.
- 3F + 3F.1 + AG5 + HATP-CLI-migration + 18D focused bucket: 202
  passed, 5 failed — exact match (frozen "diff-since-phase-entry" and
  contract byte-identity tripwires from unrelated historical phases).
- Packaging smoke: 20 passed, 0 failed.
- `fast_green` (`-m fast_green -n auto`): 336 failed, 8731 passed, 5
  skipped, 9 errors — within the same documented flake tolerance 3H
  itself characterized (a timing-sensitive `test_head_equals_
  origin_main` push-state tripwire plus `-n auto` parallel-execution
  flakes); zero source drift since the candidate, so no new
  attributable class is possible.

**Zero attributable regressions.**

## 10. Release notes audit

`docs/RELEASE_NOTES_V0_4_1.md` reconfirmed accurate against the
evidence above. Preserves every required distinction (`Permission
Broker ALLOW != execution capability`; `Permission != human
authority`; `human rollback trigger != Permission Broker decision`;
`rollback readiness != rollback execution`; `HATP_MANDATORY != default
rollback path`). No universal-coverage overclaim — scope explicitly
limited to the currently audited root-mutating command set. Not
modified this phase.

## 11. Final blocker gate

**BLOCKING: 0. MUST-FIX: 0.** ACCEPTED-DEBT (pre-existing, unchanged,
repository-maintainer-only, unrelated to this phase): `tasks/active/`
holds 4 files (expected ≤1) and a long-standing `tasks/DONE.md`
sync-debt backlog — identical in character to what 3H itself disclosed
and left unrepaired as out of scope; not touched here either (no
engineering in a publication-only phase).

## 12. Human publication authorization

Explicit human authorization to publish PCAE v0.4.1 was given in the
active session ("Approved") after this phase's own pre-publication
verification (§1–§11, matching the required
`PCAE v0.4.1: PUBLICATION READY` checkpoint) completed with zero
blocking/must-fix findings. Authorization covered: annotated tag,
remote tag push, GitHub Release creation, upload of the exact verified
wheel/sdist, and post-publication verification. Re-verified the
baseline (clean tree, `HEAD == origin/main`, no local/remote `v0.4.1`
tag) immediately before taking the first irreversible action.

## 13. Publication actions taken

- Created annotated tag `v0.4.1`, target pinned explicitly to
  `release_candidate_commit` (not `HEAD`). Verified
  `git rev-parse v0.4.1^{commit} == 9869cb65d890b70d8649ddd4216ffda4e7d98df5`.
- Pushed the tag (no force). Verified remote peeled ref
  (`refs/tags/v0.4.1^{}`) resolves to the identical candidate SHA —
  `tagged_commit == release_candidate_commit` on both local and
  remote.
- Created the public GitHub Release `v0.4.1` (title "PCAE v0.4.1",
  target = candidate commit, not draft, not prerelease, `--latest`).
  Release-body notes derived from `docs/RELEASE_NOTES_V0_4_1.md` with
  its stale "release-candidate preparation only / no tag has been
  created" preamble line (accurate only pre-publication) stripped for
  the public body; the tracked file itself was left unmodified (no
  source-file engineering this phase).
- Recomputed the frozen wheel/sdist SHA-256 immediately before upload
  (exact match) and uploaded those exact bytes — no rebuild at
  publication time.
- Downloaded the public assets post-upload: filename, byte size, and
  SHA-256 all exactly match the local frozen artifacts.
- Confirmed public release state: correct tag, correct target commit,
  not draft/prerelease, `v0.4.1` now the repository's "Latest" release
  (`v0.4.0` no longer flagged Latest), release notes correct.
- Installed the downloaded public wheel and public sdist into fresh
  disposable venvs with no local source on path: version `0.4.1`,
  import, and CLI all PASS on both.
- Re-ran the full 19-check installed-artifact rollback Permission
  Broker + HATP-isolation + human-trigger + dry-run-readiness smoke
  suite (§8) against the **public** wheel install: 19/19 PASS,
  identical results.
- `pcae runtime inspect` from the public wheel install: `Observed /
  observe / unavailable`, unchanged.
- Public Plan B+ / corrupt-store smoke: not independently re-executed
  against the public wheel specifically (the distribution does not
  ship `tests/`, and reconstructing that suite from production APIs
  alone, on top of the already-large §8 reconstruction, was judged
  disproportionate). Relied instead on: (a) the source-level Plan B+ /
  corrupt-store sweep in §9 (43 passed, 0 failed) run against the
  exact same byte-identical source that produced the published
  artifact, and (b) the public wheel's independently confirmed
  byte-identical hash match to that same source build. This is
  disclosed here rather than asserted as directly-executed evidence.

## 14. v0.4.0 untouched (post-publication)

Re-confirmed via `gh release view v0.4.0`: tag target, both asset
names, and both asset sizes unchanged after `v0.4.1` publication.

## 15. PyPI

**NOT PUBLISHED.** Not authorized this phase; no PyPI action taken.

## 16. Article / private-research-repo boundary

The article remains **STOPPED** — not read, not modified, not
published, not automatically resumed. `~/repos/pcae-deepseek-research`
was not inspected, modified, or imported from this phase.

## 17. Post-publication governance

`pcae health` — healthy. `pcae check` — passed. `pcae status
coherence` — coherent. `pcae push check` — clean, nothing to push
(publication touched GitHub tag/release state only, not the harness
repository's own tracked files, until this phase's own lifecycle
commit). `pcae runtime inspect` — `Observed / observe / unavailable`,
unchanged. Telegram sink configured/enabled.

## 18. Deferred work

Per phase-prompt boundary: no work begun this phase on runtime
preflight disclosure, rollback readiness/evidence auto-generation,
Repository Intelligence internal consumption, Advisory context
consumption, or Runtime Enforcement consumption. These remain the
candidate items for the next strategic-direction decision, deliberately
not selected here.

## 19. Final verdict

```
PCAE v0.4.1:
PUBLICLY RELEASED
RELEASE THEME:
PERMISSION BROKER ROLLBACK COVERAGE COMPLETION
RELEASE-CANDIDATE COMMIT:
VERIFIED (9869cb65d890b70d8649ddd4216ffda4e7d98df5)
TAG:
v0.4.1
VERIFIED
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
PRESERVED (source-level; public-wheel-specific re-execution disclosed as not directly run, see §13)
BUILD REPRODUCIBILITY:
VERIFIED
WHEEL:
PUBLISHED AND CHECKSUM-VERIFIED
SDIST:
PUBLISHED AND CHECKSUM-VERIFIED
POST-PUBLICATION INSTALL:
PASS
RUNTIME:
Observed / observe / unavailable
PYPI:
NOT PUBLISHED
ARTICLE:
STOPPED
RELEASE STATUS:
COMPLETE
```

## 20. Recommended next strategic action

Do not automatically resume article work. Return to the deferred
capability-consumption roadmap and reconsider, without committing to
any of them in this phase: (1) runtime preflight disclosure; (2)
rollback readiness/evidence auto-generation; (3) Repository
Intelligence + Advisory integration. No selection made here.
