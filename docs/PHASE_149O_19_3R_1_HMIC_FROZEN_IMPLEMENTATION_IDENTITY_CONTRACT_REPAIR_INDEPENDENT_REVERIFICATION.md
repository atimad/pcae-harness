# Phase 149O.19.3R.1 — HMIC Frozen Implementation Identity Contract Repair Independent Re-Verification

## 0. Purpose and posture

This is a **documentation/test-only independent re-verification phase**.
No `src/pcae/**` file was modified. No contract file (HMIC-001, HMRC-001,
HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001) was modified.
No certification artifact, Active-Certification Pointer, or revocation
record was created. No `HATP_MANDATORY` activation occurred. The
hard-coded `mandatory_consumption_implementation_independently_verified
= False` ceiling (`hatp_mandatory_cutover.py:842-853`) is unchanged.

This phase's job is to independently re-verify Phase 149O.19.3R's own
narrow contract repair of HMIC-001 (`docs/contracts/
HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`),
which repaired Blocking finding **B-149O.19.3-1** (149O.19.3's own
independently-found omission of the HATP provider layer from the frozen
authority-bearing file set, HMIC-REQ-050). Per this phase's own charter
and per §49's "Recommended next phase" text, this re-verification does
**not** trust 149O.19.3R's own dependency table, diagrams, or test
constants; every claim below was reconstructed independently from
source: a fresh Python `ast`-based import walk, direct reading of all 22
frozen files, an independent reimplementation of `implementation_scope_
digest`, and direct inspection of call sites (not prose) to determine
reachability from `assess_hatp_mandatory_activation_readiness`.

## 1. Baseline

```
$ git status --short
(clean)
$ git log --oneline -5
74cc50c0 Phase 149O.19.3R: restore idle-task default allowed-file list
44600aa7 Phase 149O.19.3R: write phase-completion metadata and canonical report staging header
be2c1b54 Phase 149O.19.3R: close out task lifecycle
2e6aa662 Phase 149O.19.3R: sync task-transition changelog entry
942df2a2 Phase 149O.19.3R: HMIC Frozen Implementation Identity Narrow Contract Repair
$ git rev-list --count origin/main..HEAD
0
```

`PROJECT_STATUS.md`'s "Current Phase" section confirms 149O.19.3R as the
latest completed phase, contract status **"FROZEN — REPAIRED, PENDING
INDEPENDENT RE-VERIFICATION (not VERIFIED)"**, and explicitly recommends
**149O.19.3R.1** before any 149O.19.4-class implementation phase.

