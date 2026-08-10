# Phase 149O.19.5C Complete — HMIC Protected Certification State Store

**Phase ID:** 149O.19.5C
**Mode:** bounded production implementation (Wave C of 5 under HMIC-001 v1.0)
**Predecessor:** 149O.19.5B (HMIC Implementation + Contract Identity Derivation — completed, Wave B)
**Date:** 2026-08-10
**Status:** completed
**Implementation verdict:** `HMIC PROTECTED CERTIFICATION STATE STORE: IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE`
**Commits:** ef451f4c990479cfe717ee1b1bc8d3152f4ef1bf, 37d6bd001f740de5a6430fc6befb3da46a25c530, e5da16ed572b70fa9ff60145c2fa8a07ccf07339
**Pushed:** pending
**origin/main..HEAD:** 3
**Metadata consistency:** consistent

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_19_5C_HMIC_PROTECTED_CERTIFICATION_STATE_STORE.md`)
is the canonical artifact of this phase. Confirmed baseline: repo clean,
`origin/main..HEAD=0` at entry, 149O.19.5B completed/complete, HMIC-001
status VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS, hardcoded
`False` readiness ceiling unchanged, HATP production NOT READY, runtime
`Observed/observe/unavailable`.

**Scope wall preserved:** stored ≠ active-valid ≠ independently
verified ≠ readiness ≠ activation authority. This wave answers only:
does artifact ID X exist? what bytes/model are stored for X? which
explicit certification ID is currently bound? is certification ID X
explicitly recorded as revoked? It never answers whether X is valid,
correctly bound, or whether activation may proceed — those remain Wave
D and Wave F, not implemented here.

**Implemented:** extended `src/pcae/core/hatp_mandatory_certification.py`
(sole production file touched — the same module Waves A/B created) with
the protected storage/locking layer: `_certification_transition_lock`
(dedicated `.certification-transition.lock`, `fcntl.flock`, distinct
from HMRC-001's own `.cutover-transition.lock`), `_reject_unsafe_
protected_path` (symlink rejection generalized to storage paths that
may not yet exist), `_atomic_write_protected_json` (`mkstemp`+`fsync`+
`os.replace`), tri-state (OK/ABSENT/MALFORMED) readers `_read_
certifications`/`_read_certification_bindings` (never auto-provisioning,
never lock-acquiring), explicit-ID load seams plus their production,
agent-readable wrappers `load_certification`/`load_active_binding`, and
internal admin-only-caller writers `_append_certification_record`/
`_write_active_binding`/`_write_revocation`. Both on-disk files
(`certifications.json`, `certification-bindings.json`) are single
shared documents keyed by `(repository_instance_id, canonical_
deployment_root)`, directly under `HATPTrustStore.production().root` —
no directory-per-repository layout, no path ever built from
`certification_id`.

**Create-once + self-consistency:** `_append_certification_record`
re-derives `certification_id` from a candidate's own eight stated
fields before persisting, refusing a self-inconsistent record; an
exact byte-identical replay is an idempotent no-op, any byte difference
is a rejected conflict. **Active binding:** plain locked last-write-wins
(HMIC-REQ-099, never compare-and-swap); no implicit-latest selection;
never verifies the pointed record exists, and never rewrites/clears a
binding merely because the pointed record is later revoked.
**Revocation:** monotonic field mutation on the existing record, never
deletion, never an un-revoke path; identical-timestamp replay is
idempotent, a differing timestamp is a rejected conflict.

**Fails closed throughout:** `CertificationStorageSymlinkError`,
`CertificationRecordNotFoundError`, `CertificationConflictError`,
`CertificationIdentityMismatchError` — symlinked/non-regular storage
paths, missing records, conflicting writes, and self-inconsistent
candidates all raise rather than silently succeeding or falling back.
No `is_valid`/`is_certified`/`validate_active`-named function exists in
this module; no admin ceremony, no ordinary `pcae` CLI surface; every
write primitive is private and never called with `HATPTrustStore.
production().root` anywhere in this module.

**Stop Condition W-1 preserved unconditionally:** the module is never
imported by `hatp_mandatory_cutover.py`; the hardcoded
`mandatory_consumption_implementation_independently_verified = False`
ceiling remains byte-unchanged; `hatp_mandatory_certification.py` itself
remains outside the v1.0 22-file frozen subject.

**Two 149O.19.5A/B-era stale scope-boundary assertions widened, in
place** (deliberate, mirrors the existing 149O.19.3-era/149O.19.5B-era
widening precedent already in this repository's history): the 19.5A
suite's network-abstinence check now inspects actual `import` statements
via AST rather than a raw substring scan (Wave C legitimately
introduces the word "socket" in a non-regular-file-rejection comment and
imports `fcntl` for locking, neither network-shaped — the real
invariant, no `socket`/`requests`/`urllib` import, is unchanged and
re-checked precisely); the 19.5B suite's "never reads
certifications.json" check now scopes its string-literal scan to Wave
B's own named functions only, since Wave C's own later section of the
same file legitimately reads/writes both certification filenames.

**Added a 56-test Wave-C suite**
(`tests/test_phase_149o_19_5c_hmic_protected_certification_state_
store.py`) covering: no-auto-provisioning reads, storage topology
(exactly two files + lock, no per-cert path), create-once/idempotent/
conflict/self-consistency, atomic write (no temp residue on success,
cleanup on `fsync` failure), active-binding no-implicit-latest/
explicit-pointer/plain-replace semantics, revocation (field mutation,
monotonicity, idempotency, conflict, no un-revoke, revoked-binding-
unaffected), symlink rejection (root, immediate parent, both files,
write-time final-path symlink), non-regular-file rejection (directory,
FIFO), malformed-vs-absent distinction, multi-repository/multi-
deployment isolation, copy-attack, dedicated-lock-file identity,
real-thread (not mocked) concurrency races, production-entrypoint
read-only-surface confirmation, and import-side-effect-free
confirmation.

Ran full Fast Green under the repository's Python interpreter
(`python3 -m pytest -m fast_green`). True A/B baseline established via
`git stash -u` — not just an uncommitted-diff comparison: baseline
**37 failed / 5853 passed**; post-implementation **39 failed / 5907
passed**. Exact `diff` of the sorted `FAILED` line lists confirms all
37 baseline failures byte-identical between runs (unrelated
pre-existing issues — a flaky parametrized timestamp test and several
already-broken ancient "no-production-change-since-me" assertions),
and exactly 2 net-new failures, both the same already-documented
benign class this repository's own 149O.19.5A/B phase docs record
repeatedly: an ancient phase's own "no `src/pcae/` change since my
fixed historical entry commit" assertion, tripped for the first time by
this file's first touch since that old baseline — not a functional
regression. Clean, deselected run (all 39 pre-existing/newly-tripped
nodeids explicitly `--deselect`ed): **0 failed / 5907 passed / 2
skipped** — zero functional regressions introduced.

No production source outside the one Wave-C-authorized module edit was
modified. No contract file (`HMIC-001`/`HMRC-001`/`HATP-001`/`HSCE-001`/
`RAE-001`/`RWMPC-001`/`PBPA-001`/`PBPC-001`) was modified — all remain
byte-unchanged. The exact 22-file `HMIC-REQ-050` frozen subject remained
byte-unchanged. No Permission Broker/`POL-005` change. No `COMP-002`
capability implemented. No real certification artifact, active-
certification pointer, or revocation record created anywhere on this
host — every test uses an isolated `tmp_path` protected root. No
Cutover Record or activation marker created or modified. No real
`HATP_MANDATORY` activation occurred anywhere.

**B-149O.19.3-1 (unchanged, carried forward):** remains INDEPENDENTLY
CONFIRMED CLOSED. This implementation phase does not reopen or alter
it.

**B-149O-1..4 verdict (unchanged, carried forward):**
**INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED.** This phase does
not reopen or alter this finding.

**Implementation verdict:** `HMIC PROTECTED CERTIFICATION STATE STORE:
IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE`.

**Recommended next phase:** `149O.19.5D` — HMIC Active Certification
Validation Engine (Wave D: fresh active-binding load, explicit-
certification load, revocation evaluation, repository/deployment
cross-check, implementation identity comparison, contract identity
comparison, verification-record checks owned by contract, exact closed
HMIC `ValidationStatus` result). Not pre-authorized by this phase;
still no admin ceremony, no readiness integration, no hardcoded-`False`
replacement, no activation.
