# Phase 149O.20L.7O.3W.1R — Runtime Invocation Authority + PB Dispatch Foundation Blocking Repair

## 1. Objective

Close exactly the seven BLOCKING findings established by 3W.1, without
changing frozen authority/dispatch contracts, enabling execution, or repairing
separately carried historical and test-infrastructure debt.

## 2. Baseline

- Repair baseline: `abd3f5b4fb1ab6fc763fa2e6172518fa37c513c2`
- Defective functional baseline for attribution:
  `289bd75d2d9843e95f336bcba2eed35bc414adb7`
- Public release: v0.4.3 at
  `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged.
- Entry runtime: `Observed` / `observe` / `unavailable`.

## 3. 3W.1 verdict

`AUTHORITY/PB FOUNDATION: NOT VERIFIED`; seven BLOCKING findings; zero
unexplained attributable functional regressions; no production repair in
3W.1.

## 4. Seven blocker recovery

Primary evidence contained exactly seven BLOCKING findings. Matrix A preserves
their exact verification wording.

### Matrix A — Seven blocker inventory

| ID | Exact finding | File/symbol | Contract | Root cause | Pre-repair reproduction |
|---|---|---|---|---|---|
| B1 | Forgeable ValidatedAuthorityProjection and public raw approval_present=True; runtime_dispatch_context is optional even for runtime_dispatch. | `runtime_authority.ValidatedAuthorityProjection`; `runtime_dispatch_permission.project_human_authority_binding`; `permission_broker_foundation.PermissionBrokerRequest`, generic builder and `PermissionBroker.evaluate` | RIHAC §16; PBRD §§5, 7, 15, 22 | Structural objects were mistaken for trusted producer evidence; runtime action shape was not action-specifically enforced. | REPRODUCED: a directly constructed projection and raw PB request both produced simulated `ALLOW`. |
| B2 | Approval-store symlink/hardlink escape and external overwrite; create-only is not secure against adversarial precreated paths. | `RuntimeInvocationApprovalStore.create/load/exists` | RIHAC §§15, 18; RIASC §§11-12 | `Path.exists`/`write_text`/`replace` followed adversarial links and reused a predictable pre-existing container. | REPRODUCED: approval-directory symlink escaped; pre-created hardlink target was overwritten. |
| B3 | Incomplete RIASC type/value enforcement and duplicate-key acceptance. | `validate_riasc_schema_shape`; `RuntimeInvocationApprovalStore.load` | RIASC §§2-7, 10-11 | Several nested fields had only closed-shape checks, and ordinary `json.loads` accepted last duplicate key. | REPRODUCED: invalid `phase_id` type and duplicate `approval_id` were accepted. |
| B4 | Approval-preview provenance is not recomputed/bound. | `validate_approval` step 4 | RIHAC §§12, 16; RIASC §§7, 11 | Record digest authenticated the presented preview digest but validation never derived the expected digest from reviewed facts. | REPRODUCED: tampered preview digest plus recomputed record digest validated. |
| B5 | Descriptor version and filesystem/approval scope are not fully cross-bound. | `InvocationRequestContext`; `validate_approval` step 8; runtime dispatch trusted projection | RIHAC §§3, 11, 16; RIASC §11; PBRD §§4-5 | Live context carried only a subset of scope/adapter facts and PB projection did not prove the validated subject/scope matched request facts. | REPRODUCED: descriptor-version mismatch validated and broader filesystem scope reached PB with approval present. |
| B6 | Timestamp freshness/expiry uses lexical, not instant, comparison. | `create_runtime_invocation_approval`; `validate_approval` step 10 | RIHAC §§14, 16; RIASC §11 | RFC3339 strings with optional fractional seconds were compared lexically. | REPRODUCED: chronologically expired fractional time validated and earlier expiry could be created. |
| B7 | Idempotency derivation omits identity-critical facts and has no durable cross-process conflict guarantee. | `RuntimeDispatchRequestConstructionInput`; canonical projection; `new_runtime_dispatch_identity`; `RuntimeDispatchIdentityTracker` | PBRD §§6, 10, 15; RDGO §10a; RPAC-REQ-064–068 | Canonical projection was incomplete, excluded invocation identity, and collision state existed only in process memory. | REPRODUCED: seven contract facts absent, distinct invocations shared a key, and a new tracker forgot prior state. |

## 5. Seven blocker reproduction

All seven were independently reproduced with fresh, smallest-path local
reproducers against the clean repair baseline before any production edit:
`B1 REPRODUCED`; `B2 REPRODUCED`; `B3 REPRODUCED`; `B4 REPRODUCED`; `B5
REPRODUCED`; `B6 REPRODUCED`; `B7 REPRODUCED`.

## 6. Blocker-family classification

- Approval trust/PB shortcut: B1.
- Canonical-store confinement/corruption: B2 and duplicate-key portion of B3.
- Schema/provenance/binding/freshness: B3-B6.
- Replay/idempotency: B7.

## 7. Root-cause graph

```text
structural object accepted as trusted evidence -> B1 -> validator seal + trusted PB factory/evaluator
path-based replace/follow semantics -> B2 -> no-follow, exclusive container/file publication
partial schema/parser enforcement -> B3 -> exact nested types + duplicate-key rejection
missing derived cross-field checks -> B4, B5 -> recomputed preview + exact full binding
lexical time ordering -> B6 -> parsed UTC-instant ordering
incomplete/process-local identity -> B7 -> complete projection + durable append-only gate-2 registry
```

## 8. Contract mapping

B1 maps to RIHAC-001 §16 step 12 and PBRD-001 §§5/7/15/22. B2 maps to
RIHAC-001 §§15/18 and RIASC-001 §12. B3 maps to RIASC-001 §§2-7/10-11.
B4 maps to RIHAC-001 §§12/16 and RIASC-001 §§7/11. B5 maps to RIHAC-001
§§3/11/16, RIASC-001 §11, and PBRD-001 §§4-5. B6 maps to RIHAC-001
§§14/16 and RIASC-001 §11. B7 maps to PBRD-001 §§6/10/15, RDGO-001
§10a, and RPAC-REQ-064–068.

## 9. Contract-sufficiency verdict

**YES for all seven.** Every defect is repairable entirely within already
frozen normative semantics. Contract change required: **NO**.

## 10. Repair scope

### Matrix B — Repair mapping

| Finding | Repair | Files changed | Tests | Contract change? |
|---|---|---|---|---|
| B1 | Seal validator-issued evidence; trusted runtime PB factory; action-specific PB fail-closed validation. | `runtime_authority.py`, `runtime_dispatch_permission.py`, `permission_broker_foundation.py` | verifier plus 3W.1R closure suite | NO |
| B2 | Validate every store component; exclusive approval directory; directory-relative `O_NOFOLLOW` and atomic link publication; reject hardlinked loads. | `runtime_invocation_approval_store.py` | store, verifier, 3W.1R closure suite | NO |
| B3 | Complete nested type/value checks and reject duplicate JSON keys. | `runtime_authority.py`, `runtime_invocation_approval_store.py` | authority/store/verifier/closure | NO |
| B4 | Recompute exact preview digest during validation. | `runtime_authority.py` | verifier/closure | NO |
| B5 | Carry exact full approval scope/adapter binding and verify PB subject-scope digest. | `runtime_authority.py`, `runtime_dispatch_permission.py` | authority/dispatch/verifier/closure | NO |
| B6 | Parse frozen UTC profile and compare aware instants. | `runtime_authority.py` | authority/verifier/closure | NO |
| B7 | Bind all identity-critical facts and invocation identity; durable create-exclusive cross-process registry. | `runtime_dispatch_permission.py` | dispatch/idempotency/verifier/closure | NO |

## 11. Authority model/store repairs

The authority model now emits validator-sealed evidence only after all ordered
checks. The canonical store creates a fresh approval container exclusively and
publishes one immutable file using directory-relative no-follow operations.

## 12. Provenance repairs

Validation recomputes the preview digest from the exact subject, approval
scope, and expiry and rejects any mismatch. Human identity remains distinct
from producer component and runtime target.

## 13. Subject/binding repairs

The five-member subject remains exact. Repository, task, invocation, target,
prompt, governance, full approval scope, and complete adapter binding must all
match. No best-effort matching exists.

## 14. Freshness repairs

All seven frozen freshness rules remain. Expiry and creation ordering now use
chronological UTC instants; no eighth freshness rule was added.

## 15. Path/symlink repairs

Traversal/absolute/separator injection remains impossible by approval-ID
grammar. Store root components, approval directories, and final files reject
symlinks/non-directories; pre-existing containers conflict; hardlinked final
files are untrusted. Platform link variants are covered by closure tests.

## 16. Corruption/tamper repairs

Malformed UTF-8/JSON, duplicate keys, schema errors, partial containers,
identity mismatch, symlink/hardlink artifacts, and non-regular files fail
closed. No invalid-store-to-caller-hint fallback exists.

## 17. Trusted PB projection repairs

Only a validator-issued sealed projection can yield a non-empty human authority
binding. The generic PB builder refuses `runtime_dispatch`; direct unsealed PB
objects are denied before policy evaluation. Caller `approval_present=True` is
not validated authority.

## 18. Option-B request repairs

Runtime dispatch requires the trusted nested context. PB validates all fourteen
facts, closed nested types, outer task/phase/capability binding, action/class,
transport/network constants, and authority presence/binding consistency.
Non-runtime actions remain context-free and backward compatible.

## 19. attempt/idempotency repairs

`invocation_id`, `attempt_id`, and `idempotency_key` remain distinct. The key
binds invocation identity, repository fingerprint/base commit, task and task
contract, lifecycle, prompt, target/config/descriptor, capability, full
approval scope/effects/network, and resource budget. A durable local gate-2
registry detects same-invocation changed-content and attempt/key conflicts
across processes. It is not an exactly-once claim or gate-9 record.

## 20. POL-004

Validated trusted approval satisfies `MissingHumanApprovalRule` itself.
Missing/forged/unvalidated evidence remains missing. Other HUMAN_REVIEW policy
rules remain independent.

## 21. POL-005

`ExecutionDisabledRule` is source-identical to baseline; AST source SHA-256 is
`0d5232c207d72d358b18a3e1af106b7409a19a885cbe76c4a6dcce9233ed2252`.
The strongest valid non-simulation request remains final `DENY`, caused by
`POL-005`, reason `execution_boundary_unavailable`.

## 22. One-shot staging

Approval consumption remains **NO / NOT IMPLEMENTED**. Creation, load,
validation, PB construction/evaluation, and POL-005 DENY do not create a
`dispatch_attempted` marker. The B7 gate-2 identity registry is not approval
consumption.

## 23. No RE/Shell/effect proof

### Matrix E — Side effects

| Effect | Expected | Observed | Evidence |
|---|---:|---:|---|
| runtime subprocess | 0 | 0 | import/source audit and tripwire tests |
| network/provider | 0 | 0 | import/source audit and socket tripwire |
| credential read | 0 | 0 | environment tripwire |
| external runtime | 0 | 0 | no adapter/RE call path |
| background work | 0 | 0 | thread-start tripwire |
| runtime source mutation | 0 | 0 | filesystem snapshot test; only governed evidence stores change |

Production Runtime Enforcement calls: **0**. Shell Gate calls: **0**.

## 24. Dry regression

The production dry path remains `adapter_invocation`,
`simulation_only=true`; it was not migrated to `runtime_dispatch`.

## 25. Existing PB regressions

PB foundation/policy, rollback, push, publication (excluding unavailable build
tool nodes), mutation, and dry/bootstrap representative suites pass.

## 26. Persistence regressions

Positive create/load/restart, duplicate conflicting write, corruption,
copied/identity-mismatched artifact, stale approval, symlink/hardlink, and
cross-process identity cases are covered. Canonical approval create remains
strict create-only; a duplicate identical approval write is a hard conflict
under frozen one-shot semantics.

## 27. Seven fresh closure tests

| Finding | Pre-repair reproducer | Post-repair result | Test |
|---|---|---|---|
| B1 | forged projection/raw PB boolean | rejected/denied | `test_finding_1_forged_projection_and_raw_pb_shortcuts_fail_closed` |
| B2 | directory symlink/tmp symlink/tmp hardlink | fail closed; sentinel unchanged | `test_finding_2_store_link_attacks_cannot_escape_or_overwrite` |
| B3 | invalid nested values/duplicate JSON | rejected | `test_finding_3_*` |
| B4 | forged preview digest with valid record digest | rejected | `test_finding_4_preview_provenance_is_recomputed_and_bound` |
| B5 | descriptor drift/broader filesystem scope | rejected | `test_finding_5_descriptor_and_full_scope_are_cross_bound` |
| B6 | fractional lexical-order exploit | expired/creation rejected | `test_finding_6_freshness_uses_chronological_instants` |
| B7 | omitted facts/shared key/process restart | complete/different/durable conflict | `test_finding_7_*` |

## 28. Negative variants

Bounded variants cover multiple invalid nested field types, directory/file
symlinks, hardlinks, partial containers, descriptor and filesystem scope drift,
raw and structural approval shortcuts, fractional ordering in creation and
validation, distinct invocations, changed-content retry, and post-mint attempt
tampering.

## 29. Contract drift

`git diff <repair_baseline>..HEAD -- docs/contracts` is empty. Normative
contract drift: **NONE**.

## 30. Production diff

Production changes are confined to the four Matrix-B files. Every changed
production line maps to B1-B7; no opportunistic refactor or unrelated source
change is present.

## 31. Regression attribution

Fixed-SHA partitioned baseline/candidate results will be frozen after the
functional repair commit. No monolithic full-suite claim will be made.

### Matrix F — Regression attribution

| Partition/failure | 3W defective baseline | repaired candidate | Classification | Attributable? |
|---|---:|---:|---|---|
| Focused authority/PB implementation + verifier/repair | baseline expected unsafe verification assertions | 289 passed | intended repair | No |
| Representative PB/rollback/push/publication/dry, excluding slow packaging | pending fixed-SHA | 880 passed / 34 deselected working-tree precheck | pending | pending |
| Slow publication packaging (`python -m build`) | tool unavailable | tool unavailable | ENVIRONMENT_OR_TEST_INFRASTRUCTURE | No |

## 32. Test infrastructure debt

Carry separately: order-dependent Shell-Gate audit test hang/debt. It is not
repaired or reopened. Local publication packaging nodes also lack the optional
`build` module and are an environment exclusion.

## 33. Historical self-check debt

Carry separately: fixed-phase historical source/count checks identified by
3W.1. No bulk historical-test rewrite was performed.

## 34. Two older MUST-FIX findings

Recovered verbatim from 3S.2.1: (1) malformed adapter result can escape as an
uncaught exception; (2) the older `RuntimeInvocationStore` derives a path from
an unsanitized `invocation_id`. Neither becomes reachable through this repair:
the new foundation calls no adapter/Runtime Enforcement, and its approval and
identity stores validate generated identifiers independently. Neither was
opportunistically repaired.

## 35. Runtime inspect limitation

`TRUTHFUL_WITH_LIMITATION`: no real adapter is registered/available. Runtime
remains `Observed` / `observe` / `unavailable`.

## 36. New findings

Final counts pending fixed-SHA attribution. No new implementation blocker has
been observed in focused verification.

## 37. Seven-finding final disposition

### Matrix G — Final blocker status

| Finding | Status | Closure evidence |
|---|---|---|
| B1 | CLOSED | sealed validator projection, trusted factory, PB structural DENY, closure test |
| B2 | CLOSED | no-follow/exclusive store and link-attack closure variants |
| B3 | CLOSED | complete nested checks and duplicate-key rejection |
| B4 | CLOSED | recomputed preview binding test |
| B5 | CLOSED | exact adapter/full-scope validation and projection/request digest binding |
| B6 | CLOSED | aware-instant creation/expiry tests |
| B7 | CLOSED | complete projection, invocation-bound keys, durable cross-process conflict tests |

## 38. Final verdict

Pending final fixed-SHA attribution and governance closure. The repair itself
has 7/7 closure evidence and preserves hard-deny/runtime-unavailable invariants.

## 39. Recommended next phase

**149O.20L.7O.3W.1R.1 — Independent Verification of Runtime Invocation
Authority + PB Dispatch Foundation Blocking Repair**.

## 40. Human decision required

**YES.** This repair phase does not self-certify and must stop after governance
closure. Do not begin Runtime Enforcement work automatically.

### Matrix C — Authority security

| Attack | Pre-repair behavior | Required | Post-repair |
|---|---|---|---|
| forged projection | approval present / simulated ALLOW | only validator output trusted | construction rejected |
| raw `approval_present=True` / missing context | simulated ALLOW | Option-B context mandatory/trusted | generic builder rejects; direct PB object DENY |
| link/precreated-store attacks | escape/overwrite | canonical create-only confinement | fail closed, external sentinel unchanged |
| schema/duplicate-key ambiguity | accepted | closed exact schema | rejected |
| preview/descriptor/scope/time replay | validated | exact provenance/binding/freshness | rejected |
| identity replay across process | forgotten/shared | durable deterministic collision | retry stable; changed-content conflict |

### Matrix D — PB trust boundary

| Concern | Trusted source | Validation | Fail-closed behavior |
|---|---|---|---|
| human authority | RIHAC ordered validator | validator seal + exact subject/scope evidence digest | absent/forged is missing or construction error |
| identity triple | PCAE gate-2 mint + durable registry | generated IDs, complete canonical key, registration digest | changed/unregistered identity rejected |
| Option-B facts | trusted runtime-dispatch builder | 14 facts plus outer bindings/constants | malformed/missing/unsealed request DENY |
| policy | fresh PB evaluation | POL-004 independent; POL-005 unchanged | any real request DENY |
