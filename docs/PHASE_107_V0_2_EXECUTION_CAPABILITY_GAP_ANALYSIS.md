# Phase 107A — v0.2 Execution Capability Gap Analysis

## Purpose

Enumerate, precisely, what execution-relevant capability already exists
in PCAE (as of `v0.1.0-rc1` and Phase 106M) versus what is still missing
before any governed autonomous execution (v0.2, Level 3 — see
`docs/V0_2_AUTONOMY_ROADMAP.md`) can exist, and lay out the risk
analysis, dependency graph, implementation order, and test strategy for
closing that gap safely.

## Scope

Documentation/gap-analysis only. Reviews existing design/evidence/
prototype artifacts already committed to this repository (permission
broker, shell gate, evidence bundle, decision engine, coordinator, no-go
registry, shared safety/authorization contract) and the current release/
repository-safety state (GitHub Release, branch protection). Produces no
new code, no new command, no new execution path.

## Non-Goals

No runtime enforcement; no autonomous execution; no real backend
invocation; no adapter execution; no subprocess execution beyond
existing lifecycle/test/docs/git-remote-verification command behavior;
no shell execution beyond that same boundary; no network calls outside
the existing Telegram outbound path and ordinary git remote/GitHub
verification; no shell interception; no Telegram inbound/polling; no
remote shell; no `/run`; no automatic apply/apply execution/patch
parsing; no commit/push authorization changes beyond the existing
governed lifecycle and the already-applied GitHub branch protection; no
real AI backend calls; no executable artifact-only invocation path; no
execution enablement flag or toggle; no cryptographic signing; no remote
attestation; no database-backed audit storage; no shell mediation; no
rollback execution, file mutation rollback, or automatic restore; no git
reset/checkout/revert execution. **No new git tag.** No final `v0.1.0`
tag. No new GitHub Release. No PyPI publication. No GitHub Packages
publication.

## Current v0.1 Release State

- `v0.1.0-rc1` tag: exists locally and on origin (created 106F, unchanged
  since).
- GitHub Release for `v0.1.0-rc1`: published, **prerelease**, sdist +
  wheel attached, checksums verified (106L). Unchanged by this phase.
- No final `v0.1.0` tag. No PyPI publication. No GitHub Packages
  publication.
- `.pcae-local/` remains ignored; no LinkedIn article/source-packet
  material committed (106J.1, 106K, 106L, 106M all re-confirmed this).

## Current Repository Safety State

- `main` is GitHub branch-protected (106M): 1 required approving PR
  review, stale-review dismissal, force-push blocked, deletion blocked,
  conversation resolution required, admin enforcement **off**
  (transitional).
- Contributor documentation (`CONTRIBUTING.md`,
  `docs/CONTRIBUTOR_WORKFLOW.md`), PR template
  (`.github/pull_request_template.md`), and `CODEOWNERS` all exist.
- The existing `governance` CI check (`.github/workflows/pcae-governance.yml`)
  runs on every PR and push to `main`; not yet a required status check.

## Current Capabilities Already Present

