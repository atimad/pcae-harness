# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R — Independent Verification of HPAC-PAWA-001 v1.3 Certification-Coordinator Authority Contract

**Alias (display-only, non-authoritative):** N16-5-H3-PAWA13-IV

**Canonical predecessor:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R (alias N16-5-H3-PAWA13)

## Status: HPAC-PAWA-001 v1.3 — INDEPENDENTLY VERIFIED. H-3 CONTRACT BLOCKER: INDEPENDENTLY VERIFIED RESOLVED. H-3 PRODUCTION IMPLEMENTATION: PENDING. N-16-5: NOT CLOSED.

---

## 1. Scope and independence

This is a **verification-only** phase (HPAC-PAWA-REQ-274, the v1.1 **C-3**
precedent). It authored **no** production certification path, edited **no**
normative contract text, performed **no** ceremony, mutated **no** protected
host state, and did **not** close N-16-5.

The v1.2 → v1.3 authority model was independently reconstructed from: the
immutable git history of the contract document; the v1.2 baseline blob
(`ab5b471d06619e452433e624a971f5e1c84b400d`, byte-identical to the
guard-attribution baseline `b2530066`); the v1.3 freeze commit
(`76523d8ce07435619127fbf19491a8d200ceb4bc`); primary-source production modules
(`hpac_lifecycle.py`, `human_authentication_proof.py`,
`hpac_rhamp_counter_state.py`, `hpac_protected_admin_writer.py`,
`hpac_rhamp_terminal_reasons.py`, `hpac_pawa_schemas.py`); and the referenced
frozen contracts. The predecessor freeze verdict and its passing tests were
**not** taken as normative.

**IV phase-entry SHA (V0):** `4977a2e5db362e9e86f898cf438578f00e8051f5`
(`origin/main..HEAD` = 0 at entry; working tree clean).

## 2. CPIPC lineage

Parsed with `pcae.core.phase_id`:

| Check | Result |
|---|---|
| candidate = predecessor + exactly one trailing `.1R` segment | ✅ direct successor |
| same series (149) | ✅ |
| same branch (`O`) | ✅ |
| strict ordering (`compare(pred, cand)` = `less`) | ✅ predecessor first |
| predecessor is latest completed phase | ✅ (`architecture-status`: no active phase; bootstrap: latest completed = predecessor, report complete) |
| uniqueness / no active conflicting phase | ✅ |
| CPIPC-derived canonical id | **identical** to the proposed id — no discrepancy; alias `N16-5-H3-PAWA13-IV` remains display-only |

## 3. v1.2 → v1.3 normative delta (independently reconstructed)

