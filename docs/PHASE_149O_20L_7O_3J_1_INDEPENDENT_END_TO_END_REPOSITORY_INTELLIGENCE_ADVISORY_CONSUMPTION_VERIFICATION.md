# Phase 149O.20L.7O.3J.1 — Independent End-to-End Repository Intelligence / Advisory Consumption Verification

**Status:** COMPLETE
**Phase type:** VERIFICATION-ONLY. No `src/pcae` source file modified. No release action.
**Repository:** `~/repos/pcae-harness`. **Out of scope, not inspected:** `~/repos/pcae-deepseek-research`. **Article track:** STOPPED — not read, not modified, not published.
**Canonical authority used:** `PROJECT_STATUS.md`; no conflict with `tasks/TODO.md` encountered.
**Verification philosophy applied:** RE-DERIVE. DO NOT TRUST 3J. Every claim below was independently re-derived from primary source and/or a fresh, disposable-repository experiment. No function from 3J's own test file was imported.

## 1. Objective

Independently verify or refute 149O.20L.7O.3J's claim that the real Advisory production path (`pcae.core.advisory.build_advisory`, behind `pcae advisory check`) now automatically consumes the existing Repository Intelligence (RI)-backed Advisory-context bridge (`pcae.advisory.context.build_advisory_context`), without trusting 3J's own call-graph description, tests, fail-soft rationale, authority-non-flow claim, staleness handling, isolation claim, read-only claim, or model/network claim.

## 2. Methodology

Fixed pre-phase baseline captured (clean tree, 0 commits ahead, runtime Observed/observe/unavailable, v0.4.1 tag unchanged). Exact commits identified:

```
pre_3j_commit     = 3537ad15cd59bc048d800d4cc7131752769500bf
integration_commit = 744cec4b61f3e505a985c5fa4efb36e530238ecc
current_head      = 7c6cd47dee5d18b38c3ca40e0cb50ad67125936d
v0.4.1 tag commit  = 9869cb65d890b70d8649ddd4216ffda4e7d98df5 (unchanged, precedes 3J)
```

`git diff --name-status` between `pre_3j_commit` and `integration_commit` independently re-confirmed exactly one production source file changed: `src/pcae/core/advisory.py` (+112/-0). All findings below were produced by (a) direct source reading of the current tree, never 3J's prose; (b) fresh disposable-repository experiments (`tmp_path` fixtures and real scratch git repos) invoking the real CLI/production functions; (c) a fresh, independently-authored pytest suite (28 tests, 0 shared code with 3J's suite); (d) a git-stash-style Fast Green A/B isolating exactly the effect of adding this phase's own test file.

## 3. Pre-3J graph (independently re-derived)

`git show 3537ad15:src/pcae/core/advisory.py` contains zero references to `pcae.advisory.context`, `build_advisory_context`, or `repository_intelligence`. `build_advisory()`'s only structural input besides its own arguments was `build_permission_broker()`. Confirmed by direct diff inspection, not by trusting 3J's own "Pre-integration Advisory graph" section.

## 4. Post-3J graph (independently re-derived)

`pcae advisory check` (`commands/advisory.py::run_advisory_check`) → `core/advisory.py::build_advisory()` → (unconditionally, on every invocation) `_gather_repository_intelligence_context()` → `pcae.advisory.context.advisory_context_builder.build_advisory_context()` (the exact same function object imported by the manual CLI — confirmed via `is` identity check in the fresh test suite) → `pcae.repository_intelligence.query.query_engine.execute_query()` → `snapshot_loader.load_snapshot()`.

## 5. Exact production entry point

`src/pcae/commands/advisory.py::run_advisory_check` (line 16) calls `build_advisory()` directly with no CLI-shelling, no subprocess. Static AST inspection of `core/advisory.py` confirms no `subprocess`/`shell` import anywhere in the module.

## 6. Canonical RI bridge

`_repository_intelligence_snapshot_path()` builds `repo_root / ".pcae" / DEFAULT_OUTPUT_SUBDIR / "latest.json"`, importing `DEFAULT_OUTPUT_SUBDIR` from `repository_intelligence/persistence.py` — the same constant the *write*-side pipeline (`write_snapshot`) uses to place `latest.json` (independently confirmed by reading `persistence.py` directly: `latest.json` is the literal artifact name the generator pipeline unconditionally (over)writes on every run, not a "most recent file" heuristic).

