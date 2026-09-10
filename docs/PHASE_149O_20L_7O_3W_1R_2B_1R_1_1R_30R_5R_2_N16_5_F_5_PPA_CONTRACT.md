# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1 (alias N16-5-F-5-PPA-CONTRACT) — HPAC-PPA-001 Contract Evolution: Out-of-Process Presentation-Evidence Writer Ownership Alignment

**Status: COMPLETE — CONTRACT FROZEN.**
**HPAC-PPA-001 evolved v1.0 → v2.0 (MAJOR, HPAC-PPA-REQ-069).**
**The N16-5-F-5-TB-CONTRACT-IV blocking finding (evidence-writer-delivery
adjudication option B) is resolved at contract level.**
**F-5-B2: BLOCKED PENDING CONTRACT IV + IMPLEMENTATION. F-5: CERTIFICATION
BLOCKED. N-16-5: NOT CLOSED. N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly
last).**

This is a **contract-only** governed phase. It evolves one frozen contract
(`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`) in place,
reconciles downstream point-in-time guards (widen-not-weaken), and adds one
contract-verification test suite. It implements **no** helper executable,
launcher, IPC channel, or evidence write; it removes **no** in-process code; it
mutates **no** `src/pcae`, `scripts`, `pyproject.toml`, or `schemas` file; it
mutates **no** protected host state; it performs **no** ceremony. Runtime
posture is unchanged throughout: `not_implemented` / `Observed` / `observe` /
`unavailable` / 0 plugins / 0 capabilities; the first governed runtime external
effect remains **ABSENT / UNREACHABLE**.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved. No
delegated worker performed any part of this phase.

---

## 0. Governance / phase identity

### 0.1 Repository state at phase entry

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `8c0e2e0a15df72a2329b056afc0dea2fad391495` |
| `origin/main` | `8c0e2e0a15df72a2329b056afc0dea2fad391495` (identical) |
| `origin/main..HEAD` | 0 commits |
| Working tree | clean at entry |
| Conflicting active governed phase | none — only the idle placeholder `20260910-1129-idle-post-n16-5-f-5-tb-contract-iv-blocked-…` |
| Governed task-transition commit opening this phase | `f0ca3423ece0a54052dd1195f5c889865eb19c3d` (this is the test-suite baseline SHA `ENTRY`) |

### 0.2 Predecessor

| Field | Value |
|---|---|
| Alias | **N16-5-F-5-TB-CONTRACT-IV** |
| Canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1` (50 subphase segments) |
| Predecessor completion — canonical artifacts | `PROJECT_STATUS.md` "## Current Phase" **STATUS: N16-5-F-5-TB-CONTRACT-IV COMPLETE — NOT VERIFIED / BLOCKED**; `.pcae/phase-completion-metadata.json` `status = "blocked"` (terminal), `phase_id` matches; `.pcae/phase-completion-report.md` staging header matches; governed done task `tasks/done/20260910-1119-phase-…-n16-5-f-5-tb-contract-iv.md`; canonical report `.pcae/phase-reports/20260910-093110-…1.1.1.1.1.md` |
| Predecessor verdict | **NOT VERIFIED / BLOCKED** — the mandatory HPAC-PPA-001 evidence-writer-delivery adjudication resolves to **option B**: HPAC-PAWA-HELPER-001 v1.0 §17 (HPAC-PAWA-HELPER-REQ-070) and HPAC-PAWA-001 v2.0 §42B note freeze `presentation_evidence_write` as *invoked by the HPAC-PPA-001 presentation helper itself*, materially conflicting with HPAC-PPA-001 v1.0 HPAC-PPA-REQ-041 / -052 / -054 and PPA-INV-2. Every other IV criterion was independently established. A fresh governed HPAC-PPA-001 contract-evolution phase is the required successor. |
| CPIPC validation | **VALID** — see §0.3 |

### 0.3 CPIPC-valid successor derivation

Independently derived via `pcae.core.phase_id`, **not** taken from any
precomputed value in the authorizing prompt.

| Check | Result |
|---|---|
| Canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1` |
| `pcae.core.phase_id.is_valid` | `True` |
| `normalize(id) == id` | `True` (exact canonical representation) |
| Same series / branch as predecessor | `149` / `O` — `same_series` and `same_branch` both `True` |
| Strict ordering | `compare(pred, child) == "less"` |
| Exactly one appended segment | child has 51 subphase segments vs predecessor 50; appended segment is `(1, "")` = `.1` |
| Uniqueness — full git history | `git log --all --pretty=%s` count of the trailing token `…1R.1.1.1.1.1.1 (` = **0** |
| Uniqueness — `docs/` `tasks/` `.pcae/` | no file contains the child ID (nor the child + `.1`) |
| Conflicting active governed phase | none |
| Alias | **N16-5-F-5-PPA-CONTRACT** — display only; contains no `<digit><letter>` token (CPIPC alias-token trap) |