`git diff ab5b471d..76523d8c -- docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
= **806 insertions, 23 deletions, one file**. `git diff --name-only
b2530066..HEAD -- docs/contracts` names **exactly** this one file. `git diff
--stat b2530066..HEAD -- src/pcae scripts pyproject.toml` is **empty**.

**V1.3 NORMATIVE DELTA — INDEPENDENTLY RECONSTRUCTED:**

New sections: **§7B** (v1.2→v1.3 delta table), **§33A** (certification-coordinator
recognition sequence), **§38A** (authorized certification consumer), **§39A**
(certification consumer inventory guard), **§42B** (certification-lifecycle
writer family + closed five-role allowlist + per-role table), **§42C** (v1.3
rejection → existing 21-code mapping), **§43A** (session / subject scope),
**§44A** (currentness / replay preservation), **§49A** (one-ceremony lifetime),
**§68A** (certification authority walls), **§80.3** (v1.3 MINOR rule S-2 + MAJOR
review), **§90.3 / §95.2 / §95B / §96B** (verdict / disposition / next phases).

Edited in place: title / `Version:` line (1.2 → 1.3); §7 lineage prose
(`v1.0 → v1.1 → v1.2 → v1.3`, every evolution MINOR); **HPAC-PAWA-REQ-087**
(appends one further enumerated category; the v1.2 sentence survives verbatim);
**HPAC-PAWA-REQ-096** (subject rescoped to "§42 administrative-mutation"; a
"specialized, not redefined" carve-out added); §91 counts (233 → 275
requirements; 12 → 13 invariants); §92 (**PAWA-INV-13** added); §93 / §94
(history); §95B (append-only shape disposition A/B/C/D).

New requirements **HPAC-PAWA-REQ-234 … HPAC-PAWA-REQ-275** (42, contiguous). New
invariant **PAWA-INV-13**. No unrelated authority expansion: every added line is
certification-scoped, a lineage/count line, or the §96 specialization; the delta
contains **no** positive grant of runtime / execution / dispatch / PB / policy
authority and **no** new companion-contract creation.

## 4. Version classification — MINOR (S-2) VERIFIED

The §152 MAJOR-trigger list was independently walked against v1.3:

| §152 MAJOR trigger | v1.3 |
|---|---|
| `sudo`/`euid`/env sufficient authority | **no** — §33A authority basis is the §33 conjunction (live effective FS write authority + descriptor + `O_EXCL` write probe); §34 / REQ-076 unchanged |
| collapse / remove configured-agent exclusion | **no** — §33A reuses §26 / §31 / §32A unchanged |
| same-principal agent / deployment-owner topology | **no** — §61 / REQ-205 reused, still fail-closed |
| remote / network / cloud authority service | **no** — fully local standalone script |
| capability bearer / durable / serialisable / reusable across operations | **no** — §49A: single-use, process-local, restart-dead, non-bearer; §45–§49 verbatim |
| broaden capability into runtime approval / PB / RE / runtime-capability / execution | **no** — §68A / REQ-261 denies each; path terminates at Gate-5 |
| change bootstrap trust root | **no** |
| remove `generation` / rollback protection | **no** — §33A reuses §20 / §20A (incl. `agent_exclusion_digest`) |
| add signing-key / pinned-key / keychain authority input | **no** |
| widen authorized-consumer inventory by wildcard / prefix / glob | **no** — exactly one enumerated category + exactly one enumerated five-role allowlist; §39A / REQ-244 forbid glob/`fnmatch`/prefix (PAWA-INV-9) |

**No MAJOR trigger fires.** The evolution fits the §153 MINOR permits — "add an
authorized-consumer **category** by explicit enumeration (never wildcard)" and
"add **one** explicitly enumerated protected-admin **metadata mutation family**
whose target is inside the same protected root … capability remains
process-local / non-bearer / one-operation … no §152 MAJOR trigger fires" — and
matches, shape-for-shape, the **v1.2 §80.2** precedent
(`configure_presentation_mechanism`, classified MINOR by REQ-230 and
independently verified by `.1R.30R.4R.2`). **REQ-154** is not violated: the §42
administrative-mutation capability's granted scope is unchanged; the §96 edit is
a bounded carve-out for a *separate, new* writer family, not a widening of an
already-minted capability.

**VERSION CLASSIFICATION: MINOR S-2 — VERIFIED.**

*Observation O-1 (non-blocking):* §153's family permit is worded
"metadata mutation family"; the certification family writes
authentication-lifecycle / proof / counter-state records rather than
principal-administration metadata, so the permit is read at its broadest. This
is within the contract's own amendment discipline — §80.3 / REQ-269 explicitly
establishes the S-2 rule for exactly this shape with stated reasoning and the
v1.2 precedent — and is recorded as an observation, not a defect.

## 5. Requirement / invariant inventory — VERIFIED

- `HPAC-PAWA-REQ-001 … HPAC-PAWA-REQ-275`: **275** definitions, each defined
  exactly once (`- **HPAC-PAWA-REQ-NNN.**`), the id set is exactly
  `{1..275}` — sequential, **no gaps, no duplicates, no reused id with changed
  unrelated meaning**. (Definitions are grouped by section, not strictly
  file-ordered; the closure invariant is on the set.)
- v1.3 additions are exactly `REQ-234 … REQ-275`.
- `PAWA-INV-1 … PAWA-INV-13`: sequential, coherent; **PAWA-INV-13** defined
  exactly once.
- Historical traceability: `REQ-087 / 088 / 223 / 224` — the v1.2 text survives
  **verbatim** inside each (087 is extended by an appended sentence; 088 / 223 /
  224 are unchanged). The certification exception is introduced **only** by new
  requirement ids, never by re-meaning a frozen one; the v1.2 semantics remain
  fully reconstructable and v1.3 does not imply the exception pre-existed it.

## 6. Closed category + closed five-role allowlist — VERIFIED (primary-source grounded)

Independently reconstructed the positive authentication chain from production
source:

| Role (contract) | Primary-source origin | Positive-chain write |
|---|---|---|
| `hpac_challenge_coordinator` | `hpac_lifecycle.py::_GENESIS_WRITER_ROLE` | `STATE_CHALLENGE_CREATED` |
| `hpac_assertion_recorder` | `hpac_lifecycle.py::_ASSERTION_WRITER_ROLE` | `STATE_ASSERTION_RECEIVED` |
| `human_authentication_proof_verifier` | `hpac_lifecycle.py::_VERIFIED_WRITER_ROLE` **and** `human_authentication_proof.py::_WRITER_ROLE` | `proof.json` + `STATE_PROOF_VERIFIED` |
| `hpac_gate5_binder` | `hpac_lifecycle.py::_BOUND_WRITER_ROLE` | `STATE_PROOF_VERIFIED_AND_BOUND` |
| `hpac_rhamp_counter_state_verifier` | `hpac_rhamp_counter_state.py::COUNTER_STATE_VERIFIER_ROLE` | one bounded transition on an **accepted** decision only (`subject=credential_id`) |

- The contract allowlist (§42B / REQ-246) equals this set **exactly** — not a
  subset-plus-other, not a prefix, not a wildcard.
- `hpac_lifecycle_terminator` (`_TERMINAL_WRITER_ROLE`) writes **only** the
  negative terminal states `EXPIRED` / `REVOKED` / `REJECTED` and is
  **explicitly NOT** a member; a rejected/expired certification ceremony fails
  closed without a production write; a future production terminator write
  requires a new governed evolution. **TERMINATOR: DENY — VERIFIED.**
- **UNKNOWN / WILDCARD / PREFIX ROLE: DENY — VERIFIED** (`operation_scope_invalid`,
  §42C; "No wildcard, no prefix match, no `fnmatch`, no arbitrary role
  argument, no future role implicitly authorized").
- **AUTHORIZED FACTORY-CONSUMER SET: CLOSED** — extended only by the explicit
  §38A enumeration of `pcae.core.hpac_certification_coordinator` via
  `scripts/hpac_certification_admin.py`; §39A / REQ-244 forbid any
  glob/`fnmatch`/prefix broadening (PAWA-INV-9). The category is normatively
  distinct from launcher / helper / presentation-evidence writer / ordinary
  verifier / Gate / runtime / agent / CLI / plugin / test fixture, and its
  identity is a recognised module, not a caller-supplied string (REQ-236.1 —
  "verify the calling module is the **exact** §38A certification consumer").
- **TEST FIXTURE: NON-PRODUCTION** — REQ-265 explicitly refuses to legitimize
  `_production_test_fixture` / an imported `_PRODUCTION_WRITER_FACTORY_SEAL` /
  `_test_decision_source` / `DeterministicCtap2Provider` / an in-process launch
  shim; the H-3 implementation must compose only through the recognized
  `certification_writer` boundary.

## 7. §33A recognition sequence — VERIFIED (reuses §33, fails closed)

§33A (REQ-234–238) mints the certification family **only** through a distinct
`certification_writer(...)` factory exported from the same non-agent-importable
admin-only module as the §36 production factory, invoked **only** by the exact
§38A consumer. `HPACStoreAuthority.writer(role)` still `raise`s for every
non-`FIXTURE_NON_REAL` class (§40 / REQ-092); no new public generic mint, no
string-addressable role escalation, no caller-controlled role argument.

**§33 → §33A conjunct table:**

| §33 step | §33A treatment |
|---|---|
| 1 canonical-root resolution + trust (§25) | reused verbatim — **IDENTICAL** |
| 2 configured-agent principal + `AGENT-EXCLUSION/1.0` substeps (§32A: schema/digest/ownership/mode, `record_digest == current-generation.agent_exclusion_digest`, live account, `live uid == provisioned_uid`, live groups) | reused verbatim — **IDENTICAL** |
| 3 protected-root ownership + configured-agent exclusion negative boundary + safe ancestors (§26) | reused verbatim — **IDENTICAL** |
| 4 `HPAC-STORE-AUTHORITY/1.0` manifest `{device,inode}` binding | reused verbatim (steps 1–9 run verbatim as required conjuncts) — **IDENTICAL** |
| 5 descriptor no-follow validation (§14 / §27) | reused verbatim — **IDENTICAL** |
| 6 `current-generation.json` closed field set + `descriptor.generation == current_generation` (§20A) | reused verbatim — **IDENTICAL** |
| 7 current context ≠ configured agent principal (§31) | reused verbatim — **IDENTICAL** |
| 8 `O_EXCL \| O_NOFOLLOW` write probe under `.authority/` (§28 / §29) | reused verbatim — **IDENTICAL** |
| 9 authorized-factory-consumer check (§32) | reused verbatim **+ TIGHTENED** — REQ-236.1 adds the exact §38A certification-consumer identity check (`unauthorized_factory_consumer` on mismatch) |
| 10 mint | **SPECIALIZED** — REQ-236.4 mints one process-local, single-use, restart-dead `PRODUCTION` capability bound to `(role, subject, certification_session_id)`; `subject` = `proof_id` for the four lifecycle roles, `credential_id` for the counter role |
| 11 audit | **SPECIALIZED** — REQ-236.5 / REQ-251 records the §55 field set plus, as non-authoritative facts, role / session / bound ids / ceremony phase; never serialises `_authority_seal` |

**No §33 mandatory trust conjunct is missing or weakened.** REQ-237: fresh run
on every call, no caching, one atomic recognition unit (PAWA-INV-3, PAWA-INV-12,
PAWA-INV-13). REQ-238: any failed conjunct/check → the corresponding §56 code
(§42C map), **no** capability minted, "the absence of a denial is never
authority." Recognition is **not** self-assertable from ambient identity
(`USER` / `SUDO_USER` / `LOGNAME` / cwd / `PATH`) or caller-provided strings —
REQ-270 fixes the authority basis as the §33 conjunction.

Session / subject scope (§43A, REQ-255/256): a capability minted for session A /
subject A cannot write session B / subject B (`target_scope_invalid`); no
principal / credential scope is inferred from a role or subject; the `proof_id`
/ `certification_session_id` is reserved before the ceremony (§100 discipline).

**RECOGNITION FAIL-CLOSED: VERIFIED. SS33 CONJUNCTS PRESERVED: YES.**

*Observation O-2 (non-blocking):* §33A's "the §33 steps 1–9 **verbatim**"
together with the separate §38A exact-consumer check (REQ-236.1) is slightly
redundant about which consumer inventory step 9 consults — step 9 resolves
because §38A / REQ-239 explicitly enumerates the certification coordinator into
the authorized-consumer set, and REQ-236.1 then narrows to exact identity.
Fail-closed behaviour is preserved; recorded as a wording observation.

## 8. Mint authority / capability semantics — VERIFIED

- **GENERIC PRODUCTION WRITER AUTHORITY: NOT INTRODUCED** — the factory is
  dedicated, certification-category-only, role-allowlist constrained,
  fail-closed; it is not `production_writer(role=…)` for arbitrary roles.
- **MINT REMAINS PROTECTED** — ordinary `HPACStoreAuthority.writer()` cannot
  self-select a PRODUCTION certification role; no public general-purpose
  production mint; no caller-controlled escalation.
- **NON-BEARER / PROCESS-LOCAL / RESTART-DEAD / SINGLE-USE: VERIFIED** — §49A /
  REQ-258/259: §45–§48 apply "**verbatim**"; single-use per role **per one
  authentication ceremony**; `scripts/hpac_certification_admin.py` is
  short-lived, one ceremony per invocation, process exits after; no capability
  survives its ceremony. Any type change to enforce this is **additive**
  (spent-flag / one-shot wrapper), never a weakening (REQ-260).
- **REMINT / DELEGATION / ROLE ESCALATION: DENIED — VERIFIED** — REQ-250
  ("FACTORY ≠ CONSUMER, CONSUMER ≠ MINTER"): possession of any/all five
  capabilities does not permit remint, delegate, convert-to-generic, serialise,
  store, or reissue; a second `certification_writer` call re-runs the full §33A
  sequence.
- **HPAC-PRESENTATION-EVIDENCE/2.0: OUTSIDE the family** (§42B / REQ-248) — the
  coordinator reuses the existing `mint_protected_presentation_evidence_writer`
  path **unchanged** and *consumes* the evidence; the §20 evidence-writer
  boundary and HPAC-PPA-001 v1.0 are unaffected.
- **CURRENTNESS / REPLAY: PRESERVED** (§44A / REQ-257) — challenge expiry &
  single-use, proof expiry, presentation-evidence single-use, counter
  currentness all preserved; v1.3 introduces **no** new TTL; the coordinator
  SHALL NOT bypass any.

## 9. §68A walls + PAWA-INV-13 — VERIFIED

| Wall | Result |
|---|---|
| certification authority ≠ execution authority (Gate 6–10, `DispatchEnvelope`, no-go override, runtime approval, PB permission, policy exception, RE result, runtime capability, adapter admission, runtime state transition) | **VERIFIED** (REQ-261) — path "**terminates no later than the bounded Gate-5 certification result**" |
| coordinator ≠ human approver (cannot manufacture APPROVE / REJECT / UP / UV / real presentation / real assertion); deployment owner ≠ human approver | **VERIFIED** (REQ-262; §46 preserved) |
| real ≠ deterministic (possession of the five capabilities never converts deterministic auth/presentation into REAL assurance; `verify_human_authentication(require_real_assurance=True)` still requires every record `authority_class is PRODUCTION` **and** the real auth-mechanism id **and** the real presentation-mechanism id, HPAC-PPA-REQ-057 — "the coordinator only makes those PRODUCTION records reachable, it does not relax the check") | **VERIFIED** (REQ-263) |
| PB / policy wall (no PB ALLOW, no POL override, no POL-005 bypass) | **VERIFIED** (REQ-261) |
| RE / runtime wall (no RE ALLOW, no runtime/plugin capability, no adapter admission, no `DispatchEnvelope` execution) | **VERIFIED** (REQ-261) |
| Gate 5 not manufactured / not bypassed; Gate-5 success not turned into a bearer token | **VERIFIED** (REQ-264) |
| Gate-5 termination — no clause implies automatic continuation to Gate 7/8/9/10 / `adapter.dispatch` / external effect | **VERIFIED** (REQ-261/268); **FIRST GOVERNED RUNTIME EXTERNAL EFFECT: ABSENT / UNREACHABLE** |
| N-16-6 / N-16-7 exclusion — v1.3 contains no runtime-enablement clause | **VERIFIED** (REQ-268); N-16-7 strictly last |

**PAWA-INV-13** independently read: it precisely captures the non-escalation
invariant (one enumerated non-agent-importable consumer + closed five-role
single-use / process-local / non-bearer / restart-dead family + dedicated §33A
mint reusing §33 verbatim + fail-closed; never manufactures APPROVE/REJECT/UP/UV
/ real presentation / real assertion / PRODUCTION `AuthenticatedHumanPrincipal`
/ Gate result / PB-policy-RE decision / runtime capability / `DispatchEnvelope`
/ external effect; deterministic inputs never become REAL; path terminates at
Gate-5; no wildcard/prefix/glob; no new `pawa_failure_code`; no RHAMP-001 edit;
no protected-root schema change). It is not redundant-but-weaker than other
requirements and does not authorize an effect by denying another.

## 10. Failure vocabulary / schema / cross-contract sufficiency — VERIFIED

- **NO NEW `PawaOperation`** — `PawaOperation` enum (primary source) has exactly
  `{enroll_principal, revoke_principal, enroll_credential, revoke_credential,
  initialize_credential_sidecar_state, configure_presentation_mechanism}`; no
  `certify_*`; the certification family "is **not** a new `PawaOperation`"
  (REQ-245). Independently assessed: the five per-authentication `proofs/v2` /
  counter-state lifecycle writes are correctly representable **without** a new
  operation — they are not protected principal-administration mutations and a
  single multi-role `PawaOperation` (rejected option D) would weaken the
  per-role / per-write binding.
- **NO NEW `pawa_failure_code`** — `PAWA_FAILURE_CODES` has exactly **21**
  values (source `assert len == 21`), byte-unchanged since H0. Each v1.3 denial
  maps truthfully (§42C): caller ≠ §38A consumer → `unauthorized_factory_consumer`
  (#15); role ∉ allowlist incl. terminator/wildcard/prefix/arbitrary →
  `operation_scope_invalid` (#16); malformed/`None`-bypass session/principal/
  credential/proof id → `operation_scope_invalid` (#16); unresolvable/revoked/
  unbound target → `operation_scope_invalid` (#16, consistent with the §42
  REQ-228 precedent); wrong session/subject/role/chain-head → `target_scope_invalid`
  (#17); reuse after write/ceremony/rotation/restart → `capability_stale` (#18);
  forged/deserialised → `reconstruction_attempt` (#20); §33A conjunct failure →
  its exact existing §56 code; unclassified → `internal_fail_closed` (#21).
  REQ-254 provides the fail-closed "BLOCKED-on-contract-compatibility" escape
  for any future unmappable case — no code is ever silently added.
- **NO NEW `terminal_reason_code` / NO RHAMP EDIT** — `TERMINAL_REASON_CODES`
  has exactly **41** values, byte-unchanged; RHAMP-001 v1.0 contract
  byte-unchanged (`REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`
  hash `87f7529c0cb1` at `b2530066` = `76523d8c` = V0). The §57 PAWA→RHAMP map
  is unchanged; `set(RHAMP_TERMINAL_REASON_MAP) == set(PAWA_FAILURE_CODES)`
  holds in source.
- **NO NEW SCHEMA FIELD / ARTIFACT** — `src/pcae/core/hpac_pawa_schemas.py`
  (holds `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` and
  `HPAC-PAWA-CURRENT-GENERATION/1.0`) byte-unchanged since H0 (hash
  `771d4416a61d`); REQ-275: the certification family adds no field, no
  protected-root artifact, no provisioning step — it consumes the
  already-provisioned anchor exactly as the §42 factory does.
- **NO COMPANION CONTRACT REQUIRED** — coordinator recognition, five-role
  minting, lifecycle binding, and effect termination are all normatively
  complete inside HPAC-PAWA-001 v1.3 plus the existing referenced contracts;
  "v1.3 is additive and authority-preserving; no parent cascade."

**Cross-contract byte identity (V12_BASELINE `ab5b471d` = V13_FREEZE `76523d8c`
= V0 `4977a2e5`):**

| Artifact | Hash | Result |
|---|---|---|
| HPAC-001 v2.1 (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`) | `59508ef00e39` | **BYTE-UNCHANGED** |
| RHAMP-001 v1.0 (`REAL_HUMAN_AUTHENTICATION_MECHANISM…CONTRACT.md`) | `87f7529c0cb1` | **BYTE-UNCHANGED** |
| HBDC-001 v1.2 (`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) | `0fc604235a0b` | **BYTE-UNCHANGED** |
| HPAC-PPA-001 v1.0 (`HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`) | `7fc0a2a170d8` | **BYTE-UNCHANGED** |
| HATP trusted-provenance (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`) | `1d68d9b68dc8` | **BYTE-UNCHANGED** |
| descriptor + current-generation schemas (`hpac_pawa_schemas.py`) | `771d4416a61d` | **BYTE-UNCHANGED** |

