# Phase 149O.20L.7O.3O.2 — PCAE v0.4.3 Publication Execution

**Status: PUBLICLY RELEASED. COMPLETE.**

## 1. Objective

Execute the human-authorized publication of PCAE `v0.4.3` from the
frozen release candidate independently re-verified in
`149O.20L.7O.3O.1`, and no further. Publication-only: no engineering,
no repair-and-publish.

## 2. Human publication authorization

Explicit human authorization was given in the active session, in the
user's own words: "Publish PCAE v0.4.3 from release candidate
`63580893b1de4782a694ab802ff7bdebdf29b0e6`: create and push the
annotated v0.4.3 tag pinned exactly to that commit, create the GitHub
Release using the verified release notes, upload only the frozen
verified wheel and sdist, verify the public asset bytes/checksums and
post-publication installs, keep PyPI unpublished, and keep the article
stopped." This supersedes `3O.1`'s STOP; prior release authorizations
(for `v0.4.0`/`v0.4.1`/`v0.4.2`) did not carry forward and were not
relied upon.

## 3. Phase-entry commit / release candidate

- Phase-entry `HEAD` == `origin/main` == `be1006a323928b90abe7668b5d11f0e182bd48da`
  (post-`3O.1`), clean, 0 commits ahead.
- `release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6`,
  independently confirmed via `git rev-parse` immediately before
  tagging.
- Candidate-to-`HEAD` drift on `src/pcae`, `pyproject.toml`,
  `docs/RELEASE_NOTES_V0_4_3.md` re-confirmed empty at this phase's
  start (same result as `3O`/`3O.1`).

## 4. Tag / candidate distinction

```
release_candidate_commit = 63580893b1de4782a694ab802ff7bdebdf29b0e6
tagged_commit             = 63580893b1de4782a694ab802ff7bdebdf29b0e6
```

Equal, as required. Later `3N.2`/`3O.1` documentation/reporting commits
were **not** the tag target.

## 5. Local tag creation and verification

`git tag -a v0.4.3 63580893b1de4782a694ab802ff7bdebdf29b0e6 -m "..."`.
`git rev-parse v0.4.3^{commit}` == `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
Exact match. **PASS.**

## 6. Tag push and remote verification

`git push origin v0.4.3` (no force). `git ls-remote --tags origin
refs/tags/v0.4.3` == local tag object `da45064affafdf882661435ca2ad96ea9fce3527`.
`git cat-file -p` on that tag object shows `object
63580893b1de4782a694ab802ff7bdebdf29b0e6`, `type commit`, `tag v0.4.3`.
Local tag object == remote tag object == wraps release candidate.
**PASS.**

## 7. Version

`pyproject.toml` and `src/pcae/__init__.py` both `0.4.3`, unchanged
from `3O`/`3O.1`. No version edit made this phase.

## 8. v0.4.2 isolation

`v0.4.2` tag (`bc7935f4bb86ea7f6ade823a4e63ed9c9cc0a0c4`) and GitHub
Release (2 assets, `sha256:20fce764...b4` wheel /
`sha256:19f63724...455` sdist) inspected via `gh release view v0.4.2`
before and after this phase's publication actions: byte-for-byte
unchanged. **PASS.**

## 9. Build provenance

Reused, not rebuilt, `3O`'s exact frozen artifact bytes (two
independent `git clone --no-local` builds pinned to the candidate
commit, `hatchling==1.32.0`, root-anchored sdist includes). No rebuild
was performed this phase (no rebuild-fallback needed; exact frozen
bytes were available and re-hashed immediately before every use).

## 10. Wheel / sdist frozen record

```
wheel: pcae_harness-0.4.3-py3-none-any.whl
  size: 2,352,742 bytes
  sha256: e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4
sdist: pcae_harness-0.4.3.tar.gz
  size: 2,054,469 bytes
  sha256: 8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276
