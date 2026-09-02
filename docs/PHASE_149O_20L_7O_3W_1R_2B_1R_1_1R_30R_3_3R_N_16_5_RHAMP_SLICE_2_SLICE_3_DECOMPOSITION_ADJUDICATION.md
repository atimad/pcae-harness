# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R — N-16-5 RHAMP Slice 2 / Slice 3 Decomposition Adjudication

**Status: ADJUDICATION COMPLETE — DECISION A (RE-MERGE) SELECTED — RHAMP-001 v1.0
PRESERVED BYTE-UNCHANGED — NO PRODUCTION CODE CHANGED — IMPLEMENTATION NOT BEGUN.**

**Phase type:** governed architecture / decomposition adjudication (operator
authority). No `src/pcae/**` change, no `scripts/**` change, no normative
contract change. One verification-only adjudication test suite added.

**Phase-entry SHA (V):** `93266b7d64d514ec5c5456fa04c9ea96a610aa92` — the
finalized `.1R.30R.3.3` head (`git log` subject: *"Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3: reconcile governed push state in BLOCKED
completion metadata (pushed; origin/main..HEAD = 0)"*). At entry
`git status --branch --short` showed `## main...origin/main` with a clean tree
and `git rev-list --count origin/main..HEAD == 0`.

**Immutable adjudication baseline (A):** `93266b7d64d514ec5c5456fa04c9ea96a610aa92`.
A == V. A was derived independently by reading `git log --oneline` and taking
the latest phase-completion / push-reconcile commit as the canonical finalized
head — not inherited from prose.

**Authorizing operator:** primary human-authorized operator (this phase's own
explicit authorization; phase ID `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R`
recommended, NOT reserved; confirmed CPIPC-valid — see §21).

**Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
plugins / 0 capabilities. **First external effect: ABSENT / UNREACHABLE.**

**`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved (§20).

---

## 0. Executive verdict

The historically BLOCKED phase `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3` correctly
identified a **decomposition blocker**: RHAMP-001 v1.0 binds canonical FIDO2
credential registration to the real CTAP2 `authenticatorMakeCredential`
ceremony (RHAMP-REQ-043 / -048 / -055 / -056 / -069 / -150), defines **no**
material-less / staged / placeholder / administratively-supplied-material
enrollment mode, and (RHAMP-REQ-156 / §72 freeze verdict) bundles "mechanism +
registry + bootstrap" into **one atomic implementation phase** — it never
severs that phase at the operator's Slice-2 (registry + counter-state +
enrollment, no FIDO2) / Slice-3 (`FIDO2HumanAuthenticator` + native CTAP2)
boundary.

Three candidate architectures were evaluated against the frozen contract and
its own versioning rules:

| | Candidate | Verdict |
|---|---|---|
| **A** | **Re-merge** — fold the former Slice 2 + Slice 3 back into RHAMP-REQ-156's single `.1R.30` bundle (minus the already-CLOSED PAWA writer anchor), implemented and independently verified as one unit; **zero contract change**. | **SELECTED** |
| **B** | RHAMP-001 v1.1 contract evolution defining a staged / material-deferred enrollment (`PENDING_MATERIAL` lifecycle, two-step publish). | **REJECTED** — requires at minimum a MINOR and plausibly a MAJOR + an HPAC-001 v2.1 cascade (RHAMP-REQ-167); introduces a pseudo-authoritative intermediate credential state (violates decision-quality bar #7); delivers no security benefit not already available under A. |
| **C** | Material-free Slice-2 re-scope — schemas + store code + path/provenance validation + counter primitives + PAWA plumbing + structurally-NON_REAL fixtures only; move `makeCredential` + real enrollment + first-credential bootstrap + ACTIVE publish to Slice 3; **no contract text change**. | **REJECTED** — no Slice-2 artifact under C is canonical RHAMP registration state (it is pre-implementation scaffolding, not a RHAMP slice); its one genuine benefit (developing the store layer without the CTAP2 ceremony in the diff) is **fully available inside Candidate A** via the RHAMP-REQ-154 deterministic NON_REAL fixture; it adds a phase boundary + an IV pass with no isolation dividend and risks a scaffolding phase mislabeled as enrollment. |

**Decision: A. RHAMP-001 v1.0 is preserved byte-for-byte. No future contract
change is required for N-16-5.** The recommended successor is a single fresh
merged-mechanism implementation phase `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4`
followed by its independent verification `.1R.30R.3.5`; the historical
`.1R.30R.3.3` BLOCKED verdict and all historical BLOCKED artifacts remain
immutable; the former `.1R.30R.3.4 / .3.5 / .3.6` recommendations are
**superseded, not reserved, not to be reused blindly**.

N-16-5 remains **NOT CLOSED**.

---

## 1. Phase identity and SHAs

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R`
- **Title:** N-16-5 RHAMP Slice 2 / Slice 3 Decomposition Adjudication
- **Phase-entry SHA (V) / immutable baseline (A):**
  `93266b7d64d514ec5c5456fa04c9ea96a610aa92` (A == V).
- **Prior finalized phase:** `.1R.30R.3.3` (BLOCKED — decomposition blocker;
  immutable).
- The historical `.1R.30` BLOCKED anchor, the historical `.1R.30R.3.2` BLOCKED
  anchor, and the historical `.1R.30R.3.3` BLOCKED anchor are unchanged, not
  reused, not resumed by this phase.

## 2. Primary sources read

**Governing contract (read in full):**

- **RHAMP-001 v1.0** —
  `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`
  (1580 lines, read in full). Load-bearing: §0 (fail-closed), §1
  (companion-not-amendment; RHAMP-REQ-001..004), §2 (`rhamp_schema_version`),
  §4 (`mechanism_id` allowlist; RHAMP-REQ-011..013), §5 (`verifier_kind`
  allowlist), §6–§8 (RP / canonical client-data / no-false-origin-claim), §9–§10
  (authenticator profile, UP/UV floor), §11 (authentication ≠ approval), §12
  (ceremony model + frozen stage order; RHAMP-REQ-039..042), **§13 (credential
  registration profile — RHAMP-REQ-043..046)**, **§14 (first-credential
  bootstrap authority — RHAMP-REQ-047..050)**, §15 (enrollment evidence —
  RHAMP-REQ-051/052), §16 (multi-credential), **§17 (`CredentialRecord` +
  `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar — RHAMP-REQ-055..058)**, §18 (private-key
  / PIN / biometric boundary), §19 (attestation), **§20–§22 (signature-counter
  policy + `RHAMP-COUNTER-STATE/1.0` + linearization — RHAMP-REQ-065..073)**,
  §23–§25 (TTLs), §26–§27 (challenge entropy, replay), §28–§35 (protected
  presentation helper), §36–§37 (client-data binding + assertion verification —
  RHAMP-REQ-101..103), §38 (HATP FIDO2 provider reuse boundary —
  RHAMP-REQ-104/105), §39 (dependency policy), §40 (mechanism-registry
  evolution — RHAMP-REQ-109/110), §41 (NON_REAL non-upgradeability —
  RHAMP-REQ-111..113), §42 (ownership), §43 (revocation), §44 (credential
  generation / currentness — RHAMP-REQ-118..120), §45–§47 (proofs, proof
  writer), §48 (retention/privacy), **§49 (41-code `terminal_reason_code`
  table — RHAMP-REQ-129/130)**, §50 (terminal-reason semantics), §51–§56
  (transport / topology / deferrals), §57–§60 (helper IPC / concurrency /
  restart / recovery), §61 (protected-admin enrollment / audit —
  RHAMP-REQ-150/151), §62–§63 (mandatory real-hardware + automated fixture
  policy — RHAMP-REQ-152..155), **§64 (implementation / IV decomposition —
  RHAMP-REQ-156/157)**, §65 (N-16-6 / N-16-7 separation), §66 (N-23), §67
  (guard-impact expectations), §68 (contract-production equivalence), §69
  (normative matrices index), **§70 (versioning — RHAMP-REQ-166..169)**, §71
  (RHAMP-INV-001..018), §72 (freeze verdict).

**Freeze / lineage artifacts (read in full):**

- `.1R.29` RHAMP-001 v1.0 contract-freeze report
  (`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_29_...md`, 630 lines) — §23
  (existing-contract versioning re-derivation, the companion-contract
  rationale), §25 (frozen implementation / IV sequence), §27 (STOP-condition
  check — none applied), §29 (recommended `.1R.30` scope).
- `.1R.30R.3.3` BLOCKED artifact
  (`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_3_...md`, 556 lines) — the
  decisive finding (§4), the blocker classification (§15), the recommended
  successor candidates (§16).
- `.1R.30R.3.2.1.1` IV artifact, `.1R.30R.3.2.1` repair artifact, historical
  `.1R.30R.3.2` BLOCKED artifact, `.1R.30R.3.1` Slice-1 implementation
  artifact, `.1R.30R.2A.3` contract IV, `.1R.30R.2A.2` PAWA v1.1 freeze,
  `.1R.30R` HPAC-REQ-022/023 architecture and contract adjudication,
  historical `.1R.30` BLOCKED artifact — read via `git show` / on-disk for the
  Slice-1 CLOSED state, the PAWA writer-anchor carve-out rationale, and the
  N-16-5-NOT-CLOSED correction chain.
- `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.1) — the Slice-1 administrative-authority model the merged
  successor consumes. Byte-unchanged by this phase.
- `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.1) —
  `CredentialRecord` (HPAC-REQ-013), create/append-only registry
  (HPAC-REQ-015), `{active, revoked}` monotonic status (HPAC-REQ-062),
  enrollment authority (HPAC-REQ-022..024), authority-generation snapshot
  (HPAC-REQ-098a). Byte-unchanged by this phase.
- `docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md` (CPIPC-001 v1.0) —
  §4.2 grammar (`phase-id = series , branch , { "." , subphase-segment }`;
  `numeric-segment = digit , { digit } , [ letter , { letter } ]`), for the
  successor-ID validity check (§21).
- `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001
  v2.0 §12 condition 7 — names "HPAC-001 v2.1" literally), and the versioning
  sections of RIASC-001 v3.0, RDGO-001 v3.1, `HPAC-AUTHORITY-CONSUMPTION` /2.1
  — for the Candidate-B cascade analysis (§16).

**Production source read READ-ONLY as implementability / scope-fence evidence
(not modified):**

- `src/pcae/core/hpac_verifier.py` —
  `_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.deterministic.test-only.v1"})`
  (L128); `_verify_assertion_material` (L429) — *"does not attempt real
  signature math"*, `proof.mechanism_id not in _ELIGIBLE_MECHANISM_IDS` reject
  at L460; `_check_up_uv` (L467); `_authority_class_of` (L485);
  `verify_human_authentication` with `require_real_assurance` at L508 / L705 —
  *"rejects unless every resolved record's class is PRODUCTION"*;
  `is_verifier_authenticated_principal` — the trust boundary.
- `src/pcae/core/human_principal_registry.py` — `REGISTRY_SCHEMA_VERSION =
  "HPAC-REGISTRY/2.0"`; `CredentialRecord` closed fields (`credential_id,
  principal_id, mechanism_id, public_key, assurance_capabilities, status,
  enrollment_provenance_ref, enrolled_at, revoked_at` — **no private-key / PIN
  / biometric / pending-material field exists**); `HumanPrincipalRegistryStore`
  production writer path; `enroll_credential` / `revoke_credential`.
- `src/pcae/core/hpac_protected_admin_writer.py`,
  `src/pcae/core/hpac_pawa_agent_exclusion.py`,
  `src/pcae/core/hpac_pawa_schemas.py`, `src/pcae/core/hpac_foundation.py`,
  `src/pcae/core/human_principal_registry.py` — the Slice-1 PAWA
  `production_writer()` factory, the one-operation `ProductionWriterHandle`,
  the HPAC-REQ-023 deployment-owner anchor — read to confirm the merged
  successor has a real administrative-authority entry point to consume.
- `src/pcae/core/approval_presentation.py` — `verifier_kind !=
  "deterministic-test-fixture"` reject; `PresentationMechanismDescriptor`;
  `TrustedApprovalPresentationStore` — read to confirm the protected
  presentation stays a *later* phase, unaffected by Decision A.