---

## 1. Authoritative predecessor finding (re-established from primary text)

HPAC-PPA-001 **v1.0** (`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`,
FROZEN by phase `…30R.4R`, requirement bodies `HPAC-PPA-REQ-001..076`,
`PPA-INV-1..8`) states, verbatim:

- **HPAC-PPA-REQ-041** — the evidence authority is a seal-guarded,
  process-local, non-serializable, non-copyable, restart-dead, single-use
  `HPACWriterCapability` (or repository-equivalent use of the same existing
  capability/provenance primitive), *"held only by the trusted launcher
  mediator. It is never sent to the helper or requesting caller."*
- **HPAC-PPA-REQ-052** — the expected production modules include
  `pcae.core.protected_presentation` as *"sole launcher/mediator **and
  evidence-writer issuer**"*, a module distinct from the packaged helper
  `pcae.protected_presentation_helper`.
- **HPAC-PPA-REQ-054** — *"Evidence producer is only the launcher mediator
  after a response from the verified helper."*
- **PPA-INV-2** — *"Installer, launcher, helper response, and evidence writer
  are distinct trust actions with no authority transfer."* (four distinct
  actions; the wording implies distinct process / holder.)
- **HPAC-PPA-REQ-069 / REQ-070** — MAJOR.MINOR versioning. MAJOR triggers
  include making evidence authority bearer/durable/reusable, allowing
  caller-selected writer, merging PAWA and runtime evidence authority, or
  transferring authority. MINOR permits *"add a platform adapter within these
  exact properties, tighten a bound, or add a failure mapping without
  remeaning an existing outcome"*, and *"No version may retrospectively widen
  an issued capability…"*.

Against **HPAC-PAWA-HELPER-001 v1.0 §17 / HPAC-PAWA-HELPER-REQ-070**:
`presentation_evidence_write` is *"invoked **by the HPAC-PPA-001 presentation
helper itself**, post-ceremony, after one valid `APPROVE` response"* — and
**HPAC-PAWA-001 v2.0 §42B note** makes `mint_protected_presentation_evidence_writer`
*become* that helper operation. HPAC-PAWA-HELPER-001 §17's cross-contract note
explicitly defers the reconciliation to this phase.

---

## 2. Version classification — independent adjudication

**Result: MAJOR (v1.0 → v2.0).**

Moving the presentation-evidence-writer holder from the trusted launcher
mediator into the verified helper process, and collapsing two of PPA-INV-2's
four distinct trust actions (helper response + evidence writer) into one
process, **restructures authority ownership**. This is not within
HPAC-PPA-REQ-070's MINOR permits:

- REQ-041's parenthetical *"or repository-equivalent use of the same existing
  capability/provenance primitive"* governs **which primitive** implements the
  authority, **not which component holds it**.
- REQ-070's *"add a platform adapter within these exact properties"* cannot
  carry a change to who the authority holder is.

The direction is the correct security direction — the authority moves
**further** from the agent interpreter, never onto a heap shared with
attacker-controlled code — but v1.0 as frozen does not authorise it, so a new
**MAJOR** is required. v2.0 **widens nothing** issued under v1.0.

This matches the predecessor IV's own adjudication ("MAJOR-class under
HPAC-PPA-REQ-069") and was re-derived here from the primary REQ-069 / REQ-070
text.

---

## 3. The v2.0 normative delta

