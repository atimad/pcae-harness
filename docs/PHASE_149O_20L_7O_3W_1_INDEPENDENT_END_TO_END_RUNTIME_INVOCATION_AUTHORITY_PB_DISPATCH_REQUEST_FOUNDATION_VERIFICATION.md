# Phase 149O.20L.7O.3W.1 — Independent End-to-End Runtime Invocation Authority + PB Dispatch Request Foundation Verification

## 1. Objective

Independently verify the Phase 3W production foundation against RIHAC-001
v1.0, RIASC-001 v1.0, PBRD-001 v1.1, RDGO-001 v2.0, and RPAC-001 without
repairing production code or enabling execution.

## 2. Independence

The verifier reconstructed contracts and source directly and added
`tests/test_runtime_authority_pb_verification_3w1.py`. That module does not
import Phase 3W's `_rdw3w_helpers`. Phase 3W's 190 tests were rerun only as
implementation evidence, not treated as independent proof.

## 3. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| Verification-entry SHA | `0106c3c2d6f0ee740b7ffca97d4ffd79f6494022` |
| Fixed 3W baseline | `daebfdbb2d8664518c51e904b64aad555195d626` |
| Fixed 3W candidate | `289bd75d2d9843e95f336bcba2eed35bc414adb7` |
| Release | `v0.4.3` at `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged |
| Runtime | `Observed` / `observe` / `unavailable` |
| Phase status | Complete; **NOT VERIFIED** |
| Completeness | Complete independent verification; no production repair |

## 4. 3W source delta

The fixed delta contains 18 files, 4,173 insertions, and 24 deletions. New
production files are `runtime_authority.py` (890 lines),
`runtime_dispatch_permission.py` (272), and
`runtime_invocation_approval_store.py` (164). Additive edits affect
`permission_broker_foundation.py` (+81) and `runtime_invocation.py` (+17).
Eight test files plus `_rdw3w_helpers.py` add 190 tests. No contract changed.

## 5. Production caller graph

AST inspection found zero non-test callers of approval creation, authority
validation, the approval store, or the new dispatch-request builder.
`RuntimeDispatchRequestFacts`, `ValidatedAuthorityProjection`, and the
projection adapter are referenced only inside the new foundation. Existing
generic PB constructors retain seven production callers. The Phase 3W path is
therefore foundation-only and not a real dispatch entrypoint.

## 6. Contract-to-code mapping

RIHAC/RIASC map to `runtime_authority.py` and the approval store; PBRD maps
to `runtime_dispatch_permission.py` plus the additive PB foundation fields;
RDGO gates 1–6 are represented only as foundations and gates 7–11 remain
unimplemented; RPAC remains the boundary contract. Mapping exists, but the
authority and PB trust boundaries do not fully enforce the contracts.

## 7. RIASC schema

The model has exactly 16 top-level fields and rejects missing/unknown fields,
but the hand-written validator does not enforce all normative types and
formats and accepts duplicate JSON keys through last-key-wins parsing.

| RIASC field | Source | Production enforcement | Adversarial test | Verdict |
|---|---|---|---|---|
| `schema_id` | contract const | exact const | mutation | PASS |
| `schema_version` | contract const | exact const | mutation | PASS |
| `contract_version` | contract const | exact const | mutation | PASS |
| `record_type` | contract const | exact const | mutation | PASS |
| `approval_id` | coordinator | ID pattern + filename match | mismatch/duplicate-key | FAIL |
| `record_digest` | canonical record | digest recomputation | tamper | PASS |
| `created_at` | trusted clock | string/lexical comparison | fractional timestamp | FAIL |
| `expires_at` | trusted policy | string/lexical comparison | fractional timestamp | FAIL |
| `subject` | coordinator | closed 5-field object | all five swaps | PASS |
| `governance_context` | lifecycle | closed shape; incomplete value typing | wrong `phase_id` type | FAIL |
| `approval_scope` | request/scope owner | closed shape; incomplete value typing | bad capability/ref | FAIL |
| `adapter_binding` | registry/config | closed shape; incomplete value typing | bad IDs/version | FAIL |
| `freshness_snapshot` | live context | closed shape; incomplete policy typing | bad policy version | FAIL |
| `provenance` | approval coordinator | consts, but incomplete identity typing | bad approver ID | FAIL |
| `prompt_hash_profile` | contract const | exact const | mutation | PASS |
| `attempt_limit` | contract const | exact value 1 | mutation | PASS |

**RIASC-001 production enforcement: NOT VERIFIED.**

## 8. Five-member subject

The closed subject is exactly `(invocation_id, runtime_target_id,
prompt_hash, repository_identity, task_id)`. Independent attacks changing
each member fail validation. **VERIFIED for those five bindings.**

## 9. Authority shortcut attacks

Unknown raw fields such as `approved`, `authorized`, `permission`,
`pb_allow`, and `execution_allowed` fail schema validation. However, the
generic PB constructor publicly accepts `approval_present=True`; this is a
separate, blocking shortcut around authority validation.

## 10. Approval provenance

Producer/mechanism constants and record digest are checked. The validator
does not validate the preview digest against a reconstructed preview and
does not completely type-check `approver_id`. Provenance is not trustworthy
enough to authorize dispatch.

## 11. Approval store

The intended location is
`.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json`. Normal
create/load, malformed JSON, truncation, schema failure, and filename/record
identity mismatch fail as expected.

## 12. Create-only/atomicity

Sequential duplicate creation fails. The temp-then-replace implementation is
not securely create-only under adversarial precreated path objects and offers
no durable cross-process exclusivity proof.

## 13. Path confinement

Traversal-like approval IDs are rejected before path construction. That
lexical protection does not prevent traversal through filesystem links
already placed beneath the nominal canonical root.

## 14. Symlink/hardlink analysis

A precreated approval-directory symlink redirects `approval.json` outside
the store. A precreated `approval.json.tmp` symlink or hardlink permits an
external file overwrite. **BLOCKING path-confinement failure.**

## 15. Corruption handling

Malformed, truncated, wrong-shape, and lookup-ID-mismatched records fail.
Conflicting duplicate JSON keys are not rejected; the final duplicate wins.
This is a fail-open canonical-decoding defect.

## 16. Repository replay

An approval copied into a different repository identity fails. **PASS.**

## 17. Task swap

An approval created for task A fails under task B. **PASS.**

## 18. Target swap

An approval created for one exact target fails for another. **PASS.**

## 19. Prompt swap

An approval created for one semantic prompt hash fails after prompt change.
**PASS.**

## 20. Seven freshness rules

HEAD, task-contract digest, task state, prompt, target, adapter configuration,
and expiry drift all block. Policy drift produces the contract-defined
fresh-PB requirement rather than silently authorizing. The rule set exists,
but timestamp parsing and other cross-bindings remain defective.

## 21. Expiry/revocation

Revocation remains explicitly outside v1. Expiry uses lexical string
comparison rather than parsed instants: `12:30:00.9Z` can be treated as
earlier than `12:30:00Z`, and creation can accept a chronologically earlier
expiry across fractional formatting. **BLOCKING.**

## 22. One-shot staging

The durable gate-9 consumption record is deliberately not implemented.
Validation consults an injected state lookup and blocks consumed/uncertain
states, but cannot itself provide one-shot dispatch semantics.

## 23. Premature consumption

Repeated validation and a later POL-005 denial do not consume the approval.
This correctly avoids premature consumption; actual atomic pre-dispatch
consumption remains a later gate.

## 24. Tampering

Record-digest tampering fails. A changed approval-preview digest passes if
the attacker recomputes the record digest; descriptor-version and filesystem
scope substitutions can also escape the intended cross-binding. **FAIL.**

## 25. Restart persistence

Normal store reload in a fresh process preserves approval identity and
record digest. **PASS**, subject to the store-security blockers above.

## 26. attempt_id

`new_attempt_id()` is reused, generates `att-<32-hex>`, and produces a fresh
value per attempt. It is not caller supplied. **VERIFIED.**

## 27. idempotency_key

Keys are deterministic SHA-256 values, but distinct newly minted invocation
IDs for otherwise identical inputs receive the same key and the collision
tracker is process-local. **NOT VERIFIED.**

## 28. Idempotency derivation

The projection omits contract-bound base commit/task-contract identity,
process profile, complete approval scope/effect/network facts, and related
frozen identity-critical inputs. This violates the complete logical-request
binding requirement. **BLOCKING.**

## 29. Cross-process determinism

The same encoded input produces the same key in a clean process. **PASS for
determinism only**, not for completeness or durable conflict prevention.

## 30. Replay/conflict scenarios

The in-memory tracker rejects same-attempt/different-content and
same-key/different-invocation conflicts within one process. It supplies no
cross-process or restart guarantee and cannot repair the incomplete digest.

## 31. PBRD Option-B architecture

The optional nested `runtime_dispatch_context` field is additive and leaves
existing action envelopes compatible. For `runtime_dispatch`, however, the
generic constructor permits the context to be absent. **NOT VERIFIED.**

## 32. Fourteen facts

| Fact | Trusted source | Production representation | Test | Verdict |
|---|---|---|---|---|
| `invocation_id` | coordinator | direct field | generated/bound | PASS |
| `attempt_id` | coordinator | direct field | generated/unique | PASS |
| `idempotency_key` | coordinator | direct field | deterministic/completeness | FAIL |
| `repository_identity` | repo resolver | direct field | repo swap | PASS |
| `task_id` | lifecycle | direct field | task swap | PASS |
| `lifecycle_context` | lifecycle | closed nested object | phase/session | PARTIAL |
| `runtime_target_id` | selector | direct field | target swap | PASS |
| `adapter_descriptor_binding` | registry/config | closed nested object | descriptor substitution | FAIL |
| `prompt_hash` | prompt builder | direct field | prompt swap | PASS |
| `requested_capability` | governed request | direct field | type/swap | PARTIAL |
| `transport_type` | contract | const `local_cli` | const check | PASS |
| `network_requirement` | descriptor/preflight | const false | const check | PASS |
| `filesystem_scope_ref` | scope owner | closed nested object | broader-scope substitution | FAIL |
| `human_authority_binding` | RIHAC validator | closed nested object | forged projection | FAIL |

The dataclass has exactly fourteen facts, but the complete trusted-source and
cross-binding semantics are not enforced. **PBRD-001 Option-B: NOT VERIFIED.**

## 33. Existing-action isolation

Existing action constructors leave `runtime_dispatch_context=None`.
Representative push, rollback, publication, mutation-permission, and PB
consumer suites passed (162 tests), plus 197 dry/bootstrap/PB regressions.

## 34. runtime_dispatch action

`runtime_dispatch` is registered and no longer triggers POL-006 as unknown.
The generic public constructor can nevertheless create it without its
mandatory context. **Action exists; contract enforcement fails.**

## 35. execution_class

The new action uses the existing `adapter` class as required. **PASS.**

## 36. Trusted approval projection

`ValidatedAuthorityProjection` is a public frozen dataclass, but possession
of its type is treated as proof of successful validation. There is no
unforgeable validator-owned construction boundary. **NOT TRUSTED.**

## 37. Forged projection attack

A caller can instantiate a forged projection, build a context that sets
`approval_present=True`, and obtain a simulated PB ALLOW with POL-004 not
triggered. Separately, the generic PB builder accepts a raw true boolean.
**BLOCKING.**

## 38. POL-004

With `approval_present=False`, POL-004 is applicable and produces
HUMAN_REVIEW for the adapter class. With true it does not trigger. The rule
is specific and unchanged, but both true-setting paths are forgeable.

## 39. HUMAN_REVIEW

HUMAN_REVIEW remains non-authorizing and loses to DENY. **PASS.**

## 40. PB precedence

Deterministic precedence remains `DENY > HUMAN_REVIEW > ALLOW`. **PASS.**

## 41. POL-005 source proof

`ExecutionDisabledRule` has identical source at both fixed SHAs; exact class
source SHA-256 is
`0d5232c207d72d358b18a3e1af106b7409a19a885cbe76c4a6dcce9233ed2252`.

## 42. POL-005 hard-deny E2E

An otherwise strongest valid real (`simulation_only=False`) authority/PB
request still ends in hard DENY caused by POL-005. **PASS.**

## 43. Authority/permission separation

Validation does not consume approval and PB does not itself perform external
dispatch. The intended separation exists, but forged authority projection
collapses the authority-to-permission trust boundary. **FAIL.**

## 44. Dry-path regression

The production dry-runtime command completed with `SIM_RESULT_CAPTURED`, no
external runtime, and no real execution. Dry/runtime compatibility suites
passed. **PASS.**

## 45. PB regressions

Existing PB consumers remain compatible in focused suites and fixed-SHA
partitions. The candidate's three old “PB file was never touched” assertions
are historical self-checks invalidated by the intentional additive PB change.

## 46. Invocation-store staging

The old dry `RuntimeInvocationStore` remains separate. Phase 3W neither
activates it for real dispatch nor adds a new production consumer.

## 47. RDGO gate implementation status

| RDGO gate | 3W implementation state | Evidence | External effect? |
|---:|---|---|---|
| 1 | existing governed intake only | no new caller | No |
| 2 | identity/request foundation, incomplete binding | source/tests | No |
| 3 | approval creation foundation, unsafe store/schema | source/tests | No |
| 4 | deferred static preflight | caller graph | No |
| 5 | validator foundation, projection forgeable | source/tests | No |
| 6 | PB request/policy foundation, POL-005 DENY | source/tests | No |
| 7 | Runtime Enforcement deferred | zero callers | No |
| 8 | live executable revalidation deferred | source boundary | No |
| 9 | durable pre-dispatch/consumption deferred | source boundary | No |
| 10 | dispatch not implemented | tripwire/caller graph | No |
| 11 | result acceptance not integrated | caller graph | No |

## 48. Runtime Enforcement non-activation

Calls from the new authority/PB foundation: **0**.

## 49. Shell Gate non-activation

Calls from the new authority/PB foundation: **0**. Shell Gate source and tests
are unchanged by the candidate.

## 50. Side-effect instrumentation

A fresh tripwire executed the full construct/validate/PB path while replacing
runtime/process/network/credential boundaries. It recorded no calls.

## 51. Filesystem effects

| Effect | Expected | Observed | Evidence |
|---|---|---|---|
| runtime subprocess | 0 | 0 | tripwire/import audit |
| network/provider | 0 | 0 | tripwire/import audit |
| credential read | 0 | 0 | tripwire/import audit |
| external runtime | 0 | 0 | dry runtime + tripwire |
| background task | 0 | 0 | source/import audit |
| source mutation | 0 | 0 | git diff/status |

The approval-store tests intentionally write only inside disposable temporary
directories. The symlink/hardlink tests demonstrate unsafe *possible* scope;
they do not touch external systems.

## 52. Import/global-state audit

The new modules import no subprocess, network, provider, or credential APIs.
Clean-process imports create no files. No module-level mutable authority cache
was found; the optional tracker is explicitly instance/process-local.

## 53. Two existing MUST-FIX findings

Phase 3S.2.1's malformed adapter result can still escape as an exception, and
its old invocation store accepts unsanitized IDs. Neither is reachable through
the Phase 3W foundation (zero caller path). Both remain
**DEFERRED-REAL-RUNTIME MUST-FIX**, to repair before their old components
become reachable. The new Phase 3W blockers precede Runtime Enforcement
planning.

## 54. Runtime inspect

Five checkpoints (entry; after authority tests; after PB tests; after
regression attribution; close) remained `Observed` / `observe` /
`unavailable`, implementation `not_implemented`, zero plugins/capabilities.

## 55. Contract drift

All five normative contract files are byte-identical baseline to candidate.
SHA-256: RIHAC `6cd84f2b…f2ba`; RIASC `6a4be213…224b`; PBRD
`28883a56…f7d`; RDGO `9e347e01…ff1`; RPAC `395f6b9d…0c89`.

## 56. Source-diff security audit

Of 22 shared functions in `permission_broker_foundation.py`, one existing
body (`build_permission_broker_request`) changed additively; all 40 shared
functions in `runtime_invocation.py` are unchanged. The 3W report's literal
claim that zero existing function bodies changed is therefore inaccurate,
although the additive signature/assignment is the intended Option-B delta.

## 57. Implementation tests

The eight Phase 3W test files collected 190 tests: **190 passed in 0.28s**.
This is implementation evidence, not independent certification.

## 58. Fresh adversarial tests

`tests/test_runtime_authority_pb_verification_3w1.py`: **83 passed in
0.20s**. The suite names and asserts demonstrated blocking gaps as observed
unsafe behavior so future repairs will require updating those expectations;
it does not convert the defects into acceptable behavior.

## 59. Whole-repo attribution investigation

A monolithic run was not certified because the environment previously
blocked custom process-control timeout machinery and the repository contains
known infrastructure/historical failure volume. Verification used ordinary
pytest partitions in detached disposable fixed-SHA worktrees, with xdist only
where supported. No custom process-group or child-process cleanup was used.

## 60. Shell-Gate hang reproduction

The reported audit-verify node completed at both SHAs when isolated (baseline
1 passed/0.34s; candidate 1 passed/0.31s); the reported hang was not
reproduced. A different tamper test is order-dependent: it mutates the first
persistent audit JSON without ensuring the original decision differs. It
passed at baseline and failed at candidate after broad-run state creation,
despite byte-identical Shell-Gate production/test files. Classification:
**ENVIRONMENT_OR_TEST_INFRASTRUCTURE**, not a product regression. No Shell
Gate code or test was changed.

## 61. Historical self-check classification

Four known historical tests fail at both SHAs (4/4) and are
**BASELINE_REPRODUCED / PRE_EXISTING / HISTORICAL_SELF_CHECK_DEBT**. The
three candidate-only “Permission Broker files untouched” tests are
**HISTORICAL_SELF_CHECK_DEBT** because their assertion records an old phase's
file-freeze, while Phase 3W intentionally and normatively modifies that file.

## 62. Expected obsolete-test classification

`test_future_action_is_not_implemented_but_selected_class_exists` asserts
exactly that `runtime_dispatch` is absent from `KNOWN_ACTION_TYPES`. It passes
at baseline and fails at candidate. Phase 3W intentionally implements that
exact action; PBRD-001 v1.1 requires it; current functional tests verify its
registration, 14-fact representation, execution class, and policy behavior.
Classification: **EXPECTED_OBSOLETE_ASSERTION**.

## 63. Fixed Fast Green attribution

| Partition / failure category | Baseline | Candidate | Classification | Attributable? |
|---|---:|---:|---|---|
| A–F ordinary serial | 2,581 passed | 2,581 passed | equivalent | No |
| G–M ordinary xdist | 1,065 passed, 4 failed | same | BASELINE_REPRODUCED / PRE_EXISTING (HATP fractions) | No |
| N–S ordinary xdist | 5,014 passed, 332 failed, 5 skipped, 9 errors | 5,008 passed, 338 failed, 5 skipped, 9 errors | 6 candidate-only investigated | See below |
| N–S three old no-PB-change nodes | passed | failed | HISTORICAL_SELF_CHECK_DEBT | No |
| N–S two certification-state nodes | passed | broad-run failed; isolated passed | ENVIRONMENT_OR_TEST_INFRASTRUCTURE | No |
| N–S Shell-Gate tamper node | passed | failed | ENVIRONMENT_OR_TEST_INFRASTRUCTURE | No |
| T–Z ordinary xdist | 144 passed | 144 passed | equivalent | No |
| Historical four-node set | 4 failed | 4 failed | BASELINE_REPRODUCED / PRE_EXISTING | No |
| Future-action obsolete node | 1 passed | 1 failed | EXPECTED_OBSOLETE_ASSERTION | Intentional capability addition |

Partition totals (marker-selected A–Z): baseline **8,804 passed, 336 failed,
5 skipped, 9 errors**; candidate **8,798 passed, 342 failed, 5 skipped, 9
errors**. The monolithic suite was not completed, so this report does **not**
claim FULL FAST GREEN PASS.

**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.** This statement is
strictly about fixed-SHA regression attribution and does not erase the fresh
blocking verification findings.

## 64. Push-state sentinel

Push/HEAD cleanliness is a lifecycle sentinel, kept separate from functional
attribution. Final commit/push evidence is recorded by phase completion.

## 65. Findings

**BLOCKING**

1. Forgeable `ValidatedAuthorityProjection` and public raw
   `approval_present=True`; `runtime_dispatch_context` is optional even for
   `runtime_dispatch`.
2. Approval-store symlink/hardlink escape and external overwrite; create-only
   is not secure against adversarial precreated paths.
3. Incomplete RIASC type/value enforcement and duplicate-key acceptance.
4. Approval-preview provenance is not recomputed/bound.
5. Descriptor version and filesystem/approval scope are not fully cross-bound.
6. Timestamp freshness/expiry uses lexical, not instant, comparison.
7. Idempotency derivation omits identity-critical facts and has no durable
   cross-process conflict guarantee.

**MUST-FIX / DEFERRED-REAL-RUNTIME:** the two unchanged Phase 3S.2.1 findings
in §53. **NON-BLOCKING:** inaccurate 3W “zero existing function bodies
altered” wording. **TEST-INFRASTRUCTURE-DEBT:** order-dependent Shell-Gate
audit test and fixed historical test infrastructure. **HISTORICAL-SELF-CHECK-
DEBT:** old phase/file-freeze assertions. No candidate failure was called
non-attributable without fixed-SHA or source evidence.

## 66. Authority/PB foundation verdict

```text
RUNTIME INVOCATION AUTHORITY + PB FOUNDATION:
NOT VERIFIED

