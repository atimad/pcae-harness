# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R — HPAC-PAWA-001 v1.3 Certification-Coordinator Authority Contract Reconciliation / Freeze

**Alias:** N16-5-H3-PAWA13

## Status: HPAC-PAWA-001 v1.3 — FROZEN (MINOR, S-2). H-3 CONTRACT BLOCKER: RESOLVED. H-3 PRODUCTION IMPLEMENTATION: PENDING. N-16-5: NOT CLOSED.

## Summary

The predecessor phase `…1.1R.1R.1R` independently reproduced blocking finding
**H-3** from primary source — the real end-to-end N-16-5 real-human /
genuine-YubiKey certification chain has **no production authority path** and
composes only through disclosed test-only seals — and demonstrated that H-3
cannot be honestly repaired under frozen HPAC-PAWA-001 v1.2, whose closed
authorized-consumer set (`HPAC-PAWA-REQ-087`) and §088 / §224 unauthorized list
exclude the certification consumer the chain requires while the chain requires
it.

This is a **contract-only reconciliation / freeze** phase. It amends
HPAC-PAWA-001 **v1.2 → v1.3** with the minimum honest normative delta:

1. **One** explicitly enumerated, non-agent-importable production
   factory-consumer category — the **N-16-5 real-human-authentication
   certification coordinator** (`pcae.core.hpac_certification_coordinator`,
   reached only from `scripts/hpac_certification_admin.py`), §38A / §39A.
2. **One** closed **certification-lifecycle writer family** (§42B) over the
   closed five-role allowlist
   `{ hpac_challenge_coordinator, hpac_assertion_recorder,
   human_authentication_proof_verifier, hpac_gate5_binder,
   hpac_rhamp_counter_state_verifier }`, minted only by a new
   `certification_writer(...)` factory reached by that one consumer under a
   dedicated **§33A recognition sequence** that reuses the §33 machinery
   (root topology + `HPAC-PAWA-AGENT-EXCLUSION/1.0` resolution + configured-agent
   identity binding + descriptor + current-generation + `O_EXCL|O_NOFOLLOW`
   write probe + not-configured-agent + authorized-factory-consumer) **verbatim**,
   then adds certification-consumer / role-allowlist / session-binding / mint /
   audit steps, all fail-closed.
3. **Walls** (§68A, PAWA-INV-13): coordinator ≠ verifier / Gate / human approver
   / authenticator / presentation-evidence writer / deployment-owner-as-approver
   / test harness; certification authority ≠ execution / PB / policy / RE /
   runtime capability / `DispatchEnvelope`; deterministic inputs never become
   REAL assurance through the coordinator; the path terminates at the bounded
   Gate-5 assurance result and authorizes no first external effect.

No new `pawa_failure_code` (every v1.3 rejection maps onto the existing 21
codes, §42C); no new `terminal_reason_code`; no RHAMP-001 edit; no new
`PawaOperation`; no new protected-root artifact or schema field; no new
companion contract. §96 is **specialized** (a narrow enumerated exception), not
redefined; the contract is internally self-consistent. **MINOR** under §80 /
§152 (S-2, §80.3), consistent with §153's permits and the v1.2 §80.2 precedent;
a full MAJOR-trigger review shows none fires.

**No `src/pcae` / `scripts` / `pyproject.toml` / dependency change. No ceremony.
Zero writes to the protected root.** Runtime unchanged (`not_implemented` /
`Observed` / `observe` / `unavailable`, 0 plugins / 0 capabilities). No first
governed runtime external effect. N-16-6 / N-16-7 remain OPEN / UNTOUCHED
(N-16-7 strictly last).

## Anchors

- **H0 (phase-entry SHA):** `b2530066b062b14b3c6f6df7c71c3092b22f215b`
- **Predecessor:**
  `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R`
  — N-16-5 Production Authority-Path Repair (BLOCKED, finding H-3; latest
  canonical completed phase — confirmed via `pcae session bootstrap` +
  `pcae phase-report show --latest`).