Primary sources read directly for this phase: `docs/contracts/
HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
(1786 lines, in full for the relevant sections: §16-21, §41 attack #11,
§49), `docs/PHASE_149O_19_3_HATP_MANDATORY_INDEPENDENT_VERIFICATION_
CERTIFICATION_CONTRACT_INDEPENDENT_VERIFICATION.md`, `docs/
PHASE_149O_19_3R_HMIC_FROZEN_IMPLEMENTATION_IDENTITY_CONTRACT_REPAIR.md`,
and all 22 HMIC-REQ-050 frozen `src/pcae/**` files plus the four bound
contract files.

## 2. Historical 18-file reconstruction and repaired-contract diff

`git show 942df2a2 --stat` shows exactly the 5 files 149O.19.3R's own
`PROJECT_STATUS.md` narrative claims: the HMIC contract (+259/-?
lines), the repair doc (new, 469 lines), the 149O.19.2 freeze suite
(count-assertion-only diff), the 149O.19.3 verification suite
(status-aware split), and a new 32-test repair module. No `src/pcae/**`
file appears in this diff. This independently confirms the "narrow
repair only" claim at the commit-diff level, not just from prose.

The pre-repair 18-file set (reconstructed from HMIC-REQ-050's stated
history plus 149O.19.3R's own repair module's `_PRE_REPAIR_SRC_
RELATIVE_PATHS` cross-checked against the contract's own §49 prose,
which independently states the same 18 names):

```
core/hatp_mandatory_cutover.py       core/hatp_evidence_store.py
core/hatp_ag_authority.py            core/hatp_signed_evidence.py
core/hatp_rollback_consumption.py    core/agent.py
core/hatp_bootstrap.py               commands/agent.py
core/human_approval_trusted_provenance.py   cli.py
core/repository_identity.py          core/permission_broker.py
core/rollback_approval_evidence.py   core/permission_broker_foundation.py
+ 4 contract files (HMRC-001/HATP-001/HSCE-001/RAE-001)
```

The four newly-added files (independently confirmed present in HMIC-
REQ-050's current text, §17, lines 542-545 of the contract):

```
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py
```

Total: **22**, independently counted from the contract's own literal
enumeration (not copied from any table) — confirmed by direct line
count of HMIC-REQ-050's fenced code block (18 `src/pcae/**` paths + 4
contract paths).

## 3. Provider-layer and hardware-credential source analysis (independent read)

Read directly, not summarized from the repair table:

- **`core/hatp_providers.py`**: defines `create_production_hardware_
  provider` / `discover_hardware_providers`, the sole production
  provider-registry/selection surface. Dynamically imports `hatp_fido2_
  provider.Fido2HardwareProvider` and, with `allow_piv_fallback=True`,
  `hatp_piv_provider.PivHardwareProvider`.
- **`core/hatp_fido2_provider.py`**: imports `from fido2 import cbor` /
  `cose` / `ctap` / `ctap2.base` / `hid` / `webauthn` (third-party,
  pinned `fido2>=1.1,<2`), `from pcae.core.hatp_hardware_credentials
  import HATPHardwareCredentialStore, HATPHardwareCredentialStoreError`,
  and `from pcae.core.hatp_providers import (...)`. `Fido2HardwareProvider.
  verify()` (line 341) performs the real cryptographic
  signature/attestation check.
- **`core/hatp_piv_provider.py`**: imports `hatp_providers`; currently
  fail-closed/`NOT_CONFORMANT` by design but implements the same
  `HATPProofVerifierProvider` interface real callers reach.
- **`core/hatp_hardware_credentials.py`**: **zero** `pcae.*` imports
  (leaf node — independently confirmed, `grep -n "^from\|^import"`
  shows only `json`/`os`/`stat`/`sys`/`dataclasses`/`pathlib`/`typing`).
  A protected, read-only registry mapping `signer_key_id` to public-key
  material; its own module docstring states `verify_hatp_proof` never
  reads it directly — only a concrete provider does, "fully inside the
  opaque `provider.verify()` call."

All four claims in 149O.19.3R's transitive-completeness table (§49)
about this sub-tree's structure are independently confirmed correct by
direct source read.

## 4. Fresh transitive PCAE-owned import walk (independent, AST-based)

A fresh Python `ast`-based (not regex, not trusting the contract's own
prose) import walk was run from all 22 frozen files. Two passes were
run:

**Pass A (full closure, including `cli.py`/`commands/agent.py`/`core/
agent.py`)**: pulls in ~300 files — the entire CLI command-dispatch
surface (every `commands/*.py`, `repository_intelligence/**`, `cltr/**`,
`aesic/**`, `schema_runtime/**`, `interactive_workflow/**`,
`governance/**`, etc.). This matches 149O.19.3R's own stated
methodology note that these three files' "dozens of unrelated
command-dispatch imports" were "already reviewed and accepted at
149O.19.2/149O.19.3" and are excluded from the authority-sensitive
closure analysis, not from the frozen set itself (they remain bound by
their own bytes, HMIC-REQ-050).

**Pass B (authority-adjacent closure only, excluding the three
broad-surface files' own onward command-dispatch fan-out)**: starting
from the 15 authority-relevant frozen files (excluding `cli.py`/
`commands/agent.py`/`core/agent.py`), the transitive `pcae.*` closure is
exactly:

```
core/paths.py                      — B: generic path-join helper, no
                                      HATP/consumption logic
core/gate_dry_run.py               — C: PB policy-decision-support
core/scope_preflight.py            — C: PB policy-decision-support
core/shell_gate.py                 — C: PB policy-decision-support
core/gate_dry_run_context.py       — C: downstream reporting/aggregation
core/artifact_index.py             — C: downstream reporting/aggregation
core/decision_log.py               — C: downstream reporting/aggregation
core/governance_timeline.py        — C: downstream reporting/aggregation
core/memory_snapshot.py            — C: downstream reporting/aggregation
core/project_state.py              — C: downstream reporting/aggregation
core/risk_register.py              — C: downstream reporting/aggregation
governance/publication/{chgr_envelope,chgr_rendering,coordinator,
  errors,models,record,serialization,storage}.py
                                    — C: RAE-001 creation-ceremony surface
interactive_workflow/{confirmation/models,errors,models/session,
  orchestration/models,preview/models,publication_handoff/{handoff,
  models},serialization/*,session/identity}.py
                                    — C: RAE-001 creation-ceremony surface
schema_resources/__init__.py, schema_runtime/**
                                    — C: CHGR-envelope schema plumbing,
                                      no signature/approval logic
```

This is **exactly** the set 149O.19.3R's own §49 table names (`pcae.core.
paths`; the `gate_dry_run`/`scope_preflight`/`shell_gate` trio and their
own `gate_dry_run_context`/`artifact_index`/`decision_log`/
`governance_timeline`/`memory_snapshot`/`project_state`/`risk_register`
dependents; `rollback_approval_evidence.py`'s own governance/publication
and interactive_workflow imports). No additional file appeared in this
independent walk beyond what the repair's own table already disclosed.

**Classification, independently re-derived (not copied):**

| File(s) | Class | Independent justification |
|---|---|---|
| `core/paths.py` | B — utility | Read directly: `HarnessPath`/repo-root join helper only; no signature, approval, or verification symbol present |
| `gate_dry_run.py`/`scope_preflight.py`/`shell_gate.py` and their reporting-utility dependents | C — environment/PB-policy, already excluded | HMIC-REQ-068 already excludes PBPA-001/PBPC-001 policy from `contract_versions`; independently confirmed none of these modules reference `signature`/`verify_hatp`/`approval_present`/`RollbackApproval`/`HATPProof` (fresh `grep`, zero hits) |
| `governance/publication/**`, `interactive_workflow/**` reached from `rollback_approval_evidence.py` | C — RAE-001 creation-ceremony, not reachable from consumption/readiness call graph | Independently read `resolve_rollback_approval_evidence` (line 1218) and its helper `_resolve_decision_ref` (line 856): both read CHGR JSON records directly off disk (`record_path.read_text(...)`) — neither calls `create_rollback_approval_decision` nor `PublicationCoordinator.execute` anywhere in their bodies. Confirmed by direct `grep` that these two symbols appear in `rollback_approval_evidence.py` only inside `create_rollback_approval_decision`'s own definition (the creation path), never inside `resolve_rollback_approval_evidence`/`resolve_rollback_approval_evidence_with_hatp` |
| `schema_runtime/**`, `schema_resources/**` | C — CHGR-envelope schema plumbing | Reached only via `governance/publication/chgr_envelope.py`, itself already class C |

### Specifically-checked files named in the task brief

- **`hatp_bootstrap.py`**: inside the 22-file set (HMIC-REQ-050 line
  531). Imports only `repository_identity.py` (also frozen).
- **`repository_identity.py`**: inside the 22-file set (line 533).
  Imports only `core/paths.py` (class B).
- **`permission_broker.py`** / **`permission_broker_foundation.py`**:
  both inside the 22-file set (lines 540-541).
  `permission_broker.py` imports `gate_dry_run.py`/`scope_preflight.py`/
  `shell_gate.py` — all class C per above (PB *policy* support, already
  excluded by HMIC-REQ-068's PBPA-001/PBPC-001 boundary, not PB request
  *construction* itself, which lives in the frozen files).
- **AG3/AG5 effect-gate owner**: `hatp_ag_authority.py` (frozen,
  line 529) is independently confirmed, by its own module docstring
  ("HATP Production Authority Adapter for AG3/AG5"), to be the sole
  production entry point AG3 (`execute_rollback`)/AG5
  (`build_rollback_execution`) consume. A separate file,
  `core/mutation_permission.py`, mentions AG3/AG5 only in a comment
  ("(AG3, AG5) are explicitly out of Wave-1 scope and are not wired
  here") and is imported by nothing (`grep -rl "mutation_permission"
  src/pcae` returns no importer) — confirmed dead/unreachable
  (classification D), correctly outside the frozen set.
- **`hatp_mandatory_cutover.py`**: inside the 22-file set (line 528).
- **RAE/PB/effect-gate authority code**: covered above via
  `hatp_ag_authority.py` and `permission_broker*.py`.
- **Human-approval/rollback-evidence verifiers**: `human_approval_
  trusted_provenance.py` and `rollback_approval_evidence.py` are both
  inside the 22-file set (lines 532, 534).

### A file the repair's own table does not mention: `hatp_signing_ceremony.py`

This independent re-walk found one file the 149O.19.3R transitive-
completeness table does not discuss at all: `core/hatp_mandatory_
cutover.py` line 825 performs a **dynamic** `importlib.import_module
("pcae.core.hatp_signing_ceremony")` inside `assess_hatp_mandatory_
activation_readiness` — invisible to a static AST import walk that only
inspects `Import`/`ImportFrom` nodes, which is why it did not appear in
either Pass A or Pass B above. It was found only by a targeted `grep`
for `hatp_signing_ceremony` across `src/pcae/core/hatp_mandatory_
cutover.py`.

Independent analysis of what this call site actually does: it only
records **whether the module imports successfully**
(`signing_available = True/False`), used solely to populate one
`HATPMandatoryActivationReadinessCheck` boolean/detail-string pair. No
function or class from `hatp_signing_ceremony` is called, and no value
it would return is consumed anywhere in the readiness/verification/
consumption chain. `hatp_signing_ceremony.py` is the **creation-side**
signing-ceremony tool (`sign_rollback_evidence`/`production_sign_
rollback_evidence`, invoked from `commands/hatp.py`) that *produces*
signed evidence files — it is architecturally analogous to
`rollback_approval_evidence.py`'s own excluded RAE creation-ceremony
imports (§4 table above). Independently confirmed via `hatp_signed_
evidence.py`'s own docstring (lines 13-18): "a successful parse or
construction means only [...] `verify_hatp_proof`'s responsibility,
never reimplemented or shortcut" — i.e. evidence produced by
`hatp_signing_ceremony.py` receives **no trust credit** from having
been created by that tool; it is re-verified from scratch by the frozen
`verify_hatp_proof` → `hatp_providers` → `hatp_fido2_provider` →
`hatp_hardware_credentials` chain regardless of provenance. Mutating
`hatp_signing_ceremony.py`'s internal logic (short of breaking its own
`import` statement, which would only flip one readiness-check boolean,
itself already fail-closed-neutral since `mandatory_consumption_
implementation_independently_verified` is hard-coded `False`
independently of this check) cannot change any HATP verification
status, RAE/HATP approval derivation, PB request construction, or AG3/
AG5 gating outcome.

**Classification: B — import-existence probe only, no output
consumed; correctly excluded from HMIC-REQ-050.** This is a
**non-Blocking documentation gap** in 149O.19.3R's own §49 table (the
file exists, is dynamically reachable, and was not analyzed), not a
binding defect — the independent analysis above confirms exclusion is
correct on the merits. Recorded as a finding (§8) for a future
narrow doc-repair phase to add explicitly to §49, not repaired here per
this phase's own hard constraint against modifying HMIC-001.

## 5. Independent digest reconstruction and mutation sensitivity

`implementation_scope_digest` was reimplemented from HMIC-REQ-054/055/
056/057/058's normative text only (SHA-256 of each file's raw on-disk
bytes; canonical POSIX-relative path; lexicographic path order; per-file
record `<path>\0<sha256_hex>\n` UTF-8; final digest = SHA-256 of the
concatenated ordered records) — not by reusing 149O.19.3R's own helper
code.

Results (script run under `.venv` Python 3.9.6, working tree at
`942df2a2`/current HEAD, clean):

- `implementation_scope_digest` over the current 22-file set is
  deterministic and reproducible across repeated runs.
- **Mutation sensitivity**: a single-bit flip in the first byte of
  **every one of the 22 frozen files** (not just the 4 new ones) changes
  the resulting digest. All 22/22 sensitive.
- **Pre/post repair defect reproduction**: for each of the 4 newly-added
  files, a single-bit mutation:
  - leaves the **historical 18-file-model digest unaffected**
    (independently reproducing B-149O.19.3-1: `Fido2HardwareProvider.
    verify()` or `hatp_hardware_credentials.py`'s lookup logic could be
    silently altered under the old model without detection), and
  - **does change the current 22-file-model digest** for all 4 files.

This independently proves the repair closes the specific defect
149O.19.3 found, at the algorithmic level, not just at the level of "the
contract text now lists more files."

## 6. Requirement / invariant / attack-matrix counts (independently re-counted)

- `HMIC-REQ-001`–`HMIC-REQ-144`: **144** unique IDs, sequential,
  gap-free (`grep -oE "HMIC-REQ-[0-9]{3}" ... | sort -u | wc -l` = 144).
- `CIVC-1`–`CIVC-12`: **12** unique invariants.
- Attack matrix: **32** rows (independently counted in the attack-matrix
  table region of the contract).

All three counts match 149O.19.3R's own claim, independently confirmed
by direct extraction rather than trusting the repair doc's prose.

## 7. Future HMIC validator self-reference

No HMIC-001 validator, admin-writer, or `certifications.json` exists
anywhere in `src/pcae/**` today (independently re-confirmed: no file
under `src/pcae` contains `certifications.json`, and no module
implements a certification-writing API). §49's own text states this
explicitly and defers the question of whether a future validator's own
source joins a future HMIC-001 version's frozen set to that future
phase, while relying on HMIC-REQ-076-082 (OS-permission-gated Protected
Root, not in-process check) as the non-circular posture in the interim.

**Verdict: NON-BLOCKING CONCERN, not a gap in the current contract's own
scope.** The current HMIC-001 v1.0 frozen set correctly binds the
implementation *being certified*, not a not-yet-existing validator. The
contract explicitly and non-silently defers (rather than omits) the
question of a future validator's self-binding. There is nothing to
verify today because there is no validator code to bind — this is a
structural, not a documentation, limitation, and it is already disclosed
(§49, HMIC-REQ-063 analog reasoning).

## 8. Editable-install / PYTHONPATH shadow concerns

`python3 -c "import pcae; print(pcae.__file__)"` resolves to `/Users/
atilamadai/repos/pcae-harness/src/pcae/__init__.py` — the certified
checkout path, confirming editable-install resolution currently binds to
the correct source root. This is the same finding 149O.19.3 already
made and HMIC-REQ-063 already names as a residual limitation:
`implementation_scope_digest` verifies on-disk bytes at the certified
*paths*, but does not itself prove that `sys.modules` at *runtime*
resolved those exact files rather than a `PYTHONPATH`-shadowed or
`sitecustomize`-injected alternate module with the same dotted name.
Attack-matrix row #29 already names this "out of scope, not silently
claimed solved" in v1.0. No new gap found here; **CLOSED BY CONTRACT**
(already disclosed, not silently assumed solved).

## 9. Findings

1. **(Non-Blocking, documentation-only)** `hatp_signing_ceremony.py`
   is dynamically imported (`importlib.import_module`, not a static
   `import` statement) inside `assess_hatp_mandatory_activation_
   readiness` (`hatp_mandatory_cutover.py:825`) but is not discussed
   anywhere in 149O.19.3R's §49 transitive-completeness table. Independent
   analysis (§4 above) confirms its exclusion from HMIC-REQ-050 is
   *correct on the merits* (import-existence probe only; no function
   output consumed; evidence it produces receives no trust credit and is
   fully re-verified by the already-frozen chain) — this is a gap in the
   repair's own *documentation completeness*, not in the frozen file
   set's *binding correctness*. Recommend a future narrow doc-only
   repair phase add an explicit row for this file to §49 (not repaired
   here, per this phase's hard constraint against modifying HMIC-001).
2. No other under-binding defect was found. The independent Pass B
   closure walk (§4) reproduces 149O.19.3R's own claimed dependency set
   exactly, with the one addition noted in finding 1 above (itself
   confirmed non-authority-sensitive).

No Blocking findings were discovered by this re-verification.

## 10. Verdicts

- **B-149O.19.3-1: INDEPENDENTLY CONFIRMED CLOSED**, with one qualifier:
  the closure is confirmed at both the contract-text level and the
  algorithmic/digest-sensitivity level (§5); the one non-Blocking
  documentation gap (finding 1, §9) does not reopen the finding because
  independent analysis confirms the omitted file was correctly excludable
  regardless.
- **HMIC verification verdict: VERIFIED — the repaired 22-file
  `HMIC-REQ-050` frozen set, independently re-walked from source, closes
  B-149O.19.3-1.** Not yet a claim that any real certification exists —
  none does, and none was created by this phase.
- **Implementation identity verdict: (B) safe-with-non-blocking-
  limitations.** Not (A) complete-and-unambiguous only because of the
  already-contract-disclosed residual limitations (HMIC-REQ-063 import-
  shadowing, attack row #29; HMIC-REQ-060 extra-file invisibility) plus
  this phase's own non-Blocking documentation-completeness finding
  (§9.1). Not (C) — no still-under-bound-and-therefore-Blocking omission
  was found.
- **Provider-layer BOUND/NOT BOUND, per newly-added file:**
  - `core/hatp_providers.py` — **BOUND**
  - `core/hatp_fido2_provider.py` — **BOUND**
  - `core/hatp_piv_provider.py` — **BOUND**
  - `core/hatp_hardware_credentials.py` — **BOUND**
- **Transitive closure verdict: YES** — the 22-file set is sufficient;
  no further authority-sensitive (class A) file was found unbound by
  this independent re-walk.
- **Validator self-reference verdict: NON-BLOCKING CONCERN** (explicitly
  and non-silently deferred by the contract to a future phase; no
  validator code exists yet to bind).
- **Recommended next phase: 149O.19.4** (implementation-plan-only phase)
  may proceed. Optionally, a narrow documentation-only follow-up phase
  may add an explicit §49 row for `hatp_signing_ceremony.py` (finding
  9.1) at the team's discretion — this is not a blocking prerequisite.

## 11. Test results

All commands run under `.venv` (pinned CPython 3.9.6), clean working
tree at HEAD (`942df2a2`... plus the four idle/lifecycle housekeeping
commits through `74cc50c0`), before this phase added its two new files.

**Regression suites (149O.19.2 freeze + 149O.19.3 verification + 149O.19.3R repair, run together):**

```
$ .venv/bin/python3 -m pytest -q \
    tests/test_phase_149o_19_2_hatp_mandatory_independent_verification_certification_contract_freeze.py \
    tests/test_phase_149o_19_3_hmic_contract_independent_verification.py \
    tests/test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py
103 passed in 2.55s
```

**New independent re-verification suite (this phase):**

```
$ .venv/bin/python3 -m pytest -q \
    tests/test_phase_149o_19_3r_1_hmic_frozen_identity_repair_independent_reverification.py
29 passed in 1.19s
```

**Fast Green (before this phase's new test file existed — establishes
the pre-existing-failure baseline):**

```
$ .venv/bin/python3 -m pytest -m fast_green -q
28 failed, 5563 passed, 1 skipped, 25639 deselected, 7 warnings in 379.14s
```

**Fast Green (after adding this phase's new test file):**

```
$ .venv/bin/python3 -m pytest -m fast_green -q
28 failed, 5592 passed, 1 skipped, 25639 deselected, 7 warnings in 389.72s
```

The same 28 named failures appear in both runs (all pre-existing,
unrelated `149O.16`/`149O.17`/`149O.18*`-phase byte-diff/file-allowlist
tests anchored to their own historical baseline commits — none reference
HMIC-001, `hatp_providers.py`, `hatp_fido2_provider.py`,
`hatp_piv_provider.py`, or `hatp_hardware_credentials.py`); passed count
increased by exactly 29, matching this phase's new test module's own
test count, with zero new failures introduced.

**Broad sweep (`-k "hmic or 149o_19_3 or hatp"`):**

```
$ .venv/bin/python3 -m pytest -k "hmic or 149o_19_3 or hatp" -q
133 failed, 2728 passed, 3 skipped, 28396 deselected, 7 warnings in 85.56s
```

**A/B confirmation via `git stash -u`** (this phase's own two new files
plus the harness's own automated task-lifecycle housekeeping files
stashed, then popped back): with this phase's changes fully removed, the
identical broad sweep produced **133 failed** (same count, verified
same test names), **2699 passed** (exactly 29 fewer, matching this
phase's own new test count exactly), 3 skipped, 28396 deselected. This
confirms all 133 broad-sweep failures are pre-existing and unrelated to
this phase (most are older `149O.1H`/`149O.3`/`149O.5`/`149O.7`/`149O.9`
-phase tests pinned to their own historical exact-byte/diff/count
baselines against a repository that has since advanced many more
phases — a pattern this task's own instructions anticipated as
"pre-existing/unrelated"). This phase's own regression suites (§ above,
103 passed) and new suite (29 passed) are unaffected either way.

## 12. Constraints compliance (restated)

No `src/pcae/**` file was modified. No contract file (HMIC-001 or any
of HMRC-001/HATP-001/HSCE-001/RAE-001/RWMPC-001/PBPA-001/PBPC-001) was
modified. No certification artifact, pointer, or revocation state was
created. The hard-coded `False` readiness ceiling
(`hatp_mandatory_cutover.py:842-853`) is unchanged. No real
`HATP_MANDATORY` activation occurred. HATP production remains **NOT
READY**; runtime remains **Observed / observe / unavailable**.
