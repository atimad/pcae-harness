# Phase 149O.20L.7O.2N.10 — HRAC-001 Independent Verification

## Verdict

```
HRAC-001 v1.0
REMOTE WEBAUTHN ASSERTION CEREMONY COMPANION
— INDEPENDENTLY VERIFIED
ASYNC REQUEST/RESPONSE STATE MACHINE
— VERIFIED
ONE-TIME CONSUMPTION / CONCURRENCY
— VERIFIED
HSCE-001 + HRWP-001 COMPOSITION
— VERIFIED
REMOTE SIGNING EVIDENCE ORCHESTRATION
— VERIFIED
NO IMPLEMENTATION
NO REAL HARDWARE EFFECT
```

**Verdict letter (§64 of the governing prompt): B — VERIFIED WITH NON-BLOCKING FINDINGS — NEXT PREREQUISITES MAY PROCEED.**

No Blocking defect found. One Non-Blocking finding is carried forward
(not newly discovered — independently reconfirmed): the `protocol_name`
closed-vocabulary contradiction first identified in Phase
149O.20L.7O.2N.8 and correctly carried forward, undisturbed, by HRAC-001
§44 (HRAC-REQ-066) and by the prior phase (2N.9). This finding is
Non-Blocking for HRAC-001's own contract-text coherence but remains
Blocking for any future real remote-WebAuthn credential *enrollment*
(and therefore for the *assertion* ceremony this contract governs, which
requires an already-enrolled credential to exist).

## True phase-entry commit

`c0e914f9` — Phase 149O.20L.7O.2N.9: exact-match origin_main_head/push-state fields post-push (HEAD at phase start, `main`, clean, nothing_to_push).

## Contract under verification

- **Identity:** HRAC-001
- **File:** `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md`
- **Reported version:** v1.0
- **Predecessor:** Phase 149O.20L.7O.2N.9 (freeze)

## Contracts / source independently read this phase

- `docs/contracts/HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md` (HRAC-001, full text, all 76 requirements)
- `docs/contracts/HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md` (HRWP-001, full requirement-number sweep, §4/§7/§12-§13/§16/§18/§20-§25/§27/§35 read in depth)
- `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md` (HSCE-001 v1.3, §24 atomic-write/exclusive-publish text (HSCE-REQ-052) and §32/§48 TOCTOU text (HSCE-REQ-068/069/070/080/083) read in full)
- `src/pcae/core/hatp_signing_ceremony.py` (production synchronous orchestrator — `resolve_signing_context`, `_resolve_deployment_binding_signer`, `sign_rollback_evidence`, the `input()` confirmation call site)
- `src/pcae/core/hatp_hardware_credentials.py` (`_PROTOCOL_VALUES` frozenset, current production closed vocabulary)
- `src/pcae/core/hatp_fido2_provider.py` (corroborating evidence for the WebAuthn-signature-counter/non-byte-identical-assertion reasoning behind the one-time-consumption finding, §14 below)

Not independently trusted as an oracle: Phase 149O.20L.7O.2N.9's own
tests, summary/report prose, state-count claim, HSCE-compatibility
claim, or one-time-consumption claim. Every load-bearing claim below was
re-derived from the primary sources listed above and cross-checked by
the fresh test suite (`tests/test_phase_149o_20l_7o_2n_10_hrac_001_independent_verification.py`,
32 tests, none copied from 2N.9's suite).

## 1. Requirement completeness

Independently re-extracted `HRAC-REQ-\d+` via regex over the contract
text: 76 matches, values `001..076`, `sorted(set(...)) == range(1,77)` —
sequential, gapless, no duplicate bold-defined requirement. Confirmed
mechanically (`test_hrac_requirement_numbering_is_complete_sequential_no_gaps_no_duplicates`).

## 2. Authority-boundary verification

HRAC-001 §2 (HRAC-REQ-003/004) correctly limits itself to async
request/response orchestration, correlation, one-time consumption, and
evidence capture. It does not redefine:
- HRWP-001's cryptographic verification algorithm (HRAC-REQ-033/034
  explicitly call HRWP-001's verifier "exactly once" and treat its
  outcome as dispositive — no second, competing check).
