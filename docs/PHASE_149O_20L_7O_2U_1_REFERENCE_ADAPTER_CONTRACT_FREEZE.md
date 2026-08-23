# Phase 149O.20L.7O.2U.1 — Reference Adapter Contract Freeze

Status: contract / design freeze only. No adapter code. No CLI
implementation. No production source change. No new authority surface
enabled. This phase executes the plan frozen in
`docs/PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md`
§12 and §22 (phase 2U.1), with both prerequisite human decisions already
resolved: the intake boundary is a **generic diff/JSON contract**, and
Claude Code is the **first thin reference-adapter producer** against it,
not a normative part of the contract itself.

## 1. Why a new contract is needed (grounded in current code)

Inspected the real 69A–69O chain's CLI surface directly
(`src/pcae/cli.py`, `execution-activation`, `execution-change-package`,
`promotion-review`, `promote`):

- `pcae execution-activation invoke` is explicitly scoped to invoking
  **claude-local** in read-only mode against a fully authorized EAR
  (Execution Authorization Record) — "Read-only execution activation
  for claude-local (Phase 69G). First PCAE command that sets
  `execution_allowed=True` within invocation boundary." It is not a
  generic "accept any agent's output" surface; it is PCAE's own
  sandboxed invocation of one specific, first-party runtime.
- `ExecutionChangePackage` (ECP) — the artifact holding diffs, hashes,
  and the `promotion_eligible` path list that `promotion-review create`
  and `promote` consume — is, per its own CLI help text, "created
  automatically during sandboxed execution... this surface is
  read-only." There is no command that constructs an ECP from a diff
  that did not originate inside PCAE's own sandboxed `execution-activation`
  run.
- Downstream of the ECP, the chain is already generic in spirit:
  `pcae promotion-review create --ecp-id ... --disposition ...
  --approved-path ... --promotion-authorized` and `pcae promote
  --epr-id ...` do not reference claude-local or any specific runtime —
  they operate purely on ECP/EPR identifiers and approved-path lists.

**Conclusion**: the gap is narrow and specific. It is not "PCAE cannot
govern external agents" — the promotion/rollback/audit chain downstream
of an ECP is already runtime-agnostic. The gap is that **only PCAE's own
sandboxed claude-local invocation can currently produce an ECP.** An
external agent's already-proposed change (from Claude Code, or any other
tool, running outside PCAE's sandbox) has no path into that chain today.

This phase freezes the contract for closing exactly that gap, without
touching `execution-activation`, `execution-snapshot`, or
`execution-change` (the claude-local-specific machinery), and without
changing `promotion-review`/`promote`/`rollback`'s existing semantics.

## 2. Architecture (frozen)

```
any external agent/harness (Claude Code first)
        |
        v
  thin adapter (per-agent, not part of this contract)
        |
        v
  generic PCAE intake contract  <-- FROZEN BY THIS PHASE
        |
        v
  ExecutionChangePackage (ECP)-compatible artifact
  (new creation path; existing ECP schema/consumers unchanged)
        |
        v
  existing, unmodified chain:
  promotion-review create --ecp-id ... --disposition ...
        |
        v
  pcae promote --epr-id ...   (human-gated, unchanged)
        |
        v
  pcae rollback ...           (human-gated, unchanged)
```

The generic intake contract is a **new, additive creation path for an
ECP-shaped artifact**, sitting alongside (not replacing) the existing
"created automatically during sandboxed execution" path. Both paths
produce the same downstream artifact shape so `promotion-review`/
`promote`/`rollback` require zero changes.

## 3. Generic intake contract (frozen schema, v1)

An externally-produced proposed change is submitted as an **Intake
Candidate** document:

```json
{
  "intake_contract_version": "1.0",
  "producer": {
    "kind": "string (e.g. \"claude-code\", \"generic-diff\")",
    "adapter_version": "string, free-form, informational only"
  },
  "task_context": {
    "task_id": "string, must match an active or recently-closed PCAE task",
    "declared_goal": "string, free-text, informational only"
  },
  "proposed_changes": [
    {
      "path": "string, repo-relative path",
      "operation": "one of: modify | create | delete",
      "diff": "string, unified diff or full-file content per operation",
      "content_hash_after": "string, sha256 of the proposed post-change content"
    }
  ],
  "producer_claims": {
    "summary": "string, free-text, the producer's own account of what it did",
    "self_reported_complete": "boolean"
  }
}
```

**Design constraints (frozen):**

- **No new authority.** An Intake Candidate is *evidence*, exactly like
  today's automatically-created ECP — it is never self-authorizing.
  `promotion_eligible` status and human review/authorization remain
  required before `promote` will act on any path from it. This mirrors
  the existing non-authorizing evidence boundary (§32 of the 2U plan).
- **Producer identity is not trusted content.** `producer.kind` is
  informational metadata for audit/reporting, never a basis for
  granting elevated trust or skipping review. Nothing in the promotion
  chain branches on `producer.kind == "claude-code"`.
