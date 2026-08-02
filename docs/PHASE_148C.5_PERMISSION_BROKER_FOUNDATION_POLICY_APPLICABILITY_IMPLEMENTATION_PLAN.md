# Phase 148C.5 — Permission Broker Foundation Policy Applicability Implementation Plan

## 0. Phase Type and Scope

**Implementation planning only.** This phase produces a concrete,
bounded, reviewable production implementation plan for PBPA-001 v1.0.
It does not modify `src/pcae/**`, does not implement applicability,
does not change `POL-001..012` semantics, does not modify `pcae push`,
does not close Finding B-1, does not begin Phase 148D, and does not
elevate runtime capability. Confirmed via `git diff --name-only
<148C.5-baseline>..HEAD -- src/pcae/`, empty (Section 57/Final Report).

This plan does not accept PBPA-001 v1.0's own text as sufficient
authority for "how" to implement it; every design decision below is
traced to a specific `PBPA-REQ-###` requirement, a specific existing
source line, or a specific existing test, discovered by direct
inspection during this phase — not copied from PBPA-001's own
illustrative code sketches, which are explicitly non-normative
(PBPA-001 §6 frames Option A/B/hybrid as candidates it *selects*
between, not as prescribed literal code).

---

## 1. Exact Production Change Surface

**Single production file in scope:**

```
src/pcae/core/permission_broker_foundation.py   (787 lines, MUST_CHANGE)
```

Confirmed by direct inspection of every production module that imports
`permission_broker_foundation` or `command_path_observation`
(`grep -rl` across `src/pcae/`):

| File | Relationship | Classification |
|---|---|---|
| `src/pcae/core/permission_broker_foundation.py` | Owns `PolicyRule`, `PolicyRegistry`, `PermissionBrokerRequest`, `PermissionBrokerDecision`, `DEFAULT_POLICY_RULES` | **MUST_CHANGE** |
| `src/pcae/core/command_path_observation.py` | Constructs a request and calls `PermissionBroker().evaluate()` once per `observe()` call (`:82`); consumes only the existing `PermissionBrokerDecision` return type, no field-by-field access | **MUST_NOT_CHANGE** — additive fields on `PermissionBrokerDecision` do not require any change here; `observe()`'s own contract (never raises, discards nothing it currently doesn't already discard) is unaffected |
| `src/pcae/commands/health.py`, `task.py`, `check.py`, `push.py` | Call `observe()` with `action_type="read"`, `execution_class="none"` (Section 9) | **MUST_NOT_CHANGE** |
| `src/pcae/core/runtime_introspection.py` | Imports one constant, `IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE` (`:74-76`), read-only | **MUST_NOT_CHANGE** |
| `src/pcae/core/runtime_snapshot.py`, `runtime_context.py`, `advisory_runtime.py`, `commands/runtime_inspect.py` | Each explicitly documents, in its own module docstring, that it never calls `PermissionBroker.evaluate()` and does not import `permission_broker_foundation` beyond (at most) `command_path_observation.INTEGRATION_REGISTRY` | **MUST_NOT_CHANGE** |
| `src/pcae/core/runtime_registry.py` | References `permission_broker_foundation.py`'s `_sanitize_result()` only in a comment, no import | **MUST_NOT_CHANGE** |

No broad refactor is in scope. The plan below is additive within one
file.

---

## 2. Exact Test Change Surface

Ten existing test files reference `permission_broker_foundation` or
`command_path_observation`. Two, `tests/test_permission_broker.py` and
`tests/test_permission_broker_cli.py`, import from
`pcae.core.permission_broker` — an unrelated, pre-existing Phase 88R
prototype module with a similar name — and are **out of scope**
(MUST_NOT_CHANGE, confirmed by `grep -n "^from\|^import"` showing no
reference to `permission_broker_foundation`).

| Test file | Effect of this implementation | Disposition |
|---|---|---|
| `tests/test_permission_broker_foundation.py` | 2 call sites assert `HUMAN_REVIEW` for a request whose only non-default field is `approval_present=False`, using `_valid_request()`'s default `execution_class="none"` (`:177`, `:206`) | **MUST BE UPDATED** (Section 9's finding) |
| `tests/test_permission_broker_policy_composition_hardening.py` | `test_decision_exposes_all_evaluated_triggered_causing_ids` asserts `len(decision.evaluated_policy_ids) == 12` (`:325`); `test_registry_accepts_additional_rules_without_modifying_broker` asserts `== 13` after adding one extra rule (`:381`); 2 more call sites assert `HUMAN_REVIEW`/`applicable=False`-affected outcomes at default `execution_class="none"` (`:144`, `:345`) | **MUST BE UPDATED** (Section 9) |
| `tests/test_permission_broker_policy_rule_framework.py` | `test_broker_evaluated_policy_ids_always_all_twelve` (`:203-207`) asserts `decision.evaluated_policy_ids == POLICY_IDS` (all 12) across four override combinations, none of which change `execution_class` from the default `"none"`; 3 more `HUMAN_REVIEW`-asserting call sites at default `execution_class="none"` (`:217`, `:228`, `:311`, `:390`) | **MUST BE UPDATED** — this test's own name states an invariant PBPA-REQ-081 deliberately redefines |
| `tests/test_permission_broker_verification_compatibility.py` | 2 call sites assert `HUMAN_REVIEW`-affected outcomes at default `execution_class="none"` (`:322`, `:353`); `:449` enumerates `PermissionBrokerDecision` field names (additive fields require this list to grow, not shrink or reorder) | **MUST BE UPDATED** |
| `tests/test_permission_broker_observation_hardening.py`, `test_permission_broker_observation_verification.py`, `test_permission_broker_command_path_prototype.py` | Exercise `observe()`/`command_path_observation`, which always passes `execution_class="none"` (Section 9); `approval_present` is always `True` at these call sites (health/task/check/push production code, not test-supplied) | **Expected unaffected** — verify during implementation, no plan-time change identified |
| `tests/test_permission_broker_command_path_design.py` | Documentation-only assertions against `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md` and `docs/PHASE_109_..._DESIGN.md`; no import of `permission_broker_foundation` | **MUST_NOT_CHANGE** |
| `tests/test_permission_broker.py`, `test_permission_broker_cli.py` | Target unrelated `pcae.core.permission_broker` (Phase 88R) | **MUST_NOT_CHANGE**, out of scope |

**New test coverage required** (not just updates): a complete
POL-001..012 applicability matrix test (Section 34 below), an
anti-spoofing/fail-closed matrix (Section 32), and explicit
`applicable_policy_ids`/`non_applicable_policy_ids` explainability
tests (Section 39). None of this exists today under any name.

---

## 3. PermissionRequest Consumer Inventory

Every production construction of a broker request is inventoried
below (found via `grep -rn "observe(" src/pcae/commands/`):

| Caller | `action_type` | `execution_class` | `approval_present` | `evidence_available` | `simulation_only` |
|---|---|---|---|---|---|
| `commands/health.py:23` | `"read"` | `"none"` | `True` | `True` | default (`True`) |
| `commands/task.py:1406` | `"read"` | `"none"` | `True` | `True` | default (`True`) |
| `commands/check.py:23` | `"read"` | `"none"` | `True` | `True` | default (`True`) |
| `commands/push.py:304` | `"read"` | `"none"` | `True` | `True` | default (`True`) |

**Compatibility sensitivity: none.** All four real callers use
`execution_class="none"` (outside `POL-004`'s applicable set,
PBPA-REQ-063) and `approval_present=True` (so `POL-004` does not
trigger today regardless of applicability). Every one of the twelve
`POL-001..012` results for these four call sites is therefore
unchanged by implementing PBPA-001 — this independently confirms
PBPA-REQ-042's "zero observed production behavior change" claim,
rather than merely repeating it. `observe()`'s return value is
discarded by every caller (`command_path_observation.py`'s own
contract, Section 1); no caller branches on `decision.decision` or
inspects `applicable_policy_ids`/`non_applicable_policy_ids`, so the
new fields introduce no new coupling.

