# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.4 Complete — Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption Boundary Implementation Planning

Status: completed.

Planning-entry commit: `95644e028a9b1244fa0901f309226b11824796e0`.

Canonical hand-authored phase doc:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_4_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY_IMPLEMENTATION_PLANNING.md`.

## Technical verdict

**PLANNING COMPLETE.**

`.1R.2`'s §1 claims the design is "eight non-collapsible layers" but never
enumerates them; §52/Matrix E instead lists ten concrete sub-phases whose
"Phase 2" bundles the mechanism-neutral HPAC verifier together with
B1/B7/N1/N2 production-authority repair. This phase:

1. Reconstructed the only eight-item decomposition consistent with both
   claims (splitting old Phase 1 into L1/L2/L4 and old Phase 2 into L3/L5).
2. Re-derived from primary contract text — not assumed — that L3 (verifier)
   is architecturally separable from L5 (B1/B7/N1/N2 repair): the verifier
   consumes only the already independently-verified foundation, its
   HPAC-REQ-056 `AuthenticatedHumanPrincipal` output is contractually
   ephemeral and non-serializable (HPAC-REQ-058), and N2's repair is a
   *consumer* of the verifier, not a co-requisite for building it.
3. Produced a full implementation plan for the standalone verifier:
   responsibilities (HPAC-001 §18's already-normative 8-step algorithm),
   explicit non-responsibilities, input/output contracts, trust/provenance
   model, anti-transfer model, NON-REAL assurance classification,
   principal/proof/presentation/lifecycle consumption ownership, Gate-5/
   Gate-9 relationship, fail-closed failure model, error-taxonomy reuse
   (no new parallel taxonomy), persistence decision (ephemeral only, no
   new store), a 25-vector threat matrix, and a test plan.
4. Froze the exact next-phase IDs following this repository's observed
   `.<N>`/`.<N>.1` naming convention (re-derived from `docs/` listing, not
   assumed): **`149O.20L.7O.3W.1R.2B.1R.1.1R.5`** (verifier implementation)
   and **`...1R.5.1`** (its independent verification) — not `.1R.4.x`,
   which would incorrectly imply this planning phase itself needed repair.

No verifier code was written. No production trust-path file
(`human_principal_registry.py`, `approval_presentation.py`,
`human_authentication_proof.py`, `hpac_lifecycle.py`,
`runtime_invocation_authority_consumption.py`, `runtime_authority.py`,
`runtime_dispatch_permission.py`) was modified. No contract file was
modified. `.1R.2` was treated as historical evidence and not overwritten.

## Reconciliation summary

| | |
|---|---|
| Old plan | `.1R.2 §52` Phase 2 = verifier (L3) + B1/B7/N1/N2 repair (L5), bundled |
| Verified implementation experience | L1/L2/L4 foundation required three repair/re-verify rounds (`.1R.3.1→.3.2→.3.2.1→.3.2.2→.3.2.2.1`) at fine single-responsibility granularity; N2 repair structurally consumes the verifier's output, so a phase building both cannot be independently verified without first independently verifying the thing it depends on |
| Revised sequence | L3 becomes its own governed phase (`...1R.5`) with its own independent verification (`...1R.5.1`), before L5 (`...1R.6`/`...1R.6.1`) begins |

## Central planning decision

**Verifier-only separation is architecturally valid.** Re-derived from
HPAC-001 §18/§19, RDGO-001 §6/§10, and PBRD-001 §7: the verifier can
consume trusted canonical HPAC foundation state, produce a
mechanism-neutral non-authorizing ephemeral result, remain unconsumed by
production runtime authority, remain independent of PB, and remain
independent of `RuntimeInvocationApproval` repair — all five criteria hold
without forcing a carve-out.

## Verifier scope frozen for the next phase

- **Responsibilities:** HPAC-001 §18's 8-step algorithm in full (canonical
  approval/proof resolution, registry/credential/subject binding, trusted
  presentation/attestation verification, credential signature
  verification, UP+UV, freshness, lifecycle/replay resolution, atomic
  `PROOF_VERIFIED_AND_BOUND` creation + `AuthenticatedHumanPrincipal`
  emission).
- **Exclusions:** no PB `ALLOW`/POL evaluation; no Gate-5 projection
  object; no Gate-9 consumption write; no B1/B7/N1/N2 repair; no real
  FIDO2/UI; no cacheable "verified" flag.
- **Output/authority model:** `AuthenticatedHumanPrincipal` is the
  existing frozen contract type (HPAC-REQ-056) — not invented here.
  Trusted-construction only, ephemeral, non-serializable — closes the
  anti-transfer/copied-result/caller-forgeable-boolean threats by
  construction, not by adding new binding fields.
- **NON-REAL handling:** deterministic-mechanism success must carry
  `FIXTURE_NON_REAL` assurance classification copied from the resolved
  mechanism's provenance, never conflated with real human authentication.
- **Persistence:** ephemeral only; no new canonical store; the durable
  evidence is the existing `PROOF_VERIFIED_AND_BOUND` lifecycle event.

## Threat matrix and test plan

25-vector threat matrix (forged/copied principal, proof, presentation,
attestation; mechanism/installation/challenge/invocation substitution;
UP/UV false; revocation; expiry; replay; stale/disconnected lifecycle;
copied/constructed/reused verifier result; deterministic relabeling;
canonical-looking record outside trusted store; internal failure) is
mapped to specific rejection behavior in the phase doc §30. Test plan
(§31) covers per-step unit tests, all 25 adversarial cases, foundation
regression re-run (80 passing per `.1R.3.2.2.1`), and PB/runtime-authority
zero-consumer tests.

## Governance verdict

**DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** (historical `.3`
incident, preserved, not revisited). No delegated agent was granted
commit, phase-finalization, or push authority in this phase.

## No-Go confirmation

- No verifier implementation (`hpac_verifier.py` not created).
- No production trust-path modification.
- No normative contract modification.
- No B1, B7, N1, or N2 production repair (all remain contract closed /
  implementation open).
- No Permission Broker integration.
- No Runtime Enforcement or Shell Gate activation.
- No real FIDO2, WebAuthn, CTAP, enrollment, or credential operation.
- No protected approval UI, approval CLI, or enrollment CLI.
- No provider, network, subprocess, hardware, or external runtime effect.
- No Gate-9 production wiring, Gate-10 dispatch, or PB/runtime-dispatch
  consumption.
- No historical `.1R.2` or `.1R.3.x` artifact rewrite.
- No revert, force push, history rewrite, or hook bypass.

Runtime remains `Observed / observe / unavailable`. POL-005 unchanged.

## Commit and push state

Phase commits:

- `95644e028a9b1244fa0901f309226b11824796e0`
- `8b77c434253923fd6d38377c77f8081af2a40387`
- `003a5adadfe942bd38069121d6f71b21747fa76c`

Pushed: pending (to be finalized after `pcae push`).

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.5`** — Mechanism-Neutral HPAC Verifier and
Principal-Registry Consumption Boundary Implementation. **Requires
separate explicit human authorization before starting.** Its independent
verification phase is **`149O.20L.7O.3W.1R.2B.1R.1.1R.5.1`**.
