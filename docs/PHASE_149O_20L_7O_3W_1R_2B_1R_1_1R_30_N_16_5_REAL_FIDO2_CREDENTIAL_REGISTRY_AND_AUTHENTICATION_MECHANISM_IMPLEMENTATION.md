# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30 — N-16-5 Real FIDO2 Credential Registry and Authentication Mechanism Implementation

**Status: BLOCKED** (valid early-STOP condition reached during primary-source
reconstruction, before any production source was created or modified).

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30`
- **Phase-entry SHA:** `e40d4ce14858ef18aca4bd845f5ccca9411be7f5`
  (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.29: reconcile governed push state …`)
- **Candidate SHA (this finalization):** the governed BLOCKED-finalization
  commits below; `git diff e40d4ce1 HEAD -- src/pcae` is **empty**,
  `git diff e40d4ce1 HEAD -- docs/contracts` is **empty**.
- **Authorization:** explicit single-phase human authorization for `.1R.30`
  only (mechanism + registry + bootstrap half of N-16-5, per RHAMP-001 v1.0
  §64 / RHAMP-REQ-156 `.1R.30` row). No protected approval UI, no real
  approval-proof path, no PRODUCTION approval authority, no N-16-6/N-16-7, no
  Slice C, no first external effect, no execution enablement was in scope and
  none was performed.

---

## 1. Outcome

`.1R.30` is **BLOCKED** at implementation scope item **A — "production
`HumanPrincipalRegistryStore` writer path"** (phase prompt §4.A, §6, §7;
RHAMP-REQ-156 `.1R.30` row; RHAMP-REQ-047/048/049; RHAMP-INV-005). The block
was reached during the mandated primary-source reconstruction (phase prompt
§2, §3, §94 steps 1–4), **before** any `FIDO2HumanAuthenticator`, sidecar
store, counter-state store, enrollment tool, `hpac_verifier` real branch,
`_ELIGIBLE_MECHANISM_IDS` change, or test was written.

**Blocker classification: `store` / `provenance`, with a `contract`-ambiguity
component.** The existing governance model implements only the *negative* half
of HPAC-REQ-022/023's protected-admin anchor (the protected root is validated
as **not** agent-writable) and provides **no** *positive* half — there is no
implemented, contract-specified mechanism by which the "externally established
deployment-owner protected administration principal" authenticates to PCAE and
obtains a **production** `HPACWriterCapability`. Building one requires either
(a) inventing a new admin-authority model, which phase prompt §18 explicitly
forbids ("Do not invent a new admin authority model"), or (b) evolving the
`hpac_foundation.py` trust boundary, which is the valid early-STOP condition
"the existing HumanPrincipalRegistry model cannot safely host a production
writer without contract evolution", or (c) resolving a genuine HPAC-001
silence — *how* the external OS principal proves itself (a root-owned
capability descriptor? a setuid helper? an out-of-band signed token? a `sudo`
gate?) — each with materially different security properties, which is the
valid early-STOP condition "a new contract ambiguity requires human
adjudication".

Per RHAMP-REQ-049 verbatim: *"A ceremony that cannot establish the
HPAC-REQ-023 anchor → reject (`bootstrap_authority_unproven`); the
implementing phase STOPS (BLOCKED) if the existing governance model provides
no such anchor."* And RHAMP-INV-005: *"an unprovable anchor fails closed /
BLOCKS (§14)."*

---

## 2. Primary sources reconstructed (phase prompt §2, §3)

Read in full or to complete relevant scope before the block was reached:

| Source | Scope read | Purpose |
|---|---|---|
| `PROJECT_STATUS.md` (current head) | current-phase block + N-16 gate-chain state | baseline confirmation |
| `docs/PHASE_…_1R_28_…PLANNING.md` | §0, §4–§13, §12 residual set, §31, §32, §35 | `.1R.28` planning baseline; production-writer gap analysis |
| `tasks/done/20260901-2259-phase-…-1r-29-rhamp-001-v1-0-contract-freeze.md` | full | `.1R.29` freeze scope |
| `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md` (RHAMP-001 v1.0) | **full — all 71 sections, RHAMP-REQ-001..169, all 18 invariants, §49.1 41-code table** | the sole normative source for `.1R.30` scope |
| `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.1) | §7 (HPAC-REQ-022/023/024), §8 (HPAC-REQ-025..031), §9–§10, §28 (HPAC-REQ-079/080), §30 | parent contract; bootstrap-authority anchor definition |
| `src/pcae/core/hpac_foundation.py` | **full (782 lines)** | `HPACStoreAuthority`, `HPACWriterCapability`, `ProtectedAdminCapability`, `production()` / `writer()` / `_validate_production_boundary` |
| `src/pcae/core/human_principal_registry.py` | **full (578 lines)** | `HumanPrincipalRegistryStore`, `enroll_principal`/`enroll_credential`, `_writer()`, `CredentialRecord` (byte-frozen field set) |
| `src/pcae/core/hpac_verifier.py` | **full (746 lines)** | `_ELIGIBLE_MECHANISM_IDS`, `_verify_assertion_material`, `_verify_mechanism_eligibility`, `_check_up_uv`, `_authority_class_of`, `verify_human_authentication`, `require_real_assurance` semantics |
| `src/pcae/core/human_authenticator.py` | **full (130 lines)** | `HumanAuthenticator` `Protocol`, `Challenge`, `ProofMaterial`, `MechanismDescriptor`, `AssuranceLevel` |
| `src/pcae/core/hatp_principal_signer_admin.py` | `enroll_principal`/`revoke_principal`/`enroll_signer` structure, `_resolve_protected_root`, `_require_trust_store_available`, evidence models | HATP admin-ceremony pattern (reuse-as-pattern candidate) |
| `src/pcae/core/hatp_fido2_provider.py` | module inventory (grep-level) | CTAP2 primitive-reuse surface (§38) — not needed once blocked |
| Repository inspection: `git status/log/rev-list`, `pcae health/check/status coherence/doctor task-memory/push check/runtime inspect`, `pcae notify status`, `pcae phase-report show --latest` | full | phase-entry baseline (below) |

**Not read to completion** (block reached first, correctly per phase prompt
§3's "read … before coding" and the BLOCKED instruction "do not repair
outside scope"): RIHAC-001 v2.0, RIASC-001 v3.0, HPSE-001 v1.1, HHCE,
`HPAC-AUTHORITY-CONSUMPTION/2.1`, Gate-5/Gate-9 contracts, `approval_presentation.py`,
`hpac_lifecycle.py`, `human_authentication_proof.py`, the HATP FIDO2 provider
in full. These govern the presentation / proof-lifecycle / gate-consumption
half, which `.1R.30` does not implement and which the block does not depend
on.

---

## 3. Phase-entry baseline (phase prompt §3) — CONFIRMED

| Check | Result |
|---|---|
| `.1R.29` is the latest completed phase | ✅ `pcae phase-report show --latest` → `149O.20L.7O.3W.1R.2B.1R.1.1R.29 (completed, report: complete)` |
| No active governed phase before startup | ✅ active task was the post-`.1R.29` idle placeholder |
| `origin/main..HEAD` = 0 | ✅ `git rev-list --count origin/main..HEAD` → `0` |
| Runtime `Observed` / `observe` / `unavailable` | ✅ `pcae runtime inspect` → `not_implemented` / `Observed` / `unavailable`; 0 plugins / 0 capabilities |
| First external effect ABSENT | ✅ no `adapter.dispatch(` call site; no Slice C; runtime non-executing |
| `pcae health` | ✅ healthy |
| `pcae check` | ✅ passed |
| `pcae status coherence` | ✅ coherent |
| `pcae doctor task-memory` | ⚠️ warning-only pre-existing `tasks/DONE.md`-omission hygiene debt from earlier phases; **no current-phase error** |
| `pcae push check` | ✅ `nothing_to_push` |
| `pcae notify status` | ✅ Telegram configured, enabled, outbound-ready |

---

## 4. Contract → production traceability (phase prompt §5) — as far as reached

The block is at item A. The traceability rows below are the analysis completed
**before** the block, showing which RHAMP requirements *would* have mapped to
existing seams (no defect found in those) and where the missing anchor sits.

| RHAMP req | Intended `.1R.30` implementation | Existing seam | Status |
|---|---|---|---|
| RHAMP-REQ-011 / §40 (`_ELIGIBLE_MECHANISM_IDS += {"hpac.fido2.uv_presence.v2"}`) | `hpac_verifier.py:128` `frozenset` literal | `_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.deterministic.test-only.v1"})` — exact, no wildcard | seam present; not reached |
| RHAMP-REQ-055 (`CredentialRecord` byte-unchanged) | no change | `human_principal_registry.py:98` frozen 9-field dataclass, `_CREDENTIAL_ALLOWED_FIELDS` closed | ✅ compatible — no change needed |
| RHAMP-REQ-034 / §10 (add `FLAG.UV` check HATP omits) | `hpac_verifier._check_up_uv` already asserts `proof.uv is True`; real branch adds `AuthenticatorData` `FLAG.UV` decode | `_check_up_uv` at `hpac_verifier.py:467` | seam present; not reached |
| RHAMP-REQ-102 / §37 (real CTAP2 assertion verification) | replace `_verify_assertion_material`'s categorical-reject with `CoseKey.verify` over `authenticatorData ‖ client_data_hash` | `_verify_assertion_material` at `hpac_verifier.py:429` is a documented "no real verifier in this phase" stub | seam present; not reached |
| RHAMP-REQ-023 / §7 (`RHAMP-CLIENT-CONTEXT/1.0`) | new canonical client-data object + `client_data_hash` | `Challenge` (`human_authenticator.py`) + `canonical_digest` (`hpac_foundation.py`) | primitives present; not reached |
| RHAMP-REQ-056/057 (`RHAMP-FIDO2-CREDENTIAL/1.0` sidecar) | new protected per-credential artifact under `<HPAC_PROTECTED_ROOT>/credentials/<credential_id>/fido2-credential.json` | `write_atomic_create_only` + `read_canonical_json_document` + `HPACStoreAuthority.record_write/verify_record` | primitives present; **write requires a writer capability — see block** |
| RHAMP-REQ-068/069 (`RHAMP-COUNTER-STATE/1.0`) | new protected per-credential artifact, atomic-replace updated | `write_atomic_replace` + read-back (`hpac_foundation.py:701`) satisfies RHAMP-REQ-073's atomicity prerequisite | primitive present; **write requires a writer capability — see block** |
| RHAMP-REQ-071/072 (counter linearization) | order: counter check (verify step) → proof mint (step 10) → atomic counter update | `hpac_verifier.verify_human_authentication` step 10 + `write_atomic_replace` | design viable; not reached |
| **RHAMP-REQ-043/047/048/049 / §13, §14 (production writer path + first-credential bootstrap)** | **`HumanPrincipalRegistryStore.enroll_credential(<production writer capability>, …)` under a protected-admin ceremony anchored by HPAC-REQ-023's external deployment-owner principal** | **`HPACStoreAuthority.writer()` `hpac_foundation.py:417` — categorically `raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")` for any non-`FIXTURE_NON_REAL` class. No production-writer factory (`hpac_foundation.py:301`: "There is intentionally no public production-writer factory in this phase"). `ProtectedAdminCapability` is "Legacy fixture-only … can never authorize a production store" (`hpac_foundation.py:109`).** | **❌ BLOCKED — no anchor** |

---

## 5. The block, with exact source and contract evidence (phase prompt BLOCKED instructions)

### 5.1 What `.1R.30` scope item A requires

Phase prompt §4.A / §6 / §7 and RHAMP-REQ-156 (`.1R.30` row) require a
**production** `HumanPrincipalRegistryStore` writer path that:

- enforces a canonical protected-root location, **trusted writer
  identity/provenance**, atomic write, read-back verification, no
  caller-selected path, no symlink/traversal escape (phase prompt §7);
- is exercised by the first-credential **bootstrap ceremony** whose authority
  is *"HPAC-REQ-023's externally established deployment-owner protected
  administration principal — an OS/equivalent protected administration
  principal that owns the deployment-scoped protected root outside every
  repository and is **unavailable to ordinary same-user agent execution**"*
  (RHAMP-REQ-047);
- fails closed with `bootstrap_authority_unproven` and **STOPS (BLOCKED)** *"if
  the existing governance model provides no such anchor"* (RHAMP-REQ-049).

### 5.2 What the existing governance model actually provides

`hpac_foundation.py` (read in full):

```
# line 12–13 (module docstring)
    an externally provisioned protected root; real enrollment/writer ceremony is
    still deferred.

# line 300–302 (HPACStoreAuthority class docstring)
    ``production()`` accepts no root and resolves the platform constant.
    There is intentionally no public production-writer factory in this phase.

# line 417–431 (HPACStoreAuthority.writer)
    def writer(self, role: str, *, subject: Optional[str] = None) -> HPACWriterCapability:
        """Issue a bound fixture writer; real writer ceremony is deferred."""
        if self.authority_class is not HPACAuthorityClass.FIXTURE_NON_REAL:
            raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")

# line 109–117 (ProtectedAdminCapability)
    """Legacy fixture-only mutation marker retained for `.3` tests.
    It is intentionally public and reproducible, and for exactly that reason
    can never authorize a production store. …"""
```

`human_principal_registry.py` (read in full):

```
# line 263–265
    @classmethod
    def production(cls) -> "HumanPrincipalRegistryStore":
        return cls(HPACStoreAuthority.production())

# line 332–339 (HumanPrincipalRegistryStore._writer) — the mutation gate every
# enroll_*/revoke_* call routes through:
    def _writer(self, capability):
        if isinstance(capability, HPACWriterCapability):
            self._authority.require_writer(capability, self._WRITER_ROLE)  # PRODUCTION → OK only if a
                                                                          # PRODUCTION HPACWriterCapability exists
        return self._authority.legacy_fixture_writer(capability, self._WRITER_ROLE)  # forces FIXTURE_NON_REAL
```

`HumanPrincipalRegistryStore.production()` constructs a `PRODUCTION`
`HPACStoreAuthority`, but **the only way to obtain the
`HPACWriterCapability` that `_writer()` → `require_writer()` demands is
`HPACStoreAuthority.writer()`, which refuses every non-fixture class.** There
is no production-writer factory, no protected-admin authentication ceremony,
and no consumable representation of the "external deployment-owner protected
administration principal" anywhere in `src/pcae` (verified:
`grep -rn "HPACAuthorityClass.PRODUCTION" src/pcae` and
`grep -rln "deployment.owner|production_writer|ProductionWriter" src/pcae` —
the latter returns nothing).