All of v2.0 lives in the appended header evolution record, the `(v2.0) §N note.`
blockquotes on §8 / §10 / §14, the re-derived `PPA-INV-2 (v2.0)` and new
`PPA-INV-9..12`, the new §21 (`HPAC-PPA-REQ-077..103`), the §21A delta table,
and the §22 v2.0 freeze verdict. Every v1.0 requirement body is
**byte-verbatim** (verified — see §5).

### 3.1 Evidence-producer disposition

| Question | v1.0 | v2.0 |
|---|---|---|
| Who produces `HPAC-PRESENTATION-EVIDENCE/2.0`? | the launcher mediator, after a helper response (REQ-054) | the **verified protected presentation helper process** that conducted the ceremony, after one valid `APPROVE` (**HPAC-PPA-REQ-077**) |
| Who holds the write authorization? | the launcher mediator; never sent to the helper (REQ-041) | process-local **to the helper**; performed inside the helper process; **no returnable writer** (**HPAC-PPA-REQ-078 / -079**, §8 note) |
| What is `pcae.core.protected_presentation`'s role? | sole launcher/mediator **and evidence-writer issuer** (REQ-052) | sole launcher / mediator **only**; the evidence-write is a **protected-side-internal operation of the helper process** — never minted / returned / serialised / delivered (**HPAC-PPA-REQ-081**, §10 note) — option C of the phase authorisation §17 |
| What crosses the helper boundary? | (v1.0: writer held launcher-side) | **only typed evidence / result / a protected-root-relative evidence reference** — no capability / handle / seal / reconstructable descriptor (**HPAC-PPA-REQ-078 / -082 / -087**, `PPA-INV-9`) |

### 3.2 PPA-INV-2 re-derivation

`PPA-INV-2 (v2.0)` — installation configuration, launcher mediation, protected-UI
rendering, human election capture, presentation-evidence persistence, and the
helper's typed response remain **distinct trust actions with separate
preconditions, outputs and failure states and no authority transfer**, **even
when several are performed by the same verified protected helper process**. None
implies any other authority; there is no automatic promotion between them. The
v1.0 four-action wording is preserved; only the implicit separate-process /
separate-holder reading is removed. (**HPAC-PPA-REQ-083**.)

### 3.3 New invariants

- **PPA-INV-9** — no evidence-writer object / capability / handle / seal /
  reconstructable descriptor crosses any process boundary (PAWA-INV-15/16 /
  PAWAH-INV-1 alignment); only typed evidence leaves the helper; the
  authorization is gone at helper exit.
- **PPA-INV-10** — the helper authoring evidence is the **same**
  integrity-verified one-shot protected helper object/process that conducted
  the ceremony (§6 / §29 / §30 / HPAC-PPA-REQ-088); a validate-one-run-another
  split fails closed; helper hash / path / registration metadata ≠ trust root.
- **PPA-INV-11** — typed evidence / result / acknowledgement is not privileged
  authority; a lost response is not proof no evidence exists and never frees a
  spent one-shot; once the evidence-write attempt boundary is crossed there is
  no auto-retry, only reconciliation against protected-root canonical evidence.
- **PPA-INV-12** — HPAC-PPA-001 defines valid presentation evidence and valid
  human election; HPAC-PAWA-HELPER-001 §17 carries the `presentation_evidence_write`
  bytes; neither confers the other's authority; no circular trust.

### 3.4 Walls preserved verbatim

`APPROVE` / `REJECT` from the actual protected interaction only; `approved=true`
request field never creates approval; YubiKey touch = UP ≠ approval; peer
credential ≠ human identity ≠ human approval (**HPAC-PPA-REQ-093**). Presentation
evidence ≠ authentication proof; `APPROVE` ≠ authenticated principal; human-auth
proof still requires its own RHAMP / HPAC chain; the helper does not become the
real-authentication verifier by being the evidence producer (**HPAC-PPA-REQ-094**).
Presentation evidence write ≠ Gate 5 ALLOW ≠ PB permission ≠ runtime capability ≠
execution; no runtime / plugin capability, `DispatchEnvelope`, Gate 6+ authority,
adapter admission, or external-effect permission (**HPAC-PPA-REQ-095**).

### 3.5 Provenance / trust root / freshness / failure model