**Cross-contract semantic consistency: VERIFIED** — §96's verifier-only rule is
**specialized** by the §42B narrow enumerated exception, not left in
contradiction; the closed-consumer language of §38 / §87 is **extended by
explicit enumeration** (§38A), not opened; RHAMP credential / counter /
authentication semantics, HPAC assurance issuance, protected-presentation
authority, HBDC trust, Gate-5 consumption, and currentness/revocation are all
consumed as-is.

## 11. Mechanism / principal neutrality; no instance data — VERIFIED

- **MECHANISM FLEXIBILITY: PRESERVED** (REQ-266) — v1.3 hardcodes no YubiKey /
  USB / AAGUID / hardware brand / `pcae-protected-local-presentation/1.0` into
  the category or the five roles; lifecycle authority is frozen at the
  mechanism-neutral HPAC layer; future mobile / passkey authentication profiles
  and future mobile protected-approval profiles remain possible.
- **PRINCIPAL MECHANISM-NEUTRAL** — no requirement redefines the human principal
  as a FIDO2 identity; `PrincipalRecord` stays mechanism-neutral;
  `human principal ≠ credential`.
- **NO INSTANCE DATA IN THE CONTRACT** (REQ-267) — the only occurrences of a
  concrete principal / credential id (`hp-8cee9b36…`, `hpc-2e7bbfa0…`) are
  inside the two clauses (§7B row, REQ-267) that **forbid** freezing them, each
  with an ellipsis, in "SHALL NOT normatively freeze" framing — never as
  normative authority data. No counter value, AAGUID, helper installation id,
  anchor id, or specific challenge/operation is frozen.

