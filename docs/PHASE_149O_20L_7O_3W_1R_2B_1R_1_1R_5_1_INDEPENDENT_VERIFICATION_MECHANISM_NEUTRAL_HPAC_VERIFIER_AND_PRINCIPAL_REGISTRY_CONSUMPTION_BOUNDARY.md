# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.1 — Independent Verification of Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption Boundary Implementation

## 1. Identity

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.5.1`
- **Verifies:** `149O.20L.7O.3W.1R.2B.1R.1.1R.5` (mechanism-neutral HPAC verifier and principal-registry consumption boundary implementation)
- **Verification-entry commit (HEAD at start):** `1df9c855` (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5: finalize pushed metadata`)
- **Baseline (pre-`.1R.5`):** `817b788a` (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.4: finalize pushed metadata`)
- **`.1R.5` implementation range (from the canonical report, independently re-derived below):**
  `d502fc5c`, `accf6273`, `319a64f0`, `2883315a`

## 2. Commit-range reconstruction (§5)

Independently inspected with `git show --stat --summary` / `git show --name-status --format=fuller` for each SHA (not trusted from the report's commit-subject text alone):

| Commit | Nature | Files |
|---|---|---|
| `d502fc5c` | **Implementation-bearing.** Sole commit creating `src/pcae/core/hpac_verifier.py` (432 lines, new) and `tests/test_hpac_verifier.py` (543 lines, new), plus the `.1R.5` implementation doc, plus three small edits to earlier `.1R.3.1`/`.1R.3.2`/`.1R.3.2.1` test files (7-10 line diffs — need independent check, see §2.1 below). | 6 files, +1496/-3 |
| `accf6273` | Documentation/lifecycle-only. `PROJECT_STATUS.md` + `CHANGELOG.md` sync. | 2 files, +57/-3 |
| `319a64f0` | Lifecycle/finalization-only. Task transition to idle (`tasks/DONE.md`, task contract files). | 4 files, +171 |
| `2883315a` | Lifecycle/finalization-only. Removes the now-stale prior idle-task file. | 1 file, -87 |

Only `d502fc5c` carries implementation weight. This matches the report's own characterization ("Files changed: 12" — 6+2+4+1 = 13 counting adds/deletes across all four commits, close enough given the report counts distinct paths, not per-commit files; not independently reconcilable to the exact figure but not materially misleading).

### 2.1 Independent check of `d502fc5c`'s test-file edits to earlier phases

`d502fc5c` touches three test files from already-verified prior phases (`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`, `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`, `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`) with small diffs (7-10 lines each). These are **not** re-litigated here in full (out of this phase's scope — those phases are independently verified and closed), but their presence inside the otherwise-clean `.1R.5` implementation commit is noted as an OBSERVATION: a "pure new module" implementation commit also lightly touching three unrelated prior-phase test files is a minor scope-hygiene note, not a functional finding — `git show d502fc5c -- <those paths>` shows only import-path/fixture-signature adjustments, not behavioral changes to already-frozen foundation code.

## 3. Contracts and plans read (§3)

Read in full, independently, before comparing to `.1R.5`'s implementation or its own prose:

- `PROJECT_STATUS.md`
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_4_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY_IMPLEMENTATION_PLANNING.md` (`.1R.4` planning)
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY_IMPLEMENTATION.md` (`.1R.5` implementation doc)
- `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (**HPAC-001 v2.0**, read in full — this is the primary normative source for §6/§41 below)
- `src/pcae/core/hpac_verifier.py` (implementation, read in full)
- `src/pcae/core/hpac_foundation.py`, `src/pcae/core/hpac_lifecycle.py` (consumed foundation, read for API shape)
- `tests/test_hpac_verifier.py` (the 27 existing `.1R.5` tests, read in full and classified — §9 below)

**Not independently re-read in full this phase** (explicit limitation, not a gap treated as verified): RIHAC-001 v2.0, RIASC-001 v3.0, PBRD-001 v2.0, RDGO-001 v3.0, RPAC-001 v1.0, POL-005, and the `.3.2.2.1`/`.3.2.2`/`.3.2.1`/`.3.2`/`.3.1` foundation-layer verification/repair docs, and the original `.1R.2` planning. HPAC-001 v2.0 is the contract this module directly implements and was read in full; the others govern layers this module explicitly does not touch (PB, RIHAC approval validity, RIASC wire shape, RDGO gate sequencing, RPAC provider neutrality) and this module's own zero-consumption of them is independently confirmed structurally (§7 below) rather than by re-deriving their full text. This is disclosed as a scope-boundary limitation of this verification pass, not asserted as full compliance with those contracts.

## 4. Independently-derived HPAC-REQ-054 sequence (§6)

Extracted directly from `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` §18 **before** re-reading `hpac_verifier.py`'s implementation in detail a second time:

1. Resolve `principal_id` in `HumanPrincipalRegistry`; reject if missing or not `active`.
2. Resolve `credential_id` under that principal; reject if missing, not bound to this `principal_id`, or not `active`.
3. Resolve `mechanism_id`; reject if unknown or below the minimum required assurance level (§20).
4. Recompute `challenge_digest` from the exact challenge state and compare; reject on mismatch.
5. Verify subject and informed-intent binding: challenge's canonical subject digest equals the approval subject/scope/expiry, and `trusted_presentation_ref` resolves by §39's canonical path/schema to evidence whose mechanism descriptor and attestation prove the identical canonical facts were displayed through a non-substitutable channel; reject lookalikes, ordinary stdout/stdin, missing election, blind touch, or display/challenge mismatch.
6. Verify `assertion` against the resolved credential's public verification material; reject on signature/assertion failure.
7. Verify both UP and UV are `true` for real-runtime authority; reject UP-only, UV-only, or downgrade.
8. Verify freshness: `authenticated_at` recent relative to trusted clock, challenge not expired; reject if stale.
9. Resolve §40's complete hash-chained lifecycle and §41's canonical consumption path; verify state is fresh or already `PROOF_VERIFIED_AND_BOUND` to this exact same binding; reject cross-binding, expired/revoked, or replay.
10. Atomically create §40's `PROOF_VERIFIED_AND_BOUND` event (or accept an already-present byte-identical same-binding event idempotently) and emit an ephemeral immutable `AuthenticatedHumanPrincipal`.

**This is 10 numbered normative steps**, each mandatory (HPAC-REQ-055: "No later step runs as a shortcut when an earlier step fails").

### 4.1 A pre-existing mis-derivation in `.1R.4`'s own planning document

The `.1R.4` planning document's §7 ("Verifier responsibilities") states: *"HPAC-REQ-054's **eight-step** algorithm..."* and *"No step is a shortcut. **All eight** are the verifier's responsibility"* (planning doc §7, §12). This is factually wrong on its face: HPAC-001 v2.0 §18 defines **ten** numbered steps, not eight. Comparing the planning doc's own 8-item list against the contract's 10 steps shows the planning doc's list **silently drops contract step 4** ("recompute `challenge_digest` from the exact challenge state and compare") entirely — it is not present under any other numbered item, and the planning doc's item 4 ("Verify the assertion against the resolved credential's public key") is contract step 6, with contract step 3 (mechanism resolution/assurance-level check) folded into the same planning item without being named.

This matters because `.1R.5`'s implementation (and its own doc/tests) inherited the planning doc's 8-step framing, and the `.1R.5` phase report's claim — *"Implemented the standalone mechanism-neutral HPAC verifier ... per the .1R.4 planning document's frozen scope: HPAC-REQ-054's **ten**-step verification sequence"* — is not accurate to what was actually planned or built: the thing that was built faithfully implements the **planning document's own (silently incomplete, 8-item) re-derivation**, not the contract's actual 10-step text. See §6 below for the concrete consequence.

## 5. Step-by-step implementation comparison

| HPAC-REQ-054 step | `hpac_verifier.py` location | Adjudication |
|---|---|---|
| (prerequisite) resolve proof by `proof_id` | `proof_store.resolve_canonical(proof_id)`, line ~302 | Not a numbered contract step but a necessary precondition to have any `principal_id`/`credential_id`/etc. to resolve; canonical-resolution-only, no caller object accepted. OK. |
| 1. principal active | `_resolve_principal`, called line 310 | Implemented; canonical-resolution-only. **VERIFIED.** |
| 2. credential active + bound to claimed principal | `_resolve_credential`, called line 311 | Implemented; canonical-resolution-only. **VERIFIED.** |
| 3. mechanism known / min assurance | Folded into `_verify_assertion_material` (mechanism-ID equality + allowlist membership check only) | **Partially implemented.** Mechanism *identity* is checked (credential.mechanism_id == proof.mechanism_id, and must be in the single-member eligible set). No **assurance-level** comparison exists because HPAC-REQ-059's three-level vocabulary (`ASSERTED`/`CREDENTIAL_PRESENCE`/`PRINCIPAL_VERIFIED_INTENT`) is not modeled anywhere in the foundation yet — only the orthogonal `authority_class` (`FIXTURE_NON_REAL`/`PRODUCTION`) axis exists, which the verifier does check (`_authority_class_of`, `require_real_assurance`). Given only one mechanism is ever eligible in this phase, an assurance-level *comparison* is currently vacuous by construction. **NON-BLOCKING** (structural deferral, consistent with `.1R.4` §13's explicit choice to reuse `authority_class` rather than implement HPAC-REQ-059's vocabulary — but this should be named explicitly as a deferred requirement in a future phase, not silently absent). |
| 4. recompute `challenge_digest` from canonical challenge state | **Not implemented as an independent recomputation.** The verifier never re-derives a challenge digest from raw challenge bytes (domain separator, nonce, `issued_at`/`expires_at`, etc. per HPAC-REQ-049). It only cross-checks `proof.challenge_digest` against the lifecycle genesis event's recorded `binding["challenge_digest"]` for **string equality**, deferred to step 9's block (lines 372-383). | **NOT INDEPENDENTLY VERIFIED.** See §6 below — this is a genuine gap, though its exploitability is bounded by the fact that no standalone canonical `Challenge` store exists in the foundation (Challenge is explicitly ephemeral per HPAC-REQ-049/the module's own comment), so a literal "recompute from exact challenge state" may not even be architecturally implementable yet without a new canonical store this phase was not authorized to add. Classified **NON-BLOCKING given current foundation state**, but the `.1R.5` report's claim to have implemented "the ten-step verification sequence" is not accurate given this — see §4.1. |
| 5. subject/presentation binding | `presentation_store.resolve_canonical(...)`, `approval_id`/`approval_subject_digest` cross-checks, lines 323-341 | Implemented; canonical-resolution-only, rejects caller-created lookalikes structurally (resolution itself would fail — see foundation layer, verified `.1R.3.1`/`.1R.3.2.2.1`). **VERIFIED** (within this module's boundary — presentation-evidence integrity itself is the already-verified foundation's job). |
| 6. assertion vs. credential public material | `_verify_assertion_material`, lines 203-231 | Implemented as a **fail-closed allowlist rejection** (no real cryptographic verification exists in this phase, by design — `.1R.4` §8 explicitly excludes real FIDO2). Matches the frozen non-goal. **VERIFIED against the (deliberately deferred) frozen scope.** |
| 7. UP and UV both true | `_check_up_uv`, lines 234-249 | Implemented as two independently-checked booleans, not a folded flag. **VERIFIED** — see §7 below for the independence test matrix. |
| 8. freshness | Lines 352-356 (`authenticated_at > now`, `expires_at < now`) | Implemented. **VERIFIED.** |
| 9. lifecycle/consumption-path resolution | Lines 363-403 | Implemented via `lifecycle_store.resolve_canonical_chain`, genesis-binding cross-check against every claimed identifier, current-state branch (`PROOF_VERIFIED_AND_BOUND` idempotent-revalidate vs `PROOF_VERIFIED` advance vs anything else rejected). **VERIFIED** — see §8 below; this is also where contract step 4's *comparison* half is folded in (see above), just not its *recomputation* half. |
| 10. atomic create / idempotent accept + emit result | Lines 393-399 (`bind_gate5_canonical`) and 421-432 (`AuthenticatedHumanPrincipal` construction) | Lifecycle-write half implemented correctly (delegates to `hpac_lifecycle.py`'s own already-verified atomic writer, does not reimplement). Result-construction half has a **BLOCKING** trust-boundary defect — see §10. |

## 6. HPAC-REQ-054 adjudication

**NOT VERIFIED**, for two independent reasons of different severity:

- Step 3's assurance-level half and step 4's independent-recomputation half are not implemented (NON-BLOCKING given the foundation's current architecture — no canonical Challenge store and no assurance-level vocabulary exist yet to check against — but this is a real gap between the contract text and what was built, inherited from `.1R.4`'s own incomplete "eight-step" re-derivation, §4.1).
- The `.1R.5` phase report's and implementation doc's claim to have implemented "**HPAC-REQ-054's ten-step verification sequence**" is not accurate; what was independently re-derived and built is closer to 8-9 of the 10 steps, with step 4 not independently implemented at all. This is exactly the class of overclaiming §1/§40 of the governing phase prompt asks this verification to catch, not accept on the strength of the module's own docstring/report prose.

This finding does not, by itself, demonstrate a currently-exploitable authority bypass (see the bounding discussion above), but it means HPAC-REQ-054 as literally written is **not** fully and accurately represented as closed by this implementation.

## 7. UP/UV independence test matrix (§16)

Verified via the fresh suite (`test_up_false_uv_true_rejected`, `test_uv_false_up_true_rejected`) plus reading `_check_up_uv`'s unconditional `proof.up is not True or proof.uv is not True` check:

| UP | UV | Result |
|---|---|---|
| false | false | Rejected (upstream proof-store validation already forecloses this; independently re-checked at the verifier's own step 7 regardless) |
| true | false | Rejected — `test_uv_false_up_true_rejected` PASSED |
| false | true | Rejected — `test_up_false_uv_true_rejected` PASSED (after a test-authoring bug in this phase's own draft was fixed; the underlying proof-store immutability itself independently forecloses constructing such a proof, which is itself confirmatory evidence of defense-in-depth) |
| true | true | Succeeds (subject to every other step) |

**UP/UV: VERIFIED** — both checked as genuinely independent booleans, not folded into one flag, matching HPAC-REQ-042/HPAC-REQ-054 step 7 exactly.

## 8. Lifecycle / replay / anti-transfer (§13, §21)

Independently tested (fresh suite): orphan `proof_id` with no lifecycle chain → rejected; idempotent re-verification of an already-`PROOF_VERIFIED_AND_BOUND` binding → succeeds and returns a fresh ephemeral instance each time (not a cached/shared object); a second verification attempt against the same proof but a *different* `approval_id` after binding → rejected (cross-binding); a proof produced under invocation A's subject presented against invocation B's `approval_id` → rejected (HPAC-REQ-072 anti-transfer).

**Anti-transfer / invocation binding: VERIFIED.**

## 9. Canonical-input-resolution and principal/credential/presentation/proof consumption (§8-§12, §14-§16)

Every authority-bearing input the verifier's public function accepts is a bare string/opaque ID (`proof_id`, `approval_id`) plus canonical *store* objects (`registry`, `presentation_store`, `descriptor_store`, `proof_store`, `lifecycle_store`) — never a caller-constructed record. Confirmed by:

- Reading the full parameter list of `verify_human_authentication` (no `PrincipalRecord`/`CredentialRecord`/proof-dict/presentation-dict parameter exists).
- `test_caller_supplied_principal_record_cannot_substitute_for_registry` (fresh suite): structural signature check.
- Splicing forged proof documents at the raw-store level (`test_unknown_principal_id_in_proof_rejected`, `test_credential_bound_to_another_principal_rejected`, `test_mechanism_id_substitution_between_credential_and_proof_rejected`, `test_unsupported_mechanism_never_verifies_even_if_otherwise_well_formed`) — all four rejected as expected, at the specific step each name claims.
- `test_revoked_principal_rejected` / `test_revoked_credential_rejected` — both reject even against an otherwise fully valid chain.
- `test_presentation_bound_to_different_approval_id_rejected` — presentation/approval substitution rejected.

**Canonical principal consumption: VERIFIED.**
**Canonical proof/presentation/lifecycle consumption: VERIFIED** (modulo the challenge-digest recomputation gap in §6, which lives at the lifecycle-cross-check boundary specifically, not the presentation/proof boundary).

## 10. `AuthenticatedHumanPrincipal` construction/provenance analysis — BLOCKING FINDING

### 10.1 What the implementation does correctly

- `__init__` requires `_seal is _VERIFIER_CONSTRUCTOR_SEAL`, an unexported module-private `object()` sentinel; direct construction with any other seal value raises. **Confirmed** (`test_direct_construction_with_wrong_seal_rejected` — this mirrors the existing `.1R.5` test, independently re-confirmed).
- `__reduce__` unconditionally raises `TypeError`, closing `pickle.dumps` and `copy.deepcopy` (which uses `__reduce_ex__`/`__reduce__` when no `__deepcopy__` is defined). **Independently confirmed**, including `copy.copy` (shallow), which the existing `.1R.5` suite did not test — the fresh suite added `test_verifier_result_cannot_be_shallow_copied` and confirmed it also raises `TypeError`.
- `__eq__`/`__hash__` are identity-only (`self is other` / `id(self)`), so a field-cloned lookalike is never `==` to a genuine result even when every visible attribute matches — confirmed by `test_verifier_result_attribute_copy_produces_a_distinguishable_object` (fresh test, goes further than the existing suite's `test_copied_verifier_result_is_not_equal_to_a_fresh_one`, which only compared two independently-obtained *legitimate* results, not a deliberately field-cloned forgery).
- Zero downstream production consumers exist (§12 below), so there is currently no live code path a forged instance could reach.

### 10.2 The defect: `object.__new__` bypasses the seal entirely

`AuthenticatedHumanPrincipal` declares `__slots__` but **no `__new__` override**. In Python, `object.__new__(cls)` allocates a bare instance of `cls` without invoking `cls.__init__` at all. Because the trusted-construction check (`_seal is not _VERIFIER_CONSTRUCTOR_SEAL: raise`) lives **only inside `__init__`**, it is never reached by this path. Independently demonstrated (both by direct interactive probing before writing the fresh suite, and by the fresh suite's own failing tests):

```python
forged = object.__new__(AuthenticatedHumanPrincipal)
forged.principal_id = "forged-principal"
...
forged.assurance_class = HPACAuthorityClass.PRODUCTION
forged.verified_at = NOW
forged._verifier_seal = object()

isinstance(forged, AuthenticatedHumanPrincipal)   # True
forged.is_real_runtime_eligible                    # True
```

The forged object is a genuine, fully-functional instance of the class — `isinstance`-true, every `__slots__` attribute populated including `assurance_class`, and its `is_real_runtime_eligible` property (the exact property `.1R.4`'s planning doc §13 says is meant to structurally distinguish "deterministic verification success" from "real human authentication") reports `True` for a value that never went through `verify_human_authentication` at all.

**This directly contradicts HPAC-REQ-056**: *"`AuthenticatedHumanPrincipal` ... SHALL be producible only as the return value of a successful §18 verification sequence, never by direct construction from caller-supplied strings or dicts."* `object.__new__` plus attribute assignment is exactly "direct construction from caller-supplied strings" under a different Python mechanism than `__init__` — the contract's prohibition is stated in terms of the *outcome* (producible only as verification's return value), not scoped to one specific Python code path, and the outcome is violated.

### 10.3 Test evidence

Two fresh tests assert the contract-required behavior and **FAIL** against current `HEAD` (`d502fc5c`/current `hpac_verifier.py`), which is the correct and intended way for an independent-verification suite to surface a real defect rather than silently adapting the assertion to match the implementation:

```
FAILED tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py::test_object_dunder_new_bypasses_trusted_construction_seal
FAILED tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py::test_forged_via_object_new_would_report_real_runtime_eligible
```

### 10.4 Why the existing `.1R.5` suite did not catch this

`tests/test_hpac_verifier.py::test_caller_constructed_verifier_result_rejected` (the only existing test aimed at this exact boundary) exercises only the direct-`__init__`-with-wrong-seal path. It never attempts `object.__new__`, `copy.copy` on a *forged* (not legitimately-obtained) instance, or any allocation path that bypasses `__init__`. The test's name ("caller constructed verifier result rejected") is broader than what it actually proves — a case of a test name overclaiming a stronger guarantee than its body demonstrates (exactly the failure mode §33 of the governing prompt asks this phase to look for).

### 10.5 Adjudication

**`AuthenticatedHumanPrincipal` provenance: NOT VERIFIED — BLOCKING.** The trusted-construction boundary (HPAC-REQ-056) is not closed against `object.__new__`-based forgery. Severity is currently bounded by zero production consumers (§12) — nothing today can be tricked into accepting a forged instance — but the type itself does not honestly enforce the guarantee its own docstring and the contract claim it enforces, and this is exactly the highest-risk surface the governing prompt (§18-19) asked this phase to stress hardest.

## 11. Deterministic NON-REAL assurance (§17)

`test_full_valid_chain_succeeds_and_is_non_real_assurance` (fresh): a fully valid deterministic chain (UP=true, UV=true, matching principal/credential/challenge/invocation/presentation/lifecycle) succeeds and classifies as `HPACAuthorityClass.FIXTURE_NON_REAL`, with `is_real_runtime_eligible is False`. `test_deterministic_assurance_upgrade_attempt_rejected_via_require_real_assurance` (fresh): the same fully-valid chain is rejected when `require_real_assurance=True` is passed, confirming no caller-driven upgrade path exists via that flag. No other publicly-writable field on the verifier's inputs can alter the emitted `assurance_class` — it is copied from `_authority_class_of(...)` over the *resolved* records, never caller-declared.

**Deterministic NON-REAL assurance: VERIFIED.**

## 12. Production consumer / PB / Gate-9 / runtime isolation (§14-15, §24-29)

- `test_hpac_verifier_module_has_zero_production_consumers` (fresh, AST-based, scans all of `src/pcae` excluding the module itself for any `import`/`from ... import` referencing `hpac_verifier`) — **zero matches.** Confirmed independently outside the test suite too: `grep -rn "hpac_verifier\|AuthenticatedHumanPrincipal\|verify_human_authentication" src/pcae` finds exactly one hit outside the module itself, a **comment** in `human_authenticator.py` ("into a trusted `AuthenticatedHumanPrincipal`") — not an import, not a call.
- `test_hpac_verifier_module_never_imports_pb_runtime_authority_or_gate9` (fresh, AST-based) — no import of `permission_broker`, `runtime_dispatch_permission`, `runtime_authority`, `runtime_invocation_authority_consumption`, or `runtime_invocation_approval_store` anywhere in `hpac_verifier.py`. Confirmed.
- `grep -n "runtime_invocation_authority_consumption\|consumption.json\|dispatch_attempted" src/pcae/core/hpac_verifier.py` — the only hits are in the module's own **docstring**, explicitly disclaiming that it touches Gate 9.
- `grep -ni "fido2\|webauthn\|ctap" src/pcae/core/hpac_verifier.py` — only in comments explaining what is deliberately *not* implemented.
- `git log --oneline 817b788a..HEAD -- src/pcae/core/runtime_authority.py src/pcae/core/runtime_dispatch_permission.py src/pcae/core/runtime_invocation_approval_store.py` — **empty**; none of these three files were touched between the `.1R.4` baseline and current `HEAD`.

**PB isolation: VERIFIED. Runtime-authority isolation: VERIFIED. Gate-9 isolation: VERIFIED. Zero production consumers: VERIFIED. No real FIDO2/WebAuthn/CTAP: VERIFIED. B1/B7/N1/N2 files untouched: VERIFIED (contract status — whether B1/B7/N1/N2 *contracts* are closed is out of this module's scope and unaffected either way).**

## 13. `.1R.5`'s existing 27 tests — classification (§33)

| Test | Class | Note |
|---|---|---|
| `test_canonical_valid_deterministic_verification_succeeds_at_non_real_assurance` | normative trust test | Sound |
| `test_deterministic_success_remains_non_real_even_with_up_and_uv_true` | normative trust test | Sound |
| `test_idempotent_same_binding_reverification_succeeds` | normative trust test | Sound |
| `test_unknown_proof_id_rejected` | normative trust test | Sound |
| `test_malformed_proof_id_rejected` | structural/model test | Sound, narrow |
| `test_revoked_principal_rejected` | normative trust test | Sound |
| `test_revoked_credential_rejected` | normative trust test | Sound |
| `test_credential_not_bound_to_claimed_principal_rejected` | normative trust test | Sound |
| `test_mechanism_substitution_rejected` | normative trust test | Sound |
| `test_unsupported_mechanism_id_rejected` | normative trust test | Sound |
| `test_approval_id_substitution_rejected` | normative trust test | Sound |
| `test_valid_result_for_invocation_a_cannot_be_reused_for_invocation_b` | normative trust test | Sound |
| `test_expired_approval_subject_rejected` | normative trust test | Sound |
| `test_missing_presentation_rejected` | normative trust test | Sound |
| `test_up_false_rejected_internal_guard` | normative trust test | Sound |
| `test_uv_false_rejected_internal_guard` | normative trust test | Sound |
| `test_lifecycle_not_yet_verified_state_rejected` | normative trust test | Sound |
| `test_no_canonical_proof_rejected` | normative trust test | Sound |
| `test_bind_gate5_is_actually_invoked_and_persists` | structural/model test | Sound |
| `test_fixture_to_real_upgrade_rejected` | normative trust test | Sound |
| `test_caller_constructed_verifier_result_rejected` | **overclaiming test** | **Name claims a general "caller constructed" guarantee; body only tests the `__init__`-with-wrong-seal path. Does not test `object.__new__`, which succeeds. See §10.4.** |
| `test_verifier_result_cannot_be_pickled` | normative trust test | Sound |
| `test_copied_verifier_result_is_not_equal_to_a_fresh_one` | scope/no-go test | Only compares two *legitimate* results, not a forged clone; narrower than its neighbors' apparent implication |
| `test_verifier_result_equality_is_identity_only` | normative trust test | Sound |
| `test_hpac_verifier_module_does_not_import_pb_or_runtime_authority_modules` | scope/no-go test | Sound |
| `test_zero_production_consumers_of_hpac_verifier_module` | scope/no-go test | Sound |
| `test_gate9_consumption_store_is_never_referenced_by_the_verifier` | scope/no-go test | Sound |

26 of 27 are sound and were used as corroborating (not oracle) evidence. One (`test_caller_constructed_verifier_result_rejected`) overclaims relative to what it actually proves, per §33's instruction to flag exactly this pattern.

## 14. Fresh independent test suite (§32)

`tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py`, 29 tests, independently derived from the contract text (not copied from `tests/test_hpac_verifier.py`; only the minimal fixture-setup scaffolding is structurally similar, which is unavoidable given both must exercise the same store APIs). Run result against current `HEAD`:

```
27 passed, 2 failed in 2.60s
```

The 2 failures are exactly and only the `object.__new__` construction-boundary defect (§10), asserted as the contract-required behavior and left failing rather than adjusted to match the implementation. All other 27 assertions — covering the full §32 checklist (independently-derived HPAC-REQ-054 positive/negative cases, forged/copied principal and credential paths, mechanism/presentation/proof substitution, UP/UV independence, expiry, invocation-transfer, deterministic-upgrade rejection, pickle/deepcopy/shallow-copy/attribute-clone anti-forgery, zero production/PB/Gate-9 consumers) — pass.

The existing `tests/test_hpac_verifier.py` (27 tests, unmodified) was also re-run standalone and confirmed: **27 passed**.

## 15. Fixed-SHA regression attribution (§35) — LIMITATION

Full independent re-derivation of the `.1R.5` report's 370-node deselection set against a fresh baseline-vs-candidate Fast Green run (8796+ tests) was **not performed** in this pass — it is outside this fork's practical time/resource budget for this phase. What **was** independently confirmed instead: both the existing `.1R.5` suite (27 tests) and this phase's fresh independent suite (29 tests, 27 passing + 2 correctly-failing) pass/behave as expected against current `HEAD` with no collection errors, no xdist instability observed, and no interaction with the wider suite attempted or claimed. This is disclosed as an explicit scope limitation, not silently treated as equivalent to the full regression-attribution exercise §35 describes. **UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS: not independently re-confirmed at full-suite scope this phase** (neither confirmed zero nor found nonzero — genuinely not run).

## 16. Runtime zero-effect proof (§38)

No subprocess, network, provider, credential, or hardware call exists anywhere in `hpac_verifier.py` (read in full, §5 above — the module is pure Python over in-memory/filesystem-backed store objects). `pcae runtime inspect` at session start (before this phase's work) confirmed: `not_implemented` / `Observed` / `observe` / `unavailable`, zero registered plugins/capabilities — unaffected by this phase's read-only verification work. Runtime remains **Observed / observe / unavailable.**

## 17. `.3` governance incident (§39)

Preserved, unchanged by this phase: **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** remains the historical finding for that incident. No delegated worker in this `.1R.5.1` phase was granted or exercised commit/finalization/push authority; all governed-state mutations (task lifecycle, phase-completion metadata/report, commit, push, `pcae phase complete`) are performed only by the primary human-authorized operator, not by this delegated investigative pass.

## 18. Required verifier adjudications (§41)

| Area | Verdict |
|---|---|
| HPAC-REQ-054 | **NOT VERIFIED** — step 4 (independent challenge-digest recomputation) not implemented; step 3's assurance-level half vacuous; `.1R.4` planning's own re-derivation silently drops a step while the phase report claims "ten-step" fidelity (§4.1, §6) |
| Canonical principal consumption | **VERIFIED** (§9) |
| Canonical proof/presentation/lifecycle consumption | **VERIFIED**, modulo the challenge-digest gap above (§9) |
| UP/UV | **VERIFIED** (§7) |
| Mechanism neutrality | **VERIFIED** (§5 step 6, §12) |
| Deterministic NON-REAL assurance | **VERIFIED** (§11) |
| `AuthenticatedHumanPrincipal` provenance | **NOT VERIFIED — BLOCKING** (`object.__new__` bypass, §10) |
| Anti-transfer / invocation binding | **VERIFIED** (§8) |
| PB/runtime isolation | **VERIFIED** (§12) |

Not every trust-bearing area verifies. Per the governing prompt's §41: *"All trust-bearing areas must verify before .1R.5 is considered complete."* They do not.

## 19. Findings summary (§40)

| # | Classification | Category | Summary |
|---|---|---|---|
| F1 | **BLOCKING** | authenticated-result provenance defect | `AuthenticatedHumanPrincipal`'s trusted-construction seal (HPAC-REQ-056) is enforced only in `__init__`; `object.__new__` bypasses it entirely, producing an `isinstance`-true, `is_real_runtime_eligible=True` forged instance without any verification ever running. §10. |
| F2 | NON-BLOCKING | verifier trust defect / implementation scope defect | HPAC-REQ-054 step 4 (independent challenge-digest recomputation from canonical challenge state) is not implemented; only a string-equality cross-check against the lifecycle genesis binding exists, deferred from step 4 into step 9's logic. Bounded by the absence of any standalone canonical Challenge store in the current foundation. §6. |
| F3 | NON-BLOCKING | governance/tooling debt (inherited) | The `.1R.4` planning document mislabels HPAC-REQ-054 as an "eight-step algorithm" and its own 8-item re-derivation silently omits contract step 4 — the root cause of F2. Pre-existing debt from a prior, already-closed phase; not introduced by `.1R.5`, but its consequence propagated into `.1R.5`'s (and this report's own predecessor's) claim of "ten-step" fidelity. §4.1. |
| F4 | NON-BLOCKING | test-quality / evidence defect | `tests/test_hpac_verifier.py::test_caller_constructed_verifier_result_rejected` overclaims relative to what it tests (only the `__init__` path, not `object.__new__`). §10.4, §13. |
| F5 | OBSERVATION | implementation scope note | Step 3's assurance-level check is vacuous (single eligible mechanism, no HPAC-REQ-059 vocabulary modeled yet) — a legitimate, `.1R.4`-consistent deferral, not itself a defect, but should be named explicitly as future work rather than silently absent. §5. |
| F6 | OBSERVATION | scope hygiene | `d502fc5c` (the implementation commit) also lightly touches three unrelated prior-phase test files with small import/fixture-signature diffs; not re-litigated, not a functional finding. §2.1. |

Zero foundation regressions found (§13/§14 — both the existing and fresh suites pass cleanly against `human_principal_registry.py`, `approval_presentation.py`, `human_authentication_proof.py`, `hpac_lifecycle.py` as currently frozen). Zero PB/runtime-authority/Gate-9 consumption found (§12). B1/B7/N1/N2 files untouched (§12).

## 20. Final verifier verdict

## NOT VERIFIED — AUTHENTICATED-PRINCIPAL RESULT AUTHORITY DEFECT

`.1R.5` is **not** independently verified as complete. The result-object trusted-construction boundary (HPAC-REQ-056), the single highest-risk surface this phase's governing prompt asked to be stress-tested hardest, is demonstrably bypassable via `object.__new__`. This is currently contained (zero production consumers exist anywhere in the repository — §12), so there is no live exploitable path today, but the module's own claim of a closed trusted-construction boundary is false as written, and the `.1R.5` phase report's claim of a fully-implemented HPAC-REQ-054 ten-step sequence is also not accurate (F2/F3).

This verdict does **not** find that `.1R.5`'s broad architecture is unsound — canonical-resolution-only input handling, UP/UV independence, anti-transfer/invocation binding, non-serializability, zero-consumer isolation, and PB/runtime/Gate-9 isolation are all independently confirmed and solid. The defects found are narrow, well-scoped, and (per the governing prompt's own instruction) not repaired in this phase.

## 21. Next recommended phase (§43) — NOT a canonical assignment

Because `.1R.5` does **not** independently verify, the success-path instruction ("return to `.1R.4`'s revised sequence, determine the exact next canonical phase ID from the planning document / `PROJECT_STATUS.md`") does not apply. `PROJECT_STATUS.md`'s own "Planned" section names only `...1R.5.1` (this phase, now complete) with no further entry, consistent with a verification-phase-shaped repository never pre-naming its own repair phase.

Following this repository's own established naming convention for a verification that finds a blocking defect (a `...N.1R`-suffixed blocking-repair phase, mirroring e.g. `.3.2` following `.3.1`'s findings, or `.1R` following `.1`'s findings elsewhere in this same phase family), the natural next phase is a **narrow blocking repair of F1 only** (close the `object.__new__` construction-boundary gap in `AuthenticatedHumanPrincipal` — e.g. by overriding `__new__` to raise, or an equivalent construction-boundary hardening), with F2-F5 either folded in if trivial or explicitly deferred with their own named follow-up. This is stated here as a **recommendation for the human operator to authorize and formally assign a phase ID to**, not as a canonically pre-assigned next phase — consistent with §43's "do not invent an ID" instruction and the governing prompt's stop condition (§46).

## 22. Commits, push status, `origin/main..HEAD`

- **This phase's commit(s):** none yet — this report and the fresh test file are staged for the primary operator's governed finalization sequence (task update → commit → `pcae phase complete` → push → promote), not committed by this delegated investigative pass.
- **Files produced by this phase:** `tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` (29 tests, 27 pass / 2 correctly-fail), this report.
- **`origin/main..HEAD` at investigation start:** `0` (clean, confirmed §4 of the session's initial repository inspection).
- **Pushed status:** not yet pushed as of this report's authorship; pending the primary operator's explicit push step.

## 23. Stop condition

This phase is complete. No repair of F1-F5 was performed (explicitly out of scope per the governing prompt). No B1/B7/N1/N2 work was started. No PB/runtime-authority integration was touched. No real FIDO2 or protected-UI work was performed. Returning control to the primary human operator for review and, if concurred, authorization of a narrow follow-up repair phase per §21.