- **HPAC-PPA-REQ-088** — same verified helper object/process (open-no-symlink,
  type/link/owner/mode/ACL, SHA-256 == `helper_sha256`, same opened file object
  exec or **STOPS BLOCKED**); the single trust root is **unchanged** (OS
  filesystem write authority on the out-of-band protected root); **no second
  trust root**.
- **HPAC-PPA-REQ-089** — private one-shot channel, OS-authenticated
  deployment-owner peer, fail closed before the protected operation; peer
  authentication is infrastructure evidence only.
- **HPAC-PPA-REQ-090** — no trusted evidence for an expired / consumed
  ceremony, wrong session / subject, replayed request, stale installation
  generation, or mismatched mechanism; a response loss never makes a consumed
  ceremony reusable.
- **HPAC-PPA-REQ-091 / -092** — seven-state model
  (`CEREMONY_REQUEST_RECEIVED` → … → `EVIDENCE_WRITE_ATTEMPT_STARTED` (the
  no-auto-retry boundary) → `EVIDENCE_COMMITTED` → `RESPONSE_EMITTED`); a
  missing response is not proof no evidence exists; reconcile against
  protected-root canonical evidence, never resend a spent one-shot.

### 3.6 Scope / neutrality

- **HPAC-PPA-REQ-096** — mechanism neutrality preserved; current
  `pcae-protected-local-presentation` remains a supported profile; a future
  mobile-only / passkey / protected-mobile approval profile remains possible.
- **HPAC-PPA-REQ-097** — **NO SCHEMA CHANGE REQUIRED** —
  `HPAC-PRESENTATION-EVIDENCE/2.0`, `HPAC-PRESENTATION-INSTALLATION/1.0`,
  `HPAC-PRESENTATION-CURRENT-GENERATION/1.0`, `HPAC-WRITER-PROVENANCE/1.0`
  already express every needed field; producer process location is verification
  state, not an evidence field.
- **HPAC-PPA-REQ-098** — **no new `pawa_failure_code`, no new RHAMP
  `terminal_reason_code`**; the existing 21-value vocabulary + RHAMP's closed
  terminal reasons cover the evolved semantics.
- **HPAC-PPA-REQ-099** — a compatibility shim may translate an old logical
  request into the new typed request but SHALL NOT recreate the launcher-held
  writer, mint an in-process writer, return a handle, transfer a writer to the
  helper, or permit two production authority paths. The v1.0 launcher-held /
  `mint`-style in-process path is **superseded and non-production** as of v2.0;
  its code removal is a later governed slice.
- **HPAC-PPA-REQ-100** — bounded security claims (resists compromised ordinary
  interpreter / malicious plugin / gc introspection / fake helper / forged
  request / replay / launcher-side fabrication; does **not** claim resistance
  to hostile root, compromised kernel, or a compromised registered helper
  binary).
- **HPAC-PPA-REQ-101** — cross-contract conflict **resolved at contract level**;
  HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0,
  RDGO-001 v3.1, HPAC-PAWA-001 v2.0, HPAC-PAWA-HELPER-001 v1.0, and the
  descriptor + current-generation schemas remain **byte-unchanged**.
- **HPAC-PPA-REQ-102** — no `src/pcae` / `scripts` / `pyproject.toml` /
  `schemas` change; no protected-host mutation; no ceremony; runtime unchanged.
- **HPAC-PPA-REQ-103** — required successors, **derived, NOT begun**:
  (1) dedicated IV **N16-5-F-5-PPA-CONTRACT-IV** (a MAJOR carries its own IV —
  mandatory); (2) a fresh/scoped cross-contract IV of the resolved trio
  HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0 + HPAC-PPA-001 v2.0; (3) the
  HPAC-PAWA-REQ-340 implementation sequence, each under its own fresh human
  authorization, ending with a fresh `N16-5-FINAL-CERT` on a fresh CPIPC-valid
  successor id.

---

## 4. Cross-contract consistency review

