# Phase 149O.20L.7O.2D.3 — HATP Principal/Signer Enrollment Contract Repair Independent Verification

## 0. Phase Identity

- **Phase entry commit:** `8920f8b9fd2605c2804ec7bf95f7b63148145a5c` ("Phase 149O.20L.7O.2D.2: close task, transition to idle")
- **Repository:** clean at entry; `origin/main..HEAD` = 0 (verified, `git fetch` + `git rev-list --count`)
- **HPSE-001 exact version:** v1.1 (`docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md`, status line: `FROZEN — PENDING SECOND INDEPENDENT VERIFICATION`)
- **HBDC-001 exact version:** v1.2, unchanged during 7O.2D.2 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, `**Version:** 1.2`)
- **RepositoryIdentity:** `0107866f-af7c-40b4-8317-74e71acb05ca` — this UUID is a real-host (Dell) fact established at Phase 149O.20L.7O.2B/2B.1, referenced consistently across every phase document since, including 149O.20L.7O.2D.1/2. This local development clone has no `.pcae/repository-identity.json` (expected — it is not the Dell deployment target). No mutation to this value could have occurred during 7O.2D.2: no production code path capable of writing `repository-identity.json` was touched (confirmed by diff, §3 below), and no phase in this chain has host access to mutate it. Treated as unchanged by inference from the absence of any mutating code path, not by direct re-probe of the Dell host from this session.
- **DeploymentBinding:** absent (unbroken since 149O.20L.7O.2B; no writer capable of creating one exists in production source, confirmed §3).
- **Protected Root:** empty of principal/signer/hardware-credential state (same reasoning).
- **Runtime:** Observed/observe/unavailable — no runtime mutation performed.
- **Implementation-readiness gate:** NOT satisfied. This phase does not change that; it independently evaluates whether HPSE-001 v1.1's *text* now correctly states and structurally enforces that gate, which is a distinct question from whether the gate is currently satisfied (it is not, and is not claimed to be).

This phase does not trust 7O.2D.2's phase report, its companion tests, its closure assertions, its architecture prose, or its characterization of the two former Blocking findings. Every claim below was independently re-derived by reading primary source directly: the HPSE-001 v1.1 contract text itself, `hatp_hardware_credentials.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_providers.py`, `hatp_bootstrap.py`, `hatp_deployment_binding_admin.py`, `hatp_mandatory_certification.py`, and the actual `git diff` of the 7O.2D.2 commit range.

---

## 1. Entry Checks

| Check | Result |
|---|---|
| `git status` | clean |
| `origin/main..HEAD` | 0 commits |
| HPSE-001 exact version | v1.1, confirmed by reading the contract's own status line |
| HBDC-001 exact version | v1.2, confirmed unchanged; its own "Depends on" line still literally reads `HPSE-001 v1.0` (disclosed stale, NB-5, §11 below) |
| Production implementation for HHCE-001 | None exists — confirmed by `grep` across `src/` and `scripts/` for `def register_credential`, `def enroll_signer`, `def enroll_principal`; zero matches |
| Dell mutation | None — no host access from this session; no writer capable of mutating Dell state exists in production source (confirmed §3) |

---

## 2. Primary-Source Reconstruction of B-149O.20L.7O.2D.1-1 (independent, not from HPSE-REQ-056 backward)

Read directly: `src/pcae/core/hatp_hardware_credentials.py` (full file, 286 lines).

Findings, independently derived:

