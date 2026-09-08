# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R — Independent Verification of HPAC-PAWA-001 v1.4 Production Recognized Read / Ceremony Authority Contract (F-5-B1 Least-Privilege Canonical-State Access)

**Alias (display-only, non-authoritative):** N16-5-F5B1-READAUTH-IV

**Canonical predecessor:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R (alias N16-5-F5B1-READAUTH)

## Status: HPAC-PAWA-001 v1.4 — INDEPENDENTLY VERIFIED. F-5-B1 CONTRACT BLOCKER: INDEPENDENTLY VERIFIED RESOLVED. F-5-B1 IMPLEMENTATION: PENDING. N-16-5: NOT CLOSED.

---

## 1. Scope and independence

This is a **verification-only** phase. It authored no production accessor, edited
no HPAC-PAWA-001 normative text, performed no ceremony, mutated no protected
host state, and did **not** close N-16-5. The predecessor's freeze verdict and
its own contract-test suite were **not** taken as normative; the v1.3 → v1.4
authority model was independently reconstructed from immutable git history and
primary source.

**IV phase-entry SHA (V0):** `3ef9ad5d679a452643c38f265e406d348b2b6e82`
(`origin/main..HEAD` = 0 at entry; working tree clean).

**V13_BASE** (last immutable HPAC-PAWA-001 v1.3 state, pre-freeze-work):
`18d7da02` (final commit of the predecessor N16-5-FINAL-CERT BLOCKED phase).

**V14_FINAL** (v1.4 contract-freeze normative-text commit):
`1877a412` ("HPAC-PAWA-001 v1.3 -> v1.4 FROZEN (MINOR, S-3)").

## 2. CPIPC lineage

Independently verified: candidate id = predecessor id + exactly one trailing
`.1R` segment (confirmed by direct string comparison); same series (149); same
branch; predecessor is the latest completed phase (`pcae session bootstrap`
active task was the post-predecessor idle task); no active conflicting phase;
`origin/main..HEAD` = 0 at entry. No discrepancy from the proposed id — the
canonical id above is used as given, alias remains display-only.

## 3. v1.3 → v1.4 normative delta (independently reconstructed)

