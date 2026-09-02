# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1 — REPAIRED

**N-16-5 PAWA `HPACWriterCapability` Non-Bearer / One-Operation Integrity
Repair**

**STATUS: REPAIRED — INDEPENDENT VERIFICATION PENDING.** Repairs the
decisive product defect independently found and twice reproduced by
`.1R.30R.3.2` (Independent Verification, preserved **BLOCKED**, immutable,
not re-opened or re-verified by this phase). N-16-5 remains **NOT CLOSED**
— a fresh independent verification of this repair is required before Slice
1 can be considered IV-complete.

## 1. SHAs

- **A** (finalized `.1R.30R.3.1` head) = `aff46ec3` — "reconcile governed
  push state in Slice-1 completion metadata (pushed; origin/main..HEAD = 0)"
- **V** (finalized `.1R.30R.3.2` head, == this phase's entry) = `83b7f70b`
  — "reconcile governed push state in BLOCKED completion metadata (pushed;
  origin/main..HEAD = 0)"
- **R0** (`.1R.30R.3.2.1` phase-entry SHA) = `83b7f70b` (== V; `git status
  --branch --short` showed `main...origin/main` with a clean tree and
  `origin/main..HEAD = 0` at entry)

Derived independently from `git log --oneline` and `git rev-parse HEAD`, not
inherited from prose.

## 2. Primary sources read

- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_INDEPENDENT_VERIFICATION_OF_N_16_5_PAWA_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_SLICE_1.md`
  (the BLOCKED IV report) — read in full, §5 (decisive finding), §6
  (verdict), §7 (other confirmed items).
- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.1) §40–§49 (`HPACWriterCapability` class, issuance
  inputs, operation/principal/credential scope, process-local, non-bearer
  HPAC-PAWA-REQ-102, non-serializable HPAC-PAWA-REQ-103, restart
  invalidation, one-operation HPAC-PAWA-REQ-106/107/108) — read in full.
- Production source in full: `src/pcae/core/hpac_foundation.py` (the
  `HPACWriterCapability` class, `HPACStoreAuthority._new_capability` /
  `require_writer` / `record_write`), `src/pcae/core/hpac_protected_admin_writer.py`
  (`production_writer`, `ProductionWriterHandle.consume`, `_mint`-adjacent
  recognition sequence), `src/pcae/core/human_principal_registry.py`
  (`_writer`, `_write`, `enroll_principal`/`revoke_principal`).
- The existing fresh `.1R.30R.3.1` 95-test suite, read in full, including
  `test_54_direct_constructor_rejected`,
  `test_55_object_new_reconstruction_rejected`,
  `test_56_copy_does_not_create_a_second_usable_capability`,
  `test_59_restart_invalidation_fresh_seal`,
  `test_60_one_operation_replay_rejected_at_both_layers`.

## 3. Historical defect reproduction (before any edit)

Independently reproduced the exact adversary from `.1R.30R.3.2` §5.3
against the finalized `.1R.30R.3.1` head (`A = aff46ec3`), using a detached
`git worktree` at `A` (not this working tree):

1. Mint one legitimate `PRODUCTION` `HPACWriterCapability` via a fixture
   `HPACStoreAuthority`.
2. `authority.require_writer(cap, ...)` — accepted (legitimate use).
3. `forged = HPACWriterCapability.__new__(HPACWriterCapability)`; copy
   `forged._authority_seal = cap._authority_seal`, plus `role`, `subject`,
   `authority_class`, `_single_use = True`, `_spent = False`.
4. `authority.require_writer(forged, ...)` on `A` → **ACCEPTED** (defect
   reproduced, confirming the BLOCKED report independent of its own prose).

The identical script against the repaired working tree (`R`) → **REJECTED**
(`HPACAuthorityError: writer capability is absent, forged, or bound to
another HPAC root`).

End-to-end reproduction through the real `production_writer()` →
`HumanPrincipalRegistryStore` path (matching §5.3 exactly: legitimate
`enroll_principal`, then a forged-capability `revoke_principal`) on `R`:
the forged `revoke_principal` call raises `HumanPrincipalRegistryError`
wrapping the same `HPACAuthorityError`. The legitimate `enroll_principal`
still succeeds.

## 4. Root cause

`require_writer`'s only binding check
(`hpac_foundation.py`, pre-repair) was:

```python
if not isinstance(writer, HPACWriterCapability) or writer._authority_seal is not self._seal:
    raise HPACAuthorityError(...)