- **Task-scope check reuses existing governance, unchanged.** Every
  path in `proposed_changes` is checked against the *existing*
  active-task allowed-file mechanism (`pcae check`'s current allow-list
  enforcement) before an Intake Candidate can become
  `promotion_eligible` — this is the concrete "deny path" from the 2U
  plan's demo (§10), and it requires no new enforcement code, only
  routing the intake path's file list through the check that already
  exists.
- **Content-hash verification, not trust-on-claim.** `content_hash_after`
  is verified against the actual proposed content before intake
  succeeds; `producer_claims.self_reported_complete` is recorded as
  evidence but never treated as authorization or as a substitute for
  human review — this directly implements the plan's "validates
  completion claims against real repo state" headline (§6 of the 2U
  plan) rather than trusting an agent's own "done" claim.
- **No sandboxed re-execution required.** Unlike the claude-local path
  (which sandboxes a live invocation via `git worktree` + `rsync`),
  intake candidates arrive as an already-produced diff. The intake
  contract's job is bookkeeping, hashing, and task-scope validation —
  not re-running the external agent.

## 4. Thin Claude Code reference-adapter relationship (frozen, non-normative)

Claude Code is the first concrete producer implementing a **thin
adapter** against the contract in §3. The adapter's sole job:

1. Read Claude Code's own session/task output (file paths touched,
   diffs, any session summary Claude Code already produces).
2. Translate that output into an Intake Candidate document matching
   §3's schema exactly — no Claude-Code-specific fields leak into the
   generic contract.
3. Submit the Intake Candidate through the generic intake surface
   (§5) like any other producer would.

**Explicitly frozen boundary**: nothing in §3's schema, in the intake
CLI surface design (§5), or in the downstream ECP/EPR/promote/rollback
chain may reference Claude Code, its session format, its tool-call
structure, or any other Claude-Code-specific concept. If a future
adapter (for a different agent/harness) cannot be written without
modifying the generic contract, the contract is not actually generic and
must be revised before that adapter ships — this is the acceptance test
for "genericness," recorded here for 2U.2 to honor.

## 5. Intake CLI surface (frozen shape, not implemented)

To be implemented in 2U.2, following this repository's existing
subcommand conventions (`show`/`list`/`create` patterns already used by
`promotion-review`, `execution-change-package`, etc.):

- `pcae intake create --task-id <id> --candidate-file <path-to-json>` —
  validate an Intake Candidate document against §3's schema, verify
  content hashes, run the existing task-scope check against
  `proposed_changes[].path`, and produce a new ECP-compatible artifact
  (reusing the existing ECP identifier scheme and `promotion_eligible`
  field semantics unchanged).
- `pcae intake show --intake-id <id>` — read-only inspection, mirroring
  `execution-change-package show`.
- `pcae intake list --task-id <id>` — read-only listing, mirroring
  `execution-change-package list`.

No `intake create` output is ever promotion-authorized by itself. The
existing `pcae promotion-review create --ecp-id <the produced ECP-id>
--disposition ...` step remains the human decision point, unchanged.

## 6. What this phase does not do

- No `pcae intake` command exists yet — §5 is a frozen design for 2U.2
  to implement, not a working CLI surface.
- No actual Claude Code adapter script/tool exists yet — §4 is a frozen
  relationship description, not code.
- No change to `execution-activation`, `execution-snapshot`,
  `execution-change`, `promotion-review`, `promote`, or `rollback` — all
  verified unmodified by this phase (§7).
- No relaxation of `promotion_authorized=True` gating, no new
  root-mutating command, no weakening of the non-authorizing evidence
  boundary.

## 7. Verification performed this phase

- Read `src/pcae/cli.py` `execution-activation`, `execution-change-package`,
  `promotion-review`, `promote`, `execution-snapshot`, `execution-change`
  parser definitions directly (not from prior phase prose) to ground
  §1's gap analysis in the actual current CLI surface and its own help
  text.
- Confirmed via `git diff --stat HEAD -- src/pcae scripts` (run at
  phase close) that no production code was modified.
- Confirmed via `git diff --name-only` (run at phase close) that no
  HATP/WebAuthn/FIDO2 path was touched.
- Test suite added this phase mechanically verifies: this contract
  document exists and contains the frozen schema fields, no Claude-Code
  identifier appears in the schema block itself (§3), and no production
  code was modified.

## 8. Handoff to 2U.2

2U.2 (Reference Adapter Implementation, per the 2U plan §22) implements:
the `pcae intake` CLI surface (§5), the ECP-compatible artifact
construction and content-hash verification (§3), the task-scope check
routing (§3), and the thin Claude Code adapter (§4) as a separate,
clearly-labeled reference script — not as changes to the generic
contract. Per the 2U plan, 2U.2 requires independent verification
(2U.3) because it touches an authority-adjacent surface (a new evidence
intake boundary feeding the existing promotion chain), even though it
adds no new root-mutation authority.
