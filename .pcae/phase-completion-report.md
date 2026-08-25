# Phase 149O.20L.7O.3C.4 Complete — Connected Capability Release Scope, Version, and Reproducible-Build Hardening

**Verdict: PCAE v0.4.0 RELEASE CANDIDATE PREPARED (NOT PUBLISHED).**
Froze the independently-verified connected-capability scope, derived
v0.4.0 from the real post-`v0.3.1` delta (unconditional automatic
cross-capability orchestration at `pcae phase complete`, not a
patch-level fix), found and fixed a genuine sdist-packaging
contamination defect (unanchored `include` globs sweeping in a local
`.claude/worktrees/<agent-id>/` directory), pinned the build backend to
`hatchling==1.32.0`, and verified byte-identical wheel/sdist artifacts
across two independent clean-clone builds. Both artifacts install
cleanly and the installed CLI's golden path and governance gates behave
correctly. Zero attributable Fast Green regressions. Runtime unchanged
(`Observed`/`observe`/`unavailable`). No tag, GitHub Release, or PyPI
publication was created.

## Summary

**Version:** `v0.4.0`, selected because `pcae phase complete` now
performs unconditional automatic cross-capability orchestration
(auto-detect a `Confirmed` Interactive Workflow session → CHGR
consumption → Permission Broker gate → Publication Execution Ownership)
that did not exist at `v0.3.1` — a new, backward-compatible product
capability, not a patch-level fix.

**Reproducible-build fix:** a real `python -m build` run from the
working tree produced an sdist containing a nested
`.claude/worktrees/agent-a792203d34f32ceda/` checkout (its own
`src/pcae`, `README.md`, `LICENSE`, `pyproject.toml`), because
`[tool.hatch.build.targets.sdist].include` patterns were unanchored and
matched those same path segments at any depth. Fixed by root-anchoring
the patterns (leading `/`); re-verified with a second build showing zero
contamination. `[build-system].requires` now pins `hatchling==1.32.0`.

**Reproducibility verification:** two independent clean-clone builds
(`/tmp/pcae_clean_a`, `/tmp/pcae_clean_b`), each in its own disposable
venv created and destroyed independently, pinned to the frozen candidate
commit:

```text
wheel:  pcae_harness-0.4.0-py3-none-any.whl
        sha256: 8125d21dc5093892d7303ccbd416cfed91429798ad2d3f17e1512d24b2c3ea00
sdist:  pcae_harness-0.4.0.tar.gz
        sha256: 13492127f261e0460ba943598dca010881c672e2c2602348697050f763960f61
```

Both hashes matched byte-for-byte across build A and build B.

**Installed verification:** both the wheel and sdist install cleanly
into disposable venvs (`pcae --version`/`import pcae` → `0.4.0`, `pcae
--help` works, non-editable site-packages install confirmed). The
installed wheel's CLI golden path (`pcae init` → `session bootstrap` →
`task new` → `intake from-files`) runs correctly, including a
correctly-fail-closed rejection of an out-of-scope file path. `pcae
phase complete` from the installed wheel correctly rejects an
intentionally-incomplete report with a clean, structured governance-gate
rejection (no crash). `pcae runtime inspect` from the installed wheel
confirms `Observed`/`observe`/`unavailable`, unchanged.

**Regression:** a focused suite (Plan B+/3C.2–3C.3.2/Permission
Broker/CHGR/phase-report/packaging, 1563 tests) found 2 pre-existing,
environment-dependent failures (`test_143e_wheel_contains_all_six_chgr_record_schemas`,
`test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv`)
— both invoke `python -m build` against the ambient global Python,
which lacks the `build` package installed; independently reconfirmed
identical via `git stash` A/B at the committed candidate commit.

**Fast Green:** phase-entry `HEAD`: 335 failed / 8692 passed / 5 skipped
/ 9 errors. Committed candidate commit: 336 failed / 8691 passed / 5
skipped / 9 errors — exactly **one** attributable nodeid
(`test_head_equals_origin_main`, a pre-push local-ahead-of-origin
self-check that resolves the instant this phase is pushed). Deselecting
the full 345-nodeid failing/erroring set at the candidate commit: **0
failed, 8691 passed, 5 skipped.** Zero attributable regressions.

**Runtime:** `Observed`/`observe`/`unavailable`, unchanged, reconfirmed
from source and from the installed release-candidate wheel.

**Release:** `v0.4.0` remains **NOT RELEASED**. No tag, GitHub Release,
artifact upload, or PyPI publication occurred. `v0.3.1`/`v0.3.0`
untouched. The article track remains stopped;
`~/repos/pcae-deepseek-research` was not inspected, modified, or
imported from.

**BLOCKING: 0. MUST-FIX: 0.** Recommended next phase:
`149O.20L.7O.3D — PCAE v0.4.0 Public Release`, gated on explicit human
authorization before any irreversible publication step.

See `docs/PHASE_149O_20L_7O_3C_4_CONNECTED_CAPABILITY_RELEASE_SCOPE_VERSION_AND_REPRODUCIBLE_BUILD_HARDENING.md`
for the full evidence trail, delta table, and publication checklist.
