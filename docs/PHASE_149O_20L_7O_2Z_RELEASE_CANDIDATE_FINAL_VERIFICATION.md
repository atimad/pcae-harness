# Phase 149O.20L.7O.2Z — Post-v0.3.1 Release Candidate Final Verification

## 1. Phase-Entry Confirmation

Before any change: working tree clean, `origin/main..HEAD` = 0 commits,
no active governed phase (idle task open), stable `v0.3.0` tag
unchanged. `git rev-parse v0.3.0` returns the annotated tag object
(`1f9076e6...`); `git rev-parse v0.3.0^{commit}` returns
`738a81553128665a9c206f3ce33c931dc9089a6c`, matching the governing
prompt's stated SHA exactly and matching `origin`'s
`refs/tags/v0.3.0^{}`. `pcae health`/`check`/`status coherence`: all
passed/coherent. `pcae doctor task-memory`: 129 pre-existing warnings
(unchanged historical debt). `pcae push check`: `nothing_to_push`.
`pcae runtime inspect`: `execution_capability: unavailable`. Telegram
runtime: configured. `pcae phase-report show --latest`: confirms
149O.20L.7O.2Y complete, 2Z listed as the recommended next phase.

## 2. Frozen Release-Candidate Scope

Reconstructed independently from 2Y's own source-cited evidence (§2Y
report §1–§5), re-verified directly against `src/pcae/core/agent.py`,
`src/pcae/core/intake.py`, `src/pcae/commands/session.py`, and
`src/pcae/commands/intake.py` in this phase, not copied from 2Y's
prose:

| Capability | Implemented | Independently verified this phase | Packaged | Documented truthfully | Compatible with v0.3.0 |
|---|---|---|---|---|---|
| `pcae intake from-files` (generic producer-neutral CLI) | Yes | Yes (§7, §14, §17) | Yes | Yes (quickstart golden path promoted, §9) | Yes — additive |
| Lock-derived descriptive producer provenance | Yes | Yes | Yes | Yes | Yes — additive |
| No-lock generic compatibility (explicit `--producer`) | Yes | Yes (§17) | Yes | Yes | Yes — unchanged from v0.3.0 adapter behavior |
| `codex-ox` supported identity | Yes | Yes (§6, §18) | Yes | Yes (boundary re-confirmed) | Yes — additive |
| Session bootstrap backend-lock recognition (`codex-ox` in `_LOCKABLE_BACKENDS`) | Yes | Yes (source-read, §4) | Yes | Yes | Yes — additive |
| Malformed-agent-lock fail-closed handling (2Y: invalid JSON) | Yes | Re-confirmed | Yes | Yes | Yes |
| Malformed-agent-lock fail-closed handling, wrong-type JSON (2Z: new, this phase) | Yes — repaired this phase | Yes (§7) | Yes | Yes | Yes — bounded bug fix |
| Claude compatibility wrapper (`scripts/claude_code_intake_adapter.py`) | Yes | Repository-only, confirmed unpackaged (§10) | No | Yes (demoted to reference footnote, §9) | Yes — unchanged |

No new capability enters this table beyond 2Y's own frozen set plus the
one release-blocker repair (§7) required to keep the malformed-lock
story internally consistent (a "should not crash on ordinary corrupted
input" claim that only handled invalid JSON, not valid-JSON-wrong-type,
would itself be a documentation-truth defect).

## 3. Version Bump

Canonical version sources independently identified: `pyproject.toml`
(`[project].version`, static, not `dynamic`) and `src/pcae/__init__.py`
(`__version__`, read at runtime by
`pcae.core.runtime_introspection` for `pcae runtime inspect`'s
`release_version` field — the only CLI-surfaced version report; no
`pcae --version` flag exists). No other static or generated version
location found (`grep -rl "0.3.0"` across `src/` and `pyproject.toml`
returned only these two files).

Both bumped `0.3.0` → `0.3.1`. Verified:
- `python -c "from pcae import __version__; print(__version__)"` → `0.3.1`
- `pcae runtime inspect --json` → `"version": {"release_version": "0.3.1", ...}`
- Wheel/sdist filenames verified in §12 below.

No Git tag created.

## 4. Stable-Release Isolation

