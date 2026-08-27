# Phase 149O.20L.7O.3W.1R.1 — Independent Verification of Runtime Invocation Authority + PB Dispatch Foundation Blocking Repair

## 1. Objective

Independently verify Phase 3W.1R's claimed closure of the seven original
Phase 3W.1 authority/PB blockers against RIHAC-001 v1.0, RIASC-001 v1.0,
PBRD-001 v1.1, RDGO-001 v2.0, and RPAC-001 v1.0, without modifying
production or activating execution.

## 2. Independence

The verifier read the original 3W.1 artifact as the primary finding source,
then read contracts and current production before consulting the repair
mapping. Fresh test module
`tests/test_runtime_authority_pb_reverification_3w1r1.py` imports production
only and does not import any 3W/3W.1/3W.1R test helper or test module.

## 3. Baseline

| Fact | Value |
|---|---|
| Verification baseline | `63fe8ef5871b0190d6289460de6631f79fb27a76` |
| Defective 3W candidate | `289bd75d2d9843e95f336bcba2eed35bc414adb7` |
| Repaired functional candidate | `a9d1c912b71a503deb8ca019703f9176901395cf` |
| Public release | v0.4.3 at `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged |
| Entry runtime | `Observed` / `observe` / `unavailable` |
| Entry Git state | clean, pushed, `origin/main..HEAD=0` |

## 4. Seven original blockers

The original 3W.1 primary artifact contains exactly seven BLOCKING findings:

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

| Finding | Original affected file/symbol | Contract | Original attack |
|---|---|---|---|
| B1 | `ValidatedAuthorityProjection`; generic/runtime PB construction | RIHAC §16; PBRD §§5, 7, 22 | forged projection, raw boolean, missing Option-B context |
| B2 | `RuntimeInvocationApprovalStore.create/load` | RIHAC §§15, 18; RIASC §12 | directory/temp symlink and hardlink overwrite |
| B3 | `validate_riasc_schema_shape`; JSON load | RIASC §§2–7, 10–12 | invalid nested values and duplicate keys |
| B4 | `validate_approval` provenance step | RIHAC §§12, 16; RIASC §§7, 11 | changed preview digest plus recomputed record digest |
| B5 | `InvocationRequestContext`; PB authority projection | RIHAC §§3, 11, 16; PBRD §§4–5 | descriptor/scope substitution |
| B6 | approval creation/expiry validation | RIHAC §§14, 16; RIASC §11 | fractional-time lexical-order exploit |
| B7 | dispatch projection/identity tracker | PBRD §§6, 10, 15; RDGO §10a; RPAC-REQ-064–068 | incomplete digest and process-local collision state |

## 5. Repair delta

The functional repair changed exactly four production files between the
defective and repaired functional SHAs: `runtime_authority.py`,
`runtime_invocation_approval_store.py`, `runtime_dispatch_permission.py`, and
`permission_broker_foundation.py` (695 insertions, 95 deletions).

## 6. Repair mapping

### Matrix A — Seven blocker re-verification

| Finding | Original root cause | Repair | Fresh test | Variant test | Verdict |
|---|---|---|---|---|---|
| B1 | public structural objects/boolean treated as authority | object seals, trusted builders, mandatory context | naive forge/raw boolean/missing context rejected | copied projection seal and copied PB-request seal both obtain simulated ALLOW | **OPEN** |
| B2 | path replace/follow semantics | no-follow directory-relative exclusive persistence | directory symlink cannot escape | slash/backslash/absolute IDs, store symlink, hardlinked record, duplicate writes | CLOSED |
| B3 | partial hand validation/last-key-wins JSON | complete nested validation and duplicate-key hook | invalid nested fields rejected | malformed/truncated/non-object/unknown fields | CLOSED |
| B4 | preview digest trusted as stored | recompute preview from reviewed facts | changed preview with recomputed record digest rejected | subject/provenance/prompt tamper | CLOSED |
| B5 | partial scope/descriptor cross-binding | exact object equality plus binding digest | descriptor and scope drift rejected | version/digest/filesystem/process variants | CLOSED |
| B6 | lexical timestamp order | strict UTC parsing and instant comparison | fractional exploit closed | creation and validation boundary variants | CLOSED |
| B7 | incomplete projection/process-local state | complete projection and durable local registry | all contract-bound facts change key; cross-process determinism holds | copied identity seal creates an unregistered attempt accepted by builder | **OPEN** |

No contract changed. The repair mechanisms match the repair report, but B1
and B7 do not remove their root causes because object identity seals are
copyable and builder validation does not re-establish producer/registry
provenance.

## 7. Fresh blocker reproduction

Fresh results against current repaired source:

```text
BLOCKER 1: OPEN
BLOCKER 2: CLOSED
BLOCKER 3: CLOSED
BLOCKER 4: CLOSED
BLOCKER 5: CLOSED
BLOCKER 6: CLOSED
BLOCKER 7: OPEN
```

The new module has 97 passing tests. Tests named `exposes_blocker` assert the
observed unsafe behavior as evidence; a green verifier run therefore does not
mean the repair passed.

## 8. Negative variants

Bounded variants covered copied seals, direct dataclass replacement, raw PB
booleans, missing context, six malformed ID/path forms, symlinked directory
components, hardlinked records, duplicate identical/conflicting writes,
duplicate JSON keys, seven tamper families, four descriptor/scope drifts,
fractional times, all five subject members, all seven freshness conditions,
all fourteen PB facts, and twelve idempotency-bound input families.

## 9. Contract integrity

`git diff abd3f5b4..a9d1c912 -- docs/contracts` is empty. RIHAC-001 v1.0,
RIASC-001 v1.0, PBRD-001 v1.1, RDGO-001 v2.0, and RPAC-001 v1.0 are unchanged.
The open findings are implementation nonconformance, not contract gaps.

## 10. Approval-store trust

The filesystem store itself is repository-confined, create-only, atomic at
publication, filename-bound, duplicate/conflict rejecting, link-aware, and
fail-closed on corruption. End-to-end approval-store trust is nevertheless
**NOT VERIFIED** because `validate_approval` accepts a bare
`RuntimeInvocationApproval` object and has no evidence that it came from the
canonical store.

## 11. Path confinement

`..`, slash, backslash, absolute, empty, and malformed approval IDs fail the
closed `ria-<32-hex>` grammar. Approval directory and fixed store components
are checked as non-symlink directories. Verdict: **PASS for the store API**.

## 12. Symlink/hardlink analysis

Pre-existing approval-directory symlinks and symlinked `.pcae` components are
rejected. Final records with link count other than one are rejected. No
external sentinel changed. A concurrent directory-swap race was not claimed
tested; the implemented directory-FD/no-follow boundary is the evidence used.

## 13. Corruption/tamper

Truncated/invalid/non-object JSON, duplicate keys, wrong schema, changed
subject/provenance/prompt/repository, unknown fields, hardlinks, and
filename/record-ID mismatch fail closed at the appropriate store/schema/live
binding boundary. There is no caller-hint fallback. Verdict: **PASS**, subject
to the missing store-origin binding in §10.

## 14. Provenance

Preview and record digests are recomputed, producer/mechanism constants are
checked, and human ID must differ from producer. However,
`create_runtime_invocation_approval` is a public callable that accepts
`approver_id` and `identity_evidence_kind` as strings and emits a record that
validates as `identified_human_distinct_from_producer`, without trusted
confirmation evidence. **New BLOCKING finding N2: human provenance is
caller-manufacturable.**

## 15. Subject binding

The exact five-member subject is `(invocation_id, runtime_target_id,
prompt_hash, repository_identity, task_id)`. Fresh one-at-a-time mismatches
all reject. Verdict: **PASS once genuine canonical authority is assumed**.

## 16. Repo/task/target/prompt replay

Copied repo-A records reject against repo B; task A rejects under task B;
target A rejects under target B; semantic prompt changes reject. NFC and
CRLF/CR normalization is stable while load-bearing whitespace changes the
hash. No best-effort fallback exists.

## 17. Seven freshness rules

| Rule | Classification | Evidence |
|---|---|---|
| HEAD | ACTIVELY ENFORCED | mismatch returns stale approval |
| task state/contract | ACTIVELY ENFORCED | state and digest mismatch reject |
| prompt | ACTIVELY ENFORCED | subject mismatch rejects |
| runtime target | ACTIVELY ENFORCED | exact target mismatch rejects |
| adapter configuration | ACTIVELY ENFORCED | full adapter binding mismatch rejects |
| policy version | STAGED FOR LATER LIVE PREFLIGHT | projection survives only with explicit fresh-PB-re-evaluation disposition, as frozen |
| timeout/expiry | ACTIVELY ENFORCED | trusted current time compared as UTC instant |

This matches frozen ownership; no placeholder is counted as live enforcement.

## 18. One-shot staging

Creation, load, validation, request construction, PB evaluation, and POL-005
DENY do not consume approval. Revalidation succeeds afterward. Gate-9
consumption remains **NOT IMPLEMENTED**, as required for this foundation.

## 19. attempt_id

Normal construction mints `att-<32-hex>` and retries use a distinct attempt.
But a sealed identity can be copied with `dataclasses.replace`, its public
digest recomputed, and an unregistered replacement attempt accepted. Verdict:
**NOT VERIFIED / B7 OPEN**.

## 20. idempotency_key

Normal keys are deterministic, distinct from attempt IDs, stable for the
same invocation/content, independent of wall clock/PID/environment ordering,
and change across repository/base/task/task-contract/lifecycle/target/adapter/
prompt/capability/filesystem/process/budget changes. Verdict: derivation
**PASS**; trusted identity ownership remains **FAIL** through B7.

## 21. Replay/idempotency

The durable registry detects ordinary same-invocation changed-content and
same-key/different-invocation collisions across processes. It is bypassable
because the final builder validates a copyable seal and self-consistent digest
without rechecking the registry record. No exactly-once claim is made.

## 22. PBRD Option-B

The action-specific nested type is mandatory for `runtime_dispatch`; generic
construction refuses it; non-runtime actions remain compatible. All fourteen
facts are structurally mandatory. Overall PBRD verdict: **NOT VERIFIED**
because the trusted authority fact and attempt identity are forgeable.

## 23. Fourteen facts

All fourteen contract facts were recovered and independently mutated:
invocation ID, attempt ID, idempotency key, repository identity, task ID,
lifecycle context, runtime target, adapter descriptor binding, prompt hash,
requested capability, local-CLI transport, network=false, filesystem scope,
and human-authority binding. Every malformed fact produces structural DENY.

## 24. Trusted projection

Nominal trace is approval validation -> `ValidatedAuthorityProjection` ->
`project_human_authority_binding` -> trusted PB builder. At
`runtime_authority.py:774-817`, trust is only identity comparison against an
object stored in a public frozen dataclass field. `dataclasses.replace`
retains it. The architecture does not structurally prove fresh validation.

## 25. Forged projection attacks

Naive hand construction is rejected. Two close variants succeed:

1. copy a legitimate projection, replace approval ID/digest/binding, retain
   `_validator_seal`, then obtain `approval_present=true` and simulated ALLOW;
2. copy a sealed no-authority PB request, replace its authority binding and
   boolean, retain `_runtime_dispatch_seal`, then obtain simulated ALLOW.

This directly violates PBRD §§5/7 and keeps original B1 OPEN.

## 26. POL-004

Rule-local behavior is correct: genuine trusted-looking approval suppresses
POL-004, missing approval triggers HUMAN_REVIEW, and a naive unsealed forge is
missing. End-to-end behavior is **NOT VERIFIED** because copied seals make a
forged hint look trusted.

## 27. HUMAN_REVIEW

HUMAN_REVIEW remains non-authorizing. Valid approval does not suppress other
review policies. Missing approval plus a non-simulation request triggers
POL-004 and POL-005; DENY wins.

## 28. PB precedence

Source and fresh evaluation confirm `DENY > HUMAN_REVIEW > ALLOW`, unchanged.

## 29. POL-005 source identity

The `ExecutionDisabledRule` source block is byte-identical at pre-3W
`daebfdbb`, 3W `289bd75d`, and repaired candidate `a9d1c912`; normalized block
SHA-256 is `63224afe1d6220e1573ff0376155dc710104c630b8b1ea35e2f51a93cba6940a`.
No weakening occurred.

## 30. Strongest-valid-request DENY

A current, unconsumed, schema-valid approval; exact subject/scope; fresh
identity; all fourteen facts; trusted projection; and otherwise favorable
policies still produce final `DENY`, sole cause `POL-005`, reason
`execution_boundary_unavailable`.

## 31. Authority-vs-enablement

Even a structurally accepted or forged authority projection plus PB request
does not enable real execution: non-simulation evaluation is hard-DENY and no
later gate exists. Authority is not enablement.

## 32. PB compatibility

The focused authority/PB/Foundation set passes. The fixed-SHA consumer
partition reproduces the repair counts exactly; existing non-runtime actions
remain context-free. No new requirement leakage was found.

## 33. Dry regression

The production dry regression partition passes. The path remains
`adapter_invocation`, `simulation_only=true`, with explicit target and no
fallback. It was not migrated to `runtime_dispatch`.

## 34. RE non-activation

Production caller/source search finds zero Runtime Enforcement calls from the
authority/PB foundation. Observed calls: **0**.

## 35. Shell Gate non-activation

Production caller/source search finds zero Shell Gate calls from the repaired
foundation. Observed calls: **0**.

## 36. No subprocess/network/credentials

Fresh tripwires around the pure authority -> request -> PB path observe:
runtime subprocess **0**, network/provider **0**, credential reads **0**,
external runtime **0**, background threads/jobs **0**.

## 37. Filesystem effects

Disposable repositories contain only expected approval and gate-2 identity
artifacts. Main HEAD/index/tracked source remain unchanged by runtime paths;
runtime-authored untracked source is **0**. Verification adds only its test,
report, and governance memory.

## 38. Import/global-state

Fresh-process import creates no files and imports no subprocess/socket/
provider SDK. Identity registries are repository-local and cross-process
deterministic. There is no mutable module-global authority cache, but the
module-global seals are transferable capabilities, which is the B1/B7 defect.

## 39. Seven closure matrix

See Matrix A. Final result: **5 CLOSED / 2 OPEN**.

## 40. Root-cause closure

| Finding | Root cause removed? | Reason |
|---|---|---|
| B1 | NO | seals are copyable; PB validates shape/seal, not validator provenance |
| B2 | YES | no-follow/exclusive directory-FD persistence restores confinement |
| B3 | YES | strict recursive validation and duplicate-key rejection |
| B4 | YES | preview digest recomputed from exact reviewed facts |
| B5 | YES | exact scope/adapter equality and binding digest |
| B6 | YES | parsed aware-instant comparisons |
| B7 | NO | identity seal/digest can be copied and builder does not recheck registry |

## 41. New blocker search

Two additional BLOCKING findings were found:

- **N1 — canonical-store provenance is not bound to validation.**
  `validate_approval` accepts a caller-created approval object directly;
  steps 1–2 are documented as another caller's responsibility, with no
  store-issued evidence. A recomputed, schema-valid object can validate
  without ever existing canonically.
- **N2 — human-confirmation provenance is caller-manufacturable.**
  `create_runtime_invocation_approval` accepts arbitrary approver/evidence
  strings and emits an artifact later described as identified-human evidence.
  No trusted confirmation result or producer capability is required.

Both are reachable within the foundation API today, though POL-005 prevents a
real effect. They must be repaired under existing frozen semantics.

## 42. Older MUST-FIX findings

Recovered verbatim:

1. **Malformed adapter result crashes uncaught instead of failing closed
   cleanly.** `simulate_invocation` passes an unvalidated collect result to
   `RuntimeInvocationStore.write_result`, allowing uncaught `AttributeError`.
2. **`RuntimeInvocationStore` does not sanitize `invocation_id` against path
   traversal.** Raw IDs are joined beneath the old dry store without
   confinement validation.

Neither is reachable from the repaired foundation: it imports/calls neither
`runtime_adapter.simulate_invocation` nor the older `RuntimeInvocationStore`.
They remain **MUST-FIX / DEFERRED-REAL-RUNTIME**, not repaired here.

## 43. Runtime inspect

`TRUTHFUL_WITH_LIMITATION`: no real adapter is registered or available.
Runtime remains `Observed` / `observe` / `unavailable`.

## 44. Fixed-SHA attribution

### Matrix F — Regression attribution

| Partition/failure | Defective baseline | Repaired candidate | Classification | Attributable |
|---|---:|---:|---|---|
| Shared eight 3W files | 190 passed | 190 passed | equivalent | No |
| Repair verifier + closure | absent | 99 passed | intended repair evidence | No |
| PB/runtime/3F/publication/dry, xdist, non-slow | 4,077 passed / 1 failed | 4,176 passed / 1 failed | same failure + 99 intended tests | No |
| runtime snapshot `Session:` assertion | failed | failed | BASELINE_REPRODUCED / PRE_EXISTING | No |

Candidate-only functional failures: **0**. Remaining unexplained attributable
functional regressions: **0**. The independent security blockers are current
behavior findings, not candidate-only test regressions.

## 45. Test-infrastructure debt

Shell-Gate order/hang debt remains separately carried and was not reopened.
Optional packaging tests requiring unavailable `build` remain environment
debt. No aggressive process-control harness was constructed.

## 46. Historical-self-check debt

Historical fixed-phase/file-freeze assertions remain carried. The assertion
that `runtime_dispatch` does not exist remains EXPECTED_OBSOLETE because the
frozen current PBRD requires the implemented action.

## 47. Contract integrity

Normative drift is **NONE**. The failed verdict is based on direct conflict
between current implementation and already-frozen trust/source requirements;
no undocumented reinterpretation is accepted.

## 48. Findings

### Matrix B — Authority attacks

| Attack | Required result | Observed | Verdict |
|---|---|---|---|
| naive projection/raw boolean | reject | rejected | PASS |
| copied validator seal | reject | simulated ALLOW | BLOCKING |
| copied PB-request seal + fake binding | reject | simulated ALLOW | BLOCKING |
| direct noncanonical approval object | reject | validates | BLOCKING |
| caller-supplied human strings | no trusted authority | identified-human projection | BLOCKING |
| repo/task/target/prompt replay | reject | rejected | PASS |
| store link/corruption attacks | reject | rejected | PASS |
| copied identity seal/unregistered attempt | reject | builder accepts | BLOCKING |

### Matrix C — PBRD trust boundary

| Concern | Trusted source | Validation | Adversarial result |
|---|---|---|---|
| approval reference | canonical store + validator | ID/digest shape | store provenance absent |
| approval projection | RIHAC validator | copyable object seal | bypassed |
| PB request | trusted integration | copyable object seal + 14-fact shape | bypassed |
| attempt identity | coordinator + durable registry | copyable seal + self-digest | registry bypassed |
| ordinary facts | named owners | strict shape/binding | pass |

### Matrix D — Identifier semantics

| ID | Creator | Meaning | Replay rule | Verified |
|---|---|---|---|---|
| invocation_id | coordinator | logical invocation | stable only for same invocation | partial: seal-copy boundary |
| approval_id | approval coordinator | human act | create once/canonical lookup | no: noncanonical object accepted |
| attempt_id | coordinator | concrete try | new each retry, registered | no: copied identity accepted |
| idempotency_key | coordinator | canonical logical request | same unchanged invocation/content | derivation yes; ownership no |
| PB request_id | PB builder | evaluation envelope | immutable evidence | structural only |

### Matrix E — Side effects

| Effect | Expected | Observed | Evidence |
|---|---:|---:|---|
| runtime subprocess | 0 | 0 | fresh tripwire |
| network/provider | 0 | 0 | socket/source tripwire |
| credential read | 0 | 0 | environment tripwire |
| external runtime | 0 | 0 | no caller path/POL-005 |
| background work | 0 | 0 | thread-start tripwire |
| runtime source mutation | 0 | 0 | Git/filesystem audit |

### Matrix G — Final findings

| Finding | Severity | Status | Next boundary |
|---|---|---|---|
| B1 copied projection/PB seals | BLOCKING | OPEN | trusted construction repair |
| B2 store links | BLOCKING | CLOSED | retain regression |
| B3 schema/duplicate keys | BLOCKING | CLOSED | retain regression |
| B4 preview provenance | BLOCKING | CLOSED | retain regression |
| B5 descriptor/scope | BLOCKING | CLOSED | retain regression |
| B6 instant comparison | BLOCKING | CLOSED | retain regression |
| B7 copied identity/registry bypass | BLOCKING | OPEN | identity provenance repair |
| N1 missing canonical-store provenance | BLOCKING | OPEN | store-bound validation API |
| N2 caller-manufactured human provenance | BLOCKING | OPEN | trusted confirmation boundary |
| older malformed result/path traversal | MUST-FIX / DEFERRED-REAL-RUNTIME | OPEN, unreachable | before first non-mock adapter |
| runtime inspect limitation | OBSERVATION | OPEN | before availability claim |

## 49. Authority/PB verdict

```text
RUNTIME INVOCATION AUTHORITY + PB FOUNDATION REPAIR:
NOT VERIFIED
3W.1 ORIGINAL BLOCKERS:
5 / 7 INDEPENDENTLY CLOSED; B1 AND B7 OPEN
NEW BLOCKING:
2
RIHAC-001:
IMPLEMENTATION NOT VERIFIED
RIASC-001:
STRUCTURAL ENFORCEMENT VERIFIED; AUTHORITY ORIGIN NOT VERIFIED
PBRD-001:
OPTION-B TRUST BOUNDARY NOT VERIFIED
TRUSTED APPROVAL PROJECTION:
BYPASS PRESENT
POL-004:
RULE-SPECIFIC LOGIC CORRECT; TRUSTED INPUT FORGEABLE
POL-005:
UNCHANGED HARD DENY
```

## 50. Next-layer readiness

**READY FOR RUNTIME ENFORCEMENT INTEGRATION PLANNING: NO.** Two original
blockers and two new blockers remain. The two older 3S.2.1 MUST-FIX findings
remain unreachable today but would become load-bearing later.

## 51. Real-runtime readiness

**REAL-RUNTIME READY: NO.** Runtime Enforcement integration, Shell Gate/
containment, gate-9 consumption, runtime-inspect reconciliation, the older
MUST-FIX repairs, and a first real process fixture remain incomplete.

## 52. Next options

1. **Option C — another authority/PB hardening phase: REQUIRED and first.**
   Remove copyable seal authority, bind validation to canonical store output,
   bind approval creation to trusted human-confirmation evidence, and recheck
   identity registry provenance at request construction.
2. Option A — repair the two older 3S.2.1 findings: next after authority/PB
   trust closure and before their components become reachable.
3. Option B — Runtime Enforcement integration planning: blocked by option C.

## 53. Recommendation

Next governed phase:

**149O.20L.7O.3W.1R.2 — Runtime Invocation Authority Provenance, Trusted
Construction, and Identity Registry Blocking Repair**

Scope it to B1, B7, N1, and N2 under unchanged contracts, preserve POL-005,
and require another independent verification before Runtime Enforcement work.

## 54. Human decision required

**YES.** Stop after 3W.1R.1. Production source modified: **NO**. Execution
activated: **NO**. Release changed: **NO**. Article remains stopped. Private
research remains untouched. Governance-only Git push/notification may use the
existing governed lifecycle; the verified authority/PB foundation itself made
zero runtime/provider/network/credential effects.

