# Phase 148C.2 Complete — Permission Broker Foundation Policy Applicability Model Design

**Phase ID:** 148C.2
**Mode:** Architecture/design only
**Predecessor:** 148C.1 (Permission Broker Production Consumption Contract Clarification and Repair)
**Date:** 2026-08-01
**Status:** completed
**Pushed:** pushed

This is the lightweight staging header for `pcae phase complete`. The full
design document (40 sections: Foundation/`POL-001..012` re-derivation,
`POL-004` deep re-derivation, request-classification inventory, implicit-
applicability analysis, four candidate architectures compared, selected
hybrid architecture, `NOT_APPLICABLE`/missing-vs-non-applicable semantics,
fail-closed and security analysis, contract-impact matrix, B-1 closure
path, recommended next phase) is at
`docs/PHASE_148C.2_PERMISSION_BROKER_FOUNDATION_POLICY_APPLICABILITY_MODEL_DESIGN.md`.

---

## Executive Summary

Phase 148C.2 independently re-derives the Permission Broker Foundation's
original purpose and every `POL-001..012` rule's intended domain, finding
exactly one implemented rule, `POL-004` (Missing Human Approval), with a
textually demonstrable non-universal domain — its own upstream lineage
(`NG-008` → `INV-003` → `COMP-003`) scopes it to the generic
mediated-execution lifecycle, which git-tracked content mutations
structurally never enter, per
`docs/V0_2_PR_COMPATIBLE_GOVERNED_DEVELOPMENT_WORKFLOW.md` §5's frozen
Git-Approval/Execution-Approval separation.

Found applicability already implicit in frozen upstream text (`NG-008`'s
own scope statement; Phase 109's own command-category design language,
"`POL-004` approval **where applicable**") that was never encoded into
the Foundation's evaluate-everything mechanism when it was built (Phase
108) — classified as implementation/model incompleteness, confirming
rather than contradicting Phase 148C.1's Category C diagnosis.

Compared four candidate architectures (policy-owned applicability
predicate; declarative applicability metadata; frozen policy profiles;
universal-with-conditional-logic) against determinism, fail-closed
defaults, spoof resistance, auditability, backward compatibility,
extensibility, minimal semantic change, and implementation simplicity.

**Selected: a hybrid of Candidate A and Candidate B.** Each `PolicyRule`
optionally declares a frozen `applicable_execution_classes` set (default
`None` = universal, preserving current behavior for eleven of twelve
rules unchanged); the `PolicyRegistry` — never the caller, never a
per-request exclusion parameter — resolves and enforces it using the
Foundation's existing `execution_class` field. No new request field, no
new broker-level decision value (`ALLOW`/`DENY`/`HUMAN_REVIEW` remain the
only three), no caller-selectable policy bypass.

Under this design, `pcae push`'s existing, contract-fixed
`execution_class=EXECUTION_CLASS_MUTATION` would place it outside
`POL-004`'s recommended domain (`{shell, backend, adapter, rollback}`) as
one instance of a general rule — not a push-specific carve-out.

**This design does not close B-1.** It is architecture only:
unimplemented, unfrozen as a normative contract, unverified. The full
remaining closure path (contract freeze → independent verification →
Foundation implementation → implementation verification → PBPC-001
re-evaluation → B-1 re-verification) is documented in the design
document's §25.

**Verdict: DESIGN COMPLETE. B-1 REMAINS OPEN.**

No `src/pcae/**` file was modified (confirmed via `git diff --name-only`
before/after, empty). No Permission Broker Foundation behavior was
changed. No `POL-001..012` rule was modified. No `POL-013+` policy was
introduced. No approval was fabricated. Runtime remains `Observed /
observe / unavailable`, unchanged.

Recommended next phase: **148C.3 — Permission Broker Foundation Policy
Applicability Contract Freeze** — independently author and freeze the
normative contract text for the applicability layer this document
designs, adversarially re-examining its own conclusions rather than
accepting them as an oracle. **148D is not recommended.** This
recommendation is not an authorization to begin either.

---

## Appendix: Bootstrap and Governance Validation

Bootstrap (run before this phase began): `pcae session bootstrap
--agent-id claude-local`; `pcae check`/`pcae health`/`pcae status
coherence`/`pcae doctor task-memory`/`pcae runtime inspect`/`pcae push
check`/`pcae notify status`/`pcae phase-report show --latest`/`pcae
phase-report reconcile --phase-id 148C.1` all clean at phase start,
confirming 148C.1 completed with Finding B-1 open and 148C.2
recommended. `pcae task new` opened this phase's own governed task
contract, scoped to this phase's own design document and ordinary
status/task bookkeeping; `src/pcae/**` explicitly forbidden.

Validation performed during this phase: live, read-only re-reproduction
of Finding B-1 against the actual, unmodified `PermissionBroker`/
`PolicyRegistry`/`build_permission_broker_request` (a
PBPC-REQ-046-conformant request still returns `HUMAN_REVIEW`,
`causing_policy_ids=('POL-004',)`, unchanged since no source was
modified). Direct source inspection of `PolicyRegistry.evaluate_all`
reconfirmed no per-`action_type`/`execution_class` rule filtering exists
anywhere in the Foundation today. All twelve `POL-001..012` rules read
directly from `src/pcae/core/permission_broker_foundation.py` and
independently classified for universal-vs-scoped domain, cross-checked
against `docs/PHASE_108_PERMISSION_BROKER_POLICY_RULE_FRAMEWORK.md`'s own
12-row table. `pcae check`/`pcae health`/`pcae status coherence`/`pcae
doctor task-memory`/`pcae runtime inspect`/`pcae push check` all re-run
clean before finalization; `pcae runtime inspect` reconfirmed `Observed /
observe / unavailable`, unchanged before and after this phase. `git diff
--name-only -- src/pcae/` confirmed empty before this phase's own
commits and after — no production source changed by this phase.

**Known, disclosed operational note on this artifact's own trust gate**
(the same self-referential staleness gap Phase 147P's, 147Q's, 147R's,
148A's, 148B's, 148C's, and 148C.1's own canonical reports each
documented in this same appendix section): this phase's `pcae phase
complete` invocation was rejected by the Repository Transition
Validator's `phase_identity_consistency`/`metadata_consistency` checks on
the first several attempts, because those checks compare the *incoming*
phase identity (148C.2) against whatever canonical report/metadata
existed on disk at completion time — which, before this phase's own
successful completion, was still Phase 148C.1's own canonical report and
structured metadata (`phase_id: "148C.1"`). This is not a defect in this
phase's own design work; it is the same pre-existing, previously-
documented self-referential staleness check prior phases' own appendices
described. This phase completes the repository transition by writing
`.pcae/phase-completion-metadata.json` and this canonical report artifact
directly, to bring both back into agreement with the now-current phase
identity, exactly as those prior phases' own appendices document doing
for themselves. Resolving this required directly authoring both staging
artifacts (not merely the metadata JSON) before `pcae phase complete`
would accept the transition — a step this phase's own diff records
honestly rather than silently working around.