## 12. Historical guard reconciliation — INDEPENDENTLY VERIFIED

Guard-attribution baseline re-derived from git topology: `b2530066` is the
predecessor (contract-freeze) phase-entry SHA — `b2530066` → `ab5b471d`
(open-phase-task commit; contract byte-identical) → `76523d8c` (freeze). The
v1.2 contract-text baseline blob is therefore `ab5b471d` (contract hash
`197807ab…` at both `b2530066` and `ab5b471d`; `d779f912…` at `76523d8c` and
V0).

`git diff --name-only b2530066..HEAD` = evidence JSON + report + metadata +
PROJECT_STATUS + CHANGELOG + tasks + **one** `docs/contracts` file + **25** test
files. **Production source, scripts, and `pyproject.toml`: empty diff.**

Independent scrutiny of the test-file changes:

- **No `def test_` was removed, renamed, or disabled** across all 25 changed
  files (`_defs(old) ⊆ _defs(new)` for every file; the only `-def test_…` /
  `+def test_…` pairs are `test_61_no_contract_change` / `test_78_no_contract_change`
  reformatted from one-liners, names preserved).
- **No `pytest.mark.skip` or `xfail` was added** (per-file count non-increasing).
- **Point-in-time guard reconciliations** (phase-aware, widened-not-weakened):
  - `…30r_4r_contract_reconciliation.py::test_32` — `== ""` → `⊆ {PAWA
    contract}` since `R4R_FINALIZED`; still asserts only the PAWA file changed.
  - `…30r_4r_contract_reconciliation.py::test_33` — `== range(1,234)` →
    `in (range(1,234), range(1,276))`; the "closed / sequential / no gaps / no
    duplicates" property is unchanged, only the ceiling moves.
  - `…30r_3_3r_decomposition_adjudication.py::test_rhamp_001_byte_unchanged_since_baseline_a`
    — the already-stale broad "no `docs/contracts` file changed" form is
    replaced by (a) a **tighter** assertion that RHAMP-001 *itself* is
    byte-unchanged and (b) a bound that later contract deltas ⊆ {PAWA, PPA}.
  - `…f7…::test_61_no_contract_change`, `…f8…::test_78_no_contract_change` —
    `== ""` → `⊆ {PAWA contract}`; an arbitrary other contract edit still fails.
