# Phase 149O.20L.7O.3F.1 — Independent End-to-End Rollback Permission-Boundary Verification

**Status: VERIFICATION-ONLY — COMPLETE. Zero Blocking findings.**

## 1. Objective

Independently re-derive, without trusting 149O.20L.7O.3F's own claims,
tests, or classifications, whether 3F's reported integration
(`mutation_permission.evaluate_rollback_permission()` gating
`core/agent.py::build_rollback_execution`'s default,
non-`HATP_MANDATORY` dispatch path) genuinely closes the sole
remaining Permission Broker production-coverage gap on the rollback
default path, with no bypass, no fallback, no runtime-capability
leakage, and no regression.

## 2. Methodology

Fresh source reconstruction at the pre-3F commit and the current
commit, a repo-wide grep-based consumer/bypass audit, a newly written
independent test module (`tests/test_phase_149o_20l_7o_3f_1_independent_rollback_permission_verification.py`,
19 tests, imports nothing from 3F's own test file), execution of all
pre-existing relevant regression suites, and a full two-sided Fast
Green A/B run (current worktree vs. an isolated read-only git worktree
checked out at the pre-3F commit `97bb9cda`). No file under `src/pcae/`
was modified during this phase.

## 3. Pre-3F historical graph

Read via `git show 97bb9cda:src/pcae/core/agent.py`. Pre-3F,
`build_rollback_execution` had exactly one gate before the file
restore/remove loop: the `HATP_MANDATORY` branch check
(`if resolve_production_hatp_cutover_mode(root).mode == CutoverMode.HATP_MANDATORY: ...`).
On every other mode (`LEGACY_COMPATIBLE`, `PREPARED` — every mode any
real current deployment resolves to), execution fell straight through
to the restore/remove loop with **zero** Permission Broker evaluation.
3F's central premise — that the default dispatch path was
completely unbrokered — is independently **CONFIRMED**, not merely
repeated from 3F's own report.

## 4. Current graph

Read directly from current `src/pcae/core/agent.py`:

- Dry-run return: line 94195–94208, before any gate.
- `HATP_MANDATORY` branch: lines 94266–94336, byte-identical to
  pre-3F (confirmed by diff: only the `_RER_VALID_STATUSES` frozenset
  line and the new gate block were added anywhere in this function).
- New gate (`evaluate_rollback_permission` call site): lines
  94350–94376, immediately before the mutation loop at line 94382.
- No mutation of any kind precedes the new gate on the default path.

## 5. Highest-level entry point

`src/pcae/cli.py:3127–3158` wires `rollback_parser.set_defaults(handler=run_rollback)`.
Exact production syntax: `pcae rollback --per-id <PER_ID> [--hatp-evidence-id ID] [--dry-run] [--json]`.
`run_rollback` (`src/pcae/commands/agent.py:16263`) is the sole
production caller of `build_rollback_execution` — confirmed by
repo-wide `rg 'build_rollback_execution\('` finding exactly one
non-definition call site. The broker gate is proven reachable from the
real top-level human-facing command, not only from an internal helper.

## 6. Effect boundary

The gate at 94350–94376 sits strictly before the restore/remove
mutation loop (94382+). On DENY, broker failure, or a malformed
result, the function returns immediately with `execution_allowed:
False` and zero file mutation — proven both by static read and by the
fresh DENY/exception/malformed-result tests (§12–§16 below), all
passing.

## 7. Direct-helper reachability

Repo-wide grep found no caller of the restore/remove helpers or of
`build_rollback_execution` other than `run_rollback`. A fresh test
invoking `build_rollback_execution` directly (bypassing the CLI layer
entirely) still hits the gate and is denied when the broker denies —
proving the gate is enforced at the shared production function, not
merely at a CLI wrapper.

## 8. Permission policy applicability

`src/pcae/core/permission_broker_foundation.py:449–468`:
`MissingHumanApprovalRule` (POL-004)'s `applicable_execution_classes`
explicitly **excludes** `EXECUTION_CLASS_MUTATION` and **includes**
`EXECUTION_CLASS_ROLLBACK`. Every existing Wave-1 adapter (commit,
push — `mutation_permission.py:276–300, 375–395`) already uses the
identical `ACTION_*` + `EXECUTION_CLASS_MUTATION` pairing pattern.
3F's choice of `EXECUTION_CLASS_MUTATION` over `EXECUTION_CLASS_ROLLBACK`
is precedented (not novel) and correctly avoids inventing an
unconditional POL-004 `HUMAN_REVIEW` requirement this phase's
governing instruction never authorized.

## 9. Execution-class analysis

Confirmed: pairing `ACTION_ROLLBACK` with `EXECUTION_CLASS_MUTATION`
does not weaken any existing required policy — `EXECUTION_CLASS_ROLLBACK`
remains untouched and still governs the separate HATP-gated AG3/AG5
advisory evaluation in `hatp_ag_authority.py`. The two execution
classes now cover two genuinely different rollback paths (HATP-gated
vs. default), not the same path twice.

## 10. COMP-008 identity analysis

Repo-wide grep confirms `COMP-008` is registered generically as
`ComponentRegistryEntry("COMP-008", "Rollback Boundary", "not_implemented")`
in the canonical component registry — not HATP-specific in its
registered meaning. Reuse for the default-path gate is a legitimate
application of an existing general "Rollback Boundary" component
identity, not a semantic mismatch.

## 11. Capability identity analysis

The `build_rollback_execution` capability literal was already
registered and consumed only by the separate HATP-gated AG5
evaluation in `hatp_ag_authority.py`. Reusing the same literal for the
Wave-1-style default-path adapter correctly identifies the same
underlying function boundary from a second, independent evaluation
path; no identity aliasing or policy collision was found — the two
evaluations (HATP-gated advisory vs. default-path Wave-1 gate) are
mutually exclusive by construction (one only runs in `HATP_MANDATORY`
mode, the other only outside it).

## 12. ALLOW

Fresh end-to-end test constructs a disposable rollback scenario, mocks
the broker to return ALLOW, and confirms via the real
`build_rollback_execution` call path that the pre-existing eligible
dispatch proceeds, only the expected disposable file mutation occurs,
and the resulting `RollbackExecutionRecord` truthfully reflects
success. **PASS.**

## 13. DENY

Fresh test confirms: zero file mutation, `record["status"] ==
"aborted_permission_denied"`, `record["rollback_executed"] is False`,
record persisted, `execution_allowed: False` returned to the caller.
**PASS.**

## 14. HUMAN_REVIEW

Not applicable under the current policy: `MissingHumanApprovalRule`
(POL-004), the only rule capable of returning `HUMAN_REVIEW`, is
scoped to `EXECUTION_CLASS_ROLLBACK`/`SHELL`/`BACKEND`/`ADAPTER` and
explicitly excludes `EXECUTION_CLASS_MUTATION` — the class this
adapter uses. **NOT APPLICABLE UNDER CURRENT POLICY** (per §14 of the
governing instruction, no HUMAN_REVIEW test path was fabricated by
altering policy).

## 15. Broker failure

Fresh test raises an exception from the broker call site; confirms
zero mutation, no fallback to ALLOW. **Fail-closed, PASS.**

## 16. Malformed result

Fresh test supplies a broker result object lacking `.authorized` /
non-boolean object; the shared primitive
(`evaluate_repository_mutation_permission`) performs `isinstance` and
strict `== DECISION_ALLOW` checks, not substring/truthy parsing —
confirmed at both the call site and the shared-primitive unit level.
A malformed result cannot be accidentally treated as ALLOW. **PASS.**

## 17. Status vocabulary audit

Repo-wide grep for `_RER_VALID_STATUSES`, the sibling precedent status
`aborted_hatp_mandatory_denied`, `record["status"]`, and all RER
status consumers found that every consumer (`_ect_check_interrupted_states`,
`_ect_check_partial_states`, CLI rendering, generic `_rer_validate`)
does either positive-list membership against specific known statuses
(`"in_progress"`, `"partial"`) or generic frozenset validation — no
fixed enum/switch exists that would silently mishandle an unrecognized
status. `aborted_permission_denied` was added using the exact same
mechanism as the already-shipped `aborted_hatp_mandatory_denied`
precedent.

## 18. aborted_permission_denied terminal-state semantics

A denied record is not flagged as `in_progress` or `partial` by any
consumer (confirmed by fresh test); it cannot be interpreted as
successful or eligible for continuation. It is a genuine terminal
state, structurally identical in every consumer's eyes to its already-
vetted sibling status. Retry re-enters `build_rollback_execution` from
scratch (new record), it does not resume/replay the denied record.

## 19. DENY retry/idempotency

Fresh test repeats the same denied request; confirms deterministic
zero-mutation result each time, no status flip, no inconsistent
duplicate record state.

## 20. ALLOW retry/idempotency

Existing rollback idempotency/reconciliation semantics (pre-existing,
untouched by 3F) continue to govern repeated-effect prevention; the
new gate sits strictly before those mechanisms and does not alter
them.

## 21. Restart/recovery

Not separately re-tested as a new mechanism: 3F introduced no new
persistence/checkpoint behavior beyond the existing
`store_rollback_execution_record` call already used by every other
terminal status in this function. Recovery semantics are unchanged
from pre-3F.

## 22. Human trigger independence

`pcae rollback --per-id <PER_ID>` remains the sole production entry
point (§5); the new gate is a machine-checked authorization check on
an already-human-initiated action, not a substitute trigger. Broker
ALLOW does not fabricate or bypass the `--per-id` human-authorization
requirement — confirmed by static read (the CLI's own `--per-id`
argument requirement is untouched by the 3F diff).

## 23. Runtime independence

Fresh test runs `pcae runtime inspect --json` (via subprocess) before
and after an ALLOW-path disposable rollback and confirms
`Runtime state: Observed`, `Execution capability: unavailable`,
`Maximum plugin capability: observe` are byte-identical before and
after. Broker ALLOW does not mutate runtime capability. **PASS
(permission != execution capability, independently reverified).**

## 24. HATP_MANDATORY isolation

Diff-confirmed: the `HATP_MANDATORY` branch body is unchanged line-
for-line from pre-3F. Fresh test with a spy on
`evaluate_rollback_permission` confirms it is never called when mode
resolves to `HATP_MANDATORY`. `resolve_production_hatp_cutover_mode`
is re-resolved fresh (no caller-supplied override, no cached earlier
read), so branch selection cannot be manipulated by rollback-request
input to escape the new gate's coverage while still executing the
default-path mutation logic.

## 25. Branch-bypass audit

No production-reachable path was found that executes the default-
path restore/remove mutation while resolving into the `HATP_MANDATORY`
branch's code (they are mutually exclusive by the `if/else` structure
itself, and mode resolution has no caller-controlled override
parameter in `build_rollback_execution`'s signature).

## 26. Operation identity

Fresh test asserts (via mock spy) that the broker call for a rollback
carries `action_type=ACTION_ROLLBACK`, `execution_class=EXECUTION_CLASS_MUTATION`,
`requested_component="COMP-008"`, `requested_capability="build_rollback_execution"`
— and that this identity tuple is distinct from a push adapter's
identity tuple captured in the same test run. No cross-consumer
identity collision.

## 27. Audit/evidence

DENY and failure paths produce a `RollbackExecutionRecord` with
`status`, `rollback_executed: False`, and denial details from
`permission_denial_details()` — using the same existing evidence
shape as every other terminal RER status, not a new parallel audit
format.

## 28. Push regression

`tests/test_mutation_permission_push_routing_integration.py` and the
full permission-broker/push/publication/policy suite (see §30) pass
unchanged; the rollback adapter is additive and does not alter shared
`evaluate_repository_mutation_permission` behavior for push callers.

## 29. Publication regression

Publication-path tests within the same broad regression sweep (§30)
pass unchanged.

## 30. Existing regression suites (exact counts)

| Suite group | Result |
|---|---|
| `test_ag5_hatp_mandatory_consumption.py` + 3F's own suite | 43/43 passed |
| Rollback suites (`test_rollback_approval_evidence_{contract,models,persistence,validation}.py`, `test_hatp_rollback_consumption.py`, `test_enforcement_rollback.py`, `test_cltr_rehearsal_rollback.py`) | 192/192 passed |
| Full mutation_permission + permission_broker + policy suite (21 files) | 983 passed, 2 failed |
| New fresh 3F.1 suite (19 tests) | 19/19 passed |

The 2 failures in the broad permission-broker sweep
(`test_permission_broker_consumer_scope_inventory`,
`test_actual_git_push_dispatch_site_in_core_agent_remains_unwired`)
were independently reproduced identically at the pre-3F commit
(`97bb9cda`) in an isolated git worktree — pre-existing, unrelated to
this integration. **Zero attributable regressions in this group.**

## 31. Fast Green A/B (exact node-ID diff)

Two full `pytest -m fast_green -p no:randomly` runs: current worktree
(HEAD `53ef81ff` + this phase's fresh test file) vs. an isolated
read-only git worktree at pre-3F commit `97bb9cda`.

- Baseline (pre-3F): 338 failed, 8689 passed, 5 skipped, 27786
  deselected, 9 errors.
- Current: 338 failed, 8729 passed, 5 skipped, 27786 deselected, 9
  errors. (+40 passed = 3F's 21 tests + this phase's 19 tests, both
  absent from the pre-3F worktree.)
- Exact newly-failing (in current, not baseline): **1** —
  `tests/test_phase_149o_18e_cli_legacy_authority_migration_integration.py::TestProductionFileAllowlist::test_ag5_build_rollback_execution_body_unchanged_since_entry`.
  This is a frozen "function body unchanged since its historical entry
  commit" tripwire that necessarily fails once `build_rollback_execution`
  is legitimately modified by 3F — non-functional, expected, and
  self-acknowledged by the tripwire's own name.
- Exact newly-passing (in baseline, not current): **1** —
  `tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main`.
  A `HEAD == origin/main` timing-sensitive check that flips depending
  on push state at run time — non-functional, not caused by any source
  change.

**Attributable functional regressions: 0.**

## 32. Findings

No Blocking findings. No Non-Blocking findings beyond the two already-
documented frozen tripwire effects above (both classified NON-BLOCKING,
not attributable to source behavior change).

## 33. Final verdict

```
PERMISSION BROKER ROLLBACK DEFAULT-PATH CONSUMPTION:
INDEPENDENTLY VERIFIED
HISTORICAL DEFAULT PATH:
CONFIRMED UNBROKERED
CURRENT DEFAULT PATH:
BROKER-GOVERNED
BROKER BEFORE EFFECT:
VERIFIED
ALLOW:
VERIFIED
DENY:
ZERO MUTATION VERIFIED
BROKER FAILURE:
FAIL-CLOSED
MALFORMED RESULT:
FAIL-CLOSED
NO-BYPASS:
VERIFIED
ABORTED_PERMISSION_DENIED:
SAFE TERMINAL STATE VERIFIED
ROLLBACK READINESS/EVIDENCE:
UNCHANGED
HUMAN TRIGGER:
UNCHANGED
HATP_MANDATORY:
UNCHANGED
PERMISSION != CAPABILITY:
VERIFIED
RUNTIME:
Observed / observe / unavailable
ATTRIBUTABLE REGRESSIONS:
0
BLOCKING:
0
```

## 34. Release recommendation

Zero Blocking findings. Per the governing instruction, this phase does
**not** automatically release. Recommends next:
**149O.20L.7O.3G — Post-Rollback Permission Integration Release and
Next-Capability Decision** — to decide between a narrow v0.4.1 quick
release containing the rollback Permission Broker gap closure, or
combining it with selected Plan A work before the next release, and to
reassess runtime preflight disclosure and rollback readiness/evidence
auto-generation against the newly broker-complete rollback path.

## 35. Deferred candidates (remain deferred, not implemented here)

- Runtime preflight disclosure
- Rollback readiness/evidence auto-generation
- Repository Intelligence internal consumption
- Advisory context consumption
- Runtime Enforcement consumption

No `src/pcae/` file was modified during this phase. Public v0.4.0
(tag `ea3f731e`) untouched. Runtime unchanged
(Observed/observe/unavailable). Private research repository
(`~/repos/pcae-deepseek-research`) and the article were not accessed.
