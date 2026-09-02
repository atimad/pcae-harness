# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1.1 — INDEPENDENTLY VERIFIED

**Independent Verification of the N-16-5 PAWA `HPACWriterCapability`
Non-Bearer / One-Operation Integrity Repair (`.1R.30R.3.2.1`)**

**STATUS: INDEPENDENTLY VERIFIED.** Independent re-derivation from primary
source (contract, production code, and fresh, independently-constructed
adversaries — not merely re-running or trusting `.1R.30R.3.2.1`'s own
claims) confirms the repair closes the decisive `.1R.30R.3.2` BLOCKED
finding, introduces no new bypass, makes no normative contract change, and
stays within every scope fence. One non-blocking finding is disclosed (a
pre-existing, repair-unrelated write-ordering property, empirically
confirmed to grant no authority bypass). **N-16-5 Slice 1: CLOSED.**

## 1. SHAs

- **A** (finalized `.1R.30R.3.1` head) = `aff46ec3`
- **V** (finalized `.1R.30R.3.2` head) = `83b7f70b`
- **R0** (`.1R.30R.3.2.1` phase-entry SHA, == V) = `83b7f70b`
- **R** (finalized `.1R.30R.3.2.1` repair head) = `f3c4424c`
- **I** (`.1R.30R.3.2.1.1`, this phase's entry SHA) = `59e08949` (`git
  status --branch --short` showed `main...origin/main`, clean tree,
  `origin/main..HEAD = 0` at entry)

Independently re-derived from `git log --oneline` / `git rev-parse`, not
inherited from prose.

## 2. Primary sources read (in full, independently, not merely trusted)

- `docs/PHASE_..._30R_3_2_1_...REPAIR.md` (the `.1R.30R.3.2.1` repair
  report) — read in full.
- `docs/PHASE_..._30R_3_2_...SLICE_1.md` (the `.1R.30R.3.2` BLOCKED IV
  report) — read in full.
- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.1) §40–§49 (`HPACWriterCapability` class through
  one-operation), §56 (failure taxonomy, row 20) — read in full.
- Production source in full: `src/pcae/core/hpac_foundation.py`
  (`HPACWriterCapability`, `_CapabilityIssuanceRecord`,
  `_ISSUED_CAPABILITY_REGISTRY` and its three helper functions,
  `HPACStoreAuthority._new_capability` / `require_writer` / `record_write`),
  `src/pcae/core/hpac_protected_admin_writer.py` (`production_writer`,
  `ProductionWriterHandle.consume`, `_record_issuance_evidence`),
  `src/pcae/core/human_principal_registry.py` (`_write`, `_writer`,
  `enroll_principal`, `revoke_principal`, `_load`).
- The existing `.1R.30R.3.1` product suite (99 tests, including
  `test_55a`-`test_55d`) and the `.1R.30R.3.2.1` dedicated repair suite (24
  tests) — read in full.

## 3. Independent historical A→R adversary re-derivation

Constructed a fresh detached `git worktree` at immutable `A = aff46ec3`
(not the `.1R.30R.3.2.1` repair phase's own worktree — a new one, in a
different scratch location) and an independently-written reproduction
script (own field selection, own fixture wiring via `A`'s own test
module — mechanical plumbing only, not the adversary logic):

1. Mint one legitimate `PRODUCTION` capability via `production_writer()`.
2. Spend it once: `HumanPrincipalRegistryStore.enroll_principal(cap, ...)`.
3. `forged = HPACWriterCapability.__new__(HPACWriterCapability)`; copy
   `_authority_seal`, `role`, `subject`, `authority_class` off the spent
   `cap`; set `_single_use = True`, `_spent = False`.
4. `store.revoke_principal(forged, ...)`.

**Result at A:** `SECOND MUTATION (revoke_principal) via forged
capability: SUCCEEDED` — the historical defect independently reproduces.

**Result at R (this working tree, identical script):**
`HumanPrincipalRegistryError: writer capability is absent, forged, or
bound to another HPAC root` — rejected.

## 4. Root cause (independently re-derived)

`require_writer`'s pre-repair check (`writer._authority_seal is
self._seal`) binds only on a plain, readable, `__slots__` instance
attribute. `HPACWriterCapability.__new__` bypasses `__init__`'s
constructor-seal gate. A caller already holding one legitimate (even
already-spent) capability can read its real `_authority_seal` object off
it and assign that exact reference onto a `__new__` shell — the identity
check then genuinely, not fraudulently, passes. No field stored *on* the
capability object can close this, because any such field is, by the same
argument, readable and copyable. Independently confirmed against
`hpac_foundation.py` source at both A and R.

## 5. HPAC-PAWA-REQ-102/103 analysis — independently adjudicated

| Requirement | Normative property | Mechanism prose | Repaired implementation | Equivalent? |
|---|---|---|---|---|
| REQ-102 (§46) | Canonical, process-local, non-bearer capability, recognised by *identity*, not value comparison | "recognised by `require_writer`'s identity check (`writer._authority_seal is self._seal`)" — one example mechanism | Two identity checks: seal identity (unchanged) + registry-object-identity (new, `record.capability is writer`) | Yes — still identity-based, still not a value comparison; the *property* REQ-102 states is delivered, now by a strengthened mechanism |
| REQ-103 (§47) | `object.__new__` + known-field reconstruction fails as authority | "fails the seal-identity check" | Now literally true again: a reconstruction fails, for the correct reason (registry non-membership), not by accident | Yes, restored |
| §56 row 20 | `reconstruction_attempt` maps to a forged/`object.__new__` capability failing the seal-identity check | same | Same failure code path still applies (rejection still raises `HPACAuthorityError`, still mapped to `reconstruction_attempt`-class rejection at write time) | Yes |

**Contract-versioning verdict (independently derived): no change needed.**
REQ-102 describes a security *property* via one *example* mechanism, not
an exhaustive mechanism specification; the repair adds a second,
still-identity-based check, which is additive strengthening, not a
mechanism replacement requiring a MINOR/PATCH bump. `git diff 83b7f70b
HEAD -- docs/contracts` is empty; `HPAC-PAWA-001` v1.1, `HPAC-001` v2.1,
`RHAMP-001` v1.0, `HBDC-001` v1.2 are byte-unchanged. **CONFIRMED** — this
independently re-derives (not merely re-states) the repair report's own
§5 verdict.

## 6. Issuance registry — independent inventory

- **Module:** `src/pcae/core/hpac_foundation.py` only. Independently
  confirmed via `grep -rl --include=*.py` across `src/pcae`: no other
  module references `_ISSUED_CAPABILITY_REGISTRY`,
  `_register_issued_capability`, `_lookup_issued_capability`, or
  `_mark_capability_consumed`.
- **Key:** `id(capability)`. **Value:** `_CapabilityIssuanceRecord`
  (`capability` — strong reference; `issuance_id` — 32 random bytes,
  never exposed; `role`, `subject`, `authority_class` — frozen at mint;
  `state` — `ACTIVE`/`CONSUMED`).
- **Lock:** `_ISSUANCE_REGISTRY_LOCK` (`threading.Lock`), held across
  every registry read and write in all three helper functions —
  independently confirmed by source inspection of each function body.
- **Population path:** `_register_issued_capability`, called only from
  `HPACStoreAuthority._new_capability` (the sole construction site).
- **Consumption path:** `_mark_capability_consumed`, called only from
  `record_write`, at the same transition point the pre-existing
  object-local `_mark_spent` call already occupied (independently located
  by source-order inspection of `record_write`: the registry-consumed
  transition is co-located with, and follows, the provenance write).
- **Invalidation/reset:** none exists. An AST-level inventory of every
  module-level function in `hpac_foundation.py` whose body references
  `_ISSUED_CAPABILITY_REGISTRY` found **exactly** the three expected
  functions — no `_clear_issued_capabilities`, `_invalidate_capability`,
  `_deregister_capability`, or `_reset_registry` helper exists anywhere in
  source.

**Registry write ownership (independent inventory):**

| Function | Operation | Authorized? | Why |
|---|---|---|---|
| `_register_issued_capability` | insert | Yes | sole caller: `_new_capability`, the sole construction site |
| `_lookup_issued_capability` | read-only | Yes | called from `require_writer` |
| `_mark_capability_consumed` | state transition ACTIVE→CONSUMED | Yes | sole caller: `record_write`, at the existing spend transition point |

No unexpected direct-registration helper exists.

## 7. Registry key safety / object-ID reuse — independently verified

`_lookup_issued_capability` checks `record.capability is capability` in
addition to the `id()`-keyed dict lookup (source-confirmed; independent
test written to exercise the lookup path against both the real object and
an unrelated impostor object). The registry holds a **strong reference**
to each issued capability for the life of its entry — independently
confirmed via `inspect.getsource` on `_CapabilityIssuanceRecord.__init__`
(`self.capability = capability`, no `weakref`). Consequence, independently
verified: a full `gc.collect()` pass while a capability is still
reachable does not evict its ACTIVE registry entry, and — because the
strong reference keeps the object alive for the life of the entry — `id()`
can never be silently reassigned to a **different live**
`HPACWriterCapability` while an entry stands, closing the classic id-reuse
forgery this table would otherwise itself be vulnerable to.

## 8. Field mutation on a genuinely issued (non-shell) capability —
independently verified

Distinct from the repair suite's shell-based transplant tests: mutated
`subject`, `role`, and `authority_class` directly on **real, registered**
capability objects (not shells) and called `require_writer`:

- Mutated `subject` → rejected (registry-recorded `subject` dominates);
  restoring the true `subject` re-validates successfully — the mutation
  attempt did not corrupt the registry-authoritative record.
- Mutated `role` → rejected.
- Mutated `authority_class` (PRODUCTION → FIXTURE_NON_REAL on the object) →
  **has no effect at all** on `require_writer`'s decision, because the
  check compares `record.authority_class` (registry, frozen PRODUCTION),
  never `writer.authority_class` (the mutated field) — the strongest
  possible demonstration of registry dominance for this field.

## 9. Registration-failure fail-closed — independently verified

Injected a failure inside `_CapabilityIssuanceRecord.__init__`
(`secrets.token_bytes` raising) during a mint attempt. The exception
propagates out of `_new_capability` before any capability is returned to
the caller; independently confirmed the registry gained **no new entry**
as a result (snapshot-diffed before/after). No capability escapes as
authoritative when registration fails.

## 10. Validation-failure lifecycle — independently verified

A wrong-subject `enroll_principal` attempt against a genuine, unspent
capability is rejected (`HumanPrincipalRegistryError`); the registry entry
remains `ACTIVE` and `cap._spent` remains `False` afterward — the rejected
attempt does not corrupt or burn the capability. A subsequent
correctly-scoped call with the same capability object still succeeds.

## 11. Post-durable-write / pre-consumption-mark exception path — the
decisive one-operation question, independently investigated

This is the one item this IV pursued beyond the existing suites' own
coverage, because `record_write`'s ordering places the capability's own
`_mark_spent` / the new `_mark_capability_consumed` call **after** its own
provenance write — while the actual registry-document mutation (in
`HumanPrincipalRegistryStore._write`) happens **before** `record_write` is
even called. If `record_write`'s own provenance write then fails, does the
capability remain reusable for a second, distinct, successful mutation?

**Independently tested** (`monkeypatch` on `write_atomic_replace` to fail
only the provenance write, not the registry-document write):

1. The registry-document mutation (e.g. `enroll_principal`'s document
   write) **does** land durably — confirmed via a subsequent
   `HPACAuthorityError: HPAC record has no writer provenance` on read
   (the record exists; only its provenance is missing).
2. `cap._spent` remains `False`; the issuance-registry record remains
   `ACTIVE` — the capability's bookkeeping does not reflect the mutation
   that already happened.
3. **Decisive test:** the same, formally-still-ACTIVE capability was then
   used for a second, semantically distinct mutation (`revoke_principal`).
   **Result: rejected** — `HPACAuthorityError: HPAC record has no writer
   provenance`. Every registry read (`HumanPrincipalRegistryStore._load`)
   requires `verify_record` to succeed, which itself requires the
   provenance record that failed to write; the store fails closed for
   **all** subsequent operations (read or write) on that record, not only
   the retried one.

**Conclusion:** no authority bypass is achievable through this path — the
store's own read-time fail-closed requirement (unrelated to, and
unchanged by, this repair) closes the gap the capability's own
bookkeeping leaves open. This is a genuine, verified property, not an
assumption.

**Disclosed as a non-blocking finding, not BLOCKED:** the capability's
*formal* state (`_spent=False`, registry `ACTIVE`) can transiently
misrepresent reality after this specific failure combination, and the
affected registry record becomes unusable (wedged, fails closed on every
future read) until manually repaired — an availability/operability gap,
not a security bypass. This ordering is **pre-existing**, unchanged by
`.1R.30R.3.2.1` (which touched only the seal-forgery/registry-membership
question, not this write-ordering), and out of this repair's own declared
scope. **Recommendation for a future phase** (not this one): consider
moving the registry-consumption mark to occur atomically with, or before,
the registry-document write rather than after `record_write`'s own
(separate) provenance write — or making provenance-write failure itself
retry-safe. Not required to close N-16-5 Slice 1, since no authority
bypass results.

## 12. Concurrency — independently re-confirmed

A fresh 6-thread race (2 more racers than the repair suite's own 4-thread
test, to reduce the chance of a timing accident) against one `PRODUCTION`
capability: **exactly 1 of 6** concurrent `revoke_principal` calls
succeeds. `_ISSUANCE_REGISTRY_LOCK` is held across every registry mutation
in all three helper functions (source-confirmed, not merely assumed).

## 13. Issuance evidence — independently inspected (not merely trusted)

Read the actual written issuance-evidence JSON document (not just the
source that produces it). Confirmed: exactly the closed REQ-118 field set;
no `_authority_seal`; no `issuance_id`; `capability_identifier` is
deterministically `"hpaw-cap-" + sha256(operation_id)[:32]` — derivable
only from `operation_id`, never from any capability-object state.
Independently attempted the item-29 adversary: a shell built from **only**
the fields an auditor could plausibly derive from evidence (no seal at
all) is rejected by `require_writer`.

## 14. Fork / process-boundary — independently adjudicated

`grep`-confirmed: no `os.fork`, `multiprocessing`, or `subprocess.Popen`/
`subprocess.run` reachable from `hpac_foundation.py`,
`hpac_protected_admin_writer.py`, or `human_principal_registry.py`. The
contract (HPAC-PAWA-REQ-108) documents the admin tool as short-lived,
one operation per invocation. **Adjudication: fork/multi-process use is
explicitly outside the PAWA process-local trust model; no ambiguity is
introduced by this repair, and no production code path could create one.**

## 15. Consumer boundary — independently re-confirmed

`grep`-confirmed no PAWA-module token (`hpac_protected_admin_writer`,
`hpac_pawa_agent_exclusion`, `hpac_pawa_schemas`, `human_principal_registry`)
appears in `src/pcae/cli.py`, any file under `src/pcae/commands/`, or
`src/pcae/core/agent.py`. Unchanged since `.1R.30R.3.1`.

## 16. Sole construction site — independently re-confirmed

`grep`-confirmed exactly one production call expression assigning
`HPACWriterCapability(...)` anywhere in `src/pcae` (inside
`_new_capability`).

## 17. Existing-test-modification non-weakening — independently
re-examined

The one pre-existing test whose assertion text changed
(`test_require_writer_uses_identity_check_on_seal`,
`.1R.30R.1` IV suite) was diffed directly (`git show f3c4424c --
tests/...30r_1...`): the old exact-substring assertion
(`"writer._authority_seal is not self._seal"`) no longer matches because
the check is now `getattr`-wrapped; it was loosened to `"is not
self._seal"` **and** a new, additional assertion
(`"_lookup_issued_capability(writer)" in text`) was added. Net effect:
strictly additive — the new code could not satisfy the old exact-string
assertion at all (it would have false-failed on correct, hardened code),
so the substring had to track the real source change, while a materially
stronger check was added alongside it. **Not a weakening.**

## 18. Fresh independent IV suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_1_writer_capability_integrity_iv.py`
— 30 new tests, independently authored (not copied from the repair
suite's own tests), covering: independent A→R adversary re-derivation;
registry strong-reference / id-reuse structural safety; object-identity
lookup verification; field mutation on real (non-shell) capabilities
(subject / role / authority_class, 3 tests); registration-failure
fail-closed; validation-failure lifecycle; the post-durable-write
exception path (3 tests, §11 above); spend-transition source-location;
issuance-evidence content inspection and audit-reconstruction rejection (2
tests); registry non-export / issuance-function-inventory (AST-based) /
consumer-boundary statics (3 tests); fork/multiprocessing absence (2
tests); concurrency-lock-scope and a 6-thread independent re-run;
sole-construction-site / contract-byte-identity / production-diff-scope /
historical-preservation / no-new-field / runtime / no-Slice-2 rechecks (9
tests); GC/strong-reference behavior. **30 passed, 0 failed.**

## 19. Re-run of existing suites (unedited)

- `.1R.30R.3.1` product suite + the 4 `test_55a`-`d` additions: **99
  passed, 0 failed.**
- `.1R.30R.3.2.1` dedicated repair suite: **24 passed, 0 failed.**
- Combined: **123 passed, 0 failed** — matches the repair phase's own
  reported count exactly.

`git status --short -- tests/` shows only the one new, untracked IV test
file — zero existing test file was edited by this phase. No `def test_`
removed/renamed; no `skip`/`skipif`/`xfail`/`pytest.skip` added anywhere.

## 20. Broad fixed-SHA sweep (fast_green, full repository)

`python -m pytest -m fast_green -n auto -q`: **8968 passed, 342 failed, 5
skipped, 9 errors** (136.13s). Independently grepped the full failure/error
list for any token related to this repair's scope (`pawa`,
`hpac_foundation`, `hpac_protected_admin_writer`, `human_principal_registry`,
`writer_capability`, `writer_anchor`): **zero matches.** Every failure and
error belongs to unrelated historical phase-verification suites (HATP/
HMIC/HBDC/Dell-redeployment/repository-identity/shell-gate families) —
consistent with this repository's long-documented pre-existing fast_green
debt, unrelated to and unchanged by this phase (this phase made zero
`src/pcae` changes, so this count cannot have moved). **R-only
unexplained functional failures: 0.**

## 21. Historical preservation

`git diff 83b7f70b HEAD -- docs/PHASE_..._30R_3_2_...SLICE_1.md` is empty
— the BLOCKED report is byte-unchanged; its `STATUS: BLOCKED.` verdict
stands, not reopened or reinterpreted.

## 22. Scope fence — confirmed absent/unchanged

No Slice 2 (`RHAMP-FIDO2-CREDENTIAL/1.0`, `RHAMP-COUNTER-STATE/1.0`,
enrollment, `FIDO2HumanAuthenticator`) — token scan of the full
`.1R.30R.3.2.1` production diff confirms none introduced.
`hpac_verifier.py` / Gate 5 / Gate 9 byte-unchanged since phase entry.
`_ELIGIBLE_MECHANISM_IDS` unwidened. No protected presentation. No
`require_real_assurance` wiring. Runtime independently re-confirmed:
`Observed` / `observe` / `unavailable`, 0 plugins, 0 capabilities. First
external effect remains ABSENT/UNREACHABLE. No N-16-6/N-16-7 work; N-16-7
stays strictly last. No Slice C. This IV changed zero `src/pcae`,
zero contract, zero existing test file.

## 23. Product verdicts

| Property | Verdict |
|---|---|
| Canonical issuance membership | **VERIFIED** |
| Non-bearer | **VERIFIED** |
| Object-instance binding | **VERIFIED** |
| One-operation | **VERIFIED** (with the non-blocking §11 disclosure — no authority bypass) |
| Concurrent use | **VERIFIED** |
| Scope binding | **VERIFIED** |
| Restart invalidation | **VERIFIED** |
| HumanPrincipalRegistryStore production consumption | **VERIFIED** |
| Consumer boundary | **VERIFIED** |
| Contract↔repair equivalence | **VERIFIED** |

## 24. Slice-1 final adjudication

**INDEPENDENTLY VERIFIED — N-16-5 PAWA PRODUCTION PROTECTED-ADMIN WRITER
ANCHOR SLICE 1 COMPLETE.**

- HPAC-PAWA-001 v1.1: **IMPLEMENTED + VERIFIED FOR SLICE 1**
- Canonical issuance integrity: **VERIFIED**
- Non-bearer (HPAC-PAWA-REQ-102): **VERIFIED**
- One-operation (HPAC-PAWA-REQ-106/107): **VERIFIED** (non-blocking
  disclosure at §11)
- Historical `.1R.30R.3.2`: **BLOCKED / PRESERVED**, immutable
- Repair `.1R.30R.3.2.1`: **VERIFIED**
- **Slice 1: CLOSED**
- Slice 2: **NOT BEGUN**
- **N-16-5: CLOSED**
- Runtime: `Observed` / `observe` / `unavailable`
- First external effect: **ABSENT**

## 25. Non-blocking finding (disclosed, not repaired)

**F-1 (this phase).** `record_write`'s registry-consumption mark occurs
after its own provenance write, which itself occurs after the actual
registry-document mutation in `HumanPrincipalRegistryStore._write`. If the
provenance write fails, the capability's own bookkeeping
(`_spent`/registry state) does not reflect the mutation that already
landed. **Empirically verified to grant no authority bypass** — every
subsequent read of the affected record fails closed (missing provenance),
blocking reuse — but it does wedge that record until manual repair. Class:
availability/operability, not security. Pre-existing, not introduced or
altered by `.1R.30R.3.2.1`. No repair performed inside this IV (per this
phase's own governance rules — verification only). Recommend a future
phase evaluate reordering the consumption mark to close the availability
window, if judged worthwhile relative to other priorities; does not block
N-16-5 closure.

## 26. Next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3` — N-16-5 RHAMP FIDO2 Credential
Registry, Counter-State, and Protected-Admin Enrollment Implementation
(Slice 2). ID recommended, **NOT reserved** — confirm under CPIPC before
use. Do not begin it here. Do not implement RHAMP credential/counter-state.
Do not implement enrollment. Do not implement `FIDO2HumanAuthenticator`.
Do not modify `hpac_verifier` for REAL authentication. Do not widen
`_ELIGIBLE_MECHANISM_IDS`. Do not implement protected presentation. Do not
wire `require_real_assurance` through Gate 5/9. Do not begin N-16-6 or
N-16-7 (N-16-7 strictly last). Do not begin Slice C. Do not implement or
call the first external effect. Do not enable execution.

## 27. N-16-6 / N-16-7 / N-23

Remain OPEN / untouched / carried unchanged, as before.

## 28. Governance incident (preserved)

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
Only the primary human-authorized operator holds `.1R.30R.3.2.1.1`
lifecycle authority. All governed commit/push/phase-completion actions for
this phase are performed directly by the primary human-authorized
operator, not by a delegated worker.