- HSCE-001's `HumanApprovalProvenanceProof`/`HATPSignedEvidenceEnvelope`
  shape (HRAC-REQ-049/050/052 reuse `canonicalize_hatp_proof_payload`,
  `build_hatp_signed_evidence_envelope`, and `HATPEvidenceStore.publish`
  unmodified — confirmed against HSCE-REQ-032's closed four-field
  schema, itself unamended).
- HPSE-001/HBDC-001 identity/binding schema (HRAC-REQ-019-021 reuse
  `DeploymentBinding`/`SignerRecord` resolution verbatim via
  HSCE-REQ-080, never a second disambiguation step).

No authority overreach found.

## 3. Synchronous-vs-async signing analysis

Independently traced `hatp_signing_ceremony.py::sign_rollback_evidence`
and `resolve_signing_context`/`_resolve_deployment_binding_signer`. The
production flow is exactly what HRAC-REQ-008 describes: one CLI
invocation running (1) context resolution, (2) signer resolution, (3)
synchronous `input()`-gated human confirmation, (4) one synchronous
`provider.request_signature(...)` call blocking on hardware touch, (5) a
second TOCTOU resolution pass, (6) envelope construction/publish — all
in one process, no persisted intermediate state. HRAC-REQ-009's claim
that only steps (3)-(4) become asynchronous in the remote path, with
(1),(2),(5),(6) unchanged in kind but required to run again at
verification time, is accurate and does not silently drop or alter any
of the six steps.

## 4. State machine — exact verification

Independently modeled the closed 7-state set and the 7 listed
transitions as a graph (not copied from the contract's own prose) and
mechanically confirmed via `tests/test_phase_149o_20l_7o_2n_10_...py`:

- Every non-terminal state (`PENDING`, `RESPONSE_RECEIVED`, `VERIFIED`)
  has at least one outgoing transition — no dead end.
- No transition originates from a terminal state (`COMPLETED`,
  `EXPIRED`, `FAILED`, `CANCELLED`) — terminal closure holds.
- Every one of the 7 states is reachable from `PENDING` by BFS.
- No cycle exists anywhere in the transition graph (DFS cycle check over
  all 7 states) — this is a true DAG, so "no transition can reopen a
  terminal state" is not merely asserted but structurally impossible.
- The contract's own prose table matches the independently-derived
  graph exactly, and no additional named state beyond the closed 7
  appears anywhere in the document (regex-swept).

No unreachable state, no missing terminal state, no illegal transition,
no cycle, no reopened terminal state.

## 5. Request identity

`request_id` is specified as a fresh CSPRNG value (`secrets.token_hex(32)`-equivalent),
explicitly *not* content-addressed — correctly distinguished from
HSCE-001's `evidence_id = digest_hatp_proof_payload(proof)` convention.
This is the right choice: a pending request precedes any signed content,
so content-addressing would incorrectly collide two independently-issued
concurrent requests for the same operation. Verified the reasoning is
sound, not merely asserted.

## 6. Challenge context / canonicalization / domain separation

The HRAC-REQ-022 challenge context enumerates 13 fields (`request_id`
through `expires_at`) — independently confirmed all 13 appear in the
isolated HRAC-REQ-022 text block, no silent omission. Canonicalization
reuses HSCE-REQ-053's existing discipline (UTF-8, `sort_keys=True`,
`allow_nan=False`, duplicate-key rejection) — not reinvented. The wire
challenge is `sha256(canonical_challenge_context_bytes)`,
base64url-encoded (WebAuthn's own convention, correctly distinguished
from this repo's own plain-hex convention used elsewhere, with a stated
reason: this value crosses the browser API boundary). Domain separation
is the fixed string `PCAE/HATP/HRAC/SIGN/V1`, confirmed absent from
HRWP-001's own text (no accidental cross-contract string collision).

## 7. Replay protection / one-time consumption (load-bearing)

This is the single most load-bearing claim in the contract: that
HSCE-REQ-052's exclusive-publish (`os.link` against a path keyed by
`evidence_id`) generalizes safely to a *different* keying scheme
(`request_id`) and a *different* consumption semantics (no
idempotent-duplicate branch).

