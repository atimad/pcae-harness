# HATP Mandatory Rollback Consumption Contract

**Contract ID:** HMRC-001
**Version:** 1.0
**Status:** FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION (not VERIFIED)
**Frozen by:** Phase 149O.15
**Depends on (unamended, byte-unchanged):** HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0, RWMPC-001 v1.0, PBPA-001 v1.0, PBPC-001 v1.2
**Selected architecture source:** `docs/PHASE_149O_14_HATP_AG3_AG5_MANDATORY_PRODUCTION_CONSUMPTION_ARCHITECTURE.md`

This is a **contract-freeze document**. It normatively freezes the shape
of a future implementation. It implements nothing. No `src/pcae/**`
file, and no other contract file, was modified to produce this
document.

---

## 0. Contract Identity and Status

HMRC-001 is a new, standalone contract. It does not amend HATP-001,
HSCE-001, RAE-001, RWMPC-001, PBPA-001, or PBPC-001. It **consumes**
those contracts' existing, frozen, unmodified guarantees and defines
the one remaining seam they leave open: how signed HATP rollback
evidence becomes the **mandatory**, exclusive source of human-approval
authority at the real AG3/AG5 effect boundary, and how a deployment
migrates from today's legacy authority to that mandatory authority
without ever creating a window of dual (OR) authority.

Naming rationale: the repository's existing convention pairs a
descriptive acronym with a numeric contract ID (HSCE-001, HATP-001,
RAE-001, PBPA-001, PBPC-001, RWMPC-001). "HATP Mandatory Rollback
Consumption Contract" (**HMRC-001**) was selected over "HATP Production
Consumption Contract" (candidate HPC-001) because the scope is
specifically rollback (AG3/AG5), not general production consumption of
HATP evidence for other future operation classes; a narrower, precise
name avoids implying an all-operations scope this contract does not
have.

---

## 1. Normative Language

SHALL / SHALL NOT / MUST / MUST NOT express mandatory requirements.
MAY expresses a genuinely open implementation choice. Every requirement
carries a stable ID: `HMRC-REQ-###`.

---

## 2. Purpose

Freeze a normative contract governing:

```
signed HATP evidence
  → explicit evidence selection (evidence_id, caller-supplied, no default)
  → canonical evidence loading (HATPEvidenceStore.load)
  → fresh current-state HATP verification (verify_hatp_proof, via the
    existing gated RAE/HATP adapter)
  → gated RAE/HATP approval derivation (existing, unmodified)
  → Permission Broker request/decision (existing, unmodified policy)
  → mandatory effect-boundary enforcement
```

for AG3 (`pcae remote rollback execute` → `execute_rollback` →
`_run_git_revert`) and AG5 (`pcae rollback --per-id` →
`build_rollback_execution` → real file write/unlink loop), together
with a protected, one-way migration path from legacy authority to
HATP-mandatory authority.

**HMRC-REQ-001.** This contract SHALL govern only the mandatory
consumption of already-existing, already-frozen HATP rollback evidence
for real AG3/AG5 rollback authority/effect attempts. It SHALL NOT
govern any other operation class.

---

## 3. Scope

**HMRC-REQ-002.** This contract does NOT own, and SHALL NOT redefine:
the signing ceremony or evidence-store schema (HSCE-001); proof
cryptography, verification algorithm, freshness, revocation, or binding
semantics (HATP-001); RAE Decision/Binding semantics (RAE-001); PB
policy meanings, POL-004/POL-005 rules, or decision vocabulary
(PBPA-001/PBPC-001); general runtime execution capability (COMP-002);
or repository-wide mutation coverage classification beyond what
RWMPC-001 already establishes for `EXECUTION_CLASS_ROLLBACK`.

**HMRC-REQ-003.** This contract references those frozen authorities by
exact existing function/class name. It SHALL NOT introduce a
duplicate, parallel implementation of any of them.

**HMRC-REQ-004.** This contract governs mandatory rollback authority
*consumption* only. It does NOT establish general runtime execution
capability. `COMP-002` remains a separate, later track. `POL-005`
remains unchanged.

---

## 4. Terminology

**HMRC-REQ-005.** The following terms are frozen for this contract and
any future implementation/verification phase that cites it:

| Term | Meaning |
|---|---|
| **Evidence ID** | The 64-lowercase-hex locator string identifying one `HATPSignedEvidenceEnvelope` (HSCE-001 §17/§25). A locator only — never itself an authority fact (MC-1). |
| **Signed Evidence Envelope** | `HATPSignedEvidenceEnvelope`, HSCE-001's existing, unmodified persisted evidence artifact. |
| **Consumption Attempt** | One evaluation, at one real or attempted AG3/AG5 effect boundary crossing, of the full chain in §9. Every attempt is independent; none trusts a prior attempt's result (MC-2/MC-3). |
| **Consumption Mode** | The deployment's current position in the Cutover State Model (§13): `LEGACY_COMPATIBLE`, `PREPARED`, or `HATP_MANDATORY`. |
| **Legacy-Compatible Mode** | `LEGACY_COMPATIBLE` — see §14. |
| **Prepared Mode** | `PREPARED` — see §15. |
| **HATP-Mandatory Mode** | `HATP_MANDATORY` — see §16. |
| **Mandatory Consumption Boundary** | The point, inside `execute_rollback`/`build_rollback_execution` themselves, immediately preceding the real effect call, at which the full chain in §9 is evaluated and its result gates the effect (§18/§19). |
| **Approval Fact** | The boolean `approval_present`, derived by the existing RAE/HATP conjunction (§11). An input fact, never itself a permission or execution decision (RAE-001 §4, restated here). |
| **Permission Decision** | The Permission Broker's `ALLOW` / `DENY` / `HUMAN_REVIEW` result for one request (PBPA-001/PBPC-001, unmodified). |
| **Effect Boundary** | The exact call site of the real mutation: `_run_git_revert(...)` for AG3; the real `write_text`/`write_bytes`/`unlink` loop over `file_plan` for AG5. |
| **Cutover Record** | The protected, admin-owned artifact recording current Consumption Mode for one repository/deployment instance (§17). |
| **Protected Activation Authority** | The Class-B protected administrative/bootstrap authority — never an agent, ordinary CLI caller, or repository-writable state — that alone may move a deployment `PREPARED → HATP_MANDATORY` (§16, §22). |

