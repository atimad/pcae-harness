# Phase 149O.20L.7O.2G.1 — HMIC Trust-Enrollment / Signing Target-Set Reconciliation

**Phase-entry commit:** `03c585b325fdbb7d880332ce42e83b55232ef979` (Phase 149O.20L.7O.2G: close governed task, transition to idle)

**Status:** Analysis/reconciliation only. No HMIC contract modification, no `hatp_mandatory_certification.py` modification, no production constant change, no digest repin, no certification, no activation, no real provisioning.

## Verdict

**HMIC TRUST-ENROLLMENT / SIGNING TARGET SET RECONCILED — EXACT SOURCE, CONTRACT-CONTENT, AND CONTRACT-VERSION MEMBERSHIP DERIVED**

Not "HMIC aligned." Not "HMIC certified." Not "HATP ready." Not "Trust Enrollment authorized." Not "Provisioning ready." No HMIC change occurred in this phase.

---

## 1. Charter and Finding

This phase exists because 149O.20L.7O.2G's primary target-set result contained a load-bearing internal inconsistency: §9.1 of 2G's report stated the required future implementation/content source set as **33** entries (30 current + only the 3 new Python source files), while §9.2/§10 of the *same report* recommended binding HPSE-001 and HHCE-001 for **both content and version**, mirroring the HBDC-001 precedent — an action that, if actually taken, adds 2 more entries to the content-bound set (the two new contract `.md` files), which §9.1's count never reflects.

**Finding identifier:** `B-149O.20L.7O.2G-1` — HMIC Target-Set / Contract-Content Binding Reconciliation Gap.

**Status entering this phase:** OPEN — BLOCKING FOR 2H.

This finding does not reopen BF-1, BF-2, B-149O.20L.7O.2F.3-1, or B-149O.20L.7O.2F.3-2 — those remain independently closed at their implementation boundaries (reconfirmed §8 below). This finding concerns HMIC identity construction only.

## 2. Primary Evidence Read Directly (This Phase)

- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001, current `main`) — HMIC-REQ-050, HMIC-REQ-051, HMIC-REQ-052, **HMIC-REQ-053**, HMIC-REQ-054, HMIC-REQ-067, HMIC-REQ-068, HMIC-REQ-069, read in full at their live line ranges (546–992).
- `src/pcae/core/hatp_mandatory_certification.py` (current `main`, 2130 lines) — `_FROZEN_SRC_PCAE_RELATIVE_FILES`, `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`, `_FROZEN_AUTHORITY_BEARING_FILES`, `_CONTRACT_IDENTITY_FILES`, `_CONTRACT_VERSIONS_REQUIRED_KEYS`, `derive_contract_versions` — read directly, not from 2G's summary.
- `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001 v1.1) — full header, §26, §44 (HPSE-REQ-073), §45.
- `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001 v1.1) — header.
- `docs/PHASE_149O_20D_1_HMIC_V1_2_HBDC_CONTENT_IDENTITY_BINDING_REPAIR.md` (the HBDC-001 precedent phase) — full defect reconstruction and repair rationale.
- `docs/PHASE_149O_20L_7K_HMIC_FROZEN_SOURCE_SCOPE_AMENDMENT_FOR_DEPLOYMENTBINDING_PRODUCER.md` (same-phase contract+production alignment precedent) — purpose/structure.
- `src/pcae/core/hatp_signing_ceremony.py`, `hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py` — `import pcae.*` statements re-verified directly against 2G's §5 AST-walk claims.
- `docs/PHASE_149O_20L_7O_2G_HATP_TRUST_ENROLLMENT_AND_SIGNING_HMIC_TRANSITIVE_AUTHORITY_SCOPE_ANALYSIS.md` — read as the artifact being reconciled, not as a source of un-reverified membership claims.

No membership claim below is taken from 2G's summary without independent re-derivation from the primary sources listed above.

## 3. Current HMIC Baseline (Independently Re-Derived)

### 3.1 Current source/content set — 30 entries (re-confirmed)

