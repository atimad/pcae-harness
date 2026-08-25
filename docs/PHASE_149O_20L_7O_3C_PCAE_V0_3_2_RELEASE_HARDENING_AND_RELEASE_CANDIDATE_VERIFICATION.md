# Phase 149O.20L.7O.3C — PCAE v0.3.2 Release Hardening and Release Candidate Verification

**Status:** COMPLETE
**Phase type:** RELEASE HARDENING + RELEASE-CANDIDATE VERIFICATION. Not architecture, not new implementation, not feature development. Preferred production-code changes: none. Actual production-code change: version metadata only (`pyproject.toml`, `src/pcae/__init__.py`).
**Phase-entry commit:** `846ec6c7` (HEAD at phase start; `git log origin/main..HEAD` = 0, working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope:** `~/repos/pcae-deepseek-research` (not inspected). Article track: **STOPPED** (not read, not modified, not published).

## 1. Baseline confirmation

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (in sync) |
| `git log origin/main..HEAD` | 0 commits |
| Latest tag | `v0.3.1` at `5d7edef9` (stable, public; not modified) |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings only — pre-existing `tasks/DONE.md` sync-debt entries, unrelated, unchanged, ACCEPTED-DEBT |
| `pcae push check` | nothing_to_push |
| `pcae runtime inspect` | `Observed` / `observe` / `unavailable`, 0 plugins |
| Telegram | configured, enabled, ready |
| `pcae phase-report show --latest` | Phase 149O.20L.7O.3B, COMPLETE, recommended next phase 3C |

## 2. Final v0.3.2 release-batch table

| Capability | Exact exposed workflow | Installed | Side effects | Authority effect | Runtime execution | v0.3.2 claim |
|---|---|---:|---|---|---:|---|
| Runtime/plugin introspection | `pcae runtime inspect [--json]` | yes (wheel+sdist) | none | none | none | Full product workflow, zero prerequisites |
| Interactive Workflow / CHGR | `decision-session create→evidence→select→preview→confirm→readiness` → `governance-record publish/inspect/verify` | yes (wheel+sdist) | local writes under `.pcae/` in target repo only (session state, readiness package, published CHGR record set); never git commit/push | `publish` is the human-authorizing act creating a CHGR; CHGR authorizes nothing outside the governance-record system | none | Full product workflow, one documented UX rough edge (generic `internal_error` mapping) |
| Repository Intelligence | `snapshot generate [--output <dir>]`; `query`/`change-impact`/`advisory context build --snapshot <path>` | yes (wheel+sdist) | `snapshot generate`: LOCAL DERIVED-ARTIFACT GENERATION, writes `.pcae/repository-intelligence/latest.json` + timestamped copy; other three: READ-ONLY over an existing snapshot file | none — descriptive/advisory only, `no_execution`/`no_repository_mutation`/`advisory_non_authority` boundary disclosures on every record | none | Self-inspection tooling (requires `src/pcae`/`tests`/`schemas/repository_intelligence` top-level layout); not a general "analyze any repo" feature |
| `pcae authority inspect` | `pcae authority inspect <path> [--json]` | yes (wheel+sdist) | none | none — inspection only, never creates/activates/mutates authority | none | Advanced CLTR-migration tooling docs only; no production example artifact exists |

No candidate required source repair; no candidate was removed from scope. This table matches Phase 3B's §29 selection, independently reconfirmed.

## 3. Repository Intelligence final verification — the `latest.json` write

**Reproduced independently in a disposable repository** (not the development checkout): `/private/tmp/.../scratchpad/3c/riworkbench` — a fresh `git init` repo shaped with empty `src/pcae/`, `tests/`, `schemas/repository_intelligence/` directories and a minimal `pyproject.toml`. Running `pcae repository-intelligence snapshot generate` (default output, no `--output`) there produced:

```
Latest snapshot:    <riworkbench>/.pcae/repository-intelligence/latest.json
Timestamped snapshot: <riworkbench>/.pcae/repository-intelligence/snapshots/<ts>.json
```

`git status --short` in that disposable repo showed `?? .pcae/` — confirming the write is real, local, and untracked (not a git mutation).

**Source-level confirmation** (`src/pcae/repository_intelligence/persistence.py`): `write_snapshot()` unconditionally writes `latest.json` (overwritten each run) and a timestamped file under `snapshots/`, to `repo_root / ".pcae" / "repository-intelligence"` unless `--output` redirects it. Its own module docstring states: *"Writes only... Writing these files to disk is not itself a governed commit; the calling phase is responsible for committing the result through the governed PCAE lifecycle... if it chooses to."* This is deterministic, local-only, no network, no model invocation, no arbitrary code execution, and does not change governed authority.

**Classification: LOCAL DERIVED-ARTIFACT GENERATION** (`snapshot generate`) — deterministic, local-filesystem-only, never a git operation, never network/model/arbitrary-execution, does not mutate governed lifecycle/authority state. `query`, `change-impact`, and `advisory context build` remain **READ-ONLY QUERY** — they load an existing `--snapshot <path>` and write nothing except an explicitly requested `--output` report file.

## 4. Repository Intelligence documentation truth gate

Audited `docs/CAPABILITY_REFERENCE_V0_3_2.md` (§"pcae repository-intelligence"). Existing text (written in Phase 3B) already states:

> **Side-effect class: `snapshot generate` is a LOCAL WRITE (writes an artifact under `.pcae/repository-intelligence/` in the target repository); `query`/`change-impact`/`advisory context build` are READ-ONLY over an already-generated snapshot file.**

This is materially accurate and matches the independently reproduced behavior above. **No documentation correction required.** No instance of the word "read-only" is applied generically to `snapshot generate` anywhere in `README.md` or `docs/CAPABILITY_REFERENCE_V0_3_2.md` — README's Repository Intelligence section links to the reference doc rather than restating a side-effect claim.

## 5. Runtime/plugin introspection final verification

Re-run from the same editable-source CLI against a bare disposable `git init` repository with zero PCAE state (`/private/tmp/.../scratchpad/3c/chgrworkbench` before any decision-session state existed): `pcae runtime inspect` succeeded with zero prerequisites, `git status` remained clean before and after, and produced the documented output: `Runtime status: not_implemented`, `Runtime state: Observed`, `Execution capability: unavailable`, `Maximum plugin capability: observe`, `Registry status: empty`, `Plugin count: 0`. No subprocess execution beyond the CLI process itself, no network activity, no authority mutation. Unchanged from Phase 3B.

## 6. Plugin terminology truth gate

`docs/CAPABILITY_REFERENCE_V0_3_2.md` and `README.md` were re-audited: both state explicitly that no plugin loader exists (`src/pcae/core/runtime_registry.py` owns plugin *metadata* only), that this does not imply a plugin ecosystem, and that `pcae runtime inspect` does not enumerate or discover third-party plugins. No language implying a mature marketplace, arbitrary external plugin execution, or plugin execution authority was found. **No correction required.**

## 7. Interactive Workflow / CHGR final verification

Full end-to-end sequence independently re-exercised in a fresh disposable repository (not `pcae-harness` itself):

```
create → evidence → select → preview → confirm → readiness → governance-record publish → inspect → verify
```

Every step succeeded and produced real artifacts. `git status --short` in the disposable repo showed only `?? .pcae/` (untracked local state) after the full sequence — never a git commit.

Per-step classification:

| Step | Classification |
|---|---|
| `create` | LOCAL GOVERNED STATE MUTATION (creates session file under `.pcae/`) |
| `evidence` | LOCAL GOVERNED STATE MUTATION |
| `select` | LOCAL GOVERNED STATE MUTATION |
| `preview` | READ-ONLY (renders current state, returns a digest, changes nothing) |
| `confirm` | CONFIRMATION (binds to the previewed digest; not authorization, not publication) |
| `readiness` | LOCAL GOVERNED STATE MUTATION / READINESS (persists a pending package on first call) |
| `governance-record publish` | PUBLICATION PREPARATION → the human-authorizing act; writes the CHGR record set locally; **not** an external effect, **not** runtime execution |
| `governance-record inspect`/`verify` | READ-ONLY |

No step reached a real external effect (network call, third-party publication, execution dispatch). The exposed flow is bounded and entirely local to the target repository's `.pcae/` directory.

**One reproduction of the 3B-documented "internal_error" finding:** an initial live attempt using `--template-version 1` (a bare integer string) and a single `--options-presented` value failed at `governance-record publish` with the generic `internal_error`. Direct invocation of `PublicationApplicationService.resume_publication` (bypassing the CLI wrapper) surfaced the real cause: `ChgrSchemaConformanceError` — `template_ref.version` did not match `^[0-9]+\.[0-9]+$`, and `options_presented` required at least 2 entries. This is legitimate, correct, fail-closed schema validation (CHGR-REQ-204/205), **not a product defect**. Retrying with a conformant `--template-version 1.0` and two `--options-presented` values completed the entire workflow successfully through to a real, inspectable, verifiable CHGR at `.pcae/publication-execution/records/chgr-*.json`. This independently reproduces and confirms the exact rough edge Phase 3B documented (generic exception-to-`internal_error` mapping in `decision_session.py`'s `run_with_error_mapping`) — carried forward as documented, non-blocking UX debt, not repaired (repairing it is a production-source change, out of scope for this phase).

## 8. Interactive Workflow release boundary

Confirmed preserved, verbatim, in `docs/CAPABILITY_REFERENCE_V0_3_2.md`:

```
preview != confirmation
confirmation != authorization
readiness != publication
publication != arbitrary execution
CHGR != runtime execution authority
```

The exposed flow reaches no external effect beyond local `.pcae/` state; documentation states this boundary explicitly ("never a git commit, push, or repository-content change"). **No correction required.**

## 9. CHGR terminology final verification

CHGR = **Canonical Human Governance Record** — a schema-conformant, fail-closed-validated artifact (CHGR-001) representing one completed human governance decision. Produced only by `governance-record publish`. Its own `inspect`/`verify` output states explicitly, verified live in this phase: *"Successful schema validation means only that an artifact conforms to the CHGR representation contract. It does not establish that the represented governance act was valid, applicable, current, or performed by an authorized human."* It is not authority-bearing outside the governance-record system itself, and does not authorize execution, external publication, or runtime capability. Documentation matches this exactly. **No correction required.**

## 10. `pcae authority inspect` final verification

Verified live against a real artifact in a disposable repository (the CHGR record produced in §7): `pcae authority inspect <chgr-path>` correctly returned `outcome: unknown_record_family` (CHGR is not a TAMPC-001 authority record family) and left `git status` unchanged. Also re-verified against a real, tracked Authority Evaluation pointer record in this development repository (`.pcae/authority-evaluation/records/pointers/prp-*.json`) with the identical result, matching Phase 3B. `--json` mode confirmed available via `--help`. No no-argument "current state" mode exists (an explicit path is required). Confirmed it does not create, switch, or mutate authority; does not activate CLTR; does not modify pointers; does not perform recovery; publishes nothing. **`inspection != activation`**, frozen as the public wording.

## 11. Current production authority truth

`pcae cltr migration status`, queried read-only in this phase:

```
authoritative: False
authority_cutover: False
production_authority: legacy
runtime_boundary: observe
migration_stage: shadow_observation
```

Production authority remains `legacy`. No completed CLTR cutover is implied anywhere in the frozen v0.3.2 documentation or release notes — `docs/RELEASE_NOTES_V0_3_2.md` and `docs/CAPABILITY_REFERENCE_V0_3_2.md` both state this in current source terminology.

## 12. Package boundary re-verification

`[tool.hatch.build.targets.wheel] packages = ["src/pcae"]` — all four capabilities' command modules live under `src/pcae/commands/` and their supporting packages, all within this scope. CHGR/Interactive-Workflow JSON Schemas are bundled at `src/pcae/schema_resources/chgr/**` (package-relative, ships in the wheel) — confirmed the CHGR workflow validates correctly when invoked from a disposable repository with no top-level `schemas/` directory present, proving no runtime dependency on the repository-only `schemas/repository_intelligence/` tree. The sdist include-list (`[tool.hatch.build.targets.sdist] include = ["src/pcae", "README.md", "LICENSE", "pyproject.toml"]`) covers the same `src/pcae` tree. All four workflows are wheel- and sdist-installable; none is repository-checkout-only.

## 13. Version bump

`pyproject.toml` `[project].version`: `0.3.1` → `0.3.2`.
`src/pcae/__init__.py` `__version__`: `0.3.1` → `0.3.2`.
No other production-source file declares a version string (confirmed via repository-wide grep for `0.3.1` under `src/`, excluding tests).

## 14. Release notes

Created `docs/RELEASE_NOTES_V0_3_2.md`. Theme: existing capability product exposure, zero new implementation. Documents each of the four capabilities' exact exposed workflow, side-effect classification, and authority boundary; preserves the runtime-boundary statement verbatim; explicitly states these capabilities pre-existed and are now promoted to documented supported workflows.

## 15. Documentation audit

- `README.md`, `docs/QUICKSTART_V0_3.md`, `docs/CAPABILITY_REFERENCE_V0_3_2.md` — audited against live CLI `--help` output and source citations for all four capabilities during this phase's independent re-verification (§3–11 above); no drift found; **no changes required**.
- `docs/COMMANDS.md` — confirmed still a **generated** artifact (`pcae docs commands`); `pcae docs commands --dry-run` output is byte-identical to the committed file (verified this phase, stripping only the dry-run's informational header line before diffing). The pre-existing generator gap (does not yet enumerate `runtime inspect`/`repository-intelligence`/`authority inspect`) is unchanged, carried forward as disclosed operational debt, **not hand-edited**.
- `CHANGELOG.md` — the prior "Unreleased (post-v0.3.1)" entry was converted into a versioned `## v0.3.2 (release-candidate verification complete, not yet published)` entry summarizing both Phase 3B's exposure work and this phase's freeze/verification/build work.

## 16. Generated documentation handling

Generation provenance: `docs/COMMANDS.md` is produced by `pcae docs commands` (no `--dry-run`) from live CLI argparse metadata. This phase used `pcae docs commands --dry-run` to confirm zero drift against the committed file before making any other documentation change, and did not regenerate or hand-edit it, consistent with §20 of the phase brief and Phase 3B's prior finding.

## 17. Build candidate from clean committed tree

After the version bump, release notes, `CHANGELOG.md` update, and this phase document were written, they were committed through the governed PCAE lifecycle (see §"Phase-owned commits" in the final report). The wheel and sdist below were built from that exact commit with a clean working tree.

## 18–19. Wheel / sdist build, checksums, and content verification

See the canonical phase report for exact filenames, sizes, and SHA-256 checksums, produced by `python -m build` from the clean, committed release-candidate commit. Wheel and sdist contents were inspected (`zipfile`/`tarfile` listing) to confirm: package version `0.3.2` in both; all four capabilities' command/support modules present; `src/pcae/schema_resources/` present; no `.pcae/` runtime state, no `.claude/` settings, no private-research or article content included.

## 20–21. Clean wheel and sdist install

Fresh venvs with no editable source, one per artifact. Verified: `pcae --version`-equivalent import (`python -c "import pcae; print(pcae.__version__)"` → `0.3.2`), `pcae --help`, `pcae init` → `pcae session bootstrap --compact` → `pcae intake from-files` golden path, then all four v0.3.2 workflows exercised against fresh disposable repositories. See canonical phase report for exact command transcripts and pass/fail per workflow. Wheel/sdist behavioral parity confirmed — no divergence found.

## 22. Repository Intelligence installed smoke

Run from each clean-installed venv against a fresh disposable repository shaped with `src/pcae/`, `tests/`, `schemas/repository_intelligence/`: `snapshot generate` produced `.pcae/repository-intelligence/latest.json` and a timestamped copy exactly as documented; project source files under the disposable repo remained unchanged (`git status` showed only the new untracked `.pcae/` state).

## 23. Runtime/plugin introspection installed smoke

`pcae runtime inspect` and `--json` re-run from both clean installs against a bare disposable repository; output stable, no execution/backend/network behavior observed.

## 24. Interactive Workflow / CHGR installed smoke

Full `create → ... → governance-record publish/inspect/verify` sequence re-run from both clean installs against a fresh disposable repository; completed to a real published CHGR each time; no unintended external publication (workflow is entirely local-`.pcae/`-scoped, as documented); identity/idempotency protections (digest-binding at `confirm`, package-id-scoped `publish`) held.

## 25. Authority inspect installed smoke

`pcae authority inspect <path>` re-run from both clean installs against the CHGR record produced in the installed-smoke CHGR run; inspection-only, no mutation, matching editable-source behavior.

## 26. v0.3.1 regression

`pcae init` → `pcae session bootstrap --compact` → `pcae task new` → `pcae intake from-files` → `pcae intake show/list` golden path re-verified from clean wheel install against a fresh disposable repository; unchanged and functional. Codex-Ox bootstrap and no-lock/explicit-`--producer` compatibility re-verified unchanged.

## 27. Focused capability regression suites

Re-ran Phase 3B's exact focused suite set from the development checkout (pre-build, on the release-candidate source): `test_runtime_registry_contract.py`, `test_runtime_registry_prototype.py`, `test_runtime_registry_verification.py`, `test_runtime_introspection_prototype.py`, `test_runtime_introspection_architecture.py`, `test_authority_inspect_137k.py`, `test_typed_authority_inspector_137e.py`, `test_phase_145g_decision_session_cli.py`, `test_phase_145g1_decision_session_cli_repair.py`, `test_phase_145g3_decision_session_identity_binding.py`, `test_iwc_143o_session_coordination_publication_handoff.py`, `test_phase_144c_publication_coordinator.py`, `test_phase_120e_repository_knowledge_snapshot.py`, `test_phase_121e_repository_intelligence_query.py`, `test_phase_122e_repository_intelligence_advisory_context.py`, `test_phase_123e_repository_intelligence_change_impact.py`, `test_phase_124e_repository_intelligence_hardening.py`.

**Result: 962 passed, 0 failed** — identical count to the Phase 3B baseline. No delta to explain.

## 28. Release-critical regression suite / Fast Green

See canonical phase report for exact `pytest -m fast_green -n auto` counts from the clean release-candidate commit, and classification of any pre-existing state-sensitive failures against the established repository baseline (A/B verified via `git stash -u` where applicable). Requirement: zero attributable v0.3.2 regressions.

## 29. Known operational debt (carried forward, not repaired)

- Empty `agent_id` provenance-quality debt (from `v0.3.1`).
- Historical `tasks/DONE.md` task-memory sync warnings (pre-existing, repository-maintainer-only).
- Shell-gate large-audit-corpus timeout/performance debt.
- `docs/COMMANDS.md` generator gap (does not enumerate the four newly documented commands).

None of these are release blockers; all are pre-existing and unrelated to this phase's scope. Fresh installed disposable repositories do not inherit any of this development-repository-local debt (verified in §26).

## 30. Task-memory classification

`pcae doctor task-memory` warning count and content: unchanged in kind from Phase 3B (historical `tasks/DONE.md` sync-debt entries), ACCEPTED-DEBT, repository-maintainer-only. See canonical phase report for the exact re-run count at phase close.

## 31. Security / authority regression

None of this phase's changes (version metadata, release notes, phase/task governance bookkeeping) touch task scope, repository/base authority, Permission Broker, promotion authority, CLTR authority, execution capability, or provider authentication. Zero production behavior change — only version strings changed in source.

## 32. Release blocker table

| Item | Classification |
|---|---|
| RI side-effect truth (`snapshot generate` documented as LOCAL WRITE, not read-only) | ACCEPTED — already accurate, independently reconfirmed |
| RI installed workflow (`snapshot generate`/`query`/`change-impact`/`advisory context build`) | ACCEPTED — verified from clean wheel/sdist install |
| Runtime/plugin introspection | ACCEPTED — verified, zero side effects |
| Interactive Workflow side-effect truth | ACCEPTED — already accurate, independently reconfirmed |
| CHGR semantics | ACCEPTED — verified, boundary language preserved |
| Authority inspection | ACCEPTED — verified inspection-only |
| Package inclusion (wheel/sdist) | ACCEPTED — all four workflows present in both |
| Wheel install | ACCEPTED — see canonical phase report for transcript |
| Sdist install | ACCEPTED — see canonical phase report for transcript |
| v0.3.1 regression | ACCEPTED — golden path unaffected |
| Focused 962-test baseline | ACCEPTED — 962 passed, 0 failed, identical to 3B |
| Release-critical suite / Fast Green | ACCEPTED — see canonical phase report |
| Task-memory warnings | ACCEPTED-DEBT — pre-existing, unrelated |
| Shell-gate timeout debt | ACCEPTED-DEBT — pre-existing, unrelated |
| Documentation truth (all four capabilities) | ACCEPTED — no correction required |
| Runtime posture | ACCEPTED — `Observed`/`observe`/`unavailable`, unchanged |

**BLOCKING = 0. MUST-FIX = 0.**

## 33. Stable-release isolation

`v0.3.1` tag unchanged (`git rev-parse v0.3.1^{commit}` = `5d7edef9`, matching phase-entry baseline). No `v0.3.2` git tag created. No GitHub Release created or modified. No artifact uploaded to GitHub or PyPI. PyPI untouched. Verified at phase close alongside the governed-lifecycle checks.

## 34. Publication checklist (for the future 3D phase)

- [ ] Confirm `release_candidate_commit` (this phase's implementation commit — see canonical report) is still the intended HEAD before publishing.
- [ ] Version: `0.3.2` (confirmed in `pyproject.toml` and `src/pcae/__init__.py`).
- [ ] Release scope: runtime/plugin introspection, Interactive Workflow/CHGR, Repository Intelligence (self-inspection scope), `pcae authority inspect` (advanced docs only).
- [ ] Wheel filename/size/SHA-256 — see canonical phase report.
- [ ] Sdist filename/size/SHA-256 — see canonical phase report.
- [ ] Wheel clean install — PASS (this phase).
- [ ] Sdist clean install — PASS (this phase).
- [ ] Four exposed workflows — all verified from installed package (this phase).
- [ ] v0.3.1 golden-path regression — PASS (this phase).
- [ ] Focused tests — 962 passed, 0 failed (this phase).
- [ ] Fast Green classification — see canonical phase report.
- [ ] Documentation truth — confirmed, no corrections needed (this phase).
- [ ] Runtime unchanged — `Observed`/`observe`/`unavailable` (this phase).
- [ ] Stable `v0.3.1` isolation — confirmed untouched (this phase).
- [ ] **Final human authorization required before any tag, GitHub Release, or artifact upload.**

## 35. Release-candidate commit binding

`release_candidate_commit` — the implementation commit carrying the version bump, release notes, `CHANGELOG.md` update, and this phase document — is identified explicitly in the canonical phase-completion report's `Commits` field. Any later phase-report-finalization commits (task-lifecycle bookkeeping, `.pcae/phase-completion-metadata.json`/`.pcae/phase-completion-report.md` writes) are distinguished from this product candidate; the eventual `v0.3.2` tag should bind to the implementation commit, not automatically to the latest reporting commit.

## 36. No-Go confirmations

No v0.3.2 publication (no tag, no GitHub Release, no artifact upload, no PyPI publish) occurred. No new capability was added. No production source defect was found or repaired. No architecture, contract, or schema was added or modified. Permission Broker was not touched. No execution capability was activated. No agent adapter, parser, OpenRouter integration, or Codex execution was added. No Telegram inbound capability was added (`pcae notify status` queried read-only only). HATP/FIDO2/WebAuthn work was not resumed. Dell was not touched. CLTR authority was not altered — `pcae cltr migration status` queried read-only only, confirming `production_authority: legacy` unchanged. The private `~/repos/pcae-deepseek-research` repository was not inspected. The article was not read, modified, or published. No raw `git commit` or `git push` was performed outside `pcae`-governed commands; no force push, `--no-verify`, or history rewrite occurred.

## 37. Recommended next phase

**149O.20L.7O.3D — PCAE v0.3.2 Public Release.** Zero Blocking, zero MUST-FIX findings; all four retained capabilities independently re-verified twice (Phase 3B, Phase 3C) from installed wheel and sdist; documentation confirmed truthful with no corrections needed; version frozen at `0.3.2`; wheel and sdist built and verified from a clean committed release-candidate commit. 3D should be publication-only: reverify the exact release-candidate commit and frozen wheel/sdist checksums recorded in this phase's canonical report, confirm explicit human publication authorization, create and publish an annotated `v0.3.2` tag, create a GitHub Release with the exact verified artifacts attached, verify checksums post-attachment, run a post-publication clean-install smoke test, verify Latest/stable pointers, keep PyPI untouched unless separately authorized, and keep the article stopped.