- **CPIPC successor validation:** the canonical parser (`pcae.core.phase_id`)
  confirms the operator-supplied ID `…1.1R.1R.1R.1R` is valid, `same_series` and
  `same_branch` with the predecessor, and strictly greater
  (`compare` → `less` predecessor→candidate). It is the established `R`-suffix
  repair-successor of a completed phase (final subphase token `1R` → `1R`
  appended), is absent from `tasks/done/` and `docs/`, matches the predecessor
  report's own "Successor" recommendation, does not reopen or reuse a completed
  phase ID, and introduces no parallel numbering scheme. **No mechanical
  discrepancy — the operator-supplied ID and the alias `N16-5-H3-PAWA13` are
  used exactly as given.**
- **`origin/main..HEAD` at entry:** 0. **At exit:** 0.

## 1. Governed orientation

| Check | Result |
|---|---|
| `git status` | clean at entry; branch `main` even with `origin/main` |
| `pcae session bootstrap` | lock rehydrated (`claude-local`); health healthy; check passed |
| `pcae check` | passed |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; registry empty; 0 plugins / 0 capabilities; PB `execution_unavailable`; posture `non-executing` |
| `pcae notify status` | Telegram configured, enabled, outbound-ready |
| Predecessor is latest canonical completed phase | ✅ |
| No conflicting active phase | ✅ (idle placeholder closed at phase start) |

No `git reset` / `stash` (during authoring) / `revert` / `clean` was performed.

## 2. H-3 contract conflict — independently reproduced

