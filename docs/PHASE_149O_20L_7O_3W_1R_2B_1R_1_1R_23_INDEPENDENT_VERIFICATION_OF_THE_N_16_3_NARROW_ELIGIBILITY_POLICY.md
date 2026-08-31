# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.23 — Independent Verification of the N-16-3 Narrow-Eligibility Policy

**Type:** independent verification of `.1R.22` (N-16-3 Narrow-Eligibility Policy and Contract Implementation).
**Status:** **BLOCKED INDEPENDENT-VERIFICATION RESULT — finalized (Option B).**
The substantive N-16-3 model — PBRD-001 v3.0 MAJOR trigger + migration,
trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` classification, the POL-005
§12a carve-out, POL-013's never-positive behaviour, `_compose` precedence,
and **production unsatisfiability** — is independently RE-DERIVED and
**closed-worthy**. **Regression / verification-evidence acceptance is
BLOCKED** and referred to a dedicated repair phase
(`149O.20L.7O.3W.1R.2B.1R.1.1R.22R`). See §2, §12, §20.
**Verification-entry SHA:** `15aeb269` (`.1R.22` finalize head; `HEAD == origin/main`; `origin/main..HEAD = 0` at entry).
**Immutable pre-`.1R.22` baseline (independently reconstructed):** `8603fe6a`
— the `.1R.21` push-state-reconcile head and the parent of the `.1R.22`
production implementation commit `1dadeb21`
(`git merge-base --is-ancestor 8603fe6a origin/main` → true; `git rev-list --count 8603fe6a..HEAD` → 9).
**Production source modified by this phase:** none.
**Normative contracts modified by this phase:** none.
**Scope-fence / guard files modified by this phase:** none — the 16 discovered
undisclosed `.1R.22`-attributable guard-test failures are **NOT repaired
inside `.1R.23`**; they are referred to `.1R.22R`.
**Execution:** not enabled. Runtime `not_implemented / Observed / observe /
unavailable`; POL-005 hard DENY unchanged for every non-eligible
non-simulation request; 0 plugins / 0 capabilities; `pcae runtime inspect`
posture byte-identical at entry and finalization. **FIRST EXTERNAL EFFECT: ABSENT.**
**Governance:** governed `pcae` lifecycle only. The historical delegated `.3`
finalization / commit / push incident remains **UNAUTHORIZED**. Only the
primary human-authorized operator holds `.1R.23` lifecycle authority;
delegated workers may not commit / finalize / push. This phase is **not
self-closed** — the substantive verdicts below are offered as evidence; the
blocker is referred out, not adjudicated away.

---

## 1. Verification method

RE-DERIVE, DO NOT TRUST. Every verdict below was derived from primary source
(`src/pcae/core/permission_broker_foundation.py`,
`src/pcae/core/runtime_dispatch_permission.py`,
`src/pcae/core/runtime_authority.py`, the PBRD-001 v3.0 / PBNDE-001 v1.0 /
PBPA-001 v1.1 contract text, `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`,
and Git history), not from the `.1R.22` report, its 43-test suite, contract
prose, helper names, profile constants, or migration comments.

Fresh IV suite: `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py`
— **55 test functions**, no production or contract mutation. Fixed-SHA A/B
run deterministically (no xdist) against a `git worktree` at `8603fe6a`.

## 2. Exact `.1R.22` commit range (independently reconstructed)

`git rev-list --count 8603fe6a..HEAD` → **9**; every subject carries the
`…1R.1.1R.22` token; `git diff --name-only 8603fe6a HEAD -- src/pcae` →
exactly the two authorized files.

| # | SHA | Role |
|---|---|---|
| baseline | `8603fe6a` | immutable pre-`.1R.22` baseline (`.1R.21` push-reconcile head; parent of `1dadeb21`) |
| 1 | `1dadeb21` | **production implementation** — N-16-3 in `permission_broker_foundation.py` + `runtime_dispatch_permission.py`; policy-count + scope-fence guard reconciliations |
| 2 | `5114039a` | earlier-phase scope-fence / byte-freeze / meta-guard reconciliations; canonical `.1R.22` doc; status + changelog |
| 3 | `0f2bd4b5` | PBRD-001 v3.0 (MAJOR) §12a + §16 migration; PBNDE-001 v1.0 (new); PBPA-001 v1.1; NG-025 annotation; rdp docstring; DECISIONS versioning adjudication |
| 4 | `a6c1afdd` | 43-test defensive policy suite; `.1R.19R` contract-diff guard + 148c10 PBPA-version guard reconciliation |
| 5 | `ff96f7b1` | close implementation task → idle; expand idle allowed-file zone |
| 6 | `39d5c94f` | task-memory hygiene (stale idle + superseded phase task → `tasks/done/`) |
| 7 | `67525b62` | staged canonical completion metadata / report |
| 8 | `2377a230` | task-memory hygiene (reconciled idle file status → done) |
| 9 | `15aeb269` | governed push-state reconciliation (verification-entry head) |

Production scope since baseline (`git diff --name-only 8603fe6a HEAD -- src/pcae`):
**exactly** `src/pcae/core/permission_broker_foundation.py` and
`src/pcae/core/runtime_dispatch_permission.py`. No Gate 5/7/8/9/10 module, no
Slice-A/B module, no adapter, no runtime-introspection change
(`git diff --stat 8603fe6a HEAD` for each is empty).
Normative scope: **exactly**
`PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`,
`PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` (new),
`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`.

---

## 3. Verdict summary

| Component | Verdict |
|---|---|
| PBRD-001 v3.0 MAJOR trigger correctness (§16) | **VERIFIED** |
| PBRD-001 v3.0 explicit migration completeness / no auto-upgrade | **VERIFIED** |
| Legacy v2.x caller → no narrow-profile promotion, still POL-005 DENY | **VERIFIED** |
| Trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` classification (13 predicates, builder-only) | **VERIFIED** |
| Forged / transplanted / incomplete-marker → structural DENY | **VERIFIED** |
| Classification-recomputation completeness (every predicate fact recomputed live) | **VERIFIED** (see N-23-2 for a contract-wording note) |
| N-16-6 admission interface + fail-closed non-admitting production stub | **VERIFIED** |
| Private `_supply_chain_admission_resolver` override is not a production trust bypass | **VERIFIED** — no production call site passes it; the sole production builder call omits it |
| **Production profile unsatisfiability** | **VERIFIED** — two independent blockers (N-16-6 + N-16-5) |
| No production PB ALLOW for a real `runtime_dispatch` | **VERIFIED** |
| POL-005 amended semantics — exact one-profile carve-out; universal applicability retained | **VERIFIED** |
| POL-005 DENY `PolicyResult` body byte-identical | **VERIFIED** |
| POL-013 static never-ALLOW / never-HUMAN_REVIEW (AST) | **VERIFIED** |
| POL-013 dynamic vocabulary (`not-triggered` \| `DENY` only) + adapter-only applicability | **VERIFIED** |
| `_compose` / `_structural_request_failure` / `_decision` byte-unchanged; `DENY > HUMAN_REVIEW > ALLOW` intact | **VERIFIED** |
| Human authority alone never exempts POL-005 | **VERIFIED** |
| Broader effect classes (provider/network/credential/shell/arbitrary argv/wrong target/missing admission) all blocked | **VERIFIED** |
| NON_REAL / real-human-authority wall (N-16-5) — upstream, unchanged | **VERIFIED** |
| Gate-7 independence / runtime-capability identity / first-effect absence | **VERIFIED** |
| NG-025 annotation in the correct file; PBPA-001 v1.1 additive-only | **VERIFIED** |
| No test weakening in the `.1R.22` diff (0 removed defs, 0 xfail, 1 scoped skip) | **VERIFIED** |
| **Fixed-SHA A/B regression attribution / `.1R.22` verification-evidence completeness** | **BLOCKED — N-23-3** |

