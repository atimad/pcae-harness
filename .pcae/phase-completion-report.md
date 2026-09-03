# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2 Complete — N-16-5 Protected-Presentation Interactive Human Election and Portable Helper Launch Repair

- **Status:** COMPLETE — repair only.
- **H-2:** REPAIRED; fresh IV / real presentation certification pending.
- **F-2:** REPAIRED; fresh IV pending.
- **N-16-5:** NOT CLOSED.
- **Entry / attribution SHA:** `0250e5f7`.
- **Production diff:** exactly `src/pcae/protected_presentation_helper.py` and
  `src/pcae/core/protected_presentation.py`.
- **Contracts changed:** none.

## Repair

The production helper now opens `/dev/tty` directly, writes the exact
neutralized request-bound presentation, and accepts one exact `APPROVE` or
`REJECT`. Protocol input, inherited stdin, argv, environment, empty input,
EOF, invalid input, interruption, and no terminal cannot approve; each fails
closed to `CANCEL`. All C0/C1 and BiDi terminal-spoofing controls are
neutralized. The disclosed deterministic decision source remains NON_REAL and
unavailable to the production resolver.

The macOS Python 3.9.6 `/dev/fd/N` exit-zero/no-helper-execution failure was
reproduced. The launcher now uses the existing exact `sys.executable` with a
fixed `-I -c` bootstrap that reads and executes only the inherited,
launch-time-revalidated helper descriptor. Digest/current-generation and
held-inode TOCTOU guarantees remain intact. No path reopen, shell, PATH search,
caller-controlled executable or argv, cwd import, generic process API,
network, runtime capability, or external-effect authority was introduced.

## Evidence

- Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2 fresh suite: **71 passed, 0
  failed, 0 skipped, 0 errors**.
- Presentation implementation / IV / repair: **205 passed**.
- Historical guard sweep: **347 passed**.
- CTAP2 repair / IV: **96 passed**.
- Broad affected PAWA/PPA/RHAMP/FIDO2/verifier/Gate sweep: **893 passed**;
  two historical adversarial finding-demonstration nodes were explicitly
  deselected only after both failed identically at `A=0250e5f7`. Zero
  unexplained repair-attributable regression.
- `pcae health`, `pcae check`, and `pcae status coherence`: passed.
- Runtime: `not_implemented` / `Observed` / `observe` / `unavailable`, zero
  plugins/capabilities; first external effect absent/unreachable.

The carried F-1, sibling, moving-metadata, contract-set, and point-in-time
guards are pinned to exact immutable historical heads or exact filename sets.
No test definition was removed or renamed; no skip, skipif, `pytest.skip`,
xfail, wildcard, fnmatch, or generic-process-guard weakening was introduced.

A bounded real TTY smoke rendered a harmless request through the actual
helper. The session could not expose direct operator control of that PTY, so no
decision was synthesized; interruption returned `CANCEL` and no evidence. It
is not claimed as a genuine election or certification.

## Certification placement and boundaries

RHAMP-REQ-156 and HPAC-PPA-REQ-074 require a fresh post-repair independent
verification and real certification phase. Option A therefore applies.
Recommended successor, not begun:
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1` — Independent Verification of
Protected-Presentation Human Election + Final Presentation-Bound N-16-5
Certification and Closure. It must independently verify this repair and
complete a genuine terminal APPROVE → PPA evidence → genuine FIDO2 assertion →
`PRODUCTION` principal → existing Gate 5 chain before N-16-5 can close.

`pcae-protected-local-presentation/1.0` and
`hpac.fido2.uv_presence.v2` remain supported, non-exclusive profiles. A future
mobile-only profile remains open. N-16-6 and N-16-7 remain OPEN / UNTOUCHED;
N-16-7 stays strictly last. No runtime effect or execution was enabled.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.** The primary
human-authorized operator alone performed the governed lifecycle.
