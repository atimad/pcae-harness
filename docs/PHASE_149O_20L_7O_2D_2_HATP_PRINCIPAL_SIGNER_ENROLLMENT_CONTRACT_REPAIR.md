# Phase 149O.20L.7O.2D.2 — HATP Principal/Signer Enrollment Contract Repair

## Phase identity

**Phase-ID:** 149O.20L.7O.2D.2
**Title:** HATP Principal/Signer Enrollment Contract Repair
**Mode:** documentation (contract architecture repair; no implementation)
**Phase-entry commit:** `d12462c4` (tip of Phase 149O.20L.7O.2D.1 at task-open time)
**HPSE-001 entering version:** v1.0, NOT VERIFIED (2 Blocking, 5 Non-Blocking findings, per Phase 149O.20L.7O.2D.1's independent verification)
**HBDC-001 entering version:** v1.2 (untouched this phase — see §25)
**RepositoryIdentity:** `0107866f-af7c-40b4-8317-74e71acb05ca` (unchanged; not re-read live on `hac-dell` this phase — this is a documentation-only contract repair with no dependency on live Dell state)
**DeploymentBinding:** ABSENT (unchanged)
**Protected Root:** EMPTY (unchanged)

This phase repairs HPSE-001 v1.0 in response to the two Blocking findings Phase 149O.20L.7O.2D.1 independently demonstrated. It is contract architecture only: it names, bounds, and sequences required future work; it implements none of it. No production `.py` file under `src/pcae/` or `scripts/` was modified. No hardware provider code was implemented. No `hardware-credentials.json` writer was implemented. No Principal/Signer enrollment writer was implemented. No credential was provisioned. No principal or signer was enrolled. No `DeploymentBinding` was created. No election was initiated. No CHGR was published. No certification occurred. No Dell host was mutated.

---

## 1. Reconstruction of both Blocking findings at phase entry (§3 of the governing prompt)

Before editing HPSE-001, this phase independently re-read primary source, fresh this session, then cross-checked it against Phase 149O.20L.7O.2D.1's own findings rather than trusting that report's prose as an oracle:

- `src/pcae/core/hatp_hardware_credentials.py` (286 lines, full read): confirms `HATPHardwareCredentialStore` exposes exactly one production method, `lookup_credential` — no `enroll`, `revoke`, `rotate`, `write`, or `create` method exists anywhere in the module. Confirms the module's own docstring: "Enrollment (writing a new credential into this registry) is explicitly OUT of Wave-5 scope -- HATP-001/149O.1D assign registry-mutation to a future Human/Admin-only administrative surface." Confirms the frozen `HardwareCredentialRecord` schema: `signer_key_id: str`, `provider_profile: str`, `protocol_name: str` (`"FIDO2" | "PIV"`), `algorithm: str`, `public_key: bytes` (parsed from `public_key_hex`), `status: str` (`"active" | "revoked"`) — no private-key material, no PIN, no secret device state.
- `src/pcae/core/hatp_fido2_provider.py` (405 lines, full read): confirms `Fido2HardwareProvider.credential_identity()` (lines 270-276) is a pure, unconditional `raise HATPProviderUnavailableError(...)` — no `if`, no device probe, no resident-credential discovery call, independent of whether a physical device is attached. Confirms `verify()` (lines 341-404) returns `signature_valid=False` whenever `record_store.lookup_credential(signer_key_id)` returns `None` (line 359) — the mechanism B-1 depends on.
- `src/pcae/core/hatp_piv_provider.py` (119 lines, full read): confirms `PivHardwareProvider.credential_identity()` (lines 93-94) is likewise an unconditional `raise HATPProviderUnavailableError(_UNAVAILABLE_REASON)`, and confirms the module's own `NOT_CONFORMANT` design-conformance verdict and "no PKCS#11/smart-card library is installed or selected" disclosure.
- `src/pcae/core/hatp_providers.py` (392 lines, full read): confirms `HATP_HARDWARE_PROVIDER_V1` is a one-member closed tuple; confirms `HATPHardwareSigner.credential_identity()`'s Protocol-level docstring ("Stable key/credential identifier... usable for enrollment by a future Wave-2/7 administrative surface. This method only reports the identity -- it enrolls nothing itself").
- `src/pcae/core/hatp_signing_ceremony.py` (726 lines; `_resolve_signer`, lines 528-556, read in full): confirms HSCE-REQ-018/024's own text — `principal_id`/`signer_key_id` are resolved exclusively from `provider.credential_identity()`, meaning the signing-ceremony *production* side is equally blocked by B-2's finding, not merely the enrollment side HPSE-001 itself governs; this independently corroborates that the gap is systemic to the provider layer, not narrow to enrollment.
- `src/pcae/core/human_approval_trusted_provenance.py` (`verify_hatp_proof`, lines 762-926, read in full): confirms the live cross-check chain (signer via `trust_store.lookup_signer`, `principal.status`, `authority.status`, and `DeploymentBinding` field cross-checks against the live signer record) that this repair documents explicitly at HPSE-REQ-067/068 (closing NB-1).
- `docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md` (HPSE-001 v1.0, full read, 192 lines): confirms HPSE-REQ-010/011's exact v1.0 text, HPSE-REQ-044/045/046's exact v1.0 text, and confirms §2's exact v1.0 scope-exclusion language for `hardware-credentials.json`.
- `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` (HATP-001 v1.0 header read): confirms HATP-001 remains FROZEN, unamended, and is not touched by this repair.
- `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.2 header read): confirms HBDC-001 v1.2's own header text, including its existing "Depends on: ...HPSE-001 v1.0... does not require it to be implemented or independently verified for §16.2's own text to be well-formed" disclosure — confirming HBDC-001's own text does not require updating merely because HPSE-001's version number changes (§25 below).

**Both findings remain true at this phase's entry.** Source has not changed since Phase 149O.20L.7O.2D.1 (`d12462c4` is that phase's own completion commit; no intervening phase touched any of the seven files above).

### B-149O.20L.7O.2D.1-1, reconstructed

HPSE-001 v1.0 §2 explicitly excludes `hardware-credentials.json` from its own scope ("a separate, sibling protected artifact this contract references but does not amend") without naming a required future writer or companion contract for it anywhere in the document — unlike its careful naming of the `PrincipalRecord.revoked_at` widening (HPSE-REQ-008) and the `DeploymentBinding` producer amendment (HPSE-REQ-047/048). Since `Fido2HardwareProvider.verify()` unconditionally fails whenever no matching credential record exists, and nothing in v1.0 ever requires one to be written, a signer enrolled to the letter of every one of HPSE-001 v1.0's 52 requirements is permanently unable to produce a proof that reaches `VALID`.

### B-149O.20L.7O.2D.1-2, reconstructed

HPSE-REQ-010/011 (v1.0) characterized `credential_identity()` as a method that "MAY be unable to re-derive" a signer identity "from the physical device alone at a later time" — language that reads as a narrow re-derivability limitation on an otherwise-working method. The actual state, confirmed by direct source read above: both `Fido2HardwareProvider.credential_identity()` and `PivHardwareProvider.credential_identity()` unconditionally raise `HATPProviderUnavailableError`, regardless of device presence. HPSE-REQ-046's first-use sequence names "(1) physical credential provisioning" as the sole prerequisite before enrollment; even a fully provisioned, attached, compliant device would not let `enroll_signer` succeed today, because no code path anywhere in this codebase can produce a real `signer_key_id` from a live device.

## 2. `hardware-credentials.json` semantic reconstruction (§4 of the governing prompt)

Frozen exactly as `hatp_hardware_credentials.py` already defines it (no parallel registry invented, per the governing prompt's own §4 instruction):

- **Canonical path:** platform-fixed (`/Library/Application Support/PCAE/HATP/hardware-credentials` on macOS, `/etc/pcae/hatp/hardware-credentials` on Linux), sibling to (not inside) the Wave-2 trust-store root, never derived from `Path.home()`/environment/CLI input.
- **Schema:** a JSON document with a top-level `"credentials"` array; each element parses to `HardwareCredentialRecord(signer_key_id: str, provider_profile: str, protocol_name: "FIDO2"|"PIV", algorithm: str, public_key: bytes, status: "active"|"revoked")`.
- **Record identity:** `signer_key_id` (matched 1:1 against the identical field in `registry.json`'s `SignerRecord`, per HPSE-REQ-061, new this amendment).
- **Provider-specific fields:** `protocol_name`, `algorithm` (a COSE algorithm identifier name, e.g. `"ES256"`).
- **Public/credential material permitted:** `public_key` (DER SubjectPublicKeyInfo, hex-encoded on disk as `public_key_hex`).
- **Private material forbidden:** no field for private key, PIN, or secret device state exists in the schema; the module's own docstring states this explicitly ("item 73").
- **Status/lifecycle:** two-value `{"active", "revoked"}`, identical vocabulary to `PrincipalRecord`/`SignerRecord`.
- **Ownership/trust boundary:** provider-owned, read-only from every consumer's perspective today; no writer exists in production code.
- **Reader:** `HATPHardwareCredentialStore.lookup_credential(signer_key_id)`.
- **Verification consumer:** `Fido2HardwareProvider.verify()` (and, by the identical pattern, any future `PivHardwareProvider.verify()`), called from inside `human_approval_trusted_provenance.verify_hatp_proof`'s `provider.verify(...)` call.

This repair does not widen this schema. HPSE-REQ-054 (new) explicitly binds HHCE-001's future writer to this exact, already-defined schema.

## 3. Selected writer-contract disposition (§6 of the governing prompt)

Three options were evaluated: (A) bring the `hardware-credentials.json` writer into HPSE-001's own scope; (B) a full new companion contract, authored now; (C) an explicit prerequisite contract referenced by name, not authored now.

**Selected: (C).** Full rationale is recorded normatively in the contract text itself (HPSE-001 v1.1 §27, reproduced in substance here): `hardware-credentials.json` is a deliberately separate trust boundary from `registry.json` — different protected root, different schema, different threat model (public-key material vs. identity/authorization binding) — and HPSE-001 v1.0 §2 was already careful to draw that scope line. Collapsing the writer's full requirement set into HPSE-001 (option A) would blur a boundary the original contract deliberately established, and would expand this repair phase's own explicit mandate ("repair contract architecture only... in response to the two Blocking findings") well past a narrow, targeted amendment. Authoring a full second contract now (option B) is a materially larger undertaking than this phase's mandate calls for — HPSE-001 v1.0 itself set the precedent for the correct scope discipline here: §21-§22 name a required future `DeploymentBinding` producer amendment precisely, in two paragraphs, without authoring it. Option (C) — naming **HHCE-001 ("HATP Hardware Credential Enrollment Contract")** as a required future companion contract, with its minimum required scope bounded (not authored) — is the minimum coherent repair that structurally closes B-1 (via the cross-registry precondition, HPSE-REQ-056, §4 below) rather than merely disclosing it. This is recorded as HPSE-REQ-053/054 (HPSE-001 v1.1 §27).

## 4. Cross-registry consistency model (§9-§10 of the governing prompt)

The load-bearing invariant (HPSE-REQ-056, HPI-7): **an `active` `SignerRecord` MUST have a corresponding `active` `HardwareCredentialRecord` for the identical `signer_key_id`, checked live at `enroll_signer` time, before the signer write occurs.** Enrollment order is fixed: hardware credential registration (via HHCE-001's future writer) **before** signer enrollment (via this contract's `enroll_signer`) — never the reverse, never concurrent without the lock ordering below.

**Locking:** `hardware-credentials.json` requires its own independent lock (HPSE-REQ-057) — it is a separate file, so `registry.json`'s existing `.deployment-binding-transition.lock` (HPSE-REQ-033) does not automatically extend to it. A fixed global acquisition order is set to prevent deadlock: the hardware-credential-store lock is acquired **first (outer)**, `.deployment-binding-transition.lock` **second (inner)**, whenever one logical operation needs both (as `enroll_signer`'s HPSE-REQ-056 precondition check does).

**Atomicity strategy:** true cross-file atomicity is not assumed or required. The chosen staged strategy (HPSE-REQ-058, §5 below) has exactly the characteristics the governing prompt's §27 asked for: no active signer exists before its required credential record does (HPSE-REQ-056); a partial credential registration without a corresponding signer is harmless and inert (§5 case B); retries are idempotent (§5 cases A/B); state is reconcilable via audit-log comparison (§5 case D) rather than requiring an impossible real two-phase filesystem transaction.

## 5. Partial-failure model (§10 of the governing prompt)

Six named cases (HPSE-REQ-058, full text in the contract), summarized:

| Case | Outcome | Disposition |
|---|---|---|
| A. Credential write fails | `registry.json` untouched | Retryable, no side effect |
| B. Credential succeeds, signer fails | Credential durable but unreferenced | Harmless/inert (no active signer without it); retry is idempotent |
| C. Signer succeeds, credential missing | — | Structurally unreachable via this contract's own writer (HPSE-REQ-056's precondition check prevents it); if observed via out-of-band tampering, a reconciliation-scan finding, not a runtime case |
| D. Audit fails after durable write(s) | Durable-but-unaudited | Identical disposition to existing HPSE-REQ-039; never the reverse (audited-but-not-durable); recoverable by reconciliation |
| E. Read-back mismatch | Aborts before dependent write | Each write independently read-back-verified before the next step |
| F. Concurrent enrollment | Prevented | HPSE-REQ-057's fixed lock ordering rules out unsafe interleaving |

## 6. `credential_identity()` current-state correction and target semantics (§11-§14 of the governing prompt)

**Current-state correction (HPSE-REQ-011, revised in place, same ID):** the v1.0 text ("MAY be unable to re-derive... at a later time") is replaced with an explicit, precise disclosure that both production providers unconditionally raise `HATPProviderUnavailableError`, independent of device presence — a zero-implementation placeholder, not a re-derivability limitation. The revision is documented as a revision in the contract text itself (an inline "(revised, v1.1...)" marker on the requirement, plus §32's dedicated section and §46's closure mapping) — never a silent rewrite.

**Target semantics (HPSE-REQ-059, new):** freezes the required semantic *output* only — a stable, durable, protocol-appropriate credential-identity byte string obtainable exactly once, at enrollment time, via that provider's own canonical ceremony (e.g. a CTAP2 `makeCredential`-based ceremony for FIDO2). Deliberately does not freeze an implementation function name, per the governing prompt's own §14 instruction — a future implementation may keep `credential_identity()`, rename it, or introduce a distinct `enroll_credential()`; any of these satisfy HPSE-REQ-059 provided the semantic output matches.

**Hardware-provider implementation prerequisite (HPSE-REQ-060, new):** names, as a prerequisite distinct from and in addition to physical device provisioning (HPSE-REQ-045), that the selected provider implementation must actually implement HPSE-REQ-059's semantics before real enrollment can proceed. This is B-2's actual closure mechanism — not merely a corrected disclosure, but a named implementation gate (folded into the composite readiness gate, HPSE-REQ-072).

## 7. `signer_key_id` durability model (§15-§16 of the governing prompt)

**Disambiguation (HPSE-REQ-061, new):** `signer_key_id` is exactly the hex-encoded output of HPSE-REQ-059's canonical enrollment ceremony — never a separately hashed or otherwise-derived value. This makes explicit an equivalence HPSE-REQ-009/010/012 (v1.0) already implied (via the shared hex-encoding convention, HPSE-REQ-012) but never stated as a standing rule.

**Durable artifact (HPSE-REQ-062, new):** after enrollment, the authoritative source of truth is the *pair* — `SignerRecord` (identity/lifecycle binding, `registry.json`) and `HardwareCredentialRecord` (public-key material, `hardware-credentials.json`) — never either alone. `SignerRecord` carries no public-key material (HPSE-REQ-014, unchanged); `HardwareCredentialRecord` carries no principal binding. HPSE-REQ-056 guarantees both exist together for any `active` signer.

## 8. FIDO2/PIV treatment (§18 of the governing prompt)

HPSE-REQ-064 (new) confirms the correction and both new prerequisites (HPSE-REQ-059/060) apply identically and independently to both protocols — neither has a working implementation today, and both are gated by the same HPSE-REQ-060 prerequisite. Each protocol's own future ceremony mechanics may differ (HPSE-REQ-059 deliberately does not freeze one), but this contract does not fork into per-protocol enrollment contracts, mirroring the existing single-`provider_profile`-string design (HPSE-REQ-018/019, unchanged). Design-conformance verdicts remain distinct and are now stated explicitly in the contract text: FIDO2 is `CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS`, PIV is `NOT_CONFORMANT` — an existing, unmodified vocabulary fact, now disclosed (closes NB-3).

## 9. Physical credential prerequisite refinement (§19 of the governing prompt)

HPSE-REQ-065 (new) names four distinct states, never conflated: (1) compatible provider implementation exists (HPSE-REQ-060); (2) physical hardware credential available/attached (HPSE-REQ-045, existing); (3) credential registered into `hardware-credentials.json` (HPSE-REQ-056's precondition target); (4) signer enrolled into `registry.json` (`enroll_signer`, existing). HPSE-REQ-045/046 are revised in place to reflect this: REQ-045 gets a clarifying addition distinguishing its own "device present" scope from REQ-060's independent "provider implementation works" scope; REQ-046's first-use sequence expands from 8 to 12 steps to insert the provider-implementation and credential-registration steps explicitly, without removing any v1.0 step.

## 10. Enrollment readiness state machine (§20 of the governing prompt)

HPSE-REQ-066 (new): `PROVIDER_UNIMPLEMENTED → PROVIDER_AVAILABLE → CREDENTIAL_PRESENT → CREDENTIAL_REGISTERED → SIGNER_ENROLLED`, each strictly prerequisite to the next. Today's actual state for both protocols is `PROVIDER_UNIMPLEMENTED`. No stage's presence may be presented, logged, or interpreted as implying readiness at a later stage — directly closing the "presence == enrollment" conflation risk both Blocking findings exploited.

## 11. Producer/verifier trust clarification (§21-§22 of the governing prompt, closes NB-1)

HPSE-REQ-067/068 (new) document, without changing any production code, the hybrid disposition Phase 149O.20L.7O.2D.1 §9 independently confirmed already holds: `verify_hatp_proof` independently re-derives and cross-checks live signer/principal/authority/binding state on every verification call; `HBDC-REQ-042` remains scoped to deployment-identity matching only and is not, and need not become, the sole semantic-authority validator. A future amendment proposing to overload `HBDC-REQ-042` must first demonstrate why this existing hybrid disposition is insufficient.

## 12. Revocation clarification (§23 of the governing prompt)

HPSE-REQ-069 (new) names the *effective current disposition*, independently confirmed by Phase 149O.20L.7O.2D.1 §9: because `verify_hatp_proof` re-checks live status on every call (HPSE-REQ-067), an already-created `DeploymentBinding` referencing a since-revoked principal/signer does **not** need to be physically rewritten or revoked — any subsequent proof under that identity already fails closed at verification. This is documentation of existing production behavior, not a new requirement on `DeploymentBinding`/HBDC-001 (which this contract does not govern). A future HBDC-001 amendment may still add an explicit cascade check for defense-in-depth, but none is required to close a live gap, because none exists.

## 13. `PrincipalRecord.revoked_at` disposition (§24 of the governing prompt)

HPSE-REQ-008 is **unchanged**. Phase 149O.20L.7O.2D.1 independently found this disclosure "textbook... non-blocking," unambiguous, and precisely scoped. This repair reaffirms that verdict explicitly (a one-sentence "v1.1 note" appended to HPSE-REQ-008's existing text, §5) rather than silently leaving it unaddressed.

## 14. `authority_scope`/HBDC disposition (§25 of the governing prompt)

**Unchanged.** HBDC-001 v1.2's `authority_scope` vocabulary (§16.2, `HBDC-REQ-071..076`) was independently found sound by Phase 149O.20L.7O.2D.1 and is unrelated to either Blocking finding this repair closes. No HBDC-001 text was touched by this phase (§25 below expands on the one disclosed exception: a stale but harmless cross-reference).

## 15. Locking impact (§26 of the governing prompt)

HPSE-REQ-033 (existing, `.deployment-binding-transition.lock`) is **unchanged**. HPSE-REQ-057 (new) adds the additional ordering rule required now that a second lock exists (the hardware-credential-store lock): outer-then-inner, fixed, global, never reversed — see §4 above.

## 16. Atomicity/staging (§27 of the governing prompt)

See §4-§5 above. No impossible cross-file filesystem transaction is demanded; the chosen staged strategy (credential-first, signer-second, with a hard precondition check rather than a soft convention) achieves the governing prompt's own named preferred characteristics in full.

## 17. Audit ordering (§28 of the governing prompt)

HPSE-REQ-070 (new): hardware credential registration and signer enrollment SHALL each emit their own separately attributable audit event — never conflated, even when performed as part of one logical administrative session. This is required for §5's case-B/case-D dispositions to be meaningfully diagnosable in practice, not merely in principle.

## 18. Error vocabulary changes (§29 of the governing prompt)

HPSE-REQ-071 (new) extends HPSE-REQ-034's minimum error set with four members: `HARDWARE_PROVIDER_UNIMPLEMENTED`, `HARDWARE_CREDENTIAL_NOT_REGISTERED`, `HARDWARE_CREDENTIAL_CONFLICT`, `CREDENTIAL_IDENTITY_UNAVAILABLE` — the minimum set needed by §27-§38's new preconditions, no broader (per the governing prompt's own "do not casually expand error vocabulary" instruction).

## 19. Implementation-readiness gate (§30 of the governing prompt)

HPSE-REQ-072 (new): a single composite gate — (a) provider implementation satisfies HPSE-REQ-059/060; (b) HHCE-001 exists, is independently verified, and its writer is implemented and independently verified; (c) a matching active credential is actually registered; (d) target principal is active; (e) provider-profile consistency passes. `enroll_signer` implementation SHALL NOT begin until all five hold. This is this repair's direct mechanical closure of both Blocking findings, referenced explicitly by the closure mapping (§46 of the contract, reproduced at §21 below).

## 20. Future sequencing (§31 of the governing prompt)

HPSE-REQ-046 (revised in place) now states the 12-step sequence: provider-layer implementation → HHCE-001 writer implementation → independent implementation verification of both → physical provisioning → hardware credential registration → principal enrollment → signer enrollment (gated by HPSE-REQ-056) → independent verification of both registries → `DeploymentBinding` proposition → election + CHGR → `DeploymentBinding` creation → independent real-host verification. None of this sequence was executed this phase.

## 21. Blocking closure mapping (§37 of the governing prompt — reproduced from HPSE-001 v1.1 §46)

- **B-149O.20L.7O.2D.1-1** → HPSE-REQ-053, HPSE-REQ-054, HPSE-REQ-056 (the structural mechanism), HPSE-REQ-057/058 (safety under concurrency/partial failure), HPSE-REQ-072(b)/(c).
- **B-149O.20L.7O.2D.1-2** → HPSE-REQ-011 (revised), HPSE-REQ-059, HPSE-REQ-060 (the actual gap), HPSE-REQ-045/046 (revised), HPSE-REQ-064, HPSE-REQ-072(a).

Both findings converge on HPSE-REQ-072's single composite gate: an implementer cannot claim `enroll_signer` is implementation-ready while either finding's underlying gap remains open.

## 22. HMIC source-scope consequence (§32 of the governing prompt)

HPSE-REQ-073 (new, §44 of the contract) records — without amending HMIC-001 — the complete set of authority-bearing surfaces a future HMIC-001 source-scope analysis must include: the hardware-provider-layer implementation changes (already-HMIC-bound files, so any change mechanically triggers re-certification); HHCE-001's own writer module and script (new files, not yet bound); this contract's own future Principal/Signer writer module and script (already disclosed, v1.0 §26); the `DeploymentBinding` producer amendment (already named, HPSE-REQ-047/048); and `hatp_bootstrap.py` parser/schema changes for `PrincipalRecord.revoked_at` (already an HMIC-bound file). No HMIC-001 text was modified.

## 23. Runtime neutrality (§34 of the governing prompt)

HPSE-REQ-074 (new) extends HPSE-REQ-051's existing runtime-neutrality/non-agent-invocability discipline explicitly to HHCE-001's future writer. A scan of every file read this phase and the full amended contract text found zero occurrences of `Claude`, `Codex`, `DeepSeek`, or any other agent-runtime identifier outside HPSE-REQ-051/074's own explicit, defensive prohibitions naming those exact terms.

## 24. New HPSE-001 version, requirement IDs (§35 of the governing prompt)

**HPSE-001 v1.0 → v1.1** (in-place minor bump, mirroring this repository's own IWC-001 v1.0→v1.1 and TAMPC-001 precedent for a widening amendment that revises existing requirement text without renumbering). New requirement IDs `HPSE-REQ-053` through `HPSE-REQ-074` (22 new) were added strictly after `HPSE-REQ-052`, per this repository's standing convention ("never silently rewrite existing requirement identities"). Three existing requirements — `HPSE-REQ-011`, `HPSE-REQ-045`, `HPSE-REQ-046` — were revised **in place**: their text changed to correct/expand disclosure, but their IDs, numbering position, and requirement identity are unchanged; each revision is marked inline in the contract text itself ("(revised, v1.1...)") and cross-referenced from this report, never a silent rewrite.

## 25. HBDC-001 version disposition (§36 of the governing prompt)

**Unchanged — remains v1.2.** HBDC-001's `authority_scope` vocabulary (§16.2) and every other substantive section is untouched by this repair; per the governing prompt's own explicit instruction ("do not bump HBDC-001 version again unless its text actually changes"), no HBDC-001 edit was made. **One disclosed, deliberately-deferred residual staleness:** HBDC-001 v1.2's own header "Depends on" line still reads "HPSE-001 v1.0" (now stale, since HPSE-001 is v1.1 as of this phase) — left unrepaired for the identical reason (HBDC-001's own substantive text is unaffected), and recorded explicitly (HPSE-001 v1.1 §47, NB-5 disposition) as a known future documentation-only touch-up, mirroring the pre-existing NB-5 staleness precedent HBDC-001 already carried before this phase.

## 26. Implementability test (§40 of the governing prompt)

Re-applying Phase 149O.20L.7O.2D.1's own test against the repaired text: **could two competent implementers, both claiming full HPSE-001 v1.1 compliance, produce materially incompatible enrollment systems?**

- **When does the credential record become active?** Unambiguous: at HHCE-001's `register_credential` write, read-back-verified, per HPSE-REQ-054's mirroring of HPSE-REQ-032.
- **When does the signer record become active?** Unambiguous: at `enroll_signer`'s write, gated by HPSE-REQ-056's precondition (already-active credential record for the identical `signer_key_id`), under the fixed lock ordering of HPSE-REQ-057.
- **What does `signer_key_id` mean?** Unambiguous after HPSE-REQ-061: exactly the hex-encoded output of HPSE-REQ-059's canonical enrollment ceremony, never a separately derived value.
- **Which operation writes `hardware-credentials.json`?** Unambiguous: HHCE-001's writer only (HPSE-REQ-053/054); `enroll_signer` never writes it directly, only reads it as a precondition check (HPSE-REQ-056).
- **Provider-unimplemented behavior?** Unambiguous: `HARDWARE_PROVIDER_UNIMPLEMENTED` (HPSE-REQ-071), distinct from the existing device-absence `HATPProviderUnavailableError`/`CREDENTIAL_IDENTITY_UNAVAILABLE` case.
- **Partial-failure recovery?** Unambiguous: the six-case matrix (HPSE-REQ-058) names a disposition for every combination the governing prompt's own §10 asked about.

**No — the repaired contract no longer permits this divergence.** Both implementers are now structurally prevented (HPSE-REQ-056, HPI-7), not merely warned by disclosure, from producing a `SignerRecord` that is durable, audited, and structurally indistinguishable from a real signer yet functionally inert — the exact defect Phase 149O.20L.7O.2D.1 found.

## 27. Proof of scope discipline

- **No implementation:** no production `.py` file under `src/pcae/` or `scripts/` was modified this phase. See §29 for the mechanical `git diff` confirmation.
- **No Dell mutation:** no SSH session or remote command was issued this phase.
- **No credential provisioning:** no physical device interaction of any kind occurred.
- **No enrollment:** no `PrincipalRecord`/`SignerRecord`/`HardwareCredentialRecord` was created, read from a live registry, or referenced beyond reading existing source/documentation/schema definitions.
- **No `DeploymentBinding` creation, no election initiated, no CHGR published, no certification performed, no Boundary A/B/C activity, no HATP activation, no Protected Root mutation, no RepositoryIdentity mutation:** none occurred.

## 28. Final verdict

```
HATP PRINCIPAL/SIGNER ENROLLMENT CONTRACT REPAIR:
HPSE-001 v1.0 -> v1.1

CONTRACT REPAIRED — READY FOR SECOND INDEPENDENT VERIFICATION

Blocking findings closed by this repair: 2
  B-149O.20L.7O.2D.1-1 -> HPSE-REQ-053/054/056/057/058/072(b)(c)
  B-149O.20L.7O.2D.1-2 -> HPSE-REQ-011(revised)/045(revised)/046(revised)/059/060/064/072(a)
Non-Blocking findings: 5 total -- 2 repaired now (NB-1, NB-3), 1 already resolved (NB-4,
  reaffirmed), 2 explicitly deferred (NB-2: future implementation-hygiene; NB-5: HBDC-001's
  own pre-existing scope, plus one newly-disclosed, deliberately-deferred residual staleness
  in HBDC-001's own header cross-reference)

New requirement IDs: HPSE-REQ-053..074 (22 new)
Requirements revised in place (same ID): HPSE-REQ-011, HPSE-REQ-045, HPSE-REQ-046
Requirement count: 74 (HPSE-REQ-001..074, sequential, no gaps, no duplicates -- mechanically
  re-verified)
HBDC-001: unchanged, remains v1.2

Implementation remains prohibited. No enrollment writer, no HHCE-001 writer, and no
hardware-provider-layer implementation exist after this phase. Second independent
verification (149O.20L.7O.2D.3) is required before any implementation phase may begin.
```

This verdict does not mean the repaired contract is implementation-ready — it means the contract text itself no longer contains the specific defect (B-1/B-2) an implementer could exploit to produce a compliant-but-inert signer. HPSE-REQ-072's composite gate remains unsatisfied (HHCE-001 does not exist; no provider implements HPSE-REQ-059's semantics) — implementation of `enroll_signer` remains correctly blocked by the contract's own text, exactly as intended.

## 29. Tests

`tests/test_phase_149o_20l_7o_2d_2_hatp_principal_signer_enrollment_contract_repair.py` — mechanically re-verifies this phase's own load-bearing claims against live source and the amended contract text, never against this report's own prose: requirement-numbering completeness (001..074, no gaps, no duplicates); presence and exact IDs of every new requirement named in the closure mapping; that `HPSE-REQ-011`/`045`/`046` are marked as revised while every other v1.0 requirement's original text is preserved verbatim; the version bump to v1.1; the HHCE-001 naming; the composite implementation-readiness gate's five named preconditions; that HBDC-001's text is byte-for-byte unchanged since phase entry; and that no `src/`/`scripts/` file changed since the phase-entry commit.

## 30. Governance results, commits, push status

See `.pcae/phase-completion-metadata.json` / `.pcae/phase-completion-report.md` for the canonical machine-checked record (health/check/fast_green/full-suite results, commit list, `origin/main..HEAD`, pushed status) generated by `pcae phase complete`.

## 31. Recommended next phase

**149O.20L.7O.2D.3 — HATP Principal/Signer Enrollment Contract Repair Independent Verification.** Must independently re-derive both former Blocking findings against this v1.1 text and prove they are actually closed (not merely narrated as closed); must attack HHCE-001's named-but-unauthored disposition, the cross-registry consistency invariant's structural (not merely disclosed) closure, the lock-ordering rule's deadlock-freedom, the six-case failure matrix's completeness, `signer_key_id` durability, FIDO2/PIV parity, the readiness state machine, the updated error vocabulary, the composite implementation-readiness gate's sufficiency, audit ordering, and runtime neutrality. Must not implement anything.

## 32. Strategic breakpoint

Unaffected and preserved. The approved breakpoint remains after the first `DeploymentBinding` is created and independently verified on the real host, before Boundary C. This phase performed no enrollment, no provisioning, no `DeploymentBinding` creation, no election, no CHGR, no certification, and no Dell mutation — the breakpoint precondition is unchanged and unreached. After that eventual milestone: DeepSeek Harness vs PCAE Comparative Architecture Study, then PCAE Runtime Adapter + Plugin Architecture Proposal — not started this phase.