**Overall:** the N-16-3 policy model is substantively **INDEPENDENTLY
VERIFIED / closed-worthy**. The phase is **BLOCKED** on one defect: **16
functional guard-test nodes that pass at `8603fe6a` and fail at `15aeb269`,
attributable to the authorized `.1R.22` changes, that the `.1R.22` canonical
record neither reconciled nor disclosed** — directly contradicting its
"0 unexplained attributable functional regressions" (§12 / PROJECT_STATUS)
and "each was widened … and is listed here" (§11.1) claims.

---

## 4. PBRD §16 MAJOR trigger — independent re-derivation

PBRD-001 §16 (present verbatim at `8603fe6a`, in the v2.1 text) already
lists *"weakening POL-005 eligibility"* among the changes that *"require a
new MAJOR plus explicit migration and independent verification."* The new
§12a `RUNTIME_DISPATCH_LOCAL_CLI_V1` rule makes POL-005 return *not-triggered*
for one request class it previously matched categorically
(`ExecutionDisabledRule.evaluate` gains a second `_not_triggered` branch;
baseline had exactly one — the `simulation_only` branch). That **is**
"weakening POL-005 eligibility." **The v3.0 MAJOR is correct.** The `.1R.21`
planning artifact's provisional v2.2-MINOR adjudication was wrong; the human
operator's correction to v3.0 MAJOR matches primary source and is not merely
inherited here — it is independently re-derived. Repository convention
(RDGO v2→v3.0, PBRD v1.1→v2.0) carries a contract MAJOR inline in its
implementing phase, so no separate migration phase was required.

