# Phase 149O.19.5B Complete — HMIC Implementation + Contract Identity Derivation

**Phase ID:** 149O.19.5B
**Mode:** bounded production implementation (Wave B of 5 under HMIC-001 v1.0)
**Predecessor:** 149O.19.5A (HMIC Certification Data Models + Canonical Parsing — completed, Wave A)
**Date:** 2026-08-10
**Status:** completed
**Implementation verdict:** `HMIC IMPLEMENTATION + CONTRACT IDENTITY DERIVATION: IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE`
**Commits:** 34eae7050f8159071b45ceb9785592b7ae7dc1a0, 8d270ad9ceafb43730b2454b9d4b1052aa5396dc, 786246c4bf9d8fb50ff4a8ff7efbba86be0573a1
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_19_5B_HMIC_IMPLEMENTATION_CONTRACT_IDENTITY_DERIVATION.md`)
is the canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0` at entry, 149O.19.5A completed/complete at
`889bb98b`, HMIC-001 status VERIFIED WITH NON-BLOCKING FINDINGS —
CONFORMS, hardcoded `False` readiness ceiling unchanged, HATP production
NOT READY, runtime `Observed/observe/unavailable`.

**Scope decision (confirmed with requester before implementation):**
the governing prompt asked for a Wave-B runtime/executed-source-binding
check. Direct contract inspection found HMIC-REQ-063 names this an
explicit, out-of-scope-for-v1.0 residual limitation, and the 149O.19.4
plan's own Wave B API surface (§9.3) names exactly six functions, none
a runtime-source-binding check. Implementing one anyway would be
undocumented scope creep beyond the frozen, independently-verified
plan. **Decision: skip it.** This phase implements exactly the plan's
six named functions plus `derive_certification_id`.

**Implemented:** extended `src/pcae/core/hatp_mandatory_certification.py`
(sole production file touched — the same module Wave A created) with
the pure identity-derivation layer: `_FROZEN_AUTHORITY_BEARING_FILES`
(the literal 22-path HMIC-REQ-050 enumeration, re-extracted and matched
string-for-string against live contract text at test time),
`derive_repository_instance_id`, `derive_canonical_deployment_root`,
`derive_implementation_commit` (`git rev-parse HEAD`, HMIC-REQ-046),
`derive_implementation_scope_digest` (the exact two-level SHA-256
domain-separated per-file-record construction, HMIC-REQ-054-062,
TOCTOU-resistant `O_NOFOLLOW` reads, full symlink-walk-to-repository-
root safety), `derive_contract_versions` (the four-contract HMRC-001/
HATP-001/HSCE-001/RAE-001 bound set, HMIC-REQ-067), and
`derive_certification_id` (HMIC-REQ-038, pure, no I/O). Every
filesystem-facing function takes a neutral `root: HarnessPath` locator
only; no function accepts a caller-supplied Git SHA, digest, file-list,
contract, or source-binding override.

**Live-repository finding:** the four bound contract files are not
byte-consistent about their own header label — `HMRC-001` uses
`**Contract ID:**` while `HATP-001`/`HSCE-001`/`RAE-001` use
`**Contract:**` (confirmed by direct inspection of all four files).
HMIC-001's text never gives an explicit parsing grammar for this
header. `derive_contract_versions` matches both observed spellings — a
documented convention-matching decision against the contracts' own live
text, not a guessed grammar.

**Fails closed throughout:** `HMICIdentityDerivationError` and four
narrower subclasses (`FrozenFileDerivationError`,
`GitIdentityDerivationError`, `ContractIdentityDerivationError`,
`RepositoryIdentityUnavailableError`) — missing/symlinked/non-regular
frozen files, an unreachable Git repository, and a missing/malformed
contract header all raise rather than returning a partial or default
identity. No `is_certified`/`verified`/`valid`-named function exists;
no `derive_*` function returns or is annotated to return
`CertificationStatus`.

**Stop Condition W-1 preserved unconditionally:** the module is never
imported by `hatp_mandatory_cutover.py`; the hardcoded
`mandatory_consumption_implementation_independently_verified = False`
ceiling remains byte-unchanged; `hatp_mandatory_certification.py` itself
remains outside the v1.0 22-file frozen subject.