| Capability | Evidence | Status |
|---|---|---|
| Governed task/phase lifecycle | `pcae task`, `pcae phase`, `docs/V0_1_GOLDEN_WORKFLOW.md` | Present, stable |
| Report trust validator | `src/pcae/core/phase_report_trust.py` | Present, stable |
| Report trust hard-fail gates | 105D (`pcae phase complete` hard-fails on incomplete/invalid reports by default) | Present, stable |
| Phase-report trust CLI | `pcae phase-report trust`, `pcae phase-report show --trust` | Present, stable |
| Task-finish report/notification integration | `pcae task finish --commit` (105C.1/105D/106H trust-gate symmetry) | Present, stable |
| Golden workflow | `docs/V0_1_GOLDEN_WORKFLOW.md` | Present, documented, tested |
| Package/install smoke validation | 106D packaging tests; 106L rebuild + smoke-install | Present, re-verified every release phase |
| GitHub Release publication | 106L, verified checksums, prerelease | Present |
| Branch protection and PR-first contributor docs | 106M, applied via `gh api`, live-verified | Present |
| No-go registry | `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (17 frozen entries, RE-NOGO-001–017) | Present, frozen (104B) |
| Shared safety/authorization contract | 12 authorization flags (all `False`), 5 safety flags (all `True`) | Present, frozen (104) |
| Evidence-only runtime-readiness artifacts | Permission broker (87–91), shell gate (87–95) — both prototype/simulation only | Present, evidence-only |
| Decision/coordinator design artifacts | Evidence bundle (101), decision engine (102), coordinator (103) — contract-frozen, evidence-only | Present, design-only |
| Telegram outbound | `pcae notify status`; no inbound handler anywhere in `core/notifications.py` | Present, outbound-only |
| `fast_green` 4390/4390 | Re-verified every phase since 106D | Present, stable baseline |
| Task-memory clean | `pcae doctor task-memory` | Present, stable |
| Push-check clean | `pcae push check` | Present, stable |
| Post-RC audit/repair/verification cycle | 106G (audit) → 106H (repair) → 106I (live-CLI re-verification) | Present, demonstrates the process actually catches real bugs |
| Effectiveness evaluation framework | `docs/V0_1_EFFECTIVENESS_EVALUATION_FRAMEWORK.md` (106K) | Present, not yet applied to v0.2 work |

## Missing Capabilities for Autonomy

| Capability | Why It's Missing | Blocking No-Go |
|---|---|---|
| Actual runtime enforcement | Permission broker/shell gate are prototypes/simulations only; no code path enforces a real decision against a real action | RE-NOGO-001 |
| Permission broker enforcement implementation | `pcae permission-broker` exists as design/simulation; no real allow/deny/human_review decision gates a real action | RE-NOGO-001, RE-NOGO-002 |
| Command mediation | No code path intercepts and mediates a command before it runs | RE-NOGO-005 |
| Shell/subprocess/network gate | Narrow shell gate (93) is a prototype with an audit evidence model, not an enforced gate | RE-NOGO-005 |
| Backend invocation boundary | No real AI backend is ever called by PCAE itself | RE-NOGO-003 |
| Adapter invocation boundary | No adapter execution exists; adapter design docs are evidence-only | RE-NOGO-004 |
| Execution enablement model | No flag/toggle exists yet (intentionally — RE-NOGO-010 requires designing this explicitly, default off) | RE-NOGO-010 |
| Human approval enforcement | No gate requires and verifies a human clicked "approve" before an action runs | (new; not yet in registry as an implemented gate) |
| Durable audit persistence | Current audit evidence is Markdown/JSON report artifacts, not a persistent, queryable, append-only store | RE-NOGO-009 |
| Rollback execution governance | Rollback/promote commands are evidence-only design tracks (per `docs/RELEASE_HANDOFF_V0_1_RC1.md`'s "v0.2 Autonomy Boundary" note); no real rollback path exists | RE-NOGO-007 |
| Emergency stop/abort | No abort mechanism exists for an in-progress mediated action | RE-NOGO-015 |
| Execution sandboxing model | Not designed — what environment would a mediated shell/backend/adapter call actually execute in | (new) |
| Artifact provenance/signing, if needed | No cryptographic signing convention exists in this repository (confirmed absent, by design, in 106F) | Not required for v0.2 per this roadmap; revisit if release-artifact integrity requirements change |
| Output capture/redaction | No mechanism captures/redacts action output before it reaches audit records or Telegram | RE-NOGO-016 |
| Telegram inbound command gateway, if desired | Explicitly out of scope; outbound-only remains the design (RE-NOGO-013) unless a dedicated future phase gates it | RE-NOGO-013 |
| Multi-agent orchestration execution policy | Coordinator (103) is contract-frozen and evidence-only; no execution policy exists for it yet | (future; post-Level-3) |
| Production safety proof | RE-NOGO-011 requires an end-to-end safety proof that does not exist yet for any execution boundary | RE-NOGO-011 |
| PR-compatible governed development workflow | If `enforce_admins` is ever turned on, the current governed lifecycle's final push step (`pcae push`) needs a documented PR-based equivalent — not yet designed | (new; addressed by 107D) |

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Jumping directly to broad autonomous execution (Level 4/5) without proving Level 3 first | Would be high if attempted | Severe — unreviewed/unmediated actions on a real repository | This roadmap explicitly targets Level 3 first and stages 108A–115A before any execution is enabled |
| Permission broker enforcement introduced without adequate test coverage | Medium if rushed | High — a broker bug could allow an action that should have been denied | 108B (contract freeze) and 108C (hardening) are separate phases from 108A specifically so enforcement isn't declared done on first pass |
| Shell/backend/adapter mediation shipped "enabled by default" | Low if roadmap is followed | Severe | Explicit requirement: 109B/110A/110B are all "disabled by default" |
| Durable audit persistence introduces a new dependency (database) prematurely | Medium | Medium — added operational complexity, possible v0.1 simplicity regression | Roadmap explicitly notes durable persistence does not require a database; 112A should decide the simplest sufficient design |
| Rollback governance implemented without emergency stop | Low if sequence is followed | High — a bad action could be underway with no way to interrupt it | 114A (emergency stop) is sequenced before 115A (first execution demo), and 113A (rollback) precedes 114A |
| Branch protection (`enforce_admins`) tightened mid-v0.2-implementation without a workflow plan | Medium — likely to happen eventually | Medium — could stall a phase mid-work if the governed push step suddenly requires a PR | 107D is scheduled early (before 108A) specifically to solve this in advance |
| Existing evidence-only prototypes (permission broker, shell gate, decision engine, coordinator) get treated as "already implemented" and rushed to enforcement | Medium | High — these are real design assets, but none of them enforce anything today | This document explicitly separates "present" (design/evidence) from "missing" (real enforcement) for each one |

## Dependency Graph

```
107A (this phase: roadmap/gap analysis)
  └─> 107B (v0.2 contract freeze)
        └─> 107C (no-go gate freeze)
              └─> 107D (PR-compatible workflow design)
                    └─> 108A (permission broker enforcement impl)
                          └─> 108B (broker contract freeze)
                                └─> 108C (broker hardening)
                                      └─> 109A (shell/subprocess mediation design)
                                            └─> 109B (mediation prototype, disabled by default)
                                                  └─> 109C (mediation hardening)
                                                        ├─> 110A (backend invocation boundary, disabled by default)
                                                        └─> 110B (adapter invocation boundary, disabled by default)
                                                              └─> 111A (human approval enforcement gate)
                                                                    └─> 112A (durable audit store)
                                                                          └─> 113A (rollback execution governance)
                                                                                └─> 114A (emergency stop / abort)
                                                                                      └─> 115A (first human-approved bounded execution demo)
