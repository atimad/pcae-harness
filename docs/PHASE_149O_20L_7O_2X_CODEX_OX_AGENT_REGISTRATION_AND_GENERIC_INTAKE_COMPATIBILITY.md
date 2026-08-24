# Phase 149O.20L.7O.2X — Codex-Ox Agent Registration and Generic Intake Compatibility

**Phase type:** small registration/compatibility change. Adds one
declarative advisory-registry identity (`codex-ox`) and one
backend-lock-recognition entry; touches no authority/decision logic.
Creates no new authorization semantics.

**Verdict: CODEX-OX AGENT REGISTRATION — IMPLEMENTED. Generic intake
compatibility verified at implementation boundary — independent
verification recommended as 149O.20L.7O.2X.1.**

```
BLOCKING FINDINGS:                0
CODEX-OX AGENT REGISTRATION:      IMPLEMENTED
GENERIC INTAKE COMPATIBILITY:     VERIFIED AT IMPLEMENTATION BOUNDARY
                                   -- INDEPENDENT VERIFICATION PENDING
PRODUCER PROVENANCE:              DESCRIPTIVE / NON-AUTHENTICATING /
                                   NON-AUTHORIZING
AGENT IDENTITY:                   codex-ox preserved literally (no
                                   normalization to codex/codex-local/ox/
                                   openrouter)
DEDICATED CODEX-OX INTAKE ADAPTER: NONE
NATIVE OX/CODEX PARSER:           NONE
RUNTIME:                          Observed / observe / unavailable
                                   (unchanged)
v0.3.0:                           unchanged / published
ARTICLE:                          unchanged / not published
```

---

## 1. True Phase Entry