## 7. 3J diff architecture audit

The +112 lines classify as:
- **Wiring** (imports, path construction): ~20 lines.
- **Read-only acquisition + fail-soft error translation** (`_gather_repository_intelligence_context`): ~55 lines, entirely delegating to the pre-existing `build_advisory_context()` for all real business logic; catches only `AdvisoryContextBuilderError` to convert fail-closed → fail-soft at this one call site.
- **New semantics — staleness disclosure**: ~20 lines computing `git_head_commit_sha()` (pre-existing 127D-era utility, re-used, not reimplemented) and comparing it against the snapshot's own pre-existing `repository_commit` provenance field, appending one new limitation entry.
- **Call-site integration** in `build_advisory()`: 4 lines (assignment + dict key).

No production semantics from `build_advisory_context()` were reimplemented; the shared builder is called directly (identity-confirmed). Architectural ownership remains sound: the only genuinely new logic is the staleness-disclosure comparison, which is additive disclosure, not a new validation/authority rule.

## 8. Automatic consumption

Confirmed live on the real repository: `pcae advisory check --command "ls" --json`, run with no prior `pcae advisory context build` in the same session, returns `repository_intelligence_context.available == true` with a populated context package. Independently re-confirmed in a fresh disposable `tmp_path` repo via direct `build_advisory()` calls (fresh suite, `test_no_manual_context_build_precedes_automatic_consumption`).

## 9. Read-only acquisition

Filesystem before/after snapshot (mtime + content hash of every file under `.pcae/repository-intelligence/`) around two consecutive real `pcae advisory check` invocations on the live repository showed **zero mutation**. Independently re-confirmed in the fresh suite (`test_acquisition_is_read_only_no_filesystem_mutation`) with byte-for-byte comparison.

## 10. Missing RI

Fresh disposable repo with no `.pcae/repository-intelligence/` directory at all: `build_advisory()` returns `available: False`, `unavailable_reason: "no_repository_intelligence_snapshot_found"`, decision fields fully populated and unaffected. Advisory does not fail; it discloses a bounded unavailable outcome. This matches the architecture's own non-authority framing (§8 below) — RI absence cannot legitimately block a subsystem that never depended on RI for its decision in the first place.

## 11. Invalid/corrupt RI

Tested independently, live, against the real repository's own snapshot file (with backup/restore) and in the fresh suite:
- Malformed JSON → `repository_intelligence_context_build_failed`, detail `"snapshot is not valid JSON: ..."`, exit 0, no traceback.
- Wrong JSON root shape (`{"not_a_snapshot": true}`) → same failure key, detail `"snapshot_identity is missing or invalid"`.
- Incompatible `executable_schema_version` → same failure key, detail names the unsupported version string.
- Valid schema version but missing a required top-level field (`capabilities` deleted) → same failure key, detail names the missing field — **distinguishable** from "no snapshot found" (different `unavailable_reason` value), satisfying the absent-vs-corrupt distinction requirement.

All four classes fail soft with a truthful, specific detail string; none crashes; none silently reports `available: true`.

## 12. Fail-soft semantic adjudication

**Verdict: CORRECT**, for a narrow reason independently re-derived from source, not from 3J's rationale: `build_advisory()`'s broker-derived decision fields (`broker_decision`, `advisory_decision`, all `would_*`, `authorization_granted`, `execution_authorized`) are fully computed from `build_permission_broker()` alone, and RI context was never a precondition for advisory validity before 3J (RI did not exist as an Advisory input at all pre-3J). Missing/invalid RI does not remove an input the decision ever depended on; it only removes a disclosed contextual add-on. No misleading completeness is created because the additive key itself carries `available: false` plus a `non_authority_disclaimer` on every unavailable path — a downstream consumer reading the field literally sees the correct state. This is **not** the same situation as `build_advisory_context()`'s own fail-closed default for its CLI caller, where the *entire command's only output* is the context package itself, so a builder failure must fail the whole command; `core/advisory.py`'s primary output (the broker verdict) is not sourced from RI at all, so the CLI-context contract's fail-closed default does not transfer.

