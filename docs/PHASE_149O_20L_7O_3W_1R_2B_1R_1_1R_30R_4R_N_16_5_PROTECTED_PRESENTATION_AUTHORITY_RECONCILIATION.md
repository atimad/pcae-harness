# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R — N-16-5 Protected-Presentation Helper Installation and Evidence-Writer Authority Contract Reconciliation

## Verdict

**CONTRACT RECONCILIATION COMPLETE — IMPLEMENTATION PRECONDITION RESOLVED.**

The `.30R.4` blocker is independently reproduced and resolved by the minimum
coherent normative delta:

1. **HPAC-PAWA-001 v1.1 → v1.2 (MINOR)** — one metadata-only
   `configure_presentation_mechanism` mutation family, exact writer role
   `presentation_mechanism_installer`, exact consumer
   `pcae.core.hpac_protected_presentation_admin`, and no executable/runtime
   authority.
2. **HPAC-PPA-001 v1.0 (new narrow companion)** — exact helper installation,
   digest/current-generation lifecycle, fixed launch, response authenticity,
   and process-local evidence-writer authority.

No production source or script changed. No protected presentation, helper,
Gate wiring, N-16-6, N-16-7, Slice C, dispatch, runtime capability, or effect
was implemented. N-16-5 remains **NOT CLOSED**.

Phase-entry SHA `A` is
`db5f1dd761174d6ac1ca16e49e8871c02f747fdf`, the finalized historical
`.30R.4` BLOCKED head. The repository was clean and synchronized at entry.

## Independent blocker reconstruction

| Requirement | Source | Existing authority | Missing authority at A | Reconciled result |
|---|---|---|---|---|
| protected administrator installs/revokes real presentation descriptor | RHAMP-REQ-015/016; HPAC-REQ-080/090 | PAWA deployment-owner anchor | no presentation mutation or consumer | PAWA v1.2 metadata mutation + exact admin consumer |
| pinned helper bytes and installation/currentness | RHAMP-REQ-082/083/087/088 | protected root and descriptor shape | no installation record/current anchor | HPAC-PPA installation + current-generation schemas |
| trusted helper emits exact response | RHAMP-REQ-143..148 | frozen response semantics | no concrete local authenticity/currentness authority | verified opened bytes + private one-shot channel + nonce/generation binding |
| canonical evidence write | HPAC-REQ-091..093 | existing store/role/provenance seam | no production issuer for `protected_presentation_mechanism` | launcher-held process-local single-use writer, outside PAWA |

Executable reproduction from `.30R.4` remains valid: current production
`PawaOperation` has five members; `production_writer("install_presentation_mechanism")`
returns `operation_scope_invalid`; the production descriptor store cannot mint
its fixture installer. Historical `.30R.4` remains BLOCKED and byte-unchanged.

## Required adjudication verdict

**INSTALLATION AUTHORITY:** the existing HPAC-PAWA deployment-owner protected
administration anchor.

**EXECUTABLE INSTALL MODEL:** out-of-band deployment-owner installation of
immutable content-addressed helper bytes, followed by PAWA-authorized metadata
registration/pinning. PAWA never writes executable bytes.

**PAWA CONTRACT IMPACT:** HPAC-PAWA-001 **v1.2 MINOR**.

**PRESENTATION INSTALLATION MUTATION:** exactly
`configure_presentation_mechanism`, closed lifecycle action
`{install, rotate, revoke}`, role `presentation_mechanism_installer`, subject
the exact mechanism id, one configuration transaction, bounded multi-write.

**INSTALLER CONSUMER:** exactly
`pcae.core.hpac_protected_presentation_admin`, reachable only from standalone
`scripts/hpac_protected_presentation_admin.py`; no wildcard/prefix/glob.

**INSTALLATION RECORD:** `HPAC-PRESENTATION-INSTALLATION/1.0` immutable
generation records plus `HPAC-PRESENTATION-CURRENT-GENERATION/1.0` current
anchor, under the frozen HPAC presentation-mechanism directory.