```

`_authority_seal` is a plain, readable `__slots__` instance attribute (no
`__setattr__` override, no cryptographic binding). `HPACWriterCapability.__new__`
bypasses `__init__`'s constructor-seal gate entirely. A caller that already
legitimately holds one issued capability — even an already-spent one — can
read `cap._authority_seal` (the literal `object()` the issuing authority
holds) and assign that same object reference to a `__new__`-constructed
shell. The identity check then genuinely passes: it really is the same
object, not a reconstruction of it. No amount of *additional* checking on
the capability object itself can close this, because any value stored on
the object is, by the same argument, readable and copyable onto a shell.

Classified: **security property — canonical-issuance-object identity —
cannot be represented as a value stored on the capability; it must be an
out-of-band, process-local fact the object cannot carry a copy of.**

## 5. HPAC-PAWA-REQ-102/103 analysis — contract-impact verdict: NO normative change

- **HPAC-PAWA-REQ-102** ("recognised by `require_writer`'s **identity**
  check ... not a value comparison") states a *security property*
  (canonical-factory-produced, recognised by identity) via one *example*
  mechanism (seal identity). The repair adds a **second** identity check
  (registry-object-identity) — still an identity check, still not a value
  comparison. The property REQ-102 describes is unchanged; the mechanism is
  strengthened, not replaced.
- **HPAC-PAWA-REQ-103** claims `object.__new__` + known field values "fails
  the seal-identity check". `.1R.30R.3.2` found this claim empirically false
  for an attacker who already holds a real seal reference. After this
  repair, the claim is **true again in practice**: an `object.__new__`
  reconstruction fails — now for the correct, sufficient reason (registry
  non-membership), not merely because the seal happens to be unset.
- **Verdict: no HPAC-PAWA-001 contract text is false after this repair; no
  normative version change is required.** `HPAC-PAWA-001` stays **v1.1,
  byte-unchanged**. `HPAC-001` v2.1, `RHAMP-001` v1.0, `HBDC-001` v1.2 stay
  byte-unchanged. `git diff 83b7f70b HEAD -- docs/contracts` is empty
  (verified in §9 below).

This resolves the BLOCKED report's own contract note ("closing the gap
likely needs a small HPAC-PAWA-001 amendment ... not a silent code-only
patch") by demonstrating a code-only patch that does not, in fact, leave
any contract text false or the security property unmet — it delivers
exactly the property REQ-102 already required, through a strengthened but
still-identity-based mechanism.

## 6. Target authority model (frozen for this repair)

A usable PRODUCTION `HPACWriterCapability` must satisfy, at `require_writer`:

1. `isinstance` + seal-identity match (unchanged, first gate);
2. canonical process-local issuance-registry **object membership** — the
   exact object, not a structurally identical one, was returned by the
   sole construction site and has not been evicted;
3. registry-bound scope match (`role`/`subject`/`authority_class` as
   recorded **at mint time**, not the capability's own — possibly
   attacker-mutated — mutable slots);
4. unspent/active lifecycle state, in the registry (authoritative) and on
   the object (`_spent`, defense in depth).

A readable object attribute, by itself, is insufficient for (2)-(4).

## 7. Process-local issuance registry (implementation)

`src/pcae/core/hpac_foundation.py`, new module-level state (not exported in
`__all__`):

- `_CapabilityIssuanceState` — closed `{ACTIVE, CONSUMED}`.
- `_CapabilityIssuanceRecord` — `capability` (strong reference), `issuance_id`
  (`secrets.token_bytes(32)`, non-authoritative, audit/debug only, never
  exposed on the capability or in any serialized projection), `role`,
  `subject`, `authority_class`, `state`.
- `_ISSUED_CAPABILITY_REGISTRY: dict[int, _CapabilityIssuanceRecord]` keyed
  by `id(capability)`, guarded by `_ISSUANCE_REGISTRY_LOCK`
  (`threading.Lock`).
- `_register_issued_capability(...)` — called only from
  `HPACStoreAuthority._new_capability` (the sole construction site,
  HPAC-PAWA-REQ-091/finding #6 of `.1R.30R.3.2`), immediately after mint.
- `_lookup_issued_capability(capability)` — returns the record only if
  `record.capability is capability` (object identity, not `==`), else
  `None`.
- `_mark_capability_consumed(capability)` — called from `record_write` at
  the exact point the object-local `_spent` flag was already being set,
  under `writer._single_use`.

A **strong reference** to the capability is kept for the life of each
entry (there is no explicit eviction), so `id()` can never be reassigned to
a different live object while the entry stands — the classic id-reuse
forgery this table would otherwise itself be vulnerable to. This is a
process-local, admin-tool-scale table (HPAC-PAWA-REQ-108: the enclosing
admin tool is short-lived, one operation per invocation); memory growth is
bounded by how many capabilities a single process mints, which for the
PRODUCTION path is exactly one per `production_writer()` call. It is never
serialized, never written to disk, and does not survive a process restart
(HPAC-PAWA-REQ-105) — a fresh process has an empty table, matching every
other PAWA process-local fact.

**Per-mint identity.** `issuance_id` (`secrets.token_bytes(32)`) is
generated per mint but is deliberately **not** stored on the capability
object and never exposed — a token *on the object* would be exactly as
copyable as `_authority_seal` was. The unforgeable fact is the registry
membership of the literal object, not any value.

**Object/issuance binding.** Membership is `record.capability is writer`
(Python's default identity-based `is`/hash on a class with no `__eq__`
override) — a separately constructed object, even with every field copied,
is never `is` the canonical object and is therefore never a member,
regardless of field content.

**Constructor-seal role preserved.** `_WRITER_CONSTRUCTOR_SEAL` still gates
`__init__` (direct construction remains rejected); its role is unchanged —
constructor gating only, never the decisive per-capability authority proof
(that role now belongs to registry membership).

## 8. `require_writer` hardening

```python
def require_writer(self, writer, role, *, subject=None):
    if not isinstance(writer, HPACWriterCapability):
        raise HPACAuthorityError(...)
    if getattr(writer, "_authority_seal", _MISSING) is not self._seal:
        raise HPACAuthorityError(...)
    record = _lookup_issued_capability(writer)
    if record is None:
        raise HPACAuthorityError(...)
    if record.role != role or record.subject != subject:
        raise HPACAuthorityError(...)
    if record.authority_class is not self.authority_class:
        raise HPACAuthorityError(...)
    if record.state is _CapabilityIssuanceState.CONSUMED or getattr(writer, "_spent", True):
        raise HPACAuthorityError(...)
    self._ensure_root(create=True)