Independently re-read HSCE-REQ-052 in full (`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
§24): the technique is temp-file-in-same-directory → write+flush+fsync →
`os.link(temp_path, final_path)` as the exclusive-create primitive.
`os.link`'s exclusivity guarantee (POSIX: fails atomically with
`FileExistsError` if `final_path` already exists) is **keying-agnostic**
— it provides "first successful call wins" regardless of what string the
path is derived from. HSCE-001 keys it by `evidence_id` (content
address) *because* two independently-produced identical envelopes are a
legitimate idempotent case there. HRAC-001 keys the identical mechanism
by `request_id` and, correctly, does *not* carry forward the
idempotent-duplicate branch: HRAC-REQ-036 explicitly states there is "no
meaningful same-answer-safe-to-ignore case" because each WebAuthn
`getAssertion()` call increments the authenticator's own signature
counter and re-signs fresh bytes — corroborated independently against
`hatp_fido2_provider.py`'s own `Ctap2`/`get_assertion` usage, which
confirms per-call fresh signing is the actual WebAuthn/CTAP2 behavior,
not an invented property. This divergence from HSCE-REQ-052 is
**explicit and justified**, not silent — the correct disposition. The
underlying atomicity primitive is unchanged and requires no new proof of
correctness; only the keying and the post-loss handling differ, and both
differences are independently sound.

**Conclusion: the HSCE-REQ-052 generalization is safe and correctly
adapted, not merely analogized.** This closes the single item the
governing prompt flagged (§14/§63) as the most likely site of a
Blocking defect.

## 8. Concurrency — exactly one winner

Modeled the Mac-and-iPhone-concurrent-valid-assertions scenario directly
against the `os.link`-keyed-by-`request_id` mechanism: since `os.link`
provides OS-level, not application-level, mutual exclusion, exactly one
concurrent caller's `os.link` call can succeed for a given `request_id`;
every other caller — even one whose own HRWP-001 verification
independently succeeds — necessarily receives `FileExistsError` and is
rejected as `request_already_consumed` (HRAC-REQ-038/039). No two
signing results are producible for one request under any interleaving.
The contract states this correctly and does not silently rely on
application-level locking that a real concurrent-process implementation
could get wrong.

## 9. Multiple outstanding requests / response correlation

HRAC-REQ-040/023 correctly forbid any "most recent pending request"
selection logic (confirmed present verbatim, `SHALL NOT` binding) — every
response must bind to an exact `request_id`, with a mismatch rejected as
`malformed_response` before further processing (§23/HRAC-REQ-032/040).
`request_id` alone is explicitly insufficient for correlation
authority — HRAC-REQ-033 step (3) requires the embedded WebAuthn
challenge to also be reconstructed and matched server-side (never
trusted from the client), satisfying the governing prompt's §18
requirement that request-ID-plus-challenge, not request-ID alone, gates
correlation.

## 10. HRWP-001 verifier handoff / EXPLICIT_SIGNER

HRAC-REQ-033/034 correctly delegate all cryptographic/origin/RP-ID
checking to HRWP-001's authoritative verifier, calling it exactly once
and treating its outcome as dispositive — no competing verification
logic. EXPLICIT_SIGNER (HRWP-REQ-014) is reused, not re-litigated:
independently confirmed HRAC-001's text contains neither `ANY_ACTIVE`
nor `PREFERRED_WITH_FALLBACK` (the two policies HRWP-001 explicitly
rejected in favor of EXPLICIT_SIGNER) — no silent reopening of that
policy choice.

## 11. Revocation / DeploymentBinding-change / source-change races (load-bearing)

This is the second most load-bearing claim: whether a stale pending
request can bypass a mid-flight revocation or binding change.

HRAC-REQ-033 step (2) requires the orchestration layer to **re-resolve**
HRAC-REQ-017's live-state fields a second time at verification time —
repository identity, `DeploymentBinding`/`SignerRecord`/`PrincipalRecord`/
`HardwareCredentialRecord`, and Decision/Binding digests — using the
identical HSCE-REQ-083 cross-record TOCTOU discipline, independently
re-read in full from HSCE-001 §48. HSCE-REQ-083 confirms this
discipline compares canonical field values (not object identity) and
treats *any* difference, including same-principal/same-signer changes to
authority-relevant binding or credential fields, as a fail-closed
mismatch. HRAC-REQ-033 step (4) correctly discards the freshly-verified
assertion and captures no evidence on any TOCTOU mismatch
(`toctou_context_changed`), mirroring HSCE-REQ-070's "discard, persist
nothing" discipline exactly. **A stale pending request created before a
mid-flight revocation, `DeploymentBinding` change, or source/HMIC
validity change cannot bypass that change** — the recheck is
unconditional and runs on every verification attempt, not merely
requested. No Blocking defect found here.

## 12. Governance-authorization revocation/cancel

If the underlying governed authorization is withdrawn, HRAC-REQ-016/034/057
require the ceremony to never manufacture or substitute for it — the
signer/binding TOCTOU recheck (§11 above) is the operative mechanism by
which a withdrawn authorization surfaces at verification time. No gap
found: cancellation of the *request itself* (§24, `PENDING`-only, HRAC-
REQ-041/042) is a distinct, correctly-scoped operation from withdrawal
of the underlying *authorization*, and the two do not conflict.

## 13. Expiry / late response

Server-clock authoritative (HSCE-REQ-068's existing clock discipline
reused), a late response rejected as `expired_challenge` before any
verification call, with no path back to `PENDING`/`RESPONSE_RECEIVED`
(HRAC-REQ-013/037). Confirmed distinct from "no response ever arrived" —
both collapse to the same terminal `EXPIRED` outcome, which is the
correct simplification (no observable difference downstream).

## 14. Cancellation

`CANCELLED` exists, is `PENDING`-only, requires authorization at least
equal to the request-creation tier, invalidates the ceremony session
immediately, and a late response against a cancelled request is rejected
as `request_cancelled` (never silently accepted or misreported as
`expired`) — a real, distinct error category, correctly not collapsed
into `expired_challenge` the way server-restart is (§15 below).

## 15. Server restart / durability

v1.0 explicitly chooses non-durability for `PENDING`/`RESPONSE_RECEIVED`
requests across restart — stated as a deliberate scope choice with an
explicit externally-observable-effect argument ("identical to
`expired_challenge`: no completion is ever possible"), not an
unresolved ambiguity. `COMPLETED` evidence durability is inherited
unchanged from HSCE-001's own crash-after-publish guarantee. No
half-durable ambiguity found.

## 16. Request-store semantics

Correctly scoped as authority-bearing only for consumption-marking and
TOCTOU-snapshot storage, never for cryptographic trust (mirrors
HSCE-REQ-060/061's "evidence-file existence is never approval," restated
for request records). Locking requirement is the same atomic-exclusive-
create primitive already required for consumption (no second locking
primitive introduced). Literal path/topology is correctly left open
(this store may need network-process reachability, a topology decision
this contract does not select) — named as an implementation-phase
decision, not silently assumed.

## 17. Terminal-state immutability

Structurally proven in §4 above (DAG check: no transition originates
from a terminal state, confirmed for all 4 terminal states).

## 18. Evidence capture / raw-material retention / signing-result handoff

The remote evidence record (HRAC-REQ-051) is additive to, never a
modification of, HSCE-001's closed four-field `HATPSignedEvidenceEnvelope`
schema (HSCE-REQ-032, independently confirmed unamended). Raw
`clientDataJSON`/`authenticatorData`/`signature` retention is correctly
bounded to whatever HRWP-001's own evidence schema (HRWP-REQ-050)
already persists — no second, redundant raw copy. The signing-result
handoff to HSCE (HRAC-REQ-049/050) is a *verified* proof/result, never
raw unverified browser JSON — the §18 client response schema is
discarded once verification succeeds.

## 19. Evidence profile / closed-vocabulary audit

`provider_profile = HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN` (already
existing HRWP-001 vocabulary) is a sufficient discriminator; HRAC-001
introduces no second, redundant type field on the envelope (no schema
widening of HSCE-REQ-032's closed four-field set — confirmed). New
vocabulary items this contract introduces (`operation_type`, `error_type`,
state-machine values) are each required to be closed
`Enum`/`frozenset` values from first implementation, not open strings —
confirmed present as an explicit requirement, not left to a future
implementer's discretion.

## 20. `protocol_name` finding — independently reconfirmed

Directly inspected `src/pcae/core/hatp_hardware_credentials.py`:
`_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})` (line 56) — confirmed
`"WEBAUTHN"` is still absent from current production. HRAC-REQ-066's
claim that HRAC's own signer-resolution reuse (HSCE-REQ-080, reused
verbatim by HRAC-REQ-019) reads `HardwareCredentialRecord.provider_profile`,
never `protocol_name`, was independently checked against
`_resolve_deployment_binding_signer`'s actual body in
`hatp_signing_ceremony.py`: `protocol_name` does not appear anywhere in
that function. **HRAC-REQ-066's claim is accurate**: this contract does
not depend on the finding being resolved to be internally coherent, but
the finding remains a hard prerequisite for real credential enrollment
(HRWP-001's own scope) before any real assertion (this contract's
scope) has a live credential to assert against. The finding is carried
forward explicitly, not concealed — this is the phase's sole Non-Blocking
finding, unchanged in substance from 2N.8/2N.9.

## 21. Client authority exclusions

Independently swept every field HRAC-REQ-017 lists as bound at request
creation: `principal_id`, `signer_key_id`, `HardwareCredentialRecord`,
`DeploymentBinding`, `provider_profile`, `repository_id`,
`canonical_deployment_root`, binding/decision digests, `expected_rp_id`,
`allowed_credential_ids` — every one is explicitly stated as
server-resolved, "none client-suppliable, none mutable after creation."
No client-controlled authoritative field found anywhere in the contract
text.

## 22. Session token / CSRF / mixup protections

Session token explicitly stated as a locator only, never authority
(HRAC-REQ-027, restates HRWP-REQ-045). Cross-session/cross-device
mixup is prevented by the same exact `request_id` + embedded-challenge
correlation (§9 above) — no second, bolted-on CSRF-token layer
introduced, matching HRWP-REQ-042's own "not a separate CSRF-token
layer" design (independently confirmed present in HRWP-001 §23).
Cross-repository and cross-operation mixup are prevented by
`repository_id` and `operation_reference` both being bound inside the
canonical challenge context (§6 above) and re-verified at verification
time (§11 above) — a proof for operation X cannot satisfy a request for
operation Y or repository A cannot satisfy repository B, since the
challenge digest itself would not match.

## 23. Governance ordering / UP / UV / signCount / failure taxonomy / privacy

- Governance ordering: HRAC-REQ-016/057 correctly require authorization
  to exist *before* request creation, never manufactured by the
  ceremony itself.
- UP/UV: correctly deferred to HRWP-001's own policy (`"preferred"` UV,
  UP always required) — HRAC-001 only records what was *observed*, never
  substitutes its own policy.
- signCount: correctly scoped as diagnostic-only, no invented
  clone-detection guarantee.
- Failure taxonomy: independently swept the governing prompt's §50/§72
  required attack-scenario list against HRAC-REQ-043's closed table.
  Every scenario maps to a defined `error_type` or an explicit
  state-machine/consumption-layer outcome (verified mechanically in the
  test suite) — no gap found. The vocabulary is explicitly closed,
  requiring a governed amendment to extend (confirmed present, not
  merely implied).
- Privacy: no IP/fingerprint/device-identity collection required or
  permitted absent a future amendment naming a specific justification.

## 24. Delivery-adapter independence / Mac-iPhone portability / RP-ID dependency

Delivery mechanism (Telegram/QR/URL) explicitly kept outside the
trusted-kernel boundary, never authority-bearing (§48). Mac and iPhone
are confirmed to use the identical server-side contract — no
platform-specific authority branch exists anywhere in the text.
RP-ID/origin/TLS literal values are correctly named as an unresolved,
explicit infrastructure dependency (not silently assumed) — HRAC-001
adds no new infrastructure dependency beyond what HRWP-001 already
named.

## 25. Contract cycle analysis

Independently traced the dependency direction: HRAC-001 depends on
HRWP-001 and HSCE-001 (and, transitively, HPSE-001/HBDC-001); neither
HRWP-001's nor HSCE-001's own frozen text names HRAC-001 as a
dependency of itself (confirmed by absence, not by an explicit
disclaimer alone — no `SHALL depend on HRAC` string exists in either
predecessor contract). **No cycle exists.** HRAC-001 cannot retroactively
grant itself authority its dependencies do not already grant.

## 26. HSCE-001 versioning impact

Independently confirmed HSCE-001 does not require a version bump: every
reused concept (§42/HRAC-REQ-063) is reused in its existing closed form
without modification; new concepts (§43/HRAC-REQ-064) are additive,
alongside HSCE-001's existing surface, never inside or in conflict with
it.

## 27. Fast Green

New test file: `tests/test_phase_149o_20l_7o_2n_10_hrac_001_independent_verification.py`,
32 tests, 32 passed, 0 failed, standalone
(`python -m pytest tests/test_phase_149o_20l_7o_2n_10_hrac_001_independent_verification.py -q`).

Full-repository `pytest -m fast_green -q` run (no production source or
existing contract text touched this phase — this phase's diff is purely
additive: one new test file and this doc): **341 failed, 8690 passed, 4
skipped, 9 errors, 27113 deselected** in the raw unfiltered run. All 341
failures/9 errors are in test files belonging to unrelated prior phases
(149O.20L.7O.2H.*, 149O.2, 149O.20E, 149O.20K.*, 149O.20M.*, HMIC/HBDC
digest-drift and readiness tests, `test_shell_gate.py`) — none reference
HRAC-001, HRWP-001, HSCE-001, or this phase's new test file by name or
by path. Since this phase made zero changes to any file these failing
tests exercise (the only files touched this phase are additive: this
doc, the new test file, and the routine
`PROJECT_STATUS.md`/`CHANGELOG.md`/`.pcae/*` bookkeeping files), these
341 failures are pre-existing and not attributable to this phase by
construction, not merely by inspection. **This phase's own attributable
regression count: 0 failed** (32 new tests, all passing; no existing
test file, contract text, or production source modified).

## 28. Implementation prerequisite DAG / recommended next phase

Independently re-derived from HRAC-REQ-074, cross-checked against §57-59
of the governing prompt: (1) this independent verification (now
complete); (2) the `protocol_name` vocabulary repair (§20 above) and (3)
RP-ID/origin/HTTPS infrastructure selection have **no ordering
dependency on each other** (HRAC-001's own text states this explicitly)
— both must complete before (4) server-side implementation, but neither
blocks the other. Given no forcing dependency between (2) and (3), and
per the governing prompt's own instruction not to mix unrelated
implementation and infrastructure work automatically, the two remain
independent tracks; either may be scheduled next. The narrower,
purely-textual, zero-infrastructure-dependency item is the `protocol_name`
repair — a small, self-contained HRWP-001 text correction (widening
`_PROTOCOL_VALUES` or correcting HRWP-REQ-019's prose) requiring no
external provisioning decision, versus RP-ID/TLS selection which
requires an actual infrastructure/domain decision outside this
repository's own governed scope.

**Recommended next phase:** a narrow HRWP-001 text repair resolving the
`protocol_name`/`_PROTOCOL_VALUES` closed-vocabulary contradiction
(widen `_PROTOCOL_VALUES` to include `"WEBAUTHN"`, or correct
HRWP-REQ-019's "no schema widening" claim) — independently verified this
phase to still be live in current production. RP-ID/origin/HTTPS
infrastructure selection remains a parallel, independent prerequisite
that may be scheduled before or after the vocabulary repair, per
HRAC-REQ-074's explicit no-ordering-dependency statement. No
implementation, HTTP route, request store, or provider code should begin
until both complete.

## No-Go compliance

No amendment made to HRAC-001, HRWP-001, or HSCE-001. No implementation
code, request store, HTTP route, credential, hardware effect, HMIC
change, redeployment, protected state, or HATP activation. No PB/runtime
change. Verification-only, as scoped.

## Runtime / governance state

Unchanged this phase: HMIC v1.7/38 ACTIVE/VALID; Trust-Enrollment
ABSENT; HATP NOT READY/NOT ACTIVE; Runtime observed/observe/unavailable.

## Governance checks (pre-finalization)

- `pcae health`
- `pcae check`
- `pcae status coherence`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae runtime inspect`
- `pcae notify status`

(exact output recorded in the finalization commit sequence)
