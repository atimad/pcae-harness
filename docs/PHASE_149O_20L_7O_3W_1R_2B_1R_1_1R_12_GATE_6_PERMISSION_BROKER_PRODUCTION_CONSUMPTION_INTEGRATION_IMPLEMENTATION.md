# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.12 — Gate-6 Permission Broker Production Consumption Integration Implementation

Status: **IMPLEMENTED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

Implements only the Gate-6 production-consumption slice frozen by `.1R.9`
§16.1 slice 2 / §16.2 and carried forward by `.1R.11`. No Gate-7, no
Gate-8, no Gate-9 atomic consumption, no Gate-10, no runtime execution
enabled. No Permission Broker policy, evaluator, or POL-005 change. No
normative contract modified. Runtime remains
`not_implemented / Observed / observe / unavailable`.

- **Phase-entry SHA:** `a26b9fe25c0830eaa1d2217edc6fe66c5718784a`
  (`Phase …1R.12: record governed task transition from post-1R.11 idle`).
- **Governing plan:** `.1R.9` — Gate-5/Gate-9 Production Authority
  Coordinator Integration Planning (§16.1 slice 2, §16.2, §22, §25 matrix,
  §23 POL-005, §26 traceability, §27 matrix rows 17–20).
- **Immediately preceding independent verification:** `.1R.11` — Gate-5
  approval-validation coordinator integration **CLOSED** (with non-blocking
  findings V-1/V-2/V-3).

---

## 1. `.1R.9` Gate-6 mapping

`.1R.9` §16.1 slice 2 (verbatim): *"Gate-6 Permission Broker production
consumption — wire a real `runtime_dispatch` `PermissionBrokerRequest`
carrying the Gate-5 validated projection (PBRD-001 §7 `human_authority_binding`,
§14) through the current PB evaluator; preserve `DENY > HUMAN_REVIEW >
ALLOW`; POL-005 still DENYs `simulation_only=False`. No PB policy/evaluator
change; no POL-005 change."*

`.1R.9` §25 production-file matrix, slice `.1R.12` rows:

| File | Frozen proposed change |
|---|---|
| `runtime_dispatch_permission.py` | *"add/adjust the production consumer that feeds a Gate-5 projection + `authority_current_time` through the existing builder for a real (`simulation_only=False`) `runtime_dispatch` request; **no change to the 14-fact shape or B7 reread**"* |
| `permission_broker_foundation.py` | **None** (POL-005 & evaluator untouched); read-only consumption |
| `project_human_authority_binding` | **None** (already the correct single consumer, PBRD-001 §7) |
| `runtime_introspection.py` | **None** — no capability elevation |

This phase changed **exactly one production file** — `runtime_dispatch_permission.py`
— strictly within that frozen envelope.

---

## 2. Gate-6 owner (frozen)

`runtime_dispatch_permission.run_gate6_permission_broker` is the single
owner of "Gate 6 ran" for `runtime_dispatch`. It owns:

- Gate-5 result provenance acceptance (`is_gate5_result`);
- exact-invocation binding of the referenced projection;
- `PermissionBrokerRequest` construction (delegated to the already-verified
  `.1R.7` trusted builder — never a caller-supplied request);
- the human-authority binding (delegated, unchanged, to
  `project_human_authority_binding`);
- Permission Broker evaluator invocation (the **unmodified**
  `PermissionBroker().evaluate`);
- the normalized, ephemeral `Gate6Decision` envelope.

It does **not** own — and does not duplicate — any policy semantics: DENY /
HUMAN_REVIEW / ALLOW rules, POL registry logic, decision precedence, and
reason-chain composition all stay in `permission_broker_foundation.py`
(§11). An AST test asserts the Gate-6 code calls none of `_compose`,
`evaluate_all`, `PolicyResult`, `PolicyRegistry`, `ExecutionDisabledRule`,
`MissingHumanApprovalRule`, `ReasonChainLink`, `_decision`,
`_sanitize_result`, and constructs no `PermissionBrokerRequest` directly.

There is exactly **one** `.evaluate(` call site in the module (test-asserted).

---

## 3. `Gate5Result` consumption model

`run_gate6_permission_broker` accepts `gate5_result` **only** if
`runtime_dispatch_gate5.is_gate5_result(gate5_result)` is true — i.e. the
exact identity object a prior successful `run_gate5` returned and inserted
into the module-local `_GATE5_RESULTS` set. `is_gate5_result` is
`isinstance` **and** exact-object set membership; it is never
type/shape/field/equality based.