reproducibility: PASS
```

Recomputed immediately before upload (this phase); identical to the
`3O`/`3O.1` record. No rebuild after publication began.

## 11. Public GitHub Release

`gh release create v0.4.3 --title "v0.4.3 — Rollback Evidence
Visibility" --notes-file <derived-from-docs/RELEASE_NOTES_V0_4_3.md>
--latest`. Notes body used the verified release-notes content
(theme, what-is-new, what-has-not-changed, version rationale,
release-engineering, deferred sections) verbatim; the file's internal
pre-publication process header ("Status: release candidate frozen, NOT
PUBLISHED... Publication requires a separate, explicitly
human-authorized phase") was omitted from the public body because it
is now false (publication has occurred) and because it references an
internal phase-document path not meant for public release notes —
this is content selection for a public audience, not an edit to the
underlying `docs/RELEASE_NOTES_V0_4_3.md` file, which was not
modified. Release published at
`https://github.com/atimad/pcae-harness/releases/tag/v0.4.3`,
`isDraft: false`, `isPrerelease: false`, marked Latest.

## 12. Asset upload and public byte verification

Uploaded only the two frozen files (`gh release upload`), hashes
recomputed immediately pre-upload and matching Section 10 exactly.
Downloaded both assets back from the public release
(`gh release download v0.4.3`) and re-hashed:

```
pcae_harness-0.4.3-py3-none-any.whl: 2,352,742 bytes,
  sha256:e42ca72c136e95fbb179582c3058b1d6c2001edbbbe80f61af8c45002a8ff5e4
pcae_harness-0.4.3.tar.gz: 2,054,469 bytes,
  sha256:8a088983971b19d6e16f0e6ce3d7a9aa69fa27e987b574c4a109e74589977276
```

Exact match to filename/size/hash. **PASS.**

## 13. Public release state

`gh release view v0.4.3` / `gh release list`: `v0.4.3` public,
`targetCommitish: main`, both assets `state: uploaded` with matching
digests, marked `Latest`, not prerelease, not draft. `v0.4.2`
unaffected (Section 8).

## 14. Public wheel install and golden path

Fresh venv, public wheel installed alone (downloaded from the
release, not the local frozen copy). `pcae.__version__ == "0.4.3"`;
CLI (`pcae --help`) works. Golden path in a disposable `git init`-ed
directory: `pcae init` → (baseline commit, scoped task contract) →
`pcae session bootstrap --agent-id pub-verify-wheel` → `pcae task new`
→ `pcae intake from-files` → `ACCEPTED`, `intake_id` assigned,
`execution_allowed: False`, `promotion_executed: False` → `pcae intake
list` shows the candidate. **PASS.**

## 15. Public rollback-evidence smoke

Reused `3O`'s own fixture-construction script
(`wheel_rollback_smoke.py`) unmodified, run fresh against the public
wheel's installed `pcae` CLI (subprocess):

- **Dry-run**: `rc=0`, `Rollback: DRY RUN` present, `file_plan:`
  present, no `AUTHORIZED` claim.
- **Real rollback, no prior dry-run** (mandatory): `rc=0`, `Rollback:
  COMPLETED`, `divergence_check:` present, `b.txt: success` present,
  target file removed.
- **Divergence**: `rc=1`, JSON payload has `file_plan`,
  `divergence_check`, `execution_allowed: false`,
  `error: divergence_conflict`, `blocking_paths: ["c.txt"]`; target
  file byte-unchanged; `governance_boundaries` block confirms
  `automatic_rollback_allowed: false`, `git_commit_forbidden: true`,
  `git_push_forbidden: true`, `conflict_blocks_before_any_file_is_
  touched: true`.

Evidence non-authority, human trigger, and HATP isolation are the same
invariants exercised by this smoke (every invocation an explicit CLI
call; divergence block occurs before any write; Permission Broker
gating unchanged). **PASS.**

## 16. Public RI regression