- **Three byte-freeze meta-guards** converted to token-safe not-weakened checks
  (`_defs(old) ⊆ _defs(new)`; `new.count("pytest.mark."+"skip") ≤ old.count(...)`;
  `new.count("x"+"fail") ≤ old.count(...)`) — these are **additive
  strengthening**; each still proves its intended historical property and adds
  a no-false-green guard. Token-splitting is cosmetic (avoids self-tripping
  sibling scanners).

**Attributable functional regressions since `b2530066`: 0.** (Per predecessor
guard-set A/B: 149→146 failed, 0 attributable regressions, 3 pre-existing
incidentally repaired; independently reconfirmed no `def test_` removed and no
skip/xfail added.)

**HISTORICAL GUARD RECONCILIATION: INDEPENDENTLY VERIFIED — NOT WEAKENED.**

## 13. Phase-alias parser finding — REPORTING-UX-1 (NONBLOCKING DISPLAY LIMITATION)

`pcae architecture-status inspect` reports:
> `## Current Phase section present but its phase-ID/title line did not parse — current phase could not be identified`

Investigated read-only. Classification: **A — DISPLAY / PARSER LIMITATION
ONLY**, not a canonical identity / report-trust defect:

- The full canonical phase id is present, correct, and complete in the
  canonical predecessor phase report title and in this report's title.