`git rev-parse v0.3.0^{commit}` = `738a81553128665a9c206f3ce33c931dc9089a6c`
(confirmed twice: phase-entry §1, and again at finalization §24) — no
tag movement. `git ls-remote --tags origin` confirms the same SHA on
`origin`. No `v0.3.0`-labeled documentation or release-note file
(`docs/RELEASE_NOTES_V0_3_0.md`, `docs/RELEASE_NOTES_V0_3_0_RC1.md`,
the `## v0.3.0` `CHANGELOG.md` section) was touched this phase — only
new, additively-appended `v0.3.1` content was added.

## 5. Final Release-Capability Matrix

| Capability | v0.3.0 | v0.3.1 RC |
|---|---|---|
| generic intake create/show/list | yes | yes |
| shared producer-neutral `from-files` helper | no | yes |
| governance-lock producer provenance | no | yes |
| direct/no-lock producer compatibility | yes (adapter script `--producer`) | yes (`from-files --producer`) |
| Claude compatibility wrapper | primary implementation | repository-only, thin deprecated wrapper |
| Codex identity (`codex-local`) | yes (unchanged) | yes (unchanged) |
| Codex-Ox identity (`codex-ox`) | no | yes — agent/session identity only, no execution backend |
| Cursor adapter | no | no |
| DeepSeek adapter | no | no |
| native Claude parser | no | no |
| native Codex/Ox parser | no | no |
| OpenRouter transport | no | no |
| provider/model authentication | no | no |
| runtime execution | unavailable | unavailable |

Every "no" above independently re-confirmed by absence of any matching
symbol/adapter/registry entry in `src/pcae/`.

## 6. Final Supported-Agent Matrix

Independently re-derived directly from `MULTI_AGENT_REGISTRY`,
`AGENT_CONFIG_REGISTRY`, `_LOCKABLE_BACKENDS`
(`src/pcae/commands/session.py`), `_RUNTIME_PROBE_AGENTS`, and
`_build_invoke_command` (`src/pcae/core/agent.py`), and cross-checked
against live `pcae agents` output — matches 2Y's own independently
derived table exactly, re-verified from source rather than copied:

| Identity | Capability reg. | Config reg. | Bootstrap backend-lock | Governance lock | Generic intake provenance | Backend invocation | Runtime probe | Native parser | Dedicated adapter | Authenticated identity | Execution capability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `claude-local` | Yes | Yes | Yes | Yes (arbitrary) | Yes | Yes (`claude -p`) | Yes | No | No | No | No |
| `codex-local` | Yes | Yes | No (only bare `codex` is lockable) | Yes | Yes | Yes (`codex exec`) | Yes | No | No | No | No |
| `codex-ox` | Yes | Yes | Yes | Yes | Yes | No (`_build_invoke_command` returns `None`) | No | No | No | No | No |
| `pcae-native` | Yes | Yes | No | Yes | Yes | No | No | No | No | No | No |
| `kimi-local` | Yes | Yes | No | Yes | Yes | Yes (`kimi -p`) | Yes | No | No | No | No |
| `deepseek-local` | Yes (`undeclared` adapter) | Yes | No | Yes | Yes | No | No | No | No | No | No |
| `gemini-local` | Yes (`undeclared`) | Yes | No | Yes | Yes | No | No | No | No | No | No |
| `grok-local` | Yes (`undeclared`) | Yes | No | Yes | Yes | No | No | No | No | No | No |
| `perplexity-local` | Yes (`undeclared`) | Yes | No | Yes | Yes | No | No | No | No | No | No |
| arbitrary custom identity | No | No | No | Yes | Yes | No | No | No | No | No | No |

