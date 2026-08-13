# Phase 149O.20L: Class-B Full-HBDC Readiness Contract / Integration Analysis

**Status:** COMPLETE — ARCHITECTURE/CONTRACT ANALYSIS ONLY — NO IMPLEMENTATION — NO CONTRACT AMENDMENT MADE
**Addresses:** CBV-S10 (READINESS CONTRACT / INTEGRATION GAP)
**Contracts read (unmodified):** HMRC-001 v1.0 (`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`), HMIC-001 v1.3 (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`), HBDC-001 v1.0 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`)
**Production read (unmodified):** `src/pcae/core/hatp_mandatory_cutover.py`, `src/pcae/core/hatp_mandatory_certification.py`, `src/pcae/core/hatp_class_b_conformance.py`, `src/pcae/core/hatp_class_b_topology_verifier.py`, `src/pcae/core/hatp_environment_lock_verifier.py`
**Proof:** `tests/test_phase_149o_20l_class_b_full_hbdc_readiness_contract_integration_analysis.py` (18 passed, 0 failed)

This is an architecture/contract/integration analysis phase. No production readiness, Class-B verifier, HMIC, or HBDC code was modified. No contract document was amended. No provisioning, certification, or activation occurred.

---

## 1. Current readiness contract and root (reconstructed from primary source)

The sole production activation-readiness entrypoint is `assess_hatp_mandatory_activation_readiness(root)` in `src/pcae/core/hatp_mandatory_cutover.py:928`, delegating to the internal test seam `_assess_hatp_mandatory_activation_readiness_at_root` (`hatp_mandatory_cutover.py:752-925`). It is governed by **HMRC-REQ-054** (`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md:562-571`), which states `PREPARED` requires, at minimum, the conjunction of:

1. Class-B deployment valid (existing 149O.6/149O.7 architecture)
2. HATP substrate operational (`inspect_hatp_verification_substrate_readiness(...).operational`)
3. HSCE signing implementation available
4. Mandatory-consumption implementation version present and independently verified (originally a placeholder — "a future 149O.16-class verification, not this contract" — later concretely supplied by HMIC-001, HMIC-REQ-004)
5. Production dependency provenance valid
6. Protected Activation Authority mechanism available

**Live production reconstructs seven terms, not six** (confirmed by `test_readiness_vector_has_exactly_seven_terms_on_the_real_host`, reading `readiness.checks` directly, not from memory):

| # | Live check name (`HATPMandatoryActivationReadinessCheck.name`) | Maps to HMRC-REQ-054 bullet |
|---|---|---|
| 1 | `class_b_protected_storage_available` | bullet 1 |
| 2 | `repository_deployment_identity_valid` | **not enumerated in HMRC-REQ-054's text at all** |
| 3 | `hatp_substrate_operational` | bullet 2 |
| 4 | `hsce_signing_implementation_available` | bullet 3 |
| 5 | `mandatory_consumption_implementation_independently_verified` | bullet 4 |
| 6 | `production_dependency_provenance_valid` | bullet 5 |
| 7 | `protected_activation_authority_mechanism_available` | bullet 6 |

This is a **pre-existing, disclosed observation, not a defect this phase repairs**: `repository_deployment_identity_valid` is an identity prerequisite the implementation "already owns" per `_assess_hatp_mandatory_activation_readiness_at_root`'s own docstring ("plus the identity/storage prerequisites this module already owns"), predating both HMIC-001 and this phase. It is noted here because §4 of this analysis must record the *exact* live vector, not the contract's own six-item summary, and because it establishes precedent: **HMRC-REQ-054's enumerated conjunction and the live implementation's checked conjunction are not required to have identical cardinality** — the contract states a floor ("at minimum"), and production may (and does) add terms beyond it. This matters directly for this phase's own recommendation (§9): adding an eighth term does not, by itself, require touching every one of HMRC-REQ-054's existing six bullets.

Aggregation rule (`hatp_mandatory_cutover.py:922-925`): `ready = (len(unmet_reasons) == 0)` — pure AND-conjunction, no partial credit, no majority rule. Failure semantics: any unsatisfied check contributes its `.detail` string to `reasons`; no check can be individually waived. Indeterminate semantics: every check is a plain Python `bool`; there is no "unknown" state in the readiness vector itself — exceptions during a sub-inspection are caught and mapped to `satisfied=False` (fail-closed), never propagated, never treated as ready (confirmed for the HMIC term at `hatp_mandatory_cutover.py:876-881`, for substrate at `:830-831`). Diagnostics: each check carries a free-text `detail` string (not a further-structured object). Contract source: HMRC-REQ-054/055 (readiness), HMIC-REQ-004 (five-term non-ownership disclaimer), no contract currently enumerates `repository_deployment_identity_valid`.

