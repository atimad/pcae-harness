# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5 Complete — Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption Boundary Implementation

Status: completed.

Implementation-entry commit: `d502fc5c705dbce6b7f36cf73fac9bb7d427ebf0`.

Canonical hand-authored phase doc:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY_IMPLEMENTATION.md`.

## Technical verdict

**MECHANISM-NEUTRAL HPAC VERIFIER: IMPLEMENTED — INDEPENDENT VERIFICATION
PENDING — NOT YET CERTIFIED.**

Implemented `src/pcae/core/hpac_verifier.py`, executing
`HPAC-REQ-054`'s ten-step fail-closed verification sequence
(`docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` §18, read
directly rather than relying on `.1R.4`'s paraphrase) against the
existing, independently-verified Layer-1/2 foundation:

1. Resolve the canonical proof by `proof_id` only.
2. Resolve the principal; require `active` status.
3. Resolve the credential; require `active` status and binding to the
   claimed principal.
4. Mechanism compatibility + assertion-material check.
5. Presentation evidence: canonical resolution plus `approval_id`/
   `approval_subject_digest` binding checks.
6. Challenge-state consistency via the lifecycle chain's genesis binding.
7. UP/UV, both mandatory.
8. Freshness against `now` and the approval subject's `expires_at`.
9. Full canonical lifecycle chain resolution and genesis-binding
   cross-check.
10. Idempotent-or-fresh `PROOF_VERIFIED_AND_BOUND` transition, then
    ephemeral `AuthenticatedHumanPrincipal` emission.

`AuthenticatedHumanPrincipal` is trusted-construction-only (no public
constructor) and non-serializable (`__reduce__` raises); assurance
classification is copied from resolved records, never caller-declared —
the deterministic path always remains `FIXTURE_NON_REAL`, even with
UP/UV both true.

## Deliberate scope decision

`.1R.4` §9's input table lists `RuntimeInvocationApprovalStore` as a
verifier input. This implementation does **not** call it: no adapter
between `RuntimeInvocationApproval` (RIASC) and the HPAC-side
`CanonicalRuntimeApprovalSubject` exists in this codebase, building one
would exceed `.1R.4` §36's own restated no-go-bounded scope, and
`runtime_invocation_approval_store.py` is one of the three files the
future B1/B7/N1/N2 repair phase is scoped to modify. `approval_id` is
consumed only as an opaque binding key checked against records that
already carry it. Documented in the phase doc §9 as an explicit,
narrower-not-broader deviation, flagged for `...1R.5.1` to confirm or
revise.

## Tests

27 new tests (`tests/test_hpac_verifier.py`), all passing:
happy-path/assurance classification, canonical-resolution-only inputs,
presentation/invocation/approval binding, UP/UV defense-in-depth,
lifecycle state/replay, fixture-to-real upgrade rejection,
anti-forgery/anti-transfer, and zero-consumer/zero-effect static checks.

```
python -m pytest tests/test_hpac_verifier.py -q
27 passed
```

Three pre-existing "zero production consumers of the foundation"
regression tests were updated by exactly one exclusion-set line each to
allow `hpac_verifier.py` — the phase's own sanctioned, intentional
consumer — while continuing to reject any other consumer.

## Fast Green

`8796 passed, 0 failed` (5 skipped) after deselecting the exact 370
nodeids that failed or errored across repeated full
`pytest -m fast_green` runs at this phase's own HEAD — all independently
confirmed, by fixed-SHA `git stash` A/B against baseline `817b788a`, to
be pre-existing and confined to the unrelated HATP/HMIC/Class-B/HBDC
host-specific and order-sensitive test cluster (documented repository
debt). Zero attributable regressions.

## Consumer inventory

```
grep -rl "hpac_verifier" src/pcae --include="*.py" | grep -v "hpac_verifier.py$"   → (empty)
grep -rn "hpac_verifier" src/pcae/core/runtime_authority.py
                          src/pcae/core/runtime_dispatch_permission.py            → (empty)
```

Zero production consumers of `hpac_verifier.py` exist. PB, runtime
authority, and Gate 9 (`runtime_invocation_authority_consumption.py`)
remain unreferenced by the verifier (AST-checked).

## Governance verdict

**DELEGATED FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** (historical `.3`
incident, preserved, not revisited). No delegated agent was granted
commit, phase-finalization, or push authority in this phase.

## No-Go confirmation

- No B1, B7, N1, or N2 production repair (all remain contract closed /
  implementation open).
- No Permission Broker integration.
- No Runtime Enforcement or Shell Gate activation.
- No real FIDO2, WebAuthn, CTAP, enrollment, or credential operation.
- No protected approval UI, approval CLI, or enrollment CLI.
- No provider, network, subprocess, hardware, or external runtime effect.
- No Gate-9 production wiring, Gate-10 dispatch, or PB/runtime-dispatch
  consumption.
- No production trust-path file modified.
- No normative contract modification.
- No revert, force push, history rewrite, or hook bypass.

Runtime remains `Observed / observe / unavailable`. POL-005 unchanged.

## Commit and push state

Phase commits:

- `d502fc5c705dbce6b7f36cf73fac9bb7d427ebf0`
- `accf6273a972274da28e4e7d449eb92221294304`
- `319a64f075a0846fe0a553fed169443fc2bfb261`
- `2883315a2202bf2216ec6cd56a870c7b2cd858bf`

Pushed: pending (to be finalized after `pcae push`).

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.5.1`** — Independent Verification of
Mechanism-Neutral HPAC Verifier and Principal-Registry Consumption
Boundary Implementation. **Requires separate explicit human
authorization before starting.**