- `.pcae/phase-completion-metadata.json` and the governed task lifecycle carry
  the exact canonical id.
- The phase-report trust gate consumes the canonical id correctly (predecessor
  report status: complete; `pcae check` / `pcae status coherence`: pass).
- The alias (`N16-5-H3-PAWA13` / `N16-5-H3-PAWA13-IV`) is **display-only** and
  is not a phase id, a CPIPC authority, a task-identity substitute, a
  report-trust key, a commit-authority token, or a lifecycle-ordering token.
- The **only** consumer failing is the `architecture-status` current-phase
  parser, whose regex does not recognise the alias-enhanced
  `## Current Phase` prose formatting the predecessor introduced.

Recorded as prospective finding **REPORTING-UX-1** (architecture-status
current-phase display parser does not recognise alias-enhanced phase-title
formatting while canonical phase identity and report trust remain correct). It
is **not** an H-3 prerequisite and is **not** repaired here; a separate
reporting-UX / parser phase is recommended.

## 14. Boundaries held

| | |
|---|---|
| src/pcae production behaviour modified | **NO** (`git diff V0..HEAD` touches no `src/pcae/`) |
| `certification_writer` / `hpac_certification_coordinator` / `scripts/hpac_certification_admin.py` implemented | **NO** (none exist) |
| new production mint function / `PawaOperation` added | **NO** |
| HPAC-PAWA-001 v1.3 normative text changed by this IV | **NO** (`76523d8c:…contract == V0:…contract == working tree`) |
| any other frozen contract amended | **NO** |
| protected host / principal / credential / counter state touched | **NO** |
| YubiKey interaction / `makeCredential` / `getAssertion` / FIDO2 PIN | **0 / 0 / 0 / 0** |
| APPROVE / REJECT / presentation evidence / challenge / auth proof / Gate-5 | **0 / 0 / 0 / 0 / 0 / 0** |
| protected-root writes | **0** |
| `require_real_assurance=True` invoked / PRODUCTION `AuthenticatedHumanPrincipal` minted | **NO / NO** |
| H-3 repaired / N-16-5 closed / N-16-6 begun / N-16-7 begun | **NO / NO / NO / NO** |
| runtime execution enabled / first governed runtime external effect invoked | **NO / NO** |

