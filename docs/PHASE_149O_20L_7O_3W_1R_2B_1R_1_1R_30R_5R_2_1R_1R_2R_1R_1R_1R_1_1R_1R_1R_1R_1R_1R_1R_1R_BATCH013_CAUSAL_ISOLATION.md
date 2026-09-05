# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R — Checkpointed RHAMP Execution-Time Class-Identity / State-Trace Campaign Continuation, Batch-013 Causal Isolation, Production-Reachability Determination, and F-5 Hold Re-Adjudication

**STATUS: COMPLETE (diagnostic/adjudication phase). CHECKPOINT METHOD:
VERIFIED (continuation, not reset). RESUME MODEL: A. CHECKPOINTED RHAMP
TRACE CAMPAIGN: VALID (continued). CAMPAIGN_ID:
`RHAMP-XTEST-IDENTITY-TRACE/1`. CORPUS_ID: `RHAMP-XTEST-CORPUS/1`. CLEAN
BATCHES: 18/31 (unchanged). NON-CLEAN LEAD BATCHES: 1 (batch-013, now
root-caused). INCONCLUSIVE/TIMEOUT: 7/31 (unchanged, not scanned this
phase). NEVER ATTEMPTED: 5/31 (unchanged, not scanned this phase).
CONTAMINATION ROOT CAUSE: IDENTIFIED. CONTAMINATION STAGE: TEST-EXECUTION.
CONTAMINATION LOCATION: TEST-HARNESS ONLY. CURRENT F-5 READINESS: NOT YET
ESTABLISHED (11/12 clearance criteria satisfied; one narrow re-check
blocked by a permission restriction in this diagnostic process, not by
new evidence of a violation). F-5 EXECUTION HOLD: REMAINS. N-16-5: NOT
CLOSED.**

## Predecessor lineage and CPIPC successor evidence