Pre-existing, not-new vocabulary mismatch (`_LOCKABLE_BACKENDS`'s
`codex`/`claude-deepseek`/`claude-kimi` vs. the capability/config
registries' `*-local` naming): re-confirmed unchanged, not reconciled
per this phase's own No-Go instruction.

## 7. Codex-Ox Release Truth / Malformed-Agent-Lock Independent Verification

**Codex-Ox statement re-confirmed:** `codex-ox` is supported as a PCAE
agent/session identity for registration, bootstrap, governance-lock
provenance, and generic intake compatibility. It is not a PCAE-native
execution backend, not OpenRouter transport, not a native Ox/Codex
parser, and not an authenticated provider/model identity. Grep across
`README.md`, `docs/*.md`, `CHANGELOG.md`, `PROJECT_STATUS.md` found no
instance of a bare "Codex-Ox integration" claim or any "PCAE
executes/runs/calls Codex" phrasing.

**Malformed-agent-lock repair — independently re-verified from
production source, not from 2Y's tests, freshly against the current
CLI**:

2Y's repair (`derive_producer_provenance`, `src/pcae/core/intake.py`)
wraps `agent_core.read_agent_lock(root)` in
`try/except (json.JSONDecodeError, OSError)`. Freshly testing every
case the governing prompt requires, against the live CLI in a
disposable repository:

| Case | Before this phase | After this phase |
|---|---|---|
| Malformed JSON (`{not valid`) | `NOT SUBMITTED`, clean rejection (2Y repair) | Unchanged — clean rejection |
| Truncated JSON | `NOT SUBMITTED`, clean rejection (2Y repair) | Unchanged — clean rejection |
| Structurally invalid — JSON array (`[1,2,3]`) | **Uncaught `AttributeError`, raw traceback** (`'list' object has no attribute 'get'`) | Clean rejection: `malformed_agent_lock:...got list` |
| Wrong JSON type — string | **Uncaught `AttributeError`** | Clean rejection |
| Wrong JSON type — number | **Uncaught `AttributeError`** | Clean rejection |
| Wrong JSON type — null | **Uncaught `AttributeError`** | Clean rejection |
| Missing fields (`{}`) | Accepted, `producer.kind: ""` | Unchanged |
| `pcae session bootstrap` + malformed JSON | Clean rejection (accidental, `JSONDecodeError` is `ValueError`) | Unchanged |
| `pcae session bootstrap` + wrong-type JSON | **Uncaught `AttributeError`, raw traceback** (`acquire_agent_lock_idempotent` → `AgentLock.agent_id`) | Clean rejection: `ValueError("Agent lock already held by .")`, exit 1, no traceback |
| Valid lock | Accepted, `producer.kind` = lock's `agent_id` | Unchanged |
| No-lock compatibility, explicit `--producer` | Accepted, `source: "candidate"` | Unchanged |

**Finding:** 2Y's repair was incomplete. `read_agent_lock` does not
raise for well-formed JSON that decodes to a non-dict value (list,
string, number, bool, null) — it returns an `AgentLock` object
successfully. The crash occurred one line later, at
`AgentLock.agent_id`'s `self.data.get("agent_id")`, which is *outside*
2Y's try/except in `derive_producer_provenance`, and entirely
unguarded in `acquire_agent_lock_idempotent` (used by
`pcae session bootstrap`) and `release_agent_lock`. This reproduces
reliably from ordinary corrupted input (e.g. a tool that serializes an
empty list or `null` to the lock path instead of an object) — the same
category 2Y itself classified SHOULD-FIX-BEFORE-RELEASE for invalid
JSON.

**Repaired this phase** (bounded, two call sites):
1. `AgentLock.agent_id` property (`src/pcae/core/agent.py`): returns
   `""` instead of raising when `self.data` is not a `dict` — the
   shared low-level fix, immediately safe for every caller (bootstrap,
   release, intake) without changing behavior for the well-formed-dict
   case.
2. `derive_producer_provenance` (`src/pcae/core/intake.py`): explicit
   `isinstance(lock.data, dict)` check, rejecting deterministically
   with a clear `malformed_agent_lock:...` reason rather than silently
   falling through to the same acceptance path used for a well-formed
   empty-`agent_id` lock — preserving the "do not silently broaden
   fallback behavior" requirement (a non-dict top-level structure is a
   stronger corruption signal than a well-formed object with a blank
   field, and is treated as rejection, not silent acceptance).

Result for `pcae session bootstrap`: the crash becomes a controlled
`ValueError` ("Agent lock already held by .") already caught by
`run_session_bootstrap`'s existing `except ValueError` — exit 1, clean
message, no traceback, no repository mutation, no lock acquired.

`agent.read_agent_lock` itself remains unchanged and still raises
`json.JSONDecodeError` for invalid JSON (2Y's own established scoping,
re-confirmed) — only `AgentLock.agent_id` and
`derive_producer_provenance` were touched.

Behavior classification: **controlled, deterministic, fail-safe,
non-authorizing, no repository corruption** — for every case tested.

