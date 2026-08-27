# Phase 149O.20L.7O.3W.1R.2B — Runtime Invocation Human-Principal Authentication Contract Freeze

## 1. Objective

Freeze the minimum contract architecture required to make

```text
authenticated human principal
  -> explicit invocation approval act
  -> verifiable approval proof
  -> RuntimeInvocationApproval provenance
```

a trustworthy chain, resolving finding **N2** left open by
149O.20L.7O.3W.1R.2 (STOPPED, contract-insufficient) and architected by
149O.20L.7O.3W.1R.2A (read-only, contract evolution not yet frozen). This
phase is contract-only: it implements nothing, touches no hardware,
activates no execution, and repairs no B1/B7/N1 finding.

## 2. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| Phase-entry SHA | `ca09ab39befc24bd68d510337224daabc6ab32c8` (== `origin/main`) |
| Ahead of `origin/main` | 0 |
| Public release | v0.4.3 at `63580893b1de4782a694ab802ff7bdebdf29b0e6`, unchanged |
| Runtime | `Observed` / `observe` / `unavailable` |
| Entry Git state | clean |
| `pcae health`/`check`/`status coherence`/`push check`/`runtime inspect` | healthy / passed / coherent / clean (nothing to push) / not_implemented, Observed, unavailable |
| `pcae doctor task-memory` | pre-existing `tasks/DONE.md` sync warnings only (unrelated historical debt, unchanged by this phase) |
| Telegram | configured, enabled, outbound-ready |
| No active governed phase before start | confirmed (agent lock held for this session; idle task active) |

## 3. N2 exact requirement

Recovered verbatim from primary evidence, re-confirmed against source this
phase (`src/pcae/core/runtime_authority.py:387` `create_runtime_invocation_approval`,
`:285` `ApprovalProvenance`, `:858-860` `validate_approval`):

> "`create_runtime_invocation_approval` is a public callable that accepts
> `approver_id` and `identity_evidence_kind` as strings and emits a record
> that validates as `identified_human_distinct_from_producer`, without
> trusted confirmation evidence." (3W.1R.1 §14)

**What the current path accepts:** any caller may pass
`approver_id="atila-madai"`, `identity_evidence_kind="os_authenticated_user"`
(or `"typed_confirmation_only"`) and receive a fully schema-valid,
digest-consistent `RuntimeInvocationApproval`. `validate_approval`'s only
checks (`runtime_authority.py:858-860`) are "is `approver_id` non-empty" and
"does `approver_id` differ from the fixed `producer_component` constant."

**What trusted-human property is missing:** independent verification that a
real human, distinguishable from any co-resident autonomous process under
the same OS account, actually produced the approval act. `identity_evidence_kind`
membership in its two-value enum is checked; whether the claimed evidence
*exists* is never checked.

**Why caller-manufacturable provenance is unsafe:** PCAE is an autonomous
coding harness. A delegated or forked agent runs under the identical OS
account as the human operator (RIHAC-001 v1.1 §3, the mandatory same-user
autonomous-agent threat). Any caller reachable through the foundation API —
including, per 149O.20L.7O.3W.1R.2A §4, an agent process, not only a
human-typed CLI invocation — can construct a valid-looking approval with no
human ever having reviewed anything.

**Why v1.0 contracts were insufficient:** RIHAC-001 v1.0 §3 stated
"identified by provenance evidence" as a requirement but never defined what
verifying that evidence concretely requires; RIASC-001 v1.0 §7 defined a
schema shape (`approver_id`, `identity_evidence_kind` enum) that is
satisfiable by an unauthenticated caller string. Schema conformance was
mistaken, structurally, for authority — exactly the "valid provenance-shaped
data != authenticated human provenance" distinction this phase's governing
prompt names explicitly.

## 4. Contract evolution set

Per RPAC-001/PBRD-001/RDGO-001 re-reading this phase (§46-§48 below), only
RIHAC-001 and RIASC-001 require evolution, plus one new companion contract:

| Contract | Prior version | New version | Change |
|---|---|---|---|
| RIHAC-001 | 1.0 | **1.1** | Additive tightening: §3/§12/§16 now require principal-registry lookup + proof verification |
| RIASC-001 | 1.0 | **2.0** | `provenance` required-field meaning redefined (`approver_id`/`identity_evidence_kind` retired, four new fields added) — see §26-§27 |
| HPAC-001 | (new) | **1.0** | New companion contract owning principal identity, registry, mechanism abstraction, proof, verification |
| PBRD-001 | 1.1 | 1.1 (unchanged) | PB receives only a reference/projection; no field change required (§46) |
| RDGO-001 | 2.0 | 2.0 (unchanged) | Authentication fits inside existing gate 3/gate 5 content (§47) |
| RPAC-001 | 1.0 | 1.0 (unchanged) | RPAC-REQ-049 already anticipated this (§48) |

No PBRD-001/RDGO-001/RPAC-001 evolution was required, so this phase does
not stop under item 4's "STOP and explain before broadening scope" rule —
scope stayed exactly at RIHAC-001 + RIASC-001 + one new companion contract,
as anticipated.

## 5. Contract artifacts

Frozen this phase:

- `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` — RIHAC-001 v1.1 (amended in place)
- `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` — RIASC-001 v2.0 (amended in place)
- `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` — HPAC-001 v1.0 (new)