- Predecessor: `149O...1R.1R.1R.1R.1R.1R.1R` ("Checkpointed
  Incrementally-Resumable RHAMP Execution-Time Class-Identity / State-Trace
  Coverage Advancement, Method Validation, and F-5 Hold Adjudication").
- This phase: `149O...1R.1R.1R.1R.1R.1R.1R.1R` — verified via
  `pcae.core.phase_id.parse`/`same_series`/`same_branch`/`compare`: same
  series (149), same branch (`O`), `compare(predecessor, candidate) ==
  "less"`, and the candidate's subphase tuple equals the predecessor's tuple
  plus exactly one trailing `(1, 'R')` segment — a direct CPIPC successor,
  not merely two independently-valid IDs. **CPIPC SUCCESSOR: VERIFIED.**
- R0 (this phase's entry SHA) = `4fe1ba7046daf389266335800a1bc9fa591e5a47`.

## Predecessor K0 / production-diff reconciliation

- `P_ENTRY` = `ac6aee007540cb2433b1714f0c09b7cbbcf19920` ("open task,
  archive superseded idle task" — the commit's own subject names the
  predecessor phase ID; its parent, `2ea285f3`, belongs to the prior sibling
  phase, confirming this is the true phase-entry boundary).
- `P_CHANGE` = `5c86c630` ("checkpointed RHAMP batch-composition campaign").
- `P_FINAL` = `4fe1ba70` (== this phase's own R0).
- **REPORTED K0 ACTUAL ROLE:** `P_ENTRY` itself — the predecessor's
  `RHAMP_XTEST_CORPUS_1_manifest.json`'s own `K0` field is
  `ac6aee007540cb2433b1714f0c09b7cbbcf19920`, matching `P_ENTRY` exactly.
  **PREDECESSOR K0 METADATA LABELING: ACCURATE** (not a mislabeling — `K0`
  literally denotes the predecessor's phase-entry commit, used as the
  corpus-freeze point).
- `git diff --name-only ac6aee00 4fe1ba70 -- src/pcae scripts pyproject.toml
  docs/contracts` → **empty**. `git diff --name-status ac6aee00 4fe1ba70 --
  tests/` → additions only (checkpoint/evidence/IV artifacts), no existing
  test modified. **PREDECESSOR NO-PRODUCTION-DIFF: INDEPENDENTLY VERIFIED.**

## `Tests run` report-header semantics

Traced `src/pcae/core/phase_reports.py` lines 466-472: the header uses
`self.tests_run` if positive, else falls back to `"{len(test_results)}
suite(s)"`, else `"not captured"`. `tests_run` is derived by the phase-
complete finalizer from `tests_added_or_updated`'s **leading integer
token** — a count of *test artifacts added/updated this phase*, not a raw
pytest-invocation counter. The predecessor's own
`.pcae/phase-completion-metadata.json` set
`tests_added_or_updated: "1 new fresh phase-specific IV test file ...
29 pytest invocations run this phase for the diagnostic campaign itself
... tracked separately as diagnostic budget, not phase-specific IV."` —
exactly matching the observed header value of `1`, with the true 29-
invocation accounting correctly preserved in prose and the invocation-log
evidence file. **REPORT HEADER TEST-COUNT SEMANTICS: EXPECTED** (not a
defect — the field is intentionally scoped to "new/updated test files,"
distinct from the diagnostic-campaign invocation budget it sits beside).

## Campaign continuation (not reset)

Loaded the predecessor's canonical checkpoint
(`.pcae/evidence/RHAMP_XTEST_CHECKPOINT_current.json`,
`self_digest=sha256:3f8ef5...`). Verified `campaign_id`/`corpus_id`/
`corpus_digest`/`tracer_digest`/`resume_model` unchanged; the 18 clean
`completed_unit_ids` were **not** re-run; the manifest's frozen batch-013
file list (25 files) was used verbatim. Wrote a new checkpoint
(`self_digest=sha256:a27cf7...`) whose `previous_checkpoint_digest` points
at the predecessor's `self_digest`, preserving the chain. Coverage counts
are **unchanged this phase** (18 clean / 1 non-clean / 7 inconclusive / 5
never-attempted = 31) — this phase's work is entirely *within* the
already-checkpointed batch-013 unit, not new coverage.

## Batch-013 causal isolation

This phase's own diagnostic budget (fresh 30 invocations / 60 min; 14
invocations / ~171s (~2.9 min) used, stopped voluntarily at legitimate
stop condition A — root cause identified and reachability adjudicated).
Full per-invocation record and bisection narrative:
`.pcae/evidence/RHAMP_XTEST_CORPUS_1_experiment_log.md` (appended section).
Tracer: a reconstructed `rhamp_xtest_tracer2` (the predecessor's own tracer
script was scratch-only and not preserved, matching its own noted pattern
for other ephemeral driver code) — same `tracer_version=1` semantics:
`id()`/`__module__`/`__qualname__` of `HPACStoreAuthority` and
`HumanPrincipalRegistryStore` captured at collection-finish and again at
session-finish.

Bisection path: victim-alone (clean) → full batch-013 (reproduces, 79
errors) → 13-file half (reproduces) → 6-file quarter (reproduces) → 3+3
split (`146l+147g+147h` reproduces; `146g+146h1+146h3` clean) → per-file
isolation (`146l` alone clean, `147g` alone clean, **`147h` alone
reproduces**) → node-level isolation (single test node reproduces) →
trigger-removal control (`147h` minus that node → clean) → fresh-process
repeat of the minimal reproducer (identical result).

### Root cause: IDENTIFIED

**File:**
`tests/test_phase_147h_authority_evaluation_independent_verification.py`,
lines 780-791.
**Node:**
`TestForbiddenDependenciesIndependent::test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone`.

The node deletes every `sys.modules` entry matching
`pcae.authority_evaluation*` **or any of `_FORBIDDEN_IMPORT_ROOTS`**
(lines 732-742, which includes the literal string `"pcae.core"`), then
calls `importlib.import_module("pcae.authority_evaluation")`. This removes
`pcae.core.hpac_foundation` and `pcae.core.human_principal_registry` (and
every other loaded `pcae.core.*` submodule) from `sys.modules`, but does
**not** invalidate references other already-imported code still holds to
the pre-deletion class objects (fixtures, registries, or other test
modules' `from pcae.core.hpac_foundation import HPACStoreAuthority`
module-level bindings). When the victim later triggers a fresh import of
those modules, Python constructs **new** module/class objects with
identical `__module__`/`__qualname__` but a distinct `id()` — the exact
signature the tracer recorded. `isinstance(record, HPACStoreAuthority)`
-style checks in the victim then compare live objects against whichever
class reference happens to be bound wherever the check executes, producing
the observed 37 failures and 2 victim `ERROR`s
(`test_94_counter_missing_fails_closed_not_zero`,
`test_95_assurance_class_of_enrolled_records_is_production`).

**Mechanism:** DUPLICATE MODULE IMPORT / STALE REFERENCE.
**Contamination stage:** TEST-EXECUTION (inside the trigger node's own
function body — not collection, fixture-setup, or teardown).

### Four-way causal proof

| Leg | Composition | Result |
|---|---|---|
| A — victim alone | victim only | 125 passed, 0 errors — **clean** |
| B — minimized trigger + victim | trigger node + victim | 5 failed, 131 passed, 79 errors, id() drift — **contaminated** |
| C — composition minus trigger | full `147h` file, trigger node `--deselect`ed, + victim | 214 passed, 1 deselected, id() stable — **clean** |
| D — fresh-process repeat of B | trigger node + victim, new process | 5 failed, 131 passed, 79 errors — **identical to B** |

### Production reachability: NOT PRODUCTION-REACHABLE → TEST-HARNESS ONLY

- `grep -rn "del sys.modules\|importlib.reload" src/pcae/` → **zero
  occurrences**. The mechanism does not exist anywhere in production
  source.
- `scripts/hpac_protected_presentation_admin.py` and
  `scripts/hpac_protected_root_admin.py` contain **no `sys.modules`
  manipulation** — traced their imports/factories/registries/verifiers
  source-only (not run against the real protected root); the PPA
  registration path cannot encounter this trigger.
- **Uniqueness across the corpus:** `grep -rl "del sys.modules\[" tests/`
  finds 6 files total. The other 5 either use unique synthetic module
  names (3 HATP files: timestamp-canonicalization x2,
  repository-identity-trust-store — none touch `pcae.core`) or scope their
  deletion to an unrelated root (`pcae.cltr.authority` in one CLTR file;
  `pcae.authority_evaluation`-only in this same file's two sibling tests).
  This phase's own new IV test
  (`test_trigger_pattern_is_unique_among_all_test_files_touching_pcae_core`)
  mechanically re-verifies this uniqueness. **Per governed item 23, this
  single identified causal defect fully explains the batch-013 signal**;
  the remaining 5 never-attempted + 7 inconclusive batches were not
  rescanned this phase.

## Bounded clean-context N-16-5 readiness band (item 30)

Fresh process, no batch-013 files present, 15 files spanning Gate 5, Gate
9, `hpac_verifier`, the merged-RHAMP IV, protected-presentation
real-assurance IV, and 3 PAWA v1.1/v1.2 IV files: **700 passed, 2 failed**
(`test_object_dunder_new_bypasses_trusted_construction_seal`,
`test_forged_via_object_new_would_report_real_runtime_eligible` — the
pre-existing, previously-adjudicated "hpac_verifier forged-object findings:
NONBLOCKING THROUGH ACTUAL CONSUMPTION PATH" finding, preserved unchanged
per item 31, no new evidence contradicts it), `id()` stable throughout.
PAWA/PPA/protected-presentation/RHAMP/`hpac_verifier`/Gate evidence
**remains meaningful**.

Configured-agent-identity-threading-repair IV suite (bounded band): 35
passed, 3 skipped, 3 failed — `test_iv_entry_sha_is_current_head` is a
frozen-HEAD point-in-time guard (expected to fail as HEAD moves forward);
the other two (`test_host_protected_root_generation_and_helper_digest_unchanged`,
`test_ppa_current_generation_and_installation_absent_on_host`) raised
`PermissionError` on `.stat()` of
`/Library/Application Support/PCAE/HPAC/protected-root/.authority/*` in
this diagnostic phase's own process/user context — see F-5 hold reasoning
below.

## F-5 EXECUTION HOLD: REMAINS (narrow reason)

Of the 12 governed clearance criteria (item 33), **11 are satisfied** by
the evidence above (root cause identified; four-way causal proof; stage
established; reachability established as test-harness-only; production
separation demonstrated; configured-agent/PAWA/PPA/protected-presentation/
RHAMP/`hpac_verifier`/Gate evidence all remain meaningful). The blocker is
**criterion 11** (no current generation-1 invariant violation): this
diagnostic phase's own process lacks filesystem permission to read
`_PROTECTED_ROOT/.authority/*`, so the host's generation-1 / PPA-absent
state could **not be positively confirmed** here — the check raised
`PermissionError` rather than returning a definite pass. Per item 34
("relevant verification remains unreliable"), the hold **REMAINS** pending
exactly that one narrow re-check under adequate host-filesystem
permissions. No further contamination-campaign diagnostic work is required
first — this is a permissions/environment gap in *this* execution context,
not new evidence of an actual invariant violation, and not itself part of
the contamination question this phase was chartered to resolve.

## No production / existing-test / contract / dependency / host change

- `git diff --name-only P_FINAL HEAD -- src/pcae scripts pyproject.toml
  docs/contracts` → empty.
- `git diff --name-status P_FINAL HEAD -- tests/` → additions only (this
  phase's own new IV file); no existing test modified, skipped, or
  reference-removed.
- No `scripts/hpac_protected_root_admin.py provision` or
  `scripts/hpac_protected_presentation_admin.py install` run; no
  reprovisioning, reinstall, or generation reset; no PPA registration; no
  YubiKey/FIDO2/human-approval ceremony; no Telegram re-dispatch of
  historical reports.
- Runtime remains `Observed`/`observe`/`unavailable`; 0 plugins/
  capabilities; first governed runtime external effect ABSENT/UNREACHABLE.

## Diagnostic budget accounting

14 of 30 targeted pytest invocations; ~171.4s of ~3600s experimental time.
Legitimate stop condition: **A — root cause identified and reachability
adjudicated** (item 60), reached with 16 invocations and ~59.3 minutes of
budget still available — stopped voluntarily, not by exhaustion, once the
governed bar (four-way causal proof + stage + reachability + uniqueness +
bounded clean-context band) was met.

## Next recommended (not begun)

A narrowly-scoped continuation phase to (a) re-run the two blocked
generation-1/PPA-absence host checks under adequate filesystem permissions
and, if they confirm the carried-forward state, (b) formally re-adjudicate
F-5 EXECUTION HOLD → CLEARED and derive the Production Protected-
Presentation Registration Continuation successor per item 50. This phase
does not begin that work. N-16-6 and N-16-7 remain untouched.
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved.
