# Phase 149O.20L.7O.2W — Generic Producer Intake Helper and Session Provenance Integration

**Phase type:** production integration/hardening. Touches intake
provenance, CLI/user workflow, session/agent-state consumption, and
reference-adapter architecture. Creates no new authorization semantics.

**Verdict: GENERIC PRODUCER INTAKE HELPER — IMPLEMENTED. Independent
verification recommended as 149O.20L.7O.2W.1.**

```
BLOCKING FINDINGS:                0
PRODUCER PROVENANCE:              derived from PCAE governance agent lock
                                   when available (agent_lock.read_agent_lock)
PRODUCER IDENTITY:                descriptive / non-authenticating / non-authorizing
GENERIC DIRECT INTAKE:            preserved (pcae intake create unchanged)
NO-LOCK EXTERNAL PRODUCER:        supported via required --producer
CLAUDE-SPECIFIC CORE LOGIC:       none (grep-verified, existing 2U.3 gate)
CLAUDE HELPER:                    thin subprocess wrapper around
                                   `pcae intake from-files`
CODEX:                            uses same generic helper, no dedicated
                                   adapter
CUSTOM PRODUCER:                  uses same core semantics
ALLOW/DENY:                       producer-independent (tested)
TASK SCOPE:                       unchanged, lock snapshot not trusted
PROMOTION AUTHORITY:              unchanged
RUNTIME:                          Observed / observe / unavailable (unchanged)
v0.3.0:                           unchanged / published
ARTICLE:                          unchanged / not published
```

---

## 1. True Phase Entry

