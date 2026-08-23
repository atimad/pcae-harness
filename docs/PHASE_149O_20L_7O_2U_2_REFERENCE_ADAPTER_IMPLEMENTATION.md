# Phase 149O.20L.7O.2U.2 — Reference Adapter Implementation

Status: implementation only. Independent verification is 2U.3's job, not
claimed here. No HATP/WebAuthn/DeepSeek/Codex work. No release tag. No
raw/force git push. No Permission Broker enforcement change. Runtime
posture unchanged (`Observed` / `observe` / `execution_unavailable`).

This phase implements the contract frozen in Phase 149O.20L.7O.2U.1
(`docs/PHASE_149O_20L_7O_2U_1_REFERENCE_ADAPTER_CONTRACT_FREEZE.md`),
re-derived from that canonical report and from current production source
(`src/pcae/cli.py`'s `execution-activation`/`execution-change-package`/
`promotion-review`/`promote`/`rollback` blocks, `src/pcae/core/check.py`'s
task-scope primitives, `src/pcae/core/agent.py`'s ECP/EPR/PER schemas) —
not from summary prose.

## 1. What was built

- `src/pcae/core/intake.py` — the intake contract validator and
  ECP-compatible artifact constructor.
- `src/pcae/commands/intake.py` — thin CLI handlers (`create`/`show`/`list`).
- `src/pcae/cli.py` — `pcae intake create|show|list` subparser wiring.
- `scripts/claude_code_intake_adapter.py` — the thin Claude Code reference
  producer.
- `tests/test_phase_149o_20l_7o_2u_2_reference_adapter_implementation.py`
  — 24-case adversarial test matrix.

No new subsystem directory was created. `pcae.core.intake` sits beside
the existing `pcae.core.agent`/`pcae.core.check`/`pcae.core.tasks`
modules it reuses; `pcae.commands.intake` sits beside the existing
`pcae.commands.check` it depends on for path-matching. The adapter
script is a flat file in `scripts/`, matching the existing
`scripts/hatp_*_admin.py` convention (no new `scripts/examples/` or
`scripts/tools/` directory).

## 2. How the contract was re-derived, and where it was concretized

2U.1 froze the *shape and intent* of the contract (generic diff/JSON,
non-authorizing, task-scope checked, hash-verified, Claude Code as first
thin non-normative producer) but explicitly left the exact wire format
for 2U.2 to pin down (2U.1 §5: "frozen design for 2U.2 to implement, not
a working CLI surface"). Concretizations made this phase, all consistent
with 2U.1's stated constraints:

- **`content_after` (full content) instead of `diff` (unified diff).**
  2U.1's schema sketch listed `"diff": "string, unified diff or full-file
  content per operation"`. Implementing a unified-diff *parser* that
  applies patches to arbitrary base content is a meaningfully larger,
  separately-reviewable attack surface (hunk-header parsing, fuzzy
  matching, malformed-patch handling) for a phase whose scope is "no new
  authority surface." Requiring full post-change content instead makes
  hash verification a direct, unambiguous `sha256(content_after) ==
  content_hash_after` comparison with no patch-application step at all.
  This is a strictly more conservative, more auditable design than a
  diff-applying one, not a scope expansion.
- **Binary content is out of scope for v1.** `content_after` is required
  to be a UTF-8 string. A candidate proposing binary content is rejected
  with a clear error rather than accepted via base64 smuggling. Base64
  binary support, if wanted later, is a separately-reviewable extension,
  not silently included here.
- **`repo_binding` (repo_fingerprint + base_commit) was added explicitly**,
  per the coordinator's phase directive, as the concrete mechanism for
  "repo/base-commit binding" that 2U.1's schema sketch named as a
  requirement in prose but had not yet reduced to fields. `repo_fingerprint`
  is `sha256` of this repository's sorted root-commit hash(es) — stable
  across clones of the same history, computed independently by PCAE, never
  trusted from the candidate beyond the equality check. `base_commit` must
  be a real commit that is an ancestor of (or equal to) current `HEAD`.
- **`candidate_id` was added** as a required, producer-supplied stable
  identifier, independent of content, specifically so that ID-collision
  detection (2U.2's required test-matrix item) is a meaningful check
  rather than trivially satisfied by content-derived IDs.
- **Task binding is scoped to the *currently active* PCAE task only**,
  not "active or recently-closed" as 2U.1's design prose loosely put it.
  This is the more conservative reading and keeps intake routed through
  exactly the same `find_latest_active_task` + `path_matches_any`
  primitives `pcae check` itself uses — "reusing existing task-scope
  governance, not a new engine," per the phase directive. Extending
  binding to recently-closed tasks, if wanted, is additive future work,
  not a narrowing of what 2U.1 froze.

None of these concretizations changes 2U.1's frozen invariants: the
contract remains generic (no Claude-Code field), non-authorizing (no
authority field is read from candidate content), and additive (it
produces the same ECP shape the existing sandboxed-execution path
produces, changing zero downstream commands).

## 3. Architecture (as built)

```
any external agent/harness (Claude Code first, via scripts/claude_code_intake_adapter.py)
        |
        v  (JSON document, Intake Candidate v1.0)
  pcae intake create --candidate-file <path>
        |
        v
  pcae.core.intake.validate_and_ingest_intake_candidate()
        |  1. parse/shape checks (fail closed on malformed/unknown version)
        |  2. candidate_id idempotency / collision check
        |  3. task binding: task_context.task_id == currently active task
        |  4. repo binding: repo_fingerprint match + base_commit ancestry
        |  5. per-file: path safety (no traversal/absolute), task-scope
        |     check (reused path_matches_any), hash verification
        |  6. per-file exclusion classification (reused _ecp_classify_exclusion)
        v
  ExecutionChangePackage, stored via the EXISTING
  agent_core.store_execution_change_package() — same store, same schema,
  same _ecp_validate() gate every sandboxed-execution ECP must also pass.
  execution_allowed=False, promotion_executed=False, rollback_executed=False.
        |
        v
  UNCHANGED downstream chain:
  pcae promotion-review create --ecp-id <produced ecp_id> --disposition ... [--promotion-authorized]
        |
        v
  pcae promote --epr-id ...   (human-gated, unmodified)
        |
        v
  pcae rollback ...           (human-gated, unmodified)
```

A parallel, additive-only store (`.pcae/intake-candidates/`) records
every submission attempt — accepted or rejected — as an audit trail
distinct from the ECP store, with its own tamper-evidence hash
(`record_integrity_hash`, verified on every read).

## 4. The hard invariant, and how it is enforced

`received != validated != authorized != permitted != promoted !=
executed.` Concretely:

- No field of a submitted candidate document is ever copied into
  `execution_allowed`, `promotion_executed`, `promotion_authorized`, or
  any other authority-bearing field. Those fields are hardcoded `False`
  in every ECP and intake record this module produces, exactly as the
  pre-existing `_ecp_validate()`/`_epr_validate()` gates already require
  of every ECP/EPR regardless of origin.
- `promotion_authorized` is set only inside `build_promotion_review()`,
  from its own `--promotion-authorized` CLI flag — a separate command
  this module never calls and cannot invoke on a candidate's behalf.
- A candidate that includes forged fields such as
  `"promotion_authorized": true`, `"approved": true`, `"executed": true`,
  or `"execution_allowed": true` anywhere in its document (top level,
  inside a proposed change, inside `producer_claims`) is accepted or
  rejected on the *same* fail-closed criteria as any other candidate —
  those fields are simply never read. Verified by a parametrized test
  (`test_forged_authority_fields_are_ignored`) asserting the resulting
  ECP still has `execution_allowed=False`/`promotion_executed=False`
  regardless.

## 5. Fail-closed behavior (test matrix, 24 cases)

| Case | Mechanism |
|---|---|
| Valid allow case | Task-in-scope, hash-correct, base-commit-valid candidate is accepted; downstream `build_promotion_review`/`promote` work unmodified |
| Out-of-scope deny | `path_matches_any` against the active task's `allowed_files` (identical primitive `pcae check` uses) |
| Hash mismatch | `sha256(content_after) != content_hash_after` |
| Missing/invalid base commit | `git cat-file -e <commit>^{commit}` fails |
| Base commit not ancestor of HEAD | `git merge-base --is-ancestor <commit> HEAD` fails |
| Repo binding mismatch | `repo_fingerprint` != this repo's computed fingerprint |
| Malformed candidate (not an object) | Type check before any field access |
| Unknown schema version | `intake_contract_version not in SUPPORTED_INTAKE_VERSIONS` |
| Forged authority fields | Never read; ECP/intake record fields stay hardcoded `False` (4 parametrized sub-cases) |
| Path traversal / absolute path | `_path_is_safe_relative`: rejects leading `/`, `..` components, empty segments, `.` segments (4 parametrized sub-cases) |
| Duplicate candidate_id, conflicting content | Content-hash comparison against the prior accepted record for the same `candidate_id` |
| Duplicate candidate_id, identical content | Idempotent replay — same `ecp_id` returned, not a re-ingestion |
| Stored-artifact tampering after accept | `record_integrity_hash` recomputed on every read; mismatch reported as `integrity_verified: False` |
| Claude Code adapter positive | Adapter output validated end-to-end through the same core validator |
| Claude Code adapter negative (malformed) | Adapter's own `_parse_file_arg` raises on malformed `--file` syntax |
| Claude Code adapter cannot bypass checks | Adapter-produced out-of-scope and hash-tampered candidates are rejected by the identical core validator — the adapter has no privileged path |
| Task not active / mismatched | `find_latest_active_task(root).task_id != task_context.task_id` |
| Delete operation carrying a content hash | Explicitly rejected — deletes should never declare post-change content |

## 6. Trust-scope / HMIC reassessment

Checked whether the new production modules require HMIC registration or
trust-scope binding. HMIC (`src/pcae/core/hmic_*`/`hatp_*` naming
convention) governs HATP credential/identity certification specifically
— confirmed by grep across `src/pcae/core/` that every genuine HMIC
reference is scoped to `hatp_*.py` modules (the two apparent hits in
`agent.py` are a false-positive substring match inside the word
"algorithmically", not real HMIC references). `pcae.core.intake` carries
no HATP-relevant identity or credential boundary — it is an
evidence-only, non-authorizing artifact producer, gated by the same
pre-existing ECP/EPR trust gates every other ECP producer already goes
through. **Conclusion: no HMIC registration applies; none was added.**
This was an explicit reassessment, not a silent omission.

## 7. Verification performed this phase

- New adversarial suite: `pytest tests/test_phase_149o_20l_7o_2u_2_reference_adapter_implementation.py` — 24 passed, 0 failed.
- Downstream regression suites (execution/ECP/promotion/rollback/task-scope/
  mutation-permission/artifact-integrity): `test_agent.py`,
  `test_mutation_permission_promotion_integration.py`,
  `test_mutation_permission_core.py`,
  `test_mutation_permission_commit_integration.py`,
  `test_mutation_permission_push_routing_integration.py`,
  `test_canonical_artifact_promotion.py`,
  `test_rollback_approval_evidence_contract.py`,
  `test_rollback_approval_evidence_models.py`,
  `test_rollback_approval_evidence_persistence.py`,
  `test_rollback_approval_evidence_validation.py`,
  `test_repository_wide_mutation_inventory_guard.py` — 4370 passed, 0
  failed, confirming zero regression to the existing chain this phase
  reuses rather than modifies.
- A controlled Fast Green run (`pytest -m fast_green`) was executed this
  phase; its outcome is recorded verbatim in the phase-completion
  metadata's `fast_green` field.
- `git diff --stat HEAD -- src/pcae scripts` at phase close confirms the
  only production changes are the four new/modified files listed in §1
  (three new files, one addition to `cli.py`) — no existing
  `execution-activation`/`execution-change-package`/`promotion-review`/
  `promote`/`rollback` logic was modified.
- `git diff --name-only` confirms no HATP/WebAuthn/FIDO2 path was
  touched.

## 8. What this phase does not do

- Does not claim independent verification — that is 2U.3.
- Does not enable execution, change runtime posture, or add Permission
  Broker enforcement.
- Does not create a release/tag.
- Does not modify `execution-activation`, `execution-snapshot`,
  `execution-change`, `promotion-review`, `promote`, or `rollback`.
- Does not support binary content or unified-diff patch application in
  v1 (documented scope narrowing, §2).
- Does not extend task binding to recently-closed tasks (documented
  scope narrowing, §2).

## 9. Handoff to 2U.3

2U.3 (Reference Adapter Independent Verification, per the 2U plan)
should independently reproduce this phase's adversarial test matrix
against the real, unmodified `src/pcae/core/intake.py`, specifically
checking: (a) no path exists by which a candidate-supplied field reaches
an authority-bearing field anywhere in the ECP/EPR/PER chain; (b) the
task-scope, hash, and repo/base-commit checks cannot be bypassed by
malformed or adversarial input beyond what this phase's suite already
covers; (c) the tamper-detection mechanism (§5) is sound; (d) the scope
narrowings in §2 are appropriately conservative, not silently unsafe.