## 5. Migration completeness

PBRD-001 v3.0 §16 "explicit migration semantics" defines, at minimum:
v2.1 superseded-prior-MAJOR status; v3.0 as current canonical; v1.x/v2.x
authority-binding semantics have no migration; **v2.x request shapes remain
parseable but are categorically DENIED** (no `profile_classification`, no
N-16-6 admission sub-fields → POL-005 keeps its hard-DENY match, POL-013
DENYs on the missing predicates); **no silent auto-upgrade** (marker is
builder-derived only, from a complete predicate set); **classification
absence ⇒ the old POL-005 domain** (no compatibility default to the narrow
profile); sibling cross-reference refresh deferred to a normalization pass
(RDGO/RIHAC normative content does not depend on PBRD's version — a stale
"Related contracts" line is a reference-only lag); IV mandatory
(this phase). **No v2.x request can become `RUNTIME_DISPATCH_LOCAL_CLI_V1`
implicitly** — independently reproduced: `full_chain(simulation_only=False)`
yields `profile_classification == ""` and a POL-005 DENY.

## 6. Trusted-derived classification — predicate inventory (independently counted)

The predicate-id set was extracted directly from the AST of
`_narrow_local_cli_dispatch_v1_failed_predicates` (not from the report's
count):

| Predicate id | Normative req (PBNDE §3 / PBRD §12a.1) | Production check | Trusted producer | Caller-controllable? | Binding | Fail behaviour |
|---|---|---|---|---|---|---|
| `P_trusted_builder_seal` | seal-constructed | `request._runtime_dispatch_seal is _RUNTIME_DISPATCH_REQUEST_SEAL` | module sentinel | no | structural | DENY |
| `P_action_runtime_dispatch` | `action_type == runtime_dispatch` | envelope field | `_build_runtime_dispatch_permission_broker_request` | no | envelope | DENY |
| `P_execution_class_adapter` | `execution_class == adapter` | envelope field | same | no | envelope | DENY |
| `P_runtime_dispatch_context` | facts present + exact type | `type(facts) is RuntimeDispatchRequestFacts` | trusted builder | no | structural | DENY |
| `P_transport_local_cli` | `transport_type == local_cli` | `facts.transport_type` | trusted builder (const default; no input field) | no | structural | DENY |
| `P_network_prohibited` | `network_requirement == false` | `facts.network_requirement is not False` | `inputs.network_requirement` | value only | canonical digest (§5) + live recompute | DENY |
| `P_supply_chain_admission` | resolvable `local_fixed_argv` admission | `admission_class == local_fixed_argv and _sha256(admission_record_digest)` | N-16-6 resolver via trusted builder | **no** (`_validate_construction_inputs` rejects caller-preset fields) | canonical digest + live recompute | DENY |
| `P_human_authority_present` | approval present | `request.approval_present is True` | `project_human_authority_binding` (only path to `True`) | no | envelope | DENY |
| `P_human_authority_binding_valid` | RIHAC-001 v2.0 validated projection | `_generated_id(approval_id,"ria")` + two sha256 digests | `project_human_authority_binding` from a trusted `ValidatedAuthorityProjection` | no | structural + live recompute | DENY |
| `P_attempt_identity` | coordinator-minted `attempt_id` + `idempotency_key` | `_generated_id(attempt_id,"att")` + `_sha256(idempotency_key)` | gate-2 identity tracker | no | structural + live recompute | DENY |
| `P_runtime_target` | exactly one bound target | `_bounded_string(runtime_target_id,128)` | `inputs.runtime_target_id` | value only | canonical digest + live recompute | DENY |
| `P_filesystem_scope` | digest-bound scope ref | `type(scope) is RuntimeDispatchFilesystemScopeRef and _bounded_string(scope_id) and _sha256(scope_digest)` | `inputs.filesystem_scope_ref` | value only | canonical digest + live recompute | DENY |
| `P_trusted_profile_classification` | the derived marker itself (POL-013 only) | `facts.profile_classification == PROFILE_…_V1` | `derive_runtime_dispatch_local_cli_v1_classification` | no | see §7 | DENY |