`pcae runtime inspect`: `not_implemented` / `Observed` / `observe` /
`unavailable`; **0 plugins / 0 capabilities**. First governed runtime external
effect: **ABSENT / UNREACHABLE**.

## 15. Fresh IV test suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_pawa_v1_3_contract_iv.py`
— **74 tests, 0 failures**. Coverage: CPIPC lineage; immutable v1.2 baseline &
v1.3 freeze reconstruction; normative delta; MINOR/S-2 + full §152 review;
REQ/invariant inventory; historical `REQ-087/088/223/224` traceability; closed
category & primary-source-grounded five-role allowlist; terminator/wildcard/
prefix denial; §33↔§33A conjunct reuse & fail-closed; dedicated factory /
non-generic / non-bearer / process-local / restart-dead / single-use / no
remint / no delegation; per-role bounded authority; presentation-evidence
outside the family; §68A walls; `PawaOperation` (primary source) / 21
`pawa_failure_code` / 41 `terminal_reason_code` / schema byte-identity;
cross-contract byte identity; mechanism/principal neutrality; no instance ids;
predecessor guard-edit independence (no `def test_` removed, no skip/xfail
added); no certification production module; runtime unchanged; N-16-5 open.

**Full repository suite** (`python -m pytest -n auto`): the `-n auto` collection
is blocked by a **pre-existing** environmental defect —
`tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py`
(last touched Phase 149O.1I, `ab083895`) uses `str(uuid.uuid4())` inside
`@pytest.mark.parametrize` tuples (lines 263, 828), producing non-deterministic
collection ids and the xdist "Different tests were collected between gw0 and
gwN" error. This reproduces identically with this phase's test file removed and
is **not attributable** to this IV. The suite was run with that one file
isolated: `<PYTEST_RESULT>`. That file run standalone (`-n0`):
`<PYTEST_1H_RESULT>`.

## 16. Governance

```
DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

No delegated worker changed normative contract text, implemented H-3,
finalized, committed, pushed, mutated protected state, or performed a ceremony.
The primary operator owns canonical lifecycle completion. No `--no-verify`, no
force push, no history rewrite, no hook bypass — governed PCAE lifecycle only.

## 17. Required final verdicts

```
PHASE ALIAS:                                   N16-5-H3-PAWA13-IV (display-only)
HPAC-PAWA-001 VERSION:                          v1.3
v1.3 NORMATIVE DELTA:                           INDEPENDENTLY RECONSTRUCTED
VERSION CLASSIFICATION:                         MINOR S-2 VERIFIED
AUTHORIZED FACTORY-CONSUMER SET:                CLOSED
CERTIFICATION FACTORY-CONSUMER CATEGORY:        INDEPENDENTLY VERIFIED
CERTIFICATION ROLE ALLOWLIST:                   { hpac_challenge_coordinator,
                                                 hpac_assertion_recorder,
                                                 human_authentication_proof_verifier,
                                                 hpac_gate5_binder,
                                                 hpac_rhamp_counter_state_verifier }