| Contract | Version | Byte-status since ENTRY | Semantic status |
|---|---|---|---|
| HPAC-PAWA-001 | v2.0 | byte-unchanged | consistent — v2.0 §42B note / §42F `presentation_evidence_write` model is now **authorised** by HPAC-PPA-001 v2.0 §21 |
| HPAC-PAWA-HELPER-001 | v1.0 | byte-unchanged | consistent — §17 (HPAC-PAWA-HELPER-REQ-070..073) now has a matching HPAC-PPA-001 normative basis; §17's deferred cross-contract question is answered (option B, executed) |
| HPAC-001 | v2.1 | byte-unchanged | consistent — descriptor / evidence / attestation / paths / roles referenced, not re-meant |
| RHAMP-001 | v1.0 | byte-unchanged | consistent — no new real kind, ceremony ordering, transport, or terminal reason |
| HBDC-001 | v1.2 | byte-unchanged | consistent |
| RIHAC-001 / RIASC-001 / RDGO-001 | v2.0 / v3.0 / v3.1 | byte-unchanged | consistent — the runtime-invocation human-authority chain and dispatch-gate ordering are referenced, not re-meant; the presentation path still terminates before Gate 5 |
| `HPAC-PRESENTATION-EVIDENCE/2.0` + descriptor + current-generation schemas | — | byte-unchanged | consistent — HPAC-PPA-REQ-097 |

**Key question — resolved YES:** the evolved HPAC-PPA-001 v2.0 now permits
exactly the `presentation_evidence_write` model frozen by HPAC-PAWA-HELPER-001
v1.0 §17 without weakening any human-approval or human-authentication wall
(HPAC-PPA-REQ-093 / -094 / -095 preserved verbatim).

---

## 5. Byte-verbatim verification of v1.0 requirement bodies

`git show ENTRY:docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`
vs the working tree: the only deletions are in the header identity block (title
line, `**Version:** 1.0`, the frozen-by line, `**Protected administration:**
HPAC-PAWA-001 v1.2.`, and one scope sentence that was **expanded**, not
removed). **No `HPAC-PPA-REQ-*` body line and no `PPA-INV-1..8` body line was
deleted or reworded.** The contract-verification suite asserts every v1.0
requirement body appears verbatim in the v2.0 text
(`test_08_every_v1_0_requirement_body_survives_verbatim`).

---

## 6. Downstream guard reconciliation (widen-not-weaken)

A contract-file change trips a set of point-in-time "no normative contract
change / still v1.0 / numbering closed 1..76 / sibling contracts byte-unchanged"
guards across completed-predecessor suites. Method: A/B run at the phase-entry
SHA (`f0ca3423`, changes stashed) vs the reconciled working tree; `comm`-diff
the FAILED node lists.

**Attributable failures reconciled (widen-not-weaken):**

