# Phase 149O.20L.7O.3D Complete — PCAE v0.4.0 Public Release

**Verdict: PCAE v0.4.0 PUBLICLY RELEASED.** Explicit human publication
authorization was obtained before any irreversible action. Independently
re-verified the frozen 3C.4 release candidate rather than trusting its
summary — re-derived candidate identity, version, `v0.3.1`/`v0.3.0`
isolation, and build hashes from primary sources; independently resolved
a real arithmetic/categorization error in 3C.4's own Fast Green count.
Created and pushed annotated tag `v0.4.0` bound exactly to the candidate
commit, published the GitHub Release, uploaded hash-verified artifacts,
and independently confirmed public asset byte-identity. Ran the Plan
B+/corrupt-store/Permission Broker behavioral suite against the public
wheel. PyPI confirmed not published. Runtime unchanged
(`Observed`/`observe`/`unavailable`).

## Summary

**Release candidate:** `ea3f731ef50ea16985fd4a0562f0c091bb8109b2`
(3C.4's own phase-owning commit). `git diff` from candidate to
phase-entry `HEAD` touched only lifecycle/reporting files — zero drift
in `src/pcae`/`pyproject.toml`.

**Fast Green correction (Sec 5 of the phase document):** 3C.4's prose
breakdown ("344+2+1=347") did not match its own stated 345-nodeid total.
Two independent full re-runs at unchanged `HEAD` gave **335 failed /
8692 passed / 5 skipped / 9 errors** and **336 failed / 8691 passed / 5
skipped / 9 errors** (±1 known `test_head_equals_origin_main`-style
timing flake). Direct nodeid inspection (not prose) found the failing
set spans a much broader pre-existing self-referential "no drift since
my own historical candidate SHA" cluster than 3C.4 characterized —
`deploymentbinding`, `dell_redeployment`, `repositoryidentity`, `hmrc`,
`shell_gate`, plus HATP/HMIC/HBDC — but **zero nodeids reference
`governance_auto_publication`, `publication_permission_gate`,
`mutation_permission`, or `phase.py`'s new auto-publish call site**.
**Attributable regressions = 0**, confirmed on stronger evidence; 3C.4's
own report was not edited.

**Build reproducibility (re-verified):** two additional independent
clean-clone builds pinned to the candidate commit (one pre-authorization
verification pass, one immediately before upload) both reproduced:

```text
wheel:  pcae_harness-0.4.0-py3-none-any.whl (2,349,213 bytes)
        sha256: 8125d21dc5093892d7303ccbd416cfed91429798ad2d3f17e1512d24b2c3ea00
sdist:  pcae_harness-0.4.0.tar.gz (2,051,181 bytes)
        sha256: 13492127f261e0460ba943598dca010881c672e2c2602348697050f763960f61
```

Byte-identical to the canonical 3C.4 record across all 4 independent
builds now performed.

**Tag:** annotated `v0.4.0` created bound explicitly to the candidate
commit (verified via `git rev-parse v0.4.0^{commit}` before push), then
pushed with no force. Remote peeled ref (`git ls-remote --tags origin
'refs/tags/v0.4.0^{}'`) confirmed identical. **local tag == remote tag
== release_candidate_commit == tagged_commit.**

**GitHub Release:** `https://github.com/atimad/pcae-harness/releases/tag/v0.4.0`,
not draft, not prerelease, marked Latest, `targetCommitish` verified.
Assets uploaded with hashes matching the frozen record exactly; GitHub's
own reported digests matched; **independently downloaded both public
assets and re-hashed them — byte-identical to the release-of-record.**

**Post-publication smoke (public artifacts only, no local source):**
public wheel and sdist both install cleanly in fresh disposable venvs,
report `0.4.0`, CLI functional, golden path passes. The 51-test 3C.3/
3C.3.2 independent-verification suite (Plan B+ auto-publish, corrupt-
store fail-closed, Permission Broker no-bypass) was run directly against
the public wheel's installed code: **43 passed, 8 failed** — the 8
failures are AST/source-scan tests requiring a repo checkout
(structurally inapplicable to an installed-artifact-only environment),
not behavioral regressions. `pcae runtime inspect` from the public wheel
confirms `Observed`/`observe`/`unavailable`, unchanged.

**PyPI:** confirmed **NOT PUBLISHED** via a direct `404` from
`pypi.org/pypi/pcae-harness/json` (not assumed).

**Isolation:** `v0.3.1`/`v0.3.0` GitHub Releases and tags untouched. The
article track remains stopped; `~/repos/pcae-deepseek-research` was not
inspected, modified, or imported from.

**BLOCKING: 0. MUST-FIX: 0.**

**Next strategic direction (not started):** which deferred mature PCAE
capability becomes production-consumed next — candidates: Repository
Intelligence internal consumption, Runtime/plugin capability-aware
orchestration, remaining Permission Broker coverage, Runtime Enforcement
consumption, rollback readiness/evidence integration, Advisory context
consumption.

See `docs/PHASE_149O_20L_7O_3D_PCAE_V0_4_0_PUBLIC_RELEASE.md` for the
full evidence trail.
