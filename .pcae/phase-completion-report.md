# Phase 149O.20L.7O.3T Complete — Real-Runtime Prerequisite Dependency and Trust-Boundary Hardening Plan

**Verdict: COMPLETE. READ-ONLY STRATEGIC PLANNING. NO SRC/PCAE MODIFIED. EXECUTION NOT ACTIVATED.**

Phase 149O.20L.7O.3T produced an evidence-derived dependency graph and
hardening plan for the transition from the verified production dry
adapter consumer (`pcae session bootstrap --compact --dry-runtime
--runtime-target <id>`, 149O.20L.7O.3S.2 / independently verified by
149O.20L.7O.3S.2.1) to a future human-authorized real-runtime dispatch,
without implementing or activating real execution.

**Phase-entry SHA:** `c7037b388bf5ea0f0713f6e534689816e9c4885b`.
**v0.4.3 public state:** unchanged, `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
**Runtime state:** `Observed` / `observe` / `unavailable`, unchanged at
phase entry and phase close. **Production dry consumer state:**
IMPLEMENTED, VERIFIED, PRODUCTION-CONSUMED (unchanged from 3S.2/3S.2.1).

## The 16 real-runtime prerequisites

Re-derived directly from `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`
(RPAC-001 v1.0) and the 3R classification
(`docs/PHASE_149O_20L_7O_3R_DETERMINISTIC_MOCK_DRY_RUNTIME_ADAPTER_IMPLEMENTATION_PLAN.md`,
line 93: "16 REAL-RUNTIME-PREREQUISITE"): RPAC-REQ-014, 028, 044, 045,
046, 047, 048, 057, 058, 059, 071, 072, 084, 086, 095, 097. All 16 appear
in the phase document (`docs/PHASE_149O_20L_7O_3T_...md`, Section 4)
with exact contract wording, current status (Section 5), and dependency
edges (Section 6). None is fully satisfied; all remain UNSTARTED,
PARTIALLY SATISFIED, or an explicit named gap.

## Dependency ordering

First unblocker: **RPAC-REQ-044** (Permission Broker request-shape
amendment). Hard serial spine: RPAC-044 -> RPAC-045/046 (Runtime
Enforcement real gate) -> RPAC-047 (RE/Shell-Gate division of labor) ->
RPAC-048 (Shell Gate enforcement) -> RPAC-057 (local CLI target) ->
RPAC-095 (first real adapter). Parallelizable now: RPAC-084
(credential-reference architecture), RPAC-086 (supply-chain pinning),
RPAC-097 (legacy-path retirement).

## First hard blocker: POL-005

Independently re-confirmed by direct source read of
`src/pcae/core/permission_broker_foundation.py` lines 489-518
(`ExecutionDisabledRule`): `if request.simulation_only: return
_not_triggered(...)`, else unconditional `DECISION_DENY` with reason
`"execution_boundary_unavailable"`. No `applicable_execution_classes`
override is declared, so the rule applies to every `execution_class`
(`none`, `mutation`, `shell`, `backend`, `adapter`, `rollback`)
unconditionally, matching its own docstring ("Unconditionally active by
construction (NG-025)"). This confirms and extends 3S.2.1's finding: it
is the structurally first blocker because nothing downstream in the
dependency graph is reachable while it unconditionally denies any
non-simulation request.

## PB action vocabulary and redesign options

Existing vocabulary (`permission_broker_foundation.py` lines 94-134):
action_types `read`, `source_mutation`, `docs_mutation`, `test_mutation`,
`commit`, `push`, `rollback`, `shell_command`, `backend_invocation`,
`adapter_invocation`; execution_classes `none`, `mutation`, `shell`,
`backend`, `adapter`, `rollback`. `adapter_invocation`/`adapter` is the
existing closest match for runtime dispatch but is confirmed
structurally insufficient (RPAC-REQ-044: no target/adapter/prompt-digest/
repository/effects/credentials/budget/idempotency binding). Three bounded
redesign options produced (phase document Section 41): (A) new explicit
`runtime_dispatch` permission action; (B) reuse `adapter_invocation` with
a simulation/real mode enum; (C) separate transport/network/process
permissions per effect class (RPAC-REQ-085-aligned). No option selected;
Option C is noted as most aligned with existing contract language and
the pre-existing fine-grained `RuntimeEnforcementEvidenceBundle`
vocabulary, at higher implementation cost.

## Human authority

Searched CHGR-001 (schema/artifact-only per its own README: "Not
implemented ... runtime consumption, or authority resolution"),
Interactive Workflow Confirmation (explicitly barred from populating
`approval_present` by RWMPC-REQ-023: "Confirmation is not approval"),
and phase/session approvals (too coarse). **No existing artifact
cleanly authorizes real runtime invocation. Classified
CONTRACT/AUTHORITY GAP** — no approval semantics invented. Three options
produced (Section 42): (A) new explicit runtime-invocation approval
record; (B) new CHGR record type/subject; (C) phase/session approval
binds invocation (rejected as too coarse, blurs the required
`registered != ... != authorized != dispatched` distinctions).

## Runtime Enforcement

Confirmed by direct source read of `src/pcae/core/backend_invocations.py`
(`RuntimeEnforcementCoordinator`/`RuntimeEnforcementEvidenceBundle`,
Phase 103A/101B): design-only, non-executing, non-authorizing, 0
production consumers; output vocabulary has no "granted"/"authorized"
terminal state at all (only `denied`/`fail_closed`/`blocked_by_*`/
`evidence_only`/`design_review_only`); `validate()` hard-asserts
`execution_available`/`execution_authorized`/`push_authorized` must be
`False`. Cannot evaluate a real adapter invocation today. Contract
evolution required; an adapter-specific projection into the existing
evidence-bundle vocabulary (which already declares
`adapter_execution_authorized`/`network_authorized`/`subprocess_authorized`/
`shell_authorized`/`mutation_authorized`) appears more economical than
building a duplicate engine — no duplicate enforcement engine
recommended.

## Shell Gate

Confirmed simulation-only: `src/pcae/core/shell_gate.py` module
docstring, "Never executes command text. Never grants authorization."
Classification: **MANDATORY** (or an enforcing equivalent, per
RPAC-REQ-047's "Shell Gate or an equivalent") before any local CLI
runtime dispatch that constructs shell text/pipelines/`shell=True`; a
fixed-argv-only adapter still requires an equivalent enforcing
process-construction policy.

## Process supervision / environment isolation / filesystem containment

Process supervision: none of process ownership, PID/tree tracking,
timeout, cancellation, detached-descendant containment exist today (no
`subprocess.Popen`/process-group code found in the runtime-adapter
modules); process ownership, timeout, and detached-descendant
containment are hard blockers before any local CLI dispatch.
Environment isolation: no env allowlist or secret-injection mechanism
exists; depends on the missing credential-reference architecture.
Filesystem containment: no runtime-specific sandboxing exists; an
isolated `git worktree` (a pattern PCAE already uses for its own
disposable verification work) is recommended as the lowest-cost first
containment mechanism.

## Network requirements

No PB action or execution_class for network egress exists at all
(confirmed absent from `KNOWN_ACTION_TYPES`/`KNOWN_EXECUTION_CLASSES`).
Must become an explicit, default-denied PB action before any API/
provider adapter (RPAC-REQ-085). A local CLI adapter making no network
calls needs no such action, reinforcing local CLI as the lower-
trust-complexity first target.

## Credential-reference architecture

Confirmed absent entirely from `src/pcae` (searched broadly; the term
exists only in RPAC-001 contract prose). RPAC-REQ-084 itself names this
"an explicit blocker for a real authenticated adapter." Classified: hard
dependency, missing entirely. No secret access was performed in
confirming this.

## Provider/model identity

Minimum trusted source must be PCAE-owned configuration
(`RuntimeTargetConfiguration`), never a runtime-reported claim, per
RPAC-REQ-006/007/008/028 and directly corroborated by 3S.2.1's
provenance-spoofing tests (adapter_id never changed despite 5 spoofed
agent_id values).

## Local CLI vs. API comparison

Local CLI chain: RPAC-048 -> 057 -> 058 -> process supervision ->
filesystem containment. API chain: RPAC-059 -> 084 (shared) -> network
policy -> cost/budget governance. Shared blockers: RPAC-044, 045/046,
084, 086, human authorization. Local CLI has strictly fewer unique
blockers and needs no network PB action for a no-network executable.

## Invocation persistence/recovery, at-most-once/retry

`RuntimeInvocationStore` (`src/pcae/core/runtime_invocation.py`) uses
atomic tmp-then-`Path.replace()` writes; before-dispatch durability
exists, after-dispatch uncertainty is entirely unaddressed (no dispatch
layer or "dispatch attempted" marker exists yet). Desired guarantee:
**at-most-once** dispatch attempt with retry requiring fresh human
authorization — **exactly-once is explicitly not claimed** as possible
for local-process/network dispatch. Retry taxonomy already specified in
contract (RPAC-REQ-071/072) with no implementation yet; retryable classes
(pre-dispatch unavailability, confirmed-non-accepted rate-limiting,
confirmed-non-delivered transport failure, pre-effect timeout) vs.
non-retryable (unknown delivery, runtime mutation, malformed/conflicting
completion, ambiguous process termination).

## Result capture / generic intake / mutation trust

Result must remain untrusted (RPAC-REQ-084, corroborated by 3S.2.1's
finding that `build_intake_handoff` never calls the actual
acceptance/ingest entry point). Existing Stage-B intake-candidate builder
already consumes any `RuntimeInvocationResult`-shaped object without
new trust-contract evolution for evidence production; the acceptance
half (`validate_and_ingest_intake_candidate`) remains a separate,
unmodified, human/governance-gated step. File-based/patch-based intake
is the preferred return path over direct worktree mutation by the
runtime. Explicit chain preserved: runtime produced file != trusted
source != accepted change != authorized commit; all existing
intake/review/promotion gates (114A-114R) remain intact.

## Cancellation / detached-process risk

Local CLI: SIGTERM then escalation, mandatory bounded timeout. API:
client-side cancellation may not stop provider-side completion/billing
("unknown delivery" retry-taxonomy bucket). Detached/background process
risk: no process-group/session containment exists anywhere in
`src/pcae` today; mandatory before any local CLI execution.

## Threat model

Full 11-row threat matrix produced in the phase document (Section 37):
malicious prompt/context, provider compromise, arbitrary shell/tool
behavior, filesystem escape, network exfiltration, credential leakage,
process escape, result spoofing, replay/duplicate execution, cost abuse
— each mapped to current exposure and existing/missing mitigation.

## 2 MUST-FIX findings recovered (3S.2.1)

Recovered verbatim from
`docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md`
Section 62: (1) malformed non-mock adapter `collect()` result crashes
`simulate_invocation` with an uncaught `AttributeError` inside
`RuntimeInvocationStore.write_result` rather than producing a clean
`FAILURE_MALFORMED_RESULT`, unreachable today because the only
registered adapter is the mock (which always returns well-formed
results); becomes a de facto blocker the moment a second, real adapter
is registered. (2) `RuntimeInvocationStore._invocation_dir`/
`_write_create_only` perform no path-traversal sanitization on
`invocation_id`, unreachable today because both public production entry
points always use internally `new_invocation_id()`-generated IDs
(`f"inv-{uuid.uuid4().hex}"`); becomes load-bearing only if a future
surface accepts a caller-supplied `invocation_id`. Neither repaired this
phase (not separately authorized).

## Runtime inspect limitation disposition

`TRUTHFUL_WITH_LIMITATION` carried forward unchanged; `pcae runtime
inspect` not modified. Determined the limitation must be repaired
**before the first real adapter is registered** (not before release, not
"after registration," not "not required") — an operator relying on the
tool to assess real-execution availability needs the dry/real
distinction discoverable once a real adapter exists.

## Failure-before-effect / durable-before-effect / TOCTOU

Mandatory pre-spawn/pre-network-send/pre-billing/pre-mutation check
lists produced (Section 45). Durable-before-effect fields identified:
invocation ID, target, prompt hash (new), authority reference (new), PB
decision + digest (new), Runtime Enforcement decision + digest (new),
repo/task binding — secrets never persisted. TOCTOU analysis: HEAD,
prompt hash, and adapter/target configuration must be snapshot-bound;
task state, credential/account validity, executable identity, and
policy/decision freshness must be freshly re-checked immediately before
dispatch, not merely snapshot-bound.

## Adapter config trust / executable trust / API trust / cost governance

Adapter configuration must be repository-local/admin-controlled, never
accepted from untrusted task/model content. Executable trust for v1:
resolved/pinned executable with hash verification, not bare PATH lookup
(RPAC-REQ-086). API trust deferred (endpoint pinning, TLS reliance,
model allowlist, non-self-asserted provenance) until an API adapter is
actually built. Cost/budget governance: classified as later hardening
for the local-CLI-only v1 path, but a hard prerequisite before any API
adapter (no mechanism exists today).

## Audit / explainability

Audit fields required: requester, repo/task, prompt hash, target,
authority, PB decision, Runtime Enforcement decision, dispatch-attempt
marker, process/provider identity, outcome, result-intake reference. The
existing atomic `RuntimeInvocationStore` document model is the correct
extension point — no new mechanism needed, only new fields, and PB/RE
decisions must start flowing into it to answer all six explainability
questions posed by the instructions.

## Restart/recovery, local-CLI, and API/provider trust matrices

Full matrices produced in the phase document (Sections 55-57), covering
6 crash points and 7 local-CLI / 6 API-provider trust concerns each with
current control, gap, and blocking-status.

## 16-prerequisite matrix and dependency DAG

Full matrix (Section 58) and human-readable DAG (Section 59) produced,
covering current state, dependency, contract/implementation/security
work, and priority for all 16 requirements.

## Minimum viable real-runtime path / initial scope restrictions

One explicit target (no fallback), one fresh invocation-scoped human
authorization, no automatic retry, one runtime/one repo/one task,
bounded timeout, bounded sanitized environment, untrusted result routed
through the existing unmodified intake/review pipeline. v1 restrictions:
local CLI only, no API providers, no parallel invocations, no automatic
retries, no background/detached execution, no unattended scheduling, no
multi-repo, explicit human approval every invocation.

## First real adapter recommendation

Ranked (Section 30, per RPAC-REQ-095's own explicit sequencing): (1)
generic local fixed-argv executable with a deterministic non-AI fixture
— lowest trust complexity, exercises the full process-supervision/
containment/Shell-Gate chain independent of AI-specific concerns; (2)
Codex CLI; (3) Claude-local; (4) API/OpenRouter-style provider (highest
trust complexity, ranked last).

## Release implications

No release decision made. The real-runtime chapter is a plausible v0.5.0
candidate given the magnitude of the capability shift, but no version is
frozen; this is a planning placeholder only.

## Exact next phase

**"Real Runtime Dispatch Authority and Permission Contract
Architecture"** — evidence-derived: PB (POL-005/RPAC-044) is
structurally the first blocker, but RPAC-REQ-045 requires Runtime
Enforcement to sit "after human approval ... and Permission Broker
permission" as adjacent, interdependent gates in the same short chain —
so PB redesign and the human-authority artifact must be designed
together, not sequentially. This phase recommends a combined
contract-design phase (still no implementation): select a PB redesign
option, select a human-authority artifact design, and define the binding
between them. **Human decision required.**

## Production source modified / execution activated / external invocation

**Production source modified: NO** (git diff confirms 0 `src/pcae`
files touched — only `docs/`, `PROJECT_STATUS.md`, `CHANGELOG.md`, and
task-lifecycle/report files). **Execution activated: NO.** **External
runtime invocation: NONE.** Runtime remains `Observed`/`observe`/
`unavailable`, unchanged throughout. **Version/release: unchanged**,
v0.4.3 still resolves to `63580893b1de4782a694ab802ff7bdebdf29b0e6`.
Article remains STOPPED; private research repository
(`~/repos/pcae-deepseek-research`) untouched, not inspected.

## Checks run

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings limited to pre-existing
`tasks/DONE.md` synchronization debt (unrelated to this phase). `pcae
push check`: clean. `pcae runtime inspect`: unchanged
(`not_implemented`/`Observed`/`observe`/`unavailable`). Telegram: configured,
enabled, outbound-ready.

## Commits, pushed, origin/main..HEAD

Commits and push state recorded in `.pcae/phase-completion-metadata.json`
(`phase_commits`, `pushed_status`, `origin_main_head`,
`origin_main_head_count`).

**REAL-RUNTIME PREREQUISITE PLAN: COMPLETE**
**PRODUCTION DRY RUNTIME: VERIFIED / CONSUMED**
**REAL-RUNTIME READY: NO**
**FIRST HARD BLOCKER: POL-005 (ExecutionDisabledRule) — unconditional deny of any non-simulation request**
**POL-005: intentional temporary safeguard, denies unconditionally until COMP-002 (execution boundary) is implemented and verified**
**PB REAL-DISPATCH SEMANTICS: CONTRACT WORK REQUIRED (3 bounded options produced, none selected)**
**HUMAN AUTHORITY: CONTRACT/AUTHORITY GAP — no existing artifact authorizes real runtime invocation**
**RUNTIME ENFORCEMENT: design-only, non-authorizing, 0 production consumers — contract evolution or adapter-specific projection required**
**PROCESS SUPERVISION: absent — hard blocker before local CLI**
**ENVIRONMENT CONTAINMENT: absent — depends on missing credential-reference architecture**
**INVOCATION RECOVERY: atomic before-dispatch durability exists; after-dispatch uncertainty unaddressed; at-most-once (not exactly-once) is the achievable guarantee**
**16 PREREQUISITES: DEPENDENCY-ORDERED (see Section 59 DAG)**
**FIRST REAL ADAPTER: generic local fixed-argv executable, non-AI deterministic fixture**
**EXECUTION ACTIVATION: NOT PERFORMED**
**NEXT PHASE: Real Runtime Dispatch Authority and Permission Contract Architecture**
**HUMAN DECISION: REQUIRED**