**EVIDENCE WRITER AUTHORITY:** a launcher-held seal-guarded process-local,
non-serializable, restart-dead, single-use `HPACWriterCapability` bound in the
canonical issuance registry to one request and current helper generation.

**EVIDENCE WRITER ROLE:** exactly existing role
`protected_presentation_mechanism`, explicitly outside PAWA.

**EVIDENCE CURRENTNESS:** exact request/approval/challenge/principal/operation
binding plus installation id, generation, installation digest, descriptor
digest, private-channel nonce, and revalidation immediately before evidence
persistence. Rotation/revocation supersedes outstanding responses.

**HPAC CONTRACT IMPACT:** none; HPAC-001 v2.1 byte-unchanged.

**RHAMP CONTRACT IMPACT:** none; RHAMP-001 v1.0 byte-unchanged.

**WRITER-PROVENANCE IMPACT:** none;
`HPAC-WRITER-PROVENANCE/1.0` already carries exact role, subject, root, store,
path, and record digest. Resolver allowlists give roles meaning.

**N-16-6 RELATIONSHIP:** **DISTINCT / NO AUTHORITY TRANSFER**.

## Installation model and least authority

Candidate A — out-of-band executable + PAWA metadata registration — is
selected. Candidate B — PAWA-bounded byte installation — is rejected because
RHAMP says administrator-installed and does not require PCAE to copy bytes;
granting such power would approach generic executable installation. Candidate C
— self-installing helper — is rejected because it collapses the trust anchor
and permits the component being admitted to establish its own authority.

The fixed helper path is content-addressed beneath `HPAC_PROTECTED_ROOT`:

`presentation-helper/installations/<sha256>/pcae-protected-local-presentation`

The absolute path must equal the protected-root-derived path. Trust requires
the opened byte stream's SHA-256, current installation/descriptor/anchor
agreement, production provenance, same root/installation identity, no symlink,
regular single-link file, deployment-owner ownership, and no configured-agent,
group, other, or ACL write. Validation and execution must use the same opened
object or a platform-equivalent identity-preserving handle.

## Installation lifecycle

- **Bootstrap:** admin installs immutable bytes out of band, then PAWA registers
  generation 1. No prior protected presentation is required; no circularity.
- **Rotation:** new bytes receive a new content-addressed path; metadata G+1
  supersedes exact G; descriptor and current anchor move in one bounded
  multi-write transaction.
- **Revocation:** G+1 is revoked; descriptor and anchor are revoked atomically;
  no deterministic fallback and no outstanding evidence acceptance.
- **Recovery:** explicit deployment-owner reprovision with a new installation
  id and generation 1; no first-use, repository, environment, or fixture path.
- **Rollback:** restoring only old records/bytes fails current-anchor checks.
  Whole-machine/root snapshot rollback remains bounded by the existing PAWA TCB
  and is not overclaimed.

## Runtime evidence authority

The helper process does not receive a filesystem writer. The trusted launcher
mediator verifies the current installation, opens/executes the same bytes,
creates a private one-shot channel and 256-bit nonce, binds the complete request
and helper generation, validates the response, and retains the evidence writer
in the parent process. Only a valid explicit `APPROVE` response may drive one
create-only `HPAC-PRESENTATION-EVIDENCE/2.0` write and provenance sidecar.

`REJECT`, cancel, timeout, crash, malformed response, replay, substitution,
rotation, revocation, or expiry produces no approval evidence and cannot leave
a reusable writer. Durable evidence is canonical/audit material, not bearer
authority; it still requires HPAC/RHAMP verification, fresh REAL authentication,
proof lifecycle binding, and Gate consumption.

## Contract/version analysis

PAWA's existing MINOR rule explicitly permits an exact new consumer category.
The added mutation remains inside the same protected root and preserves
R1-HYBRID, two-principal topology, exact consumer inventory, non-bearer,
process-local, restart invalidation, one-operation/multi-write lifecycle,
generation/currentness, failure codes, and trust root. No PAWA MAJOR trigger
fires.

