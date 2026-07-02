# PCAE v0.1.0-rc1 — Release Handoff

## Tag Name

`v0.1.0-rc1`

## Commit Hash Tagged

- **Tagged commit:** `d155dddcf56e7ec17ed558f234d6148799192290`
  ("Record 106F pre-tag finalization progress" — the clean, fully-pushed
  tag-ready state confirmed by Phase 106F's pre-tag gate results; see
  `docs/PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md`).
- **Tag object hash (annotated tag):** `b47ce1817a697eab6bee8ef158ba50d96e57c3bb`

Verify at any time with:

```bash
git rev-parse v0.1.0-rc1^{commit}   # d155dddcf56e7ec17ed558f234d6148799192290
git rev-parse v0.1.0-rc1            # b47ce1817a697eab6bee8ef158ba50d96e57c3bb (tag object)
```

## Release Status

**Release candidate**, tagged and pushed to origin. Not a final release.
No `v0.1.0` tag exists.

## Release Scope

PCAE v0.1 is a governed, **non-executing** AI coding lifecycle harness —
see `docs/RELEASE_SCOPE_V0_1.md` (106A, frozen) for the full scope
definition: included/excluded capabilities, supported use cases, and
forbidden safety claims.

## Install/Build/Smoke Status

- Editable install, non-editable install, and `python -m build`
  (sdist + wheel): all succeeded (106D;
  `docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`).
- Release artifacts rebuilt from the tag-ready state in this phase
  (106F): sdist (`pcae_harness-0.1.0.tar.gz`) and wheel
  (`pcae_harness-0.1.0-py3-none-any.whl`) both built successfully in a
  throwaway virtual environment and smoke-installed cleanly; see
  `docs/PHASE_106_V0_1_RC_TAG_ARTIFACT_FINALIZATION.md` for exact
  artifact names/sizes.
- Fresh-clone golden workflow smoke test: succeeded (106D).

## Validation Baseline

| Check | Result |
|---|---|
| Fast-green (`-m fast_green -n auto`) | **4390/4390 — fully green** |
| Combined regression | 2220/2220 passed |
| Release/lifecycle regression | 421/421 passed |
| Focused release-candidate/packaging/golden-workflow tests | 109/109 passed |
| `report_notification_tests` | 219/219 passed |
| `bootstrap_session_reporting_tests` | present_in_canonical_metadata |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean |

## Post-RC Verification (106G–106I)

After tagging, `v0.1.0-rc1` went through a post-RC inspection/repair/
verification cycle before documentation alignment:

- **106G** — post-RC lifecycle connectivity audit. Found a real trust-gate
  asymmetry: `pcae task finish --commit`'s Telegram-dispatch gate omitted
  a completeness check `pcae phase complete`'s gate had required since
  105D. See `docs/PHASE_106_POST_RC_SYSTEM_INSPECTION_LIFECYCLE_CONNECTIVITY_AUDIT.md`.
- **106H** — repaired the asymmetry via a shared helper
  (`apply_old_schema_gate()`); both commands now enforce the same
  combined trust gate. See `docs/PHASE_106_RC_AUDIT_FINDINGS_REPAIR.md`.
- **106I** — re-verified the repair through the live installed `pcae`
  binary (not just unit tests) in an isolated scratch repository: both
  commands agree exactly on dispatch/hard-fail decisions and blocker
  text for the same report. See
  `docs/PHASE_106_RC_END_TO_END_VERIFICATION_FULL_PHASE_CHECK.md`.

Current baseline after this cycle (106I): fast-green **4390/4390 fully
green**, combined regression **2240/2240**, `report_notification_tests`
**219/219**, `bootstrap_session_reporting_tests`
**present_in_canonical_metadata**, `pcae health`/`check`/`doctor
task-memory`/`push check` all green. No new tag was created during this
cycle — `v0.1.0-rc1` is unchanged from the tag recorded above.

## Golden Workflow Pointer

`docs/V0_1_GOLDEN_WORKFLOW.md` — the command-verified operator workflow
for using PCAE v0.1, from start-of-phase through post-completion
verification.

## Release Notes Pointer

`docs/RELEASE_NOTES_V0_1_DRAFT.md` — positioning, highlights,
installation summary, safety boundary, known limitations, what is not
included, and the v0.2 autonomy preview. Promote this draft's content
when publishing a GitHub Release for this tag (not performed in this
phase).

## Known Limitations

- Two independent report-trust schemas exist internally (legacy 95M.1,
  105A/105B); the schemas themselves remain distinct, though their
  *combination logic* is now shared between `task finish --commit` and
  `phase complete` (106H) — not a full unification, but no longer a
  source of divergence between the two commands.
- `pcae push check`'s report-trust gate checks content completeness
  only, not push-state fields, by deliberate design.
- Package version is static in `pyproject.toml` (`0.1.0`), not derived
  from git tags — the `-rc1` qualifier lives in the tag name only.
- Release artifacts (sdist/wheel) are built and verified but not
  published to any index or attached to a GitHub Release in this phase.
- `docs/ROADMAP.md` (an internal planning artifact, not a release-facing
  document) remains stale relative to actual repo state — `README.md`
  was brought current in Phase 106J.

## Non-Execution Boundary

PCAE v0.1.0-rc1 is non-executing by design: no runtime enforcement, no
autonomous execution, no real AI backend invocation, no adapter
execution, no shell mediation, no rollback execution. Telegram is
outbound-only — there is no inbound handler or command-reception path
anywhere in `core/notifications.py`. All authorization flags are `False`;
all safety flags (`simulation_only`, `no_execution`, `evidence_only`,
`non_authorizing`, `design_only`) are `True`.

## v0.2 Autonomy Boundary

v0.2 is the target release for governed autonomy — runtime enforcement,
governed real backend invocation, adapter execution under human-approval
gates, durable audit persistence, and rollback execution governance. None
of this exists in `v0.1.0-rc1`; it is the non-executing governance
foundation v0.2 will be built on top of. See
`docs/RELEASE_SCOPE_V0_1.md`'s "v0.2 Full-Autonomy Roadmap Boundary".

## How to Verify the Tag Locally

```bash
git tag --list | grep v0.1.0-rc1
git rev-parse v0.1.0-rc1
git show --stat --oneline v0.1.0-rc1
```

## How to Verify the Tag From Origin

```bash
git ls-remote --tags origin v0.1.0-rc1
git fetch origin --tags
git rev-parse v0.1.0-rc1
```

## What to Do Next

1. Review this handoff document and `docs/RELEASE_NOTES_V0_1_DRAFT.md`.
2. Optionally publish a GitHub Release for `v0.1.0-rc1` (not performed in
   this phase — requires explicit operator request per this phase's
   operating rules).
3. Optionally publish the built sdist/wheel to a package index.
4. Use `v0.1.0-rc1` for external validation before considering a final
   `v0.1.0` tag — no final `v0.1.0` tag exists or was created by this
   phase.
5. When ready to plan v0.2, proceed to **107A — v0.2 Full Autonomy
   Roadmap / Execution Capability Gap Analysis** (recommended next phase;
   not started in this phase).
