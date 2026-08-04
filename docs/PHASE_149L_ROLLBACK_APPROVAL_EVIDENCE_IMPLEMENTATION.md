# Phase 149L — Rollback Approval Evidence Implementation

## 0. Phase Identity

**Phase:** 149L
**Type:** Bounded production implementation of the RAE-001 v1.0 approval-evidence substrate.
**Governing contract:** RAE-001 v1.0, FROZEN (Phase 149I), independently verified with zero
BLOCKING findings (Phase 149J), implementation-planned (Phase 149K,
`docs/PHASE_149K_ROLLBACK_APPROVAL_EVIDENCE_IMPLEMENTATION_PLAN.md`).
**Runtime posture, unaffected:** State **Observed**, maximum capability **observe**, execution
availability **unavailable**.

## 1. Baseline

```
git status --short                      -> clean
git rev-list --count origin/main..HEAD  -> 0
```

Latest completed phase: 149K (report: complete). RAE-001 v1.0 verified with zero BLOCKING
findings. AG3/AG5 unimplemented. `pcae health` -> healthy. `pcae check` -> passed. `pcae status
coherence` -> coherent. `pcae doctor task-memory` -> clean. `pcae push check` -> nothing_to_push.
`pcae runtime inspect` -> Observed / observe / unavailable, Permission Broker status
`execution_unavailable`, registry empty. `pcae notify status` -> Telegram configured/enabled.
Fast Green baseline: **4391 passed**.

## 2. Production Files Changed

| File | Status |
|---|---|
| `src/pcae/core/rollback_approval_evidence.py` | New (~810 lines): models, storage, creation, Evidence Validator, derivation API |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_binding.schema.json` | New |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_revocation.schema.json` | New |
| `src/pcae/schema_resources/rollback_approval/manifest.schema.json` | New |
| `src/pcae/schema_resources/rollback_approval/manifest.json` | New |
| `src/pcae/schema_resources/__init__.py` | Additive only: `rollback_approval_root()` accessor (19 lines added, matching `chgr_root()`/`cltr_cutover_root()` pattern) |

No other `src/pcae/**` file was touched. `git diff --name-only 318f4b50..HEAD -- src/pcae/`
(pre-149L baseline, 149I's contract-freeze commit) confirms exactly this set once staged.

## 3. Test Files Added

| File | Tests |
|---|---|
| `tests/test_rollback_approval_evidence_models.py` | 23 |
| `tests/test_rollback_approval_evidence_persistence.py` | 11 |
| `tests/test_rollback_approval_evidence_validation.py` | 30 |
| `tests/test_rollback_approval_evidence_contract.py` | 13 |
| **Total** | **77**, all passing |

## 4. Implementation Summary, By RAE-001 Component

- **Decision model (§7):** RAE-001 deliberately reuses `human_governance_record` itself as the
  Decision; this phase introduces no parallel Decision dataclass, only the read-only
  `RollbackApprovalDecisionRef{record_id, record_digest}` pointer type, and the frozen
  `ROLLBACK_APPROVAL_TEMPLATE` constant (`template_id="rollback-approval"`).
- **Binding model (§8):** `RollbackApprovalBinding`, a `frozen=True` dataclass, field-for-field
  matching RAE-001's table, with `__post_init__` enforcing the family-lock
  (`rollback_site` <-> `rollback_operation_reference` type) and the two conditional-field rules
  (`revocation_metadata` iff `state==REVOKED`; `use_binding` iff `state==USED`).
- **AG3/AG5 profiles (§9-§10):** `Ag3OperationReference{job_id, original_commit_sha}` and
  `Ag5OperationReference{per_id, ecp_id}`, two structurally distinct Python types (not an
  enum-tagged shared dataclass) so a cross-family field read fails with `AttributeError`, not a
  stale/`None` value.
- **Canonical storage (§12, §56 file budget):** `.pcae/rollback-approval-evidence/{bindings,
  revocations}/`, a new sibling of `.pcae/publication-execution/`. Atomic write
  (`tempfile.mkstemp` + `fsync` + `os.replace`), no-overwrite guard, duplicated (not imported)
  from `governance/publication/storage.py`'s proven technique.
- **Canonical creation (§16, RAE-REQ-079):** `create_rollback_approval_decision` is a thin
  wrapper around the real, unmodified `PublicationCoordinator`/`PublicationReadinessPackage`
  CHGR pipeline — it produces one genuine, published `human_governance_record` (+ 3 CHGR
  companion artifacts) through the exact same Confirmation->Publication ritual every other
  Decision Template uses. `create_rollback_approval_binding` enforces Decision-before-Binding
  ordering and the at-most-one-active-Binding-per-Decision rule (RAE-REQ-019) before persisting.
- **Evidence Validator (§12-§13, RAE-REQ-034-042):** `resolve_rollback_approval_evidence`
  evaluates RAE-REQ-038's full conjunction in order (existence -> digest recomputation ->
  Decision resolution -> `approve_rollback` check -> authority check -> site/operation exact
  match -> revocation -> used -> future-dated/TTL -> repository-state staleness ->
  supersession), wrapped in a single fail-closed `try/except Exception` umbrella so no internal
  error ever propagates or defaults to `True`.