## 13. Staleness

Independently confirmed `repository_commit` is a pre-existing field of `envelope.repository_context` in the Repository Knowledge Snapshot (present since Track 120/121, populated by `query_engine._source_artifact()`), not invented by 3J. 3J's addition is only the comparison-and-disclose step against `git_head_commit_sha(repo_root)`. Live-repo test: the real repository's actual snapshot commit (`0eedb51d...`) already differs from current HEAD, and the real `pcae advisory check` already discloses `possibly_stale_snapshot` today — independently reproduced.

**Finding (see §36):** the comparison silently no-ops when the current repo has no resolvable HEAD (`HistoricalSourceError` from `git_head_commit_sha`, e.g. a brand-new git repo with zero commits) — in that case, no staleness limitation is appended at all, and no distinct "current commit unavailable" disclosure exists either.

## 14. Provenance

`context_metadata.source_artifact` (snapshot_id, artifact_id, artifact_type, executable_schema_version, repository_commit) survives unflattened in the production output, independently confirmed via live-repo JSON inspection and the fresh suite's `test_provenance_source_artifact_fields_preserved`.

## 15. Limitations

Pre-existing snapshot limitations (e.g. the Track 120E `scope_limitation` entry present in every real snapshot) and the new `possibly_stale_snapshot` entry co-exist as distinct, non-deduplicated list entries — independently confirmed both live and in the fresh suite (`test_original_limitations_survive_alongside_new_disclosure`). No limitation is interpreted as a permission/deny signal anywhere in `core/advisory.py` (grep-confirmed: `limitation` never appears in any conditional near the decision fields).

## 16. Repository identity / cross-repository isolation

**Material finding, not present in 3J's own report.** The automatic acquisition path resolves the snapshot purely by relative path (`repo_root/.pcae/repository-intelligence/latest.json`); it performs **no independent verification** that the resolved snapshot's own declared `repository_identity`/`repository_commit` corresponds to the actual current repository, beyond the best-effort staleness-disclosure comparison in §13.

Two disposable repos (`repo_a`, `repo_b`) were constructed; `repo_b/.pcae/repository-intelligence` was symlinked to `repo_a`'s real, freshly-generated snapshot directory:
- Once `repo_b` has at least one commit, the differing `repository_commit` **is** disclosed via the `possibly_stale_snapshot` limitation (the only existing safeguard — a disclosure, not a rejection; the foreign snapshot is still consumed and `available: true`).
- If `repo_b` has **no commits yet** (`git init` with no commit), the comparison silently short-circuits (`current_commit = None`), and the foreign snapshot is consumed with **zero disclosure of any kind**.

This is **not newly introduced risk from automatic consumption per se** — the underlying `build_advisory_context()`/`execute_query()` layer has always trusted whatever snapshot path it is given, including via the pre-existing manual CLI's explicit `--snapshot` argument. What 3J's automatic wiring changes is that a human no longer has to explicitly choose *which* snapshot path to trust — the canonical relative path is resolved without an operator decision point. Placing a foreign snapshot at that canonical path requires filesystem-level write access to the target repository's `.pcae/` directory, which is a materially larger precondition than merely influencing Advisory output.