Rejected, each returning `(None, ("gate6_untrusted_gate5_result",))` and
creating no `Gate6Decision`:

- a caller-constructed `Gate5Result` (its `__init__` `_seal` guard blocks
  the normal path; an `object.__new__` forgery has no registry membership);
- a field-equivalent reconstruction (every slot populated by hand);
- a copy / `deepcopy` (both raise `TypeError` via `__reduce__` before they
  can even be attempted; a manual rebuild is not a member);
- a serialized clone (`pickle.dumps` raises `TypeError`);
- a bare `validated=true` object / a duck-typed object exposing
  `.projection` / `.invocation_id`;
- `None`.

**Gate 6 does not recreate Gate-5 validation.** It never calls
`validate_approval`, `reverify_authenticated_principal`, or the HPAC
verifier. It consumes the already-validated authority the Gate-5 result
references and, at its own point of use, re-checks that authority is still
trusted (§4). This is the exact verified Gate-5 consumption mechanism
(`is_gate5_result` + point-of-use projection re-resolution), not a
field-equivalence check.

`Gate5Result` is not a bearer token: possession is insufficient. Even a
genuine `Gate5Result` yields no PB request unless its referenced projection
is *still* a registry-provenanced `ValidatedAuthorityProjection` whose
`_content_binding_digest` recomputes and whose `subject_scope_binding_digest`
matches the exact `identity` + `inputs` at Gate-6 time (§4).

---

## 4. `PermissionBrokerRequest` construction — authority derives from trusted state only

Conceptual flow (RDGO-001 §1, §7; PBRD-001 §7):

```text
canonical invocation (identity + inputs, trusted-caller-resolved)
        │
        ▼
Gate-5 validated authority  (gate5_result.projection, registry-provenanced)
        │   is_gate5_result(gate5_result)               ← Gate-6 step 1
        │   gate5_result.invocation_id == identity.invocation_id   ← step 2
        ▼
trusted human_authority_binding
        │   build_runtime_dispatch_permission_broker_request(...)  ← step 3
        │     → project_human_authority_binding(projection, identity, inputs, current_time):
        │         is_trusted_validated_authority_projection(projection)      (B1 predicate)
        │         revalidate_validated_authority_projection(projection, current_time)  (freshness)
        │         projection.subject_scope_binding_digest == digest(identity, inputs)  (exact bind)
        │     → identity._identity_tracker.revalidate(identity)   (B7 durable reread)
        ▼
PermissionBrokerRequest   (frozen; approval_present set ONLY by the above)
        │
        ▼
PermissionBroker().evaluate(request)                    ← step 4 (unmodified evaluator)
        ▼
Gate6Decision (ephemeral, non-transferable)             ← step 5
```

Gate 6 constructs the request **exclusively** through
`build_runtime_dispatch_permission_broker_request`. It never accepts a
caller-supplied `PermissionBrokerRequest`. A caller therefore cannot
supply a complete request containing `human_authority_binding` /
`approval_present=true` and have it trusted: `approval_present` is not a
parameter of the trusted builder (test-asserted), and
`project_human_authority_binding` reads *only* a registry-provenanced
`ValidatedAuthorityProjection` — never raw prose, a boolean, a public
digest, or a caller object (verified `.1R.7` / `.1R.8` B1).

A construction failure — untrusted projection, stale projection
(`revalidate` false), `subject_scope_binding_digest` mismatch, forged
identity seal, B7 registry drift, tampered `idempotency_key` — is caught
and returned as `(None, ("gate6_request_construction_failed:<reason>",))`.
Fail-closed, deterministic, no `Gate6Decision`, no partial state.

### Exact invocation binding (§16 of the phase prompt)

Two independent checks reject cross-invocation reuse:

1. `gate5_result.invocation_id != identity.invocation_id` →
   `("gate6_invocation_binding_mismatch",)` (the precise invocation-id
   swap).
2. inside the builder, `projection.subject_scope_binding_digest` is
   recomputed from `identity.invocation_id` + `inputs.runtime_target_id` +
   `inputs.prompt_hash` + `inputs.repository_identity` + `inputs.task_id` +
   the approval scope + adapter binding; any changed target / subject /
   operation / prompt / scope / adapter / mode-relevant field →
   `validated_authority_subject_scope_mismatch` → construction failure.

No cross-invocation reuse; no changed permission-relevant field accepted.

---

## 5. `human_authority_binding` implementation

Unchanged from `.1R.7`. `project_human_authority_binding` builds the
`RuntimeDispatchHumanAuthorityBinding` from the trusted projection:

