# Phase 149O.20L.7O.3B — Selected Existing Capability Verification and Product Exposure

**Status:** COMPLETE
**Phase type:** INDEPENDENT PRODUCT-SURFACE VERIFICATION + DOCUMENTATION EXPOSURE. Zero production source, CLI, contract, schema, or packaging-configuration file was modified.
**Phase-entry commit:** `01d7dfe9` (HEAD at phase start; `git log origin/main..HEAD` = 0, working tree clean).
**Repository:** `~/repos/pcae-harness`. **Out of scope:** `~/repos/pcae-deepseek-research` (not inspected). Article track: **STOPPED** (not read, not modified).

## 1. Baseline confirmation

| Check | Result |
|---|---|
| `git status --short` | clean |
| `git status --branch --short` | `## main...origin/main` (in sync) |
| `git log origin/main..HEAD` | 0 commits |
| Latest tag | `v0.3.1` (stable, public; not modified) |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings only — pre-existing `tasks/DONE.md` sync-debt entries, unrelated, unchanged |
| `pcae push check` | nothing_to_push |
| `pcae runtime inspect` | `Observed` / `observe` / `unavailable`, 0 plugins |
| Telegram | configured, enabled, ready |
| `pcae phase-report show --latest` | Phase 149O.20L.7O.3A, COMPLETE, recommended next phase 3B |

## 2. Methodology

Re-read the full 3A audit document. Built a current wheel and sdist from `HEAD` (no version change; both build as `0.3.1`, matching `pyproject.toml`). Installed each into a disposable venv. Exercised every selected capability from these clean installs against disposable git repositories created outside `pcae-harness`, using only legitimate supported PCAE commands to produce any prerequisite state. Ran existing focused test suites. Wrote documentation only after verification.

## 3. Package build and clean-install verification

- `python -m build` from clean `HEAD` produced `pcae_harness-0.3.1-py3-none-any.whl` and `pcae_harness-0.3.1.tar.gz` with no errors.
- Both installed cleanly into separate disposable venvs (`wheel-venv`, `sdist-venv`); `pcae --help` and per-capability `--help` output confirmed identical CLI registration in both.
- No upload, no tag, no GitHub Release, no PyPI action.

## 4–6. Repository Intelligence — independent verification

**3A claim:** B-rated (release-ready) for RKS/Query/Advisory-Context/Change-Impact; INTEGRATE NOW.

