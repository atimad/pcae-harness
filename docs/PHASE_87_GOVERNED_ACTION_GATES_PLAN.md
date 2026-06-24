# Phase 87 Governed Action Gates Plan

## 1. Purpose

Define the safe transition from Phase 86's read-only project intelligence to governed
action gates. This plan establishes boundaries, candidate gates, safety principles,
threat model, approval requirements, staged roadmap, and explicit non-goals before
any gate implementation starts.

## 2. Scope

Planning only. This artifact defines what should be built, in what order, with what
safeguards. It does not implement action gates, create storage, modify source code,
or add tests.

## 3. Non-Goals

- Implementing any action gate, permission broker, shell gate, or storage.
- Creating `.pcae` storage, generated cache, or machine-readable state files.
- Modifying source code, tests, README, or existing artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.
- Granting permission or authorization from this planning artifact.

## 4. Starting Point from Phase 86

Phase 86 delivered the complete read-only project-intelligence stack:

| Layer | Command | Phase |
|-------|---------|-------|
| Artifact Index | `pcae artifact-index --json` | 86C |
| Memory Snapshot | `pcae memory-snapshot --json` | 86D |
| Governance Timeline | `pcae governance-timeline --json` | 86E |
| Decision Log | `pcae decision-log --json` | 86F |
| Risk Register | `pcae risk-register --json` | 86G |
| Project State | `pcae project-state --json` | 86H |

Additional Phase 86 deliverables:

- 86A: Implementation roadmap
- 86B: Data model and storage design
- 86I: Integration tests (38 tests, cross-layer consistency verified)
- 86J: Documentation update (README section, stack summary)
- 86K: Final verification (readiness_decision=ready_for_phase_87_planning)

Test suite: 7122 tests, 0 failures.

## 5. Why Read-Only Intelligence Is Not Authorization

Phase 86 commands observe and report governance state from committed evidence. They
do not grant permission, authorize execution, approve adoption, authorize commits,
authorize pushes, or invoke agents. Phase 87 must preserve that boundary while
designing any future action gate.

Key distinctions:

| Observation | Authorization |
|-------------|---------------|
| "Phase 86G is completed" | "You may start 86H" |
| "Next safe action: 86I (recommendation)" | "86I is approved for execution" |
| "Risk is accepted" | "Risk is mitigated" |
| "No blockers detected" | "Proceed without review" |
| "Git status is clean" | "Push is authorized" |

Phase 87 must never conflate these. Every gate must explicitly evaluate evidence and
produce a decision separate from the read-only observation.

## 6. Phase 87 Design Principles

1. **Observation is not authorization.** Reading project-state does not permit action.
2. **Recommendation is not permission.** `next_safe_actions` are suggestions, not gates.
3. **Read-only intelligence remains non-authorizing.** Existing Phase 86 commands must
   not gain write authority.
4. **Every action gate requires explicit scope.** A gate must know exactly what it is
   evaluating and what it may allow or deny.
5. **Every action gate requires evidence.** A gate must cite specific artifacts, commits,
   or command outputs as the basis for its decision.
6. **Every action gate requires deny-by-default posture.** Missing evidence, unknown state,
   or ambiguous conditions result in denial.
7. **High-risk actions require human approval.** Backend invocation, adoption execution,
   commit, push, rollback, and storage writes require human sign-off.
8. **Accepted risk is not mitigation.** Gates must not treat accepted risk as resolved.
9. **Must-never-repeat controls remain enforceable.** Gates must refuse actions that violate
   must-never-repeat boundaries.
10. **Storage/write behavior requires a separate gate.** No storage until a storage gate
    phase explicitly approves it.
11. **Permission broker remains future until explicitly scoped.** Planning a broker does not
    authorize building one.
12. **Shell gate remains future until explicitly scoped.** Planning a gate wrapper does not
    authorize intercepting commands.

## 7. Threat Model

| # | Threat | Impact | Mitigation |
|---|--------|--------|------------|
| AG-1 | project-state recommendation treated as permission | Agent proceeds without approval | Gates must produce explicit allow/deny decisions, not consume recommendations |
| AG-2 | next_safe_action executed automatically | Unauthorized action occurs | next_safe_actions remain labeled as recommendations; no gate may treat them as approvals |
| AG-3 | Accepted risk treated as mitigation | Risk assumed resolved | Gate must check risk_status explicitly; accepted ≠ mitigated |
| AG-4 | Stale signal ignored | Stale governance data drives current action | Gate must check freshness; stale evidence requires review |
| AG-5 | Must-never-repeat control bypassed | Forbidden pattern repeats | Gate must check must_never_repeat_controls before allowing action |
| AG-6 | Write-capable gate added too early | Scope creep into unverified territory | Rollout requires dry-run phases before any write-capable gate |
| AG-7 | Storage created without storage gate | Uncontrolled persistent state | Storage requires explicit storage gate phase approval |
| AG-8 | Permission broker implemented without contract | Unscoped permission authority | Broker requires architecture design phase before implementation |
| AG-9 | Shell gate implemented without command policy | Unscoped command interception | Shell gate requires command taxonomy and policy design first |
| AG-10 | Agent/backend invocation allowed from read-only output | Unauthorized invocation | Read-only outputs do not authorize invocation; gate must have independent approval |
| AG-11 | Commit/push authorized from summary text | Unauthorized repository mutation | Commit/push require explicit gate evaluation, not text parsing |
| AG-12 | Human approval boundary skipped | Safety boundary bypassed | High-risk gates must fail-closed without human sign-off |
| AG-13 | Gate decision persisted without audit trail | Unverifiable gate history | Future gate decisions must be logged with evidence |
| AG-14 | Gate scope wider than task contract | Action exceeds authorized scope | Gate must check task contract allowed/forbidden files |
| AG-15 | Read-only command silently gains write authority | Boundary collapse | Existing commands must never be modified to write; new commands required |