The **only** consumers with compatibility sensitivity are the test
files inventoried in Section 2, which directly construct
`PermissionBrokerRequest`/call `PermissionBroker().evaluate()` with
test-supplied `execution_class` and `approval_present` values,
independent of any production call site.

---

## 4. Data Model Plan

Minimum addition, derived from PBPA-REQ-043/044:

```python
class PolicyRule:
    policy_id: str = ""
    name: str = ""
    implementation_status: str = POLICY_STATUS_NOT_IMPLEMENTED
    applicable_execution_classes: frozenset[str] | None = None   # NEW
```

`None` (the default) means universal — identical in effect to every
current rule's behavior today (PBPA-REQ-044: "absent metadata... means
universal — identical, not merely similar, to the explicit `None`
case"). Only `MissingHumanApprovalRule` overrides it:

```python
class MissingHumanApprovalRule(PolicyRule):
    ...
    applicable_execution_classes = frozenset({
        EXECUTION_CLASS_SHELL,
        EXECUTION_CLASS_BACKEND,
        EXECUTION_CLASS_ADAPTER,
        EXECUTION_CLASS_ROLLBACK,
    })
```

`PolicyResult` gains one additive field (PBPA-REQ-014):

```python
@dataclass(frozen=True)
class PolicyResult:
    ...
    applicable: bool = True   # NEW; default True preserves every
                               # existing PolicyResult call site/fixture
```

`PermissionBrokerDecision` gains two additive fields (PBPA-REQ-081):

```python
@dataclass(frozen=True)
class PermissionBrokerDecision:
    ...
    applicable_policy_ids: tuple[str, ...] = ()      # NEW
    non_applicable_policy_ids: tuple[str, ...] = ()  # NEW
```

No new top-level module (Option B, "separate immutable applicability
object") and no registry-level static mapping (Option C) are adopted —
see Section 5.

---

## 5. Policy Metadata Representation — Option Selection

Evaluated per PBPA-001 §6's own selection criteria (Section 48
requires this plan re-derive the choice, not just restate it):

- **Option A (field on `PolicyRule`, selected):** immutable (frozen
  class attribute, same mechanism already used for
  `implementation_status`), inspectable (`rule.applicable_execution_classes`
  readable without registry access), deterministic, versionable (travels
  with the module, no separate artifact — PBPA-REQ-043), testable
  (direct attribute assertion). Zero new classes, zero constructor
  signature changes (Section 26).
- **Option B (separate `PolicyApplicability` object):** rejected —
  adds an indirection layer with no capability Option A lacks; 148C.2
  §18 (re-confirmed 148C.4 §3) already compared this and selected the
  hybrid that keeps metadata policy-owned.
- **Option C (registry-level static mapping keyed by `policy_id`):**
  rejected — this is exactly the "dual applicability authority" PBPA-001
  §7/PBPA-REQ-021 forbids (registry enforces; policy owns and declares).
  A registry-level mapping would let two independently-edited pieces of
  code define one policy's domain.

**Selected: Option A**, matching PBPA-001's own selection and
independently re-confirmed as the least-complex option that satisfies
Section 6 below.

---

## 6. Avoiding Dual Applicability Authority