- Phase-entry commit (`HEAD` before this phase's task transition):
  `f25922f1` ("Phase 149O.20L.7O.2V.1: remove 7 orphaned stale
  active-task files").
- No `src/pcae/**` changes existed at entry beyond that commit; v0.3.0
  (tag `v0.3.0`, SHA `738a815...`) was the last published release,
  untouched by this phase.

## 2. Re-Derived Current State (Primary Sources, Not Handoff Prose)

Read directly: `src/pcae/core/agent.py`, `src/pcae/commands/session.py`,
`src/pcae/core/backend_preflight.py`, `src/pcae/core/intake.py`,
`src/pcae/commands/intake.py`, `src/pcae/cli.py`,
`scripts/claude_code_intake_adapter.py`.

### 2.1 Three Agent-Identity Vocabularies (mechanically extracted)

| Source | File | Vocabulary | Accepts arbitrary values? |
|---|---|---|---|
| Capability registry (`MULTI_AGENT_REGISTRY`) | `src/pcae/core/agent.py` (declared statically) | `claude-local`, `codex-local`, `pcae-native`, `kimi-local`, `deepseek-local`, `gemini-local`, `grok-local`, `perplexity-local` | No — fixed tuple |
| Governance agent lock (`.pcae/agent-lock.json`) | `src/pcae/core/agent.py::acquire_agent_lock` / `read_agent_lock` | none enforced | **Yes** — any caller-supplied string |
| Backend/session lock (`.pcae/agent-locks/latest.json`) | `src/pcae/commands/session.py::_LOCKABLE_BACKENDS` (only reachable via `--sync-lock`) | `claude-local`, `claude-deepseek`, `claude-kimi`, `codex`, `manual`, `noop` | No — `_sync_backend_lock` rejects anything else |

Confirmed mismatch example from the handoff: `codex-local` (capability
registry) vs `codex` (backend/session lock) — the two vocabularies are
genuinely different lists, not a typo in one place.

This phase does **not** unify these three vocabularies (out of scope per
handoff §17/§18) — it only selects one of them as the provenance source
for generic intake (§3 below) and documents the other two as-is.

## 3. Selected Provenance Source

**Selected: `agent_core.read_agent_lock(root)` → `.pcae/agent-lock.json`
`agent_id` field.**

Why this one and not the backend/session lock:

1. It accepts arbitrary caller-supplied identities the same way the
   generic helper needs to (handoff §35's "arbitrary lock ID" case would
   be unsupportable if the backend lock's fixed six-name vocabulary were
   used instead).
2. It is repository-scoped, one-per-session governance state that PCAE
   already records for the *session*, not a narrower
   execution/backend-oriented artifact. The backend lock
   (`.pcae/agent-locks/latest.json`) is explicitly about whether a named
   CLI backend is invocable (`backend_command`, `backend_available`,
   `invocation_allowed`) — semantics irrelevant to "who is the operator
   of this governance session," which is what intake provenance needs.
3. `pcae session bootstrap --agent-id <id>` already calls
   `acquire_agent_lock_idempotent` unconditionally (only the backend-lock
   rehydration is gated behind `--sync-lock` / `_LOCKABLE_BACKENDS`), so
   every bootstrapped session already has a governance agent lock without
   any extra step.

Implementation: `derive_producer_provenance()` in
`src/pcae/core/intake.py`.

## 4. Producer Provenance Is Descriptive — Frozen Invariant

`derive_producer_provenance` and `validate_and_ingest_intake_candidate`
never let `producer` influence `execution_allowed`, `promotion_executed`,
task-scope decisions, or repo/base/hash validation. This was already true
of `validate_and_ingest_intake_candidate` before this phase (it only ever
copies `producer`/`producer_claims` verbatim into the stored ECP/intake
record); this phase adds a *second* producer-shaped field
(`producer.source`, see §7) which is subject to the identical rule and is
covered by the same authority-injection test matrix
(`test_producer_field_cannot_set_authority_fields` and the parametrized
`test_top_level_authority_field_injection_ignored` family in the existing
2U.3 suite, unmodified).

## 5. Shared Generic Helper — Location and Contents

**Location: `src/pcae/core/intake.py`** (not a new module — see §11).
New production functions, all reused by both the CLI and any future
in-process caller:

- `compute_content_hash(content) -> str`
- `parse_file_change_spec(raw) -> dict` — parses
  `path:operation[:content_file]` using the existing `_VALID_OPERATIONS`
  vocabulary (`create`/`modify`/`delete`); no new operations added.
- `current_head_commit(root) -> str | None` — `git rev-parse HEAD`,
  alongside the existing `compute_repo_fingerprint` (`git rev-list
  --max-parents=0 HEAD`).
- `derive_producer_provenance(root, explicit_producer_kind=None) ->
  (dict|None, list[str])` — §3/§8/§9 logic.
- `build_intake_candidate_from_files(root, task_id, candidate_id,
  file_specs, summary="", self_reported_complete=False,
  explicit_producer_kind=None, adapter_version=...) -> dict` — the single
  producer-neutral candidate-construction entry point.

CLI plumbing: `run_intake_from_files` in `src/pcae/commands/intake.py`
(thin argument/JSON layer only, matching the existing `run_intake_create`
pattern) and the `pcae intake from-files` subparser in `src/pcae/cli.py`.

## 6. Preferred Product Surface

**`pcae intake from-files`** — added as a new subcommand under the
existing `intake` parser (not a new top-level command), consistent with
`intake create` / `intake show` / `intake list`.

```
pcae intake from-files \
  --task-id <task-id> \
  --candidate-id <id> \
  --file path:operation[:content-file] [--file ... repeatable] \
  --summary "..." \
  [--self-reported-complete] \
  [--producer <id>] \
  [--dry-run] [--json]
```

## 7. No User-Supplied Producer By Default / Producer Source Marker

When a governance agent lock is active, `--producer` is not required —
`producer.kind` is derived from `lock.agent_id`. An additive,
schema-compatible `producer.source` field (`"agent_lock"` or
`"candidate"`) records which path supplied it, per handoff §23. This is
additive metadata inside the `producer` object, which
`validate_and_ingest_intake_candidate` already treats as an opaque dict
(`candidate.get("producer") if isinstance(..., dict) else {}` — see
`src/pcae/core/intake.py` around the existing `validate_and_ingest_intake_candidate`
body) — no change to the frozen 2U.1 top-level candidate schema was
needed or made.

## 8. Explicit External / Unbootstrapped Producer Path — Preserved

No governance lock → `build_intake_candidate_from_files` requires
`--producer`/`explicit_producer_kind` and fails closed with
`no_active_agent_lock_and_no_explicit_producer_supplied` if it is
missing — it never invents `producer.kind = "unknown"`. This preserves
the v0.3 external-producer compatibility policy: an operator with no
PCAE session can still submit via `pcae intake create` directly (§10,
unmodified) or via `pcae intake from-files --producer <id>`.

## 9. Mismatch Handling

If `--producer` is supplied *and* a governance lock is active *and* they
differ, `derive_producer_provenance` returns
`producer_conflicts_with_active_agent_lock:explicit=...,lock=...` and the
candidate is not built at all (deterministic rejection before any repo
binding or submission work happens) — not an authority violation, a
provenance-consistency guard. If they match, this is a no-op-consistent
case, not treated as a conflict
(`test_producer_matching_active_lock_is_not_a_conflict`).

## 10. Direct Generic Intake — Unchanged

`pcae intake create --candidate-file ...` and
`validate_and_ingest_intake_candidate` were not modified in this phase
beyond the new helper functions appended below them; `pcae intake create`
never calls `build_intake_candidate_from_files`, so nothing about
existing generic-JSON submission changed. Full existing 2U.2/2U.3 suites
pass unmodified except three tests that exercised the retired script's
*internal* `build_intake_candidate`/`_parse_file_arg` functions directly
(§13) and one allowlist test extended for the new `git rev-parse` call
(§14).

## 11. Shared Library Location Justification

No new module was created. `src/pcae/core/intake.py` already owns
`compute_repo_fingerprint`, hashing, and candidate validation/ECP
construction; the from-files helper is the same kind of logic
(repo/base binding + hashing + generic candidate assembly), so adding it
here avoids a second trusted surface purely for style, per handoff §45.

## 12. Claude Helper Disposition

**Option A: thin compatibility wrapper.** `scripts/claude_code_intake_adapter.py`
no longer contains any intake-contract logic, repo-fingerprint logic, or
content-hashing logic. It parses its own CLI args and shells out to
`pcae intake from-files` (translating `--file`/`--summary`/
`--self-reported-complete`/`--producer`/`--dry-run` 1:1), then prints
that subprocess's stdout/stderr and returns its exit code — the same
translate-then-delegate shape the script always had, just delegating to
`pcae intake from-files` instead of building the candidate document
itself.

`grep -in "claude\|anthropic" src/pcae/core/intake.py
src/pcae/commands/intake.py` → no matches (verified; the pre-existing
2U.3 test `test_no_normative_claude_dependency_in_core_intake_module`
still passes). The wrapper script's own filename/docstring are the only
remaining Claude-specific strings, exactly as handoff §13 allows.

## 13. Codex / Claude / Custom Producer Proof (No Dedicated Adapters)

All three proven against the identical `build_intake_candidate_from_files`
+ `validate_and_ingest_intake_candidate` path, differing only in the
governance-lock `agent_id` bootstrapped beforehand — see
`tests/test_phase_149o_20l_7o_2w_producer_provenance_integration.py`:

- `test_lock_derived_producer_claude_identity` — `agent_id="claude-local"`
  → `producer.kind == "claude-local"`, `source == "agent_lock"`.
- `test_lock_derived_producer_codex_identity_no_dedicated_adapter` —
  `agent_id="codex-local"` → accepted, `execution_allowed` False, no
  Codex-specific code path exercised.
- `test_lock_derived_producer_arbitrary_custom_identity_preserved` —
  `agent_id="my-custom-agent"` → preserved verbatim, not normalized or
  rejected (handoff §35).
- `test_no_lock_with_explicit_producer_preserves_v0_3_compatibility` —
  no lock, `explicit_producer_kind="fully-external-producer"` → accepted,
  `source == "candidate"`.

## 14. ALLOW/DENY Equivalence Across Producers

`test_allow_decision_identical_across_producers` and
`test_deny_decision_identical_across_producers_out_of_scope`, each
parametrized over `claude-local` / `codex-local` /
`a-wholly-fictional-agent` — identical accept/reject outcome and
identical rejection reason (`out_of_scope_path`) in the deny case,
regardless of producer.

## 15. Authority Non-Flow Proof

`test_producer_field_cannot_set_authority_fields` — a candidate whose
`producer` object itself carries injected `execution_allowed`/
`promotion_authorized` keys is still accepted only as non-authorizing
evidence (`execution_allowed`/`promotion_executed` False on both the
intake result and the stored ECP). This extends the existing 2U.3
authority-injection matrix, which already covered top-level and
`producer_claims`-level injection, to the `producer` object itself.

## 16. Task-Scope and Base-Commit Authority — Lock Snapshot Not Trusted

`AgentLock` snapshots `active_task` and `git_branch` at acquisition time
(`build_agent_lock_data`, unmodified). Two tests prove the from-files
helper never substitutes these stale snapshots for canonical authority:

- `test_lock_active_task_snapshot_not_trusted_for_scope` — after the
  lock is acquired against task A, task A is superseded by task B
  (`find_latest_active_task` now returns B). A candidate for the
  now-stale task A (the one the lock still snapshots) is rejected
  `task_not_active`; one for current task B is accepted — scope authority
  still comes from `find_latest_active_task`, called fresh inside
  `validate_and_ingest_intake_candidate`, exactly as before this phase.
- `test_lock_git_branch_snapshot_not_used_as_base_authority` — after the
  lock is acquired, HEAD is advanced by a new commit; the built
  candidate's `base_commit` reflects the new real HEAD (via
  `current_head_commit`'s live `git rev-parse HEAD`), not anything cached
  at lock-acquisition time.

## 17. Stale Lock Behavior

`test_stale_lock_still_used_as_descriptive_provenance` — a lock acquired
far enough in the past to be `stale` per existing
`build_agent_status`/`AGENT_LOCK_STALE_AFTER_SECONDS` semantics still
supplies its `agent_id` as descriptive provenance without error. No new
authority rule was introduced around staleness (handoff §19): staleness
is already advisory harness-wide, and provenance is descriptive, so
propagating that existing advisory-only status was the minimum change
consistent with current governance semantics.

## 18. Contract Compatibility

The frozen 2U.1 top-level candidate schema
(`intake_contract_version`/`candidate_id`/`producer`/`task_context`/
`repo_binding`/`proposed_changes`/`producer_claims`) is unchanged.
`producer.source` is an additive key inside the already-opaque
`producer` object (§7) — no `SUPPORTED_INTAKE_VERSIONS` bump, no core
validation change.

## 19. Existing Regression Suites

Ran (all pre-existing, unmodified except as noted in §13/§14 test
additions and the two 2U.2/2U.3 fixups in §20):

- `tests/test_phase_149o_20l_7o_2u_1_reference_adapter_contract_freeze.py`
- `tests/test_phase_149o_20l_7o_2u_2_reference_adapter_implementation.py`
- `tests/test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`
- `tests/test_agent.py` (agent-lock / registry tests)
- `tests/test_session.py` (session/bootstrap tests)
- New: `tests/test_phase_149o_20l_7o_2w_producer_provenance_integration.py`

Result: `4549 passed, 2 failed` (raw, unfiltered, run against the
uncommitted working tree). Both failures confirmed non-attributable via
`git stash -u` A/B against clean `HEAD` (`f25922f1`):

- `test_no_intake_cli_command_implemented_yet` — fails identically on
  clean `HEAD` (pre-existing; `pcae intake ...` has existed in
  `src/pcae/cli.py` since Phase 2U.2, well before this phase — the
  2U.1 contract-freeze test asserting it does not yet exist was never
  updated once 2U.2 shipped).
- `test_no_production_code_modified_this_phase` — passes on clean `HEAD`
  (0 diff); fails only while this phase's own changes are uncommitted
  (`git diff --stat HEAD -- src/pcae scripts` is nonzero mid-phase by
  construction). Resolves automatically once this phase's implementation
  commit lands, since the test compares the working tree to `HEAD`, not
  to a frozen historical baseline.

Deselected fast_green-equivalent clean run for the targeted suite:
`python -m pytest tests/test_agent.py tests/test_session.py
tests/test_phase_149o_20l_7o_2u_1*.py tests/test_phase_149o_20l_7o_2u_2*.py
tests/test_phase_149o_20l_7o_2u_3*.py tests/test_phase_149o_20l_7o_2w*.py
--deselect tests/test_phase_149o_20l_7o_2u_1_reference_adapter_contract_freeze.py::test_no_intake_cli_command_implemented_yet
--deselect tests/test_phase_149o_20l_7o_2u_1_reference_adapter_contract_freeze.py::test_no_production_code_modified_this_phase
-q` → 4549 passed, 0 failed.

## 20. 2U.2/2U.3 Fixups Required By This Phase's Refactor

The retired script's internal functions (`build_intake_candidate`,
`_parse_file_arg`) no longer exist, since all of their logic moved into
`pcae.core.intake` (§5). Three 2U.2 tests that imported and called those
internal functions directly were rewritten to call the equivalent shared
functions (`intake.build_intake_candidate_from_files`,
`intake.parse_file_change_spec`) instead — same assertions, same attack
coverage, updated call surface. Two 2U.3 subprocess-level tests
(`test_claude_adapter_dry_run_produces_generic_schema_no_claude_specific_leak_into_core`,
`test_claude_adapter_malformed_file_arg_fails_clearly`) were updated to
pass `--producer claude-code` (the wrapper's new no-lock requirement,
§8) and to check the new `file_spec_error` message text instead of the
retired `adapter_error` text. One 2U.3 allowlist test
(`test_core_intake_module_never_shells_out_to_apply_a_patch`) was
extended to permit the new, reviewed `git rev-parse` call
(`current_head_commit`) alongside the existing `rev-list`/`cat-file`/
`merge-base`/`show`/`check-ignore` allowlist.

## 21. Trust/HMIC Assessment

Moving producer derivation into `pcae.core.intake` (a production module
already inside the trust boundary that constructs ECPs) does not change
its classification: the function only *reads* `.pcae/agent-lock.json`
(already-trusted local governance state, same file
`pcae session bootstrap` already reads) and writes the result into the
same non-authorizing `producer` field that has existed since 2U.2. It is
**authority-adjacent** (it feeds provenance metadata that operators and
auditors read) but not **authority-bearing** (§4/§15 prove it cannot
influence `execution_allowed`/`promotion_executed`/task-scope/repo-base
decisions) — consistent with, not an escalation of, the existing
intake trust-scope classification from 2U.3 §57-60.

## 22. Carried-Over Findings (Unchanged, Not Reopened)

- Windows path-hardening finding: unchanged, not revisited (helper reuses
  the existing `_path_is_safe_relative` check unmodified).
- Repository-fingerprint design: unchanged (`compute_repo_fingerprint`
  reused verbatim, not redesigned).
- Runtime state: unchanged — `Observed / observe / unavailable`; no
  agent execution activated by this phase.
- Permission broker: not touched; no PB enforcement added.
- v0.3.0 release artifacts (tag, GitHub Release, package version): not
  touched.
- v0.3.0 article: not touched; remains a local, unpublished draft.

## 23. No-Go List Compliance

None of the handoff's 23 no-go items were done: no per-agent adapter was
created (Codex/custom producers reuse the one generic helper — §13); no
native Codex/Claude/Cursor/DeepSeek parser was implemented; no
authentication was added to any agent identity; producer provenance was
not turned into authority (§4/§15); the three-vocabulary registry was
not redesigned (§2.1 documents, does not unify); task-scope and
promotion authority are unchanged (§16); the generic intake contract's
normative schema is unchanged (§18); Windows path/fingerprint findings
were not reopened; runtime was not activated; no PB enforcement added;
HATP/WebAuthn/Dell untouched; v0.3.0 release and article untouched; no
raw/force git push or history rewrite performed.

## 24. Recommended Next Phase

**149O.20L.7O.2W.1 — Generic Producer Intake Helper and Session
Provenance Integration Independent Verification.** Per handoff §56, this
phase's own implementation and tests are not a substitute for an
independent adversarial re-derivation of: the provenance-source choice
(§3), lock/candidate mismatch handling (§9), arbitrary lock IDs (§13),
stale-lock handling (§17), producer-to-authority non-flow (§4/§15),
task-scope isolation from the lock snapshot (§16), generic direct-intake
compatibility (§10), wrapper thinness (§12), vocabulary-mismatch
containment (§2.1), and trust-scope classification (§21).