- `HATPHardwareCredentialStore` exposes exactly one public read method, `lookup_credential(signer_key_id) -> Optional[HardwareCredentialRecord]`. No `enroll`, `register`, `revoke`, `deactivate`, or any other mutating method exists anywhere in the class or module.
- The module's own docstring (lines 32–40) explicitly states enrollment is "OUT of Wave-5 scope" and defers it to "a future Human/Admin-only administrative surface" — this is the module's own primary-source acknowledgment that its own writer has never existed, independent of any contract text.
- `hatp_fido2_provider.py::Fido2HardwareProvider.verify()` (read directly, lines 341–360) calls `record_store.lookup_credential(signer_key_id)` and fails closed (`record is None or record.status != "active" or ...`) whenever no matching record exists.
- Consequence, independently derived (not copied from the contract's own §27 prose): a `SignerRecord` written to `registry.json` by any conformant future enrollment writer, with no corresponding write ever having occurred to `hardware-credentials.json` (because no writer for that file exists), will cause every verification of a proof produced under that signer to fail at `Fido2HardwareProvider.verify()`'s `lookup_credential` check. This independently confirms the "durable but functionally inert signer" defect class the finding names — reconstructed from the two files' actual code, not accepted from 7O.2D.1's or 7O.2D.2's own characterization.
- No writer for `hardware-credentials.json` was added anywhere in `src/` or `scripts/` as of this phase's entry commit (confirmed by `grep` above and by the `git diff` in §3).

**Independent verdict on B-1's underlying defect:** confirmed real, reconstructed from primary source, matches the finding's own description.

---

## 3. Primary-Source Reconstruction of B-149O.20L.7O.2D.1-2

Read directly:

```
src/pcae/core/hatp_fido2_provider.py:270-276
    def credential_identity(self) -> str:
        raise HATPProviderUnavailableError(
            "credential_identity() requires a live CTAP2 device with a discoverable/resident"
            " credential; no device is available in this environment. Credential identity for a"
            " non-resident credential is established at enrollment time (Wave 2/7 administrative"
            " surface, out of Wave-5 scope) and is not re-derivable from the device alone."
        )

src/pcae/core/hatp_piv_provider.py:93-94
    def credential_identity(self) -> str:
        raise HATPProviderUnavailableError(_UNAVAILABLE_REASON)
```

Both method bodies are a single unconditional `raise` statement — no `if`, no device probe, no branch on physical presence, confirmed mechanically (the accompanying test suite added by this phase, `TestCredentialIdentityUnconditionalRaise`, asserts `"if " not in body`). This is independent of physical device attachment: even with a compliant FIDO2/PIV device physically present, both implementations raise unconditionally today.

**Independent verdict on B-2's underlying defect:** confirmed real and precisely as HPSE-REQ-011 (v1.1) now states it — "unconditionally raise... independent of physical device presence, attachment, or provisioning state — a zero-implementation placeholder, not a re-derivability limitation."

### No implementation was added during 7O.2D.2

```
git diff --stat 76930e2f~1..8920f8b9
```
touched exactly: `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`, `CHANGELOG.md`, `PROJECT_STATUS.md`, the two new/repaired contract/architecture docs, three task files, and one new test file. **Zero files under `src/pcae/` or `scripts/` were touched.** This independently confirms 7O.2D.2's own claim that it is architecture-only, and confirms this phase itself has not (and need not) modify any production module either.

---

## 4. HHCE-001 Disposition Verdict

Applying the phase prompt's own taxonomy (§5): **(A) — sufficiently defined as a prerequisite interface whose own contract may safely be authored next.**

Rationale, independently assessed against HPSE-REQ-053/054's actual text (not the contract's own self-assessment at §27):