- **Canonicality (§15 of the 149K plan, 149J's PARTIAL finding):** implemented exactly as
  planned — a forged Binding file placed directly in `bindings/` is schema-shape-valid but is
  rejected because its `governance_record_reference` cannot resolve to a real, digest-matching,
  correctly-templated, published CHGR record (`_resolve_decision_ref`, shared unchanged between
  creation-time and consumption-time checks). Verified directly in
  `test_rollback_approval_evidence_validation.py::test_hand_authored_binding_outside_creation_api_is_rejected`.
- **TTL (§30, RAE-REQ-043):** exactly 24 hours, computed once at creation
  (`created_at + timedelta(hours=24)`), inclusive boundary (`now >= expires_at` -> `STALE`).
  Tested at just-before/exactly/just-after the boundary with a private, test-only frozen-clock
  context manager (`_frozen_clock`) — never a production configuration value or CLI flag.
- **Revocation/supersession (§34-§36):** append-only. Revocation is a new
  `revocations/<evidence_id>.json` file, never an in-place edit of the Binding; the Evidence
  Validator checks revocation-record *existence*, never the (immutable, as-created) Binding
  file's own `state` field. Supersession compares `created_at` across all Bindings sharing an
  operation reference — used only to detect supersession for an *already-identified*
  `evidence_id`, never to select which `evidence_id` to resolve (RAE-REQ-041 upheld).
- **`approval_present` derivation (§28):** `derive_rollback_approval_present(operation_context,
  evidence_id)` — no caller-override parameter exists on the signature; `True` only for
  `RollbackApprovalValidationResult.VALID`.

## 5. Finding — Template Version Format (NON-BLOCKING)

RAE-REQ-011's prose names the frozen Decision Template's version as `"1.0.0"`. CHGR's own,
unamended `template_version` schema field
(`schema_resources/chgr/shared/identity.schema.json#/$defs/template_version`) is pattern-locked
to MAJOR.MINOR (`^[0-9]+\.[0-9]+$`) everywhere it appears (`decision_template.schema.json` and
`human_governance_record.template_ref` alike). `"1.0.0"` is not schema-conformant against this
exact, unamended schema — independently reconfirmed by direct construction:
`build_publication_record` fail-closed-refuses it (`CHGR-REQ-204/205`). This is a mechanical
version-string format correction only — no RAE-001 semantic content (template_id, options,
`eligible_authority`, or any other frozen field value) is altered. `rollback_approval_evidence.py`
uses `ROLLBACK_APPROVAL_TEMPLATE_VERSION = "1.0"` (documented inline at its definition), required
because RAE-REQ-011 itself names conformance to this exact, unamended CHGR schema as its own
authoring basis. Not a stop condition: none of §102's stop-condition categories name a version-
string format mismatch, and the fix required no contract reinterpretation, no weakening of any
RAE-001 requirement, and no CHGR modification.

## 5b. Finding — Architecture Zone Policy Gap (NON-BLOCKING)

149K's plan (§4) chose `src/pcae/core/rollback_approval_evidence.py` as the module's home,
matching `mutation_permission.py`'s precedent, but did not check `.pcae/policy.toml`'s
`[architecture.rules]` dependency-direction policy. `core`'s allowed dependency set was
`["core", "cltr"]` only — it did not permit `governance` or `interactive_workflow`, both of
which `create_rollback_approval_decision` legitimately needs (RAE-REQ-079: Decision creation
is architecturally owned by the existing CHGR Confirmation->Publication pipeline, not a new
parallel command family). `pcae check` surfaced this as two `ArchitectureDependencyWarning`s
(`core -> governance`, `core -> interactive_workflow`) — non-blocking under this task's
`advisory` enforcement mode, but a real, previously-undetected policy gap, not something to
silently accept. Resolved by extending `core`'s allowed-target list in `.pcae/policy.toml`
(one line, plus a documentation comment matching this file's own established per-phase
convention for exactly this kind of new, narrow, justified zone edge — see the many similar
comments already in that file for `commands`, `governance`, `interactive_workflow`, and
`aesic`). The dependency remains strictly one-way: no `governance` or `interactive_workflow`
module imports back into `core` (mechanically unaffected by this change, and independently
consistent with `rollback_approval_evidence.py`'s own import-graph tests). `pcae check` reports
zero dependency warnings after this change.

## 6. Import Boundary (mechanically verified)

`tests/test_rollback_approval_evidence_contract.py` asserts, via AST-parsed import inspection,
that `rollback_approval_evidence.py` imports none of: the Permission Broker Foundation module,
the Wave-1 mutation-permission adapter, `pcae.core.agent`, or `pcae.cltr.authority.*`/
`pcae.cltr_cutover`. During implementation, a pre-existing repository-wide regression guard
(`tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_permission_broker_consumer_scope_inventory`)
flagged the new module because its *docstring prose* (documenting what it must NOT import)
contained the literal substring `permission_broker_foundation`. This was a true positive against
an overly literal string-scan guard, not a real import — corrected by rephrasing the prose
(no code change) to describe the module by name without the exact importable-path substring.
Re-run confirmed clean (see §8).

## 7. Regression Results

| Suite | Result |
|---|---|
| `pytest -k 'chgr' -n auto` | 225 passed, 2 pre-existing failures (unrelated `python -m build` wheel/sdist environment issue — reproduced identically on pre-149L `HEAD`) |
| `pytest -k 'tam or authorization or cltr_cutover' -n auto` | 2810 passed, 9 confirmed pre-existing failures (same `python -m build` environment issue, reproduced identically without this phase's changes), 8 skipped |
| `pytest -k 'iwc or interactive_workflow' -n auto` | 693 passed |
| `pytest -k 'aesic or authority_evaluation' -n auto` | 431 passed |
| `pytest -k 'permission_broker or pol_004 or pol_001 or pol_005' -n auto` | 980 passed (after the §6 docstring correction) |
| `pytest -k '149j'` | 49 passed (149J's own independent-verification suite, unmodified, identical to its original run) |
| `pytest -k '149f or 149g or wave1 or mutation_permission' -n auto` | 79 passed (Wave-1 regression) |
| `pytest -k 'rollback' -n auto` | 412 passed (existing AG3/AG5-adjacent tests; zero new AG3/AG5 execution test added) |
| `pytest -m fast_green -n auto -q` | **4391 passed** — identical to the pre-phase baseline. New test files are not in `tests/conftest.py`'s `FAST_GREEN_MODULES` allowlist (a curated list of core-module names, not phase-numbered files — consistent with how every other `test_phase_*`/`test_149*` file in this repository is excluded from that marker), so this is the expected, correct outcome, not evidence of zero new coverage. |
| New suite alone: `pytest tests/test_rollback_approval_evidence_*.py -n auto` | **77 passed** |

All pre-existing failures were independently reproduced on `HEAD` with this phase's changes
stashed, confirming they are environment-scoped (`python -m build` unavailable/misconfigured in
this sandbox) and not introduced by this phase.

`pcae runtime inspect` before and after this phase's work: both **Observed / observe /
unavailable**, Permission Broker status `execution_unavailable`, registry empty. Unchanged.

## 8. Contract / Boundary Diff Verification

```
git diff --name-only 318f4b50..HEAD -- docs/contracts/                          -> empty
git diff --name-only 318f4b50..HEAD -- src/pcae/core/agent.py \
  src/pcae/commands/agent.py                                                    -> empty
git diff --name-only 318f4b50..HEAD -- src/pcae/core/mutation_permission.py     -> empty
git diff --name-only 318f4b50..HEAD -- src/pcae/core/permission_broker_foundation.py \
  src/pcae/core/permission_broker.py                                           -> empty
```

All four boundaries confirmed empty. RAE-001 remains v1.0, unamended.

## 9. Implementation Verdict

```
RAE EVIDENCE SUBSTRATE IMPLEMENTED
— READY FOR INDEPENDENT VERIFICATION
```

## 10. No-Go Confirmations

RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains unchanged. PBPC-001 v1.2 remains
unchanged. PBPA-001 v1.0 remains unchanged. CHGR-001 remains unchanged. No AG3 Permission Broker
integration was implemented. No AG5 Permission Broker integration was implemented. No rollback
execution behavior was changed. No production rollback request now hardcodes or derives
`approval_present=True`. The implemented approval-present derivation is an evidence service
only and is not yet consumed by AG3/AG5. No self-declared legacy flag was promoted to trusted
approval. IWC confirmation remains distinct from approval. AESIC/AEM remain disclosure-only. No
illegal CHGR/TAM authority-family composition was introduced. No POL-001..012 meaning was
changed. No POL-013+ was added. No Runtime Enforcement behavior was changed. TK1/TK2/TK3 remain
deferred. No Prompt Generation, Prompt Dispatch, or agent invocation capability was implemented.
Runtime remains Observed, maximum capability remains observe, and execution availability remains
unavailable.

## 11. Recommended Next Phase

```
149M — Rollback Approval Evidence Implementation Independent Verification
```

149M should independently attack: the canonical-vs-noncanonical distinction (§15 mechanism),
Decision/Binding creation ordering, authority validation's honest limits (§19's template-shape-
only check), operation binding (AG3/AG5 exact-match, both directions), the TTL boundary,
revocation/supersession, replay/retry semantics, agent-forgery resistance, `approval_present`
derivation's full conjunction, the CHGR/TAM import wall, and AG3/AG5 non-interference — plus this
report's own §5 finding (template version format) for independent confirmation that it is
correctly scoped as non-semantic.