**13 checked predicates.** The credential / provider / model / shell /
command-string exclusions (PBRD §6 "P5..P7") hold **by construction** — the
request model defines no such field — so their absence is structural, not a
runtime check. This matches PBNDE-001's design; the "P1..P21" numbering in
the contract is a superset label, and the operative conjunction is these 13.

## 7. Classification recomputation completeness (the decisive target)

The marker is **derived last** by
`build_runtime_dispatch_permission_broker_request`
(`derive_runtime_dispatch_local_cli_v1_classification(provisional)` → stamp
via `replace(facts, profile_classification=marker)`), and is **the only
write** of `profile_classification` in `src/pcae` (independently grep-verified).
`_validate_construction_inputs` rejects any caller that pre-sets
`admission_record_digest` / `admission_class`.

**Recomputation relation, independently proven:**
`_valid_runtime_dispatch_request` (run first, inside
`_structural_request_failure`, before any policy) calls
`_narrow_local_cli_dispatch_v1_failed_predicates(request, check_marker=False)`
against the **live** request state and enforces:
* `marker ∉ {"", PROFILE_…_V1}` → DENY;
* `marker == PROFILE_…_V1` **and** profile incomplete → DENY;
* `marker == ""` **and** profile complete → DENY (a "complete profile that
  lacks the trusted marker" — the admission-field-forgery case).

Every predicate-relevant fact is re-read live, so a post-construction
mutation of any of them (via `dataclasses.replace` on the sealed request,
which preserves the seal) that breaks the profile is a **structural DENY**;
a mutation that strips the seal defeats `_is_trusted_narrow_local_cli_dispatch_v1`
and re-triggers POL-005's DENY. Independently reproduced across 8 distinct
predicate mutations (IV suite `test_every_predicate_fact_is_recomputed_live`,
`test_marker_survives_replace_but_stripping_the_seal_defeats_the_carveout`).

**Digest-binding matrix.** The N-16-6 admission sub-fields are now part of
`canonical_runtime_dispatch_projection` → they feed `idempotency_key`
(independently reproduced: `k_prod != k_adm`). `network_requirement`,
`runtime_target_id`, `filesystem_scope_ref`, `idempotency_key`, `attempt_id`
are digest-bound. `transport_type`, the seal, `action_type`,
`execution_class` are structurally fixed by the builder. **No narrow-profile
predicate is unbound** — each is either in the canonical digest or
structurally fixed **and** all are recomputed live.

## 8. Production unsatisfiability — two independent blockers

**B1 (N-16-6).** `_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER` is
`_NonAdmittingSupplyChainAdmissionResolver`, which returns
`SupplyChainAdmissionResult(admitted=False, admission_record_digest="",
admission_class="unadmitted")` for **every** adapter id. `_resolve_supply_chain_admission`
additionally fails closed on a non-`SupplyChainAdmissionResolver`, a raising
resolver, a non-`SupplyChainAdmissionResult`, or an admitting result with a
malformed/empty class. → `P_supply_chain_admission` **always fails** in
production → marker never derived.

**B2 (N-16-5).** There is **no path — production or test — to a trusted
`ValidatedAuthorityProjection`**: `runtime_authority.validate_approval`
deliberately rejects every caller-supplied approval object
(`noncanonical_approval_reference:caller_supplied_object`), and
`project_human_authority_binding` is the *only* function that can set
`approval_present=True`, and only from such a trusted projection. →
`P_human_authority_present` / `P_human_authority_binding_valid` **always
fail** for a real request. Independently reproduced: even with a synthetic
admitting resolver (`_AdmittingResolver`, identity minted with the same
resolver so the idempotency key matches), the builder still yields
`profile_classification == ""` and `approval_present is False`.

**Private override is not a bypass.** `_supply_chain_admission_resolver` is
an underscore-private kwarg on three functions, default `None`. **No
production call site passes it** (grep-verified — the only two `src/pcae`
occurrences are internal pass-throughs of the same-named parameter, both
defaulting to `None`). The **sole production call** to
`build_runtime_dispatch_permission_broker_request` is
`run_gate6_permission_broker` (line ~993 of `runtime_dispatch_permission.py`),
which does **not** pass the override. So even setting B2 aside, no
production code can flip an adapter to `admitted`.

**No production PB ALLOW.** For a real production `runtime_dispatch`,
`_compose` returns DENY (`causing_policy_ids` includes `POL-005`). The
`_compose` INV-008 default ALLOW (`policy_would_allow_if_execution_existed`,
`implementation_status = EXECUTION_UNAVAILABLE`) **is** structurally
reachable for a *structurally-complete* profile with nothing else triggering
— see **N-23-1** — but that state is unreachable in production (B1 + B2),
contract-sanctioned as non-executable (PBRD §12a.4/.5), and every downstream
gate (7–10) plus runtime-unavailable independently blocks any effect.

## 9. POL-005 / POL-013 / `_compose`

* **POL-005 DENY body byte-identical** to `8603fe6a`
  (`decision_reason="execution_boundary_unavailable"`, `NG-025`, `INV-001`,
  `COMP-002`, identical remediation). The only change is the carve-out `if`
  before it. `applicable_execution_classes` stays `None` (universal).
* **The carve-out predicate `_is_trusted_narrow_local_cli_dispatch_v1` reads
  ONLY** `runtime_dispatch_context.profile_classification == PROFILE_…_V1`
  and the construction seal — no caller field, no shape inference
  (source-verified).
* **POL-013 static analysis (AST):** `evaluate` has exactly two return
  shapes — `_not_triggered(...)` and a `PolicyResult(decision=DECISION_DENY,
  …)`. No `DECISION_ALLOW` / `DECISION_HUMAN_REVIEW` name or `"ALLOW"` /
  `"HUMAN_REVIEW"` constant appears in the rule's code (docstrings stripped).
  **POL-013 can never emit ALLOW or HUMAN_REVIEW.**
* **POL-013 dynamic:** complete profile → `not-triggered`; each predicate
  gap → `DENY` with `decision_reason == "narrow_local_cli_dispatch_profile_incomplete"`;
  `simulation_only=True` / non-`runtime_dispatch` adapter request → no-op.
  Applicability `frozenset({EXECUTION_CLASS_ADAPTER})`; registered last;
  `POLICY_IDS_CANONICAL == {POL-001..013}`; `PolicyRegistry()` completeness
  check still passes.
* **`_compose`, `_structural_request_failure`, `_decision` byte-unchanged**
  since `8603fe6a` (whole-function diff empty). `DENY > HUMAN_REVIEW > ALLOW`
  intact; a co-present DENY dominates a complete profile; a lone POL-013
  `not-triggered` casts no ALLOW vote.
* **Human authority alone never exempts POL-005** — `approval_present=True`
  with an invalid profile → DENY (reproduced).

## 10. Broader effect classes / bindings / NON_REAL wall

Provider/API transport, `network_requirement=True`, unadmitted supply chain,
wrong `admission_class`, empty `runtime_target_id`, invalid human-authority
binding — **each independently → DENY**. Runtime-target / attempt /
idempotency-key / filesystem-scope mutation on a marked request → structural
DENY. `runtime_authority.py` is **not** among the `.1R.22` changed files —
the NON_REAL / real-human-authority wall (N-16-5) is upstream and unchanged.

## 11. Gate independence / runtime posture / NG-025 / PBPA

* Gate 5/7/8/9/10 modules **byte-unchanged** since `8603fe6a`
  (`git diff --stat` empty for each). POL-005 (Gate-6 policy) does not read
  Gate-7 positive state — N-16-4 remains independent.
* `pcae runtime inspect`: `not_implemented / Observed / observe / unavailable`;
  registry empty; 0 plugins / 0 capabilities. **Unchanged.**
* No first-effect primitive (`adapter.dispatch(`, `subprocess`, `socket`,
  `Popen`, `os.system`, `urllib`, `requests`, `httpx`) added in the touched
  modules (added-line scan of the `8603fe6a..HEAD` `src/pcae` diff).
* NG-025 annotation is in `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
  (not the RE No-Go Registry); it is an additive canonical-statement
  annotation, "Human override remains `no`", schema/verdict unchanged.
* PBPA-001 v1.1: additive `POL-013` row (`{ADAPTER}` scoped); PBPA-REQ-062
  count 1→2 scoped; PBPA-REQ-089 (first exercise of PBPA-REQ-087). No
  existing row's applicability class changed.

## 12. Fixed-SHA A/B and regression attribution — THE BLOCKER (N-23-3)

**Baseline:** `git worktree add <wt> 8603fe6a`. **HEAD:** `15aeb269`.
Deterministic, no xdist. B (`15aeb269`) and C (`origin/main`) are the same
commit — `git rev-parse HEAD origin/main` identical — so B ≡ C, no
origin-relative node class.

**Substantive suites — 0 attributable regressions.** New IV suite (55) +
`.1R.22` narrow-eligibility suite (43) + `runtime_dispatch_permission` +
`runtime_dispatch_regression_pb_actions` +
`permission_broker_policy_applicability` +
`permission_broker_policy_composition_hardening` +
`permission_broker_verification_compatibility` +
`runtime_authority_pb_[re]verification` +
`runtime_authority_production_repair` + Gate 5/9/10 + Slice-A/B + `.1R.11` /
`.1R.15.2` / `.1R.15.5` / `.1R.17*` / `.1R.18` / `.1R.19*` / `.1R.20` +
PBPC 148c10: **all green at HEAD** (1 397 nodes across the two batches).

**Known pre-existing failures (reproduce identically at `8603fe6a` — 0 A/B
delta), matching the `.1R.22` §12 disclosure:**
* `…_1r13.py::test_no_downstream_production_consumer_of_gate6_symbols`
* `test_runtime_authority_pb_verification_3w1.py::test_only_content_bound_projection_registry_is_added_to_authority_module`
  (expects `runtime_dispatch_permission.py` to carry no module-level mutable;
  `_GATE6_DECISIONS` — a `.1R.12` addition — already violates it; `.1R.22`
  adds no new module-level mutable)
* `test_phase_148f_…::test_permission_broker_consumer_scope_inventory`
* `test_phase_148g2_…::test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`

**N-23-3 — 16 undisclosed `.1R.22`-attributable functional guard-test
failures.** Each **passes at `8603fe6a` and fails at `15aeb269`**
(re-run individually at both SHAs to confirm; not order-dependent). None
appears in the `.1R.22` artifact §11.1 guard-impact inventory (the file
basenames are absent from the whole `.1R.22` doc) or in the §12 disclosure.
They are all stale point-in-time **text/count freeze** guards made red by
the two authorized changes — not behavioural regressions of the Permission
Broker — but they are real failing nodes that the `.1R.22` record's
"0 unexplained attributable functional regressions" and "each was widened …
and is listed here" claims positively exclude.

| # | Node | Root cause (authorized change) |
|---|---|---|
| 1 | `test_permission_broker_policy_rule_framework.py::test_registry_has_twelve_policies` | POL-013 added → registry is 13 |
| 2 | `test_permission_broker_policy_rule_framework.py::test_policy_ids_are_stable_and_ordered` | POL-013 added |
| 3 | `test_permission_broker_policy_rule_framework.py::test_broker_evaluated_policy_ids_equal_applicable_policy_set` | POL-013 (adapter-scoped) changes the applicable set |
| 4 | `test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_even_when_one_triggers` | rule-count assumption |
| 5 | `test_permission_broker_policy_rule_framework.py::test_registry_evaluates_all_rules_every_time` | rule-count assumption |
| 6 | `test_permission_broker_observation_verification.py::test_broker_default_policy_rule_count_unchanged` | `len(DEFAULT_POLICY_RULES)` 12→13 |
| 7 | `test_phase_149d_rwmpc_contract_independent_verification.py::TestContractsUnamended::test_pbpc_and_pbpa_contract_files_unchanged_since_before_chapter_149` | PBPA-001 v1.0→v1.1 byte change |
| 8 | `test_phase_149o_16_hatp_…::test_pol_005_denies_unconditionally_when_simulation_only_false` | POL-005 `evaluate` body grew (carve-out `if`); brittle text-window grep |
| 9 | `test_phase_149o_18c_…::TestContractByteIdentity::test_contract_byte_unchanged[PBPA]` | PBPA-001 byte change |
| 10 | `test_phase_149o_18d_…::TestContractByteIdentity::test_contract_byte_unchanged[PBPA]` | PBPA-001 byte change |
| 11 | `test_phase_149o_18e_…::TestContractByteIdentity::test_contract_byte_unchanged[PBPA]` | PBPA-001 byte change |
| 12 | `test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py::test_upstream_contract_byte_unchanged_by_this_repair[PBPA]` | PBPA-001 byte change |
| 13 | `test_phase_149o_20l_7o_3v_1r_1_contract_verification.py::TestBoundariesUnchanged::test_pol_005_unchanged_claim_present` | PBRD "POL-005 … UNCHANGED" line reworded |
| 14 | `test_phase_149o_20l_7o_3v_1r_contract_repair.py::TestNoNewContradictions::test_no_go_statements_preserved` | PBRD NG-statement text edits |
| 15 | `test_trusted_approval_presentation_hpac_proof_lifecycle_canonicalization_repair_3w1r2b1r111r.py::test_pbrd_remains_projection_only_and_pol005_remains_hard_deny` | PBRD "POL-005 production behavior: UNCHANGED" line reworded |
| 16 | `…_3w1r2b1r111r.py::test_rpac_companion_contract_is_byte_identical_and_riasc_pbrd_only_normalized` | PBRD v2.1→v3.0 header/body |

Encoded in the IV suite as
`R122_UNDISCLOSED_ATTRIBUTABLE_GUARD_REGRESSIONS` with
`test_r122_artifact_does_not_disclose_these_regressions`,
`test_count_is_sixteen_…`, and
`test_ab_delta_is_exactly_these_sixteen_when_a_baseline_worktree_is_available`.

**Why this blocks (§75).** "An undisclosed scope-fence/meta-guard regression
attributable to `.1R.22` is found." This is the identical failure mode that
BLOCKED `.1R.18` (17 undisclosed `.1R.17` guard regressions → `.1R.17R`)
and `.1R.20` (3 undisclosed `.1R.19` guard regressions → `.1R.19R`).
Repairing it requires editing guard **test** files across ≥9 phases
(widen count/version/byte-freeze assertions to the authorized POL-013 /
PBPA-v1.1 / PBRD-v3.0 set, no wildcard, each still rejecting an
unauthorized change) — reconciliation work that belongs in a dedicated
repair phase with its own authorization, not this IV phase (§82: "Do not
modify … Do not begin …"). `.1R.23` does not repair it.

## 13. No test weakening in the `.1R.22` diff

`git diff 8603fe6a HEAD -- tests/`: **0** removed `def test_`; **0** added
`xfail`; **1** added `pytest.skip` — a scoped byte-freeze reconciliation in
`test_runtime_authority_production_repair_3w1r2b1r1117.py` limited to exactly
3 authorized paths (2 contracts + `permission_broker_foundation.py`), no
wildcard, the guard still enforces byte-identity for every other file. No
`def test_` renamed. The 20 guard files `.1R.22` **did** reconcile (§11.1)
each still carry a `forbidden`/adversarial companion that trips on an
unauthorized change (spot-checked at HEAD — all green).

## 14. `.1R.22` 43-test suite review

Substantive and largely well-targeted. Disclosed design choice: the
"structurally complete profile" cases (12–15, 27, 28, 30) seal the request
directly (`_build_runtime_dispatch_permission_broker_request` + a manually
stamped marker, after asserting `_failed(prov, check_marker=False) == ()`)
rather than driving `build_runtime_dispatch_permission_broker_request`,
because there is no path to a trusted `ValidatedAuthorityProjection`. This
is a reasonable POLICY-isolation choice and is stated in the helper
docstring; production-path unsatisfiability is separately covered
(cases 24, 24b, 33). `test_case_12` correctly asserts the complete-profile
INV-008 ALLOW with `implementation_status == EXECUTION_UNAVAILABLE`
(consistent with N-23-1). No test merely mirrors an implementation constant
in a way that would mask a defect. **The suite's gap is not in what it
asserts but in the A/B completeness claim it backs (N-23-3).**

## 15. New findings

* **N-23-1 (informational).** A structurally-complete (test-constructed,
  sealed) `RUNTIME_DISPATCH_LOCAL_CLI_V1` request with no other policy
  triggering composes to the `_compose` INV-008 default
  `DECISION_ALLOW` / `policy_would_allow_if_execution_existed` /
  `implementation_status = EXECUTION_UNAVAILABLE`. This is
  **contract-sanctioned** (PBRD §12a.4 "SHALL NOT by itself produce ALLOW";
  §12a.5 "ALLOW still means only §2's bounded statement"; gates 7–10 each
  independently gate the effect), explicitly **non-executable** (INV-008),
  and **unreachable in production** (B1 + B2). Not a defect — but the plain
  statement "the narrow profile never reaches ALLOW" is only true *in
  production*; a complete profile *does* reach the non-executable INV-008
  ALLOW. No production or contract change warranted.
* **N-23-2 (informational, contract-wording).** PBNDE-001 §3 and PBRD-001
  v3.0 §12a.1 say the marker is *"committed into the request canonical
  digest (§5)."* It is **not** literally in the digest —
  `canonical_runtime_dispatch_projection` has no `profile_classification`
  field. PBRD §5's "v3.0 — derived commitments" paragraph describes the
  **actual** mechanism correctly ("bound by a stronger mechanism than digest
  inclusion: the trusted structural validator recomputes it … and fails
  closed on any inconsistency"). The implemented mechanism (live
  recomputation in `_valid_runtime_dispatch_request`) is at least as strong
  as digest inclusion. Wording inconsistency only; no behavioural defect.
  A future normalization pass should align §3 / §12a.1 with §5.
* **N-23-3 (BLOCKER).** See §12 — 16 undisclosed `.1R.22`-attributable
  functional guard-test failures; the `.1R.22` "0 unexplained attributable
  functional regressions" / "each … listed here" claims are false.

## 16. Contract-production equivalence (spot matrix)

| Normative token | Contract | Production symbol |
|---|---|---|
| `RUNTIME_DISPATCH_LOCAL_CLI_V1` | PBRD §12a / PBNDE §3 | `PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1` |
| POL-005 §12a carve-out | PBNDE §2 | `ExecutionDisabledRule.evaluate` + `_is_trusted_narrow_local_cli_dispatch_v1` |
| POL-013 | PBNDE §4 / PBPA §17 | `NarrowLocalCliDispatchEligibilityRule` (`policy_id="POL-013"`) |
| `local_fixed_argv` admission | PBNDE §5 | `ADMISSION_CLASS_LOCAL_FIXED_ARGV` |
| fail-closed non-admitting N-16-6 stub | PBNDE §5 | `_NonAdmittingSupplyChainAdmissionResolver` / `_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER` |
| structural recompute-and-reject | PBRD §5 / PBNDE §3 | `_valid_runtime_dispatch_request` |
| `narrow_local_cli_dispatch_profile_incomplete` | PBRD §12a.3 | POL-013 `decision_reason` |

## 17. Adjudications

* **N-16-3 — PARTIALLY CLOSED.** The policy model, trusted derivation,
  caller-bypass resistance, POL-005 exact carve-out, POL-013 never-positive
  behaviour, old-caller denial, and **production unsatisfiability** are all
  independently verified. **Not fully CLOSED** solely because of N-23-3
  (undisclosed attributable guard-regression debt). Closure follows `.1R.22R`.
* **PBRD-001 v3.0 MAJOR MIGRATION — VERIFIED.**
* **POL-005 NARROW MATCH-DOMAIN EVOLUTION — VERIFIED** (one exact
  trusted profile excluded; every other prior domain hard-DENY; no caller
  self-classification bypass).
* **POL-013 — VERIFIED; NEVER EMITS ALLOW OR HUMAN_REVIEW.**
* **`RUNTIME_DISPATCH_LOCAL_CLI_V1` PRODUCTIONALLY UNSATISFIABLE — VERIFIED**
  (two independent blockers: N-16-6 non-admitting resolver; N-16-5 absent
  real human authority).
* **`.3` delegated finalization / commit / push — remains UNAUTHORIZED**
  (preserved verbatim; creates no precedent).

## 18. Remaining prerequisite posture

`N-16-4`, `N-16-5`, `N-16-6`, `N-16-7`: **OPEN.** Slice C / Slice D: **no
phase ID.** First external effect: **ABSENT.**

## 19. Final verdict

**BLOCKED INDEPENDENT-VERIFICATION RESULT (Option B).** The N-16-3
Narrow-Eligibility Policy is **substantively INDEPENDENTLY VERIFIED /
closed-worthy**; acceptance is **BLOCKED** on **N-23-3** and referred to
`149O.20L.7O.3W.1R.2B.1R.1.1R.22R`.

## 20. Required human decision

Authorize **`149O.20L.7O.3W.1R.2B.1R.1.1R.22R` — N-16-3 Scope-Fence /
Verification-Evidence Reconciliation and Repair**: widen the 16 stale
point-in-time guard assertions (registry cardinality → 13; PBPA-001
byte-freeze → v1.1; PBRD/POL-005 text-freeze → v3.0 wording) to the exact
authorized change set, no wildcard, each still rejecting an unauthorized
change; issue a provenance-preserving `.1R.22` §11/§12 erratum correcting
the "0 unexplained attributable functional regressions" / "each … listed
here" claims to the true "16 attributable, non-behavioural, referred to
`.1R.22R`"; no production or normative-contract change. Then
`149O.20L.7O.3W.1R.2B.1R.1.1R.22R.1` — Independent Verification of that
reconciliation — before N-16-4. **Do not skip to N-16-4.**

## 21. Repository state

* Verification-entry SHA: `15aeb269` — `HEAD == origin/main`,
  `origin/main..HEAD = 0` at entry and (after governed finalization of this
  BLOCKED report) at exit.
* Production source / normative contracts / scope-fence guards modified by
  `.1R.23`: **none.**
* Added by `.1R.23`: `tests/test_narrow_eligibility_policy_iv_3w1r2b1r1_1r23.py`
  (55 tests, all green), this artifact, `PROJECT_STATUS.md` /
  `CHANGELOG.md` / task-lifecycle / `.pcae` completion metadata.
* `.1R.23` commits: see the governed `pcae` phase report.