### 5.3 HPAC-001 froze the policy, not the mechanism

HPAC-001 v2.1 §7:

- **HPAC-REQ-022** — the protected root "SHALL be owned and writable only by an
  OS/equivalent protected administration principal unavailable to ordinary
  same-user agent execution." → **the *negative* boundary.** Implemented:
  `HPACStoreAuthority._validate_production_boundary()` (`hpac_foundation.py:351`)
  calls `hatp_class_b_topology_verifier._effective_write_access` /
  `_ancestor_chain_safe` and raises unless the root is provably **not**
  agent-writable with safe ancestors. This half exists and is correct.
- **HPAC-REQ-023** — the external principal "SHALL launch a non-defaultable
  ceremony, display the exact registry identity … require authenticator UP and
  UV, verify the FIDO2 registration response, and atomically create the first
  records …" → **describes what the ceremony must *do*, not how PCAE
  code *recognises* the principal or *mints* its writer capability.**
- **HPAC-REQ-024** — bootstrap mutation "SHALL be available only in the
  protected administration context and never as an ordinary `pcae` CLI …" →
  again a *prohibition*, not a *mechanism*.
- **HPAC-REQ-080** — "Only the external protected deployment administration
  principal may configure …" — a *policy*, not a *mechanism*.

The `.1R.28` planning artifact states this explicitly (§4, lines 176–179):
*"The **only** gap is HPAC-REQ-023's real bootstrap enrollment ceremony
(external deployment-owner protected admin, non-defaultable, UP+UV, verified
`makeCredential` response) — **frozen in HPAC-001, not yet implemented**."* —
and §5 line 195: `_verify_assertion_material` *"currently categorically rejects
every non-deterministic mechanism; no real signature math"*. The planning
artifact assumed this gap was routine implementation work for `.1R.30`; the
reconstruction here finds that closing it is not routine — it is the exact
anchor RHAMP-REQ-049 / RHAMP-INV-005 name as a mandatory STOP when absent.

