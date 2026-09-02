# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2 Complete — HPAC-PAWA-001 v1.0 Production Protected-Admin Writer Anchor Contract Freeze

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2
**Type:** governed contract freeze / primary-source analysis / contract-versioning re-derivation / decision-freezing / documentation
**Status:** HPAC-PAWA-001 v1.0 FROZEN AS THE SOLE NORMATIVE DELTA — N-16-5 WRITER-ANCHOR CONTRACT FROZEN — IMPLEMENTATION PENDING — NOT CLOSED
**Phase-entry SHA:** `5373ee21` (task-open commit); baseline tree = the `.1R.30R.1` finalized head `91741564`; `origin/main..HEAD = 0` at entry
**Production source changed:** none (`git diff 91741564 HEAD -- src/pcae` empty)
**Normative contracts changed:** exactly one new companion contract added — `git diff --name-only 91741564 HEAD -- docs/contracts` names only `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (HPAC-PAWA-001 v1.0, initial freeze); **no existing contract edited**; HPAC-001 stays v2.1; RHAMP-001 stays v1.0; HBDC-001 stays v1.2
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

This phase turned the `.1R.30R` adjudication (verdict: NEW COMPANION CONTRACT),
as independently verified by `.1R.30R.1` (ADJUDICATION VERIFIED; three
non-blocking findings F-1 / F-2 / F-3), into a precise normative companion
contract — **HPAC-PAWA-001 v1.0 — HPAC Production Protected Administration
Writer Anchor Contract** (`HPAC-PAWA-REQ-001..163` sequential, no gaps, no
duplicates; `PAWA-INV-1..11`), authored under HPAC-001 v2.1's existing §7
extension points and changing none of its text. It freezes the *mechanism*
HPAC-001 §7 deliberately deferred while freezing only the *policy*.

Primary sources read to complete relevant scope: the `.1R.30R` adjudication
artifact **in full** (1064 lines); the `.1R.30R.1` IV artifact **in full**
(1549 lines); the historical `.1R.30` BLOCKED artifact; HPAC-001 v2.1
(§7 HPAC-REQ-021/022/023/024 in full, §8, §28, §37, §38); RHAMP-001 v1.0
(§1, §14 RHAMP-REQ-047..050, §15, §17, §20–§22, §49 the 41-code
`terminal_reason_code` table in full, §50, §61, §64, §65, §68, §70, §71);
HBDC-001 v1.2 **in full** (397 lines); CPIPC-001 v1.0 §4. Production source
read **as evidence only** (not modified): `src/pcae/core/hpac_foundation.py`
in full (782 lines — `HPACStoreAuthority.writer()` refuses every non-fixture
class L420-421; `_validate_production_boundary` the negative half L351-367;
`_current_agent_identity` == live `os.geteuid()` — the F-1 basis;
`HPACWriterCapability` seal / `__reduce__` discipline; the `{device, inode}`
manifest binding L409-410) and `scripts/hatp_deployment_binding_admin.py`.

## What HPAC-PAWA-001 v1.0 freezes

- **Trust root** = OS filesystem write authority on the out-of-band-provisioned
  `<HPAC_PROTECTED_ROOT>`, the **configured** agent principal
  (`PCAE_AGENT_PRINCIPAL`, canonical PCAE configuration — **not**
  `os.geteuid()`) provably excluded. Identical trust root to HBDC-001's IV'd
  Class-B Protected Root; **HBDC-001 is precedent, not a shared authority
  root** (§4, §65–§66).
- **Positive recognition** = six required conjuncts, an 11-step sequence (§33):
  fixed-root resolution; configured-agent exclusion (`_effective_write_access`
  against the **configured** principal's ids); root ownership + safe ancestors;
  `{device, inode}` root-identity binding; a root-identity-bound
  `.authority/deployment-owner.json` (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`,
  closed schema, monotonic `generation`, `HPAC-WRITER-PROVENANCE/1.0` digest,
  `state == ACTIVE`); `generation == current_generation` against the anchored
  `HPAC-PAWA-CURRENT-GENERATION/1.0` record; a not-(configured-)agent
  current-context check; an `O_EXCL|O_NOFOLLOW` create-and-unlink positive write
  probe against a dedicated ephemeral sentinel under `.authority/`; an
  authorized-factory-consumer check; then mint + audit.
- **Capability issuer** = a new `PRODUCTION` writer factory in a
  **non-agent-importable** module (recommended
  `src/pcae/core/hpac_protected_admin_writer.py`), guarded by an **exact**
  consumer-inventory test (HBDC-REQ-056/066 pattern; **no wildcard / prefix /
  glob**).
