# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2

## Production Protected-Root / Protected-Presentation Helper Deployment Preparation

## Verdict

**BLOCKED before host mutation. F-6: OPEN / BLOCKING. F-5: OPEN /
UNCHANGED. N-16-5: NOT CLOSED.**

CPIPC-001 accepts the exact requested phase identifier. The immutable
predecessor/F-4-IV head and this phase entry are
`A = D0 = 7124c019bf3f46eb07456b81146484609197dbc2`. The governed task-opening
commit is `976bc226c18d8ced7fb548b155a27c83af1a4861`.

## Pre-deployment hard stop

The mandatory no-hardware pre-deployment regression sweep found a new current
moving-history defect before any protected-root mutation:

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_1_f4_immutable_scope_iv.py::test_43_no_protected_root_mutation_is_in_iv_diff`

The node evaluates:

```python
assert not any("protected-root" in p for p in git("diff", "--name-only", V).splitlines())
```

where `V = 90510428422e451382549ce76111610752aaafb4`, the F-4 repair head. Its
historical purpose was to prove that the F-4 independent-verification phase did
not mutate the production protected root. Its authority, however, is the moving
successor interval `V..HEAD`, and its predicate is a filename substring rather
than an immutable F-4-IV phase boundary or host-state evidence.

At finalized F-4-IV head `7124c019`, the unchanged node passes 1/1. At this
phase's legitimate successor task-opening commit, it fails solely because the
new governed task filename contains the authorized phase title words
`production-protected-root-protected-presentation-helper-deployment-preparation`.
No protected host state has changed. This is the same historical/live-successor
conflation class as F-4, but it is a distinct node and invariant.

Finding **F-6 — Immutable F-4-IV Host-Mutation Evidence Guard** is therefore
OPEN / BLOCKING. The correct semantic repair must bind the historical F-4-IV
"no protected-root mutation" fact to immutable F-4-IV phase evidence, not live
successor filenames. This deployment-preparation phase is not authorized to
repair that predecessor verification defect, rename the task to evade it, skip
the node, or weaken its assertion.

## Deployment reconstruction completed read-only

The frozen deployment model was re-derived sufficiently to establish that it
is non-circular: the deployment owner first provisions the fixed PAWA protected
root and installs exact content-addressed helper bytes out of band; the
standalone `hpac_protected_presentation_admin.py` then obtains one process-local
`configure_presentation_mechanism` capability for exact mechanism
`pcae-protected-local-presentation` and action `install`, and completes one
bounded metadata multi-write. Installer, launcher, evidence writer, and human
approver remain separate. No generic executable installation authority is
present or authorized.

The fixed macOS production root remains
`/Library/Application Support/PCAE/HPAC/protected-root`. Read-only inspection
confirms it is absent, with no presentation installation descriptor, current
generation, or helper bytes. `hpac_protected_presentation_admin.py status`
reports no presentation-mechanism installation.

Because the prompt requires aborting host mutation when a current unexplained
blocking software regression exists, the phase stopped at this precondition.
No administrator prompt was opened; no directory, helper, descriptor,
generation, PAWA capability, evidence, principal, PB permission, or runtime
capability was created.

## Verification and boundary results

- Pre-deployment focused deterministic sweep: **522 passed, 1 failed**; the
  sole failure is F-6 above.
- Immutable predecessor reproduction: the exact F-6 node is **1 passed** at
  `7124c019` and **1 failed** at the legitimate successor.
- Production source, production scripts, dependencies, and normative contracts:
  unchanged from `D0`.
- F-3 and F-4 repairs remain unchanged; F-4's core immutable-scope guard remains
  independently verified. The new defect is the adjacent F-4-IV host-mutation
  guard, not a regression in the repaired F-4 node.
- F-5 host state: absent and unchanged.
- Human protected election and YubiKey interaction: none.
- Runtime: `not_implemented / Observed / observe / unavailable`, zero plugins,
  zero capabilities; first governed runtime external effect remains absent.
- N-16-6 and N-16-7: open and untouched.

## Disposition

F-5 deployment preparation did **not** occur and cannot be reported PREPARED.
N-16-5 remains **NOT CLOSED**. A fresh narrow repair successor must first repair
F-6 using immutable historical F-4-IV evidence, followed by fresh independent
verification. Only then may a separately authorized F-5 deployment-preparation
retry occur, followed by deployment IV and final real certification.

FIDO2/YubiKey remains one real-hardware-verified supported authentication
profile, not exclusive. Local protected TTY remains one supported presentation
profile, not exclusive. Mechanism-neutral human authentication and protected
approval, including a mobile-only profile, remain open planned future
architecture and are not prerequisites for unrelated non-effecting work.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.**