RIHAC-001 v1.0:
NOT VERIFIED IN PRODUCTION

RIASC-001 v1.0:
PRODUCTION ENFORCEMENT NOT VERIFIED

PBRD-001 v1.1 OPTION B:
NOT VERIFIED

READY FOR RUNTIME ENFORCEMENT INTEGRATION PLANNING:
NO
```

## 67. Real-runtime readiness

```text
REAL-RUNTIME READY:
NO
```

POL-005 remains hard DENY, gates 7–11 are incomplete, and no real runtime is
available or activated.

## 68. Next dependency

The evidence-derived next phase is exactly **Runtime Invocation Authority +
PB Dispatch Foundation Blocking Repair**, followed by a new independent
re-verification. Only after closure should Runtime Enforcement integration
planning be reconsidered. The Phase 3S.2.1 findings must also be repaired
before their old components become reachable.

## 69. Recommendation

Do not integrate Runtime Enforcement and do not weaken POL-005. Repair the
seven bounded authority/PB findings, preserve the passing five-member replay,
freshness, policy, dry-runtime, and no-effect properties, then rerun fresh
independent adversarial verification and fixed-SHA regression attribution.

## 70. Human decision required

Stop after this report and governed close. Beginning the repair phase requires
explicit human authorization. Production source modified by 3W.1: **NO**.
Execution activated: **NO**. Release changed: **NO**. Article remains stopped;
private research remains untouched; no network/provider/credential access
occurred.

## Identifier matrix

| Identifier | Creator | Meaning | Bound inputs | Replay rule | Verdict |
|---|---|---|---|---|---|
| `invocation_id` | PCAE coordinator | logical invocation | five-member approval subject/PB fact | stable for retries | PASS |
| `approval_id` | approval coordinator | human act record | stored record + filename | create once | PARTIAL: store unsafe |
| `attempt_id` | PCAE coordinator | concrete try | PB fact | fresh each retry | PASS |
| `idempotency_key` | PCAE coordinator | logical request digest | incomplete construction projection | same safe retry; distinct invocation conflict | FAIL |
| PB request/decision identity | PB request builder | immutable policy evaluation evidence | envelope/request digest and policy evidence | invalidate on relevant drift | PARTIAL |

## Attack matrix

| Attack | Expected result | Observed | Verdict |
|---|---|---|---|
| repository/task/target/prompt replay | reject | rejected | PASS |
| stale HEAD/task/state/config/expiry | reject | rejected except fractional-time edge | PARTIAL |
| unknown/shortcut approval fields | reject | rejected | PASS |
| duplicate JSON authority key | reject | last-key wins | FAIL |
| forged validated projection | reject | accepted as authority | FAIL |
| raw PB `approval_present=True` | reject | accepted | FAIL |
| missing 14-fact context | reject | generic request accepted | FAIL |
| descriptor/scope substitution | reject | accepted in tested variants | FAIL |
| symlink/hardlink store escape | reject | external target writable | FAIL |
| valid authority + real request | POL-005 DENY | DENY | PASS |

## Final integrity statement

Phase 3W.1 changed verification tests and project memory only; it did not
modify `src/pcae`, contracts, Shell Gate, Runtime Enforcement, runtime
inspection, POL-005, dry behavior, release metadata, or any external system.