One normative truth: `PolicyRule.applicable_execution_classes` (owned
by the policy class). The registry never redefines it; it only reads
it. The predicate (Section 7) is a single generic function shared by
every rule — it is not overridden per-subclass, so no rule can encode
a second, competing definition of its own domain. `MissingHumanApprovalRule.evaluate()`
itself is untouched (PBPA-001 §46 table: "NO CHANGE... only a sibling
applicability attribute is added") — the condition it evaluates
(`approval_present`) and the domain it applies to
(`applicable_execution_classes`) remain two separate, non-overlapping
concerns by construction.

---

## 7. Policy Predicate Plan

One generic method on the `PolicyRule` base class, not a per-rule
override (this is what keeps applicability single-authority, Section 6):

```python
class PolicyRule:
    ...
    def applies_to(self, request: PermissionBrokerRequest) -> bool:
        return (
            self.applicable_execution_classes is None
            or request.execution_class in self.applicable_execution_classes
        )
```

Pure, deterministic, side-effect-free, reads only `self`'s frozen class
attribute and the request's `execution_class` field — no I/O, no
mutation, no dependency on evaluation order. Called by
`PolicyRegistry.evaluate_all` (Section 15), never by callers, never by
`PermissionBroker.evaluate()` directly, preserving PBPA-REQ-021's
"registry is the sole enforcer" rule.

An unknown `execution_class` value (not a member of any rule's
`applicable_execution_classes` frozenset, and not `None`) simply
evaluates to `False` for scoped rules — no exception, no special case
needed, because `POL-006` (`UnknownCapabilityRule`, universal,
`applicable_execution_classes = None`) independently denies any
`execution_class not in KNOWN_EXECUTION_CLASSES` regardless of what
this predicate returns for other rules (Section 8).

---

## 8. `execution_class` Validation Plan

**No new validation is required.** `POL-006` (`UnknownCapabilityRule`,
`permission_broker_foundation.py:478-522`) already DENYs any
`execution_class not in KNOWN_EXECUTION_CLASSES` today, and — critically
— it is and remains universal (`applicable_execution_classes = None`,
Section 17), so it is never itself filtered out by applicability
resolution. PBPA-REQ-077 makes this a normative requirement, not an
implementation convenience: "`POL-006` and `POL-007`... are themselves
universal... and are NEVER subject to applicability filtering by any
other rule's scope."

Handling by case:

| Case | Outcome |
|---|---|
| Missing `execution_class` (structurally impossible — dataclass field is required, not `Optional`) | N/A; `PermissionBrokerRequest` construction itself would fail before reaching the broker |
| Malformed / unsupported value | `POL-006` DENYs (`_compose` DENY precedence, unchanged); every `applicable_execution_classes`-scoped rule's predicate also independently returns `False` for it, so no scoped rule could contribute an ALLOW even if `POL-006` were somehow bypassed — two independent fail-closed layers, not one |
| Future value not yet in `KNOWN_EXECUTION_CLASSES` | Same as malformed — `POL-006` DENYs until a dedicated future amendment adds it to `KNOWN_EXECUTION_CLASSES` (existing `POL-006` behavior, unchanged) |
| Action/class mismatch (e.g. `action_type="read"` with `execution_class="mutation"`) | Out of scope for this contract layer — PBPA-001 does not introduce action/class pairing validation (no `PBPA-REQ-###` requires it) and this plan does not add it; it would be a `POL-006`-adjacent enhancement, not an applicability concern |

No classification issue can silently reduce applicability below what
`POL-006`'s existing DENY already forecloses.

---

## 9. Classification Authority Plan — and the Concrete Backward-Compatibility Finding

PBPA-REQ-022 fixes `execution_class` per integration point, not
caller-discretionary per request; this implementation does not add new
authentication of `execution_class` beyond what `POL-006` already
enforces (set membership) — no adapter-level re-derivation exists
today, and PBPA-001 itself does not require one (its anti-spoofing
model, independently re-verified 148C.4 §16-17, rests on
"contract-fixed per integration point," a design-time guarantee
enforced by code review of the four call sites in Section 3, not a
runtime cross-check). This plan does not deepen that guarantee; it
inherits it unchanged.

**The concrete finding this phase adds, not present in PBPA-001's own
text:** PBPA-REQ-042 states implementing this contract "changes zero
observed production behavior... today." That claim is accurate for
*production* consumption (Section 3) but does not cover the **existing
test suite**, which does exercise `PermissionBroker.evaluate()`
directly with a `execution_class="none"` default. Independently
verified by direct inspection (Section 2): four test files, at minimum
ten call sites, assert `HUMAN_REVIEW` for `approval_present=False`
requests using the default `execution_class="none"` — a class outside
`POL-004`'s frozen applicable set. Once `POL-004` becomes
non-applicable to `"none"`, those specific call sites' expected
decision changes from `HUMAN_REVIEW` to `ALLOW` (no other policy
triggers under those defaults). This is real, mechanical,
implementation-time test work — not a hypothetical the plan can defer.
See Section 40.

---

## 10. Backward Compatibility Strategy

```
recognized, scoped policy (POL-004 only)
    → applicability narrowed per PBPA-REQ-063

every other current policy (POL-001,002,003,005,006,007,008,009,010,011,012)
    → applicable_execution_classes = None (unchanged, universal)

legacy/unclassified consumer (any caller not using an in-scope
execution_class for POL-004)
    → sees identical results to today, confirmed per-consumer in Section 3
```

Guarantee: no existing production consumer receives fewer applicable
policies (Section 3 confirms this by enumeration, not assumption — all
four real consumers use `"none"`, already outside `POL-004`'s narrowed
scope, and already supply `approval_present=True`). No conservative
"unclassified → universal" special case is needed beyond the existing
`applicable_execution_classes = None` default, because every current
consumer's `execution_class` is already a `KNOWN_EXECUTION_CLASSES`
member (`"none"`) — there is no unclassified state to handle
separately.

---

## 11. Production Metadata Plan — POL-001..012

Table independently re-derived from PBPA-001 §17/§18 (itself
independently re-verified against primary source by 148C.4 §14-15) —
not copied without re-checking against current source
(`permission_broker_foundation.py:577-590`):

| Policy | Current evaluator | PBPA applicability | Production metadata | Predicate behavior |
|---|---|---|---|---|
| POL-001 `MissingActiveTaskRule` | implemented | universal | `None` (default, unchanged) | Evaluated for every request, as today |
| POL-002 `StubPolicyRule("POL-002", ...)` | not implemented | deferred (F-1) | `None` (default, unchanged) | Registered, never triggers (stub), as today |
| POL-003 `MissingEvidenceRule` | implemented | universal | `None` (default, unchanged) | Evaluated for every request, as today |
| POL-004 `MissingHumanApprovalRule` | implemented | **scoped** | `frozenset({SHELL, BACKEND, ADAPTER, ROLLBACK})` | Evaluated only for these 4 classes; `NOT_APPLICABLE` for `none`/`mutation` |
| POL-005 `ExecutionDisabledRule` | implemented | universal | `None` (default, unchanged) | Evaluated for every request, as today (PBPA-REQ-069) |
| POL-006 `UnknownCapabilityRule` | implemented | universal (never filtered, PBPA-REQ-077) | `None` (default, unchanged) | Evaluated for every request, always |
| POL-007 `UnknownComponentRule` | implemented | universal (never filtered, PBPA-REQ-077) | `None` (default, unchanged) | Evaluated for every request, always |
| POL-008..012 `StubPolicyRule(...)` | not implemented | deferred (F-1) | `None` (default, unchanged) | Registered, never triggers, as today |

No policy's *meaning* (evaluator logic) is reinterpreted — only
`POL-004` gains a sibling attribute; its `evaluate()` body
(`:427-443`) is untouched (Section 6).

---

## 12. POL-004 Production Plan

```python
class MissingHumanApprovalRule(PolicyRule):
    policy_id = "POL-004"
    name = "Missing Human Approval"
    implementation_status = POLICY_STATUS_IMPLEMENTED
    applicable_execution_classes = frozenset({
        EXECUTION_CLASS_SHELL,
        EXECUTION_CLASS_BACKEND,
        EXECUTION_CLASS_ADAPTER,
        EXECUTION_CLASS_ROLLBACK,
    })

    def evaluate(self, request: PermissionBrokerRequest) -> PolicyResult:
        # UNCHANGED — same body as today (:427-443)
        ...
```

No `if action == push`, no push-specific branch, no fake approval, no
weakening of `HUMAN_REVIEW`. The scope is the general rule PBPA-001 §18
derived (and 148C.4 §11-12 independently re-derived through three
primary sources), applied uniformly to whichever request happens to
carry a scoped `execution_class` — `pcae push`'s future
`execution_class=mutation` falls outside this set as one instance of
that general rule, not a carve-out written to produce that result
(Section 13).

**Invariant preserved exactly:** for any request where
`POL-004.applies_to(request)` is `True` and `approval_present=False`,
the decision remains `HUMAN_REVIEW` — same code path, same
`decision_reason="missing_human_approval"`, same `NG-008`/`INV-003`
mapping, unchanged.

---

## 13. Mutation Class and `pcae push` (Documentation Only — Not Implemented Here)

`pcae push` does not consume `PermissionBroker` today (PBPA-REQ-042;
independently reconfirmed 148B/148C/148C.1/148C.2/148C.3/148C.4). This
plan does not implement PBPC and does not touch `push.py` beyond
Section 3's read-only inventory. For a *future* PBPC-conformant push
request (not built by this phase), documented here only for later B-1
re-evaluation:

- Expected `execution_class`: `EXECUTION_CLASS_MUTATION` (`"mutation"`),
  per PBPA §8/`PBPC-REQ-034` as already frozen by PBPC-001 v1.1.
- `POL-004` applicability: **NOT_APPLICABLE** — `"mutation"` is not a
  member of `{shell, backend, adapter, rollback}` (PBPA-REQ-063).
- Determining rule: `POL-004`'s frozen `applicable_execution_classes`
  set (Section 12), applied by the generic predicate (Section 7) to
  whatever `execution_class` a future PBPC integration supplies.

This does not close B-1. B-1 closure requires a real PBPC-conformant
push integration to exist and be independently verified
(§12/§38-remaining-path, restated 148C.3/148C.4) — a request that does
not exist yet, built by phases after this one.

---

## 14. `simulation_only` Plan

`simulation_only` is not read by `applies_to()` (Section 7) and is not
part of `applicable_execution_classes` metadata for any policy
(PBPA-REQ-068). It continues to mean exactly what Phase 108A/PBPC-001
§10.1 already established: whether the Foundation's own
not-yet-existing execution boundary is being asked to act — orthogonal
to `execution_class`, which describes the requested operation's own
character (PBPA-REQ-070/071). Implementation adds no code path where
`simulation_only=True` changes which policies are applicable; `POL-005`
(`ExecutionDisabledRule`) remains universal and continues to evaluate
its own, unrelated triggering condition (`if request.simulation_only`)
on every request, exactly as today (PBPA-REQ-069). No downgrade path
exists because none is introduced.

---

## 15. Applicability API

No new public/CLI surface (Section 15's own instruction). The only
change is internal, inside `PolicyRegistry.evaluate_all`:

```python
def evaluate_all(self, request: PermissionBrokerRequest) -> tuple[PolicyResult, ...]:
    results: list[PolicyResult] = []
    for rule in self._rules:
        if not rule.applies_to(request):
            results.append(PolicyResult(
                policy_id=rule.policy_id,
                triggered=False,       # registry's own not-run default (PBPA-REQ-015)
                applicable=False,
            ))
            continue
        try:
            raw = rule.evaluate(request)
        except Exception:
            raw = None
        results.append(_sanitize_result(rule, raw))   # applicable=True (dataclass default)
    return tuple(results)
```

This keeps `evaluate_all`'s existing signature and return type exactly
as-is — one `PolicyResult` per registered `policy_id`, in registry
order, for every request (Section 18's completeness guarantee) — while
satisfying PBPA-REQ-015 ("a policy with `applicable=False` SHALL NOT be
passed to its own `evaluate()` method"). `_compose` (Section 22)
already only inspects `r.triggered`, so a non-applicable
`triggered=False` result structurally cannot contribute to DENY/
HUMAN_REVIEW precedence — no change to `_compose` itself is required
(PBPA-REQ-079/080).

---

## 16. Explainability Result Plan

`_compose` (Section 22) gains two lines computing the additive fields
from `results` (already available, no new data source):

```python
applicable_policy_ids = tuple(r.policy_id for r in results if r.applicable)
non_applicable_policy_ids = tuple(r.policy_id for r in results if not r.applicable)
```

`evaluated_policy_ids`'s existing computation
(`tuple(r.policy_id for r in results)`, `:676`) is **redefined in
meaning, not in code** — per PBPA-REQ-081, since non-applicable results
are now registry-synthesized placeholders never passed to `evaluate()`,
`evaluated_policy_ids` already equals `applicable_policy_ids` without
any further code change; the two fields will hold identical tuples.
(This plan does not de-duplicate them into one field — PBPA-REQ-081
keeps `evaluated_policy_ids` for compatibility of the field's
*existence*, while clarifying its meaning going forward; no field is
removed, matching PBPA-001 §46's "additive fields only" classification.)

No persistence — these fields are returned data only, never written to
`.pcae/`, matching the module's existing io-free contract.

---

## 17. No New Top-Level Decision

Unchanged: `DECISION_ALLOW`/`DECISION_DENY`/`DECISION_HUMAN_REVIEW`
remain the only three `PermissionBrokerDecision.decision` values
(PBPA-REQ-013). `NOT_APPLICABLE` exists only as `PolicyResult.applicable
= False`, one layer below the broker decision, never surfaced as a
fourth decision value.

---

## 18. Required Policy Set Validation

New validation, at `PolicyRegistry.__init__`, per PBPA-REQ-073:

```python
def __init__(self, rules: tuple[PolicyRule, ...] = DEFAULT_POLICY_RULES) -> None:
    ids = tuple(rule.policy_id for rule in rules)
    if len(ids) != len(set(ids)):
        raise ValueError("PolicyRegistry: duplicate policy_id in rule set")
    missing = POLICY_IDS_CANONICAL - set(ids)
    if missing:
        raise ValueError(f"PolicyRegistry: missing canonical policy id(s): {sorted(missing)}")
    self._rules = rules
```

This requires freezing a `POLICY_IDS_CANONICAL: frozenset[str]`
constant separate from today's `POLICY_IDS` (which is *derived from*
`DEFAULT_POLICY_RULES`, `:592`, and therefore cannot itself serve as
the independent canonical reference PBPA-REQ-073 requires — validating
a registry's completeness against a set derived from that same
registry would be circular). `POLICY_IDS_CANONICAL` is a fixed literal
of the twelve `POL-001..012` strings.

**Failure behavior:** construction-time `ValueError`, not a runtime
DENY — this is a programming defect (a registry built by future code
that forgot a policy), not a request-time condition, consistent with
PBPA-REQ-073 calling it a "registry-construction defect."
`test_registry_accepts_additional_rules_without_modifying_broker`
(Section 2) adds a superset (`DEFAULT_POLICY_RULES + one extra rule`)
and remains valid under this check (canonical set is a subset, not an
exact-match requirement).

---

## 19. Registry Validation Plan

Today: no validation exists at any stage (construction, registration,
or `evaluate_all`) — `PolicyRegistry.__init__` (`:640-641`) stores
`rules` unconditionally. Minimal change: add the two checks in Section
18 at `__init__` only (not at every `evaluate_all` call, which would
repeat a constant-cost check on every request for no benefit — the
registry's rule tuple cannot change after construction, since
`PolicyRule.applicable_execution_classes` is a frozen class attribute
and `self._rules` is never reassigned).

Enforced: unique `policy_id` (Section 18), canonical-set completeness
(Section 18), immutable metadata (Section 24 — enforced by Python
`frozenset`/class-attribute mechanics, no runtime check needed). Not
enforced at this layer: "valid applicability metadata" beyond
type — `applicable_execution_classes` is either `None` or a
`frozenset[str]`; a rule author supplying a non-frozenset value is a
type-checking-time defect (mypy/static analysis, per repository
convention), not a runtime `PolicyRegistry` validation concern, since
no primary source (`PBPA-REQ-###`) requires a runtime type check here.

---

## 20. Applicability Failure Plan

| Failure | Outcome | Mechanism |
|---|---|---|
| Predicate exception (a future rule's `applies_to` override raises) | Cannot resolve ALLOW | Not handled specially by this plan — `applies_to()` (Section 7) has no override point in v1.0's scope (only the base-class generic implementation exists); this row is reserved should a future phase add per-rule predicate overrides. Today's implementation cannot raise (pure attribute/membership check). |
| Malformed metadata (non-frozenset, non-`None`) | Construction-time defect | Section 19 — not a runtime request-path failure |
| Unsupported `execution_class` | DENY | `POL-006`, Section 8 — independent of applicability resolution |
| Missing policy | Construction-time `ValueError` | Section 18 |
| Duplicate policy | Construction-time `ValueError` | Section 18 |
| Unknown policy version | N/A — no per-policy versioning exists or is introduced (Section 25) | — |
| Applicability-version mismatch | N/A — applicability travels with the Foundation module version, no separate version field (PBPA-REQ-043) | — |

No case above converts a failure into `NOT_APPLICABLE` — construction
failures raise before any request is ever evaluated; request-path
failures (unsupported class) DENY via `POL-006`, never silently narrow
applicability for other rules.

---

## 21. Empty Applicable Set

Independently re-confirmed by 148C.4 §15/Finding V-2 and re-verified
here directly against the metadata table in Section 11: for every one
of the six `KNOWN_EXECUTION_CLASSES` values, `POL-001, POL-003, POL-005,
POL-006, POL-007` (all universal, `applicable_execution_classes = None`)
remain applicable — an empty applicable set is not reachable under this
implementation for any currently-known class. Defense-in-depth per
Finding V-2's own recommendation: `_compose`'s existing empty-`results`
branch (`:680-691`, `DECISION_DENY`, `"no_applicable_policy"`) already
fails closed and requires no new code — it exists today for the
"registry has zero rules" case and is reachable-in-principle for
"registry has rules but none applicable," with no additional
implementation required. This plan does not add a distinct
`applicable_policy_ids == ()` check beyond what `_compose`'s existing
empty-triggered-among-applicable logic already provides, since
`_compose` operates on `results` (all `PolicyResult`s, applicable or
not) rather than a pre-filtered applicable-only list — no rewrite is
needed (Section 22).

---

## 22. Decision Aggregation Preservation

`_compose` (`:662-736`) is **not modified**. It already receives the
full `results` tuple (including registry-synthesized
`applicable=False, triggered=False` entries from Section 15) and
already only inspects `r.triggered` for DENY/HUMAN_REVIEW matching
(`:694`) — a non-applicable entry's `triggered=False` makes it
structurally indistinguishable, from `_compose`'s point of view, from
"evaluated and did not fire," which is exactly PBPA-REQ-079's required
effect ("sufficient to achieve this without any change to `_compose`'s
own logic"). The two new lines computing
`applicable_policy_ids`/`non_applicable_policy_ids` (Section 16) are
additions to `_compose`'s return construction, not changes to its
precedence logic.

Tests required (Section 41) proving: DENY precedence unchanged;
HUMAN_REVIEW precedence unchanged; ALLOW behavior unchanged; only
applicable policies can contribute a `triggered=True` result.

---

## 23. Deterministic Ordering

Unchanged: `results` (and therefore `applicable_policy_ids`,
`non_applicable_policy_ids`, `evaluated_policy_ids`,
`triggered_policy_ids`) preserve `DEFAULT_POLICY_RULES` / the
constructed registry's tuple order — `POL-001..012` numeric order for
the default registry (`:577-590`) — because `evaluate_all` (Section 15)
iterates `self._rules` in order and appends to `results` in order, as
it already does today. No `set`, no dict-ordering dependency, no
externally-observable non-determinism is introduced.

---

## 24. Immutability

`applicable_execution_classes: frozenset[str] | None` uses `frozenset`
(hashable, immutable) matching the existing `COMPONENT_IDS`,
`KNOWN_ACTION_TYPES`, `KNOWN_EXECUTION_CLASSES` convention already in
this module (`:81`, `:107-118`, `:127-134`). It is a class attribute on
a class with no `__init__`-time override for the four implemented
rules with fixed scope (`MissingHumanApprovalRule` sets it as a class
attribute, same mechanism as `implementation_status`), so no runtime
broker API path can mutate it — there is no setter, no public method
that assigns to it, and Python class attributes are not accidentally
mutable through the `PermissionBroker`/`PolicyRegistry` public surface.

---

## 25. Versioning Implementation

**No new version constant is introduced.** PBPA-REQ-043 is explicit:
applicability metadata "travels with the Foundation contract version,
no separate artifact." The Foundation module has no existing
`__version__`-style constant of its own today (it is versioned by
which phase last froze/amended it, tracked in `PROJECT_STATUS.md` and
this document's own changelog, not in-source) — introducing one now
would be version machinery for decoration, explicitly against this
section's own instruction. Compatibility/future changes are controlled
the same way every other `POL-###` change has been controlled to date:
a dedicated phase, a frozen contract amendment (e.g. PBPA-001 v1.1),
and this repository's existing phase-numbering discipline.

---

## 26. Existing API Compatibility

| Change | Classification | Compatibility risk |
|---|---|---|
| `PolicyRule.applicable_execution_classes` class attribute (new) | **ADDITIVE** | None — `MissingActiveTaskRule()`, `StubPolicyRule("POL-999", "Test Stub")` (`tests/test_permission_broker_policy_rule_framework.py:153,162,168`) construct with existing no-arg/2-positional-arg signatures, unaffected; new attribute has a class-level default |
| `PolicyRule.applies_to()` method (new) | **ADDITIVE** | None — no existing subclass overrides a method of this name (confirmed: only `evaluate()` is overridden anywhere in the module or tests) |
| `PolicyResult.applicable: bool = True` (new field) | **ADDITIVE, BACKWARD_COMPATIBLE** | Existing `PolicyResult(...)` construction call sites (production and test) that don't pass `applicable=` get the default `True`, matching today's implicit "every result comes from an evaluated rule" assumption |
| `PermissionBrokerDecision.applicable_policy_ids`/`non_applicable_policy_ids: tuple[str, ...] = ()` (new fields) | **ADDITIVE, BACKWARD_COMPATIBLE** | Same reasoning; `tests/test_permission_broker_verification_compatibility.py:449`'s field-name enumeration (Section 2) is the one test that must be updated to include the two new names — an intentional, expected update to a test whose purpose is exactly "enumerate all fields," not a break |
| `evaluated_policy_ids` semantic redefinition (PBPA-REQ-081) | **BACKWARD_COMPATIBLE with a documented semantic change** — not purely additive | This is the finding in Section 9: the field's *value* changes for requests where a scoped policy is non-applicable, even though its type and existence do not. No `INTERNAL_ONLY` or `BREAKING` classification applies because the field remains public and present; but this plan does not understate the change by calling it purely additive |
| `PolicyRegistry.__init__` gaining validation that can raise `ValueError` (Section 18) | **BACKWARD_COMPATIBLE for all current callers** | Every current call site (`PolicyRegistry()` with the default `DEFAULT_POLICY_RULES`, or the test's `DEFAULT_POLICY_RULES + one extra rule`) passes a superset of the canonical 12 with no duplicates, so none raise; a hypothetical future caller passing an incomplete rule tuple would newly raise, which is the intended fail-closed behavior (Section 18), not an accidental break |

No `BREAKING` change is introduced. **Dangerous default rejected:**
"missing applicability metadata ⇒ applies nowhere" is explicitly not
adopted — the selected default (`None` ⇒ universal, Section 4) is the
"safer default" this section's own guidance names, and is exactly what
PBPA-REQ-044 requires.

---

## 27. Implementation Staging

```
Stage 1 — Types and metadata
  Add PolicyRule.applicable_execution_classes (default None) and
  PolicyResult.applicable (default True). Add MissingHumanApprovalRule's
  override. No wiring into evaluate_all yet — evaluate_all still calls
  rule.evaluate() unconditionally. Zero behavior change; adds only
  inert, unread attributes. Full existing test suite passes unmodified.

Stage 2 — Registry validation
  Add POLICY_IDS_CANONICAL and PolicyRegistry.__init__'s duplicate/
  missing-policy checks (Section 18). Still no applicability filtering.
  Zero behavior change for any currently-passing registry construction.

Stage 3 — Applicability resolution
  Add PolicyRule.applies_to() (Section 7). Still not called by
  evaluate_all. Zero behavior change; pure, tested in isolation.

Stage 4 — Evaluation integration
  Wire applies_to() into evaluate_all (Section 15) — the one stage that
  actually changes runtime behavior (POL-004 becomes non-applicable for
  none/mutation). This is the stage where Section 9's test updates
  (Section 40) land, in the same commit, so no intermediate commit
  exists with filtering active but tests unupdated (Section 30).

Stage 5 — Explainability
  Add applicable_policy_ids/non_applicable_policy_ids to _compose
  (Section 16). Additive; does not change decision/triggered/DENY-
  HUMAN_REVIEW-ALLOW behavior already finalized in Stage 4.

Stage 6 — Compatibility and adversarial hardening
  Full new test matrix (Sections 32-39): anti-spoofing, complete
  POL-matrix coverage, unknown/missing/duplicate-policy fail-closed
  tests, explainability determinism tests, legacy-compatibility
  re-verification (Section 3's four real consumers re-run against the
  new code and re-confirmed byte-identical decisions).
```

This order is chosen, not merely copied from the illustrative
structure in the originating prompt, because each stage before Stage 4
is independently a no-behavior-change commit (verifiable by running
the full existing suite unmodified) — this directly satisfies Section
30's "safe intermediate state" requirement without a feature flag
(Section 28).

---

## 28. Feature Flag Assessment

**No feature flag is needed or recommended.** Reasoning:

- The behavior change is confined to one rule (`POL-004`) and is
  proven safe for every real production consumer (Section 3) before
  any flag would even be relevant.
- Staging (Section 27) already provides safe intermediate commit
  points without runtime toggling.
- A flag whose disabled state "restores old universal evaluation"
  would, by construction, be exactly the kind of caller-facing
  weakening mechanism PBPA-REQ-022 forbids if it were ever exposed
  beyond a temporary rollout — and this repository's own instruction
  (Section 28 of the originating scope) explicitly names
  `PCAE_DISABLE_POLICY_APPLICABILITY` as an anti-pattern to avoid.
- No production consumer branches on the broker's decision (Section
  3), so there is no rollout-risk audience a flag would protect;
  "rollout risk" here is bounded to the test suite, which this plan
  updates in the same commit as the behavior change (Stage 4), not
  gradually.

---

## 29. Migration Strategy

Atomic within Stage 4 (Section 27): applicability filtering and the
test updates it requires land together, in one commit, not spread
across a window where filtering is live but assertions are stale.
Metadata (Stages 1-3) must exist before filtering activates (Stage 4)
by construction — `evaluate_all` cannot call `rule.applies_to()`
(Section 15) before `applies_to()` exists (Stage 3) or before
`applicable_execution_classes` is defined (Stage 1). No legacy policy
definition exists outside `DEFAULT_POLICY_RULES` in this codebase
(Section 1's consumer inventory found none), so there is no external
policy-definition migration to plan for.

---

## 30. Safe Intermediate State

Stages 1-3 (Section 27) are, individually, "add code, wire nothing" —
verified safe by running the full existing suite unmodified after each
stage and confirming zero failures (a concrete Stage 6 acceptance
check, Section 41). No intermediate commit reaches "applicability
filtering enabled + incomplete metadata" because filtering (Stage 4)
and the one rule with non-`None` metadata (`POL-004`, added in Stage
1) are both complete before Stage 4 begins — there is no rule added
between Stage 1 and Stage 4 that could be "incomplete" at the moment
filtering activates. If governed commits must be separate per this
repository's convention, Stages 1-3 may each be their own commit,
verified independently; Stage 4 is the one commit where behavior
actually changes and must include its required test updates
atomically.

---

## 31. Rollback Plan

`git revert` of Stage 4's commit (Section 27) restores
`evaluate_all`'s unconditional `rule.evaluate()` call, which — because
Stages 1-3's additions are inert until Stage 4 wires them in
(Section 27) — immediately and fully restores today's conservative,
universal-evaluation behavior with no dependency on any runtime state
(no flag, no `.pcae/` artifact, no database row to also roll back).
Stages 1-3 may remain reverted or not; leaving their inert additions
in place after reverting Stage 4 changes nothing observable. No
policy's meaning is lost by a rollback — `evaluate()` bodies are never
touched by any stage (Section 6/12).

---

## 32. Anti-Spoofing Test Matrix (planned, not written by this phase)

| Test | Expected |
|---|---|
| Caller lies about `execution_class` (claims `"none"` for what is really a shell command) | Not detectable by this layer — inherited limitation (Section 9), documented not silently assumed away; broker has no independent evidence source to check against, matching PBPA-001's own threat model boundary |
| `action_type`/`execution_class` mismatch | Out of scope (Section 8) — no new check added |
| Future unknown class | `POL-006` DENY (Section 8) |
| Missing class | Structurally impossible (dataclass required field) |
| Malformed class (e.g. empty string, wrong type) | `POL-006` DENY (string not in `KNOWN_EXECUTION_CLASSES`); a non-`str` value would need `KNOWN_EXECUTION_CLASSES.__contains__` to handle gracefully, which `frozenset.__contains__` already does (returns `False`, no exception) |
| Simulation spoofing (`simulation_only` used to imply a weaker class) | Not possible — `simulation_only` is not an applicability input (Section 14) |
| Direct Foundation invocation bypassing `command_path_observation.observe()` | Broker has no caller-identity check today and this plan does not add one — same limitation as today, unrelated to applicability |
| Class/profile downgrade via caller-supplied exclusion parameter | Structurally impossible — no such parameter exists on `PermissionBroker.evaluate()` or `PolicyRegistry.evaluate_all()`, and this plan does not add one (PBPA-REQ-022) |
| Forged metadata (attempting to set `applicable_execution_classes` at the instance level) | Not preventable at the language level for a determined caller mutating Python object internals, same boundary every "immutable" Python dataclass/class-attribute pattern in this module already accepts (e.g. `implementation_status` today) — not a new gap introduced by this plan |

---

## 33. POL-004 Tests (planned)

- In-scope class (e.g. `execution_class="shell"`), `approval_present=False` → `HUMAN_REVIEW`, `POL-004` in `triggered_policy_ids` and `applicable_policy_ids`.
- In-scope class, `approval_present=True` → not triggered, `POL-004` in `applicable_policy_ids`, not in `triggered_policy_ids` — existing semantics preserved.
- Out-of-scope class (`"none"`, `"mutation"`) → `POL-004` in `non_applicable_policy_ids`, never in `evaluated`/`triggered`/`applicable_policy_ids`; overall decision is `NOT_APPLICABLE`-driven `ALLOW` when nothing else triggers, not `HUMAN_REVIEW`.
- Evidence independence: toggling `approval_present` for an out-of-scope-class request does not change `POL-004`'s applicability (still `NOT_APPLICABLE` either way) — proves applicability is resolved from `execution_class` alone, strictly before `approval_present` is read (PBPA's core separation, re-verified 148C.4 §8-9).

---

## 34. Complete POL Matrix Tests (planned)

One applicability test per `POL-001..012` (not just `POL-004`),
parametrized across all six `KNOWN_EXECUTION_CLASSES` values, asserting
`applicable=True` for the eleven universal rules on every class, and
the `{shell,backend,adapter,rollback}`/`{none,mutation}` split for
`POL-004` specifically (Section 11's table, made executable).

---

## 35. Unknown/New Class Tests (planned)

- A request with `execution_class` outside `KNOWN_EXECUTION_CLASSES` → `POL-006` DENY; every other policy's `applicable_policy_ids` membership is irrelevant to the outcome (DENY precedence, Section 22) — proves an unknown class cannot produce a *weaker* decision even though applicability resolution itself would (harmlessly) mark scoped rules non-applicable for it.
- A documented "future-class compatibility" test: adding a new value to `KNOWN_EXECUTION_CLASSES` without adding it to `POL-004.applicable_execution_classes` leaves `POL-004` non-applicable for it by default (fail-closed toward *narrower* POL-004 applicability, never silently toward wider) — consistent with PBPA-REQ-040's "never silently weaker" guarantee read in the direction that matters for a new class.

---

## 36. Missing Policy Tests (planned)

Construct `PolicyRegistry(rules=tuple(r for r in DEFAULT_POLICY_RULES if r.policy_id != "POL-004"))` → `PolicyRegistry.__init__` raises `ValueError` (Section 18), never silently treats `POL-004` as `NOT_APPLICABLE`-everywhere.

---

## 37. Duplicate Policy Tests (planned)

Construct `PolicyRegistry(rules=DEFAULT_POLICY_RULES + (MissingActiveTaskRule(),))` (a second `POL-001`) → `ValueError` (Section 18), deterministic rejection, no "first wins" / "last wins" / merge behavior.

---

## 38. Predicate Failure Tests (planned)

Since `applies_to()` in this plan is a single non-overridable base
implementation with no exception path (Section 20), this test category
is reserved rather than concretely written: inject a `PolicyRule`
subclass whose (future, hypothetical) `applies_to()` override raises,
and assert the registry converts it to a fail-closed outcome
(`_sanitize_result`-equivalent handling) rather than silently skipping
that rule — mirroring today's `evaluate()` exception handling
(`:653-658`), extended to `applies_to()` if a future phase ever adds
per-rule predicate overrides. Not exercisable against v1.0's actual
implementation (no override exists), but specified now so a future
predicate-overriding phase inherits the requirement rather than
discovering the gap.

---

## 39. Explainability Tests (planned)

- `applicable_policy_ids` + `non_applicable_policy_ids` partition
  `POLICY_IDS_CANONICAL` exactly (no overlap, no omission), for every
  `KNOWN_EXECUTION_CLASSES` value.
- Deterministic ordering (Section 23) — repeated evaluation of an
  identical request produces byte-identical tuples.
- `evaluated_policy_ids == applicable_policy_ids` (Section 16's
  redefinition, made executable).

---

## 40. Legacy Compatibility Tests — Required Updates (planned, concrete)

The ten-plus call sites inventoried in Section 2/finding in Section 9
must each be updated, not deleted — preserving `POL-004`'s
`HUMAN_REVIEW` behavior as a still-tested invariant, just against an
in-scope `execution_class`:

```python
# Before (tests HUMAN_REVIEW at execution_class="none" — no longer valid):
request = _valid_request(approval_present=False)

# After (tests HUMAN_REVIEW at an in-scope class — invariant preserved):
request = _valid_request(execution_class="shell", approval_present=False)
```

Plus one **new** assertion per updated file confirming the
previously-implicit case is now explicit: `execution_class="none"` +
`approval_present=False` → `ALLOW` (not `HUMAN_REVIEW`), with `POL-004`
in `non_applicable_policy_ids`. `test_broker_evaluated_policy_ids_always_all_twelve`
(Section 2) is renamed/rewritten to assert `evaluated_policy_ids`
depends on `execution_class` (12 for `execution_class="shell"`, 11 for
`"none"`/`"mutation"`), replacing the now-incorrect "always all twelve"
invariant its current name states.

---

## 41. Existing Broker Regression Suites

Required to pass, unmodified in logic (only the specific call sites in
Sections 2/40 change):

```
tests/test_permission_broker_foundation.py
tests/test_permission_broker_policy_composition_hardening.py
tests/test_permission_broker_policy_rule_framework.py
tests/test_permission_broker_verification_compatibility.py
tests/test_permission_broker_observation_hardening.py
tests/test_permission_broker_observation_verification.py
tests/test_permission_broker_command_path_prototype.py
tests/test_permission_broker_command_path_design.py
```

plus the four production consumer call sites (Section 3), exercised
indirectly via `pcae health` / `pcae check` / `pcae doctor task-memory`
/ `pcae push check` CLI-level tests already present in the suite.

---

## 42. Runtime Enforcement Regression

No `src/pcae/core/runtime_*.py` module changes (Section 1). Regression
scope: re-run `tests/test_runtime_*.py` (existing suite) unmodified and
confirm zero failures, proving semantic isolation — that this
implementation's changes to `permission_broker_foundation.py` do not
leak into runtime-capability reporting (`pcae runtime inspect` remains
`Observed`/`observe`/`unavailable`, Section 45/59).

---

## 43. Push Regression

`push.py` does not consume `PermissionBroker` today (Section 3/13).
Regression scope: re-run `tests/test_push*.py` (existing suite)
unmodified and confirm zero failures — proving this implementation
changes nothing about `pcae push`'s actual behavior, only (via
`observe()`, Section 3) a discarded, non-authoritative observation call
whose result was already provably unaffected (Section 3's table).

---

## 44. No-Execution Proof

This plan adds: one class attribute, one method (`applies_to`, pure
attribute/membership logic), one `__init__` validation (two set
operations), two dataclass fields, and two list-comprehension lines in
`_compose`. None of these import `subprocess`, `shell_gate`,
`backend_invocations`, `notifications`, or perform network I/O, file
I/O, or state mutation — consistent with, and independently
re-verifiable against, `test_broker_module_imports_only_stdlib`
(`tests/test_permission_broker_foundation.py:375`) and the module's own
AST-import-isolation tests (Section 1), which this plan's design was
checked against before being finalized here, not merely asserted to
satisfy after the fact.

---

## 45. B-1 Reproduction During Implementation

The four representative request shapes 148C.4 §13 exercised live
against the unmodified Foundation remain valid B-1 reproduction cases;
this plan requires the future implementation phase (148C.6) to re-run
them against the new code as a baseline-preservation check, not to
declare B-1 closed by any local synthetic result change. A future
correctly-classified `execution_class="mutation"` push-shaped request
would, under this plan's `POL-004` scoping, resolve `POL-004` as
`NOT_APPLICABLE` rather than `HUMAN_REVIEW` — but this is a Foundation-
internal fact about an unintegrated request shape, not a B-1 closure;
B-1 closure requires an actual PBPC-conformant `pcae push` integration
(does not exist, Section 13) followed by its own independent
verification (148C.7-equivalent) and a PBPC-001 v1.2 re-evaluation —
none of which this phase or its recommended successor (148C.6)
performs.

---

## 46. Explicit Boundary: 12-Hard-Block Coverage Not Solved Here

This plan solves: policy applicability inside the already-existing
Permission Broker Foundation (`POL-001..012`, currently 5 implemented +
7 stub/deferred). It does **not** solve: mapping `pcae push`'s current
hard-block conditions (enumerated in
`docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`'s
own compatibility table, e.g. `:281`) into broker-owned policy
judgments — that is PBPC-001's own, separate, still-unimplemented
concern (PBPC-001 §8/§18, reconfirmed open by 148C.4 §19). No push
policy (`POL-013+`) is added, proposed, or sketched by this plan beyond
the pre-existing `POL-013` used purely as a test fixture in
`test_registry_accepts_additional_rules_without_modifying_broker`
(Section 2), which is not a production policy.

---

## 47. Production Implementation File Budget

```
production: 1 file (src/pcae/core/permission_broker_foundation.py) —
            no new file; all additions are within the existing module,
            consistent with its own "single policy decision point"
            design principle (module docstring, Section 0)

tests:      8 existing files updated (Section 2), 0 new files expected
            — new coverage (Sections 32-39) is planned as additional
            test functions/parametrizations within the existing 8
            files, matching each file's current scope boundary (e.g.
            complete-POL-matrix tests belong in
            test_permission_broker_policy_rule_framework.py, which
            already tests per-rule behavior)

docs/status: this document, PROJECT_STATUS.md, CHANGELOG.md,
             tasks/DONE.md, .pcae/ finalization artifacts — ordinary
             phase bookkeeping, not implementation
```

No cross-module changes are required; the isolation this module has
maintained since Phase 108A (module docstring, Section 0) is preserved
by construction, not by additional discipline imposed by this plan.

---

## 48. Public API Assessment

See Section 26's table for the full per-change classification. Summary:
zero `BREAKING` changes; all changes are `ADDITIVE` or
`BACKWARD_COMPATIBLE` (one field, `evaluated_policy_ids`, carries a
documented behavioral/semantic change under PBPA-REQ-081 without
changing its type, name, or presence — called out explicitly rather
than folded into "additive").

---

## 49. Performance Assessment

`applies_to()` (Section 7) is an `O(1)` attribute read plus an `O(1)`
average-case `frozenset` membership test (or a single `is None` check
for the eleven universal rules) — no measurable complexity added to
`evaluate_all`'s existing `O(n)` loop over twelve rules. Registry
construction validation (Section 18) is `O(n)` over twelve rule IDs,
run once per `PolicyRegistry()` construction (today already happens
once per `PermissionBroker()` construction at each of the four
`observe()` call sites, Section 3 — no new per-request cost, since
`PolicyRegistry()` is constructed once per broker instantiation, not
per evaluation). No filesystem, network, or dynamic plugin-scan access
is introduced anywhere in this plan.

---

## 50. Failure Diagnostics Plan

| Condition | Surfaced as |
|---|---|
| Policy not applicable | `PolicyResult.applicable=False` in `results`; `policy_id` present in `PermissionBrokerDecision.non_applicable_policy_ids` — never a `DECISION_DENY`/`DECISION_HUMAN_REVIEW`, never conflated with either |
| Policy missing from registry | `PolicyRegistry.__init__` raises `ValueError` — a construction-time exception, never a decision value |
| Invalid classification (`execution_class`/`action_type`) | Existing `POL-006` DENY vocabulary, unchanged |
| Predicate failure | Reserved (Section 38) — not reachable in v1.0's scope |
| Registry invalid (duplicate/missing policy) | `ValueError` at construction, same as "missing" row above |

Applicability-system conditions are never falsely reported as
`DECISION_DENY` through the broker's existing decision vocabulary —
`NOT_APPLICABLE` stays exactly one layer below `PermissionBrokerDecision.decision`
(Section 17), matching PBPA-REQ-016's explicit prohibition on
collapsing it into any of the three existing values.

---

## 51. Security Invariants (all preserved by this plan)

- Caller cannot select policy membership — no `exclude_policies`-shaped parameter exists or is added (Section 7/Section 32, PBPA-REQ-022).
- Caller cannot obtain a weaker policy set by a false `execution_class` claim beyond the pre-existing, inherited limitation named explicitly in Section 9/32 (not deepened, not newly introduced).
- Unknown class fails conservative — `POL-006` DENY, unaffected by applicability (Section 8).
- Missing required policy fails closed — construction-time `ValueError` (Section 18).
- Predicate failure fails closed — reserved for future override points (Section 38); not reachable today.
- Non-applicable is never `ALLOW` — it is silence, one layer below the decision (Section 17/50).
- Applicable policy's meaning is unchanged — every `evaluate()` body untouched (Section 6/12).
- `approval_present` never controls applicability — applicability is resolved from `execution_class` alone, strictly before `approval_present` is read (Section 7's predicate reads only `execution_class`; Section 33's evidence-independence test makes this executable).
- `simulation_only` cannot serve as a downgrade switch — not an applicability input (Section 14).
- Applicability metadata is immutable/governed — frozen class attribute, policy-owned, registry-enforced (Section 24/6).

---

## 52. Implementation Acceptance Criteria

A future implementation (148C.6) is complete only if all twenty hold:

1. PBPA-001 v1.0 implemented per this plan's Sections 4-25 exactly (or a documented, independently-justified deviation).
2. All twelve `POL-001..012` applicability rows represented (Section 11).
3. Caller cannot select policy membership (Section 51).
4. `execution_class` validated via existing, unmodified `POL-006` (Section 8).
5. Action/class mismatches remain out of scope, not silently accepted as a false guarantee (Section 8).
6. Unknown class fails conservative (Section 8/35).
7. Future classes cannot silently bypass policies — default-narrower behavior for `POL-004`, unaffected universality for the other eleven (Section 35).
8. Missing policy fails closed (Section 18/36).
9. Duplicate policy fails closed (Section 18/37).
10. Predicate failure fails closed where reachable (Section 38, reserved).
11. Non-applicable remains distinct from `ALLOW` (Section 17/50).
12. Existing decision enum unchanged — three values only (Section 17).
13. Policy evaluation semantics unchanged — no `evaluate()` body edited (Section 6/12).
14. Decision aggregation semantics unchanged — `_compose`'s precedence logic untouched (Section 22).
15. `POL-004` semantics unchanged when applicable (Section 12/33).
16. Applicability explanation deterministic (Section 23/39).
17. Legacy behavior remains safe — all four real consumers re-verified byte-identical (Section 3/41).
18. No execution capability introduced (Section 44).
19. No `pcae push` integration introduced (Section 13/43).
20. B-1 remains formally open pending later PBPC re-evaluation (Section 45).

---

## 53. Independent Verification Requirements (for 148C.7)

The phase following implementation must not trust 148C.6's own tests
alone. Required:

- Source-level inspection of the actual diff against this plan (Sections 1-26), not just "tests pass."
- Direct public API tests constructed independently, not copied from 148C.6's own suite.
- Malicious classification inputs (Section 32) exercised against the real implementation.
- Malformed registries (Section 18/36/37) exercised directly.
- Policy substitution / registry-injection attempts (Section 32).
- `execution_class` spoofing attempts, within the documented inherited-limitation boundary (Section 9/32) — confirming the limitation is documented, not silently expanded.
- `simulation_only` spoofing attempts (Section 14) — confirming no downgrade path exists.
- Complete `POL-001..012` matrix re-derived independently (Section 34), not trusted from 148C.6's table.
- Deterministic output re-verified (Section 23/39).
- Backward compatibility re-verified against Section 3's four real consumers, live.
- Current B-1 reproduction (148C.4 §13's four request shapes) re-run and compared against pre-implementation baseline (Section 45).

---

## 54. Expected Implementation Sequence

If this plan finds no Blocking issue (Section 55: it does not), the
recommended next phase is:

**148C.6 — Permission Broker Foundation Policy Applicability
Implementation**, implementing exactly Sections 4-25 and Sections 27-31
of this plan (the staged, additive change to
`permission_broker_foundation.py`), followed by:

**148C.7 — Permission Broker Foundation Policy Applicability
Independent Implementation Verification** (Section 53), before any
PBPC/B-1 re-evaluation is authorized.

---

## 55. Planning Findings

| ID | Finding | Classification |
|---|---|---|
| P-1 | Four test files, ~10 call sites, assert `HUMAN_REVIEW` for `approval_present=False` requests at the default `execution_class="none"` — outside `POL-004`'s frozen applicable set. These call sites' expected decision changes from `HUMAN_REVIEW` to `ALLOW` once applicability filtering activates. Concrete remediation specified (Section 40). | **NON-BLOCKING** — mechanical, fully specified, planned as part of Stage 4 (Section 27), not a defect in the architecture |
| P-2 | `test_broker_evaluated_policy_ids_always_all_twelve` (and two `len(...) == 12`/`== 13` assertions) directly names and asserts an invariant PBPA-REQ-081 deliberately redefines. Concrete remediation specified (Section 40). | **NON-BLOCKING** — same category as P-1, called out separately because it is a *named* invariant, not just a default-value incidental |
| P-3 | `evaluated_policy_ids`'s semantic redefinition (Section 16/26) is a real behavioral change to a public field's value (not just its documentation), even though its type/name/presence are unchanged — this plan does not classify it as purely `ADDITIVE` to avoid understating it (Section 48). | **OBSERVATION** — accurately classified, not a defect; recorded so 148C.6/148C.7 do not re-litigate whether it "counts" as additive |
| P-4 | `execution_class` authenticity remains caller-supplied with no independent broker-side re-derivation, both before and after this plan — an inherited limitation, not introduced or worsened by this implementation (Section 9/32). | **DEFERRED** — same boundary PBPA-001 §9/148C.4 already accepted as this contract layer's threat-model edge; not this plan's to close |
| P-5 | No per-`execution_class` required-policy-set invariant is adopted (Section 21, matching PBPA-REQ-072's own non-adoption) — the empty-applicable-set case remains unreached-but-unguarded-by-a-dedicated-check beyond `_compose`'s pre-existing empty-`results` DENY branch. | **DEFERRED** — matches 148C.4 Finding V-2's own "recommend a future amendment" disposition; not blocking this plan or its implementation |

**No Blocking planning defect was found.** Specifically checked and
ruled out: PBPA does not require a broad incompatible public API break
(Section 26 — all changes additive or documented-semantic); a safe
migration path exists (Section 29-31); `execution_class` can be
validated to the same (inherited, documented) degree as today, no
worse (Section 8/9); applicability is representable without
duplicating authority (Section 5-6); required policy metadata can be
added safely (Section 18-19); legacy consumers do not silently weaken
(Section 3, exhaustively enumerated — zero of four real consumers are
affected).

---

## 56. Deliverable Cross-Reference

This document is the required deliverable (Section 56 of the
originating scope). Cross-reference of required contents to sections
above: objective (§0/Primary Objective), source inventory (§1-3),
production change surface (§1), consumer inventory (§3), test change
surface (§2), data-model plan (§4), metadata representation (§5),
predicate architecture (§7), classification validation (§8),
classification ownership (§9), applicability API (§15), POL-001..012
metadata plan (§11), POL-004 plan (§12), simulation plan (§14),
required-policy validation (§18), registry validation (§19), failure
handling (§20/50), backward compatibility (§10/26), explainability
(§16/39), determinism (§23/39), API compatibility (§26/48), migration
(§29), safe intermediate states (§30), rollback (§31), implementation
stages (§27), test matrix (§32-40), security invariants (§51), B-1
handling (§13/45), 12-hard-block boundary (§46), acceptance criteria
(§52), independent verification requirements (§53), findings (§55),
recommended next phase (§54).

---

## 57. Production Source Boundary

```bash
git diff --name-only <148C.5-baseline>..HEAD -- src/pcae/
```

Expected and confirmed empty at finalization (Final Report, below). No
test source is modified by this phase either — Sections 2/40's
specific test updates are *planned*, described in exact diff form, but
not applied; they are 148C.6's work.

---

## 58. Validation Run This Phase

```
pcae health                    -> healthy
pcae check                     -> passed
pcae status coherence          -> coherent
pcae doctor task-memory        -> clean
pcae push check                -> nothing_to_push
pcae runtime inspect           -> Observed / observe / unavailable
pcae notify status              -> Telegram configured, enabled, ready
pcae phase-report show --latest -> confirmed 148C.5 as Planned/next phase
pcae phase-report reconcile --phase-id 148C.4 -> read-only, no mutation
```

All read-only, run at phase start (transcript, this session). No
`pytest` re-run of the full broker suite was required beyond what
Section 1-2's `grep`/direct-source inspection already established,
since this phase modifies no test source — Fast Green is run at
finalization (Section 59/Final Report) to confirm the *existing* suite
remains green after this phase's own (docs-only) diff, not to validate
any planned-but-unwritten test change.

---

## 59. Findings Recorded, Recommended Next Phase

**Recommended next phase: 148C.6 — Permission Broker Foundation Policy
Applicability Implementation** (Section 54), implementing exactly
Sections 4-25/27-31 of this plan. **148D remains NOT recommended**
(Finding B-1 open, Section 45). No implementation, no `src/pcae/**`
change, no B-1 closure, and no runtime-capability change occurred in
this phase — see Final Report below for the full confirmation list.