```text
approval_id                 = projection.approval_id
approval_record_digest      = projection.record_digest
validation_evidence_digest  = projection.evidence_digest()   (recomputed)
```

and returns `approval_present=True` only on that path; `validated_authority
is None` or any failed check yields the empty-reference binding and
`approval_present=False`. PBRD-001 §7's substantive property — *"Only
successful RIHAC-001 v2.0 validation may cause the trusted request builder
to set `approval_present=true`; … not itself authority and is not
caller-settable"* — is preserved exactly.

**Finding V-4 (non-blocking contract-alignment debt), see §12.** The
`RuntimeDispatchHumanAuthorityBinding` shape frozen by `.1R.7` (3 fields:
`approval_id`, `approval_record_digest`, `validation_evidence_digest`)
differs from the literal 7-field enumeration in PBRD-001 v2.0 §4 fact 14
(`approval_id`, `approval_digest`, `authority_projection_id`,
`authority_projection_digest`, `authority_contract_version` const
`RIHAC-001/2.0`, `proof_validation_digest`, `request_binding_digest`).
`.1R.9` §25 explicitly froze this slice as *"no change to the 14-fact
shape"*, so this phase carries the `.1R.7` shape forward verbatim and does
**not** reshape the binding or touch the contract. The divergence is
pre-existing, does not affect Gate-6 correctness (§12), and is recorded for
a dedicated contract-clarification phase or `.1R.13`.

---

## 6. PB evaluator invocation + `DENY > HUMAN_REVIEW > ALLOW` precedence

Gate 6 calls `PermissionBroker().evaluate(request)` (or a caller-supplied
`PermissionBroker`, exact-type-checked). The evaluator is **byte-unchanged**
(`git diff a26b9fe2 HEAD -- src/pcae/core/permission_broker_foundation.py`
is empty). Precedence is owned by `permission_broker_foundation._compose`
(`DENY > HUMAN_REVIEW > ALLOW`, fail-closed on empty results) and is not
re-implemented, parameterised, or influenced by Gate 6. Gate 6 introduces
no caller-controlled precedence.

For a real `runtime_dispatch` request (`simulation_only=False`):

| Upstream state | Applicable rules that fire | Composed decision |
|---|---|---|
| any | POL-005 (`ExecutionDisabledRule`) → DENY / NG-025 | **DENY** |
| no valid Gate-5 authority | POL-004 would give HUMAN_REVIEW + POL-005 DENY | **DENY** (precedence) |

For `simulation_only=True` with no valid authority: POL-004 →
**HUMAN_REVIEW** (not collapsed to DENY or ALLOW). ALLOW is returned only
when no stronger rule triggers.

Because the deterministic HPAC mechanism is permanently NON-REAL
(`.1R.9` §21, `.1R.11` §9), `run_gate5` never returns a `Gate5Result` on
any obtainable path, so a real positive Gate-6 evaluation (steps 3–5 with
`approval_present=True`) **cannot be constructed without real FIDO2/UI**.
This phase does not manufacture one (`.1R.9` §41, phase prompt §30). The
POL-005 / precedence / HUMAN_REVIEW behaviour above is verified directly
against the `.1R.7` builder and the unmodified evaluator, clearly separated
from Gate-6 production-authority eligibility.

---

## 7. POL-005 preservation

POL-005 (`ExecutionDisabledRule`, `policy_id = "POL-005"`) is **not
modified** (byte-identical, test-asserted). The new Gate-6 path continues
to reject every `simulation_only=False` request:
`decision == "DENY"`, `"POL-005" in causing_policy_ids`, `"NG-025" in
matched_no_go_ids`, `decision_reason == "execution_boundary_unavailable"`.

Verified human authority does **not** override POL-005:
`ExecutionDisabledRule.evaluate()` ignores `approval_present` entirely — a
request with `approval_present=True, simulation_only=False` still triggers
DENY / NG-025 (test `test_pol005_denies_even_when_approval_present_would_be_true`).
No Gate-5-validated-authority special-casing exists anywhere in the Gate-6
path.

---

## 8. Request immutability / snapshot / TOCTOU