Primary source read: `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
(all 2767 v1.2 lines, incl. exact `HPAC-PAWA-REQ-087 / 088 / 095 / 096 / 152 /
153 / 219–233`); `HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`;
`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`;
`REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`;
`src/pcae/core/hpac_lifecycle.py`, `human_authentication_proof.py`,
`hpac_rhamp_counter_state.py`, `hpac_verifier.py`,
`hpac_protected_admin_writer.py`.

**The v1.2 conflict:** the certification chain
`open_challenge_canonical → record_assertion_canonical →
record_verified_canonical / create_canonical → bind_gate5_canonical →
apply_after_verification → verify_human_authentication(require_real_assurance=True)
→ Gate 5` needs a **PRODUCTION** `HPACWriterCapability` for each of the five
roles below; `HPACStoreAuthority.writer(role)` raises for every non-`FIXTURE`
class (`hpac_foundation.py`), the production mint sites in
`hpac_protected_admin_writer` (`production_writer()` /
`mint_protected_presentation_evidence_writer()`) cover **none** of the five, and
`HPAC-PAWA-REQ-088 / 224` explicitly name *verifier / Gate / runtime / agent /
CLI / plugin* as unauthorized. A certification coordinator is exactly a
verifier/Gate-adjacent consumer ⇒ a normative HPAC-PAWA-001 change is required.

| # | Role (source constant) | Canonical method | Record |
|---|---|---|---|
| 1 | `hpac_challenge_coordinator` (`HPACLifecycleStore._GENESIS_WRITER_ROLE`) | `open_challenge_canonical` | `STATE_CHALLENGE_CREATED` |
| 2 | `hpac_assertion_recorder` (`_ASSERTION_WRITER_ROLE`) | `record_assertion_canonical` | `STATE_ASSERTION_RECEIVED` |
| 3 | `human_authentication_proof_verifier` (`_VERIFIED_WRITER_ROLE`; `HumanAuthenticationProofStore._WRITER_ROLE`) | `record_verified_canonical` + `create_canonical` | `STATE_PROOF_VERIFIED` + `proofs/v2/<id>/proof.json` |
| 4 | `hpac_gate5_binder` (`_BOUND_WRITER_ROLE`) | `bind_gate5_canonical` | `STATE_PROOF_VERIFIED_AND_BOUND` |
| 5 | `hpac_rhamp_counter_state_verifier` (`COUNTER_STATE_VERIFIER_ROLE`) | `apply_after_verification` | `credentials/<id>/` counter-state |

**Five-role set independently revalidated:** exactly these five drive the
positive chain to `STATE_PROOF_VERIFIED_AND_BOUND` + the counter transition that
Gate 5 consumption (`hpac_lifecycle.py:788`, `is_verifier_authenticated_principal`,
`assurance_class is PRODUCTION`) requires. The sixth lifecycle role
`hpac_lifecycle_terminator` (`_TERMINAL_WRITER_ROLE`) writes **only** the
negative terminal states `EXPIRED` / `REVOKED` / `REJECTED` and is **not** on the
positive path — it is **explicitly excluded** from the v1.3 allowlist
(`HPAC-PAWA-REQ-246`); a rejected / expired ceremony fails closed without a
production write.

**Verdict:** `H-3 CONTRACT CONFLICT — VERIFIED`. `PRE-REPAIR PRODUCTION
CERTIFICATION AUTHORITY PATH — ABSENT`. `TEST-ONLY MECHANICAL PATH — PRESENT`.

## 3. Contract-shape derivation (independent — §95B)

Options A / B / C / D were independently derived rather than adopting the
predecessor's proposal verbatim. **A** was frozen: one enumerated
factory-consumer category + a closed five-role allowlist + a dedicated
`certification_writer` factory + the §33A recognition sequence; the contract
freezes the category / allowlist / per-role bindings, and (§57 discipline) does
**not** require a monolithic coordinator — the implementation may split
responsibilities. B (per-role sub-consumer modules), C (per-role factory
categories), and D (a new multi-role `PawaOperation`) were rejected as heavier
without added authority separation or as weakening the per-write / per-role /
single-use binding. **Preference applied: the narrowest design with the
strongest authority separation.** Full disposition in HPAC-PAWA-001 §95B.

## 4. REQ-087 / 088 / 223 / 224 reconciliation

| Requirement | v1.2 state | v1.3 disposition |
|---|---|---|
| `HPAC-PAWA-REQ-087` (closed authorized `PRODUCTION` writer factory consumers) | principal-admin + bootstrap + recovery + (v1.2) protected-presentation-mechanism configuration admin | **CLARIFIED BY NEW REQUIREMENT** — REQ-087 amended in place to add one further category *for the separate `certification_writer` factory* (§38A); set stays **closed**, extended only by explicit enumeration |
| `HPAC-PAWA-REQ-088` (unauthorized consumers) | ordinary agent / CLI / Gate / runtime / plugin / hooks / task / session / `core/agent.py` / `cli.py` / `commands/**` | **UNCHANGED** and **restated** for the certification factory in `HPAC-PAWA-REQ-240` (adds the launcher, helper, presentation-admin, and test-fixture / phase-harness as explicitly unauthorized certification consumers) |
| `HPAC-PAWA-REQ-223` (exact v1.2 presentation-admin consumer; "not a prefix, glob, or category wildcard"; "launcher, helper, presentation store, verifier, Gates, runtime, agent, CLI, and plugins remain unauthorized") | frozen | **UNCHANGED** — used as the precedented amendment *form* for §38A (`HPAC-PAWA-REQ-239` mirrors it exactly for `pcae.core.hpac_certification_coordinator` / `scripts/hpac_certification_admin.py`) |
| `HPAC-PAWA-REQ-224` (presentation-admin module / script non-agent-importable, not a CLI command / plugin / runtime provider / Gate consumer / repo hook / task callback) | frozen | **UNCHANGED** — mirrored for the certification module / script in `HPAC-PAWA-REQ-241` |
| `HPAC-PAWA-REQ-095 / 096` (§42 capability SHALL NOT write `HPAC-PROOF/2.0` / lifecycle events / Gate-5 artifacts — "those remain the trusted verifier's") | frozen | **SPECIALIZED IN PART** — `HPAC-PAWA-REQ-096` amended in place: the §42B certification family adds a **narrow enumerated exception** (one consumer, one bounded session, the real chain, same canonical stores / provenance); **outside** a bounded certification session the trusted verifier remains the sole author; `HPAC-PRESENTATION-EVIDENCE/2.0`, `HPAC-AUTHORITY-CONSUMPTION/2.1`, Gate-9, and every runtime/PB/RE/effect authority remain **outside** the family |

The v1.2 contradiction — the certification consumer must exist but is normatively
excluded — is **eliminated**: it is now one explicitly enumerated authorized
consumer with a closed role allowlist, a dedicated fail-closed recognition
sequence, and a closed mint authority, while every ordinary category stays
unauthorized.

## 5. Authority matrix (normative — HPAC-PAWA-001 §33A / §38A / §42B / §68A)

| Actor / category | Invoke `certification_writer`? | Receive challenge role? | Receive assertion-recorder role? | Receive proof-verifier role? | Receive Gate-5-binder role? | Receive counter-verifier role? | Remint? | Delegate? | Dispatch effect? |
|---|---|---|---|---|---|---|---|---|---|
| N-16-5 certification coordinator (`pcae.core.hpac_certification_coordinator` via `scripts/hpac_certification_admin.py`) | **YES** (only via §33A, only as the deployment owner / equally-privileged protected-admin context) | YES (one, session-bound) | YES (one) | YES (one) | YES (one) | YES (one) | **NO** | **NO** | **NO** |
| deployment owner (not via the coordinator) | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| launcher `pcae.core.protected_presentation` | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| helper `pcae.protected_presentation_helper` | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| presentation evidence writer / admin | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| `hpac_verifier` (as factory importer) | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| Gate 5 / any gate coordinator | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| runtime adapter / plugin runtime | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| ordinary agent / `core/agent.py` | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| ordinary `pcae` CLI / `commands/**` | NO | NO | NO | NO | NO | NO | NO | NO | NO |
| test fixture / phase orchestration harness | NO | NO | NO | NO | NO | NO | NO | NO | NO |

Every "NO" cell is a fail-closed `unauthorized_factory_consumer` (#15) /
`operation_scope_invalid` (#16) / `target_scope_invalid` (#17) — the §42C
mapping. No fallback.

## 6. Recognition-sequence table (HPAC-PAWA-001 §33A)

| Step | Check | Failure → `pawa_failure_code` |
|---|---|---|
| 1 | canonical `<HPAC_PROTECTED_ROOT>` resolution + trust (§25) | `protected_root_missing` / `protected_root_untrusted` |
| 2 | `HPAC-PAWA-AGENT-EXCLUSION/1.0` load + live account resolution + `live uid == provisioned_uid` + live groups (§32A) → `ConfiguredAgentAuthorityIdentity` | `agent_principal_unknown` |
| 3 | configured-agent exclusion negative boundary (§26) | `agent_has_protected_write_authority` |
| 4–5 | descriptor trust: closed schema / digest / `protected_root_identity` / ownership / mode / `provenance_ref` / `state == ACTIVE` (§14 / §27) | `descriptor_*` |
| 6 | `current-generation.json` incl. `agent_exclusion_digest`; `descriptor.generation == current_generation` (§20A) | `descriptor_generation_stale` / `descriptor_installation_mismatch` |
| 7 | not-configured-agent current-context (§31) | `current_context_is_agent` |
| 8 | `O_EXCL\|O_NOFOLLOW` positive write probe under `.authority/` (§28) | `write_probe_failed` |
| 9 | authorized-factory-consumer (§32) | `unauthorized_factory_consumer` |
| 10 | caller is the exact §38A certification consumer | `unauthorized_factory_consumer` |
| 11 | requested `role` ∈ the closed five-role allowlist | `operation_scope_invalid` |
| 12 | certification-session binding: nonempty `certification_session_id`; active mechanism-neutral principal; active bound credential; bound `proof_id` / challenge | `operation_scope_invalid` / `target_scope_invalid` |
| 13 | mint one process-local, single-use, restart-dead `PRODUCTION` capability bound to `(role, subject, certification_session_id)` | — |
| 14 | record issuance audit evidence (§55 + §42B) | — |

Steps 1–14 are **one atomic recognition unit**; the sequence runs fresh on every
call; any failed conjunct → no capability (PAWA-INV-3, PAWA-INV-12, PAWA-INV-13).

## 7. Contract-delta table

| Contract area | v1.2 state | H-3 conflict | v1.3 required state | Security non-regression |
|---|---|---|---|---|
| authorized factory-consumer set | closed; no certification consumer | consumer required but excluded | + one enumerated category (§38A); set stays closed | PAWA-INV-9 preserved; no wildcard/prefix/glob |
| five-role allowlist | n/a | five FIXTURE-only roles | closed `{challenge, assertion, proof-verifier, gate5-binder, counter-verifier}`; terminator + all else denied | new role ⇒ new governed contract evolution |
| mint authority | §36 factory only | no certification mint | + `certification_writer` factory behind the §37 non-agent-importable fence; `writer()` still raises; no generic mint | seal discipline unchanged |
| recognition sequence | §33 (11 steps) | none for certification | + §33A (§33 conjuncts 1–9 verbatim + certification steps); fail-closed | trust root / agent exclusion / two-OS-principal / generation-rollback reused |
| capability lifetime | §45–§49 | n/a | single-use per role per one ceremony; process-local; non-bearer; restart-dead; no delegation/remint | §152 MAJOR trigger (bearer/reusable) not fired |
| §96 verifier-only records | verifier is sole author | production writer for those records required | narrow enumerated exception (one consumer, one session); verifier sole author outside it | evidence / consumption / Gate-9 / runtime records stay outside |
| failure taxonomy | 21 closed codes | n/a | 21 unchanged; §42C maps every v1.3 rejection | RHAMP §57 map unchanged; RHAMP-001 byte-unchanged |
| walls | §5 / §13 / §67 / §68 / PAWA-INV-2 / -8 | n/a | all preserved + §68A + PAWA-INV-13 | human-approval / real-vs-deterministic / PB / policy / runtime / effect all preserved |
| effect boundary | first effect ABSENT | n/a | certification path terminates at Gate-5 assurance result | no `DispatchEnvelope`, no runtime capability, no external effect |

## 8. Cross-contract consistency

Checked against HPAC-001 v2.1, RHAMP-001 v1.0, HPAC-PPA-001 v1.0, the
HPAC lifecycle / proof / counter-state / Gate-5 territory, RIHAC-001 v2.0,
RIASC-001 v3.0, RDGO-001 v3.1, HBDC-001 v1.2. **No second frozen contract
requires amendment:** v1.3 references existing lifecycle / proof / counter-state
semantics by name in normative text only; `verify_human_authentication`,
`is_verifier_authenticated_principal`, Gate 5, and the presentation
evidence-writer boundary are **consumed, not redefined**;
`require_real_assurance=True` is not relaxed; `HPAC-PRESENTATION-EVIDENCE/2.0`
stays outside the family and HPAC-PPA-001 v1.0 is byte-unchanged. Verified
byte-unchanged at H0 (contract test `test_35`): HPAC-PPA-001, RHAMP-001,
HPAC-001, HBDC-001, and every other `docs/contracts` file except the PAWA
contract itself. **CROSS-CONTRACT CONSISTENCY: VERIFIED — NOT BLOCKED.**

## 9. MINOR adjudication (S-2)

Full MAJOR-trigger review in HPAC-PAWA-001 §80.3 / `HPAC-PAWA-REQ-270`: none of
the §152 triggers fires — authority basis stays live effective filesystem write
authority (no sudo/euid/env); the configured-agent exclusion and two-OS-principal
topology are reused unchanged; no remote authority service; the certification
capability is non-bearer / non-durable / non-serialisable / single-use /
restart-dead; it grants **no** runtime approval / PB / RE / runtime capability /
execution — the path terminates at the Gate-5 assurance result; the bootstrap
trust root and generation/rollback protection are unchanged; no signing key /
pinned key / keychain; the consumer inventory is widened by **exactly one
explicitly enumerated** category and the role set is **exactly one explicitly
enumerated** closed allowlist — no wildcard / prefix / glob. Consistent with
§153's permits and the v1.2 §80.2 precedent. **⇒ HPAC-PAWA-001 v1.3 — MINOR.**

A reasonable reader could argue the §96 specialization approaches a
mutation-scope change; the **dedicated HPAC-PAWA-001 v1.3 contract IV**
(`HPAC-PAWA-REQ-274`, alias **N16-5-H3-PAWA13-IV**) is therefore the recommended
default before the H-3 implementation relies on this text (the v1.1 **C-3**
precedent), foldable into the implementation IV only at explicit operator
discretion.

## 10. Contract verification suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_h3_pawa13_v1_3_contract_reconciliation.py`
— **54 cases, all passing**, static / read-only. Covers: phase lineage / CPIPC
(01–03); version v1.3 + preserved v1.0/v1.1/v1.2 history + H0-was-v1.2 (04–07);
closed-set + new category + §33A + five-role allowlist + no-wildcard + unknown /
terminator role denied (08–13); ordinary launcher / helper / presentation store /
verifier / Gate / runtime / agent / CLI / plugin / test-fixture unauthorized
(14) + §088 / §224 preserved (15); non-bearer / single-use / process-local /
restart-dead / no-remint / no-delegation / no-generic-authority / FACTORY≠CONSUMER
(16–19); per-role boundaries + presentation evidence outside the family (20–25);
human-approval / real-vs-deterministic / PB-policy / runtime-effect / Gate-5
termination walls + PAWA-INV-13 (26–30); no new `pawa_failure_code` / no new
`terminal_reason_code` / no RHAMP edit / no new `PawaOperation` / schemas
byte-unchanged / related frozen contracts byte-unchanged at H0 (31–35);
MINOR / S-2 / MAJOR review / §96 specialized (36–37); no `src/pcae` / `scripts`
change since H0 / exactly one `docs/contracts` file changed / no instance ids /
REQ IDs 1–275 sequential / N-16-5 not closed / dedicated v1.3 IV recommended /
mechanism neutrality / runtime unchanged (38–45), plus the parametrized
sub-cases.

The §33A / §38A / §42B / §68A **guard and functional tests** (production
reachability, factory recognition denial, five-role mint restrictions,
no-deterministic-elevation, no principal / Gate / PB / effect manufacture) are
**specifications for the H-3 implementation phase and the dedicated v1.3
contract IV**, not authored now (`HPAC-PAWA-REQ-273`).

## 11. Point-in-time guard reconciliation

**Method (memory trap 11 / `HPAC-PAWA-REQ-217` discipline):** a 65-file guard-set
was run at the phase-entry SHA `b2530066` and again at the reconciled HEAD; the
FAILED node lists were `comm`-diffed. Candidate-only (attributable) failures
were reconciled phase-aware — the authorized set widened by **exactly** the one
`HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` file, subset / `==`
orientation kept, **no wildcard / glob / `fnmatch`**, **no `def test_` renamed,
removed, or disabled**. Baseline-common failures (protected-root-exists and
unrelated `src/pcae` point-in-time guards from later `.5R.2.1R…` micro-phases)
were classified as pre-existing and **not** touched.

**Result: 0 attributable functional regressions.** Guard-set at entry: 149
failed / 2890 passed. Guard-set at reconciled HEAD: 146 failed / 2893 passed
(3 pre-existing failures incidentally repaired; **zero** candidate-only
remaining). All 146 residual failures reproduce identically at `b2530066`.

~24 "no normative contract change since `<baseline>`" guards across ~19 IV /
repair suites were widened by the one PAWA file (e.g. `…3_1::test_87`,
`…3_4::test_01`, `…30r_5::test_all_contracts_byte_unchanged_since_A` +
parametrized case, `…4r_1::test_03`, `…5r_2_protected_presentation_interactive_election_repair::test_04`,
the `…5r_2_1r_1r*` `f4` / `f6` / `f7` / `f8` / `f9` immutable-scope /
host-mutation / evidence-guard suites, the two `contamination` suites, the two
`ppa_deployment` / `ppa_registration` suites, `…privileged_ro_gen1_ppa_absence_f5_hold`).
Three downstream **byte-freeze meta-guards** (`…f9_iv…::test_37` / `test_38`,
`…f9_deployment_evidence_guard_repair::test_44`) were converted from byte-identity
to **not-weakened** checks (`def test_` count non-decreasing; no dynamic-match
helper / disabled-test token introduced), and the `batch013` / `privileged_ro`
"only additions" guards were widened to allow later-phase modifications while
still forbidding any test-function removal.

Also reconciled: `…4r_2…::test_07_contract_identities_are_the_frozen_versions`
(v1.2 header requirement widened to accept `# HPAC-PAWA-001 v1.3`);
`…4r_contract_reconciliation::test_32` / `test_33` (contract-set + REQ-count
`range(1,234) | range(1,276)`); `…3_3r::test_rhamp_001_byte_unchanged_since_baseline_a`
(**pre-existing at H0**, stale from `.30R.4R` — reconciled to the guard's true
intent: RHAMP-001 byte-unchanged, later `docs/contracts` delta bounded to the
PAWA + PPA evolutions); `…5r_ctap2_pin_uv_repair::test_41` +
`…5r_1_ctap2_pin_uv_repair_iv::test_19`.

Fresh suite `…v1_3_contract_reconciliation.py` **54 / 0**; targeted affected
suites (`…v1_3_contract_reconciliation`, `…4r_contract_reconciliation`,
`…2a_3_v1_1_contract_freeze_iv`, `…3_1`, `…3_3r`, `…3_4`, `…4r_1`, `…4r_2`,
`…ppa_deployment_state_iv`, `test_hpac_verifier`, `test_hpac_lifecycle`)
**621 / 0**.

## 12. Required final verdicts

```
PHASE ALIAS:                                     N16-5-H3-PAWA13
HPAC-PAWA-001 PREVIOUS VERSION:                  v1.2
HPAC-PAWA-001 CURRENT VERSION:                   v1.3
H-3 CONTRACT CONFLICT:                           VERIFIED
AUTHORIZED FACTORY-CONSUMER SET:                 CLOSED
NEW CERTIFICATION FACTORY-CONSUMER CATEGORY:     FROZEN  (N-16-5 real-human-authentication certification coordinator;
                                                 pcae.core.hpac_certification_coordinator via scripts/hpac_certification_admin.py)
CERTIFICATION CATEGORY RECOGNITION SEQUENCE:     FROZEN  (§33A — §33 conjuncts 1–9 verbatim + certification steps; fail-closed)
CERTIFICATION ROLE ALLOWLIST:                    { hpac_challenge_coordinator, hpac_assertion_recorder,
                                                   human_authentication_proof_verifier, hpac_gate5_binder,
                                                   hpac_rhamp_counter_state_verifier }
UNKNOWN ROLE:                                    DENY (operation_scope_invalid)
ORDINARY LAUNCHER:                               UNAUTHORIZED
HELPER:                                          UNAUTHORIZED
ORDINARY VERIFIER:                               UNAUTHORIZED
ORDINARY GATE:                                   UNAUTHORIZED
RUNTIME:                                         UNAUTHORIZED
AGENT:                                           UNAUTHORIZED
ORDINARY CLI:                                    UNAUTHORIZED
PLUGIN:                                          UNAUTHORIZED
REMINT / DELEGATION:                             DENIED
GENERIC PRODUCTION WRITER AUTHORITY:             NOT INTRODUCED
NON-BEARER / TRUSTED-CONSTRUCTION SEMANTICS:     PRESERVED
HUMAN APPROVAL SEPARATION:                       PRESERVED
REAL-vs-DETERMINISTIC ASSURANCE WALL:            PRESERVED
PB/POLICY WALL:                                  PRESERVED
RUNTIME / EFFECT WALL:                           PRESERVED
CROSS-CONTRACT CONSISTENCY:                      VERIFIED
PRODUCTION IMPLEMENTATION:                       NOT PERFORMED
REAL CEREMONY:                                   NOT PERFORMED
H-3 CONTRACT BLOCKER:                            RESOLVED
H-3 PRODUCTION IMPLEMENTATION:                   PENDING
H-3:                                             CONTRACT RECONCILED — IMPLEMENTATION PENDING
F-5:                                             DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED PENDING H-3 IMPLEMENTATION
N-16-5:                                          NOT CLOSED
N-16-6:                                          OPEN / UNTOUCHED
N-16-7:                                          OPEN / UNTOUCHED / STRICTLY LAST
RUNTIME:                                         not_implemented / Observed / observe / unavailable (0 plugins / 0 capabilities)
FIRST GOVERNED RUNTIME EXTERNAL EFFECT:          ABSENT / UNREACHABLE
```

## 13. No-ceremony / no-mutation attestation

`makeCredential` 0; real `getAssertion` 0; YubiKey touch 0; FIDO2 PIN prompt 0;
protected APPROVE 0; protected REJECT 0; real presentation evidence 0; challenges
opened 0; proofs created 0; Gate 5 certifications 0; principals minted 0;
authorized protected host mutation 0; unauthorized protected host mutation 0;
counter-state generation before 0 / after 0; secrets requested / echoed / logged
0; `require_real_assurance=True` calls 0; `AuthenticatedHumanPrincipal` minted 0.

## 14. Boundaries preserved

- `git diff --name-only H0 HEAD` touches only
  `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`,
  `docs/PHASE_…`, `tests/…` (the new contract-only suite + four point-in-time
  guard reconciliations), `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`,
  `.pcae/**`. **No `src/pcae`, `scripts`, `pyproject.toml`, or dependency
  change.**
- No principal / credential / counter / protected-root / helper / generation /
  PPA-registration state created, recreated, reset, rotated, or repaired.
- Runtime `not_implemented` / `Observed` / `observe` / `unavailable`, 0 / 0 —
  unchanged. No `adapter.dispatch`, no `DispatchEnvelope`, no plugin, no first
  governed runtime external effect.
- Human principal remains mechanism-neutral; `hpac.fido2.uv_presence.v2` and
  `pcae-protected-local-presentation/1.0` remain supported / non-exclusive; the
  mobile / passkey future path stays open.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved. No
  delegated worker used; the primary human-authorized session performed all
  read-only investigation, primary-source study, contract authoring, task
  lifecycle, commits, and push.
- Durable Telegram Acceptance Receipt / Phase-Notification Auditability:
  preserved. No historical notification re-dispatch. This phase's normal
  completion notification is authorized.

## 15. Successor phases (derived — NOT begun)

1. **Dedicated Independent Verification of HPAC-PAWA-001 v1.3**
   (alias **N16-5-H3-PAWA13-IV**; `HPAC-PAWA-REQ-274`) — recommended default
   before the H-3 implementation relies on this text.
2. **N-16-5 Production Certification Authority-Path Implementation Against
   HPAC-PAWA-001 v1.3 — H-3 Repair** (alias **N16-5-H3-IMPL**).
3. **Dedicated Independent Verification of the H-3 implementation**
   (alias **N16-5-H3-IV**).
4. **Fresh final real-human / genuine-YubiKey N-16-5 certification**
   (alias **N16-5-FINAL-CERT**; a fresh CPIPC-valid successor id — do not reuse a
   completed certification phase id).

Each requires its own explicit human authorization; IDs recommended, NOT
reserved; each needs its own human authentication and (where a ceremony occurs)
its own protected human approval. None is bundled into this phase. N-16-6 and
N-16-7 remain OPEN / UNTOUCHED and strictly out of scope; N-16-7 strictly last.

## 16. Evidence

`.pcae/certification/n16_5_h3_pawa13_v1_3_contract_freeze.json`
(schema `PCAE-N16-5-H3-PAWA13-V1-3-CONTRACT-FREEZE/1.0`) records H0, the CPIPC
successor validation, the orientation snapshot, the reproduced H-3 contract
conflict, the independently revalidated five-role set, the REQ-087 / 088 / 223 /
224 reconciliation, the contract-shape disposition, the contract-delta and
authority matrices, the MINOR (S-2) adjudication, the cross-contract consistency
result, the contract verification suite outcome, the point-in-time guard
reconciliations, and the all-zero ceremony / mutation audit.