HPAC-PPA-001 is necessary because runtime evidence issuance is intentionally
outside PAWA. Putting runtime evidence authority into PAWA would contradict
HPAC-PAWA-REQ-096 and collapse installer/evidence roles. Evolving HPAC-001 or
RHAMP-001 is unnecessary because their frozen descriptor/evidence/attestation
and helper requirements already expose the required specialization points.

The existing 21 PAWA codes suffice. Runtime failures use RHAMP's existing
`helper_integrity_unverified`, `helper_response_untrusted`,
`ceremony_superseded`, `ceremony_cancelled`, `ceremony_timed_out`,
`challenge_expired`, and presentation-integrity outcomes. No terminal vocabulary
was added.

## Exact future production surface — not implemented

- `pcae.core.protected_presentation_installation`
- `pcae.core.hpac_protected_presentation_admin`
- `pcae.core.protected_presentation`
- `pcae.protected_presentation_helper`
- `scripts/hpac_protected_presentation_admin.py`
- existing `approval_presentation.py`, `hpac_verifier.py`, Gate 5, and Gate 9
  only in the separately authorized implementation successor.

No name above exists or gains authority merely because this contract names it.

## Verification evidence

- Fresh `.30R.4R` suite: **42 passed**.
- Historical/current PAWA, RHAMP, presentation and contract suites: **511
  passed** in the targeted combined sweep.
- No test definition removed or renamed; no skip/skipif/`pytest.skip`/xfail
  added; seven historical point-in-time checks were pinned to their immutable
  owning phase heads instead of current HEAD.
- `git diff A -- src/pcae scripts`: empty.
- Existing contracts other than HPAC-PAWA-001: byte-identical to A; new
  HPAC-PPA-001 is the only new contract.
- Historical `.30R.4` artifact SHA-256 remains
  `757268a2481f8077f1c7ed7334c763383f03e7b0813222f025bee54a9ab28715`.
- Repository-wide diagnostic: `pytest -n auto` cannot collect consistently
  because a historical HATP suite generates UUID-valued parameter IDs during
  collection independently on each worker. A serial all-history run reached
  1,084 passes before being stopped after 6m41s; its two observed failures are
  pre-existing advisory-directory guards, and `src/pcae/advisory` is already
  present at phase-entry A (tree `731313ea0a803a6bed3fd5202ca333fa0f0dd59b`).
  Neither diagnostic is repair-attributable or part of the deterministic
  affected-scope verdict above.

## Current status and no-go proof

- Merged RHAMP authentication: IMPLEMENTED + INDEPENDENTLY VERIFIED.
- Protected-presentation implementation precondition: RESOLVED.
- Presentation helper installation authority: CONTRACTUALLY FROZEN / READY.
- Presentation evidence-writer authority: CONTRACTUALLY FROZEN / READY.
- Protected presentation: NOT IMPLEMENTED.
- Real-assurance Gate consumption: NOT IMPLEMENTED.
- N-16-5: NOT CLOSED.
- N-16-6 / N-16-7: OPEN / UNTOUCHED.
- N-23-1: INFO; N-23-2: INFO / DEFERRED.
- Runtime: Observed / observe / unavailable; zero plugins/capabilities.
- First external effect: ABSENT / UNREACHABLE.

No production file, Gate, helper, UI, browser, network approval, arbitrary
subprocess, PB/policy override, runtime capability, adapter, dispatch, Slice C,
or effect was introduced.

## Exact successor

Recommended, not begun and requiring separate explicit authorization:

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1` — **N-16-5 Protected Human-Approval
Presentation and Real-Assurance Consumption Implementation After Authority
Reconciliation**.

Historical `.30R.4` remains BLOCKED and immutable. The implementation successor
must itself be followed by a fresh independent verification plus mandatory real
CTAP2 hardware verification before N-16-5 may close.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