## 8. Candidate Action Gates

These are candidate gates for future Phase 87 phases. None are implemented in 87A.

| Gate | Purpose | Risk Level | Human Required |
|------|---------|------------|----------------|
| `task_start_gate` | Evaluate whether a new task/phase may begin | medium | no (dry-run first) |
| `scope_check_gate` | Evaluate whether proposed changes are within task scope | medium | no |
| `backend_invocation_gate` | Evaluate whether a backend may be invoked | critical | yes |
| `prompt_send_gate` | Evaluate whether a prompt may be sent | critical | yes |
| `capture_acceptance_gate` | Evaluate whether captured output is acceptable | high | depends |
| `intake_review_gate` | Evaluate whether intake classification is valid | high | depends |
| `adoption_approval_gate` | Evaluate whether an adoption candidate may be applied | critical | yes |
| `source_mutation_gate` | Evaluate whether source code may be modified | high | depends on scope |
| `test_mutation_gate` | Evaluate whether test code may be modified | medium | depends on scope |
| `commit_gate` | Evaluate whether a commit may be created | high | yes |
| `push_gate` | Evaluate whether a push may proceed | high | yes |
| `rollback_gate` | Evaluate whether a rollback may proceed | high | yes |
| `storage_write_gate` | Evaluate whether storage may be written | high | yes |
| `permission_broker_gate` | Evaluate runtime permission requests | critical | yes |
| `shell_command_gate` | Evaluate shell commands before execution | critical | yes |

## 9. Gate Decision Model

Future gates should produce explicit decisions from these values:

| Decision | Meaning |
|----------|---------|
| `allow` | Action may proceed |
| `deny` | Action is refused |
| `requires_human_review` | Human must approve before proceeding |
| `requires_more_evidence` | Additional evidence needed |
| `blocked_by_risk` | Active risk prevents action |
| `blocked_by_scope` | Action exceeds task contract scope |
| `blocked_by_lifecycle_state` | Lifecycle state does not permit action |
| `blocked_by_missing_artifact` | Required artifact is missing |
| `blocked_by_must_never_repeat_control` | Action violates must-never-repeat boundary |
| `unknown` | Gate cannot determine; defaults to deny |

The default decision when evidence is missing or ambiguous must be `deny`.

## 10. Gate Input Sources

Future gates may read from:

| Source | Type |
|--------|------|
| `pcae project-state --json` | Integrated project state |
| `pcae risk-register --json` | Active/accepted/stale risks |
| `pcae decision-log --json` | Decision records and authorization flags |
| `pcae governance-timeline --json` | Event history |
| `pcae memory-snapshot --json` | Phase/lifecycle/roadmap state |
| `pcae artifact-index --json` | Artifact evidence |
| Task contract | Allowed/forbidden files, scope |
| `git status` | Repository state |
| `pcae health/check/doctor/push` | PCAE command outputs |
| Human approval | Explicit sign-off |

**Reading these sources does not itself authorize action.** A future gate must
explicitly evaluate them and produce a gate decision.

## 11. Gate Output States

A gate evaluation should produce a structured output including:

- gate_id
- gate_type
- decision (from decision model above)
- evidence_consulted (list of sources read)
- evidence_missing (list of sources expected but absent)
- blocking_conditions (list of conditions that caused denial)
- human_review_required (boolean)
- task_contract (reference)
- timestamp
- safety_notes

## 12. Human Approval Boundaries

Human approval is required for future:

| Action | Human Required |
|--------|----------------|
| Backend invocation | yes |
| Prompt sending | yes |
| Source mutation (outside explicit scope) | yes |
| Test mutation (outside explicit scope) | yes |
| Adoption execution | yes |
| Commit | yes |
| Push | yes |
| Rollback | yes |
| Storage write | yes |
| Permission broker activation | yes |
| Shell gate activation | yes |
| Accepted-risk override | yes |
| Must-never-repeat override | yes |

## 13. Storage/Cache Policy

- Phase 87A creates no storage, cache, or `.pcae` persistent state.
- Any future write-capable storage requires a separate storage gate phase.
- Read-only command outputs remain stdout-only unless explicitly changed by a governed
  future phase.
