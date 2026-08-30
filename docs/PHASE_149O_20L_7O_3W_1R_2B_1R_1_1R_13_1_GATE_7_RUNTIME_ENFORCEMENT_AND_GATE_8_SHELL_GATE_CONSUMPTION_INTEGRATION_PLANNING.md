# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.1 — Gate-7 Runtime Enforcement and Gate-8 Shell Gate Consumption Integration Planning

Status: **PLANNING ONLY — NOT IMPLEMENTED.** No production source modified.
No contract modified. No Gate-7 (Runtime Enforcement) coordinator code, no
Gate-8 (Shell Gate / process containment) coordinator code, no Gate-9
consumption code, no adapter/dispatch code written. No runtime capability
enabled. No real subprocess, provider, network, credential, or hardware
operation. No `.1R.14` work begun. Runtime remains
`not_implemented / Observed / observe / unavailable`; POL-005 unchanged;
real execution UNAVAILABLE.

This phase is architecture/planning only. It independently derives, from
the frozen contracts and current `src/pcae/**`, the exact contract
responsibility of RDGO-001 v3.0 **Gate 7 (Runtime Enforcement)** and
**Gate 8 (process containment and live preflight — the Shell Gate
boundary)**; the Gate-6 → Gate-7 and Gate-7 → Gate-8 handoffs; ownership;
input/output/provenance models; runtime-posture behavior under
`Observed / observe / unavailable`; stale-state, failure, and idempotency
models; the Gate-8 → Gate-9 handoff contract that `.1R.14` will consume;
the precise criteria that must be met before `.1R.14` may begin; the
defensive validation matrices; the anticipated production-file matrix; and
freezes the exact implementation and independent-verification phase IDs for
the Gate-7 and Gate-8 chapters.

Gate numbering in this document is **RDGO-001 v3.0 numbering** (§1 of that
contract): Gate 5 = approval validation, Gate 6 = Permission Broker, Gate 7
= Runtime Enforcement, Gate 8 = process containment and live preflight,
Gate 9 = durable pre-dispatch record + atomic authority consumption, Gate
10 = adapter dispatch (first external effect). This matches the "Gate 5..10
runtime-dispatch chain" numbering used across the `.1R.9`–`.1R.13` family.

---

## 1. Current verified milestone

Re-derived from the frozen contracts, current `src/pcae/**`, and the
`.1R.9`–`.1R.13` phase documents — not from summary prose. Treated as
independently verified unless fresh primary evidence disproves it.

### 1.1 HPAC / authority (carried, verified)

- Canonical HPAC foundation — VERIFIED (`.1R.3.2.2.1` family, `.1R.8`
  fixed-SHA reconfirmation): principal-registry trust root, fixture
  non-upgradability (`HPACStoreAuthority.writer` — no `PRODUCTION` writer
  exists), protected-presentation provenance, `HPAC-PRESENTATION-EVIDENCE/
  2.0`, `HPAC-REQ-092` attestation schema, authoritative lifecycle genesis,
  canonical-store containment (`HPAC_PROTECTED_ROOT`, deployment-scoped,
  `production()` fails closed on this host).
- Mechanism-neutral HPAC verifier — VERIFIED (`.1R.5.2.1`, F1 CLOSED):
  `verify_human_authentication` / `reverify_authenticated_principal`;
  verifier-owned `AuthenticatedHumanPrincipal` provenance (identity-only
  `__eq__`/`__hash__`, `__reduce__` raises, registry + verification-context
  membership); deterministic NON-REAL assurance preserved (every obtainable
  verifier result is `FIXTURE_NON_REAL`).
- B1 / B7 / N1 / N2 production authority repair — CLOSED and independently
  verified (`.1R.8`, non-blocking O1–O4). Change isolated to
  `runtime_authority.py`, `runtime_dispatch_permission.py`,
  `hpac_verifier.py`.

### 1.2 Gate 5 — CLOSED

`.1R.10` implementation + `.1R.11` independent verification (VERIFIED WITH
NON-BLOCKING FINDINGS):

- `runtime_dispatch_gate5.run_gate5` is the frozen Option-C layered
  coordinator; it OWNS "Gate 5 ran" by sequencing the already-verified
  RIHAC-001 v2.0 §16 sub-checks and confirming the HPAC lifecycle
  sequence-3 `PROOF_VERIFIED_AND_BOUND` binding (HPAC-REQ-097).
- `Gate5Result` is ephemeral, identity-only, non-serializable, registry-
  provenanced (`_GATE5_RESULTS`); `is_gate5_result` is exact-object
  membership only.
- The deterministic NON-REAL hard stop is inherited from
  `validate_approval` (`runtime_authority.py`): no projection is emitted
  unless `principal.assurance_class is HPACAuthorityClass.PRODUCTION`, and
  no deterministically-writable HPAC store can carry `PRODUCTION`. **Gate 5
  therefore returns fail-closed in production for every real request today.**
- Gate 5 consumes nothing and is idempotently repeatable.

### 1.3 Gate 6 — CLOSED

`.1R.12` implementation + `.1R.13` independent verification (VERIFIED WITH
NON-BLOCKING FINDINGS — GATE-6 CLOSED at the PB production-consumption
boundary):

- `runtime_dispatch_permission.run_gate6_permission_broker` is the **sole**
  production Gate-6 owner and the only production caller of the `.1R.7`
  trusted `runtime_dispatch` request builder.
- It consumes a registry-provenanced `Gate5Result` only (`is_gate5_result`),
  re-binds its `ValidatedAuthorityProjection` to the exact canonical
  invocation (`invocation_id` equality + `subject_scope_binding_digest`
  recompute inside the trusted builder), evaluates through the
  **byte-unmodified** canonical `PermissionBroker` evaluator exactly once,
  and returns exactly one ephemeral, non-transferable `Gate6Decision`.
- `DENY > HUMAN_REVIEW > ALLOW` precedence and POL-005's hard DENY of every
  `simulation_only=False` request are owned entirely by the evaluator and
  preserved unchanged. Validated (would-be) human authority does not
  override POL-005.
- `Gate6Decision` is not an execution token: an `ALLOW` means only "PB
  policy would permit this if execution existed" (`implementation_status`
  stays `execution_unavailable`).
- **No Gate-7, Gate-8, Gate-9, or Gate-10 path exists** from Gate 6 (AST
  forbidden-import scan; 0 `consumption.json`).
- Gate 6 consumes nothing.

### 1.4 Current runtime posture (re-asserted this phase)

```text
pcae runtime inspect →
  Runtime status:            not_implemented
  Runtime state:             Observed
  Execution capability:      unavailable
  Maximum plugin capability: observe
  Permission Broker status:  execution_unavailable
  Governance posture:        non-executing
```

`POL-005` (`ExecutionDisabledRule`) is unchanged and universal. Every
truthful `simulation_only=false` request — including `runtime_dispatch` —
is denied.

---

## 2. Current unresolved sequence

```text
Gate 5  — CLOSED   (runtime_dispatch_gate5.run_gate5)
   ↓
Gate 6  — CLOSED   (runtime_dispatch_permission.run_gate6_permission_broker)
   ↓
Gate 7  — NOT DEFINED as a production consumption coordinator
   ↓
Gate 8  — NOT DEFINED as a production consumption coordinator
   ↓
Gate 9  — .1R.14 FROZEN, BLOCKED (needs Gate-7 + Gate-8 chapters, or an
          explicit human-authorized test-path-first scope)
   ↓
Gate 10 — first external effect (no production adapter dispatch exists)
```

This phase defines Gate 7 and Gate 8 precisely enough that a later
Gate-8 → Gate-9 handoff contract can let `.1R.14` proceed safely. It does
not implement any of them.

---

## 3. Primary source material inspected

### 3.1 Contracts (read in full)

