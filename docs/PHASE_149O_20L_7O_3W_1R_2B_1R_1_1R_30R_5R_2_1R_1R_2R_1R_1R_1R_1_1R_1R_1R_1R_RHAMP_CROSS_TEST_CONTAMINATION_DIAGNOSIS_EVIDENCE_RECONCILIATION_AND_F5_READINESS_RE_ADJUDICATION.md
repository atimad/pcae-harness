# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R — RHAMP Cross-Test Contamination Diagnosis, Evidence Reconciliation, and F-5 Readiness Re-Adjudication

## Scope

Diagnostic/adjudication only. No production repair, no test modification,
no F-5 execution, no protected-root mutation, no human/YubiKey ceremony,
no historical Telegram re-dispatch performed in this phase.

## Phase-ID validity (CPIPC)

Successor `...1R.1R.1R.1R` independently re-validated against
`src/pcae/core/phase_id.py` (CPIPC-001 v1.0, sole authority): both the
predecessor and this phase's candidate ID `parse()` successfully;
`same_series`/`same_branch` both `True`; `compare(predecessor, candidate)
== "less"` (strictly ordered after). **No discrepancy — the ID specified
in the phase prompt is exactly the CPIPC-valid successor.** Predecessor
(`...1R.1R.1R`) confirmed as the latest canonical completed phase via
`pcae phase-report show --latest` before opening this phase.

## D0 (phase-entry freeze)

- `D0` = `e6bd2c718eca485104da8638ed8122035f692ed3`
- Working tree/staging: clean at entry
- Environment used for all diagnostic pytest invocations in this phase:
  `.venv/bin/python` = Python 3.9.6, pytest 8.4.2, pytest-xdist 3.8.0
  (the project's canonical test environment; distinct from the Homebrew
  Python 3.14.5 that `python`/`python3` resolve to on this host — the
  `pcae` CLI itself works under either, but pytest runs used the pinned
  `.venv`)
- `PYTHONHASHSEED`: unset (default randomized per-process, as in all
  prior phases in this chain)
- `pyproject.toml` `[tool.pytest.ini_options]`: `testpaths = ["tests"]`,
  `pythonpath = ["src"]`, `addopts = "--dist=loadfile"` — unchanged from
  D0 through phase end (verified below)

## Diagnostic budget accounting

Full accounting preserved durably at
`.pcae/evidence/149O_1R1R2R1R1R1R1_1R1R1R1R_experiment_log.md`
(SHA-256 covered by the evidence manifest below). Summary: **5 completed
targeted pytest invocations + 1 aborted/infeasible large-scale attempt**,
of the 30-invocation maximum; **~24 minutes of cumulative wall-clock
diagnostic time**, of the 60-minute maximum. Diagnostic experimentation
was deliberately stopped inside budget once the available falsifiable
hypotheses were exhausted and a further attempt at full-prefix bisection
was independently shown infeasible (see below), rather than continuing
to consume the remaining budget without a new hypothesis to test. No
diagnostic subprocess was left running or unaccounted for (verified via
`ps aux | grep pytest` = empty after every invocation completed or was
terminated).

## Evidence preservation (post-completion reconciliation)

Surviving `/tmp/pcae-triage-149o-1r1r1r/` evidence (left by the prior,
non-governed reconciliation pass referenced in the phase prompt) was
copied unchanged into durable canonical storage under `.pcae/evidence/`
with a byte-identical SHA-256 match confirmed between original and copy
for every file:

| File | SHA-256 |
|---|---|
| `full_sweep_reproduction_at_head.log` | `31fdef417a84240d8ac760cc66658bcff17070dd8292ffd97d28d9039496c144` |
| `isolated_results.tsv` | `02182885f29d822d55a90acaf684de7d9f0f5b05972703163d9fdb2cd51b529c` |
| `failing_files.txt` | `6a1acdc594678a05fbfcf8a70f7ee0bb8f4df19bbc7ba502b6a4e691e23cff91` |
| `short_summary.txt` | `b4774b643a71d741e4ed604f3b4a6e6e0a41f0e604d94f57517458078ea1f949` |

(`isolate_check.sh`/`isolate_check.out` were transient scratch files, not
preserved — their content is fully subsumed by `isolated_results.tsv`.)
Originals in `/tmp` left unmodified; durable copies are the canonical
record from this point forward. The log's own final summary line —
`1092 failed, 40538 passed, 24 skipped, 9 warnings, 117 errors in
8831.59s (2:27:11)` — is independently confirmed present verbatim in the
durable copy, matching the predecessor phase's own report prose exactly.