```

Every arrow represents a hard prerequisite, not just a suggested order:
none of 109A–110B may begin before 108C is complete and tested; 115A may
not begin before 111A–114A are all complete and tested.

## Implementation Order

Matches the dependency graph above exactly — see
`docs/V0_2_AUTONOMY_ROADMAP.md`'s "Recommended Phase Sequence" table for
the phase-by-phase list with names.

## Test Strategy

- Every implementation phase (108A onward) adds focused unit tests for
  the specific capability introduced, run alongside — never instead of —
  the existing `fast_green` regression (4390/4390 floor).
- Enforcement-boundary phases require live-CLI verification in an
  isolated scratch repository, not just unit tests, matching the standard
  106I established when verifying the 106H trust-gate repair.
- Each phase's "hardening" follow-up (108C, 109C) exists specifically to
  add edge-case and adversarial-input test coverage after the initial
  implementation phase, mirroring the existing project pattern of
  design → prototype → hardening seen in the permission
  broker/shell-gate/evidence-bundle/decision-engine/coordinator tracks
  (87–103).
- No phase may claim a capability "implemented" while `execution_allowed`
  for that capability is anything other than an explicit, narrowly
  scoped, tested `True` — default is off for every new capability.

## No-Go Gates

This gap analysis defers to, and does not duplicate, the frozen registry
at `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (RE-NOGO-001 through
RE-NOGO-017). The "Missing Capabilities" table above maps each gap to its
corresponding registry entry where one exists, and flags gaps that are
new (human approval enforcement, execution sandboxing, PR-compatible
workflow) for the registry to be extended in 107C.

## Branch-Protected Main Implications

- All v0.2 documentation/design/implementation phases must go through the
  same governed PCAE lifecycle (`pcae commit implementation`, `pcae task
  finish --commit`, `pcae push`) used throughout v0.1 and 106M.
- Today, the repo owner (admin) can still push directly via `pcae push`
  because `enforce_admins: false` — this phase's own push will succeed
  the same way 106M's did (logged by GitHub as an admin bypass of the
  PR-required rule).
- This will not necessarily remain true. If/when `enforce_admins: true`
  is adopted (a distinct, future, explicitly-approved decision — not
  performed here or in 106M), the governed lifecycle's final "push
  directly to `main`" step no longer works for anyone, including the
  repo owner. **107D exists specifically to design what replaces it**
  (e.g., `pcae push` targeting a feature branch + an automated or
  semi-automated PR-open-and-merge step) before that day arrives.
- No v0.2 roadmap phase may bypass branch protection, force-push, or use
  `--no-verify` to route around it.

## Recommended Next Phase

**107B — v0.2 Autonomy Contract Freeze.**
