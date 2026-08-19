# Phase 149O.20L.7O.2I — HATP Remaining-Prerequisite State and Sequencing Reconciliation

**Type:** ANALYSIS / RECONCILIATION ONLY. No certification, provisioning,
enrollment, DeploymentBinding, Protected Root, readiness/contract wiring,
activation, Permission Broker, or runtime change was performed by this
phase.

**Entering state:** HMIC-001 v1.6, FROZEN, repair complete
(149O.20L.7O.2H.2), independent verification VERIFIED WITH NON-BLOCKING
FINDINGS (149O.20L.7O.2H.3). Runtime: Observed / observe / unavailable
(unchanged throughout, confirmed by `pcae runtime inspect`). Non-Blocking
finding carried in: `NB-149O.20L.7O.2H.3-1` — repository memory
self-contradicts on CBV-S10 status.

## 1. CBV-S10 reconstruction (resolves NB-149O.20L.7O.2H.3-1)

CBV-S10 is one of the twelve `CBV-S1..S12` Class-B architectural stop
conditions catalogued by the 149O.20H Class-B implementation plan. It
names the gap: the Full-HBDC Class-B deployment-conformance verifier
existed but was **not wired into the production HATP activation-readiness
calculation** (`_assess_hatp_mandatory_activation_readiness_at_root` in
`src/pcae/core/hatp_mandatory_cutover.py`), i.e. a readiness-contract /
production-integration gap, not an implementation-existence gap.

Reconstructed history, read directly from `PROJECT_STATUS.md` in
chronological (top-newest) order and cross-checked against `git log` for
`src/pcae/core/hatp_mandatory_cutover.py`:

- **149O.20L.1/1A/1B/2** — HMRC-001 amended v1.0→v1.1, adding
  HMRC-REQ-086–100 (§19A), the eighth ("Full-HBDC Class-B deployment
  conformance") readiness prerequisite, contract-only; CBV-S10 stated
  OPEN throughout ("readiness contract/integration gap").
- **149O.20L.3** (commit `e2ccb7a3`) — production wiring: added
  `class_b_conformance_status_satisfies_readiness` and the eighth
  `HATPMandatoryActivationReadinessCheck` term
  (`class_b_deployment_conformance_satisfies_readiness`), joined into the
  same `checks`/`unmet_reasons`/`ready = len(unmet_reasons) == 0`
  conjunction as the pre-existing seven terms, additive-only
  (`+51/-0`). CBV-S10 explicitly left **OPEN — INDEPENDENT PRODUCTION
  VERIFICATION PENDING** by this phase's own report.
- **149O.20L.4** — independent verification of the L.3 wiring: 18 closure
  criteria (closed-enum mapping, fail-closed on exception, no
  caller-override parameter, single-constructor/single-caller AST
  confirmation, TOCTOU/reverse-TOCTOU, real unmocked host call, byte
  identity of the three Class-B verifier modules and
  HMRC-001/HMIC-001/HBDC-001) all independently satisfied, no Blocking
  defect. Verdict recorded verbatim: **"`CBV-S10`: INDEPENDENTLY CONFIRMED
  CLOSED AT READINESS CONTRACT + PRODUCTION INTEGRATION BOUNDARY."**
  Explicitly scoped: this closure does **not** extend to
  deployment/provisioning/activation — Class-B stays NOT PROVISIONED,
  HATP stays NOT READY on the real host.
- **149O.20L.5 through 149O.20L.7O.2H.3** (Class-B provisioning
  authorization/planning, then an unrelated HMIC/Trust-Enrollment/signing
  work stream) — none of these phases touched
  `hatp_mandatory_cutover.py`, `hatp_class_b_conformance.py`,
  `hatp_class_b_topology_verifier.py`, `hatp_mandatory_certification.py`,
  or HMRC-001; each says so explicitly in its own report ("Class-B
  verifier files ... remain bound and unchanged"). Their own boilerplate
  no-go sections, however, kept **restating "CBV-S10 remains OPEN,
  untouched"** as an unreviewed carry-forward phrase rather than
  re-deriving status from the (already-closed) L.4 record — this is the
  literal mechanism that produced `NB-149O.20L.7O.2H.3-1`.

**Verification performed by this phase:** confirmed by direct source read
(§ above, line numbers `hatp_mandatory_cutover.py:936-975`) that the
eighth Class-B term is still present, still joined into the same
`unmet_reasons` conjunction, still calls
`verify_class_b_deployment_conformance()` fresh/uncached with fail-closed
exception handling, and that no commit has touched this file since
`e2ccb7a3` (149O.20L.3) — `git log` shows no intervening commit.

**Disposition: CBV-S10 — INDEPENDENTLY CONFIRMED CLOSED AT READINESS
CONTRACT + PRODUCTION INTEGRATION BOUNDARY (unchanged since 149O.20L.4;
never regressed).** This is a narrow, boundary-scoped closure: it means
the production readiness calculation *correctly includes* the Class-B
term. It does **not** mean Class-B is provisioned, a DeploymentBinding
exists, HATP is certified, or the real host is ready — those remain
separate, independently-tracked, still-open prerequisites (see §§3, 6,
7). `NB-149O.20L.7O.2H.3-1` is resolved: the "OPEN" restatements in
149O.20L.5 through 2H.3 were stale unreviewed boilerplate, not a real
regression or reopening; there is no primary-source or production
evidence of any reopening event.

## 2. HMIC certification state

HMIC-001 is v1.6, FROZEN (repair complete, independently verified with
non-blocking findings at 2H.3). It defines the closed-schema
`CertificationRecord` and the `_CONTRACT_VERSIONS_REQUIRED_KEYS`/
`_CONTRACT_IDENTITY_FILES` seven-contract-identity binding (HATP, HBDC,
HHCE, HMRC, HPSE, HSCE, RAE) plus the 36-member (27 `src/pcae/`-relative +
9 repository-root-relative) frozen authority-bearing source set.

No `certifications.json`, `certification-bindings.json`, or any active
certification pointer/revocation record exists anywhere in the tracked
repository (confirmed by exhaustive filename search; only a JSON
**schema** file exists at
`src/pcae/schema_resources/cltr_cutover/records/certification.schema.json`,
which is a schema, not a record). What has been repeatedly verified
across phases 149O.19–2H.3 is **source identity** (the 36-member
frozen-file set / 7-member contract-version derivation) — this is a
precondition a future certification record would need to match, not a
certification itself. **No HMIC certification of any kind currently
exists.**

## 3. Class-B / HBDC state

HBDC-001 is v1.2 (bound, content+version, into HMIC's seven-contract
identity). The Class-B verifier island
(`hatp_class_b_topology_verifier.py`, `hatp_class_b_conformance.py`, plus
the environment-lock module) is implemented, HMIC-source-bound, and wired
into readiness (§1). `verify_class_b_deployment_conformance()` is the
sole authoritative call site; repeated phases (149O.20L class + 2J/2K
series) reconfirmed zero alternate callers/consumers outside this island
plus the one readiness call site.

No real host currently satisfies Class-B `COMPLIANT` — every real,
unmocked host call recorded across 149O.20L.3/.4/.class analysis returned
`NON_COMPLIANT`/`ready=False`. No DeploymentBinding-producer output
exists (no DeploymentBinding record found anywhere in the repository).
Class-B participates in readiness (§1) but not yet in any certification
or activation record, because no such record exists at all (§2).

## 4. Trust-Enrollment state (HHCE-001 / HPSE-001 / HSCE-001)

- **HHCE-001** (Hardware Credential Enrollment) v1.1 — content+version
  HMIC-bound (149O.20L.7O.2H). Implementation: FIDO2 provider
  (`hatp_fido2_provider.py`) and hardware-credential admin
  (`hatp_hardware_credential_admin.py`) exist and are HMIC-bound;
  independently verified through 2F.2/2F.3/2F.5 (durable-registry signer
  resolution, TOCTOU repair). No real `hardware-credentials.json` or any
  hardware credential record exists (confirmed absent by filename
  search).
- **HPSE-001** (Principal/Signer Enrollment) v1.1 — content+version
  HMIC-bound. Implementation (`hatp_principal_signer_admin.py`) exists,
  independently verified (2D.1/2D.3). No real Principal or Signer record
  exists.
- **HSCE-001** (Signing Ceremony + Evidence Store) v1.3 — content+version
  HMIC-bound (was already correctly bound before the 2G/2H work; 2G
  confirmed no gap). Implementation (`hatp_signing_ceremony.py`)
  independently verified through 2F.2–2F.5 (durable-registry signer
  resolution selected as Model B over authenticator rediscovery).

All three contracts and their implementations are independently
verified at the **implementation boundary**. HMIC's own call-graph
analysis (2G) confirmed none of these three modules is reached by any
of HMIC's three existing closure limbs except the newly-added limb (d)
(dual-anchor: `production_sign_rollback_evidence` reachability +
non-reachability of the admin writers) — i.e., HMIC source-binds these
files but does not itself call into or execute enrollment. **No real
enrollment state (Principal, Signer, hardware credential, or
DeploymentBinding) exists anywhere in the repository** — confirmed
absent by exhaustive filename search, consistent with every phase's own
no-go confirmation.

## 5. Certification vs Trust-Enrollment ordering

HMIC certification's closed schema (`CertificationRecord`,
`_CONTRACT_VERSIONS_REQUIRED_KEYS`) validates **contract-version
identity of the seven bound contracts and byte/digest identity of the
36-member frozen source set** — a static/source-identity concern. It
does not read or depend on any Principal/Signer/hardware-credential/
DeploymentBinding *record content*; HHCE-001/HPSE-001/HSCE-001 are bound
to HMIC only as **source files**, not as runtime state HMIC certification
consumes. Certification therefore validates that Trust-Enrollment
**source bytes** are the frozen, verified version — not that any actual
trust has been enrolled. HMIC certification does not require a
DeploymentBinding to exist (no code path constructs or reads one during
certification). DeploymentBinding creation is a distinct producer chain
(Class-B / HHCE / HPSE modules) and does not require a prior HMIC
`VALID` certification state in production source (no such check found in
the admin/producer modules). Enrollment (writing Principal/Signer/
hardware-credential/DeploymentBinding records) mutates only protected
runtime/data-layer files, never the HMIC-bound source files themselves —
so enrollment cannot desynchronize an existing certification's
source-identity check.

**Safe sequence implied by evidence:** certification (source-identity
attestation) and Trust-Enrollment (real record creation) are
**independent, non-blocking-on-each-other** axes; certification could in
principle be created before or after enrollment without invalidating
either, since neither reads the other's state. Readiness (§1, §13)
is the axis that *does* depend on enrollment-adjacent state (Class-B
conformance) but not on certification.

## 6. DeploymentBinding prerequisites

From the HHCE-001/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md producer chain:
DeploymentBinding requires a RepositoryIdentity, a canonical deployment
root, an enrolled Principal, an enrolled Signer, a provider profile
(FIDO2), a hardware credential record bound to that Signer, and Class-B
conformance context for the target host. It is a **consequence of**
Principal/Signer/hardware-credential enrollment plus Class-B conformance
evidence — not a prerequisite to certification (§5) and not itself
required by readiness's Class-B term (`verify_class_b_deployment_
conformance` evaluates host topology/environment-lock directly, not a
stored DeploymentBinding record). Protected Root state and host topology
are inputs to Class-B conformance, which is in turn an input to
DeploymentBinding — so DeploymentBinding sits downstream of both
enrollment and Protected Root/Class-B evidence.

## 7. Real host (hac-dell) state

No SSH or mutation performed by this phase (prohibited). Using only
canonical repository evidence carried forward from prior real,
unmocked host calls (149O.20L.3/.4, most recent dated calls in this
work-stream):

| Item | Classification |
|---|---|
| machine-id `54ff22ce...`, hostname, Ubuntu 24.04.3, RepositoryIdentity `0107866f-...` | HISTORICALLY VERIFIED — FRESH CHECK REQUIRED (identity facts, not expected to drift, but no live re-check performed this phase) |
| Class-B conformance | VERIFIED CURRENT AS OF 149O.20L.4's real unmocked call: `NON_COMPLIANT` |
| Protected Root existence on that host | ABSENT (no host-side provisioning phase has run) |
| Hardware credential / Principal / Signer / DeploymentBinding on that host | NOT YET PROVISIONED |

No fresher real-host evidence exists in the repository than 149O.20L.4;
this phase does not refresh it (would require a live host call, out of
scope for an analysis-only phase and not requested).

## 8. Protected Root prerequisites

Protected Root is a filesystem-topology + OS-permission-bits concern
(`protected_activation_authority_mechanism_available` readiness check,
§13) — logically prior to hardware credential registration, Principal/
Signer enrollment under that root, and DeploymentBinding (§6), because
those write records the root is meant to protect. It is **not** the
same thing as HMIC certification identity (§2, a source/contract
concern) or readiness's other seven terms — it is one specific
readiness term among eight. No Protected Root currently exists on any
tracked evidence path (production code's own fallback detail string
confirms: "protected root does not exist" is the code's documented
behavior when absent).

## 9. FIDO2 vs PIV

HHCE-001 v1.1 implements FIDO2 first; PIV is contractually deferred/
unimplemented (per HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md and
prior 149O.20L.7O.2E's own selection record, "selected FIDO2 as first
provider over PIV"). Readiness's Class-B/HHCE-adjacent terms do not
require a specific provider by name in the readiness calculation itself
— they require Class-B conformance and hardware-credential-admin
availability, both of which are provider-generic call surfaces with
FIDO2 as the currently-implemented concrete provider. No readiness or
certification requirement text found anywhere in HMIC-001, HMRC-001, or
HHCE-001 requires PIV specifically or requires *both* providers.
**Classification: PIV is DEFERRED NON-BLOCKING** — an optional
additional provider, not required for any prerequisite in the current
DAG (§16).

## 10. Human authorization/governance prerequisites

No phase roadmap entry in this repository has ever been treated as
self-authorizing; every real-effect boundary crossed in this
work-stream (e.g., 149O.20L.5/.6/.6A Class-B provisioning
authorization/planning, the Dell redeployment CHGR publication at
149O.20L.7N.2) required a distinct, explicit human-governance act
(`CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`, CHGR records) separate
from and prior to the technical phase performing the effect. This
phase does not perform any real effect, so it requires none, but
records for completeness: certification creation, hardware enrollment,
Principal/Signer enrollment, DeploymentBinding creation, readiness-state
transition, and activation each individually require their own
authorization act under CHGR-001 — none has occurred for any of these
six items as of this phase.

## 11. Permission Broker boundary

HMRC-001 §-referenced text (`HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
lines 83-94, 335-371) is explicit: Permission Broker (`PBPA-001`/
`PBPC-001`) policy meanings and `POL-005` (`ExecutionDisabledRule`) are
**separate, later tracks**, distinct from HATP mandatory-consumption
certification/readiness. `COMP-002` (general runtime execution
capability) is explicitly disclaimed as NOT claimed by HMRC-001. PB/
`POL-005` currently resolves `DENY` because `COMP-002` remains
`not_implemented` — this is a runtime-execution boundary, not a
trust-provisioning boundary. **Certification, readiness, and enrollment
can all progress with PB/runtime unchanged; PB only becomes relevant at
or after activation, when execution capability is what's being gated.**