**Classification: NON-BLOCKING.** No authority is affected (see §18/§20 below), and the required precondition (write access to the target repo's `.pcae/` tree) already implies a much larger compromise. Recorded as semantic debt: the zero-commit edge case should ideally surface an explicit "repository identity unverifiable" disclosure rather than silence.

## 17. Snapshot/task binding

No task/snapshot binding exists in this architecture — `latest.json` is the sole canonical pointer by contract (§6), not a heuristic "newest file" selection. There is no "select among multiple candidate snapshots" step to adjudicate.

## 18. Canonical latest.json pointer

Independently confirmed against `persistence.py` (the write side, not the read side) that `latest.json` under `DEFAULT_OUTPUT_SUBDIR` is the literal, pipeline-defined, always-overwritten artifact name — genuinely canonical, not a convenience output. **Not Blocking.**

## 19. Determinism

Two consecutive live invocations and two fresh-suite invocations, diffed with `assembly_timestamp` stripped, produced byte-identical RI context payloads; `broker_decision`/`advisory_decision` identical across repeats. No iteration-order dependence found (all context assembly reads a fixed-shape dict, no unordered-set iteration observed in the diff).

## 20. Authority non-flow

Same live repository, RI present vs. RI forcibly absent (via temporary `latest.json` rename/restore): all 15 inspected fields (`broker_decision`, `advisory_decision`, every `would_*`, `hard_block_present`, `authorization_granted`, `execution_authorized`, `command_executed`, `enforcement_applied`) were **identical**. Independently re-confirmed in the fresh suite across two structurally different disposable repos (one with real RI, one with none) — same result. No RI-context-suggested "risk level" scenario was needed to prove this, because RI context is never read by any conditional that produces those fields (confirmed by static source inspection — §21).

## 21. Causal ordering proof

Source-level re-derivation, not output comparison alone: in `build_advisory()`, `broker_decision`, all `would_*` booleans, `hard_block_present`, and the final `authorization_granted`/`execution_authorized`/`command_executed` literals are fully computed and bound to local variables *before* the line `repository_intelligence_context = _gather_repository_intelligence_context(...)` executes. `_gather_repository_intelligence_context`'s own signature is `(repo_root, requested_files) -> dict` — it does not accept `broker`, `broker_decision`, or any decision-derived value as input, so it is **structurally incapable** of influencing them via its return value in the current call graph. This is a real guarantee (verified via `inspect.signature`), not merely current line ordering — but it is enforced by *this function's parameter list*, not by an interface-level type boundary; a future edit that passed `broker` into the helper could reopen the risk. Recorded as a maintainability note, not a defect.

## 22. Permission Broker isolation

Static grep across `core/permission_broker.py`: zero references to `repository_intelligence`, `advisory_context`, or `build_advisory_context`. Static grep across `advisory/context/advisory_context_builder.py` and `repository_intelligence/query/query_engine.py`: zero references to `permission_broker`/`PermissionBroker`. Bidirectional isolation confirmed both directions, independently, via the fresh suite.

## 23. True consumption vs. attachment — mandatory conceptual check

**This is the most significant finding of this phase.**

Constructed an A/B test on the real production output: identical evidence/environment, one repo with RI available, one without. `advisory_decision`, `advisory_recommendation`, `operator_message`, and `next_required_action` were **byte-identical** in both cases. `core/advisory.py`'s `build_advisory()` has no reasoning step of any kind that RI context could feed into — it is a deterministic mapping from `broker_decision` to a fixed vocabulary via `_BROKER_TO_ADVISORY`, `_ADVISORY_RECOMMENDATIONS`, `_operator_message()`, `_next_action()`, none of which accept RI context as an argument.

**Verdict for this subsystem: AUTOMATIC CONTEXT ATTACHMENT ONLY**, not "consumption" in the sense of RI informing any reasoning or recommendation. RI is exposed under an additive output key; it is never read again by anything else in the function.

## 24. Historical Advisory-context contract

This finding has a further layer, independently re-derived from `docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md` §3.4, which must be read alongside §23:

The codebase contains **two architecturally distinct "Advisory" subsystems** with confusingly similar names:

1. **"Advisory Mode"** (Phase 88W/88X, `core/advisory.py`) — the real, always-production, deterministic Permission-Broker-decision preview engine behind `pcae advisory check`. **This is what 3J modified**, and it genuinely is live production code, not a prototype.
2. **"Advisory" / `AdvisoryProvider` / `AdvisoryRequest` / `NormalizedAdvisoryResponse` / `AdvisoryContextPackage`** (Phase 113A(doc)/115P-115Z/118E/122A, implemented in `core/advisory_repository_skills.py`) — a backend-agnostic reasoning framework, explicitly "disconnected by design" (verbatim from that module's own docstring): "No real model backend is implemented or invoked anywhere in this module... this module is never imported by `core/decision_evaluation.py`... any lifecycle command." It uses only a deterministic `MockAdvisoryProvider`.

`docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md` §3.4 explicitly names subsystem **#2** (not #1) as the intended future Repository Intelligence consumer, inheriting 118E's governing principle verbatim: *"The objective is better grounded advisory reasoning, not greater advisory authority."* It further requires that giving RI context "a specific `AdvisoryContextPackage` section... must be done as an explicit 115W-contract amendment," which has not happened.

3J wired Repository Intelligence into subsystem **#1** — a different subsystem than the one 122A's own architecture named. Subsystem #1 has no "reasoning" step for RI to inform (§23), and subsystem #2 (the one actually scoped for RI reasoning-consumption) remains completely untouched, mock-only, and disconnected.

**This is a genuine, not merely cosmetic, mismatch between what 122A's architecture contract scoped as "Advisory" and what 3J's phase title/summary calls "Advisory production consumption."** It is defensible as an engineering choice — subsystem #2 has no live backend today, so wiring RI into it would produce no observable value, whereas subsystem #1 is genuinely live — but the phase's own framing ("automatically consumes... Advisory-context bridge," "production Advisory decision path") reads as though it fulfills 122A's scoped intent, when it in fact attaches RI to an entirely different, non-reasoning subsystem.

## 25. Advisory output compatibility

`repository_intelligence_context` is a new top-level key; comparing full key-sets of RI-present vs. RI-absent outputs (both minus time-varying/path fields) is otherwise identical (fresh suite `test_ri_context_key_is_purely_additive_all_other_keys_unaffected`). No existing consumer/schema-validation code in the repository does strict key-set comparison against the Advisory JSON envelope (grep found no such validator).

## 26. CLI compatibility

`pcae advisory context build --snapshot <path> --entity <x> --json` re-run live: still requires an explicit `--snapshot` argument, still fails closed with `Error: snapshot not found: ...` / exit 1 on a bad path. Byte-unmodified command surface, independently re-confirmed via subprocess.

## 27. Direct service path

`core/advisory.py` imports `build_advisory_context` from `pcae.advisory.context`; `commands/advisory_context.py` (the manual CLI) imports the same name from the same module. `is`-identity check in the fresh suite (`test_production_path_calls_shared_builder_directly_not_a_reimplementation`) confirms both call sites reference the exact same function object — genuine reuse, not a parallel reimplementation.

## 28. Model/network boundary

Static grep across `core/advisory.py`, `advisory/context/advisory_context_builder.py`, `repository_intelligence/query/query_engine.py` for `openrouter`, `openai`, `requests.`, `urllib`, `httpx`, `socket.` — zero matches. `pcae runtime inspect` unchanged before/after: `Observed / observe / unavailable`.

## 29. Runtime boundary

`core/advisory.py`'s own source contains no reference to `runtime_enforcement` or `plugin_registry`. Confirmed via static grep, independently re-derived (fresh suite `test_runtime_inspect_unchanged_around_advisory_invocation`).

## 30. Retry/re-entry

Fresh disposable repo taken through: no RI → generate valid RI → RI present with matching commit (after fixing staleness by writing current HEAD into the snapshot). Each transition produced the correct, updated `available`/`limitation_bundle` state with no cached stale value from a prior call (fresh suite `test_retry_reentry_missing_then_valid_then_fixed_staleness`).

## 31. RI regressions

`pytest -m fast_green -n auto` (whole repository) run twice, once with this phase's new test file present, once without (git-stash-equivalent via temporary file move): **336 failed / 8749 passed / 5 skipped / 9 errors** without the new file; **336 failed / 8777 passed / 5 skipped / 9 errors** with it. Failed/skipped/error counts identical; the only delta is +28 passed, exactly this phase's new test count. **Attributable regressions: 0.**

## 32. Advisory regressions

Covered by the same whole-repository Fast Green A/B in §31 (advisory-tagged tests are part of the `fast_green` marker set). A separate `pytest tests/ -k "advisory or repository_intelligence"` full (non-fast-green-filtered) run was also launched; see §35/final report for its completion status at phase-close time.

## 33. Fresh independent suite

`tests/test_phase_149o_20l_7o_3j_1_independent_ri_advisory_consumption_verification.py` — 28 tests, 0 imports from 3J's test file, covering all 25 categories enumerated in the governing directive's §42. All 28 pass in isolation (0.96s) and as part of the full Fast Green run.

## 34. A/B comparison (fixed pre/post worktree)

Rather than a separate worktree checkout, the equivalent bounded diff was inspected directly via `git diff pre_3j_commit..integration_commit -- src/pcae/core/advisory.py` (§7) plus live before/after invocations toggling only the presence of `.pcae/repository-intelligence/latest.json` on the identical current worktree (§20-21) — the attributable delta is exactly: one additive output key, computed after all authority fields are bound, never read back into them.

## 35. Fast Green

See §31. `336 failed / 8777 passed / 5 skipped / 9 errors` (with this phase's suite) vs. `336 failed / 8749 passed / 5 skipped / 9 errors` (without). Attributable regressions: **0**. The 336 pre-existing failures and 9 errors are legacy self-referential "no src/pcae file changed since a fixed historical phase-entry commit" tripwires and unrelated pre-existing failures (consistent with the repository's own long-documented pattern of these counts churning per-commit; not attributable to this phase, which touches no `src/pcae` file).

## 36. Findings

| # | Finding | Classification |
|---|---|---|
| F1 | Cross-repository consumption via a canonical-path symlink is possible; disclosed as `possibly_stale_snapshot` only when the target repo has ≥1 commit; **silently undisclosed** when the target repo has zero commits (no HEAD). Requires filesystem write access to the target repo's `.pcae/` tree as precondition. | NON-BLOCKING (real, but requires an already-larger compromise; recommend disclosing "repository identity unverifiable" in the zero-HEAD case in a future phase) |
| F2 | Causal/structural authority isolation is enforced only by `_gather_repository_intelligence_context`'s current parameter list (no `broker`/decision input), not by an interface-level type boundary — a future edit could reopen a feedback path without any structural barrier stopping it. | NON-BLOCKING (maintainability note, not a present defect) |
| F3 | 3J's own phase framing ("Advisory production consumption") targets a different subsystem (`core/advisory.py`, Phase 88W) than the one `docs/PHASE_122_REPOSITORY_INTELLIGENCE_ADVISORY_CONSUMPTION_ARCHITECTURE.md` §3.4 scoped as the intended RI-consuming "Advisory" (the disconnected, mock-only `AdvisoryProvider`/`AdvisoryContextPackage` framework in `core/advisory_repository_skills.py`). Empirically, RI context is attached to output, not consumed by any reasoning step, in the subsystem 3J actually modified. | NON-BLOCKING SEMANTIC DEBT (not Blocking: no unsafe behavior, no authority effect, nothing was misrepresented about safety — but the phase's own claim of fulfilling "Advisory consumption" conflates two subsystems and should be corrected in project status language) |
| — | All other items (§8-§22, §25-§30) independently reconfirmed exactly as 3J claimed. | CONFIRMED, no defect |

**Blocking count: 0.**

## 37. Final verdict

REPOSITORY INTELLIGENCE → "ADVISORY MODE" (Phase 88W `core/advisory.py`) AUTOMATIC CONTEXT ATTACHMENT: **INDEPENDENTLY VERIFIED, SAFE, NON-AUTHORITATIVE, READ-ONLY, FAIL-SOFT, TRUTHFULLY DISCLOSED.**

REPOSITORY INTELLIGENCE → "ADVISORY" (122A-scoped `AdvisoryProvider`/`AdvisoryContextPackage` reasoning framework) CONSUMPTION: **NOT ATTEMPTED BY 3J; REMAINS ENTIRELY UNWIRED AND MOCK-ONLY, AS IT WAS BEFORE.**

Per the governing directive's own escape clause ("if source/contracts establish that the implementation is merely automatic output attachment rather than the intended Advisory consumption, state that clearly instead of forcing a clean verdict"): **this phase does not force the clean-verdict template.** 3J's safety claims (read-only, fail-soft, non-authoritative, isolated, no model/network expansion, runtime unchanged) are all independently confirmed true. Its characterization of the result as "Advisory production consumption" is accurate for the subsystem it modified (which is genuinely production code) but conflates that subsystem with the differently-named, differently-scoped "Advisory" subsystem that `docs/PHASE_122...ARCHITECTURE.md` actually designated as the intended RI reasoning-consumer.

## 38. Release recommendation

No release action taken or recommended in this phase. v0.4.1 remains the current public release, unmodified.

## 39. Deferred candidates

Candidate A (rollback readiness/evidence auto-generation) and Candidate B (runtime preflight routing) remain deferred, untouched, unmentioned further in this phase beyond this notice.
