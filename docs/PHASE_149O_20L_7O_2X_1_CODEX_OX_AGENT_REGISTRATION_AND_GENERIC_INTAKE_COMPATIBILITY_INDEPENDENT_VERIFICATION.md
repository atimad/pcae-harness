# Phase 149O.20L.7O.2X.1 — Codex-Ox Agent Registration and Generic Intake Compatibility Independent Verification

## 1. True Phase Entry

Phase entry commit: `a7410e83` (`Phase 149O.20L.7O.2X: restore idle-task
allowed-files after phase-complete lock release`) — the HEAD this
independent-verification phase started from.

2X implementation commit independently inspected: `7dc2f0fa72c5b9d57fa6f427b3ac680c73b093cf`
(`Phase 149O.20L.7O.2X: Codex-Ox Agent Registration and Generic Intake
Compatibility`). Parent commit used as the pre-2X historical baseline:
`56e44d8c5554d6675435989b94d8558d141c4ca4`.

Verification philosophy applied throughout: **re-derive, do not trust.**
The 2X report, its own tests, and its documentation conclusions were
treated only as claims to independently re-check against production
source, git history, and fresh test execution — never as evidence in
themselves.

## 2. Pre-2X Baseline Behavior (Historical Source)

Independently confirmed by inspecting `git show <parent-commit>:<path>`
directly (not the 2X report's description of it):

- `src/pcae/commands/session.py` at the pre-2X commit: `_LOCKABLE_BACKENDS
  = frozenset({"claude-local", "claude-deepseek", "claude-kimi", "codex",
  "manual", "noop"})` — `codex-ox` absent. A `pcae session bootstrap
  --agent-id codex-ox` at this commit would have synced no
  `.pcae/agent-locks/latest.json` entry (`_sync_backend_lock` rejects any
  name outside this set with `"'{agent_id}' is not a recognized lockable
  backend identity"`), reproduced behaviorally against the current
  implementation using the historical set.
- `src/pcae/core/agent.py` at the pre-2X commit: no `agent_id="codex-ox"`
  entry in `MULTI_AGENT_REGISTRY`, no `"codex-ox"` key in
  `AGENT_CONFIG_REGISTRY` — `pcae agents` would not have listed it and
  `get_agent_config("codex-ox")` would have returned `None`.
- The **core governance agent lock** (`acquire_agent_lock` /
  `read_agent_lock` in `agent.py`, and `derive_producer_provenance` /
  `build_intake_candidate_from_files` in `intake.py`) is untouched by the
  2X diff — confirmed by `git diff <parent> 7dc2f0fa -- src/pcae/core/agent.py`
  containing no change to `acquire_agent_lock`/`read_agent_lock`, and
  `git diff <parent> 7dc2f0fa -- src/pcae/core/intake.py` being empty.
  Because this lock accepts **any** caller-supplied `agent_id` string by
  design (no vocabulary check anywhere in `acquire_agent_lock`), the
  governed-lock → generic-intake-provenance path already worked for the
  literal string `"codex-ox"` before 2X, exactly as 2X claimed — this is
  independently re-derived from source, not taken on the 2X report's
  word.

**What 2X actually changed**, confirmed by diff: only the advisory
capability/config registries (`MULTI_AGENT_REGISTRY`,
`AGENT_CONFIG_REGISTRY` in `agent.py`) and the session-bootstrap
backend-lock recognition set (`_LOCKABLE_BACKENDS`/`_BACKEND_INFO` in
`session.py`) — 34 added lines total across the two files. Nothing in
`intake.py` changed at all.

## 3. Fresh Full Identity-Vocabulary Inventory

A fresh `grep -rln --include=*.py codex-ox src/pcae` (not the 2X report's
own enumeration) confines every `codex-ox` production reference to
exactly two files: `src/pcae/core/agent.py` and
`src/pcae/commands/session.py`. No hit in `docs.py`'s generated
enumerations, no hit in any CLI-argument-choices module, no hit in any
config schema.

Classification of every registry independently inspected:

| Registry | Contains `codex-ox`? | Classification |
|---|---|---|
| `MULTI_AGENT_REGISTRY` (agent.py) | Yes | Advisory configuration (capability discovery) |
| `AGENT_CONFIG_REGISTRY` (agent.py) | Yes | Advisory configuration (CLI adapter hint) |
| `.pcae/agent-lock.json` core lock (`acquire_agent_lock`) | Accepts it (unrestricted) | Production selection authority for governance-session identity only — carries no execution authority |
| `_LOCKABLE_BACKENDS` / `.pcae/agent-locks/latest.json` (session.py) | Yes | Descriptive identity (backend-lock rehydration bookkeeping) |
| `_build_invoke_command` (agent.py, actual subprocess dispatch) | **No** | Execution backend registry — deliberately excludes it |
| `_RUNTIME_PROBE_AGENTS` (agent.py) | **No** | Runtime observation/probe surface — deliberately excludes it |
| `build_remote_policy()["allowed_agents"]` (agent.py) | **No** | Execution backend registry (remote autonomous execution allow-list) — deliberately excludes it |
| `REMOTE_PLAN_DEFAULT_AGENT`, `_PAP_DEFAULT_AGENT`, `_IPILOT_DEFAULT_AGENT`, `_PAP_DEFAULT_RUNTIME`, `_IPILOT_DEFAULT_RUNTIME` (agent.py) | **No** | Design/prototype default literals — untouched |
| `docs.py` generated enumerations | **No** | Documentation-generated surface — untouched |

The vocabulary is **not** "five" merely because 2X's own report says so
— it is these two production files plus the pre-existing
vocabulary-agnostic core lock; every other registry in the repository
that recognizes agent/backend names was independently grepped and
confirmed absent.

## 4. Necessity of Each Registration Change

For each of the two production files 2X changed:

- **`MULTI_AGENT_REGISTRY`** — owns `pcae agents` enumeration and
  capability-discovery lookups (`get_agent_by_id`). Without an entry,
  `pcae agents --json` would not list `codex-ox`, and any caller of
  `get_agent_by_id("codex-ox")` gets `None`. The entry grants no
  authority: `capabilities` is a plain descriptive tuple
  (`code_generation`, `test_writing`), consumed nowhere for
  allow/deny decisions (grep-confirmed: `"runtime_execution"` as a
  string is not read by `core/review.py` or any execution-authorization
  path).
- **`AGENT_CONFIG_REGISTRY`** — owns `get_agent_config` (CLI-adapter
  hint used only for *preview* string generation, e.g.
  `_derive_command_preview`). Without an entry, dry-run previews for a
  `codex-ox` remote-execution job would render `None`. The entry does
  not enable execution — `_build_invoke_command`, the actual dispatch
  function, does not consult this registry's presence at all and has no
  `codex-ox` branch (§5/§15 below).
- **`_LOCKABLE_BACKENDS`/`_BACKEND_INFO`** — owns the descriptive
  `.pcae/agent-locks/latest.json` backend-lock rehydration performed
  during `pcae session bootstrap`. Without this entry, bootstrap with
  `--agent-id codex-ox` still acquires the **core** governance lock
  (unaffected, §2) but leaves the backend-lock artifact unsynced,
  reporting `recognized_backend: false`. The added entry only sets
  `invocation_allowed: False`, `execution_authorized: False` — matching
  every other declared-but-unexecutable identity.

Each addition is necessary for its stated, narrow purpose (enumeration
and one advisory bookkeeping artifact) and none is oversized relative to
the capability actually delivered.

## 5. Deliberate Omissions — Independently Verified

- **Backend invocation registry** (`_build_invoke_command`, agent.py):
  source-inspected — its branches are `"claude-local"`, `"codex-local"`,
  `"kimi-local"`; `codex-ox` falls to the final `return None` branch.
  Fresh test `test_build_invoke_command_returns_none_for_codex_ox_no_silent_codex_local_fallback`
  confirms `_build_invoke_command("codex-ox", "prompt")` returns `None`
  directly against the running interpreter (not inferred from source
  reading alone). The two real invocation call sites
  (`build_remote_invoke_...`, `build_remote_invoke_writable`) both check
  for `None` and return an `"cannot be invoked: ... not safely
  derivable"` result — no silent fallback to codex-local's argv.
- **Runtime-probe list** (`_RUNTIME_PROBE_AGENTS`): confirmed absent —
  membership means an actual `<agent> <exe> --help` capability-detection
  probe is run for that identity; `codex-ox` shares the same executable
  (`codex`) as the already-probed `codex-local`, so adding it would
  duplicate a probe against the same binary for no new information.
  Omission is correct and non-lossy.
- **PAP/IPILOT design/prototype literals**: `_PAP_DEFAULT_AGENT`,
  `_IPILOT_DEFAULT_AGENT`, `REMOTE_PLAN_DEFAULT_AGENT`, etc. are frozen
  advisory-preview single-default literals from earlier prototype-design
  phases, not enumerations a real agent identity needs to appear in to
  function; grep confirms none were touched. Omission is correct — these
  are not vocabulary a supported identity must join.
- **`build_remote_policy()["allowed_agents"]`**: independently confirmed
  `codex-ox` is absent (`{"claude-local", "codex-local", "kimi-local"}`
  only) and that `check_remote_job_readiness`/job-creation both gate on
  `requested_agent in policy["allowed_agents"]` *before* any execution
  path is reachable — a `codex-ox` remote job is blocked at readiness
  (`"agent 'codex-ox' is not in allowed_agents"`), never reaching
  `dry_run_result: "would_execute"`. This omission is load-bearing and
  correct: it is what keeps registration from reading as remote-execution
  eligibility.

None of the omissions breaks the intended supported use case
(registration, bootstrap, governance-lock provenance, generic intake
compatibility) — they are all execution-adjacent surfaces that
registration was never meant to unlock.

## 6. Meaning of "First-Class Supported"

Independently derived and confirmed exact:

> `codex-ox` is a first-class PCAE agent/session identity for
> registration (`pcae agents`), bootstrap recognition
> (`pcae session bootstrap`), governance-lock provenance
> (`.pcae/agent-lock.json` / `derive_producer_provenance`), and generic
> intake compatibility (`validate_and_ingest_intake_candidate`).

It is **not**: "PCAE can execute Codex against Ox/OpenRouter." Verified
directly: `_build_invoke_command` returns `None` for `codex-ox` (§5);
`invocation_allowed`/`execution_authorized` are hardcoded `False` in the
backend-lock sync regardless of whether the local `codex` binary happens
to be on `PATH` (§7); `build_remote_policy()` excludes it from
remote-execution eligibility (§5). No documentation inspected (§24)
blurs this distinction.

## 7. Capability Declaration Accuracy

`codex-ox`'s `MULTI_AGENT_REGISTRY` entry: `capabilities=
("code_generation", "test_writing")` — **omits** `"runtime_execution"`,
which `codex-local`'s entry carries (fresh test
`test_codex_ox_capability_entry_differs_from_codex_local_by_missing_runtime_execution`
confirms this differential directly against the live registry, not from
reading the diff alone). Declared capabilities are consistent with
actual behavior: no code path treats `codex-ox` as capable of causing
file mutation, execution, commit, or push (`invocation_allowed`,
`execution_authorized`, `may_commit`, `may_push` are all `False` in the
synced backend lock — §9).

## 8. Agent-Config Accuracy

`get_agent_config("codex-ox").executable_hint == "codex"`, identical to
`codex-local`'s hint — confirming no new/fictitious binary is implied
(fresh test:
`test_codex_ox_agent_config_points_to_same_executable_as_codex_local_not_a_new_binary`).
`configuration_notes` independently scanned for provider/network overclaim
tokens (`openrouter.ai`, `api_key`, `apikey`, `bearer `,
`authorization:`, `http://`, `https://api`) — none present; the notes
state provider/model configuration is "external to PCAE," consistent
with §6/§16/§17.

## 9. Session-Bootstrap Verification

Fresh tests (not calling 2X's own test functions) exercise
`pcae session bootstrap --agent-id codex-ox` end-to-end via `pcae.cli.main`
in freshly-initialized temp harnesses:

- Core governance lock persists the literal string `"codex-ox"`
  (`read_agent_lock(root).agent_id == "codex-ox"`), re-read from a
  freshly-constructed `HarnessPath` object (simulating a new-process
  read, not reusing in-memory state).
- Backend-lock artifact (`.pcae/agent-locks/latest.json`) is written with
  `backend_name: "codex-ox"`, `backend_type: "codex"`,
  `invocation_allowed: false`, `execution_authorized: false`,
  `may_execute_shell: false`, `may_commit: false`, `may_push: false`.
- A fresh test monkeypatches `socket.socket` to raise `AssertionError` if
  called during bootstrap — bootstrap with `--agent-id codex-ox` still
  succeeds, independently proving no network socket is opened.
- The installed package's CLI entry point (`pcae.cli.main`, the same
  module `python -m pcae` resolves to) recognizes `codex-ox` identically
  — confirming this is not a repository-only, unpackaged behavior (§21).

## 10. Literal Identity Verification

Freshly re-verified end to end: input `"codex-ox"` → core governance
lock `agent_id == "codex-ox"` → backend-lock `backend_name ==
"codex-ox"` → `derive_producer_provenance` returns `{"kind": "codex-ox",
"source": "agent_lock"}` → stored intake record's `producer.kind ==
"codex-ox"`. No normalization to `codex`, `codex-local`, `ox`, or
`openrouter` observed at any hop; a dedicated grep of
`_derive_command_preview`/`_build_invoke_command` confirms `codex-ox` is
never string-substituted with another identity before being compared or
dispatched.

## 11. Generic Intake Compatibility / No Special-Case Branch

`git diff <pre-2X> 7dc2f0fa -- src/pcae/core/intake.py` is **empty** —
2X touched zero lines of the intake module. A fresh grep of
`intake.py`'s full text for `"codex-ox"`/`codex_ox` finds nothing.
Parametrized fresh test
`test_intake_path_identical_across_identities_for_equivalent_state` runs
the identical `validate_and_ingest_intake_candidate` path for
`claude-local`, `codex`, `codex-ox`, and an arbitrary unregistered
string producer and gets structurally identical outcomes
(`accepted=True`, `execution_allowed=False`, `promotion_executed=False`).

## 12. Producer-to-Authority Non-Flow

Fresh test
`test_producer_identity_has_no_effect_on_authority_relevant_outcome_fields`
constructs four equivalent candidates (identical task/base-commit/file
content) differing only in `producer.kind`
(`claude-local`/`codex`/`codex-ox`/`arbitrary-identity-42`) and confirms
identical `execution_allowed`, `promotion_executed`, `file_count`, and
`promotion_eligible_count` across all four. Producer identity is
confirmed to have zero effect on any authority-relevant field.

## 13. Forged Producer Authority Fields (codex-ox specific)

Fresh test
`test_forged_producer_authority_fields_from_codex_ox_do_not_change_canonical_authority`
submits a `codex-ox`-produced candidate whose `producer`/`producer_claims`
dicts contain forged `execution_allowed: true`,
`promotion_authorized: true`, `promotion_executed: true` keys. Result:
canonical `execution_allowed`/`promotion_executed` remain `False` on both
the immediate result and the persisted intake record; the forged keys
are preserved verbatim in the stored `producer`/`producer_claims` fields
(proving they are recorded for audit, not silently stripped, and
separately proving they had zero effect on the fields that matter).

## 14. Out-of-Scope Intake

Fresh test `test_out_of_scope_codex_ox_candidate_rejected_exactly_like_any_other_producer`
submits a `codex-ox` candidate touching a path outside the active task's
`allowed_files`. Rejected with `out_of_scope_path:...`, identical to the
rejection any other producer receives. Independently proves `codex-ox`
support confers no scope privilege.

## 15. No-Lock Compatibility

Fresh tests confirm: (a) with no governance lock active, an explicit
external producer (`"explicit-external-producer"`) still submits
successfully — 2X did not make bootstrap or registered-agent membership
mandatory for intake; (b) an entirely unregistered custom producer name
(`"totally-unregistered-agent-name"`) still round-trips through
`derive_producer_provenance` correctly after `codex-ox`'s registration,
confirming registration did not narrow the pre-existing "arbitrary
identity accepted" behavior established in 2W/2W.1; (c) a governance-lock
conflict test (lock held by `codex-ox`, explicit producer `"some-other-
identity"` supplied) still deterministically rejects with
`producer_conflicts_with_active_agent_lock`, exercising the conflict path
specifically with `codex-ox` as the locked identity.

## 16. No Dedicated Adapter / No Native Parser

Fresh repository-wide search for `codex_ox_intake_adapter`,
`codex_ox_adapter`, `ox_parser`, `openrouter_parser`, `codex_ox_parser`
name fragments across every `.py` file under `src/pcae`: zero matches.
Additionally confirmed the generic-looking `intake.py` module itself
contains no `codex-ox`/`codex_ox` branch anywhere in its text (not just
absent from filenames) — ruling out a hidden agent-specific branch inside
an otherwise-generic module, per the instruction not to rely on filename
search alone.

## 17. No OpenRouter / Ox Execution Integration

`git diff <pre-2X> 7dc2f0fa -- src/pcae/core/agent.py
src/pcae/commands/session.py` (the only two files touched) scanned
line-by-line for `requests.`, `urllib`, `http.client`, `socket.socket`,
`subprocess.run`, `subprocess.Popen`, `openrouter.ai`, `api_key=`,
`Authorization:` — zero matches among added lines. The diff adds no
import, no client construction, no dispatch call — registration is pure
metadata/configuration/bootstrap recognition, confirmed mechanically
rather than by re-reading the diff prose.

## 18. Authentication Boundary

No source or comment inspected (the `codex-ox` registry-entry docstring
and surrounding ~1.2KB of context) contains any authentication-overclaim
phrase ("codex actually ran," "ox actually produced," "openrouter
actually served," "authenticated execution," "verified model identity").
Correct semantics hold throughout: the persisted state is `session
declared agent_id = codex-ox`, never a claim that PCAE authenticated a
Codex/Ox execution, a specific model, or a specific account.

## 19. Vocabulary Fallback / Alias Analysis

No silent fallback found anywhere in the two changed files or their
callers:

- `_build_invoke_command("codex-ox", ...)` → `None` (not codex-local's
  argv) — independently exercised, not merely read.
- `_derive_command_preview("codex-ox", ...)` falls through to the
  generic `f"[preview] {hint} --prompt '...'"` branch (neither the
  codex-local nor claude/kimi special case) — this is a **preview
  string only**, produced for a job that `check_remote_job_readiness`
  will have already blocked at the `agent_allowed` gate
  (`"agent 'codex-ox' is not in allowed_agents"`) before any dry-run
  reaches `would_execute`. It never becomes an actual dispatched
  command; `_build_invoke_command`, the real dispatch function, is
  unaffected by this cosmetic preview-string quirk.
- `build_remote_policy()["allowed_agents"]` excludes `codex-ox` — a
  remote job requesting it is blocked before reaching `would_execute`
  regardless of the preview string above.
- No missing-registration-defaults-to-an-executable-backend path was
  found; every unrecognized/unregistered identity is handled by an
  explicit rejection (`_sync_backend_lock`'s "not a recognized lockable
  backend identity", `_build_invoke_command`'s `None`), never a silent
  default assignment to a real backend.

No Blocking silent-fallback-to-execution scenario exists.

## 20. W.1 Non-Blocking Findings — Status Confirmed Unrelated

Both W.1 findings independently re-triggered fresh, confirming they are
agent-identity-agnostic (the failure/degradation occurs before any
`agent_id` value — `codex-ox` or otherwise — is inspected):

1. Malformed `.pcae/agent-lock.json` (`"{not valid json"`) still raises
   an uncaught `json.JSONDecodeError` from `read_agent_lock` — reproduces
   identically regardless of what identity would have been recorded.
   **CONFIRMED, NON-BLOCKING, unrelated to codex-ox.**
2. A lock JSON missing the `agent_id` key still degrades
   `derive_producer_provenance` to `producer.kind == ""` (accepted,
   purely descriptive). **CONFIRMED, NON-BLOCKING, unrelated to
   codex-ox.**

Neither becomes Blocking for `codex-ox` specifically — both existed
identically before 2X's registration and are independent of which agent
identity is involved.

## 21. Independent Fast Green Attribution

Two full `-m fast_green -n auto` sweeps were run independently (not
reused from 2X's own numbers):

- **Clean baseline** (fixed `git worktree` at HEAD `a7410e83`, the
  committed state this phase started from): `334 failed, 8693 passed,
  5 skipped, 9 errors` (343 failure-class outcomes).
- **Working-tree state for this phase** (2X.1's own uncommitted
  additions — one new test file plus routine task-lifecycle files; no
  `src/pcae/**` changes): `335 failed, 8692 passed, 5 skipped, 9 errors`
  (344 failure-class outcomes).

Node-ID diff between the two runs' failure sets: exactly **one** delta —
`tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
present only in the dirty-tree run. Independently investigated: this
test shells out to `python -m pcae shell-gate audit verify` against the
real repository with a 15-second subprocess timeout. Re-run in isolation
while the machine was under heavy concurrent CPU load from this same
verification session's own parallel `fast_green`/`test_agent.py` sweeps,
it failed with `subprocess.TimeoutExpired`; re-run in isolation once
those competing processes had finished, it **passed in 9.37s**. This is
a resource-contention timeout artifact of running this verification
session's own heavy test suites concurrently, not a defect introduced by
2X.1's changes (which touch no `src/pcae` file) and not related to
`codex-ox` semantics in any way.

**Zero attributable regressions.** (2X.1's own diff is test/doc/task-file
only, so this sweep does not reproduce 2X's own reported 16-test
uncommitted-`src/pcae`-diff-guard delta — that class of guard test does
not trigger for a diff that touches no `src/pcae` file, which is exactly
what should happen and is independent corroboration that those guards
key off real production-source drift rather than an arbitrary trigger.)

## 22. Package/Install Behavior

`pyproject.toml`'s `[tool.hatch.build.targets.wheel]` sets `packages =
["src/pcae"]` (whole-package inclusion, not a curated file list) and the
sdist `include` list also carries `src/pcae` wholesale — both build
targets ship `agent.py`/`session.py` unmodified from source, so
`codex-ox`'s registration is packaged, not repository-only. Confirmed
behaviorally: the currently-importable `pcae.core.agent` module (the
same one `pcae.cli:main`, the packaged console-script entry point,
imports) carries the registration, and `pcae session bootstrap
--agent-id codex-ox` recognizes it end-to-end through that same
entry-point path in a fresh temp harness.

## 23. Documentation Truthfulness

`docs/PHASE_149O_20L_7O_2X_CODEX_OX_AGENT_REGISTRATION_AND_GENERIC_INTAKE_COMPATIBILITY.md`
and the current `PROJECT_STATUS.md` "Current Phase" entry were both
inspected. Neither uses an unqualified phrase like "Codex-Ox
integration" that would reasonably imply execution integration; both
explicitly separate "registered as a first-class supported identity" /
"generic-intake-provenance path" language from execution/runtime claims,
and both explicitly state the capability declaration deliberately
excludes `runtime_execution` and that runtime posture is unchanged
(`Observed`/`observe`/`unavailable`). `docs.py`'s generated-documentation
surface contains no `codex-ox` reference at all (§3), so no
generated-doc overclaim risk exists either. **No narrowing required.**

## 24. Release Readiness Interpretation

The release can truthfully advertise `codex-ox` as a supported PCAE
agent/session identity — for registration, bootstrap recognition,
governance-lock provenance, and generic intake compatibility — without
implying execution functionality that does not exist, **provided** any
release-facing copy uses language consistent with §6/§23 above (i.e.
does not compress this into a bare "Codex-Ox integration" claim). This
phase does not select a release version; that decision, and whether to
first repair the two carried-forward W.1 findings, is deferred to the
recommended next phase (§26).

## 25. Fresh Independent Tests

37 fresh tests added in
`tests/test_phase_149o_20l_7o_2x_1_independent_verification.py`, none of
which call or import any 2X test function. Coverage: pre-2X baseline
reconstruction from historical git source (4 tests), fresh full-registry
inventory across production vocabularies (5), capability/config
registration necessity and accuracy (4), session-bootstrap literal
identity/no-execution-authority/no-network (3), generic-intake
compatibility and producer-to-authority non-flow (2), forged producer
authority fields (1), out-of-scope intake (1), no-lock/unregistered-
custom-identity/lock-conflict compatibility (3), no dedicated
adapter/parser (2), no HTTP/subprocess dispatch added in the diff (1),
no authentication overclaim in source (1), vocabulary fallback/alias
analysis (3), W.1 finding identity-agnosticism (2), packaging (2).

## 26. Regressions Actually Run

- `tests/test_phase_149o_20l_7o_2x_1_independent_verification.py` — 37
  passed.
- `tests/test_phase_149o_20l_7o_2x_codex_ox_agent_registration.py`
  (2X's own suite, run as regression not as evidence) — passed.
- `tests/test_phase_149o_20l_7o_2w_1_independent_verification.py` —
  passed.
- `tests/test_phase_149o_20l_7o_2w_producer_provenance_integration.py`,
  `test_phase_149o_20l_7o_2u_2_reference_adapter_implementation.py`,
  `test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`,
  `test_phase_149o_20l_7o_2u_4_allow_deny_demo_acceptance.py`,
  `test_review.py`, `test_canonical_artifact_promotion.py`,
  `test_mutation_permission_promotion_integration.py` — 200 passed
  (intake/promotion/review regression group).
- `tests/test_agent.py` + `tests/test_session.py` (full files, `-n
  auto`) — **4381 passed, 0 failed** (593.87s).
- Full `fast_green` A/B (independent worktree-based clean baseline vs.
  this phase's own working tree) — §21.

## 27. Governance Results

- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae runtime inspect`: `execution_capability: unavailable`,
  `non_executing_posture: true`, `broker_implementation_status:
  execution_unavailable` — unchanged runtime posture, independently
  re-queried (not read from 2X's report).
- v0.3.0 tag, release, wheel/sdist, and release-claims: not touched by
  this phase (no commands in this phase's own history touch tag, release
  assets, or `docs/` article publication state).
- Private research repository `~/repos/pcae-deepseek-research`: not
  inspected, modified, or imported from.
- Article: unchanged/unpublished.

## 28. Findings

| # | Finding | Classification |
|---|---|---|
| 1 | `codex-ox` correctly reuses the generic producer-intake helper with no special-case branch; producer identity confirmed to have zero effect on any authority-relevant field, including under forged producer-authority-field injection specific to `codex-ox`. | CONFIRMED |
| 2 | All three deliberate omissions (backend invocation registry, runtime-probe list, PAP/IPILOT literals) are correct and non-lossy for the stated supported use case. | CONFIRMED |
| 3 | No silent fallback from `codex-ox` to any executable backend exists anywhere in the invocation, preview, or remote-policy paths. | CONFIRMED |
| 4 | Literal identity (`codex-ox`) is preserved end-to-end with no normalization, across bootstrap, lock readback, and intake provenance. | CONFIRMED |
| 5 | Capability/config registry entries for `codex-ox` are accurate and do not overstate executable capability relative to `codex-local`'s. | CONFIRMED |
| 6 | Current documentation (phase doc + `PROJECT_STATUS.md`) does not blur "supported identity" with "execution integration." | CONFIRMED |
| 7 | W.1's two carried-forward findings remain identity-agnostic and unrelated to `codex-ox`. | CONFIRMED, NON-BLOCKING (carried forward, unrepaired) |
| 8 | One Fast Green delta test (`test_audit_verify_cli`) is a resource-contention subprocess-timeout artifact of this verification session's own concurrent heavy test runs, not a 2X/2X.1 regression. | CONFIRMED, NON-BLOCKING |

**Zero Blocking findings.**

## 29. Final Verdict

```text
INDEPENDENTLY VERIFIED
— CODEX-OX AGENT REGISTRATION AND GENERIC INTAKE COMPATIBILITY COMPLETE

CODEX-OX SUPPORT SCOPE:
FIRST-CLASS AGENT/SESSION IDENTITY
BOOTSTRAP RECOGNITION
GOVERNANCE-LOCK PROVENANCE
GENERIC INTAKE COMPATIBILITY

PCAE-NATIVE CODEX-OX EXECUTION BACKEND:
NOT IMPLEMENTED

OPENROUTER/OX TRANSPORT:
NOT IMPLEMENTED

PRODUCER PROVENANCE:
DESCRIPTIVE
NON-AUTHENTICATING
NON-AUTHORIZING

DEDICATED ADAPTER:
NONE

NATIVE PARSER:
NONE

RUNTIME:
Observed / observe / unavailable
```

## 30. Recommended Next Action

Per the governing prompt's explicit instruction, this phase stops here.
Do **not** begin another agent-specific implementation phase next. The
next chapter should be a small **Post-v0.3 Release Hardening and Release
Scope Reassessment** phase to determine: the accumulated post-v0.3
capability set; whether the release should be `v0.3.1` or the next minor
version; whether the two W.1 lock-handling findings should be repaired
before release; release-critical documentation truthfulness;
packaged-capability set; installation/smoke validation; the
supported-agent matrix; and article-rewrite readiness. That phase should
not preselect the release version, and the article must not be published
until it runs.
