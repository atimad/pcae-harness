# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.21 — N-16-3 Local-CLI Narrow-Eligibility Policy and Contract Planning

**Type:** planning / contract analysis only.
**Status:** COMPLETE — N-16-3 ARCHITECTURE/CONTRACT PLAN COMPLETE; IMPLEMENTATION PENDING.
**Production source changed:** none (`git diff --name-only <entry> HEAD -- src/pcae` empty).
**Normative contracts changed:** none (`git diff --name-only <entry> HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` empty).
**POL-005:** unchanged in production — `ExecutionDisabledRule` byte-identical; still an unconditional hard DENY for every truthful non-simulation request.
**Execution:** not enabled. Runtime remains `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; deterministic authentication remains NON_REAL.
**Phase-entry SHA:** `ced1b934` (`origin/main` synced; `origin/main..HEAD = 0` at entry).
**Governance:** governed `pcae` lifecycle only. The historical delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED**; only the primary human-authorized operator holds `.1R.21` lifecycle authority. Delegated workers may assist within explicit scope only and may not autonomously commit / finalize / push.

This document is the canonical planning artifact required by the phase
prompt §68 / §70. The required final report is §30.

---

## 1. Current independently verified architecture (established; not reopened)

Treated as verified unless fresh primary evidence in this document disproves
it (none does). Re-checked against current primary source this phase.

| Component | State | Verifying phase | Primary re-check this phase |
|---|---|---|---|
| Gate 5 — Approval Validation coordinator | CLOSED | `.1R.11` | `runtime_dispatch_gate5.py` byte-unchanged since `738e8209` (`.1R.19R.1` report §"No drift") |
| Gate 6 — Permission Broker production consumer | CLOSED | `.1R.13` | `runtime_dispatch_permission.py` byte-unchanged since `738e8209`; `permission_broker_foundation.py` (POL-005) byte-unchanged |
| Gate 7 — Runtime Enforcement coordinator | CLOSED | `.1R.13.3` | `runtime_dispatch_gate7.py` byte-unchanged since `738e8209` |
| Gate 8 — Process Containment (Shell Gate) coordinator | CLOSED | `.1R.13.5` | `runtime_dispatch_gate8.py` byte-unchanged since `738e8209` |
| Gate 9 — Atomic Authority Consumption coordinator | CLOSED | `.1R.15` | `runtime_dispatch_gate9.py` byte-unchanged since `738e8209` |
| Runtime-dispatch contract normalization (RDGO v3.1 / PBRD v2.1 / HPAC v2.1 / RIASC §9 errata / RE-registry 1.1) | CLOSED | `.1R.15.5` | RDGO-001 v3.1 and PBRD-001 v2.1 read in full this phase; byte-unchanged since `a2b679fe` |
| Gate-10 Slice A — pre-effect eligibility + `DispatchEnvelope` | VERIFIED; Slice-A lifecycle CLOSED | `.1R.17` / `.1R.17R` / `.1R.17R.1` | `runtime_dispatch_gate10_eligibility.py` byte-unchanged since `738e8209`; **no `adapter.dispatch()` call site** |
| Gate-10 Slice B — dispatch-attempt durable lifecycle, at-most-once, item 9, N-16-2 (Slice-B scope) | VERIFIED / CLOSED | `.1R.19` / `.1R.19R` / `.1R.19R.1` | `runtime_dispatch_attempt_lifecycle.py` present; non-authoritative mirror `RuntimeInvocationRecord`; `record_grants_no_effect_authority()` body is `return True` |
| First external effect | ABSENT | — | no `adapter.dispatch(` call site anywhere in `src/pcae`; Gate 10's *effect* keeps no phase ID |

**Current runtime (read directly from `runtime_introspection.py` +
`pcae runtime inspect`):** State `Observed`; Maximum Capability `observe`;
Execution Availability `unavailable`; Permission Broker status
`execution_unavailable`; governance posture `non-executing`. POL-005 remains
hard DENY.

**Remaining first-effect prerequisite set (carried forward exactly from
`.1R.16` §35 rows 13–17):**

| ID | Prerequisite | Status |
|---|---|---|
| **N-16-3** | PBRD-001 §12 POL-005 narrow-eligibility rule for the exact local-CLI `runtime_dispatch` profile + IV | **THIS PHASE plans it — NOT SATISFIED / PLANNED** |
| N-16-4 | Real, positive, single-attempt Runtime Enforcement gate over the full RDGO v3.1 projection | NOT SATISFIED — not begun |
| N-16-5 | Real FIDO2 / WebAuthn / CTAP + protected human-approval UI | NOT SATISFIED — not begun |
| N-16-6 | RPAC-REQ-095 generic fixed-argv external-executable adapter + supply-chain admission | NOT SATISFIED — not begun |
| N-16-7 | Runtime capability enablement (`Observed → Approved/Executable`) | NOT SATISFIED — not begun |

This phase addresses **only** N-16-3. N-16-4..7 are not begun.

---

## 2. Central planning question and semantic walls (phase prompt §3)

**Question.** What exact, narrowly bounded policy rule could allow a future
local-CLI `runtime_dispatch` request to become Permission-Broker *eligible*
(i.e. POL-005 does not categorically preclude ordinary PB evaluation)
without converting human approval into a policy override, weakening POL-005
globally, or making runtime execution generally available?

**Answer (frozen — see §21 for the normalized rule).** POL-005's
unconditional hard-DENY meaning is preserved for its entire existing match
domain. A single new **trusted-derived** execution profile —
`RUNTIME_DISPATCH_LOCAL_CLI_V1` — is defined as a distinct execution class
that is **not within** the historical POL-005 hard-block domain. POL-005
continues to DENY everything it matches; it simply does not match this one
narrow class. A **dedicated conjunctive eligibility policy** (proposed
`POL-013`, "Narrow Local-CLI Dispatch Eligibility") then governs that class:
it requires **every** trusted profile predicate to be present and
canonically bound, and its *most permissive* possible output is
`not-triggered` (i.e. "POL-005 does not categorically block; continue
ordinary evaluation") — it **never** emits `ALLOW` and never suppresses any
other policy. Failure of any predicate → `POL-013` DENY *and* POL-005
retains its hard-DENY match (defence in depth). This is Option **C + D**
(§13); Options A / B / E are rejected in §13.4.

**Semantic walls (phase prompt §3) — verified against current source:**

| Wall | Enforced by (current source) | Verified |
|---|---|---|
| human approval ≠ PB permission | Gate 5 produces only a validated-authority projection; `approval_present` is a derived Foundation input, never authority (PBRD §7; `runtime_dispatch_permission.py` `project_human_authority_binding`) | ✅ |
| PB permission ≠ Runtime Enforcement capability | Gate 6 → Gate 7 are separate coordinators; RDGO §8 "SHALL NOT infer approval from PB ALLOW, permission from approval, capability from the target name" | ✅ |
| Runtime Enforcement capability ≠ runtime execution availability | Gate 7 decision vs `runtime_introspection.EXECUTION_AVAILABILITY`; RDGO §11 item 5 re-reads current capability, not Gate 7's snapshot | ✅ |
| runtime execution availability ≠ external effect | Gate 10 `adapter.dispatch()` is the sole effect boundary; RDGO §11; no call site exists | ✅ |
| POL-005 eligibility ≠ blanket execution permission | `_compose` precedence `DENY > HUMAN_REVIEW > ALLOW`; eligibility = a policy *not triggering*, not an ALLOW; every other policy still evaluates | ✅ |

Every wall is a separate gate/owner with its own fail-closed behaviour;
N-16-3 does not merge, weaken, or bypass any of them.

---

## 3. N-16-3 re-derived from primary source (phase prompt §6)

### 3.1 Exact source wording

**PBRD-001 v2.1 §12 "POL-005 evolution boundary" (verbatim, closing
mandate):**

> "The future change SHALL be a narrowly scoped eligibility rule for the
> exact local-CLI `runtime_dispatch` profile, not deletion of POL-005, a
> universal non-simulation bypass, or an inference that
> `simulation_only=false` is itself permission. Every non-eligible
> non-simulation request remains denied."

Preceding it, §12 enumerates **eleven** conditions, *all* of which must be
"separately implemented and independently verified" before `runtime_dispatch`
"may become eligible":

1. the `runtime_dispatch` action and the exact `adapter` classification;
2. trusted construction and digest binding of all fourteen request facts,
   including `attempt_id` and `idempotency_key`;
3. RIHAC-001 v2.0 / RIASC-001 v3.0 / HPAC-001 v2.1 approval creation,
   protected proof/registry resolution, validation, expiry, and one-shot
   consumption;
4. **current-policy PB evaluation with no precedence weakening;**
5. a real, positive, single-attempt Runtime Enforcement gate over the full
   RDGO-001 v3.1 projection;
6. local executable supply-chain identity and live preflight;
7. Shell Gate/equivalent process containment with network denied;
8. atomic durable-before-effect state and uncertainty recovery;
9. the two 3S.2.1 prerequisite repairs at their required reachability point;
10. runtime-inspect repair before any real adapter availability claim; and
11. independent verification of this contract freeze.

**RDGO-001 v3.1 §20:** "This contract does not … relax POL-005 …".
**RDGO-001 v3.1 §7 (Gate 6):** "`DENY`, PB failure, malformed output, or
unresolved `HUMAN_REVIEW` stops the flow."

### 3.2 What defect/gap N-16-3 names

**PBRD §12 already mandates the *shape* of the rule but does not define it.**
The gap is: there is no defined, normative, implementable narrow-eligibility
rule for the exact local-CLI `runtime_dispatch` profile. Until one exists,
the only conformant production behaviour is POL-005's unconditional DENY
(which is correct today and must stay correct until every §12 condition is
met). N-16-3 = **author that rule** (contract + policy semantics), design
its trusted derivation, and independently verify it — *without* enabling it
in production (N-16-4..7 keep it unsatisfiable).

**Cross-reference note (non-blocking).** `.1R.16` §35 row 13 labels N-16-3
"item 4 of the eleven". Item 4 is "current-policy PB evaluation with no
precedence weakening" — a *constraint on* the rule, not the rule itself. The
rule itself is the §12 closing mandate paragraph (quoted in §3.1). This
document treats N-16-3 as **the §12 closing narrow-eligibility mandate,
subject to item 4's no-precedence-weakening constraint**. The `.1R.16`
phrasing is an imprecise cross-reference, not a contradiction; N-16-3's
scope is unchanged.

### 3.3 Which contract owns it

**PBRD-001** owns the narrow-eligibility *rule text* (§12 is its section).
**The Permission Broker Foundation policy registry** (`policy.py` /
`permission_broker_foundation.py`) owns the *production policy semantics*
(POL-005 and any companion policy). **PBPA-001** owns *applicability*
(whether a policy's requirement exists for a given request). **RDGO-001**
only cross-references (Gate 6 owns PB policy exclusively — §7 / §8 / §15).

### 3.4 Dependency relationship

| Question | Answer | Evidence |
|---|---|---|
| Does N-16-3 block Slice C (first concrete effect adapter)? | **YES — hard prerequisite** | `.1R.16` §35 row 13; §12 item 4 |
| Does N-16-3 block **N-16-4** *planning*? | **No** | N-16-4 is a real Gate-7 positive path over the RDGO projection; it can be designed against the existing contract. But N-16-4's *positive* result is meaningless while POL-005 DENYs at Gate 6 upstream, so N-16-3 should land first for coherence (§54). |
| Does N-16-3 block **N-16-5 / N-16-6 / N-16-7**? | **No** | Each is independent infrastructure (FIDO2/UI, adapter+supply-chain, capability enablement). N-16-3 *references* N-16-6's admission predicate and N-16-5's real-authority classification but defines the policy structurally without them. |
| Does N-16-3's *implementation* (`.1R.22`) enable any positive production path alone? | **No — by design (§47)** | N-16-4..7 each independently keep the narrow profile unsatisfiable. |

**No prerequisite earlier than N-16-3 is discovered.** Item 9 (the two
3S.2.1 repairs + runtime-inspect repair) was folded into Slice B and closed
by `.1R.19` / `.1R.19R.1`. Items 1–3, 7–8, 10–11 of §12 are satisfied by the
Gate 5–9 chain + `.1R.15.5` + Slice A/B IV. Items 4–6 map to N-16-3 / N-16-4
/ N-16-6. The analysis is bounded.

---

## 4. Current POL-005 semantics re-derived from production (phase prompt §7)

Source: `src/pcae/core/permission_broker_foundation.py`
`class ExecutionDisabledRule` (POL-005), read directly.

```python
class ExecutionDisabledRule(PolicyRule):
    policy_id = "POL-005"
    name = "Execution Disabled"
    implementation_status = POLICY_STATUS_IMPLEMENTED
    # applicable_execution_classes NOT declared  ->  universal (PBPA-REQ-019)

    def evaluate(self, request):
        if request.simulation_only:
            return _not_triggered("POL-005")
        return PolicyResult(
            policy_id="POL-005",
            triggered=True,
            decision=DECISION_DENY,
            decision_reason="execution_boundary_unavailable",
            matched_no_go_ids=("NG-025",),
            matched_invariants=("INV-001",),
            matched_component_ids=("COMP-002",),
            required_remediation=("No execution boundary exists today. …",),
            simulation_only=False,
        )
```

| Facet | Exact current behaviour |
|---|---|
| **Match condition** | `request.simulation_only is False` — i.e. any truthful non-simulation request, of **any** `action_type` and **any** `execution_class`. `simulation_only` defaults `True` on `PermissionBrokerRequest`; only the trusted runtime-dispatch builder (or a caller of `build_permission_broker_request`) can pass `False`, and the runtime-dispatch builder passes `simulation_only` straight through from its `simulation_only=` argument. |
| **Applicability (PBPA-001)** | **Universal.** No `applicable_execution_classes` declared → `None` → applies to every request (PBPA-REQ-019 / -020). It is *not* scoped to `adapter`. |
| **Action class** | Emits `DECISION_DENY` (hard). Never `HUMAN_REVIEW`, never `ALLOW`. |
| **Execution class** | Independent of `execution_class` — matches `none`, `mutation`, `shell`, `backend`, `adapter`, `rollback` alike when `simulation_only is False`. |
| **Precedence** | `_compose`: `DENY > HUMAN_REVIEW > ALLOW`, computed by iterating `(DENY, HUMAN_REVIEW)` and returning the first category with any triggered rule. A POL-005 DENY is therefore **absolute** — no ALLOW from any other rule can overcome it, and there is no per-rule precedence weighting or override channel. An empty/failed evaluation also fails closed to DENY. |
| **Evaluation result** | `causing_policy_ids` includes `POL-005`; `matched_no_go_ids=("NG-025",)`; `decision_reason="execution_boundary_unavailable"`; `simulation_only=False` carried on the decision. |
| **Relationship to other policies** | Orthogonal. POL-001 (missing task), POL-003 (missing evidence), POL-004 (missing approval → HUMAN_REVIEW, scoped to mediated classes incl. `adapter`), POL-006 (unknown action/class → DENY) all evaluate independently on the same request. POL-005 does not depend on or suppress any of them. |
| **Is it absolute for all execution-like activity, or narrower?** | **Absolute for all non-simulation activity.** Its `decision_reason` and `required_remediation` tie it specifically to COMP-002 ("no execution boundary exists today … cannot be satisfied until a future phase implements and verifies COMP-002"), and NG-025 is "unconditionally active by construction". It is the single categorical "execution is disabled repository-wide" statement. |

**Precise restatement (not a paraphrase of "hard DENY"):**

> POL-005 is triggered exactly when `request.simulation_only is False`. When
> triggered it returns an unconditional `DENY` citing NG-025 / INV-001 /
> COMP-002, for every `action_type` and `execution_class`. It is universally
> applicable, is never `HUMAN_REVIEW` or `ALLOW`, carries no exception
> channel, and under `_compose`'s `DENY > HUMAN_REVIEW > ALLOW` precedence a
> single POL-005 trigger determines the decision regardless of any other
> rule.

---

## 5. PBRD-001 §12 re-derived (phase prompt §8)

Source: `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` §12
(+ §1, §2, §3, §4, §5, §6, §7, §9, §11, §15, §16), read in full.

| §12 topic | What §12 currently says |
|---|---|
| **First external effect** | Not §12's subject directly; §3 says the external process "shall be created only after RDGO-001 gates 1–9 succeed"; §12 governs whether Gate 6 can ever ALLOW the request that precedes those gates. |
| **Permission eligibility** | `runtime_dispatch` "may [become] eligible **only after all** of the [eleven] following are separately implemented and independently verified". Eligibility is explicitly gated on the *conjunction*. |
| **Simulation vs effecting** | "an inference that `simulation_only=false` is itself permission" is **forbidden**. The effecting request must satisfy the narrow rule; `simulation_only=false` alone must always DENY. |
| **Local vs remote/provider** | §1 "local-CLI runtime dispatch remains a mediated adapter operation"; §3 "excludes API calls, provider SDKs, network permission"; §3 `network_requirement SHALL be false`; §11 "grants no network permission … API/provider dispatch remains blocked". The narrow rule is **local-only** by construction. |
| **POL-005** | "unchanged in production by this freeze … remains universal and denies every truthful non-simulation request, including `runtime_dispatch`." |
| **Future runtime-dispatch profile** | "a narrowly scoped eligibility rule for the **exact local-CLI `runtime_dispatch` profile**" — the rule is profile-scoped, not action-scoped and not class-scoped generally. |
| **Narrow eligibility** | "not deletion of POL-005, a universal non-simulation bypass, or an inference that `simulation_only=false` is itself permission. Every non-eligible non-simulation request remains denied." |
| **§16 versioning constraint** | "weakening POL-005 eligibility … requires a new MAJOR plus explicit migration and independent verification." — see §34. |
| **§4 fact 14 / §7** | `approval_present=true` is set **only** by successful RIHAC-001 v2.0 validation, never caller-settable; PB "never consumes an approval". |
| **§9 precedence** | "The existing deterministic precedence is unchanged: `DENY > HUMAN_REVIEW > ALLOW`." |

**Exact normative requirements the narrow rule must satisfy (mapped):**

- R1 — profile-scoped, not a class-wide or action-wide carve-out (§12);
- R2 — POL-005 not deleted; still denies every *non-eligible* non-simulation
  request (§12);
- R3 — no "universal non-simulation bypass" (§12);
- R4 — `simulation_only=false` is never itself permission (§12);
- R5 — no precedence weakening; `DENY > HUMAN_REVIEW > ALLOW` intact (§9,
  §12 item 4);
- R6 — eligibility is conjunctive over every §12 condition; the rule may be
  *defined* now but must remain *unsatisfiable* until N-16-4..7 close (§12
  "only after all");
- R7 — network prohibited; no provider/API path (§3, §11);
- R8 — no credential path (§6, §11);
- R9 — independent verification of the rule is itself a §12 condition
  (item 11 / N-16-3's IV).

---

## 6. Modeled future Slice-C Permission Broker request (phase prompt §9)

Built from current contract vocabulary; **not executed**. This is the
request a future Slice-C coordinator would hand Gate 6.

| PB field | Value in the modeled Slice-C request | Source / trust owner |
|---|---|---|
| `action_type` | `runtime_dispatch` | trusted invocation coordinator; `ACTION_TYPE_RUNTIME_DISPATCH` ∈ `KNOWN_ACTION_TYPES` |
| `execution_class` | `adapter` | trusted builder const (`EXECUTION_CLASS_ADAPTER`) |
| `simulation_only` | **`False`** (truthful real dispatch) | trusted builder argument |
| `approval_present` | `True` | derived — set only by successful RIHAC-001 v2.0 validation (PBRD §7) |
| `evidence_available` | `True` | trusted builder |
| `task_id` / `phase_id` | active governed task / phase | task lifecycle / lifecycle owner |
| `requested_component` | `REQUESTED_COMPONENT_ADAPTER_BOUNDARY` | trusted builder const |
| `runtime_dispatch_context` | sealed `RuntimeDispatchRequestFacts` (14 facts) with `transport_type="local_cli"`, `network_requirement=False`, valid `human_authority_binding`, `adapter_descriptor_binding`, `filesystem_scope_ref`, `attempt_id`, `idempotency_key` | trusted builder + `_RUNTIME_DISPATCH_REQUEST_SEAL` |

**Policy-by-policy evaluation of this request against the *current*
registry:**

| Policy | Applicable? | Triggered? | Decision | Reason |
|---|:--:|:--:|---|---|
| POL-001 Missing Active Task | yes | no | — | `task_id` present |
| POL-003 Missing Evidence | yes | no | — | `evidence_available=True` |
| POL-004 Missing Human Approval | yes (`adapter` ∈ applicable classes) | no | — | `approval_present=True` (valid RIHAC v2 projection) |
| **POL-005 Execution Disabled** | **yes (universal)** | **YES** | **DENY** | `simulation_only is False` → `execution_boundary_unavailable`, NG-025, INV-001, COMP-002 |
| POL-006 Unknown Capability | yes | no | — | `runtime_dispatch` ∈ known actions; `adapter` ∈ known classes |
| POL-007 Unknown Component | yes | no | — | component known |
| structural `_valid_runtime_dispatch_request` | — | pass | — | sealed, 14 facts valid, `network_requirement is False`, authority consistent |

**Current decision: `DENY`**, `causing_policy_ids = ("POL-005",)`,
`matched_no_go_ids = ("NG-025",)`, `precedence_reason =
"deny_precedence: 1 DENY-triggering policy present"`. This is **correct
today** and MUST remain the outcome for every request that does not satisfy
the full narrow profile.

---

## 7. Target narrow local-CLI `runtime_dispatch` profile (phase prompt §10)

Frozen as a **single bounded profile**, `RUNTIME_DISPATCH_LOCAL_CLI_V1`.
Every dimension has an explicit disposition; a request is *in the profile*
only if **all** hold, each from its trusted source (§15).

| # | Predicate | Required value | Rationale / contract |
|---:|---|---|---|
| P1 | `action_type` | `runtime_dispatch` | PBRD §1 |
| P2 | `execution_class` | `adapter` | PBRD §1; reuse existing class |
| P3 | `transport_type` | `local_cli` (const) | PBRD §4 fact 11; RDGO §5 |
| P4 | `network_requirement` | `False` (const) | PBRD §3 / §11; RDGO §5. If a target needs network it is **not** eligible for this profile. |
| P5 | provider / model fields | absent | PBRD §6 (no mandatory provider/model; no universal provider abstraction) |
| P6 | credential material / secret fields | absent | PBRD §6 / §11 — credential access is out of v1 scope entirely |
| P7 | shell string / arbitrary command string | absent | PBRD §6; RDGO §11 "argument vector, not unrestricted shell evaluation" |
| P8 | executable path | descriptor/config-referenced, **supply-chain admitted** (N-16-6) — never a caller command string | PBRD §6; RDGO §9; §12 item 6 |
| P9 | argument vector | fixed argv from the admitted adapter descriptor (N-16-6); no dynamic argv | RDGO §11; RPAC-REQ-095 |
| P10 | environment | trusted allowlist assembled by the coordinator from the descriptor; no dynamic env injection | RDGO §9(a); §12 item 7 |
| P11 | cwd | repository-scoped (governed isolated worktree / `filesystem_scope_ref`) | RDGO §9(a); PBRD §4 fact 13 |
| P12 | resource / time limit | bounded (containment profile references) | RDGO §9(a) — *established* at Gate 8; the PB predicate only requires the containment-profile reference to be present and well-formed |
| P13 | `adapter_descriptor_binding` | closed object: `adapter_id`, descriptor version + digest, target-config digest — bound to a **canonical supply-chain admission record** (N-16-6) | PBRD §4 fact 8; §12 item 6 |
| P14 | `human_authority_binding` | valid RIHAC-001 v2.0 validated-authority projection; `approval_present=True`; **real** (not deterministic NON_REAL) human authority (N-16-5) | PBRD §4 fact 14 / §7; §12 item 3 |
| P15 | `attempt_id` / `idempotency_key` | present, well-formed, coordinator-minted at RDGO Gate 2; bound (Slice B) | PBRD §4 facts 2–3; RDGO §10a |
| P16 | Gate 5→9 lineage | the request reaches Gate 6 only within an in-progress RDGO Gate 1→…→6 flow (Gate 5 already produced a validated projection this pass) | RDGO §1 numeric order |
| P17 | single attempt | one consumed authority → one `attempt_id` → at-most-once dispatch attempt; PB ALLOW is not reusable | RDGO §10a / §18; Slice B |
| P18 | durable DispatchAttempt lifecycle | the Slice-B mirror + Gate 9 `consumption.json` machinery is present and wired | RDGO §9 / §10; N-16-2 |
| P19 | runtime target | one exact `runtime_target_id`, a locally admitted runtime target; no alias/fallback | RDGO §3; PBRD §4 fact 7 |
| P20 | `filesystem_scope_ref` | present, closed object, digest-bound | PBRD §4 fact 13 |
| P21 | **trusted profile classification** | a derived marker `RUNTIME_DISPATCH_LOCAL_CLI_V1` produced by the trusted request builder from P1–P20 — **never** a caller-supplied field | anti-bypass (§14) |

**Prefer the narrowest practical first profile.** P4 (`network=false`) and
P6 (no credentials) are **mandatory** for `…_V1` (§23, §24). A network- or
credential-using local executable belongs to a strictly later profile, not
this one.

---

## 8. Eligibility dimensions are separately satisfied (phase prompt §11)

The future Slice-C request must **independently** satisfy each of the
following; **no one dimension substitutes for another**:

| Dimension | Owner / gate | Satisfied by |
|---|---|---|
| human-authority eligibility | Gate 3 + Gate 5 (RIHAC v2) | real approval + fresh validated projection (N-16-5) |
| PB policy eligibility | **Gate 6 (N-16-3 — this plan)** | narrow profile present → POL-005 not categorically blocking; `POL-013` conjunction passes; **and** no other policy DENYs; POL-004 not triggered (approval valid) |
| Runtime Enforcement eligibility | Gate 7 (N-16-4) | real positive single-attempt RE decision over the full RDGO projection |
| containment eligibility | Gate 8 | established bounded process environment + live preflight |
| runtime capability eligibility | current `runtime_introspection` (N-16-7) | `EXECUTION_AVAILABILITY == "available"` (not today) |
| adapter admission | N-16-6 / Gate 8 | supply-chain-admitted fixed-argv executable identity |
| attempt-lifecycle eligibility | Gate 9 + Slice-B mirror | durable `consumption.json` `/2.1` + mirror `PREPARED→…` |

N-16-3 owns exactly one row (PB policy eligibility) and **references** two
others (adapter admission P13, human-authority realness P14) via *bound
predicates* it does not itself produce.

---

## 9. No "human-approved override" (phase prompt §12)

**Explicitly rejected models:**

```python
if human_approved:            # REJECTED
    ignore POL-005
```
```python
if principal in TRUSTED:      # REJECTED
    return ALLOW
```

Neither is compatible with the architecture or this plan:

- `_compose` has **no** channel by which any input flips a DENY. A DENY
  category always wins. There is no "trusted principal → ALLOW" and no
  "approved → skip POL-005".
- PBRD §7 / §8: a valid approval means only that POL-004's
  `MissingHumanApprovalRule` is *not triggered*; "valid human authority does
  not suppress" other policies. "PB HUMAN_REVIEW is … not an automatic
  second human-approval ceremony" — and conversely approval is not a
  policy waiver.
- In this plan, `human_authority_binding` validity (P14) is **one predicate
  among twenty-one**. It is necessary, never sufficient, and it does not
  touch POL-005's match logic — the narrow **profile classification** (P21),
  derived from P1–P20, is what removes the request from POL-005's hard-block
  domain, and P14 is only one contributor to that.

Human approval is **input to authority lineage**, consumed once at Gate 9,
never a policy override.

---

## 10. Policy architecture options A–E (phase prompt §13)

### 10.1 Option A — narrow POL-005 exclusion

POL-005 stays hard DENY except it does not *match* one explicitly named
governed local-dispatch execution class.

- **Mechanics:** `evaluate()` gains `elif is_narrow_local_cli_dispatch(request): return _not_triggered("POL-005")`.
- **+** Preserves DENY for every other class; small change.
- **−** Makes POL-005's *meaning* depend on a class taxonomy embedded in
  `ExecutionDisabledRule` itself; POL-005 becomes conditionally universal,
  which is a subtle weakening of "unconditionally active by construction"
  (NG-025). Harder to audit ("why did POL-005 not trigger here?").
- **Verdict:** viable but **inferior to C** — C frames the same mechanical
  outcome as "this class was never in POL-005's domain" rather than "POL-005
  now has an exception", which is cleaner for auditability and for the
  NG-025 canonical statement.

### 10.2 Option B — retain POL-005, add a higher-specificity ALLOW policy

A new policy emits `ALLOW` for the narrow profile and is expected to
"override" POL-005.

- **Precedence check (decisive):** `_compose` iterates `(DENY,
  HUMAN_REVIEW)` and returns the **first** category with any triggered
  rule. An `ALLOW` is only reached when **zero** rules triggered DENY or
  HUMAN_REVIEW. There is **no specificity ordering**, no per-policy weight,
  no override channel. A higher-specificity ALLOW **cannot** overcome a
  POL-005 DENY.
- **Verdict:** **REJECTED.** The broker contract does not permit an ALLOW to
  override an unconditional DENY, and PBRD §9 / §12 forbid weakening
  precedence. Do not assume an override model — the code disproves it.

### 10.3 Option C — evolve the execution-class taxonomy (trusted, narrow)

Define `RUNTIME_DISPATCH_LOCAL_CLI_V1` as a distinct **trusted-derived**
execution profile that is **not semantically within** the historical
POL-005 hard-block class (which was "all non-simulation execution while
COMP-002 is `not_implemented`"). POL-005's meaning for its existing domain
is unchanged; it simply does not match this one class.

- **Genuine semantic precision, not relabeling? — YES**, because:
  (a) the classification is **trusted-derived** (P21), never caller-set, so
  a caller cannot "relabel" its way out;
  (b) the class is **materially narrower** on every axis (local process,
  fixed argv, no network, no credentials, supply-chain-admitted executable,
  real human authority, single attempt, durable lifecycle, repo-scoped
  cwd) — it is not the old class with a new name;
  (c) it stays **unsatisfiable** in production until N-16-4..7 (§47), so the
  taxonomy change has zero behavioural effect on ship.
- **−** Requires a versioned amendment to POL-005's canonical statement /
  NG-025 (§34, §35) and a new execution-class constant.
- **Verdict:** **PREFERRED** for the POL-005 mechanism.

### 10.4 Option D — dedicated conjunctive eligibility policy

A new policy (proposed **`POL-013`**, "Narrow Local-CLI Dispatch
Eligibility") that requires **all** narrow-profile predicates and is still
subject to every hard no-go.

- **Relationship to POL-005:** complementary, not competing. `POL-013` is
  applicable only to `runtime_dispatch` / `adapter` requests. Its outputs:
  - **all predicates present + bound** → `not-triggered` (contributes
    nothing; lets ordinary evaluation proceed);
  - **any predicate missing / malformed / unknown-state** → `DENY`
    (`narrow_local_cli_dispatch_profile_incomplete`), which *reinforces*
    POL-005 rather than competing with it.
  - `POL-013` **never** emits `ALLOW` and **never** `HUMAN_REVIEW`.
- **+** Keeps the conjunction logic out of `ExecutionDisabledRule`; single
  responsibility; explainable (`causing_policy_ids` shows exactly which
  predicate failed).
- **Verdict:** **PREFERRED** as the companion to Option C. Option C removes
  the categorical POL-005 block for the class; Option D is the gate that
  proves the request actually *is* the narrow profile and fails closed
  otherwise.

### 10.5 Option E — no safe policy evolution yet

- The rule is **contract-expressible now** (§21) — it does not require
  N-16-4/5/6/7 to *exist* in order to be *defined*, only to be *satisfied*.
- Deferring N-16-3 would block N-16-4..7 planning coherence (each needs to
  know the eligibility target) and provides no safety benefit — the rule
  ships unsatisfiable.
- **Verdict:** **REJECTED.** Do not force the exception, but do not defer
  the definition either; §47's "structure exists, no real request can
  satisfy it" outcome is the correct one.

### 10.6 Selected architecture: **C + D**

- Option **C** — a new trusted-derived execution profile
  `RUNTIME_DISPATCH_LOCAL_CLI_V1` that is not within POL-005's hard-block
  domain; POL-005's canonical statement gets a versioned amendment naming
  the single carve-out.
- Option **D** — a dedicated conjunctive `POL-013` that requires every
  narrow-profile predicate, fails closed on any gap, and never emits ALLOW.
- Rejected: **A** (POL-005 semantics become taxonomy-dependent — C is the
  cleaner framing of the same outcome), **B** (precedence forbids an ALLOW
  override — code-proven), **E** (rule is expressible now; deferral has no
  safety benefit).

---

## 11. Anti-bypass analysis (phase prompt §14)

For each option: *could a caller manufacture the narrow-profile fields and
escape POL-005 before the downstream trust gates detect it?*

| Vector | Defence in the C + D design | Owning mechanism |
|---|---|---|
| Caller sets a `narrow_profile=true` field | There is **no such field**. The profile classification P21 is derived by the trusted builder from P1–P20; `RuntimeDispatchRequestFacts` is constructible **only** behind `_RUNTIME_DISPATCH_REQUEST_SEAL`; `_valid_runtime_dispatch_request` fails closed if the seal is absent. | `runtime_dispatch_permission.py` trusted builder; `permission_broker_foundation.py` seal check |
| Caller forges `RuntimeDispatchRequestFacts` directly | `build_permission_broker_request` raises `runtime_dispatch_requires_trusted_builder`; the sealed internal builder is module-private. | existing (`.1R.13`) |
| Caller sets `approval_present=true` | PBRD §7 / §15 "Caller sets `approval_present` → Reject request construction"; only successful RIHAC v2 validation sets it. | Gate 5 / trusted builder |
| Caller supplies `attempt_id` / `idempotency_key` | PBRD §15 "Caller sets/influences `attempt_id` or `idempotency_key` → Reject request construction"; minted at Gate 2. | RDGO §10a; trusted coordinator |
| Caller claims a fake `adapter_id` / executable | P13 requires a **canonical supply-chain admission record** (N-16-6); `POL-013` requires the admission binding to be present and to resolve. A fabricated adapter id has no admission record → `POL-013` DENY; and Gate 8 re-hashes the executable. | N-16-6 admission store; Gate 8 |
| Caller declares `network_requirement=false` but the executable needs network | P4 is a *bound fact, grants nothing* (PBRD §4 fact 12); Gate 8 "confirm network remains denied"; a network-using executable is simply outside `…_V1` and its admission record (N-16-6) would not classify it as network-free. | Gate 8; N-16-6 |
| Caller replays a valid approval from another invocation | `human_authority_binding` commits `invocation_id` + subject/scope; Gate 5 re-binds; Gate 9 consumes atomically once; `POL-013` requires the projection's `invocation_id` to equal the request's. | RIHAC v2; RDGO §10 item 5 |
| Caller mutates argv after the PB decision | PB decision expires on any request change (PBRD §10); Gate 8 re-resolves argv; the fixed argv is from the admitted descriptor, not the caller. | PBRD §10; Gate 8; N-16-6 |

**Conclusion:** the narrow-profile classification is **trusted-derived, not
caller-declared**, at every predicate. No manufacture-and-escape path
exists in the C + D design. This is the load-bearing property and it is
already structurally supported by the sealed builder shipped in `.1R.13`.

---

## 12. Trusted request-field ownership matrix (phase prompt §15)

For every narrow-eligibility predicate: authoritative producer,
caller-controllability, verification gate, digest/binding.

| Predicate | Authoritative source | Caller-controllable? | Gate(s) verified | Digest / binding |
|---|---|:--:|---|---|
| local CLI origin (P3 `transport_type=local_cli`) | trusted builder const (PBRD-001 integration point) | **No** | Gate 6 structural (`_valid_runtime_dispatch_request`), Gate 8 reconfirm | inside request canonical digest (PBRD §5) |
| runtime target (P19) | explicit operator selection at Gate 2 → target selector + registry | No (no alias/fallback) | Gates 2, 4, 8, 9 | `runtime_target_id` in request digest + `subject.runtime_target_id` |
| execution class (P2 `adapter`) | trusted builder const | **No** | Gate 6 structural, POL-006 | request digest |
| **profile classification (P21 `RUNTIME_DISPATCH_LOCAL_CLI_V1`)** | **trusted request builder, derived from P1–P20** | **No** | Gate 6 (`POL-013`) | committed into the request canonical digest; see §16 |
| adapter identity (P13) | Runtime Registry / config preflight | No | Gates 4, 8 | `adapter_descriptor_binding` (adapter_id + descriptor digest + target-config digest) |
| executable admission (P8) | **N-16-6 canonical supply-chain admission record** | No | Gate 6 (`POL-013` requires admission binding), Gate 8 (re-hash) | admission-record digest bound into `adapter_descriptor_binding` (proposed N-16-6 field) |
| fixed argv (P9) | admitted adapter descriptor (N-16-6) | No | Gate 8 establishes; Gate 9 recomputes | `containment_evidence_digest` (Gate 8) |
| network prohibition (P4) | target descriptor + static preflight | No (const `False`) | Gates 4, 8 | request digest fact 12; Gate 8 containment digest |
| credential prohibition (P6) | request exclusions (PBRD §6 — no field exists) | **No (structurally absent)** | request construction rejects credential-bearing fields; Gate 8 "no credential access required" | n/a — absence is the invariant |
| simulation/effecting flag (P: `simulation_only=false`) | trusted builder argument | Partially (a real request sets it; but a *false* claim of simulation just means POL-005 doesn't trigger and no effect happens anyway) | Gate 6 (POL-005), Gate 7, Gate 10 | decision carries `simulation_only` |
| human-authority lineage (P14) | RIHAC-001 v2 validator (Gate 5) | **No** (`approval_present` derived) | Gates 3, 5, 9 | `human_authority_binding` 3-tuple + `validation_evidence_digest` over the full projection |
| real (non-NON_REAL) human authority (P14) | N-16-5 real FIDO2/UP+UV; HPAC assurance decision at Gate 5 | **No** | Gate 5 assurance decision; Gate 9 revalidation | inside `validation_evidence_digest` / HPAC proof lifecycle |
| attempt identity (P15) | trusted invocation coordinator, Gate 2 | **No** (PBRD §15) | Gates 2–11; Gate 9 item 1 | `idempotency_key` = SHA-256 of canonical content; `attempt_id` random |
| Gate 5→9 lineage (P16) | RDGO gate sequence | No | Gates 1–6 numeric order | validated projection freshness verdict |
| filesystem scope (P20) | governed isolated-worktree / scope owner | No | Gates 5, 8, 9 | `filesystem_scope_ref` digest |
| durable lifecycle wired (P18) | Slice-B mirror + Gate 9 store | No | Gates 9, 10 | `consumption.json` `/2.1` `record_digest` |

**Every authority-bearing predicate is `Caller-controllable? = No`.** The
only partially-caller-influenced field (`simulation_only`) is safe in both
directions: `true` → POL-005 doesn't trigger but nothing dispatches; `false`
→ the full narrow profile + all gates must still pass.

---

## 13. Execution-class trust (phase prompt §16)

**Is `execution_class` currently descriptive caller input or trusted derived
state?** — **Trusted, for `runtime_dispatch`.** The generic
`build_permission_broker_request` takes `execution_class` as an argument
(caller-influenced for the *legacy* action types), **but** it raises
`runtime_dispatch_requires_trusted_builder` if `action_type ==
runtime_dispatch` or a `runtime_dispatch_context` is present. The only path
to a `runtime_dispatch` request is
`build_runtime_dispatch_permission_broker_request`, which **hard-codes**
`execution_class=EXECUTION_CLASS_ADAPTER` and stamps
`_RUNTIME_DISPATCH_REQUEST_SEAL`. `_valid_runtime_dispatch_request` then
fails closed unless `execution_class == EXECUTION_CLASS_ADAPTER` **and** the
seal matches.

**Consequence for N-16-3:** a POL-005 carve-out / `POL-013` eligibility
**may** be based on the `runtime_dispatch` + `adapter` classification
*because that classification is already trusted-derived and seal-protected*.
It must **not** be based on any *new* caller-visible self-classification
field. The **new** profile marker P21 (`RUNTIME_DISPATCH_LOCAL_CLI_V1`) must
be produced by the **same trusted builder** from P1–P20, never accepted as
input. Plan the trusted derivation mechanism (§16 of this document → §17)
as a mandatory `.1R.22` deliverable.

---

## 14. Local-CLI origin trust (phase prompt §17)

**What proves `origin = PCAE local CLI`?**

| Evidence | Trustworthy? | Notes |
|---|:--:|---|
| a caller-supplied `"local_cli": true` | **No** | never trust; not a field in the design |
| `transport_type == "local_cli"` const set by the trusted builder | **Yes** | seal-protected; `_valid_runtime_dispatch_request` requires it |
| the request was constructed by `build_runtime_dispatch_permission_broker_request` (seal present) | **Yes** | the single command-path-owned request builder; no generic/dict path (§13) |
| RDGO Gate 2 provenance — request-identity triple minted by the trusted invocation coordinator | **Yes** | `invocation_id`/`attempt_id`/`idempotency_key` are coordinator-allocated |
| session / runtime provenance (active governed session, `lifecycle_context`) | **Yes (supporting)** | `lifecycle_context.phase_id == request.phase_id` enforced |

**Plan:** the `.1R.22` trusted builder derives P21 only when: the seal is
present, `transport_type == "local_cli"`, `network_requirement is False`,
the identity triple is coordinator-minted, and (N-16-6) the adapter is a
supply-chain-admitted **local fixed-argv** class. An explicit internal
`invocation_source` enum (`PCAE_LOCAL_CLI`) set by the coordinator is
recommended as a belt-and-braces addition, but the *seal + const transport*
already provides the trust; the enum is not load-bearing on its own.

---

## 15. Fixed executable identity prerequisite (phase prompt §18)

**N-16-6 remains open.** Can N-16-3 define the policy contract now but keep
positive eligibility impossible until supply-chain admission is satisfied?
— **YES. Frozen.**

- `.1R.22` defines `POL-013` to **require** a resolvable canonical
  supply-chain admission binding for `adapter_descriptor_binding` (P8 /
  P13). Until N-16-6 ships an admission store and at least one admitted
  fixed-argv executable, **no** request can carry a valid admission binding
  → `POL-013` DENYs → POL-005's carve-out never applies (the profile is
  incomplete).
- N-16-3 does **not** itself decide arbitrary executable trust (§22 / §50).
  It requires a *binding to* an admission record whose production and
  verification belong to N-16-6 and Gate 8.

---

## 16. Real human authority prerequisite (phase prompt §19)

**N-16-5 remains open.** The narrow policy may be defined structurally now
but MUST require a trusted **real**-human-authority classification not
satisfiable by deterministic NON_REAL mechanisms. — **Frozen.**

- `POL-013` requires `approval_present == True` **and** the validated
  projection's assurance verdict to reflect a **real** authenticated
  principal (the HPAC assurance decision at Gate 5 — "whether this
  authenticated principal may validate a production approval"). Today
  `validate_approval` hard-stops on a NON_REAL lineage (`.1R.16` §30.1
  point 1) — so no valid `human_authority_binding` for a real request can
  be produced. `POL-013` does **not** re-authenticate the human (§9 wall) —
  it reads the Gate-5 verdict as an input.
- The policy itself never parses FIDO2, never reads HPAC registries
  (PBRD §7) — that remains Gate 5's job.

---

## 17. Runtime Enforcement prerequisite (phase prompt §20)

**N-16-4 remains open.** How should Gate 6's narrow policy bind to a future
positive Gate-7 result? — **It must not.**

- Gate 6 (`POL-013` + POL-005 carve-out) produces **PB eligibility only**.
  RDGO §7 / §8: Gate 7 "independently evaluates the complete bound
  request", "SHALL NOT infer … permission from approval". Gate 6 MUST NOT
  assume Gate 7 will ALLOW, MUST NOT read a Gate-7 result, and MUST NOT
  carry any Gate-7 expectation.
- The binding is **one-directional and downstream**: Gate 7 receives the PB
  decision + policy IDs + version + decision digest as *inputs* (RDGO §8
  item 2) and re-validates authority currentness; it never rubber-stamps
  PB. A PB ALLOW with a Gate-7 DENY → no dispatch (PBRD §10 / §15).
- `.1R.22` MUST include a test that a PB narrow-eligible decision does not
  change, reference, or depend on any Gate-7 state (defensive matrix
  case 20).

---

## 18. Runtime capability prerequisite (phase prompt §21)

**N-16-7 remains open.** Even a future PB ALLOW must produce **no external
effect** while `Execution Availability: unavailable`. — **Frozen contract
relationship.**

- POL-005 carve-out + `POL-013` pass + all other gates ALLOW **still**
  yields no effect: RDGO §11 item 5 requires "runtime capability eligible
  (execution availability …)" at Gate 10 entry, re-read from **current**
  `runtime_introspection.EXECUTION_AVAILABILITY` (not any snapshot). Today
  that is `"unavailable"` → Gate 10 fails closed (`.1R.16` §33 / F-G10-7).
- N-16-3 does not touch runtime capability. The `Observed → Approved /
  Executable` transition is N-16-7 — a governed, separately verified step,
  strictly last (§56).

---

## 19. Supply-chain relationship (phase prompt §22)

The N-16-3 policy **does not** decide arbitrary executable trust. It
**requires** a canonical admission predicate / binding where appropriate
(P8 / P13). N-16-6 governs executable + adapter identity, supply-chain
admission (RPAC-REQ-054 / -086), and the fixed-argv adapter class
(RPAC-REQ-095). `POL-013` predicate: "`adapter_descriptor_binding` carries a
resolvable canonical supply-chain admission binding whose class is
`local_fixed_argv`" — planning only; the store, the record schema, and its
verification are N-16-6 deliverables.

---

## 20. Network and credential prohibition (phase prompt §23, §24)

**Network (§23).** The first eligible local-CLI profile **REQUIRES
`network_requirement == false`** — frozen explicitly. PBRD §3: "If a target
needs network egress, it is not eligible for this contract." A local
executable that inherently uses network belongs to a **later** policy
profile, not `…_V1`. Prefer narrowest practical first profile.

**Credentials (§24).** The first profile **REQUIRES `credentials_required
== false`** — frozen. PBRD §6 / §11: credential access is entirely out of
v1 scope; there is no credential field, and a credential-bearing field in
the request is a construction-time rejection. Default toward yes (mandatory)
— and the contracts require it.

---

## 21. Candidate normalized rule (phase prompt §31)

**Frozen preferred rule — `RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow
eligibility (normative-quality language, repository terminology):**

> **POL-005 amendment (canonical statement, versioned).** The
> `ExecutionDisabledRule` (POL-005) SHALL be triggered for every request
> with `simulation_only == false` **except** a request that the trusted
> Permission Broker runtime-dispatch request builder has classified as the
> `RUNTIME_DISPATCH_LOCAL_CLI_V1` profile. For that single class POL-005
> SHALL return *not-triggered* — meaning **only** that POL-005 does not
> categorically preclude ordinary Permission Broker evaluation of the
> request. POL-005 SHALL NOT be deleted, SHALL remain universally
> applicable, and SHALL continue to return an unconditional `DENY` for
> every other non-simulation request of every action type and execution
> class. The classification SHALL be derived exclusively by the trusted
> request builder from the bound request facts and SHALL NOT be a
> caller-supplied field.
>
> **`POL-013` — Narrow Local-CLI Dispatch Eligibility (new policy).**
> Applicable only to requests with `action_type == runtime_dispatch` and
> `execution_class == adapter`. `POL-013` SHALL evaluate the conjunction of
> every `RUNTIME_DISPATCH_LOCAL_CLI_V1` predicate (P1–P21 of the N-16-3
> profile): trusted-builder seal present; `transport_type == local_cli`;
> `network_requirement == false`; no credential or provider/model field;
> no shell/command string; `adapter_descriptor_binding` carries a
> resolvable canonical supply-chain admission binding of class
> `local_fixed_argv`; `human_authority_binding` is a valid RIHAC-001 v2.0
> validated-authority projection for the exact `invocation_id` with a real
> (non-NON_REAL) assurance verdict; `attempt_id` and `idempotency_key`
> present and coordinator-minted; one exact `runtime_target_id`;
> `filesystem_scope_ref` present and digest-bound; the durable
> dispatch-attempt lifecycle is wired.
>
> - If **every** predicate holds → `POL-013` is *not-triggered* (it
>   contributes nothing; ordinary evaluation of all other policies
>   proceeds).
> - If **any** predicate is missing, malformed, of unknown state, bound to
>   an unresolvable record, or of a broader effect class → `POL-013` SHALL
>   return `DENY` with reason `narrow_local_cli_dispatch_profile_incomplete`
>   and the specific failed-predicate id, **and** POL-005 SHALL also retain
>   its `DENY` match (the classification was not achieved).
> - `POL-013` SHALL NOT return `ALLOW` or `HUMAN_REVIEW` under any input.
>
> **Eligibility is not permission.** A `RUNTIME_DISPATCH_LOCAL_CLI_V1`
> request that clears POL-005 and `POL-013` is then subject to POL-001,
> POL-003, POL-004, POL-006, POL-007, POL-006-class no-gos, and the full
> deterministic `DENY > HUMAN_REVIEW > ALLOW` composition, exactly as
> today. A final `ALLOW` still means only PBRD-001 §2's bounded statement,
> and Gates 7–10 each independently gate the effect.

---

## 22. Eligibility-to-evaluation, not guaranteed ALLOW (phase prompt §32)

**Critical distinction, frozen:**

```
narrow profile proven  ->  POL-005 does not categorically preclude ordinary PB evaluation
                       -/->  ALLOW
```

`POL-013` passing and POL-005 not triggering leaves the request to be
evaluated by every other policy. In particular:

- POL-004 (`adapter` ∈ applicable classes) will emit **HUMAN_REVIEW** if
  `approval_present` is false — and HUMAN_REVIEW **dominates** ALLOW.
- Any future DENY policy (e.g. a task-state, evidence, or no-go rule) still
  DENYs.
- The `ALLOW` branch of `_compose` is reached only when **no** rule
  triggered DENY or HUMAN_REVIEW — unchanged.

The narrow profile **never directly returns ALLOW by classification**
(defensive matrix case 15).

---

## 23. Default-deny outside the exact profile (phase prompt §33)

**Frozen:**

| Condition | Result |
|---|---|
| any missing predicate | POL-005 DENY + `POL-013` DENY |
| any predicate of unknown / indeterminate state | POL-005 DENY + `POL-013` DENY (fail closed) |
| any malformed binding (unresolvable admission record, bad digest) | POL-005 DENY + `POL-013` DENY |
| unsupported adapter / executable class (not `local_fixed_argv`) | POL-005 DENY + `POL-013` DENY |
| any broader effect profile (network, credentials, provider, shell, dynamic argv) | POL-005 DENY + `POL-013` DENY |
| `runtime_dispatch_context` absent or seal missing | `_valid_runtime_dispatch_request` structural DENY (pre-policy) |

**No fuzzy matching. No partial credit. No "close enough".** The
classification is all-or-nothing and trusted-derived.

---

## 24. Policy precedence (phase prompt §29)

**Re-derived exact precedence** (`_compose`, read directly):

```
1. empty results / evaluation failure           -> DENY (fail closed)
2. any triggered rule with decision == DENY      -> DENY   (first category checked)
3. else any triggered rule == HUMAN_REVIEW       -> HUMAN_REVIEW
4. else                                          -> ALLOW ("policy_would_allow_if_execution_existed")
```

So the order is **`DENY > HUMAN_REVIEW > ALLOW`, fail-closed**, with **no**
specificity tier, weight, or override.

**How the narrow eligibility interacts:**

- POL-005 not triggering for `…_V1` **removes one DENY contributor** — it
  does not add an ALLOW and does not change the composition algorithm.
- `POL-013` only ever contributes **nothing** (pass) or **a DENY** (fail) —
  it can never move the outcome toward ALLOW beyond "not blocking".
- Every other policy's DENY / HUMAN_REVIEW still dominates.
- **No hidden precedence exception. No new precedence tier.** §12 item 4
  ("no precedence weakening") is satisfied by construction.

---

## 25. Hard no-go preservation (phase prompt §30)

Inventory of blocks that MUST still dominate even for the narrow profile:

| Block | Still dominates? | Mechanism |
|---|:--:|---|
| POL-006 unknown action/class (NG-024 / NG-015) | yes | independent; unchanged |
| POL-001 missing active task (NG-001) | yes | independent |
| POL-003 missing evidence (NG-023) | yes | independent |
| POL-004 missing human approval (NG-008) → HUMAN_REVIEW | yes — dominates ALLOW | independent; `adapter` in applicable set |
| `_valid_runtime_dispatch_request` structural failure (NG-023) | yes — pre-policy DENY | seal / 14-fact / `network_requirement is False` / authority-consistency checks |
| forbidden action / credential-required / untrusted runtime target / protected paths / policy-config tamper / unsupported adapter | yes | `POL-013` fails closed on each; plus any dedicated future no-go policy evaluates independently |
| runtime unavailable (owned by Gate 7 / Gate 10) | yes — downstream | RDGO §11 item 5; not a Gate-6 concern, but the effect is still blocked |
| RE-NOGO-001..017 | yes | Gate 7 per-decision projection + environmental-readiness process; N-16-3 changes none |
| POL-005 for **every non-`…_V1` non-simulation request** | yes | the carve-out is exactly one class |

Narrow eligibility does **not** become general allow.

---

## 26. Attempt-count semantics (phase prompt §27)

Frozen — compatible with Slice B:

```
one consumed authority  ->  one attempt identity (attempt_id)  ->  at-most-once dispatch attempt
```

- A PB narrow-eligible decision is **bound to the exact request digest**
  (14 facts incl. `attempt_id` / `idempotency_key`) and **expires** on any
  change (PBRD §10). "A changed `attempt_id` … always invalidates any prior
  PB decision."
- A PB ALLOW / eligibility decision is **not reusable** across attempts: a
  retry mints a new `attempt_id` at a fresh Gate 2 pass → a new request
  digest → a fresh Gate 6 evaluation.
- `POL-013` MUST require `attempt_id` + `idempotency_key` present (P15);
  their consumption is Gate 9's job, not Gate 6's.

---

## 27. Permission decision lifetime (phase prompt §28)

Frozen — preserves Gate-6 architecture:

| Property | Value |
|---|---|
| point-in-time | yes — evaluated against current PB policy version at Gate 6 |
| bound to invocation / attempt | yes — request digest over all 14 facts; decision digest recorded |
| non-transferable | yes — `Gate6Decision` identity-sealed (`.1R.13`); not serializable as authority |
| re-read via lineage at Gate 10, not re-evaluated | yes — RDGO §7 / §8 / §15; Gate 10 byte-compares `consumption.json.pb_binding`, requires `decision == "ALLOW"`, and **does not re-run PB policy** (`.1R.16` §18 / F-G10-12) |
| stale `policy_version` after Gate 6 | resolved by **re-entering Gate 6**, never by a later gate; a later gate may surface `policy_drift_requires_fresh_pb_re_evaluation` as an advisory reason only |

N-16-3 does not change any of this. `POL-013` and the POL-005 amendment are
ordinary policies evaluated at Gate 6; their version is part of
`policy_version`.

---

## 28. Gate relationships (phase prompt §43–§46)

| Gate | Relationship to N-16-3 |
|---|---|
| **Gate 5** (phase prompt §43) | Validates human authority; produces the validated-authority projection. **It MUST NOT decide POL eligibility.** N-16-3 only documents the *lineage dependency*: `POL-013` reads `approval_present` + the assurance verdict as **inputs**, produced by Gate 5. |
| **Gate 6** (phase prompt §44) | **Sole PB policy owner.** N-16-3 belongs here entirely. POL-005 amendment + `POL-013` live in the Foundation policy registry. No later gate reinterprets policy. |
| **Gate 7** (phase prompt §45) | Separately evaluates runtime enforcement. **PB eligibility MUST NOT imply Gate-7 ALLOW.** Gate 7 receives the PB decision as an input and independently re-validates. |
| **Gate 8 / Gate 10** (phase prompt §46) | Containment establishment (Gate 8) and final effect-state read-back (Gate 10) remain downstream. N-16-3 does **not** move their checks into PB policy. `POL-013` only requires the *presence and well-formedness* of the containment-profile / admission bindings — Gate 8 establishes and Gate 10 re-reads the actual containment. |

---

## 29. Security-boundary review (phase prompt §49)

Each failure mode mapped to the owning gate / binding:

| Failure mode | Defence | Owner |
|---|---|---|
| caller lies about origin | seal + const `transport_type=local_cli`; no caller origin field | trusted builder (Gate 6 struct) |
| caller lies about network use | `network_requirement` is a bound fact granting nothing; N-16-6 admission classifies network-free; Gate 8 confirms network denied | Gate 8 / N-16-6 |
| caller lies about executable admission | `POL-013` requires a resolvable canonical admission record; Gate 8 re-hashes the executable | N-16-6 store / Gate 8 |
| caller changes argv after the PB decision | PB decision expires on request change; Gate 8 re-resolves the fixed argv from the admitted descriptor | PBRD §10 / Gate 8 |
| caller substitutes the runtime target | `runtime_target_id` is subject-bound; no alias/fallback; re-checked Gates 8/9 | RDGO §3 / §15 |
| human approval copied from another invocation | `human_authority_binding` commits `invocation_id` + subject scope; Gate 5 re-binds; Gate 9 consumes once | RIHAC v2 / RDGO §10 |
| effect plan changes downstream | Gate 8 `containment_evidence_digest`; Gate 9 recomputes; Gate 10 re-reads and byte-verifies | Gates 8/9/10 |
| policy result replayed to another attempt | decision bound to request digest incl. `attempt_id`; expires on any change; Gate 10 requires exact lineage match | PBRD §10 / RDGO §11 item 4 |
| caller manufactures the profile marker | P21 is not an input; derived by the trusted builder; sealed | trusted builder |
| POL-005 carve-out abused for a non-`…_V1` request | carve-out matches exactly one trusted-derived class; every other non-simulation request → POL-005 DENY | POL-005 amendment |

**No defence relies on the caller. No downstream check is *removed* — only
*not duplicated* (§50).**

---

## 30. Required final report (phase prompt §71)

- **Phase ID / title:** 149O.20L.7O.3W.1R.2B.1R.1.1R.21 — N-16-3 Local-CLI
  Narrow-Eligibility Policy and Contract Planning.
- **Phase-entry SHA:** `ced1b934` (`origin/main` synced; `origin/main..HEAD
  = 0` at entry).
- **Primary sources inspected (in full unless noted):**
  `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001
  v2.1, incl. §12 verbatim); `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`
  (RDGO-001 v3.1); `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (schema
  1.1); `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`
  (PBPA-001 — applicability / precedence sections);
  `src/pcae/core/permission_broker_foundation.py` (POL-001..007,
  `ExecutionDisabledRule`, `_compose`, `_structural_request_failure`,
  `RuntimeDispatchRequestFacts`, `build_permission_broker_request`,
  `_build_runtime_dispatch_permission_broker_request`,
  `_valid_runtime_dispatch_request`, seal); `src/pcae/core/runtime_dispatch_permission.py`
  (`build_runtime_dispatch_permission_broker_request`,
  `project_human_authority_binding`); `docs/PHASE_…1R_16…PLANNING.md`
  (§7, §18, §19, §20, §30, §33, §35, §36.2); the `.1R.19R.1` canonical
  report + completion metadata (Slice-B closure, drift evidence);
  `runtime_introspection.py` constants via `pcae runtime inspect`.
- **Exact N-16-3 wording:** §3.1 (PBRD-001 §12 closing narrow-eligibility
  mandate + the eleven conjunctive conditions).
- **Current POL-005 semantics:** §4 (triggered iff `simulation_only is
  False`; unconditional universal DENY; NG-025 / INV-001 / COMP-002; no
  HUMAN_REVIEW / ALLOW / exception channel; absolute under `_compose`).
- **PBRD §12 interpretation:** §5 (profile-scoped; conjunctive; POL-005 not
  deleted; no non-simulation bypass; `simulation_only=false` never itself
  permission; §16 MAJOR constraint on weakening).
- **Modeled future PB request:** §6 — 14-fact sealed `runtime_dispatch` /
  `adapter` / `simulation_only=false` / `approval_present=true`.
- **Current decision for it:** **`DENY`**, `causing_policy_ids=("POL-005",)`,
  `matched_no_go_ids=("NG-025",)` — correct today.
- **Target narrow local-CLI profile:** §7 — `RUNTIME_DISPATCH_LOCAL_CLI_V1`,
  21 predicates, network + credentials prohibited, supply-chain-admitted
  fixed-argv, real human authority, single attempt, durable lifecycle,
  trusted-derived classification.
- **Predicate ownership matrix:** §12 — every authority-bearing predicate
  `Caller-controllable? = No`.
- **Caller-control analysis:** §11, §13 — the classification is
  trusted-derived at every predicate; no manufacture-and-escape path.
- **Semantic-wall results:** §2 — all five walls verified against current
  source; none merged or weakened.
- **Options A–E analysis:** §10 — A viable/inferior; **B REJECTED**
  (precedence forbids ALLOW override — code-proven); **C PREFERRED**
  (trusted narrow class); **D PREFERRED** (conjunctive `POL-013`); **E
  REJECTED** (rule is expressible now).
- **Anti-bypass analysis:** §11 — trusted-derived classification; sealed
  builder; N-16-6 admission binding; Gate-8 re-hash; PB-decision expiry.
- **Selected architecture:** §10.6 — **Option C + D**: POL-005 versioned
  canonical-statement amendment naming the single
  `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out + new conjunctive `POL-013`
  that never emits ALLOW.
- **Rejected-option rationale:** §10.1–§10.5.
- **Exact conceptual PBRD delta:** §31.
- **Exact conceptual POL-005 delta:** §32.
- **PB request / schema impact:** §33 — one derived internal field
  (`profile_classification` / P21) committed into the request digest; no
  caller-visible field added; one proposed `adapter_descriptor_binding`
  sub-field for the N-16-6 admission-record digest.
- **Trusted builder impact:** §33 —
  `build_runtime_dispatch_permission_broker_request` derives P21 from
  P1–P20; no generic path.
- **Digest / binding impact:** §33 — P21 + admission-record digest inside
  the PBRD §5 canonical request digest and (transitively)
  `consumption.json` `record_digest`.
- **Policy precedence:** §24 — `DENY > HUMAN_REVIEW > ALLOW`, fail-closed,
  no tier / weight / override; unchanged.
- **Default-deny rules:** §23 — any missing / unknown / malformed / broader
  predicate → POL-005 DENY + `POL-013` DENY; no fuzzy matching.
- **Hard no-go preservation:** §25 — POL-001/003/004/006/007, structural
  failure, RE-NOGO-*, and POL-005-for-everything-else all still dominate.
- **Backward compatibility:** §36 — every existing caller / config leaves
  `runtime_dispatch_context = None`; no legacy request is reclassified;
  POL-005 unchanged for all of them.
- **Versioning adjudication:** §34 — PBRD-001 **§12 clause: MINOR** (adds
  the promised rule text, no fact/precedence change); **POL-005 canonical
  statement: versioned amendment (POL-005 keeps its ID) + a new NG
  annotation** — the *policy-semantics* change is materially MAJOR-class and
  is carried as an explicit versioned amendment with migration + IV;
  **`POL-013`: new additive policy**; **PB request schema: additive
  internal field, no MAJOR**; **RE No-Go Registry: additive annotation
  only**.
- **POL-005 version / identity question:** §35 — POL-005 **retains its ID**
  (historical auditability / audit trail continuity); its canonical
  statement is amended under a versioned change naming exactly the
  `RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out; `POL-013` is the new companion
  policy; NG-025's canonical statement gets a parallel versioned
  annotation. No superseding ID; no POL-005 deletion.
- **Security-boundary matrix:** §29.
- **Defensive test matrix:** §37 (25 cases, phase prompt §48).
- **Anticipated contract files:** §38.
- **Anticipated production files:** §39.
- **Implementation decomposition:** §40 — `.1R.22` implementation,
  `.1R.23` IV.
- **Exact `.1R.22` / `.1R.23` recommendation:** §40 — supported; forward
  tokens; IDs above `.1R.20` are not reserved (`.1R.16` §36.2), so `.1R.21`
  (this) / `.1R.22` / `.1R.23` are the next free sequential IDs.
- **N-16-3 status:** **ARCHITECTURE / CONTRACT PLAN COMPLETE — IMPLEMENTATION
  PENDING.** NOT CLOSED.
- **N-16-4..7 proposed ordering:** §41 — N-16-3 → N-16-4 → N-16-5 → N-16-6
  → N-16-7 (dependencies in §41; N-16-7 strictly last).
- **First-effect status:** **STILL BLOCKED — no phase ID.**
- **Runtime state:** `not_implemented / Observed / observe / unavailable`;
  POL-005 hard DENY unchanged.
- **Contract identity:** RDGO-001 v3.1, PBRD-001 v2.1, HPAC-001 v2.1,
  RIHAC-001 v2.0, RIASC-001 v3.0, RPAC-001 v1.0, PBPA-001, POL-005
  (`permission_broker_foundation.py`), RE No-Go Registry schema 1.1 — all
  byte-unchanged (`git diff --name-only <entry> HEAD -- docs/contracts
  docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md src/pcae` empty).
- **Production-diff result:** empty.
- **Runtime / no-effect evidence:** §42.
- **`.3` governance incident status:** UNAUTHORIZED — preserved.
- **Commits / pushed status / `origin/main..HEAD`:** recorded in the
  completion metadata / report after governed push;
  `origin/main..HEAD = 0` at finalization.

**FINAL VERDICT:**

- **N-16-3 POLICY/CONTRACT ARCHITECTURE: PLANNED — IMPLEMENTATION NOT
  BEGUN.**
- **POL-005 NARROW-ELIGIBILITY MODEL: FROZEN FOR IMPLEMENTATION — CURRENT
  HARD-DENY PRODUCTION BEHAVIOUR UNCHANGED.**
- **FIRST EXTERNAL EFFECT: STILL BLOCKED.**

---

## 31. Exact conceptual PBRD-001 §12 delta (phase prompt §38 — no contract edit)

**Proposed `.1R.22` change — a new subsection `§12a` (or an appended
normative block in §12).** No existing §12 text is deleted. Proposed
normative text:

> **§12a. `RUNTIME_DISPATCH_LOCAL_CLI_V1` narrow-eligibility rule.**
> When, and only when, all eleven §12 conditions are separately implemented
> and independently verified, `runtime_dispatch` becomes eligible for
> ordinary Permission Broker evaluation under the following rule and no
> other:
>
> 1. The trusted PB runtime-dispatch request builder SHALL derive a closed
>    profile classification `RUNTIME_DISPATCH_LOCAL_CLI_V1` from the bound
>    request facts. The classification SHALL hold only if: the request is
>    seal-constructed; `action_type == runtime_dispatch`; `execution_class
>    == adapter`; `transport_type == local_cli`; `network_requirement ==
>    false`; no credential, secret, provider, or model field is present; no
>    shell or command string is present; `adapter_descriptor_binding`
>    carries a resolvable canonical supply-chain admission binding of class
>    `local_fixed_argv`; `human_authority_binding` is a valid RIHAC-001
>    v2.0 validated-authority projection bound to the exact `invocation_id`
>    with a real (non-deterministic, non-NON_REAL) assurance verdict;
>    `attempt_id` and `idempotency_key` are coordinator-minted and present;
>    exactly one `runtime_target_id` is bound; `filesystem_scope_ref` is
>    present and digest-bound; and the durable dispatch-attempt lifecycle
>    is wired. The classification SHALL NOT be a caller-supplied field and
>    SHALL be committed into the request canonical digest.
> 2. For a `RUNTIME_DISPATCH_LOCAL_CLI_V1`-classified request, POL-005
>    SHALL return *not-triggered*, meaning only that POL-005 does not
>    categorically preclude ordinary evaluation.
> 3. A dedicated policy (`POL-013`) SHALL evaluate the full predicate
>    conjunction and SHALL return `DENY` (never `ALLOW`, never
>    `HUMAN_REVIEW`) on any missing, malformed, unknown-state, or broader
>    predicate.
> 4. Eligibility SHALL NOT weaken the `DENY > HUMAN_REVIEW > ALLOW`
>    precedence, SHALL NOT suppress any other policy, and SHALL NOT by
>    itself produce `ALLOW`. Every other non-simulation request of every
>    action type and execution class SHALL continue to receive POL-005's
>    unconditional `DENY`.
> 5. A final `ALLOW` for such a request means only §2's bounded statement;
>    Gates 7–10 each independently gate the effect; runtime execution
>    availability, Runtime Enforcement, containment, and the durable
>    pre-dispatch record remain separate mandatory gates.

**Versioning of the PBRD change:** MINOR (§34) — no request fact added or
removed; no precedence change; the clause spells out the rule §12 already
mandated ("The future change SHALL be a narrowly scoped eligibility
rule …"). The `.1R.23` IV re-derives that this is MINOR-consistent.

---

## 32. Exact conceptual POL-005 delta (phase prompt §39 — no production edit)

| Aspect | Old (current) | New (proposed for `.1R.22`) |
|---|---|---|
| **Match domain** | every request with `simulation_only == false`, all action types, all execution classes | every request with `simulation_only == false` **except** a request the trusted builder classified `RUNTIME_DISPATCH_LOCAL_CLI_V1` |
| **Exclusion / conjunction** | none | exactly one class; the class holds only when the P1–P21 conjunction (§7) is fully satisfied and trusted-derived |
| **Provenance requirements** | none (unconditional) | the classification MUST come from the sealed trusted request builder; `_valid_runtime_dispatch_request` must have passed; a missing seal → structural DENY before POL-005 is even reached |
| **Action on trigger** | unconditional `DENY`, NG-025 / INV-001 / COMP-002 | unchanged for every non-`…_V1` request |
| **Action when not triggered** | (only when `simulation_only == true`) | additionally: *not-triggered* for a `…_V1` request — meaning only "POL-005 does not categorically block"; **no ALLOW implied** |
| **Hard-DENY fallback** | n/a | any `…_V1` predicate failure → POL-005 retains its `DENY` match (the classification was not achieved) + `POL-013` DENY |
| **Other-policy precedence** | orthogonal | unchanged — POL-001/003/004/006/007 and the composition algorithm are untouched; HUMAN_REVIEW still dominates ALLOW |
| **Policy ID** | `POL-005` | `POL-005` (retained; versioned canonical-statement amendment) |
| **NG-025 canonical statement** | "unconditionally active by construction" | versioned annotation: "unconditionally active for every non-simulation request except the single trusted-derived `RUNTIME_DISPATCH_LOCAL_CLI_V1` class; see PBRD-001 §12a" |

**Implementation sketch for `.1R.22` (planning reference only — not code to
apply now):**

```python
def evaluate(self, request):
    if request.simulation_only:
        return _not_triggered("POL-005")
    if is_trusted_narrow_local_cli_dispatch_v1(request):   # derived, seal-checked
        return _not_triggered("POL-005")                   # not ALLOW — just "not categorically blocking"
    return PolicyResult(... DENY, NG-025, INV-001, COMP-002 ...)   # unchanged
```

where `is_trusted_narrow_local_cli_dispatch_v1` reads only the
trusted-derived `profile_classification` marker set by the builder (§33),
never a caller field.

---

## 33. PB request representation, trusted builder, digest/binding (phase prompt §40, §41, §42)

**Can the current `PermissionBrokerRequest` / `RuntimeDispatchRequestFacts`
represent all trusted narrow-profile evidence without a schema change?** —
**Almost. Two additive internal fields are required.**

| Evidence | Already representable? | Gap → `.1R.22` addition |
|---|:--:|---|
| local CLI origin | yes | — (`transport_type` const) |
| network prohibition | yes | — (`network_requirement` const) |
| no credential/provider field | yes | — (structurally absent) |
| attempt / idempotency identity | yes | — |
| human-authority binding | yes | — |
| runtime target / filesystem scope | yes | — |
| **supply-chain admission of the executable** | **no** | add `admission_record_digest` (+ `admission_class`) to `RuntimeDispatchAdapterDescriptorBinding` — populated by N-16-6's admitted-descriptor preflight; **not** caller input |
| **the narrow-profile classification itself (P21)** | **no** | add a derived, non-caller `profile_classification: str` (value `RUNTIME_DISPATCH_LOCAL_CLI_V1` or `""`) to `RuntimeDispatchRequestFacts`, set **only** by `build_runtime_dispatch_permission_broker_request` from P1–P20; `_valid_runtime_dispatch_request` fails closed if it is set without the seal or inconsistent with the other facts |

**Trusted builder (phase prompt §41).** The **only** builder allowed to
populate the two new fields is
`build_runtime_dispatch_permission_broker_request` in
`runtime_dispatch_permission.py` (already the sole seal holder). It computes
`profile_classification` last, after every other fact is validated and the
N-16-6 admission binding resolves. The caller cannot supply either field
(the generic `build_permission_broker_request` already rejects any
`runtime_dispatch_context`).

**Digest / commitment binding (phase prompt §42).** Both new fields are
inside `RuntimeDispatchRequestFacts` → covered by PBRD §5's "canonical
digest over the complete Foundation envelope plus all fourteen facts" (the
count description updates to "the runtime-dispatch subject facts"; no
*logical* fact is added — `admission_record_digest` is a sub-field of the
existing fact 8, and `profile_classification` is a derived commitment over
the others). Transitively the classification is committed into
`consumption.json` `record_digest` at Gate 9 (RDGO §10 item 6 PB binding).
No policy-critical field is left unbound. A change to any predicate changes
`profile_classification` derivation → changes the request digest → expires
any prior PB decision (defensive matrix case 17).

---

## 34. Versioning adjudication (phase prompt §34)

| Artifact | Change | Adjudication | Rationale |
|---|---|---|---|
| **PBRD-001** | new §12a spelling out the narrow-eligibility rule | **MINOR** | §12 already mandates "a narrowly scoped eligibility rule"; §12a defines it; no request fact added/removed, no precedence change, no execution-class change, no old valid request invalidated. PBRD §16: additive request evidence / clarification may increment MINOR when meanings/behaviour/precedence are unchanged. |
| **Permission Broker Foundation — POL-005 canonical statement** | match domain gains one trusted-derived carve-out | **Versioned canonical-statement amendment (POL-005 keeps its ID); semantically MAJOR-class → carried with explicit migration + independent verification** | The RE No-Go Registry / policy-registry convention: "Canonical statements amended only via versioned change". This is not additive — POL-005 stops matching one class. Treated with MAJOR rigour (migration note + `.1R.23` IV) but **without** a new policy ID, to preserve audit-trail continuity (§35). |
| **`POL-013` (new policy)** | new conjunctive eligibility policy, applicable to `runtime_dispatch`/`adapter` only, never emits ALLOW | **New additive policy** | Additive to the registry; changes no existing policy's behaviour; PBPA-scoped applicability. |
| **PB request schema** (`RuntimeDispatchRequestFacts` + `RuntimeDispatchAdapterDescriptorBinding`) | two additive **internal, non-caller** fields (`profile_classification`, `admission_record_digest`/`admission_class`) | **Additive; no MAJOR** | No caller-visible field; existing callers unaffected (`runtime_dispatch_context` stays `None`); backward compatible. PBRD MINOR covers the representation. |
| **RE No-Go Registry** | NG-025 canonical-statement annotation | **Additive annotation only** (schema unchanged) | Parallels the schema-1.1 precedent (V-13-3-2): annotation, no ID/blocking-verdict change. |
| **RDGO-001** | none | **no change** | Gate 6 already "owns PB policy exclusively"; §7 wording ("`DENY` … stops the flow") is unaffected — a non-triggered POL-005 for `…_V1` is not a DENY. |
| **RIHAC-001 / RIASC-001 / HPAC-001 / RPAC-001 / PBPA-001** | none | **no change** | N-16-3 reads their outputs; adds nothing to them. |
| **N-15-5-1 hygiene debt** | not touched | **deferred** (§58) | Unrelated PBRD duplicate-"§4a" numbering; no direct cross-reference to N-16-3 becomes ambiguous. |

**Versions chosen only after the semantic analysis above, per phase prompt
§34.**

---

## 35. POL-005 version / identity question (phase prompt §35)

POL-005's match semantics change (it stops matching one narrow class).
Options considered:

| Option | Verdict |
|---|---|
| POL-005 keeps ID + versioned canonical-statement amendment | **SELECTED** — preserves historical meaning and the audit trail (every prior `causing_policy_ids=("POL-005",)` decision stays interpretable); the amendment is explicit, dated, and IV'd; the carve-out is a single named trusted-derived class |
| "POL-005 v2" as a distinct policy ID | rejected — fragments the audit history; NG-025 references would need dual mapping |
| POL-005 narrowed + a new policy for the carve-out | **partially adopted** — the *carve-out gate* is the new `POL-013`; but POL-005 itself is amended, not replaced |
| Superseding rule / new policy ID replacing POL-005 | rejected — §12 forbids "deletion of POL-005" |

**Result:** POL-005 **retains its ID**; canonical statement amended under a
versioned change ("v2 semantics") naming exactly the
`RUNTIME_DISPATCH_LOCAL_CLI_V1` carve-out; `POL-013` is the new companion;
NG-025 gets a parallel annotation. Historical auditability preserved.

---

## 36. Backward compatibility (phase prompt §36)

| Concern | Guarantee |
|---|---|
| existing callers of `build_permission_broker_request` | unaffected — the function still rejects any `runtime_dispatch` action / `runtime_dispatch_context`; `simulation_only` default `True`; POL-005 behaviour identical for them |
| existing `PermissionBrokerRequest` consumers / configs | `runtime_dispatch_context` stays `None`; the two new internal fields live on `RuntimeDispatchRequestFacts` only |
| legacy runtime-dispatch requests (pre-`…_V1`) | `profile_classification == ""` → POL-005 DENYs exactly as today; no legacy request becomes eligible accidentally (defensive matrix case 18) |
| provider / network / credential requests | still blocked — outside `…_V1` by construction (P4 / P5 / P6) |
| the dry `adapter_invocation` / `simulation_only=true` path | untouched (PBRD §13); not migrated |
| stored PB decisions / `consumption.json` `/2.0` and `/2.1` records | unaffected; `/2.0` remains gate-10-ineligible independently |

**No legacy caller becomes eligible accidentally.**

---

## 37. Fail-closed parser/schema behaviour + defensive test matrix (phase prompt §37, §48)

**Fail-closed (phase prompt §37).** Unknown or malformed new policy fields
MUST NOT be read as narrow-profile eligibility: `profile_classification`
with any value other than the exact literal `RUNTIME_DISPATCH_LOCAL_CLI_V1`
→ treated as absent → POL-005 DENY + `POL-013` DENY. An
`admission_record_digest` that does not resolve to a canonical admission
record → `POL-013` DENY. `_valid_runtime_dispatch_request` rejects a
`profile_classification` set without a matching seal or inconsistent with
P1–P20.

**Defensive policy test matrix (to be implemented in `.1R.22`; verified in
`.1R.23`) — 25 cases, every one asserting NO external effect:**

| # | Case | Expected |
|---:|---|---|
| 1 | existing `runtime_dispatch` request without a narrow profile | DENY (POL-005) |
| 2 | caller-forged `profile_classification` field (no seal / generic builder) | construction rejected → structural DENY |
| 3 | trusted local-CLI origin but missing executable admission binding | `POL-013` DENY + POL-005 DENY |
| 4 | admitted executable but a dynamic / non-fixed argv | `POL-013` DENY |
| 5 | fixed argv but `network_requirement=true` | `POL-013` DENY (+ `_valid_runtime_dispatch_request` already rejects) |
| 6 | credential field present in the request | construction rejected |
| 7 | shell / command-string field requested | construction rejected / `POL-013` DENY |
| 8 | wrong / aliased `runtime_target_id` | DENY (no alias; subject mismatch) |
| 9 | deterministic / NON_REAL human-authority lineage | ineligible — Gate 5 hard-stop; `approval_present=false` → POL-004 HUMAN_REVIEW; `POL-013` DENY |
| 10 | missing Gate-9 / attempt binding where required | `POL-013` DENY |
| 11 | malformed profile evidence (bad digest, unknown enum) | fail closed → DENY |
| 12 | all narrow predicates structurally valid | no POL-005 categorical block; `POL-013` not-triggered; **decision still gated by every other policy** |
| 13 | case 12 + another DENY policy triggered | DENY (that policy) |
| 14 | case 12 + `approval_present=false` | HUMAN_REVIEW (POL-004) — dominates ALLOW |
| 15 | narrow profile never directly returns ALLOW by classification alone | ALLOW only via `_compose` default (no DENY/HUMAN_REVIEW) |
| 16 | PB decision bound to the exact invocation / attempt | decision digest over 14 facts; changing `attempt_id` → new evaluation |
| 17 | mutate any profile predicate after construction | request digest changes → prior decision expired |
| 18 | old callers (legacy action types) | unaffected — POL-005 identical |
| 19 | provider / network class request | still blocked |
| 20 | credentialed class request | still blocked |
| 21 | arbitrary executable path (no admission record) | blocked |
| 22 | arbitrary argv | blocked |
| 23 | unsupported adapter class (not `local_fixed_argv`) | `POL-013` DENY |
| 24 | runtime unavailable (`EXECUTION_AVAILABILITY != "available"`) | still no effect downstream (Gate 10) even if Gate 6 is eligible |
| 25 | no first-effect implementation exists | `grep 'adapter.dispatch('` over `src/pcae` → zero call sites |

Plus (phase prompt §61 planning-traceability checks, not functional tests
for unchanged code): every §7 predicate has an owning source in §12; no
caller-controlled predicate is treated as trusted (§11 / §12); every
rejected option (§10) has explicit rationale; the versioning/dependency
matrix (§34) is complete.

---

## 38. Anticipated contract files (phase prompt §68, §71)

| File | Anticipated `.1R.22` change | Version |
|---|---|---|
| `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | new §12a (narrow-eligibility rule text — §31) | PBRD-001 v2.1 → **v2.2 (MINOR)** |
| Permission Broker Foundation policy registry doc (`docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md` / a new POL-013 freeze doc) | POL-005 canonical-statement amendment; `POL-013` definition | versioned amendment + additive policy |
| `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` | NG-025 canonical-statement annotation | schema unchanged; annotation only |
| `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` | `POL-013` applicability entry (`runtime_dispatch`/`adapter` only) | additive |
| `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` | note that the Gate-6 consumer passes the derived classification through | additive clarification (possibly none) |

---

## 39. Anticipated production files (phase prompt §71)

| File | Anticipated `.1R.22` change |
|---|---|
| `src/pcae/core/permission_broker_foundation.py` | `ExecutionDisabledRule.evaluate` gains the `is_trusted_narrow_local_cli_dispatch_v1` carve-out; new `NarrowLocalCliDispatchEligibilityRule` (POL-013); `RuntimeDispatchRequestFacts` gains derived `profile_classification`; `RuntimeDispatchAdapterDescriptorBinding` gains `admission_record_digest` / `admission_class`; `_valid_runtime_dispatch_request` gains classification-consistency checks; register POL-013 in `PolicyRegistry` |
| `src/pcae/core/runtime_dispatch_permission.py` | `build_runtime_dispatch_permission_broker_request` derives `profile_classification` from P1–P20 after all other validation; resolves the N-16-6 admission binding (behind an interface — N-16-6 supplies the store) |
| `src/pcae/core/policy.py` | if the shared policy catalogue lists POL IDs, add POL-013 |
| tests | new `tests/test_runtime_dispatch_narrow_eligibility_3w1r2b1r1_1r22.py` (the §37 matrix); scope-fence guard widenings for the touched files (the recurring lesson — subset checks over the exact authorized filename set, no wildcard) |

**No** `adapter.dispatch()` call site. **No** runtime capability change.
**No** N-16-6 store implementation (interface only; `.1R.22` may ship a
NON-admitting stub that always fails closed, so the profile stays
unsatisfiable).

---

## 40. Implementation decomposition (phase prompt §52, §65) — frozen

| ID | Title | Scope | Effect? | Authorization |
|---|---|---|:--:|---|
| **`149O.20L.7O.3W.1R.2B.1R.1.1R.22`** | **N-16-3 Narrow-Eligibility Policy and Contract Implementation** | PBRD-001 §12a (→ v2.2 MINOR); POL-005 canonical-statement amendment; new `POL-013` conjunctive eligibility policy (never emits ALLOW); derived `profile_classification` + `admission_record_digest` internal request fields via the trusted builder; N-16-6 admission-binding **interface** with a fail-closed stub; the §37 25-case defensive test matrix; scope-fence guard reconciliation. **No `adapter.dispatch()` call site, no runtime capability change, no N-16-6 store, no execution enablement. The narrow profile remains unsatisfiable in production (§47).** | none | separate explicit human authorization required |
| **`149O.20L.7O.3W.1R.2B.1R.1.1R.23`** | **Independent Verification of the N-16-3 Narrow-Eligibility Policy** | RE-DERIVE against PBRD-001 §12 / §16, `_compose`, current source: old callers still DENY; no human-approval override; the classification is trusted-derived at every predicate; default-deny outside the exact profile; `DENY > HUMAN_REVIEW > ALLOW` intact; all broader effect classes still blocked; POL-005 still hard DENY for everything else; no `ALLOW` reachable in production (profile unsatisfiable); no execution / runtime / contract-semantics drift beyond the approved N-16-3 change; fixed-SHA A/B | observes only | separate explicit human authorization required |

Then proceed to the next unresolved prerequisite (N-16-4 — §41).
**`.1R.22` / `.1R.23` are RECOMMENDED, not reserved.** No IDs above
`.1R.23` are reserved. Slice C / Slice D keep **no phase ID**. Do not
implement either `.1R.22` or `.1R.23` in this phase.

---

## 41. N-16-4..7 dependency ordering (phase prompt §54, §55, §56)

**Proposed ordering (dependencies derived, not assumed):**

```
N-16-3 (this plan; impl .1R.22 / IV .1R.23)   POL-005 narrow eligibility
   -> N-16-4   real, positive, single-attempt Runtime Enforcement gate over the full RDGO v3.1 projection
   -> N-16-5   real FIDO2 / WebAuthn / CTAP + protected human-approval UI
   -> N-16-6   RPAC-REQ-095 fixed-argv external-executable adapter + supply-chain admission store
   -> N-16-7   runtime capability enablement (Observed -> Approved/Executable)
   -> Slice C  first concrete effect adapter integration      -- NO PHASE ID
   -> Slice D  independent end-to-end verification             -- NO PHASE ID
```

| Edge | Dependency rationale |
|---|---|
| N-16-3 → N-16-4 | A positive Gate-7 result is meaningless while Gate 6 upstream DENYs (POL-005). N-16-3 first gives N-16-4 a coherent eligibility target. N-16-4 does not *technically* need N-16-3 to build, but the ordering keeps the chain coherent and testable end-to-end. |
| **Should N-16-5 precede N-16-4? (phase prompt §55)** | **No — N-16-4 first.** A structural positive Runtime Enforcement path can be implemented and verified while real HPAC remains unreachable (Gate 7 evaluates the *projection*, and a NON_REAL lineage still fails closed at Gate 7 today — `.1R.16` §30.1 point 2). N-16-4 is contract/structure work with **no hardware dependency** and lower risk. N-16-5 (real FIDO2/CTAP + protected UI) has a hardware + UX dependency and higher integration risk; doing the lower-risk structural gate first means N-16-5 slots into an already-verified positive RE path. |
| N-16-5 → N-16-6 | The adapter + supply-chain admission (N-16-6) is only exercisable end-to-end once a real approval can be produced (N-16-5); building N-16-6 earlier is possible but its integration test needs N-16-5. |
| N-16-6 → N-16-7 | Capability enablement (N-16-7) must not precede a real admitted adapter — enabling execution with no admitted executable would be an unsafe intermediate state. |
| **N-16-7 strictly last (phase prompt §56)** | Proven: `all policy (N-16-3) + runtime enforcement (N-16-4) + human authentication (N-16-5) + adapter admission (N-16-6) + Gate-10 lifecycle (Slice A/B, done)` must each independently verify before runtime moves off `unavailable`. RDGO §11 item 5 + `.1R.16` §33: capability is re-read from *current* state at Gate 10; promoting it earlier creates a window where a PB ALLOW + RE ALLOW could reach a Gate 10 that finds capability available but no admitted adapter. **Capability promotion is never folded into an earlier prerequisite.** |

Each of N-16-4..7 is **its own explicitly authorized implementation + IV
pair**. Slice C / D keep no phase ID until N-16-3..7 all close.

---

## 42. Runtime zero-effect evidence (phase prompt §62)

| Assertion | Evidence |
|---|---|
| PB policy production source modified | **no** — `git diff --name-only ced1b934 HEAD -- src/pcae` empty |
| runtime state modified | **no** — `runtime_introspection` constants byte-unchanged; `pcae runtime inspect` byte-identical at entry and finalization |
| adapter registration | **no** — `RuntimeRegistry` empty; 0 plugins / 0 capabilities |
| runtime subprocess effect | **0** — the only subprocesses this phase are `git` (history/read), `pcae` (governed lifecycle), and read-only shell inspection |
| provider / network | **0** |
| credential operation | **0** |
| hardware operation | **0** |
| first external effect | **0** — no `adapter.dispatch(` call site anywhere in `src/pcae`; Gate 10's effect keeps no phase ID |
| normative contract modified | **no** — `git diff --name-only ced1b934 HEAD -- docs/contracts docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` empty |
| POL-005 behaviour | unchanged — `ExecutionDisabledRule` byte-identical; still hard DENY for every non-simulation request |

---

## 43. Contract identity (phase prompt §59)

All normative contracts and production policy source byte-unchanged this
phase: RDGO-001 v3.1, PBRD-001 v2.1, HPAC-001 v2.1, RIHAC-001 v2.0,
RIASC-001 v3.0, RPAC-001 v1.0, PBPA-001, POL-005
(`permission_broker_foundation.py`), RE No-Go Registry schema 1.1.
Verified by `git diff --name-only ced1b934 HEAD -- docs/contracts
docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md src/pcae` (empty).

---

## 44. No-go conditions and STOP-condition check (phase prompt §70)

No valid early-STOP condition applies:

- PBRD / POL / RDGO contracts are **not** mutually contradictory — a
  bounded planning conclusion (§21) was reached.
- N-16-3 is resolvable **without** changing fundamental permission
  semantics: `_compose` precedence, POL-005's universal applicability, and
  the `DENY > HUMAN_REVIEW > ALLOW` order are all preserved; the change is a
  single trusted-derived carve-out.
- The model does **not** make human approval override Permission Broker
  policy (§9, §12) — approval is one predicate among twenty-one and never
  touches POL-005's match logic or precedence.
- The model does **not** require runtime execution enablement to define its
  contract — the rule is fully expressible now and ships unsatisfiable
  (§47).
- **No prerequisite earlier than N-16-3** was discovered (§3.4).
- Repository state is coherent (`pcae health` / `check` / `status
  coherence` all pass; `origin/main..HEAD = 0`).
- No required local tool is unavailable.

**No BLOCKED condition reached. The phase completes through full governed
finalization.**

---

## 45. `.3` governance incident

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved. Only
the primary human-authorized operator holds `.1R.21` lifecycle authority;
no delegated worker committed, finalized, or pushed.

---

*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.21.*