## 12. Runtime/execution boundary

Derived semantic relationship, from §§1, 11 evidence:

`HATP-ready` (readiness's eight-term conjunction, §1/§13) is
independent of `runtime-capable`/`execution-available` (`COMP-002`/PB).
`HATP-active` (a certification+cutover state that does not yet exist,
§2) would be a prerequisite most contracts treat as necessary but the
evidence shows it is **not sufficient** for execution — `COMP-002` and
PB `POL-005` gate execution separately and later. So the relationship
is: `HATP-ready` and `HATP-active` can both be reached while runtime
stays Observed/observe/unavailable; only a *separate*, later
`COMP-002` implementation phase would make `PB-allow`/
`runtime-capable`/`execution-available` reachable. Certification,
readiness progress, and enrollment in this work-stream do not
themselves flip that boundary.

## 13. Readiness calculation

Production function: `_assess_hatp_mandatory_activation_readiness_at_root`
in `src/pcae/core/hatp_mandatory_cutover.py`, called by
`assess_hatp_mandatory_activation_readiness` and the lock-held
`_write_cutover_transition` re-check. Eight-term conjunction
(`ready = len(unmet_reasons) == 0`):

| Readiness term | Contract req | Producer | Current state | Evidence | Remaining action |
|---|---|---|---|---|---|
| `hatp_substrate_operational` | HMRC-001 | cutover module | evaluated live | code read | none (structural) |
| `mandatory_consumption_implementation_independently_verified` | HMRC-001/HMIC-001 | AG3 verification | evaluated live | code read | none (structural) |
| `production_dependency_provenance_valid` | HMRC-001 | trust-store resolution | evaluated live | code read | none (structural) |
| `class_b_protected_storage_available` | HBDC-001 | storage check | evaluated live | code read | Protected Root not yet provisioned on real host (§8) |
| `hsce_signing_implementation_available` | HSCE-001 | signing ceremony module | evaluated live | code read | none (structural; implementation present) |
| `repository_deployment_identity_valid` | HMRC-001 | RepositoryIdentity | evaluated live | code read | none on repo side; real-host freshness re-check advisable (§7) |
| `protected_activation_authority_mechanism_available` | HMRC-001 §19A precursor | Protected Root stat | ABSENT on real host | §8/§7 | provision Protected Root on hac-dell |
| `class_b_deployment_conformance_satisfies_readiness` | HMRC-001 §19A / HMRC-REQ-086-100 | `verify_class_b_deployment_conformance` | `NON_COMPLIANT` on last real call | §3/§7 | Class-B provisioning on hac-dell |

CBV-S10's own gap (§1) was exactly the omission of the eighth row; it is
now present and independently verified. No further contractually-implied
missing term was found during this reconciliation — no repair/integration
gap beyond what is already tracked in the table above (host-side
provisioning, not code).

## 14. Activation preconditions

From primary contracts (HMIC-001 §31 validator, HMRC-001 cutover gate):
activation requires (a) `ready=True` from §13's eight-term calculation,
(b) a valid `CertificationRecord` matching the current 7-member
contract-version/36-member source-identity set (§2 — does not yet
exist), (c) explicit human authorization for the cutover/activation act
itself (§10 — not yet performed), (d) no active revocation. It does
**not**, per current source, additionally require a DeploymentBinding or
enrolled Principal/Signer as a direct gate condition inside the
readiness/certification code paths inspected — those are inputs to the
Class-B conformance term (§13 row 8) rather than separately-checked
gates.

## 15. Revocation/failure ordering (brief)

Readiness (§13) is **continuously (re-)evaluated** — every assessment
call is fresh/uncached, so certification/Principal/Signer/credential
revocation, DeploymentBinding replacement, host Class-B regression, or
repository-identity change would each immediately flip the relevant term
back to unmet on the next assessment; there is no persisted "once
provisioned, stays ready" state. By contrast, a `CertificationRecord`
(once created, §2) would be a **one-time-provisioned, separately
revoked** artifact — its own revocation state is a distinct check from
the live readiness recomputation. This asymmetry is intentional and
matches the TOCTOU-resistance design independently verified at 149O.20L.4
and 149O.20L.7O.2F.5.

## 16. Prerequisite DAG

Edges cited to contract requirement / production dependency established
above:

```
RepositoryIdentity/canonical root (existing, §7)
        |
        v
Protected Root provisioning on hac-dell (§8, §13 row 7)  <-- NOT DONE
        |
        +--> class_b_protected_storage_available (§13 row 4)
        |
        v
Class-B host provisioning / topology + environment-lock (§3, §7)  <-- NOT DONE
        |
        v
class_b_deployment_conformance_satisfies_readiness (§13 row 8)  <-- currently NON_COMPLIANT
        |
        v
Readiness ready=True (§13, all 8 terms)  <-- NOT YET (rows 4,7,8 unmet)

Hardware credential enrollment (HHCE, §4)  <-- NOT DONE, independent of readiness
        |
        v
Principal/Signer enrollment (HPSE, §4)  <-- NOT DONE
        |
        v
DeploymentBinding (§6)  <-- NOT DONE, consumes Class-B conformance evidence + enrollment

HMIC CertificationRecord creation (§2, §5)  <-- NOT DONE, independent of enrollment/DeploymentBinding,
        |                                        depends only on source-identity (already verified)
        v
Activation gate (§14): ready=True AND valid CertificationRecord AND human authorization AND no revocation
        |
        v
HATP-active (does not by itself unlock execution, §12)
        |
        v
Separate COMP-002 / Permission Broker POL-005 track (§11, §12)  <-- unrelated, later
```

No cycle exists. Certification and Trust-Enrollment/DeploymentBinding
are parallel, mutually-independent branches (§5) that both must
eventually feed Activation (§14) but do not block each other's
internal progress.

## 17. Classification

- **STATIC:** RepositoryIdentity, canonical deployment root, HMIC
  36-member source identity, 7-contract-version set.
- **PROVISIONED (host-side, one-time):** Protected Root, hardware
  credential, Class-B topology/environment-lock conformance.
- **CERTIFIED:** HMIC `CertificationRecord` (does not yet exist).
- **ENVIRONMENTAL (continuously re-evaluated):** Class-B live
  conformance status, substrate operational, dependency provenance,
  Protected Root live permission bits.
- **DYNAMIC:** Readiness `ready` boolean (recomputed every call).
- **AUTHORIZATION:** Human CHGR act per real-effect step (§10) —
  certification, each enrollment step, DeploymentBinding, readiness
  transition, activation, each separately required and none yet
  performed.

## 18. First safe real-effect next phase

From the DAG (§16), the **first unmet node with no unmet prerequisite of
its own** is **Protected Root provisioning on hac-dell** — everything
upstream of it (RepositoryIdentity, canonical root) is already static
and verified; everything downstream (Class-B host provisioning,
enrollment, DeploymentBinding, certification, activation) depends on it
either directly (readiness row 7) or transitively (Class-B storage
check, row 4). No contract/readiness repair gap was found blocking this
— CBV-S10 (§1) is already closed at its own boundary and requires no
further contract or integration repair. Certification (§2) and
enrollment (§4) are independent branches that *could* also proceed in
parallel without a DAG violation, but Protected Root provisioning is
recommended first because it is a shared dependency of the readiness
axis and unblocks the largest number of downstream nodes with the
narrowest single real-effect action. This phase does **not** authorize
combining certify+provision+enroll+bind+activate — each remains an
independently inspectable authority transition per the governing
instruction.

## No-go proof

None of the following occurred in this phase: HMIC certification
creation, certification activation, FIDO2/PIV provisioning, real
hardware credential registration, real Principal enrollment, real
Signer enrollment, real DeploymentBinding creation, hac-dell/Protected
Root mutation, SSH to hac-dell, readiness contract/integration change,
HATP activation, Permission Broker change, runtime capability change.
Verified: `git status` reports only the analysis/status files listed in
this phase's completion metadata; `verify_class_b_deployment_conformance`
and all production HATP modules are byte-unchanged since phase entry
(`git diff` against phase-entry commit for `src/` and `docs/contracts/`
is empty except this new analysis document). Runtime confirmed unchanged
via `pcae runtime inspect` (Observed / observe / unavailable).

## Recommended next phase

**149O.20L.7O.2J — HATP Class-B Real Host Protected Root Provisioning
Authorization** (or equivalently-named authorization/planning phase for
the §18 first safe real-effect step). Not begun by this phase.