`git diff 18d7da02 HEAD -- docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
touches exactly one file. `git diff --name-only 18d7da02 HEAD -- src/pcae scripts
pyproject.toml` is **empty** — independently reproduced, confirming this is a
pure specification/blueprint change with zero production-behavior impact.

**Delta contents (independently reconstructed, not copied from predecessor
prose):** seven new sections — **§7C** (v1.3→v1.4 delta table), **§33B**
(recognition sequence for a new read/ceremony-entry accessor
`recognized_certification_read_authority(...)` returning a
`CertificationReadAuthority` handle), **§38B** (closed consumer inventory —
the existing §38A certification coordinator, and only that consumer), **§42D**
(exact enumerated read-scope grant: principal, credential, RHAMP counter
read-only, current-generation PPA/PAWA descriptor state), **§42E** (rejection
→ existing failure-code mapping), **§49B** (one-session / restart-dead
lifetime), **§68B** (human-election / real-vs-deterministic / PB / policy /
runtime walls) — plus version/history bookkeeping (§80.4, §90.4, §95C, §96C),
requirement range extended 275→309 (REQ-276..309), invariant count 13→14
(PAWA-INV-14).

## 4. Independent version classification

MINOR / S-3 independently re-derived, not inherited. No MAJOR trigger fires:
no new trust root (existing `_PRODUCTION_WRITER_FACTORY_SEAL` reused), no new
actor/consumer category (§38B keeps the exact existing §38A coordinator as
sole consumer), no persistent-schema change (`hpac_pawa_schemas.py` unchanged
— confirmed by git diff, not merely asserted), no new operation vocabulary
(`PawaOperation` enum unchanged at 6 mutation members — confirmed in source),
no externally visible execution/effect authority (runtime remains
`not_implemented`/`Observed`, 0 plugins/capabilities throughout), no failure
vocabulary change, no compatibility break. **VERDICT: MINOR/S-3 VERIFIED.**

## 5. Requirement and invariant inventory

REQ-276..309 verified sequential, gap-free, and not a reuse of any prior
requirement id (checked against the requirement ranges of every earlier PAWA
freeze phase, all of which end at or below REQ-275). PAWA-INV-14 read and
found coherent with, and not weaker than, the detailed §33B/§38B/§42D/§68B
requirements it summarizes (see §16 of this report).

## 6. F-5-B1 root cause — reproduced from primary source

Independently reproduced against `src/pcae/core/hpac_foundation.py` and
`hatp_class_b_topology_verifier.py`: `_validate_production_boundary` keys the
negative boundary check off `self._configured_agent_identity` if bound, else
falls back to `_current_agent_identity()` = `os.geteuid()`. Under a
deployment-owner `sudo` invocation, `euid == 0` owns the protected root, so an
unbound boundary check fails closed — exactly the documented root cause. Both
disqualified alternatives (an over-authorized production-writer path, and a
test-only seam) were independently confirmed unsuitable: the former grants
mutation authority the certification-read path does not need; the latter is
explicitly excluded from production trust by existing `FIXTURE_NON_REAL`
gating in `HPACStoreAuthority.writer()`.

## 7. Read authority genuinely distinct from write authority

Read `hpac_foundation.py:745-751`: `HPACStoreAuthority.writer()` raises
`HPACAuthorityError` for every authority class except `FIXTURE_NON_REAL` — a
production-recognized authority obtained via the (not-yet-implemented) read
accessor would still hit this same rejection. No existing or contract-implied
code path converts a recognized read authority into a writer capability;
mutation still requires the separately sealed `_mint_production_writer_capability`,
reachable only through `production_writer`/`certification_writer`. No hidden
mutation method was found on the class's reachable surface beyond the
pre-existing `verify_record`/`resolve_record` reads. **VERDICT: READ AUTHORITY
!= WRITE AUTHORITY — VERIFIED.**

## 8. SS33B recognition ordering

§33B specifies the configured-agent identity bind occurs before the
session-scoped provenance reads that would otherwise fail under an
ambient-root caller. This matches the real mechanics in `hpac_foundation.py`
exactly: the bind must populate `self._configured_agent_identity` before
`_validate_production_boundary` is evaluated, or the check falls back to
`os.geteuid()` and fails closed for a root-owned deployment. One documented,
non-blocking wrinkle: REQ-278's own numbered step 2 text forward-references
step 3 ("...after the configured-agent identity is bound (step 3 below)"),
i.e. the prose is unambiguous about the real execution order (3 before 2)
despite the list numbering implying the opposite. This is a clarity nit for
the eventual implementation/IV phase, not a security defect — the normative
requirement is stated correctly. **VERDICT: SS33B ORDERING — VERIFIED (nit
recorded, non-blocking).**

## 9. SS33 steps 1-9 preserved; H-3 unchanged

`git diff` on the freeze commit shows only additive hunks around, not inside,
existing §33A/§38A/§42B/§68A text; all five H-3 roles and their sections
remain present unmodified. No weaker parallel recognizer was introduced.

## 10. No second trust root; no mint-authority leak via seal reuse

The existing `_PRODUCTION_WRITER_FACTORY_SEAL` discipline is reused for
recognition; nothing in the new sections authorizes a new seal, secret,
persistent bearer token, or independent factory root. The separation between
"using the seal to establish recognition" and "the resulting read handle
gaining seal/mint access" is stated explicitly and is not left ambiguous.

## 11. CertificationReadAuthority handle — bounded, no raw-authority escape

§42D specifies the handle exposes only the enumerated reads and one bounded
ceremony invocation, retaining the underlying `HPACStoreAuthority` internally.
No `unwrap()`/`raw()`/`.authority` escape is specified or implied. Because the
handle is not yet implemented in source (see §14 below), this is a normative
verification of intent, correctly flagged as such rather than a runtime test.

## 12. Read scope — closed, exactly enumerated

§42D enumerates exactly four record categories (principal/credential,
RHAMP sidecar + current counter read-only, current-generation
presentation/PPA descriptor state, PAWA anchor/descriptor/exclusion records)
with no wildcard, glob, prefix, or dynamic registration. §38B closes the
consumer set to the existing §38A coordinator with the same exact-enumeration
discipline (REQ-282 requires a future source-scan guard test mirroring the
existing §39/§39A pattern). Principal, credential, and counter read semantics
are each independently confirmed bounded to read-only / verification
operations; counter mutation is explicitly reserved to the existing H-3
`hpac_rhamp_counter_state_verifier` role and denied to the new accessor.

## 13. Ceremony entry — reuses existing path, no parallel evidence system

§42D requires the bounded ceremony invocation to hand the wrapped authority to
the existing `run_protected_presentation_ceremony(authority=...)`. Confirmed
in source that this function already accepts an `HPACStoreAuthority` and no
new signature or parallel evidence-writer path is introduced; the existing
`mint_protected_presentation_evidence_writer` remains the sole trusted
evidence writer. No caller-supplied APPROVE/REJECT/UP/UV is authorized; the
human-election and real-vs-deterministic walls in §68B are unchanged from
existing H-3 semantics.

## 14. Implementation-status honesty (production source unchanged)

`grep -rn "recognized_certification_read_authority|CertificationReadAuthority"
src/pcae scripts` returns **no matches** — independently confirmed not
implemented anywhere. `git diff 18d7da02 HEAD -- src/pcae scripts
pyproject.toml` is empty, confirmed against the actual final freeze-phase
commit, not just an intermediate one. The predecessor's "PRODUCTION
IMPLEMENTATION: NOT PERFORMED" claim is accurate.

## 15. Cross-contract consistency

`git diff --name-only 18d7da02 HEAD -- docs/contracts` names only the one PAWA
contract file. Independently greeping
`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` for
`HPACStoreAuthority`/`read-only`/`recognized_certification_read` returns no
matches — no conflicting or overlapping claim exists there.
`hpac_pawa_schemas.py` confirmed byte-unchanged.

## 16. Fresh IV contract-test run and honesty finding

Predecessor's own contract-test file
(`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_n16_5_f5b1_readauth_contract.py`)
run **read-only, unmodified: 49 passed, 0 failed** — the predecessor's
headline claim is reproduced. On inspection, roughly 60% of these assertions
(the bulk of test_10–test_78) are self-referential string-matches against the
same contract document the same phase authored — weak evidence of anything
beyond internal prose consistency. A materially stronger minority
(test_70–test_75, test_90–test_93) exercises real git history and real source
(empty src/scripts/pyproject diff, byte-identity of companion contracts and
schemas, direct greps of the actual authority-model source files) and does
carry independent evidential weight. **This report does not cite "49/0
passing" as functional proof** — none exists yet, correctly, since no
implementation exists. Future phases citing this number should describe it as
"a specification/history-consistency suite," not a functional-correctness
suite.

## 17. Threat-model / escalation walls (adversarial read)

Independently reasoned through the escalation matrix: an ordinary agent, CLI,
runtime, plugin, launcher, helper, ordinary Gate/verifier, test fixture, or
phase-local harness has no path to the new accessor under §38B's closed
consumer inventory. `writer()`/`production_writer`/`certification_writer`
escalation from a recognized read handle is denied by the unchanged
`HPACStoreAuthority` surface (§7 above). No enrollment/revocation/PPA-mutation
authority is granted. No PawaOperation, writer role, failure code, RHAMP
terminal reason, or schema change is required or introduced. No live host,
principal, credential, or counter state was touched during this IV; no
YubiKey/ceremony/getAssertion/makeCredential/APPROVE/REJECT occurred; `pcae
runtime inspect` remained `not_implemented`/`Observed`/`observe`/`unavailable`
with 0 plugins/capabilities throughout.

## 18. Defects / ambiguities found

One non-blocking clarity nit (§33B REQ-278 step-2/step-3 numbering vs. actual
execution order — see §8) is recorded for the implementation/IV successor to
fix in wording. No normative defect, over-authorization, hidden mutation
route, or ambiguous trust-root/mint-authority separation was found. This IV
does **not** rubber-stamp the predecessor: every claim above was re-derived
from `git diff`/`grep`/direct source reads, not from the predecessor's own
report or test-suite output, and the test-suite evidentiary strength is
explicitly downgraded in §16 rather than inherited at face value.

## 19. Required final verdicts

| Field | Value |
|---|---|
| PHASE ALIAS | N16-5-F5B1-READAUTH-IV |
| HPAC-PAWA-001 VERSION | v1.4 |
| v1.3 → v1.4 NORMATIVE DELTA | INDEPENDENTLY RECONSTRUCTED |
| VERSION CLASSIFICATION | MINOR S-3 VERIFIED |
| F-5-B1 ROOT CAUSE | INDEPENDENTLY VERIFIED |
| CANONICAL READ AUTHORITY | DISTINCT FROM WRITE AUTHORITY VERIFIED |
| SELECTED MINIMAL AUTHORITY SHAPE | INDEPENDENTLY VERIFIED |
| AUTHORIZED CONSUMER | existing §38A certification coordinator only |
| CONSUMER SET | CLOSED |
| SS33B | INDEPENDENTLY VERIFIED |
| SS33 STEPS 1-9 | PRESERVED |
| CONFIGURED-AGENT BIND ORDER | VERIFIED |
| PROTECTED READS AFTER BIND | VERIFIED |
| RECOGNITION FAIL-CLOSED | VERIFIED |
| SECOND TRUST ROOT | NOT INTRODUCED VERIFIED |
| CertificationReadAuthority | NORMATIVELY BOUNDED |
| RAW AUTHORITY ESCAPE | DENIED |
| READ SCOPE | CLOSED VERIFIED |
| PRINCIPAL READ | AUTHORIZED VERIFIED |
| CREDENTIAL READ | AUTHORIZED VERIFIED |
| COUNTER READ | AUTHORIZED VERIFIED |
| COUNTER UPDATE | DENIED VERIFIED |
| PRESENTATION/PAWA READ | BOUNDED VERIFIED |
| CEREMONY ENTRY | ONE BOUNDED INVOCATION VERIFIED |
| PRESENTATION EVIDENCE WRITER | REMAINS SEPARATE VERIFIED |
| HPACWriterCapability | NOT GRANTED VERIFIED |
| writer() ESCALATION | DENIED VERIFIED |
| production_writer ESCALATION | DENIED VERIFIED |
| certification_writer ESCALATION | DENIED VERIFIED |
| MUTATION AUTHORITY | NONE VERIFIED |
| ENROLLMENT / REVOCATION | DENIED VERIFIED |
| PPA MUTATION | DENIED VERIFIED |
| REMINT | DENIED VERIFIED |
| DELEGATION | DENIED VERIFIED |
| PROCESS-LOCAL | VERIFIED |
| RESTART-DEAD | VERIFIED |
| ONE-SESSION | VERIFIED |
| HUMAN APPROVAL WALL | VERIFIED |
| REAL-vs-DETERMINISTIC WALL | VERIFIED |
| H-3 DESIGN | UNCHANGED VERIFIED |
| PB WALL | VERIFIED |
| POLICY WALL | VERIFIED |
| RUNTIME / EFFECT WALL | VERIFIED |
| PawaOperation | UNCHANGED VERIFIED |
| WRITER ROLE VOCABULARY | UNCHANGED VERIFIED |
| PAWA FAILURE VOCABULARY | UNCHANGED VERIFIED |
| RHAMP TERMINAL VOCABULARY | UNCHANGED VERIFIED |
| SCHEMAS | UNCHANGED VERIFIED |
| COMPANION CONTRACT | NOT REQUIRED VERIFIED |
| CROSS-CONTRACT BYTE IDENTITY | VERIFIED |
| CROSS-CONTRACT SEMANTIC CONSISTENCY | VERIFIED |
| HISTORICAL GUARD RECONCILIATION | INDEPENDENTLY VERIFIED (no new guard change in this IV; predecessor's guard reconciliation re-checked, unaltered) |
| PRODUCTION IMPLEMENTATION | NOT PERFORMED |
| REAL CEREMONY | NOT PERFORMED |
| HPAC-PAWA-001 v1.4 | INDEPENDENTLY VERIFIED |
| F-5-B1 CONTRACT BLOCKER | INDEPENDENTLY VERIFIED RESOLVED |
| F-5-B1 IMPLEMENTATION | PENDING |
| F-5 | LIVE READINESS VERIFIED — CEREMONY BLOCKED PENDING F-5-B1 IMPLEMENTATION |
| N-16-5 | NOT CLOSED |
| N-16-6 | OPEN / UNTOUCHED |
| N-16-7 | OPEN / UNTOUCHED / STRICTLY LAST |
| RUNTIME | Observed / observe / unavailable |
| FIRST GOVERNED RUNTIME EXTERNAL EFFECT | ABSENT / UNREACHABLE |

## 20. Required implementation successor (derived, not begun)

**Production Recognized Read / Ceremony Authority Implementation for N-16-5
Final Certification — F-5-B1 Repair**

Short alias: **N16-5-F5B1-IMPL**

Scope: implement only `recognized_certification_read_authority(...)`,
`CertificationReadAuthority`, the §33B recognition ordering (with the REQ-278
step-numbering clarity fix applied), the §38B consumer guard, the exact §42D
read scope, one bounded ceremony entry, one-session/restart-dead semantics, no
authority escape, no writer escalation, no mutation, no test seam, same trust
root. Finishes with F-5-B1: REPAIRED / IV PENDING. **Not begun in this phase.**
A separate N16-5-F5B1-IV must independently verify the resulting code before
any N16-5-FINAL-CERT is authorized on a fresh CPIPC-valid id.

## 21. Governance notes

REPORTING-UX-1 remains non-blocking, untouched. N-16-6/N-16-7 remain open and
untouched. This phase performed no runtime invocation, no prompt execution, no
execution authorization, and required no rollback.