| Suite | Guard(s) | Reconciliation |
|---|---|---|
| `…30r_4r_1_protected_presentation_real_assurance` | `test_02_hpac_ppa_001_v1_0_identity` | accept `v1.0` or `v2.0` header; ceiling `76` or `103` |
| `…30r_4r_2_…_iv` | `test_07`, `test_08_ppa_requirement_numbering_is_closed_1_to_76` | accept v1.0/v2.0 header; numbering `range(1,77)` or `range(1,104)` |
| `…30r_4r_contract_reconciliation` | `test_32`, `test_33_requirement_numbering_is_closed_and_sequential` | admit the in-place HPAC-PPA-001 evolution; ceiling widened |
| `…tb_contract` | `test_62_sibling_contracts_and_schemas_byte_unchanged`, `test_63_hpac_ppa_001_still_v1_0` | RHAMP/HPAC/HBDC/schema still byte-frozen; HPAC-PPA-001 byte-freeze → not-weakened (v1.0 REQ ids ⊆ v2.0, header v2.0) |
| `…tb_contract_iv` | `test_05_sibling_version_headers_match_v2_0_claims` | accept v1.0/v2.0 PPA header |
| `…5r_2_1r_f3_immutable_phase_entry_evidence_repair` | `test_18_contract_bytes_unchanged[PPA]` | PPA param → not-weakened check |
| `…n16_5_f5b1_readauth_contract` | `test_72_schemas_byte_unchanged_since_c0` | PPA dropped from byte-freeze loop → not-weakened |
| `…n16_5_h3_pawa13_v1_3_contract_reconciliation` | `test_35`, `test_39_only_this_contract_changed_in_docs_contracts` | PPA dropped from byte-freeze loop / admitted in delta set |
| `…5r_2_1r_1r_1_f4_immutable_scope_iv` | `test_33_f3_suite_is_byte_unchanged_by_repair` | f3-suite byte-freeze → not-weakened |
| `…5r_2_1r_1r_2r_1_f6_immutable_host_mutation_guard_iv` | `test_48_no_contract_change` | admit PPA in the delta set |
| `…5r_2_1r_1r_f4_immutable_scope_repair` | `test_22_f3_repair_suite_unchanged`, `test_29_no_contract_change` | f3-suite byte-freeze → not-weakened; admit PPA |
| `…5r_2_1r_1r_2r_f6_immutable_host_mutation_guard_repair` | `test_38_no_contract_change` | admit PPA |
| `…5r_2_1r_1r_2r_1r_f7_remaining_f4_iv_evidence_guard_repair` | `test_51_no_other_guard_repaired`, `test_61_no_contract_change` | f4-iv hunk-count → not-weakened; admit PPA |
| `…5r_2_1r_1r_2r_1r_1r_f8_immutable_f6_iv_evidence_guard_repair` | `test_78_no_contract_change` | admit PPA |
| `…5r_2_1r_1r_2r_1r_1r_1r_f9_deployment_evidence_guard_repair` | `test_43_f7_nodes_unchanged`, `test_50_no_contract_change` | f4-iv byte-freeze → not-weakened; admit PPA |
| `…5r_2_1r_1r_2r_1r_1r_1r_1_f9_iv_and_n16_5_clearance` | `test_42_no_contract_change` | admit PPA |
| `…n16_5_h3_impl` | `test_128_admin_script_status_does_not_mutate_and_exits_cleanly_or_2` | before/after diff comparison instead of "working tree free of contract paths" |

**Discipline:** subset (`<=`) orientation preserved; NO wildcard / glob /
`fnmatch` / `.rglob(` added; NO test function renamed, removed, or disabled
(the contract-verification suite's `test_36_downstream_guard_reconciliation_is_widen_not_weaken`
asserts this for every touched file). String-scan meta-guards are not tripped
(token-split `"fn" + "match"` etc. in reconciliation code).