- `src/pcae/core/hatp_fido2_provider.py` — `_HATP_RP_ID = "hatp.pcae.local"`,
  `_HATP_ORIGIN`, `_RP_ID_HASH`; `CoseKey.parse(cbor.decode(record.public_key))`
  + `cose_key.verify(bytes(authenticator_data) + client_data.hash, signature)`;
  `is_user_present()` — **UP only, no UV check** (finding N-16-5-3);
  `CollectedClientData.create(...)`; `allow_list=[{"type": "public-key", "id":
  credential_id}]`; `CtapHidDevice.list_devices()` monkeypatched in tests. Read
  to inventory the reusable authority-neutral CTAP2 primitives (§18).
- `src/pcae/core/runtime_dispatch_gate5.py`, `runtime_dispatch_gate9.py` —
  read-only as scope fences (byte-unchanged; §19).

## 3. Initial inspection (this phase's §3)

```
git status --short                       →  (clean at entry)
git status --branch --short              →  ## main...origin/main
git rev-list --count origin/main..HEAD   →  0
git log --oneline origin/main..HEAD      →  (empty)
git log --oneline -380                   →  read; latest finalized head 93266b7d (.1R.30R.3.3)
git rev-parse HEAD                       →  93266b7d64d514ec5c5456fa04c9ea96a610aa92
pcae health            →  healthy; required files present; policy valid; lock held claude-local;
                          session continuity verified; enforcement strict; git status clean
pcae check             →  PCAE check passed; session continuity verified
pcae status coherence  →  coherent
pcae doctor task-memory→  warnings only (~16 tasks/done ⊄ DONE.md — pre-existing backlog present at A; §17)
pcae push check        →  nothing_to_push (task memory: warnings [pre-existing]; lifecycle review: missing;
                          phase report trust: passed; phase report identity: passed)
pcae runtime inspect   →  status not_implemented; state Observed; execution unavailable;
                          max capability observe; registry empty; plugins 0; capabilities 0;
                          Permission Broker execution_unavailable; governance posture non-executing
source ~/.config/pcae/telegram.env ; pcae notify status
                       →  Telegram configured, enabled, ready
pcae phase-report show --latest
                       →  149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3 (completed; report complete ✅;
                          summary: "BLOCKED -- decomposition blocker ...")
```

**Confirmed at entry:**

- `.1R.30R.3.3` **is** the latest completed phase; its status is **BLOCKED** ✔
- `origin/main..HEAD == 0` ✔
- no active governed phase at entry (idle placeholder task) ✔
- Slice 1 **is** CLOSED (`.1R.30R.3.2.1.1` independently verified the
  `.1R.30R.3.2.1` repair; PAWA v1.1 IMPLEMENTED + VERIFIED FOR SLICE 1) ✔
- N-16-5 **is** NOT CLOSED (the `.1R.30R.3.3` append-only correction stands) ✔
- runtime `Observed` / `observe` / `unavailable` ✔
- first external effect **ABSENT / UNREACHABLE** ✔

## 4. Independent reconstruction of the `.1R.30R.3.3` decomposition blocker

This section re-derives the blocker from RHAMP-001 v1.0 primary text — **not**
by citing the `.1R.30R.3.3` report. It reaches the same conclusion the BLOCKED
phase reached.

### 4.1 Requirement-by-requirement dependency table

| RHAMP-REQ | Requirement text / semantic meaning | Dependency on `makeCredential` | Why a "Slice-2-only" (no-FIDO2) implementation cannot satisfy it | Normative or explanatory |
|---|---|---|---|---|
| **RHAMP-REQ-043** (§13) | The frozen registration flow is an ordered sequence: protected-admin ceremony launch → protected presentation → protected-admin election → **CTAP2 `authenticatorMakeCredential`** → **PCAE verifies the makeCredential response, extracts `(raw_credential_id: bytes, COSE public key)`** → `HumanPrincipalRegistryStore.enroll_credential(... public_key = hex(cbor(COSE_Key)), assurance_capabilities = ("UP","UV",<"usb"|"nfc">), ...)` [atomic, read-back verified] → create the §17 sidecar and the §21 counter-state record → durable provenance → *"credential eligible for future authentication"*. | **Direct.** `enroll_credential`'s `public_key` argument and the sidecar's `raw_credential_id` / `cose_public_key` are *defined to be* the extracted outputs of a verified `makeCredential` response. | There is no `enroll_credential` invocation in RHAMP-001 v1.0 whose credential material originates from any other source. A no-FIDO2 Slice 2 has no `(raw_credential_id, COSE public key)` to pass; it can only (a) skip `enroll_credential` entirely (no registration state produced) or (b) fabricate material (RHAMP-REQ-155 violation, §4.5). | **Normative** ("SHALL" via §0; the flow is the frozen §13 matrix, RHAMP-REQ-165 item 4). |
| **RHAMP-REQ-044** (§13) | `enroll_credential` SHALL require an existing `active` `PrincipalRecord`; else `enrollment_principal_ineligible`. | Indirect — this half *is* FIDO2-free (principal selection). | Satisfiable in isolation, but it is only a precondition; it produces no credential. | Normative. |
| **RHAMP-REQ-045 / -046** (§13) | Duplicate `credential_id` / raw CTAP2 id → `enrollment_duplicate_credential`; rotation is `enroll` + `revoke`, never in-place overwrite. | Direct — the duplicate check is over a *real* raw CTAP2 credential id. | The uniqueness domain includes the raw CTAP2 credential id, which only exists after `makeCredential`. | Normative. |
| **RHAMP-REQ-047 / -048 / -049 / -050** (§14) | First-credential bootstrap ceremony SHALL require **all of**: local interactive mode; an already-canonical `PrincipalRecord`; explicit protected-administrative confirmation; a protected presentation of the exact principal + credential; **authenticator UP + UV**; **verification of the `makeCredential` response**; and **an atomic create of the first `CredentialRecord` + sidecar + counter-state + durable provenance entry**. | **Direct.** *"authenticator UP + UV"* and *"verification of the `makeCredential` response"* are inside the mandatory `"all of"` conjunction. | The BLOCKED phase's own mandate demanded a "protected-admin first-credential bootstrap" deliverable, a "publish point", and "enrollment evidence of a real transaction" — none of which exist without the ceremony inside the `"all of"`. | **Normative** ("SHALL … require all of"). |
| **RHAMP-REQ-051 / -052** (§15) | Durable enrollment evidence SHALL record the enrollment `challenge`/nonce identifier, the raw-credential-id **digest**, `credential_generation` before/after, and the enrollment **result digest** — audit evidence, not reusable authority. | Direct — the raw-credential-id digest and result digest are over `makeCredential` outputs. | An evidence record with a null / synthetic raw-credential-id digest is not the RHAMP-REQ-051 artifact. | Normative. |
| **RHAMP-REQ-055 / -056 / -057 / -058** (§17) | `CredentialRecord.public_key = hex(cbor(COSE_Key))`; the `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar is a **closed** schema with fields **exactly** `raw_credential_id` (base64url of the CTAP2 credential-id bytes) and `cose_public_key` (hex of `cbor(COSE_Key)`); *"immutable, create-only, atomically written, read-back verified"*; `allowList` construction and assertion verification read the sidecar's `raw_credential_id` + `cose_public_key`, cross-checked against the registry. | **Direct.** Both closed-schema fields are authenticator output. | RHAMP-001 v1.0 defines **no** sidecar variant without `raw_credential_id` / `cose_public_key` and **no** `PENDING_MATERIAL` credential-lifecycle state. A schema-valid canonical `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar cannot be instantiated before `makeCredential`. | **Normative** (closed schema; RHAMP-REQ-006 — an unrecognised / malformed schema fails closed). |
| **RHAMP-REQ-069** (§21) | The `RHAMP-COUNTER-STATE/1.0` record *"is created at enrollment (§13)"* with `last_accepted_meaningful = 0`, keyed by `credential_id`. | Indirect but bound — "enrollment" **is** the §13 flow that contains `makeCredential`, and the record is keyed by the `credential_id` minted in that flow. | The counter-state record has no independent existence before a credential exists; §21's canonical path is `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/counter-state.json`. | Normative. |
| **RHAMP-REQ-129 / §49.1 row 3** | Closed 41-code `terminal_reason_code` vocabulary; row 3 `enrollment_ceremony_evidence_invalid` — trigger: *"UV-required human act / **makeCredential evidence** fails verification"*. | The contract's own **enrollment failure semantics presuppose** a `makeCredential` ceremony. | A Slice-2 with no ceremony has no path to row 3 and cannot exercise the enrollment failure taxonomy it was asked to wire. | Normative. |
| **RHAMP-REQ-150 / -151** (§61) | The future enrollment command/tool SHALL require *"authenticator presence + UV"* and durable audit for enrollment/revocation/replacement/recovery. | Direct — "authenticator presence + UV" is a hardware ceremony. | Same as RHAMP-REQ-048. | Normative. |
| **RHAMP-REQ-155** (§63) | *"**No synthetic / virtual / deterministic fixture object SHALL ever become REAL authority in a production registry.**"* | Direct constraint. | A Slice-2 that populated the production `CredentialRecord` / sidecar / counter-state with administratively-supplied or test material and treated it as production credential authority violates RHAMP-REQ-155. | Normative. |
| **RHAMP-REQ-156** (§64) + **§72 freeze verdict** | The frozen successor sequence: `.1R.30` = *"Real FIDO2 credential registry **+** authentication mechanism implementation"* — its explicit scope list is a **single** bundle: production `HumanPrincipalRegistryStore` writer path; the §17 sidecar and §21 counter-state store; **the protected-admin enrollment + first-credential bootstrap ceremony tool (§13, §14)**; `FIDO2HumanAuthenticator`; real CTAP2 assertion verification incl. `FLAG.UV`; `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`; `terminal_reason_code` wiring; reuse `hatp_fido2_provider` CTAP2 primitives. §72: *"decomposed into `.1R.30` (mechanism + registry + bootstrap) → `.1R.31` (IV) → `.1R.32` (protected presentation + real-assurance wiring) → `.1R.33` (IV + mandatory real-hardware verification + N-16-5 closure)"*. | Structural. The contract's own decomposition puts registry + sidecar + counter-state + enrollment + bootstrap **in the same phase** as `makeCredential` + `getAssertion` verification + `FIDO2HumanAuthenticator`. | The operator Slice-2 / Slice-3 boundary ("Slice 2 = registry + counter-state + enrollment, no FIDO2"; "Slice 3 = FIDO2 authenticator + CTAP2 verify") is a cut **through the middle of the frozen `.1R.30` bundle** at a seam the contract never draws. | **Normative** (the `.1R.30` **scope grouping** is frozen contract text; only the phase-ID *strings* are "recommended, NOT reserved" — RHAMP-REQ-156 header, §72). |
| **RHAMP-REQ-157** (§64) | N-16-5 → N-16-6 → N-16-7; N-16-7 strictly last; no Slice C until N-16-3..7 close. | — | Unaffected by the decomposition choice; carried. | Normative. |

### 4.2 The lifecycle-state gap (decisive)

`CredentialRecord.status` is `{active, revoked}` **monotonic** (RHAMP-REQ-055
profile table; HPAC-001 HPAC-REQ-062). RHAMP-001 v1.0 defines:

- **no** `PENDING_MATERIAL` / `PENDING_REGISTRATION` / placeholder / pre-ACTIVE
  credential-lifecycle state;
- **no** enrollment "transaction identifier" that durably survives between a
  material-free step and a later ceremony step;
- **no** two-phase publish where the credential material lands after the record
  is created.

Therefore there is **no coherent canonical intermediate credential state**
short of a real `makeCredential` ceremony. This is the same fact the
`.1R.30R.3.3` phase recorded, re-derived here from the contract's status model.

### 4.3 What the operator Slice split assumed, and why it does not hold

The Slice-1 carve-out (the PAWA *writer anchor*) was **legitimate**: the
`.1R.30R` HPAC-REQ-022/023 architecture adjudication established that
writer-**capability issuance** requires only a filesystem-ownership role plus an
explicit local administrative invocation — **not FIDO2** — and that carve-out
was itself governed by a *new companion contract* (HPAC-PAWA-001, frozen at
`.1R.30R.2` / evolved to v1.1 at `.1R.30R.2A.2`, independently verified at
`.1R.30R.2A.3`, implemented at `.1R.30R.3.1`, IV-closed through `.1R.30R.3.2.1.1`).
It was not a silent re-slicing.

