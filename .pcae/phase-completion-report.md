# Phase 149O.20L.7O.3B Complete — Selected Existing Capability Verification and Product Exposure

**Verdict: COMPLETE — INDEPENDENT VERIFICATION FROM CLEAN WHEEL/SDIST
COMPLETE. 4 CANDIDATES VERIFIED, ALL CONFIRMED FOR EXPOSURE (ONE
SCOPE-CORRECTED, ONE DOCUMENTED NARROWLY). RECOMMENDED NEXT VERSION:
v0.3.2. ZERO PRODUCTION SOURCE CHANGES. RUNTIME: Observed / observe /
unavailable. ARTICLE: STOPPED.**

Independently re-verified the four capabilities Phase 3A selected for
quick release, from a clean-built wheel and sdist (`pcae_harness-0.3.1`,
unchanged version) installed into disposable environments and exercised
against disposable git repositories outside `pcae-harness`, per the
phase brief's "verify first, document second" rule.

## Summary

`pcae runtime inspect` — confirmed a full zero-prerequisite,
no-side-effect product workflow, wheel- and sdist-verified. Interactive
Workflow/CHGR — confirmed and exercised end-to-end
(`create`→`evidence`→`select`→`preview`→`confirm`→`readiness`→
`governance-record publish`→`inspect`/`verify`), producing a real,
schema-verifiable CHGR record; authority distinctions
(preview≠confirmation≠publication≠execution) hold and are documented.
Repository Intelligence — confirmed real, tested, and safe, but
**scope-corrected**: `snapshot generate` hardcodes `src/pcae/`,
`tests/`, `schemas/repository_intelligence/` as required top-level
paths (verified both by a live failing invocation against a bare
disposable repository and by direct source citation), meaning it only
functions as *self-inspection of a `pcae-harness`-shaped checkout*, not
a general "analyze any repository" feature — documented accordingly,
correcting 3A's unqualified framing. `pcae authority inspect` —
confirmed read-only/non-authoritative/fail-closed, but no production
record artifact of any family it supports exists anywhere in this
repository's tracked governance state today (CLTR migration remains
`production_authority: "legacy"`) — documented narrowly as advanced
CLTR-tooling, not a README headline.

## Findings

One apparent defect during `governance-record publish` testing
(`internal_error`) was fully reproduced by bypassing the CLI's error
wrapper and correctly attributed to invalid test input — a
`--template-ref` value (`"manual:v1"`) violating CHGR's closed
identifier pattern (`^[a-z][a-z0-9_-]{2,63}$`), not a code defect;
retrying with a conformant value completed the workflow successfully.
One minor, non-blocking UX rough edge was found and documented, not
repaired: `decision_session.py`'s shared error-mapping wrapper collapses
every non-`ApplicationServiceError`/`ValueError` exception — including
this legitimate, specific `ChgrSchemaConformanceError` — into the same
generic `internal_error` message.

`docs/COMMANDS.md` was found to be a *generated* artifact (`pcae docs
commands`) whose generator does not currently enumerate `pcae runtime
inspect`, `pcae repository-intelligence`, or `pcae authority inspect` as
command areas (`pcae docs commands --dry-run` output was byte-identical
to committed `HEAD`). An initial hand-edit was reverted (`git checkout
--`) once this was identified, to avoid permanent generated-artifact
drift; a new hand-maintained `docs/CAPABILITY_REFERENCE_V0_3_2.md` was
created instead. This generator gap is disclosed as operational debt,
not fixed (a production-source change, out of scope here). One
accidental write to this repository's own tracked
`.pcae/repository-intelligence/latest.json` occurred during initial
Repository Intelligence verification and was immediately caught and
reverted before any further work.

## Final v0.3.2 Batch

1. Runtime/plugin introspection (`pcae runtime inspect`) — CONFIRMED, full product workflow
2. Interactive Workflow/CHGR — CONFIRMED, full product workflow (one field-format caveat documented)
3. Repository Intelligence — CONFIRMED, scope-corrected to self-inspection docs
4. `pcae authority inspect` — CONFIRMED, advanced CLTR-tooling docs only

**Recommended theme:** expose PCAE's existing governed inspection and
intelligence capabilities as supported installed workflows, accurately
scoped to what each one actually does. **Recommended version:** v0.3.2
(unchanged from 3A).

## Test Evidence

962 targeted existing tests run across the four capabilities (0
failures), not a full `python -m pytest -n auto` regression — per the
phase brief's explicit focused-verification instruction. Suites:
`test_runtime_registry_{contract,prototype,verification}.py`,
`test_runtime_introspection_{prototype,architecture}.py`,
`test_authority_inspect_137k.py`, `test_typed_authority_inspector_137e.py`
(693 combined); `test_phase_145g_decision_session_cli.py`,
`test_phase_145g1_decision_session_cli_repair.py`,
`test_phase_145g3_decision_session_identity_binding.py`,
`test_iwc_143o_session_coordination_publication_handoff.py`,
`test_phase_144c_publication_coordinator.py` (197); `test_phase_120e_
repository_knowledge_snapshot.py`, `test_phase_121e_repository_
intelligence_query.py`, `test_phase_122e_repository_intelligence_
advisory_context.py`, `test_phase_123e_repository_intelligence_
change_impact.py`, `test_phase_124e_repository_intelligence_
hardening.py` (72).

## Governance

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings, unchanged,
repository-maintainer-only. `pcae runtime inspect`:
`execution_capability: unavailable`, unchanged before/after this phase.
No article read/modified/published. No inspection of the private
`~/repos/pcae-deepseek-research` repository. No PyPI action, no tag, no
GitHub Release. No production source, CLI, contract, schema, or
packaging-configuration file was modified this phase.

## Recommended Next Phase

**3C — PCAE v0.3.2 Release Hardening and Release Candidate
Verification.** Freeze the exact v0.3.2 scope finalized in this phase,
bump version, prepare release notes, build wheel/sdist, verify
checksums, clean-install smoke, rerun the four selected capability
workflows exactly as documented here, run release-critical regression,
produce a publication checklist, do not publish.

Full text:
`docs/PHASE_149O_20L_7O_3B_SELECTED_EXISTING_CAPABILITY_VERIFICATION_AND_PRODUCT_EXPOSURE.md`.
