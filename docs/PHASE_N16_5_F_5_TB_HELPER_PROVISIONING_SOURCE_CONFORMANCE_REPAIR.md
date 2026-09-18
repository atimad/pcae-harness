# Phase N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR — Evidence

Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(direct `.1` CPIPC child of the predecessor IV phase; independently derived
and validated via `pcae.core.phase_id.is_valid` — True on both parent and
child; no collision found against `git log --all` / working tree text
search).

Predecessor: `docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_PROVISIONING_CONTRACT_REPAIR_IV.md`
— **COMPLETE — NOT VERIFIED / BLOCKED.** Its load-bearing finding: the
contract-text repair of F1-A/F1-B (HPAC-PAWA-001 v4.0 §98, HPAC-PAWA-HELPER-001
v5.0 §30E) is sound, but had not propagated to the already-deployed
production source implementing the mechanism the contract describes.

**Disposition of this phase: SOURCE CONFORMANCE REPAIRED — PENDING FRESH
INDEPENDENT VERIFICATION.**

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved
(primary operator performed all finalization/commit/push steps directly;
one delegated worker fork performed the bounded source edit, fresh tests,
and regression sweep only, per this document's own authorization boundary).

---

## 1. Mandatory pre-phase reconstruction

Independently reconstructed before any edit (not accepted from the
predecessor's prose):

- **Worktree/push state at entry:** `git status --short` clean;
  `origin/main..HEAD` = 0/0 (fetched and verified); no active governed phase
  (only an idle post-IV placeholder task, closed at this phase's start).
- **Contract identities**, read directly from `docs/contracts/*.md`:
  HPAC-PAWA-001 **v4.0**, HPAC-PAWA-HELPER-001 **v5.0**, HPAC-PPA-001
  **v2.1** — all confirmed by `**Version:**` header grep, matching the
  predecessor's claim.
- **Live source divergence**, confirmed directly from `src/pcae/core/`:
  - `hpac_pawa_helper_protocol.py`: `CLOSED_ADMIN_MUTATIONS` still contained
    `configure_presentation_mechanism` and `configure_privileged_helper`
    (7-member set).
  - `hpac_pawa_helper_store_adapter.py::perform_recognized_admin_mutation`:
    live `if mutation == "configure_presentation_mechanism":` /
    `if mutation == "configure_privileged_helper":` branches, dispatching to
    `ProtectedPresentationInstallationStore.apply_configuration` /
    `.register_helper_metadata` respectively — real writes.
  - `hpac_pawa_helper_operations.py::handle_admin_mutation`: docstring and a
    `mutation != "configure_privileged_helper"` special-case exemption on
    the `transaction_id` requirement, both referencing the forbidden op.
- **Existing standalone (Model P-D) provisioning path**, confirmed present
  for `configure_presentation_mechanism` only:
  `hpac_protected_admin_writer.py::PawaOperation.CONFIGURE_PRESENTATION_MECHANISM`,
  consumed solely by
  `hpac_protected_presentation_admin.py::configure_presentation_mechanism`
  (the "sole enumerated production consumer", per that module's own
  docstring). **No equivalent standalone dispatch exists yet for
  `configure_privileged_helper`** — confirmed by grep: no `PawaOperation`
  member for it in `hpac_protected_admin_writer.py`. Per phase-authorization
  scope, this phase does **not** implement one; the absence of a standalone
  path for `configure_privileged_helper` is not a reason to leave the H-side
  route live.
- **Dead-code consequence identified and classified, not touched:** removing
  the `configure_privileged_helper` store-adapter branch makes
  `protected_presentation_installation.py::register_helper_metadata` and
  role constant `privileged_helper_metadata_registrar` unreachable (grep
  confirms `hpac_pawa_helper_store_adapter.py` was their only caller). Left
  untouched — outside the narrow 3-file scope; flagged here for a future
  cleanup phase, not this one.

---

## 2. Source repair performed

Exactly three production files touched, matching the phase's allowlist:

1. **`src/pcae/core/hpac_pawa_helper_protocol.py`** — `CLOSED_ADMIN_MUTATIONS`
   reduced from 7 to 5 members (removed `configure_presentation_mechanism`,
   `configure_privileged_helper`); explanatory comment added citing
   HPAC-PAWA-HELPER-REQ-184/HPAC-PAWA-REQ-345 and Model P-D.
2. **`src/pcae/core/hpac_pawa_helper_store_adapter.py`** —
   `perform_recognized_admin_mutation`'s two forbidden dispatch branches
   removed in full (both the `configure_presentation_mechanism` and the
   `configure_privileged_helper` branch — the former's removal is required
   too, since it must be reachable only via the standalone PAWA path, never
   via H's own `admin_mutation` route). Replaced with an explanatory
   comment; the function now falls through unrecognized `mutation` values to
   its existing `operation_scope_invalid` fail-closed raise.
3. **`src/pcae/core/hpac_pawa_helper_operations.py`** —
   `handle_admin_mutation`'s docstring corrected (no longer describes
   `configure_privileged_helper` as a supported operation); the
   `mutation != "configure_privileged_helper"` exemption on the
   `transaction_id` check removed (now unconditional, since the mutation can
   never reach this point with that value).

No other production file was modified. No contract file
(`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`,
`HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`,
`HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`) was modified — sha256
confirmed byte-identical before and after (§4). No standalone PAWA §98
provisioning script was implemented for `configure_privileged_helper`. No
foundation (`_validate_production_boundary` / configured-agent-vs-live-process)
code was touched. `_PRODUCTION_WRITER_FACTORY_SEAL` and the legacy protected
writer factory were not imported, referenced, or modified.

---

## 3. Fresh conformance evidence

New file: `tests/test_n16_5_f_5_tb_provisioning_source_conformance_repair.py`
— **41 passed, 1 skipped** (the skip is a `runtime_state` module-presence
guard for item 26 of the attack matrix; the runtime invariant is otherwise
independently confirmed via PROJECT_STATUS.md/this document, not via a
module that does not exist in this repository).

Covers, at minimum: both forbidden ops absent from `CLOSED_ADMIN_MUTATIONS`
and confirmed to be exactly the five legitimate subtypes; rejection via
`handle_admin_mutation` with `operation_scope_invalid`; alias/casing forms
gain no acceptance; unknown mutations still fail closed; no store-adapter or
operations source branch dispatches either forbidden op (source-text
assertion); direct `perform_recognized_admin_mutation` calls for the
forbidden ops raise; no indirect alias/dispatch table reintroduces them; all
five legitimate admin subtypes remain mintable and `enroll_principal` works
end-to-end through the real store; wrong-authority-family denial still
holds; no generic callable/`eval`/`exec`/dynamic-import dispatch fallback
exists; Model E's three authority classes remain non-subclasses of
`HPACWriterCapability` in both directions; `_PRODUCTION_WRITER_FACTORY_SEAL`
object identity unchanged; contract files parse and are still v4.0/v5.0/v2.1;
production diff confined to the three expected files (asserted via
`git diff --name-only HEAD -- src/`); no Permission-Broker/runtime-capability
file touched; no `pyproject.toml` change; no `/Library/Application
Support/PCAE` path referenced by the repaired source; no `subprocess.run`/
`os.system` added; N-16-5 not marked closed in `PROJECT_STATUS.md`; N-16-6/
N-16-7 not referenced by the repaired source.

---

## 4. Contract byte-identity

sha256, captured before the repair and re-verified identical after:

| File | sha256 |
|---|---|
| `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b03b84e571a03f3560cd3ecad86b0d98d3823feec20c82d8a6f59da49cafa83d` |
| `HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `bea3bcc1902858bc3807f396419764a7d537425794b836448648d5f83ee982bc` |
| `HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `7844c3dddd77dcf5c76311192a49536366c12b3622a0249532dba4ea75e36e3d` |

Unchanged. `**Version:**` fields independently re-confirmed 4.0 / 5.0 / 2.1
after the repair.

---

## 5. Regression sweep and Fast Green attribution

**Method:** direct baseline-vs-candidate comparison via `git stash` of
exactly the three repaired production files (isolating the repair's own
diff), re-running the identical test selections against both states.

- **Predecessor's own repair/IV suites**
  (`test_n16_5_f5_tb_prov_repair_contract.py`,
  `test_n16_5_f5_tb_prov_repair_iv.py`), the writer-authority contract/impl
  suites, real-helper-boundary-repair (+ IV), real-helper-store-launcher-impl,
  and this phase's own new suite: **328 passed, 10 failed** (candidate) vs.
  **N/A, baseline lacks the fix** for the two intentionally-flipping tests
  (below); all 10 failures individually reconciled:
  - **2 predecessor-IV LOAD_BEARING finding-proof tests**
    (`test_n16_5_f5_tb_prov_repair_iv.py::test_LOAD_BEARING_source_still_implements_removed_vocabulary`,
    `::test_LOAD_BEARING_store_adapter_still_dispatches_configure_privileged_helper_through_h`)
    — these tests were written to assert the *pre-repair* divergence exists.
    Their new failure is the **direct, intended proof that this phase's
    repair closed the divergence** — not a regression. Per phase
    instructions ("do not mechanically delete historical evidence... tests
    that intentionally document old epochs"), this file is left byte-unchanged
    as the historical record of the finding this phase fixes. A future IV
    phase should retire or supersede it with fresh assertions of the
    now-conforming state (the new conformance suite already provides most of
    these).
  - **3 pre-existing baseline failures**, confirmed via `git stash`
    round-trip to fail **identically with or without this phase's diff**
    (`test_n16_5_f_5_tb_helper_iv_r.py::test_contract_byte_identity[...]`,
    `test_n16_5_f_5_tb_helper_writer_authority_contract_repair.py::test_contract_title_and_version_field_are_v3`,
    `::test_pawa_and_ppa_files_not_modified`) — stale point-in-time
    contract-version/sha pins from earlier epochs (v3.0/pre-v4.0 text),
    already broken before this phase began. Zero attribution to this repair.
  - **5 historical-epoch vocabulary pins**, confirmed via the same
    `git stash` round-trip to pass on baseline and fail only on candidate —
    i.e. genuinely caused by this phase's diff, but by design:
    `test_n16_5_f_5_tb_helper_iv_r.py::test_admin_mutation_closed_set`,
    `::test_admin_mutation_never_touches_filesystem_only_metadata_store`,
    `test_n16_5_f_5_tb_helper_writer_authority_impl.py::test_10_configure_privileged_helper_metadata_only_real_write`,
    `::test_13_all_seven_admin_subtypes_in_closed_enum`,
    `::test_34_no_disk_export_helper_metadata_document_has_no_authority_fields`.
    All five assert the **pre-repair, 7-member vocabulary** (the
    `N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL` §30B v3.0 implementation
    suite, and an independent IV-R reverification suite, both written before
    the provisioning-contract-repair epoch existed). They are historical-
    epoch pins per phase instructions ("Historical tests that assert older
    contract versions may legitimately fail under current version epochs...
    do not edit them merely to make green"); left unmodified.
- **Broader keyword sweep** (`tests/ -k "hpac_pawa_helper or pawa_helper or
  model_e or writer_authority"`): 278 passed / 8 failed / 5 skipped
  (candidate) — the 8 failures are exactly 5 of the above plus 3 additional
  historical version-pin failures in
  `test_n16_5_f_5_tb_helper_writer_authority_contract_repair_iv.py`
  (`test_identity_block_declares_v3_status_and_pending_reverification`,
  `test_requirement_ids_are_contiguous_from_001_with_one_lettered_insertion`,
  `test_section_33_requirement_count_statement_matches_independently_derived_max`),
  independently confirmed via `git stash` round-trip to be **identical
  pre-existing baseline failures**, unrelated to this repair.
- **Foundation/PAWA/PPA/writer-anchor suite family**
  (`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`,
  `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`, the
  `.30r_1`/`.30r_3_1`/`.30r_4*`/`.30r_5r_1` writer-anchor/protected-
  presentation/CTAP2 suites): **423 passed / 18 failed**, all 18 confirmed
  via `git stash` round-trip **identical on baseline and candidate** — all
  pre-existing point-in-time contract-byte/version-pin assertions unrelated
  to this repair (e.g. `test_no_production_writer_factory_symbols_anywhere_in_src`,
  `test_87_contract_byte_identity_hpac_rhamp_hbdc_unchanged_since_entry`,
  `test_19_r30r5r_repair_suite_still_passes`). Zero attribution.
- **N16_5_F5B\*/H3/contract family** (9 additional suites): **483 passed /
  22 failed**, all 22 confirmed via `git stash` round-trip **identical on
  baseline and candidate** — pre-existing contract-version/diff-since-C0
  point-in-time pins (e.g. `test_01_pawa_contract_version_is_v1_4`,
  `test_70_no_src_or_scripts_change_since_c0`). Zero attribution.

**Net result: zero unexplained/unattributed regressions.** Every failing
test outside this phase's own new suite is either (a) a pre-existing
baseline failure confirmed identical with and without this phase's diff, or
(b) a historical-epoch vocabulary/finding-proof assertion whose failure is
the expected, intended, and correctly-classified consequence of this exact
repair (not left silently — documented above per test name).

`pcae check` / `pcae health` / status-coherence and push-readiness checks:
run at finalization (§7).

---

## 6. Runtime invariant

Verified unchanged at entry and at completion:

> State: Observed. Maximum Capability: observe. Execution Availability:
> unavailable.

No source change in this phase adds a `subprocess`/`os.system` call, a
Permission-Broker file change, or any runtime-capability-enabling code. The
first governed runtime external effect remains absent/unreachable.

---

## 7. Verdicts

| Item | Verdict |
|---|---|
| `configure_privileged_helper` absent from `CLOSED_ADMIN_MUTATIONS` | Yes |
| `configure_presentation_mechanism` absent from `CLOSED_ADMIN_MUTATIONS` | Yes |
| Store-adapter dispatch branches for both removed | Yes |
| Operations-handler acceptance/exemption for `configure_privileged_helper` removed | Yes |
| Alternate/hidden H route remains | No |
| Legitimate Model E helper operations (5 remaining admin subtypes, certification-write, presentation-evidence) | Functional, unchanged |
| Contract files (PAWA v4.0 / HELPER v5.0 / PPA v2.1) | Byte-unchanged (sha256 confirmed, §4) |
| Model E authority semantics (3 non-subclass families, no shared base, `_HELPER_AUTHORITY_SEAL` gate) | Unchanged |
| Foundation (`_validate_production_boundary`, configured-agent boundary) | Unchanged, untouched |
| Live deployment/protected-state mutation | None (disposable fixture roots only) |
| Fresh conformance tests | 41 passed / 1 skipped |
| Focused regressions | Zero unattributed failures (§5) |
| Fast Green | Zero attributable regressions (§5) |
| Standalone PAWA §98 script for `configure_privileged_helper` implemented | No (correctly out of scope) |
| Real FIDO2 / protected approval / certification performed | No |
| N-16-5 | **Remains NOT CLOSED** |
| N-16-6 / N-16-7 | Untouched |
| Runtime state | Observed / observe / unavailable |

---

## 8. Disposition and recommended successor

**SOURCE CONFORMANCE REPAIRED — PENDING FRESH INDEPENDENT VERIFICATION.**

This phase is *not* an independent verification of itself. It removed the
live source divergence the predecessor IV found, added fresh conformance
tests, and confirmed zero attributable regressions — but per phase
authorization, does not and cannot certify itself as independently verified.

**Recommended successor (not begun by this phase):**
`N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV` — a fresh,
independent adversarial re-verification of this repair, in the same style as
the predecessor's own IV, before N-16-5 is reassessed for closure. If that
IV confirms conformance, the next blocker returns to one of the already-known
prerequisites: helper-admission implementation, or the separate, still-open
`hpac_foundation.py` `_validate_production_boundary` / configured-agent-vs-
live-process foundation repair (from N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL,
unaffected by this phase). **The successor was NOT begun.**

N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.