The Slice-2 / Slice-3 boundary assumed that canonical credential
**registration** is likewise FIDO2-free. Per §4.1–§4.2 it is not: canonical
registration and first-credential bootstrap are, in RHAMP-001 v1.0, defined
**only** as sequences that include and consume a verified `makeCredential`
ceremony, and the artifacts have no non-canonical intermediate. RHAMP-REQ-156
places enrollment + bootstrap **in the same phase** as the CTAP2 mechanism.

### 4.4 Blocker classification (independent)

**Class:** decomposition blocker — *"a real FIDO2/CTAP ceremony is required to
complete Slice 2 as scoped"* and *"there is no coherent canonical intermediate
credential state short of a real ceremony"*. Not a `CredentialRecord`-must-change
blocker (no `src/pcae` was touched; the blocker is a *missing enrollment path*,
not a schema conflict), not a PAWA-cannot-authorize blocker (Slice 1 is intact
and CLOSED), not a protected-store-cannot-be-atomic blocker, not an
unexplained-regression blocker. RHAMP-001 v1.0 is internally coherent; the gap
is exactly the operator Slice-2 / Slice-3 seam.

### 4.5 The synthetic-material trap

A Slice-2 that populated the production `CredentialRecord` / sidecar /
counter-state with administratively-supplied or deterministic-fixture material
and treated it as production credential **authority** would violate
RHAMP-REQ-155 directly. Synthetic authenticator fixtures are permitted **only**
as structurally-NON_REAL test fixtures (RHAMP-REQ-154), which by RHAMP-REQ-111
(§41) can never be relabelled / converted / "upgraded" into REAL authority.
This closes the one apparent escape hatch from the blocker.

## 5. `makeCredential` dependency graph (this phase's §5)

Node → node, with the CTAP2-`makeCredential`-dependent nodes marked **[MC]**:

```
protected-admin authorization
    (PAWA production_writer() handle — HPAC-PAWA-001 v1.1; Slice 1, CLOSED; FIDO2-free)
  → local-interactive-mode check (RHAMP-REQ-048/135)                       [FIDO2-free]
  → canonical active PrincipalRecord selection (RHAMP-REQ-044)             [FIDO2-free]
  → protected presentation of the exact principal + credential            [FIDO2-free*]
        (* enrollment-time presentation; a later concern, but not a CTAP2 node)
  → explicit protected-admin election (RHAMP-REQ-043)                      [FIDO2-free]
  → CTAP2 authenticatorMakeCredential                                     [MC]
        (rp.id = "hpac.pcae.local", ES256, UP+UV, non-discoverable, attestation "none")
  → PCAE verifies the makeCredential response                            [MC]
  → authenticator-generated raw_credential_id : bytes                    [MC]
  → COSE public key (CoseKey)                                            [MC]
  → registration validation
        (duplicate-id check over the raw CTAP2 id — RHAMP-REQ-045)       [MC]
  → HumanPrincipalRegistryStore.enroll_credential(
        public_key = hex(cbor(COSE_Key)),                                [MC]
        assurance_capabilities = ("UP","UV",<"usb"|"nfc">), ... )         [MC]
        [atomic, read-back verified, writer-provenance recorded]
  → RHAMP-FIDO2-CREDENTIAL/1.0 sidecar create
        (raw_credential_id = base64url(...), cose_public_key = hex(...))  [MC]
        [immutable, create-only, atomic, read-back verified]
  → RHAMP-COUNTER-STATE/1.0 record create
        (keyed by the credential_id minted above;
         last_accepted_meaningful = 0, generation = 0, review_flag = false) [MC-keyed]
  → principal linkage (CredentialRecord.principal_id)                     [MC]
  → lifecycle / currentness
        (credential_generation = whole-CredentialRecord digest — HPAC-REQ-098a) [MC]
  → durable enrollment provenance / audit entry (RHAMP-REQ-051)          [MC-digest]
  → credential eligible for future authentication
```

**Nodes that require a live CTAP2 `makeCredential` result:** every node from
`CTAP2 authenticatorMakeCredential` onward. The only genuinely FIDO2-free nodes
are the *preconditions* (authorization, mode check, principal selection,
election). "Slice 2 as scoped" claimed the whole right-hand column; it holds
only the left-hand preconditions.

## 6. Authentication dependency graph (this phase's §6)

`makeCredential` (registration-time) and `getAssertion` (authentication-time)
are **distinct** CTAP2 commands and are not conflated here.

```
[registration-time — from §5]
  registered CredentialRecord + RHAMP-FIDO2-CREDENTIAL/1.0 sidecar + RHAMP-COUNTER-STATE/1.0
        │
        ▼
[authentication-time — one fresh step-up ceremony per approval, RHAMP-REQ-039]
  resolve principal_id → credential_id → raw credential id (from trusted state)
  → canonical allowList = [{type:"public-key", id:<raw credential id>}]
        (all active credentials of the principal — RHAMP-REQ-054;
         raw_credential_id + cose_public_key read from the sidecar, cross-checked
         against the registry public_key — RHAMP-REQ-058)
  → construct Challenge (HPAC-REQ-049) + canonical RHAMP-CLIENT-CONTEXT/1.0 (§7)
  → client_data_hash = SHA-256(canonical client-data bytes)
  → CTAP2 authenticatorGetAssertion(client_data_hash, allow_list, rp_id="hpac.pcae.local")
        (human touches key; UV satisfied inside the authenticator)
  → assertion: authenticatorData ‖ signature
  → hpac_verifier._verify_assertion_material real branch (§37 / RHAMP-REQ-102):
       · credential lookup + principal ownership       (credential_principal_mismatch)
       · authenticatorData.rpIdHash == SHA-256("hpac.pcae.local")   (rp_id_hash_mismatch)
       · COSE signature over authenticatorData ‖ client_data_hash
             via CoseKey.parse(cbor.decode(public_key)).verify(...)  (signature_invalid)
       · client_data_hash equals recomputed canonical hash          (client_data_hash_mismatch)
       · ceremony_kind / context_identifier frozen constants        (client_data_context_mismatch)
       · FLAG.UP set  (user_presence_missing)  AND  FLAG.UV set  (user_verification_missing)
       · §20 signature-counter policy vs the §21 counter-state record (signature_counter_regression)
       · credential.status == active / principal.status == active
       · challenge active + unconsumed + challenge_digest recompute
       · mechanism_id resolves + >= PRINCIPAL_VERIFIED_INTENT
       · HPAC-REQ-054 step 5 presentation resolution + step 9 lifecycle/consumption
       · proof age <= 300s + authority-generation currentness
  → step 10: PROOF_VERIFIED_AND_BOUND lifecycle event + ephemeral AuthenticatedHumanPrincipal
  → immediately after step 10, before return: atomic RHAMP-COUNTER-STATE/1.0 update
        (last_accepted_meaningful, last_observed_raw, generation, updated_at — RHAMP-REQ-071)
```

**Registration-time parts:** `makeCredential`, credential-id/public-key
extraction, `CredentialRecord` + sidecar + counter-state create, enrollment
provenance. **Authentication-time parts:** `allowList` construction,
`getAssertion`, `rpIdHash` / signature / client-data / UP / UV / counter checks,
proof mint, counter-state update. `FLAG.UV` enforcement and the counter-state
**update** are authentication-time; the counter-state record **creation** is
registration-time.

## 7. RHAMP-REQ-156 atomicity — what "mechanism + registry + bootstrap" means (this phase's §7 — decisive)

RHAMP-REQ-156's `.1R.30` row and the §72 freeze verdict parenthetical
(`.1R.30` = "mechanism + registry + bootstrap") are read together. The `.1R.30`
scope list enumerates, in one phase:

1. production `HumanPrincipalRegistryStore` **writer path** (registry);
2. the §17 sidecar store **and** the §21 counter-state store (registry);
3. the protected-admin **enrollment + first-credential bootstrap** ceremony
   tool — §13, §14 (bootstrap);
4. `FIDO2HumanAuthenticator` for `hpac.fido2.uv_presence.v2` (mechanism —
   `getAssertion`);
5. real CTAP2 **assertion verification** in `hpac_verifier` (§37) including the
   `FLAG.UV` check (mechanism — verify);
6. `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}` (mechanism —
   registry identity);
7. `terminal_reason_code` wiring (mechanism);
8. reuse `hatp_fido2_provider` CTAP2 primitives as a shared library.