## Original-sweep provenance limitation (canonicalized honestly)

**ORIGINAL SWEEP: AGGREGATE-ONLY HISTORICAL EVIDENCE.** 40587 passed /
979 failed / 117 errors. **EXACT EXECUTION SHA: UNRESOLVED.** **ORIGINAL
NODE INVENTORY: UNAVAILABLE.** **ORIGINAL RAW LOG: UNAVAILABLE.** No
newly discovered primary evidence in this phase establishes the original
sweep's exact commit, command, or node inventory beyond what the
predecessor phase already recorded (source-byte-equivalence of
`src/pcae`/`scripts`/`pyproject.toml`/`docs/contracts` across the
`[TEL_CHANGE(8bfce890) .. T_ENTRY(9b49d9a4)]` range). This phase does not
attempt to reconstruct it further — that reconstruction is confirmed
impossible from surviving evidence, and is not required to adjudicate
F-5 (per this phase's own governing rules).

## Later reproduction identity

The surviving `full_sweep_reproduction_at_head.log` is labeled **FULL-
SUITE REPRODUCTION AT T_ENTRY (`9b49d9a4`)**, single-process
(`python -m pytest -q -p no:cacheprovider`, no `-n`/xdist — confirmed by
the log's plain dot-progress format with no `[gw*]` worker prefixes),
result `1092 failed, 40538 passed, 24 skipped, 9 warnings, 117 errors in
8831.59s`. This is **explicitly a separate identified run**, not the
original sweep. It is **not substituted for** the original sweep
anywhere in this report.

## Count accounting (not falsely reconciled)

Original: 979 failed + 117 errors = **1096**. Later reproduction: 1092
failed + 117 errors = **1209**. Errors match exactly (117 = 117); failed
count is +113 in the reproduction. This delta is **not** mapped
node-by-node back to the original run — no evidence permits that mapping,
and none is invented here. The +113 is consistent with (and, per the
diagnosis below, at least partially attributable to) the cross-test
contamination class, whose exact node count is inherently order/
collection-sensitive across separate full-suite invocations.

## Fixture-state difference (conftest correction, canonicalized)

`tests/conftest.py` carries the Telegram-repair's autouse
`_isolate_notification_receipts_dir` fixture (setting
`PCAE_NOTIFICATION_RECEIPTS_DIR` for tests), added by `TEL_CHANGE`
(`8bfce890`), which predates the original sweep in real time but not
necessarily in the fixture state present during whatever invocation
produced the original 40587/979/117 tally. **Source-byte equivalence of
`src/pcae` alone does not imply full test-execution equivalence** between
a pre-Telegram-repair original run and this post-repair reproduction.
This correction is recorded as a canonical limitation on any claim of
exact original/reproduction equivalence; it does not by itself explain
the +113 delta (which is attributed to contamination, not conftest
state), and it changes no verdict.

## CAIR-triggered historical-guard corrections (independently reconfirmed)

`git show --stat 8407dd24` (the confirmed `CAIR_CHANGE` commit) touches
`src/pcae/core/hatp_class_b_topology_verifier.py` plus two test files —
independently reconfirming this phase's predecessor's claim that this is
a **legitimate later governed change**, not an unrelated regression.
`test_31_current_phase_changes_no_production_or_contract` and
`test_05_production_diff_is_exactly_the_two_authorized_files` (and, newly
observed in this phase's own targeted regression — see below — the
structurally identical guards inside
`test_..._1r_configured_agent_identity_threading_repair.py`) all share
the same anti-pattern this repository's own F-3/F-4/F-6/F-7/F-9 family
already names: comparing a fixed historical-phase's frozen file content
or `git diff <fixed-SHA> HEAD` against **current, moving** HEAD, which
necessarily breaks on every subsequent legitimate unrelated commit.
**Classification: HISTORICAL-MOVING-AUTHORITY DEFECT — CAIR-triggered
where applicable, current test-suite technical debt, not repaired here,
not blocking.** Not called "unrelated to CAIR" where CAIR is confirmed as
the trigger.

## RHAMP victim identification

- Module: `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
- Failing fixture: `rig` (`Rig.__init__`, line 180, calling
  `w.enroll_principal_via_pawa(...)`)
- Call chain: `hpac_protected_admin_writer.py:1095`
  (`enroll_principal_via_pawa`) → `store = HumanPrincipalRegistryStore(handle.authority)`
  → `human_principal_registry.py:260` (`HumanPrincipalRegistryStore.__init__`)
  → `self._authority = root if isinstance(root, HPACStoreAuthority) else HPACStoreAuthority.fixture(Path(root))`
- Exact recorded traceback (verbatim from the durable log, lines
  718-746): `isinstance(root, HPACStoreAuthority)` evaluates **`False`**
  even though `root`'s own repr is
  `<pcae.core.hpac_foundation.HPACStoreAuthority object at 0x1215b8460>`
  — i.e. an object that **is** an `HPACStoreAuthority` by its own
  `type().__module__`/`__qualname__` fails the `isinstance` check against
  the name `HPACStoreAuthority` imported at the top of
  `human_principal_registry.py`. The `else` branch then executes
  `HPACStoreAuthority.fixture(Path(root))`, and `Path(root)` raises
  `TypeError: expected str, bytes or os.PathLike object, not
  HPACStoreAuthority` (a real `pathlib` internals frame, not a mock).
  This is a **class-identity divergence**, not a logic bug in either
  production module.
- 79 of the 117 total sweep errors (68% of all errors) come from this one
  fixture chain in this one file — independently reconfirmed by directly
  grepping the durable log (`grep -c "ERROR
  tests/..._merged_rhamp_mechanism.py"` = 79).

## Victim-alone baseline (invocation #1, fresh process, D0)

`.venv/bin/python -m pytest -q -p no:cacheprovider
tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
→ **`125 passed in 2.82s`**. Confirms the module has no deterministic
defect of its own; independently re-verifies the predecessor's own claim.

## Candidate contaminator search and bounded compositions

Exhaustive grep across every file in `tests/` found **zero** instances of
`importlib.reload`, `sys.modules[...] = ...`, or `del sys.modules[...]`
touching `hpac_foundation`, `HPACStoreAuthority`, `human_principal_registry`,
or `hpac_protected_admin_writer` by name (37 files in the suite do
`importlib.reload`/mutate `sys.modules` at all, and each was individually
checked — all target unrelated `pcae.cltr_prototype`/`pcae.cltr.authority`
modules or use a private, cleaned-up `sys.modules` key that cannot leak,
per that test file's own documented hazard-avoidance comment). This rules
out the most direct "a test file deliberately reloads the victim's
dependency" mechanism as the trigger.

Two bounded candidate compositions were constructed and run to
completion (full detail, commands, and timings in the durable experiment
log):

1. **The 15 `importlib.reload`-using CLTR-authority test files (the only
   files in the entire suite that reload/mutate `sys.modules` at all) +
   the victim**, single process: **victim fully clean (0
   failures/errors)**. The 42 failures observed in this composition are
   an unrelated wheel/sdist packaging-artifact cluster, not the RHAMP
   signature. **Falsified.**
2. **The full 55-file "clean-in-isolation" thematic cluster** (every file
   the prior reconciliation identified as passing cleanly when run
   individually — including the victim and all its `.30R.3.*`/
   `.30R.4R.*`/`.30R.5R.*` RHAMP/PAWA/CLTR-adjacent siblings), run
   together without any of the other ~500 files in the suite:
   **`2148 passed, 1 skipped in 370.64s` — fully clean.** **Falsified**:
   the trigger is not contained within this thematic self-cluster; it
   requires some file(s) from elsewhere in the ~572-file prefix that
   precedes the victim alphabetically.
3. A third attempt — the full 571-file alphabetical prefix minus
   `slow`/`integration`/`phase_closure`-marked tests, to test whether
   excluding the suite's known-dominant slow/subprocess tests made
   full-prefix bisection tractable — was aborted after ~10-11 minutes
   having reached only ~7% collection/execution progress, with two
   unrelated failures observed and the victim not yet reached.
   Extrapolating the observed rate, completing this composition would
   require on the order of 2.5+ hours: **independently confirmed
   infeasible within any reasonable bounded diagnostic budget**,
   regardless of the incidental early termination.

No further falsifiable, budget-feasible hypothesis was available. Per
this phase's own governing rule ("if the budget expires without
identifying the trigger: CONTAMINATION ROOT CAUSE: UNRESOLVED... that is
a valid canonical result"), diagnostic experimentation was stopped here.

## Verdicts

**CONTAMINATION ROOT CAUSE: UNRESOLVED.** The exact trigger causing
`isinstance(root, HPACStoreAuthority)` to evaluate `False` against a live
`HPACStoreAuthority` instance was not identified. Two specific,
evidence-motivated candidate compositions were constructed and
definitively falsified; a third was shown infeasible to complete within
any bounded budget. The true trigger requires some subset of the
remaining ~500 files outside both tested clusters, in a combination not
identified in this phase.

**CONTAMINATION LOCATION: NOT ESTABLISHED.** Because the root cause is
unresolved, this phase cannot establish whether the mechanism is
test-harness-only or reachable through a supported production code path.
No evidence found in this phase suggests a production-reachable trigger
(no production entry point performs `importlib.reload`, dynamic
re-import, or `sys.modules` mutation of `hpac_foundation` or its
dependents — confirmed by source inspection of
`hpac_protected_admin_writer.py` and `human_principal_registry.py`, both
of which use ordinary module-top-level imports with no lazy/dynamic
re-import), but absence of a found production path is not proof of
absence of one, so this is recorded as **NOT ESTABLISHED**, not
**TEST-HARNESS ONLY**.

## Configured-agent-identity repair — regression re-check (§21)

Targeted current run of both configured-agent-identity threading repair
suites (fresh, D0, not the diagnosed contaminating composition):
`8 failed, 60 passed, 3 skipped` → after widening this phase's own task
allowed-file scope (which had been causing `pcae health` to report
unhealthy and fail one test that shells out to it — a self-inflicted,
phase-lifecycle-only cause, not a product defect) → `7 failed, 61 passed,
3 skipped`. The remaining 7: 5 are the same HISTORICAL-MOVING-AUTHORITY
pattern described above (CAIR-triggered, not a regression); 2 are
`PermissionError` reads of
`/Library/Application Support/PCAE/HPAC/protected-root/.authority/*.json`
— the expected fail-closed OS-permission behavior for an unprivileged
process reading protected-root files on this host, not a regression.
**No functional contradiction of `_current_agent_identity`,
`_effective_write_access`, ACL subject evaluation, or trusted-executable/
PATH-precedence semantics was found. CONFIGURED-AGENT-IDENTITY THREADING
REPAIR: INDEPENDENTLY VERIFIED — preserved, no contradiction found.**

## PAWA/PPA/RHAMP relevant-band re-check (§22)

The 55-file thematic cluster experiment above (`2148 passed, 1 skipped`)
independently covers essentially the entire RHAMP/PAWA/protected-
presentation/HATP/CLTR-authority relevant band and confirms it is fully
clean when run the way this repository's own governed phases have always
actually verified their work (targeted, not a raw full-repository
sweep) — reconfirming, with fresh current-state evidence, the
predecessor's own conclusion that these checks remain meaningful.

## hpac_verifier forged-object finding — independently adjudicated (§23)

Direct current-source inspection of `src/pcae/core/hpac_verifier.py`
(`is_verifier_authenticated_principal`, lines 335-360) confirms the
consumption check is:
`isinstance(candidate, AuthenticatedHumanPrincipal) and candidate in
_AUTHENTIC_PRINCIPAL_REGISTRY and candidate in
_AUTHENTIC_PRINCIPAL_CONTEXTS` — i.e. exact-object registry/context
membership (`set`/`dict` identity via `__eq__`/`__hash__` against objects
only ever inserted by a genuine prior `verify_human_authentication` call),
**not** a bare `isinstance`/field/equality shape check. Critically, this
also means the specific class-identity-divergence failure mode diagnosed
in this same phase (an `isinstance` check spuriously returning `False`
for a genuine object) is, for this specific consumption path,
**fail-closed by construction**: it could only cause a genuine principal
to be spuriously *rejected*, never a forged one to be spuriously
*accepted*. **Independently reconfirmed nonblocking** through the actual
Gate 5/`hpac_verifier` consumption semantics, not merely because the
test's own docstring calls the underlying construction-boundary gap
"expected."

## Public-reconciliation finding — reachability re-check (§24)

`test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`
(`tests/test_phase_reports.py`) concerns `phase_reports.py`'s
notification/checkpoint-receipt machinery. Direct source inspection of
`scripts/hpac_protected_presentation_admin.py` and
`scripts/hpac_protected_root_admin.py` (the only entry points for the
planned F-5 PPA-registration continuation) confirms **neither imports
nor references `phase_reports`/notification code in any way** (grep for
`phase_report`/`notif` in both scripts' imports: zero hits).
**Independently reconfirmed unreachable from the planned F-5
continuation path — nonblocking**, consistent with (and now confirmed
independently of) the predecessor's chronology-based classification.

## No production/existing-test/contract/dependency modification

`git diff --name-only D0 -- src/pcae scripts pyproject.toml
docs/contracts` = empty. `git diff --name-only D0 -- tests/` = empty (no
existing test file modified — the only test-adjacent change in this
phase is this phase's own new, additive fresh-verification file, listed
below). `git status --short` at phase end shows only: this phase's task
lifecycle files (`tasks/active/*`, `tasks/done/*`), this canonical
report, the `.pcae/evidence/*` durable-evidence copies + experiment log,
and the standard completion-metadata/`PROJECT_STATUS.md`/`CHANGELOG.md`
updates.

## No host mutation; no F-5 action

No `scripts/hpac_protected_root_admin.py provision` or
`scripts/hpac_protected_presentation_admin.py install` was run against
real protected state. No sudo, no descriptor write, no generation
change, no helper reinstall, no YubiKey/FIDO2/human-approval ceremony
requested or performed, no historical Telegram notification re-dispatch.
Generation-1 host state carried forward unchanged per the phase's own
instruction (not re-derived from privileged live inspection — consistent
with, and no contradiction found for, the prior recorded state: protected
root PRESENT, generation 1, configured agent `atilamadai`/uid 501, helper
PRESENT SHA-256
`933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`, PPA
presentation/current-generation ABSENT).

## Runtime / no-first-effect

`pcae runtime inspect`: `not_implemented` / `Observed` / execution
`unavailable`, 0 plugins, 0 capabilities — unchanged throughout this
phase. No `adapter.dispatch`, `DispatchEnvelope`, plugin activation, or
capability elevation occurred. **FIRST GOVERNED RUNTIME EXTERNAL EFFECT:
ABSENT / UNREACHABLE.**

## Fresh phase-specific verification

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_contamination_diagnosis_iv.py`
covers, additively (no existing test modified): phase-ID/CPIPC lineage;
D0; evidence-manifest hash integrity (re-derives and compares the SHA-256
of all four durable `.pcae/evidence/` copies against the values recorded
in this report); the victim-alone-baseline claim; that the two candidate
compositions are recorded as falsified and the third as infeasible in the
durable experiment log; that the diagnosis, location, readiness, and hold
verdicts in this report are exactly the required closed vocabulary; that
`git diff` from D0 touches no `src/pcae`/`scripts`/`pyproject.toml`/
`docs/contracts`/existing test file; that no host-mutating admin script
was invoked; that runtime remains `not_implemented`/`Observed`/
`unavailable` with 0 plugins/capabilities; and that N-16-5 remains
recorded NOT CLOSED with N-16-6/N-16-7 untouched.

## Final readiness/hold verdict

**CONTAMINATION ROOT CAUSE: UNRESOLVED.**

**CONTAMINATION LOCATION: NOT ESTABLISHED.**

**CURRENT F-5 READINESS: NOT YET ESTABLISHED.**

**F-5 EXECUTION HOLD: REMAINS.**

Reason (named exactly, per this phase's own clearance rule): clearance
criterion 1 ("contamination root cause is causally identified") is not
met. This is true regardless of how clean every other relevant check
came back in this phase (configured-agent, PAWA/PPA/RHAMP relevant band,
`hpac_verifier`, public-reconciliation, CAIR-guard classification, no
production/host/contract change) — an unresolved class-identity-
contamination mechanism of unknown scope is sufficient on its own to keep
the hold in place, per this phase's own §29/§30 rules. This does **not**
rewrite the predecessor's own historical "F-5 CONTINUATION HOLD: CLEARED"
verdict, which remains historical evidence of what was concluded at that
earlier time; it records this phase's own, later, re-adjudication as
required by the operator's newer instruction.

**N-16-5: NOT CLOSED.** N-16-6/N-16-7 remain open/untouched/unbegun.

## Recommended (not begun) successor

The narrowest evidence-supported successor is a **dedicated, further-
bounded RHAMP cross-test contamination bisection phase**, scoped
narrowly to: (a) construct and test 2-4 additional candidate compositions
drawn from the ~500 files not covered by either composition tested here
(the CLTR-authority-reload cluster and the 55-file RHAMP/PAWA thematic
cluster are both now ruled out), informed by collection-order and
global-registry-mutation analysis rather than blind full-prefix
bisection (which this phase independently confirmed infeasible within
any reasonable single-phase budget); or (b) if root cause remains
unresolved after that additional bounded attempt, an explicit operator
decision on whether to accept a narrower, evidence-based argument that
the specific unresolved mechanism cannot affect any F-5/N-16-5-relevant
check (which this phase does not attempt, per its own instruction not to
force a clearance verdict). **Not begun here.**

## Governance

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved —
this phase's finalization, commit, and push were performed solely by the
primary human-authorized operator's session.
