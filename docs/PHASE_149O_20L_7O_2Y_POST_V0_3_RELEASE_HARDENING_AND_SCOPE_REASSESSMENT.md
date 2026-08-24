# Phase 149O.20L.7O.2Y — Post-v0.3 Release Hardening and Release Scope Reassessment

## 1. Stable v0.3.0 Baseline

Stable tag: `v0.3.0` (annotated tag object `1f9076e6...`, pointing to
commit `738a81553128665a9c206f3ce33c931dc9089a6c`) — matches the
prompt's stated SHA exactly, independently confirmed via
`git rev-parse v0.3.0^{commit}`. Tag, GitHub Release, and published
wheel/sdist are unmodified by this phase; this phase concerns only the
next release.

## 2. Complete Post-v0.3 Change Inventory

`git rev-list --count v0.3.0..HEAD` = 31 commits, all tracing to three
chains: 2V.1 (post-tag release-prep/task-lifecycle cleanup, no
production code), 2W/2W.1 (Generic Producer Intake Helper and Session
Provenance Integration + its independent verification), and 2X/2X.1
(Codex-Ox Agent Registration and Generic Intake Compatibility + its
independent verification).

`git diff --stat v0.3.0..HEAD`: 37 files changed, 5062 insertions(+),
2963 deletions(-). Production-source diff (excluding tests/docs/tasks/
.pcae governance bookkeeping): **6 files, +350/−107 lines**:
`src/pcae/core/agent.py`, `src/pcae/core/intake.py`,
`src/pcae/commands/session.py`, `src/pcae/commands/intake.py`,
`src/pcae/cli.py`, `scripts/claude_code_intake_adapter.py`.

Classification of every changed path:

| Path | Classification |
|---|---|
| `src/pcae/core/agent.py` | PRODUCT-FACING (codex-ox registration) |
| `src/pcae/core/intake.py` | PRODUCT-FACING (generic from-files helper; this phase adds a bounded fail-closed fix) |
| `src/pcae/commands/session.py` | PRODUCT-FACING (codex-ox backend-lock recognition) |
| `src/pcae/commands/intake.py` | PRODUCT-FACING + PACKAGING (`run_intake_from_files` CLI handler) |
| `src/pcae/cli.py` | PACKAGING (wires `pcae intake from-files` argparse subcommand) |
| `scripts/claude_code_intake_adapter.py` | INTERNAL HARDENING (reduced to a thin deprecated wrapper; repository-only, not packaged) |
| `PROJECT_STATUS.md`, `CHANGELOG.md`, `docs/PHASE_*.md` (4 new) | DOCUMENTATION |
| `.pcae/phase-completion-*.json/.md`, `.pcae/phase-metadata-repairs.log` | GOVERNANCE-ONLY |
| `tasks/**` (renames/adds) | GOVERNANCE-ONLY |
| `tests/**` (7 files, 4 new) | TEST-ONLY |

No UNRELATED/DEFERRED changes found — every post-v0.3 file change traces
to 2W/2W.1/2X/2X.1 or their governance bookkeeping.

## 3. Release-Candidate Capability Set

