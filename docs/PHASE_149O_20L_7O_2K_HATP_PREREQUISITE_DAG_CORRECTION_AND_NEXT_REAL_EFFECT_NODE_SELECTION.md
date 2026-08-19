# Phase 149O.20L.7O.2K — HATP Prerequisite DAG Correction and Next Real-Effect Node Selection

## HMIC Certification vs. FIDO2 Hardware-Credential Enrollment

## 0. Phase Identity and Type

**Phase:** 149O.20L.7O.2K
**Type:** ANALYSIS/AUTHORIZATION ONLY. No SSH to hac-dell. No Protected Root
mutation. No HMIC certification. No FIDO2 hardware touch. No
Trust-Enrollment/Principal/Signer/DeploymentBinding creation. No
readiness/HATP activation. No Permission Broker or runtime change. This
phase's only artifacts are this document, its phase-local evidence test
file, and ordinary task/lifecycle/report/PROJECT_STATUS.md/CHANGELOG.md
bookkeeping.
**Phase-entry commit:** `e2c1772deef655fcd506e1e81406eae419f8519c`
**Basis:** `docs/PHASE_149O_20L_7O_2J_HATP_CLASS_B_REAL_HOST_PROTECTED_ROOT_PROVISIONING_AUTHORIZATION.md`
(2J, read directly, not from summary); `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
(HMIC-001 v1.6, read directly, §§0,3,6-9,11-14,16-28,31-35); `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(HBDC-001 v1.2, read directly, §§2,9-17,19-20); `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`
(HPSE-001 v1.1, read directly, §§8-9,11,19,27-38); `src/pcae/core/hatp_providers.py`,
`src/pcae/core/hatp_fido2_provider.py`, `src/pcae/core/hatp_hardware_credential_admin.py`,
`src/pcae/core/hatp_principal_signer_admin.py`, `src/pcae/core/hatp_mandatory_certification.py`,
`scripts/hatp_certification_admin.py`, `scripts/hatp_deployment_binding_admin.py`
(all read directly); and `docs/PHASE_149O_20L_7O_2C_DEPLOYMENTBINDING_FIRST_USE_FIELD_RESOLUTION_ARCHITECTURE.md`
§7 (last primary evidence of physical FIDO2/PIV device absence on hac-dell).

---

## 1. Entering State (§1 of Governing Prompt)

2J falsified 2I's premise: Protected Root is NOT absent on hac-dell. It
already exists, `root:pcae 750`, ACL confirmed, safe ancestors,
HBDC-REQ-011..018 satisfied. The sole residual Class-B failure is
HBDC-REQ-042 (`no_active_deployment_binding_matches_repository_and_root`).

HMIC-001: v1.6. Frozen source identity: 36 members (27 `src/pcae/`-relative
+ 9 repository-root-relative), independently re-counted this phase (§12).
Contract-identity `contract_versions`: 7 members. Real HMIC certification:
ABSENT. Real `HardwareCredentialRecord`: ABSENT. Real Principal: ABSENT.
Real Signer: ABSENT. Real `DeploymentBinding`: ABSENT. Runtime: Observed /
observe / unavailable.

---

## 2. Purpose (§2 of Governing Prompt)

With Protected Root removed as an unsatisfied DAG node, this phase
re-derives — from current contracts and current production source, not
from phase history alone — which of two candidates is the true next
unmet real-effect node: (A) HMIC `CertificationRecord` creation, or (B)
first FIDO2 hardware-credential enrollment. Neither is assumed to win in
advance.

---

## 3. Corrected DAG — First Cut (§3 of Governing Prompt)

2I's DAG named "Protected Root provisioning on hac-dell" as the first
unmet node. That node is removed and replaced:

```
REMOVED (2I, stale):  Protected Root provisioning  <-- UNSATISFIED
REPLACED WITH (2J, current primary evidence):
  Protected Root: SATISFIED AT HBDC-REQ-011..018 BOUNDARY
  -- freshness recheck (2J §7 envelope) required before any future
     real-effect operation relies on it.
```

2I's own document is not edited (out of this phase's allowed-file scope,
and 2J already carries the correction forward per its own §16). This
phase's corrected DAG (§22 below) supersedes both 2I's stale node and
2J's own deferred "selection is out of scope for 2J" placeholder.

---

## 4. Primary Sources Re-Read (§4 of Governing Prompt)

Read directly this phase, not inherited from any prior phase's prose
summary: HMIC-001 v1.6 (§0 status header, §3 scope, §6 threat model, §7
authority, §8 protected root, §9 storage topology, §11-14 schemas, §16-20
implementation identity and contract binding set, §21-28 creation/writer/
revocation, §31-35 validation algorithm and activation integration);
HBDC-001 v1.2 (§2 scope, §9-11 principal/root authority, §16-16.2
repository/deployment binding and `DeploymentBinding` producer, §17 HBDC
trust/binding disposition, §19-20 invariants/vocabulary); HPSE-001 v1.1
(§8 principal↔signer cardinality, §9 provider profile, §11 writer
surface, §19 hardware-credential sequencing, §27-31 cross-registry
consistency, §32-38 current-state corrections and readiness state
machine); HHCE-001 (`HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md`,
read for scope/writer shape); HSCE-001 (current version header read,
unamended by this phase); current HATP readiness/mandatory-cutover
source (`hatp_mandatory_cutover.py`); current `DeploymentBinding`
requirements (HBDC-001 §16.1, `hatp_deployment_binding_admin.py`);
current FIDO2 provider/enrollment source (`hatp_providers.py`,
`hatp_fido2_provider.py`); human-governance requirements controlling
certification (HMIC-REQ-076-078) and trust enrollment (HPSE-REQ-042-043,
HBDC-REQ-064-065).

---

## 5. HMIC Certification Candidate — Exact Operation (§5 of Governing Prompt)

Reconstructed from HMIC-001 §23-25 and `scripts/hatp_certification_admin.py`
(a real, fully-implemented, standalone, non-agent-writable admin script,
frozen at Phase 149O.19.5E, amended for the current 30/36-file scope by
149O.20L.7K/7O.2H/7O.2H.2):

- **Exact admin entry point:** `python scripts/hatp_certification_admin.py
  create --repository-root . --certified-by "<name>" --verification-record-path
  <path>` (create only; `activate`/`revoke` are separate subcommands, not
  invoked by this envelope — §25 below). Never a `pcae` CLI subcommand
  (HMIC-REQ-081/082); never agent-reachable.
- **Exact protected files written:** `certifications.json` only, under
  Protected Root (`create` ceremony). `certification-bindings.json` is
  written only by the distinct `activate` subcommand — NOT authorized by
  this envelope.
- **Active binding in the same ceremony?** No. HMIC-REQ-086/118:
  `CERTIFY` and `ACTIVATE` are separate ceremonies performed by the same
  principal but never combined (HMIC-REQ-035, "creation ceremony" §23
  step 7 is explicit that activation is a distinct, later, separately-
  confirmed step).
