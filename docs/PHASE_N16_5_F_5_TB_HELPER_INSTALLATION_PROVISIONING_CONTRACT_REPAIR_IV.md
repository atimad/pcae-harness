# Phase N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR-IV — Evidence

Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(direct `.1` CPIPC child of the predecessor contract-repair phase; independently
derived and validated via `pcae.core.phase_id.is_valid` — True on both parent
and child — no collision found against `git log --all` / working tree text
search).

Predecessor: `docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md`
(commit `4ab787d6`, canonical report finalized at `fe001e79`/`692481e5`/`8aeabd48`) —
**COMPLETE — CONTRACT REPAIRED / FROZEN — PENDING INDEPENDENT VERIFICATION.**

**Disposition of this phase: COMPLETE — NOT VERIFIED / BLOCKED.**

**Scope actually authorized and performed:** independent adversarial
verification of the predecessor's contract-text repair (HPAC-PAWA-001 v4.0
§98, HPAC-PAWA-HELPER-001 v5.0 §30E, HPAC-PPA-001 v2.1 unchanged). No
production `src/pcae/**` file was modified. No live host state was touched.
No implementation was begun.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`

---

## 1. Predecessor canonical-report contradiction — adjudicated

The activating prompt for this phase asserted that the predecessor's
canonical report simultaneously states "COMPLETE — CONTRACT REPAIRED /
FROZEN — PENDING INDEPENDENT VERIFICATION" **and** "COMPLETE — NOT VERIFIED
/ BLOCKED... F1 unresolved... NOT READY FOR IMPLEMENTATION" as if both were
the *same* phase's disposition.

Independently re-read from repository truth:

- `docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md`
  (line 10), `.pcae/phase-completion-report.md` (line 7), and
  `PROJECT_STATUS.md` (`## Current Phase`, line 5) **all** state, uniformly
  and only: **"COMPLETE — CONTRACT REPAIRED / FROZEN — PENDING INDEPENDENT
  VERIFICATION."** No file anywhere states "COMPLETE — NOT VERIFIED /
  BLOCKED" for *this* phase.
- The "COMPLETE — NOT VERIFIED / BLOCKED (F1)" disposition belongs to a
  **different, earlier phase** — the predecessor's own predecessor,
  `docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_IDENTITY_CONTRACT_REPAIR_IV.md`
  — and is correctly *cited* by the contract-repair phase as the finding
  (F1) it set out to repair (evidence doc §0/predecessor line, canonical
  report line 11). Citing a predecessor's blocked disposition while
  reporting your own phase's different, successful disposition is not a
  self-contradiction.

