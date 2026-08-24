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

## 11–13. Build From Fixed Committed Tree / Wheel + Sdist / Checksums

[Populated after the governed commit — see §Finalization; this phase's
build, checksum, and clean-install evidence is bound to the exact
release-candidate commit SHA recorded there, per the governing
instruction not to treat a dirty working tree as authoritative release
evidence.]

## 14–19. Installed Smoke, Package Boundary, No-Lock, Codex-Ox, Authority Regression

[Populated after §11–13's build, from the built wheel/sdist in
disposable environments — see §Finalization.]

## 20. Clean Committed Regression Baseline

[Populated after the governed commit, run from the exact clean
committed release-candidate tree — see §Finalization.]

## 21. Resource-Sensitive Tests

[Populated alongside §20.]

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

Before: see §1. After: see §Finalization.

## 24. Stable-Tag Isolation (Final Re-Confirmation)

See §Finalization.

## 25. Publication Checklist

See §Finalization.

## 26. Release Blocker Table

See §Finalization.

## Recommended Next Phase

If this phase completes with zero unresolved BLOCKING/MUST-FIX items:
**149O.20L.7O.2Z.1 — PCAE v0.3.1 Public Release** (tag, GitHub Release,
artifact upload, post-publication smoke; PyPI and the article remain
untouched pending separate authorization). Not performed in this
phase.