- **Capability scope** = one administrative operation (5 closed mutation
  classes); one target principal / credential / enrollment-transaction;
  process-local; non-serializable (`__reduce__` raises); non-bearer (seal
  identity, not value); restart-invalid; **one-operation lifetime** (an additive
  `.1R.30R.3` spent-flag invariant, never a weakening of the existing type).
- **Bootstrap** = a one-time out-of-band deployment-owner `provision` step —
  create-only; non-recurring; not agent-reachable; **non-circular** (needs no
  existing `HPACWriterCapability`, no FIDO2, no prior PCAE principal).
- **Rotation** = explicit; `generation += 1`; a monotonic
  `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor; the old generation cannot mint.
  **Revocation** = deployment-owner filesystem replace/remove/mark; state
  `{ACTIVE, SUPERSEDED, REVOKED}`; revoked → fail closed. **Migration** = new
  `installation_id` + fresh root identity + `generation` 1; copying files alone
  is never sufficient.
- **Failure taxonomy** = 21 closed `pawa_failure_code` values (§56) mapping
  **deterministically** onto RHAMP-001 v1.0 §49 codes **#1
  `bootstrap_authority_unproven` / #2 `enrollment_not_protected_admin` / #40
  `protected_root_invalid` / #41 `internal_verification_error`** — **no new
  `terminal_reason_code`**; RHAMP-001 byte-unchanged.
- **Same-UID / two-principal requirement** = the configured agent principal
  SHALL be OS-separable from the deployment owner; where it is not, REAL
  `PRODUCTION` writer issuance is **INELIGIBLE** and no capability is minted —
  fail closed, never a downgrade.
- **Walls preserved** = writer capability ≠ `AuthenticatedHumanPrincipal` ≠
  approval proof ≠ PB permission ≠ Runtime Enforcement result ≠ runtime
  capability ≠ `DispatchEnvelope` ≠ execution. Local / offline only; no network,
  no cloud token, no signing key, no keychain (Candidates B/C/D rejected).

## Findings incorporated

- **F-1** — HPAC-PAWA-001 §10 freezes a **per-predicate identity matrix**:
  every recognition predicate names the exact identity it is evaluated against
  (the configured agent principal / the current invoking OS process / the
  protected-root owner / the descriptor owner / the importing source module / a
  fixed compiled-in path), its authority source, whether it is caller-controlled,
  and its failure behaviour. §9 fixes the configured agent principal's source of
  truth = **canonical PCAE agent configuration / lock** (`PCAE_AGENT_PRINCIPAL`),
  **never** `os.geteuid()`, never `--agent-id`, never caller input; unresolvable
  → `agent_principal_unknown` fail closed; no `agent_id=None` bypass. §26 / §62:
  the *negative* boundary check on the writer path keys off the **configured
  agent principal's** ids; the *positive* write probe keys off the **invoking
  process's** live capability. §27 bans "current user" as an authority term.
- **F-2** — HPAC-PAWA-001 §77 records: **`.1R.30R.3`, not `.1R.30R.2`, is the
  fresh implementation successor** (implementation needs the frozen contract
  first). The `.1R.30R` doc's §21.4 heading / §24 summary line are erroneous;
  the dominant statement and the `.1R.30R.1` IV are correct. Historical `.1R.30`
  stays immutable BLOCKED, never reused, never resumed (PAWA-INV-11).
  **No `.1R.30R` / `.1R.30` doc edit was made.**
- **F-3** — HPAC-PAWA-001 §14 adds `generation` + a closed `supersedes` object
  to the descriptor schema. §20: `generation` is monotonic, installation-local,
  strictly increasing (initial = 1; rotation = `previous + 1`); the current
  generation is anchored by a new protected `HPAC-PAWA-CURRENT-GENERATION/1.0`
  record (create-only at provisioning, atomic-replace-only on rotation,
  monotonic); recognition requires `descriptor.generation == current_generation`
  + digest match; `generation` is **not advisory**; if monotonic atomic-replace
  is unavailable the implementing phase STOPS (BLOCKED). §21: a bytes-only
  rollback of an old descriptor → `descriptor_generation_stale`.

## Contract-versioning verdict re-derived

**NEW COMPANION CONTRACT** — not (A) implementation-defined [would hide
normative trust decisions in code], not (C/D) an HPAC-001 MINOR/MAJOR [additive,
authority-preserving; a bump cascades — RIHAC-001 §12 cond 7 names "HPAC-001
v2.1" literally], not (E) BLOCKED [no circularity, no MAJOR redesign, no remote
infrastructure, no reusable same-UID bearer secret; HBDC-001 is a direct IV'd
precedent]. Companion precedent: REPRC-001 v1.0 / PBNDE-001 v1.0 / RHAMP-001
v1.0. HPAC-001 stays **v2.1**; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`;
RHAMP-001 stays **v1.0** byte-unchanged; the only version movement is
**HPAC-PAWA-001 v1.0 (initial freeze)**.