### 5.4 Why this is a STOP and not in-scope implementation

Three of the phase prompt's own "VALID EARLY STOP CONDITIONS" are each
independently satisfied:

1. *"the existing HumanPrincipalRegistry model cannot safely host a production
   writer without contract evolution"* — `hpac_foundation.py` would have to be
   changed to add a production-writer trust path; this module is the HPAC
   trust root, and the change defines how a real human-authentication
   registry is ever mutated.
2. *"the external deployment-owner protected-admin bootstrap authority
   required by HPAC-REQ-023 cannot be consumed safely by the enrollment
   tool"* — there is no consumable authority object; the enrollment tool would
   have nothing to consume.
3. *"a new contract ambiguity requires human adjudication"* — HPAC-001 does
   not specify the concrete trust mechanism for the external principal (a
   root-owned capability descriptor under `<HPAC_PROTECTED_ROOT>/.authority/`?
   a setuid/`sudo`-gated helper binary? an out-of-band administrator-signed
   installation record? OS-keychain-held admin key?). Each is a distinct
   security architecture with distinct threat properties, and phase prompt
   §18 forbids "invent[ing] a new admin authority model."

Phase prompt §18 verbatim: *"Reconstruct exact HPAC-REQ-023 authority source.
Do not invent a new admin authority model. If the source is external to PCAE,
enforce its frozen boundary precisely. **If current production source cannot
consume it safely: STOP.**"*