`activate_hatp_mandatory`/`assess_hatp_mandatory_activation_readiness` have **no CLI command, no caller, and no consumer anywhere in `src/` or `scripts/` outside `hatp_mandatory_cutover.py` itself** (confirmed by repo-wide grep, §12 below) — this is a purely library-level, human-operator-invoked function, not something any current report or CLI surfaces today.

---

## 2. Does any existing readiness term already require full HBDC conformance?

No. Proven, not inferred (`TestClassBTermIsNarrowerThanFullConformance`):

- `class_b_protected_storage_available`'s entire computation is `protected_root.is_dir() and not protected_root.is_symlink()` (`hatp_mandatory_cutover.py:786`) — a two-predicate directory-existence-and-non-symlink check on exactly one path.
- `_assess_hatp_mandatory_activation_readiness_at_root`'s full source contains **zero** references to `verify_class_b_deployment_conformance`, `verify_class_b_topology_conformance`, or `verify_environment_lock_conformance` (confirmed by direct substring search of `inspect.getsource(...)`, and independently by the zero-consumer AST sweep in §12).
- `protected_activation_authority_mechanism_available` checks one predicate: `not (protected_root.stat().st_mode & 0o022)` — a single mode-bit check, a strict subset of HBDC-REQ-014 (which the HBDC-001 contract itself cross-references: "consistent with the check already implemented in `hatp_mandatory_cutover._assess_hatp_mandatory_activation_readiness_at_root`'s `protected_activation_authority_mechanism_available` step" — `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md:95`). HBDC-001 explicitly treats this existing readiness check as **one ingredient it reuses**, not as something that already encompasses HBDC-001's other ~40 requirements.

Full HBDC Class-B deployment conformance (`verify_class_b_deployment_conformance()`) aggregates, per `hatp_class_b_conformance.py`: topology conformance (agent identity, mode/group/ACL rights, Trusted-Git and Protected-Root ancestor-chain resolution, symlink/hard-link safety — 11 sub-checks), environment-lock conformance (interpreter-writability, venv-lock, `PYTHONPATH`/user-site/`.pth`/meta-path/module-origin/editable-install/launcher/shell-injection/third-party-boundary — ~13 sub-checks), Model-A deployment detection (HBDC-REQ-022/024), and deployment-identity binding (HBDC-REQ-042..046) — roughly two dozen HBDC-REQ items across four independent check families. `class_b_protected_storage_available` and `protected_activation_authority_mechanism_available` together cover, at most, the topology family's Protected-Root-mode sliver of HBDC-REQ-014 alone. **None of the remaining readiness terms (substrate, HSCE, HMIC, dependency provenance, repository identity) touches Class-B topology, environment lock, Model-A, or deployment-identity binding at all** — they are semantically disjoint concerns (substrate = HATP hardware/provider readiness; HSCE = signing-ceremony module importability; HMIC = *implementation-source* identity, not *deployment* state).