```

- **`getattr(..., _MISSING)`** instead of direct attribute access: an
  unset-slot `object.__new__` shell now fails closed with a clean
  `HPACAuthorityError`, not a raw `AttributeError` (defense-in-depth;
  `test_55` incidentally "passed" pre-repair only because it caught the
  `AttributeError`, per `.1R.30R.3.2` §5.4 — this repair makes the
  rejection reason correct without relying on that accident).
- **Registry-bound scope dominates object fields**: `record.role` /
  `record.subject` (frozen at mint), not `writer.role` / `writer.subject`
  (plain mutable slots an attacker could otherwise reassign post-mint to
  widen scope — a related, narrower gap closed as a side effect).
- **Registry state is authoritative for spend**, with the object's
  `_spent` flag consulted too (defense in depth): a resettable `_spent`
  attribute alone can no longer un-spend a capability, since the registry
  copy is external state the capability object cannot reach.

## 9. Consumption / one-operation lifecycle

`record_write` marks both the existing object-local `_spent` flag (via
`_mark_spent`, seal-guarded, unchanged) and the registry state to
`CONSUMED`, at the same transition point — the successful atomic-replace
provenance write, exactly where `.1R.30R.3.1` already placed the spend
transition. No change to write-failure / validation-failure lifecycle
semantics (a failure before this point still leaves the capability
unspent in both places, matching pre-repair behaviour — this repair does
not alter that ordering, only adds a second, non-bypassable place the
"already consumed" fact is recorded).

**Concurrency.** `HumanPrincipalRegistryStore._write` already serializes
the actual mutation via `writer_transaction`'s exclusive `fcntl` lock and a
compare-and-swap on the loaded registry document (`expected_current`); a
losing concurrent caller sees `HumanPrincipalRegistryConflictError` from
that pre-existing mechanism, independent of this repair. A fresh
4-thread-race test (`test_17`, dedicated suite) confirms exactly one of
four concurrent `revoke_principal` calls against the same capability
succeeds.

## 10. Results by category

| Item | Result |
|---|---|
| Canonical issuance | succeeds unchanged |
| Non-issued `object.__new__` shell (bare) | rejected — clean `HPACAuthorityError` |
| Non-issued shell with copied real seal (decisive adversary) | **rejected** — was accepted pre-repair |
| Direct constructor | rejected (unchanged, `_WRITER_CONSTRUCTOR_SEAL`) |
| `copy.copy` / `copy.deepcopy` | rejected (unchanged, `__reduce__` raises `TypeError`) |
| `pickle` | rejected (unchanged) |
| Restart (fresh authority instance) | rejected (fresh `_seal` **and** empty registry) |
| One-operation replay | rejected (`capability_stale` at factory layer; registry+object state at foundation layer) |
| Concurrent use (4 threads, 1 capability) | exactly 1 success |
| Token/scope transplant (copied seal, different subject) | rejected |
| Registry-bound scope vs. mutated object field | registry value dominates; mutated field alone does not widen scope |
| Fixture capability vs. PRODUCTION registry write | rejected (`authority_class` mismatch, unaffected by this repair) |
| Issuance evidence / audit projection | unchanged; still non-authoritative, still excludes the seal; the new `issuance_id` is never written to any evidence document |
| `FIXTURE_NON_REAL` / PRODUCTION separation | unchanged; both classes registered uniformly (single construction site), `authority_class` check still gates cross-class use |
| Sole construction site | unchanged — one call site (`_new_capability`) |
| Non-agent-importable boundary | unchanged — no new import into `cli.py` / `commands/**` / `core/agent.py` |
| Slice 2 / FIDO2 / RHAMP sidecar | absent (verified by token scan) |
| `hpac_verifier.py` / Gate 5 / Gate 9 | byte-unchanged (`git diff 83b7f70b HEAD` empty) |
| `_ELIGIBLE_MECHANISM_IDS` | unwidened |
| Runtime | `Observed` / `observe` / `unavailable`, 0 plugins / 0 capabilities |
| First external effect | ABSENT / UNREACHABLE |

## 11. Production diff scope

`src/pcae/core/hpac_foundation.py` only:

- imports: `+secrets`, `+threading`;
- new module-level: `_CapabilityIssuanceState`, `_MISSING`,
  `_CapabilityIssuanceRecord`, `_ISSUANCE_REGISTRY_LOCK`,
  `_ISSUED_CAPABILITY_REGISTRY`, `_register_issued_capability`,
  `_lookup_issued_capability`, `_mark_capability_consumed`;
- `HPACStoreAuthority._new_capability` — registers the minted capability;
- `HPACStoreAuthority.require_writer` — hardened per §8;
- `HPACStoreAuthority.record_write` — marks the registry entry consumed
  alongside the existing `_mark_spent` call.

No other production file touched. `HPACWriterCapability`'s `__slots__` is
byte-unchanged (still exactly `("_authority_seal", "role", "subject",
"authority_class", "_single_use", "_spent")`).

## 12. Tests

- **Existing product suite** (`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py`):
  95 pre-existing tests kept unedited (0 removed/renamed/skipped/xfailed);
  4 new tests added directly after `test_55`
  (`test_55a_nonissued_capability_shell_is_rejected`,
  `test_55b_writer_authority_requires_canonical_issuance_membership`,
  `test_55c_one_operation_capability_cannot_be_duplicated_via_field_copy`,
  `test_55d_registry_bound_scope_dominates_mutated_object_fields`) — the
  exact missing adversary regression `.1R.30R.3.2` §6 asked for, added to
  the *product* suite, not only a repair-phase meta-suite. **99 passed, 0
  failed.**
- **Dedicated repair suite**
  (`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_pawa_writer_capability_integrity_repair.py`,
  new file, 24 tests): historical-preservation, decisive-adversary
  (direct + end-to-end), canonical-issuance-still-works, bare-shell,
  direct-constructor, copy/deepcopy/pickle, restart, one-operation replay
  (factory + foundation layer), token/scope transplant, wrong-role,
  fixture-vs-production, concurrent-use, sole-construction-site,
  registry-helper-not-exported, issuance-id-never-on-object, no-Slice-2,
  hpac_verifier/contract byte-identity, runtime-unchanged. **24 passed, 0
  failed.**
- **`.1R.30R.1` adjudication IV suite**
  (`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py`):
  `test_require_writer_uses_identity_check_on_seal` updated — additively —
  to also require the new registry-membership hardening text is present,
  since its old exact-substring assertion (`"writer._authority_seal is not
  self._seal"`) no longer matches the `getattr`-wrapped form. This is the
  **only** existing test anywhere in the repository whose assertion text
  needed to change; it now asserts strictly more than before.

## 13. Fixed-SHA attribution

`A` = finalized `.1R.30R.3.1` head (`aff46ec3`); `R` = this working tree.
Ran the full HPAC-touching test surface (36 files) against both:

- **On `A`** (repair stashed out): the same 39 tests fail as on `R`, byte
  identical failure text, except `test_require_writer_uses_identity_check_on_seal`
  (passes on `A`'s original text, updated on `R` to match the repair —
  expected, not a regression) and the two working-tree-diff hygiene guards
  (pass on `A`'s clean stash-restored tree, fail on `R`'s intentionally
  uncommitted diff — clear on commit).
- **`R`-only unexplained functional failures: 0.**
- One additional test
  (`test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::test_concurrent_conflicting_successors_have_one_canonical_winner`)
  was observed to fail once and pass twice across three consecutive runs
  of the **unmodified** repository (a `tmp`-file race in an unrelated
  module, `hpac_lifecycle.py`) — a pre-existing flake, not
  repair-attributable, confirmed independent of this repair by re-running
  identically on `A`.

Full HPAC-touching surface with the repair present: **1613 passed, 39
failed (all pre-existing/hygiene, classified above), 3 skipped.**

## 14. Guard reconciliation

- `.1R.30R.1` IV suite: `test_require_writer_uses_identity_check_on_seal`
  updated per §12.
- No other point-in-time production-file-scope guard names
  `hpac_foundation.py` in a *closed* per-phase allowlist that this repair's
  hunk falls outside of — the file was already an authorized member of the
  five/six-file PAWA production set from `.1R.30R.3.1` onward; guards that
  reference the accumulated PAWA file set required no further widening.
  Two unrelated older-phase guards
  (`test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py::test_widened_guard_module_passes_at_head[...]`,
  `test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py::test_no_working_tree_production_or_contract_diff`)
  assert a **clean working tree** (`git diff HEAD`), not a historical
  baseline allowlist — they fail only while this repair's commit is
  pending and clear on commit, by construction, for any production change.

## 15. No-test-weakening confirmation

`git diff -- tests/` (three touched files): 104 insertions, 1 deletion (the
one updated assertion line in §12, itself widened). No `def test_` line
removed or renamed; no `skip` / `skipif` / `xfail` / `pytest.skip` added;
no wildcard/fnmatch broadening. Independently confirmed via
`git diff --stat` and a targeted grep of the diff for `^-def test_` /
added `skip`/`xfail` tokens — none found.

## 16. Contract byte identity

`git diff 83b7f70b HEAD -- docs/contracts` — empty. `HPAC-PAWA-001` v1.1,
`HPAC-001` v2.1, `RHAMP-001` v1.0, `HBDC-001` v1.2 byte-unchanged.

## 17. Scope fence — confirmed absent/unchanged

No Slice 2 (`RHAMP-FIDO2-CREDENTIAL/1.0`, `RHAMP-COUNTER-STATE/1.0`,
enrollment ceremony, `FIDO2HumanAuthenticator`). No `hpac_verifier.py`
change (`git diff 83b7f70b HEAD -- src/pcae/core/hpac_verifier.py`
empty). `_ELIGIBLE_MECHANISM_IDS` unwidened. No protected presentation, no
`require_real_assurance` wiring through Gate 5 / Gate 9 (both byte-unchanged).
No N-16-6 / N-16-7 work; N-16-7 stays strictly last. No Slice C. The first
external effect remains ABSENT AND UNREACHABLE. Runtime remains
`not_implemented` / `Observed` / `observe` / `unavailable`, 0 plugins / 0
capabilities. No execution enabled.

## 18. Historical `.1R.30R.3.2` preservation

`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_INDEPENDENT_VERIFICATION_OF_N_16_5_PAWA_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_SLICE_1.md`
is byte-unchanged by this phase (`git diff 83b7f70b HEAD -- docs/PHASE_..._30R_3_2_...md`
empty). Its `STATUS: BLOCKED.` verdict and `N-16-5 remains **NOT CLOSED**`
conclusion are not rewritten. This repair phase supersedes only the
underlying product defect it found; it does not re-verify or re-open
`.1R.30R.3.2` itself.

## 19. Repair provenance

```
.1R.30R.3.1  Slice-1 implementation (IMPLEMENTED, IV not closed)
     |
.1R.30R.3.2  Independent Verification -- found capability-integrity defect
             (BLOCKED, preserved, immutable)
     |
.1R.30R.3.2.1  this phase -- narrow integrity repair (REPAIRED, IV PENDING)
     |
.1R.30R.3.2.1.1  (recommended, not reserved) -- fresh independent
                 verification of this repair
```

## 20. Verdict

- HPACWriterCapability canonical issuance integrity: **REPAIRED — IV
  PENDING**
- NON-BEARER semantics (HPAC-PAWA-REQ-102): **REPAIRED — IV PENDING**
- ONE-OPERATION semantics (HPAC-PAWA-REQ-106/107): **REPAIRED — IV
  PENDING**
- Historical `.1R.30R.3.2`: **BLOCKED / PRESERVED**
- Slice 1: **IMPLEMENTED WITH REPAIR — FRESH SUCCESSOR IV REQUIRED — NOT
  CLOSED**
- **N-16-5: NOT CLOSED**
- Runtime: Observed / observe / unavailable
- First effect: ABSENT
- N-16-6 / N-16-7: OPEN, untouched, N-16-7 strictly last
- N-23-1 / N-23-2: carried unchanged

## 21. Governance incident (preserved)

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved. Only
the primary human-authorized operator holds `.1R.30R.3.2.1` lifecycle
authority. Governed commit/push/phase-completion for this phase are
performed directly by the primary human-authorized operator, not by a
delegated worker.

## 22. Next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1.1` — a fresh independent
verification of this repair (ID **recommended, NOT reserved** — confirm
under CPIPC before use), extending this repair's own lineage the same way
`.3.2` → `.3.2.1` did, rather than a sibling branch off `.3.1` or a
re-opening of `.3.2`. Do not begin it here. Do not begin Slice 2. Do not
implement RHAMP credential sidecars, RHAMP counter-state, credential
enrollment, or `FIDO2HumanAuthenticator`. Do not modify `hpac_verifier` for
REAL authentication. Do not widen `_ELIGIBLE_MECHANISM_IDS`. Do not
implement protected presentation. Do not wire `require_real_assurance`
through Gate 5/9. Do not begin N-16-6 or N-16-7. Do not begin Slice C. Do
not implement or call the first external effect. Do not enable execution.
