# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3 Narrow-Eligibility Policy and Contract Implementation

**Type:** implementation (policy + contract; MAJOR contract evolution).
**Status:** COMPLETE — N-16-3 IMPLEMENTED, INDEPENDENT VERIFICATION PENDING `.1R.23`.
**Phase-entry SHA:** `8603fe6a` (`origin/main` synced; `origin/main..HEAD = 0` at entry).
**Execution:** NOT enabled. Runtime remains `not_implemented / Observed / observe / unavailable`;
0 plugins / 0 capabilities; deterministic authentication remains NON_REAL.
**First external effect:** ABSENT — no `adapter.dispatch(` call site anywhere in `src/pcae`.
**Governance:** governed `pcae` lifecycle only. The historical delegated `.3`
finalization / commit / push incident remains **UNAUTHORIZED — preserved**.
Only the primary human-authorized operator holds `.1R.22` lifecycle authority.

This is the canonical artifact required by the phase prompt §79 / §81. The
final report is §20.

---

## 1. Governing baseline and the versioning adjudication

### 1.1 Frozen architecture (`.1R.21`)

The authoritative plan is **`.1R.21` — N-16-3 Local-CLI Narrow-Eligibility
Policy and Contract Planning**. Re-read in full at phase entry. The selected
model (**Option C + D**) is implemented unchanged:

1. a trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` execution profile;
2. that exact profile lies **outside** POL-005's categorical hard-block match
   domain (Option C — a versioned POL-005 canonical-statement amendment);
3. a dedicated conjunctive **`POL-013`** validates the full predicate
   conjunction (Option D);
4. `POL-013` **never** emits `ALLOW` (and never `HUMAN_REVIEW`);
5. any missing / malformed / untrusted / broader predicate → `POL-013` `DENY`
   **and** POL-005 retains its hard-DENY match;
6. every other PB policy still evaluates normally;
7. no human-approval override (`if human_approved: ignore POL-005` and
   `trusted principal → ALLOW` both remain rejected — §6);
8. no positive production path — the profile is **unsatisfiable in
   production** because the N-16-6 supply-chain admission binding has no
   admitting implementation (§9).

### 1.2 Versioning adjudication (human-authorized correction to `.1R.21`)

`.1R.21` §31 / §34 planned the PBRD-001 change as **v2.2 (MINOR)**. During
`.1R.22` primary-source review this was found to conflict with **PBRD-001
v2.1 §16** ("Versioning"), which lists **"weakening POL-005 eligibility"**
among the changes that **"require a new MAJOR plus explicit migration and
independent verification."** §12a is exactly the clause that narrows POL-005's
categorical match domain. The phase prompt §5 directs: *"If repository
policy-version conventions require a different formal mechanism: STOP and
report."*

The phase was **BLOCKED at primary-source review** (before any repository
mutation) and the human operator adjudicated:

> **Carry N-16-3 as PBRD-001 v3.0 — MAJOR**, and expand `.1R.22` authorization
> only as necessary to satisfy PBRD §16's required explicit migration +
> independent-verification mechanics. Do not implement the v2.2 MINOR path.
> Rationale: §16 explicitly lists "weakening POL-005 eligibility" as a MAJOR
> trigger; `.1R.22` changes POL-005 from universal effecting-request hard DENY
> to a model with one narrowly trusted-derived carve-out; even though §12
> anticipated a future narrow-eligibility rule, the operative contract meaning
> still changes, so the contract's own versioning rule controls; a v2.2
> artifact would reasonably be classified by future verification as violating
> §16.

Repository convention for a contract MAJOR was checked: **RDGO-001 v2 → v3.0**
(a load-bearing gate-semantics MAJOR) was carried **inline** in its
implementing/freeze phase, with the migration statement in the contract's own
"Versioning and freeze verdict" section and the independent verification in a
separate paired phase. **PBRD-001 v1.1 → v2.0** (the `human_authority_binding`
meaning MAJOR) was likewise carried inline in a freeze phase. **No
separate-migration-phase convention exists** — so the migration artifact is
authored inline in `.1R.22` and the independent verification is `.1R.23`, per
the human authorization. `.1R.22` therefore did **not** re-STOP.

### 1.3 Corrected NG-025 annotation target

`.1R.21` §38 listed the NG-025 canonical-statement annotation against
`docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`. That file is the `RE-NOGO-NNN`
registry and contains **no `NG-025`**. `NG-025` ("Execution Boundary
Unavailable") is owned by **`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`**
("PCAE v0.2 Execution Readiness No-Go Gates", `NG-001`..`NG-025`). `.1R.21`'s
target is recorded as a **planning-document location error**; the annotation
is applied to the actual canonical owner. No unrelated `RE-NOGO-*` entry was
created to match the mistaken path (primary-source cross-reference rules do
not require an annotation in both places — the two registries are additive and
independent, and NG-020's "dedicated, explicit amendment phase" requirement
for a registry change is satisfied by `.1R.22` itself).

---

## 2. Primary sources inspected

Read in full unless noted:

- `.1R.21` planning artifact (all 1399 lines) — frozen Option C + D model.
- `.1R.16` planning artifact (versioning-relevant sections; §35/§36.2/§38) —
  defers the versioning *mechanism* to N-16-3.
- `.1R.19R.1` canonical report + completion metadata (Slice-B closure).
- `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001 v2.1),
  §§0–17 incl. §12 verbatim and §16 verbatim.