**Attributable-regression tally: 0.** Final A/B over the union of every touched
test file plus their freezer suites: identical FAILED node set at baseline and
at the reconciled tree. The pre-existing baseline failures (old BLOCKED-phase
`f3`/`f4`/`f6`/`f7`/`f8`/`f9` immutable-evidence suites red from the
predecessor's unreconciled `src/pcae` + PAWA v2.0 changes) are **unchanged** —
not introduced, not repaired, by this phase.

---

## 7. Contract-verification suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_1_1_n16_5_f_5_ppa_contract.py`
— 39 static / read-only assertions independently reconstructing each contract
meaning: CPIPC identity; v2.0 header / append-only evolution record; MAJOR
classification; contiguous numbering `1..103`; v2.0 additions exactly
`REQ-077..103`; every v1.0 body byte-verbatim; `PPA-INV-1..12` once each;
helper = sole evidence producer; no generic writer transfer; launcher no longer
holds the production writer; REQ-052 issuer → protected-side-internal;
helper response ≠ evidence authority; `PPA-INV-2 (v2.0)` semantic separation;
bounded ceremony/session/subject/generation binding; helper cannot self-assert;
ceremony-entry ≠ approval ≠ authentication; Gate 5 / PB / runtime / execution
non-expansion; same-file-object provenance; single trust root / no second root;
freshness / replay / currentness; seven-state failure model + no-auto-retry;
transport-not-authority relationship to HPAC-PAWA-HELPER-001; mechanism
neutrality / mobile future; NO SCHEMA CHANGE; no new failure code; compatibility
shim forbids insecure fallback; bounded security claims; cross-contract conflict
resolved + siblings byte-unchanged; scope fence (no src/scripts/pyproject/schema
change; docs/contracts delta = exactly HPAC-PPA-001); runtime unchanged;
downstream reconciliation widen-not-weaken; successor IV derived not begun;
delta table + v2.0 freeze verdict present; phase report present.

---

## 8. Final canonical status

| Field | Value |
|---|---|
| Canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1` |
| Display alias | N16-5-F-5-PPA-CONTRACT |
| Predecessor Phase ID | `…1.1R.…1.1.1.1.1` (N16-5-F-5-TB-CONTRACT-IV) |
| Predecessor finalized HEAD | `8c0e2e0a` (`origin/main` at entry) |
| CPIPC validation | VALID |
| Previous HPAC-PPA-001 version | v1.0 |
| New HPAC-PPA-001 version | **v2.0** |
| Version-classification rule / result | HPAC-PPA-REQ-069 / **MAJOR** (authority-ownership restructure; not a REQ-070 platform adapter) |
| Launcher evidence-writer disposition | **removed** as production holder / issuer; retains §6/§7 mediation + typed acknowledgement only |
| Helper evidence-producer disposition | **sole producer** — bounded, process-local, in-process write; no returnable writer |
| Evidence-writer issuer (REQ-052) disposition | **option C** — protected-side-internal operation of the helper process; never minted / returned / serialised / delivered |
| PPA-INV-2 new meaning | semantic trust-action separation preserved even within one verified helper process (`PPA-INV-2 (v2.0)`) |
| No-authority-transfer result | frozen — `PPA-INV-9` / HPAC-PPA-REQ-078 / -087 |
| Generic-writer result | prohibited |
| Presentation-evidence provenance model | verified helper process; same file object as the ceremony; single OS-filesystem trust root |
| Ceremony / session / subject / generation binding | preserved + made explicit (HPAC-PPA-REQ-079) |
| Replay / currentness result | preserved (HPAC-PPA-REQ-090) |
| Failure / uncertainty result | seven-state model + no-auto-retry (HPAC-PPA-REQ-091 / -092) |
| Single-trust-root result | **unchanged**; no second root |
| Deterministic-vs-real result | preserved (HPAC-PPA-REQ-058 unchanged) |
| Mechanism-neutral / mobile result | preserved (HPAC-PPA-REQ-096) |
| PB / POL / runtime / effect non-expansion | preserved (HPAC-PPA-REQ-095 / -003 / §15) |
| Cross-contract consistency with PAWA v2.0 / helper v1.0 | achieved — conflict resolved at contract level |
| Schema impact classification | **NO SCHEMA CHANGE REQUIRED** (HPAC-PPA-REQ-097) |
| Sibling-contract impact | none — all byte-unchanged |
| Contract guard results | new suite 39/39; downstream reconciliation A/B 0 attributable regressions |
| Broader regression tally | pre-existing BLOCKED-phase f-suite failures unchanged (documented §6); 0 attributable |
| Files changed | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`; the new contract-verification suite; 18 downstream guard files (widen-not-weaken); `PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/**`; `.pcae/phase-completion-*` |
| Production source changes | **none** |
| Contract files changed | **1** (HPAC-PPA-001, in place) |
| Schema changes | **none** |
| Live protected-host writes | **none** |
| Real ceremony | **NOT PERFORMED** |
| Runtime state | `not_implemented` / Observed / observe / unavailable |
| Plugins / capabilities | 0 / 0 |
| First external effect | ABSENT / UNREACHABLE |
| `pcae check` / `pcae health` / `pcae status coherence` | pass |
| `pcae push check` | `nothing_to_push` after push |
| doctor / task-memory | pass |
| notification | one Telegram phase notification on promotion |
| `origin/main..HEAD` | 0 after push |
| F-5-B2 status | **BLOCKED** pending contract IV + implementation |
| F-5 status | **CERTIFICATION BLOCKED** |
| N-16-5 status | **NOT CLOSED** |
| N-16-6 / N-16-7 status | **OPEN / UNTOUCHED** (N-16-7 strictly last) |
| Recommended PPA contract-IV successor | **N16-5-F-5-PPA-CONTRACT-IV** — derived, **NOT begun** |
| Successor explicitly not begun | confirmed — no IV suite, no IV phase, no implementation slice, no N-16-6 / N-16-7 work |

**This phase ends at HPAC-PPA-001 v2.0 contract freeze.** The dedicated IV and
every later phase require their own explicit human authorization.