## Every valid early-STOP condition checked — NONE triggered

Canonical doc §9 walks each of the phase prompt's BLOCKED conditions; none
applies. HPAC-PAWA-001 is frozen without modifying HPAC-001 or RHAMP-001; the
HBDC-001 assumptions are expressed safely under HPAC's separate namespace; the
positive anchor is defined without `euid`/`root`/`sudo` alone as authority; the
configured-agent exclusion is stated precisely (§9, `_effective_write_access`
already parameterises `uid`/`gids`); the generation/rollback semantics are
frozen with a scoped `.authority/`-namespace record and the existing
atomic-replace idiom; the write probe is specified without TOCTOU ambiguity
requiring broader architecture (re-verify at write time); the capability stays
process-local/non-bearer/narrow-scope via an additive spent flag; the
out-of-band bootstrap is non-circular; migration is distinguished from
rollback; the consumer-inventory guarantee uses an existing PCAE guard pattern;
and the contract does not accidentally authorize runtime approval, PB, RE,
runtime capability, or execution.

## Governance

- `pcae health` healthy · `pcae check` passed · `pcae status coherence`
  coherent · `pcae doctor task-memory` warning-only historical `DONE.md`
  omissions (pre-existing hygiene debt; no current-phase error) ·
  `pcae push check` `nothing_to_push` (before the governed push) ·
  `pcae runtime inspect` `not_implemented / Observed / observe / unavailable`,
  0/0.
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved.
  Only the primary human-authorized operator holds `.1R.30R.2` lifecycle
  authority. Governed `pcae` lifecycle only — no raw `git commit`/`git push`,
  no `--no-verify`, no force push, no history rewrite, no hook bypass.
- No STOP / BLOCKED condition reached — every valid early-STOP condition in the
  phase prompt was checked (canonical doc §9) and none applies.

## Verdict

**HPAC-PAWA-001 v1.0: FROZEN** as the sole normative delta.

- **N-16-5: WRITER-ANCHOR CONTRACT FROZEN — IMPLEMENTATION PENDING — NOT
  CLOSED.**
- **PRODUCTION PROTECTED-ADMIN WRITER ANCHOR: CONTRACT FROZEN — NOT
  IMPLEMENTED.**
- **HPAC-001: v2.1 (NO bump). RHAMP-001: v1.0 (byte-unchanged). HBDC-001: v1.2
  (precedent only). Every other existing contract: byte-unchanged.
  `src/pcae/**`: unchanged.**
- **F-1 / F-2 / F-3: INCORPORATED.**

**Runtime: not_implemented / Observed / observe / unavailable. First external
effect: ABSENT. Execution enabled: NO. N-16-6 / N-16-7: OPEN, untouched, N-16-7
last. N-23-1 / N-23-2: carried.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3` — **N-16-5 Production Protected-Admin
Writer Anchor + Real FIDO2 Credential Registry and Authentication Mechanism
Implementation**. Requires its own separate explicit human authorization (ID
recommended, NOT reserved). It realises the originally intended historical
`.1R.30` scope from the adjudicated + frozen baseline; it is **NOT** a resumed
`.1R.30` (historical `.1R.30` remains immutable BLOCKED). Then `.1R.30R.4` (IV)
→ `.1R.30R.5` (protected presentation + real-assurance wiring) → `.1R.30R.6`
(IV + mandatory real-CTAP2-hardware verification + N-16-5 closure) → N-16-6 →
N-16-7 (strictly last). No Slice C until N-16-3..7 all close. **Do not begin
`.1R.30R.3`.** Do not modify `src/pcae`. Do not modify normative contracts. Do
not implement real FIDO2/WebAuthn/CTAP. Do not implement the protected UI. Do
not access hardware authenticators. Do not provision or write any protected
root. Do not begin N-16-6..7. Do not begin Slice C. Do not implement or call
the first external effect. Do not enable execution.

See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2_HPAC_PAWA_001_V1_0_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT_FREEZE.md`
and `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
