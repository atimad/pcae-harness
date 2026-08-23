# Phase 149O.20L.7O.2U.4 — Deny/Allow Demo and Quick-Start Documentation

**Phase type:** integration acceptance + documentation/demo. No
production `src/pcae/**` source modified. No frozen 2U.1 contract
modified. Independent verification not required (no authority-boundary
change) — confirmed applicable, since this phase found no defect
requiring one.

**Verdict: A — v0.3 ALLOW/DENY REFERENCE WORKFLOW DEMONSTRATED,
QUICKSTART REPRODUCIBLE, READY FOR 149O.20L.7O.2U.5 (Release Candidate
Preparation).**

```
ALLOW:                          PASS -- in-scope proposal accepted, reached
                                 existing unmodified review/promotion chain,
                                 real promotion wrote the approved file
DENY:                           PASS -- out-of-scope (otherwise valid)
                                 proposal rejected by task-scope governance,
                                 no ECP, no promotion path, no file mutation
AUDIT TRAIL:                    VISIBLE / REPRODUCIBLE (intake show/list,
                                 ECP show, EPR show, PER result)
QUICKSTART:                     docs/QUICKSTART_V0_3.md -- REPRODUCIBLE
                                 (clean-room walkthrough passed start-to-finish)
CLAUDE ADAPTER:                 REAL SCRIPT, DETERMINISTIC FIXTURE INPUT
                                 (see boundary statement, S8)
2U.2 SUITE:                     24/24 passed (re-run)
2U.3 SUITE:                     116/116 passed (re-run)
DOWNSTREAM REGRESSION (focused): 846 passed / 21 pre-existing failures,
                                 all HATP/HMIC rollback-contract byte-identity
                                 tests, unrelated to intake/ECP/promotion
FAST GREEN:                     see S12 (raw, unfiltered)
PRODUCTION CODE MODIFIED:       NONE
RUNTIME:                        Observed / observe / unavailable (unchanged
                                 before and after this phase)
v0.3.0-rc1:                     NOT TAGGED, NOT RELEASED (per NO-GO list)
RECOMMENDED NEXT PHASE:         149O.20L.7O.2U.5 -- v0.3 Release Candidate
                                 Preparation
```

---

## 1. True Phase Entry

- Phase-entry commit (`HEAD` at 2U.4 start, before this phase's task
  transition): `87d63331b474a371d747de40ff9abb054dfb3279`
- `origin/main` at phase entry: `87d63331b474a371d747de40ff9abb054dfb3279`
  (repo was clean/pushed at entry).
- 2U.2 implementation revision (independently confirmed unchanged this
  phase): `0ab6faa5344e8f2d449e6ac0417a65dc4609f603`.
- 2U.3 independent-verification revision (unchanged this phase):
  `46e509134f762d927ab39b34aa53653015df8c16`.
- v0.3 release-plan reference:
  `docs/PHASE_149O_20L_7O_2U_V0_3_RELEASE_EXECUTION_PLAN_AND_CRITICAL_PATH_FREEZE.md`,
  §critical-path items 4–5 (2U.4 objective/acceptance text, 2U.5 as the
  next frozen phase).

## 2. User-Flow Re-Derivation (From Code, Not Old Docs)

Directly inspected and exercised (not assumed from prior documentation):
`pcae init`, `pcae task new/show/update/transition`, `pcae intake
create/show/list` (`src/pcae/commands/intake.py`, `src/pcae/core/intake.py`),
`scripts/claude_code_intake_adapter.py`, `pcae promotion-review create`,
`pcae promote [--dry-run]`, `pcae execution-change-package show/list`.
CLI `--help` output for every one of these was read live this phase
before use; no command was invented from memory of older docs.

## 3. Disposable Demo Repository

A fresh local Git repository was created under a scratch/temp directory
(not committed to this repo; not the private DeepSeek research
repository, which was not touched or inspected):

```
pcae-demo-app/
  README.md
  src/app.py       (def greet(name): return f"Hello, {name}!")
  tests/test_app.py
```