**Independent re-verification finding (differs from 3A's framing):** `snapshot generate` requires the working tree to contain `src/pcae/`, `tests/`, and `schemas/repository_intelligence/` at its top level — hardcoded in `src/pcae/repository_intelligence/snapshot_builder.py` (`list_top_level_entries(repo_root, "src/pcae")`; fixed tuple `(("tests", "test"), ("schemas/repository_intelligence", "schema"))`). No `--repo-root` option exists. Verified live from the wheel install:
- Against a disposable `git init` repository (no PCAE-shaped layout): `snapshot generate` fails closed with `Error: No architectural entities could be observed at the expected top-level locations (src/pcae, tests, schemas/repository_intelligence); refusing to produce a non-conformant snapshot with an empty required architectural_entities array.`
- Against a real `pcae-harness` checkout (using `--output` redirected to a scratch directory to avoid mutating the dev repo's tracked `.pcae/repository-intelligence/latest.json`): succeeds, produces a real snapshot (20 entities, 2 subsystems, 5 claims, 27 sources, 4 unknowns).
- `query --snapshot <path> --entity <id> --json` against the generated snapshot returned a real, fully attributed JSON record with explicit `verification_state`, `limitations`, and `boundary_disclosures` (`no_execution: true`, `no_repository_mutation: true`, `advisory_non_authority: true`). Read-only confirmed.
- `change-impact` and `advisory context build` both require `--snapshot <path>` and are pure reads over an existing snapshot file — no writes.

**Correction from a first testing mistake:** an initial attempt at `pcae repository-intelligence snapshot generate` with default output (no `--output`) was run against the `pcae-harness` dev repo itself and wrote to the tracked `.pcae/repository-intelligence/latest.json`, mutating dev-repo state. This was caught immediately (`git status` showed the modification) and reverted with `git checkout -- .pcae/repository-intelligence/latest.json`; the untracked timestamped snapshot file was deleted. All subsequent verification used `--output <scratch-dir>` to avoid any further dev-repo mutation. §33's "no dev-repo mutation" rule is otherwise satisfied throughout the phase.

**Classification: CONFIRMED AS ADVANCED READ-ONLY WORKFLOW — self-inspection only, not a general product feature.** This is not "prototype/incomplete" — it is real, deterministic, fully tested, and safe — but it is dependent on a specific checkout layout (`§`-criteria "dependent on development checkout state"), meaning it can never coherently be marketed as "inspect your own repository" to an ordinary end user installing PCAE into an arbitrary project. It is documented (`docs/CAPABILITY_REFERENCE_V0_3_2.md`) as PCAE self-inspection tooling, primarily useful to PCAE contributors — not placed in the README as a general-audience feature pitch, and not phrased as "inspect your repository" anywhere. This differs from 3A's "INTEGRATE NOW" / user-value-5 framing, which assumed general applicability that was not independently checked against source in 3A and does not hold.

**Authority boundary (§6):** confirmed descriptive/derivative only; `no_execution`, `no_repository_mutation`, `advisory_non_authority` boundary disclosures are present on every record; does not replace Decision Evaluation, Permission Broker, task scope, or lifecycle authority.

## 7–9. Runtime/plugin introspection — independent verification

**3A claim:** F (contract/metadata-only, but complete and honestly self-scoped); EXPOSE/PACKAGE NOW.

**Independently confirmed, unchanged from 3A:** `pcae runtime inspect` (from the wheel install, run against a bare disposable `git init` repository with zero PCAE state) succeeded with zero prerequisites and produced the documented output: `Runtime status: not_implemented`, `Runtime state: Observed`, `Execution capability: unavailable`, `Maximum plugin capability: observe`, `Registry status: empty`, `Plugin count: 0`. `git status` in the target repository remained clean before and after — no side effects. `--json` mode also verified. Sdist install produced byte-identical CLI registration.

`pcae runtime snapshot --preview` (a distinct command from `inspect`, both under the `runtime` noun) was also exercised: against the same bare disposable repository it correctly reported `Snapshot readiness: not ready` (this command previews *governance-runtime* portability state — active task, agent lock, session continuity — and requires the target repository to already carry PCAE governance state; it is unrelated to plugin introspection and is not conflated with it in documentation).

**Plugin terminology (§9):** confirmed no plugin loader exists (`src/pcae/core/runtime_registry.py` owns plugin metadata only). Documentation states this explicitly — `pcae runtime inspect` reports introspection/registered-capability state, not a general third-party plugin ecosystem.

**Classification: CONFIRMED AND EXPOSED as a full PRODUCT WORKFLOW.** Zero prerequisites, zero side effects, works in any repository, wheel- and sdist-verified.

## 10–13. Interactive Workflow / CHGR — independent verification

**3A claim:** A (released), discoverability caveat only.

Full end-to-end workflow independently exercised from the wheel install, against a fresh disposable `git init` repository:

```
create → evidence → select → preview → confirm → readiness → governance-record publish → governance-record inspect/verify
```

Every step succeeded and produced real, schema-conformant artifacts (`session_state` transitions: `Created` → `EvidenceReady` → `DecisionSelected` → `Confirmed`; readiness produced a `pending` package; `governance-record publish` produced a real CHGR record set on disk at `.pcae/publication-execution/records/chgr-*.json`, `chgrprov-*.json`, `chgrconf-*.json`, `chgrintg-*.json`; `inspect`/`verify` against the published CHGR both returned `representation-only, non-authoritative` results with all structural checks passing).

**Authority model (§11), confirmed distinct at every step:**
- `preview` renders exact content and a binding digest; changes nothing.
- `confirm` requires echoing the exact `preview_digest` back — the binding mechanism. Confirmation ≠ authorization; confirmation ≠ publication.
- `readiness` constructs/persists a pending package on first call against a `Confirmed` session (a write). Readiness ≠ publication.
- `governance-record publish` is the human-authorizing act that actually creates the CHGR. Publication ≠ execution — the resulting CHGR authorizes nothing outside the governance-record system itself.

**One real finding during verification, resolved as test-input error, not a product defect:** an initial `governance-record publish` attempt failed with a generic `error_type: internal_error`. Reproducing the failure directly against the internal `PublicationApplicationService.resume_publication` (bypassing the CLI's error-mapping wrapper) surfaced the real exception: `ChgrSchemaConformanceError: ... 'manual:v1' does not match '^[a-z][a-z0-9_-]{2,63}$'` — the `--template-ref` value used in the first test attempt (`"manual:v1"`, containing a colon) violated CHGR's closed identifier pattern. This is correct, working, fail-closed schema validation (CHGR-REQ-204/205), not a defect. Retrying with a conformant `template-ref` (`"manual-review"`) completed the entire workflow successfully. **Genuine, minor, non-blocking UX finding recorded (not repaired, per §34 no-source-repair rule):** `decision_session.py`'s shared `run_with_error_mapping` wrapper maps every non-`ApplicationServiceError`/`ValueError` exception — including this legitimate, specific `ChgrSchemaConformanceError` — to the same generic `internal_error` message, rather than a more specific `invalid_request`-shaped error. This does not block exposing the workflow (it completes correctly with conformant input) but is documented as a known rough edge in `docs/CAPABILITY_REFERENCE_V0_3_2.md` with the exact identifier pattern required.

**CHGR terminology (§13):** Canonical Human Governance Record — a schema-conformant, fail-closed-validated artifact representing one completed human governance decision. Its own output states explicitly that successful validation "does not establish that the represented governance act was valid, applicable, current, or performed by an authorized human." Documented accurately — CHGR alone does not establish execution, external publication success, permission, or runtime capability.

**Classification (§12): EXPOSE COMPLETE SUPPORTED WORKFLOW.** The full production path (already independently verified end-to-end, packaged, wheel- and sdist-confirmed) is suitable for users, with the field-format caveat documented.

## 14–16. `pcae authority inspect` — independent verification

**3A claim:** C (standalone inspector CLI, undocumented, thin test coverage); EXPOSE/PACKAGE NOW (bundle-in, low-medium value).

Confirmed: `pcae authority inspect <path> [--json]` requires an explicit artifact path (no no-argument "current state" mode). Source: `src/pcae/commands/authority_inspect.py` → `pcae.cltr.authority_inspection.inspect_artifact_at_path` (TAMPC-001 v1.0). Verified live, read-only, against a real file already tracked in this repository (`.pcae/authority-evaluation/records/pointers/prp-*.json`, an Authority Evaluation pointer record — a different record family): correctly returned `outcome: unknown_record_family` and left `git status` unchanged. No malformed/unavailable-file behavior was separately exercised beyond this (the unknown-family path already exercises the fail-closed behavior).

**New finding beyond 3A's framing:** `grep -rl '"record_type"' .pcae/` followed by inspecting each match's `record_type` value shows the only record families present anywhere in this repository's tracked `.pcae/` state are `governance_record_integrity`, `governance_record_provenance`, `human_confirmation_evidence`, and `human_governance_record` (CHGR-family) — none of the CLTR authority-cutover families (`authority_epoch`, `cutover_request`, `certification`) this command supports exist anywhere in production data, consistent with `pcae cltr migration status` reporting `production_authority: "legacy"` / `authority_cutover: false`. **There is currently no real, production-generated example artifact for this command to inspect.**

**Truth boundary (§16), confirmed:** inspecting an artifact never means PCAE possesses, has activated, or has transferred authority; current production authority remains `legacy`, stated in current source terminology, not CLTR-cutover language.

**Classification: CONFIRMED AS ADVANCED CLTR-TOOLING DOCS ONLY — not a README headline feature.** Real, correctly read-only, correctly fail-closed, but with no real-world usable example today. Documented narrowly in `docs/CAPABILITY_REFERENCE_V0_3_2.md`, consistent with (and slightly more conservative than) 3A's own low-medium release-value rating.

## 17. Packaging verification

| Capability | Wheel | Sdist | Repo-only | CLI registered | Installed usable |
|---|---:|---:|---:|---:|---:|
| `pcae runtime inspect` | yes | yes | no | yes | yes |
| Interactive Workflow / CHGR | yes | yes | no | yes | yes |
| Repository Intelligence | yes | yes | no (but functionally requires a `pcae-harness`-shaped tree) | yes | yes, self-inspection only |
| `pcae authority inspect` | yes | yes | no | yes | yes (no production example artifact exists) |

## 18. Clean environment rule

All four capabilities' final documented workflows were exercised from the wheel install against disposable repositories (not editable source, not the dev repo's own working tree, with the single documented Repository Intelligence exception noted in §4–6, immediately reverted). Sdist install was verified for CLI-registration parity (`--help` output identical) for all four; the full multi-step CHGR workflow and the RI hardcoded-path finding were verified from the wheel install specifically (sdist installs the same wheel-equivalent package; no material difference was expected or found in CLI surface).

## 19–28. Documentation changes

- **`README.md`** — added "More Capabilities Already Included" section: `pcae runtime inspect` (full product workflow), the interactive governed decision workflow (full product workflow, linked to `docs/COMMANDS.md#decision-session` which was already accurate), Repository Intelligence (explicitly scoped as self-inspection, linked to the new reference doc), and a narrow one-paragraph mention of `pcae authority inspect` deliberately kept out of the bulleted feature list.
- **`docs/QUICKSTART_V0_3.md`** — added an "Explore Next" section between the golden-path close-out (§12, audit trail) and the "What PCAE Does NOT Yet Do" section (§13), so the primary intake golden path (§1–12) is unmodified. Links to the new reference doc.
- **`docs/COMMANDS.md`** — **not modified.** This file is a *generated* artifact (`pcae docs commands`); `pcae docs commands --dry-run` output was byte-identical to the committed `HEAD` version, confirming the drift `pcae check` flagged came entirely from an initial hand-edit attempt, which was reverted (`git checkout -- docs/COMMANDS.md`). The generator does not currently enumerate `pcae runtime inspect`, `pcae repository-intelligence`, or `pcae authority inspect` as command areas — a real, pre-existing generator gap, disclosed here as operational debt, not fixed (fixing the generator is a production-source change, out of scope for this documentation-only phase). `decision-session` and `governance-record` *are* already correctly covered by the generator and were independently re-verified accurate against live CLI output — no change needed there.
- **`docs/CAPABILITY_REFERENCE_V0_3_2.md`** (new) — the `docs/COMMANDS.md`-equivalent the phase brief anticipates (§22's "or repository-conventional equivalent"), containing full verified syntax, prerequisites, side-effect classification, authority semantics, and worked examples for all four capabilities, including the two findings above (Repository Intelligence's hardcoded-path scope; `governance-record publish`'s generic-error-mapping rough edge; `authority inspect`'s no-production-example-artifact finding).
- **`CHANGELOG.md`** — added an "Unreleased (post-v0.3.1, on `main`)" entry summarizing the documentation exposure and its scope/findings.

**Side-effect labels (§23):** `pcae runtime inspect` — READ-ONLY, NO EXECUTION. Interactive Workflow — LOCAL GOVERNED MUTATION (writes to `.pcae/` in the target repository only; never a git commit/push). Repository Intelligence `snapshot generate` — LOCAL WRITE (writes `.pcae/repository-intelligence/`); `query`/`change-impact`/`advisory context build` — READ-ONLY. `authority inspect` — READ-ONLY, NO EXECUTION.

**Runtime capability disclosure (§24):** preserved verbatim in both README and the reference doc — `Observed` / `observe` / `unavailable`. None of the four newly-documented capabilities change this.

## 29. Release-batch final selection

| Candidate | Final classification |
|---|---|
| Runtime/plugin introspection (`pcae runtime inspect`) | **CONFIRMED FOR v0.3.2** — full product workflow |
| Interactive Workflow / CHGR | **CONFIRMED FOR v0.3.2** — full product workflow, one documented field-format caveat |
| Repository Intelligence (RKS/Query/Advisory-Context/Change-Impact) | **CONFIRMED FOR v0.3.2, scope-corrected** — advanced/self-inspection docs, not a general-audience README feature; retained because real, safe, tested, and honestly documented |
| `pcae authority inspect` | **CONFIRMED AS ADVANCED DOCS ONLY** — narrow CLTR-tooling mention, deliberately excluded from README headline treatment |

No candidate required source repair or was fully removed; Repository Intelligence's scope was corrected from 3A's framing based on new independent evidence (the hardcoded-path finding), and `authority inspect` was documented more conservatively than 3A's already-modest rating, based on the no-production-artifact finding.

## 30. Release theme

**Expose PCAE's existing governed inspection and intelligence capabilities as supported installed workflows — accurately scoped to what each one actually does.** Derived from the verified results: three of four candidates are genuinely general-purpose product workflows; the fourth (Repository Intelligence) is real and valuable but scoped to self-inspection, not general repository analysis, and is documented as such rather than oversold.

## 31. Version check

Confirmed **v0.3.2** remains appropriate. All work performed was verification and documentation; zero production source, CLI, contract, or packaging-configuration change occurred; no new commands, no new dependencies, no behavior change. This is patch-level documentation/discoverability scope.

## 32. Focused verification tests

| Capability | Suite(s) | Passed | Failed | Skipped |
|---|---|---:|---:|---:|
| Runtime/plugin introspection + `authority inspect` | `test_runtime_registry_contract.py`, `test_runtime_registry_prototype.py`, `test_runtime_registry_verification.py`, `test_runtime_introspection_prototype.py`, `test_runtime_introspection_architecture.py`, `test_authority_inspect_137k.py`, `test_typed_authority_inspector_137e.py` | 693 | 0 | 0 |
| Interactive Workflow / CHGR | `test_phase_145g_decision_session_cli.py`, `test_phase_145g1_decision_session_cli_repair.py`, `test_phase_145g3_decision_session_identity_binding.py`, `test_iwc_143o_session_coordination_publication_handoff.py`, `test_phase_144c_publication_coordinator.py` | 197 | 0 | 0 |
| Repository Intelligence | `test_phase_120e_repository_knowledge_snapshot.py`, `test_phase_121e_repository_intelligence_query.py`, `test_phase_122e_repository_intelligence_advisory_context.py`, `test_phase_123e_repository_intelligence_change_impact.py`, `test_phase_124e_repository_intelligence_hardening.py` | 72 | 0 | 0 |

No broad `python -m pytest -n auto` regression suite was run this phase — per the phase brief's focused-verification instruction, only suites directly relevant to the four selected capabilities were run. All 962 targeted tests pass.

## 33. Installed workflow tests

Disposable repositories created via `git init` outside `pcae-harness` (in the session scratchpad, not under version control by this repository). No internal `.pcae` fixtures were copied. All prerequisite state (decision sessions, readiness packages, RI snapshots) was produced exclusively via legitimate supported PCAE commands run from the clean installed CLI. The one accidental dev-repo mutation (§4–6) was caught and reverted before any further work.

## 34. Product defects found

None requiring source repair. One test-input error was initially mistaken for a possible defect (`governance-record publish` "internal_error") and was fully reproduced and correctly attributed to invalid `--template-ref` input, not a code defect (§10–13). One minor, non-blocking UX rough edge was found and documented, not repaired: generic exception-to-`internal_error` mapping in `decision_session.py`'s `run_with_error_mapping` obscures specific validation failures like `ChgrSchemaConformanceError`.

## 35–40. Carried-forward scope exclusions

Permission Broker: not touched, 3A classification (B, primitive-level gap DEFERRED) carried forward unchanged. HATP/HMIC/Class-B: not touched; no provisioning, certification, activation, readiness, or Dell mutation occurred or was proposed. Shell Gate: not touched; enforcement not enabled; audit-corpus timeout debt not addressed. Telegram: outbound-only, unchanged; only `pcae notify status` was queried (read-only). Backend/provider integrations: none touched — no Codex execution, no OpenRouter, no new backend, no adapter work. Operational debt (empty-`agent_id` provenance, historical task-memory sync-debt, shell-gate audit-corpus size) carried forward unchanged, not repaired.

## 41–42. Documentation truth audit

Every new claim in `README.md`, `docs/QUICKSTART_V0_3.md`, and `docs/CAPABILITY_REFERENCE_V0_3_2.md` traces to a specific live command invocation or source citation captured during this phase (see §4–16 above). No claim exceeds verified evidence. Link/anchor check performed manually: all `docs/CAPABILITY_REFERENCE_V0_3_2.md#<anchor>` and `docs/COMMANDS.md#decision-session` links were checked against the target files' actual heading-derived GitHub anchors and corrected once (an initial mistake put the anchor fragment in the link *label* rather than the URL — caught and fixed for all four instances before this document was written). CLI-help-to-documentation comparison performed live for every documented command (see per-capability sections). Quickstart golden path (§1–12) left byte-unmodified — only the new "Explore Next" section was inserted after it.

## 43. Current product workflow map

```
CHANGE INTAKE
    -> pcae intake create/show/list, pcae intake from-files (unchanged, v0.3.0/v0.3.1)

REPOSITORY UNDERSTANDING (self-inspection only, pcae-harness checkouts)
    -> pcae repository-intelligence snapshot generate
    -> pcae repository-intelligence query --snapshot <path>
    -> pcae repository-intelligence change-impact --snapshot <path>
    -> pcae advisory context build --snapshot <path>

RUNTIME INSPECTION
    -> pcae runtime inspect

GOVERNANCE / AUTHORITY INSPECTION
    -> pcae authority inspect <path>   (CLTR-tooling; no production example yet)

INTERACTIVE GOVERNANCE
    -> pcae decision-session create/evidence/select/preview/confirm/readiness
    -> pcae governance-record publish/inspect/verify
```

## 44. No new architecture

No architecture document, normative contract, schema, plugin ABI, or authority model was created. Only this phase document plus the capability reference doc and the standard task/session/handoff governance artifacts were produced.

## 45. No release action

No version change, no tag, no GitHub Release, no artifact upload, no PyPI publication.

## 46. Governance results (this phase)

- `pcae health`: healthy
- `pcae check`: passed
- `pcae status coherence`: coherent
- `pcae doctor task-memory`: warnings (pre-existing, unrelated, unchanged)
- `pcae push check`: nothing_to_push (pre-finalization baseline; re-verified at close)
- `pcae runtime inspect`: unchanged (`Observed`/`observe`/`unavailable`)
- Telegram: configured, ready
- Production-source change count: **0**

## 47. Summary

```
SELECTED CAPABILITY VERIFICATION:
PASS

PRODUCTION SOURCE CHANGES:
0

REPOSITORY INTELLIGENCE:
CONFIRMED AND EXPOSED, scope-corrected to self-inspection only
(not a general "inspect your repository" product feature)

RUNTIME/PLUGIN INTROSPECTION:
CONFIRMED AND EXPOSED

INTERACTIVE WORKFLOW / CHGR:
CONFIRMED AND EXPOSED AT FULL SAFE SCOPE

AUTHORITY INSPECT:
CONFIRMED AND EXPOSED as advanced CLTR-tooling docs only
(no production example artifact exists yet)

FINAL RELEASE BATCH:
Runtime/plugin introspection, Interactive Workflow/CHGR,
Repository Intelligence (self-inspection scope), pcae authority inspect
(advanced docs only)

RUNTIME:
Observed / observe / unavailable

RECOMMENDED VERSION:
v0.3.2

ARTICLE:
STOPPED
```

## 48. Recommended next phase

**149O.20L.7O.3C — PCAE v0.3.2 Release Hardening and Release Candidate Verification.** 3C should: freeze the exact v0.3.2 scope as finalized in §29 above; bump version; prepare release notes; build wheel/sdist; verify checksums; clean-install smoke; rerun the four selected capability workflows exactly as documented here; run release-critical regression; produce a publication checklist; not publish. No bounded integration/repair phase is required first — zero Blocking defects were found, all retained capabilities were verified from an installed package, documentation is truthful and scope-corrected where the initial audit's framing did not hold, and the batch is coherent.