**Two 149O.19.5A-era stale dependency-closure assertions widened, in
place** (deliberate, plan-traced, mirrors the existing 149O.19.3-era
widening precedent already in this repository's history): both
`tests/test_phase_149o_19_5a_hmic_certification_models_canonical_
parsing.py` and `tests/test_hatp_mandatory_certification_models.py`
forbade `subprocess`/`hatp_bootstrap` imports that the 149O.19.4 plan
explicitly assigns Wave B (`derive_implementation_commit`'s `git
rev-parse HEAD`; `derive_canonical_deployment_root`'s literal "calls
hatp_bootstrap.py"). Widened to admit exactly these two plan-authorized
additions; every other forbidden import (`hatp_mandatory_cutover`,
providers, Permission Broker, `rollback_approval_evidence`, `agent`,
`cli`) remains fully enforced.

**Added a 78-test Wave-B suite**
(`tests/test_phase_149o_19_5b_hmic_identity_derivation.py`) covering:
22-file manifest exactness (re-extracted from live contract text),
frozen-path-literal safety, implementation-scope-digest algorithm
(independently-computed golden fixture, per-file sensitivity for both
file groups, non-frozen-file invisibility, missing/symlinked/
non-regular-file rejection including a symlinked-parent-directory
case), real-temporary-Git-repo commit derivation (not mocked), commit/
digest AND-semantics independence, repository/deployment identity
(fail-closed absence, no creation side effect), contract-version
derivation (both live header-label spellings, fixed deterministic
order, real-repository four-contract exactness), certification-ID
derivation (independently-computed golden fixture, purity proof,
per-field mutation sensitivity), no-certification-validity-judgment
proofs, and Wave-B dependency discipline.

Ran full Fast Green under the repository's pinned CPython 3.9.6
virtualenv (`.venv/bin/python -m pytest -m fast_green`). True A/B
baseline established via a real `git worktree` checkout of the
phase-entry commit (`889bb98b`) — not just an uncommitted-diff
comparison: baseline **34 failed / 5840 passed**; post-commit **33
failed / 5919 passed**. The only baseline failure absent post-commit
(`test_shell_gate.py::TestAuditPersistence::
test_verify_detects_tampered_record`) is a one-off flake, absent from
every other run this phase; every other failing nodeid is identical
between baseline and post-commit (confirmed by exact `diff` of the
sorted `FAILED` line lists). Clean, deselected run (all 33 pre-existing
nodeids explicitly `--deselect`ed): **0 failed / 5919 passed / 1
skipped** — zero new failures introduced.

No production source outside the one Wave-B-authorized module edit was
modified. No contract file (`HMIC-001`/`HMRC-001`/`HATP-001`/`HSCE-001`/
`RAE-001`/`RWMPC-001`/`PBPA-001`/`PBPC-001`) was modified — all remain
byte-unchanged. The exact 22-file `HMIC-REQ-050` frozen subject remained
byte-unchanged. No Permission Broker/`POL-005` change. No `COMP-002`
capability implemented. No certification artifact, active-certification
pointer, or revocation record created anywhere in the repository. No
Cutover Record or activation marker created or modified. No real
`HATP_MANDATORY` activation occurred anywhere. No runtime/executed-
source-binding check was implemented (§ Scope decision above).

**B-149O.19.3-1 (unchanged, carried forward):** remains INDEPENDENTLY
CONFIRMED CLOSED. This implementation phase does not reopen or alter
it.

**B-149O-1..4 verdict (unchanged, carried forward):**
**INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED.** This phase does
not reopen or alter this finding.

**Implementation verdict:** `HMIC IMPLEMENTATION + CONTRACT IDENTITY
DERIVATION: IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION
WAVE`.

**Recommended next phase:** `149O.19.5C` — HMIC Protected Certification
State Store (Wave C: immutable certification artifact persistence,
explicit active certification binding, revocation state, atomicity,
protected storage topology, concurrency/locking, temp-root tests). Not
pre-authorized by this phase; still no active certification validation
engine, no admin ceremony, no readiness integration, no real
certification state.