**Verdict: no load-bearing contradiction exists in the predecessor's
canonical report.** The activating prompt's framing conflates two distinct
phases' dispositions. This is recorded here per phase-authorization §2's
instruction not to silently pick an interpretation, but the correct
adjudication is that the premised contradiction is not present in
repository truth — interpretation **A** as originally offered ("the stale
wording is a reporting inconsistency") is closer, except there is no stale
wording to begin with; every canonical artifact is internally consistent.

This adjudication does **not** end the IV — §2 below.

---

## 2. F1-A / F1-B independently re-verified against contract text

Independently re-read (not accepted from the predecessor's prose):

- `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` §13
  (REQ-052/053/057), §30E (REQ-184-188) — confirmed HELPER v5.0, 189
  declarations.
- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  §98 (REQ-345-352) — confirmed PAWA v4.0, 352 declarations.
- `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` §5
  (REQ-021-022) — confirmed PPA v2.1, byte-identical to the version cited
  by PAWA-REQ-351.

Findings, confirmed independently:

- **F1-A (provisioning/bootstrap circularity):** REQ-346 states genesis
  requires "No admitted H, no ceremony, no prior PCAE principal, and no
  `admin_mutation` dispatch through any helper process." REQ-345 scopes the
  dispatching capability to the standalone helper-admin script exclusively.
  **Textually eliminated** — genesis no longer presupposes an admitted H.
- **F1-B (self-lineage/rotation contradiction):** REQ-347 states rotation
  is performed by "the helper-admin script — never the current H=G itself,
  never dispatched through G's §33C boundary." HELPER-REQ-185 confirms
  HELPER175 is "satisfied by construction" because the mutation id is no
  longer a member of the enum H can ever be asked to perform at all
  (REQ-184), not merely denied by a runtime check. **Textually eliminated**,
  and by a stronger mechanism than a runtime guard (closed-enum absence,
  fails at `operation_scope_invalid` per HELPER-REQ-187 before any
  admission logic runs).
- **PPA reuse (Model P-D):** REQ-021-025's genesis/rotation/consumer shape
  is structurally identical to REQ-345-350's, not merely an analogy —
  confirmed by direct requirement-by-requirement comparison (fresh test
  `test_ppa_req_021_022_shape_matches_pawa_345_350`).
- **Model E / cross-contract preservation:** `configure_privileged_helper`
  was never one of Model E's three sealed families (§30B); HELPER v5.0's
  own text confirms the five *remaining* operations and their
  `pawa_failure_code` mappings are unchanged (REQ-188). No fourth/fifth
  Model E family introduced.

**At the contract-text level, the predecessor's repair is sound.** This
confirms the predecessor's own adjudication of F1-A/F1-B. The IV's finding
below is orthogonal to contract-text soundness.

---

## 3. LOAD-BEARING FINDING — contract repair has not propagated to the already-deployed source it describes

This is the reason for this phase's BLOCKED disposition.

### 3.1 What was found

`src/pcae/core/hpac_pawa_helper_protocol.py` (written by an **earlier**
phase, N16-5-F-5-TB-HELPER-IMPL, commit `3787cbb6`, months before the
contract-repair phase existed; last touched by N16-5-F-5-TB-REPLAY-REPAIR,
commit `29a2ec35` — **neither commit is owned by, or was touched by, the
contract-repair phase**) still defines:

```python
CLOSED_ADMIN_MUTATIONS: FrozenSet[str] = frozenset(
    {
        "enroll_principal",
        "revoke_principal",
        "enroll_credential",
        "revoke_credential",
        "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
        "configure_privileged_helper",
    }
)
```

— i.e. the **pre-repair** (v4.0/v4.0, not v5.0) vocabulary, still including
both mutations the frozen HELPER-REQ-184 says are "no longer" members.

This is not dead code. Independently traced the live call graph:

1. `src/pcae/core/hpac_pawa_helper_entrypoint.py` dispatches every incoming
   `HelperRequest` through the closed `§13` dispatch table (`dispatch(...)`).
2. `src/pcae/core/hpac_pawa_helper_operations.py::handle_admin_mutation` —
   the real `admin_mutation` handler H's own process executes — checks
   `mutation not in CLOSED_ADMIN_MUTATIONS` (imported from
   `hpac_pawa_helper_protocol.py`) and only rejects mutations **outside**
   that set. `configure_privileged_helper` passes this check today.
3. `src/pcae/core/hpac_pawa_helper_store_adapter.py` has a live branch,
   `if mutation == "configure_privileged_helper":`, that calls
   `install_store.register_helper_metadata(...)` — a real write.

This is precisely the F1-A/F1-B dispatch route (`admin_mutation` "driven
through the §33C helper boundary," i.e. through H's own process) that the
frozen contract's REQ-345/REQ-184 say must no longer exist. **The circular,
self-lineage-violating mechanism the contract repair eliminated in prose
remains fully wired and reachable in the actual production code today.**

### 3.2 Why this was not caught by the predecessor

The predecessor's own source-impact map
(`docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR.md`
§8) lists:

| Item | Category (predecessor's claim) |
|---|---|
| `src/pcae/core/hpac_pawa_helper_writer_authority.py` | no change |
| `src/pcae/core/hpac_pawa_helper_store_adapter.py` | no change |

"No change" was read (correctly, for the narrow claim "this phase's own
diff does not touch this file") but the map never asks the different,
necessary question: **is the file, as it already stood, now inconsistent
with the contract text this phase just froze?** It is. The map never
mentions `hpac_pawa_helper_protocol.py` (the file actually defining the
closed enum) at all. `src/pcae/**` byte-unchanged **by this phase's diff**
is a true and narrow claim; it was implicitly, and incorrectly, treated as
equivalent to "the deployed system is unaffected by the stale vocabulary."
It is not — the vulnerable path was never removed, only re-described.

### 3.3 Is this "F1 relocated" or "a different defect"?

Neither cleanly. Re-examining phase-authorization §2's options:

- **Not (A)** — the repair is not a "reporting inconsistency"; the contract
  text is genuinely repaired.
- **Not quite (B)** — PAWA's new direct-dispatch model (§98) does not
  itself relocate the problem; REQ-345-350 have a coherent, non-circular
  provenance boundary (§4 below).
- **(C) — a different, load-bearing defect**, precisely: **the contract
  repair and the production source it describes have diverged.** The
  contract now describes a system that does not yet exist; the system that
  does exist still implements the pre-repair, circular design. F1 is
  eliminated in the document and **unaffected, live, and reachable** in the
  code. Calling F1 "repaired" without this caveat overstates what changed.

### 3.4 Fresh evidence

`tests/test_n16_5_f5_tb_prov_repair_iv.py` (14/14 pass), specifically:

- `test_LOAD_BEARING_source_still_implements_removed_vocabulary`
- `test_LOAD_BEARING_store_adapter_still_dispatches_configure_privileged_helper_through_h`
- `test_LOAD_BEARING_operations_handler_accepts_provisioning_mutation_from_h`
- `test_predecessor_source_impact_map_did_not_flag_this`

These tests are **expected to pass today** (they document the live defect)
and are designed to **start failing** once a future repair phase removes
both mutation ids from `CLOSED_ADMIN_MUTATIONS` and the store-adapter/
operations dispatch branches — at which point that future phase, not this
IV, must retire or rewrite this test module (out of this IV's scope per
§21/§25 — no production change is authorized here).

---

## 4. PAWA direct-dispatch trust boundary (§8 of phase-authorization) — adversarially reviewed at the contract-text level

Reviewed against the contract text only (no implementation exists to attack
directly — the standalone script `scripts/hpac_pawa_helper_admin.py` named
by REQ-345 does not exist in the repository; confirmed by
`git ls-files -- scripts/ | grep -i helper_admin` returning nothing beyond
the unrelated `hpac_certification_admin.py` / `hpac_principal_admin.py` /
`hpac_protected_presentation_admin.py` / `hpac_protected_root_admin.py`).

- **Trust anchor:** REQ-345 mints the capability via "the existing
  production writer-mint path (HPAC-PAWA-001 §36-§38... pre-v2.0
  in-process mint)" — the same trust root as every other PAWA `PRODUCTION`
  capability (§4/REQ-010: OS filesystem write authority on the
  out-of-band-provisioned protected root). **No second trust root
  introduced** — REQ-352 says this explicitly and the mechanism supports it.
- **Not a generic broker:** the capability is scoped by contract text to
  exactly one mutation family, subject, and transaction id (REQ-345); this
  matches PAWA-INV-15's process-local/non-bearer/single-use discipline,
  narrowly exempted (not broadened) for exactly two named mutations,
  mirroring PPA's own pre-existing exemption for
  `configure_presentation_mechanism`.
- **Configured-agent exclusion (REQ-350):** explicitly requires the
  helper-admin script's OS process principal to be the deployment owner and
  explicitly excludes the configured agent principal, "an ordinary PCAE
  agent process," and H itself (current, retired, or successor) from ever
  being eligible executors — text-level coverage is present and matches
  the REQ-192/193 resolution discipline already frozen elsewhere.
- **No path/hash-as-provenance defect found in text:** REQ-345/346 bind
  bytes via out-of-band installation plus the capability, not via a
  path-existence or digest-only check; REQ-349's crash/replay handling is
  explicit and fail-closed with no automatic retry.

**Because no script implementation exists yet, this section's coverage is
necessarily contract-text-only.** It cannot and does not certify runtime
behavior (arbitrary-argv/env-injection/TOCTOU/symlink-substitution attacks
require an implementation to attack). This gap is inherent to IV timing
(implementation has not begun) and is not itself a blocking defect — the
phase-authorization explicitly forbids implementing anything here.

---

## 5. Model I-B / configured-agent exclusion / platform — spot-checked, no regression found

- `hpahi`/`hpawi`/`hppi` disjoint grammar: unchanged by this contract set
  (§30E/§98 are additive sections; §30D's REQ-172/174 typed grammar is
  explicitly stated as "remains in force" in both contracts' header
  blocks).
- Configured-agent exclusion: REQ-350 reuses REQ-192/193's live-resolution
  predicate verbatim (no `os.geteuid()`, no env var, no argv), consistent
  with the mandatory-fail-closed discipline elsewhere in PAWA.
- Platform: no macOS/Linux-specific claim is added by §98/§30E; the
  still-open `hpac_foundation.py` configured-agent-vs-live-process
  read/write boundary gap (from N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL)
  is untouched and remains a **separate**, already-known, already-recorded
  prerequisite — this IV does not reopen it (phase-authorization §29).

No new defect found in this area; not re-litigated further per phase scope.

---

## 6. Fast Green / regression attribution

- **Baseline:** `93580bc470bb0053fff6b7ac8ba1fc644b15e65c` (origin/main HEAD
  at IV phase entry, verified `git rev-parse HEAD` == `git rev-parse
  origin/main`, worktree clean, `origin/main..HEAD` empty at entry).
- **Candidate:** baseline + exactly two new files this IV adds
  (`tests/test_n16_5_f5_tb_prov_repair_iv.py`, this evidence document) plus
  governance bookkeeping (`PROJECT_STATUS.md`, `tasks/**`, `.pcae/**`,
  `CHANGELOG.md`). **Zero `src/pcae/**` bytes changed; zero
  `docs/contracts/**` bytes changed.**
- **Method:** because the candidate's only executable-test-relevant diff is
  one new, additive test file, the candidate-vs-baseline attribution is by
  direct construction rather than a `git stash` round-trip: every test that
  fails on the candidate and is not in the new file is, by definition,
  identical to a baseline failure (the new file cannot affect any other
  file's collection or execution — verified: no shared fixtures, no
  monkeypatching, no `conftest.py` change).
- **Full `helper|pawa|ppa|hpac`-keyword sweep:** 85 failed, 1881 passed, 37
  skipped (`tests/` -k "helper or pawa or ppa or hpac"). All 85 failing
  node ids are outside `tests/test_n16_5_f5_tb_prov_repair_iv.py` (grep
  confirms zero matches). This 85-failure count and composition matches the
  predecessor's own independently-reproduced count (their §0 primary-
  operator review: "85 failed / both" baseline and candidate), i.e. these
  are the same pre-existing historical-snapshot version-pin failures
  (contract-version-string assertions that pin now-superseded v1.3/v1.4/
  v2.0-era strings — e.g. `test_01_pawa_contract_version_is_v1_4`,
  `test_04_contract_version_is_v1_3`, `test_18_contract_bytes_unchanged`)
  — expected churn from the v3.0→v4.0 / v4.0→v5.0 MAJOR bumps two phases
  ago, not attributable to this IV's diff.
- **This IV's own new/edited test files:**
  `tests/test_n16_5_f5_tb_prov_repair_iv.py` — 14/14 pass.
  `tests/test_n16_5_f5_tb_prov_repair_contract.py` (predecessor's, run
  unmodified) — pass (confirmed via full-module run alongside
  `test_hpac_pawa_helper_writer_authority_contract_v2.py` /
  `test_hpac_pawa_helper_protocol_foundation.py`: 113 passed, 1 skipped).

**Zero attributable regressions from this IV's diff.**

---

## 7. Verdicts (phase-authorization §28 required list)

| Item | Verdict |
|---|---|
| Predecessor contradiction | Adjudicated: no contradiction present; activating-prompt framing conflated two distinct phases' dispositions (§1) |
| Predecessor commit/finalization chain | Reconstructed and confirmed (see §6; entry baseline `93580bc4` == origin/main == HEAD, clean) |
| Fast Green baseline/candidate | Real, direct-construction attribution; zero attributable regressions (§6) |
| Current contract versions | HELPER v5.0 (189 decl.) / PAWA v4.0 (352 decl.) / PPA v2.1 unchanged — independently confirmed |
| F1-A (bootstrap circularity) | **Contract text: eliminated.** Production source: NOT eliminated — live, reachable, unrepaired (§3) |
| F1-B (self-lineage/rotation) | **Contract text: eliminated.** Production source: NOT eliminated — same mechanism, same finding (§3) |
| Model P-D | Sound at the contract-text level; trust boundary non-circular in text (§4); cannot be verified at runtime because no implementation exists |
| PAWA direct-dispatch provenance | No second trust root, narrowly scoped, text-level only (§4) |
| PPA reuse | Valid — structurally identical requirement shapes, not mere analogy (§2) |
| Model I-B | Unchanged, no regression found (§5) |
| Model E preservation | Intact; `configure_privileged_helper` never was a Model E family (§2) |
| Configured-agent exclusion | Mandatory, coherent, unchanged predicate reused (§5) |
| Foundation dependency | Untouched, separate, already-known (§5) |
| Platform | No new claim; deferred items unchanged (§5) |
| No-go confirmations | No `src/pcae/**` byte changed; no `docs/contracts/**` byte changed; no live host state touched; no implementation begun |
| N-16-5 state | **NOT CLOSED** |
| N-16-6/N-16-7 | Untouched |
| Runtime state | Observed / observe / unavailable; 0 plugins / 0 capabilities; first external effect ABSENT |

---

## 8. Disposition and recommended next phase

**COMPLETE — NOT VERIFIED / BLOCKED.**

Reason: the contract-text repair of F1 is independently confirmed sound,
but it has not been propagated to the already-existing, already-wired
production source that implements the very mechanism F1 describes. The
circular, self-lineage-violating `configure_privileged_helper` dispatch
route through H's own `admin_mutation` handler remains live in
`src/pcae/core/hpac_pawa_helper_protocol.py` (enum),
`hpac_pawa_helper_store_adapter.py` (dispatch branch), and
`hpac_pawa_helper_operations.py` (handler acceptance). Until that source is
brought into conformance with HELPER v5.0 §30E / PAWA v4.0 §98, F1 remains
practically exploitable in the deployed system regardless of the frozen
contract text.

**Smallest recommended contract-repair-adjacent successor (per §24 — not
begun by this phase):** a narrow, source-only conformance-repair phase that
removes `configure_privileged_helper` and `configure_presentation_mechanism`
from `CLOSED_ADMIN_MUTATIONS` in `hpac_pawa_helper_protocol.py` and deletes
the now-forbidden dispatch branches in `hpac_pawa_helper_store_adapter.py`
/ `hpac_pawa_helper_operations.py`, bringing already-existing source into
byte-level conformance with the already-frozen HELPER v5.0 / PAWA v4.0
contract text. This is narrower than implementing REQ-345-350's new
standalone-script dispatch path (which remains a separate, larger,
not-yet-authorized implementation phase) — it is strictly a *removal* of
dead-per-contract code paths from an *existing* module, requiring its own
governed authorization and its own independent verification before any
`scripts/hpac_pawa_helper_admin.py` implementation phase begins.

N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched. The separate,
already-known `hpac_foundation.py` configured-agent-vs-live-process
write-boundary gap (from N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL) is
unaffected by this IV and remains open.
