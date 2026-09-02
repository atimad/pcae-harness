# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5 — Independent Verification of the N-16-5 Merged RHAMP Real FIDO2 Credential Registration, Counter-State, Bootstrap & Authentication Mechanism Implementation

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.5
**Type:** governed independent-verification phase (verification only — no production/contract repair)
**Status:** **BLOCKED.** N-16-5: **NOT CLOSED.**
**A (finalized `.1R.30R.3.3R` head):** `5a6f9d87`
**I (finalized `.1R.30R.3.4` head):** `c9cf99d5`
**V (`.1R.30R.3.5` phase-entry SHA):** `c9cf99d5` (= HEAD at entry; `origin/main..HEAD = 0`)

All three SHAs were independently re-derived from `git log`/`git rev-list`, not inherited from the `.1R.30R.3.4` report's prose.

## What was independently re-verified (clean)

- **Production diff inventory (A→I):** `git diff --name-status A I -- src/pcae scripts pyproject.toml` returned exactly the claimed 9 new + 4 modified files. No unexpected production change.
- **Contract byte-identity:** RHAMP-001 v1.0, HPAC-PAWA-001 v1.1, HPAC-001 v2.1, and every other file under `docs/contracts` are byte-unchanged A→I (`git diff --name-only A I -- docs/contracts` empty). `pyproject.toml` byte-unchanged (no new dependency; `fido2>=1.1,<2` was already the `hatp-hardware` extra).
- **CredentialRecord identity:** no diff hunk touches `class CredentialRecord` or `_CREDENTIAL_ALLOWED_FIELDS` anywhere A→I — schema byte-unchanged.
- **Registration call graph:** independently traced in `hpac_rhamp_enrollment.py` — PAWA mint → `handle.consume` → native `make_credential` → creation-result validation (rpIdHash / UP / UV / algorithm / transport) → duplicate-credential check → sidecar create-only write → counter-state create-only write → **registry `enroll_credential` append is the true ACTIVE-publish boundary** → `complete_multi_write`. Ordering is correct: every artifact written before the registry append remains non-authoritative.
- **Mechanism/vocabulary exactness:** `_ELIGIBLE_MECHANISM_IDS` is exactly the 2-member frozenset `{hpac.deterministic.test-only.v1, hpac.fido2.uv_presence.v2}` (no wildcard/prefix). `terminal_reason_code` is exactly the closed 41-value enum.
- **Presentation/Gate fence:** no `require_real_assurance` wiring into Gate 5 or Gate 9 (both byte-identical A→I); no `pcae-protected-local-presentation/1.0` implementation exists anywhere in the diff; the real `hpac_verifier` branch cannot mint a PRODUCTION `AuthenticatedHumanPrincipal` end-to-end because no PRODUCTION presentation descriptor kind is accepted yet.
- **Runtime/effect boundary:** `pcae runtime inspect` confirms `Observed / observe / unavailable`, 0 plugins, 0 capabilities. No `adapter.dispatch(` or effect-adapter pattern was introduced. First external effect remains absent/unreachable. N-16-6/N-16-7/Slice C untouched.
- **No test weakening:** no pre-existing `def test_` was renamed, removed, skipped, or `xfail`-marked beyond the pre-existing POSIX platform guards already present at A.
- **Suite reruns:** the unchanged `.1R.30R.3.4` implementation suite reran **124/124 passed**. A broad deterministic, non-xdist RHAMP/FIDO2/PAWA/HPAC lineage sweep showed 25 pre-existing failures at A and the identical 25 at I (verified via a disposable `git worktree` at A, since removed) — **zero I-only unexplained regressions**.
- **PAWA Slice 1:** remains CLOSED, unchanged; the additive `_multi_write` slot on `HPACWriterCapability` is strictly additive per HPAC-PAWA-REQ-082/107.
- **No custom cryptography:** the only signature primitive is `fido2`'s `CoseKey.verify`/CBOR handling plus stdlib `hashlib`; no hand-rolled crypto.

## BLOCKING finding — `_multi_write` completion has no re-entry/replay guard

**Exact evidence:** `HPACStoreAuthority.complete_multi_write`, `src/pcae/core/hpac_foundation.py:739-758`, never checks the capability's existing `_spent`/registry-`CONSUMED` state before spending it — unlike every other authority entrypoint in the same class (`require_writer`, `record_write`), which explicitly defends against exactly this pattern.

**Reproduced (fresh tests, not assertion):**
- Calling `complete_multi_write` a second time on an already-completed capability does **not** raise — contradicting the method's own docstring, which claims a second call fails closed with `capability_stale`.
- 8 concurrent threads calling `complete_multi_write` on the same capability **all "succeed"** — no exclusivity is enforced at the completion boundary.

**Classification:** this is a direct match to the phase's own listed BLOCKED trigger — *"`_multi_write` weakens the verified one-operation / non-bearer semantics"* — i.e. the spec §12/§13 required invariant that one PAWA issuance authorizes **at most one** predeclared bounded multi-artifact transaction, not reusable writer authority.

**Mitigating factor (independently checked, not assumed):** no live production exploit path exists today. `record_write`'s independent `require_writer` gate already rejects any further durable write once `_spent` is first set `True` by any completion, and the sole production call site (`hpac_rhamp_enrollment.py:302`) invokes `complete_multi_write` exactly once, synchronously, on a capability local to a single ceremony invocation. This is a **latent contract violation** in `complete_multi_write` itself, not a currently-reachable double-registration.

## Fresh independent IV suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_5_merged_rhamp_iv.py` — new, 16 tests: 14 pass, 2 fail. Both failures are the exact finding above, deliberately left failing/uncorrected — this IV is verification-only and may not repair production code.

## Verdict

Per §75-80 of the phase's own directive, a clean "INDEPENDENTLY VERIFIED" outcome is not available. The registration, counter-state, bootstrap, makeCredential/getAssertion, and presentation-fence surfaces all independently verify cleanly, but the `_multi_write` completion-boundary gap is a genuine, reproducible violation of a decisive documented invariant and therefore requires a **BLOCKED** disposition rather than force-fitting success.

- RHAMP credential registration: VERIFIED
- RHAMP counter-state: VERIFIED
- PAWA protected-admin bootstrap: VERIFIED
- Multi-artifact registration atomicity: VERIFIED (the registry publish point itself is correctly ordered)
- `_multi_write` bounded authority: **NOT VERIFIED** (decisive finding above)
- FIDO2HumanAuthenticator: VERIFIED
- makeCredential path: VERIFIED
- getAssertion path: VERIFIED
- rpIdHash / UP / UV / COSE signature / challenge-replay: VERIFIED
- Counter linearization: VERIFIED
- hpac_verifier REAL branch: VERIFIED
- Deterministic CI isolation: VERIFIED
- Production presentation fence: VERIFIED
- Contract↔production equivalence: VERIFIED

**N-16-5: NOT CLOSED.**

## Recommended successor

**149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6** — narrow repair phase: add the missing already-spent/`CONSUMED` re-entry guard to `HPACStoreAuthority.complete_multi_write` (mirroring `require_writer`'s existing pattern), so the method's own documented fail-closed contract holds structurally rather than only incidentally via `record_write`'s independent backstop. Scope limited to that one method plus the 2 currently-failing IV tests. Do not reopen the registration/counter/getAssertion surfaces already cleanly verified in this phase. Own explicit human authorization required before beginning it.

Do not begin N-16-6, N-16-7, or Slice C. Do not implement protected presentation. Do not wire `require_real_assurance` through Gate 5/9.