- Generated cache must never become authoritative. Repo artifacts remain source of truth.

## 14. Permission Broker Relationship

The permission broker is a future architecture direction, not implemented in 87A.

If implemented in a future phase, it would:

- Evaluate proposed actions before shell/backend execution.
- Use explicit command/action policy (not implicit project-state consumption).
- Deny by default.
- Log all decisions with evidence.
- Require human review for high-risk actions.
- Not rely on read-only project-state recommendations as direct permission.

Implementation requires a dedicated architecture design phase (proposed 87H) before
any broker code is written.

## 15. Shell Gate Relationship

The shell gate is a future enforcement layer, not implemented in 87A.

If implemented in a future phase, it would:

- Intercept or wrap shell commands before execution.
- Distinguish read-only commands from mutating commands.
- Understand task scope, lifecycle state, and approved files.
- Block raw push, force push, hook bypass normalization, and unauthorized writes.
- Log all allowed/blocked decisions.

Implementation requires a dedicated architecture design phase (proposed 87I) before
any gate wrapper code is written.

## 16. CLI/Action Relationship

- Existing Phase 86 commands remain read-only. They must not gain write authority.
- Future gate commands must use separate names or explicit subcommands (e.g.,
  `pcae gate evaluate --scope`, not modification of `pcae project-state`).
- No existing read-only command should gain write authority silently.
- Gate commands must be clearly distinguishable from observation commands.

## 17. Safety Invariants

These invariants must hold throughout Phase 87:

1. Read-only commands remain read-only.
2. `pcae project-state` remains non-authorizing.
3. Gate decisions must be explicit (allow/deny/blocked).
4. Deny by default when evidence is missing.
5. Human approval required for high-risk actions.
6. Must-never-repeat controls cannot be silently overridden.
7. Accepted risk cannot be treated as mitigation.
8. No storage/write behavior without explicit storage gate.
9. No backend invocation without backend invocation gate.
10. No commit/push without commit/push gate.
11. No permission broker without architecture design phase.
12. No shell gate without architecture design phase.

## 18. Test Strategy

Future Phase 87 implementation phases should follow the Phase 86 test pattern:

- Each implementation phase adds tests for new behavior.
- Integration tests validate cross-gate consistency.
- Tests assert deny-by-default behavior.
- Tests assert human-required flags on high-risk gates.
- Tests assert no unauthorized file creation.
- Tests assert gate decisions are explicit and logged.
- `python -m pytest -n auto` remains the default test command.
- Existing Phase 86 tests must not regress.

## 19. Rollout Roadmap

Recommended Phase 87 sequence (planning only, no task contracts created):

| Phase | Deliverable | Type |
|-------|-------------|------|
| **87A** | Governed Action Gates Plan (this artifact) | planning |
| **87B** | Action Gate Taxonomy and Decision Model | design |
| **87C** | Read-Only Gate Evaluation Dry-Run | implementation (read-only) |
| **87D** | Scope Gate Prototype | implementation (read-only) |
| **87E** | Backend Invocation Gate Dry-Run | implementation (read-only) |
| **87F** | Adoption/Mutation Gate Dry-Run | implementation (read-only) |
| **87G** | Commit/Push Gate Dry-Run | implementation (read-only) |
| **87H** | Permission Broker Architecture Design | design |
| **87I** | Shell Gate Architecture Design | design |
| **87J** | Phase 87 Integration Tests | testing |

Key principles:

- Start with taxonomy/design before implementation.
- Dry-run (read-only evaluation) phases come before write-capable phases.
- Permission broker and shell gate get architecture design phases before implementation.
- Integration tests verify the gate stack before proceeding.

## 20. Deferred Items

| Item | Status | Rationale |
|------|--------|-----------|
| Write-capable action gates | deferred | Requires dry-run validation first |
| Persistent gate decision storage | deferred | Requires storage gate phase |
| Permission broker implementation | deferred | Requires architecture design (87H) |
| Shell gate implementation | deferred | Requires architecture design (87I) |
| Generated cache as gate input | deferred | Cache must never become authoritative |
| Automatic next-phase execution | deferred | Requires human approval boundary preservation |
| Agent/backend invocation from gate output | deferred | Requires backend invocation gate (87E) |

## 21. Recommended Next Phase

**87B — Action Gate Taxonomy and Decision Model.**

87B should define the complete action gate taxonomy, decision model schema, input/output
contracts, and evaluation semantics. Design only — no implementation. This provides the
shared vocabulary and model that all subsequent 87-series phases will reference.

---

phase_87_plan_name=phase_87_governed_action_gates_plan
phase_87_plan_version=0.1
phase_87_plan_status=draft_documented
implementation_status=not_started
gate_implementation_status=not_started
permission_broker_implementation_status=not_started
shell_gate_implementation_status=not_started
storage_implementation_status=not_started
candidate_gates_defined=15
threat_model_entries=15
safety_invariants=12
human_approval_boundaries=13
deferred_items=7
recommended_next=87B
backend_invocation_performed=false