- **One transaction or distinct?** Distinct (HMIC-REQ-086, HMIC-REQ-118).
- **Exact current source identity used:** `derive_repository_instance_id`,
  `derive_canonical_deployment_root`, `derive_implementation_commit`,
  `derive_implementation_scope_digest`, `derive_contract_versions` — all
  read-only, tool-derived, never human-typed (HMIC-REQ-077,
  `hatp_mandatory_certification.py:1196-1401`).
- **Exact current contract identity used:** the seven bound contracts'
  own live version headers (HMIC-001 §20; currently HMRC-001, HATP-001,
  HSCE-001, RAE-001, HBDC-001, HPSE-001, HHCE-001 — 7 members, §12
  below).
- **Exact implementation commit binding:** `git rev-parse HEAD` at
  certify time (HMIC-REQ-046).
- **Exact `verification_record_digest` requirement:** a digest of a
  canonical phase-report artifact this certification attests to —
  evidentiary/audit metadata only, never itself re-inspected by
  validation and never a sufficient or partial-sufficient condition for
  `VALID` (HMIC-REQ-071/072/073).
- **Exact operator/human requirement:** Protected Admin Authority
  (HMIC-REQ-013/016), reviewing the canonical phase report out of band
  (human judgment, not this contract's concern, HMIC-REQ-076 step 2),
  confirming the tool-derived tuple, and supplying `certified_by` — the
  only two human-entered fields being confirmation and `certified_by`
  (HMIC-REQ-077).
- **Exact Protected Root requirement:** `HATPTrustStore.production().root`
  must exist, be compliant, and be writable only by the admin principal
  invoking the script (HMIC-REQ-021, HBDC-REQ-011..021) — already
  satisfied per 2J §1/§6.
- **Exact Class-B prerequisite, if any:** NONE mechanically. Class-B
  deployment validity is a *sibling* readiness term to certification
  inside HMRC-001's six-item conjunction (HMIC-REQ-004), not a
  precondition of §31's validation algorithm or §23's creation ceremony.
  See §15 below.
- **Exact Trust-Enrollment prerequisite, if any:** NONE. §31's validation
  algorithm never reads `hardware-credentials.json`, `registry.json`
  (principals/signers), or `deployment-bindings.json` at any of its 12
  steps. See §6 below.
- **Exact `DeploymentBinding` prerequisite, if any:** NONE — same basis.
- **Exact FIDO2 prerequisite, if any:** NONE — same basis.

This phase does not infer a hardware-credential dependency merely
because both certification and enrollment are trust-related; the
contract text is read directly and names none (§5-§9 of governing
prompt honored).

---

## 6. What HMIC Certification Certifies (§6 of Governing Prompt)

**Answer: (A) source + contract identity only — narrower even than "host
state."** Certification attests: repository/deployment identity
(`repository_instance_id`, `canonical_deployment_root`), implementation
identity (`implementation_commit` + `implementation_scope_digest` over
the frozen 36-member authority-bearing *source* file set), and contract
identity (`contract_versions`, the seven bound contracts' version
strings). It does **not** certify host/Class-B state (owner/mode/ACL/
environment lock) — that is HBDC-001's own, separately-evaluated
readiness term (HMIC-REQ-004).

Explicitly, per §31's 12-step validation algorithm (HMIC-REQ-103) and
§17-20's frozen-file enumeration: `hardware-credentials.json`,
`registry.json`'s `principals`/`signers` sections, and
`deployment-bindings.json`/`registry.json`'s `deployment_bindings`
section are **not** inputs to HMIC validation or certification creation,
in any of the following senses:

- **Not read** by `_validate_at_root` (§31) at any of its 12 steps
  (resolve root → resolve identity → load certification files → strict
  parse → repository/deployment match → status → recompute identity →
  contract-version match → self-consistency → `VALID`). No step touches
  `registry.json` or `hardware-credentials.json`.
- **Not part of `implementation_scope_digest`** — the 36-member frozen
  set (§17 of HMIC-001) binds *source code* (`.py` modules implementing
  the writers/validators/providers) and *contract-document bytes*, never
  *runtime data files* the writers produce. `hatp_hardware_credential_admin.py`
  and `hatp_principal_signer_admin.py` are in the frozen set (source);
  `hardware-credentials.json` and `registry.json` are not (data).
- **Not part of `contract_versions`** — that field binds contract
  *version strings*, not the *content* of any registry file.

This is the load-bearing distinction the governing prompt's §6 asks for:
source code that *implements* trust records is HMIC-bound; the *data
records themselves* are not.

---

## 7. Certification Preconditions Table (§7 of Governing Prompt)

| Certification prerequisite | Requirement | Current status | Blocking? |
|---|---|---|---|
| Protected Root exists, compliant | HMIC-REQ-021, HBDC-REQ-011..018 | SATISFIED (2J §1, freshness recheck required at future-phase entry, 2J §7) | No |
| Repository identity | `repository_instance_id` derivable, CRI Layer 1 | SATISFIED (present, validated, 2J §4/7O.2B.1) | No |
| Canonical deployment root | `resolve_canonical_deployment_root()` resolvable | SATISFIED (Model A, source tree present, 2J §4) | No |
| Implementation commit | `git rev-parse HEAD` resolvable | SATISFIED (mechanical; any commit is a valid identity component) | No |
| 36-member source digest | frozen file set present, byte-stable | SATISFIED (§12 below; independently re-counted this phase) | No |
| 7-member contract identity | seven bound contracts' version headers readable | SATISFIED (HMRC-001, HATP-001, HSCE-001, RAE-001, HBDC-001 v1.2, HPSE-001 v1.1, HHCE-001 — all present, §12 below) | No |
| Independent verification record (evidentiary) | a canonical phase-report artifact to reference as `verification_record_digest` | SATISFIED, non-blocking — HMIC-REQ-072 makes this evidentiary-only, never a validity condition; this repository already holds an extensive independent-verification phase chain (e.g. 149O.19.3R.1, 149O.20K.3, 149O.20L.7L.2/7L.4/7L.5) the future admin MAY reference; the *most recent* v1.5→v1.6 amendment (2H.2) is itself still "independent verification pending" as contract self-disclosure, which is a documentation-completeness note, not a mechanical HMIC-REQ-076/HMIC-REQ-072 gate | No (flagged, not blocking — see §33) |
| Administrator identity (Protected Admin Authority) | real OS write access to Protected Root | Not independently re-verified live by this phase (no SSH performed); 2J's frozen re-verification envelope applies | Yes, procedurally — a future phase MUST run 2J §7's precheck and confirm live OS write access before invoking the script; this is a freshness gate, not a design gap |
| Current certification absence | no pre-existing `CertificationRecord` for this repository/deployment key | ABSENT (§1; consistent with §30 idempotency discussion) | No — absence is the expected, correct starting state |
| Class-B state | COMPLIANT/NON_COMPLIANT/INDETERMINATE | NON_COMPLIANT (sole failure HBDC-REQ-042) | **No** — not a certification input (§6, §15) |
| Hardware credential | `HardwareCredentialRecord` present | ABSENT | **No** — not a certification input (§6) |
| Principal | `PrincipalRecord` present | ABSENT | **No** — not a certification input (§6) |
| Signer | `SignerRecord` present | ABSENT | **No** — not a certification input (§6) |
| `DeploymentBinding` | present, matching | ABSENT (HBDC-REQ-042) | **No** — not a certification input (§6) |
| Human authorization | Protected Admin Authority election/confirmation (HMIC-REQ-076 steps 2/5) | Not yet obtained — this is exactly what a future, separate real-effect phase must obtain; not obtained by this analysis-only phase | Yes — this is the actual real-effect gate, deliberately not satisfied here (§18, §37) |

No unknown row above is classified as satisfied by assumption; each
status is cited to a specific requirement or primary-evidence phase.

---

## 8. Certification Outputs — Distinguished (§8 of Governing Prompt)

| Fact | Becomes true after `create` alone? | Becomes true after `activate` (separate, NOT authorized here)? |
|---|---|---|
| `CertificationRecord` exists in `certifications.json`, `status="active"` (record-level, not binding-level) | **Yes** | Yes (unchanged) |
| Active `CertificationBinding` exists in `certification-bindings.json` | **No** | Yes |
| `validate_active_hatp_mandatory_independent_verification_certification()` returns `VALID` | **No** — with no active binding, step 4 of §31 (load `certification-bindings.json`) returns `MISSING` before the new record is ever consulted | Yes, if all 12 steps pass |
| `mandatory_consumption_implementation_independently_verified` readiness term becomes `True` | **No** | Yes, if `VALID` |
| HATP overall `ready=True` | **No** | No — five other independent readiness terms also required (HMIC-REQ-004), including Class-B (currently NON_COMPLIANT) |
| HATP `HATP_MANDATORY` active | **No** | No — activation is `activate_hatp_mandatory()`, a wholly separate act HMIC-001 does not perform (HMIC-REQ-006, HMIC-REQ-118-121) |

This phase's frozen envelope (§25 below) authorizes only the leftmost
"Yes" column — record creation, not activation, not readiness, not
HATP activation.

---

## 9. FIDO2 Enrollment Candidate — Exact Operation (§9 of Governing Prompt)

Reconstructed from HPSE-001 §19,27-38 and `hatp_fido2_provider.py`/
`hatp_hardware_credential_admin.py` production source:

- **Physical hardware interaction:** real, if a device is attached
  (`Fido2HardwareProvider.enroll_credential`, real CTAP2 `makeCredential`
  call against `CtapHidDevice.list_devices()`'s first enumerated device).
- **CTAP call:** `Ctap2.make_credential(client_data_hash, rp, user,
  key_params)` — a genuine hardware ceremony, not a stub, as of Phase
  149O.20L.7O.2F ("Surface A").
- **Credential creation:** yes — mints a fresh credential on the device;
  never extracts a private key (HHCE-REQ-004/012(d)).
- **Non-resident credential behavior:** the enrollment ceremony as
  implemented does not require the credential be discoverable/resident
  (`credential_identity()` itself, a *different* method, remains an
  unconditional raise and is not called by production enrollment or
  signing — see 2F.2's repair note in `hatp_fido2_provider.py:315-338`).
- **Credential ID / public-key output:** `EnrolledFido2Credential`
  (`credential_id_hex`, `algorithm`, `public_key_hex`, `provider_profile`)
  — the exact tuple `hatp_hardware_credential_admin.register_credential()`
  (Surface B) requires.
- **Provider profile:** `HATP_HARDWARE_PROVIDER_V1`, the sole closed
  vocabulary value (HPSE-REQ-018).
- **`HardwareCredentialRecord` write:** performed by a *separate* function
  (`register_credential`, `src/pcae/core/hatp_hardware_credential_admin.py`),
  not by `enroll_credential()` itself — two distinct steps, mirroring
  HMIC's own create/activate separation.
- **Protected Root write location:** `hardware-credentials.json` under
  Protected Root (distinct file from `certifications.json`/
  `registry.json`).
- **Exact human interaction/touch:** CTAP2 user-presence touch during
  `make_credential` (hardware-enforced; this module never caches or
  substitutes a presence result, per `hatp_providers.py` capability
  notes).
- **Exact admin identity:** the writer (`register_credential`) is a
  library function; **no standalone `scripts/hatp_hardware_credential_admin.py`
  entry-point script exists** (verified §29 below) — unlike certification
  and `DeploymentBinding`, which each have a real, frozen, standalone
  admin script under `scripts/`.
- **Must Principal already exist?** No — `register_credential` writes
  only `hardware-credentials.json`, independent of `registry.json`'s
  `principals`/`signers` sections (HPSE-001 §28, registry separation).
- **Must Signer already exist?** No — same basis; a `SignerRecord` is
  created *after* the credential, by `enroll_signer` (HPSE-REQ-056: the
  ordering is credential-then-signer, never the reverse).
- **Must HMIC already be `VALID`?** No — nothing in HPSE-001/HHCE-001
  conditions hardware-credential registration on HMIC certification
  status; no contract text names this dependency.
- **Must `DeploymentBinding` already exist?** No — `DeploymentBinding`
  is downstream of Signer (§16 below), not a precondition of hardware-
  credential registration.
- **Must Class-B already be `COMPLIANT`?** No mechanical requirement
  found; HBDC-REQ-042's own scope is deployment-identity matching, not a
  gate on hardware-credential registration (HPSE-REQ-068).

---

## 10. FIDO2 Enrollment Preconditions Table (§10 of Governing Prompt)

| FIDO2 enrollment prerequisite | Requirement | Current status | Blocking? |
|---|---|---|---|
| Protected Root | exists, compliant | SATISFIED (2J §1) | No |
| `pcae` OS identity | agent principal exists, not required for enrollment (admin-only writer) | N/A to this ceremony (admin-invoked) | No |
| Provider support | `Fido2HardwareProvider.enroll_credential` implemented and real | SATISFIED (Phase 149O.20L.7O.2F "Surface A" — real CTAP2 `makeCredential`, not a stub) | No |
| FIDO2 device availability | a compliant physical device attached to hac-dell | **Last primary evidence: ABSENT** — 149O.20L.7O.2C §7 independently confirmed "no physical FIDO2/PIV device present on the target host"; no later real-host phase reports a device now attached; this phase performed no SSH and cannot refresh this fact | **Yes — the true current blocker (§24 below)** |
| Admin writer for `hardware-credentials.json` | a standalone, non-agent-writable script mirroring `scripts/hatp_certification_admin.py`'s pattern | **ABSENT** — library function `register_credential()` exists (`src/pcae/core/hatp_hardware_credential_admin.py`), but no `scripts/hatp_hardware_credential_admin.py` wrapper exists (§29 below); an operator would need ad hoc Python invocation, which the governing prompt's §29 explicitly disallows ("no open-ended manual scripting") | Yes — a real, separate implementation gap |
| HMIC certification | not required (§9) | N/A | No |
| Principal | not required for credential registration (§9) | N/A | No |
| Signer | not required for credential registration (§9) | N/A | No |
| `DeploymentBinding` | not required for credential registration (§9) | N/A | No |
| Repository/root identity | resolvable | SATISFIED | No |
| Class-B state | not a mechanical gate (§9) | N/A | No |
| Human authorization | fresh, separate election (HPSE-REQ-042 analog for HHCE-001, not yet drafted as its own req set) | Not obtained (out of scope, this phase) | Yes — the actual real-effect gate |

Two independent, currently-unsatisfied blockers exist for FIDO2
enrollment as the *first* real-effect step: (1) no physical device
confirmed present, and (2) no frozen standalone admin script exists for
the credential-registration half of the ceremony (`enroll_credential()`
alone, without a governed `register_credential()` wrapper script,
produces a minted credential with no durable, auditable write path
matching this repository's own established admin-tooling convention).

---

## 11. FIDO2 Enrollment Outputs — Distinguished (§11 of Governing Prompt)

| Artifact | Created by `enroll_credential()` alone? | Created by `register_credential()` (separate call)? |
|---|---|---|
| Physical credential on device | Yes | No (device-side only) |
| `EnrolledFido2Credential` (in-memory return value) | Yes | consumed as input, not itself stored |
| `HardwareCredentialRecord` (`hardware-credentials.json`) | No | Yes |
| `PrincipalRecord` | No | No — a wholly separate HPSE-001 operation |
| `SignerRecord` | No | No — a wholly separate HPSE-001 operation (`enroll_signer`, requires HPSE-REQ-056's precondition) |
| `DeploymentBinding` | No | No — a wholly separate HBDC-001 §16.1 operation |

No single command silently creates all four; this repository's own
source already keeps each authority-bearing record transition separately
inspectable, consistent with the governing prompt's §11 strong default.

---

## 12. Certification ↔ Enrollment Order (§12 of Governing Prompt)

**Sequence A: HMIC certification → FIDO2 enrollment.**
- Dependency violation? None found — certification consumes no
  enrollment-produced record (§6).
- Circular prerequisite? None.
- Certification invalidation? A later FIDO2 enrollment writes only
  `hardware-credentials.json`/`registry.json` (data), never a
  36-member-frozen *source* file, so `implementation_scope_digest`
  remains unchanged (§13 below) — certification is NOT invalidated by a
  later enrollment.
- Unnecessary trust-state mutation? None — certification mutates only
  `certifications.json`.
- Unbound authority? None — certification confers no runtime capability
  (HMIC-REQ-124).
- Impossible validation? None.

**Sequence B: FIDO2 enrollment → HMIC certification.**
- Dependency violation? None found either — nothing in HMIC-001 requires
  certification to occur *after* enrollment.
- Circular prerequisite? None.
- Certification invalidation? N/A (certification occurs second in this
  ordering).
- Unnecessary trust-state mutation? None inherent, but: FIDO2 enrollment
  currently has two unsatisfied preconditions (§10) that certification
  does not share, making Sequence B strictly harder to actually execute
  today regardless of contract-level admissibility.
- Unbound authority? None.
- Impossible validation? None.

**Contract text supports either order as admissible in principle**
(HMIC-REQ-004's independence framing, §6's non-consumption finding).
**§24 selects between them on readiness grounds, not order-validity
grounds** — both orders are legal; only one candidate is actually
unblocked today.

---

## 13. Does Enrollment Change HMIC Identity? (§13 of Governing Prompt)

**No.** FIDO2 enrollment writes only protected *runtime/trust data*
(`hardware-credentials.json` via `register_credential`, `registry.json`
via a later, separate `enroll_signer` call) — never any of the 36 frozen
*source* files or the contract-document bytes `implementation_scope_
digest` binds (HMIC-001 §17-19; confirmed by direct inspection this
phase, §12 below, that `hardware-credentials.json` and `registry.json`
are absent from `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_
ROOT_RELATIVE_FILES`). An existing HMIC certification's
`implementation_scope_digest` therefore remains stable across a future
FIDO2 enrollment. If a future amendment ever bound `hardware-
credentials.json` or `registry.json` *content* into the digest (it does
not today), this conclusion would need re-derivation — that amendment
does not exist.

---

## 14. Does Certification Depend on Enrollment State? (§14 of Governing Prompt)

**No**, distinguishing source-code membership from data-record content
exactly as the governing prompt's §14 asks: `hatp_hardware_credential_
admin.py` and `hatp_principal_signer_admin.py` (the *source code that
implements* enrollment) ARE members of HMIC's 36-file frozen set (bound
since 149O.20L.7O.2H, limb (d)) — their *bytes* participate in
`implementation_scope_digest`. But the *data* those modules would write
(`hardware-credentials.json`, `registry.json` principal/signer entries)
is never read by §31's validation algorithm (§6, §7 tables above). A
certified implementation with zero enrolled credentials and a certified
implementation with fully enrolled credentials produce an identical
`implementation_scope_digest`, because the digest is over unchanging
source bytes, not over the mutable data those source files' functions
write at runtime.

---

## 15. Class-B Current State (§15 of Governing Prompt)

Reconstructed from `hatp_class_b_conformance.py` and 2J §1/§10, verified
this phase (§12): Class-B `verify_class_b_deployment_conformance` returns
**NON_COMPLIANT** today, and — per 2J's independently re-run, twice,
deterministic result (34 total checks, 33 satisfied) — the **sole**
residual failure is `HBDC-REQ-042` (`no_active_deployment_binding_
matches_repository_and_root`).

- **Is Class-B `NON_COMPLIANT` solely because `DeploymentBinding` is
  absent?** Yes, per 2J's re-run and this phase's re-read of
  `_check_deployment_identity`'s exact failing branch — no other check
  among the 34 currently fails.
- **Is Class-B `COMPLIANT` a prerequisite to HMIC certification?** No
  (§6, §7, §9 — certification's validation algorithm never reads
  Class-B/`DeploymentBinding` state; HMIC-REQ-004 makes Class-B a
  *sibling*, not a *predecessor*, readiness term).
- **Is Class-B `COMPLIANT` a prerequisite to FIDO2 enrollment?** No
  mechanical gate found (§9-§10) — hardware-credential registration and
  even signer enrollment do not condition on Class-B's deployment-
  conformance verdict; the *reverse* is true (a `DeploymentBinding`,
  which flips HBDC-REQ-042, itself requires Signer, which requires
  hardware credential, §16).
- **Is Class-B only required later, for readiness?** Yes — Class-B
  deployment validity is one of HMRC-001's six independent readiness
  terms for `PREPARED`/`HATP_MANDATORY` activation (HMIC-REQ-004),
  consumed only at that later activation-readiness boundary, not at
  either candidate's own creation/enrollment boundary.

---

## 16. `DeploymentBinding` Dependency (§16 of Governing Prompt)

Derived, not assumed, from HPSE-001 §27-31 and HBDC-001 §16.1:

```
HardwareCredential (register_credential, HHCE-001-governed)
        |
        v   [HPSE-REQ-056 precondition: live lookup, "active" record required]
Signer (enroll_signer, HPSE-001-governed; ALSO requires an existing,
        "active" PrincipalRecord, HPSE-REQ-027)
        |
        v   [DeploymentBinding producer draws principal_id/signer_key_id
             from admin's enrollment context, HBDC-REQ-058]
DeploymentBinding (hatp_deployment_binding_admin.py, HBDC-001 §16.1-governed)
```

**Confirmed order: HardwareCredential → (Principal, independently) →
Signer → `DeploymentBinding`.** Signer enrollment requires HardwareCredential
to exist first at writer time (HPSE-REQ-056, HPSE-REQ-058's lock-ordering
precondition check performed live under the hardware-credential-store
lock before the registry-transition lock, HPSE-REQ-057) — this is exactly
the "prove it" instruction the governing prompt gives, and HPSE-REQ-056's
text is unambiguous on this point: hardware-credential registration
"before signer enrollment ... never the reverse."

---

## 17. Principal / Signer Dependency (§17 of Governing Prompt)

- **May Principal/Signer enrollment occur before HMIC certification?**
  Yes — no contract text conditions `enroll_principal`/`enroll_signer` on
  certification status (§6, §14).
- **Does it require hardware credential first?** Principal enrollment:
  no (Principal has no hardware dependency, HPSE-001 §4-5). Signer
  enrollment: yes, per §16 above (HPSE-REQ-056).
- **May it be performed in one atomic writer ceremony?** No — HPSE-001
  defines `enroll_principal` and `enroll_signer` as separate mutating
  operations (HPSE-REQ-026), and the cross-registry sequence (hardware
  credential then signer) is itself two separate writer calls under
  ordered locks (HPSE-REQ-057), not one atomic cross-file transaction
  (HPSE-REQ-058 partial-failure matrix exists precisely because no such
  atomicity is claimed).
- **Requires independent human authorization?** Yes — HPSE-REQ-042/043,
  a fresh, separate election per operation, mirroring HBDC-REQ-064/065.
- **Changes any HMIC identity?** No (§13-14 above — data, not source).

This phase performs none of these operations (§37).

---

## 18. Human Authority (§18 of Governing Prompt)

| | HMIC certification | FIDO2 enrollment |
|---|---|---|
| Deciding authority | Protected Admin Authority (HMIC-REQ-013/016) | Protected Admin Authority, invoking a not-yet-scripted writer (§10) |
| Evidence form | out-of-band human review of a canonical phase report (HMIC-REQ-076 step 2), tool-derived tuple confirmation, `certified_by` string | a fresh, separate election (HPSE-001 §18 analog required of HHCE-001 per HPSE-REQ-054, not yet its own drafted req set) |
| Distinctions preserved | operator approval (human confirmation) != cryptographic proof (CTAP2 signature, not used by certification) != HMIC certification (the record itself) != permission (OS write access) != capability (runtime execution right, never granted, HMIC-REQ-124) != execution (agent runtime action, structurally excluded, HMIC-REQ-017/018) | identical distinctions apply; additionally CTAP2 user-presence touch is a *device-level* human-presence proof, structurally distinct from the *administrative* election HPSE-REQ-042 requires |

This phase freezes a **future** authorization envelope (§25); it does
not itself perform, or substitute for, either operation's real human
authorization act.

---

## 19. Permission Broker (§19 of Governing Prompt)

**Neither candidate currently passes through Permission Broker.**
HMIC-REQ-122 ("Certification Does Not Evaluate PB") and HMIC-REQ-125
("`POL-005`/`COMP-002` Unaffected") state this explicitly for
certification. No contract text (HPSE-001, HBDC-001, HHCE-001) routes
hardware-credential registration, Principal/Signer enrollment, or
`DeploymentBinding` creation through Permission Broker either — each is
an out-of-band administrative ceremony performed by a non-agent-reachable
tool, structurally outside PB's agent-request-evaluation scope. `POL-005`/
`COMP-002` are irrelevant execution-authorization concerns for either
candidate and are not carried into this phase's analysis (governing
prompt §19's own instruction honored).

---

## 20. Runtime (§20 of Governing Prompt)

Runtime remains Observed / observe / unavailable. Both candidate
administrative actions are Protected-Admin-Authority filesystem writes
via a non-agent-reachable tool (HMIC-REQ-079-082; HPSE-REQ-028-029) —
neither is agent runtime execution, and neither contract conditions its
ceremony on runtime availability. HMIC-REQ-124 additionally confirms
certification creates no runtime execution capability. Administrative
protected-state mutation by the Protected Admin Authority is not agent
runtime execution under either contract's own terms; this phase does not
invent such a linkage.

---

## 21. Protected Root Freshness (§21 of Governing Prompt)

This phase performed no SSH and needs none — it relies entirely on 2J's
already-frozen re-verification envelope (2J §7.1-7.3), unchanged and
reaffirmed here: `stat`/`getfacl`/`find` against `/etc/pcae/hatp/trust-store`,
`machine-id`/`hostname`/OS/arch checks, `git rev-parse HEAD` on
`/opt/pcae/runtime/src`, `id pcae` — all READ-ONLY, none executed by this
phase. Any future real-effect phase (whichever candidate it authorizes)
MUST re-run this exact envelope fresh at its own entry before relying on
Protected Root state, per 2J §7.2's PASS/FAIL classification (unmodified,
reaffirmed, not re-authored here to avoid drift between two documents
describing the identical check).

---

## 22. Corrected Prerequisite DAG (§22 of Governing Prompt)

```
RepositoryIdentity/canonical root (existing, verified)
        |
        v
Protected Root on hac-dell           <-- SATISFIED (2J §1; freshness recheck required, §21)
        |
        +-----------------------------------------------------------+
        |                                                           |
        v                                                           v
HMIC v1.6 source/contract identity    Class-B host provisioning/environment-lock
(36/7, verified, §12)                 (7E Actions 1-5; 33/34 checks pass, sole
        |                              gap HBDC-REQ-042)
        v                                                           |
HMIC CertificationRecord creation                                   v
(admin ceremony, §5, §23)             class_b_deployment_conformance_
        |                              satisfies_readiness  <-- NON_COMPLIANT
        v                                                           |
HMIC CertificationBinding activation                                v
(separate ceremony, NOT this phase)   [needs DeploymentBinding, below]
        |                                                           |
        |          FIDO2 hardware device present on host (UNVERIFIED
        |          PRESENT; last evidence: ABSENT, 149O.20L.7O.2C)
        |                        |
        |                        v
        |          HardwareCredential registration (register_credential;
        |          library exists; standalone admin script ABSENT, §29)
        |                        |
        |                        v
        |          Principal enrollment (enroll_principal; independent
        |          of hardware; library exists)
        |                        |
        |                        v
        |          Signer enrollment (enroll_signer; requires active
        |          Principal AND registered HardwareCredential, HPSE-REQ-056)
        |                        |
        |                        v
        |          DeploymentBinding creation (hatp_deployment_binding_admin.py;
        |                        closes HBDC-REQ-042)
        |                        |
        +------------------------+
                     |
                     v
        Readiness ready=True (HMRC-001 six-term conjunction: certification
        VALID AND Class-B COMPLIANT AND HATP substrate operational AND
        HSCE signing available AND dependency provenance valid AND
        Protected Activation Authority mechanism available)
                     |
                     v
        HATP_MANDATORY activation (activate_hatp_mandatory, separate
        explicit call; human authorization; NOT this phase, NOT the
        next phase either)
```

Every edge above is cited to a specific requirement or primary-evidence
phase in §5-§17; no inferred convenience edge is present. The HMIC branch
and the Class-B/enrollment branch are independent until they both must
hold simultaneously at the final readiness conjunction — they are not
sequential with respect to each other.

---

## 23. Cycle Analysis (§23 of Governing Prompt)

Testing the governing prompt's named candidate cycle — "HMIC certification
requires Class-B; Class-B requires DeploymentBinding; DeploymentBinding
requires Signer; Signer requires certification" — against §22's DAG:

- HMIC certification requires Class-B? **No** (§6, §15 — refuted by
  direct contract text, HMIC-REQ-004 and §31's validation algorithm).
- Class-B requires `DeploymentBinding`? **Yes** (HBDC-REQ-042, confirmed
  §15).
- `DeploymentBinding` requires Signer? **Yes** (§16, HBDC-REQ-058).
- Signer requires certification? **No** (§17 — refuted; `enroll_signer`'s
  only preconditions are an active Principal and a registered hardware
  credential, HPSE-REQ-027/056; certification is never named).

**The hypothesized cycle does not exist** — the first edge in the chain
(certification→Class-B) is false, which alone breaks the cycle; the
fourth edge (Signer→certification) is independently also false. No other
candidate cycle was found by walking §22's DAG (each node's predecessor
set was checked against the requirement citing it in §5-§17; no back-edge
exists). **No Blocking architectural defect.**

---

## 24. Selected Next Real-Effect Node (§24 of Governing Prompt)

Applying the exact selection criteria — all predecessors satisfied;
narrowest authority transition; independently observable; fail-closed;
reversible/revocable where required; no future prerequisite violated; no
unnecessary coupling — to the two candidates:

| Criterion | HMIC certification | FIDO2 enrollment |
|---|---|---|
| All predecessors satisfied? | **Yes** — Protected Root compliant (§1/§21), source/contract identity stable (§12), no Class-B/hardware/Principal/Signer/DeploymentBinding predecessor exists (§6-§9, §15) | **No** — physical device presence unverified/last-known-absent (§10); no standalone admin script exists for the credential-registration half (§10, §29) |
| Narrowest authority transition | append one immutable `CertificationRecord`; explicitly not activation (§5, §8) | mint one hardware credential + one registry record; narrower in artifact count but blocked on an external physical fact this phase cannot resolve |
| Independently observable | Yes — `load_certification`/read of `certifications.json` (§8) | Yes, in principle, once registered |
| Fail-closed | Yes (HMIC-REQ-083-084, atomic write, create-once) | Yes (`register_credential`'s existing atomic-write/read-back discipline) |
| Reversible/revocable | Yes — `revoke` is a distinct, defined ceremony (§32) | Yes — `revoke_credential` exists (§32) |
| No future prerequisite violated | Confirmed — certification does not consume or foreclose any enrollment-side record (§6, §13) | Confirmed in principle, but moot while blocked |
| No unnecessary coupling | Yes — create-only, no activation bundled (§27 discipline honored) | Would require bundling around a missing admin-script layer to proceed responsibly today |

**Selected: (A) HMIC `CertificationRecord` creation.**

**Rejected candidate reasoning (FIDO2 enrollment):** not because it is
contractually disfavored — §12 found both orders admissible — but
because, on current primary evidence, it fails the first selection
criterion outright: the last confirmed real-host fact (149O.20L.7O.2C
§7) is that no compliant physical FIDO2/PIV device is present on
hac-dell, and this phase performed no SSH to refresh that fact (§21,
by design — freshness recheck is a *future* phase's job, not this
analysis phase's). Independently, even if a device were confirmed
present, the credential-registration half of the ceremony lacks the
standalone, non-agent-writable admin script this repository's own
established convention requires (mirroring `scripts/hatp_certification_
admin.py` and `scripts/hatp_deployment_binding_admin.py`) — proceeding
without one would mean authorizing "call `register_credential()`
directly," which is exactly the "no open-ended manual scripting"
outcome the governing prompt's §29 forbids. Both gaps are real,
evidence-supported, and independent of implementation convenience.

**Verdict shape selected: A** — HMIC CERTIFICATION SELECTED AS NEXT
REAL-EFFECT NODE — AUTHORIZATION ENVELOPE FROZEN — NOT EXECUTED (§38,
§42).

---

## 25. Frozen Authorization Envelope — HMIC Certification (§25 of Governing Prompt)

- **Exact host:** hac-dell (`machine-id` `54ff22ce400b475aa0d55cb68f4a3334`,
  hostname `atila-Latitude-E5470`, Ubuntu 24.04.3, x86_64 — 2J §4,
  reaffirmed §21).
- **Protected Root:** `/etc/pcae/hatp/trust-store` (2J §5-§6).
- **Current `RepositoryIdentity`:** `0107866f-af7c-40b4-8317-74e71acb05ca`
  (2J §4; re-derived read-only by the tool at ceremony time regardless,
  HMIC-REQ-045).
- **Current HMIC version:** v1.6 (this phase; unchanged).
- **Required 36/7 source identity:** the current `_FROZEN_SRC_PCAE_
  RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` set (36
  members) and the current 7-member `contract_versions` set (§12),
  re-derived fresh by the tool, not cached from this document.
- **Exact admin ceremony:** `python scripts/hatp_certification_admin.py
  create --repository-root . --certified-by "<Protected Admin Authority's
  own identity string>" --verification-record-path <path to a canonical
  phase-report artifact, e.g. this document or a dedicated future
  verification phase's report>` — `create` subcommand only.
- **Exact record(s) written:** one new, immutable `CertificationRecord`
  appended to `certifications.json`, `status="active"` (record-level
  status, distinct from binding activation, §8). No write to
  `certification-bindings.json`.
- **Exact prechecks:** 2J §7.1's full read-only command envelope, run
  fresh at the future phase's own entry (§21), PLUS: `git rev-parse HEAD`
  on the repository being certified (already part of the tool's own
  derivation, HMIC-REQ-046) and a live read of the seven bound contracts'
  version headers (already part of the tool's own derivation,
  HMIC-REQ-076 step 4) — no additional manual precheck is layered on top
  of what the tool itself already performs read-only.
- **Exact human authorization:** a fresh, separate Protected Admin
  Authority election reviewing the canonical phase report this
  certification's `verification_record_digest` will reference, followed
  by explicit confirmation of the tool-presented tuple (HMIC-REQ-076
  steps 2/5, HMIC-REQ-077) — NOT obtained by this phase; the next phase's
  own charter must obtain it.
- **Exact evidence inputs:** the tool's own read-only derivation outputs
  (§5 above) plus the human's `certified_by` string and verification-
  record locator.
- **Exact expected output:** exactly one new `CertificationRecord`, no
  active `CertificationBinding` change, no readiness change, no
  activation.
- **Validation immediately after write:** the future phase MUST run
  `load_certification(new_certification_id, root)` and confirm the
  record reads back with the expected fields, AND run `validate_active_
  hatp_mandatory_independent_verification_certification()` and confirm
  it still returns `MISSING` (not `VALID`) — because no active binding
  was written — as positive proof the create-only boundary held (§8).
  A `VALID` result at this checkpoint would itself indicate the envelope
  was violated (an unauthorized `activate` occurred) and MUST be treated
  as a Blocking anomaly, not a success.
- **Failure behavior:** rely entirely on the existing writer's own
  atomic-write/create-once/read-back-verify discipline (HMIC-REQ-083-084)
  — no new locking or retry logic authorized; a failed write leaves
  `certifications.json` byte-unchanged (mkstemp+fsync+os.replace never
  exposes a partial document).
- **Explicitly NOT authorized by this envelope:** Trust-Enrollment
  (Principal/Signer/HardwareCredential); `DeploymentBinding`; readiness
  change; `HATP_MANDATORY` activation; the `activate` or `revoke`
  subcommands.

---

## 26. FIDO2 Envelope — Not Frozen (§26 of Governing Prompt)

Not applicable — FIDO2 enrollment was not selected (§24). No envelope is
frozen for it by this phase. §10's two identified gaps (device presence,
standalone admin script) are named here as the specific work a future
phase pursuing FIDO2 first would need to close, but authoring that
envelope is out of this phase's scope per §27/§43.

---

## 27. Do Not Authorize Both (§27 of Governing Prompt)

Honored — only §25's HMIC-certification-create-only envelope is frozen.
No combined certification+enrollment phase is authorized, and no FIDO2
envelope of any kind is frozen (§26).

---

## 28. Authorization Freshness (§28 of Governing Prompt)

The §25 envelope is bound to, and invalidated by material change in: host
`machine-id`/hostname/OS/arch (§21); `RepositoryIdentity`
`0107866f-af7c-40b4-8317-74e71acb05ca`; canonical deployment root
(`/opt/pcae/runtime/src`); Protected Root path (`/etc/pcae/hatp/trust-store`);
HMIC version (v1.6) and its 36/7 identity; the seven bound contracts'
current versions (§12); the repository commit at future-phase entry
(this phase's own entry commit, `e2c1772d...`, is itself superseded by
whatever commit the future phase enters at — the tool re-derives
`implementation_commit` fresh regardless, HMIC-REQ-046, so no manual
commit-pinning is needed beyond re-running the tool). A future phase
entering under a materially different HMIC/HBDC/HPSE/HHCE version MUST
re-derive §5-§24 from primary source again, not reuse this document's
tables uncritically — mirroring 2J §11's identical discipline.

---

## 29. Plan / Command Envelope (§29 of Governing Prompt)

```
READ-ONLY PRECHECK  (2J §7.1, reaffirmed §21; run fresh, not cached):
  sudo -n stat -c "%U:%G %a %F" /etc/pcae/hatp/trust-store
  sudo -n getfacl -p /etc/pcae/hatp/trust-store
  sudo -n find /etc/pcae -maxdepth 3 -printf "%p %u:%g %m %y\n"
  sudo -n find /etc/pcae/hatp/trust-store -type f
  cat /etc/machine-id
  hostname
  cat /etc/os-release
  uname -m
  sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
  id pcae

REAL-EFFECT COMMAND  (governed admin entrypoint, §25; not executed by
this phase):
  python scripts/hatp_certification_admin.py create \
    --repository-root . \
    --certified-by "<Protected Admin Authority identity>" \
    --verification-record-path <canonical phase-report path>

READ-ONLY POSTCHECK  (§25 "Validation immediately after write"):
  python -c "from pcae.core.hatp_mandatory_certification import \
    load_certification, validate_active_hatp_mandatory_independent_ \
    verification_certification; ..."  # read-only inspection only,
    confirming the new record and confirming no active binding exists
```

No generic shell; no open-ended `sudo sh -c`. Every line above is a
fixed, individually-auditable invocation, using the existing, real,
frozen `scripts/hatp_certification_admin.py` entrypoint — not a new
tool this phase invents.

**Standalone-script asymmetry confirmed this phase (bears on §10, §24):**
`ls scripts/` contains exactly `hatp_certification_admin.py` and
`hatp_deployment_binding_admin.py`. No `hatp_hardware_credential_admin.py`
or `hatp_principal_signer_admin.py` script exists under `scripts/`,
though their underlying library modules exist under `src/pcae/core/`.

---

## 30. Idempotency / Existing State (§30 of Governing Prompt)

If a `CertificationRecord` for this exact `(repository_instance_id,
canonical_deployment_root)` key already exists at future-phase entry
(it does not today, §1/§7): the tool's create-once discipline
(HMIC-REQ-084) fails the write if a record with the same
`certification_id` already exists with *different* authority-sensitive
values, and treats identical-content resubmission as the concurrency
rule governs (§32/HPSE-analog). No silent overwrite; no duplicate mint.
The future phase MUST re-derive the current tuple fresh and compare
against any existing record before invoking `create`, treating an
unexpected pre-existing record as a reconciliation case requiring
operator review, not an auto-skip.

---

## 31. Failure / Interruption (§31 of Governing Prompt)

Reliance is entirely on the existing writer transaction/locking
semantics already in production: `_certification_transition_lock`
(mutual exclusion), `mkstemp`+`fsync`+`os.replace` atomicity
(HMIC-REQ-083), and `_read_back_and_verify`-equivalent read-back checks.
A crash mid-write leaves the prior document intact (no partial document
is ever observable, by construction). A post-validation failure (the
§25 postcheck reads back the wrong record, or `VALID` unexpectedly
appears) MUST halt the future phase and require operator review — not be
guessed at from file timestamps or "latest" heuristics (explicitly
prohibited, HMIC-REQ-085).

---

## 32. Rollback / Revocation (§32 of Governing Prompt)

`scripts/hatp_certification_admin.py revoke --certification-id <id>`
(HMIC-REQ-091-093) field-mutates the record's `status` to `"revoked"`
and sets `revoked_at` — never deletes, never un-revokes (monotonic per
record). This is the correct, contract-defined rollback mechanism for
the selected operation; no destructive rollback (deletion) is invented.
Not exercised by this phase (§25's envelope authorizes `create` only;
`revoke` is available to a future phase if the created record must be
withdrawn, but that is itself a separate, explicit act with its own
authorization, not automatically bundled here).

---

## 33. Evidence Required (§33 of Governing Prompt)

- **Before:** host identity (2J §4/§21 re-check output); source identity
  (36/7 pre-write snapshot); current `certifications.json`/
  `certification-bindings.json` state (expected: both absent or empty
  for this repository key); Protected Root state (2J §7 precheck
  output).
- **During:** exact `create` invocation (redacted of no secrets — no
  secret material is involved in this ceremony); actor (`certified_by`
  string); tool-derived tuple as presented for confirmation; human
  confirmation record.
- **After:** the newly written `CertificationRecord` (full field set,
  §5 schema); `certification_id`; independent re-parse/self-consistency
  check (HMIC-REQ-040, re-derive `certification_id` from stored fields);
  current `certifications.json` document state; explicit confirmation
  that `certification-bindings.json` is byte-unchanged (no adjacent
  record written) — the specific "no unauthorized adjacent record" proof
  the governing prompt's §33 requires.
- No secrets are involved in this ceremony (no cryptographic key
  material, no password) — nothing here to redact beyond the ordinary
  `certified_by` identity string, which is not itself secret.

---

## 34. Following DAG Node (§34 of Governing Prompt)

Immediate successor after a successful, real HMIC certification
`create`: the pending `activate` step (a separate, explicit ceremony,
§8/§25) — **not** authorized by this phase or its recommended successor.
Independently, the FIDO2/hardware-credential branch (§22's parallel
branch) remains available to pursue concurrently or afterward, gated on
resolving §10's two named gaps (device presence, admin script). Neither
successor is authorized here (§43).

---

## 35. Phase-Local Testing (§35 of Governing Prompt)

`tests/test_phase_149o_20l_7o_2k_hatp_prerequisite_dag_correction_and_next_real_effect_node_selection.py`
mechanically confirms: Protected Root state-correction language is
present and consistent with 2J; HMIC 36/7 counts (source files +
contract_versions) match current production source; `certifications.json`/
`certification-bindings.json`/`hardware-credentials.json`/`registry.json`
principal/signer state is exercised via zero-record fixture assumptions,
not asserted against live host files (none exist in-repo); the corrected
DAG document text and no-cycle claim are present; the selected node
(certification) is named exactly once and FIDO2 is explicitly named
rejected; the standalone-script asymmetry (`scripts/` contents) is
confirmed; no production source changed since phase entry (`git diff`
differential). This is a focused evidentiary suite, not a production
orchestration engine — no certification/enrollment ceremony is invoked
by any test.

---

## 36. Regression (§36 of Governing Prompt)

No production behavior changes. Confirmed this phase: HMIC remains v1.6,
36/7 (§12); HBDC remains v1.2; Protected Root source/config unchanged
(`hatp_bootstrap.py` untouched); Class-B verifier unchanged
(`hatp_class_b_conformance.py` untouched); Trust-Enrollment unchanged
(`hatp_hardware_credential_admin.py`, `hatp_principal_signer_admin.py`,
`hatp_fido2_provider.py` untouched); readiness unchanged
(`hatp_mandatory_cutover.py` untouched); runtime unchanged. Fast Green
run and cited honestly in the final report (§14 of the governing prompt),
raw outcomes preserved separately from the attributable delta, mirroring
2J's own git-stash differential discipline.

---

## 37. No-Go — All Honored, None Performed (§37 of Governing Prompt)

This phase did not: SSH-mutate hac-dell; alter Protected Root; create
certification; activate certification; touch FIDO2 hardware; create a
`HardwareCredentialRecord`; create a Principal; create a Signer; create
a `DeploymentBinding`; wire readiness; activate HATP; change Permission
Broker; change runtime capability; perform PIV work; touch Stream B.

---

## 38. Verdict (§38 of Governing Prompt)

**A: HMIC CERTIFICATION SELECTED AS NEXT REAL-EFFECT NODE —
AUTHORIZATION ENVELOPE FROZEN — NOT EXECUTED.**

---

## 39. Governance (§39 of Governing Prompt)

Used governed PCAE lifecycle only (`pcae task new`/`close`, `pcae
commit`, `pcae phase complete`, `pcae push`) — no raw `git commit`/`git
push`, no `--no-verify`, no force push, no hook bypass, no lifecycle
bypass. Pre-finalization checks (`pcae health`, `pcae check`, `pcae
status coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae
runtime inspect`, `pcae notify status`) run and recorded honestly in the
final report, not assumed.

---

## 40. Findings

**Finding 2K-1 (non-Blocking, contract self-disclosure noted, not
repaired here — out of this phase's narrow scope):** HMIC-001 v1.6's own
status header reads "PENDING INDEPENDENT VERIFICATION (not VERIFIED at
v1.6)." §7/§33 of this document classify this as evidentiary/non-blocking
per HMIC-REQ-072's own explicit text (the referenced verification record
is never itself a validity condition). A future phase MAY choose to
close this disclosure with a dedicated 149O.19-class verification pass
before invoking §25's envelope, as good practice, but this document finds
no contract clause making that a hard prerequisite to `create`.

**Finding 2K-2 (non-Blocking, named for a future phase, not repaired
here):** No standalone `scripts/hatp_hardware_credential_admin.py` or
`scripts/hatp_principal_signer_admin.py` entrypoint script exists,
despite their underlying library writers (`register_credential`,
`enroll_principal`/`enroll_signer`) being real, implemented production
code. This is the concrete, evidence-based reason FIDO2 enrollment is
not selected as this phase's next node (§24), independent of the
device-presence gap. A future phase authorizing FIDO2 enrollment as its
own next real-effect node would need to either author this script first
(mirroring `hatp_certification_admin.py`'s pattern) or explicitly justify
direct library invocation as compliant with this repository's own
admin-tooling discipline — neither is decided here.

No other Blocking finding was identified: the DAG is acyclic (§23); the
selected node's every predecessor is independently verified satisfied
(§7, §24); no unauthorized coupling was found between certification and
either Class-B or Trust-Enrollment state (§6, §13-15).

---

## 41. Recommended Next Phase (§43 of Governing Prompt)

The narrow real-effect phase corresponding only to the node selected
here: **HMIC CertificationRecord creation** (`create` only, per §25's
frozen envelope) — not named with a specific future phase ID by this
document (per the governing prompt's own §43 instruction not to
pre-name it). That phase must independently obtain Protected Admin
Authority's fresh election and confirmation before invoking
`scripts/hatp_certification_admin.py create`, and must re-run this
phase's §21/§29 read-only prechecks fresh at its own entry rather than
reusing this document's tables uncritically (§28).

Not started, not authorized by this phase.