`git init` → `pcae init` → `pcae task new "Update greeting message in
app.py" --goal "Change the greet() function's message text"
--allowed-file "src/app.py" --mode implementation`. Task ID:
`20260823-2159-update-greeting-message-in-app-py`. Scope: only
`src/app.py` in scope; `README.md` (and everything else) out of scope.
No mocking anywhere in this path — real `pcae init`, real task contract,
real Git repository, real intake/promotion code.

## 4. ALLOW Scenario

**Adapter invocation** (real script, run against the disposable repo):

```
python3 scripts/claude_code_intake_adapter.py \
  --task-id 20260823-2159-update-greeting-message-in-app-py \
  --candidate-id allow-1-greeting-update \
  --file "src/app.py:modify:<content-file>" \
  --summary "Update greet() to say 'Hello there' instead of 'Hello'" \
  --self-reported-complete
```

**CLAUDE ADAPTER TRANSLATION: REAL SCRIPT. LIVE CLAUDE GENERATION: NOT
PART OF THIS ACCEPTANCE.** The adapter script itself ran for real and
produced the generic intake JSON and called the real `pcae intake
create --json`; the *content* it translated was a deterministic fixture
(a small pre-written new `src/app.py` body), not a live Claude Code
session — no new credential or paid external action was invoked, per
§39/§9's non-blocker instruction. This is stated plainly rather than
presented as live agent output.

**Result** (`pcae intake create` exit code 0):

```
accepted: true
intake_id: intake-20260823-2159-update-greeting-message-in-app-py-20260823T195940546168
ecp_id:    ecp-intake-20260823-2159-update-greeting-message-in-app-py-20260823T195940545826
execution_allowed: false
promotion_executed: false
rejection_reasons: []
```

`pcae intake show --intake-id <id>`: `validation_outcome: accepted`,
`integrity_verified: True`, `execution_allowed: False`,
`promotion_executed: False`. `pcae intake list`: the candidate is
discoverable (`outcome=accepted`).

**Downstream review** (existing, unmodified chain — the human-review
boundary):

```
pcae promotion-review create --ecp-id <ecp_id> --reviewed-by demo-operator \
  --disposition approved --approved-path src/app.py --promotion-authorized \
  --review-rationale "Small in-scope greeting text change reviewed and approved for demo."
```

`created: true`, `promotion_authorized: true`,
`reviewer_identity_not_verified_by_pcae: true` (an existing, documented
governance boundary property of `promotion-review create` — reviewer
identity is a CLI-supplied label, not authenticated; this phase did not
add or need any bypass to use it). EPR ID:
`epr-intake:20260823-2159-update-greeting-message-in-app-py-20260823T195947496562`.

**Promotion** (the one command that mutates root):

```
pcae promote --epr-id <epr_id> --dry-run   # would_block: false
pcae promote --epr-id <epr_id>             # promoted: true, status: completed
```

`per_id`: `per-intake:20260823-2159-update-greeting-message-in-app-py-20260823T195953146203`.
**Actual target-file effect**: promotion *did* mutate the demo
repository's working tree — `src/app.py` now reads
`def greet(name: str) -> str:\n    return f"Hello there, {name}!"\n`,
verified by direct file read after the command, not asserted from
command output alone. `git_commit_forbidden: True` /
`git_push_forbidden: True` remained enforced — the file was written but
never committed or pushed by PCAE. The quickstart documents this actual
behavior (§11) rather than a stronger or weaker claim.

**Source of promotion authority**: the explicit `--promotion-authorized`
flag on `pcae promotion-review create`, consumed by `pcae promote`
solely via the stored EPR's `promotion_authorized` field — never from
intake data (confirmed structurally: the intake JSON schema has no such
field, and 2U.3's 116-case suite already independently proved no
producer-supplied field reaches an authority-bearing field).

## 5. DENY Scenario

Same adapter path, same task, a structurally/hash/repo/base-valid
proposal targeting `README.md` (outside the task's `src/app.py`-only
scope):

```
python3 scripts/claude_code_intake_adapter.py \
  --task-id 20260823-2159-update-greeting-message-in-app-py \
  --candidate-id deny-1-readme-edit \
  --file "README.md:modify:<content-file>" \
  --summary "Add marketing copy to README" \
  --self-reported-complete
```