- Phase-entry commit (`HEAD` before this phase's task transition):
  `56e44d8c` ("Phase 149O.20L.7O.2W.1: sync pushed_status/origin_main_head
  to post-push literal values"). Repository clean, 0 commits ahead of
  `origin/main`, `pcae health`/`pcae check`/`pcae status coherence` all
  passing at entry.
- v0.3.0 (tag `v0.3.0`) is the last published release, untouched by this
  phase.

## 2. Pre-Change Agent Identity Reconstruction

Re-derived directly from `src/pcae/core/agent.py` and
`src/pcae/commands/session.py` (not from prior phase reports), confirming
the three-vocabulary mismatch 2W/2W.1 documented is unchanged at entry:

| Vocabulary | Location | Members at entry | Arbitrary values accepted? |
|---|---|---|---|
| Capability registry (`MULTI_AGENT_REGISTRY`) | `core/agent.py` | `claude-local`, `codex-local`, `pcae-native`, `kimi-local`, `deepseek-local`, `gemini-local`, `grok-local`, `perplexity-local` (8) | No — fixed tuple |
| Agent config registry (`AGENT_CONFIG_REGISTRY`) | `core/agent.py` | same 8 agent IDs, mapping to `adapter_type`/`executable_hint` | No — fixed dict |
| Governance agent lock (`.pcae/agent-lock.json`) | `core/agent.py::acquire_agent_lock`/`read_agent_lock` | none enforced | **Yes** — any caller-supplied string |
| Backend/session lock (`.pcae/agent-locks/latest.json`) | `commands/session.py::_LOCKABLE_BACKENDS` | `claude-local`, `claude-deepseek`, `claude-kimi`, `codex`, `manual`, `noop` (6) | No — `_sync_backend_lock` rejects anything else, but non-membership is non-fatal to bootstrap (see §3) |
| Separate `pcae backend` invocation registry | `core/agent.py` backend-apply-plan subsystem | `claude`, `claude-deepseek`, `codex`, `qwen`, `mock` (5) | No — out of scope this phase (§6) |

`derive_producer_provenance` (`src/pcae/core/intake.py`) reads only the
governance agent lock — none of the other four vocabularies. This is
unchanged from 2W and is the reason the baseline behavior in §3 already
holds before any code change in this phase.

## 3. Baseline `codex-ox` Behavior (Before Any Code Change)

Verified directly, in an isolated temporary harness (never against the
live governed repository), by calling
`pcae.commands.session.run_session_bootstrap` with
`agent_id="codex-ox"` before touching any registry:

- The governance agent lock (`acquire_agent_lock_idempotent`) accepted
  `codex-ox` immediately — no code path rejects an unregistered string.
- `.pcae/agent-lock.json` stored the literal value `codex-ox` (no
  normalization).
- The provenance event and `current_session.agent_id` both recorded the
  literal `codex-ox`.
- `_sync_backend_lock` (`commands/session.py`) — called unconditionally
  in the full, non-compact bootstrap path, **not gated on `--sync-lock`**
  (that flag only gates the *compact*-bootstrap sync path; the 2W phase
  doc's characterization of `_LOCKABLE_BACKENDS` as "only reachable via
  `--sync-lock`" describes the compact path only) — returned
  `lock_synced: false`, `recognized_backend: false`, and printed
  `Backend lock: not rehydrated ('codex-ox' is not a recognized lockable
  backend identity)`. This did **not** fail the bootstrap command; it
  only meant `.pcae/agent-locks/latest.json` was left unwritten/stale.
- `derive_producer_provenance` in `pcae.core.intake` already derives
  `{"kind": "codex-ox", "source": "agent_lock"}` with zero code changes,
  because it reads only the governance lock (§2), not the backend lock
  or either advisory registry.

**Conclusion:** the governed-lock → generic-intake-provenance path (the
core of the architecture rule in the task prompt) already worked for
`codex-ox` as an arbitrary string. What was missing for genuine
first-class support was narrower: `codex-ox` was invisible to the
user-facing capability/config enumeration (`pcae agents`, `pcae agents
config`) and its backend lock was never rehydrated during the intended
supported bootstrap flow.

## 4. Registration Surfaces Modified (and Why)

Only three surfaces were changed, each independently justified against
the phase's own required-surface list:

1. **`MULTI_AGENT_REGISTRY`** (`src/pcae/core/agent.py`) — added an
   `AgentEntry` for `codex-ox`. Justification: this is the "supported
   agent configuration" / "user-facing agent enumeration" surface
   (`pcae agents`, `pcae agents validate`, `pcae agents lifecycle`)
   explicitly named in the task's required-surfaces list. Without this,
   an operator running `pcae agents` would have no way to discover that
   `codex-ox` is a supported identity.
2. **`AGENT_CONFIG_REGISTRY`** (`src/pcae/core/agent.py`) — added an
   `AgentConfigEntry` for `codex-ox` (adapter_type `cli`, executable_hint
   `codex` — the same Codex CLI executable as `codex-local`).
   Justification: this is the "agent configuration registry" surface
   named in the task's required-surfaces list, and is exactly the
   "generic configuration mechanism where adding a declarative entry is
   trivial" the task permits (§12 of the task prompt) — no new adapter
   code, just a data entry pointing at the existing `codex` executable.
3. **`_LOCKABLE_BACKENDS` / `_BACKEND_INFO`** (`src/pcae/commands/
   session.py`) — added `codex-ox` to both. Justification: this is the
   "session/bootstrap identity" surface — it is what makes the intended
   supported flow (`pcae session bootstrap --agent-id codex-ox`)
   rehydrate `.pcae/agent-locks/latest.json` and report
   `recognized_backend: true` instead of printing a "not a recognized
   lockable backend identity" message for a now-first-class identity.

### Surfaces deliberately NOT modified (and why)

- **`pcae backend` invocation registry** (`claude`, `claude-deepseek`,
  `codex`, `qwen`, `mock`) — this is the separate, heavier
  invocation/readiness/apply-plan subsystem (`pcae backend readiness`,
  `apply-plan`, `invoke`). Adding `codex-ox` there would be adjacent to
  execution/invocation authority, which the task explicitly forbids
  expanding (§6, §12, §20 of the task prompt). Registration here is
  about governance/session labeling, not invocation authority.
- **`_RUNTIME_PROBE_AGENTS`** (`core/agent.py`, used by `pcae agents
  runtime-discover`) — this actively spawns `codex --help`/`codex mcp
  --help` subprocess probes. `codex-local` already covers probing the
  same `codex` executable; adding a second, redundant probe entry for
  the same binary under a different governance label was not required
  by any of the listed surfaces and was excluded per the "do not
  blindly add codex-ox everywhere" instruction.
- **PAP/IPILOT/planning-dry-run design-prototype literals** (the large
  number of hardcoded `"codex-local"` string literals scattered through
  `core/agent.py`'s read-only architecture-design and prototype
  sections, e.g. `_PAP_DEFAULT_AGENT`, IPILOT registry entries,
  phase-ordering heuristics) — these are self-contained, read-only
  design/prototype surfaces, not derived from `MULTI_AGENT_REGISTRY`
  (confirmed: `MULTI_AGENT_REGISTRY` is referenced only within its own
  ~1500-line section of the module) and not part of any surface named
  in the task's required-surfaces list.
- **`pcae.core.intake` / `pcae.core.session` authority logic** — no
  `if agent_id == "codex-ox"` branch was added anywhere (§7 below).
- **CLI argument parsing** (`src/pcae/cli.py`) — `--agent-id` was already
  unconstrained free text (no `choices=` restriction existed before or
  after this phase); no CLI change was needed for `codex-ox` to be
  accepted as a bootstrap argument.
- **`docs/COMMANDS.md`** — mechanically regenerated from CLI
  help/subcommand structure, not from registry contents; unaffected by
  this phase (no CLI flags/subcommands were added or changed) and left
  unregenerated.
- **README.md** — does not enumerate specific agent IDs; unaffected.

## 5. Literal Identity Result

The `codex-ox` `AgentEntry`/`AgentConfigEntry` registrations use the
literal string `"codex-ox"` as their key. Independently re-verified
post-change that:

- `pcae session bootstrap --agent-id codex-ox` stores `agent_id:
  "codex-ox"` verbatim in `.pcae/agent-lock.json` (the governance lock),
  distinct from `"codex"` and `"codex-local"`.
- The backend lock (`.pcae/agent-locks/latest.json`) now rehydrates with
  `backend_name: "codex-ox"`, `lock_owner: "codex-ox"` — never
  normalized to `"codex"` or `"codex-local"` (regression-tested:
  `tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py::
  test_session_bootstrap_codex_ox_not_normalized_to_codex_local`).
- `derive_producer_provenance` continues to derive `producer.kind ==
  "codex-ox"` unchanged (it was already correct at baseline, §3; the
  registry additions do not touch this function at all).

## 6. Capability Declaration Result

`codex-ox`'s `AgentEntry` deliberately differs from `codex-local`'s: it
is `status=available` (honest — the same Codex CLI already installed for
`codex-local` makes `codex-ox` immediately usable today, verified via
the isolated-harness baseline test in §3) but its `capabilities` tuple
is `("code_generation", "test_writing")` — **excluding**
`"runtime_execution"`, which `codex-local`'s entry carries. This is a
deliberate, narrower declaration than the otherwise-identical
`codex-local` entry, so that this advisory registry text cannot read as
granting execution authority for a governance-session label whose
entire purpose (per the task prompt) is to be non-authorizing. This
field is advisory/display-only in `MULTI_AGENT_REGISTRY` (confirmed:
`"runtime_execution"` as a capability string is not consumed by any
allow/deny/authority decision in `core/agent.py`, `core/intake.py`, or
`core/review.py` — grep-verified) — the runtime execution posture that
actually matters (`pcae runtime inspect`) is a wholly separate subsystem
and was re-confirmed unchanged (§10).

`AGENT_CONFIG_REGISTRY["codex-ox"].configuration_notes` explicitly
separates the governed identity from provider/model configuration and
contains no credential, endpoint, token, or account material (regression
test: `test_codex_ox_registered_in_agent_config_registry`, which
adversarially checks the notes text for `api_key`/`bearer`/`token`/
`openrouter.ai/api` substrings).

## 7. Generic Intake Provenance Result / No Special-Case Branch

Freshly re-verified against the actual current `src/pcae/core/intake.py`
source (not assumed from 2W's report):

- `derive_producer_provenance` contains **zero** references to
  `"codex-ox"` or `codex_ox` (regression test:
  `test_no_codex_ox_special_case_branch_in_generic_intake_module`, which
  greps the live module source). `codex-ox` flows through the exact same
  `read_agent_lock(root)` → `{"kind": lock.agent_id, "source":
  "agent_lock"}` path as every other identity.
- `build_intake_candidate_from_files` / `validate_and_ingest_intake_
  candidate` were not modified in this phase at all (`git diff` confirms
  zero changes to `src/pcae/core/intake.py`).

## 8. Claude / Codex / Codex-Ox Equivalence Result

`tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py::
test_claude_codex_codex_ox_use_identical_intake_semantics` parametrizes
`claude-local`, `codex-local`, and `codex-ox` through the identical
build → validate → ingest path and asserts identical outcome shape
(`accepted=True`, `execution_allowed=False`, `promotion_executed=
False`), differing only in the literal `producer.kind` string. Passes
for all three.

## 9. Arbitrary Custom Identity / No-Lock Compatibility Regression

- `test_arbitrary_custom_identity_still_works_alongside_codex_ox_
  registration` — an unregistered string (`some-other-unregistered-
  agent`) still derives correctly through the governance lock with
  `codex-ox` now registered; the governance lock's arbitrary-string
  acceptance was not narrowed.
- `test_no_lock_generic_intake_still_works_with_codex_ox_registered` —
  the no-lock/explicit-`--producer` external-compatibility path (2W/2W.1's
  binding guarantee) is unaffected.
- `pcae session bootstrap --agent-id codex-ox` remains fully optional:
  no code path in this phase makes session bootstrap mandatory for
  generic intake.

## 10. Producer-to-Authority Non-Flow Result

- `test_codex_ox_producer_cannot_influence_authority_fields` —
  a `codex-ox`-derived candidate with a forged `producer.execution_
  allowed=True`/`producer.promotion_authorized=True` still yields
  `execution_allowed=False`/`promotion_executed=False` on both the
  intake result and the stored ECP (same adversarial pattern 2W used for
  `claude-local`).
- `test_codex_ox_scope_denial_identical_to_other_identities` — an
  out-of-scope path submitted under a `codex-ox` lock is rejected with
  `out_of_scope_path`, identical to every other identity.
- `src/pcae/core/canonical_artifact_promotion.py` and
  `src/pcae/commands/review.py` were grepped and contain zero references
  to `producer` or `codex-ox` (unchanged from 2W.1's finding — this
  phase did not touch either file).

## 11. No Dedicated Adapter / No Native Parser Proof

- `test_no_dedicated_codex_ox_intake_adapter_file_exists` — repository-
  wide filename scan for `codex_ox_intake_adapter.py` and five related
  banned names; zero matches.
- No new file was created anywhere under `src/pcae/` or `scripts/` in
  this phase (`git status` confirms only edits to `core/agent.py` and
  `commands/session.py`, plus test/doc additions).
- `codex-ox`'s `AgentConfigEntry.executable_hint` points at the same
  `codex` executable `codex-local` already uses — no new executable,
  transport, or parser was introduced.

## 12. Packaging Result

`codex-ox` is a data entry inside `src/pcae/core/agent.py` and
`src/pcae/commands/session.py`, both already part of the packaged `pcae`
distribution (no new files, no new package-data entries, no
`pyproject.toml` change needed). `python -m pcae --help` and `pcae
agents --json` were exercised via the editable install already active
in this environment (`pcae` on `PATH` resolves to this checkout); no
packaging regression is plausible from a pure-data addition to two
already-packaged modules.

## 13. W.1 Finding Disposition

Both non-blocking 2W.1 findings are carried forward unrepaired, per the
task's explicit instruction not to fix them unless `codex-ox`
registration directly depended on them:

1. **Malformed `.pcae/agent-lock.json` raises an uncaught
   `JSONDecodeError`** — `codex-ox` registration does not touch
   `read_agent_lock`/`acquire_agent_lock` and does not depend on
   malformed-lock handling; not Blocking for this phase; left unrepaired.
2. **Empty-`agent_id` fallback/provenance-quality behavior** —
   unrelated to a specific, non-empty literal identity like `codex-ox`;
   not Blocking; left unrepaired.

Neither became Blocking during this phase's implementation or testing.

## 14. Runtime Confirmation

`pcae runtime inspect --json` before and after this phase's changes
reports identical values: `state.current_state == "Observed"`,
`governance.execution_capability == "unavailable"`,
`governance.non_executing_posture == True`. Regression test:
`test_runtime_inspect_unaffected_by_codex_ox_registration`. No network
behavior, no Codex CLI invocation, no OpenRouter call, and no backend
invocation was added anywhere in this phase — `codex-ox`'s
`AGENT_CONFIG_REGISTRY`/`_BACKEND_INFO` entries carry
`invocation_allowed: False` / `execution_authorized: False`, identical
in shape to every pre-existing entry.

## 15. Files Changed / Phase-Owned Commits

- `src/pcae/core/agent.py` — `MULTI_AGENT_REGISTRY` + `AGENT_CONFIG_
  REGISTRY` additions (§4.1, §4.2).
- `src/pcae/commands/session.py` — `_LOCKABLE_BACKENDS` + `_BACKEND_
  INFO` additions (§4.3).
- `tests/test_agent.py` — updated pre-existing count/id-set assertions
  (`agent_count`/`available`/adapter-summary counts) that mechanically
  changed from 8 to 9 registered agents (5 available); no assertion's
  *meaning* was changed, only the now-correct cardinality.
- `tests/test_session.py` — one new focused test
  (`test_2x_bootstrap_rehydrates_codex_ox_lock`), following the existing
  74W.2 backend-lock-rehydration test pattern.
- `tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py` — new,
  19 focused tests (§5-§14 above map to specific tests in this file).
- `docs/PHASE_149O_20L_7O_2X_CODEX_OX_AGENT_REGISTRATION_AND_GENERIC_
  INTAKE_COMPATIBILITY.md` — this document.
- `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`,
  `.pcae/phase-completion-metadata.json`,
  `.pcae/phase-completion-report.md` — governance finalization artifacts.

## 16. Test Evidence / Regression Scope

Ran and passing:

- `tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py` — 19
  passed (new, this phase).
- `tests/test_session.py` — 145 passed (full file, includes new 2X test
  plus all pre-existing 74W.2/94Q.1 session-bootstrap tests).
- `tests/test_agent.py`, targeted subset covering every registry/
  lifecycle/adapters/validate surface touched by this phase (`-k
  "agent_count or agents_json or agents_human or agents_validate or
  validate_agent_registry_core or lifecycle or adapters or
  config_validate or config_show or config_available or
  config_declared"`) — 123 passed, 0 failed.
- `tests/test_agent.py`, full file (65798 lines, thousands of tests
  spanning many unrelated read-only architecture/design-prototype
  surfaces) — **4236 passed, 0 failed** (full run, 9m17s).
- `tests/test_phase_149o_20l_7o_2u_1_reference_adapter_contract_
  freeze.py`, `tests/test_phase_149o_20l_7o_2u_2_reference_adapter_
  implementation.py`, `tests/test_phase_149o_20l_7o_2u_3_reference_
  adapter_independent_verification.py`, `tests/test_phase_149o_20l_7o_
  2w_producer_provenance_integration.py`,
  `tests/test_phase_149o_20l_7o_2w_1_independent_verification.py` — spot-
  checked unaffected (this phase did not modify `core/intake.py`,
  `commands/intake.py`, or `scripts/claude_code_intake_adapter.py`). Two
  known pre-existing failures observed here
  (`test_no_production_code_modified_this_phase`,
  `test_no_intake_cli_command_implemented_yet`) — same class as
  documented in the 2W phase doc §19, confirmed non-attributable below.
- `tests/test_canonical_artifact_promotion.py`, `tests/test_review.py`,
  `tests/test_mutation_permission_promotion_integration.py` (promotion/
  review producer non-flow) — 33 passed, 0 failed.

**Full `fast_green` A/B (`python -m pytest -m fast_green -n auto -q`),
clean `HEAD` (`56e44d8c`) vs. this phase's uncommitted working tree, via
`git stash -u` / `git stash pop`:**

| | Clean `HEAD` | Dirty (this phase, uncommitted) |
|---|---|---|
| passed | 8691 | 8676 |
| failed | 335 | 351 |
| skipped | 5 | 5 |
| errors | 9 | 9 |

Diffing the two failure sets (`comm -13`/`comm -23` over sorted
`FAILED`/`ERROR` lines) shows **zero** tests that fail on clean `HEAD`
and pass in the dirty tree, and exactly 16 tests that pass on clean
`HEAD` but fail in the dirty tree — all mechanically explained. Every
one of the 16 is a guard test from an *unrelated*, already-completed
historical phase asserting "no `src/pcae` files changed since phase
entry" / "working tree clean" (e.g.
`test_no_src_pcae_files_dirty_in_working_tree`,
`test_git_status_touches_no_src_pcae_or_contract_file`,
`test_working_tree_unchanged_by_this_verification_run`) — they fail
purely because this phase's own `src/pcae/core/agent.py` /
`src/pcae/commands/session.py` edits were still uncommitted at test-run
time, identical in kind to `test_no_production_code_modified_this_phase`
(2W phase doc §19). None of the 16 assert anything about agent
registries, session bootstrap, or intake behavior. This resolves once
this phase's implementation commit lands (the working tree itself is
clean again at that point).

## 17. Governance Results

- `pcae check`: passed.
- `pcae health`: healthy.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings (pre-existing historical
  tasks/DONE.md sync debt predating this phase, unrelated to 2X — same
  warning set observed at phase entry before any 2X change).
- `pcae push check`: nothing_to_push at phase entry (baseline
  confirmation prior to this phase's commits).
- `pcae runtime inspect`: Observed / execution_unavailable — unchanged
  (§14).

## 18. No-Go Confirmations

No `codex_ox_intake_adapter.py` (or equivalent) was created (§11). No
native Ox or Codex output parser was created (§11). No Cursor or
DeepSeek adapter was touched. No OpenRouter API integration, network
call, or Codex CLI execution was added — `codex-ox`'s registry entries
are pure advisory/configuration data with `invocation_allowed`/
`execution_authorized` fixed to `False` (§6, §14). No authenticated or
cryptographic agent identity was added — the governance lock still
accepts arbitrary caller-supplied strings unchanged (§9). No agent
vocabulary unification was performed — the five-vocabulary mismatch in
§2 is documented, not reconciled; `codex-ox` was added to exactly three
of them, each independently justified (§4). No normalization of
`codex-ox` to `codex`/`codex-local`/`ox`/`openrouter` occurs anywhere
(§5). No change to task-scope, base/repository, promotion, or Permission
Broker authority was made or is possible through this phase's changes
(§10). No runtime execution was activated (§14). No HATP, FIDO2,
WebAuthn, or Dell deployment work was touched. No modification was made
to the v0.3.0 tag, GitHub Release, or package artifacts. No publication
or modification of the v0.3.0 article was performed. No inspection,
read, or reference of the private `~/repos/pcae-deepseek-research`
repository occurred at any point this phase. No raw `git commit`/`git
push`, force push, `--no-verify`, or history rewrite was performed —
only `pcae`-governed commit/task/phase commands were used.

## 19. Findings

None Blocking. Two pre-existing NON-BLOCKING findings carried forward
unrepaired (§13), consistent with the task's instruction not to repair
them absent a direct dependency.

## 20. Recommended Next Phase

**149O.20L.7O.2X.1 — Codex-Ox Agent Registration and Generic Intake
Compatibility Independent Verification.** Per the task's own governing
instruction, this phase's implementation and its own tests are not a
substitute for an independent adversarial re-derivation of: baseline
pre-2X behavior (§3), the necessity of each of the three registration
changes (§4), literal `codex-ox` identity preservation (§5), correct
session/bootstrap behavior (§3, §5), capability-declaration accuracy and
its deliberate exclusion of `runtime_execution` (§6), generic-intake
reuse with no special-case branch (§7), no dedicated adapter / no native
parser (§11), no provider/authentication overclaim (§6, §12),
producer-to-authority non-flow (§10), no-lock compatibility (§9),
vocabulary-mismatch containment (§2, §4's "deliberately not modified"
list), packaging (§12), and unchanged runtime posture (§14). Do not
proceed directly to a release-scope phase before 2X.1 completes.