- HPSE-REQ-054 bounds HHCE-001's *minimum required scope* concretely: a preview variant per mutating operation; exactly `register_credential`/`revoke_credential`/`deactivate_credential`; schema validation against the *already-existing, already-frozen* `HardwareCredentialRecord` schema (`hatp_hardware_credentials.py`, independently read in §2 — the schema is real and already fixed, not proposed); provider-profile validation against the identical closed allowlist HPSE-REQ-020 already validates against; the identical `_write_atomic` idiom (independently confirmed to exist at `repository_identity.py:153`); its own lock with an explicit ordering rule relative to the existing transition lock (HPSE-REQ-057, independently checked for deadlock-freedom, §6 below); read-back verification; audit emission; fail-closed symmetry with HPSE-REQ-035/036/037.
- This is materially more constrained than a bare "HHCE-001 will exist" placeholder. A future contract-authoring phase for HHCE-001 has almost every load-bearing architectural decision already fixed for it: data model, atomicity idiom, lock scope and ordering, audit discipline, and the precondition its writer's output must satisfy (HPSE-REQ-056, defined in *this* contract, not deferred to HHCE-001).
- The trust-boundary-separation rationale (§27: `hardware-credentials.json` is provider-owned cryptographic material with a different threat model than `registry.json`'s identity/authorization binding) is independently verified as consistent with the two files' actual, already-existing separate schemas, separate fixed protected roots, and separate module (`hatp_hardware_credentials.py` vs. `hatp_bootstrap.py`) — this is not new text invented to justify the split; it restates a separation the primary source already has.

**This verdict is not merely accepting 7O.2D.2's own rationale.** The independent check applied here is: does HPSE-REQ-054's bound leave two competent implementers of HHCE-001 free to disagree about anything *this contract itself* depends on? No — because the one thing HPSE-001 itself structurally depends on (the cross-registry precondition, HPSE-REQ-056) is defined here, in HPSE-001, not deferred into HHCE-001's undefined future text. HHCE-001 is free to vary in its own internal API shape, but HPSE-001's own correctness does not depend on any of those free variables. This is the decisive fact that makes disposition (A) correct rather than (B) ("merely named without enough semantic constraints") — the constraints that matter for HPSE-001's own well-formedness are already fixed in HPSE-001, not left to HHCE-001.

Disposition (C) from the contract's own self-report ("a named prerequisite companion contract, not authored by this phase") is the scope-boundary rationale for *why a separate contract at all*, not a verdict on *how well-defined* the prerequisite is. The two questions are independent; this phase's answer to the phase-prompt's actual §5 question ("sufficiently defined" vs. "merely named") is disposition (A).

---

## 5. HPSE-REQ-056 / HPI-7 Structural Closure — Attack Matrix

Independently read §29 (HPSE-REQ-056) and HPI-7 (§49). Attacking each named path from the governing prompt:

| Path | Outcome per contract text | Verdict |
|---|---|---|
| Fresh enrollment | `enroll_signer` checks live `lookup_credential` under lock before writing | Closed |
| Retry after credential-only durable state | HPSE-REQ-058(B): retry re-checks precondition (still satisfied), proceeds | Closed, idempotent |
| Existing partial state | Covered by the six-case matrix, §6 below | Closed |
| Malformed state | HPSE-REQ-036: malformed `registry.json` fails closed on every read | Closed |
| Duplicate signer | HPSE-REQ-022/037: existing duplicate-key rejection, fails closed with a typed error | Closed |
| Credential revoked after registration but before signer write | This is the one path requiring inference, not a direct statement — see finding NBF-1 below | Closed by inference, not fully explicit |
| Signer activation before credential activation | HPSE-REQ-056 itself makes this structurally impossible for the contract's own writer | Closed |
| Credential removed/corrupted after signer activation | Explicitly out of `enroll_signer`'s own scope (HPSE-REQ-058(C)): "a reconciliation-scan finding for a future audit tool, not a runtime case `enroll_signer` itself must handle" | Explicitly disclosed as a residual gap, not silently ignored |

**NBF-1 (Non-Blocking Finding, this phase, new): the credential lock's hold-duration through `enroll_signer`'s full check-then-write critical section is established by inference from HPSE-REQ-058(C)'s "structurally unreachable" claim, not by an explicit sentence in HPSE-REQ-057 itself stating the lock is held continuously from precondition-check through signer-write completion.**

Detail: HPSE-REQ-057 states the two locks "MUST be acquired in a single, fixed, global order... whenever one writer... needs both," and HPSE-REQ-058(C) separately claims that credential-missing-but-signer-written "SHALL NOT occur under a conformant implementation... the precondition is checked immediately before the signer write, under the lock ordering of HPSE-REQ-057, making this sequence structurally unreachable through this contract's own writer." For HPSE-REQ-058(C)'s "structurally unreachable" claim to be literally true, `enroll_signer` must hold the hardware-credential-store lock continuously from the precondition check through the completed, read-back-verified signer write — if the outer lock were released immediately after the check (before the signer write), a concurrent `revoke_credential` could race in between, and the claimed-impossible sequence (C) would become reachable through the contract's own writer, not merely through out-of-band tampering. HPSE-REQ-057's own text does not say "held for the duration," only "acquired in a fixed order" — the continuous-hold requirement is the only reading under which HPSE-REQ-058(C)'s explicit `SHALL NOT` claim is true, so a careful implementer reading §29-§31 together (not HPSE-REQ-057 in isolation) is led to the correct behavior — but this is inference across three requirements, not one self-contained normative sentence. This is a documentation-precision gap, not a structural gap: the correct behavior is entailed by the contract's existing text taken as a whole, and no implementer following HPSE-REQ-058(C)'s literal `SHALL NOT` could satisfy it without the continuous hold. **Classification: Non-Blocking** — a future minor amendment to HPSE-REQ-057 adding one clause ("held continuously through the completed write, never released between the precondition check and the write") would close this precisely, but its absence today does not leave a live security gap, only an inference step.

**Independent verdict: HPSE-REQ-056/HPI-7 achieve structural closure of B-1** — not "the contract mentions it now," but the precondition is a live, checked-under-lock gate a conformant writer literally cannot bypass, with the one identified gap (NBF-1) being a documentation-precision issue resolved by cross-reading, not a live bypass path.

---

## 6. Six-Case Partial-Failure Matrix — Independent Attack

Read §31 (HPSE-REQ-058) directly and independently re-derived against my own decomposition (not accepted from the contract's own case labels):

| # | Case | Independent classification |
|---|---|---|
| 1 | Hardware credential write fails before durable state | Retryable, no side effect — `registry.json` untouched because `enroll_signer` never starts its own transition-lock acquisition until the precondition already observes a durable credential |
| 2 | Credential durable, signer write never begins | Harmless, inert, durable-but-incomplete — unreferenced credential grants no authority (independently confirmed: `SignerRecord` alone, not `HardwareCredentialRecord` alone, is what `_resolve_signer`/`verify_hatp_proof` consult for authorization, per HPSE-REQ-062, independently cross-checked against HPSE-REQ-050's description of `_resolve_signer`) |
| 3 | Signer write fails before durable state | Retryable — no signer record was ever durably written; re-attempt re-checks the (unaffected) credential precondition |
| 4 | Credential + signer durable, audit incomplete | Durable-but-unaudited, recoverable by reconciliation against the audit log — explicitly never "audited-but-not-durable" per the fixed ordering (validate → mutate → read-back → audit) |
| 5 | Read-back mismatch in either registry | Blocking for that specific write attempt only — aborts before any dependent write proceeds, per each write's own independent read-back-verify step |
| 6 | Concurrent/replayed enrollment attempt | Prevented structurally by the fixed lock-acquisition order (§5/NBF-1 above) — no interleaving can violate HPSE-REQ-056 |

No case is left with ambiguous exception semantics: HPSE-REQ-071 names four new, distinctly rooted error conditions (`HARDWARE_PROVIDER_UNIMPLEMENTED`, `HARDWARE_CREDENTIAL_NOT_REGISTERED`, `HARDWARE_CREDENTIAL_CONFLICT`, `CREDENTIAL_IDENTITY_UNAVAILABLE`) that map cleanly onto cases 1/2 (not-registered), 6 (conflict), and the provider-unavailable-vs-not-implemented split independently verified in §7 below. Independently re-checked: none of these four overlaps semantically with HPSE-REQ-034's original nine, and none of the six cases above maps to more than one named error condition.

**Independent verdict: the six-case matrix is complete and each case receives an exact, non-overlapping classification**, matching the contract's own claim.

---

## 7. Lock Ordering / Deadlock-Freedom — Independent Proof

Read HPSE-REQ-057 directly. Independent deadlock analysis (not accepted from the contract's own assertion):

- Two locks exist: the hardware-credential-store lock (new, HHCE-001-scoped) and `.deployment-binding-transition.lock` (existing — independently confirmed at `hatp_deployment_binding_admin.py:160,494-503`, a fixed-path `fcntl.flock`-based lock).
- The contract fixes exactly one global acquisition order for any operation needing both: credential lock outer, transition lock inner. Only `enroll_signer` (via HPSE-REQ-056's precondition check) is named as needing both. HHCE-001's own `register_credential`/`revoke_credential` need only the credential lock (never touching `registry.json`). Other Principal/Signer writer operations (`revoke_signer`, `enroll_principal`, `revoke_principal`) are not stated to need the credential lock at all, and nothing in HPSE-REQ-056 requires them to.
- Standard lock-ordering theorem: deadlock requires a cycle in the wait-for graph, which requires at least two distinct processes each holding one lock and waiting for the other in reversed order. Since the contract fixes a single, non-reversible acquisition order for the only operation that ever needs both locks, and no other operation acquires the transition lock first and then waits on the credential lock, no such cycle can form. **Independently confirmed: deadlock-free**, given conformant implementations obey the stated order (which is the only order the contract permits at all — "never the reverse, by any writer, in any operation").
- This proof depends on the continuous-hold assumption from §5/NBF-1 for correctness of the *precondition invariant*, but not for deadlock-freedom itself — deadlock-freedom holds regardless of hold-duration, since it depends only on acquisition order, not release timing.

---

## 8. Split-Brain Analysis

Attacking the named scenario (Process A loads hardware-credential registry, Process B loads Principal/Signer registry, A writes, B writes stale assumptions):

- If Process B is `enroll_signer`, it acquires the credential lock (outer) before reading the credential registry for its precondition check (per §5's continuous-hold reading), so any concurrent Process A performing `register_credential`/`revoke_credential` (which needs only the credential lock) is serialized against B — B cannot observe a stale credential-registry snapshot while proceeding to write a `SignerRecord`, because A and B cannot hold the credential lock simultaneously.
- If Process A is some future revocation-cascade or reconciliation tool (not currently named as production code — none exists per §3), it would need to acquire at least the credential lock to safely revoke a credential referenced by an active signer; the contract does not yet name such a tool, so this is not a live gap, only an unbuilt future surface (consistent with HPSE-REQ-058(C)'s own disclosure that out-of-band tampering is a reconciliation-scan concern, not a live writer-reachable path).
- **Independent verdict: no writer-reachable split-brain exists**, contingent on the continuous-hold reading of HPSE-REQ-057 (§5/NBF-1) being the correct one — which this report already establishes as the only reading consistent with HPSE-REQ-058(C)'s literal claim.

---

## 9. Cross-File Transaction Realism

Independently confirmed §31 (the six-case matrix, §6 above) defines exactly the staged fail-closed protocol the phase prompt's §15 requires, without inventing an impossible filesystem-wide atomic transaction: credential-only durable state is harmless (case 2), active signer cannot precede valid credential (HPSE-REQ-056 precondition + lock), retry uses persisted state (cases 1/3), and each write's own independent read-back establishes local consistency (case 5). No blocking finding.

---

## 10. `credential_identity()` Current-vs-Target Semantics

Independently read HPSE-REQ-059/060 (§32) against the actual current implementations (§3 above). HPSE-REQ-059 deliberately freezes only the semantic *output* (a stable, durable, protocol-appropriate credential-identity byte string) without naming an implementation function or call signature — independently confirmed this is a real, substantive design choice, not vagueness: it correctly avoids over-constraining a future implementation phase's function-naming decision while still fixing the property that matters (the output's stability and durability). HPSE-REQ-060 independently and correctly separates two facts that are logically independent and both currently false: (a) a compliant physical device is attached (HPSE-REQ-045's provisioning step — a fact about the *host*), and (b) the selected provider implementation actually implements HPSE-REQ-059's semantics (a fact about the *code*, independently confirmed false for both protocols in §3). No sentence anywhere in HPSE-REQ-059/060/064/065/066 implies physical attachment alone would satisfy the gate — independently verified by reading each of those five requirements in full; each explicitly names implementation-readiness as a separate, additional condition.

---

## 11. FIDO2 / PIV Parity

Independently read HPSE-REQ-064. Both protocols' `credential_identity()` are confirmed unconditional-raise (§3). The contract's closing clause distinguishes FIDO2's `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS` from PIV's `NOT_CONFORMANT` — independently cross-checked against `hatp_fido2_provider.py` (capabilities: `credential_identity=True`, `hatp_conformant=CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`, but the *method* still unconditionally raises regardless of the capability flag's value — the flag describes design intent, not current working status) and `hatp_piv_provider.py` (`credential_identity=False`, `hatp_conformant=NOT_CONFORMANT`). This is an important, independently-confirmed subtlety: FIDO2's `capabilities().credential_identity=True` does **not** mean the method works — it means the design intends to support it once implemented, which the contract correctly does not conflate with implementation-readiness (HPSE-REQ-060 gates on the latter, independent of the former). No blocking finding; the design-conformance/implementation-readiness distinction is real and correctly maintained in both directions.

---

## 12. `signer_key_id` Durability and Source of Truth

Independently read HPSE-REQ-061/062. `signer_key_id == hex(credential_identity_bytes)` is stated as an equivalence, not a derivation — independently checked against `hatp_hardware_credentials.py`'s existing `public_key_hex` encoding convention (§2, confirmed the same hex-of-raw-bytes idiom is already established elsewhere in the same file family, not invented here). The durable source of truth is explicitly the *pair* (`SignerRecord` + `HardwareCredentialRecord`), independently cross-checked: `SignerRecord`'s existing schema (read directly at `hatp_bootstrap.py:109-114`) carries no public-key field, and `HardwareCredentialRecord`'s schema (read directly at `hatp_hardware_credentials.py:88-98`) carries no `principal_id` field — confirming neither artifact alone suffices, exactly as HPSE-REQ-062 claims. No competing authority is left open: HPSE-REQ-056 guarantees both exist together for any `active` signer produced through this contract's own writer. **No Blocking finding.**

---

## 13. Credential Registry Integrity (Invariants HPSE-001 Freezes for HHCE-001)

Independently read HPSE-REQ-054 against `hatp_hardware_credentials.py`'s actual, already-frozen schema (§2): `signer_key_id`, `provider_profile`, `protocol_name`, `algorithm`, `public_key`/`public_key_hex`, `status` — confirmed to already exist exactly as HPSE-REQ-054 describes, with no widening proposed. No private-key material field exists in the schema (independently confirmed, `hatp_hardware_credentials.py:88-98`), matching HPSE-REQ-014's cross-reference. Fail-closed malformed behavior is independently confirmed already implemented (`_parse_credential`, lines 143-180: rejects missing fields, non-string types, invalid protocol/status enum values, invalid hex). Timestamp semantics are not part of `HardwareCredentialRecord`'s current schema at all (no `created_at`/`revoked_at` field exists today) — HPSE-REQ-054 does not name this as a required addition either, which is a minor omission relative to HPSE-REQ-052's own timestamp-grammar requirement (which only names `SignerRecord.revoked_at`/`PrincipalRecord.revoked_at`, not any `HardwareCredentialRecord` timestamp). **Non-Blocking finding, NBF-2 (new, this phase):** HHCE-001's eventual schema will need its own revocation-timestamp field and grammar rule (mirroring HPSE-REQ-052) if `revoke_credential`/`deactivate_credential` are to have auditable revocation timestamps at the record level rather than only in the audit log — HPSE-REQ-054 does not explicitly name this, though it is a natural, low-risk consequence of HHCE-001 authoring its own contract next. This does not block HPSE-001 v1.1's own closure since it is HHCE-001's future scope, not HPSE-001's.

---

## 14. Readiness State Machine

Independently read HPSE-REQ-066 (§38). Mechanically re-derived the five stages and their gating logic: `PROVIDER_UNIMPLEMENTED → PROVIDER_AVAILABLE → CREDENTIAL_PRESENT → CREDENTIAL_REGISTERED → SIGNER_ENROLLED`. Cross-checked against current real state (§3): both protocols are at `PROVIDER_UNIMPLEMENTED` today (neither implements HPSE-REQ-059's semantics). No shortcut path exists in the stated vocabulary from `CREDENTIAL_PRESENT` directly to `SIGNER_ENROLLED` — each transition requires the prior stage's own explicit satisfaction, and the contract text explicitly disclaims that "presence at an earlier stage never implies readiness at a later one." **No Blocking finding.**

Minor observation (informational, not a finding): the five-stage machine in §38 is a strict subset/simplification of the phase prompt's own six-stage sketch (§23, which additionally separately named `PRINCIPAL_ENROLLED` before `SIGNER_ENROLLED` and a terminal `ENROLLMENT_READY`). HPSE-001's own §37 (HPSE-REQ-065) separately enumerates principal enrollment as part of the four prerequisite states to a "real, usable signer," so the omission from §38's specific five-stage vocabulary is a scope choice (§38 names the *hardware-credential-side* readiness progression specifically, principal enrollment being a pre-existing, unchanged v1.0 concept already covered by HPSE-REQ-027), not an oversight. Not classified as a finding.

---

## 15. Composite Implementation-Readiness Gate (HPSE-REQ-072)

Independently read HPSE-REQ-072 against B-1 and B-2's own text. Five conditions: (a) provider implementation supports HPSE-REQ-059 semantics [closes B-2]; (b) HHCE-001 exists+verified+writer implemented+verified [closes B-1]; (c) matching active hardware credential actually registered for the specific attempt; (d) target principal active; (e) provider-profile allowlist match. Independently verified these are jointly necessary and none is redundant with another: (a) is a code-implementation fact, (b) is a companion-contract-and-implementation fact, (c) is a per-attempt runtime fact, (d)/(e) are pre-existing v1.0 preconditions unchanged by this amendment. No condition subsumes another. **Independent verdict: sufficient and jointly necessary, correctly closes both Blocking findings as a composite mechanism, not prose disclosure alone** — matches the contract's own claim, independently re-derived rather than accepted.

---

## 16. Error Vocabulary (HPSE-REQ-034/071)

Independently read both. The four new conditions (`HARDWARE_PROVIDER_UNIMPLEMENTED`, `HARDWARE_CREDENTIAL_NOT_REGISTERED`, `HARDWARE_CREDENTIAL_CONFLICT`, `CREDENTIAL_IDENTITY_UNAVAILABLE`) are checked against the original nine (HPSE-REQ-034) for overlap: none duplicates an existing member's meaning. `CREDENTIAL_IDENTITY_UNAVAILABLE` vs. `HARDWARE_PROVIDER_UNIMPLEMENTED` distinction independently verified as coherent: the former is the enrollment-time-facing name for the pre-existing `HATPProviderUnavailableError` (an error class that already exists in `hatp_providers.py`, independently confirmed at line 196) when raised specifically during the credential-identity ceremony, the latter is the "no implementation exists at all" case — these are not the same thing today (both providers currently raise `HATPProviderUnavailableError` unconditionally, which independently confirms the *current* observable symptom is `CREDENTIAL_IDENTITY_UNAVAILABLE`-shaped even though the root cause is `HARDWARE_PROVIDER_UNIMPLEMENTED`-shaped — this is exactly HPSE-REQ-045's own "shared fail-closed symptom does not imply a shared root cause" observation, independently re-confirmed against the actual code). No bare `ValueError`-typed normative outcome exists in the new set. **No Blocking finding.**

---

## 17. Retry / Idempotency Semantics

Independently attacked each named scenario against §31's matrix (§6 above): duplicate credential registration → `HARDWARE_CREDENTIAL_CONFLICT` (named, HPSE-REQ-071); repeated principal/signer enrollment → existing HPSE-REQ-037 duplicate-key fail-closed; retry after credential-only durable state → case (B), safe and idempotent; retry after signer-durable-but-audit-incomplete → case (D), recoverable by log comparison, not itself a retry-unsafe state since the registry write already succeeded; conflicting different credential for the same signer ID → structurally prevented, since `signer_key_id` is derived from `credential_identity()`'s own output (HPSE-REQ-061), not caller-suppliable, so no "different credential, same ID" case can arise through the contract's own writer (a caller cannot supply a mismatched pair). **No ambiguous outcome found.**

---

## 18. Audit Ordering

Independently read HPSE-REQ-070 against HPSE-REQ-038/039's existing one-registry discipline. Confirmed: hardware-credential-registration and signer-enrollment audit events are required to be separately attributable, and the ordering discipline (validate → mutate → read-back → audit) is extended, not altered, for the two-registry case. This is the same disclosed, known limitation as the one-registry case (audit-emission failure after a successful write propagates uncaught) — independently checked, this is a consistent, not new, disclosed limitation, not silently introduced by this amendment.

---

## 19. Producer/Verifier Trust Model

Independently read HPSE-REQ-067/068 against `human_approval_trusted_provenance.py::verify_hatp_proof`'s actual behavior (not re-read line-by-line in this phase, since 7O.2D.1 already independently confirmed this at its own §9 and this phase's primary interest is whether HPSE-001 v1.1's *text* accurately documents it — the text's own claims are internally consistent with what §2/§3's independently-read code confirms about `_resolve_signer`/`verify()`'s check patterns). HPSE-REQ-068 correctly keeps `HBDC-REQ-042` scoped to deployment-identity conformance only, and does not move semantic validation into HBDC-001. **No Blocking finding; matches §28 instruction not to mistakenly move semantic validation into HBDC-001.**

---

## 20. Revocation Disposition

Independently read HPSE-REQ-069. The claim — that `verify_hatp_proof`'s live re-check of `principal.status`/`signer.status`/`authority.status` (independently confirmed exists as a documented architectural fact by HPSE-REQ-067, itself cross-checked against `_resolve_signer`'s described check pattern in §2) makes physical `DeploymentBinding` rewrite unnecessary on revocation — is a documentation-only clarification, not a new behavior. This phase does not independently re-execute `verify_hatp_proof` against a live revoked-principal proof (that would require actual enrollment, forbidden by this phase's scope), so this verdict rests on the code-reading chain already established, not a live test. **Classified as intentional live-validation semantics, appropriately scoped — not expanded beyond what security requires**, per the phase prompt's own §29 instruction.

---

## 21. `PrincipalRecord.revoked_at` (HPSE-REQ-008)

Independently confirmed via direct read of `hatp_bootstrap.py:103-105,291-295`: `PrincipalRecord` has exactly `{principal_id, status}`, `_parse_principal`'s allowed-field set is exactly `{"principal_id", "status"}` — no `revoked_at` field exists. This exactly matches HPSE-REQ-008's disclosure. No production change made by this phase or 7O.2D.2 (confirmed §3).

---

## 22. `authority_scope` Compatibility

Independently read HBDC-001's §16.2 text is unaffected by this amendment (HPSE-001 does not govern `authority_scope`, per §2 unchanged). No contradiction found between HPSE-001 v1.1 and HBDC-001 v1.2's existing `authority_scope` vocabulary. **No reopening of HBDC-001 required.**

---

## 23. Runtime Neutrality

Independently `grep`'d for `Claude`, `Codex`, `DeepSeek` across the full contract text: both matches are confined to HPSE-REQ-051 and HPSE-REQ-074 themselves — the two requirements whose entire purpose is disclaiming runtime coupling. No accidental coupling found anywhere else in the document. Mechanically re-verified by the companion test `TestRuntimeNeutrality`.

---

## 24. Requirement Mechanics — Mechanical Verification

Independently extracted every `**HPSE-REQ-###` definition marker (not cross-reference mentions) from the contract text: exactly 74 unique values, `001`-`074`, strictly sequential, zero gaps, zero duplicates (verified by `sort -n | uniq -d` returning empty). Exactly three requirements carry a `(revised, v1.1...)` marker: `011`, `045`, `046` — matches the contract's own §48 claim, independently re-derived rather than trusted.

---

## 25. v1.0 → v1.1 Diff Reconstruction

Independently classified: 22 new requirements (`053`-`074`), 3 revised in place (`011`, `045`, `046`, confirmed by explicit `(revised...)` markers, §24), the remaining 49 (`001`-`010`, `012`-`044`, `047`-`052`) unchanged. No unexplained semantic modification found outside the three disclosed revisions — spot-checked several unrevised requirements (`HPSE-REQ-007`, `HPSE-REQ-033`, `HPSE-REQ-050`) against their described v1.0 content in 7O.2D.1's independent-verification report and found no undisclosed drift.

---

## 26. Blocking-Finding Closure Mapping — Independent Verification

**B-149O.20L.7O.2D.1-1** — independently confirmed closed by: HPSE-REQ-053 (names HHCE-001, gates readiness), HPSE-REQ-054 (bounds scope, §4/§13 above), HPSE-REQ-056 (the actual structural mechanism, §5 above — the load-bearing piece), HPSE-REQ-057/058 (lock ordering + failure matrix, §6/§7 above), HPSE-REQ-072(b)/(c) (composite gate, §15 above). This is not "the contract mentions it now" — HPSE-REQ-056 is a checked-under-lock precondition a conformant writer cannot bypass, independently confirmed by reading the requirement's own mechanism, not its label.

**B-149O.20L.7O.2D.1-2** — independently confirmed closed by: HPSE-REQ-011 (revised — matches actual code state exactly, §3 above), HPSE-REQ-059/060 (corrected target semantics + independent implementation prerequisite, §10 above), HPSE-REQ-045/046 (provisioning-vs-implementation distinction), HPSE-REQ-064 (protocol parity, §11 above), HPSE-REQ-072(a) (composite gate inclusion).

Both closures share their structural core in HPSE-REQ-072's composite gate (§15), independently confirmed sufficient and jointly necessary.

---

## 27. Implementability Test (Two Independent Implementers)

Applying the test to each named question:

| Question | Would two implementers disagree? |
|---|---|
| Activation ordering | No — HPSE-REQ-046's 12-step sequence + HPSE-REQ-056's precondition are explicit and total-ordered |
| Orphan credential allowed? | No — HPSE-REQ-058(B) explicitly states yes, harmless |
| Orphan signer ever active? | No — HPSE-REQ-056 explicitly forbids it for the contract's own writer |
| Lock order | No — HPSE-REQ-057 states one fixed order explicitly |
| `signer_key_id` source | No — HPSE-REQ-061 states the equivalence explicitly |
| Provider-unavailable handling | No — HPSE-REQ-071's four-way split is explicit |
| Partial-failure recovery | No — §31's six cases each have an explicit disposition |
| **Lock hold-duration through the check-then-write critical section** | **Yes, potentially** — this is NBF-1 (§5): resolvable only by cross-reading HPSE-REQ-057 against HPSE-REQ-058(C), not from HPSE-REQ-057 alone |

**Verdict: one genuine implementability gap survives (NBF-1), classified Non-Blocking** because the correct behavior is still derivable (not merely guessable) from the contract's text taken as a whole, and no implementer following HPSE-REQ-058(C)'s explicit `SHALL NOT` literally could arrive at the wrong (unsafe) behavior without contradicting an explicit normative sentence elsewhere in the same document. This does not, by itself, require contract amendment before HHCE-001's own contract-authoring phase begins, but SHOULD be closed by a one-clause addition to HPSE-REQ-057 in a future minor touch-up, for precision rather than safety.

---

## 28. No-Implementation / No-Dell-Mutation Proof

- No production source corresponding to HHCE-001, provider identity implementation, HPSE enrollment writer, or `DeploymentBinding` semantic amendments was added during 7O.2D.2 (§3, `git diff --stat` confirms doc/task/metadata files only).
- This phase adds none either: only this report, its companion test file, and the standard task/metadata/status bookkeeping files.
- No Dell host was reached, provisioned, or mutated from this session. `RepositoryIdentity`, `DeploymentBinding` absence, and Protected Root emptiness are unchanged by inference (no mutating code path exists, §3), not by direct re-probe.

---

## 29. Findings Summary

**Blocking findings: none.**

**Non-Blocking findings (this phase, new):**

- **NBF-1** — HPSE-REQ-057's lock continuous-hold-through-critical-section requirement is established only by cross-reading against HPSE-REQ-058(C), not stated as a single explicit sentence (§5, §27). Recommend a one-clause future amendment for precision.
- **NBF-2** — HPSE-REQ-054 does not explicitly name a revocation-timestamp field/grammar requirement for `HardwareCredentialRecord`, though `revoke_credential`/`deactivate_credential` will plausibly need one when HHCE-001 is authored (§13). Deferred, HHCE-001's own future scope, not HPSE-001's.

Neither finding blocks HPSE-001 v1.1's own closure of B-1/B-2, and neither represents a live, exploitable gap given current (zero-implementation) production state.

---

## 30. Final Verdict

```
HATP PRINCIPAL/SIGNER ENROLLMENT CONTRACT REPAIR — INDEPENDENT VERIFICATION:

VERIFIED WITH NON-BLOCKING FINDINGS — HPSE-001 v1.1 CONTRACT REPAIR COMPLETE

— Both former Blocking findings (B-149O.20L.7O.2D.1-1, B-149O.20L.7O.2D.1-2)
  independently re-derived from primary source and confirmed structurally,
  not merely prosaically, closed.
— HHCE-001 disposition: (A) sufficiently defined as a named prerequisite
  interface; its own contract may safely be authored next.
— Cross-registry consistency invariant (HPSE-REQ-056/HPI-7): structurally
  closes B-1, contingent on the continuous lock-hold reading (NBF-1).
— Lock ordering (HPSE-REQ-057): independently proven deadlock-free.
— Six-case partial-failure matrix: complete, each case receives an exact,
  non-overlapping classification.
— Composite implementation-readiness gate (HPSE-REQ-072): sufficient and
  jointly necessary.
— Two Non-Blocking findings recorded (NBF-1, NBF-2); neither is live-exploitable
  given current zero-implementation production state.
— REAL ENROLLMENT NOT AUTHORIZED
— REAL PROVISIONING NOT AUTHORIZED
— NO ENROLLMENT WRITER IMPLEMENTED (this phase or 7O.2D.2)
— NO HHCE-001 WRITER IMPLEMENTED (HHCE-001 ITSELF NOT YET AUTHORED)
— NO HARDWARE-PROVIDER-LAYER IMPLEMENTATION CHANGE MADE
— NO DELL MUTATION
```

No implementation was performed. No enrollment writer, HHCE-001 writer, or hardware-provider implementation change was made by this phase.

---

## 31. Next-Phase Recommendation (Speed-Oriented, per Governing Prompt §41-§42)

Under the PUBLIC + FAST + TECHNICALLY RIGOROUS + VISIBLY DIFFERENTIATED strategic principle, and given this phase's finding that HHCE-001's minimum scope is already sufficiently bounded by HPSE-REQ-054 (§4/§27) that no further contract-repair cycle is required before implementation planning:

**Recommended: 149O.20L.7O.2E — HATP Trust-Enrollment Implementation Capability (bundled).** A single bounded implementation chapter covering the tightly coupled surfaces the governing prompt's §41 already names: HHCE-001's own contract authoring (minimum-scope, per HPSE-REQ-054's bound) together with its writer implementation; the hardware-provider `credential_identity()` implementation for at least one protocol satisfying HPSE-REQ-059/060; the Principal/Signer enrollment writer (`enroll_principal`/`enroll_signer`/`revoke_principal`/`revoke_signer` + preview variants) satisfying HPSE-001 v1.1 in full, including the HPSE-REQ-056 cross-registry precondition and HPSE-REQ-057 lock ordering; the `hatp_bootstrap.py` `PrincipalRecord.revoked_at` schema widening (HPSE-REQ-008); and the `DeploymentBinding` producer cross-validation amendment (HPSE-REQ-047/048). This bundle should be followed by exactly one strong independent implementation verification phase (mirroring this phase's own discipline), not fragmented into many micro-phases, per the governing prompt's explicit instruction not to "automatically explode the remaining trust work into many tiny phases."

Before implementation coding begins on this bundle, HHCE-001 itself must still be authored and frozen as its own contract document (HPSE-REQ-053(a)) — the governing prompt's own caveat that "if HHCE-001 still requires its own normative contract before coding, author/freeze that contract first" applies: this phase's own §4 verdict is that HHCE-001 is *well-scoped*, not that it already *exists*. The recommended bundle's first sub-step is therefore HHCE-001 contract authoring (short, since HPSE-REQ-054 already bounds nearly all of its substance), immediately followed by the implementation work, not a second multi-phase contract-negotiation cycle.

---

## 32. Governance, Tests, Commits

- **Tests added:** `tests/test_phase_149o_20l_7o_2d_3_hatp_principal_signer_enrollment_contract_repair_independent_verification.py` — 19 tests, all independently re-verifying this phase's own claims against live source, not against 7O.2D.2's or this phase's own prose.
- **Test results:** see `.pcae/phase-completion-metadata.json` for the fast_green and full-suite counts recorded at commit time.
- **Commits:** see `.pcae/phase-completion-metadata.json` for the phase-entry and phase-completion commit hashes.
- **Pushed status:** see `.pcae/phase-completion-report.md` for the final push state.
- **`origin/main..HEAD`:** 0 at phase entry; recorded post-completion in the phase-completion metadata.

No production `.py` file was modified by this phase. No hardware was provisioned. No principal or signer was enrolled. No `DeploymentBinding` was created. No election was initiated. No CHGR was published. No certification was performed. No Dell host was mutated.