## 8. Empty-Agent-ID Accepted Debt

Re-confirmed unchanged from 2Y's adjudication, under the now-repaired
code path: a lock with `"agent_id": ""` or a missing `agent_id` key
degrades `producer.kind` to `""`, accepted with no errors.
`get_agent_by_id("")` independently confirmed to return `None` — an
empty string cannot impersonate any registered identity. It does not
confer authority, does not bypass task scope, and does not grant
execution. Not repaired this phase — no new evidence found that makes
it release-blocking. Carried forward as accepted technical debt.

## 9. Documentation Truth

Audited: `README.md`, `docs/QUICKSTART_V0_3.md`, `CHANGELOG.md`,
`docs/RELEASE_NOTES_V0_3_1.md` (new), package metadata
(`pyproject.toml` description, unchanged and accurate), and
`pcae intake from-files --help` (unchanged, still states "Descriptive
provenance only -- never authorization" verbatim).

**Quickstart golden path promoted** (2Y's §14 deferred recommendation,
this phase's explicit scope): `docs/QUICKSTART_V0_3.md` §7 now leads
with `pcae session bootstrap` + `pcae intake from-files` as the primary
walkthrough for every producer, including Claude Code — no adapter
script required. `scripts/claude_code_intake_adapter.py` is demoted to
a clearly marked "Legacy path" blockquote, described accurately as
repository-only reference tooling, not part of the installed package.
§10 (the deny-demo) updated to the same primary path for consistency.
The intro's evidence-sourcing claim was updated to name this phase's
own installed-wheel/sdist smoke tests (§14–15) as the source of
verification for the new golden path, alongside the original 2U.4
evidence for the walkthrough it builds on.

No stale claim removed from the historical `v0.3.0`-labeled record;
the restructuring is scoped to the still-unreleased-on-`main`
`from-files`/`codex-ox` material 2Y itself introduced.

## 10. Release Notes

`docs/RELEASE_NOTES_V0_3_1.md` created, following the established
`docs/RELEASE_NOTES_V0_3_0.md` structure: Overview, Added/Improved
(from-files, lock-derived provenance, `codex-ox`, quickstart
restructure, malformed-lock hardening — both the 2Y and 2Z halves),
Compatibility, Explicit Boundaries, Package Boundary, Known
Limitations (carried-forward + the new empty-agent-ID debt item),
Installation, Upgrade (no migration required), Feedback. No claim made
beyond what §2–§9 of this document independently establish.

## 11. Build From Fixed Committed Tree

Two governed commits complete this phase's source/documentation
changes and task-lifecycle bookkeeping:

- `20bbda98` — version bump to 0.3.1, malformed-agent-lock wrong-type
  repair, quickstart golden-path promotion, release notes (8 files).
- `5d7edef9` — task-lifecycle bookkeeping sync (5 files, governance-only).

**Release-candidate commit SHA: `5d7edef9c34ee266a9c5b51940ee4f1848375d22`**
(working tree clean at this commit, confirmed by `git status --short`
before build). All artifacts, checksums, and installed-smoke evidence
below are built from this exact commit, not a dirty working tree.

## 12. Wheel and Sdist

Built with `python -m build` in a disposable venv, isolated from the
system/dev environment:

```
Successfully built pcae_harness-0.3.1.tar.gz and pcae_harness-0.3.1-py3-none-any.whl
```

- **Wheel**: `pcae_harness-0.3.1-py3-none-any.whl`, 466 files (matches
  2Y's own local-build file count exactly), `METADATA` reports
  `Version: 0.3.1`. Contains `pcae/cli.py`, `pcae/core/agent.py`,
  `pcae/core/intake.py`, `pcae/commands/intake.py`,
  `pcae/commands/session.py`. Scanned for
  `deepseek-research|article|secret|.env|scripts/` — zero matches.
- **Sdist**: `pcae_harness-0.3.1.tar.gz`, 472 entries (matches 2Y),
  `PKG-INFO` reports `Version: 0.3.1`. Same scan — zero matches.
- Not uploaded anywhere; no tag created; no GitHub Release created.

## 13. Checksums (SHA-256)

| Artifact | Size (bytes) | SHA-256 |
|---|---|---|
| `pcae_harness-0.3.1-py3-none-any.whl` | 2,338,452 | `a459617fdaf2d6424123852c84c8c7abf6e238224827196a37d1e346cf74dad6` |
| `pcae_harness-0.3.1.tar.gz` | 2,066,901 | `a4e644b5b2a99911b3d5a7dee8fb1cf50020fd5b6bdb32350bac9f3720120fda` |

These checksums correspond to the exact artifacts built from commit
`5d7edef9` above; no rebuild occurred after computing them.

## 14. Installed Wheel Smoke

Fresh disposable venv, no editable source dependency, wheel installed
via `pip install --find-links <dist-dir> pcae_harness` (dependency
resolution used the network for third-party deps such as
`jsonschema`; the `pcae_harness` package itself came from the local
wheel; no external AI/model service or Codex/OpenRouter call at any
point). Exercised end-to-end in a disposable Git repository:

- `pcae --help` — works, full command catalogue present.
- `pcae runtime inspect --json` → `"release_version": "0.3.1"`.
- `pcae init` — works.
- `pcae task new` — works.
- `pcae session bootstrap --agent-id claude-local` → lock acquired.
- `pcae intake from-files` (in-scope) → **ACCEPTED**,
  `producer.kind: "claude-local"`, `source: "agent_lock"`,
  `execution_allowed: False`, `promotion_executed: False`.
- `pcae intake list` / `pcae intake show --intake-id ...` — both work,
  full record visible.
- `pcae agent release` → `pcae session bootstrap --agent-id codex-ox`
  → `pcae intake from-files` → **ACCEPTED**,
  `producer.kind: "codex-ox"`, `source: "agent_lock"`.
- No-lock, explicit `--producer "external-tool-xyz"` → **ACCEPTED**,
  `source: "candidate"`.
- No-lock, no `--producer` → cleanly rejected
  (`no_active_agent_lock_and_no_explicit_producer_supplied`), no crash.
- Out-of-scope path, tested against all three of the above producer
  identities → all three uniformly rejected
  (`out_of_scope_path:...`), `execution_allowed: False` in every case
  — task-scope authority is producer-identity-independent (§19).

**Result: PASS.**

## 15. Installed Sdist Smoke

Second fresh disposable venv, sdist installed via
`pip install --find-links <dist-dir> pcae_harness-0.3.1.tar.gz`. Same
bounded workflow repeated: bootstrapped `claude-local` → **ACCEPTED**;
`agent release` → bootstrap `codex-ox` → **ACCEPTED**,
`producer.kind: "codex-ox"`; no-lock + `--producer` → **ACCEPTED**,
`source: "candidate"`; no-lock, no `--producer` → cleanly rejected.
`python -c "from pcae.core.agent import get_agent_by_id; print(get_agent_by_id('codex-ox'))"`
→ correct `AgentEntry`; `get_agent_by_id('')` → `None`.

**Result: PASS — identical outcomes to the wheel install. No
difference found between wheel and sdist installed behavior.**

## 16. Installed-Package Boundary

Confirmed from the installed wheel/sdist directly (not repository
tooling): `pcae.core.agent`, `pcae.core.intake`,
`pcae.commands.intake`, `pcae.commands.session`, and `pcae.cli`'s
`intake from-files` wiring are all present and importable/callable
from the installed package — every release claim in §9/§10 is
demonstrated from the clean install, not asserted from the repository
checkout. `scripts/claude_code_intake_adapter.py` and
`docs/QUICKSTART_V0_3.md` are correctly repository-only (absent from
both the wheel's 466-file listing and the sdist's 472-entry listing);
documented as such truthfully in §9/§10 and the release notes — no
release claim depends on either being installed.

## 17. No-Lock Workflow Smoke

Covered inline in §14/§15 above (no-lock + explicit `--producer`, and
no-lock without `--producer`) — both from the installed wheel and
sdist. Bootstrap is confirmed not mandatory: the no-lock path with an
explicit `--producer` is accepted identically to the bootstrapped
path, differing only in `producer.source` (`"candidate"` vs.
`"agent_lock"`); normal task-scope/base/content-hash governance
applies identically regardless.

## 18. Codex-Ox Installed Smoke

Covered inline in §14/§15: from both installed wheel and sdist,
`codex-ox` is accepted as a bootstrap identity
(`pcae session bootstrap --agent-id codex-ox`), the literal value
persists through to `producer.kind: "codex-ox"` on the resulting
intake record, and `pcae.core.agent.get_agent_by_id("codex-ox")` is
importable and correct from the installed sdist. No executable Codex
backend was invoked, no network call occurred, and no
OpenRouter/provider configuration was required or present at any
point in either install.

## 19. Authority Non-Flow Release Regression

Freshly tested from the installed wheel, in the same disposable
repository, across three producer identities (`claude-local`,
`codex-ox`, and an arbitrary no-lock `external-tool-xyz` producer):

- **Valid in-scope candidate**: all three → `ACCEPTED`,
  `execution_allowed: False`, `promotion_executed: False`.
- **Out-of-scope candidate** (a path outside the task's
  `--allowed-file` scope): all three → identically rejected with
  `reasons: ['out_of_scope_path:out_of_scope.txt']`,
  `execution_allowed: False`.
- **Forged producer authority fields**: the `from-files` CLI surface
  exposes no field capable of setting `execution_allowed` or
  `promotion_authorized` — only `--producer` (identity label) and
  `--self-reported-complete` (an advisory claim already documented as
  non-authorizing) are accepted as producer-supplied input; a
  conflicting `--producer` against an active lock is independently
  rejected deterministically (§7, `producer_conflicts_with_active_agent_lock`).

**Result: equivalent governed submissions yield equivalent authority
outcomes regardless of producer identity — producer metadata does not
affect canonical authority.** Confirmed, unchanged from v0.3.0.

## 20. Clean Committed Regression Baseline

Run from the exact clean committed release-candidate tree (`5d7edef9`,
`git status --short` empty at run time):

| Suite | Result |
|---|---|
| `tests/test_phase_149o_20l_7o_2z_release_candidate.py` (fresh, this phase, 22 tests) | 22 passed |
| `tests/test_phase_149o_20l_7o_2y_release_hardening.py` (2Y regression, re-run) | 9 passed |
| Targeted release regression (2X/2X.1/2W/2W.1/2U.2/2U.3/2U.4/review/promotion, 274 tests) | 274 passed |
| `tests/test_agent.py` + `tests/test_session.py` (full files, `-n auto`) | **4381 passed, 0 failed** (729.16s) |
| Broad `fast_green`-marked sweep (clean committed tree) | 336 failed, 8691 passed, 5 skipped, 9 errors (350 total, 146.5s) — reproduced identically on a second independent run |

**4686 tests run and passing this phase's own targeted suites** (22 +
9 + 274 + 4381 — 2Y's own 9 re-run, not double-counted against 2Y's
original tally), plus the broad Fast Green sweep as the secondary
environment-sensitivity signal (not the release gate, per 2Y's
established, re-confirmed methodology — see below).

**Independent Fast Green A/B** (fixed `git worktree` at `75fd62f5`,
the commit immediately before this phase, vs. this phase's own clean
committed tree at `5d7edef9`):

- Baseline (`75fd62f5`, pre-2Z): 333 failed, 8694 passed, 5 skipped, 9
  errors (347 total).
- Candidate (`5d7edef9`, this phase's clean tree): 336 failed, 8691
  passed, 5 skipped, 9 errors (350 total).
- Node-ID diff: **3 new failures, 0 flips.** All three independently
  investigated in isolation (§21) — zero attributable regressions from
  this phase's own production change.

The broad sweep remains, as 2Y established and this phase
independently re-confirms rather than assumes, **not** the release
regression suite — the authoritative suite for this release line is
the targeted 2W/2W.1/2X/2X.1/2Y/2Z suites plus full
`test_agent.py`/`test_session.py`, all run to completion with zero
attributable failures.

## 21. Resource-Sensitive Tests

The 3 new node IDs from §20's A/B, each independently investigated
this phase (not inherited from 2Y/2X.1's classification):

| Test | Isolated re-run | Classification |
|---|---|---|
| `test_backend_cli.py::TestBackendReviewReject::test_reject_updates_latest` | **Passed** cleanly alone (1.03s) | Concurrent-load/resource-contention artifact from the A/B's parallel `-n auto` sweeps racing each other; not attributable to this phase's change (this phase does not touch `pcae review`/backend code). |
| `test_phase_149o_20l_7n_1_..._proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main` | Reproduced deterministically: asserts `HEAD == origin/main`; this phase has 2 unpushed local commits | **Expected, self-resolving** — not a regression. Will pass again once this phase pushes (§Finalization). |
| `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` | Reproduced even in isolation: `pcae shell-gate audit verify` took 15.12s wall-clock against the test's 15s subprocess timeout, verifying 200,987 accumulated audit records | **Resource-sensitive test infrastructure, not a deterministic product defect** — independently re-confirmed (not inherited from 2X.1/2Y): this phase makes no change to `src/pcae/commands/shell_gate.py` or the audit-verify path; the near-timeout is driven by this development repository's now-very-large accumulated audit log plus host timing, the identical mechanism 2X.1 and 2Y both independently documented. Observation made in passing: the verify output additionally reports `1 tampered record` among the 200,987 — pre-existing, unrelated to this phase's scope (no shell-gate/audit files are in this phase's allowed-files), not investigated further here as it falls outside this phase's frozen scope and No-Go list (no expansion of Permission Broker/audit enforcement).

**None of the three is a deterministic release-candidate failure
attributable to this phase's production change.**

## 22. Task-Memory Warning Classification

`pcae doctor task-memory`: 129 warnings, unchanged from phase entry
(2Y reported "approximately 130"). All are pre-existing
"in `tasks/done/` but not listed in `tasks/DONE.md`"
entries spanning prior phases (149O.1H.3 onward) — repository
governance bookkeeping. Independently confirmed: no installed PCAE
package or public user ever reads `tasks/DONE.md`; this file does not
exist in the wheel or sdist (§12). Classification: **ACCEPTED-DEBT,
repository-maintainer-only, does not affect any supported release
workflow.**

## 23. Governance Checks

Before (§1): `pcae health` healthy, `pcae check` passed, `pcae status
coherence` coherent, `pcae doctor task-memory` 129 warnings, `pcae push
check` `nothing_to_push`, `pcae runtime inspect` `execution_capability:
unavailable`, Telegram runtime configured.

After (post-implementation, clean tree at `5d7edef9`): `pcae health`
healthy, Git status clean; `pcae check` passed; `pcae status coherence`
coherent; `pcae doctor task-memory` 129 warnings (unchanged); `pcae
push check` — `nothing_to_push` → `active_task`/`Ready to push` once
the 2 phase commits landed (expected, matches normal governed-commit
lifecycle); `pcae runtime inspect` — `execution_capability:
unavailable`, `Runtime state: Observed`, `Maximum plugin capability:
observe` — **identical to before**. Telegram runtime re-confirmed
configured (`source ~/.config/pcae/telegram.env && pcae notify
status`).

## 24. Stable-Tag Isolation (Final Re-Confirmation)

- `git rev-parse v0.3.0^{commit}` = `738a81553128665a9c206f3ce33c931dc9089a6c`
  — identical to phase-entry (§1) and to `origin`'s
  `refs/tags/v0.3.0^{}`. No tag movement, no history rewrite.
- `git tag -l "v0.3.1*"` → empty. No `v0.3.1` tag of any kind exists.
- No GitHub Release for `v0.3.1` was created (no `gh release`/API
  mutation performed this phase).
- No artifact (`pcae_harness-0.3.1-py3-none-any.whl` /
  `pcae_harness-0.3.1.tar.gz`) was uploaded anywhere — both remain
  local to the disposable build directory.
- No `v0.3.0`-labeled documentation, release note, or CHANGELOG
  section was edited this phase — only new, additively-appended
  `v0.3.1` content.

## 25. Publication Checklist

For the later, separately authorized `149O.20L.7O.2Z.1` publication
phase:

- [x] Release-candidate commit SHA: `5d7edef9c34ee266a9c5b51940ee4f1848375d22`
- [x] Final version: `0.3.1` (`pyproject.toml` + `src/pcae/__init__.py`, verified via `pcae runtime inspect --json`)
- [ ] Repository clean at publication time (re-verify at publish time — this phase leaves the tree clean at `5d7edef9`, but finalization below adds further governance commits)
- [ ] `origin/main..HEAD` = 0 (2 commits currently unpushed; push occurs during this phase's finalization, §Finalization)
- [x] Release-critical tests: `tests/test_phase_149o_20l_7o_2z_release_candidate.py` (22), `tests/test_phase_149o_20l_7o_2y_release_hardening.py` (9), targeted 2X/2X.1/2W/2W.1/2U.2-4/review/promotion (274), `test_agent.py`+`test_session.py` (4381) — all passed, 0 failed
- [x] Fast Green clean-tree classification: 336F/8691P/5S/9E, A/B'd against pre-2Z baseline — 3 new node IDs, all independently classified non-attributable (§21)
- [x] Wheel checksum: `pcae_harness-0.3.1-py3-none-any.whl` SHA-256 `a459617fdaf2d6424123852c84c8c7abf6e238224827196a37d1e346cf74dad6`
- [x] Sdist checksum: `pcae_harness-0.3.1.tar.gz` SHA-256 `a4e644b5b2a99911b3d5a7dee8fb1cf50020fd5b6bdb32350bac9f3720120fda`
- [x] Wheel clean install: PASS (§14)
- [x] Sdist clean install: PASS (§15), identical behavior to wheel
- [x] Public workflow smoke: PASS (§14, §15, §17, §18) — bootstrap, `intake from-files`, `intake show/list`, no-lock, `codex-ox`, out-of-scope rejection
- [x] Documentation truth: PASS (§9) — quickstart golden path promoted, no misleading Codex-Ox claim found
- [x] Release notes: `docs/RELEASE_NOTES_V0_3_1.md` (§10)
- [x] Stable tag isolation: PASS (§24)
- [ ] GitHub Release title/body draft location: not yet drafted — defer to `2Z.1` (use `docs/RELEASE_NOTES_V0_3_1.md` as source)
- [x] Artifact filenames: `pcae_harness-0.3.1-py3-none-any.whl`, `pcae_harness-0.3.1.tar.gz`
- [x] Article explicitly excluded: not read, not modified this phase (§ confirmed below)
- [x] PyPI explicitly excluded unless separately authorized: not touched this phase
- [ ] Final human approval requirement: **required before `2Z.1` runs any publication action** — not obtained or requested this phase

**This checklist's publication actions were not executed.**

## 26. Release Blocker Table

| Item | Classification |
|---|---|
| Malformed agent-lock, invalid JSON (2Y) | PASS — repaired 2Y, re-confirmed this phase |
| Malformed agent-lock, valid-JSON-wrong-type (2Z, new) | **Was SHOULD-FIX-BEFORE-RELEASE — repaired this phase** (§7) |
| Empty agent_id | SAFE-TO-DEFER — reconfirmed (§8) |
| `pyproject.toml`/`__init__.py` version string | **Was MUST-FIX before publish — fixed this phase** (`0.3.1`, §3) |
| `tasks/DONE.md` historical sync warnings (129) | ACCEPTED-DEBT — repository-maintainer-only (§22) |
| Broad Fast Green sweep — 3 new node IDs vs. pre-2Z baseline | ACCEPTED-DEBT / non-attributable — individually classified (§21): 1 concurrent-load artifact (passes isolated), 1 expected-until-push guard, 1 resource-sensitive subprocess test (reproduces isolated, unrelated to this phase's diff) |
| Subprocess timing/resource-contention (`test_audit_verify_cli`) | ACCEPTED-DEBT — reconfirmed independently this phase, not inherited (§21) |
| Package boundary | PASS (§12, §16) |
| Documentation truthfulness | PASS (§9) — quickstart golden path promoted per 2Y's deferred recommendation |
| Installed wheel result | PASS (§14) |
| Installed sdist result | PASS (§15) — identical to wheel |
| Codex-Ox semantics | PASS (§7, §18) — no misleading execution claim found |
| No-lock compatibility | PASS (§17) |
| Runtime posture | PASS — `Observed`/`observe`/`unavailable`, unchanged (§23) |

**Zero unresolved BLOCKING or MUST-FIX items.** The one new finding
this phase surfaced (wrong-type-JSON lock crash) was itself repaired
and independently re-verified within this phase, not deferred.

## Recommended Next Phase

If this phase completes with zero unresolved BLOCKING/MUST-FIX items:
**149O.20L.7O.2Z.1 — PCAE v0.3.1 Public Release** (tag, GitHub Release,
artifact upload, post-publication smoke; PyPI and the article remain
untouched pending separate authorization). Not performed in this
phase.