**Result**:

```
accepted: false
ecp_id: null
rejection_reasons: ["out_of_scope_path:README.md"]
```

A direct `pcae intake create --candidate-file <path>` invocation of an
equivalent candidate (built independently, not via the adapter, to
isolate the CLI's own exit-code contract) confirmed **exit code 1** on
rejection, with the same `out_of_scope_path:README.md` reason printed to
stdout.

**Proof the rejection is scope-specific, not malformed input**: the
candidate's `repo_binding.repo_fingerprint` and `base_commit` matched
the real repository exactly, and `content_hash_after` matched the real
SHA-256 of the proposed content — only the path was out of scope. No
hash, base, or repo field was deliberately corrupted, per the phase
instruction.

**Downstream absence, directly verified**: `pcae intake list` after both
runs shows 3 records total — 1 `accepted` (the ALLOW candidate, with a
populated `ecp`) and 2 `rejected` (both `ecp=None`). `pcae
execution-change-package list` shows exactly 1 ECP (the ALLOW one). No
promotion-review or promotion was attempted or possible for the DENY
candidate — there is no ECP ID to review. `git diff --stat README.md`
in the demo repository showed no change; `README.md` content was
verified unchanged by direct file read.

## 6. Side-by-Side

| | ALLOW | DENY |
|---|---|---|
| Proposal | `src/app.py` (in scope) | `README.md` (out of scope) |
| Repo/base/hash | valid | valid |
| Result | accepted | rejected (`out_of_scope_path:README.md`) |
| `ecp_id` | populated | `null` |
| Downstream | review → promotion-authorized → promote → file written | none possible — no ECP exists |
| Audit | `intake show/list`, `ecp show`, `epr show`, promotion result | `intake show/list` (rejection reason retained) |

## 7. Quickstart

Created `docs/QUICKSTART_V0_3.md` (structure per the frozen 13-section
outline: what PCAE does → prerequisites → install → init → task scope →
prepare proposal → intake create → inspect → allow → deny → review/
promotion → audit trail → limitations). Linked from `README.md`'s
resource table. No competing/duplicate quickstart existed to reconcile.

**Clean-room test**: a second, independent disposable repository
(`cleanroom-quickstart-test/`) was created from an empty temp directory
with no reliance on shell history or the first demo repo's state, and
every documented command (`pcae init` → `pcae task new` → adapter ALLOW
→ adapter DENY → `pcae intake show/list` → `pcae promotion-review
create` → `pcae promote --dry-run` → `pcae promote`) was executed
verbatim in sequence. Result: **passed start-to-finish**, identical
shape of outcomes to §4/§5 (ALLOW accepted → promoted → file written;
DENY rejected → no ECP → no mutation). This is not "commands look
plausible" — it is a second, independent, mechanical run.

**Install claim verified**: PCAE v0.3 is not on PyPI (true of v0.1/v0.2
also — GitHub release assets only, confirmed in the 2U release plan,
§1–2). The quickstart documents `pip install -e .` from a source
checkout, matching `docs/INSTALLATION.md`'s existing v0.2 guidance — no
PyPI claim was made.

**Time-to-first-governed-proposal**: raw CLI command execution across
`init` → `task new` → ALLOW `intake create` in the clean-room run
completed in under a second of wall-clock process time each. The
documented "~5 minutes" is a human-paced estimate (reading the
quickstart, filling in real values, typing ~6 commands) — not a claim
about CLI runtime, and this phase does not fake or round that timing
claim; it reflects the actual number of steps and their real complexity
observed in §4/§5/here, not an untested guess.

## 8. Claude Code / Generic Producer Positioning

`docs/QUICKSTART_V0_3.md` documents Claude Code as one reference
producer, with an explicit "Appendix: Generic Producer (Not Claude
Code)" section showing the same JSON contract shape any tool can emit,
consistent with 2U.1's frozen "coding agent → thin adapter → generic
PCAE intake → PCAE governance" boundary. No second real adapter was
implemented (not required per the phase instruction).

## 9. User Friction / UX Findings