**Confusable-but-distinct concepts, checked individually and found non-equivalent:** environment readiness (HSCE/substrate checks concern *HATP's own* provider/signing machinery, not the *agent's own execution environment* HBDC-001 locks down) ≠ deployment readiness (no readiness term evaluates deployment topology at all) ≠ trust/provenance (HMIC term concerns *source bytes*, HBDC concerns *runtime/deployment state* — HMIC-REQ-004 names these as five distinct terms it explicitly does not own or substitute for) ≠ HMIC validity (a certification-record validity fact, orthogonal to live deployment state — HMIC-REQ-009's semantic wall: "certification valid ≠ HATP production READY") ≠ protected-root readiness (only the directory-existence sliver) ≠ execution capability (unrelated; Permission Broker's own domain) ≠ certification (HMIC's domain, consumes nothing about Class-B deployment).

---

## 3. HBDC-001's own textual disposition

HBDC-001 itself, read directly, already anticipates and explicitly disclaims mechanical readiness gating as of its current disposition:

- **HBDC-REQ-049**: "Until HBDC-REQ-048's amendment exists, HBDC-001 conformance is evidentiary/advisory only: it informs a human or a future independent-verification phase whether Class-B topology is legitimately established, but it does not mechanically gate `validate_active_hatp_mandatory_independent_verification_certification`'s result, and no phase report or contract may represent it as doing so." (HBDC-REQ-048's amendment — binding HBDC-001's version into HMIC's `contract_versions` — was completed by 149O.20D/149O.20D.1; that satisfied the *certification-input* prerequisite, not a readiness-gating one — HBDC-REQ-049's own text names `validate_active_hatp_mandatory_independent_verification_certification`, not `assess_hatp_mandatory_activation_readiness`.)
- **HBDC-REQ-055 / CBD-8**: "Contract conformance under HBDC-001 does not by itself equal 'HATP DEPLOYMENT READY,' 'HATP PRODUCTION READY,' or 'ROLLBACK EXECUTION READY' ... Those terms retain their own, separately gated definitions." / "HBDC-001 does not mechanically gate HMIC certification validity until formally bound into HMIC's contract set (HBDC-REQ-047..049)."

HBDC-001's own text therefore does **not** already state that Class-B conformance is a prerequisite to readiness — Outcome C (§9 below) is directly contradicted by the contract's own words, not merely by absence of a wire-up.

HMIC-001's §53.12 (v1.3, 149O.20K) independently, and consistently, restates the same conclusion from the HMIC side: "**CBV-S1: OPEN ... even then, CBV-S1 remains open until a further, separately-governed phase actually wires `verify_class_b_deployment_conformance`'s result into `assess_hatp_mandatory_activation_readiness` or an equivalent certification input (HMIC-REQ-063 Option-C), which this phase explicitly does not attempt, authorize, or imply.**" This phase (149O.20L) is exactly that "further, separately-governed phase" — for the analysis-only portion; the wiring itself remains future work (§10).

---

## 4. The concrete bypass counterexample

`tests/test_phase_149o_20l_class_b_full_hbdc_readiness_contract_integration_analysis.py::TestConcreteBypassCounterexample` demonstrates the gap directly, not merely argues it from contract text:

1. `test_every_readiness_term_can_be_forced_true_in_isolation` — using an isolated `tmp_path` fixture (never `HATPTrustStore.production()`, never real filesystem authority) and the same internal test seam (`_assess_hatp_mandatory_activation_readiness_at_root`) prior verified phases (149O.19.5F) already use legitimately, all seven live readiness terms are forced `satisfied=True` — `readiness.ready is True`, `readiness.reasons == ()`.
2. `test_real_unmocked_class_b_conformance_is_not_compliant_on_the_same_host` — in the **same test**, immediately afterward, the real, completely un-mocked `verify_class_b_deployment_conformance()` (called with no arguments, so it inspects the actual host's real interpreter, real ACLs, real venv/`PYTHONPATH` state — entirely independent of the fixture's `protected_root`/`repo_root`) is freshly invoked and asserted **not** `COMPLIANT`.

Both assertions pass (confirmed: 18/18 tests green). **This is the smallest counterexample available**: it requires no contrivance of the Class-B verifier's own logic at all — the real, unprovisioned development host already satisfies neither HBDC's topology, environment-lock, Model-A, nor deployment-identity requirements (24 distinct `reasons` entries observed directly, §7 below), while readiness's own seven-item conjunction can be satisfied through isolated test-seam substitution with zero dependency on any of those 24 requirements. **CBV-S10 is concretely demonstrated, not merely a theoretical gap.**

T1/T2 (governing-prompt §36) are directly answered by this test: HMIC valid + Class-B NON_COMPLIANT/INDETERMINATE → readiness **is currently `True`** in the isolated-fixture construction (and would be `True` on the real host too, the instant the six other, already-independently-gated terms became individually satisfiable — none of which depends on Class-B conformance).

---

## 5. Refining an existing term vs. adding a new one (Outcome A vs. Outcome B)

**Candidate: refine `class_b_protected_storage_available`.**

- *Current semantic domain already "deployment conformance"?* No — its domain is exactly "does the Protected Root directory exist and is it a real directory" (§2). It predates HBDC-001 by several phase-families (149O.6/149O.7, per HMRC-REQ-054's own bullet-1 citation) and predates the Class-B verifier island (149O.20H/I) entirely.
- *Would adding HBDC alter its established meaning incompatibly?* Yes. HMIC-001 §53.4 independently confirmed and recorded that `hatp_mandatory_cutover.py` "reference[s] only the string/concept 'Class-B' (e.g. `class_b_protected_storage_available`, `class_b_bootstrap_environment_safe`) for pre-existing, unrelated readiness terms (**CBV-S10's own gap**)" — the contract record itself already treats this term's current meaning as settled and distinct from the verifier island's result.
- *Would it collapse distinct authority concepts?* Yes. Folding topology + environment-lock + Model-A + deployment-identity (four independently-diagnosable HBDC families) into a term currently named for, and scoped to, one directory-existence predicate would erase the distinction HBDC-001's own tri-state-per-check design (`ClassBCheckResult` per `check_id`) deliberately preserves.
- *Would downstream consumers lose diagnostic granularity?* Yes — a single overloaded boolean cannot represent "topology failed" vs. "environment lock failed" vs. "Model-A deployment unsupported" vs. "deployment-identity unbound" the way the current, separately-itemized `HATPMandatoryActivationReadinessCheck.detail` convention already does for every other term (e.g. the HMIC term's `detail` embeds `status=... reasons=[...]`, §1).
- *Would historical artifacts become misleading?* Yes — every phase report and contract passage (149O.18F, 149O.19.5F, HMIC-001 §53.4) that currently describes `class_b_protected_storage_available` as "pre-existing, unrelated" to the Class-B verifier would become retroactively inaccurate.
- *Would contract evolution be required anyway?* Yes — HMRC-REQ-054's own bullet-1 text ("Class-B deployment valid (existing 149O.6/149O.7 architecture)") would need textual revision regardless, so refining the existing term buys no amendment-avoidance benefit.

All six refinement disqualifiers apply. **Outcome A is rejected.**

No other existing term is even a plausible refinement candidate: `hatp_substrate_operational`, `hsce_signing_implementation_available`, `mandatory_consumption_implementation_independently_verified`, `production_dependency_provenance_valid`, and `repository_deployment_identity_valid` each govern a semantically disjoint domain (HATP hardware substrate, HSCE module presence, HMIC source-identity, trust-store construction, repository UUID validity respectively) with no textual or call-graph overlap with Class-B deployment topology at all.

**Outcome C is rejected** by §3–4's direct evidence (HBDC-001's own text disclaims mechanical gating; the counterexample proves the gap operationally).

**Outcome D (deeper architecture conflict) is rejected.** No circularity exists: `verify_class_b_deployment_conformance()` is read-only, stateless, and freshly recomputed on every call — structurally identical to every other HMRC-REQ-054 term (no-cache discipline, HMRC-REQ-052/HMIC-REQ-113). HMIC-001 §53.7 independently confirmed no import cycle and no self-reference between the verifier island and the certification/readiness modules. The existing lock-held-recheck mechanism (`_write_cutover_transition`'s `readiness_check` callback, `hatp_mandatory_cutover.py:673-685`) already generically solves the TOCTOU concern for every readiness term, including a future Class-B one, without new machinery (§10). There is no evidence of stale-state authority or unsafe representation that a straightforward new-term addition cannot resolve.

**Selected: Outcome B — a distinct, new Class-B deployment-conformance readiness term is required.**

---

## 6. Precedent for how a new term should be added

HMIC-001's own history supplies the operative precedent, and it is *not* a simple analogy — it establishes a specific procedural pattern this phase's recommendation follows:

HMRC-REQ-054 v1.0 already anticipated `mandatory_consumption_implementation_independently_verified` as a **named placeholder bullet** ("a future 149O.16-class verification, not this contract"). HMIC-001 was then created as a *separate, standalone contract* whose entire purpose (HMIC-REQ-004) is to supply the concrete evidence/mechanism for that one pre-existing bullet — HMIC-001 does not itself widen HMRC-REQ-054's enumeration; it fills in a slot HMRC-001 already reserved.

**HMRC-REQ-054 has no analogous placeholder bullet for Class-B deployment conformance.** Bullet 1 ("Class-B deployment valid (existing 149O.6/149O.7 architecture)") is not such a placeholder — it names a concrete, already-implemented, narrower check (§2/§5), not an open slot awaiting a future contract. Therefore, unlike the HMIC case, **HMRC-001 itself must be textually amended** to add a new, explicit bullet before any future contract (most naturally HBDC-001 itself, which already owns the tri-state conformance vocabulary — HBDC-REQ-052) can be recognized as supplying it. This is the one respect in which this phase's recommended path differs from a pure repeat of the HMIC precedent, and it is derived from the contracts' own text, not assumed.

---

## 7. Fail-closed mapping (contractually proven, not merely designed)

`certification_status_satisfies_readiness` (`hatp_mandatory_certification.py:481-495`) is the live precedent for exactly the mapping a future Class-B term needs: "`True` if and only if `status` is exactly `CertificationStatus.VALID`; every other member — and any value that is not a `CertificationStatus` member at all — maps to `False`." An analogous function for Class-B would map `ClassBConformanceStatus.COMPLIANT → True`; every other member of the six-member closed vocabulary (`NON_COMPLIANT`, `INDETERMINATE`, `ACCESS_ERROR`, `MALFORMED_STATE`, `UNSUPPORTED_DEPLOYMENT_MODEL`) → `False`. HBDC-REQ-052 independently mandates this at the contract level: "`INDETERMINATE` SHALL be treated as NOT ready for any readiness claim — fail-closed; there is no 'unknown but allowed' outcome." `TestCurrentShapes.test_class_b_status_is_a_closed_six_member_enum_not_boolean` confirms the live vocabulary this mapping must close over. No unknown/error state may become ready under this design — proven by the same enumeration-exhaustive `else → False` pattern the HMIC precedent already uses, not a new invention.

---

## 8. Non-bypassability

Every production path capable of producing HATP readiness, certification readiness, activation readiness, or cutover eligibility was traced (repo-wide grep + AST sweep, `TestZeroConsumerReconfirmation` and `TestNoAlternateReadinessConstructor`):

- **Readiness**: exactly one production entrypoint (`assess_hatp_mandatory_activation_readiness`), exactly one internal implementation (`_assess_hatp_mandatory_activation_readiness_at_root`), exactly one dataclass-construction site (`ast` walk confirms `HATPMandatoryActivationReadiness(...)` is instantiated at exactly one call site in the module).
- **Certification**: `validate_active_hatp_mandatory_independent_verification_certification` (HMIC-001's sole validator entrypoint) is unrelated to and does not consume Class-B conformance at all, and is not itself a bypass path for a future Class-B readiness term (it feeds readiness, not the reverse).
- **Activation**: `activate_hatp_mandatory` → `_activate_hatp_mandatory_at_root` → `_write_cutover_transition`'s lock-held `readiness_check` callback, which calls `_assess_hatp_mandatory_activation_readiness_at_root` a **second time**, fresh, while holding the transition lock — the same function a future Class-B term would be added to. There is no second, parallel activation path; `_write_cutover_transition` is the sole writer, gated by `is_valid_cutover_transition`'s closed two-transition set.
- **No alternate readiness constructor exists** (`ast` walk, one construction site) — a caller cannot fabricate a `ready=True` result by constructing the dataclass directly with a different code path, because no such second path exists in production.

A future integration that adds the Class-B check **inside** `_assess_hatp_mandatory_activation_readiness_at_root` (the single function both the advisory call and the lock-held re-check already invoke) is therefore automatically non-bypassable by construction — it inherits the existing single-entrypoint, single-constructor, dual-evaluation (advisory + lock-held) discipline for free, without inventing new enforcement.

---

## 9. Schema, compatibility, and migration impact

`HATPMandatoryActivationReadiness`/`HATPMandatoryActivationReadinessCheck` are plain in-memory `@dataclass(frozen=True)` objects — confirmed (`TestConcreteBypassCounterexample.test_readiness_result_carries_no_field_that_could_have_observed_class_b`) to have exactly the fields `{ready, checks, reasons}` / `{name, satisfied, detail}`. **No JSON serialization, CLI surface, or persisted artifact of this dataclass exists anywhere in the repository today** (confirmed by grep — no `pcae` subcommand reports it, no report schema embeds it). Consequently:

- Adding an eighth `HATPMandatoryActivationReadinessCheck` entry to the `checks` tuple is additive-only at the Python level — no existing field changes shape, and `checks` is already a variable-length tuple (going from 7 to 8 entries is not a breaking shape change to any existing consumer, because there are zero existing consumers besides the module's own internal caller).
- **No old artifacts exist to remain readable** — there is no "artifact schema version" concept for this particular dataclass to migrate. This is a materially simpler compatibility posture than, e.g., HMIC's `CertificationRecord` schema (which *is* persisted and *does* need version discipline).
- If and when a future phase does add a CLI/report surface for readiness (not proposed by this phase), that surface must, per this phase's disciplined recommendation, treat a **missing** Class-B field as fail-closed-not-ready (mirroring HBDC-REQ-021's "fail closed — not auto-provision, not silently degrade" discipline), never default it to `True`.

---

## 10. Certification interaction

Readiness is evaluated independently of, and does not gate, certification — `HATPMandatoryActivationReadiness` and `CertificationRecord`/Active-Certification-Pointer are separate data structures with no shared schema. Certification is evaluated *before* readiness only in the sense that readiness's HMIC term *consumes* a fresh certification validation result as one input (`hatp_mandatory_cutover.py:867-871`) — certification does not consume readiness in the other direction. Certification does not "freeze" readiness inputs; each readiness assessment is fully fresh (§1). Class-B conformance changing after readiness but before activation is exactly the freshness concern §11 addresses — the existing dual-evaluation pattern (advisory + lock-held re-check, §8) already exists for this reason and requires no new mechanism to extend to a Class-B term. HMIC-001 v1.3 §53's Class-B verifier source-binding (limb (c)) is a **distinct** protection: it guards the verifier's own *bytes* from undetected tampering (via `implementation_scope_digest`), not the verifier's *runtime result* freshness — HMIC binds source, it does not attest live deployment state (governing-prompt §17, restated from HMIC-REQ-063's own residual-limitation disclosure). A future Class-B readiness term does not need to be included in any certification digest; it needs to be evaluated fresh at readiness-check time, exactly like every sibling term.

---

## 11. Freshness / TOCTOU and re-evaluation boundary

`verify_class_b_deployment_conformance()` is a runtime/deployment-state result that could change between an earlier "COMPLIANT" observation and a later activation attempt (e.g., an admin loosens a Protected-Root ACL, or an agent's environment drifts). This is **not a new problem a Class-B term introduces** — it is the identical shape of problem HMRC-001 already solved generically for every readiness term via the two-tier evaluation already present in production:

1. **Advisory tier** — an operator or tool calls `assess_hatp_mandatory_activation_readiness` at any time; this result is informational only, never itself authorizing.
2. **Lock-held tier** — `_write_cutover_transition`'s `readiness_check` callback (`hatp_mandatory_cutover.py:673-685`) re-invokes the *same* assessment function immediately before the Cutover Record write, while holding an exclusive lock on the protected root — "no earlier 'was ready' result is ever trusted" (existing docstring, unchanged).

A future Class-B term inherits this discipline automatically by being added inside `_assess_hatp_mandatory_activation_readiness_at_root` itself, rather than being evaluated once and cached anywhere. No result timestamp, environment snapshot, or evidence digest needs to be invented for readiness purposes — the existing no-cache, dual-evaluation architecture is sufficient, and inventing a persisted freshness token would be over-design relative to what HMRC-REQ-052/HMIC-REQ-113's no-cache discipline already guarantees. Re-evaluation boundary: at readiness assessment (advisory) and at activation (lock-held, authoritative) — **not** on every execution attempt (Class-B deployment conformance is a cutover/activation-time deployment-topology concern, not a per-command runtime-enforcement concern; turning it into continuous enforcement would exceed HMRC-001's own scope and is not required by any HBDC-REQ).

---

## 12. Non-bypassability proof plan for a future implementation phase

A future production-integration phase (§13) must prove, at minimum:

1. The new check is added inside `_assess_hatp_mandatory_activation_readiness_at_root` (the single function both advisory and lock-held paths already share) — not as a separate, parallel gate.
2. `COMPLIANT` maps to `True`; `NON_COMPLIANT`, `INDETERMINATE`, `ACCESS_ERROR`, `MALFORMED_STATE`, and `UNSUPPORTED_DEPLOYMENT_MODEL` all map to `False` — exhaustively, via the closed-enum `else`-branch pattern `certification_status_satisfies_readiness` already establishes, not an allow-list of "known good" values.
3. `COMPLIANT` alone does not bypass any of the other seven terms — the AND-conjunction (`ready = len(unmet_reasons) == 0`) already guarantees this structurally; the new term only ever subtracts additional ready-states, never substitutes for an existing one.
4. No alternate readiness constructor exists post-integration (repeat the AST single-construction-site sweep §8 uses here).
5. No serialization can default a missing eighth field to ready (N/A today, §9 — becomes relevant only if a future phase also adds persistence).
6. Certification/activation cannot use an "old" readiness shape without fail-closed migration logic — currently vacuous (no persisted readiness shape exists to be "old"), but the discipline must be explicitly re-affirmed if persistence is later added.

---

## 13. Historical-test migration strategy

Existing readiness tests (`tests/test_phase_149o_18a_hatp_mandatory_cutover_state_foundation.py`, `tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py`, `tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py`, `tests/test_phase_149o_19_5g_hmic_assembled_attack_matrix_hardening.py`, `tests/test_hatp_mandatory_activation_guard.py`) encode: (a) contract semantics (six/seven-term conjunction shape, exact check names — several assert exact `names == [...]` lists, mirroring this phase's own `test_readiness_vector_has_exactly_seven_terms_on_the_real_host`); (b) aggregation (`ready` iff all satisfied); (c) negative cases (each term individually forced `False`); (d) activation coupling (lock-held re-check). **A future term-count-changing phase will break every hard-coded seven-item `names == [...]` assertion by design** — this is the identical, already-precedented "historical-pin supersession" pattern 149O.20K.2/K.3 classified for the 25→28 file-count widening (§19 of the 149O.20K.3 report). The correct handling, mirroring that precedent exactly: (1) any test asserting the *exact current* term count/order is a **current-production invariant test**, expected and required to be updated in the same implementation phase that adds the eighth term (not preserved unmodified); (2) any test pinned to a **specific historical commit** (via `git show <fixed-commit>:...`, mirroring `_historical_frozen_canonical_paths_at` in the 149O.19.5F suite) is a **historical invariant test**, correctly left unmodified forever, because it is asserting what a past phase's state was, not what current production is. This phase's own new test module contains no fixed-commit-historical assertions (it only asserts live/current shape), so it requires no such distinction internally, but a future 149O.20L.1/.3 phase must apply this same commit-pinning discipline to any new fixed-baseline test it adds, to avoid repeating the fixed-commit `git diff` repin-debt pattern already disclosed as a known gotcha in this repository's operating history.

---

## 14. T1–T7 threat analysis

| # | Threat | Current answer |
|---|---|---|
| T1 | HMIC valid, Class-B NON_COMPLIANT — could readiness be positive today? | **Yes** — proven concretely (§4). No current term observes Class-B conformance at all. |
| T2 | HMIC valid, Class-B INDETERMINATE — could readiness be positive today? | **Yes**, same mechanism as T1 — `INDETERMINATE` is invisible to every current term. |
| T3 | Class-B COMPLIANT, another readiness term false — must remain not ready. | **Holds today and would continue to hold** — the AND-conjunction structurally guarantees this; adding a Class-B term only ever subtracts ready-states. |
| T4 | Stale Class-B COMPLIANT result surviving to activation. | **Not a risk today** (Class-B isn't consulted at all yet); **for the future term**, resolved by inheriting the existing dual-evaluation (advisory + lock-held re-check) architecture, §11 — no new staleness window is introduced if the term is added inside the shared assessment function. |
| T5 | Missing Class-B field/artifact defaulting to ready. | **Not applicable today** (no persisted artifact exists, §9); the future integration must not introduce an optional/defaulted field — the check should be unconditionally present in the `checks` tuple, exactly like the other seven, with no "absent means pass" path. |
| T6 | Alternate readiness construction path bypassing Class-B evaluation. | **No such path exists today** (single constructor site, §8); a future integration must preserve this (proof plan §12 item 4). |
| T7 | Certification using an old readiness schema to authorize a path lacking Class-B evidence. | **Not applicable today** — certification does not consume readiness's schema at all (§10); the concern would only become live if a future phase inverts that relationship, which no current or recommended design does. |

---

## 15. CBV-S1 regression (focused, not a full re-verification campaign)

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` version header confirmed unchanged at v1.3; HMIC-REQ-050's 28-file enumeration and HMIC-REQ-067's 5-member `_CONTRACT_IDENTITY_FILES` were not re-derived from scratch this phase (per governing-prompt §34's "focused regression is sufficient" instruction) — this phase instead confirms, by direct read of `hatp_mandatory_certification.py`, that `_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` are unchanged from K.3's exit state (28/5) and that this phase modified no file inside that frozen set (§16 below). **CBV-S1: unchanged — INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT + PRODUCTION SOURCE-IDENTITY BOUNDARY**, not reopened by this phase (no contradictory evidence found or sought).

---

## 16. Production/contract files untouched confirmation

`git status --short` / `git diff` (checked before and after this phase's edits) confirm this phase touched only: this document, the new proof-test module, `PROJECT_STATUS.md`, `CHANGELOG.md`, task/lifecycle files, and `.pcae/phase-completion-*` metadata. No `src/pcae/**` file, no `scripts/**` file, and no `docs/contracts/**` file was modified. Zero Class-B verifier modification, zero HMIC modification, zero HBDC modification, zero readiness/certification/activation production-code modification, zero Permission Broker/POL-005/COMP-002 modification, zero runtime-enforcement modification.

---

## 17. Selected architecture (governing-prompt §38's required single decision)

**Full HBDC Class-B deployment conformance must become a mandatory, fail-closed, eighth input term of HATP activation readiness (HMRC-REQ-054's conjunction), evaluated by a new function following `certification_status_satisfies_readiness`'s exact closed-enum-mapping precedent (`ClassBConformanceStatus.COMPLIANT → True`, every other of the six vocabulary members → `False`), added inside `_assess_hatp_mandatory_activation_readiness_at_root` (never a parallel gate), before certification or activation may progress — requiring: (a) an HMRC-001 textual amendment adding a new, explicit HMRC-REQ-054 bullet (HMRC-001 currently has no placeholder for this, unlike its pre-existing HMIC-implementation-verification bullet), (b) no HMIC-001 or HBDC-001 amendment (HBDC-001 already supplies the tri-state vocabulary and verifier; HMIC-001's role in this integration is limited to its already-completed source-scope binding of the verifier's bytes, §53, an orthogonal protection), (c) an additive-only, non-breaking dataclass change (no persisted schema exists to migrate), and (d) inheriting, not reinventing, the existing single-entrypoint / single-constructor / dual-evaluation (advisory + lock-held) non-bypassability and freshness architecture.**

This is Outcome B. It was not assumed at the outset — Outcome A (refining `class_b_protected_storage_available`) was evaluated against all six governing-prompt §8 criteria and rejected on all of them (§5); Outcome C was evaluated against HBDC-001's own text and the concrete counterexample and rejected (§3–4); Outcome D was evaluated against the existing no-cache, no-cycle, single-entrypoint architecture and rejected (§5) — the architecture already generically solves circularity and staleness for every existing term, and does not need repair to accommodate one more.

---

## 18. Status summary

- **CBV-S10:** **OPEN — READINESS INTEGRATION ARCHITECTURE DERIVED — CONTRACT/IMPLEMENTATION WORK PENDING.** Not closed by this phase (no implementation, no contract amendment performed). The concrete gap is now demonstrated (§4), not merely asserted.
- **CBV-S1:** unchanged — INDEPENDENTLY CONFIRMED CLOSED AT HMIC CONTRACT + PRODUCTION SOURCE-IDENTITY BOUNDARY (§15).
- **Class-B verifier:** unchanged — CONTRACT VERIFIED — VERIFIER REPAIR LINE INDEPENDENTLY VERIFIED — HMIC SOURCE BINDING INDEPENDENTLY VERIFIED — NOT PROVISIONED.
- **HATP:** unchanged — **NOT READY** (real-host regression: `assess_hatp_mandatory_activation_readiness(...).ready is False`, `verify_class_b_deployment_conformance().status != COMPLIANT`, both reconfirmed §4/§16 and by `TestRealHostRegression`).
- **Runtime:** unchanged — Observed / observe / unavailable.
- **Tests actually run:** `pytest tests/test_phase_149o_20l_class_b_full_hbdc_readiness_contract_integration_analysis.py -q` → 18 passed, 0 failed; fast_green cited separately in the phase-completion metadata.
- **Production files untouched:** confirmed (§16).

---

## 19. Recommended next phase

**149O.20L.1 — Readiness Contract/Schema Evolution.** Amend HMRC-001 (add the new HMRC-REQ-054 bullet per §17; version bump per this repository's established minor-bump-for-scope-widening convention, mirroring HMIC-001 v1.0→v1.1) and define the exact new dataclass/mapping-function contract text (mirroring `certification_status_satisfies_readiness`'s precedent, §7). No production code change. Followed by:

- **149O.20L.2** — independent verification of the contract amendment (mirroring 149O.20K.1's role for HMIC's own v1.3 amendment).
- **149O.20L.3** — production readiness integration: add the eighth check inside `_assess_hatp_mandatory_activation_readiness_at_root`, wiring `verify_class_b_deployment_conformance` for the first time into any authority-bearing production path.
- **149O.20L.4** — independent verification of the production integration (non-bypassability proof plan §12, in full).

**Only after 149O.20L.4 completes may CBV-S10 close.** This phase (149O.20L) does not begin 20L.1's contract text, does not touch HMRC-001/HMIC-001/HBDC-001, and does not wire any production call path.