### 5.5 Implementation point

`src/pcae/core/hpac_foundation.py`, `HPACStoreAuthority.writer()`
(line 417–431) and the absent `HPACStoreAuthority.production_writer(...)` /
protected-admin-authentication factory; consumed by
`src/pcae/core/human_principal_registry.py:332` `_writer()` and the
(not-yet-written) `.1R.30` enrollment/bootstrap ceremony tool.

---

## 6. Scope discipline for this BLOCKED phase (phase prompt BLOCKED instructions)

- **No repair outside scope.** `hpac_foundation.py` was **not** modified. No
  production-writer path was added.
- **No contract modification.** `git diff e40d4ce1 HEAD -- docs/contracts` is
  empty. RHAMP-001 v1.0 is byte-identical to its `.1R.29` freeze. HPAC-001
  stays v2.1. `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`.
- **No `src/pcae` change.** `git diff e40d4ce1 HEAD -- src/pcae` is empty.
- **No protected approval UI, no real approval proof, no PRODUCTION
  `AuthenticatedHumanPrincipal`, no `_ELIGIBLE_MECHANISM_IDS` widening, no
  `verifier_kind` addition, no `require_real_assurance` production wiring, no
  FIDO2/CTAP code, no hardware access, no test file, no guard reconciliation.**