| Short ID | Repository artifact | Version / status |
|---|---|---|
| RDGO-001 | `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` | v3.0 — FROZEN (correctively completed) |
| PBRD-001 | `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | v2.0 — FROZEN |
| RPAC-001 | `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` | v1.0 |
| RIHAC-001 | `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` | v2.0 |
| RIASC-001 | `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` | v3.0 |
| HPAC-001 | `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` | v2.0 |
| PBPA-001 | `docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` | v1.0 |
| PB prod. consumption | `docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md` | — |
| POL-005 | `src/pcae/core/policy.py` (`ExecutionDisabledRule`) + PB foundation | source |

### 3.2 Phase documents

`.1R.9` (Gate-5/Gate-9 planning), `.1R.10` (Gate-5 impl), `.1R.11` (Gate-5
independent verification), `.1R.12` (Gate-6 impl), `.1R.13` (Gate-6
independent verification), and the `.1R.6`/`.1R.7`/`.1R.8` B1/B7/N1/N2
family.

### 3.3 Current source (read)

- `src/pcae/core/runtime_dispatch_gate5.py` — Gate-5 coordinator (309 lines).
- `src/pcae/core/runtime_dispatch_permission.py` — trusted `runtime_dispatch`
  request builder + Gate-6 coordinator (880 lines).
- `src/pcae/core/runtime_enforcement_safety_authorization.py` — **design-only
  constants** (Phase 104C): 12 authorization flag names (all default
  `False`), 5 safety flag names (all default `True`), `AUTH_FLAG_TO_NO_GO` /
  `SAFETY_FLAG_TO_NO_GO` mappings, non-executing validation helpers. **No
  decision engine, no evaluator, no coordinator.** (95 lines.)
- `src/pcae/core/enforcement_readiness.py` + `src/pcae/commands/
  enforcement_readiness.py` — **read-only readiness reporter** over the
  Phase 89J 69-gate checklist; `ENFORCEMENT_NOT_AUTHORIZED`; no runtime
  decision.
- `src/pcae/core/enforcement_audit.py`, `enforcement_approval.py`,
  `enforcement_rollback.py` — Phase 89 design/simulation models (audit event
  model, operator-approval model, rollback artifact model). Simulation-only.
- `src/pcae/core/shell_gate.py` — **read-only command classifier** (Phase
  88P family, 1719 lines): 24 command categories, 26 decision values;
  `build_shell_gate()` returns a structured gate envelope. It **never
  executes classified command text**. The only `subprocess.run` call is
  `_call_doctor_test_run` invoking `pcae doctor test-run --json` (a governed
  read-only introspection for the test-run lock), not the classified
  command.
- `src/pcae/commands/shell_gate.py` — the `pcae shell-gate` CLI surface
  over the classifier (162 lines).
- `src/pcae/core/runtime_adapter.py`, `mock_runtime_adapter.py` —
  simulation-only adapter protocol + mock; explicitly import no
  `subprocess`, `os.system`, `popen`, `spawn`, `exec*`, `pty`.
- `src/pcae/core/runtime_invocation_authority_consumption.py` — the inert
  Gate-9 model/store (create-only atomicity, digest self-check); **no
  production consumer.**
- `src/pcae/core/runtime_registry.py`, `runtime_introspection.py`,
  `runtime_context.py`, `runtime_snapshot.py`, `advisory_runtime.py` —
  observation-only runtime posture and capability introspection.

### 3.4 Effect-boundary conclusion

There is **no production Runtime Enforcement decision engine** and **no
production process-containment / dispatch mechanism** in the repository.
"Runtime Enforcement" and "Shell Gate" exist today only as design-only
constant tables, simulation models, and a read-only classifier. Gate 7 and
Gate 8 as **production consumption coordinators** must be built new; the
question this plan answers is what they consume, own, output, and reject.

---

## 4. Re-derived RDGO Gate-7 contract responsibility

Independently derived from RDGO-001 v3.0 §8 (and §1 table row 7, §14, §15,
§19), not from the label "Runtime Enforcement".

### 4.1 Exact contract text (RDGO-001 §8, verbatim)

> Runtime Enforcement receives:
> 1. the full immutable request and all fourteen PBRD-001 binding facts
>    (including `attempt_id` and `idempotency_key`);
> 2. the PB decision, policy IDs, policy version, and decision digest;
> 3. the validated approval reference and freshness verdict digest; and
> 4. static/current target-status and preflight facts.
>
> It independently evaluates the complete bound request. It SHALL NOT infer
> approval from PB ALLOW, permission from approval, capability from the
> target name, or containment from a planned profile.
>
> Its positive decision is single-attempt, expiring, and invalid across any
> relevant input or policy change. A denial, failure, stale input,
> unavailable target, or unresolved no-go stops the flow. No real process
> has been launched at this gate.

RDGO-001 §1 table row 7: Owner = "Runtime Enforcement coordinator"; Input =
"Full bound request, PB evidence, validated approval ref/freshness,
preflight facts"; Output = "Single-attempt final whether-to-invoke
decision"; External effect = "No".

RDGO-001 §14: "Gate 7 is the final whether-to-invoke execution-attempt
decision point."

### 4.2 What Gate 7 owns (mapped to the §5 checklist in the phase prompt)

| Candidate responsibility | Owned by Gate 7? | Contract basis |
|---|---|---|
| Runtime policy enforcement (an independent whether-to-invoke decision over the whole bound request) | **YES — this is the core** | §8 "independently evaluates the complete bound request"; §14 "final whether-to-invoke decision point" |
| Execution-mode / posture check (is real execution available at all) | **YES** | §8 "unavailable target … stops the flow"; §19 "Runtime unavailable/target mismatch -> no dispatch" (Gates 4/8 named, but Gate 7's independent evaluation subsumes the current-status facts of §8 item 4); §15 "Runtime Enforcement has no cache validity across any … target/status … change" |
| Capability eligibility (does the runtime/plugin capability model permit this `requested_capability`) | **YES — as an independent check**, not inferred from the target name | §8 "SHALL NOT infer … capability from the target name"; RDGO-001 §0 wall `PB ALLOW != runtime capability`, `runtime capability != Runtime Enforcement approval` |
| Runtime-target eligibility (is *this exact* target permitted to be invoked now) | **YES** | §8 item 4 "static/current target-status"; §15 target/status recheck |
| Provider / backend eligibility | **YES**, to the extent the target descriptor names a backend/transport; local-CLI-v1 only (`transport_type=local_cli`, PBRD-001 §4 fact 11) | §8 item 1 (all 14 facts, incl. `adapter_descriptor_binding`); PBRD-001 §14 "static and current live-preflight target/status facts" |
| Repository / runtime-environment eligibility (HEAD, task, prompt, config still match) | **YES — freshness/currentness revalidation** | §8 item 3 "freshness verdict digest"; §15 TOCTOU table (HEAD, task, prompt, target, adapter config, policy version) "Recheck before PB" *and* the §8 independent evaluation |
| Establishing *how* the process is launched (executable path, argv, cwd, env, child-process limits, resource limits, supervision) | **NO — that is Gate 8** | §9 "Gate 8 … controls how the one permitted local process may be launched" |
| Human authentication / approval creation | **NO — Gate 3 creates, Gate 5 validates** | §4, §6; §8 "SHALL NOT infer … permission from approval" |
| PB policy evaluation | **NO — Gate 6** | §7; §8 "SHALL NOT infer approval from PB ALLOW" (Gate 7 consumes the PB decision as evidence, never re-runs PB) |
| Approval / proof / presentation / challenge consumption | **NO — Gate 9 only** | §10 "`dispatch_attempted` is the single atomic … consumption point" |
| Durable pre-dispatch record | **NO — Gate 9** | §10 |
| Adapter dispatch / subprocess creation | **NO — Gate 10** | §11 |

### 4.3 One-sentence freeze

> **Gate 7 is the single, independent, non-consuming "final whether-to-
> invoke" decision over the complete bound `runtime_dispatch` request: it
> re-evaluates authority freshness, PB evidence, target/capability/posture
> eligibility, and repository/task/prompt/config currentness, and emits one
> ephemeral, single-attempt, expiring `Gate7Result` that authorizes nothing
> by itself and that Gate 8 must independently re-validate.**

### 4.4 What Gate 7 must NOT become

- It must not merge PB's policy decision, human approval, runtime
  capability, or containment into one authority (RDGO-001 §0, §21
  "Merging authority/permission/enforcement/containment … remains
  incompatible").
- Its output must not be a transferable capability token (§8, §11 patterns;
  mirror `Gate5Result`/`Gate6Decision` discipline — §11 of this doc).
- It must not launch, spawn, or preflight a real executable ("No real
  process has been launched at this gate").
- It must not reinterpret an upstream DENY or HUMAN_REVIEW as ALLOW (§8.7 of
  this doc).

---

## 5. Re-derived RDGO Gate-8 contract responsibility

Independently derived from RDGO-001 v3.0 §9 (and §1 table row 8, §13, §19),
not from the assumption that "Shell Gate" means only shell-command
filtering.

### 5.1 Exact contract text (RDGO-001 §9, verbatim)

> Gate 8 is owned by Shell Gate or an equivalent future process-containment
> mechanism. It controls how the one permitted local process may be
> launched; it is not an extension of PB's policy decision.
>
> Before gate 9 it SHALL:
> - re-resolve the exact descriptor/config and verify no drift;
> - resolve the exact executable without accepting a caller shell string;
> - verify executable identity/hash/version against the descriptor pin;
> - confirm installation and current local availability;
> - recheck repository fingerprint, HEAD, task state/digest, target,
>   prompt, adapter config, and current policy/RE decision;
> - establish exact cwd, argument vector, environment allowlist,
>   child-process prohibition/limit, resource/time limit, and supervision;
> - confirm network remains denied and no credential access is required;
>   and
> - bind the established containment evidence to the invocation.
>
> No dispatch occurs unless containment is successfully established. A live
> preflight check is an observation of readiness, never authority or
> permission.

RDGO-001 §1 table row 8: Owner = "Shell Gate/equivalent containment owner";
Input = "Exact executable/config, cwd, arguments, environment allowlist, RE
decision"; Output = "Established bounded process environment + live-preflight
evidence"; External effect = "No dispatch yet".

### 5.2 What Gate 8 owns (mapped to the §6 checklist in the phase prompt)

| Candidate responsibility | Owned by Gate 8? | Contract basis |
|---|---|---|
| Command / effect description validation (the exact executable + argv the process would run) | **YES** | §9 "resolve the exact executable"; "establish exact … argument vector" |
| Shell-command authorization in the sense of "no caller shell string is honored" | **YES — by rejecting shell strings entirely** | §9 "without accepting a caller shell string"; §11 "SHALL use an argument vector, not unrestricted shell evaluation" |
| Argument / working-directory / environment validation | **YES** | §9 "establish exact cwd, argument vector, environment allowlist" |
| Subprocess eligibility as *containment establishment* (child-process prohibition/limit, resource/time limit, supervision) | **YES** | §9 |
| Executable supply-chain identity (hash/version against the descriptor pin; installation + current local availability) | **YES** | §9; PBRD-001 §12 item 6 "local executable supply-chain identity and live preflight" |
| Descriptor/config drift re-resolution + repository/HEAD/task/target/prompt/policy/RE re-check | **YES — the live-preflight half of §13's static-vs-live table** | §9; §13 "Live preflight (gate 8)" column |
| Network-denied + no-credential-access confirmation | **YES** | §9 |
| Binding the established containment evidence to the invocation | **YES** | §9 "bind the established containment evidence to the invocation" |
| External-tool gatekeeping / adapter invocation eligibility as a *policy* question | **NO — that is Gate 6 (PB) and Gate 7 (RE)** | §9 "it is not an extension of PB's policy decision" |
| Actually spawning the process | **NO — Gate 10** | §11 |
| Consuming approval / proof / writing the durable record | **NO — Gate 9** | §10 |
| Re-deciding whether to invoke | **NO — Gate 7 already did; Gate 8 refuses to proceed if the RE decision is stale, but does not re-derive it** | §9 "recheck … current policy/RE decision" (recheck, not re-decide) |

### 5.3 One-sentence freeze

> **Gate 8 is the process-containment boundary: given a positive Gate-7
> decision, it re-resolves descriptor/executable/repository/policy drift,
> refuses any caller shell string, and constructs + attests one exact
> bounded launch environment (executable identity, argv, cwd, env
> allowlist, child-process/resource/time limits, supervision, network
> denied, no credentials), binding that containment evidence to the
> invocation — and it performs no dispatch and consumes nothing.**

### 5.4 What Gate 8 must NOT become

- It must not execute, spawn, fork, or `exec` anything (RDGO-001 §9; the
  current `shell_gate.py` invariant "never executes command text" must be
  preserved by the new coordinator).
- It must not accept a caller-supplied shell string or command string
  (§9; PBRD-001 §6 "untrusted executable or shell command strings").
- It must not widen scope beyond the Gate-7-approved request (§11 patterns).
- Its live-preflight observations must not be treated as authority or
  permission (§9 last sentence).
- It must not write `consumption.json` or consume any approval/proof
  (§10 — Gate 9 owns that).

---

## 6. Gate-6 → Gate-7 handoff

### 6.1 Contract-defined form

PBRD-001 v2.0 §14 ("Runtime Enforcement projection") is the normative
handoff definition. The future coordinator projects to Runtime Enforcement:

1. the full immutable PB request including all fourteen facts;
2. PB decision, causing/matched policy IDs, policy version, and decision
   digest;
3. validated approval reference plus validation/freshness verdict digest;
   and
4. static and current live-preflight target/status facts.

> "The raw approval and PB internals SHALL NOT be duplicated wholesale when
> references/digests suffice. Runtime Enforcement independently evaluates
> the complete projection; it does not rubber-stamp PB or approval."

RDGO-001 §8 restates the same four items.

### 6.2 Which of the phase-prompt options this is

| Option | Description | Verdict |
|---|---|---|
| A | `Gate6Decision` alone | **Rejected** — insufficient; the projection must also carry the validated approval reference/freshness digest and the target/status/preflight facts (§14 items 3–4), which `Gate6Decision` does not hold. |
| B | `Gate6Decision` + canonical invocation/runtime context | Closer, but still under-specified against §14 item 4. |
| C | **A new layered coordinator input assembled from `Gate6Decision` + the re-resolved Gate-5 authority projection + current target/capability/posture facts** | **SELECTED.** This is the exact §14 four-item projection. It mirrors the Gate-6 pattern: `run_gate7_runtime_enforcement` takes the trusted `Gate6Decision` (registry-provenanced), the trusted `Gate5Result` (registry-provenanced, re-resolved), the `RuntimeDispatchIdentity`, the `RuntimeDispatchRequestConstructionInput`, a current-time string, and a current runtime-status/preflight fact bundle; it re-derives the PB request through the same trusted builder or verifies the `Gate6Decision`'s bound `request_id`, and independently evaluates. |
| D | Another contract-defined form | Not indicated. |

### 6.3 The wall that must be preserved

```text
PB decision != runtime capability
```

RDGO-001 §0. Gate 7 receives the PB decision **as evidence**. A PB `ALLOW`
is not runtime capability; Gate 7 must independently establish (or, under
the current posture, fail to establish) capability. Concretely: even a
hypothetical PB `ALLOW` must yield a Gate-7 **reject** while
`Execution capability: unavailable` (see §13).

### 6.4 Provenance requirement on the handoff

Gate 7 must accept a `Gate6Decision` **only** if
`runtime_dispatch_permission.is_gate6_decision` vouches for it — the exact
object a prior successful `run_gate6_permission_broker` returned. A
caller-built `Gate6Decision`, a field-equivalent reconstruction, a copy, a
serialized clone, or a bare `decision="ALLOW"` object all fail closed
(mirrors Gate 6's treatment of `Gate5Result`; RDGO-001 §8; the B1 defect
class). Because `Gate6Decision.__reduce__` raises and `is_gate6_decision`
is exact-object registry membership, this is already structurally enforced
by the existing `.1R.12` code — Gate 7 just has to call the predicate.

---

## 7. Gate-6 decision semantics at Gate 7

### 7.1 Required behavior

RDGO-001 §8, §19; PBRD-001 §9, §10.

```text
Gate6Decision.decision == "DENY"          -> Gate 7 unreachable / reject (no Gate7Result)
Gate6Decision.decision == "HUMAN_REVIEW"  -> Gate 7 unreachable / reject (no Gate7Result)
Gate6Decision.decision == "ALLOW"         -> Gate 7 MAY proceed to its own independent evaluation only
```

- `DENY` — RDGO-001 §19 "PB DENY/failure -> no dispatch | Stop". Gate 7
  returns `(None, ("gate7_pb_decision_not_allow:DENY",))`.
- `HUMAN_REVIEW` — RDGO-001 §19 "HUMAN_REVIEW without satisfied authority ->
  no dispatch". PBRD-001 §8: "`HUMAN_REVIEW` is not authorization and v1
  defines no PB mechanism that converts it into dispatch permission." Gate 7
  **must not** treat `HUMAN_REVIEW` as a soft ALLOW. It returns
  `(None, ("gate7_pb_decision_not_allow:HUMAN_REVIEW",))`. There is no
  "resolve the review inside Gate 7" path.
- `ALLOW` — Gate 7 proceeds to its own evaluation. `ALLOW` is a
  precondition, never a conclusion (RDGO-001 §19 "PB ALLOW without valid
  authority -> no dispatch | RE must deny/fail").

### 7.2 Anti-escalation invariant

> **No Gate-7 code path converts `HUMAN_REVIEW` or `DENY` into a positive
> `Gate7Result`. The only decision value that permits Gate 7 to continue is
> the literal string `"ALLOW"`, checked by exact equality, on a
> registry-provenanced `Gate6Decision`.**

### 7.3 POL-005 relationship (see also §15)

Because POL-005 hard-DENYs every `simulation_only=False` `runtime_dispatch`
request today, a real production Gate-6 call returns `DENY`. Gate 7 is
therefore **unreachable on the real production path** right now — its
`DENY` short-circuit fires first. This is correct and is not a defect.

---

## 8. Gate-7 ownership

### 8.1 Decision (frozen)

**A new coordinator module** — proposed `src/pcae/core/runtime_dispatch_gate7.py`
— `run_gate7_runtime_enforcement(...)`, exactly mirroring the shape of
`runtime_dispatch_gate5.run_gate5` and
`runtime_dispatch_permission.run_gate6_permission_broker`.

### 8.2 Why not the existing components

| Candidate | Rejected because |
|---|---|
| `runtime_enforcement_safety_authorization.py` | Design-only constant table (Phase 104C). It has no evaluation logic and its docstring says "Non-executing. Non-authorizing." It may be **consumed** by the new coordinator as the canonical `AUTH_FLAG_TO_NO_GO` / `SAFETY_FLAG_TO_NO_GO` vocabulary, but it is not the owner. |
| `enforcement_readiness.py` | Read-only readiness reporter over a static 69-gate checklist. Wrong abstraction (project readiness, not per-request runtime decision). |
| `enforcement_approval.py` / `enforcement_audit.py` / `enforcement_rollback.py` | Phase 89 simulation models for a *different* enforcement concept (source-mutation enforcement), not RDGO-001 runtime dispatch. Reusing them would conflate two enforcement domains. |
| Extending `runtime_dispatch_permission.py` (the Gate-6 module) | Would blur the Gate-6/Gate-7 trust boundary that `.1R.13` just verified as clean ("no Gate-7 path exists"). Keep them separate modules with a one-directional `gate7 imports gate6` dependency. |

### 8.3 Duplication avoidance

The new coordinator SHALL NOT re-implement: PB policy semantics (call
nothing; consume the `Gate6Decision`), RIHAC validation (re-resolve the
projection via `is_trusted_validated_authority_projection` +
`revalidate_validated_authority_projection`, never re-run `validate_approval`
itself unless the design review shows §14 item 3 "freshness verdict digest"
requires a fresh Gate-5 re-run — see §10.4), or the NON-REAL hard stop
(inherited). It OWNS only: the independent whether-to-invoke decision, the
capability/posture/target eligibility check, the currentness re-check, and
the ephemeral `Gate7Result`.

---

## 9. Runtime Enforcement consumption model (current implementation inspection)

### 9.1 What exists today

`runtime_enforcement_safety_authorization.py` (the only file that could be
called "the Runtime Enforcement implementation"):

| Aspect | Current state |
|---|---|
| Inputs | none — it is a constant module |
| Decision model | none — helper predicates `validate_all_authorization_false`, `validate_all_safety_true` return lists of violations; no verdict type |
| Policy sources | `AUTHORIZATION_FLAG_NAMES` (12), `SAFETY_FLAG_NAMES` (5), `AUTH_FLAG_TO_NO_GO` / `SAFETY_FLAG_TO_NO_GO` (RE-NOGO-001..011) |
| Capability model | `execution_available` / `execution_authorized` flags, both default `False`, both mapped to `RE-NOGO-002` |
| Effect model | none |
| Side effects | none |
| Currently advisory / non-executing? | **Yes** — module docstring: "Design-only. Non-executing. Non-authorizing." |
| Safely callable from a Gate-7 coordinator without enabling execution? | **Yes** — it computes nothing and touches nothing; it is a vocabulary + a pure violation-lister |

### 9.2 Consequence for the plan

The Gate-7 coordinator does not "wire up" an existing engine — there is no
engine. It **is** the engine, built new, that:

- consumes the §6.2-Option-C projection;
- computes an authorization-flag / safety-flag snapshot from the **current
  runtime posture** (`runtime_introspection` / `runtime_context` — all
  authorization flags currently `False`, all safety flags currently `True`);
- maps every `False` authorization flag it needs, and every `True` safety
  flag (`simulation_only`, `no_execution`, `evidence_only`,
  `non_authorizing`, `design_only`), to its `RE-NOGO-*` id via the existing
  constant tables;
- returns a **negative** `Gate7Result` (a structured no-go set) whenever
  any blocking no-go is matched — which, under the current posture, is
  **always** (`RE-NOGO-001`, `RE-NOGO-002`, `RE-NOGO-010`, `RE-NOGO-011`
  are all matched).

### 9.3 The wall that must be preserved

```text
Runtime Enforcement decision != external effect
```

A `Gate7Result` — even a hypothetical positive one — creates no process,
no containment, no dispatch. It is evidence consumed by Gate 8, which
itself creates no effect (Gate 10 does).

---

## 10. Gate-7 input / output / provenance / runtime-posture / stale / failure / idempotency

### 10.1 Input (frozen shape)

`run_gate7_runtime_enforcement(gate6_decision, *, gate5_result, identity,
inputs, authority_current_time, runtime_status_facts, broker=None)`:

- `gate6_decision` — accepted only if `is_gate6_decision(gate6_decision)`;
- `gate5_result` — accepted only if `is_gate5_result(gate5_result)`, and
  `gate5_result.invocation_id == identity.invocation_id`;
- `identity` — `type(identity) is RuntimeDispatchIdentity`;
- `inputs` — `type(inputs) is RuntimeDispatchRequestConstructionInput`;
- `authority_current_time` — bounded string;
- `runtime_status_facts` — a closed, coordinator-resolved object carrying
  the current `runtime inspect` posture (status, state, execution
  capability, max plugin capability, PB status, governance posture) plus
  the static-preflight facts from RDGO-001 §5 (registry/descriptor/config
  presence + version, `transport_type`, declared capability, digests,
  `network_requirement=false`, filesystem-scope/process-profile refs,
  working-dir shape, "representable within local-CLI-v1 scope"). The
  coordinator resolves these itself from the trusted runtime-introspection
  surface; it does not accept a caller-supplied "eligible=true".

### 10.2 Output model (frozen — mirrors `Gate5Result` / `Gate6Decision`)

`Gate7Result`:

- constructed only behind a module-private `_seal`; `is_gate7_result` is
  **exact-object membership** in a process-local `_GATE7_RESULTS` set whose
  only insertion point is `run_gate7_runtime_enforcement`'s success path;
- `__reduce__` raises (non-serializable);
- `__eq__` / `__hash__` are identity-only (`self is other` / `id(self)`);
- `__init_subclass__` raises;
- carries: `decision` (`"ALLOW"` / `"DENY"` — no `HUMAN_REVIEW` at Gate 7;
  Gate 7 is a binary whether-to-invoke gate), `matched_no_go_ids` (tuple),
  `causing_reason_ids` (tuple), `invocation_id`, `attempt_id`,
  `request_id`, `pb_decision_digest`, `authority_freshness_digest`,
  `evaluated_input_digest`, `expires_at` (single-attempt, expiring —
  RDGO-001 §8), `evaluated_at`;
- **not an execution token**: an `ALLOW` here means only "Runtime
  Enforcement would permit the invocation if execution capability existed";
  it is not process permission (RDGO-001 §0 wall
  `Runtime Enforcement ALLOW != process permission`), not containment, not
  dispatch.

Per RDGO-001 §10 item 7 ("Runtime Enforcement binding: decision ID/digest,
verdict, expiry, and evaluated-input digest"), the `Gate7Result` carries
exactly the fields Gate 9 will later need to record — but Gate 8, not Gate
9, is its immediate consumer.

### 10.3 Provenance / anti-forgery

`shape != provenance` (RDGO-001 discipline). Gate 8 proves a `Gate7Result`
came from Gate 7 by calling `runtime_dispatch_gate7.is_gate7_result` —
exact-object registry membership — never `isinstance`, fields, or equality.
Same discipline as `Gate5Result` / `Gate6Decision`. This is the
already-established pattern; do not invent a new one.

### 10.4 Freshness re-resolution (RDGO-001 §14 item 3, §15)

Gate 7 SHALL, at its own point of use:

- re-check `is_trusted_validated_authority_projection(gate5_result.projection)`
  and `revalidate_validated_authority_projection(..., current_time=...)`
  (possession of a `Gate5Result` is never sufficient — `runtime_dispatch_gate5`
  docstring; HPAC-REQ-097 / §40.2);
- recompute the `subject_scope_binding_digest` from `identity` + `inputs`
  and compare (mirrors `project_human_authority_binding`);
- confirm `gate6_decision.invocation_id == identity.invocation_id` and
  `gate6_decision.attempt_id == identity.attempt_id`;
- **open design question for `.1R.13.2` review:** whether §14 item 3
  "validated approval reference plus validation/freshness verdict digest"
  requires Gate 7 to re-run the full Gate-5 coordinator (`run_gate5`) or
  whether re-trusting + revalidating the referenced projection satisfies
  it. Recommendation: re-trust + revalidate the projection (cheaper, and
  `run_gate5` is idempotent so a fresh run is also acceptable); the
  implementation phase MUST pick one explicitly and the verification phase
  MUST confirm the chosen path rejects a projection that was valid at Gate
  5/6 but revoked/expired before Gate 7.

### 10.5 Runtime-posture behavior (RDGO-001 §8; phase prompt §13)

Under `Observed / observe / unavailable`:

| Question | Answer | Basis |
|---|---|---|
| Does Gate 7 always reject because execution capability is unavailable? | **YES.** `runtime_status_facts.execution_capability != "available"` matches `RE-NOGO-002` (`execution_available` / `execution_authorized` both `False`); `no_execution` / `evidence_only` / `non_authorizing` safety flags match `RE-NOGO-001`; `design_only` matches `RE-NOGO-010`; `simulation_only` matches `RE-NOGO-011`. Any one blocking no-go ⇒ `Gate7Result(decision="DENY", matched_no_go_ids=(...))`. | RDGO-001 §8 "unavailable target … stops the flow"; §19 |
| Can it return a structural/advisory result while still denying progression? | **YES.** The negative `Gate7Result` *is* that structured result — it carries `matched_no_go_ids` and `causing_reason_ids` for audit — but `decision="DENY"` and no downstream gate may proceed. | §8; the `Gate6Decision` precedent (returns a real object on a `DENY` too) |
| Can a test-only structural path exist without becoming executable? | **YES**, with the same discipline as `.1R.13`: a test may substitute `is_gate6_decision` (or provide a synthetic `runtime_status_facts` with `execution_capability="available"`) to exercise the positive-branch mechanics, but the production path stays unreachable because (a) POL-005 makes the real `Gate6Decision` a `DENY`, and (b) the coordinator resolves `runtime_status_facts` itself from the real posture. No production test bypass. | `.1R.13` §12 precedent |

### 10.6 Gate-7 positive-path question (phase prompt §14)

> **Is a legitimate positive production Gate-7 success currently possible?
> NO.** Two independent reasons, either sufficient: (1) the real Gate-6
> call returns `DENY` (POL-005), so Gate 7 short-circuits before its own
> evaluation; (2) even given a hypothetical Gate-6 `ALLOW`, the current
> runtime posture matches at least four blocking `RE-NOGO-*` ids.

Gate-7 mechanics are still implementable and testable without fabricating
runtime capability: the negative path is the production path and is fully
testable; the positive-branch mechanics are testable through a
clearly-labelled test boundary that does not weaken the production
coordinator (§10.5 row 3).

### 10.7 Stale-state model (RDGO-001 §15)

Gate 7 re-checks: current runtime posture; runtime target; execution
availability; provider/backend availability (local-CLI descriptor); current
PB policy version (via the `Gate6Decision`'s `policy_version` vs a fresh
read — if drifted, reject with `gate7_pb_decision_stale_policy_version`);
repository fingerprint / HEAD / task state+digest / prompt hash / adapter
config (compare `inputs` against a fresh trusted read); execution mode. It
does **not** re-run Gate 3's human-authority ceremony or re-authenticate
the principal (Gate 5 owns that; Gate 7 re-trusts the projection only).

### 10.8 Failure model (fail-closed — RDGO-001 §0, §19)

`Gate7Result(decision="DENY", ...)` or `(None, reasons)` for every one of:

| Condition | Reason id |
|---|---|
| missing / untrusted `Gate6Decision` | `gate7_untrusted_gate6_decision` |
| `Gate6Decision.decision == "DENY"` | `gate7_pb_decision_not_allow:DENY` |
| `Gate6Decision.decision == "HUMAN_REVIEW"` | `gate7_pb_decision_not_allow:HUMAN_REVIEW` |
| missing / untrusted `Gate5Result` | `gate7_untrusted_gate5_result` |
| `gate5_result.invocation_id != identity.invocation_id` | `gate7_invocation_binding_mismatch` |
| stale / revoked / expired projection at Gate-7 revalidation | `gate7_stale_validated_authority_projection` |
| `subject_scope_binding_digest` mismatch | `gate7_authority_subject_scope_mismatch` |
| PB policy version drift since Gate 6 | `gate7_pb_decision_stale_policy_version` |
| repository / HEAD / task / prompt / adapter-config drift | `gate7_request_currentness_drift:<fact>` |
| runtime unavailable / execution capability not available | `gate7_runtime_execution_unavailable` (+ `RE-NOGO-002`) |
| unsupported runtime target / descriptor absent / not local-CLI-v1 representable | `gate7_runtime_target_ineligible` |
| any blocking safety flag set | `gate7_safety_no_go:<RE-NOGO-id>` |
| Runtime Enforcement internal error / exception | `gate7_internal_error_fail_closed` |

**No partial capability output** — a rejection creates no `Gate7Result`
that any later gate could treat as partial success.

### 10.9 Idempotency / repeatability (RDGO-001 §8, §17)

Gate 7 **consumes nothing** (no approval, proof, presentation, challenge,
nonce, or policy state changes; no `consumption.json`). It **may be
re-run**. A positive decision is single-attempt and expiring
(`expires_at`), and is invalid across any relevant input or policy change
(RDGO-001 §8 "invalid across any relevant input or policy change"; §15
"Runtime Enforcement has no cache validity"). Re-running Gate 7 after any
drift yields a fresh (or freshly-negative) result; a prior `Gate7Result`
is never a cache.

---

## 11. Gate-7 → Gate-8 handoff

### 11.1 What Gate 8 consumes from Gate 7

RDGO-001 §9 input row: "Exact executable/config, cwd, arguments,
environment allowlist, **RE decision**". So Gate 8 consumes:

1. the trusted `Gate7Result` (`is_gate7_result` — exact-object membership);
2. `Gate7Result.decision == "ALLOW"` by exact equality (a `DENY` `Gate7Result`
   is a hard stop — `gate8_gate7_decision_not_allow`);
3. the `RuntimeDispatchIdentity` and `RuntimeDispatchRequestConstructionInput`
   (for descriptor / repository / prompt / adapter-config re-resolution);
4. the re-resolved `Gate5Result` reference (for the §9 "recheck … current
   policy/RE decision" and the invocation binding);
5. a canonical **effect plan** — the exact executable path (descriptor-
   pinned, resolved by Gate 8 itself, never a caller string), the argument
   vector, the cwd, and the environment allowlist — assembled by the
   trusted coordinator from the descriptor/config, NOT from caller input.

### 11.2 Anti-substitution binding (phase prompt §25 — frozen)

Gate 8 SHALL reject:

| Substitution | Reject reason |
|---|---|
| `Gate7Result` A presented with effect plan B (different executable/argv) | `gate8_effect_plan_binding_mismatch` |
| `Gate7Result` A presented with invocation B (`invocation_id` / `attempt_id` mismatch) | `gate8_invocation_binding_mismatch` |
| changed `runtime_target_id` since Gate 7 | `gate8_runtime_target_drift` |
| changed executable identity/hash vs descriptor pin | `gate8_executable_identity_mismatch` |
| changed cwd | `gate8_cwd_drift` |
| changed environment allowlist | `gate8_environment_allowlist_drift` |
| changed provider/backend / transport | `gate8_transport_drift` |
| changed descriptor/config digest | `gate8_descriptor_config_drift` |
| any caller-supplied shell string or command string | `gate8_caller_shell_string_rejected` |

The binding is enforced by recomputing the exact `subject_scope_binding_digest`
and the adapter-descriptor digest from `identity` + `inputs` and comparing,
exactly as Gate 6 does, plus a fresh executable-hash comparison against the
descriptor pin (RDGO-001 §9, §15 "Adapter executable identity … Yes, exact
hash before spawn").

> **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-13-5-1
> normalization; `.1R.15.1` §11).** Three rows of this matrix ask Gate 8 to
> diff against a **bound reference the frozen `RuntimeDispatchRequestConstructionInput`
> shape does not contain**:
> - `changed provider/backend / transport → gate8_transport_drift`:
>   **STRUCK.** `transport_type` is the contract-fixed const `local_cli`
>   (PBRD-001 fact 11); there is no drift-able bound transport reference.
> - `changed cwd → gate8_cwd_drift` and `changed environment allowlist →
>   gate8_environment_allowlist_drift`: **reworded.** The verified Gate-8
>   behaviour is *repository-scope containment* of the working directory
>   (`gate8_cwd_outside_repository_scope`) + *name well-formedness* of the
>   environment allowlist, both **committed** into `containment_evidence_digest`
>   and **recomputed** by Gate 9 (RDGO-001 v3.1 §9 three-layer model). The
>   effect plan is trusted-coordinator-assembled, never caller input, so
>   there is no caller cwd/env "reference" to diff; substitution is caught
>   by Gate 9's full containment-evidence recomputation.
>
> The other six rows (effect-plan / invocation binding, runtime-target
> drift, executable identity/hash, descriptor/config digest,
> caller-shell-string rejection) are enforced as written and were confirmed
> by `.1R.13.5`. `.1R.15` closed V-13-5-1 for the consumption path.

---

## 12. Gate-8 ownership, input/output/provenance, Shell Gate model, no-effect guarantee

### 12.1 Ownership decision (frozen)

**A new coordinator module** — proposed `src/pcae/core/runtime_dispatch_gate8.py`
— `run_gate8_process_containment(...)`. It **consumes** the existing
`src/pcae/core/shell_gate.py` classifier for command-category validation
(defensive: confirm the resolved executable + argv classify as
`test_execution` / an allowlisted governed category and never as
`source_mutation` / `network_access` / `secret_access` / `destructive_*`),
but it does not replace it and does not extend it. The mature 88P
classifier stays the single owner of command classification; the new
coordinator owns containment establishment + drift re-resolution + the
`Gate8Result`.

### 12.2 Why not extend `shell_gate.py`

`shell_gate.py` is a general-purpose read-only classifier used by the
`pcae shell-gate` CLI for a different purpose (advising on arbitrary
proposed shell commands). Overloading it with RDGO-001 runtime-dispatch
containment would (a) couple two unrelated consumers, (b) risk the
classifier's "never executes" invariant during future edits, and (c)
duplicate the descriptor/repository/policy re-resolution that belongs to
the runtime-dispatch chain. Keep it as a consumed dependency.

### 12.3 Current Shell Gate implementation inspection

| Aspect | Current state (`shell_gate.py`) |
|---|---|
| Inputs | `repo_root: Path`, `command_text: str` |
| Allow/deny model | 26 decision values; `allow_read_only` / `allow_governed` / `allow_test_execution` / `requires_*` / `blocked_by_*` / `deny` |
| Environment validation | classifies `environment_mutation` → `requires_human_review`; does not construct an env allowlist |
| Command validation | `shlex`-split, program allowlists, category regexes; `_SGP_POLICY_FORBIDDEN_FILES` |
| cwd validation | not modeled (no cwd concept) |
| Subprocess relationship | **none for the classified command** — only `_call_doctor_test_run` runs `pcae doctor test-run --json` for the test-run lock |
| Side effects | none on the classified command; reads repo files for task-contract detection |
| Currently dispatches or only validates? | **Only validates / classifies.** Never executes classified command text (module docstring, verified by absence of `subprocess`/`Popen`/`exec` on the classified path) |
| Isolation from actual subprocess execution | structural — there is no code path from `build_shell_gate` to process creation of the classified command |

### 12.4 The wall that must be preserved

```text
Shell Gate validation != subprocess execution
```

The new Gate-8 coordinator SHALL import no `subprocess`, `os.system`,
`popen`, `spawn`, `exec*`, `pty`, `socket`, provider SDK, or HTTP client
(enforced by an AST guard in its verification suite, mirroring the
`.1R.10` Gate-5 guard). Executable-identity verification (RDGO-001 §9
"verify executable identity/hash/version") is a **file stat + hash read**,
not an execution.

### 12.5 Gate-8 input (frozen shape)

`run_gate8_process_containment(gate7_result, *, gate5_result, identity,
inputs, authority_current_time, descriptor_resolver, containment_profile)`:

- `gate7_result` — `is_gate7_result` + `decision == "ALLOW"`;
- `gate5_result` — `is_gate5_result` + invocation binding;
- `identity`, `inputs` — exact type guards;
- `descriptor_resolver` — a trusted, coordinator-supplied resolver for the
  exact executable path + hash + version from the pinned descriptor (never
  a caller string);
- `containment_profile` — the declared filesystem-scope / process-profile
  refs from `inputs` (already immutable IDs/digests in
  `RuntimeDispatchRequestConstructionInput`).

### 12.6 Gate-8 output model (frozen — mirrors the others)

`Gate8Result`:

- `_seal`-guarded construction; `is_gate8_result` = exact-object membership
  in `_GATE8_RESULTS` (only `run_gate8_process_containment`'s success path
  inserts);
- `__reduce__` raises; identity-only `__eq__` / `__hash__`;
  `__init_subclass__` raises;
- carries: `containment_established` (bool — `False` on any failure),
  `containment_evidence_digest` (SHA-256 over the closed containment object:
  executable path + hash + version, argv, cwd, env allowlist, child-process
  policy, resource/time limits, supervision, `network_denied=True`,
  `credentials_required=False`), `invocation_id`, `attempt_id`,
  `request_id`, `gate7_result_digest`, `live_preflight_digest`,
  `evaluated_at`, `expires_at`;
- **not an execution token** — RDGO-001 §0 wall
  `process permission != dispatch completion`; a `Gate8Result` is
  "containment is established and attested", never "the process ran".

### 12.7 Gate-8 provenance

`shape != provenance`. Gate 9 proves a `Gate8Result` came from Gate 8 via
`runtime_dispatch_gate8.is_gate8_result` (exact-object membership). Same
discipline as every prior gate.

### 12.8 No-effect guarantee (phase prompt §24 — frozen)

Gate 8 performs **validation and containment establishment only**. No
subprocess, no provider call, no adapter invocation, no shell execution, no
repository mutation, no network call, no credential operation. Gate 10
remains the first external effect. The verification phase MUST prove
(runtime counters + AST) zero subprocess/network/adapter calls from the
Gate-8 path.

### 12.9 Gate-8 runtime-posture reachability (phase prompt §23)

Because Gate 7 always rejects under the current posture (§10.6), **Gate 8
is structurally unreachable on the production path today.** Gate-8
mechanics are implementable and testable only through a clearly-labelled
test boundary (synthetic `Gate7Result` with `decision="ALLOW"`); the
production path stays unreachable via the Gate-5 NON-REAL stop and POL-005.
Document this explicitly in the implementation and verification phases. Do
**not** fabricate a production Gate-8 success.

### 12.10 Gate-8 stale-state / failure / idempotency

- Stale-state re-checks (RDGO-001 §9, §13 live-preflight column): exact
  descriptor/config drift; exact executable hash vs descriptor pin;
  installation + current local availability; repository fingerprint / HEAD
  / task state+digest / target / prompt / adapter config; current policy /
  RE decision (reject if the `Gate7Result` is expired or its
  `pb_decision_digest` no longer matches a fresh PB policy version); network
  still denied; no credential access required.
- Failure model (fail-closed): `Gate8Result(containment_established=False,
  ...)` or `(None, reasons)` for missing/untrusted `Gate7Result`,
  non-`ALLOW` `Gate7Result`, any drift row in §11.2, executable not
  installed / hash mismatch, env-allowlist construction failure,
  containment-supervision unavailable, caller shell string,
  network-not-deniable, internal error.
- Idempotency: Gate 8 **consumes nothing**. It may be re-run. Its result is
  expiring and invalid across any drift. Establishing containment is not a
  one-shot resource here (that is Gate 9's `dispatch_attempted`).

---

## 13. Runtime capability semantics (phase prompt §29)

Re-derived from `runtime_introspection` / `runtime_context` /
`runtime_enforcement_safety_authorization` and RPAC-001.

| Term | Meaning | Owner |
|---|---|---|
| `Observed` (runtime state) | PCAE observes runtime/plugin posture but performs no runtime execution; the runtime subsystem is `not_implemented` | `runtime_introspection` / `runtime_snapshot` |
| `Maximum plugin capability: observe` | The highest capability any registered plugin could hold is "observe" — no `invoke`, `dispatch`, or `mutate` capability is registrable | runtime capability registry (currently empty, 0 plugins) |
| `Execution capability: unavailable` | There is no code path that creates an external process for a `runtime_dispatch`; `execution_available` / `execution_authorized` flags are `False` | `runtime_enforcement_safety_authorization` flags + `runtime_context` |
| Can Runtime Enforcement ever return "eligible" under this state? | **No.** `RE-NOGO-002` is matched whenever `execution_available` is `False`. The Gate-7 coordinator owns this check; it is not inferred from PB or from the target name. | new Gate-7 coordinator |
| Which component owns the actual capability check? | The **Gate-7 coordinator** (new), reading the trusted runtime-introspection posture — **not** the Permission Broker (PBRD-001 §0 wall `PB ALLOW != runtime capability`), **not** Gate 8. | — |

```text
PB permission  !=  runtime capability
```

PB answers "does policy permit attempting this action class". Runtime
capability answers "does a runtime that can actually perform it exist and
is it available". These are separate gates by contract; the plan keeps them
in separate modules.

---

## 14. Gate-10 boundary (phase prompt §30 — frozen, do not modify)

RDGO-001 §11: "Gate 10 is the first external execution effect. It creates
at most one exact local process through the selected adapter and
already-established containment."

**Current source location of the (would-be) first effect:** there is **no
production adapter dispatch**. The adapter protocol is
`src/pcae/core/runtime_adapter.py` (`Adapter.dispatch(envelope) ->
DispatchReceipt`, `...` — abstract) and the only implementation is
`src/pcae/core/mock_runtime_adapter.py`, which is simulation-only and
explicitly imports no `subprocess` / `spawn` / `exec` / `pty`. The dry
path (`adapter_invocation` / `simulation_only=true`) is unchanged and out
of scope (RDGO-001 §20, PBRD-001 §13).

> **Gate 10 = first effect. No earlier gate (5, 6, 7, 8, 9) may invoke it.
> This phase does not create, name, or modify a production adapter-dispatch
> path.** When one is eventually built, it will be a new module consuming a
> `Gate9Result` (the durable `dispatch_attempted` record), never a
> `Gate7Result` or `Gate8Result` directly.

---

## 15. POL-005 relationship to Gate 7 (phase prompt §15 — frozen)

- POL-005 (`ExecutionDisabledRule`) acts at Gate 6 (PB). It is universal
  and byte-unchanged (PBRD-001 §12; `.1R.13` re-confirmed byte-identity).
- **Downstream invariant:** `POL-005 DENY => no Gate-7 success`. Gate 7's
  first check after provenance is `gate6_decision.decision == "ALLOW"`; a
  POL-005 `DENY` fails this by exact equality. No runtime-enforcement result
  can override a PB hard `DENY` (RDGO-001 §19 "PB DENY/failure -> no
  dispatch | Stop").
- Gate 7 SHALL NOT reinterpret an upstream `DENY` or `HUMAN_REVIEW`
  (§7.2). There is no Gate-7 code path that inspects *why* PB denied and
  proceeds anyway.
- Symmetrically for Gate 8: a non-`ALLOW` `Gate7Result` is a hard stop;
  Gate 8 never re-derives the PB/RE decision.

---

## 16. Gate-8 → Gate-9 handoff (phase prompt §26 — the central deliverable)

`.1R.14` (Gate 9) is BLOCKED until this handoff contract is frozen. This
section freezes **only the handoff contract**, not the Gate-9
implementation.

### 16.1 What Gate 9 will require from Gate 8

Derived from RDGO-001 §10 (the eight durable items) — items 5, 6, 7, 8 and
the containment reference come through the Gate-7/Gate-8 chain:

```text
Gate 9 input from the Gate-7/Gate-8 chain =
    trusted Gate8Result            (is_gate8_result — exact object)
  + Gate8Result.containment_established == True
  + containment_evidence_digest    (RDGO-001 §10 item 8 "exact containment
                                    evidence reference")
  + trusted Gate7Result            (is_gate7_result — exact object;
                                    reachable via Gate8Result.gate7_result_digest
                                    cross-check)
  + Gate7Result decision/digest/verdict/expiry/evaluated_input_digest
                                    (RDGO-001 §10 item 7 verbatim)
  + trusted Gate6Decision lineage  (PB request/decision digest, decision,
                                    policy version, causing policy IDs,
                                    matched no-go IDs — RDGO-001 §10 item 6)
  + trusted Gate5Result lineage    (approval ID/digest, RIHAC v2 projection
                                    ID/digest, HPAC proof ID/digest,
                                    presentation/challenge/subject digests,
                                    proof-validation/current-registry
                                    digests — RDGO-001 §10 item 5)
  + RuntimeDispatchIdentity        (invocation_id, attempt_id,
                                    idempotency_key — RDGO-001 §10 item 1)
  + RuntimeDispatchRequestConstructionInput
                                    (repository/task/target/prompt/adapter
                                    bindings — RDGO-001 §10 items 2/3/4)
  + current capability snapshot    (re-read inside the Gate-9 serialization
                                    boundary — RDGO-001 §10 last ¶)
```

### 16.2 Handoff invariants (frozen)

1. **Exact-object provenance at every link.** Gate 9 accepts a `Gate8Result`
   only via `is_gate8_result`; it re-derives the `Gate7Result` provenance
   via `is_gate7_result`; the `Gate6Decision` via `is_gate6_decision`; the
   `Gate5Result` via `is_gate5_result`. No field-reconstruction, copy, or
   serialized clone at any link (RDGO-001 §8/§9; the B1 defect class).
2. **Single consistent invocation.** `invocation_id` and `attempt_id` are
   equal across Gate5Result / Gate6Decision / Gate7Result / Gate8Result /
   identity (RDGO-001 §10a "Every gate from 2 through 11 … SHALL carry the
   same `attempt_id` unchanged").
3. **Containment binding.** `Gate8Result.containment_evidence_digest` is
   recomputed by Gate 9 from the referenced containment object and compared
   (RDGO-001 §10 "read-back-verified").
4. **In-boundary revalidation.** Gate 9 re-validates registry, credential,
   descriptor/config, presentation, proof/lifecycle, approval/expiry, PB,
   RE, and containment state **while holding the protected serialization
   boundary** (RDGO-001 §10 last ¶). A `Gate7Result` / `Gate8Result` that
   was valid moments earlier but is now expired/stale fails closed with no
   `consumption.json`.
   > **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-15-1).** "while
   > holding the protected serialization boundary" is normalized: there is
   > **no held lock** (see `.1R.9` §13.5 erratum). The per-`proof_id`
   > create-only atomic primitive is the linearization point; the
   > revalidation battery plus a final zero-effectful-I/O
   > authority-generation-token re-check (`S1`/`S2`) run immediately before
   > the create; any change fails closed. RDGO-001 v3.1 §10 / HPAC-001 v2.1
   > HPAC-REQ-099 are the normalized statement.
5. **Consumption happens only at Gate 9.** Neither the `Gate7Result` nor
   the `Gate8Result` is consumed by being handed to Gate 9; the atomic
   `dispatch_attempted` write is the single consumption point (RDGO-001
   §10, §28 of this doc).
6. **No effect.** The handoff carries data only; Gate 9's write is "no
   process effect yet" (RDGO-001 §1 table row 9).

### 16.3 Representation

The handoff is an in-process assembly of the five trusted objects +
`identity` + `inputs` + a fresh capability snapshot, passed as explicit
keyword arguments to the future `run_gate9_*` coordinator. It is **not**
serialized, **not** persisted before Gate 9's own atomic write, and **not**
a bearer token. This mirrors `.1R.9` §16.1 slice 3's framing exactly.

---

## 17. Gate-9 unblocking criteria (phase prompt §27 — frozen)

`.1R.14` (Gate-9 Atomic Authority Consumption Coordinator Integration
Implementation) MAY begin only when **all** of the following hold:

1. **Gate-7 implementation complete** — `.1R.13.2` closed, a
   `run_gate7_runtime_enforcement` coordinator exists with the §10 model.
2. **Gate-7 independently verified** — `.1R.13.3` closed, VERIFIED (with or
   without non-blocking findings), re-deriving §10's input/output/provenance/
   posture/failure/idempotency models against the implementation, not from
   `.1R.13.2`'s own report/tests.
3. **Gate-8 implementation complete** — `.1R.13.4` closed, a
   `run_gate8_process_containment` coordinator exists with the §12 model.
4. **Gate-8 independently verified** — `.1R.13.5` closed, VERIFIED,
   re-deriving §12's model and the §11.2 anti-substitution matrix.
5. **The Gate-8 → Gate-9 handoff contract of §16 is frozen** (this
   document, once `.1R.13.1` completes) and unchanged, or amended only by a
   further explicit human-authorized planning phase.
6. **No unresolved blocking findings** from `.1R.13.2`–`.1R.13.5`.
7. **Runtime still non-executing** — `pcae runtime inspect` still reports
   `not_implemented / Observed / observe / unavailable`; POL-005 unchanged;
   no real adapter registered — **unless** a separately explicit human
   authorization has recorded a different posture with its own verification.
8. **Independent verification of this handoff contract** — either folded
   into `.1R.13.5` (Gate-8 verification re-checks §16) or a dedicated
   note; the `.1R.14` startup check MUST confirm §16 was independently
   reviewed.

`.1R.14` additionally retains its **own** pre-existing precondition from
`.1R.9` §16.2: it is BLOCKED regardless until either (a) the Gate-7 and
Gate-8 chapters exist (criteria 1–4 above — now the expected path), or (b)
an explicit human authorization records a test-path-first scope. Criteria
1–4 satisfy path (a). `.1R.15` (Gate-9 independent verification) stays
frozen behind `.1R.14`.

`.1R.14` / `.1R.15` are **NOT renumbered** by this phase.

---

## 18. No proof / approval consumption at Gate 7 or Gate 8 (phase prompt §28 — frozen)

```text
Gate 7 consumes nothing
Gate 8 consumes nothing
Gate 9 owns atomic proof + approval consumption
```

- Neither coordinator creates, deletes, or mutates any approval, HPAC
  proof, presentation, challenge, or nonce record. Neither writes a
  `consumption.json`. Neither calls
  `runtime_invocation_authority_consumption` primitives.
- Both re-**read** canonical state (projection revalidation, descriptor
  re-resolution, executable hash) — reads are not consumption.
- The verification phases MUST prove (filesystem-write counters + AST) zero
  writes to `HPAC_PROTECTED_ROOT`, the approval store, the lifecycle store,
  or the consumption store from the Gate-7 and Gate-8 paths.

---

## 19. Existing-architecture compatibility (phase prompt §31, §32)

### 19.1 Runtime Enforcement (Gate 7)

The existing `runtime_enforcement_safety_authorization.py` provides the
**canonical no-go vocabulary** (`AUTHORIZATION_FLAG_NAMES`,
`SAFETY_FLAG_NAMES`, `AUTH_FLAG_TO_NO_GO`, `SAFETY_FLAG_TO_NO_GO`,
`RE-NOGO-001..011`) and the pure violation-lister helpers. The Gate-7
coordinator **consumes** these constants; it does not reimplement or
replace them.

> **Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-13-3-2;
> RE No-Go Registry schema 1.1).** Where §13 / this section describe the
> shared flag→no-go map as *the* Gate-7 no-go source, read it as **the sole
> source for the per-decision projection** (`Gate7Result.matched_no_go_ids`).
> The RE No-Go Registry (schema 1.1) classifies its 17 entries as
> per-decision (001–008, 010, 011), environmental-readiness (009, 013, 015,
> 016, 017 — enforced by the execution-enablement readiness process), and
> advisory (012, 014). `matched_no_go_ids` deliberately projects only the
> per-decision subset; Gate-7 progression depends on the authoritative
> Gate-7 decision, not on that projection's completeness. This is not a
> functional bypass — ten independent flag-mapped no-gos already force
> `DENY` under the current posture. No verified logic is duplicated because there is no verified
RE *decision* logic today — only the vocabulary, which is reused verbatim.
The Phase 89 `enforcement_*` simulation models are a different enforcement
domain (source-mutation) and are **not** touched.

### 19.2 Shell Gate (Gate 8)

The mature `shell_gate.py` 88P classifier is **consumed** by the Gate-8
coordinator for command-category validation of the resolved executable +
argv (defensive cross-check: the runtime-dispatch executable must classify
as an allowlisted governed/test category, never as a mutation/network/
secret/destructive category). The classifier's "never executes" invariant
and its 24-category / 26-decision model are reused unchanged. Only a new
**trusted coordinator/consumer** is added for containment establishment +
drift re-resolution + the `Gate8Result`. Mature validation is not replaced.

---

## 20. V-2 / V-3 contract alignment (phase prompt §33)

**V-2** — RDGO-001 §4/§6 say "Gate 5, not gate 3, creates the
`PROOF_VERIFIED_AND_BOUND` event"; the `.1R.11`-verified reality is that the
mechanism-neutral verifier's HPAC-REQ-054 **step 10** creates it at
`create_runtime_invocation_approval` (Gate-3) time and Gate 5 only
*confirms* it. **V-3** — the RIASC `record_digest` binding concern is
subsumed by V-2.

**Impact on Gate 7 / Gate 8: none.**

- Gate 7 and Gate 8 import nothing from `hpac_lifecycle` or `hpac_verifier`
  (this will be AST-enforced in `.1R.13.2` / `.1R.13.4`, mirroring the
  Gate-6 guard).
- They derive authority solely from `gate5_result.projection` — a
  `ValidatedAuthorityProjection` re-trusted at point of use — and never
  read, create, or depend on the HPAC lifecycle sequence-3 event or the
  disputed "which gate creates it" wording.
- The Gate-6 path already demonstrated this independence (`.1R.13` §11);
  Gate 7/8 sit further downstream and consume even less HPAC-specific state.

> **V-2 / V-3 — NON-BLOCKING (carried, unchanged); no Gate-7/Gate-8 impact,
> no amplification.** They remain candidates for the recommended
> contract-clarification phase alongside V-4. They do **not** create
> ambiguity in Gate-7/Gate-8 sequencing (both gates are strictly after Gate
> 5's confirmation and consume only its output object). No STOP condition.

---

## 21. V-4 contract alignment (phase prompt §34)

**V-4** — PBRD-001 §4 fact 14 enumerates a literal **7-field**
`human_authority_binding`; production
(`permission_broker_foundation.RuntimeDispatchHumanAuthorityBinding`) carries
**3 fields** (`approval_id`, `approval_record_digest`,
`validation_evidence_digest`). `.1R.13` §10 independently adjudicated this a
**lossless digest-collapse** (no lost authority semantics, no
contract-distinguishable collision — `validation_evidence_digest` commits
to all omitted semantics; `authority_projection_id` is enforced more
strongly by exact-object registry membership; `authority_contract_version`
is a zero-entropy constant).

**Do Gate 7 / Gate 8 consume any of the 7-field semantics directly?**

- **Gate 7:** consumes the **`Gate6Decision`** (PB decision + policy
  evidence) and the **re-resolved `Gate5Result.projection`** — it does not
  parse `human_authority_binding` field-by-field. It re-checks the
  projection's trust (`is_trusted_validated_authority_projection`) and
  revalidates it; the `subject_scope_binding_digest` recompute it performs
  is the same operational re-enforcement of `request_binding_digest` that
  `.1R.13` §10.3 already credits. **No direct dependence on the 7-vs-3
  field shape.**
- **Gate 8:** consumes the **`Gate7Result`** and re-resolves descriptor /
  executable / repository state — it touches `human_authority_binding` not
  at all. **No dependence.**

> **V-4 — NON-BLOCKING CONTRACT-ALIGNMENT DEBT (carried, unchanged).** Gate
> 7 / Gate 8 consume only the trusted upstream **objects**
> (`Gate5Result` / `Gate6Decision`), never the raw 3-field or 7-field
> binding; the digest-collapse is verified lossless. **Proven, not
> assumed:** the anticipated `.1R.13.2` / `.1R.13.4` suites include a test
> asserting the Gate-7 / Gate-8 modules import and reference neither
> `RuntimeDispatchHumanAuthorityBinding` nor the PBRD fact-14 subfields
> directly. This phase does **not** rewrite PBRD-001. V-4 remains a
> candidate for the dedicated contract-clarification phase (amend §4 fact
> 14 to document the digest-collapsed form, or require the 7 named
> subfields).

No STOP condition: V-4 creates no ambiguity in Gate-7/Gate-8 semantics.

---

## 22. V-13-1 disposition (phase prompt §35)

**V-13-1 (LOW — process transparency, non-blocking):** `.1R.12`'s canonical
report claimed "no isolation / consumer-inventory meta-guard trips" and
`fast_green: 699 passed, 0 failed`, but `.1R.12`'s single-file source
addition deterministically breaks two point-in-time frozen-baseline scope
guards from earlier phases:

- `test_gate5_..._1r10.py::test_only_expected_production_files_changed_since_baseline`
- `test_gate5_..._1r11.py::test_production_scope_is_exactly_the_three_planned_files`

Both are **non-functional** frozen-diff assertions (they pin "exactly these
N files changed since SHA X"); the `.1R.10` / `.1R.11` *functional*
closures are intact.

**Disposition for the Gate-7 / Gate-8 chapters:**

> **Replace with phase-aware invariant tests; do not carry forward
> permanently-stale frozen-diff assertions.** The `.1R.13.2` (Gate-7 impl)
> phase — which adds `runtime_dispatch_gate7.py` and will again trip these
> two guards plus any added since — SHALL, as part of its scope:
> (a) re-baseline the two named guards to the `.1R.13.1` completion SHA, or
> (b) convert them to phase-aware invariant tests (assert "the Gate-5/6
> production surface is a **subset** of {known files} and no *unexpected*
> file changed", rather than "exactly these three"), and
> (c) disclose in its own canonical report every point-in-time guard its
> source addition trips, with A/B (git-worktree) attribution — the
> transparency step `.1R.12` omitted.
> The `.1R.13.3` (Gate-7 verification) phase re-confirms the re-baseline /
> conversion is correct and that no *functional* regression hides behind
> it.

This is **planning-only guidance**; `.1R.13.1` performs no test maintenance
(no `src/` or `tests/` change this phase).

---

## 23. O1–O4 / F2–F4 / F7 review (phase prompt §36)

These findings originate in earlier `.1R.*` verification phases. Re-evaluated
here **only** for Gate-7 / Gate-8 consumption relevance; none is
re-adjudicated or silently closed. Definitive current text stays in each
originating phase document.

| Finding | Originating text (summary) | Becomes relevant to Gate 7 / Gate 8? | Disposition |
|---|---|---|---|
| **O1** — B1 positive-emission path unreachable under Option-A (`validate_approval` emits no projection today; NON-REAL stop) | `.1R.8` §26 | Gate 7 relies on the projection revalidation predicate; the **negative** path is fully reachable and testable. Positive-branch mechanics need a labelled test boundary (§10.5). | **Carried unchanged.** Inherent to the frozen NON-REAL staging, not a defect. Becomes end-to-end testable only once a real assurance mechanism exists. |
| **O2** — N1 canonical-store trust is path + file integrity, not a cryptographic writer seal | `.1R.8` §26 | **Marginally.** Gate 7 re-resolves the projection by trusting the registry-provenanced object, not the store file; Gate 8 re-reads descriptor/executable state. Neither assumes the approval store has writer provenance it lacks. | **Carried unchanged.** The Gate-7/Gate-8 coordinators MUST NOT assume store writer-provenance; they rely on exact-object registry membership + the protected-root boundary (which is stronger). A future writer-provenance chapter closes O2 if ever required. |
| **O3** — `test_*_detected_by_fresh_reverification` naming over-promise (F4 class) | `.1R.8` §26 | No — cosmetic. | **Carried.** New Gate-7/Gate-8 verification tests MUST be accurately named (state which stage rejects). |
| **O4** — historical `tasks/DONE.md` omissions (hygiene debt) | ongoing (`pcae doctor task-memory` warnings) | No — unrelated to runtime gates. | **Carried unchanged.** Not touched by this phase. Recommend a dedicated hygiene pass reconcile `tasks/done/` vs `tasks/DONE.md`. |
| **F2 / HPAC-REQ-054 Step 4** — independent challenge-digest recomputation | REPAIRED, `.1R.7`, `.1R.8`-verified | Indirectly load-bearing: Gate 7 re-trusts a projection whose creation required Step-4. Already implemented. | **Confirmed prerequisite already satisfied.** No new work. |
| **F3** — `.1R.4` "eight-step" planning-doc label debt | NON-BLOCKING, documentation-labeling only | No. | **Carried, deferred.** No repair required. |
| **F4** — `test_caller_constructed_verifier_result_rejected` name overclaim | NON-BLOCKING, cosmetic | No. | **Carried, deferred.** New tests accurately named (see O3). |
| **F7** — the identity registries resist caller-supplied-**data** forgery, **not** same-process **arbitrary code execution** | NON-BLOCKING observation, **not broadened** by any later phase | The new Gate-7/Gate-8 coordinators, their `_GATE7_RESULTS` / `_GATE8_RESULTS` registries, and their consumption of `Gate5Result` / `Gate6Decision` all run under the **same-account autonomous-agent assumption**. | **Carried unchanged — threat model NOT broadened.** Both new coordinators and both verification phases MUST state F7's boundary verbatim: HPAC/runtime-gate integration is **not** asked to solve arbitrary in-process compromise; no UID / username / process-ownership / stdio / Git identity / PCAE session identity / producer identity is trusted — only the verified HPAC provenance chain establishes human authentication, and only exact-object registry membership establishes gate-result provenance. A process-isolation / hardening chapter remains a legitimate, separate, **unscheduled** topic and is **not** a prerequisite for Gate-7 / Gate-8 wiring. |

---

## 24. Gate-7 defensive validation matrix (phase prompt §37)

Planned for the `.1R.13.2` implementation suite and independently
re-derived in `.1R.13.3`. Uses precise defensive terminology (validate
provenance, verify rejection, fail-closed, consumption boundary,
runtime-enforcement boundary, stale-state case, substitution case,
canonical re-resolution).

| # | Case | Expected outcome |
|---|---|---|
| 1 | legitimate registry-provenanced `Gate6Decision` with `decision="ALLOW"` required | proceeds to Gate-7 evaluation only |
| 2 | caller-created `Gate6Decision` (forged fields) | `is_gate6_decision` False → `gate7_untrusted_gate6_decision`; no `Gate7Result` |
| 3 | copied / `deepcopy` / field-reconstructed `Gate6Decision` | rejected (registry membership fails; `__reduce__` raises) |
| 4 | `Gate6Decision.decision == "DENY"` | `gate7_pb_decision_not_allow:DENY`; verify rejection; no progression |
| 5 | `Gate6Decision.decision == "HUMAN_REVIEW"` | `gate7_pb_decision_not_allow:HUMAN_REVIEW`; **HUMAN_REVIEW never becomes ALLOW** |
| 6 | `Gate6Decision.decision == "ALLOW"` under current posture | `Gate7Result(decision="DENY", matched_no_go_ids⊇{RE-NOGO-002,...})` — fail-closed on unavailable capability |
| 7 | invocation substitution (`Gate6Decision` for invocation A, identity B) | `gate7_invocation_binding_mismatch` |
| 8 | attempt-id substitution | `gate7_invocation_binding_mismatch` (attempt branch) |
| 9 | stale `Gate5Result.projection` (revoked/expired after Gate 5/6, before Gate 7) — stale-state case | `gate7_stale_validated_authority_projection`; canonical re-resolution rejects |
| 10 | `subject_scope_binding_digest` mismatch (permission-relevant field changed) | `gate7_authority_subject_scope_mismatch` |
| 11 | PB policy-version drift since Gate 6 | `gate7_pb_decision_stale_policy_version` |
| 12 | repository / HEAD / task / prompt / adapter-config drift | `gate7_request_currentness_drift:<fact>` |
| 13 | runtime execution unavailable (current posture) | `gate7_runtime_execution_unavailable` + `RE-NOGO-002` |
| 14 | unsupported / absent runtime target; not local-CLI-v1 representable | `gate7_runtime_target_ineligible` |
| 15 | runtime-enforcement internal exception | `gate7_internal_error_fail_closed`; no partial output |
| 16 | `Gate7Result` non-transferable (copy / serialize / reconstruct) | `__reduce__` raises; `is_gate7_result` False for any non-identity object |
| 17 | repeated Gate-7 run consumes nothing | no approval/proof/lifecycle/consumption write; fresh result each call |
| 18 | no Gate-8 call if Gate 7 fails | Gate-7 module imports/calls no Gate-8 symbol (AST) |
| 19 | no Gate-9 / Gate-10 effect | AST forbidden-import scan; 0 subprocess/network/adapter/consumption calls (runtime counters) |
| 20 | NON-REAL principal cannot drive a trusted positive Gate 7 in production | real `Gate6Decision` is `DENY` (POL-005); Gate-7 short-circuits; §12 `.1R.13` precedent |

---

## 25. Gate-8 defensive validation matrix (phase prompt §38)

Planned for `.1R.13.4`, re-derived in `.1R.13.5`.

| # | Case | Expected outcome |
|---|---|---|
| 1 | legitimate registry-provenanced `Gate7Result` with `decision="ALLOW"` required | proceeds to containment establishment only |
| 2 | caller-created `Gate7Result` | `is_gate7_result` False → `gate8_untrusted_gate7_result` |
| 3 | copied / reconstructed / serialized `Gate7Result` | rejected |
| 4 | `Gate7Result.decision == "DENY"` | `gate8_gate7_decision_not_allow`; hard stop |
| 5 | exact invocation binding (`invocation_id` / `attempt_id`) | mismatch → `gate8_invocation_binding_mismatch` |
| 6 | exact effect-plan binding (executable + argv) | substitution → `gate8_effect_plan_binding_mismatch` |
| 7 | command / shell string substitution — caller supplies a shell string | `gate8_caller_shell_string_rejected` (argv vector only; RDGO-001 §9/§11) |
| 8 | cwd substitution | `gate8_cwd_drift` |
| 9 | environment-allowlist substitution / widening | `gate8_environment_allowlist_drift` |
| 10 | runtime-target substitution since Gate 7 | `gate8_runtime_target_drift` |
| 11 | executable identity/hash ≠ descriptor pin (supply-chain) — substitution case | `gate8_executable_identity_mismatch` |
| 12 | descriptor/config drift — canonical re-resolution | `gate8_descriptor_config_drift` |
| 13 | Shell Gate classifier denies the resolved executable/argv (classifies as mutation/network/secret/destructive) | `gate8_shell_gate_category_denied`; fail-closed |
| 14 | Shell Gate classifier internal failure | fail-closed (`gate8_shell_gate_internal_error`) |
| 15 | network not deniable / credential access required | `gate8_network_not_deniable` / `gate8_credentials_required` |
| 16 | `Gate8Result` non-transferable | `__reduce__` raises; identity-only |
| 17 | repeated Gate-8 run consumes nothing | no `consumption.json`; no approval/proof write; fresh result |
| 18 | no Gate-9 consumption from the Gate-8 path | AST: no consumption-store symbol imported/called |
| 19 | no Gate-10 effect | AST forbidden-import (`subprocess`/`socket`/`spawn`/`exec`/`pty`/provider SDK); 0 process/network calls (runtime counters) |
| 20 | Gate 8 structurally unreachable in production today | real chain never yields a positive `Gate7Result`; §12.9 |

---

## 26. Implementation packaging decision (phase prompt §39 — frozen)

**Separate slices** — the recommended default, and correct here because
Gate 7 (independent whether-to-invoke decision) and Gate 8 (process
containment establishment) have **distinct trust boundaries** and distinct
failure surfaces, and the contracts define them as separate gates with
separate owners (RDGO-001 §8 vs §9, different owning components). Coupling
is **not** unavoidable: Gate 8 consumes only Gate 7's ephemeral output
object, exactly as Gate 7 consumes Gate 6's. Separate trust-boundary
verification is preferred.

```text
.1R.13.2  Gate-7 implementation
.1R.13.3  Gate-7 independent verification
.1R.13.4  Gate-8 implementation
.1R.13.5  Gate-8 independent verification
```

Not over-fragmented (Gate 7's sub-checks — provenance, PB-decision gate,
freshness, posture, currentness — are not independently meaningful gates).
Not over-bundled (Gate 7 and Gate 8 are different trust boundaries).

---

## 27. Canonical phase IDs / titles (phase prompt §40 — frozen)

Per this project's no-invent-beyond-need discipline, this numbering family
(`.1R.13.x` matches the established dotted-sub-phase convention, e.g.
`.1R.3.2.1`, `.1R.5.2.1`), and the constraint that `.1R.14` / `.1R.15`
(Gate 9 + its verification) are already frozen and **NOT renumbered**:

| Phase ID | Title | Scope | Authorization |
|---|---|---|---|
| `149O.20L.7O.3W.1R.2B.1R.1.1R.13.1` | Gate-7 Runtime Enforcement and Gate-8 Shell Gate Consumption Integration **Planning** | this document | **this phase** (human-authorized) |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.13.2` | **Gate-7 Runtime Enforcement Coordinator Integration Implementation** | new `src/pcae/core/runtime_dispatch_gate7.py` + §10 model + §22 V-13-1 scope-guard re-baseline/conversion + minimal wiring; the §24 test suite | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.13.3` | **Independent Verification of Gate-7 Runtime Enforcement Coordinator Integration** | independently re-derive §4, §6, §7, §10, §13, §24 against the `.1R.13.2` implementation — not trusted from its report/tests | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.13.4` | **Gate-8 Process Containment (Shell Gate) Coordinator Integration Implementation** | new `src/pcae/core/runtime_dispatch_gate8.py` + §12 model + §11.2 anti-substitution binding + the §25 test suite | separate explicit human authorization required |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.13.5` | **Independent Verification of Gate-8 Process Containment Coordinator Integration** | independently re-derive §5, §11, §12, §16, §25 against `.1R.13.4`; re-check the §16 Gate-8 → Gate-9 handoff contract | separate explicit human authorization required |

**Unchanged, still frozen, still BLOCKED, NOT renumbered:**

- `149O.20L.7O.3W.1R.2B.1R.1.1R.14` — Gate-9 Atomic Authority Consumption
  Coordinator Integration Implementation. BLOCKED until §17 criteria met.
- `149O.20L.7O.3W.1R.2B.1R.1.1R.15` — Independent Verification of Gate-9
  Atomic Authority Consumption Coordinator Integration.

The Gate-10 (adapter dispatch) chapter is **not** frozen with an ID here.

---

## 28. Anticipated production-file matrix (phase prompt §41)

Minimize production changes. For each phase, the anticipated surface (to be
confirmed and frozen in that phase's own task contract):

### 28.1 Gate 7 (`.1R.13.2`)

| File | Current role | Proposed change | Gate | Authority sensitivity | Test surface |
|---|---|---|---|---|---|
| `src/pcae/core/runtime_dispatch_gate7.py` **(new)** | — | Gate-7 coordinator: `run_gate7_runtime_enforcement`, `Gate7Result`, `is_gate7_result`, `_GATE7_RESULTS`; §10 model; fail-closed envelope | 7 | **Critical** | full §24 matrix |
| `src/pcae/core/runtime_enforcement_safety_authorization.py` | design-only no-go vocabulary | **None anticipated** (consumed read-only as constants). Modify only if `.1R.13.3` finds a concrete gap. | 7 | Low (constants) | regression: existing helper tests unchanged |
| `src/pcae/core/runtime_dispatch_permission.py` | Gate-6 coordinator + trusted builder | **None anticipated.** Gate 7 imports `is_gate6_decision` / `Gate6Decision` — read-only. If a shared trusted-builder call is needed, add a thin read-only accessor only. | 6→7 | High | regression: all `.1R.13` Gate-6 tests unchanged |
| `src/pcae/core/runtime_introspection.py` / `runtime_context.py` | observation-only posture | **None anticipated** (read-only consumption for `runtime_status_facts`). | 7 | Medium | regression |
| `tests/test_gate7_runtime_enforcement_coordinator_integration_..._1r13_2.py` **(new)** | — | §24 matrix | 7 | — | — |
| scope-guard tests from `.1R.10` / `.1R.11` | frozen-diff assertions | re-baseline or convert to phase-aware invariant tests (§22) | — | — | — |

### 28.2 Gate 8 (`.1R.13.4`)

| File | Current role | Proposed change | Gate | Authority sensitivity | Test surface |
|---|---|---|---|---|---|
| `src/pcae/core/runtime_dispatch_gate8.py` **(new)** | — | Gate-8 coordinator: `run_gate8_process_containment`, `Gate8Result`, `is_gate8_result`, `_GATE8_RESULTS`; §12 model; §11.2 anti-substitution binding; containment-evidence digest | 8 | **Critical** | full §25 matrix |
| `src/pcae/core/shell_gate.py` | read-only 88P command classifier | **None anticipated** (consumed read-only via `build_shell_gate` for the executable/argv category cross-check). Modify only if `.1R.13.5` finds a concrete gap. | 8 | Medium | regression: existing 88P classifier tests unchanged |
| `src/pcae/core/runtime_dispatch_gate7.py` | Gate-7 coordinator (from `.1R.13.2`) | **None** — Gate 8 imports `is_gate7_result` / `Gate7Result` read-only | 7→8 | High | regression |
| `src/pcae/core/runtime_registry.py` | runtime descriptor/config registry | **None anticipated** (read-only descriptor/executable resolution). | 8 | Medium | regression |
| `tests/test_gate8_process_containment_coordinator_integration_..._1r13_4.py` **(new)** | — | §25 matrix | 8 | — | — |

### 28.3 Explicitly NOT changed by any of `.1R.13.2`–`.1R.13.5`

`runtime_invocation_authority_consumption.py` (Gate-9 store — untouched
until `.1R.14`), `runtime_adapter.py` / `mock_runtime_adapter.py` (Gate 10),
`policy.py` / POL-005, `permission_broker_foundation.py`, all 9 normative
contracts, `runtime_dispatch_gate5.py`, `hpac_*`, schema packages,
version/build config, `pcae runtime inspect`.

---

## 29. Consumer inventory (phase prompt §42 — frozen expectation)

New/changed consumers introduced by `.1R.13.2`–`.1R.13.5`:

| Symbol | New consumer(s) | Any alternate path? |
|---|---|---|
| `Gate6Decision` / `is_gate6_decision` | `runtime_dispatch_gate7.run_gate7_runtime_enforcement` **only** | No — verified by consumer-inventory AST test |
| `Gate5Result` / `is_gate5_result` | already consumed by Gate 6; Gate 7 adds one more registry-check call site | No new authority path (re-trust + revalidate only) |
| future `Gate7Result` / `is_gate7_result` | `runtime_dispatch_gate8.run_gate8_process_containment` **only** | No |
| future `Gate8Result` / `is_gate8_result` | future `run_gate9_*` **only** (not built until `.1R.14`) | No |
| `runtime_enforcement_safety_authorization` constants | `runtime_dispatch_gate7` (read-only) | Existing Phase 89/104 readiness reporters keep their independent use; no conflict |
| `shell_gate.build_shell_gate` | `runtime_dispatch_gate8` (read-only) adds one call site alongside the existing `pcae shell-gate` CLI | No behavioral change to the classifier |

No unexpected alternate authority path. Each verification phase re-runs a
consumer-inventory scan.

---

## 30. Contract traceability (phase prompt §43)

| Planned element | RDGO-001 | PBRD-001 | RPAC / capability | Shell Gate / RE |
|---|---|---|---|---|
| Gate-7 four-item input | §8 items 1–4; §14 | §14 (RE projection); §4 (14 facts) | RPAC-REQ-042 (gate order) | — |
| Gate-7 independent evaluation | §8 "independently evaluates"; §14 "does not rubber-stamp" | §14 | — | RE-NOGO vocabulary (`runtime_enforcement_safety_authorization`) |
| Gate-7 DENY/HUMAN_REVIEW/ALLOW handling | §7, §8, §19 | §8, §9, §10 | — | — |
| Gate-7 single-attempt/expiring output | §8; §10 item 7; §15 | §10 (decisions expire) | — | — |
| Gate-7 no-consumption | §7 (PB), §8 (RE), §10 (consumption at 9) | §7 | — | — |
| Gate-7 posture check | §8 "unavailable target"; §19 | §11 | RPAC capability model; runtime `not_implemented` | `execution_available` flag → RE-NOGO-002 |
| Gate-8 containment establishment | §9 (all eight SHALL bullets); §1 row 8; §13 live column | §11 (process/fs/network/credential distinctions) | RPAC-REQ (executable identity) | `shell_gate` classifier (category cross-check) |
| Gate-8 no caller shell string | §9, §11 | §6 ("untrusted executable or shell command strings") | — | `shell_gate` "never executes" invariant |
| Gate-8 no effect | §9 ("No dispatch yet"), §11 (Gate 10 is first effect) | §11 | — | — |
| Gate-8 → Gate-9 handoff | §10 (eight items); §10 last ¶ (in-boundary revalidation) | §14 | — | — |
| Gate-9 unblocking criteria | §21 (no gate reorder), §14 mapping | §12 (POL-005 evolution preconditions 5–7) | — | — |
| Gate-10 untouched | §11, §20 | §13 | RPAC adapter contract | — |

No undocumented semantics: every planned element maps to a frozen
contract clause.

---

## 31. No normative contract modification (phase prompt §44)

This phase modifies **no** contract. No contradiction requiring a STOP was
found:

- The V-2 / V-3 / V-4 contract-alignment debts are **non-blocking** and do
  **not** create ambiguity in Gate-7 / Gate-8 sequencing (§20, §21). They
  remain candidates for a dedicated, separately-authorized
  contract-clarification phase.
- RDGO-001 §8 / §9 are internally consistent and sufficient to specify Gate
  7 and Gate 8 at the level this plan requires.
- PBRD-001 §14 cleanly defines the Gate-6 → Gate-7 handoff.

> **No contract conflict blocks `.1R.13.2`. If the `.1R.13.2` / `.1R.13.4`
> implementation review discovers a genuine contradiction, that phase SHALL
> STOP, record the exact conflict, and recommend a contract-clarification
> phase — it SHALL NOT silently reinterpret.**

---

## 32. Validation performed this phase (phase prompt §4, §47)

Planning/governance checks only (no full-suite evidence manufactured — no
`src/` or `tests/` change this phase):

| Check | Result |
|---|---|
| `git status --short` (start) | clean |
| `git status --branch --short` | `## main...origin/main` (no divergence) |
| `git log --oneline origin/main..HEAD` (start) | empty |
| `git rev-list --count origin/main..HEAD` (start) | `0` |
| `pcae health` | healthy; session continuity verified; git clean |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warning-only — pre-existing `tasks/DONE.md` omissions (O4 hygiene debt; not this phase) |
| `pcae push check` | `nothing_to_push`; phase-report trust/identity passed |
| `pcae runtime inspect` | `not_implemented / Observed / unavailable / observe`; PB `execution_unavailable`; governance posture `non-executing` — **unchanged** |
| `pcae notify status` | Telegram configured, enabled, ready |
| `pcae phase-report show --latest` | `.1R.13` — completed, report complete |

Confirmed: `.1R.13` is the latest completed phase; repository clean; no
active governed phase before this one started; `origin/main..HEAD = 0` at
start; runtime unchanged.

---

## 33. Explicit no-go conditions carried into `.1R.13.2`–`.1R.13.5`

Each implementation slice (`.1R.13.2`, `.1R.13.4`) SHALL STOP and request
explicit human direction if any of the following is encountered:

1. A genuine contract contradiction (§31).
2. A need to modify POL-005, any normative contract, `runtime inspect`,
   the adapter protocol, the Gate-9 store, or `runtime_dispatch_gate5.py`.
3. A need to import `subprocess` / `socket` / `spawn` / `exec*` / `pty` /
   a provider SDK / an HTTP client into the Gate-7 or Gate-8 module.
4. Any code path that would create a `consumption.json`, mutate an
   approval / proof / presentation / challenge / nonce, or register a real
   runtime adapter.
5. A discovered way for `HUMAN_REVIEW` or `DENY` to reach a positive
   `Gate7Result`.
6. A discovered production path to a positive `Gate7Result` / `Gate8Result`
   while `execution_capability` is `unavailable`.
7. Scope creep beyond the §28 file matrix without a task-contract amendment.

`.1R.14` (Gate 9) SHALL additionally STOP if, at its startup, any §17
unblocking criterion is unmet.

---

## 34. Summary of frozen decisions

| # | Decision |
|---|---|
| D1 | Gate 7 = single independent non-consuming "final whether-to-invoke" decision over the full bound request (§4.3). |
| D2 | Gate 8 = process-containment boundary: re-resolve drift, refuse caller shell strings, construct + attest one bounded launch environment; no dispatch, no consumption (§5.3). |
| D3 | Gate-6 → Gate-7 handoff = the PBRD-001 §14 four-item projection (Option C), assembled from a registry-provenanced `Gate6Decision` + re-resolved `Gate5Result` + current posture/preflight facts (§6). |
| D4 | `DENY` / `HUMAN_REVIEW` → Gate 7 unreachable/reject; only literal `"ALLOW"` permits Gate-7 evaluation; no anti-escalation path (§7). |
| D5 | Gate-7 owner = new `runtime_dispatch_gate7.py` coordinator; consumes (not reimplements) the RE no-go vocabulary (§8, §9, §19.1). |
| D6 | Gate-7 output = ephemeral, identity-only, non-serializable, registry-provenanced `Gate7Result` (`decision` ∈ {ALLOW, DENY}), not an execution token (§10.2). |
| D7 | Under the current posture Gate 7 **always rejects** (`RE-NOGO-002` + safety no-gos); no legitimate positive production Gate-7 success is possible today (§10.5, §10.6). |
| D8 | Gate-8 owner = new `runtime_dispatch_gate8.py` coordinator; consumes (not reimplements/replaces) the mature 88P `shell_gate.py` classifier (§12.1, §19.2). |
| D9 | Gate-8 output = ephemeral, identity-only, non-serializable, registry-provenanced `Gate8Result` (`containment_established` bool + `containment_evidence_digest`), not an execution token (§12.6). |
| D10 | Gate-7 → Gate-8 binding enforced by exact digest recompute + fresh executable-hash-vs-descriptor-pin; §11.2 anti-substitution matrix. |
| D11 | Gate-8 → Gate-9 handoff = §16: five exact-object-provenanced trusted objects + identity + inputs + fresh capability snapshot, in-process only, consumed atomically only at Gate 9 (§16). |
| D12 | Gate-9 unblocking criteria = §17 (all eight); `.1R.14` / `.1R.15` NOT renumbered. |
| D13 | Neither Gate 7 nor Gate 8 consumes anything; both are idempotently repeatable; both results are expiring and cache-invalid across any drift (§10.9, §12.10, §18). |
| D14 | Gate 10 boundary untouched; no production adapter-dispatch path created or named (§14). |
| D15 | V-2 / V-3 / V-4 — non-blocking, no Gate-7/Gate-8 impact, no STOP; carried to the recommended contract-clarification phase (§20, §21). |
| D16 | V-13-1 — `.1R.13.2` re-baselines or converts the two stale scope guards to phase-aware invariant tests and discloses every guard its source addition trips (§22). |
| D17 | O1–O4 / F2–F4 / F7 — all carried unchanged; F7 threat model **not** broadened (§23). |
| D18 | Packaging = four separate slices, each with its own independent verification (§26). |
| D19 | Frozen phase IDs `.1R.13.2` … `.1R.13.5` (§27); each needs separate explicit human authorization. |
| D20 | Anticipated production surface = two new files + read-only consumption of existing modules; minimize changes (§28). |

---

## 35. Final report

- **Phase ID / title:** `149O.20L.7O.3W.1R.2B.1R.1.1R.13.1` — Gate-7
  Runtime Enforcement and Gate-8 Shell Gate Consumption Integration
  Planning.
- **Status / completeness:** COMPLETE. Planning only. No production source
  changed; no contract changed; no test changed. Deliverable: this
  document + `PROJECT_STATUS.md` + `CHANGELOG.md` + lifecycle artifacts.
- **Files changed:** `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_1_GATE_7_RUNTIME_ENFORCEMENT_AND_GATE_8_SHELL_GATE_CONSUMPTION_INTEGRATION_PLANNING.md`
  (new), `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`,
  `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`.
- **Contracts / source inspected:** RDGO-001 v3.0, PBRD-001 v2.0, RPAC-001
  v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBPA-001 v1.0, PB
  Production Consumption Contract, POL-005 (source); `runtime_dispatch_gate5.py`,
  `runtime_dispatch_permission.py`, `runtime_enforcement_safety_authorization.py`,
  `enforcement_readiness.py`, `enforcement_audit.py` / `enforcement_approval.py`
  / `enforcement_rollback.py`, `shell_gate.py` (core + command),
  `runtime_adapter.py`, `mock_runtime_adapter.py`,
  `runtime_invocation_authority_consumption.py`, `runtime_registry.py` /
  `runtime_introspection.py` / `runtime_context.py`; `.1R.9`–`.1R.13`
  phase documents.
- **Current runtime state:** `not_implemented / Observed / observe /
  unavailable`; PB `execution_unavailable`; governance posture
  `non-executing`. **Unchanged by this phase.**
- **Exact Gate-7 contract responsibility:** the single, independent,
  non-consuming "final whether-to-invoke" decision over the complete bound
  `runtime_dispatch` request — re-evaluates authority freshness, PB
  evidence, target/capability/posture eligibility, and repository/task/
  prompt/config currentness; emits one ephemeral single-attempt expiring
  result that authorizes nothing by itself (RDGO-001 §8, §14).
- **Exact Gate-8 contract responsibility:** the process-containment
  boundary — given a positive Gate-7 decision, re-resolve descriptor/
  executable/repository/policy drift, refuse any caller shell string, and
  construct + attest one exact bounded launch environment (executable
  identity, argv, cwd, env allowlist, child-process/resource/time limits,
  supervision, network denied, no credentials), binding that containment
  evidence to the invocation; no dispatch, no consumption (RDGO-001 §9).
- **Gate-6 → Gate-7 handoff:** PBRD-001 §14 four-item RE projection
  (Option C) — registry-provenanced `Gate6Decision` + re-resolved
  `Gate5Result` projection + current target/status/preflight facts;
  references/digests, not wholesale duplication; Gate 7 evaluates
  independently.
- **DENY / HUMAN_REVIEW / ALLOW Gate-7 semantics:** `DENY` → reject, no
  `Gate7Result`; `HUMAN_REVIEW` → reject, never becomes ALLOW; `ALLOW` →
  Gate 7 proceeds to its own evaluation only. Anti-escalation invariant
  frozen (§7.2).
- **Gate-7 owner:** new `src/pcae/core/runtime_dispatch_gate7.py`
  coordinator (`run_gate7_runtime_enforcement`); consumes the existing
  design-only RE no-go vocabulary, reimplements no verified logic (there is
  no verified RE decision logic today).
- **Runtime Enforcement consumption model:** no production RE engine exists;
  only design-only constants (`runtime_enforcement_safety_authorization.py`,
  12 auth flags / 5 safety flags / `RE-NOGO-001..011`), non-executing. The
  new coordinator IS the engine, built to compute a no-go snapshot from the
  current posture (all auth flags `False`, all safety flags `True` ⇒
  `RE-NOGO-001/002/010/011` matched ⇒ always DENY today).
- **Gate7Result model / provenance:** `_seal`-guarded construction;
  `is_gate7_result` = exact-object membership in `_GATE7_RESULTS`;
  `__reduce__` raises; identity-only `==`/`hash`; `__init_subclass__`
  raises; carries decision/no-go-ids/reason-ids/digests/expiry; not an
  execution token. `shape != provenance`.
- **Gate-7 current-runtime behavior:** always rejects — real `Gate6Decision`
  is `DENY` (POL-005) so Gate 7 short-circuits; even given a hypothetical
  `ALLOW`, ≥4 blocking `RE-NOGO-*` ids match. No legitimate positive
  production Gate-7 success is possible today. Mechanics still fully
  testable (negative path is the production path; positive branch via a
  clearly-labelled test boundary, no production bypass).
- **Gate-7 failure / idempotency:** fail-closed for every condition in
  §10.8 (no partial output); consumes nothing; idempotently repeatable;
  positive result single-attempt, expiring, cache-invalid across any drift.
- **Gate-7 → Gate-8 handoff:** trusted `Gate7Result` + `decision=="ALLOW"`
  + identity/inputs + re-resolved `Gate5Result` + a coordinator-assembled
  canonical effect plan (descriptor-pinned executable, argv, cwd, env
  allowlist — never a caller string); §11.2 anti-substitution matrix.
- **Gate-8 owner:** new `src/pcae/core/runtime_dispatch_gate8.py`
  coordinator (`run_gate8_process_containment`); consumes the mature 88P
  `shell_gate.py` classifier for the executable/argv category cross-check,
  does not replace or extend it.
- **Shell Gate consumption model:** `shell_gate.py` is a read-only 24-
  category / 26-decision command classifier that never executes classified
  command text (only `subprocess.run` call is a governed `pcae doctor
  test-run` lock check). The new coordinator adds one read-only
  `build_shell_gate` call site and owns containment establishment + drift
  re-resolution + `Gate8Result`.
- **Gate8Result model / provenance:** `_seal`-guarded; `is_gate8_result`
  = exact-object membership in `_GATE8_RESULTS`; `__reduce__` raises;
  identity-only; carries `containment_established` +
  `containment_evidence_digest` + digests + expiry; not an execution
  token. `shape != provenance`.
- **Gate-8 no-effect semantics:** validation + containment establishment
  only — no subprocess, provider call, adapter invocation, shell
  execution, repository mutation, network call, or credential operation.
  AST forbidden-import guard planned. Gate 10 remains first effect.
- **Gate-8 → Gate-9 handoff:** §16 — five exact-object-provenanced trusted
  objects (`Gate8Result`, `Gate7Result`, `Gate6Decision`, `Gate5Result`
  lineage) + `RuntimeDispatchIdentity` + `RuntimeDispatchRequestConstructionInput`
  + fresh capability snapshot; in-process assembly only, not serialized,
  not persisted before Gate 9's atomic write; consumed atomically only at
  Gate 9; six frozen handoff invariants (§16.2).
- **Gate-9 unblocking criteria:** §17 — (1) Gate-7 impl complete
  (`.1R.13.2`), (2) Gate-7 independently verified (`.1R.13.3`), (3) Gate-8
  impl complete (`.1R.13.4`), (4) Gate-8 independently verified
  (`.1R.13.5`), (5) §16 handoff contract frozen, (6) no unresolved
  blocking findings, (7) runtime still non-executing unless separately
  authorized, (8) §16 independently reviewed. `.1R.14` also retains its
  `.1R.9` §16.2 precondition (satisfied by 1–4). `.1R.15` stays frozen
  behind `.1R.14`.
- **Runtime capability model:** `Observed` = observe-only, runtime
  `not_implemented`; `Maximum Capability: observe` = no invoke/dispatch/
  mutate capability registrable (0 plugins); `Execution Availability:
  unavailable` = no code path creates an external process. Runtime
  Enforcement can never return "eligible" under this state (`RE-NOGO-002`).
  The **Gate-7 coordinator** owns the capability check — not PB, not Gate
  8. `PB permission != runtime capability`.
- **Gate-10 boundary:** RDGO-001 §11 first external effect; **no production
  adapter dispatch exists** (`runtime_adapter.py` abstract +
  `mock_runtime_adapter.py` simulation-only, no `subprocess`/`spawn`/`exec`/
  `pty`). Not created, named, or modified by this phase. A future Gate-10
  module will consume a `Gate9Result`, never a `Gate7Result`/`Gate8Result`.
- **V-2 / V-3 disposition:** NON-BLOCKING, carried unchanged; no
  Gate-7/Gate-8 impact, no amplification; Gate 7/8 import nothing from
  `hpac_lifecycle` / `hpac_verifier` and depend on no sequence-3 wording;
  no sequencing ambiguity; no STOP. Candidates for the contract-
  clarification phase.
- **V-4 disposition:** NON-BLOCKING contract-alignment debt, carried
  unchanged; Gate 7/8 consume only the trusted upstream objects
  (`Gate5Result` / `Gate6Decision`), never the 3-field or 7-field
  `human_authority_binding`; digest-collapse verified lossless (`.1R.13`
  §10); planned import/reference-absence test; PBRD-001 not rewritten; no
  STOP. Candidate for the contract-clarification phase.
- **V-13-1 disposition:** `.1R.13.2` re-baselines the two stale
  point-in-time scope guards (`test_..._1r10` /
  `test_..._1r11`) to the `.1R.13.1` completion SHA **or** converts them to
  phase-aware invariant (subset) tests, and discloses in its canonical
  report every point-in-time guard its source addition trips with
  git-worktree A/B attribution. Prefer invariant tests. `.1R.13.1` performs
  no test maintenance.
- **O1–O4 / F2–F4 / F7 disposition:** all carried unchanged, none silently
  closed. O1 (unreachable positive path — inherent to NON-REAL staging);
  O2 (store trust is path+integrity — coordinators must not assume writer
  provenance); O3/F4 (name accuracy — new tests must be accurately named);
  O4 (`tasks/DONE.md` hygiene debt — untouched, recommend a hygiene pass);
  F2 (HPAC-REQ-054 Step 4 — already repaired/verified, prerequisite
  satisfied); F3 (label debt — deferred); **F7 (registries resist
  data-forgery, not arbitrary same-process code execution — threat model
  NOT broadened; process-isolation is a separate, unscheduled, non-
  prerequisite topic; both new coordinators and both verification phases
  must state F7's boundary verbatim).**
- **Gate-7 validation matrix:** §24 — 20 cases (provenance, DENY/
  HUMAN_REVIEW rejection, ALLOW-only progression, invocation/attempt
  substitution, stale/revoked projection, subject-scope mismatch, PB
  policy drift, request currentness drift, execution-unavailable fail-
  closed, ineligible target, internal-error fail-closed, non-transferable
  result, no-consumption, no Gate-8 call on failure, no Gate-9/10 effect,
  NON-REAL cannot drive production positive).
- **Gate-8 validation matrix:** §25 — 20 cases (provenance, non-ALLOW
  `Gate7Result` hard stop, exact invocation/effect-plan binding, caller
  shell string rejected, cwd/env/target/executable-hash/descriptor
  substitution, Shell Gate category deny + internal-failure fail-closed,
  network-not-deniable / credentials-required, non-transferable result,
  no-consumption, no Gate-9 consumption, no Gate-10 effect, structurally
  unreachable in production today).
- **Selected packaging:** four separate slices, each followed by an
  independent verification phase (§26).
- **Exact Gate-7 implementation phase ID / title:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.13.2` — Gate-7 Runtime Enforcement
  Coordinator Integration Implementation. Requires separate explicit human
  authorization.
- **Gate-7 verification phase ID / title:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.13.3` — Independent Verification of Gate-7
  Runtime Enforcement Coordinator Integration. Requires separate explicit
  human authorization.
- **Gate-8 implementation phase ID / title:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.13.4` — Gate-8 Process Containment (Shell
  Gate) Coordinator Integration Implementation. Requires separate explicit
  human authorization.
- **Gate-8 verification phase ID / title:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.13.5` — Independent Verification of Gate-8
  Process Containment Coordinator Integration. Requires separate explicit
  human authorization.
- **Does `.1R.14` become unblocked after those close?** Yes — completing
  `.1R.13.2`–`.1R.13.5` with VERIFIED outcomes and no unresolved blocking
  findings satisfies §17 criteria 1–6 and the `.1R.9` §16.2 path-(a)
  precondition. `.1R.14` would then still require (7) an unchanged
  non-executing runtime posture (or a separate explicit authorization) and
  (8) confirmation that §16 was independently reviewed, **and its own
  separate explicit human authorization to start.** `.1R.15` remains frozen
  behind `.1R.14`.
- **Any contract blocker:** none. No contract contradiction requiring a
  STOP was found (§31). V-2 / V-3 / V-4 are non-blocking and do not create
  Gate-7/Gate-8 sequencing ambiguity.
- **`.3` governance incident:** the `.3` delegated finalization / commit /
  push remains **UNAUTHORIZED**; history retained; creates no precedent.
  Governed PCAE lifecycle only; only the primary human-authorized operator
  holds `.1R.13.1` lifecycle authority.
- **Commits:** (recorded at finalization — see `PROJECT_STATUS.md` current-
  phase entry and `.pcae/phase-completion-metadata.json`).
- **Pushed status:** (recorded at finalization).
- **origin/main..HEAD:** `0` at phase start; `0` after finalization + push.

---

## 36. Stop condition

Only `149O.20L.7O.3W.1R.2B.1R.1.1R.13.1` is completed by this phase. Gate 7
is **not** implemented. Gate 8 is **not** implemented. `.1R.14` is **not**
begun. Gate 9 is **not** implemented. Gate 10 is **not** implemented.
Execution is **not** enabled. Runtime remains
`not_implemented / Observed / observe / unavailable`. POL-005 unchanged.
Real execution UNAVAILABLE.