- `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
  (PBPA-001 v1.0), §§4A, 8–18, 22–24, 29–31, and the POL-001..012 matrix
  (PBPA-REQ-034 — `action_type` is not an applicability input; PBPA-REQ-060/062
  — the matrix is normative; PBPA-REQ-087 — a scoped-set change is a versioned
  contract amendment).
- `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (RE-NOGO schema 1.1) — full.
- `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-001..025) — NG-020,
  NG-024, NG-025, header, human-override posture.
- `docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md` — POL registry,
  precedence, identifiers, extension model.
- `src/pcae/core/permission_broker_foundation.py` (all 1123 lines) —
  `ExecutionDisabledRule` (POL-005), `_compose`, `PolicyRegistry`
  (`POLICY_IDS_CANONICAL`), `RuntimeDispatchRequestFacts`,
  `RuntimeDispatchAdapterDescriptorBinding`, `_valid_runtime_dispatch_request`,
  `_RUNTIME_DISPATCH_REQUEST_SEAL`, `_structural_request_failure`.
- `src/pcae/core/runtime_dispatch_permission.py` (all 881 lines) —
  `build_runtime_dispatch_permission_broker_request` (sole trusted builder /
  seal holder), `canonical_runtime_dispatch_projection`,
  `new_runtime_dispatch_identity`, `project_human_authority_binding`,
  `run_gate6_permission_broker`.
- `src/pcae/core/runtime_authority.py` — `compute_canonical_digest`.
- `src/pcae/core/policy.py` — confirmed it does **not** enumerate POL IDs, so
  it is not touched (`.1R.21` §39's "if it lists POL IDs" — it does not).
- `src/pcae/core/runtime_dispatch_gate7.py` — Gate-7 projection digest
  (out of scope; read-only, to confirm no `.1R.22` change is required there).
- `src/pcae/core/runtime_invocation_authority_consumption.py` — `pb_binding`
  key set (out of scope; confirms transitive digest coverage).

---

## 3. Contract evolution — PBRD-001 v3.0 (MAJOR) with explicit migration

Authored this phase: `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (header →
PBRD-001 v3.0; new §12a; §16 rewritten with the v3.0 MAJOR rationale + the
six-point explicit migration semantics + §17 non-goal update; §4 fact 8 + §5
derived-commitment notes; freeze verdict); new
`PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` (PBNDE-001 v1.0);
`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` (header → v1.1; POL-013
matrix row; PBPA-REQ-062 count; new PBPA-REQ-089);
`V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-025 annotation). The mechanical
`PBRD-001 v2.1` → `v3.0` "Related contracts" edits in RDGO-001 / RIHAC-001 and
their siblings are **deferred to a dedicated contract-normalization pass**
(the `.1R.15.4` precedent) — each of those contracts is byte-frozen by ~50
point-in-time assertions in the RIHAC/HPAC contract-freeze suites, and a
cross-reference bump there is out of `.1R.22`'s authorized scope; PBRD-001
v3.0 §16 point 5 records this normatively. The
`runtime_dispatch_permission.py` module docstring PBRD reference is updated in
this phase.

### 3.1 PBRD-001 v2.1 → v3.0

`docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`:

| Aspect | v2.1 (superseded) | v3.0 (canonical) |
|---|---|---|
| Contract identity | v2.1, FROZEN | **v3.0, FROZEN** |
| Supersession | supersedes v1.0/v1.1 | supersedes v1.0/v1.1/**v2.x** |
| §12 (POL-005 evolution boundary) | "POL-005 unchanged … denies every truthful non-simulation request" | retained, plus a pointer to the now-defined §12a rule |
| **§12a (new)** | — | the `RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow-eligibility rule (the exact text `.1R.21` §31 froze) |
| §16 (Versioning) | v2.1 is MINOR; "weakening POL-005 eligibility … requires a new MAJOR plus explicit migration and independent verification" | **v3.0 is that MAJOR** — the migration semantics are stated in §16 itself (§3.2 below); the `.1R.23` IV is the mandated independent verification |
| §4 fact 8 | closed object: 4 fields | plus additive **internal** `admission_record_digest` / `admission_class` (N-16-6 evidence; trusted-builder-populated only) |
| §4 (facts) | fourteen logical facts | fourteen logical facts **unchanged** + one derived non-caller commitment `profile_classification` (not a fifteenth logical fact) |
| §5 (canonical digest) | "over the complete Foundation envelope plus all fourteen facts" | plus the derived commitments — bound both in the canonical-content digest (`idempotency_key`, for the admission sub-fields) and by structural recompute-and-reject at validation (for `profile_classification`) |

### 3.2 Explicit migration semantics (PBRD §16, v3.0)

Authored inline in the contract's §16, per repository convention and the
human authorization:

- **PBRD-001 v2.1 is the superseded prior MAJOR line.** v1.0 / v1.1 / v2.x
  authority bindings have no migration (v2.0 already established this for
  v1.x; v3.0 extends it to v2.x for the POL-005-eligibility semantics).
- **PBRD-001 v3.0 is the new canonical contract.**
- **Existing v2.x request shapes remain parseable.** A v2.x-shaped
  `runtime_dispatch` request (no `profile_classification`, no admission
  sub-fields) is structurally valid and is **categorically DENIED** under the
  new narrow-profile rules: `profile_classification == ""` →
  `_is_trusted_narrow_local_cli_dispatch_v1` is `False` → POL-005 keeps its
  hard-DENY match; and `POL-013` DENYs on the missing predicates. No v2.x
  request is silently auto-upgraded into `RUNTIME_DISPATCH_LOCAL_CLI_V1` — the
  marker is derived by the trusted builder only, and legacy callers of the
  generic `build_permission_broker_request` still cannot construct a
  `runtime_dispatch` request at all.
- **No implicit migration / no compatibility default to the narrow profile.**
  Classification absence means the old POL-005 domain.
- **Current-version cross-references move to v3.0.** The PBRD-001 version
  string in `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` and
  `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` "Related contracts" lines,
  and in `runtime_dispatch_permission.py`'s module docstring, are updated to
  `PBRD-001 v3.0`. RDGO-001's normative semantics are unchanged (RDGO §20
  still disclaims "relax POL-005"; a non-triggered POL-005 for `…_V1` is not a
  DENY, so RDGO §7's "`DENY` … stops the flow" is unaffected).
- **Independent verification is mandatory** and is `.1R.23`.

### 3.3 New policy contract — PBNDE-001 v1.0

`docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md`
(PBNDE-001 v1.0, "Permission Broker Narrow Local-CLI Dispatch Eligibility
Contract") freezes:

- the **POL-005 canonical-statement v2 amendment** — POL-005 **retains its
  ID** (`POL-005`) for audit-trail continuity (every prior
  `causing_policy_ids=("POL-005",)` decision stays interpretable); the
  amendment is explicit, dated, MAJOR-class, and IV'd in `.1R.23`;
- the **`POL-013` — Narrow Local-CLI Dispatch Eligibility** definition:
  applicable only to `execution_class == adapter`; within that class its
  *trigger* is further restricted to `action_type == runtime_dispatch` and
  `simulation_only is False` (mirroring POL-005's own domain; PBPA-REQ-034
  forbids `action_type` as an *applicability* input, so this is a trigger
  condition, not an applicability filter); the full P1–P21 predicate
  conjunction; **never `ALLOW`, never `HUMAN_REVIEW`**; DENY reason
  `narrow_local_cli_dispatch_profile_incomplete`;
- the **`RUNTIME_DISPATCH_LOCAL_CLI_V1` trusted-derivation** requirement —
  the classification is derived by
  `build_runtime_dispatch_permission_broker_request` from the bound facts and
  is never a caller field; `_valid_runtime_dispatch_request` recomputes it and
  fails closed on any inconsistency (including a "complete profile without the
  trusted marker" forgery);
- the **N-16-6 admission interface** requirement — a resolvable canonical
  supply-chain admission binding of class `local_fixed_argv`; the only
  production implementation is the fail-closed **non-admitting** resolver, so
  the profile is unsatisfiable in production;
- the **test-boundary isolation** rule — the `_supply_chain_admission_resolver`
  argument is underscore-private, documented test-only, and is the exact
  substitution boundary; no public production parameter can set `admitted`.

### 3.4 PBPA-001 v1.0 → v1.1

`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`: additive
amendment (per PBPA-REQ-087, a scoped-set change is a versioned contract
amendment with its own version increment and independent re-verification):

- POL-001..012 matrix (§17) → **POL-001..013**; new row:
  `POL-013 | Narrow Local-CLI Dispatch Eligibility | runtime-dispatch/adapter policy surface | {EXECUTION_CLASS_ADAPTER} | Scoped | PBNDE-001 v1.0; the trigger narrows to action_type=runtime_dispatch inside the adapter class (evaluate() condition, not applies_to — PBPA-REQ-034)`;
- PBPA-REQ-062 count language updated: **two** currently-implemented scoped
  policies (`POL-004`, `POL-013`);
- new PBPA-REQ documenting that `POL-013` is a no-op for any request that is
  not a truthful, sealed, non-simulation `runtime_dispatch` request (the dry
  `adapter_invocation` / `simulation_only=true` path is untouched);
- versioning note recording this as the first exercise of PBPA-REQ-087.

### 3.5 NG-025 annotation

`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`: an additive annotation to
NG-025's canonical statement (schema unchanged; parallels the schema-1.1
V-13-3-2 precedent) —

> NG-025 is unconditionally active for every non-simulation request **except
> the single trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` execution
> profile** defined by PBRD-001 v3.0 §12a and PBNDE-001 v1.0, which is
> productionally unsatisfiable pending N-16-4..7. Human override remains `no`.

### 3.6 Contract evolution manifest

| Artifact | Old | New | Semantic change | Finding addressed | Compatibility | Dependent refs updated |
|---|---|---|---|---|---|---|
| `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | PBRD-001 v2.1 | **PBRD-001 v3.0 (MAJOR)** | §12a narrow-eligibility rule; POL-005 categorical domain gains one trusted-derived carve-out; two additive internal derived fields | N-16-3; §16 MAJOR trigger | v2.x requests parseable but categorically DENIED; no auto-upgrade | RDGO-001 §"Related contracts"; RIHAC-001 §"Related contracts"; `runtime_dispatch_permission.py` docstring |
| `PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` | — (new) | **PBNDE-001 v1.0** | defines POL-005 v2 amendment + POL-013 + `…_V1` profile + N-16-6 interface | N-16-3 | additive | PBPA-001 §17; NG-025 annotation |
| `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` | PBPA-001 v1.0 | **PBPA-001 v1.1 (additive)** | POL-013 applicability row (`{adapter}`, scoped); PBPA-REQ-062 count | N-16-3 (POL-013 registration) | additive; no existing row changed | — |
| `V0_2_EXECUTION_READINESS_NO_GO_GATES.md` | frozen (107C) | + NG-025 annotation | canonical-statement annotation only; schema/verdict/override unchanged | N-16-3 (§12a cross-reference) | additive | — |
| `permission_broker_foundation.py` (POL-005 / registry) | (`.1R.21` baseline) | POL-005 §12a carve-out; POL-013; `POLICY_IDS_CANONICAL` → 13; two derived fields; consistency checks | N-16-3 | POL-005 identity retained; legacy callers unaffected; 13-policy canon | `runtime_dispatch_permission.py` |
| `RDGO-001` | v3.1 | v3.1 (unchanged) — only the PBRD version string in "Related contracts" | — | no semantic change | — |
| RIHAC-001 / RIASC-001 / HPAC-001 / RPAC-001 | unchanged | unchanged | N-16-3 reads their outputs, adds nothing | — | — |
| N-15-5-1 (PBRD duplicate `§4a` heading hygiene) | — | **deferred** (§68) | not touched; no direct cross-reference to N-16-3 becomes ambiguous | — | — |

Include POL-005 separately: **its policy ID is stable, its canonical
statement is amended under a MAJOR-class versioned change** (PBNDE-001 v1.0 +
PBRD-001 v3.0 §12a + the NG-025 annotation).

---

## 4. Production implementation

### 4.1 `src/pcae/core/permission_broker_foundation.py`

- **Constants:** `PROFILE_RUNTIME_DISPATCH_LOCAL_CLI_V1 =
  "RUNTIME_DISPATCH_LOCAL_CLI_V1"`; `ADMISSION_CLASS_LOCAL_FIXED_ARGV =
  "local_fixed_argv"`; `ADMISSION_CLASS_UNADMITTED = "unadmitted"`.
- **`RuntimeDispatchAdapterDescriptorBinding`:** `+ admission_record_digest:
  str = ""`, `+ admission_class: str = ""` — additive, default-empty, do not
  change the meaning of the original four fields.
- **`RuntimeDispatchRequestFacts`:** `+ profile_classification: str = ""` —
  derived, non-caller, `""` on every legacy / non-narrow-profile request.
- **`_narrow_local_cli_dispatch_v1_failed_predicates(request, *,
  check_marker)`** — the single authoritative conjunction. Pure, fail-closed,
  reads only trusted-derived / seal-protected state. Returns the ordered tuple
  of unsatisfied predicate ids (empty == full profile). Predicate ids:
  `P_trusted_builder_seal`, `P_action_runtime_dispatch`,
  `P_execution_class_adapter`, `P_runtime_dispatch_context`,
  `P_transport_local_cli`, `P_network_prohibited`, `P_supply_chain_admission`,
  `P_human_authority_present`, `P_human_authority_binding_valid`,
  `P_attempt_identity`, `P_runtime_target`, `P_filesystem_scope`,
  `P_trusted_profile_classification` (only when `check_marker=True`). The
  credential / provider / model / shell / command-string predicates
  (`.1R.21` P5–P7) hold by construction — PBRD-001 §6 defines no such field —
  so their absence is structural, not a runtime check.
- **`derive_runtime_dispatch_local_cli_v1_classification(request)`** —
  trusted-builder-only; returns the literal iff every predicate (except the
  marker itself) holds, else `""`.
- **`_is_trusted_narrow_local_cli_dispatch_v1(request)`** — the POL-005
  carve-out predicate; reads **only** the trusted-derived marker and the
  construction seal.
- **`_valid_runtime_dispatch_request`** — after the existing 14-fact
  validation, adds: `marker ∈ {"", literal}`; if `marker == literal` the
  structural predicates must be complete; **if `marker == "" ` the structural
  predicates must NOT be complete** (a complete profile without the trusted
  marker is a post-construction forgery → structural DENY). This is a
  *stronger* binding than digest inclusion.
- **`ExecutionDisabledRule.evaluate` (POL-005):** `if request.simulation_only:
  return _not_triggered` (unchanged); **new** `if
  _is_trusted_narrow_local_cli_dispatch_v1(request): return _not_triggered`
  (PBRD-001 v3.0 §12a — not an ALLOW, only "not categorically blocking");
  else the unconditional `DENY` (byte-identical body — NG-025 / INV-001 /
  COMP-002).
- **`NarrowLocalCliDispatchEligibilityRule` (POL-013):** new
  `implementation_status = POLICY_STATUS_IMPLEMENTED`,
  `applicable_execution_classes = frozenset({EXECUTION_CLASS_ADAPTER})`.
  `evaluate`: `_not_triggered` unless (`action_type == runtime_dispatch` and
  `not simulation_only` and `runtime_dispatch_context is not None`); then
  `_not_triggered` if the conjunction holds, else a `DECISION_DENY`
  `PolicyResult` (NG-025 / INV-001 / COMP-002; the failed predicate ids in the
  remediation string). **Exactly two return shapes** — statically verifiable
  that no branch returns `ALLOW` or `HUMAN_REVIEW`.
- **Registry:** `NarrowLocalCliDispatchEligibilityRule()` appended to
  `DEFAULT_POLICY_RULES` (numeric order, POL-013 last);
  `POLICY_IDS_CANONICAL = frozenset(f"POL-{n:03d}" for n in range(1, 14))`.

### 4.2 `src/pcae/core/runtime_dispatch_permission.py`

- **N-16-6 admission interface + fail-closed stub** (new section):
  `SupplyChainAdmissionResult(admitted, admission_record_digest,
  admission_class)`; `SupplyChainAdmissionResolver` (interface, `resolve()`
  raises `NotImplementedError`);
  `_NonAdmittingSupplyChainAdmissionResolver` (admits **nothing** — every
  adapter is `unadmitted`); `_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER` (the
  single production instance, non-admitting); `_resolve_supply_chain_admission`
  (fail-closed wrapper — a non-resolver, an exception, a non-`SupplyChainAdmissionResult`,
  a malformed or admitting-but-wrong-shape result all fail closed to
  `unadmitted`).
- **`_validate_construction_inputs`:** rejects a construction input whose
  `adapter_descriptor_binding` pre-sets `admission_record_digest` /
  `admission_class` — the trusted builder is the sole populator.
- **`canonical_runtime_dispatch_projection`:** the `adapter_descriptor_binding`
  sub-dict gains `admission_record_digest` / `admission_class` — resolved
  deterministically from `adapter_id` via the (defaulted) resolver, so a
  mutation of the admission binding changes the `idempotency_key`. Threaded
  `_supply_chain_admission_resolver` kwarg (test-boundary only).
- **`new_runtime_dispatch_identity`:** threads the same test-boundary resolver
  kwarg into the projection so the minted `idempotency_key` and the builder's
  key-match check stay consistent under a synthetic resolver.
- **`build_runtime_dispatch_permission_broker_request`:** `+
  _supply_chain_admission_resolver` (test-boundary only, `None` in
  production). After human-authority projection: resolves the admission
  binding, rebuilds the adapter binding with the resolved (never caller)
  values, builds the provisional request, and derives
  `profile_classification` **last** via
  `derive_runtime_dispatch_local_cli_v1_classification`. In production
  `admission_class == "unadmitted"` → `P_supply_chain_admission` fails →
  marker is `""` → the provisional request is returned unchanged. A synthetic
  admitting resolver in tests can drive the marker to the literal.
- **Signature discipline preserved:** `approval_present` still absent,
  `validated_authority` still present (`test_gate6…_1r12` regression).
- **Module docstring:** PBRD version string → `v3.0`; the "POL-005 … is
  untouched by this module" sentence updated to reflect the §12a carve-out
  and the fact that the module now *derives* the marker (still constructs no
  policy semantics — POL-005 / POL-013 own those).

### 4.3 Digest / commitment binding

| New field | Binding mechanism | Mutation outcome |
|---|---|---|
| `adapter_descriptor_binding.admission_record_digest` / `admission_class` | inside `canonical_runtime_dispatch_projection` → `idempotency_key` (canonical-content digest, PBRD §5) | `build_…` raises `idempotency_key_does_not_match_canonical_content` |
| `RuntimeDispatchRequestFacts.profile_classification` | `_valid_runtime_dispatch_request` recomputes the expected value from the bound facts and rejects any inconsistency (marker present but profile incomplete; or profile complete but marker absent) | structural DENY (`invalid_runtime_dispatch_request`) before POL-005 / POL-013 evaluate |

Both are additionally reflected in any downstream full-request digest (PBRD
§14 Gate-7 projection; `consumption.json` `record_digest` at Gate 9) — no
`.1R.22` change is required there and none was made (Gate 7+ is out of scope).
`_expected_subject_scope_binding_digest` (the RIHAC subject/scope binding) is
**not** extended — admission is a PB-policy predicate, not part of the
human-authority scope binding — and no Gate-5 projection test changes.

---

## 5. Trusted predicate ownership matrix

| # | Predicate | Canonical source | Trusted derivation | Request field / binding | Failure reason (POL-013) | Caller-controllable? |
|---:|---|---|---|---|---|:--:|
| P1 | `action_type == runtime_dispatch` | trusted builder const (`_build_runtime_dispatch_permission_broker_request`) | hard-coded; generic builder rejects | envelope | `P_action_runtime_dispatch` | **No** |
| P2 | `execution_class == adapter` | trusted builder const (`EXECUTION_CLASS_ADAPTER`) | hard-coded | envelope | `P_execution_class_adapter` | **No** |
| P3 | trusted builder seal | `_RUNTIME_DISPATCH_REQUEST_SEAL` | module-private; only `_build_runtime_dispatch_permission_broker_request` stamps it | `_runtime_dispatch_seal` | `P_trusted_builder_seal` | **No** |
| P4 | `transport_type == local_cli` | trusted builder const | fixed | facts 11 | `P_transport_local_cli` | **No** |
| P5 | `network_requirement is False` | target descriptor + static preflight (caller-resolved input, validated `is False`) | `_validate_construction_inputs` + `_valid_runtime_dispatch_request` | facts 12 | `P_network_prohibited` | No (const `False`) |
| P6 | no credential / provider / model / shell / command-string field | PBRD-001 §6 (structurally absent) | request model defines no such field | n/a — absence is the invariant | (structural) | **No (structurally absent)** |
| P7 | supply-chain admission (`admission_class == local_fixed_argv`, digest present) | **N-16-6 admission resolver** | `_resolve_supply_chain_admission` → trusted builder stamps the adapter binding | `adapter_descriptor_binding.admission_record_digest` / `admission_class`; in `idempotency_key` | `P_supply_chain_admission` | **No** — production resolver admits nothing |
| P8 | `approval_present is True` | RIHAC-001 v2 validator (Gate 5) → `project_human_authority_binding` | derived; caller cannot set (PBRD §7 / §15) | envelope `approval_present` | `P_human_authority_present` | **No** |
| P9 | valid `human_authority_binding` 3-tuple | RIHAC-001 v2 validator | `project_human_authority_binding` (registry-provenanced projection only) | facts 14 | `P_human_authority_binding_valid` | **No** |
| P10 | real (non-NON_REAL) human authority | **N-16-5** / Gate-5 assurance decision | committed inside `validation_evidence_digest`; today `validate_approval` hard-stops on a NON_REAL lineage, so no valid binding for a real request can be produced (§7) | inside `validation_evidence_digest` | (via P8/P9 — no valid binding produced today) | **No** |
| P11 | `attempt_id` / `idempotency_key` coordinator-minted, well-formed | trusted invocation coordinator, RDGO Gate 2 | `new_runtime_dispatch_identity`; PBRD §15 rejects caller influence | facts 2–3; in request digest | `P_attempt_identity` | **No** |
| P12 | one exact `runtime_target_id` | explicit operator selection + registry | `_validate_construction_inputs` (`_bounded_string`, no alias) | facts 7 | `P_runtime_target` | **No** |
| P13 | `filesystem_scope_ref` present, digest-bound | governed isolated-worktree / scope owner | `_valid_runtime_dispatch_request` (`_sha256` digest) | facts 13 | `P_filesystem_scope` | **No** |
| P14 | **trusted profile classification** `RUNTIME_DISPATCH_LOCAL_CLI_V1` | **trusted request builder**, derived from P1–P13 | `derive_runtime_dispatch_local_cli_v1_classification`; `_valid_runtime_dispatch_request` recomputes and rejects any inconsistency | facts `profile_classification` | `P_trusted_profile_classification` | **No** |

`.1R.21`'s 21-predicate model maps onto these 14 checked predicates plus the
structural invariants already enforced by `_valid_runtime_dispatch_request`
(the seal, the 14-fact shape, `network_requirement is False`, authority
consistency, the identity-triple registry, the phase/task binding) and the
downstream single-attempt / durable-lifecycle wiring owned by Gate 9 + the
Slice-B mirror (P17/P18 — present and wired, not a Gate-6 check). No predicate
was dropped for code convenience; each is recorded above with its source,
derivation, binding, and failure reason.

**Every authority-bearing predicate is `Caller-controllable? = No`.** The only
partially-caller-influenced value (`network_requirement`) is safe in both
directions: a network-using executable is simply outside `…_V1` and, once
N-16-6 exists, would not be admitted as network-free.

---

## 6. No human-approved override; walls preserved

The rejected models remain rejected and are not expressible in the code:

- `_compose` has **no** channel by which any input flips a DENY category —
  re-verified: it iterates `(DENY, HUMAN_REVIEW)` and returns the first
  category with any triggered rule; no specificity tier, weight, or override.
  POL-013 contributes only *nothing* or *a DENY*.
- `human_authority_binding` validity (P8/P9) is **one predicate among
  fourteen**; it does not touch POL-005's match logic — the trusted
  **classification marker** (P14), derived from P1–P13, is what removes the
  request from POL-005's hard-block domain, and P8/P9 are only two
  contributors to that.
- **Human-authority wall test:** a fully trusted human-approval lineage with
  an incomplete narrow profile still yields `DENY` (POL-005 + POL-013) — no
  `if trusted_human: bypass_pol_005()` path exists (defensive matrix case 15;
  §11 case 26/27).

All five `.1R.21` §2 semantic walls re-verified against current source and
preserved: human approval ≠ PB permission; PB permission ≠ RE capability; RE
capability ≠ runtime execution availability; runtime execution availability ≠
external effect; POL-005 eligibility ≠ blanket execution permission.

---

## 7. Independence from N-16-4 / N-16-5 / N-16-7

- **N-16-4 (Runtime Enforcement):** a PB narrow-eligible decision does not
  read, reference, or depend on any Gate-7 state. Defensive matrix case 28.
- **N-16-5 (real human authentication):** `POL-013` does not re-authenticate
  the human (§9 wall) — it reads `approval_present` + the projection as
  inputs. Deterministic NON_REAL authentication cannot produce a valid
  `human_authority_binding` today (`validate_approval` hard-stop), so the
  production narrow profile is not satisfiable through NON_REAL authority.
- **N-16-7 (capability enablement):** `.1R.22` touches no runtime capability.
  `pcae runtime inspect` is byte-identical at entry and finalization:
  `not_implemented / Observed / observe / unavailable`; registry empty; 0
  plugins / 0 capabilities.

---

## 8. Network / credential / shell / fixed-argv / target / adapter / attempt

- **Network:** `RUNTIME_DISPATCH_LOCAL_CLI_V1` requires
  `network_requirement == false` (P5). Any network / provider class → POL-005
  DENY + POL-013 DENY.
- **Credentials:** no credential field exists on the request (PBRD §6); a
  credential-bearing input is a construction-time rejection (`_validate_construction_inputs`).
- **Shell:** the request carries no shell / command string; the profile is
  bound (via N-16-6, P7) to a fixed-argv `local_fixed_argv` adapter class —
  no shell interpretation, no command-string execution, no metacharacter
  semantics.
- **Fixed argv:** the argv shape is owned by the admitted adapter descriptor
  (N-16-6); a post-derivation mutation of the adapter binding changes the
  `idempotency_key` and fails the builder's key-match check.
- **Runtime target:** one exact `runtime_target_id`, `_bounded_string`-
  validated, no alias / fallback (P12). Wrong / unsupported → POL-013 DENY.
- **Adapter identity:** `execution_class == adapter` + the admitted
  descriptor's `local_fixed_argv` class (P2/P7). An unsupported adapter class
  → POL-013 DENY.
- **Attempt binding:** the classification is bound to the exact request digest
  (14 facts incl. `attempt_id` / `idempotency_key`) and expires on any change
  (PBRD §10). One consumed authority → one `attempt_id` → at-most-once
  dispatch attempt (Slice B). POL-013 requires the attempt identity present
  (P11); its consumption is Gate 9's job, not Gate 6's. POL-013 creates no
  reusable permission — it never emits ALLOW.

---

## 9. Production profile is unsatisfiable

Using only real production builders / resolvers / state:

- `_PRODUCTION_SUPPLY_CHAIN_ADMISSION_RESOLVER` is the non-admitting resolver;
  every `resolve(adapter_id)` → `admitted=False`, `admission_class="unadmitted"`.
- `_resolve_supply_chain_admission` returns `unadmitted` for every adapter.
- `derive_runtime_dispatch_local_cli_v1_classification` therefore returns `""`
  (`P_supply_chain_admission` fails) on **every** production path.
- POL-005 keeps its hard-DENY match (`_is_trusted_narrow_local_cli_dispatch_v1`
  is `False`); POL-013 DENYs on `P_supply_chain_admission` (and, today, also on
  `P_human_authority_present` — N-16-5 open).
- **`RUNTIME_DISPATCH_LOCAL_CLI_V1` is not obtainable in production.**
  Expected blocker: the N-16-6 non-admitting admission interface (and,
  independently, N-16-5). Proved directly by the defensive matrix
  (case 24 — production profile unsatisfiable; case 25 — no `adapter.dispatch(`
  call site).

**No production PB `ALLOW` for the first-effect local-CLI profile is
reachable.** Gate 6 itself remains non-positive because the profile is
unsatisfiable — not merely because runtime capability is unavailable
downstream.

---

## 10. Defensive policy test matrix (25+ cases)

New suite `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py`
(`.1R.23` re-derives). Every case asserts **no external effect**. Cases 1–25
follow `.1R.21` §37 exactly; the suite adds the phase-prompt §50/§53/§54
static and forgery challenges and the §63 contract-production equivalence
map. See §12 for the byte count and A/B classification.

| # | Case | Expected |
|---:|---|---|
| 1 | existing non-simulation `runtime_dispatch` request, no narrow profile | `DENY`, `causing_policy_ids == ("POL-005", "POL-013")` |
| 2 | caller-forged `profile_classification` via the generic builder | construction rejected (`runtime_dispatch_requires_trusted_builder`) → structural DENY |
| 3 | trusted local-CLI origin, missing admission binding | POL-005 DENY + POL-013 DENY (`P_supply_chain_admission`) |
| 4 | admitted (synthetic) executable, dynamic/non-fixed argv class | POL-013 DENY |
| 5 | fixed argv, `network_requirement=true` | `_validate_construction_inputs` rejects; POL-013 would DENY |
| 6 | credential field present on the construction input | construction rejected |
| 7 | shell / command-string field requested | no such field; construction rejected / POL-013 DENY |
| 8 | wrong / aliased `runtime_target_id` | POL-013 DENY (`P_runtime_target`) / subject mismatch |
| 9 | deterministic NON_REAL human-authority lineage | `approval_present=false` → POL-004 HUMAN_REVIEW + POL-013 DENY |
| 10 | missing attempt binding | POL-013 DENY (`P_attempt_identity`) |
| 11 | malformed profile evidence (bad digest, unknown enum) | fail closed → DENY |
| 12 | all narrow predicates structurally valid (synthetic admitting resolver + synthetic real authority) | POL-005 not categorically blocking; POL-013 not-triggered; **decision still gated by every other policy** |
| 13 | case 12 + another DENY policy triggered | `DENY` (that policy) |
| 14 | case 12 + `approval_present=false` | `HUMAN_REVIEW` (POL-004) — dominates ALLOW |
| 15 | narrow profile never returns ALLOW by classification | ALLOW only via `_compose` default; POL-013 static scan — no ALLOW branch |
| 16 | PB decision bound to exact invocation / attempt | decision digest over 14 facts; changed `attempt_id` → new evaluation |
| 17 | mutate any profile predicate after construction | request digest changes / structural DENY → prior decision expired |
| 18 | legacy callers (push, rollback, backend, adapter_invocation dry) | unaffected — POL-005 / POL-013 identical; POL-013 non-applicable or not-triggered |
| 19 | provider / network class request | still blocked |
| 20 | credentialed class request | still blocked |
| 21 | arbitrary executable path (no admission record) | blocked |
| 22 | arbitrary argv | blocked |
| 23 | unsupported adapter class (not `local_fixed_argv`) | POL-013 DENY |
| 24 | production profile unsatisfiable (real resolvers only) | classification `""`; no ALLOW reachable |
| 25 | no first-effect implementation exists | `grep 'adapter.dispatch('` over `src/pcae` → 0 call sites |
| 26 | fully trusted human approval + invalid narrow profile | `DENY` |
| 27 | another DENY rule active + all narrow predicates valid | `DENY` |
| 28 | HUMAN_REVIEW rule active + all narrow predicates valid | `HUMAN_REVIEW` (not ALLOW) |
| 29 | static: no `POL-013` branch returns `ALLOW` / `HUMAN_REVIEW` | AST scan of `NarrowLocalCliDispatchEligibilityRule.evaluate` |
| 30 | POL-013 precedence: neutral pass cannot suppress a DENY / HUMAN_REVIEW / hard no-go | verified via `_compose` |
| 31 | caller reconstruction (dataclass replace / dict / manual object) of the marker | structural DENY (marker inconsistent, or complete-without-marker forgery) |
| 32 | `profile_classification` / admission-field mutation → request digest ≠ original | `build_…` key-match failure / structural DENY |
| 33 | old representative PB callers (push ALLOW, rollback, source mutation) re-run | identical decision |

---

## 11. Scope-fence guard reconciliation

Any `src/pcae` change in this gate chain trips ~a dozen earlier-phase
point-in-time byte-freeze / consumer-inventory / scope-fence guards. Each was
widened to a **subset check over the exact authorized filename set (no
wildcard)**, committed under this phase identity, and is listed here; `.1R.23`
re-derives.

### 11.1 Guard-impact inventory

Authorized `.1R.22` production surface (exact, no wildcard):
`src/pcae/core/permission_broker_foundation.py`,
`src/pcae/core/runtime_dispatch_permission.py`.
Authorized `.1R.22` contract surface:
`docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`,
`docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
`docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md`,
`docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`.

| Guard file | Assertion(s) reconciled | How |
|---|---|---|
| `test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8.py` | `test_isolation_only_three_production_files_changed_since_baseline` | `_authorized` += `permission_broker_foundation.py` (rdp already listed) |
| `test_runtime_authority_production_repair_3w1r2b1r1117.py` | `test_production_file_allowlist_matches_frozen_phase_matrix`; `test_contract_and_pol005_bytes_remain_identical` | `_authorized_surface` += `permission_broker_foundation.py`; the parametrized SHA-pin skips the three `.1R.22`-authorized byte changes |
| `test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py` | `test_all_seven_contracts_and_pol005_byte_identical`; `test_production_scope_is_exactly_the_three_planned_files` | pinned-SHA loop skips the `.1R.22`-authorized set; `_AUTHORIZED_GATE_CHAIN_SURFACE` += `permission_broker_foundation.py` |
| `test_gate9_serialization_semantics_repair_3w1r2b1r1_1r15_2.py` | `test_earlier_gate_modules_unchanged[runtime_dispatch_permission.py]` | Gate 6 removed from the byte-freeze param list; Gate 5 / 7 / 8 stay frozen |
| `test_runtime_dispatch_contract_normalization_independent_verification_3w1r2b1r1_1r15_5.py` | `test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline`; `test_no_unplanned_contract_file_changed_since_task_open` | `forbidden` drops `runtime_dispatch_permission.py` (moved to `allowed` with `permission_broker_foundation.py`); the contract-diff `==` becomes a subset check excluding the `.1R.22` contract set |
| `test_gate10_pre_effect_eligibility_coordinator_3w1r2b1r1_1r17.py` | `test_earlier_gates_and_contracts_bytes_unchanged_since_baseline`; `test_production_scope_since_baseline_is_the_single_new_file` | `_SLICE_B_AUTHORIZED_SINCE_BASELINE` += the two `.1R.22` files; the byte-freeze loop skips them + the `.1R.22` contract |
| `test_gate10_slice_a_scope_fence_reconciliation_3w1r2b1r1_1r17r.py` | `test_gate5_permission_gate7_gate8_still_byte_unchanged_since_r153`; `test_no_production_source_changed_since_baseline_except_the_one_r17_file`; `test_no_contract_file_changed_since_baseline` | new `_R122` / `_R122_CONTRACTS`; `forbidden` drops `_PERM` (Gate 6 authorizedly changed); `allowed` / `changed <= allowed` subset checks widened; adversarial `test_scope_fence_would_still_flag_an_unauthorized_gate_change` unchanged (still trips on a Gate-5 change) |
| `test_gate10_slice_a_reconciliation_independent_verification_3w1r2b1r1_1r17r_1.py` | `test_gate_5_perm_7_8_are_byte_unchanged_since_r153_baseline`; `test_no_production_source_changed_since_the_r17_head_except_authorized_slice_b`; `test_production_scope_since_baseline_is_the_one_r17_file_plus_authorized_slice_b`; `test_no_normative_contract_changed_since_baseline`; `test_gate_5_to_9_and_neighbour_modules_byte_identical_since_baseline` | same `_R122` idiom; Gate 6 + PB Foundation removed from the neighbour byte loop; adversarial `test_a_synthetic_gate5_change_would_still_trip_the_fence` unchanged |
| `test_gate10_pre_effect_eligibility_coordinator_independent_verification_3w1r2b1r1_1r18.py` | `_UNCHANGED_SINCE_BASELINE` (drops Gate 6 / PB Foundation / PBRD); `_SLICE_A_PLUS_B_SCOPE` (+ the two files); `test_no_unpushed_divergence_at_verification_entry` (+ the two files + the `.1R.22` contracts) | subset widening; the anti-wildcard meta-guard `test_widened_guard_admits_only_the_authorized_module` still passes (each widened guard still names `runtime_dispatch_gate10_eligibility` and adds no wildcard) |
| `test_dispatch_attempt_durable_lifecycle_3w1r2b1r1_1r19.py` | `test_gate5_through_gate9_byte_unchanged` (`_POST_1R19_AUTHORIZED_SURFACE` skip); `test_pol_005_unchanged_and_still_hard_deny` (byte assertion → behavioral re-assertion; POL-005 still hard-DENYs `adapter_invocation` `simulation_only=False`) | subset skip + behavioral |
| `test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py` | `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` (`_POST_1R19R_AUTHORIZED` subtract); `test_no_slice_a_or_gate_5_9_drift_since_baseline` (PB Foundation removed); `test_meta_guards_are_byte_unchanged_since_r20_head` (see §11.2) | subset subtract |
| `test_dispatch_attempt_durable_lifecycle_iv_3w1r2b1r1_1r20.py` | `test_slice_b_production_scope_since_baseline_is_exactly_the_authorized_set` (`- _R122_AUTHORIZED`); `test_pol_005_module_byte_unchanged_since_baseline` (byte → behavioral, def name kept); `test_no_normative_contract_changed_since_baseline` (subset) | subset / behavioral |
| `test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py` | `test_n20_4_lifecycle_diff_since_r20_head_is_only_the_remap` (pathspec exclude `_R122`); `test_production_diff_since_r19_head_is_exactly_the_n20_4_remap` (`- _R122`); `test_no_slice_a_gate_or_item9_drift_since_r19_head` (PB Foundation removed from param list); `test_pol_005_hard_deny_still_present` (byte → behavioral); `test_no_normative_contract_change_since_baseline` (subset); `test_meta_guards_byte_unchanged_since_r20_head` (see §11.2) | subset / pathspec-exclude / behavioral |
| `test_phase_148c10_pbpc_v12_independent_verification.py` | `test_canonical_pbpc_push_request_reaches_allow`; `test_canonical_request_approval_present_true_does_not_change_applicability`; `test_registry_still_has_exactly_twelve_canonical_policies` | `non_applicable_policy_ids` for push gains POL-013 (adapter-scoped, ALLOW unchanged); canonical count → 13 |
| `test_permission_broker_policy_composition_hardening.py` | `test_deterministic_ordering_of_evaluated_and_triggered_policies` (POL-013 non-applicable for shell); `test_registry_accepts_additional_rules_without_modifying_broker` (synthetic extra rule → `POL-014`) | applicable-set update; synthetic id bumped |
| `test_permission_broker_policy_applicability.py` | `test_registry_accepts_superset_with_extra_non_canonical_rule` (`POL-014`, count 14); `test_applicable_non_applicable_preserve_registry_order` (`{POL-004, POL-013}` non-applicable for `none`) | synthetic id bump; scoped-set update |
| `test_permission_broker_verification_compatibility.py` | `test_zero_arg_broker_and_default_registry_unchanged` (`len(DEFAULT_POLICY_RULES) == 13`) | count |
| `test_runtime_dispatch_regression_pb_actions.py` | `test_policy_registry_still_exactly_twelve_canonical_policies` (→ 13, POL-013 last) | count |
| `test_runtime_dispatch_permission.py` | fourteen-facts field set (+ `profile_classification`; 15 dataclass fields = 14 logical + 1 derived); `test_structural_non_real_path_remains_distinct_from_pol005_deny` (`("POL-005", "POL-013")`) | field set / reinforcement |
| `test_runtime_authority_pb_verification_3w1.py`, `test_runtime_authority_pb_reverification_3w1r1.py` | `causing_policy_ids == ("POL-005", "POL-013")` for non-simulation `runtime_dispatch`; fourteen-facts field set | reinforcement / field set |

**Anti-wildcard discipline:** every widened set uses exact filenames. No
`"*"`, `fnmatch`, `.startswith(` package-glob, or `Path.glob` scope entry was
introduced. Each guard's separate `forbidden` set (Gate 5 / 7 / 8 / 9,
Slice-A coordinator, Gate-10 effect module) is preserved, and each still
rejects an unauthorized importer / an unauthorized gate change (verified by
the guards' own adversarial companion tests, which are unchanged).

### 11.2 Meta-guard search

Two meta-guards byte-freeze other guard files:
`test_dispatch_attempt_durable_lifecycle_reconciliation_3w1r2b1r1_1r19r.py::test_meta_guards_are_byte_unchanged_since_r20_head`
and
`test_slice_b_reconciliation_iv_3w1r2b1r1_1r19r1.py::test_meta_guards_byte_unchanged_since_r20_head`
each froze the `.1R.18` and `.1R.15.3` IV suites. `.1R.15.3` stays
byte-frozen (untouched). `.1R.18` is authorizedly reconciled by `.1R.22`, so
each meta-guard now asserts, for `.1R.18`: it still names
`runtime_dispatch_gate10_eligibility`, and (against `git show
e05f0ea3:<path>`) its `"*"` count, its `fnmatch` count, and its `def test_`
count are **unchanged / non-decreasing** — i.e. not weakened. The
`.1R.19R.1::test_no_test_weakening_in_the_r19r_diff` scanner (net non-
decreasing test-def count per touched file; `git show` of files absent at
`R20_HEAD` returns empty, so the new `.1R.22` suite is handled correctly)
passes without modification — **no `.1R.22` reconciliation renamed a test
function or removed an assertion decorator.** Consequential meta-guards that
*run* other guards (`.1R.15.3::test_v15_2_guards_pass_at_head`,
`.1R.18::test_widened_guard_module_passes_at_head`) pass at HEAD because the
sub-guards they run are green.

---

## 12. Fixed-SHA A/B and regression attribution

**Immutable pre-`.1R.22` baseline:** `8603fe6a` (phase entry).

*(Filled in at finalization — see §20. Deterministic, no xdist. Suites:
new N-16-3 policy suite; `permission_broker_foundation`;
`permission_broker_policy_*`; `runtime_dispatch_*`; `runtime_authority_pb_*`;
Gate 5 / 6 / 7 / 8 / 9 integration + IV; the `.1R.15.*` / `.1R.17*` /
`.1R.18` / `.1R.19*` / `.1R.20` suites; PBPC / PBPA IV; the scope/consumer
guards; the meta-guards.)*

**Known pre-existing failures (reproduce identically with `.1R.22` changes
stashed — 0 A/B delta):**

- `test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py::test_no_downstream_production_consumer_of_gate6_symbols`
  — `runtime_dispatch_gate10_eligibility.py` consumes `Gate6Decision`; a
  Slice-A (`.1R.17`) point-in-time guard, tracked by that suite's own
  `test_known_pre_existing_point_in_time_scope_guard_failures_are_attributable`.
- `test_runtime_authority_pb_verification_3w1.py::test_only_content_bound_projection_registry_is_added_to_authority_module`
  — expects `runtime_dispatch_permission.py` to carry no module-level mutable;
  `_GATE6_DECISIONS` (a `.1R.12` addition) already violates it. `.1R.22` adds
  no new module-level mutable container.
- `test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_permission_broker_consumer_scope_inventory`
  — a `.148f` consumer-inventory guard already listing many later-phase
  consumers.
- `test_phase_148g2_permission_broker_operational_hardening_independent_verification.py::test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`
  — pre-existing, unrelated to PB policy.

**Required:** CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0;
UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.

---

## 13. Runtime zero-effect evidence

| Assertion | Evidence |
|---|---|
| new production module contains adapter dispatch / subprocess / spawn / provider / network / credential / hardware call | **no** — `permission_broker_foundation.py` isolation tests still pass; `runtime_dispatch_permission.py` imports nothing from `shell_gate` / `backend_invocations` / `subprocess` / `socket`; the N-16-6 stub `resolve()` returns a frozen dataclass |
| `adapter.dispatch(` call site | **0** anywhere in `src/pcae` |
| runtime state modified | **no** — `pcae runtime inspect` byte-identical at entry and finalization |
| adapter registered | **no** — `RuntimeRegistry` empty; 0 plugins / 0 capabilities |
| provider / network / credential / hardware operation | **0** |
| POL-005 behaviour for ordinary requests | unchanged — every truthful non-simulation request that is not the (unsatisfiable) narrow profile still receives the unconditional `DENY` |

---

## 14. POL-005 — precise post-amendment statement

> **POL-005 (`ExecutionDisabledRule`) still hard-DENYs every previous
> effecting execution domain** — `runtime_dispatch`, `adapter`, `local`,
> `CLI`, `fixed argv`, provider / network / credentialed / shell classes,
> unknown runtime targets, unsupported adapters, every legacy effecting
> request, and every caller-forged local profile — **except the single
> trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile**, which is
> productionally unsatisfiable. POL-005's scope is being made **more
> precise** according to the approved architecture; it is **not** weakened in
> any way a production request can exploit. No generic execution class was
> individually excluded — only the exact trusted-derived profile escapes the
> categorical match, and only via a marker the trusted request builder
> derives and `_valid_runtime_dispatch_request` re-verifies.

---

## 15. Migration semantics summary (PBRD §16, v3.0)

- v2.x request shapes remain parseable; they carry `profile_classification ==
  ""` and are **categorically DENIED** (POL-005 + POL-013).
- No silent auto-upgrade of an old request into `RUNTIME_DISPATCH_LOCAL_CLI_V1`.
- Classification absence ⇒ old POL-005 domain.
- No compatibility default to the narrow profile.
- Cross-references move to `PBRD-001 v3.0`.
- `.1R.23` independent verification is mandatory.

---

## 16. N-16-3 disposition

**N-16-3: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING `.1R.23`.** NOT
CLOSED.

**N-16-4 / N-16-5 / N-16-6 / N-16-7: OPEN** — not begun; each remains its own
explicitly authorized implementation + IV pair; N-16-4 adjudicated before
N-16-5; N-16-7 strictly last.

**First external effect: ABSENT.** Slice C / Slice D keep no phase ID.

---

## 17. Implementation verdict

```
N-16-3 NARROW-ELIGIBILITY POLICY:
  IMPLEMENTED — INDEPENDENT VERIFICATION PENDING
RUNTIME_DISPATCH_LOCAL_CLI_V1:
  IMPLEMENTED AS A TRUSTED-DERIVED PROFILE
  — PRODUCTIONALLY UNSATISFIABLE
  — INDEPENDENT VERIFICATION PENDING
POL-013:
  IMPLEMENTED — NEVER EMITS ALLOW OR HUMAN_REVIEW
  — INDEPENDENT VERIFICATION PENDING
PBRD-001:
  v2.1 -> v3.0 (MAJOR) — EXPLICIT MIGRATION + IV MANDATED
FIRST EXTERNAL EFFECT:
  ABSENT
```

---

## 18. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.23` — Independent Verification of the N-16-3
Narrow-Eligibility Policy.** RE-DERIVE against PBRD-001 v3.0 §§12/12a/16,
PBNDE-001 v1.0, PBPA-001 v1.1, `_compose`, and current source: old callers
still DENY; no human-approval override; the classification is trusted-derived
at every predicate; default-deny outside the exact profile; `DENY >
HUMAN_REVIEW > ALLOW` intact; POL-013 statically never ALLOW; all broader
effect classes still blocked; POL-005 still hard DENY for everything else; no
`ALLOW` reachable in production (profile unsatisfiable); the PBRD MAJOR + the
migration semantics are §16-consistent; no execution / runtime / contract-
semantics drift beyond the approved N-16-3 change; fixed-SHA A/B.

Requires its own explicit human authorization. **Do not begin `.1R.23`.** Do
not proceed directly to N-16-4. Then N-16-4 → N-16-5 → N-16-6 → N-16-7, each
its own authorized implementation + IV pair; Slice C / D keep no phase ID.

---

## 19. `.3` governance incident

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved. Only
the primary human-authorized operator holds `.1R.22` lifecycle authority; no
delegated worker committed, finalized, or pushed. Governance rules honoured:
no raw `git commit` / `git push`, no `--no-verify`, no force push, no history
rewrite, no hook bypass — governed `pcae` lifecycle only.

---

## 20. Required final report (phase prompt §81)

- **Phase ID / title:** 149O.20L.7O.3W.1R.2B.1R.1.1R.22 — N-16-3
  Narrow-Eligibility Policy and Contract Implementation.
- **Phase-entry SHA:** `8603fe6a`.
- **Primary sources inspected:** §2.
- **Versioning adjudication:** §1.2 — PBRD-001 v2.1 §16 lists "weakening
  POL-005 eligibility" as a MAJOR trigger; `.1R.21`'s v2.2 MINOR conflicts;
  BLOCKED at primary-source review; human adjudicated **v3.0 MAJOR** with
  inline migration + `.1R.23` IV; repo convention (RDGO v2→v3.0, PBRD
  v1.1→v2.0) carries a contract MAJOR inline in the implementing phase, so no
  re-STOP.
- **PBRD old / new version:** v2.1 → **v3.0 (MAJOR)**.
- **POL-005 amendment mechanism / version:** kept ID `POL-005`; canonical
  statement amended (v2 semantics) under PBNDE-001 v1.0 + PBRD-001 v3.0 §12a
  + the NG-025 annotation; MAJOR-class; migration note; `.1R.23` IV.
- **POL-013 definition:** §3.3 / §4.1.
- **Exact narrow-profile predicates + trusted ownership matrix:** §5.
- **profile-classification implementation:** §4.1 / §4.3.
- **admission binding implementation + N-16-6 stub:** §4.2 / §3.3.
- **trusted builder implementation:** §4.2.
- **request-digest binding:** §4.3.
- **caller-forgery result:** structural DENY (marker inconsistent /
  complete-without-marker) — §4.1, matrix cases 2 / 31 / 32.
- **legacy caller result:** identical decision — matrix cases 18 / 33.
- **POL-005 exact new match domain:** §14.
- **default-deny result:** §4.1 (any predicate gap → POL-005 DENY + POL-013
  DENY).
- **POL-013 result vocabulary:** `_not_triggered` or `DECISION_DENY` only —
  matrix cases 15 / 29.
- **static proof POL-013 never ALLOW:** matrix case 29 (AST scan).
- **policy precedence regression:** unchanged `DENY > HUMAN_REVIEW > ALLOW`,
  no tier / weight / override — §6, matrix case 30.
- **human-authority wall / network / credential / shell / fixed-argv /
  runtime-target / adapter / attempt binding:** §6 / §8.
- **other-DENY dominance / HUMAN_REVIEW dominance:** matrix cases 13 / 27 / 14
  / 28.
- **production profile unsatisfiable proof / production PB-ALLOW
  reachability:** §9.
- **PBPA applicability:** §3.4 — POL-013 `{adapter}`, scoped; PBPA-REQ-062
  count → 2 scoped implemented policies; PBPA-001 v1.1.
- **NG-025 annotation:** §3.5 — corrected target
  `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`.
- **contract evolution manifest:** §3.6.
- **contract-production equivalence matrix:** the new suite maps every §12a
  requirement, every POL-005 new match condition, and every POL-013 predicate
  to a production symbol + test (matrix + §5 + §11).
- **direct guard impact inventory / meta-guard inventory / guard changes:**
  §11.
- **old-caller / Gate 6 / Gate 7 / Slice-A/B regressions / fixed-SHA A/B /
  candidate-only unexplained regression count:** §12 (finalized below).
- **production files changed:** `src/pcae/core/permission_broker_foundation.py`,
  `src/pcae/core/runtime_dispatch_permission.py`.
- **contract files changed:** `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`
  (v3.0), `PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md` (new,
  PBNDE-001 v1.0), `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
  (v1.1), `V0_2_EXECUTION_READINESS_NO_GO_GATES.md` (NG-025 annotation),
  plus PBRD version-string cross-references in
  `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` /
  `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`.
- **runtime state:** `not_implemented / Observed / observe / unavailable`;
  registry empty; 0 plugins / 0 capabilities — unchanged.
- **first-effect absence:** confirmed — 0 `adapter.dispatch(` call sites.
- **N-16-3 disposition:** IMPLEMENTED — IV PENDING `.1R.23`.
- **N-16-4..7 statuses:** OPEN.
- **all new findings:** N-16-3-1 (`.1R.21` versioning error — PBRD change is
  §16-MAJOR, corrected to v3.0); N-16-3-2 (`.1R.21` §38 NG-025 target
  location error — corrected to `V0_2_EXECUTION_READINESS_NO_GO_GATES.md`).
- **implementation verdict:** §17.
- **exact `.1R.23` recommendation:** §18.
- **`.3` governance incident status:** UNAUTHORIZED — preserved.
- **commits / pushed status / `origin/main..HEAD`:** recorded in the
  completion metadata / report after governed push; `origin/main..HEAD = 0` at
  finalization.

**FINAL VERDICT:**

- **N-16-3 NARROW-ELIGIBILITY POLICY AND CONTRACT: IMPLEMENTED — INDEPENDENT
  VERIFICATION PENDING `.1R.23`.**
- **PBRD-001 v3.0 (MAJOR) FROZEN WITH EXPLICIT MIGRATION; POL-005 CANONICAL
  STATEMENT AMENDED (ID RETAINED); POL-013 ADDED (NEVER ALLOW).**
- **`RUNTIME_DISPATCH_LOCAL_CLI_V1`: PRODUCTIONALLY UNSATISFIABLE.**
- **FIRST EXTERNAL EFFECT: STILL BLOCKED. EXECUTION NOT ENABLED.**

---

*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22.*