**HMRC-REQ-006.** "Approval" SHALL NOT be used informally in any future
implementation to mean any of: evidence existence, evidence validity,
`approval_present`, or PB `ALLOW`. These four are distinct and ordered
per §5.

---

## 5. Semantic Walls (Normative)

**HMRC-REQ-007.** The following distinctions are frozen and SHALL NOT
be collapsed by any future implementation, log message, status field,
or user-facing text:

```
evidence exists         ≠  evidence valid
evidence valid          ≠  approval_present
approval_present        ≠  PB ALLOW
PB ALLOW                ≠  capability (real execution ability)
capability               ≠  executed (actually performed)
signing                 ≠  consumption
consumption              ≠  execution
cutover mode             ≠  substrate readiness
```

---

## 6. Evidence Reference Syntax

**HMRC-REQ-008.** The canonical CLI flag for supplying an evidence
locator on both AG3 and AG5 is exactly:

```
--hatp-evidence-id <evidence_id>
```

**HMRC-REQ-009.** No alias (`--hatp-evidence`, `--evidence-id`,
`--evidence-file`, or any other spelling) SHALL be added. Exactly one
canonical flag exists, on both operation families, identically named.

**HMRC-REQ-010.** `<evidence_id>` SHALL conform exactly to HSCE-REQ-056
(HSCE-001 §25): a 64-character, all-lowercase hexadecimal string,
rejected before any filesystem path is constructed if it contains
`../`, `/`, `\`, whitespace, uppercase hex characters, a partial-length
digest, or any other non-conforming character. This contract does not
redefine that domain; it references it.

---

## 7. AG3 CLI Target

**HMRC-REQ-011.** Based on the current real command grammar
(`pcae remote rollback execute <job_id> [--json]`, `cli.py:4174-4188`),
the frozen future AG3 syntax is:

```
pcae remote rollback execute <job_id> --hatp-evidence-id <evidence_id> [--json]
```

`<job_id>` remains the existing required positional argument. `--json`
remains available if and only if the current command already supports
it (it does). No other flag is added.

---

## 8. AG5 CLI Target

**HMRC-REQ-012.** Based on the current real command grammar
(`pcae rollback --per-id <per_id> [--dry-run] [--json]`,
`cli.py:3036-3055`), the frozen future AG5 syntax is:

```
pcae rollback --per-id <per_id> --hatp-evidence-id <evidence_id> [--dry-run] [--json]
```

`--dry-run` and `--json` remain available exactly as today (both
already exist). No other flag is added.

---

## 9. Canonical Load and Consumption Chain

**HMRC-REQ-013.** The evidence ID has no authority meaning by itself
(MC-1). A syntactically valid-looking digest is never treated as
approval.

**HMRC-REQ-014.** Implicit evidence selection is prohibited absolutely.
No future implementation SHALL provide, by any name, a "latest",
"newest", "first", "only one found", "most recent", glob-based, or
operation-inferred evidence lookup on any mandatory-consumption path.
An `evidence_id` SHALL always be supplied explicitly by the caller.

**HMRC-REQ-015.** The sole canonical loader is `HATPEvidenceStore.load
(evidence_id) -> HATPSignedEvidenceEnvelope` (HSCE-001 §5, already
implemented, unmodified). Mandatory-consumption production code SHALL
NOT: open an arbitrary path itself; parse arbitrary external evidence
JSON; or accept an envelope constructed by the caller instead of loaded
by the store.

**HMRC-REQ-016.** The canonical loaded object is exactly
`HATPSignedEvidenceEnvelope`. No raw proof file path, no inline proof
JSON, and no caller-constructed envelope is ever a valid production
canonical form.

**HMRC-REQ-017.** The full mandatory consumption chain, evaluated fresh
on every Consumption Attempt, is exactly:

```
1. explicit evidence_id (caller-supplied, HMRC-REQ-010 domain-checked)
2. HATPEvidenceStore.load(evidence_id)          -> HATPSignedEvidenceEnvelope
3. resolve_rollback_approval_evidence_with_hatp(...)   [existing, unmodified]
     -> resolve_rollback_approval_evidence(...)  (RAE-001, unmodified)
     -> verify_hatp_proof(...)                   (HATP-001, unmodified)
     -> Decision/Binding digest cross-check       (existing, unmodified)
     -> inspect_hatp_verification_substrate_readiness(...)  (existing, unmodified)
     -> approval_present: bool                    (existing 3-term AND, §11)
4. build_permission_broker_request(...)           [existing shape, §12]
5. PermissionBroker().evaluate(request)           -> ALLOW | DENY | HUMAN_REVIEW
6. Effect-Truthful PB Requirement gate (MC-14, §12)
7. only then: the real effect boundary
```

No alternate chain exists. Raw proof/evidence objects never enter this
chain directly on a mandatory-consumption path.

---

## 10. Load Errors and Verification Status — Fail-Closed Enumeration

**HMRC-REQ-018.** Every one of the following SHALL fail closed, with no
production caller able to distinguish "evidence problem" from
"authorization denied" in a way that grants the effect:

- missing evidence (`EvidenceNotFoundError`)
- invalid evidence-ID format (rejected before store access, HMRC-REQ-010)
- unsafe path / symlink target for the evidence file (`EvidencePersistenceFailureError`)
- corrupt / malformed envelope (`MalformedEvidenceEnvelopeError`)
- schema-invalid envelope (`InvalidEvidenceEnvelopeSchemaError`)
- digest mismatch between `evidence_id` and envelope content (`EvidenceIdDigestMismatchError`)
- unsupported evidence-envelope version (`UnsupportedEvidenceVersionError`)
- any `HATPVerificationStatus` other than `VALID` (`MISSING`, `MALFORMED`, `INVALID_SIGNATURE`, `UNKNOWN_SIGNER`, `UNAUTHORIZED_SIGNER`, `REVOKED_SIGNER`, `INVALID_ATTESTATION`, `USER_PRESENCE_NOT_PROVEN`, `WRONG_OPERATION`, `WRONG_REPOSITORY`, `WRONG_DEPLOYMENT`, `EXPIRED`)
- RAE result other than `VALID`
- substrate readiness `False`
- any unknown/future verification status value not in the closed vocabulary above

**HMRC-REQ-019.** Post-cutover (`HATP_MANDATORY`), none of the above
SHALL ever fall back to legacy authority. No exception.

**HMRC-REQ-020.** An unknown/future verification status is always
treated as failure, never as success-by-default (fail closed on
unrecognized state).

---

## 11. Approval Derivation — Reuse, No Duplication

**HMRC-REQ-021.** The mandatory-consumption approval fact SHALL be
derived exclusively by the existing, unmodified conjunction already
implemented in `resolve_rollback_approval_evidence_with_hatp` /
`_derive_hatp_gated_approval_present`:

```
approval_present = True  IFF  RAE_result == VALID
                          AND  HATP_status == VALID
                          AND  substrate_readiness.operational == True