No separate proof schema or principal-registry schema file was frozen as an
executable JSON Schema resource — following this repository's existing
precedent (RIASC-001 §title note: "intentionally does not add an executable
schema under `src/pcae/schema_resources/**`"), the normative shapes for
`HumanAuthenticationProof`, `PrincipalRecord`, and `CredentialRecord` are
frozen as Markdown contract text inside HPAC-001 §5/§17, for a later
implementation to transcribe under separately authorized governance.

## 6. Human principal

HPAC-001 §4 (HPAC-REQ-007 through HPAC-REQ-011). `principal_id` is a
stable, non-display, opaque identifier, explicitly excluded from equaling
any OS username, UID, Git identity, PCAE agent/session identity, or
producer identity. Immutable across credential rotation and revocation;
never reassigned or reused after revocation.

## 7. Principal registry

**Decision: yes, a canonical `HumanPrincipalRegistry` is required**
(HPAC-001 §5, HPAC-REQ-012 through HPAC-REQ-017). Two record kinds:
`PrincipalRecord` (`principal_id`, `status`) and `CredentialRecord`
(`credential_id`, `principal_id`, `mechanism_id`, `public_key_ref`,
`status`, `enrolled_at`, `revoked_at`). No email, legal name, or biometric
material is stored (§23 of HPAC-001).

## 8. Enrollment

HPAC-001 §8 (HPAC-REQ-025 through HPAC-REQ-029). Enrollment establishes who
may ever authenticate; it does not itself authenticate or approve.
Operations: `enroll_principal`, `revoke_principal`, `enroll_credential`,
`revoke_credential`, plus a preview variant for each. Every operation
requires fresh, separate election evidence — no self-enrollment shortcut,
including for the admin's own enrollment.

## 9. Bootstrap trust

**Who trusts the first principal?** HPAC-001 §7 (HPAC-REQ-023): a local
admin/human bootstrap ceremony, run by the human physically controlling the
deployment machine at that moment. This mirrors HATP's own precedent
(HBDC-REQ-066's "Admin execution principal") and standard trust-anchor
bootstrapping (WebAuthn's own first-registration model). No PCAE-internal
mechanism resolves this circularly; trust is anchored in physical/local
control at the one bootstrap moment.

## 10. Same-user-agent threat

Frozen as a mandatory normative threat in RIHAC-001 v1.1 §3 and HPAC-001
§0/§34 (HPAC-REQ-086): PCAE is an autonomous coding harness; a real or
delegated agent executes under the same OS account as the human operator.
OS username, filesystem ownership, environment variables, local process
UID, ordinary CLI stdin, and Git identity are each individually and jointly
insufficient — none requires anything a co-resident process cannot
silently produce.

## 11. Assurance requirement

HPAC-001 §20 (HPAC-REQ-059/060). Closed vocabulary: `ASSERTED` (never
sufficient — this is v1.0's retired shape), `PRESENCE_GATED`, and
`HARDWARE_BACKED_PRESENCE_GATED`. Minimum required for real local-CLI v1
dispatch: `PRESENCE_GATED` or stronger. `ASSERTED` can never qualify.

## 12. FIDO2 mechanism

HPAC-001 §14 (HPAC-REQ-039 through HPAC-REQ-046). `mechanism_id`:
`hpac.fido2.presence_gated.v1`. Credential enrollment reuses HPSE-REQ-059's
frozen target semantics as a *pattern* against HPAC-001's own separate
registry. Challenge generation binds a fresh nonce plus the exact RIHAC-001
approval-preview digest. UP (user presence — physical touch) is **required**;
UV (user verification — PIN/biometric) is **deployment-configurable, not
load-bearing** for the specific same-user-agent threat this contract
resists (§13 below elaborates the reasoning). Signed assertion verified
against enrolled public key material. Principal mapping via
`CredentialRecord.principal_id`. Replay protection via single-use
challenge/nonce, durably recorded as consumed at verification.

## 13. HATP reuse vs. separation

**Mandatory determination, resolved as Option B** (HPAC-001 §6): reuse the
low-level FIDO2 provider *pattern*, and permit a future implementation to
reuse the low-level FIDO2 *primitives* as a library dependency, while
maintaining a completely separate `HumanPrincipalRegistry` document,
`principal_id` namespace, and challenge domain from HATP's own `registry.json`.

- **Option A (direct reuse of HATP's registry) — rejected:** `registry.json`
  is HPSE-001-scoped to Class-B Protected-Root admin-signing authority
  (HBDC-REQ-066); RPAC-REQ-049 already forbids reinterpreting HATP
  artifacts as generic invocation permission. Direct reuse would either
  need an out-of-scope HPSE-001 amendment or silently collapse `HATP
  authority == runtime invocation approval authority`, which this phase's
  governing prompt explicitly forbids.
- **Option C (entirely separate, no shared pattern) — rejected:** would
  discard HPSE-001/HHCE-001's already-correct, already-verified
  registry-write discipline and HATP's already-correct low-level FIDO2
  primitive shape for no benefit — premature reinvention.
- **Option B — selected**, per HPAC-001 §6 in full.

## 14. Credential/domain separation

Cross-domain credential reuse (same physical FIDO2 device enrolled under
both HATP and HPAC-001) is **permitted** (HPAC-001 §15, HPAC-REQ-047/048):
the key material itself is not the authority boundary; the challenge domain
is. Each enrollment receives its own distinct `credential_id`/`signer_key_id`
in its own registry, preserving independent audit attribution and
preventing cross-domain replay: a challenge tagged
`hpac.runtime_invocation_approval.v1` cannot verify as an HATP signing-
ceremony assertion, and vice versa.

## 15. Challenge subject

HPAC-001 §16 (HPAC-REQ-049). The challenge binds `principal_id`, the exact
RIHAC-001 approval-preview digest (which already encodes `invocation_id`,
`runtime_target_id`, `prompt_hash`, `repository_identity`, `task_id`, and
`approval_scope` per RIHAC-001 §10/§11), a fresh nonce, and the
`hpac.runtime_invocation_approval.v1` domain tag.

## 16. Nonce/replay

HPAC-001 §16/§24 (HPAC-REQ-050/HPAC-REQ-071/HPAC-REQ-072). Origin:
cryptographically strong random bytes from the trusted challenge-
construction component. Uniqueness: never repeats. Lifetime: short,
separately-governed bound (not numerically frozen here, per RIHAC-001's own
precedent of not freezing an arbitrary `expires_at` duration). Storage:
durably recorded as consumed atomically with successful verification, never
before or after that exact point. A proof for invocation A fails for
invocation B even under an otherwise-valid, unconsumed challenge — subject
binding and nonce consumption are checked independently.

## 17. Authentication proof

HPAC-001 §17 (HPAC-REQ-052/053). `HumanAuthenticationProof` fields:
`proof_id`, `mechanism_id`, `principal_id`, `credential_id`,
`challenge_digest`, `assertion` (opaque, mechanism-specific), `authenticated_at`,
`verifier_version`. No secret, PIN, private key, or raw biometric material.

## 18. Proof verification

HPAC-001 §18 (HPAC-REQ-054/055) — exact ten-step fail-closed sequence:
principal lookup (active) → credential lookup (active, bound to principal)
→ mechanism lookup (assurance ≥ minimum) → challenge-digest recomputation
→ subject binding → assertion/signature verification → presence/verification
flag check → freshness → replay check → emit trusted
`AuthenticatedHumanPrincipal`. No later step substitutes for an earlier
failure.

## 19. Authenticated principal handle

`AuthenticatedHumanPrincipal` (HPAC-001 §19, HPAC-REQ-056). A
trusted-construction type producible only as the successful-verification
return value, mirroring — and deliberately not repeating — the exact class
of mistake B1 already names for `ValidatedAuthorityProjection`
(149O.20L.7O.3W.1R.2 §9).

## 20. Trusted construction

HPAC-REQ-057. Callers (adapter, runtime, CLI argument, approval producer)
cannot construct, replay-serialize, or otherwise manufacture an
`AuthenticatedHumanPrincipal` without a fresh, successful ten-step
verification producing it.

## 21. RuntimeInvocationApproval creation

Future flow (RIHAC-001 v1.1 §3/§16 step 4, HPAC-001 §18-19): approval
request subject → authenticated-principal challenge (HPAC-001 §16) →
authentication proof (HPAC-001 §17) → verified human principal (HPAC-001
§18-19) → `RuntimeInvocationApproval` creation (RIHAC-001 gate 3) →
canonical store (RIASC-001 §12). No caller-provided `approver_id` shortcut
exists anywhere in this flow — the field itself is retired (§26 below).

## 22. RIHAC v1.1 changes

Exact changed sections (`docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`):

- **§3** — new normative text defining exactly what "identified by
  provenance evidence" requires: `principal_id` resolution against an
  `active` registry record, a verified `HumanAuthenticationProof` over the
  approval-preview digest and a fresh challenge, and successful
  verification by the trusted validator. Retires the two-member
  `identity_evidence_kind` enum as insufficient. States the same-user-agent
  threat as binding normative text (not merely architecture commentary).
- **§12** — adds condition 7 ("successful HPAC-001 authentication-proof
  verification") to the "V1 trust is the conjunction of" list; retires the
  v1.0 sentence "No cryptographic signature is required for v1."
- **§16 step 4** — elaborated into a lettered (a)-(g) sub-sequence
  (registry lookup, credential lookup, mechanism-assurance check, proof
  load and subject-binding check, signature verification, replay check,
  fail-closed on any).
- **§14** — new cross-reference to HPAC-001 §21 for principal/credential
  revocation as an upstream freshness input, distinct from approval-level
  revocation (unchanged, still deferred per v1.0's own §14).
- **§21/§23** — versioning rationale and freeze-verdict version bump.

No subject member was removed (§5, still five members, unchanged), one-shot
semantics were not relaxed (§4, unchanged), and no existing RIHAC-001
required field/section number was deleted.

## 23. RIHAC versioning

**v1.1, additive tightening — not v2.0.** Per RIHAC-001 §21's own rule,
"additive clarification... may increment MINOR only when it does not widen
existing authority." This amendment narrows what counts as sufficient
provenance evidence (harder to satisfy, not easier), removes no subject
member, relaxes no one-shot semantics, and removes no RIHAC-001 required
field or section. RIHAC-001 is a semantic contract, not a schema — unlike
RIASC-001, it was never bound to the specific field name `approver_id`, so
retiring that field at the schema layer does not by itself force a MAJOR
bump at the semantic-contract layer. This matches the precedent PBRD-001
v1.0→v1.1 and RDGO-001 v1.0→v2.0 already set for their own additive-
tightening changes (149O.20L.7O.3W.1R.2A §39, reaffirmed here after full
re-derivation, not merely carried forward from the architecture document's
tentative recommendation).

## 24. RIASC v1.1 changes

See §26-§27. (RIASC-001's actual new version is v2.0 — see §25 for why the
architecture document's tentative "v1.1 or v2.0" question resolves to v2.0.)

## 25. RIASC cardinality reset

**Re-derived, not assumed.**

- **Top-level required-field count: unchanged at 16.** `provenance` remains
  one top-level required field; its own internal required-subfield set
  changes, but no top-level field was added or removed.
- **Subject cardinality: unchanged at 5 members** (`invocation_id`,
  `runtime_target_id`, `prompt_hash`, `repository_identity`, `task_id`).
  Human-principal identity is provenance, not subject — an explicit
  decision (§28 below), consistent with 149O.20L.7O.3W.1R.2A §35's
  "authenticated human approval event... is provenance, not part of the
  invocation subject" framing.
- **`provenance`'s own required-subfield count: 5 (v1.0) → 7 (v2.0).**
  Two retired (`approver_id`, `identity_evidence_kind`); four added
  (`principal_id`, `authentication_mechanism_id`, `credential_id`,
  `authentication_proof_ref`); three unchanged (`approval_mechanism`,
  `approval_preview_digest`, `producer_component`). Full field-by-field
  disposition table is in RIASC-001 v2.0 §7 itself; reproduced in the
  cross-contract matrix (§74 below).

## 26. Subject vs. provenance

**Decision: kept explicitly distinct.** Authenticated principal identity is
provenance (RIASC-001 `provenance` object), not part of the five-member
invocation subject (RIASC-001 `subject` object). Rationale: the subject
answers "what exact invocation was approved" (target, prompt, repo, task,
invocation identity) — a question independent of *who* approved it; adding
`principal_id` to `subject` would conflate "what was approved" with "who
approved it," and would force every subject-equality check (RIHAC-001 §5,
already load-bearing for dispatch-time revalidation) to also re-derive
principal freshness, which belongs to a different freshness axis (HPAC-001
§21's principal/credential revocation, distinct from RIHAC-001 §13's
seven approval-freshness conditions).

## 27. New authentication-proof schema

**Decision: yes**, frozen as HPAC-001 §17 (`HumanAuthenticationProof`) —
not as an executable JSON Schema resource in this phase (§5 above), mirroring
RIASC-001's own precedent of freezing normative Markdown shape without
production wiring.

## 28. Mechanism abstraction

`HumanAuthenticator` (HPAC-001 §10, HPAC-REQ-032/033): five
responsibilities — describe, status, prepare_challenge, verify_response,
resolve_principal. No implementation frozen; interface responsibilities
only, per the governing prompt's explicit "No implementation" instruction.

## 29. Mechanism descriptor / status

**Descriptor (static, HPAC-001 §14):** `mechanism_id`, `assurance_level`,
`offline_capable`, `presence_support`, `verification_support`,
`platform_compat`. **Status (dynamic, HPAC-001 §13):** `configured`,
`credential_available`, `verifier_available`, `healthy`, `unavailable`,
`revoked` — deliberately not conflated with registration.

## 30. FIDO2 UP/UV

**Decision, fully analyzed (HPAC-001 §14, HPAC-REQ-042):** UP (physical
touch) alone is the property that closes the mandatory same-user-agent
threat, because it is the one signal a co-resident autonomous process
structurally cannot produce without physical device access, regardless of
whether it can silently trigger the device's electrical wake state. UP is
therefore **required** in v1. UV (PIN/biometric identity binding) is
**deployment-configurable, not load-bearing for this specific threat** — UV
answers "which specific human among several who might share device access,"
a narrower question than "was *a* human present," and this contract's v1
default (one enrolled principal, §9 of HPAC-001) does not need to answer it
to close N2.

## 31. HATP compatibility

Resolved at §13 above and HPAC-001 §31 (HPAC-REQ-084): reuses HATP's
*pattern*, never its live registry state; no structural-similarity
acceptance across families, mirroring RIASC-001 §13's own existing rule.

## 32. Existing FIDO2 reuse

HPAC-001 §32 names the reusable production components conceptually:
`hatp_providers.py::HardwareProviderCapabilities` (descriptor shape),
`_PRODUCTION_HARDWARE_PROVIDER_PROFILES` (allowlist pattern),
`hatp_fido2_provider.py::Fido2HardwareProvider` (library-level primitive
reuse only, never a live HATP dependency), `repository_identity.py::_write_atomic`
(atomic write idiom), `hatp_bootstrap.PrincipalRecord`/`SignerRecord`
(schema-pattern reuse for a separate document). No code changes were made.

## 33. Hardware unavailable

HPAC-001 §33 (HPAC-REQ-085): required FIDO2 authenticator unavailable → no
authenticated proof → RIHAC-001 v1.1 §12 condition 7 unsatisfiable → no
trusted `RuntimeInvocationApproval` → no real dispatch. No fallback to a
caller assertion under any unavailability condition.

## 34. Revocation/recovery

HPAC-001 §21 (HPAC-REQ-061 through HPAC-REQ-065). Principal and credential
revocation are each independently monotonic. Revocation does not
retroactively invalidate an already-validated approval (matching RIHAC-001
v1.1 §14's identical open-question disposition, resolved identically in
both contracts). Revocation does invalidate every outstanding unconsumed
challenge for that principal/credential. Recovery: revoke + enroll a
replacement credential under the same `principal_id`; total principal loss
requires a bootstrap-ceremony repeat (§9 above) — no shortcut is invented,
since one would reopen the same-user-agent threat.

## 35. Enrollment threat model

HPAC-001 §28 (HPAC-REQ-079/080), fully analyzed at §41 below (malicious
repository). Agent self-enrollment is structurally impossible (enrollment
requires the out-of-repository admin writer plus fresh election evidence);
attacker credential replacement is bounded by the same election-evidence
requirement; copied/tampered registry state fails closed exactly as
HPSE-001's own registry-tamper discipline requires (unknown fields,
malformed documents rejected); stale credentials fail closed at §18 step 2.

## 36. Principal registry trust

Canonical-store trust patterns are reused: atomic write, read-back
verification, sorted deterministic serialization, closed schema (HPAC-001
§5). File location alone is never treated as sufficient — every principal/
credential lookup independently re-verifies `status == active` at
verification time (§18 step 1/2), never trusting a cached prior lookup.

## 37. Final trust conjunction

RIHAC-001 v1.1 §12, exact contract language, seven-condition conjunction:

```text
1. strict RIASC-001 (v2.0) schema validation
2. exact subject and scope binding
3. identified-human provenance
4. canonical-storage lookup (not caller-supplied path)
5. record-digest recomputation and exact comparison
6. current freshness and consumption-state validation
7. successful HPAC-001 authentication-proof verification
   (principal lookup, active status, credential lookup, challenge/subject
   binding, signature/assertion verification)
```

All seven are conjunctive; none substitutes for another; a missing or
failed condition 7 fails the whole conjunction regardless of 1-6.

## 38. B1 closure architecture

Unaffected in mechanism by this phase (B1 concerns *seal* forgeability, an
orthogonal axis to *whose* identity is bound), but its future repair
(HMAC-keyed content-bound seal, 149O.20L.7O.3W.1R.2 §9) now has a real
trust root to derive a future trusted PB projection from: authenticated,
HPAC-001-verified `RuntimeInvocationApproval` provenance, not a
transferable seal alone. This phase freezes the contract prerequisite; it
does not implement the repair.

## 39. B7 closure architecture

Unaffected in mechanism (B7 concerns *attempt* identity —
`invocation_id`/`attempt_id`/`idempotency_key` — a different axis from
*human* identity). HPAC-001's principal/proof model is kept structurally
separate from attempt-identity provenance (RIHAC-001 §6's PCAE-owned
`invocation_id` allocation is unchanged and unaffected by this amendment).
Identity registry re-check remains PCAE-owned and canonical-state resolved,
independent of, and not replaced by, human authentication.

## 40. N1 closure architecture

Canonical-store provenance becomes structurally mandatory at consumption,
in conjunction with (not instead of) HPAC-001 proof verification (RIHAC-001
v1.1 §12 conditions 4 and 7 together). Condition 4 alone (N1's eventual
fix) proves an object came from the canonical store; it does not prove a
human authenticated the object's *content* at creation time — condition 7
supplies exactly that missing half. Both are required together for a fully
trusted approval, per 149O.20L.7O.3W.1R.2A §38's own analysis, now frozen
as binding contract text rather than architecture commentary.

## 41. N2 closure architecture

**CONTRACT GAP CLOSED.** A caller-supplied `approver_id` string has no
authority anywhere in the new contract text: `approver_id` and
`identity_evidence_kind` are retired from RIASC-001 v2.0's `provenance`
object entirely (§26-§27); RIHAC-001 v1.1 §3 defines exactly what
provenance evidence must consist of (registry-resolved `principal_id` plus
a verified `HumanAuthenticationProof`); RIHAC-001 v1.1 §16 step 4 makes
that verification a mandatory validation sub-step, not an optional
enhancement. Only a verified `AuthenticatedHumanPrincipal` result (HPAC-001
§19, trusted-construction-only) may ever populate approval provenance.

## 42. PBRD impact

**No change required.** PBRD-001 already receives only a validated-
authority *reference* plus a validation-evidence *projection digest*
(PBRD-001 §7, fact #14 `human_authority_binding`) — never raw approval
prose, never raw `HumanAuthenticationProof` material. Re-confirmed this
phase by re-reading PBRD-001 v1.1 in full: no field, meaning, or precedence
in PBRD-001 references `approver_id`, `identity_evidence_kind`, or any
provenance subfield by name; the reference/digest shape is already
authentication-agnostic. HPAC-001 §11 (HPAC-REQ-035) makes this a binding
rule from the new contract's own side too: PB SHALL NOT become a human-
authentication verifier.

## 43. RDGO impact

**No change required; gate count/order/ownership unchanged at 11.**
Authentication is part of Gate 3 (human authority creation) and Gate 5
(approval validation), not a new gate — re-confirmed this phase by
re-reading RDGO-001 v2.0 §4/§6 in full. Gate 3's existing text ("A distinct,
non-defaultable human act creates the immutable RIASC-001 approval
artifact") already describes exactly the act this amendment makes
trustworthy; Gate 5's existing text ("validate producer and human
provenance") already names the exact validation step RIHAC-001 v1.1 §16
step 4 elaborates. No gate was added, renumbered, or reordered.

## 44. RPAC impact

**No change required.** RPAC-REQ-049 already explicitly permits "a later
policy [to] require hardware-backed human authority for a particular
effect" without amending RPAC-001 itself; RPAC-REQ-006's `ExecutionPrincipal`
row already states "cannot supply human authority," consistent with, not
contradicted by, this phase's selected architecture. Re-confirmed this
phase by re-reading RPAC-001's identity/audit/security-invariant sections
(§1, §15, §16) in full — RPAC-REQ-076 ("who requested; which human
approved...") is, per this phase, finally answerable truthfully once
implemented, but the requirement's own text needed no change to become
answerable.

## 45. Existing HATP contracts

Cross-checked this phase (HPSE-001 v1.1 read in full through §38, plus
targeted re-verification of `runtime_authority.py`): no hidden contract
collision. HPAC-001's separate registry, namespace, and challenge domain
(§13/§14 above) prevent any credential-registry, principal-binding,
provider-class, touch-semantics, challenge-replay, or signature-
verification conflict with HPSE-001/HHCE-001/HATP-001. See §84 of HPAC-001
(HPAC-REQ-084) for the binding no-structural-acceptance rule.

## 46. Existing FIDO2 reuse

See §32 above and HPAC-001 §32's reuse map. No code changes.

## 47. Hardware unavailable

See §33 above.

## 48. Mechanism fallback

**Decision: no automatic fallback in v1** (HPAC-001 §22, HPAC-REQ-066).
Explicit human/configured mechanism selection only. A gated software-key
fallback (HPAC-REQ-067) MAY be deployment-configured for hardware-less
environments, but only if presence-gated — a bare on-disk software key
never qualifies.

## 49. Alternative mechanisms

HPAC-001 §22 (HPAC-REQ-068): future mechanisms (OS-authenticated presence,
external approval service, another hardware authenticator family) MAY be
added as additional `HumanAuthenticator` implementations, provided each
declares its assurance level honestly and the minimum-required-assurance
gate is never lowered.

## 50. Assurance model

See §11 above (HPAC-001 §20). Small closed enum, not a boolean, chosen
because a middle `PRESENCE_GATED` value (non-hardware but still
presence-gated) is a real, useful distinction for the fallback mechanism
(§48), not overdesign.

## 51. Offline

HPAC-001 §30 (HPAC-REQ-082): the primary v1 mechanism functions fully
offline — no network call is required to produce or verify a proof.

## 52. Portability

HPAC-001 §30 (HPAC-REQ-083): FIDO2 CTAP2 hardware keys are portable across
macOS (development) and Linux (deployment) without a platform-specific
adapter, avoiding the dual-adapter cost an OS-authentication-primary
mechanism would require.

## 53. Audit/privacy

HPAC-001 §23 (HPAC-REQ-069/070). Audit records: `principal_id`, mechanism/
credential reference (not raw key material), challenge/nonce identifier
(digest, not raw value), verification result, timestamp, verifier version.
No PIN, private key, raw biometric template, or secret device state is ever
recorded. No email, legal name, or biometric template is persisted.

## 54. Same-user-agent proof obligation

HPAC-001 §34 (HPAC-REQ-086): a future implementation and its independent
verification SHALL affirmatively demonstrate that a same-OS-account
autonomous process cannot produce a passing proof without the human
physically performing the presence gesture. Named as a normative future
verification requirement, not evidence this contract-only phase produces.

## 55. Delegation/auto-approval

HPAC-001 §27 (HPAC-REQ-077/078): no delegation, no automated/policy-based
auto-authentication in v1. A delegated/forked agent can never become an
`AuthenticatedHumanPrincipal`.

## 56. Session caching

HPAC-001 §26 (HPAC-REQ-075/076): enrollment (durable) is distinct from
authentication (must not be cached). Each real invocation requires its own
fresh challenge and proof. No session-caching layer exists in v1; one, if
ever introduced, requires a separate governed contract amendment.

## 57. Replay

HPAC-001 §24 (HPAC-REQ-071/072). A proof for invocation A fails for
invocation B; a proof for a previous challenge fails for a new challenge.
Consumption recorded atomically with successful verification.

## 58. Registry scope

**Decision: deployment/user-scoped, not repository-local, not per-repo**
(HPAC-001 §7, HPAC-REQ-021). Human identity is user/deployment-level;
approval remains repo/task-bound via RIHAC-001's existing five-member
subject. A repository-local registry would force re-enrollment per
repository — inconvenient without adding security, since the registry path
is already outside repository-agent-write control regardless of whether it
is nominally "per-deployment" or "per-repository-tree" (the load-bearing
property is "outside the repo's own worktree," which a deployment-scoped
path satisfies directly).

## 59. Credential scope

Credential is a global-principal credential (bound to `principal_id` in the
deployment-scoped registry); approval challenges remain repo/task-specific
via the RIHAC-001 subject the challenge is bound to (§15 above). This
distinction is explicit and intentional, not incidental.

## 60. Trust-root scope

HPAC-001 §7 (HPAC-REQ-022): the canonical registry path is outside any
single repository's working tree or `.pcae/` governance store, at a
separate Protected-Root instance from HATP's own. This is the load-bearing
protection against the malicious-repository threat (§61 below): no code
path reachable from within a repository's own agent-writable tree can
resolve to this path by construction.

## 61. Malicious repository threat

Explicitly analyzed (HPAC-001 §28, HPAC-REQ-079/080): a repository under
agent control cannot enroll its own fake human credential (enrollment
requires the out-of-repository admin writer plus fresh election evidence,
neither reachable from repository-agent code); cannot alter the global
principal registry (path is outside repository control); cannot downgrade
required assurance (HPAC-REQ-060 is contract-fixed, not repository-
configurable); cannot silently select a weaker authenticator (no automatic
fallback exists, HPAC-REQ-066, and mechanism selection is deployment-
configured outside repository control).

## 62. Configuration authority

HPAC-001 §28 (HPAC-REQ-080): only the deployment/user-level admin, never
repository configuration, may configure the required authenticator
mechanism, registry location, and enrolled-credential set. Repository
configuration cannot lower security below this contract's fixed minimums.

## 63. Contract artifact set

Final: RIHAC-001 v1.1, RIASC-001 v2.0, HPAC-001 v1.0. No additional schema
contract was required as a fourth artifact (§27 above) — `HumanAuthenticationProof`
and the registry record shapes are frozen inside HPAC-001 itself, mirroring
HPSE-001/HHCE-001's own two-contract (not three-contract) precedent scaled
down by one, since this phase's proof schema is materially simpler than
HHCE-001's own planned hardware-credential-registry writer contract.

## 64. Companion contract naming/versioning

**HPAC-001** — "Human Principal Authentication Contract." No namespace
collision (checked this phase: `grep`-confirmed against every
`**Contract:**` identifier in `docs/contracts/*.md` — `HRAC-001` is already
in use for the unrelated HATP Remote Assertion Ceremony Contract, so that
candidate name was rejected in favor of `HPAC-001`).

## 65. Companion contract responsibility

HPAC-001 §1 (HPAC-REQ-002/003), reproduced verbatim: owns human principal
identity, `HumanPrincipalRegistry`, `HumanAuthenticator` mechanism
abstraction, enrollment, authentication proof, verifier behavior,
revocation, mechanism status, trust/assurance level, and failure behavior.
Does NOT own PB permission, runtime-target selection, execution capability,
Runtime Enforcement, or dispatch.

## 66. Static schema validation

No executable production schema was implemented this phase (§5/§27 above),
so no executable validator exists to run positive/negative fixtures
against. The normative Draft-2020-12-equivalent shapes in RIASC-001 v2.0
§10 (existing, amended §7 `provenance` object) and HPAC-001 §17
(`HumanAuthenticationProof`, described in prose per this repository's
existing precedent of not freezing executable JSON Schema for a new
artifact family in a contract-only phase) were reviewed by hand for: a
positive example (all required fields present, correct types); a
missing-field case (each of the 7 `provenance` fields individually
omitted — schema-invalid per `additionalProperties: false`/`required`);
an unknown-field case (`approver_id` reintroduced alongside the new fields
— rejected, `additionalProperties: false`); malformed-proof cases (wrong
`principal_id`, wrong `credential_id`, wrong `challenge_digest`, wrong
subject binding, replayed challenge) — each maps to a distinct, named
rejection point in HPAC-001 §18's ten-step sequence, confirmed by
inspection to have no gap where such a case would silently pass.

## 67. B1/B7/N1/N2 roadmap

| Finding | Contract change enabling repair | Future implementation action |
|---|---|---|
| B1 | RIHAC-001 v1.1 §12 condition 7 gives a real trust root a future HMAC-keyed seal can derive from | Implement seal keyed to verified, authenticated approval content, not a transferable sentinel |
| B7 | Unaffected structurally; RIHAC-001 §6 `invocation_id` allocation reaffirmed unchanged | Implement registry re-check at construction time (149O.20L.7O.3W.1R.2 §9), independent of N2 |
| N1 | RIHAC-001 v1.1 §12 condition 4 (unchanged) now pairs meaningfully with condition 7 | Implement store-bound validation handle; canonical-store provenance plus authenticated-principal proof together |
| N2 | **Directly closed** — RIHAC-001 v1.1 + RIASC-001 v2.0 + HPAC-001 v1.0 together remove every path by which a caller-supplied string could populate provenance | Implement `HumanAuthenticator` (gated on HHCE-001's disclosed provider-backend gap for the primary FIDO2 mechanism), `HumanPrincipalRegistry` writer, and RIHAC-001 v1.1 §16 step 4's verification sequence |

## 68. Implementation plan sequencing

```text
149O.20L.7O.3W.1R.2B  <- this phase: contract freeze (COMPLETE)
  -> 149O.20L.7O.3W.1R.2B.1  independent contract verification (NOT BEGUN)
  -> human-principal/FIDO2 implementation plan (NOT BEGUN)
  -> implementation (NOT BEGUN; gated on HHCE-001's disclosed
     provider-backend gap for the primary FIDO2 mechanism, HPSE-REQ-060)
  -> independent verification of implementation (NOT BEGUN)
  -> B1/B7/N1/N2 authority foundation repair (NOT BEGUN; per 149O.20L.7O.3W.1R.2A
     §67, sequenced after this freeze, not before)
  -> independent verification of repair (NOT BEGUN)
  -> Runtime Enforcement planning (NOT BEGUN; still gated on
     RPAC-REQ-045's later gates, POL-005 evolution boundary §12 of
     PBRD-001, and the two older 3S.2.1 MUST-FIX repairs at their
     reachability point)
```

Contract verification (149O.20L.7O.3W.1R.2B.1) is not skipped. This phase
stops here.

## 69. No production changes

Confirmed: no `src/pcae` file was modified; no test file was modified; PB,
Runtime Enforcement, Shell Gate, the current runtime approval
implementation, dry runtime, and `pcae runtime inspect` output are
unmodified. Only three normative contract Markdown files, this phase
document, and standard governance files (task/report/PROJECT_STATUS.md/
CHANGELOG.md) changed.

## 70. No hardware interaction

Confirmed: no FIDO2/hardware device was enumerated, touched, or enrolled;
no credential was signed; no WebAuthn/FIDO2 runtime API was called.
Contract/static text analysis only, exactly as HPAC-001 §36 requires of
this freeze.

## 71. No-Go

Confirmed for this phase: B1/B7/N1/N2 implementation was not repaired;
Runtime Enforcement was not activated; Shell Gate was not activated;
POL-005 was not relaxed; no process was launched; no Codex/Claude/OpenRouter
call occurred; no provider credential was accessed; no network was enabled;
`~/repos/pcae-deepseek-research` was not inspected, imported, relied upon,
or modified; the stopped article was not read, resumed, modified, or
published.

## 72. Governance

Governed lifecycle: agent lock acquired via `pcae session bootstrap`
(pre-existing from this session's bootstrap), phase started via `pcae phase
start` (already held — no separate acquisition needed), active task's
allowed-files/zones synced to this phase's actual scope before any edit
(`pcae task update`, see task contract). This document was authored
directly by the primary agent's fork, executing under the primary agent's
own explicit, self-contained directive (not an independently-scoped
delegation) — consistent with 149O.20L.7O.3W.1R.2C's recorded lesson that
phase finalization/commit/push must remain under primary-agent control; the
primary session reviews and finalizes this phase's own commit/push, per
that same lesson. No force, no `--no-verify`.

## 73. Required canonical report

See `.pcae/phase-completion-metadata.json` and the generated
`.pcae/phase-completion-report.md` for the full structured report,
produced via `pcae phase complete`.

## 74. Cross-contract matrix

| Concept | HPAC-001 | RIHAC-001 v1.1 | RIASC-001 v2.0 | PBRD-001 (unchanged) | RDGO-001 (unchanged) |
|---|---|---|---|---|---|
| `principal_id` | `PrincipalRecord.principal_id` (§4/§5) | §3 (new text) | `provenance.principal_id` | Not present (by design, §42) | Gate 3/5 content only |
| Mechanism | `mechanism_id`, descriptor (§14) | §3/§12 references it | `provenance.authentication_mechanism_id` | Not present | Gate 3/5 content only |
| Credential reference | `CredentialRecord.credential_id` (§9) | §16 step 4(b) | `provenance.credential_id` | Not present | Gate 3/5 content only |
| Proof reference/hash | `HumanAuthenticationProof` (§17), `challenge_digest` | §16 step 4(d) | `provenance.authentication_proof_ref` (id+digest) | Not present | Gate 3/5 content only |
| Challenge identity | `prepare_challenge` (§10/§16) | §16 step 4(d) | Not a schema field (verifier-internal) | Not present | Gate 3/5 content only |
| `approval_id` | Not present (different artifact family) | §15 (unchanged) | `approval_id` (unchanged) | `human_authority_binding` (ref+digest, unchanged) | Gates 3/5/9 |
| Invocation subject | Not present (HPAC-001 challenge binds *to* it, never redefines it) | §5 (unchanged, 5 members) | `subject` (unchanged, 5 members) | 14 facts (unchanged) | Gates 2-11 |
| Authenticated authority projection | `AuthenticatedHumanPrincipal` (§19) | §16 step 12 (unchanged numbering; content elaborated) | Not a schema field (validator-internal evidence) | `human_authority_binding` (ref+digest, unchanged) | Gate 5 output |

## 75. Trust-chain matrix

| Stage | Input | Trust root | Validation | Output |
|---|---|---|---|---|
| Principal enrollment | Human, local machine control | Physical/local bootstrap trust anchor (§9) | Fresh election evidence (HPAC-REQ-028) | `PrincipalRecord` |
| Credential enrollment | Enrolled principal + physical hardware | Bootstrap-established principal + hardware ceremony | `enroll_credential` precondition: principal `active` (HPAC-REQ-027) | `CredentialRecord` |
| Challenge construction | Approval subject (RIHAC-001 §5) + fresh nonce | Trusted PCAE coordinator | Domain tag + digest binding (HPAC-001 §15/§16) | Bound challenge |
| Proof production | Enrolled credential + challenge + physical presence gesture | `HumanAuthenticator` (HPAC-001 §10) | UP required (HPAC-REQ-042) | `HumanAuthenticationProof` |
| Proof verification | Proof + registry lookup | `ApprovalAuthorityValidator` (RIHAC-001 v1.1 §16, HPAC-001 §18) | Ten-step sequence (§18) | `AuthenticatedHumanPrincipal` |
| Approval creation | Verified principal + approval facts | Trusted coordinator (RIHAC-001 gate 3) | RIASC-001 v2.0 schema + RIHAC-001 §12 seven-condition conjunction | `RuntimeInvocationApproval` |
| PB evaluation | Validated-authority reference | PB (unchanged) | PBRD-001 §7-§9 | ALLOW/DENY/HUMAN_REVIEW |

## 76. Threat matrix

| Threat | Contract defense | Remaining dependency |
|---|---|---|
| Caller-supplied human ID | `approver_id`/`identity_evidence_kind` retired; only HPAC-001-verified `principal_id` accepted (§41) | Implementation must actually enforce this — not built here |
| Same-user autonomous agent | UP-required hardware mechanism (§12/§30); RIHAC-001 v1.1 §3 normative threat text | HHCE-REQ-060's provider-backend gap must close before real enrollment |
| Copied approval | RIHAC-001 §7/§15/§18 subject/repo/task binding (unaffected, pre-existing) | None new |
| Copied proof | HPAC-001 §24 replay protection (subject binding + nonce consumption) | Durable nonce-consumption store, not yet implemented |
| Copied registry | Atomic write + read-back verification + closed schema (HPAC-001 §5) | Registry writer, not yet implemented |
| Malicious repository | Registry path outside repo control; no repo-reachable enrollment path (§61) | None new — structural |
| Replay | HPAC-001 §24 (nonce) + RIASC-001 v2.0 subject binding | Same as "copied proof" |
| Credential theft | Revocation (HPAC-001 §21) + presence-gated hardware (theft of key alone insufficient without physical touch) | Revocation writer, not yet implemented |
| Fake authenticator | Closed `mechanism_id` allowlist (mirrors HPSE-REQ-018/019 pattern) | Allowlist enforcement, not yet implemented |
| Weaker-mechanism downgrade | HPAC-REQ-060 minimum assurance is contract-fixed, not repo/caller-configurable | Enforcement in a future verifier implementation |

## 77. Contract evolution matrix

See §4 above (full table, reproduced there per governing-prompt item 77's
required placement — duplicated here for cross-reference completeness):
RIHAC-001 1.0→1.1, RIASC-001 1.0→2.0, HPAC-001 (new)→1.0, PBRD-001/
RDGO-001/RPAC-001 unchanged.

## 78. B1/B7/N1/N2 closure roadmap

See §67 above (full table).

## 79. Implementation plan sequencing

See §68 above.

## 80. No production changes

See §69 above.

## 81. No hardware interaction

See §70 above.

## 82. No-Go

See §71 above.

## 83. Final verdict

```text
RUNTIME INVOCATION HUMAN-PRINCIPAL AUTHENTICATION CONTRACTS:
FROZEN

N2:
CONTRACT GAP CLOSED

HUMAN PRINCIPAL:
STABLE / AUTHENTICATED / NON-CALLER-MANUFACTURABLE

PRIMARY V1 AUTHENTICATION:
FIDO2 HARDWARE-BACKED USER-PRESENCE (hpac.fido2.presence_gated.v1; UP
required, UV deployment-configurable)

SAME-USER AGENT RESISTANCE:
MANDATORY / CONTRACTED (RIHAC-001 v1.1 §3, HPAC-001 §0/§34)

RIHAC:
v1.1

RIASC:
v2.0

HUMAN AUTHENTICATION COMPANION CONTRACT:
HPAC-001 v1.0, FROZEN

CALLER-SUPPLIED HUMAN IDENTITY:
NON-AUTHORITY

CANONICAL STORE:
NECESSARY BUT NOT SUFFICIENT

B1/B7/N1/N2:
READY FOR LATER IMPLEMENTATION REPAIR

POL-005:
UNCHANGED

HARDWARE:
NOT TOUCHED

RUNTIME:
Observed / observe / unavailable

EXECUTION:
NOT ACTIVATED

NEXT:
INDEPENDENT VERIFICATION OF HUMAN-PRINCIPAL AUTHENTICATION CONTRACT FREEZE
(149O.20L.7O.3W.1R.2B.1 or equivalent)

HUMAN DECISION:
REQUIRED
```

## Recommended next phase

Independent verification of this contract freeze (149O.20L.7O.3W.1R.2B.1
or equivalent), per §68. **Not begun in this phase. Requires human
authorization.**

## Human decision required

**YES.** Stop after 3W.1R.2B. Production source modified: **NO**. Test
files modified: **NO**. Hardware touched: **NO**. Execution activated:
**NO**. Release changed: **NO**. Runtime: `Observed` / `observe` /
`unavailable`, unchanged. Article remains stopped; private research
repository remains untouched, out of scope.