`PermissionBrokerRequest`, `RuntimeDispatchRequestFacts`,
`RuntimeDispatchHumanAuthorityBinding`, `RuntimeDispatchLifecycleContext`,
`RuntimeDispatchAdapterDescriptorBinding`, `RuntimeDispatchFilesystemScopeRef`
are all `@dataclass(frozen=True)`. `build_runtime_dispatch_permission_broker_request`
returns a fresh frozen request; `run_gate6_permission_broker` passes it
**straight** to `evaluator.evaluate(request)` in the same call, with no
mutation window and no separate "construct now, evaluate later" gap at the
Gate-6 layer. The projection freshness re-check
(`revalidate_validated_authority_projection`) and the B7 durable
dispatch-identity reread both occur *inside* the builder, immediately
before the frozen request is produced, so construction + evaluation are
atomic at this layer. No second serialization mechanism is introduced
(that is Gate-9's concern, out of chapter). `Gate6Decision` holds a
reference to the frozen `PermissionBrokerDecision`; it is itself immutable
(`__slots__`, identity `__eq__`/`__hash__`, no setters).

---

## 9. `Gate6Decision` — ephemeral, non-transferable output

Same discipline as `Gate5Result` / `ValidatedAuthorityProjection` /
`AuthenticatedHumanPrincipal`:

- **not caller-constructable** — `_seal` guard in `__init__`; the real
  boundary is `is_gate6_decision`, which checks exact-object membership in
  the module-local `_GATE6_DECISIONS` set, populated only by
  `run_gate6_permission_broker`'s success return;
- **not subclassable** — `__init_subclass__` raises;
- **not serializable** — `__reduce__` raises (so `pickle.dumps` /
  `copy.deepcopy` raise `TypeError`);
- **identity-only** `==` / `hash` — a forgery / reconstruction is a
  different object and never a registry member;
- **not an execution token** — it wraps the evaluator's
  `PermissionBrokerDecision`, whose `implementation_status` stays
  `execution_unavailable`. An ALLOW means "PB policy would allow this if
  execution existed", never runtime capability, Runtime Enforcement
  approval, process containment, or dispatch permission (PBRD-001 §10,
  §11). A later gate consumes it only through its own coordinator path,
  re-resolving the authority freshly.

Normalized read-only fields: `decision`, `decision_reason`,
`causing_policy_ids`, `matched_no_go_ids`, `requires_human`,
`approval_present`, `simulation_only`, `invocation_id`, `attempt_id`,
`request_id`, `evaluated_at`, and `pb_decision` (the wrapped result).

---

## 10. No-Gate-7 / No-Gate-8 / No-Gate-9 / No-Gate-10 proof

- **Gate 7 (Runtime Enforcement):** not called. The module imports nothing
  from `backend_invocations`; no `RuntimeEnforcement*` reference in code
  (AST import scan test). No Gate-7 phase ID invented.
- **Gate 8 (Shell Gate):** not called. No `shell_gate` import; no
  subprocess. No Gate-8 phase ID invented.
- **Gate 9 (atomic consumption):** not called. No
  `runtime_invocation_authority_consumption` / `runtime_dispatch_gate9`
  import. `proof consumption = 0`, `approval consumption = 0`,
  `consumption records = 0`; no `consumption.json` created anywhere by any
  Gate-6 path (test `test_no_consumption_records_created_anywhere`).
- **Gate 10:** no runtime dispatch, adapter invocation, subprocess,
  provider call, external network, credential, or hardware access. AST
  forbidden-import scan (`subprocess`, `socket`, `requests`, `httpx`,
  `urllib`, `http`, `fido2`, `webauthn`, `ctap`, `smartcard`, `usb`,
  `serial`, `ssl`, `asyncio`, `multiprocessing`, `ctypes`) passes.

Expected boundary: `PB decision produced → STOP at current chapter
boundary`. No capability activation.

---

## 11. Runtime boundary

`runtime_introspection.py` byte-unchanged:
`CURRENT_RUNTIME_STATE == "Observed"`,
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`,
`EXECUTION_AVAILABILITY == "unavailable"` — asserted still true after
Gate-6 rejections run. `pcae runtime inspect`: `not_implemented / Observed
/ observe / unavailable`, registry empty, PB status
`execution_unavailable`, posture `non-executing`. A PB ALLOW would not
change any of this (RPAC-001 execution-availability is independent of PB
ALLOW; `.1R.9` §24).

**Runtime zero-effect proof (phase prompt §42):**

```text
Runtime Enforcement calls   = 0
Shell Gate calls            = 0
runtime subprocess calls    = 0
provider / network calls    = 0
credential operations       = 0
hardware operations         = 0
Gate-9 consumption          = 0
Gate-10 effects             = 0
PB evaluator calls          = exactly 1 per successful run_gate6 invocation
                              (Gate-6 internal policy evaluation, NOT runtime execution)
```

The only subprocesses used by this phase's work were read-only `git`
history/diff inspection and the local `pytest` runner.

---

## 12. V-2 / V-3 contract-alignment review (phase prompt §25, §44)

`.1R.11` recorded:

- **V-2** — RDGO-001 §4/§6's literal *"Gate 5 … creates … sequence-3 over
  the completed approval digest"* is not literally satisfied; the
  `PROOF_VERIFIED_AND_BOUND` event is created by the verifier's
  HPAC-REQ-054 step 10 at Gate-3 / approval-creation time over the
  `approval_subject_digest`, and Gate 5 **confirms** it.
- **V-3** — the completed RIASC `record_digest` is not literally bound into
  or checked against the sequence-3 event (subsumed by V-2).

### Do V-2 / V-3 affect Gate-6 correctness? — **NO.**

1. **PBRD-001 `human_authority_binding` does not depend on the disputed
   sequence-3 wording.** Its inputs are (a) the immutable approval
   reference (`approval_id`, `record_digest`) and (b) the RIHAC-001 v2.0
   validated-authority projection reference/digest. Both are produced by
   `validate_approval` — step 4 recomputes and checks `record_digest`
   against the trusted projection, step 12 builds the projection and
   registers it. Neither reads the sequence-3 event. `project_human_authority_binding`
   reads only the projection.
2. **The Gate-6 path never touches HPAC lifecycle sequence-3.** `run_gate6_permission_broker`
   calls `is_gate5_result` (registry membership), reads `gate5_result.projection`,
   and delegates to `build_runtime_dispatch_permission_broker_request`.
   It does not call `resolve_gate5_binding_event`, `hpac_lifecycle`, or any
   sequence-3 accessor.
3. **The verified implementation remains semantically safe.** A tampered
   approval record fails `validate_approval` step 4 (`record_digest_mismatch`)
   before any projection exists; a cross-binding proof fails the verifier's
   §40 genesis-binding compare before any projection exists. Gate 6
   consumes only the post-step-12 projection, so V-2/V-3 cannot admit a
   mis-bound authority into the PB request.
4. **The full NON-REAL hard stop is upstream of Gate 6.** `run_gate5`
   cannot emit a `Gate5Result` at all today, so no production Gate-6
   evaluation is even reachable.

### Is a dedicated contract-clarification phase required before / after `.1R.13`? 

Not a prerequisite for `.1R.12` or `.1R.13`. Recommended (not blocking):
reconcile RDGO-001 §4/§6 with the `.1R.5`-wired, `.1R.5.2.1`-verified
step-10 behaviour, **and** reconcile PBRD-001 §4 fact 14's 7-field
`human_authority_binding` enumeration with the `.1R.7`-frozen 3-field
`RuntimeDispatchHumanAuthorityBinding` shape (finding **V-4**, §5), in a
dedicated contract-review/clarification task. Do not silently modify any
contract.

### Disposition (phase prompt §44)

**V-2 / V-3 — remain non-blocking; no Gate-6 impact.** Carried forward
explicitly. **V-4 (new) — non-blocking contract-to-implementation
alignment debt; no Gate-6 impact** (PBRD-001 §7's substantive
non-caller-settable / RIHAC-validation-only property is preserved by the
3-field binding). Recorded for the same contract-review surface as V-2/V-3.

If the mismatch ever becomes **blocking** for Gate 6 (it is not): STOP and
recommend contract clarification before implementation continues. It is
not blocking — no inter-contract contradiction, and every substantive
trust property PBRD-001 §7 / RDGO-001 §7 requires holds in the
implementation.

---

## 13. V-1 / O1–O4 / F2–F4 / F7 dispositions

| Finding | Disposition for `.1R.12` |
|---|---|
| **V-1** (`.1R.10` §14.2 attribution undercount — corrected + re-baselined in `.1R.11`) | Carried as corrected historical attribution debt only. This phase adds no module-load-time import (§14), so it trips **no** consumer-inventory / isolation meta-guard — the `.1R.10` re-baseline situation does not recur. Not reopened. |
| **O1** (B1 positive-emission path unreachable under NON-REAL) | Unchanged. Gate 6's positive path (`approval_present=True`) is likewise unreachable; Gate-6 anti-transfer is verified at the `is_gate5_result` predicate + trusted-builder + `Gate6Decision`-discipline levels, exactly as `.1R.8`/`.1R.11` verified B1. Not worsened. |
| **O2** (N1 store trust is path + file integrity, not a writer seal — F7 boundary) | Unchanged. Gate 6 adds `type(evaluator) is PermissionBroker` and `type(pb_decision) is PermissionBrokerDecision` exact-type guards; it relies on the same canonical stores as Gate 5. Threat model not broadened. |
| **O3** (reverification test-name over-promise) | Unchanged, not propagated. New `.1R.12` tests are named for the exact stage that rejects. |
| **O4** (`pcae doctor task-memory` historical `tasks/DONE.md` omissions) | Unchanged, carried separately. Warning-only, pre-existing, unrelated to any code path. |
| **F2 / HPAC-REQ-054 Step 4** | Satisfied prerequisite; Gate 6 does not touch the Gate-5 / verifier path. |
| **F3** (`.1R.4` "eight-step" label debt) | Unchanged, deferred; not touched. |
| **F4** (test-name overclaim class) | Unchanged, deferred; new tests accurately named. |
| **F7** (registry resists caller-supplied-data forgery, not arbitrary same-process code execution) | Unchanged, threat model **not broadened**. `Gate6Decision` ephemerality is not claimed to protect against arbitrary trusted-process memory mutation. A process-isolation chapter remains separate, unscheduled, non-prerequisite. |

**Does Gate-6 PB consumption change any severity?** No. The findings that
were "harmless with no PB consumer" (O1/O2) remain harmless: the PB
consumer added here is still unreachable in production (NON-REAL hard stop
upstream), and every reachable Gate-6 path is rejection-only. No finding is
silently carried forward — each is dispositioned above.

---

## 14. Production files changed

`git diff --name-only a26b9fe2 HEAD -- src/pcae`:

```text
src/pcae/core/runtime_dispatch_permission.py
```

**One file.** Change: module docstring extended; three names added to the
existing `from .permission_broker_foundation import (...)` line
(`DECISION_VALUES`, `PermissionBroker`, `PermissionBrokerDecision`); one
new section appended — `_GATE6_DECISION_CONSTRUCTOR_SEAL`, `_GATE6_DECISIONS`,
`class Gate6Decision`, `is_gate6_decision`, `run_gate6_permission_broker`.
No existing function, class, or the `.1R.7` builder / B7 reread /
`project_human_authority_binding` was modified. The `runtime_dispatch_gate5`
import is **function-local** (inside `run_gate6_permission_broker`), so the
module-load import graph is unchanged and no consumer-inventory guard
trips (contrast `.1R.10`, where a module-level `hpac_lifecycle` import
required 7 meta-guard re-baselines).

`permission_broker_foundation.py`, `runtime_authority.py`,
`runtime_dispatch_gate5.py`, `hpac_lifecycle.py`, `runtime_introspection.py`
— all byte-unchanged since baseline (test-asserted).

---

## 15. Consumer inventory (phase prompt §36)

New production consumers introduced by `.1R.12`:

| Symbol consumed | New consumer | Classification |
|---|---|---|
| `runtime_dispatch_gate5.Gate5Result` (type) | `runtime_dispatch_permission.run_gate6_permission_broker` (function-local import) | **authorized `.1R.12`** (`.1R.9` §16.1 slice 2) |
| `runtime_dispatch_gate5.is_gate5_result` | same | **authorized `.1R.12`** |
| `runtime_dispatch_permission.build_runtime_dispatch_permission_broker_request` | `run_gate6_permission_broker` (same module, self-call) | **authorized `.1R.12`** |
| `permission_broker_foundation.PermissionBroker` / `.evaluate` | `run_gate6_permission_broker` | **authorized `.1R.12`** (`.1R.9` §22, PBRD-001 §7) |
| `permission_broker_foundation.PermissionBrokerDecision` / `DECISION_VALUES` | `run_gate6_permission_broker`, `Gate6Decision` | **authorized `.1R.12`** |
| `Gate6Decision` / `is_gate6_decision` / `run_gate6_permission_broker` | **none** (no production caller yet — a future Gate-7 chapter would be the first) | pre-existing-style staging; **no unexpected consumer** |

`grep -rn` over `src/pcae` for `run_gate6_permission_broker`,
`Gate6Decision`, `is_gate6_decision`: only definitions in
`runtime_dispatch_permission.py`. **Zero unexpected downstream consumers.**
`gate9_callers` / `gate9_consumers` remain empty
(`runtime_invocation_authority_consumption` has zero production importers).

---

## 16. Contract identity (phase prompt §41)

`git diff a26b9fe2 HEAD -- docs/contracts` is **empty**. Individually
byte-unchanged since baseline:

- `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` (RDGO-001 v3.0)
- `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001 v2.0)
- `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (RIASC-001 v3.0)
- `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.0)
- `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001 v2.0)
- `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` (RPAC-001 v1.0)
- `PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md` (PBPA-001)
- POL-005 (`permission_broker_foundation.py`) — `policy_id = "POL-005"`,
  `execution_boundary_unavailable`, unchanged.

V-2/V-3/V-4 require contract clarification eventually; **not performed
here** (not separately authorized).

---

## 17. Contract traceability

| Change | RDGO | HPAC | RIHAC / RIASC | PBRD |
|---|---|---|---|---|
| Gate-6 consumes Gate-5 projection only, via `is_gate5_result` + point-of-use re-resolution | §1, §7 | — | §16 step 12 | §4 fact 14, §7, §10 |
| Trusted `PermissionBrokerRequest` construction only (no caller request) | §7 | — | — | §5, §6, §15 |
| `approval_present` set only by successful RIHAC validation | §7 | — | §16 step 12 | §7 |
| Exact invocation binding; no cross-invocation reuse | §7 | — | §16 steps 5–8 | §15 |
| Unmodified evaluator; `DENY > HUMAN_REVIEW > ALLOW` preserved | §7 | — | — | §9 |
| POL-005 hard DENY of `simulation_only=False` preserved; verified authority does not override | §7 | — | — | §12, §15 |
| Ephemeral non-transferable `Gate6Decision`; ALLOW ≠ capability ≠ execution | §7, §11 | — | — | §10, §11, §5 |
| No approval / proof consumption; no `consumption.json` | §7 | — | — | §7 |
| No POL-005 / evaluator / capability change | §20 (of `.1R.9`) | — | — | §12 |

No undocumented Gate-6 semantics.

---

## 18. Regression evidence

### 18.1 Fixed-SHA regression attribution (deterministic)

Baseline `a26b9fe2` (phase-entry) vs candidate `HEAD`, explicit file list,
`-p no:randomly`, no `xdist`.

- **Targeted functional suites — 0 failures:**
  `test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py`
  (34), `test_runtime_dispatch_permission.py`,
  `test_gate5_approval_validation_coordinator_3w1r2b1r1_1r10.py`,
  `test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py`,
  `test_permission_broker_foundation.py`, `test_permission_broker.py`,
  `test_permission_broker_policy_applicability.py`,
  `test_permission_broker_policy_composition_hardening.py`,
  `test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py`,
  `test_runtime_authority_production_repair_3w1r2b1r1117.py`,
  `test_runtime_dispatch_no_external_effect.py`,
  `test_runtime_dispatch_regression_dry_path.py`,
  `test_runtime_dispatch_regression_pb_actions.py`,
  `test_runtime_dispatch_attempt_idempotency.py` →
  **622 + 43 + 34 = 699 passed, 0 failed**.

- **Pre-existing `test_blocking_reproduction_*` / contradiction-documentation
  failures** in the HPAC independent-verification suites
  (`…3w1r2b1r111r31.py`, `…3w1r2b1r111r32.py`, `…3w1r2b1r111r321.py`,
  `…3w1r2b1r1115a1.py`): a deterministic A/B (stash candidate, re-run;
  restore, re-run) on the exact same 4-file set produces the **identical
  failing-node set** with and without this phase's change
  (`diff` → `IDENTICAL`). These are the pre-existing class the `.1R.11`
  report enumerates ("44 shared failures … pre-existing
  contradiction-documentation class"). **Attributable to this phase: 0.**

- **CANDIDATE-ONLY NONPASSING NODES = 0.**
- **UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

No broad deselection was used to reach this.

### 18.2 `fast_green`

`699 passed, 0 failed` across the targeted Gate-6 / Gate-5 / permission
broker / runtime-authority / runtime-dispatch suites (the full `-m
fast_green` marker carries ~344 pre-existing repo-wide failures unrelated
to this phase; this phase adds no module-load import and trips none of the
point-in-time isolation guards — confirmed by the §18.1 A/B).

### 18.3 B1 / B7 / N1 / N2 regression (phase prompt §38)

Gate-6 does not reintroduce transferable authority / public-digest trust /
caller approval authority / caller human IDs:

- authority reaches the PB request only via
  `project_human_authority_binding` reading a registry-provenanced
  `ValidatedAuthorityProjection` (B1) — unchanged; `is_trusted_validated_authority_projection`
  still exact-type + exact-object + recomputed-digest;
- the B7 durable dispatch-identity reread (`identity._identity_tracker.revalidate`)
  still fires at the PB-request choke point — unchanged;
- `validate_approval` (N1/N2 — opaque ID, exact store type, fresh
  reverification) is byte-unchanged and not called by Gate 6;
- `test_runtime_authority_production_repair_3w1r2b1r1117.py` and the B1
  re-evaluation suite pass unchanged.

### 18.4 Gate-5 regression (phase prompt §39)

`.1R.11` closure intact: `runtime_dispatch_gate5.py` byte-unchanged;
Option-C `run_gate5`, the NON-REAL rejection, the non-transferable
`Gate5Result`, "consumes nothing", and the sequence-3 confirmation
semantics all still verified by the unchanged `.1R.10` + `.1R.11` suites
(passing). Gate-6 wiring reads `Gate5Result` only through the existing
`is_gate5_result` predicate and does not weaken Gate 5.

---

## 19. New focused tests

`tests/test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py`
— **34 new tests**, rejection-only + structural (no manufactured positive
authority):

1. Provenance: `None` / caller-constructed / reconstructed / unpicklable /
   duck-typed / bare-`validated=true` `Gate5Result` all fail closed;
   `_GATE5_RESULTS` and `_GATE6_DECISIONS` stay empty on every reject.
2. Structural input guards (identity type, construction-input type,
   `authority_current_time` type, `simulation_only` type, invocation-id
   binding) present and reachable.
3. Gate-6 owns request construction + evaluation, replicates no policy
   (AST: no `_compose` / `PolicyResult` / `PolicyRegistry` /
   `ExecutionDisabledRule` / `ReasonChainLink` / `_decision` calls; builds
   no `PermissionBrokerRequest`; exactly one `.evaluate(` call site).
4. POL-005 hard DENY preserved; DENY precedes HUMAN_REVIEW; HUMAN_REVIEW
   when `simulation_only=True` and no authority; verified authority does
   not override POL-005.
5. `Gate6Decision` discipline: not caller-constructable, not subclassable,
   `is_gate6_decision` rejects forgery/None/wrong-type, non-serializable,
   identity `==`/`hash`.
6. No Gate-7/8/9/10 module imported; runtime state unchanged after
   rejections; no `consumption.json` created.
7. Production-file allowlist (`src/pcae` diff ⊆ `runtime_dispatch_permission.py`);
   `permission_broker_foundation.py` + POL-005 + all 7 contracts +
   `runtime_authority.py` + `runtime_dispatch_gate5.py` + `hpac_lifecycle.py`
   byte-unchanged.
8. `.1R.7` builder surface unchanged (no `approval_present` param; missing
   authority → `approval_present=False`, empty binding).

---

## 20. Limitations

- **No positive Gate-6 evaluation is exercised** — the NON-REAL hard stop
  makes a real `Gate5Result` unobtainable without real FIDO2/UI (`.1R.9`
  §21, O1). Gate-6's anti-transfer / trusted-construction properties are
  verified at the predicate + builder + `Gate6Decision`-discipline levels,
  as `.1R.8`/`.1R.11` verified B1. End-to-end positive testing becomes
  possible only when a real assurance mechanism exists.
- **V-4** — the `human_authority_binding` 3-field vs 7-field
  contract-to-implementation mismatch is carried, not repaired (§5, §12).
- **V-2 / V-3** — carried forward from `.1R.11`, no Gate-6 impact (§12).
- **F7** — arbitrary in-process code execution is out of scope; a
  process-isolation chapter is separate and unscheduled.
- Gate-6's future consumer (a Gate-7 Runtime Enforcement chapter) has **no
  invented ID**.

---

## 21. `.1R.13` requirement

If `.1R.12` completes without unresolved blocking implementation defects
(it does), the recommended next phase is **exactly**:

**`149O.20L.7O.3W.1R.2B.1R.1.1R.13` — Independent Verification of Gate-6
Permission Broker Production Consumption Integration.** Scope: independently
re-derive PBRD-001 v2.0 §7/§9/§10/§12/§14, RDGO-001 v3.0 §7, and POL-005
against this implementation — not trusted from this report or its tests.
Requires separate explicit human authorization.

`.1R.13` must NOT begin here. Gate-7 / Gate-8 chapters must NOT begin and
have no invented ID. `.1R.14` (Gate-9) remains **blocked** until the
Gate-7/Gate-8 chapters exist or an explicit test-path-first scope is
human-authorized, and requires separate explicit human authorization
regardless.

---

## 22. Disposition

```text
GATE-6 PERMISSION BROKER PRODUCTION CONSUMPTION:
IMPLEMENTED
— INDEPENDENT VERIFICATION PENDING
— NOT CLOSED
```

Gate 6 is **not** independently verified by this phase.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved
unchanged. No delegated worker committed, finalized, or pushed. Governed
PCAE lifecycle only: no raw `git commit` / `git push`, `--no-verify`,
force push, history rewrite, or hook bypass.