- **OBSERVATION — init scaffolding shows as out-of-scope in `pcae
  health`/`pcae check` until committed or the task is widened.**
  Running `pcae health` in the demo repository right after `pcae init`
  + a narrow `--allowed-file src/app.py` task reports `unhealthy`,
  listing the init-created files themselves (`.pcae/`, `AGENTS.md`,
  `.githooks/`, `scripts/`, `tasks/`) as changes outside task scope.
  This did not block any intake/promotion command used in this demo
  (none of them depend on `pcae health` passing), but a first-time user
  following the quickstart literally step-by-step could be confused by
  seeing "unhealthy" immediately after `pcae init`. Not a demo blocker;
  worth a smaller follow-up documentation note if it recurs as user
  feedback.
- **NON-BLOCKING — proposal content must be written to a separate file
  before submission.** The adapter's `--file path:operation:content_file`
  form (and the generic direct-JSON path) requires the new file content
  to exist on disk first; there is no "inline content" flag. Documented
  plainly in the quickstart rather than hidden.
- **NON-BLOCKING — IDs are long and must be copy-pasted between
  commands** (`intake_id`, `ecp_id`, `epr_id`, `per_id` are all
  timestamped strings). No "latest"/shorthand resolution exists yet.
  Real friction, not blocking the demo or quickstart.