"Mechanism" in RHAMP-REQ-156 therefore means **interpretation C — the entire
RHAMP real authentication mechanism**: both the credential-**creation**
capability (`makeCredential`, inside item 3's ceremony tool) **and** the
authentication capability (`FIDO2HumanAuthenticator` + `getAssertion`
verification, items 4–5), plus the mechanism-registry identity (item 6). It is
**not** interpretation B ("only the credential-creation mechanism") — items 4
and 5 are explicitly in the same `.1R.30` row. It is **not** interpretation A
restricted to "both makeCredential and getAssertion implementation" only — the
row also names the stores and the ceremony tool. The `.1R.30` bundle is
`mechanism (creation + authentication + registry-identity) + registry (writer +
sidecar + counter-state) + bootstrap (first-credential ceremony)`, atomically.

The **only** content RHAMP-REQ-156 severs out of `.1R.30` is the **protected
approval presentation** and the **real approval-authority production path** —
those are `.1R.32` ("No protected approval UI. No real approval-authority
production path yet.", verbatim in the `.1R.30` row).

**Consequence for the operator split:** the operator Slice-2 (registry +
counter-state + enrollment) and Slice-3 (`FIDO2HumanAuthenticator` + CTAP2
verify) both fall **entirely inside** the single frozen `.1R.30` bundle. The
split is an *internal* subdivision of one contract phase along a seam the
contract does not recognise, and §4 shows the seam is not severable because
items 1–3 (registry + bootstrap) consume item 8-driven `makeCredential`
outputs.

## 8. Original `.1R.29` intent (this phase's §8)

The `.1R.29` freeze report is unambiguous that the decomposition is **frozen
normative text**, not merely a recommended sequence:

- `.1R.29` §25 (*"Implementation / IV sequence — FROZEN in RHAMP-001 §64"*)
  reproduces the four-phase table and states *"Phase ordering: N-16-5 → N-16-6
  → N-16-7 … Do not implement any of the above."*
- `.1R.29` §28 contract-freeze verdict: *"Implementation / IV sequence: FROZEN
  (.1R.30 → .1R.31 → .1R.32 → .1R.33)"*.
- `.1R.29` §29 recommended next phase names `.1R.30` with **exactly** the
  `.1R.30` scope list from RHAMP-REQ-156 — registry writer path + sidecar +
  counter-state + enrollment + first-credential bootstrap + `FIDO2HumanAuthenticator`
  + CTAP2 verification + `_ELIGIBLE_MECHANISM_IDS` widening, *"as one phase"*.

**Distinction:** the *phase-ID strings* (`.1R.30`, `.1R.31`, …) are explicitly
"recommended, NOT reserved" (RHAMP-REQ-156 header) — an organizational
convenience, freely renamed. The *scope grouping* ("mechanism + registry +
bootstrap" in one implementation phase; "protected presentation + real-assurance
wiring" in the next) **is** normative contract text (§64 table, §72 verdict,
listed as normative matrix (20) in RHAMP-REQ-165). The contract author
intentionally froze the bundle boundary, precisely because §13/§14/§17/§21 make
the sub-parts non-severable. This is confirmed by `.1R.29` §27's STOP-condition
check, which explicitly considered and rejected the possibility that
"credential registry / counter-state model requires PCAE to store private-key
material" and that "first-credential bootstrap authority root cannot be frozen
safely" — the freeze deliberately kept registry + bootstrap + ceremony
together.

## 9. Current split analysis (this phase's §9)

| Operator slice | Scope as drawn | Status under RHAMP-001 v1.0 |
|---|---|---|
| **Slice 1** (`.1R.30R.3.1`, CLOSED) | PAWA production protected-admin writer anchor + agent-exclusion resolver + one-operation capability + out-of-band provision/rotate/revoke tool. FIDO2-free. | **Legitimate and complete.** Governed by its own companion contract HPAC-PAWA-001 v1.1. Not a RHAMP credential slice — it is the *administrative-authority substrate* the RHAMP enrollment tool will consume. CLOSED, unchanged, not reopened. |
| **Slice 2** (`.1R.30R.3.3`, BLOCKED) | RHAMP credential registry + `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar + `RHAMP-COUNTER-STATE/1.0` + credential lifecycle/currentness + PAWA-bound protected-admin enrollment + first-credential bootstrap — **without** real FIDO2 mechanism. | **Impossible as scoped under v1.0.** Not "partially compatible" and not "salvageable by re-scoping into a RHAMP slice": every canonical artifact it must produce (`CredentialRecord.public_key`, sidecar `raw_credential_id`/`cose_public_key`, counter-state keyed by `credential_id`, enrollment evidence digests) is a function of `makeCredential` output (§4.1); the bootstrap + publish-point + real-transaction-evidence deliverables it was mandated to produce are inside RHAMP-REQ-048's `"all of"` conjunction (§4.1); and RHAMP-REQ-155 forbids the synthetic-material escape hatch (§4.5). |
| **Slice 3** (not begun) | `FIDO2HumanAuthenticator` + native CTAP2 `getAssertion` verification + real verifier branch + `_ELIGIBLE_MECHANISM_IDS` widening. | **Also inside the `.1R.30` bundle** (RHAMP-REQ-156 items 4–6). Cannot stand alone: a real verifier branch with no enrolled real credential to verify against has nothing to test end-to-end; RHAMP-REQ-103 requires the real branch be reachable only with a `PRODUCTION`-class `CredentialRecord` resolved — which only Slice 2's (impossible) output would provide. |

The split is therefore not a clean severance of one contract phase into two — it
is a bisection of a single non-severable contract phase.

## 10. Candidate A — RE-MERGE (this phase's §10, §11, §12)

### 10.1 Definition

Preserve RHAMP-001 v1.0 **byte-unchanged**. Fold the former Slice 2 + Slice 3
back into **one** implementation phase whose scope is exactly RHAMP-REQ-156's
`.1R.30` bundle **minus** the PAWA writer anchor already delivered by Slice 1:

- production `HumanPrincipalRegistryStore` **`enroll_credential` /
  `revoke_credential`** writer path (schema byte-unchanged — RHAMP-REQ-055);
- `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar store (§17) — closed schema, immutable,
  create-only, atomic, read-back verified, `(credential_id, record_digest)`
  resolution, symlink/traversal/owner/ACL/non-canonical/digest rejection;
- `RHAMP-COUNTER-STATE/1.0` store (§21) + the §22 counter-state update
  linearization (verify-with-counter-check → step-10 proof mint → atomic
  counter-state replace before the `AuthenticatedHumanPrincipal` is returned);
  atomic-replace or BLOCK (RHAMP-REQ-073);
- the protected-admin **enrollment + first-credential bootstrap** ceremony tool
  (§13, §14, §61) — consuming the Slice-1 PAWA `production_writer()` handle and
  the HPAC-REQ-023 external deployment-owner anchor; local-interactive-only
  (§53); `bootstrap_authority_unproven` / BLOCK if the anchor cannot be
  established (RHAMP-REQ-049);
- native CTAP2 `authenticatorMakeCredential` (enrollment) via reused
  `hatp_fido2_provider` primitives as a shared library (§38) — rp.id
  `"hpac.pcae.local"`, ES256, UP+UV, non-discoverable, attestation "none";
- `FIDO2HumanAuthenticator` for `hpac.fido2.uv_presence.v2` (native CTAP2
  `authenticatorGetAssertion`, `allowList`-bound, USB-HID / NFC);
- the real CTAP2 assertion-verification branch in
  `hpac_verifier._verify_assertion_material` (§37 / RHAMP-REQ-102) — COSE
  verify via the pinned library (no custom crypto), `rpIdHash` recompute,
  canonical `client_data_hash` recompute, **the added `FLAG.UV` check**
  (finding N-16-5-3), the §20 counter check, ordering per RHAMP-REQ-103 (no
  shortcut on earlier failure);
- `_ELIGIBLE_MECHANISM_IDS += {"hpac.fido2.uv_presence.v2"}` — `frozenset`
  literal, explicit `.1R.30R.3.4` / RHAMP-001 §4/§40 citation, no wildcard, no
  `fido2.*`, no `fnmatch` (RHAMP-REQ-011 / -109);
- `terminal_reason_code` wiring for the enrollment / bootstrap / authentication
  / counter / protected-root subset of the closed 41-code table (§49);
- the deterministic virtual / synthetic authenticator **NON_REAL** test fixture
  + the ≥ 55-case negative matrix (RHAMP-REQ-154) — structurally NON_REAL,
  never REAL authority in a production registry (RHAMP-REQ-155), never
  upgradeable (RHAMP-REQ-111).

**Explicitly NOT in scope** (stays `.1R.32`-equivalent / later, unchanged by
Decision A): the process-isolated protected presentation helper; the
deterministic `renderer_profile`; helper integrity / provenance (§30); explicit
Approve/Reject election UI; real `mechanism_attestation`; `verifier_kind =
pcae-protected-local-presentation/1.0` acceptance in `approval_presentation.py`;
`require_real_assurance = True` wiring through Gate 5 / Gate 9; a
`PRODUCTION`-class `AuthenticatedHumanPrincipal` obtainable on a production
path; any hardware access (that is the `.1R.33`-equivalent controlled session);
N-16-6; N-16-7; Slice C; the first external effect; execution enablement.

### 10.2 Evaluation

| Axis | Assessment |
|---|---|
| **v1.0 contract fidelity** | Perfect — Candidate A *is* RHAMP-REQ-156's `.1R.30` bundle. Zero contract text change; `git diff --name-only A HEAD -- docs/contracts` stays empty (this phase) and the implementing phase changes only `src/pcae` + `tests`, never `docs/contracts` (RHAMP-REQ-003 obligation for `.1R.30`). |
| **Implementation complexity** | High but bounded and already scoped by RHAMP-001 §13–§22, §37, §49. One phase, one diff, one reviewer mental model. |
| **Atomicity** | Native — the multi-artifact enrollment transaction (`CredentialRecord` + sidecar + counter-state + provenance) is created and read-back-verified in one place, as RHAMP-REQ-048 requires. No cross-phase partial state. |
| **Bootstrap circularity** | Resolved by RHAMP-REQ-047 — the HPAC-REQ-023 external deployment-owner protected administration principal is the trust anchor; it terminates bootstrap without circular PCAE self-authorization, and Slice 1 already delivered the `production_writer()` entry point that consumes it. No real authenticated human need pre-exist (RHAMP-REQ-048 / PAWA-INV-4). |
| **PAWA interaction** | Clean — exactly one one-operation `ProductionWriterHandle` per enrollment transaction (§14 below); the handle scopes the registry write + sidecar create + counter-state create + provenance append as one bounded operation. No second admin model. |
| **Testability** | RHAMP-REQ-154 deterministic NON_REAL fixture covers the automated suite; the ≥ 55-case matrix is exercised once, against the merged mechanism, in one IV. |
| **Real-hardware requirement** | Deferred to the `.1R.33`-equivalent controlled session (RHAMP-REQ-152/153) — the merged implementation phase and its IV run entirely on the deterministic fixture (§17 below). |
| **Risk** | Lowest of the three — no new normative surface, no new lifecycle state, no migration, no pseudo-authoritative intermediate. |
| **Future maintainability** | Best — one mechanism module set, one IV baseline; the store layer is never IV'd twice. |
| **IV burden** | One IV (`.1R.30R.3.5`) covering the whole merged mechanism — the `.1R.28` §31 / RHAMP-REQ-156 `.1R.31` requirements, broad fixed-SHA A/B. |
| **Compatibility with `.1R.32`-equivalent presentation phase** | Unchanged — Decision A does not touch `approval_presentation.py`, the `verifier_kind` set, `require_real_assurance`, or Gate 5 / Gate 9. The presentation phase consumes the merged mechanism's verified real authentication evidence exactly as RHAMP-REQ-156 anticipated. |
| **Compatibility with a `.1R.30R.4` composite IV** | A separate "composite IV" is **not required** under Decision A — merging the slices means `.1R.30R.3.5` already verifies the mechanism as one unit; the next IV concern is the `.1R.32`-equivalent presentation + N-16-5 closure IV. |

### 10.3 Candidate A exact content mapping (this phase's §11)

Every item below is mapped to its RHAMP-001 requirement; the list is **not**
assumed — it is RHAMP-REQ-156's `.1R.30` row cross-checked against §13–§49:

| Component | Belongs in the merged phase? | RHAMP-001 anchor |
|---|---|---|
| `RHAMP-FIDO2-CREDENTIAL/1.0` store | **yes** | §17 RHAMP-REQ-055..058 |
| `RHAMP-COUNTER-STATE/1.0` store | **yes** | §21 RHAMP-REQ-068..070 |
| protected-admin enrollment tool | **yes** | §13 RHAMP-REQ-043, §61 RHAMP-REQ-150 |
| CTAP2 `authenticatorMakeCredential` | **yes** | §13 RHAMP-REQ-043 |
| first-credential bootstrap | **yes** | §14 RHAMP-REQ-047..050 |
| credential lifecycle / currentness | **yes** (reuse existing `credential_generation`) | §44 RHAMP-REQ-118..120 |
| `FIDO2HumanAuthenticator` | **yes** | §64 RHAMP-REQ-156 row `.1R.30` |
| CTAP2 `authenticatorGetAssertion` | **yes** | §9 RHAMP-REQ-030, §37 |
| `rpIdHash` validation | **yes** | §6 RHAMP-REQ-018, §37 step 2 |
| `FLAG.UP` validation | **yes** | §10 RHAMP-REQ-034, §37 step 5 |
| `FLAG.UV` validation | **yes** (the check HATP omits — N-16-5-3) | §10 RHAMP-REQ-034, §38 |
| COSE signature verification | **yes** (library `CoseKey.verify`, no custom crypto) | §37 RHAMP-REQ-102 step 3, §39 RHAMP-REQ-107 |
| counter evaluation / update | **yes** | §20–§22 RHAMP-REQ-065..072 |
| `hpac_verifier` REAL branch | **yes** | §37 RHAMP-REQ-102/103 |
| `_ELIGIBLE_MECHANISM_IDS` addition | **yes** | §4 RHAMP-REQ-011, §40 RHAMP-REQ-109 |
| protected presentation helper | **no — later phase** | §64 RHAMP-REQ-156 row `.1R.32` |
| `renderer_profile` / `mechanism_attestation` | **no — later phase** | §64 row `.1R.32` |
| `verifier_kind` widening in `approval_presentation.py` | **no — later phase** | §40 RHAMP-REQ-110 (`.1R.32`) |
| `require_real_assurance` through Gate 5 / Gate 9 | **no — later phase** | §64 row `.1R.32` |
| a `PRODUCTION` `AuthenticatedHumanPrincipal` production path | **no — later phase** | §64 row `.1R.32` |
| real-CTAP2-hardware verification | **no — `.1R.33`-equivalent closure IV** | §62 RHAMP-REQ-152/153 |

### 10.4 Candidate A phase shape (this phase's §12)

**Not** a restoration of historical `.1R.30` (which remains BLOCKED and
immutable). A **fresh** successor `.1R.30R.3.4` (see §21) using a new ID.

The contract permits **one implementation phase + one IV**. RHAMP-REQ-156's
`.1R.30` is a single phase; RHAMP-REQ-156 does not authorize internal atomic
sub-phases, and §4 shows the sub-parts are non-severable, so the merged phase
SHALL NOT itself be re-sliced. One coherent diff, independently verified once.

## 11. Candidate B — RHAMP-001 v1.1 STAGED ENROLLMENT (this phase's §13–§19)

### 11.1 Definition (conceptual only — no contract text written)

Evolve RHAMP-001 v1.0 → v1.1 with an explicit staged / material-deferred
enrollment: a lifecycle state such as `PENDING_MATERIAL` (never eligible for
`allowList` construction or authority resolution), a two-step publish where the
material-free half (schemas, readers, writers, path hardening, counter-state
primitives, PAWA authorization, revocation, lifecycle) lands first and the CTAP2
ceremony + first ACTIVE publish lands second.

### 11.2 Required new normative semantics (this phase's §14)

For a staged model to be coherent, RHAMP-001 v1.1 would have to add **all** of:

- a **new credential-lifecycle state** (`PENDING_MATERIAL` or equivalent) —
  either on `CredentialRecord.status` (which is `{active, revoked}` monotonic —
  RHAMP-REQ-055 / HPAC-REQ-062) **or** in a new "pending enrollment" artifact;
- a **new sidecar lifecycle** — the `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar is
  currently a closed, create-only, immutable schema over authenticator output
  (RHAMP-REQ-056/057); a staged model needs either a sidecar variant with
  nullable `raw_credential_id` / `cose_public_key` or a deferred-sidecar-create
  rule;
- **new currentness behaviour** — `credential_generation` (HPAC-REQ-098a) folds
  the whole `CredentialRecord`; a `PENDING_MATERIAL` record's generation
  semantics and its transition to ACTIVE would need defining;
- **new failure reasons** — at minimum a `staged_enrollment_material_absent` /
  `staged_enrollment_superseded` / `staged_enrollment_expired` family, changing
  the frozen 41-code vocabulary (§11.4);
- **new bootstrap semantics** — RHAMP-REQ-048's `"all of"` conjunction
  (which includes "verification of the `makeCredential` response" **and** "an
  atomic create of the first `CredentialRecord` + sidecar + counter-state")
  would have to be re-written as a two-stage sequence;
- possibly a **new PAWA operation** — the material-free stage and the ceremony
  stage would each need their own bounded `ProductionWriterHandle`, or a
  multi-step handle, contradicting the one-operation model;
- a **staged transaction identifier** that durably survives between stages;
- **recovery semantics** for a stage-1 record whose stage-2 ceremony never
  completes (orphan cleanup, TTL, protected-admin GC).

**What actually exists durably in stage 1?** If the staged state carries no
real `credential_id` derivable from authenticator output, no COSE public key,
and no raw credential id, then the only durable object is an **enrollment-intent
record** — a principal reference plus an operation id plus a timestamp. The
counter-state record cannot exist (it is keyed by `credential_id`). The sidecar
cannot exist (closed schema over authenticator output). So stage 1 delivers an
intent record plus the *code* for artifact writers that cannot yet be validly
exercised against canonical data — which is **Candidate C plus a throwaway
intent object** (§12).

### 11.3 Authority-safety analysis (this phase's §15)

A staged model **could** in principle keep `PENDING_MATERIAL` strictly
non-authoritative, if RHAMP-001 v1.1 froze:

```
PENDING  !=  registered credential
         !=  active allowList credential
         !=  human authentication authority
```

and every future consumer (`allowList` construction, `_authority_class_of`,
`is_verifier_authenticated_principal`, Gate 5 / Gate 9) treated it as absent.
**But** the moment `PENDING_MATERIAL` transitions to ACTIVE without a fresh
`makeCredential`, that transition is an **upgrade path for a materially-incomplete
object** — and RHAMP-REQ-167 lists *"making a NON_REAL object upgradeable"* as a
**MAJOR** trigger, and §41 (RHAMP-REQ-111) restates non-upgradeability as a
binding rule. If instead the ACTIVE transition still requires `makeCredential`
first (material only lands at stage 2, before ACTIVE), then the staging bought
nothing — the ceremony and the ACTIVE publish are still atomic, exactly as
Candidate A / the current contract already have them.

### 11.4 Versioning trigger analysis (this phase's §16) — trigger by trigger

Applying **RHAMP-REQ-167 (MAJOR)** and **RHAMP-REQ-168 (MINOR)** verbatim:

| RHAMP-REQ-167 MAJOR trigger | Fires for Candidate B? |
|---|---|
| introducing a browser / WebAuthn web-origin ceremony | no |
| introducing remote or headless approval or any network authority transport | no |
| permitting discoverable / resident credentials or a usernameless flow | no |
| relaxing the UP or UV requirement | no |
| **changing the approval-intent election ceremony or its ordering** | **the *approval* election ceremony (§12/§34) is untouched; but §13's RHAMP-REQ-043 registration flow is a frozen ordered sequence and staging re-orders it — RHAMP-REQ-165 item (4) "registration / bootstrap lifecycle" is a normative matrix. This is at least a borderline MAJOR trigger and at minimum a normative-matrix change.** |
| **changing the first-credential bootstrap authority model** | RHAMP-REQ-048's bootstrap ceremony is a frozen `"all of"` conjunction; splitting it into two stages changes the *ceremony model* even if the *authority anchor* (HPAC-REQ-023) is unchanged. **Borderline MAJOR.** |
| making attestation or a device-identity claim authoritative | no |
| adding a transport outside `{USB-HID, NFC}` | no |
| **making a NON_REAL object upgradeable** | **if `PENDING_MATERIAL` → ACTIVE happens without a fresh `makeCredential`, YES — MAJOR (§11.3). If it does not, staging is pointless.** |

| RHAMP-REQ-168 MINOR permission | Covers Candidate B? |
|---|---|
| re-state verified behaviour | no — B adds new behaviour |
| add an additional supported authenticator model within the frozen profile | no |
| tighten (never loosen) a TTL bound | no |
| **add a `terminal_reason_code` for a newly-identified terminal path without removing or re-meaning an existing one** | a staged model adds new codes — *permitted as MINOR* **only** if it does not re-mean `enrollment_ceremony_evidence_invalid` (row 3, whose trigger is "makeCredential evidence fails verification"). A two-stage enrollment re-means row 3's stage. **Marginal.** |
| clarify a test-fixture rule | no |

Additionally: any change to `CredentialRecord` (adding a `PENDING_MATERIAL`
status value) touches **HPAC-001 v2.1**'s HPAC-REQ-013 / HPAC-REQ-062 — which
RHAMP-REQ-055 forbids ("`CredentialRecord` is **byte-unchanged** by
RHAMP-001") — forcing an **HPAC-001 version bump**, which `.1R.29` §23
explicitly identified as a cascade the entire companion-contract architecture
exists to avoid (RIHAC-001 §12 condition 7 names "HPAC-001 v2.1" literally).

**Versioning verdict for Candidate B:** **not a clean MINOR.** It is, at
minimum, a MINOR that changes a normative matrix (§64 decomposition + §13
registration lifecycle) and the 41-code vocabulary; realistically a **MAJOR**
(RHAMP-REQ-167 "changing … its ordering" / "making a NON_REAL object
upgradeable") **plus** an HPAC-001 v2.1 cascade if `PENDING_MATERIAL` lands on
`CredentialRecord`. Every path requires explicit human authorization + a
dedicated contract-freeze phase + a dedicated contract IV before any
implementation.

### 11.5 Failure-vocabulary impact (this phase's §17)

A staged enrollment needs new `terminal_reason_code` values (stage-1 orphan,
stage-2 supersession, stage-1 material-absent-at-stage-2). RHAMP-REQ-129 freezes
the vocabulary at **exactly 41**; RHAMP-REQ-168 permits *adding* a code as a
MINOR only if no existing code is removed or re-meaned. A staged model
re-means the *stage* at which `enrollment_ceremony_evidence_invalid` (#3) and
`bootstrap_authority_unproven` (#1) apply. Marginal-to-non-compliant as a MINOR.

### 11.6 Migration / schema impact (this phase's §18)

There are **no** existing v1.0 installations or artifacts — RHAMP-001 v1.0 has
**never been implemented** (the historical `.1R.30` is BLOCKED; Slices 1–3 have
produced no RHAMP credential artifact). So Candidate B has **no backward-data
migration burden**. However, if `PENDING_MATERIAL` lands on `CredentialRecord`,
the *schema* change is architecturally expensive: `CredentialRecord` is
consumed by `hpac_verifier`, `allowList` construction, `_authority_class_of`,
`credential_generation` (HPAC-REQ-098a), and every IV suite from `.1R.3`
onward — a byte change there is exactly what the companion-contract pattern was
built to prevent (`.1R.29` §23). Keeping `PENDING` off `CredentialRecord` (in a
separate artifact) avoids the schema cost but then stage 1 has no credential
object at all (§11.2).

### 11.7 Benefit test (this phase's §19)

Candidate B is required to demonstrate a **concrete** benefit:

| Claimed benefit | Holds? |
|---|---|
| smaller independently verifiable implementation slices | **No** — the store writer still processes real authenticator material at stage 2 and must be IV'd there; stage-1 IV of the same writer against an intent record adds an IV pass, not isolation. |
| safer multi-artifact transaction preparation | **No** — RHAMP-REQ-048 already mandates an *atomic* multi-artifact create; splitting it into two durable stages makes the transaction **less** atomic and adds orphan-recovery surface. |
| reduced hardware dependency during store implementation | **No** — RHAMP-REQ-154's deterministic NON_REAL fixture already removes hardware from the automated suite, and it is usable inside **Candidate A** with no contract change. |
| clearer administrative vs authentication separation | **No** — RHAMP-REQ-037 / §11 / §46 already wall authentication ≠ approval, and Slice 1 already separated administrative-authority issuance from the mechanism. |

Per this phase's §19: *"Reject B if its main benefit is merely making the
previous phase numbering convenient."* That is exactly what remains after the
table above — B's only residual "benefit" is that it would let the old
`.3.3 = Slice 2` / `.3.5 = Slice 3` numbering survive. **Rejected.**

## 12. Candidate C — MATERIAL-FREE SLICE-2 RE-SCOPE (this phase's §20–§22)

### 12.1 Definition

Keep RHAMP-001 v1.0 unchanged. Re-scope Slice 2 to **only**: schemas; store
code; path / provenance validation; `RHAMP-COUNTER-STATE` transition /
concurrency primitives; PAWA authority plumbing; revocation / lifecycle;
structurally-NON_REAL fixtures — with **no** first-credential bootstrap, **no**
ACTIVE publish, **no** enrollment evidence of a real ceremony. Move
`makeCredential` + real enrollment + first-credential bootstrap + ACTIVE
publish to Slice 3.

### 12.2 Contract compatibility (this phase's §21) — the decisive question

*Can any Slice-2 artifact under C be called canonical RHAMP credential
registration state before `makeCredential`?*

**No.** Per §4.1: `CredentialRecord.public_key`, the sidecar's
`raw_credential_id` / `cose_public_key`, and the counter-state record's
`credential_id` key are all functions of `makeCredential` output. Any
`RHAMP-FIDO2-CREDENTIAL/1.0` object produced without a ceremony is either
schema-invalid (nullable fields the closed schema forbids — RHAMP-REQ-056) or
populated with fixture material (structurally NON_REAL — RHAMP-REQ-154/155,
never canonical). So under C, Slice 2 is **pre-implementation scaffolding, not a
RHAMP credential-registration slice**. Per this phase's §43, a Candidate-C phase
**must not** be titled "protected-admin enrollment implementation"; canonical
ACTIVE credential creation would remain wholly in the following real FIDO2
phase.

### 12.3 Value (this phase's §22)

| Concern | Assessment |
|---|---|
| Does C materially improve safety/testability enough to justify an extra scaffolding phase + an extra IV? | **No.** The store code (serializers, readers, atomic writers, path hardening, digest binding, `RHAMP-COUNTER-STATE` transition primitives, PAWA one-operation scoping, revocation monotonicity) is **byte-identical** whether real or fixture material flows through it. Its security-critical properties (crash-atomicity, symlink/traversal rejection, digest binding, one-operation capability scoping) first *matter for real authority* in Slice 3 — where they must be re-verified anyway. C's IV of the store against fixtures is not an isolation dividend; it is a duplicated IV pass. |
| Does C create production code for authority artifacts before the contract allows those artifacts to become canonical? | **Yes** — mild scope-ordering irregularity. RHAMP-REQ-156 bundles the writers with the ceremony; C ships the writers a phase early. Tolerable but not free. |
| Is C's one genuine benefit — developing / reviewing the store layer without the CTAP2 ceremony in the diff — available elsewhere? | **Yes, inside Candidate A.** A's implementing phase can (and per RHAMP-REQ-154 must) build the deterministic NON_REAL authenticator fixture and exercise the full store layer through it, within one diff, with no phase boundary. A reviewer reads the store layer as a coherent sub-section of A's diff. |

Per this phase's §22: *"it may create production code for authority artifacts
before the contract allows those artifacts to become canonical. If so, prefer
A."* That condition is met. **Rejected.**

## 13. Candidate comparison table (this phase's §23)

| Criterion | A — Re-merge | B — RHAMP v1.1 staged | C — material-free scaffolding |
|---|---|---|---|
| v1.0 contract fidelity | **perfect** (is RHAMP-REQ-156) | broken (needs v1.1) | preserved (no text change) |
| normative change | **none** | MINOR-changing-a-matrix at best; realistically MAJOR + HPAC-001 cascade | none |
| implementation complexity | high, bounded, one diff | highest (contract + impl + 2 IVs + migration analysis) | medium store phase + full mechanism phase |
| trust-model complexity | unchanged | **+1 lifecycle state, +PAWA multi-op, +orphan recovery** | unchanged |
| new lifecycle states | 0 | ≥ 1 (`PENDING_MATERIAL`) | 0 |
| migration cost | none | none (no v1.0 installs) but heavy `CredentialRecord` schema cost if `PENDING` lands there | none |
| testing value | full mechanism, one ≥55-case matrix, one IV | store IV'd twice | store IV'd twice |
| hardware coupling | **none in impl+IV** (NON_REAL fixture); real HW only at closure IV | same | same |
| bootstrap coherence | **native atomic** (RHAMP-REQ-048 `"all of"`) | **degraded** (two durable stages, orphan surface) | deferred to Slice 3 |
| atomicity | **native** | reduced | deferred |
| failure semantics | 41-code table wired once, unchanged | needs new codes; re-means #1/#3 stage | 41-code table wired across two phases |
| future maintenance | **best** (one module set, one baseline) | worst (contract + code co-evolution) | medium (two IV baselines for one store) |
| independent-verification clarity | **one IV, whole mechanism** | contract IV + 2 impl IVs | 2 impl IVs, overlapping surface |
| risk of pseudo-authoritative state | **none** | **present** (`PENDING_MATERIAL`) | low (scaffolding could be mislabeled) |
| effect on N-16-5 schedule | shortest — 1 impl + 1 IV before the presentation phase | longest — contract freeze + contract IV + 2× (impl + IV) | +1 phase + 1 IV vs A |

## 14. PAWA interaction, per candidate (this phase's §25)

PAWA (HPAC-PAWA-001 v1.1) remains the **sole** protected-admin authority. No
second admin model in any candidate.

| | PAWA writer authority → what enrollment operation? | one-operation capabilities | transaction scope | multi-artifact coherence |
|---|---|---|---|---|
| **A** | one `production_writer()` handle per enrollment / bootstrap ceremony → issues **one** `ProductionWriterHandle` scoping the atomic `CredentialRecord` write + sidecar create + counter-state create + provenance append as **one bounded operation** | **1** per enrollment | the whole multi-artifact enrollment transaction | native — single atomic create, read-back verified (RHAMP-REQ-048) |
| **B** | the material-free stage and the ceremony stage each need a handle → **2** one-operation handles, or a multi-step handle that violates the one-operation model | 2 (or a contradiction) | split across two durable stages | degraded — orphan / supersession surface between stages |
| **C** | store-phase handle issues writes against fixtures only (not canonical authority); real-enrollment handle in Slice 3 does the canonical create | 1 (fixture) + 1 (real, Slice 3) | store phase: non-canonical; Slice 3: canonical | canonical coherence entirely in Slice 3 |

Candidate A is the only one where "one enrollment = one PAWA one-operation
capability = one atomic multi-artifact transaction" holds cleanly, matching both
HPAC-PAWA-001 §49 (one-operation) and RHAMP-REQ-048 (atomic create).

## 15. First-credential bootstrap model (this phase's §26, §27)

Frozen for the successor implementation, per RHAMP-REQ-047..050 / §14:

- **Anchor:** HPAC-REQ-023's **external deployment-owner protected
  administration principal** — owns the deployment-scoped protected root
  outside every repository, unavailable to ordinary same-user agent execution
  (HPAC-REQ-022). Slice 1 already delivered the `production_writer()` /
  `hpac_protected_root_admin.py` entry point that establishes and consumes this
  anchor. **No** real authenticated human need pre-exist to enroll the first
  real credential (RHAMP-REQ-048; PAWA-INV-4) — the anchor terminates bootstrap
  without circular PCAE self-authorization.
- **Ceremony (RHAMP-REQ-048, "all of"):** local interactive mode (§53); an
  already-canonical `PrincipalRecord` selected by the protected admin; explicit
  protected-administrative confirmation; a protected presentation of the exact
  principal + credential being enrolled; authenticator UP + UV; verification of
  the `makeCredential` response; **atomic** create of the first
  `CredentialRecord` + sidecar + counter-state + durable provenance entry.
- **Fail-closed:** a ceremony that cannot establish the HPAC-REQ-023 anchor →
  `bootstrap_authority_unproven`; the implementing phase **STOPS (BLOCKED)** if
  the existing governance model provides no such anchor (RHAMP-REQ-049). Slice
  1 having shipped the PAWA anchor, this BLOCK is **not** expected to fire.
- **Recovery:** total principal loss → **repeat the bootstrap ceremony**
  (RHAMP-REQ-050); no principal-recovery shortcut, no fallback to a NON_REAL
  mechanism.

### Registration ≠ authentication ≠ approval (this phase's §27)

Frozen and carried, no candidate collapses these:

```
makeCredential success        !=  a runtime authenticated principal
FLAG.UV during enrollment      !=  approval intent
a hardware touch               !=  approval
an AuthenticatedHumanPrincipal !=  approval authority
```

The enrollment ceremony **may** include UP/UV, but authentication authority for
later operations still requires a fresh `getAssertion` verification (§37) and
the full HPAC proof lifecycle; **approval** additionally requires the protected
presentation (§28–§34, a later phase) and the explicit observed `approve`
election. RHAMP-REQ-037 / RHAMP-INV-002.

## 16. Counter-state timing (this phase's §28) — FROZEN

Per RHAMP-REQ-069: the `RHAMP-COUNTER-STATE/1.0` record is **created at
enrollment** (inside the §13 flow, immediately after `enroll_credential`), with
`last_accepted_meaningful = 0`, `last_observed_raw = 0`, `generation = 0`,
`review_flag = false`. It is **not** created lazily after the first
`getAssertion`, and a missing / corrupt record for an `active` credential is a
**fail-closed** condition (`protected_root_invalid`), never silently treated as
"counter 0" (RHAMP-REQ-069). It is **updated** (atomic replace) immediately
after verifier step 10 succeeds and before the `AuthenticatedHumanPrincipal` is
returned (RHAMP-REQ-071).

## 17. Canonical credential publish point (this phase's §29) — FROZEN

Under RHAMP-001 v1.0 the canonical ACTIVE credential exists at the point
`HumanPrincipalRegistryStore.enroll_credential(...)` completes its atomic,
read-back-verified write of the `CredentialRecord` with `status = active` —
which per RHAMP-REQ-043 is **after** `makeCredential` verification and **within**
the same ceremony that then creates the sidecar and counter-state. There is
**no** earlier "provisional" publish point and **no** `PENDING` state. This is
precisely why a staged model (Candidate B) would have to *introduce* a new
publish point — and why Candidate A, which keeps the single frozen publish
point, needs no contract change.

## 18. Multi-artifact atomicity + hardware-requirement timing + HATP reuse (this phase's §30, §31, §32)

### 18.1 Multi-artifact atomicity (this phase's §30)

RHAMP-001 v1.0 **does** freeze a transaction/publish model: RHAMP-REQ-048
("an atomic create of the first `CredentialRecord` + sidecar + counter-state +
durable provenance entry"), RHAMP-REQ-043 ("[atomic, read-back verified]"),
RHAMP-REQ-057 (sidecar "atomically written, read-back verified"), RHAMP-REQ-069
(counter-state "atomic replace … read-back verify"), RHAMP-REQ-073 (non-atomic
store → BLOCK). The implementing phase's obligation (no contract change): the
`CredentialRecord` + sidecar + counter-state + provenance for one enrollment are
created as one transaction that either fully commits (all four read-back
verified) or leaves no canonical partial state; a crash mid-transaction leaves
the credential resolvable as **absent**, not half-enrolled. The partial-state
matrix (record without sidecar, sidecar without counter-state, etc.) each
resolves fail-closed (`protected_root_invalid`).

### 18.2 Hardware-requirement timing (this phase's §31) — FROZEN

- **Implementation + its IV** (`.1R.30R.3.4`, `.1R.30R.3.5`): run **entirely on
  the deterministic virtual / synthetic authenticator fixture** (RHAMP-REQ-154
  — monkeypatched `CtapHidDevice.list_devices` / `Ctap2` + an in-memory
  test-only ES256 key, the `hatp_fido2_provider.py` pattern) plus real
  WebAuthn/CTAP2 protocol test vectors and cryptographic negative cases. **No
  physical hardware is required for development or CI.**
- **Mandatory real-CTAP2-hardware verification** (RHAMP-REQ-152): performed
  **once**, before N-16-5 closes, in the `.1R.33`-equivalent controlled session
  (the `.1R.30R.5` closure IV — §21). It is **not** a per-test requirement
  (RHAMP-REQ-154) and **not** a substitute for the automated suite
  (RHAMP-REQ-155) — both are required for N-16-5 closure.

### 18.3 HATP FIDO2 provider reuse boundary (this phase's §32)

`hatp_fido2_provider.py` is read **only** to inventory reusable authority-neutral
CTAP2 primitives (HPAC-REQ-019 / §38). HATP state is **never** made
authoritative; the HATP registry / `SignerRecord` semantics and the
`_HATP_RP_ID` / `_HATP_ORIGIN` constants are **not** reused (separate trust
domain, HPAC-REQ-084).

| `hatp_fido2_provider` capability | RHAMP-001 reuse under Decision A |
|---|---|
| CTAP2 device enumeration (`CtapHidDevice.list_devices`) | **reusable** — transport primitive |
| `authenticatorMakeCredential` / `authenticatorGetAssertion` over `fido2.ctap2` | **reusable** — protocol primitives |
| `CoseKey` parse + `verify` | **reusable** — the signature primitive (no custom crypto — RHAMP-REQ-107) |
| `CollectedClientData` construction | **reusable as a wire-shape helper only** — RHAMP-001 supplies its own canonical `client_data_hash` (§7); `_HATP_RP_ID` / `_HATP_ORIGIN` **not** reused |
| `allow_list` construction | **reusable** — pattern |
| cancellation / timeout handling | **reusable** — pattern |
| UP-only presence check (`is_user_present()`, no UV) | **NOT reusable as-is** — RHAMP-001 adds its own `FLAG.UV` enforcement (§10, finding N-16-5-3) |
| `_HATP_RP_ID` / `_HATP_ORIGIN` / HATP registry / `SignerRecord` | **NOT reusable** — separate trust domain |

RHAMP-REQ-105: the shared CTAP2 transport / COSE-verify primitives SHOULD be
extracted into a shared library module **only if the extraction is needed**;
blind code copying is discouraged.

## 19. Frozen constants carried unchanged (this phase's §33, §34, §35, §36, §37)

| Concern | Frozen value (no candidate changes it) | Anchor |
|---|---|---|
| Real mechanism ID (§33) | `hpac.fido2.uv_presence.v2` — one entry, no wildcard | RHAMP-REQ-011 / RHAMP-INV-001 |
| RP identifier / client context (§34) | `rp_id = "hpac.pcae.local"` (compiled-in constant, not a web origin); `RHAMP-CLIENT-CONTEXT/1.0`; native CTAP2 only — no browser origin, no TLS, no loopback, no WebAuthn client | §6, §7, §8, §56 / RHAMP-INV-004/015 |
| Authenticator profile (§35) | roaming hardware key; USB-HID / NFC; UP mandatory; UV mandatory; non-discoverable `allowList`-bound credential; attestation non-authoritative; no device-uniqueness claim | §9, §10, §19, §52 / RHAMP-INV-003/007 |
| Protected presentation boundary (§36) | remains the later `.1R.32`-equivalent phase (`.1R.30R.4` — §21); registration / authentication `!=` informed approval presentation; not merged into the mechanism phase | §64 RHAMP-REQ-156 / RHAMP-INV-002 |
| Gate 5 / Gate 9 boundary (§37) | the merged mechanism phase produces verified real *authentication* evidence; `require_real_assurance` wiring through Gate 5 / Gate 9 and a `PRODUCTION` `AuthenticatedHumanPrincipal` production path remain the later phase; Gate 5 / Gate 9 byte-unchanged by the mechanism phase | §64 row `.1R.32`; RDGO-001 v3.1 (unchanged) |

`hpac_verifier.py` is byte-unchanged by **this** adjudication phase;
`_ELIGIBLE_MECHANISM_IDS` remains `frozenset({"hpac.deterministic.test-only.v1"})`;
Gate 5 / Gate 9 byte-unchanged; RHAMP-001 v1.0, HPAC-PAWA-001 v1.1, HPAC-001
v2.1 byte-unchanged (§22 fences below).

## 20. Corrected remaining N-16-5 closure path (this phase's §38, §44)

After Decision A, the remaining N-16-5 closure requirements are:

| Step | Phase (recommended IDs; NOT reserved; each its own explicit human authorization + IV) | Scope | Contract anchor |
|---|---|---|---|
| ✅ done | `.1R.30R.3.1` → `.3.2` → `.3.2.1` → `.3.2.1.1` | **Slice 1 CLOSED** — PAWA production protected-admin writer anchor (HPAC-PAWA-001 v1.1). | `.1R.30R` adjudication; HPAC-PAWA-001 |
| ✅ done | `.1R.30R.3.3` (BLOCKED, immutable) → **`.1R.30R.3.3R` (this phase)** | decomposition blocker recorded → **adjudicated: Decision A**. | RHAMP-REQ-156 |
| **next** | **`.1R.30R.3.4`** — N-16-5 RHAMP Real FIDO2 Credential Registration, Counter-State, Bootstrap & Authentication Mechanism Implementation (merged; formerly split Slice 2 + Slice 3) | the Candidate-A scope of §10.1 — RHAMP-REQ-156's `.1R.30` bundle minus the CLOSED PAWA anchor. **No protected UI, no `require_real_assurance`, no `PRODUCTION` `AuthenticatedHumanPrincipal` path, no hardware, no N-16-6/7, no Slice C.** | RHAMP-REQ-156 `.1R.30` row; §13–§22, §37–§49 |
| then | **`.1R.30R.3.5`** — Independent Verification of `.1R.30R.3.4` | the RHAMP-REQ-156 `.1R.31` requirements; the `.1R.28` §31 IV set; broad fixed-SHA A/B; the ≥ 55-case negative matrix re-derived; RHAMP-REQ-164 contract→production equivalence for every mechanism/registry/bootstrap requirement. | RHAMP-REQ-156 `.1R.31` row |
| then | **`.1R.30R.4`** — Protected Human-Approval Presentation + Real Approval-Proof Integration + `require_real_assurance` wiring | the RHAMP-REQ-156 `.1R.32` bundle: process-isolated helper; `renderer_profile`; helper integrity/provenance (§30); explicit Approve/Reject; presentation-digest binding; real `mechanism_attestation`; `verifier_kind = pcae-protected-local-presentation/1.0`; wire `require_real_assurance = True` through Gate 5 / Gate 9; a `PRODUCTION` `AuthenticatedHumanPrincipal` becomes obtainable for exactly one bound approval. **Still no N-16-6/7, no Slice C.** | RHAMP-REQ-156 `.1R.32` row |
| then | **`.1R.30R.5`** — Independent Verification of `.1R.30R.4` + mandatory real-CTAP2-hardware verification (RHAMP-REQ-152) + **N-16-5 closure** | the RHAMP-REQ-156 `.1R.33` bundle incl. the ≥ 1 real hardware ceremony (roaming USB key; real `makeCredential` → canonical records; real `getAssertion` passing §37 with UP+UV; presentation-bound approval end-to-end → `PRODUCTION` `AuthenticatedHumanPrincipal`; wrong-challenge / missing-UV / replay / revoked-credential rejections). **On success, N-16-5 CLOSES.** | RHAMP-REQ-156 `.1R.33` row; §62 |
| after | N-16-6 → N-16-7 | separately authorized; **N-16-7 strictly last**; no Slice C until N-16-3..7 all close. | RHAMP-REQ-157 |

The premature-closure / status-logic guard the `.1R.30R.3.3` phase folded to
its successor is folded here into `.1R.30R.3.4` / `.1R.30R.3.5` scope: the
implementing phase and its IV SHALL assert that N-16-5 cannot report CLOSED
until `.1R.30R.5` completes with the real-hardware evidence.

## 21. Successor phase IDs (this phase's §41, §44, §59) — CPIPC-valid

**CPIPC-001 v1.0 §4.2 grammar check.** `phase-id = series , branch , { "." ,
subphase-segment }`; `numeric-segment = digit , { digit } , [ letter , { letter
} ]`; `letter-segment = letter , { letter }`. The current phase
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R` parses as series/branch `149O` + `20L`
… + subphase segments `… 1R . 30R . 3 . 3R`. The recommended successors:

| Recommended ID | Parse | Valid? |
|---|---|---|
| `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4` | last segment `3R` (numeric `3` + letter `R`) replaced by sibling numeric-segment `4` under parent `… .3` | **valid** — sibling of `.3.3` / `.3.3R` on the `.1R.30R.3` line |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5` | numeric-segment `5` under `… .3` | **valid** |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4` | numeric-segment `4` under parent `… .30R` | **valid** — sibling of `.30R.3` |
| `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5` | numeric-segment `5` under `… .30R` | **valid** |

All four are **recommended, NOT reserved**; each requires its own explicit human
authorization and its own IV; confirm CPIPC-validity again at use time.

### Treatment of the old `.1R.30R.3.4 / .3.5 / .3.6` recommendations (this phase's §39, §44)

The `.1R.30R.3.3` BLOCKED report and prior handoff prose recommended a
post-adjudication sequence of "Slice-2 IV (`.1R.30R.3.4`) → Slice-3
implementation / IV (`.3.5` / `.3.6`) → `.1R.30R.4` composite IV → `.1R.30R.5`
presentation → `.1R.30R.6` IV + hardware + closure". Under **Decision A** there
is no separate Slice 2 / Slice 3 and no separate composite IV. Therefore:

- the old `.1R.30R.3.4` ("Slice-2 IV"), `.1R.30R.3.5` ("Slice-3 impl"), and
  `.1R.30R.3.6` ("Slice-3 IV") recommendations are **SUPERSEDED** — they are
  **not reservations** and SHALL NOT be reused blindly;
- the ID strings `.1R.30R.3.4` and `.1R.30R.3.5` are **re-assigned** by this
  adjudication to, respectively, the merged mechanism implementation and its
  single IV (§20);
- `.1R.30R.4` is re-assigned from "composite IV" to the protected-presentation
  phase (RHAMP-REQ-156 `.1R.32`); `.1R.30R.5` to its IV + hardware + closure
  (RHAMP-REQ-156 `.1R.33`);
- `.1R.30R.6` is **not** needed and carries no recommendation.

## 22. Contract byte-identity + production zero-diff proofs (this phase's §46, §47, §49)

Independently re-derived at `A = 93266b7d` → HEAD:

| Fence | Check | Result |
|---|---|---|
| All normative contracts | `git diff --name-only 93266b7d HEAD -- docs/contracts` | **empty** — RHAMP-001 v1.0, HPAC-PAWA-001 v1.1, HPAC-001 v2.1, CPIPC-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1 all byte-unchanged |
| `src/pcae` + `scripts` | `git diff --name-only 93266b7d HEAD -- src/pcae scripts` | **empty** — no production or script file created, modified, or deleted |
| `hpac_verifier.py` byte identity | `git diff 93266b7d HEAD -- src/pcae/core/hpac_verifier.py` | **empty — unchanged** |
| `_ELIGIBLE_MECHANISM_IDS` | `hpac_verifier.py:128` | `frozenset({"hpac.deterministic.test-only.v1"})` — **unchanged; no `hpac.fido2.uv_presence.v2`** |
| Gate 5 / Gate 9 | `git diff 93266b7d HEAD -- src/pcae/core/runtime_dispatch_gate5.py src/pcae/core/runtime_dispatch_gate9.py` | **empty — unchanged** |
| `approval_presentation.py` `verifier_kind` set | (file unchanged) | still only `deterministic-test-fixture` accepted |
| `require_real_assurance` | (verifier unchanged) | still "can only reject" |
| Historical `.1R.30`, `.1R.30R.3.2`, `.1R.30R.3.3` BLOCKED artifacts | `git diff --name-only 93266b7d HEAD -- docs/` | only the **new** `.3.3R` doc is listed; no historical report modified |
| `tests/` | `git diff --name-only 93266b7d HEAD -- tests/` | only the **new** `test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_3r_decomposition_adjudication.py` is listed; no existing test file touched |

The A → HEAD tracked delta is exactly: this doc; the new adjudication test
file; `PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/**`; `tasks/DECISIONS.md`;
`.pcae/phase-completion-*`.

## 23. Adjudication test suite + no-test-weakening (this phase's §48, §50)

**Added:** `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_3r_decomposition_adjudication.py`
— a **verification-only** suite (no `src/pcae` import beyond reading module
source as text, no implementation). It asserts the source facts this
adjudication rests on:

1. RHAMP-REQ-043 makes `enroll_credential`'s `public_key` a `makeCredential`
   output (contract text);
2. RHAMP-REQ-048's first-credential bootstrap `"all of"` conjunction contains
   "verification of the `makeCredential` response";
3. RHAMP-REQ-055/056 define `RHAMP-FIDO2-CREDENTIAL/1.0` as a closed schema over
   authenticator output with **no** placeholder / pending variant;
4. RHAMP-REQ-129 freezes the vocabulary at exactly **41** codes;
5. RHAMP-REQ-156 bundles "mechanism + registry + bootstrap" into the single
   `.1R.30` row;
6. no `PENDING` / `PENDING_MATERIAL` / staged credential-lifecycle state exists
   in `human_principal_registry.py` (`CredentialRecord` status is
   `{active, revoked}` only);
7. no material-less canonical registration path exists
   (`_ELIGIBLE_MECHANISM_IDS` unchanged; `hpac_verifier` "does not attempt real
   signature math");
8. the current production tree is unchanged by this phase
   (`git diff 93266b7d HEAD -- src/pcae scripts docs/contracts` empty);
9. runtime / first-effect boundary unchanged (`_ELIGIBLE_MECHANISM_IDS`,
   Gate 5 / Gate 9 byte-identity).

**No implementation tests.** **No-test-weakening:** `git diff 93266b7d HEAD --
tests/` lists **only** the new file; no `def test_` was removed, renamed,
skipped, xfailed, or made `fnmatch`/wildcard-broader anywhere. The
`.1R.19R.1` / `.1R.22R` `test_no_test_weakening` scanners are not tripped (they
scan for removed/renamed `def test_` in touched pre-existing files; the new file
did not exist at any baseline they check).

## 24. Contract identity (this phase's §49)

Verified unchanged at HEAD: **RHAMP-001 v1.0** (1580 lines, SHA over the file
byte-identical to A), **HPAC-PAWA-001 v1.1**, **HPAC-001 v2.1**, and every other
normative contract under `docs/contracts/`.

## 25. Runtime / first external effect / N-16-6 / N-16-7 / N-23 (this phase's §51, §52, §53, §54)

- **Runtime:** State `Observed` / Maximum Capability `observe` / Execution
  Availability `unavailable` / Plugins `0` / Capabilities `0` — **unchanged**.
- **First external effect:** **ABSENT / UNREACHABLE** — unchanged. No Slice C.
  No `adapter.dispatch(` call site anywhere in `src/pcae`.
- **N-16-6 / N-16-7:** OPEN and untouched. N-16-7 strictly last. This
  adjudication does not begin, reference-as-unblocked, or schedule either.
- **N-23-1:** INFO — carried unchanged. **N-23-2:** INFO / DEFERRED
  NORMALIZATION DEBT — carried unchanged. This phase does not normalize
  PBRD / PBNDE semantics.

## 26. Historical phase status (this phase's §39, §40)

- **`.1R.30` = BLOCKED** — immutable; not reopened, not resumed, not
  reinterpreted.
- **`.1R.30R.3.2` = BLOCKED** — immutable.
- **`.1R.30R.3.3` = BLOCKED** — immutable. This adjudication **supersedes only
  the future decomposition** it recommended; it does **not** reinterpret
  `.1R.30R.3.3` as a planning success that replaces the blocker. The
  `.1R.30R.3.3` phase correctly returned a decomposition blocker; this phase
  resolves it.
- The append-only **N-16-5 NOT CLOSED** correction made by `.1R.30R.3.3` in
  `PROJECT_STATUS.md` stands; the historical `.1R.30R.3.2.1.1` report remains
  byte-unchanged.

## 27. Decision-quality bar check (this phase's §57, §58)

| # | Optimize for | Decision A |
|---|---|---|
| 1 | frozen contract fidelity | **best** — A *is* RHAMP-REQ-156; zero contract change |
| 2 | trust-boundary clarity | **best** — no new lifecycle state, no new admin model, PAWA one-operation preserved |
| 3 | fail-closed lifecycle semantics | **best** — single atomic multi-artifact publish; no partial/pending state |
| 4 | minimum unnecessary contract churn | **best** — none; B needs a MINOR/MAJOR + possible HPAC-001 cascade |
| 5 | coherent bootstrap | **best** — RHAMP-REQ-048 `"all of"` kept intact; Slice-1 anchor consumed |
| 6 | independent verifiability | **best** — one IV, whole mechanism; store not IV'd twice |
| 7 | minimum pseudo-authoritative intermediate state | **best** — zero; B introduces `PENDING_MATERIAL` |
| 8 | maintainability | **best** — one module set, one baseline |

The working hypothesis (this phase's §58 — *"Candidate A — RE-MERGE, because
RHAMP v1.0 appears intentionally to bind the first real credential
creation/registration/bootstrap mechanism into one coherent trust transition,
and introducing a staged pre-credential authority state would add lifecycle
complexity without yet-demonstrated security benefit"*) **survives primary-source
scrutiny**: §4 (dependency graph), §7 (RHAMP-REQ-156 atomicity), §8 (frozen
intent), §11.7 (B benefit test fails), §12.3 (C benefit available inside A).
**Candidate A is selected.**

## 28. Contract-change decision (this phase's §40) — DECISION A

```
DECISION A:  RHAMP-001 v1.0 PRESERVED (byte-unchanged); the former Slice 2 +
             Slice 3 are RE-MERGED into RHAMP-REQ-156's single .1R.30 bundle
             (minus the already-CLOSED PAWA writer anchor), implemented as one
             phase (.1R.30R.3.4) and independently verified as one unit
             (.1R.30R.3.5).

DECISION B:  NOT SELECTED — RHAMP v1.1 contract evolution is NOT required for
             N-16-5. (Rejected: §11.4 versioning triggers; §11.7 benefit test;
             §27 bar #7.)

DECISION C:  NOT SELECTED — a material-free scaffolding slice is contract-tolerable
             but is not a RHAMP registration slice, adds a phase + an IV with no
             isolation dividend, and its one benefit is available inside A.
             (Rejected: §12.2, §12.3, this phase's §24.)
```

**No contract file is modified by this phase.** `git diff --name-only
93266b7d HEAD -- docs/contracts` is empty (§22).

## 29. Successor implementation phase (this phase's §41, §59) — IF/AS DECISION A

**Recommended next phase (ID recommended, NOT reserved; confirm under CPIPC;
own explicit human authorization required; do not begin here):**

> `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4` — **N-16-5 RHAMP Real FIDO2 Credential
> Registration, Counter-State, Bootstrap & Authentication Mechanism
> Implementation** (merged; formerly split Slice 2 + Slice 3).

**Exact production scope:** §10.1 / §10.3 (the "yes" rows).

**Exact no-go boundaries for `.1R.30R.3.4`:** no protected presentation helper;
no `renderer_profile` / `mechanism_attestation`; no `verifier_kind` widening in
`approval_presentation.py`; no `require_real_assurance` wiring through Gate 5 /
Gate 9; no `PRODUCTION` `AuthenticatedHumanPrincipal` obtainable on a production
path; no hardware access; no N-16-6; no N-16-7; no Slice C; no first external
effect; no execution enablement; no custom cryptography; no new dependency; no
`CredentialRecord` schema change; no wildcard / `fnmatch` in
`_ELIGIBLE_MECHANISM_IDS`.

**Following independent verification phase:**
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5` — Independent Verification of
`.1R.30R.3.4` (RHAMP-REQ-156 `.1R.31` requirements; broad fixed-SHA A/B; the
≥ 55-case negative matrix; RHAMP-REQ-164 contract→production equivalence).

**Then:** `.1R.30R.4` (protected presentation + `require_real_assurance` —
RHAMP-REQ-156 `.1R.32`) → `.1R.30R.5` (IV + mandatory real-CTAP2-hardware
verification + **N-16-5 closure** — RHAMP-REQ-156 `.1R.33`) → N-16-6 → N-16-7
(strictly last).

## 30. `.3` governance incident (this phase's §55, §60) — preserved

```
DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED
```

Preserved exactly. Only the primary human-authorized operator holds
`.1R.30R.3.3R` lifecycle authority. This phase's governed commit / push /
`pcae phase complete` were performed under the operator's explicit direction in
this session, through the governed PCAE lifecycle only — no raw `git commit` /
`git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass.
No delegated worker committed, finalized, or pushed. The historical `.1R.30`,
`.1R.30R.3.2`, and `.1R.30R.3.3` BLOCKED artifacts remain immutable; this phase
neither reopened nor resumed them.

## 31. Files changed / tests / analysis

- **Added:** this canonical adjudication report.
- **Added:** `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_3r_decomposition_adjudication.py`
  (verification-only; §23).
- **Updated:** `PROJECT_STATUS.md` (new Current Phase entry, append-only),
  `CHANGELOG.md` (new bullet), `tasks/DECISIONS.md` (adjudication decision
  entry), task lifecycle artifacts, `.pcae/phase-completion-metadata.json` /
  `.pcae/phase-completion-report.md`.
- `git diff --name-only 93266b7d HEAD -- docs/contracts` → **empty** (§22).
- `git diff --name-only 93266b7d HEAD -- src/pcae scripts` → **empty** (§22).
- **Tests:** one new verification-only file; none removed, renamed, weakened,
  skipped, or xfailed. Targeted run of the new suite: all pass (§23).
- **Analysis run:** read-only `git` history inspection; `pcae health` / `check`
  / `status coherence` / `doctor task-memory` / `push check` / `runtime inspect`
  / `notify status` / `phase-report show`; full read of RHAMP-001 v1.0, the
  `.1R.29` freeze report, the `.1R.30R.3.3` BLOCKED report, and the CPIPC-001
  grammar; read-only inspection of `hpac_verifier.py`,
  `human_principal_registry.py`, `hpac_protected_admin_writer.py`,
  `approval_presentation.py`, `hatp_fido2_provider.py`.

## 32. No-go confirmations

- No `src/pcae` file was created, modified, or deleted; `git diff --name-only 93266b7d HEAD -- src/pcae` is empty.
- No `scripts/**` file was created, modified, or deleted.
- No normative contract file was edited; RHAMP-001 v1.0, HPAC-PAWA-001 v1.1, HPAC-001 v2.1, CPIPC-001, RIHAC-001, RIASC-001, RDGO-001, and every other contract are byte-unchanged.
- No RHAMP-001 version was bumped, forced, or proposed as required; v1.0 stands; no v1.1 is created or drafted.
- No RHAMP credential sidecar, counter-state artifact, enrollment ceremony, or first-credential bootstrap was implemented, and no schema code for them was written.
- No `makeCredential` call, no `getAssertion` call, no `FIDO2HumanAuthenticator`, no `CoseKey.verify`, no `rpIdHash` check, no `FLAG.UP` / `FLAG.UV` check was added anywhere.
- No `fido2` / `Ctap2` / `CtapHidDevice` / `CoseKey` / `AuthenticatorData` import was added.
- No `hpac_verifier` change; `_ELIGIBLE_MECHANISM_IDS` is byte-unchanged (`frozenset({"hpac.deterministic.test-only.v1"})`); no `hpac.fido2.uv_presence.v2` entry; no wildcard.
- No `verifier_kind` was added to any acceptance set; `approval_presentation.py` byte-unchanged.
- No protected presentation helper, `renderer_profile`, or `mechanism_attestation` was implemented.
- No `require_real_assurance` wiring through Gate 5 / Gate 9; Gate 5 and Gate 9 byte-unchanged.
- No `AuthenticatedHumanPrincipal` of class `PRODUCTION` was produced anywhere.
- No hardware authenticator was accessed, enumerated, or prompted; no CTAP device I/O.
- No real `HPAC_PROTECTED_ROOT` was provisioned, written, or mutated; no sudo; no real OS account created, modified, or resolved.
- No N-16-6 work and no N-16-7 work was begun; N-16-7 stays strictly last.
- No Slice C and no first external effect was begun, called, or made reachable; the first external effect remains ABSENT AND UNREACHABLE; runtime remains `Observed` / `observe` / `unavailable`.
- No execution was enabled; no runtime capability elevated; no `Observed -> Approved/Executable` transition.
- No historical BLOCKED verdict or canonical report was rewritten; `.1R.30`, `.1R.30R.3.2`, `.1R.30R.3.3` remain immutable; the `.1R.30R.3.2.1.1` report is byte-unchanged.
- No raw `git commit` or `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass; governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.30R.3.3R` lifecycle authority; `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.
- No test was removed, renamed, skipped, xfailed, or broadened; the only `tests/` change is the new verification-only file.
- No dependency was installed, upgraded, vendored, or unpinned.
- No BLOCKED condition was reached — this phase exists to resolve the decomposition blocker and it does (§28).
- No "Remaining" section is presented; all authorized `.1R.30R.3.3R` work is complete.

## 33. Required-final-report index (this phase's §56)

Phase ID / title — §1. Phase-entry SHA / immutable A — §1. Primary sources —
§2. `.1R.30R.3.3` blocker reconstruction — §4. Exact RHAMP requirement chain —
§4.1. `makeCredential` dependency graph — §5. Authentication dependency graph —
§6. RHAMP-REQ-156 interpretation — §7 (interpretation C). `.1R.29` original
intent — §8. Current Slice-2/Slice-3 incompatibility — §4, §9. Candidate A
analysis — §10. Candidate B analysis — §11. Candidate B versioning trigger
analysis — §11.4. Candidate B migration / schema impact — §11.6. Candidate C
analysis — §12. Candidate comparison table — §13. Chosen decision — §28
(Decision A). Reason for rejecting the other two — §11.7 (B), §12.3 (C), §13,
§27. PAWA interaction — §14. First-credential bootstrap model — §15.
Administration-vs-authentication boundary — §15. Counter-state timing — §16.
Canonical publish point — §17. Multi-artifact atomicity — §18.1.
Hardware-verification timing — §18.2. HATP provider reuse boundary — §18.3.
Mechanism ID — §19. rp_id / client context — §19. Authenticator profile — §19.
Presentation boundary — §19, §20. Gate 5 / Gate 9 boundary — §19, §20.
Corrected remaining N-16-5 sequence — §20. Historical `.1R.30R.3.3`
preservation — §26. Contract-change verdict — §28. Exact successor
implementation / contract phase — §29. Exact successor IV sequence — §20, §29.
Treatment of old `.3.4` / `.3.5` / `.3.6` recommendations — §21. Current status
— §34. Contract byte identity — §22, §24. Production zero-diff proof — §22.
No-test-weakening — §23. Runtime — §25. First-effect absence — §25.
N-16-6 / N-16-7 — §25. N-23 — §25. `.3` governance incident — §30. Commits /
pushed status / `origin/main..HEAD` — `.pcae/phase-completion-metadata.json`
and `.pcae/phase-completion-report.md`.

## 34. Current status

```
N-16-3                          CLOSED
N-16-4                          CLOSED
PAWA Slice 1                    CLOSED
HPAC-PAWA-001 v1.1              VERIFIED
historical .1R.30               BLOCKED / IMMUTABLE
historical .1R.30R.3.2          BLOCKED / IMMUTABLE
.1R.30R.3.2.1 repair            VERIFIED
.1R.30R.3.2.1.1 IV              VERIFIED
historical .1R.30R.3.3          BLOCKED / IMMUTABLE
.1R.30R.3.3R (this phase)       ADJUDICATION COMPLETE — DECISION A (RE-MERGE)
former Slice 2 / Slice 3        RE-MERGED into one implementation phase (.1R.30R.3.4)
RHAMP-001                       v1.0 — PRESERVED, byte-unchanged; NO v1.1 required
N-16-5                          NOT CLOSED
N-16-6                          OPEN
N-16-7                          OPEN (strictly last)
Runtime                        Observed / observe / unavailable
First external effect          ABSENT / UNREACHABLE
```

No status artifact implies Slice 2 was implemented. Slice 1 CLOSED;
`.1R.30R.3.3` BLOCKED; N-16-5 NOT CLOSED — all preserved.

---

**STATUS: ADJUDICATION COMPLETE. DECISION A (RE-MERGE) SELECTED. RHAMP-001 v1.0
PRESERVED BYTE-UNCHANGED. NO CONTRACT CHANGE. NO PRODUCTION OR SCRIPT CODE
CHANGED. N-16-5 NOT CLOSED. Slice 1 remains CLOSED. Historical `.1R.30`,
`.1R.30R.3.2`, `.1R.30R.3.3` BLOCKED artifacts immutable. Runtime Observed /
observe / unavailable. First external effect ABSENT. `DELEGATED .3
FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved.**

*Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.3R — canonical decomposition-adjudication artifact.*