TERMINATOR:                                     DENY VERIFIED
UNKNOWN ROLE:                                   DENY VERIFIED
WILDCARD / PREFIX ROLE:                         DENY VERIFIED
SS33A RECOGNITION SEQUENCE:                     INDEPENDENTLY VERIFIED
SS33 CONJUNCTS PRESERVED:                       YES
RECOGNITION FAIL-CLOSED:                        VERIFIED
GENERIC PRODUCTION WRITER AUTHORITY:            NOT INTRODUCED
NON-BEARER:                                     VERIFIED
PROCESS-LOCAL:                                  VERIFIED
RESTART-DEAD:                                   VERIFIED
SINGLE-USE / ONE-CEREMONY:                      VERIFIED
REMINT:                                         DENIED VERIFIED
DELEGATION:                                     DENIED VERIFIED
ROLE ESCALATION:                               DENIED VERIFIED
ORDINARY LAUNCHER:                              UNAUTHORIZED VERIFIED
HELPER:                                         UNAUTHORIZED VERIFIED
ORDINARY VERIFIER:                              UNAUTHORIZED VERIFIED
ORDINARY GATE:                                  UNAUTHORIZED VERIFIED
RUNTIME:                                        UNAUTHORIZED VERIFIED
AGENT:                                          UNAUTHORIZED VERIFIED
ORDINARY CLI:                                   UNAUTHORIZED VERIFIED
PLUGIN:                                         UNAUTHORIZED VERIFIED
HUMAN APPROVAL WALL:                            VERIFIED
REAL-vs-DETERMINISTIC WALL:                     VERIFIED
PB WALL:                                        VERIFIED
POLICY WALL:                                    VERIFIED
RUNTIME / EFFECT WALL:                          VERIFIED
GATE-5 TERMINATION:                             VERIFIED
NO NEW PawaOperation REQUIRED:                  VERIFIED
NO NEW pawa_failure_code REQUIRED:              VERIFIED
NO NEW RHAMP terminal_reason_code REQUIRED:     VERIFIED
NO NEW SCHEMA FIELD REQUIRED:                   VERIFIED
NO COMPANION CONTRACT REQUIRED:                 VERIFIED
CROSS-CONTRACT BYTE IDENTITY:                   VERIFIED
CROSS-CONTRACT SEMANTIC CONSISTENCY:            VERIFIED
MECHANISM FLEXIBILITY:                          PRESERVED
HISTORICAL GUARD RECONCILIATION:               INDEPENDENTLY VERIFIED
PHASE-ALIAS PARSER FINDING:                     NONBLOCKING DISPLAY LIMITATION (REPORTING-UX-1)
PRODUCTION IMPLEMENTATION:                      NOT PERFORMED
REAL CEREMONY:                                  NOT PERFORMED
HPAC-PAWA-001 v1.3:                             INDEPENDENTLY VERIFIED
H-3 CONTRACT BLOCKER:                           INDEPENDENTLY VERIFIED RESOLVED
H-3 PRODUCTION IMPLEMENTATION:                  PENDING
H-3:                                           CONTRACT VERIFIED — IMPLEMENTATION PENDING
F-5:                                           DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED PENDING H-3 IMPLEMENTATION
N-16-5:                                         NOT CLOSED
N-16-6:                                         OPEN / UNTOUCHED
N-16-7:                                         OPEN / UNTOUCHED / STRICTLY LAST
RUNTIME:                                        Observed / observe / unavailable
FIRST GOVERNED RUNTIME EXTERNAL EFFECT:         ABSENT / UNREACHABLE
```

## 18. Non-blocking observations

- **O-1** — §153's "metadata mutation family" permit is applied at its broadest
  to cover authentication-lifecycle records; within the contract's own §80.3 /
  REQ-269 S-2 discipline and the v1.2 §80.2 precedent. Not a defect.
- **O-2** — §33A "steps 1–9 verbatim" + the separate §38A exact-consumer check
  is slightly redundant about which inventory step 9 consults; fail-closed
  behaviour is preserved. Not a defect.
- **REPORTING-UX-1** — `architecture-status` current-phase display parser does
  not recognise alias-enhanced phase-title formatting; canonical identity and
  report trust are unaffected. Not an H-3 prerequisite; not repaired here.

## 19. Required next phase (derived, NOT begun)

**N-16-5 Production Certification Authority-Path Implementation Against
HPAC-PAWA-001 v1.3 — H-3 Repair** (alias **N16-5-H3-IMPL**).

Canonical successor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R`
(this IV's direct `.1R` successor; **recommended, NOT reserved**; requires its
own explicit human authorization; own human authentication).

It SHALL implement: the §38A `certification_writer` factory behind the §37
non-agent-importable fence; the §33A recognition sequence (§33 steps 1–9 reused
+ certification-consumer / role-allowlist / session-binding / mint / audit); the
closed five-role production mint path with per-role store/action guards; the
single-use one-shot wrapper / spent flag; the certification-session and subject
binding; `pcae.core.hpac_certification_coordinator`; the standalone
`scripts/hpac_certification_admin.py`; the §39A consumer-inventory guard; the
fixture-only seam guard; and a test that the coordinator cannot mint a
PRODUCTION principal, a Gate result, a PB / RE / runtime decision, or an
external effect. It SHALL require **no** test seals and perform **no** real
ceremony; it finishes H-3 as **REPAIRED / IV PENDING**.

Then: a dedicated implementation IV (**N16-5-H3-IV**, not merged into the
implementation) → a fresh final real-human / genuine-YubiKey **N-16-5
certification** (**N16-5-FINAL-CERT**, a fresh CPIPC-valid successor id — do not
reuse a completed certification phase id). N-16-6 / N-16-7 remain OPEN /
UNTOUCHED; N-16-7 strictly last.

**Do not begin `N16-5-H3-IMPL` / `N16-5-H3-IV` / `N16-5-FINAL-CERT` / N-16-6 /
N-16-7. Do not implement or call the first external effect. Do not enable
execution.**

```
DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```