approval_present = False  otherwise, including on any internal error
                          (fail-closed)
```

No caller-supplied override of any term in this conjunction exists or
may be added.

**HMRC-REQ-022.** This contract does not duplicate RAE verification,
Decision/Binding digest comparison, operation mapping, freshness,
revocation, or substrate-readiness logic. It reuses the existing
engine unmodified.

**HMRC-REQ-023.** The derived `approval_present` boolean SHALL remain
local to the authority adapter (`hatp_ag_authority.py`) and its
immediate PB-request construction. No generic, reusable
`approved=True` capability SHALL be exposed to any other caller.

---

## 12. Permission Broker Handoff and the Real-Effect/PB Relationship

**HMRC-REQ-024.** Permission Broker remains the sole permission-decision
owner. HATP/RAE derive only the human-approval input fact
(`approval_present`); they never decide `ALLOW`/`DENY`/`HUMAN_REVIEW`
directly.

**HMRC-REQ-025.** The mandatory-consumption PB request SHALL reuse the
existing shape already implemented by `hatp_ag_authority.py`:
`action_type=ACTION_ROLLBACK`, `execution_class=EXECUTION_CLASS_ROLLBACK`,
`requested_component="COMP-008"`, `evidence_available=True`,
`approval_present=<derived fact>`. This contract does not redesign PB
policy or RWMPC-001's classification of AG3/AG5 as
`EXECUTION_CLASS_ROLLBACK`.

**HMRC-REQ-026.** If PB returns `HUMAN_REVIEW`, the effect SHALL NOT
proceed past the Mandatory Consumption Boundary, even if HATP
verification was `VALID`.

**HMRC-REQ-027.** If PB returns `DENY`, the effect SHALL NOT proceed.

**HMRC-REQ-028.** PB `ALLOW` alone satisfies the permission-decision
term only. It is not, by itself, execution capability, and is not, by
itself, sufficient to cross the effect boundary. See MC-14 (HMRC-REQ-029).

**HMRC-REQ-029 — MC-14, the Effect-Truthful PB Requirement (ETPR).**
This is the highest-risk question this contract resolves, and it is
resolved as follows, adopting the strong security default:

Today, `hatp_ag_authority.py`'s PB request is constructed with
`simulation_only=True` unconditionally. Under `simulation_only=True`,
POL-005 (`ExecutionDisabledRule`) is never triggered, so an `ALLOW` can
result — but PBPC-001 (PBPC-REQ-037) already establishes that *every*
decision under the current runtime posture carries
`implementation_status="execution_unavailable"`, and PBPC-REQ-037A
establishes that a request truthfully marked `simulation_only=False`
resolves `DENY` via POL-005 given the current `Observed/observe/
unavailable` runtime posture. An `ALLOW` obtained under
`simulation_only=True` is therefore a policy-simulation result, not a
truthful representation that the requested rollback mutation is really
about to happen — and per §5's semantic wall, `PB ALLOW ≠ capability
≠ executed`.

**Frozen rule:** once a deployment is `HATP_MANDATORY`, an AG3/AG5
Consumption Attempt SHALL NOT cross the Mandatory Consumption Boundary
into the real effect unless the PB decision was obtained from a request
that **truthfully** represents the attempt as a real, non-simulated
mutation (i.e., `simulation_only=False` for that specific evaluation)
**and** that request resolved `ALLOW`. A `simulation_only=True`
evaluation remains permitted for advisory/diagnostic purposes (e.g.
`PREPARED`-mode rehearsal, dry-run reporting) but SHALL NEVER by itself
authorize crossing the effect boundary once `HATP_MANDATORY` applies.

**Direct consequence (frozen, not deferred to implementation):** under
today's architecture, a truthful `simulation_only=False` rollback
request deterministically resolves `DENY` via POL-005, because
`COMP-002` (Execution Boundary) remains `not_implemented`. Therefore,
**until a genuine, narrowly-scoped, rollback-specific execution-
enforcement capability exists** — distinct from and not requiring full
general-purpose `COMP-002` — a deployment that reaches `HATP_MANDATORY`
cannot obtain a truthful `ALLOW` for any real AG3/AG5 effect, and every
post-cutover real-effect attempt fails closed. This is an accepted,
explicit consequence, not an implementation defect: **`HATP_MANDATORY`
does not guarantee rollback availability** (§16, §22). Rollback effect
becomes available again only once such an enforcement capability is
built and the request is truthfully re-evaluated against it.

**HMRC-REQ-030.** This contract does NOT claim `COMP-002` is
implemented by virtue of MC-14. It names the exact narrow capability it
depends on ("rollback-specific execution-enforcement capability
suitable for a real AG3/AG5 effect") and explicitly does not conflate
it with general runtime execution capability.

---

## 13. Cutover State Model

**HMRC-REQ-031.** Exactly three Consumption Modes exist:
`LEGACY_COMPATIBLE`, `PREPARED`, `HATP_MANDATORY`.

## 14. LEGACY_COMPATIBLE

**HMRC-REQ-032.** Default state for every existing deployment,
including the current local development host. Legacy
`rollback_approval_state`-gated AG3 dispatch and legacy structural-
only AG5 dispatch remain fully operative exactly as implemented today.

**HMRC-REQ-033.** If `--hatp-evidence-id` is supplied in this mode, the
full chain (§9) MAY still be evaluated, but its result is attached as
advisory/diagnostic metadata only (mirroring today's existing
Wave-7-hook additive behavior) and never gates the effect. This
resolves the "pre-cutover evidence ID supplied" question as: evaluate
advisory-only, never authoritative (rejecting both "reject as N/A" and
any authority-bearing interpretation).

## 15. PREPARED

**HMRC-REQ-034.** An intermediate, still fully non-authoritative state:
every activation prerequisite (§22) is satisfied, but Protected
Activation Authority has not yet activated `HATP_MANDATORY` for this
deployment.

**HMRC-REQ-035.** Dispatch behavior in `PREPARED` SHALL be identical to
`LEGACY_COMPATIBLE` (HMRC-REQ-032/HMRC-REQ-033). `PREPARED` SHALL NOT
introduce any additional mandatory evaluation, rehearsal requirement, or
AND-condition beyond `LEGACY_COMPATIBLE`. This is a deliberate
simplicity choice: an OR-authority or AND-authority hybrid model is
explicitly rejected (HMRC-REQ-053).

## 16. HATP_MANDATORY

**HMRC-REQ-036.** Human approval authority for AG3/AG5 real effects
comes exclusively from a successful, fresh Consumption Attempt
(§9) satisfying MC-14 (HMRC-REQ-029). Legacy `rollback_approval_state`
and legacy structural-only AG5 dispatch have zero authority in this
mode. Missing, invalid, or otherwise failing evidence fails closed
(§10). There is no downgrade and no fallback.

**HMRC-REQ-037.** `HATP_MANDATORY` does not guarantee rollback
availability (HMRC-REQ-029). The Protected Activation Authority that
activates this mode explicitly assumes this consequence.

---

## 17. Cutover Transitions and Monotonicity

**HMRC-REQ-038.** The only permitted transitions are:
`LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY`. A direct
`LEGACY_COMPATIBLE → HATP_MANDATORY` transition is forbidden;
`PREPARED` is a required intermediate step.

**HMRC-REQ-039.** No reverse transition (`HATP_MANDATORY → PREPARED` or
`HATP_MANDATORY → LEGACY_COMPATIBLE`, or `PREPARED → LEGACY_COMPATIBLE`)
is available to ordinary runtime, an agent, a CLI caller, an
environment variable, or any repository-writable mechanism. Reversion,
if ever required, requires a separately governed administrative
mechanism outside this contract's scope — this contract does not define
one.

**HMRC-REQ-040 (Monotonicity).** No ordinary agent or runtime action
can cause `HATP_MANDATORY → LEGACY_COMPATIBLE` by deleting or altering
any repository-local state. See §19 for the exact mechanism.

---

## 18. Protected Activation Authority and Cutover Storage

**HMRC-REQ-041.** `PREPARED → HATP_MANDATORY` activation SHALL be
caused only by Protected Activation Authority: the existing Class-B
protected administrative/bootstrap authority already established by
149O.6/149O.7. It SHALL NOT be reachable by: an ordinary agent, a
per-command caller, an environment variable, a CLI force flag, or any
repository-writable configuration file an agent process can edit.

**HMRC-REQ-042.** Activation is always an explicit protected-admin
action. It SHALL NEVER occur automatically merely because activation
prerequisites (§22) become true. Readiness (`PREPARED`) and activation
(`HATP_MANDATORY`) are deliberately decoupled (HMRC-REQ-034).

**HMRC-REQ-043.** The Cutover Record SHALL be stored as a separate,
admin-owned activation record under the existing Class-B protected HATP
trust root — the same protected storage family HATP-001 already uses
for deployment binding and trust-store state. It SHALL NOT be stored
under agent-writable `.pcae/`. (Selected over "extend the protected
deployment-binding record" to keep the mandatory-cutover concern
independently auditable and independently corruptible-without-affecting
deployment-binding integrity.)

**HMRC-REQ-044.** Conceptual schema-owning module for a future
implementation: a new `hatp_mandatory_cutover.py`, distinct from
`hatp_ag_authority.py` (which remains the authority-adapter that
*consumes* the Cutover Record's current mode, not the module that
*owns* its storage/schema). This contract freezes ownership only; it
does not implement either module.

**HMRC-REQ-045 (Cutover Record Schema, v1, closed).** Exactly these
fields, no more:

```
version                    strict positive integer (bool rejected, HMRC-REQ-046)
repository_instance_id      binds to the same repository/deployment
                             identity HATP-001 §17-18 already defines
                             (CRI Model A + protected deployment binding)