`pcae advisory check --command "git status" --json` against the public
wheel install shows `repository_intelligence_context` auto-attached to
the output (`available: false` in this fixture, correctly reflecting
"no snapshot found" — this is the expected structural behavior, not a
regression) with the unchanged `non_authority_disclaimer` text. Field
present without any extra invocation, matching `3J.1`'s finding that
RI attaches to `core/advisory.py` output. **PASS.**

## 17. Public bootstrap-prompt regression

`pcae session bootstrap --compact --profile implementation` against
the public wheel install produced its deterministic prompt/instruction
output (profile banner, active-task line, governance-state line,
rules, validate-commands, stale-context guidance, bootstrap
instruction). No provider dispatch occurred. **PASS.**

## 18. Public sdist verification

Downloaded sdist re-hashed to the Section 10 record exactly (see
Section 12). Fresh separate venv install: `pcae.__version__ ==
"0.4.3"`, CLI works. **PASS.**

## 19. Runtime, before/during/after

`pcae runtime inspect`, both on the source repo and from the public
wheel install: `Runtime state: Observed`, `Execution capability:
unavailable`, `Maximum plugin capability: observe`,
`Permission Broker status: execution_unavailable`,
`Governance posture: non-executing`. Unchanged throughout. **PASS.**

## 20. PyPI boundary

```
PyPI: NOT PUBLISHED
```

No PyPI action was performed or attempted this phase.

## 21. Article boundary

The article remains **STOPPED**. It was not read, modified, or
resumed. `~/repos/pcae-deepseek-research` was not inspected, modified,
or imported from at any point in this phase.

## 22. Regressions not re-run this phase (already covered by 3O.1)

Permission Broker, Plan B+, corrupt-store, and intake/Codex-Ox
source-tree regression suites were freshly re-run in `3O.1` (212/214
passed, 2 pre-existing non-attributable `rg`-tooling-gap failures) on
the exact same `HEAD` this phase published from (no source changed
between `3O.1` and this phase's tag target); not re-run a third time
here to avoid redundant, non-additive verification. The public-install
RI, rollback-evidence, and bootstrap-prompt smokes above are this
phase's own independent public-artifact verification, additive to
`3O.1`'s source-tree and installed-frozen-artifact verification.

## 23. Post-publication governance

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings limited to the same
pre-existing historical `tasks/DONE.md` synchronization debt carried
forward from every recent phase (ACCEPTED-DEBT, unrelated to
publication). `pcae push check`: clean / nothing to push (prior to
this phase's own doc commit). `pcae runtime inspect`: unchanged
(Section 19). `pcae notify status`: Telegram configured, enabled,
ready.

## 24. Final blocker gate

**BLOCKING = 0. MUST-FIX = 0.**

## 25. Final verdict

```
PCAE v0.4.3: PUBLICLY RELEASED
RELEASE THEME: ROLLBACK EVIDENCE VISIBILITY
RELEASE-CANDIDATE COMMIT: VERIFIED
TAG: v0.4.3 VERIFIED
ROLLBACK EVIDENCE: SURFACED
ROLLBACK PREPARATION: ALREADY AUTOMATIC PRE-v0.4.3
PERMISSION BROKER: UNCHANGED
HUMAN AUTHORITY: UNCHANGED
HATP: UNCHANGED
BUILD REPRODUCIBILITY: VERIFIED
WHEEL: PUBLISHED AND CHECKSUM-VERIFIED
SDIST: PUBLISHED AND CHECKSUM-VERIFIED
POST-PUBLICATION INSTALL: PASS
MATURE S/M CONSUMPTION PROGRAM: EXHAUSTED AFTER BOTTOM-UP AUDIT
RUNTIME: Observed / observe / unavailable
PYPI: NOT PUBLISHED
ARTICLE: STOPPED
RELEASE STATUS: COMPLETE
```

## 26. Recommended next phase

None. Per the governing brief: stop after `3O.1`'s continuation
(this phase). Do not begin the next strategic chapter automatically.