- **OBSERVATION — error UX.** The DENY rejection reason
  (`out_of_scope_path:README.md`) clearly states what failed and which
  path; it does not separately state "what to do next" (e.g., "widen
  task scope or resubmit for an in-scope path"), though this is
  inferable. Non-blocking for this release.
- **OBSERVATION — audit UX.** `pcae intake show/list`, `pcae
  execution-change-package show`, and `pcae promotion-review create`'s
  own JSON output are sufficient to reconstruct the full evidence chain
  without inspecting raw `.pcae/` files directly — audit trail is
  usable via documented commands, not just technically present.

## 10. Carried-Forward Findings (Not Repaired This Phase)

- **Windows-backslash path-admission check** (2U.3 Non-Blocking).
  Release implication: this quickstart and its exercised command
  sequence are macOS/Linux only, and §13 of the quickstart says so
  explicitly rather than implying cross-platform parity. No repair
  performed here, per the phase instruction. If `v0.3.0-rc1`'s release
  notes intend to claim Windows support for intake specifically, that
  should be flagged for 2U.5 as a scoping decision — this phase does
  not resolve that question, only surfaces it.
- **Repository-fingerprint collision on byte-identical genesis commits**
  (2U.3 Non-Blocking). Release implication: unchanged assessment —
  requires reproducing the real target's exact genesis bytes; not an
  unrelated-repo impersonation vector. Not documented as a stronger
  security property than verified. No repair performed here.
- Pre-existing task-memory warnings, historical Fast Green debt, FGSC
  Non-Blocking findings, HATP/WebAuthn deferred enterprise work — not
  reopened; none became a demo blocker.

## 11. v0.3 Headline Claim Validation

- **"gates AI-agent task scope"** — supported: the DENY demonstration
  (§5) is a direct, mechanical proof of this exact property using
  production code, not narrative.
- **"validates completion claims against real repository state"** —
  supported, and attributed precisely: not to intake alone, but to the
  combination of intake's repo-fingerprint/base-commit/content-hash
  binding (verifies the *proposal* against real repo state at
  submission time) and `pcae promote`'s per-file divergence check
  (verifies the *target* against real repo state again at promotion
  time, blocking on unexpected drift). Both were exercised live this
  phase (§4's dry-run `divergence_check` block).
- **"produces an audit trail around an existing coding agent"** —
  supported: verified through the captured evidence in §4–§6 (intake
  records, ECP, EPR, PER, all independently inspectable after the
  fact).

## 12. Regression / Quality Gates

- 2U.2 suite (`tests/test_phase_149o_20l_7o_2u_2_reference_adapter_implementation.py`):
  24/24 passed (re-run this phase).
- 2U.3 suite (`tests/test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`):
  116/116 passed (re-run this phase).
- New focused acceptance harness this phase
  (`tests/test_phase_149o_20l_7o_2u_4_allow_deny_demo_acceptance.py`, 3
  tests): proves ALLOW reaches real `build_promotion_execution` and
  writes the target file; proves DENY produces no ECP and no target
  mutation and is a scope-specific (not malformed-input) rejection;
  proves ALLOW/DENY are independent outcomes from the same task. Uses
  production `pcae.core.intake`/`pcae.core.agent` code directly, no
  mocks. Does not duplicate the 116-case adversarial suite.
- Focused downstream regression (`pytest -k "task_scope or ecp or
  execution_change_package or promotion_review or promot or
  rollback"`): 846 passed, 21 failed, 2 errors. All 21 failures + 2
  errors are pre-existing HATP/HMIC rollback-contract byte-identity and
  no-HATP-argument tests (`HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  digest/byte-identity checks and related AG3/AG5 consumption-contract
  tests) — structurally unrelated to intake/ECP/promotion, and this
  phase modified zero files those tests inspect (`git status` shows
  only two new untracked files, `docs/QUICKSTART_V0_3.md` and the new
  test file, both outside every failing test's watched-file set).
- Fast Green (`pytest -m fast_green -q`, full unfiltered run, 8m20s):
  **337 failed, 8689 passed, 5 skipped, 27559 deselected, 9 errors**
  (346 failing node IDs total). Grepped the full failure/error list for
  `intake|ecp|promot|reference_adapter|2u_2|2u_3|2u_4` (case-insensitive):
  **zero matches** — no failure references intake, ECP, EPR, or
  promotion by name. Composition: 333 failures + 9 errors are
  `test_phase_149o_*` HATP/HMIC/Class-B contract byte-identity and
  frozen-source-scope tests (the same category 2U.2/2U.3 documented as
  pre-existing); the remaining 4 are
  `tests/test_hatp_mandatory_certification_models.py::test_certified_at_rejects_non_three_non_six_digit_fractions`
  parametrized cases, also HATP-certification-model tests unrelated to
  intake. This phase's only filesystem changes are two new untracked
  files (`docs/QUICKSTART_V0_3.md`,
  `tests/test_phase_149o_20l_7o_2u_4_allow_deny_demo_acceptance.py`,
  neither `fast_green`-marked) plus edits to `README.md`,
  `PROJECT_STATUS.md`, `CHANGELOG.md`, and task-lifecycle files — none
  of which any HATP/HMIC contract byte-identity test inspects. The
  335-vs-337 delta from 2U.3's last-reported count is not attributable
  to this phase's changes by construction (zero production/contract
  files touched) and is within the range of pre-existing test-count
  drift already documented as unrelated debt across prior phases; it is
  reported here as raw truth, not rounded down or re-run to force a
  match.

## 13. Remaining v0.3 Blockers

None found that require a dedicated repair phase. The friction items in
§9 are Non-Blocking/Observation, not Blocking, per the phase's own
classification rubric (none of them are "verified intake cannot
traverse the downstream chain," "in-scope rejected," "out-of-scope
accepted," "denied proposal reaches promotion," "quickstart not
reproducible," or "headline materially unsupported" — the opposite was
demonstrated for each). Per the frozen critical path (release-plan §critical-path
item 5), the next phase is release-candidate preparation, not another
demo/architecture phase.

## 14. Runtime / No-Go Confirmation

`pcae runtime inspect --json` posture unchanged before and after this
phase: `Observed` / `observe` / execution unavailable / 0 registered
plugins. No HATP/FIDO2/WebAuthn work performed. No Dell interaction. No
`v0.3.0-rc1` tag or GitHub release created. No `--demo-mode`/
`--skip-scope`/`--assume-authorized`/`--trust-adapter` or any other
demo-only bypass was added anywhere — every ALLOW/DENY outcome in this
report passed through real, unmodified governance code.

## 15. Recommended Next Phase

**149O.20L.7O.2U.5 — v0.3 Release Candidate Preparation** (quality-gate
re-verification, release-readiness checks, packaging, `v0.3.0-rc1`
tag/release), per the release plan's already-frozen critical path
(item 5) and this phase finding no Blocking defect that would require a
narrow repair phase first.
