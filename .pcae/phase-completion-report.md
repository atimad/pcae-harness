# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2 Complete — Independent Verification of the N-16-5 PAWA Production Protected-Admin Writer Anchor Implementation (Slice 1) (BLOCKED)

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2
**Type:** governed independent verification — re-derivation from primary source and frozen contract
**Status:** BLOCKED — a reproducible bypass of the PRODUCTION `HPACWriterCapability` one-operation / non-bearer invariant was found and independently confirmed; no repair, no contract edit, no test/guard weakening performed inside this IV
**Verification-entry SHA:** `V = aff46ec3` (== finalized `.1R.30R.3.1` head `I`); `A = 1793a75a` (finalized `.1R.30R.2A.3` head); `B30 = 8e655295` (immutable `.1R.30` BLOCKED); `origin/main..HEAD = 0` at entry
**Production source changed:** none (`git diff aff46ec3 HEAD -- src/pcae` empty — verification only)
**Normative contracts changed:** none (`git diff aff46ec3 HEAD -- docs/contracts` empty)
**Tests changed:** none (`git diff aff46ec3 HEAD -- tests` empty); the fresh `.1R.30R.3.1` 95-test suite was re-run unedited — 95 passed, 0 failed
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT AND UNREACHABLE; execution NOT enabled

## Summary

Independent re-derivation from primary source (not merely trusting
`.1R.30R.3.1`'s own claims) found and independently confirmed twice a
reproducible bypass of the PRODUCTION `HPACWriterCapability` one-operation /
non-bearer invariant (HPAC-PAWA-REQ-102/106/107).

`require_writer`'s only binding check is object identity
(`writer._authority_seal is self._seal`). `HPACWriterCapability.__new__`
bypasses the `__init__` constructor-seal gate entirely, and every slot
(`_authority_seal`, `role`, `subject`, `authority_class`, `_single_use`,
`_spent`) is then a plain, directly settable/readable instance attribute. A
shell object built via `HPACWriterCapability.__new__(HPACWriterCapability)`
that copies `_authority_seal`/`role`/`subject`/`authority_class` off a real,
already-held (even already-*spent*) capability, and sets `_spent = False`
directly, passes `require_writer` and authorizes a **second**, distinct
registry mutation from a single §33 recognition/mint event.

**Reproduced end-to-end** against the real `production_writer()` →
`HumanPrincipalRegistryStore` path (not mocked): legitimate
`enroll_principal` (capability spent), then a forged-capability
`revoke_principal`, both succeed.

**Contract note.** HPAC-PAWA-REQ-102 (§46) mandates exactly this raw
object-identity mechanism. HPAC-PAWA-REQ-103 (§47) and the §56 row-20
(`reconstruction_attempt`) text claim `object.__new__` reconstruction "fails
the seal-identity check" — false for a caller who already holds a real
capability object and can read its genuine seal reference directly.
Classified **product**, with a **contract note**: closing the gap likely
needs a small HPAC-PAWA-001 amendment alongside the code fix.

**Why the existing suite missed it.**
`test_55_object_new_reconstruction_rejected` constructs an empty,
seal-unset `__new__` shell — it "passes" only via an uncaught
`AttributeError` on the unset slot, not because forgery is rejected. The
copied-real-seal adversary was never exercised.

**Independently re-confirmed clean:** the exact 6-file `.1R.30R.3.1`
production diff; contract/`hpac_verifier.py`/Gate-5/Gate-9 byte-identity;
`_ELIGIBLE_MECHANISM_IDS` unwidened; no FIDO2/CTAP import in the new
surface; sole `HPACWriterCapability(` construction site; `writer()`
fixture-only hard stop preserved; non-agent-importable consumer fence
intact; runtime unchanged; sampled guard reconciliations additive-only.

No repair, no contract edit, no test/guard weakening performed inside this
IV — verification only, per the phase's own governance rules. This IV
changed zero `src/pcae`, `tests`, or `docs/contracts` files.

Full evidence in
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_2_INDEPENDENT_VERIFICATION_OF_N_16_5_PAWA_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_SLICE_1.md`.

## N-16-5 status

**NOT CLOSED.** Slice 1 is implemented but its own IV is **BLOCKED** pending
repair.

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2.1` — N-16-5 PAWA
`HPACWriterCapability` Seal-Forgery / One-Operation-Bypass Repair. Own
explicit human authorization required; ID recommended, NOT reserved. Do not
begin it. Do not begin Slice 2. `DELEGATED .3 FINALIZATION / COMMIT / PUSH:
UNAUTHORIZED` preserved — this phase's commit/push/finalization was
performed directly by the primary human-authorized operator.