mode                        "PREPARED" | "HATP_MANDATORY"
activated_at                 timestamp
activated_by                 protected-authority reference (never an
                             agent identity, never a session/task ID)
```

**HMRC-REQ-046.** `version` SHALL be validated as a strict integer.
A JSON boolean (`true`/`false`) SHALL be rejected as an invalid
`version`, following the same strict-schema hardening pattern already
used elsewhere in this repository's protected-record parsers.

**HMRC-REQ-047.** For `v1`, the schema is closed: unknown fields SHALL
be rejected, not silently ignored. Missing required fields SHALL be
rejected. Duplicate JSON keys SHALL be rejected if the parser can
detect them (mirroring existing strict-schema patterns).

**HMRC-REQ-048.** The Cutover Record applies only to the exact
repository instance/deployment identified by `repository_instance_id`.
A record present but naming a different repository/deployment SHALL be
treated as **not present for this repository** — this SHALL NOT cause
activation of the wrong deployment, and per HMRC-REQ-049 SHALL NOT be
interpreted as proof this repository was never activated either.

**HMRC-REQ-049 (Deletion/Corruption — Monotonicity Mechanism).** If the
Cutover Record is missing, corrupt, or unreadable at consumption time,
implementation SHALL NOT silently treat the deployment as
`LEGACY_COMPATIBLE`. Instead: a genuinely distinguishable, separate,
write-once monotonic marker in the existing Class-B protected
deployment baseline (already used for deployment-binding integrity,
HATP-001 §18) SHALL be consulted:

- If that baseline shows this deployment has **never** activated
  mandatory mode: absence of a Cutover Record is interpreted as
  `LEGACY_COMPATIBLE` (first-install case, HMRC-REQ-050).
- If that baseline shows this deployment **has previously activated**
  mandatory mode (i.e., the monotonic marker is set) and the Cutover
  Record is now missing/corrupt/unreadable: implementation SHALL treat
  the deployment as fail-closed-`HATP_MANDATORY`-equivalent — all
  rollback effects denied — until the record is repaired by Protected
  Activation Authority. It SHALL NEVER downgrade to
  `LEGACY_COMPATIBLE` in this case.

If a future implementation cannot provide this monotonic
distinguishability from a single optional file, it SHALL freeze a
design that can (e.g. a write-once marker set at first `PREPARED→
HATP_MANDATORY` activation, stored independently of the mutable
Cutover Record) before implementation proceeds. This contract does not
implement the marker; it freezes the requirement that one exists.

**HMRC-REQ-050 (First Install).** For a deployment where the monotonic
marker (HMRC-REQ-049) itself is absent, the deployment has never been
activated, and absence of a Cutover Record correctly means
`LEGACY_COMPATIBLE`.

**HMRC-REQ-051.** The Cutover Record file SHALL be admin-owned and
agent-unwritable, consistent with existing Class-B topology, and SHALL
be subject to the same symlink/path-safety checks HATP-001's protected
deployment-binding artifacts already use (no agent-controlled
redirection).

**HMRC-REQ-052.** Every effect attempt SHALL read the current Cutover
Record fresh. No process-long, in-memory, or any-other cache of
Consumption Mode is permitted (mirrors MC-2/MC-3 for evidence
verification).

**HMRC-REQ-053.** No prose in any future implementation of this
contract may express, in effect, `legacy_approved OR hatp_valid`
(dual/OR authority) or a permanent `legacy_approved AND hatp_valid`
requirement that keeps legacy state authority-bearing after cutover.
Legacy structural state may remain present for diagnostics/migration,
but post-cutover human authority comes solely from HATP (HMRC-REQ-036).

---

## 19. Activation Prerequisites

**HMRC-REQ-054.** `PREPARED` requires, at minimum, the conjunction of:

- Class-B deployment valid (existing 149O.6/149O.7 architecture)
- HATP substrate operational (`inspect_hatp_verification_substrate_readiness(...).operational`)
- HSCE signing implementation available (`pcae hatp sign rollback` functional)
- Mandatory-consumption implementation version present and
  independently verified (a future 149O.16-class verification, not
  this contract)
- Production dependency provenance valid
- Protected Activation Authority mechanism available

**HMRC-REQ-055.** Activation to `HATP_MANDATORY` does NOT additionally
require the MC-14 (HMRC-REQ-029) execution-enforcement capability to
exist. Protected Activation Authority MAY activate `HATP_MANDATORY`
while that capability is absent, explicitly accepting the
HMRC-REQ-037/HMRC-REQ-029 consequence that rollback effects will fail
closed until it exists. This avoids creating an impossible deployment
state while keeping the security default (fail closed on real effect)
absolute.

**HMRC-REQ-056.** `PREPARED` is a purely computed/declared readiness
state; it establishes no additional stored authority beyond the
Cutover Record's `mode` field itself (no separate "PREPARED-only"
authority object is introduced).

---

## 20. Legacy Command and Field Disposition

**HMRC-REQ-057 (`pcae remote rollback approve`, pre-cutover).** Retains
its current behavior unmodified: it mutates `rollback_approval_state`
and remains authoritative under `LEGACY_COMPATIBLE`.

**HMRC-REQ-058 (same command, `PREPARED`).** Identical behavior to
pre-cutover (HMRC-REQ-035) — it remains legacy-compatible. It MAY
additionally print a deprecation-warning diagnostic; it SHALL NOT
become, or be treated as, a second HATP authority under any
circumstance.

**HMRC-REQ-059 (same command, post-cutover).** SHALL deterministically
refuse with a distinct, documented deprecation error. It SHALL NOT
mutate `rollback_approval_state` or any other approval-adjacent field.
No silent success. No authority.

**HMRC-REQ-060 (`rollback_approval_state`, pre-cutover).** Retains full
current legacy authority (HMRC-REQ-032).

**HMRC-REQ-061 (`rollback_approval_state`, post-cutover).** Becomes
historical/display/migration metadata only. It SHALL NOT independently
authorize any effect, and SHALL NOT be consulted by the Mandatory
Consumption Boundary at all (HMRC-REQ-036).

**HMRC-REQ-062 (Pending legacy approvals at cutover).** A rollback
approved under `rollback_approval_state == "approved"` before cutover,
but attempted after the deployment reaches `HATP_MANDATORY`, SHALL
require fresh HATP evidence at the moment of the effect attempt.
Authority is evaluated at effect-attempt time, never grandfathered from
an earlier legacy state.

---

## 21. AG3/AG5 Structural Preconditions (Preserved, Unaffected by Cutover)

**HMRC-REQ-063.** Every existing AG3 structural/safety precondition —
job existence, `rollback_eligible`, `rollback_mode_recommendation ==
"revert_commit"`, clean working tree, original-commit-is-ancestor-of-
HEAD — is a structural precondition, distinct from human-approval
authority, and SHALL remain required in every Consumption Mode,
including `HATP_MANDATORY`. HATP validity never substitutes for or
overrides a structural check.

**HMRC-REQ-064.** Every existing AG5 PER-status check
(`per["status"] in {"completed", "partial"}`), `rollback_payload_available`,
ECP resolution, no-in-progress-rollback check, and the divergence
check, is likewise a structural/safety precondition, not a human-
approval authority. All remain required in every Consumption Mode.
Because AG5 has no human-approval gate today at all, `HATP_MANDATORY`
is the first mode in which AG5 gains one — it does not replace or
weaken any existing structural check.

---

## 22. Effect Boundary Placement (Mandatory Gate Location)

**HMRC-REQ-065.** CLI-only enforcement is forbidden. The mandatory gate
SHALL live inside `execute_rollback` and `build_rollback_execution`
themselves, so that a direct function call bypassing any CLI layer is
still gated identically to a CLI invocation.

**HMRC-REQ-066 (AG3 effect boundary).** The gate SHALL be placed inside
`execute_rollback`, after all existing structural preconditions
(HMRC-REQ-063) and immediately before the call to `_run_git_revert`.
No production caller SHALL be able to reach `_run_git_revert` without
passing the Mandatory Consumption Boundary once the deployment is
`HATP_MANDATORY`.

**HMRC-REQ-067 (AG5 effect boundary).** The gate SHALL be placed inside
`build_rollback_execution`, after all existing structural/divergence
preconditions (HMRC-REQ-064) and immediately before the first real
mutation in the `file_plan` write/unlink loop. Because
`build_rollback_execution` currently performs effects unconditionally
once structural checks pass, the gate MUST precede the first
`write_text`/`write_bytes`/`unlink` call, not merely precede a summary
return value.

**HMRC-REQ-068 (Direct-call bypass prevention).** Calling either
effect function directly (bypassing `commands/agent.py`) SHALL still
enforce the applicable Consumption Mode. The CLI (`commands/agent.py`,
`commands/hatp.py`) is only an evidence-ID transport layer; it SHALL
contain no cryptographic or approval-derivation logic of its own
(preserving the current, correct separation of concerns).

**HMRC-REQ-069.** Every production caller of the AG3/AG5 effect
boundary is covered by this contract. A future implementation/
verification phase MUST inventory and independently confirm there is
no additional, un-audited production caller of `execute_rollback` or
`build_rollback_execution`.

**HMRC-REQ-070.** Test seams MAY bypass production dependency
construction (e.g. injecting a fake evidence store) only through
test-specific/internal APIs never reachable from a production callable.
No production-callable API SHALL provide such a bypass.

---

## 23. Old-Hook (Wave-7) Disposition

**HMRC-REQ-071.** The three existing optional Wave-7 parameters on
`execute_rollback` and `build_rollback_execution` receive this exact,
individually frozen disposition:

- **`hatp_evidence_id`** — retained as the canonical mandatory locator
  parameter name. Post-migration, mandatory-mode dispatch requires this
  parameter to be a non-`None`, domain-valid evidence ID, and the full
  chain (§9) derives everything else internally from it. It is no
  longer additive-only/inert once `HATP_MANDATORY` applies (HMRC-REQ-036).
- **`hatp_proof`** — deprecated on every production effect path.
  Forbidden as caller-supplied input once the mandatory-consumption
  implementation lands (any future implementation SHALL remove it from
  the public signature or make it internal/private-only). It never
  becomes, and never was, an independent authority.
- **`hatp_evidence`** — identical disposition to `hatp_proof`:
  deprecated, internal-only at most, forbidden as production caller
  input on the mandatory path.

**HMRC-REQ-072.** Post-migration, the production effect-function public
API SHALL accept exactly `hatp_evidence_id` for evidence reference,
deriving the envelope, verification, approval fact, and PB decision
internally. No parallel raw-object authority path SHALL remain.

---

## 24. Forbidden Caller Inputs (Closed List)

**HMRC-REQ-073.** No future mandatory-consumption effect-function
signature SHALL accept, by any name: a caller-supplied approval boolean
(`approval_present`, `hatp_valid`, `trusted`, `operational`, or
equivalent); a caller-supplied PB decision (`pb_decision=ALLOW` or
equivalent); a caller-supplied cutover mode (`mandatory=True`,
`mode="HATP_MANDATORY"`, or equivalent); a caller-supplied provider or
trust-store override (preserving F-2 closure, unchanged from
HATP-001/RAE-001); or a caller-supplied raw proof/evidence object as an
alternate authority (HMRC-REQ-071).

**HMRC-REQ-074.** Mode is derived exclusively from the protected
Cutover Record (§18), read fresh on every attempt (HMRC-REQ-052).

---

## 25. Consumption Result — No Persistence, No Reuse

**HMRC-REQ-075.** The conceptual internal output of the authority
adapter for one Consumption Attempt is a `RollbackPermissionEvaluation`-
shaped value with fields limited to: `evidence_id`, `hatp_status`,
`pb_decision`, `reasons`. `approval_present` is not additionally
exposed beyond internal diagnostics; if exposed for diagnostics, it
SHALL be documented as valid for that attempt only.

**HMRC-REQ-076.** No Consumption Attempt result is persisted for reuse.
A repeated attempt with the same `evidence_id` SHALL reload and
re-verify from scratch (HMRC-REQ-052, MC-2/MC-3).

**HMRC-REQ-077.** If evidence is deleted, modified, or revoked after a
prior successful Consumption Attempt, a later attempt SHALL fail (or
re-verify against the new state) — no cached success carries forward.

**HMRC-REQ-078.** If two valid evidence IDs exist for the same
operation, the caller SHALL explicitly choose one; no auto-selection
exists. Each, if separately attempted, is independently verified.

**HMRC-REQ-079.** Evidence created and valid before cutover MAY be used
after cutover if it is still fresh, valid, for the correct operation,
and under current trust state at consumption time — cutover itself does
not invalidate cryptographically-current-valid evidence. This is
distinct from, and SHALL NOT be confused with, HMRC-REQ-062's rule that
*legacy approval state* (not HATP evidence) is never grandfathered.

---

## 26. Requirement Inventory — Category Index

For traceability, every requirement above is categorized:

| Category | Requirements |
|---|---|
| Scope | HMRC-REQ-001 – 004 |
| Terminology | HMRC-REQ-005 – 007 |
| Evidence reference | HMRC-REQ-008 – 010 |
| AG3/AG5 CLI | HMRC-REQ-011 – 012 |
| Canonical load / chain | HMRC-REQ-013 – 017 |
| Failure semantics | HMRC-REQ-018 – 020 |
| Approval derivation | HMRC-REQ-021 – 023 |
| PB handoff / MC-14 | HMRC-REQ-024 – 030 |
| Cutover model | HMRC-REQ-031 – 040 |
| Protected storage / authority | HMRC-REQ-041 – 053 |
| Activation readiness | HMRC-REQ-054 – 056 |
| Legacy migration | HMRC-REQ-057 – 062 |
| Structural preconditions | HMRC-REQ-063 – 064 |
| Effect boundary | HMRC-REQ-065 – 070 |
| Old-hook disposition | HMRC-REQ-071 – 072 |
| Security invariants (caller-input closure) | HMRC-REQ-073 – 074 |
| Consumption result / no caching | HMRC-REQ-075 – 079 |
| Versioning | HMRC-REQ-080 – 081 |
| Implementation readiness | HMRC-REQ-082 |

---

## 27. Security Invariants (MC-1 .. MC-14)

Carried forward from `docs/PHASE_149O_14_...ARCHITECTURE.md` §31,
refined, plus one new invariant (MC-14) resolving the PB/real-effect
question this contract was required to settle.

- **MC-1.** Evidence ID is a locator only; it never itself constitutes
  approval, verification, or permission.
- **MC-2.** Every mandatory consumption attempt re-verifies current
  HATP state fresh; no attempt trusts a prior attempt's result.
- **MC-3.** No cached verification result, no cached `approval_present`,
  no cached PB decision is ever stored or reused.
- **MC-4.** Post-cutover, missing or invalid evidence cannot fall back
  to legacy approval under any circumstance.
- **MC-5.** Post-cutover, a caller-supplied approval boolean is
  structurally absent and therefore non-authoritative.
- **MC-6.** Only protected Class-B cutover state (never an
  agent-writable file) determines whether mandatory mode applies to a
  deployment.
- **MC-7.** Cutover is one-way for any ordinary agent/runtime
  principal; reversion requires a separately governed administrative
  mechanism outside this contract.
- **MC-8.** AG3 and AG5 each bind to the exact operation they were
  signed for; no generic "any rollback" evidence exists.
- **MC-9.** Cross-family evidence (AG3-for-AG5 or AG5-for-AG3) cannot
  authorize, by construction of the existing operation-binding check.
- **MC-10.** Derived approval always passes through Permission Broker;
  it is never wired directly to dispatch.
- **MC-11.** Every effectful production caller (CLI and direct function
  call alike) is covered by the identical mandatory boundary, placed at
  the effect boundary itself, not at any single entry point.
- **MC-12.** Permission Broker `ALLOW` remains distinct from actual
  execution capability; `COMP-002` is a separate, later track.
- **MC-13.** Evidence creation itself (signing) never changes
  authority — signing only ever produces a consumable artifact.
- **MC-14 (new, this contract — the Effect-Truthful PB Requirement).**
  A real AG3/AG5 effect SHALL NOT proceed on the strength of a PB
  decision obtained from a `simulation_only=True` request. Only a
  truthfully `simulation_only=False`, `ALLOW`-resolving decision
  authorizes crossing the effect boundary once `HATP_MANDATORY`
  applies; until a rollback-specific execution-enforcement capability
  exists, this makes real post-cutover rollback effects unavailable by
  design (HMRC-REQ-029/037).

---

## 28. Threat Model

**HMRC-REQ-080 (Threat-A attacker capabilities, frozen).**

The agent/attacker principal CAN: edit the repository; edit or delete
evidence files under `.pcae/hatp-evidence/`; choose which `evidence_id`
to supply; invoke rollback commands and the legacy approve command;
call public Python functions directly; modify any repository-local
state.

The agent/attacker principal CANNOT: write protected Class-B
cutover/trust-root state; forge a hardware-backed signature; forge a
trusted signer's enrollment; substitute the production HATP provider or
trust store (F-2 closure, unmodified); supply an approval boolean to
any production function; downgrade Consumption Mode.

---

## 29. Full Mandatory Attack Matrix (45 Scenarios)

Reconciled exactly against `docs/PHASE_149O_14_..._ARCHITECTURE.md`
§30 (the authoritative source, per instruction not to trust prose over
the architecture document) — count independently re-verified at
exactly 45, no reduction, no addition beyond wording refinement to cite
`HMRC-REQ` IDs.

| # | Attack | Expected Result (frozen) |
|---|---|---|
| 1 | Missing evidence ID | Fail closed (`EvidenceNotFoundError`) — HMRC-REQ-018 |
| 2 | Malformed evidence envelope | Fail closed (`MalformedEvidenceEnvelopeError`) — HMRC-REQ-018 |
| 3 | Digest mismatch | Fail closed (`EvidenceIdDigestMismatchError`) — HMRC-REQ-018 |
| 4 | Wrong operation (evidence signed for a different job/PER) | Fail closed via operation binding — HMRC-REQ-021 |
| 5 | AG3 evidence used for AG5 dispatch | Fail closed via operation-family binding — MC-9 |
| 6 | AG5 evidence used for AG3 dispatch | Fail closed via operation-family binding — MC-9 |
| 7 | Wrong repository | Fail closed via repository-identity binding — HMRC-REQ-021 |
| 8 | Wrong deployment | Fail closed via deployment binding — HMRC-REQ-021 |
| 9 | Expired proof | Fail closed — `HATPVerificationStatus.EXPIRED` |
| 10 | Revoked signer | Fail closed — `HATPVerificationStatus.REVOKED_SIGNER` |
| 11 | Revoked authority / substrate readiness lost | Fail closed via readiness re-check — HMRC-REQ-021 |
| 12 | Decision changed after signing | Fail closed via digest cross-check — HMRC-REQ-017 |
| 13 | Binding changed after signing | Fail closed via digest cross-check — HMRC-REQ-017 |
| 14 | Fresh unregistered key | Fail closed — not in trust store, `UNKNOWN_SIGNER`-class status |
| 15 | Forged signer | Fail closed — `INVALID_SIGNATURE`/`INVALID_ATTESTATION` |
| 16 | Caller-supplied `approval_present=True` | Structurally impossible — HMRC-REQ-073 |
| 17 | Caller-supplied HATP `VALID` spoof | Structurally impossible — verification always re-runs internally, HMRC-REQ-052 |
| 18 | Test-provider injection | Structurally impossible — F-2 closure preserved, HMRC-REQ-080 |
| 19 | Arbitrary trust-store injection | Structurally impossible — F-2 closure preserved, HMRC-REQ-080 |
| 20 | Legacy-approved + missing HATP evidence, post-cutover | Fail closed — HMRC-REQ-061 |
| 21 | Legacy-approved + invalid HATP evidence, post-cutover | Fail closed — HMRC-REQ-061 |
| 22 | Delete Cutover Record | Fail closed / does not silently downgrade — HMRC-REQ-049 |
| 23 | Attempt CLI-flag downgrade (omit `--hatp-evidence-id` post-cutover) | Rejected — flag becomes effectively required once `HATP_MANDATORY` applies, HMRC-REQ-036 |
| 24 | Alternate production effect caller bypass (direct function call skipping CLI) | Fail closed — gate lives inside the effect functions, HMRC-REQ-065/068 |
| 25 | Cached previous `VALID` reused | Structurally impossible — no cache, HMRC-REQ-076 |
| 26 | Cached previous PB `ALLOW` reused | Structurally impossible — PB always re-evaluated, HMRC-REQ-076 |
| 27 | Evidence deleted after a prior successful attempt, retry | Fail closed on retry — HMRC-REQ-077 |
| 28 | Evidence modified after a prior successful attempt, retry | Fail closed on retry — HMRC-REQ-077 |
| 29 | Two valid evidence IDs, no ID supplied | Rejected — explicit selection required, HMRC-REQ-014/078 |
| 30 | Old raw `hatp_proof` parameter bypass attempt | Rejected — non-authoritative, forbidden on mandatory path, HMRC-REQ-071 |
| 31 | Old `hatp_evidence` parameter bypass attempt | Rejected — non-authoritative, forbidden on mandatory path, HMRC-REQ-071 |
| 32 | PB returns `HUMAN_REVIEW` despite valid HATP | Effect does not proceed — HMRC-REQ-026 |
| 33 | PB returns `DENY` despite valid HATP | Effect does not proceed — HMRC-REQ-027 |
| 34 | PB `ALLOW` under `simulation_only=True` | Does not authorize effect — MC-14, HMRC-REQ-029 |
| 35 | Evidence created under `LEGACY_COMPATIBLE`, consumed post-cutover | Allowed if still fresh/valid — HMRC-REQ-079 |
| 36 | Wrong AG3 job | Fail closed — operation binding, HMRC-REQ-021 |
| 37 | Wrong AG5 PER | Fail closed — operation binding, HMRC-REQ-021 |
| 38 | Wrong AG5 `ecp_id` | Fail closed — operation binding, HMRC-REQ-021 |
| 39 | Cutover-record corruption | Fail-closed-mandatory-equivalent, never legacy fallback — HMRC-REQ-049 |
| 40 | Cutover-record wrong repository | Treated as not-present-for-this-repo, no wrong-deployment activation — HMRC-REQ-048 |
| 41 | Cutover-record unknown version | Fail closed, never assume legacy — HMRC-REQ-046/047 |
| 42 | Cutover-record boolean version | Rejected — HMRC-REQ-046 |
| 43 | Repository moved/cloned/re-worktreed, evidence reused | Fail closed unless repository/deployment identity genuinely matches — HMRC-REQ-021 |
| 44 | Divergence-blocking AG5 file state combined with valid HATP evidence | AG5's structural divergence check still blocks — HATP validity never overrides a structural precondition, HMRC-REQ-064 |
| 45 | Evidence existence without an explicit evidence ID supplied | Has no effect — no implicit lookup exists, HMRC-REQ-014 |

---

## 30. Contract Versioning

**HMRC-REQ-080.** This contract is frozen as `HMRC-001 v1.0`.

**HMRC-REQ-081.** An unknown future `HMRC-001` version number
encountered by any consumer SHALL fail closed (treated as
unsupported), never silently treated as compatible.

---

## 31. Implementation Readiness

**HMRC-REQ-082.** This contract is implementation-ready — meaning a
future implementation phase may begin design work — only because:
evidence syntax is frozen (§6-8); the consumption object/chain is
frozen (§9); cutover storage is frozen (§18); cutover mode vocabulary
and transitions are frozen (§13, §17); legacy semantics are frozen
(§20); the AG3 gate and AG5 gate are frozen (§22); the PB relationship,
including MC-14, is frozen (§12); old-hook disposition is frozen (§23);
failure semantics are frozen (§10); and the 45-scenario attack matrix
is frozen (§29). No authority-sensitive TBD remains in this document.

---

## 32. B-149O-1..4 Closure Criteria (Frozen, Not Met by This Phase)

**HMRC-REQ-083.** B-149O-1..4 close only once, in a future phase:

- the actual AG3 effect path enforces this contract's Mandatory
  Consumption Boundary (HMRC-REQ-066);
- the actual AG5 effect path enforces this contract's Mandatory
  Consumption Boundary (HMRC-REQ-067);
- no raw-hook or legacy bypass remains reachable (HMRC-REQ-071, §24);
- no caller-supplied approval boolean is reachable (HMRC-REQ-073);
- all 45 attack-matrix scenarios (§29) are independently exercised
  against real production code and pass as frozen;
- a genuine `HATP_MANDATORY` cutover is independently demonstrated on
  a protected deployment; and
- independent verification (a future 149O.16-class phase) confirms all
  of the above.

Until then, B-149O-1..4 remain **INDEPENDENTLY VERIFIED AT THE
HATP-GATED AUTHORITY BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**,
unchanged by this phase. This contract does not, and could not, close
them by itself — it is a freeze document, not an implementation.

---

## 33. Contract Self-Consistency Statement

**HMRC-REQ-084.** This document has been searched for the terms
`legacy`, `fallback`, `approval`, `mandatory`, `PB`, `ALLOW`,
`execution`, `evidence_id`, `proof`, `cutover`, `prepared`, and
`HATP_MANDATORY`. No contradictory authority statement was found: every
use of "legacy" outside `LEGACY_COMPATIBLE`/`PREPARED` semantics
(§14-15) is confined to non-authoritative historical/migration meaning
post-cutover (§20); no clause grants effect on `PB ALLOW` obtained
under `simulation_only=True` (§12/MC-14); no clause permits implicit
evidence selection (§9); no clause authorizes a caller-supplied
approval/PB/mode override (§24).

**HMRC-REQ-085 (No Dual Authority).** No clause in this document is
equivalent to `legacy_approved OR hatp_valid`, nor does any clause make
legacy approval permanently, unconditionally required in addition to
HATP post-cutover in a way that keeps legacy state itself
authority-bearing (HMRC-REQ-053).

---

## 34. Expected Contract Verdict

```
HMRC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION
```

This is explicitly **not** a claim of VERIFIED. Independent contract
verification is the next phase's job (§35).

---

## 35. Next Phase

**149O.16 — HATP Mandatory Production Consumption Contract Independent
Verification.** Verification MUST independently attack: contract
internal consistency (§33); cutover monotonicity (§17-18); legacy
fallback absence (§14-16, §20); effect-boundary placement (§22); AG3
direct-call bypass; AG5 direct-call bypass; raw-hook bypass (§23);
PB/MC-14 enforcement semantics (§12, §27); and all 45 attacks (§29). No
implementation SHALL begin before 149O.16 completes.

The Python 3.9/3.10 timestamp defect (149O.12B-Obs-PY39-1) does not
block 149O.16. Sequencing after 149O.16 verifies is likely: 149O.16 →
narrow PY39 repair → mandatory-consumption implementation plan →
implementation, unless 149O.16 demonstrates the defect is irrelevant
due to a supported-version change.

---

## 36. Explicit Confirmations (Restated for the Phase Report)

No production source (`src/pcae/**`) was modified to produce this
contract. HSCE-001 v1.1, HATP-001 v1.0, RAE-001 v1.0, RWMPC-001 v1.0,
PBPA-001 v1.0, and PBPC-001 v1.2 all remain byte-unchanged. No AG3/AG5
mandatory consumption was implemented. No legacy approval behavior
changed. No Cutover Record was created. No Permission Broker behavior
changed. `POL-005` remains unchanged. No `COMP-002` capability was
implemented. No rollback dispatch behavior changed. No Class-B
provisioning occurred. No HATP production activation occurred. Signing
evidence remains distinct from approval, permission, capability, and
execution (§5). B-149O-1..4 remain independently verified at the
HATP-gated authority boundary with system execution closure deferred
(§32). HATP production remains NOT READY. Runtime remains Observed /
observe / unavailable.
