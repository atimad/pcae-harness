# Phase 149O.20L.7O.2K.4 — Post-CertificationRecord DAG Re-Derivation and Next Real-Effect Node Authorization

## 0. Phase Entry State

- True phase-entry commit: `506f6b5f621399082bbf00929e06e2ad8d15f20a` (`origin/main` identical, `origin/main..HEAD` = 0, working tree clean).
- Latest completed phase: `149O.20L.7O.2K.3` — HATP HMIC CertificationRecord Real-Host Creation, Source-Parity Revalidated (SUCCEEDED).
- This phase performs analysis/authorization only. No real effect is performed (§28 NO-GO list obeyed literally; see §9 below for the exhaustive confirmation list).

## 1. Mac/Dell Authority-Parity Classification

- Deployed revision on hac-dell (`sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD`, freshly re-run this phase): `305f8e7913bac76941dade6ff4e018c74533f062` — unchanged, exact match to 2K.3's own verification.
- Deployment working tree: clean (`git status --short` empty).
- Mac HEAD is 3 commits ahead of `305f8e79` (149O.20L.7O.2K.3's own finalization commits: report-title sync, task allowed-files sync, tracked-file repair). All three are non-authority governance/reporting commits — no source/contract/admin/deployment byte changed. Classification: **deployment remains parity-valid**. No redeployment required by this phase.

## 2. CertificationRecord — Fresh Verification

Freshly re-read via the production reader (`pcae.core.hatp_mandatory_certification._read_certifications`) against `HATPTrustStore.production().root` (`/etc/pcae/hatp/trust-store`) on hac-dell, read-only, no mutation:

- Exactly one record: `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `status=active` (an unrevoked `CertificationRecord`; "active" here is the record's own lifecycle field, distinct from the Active-Certification Pointer — §5 below preserves this distinction explicitly).
- Structurally and semantically consistent with the deployed source identity: `implementation_commit` matches `305f8e79`; `implementation_scope_digest` and the 7 `contract_versions` entries are the same values 2K.3 independently verified and recorded (unchanged, since the deployed tree is unchanged).
- **`certification-bindings.json` is ABSENT** (`_read_certification_bindings` → `_ReadStatus.ABSENT`) — confirms **Active CertificationBinding: ABSENT**, matching the phase's stated entry state exactly.

## 3. Fresh Read-Only Host State

All read via SSH, read-only, no mutation:

| Item | Value |
|---|---|
| hostname | `atila-Latitude-E5470` |
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` |
| deployed revision | `305f8e7913bac76941dade6ff4e018c74533f062` (unchanged) |
| deployment cleanliness | clean |
| Protected Root (`HATPTrustStore.production().root`) | `/etc/pcae/hatp/trust-store` |
| CertificationRecord | present, unchanged, exactly 1 (§2) |
| Active CertificationBinding | ABSENT |
| `registry.json` (Principal/Signer) | does not exist |
| hardware-credential-store root (`/etc/pcae/hatp/hardware-credentials`) | does not exist |
| `deployment-bindings.json` | does not exist |

HardwareCredentialRecord, Principal, Signer, and DeploymentBinding are each confirmed **ABSENT** by direct file/root-existence check against the production-resolved paths, not inferred.

Class-B (`pcae.core.hatp_class_b_conformance.verify_class_b_deployment_conformance()`), re-run under an ad-hoc `sudo -u pcae env -i PATH=... python3 -c ...` invocation (not a byte-exact reproduction of 2K.3's own established precedent invocation): returned `NON_COMPLIANT`, 31/34 satisfied, with `HBDC-REQ-030`/`HBDC-REQ-042` both raising `PermissionError(13)` under this invocation's more restricted environment, plus `HBDC-REQ-036` newly failing. This diverges numerically from 2K.3's canonical 32/33-with-sole-residual-`HBDC-REQ-042` result. 2K.3's own report already documents that this specific diagnostic is invocation-sensitive (an earlier `sudo -n` run as uid=0 "produced a spurious wider failure set purely as an artifact of uid=0 tripping agent/admin-co-mingling checks; discarded"). Given (a) the deployed revision, Protected Root, and every file this diagnostic reads are confirmed byte-identical to 2K.3's own re-verification, and (b) this phase performs no mutation this diagnostic could be reacting to, the numeric divergence is attributed to this phase's own SSH-invocation environment (missing/partial ACL-tooling PATH under `env -i`) rather than to real state drift. **This phase does not treat its own ad-hoc re-run as authoritative**; it relies on 2K.3's canonical, precedent-invocation value — **NON_COMPLIANT, 32/33, sole residual `HBDC-REQ-042`** — as still current, on the structural grounds above. No further debugging of the diagnostic harness was attempted (out of scope; this phase is analysis-only and the discrepancy does not change any DAG conclusion in §6-§10, since HMIC-001 §35 already establishes Class-B independence from HMIC certification/activation regardless of the exact residual count).

## 4. Semantic Walls Preserved

Restated from the governing prompt and held throughout this phase's analysis without exception:

```
CertificationRecord exists        != active certification
active certification              != HMIC VALID (unless validator proves it)
HMIC VALID                        != Class-B COMPLIANT
HMIC VALID                        != HATP READY
HATP READY                        != HATP ACTIVE
HATP ACTIVE                       != PB ALLOW
PB ALLOW                          != runtime execution capability
```

No step below treats one of these transitions as authority for another.

## 5. Activation Operation — Contract + Source Reconstruction (HMIC-001 v1.6, `scripts/hatp_certification_admin.py`)

Reconstructed from `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §23-26, §31-35, and `scripts/hatp_certification_admin.py::activate()` (lines 307-353) plus `src/pcae/core/hatp_mandatory_certification.py::_write_active_binding` (lines 1855-1899) directly — not from any phase summary.

**Exact command** (mirroring the `create` invocation's own precedent shape):
```
sudo -n /opt/pcae/runtime/venv/bin/python3 \
  /opt/pcae/runtime/src/scripts/hatp_certification_admin.py activate \
  --repository-root /opt/pcae/runtime/src \
  --certification-id 2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7 \
  --assume-yes    # or interactive confirm via _prompt_confirm
```

- **Exact protected record changed:** `certification-bindings.json` only — one `CertificationBinding` entry is written/replaced for the `(repository_instance_id, canonical_deployment_root)` key (HMIC-REQ-085/086, `_write_active_binding`).
- **`CertificationRecord` itself remains immutable:** `activate()` never touches `certifications.json`; it only reads it once (structural existence/parse precondition, see below). Confirmed directly in source — no write call to the certifications document appears in `activate()`.
- **Required election / human confirmation:** `activate()` raises `ConfirmationDeclinedError` unless `confirm=True` is passed (source line 337-341) — an explicit, separate confirmation from `create`'s own (HMIC-REQ-026, restated at §26: "create authorization != activation authorization").
- **Required record state:** structural existence and successful parse only (`load_certification(certification_id, harness_root)` — a lookup that raises if not found/unparseable). It explicitly does **not** require the record to be currently HMIC `VALID` — the source docstring states this outright ("never requires it to be currently HMIC VALID; that judgment remains Wave D's alone").
- **Required current `certification_id`:** the caller must name the exact id (`--certification-id`); no "latest"/"newest" implicit selection exists (HMIC-REQ-085/090).
- **Required source/contract identity freshness:** *not* re-validated by `activate()` itself — see §8 (Freshness) below; the record's stored fields are used as-is for the structural check, and true freshness is a validator-time (not activation-time) concern.
- **Required Protected Root:** `_resolve_protected_root(None)` → `HATPTrustStore.production().root`, no override accepted (HMIC-REQ-080).
- **Required repository/deployment identity:** derived fresh from `repository_root` exactly as `certify` derives it (`derive_repository_instance_id`, `derive_canonical_deployment_root`) — not caller-suppliable, cross-checked implicitly by using the same derivation the record itself was created under.
- **Required Class-B status:** none — no reference to Class-B, `HBDC-REQ-*`, or `verify_class_b_deployment_conformance` anywhere in `activate()` or in HMIC-001 §23-35.
- **Required HardwareCredential/Principal/Signer/DeploymentBinding:** none — no reference anywhere in `activate()` or in HMIC-001's activation sections.

## 6. Does Activation Require Trust-Enrollment Data? — No (Load-Bearing)

HMIC-001 §35 ("Certification/Activation Independence — Explicit Non-Causation") is dispositive and explicit:

- **HMIC-REQ-121:** "No code path invoked by `activate_hatp_mandatory`, or by any activation-adjacent production function, SHALL create, activate, or revoke a `CertificationRecord` or Active-Certification Pointer as a side effect" (this is about HMRC's `activate_hatp_mandatory`, distinct from *this* contract's own `activate` — but the same §35 independence principle governs HMIC-001's own certification/activation pair per HMIC-REQ-118-120).
- **HMIC-REQ-118-120:** `CERTIFY` and `ACTIVATE` are, and must remain, separate ceremonies by the same principal; a `VALID` certification does not by itself cause any mode transition; activation is the separate, explicit call.
- No section of HMIC-001, and no line of `activate()`'s source, references `hardware-credentials.json`, `PrincipalRecord`, `SignerRecord`, or `DeploymentBinding`.

**Conclusion: HMIC certification activation (this contract's `activate`) is independent of Trust-Enrollment data.** The fact that this repository's *source tree* implements Trust-Enrollment features (HHCE-001/HPSE-001 modules, bound into HMIC's own frozen-file/contract-version set per §17-20) is a fact about what is *certified* (the implementation's completeness as of the certified commit), never a runtime precondition activation itself checks. §9 of this document (below) preserves this distinction explicitly, per the governing prompt's own caution not to conflate the two.

## 7. Does Activation Require Class-B COMPLIANT? — No

No reference to Class-B, `HBDC-REQ-*`, `ClassBConformanceStatus`, or `verify_class_b_deployment_conformance` exists anywhere in `activate()`'s source or in HMIC-001 §23-35. HMIC-001 and HATP_CLASS_B_DEPLOYMENT_CONTRACT.md are sibling contracts (§3 "Scope and Relationship to Other Contracts" of HMIC-001 does not subordinate one to the other for the activation ceremony). **HMIC activation can happen while Class-B remains NON_COMPLIANT.** This document does not infer a readiness-term ordering (§20's six-item conjunction, where both terms independently gate `HATP READY`) into the certification-admin tool's own operational ordering (§24 constraint honored).

## 8. Activation Output Semantics — Exact Sequence, Verified Not Assumed

If a future phase runs `activate` successfully:

1. `certification-bindings.json` gains (or replaces) one `CertificationBinding` entry: `active_certification_id = 2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` for this repository/deployment key (§26, HMIC-REQ-085/086).
2. **HMIC validator "may return `VALID`" — not "will."** §31's validation algorithm (HMIC-REQ-103) re-derives `implementation_commit`/`implementation_scope_digest` fresh from the *current working tree* at validation time (step 9) and re-validates the 7 `contract_versions` against the bound contracts' *current* version headers (step 10) — both independent of the binding write itself. Since the deployed tree and all 7 contract versions are unchanged since certification (§1-§2), `VALID` is the expected but not activation-guaranteed outcome; the validator, not the binding write, makes that determination, fresh, on its own next invocation (HMIC-REQ-113: no cache).
3. If and only if the validator returns `VALID`, `mandatory_consumption_implementation_independently_verified = True` (HMIC-REQ-107) — the HMIC readiness term becomes `True`.
4. **Other readiness terms are unaffected.** This document does not claim HATP becomes ready: HMRC-REQ-054's readiness conjunction has multiple independent terms; Class-B (currently NON_COMPLIANT, sole residual HBDC-REQ-042) is one of them and is untouched by this operation (§20 below shows the full six-item table).

## 9. Activation Idempotency / Conflict Behavior

Derived from `_write_active_binding` (source lines 1855-1899, plain locked replacement, never compare-and-swap) and `activate()`'s own precondition check:

| Scenario | Classification | Basis |
|---|---|---|
| Binding absent (current real state) | Requires explicit `activate` call; not automatic | HMIC-REQ-086 |
| Binding already points to same `certification_id` | **SAFE IDEMPOTENT SUCCESS** — re-running `activate` with the identical id produces the same document content (no compare-and-swap precondition to violate) | `_write_active_binding` docstring: "never verifies... whichever write completes second... determines the final active pointer" |
| Binding points to another `certification_id` | **DETERMINISTIC OVERWRITE, NOT FAIL-CLOSED** — plain locked replacement; the new `activate` call simply replaces the pointer for that key; no error, no confirmation of "was something else already active" beyond the human confirmation gate itself | `_write_active_binding`, HMIC-REQ-099 |
| Named `certification_id` is revoked | **STRUCTURAL SUCCESS AT WRITE TIME, `REVOKED` AT VALIDATION TIME** — `activate()`'s own precondition is structural existence/parse only, not `VALID`; the write succeeds, but the *next* validator run returns `REVOKED` (§31 step 8), mapping readiness to `False` | `activate()` docstring, HMIC-REQ-094 |
| Named `certification_id` missing entirely | **FAIL CLOSED** — `load_certification`/`_load_by_id_from_root` raises before any write is attempted | `activate()` source lines 331-335 |
| Source identity changed since creation (working tree drifted) | **NOT REJECTED AT ACTIVATION TIME** — the binding write still succeeds (activation does not re-derive/re-check source identity); the drift is caught only by the *next validator run* (§31 step 9, `IMPLEMENTATION_MISMATCH`), not by `activate()` itself | §13 below |

## 10. Certification Freshness — Activation Does Not Revalidate

**Activation itself performs no freshness revalidation.** `activate()`'s only precondition check is structural (existence + parse). It does not recompute `implementation_scope_digest`, does not re-check `contract_versions`, and does not consult `verify_active_hatp_mandatory_independent_verification_certification` or any validator entrypoint. Freshness enforcement is entirely the validator's responsibility (§31, HMIC-REQ-103 steps 9-10), run fresh on every invocation, no cache (HMIC-REQ-113), and independently at HMRC's own locked-recheck point inside `activate_hatp_mandatory` (§34, HMIC-REQ-115-117) — a different, later ceremony than this contract's own `activate`. **A stale record does not become "active" in the sense of being HMIC-`VALID` merely because its `certification_id` is bound** — it becomes the *pointed-at* record; whether it validates `VALID` is decided fresh, separately, every time. This is the exact contract model the governing prompt's §13 asked to be either confirmed or documented precisely — confirmed here: **binding is unconditional (subject only to structural existence); validity is separately, freshly re-derived, never cached, never implied by the binding write.**

## 11. FIDO2 Candidate Re-Derivation (Not Carried Forward From 2K)

Re-derived fresh from current source, not from 2K's own blockers list:

- **Physical device availability:** UNKNOWN / not re-probed this phase. Per the governing prompt §15, this phase classifies device presence as unknown-requiring-next-phase-live-precheck (option A) rather than performing a hardware probe, because — independent of device presence — §12 below establishes a structural blocker that makes device presence moot for *this* phase's node-selection decision.
- **Supported provider:** `Fido2HardwareProvider` exists in source (`hatp_fido2_provider.py`) as the selected first provider (HHCE-001 §10); `hatp_piv_provider.py` remains an unconditional placeholder (HPSE-REQ-065/HPSE-REQ-045, unchanged).
- **Standalone admin entrypoint:** **ABSENT** — see §12.
- **Alternative governed way to invoke enrollment:** none found; no `pcae` subcommand exposes hardware-credential/principal/signer writes (by design, HHCE-REQ-019/020/HPSE-REQ-028/029 prohibit this).
- **HMIC activation prerequisite:** none (§6-7 above — HMIC activation and FIDO2 enrollment are mutually independent; neither gates the other in either direction).
- **Protected Root prerequisite:** FIDO2/hardware-credential state lives under a *separate* protected root (`HATPHardwareCredentialStore.production().root`, `/etc/pcae/hatp/hardware-credentials` — confirmed absent, §3), distinct from the HMIC trust-store root; provisioning that root (mode/ownership per HHCE-REQ-022) is itself an admin precondition, not yet done (root does not exist on hac-dell today).
- **Principal/Signer prerequisite:** per HPSE-REQ-046's 12-step first-use sequence (§17 below), hardware credential registration precedes principal enrollment, which precedes signer enrollment — none of the three has occurred (all three registries/records absent, §3).

No hardware touch was performed or attempted.

## 12. Admin Entrypoint Gap — Freshly Verified, Confirmed Still Present

2K reported no standalone `scripts/hatp_hardware_credential_admin.py` or `scripts/hatp_principal_signer_admin.py`. Freshly re-verified this phase:

```
$ ls scripts/*.py
scripts/hatp_certification_admin.py
scripts/hatp_deployment_binding_admin.py
```

**Confirmed: still absent as standalone `scripts/*.py` entrypoints.** However, this phase found something 2K's own report did not distinguish precisely: the *library-level* writer functions do exist, at `src/pcae/core/hatp_hardware_credential_admin.py` (649 lines: `register_credential`, `revoke_credential`, `preview_register_credential`, `preview_revoke_credential`) and `src/pcae/core/hatp_principal_signer_admin.py` (820 lines, symmetric `enroll_principal`/`enroll_signer`/etc.). Neither module has an `if __name__ == "__main__"` block, an `argparse` parser, or any CLI wrapper — they are importable library code only, unlike `scripts/hatp_certification_admin.py` and `scripts/hatp_deployment_binding_admin.py`, which both have full `argparse`-based `main()` entrypoints under `scripts/`.

This is significant for the DAG: HHCE-REQ-019/020 and HPSE-REQ-028/029 require the writer to be "a separate, non-agent-writable admin tool," "invocable only by the admin OS principal, out of band from any PCAE-agent-invoked code path — never agent-invocable, directly or indirectly." A bare importable function inside `src/pcae/core/` that an agent process *could* import and call does not, by itself, satisfy that architectural separation the way a standalone `scripts/*.py` binary does. **Building the missing `scripts/hatp_hardware_credential_admin.py` / `scripts/hatp_principal_signer_admin.py` CLI wrappers around the already-implemented library functions is itself a real, contract-conforming prerequisite step** — HPSE-REQ-046's own step (2) ("HHCE-001 hardware-credential-registry administrative writer implementation") is not fully discharged by library functions alone if the contract's own writer-surface requirement (a genuinely separate admin tool) is read strictly. This document does not invent a one-off shell/Python invocation to bypass this gap (§16 prohibition honored).

## 13. Principal / Signer / DeploymentBinding DAG (from HPSE-001 §19, HPSE-REQ-046)

Independently derived from `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` §19 (HPSE-REQ-044-046) and §29 (HPSE-REQ-056-057), not from a phase summary. HPSE-REQ-046's frozen 12-step first-use sequence, annotated with current status:

1. Hardware-provider-layer implementation satisfying credential-identity semantics (HPSE-REQ-059/060) — **exists in source** (`hatp_fido2_provider.py`), completeness against HPSE-REQ-059 not re-audited this phase (out of scope; last disclosed status per HPSE-REQ-011 was that neither production provider satisfied it as of that contract text — this phase does not re-verify that claim, only surfaces it as a possible residual blocker for a future FIDO2-selection phase to re-check).
2. HHCE-001 hardware-credential-registry administrative writer implementation — **library functions exist; standalone admin script wrapper does not** (§12 — partial).
3. Independent implementation verification of (1) and (2) — not confirmed complete for the standalone-script form (does not exist to verify).
4. Physical credential provisioning — UNKNOWN this phase (§11).
5. Hardware credential registration via HHCE-001's writer — not done (`hardware-credentials.json` root absent, §3).
6. Principal enrollment — not done (`registry.json` absent).
7. Signer enrollment, gated by HPSE-REQ-056's cross-registry precondition (active `HardwareCredentialRecord` must already exist for the exact `signer_key_id`) — not reachable until step 5.
8. Independent verification of both registries post-enrollment — not applicable yet.
9. `DeploymentBinding` proposition referencing the enrolled `principal_id`/`signer_key_id` — `scripts/hatp_deployment_binding_admin.py` requires `--principal-id`/`--signer-key-id` as CLI arguments (confirmed by source inspection, lines 130-131) — structurally cannot proceed until steps 6-7 complete.
10. Election + CHGR for the `DeploymentBinding` itself (separate from steps 6/7's own enrollment elections, HPSE-REQ-042).
11. `DeploymentBinding` creation.
12. Independent real-host verification.

**Ordering confirmed:** Principal enrollment (step 6) precedes Signer enrollment (step 7) — `enroll_signer` requires an existing `active` `PrincipalRecord` (HPSE-REQ-027), fails closed against a missing/revoked principal. Signer enrollment requires a hardware credential already registered (HPSE-REQ-056) — Signer cannot precede HardwareCredential. Principal and Signer are **not** one atomic ceremony — they are two separate writer operations (`enroll_principal`, `enroll_signer`), each independently elected (HPSE-REQ-042 requires a *separate* fresh election per operation). Signer binds the exact `signer_key_id` credential identity (HPSE-REQ-056's live lookup by that exact key). DeploymentBinding requires all three (Principal, Signer, and — transitively, since Signer requires it — HardwareCredential) to already exist, evidenced directly by the admin script's own required CLI arguments.

## 14. DeploymentBinding — Exact Remaining HBDC-REQ-042 Dependency

`scripts/hatp_deployment_binding_admin.py`'s `create_deployment_binding` requires `principal_id` and `signer_key_id` as explicit caller-supplied arguments (source lines 130-131) — meaning a valid, `active` `PrincipalRecord` and `SignerRecord` pair (§13 steps 6-7) must exist before a real `DeploymentBinding` can be created. This document does not create one. No other precondition beyond the enrolled Principal/Signer pair (plus the DeploymentBinding's own election/CHGR, HPSE-REQ-046 step 10) was found for the create operation itself.

## 15. Class-B Transition — What Moves 32/33 → 33/33

HBDC-REQ-042's own text is dispositive: "`repository_instance_id`... confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding`." The sole residual check (`no_active_deployment_binding_matches_repository_and_root`) is satisfied exactly and only by creating a real, matching `DeploymentBinding` (§14). **Expected candidate confirmed, not merely assumed:** no other named HBDC-REQ check in the Class-B contract's requirement inventory targets DeploymentBinding presence; `HBDC-REQ-042` is the sole residual per 2K.3's own canonical result (§3), and its own text names DeploymentBinding as the unique remedy. Class-B COMPLIANT remains structurally separate from HMIC VALID — nothing in HATP_CLASS_B_DEPLOYMENT_CONTRACT.md references certification/activation state, and nothing in HMIC-001 references Class-B state (§7).

## 16. Readiness DAG — Fresh Six-Item Reconstruction

| Readiness term | Current value | Producer | Prerequisite | Changes if only HMIC activation occurs? |
|---|---|---|---|---|
| HMIC certification validity | `False` (validator MISSING — no binding to validate) | `validate_active_hatp_mandatory_independent_verification_certification` (HMIC-001 §31) | Active CertificationBinding must exist and validate `VALID` | **`False → potentially True`** (§8 — contingent on the fresh validator run, not guaranteed by the binding write alone) |
| Class-B conformance | `False` (NON_COMPLIANT, 32/33, sole residual HBDC-REQ-042) | `verify_class_b_deployment_conformance` | Real `DeploymentBinding` (§14-15) | **Unchanged** — remains `False`; HMIC activation does not touch DeploymentBinding (§7) |
| Trust-Enrollment state (Hardware/Principal/Signer) | `False` (all three absent) | HHCE-001/HPSE-001 registries | Admin-script implementation (§12) → hardware provisioning → registration → enrollment (§13) | **Unchanged** — HMIC activation does not create Trust-Enrollment state (§6, HMIC-REQ-121-class independence) |
| DeploymentBinding presence | `False` (absent) | `scripts/hatp_deployment_binding_admin.py` | Principal + Signer enrolled (§13-14) | **Unchanged** |
| Other HMRC-REQ-054 readiness-conjunction terms (not independently re-derived this phase — out of this phase's scope, named for completeness only) | not re-assessed | HMRC-001 | HMRC-001's own domain | **Unchanged** (§7's cross-contract non-interaction, HMIC-REQ-122-125, applies identically) |
| `HATP_MANDATORY` activation itself | `NOT ACTIVE` | `activate_hatp_mandatory` (HMRC-001) | Full HMRC-REQ-054 conjunction, including the above | **Unchanged** — one term becoming potentially `True` does not satisfy a multi-term conjunction (§4 wall: `HATP READY != HATP ACTIVE`) |

No value above is invented; every "current value" traces to a fresh, this-phase read (§2-3) or to 2K.3's own canonical last-verified value where this phase's own ad-hoc re-check was invocation-sensitive but structurally unchanged (§3's Class-B note).

## 17. Corrected Current DAG

```
CertificationRecord (exists, active-status, unbound)
        │
        │  [structural existence/parse precondition only — NOT VALID check]
        ▼
  HMIC certification activation ── independent of ──▶ Trust-Enrollment (Hardware/Principal/Signer)
        │  (writes CertificationBinding only;               │
        │   CertificationRecord itself immutable)            │  independent of
        ▼                                                     ▼
  HMIC validator (fresh, uncached, every call)          Class-B COMPLIANT
        │                                                     │
        │  VALID ⇒ HMIC readiness term = True                │  requires DeploymentBinding
        ▼                                                     ▼
  [readiness term: HMIC]                          [readiness term: Class-B]

  admin-script implementation gap (scripts/hatp_hardware_credential_admin.py,
  scripts/hatp_principal_signer_admin.py — library funcs exist, CLI wrapper does not)
        │
        ▼
  physical device provisioning (UNKNOWN)
        │
        ▼
  HardwareCredentialRecord registration (HHCE-001 writer)
        │
        ▼
  Principal enrollment (HPSE-001 enroll_principal)
        │
        ▼
  Signer enrollment (HPSE-001 enroll_signer, gated on active HardwareCredentialRecord)
        │
        ▼
  DeploymentBinding creation (scripts/hatp_deployment_binding_admin.py,
  requires principal_id + signer_key_id)
        │
        ▼
  Class-B COMPLIANT (33/33)
        │
        ▼
  [readiness term: Class-B] = True

  ── both readiness-term branches feed independently into ──▶
        HMRC-REQ-054 full readiness conjunction (not fully re-derived this phase)
        │
        ▼
  HATP READY  ≠  HATP ACTIVE  (activate_hatp_mandatory, separate explicit call)
        │
        ▼
  HATP ACTIVE  ≠  PB ALLOW
        │
        ▼
  PB ALLOW  ≠  runtime execution capability
```

## 18. Cycle Analysis

No cycle exists. Every edge above is a one-directional prerequisite (contract-existence → structural-precondition → write → validator-recheck, or provisioning → registration → enrollment → binding). HMIC-REQ-126 explicitly forbids the one cycle that would otherwise be structurally possible (requiring `HATP_MANDATORY` already-active as a precondition to certify) — confirmed absent in source (`certify`/`activate` never check HATP-active state).

## 19. Selected Next Real-Effect Node — Verified, Not Assumed

**Candidate A — HMIC certification activation — is selected.**

Verification chain, each link independently confirmed above rather than assumed from likelihood:

- Current CertificationRecord valid (structurally): confirmed §2 (fresh production-reader read, exact field match, single record, `status=active`).
- Protected Root compliant: confirmed §3 (fresh SSH read of `/etc/pcae/hatp/trust-store`, unchanged from 2K.3).
- Source parity valid: confirmed §1 (deployed revision unchanged, tree clean, only non-authority governance commits ahead).
- No Trust-Enrollment dependency: confirmed §6 (HMIC-REQ-118-126, source-level absence of any reference in `activate()`).
- No Class-B dependency: confirmed §7 (no reference in contract or source; sibling-contract independence explicit).
- Fresh Protected Admin Authority can be obtained for a future phase: not itself performed this phase (no real effect, §28), but the same election mechanism 2K.3 used for `create` remains available and is contractually distinct (§26, "create authorization != activation authorization" — a fresh election is required and obtainable, not blocked by anything found this phase).
- All predecessors satisfied: the record exists, parses, and is named exactly; no other precondition gates `activate()` per source inspection (§5).

**Candidate B (FIDO2) is rejected for this node-selection**, not because it is harder, but because its own predecessor chain is *not* fully satisfied: the admin-script entrypoint gap (§12) is a genuine, contract-motivated (HHCE-REQ-019/020) structural blocker — a real, agent-invocable enrollment write would not conform to the writer-surface requirement as currently implemented. Selecting FIDO2 now would require either (a) building the missing `scripts/*.py` wrappers first (a distinct, non-trivial implementation prerequisite, itself out of scope for a real-effect-node authorization), or (b) invoking the internal `src/pcae/core/` functions directly in a way this phase's own §16 NO-GO explicitly declines to invent. Physical device presence is additionally UNKNOWN (§11).

**Candidate C (admin-entrypoint implementation) is a real, named prerequisite** (§12) but is not itself selected as *this* phase's next real-effect node, because it is not a real-effect node in the HATP protected-state sense the governing prompt scopes (§21) — it is ordinary source implementation work, ungated by Protected Root admin authority, and is more precisely characterized as a *predecessor phase* to Candidate B, not a competing real-effect candidate to Candidate A. It is named here as the concrete blocker future planning should target before FIDO2 becomes selectable.

**Verdict: A — HMIC CERTIFICATION ACTIVATION SELECTED — AUTHORIZATION ENVELOPE FROZEN — NOT EXECUTED.**

## 20. Frozen Authorization Envelope — HMIC Certification Activation

Scope, exact and bounded:

- **Bind exactly this `certification_id`:** `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`. No other id.
- **Do not create another CertificationRecord.**
- **Do not revoke.**
- **Do not create Trust-Enrollment state** (HardwareCredentialRecord, Principal, Signer).
- **Do not create DeploymentBinding.**
- **Do not activate HATP** (`activate_hatp_mandatory` remains a separate, unauthorized ceremony).

**READ-ONLY PRECHECKS** (a future phase, before writing):
1. Re-derive deployed revision, confirm still `305f8e79...` (or re-classify parity if changed, per §1's method).
2. Re-read `certifications.json`, confirm the named `certification_id` still exists, `status=active` (not revoked), and field values unchanged from §2.
3. Re-read `certification-bindings.json`, confirm still ABSENT for this repository/deployment key (or, if present, explicitly re-derive whether overwriting it is intended — §9's deterministic-overwrite behavior applies, not a silent no-op).
4. Confirm Protected Root path, mode, and ownership unchanged from §3.

**PROTECTED ADMIN ELECTION:** A fresh, separate Protected Admin Authority election is required (§26 below) — 2K.3's `create` election does not carry forward.

**HUMAN CONFIRMATION:** Genuine, explicit human confirmation of the exact `activate` operation (not a reused or implied confirmation from any prior ceremony), satisfying `activate()`'s own `confirm=True` requirement (§5).

**ACTIVATE COMMAND:** Exactly the command in §5, with the exact `certification_id` in §20's scope line, run under the deployed venv against `/opt/pcae/runtime/src`.

**POST-BINDING VALIDATOR:** Immediately after the write, run the fresh validator (§31 of HMIC-001) and record its actual `Validation Status` — do not assume `VALID`; report whatever status is actually returned (§8's "may return VALID, not will").

**READINESS CHECK:** Record the resulting HMIC readiness term (`True` iff validator returned exactly `VALID`, per HMIC-REQ-107) and explicitly re-state that Class-B, Trust-Enrollment, and overall `HATP READY`/`HATP ACTIVE` remain unaffected and separately gated (§16 table).

**NO OTHER MUTATION:** No other file under any Protected Root, and no non-Protected-Root production file, may be written by that future phase beyond `certification-bindings.json` itself and this repository's own governance/reporting artifacts (task/phase-report/commit trail).

## 21. Authority Parity Binding

The frozen envelope in §20 is bound to, and invalidated by material change to, all of:

- machine-id: `54ff22ce400b475aa0d55cb68f4a3334`
- RepositoryIdentity: as derived from `/opt/pcae/runtime/src` at this phase's entry (unchanged since 2K.3)
- canonical deployment root: `/opt/pcae/runtime/src`
- deployed authority-bearing identity: commit `305f8e7913bac76941dade6ff4e018c74533f062`
- HMIC contract version: v1.6 (36 frozen source/content members, 7 contract identities)
- exact `certification_id`: `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`
- exact Protected Root: `/etc/pcae/hatp/trust-store`
- exact operation: `activate` (never `create`, never `revoke`)

Any material change to any of the above before the future phase executes invalidates this envelope and requires re-derivation, not blind execution.

## 22. Fresh Human Authority

This phase obtains no election and no human confirmation of its own — it performs no real effect (§28). A future activation-only phase must obtain its own fresh Protected Admin Authority election and its own genuine human confirmation, specific to the `activate` operation named in §20. 2K.3's `create` election is contractually insufficient (§26: "create authorization != activation authorization," restated from HMIC-001 §35/HMIC-REQ-118-120).

## 23. Failure / Recovery (For the Future Activation-Only Phase)

| Failure mode | Disposition |
|---|---|
| Pre-write failure (named `certification_id` not found/unparseable) | Fail closed before any write (`activate()` raises at the structural-precondition check, §5) — retryable without side effect once the input is corrected |
| Mid-write failure (crash between lock acquisition and atomic write) | `_write_active_binding` uses the same `mkstemp`+`fsync`+`os.replace` atomic idiom as every other protected writer (HMIC-REQ-083); no partial document is ever observable; `fcntl.flock` is released automatically on process death (HMIC-REQ-097's dedicated lock, OS-released on abnormal termination per the same discipline HHCE-REQ-034 documents for its own lock) |
| Post-write validation failure (validator returns something other than `VALID`) | Not an error condition of `activate()` itself — the binding write already succeeded; §8 explicitly anticipates this ("may return VALID, not will"); the future phase's own report must record the actual status, not assume success |
| Conflicting existing state (binding already points elsewhere) | Deterministic overwrite, not fail-closed (§9) — the future phase's read-only prechecks (§20) exist specifically to surface this before the write, so the operator is not surprised by silent overwrite |
| Retry | Re-running `activate` with the identical `certification_id` is safe idempotent success (§9) |
| Idempotency | Confirmed structurally safe for the same-id case; not safe-by-default for a different-id case (requires deliberate operator awareness, §9) |
| Revocation/rollback | Revoking the bound `certification_id` (via `revoke`, a separate ceremony, HMIC-REQ-091-093) causes the *next* validator run to return `REVOKED` (HMIC-REQ-094), not an automatic pointer removal — the binding itself remains, pointing at now-revoked evidence, until explicitly rebound. No destructive manual JSON repair is authorized or was performed. |

## 24. Successor Node (If Determinable)

If HMIC activation succeeds and the validator returns `VALID`, the next real-effect node most plausibly readiness-relevant is **not** automatically FIDO2/DeploymentBinding — those remain gated by the separate admin-entrypoint-implementation prerequisite (§12) regardless of HMIC's own state (§16 table: Class-B/Trust-Enrollment rows are unchanged by HMIC activation). The most likely genuine successor, pending this phase's own out-of-scope status, is **Candidate C**: implementing the standalone `scripts/hatp_hardware_credential_admin.py` / `scripts/hatp_principal_signer_admin.py` CLI wrappers around the already-implemented library functions (§12) — an ordinary implementation phase, not a Protected-Root-admin real-effect phase, and therefore itself outside this phase's own real-effect-node selection scope (§19). This document does not authorize that phase; it only names it as the concrete next blocker for the FIDO2 branch.

## 25. Focused Tests / Evidence

See `tests/test_phase_149o_20l_7o_2k_4_post_certificationrecord_dag_re_derivation.py` (disposable/local state only, no real protected-state writes):

- Current `CertificationRecord` identity assertion (fixed value match).
- Binding-absence assertion.
- `activate()`'s confirmation-gate behavior (raises `ConfirmationDeclinedError` without `confirm=True`) — exercised against an isolated `tmp_path` protected root via the existing `_protected_root` test seam, never production.
- `activate()`'s structural-existence-precondition behavior (raises before any write when the named id does not exist) — same isolated fixture.
- Idempotent same-id re-activation behavior (two `activate()` calls, same id, against the same isolated fixture, both succeed with identical resulting document).
- Different-id overwrite behavior (deterministic replacement, not an error) — same isolated fixture.
- DAG structural assertions: no cycle among the 8 nodes named in §3 of the governing prompt; Candidate A's predecessor set is a subset of currently-satisfied facts; Candidate B's predecessor set is not (the admin-entrypoint-gap fact is present).

## 26. Regression

- HMIC remains v1.6, 36 frozen source/content members, 7 contract identities — unchanged (no contract-affecting source file was touched this phase; only `docs/`, `tests/`, and governance/reporting files were written, per this task's own allowed-files list).
- CertificationRecord remains present/unchanged on host — confirmed by the identical fresh read in §2 (single record, same `certification_id`, `status=active`).
- No active binding — confirmed ABSENT, §2-3.
- Class-B remains 32/33 per 2K.3's canonical value (§3's invocation-sensitivity note; no real state change occurred that could move this number).
- Source parity remains valid — §1.
- Runtime unchanged — `pcae runtime inspect`, re-run at phase entry (§27 below), unchanged from the pre-phase baseline (`not_implemented`/`Observed`/`observe`/`execution_unavailable`).

Fast Green: see §27 (Governance Checks) below for the actual run and result.

## 27. Governance Checks (Re-Run at Phase Finalization)

Recorded verbatim from the actual commands run at the end of this phase (see the phase-completion report for the literal captured output):

- `pcae health`
- `pcae check`
- `pcae status coherence`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae runtime inspect`
- `pcae notify status`
- fast_green regression selection

## 28. Proof of No Mutation

- No `sudo -u pcae`/`sudo -n` invocation this phase issued a write call (`create`, `activate`, `revoke`, `register_credential`, `enroll_principal`, `enroll_signer`, `create_deployment_binding`, or any Class-B-mutating call). Every host command issued was a read (`git rev-parse`, `git status`, direct Python read-only reader calls, `.exists()` checks, and the Class-B *verification* function itself, which is read-only by its own contract — it inspects, never writes).
- No file under any Protected Root was written.
- The only writes performed by this phase are to files inside this task's own `Allowed Files` list: this document, its accompanying test file, task-lifecycle files, and PCAE governance/reporting artifacts.

## 29. Rejected-Candidate Rationale (Restated)

- **B (FIDO2):** predecessor chain incomplete — standalone admin-script gap (§12) plus unknown physical device presence (§11). Not rejected for being "harder"; rejected because its own DAG predecessors are demonstrably unsatisfied, unlike A's.
- **C (admin-entrypoint implementation):** real and necessary, but not itself a Protected-Root real-effect node this phase's own scope (§21 of the governing prompt) authorizes selecting between — it is ordinary implementation work, named as B's own blocker (§24), not competing with A.
- **D (current certification not activation-eligible):** explicitly not the finding — §2/§5 confirm the record is structurally activation-eligible (exists, parses, names correctly); nothing found this phase supports a reconciliation-required verdict.

## 30. Expected Successful State (Restated)

POST-CERTIFICATIONRECORD HATP PREREQUISITE DAG RE-DERIVED — NEXT REAL-EFFECT NODE SELECTED (**A: HMIC certification activation**) — AUTHORIZATION ENVELOPE FROZEN (§20-22) — NO REAL EFFECT PERFORMED.