- **No N-16-6 / N-16-7 / Slice C / first external effect / execution
  enablement.** All remain exactly as at phase entry.
- **Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins; 0 capabilities — re-asserted at phase entry, byte-unchanged.
- **First external effect:** ABSENT — no `adapter.dispatch(` call site exists.

---

## 7. Carried findings

- **N-16-3** — CLOSED (carried).
- **N-16-4** — CLOSED (carried).
- **N-16-5** — CONTRACT PROFILE FROZEN (RHAMP-001 v1.0) / **IMPLEMENTATION
  PENDING — `.1R.30` BLOCKED**. NOT CLOSED.
- **N-16-6 / N-16-7** — OPEN, not begun; N-16-7 strictly last.
- **N-23-1** — INFO (carried unchanged).
- **N-23-2** — INFO / DEFERRED NORMALIZATION DEBT (carried unchanged).
- **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved.
  This finalization (task lifecycle, this document, `PROJECT_STATUS.md` /
  `CHANGELOG.md`, completion metadata / report) was authored and committed by
  the primary human-authorized operator for `.1R.30` through the governed
  `pcae` lifecycle only. No delegated worker committed, finalized, or pushed.

---

## 8. Recommended successor — repair / adjudication phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R` — HPAC-REQ-022/023 Production
Protected-Admin Writer Anchor: Architecture and Contract Adjudication**
(phase ID **recommended, NOT reserved**; requires its own separate explicit
human authorization).

Scope: adjudicate and freeze the concrete trust mechanism by which the
external deployment-owner protected administration principal (HPAC-REQ-023) is
recognised by PCAE and mints a `PRODUCTION` `HPACWriterCapability` — the
positive half of the anchor `hpac_foundation.py` deferred. Candidates to
evaluate against the HPAC-001 threat model (no new same-UID-agent path; no
repository / env / cwd / caller influence; fail-closed; offline; OS-neutral
macOS+Linux): a root-owned capability / installation descriptor under
`<HPAC_PROTECTED_ROOT>/.authority/`; a `sudo`/privilege-gated invocation
context check; an administrator-signed installation record verified against a
protected pinned key; OS keychain / keyring-held admin key. Decide whether
this is a new HPAC-001 MINOR (mechanism clarification within the frozen §7
policy) or fits entirely under existing contract semantics as a pure
implementation. Then `.1R.30` resumes from the adjudicated baseline (it does
**not** resume inside `.1R.30R`), followed by `.1R.31` (IV of `.1R.30`),
`.1R.32` (protected presentation + real-assurance wiring), `.1R.33` (IV +
mandatory real-CTAP2-hardware verification + N-16-5 closure).

Do not, in `.1R.30R`: implement the FIDO2 mechanism, the sidecar/counter
stores, the protected UI, or any approval path; touch N-16-6 / N-16-7 / Slice
C; implement or call the first external effect; enable execution.

---

## 9. Implementation verdict

```
N-16-5 REAL FIDO2 CREDENTIAL REGISTRY + AUTHENTICATION MECHANISM:
    NOT IMPLEMENTED — .1R.30 BLOCKED at scope item A (production registry
    writer path / HPAC-REQ-023 bootstrap-authority anchor)

RHAMP-001 v1.0:
    FROZEN, BYTE-UNCHANGED — implementation not begun for .1R.30 scope

REAL HUMAN AUTHENTICATION:      NOT IMPLEMENTED
REAL PROTECTED PRESENTATION:    NOT IMPLEMENTED
REAL APPROVAL PROOF:            NOT IMPLEMENTED
N-16-5:                         NOT CLOSED
Runtime:                        Observed / observe / unavailable
First external effect:          ABSENT
```

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