| Capability | Suitable for next release? |
|---|---|
| `pcae intake from-files` (generic producer-neutral CLI) | Yes — packaged, tested, documented (this phase adds quickstart/README coverage), truthful, supportable |
| Lock-derived descriptive producer provenance (`derive_producer_provenance`) | Yes — packaged, tested, now fail-closed on malformed input (this phase's repair) |
| No-lock generic compatibility (explicit `--producer`) | Yes — packaged, tested, unchanged v0.3 behavior preserved |
| Claude compatibility wrapper (`scripts/claude_code_intake_adapter.py`) | Repository-only tooling, not packaged — release claim narrowed to "reference example," not installed functionality (§10) |
| `codex-ox` supported identity | Yes — packaged, tested, documented, truthful boundary maintained (§5) |
| Session bootstrap backend-lock recognition | Yes — packaged, tested, unchanged behavior for pre-existing identities |
| Supported-agent registry updates (codex-ox only; other 4 unconfigured entries pre-date v0.3.0) | Yes for codex-ox; the four `undeclared`-adapter identities (deepseek/gemini/grok/perplexity-local) are pre-existing placeholders, not new, and remain correctly non-claimed |

## 4. Stable-vs-Current-vs-Proposed Matrix

| Capability | v0.3.0 | current `main` | proposed next release |
|---|---|---|---|
| Generic intake (`pcae intake create`) | Yes | Yes (unchanged) | Yes |
| Generic from-files CLI (`pcae intake from-files`) | No | Yes | Yes |
| Claude compatibility script | Only implementation (duplicated logic) | Thin deprecated wrapper over from-files | Yes, marked deprecated |
| Session-derived producer provenance | No (script hardcoded `"claude-code"`) | Yes, lock-derived | Yes |
| Arbitrary/custom producer support (no lock) | Yes (script's `--producer`) | Yes (`from-files --producer`) | Yes |
| `codex` (bare) backend-lock identity | Yes | Yes (unchanged) | Yes |
| `codex-local` capability/config registration | Yes | Yes (unchanged) | Yes |
| `codex-ox` registration | No | Yes | Yes |
| Cursor | Not registered anywhere | Not registered anywhere | Not registered |
| DeepSeek (`deepseek-local`) | Registered, `adapter_type: undeclared` | Unchanged | Unchanged — not a release claim |
| Native output parsing (any producer) | None | None | None |
| Runtime execution | Unavailable | Unavailable | Unavailable |
| Permission Broker enforcement | Unchanged | Unchanged | Unchanged |
| Promotion authority | Unchanged, human-gated | Unchanged | Unchanged |
| Provider/model authentication | None | None | None |

No integration is overclaimed in this matrix: DeepSeek/Gemini/Grok/
Perplexity remain placeholder registry entries pre-dating v0.3.0 with no
adapter, no executable hint, and no backend-lock recognition — unchanged
by this release line and not part of any release claim.

## 5. Supported-Agent Matrix

Independently derived directly from `MULTI_AGENT_REGISTRY`,
`AGENT_CONFIG_REGISTRY`, `_LOCKABLE_BACKENDS`, `_RUNTIME_PROBE_AGENTS`,
`_build_invoke_command`, and `build_remote_policy()["allowed_agents"]`:

| Identity | Capability reg. | Config reg. | Bootstrap backend-lock | Core governance lock | Generic intake provenance | Backend invocation | Runtime probe | Native parser | Dedicated adapter | Authenticated identity | Execution capability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `claude-local` | Yes | Yes (cli, `claude`) | Yes | Yes (arbitrary) | Yes | Yes (`claude -p`) | Yes | No | No | No | No (advisory-only preview) |
| `codex-local` | Yes | Yes (cli, `codex`) | **No** (only bare `codex` is in the lock set) | Yes (arbitrary) | Yes | Yes (`codex exec`) | Yes | No | No | No | No |
| `codex-ox` | Yes | Yes (cli, `codex`) | Yes | Yes (arbitrary) | Yes | **No** (`_build_invoke_command` returns `None`) | No | No | No | No | No |
| `pcae-native` | Yes | Yes (native) | No | Yes (arbitrary) | Yes | No | No | No | No | No | No |
| `kimi-local` | Yes | Yes (cli, `kimi`) | No | Yes (arbitrary) | Yes | Yes (`kimi -p`) | Yes | No | No | No | No |
| `deepseek-local` | Yes | Yes (`undeclared`) | No | Yes (arbitrary) | Yes | No | No | No | No | No | No |
| `gemini-local` | Yes | Yes (`undeclared`) | No | Yes (arbitrary) | Yes | No | No | No | No | No | No |
| `grok-local` | Yes | Yes (`undeclared`) | No | Yes (arbitrary) | Yes | No | No | No | No | No | No |
| `perplexity-local` | Yes | Yes (`undeclared`) | No | Yes (arbitrary) | Yes | No | No | No | No | No | No |
| arbitrary custom identity | No | No | No (unless in the fixed 7-name set) | **Yes** | **Yes** | No | No | No | No | No | No |

**Critical distinction preserved throughout:** "registered agent" (rows
above with capability/config-registry membership) is never confused with
"PCAE-native executable backend" — the only two identities with any
real subprocess-dispatch path are `claude-local`, `codex-local`, and
`kimi-local` (via `_build_invoke_command`), and even those are gated
behind `build_remote_policy()`'s allow-list, human-approval
requirements, and the frozen `execution_capability: unavailable` runtime
posture. `codex-ox` is deliberately excluded from that dispatch path
entirely (§ Codex-Ox Release Semantics below).

Also note the pre-existing, **not new**, vocabulary mismatch: the
session-bootstrap backend-lock set (`_LOCKABLE_BACKENDS`) uses a
different naming convention (`codex`, `claude-deepseek`, `claude-kimi`)
than the capability/config registries (`codex-local`, `deepseek-local`,
`kimi-local`) — documented since 2W/2W.1, unchanged and not reconciled
by this phase per its own No-Go instruction.

## 6. Codex-Ox Release Semantics

Frozen, truthful release-language boundary (re-confirmed, not
re-derived — already independently established in 2X.1):

> `codex-ox` is supported as a PCAE agent/session identity for
> bootstrap, descriptive producer provenance, and generic intake
> compatibility.

Explicitly **not**: "PCAE executes Codex through Ox/OpenRouter." Current
documentation (`docs/PHASE_149O_20L_7O_2X_*.md`, `PROJECT_STATUS.md`,
and this phase's own README/quickstart additions, §13) consistently
preserves this boundary — no instance of a bare "Codex-Ox integration"
phrase found.

## 7. W.1 Malformed-Lock Finding — Adjudication

Independently reproduced fresh (not from the 2W.1 report):

- `derive_producer_provenance`/`build_intake_candidate_from_files`
  (before this phase's repair) raised an uncaught `json.JSONDecodeError`
  on a malformed `.pcae/agent-lock.json`.
- **Affected commands**: `pcae intake from-files` (the packaged CLI
  command) and the deprecated `scripts/claude_code_intake_adapter.py`
  wrapper — both crashed with a raw Python traceback, exit code 1.
- **Not affected**: `pcae intake create` (never calls
  `derive_producer_provenance`) and `pcae session bootstrap` — the
  latter's crash was *accidentally* caught cleanly, because
  `json.JSONDecodeError` is a `ValueError` subclass and
  `run_session_bootstrap` already wraps its lock-acquire call in
  `except ValueError`.
- Does it permit unsafe acceptance? No — it fails before any
  accept/reject decision, exit code 1 either way.
- Does it create authority leakage? No — no field is set, nothing is
  written.
- Does it corrupt repository state? No — read-only failure.
- Does it prevent the no-lock fallback? No independently — but the
  crash occurs on a *present-but-corrupted* lock, a distinct condition
  from *no lock at all* (which already worked correctly).
- Is controlled fail-closed handling straightforward? Yes — a narrow
  `try/except (json.JSONDecodeError, OSError)` around the single
  `read_agent_lock` call inside `derive_producer_provenance`.

**Classification: SHOULD-FIX-BEFORE-RELEASE.** Not RELEASE-BLOCKING
(fails closed, no security defect), but a raw traceback from a packaged,
flagship CLI command on ordinary corrupted-file input is a real release
polish and public-support-burden concern the function's own docstring
already promised not to have ("never raises for ordinary input
problems").

**Repaired this phase** (bounded hardening, `src/pcae/core/intake.py`,
`derive_producer_provenance`): wraps `agent_core.read_agent_lock(root)`
in `try/except (json.JSONDecodeError, OSError)`, returning
`(None, ["malformed_agent_lock:<detail>"])` — a clean, fail-closed
rejection reason. Deliberately does **not** fall through to the no-lock
path (which would silently accept an explicit `--producer` even though a
real lock exists but is corrupted, masking the problem). Scoped to the
call site only — `agent.read_agent_lock` itself is unchanged and still
raises for other, lower-level callers whose contract does not promise
otherwise.

## 8. W.1 Empty-Agent-ID Finding — Adjudication

Independently reproduced fresh: a lock JSON with `"agent_id": ""` (or
the key missing entirely) degrades `derive_producer_provenance` to
`producer.kind == ""`, `source: "agent_lock"`, accepted with no errors.

- Structurally accepted: yes.
- Fallback: no invented value — the raw (empty) string is used verbatim.
- Can it impersonate another identity? No — independently confirmed
  `get_agent_by_id("")` returns `None`; an empty string is not, and
  cannot be confused with, any real registered identity.
- Does it affect authority? No — producer identity never flows into
  authority fields regardless of value (established in 2W.1/2X.1,
  re-confirmed this phase under the repaired code path).
- Does it merely weaken descriptive provenance quality? Yes — that is
  its only effect: an uninformative but harmless label.

**Classification: SAFE-TO-DEFER.** Not repaired this phase — repairing
it would require either inventing a placeholder value (violating "never
invent unknown," the function's existing documented policy) or requiring
registry membership (explicitly forbidden by this phase's own governing
instructions, since custom identities must remain supported). No release
harm from deferring.

## 9. Generic Intake Compatibility Regression (Fresh)

Both paths freshly re-verified this phase, from the **installed wheel**
in a clean venv (§12), not just in-repo unit tests:

- Bootstrapped: `pcae session bootstrap --agent-id claude-local` →
  governance lock → `pcae intake from-files` → `producer.kind:
  "claude-local"`, `source: "agent_lock"`. Repeated for `codex-ox` with
  identical structural outcome, `producer.kind: "codex-ox"`.
- Unbootstrapped: no lock held, `pcae intake from-files --producer
  "external-tool-xyz"` → accepted with `producer.kind:
  "external-tool-xyz"`, `source: "candidate"`.
- Unbootstrapped without `--producer`: cleanly rejected
  (`no_active_agent_lock_and_no_explicit_producer_supplied`), exit 1, no
  crash.
- All four cases: `execution_allowed: False`, `promotion_executed:
  False` — authority outcomes identical and producer-independent.

## 10. Package Boundary

`pyproject.toml`: `[tool.hatch.build.targets.wheel] packages =
["src/pcae"]` (whole-package inclusion) and
`[tool.hatch.build.targets.sdist] include = ["src/pcae", "README.md",
"LICENSE", "pyproject.toml"]`. Verified by building both artifacts this
phase (§11) and listing contents directly:

| Capability | Packaged? |
|---|---|
| `pcae.core.agent` (registries, `_build_invoke_command`, etc.) | **Yes** — `pcae/core/agent.py` present in both wheel and sdist |
| `pcae.core.intake` (generic helper, `derive_producer_provenance`) | **Yes** — `pcae/core/intake.py` present |
| `pcae.commands.intake` (`run_intake_from_files`) | **Yes** — `pcae/commands/intake.py` present |
| `pcae.commands.session` (backend-lock recognition) | **Yes** — `pcae/commands/session.py` present |
| `pcae.cli` (`pcae intake from-files` argparse wiring) | **Yes** — `pcae/cli.py` present |
| `scripts/claude_code_intake_adapter.py` | **No** — `scripts/` is outside `src/pcae`; repository-only |
| `docs/QUICKSTART_V0_3.md`, `README.md` | **No** — not packaged as package data; GitHub-hosted reference only |

No release claim in this phase's own documentation additions (§13)
depends on the repository-only adapter script being installed — the
`pcae intake from-files` CLI command it wraps is the packaged,
supportable path, and the quickstart/README updates this phase makes
lead with that command.

## 11. Local Release-Candidate Artifacts

Built with a disposable venv (`python -m pip install build`, isolated
from system Python) rather than modifying the environment:

```
$ python -m build --outdir <tmp>
Successfully built pcae_harness-0.3.0.tar.gz and pcae_harness-0.3.0-py3-none-any.whl
```

- Wheel: `pcae_harness-0.3.0-py3-none-any.whl`, 466 files, includes
  `pcae/cli.py`, `pcae/core/agent.py`, `pcae/core/intake.py`,
  `pcae/commands/intake.py`, `pcae/commands/session.py`.
- Sdist: `pcae_harness-0.3.0.tar.gz`, 472 entries, same file set under
  `src/pcae/`.
- **Version metadata is stale**: `pyproject.toml`'s `version = "0.3.0"`
  has not been bumped since the tag — both artifacts build as
  `pcae_harness-0.3.0`, indistinguishable by filename from the already-
  published v0.3.0 artifacts. This is a real, must-fix-before-publish
  item for whichever version this phase recommends (§15) — **not fixed
  in this phase** (version selection/publication is explicitly out of
  scope for 2Y; recorded as a release blocker, §16).
- Not uploaded anywhere; no tag created; no GitHub Release created.

## 12. Clean-Environment Install Smoke

Fresh venv, wheel installed via `pip install <wheel>`:

- `pcae --help` — works, full command catalogue present.
- `pcae init` in a disposable git repo — works.
- `pcae session bootstrap --agent-id claude-local` — works, lock
  acquired.
- `pcae intake from-files --task-id ... --file ... --self-reported-complete`
  — **ACCEPTED**, `execution_allowed: False`, `promotion_executed:
  False`.
- `pcae intake list` / `pcae intake show --intake-id ...` — both work,
  `producer.kind: "claude-local"`, `source: "agent_lock"` visible in the
  record.
- `pcae agent release` then `pcae session bootstrap --agent-id codex-ox`
  then `pcae intake from-files` — **ACCEPTED**, `producer.kind:
  "codex-ox"`.
- No-lock direct intake: `pcae agent release` then `pcae intake
  from-files --producer "external-tool-xyz"` — **ACCEPTED**.
- No-lock, no `--producer` — cleanly rejected, no crash.
- Separately repeated against the sdist-built install (fresh venv): CLI
  works, `pcae.core.agent.get_agent_by_id("codex-ox")` importable and
  correct.
- No external AI service invoked, no Codex CLI executed, no OpenRouter
  call made at any point — every step above is either a local governance
  operation or a local file-hash/JSON operation.

**Result: PASS**, both wheel and sdist.

## 13. Release-Critical CLI Documentation Audit

- `pcae intake from-files --help`: accurate; `--producer` help text
  states "Descriptive provenance only -- never authorization" verbatim.
- `PROJECT_STATUS.md` / 2X / 2X.1 docs: already correctly distinguish
  "supported agent/session identity" from "execution backend" — no
  overclaim found (re-confirmed, not newly discovered).
- **README.md and `docs/QUICKSTART_V0_3.md` were stale**: both only
  documented the pre-2W `scripts/claude_code_intake_adapter.py` →
  `pcae intake create` flow; neither mentioned `pcae intake from-files`
  (the packaged, generic, adapter-free path added in 2W) nor `codex-ox`
  at all. **Fixed this phase** (bounded documentation hardening,
  additive only — no existing claim removed or altered):
  - `README.md`: new "External Agent Intake (post-v0.3.0, unreleased on
    `main`)" subsection documenting `pcae intake from-files` and
    `codex-ox`, explicitly labeled as present on `main` but not yet
    shipped in a tagged release, with the same non-authority language
    used elsewhere.
  - `docs/QUICKSTART_V0_3.md`: additive note after the existing adapter-
    script walkthrough showing the direct `pcae intake from-files`
    equivalent, noting the adapter script is now a thin deprecated
    wrapper over it.
  - Neither edit touches any v0.3.0-labeled historical claim; both are
    scoped, additive, and clearly marked as post-v0.3.0/unreleased.

## 14. Current-Main Quickstart Assessment

The clean-room quickstart's *golden path* itself (adapter script →
`pcae intake create`) was left structurally intact this phase — only an
additive note was appended (§13) rather than restructuring the walkthrough
around `pcae intake from-files` as the primary flow. **Recommendation for
the next release-candidate/final-verification phase (2Z or the release
itself):** promote `pcae intake from-files` to the primary documented
path (no adapter script needed for any producer, Claude Code included),
with the adapter script demoted to a "legacy/reference" footnote, and add
`codex-ox` as an optional example bootstrap identity — not a requirement.
This is a deliberate, bounded deferral (a golden-path restructure is a
larger documentation change than "bounded hardening" should absorb
mid-phase) rather than an omission.

## 15. Versioning Decision

**Recommended: `v0.3.1` (patch).**

Rationale: every production change since `v0.3.0` is, by the phase's own
stated criteria, patch-favoring —

- `codex-ox` is additive identity registration (explicitly named as a
  patch-favoring example).
- `pcae intake from-files` consolidates and completes the *existing*
  v0.3.0 "Generic proposal intake" feature (removing its only remaining
  friction, a required adapter script) rather than introducing a new
  capability domain; the underlying contract, ECP shape, and authority
  semantics are unchanged.
- The one production bug fix this phase makes (malformed-lock crash) is
  small, backward-compatible hardening.
- No breaking change to any existing CLI surface, JSON schema, or
  authority semantic.
- No new external dependency.
- Total production diff: 6 files, +350/−107 (modest).

A minor bump would be defensible if `pcae intake from-files` were framed
as a wholly new capability domain, but it is more accurately described
as the v0.3.0 feature reaching its intended adapter-free form — the
"public feature story" is the same one `v0.3.0`'s release notes already
told, now with one fewer moving part.

## 16. Release Blocker Table

| Item | Classification |
|---|---|
| Malformed agent-lock uncaught exception | Was SHOULD-FIX-BEFORE-RELEASE — **repaired this phase** |
| Empty agent_id descriptive-quality weakness | SAFE-TO-DEFER |
| `pyproject.toml` version string still `0.3.0` | **MUST-FIX** before any publish (not fixed in this phase — version bump belongs to the publish-authorizing phase, not 2Y, since 2Y must not select/publish a version number ahead of the evidence-first sequence) |
| `tasks/DONE.md` historical sync warnings (130, pre-existing) | ACCEPTED-DEBT — repository-maintainer-only, never visible to an installed-package user, unrelated to this release line |
| 2 active task files found by `pcae doctor task-memory` this session | **Cleaned up as part of this phase's own task-lifecycle close-out** (§ Governance) — caused by an out-of-band `codex-ox` session opening this phase's task directly instead of via `task transition`; not a broader historical repair |
| Broad Fast Green host/repository-state-sensitive failures | ACCEPTED-DEBT — see §17; independently re-confirmed zero attributable regressions from this phase's own diff |
| Subprocess timing/resource-contention observation (2X.1's own finding) | ACCEPTED-DEBT — reconfirmed as an artifact of concurrent local test execution, not a repository defect |
| Package boundary | PASS — verified §10/§11 |
| Documentation truthfulness | Was SHOULD-FIX (README/quickstart staleness) — **repaired this phase**, additively |
| Installed smoke result | PASS — §12 |

**Zero remaining BLOCKING or MUST-FIX items scoped to this phase's own
production changes.** The one MUST-FIX item (stale version string) is a
publish-time action, not a code defect, and is explicitly deferred to
the recommended next phase per this phase's own no-go instruction against
selecting/publishing a version in 2Y.

## 17. Test-Baseline Rationalization / Release-Validation Matrix

| Suite | Role | Status this phase |
|---|---|---|
| `test_phase_149o_20l_7o_2y_release_hardening.py` (fresh, 9 tests) | Targeted product suite for this phase's bounded repair | 9 passed |
| 2X/2X.1/2W/2W.1/2U.2/2U.3/2U.4/review/promotion regression (439 tests) | Targeted release regression | 439 passed |
| `test_agent.py` + `test_session.py` full files | Authoritative agent/session regression | **4381 passed, 0 failed** (671.38s) |
| Broad `fast_green`-marked sweep | Inherited host/repository-state-sensitive signal, not a release gate on its own | independent clean-vs-working-tree A/B, see §Regressions Actually Run |

The broad Fast Green sweep is **not** the release regression suite —
it mixes genuine product-invariant tests with tests sensitive to local
host state, git dirtiness, and machine timing (documented across
2X/2X.1). The **authoritative release regression suite** for this
release line is: the targeted 2W/2W.1/2X/2X.1/2Y suites plus full
`test_agent.py`/`test_session.py` (the two files that own every
production surface this release line touches) — both run to completion
this phase with zero attributable failures. The broad sweep is retained
as a secondary, environment-sensitivity check via A/B diffing, not
redesigned.

### Independent Fast Green A/B (fixed `git worktree` clean baseline vs. this phase's working tree)

- Clean baseline (fixed worktree at the commit this phase started from):
  335 failed, 8692 passed, 5 skipped, 9 errors (344 total).
- This phase's working tree (one production file changed —
  `src/pcae/core/intake.py`, the bounded repair — plus new doc/test
  files): 352 failed, 8675 passed, 5 skipped, 9 errors (361 total).
- Node-ID diff: 18 new failures, 1 flipped back to passing. Of the 18
  new failures, **16 are "no `src/pcae` files dirty in working tree" /
  "touches no `src/pcae` file" guard tests belonging to unrelated
  historical phases** — they correctly and expectedly trip because this
  phase's working tree genuinely has one uncommitted `src/pcae` file at
  sweep time (resolves once committed; this is the identical, previously
  established pattern documented in 2X's own report and reconfirmed by
  2X.1). The remaining 2
  (`test_backend_cli.py::TestApplyPlanShow::test_show_after_create`,
  `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`)
  were independently re-run under reduced/isolated load:
  `test_show_after_create` passed cleanly in isolation;
  `test_audit_verify_cli` reproduces the exact same subprocess-timeout-
  under-concurrent-load mechanism independently confirmed in 2X.1
  (`pcae shell-gate audit verify` racing this same session's own
  concurrent heavy test runs) — not a 2Y-introduced regression. The one
  flipped-to-passing test
  (`test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`)
  is consistent with the same load-sensitivity, not a real behavior
  change. **Zero attributable regressions from this phase's production
  change.**

## 18. Task-Memory Warning Classification

`pcae doctor task-memory` reports two distinct issue classes:

1. **130 pre-existing "in tasks/done/ but not listed in tasks/DONE.md"
   warnings**, spanning months of prior phases (149O.1H.3 onward) —
   **HISTORICAL DEBT, repository-maintainer-only, not release-blocking**.
   These files are governance bookkeeping inside this development
   repository; no installed PCAE package or public user ever reads
   `tasks/DONE.md`.
2. **"Found 2 active task files"** — new, caused within this session by
   the `codex-ox` identity opening this phase's task via `task new`
   directly rather than `task transition --next` from the prior idle
   placeholder, leaving `tasks/active/20260824-2105-idle-...-2x-1.md`
   orphaned. **Cleaned up as part of this phase's own task-lifecycle
   close-out** (moved to `tasks/done/`) — not a broader historical
   repair, just closing out this session's own admin lapse.

## 19. Security and Authority Regression

Re-verified under the repaired code path (§9, and fresh tests in
`test_phase_149o_20l_7o_2y_release_hardening.py`): task-scope authority,
repository/base authority, promotion authority, Permission Broker,
runtime capability, and execution capability are all unaffected by this
phase's changes. The malformed-lock repair fails closed with zero
authority-field side effects (verified: no ECP/intake record is created
on rejection). `producer provenance != authenticated identity` and
`agent label != execution authority` both hold identically before and
after this phase's changes.

## 20. Article-Readiness Assessment

Article file (`/Users/atilamadai/Documents/pcae-v0.3.0-article-draft.md`)
was **not read, not modified, not published**, per instruction.

**Verdict: READY AFTER RELEASE**, with one scoping caveat for whoever
writes it: the truthful integration story after the recommended `v0.3.1`
release is "generic, adapter-free intake for any producer, with
`codex-ox` as a concrete example of a governed non-Claude identity" —
not "PCAE integrates with Claude, Codex, Codex-Ox, DeepSeek, Gemini,
Grok, and Perplexity." The latter four remain pre-v0.3.0 placeholder
registry entries (`adapter_type: undeclared`, no executable hint, no
backend-lock recognition) and must not be described as supported
integrations. The core generic-intake + codex-ox story is coherent,
packaged, tested, and truthful enough to write against once `v0.3.1`
ships.

## 21. Findings

| # | Finding | Classification |
|---|---|---|
| 1 | Complete post-v0.3 change inventory traces entirely to 2W/2W.1/2X/2X.1; no unrelated/deferred change found. | CONFIRMED |
| 2 | `pcae intake from-files` is packaged, tested, documented (after this phase), and a legitimate release capability. | CONFIRMED |
| 3 | Codex-Ox release-language boundary holds throughout current documentation. | CONFIRMED |
| 4 | Malformed-agent-lock uncaught exception was SHOULD-FIX-BEFORE-RELEASE; repaired this phase, scoped and regression-tested. | CONFIRMED, REPAIRED |
| 5 | Empty-agent_id weak-provenance behavior is SAFE-TO-DEFER; correctly cannot impersonate a registered identity. | CONFIRMED, NON-BLOCKING |
| 6 | Package boundary correctly includes every capability this release line depends on; the deprecated adapter script is correctly repository-only. | CONFIRMED |
| 7 | Local wheel and sdist build successfully; clean-environment install smoke passes end-to-end with zero external calls. | CONFIRMED |
| 8 | README.md and QUICKSTART_V0_3.md were stale relative to `main`'s actual capability set; repaired additively this phase. | CONFIRMED, REPAIRED |
| 9 | `pyproject.toml` version string is stale (`0.3.0`); this is a publish-time MUST-FIX, correctly deferred out of 2Y's scope. | CONFIRMED, DEFERRED (not blocking this phase) |
| 10 | `tasks/DONE.md` historical sync debt is repository-maintainer-only and unrelated to release quality. | CONFIRMED, ACCEPTED-DEBT |
| 11 | A session-scoped task-lifecycle irregularity (2 active task files) was cleaned up as part of this phase's own close-out. | CONFIRMED, REPAIRED |

**Zero Blocking findings against this phase's own scope.**

## Regressions Actually Run — Summary

- `tests/test_phase_149o_20l_7o_2y_release_hardening.py` (fresh, this
  phase): 9 passed.
- Targeted release regression (2X/2X.1/2W/2W.1/2U.2/2U.3/2U.4/review/
  promotion): 439 passed.
- `tests/test_agent.py` + `tests/test_session.py` (full files, `-n
  auto`): 4381 passed, 0 failed.
- Independent Fast Green A/B (fixed worktree clean baseline vs. working
  tree): 335F/8692P/9E clean vs. 352F/8675P/9E dirty — 18 new failures,
  16 attributable to unrelated historical dirty-`src/pcae`-tree guard
  tests (resolves on commit), 2 independently confirmed as
  concurrent-load subprocess-timeout artifacts, 1 flip consistent with
  the same load sensitivity. Zero attributable regressions.
- **4829 tests run and passing this phase** (9 + 439 + 4381), plus the
  Fast Green A/B as a secondary environment-sensitivity check.

## 22. Runtime Confirmation

`pcae runtime inspect`: `execution_capability: unavailable`,
`non_executing_posture: true`, `broker_implementation_status:
execution_unavailable` — unchanged before and after this phase.

## 23. v0.3.0 / Article / Publication Confirmation

- v0.3.0 tag, GitHub Release, published wheel/sdist, and historical
  release-notes claims: **untouched**.
- Article: **not read, not modified, not published.**
- No Git tag created, no GitHub Release created, no upload to PyPI or
  any other index, at any point this phase.

## 24. Next Phase

If this phase is accepted with zero unresolved blocking findings:

**149O.20L.7O.2Z — Post-v0.3.1 Release Candidate Final Verification**

Should verify (not redesign): the frozen release scope from this phase,
the version bump to `0.3.1` in `pyproject.toml`, packaged artifacts
rebuilt against that version, checksums, a repeated clean install across
wheel and sdist, the supported workflows this phase smoke-tested,
documentation truth (including promoting `pcae intake from-files` to the
quickstart's primary golden path per §14's deferred recommendation), the
regression baseline established here, stable-tag isolation, release
notes, and the publication checklist. Must not publish automatically.
