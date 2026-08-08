# Phase 149O.18A — HATP Mandatory Cutover State Foundation

**Phase type:** BOUNDED IMPLEMENTATION (Wave A of the 149O.17 implementation
plan). Implements only the HMRC-001 cutover-state substrate. No evidence
consumption, no AG3/AG5 gating, no CLI plumbing, no legacy-authority
change, no Permission Broker work, and no real `HATP_MANDATORY`
activation of the current deployment.

**Subject:** `HMRC-001 v1.0` §13/§17-19, Wave A per
`docs/PHASE_149O_17_HATP_MANDATORY_PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md`
§9.1.

---

## 1. Baseline (Initial Inspection)

Confirmed by direct command execution at phase start:

- `git status --short` / `git status --branch --short`: clean, `main...origin/main`.
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — 7 pre-existing `tasks/done/` vs
  `tasks/DONE.md` entries predating this phase (identical pre-existing
  set already noted by 149O.16/149O.16.2/149O.17; not remediated here,
  outside this phase's scope).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`; Permission
  Broker status `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.17`: 149O.17 confirmed `status: completed`, report
  `complete`, pushed, `origin/main..HEAD: 0`; reconciliation
  `status: reconciled`, `Mutation: none (inspection only)`; recommended
  next phase confirmed as 149O.18A.

Confirmed: repository clean; 149O.17 complete; HMRC-001 v1.0 independently
verified `CONFORMS` (149O.16); HATP production `NOT READY`; runtime
`Observed / observe / unavailable`. No mutation performed by this
inspection.

**Phase-entry commit:** `cb1d9e89` (149O.17's final commit).

---

## 2. Primary Sources Read

- `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  (HMRC-001 v1.0, full text, §1-36).
- `docs/PHASE_149O_17_HATP_MANDATORY_PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md`
  (full text, §1-20, especially §9.1's Wave A module design).
- `docs/PHASE_149O_16_HATP_MANDATORY_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`
  (contract-verification status).
- `src/pcae/core/hatp_bootstrap.py` (full file, 607 lines) — confirmed
  `HATPTrustStore.production().root` (lines 528-537) is the existing,
  public, unmodified protected-root accessor; confirmed no write API
  exists on `HATPTrustStore` at all ("enrollment, revocation, and
  rotation ... are not implemented by this phase at all"); confirmed
  `_reject_symlink`/`_default_production_trust_root` are private
  (leading-underscore) internals, not re-exported.
- `src/pcae/core/repository_identity.py` (full file) — confirmed
  `read_repository_identity(root: HarnessPath)` and
  `is_valid_repository_instance_id` as the Layer-1 repository-identity
  API this phase reuses unmodified.
- `src/pcae/core/hatp_ag_authority.py` (relevant sections) — confirmed
  the exact existing precedent (`_resolve_production_repository_context`)
  for deriving a production repository identity from `HarnessPath`
  without any caller-supplied override, mirrored by this phase's
  `resolve_production_hatp_cutover_mode`.
- `src/pcae/core/hatp_hardware_credentials.py`, `src/pcae/core/human_approval_trusted_provenance.py`
  — confirmed duplicate-JSON-key-rejection precedent
  (`_reject_duplicate_keys`/`_load_json_no_duplicate_keys`) and confirmed
  no `Admin`/`Principal`-gated write-authority mechanism exists anywhere
  in either file.
- `src/pcae/cltr/authority/envelope.py` — confirmed the repository's
  existing precedent for a new, authority-bearing, strict-lexical
  timestamp field (`_TIMESTAMP_PATTERN`, `Z`-suffix-only, fully anchored),
  reused for this phase's `activated_at`/`first_activated_at` fields
  rather than either existing permissive `fromisoformat`-based parser.
- `docs/PHASE_149O_6_HATP_CLASS_B_DEPLOYMENT_ACTIVATION_IMPLEMENTATION.md`
  — confirmed no formal `ProtectedAdminPrincipal`/authority-check type was
  ever established by the 149O.6/149O.7 lineage; that lineage's actual
  Class-B mechanism is OS-principal separation
  (`inspect_bootstrap_environment`'s `agent_and_admin_share_os_principal`
  check), not an application-level principal object.

**Reconfirmed directly:** `HATPTrustStore.production().root` is the
existing public protected-root accessor (`hatp_bootstrap.py:528-537`). No
alternate protected root was invented.

---

## 3. 149O.18A HMRC Requirement/Invariant/Attack Subset

Per the 149O.17 plan's §6/§7/§8 traceability tables (Wave A ownership,
module `CUT`):

**Requirements owned:** HMRC-REQ-031 through 056, 074, and the cutover
portion of 085 (25 requirements: mode vocabulary, `PREPARED`/
`HATP_MANDATORY` definitions, transition/monotonicity rules, protected
storage, Cutover Record schema, activation readiness statements, no-cache
discipline, no-dual-authority).

**Invariants owned:** MC-6 (only protected Class-B state determines mode),
MC-7 (cutover one-way for ordinary principals). MC-2 and MC-9's cutover
portions are also exercised (fresh-read, no-cache).

**Attacks owned:** #22 (delete Cutover Record), #39 (cutover-record
corruption), #40 (cutover-record wrong repository), #41 (cutover-record
unknown version), #42 (cutover-record boolean version).

Every 18A-owned requirement has a corresponding production
function/type, failure behavior, and test (see §7/§9 below). No
requirement owned by Waves B-F (evidence consumption, AG3/AG5 gating,
CLI plumbing, PB truthful-effect handling) was absorbed by this phase.

---

## 4. Production Module

**New module (the only one; no other production file was touched):**
`src/pcae/core/hatp_mandatory_cutover.py` (632 lines).

Confirmed by `git diff --name-only cb1d9e89..HEAD -- src/pcae/`: exactly
one file.

### 4.1 Cutover Mode type

`CutoverMode(str, Enum)` with exactly three members:
`LEGACY_COMPATIBLE`, `PREPARED`, `HATP_MANDATORY` (HMRC-REQ-031). No
fourth mode value exists anywhere in the module; every fail-closed
outcome reuses `HATP_MANDATORY` (the strictest existing mode) rather than
inventing a new one.

### 4.2 Cutover Record model

Frozen dataclass `CutoverRecord` with exactly the five fields
HMRC-REQ-045 freezes: `version: int`, `repository_instance_id: str`,
`mode: CutoverMode` (only `PREPARED`/`HATP_MANDATORY` are storable —
`LEGACY_COMPATIBLE` is the record's *absence*, never a stored value),
`activated_at: str`, `activated_by: str`.

### 4.3 Strict parser (`parse_cutover_record`)

Closed schema: rejects unknown fields, missing fields, and duplicate
JSON keys (`_load_json_no_duplicate_keys`, mirroring
`human_approval_trusted_provenance.py`/`hatp_hardware_credentials.py`'s
existing pattern, reimplemented locally to preserve this module's
independence). `version` uses the strict
`isinstance(value, int) and not isinstance(value, bool)` guard
(HMRC-REQ-046). `mode` accepts only `"PREPARED"`/`"HATP_MANDATORY"` —
`"LEGACY_COMPATIBLE"` as a stored value is explicitly rejected.
Constructor and parser share one validation domain: `CutoverRecord` is
never constructed anywhere in this module except through
`parse_cutover_record`'s already-validated fields, so no state is
directly constructible that the parser would reject.

### 4.4 Strict timestamp hardening (double-Z hardening)

`_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")`,
matched with `fullmatch` before any `datetime.fromisoformat` call — the
same precedent already established by `cltr/authority/envelope.py`'s
`Timestamp` type for a new authority-bearing field, not either existing
permissive `fromisoformat`-based parser
(`hatp_bootstrap.py`/`repository_identity.py`'s own `_parse_iso_timestamp`
helpers, or `rollback_approval_evidence.py`'s). Confirmed to reject:
double-`Z` (`...ZZ`), `Z`-plus-offset (`...Z+00:00`), garbage-plus-offset
(`...X+00:00`), trailing/leading whitespace, lowercase `z`, a bare
`+00:00` offset (this schema is `Z`-suffix-only, stricter than
accepting both forms), and calendar-invalid dates (month 13, hour 25).
149O.12B-Obs-PY39-1's CPython 3.9 `fromisoformat` permissiveness is not
reintroduced, independent of interpreter version, because the regex is
fully anchored (`fullmatch`) before `fromisoformat` is ever called.

### 4.5 Protected storage

Reuses `HATPTrustStore.production().root` (no modification to
`hatp_bootstrap.py`). Two files under that root:
`cutover-record.json` (the mutable, forward-transitioning Cutover
Record) and `cutover-activation-marker.json` (the write-once monotonic
activation-history marker). Confirmed outside agent-writable `.pcae/`
(`TestNoRealProductionActivation`/`TestHighPriorityAttackSmoke` in the
phase test module; `test_repo_local_pcae_directory_is_never_consulted`
in the unit test module).

A local, two-line `_reject_symlink` (checking both the target and its
parent) is reimplemented rather than importing `hatp_bootstrap.py`'s
private `_reject_symlink` — the same minimized-duplication tradeoff the
149O.17 plan recorded (§9.5): a well-understood one-line safety check
duplicated once is lower-risk than widening a sibling module's public
surface for a single reuse.

### 4.6 Mode resolution (`resolve_production_hatp_cutover_mode`)

The sole production entrypoint. Signature: `(root: HarnessPath) ->
CutoverModeResolution`. `root` is a neutral repository locator only
(used solely to read the local, non-authority-bearing
`repository_instance_id` via `repository_identity.py`, mirroring
`hatp_ag_authority.py::_resolve_production_repository_context`'s exact
precedent) — it never selects the protected trust root, which is always
resolved internally via `HATPTrustStore.production().root` and is never
caller-, env-, or CLI-selectable. Performs the full read/validate
sequence on every call — no cache (HMRC-REQ-052; confirmed by
`test_no_cache_reflects_state_change_within_same_process`).

The internal resolution algorithm (`_resolve_cutover_mode_at_root`, the
private test seam — never exposed with a caller-supplied protected-root
override on any production path) implements exactly the 149O.17 §9.1
algorithm:

1. No local repository identity provisioned → fail closed
   (`HATP_MANDATORY`, reason `fail_closed_no_local_repository_identity_provisioned`).
2. Valid Cutover Record for this repository → return its stored mode.
3. Valid Cutover Record for a *different* repository → treated as
   not-present-for-this-repo (HMRC-REQ-048), falls through to the
   absent-record path.
4. Record absent (or not-for-this-repo) → consult the monotonic
   activation-history marker:
   - Marker absent → `LEGACY_COMPATIBLE` (first install, HMRC-REQ-050).
   - Marker present for this repository → fail closed
     (`HATP_MANDATORY`, "record missing after prior activation" —
     HMRC-REQ-049, attack #22).
   - Marker present for a *different* repository, or marker itself
     corrupt → fail closed too (a shared protected root serving
     multiple repositories provides no proof of *this* repository's
     first-install status in either case; see §8 below).
5. Record present but corrupt/unreadable/symlinked/unknown-version
   (`parse_cutover_record` rejects unsupported versions, so "unknown
   version" fails closed automatically with no special case) → consult
   the marker:
   - Marker present for this repository → fail closed (attack #39/#41/#42).
   - Marker absent → internal-consistency fail-closed (149O.17 §9.1 step
     5's "should be structurally unreachable in practice" branch — a
     genuinely first-install deployment cannot organically produce a
     corrupt record, since nothing ever wrote one). Never a silent
     `LEGACY_COMPATIBLE`.

No branch of this algorithm returns `LEGACY_COMPATIBLE` except the single
first-install case (step 4's marker-absent sub-branch). Every other
outcome is either a confirmed valid record or a fail-closed
`HATP_MANDATORY`-equivalent.

### 4.7 Transition validation and write (activation-authority scope decision)

`is_valid_cutover_transition(current, target) -> bool` centralizes the
transition graph: only `LEGACY_COMPATIBLE -> PREPARED` and
`PREPARED -> HATP_MANDATORY` are valid (HMRC-REQ-038/039). Every reverse
transition, every direct skip, and every self-transition is rejected.
`PREPARED -> LEGACY_COMPATIBLE` is not frozen by HMRC-001 either way
(149O.17 §9.1); this module's transition graph omits it entirely
(conservative omission, not a guess).

**Activation-authority disposition (recorded here, not improvised at
implementation time):** direct source reading (§2 above) confirmed no
application-level "Protected Activation Authority" principal/check
mechanism exists anywhere in this codebase — `HATPTrustStore` itself is
deliberately read-only, and the 149O.6/149O.7 lineage's actual Class-B
mechanism is OS-level file-permission separation on the fixed protected
root, not an in-process principal object. Per the governing prompt's
stop-condition guidance (do not approximate protected-admin authority
with a caller-supplied username/env flag), this phase does **not**
invent a `ProtectedAdminPrincipal` type. Instead, the internal transition
writer (`_write_cutover_transition`) takes an explicit `protected_root:
Path` parameter and is never paired, anywhere in this module, with
`HATPTrustStore.production().root` (confirmed by
`TestProtectedRootUsage::test_internal_test_seam_never_paired_with_production_root_in_module_source`,
an AST-based check for real `Call` nodes, not a substring/docstring
match) — there is no production-, CLI-, or agent-reachable call path
that can cause a real activation. `activated_by` is accepted as an
explicit, caller-supplied string with no default and no derivation from
process/session/environment state, because the only legitimate caller is
a human operator who already possesses real filesystem write access to
the protected root — the actual enforcement mechanism is the same OS
file-permission boundary this repository already relies on for the
sibling `registry.json`, not an application-level check that does not
yet exist. No public CLI command exists for activation (matching the
149O.17 plan's explicit choice not to invent one).

Concurrency safety: `_write_cutover_transition` acquires an exclusive
`fcntl.flock` on a lock file under the protected root, re-resolves the
current mode fresh (TOCTOU discipline) while holding the lock, validates
the transition against that freshly-resolved current mode, and only
then performs an atomic `os.replace` write. A concurrent racing writer
either serializes behind this one and is rejected (its target no longer
follows the now-current mode), or serializes ahead and this call is
rejected the same way. No downgrade or lost-update race is possible
because only two strictly-ordered forward transitions exist at all.
Verified with real `threading` concurrency tests (§7 below).

The monotonic marker uses `O_CREAT | O_EXCL` (create-once, HSCE-style
no-clobber) — deliberately different from the Cutover Record's own
`os.replace` semantics, since the record legitimately transitions
forward while the marker must never change once written.

---

## 5. Timestamp Field Disposition

`activated_at`/`first_activated_at` are the only timestamp fields in
this phase's schema. Both use the strict `Z`-suffix-only grammar (§4.4).
149O.16.2's CPython 3.9 `fromisoformat` double-Z-class debt
(`149O.12B-Obs-PY39-1`, independently confirmed resolved) is not
reintroduced by this new, authority-bearing parser, per the 149O.17
plan's explicit instruction (§14) not to reuse either existing
permissive parser as precedent for this field.

---

## 6. Protected Root / Path Safety / Repository Identity

- **Protected root source:** `HATPTrustStore.production().root` only;
  never env, CLI, repo-local, or caller-selectable (confirmed by
  `TestProtectedRootUsage` in the phase test module, including an
  environment-variable-poisoning smoke test).
- **Protected path:** two files under that root, `cutover-record.json`
  and `cutover-activation-marker.json`; symlink rejection on both the
  file itself and its parent directory (mirroring
  `repository_identity.py`'s own `_reject_symlink` pattern).
- **Repo-local spoof:** creating `<repo>/.pcae/cutover-record.json` (or
  any other repo-local location) has no effect on resolution —
  confirmed by `test_repo_local_pcae_directory_is_never_consulted`.
- **Symlink attack:** both a symlinked record file and a symlinked
  protected-root parent directory are rejected and fail closed
  (never trusted, never treated as absent) — confirmed by
  `test_record_symlink_rejected`/`test_parent_symlink_rejected`.
- **Repository/deployment identity:** reused unmodified via
  `read_repository_identity`/`is_valid_repository_instance_id`
  (`repository_identity.py`), the same Layer-1 API
  `hatp_ag_authority.py` already uses for its own production repository
  context. No caller-provided repository identity is ever accepted.

---

## 7. Tests

- **`tests/test_hatp_mandatory_cutover.py`** (85 tests): mode vocabulary,
  transition graph (all 9 combinations), parser closed-schema/strict-
  version/strict-timestamp/duplicate-key coverage, symlink rejection,
  mode resolution across every branch of §4.6's algorithm (first
  install, valid record, wrong repository, deleted/corrupt/unknown-
  version/boolean-version record, corrupt marker never treated as
  absent, no-cache), activation-marker write-once semantics, transition
  writes (valid forward transitions, rejected downgrades/skips, input
  validation, real `threading`-based concurrent-transition-safety
  tests — both identical-transition races and
  `PREPARED`-vs-`HATP_MANDATORY` races — repo-local spoof).
- **`tests/test_phase_149o_18a_hatp_mandatory_cutover_state_foundation.py`**
  (29 tests): production file allowlist (git-diff-based, both
  `--name-only` and forbidden-file-list forms), contract byte-identity
  (all 7 upstream contracts), AST-based dependency-closure checks (no
  evidence-store/PB/agent/CLI imports — real `Call`/`Name`/`Attribute`
  nodes, not docstring substrings), mode-vocabulary structural checks,
  protected-root usage (AST-based single-call-site confirmation that
  `HATPTrustStore.production()` is called only inside the read-only
  resolver, never alongside the transition writer), test-seam isolation,
  scope-boundary no-go checks, high-priority attack-scenario smoke tests
  independent of the unit suite, and confirmation that no real
  production Cutover Record/marker was created and that the production
  resolver never mutates the current repository's `.pcae/` directory.

Both files run under 0.25s combined (114 tests) and are deterministic,
filesystem-only (temp dirs, real symlinks, real `flock`), with no
hardware, network, or wall-clock dependency — added to
`FAST_GREEN_MODULES` in `tests/conftest.py`.

---

## 8. Design Observation (Non-Blocking): Shared Single-Slot Protected State

HMRC-REQ-043/048 freeze a single, flat Cutover Record location under one
host-level protected root (not per-repository-keyed). This phase's
monotonic marker necessarily inherits the same shared-single-slot
topology (HMRC-REQ-049 does not specify per-repository keying either).
Consequence, confirmed and documented rather than silently decided: on a
host that runs more than one repository against the same protected root,
once *any* repository has ever been activated, a *different*
repository's own first-install status can no longer be affirmatively
proven from the marker alone (the marker may belong to the other
repository) — this phase's resolver treats that ambiguity conservatively
(fail closed, never assume first-install) rather than risk a
corruption-shaped downgrade. This is a direct, non-arbitrary consequence
of HMRC-001's own frozen single-file storage design, not a defect
introduced by this phase's implementation choices. Not currently
observable on this development host (single repository, no protected
root provisioned). Recorded for 149O.19/a future HMRC-001 revision to
consider if multi-repository-per-host deployments become real.

---

## 9. Regressions

- **HMRC/HATP/rollback/PB regression sweep** (`-k "149o"` plus
  `test_permission_broker.py`, `test_agent.py -k rollback`, and the
  full `-k "hatp"` sweep): re-run after implementation. All failures
  independently confirmed via `git worktree add <tmp> cb1d9e89` (a true,
  isolated baseline checkout — not a partial `git checkout`, which does
  not delete files absent from the target commit) to be either (a)
  pre-existing at the 149O.17 phase-entry commit and unrelated to this
  phase (17 tests: CPython-3.9-venv-mismatch and double-Z-quirk checks,
  a `fido2` optional-hardware-dependency collection error, and several
  historical `hatp_bootstrap`-import/contract-byte-identity assertions
  already broken before this phase began), or (b) a necessary,
  well-understood, HMRC-001-wave-sequencing consequence of this phase's
  required production module now existing — historical "no
  `hatp_mandatory_cutover.py` module exists yet" / "no `src/pcae/` file
  changed since my own phase-entry commit" assertions in
  `test_phase_149o_12b_hatp_signing_ceremony_implementation.py` (2
  tests, not Fast-Green-gating) and, within the Fast-Green-gating set,
  `test_phase_149o_15_hatp_mandatory_production_consumption_contract_freeze.py`,
  `test_phase_149o_16_hatp_mandatory_consumption_contract_independent_verification.py`,
  `test_phase_149o_16_2_publication_timestamp_compatibility_independent_verification.py`,
  and `test_phase_149o_17_hmrc_implementation_plan_completeness.py` (8
  tests). No AG3/AG5/rollback/PB *behavioral* regression was found in
  any of these sweeps — every newly-invalidated assertion is a
  structural "no production file changed"/"module doesn't exist yet"
  snapshot check, by design always going to break at the first
  implementation wave that follows a contract-freeze/planning phase.
  None of these assertions is fixable by adding a per-file allowlist
  entry within this phase's own declared, narrow file scope without
  touching multiple unrelated historical phases' test files; per
  established repository precedent (149O.16.2), they are reported here
  with full attribution rather than silently hidden.
- **PB regression** (`tests/test_permission_broker.py`): 234/234 passed,
  0 failures — no Permission Broker behavior changed.
- **AG3/AG5-adjacent rollback regression** (`tests/test_agent.py -k
  rollback`): 78/78 passed, 0 failures — no rollback dispatch behavior
  changed (expected: this phase does not touch `agent.py` at all).

---

## 10. Fast Green

`pytest -m fast_green -n auto`, deselecting the 9 tests in §9(b) above
(the 8 Fast-Green-gating, necessarily-invalidated snapshot assertions)
plus `test_this_venv_interpreter_is_actually_python_39` and
`test_double_terminal_z_pre_existing_stdlib_quirk_not_a_new_regression`
(pre-existing, confirmed unrelated), and ignoring
`test_phase_149o_7_hatp_class_b_activation_independent_verification.py`
(pre-existing `fido2` optional-dependency collection error, confirmed
unrelated via `git stash`/worktree A/B):

```
5237 passed, 2 skipped
```

Raw, unfiltered Fast Green (no deselection): **5237 passed, 10 failed, 2
skipped, 1 collection error** — the 10 failures and 1 error are exactly
the 11 items enumerated above (9 necessarily-invalidated-by-this-phase
snapshot assertions + 2 pre-existing-unrelated).

---

## 11. Report Trust

- `pcae phase-report reconcile --phase-id 149O.17`: `status: reconciled`,
  `Mutation: none (inspection only)` (confirmed at phase start, §1).
- `git diff --name-only cb1d9e89..HEAD -- src/pcae/`: exactly
  `src/pcae/core/hatp_mandatory_cutover.py`.
- `git diff --stat cb1d9e89..HEAD -- docs/contracts/`: empty for all
  seven upstream contracts (HMRC-001, HSCE-001, HATP-001, RAE-001,
  RWMPC-001, PBPA-001, PBPC-001).

---

## 12. Stop-Condition Disposition

Of the 149O.17 plan's 11 recorded implementation stop conditions (§13),
the following were directly relevant to Wave A and are resolved, not
improvised:

1. **Corrupt-record-with-no-marker edge case** — implemented exactly as
   149O.17 §9.1 step 5 specified: an internal-consistency fail-closed
   outcome (`REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY`), never a silent
   `LEGACY_COMPATIBLE`. Confirmed structurally unreachable via any code
   path in this module (nothing in this phase ever writes a corrupt
   record), and covered by a dedicated test
   (`test_corrupt_record_with_no_marker_is_internal_consistency_failure_not_legacy`).
2. **`PREPARED -> LEGACY_COMPATIBLE` transition** — HMRC-001 itself
   (HMRC-REQ-039) already forbids every reverse transition to any
   ordinary mechanism, and explicitly states reversion "requires a
   separately governed administrative mechanism ... this contract does
   not define one." This phase's transition graph therefore omits this
   transition entirely (not a guess; a direct reading of the frozen
   text) — no code path can write it.
3. **Protected storage monotonic-write-once property** — confirmed
   sufficient: the marker uses `O_CREAT | O_EXCL` (atomic create-only at
   the OS level on POSIX), and `_write_cutover_transition` additionally
   serializes all transition attempts via `fcntl.flock`, so no two
   processes can race the marker's first write.
4. **Admin-authority mechanism** — resolved per §4.7 above: no
   application-level principal type is invented; the internal transition
   writer is never paired with the production protected root anywhere
   in this module, so the real protection remains the existing OS-level
   file-permission boundary on the fixed protected root, exactly as it
   already is for the sibling `registry.json`.
5. **Atomic monotonic write / concurrent-transition safety** — resolved
   via the `fcntl.flock`-guarded compare-then-write design (§4.7),
   verified with real `threading` concurrency tests, not merely asserted.

No stop condition was reached that required halting implementation or
requesting contract clarification.

---

## 13. Implementation Verdict

```
HATP MANDATORY CUTOVER STATE FOUNDATION: IMPLEMENTED
— READY FOR 149O.18B
```

`src/pcae/core/hatp_mandatory_cutover.py` provides the complete,
independently-tested, production substrate (mode vocabulary, Cutover
Record model/parser, protected persistence, mode resolution, monotonic
activation history, transition validation) that Waves B-F will build on.
It changes no existing effect boundary, evidence-consumption path,
Permission Broker behavior, or CLI surface. The current deployment
remains `LEGACY_COMPATIBLE`-equivalent (no Cutover Record exists
anywhere real; confirmed in §9's regression sweep and §7's dedicated
no-real-activation tests).

---

## 14. Recommended Next Phase

**149O.18B — HATP Mandatory Evidence Consumption Adapter.** Per the
149O.17 plan's dependency analysis (§10.3): depends only on existing
`hatp_evidence_store.py`/`rollback_approval_evidence.py`/
`human_approval_trusted_provenance.py`/`permission_broker*.py` — not on
149O.18A's cutover-mode resolution (the adapter takes no mode parameter;
mode branching is Waves C/D's job). New production file:
`src/pcae/core/hatp_rollback_consumption.py` only. Owns: explicit
evidence-ID input, canonical `HATPEvidenceStore.load`, fresh
`verify_hatp_proof`-based RAE/HATP approval derivation (reused, not
duplicated), Permission Broker request construction (with a
structurally-truthful, never-caller-supplied `simulation_only`), and a
typed consumption result. No AG3/AG5 wiring yet.

---

## 15. Explicit Confirmations (Restated for the Phase Report)

Only `src/pcae/core/hatp_mandatory_cutover.py` was added to `src/pcae/`
this phase — confirmed by `git diff --name-only cb1d9e89..HEAD --
src/pcae/`. HMRC-001 v1.0, HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0,
RWMPC-001 v1.0, PBPA-001 v1.0, and PBPC-001 v1.2 all remain
byte-unchanged. No HATP evidence-consumption adapter was implemented. No
AG3 mandatory consumption was implemented. No AG5 mandatory consumption
was implemented. No `--hatp-evidence-id` rollback CLI plumbing was
implemented. No legacy rollback authority behavior changed. No
Permission Broker behavior changed. `POL-005` remains unchanged. No
`COMP-002` capability was implemented. No rollback dispatch behavior
changed. No real Cutover Record was created in the current production
protected store (confirmed: this development host has no provisioned
Class-B protected root at all, consistent with `pcae runtime inspect`'s
`Observed`/`observe`/`unavailable` status; even if it existed, this
phase never calls the internal transition writer with the production
root anywhere). No Class-B provisioning occurred. No HATP production
activation occurred. Current deployment behavior remains unchanged.
B-149O-1..4 remain **INDEPENDENTLY VERIFIED AT THE HATP-GATED AUTHORITY
BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**, unchanged by this phase.
HATP production remains **NOT READY**. Runtime remains `Observed /
observe / unavailable`.