`_FROZEN_SRC_PCAE_RELATIVE_FILES` (23 entries, `src/pcae/`-relative) + `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (7 entries, repository-root-relative: 5 `docs/contracts/*.md` files + 2 `scripts/*.py` admin ceremony scripts) = 30, confirmed against the live `assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 30` invariant and against HMIC-REQ-050's own literal enumeration (contract lines 561–593) — byte-for-byte identical member lists in both locations.

### 3.2 Current contract-version set — 5 members (re-confirmed)

`_CONTRACT_IDENTITY_FILES`: `HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `HBDC-001` — confirmed against HMIC-REQ-067 (v1.2 text, contract line 959).

(Non-blocking, unrelated, unrepaired in this phase: `_CONTRACT_VERSIONS_REQUIRED_KEYS`, a separate 4-member constant used only by Wave A's `_require_contract_versions` schema validator, still lacks `HBDC-001` — a pre-existing drift 2G already correctly flagged as out of this scope. Confirmed still present, unchanged, not touched here.)

## 4. Two Contract-Binding Mechanisms — Explicitly Separated

| Mechanism | What participates | Governing requirement |
|---|---|---|
| Contract **content** binding | The contract file's raw bytes, via `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` → `_FROZEN_AUTHORITY_BEARING_FILES` → `implementation_scope_digest` | HMIC-REQ-050 (enumeration), HMIC-REQ-053 (explicit rule) |
| Contract **version** binding | The contract's declared `**Version:**` header string, via `_CONTRACT_IDENTITY_FILES` → `contract_versions` | HMIC-REQ-067 |

**Current per-contract table (independently re-derived):**

| Contract | Content-bound? | Version-bound? |
|---|---|---|
| HMRC-001 | Yes (#24) | Yes |
| HATP-001 | Yes (#25) | Yes |
| HSCE-001 | Yes (#26) | Yes |
| RAE-001 | Yes (#27) | Yes |
| HBDC-001 | Yes (#28, since 149O.20D.1) | Yes |
| HPSE-001 | **No** | **No** |
| HHCE-001 | **No** | **No** |

**Decisive fact, read directly from HMIC-REQ-053 (contract lines 822–837), not inferred:** *"As of the 149O.20D.1 repair, every `contract_versions` member (HMIC-REQ-067, five entries) receives both bindings uniformly — no `contract_versions` member is exempted from the digest binding."* This is a **current, load-bearing, textual rule of HMIC-001 itself**, not an analogy or a stylistic precedent. Every one of the five contracts currently in `contract_versions` is, without exception, also content-bound. There is no existing example anywhere in HMIC's current membership of a `contract_versions` member that is *not* also content-bound.

## 5. HBDC-001 Precedent — Independently Reconstructed

Read directly from `PHASE_149O_20D_1_HMIC_V1_2_HBDC_CONTENT_IDENTITY_BINDING_REPAIR.md`:

- 149O.20D (v1.1→v1.2) added `HBDC-001` to `contract_versions` (version-bound) but left its bytes outside `implementation_scope_digest` (content-unbound) — a **deliberate, disclosed** interim gap (HMIC-REQ-145, since closed).
- The defect: a same-version, content-only edit to `HBDC-001` (Contract ID and Version header both held constant) would leave `implementation_scope_digest` unchanged — a certification bound to the pre-mutation bytes would continue validating against the post-mutation bytes. Version-only binding cannot detect same-version semantic drift.
- 149O.20D.1 (v1.2, in-place widening) closed this by adding `HBDC-001`'s document to `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (24→25 total) and rewriting HMIC-REQ-053 to state the uniform, no-exemption rule quoted in §4 above.
- **The reasoning generalizes exactly, not by analogy but by the same failure mode:** HPSE-001/HHCE-001 govern authority-sensitive semantics (principal/signer identity binding, hardware-credential registration/revocation) that could be silently loosened in a same-version text edit exactly as HBDC-001's deployment rules could. Content binding is therefore independently justified for both, on the identical semantic-drift argument HBDC-001's own repair already proved — **and, per §4, is now also mechanically mandatory** the moment either contract is added to `contract_versions`, independent of the semantic argument.

## 6. HPSE-001 Requirement — Independently Re-Derived

HPSE-001 v1.1 governs `PrincipalRecord`/`SignerRecord` identity semantics (`principal_id`, `signer_key_id`, `provider_profile`), the cross-registry consistency invariant with `hardware-credentials.json`, lock ordering, and revocation model — all directly authority-sensitive to `hatp_principal_signer_admin.py` (the new writer this phase's sibling phase, 2G, already classified DIRECT AUTHORITY SOURCE) and to `hatp_bootstrap.py`/`hatp_signing_ceremony.py`'s consumption of that state.

HPSE-001 §44 (HPSE-REQ-073) itself names the future HMIC source-scope surfaces a later amendment "MUST include, at minimum" — and lists only **source/script files** (HHCE-001's writer+script, HPSE-001's own writer+script, already-bound provider files, already-bound `hatp_bootstrap.py`). It does **not** name the contract documents' own bytes as a required HMIC-REQ-052 closure-limb member — correctly, since HMIC-REQ-052 is a source call-graph closure rule (§16 below), not a contract-content rule. This is expected and does not contradict §4/§5's finding: contract-content binding is governed by HMIC-REQ-053, a separate requirement HPSE-001 has no occasion to name, because HPSE-001 (correctly) never claims to be a member of its own future `contract_versions` list — that decision belongs to the HMIC amendment phase, not to HPSE-001's own text.

If HPSE-001's bytes changed while its declared version stayed `v1.1`, no currently-planned mechanism except content binding would detect it — version-only binding would fail exactly as HBDC-001's did pre-repair.

**Classification: CONTENT + VERSION REQUIRED.**

## 7. HHCE-001 Requirement — Independently Re-Derived

HHCE-001 v1.1 governs `HardwareCredentialRecord` construction, public-key representation, provider-profile validation, registration/revocation semantics for `hardware-credentials.json` — directly authority-sensitive to `hatp_hardware_credential_admin.py` (the new writer 2G already classified DIRECT AUTHORITY SOURCE) and to `hatp_signing_ceremony.py`'s consumer-side lookup via the already-bound `hatp_hardware_credentials.py`.

Same reasoning as §6: a same-version content edit to HHCE-001 (e.g., quietly loosening provider-profile validation or revocation-check semantics) would not be caught by version-header comparison alone.

**Classification: CONTENT + VERSION REQUIRED.**

## 8. BF-1/BF-2 and B-...2F.3-1/-2 Status — Unchanged, Not Reopened

Independently reconfirmed via `git log`: zero commits to `hatp_signing_ceremony.py`, `hatp_fido2_provider.py`, `hatp_hardware_credential_admin.py`, or `hatp_principal_signer_admin.py` since 2G's own entry commit `021175c9`, and none since this phase's entry commit `03c585b3` either.

- **BF-1:** unaffected, remains CLOSED at implementation boundary.
- **BF-2:** unaffected, remains CLOSED at implementation boundary.
- **B-149O.20L.7O.2F.3-1:** unaffected, remains CLOSED at implementation boundary.
- **B-149O.20L.7O.2F.3-2:** unaffected, remains CLOSED at implementation boundary.

This phase's finding concerns HMIC identity-binding scope only, orthogonal to implementation correctness, exactly as 2G itself noted (§8 of its report).

## 9. Three Python Source Additions — Revalidated

Re-verified directly (not from 2G's summary) via `grep -n "^from pcae\|^import pcae"` against the three candidate files' live current content:

```
hatp_signing_ceremony.py:            agent, hatp_bootstrap, hatp_evidence_store,
                                      hatp_hardware_credentials, hatp_providers,
                                      hatp_signed_evidence, human_approval_trusted_provenance,
                                      paths, repository_identity, rollback_approval_evidence
hatp_hardware_credential_admin.py:   hatp_hardware_credentials, paths, provenance
hatp_principal_signer_admin.py:      hatp_bootstrap, hatp_deployment_binding_admin,
                                      hatp_hardware_credential_admin, hatp_hardware_credentials,
                                      hatp_providers, paths, provenance
```

Identical to 2G's §5 AST-walk result, byte-for-byte. Every import target other than `paths.py`/`provenance.py` is already a bound HMIC member (`hatp_bootstrap.py` #4, `hatp_evidence_store.py` #8, `hatp_hardware_credentials.py` #18, `hatp_providers.py` #15, `hatp_signed_evidence.py` #9, `human_approval_trusted_provenance.py` #5, `repository_identity.py` #6, `rollback_approval_evidence.py` #7, `hatp_deployment_binding_admin.py` #23). No candidate is reachable from an existing limb's anchor (`assess_hatp_mandatory_activation_readiness`, `validate_active_hatp_mandatory_independent_verification_certification`, `verify_class_b_deployment_conformance`, or the `DeploymentBinding` producer functions) — confirmed by 2G's corroborating evidence that `hatp_mandatory_cutover.py` only checks `hatp_signing_ceremony`'s *importability*, never calling into its functions.

**Confirmed: all three additions correct, none spurious, none missing.** No fourth candidate source file exists — `commands/hatp.py` remains correctly excluded (CLI dispatch only, zero independent authority computation, single zero-override call).

Checked against 2G's own instruction to confirm no existing limb already reaches these files: none does — this is precisely why a new closure limb (d) is required (§16 below), not merely a file-list realignment under existing limb text.

## 10. Excluded Leaf Dependencies — Revalidated

| Leaf | Symbol used | Call-graph reach | Absorbed by an already-bound source? | Disposition |
|---|---|---|---|---|
| `paths.py` | `HarnessPath` (frozen dataclass, `cwd()` + one `Path` join, zero branching) | Terminal — no further `pcae.*` imports | Already imported by the currently-bound `hatp_mandatory_certification.py` itself; established precedent (§49 of HMIC-001, `hatp_bootstrap.py` island) treats it as outside closure | **Exclusion correct, unchanged** |
| `provenance.py` | `append_provenance_event` (append-only audit-event writer) | → `agent.py` (bound #10), `git_status.py`, `tasks.py` | Already imported by the currently-bound `hatp_deployment_binding_admin.py` (#23); never gates/rejects/alters an authority decision | **Exclusion correct, unchanged** |
| `git_status.py` | current-branch-name read, for one audit-event field | Terminal | Reached only via excluded `provenance.py`; no accept/reject/sign/verify/publish role | **Exclusion correct, unchanged** |
| `tasks.py` | `find_latest_active_task` (glob `tasks/active/*.md`, parse latest), for one audit-event field | The *called symbol* is terminal; the *module* has large unrelated fan-out (`health.py`, `session.py`, `orchestration.py`, ...) never reached by this call path | Reached only via excluded `provenance.py`'s one narrow call; the unrelated fan-out is real but never exercised by any Trust-Enrollment/signing code path | **Exclusion correct, unchanged — call-graph unit of analysis is the specific symbol called, not whole-module import, matching 2G's own §6 methodological note** |

Re-evaluation confirms no hidden source-count issue: the transitive closure from all three new candidates terminates at exactly these four leaves, each independently excludable on the identical "already-imported-by-a-currently-bound-file, no decision logic reached" precedent this contract already uses elsewhere (`hatp_bootstrap.py` island, `pcae.core.paths` exclusion at limb (a)/(c)).

## 11. Exact Future Source/Content Set — Full Membership (Not a Delta)

### 11.1 Future `_FROZEN_SRC_PCAE_RELATIVE_FILES` — 26 entries (23 current + 3 added)

```
core/hatp_mandatory_cutover.py
core/hatp_ag_authority.py
core/hatp_rollback_consumption.py
core/hatp_bootstrap.py
core/human_approval_trusted_provenance.py
core/repository_identity.py
core/rollback_approval_evidence.py
core/hatp_evidence_store.py
core/hatp_signed_evidence.py
core/agent.py
commands/agent.py
cli.py
core/permission_broker.py
core/permission_broker_foundation.py
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py
core/hatp_mandatory_certification.py
core/hatp_class_b_topology_verifier.py
core/hatp_environment_lock_verifier.py
core/hatp_class_b_conformance.py
core/hatp_deployment_binding_admin.py
core/hatp_signing_ceremony.py                    <- NEW
core/hatp_hardware_credential_admin.py            <- NEW
core/hatp_principal_signer_admin.py               <- NEW
```

### 11.2 Future `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` — 9 entries (7 current + 2 added)

```
docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                  (HBDC-001)
docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md         (HPSE-001)  <- NEW
docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md      (HHCE-001)  <- NEW
scripts/hatp_certification_admin.py
scripts/hatp_deployment_binding_admin.py
```

No standalone `scripts/`-level ceremony callers exist yet for `hatp_hardware_credential_admin.py`/`hatp_principal_signer_admin.py` (confirmed: `ls scripts/` contains only `hatp_certification_admin.py` and `hatp_deployment_binding_admin.py`) — 2G's own §4 finding that these two writers currently have "no CLI wrapper ... invoked directly by test/administrative callers" is reconfirmed, so no third/fourth new repository-root-relative script entry is added at this time; only the two source modules themselves (§11.1) and the two contract documents (§9.2/above) are added.

### 11.3 Future `_FROZEN_AUTHORITY_BEARING_FILES` — 35 entries total

`26 (src/pcae/-relative) + 9 (repository-root-relative) = 35`.

- Current count: **30**
- Future count: **35**
- **Delta: +5** (+3 source, +2 contract-content)

**This is the reconciliation result: the answer is 35, not 33.** 2G's §9.1 arithmetic captured only the 3 Python source additions and omitted the 2 contract-content additions that 2G's own §9.2/§10 already concluded were required — an internal inconsistency between 2G's own sections, not a disagreement between 2G and this phase's independent derivation. Both this phase and 2G agree, independently, that HPSE-001/HHCE-001 require content binding; only the total-count arithmetic in 2G's §9.1 failed to reflect that conclusion. §4 above additionally shows this is not merely 2G's own recommendation but a **mechanical consequence of HMIC-REQ-053's existing, current text** ("no `contract_versions` member is exempted from the digest binding") the moment HPSE-001/HHCE-001 are added to `contract_versions` at all.

## 12. Exact Future Contract-Version Set

### 12.1 Future `_CONTRACT_IDENTITY_FILES` — 7 members (5 current + 2 added)

| Contract ID | Canonical path | Current version |
|---|---|---|
| HMRC-001 | `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` | (dynamic, current live header) |
| HATP-001 | `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` | (dynamic, current live header) |
| HSCE-001 | `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` | v1.3 (dynamic re-read; already correctly current per 2G §3.2) |
| RAE-001 | `docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` | (dynamic, current live header) |
| HBDC-001 | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` | v1.2 |
| HPSE-001 | `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` | **v1.1** (confirmed live: `**Contract:** HPSE-001` / `**Version:** 1.1`) |
| HHCE-001 | `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` | **v1.1** (confirmed live: `**Contract:** HHCE-001` / `**Version:** 1.1`) |

Both new files' `**Contract:**`/`**Version:**` header lines were read directly and match the exact regex grammar `derive_contract_versions` already parses for the other five (`_CONTRACT_ID_HEADER_RE`/`_CONTRACT_VERSION_HEADER_RE`, allowing both `**Contract ID:**` and `**Contract:**` label spellings).

- Current member count: **5**
- Future member count: **7**
- **Delta: +2** (HPSE-001, HHCE-001) — this figure was already correct in 2G's §9.2 and is reconfirmed unchanged by this phase.

## 13. HMIC-REQ-050 Consequence

Future required wording/structure (not implemented in this phase — analysis only):

- Total frozen-file count changes from **thirty** to **thirty-five**.
- New literal entries (in the presentation order §11.1/§11.2 use, mirroring existing addition-order convention — new source entries appended after the current last source entry, new contract entries appended after `HBDC-001` and before the two `scripts/` entries):
  - `core/hatp_signing_ceremony.py`
  - `core/hatp_hardware_credential_admin.py`
  - `core/hatp_principal_signer_admin.py`
  - `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001)
  - `docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md` (HHCE-001)
- Contract-content files remain correctly presented in the repository-root-relative section (§11.2) — they are not, and must not become, `src/pcae/`-relative entries; this matches every existing contract entry's placement.
- Every other normative section that names the current count/membership must also change: the amendment-history prose in HMIC-REQ-050 itself (which currently narrates v1.1→v1.4's additions and would need a new "§57" or equivalent narrating this widening), HMIC-REQ-052's own limb-derivation union list (§ "This enumeration is derived as the union of..." — would need a new clause (g) naming this phase's own fresh AST walk), and HMIC-REQ-053's "five contract files" language (contract line 823: "The five contract files' byte contents..." — must become "seven").

## 14. HMIC-REQ-052 Limb (d) Consequence

- **Anchor function:** `production_sign_rollback_evidence` (`hatp_signing_ceremony.py`) — mirrors limb (a)'s single-entry-point call-graph anchor construction.
- **Anchor module (non-reachability, second anchor):** the Trust-Enrollment writer functions in `hatp_hardware_credential_admin.py` and `hatp_principal_signer_admin.py` (their registration/revocation mutating operations) — mirrors limb (c)'s third-anchor construction for `hatp_deployment_binding_admin.py`: these writer functions are *not* reachable from `production_sign_rollback_evidence`'s own call graph (a separate write path), but their write output (`HardwareCredentialRecord`/`PrincipalRecord`/`SignerRecord` state) is exactly what the signing ceremony's consumer-side lookups read.
- **Transitive authority dependency rule:** every file reachable from either anchor, transitively, that can change: hardware-credential registry state; principal/signer identity binding; provider-profile validation at registration time; or signing-time signer/credential resolution — the identical dual-anchor (reachability + non-reachability producer) shape limb (b)/(c) already establish, no new mechanism.
- **Expected newly captured sources:** exactly the three files in §11.1's `<- NEW` rows — confirmed by §9's fresh re-verification, nothing more (the four leaves in §10 remain excluded under the identical semantic test).
- **Relationship to contracts:** limb (d) governs *source* closure only (HMIC-REQ-052); it does not itself bind HPSE-001/HHCE-001's contract bytes — that is HMIC-REQ-050/053's separate concern (§16 below), reached independently via the `contract_versions` widening at §12, not via limb (d)'s call-graph logic.

## 15. Self-Binding / Digest Transition Analysis

`hatp_mandatory_certification.py` is itself already a frozen member (#19, since v1.1, W-1's closure). Widening its own `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` constants necessarily changes this file's own bytes, and therefore the digest it itself computes at the next validation/certification cycle. This is not a new problem: the identical self-referential pattern already existed at v1.3 (149O.20K) and v1.4 (149O.20L.7K), both of which widened this same module's own frozen tuples in the same phase as the contract amendment, with no reported circularity — `derive_implementation_scope_digest` always reads the file's bytes **at digest-computation time**, never a value cached from before the edit, so there is no stale-vs-fresh ambiguity: any certification computed after the edit reflects the edited bytes; any certification computed before does not, and correctly fails to match afterward (that mismatch is the intended `IMPLEMENTATION_MISMATCH` behavior, not a defect). **No transition-order problem found. Not Blocking for 2H.**

## 16. Contract Content Is Not a Closure-Limb Source

HMIC-REQ-052's closure-limb logic (limbs (a)/(b)/(c), and the future (d)) identifies **production source** — Python files reachable from a named entry point's call graph, or non-reachable producer-writer anchors of the same kind. Contract documents are never described by, or added under, this rule; HMIC-REQ-050's own text (line 558) states root-relative paths include "contract documents under `docs/contracts/`" as a *separate, explicitly named category*, and HMIC-REQ-053 is the distinct requirement that actually binds their bytes. §11.1 (source) and §11.2 (content, including the 2 new contract documents) are correctly kept in their own distinct buckets in this report for exactly this reason — the architecture already separates them; this phase's reconciliation does not blur that separation, and 2H must not describe the two new contract `.md` files as call-graph dependencies of limb (d).

## 17. Is One 2H Phase Still Appropriate?

Re-evaluated after reconciliation, against the same four options 2G considered:

- **Option A** (one additive HMIC evolution: new limb (d) + widened HMIC-REQ-050 enumeration to the *correct* 35-entry set + widened `contract_versions` to 7 + same-phase production-constant alignment, per the 149O.20L.7K precedent) — **still correct.** Nothing in this reconciliation changes the *shape* of the needed amendment, only its exact arithmetic (35, not 33) and the explicit inclusion of the 2 contract-content additions alongside the 3 source additions the amendment must make.
- **Option B** (separate Class-B vs. Trust-Enrollment evolutions) — moot, unchanged from 2G's own finding; nothing pending on the Class-B side.
- **Option C** (a further prerequisite contract clarification needed before drafting) — not supported: HMIC-REQ-053's uniform-coverage rule (§4) already provides the exact, unambiguous instruction ("every `contract_versions` member receives both bindings") 2H needs; no further contract-text ambiguity blocks drafting.
- **Option D** (2G materially wrong, broader re-analysis needed) — not supported: 2G's source-addition analysis (§9 above), leaf-exclusion analysis (§10), and content/version-binding *recommendation* (§9.2/§10 of 2G's own report) were all independently re-confirmed correct in this phase; only 2G's own §9.1 total-count arithmetic needed correction to match its own §9.2/§10 conclusion.

**Selected: Option A, using the corrected 35-entry / 9-repository-root-relative / 26-src-relative / 7-contract-version target set derived in §11–§12 above**, not 2G's uncorrected 33.

## 18. Production Alignment Precedent — Independently Reviewed

`PHASE_149O_20L_7K_...md` amended HMIC-REQ-052/HMIC-REQ-050 (limb (c)'s third anchor, 28→30 entries) and updated `hatp_mandatory_certification.py`'s production constants **in the same phase**, unlike 149O.20D→149O.20D.1's split contract-then-repair sequencing. Same-phase alignment was safe there because: (1) the added source/contract members were already fully built and stable (no concurrent implementation change), (2) the module doing the self-referential update (`hatp_mandatory_certification.py`) computes its digest fresh at read time (§15 above — no caching hazard), and (3) no certification existed on this host to invalidate mid-flight. All three conditions hold identically here: `hatp_signing_ceremony.py`/`hatp_hardware_credential_admin.py`/`hatp_principal_signer_admin.py` and HPSE-001/HHCE-001 are all already built/frozen and stable (2G confirmed zero commits since 2F.5), the self-binding mechanism is unchanged, and 2F.5/2G both already confirmed no certification exists anywhere on this host. **The 149O.20L.7K same-phase pattern applies safely to 2H; no special sequencing issue found.**

## 19. HMIC Version Consequence

The future change is a strict superset addition (new closure limb, widened enumeration, widened `contract_versions`) with no removal and no semantic narrowing of any existing binding — structurally identical in kind to the v1.1 (limb (b)), v1.3 (limb (c) first anchor), and v1.4 (limb (c) third anchor) amendments, each of which was a minor version increment. **HMIC-001 v1.4 → v1.5 is the correct version consequence**, consistent with this contract's own established minor-version-per-additive-amendment convention; nothing in this reconciliation surfaces a reason to deviate to a major version bump (no existing binding is weakened, removed, or redefined) or to a repair-style in-place same-version edit (this is new closure-surface addition, not a defect repair to already-frozen text).

## 20. Class-B / CBV Status — Confirmed Unchanged

- Class-B topology verifier, environment-lock verifier, and Class-B conformance verifier: all three remain bound (#20–#22 current / unrenumbered-but-preserved in the future 26-entry `src/pcae/`-relative list, §11.1). Unaffected by this reconciliation — confirmed via `git log` showing the last commit to all three predates and is unrelated to 2G/this phase.
- `DeploymentBinding` admin (producer + script): remains bound (#23/#30 current, preserved in §11.1/§11.2). Unaffected.
- **CBV-S1:** unaffected — the Class-B surface's own closure (limb (c)) is already complete; this reconciliation concerns the separate Trust-Enrollment surface only. Not reopened.
- **CBV-S10:** remains **OPEN**, out of scope, untouched by this phase.

## 21. Finding Disposition

`B-149O.20L.7O.2G-1` (HMIC Target-Set / Contract-Content Binding Reconciliation Gap):

**RECONCILED — EXACT TARGET SET DERIVED — INDEPENDENT IMPLEMENTATION/CONTRACT EVOLUTION PENDING — NOT CLOSED AT HMIC ALIGNMENT BOUNDARY.**

The exact future membership (35 content-bound files, 7 contract-version members) is now uniquely and mechanically derived from HMIC-REQ-053's own current text plus 2G's independently-reconfirmed source/leaf analysis. This finding remains open until a future contract-evolution phase (149O.20L.7O.2H) actually amends HMIC-001 and aligns production constants to this exact target — this phase performs no such amendment.

## 22. Verification Tests / Mechanical Evidence

`tests/test_phase_149o_20l_7o_2g_1_hmic_target_set_reconciliation.py` mechanically asserts (production constants untouched):

- Current tuple lengths: 23 / 7 / 30 (source / repo-root / total), 5 (`_CONTRACT_IDENTITY_FILES`), exactly matching live `hatp_mandatory_certification.py`.
- Exact current members of all four constants, compared entry-for-entry against the live production constants (byte-identical strings).
- Exact proposed 3 source additions exist on disk and are importable Python modules.
- Exact proposed 2 contract-content additions (HPSE-001, HHCE-001 `.md` files) exist on disk, and their live `**Contract:**`/`**Version:**` headers parse under the exact `derive_contract_versions` regex grammar already in production, yielding `("HPSE-001", "1.1")` / `("HHCE-001", "1.1")`.
- The proposed future 35-entry `_FROZEN_AUTHORITY_BEARING_FILES` (26 src + 9 root) is deterministic, duplicate-free, and every entry corresponds to a file that exists on disk.
- The proposed future 7-member `_CONTRACT_IDENTITY_FILES` is deterministic, duplicate-free.
- **A test that would fail if the future target were accidentally constructed as 33** (2G's uncorrected figure): asserts `len(proposed_future_frozen_set) == 35`, not `33`, and separately asserts `len(proposed_future_frozen_set) - len(current_frozen_set) == 5`, not `3`.
- No production `_FROZEN_*`/`_CONTRACT_IDENTITY_FILES` constant is imported for mutation — only read, for baseline comparison.

## 23. Regression

No production or contract file was modified by this phase.

**Focused new test module:** `tests/test_phase_149o_20l_7o_2g_1_hmic_target_set_reconciliation.py` — 12/12 passed.

**Fast Green — exact fixed-vs-current node-ID diff:** an isolated disposable `git worktree` was checked out at this phase's entry commit (`03c585b3`) and `python -m pytest -m "fast_green" -n auto -ra -q` was run there, then again on current source (post-2G.1, doc/test-only changes), using the identical governed interpreter and marker selection both times:

- **Fixed (pre-2G.1, `03c585b3`):** 305 failed / 8036 passed / 7 skipped / 12 errors.
- **Current (post-2G.1):** 306 failed / 8035 passed / 7 skipped / 12 errors.
- **Exact FAILED-node-ID diff:** one current-only node, `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`; zero fixed-only nodes (nothing newly resolved, nothing new stayed broken from before).
- **ERROR-node-ID set:** unchanged (12 in both trees).

**Disposition of the one current-only failure:** re-run in isolation immediately after the two full parallel `-n auto` fast_green invocations completed, it failed once at 15.14s against its own 15-second `pcae shell-gate audit verify` CLI subprocess timeout, then passed on immediate re-run at 12.61s once host load settled — the identical system-load-induced timing-flake pattern 2G's own report (§16.1) already diagnosed for the same test under the same concurrent-parallel-run condition. `tests/test_shell_gate.py` is untouched by this phase (this phase edited only this document, its own test file, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, and task/report artifacts), and the test's production target (`pcae shell-gate audit verify`) has no relationship to HATP/HMIC/Trust-Enrollment/target-set reconciliation. **Zero durable regressions attributable to this phase's changes.**

(The 305/8036/7/12 vs. 2G's own cited 304/8160/4/9 fixed-baseline figures differ from 2G's report — collection-count drift consistent with intervening phases' own test-suite growth/pruning between 2G's entry commit and this phase's entry commit `03c585b3`, not a regression introduced by this phase; the relevant comparison for this phase's own no-regression claim is the fixed-vs-current diff run in this phase, both at the identical `03c585b3` lineage, not a cross-phase absolute-count comparison.)

## 24. No-Go — Confirmed

- No HMIC contract modified — `git diff` for this phase touches only this document, its test file, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, and task/report artifacts.
- No `hatp_mandatory_certification.py` byte changed.
- No `_FROZEN_*`/`_CONTRACT_IDENTITY_FILES` production constant changed.
- No implementation digest repinned.
- No certification created or activated.
- No HATP activated.
- No real hardware provisioned; no real Principal/Signer enrolled; no real `DeploymentBinding` created.
- No mutation of `hac-dell` or the Protected Root.
- No Permission Broker / runtime capability change.
- No PIV implementation.
- CBV-S10 not wired.
- Stream B not touched.

## 25. Next Phase

**149O.20L.7O.2H — HMIC-001 v1.4→v1.5 Contract Evolution: Trust-Enrollment/Signing Closure Limb (d).** Using the exact reconciled target set from this phase: add closure limb (d) to HMIC-REQ-052 (§14); widen HMIC-REQ-050's enumeration to the corrected **35-entry** set (§11); widen `contract_versions` to the **7-member** set (§12, content- and version-bind HPSE-001/HHCE-001 per HMIC-REQ-053's existing uniform-coverage rule, §4); update the production `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` constants in the same phase as the contract amendment, per the 149O.20L.7K precedent (§18). Followed by an independent verification phase, not started, not authorized. **Stop after this phase (2G.1); do not begin 2H.**
