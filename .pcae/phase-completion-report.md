# Phase 149O.20L.7O.3W.1R.2B.1 — Independent Verification of Runtime Invocation Human-Principal Authentication Contract Freeze

## Objective

Independently determine whether the frozen RIHAC-001 v1.1 + RIASC-001 v2.0
+ HPAC-001 v1.0 contract system defines a trustworthy,
non-caller-manufacturable human-principal authentication chain for a future
`RuntimeInvocationApproval`, under the mandatory threat that an autonomous
coding agent runs under the same OS account as the human operator.

**Verdict: NOT VERIFIED.** The freeze has useful positive structure, but seven
BLOCKING findings prevent certification and leave N2 open at the contract
layer. No implementation repair was attempted.

## Independence

This phase reconstructed the normative artifacts and fixed-history delta
directly. The 3W.1R.2B report was used only to locate the freeze commit and
candidate artifacts, never as proof of their correctness. Historical v1.0
text came from fixed git object `ca09ab39befc24bd68d510337224daabc6ab32c8`;
the freeze was independently diffed at
`f2894044206185160f9de08d0598516273ce7b63`. Fresh tests were written without
importing a 3W.1R.2B test suite (none existed). No subagent, private research,
article material, hardware, provider, runtime, or network source was used.

## Baseline

| Fact | Verification result |
|---|---|
| Verification-entry SHA | `1991726db1db1504c9ad7e98b321b1dc3859fab7` |
| `origin/main` at entry | same SHA |
| `origin/main..HEAD` at entry | `0` |
| Working tree at entry | clean |
| Release tag | `v0.4.3` -> `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime | `Observed` / `observe` / `unavailable` |
| Runtime registry | 0 plugins / 0 capabilities |
| PB real execution | POL-005 hard DENY |
| `pcae health` / `pcae check` / coherence | healthy / passed / coherent |
| Task memory | historical `tasks/DONE.md` sync warnings only |

## Frozen artifacts

| Contract | Active identity | SHA-256 |
|---|---|---|
| `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` | HPAC-001 v1.0 | `7a2792f4a825f4d3c90425f43f557babc8f991c9a4f4efe5970601a7ae09bc1b` |
| `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` | RIHAC-001 v1.1 | `35365049fd4dd7a4b381f93173c56711a9b540915f06c3ebbb47dcd3e950cc91` |
| `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` | RIASC-001 v2.0 | `af7ba866befab405a7f10b0e8bfceac5e573e9ef0580fe8bb9552e527301b760` |
| `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` | PBRD-001 v1.1 | `28883a5627234b5dfafe3d646f07ed9674a35fbecee0a0bb19e17803d91dbf7d` |
| `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` | RDGO-001 v2.0 | `9e347e01604b5c9e519979475c7c99cb32603165169568f98170f3ed27229ff1` |
| `RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` | RPAC-001 v1.0 | `395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89` |

Historical RIHAC-001 v1.0 and RIASC-001 v1.0 are unambiguously recoverable
from `ca09ab39`. HPAC-001 did not exist before the freeze.

## Freeze delta

The freeze changed exactly three contract files and no production or test
file:

1. added HPAC-001 v1.0 (827 lines, HPAC-REQ-001 through HPAC-REQ-087);
2. amended RIHAC identity/header, §3 authority provenance, §12 trust
   conjunction, §14 revocation, §16 validation step 4, §21 version rationale,
   §22 boundary, and §23 verdict; and
3. amended RIASC identity/header, §1 IDs/versions, §7 provenance semantics,
   the normative JSON schema, §11 cross-field validation, and §14 verdict.

PBRD-001, RDGO-001, and RPAC-001 were byte-identical across the freeze.

## RIHAC version

**Verdict: CONTRACT-VERSION DEFECT (MUST-FIX).** The v1.0 rule explicitly
said no cryptographic signature was required. v1.1 retires that rule and
requires a cryptographic assertion, registry lookup, canonical proof
resolution, replay check, and a new HPAC dependency. A v1.0 implementation
cannot satisfy v1.1 without behavior and data-model changes. RIHAC's own §21
says semantic redefinition requires a new MAJOR; “semantic contract, not a
schema” does not make a mandatory authority-semantic redefinition compatible.
Existing artifacts remain interpreted under their declared v1.0 version, but
that version-qualified preservation does not make an implementation of v1.0
forward-compatible with v1.1.

## RIASC version

**Verdict: VERIFIED.** v2.0 is justified. It retires required
`approver_id`/`identity_evidence_kind` and replaces their meaning with
`principal_id`/`authentication_mechanism_id` plus new `credential_id` and
`authentication_proof_ref`. This is a required-field removal and meaning
change under RIASC's own version rule, so MAJOR is correct.

## HPAC scope

HPAC correctly owns principal identity, registry, enrollment, authenticator
mechanisms, challenge/proof production and verification, revocation,
assurance, and authentication failure behavior. It correctly excludes PB
permission, target selection, Runtime Enforcement policy, process dispatch,
and result acceptance. No scope-collapse finding was found.

## Principal identity

`principal_id` is opaque, stable, non-display, registry-unique, and distinct
from display name, email, OS username/UID, Git identity, agent/session ID,
producer identity, runtime identity, and process identity. Descriptive fields
cannot substitute for it. The schema permits multiple credentials per
principal and does not introduce roles/RBAC.

## Registry scope

The intended scope is deployment/user-level, physically and logically
separate from repository `.pcae` state and from HATP `registry.json`. That
scope decision is sensible, but location outside the repository is not by
itself a trust boundary against a process running as the same user.

## Repository isolation

HPAC says repository configuration cannot choose the registry, mechanism,
enrolled credential set, or minimum assurance. This is the right policy
direction. It does not freeze the OS-enforced ownership, ACL, immutable
configuration-resolution, ancestor-directory, symlink, delete/replace, or
separate-principal controls needed to make the direction true under its own
same-user threat.

## Registry trust

**BLOCKING B-1.** The trust root is narrated, not structurally terminated.
HPAC-REQ-022 relies on an out-of-repository path; HPAC-REQ-023 relies on “the
human who physically controls the deployment machine”; HPAC-REQ-024 calls the
writer “non-agent-invocable.” Under the frozen threat, the agent uses the same
OS account as that human. No contract requirement prevents that process from
invoking the standalone tool, replacing/deleting the user-level store,
weakening permissions, redirecting deployment configuration, or writing a
new principal/credential mapping.

The cited HATP precedent does not support HPAC's conclusion: HATP-REQ-026–035
requires a separate OS-enforced Human/Admin security context, protected
ownership/ACL/path resolution, and declares same-user deployment NOT READY.
HPAC selected the surface pattern but omitted the trust-boundary properties
that make HATP's pattern resistant.

## First-principal bootstrap

**BLOCKING B-1 (same root cause).** The first-principal rule is not a
non-circular trusted ceremony. The contract asserts local physical control,
then requires a fresh election-evidence reference that its own writer never
cryptographically verifies. It defines no protected bootstrap authority
record, externally authenticated admin principal, OS-separated writer
principal, or equivalent mechanism. “No prior PCAE principal exists” explains
why an external root is necessary; it does not define that root.

## Enrollment authority

Additional principal/credential enrollment, replacement, and revocation all
require fresh election evidence and prohibit self-enrollment in prose. Because
the evidence is reference-only and the writer/store/configuration are not
protected from the same-user agent, the enforcement source is forgeable.

## Same-user-agent threat

**NOT COVERED.** The threat is stated exactly and ordinary OS/CLI identity is
rejected, but registry/configuration/enrollment protection and informed-intent
proof do not survive the threat.

## OS/CLI insufficiency

The contracts correctly reject username, UID, environment, filesystem
ownership, Git identity, and ordinary CLI stdin as authentication evidence.
However, `interactive_local_cli_confirmation` remains only a const field plus
a semantic assertion; no independent non-forgeable confirmation evidence is
defined.

## FIDO2 mechanism

The primary ID is `hpac.fido2.presence_gated.v1`. It is hardware-backed,
offline, requires UP, verifies a signed assertion against an enrolled public
key, and binds a fresh challenge. This is a contract descriptor only; no
implementation or hardware claim was made.

## UP

UP proves a physical/user-presence gesture at the authenticator for the
assertion. It does not by itself prove which person touched, that the person
read the approval preview, or that the person intended the hidden semantic
subject.

## UV

UV is deployment-configurable and may be disabled. The deployment-level
administrator is intended to control it, but that configuration authority is
not protected from the same-user agent by B-1. No secure default is frozen.

## UP-vs-principal assurance

**BLOCKING B-2.** The proof chain is credential signature + UP + registry
mapping -> named `principal_id`. HPAC itself concedes UV is what binds the
gesture to a specific enrolled human rather than “someone touched it.” It
freezes no exclusive-custody/non-sharing requirement. Calling the output
`AuthenticatedHumanPrincipal` therefore overclaims named-person assurance
when UV is disabled; at most it proves presence of someone controlling the
credential mapped to that principal.

## Blind-touch risk

**BLOCKING B-3.** A same-user agent can initiate the exact challenge, answer
ordinary CLI confirmation, and ask the human to touch a security key under a
false pretext. The FIDO2 assertion binds an opaque digest but does not present
repository/task/target/prompt semantics on a trusted display. The schema has
no `confirmation_proof_ref`, trusted-display evidence, or other independently
verifiable proof that the human reviewed the preview. Consequently the only
non-caller-forgeable act—touch—can be blind and is effectively treated as
approval despite HPAC-REQ-046 saying touch alone grants no authority.

## Approval-intent binding

The challenge cryptographically binds the full approval-preview digest, which
is positive. What is missing is trustworthy human comprehension/election:
digest binding proves what the authenticator signed, not what the human saw or
intended. RIHAC/RDGO's “present the exact preview” prose has no evidence source
the validator can distinguish from agent-driven stdin.

## Domain separation

The HPAC namespace `hpac.runtime_invocation_approval.v1` is distinct from
HATP, publication, Class-B, and other approvals. Registries, principal-ID
spaces, credential IDs, and challenge domains are separate. Cross-enrollment
of the same physical key is allowed, but each domain has a separate record
and identifier. This part verifies at the textual contract level.

## Challenge subject

The challenge binds `principal_id`, approval-preview digest, nonce, and HPAC
domain. The preview transitively binds invocation ID, target, prompt hash,
repository identity, task ID, and approval scope. No authority-critical
subject field was found missing from the preview binding.

## Nonce/replay

Fresh cryptographically random, non-repeating, expiring nonces and atomic
checked-under-lock consumption are required. Invocation/repository/task/
target/prompt cross-replay and HATP/HPAC cross-domain replay are textually
rejected. A separate lifecycle contradiction is described below.

## Proof structure/schema

**BLOCKING B-4.** HPAC lists exactly eight proof fields but freezes no
normative JSON schema, schema ID/version, canonical byte representation,
canonical proof-store path, proof-store trust/uniqueness rules, or reference
resolution algorithm. RIHAC nevertheless requires loading from “HPAC-001's
canonical proof store.” RIHAC requires `challenge_subject`, a field HPAC's
proof does not define. RIASC prose calls the proof reference
`(proof_id, proof_digest)`, while its normative `artifact_ref` schema requires
`(artifact_id, artifact_digest)`. Two conforming implementers can therefore
produce incompatible proof stores/references, and canonical caller-resistant
resolution is not frozen.

## Verification sequence

The ten-step sequence is: active principal; active credential bound to it;
known mechanism meeting assurance; challenge digest; subject binding;
assertion verification; UP/UV policy flags; time freshness; nonce replay;
trusted result construction. The sequence is fail-closed and ordered, but its
storage and lifecycle inputs are incomplete/contradictory.

## Authenticated principal handle

HPAC explicitly requires trusted construction only as the return of the full
verifier. Parsing or deserializing proof material does not yield a trusted
principal; current registry state must be rechecked.

## Anti-forgery

The contract correctly forbids public digests, booleans, shared sentinels,
caller-copyable fields, and direct construction as the sole trust seal. That
would prevent the B1/B7 copyable-seal defect class if the verifier's own
registry/configuration roots were trustworthy. B-1 prevents that conclusion
for the full system.

## Credential mapping

`credential_id -> principal_id` must come from the active canonical registry,
never the caller. Multiple credentials per principal are permitted; rotation
is enroll-new then revoke-old. The mapping is only as trustworthy as B-1's
unresolved registry root.

## Revocation

**BLOCKING B-5.** Registry revocation blocks new proof verification and
invalidates outstanding challenges, but HPAC-REQ-063/RIHAC §14 explicitly
preserve an already gate-5-validated, still-unconsumed approval after its
principal/credential is revoked. That approval can reach gate 9 and dispatch
without a current active principal/credential check. This contradicts the
required “proof reused after credential revocation fails” scenario and the
claim that every consumption re-runs current registry validation.

Recovery requires credential revocation and trusted enrollment of a
replacement, or repeat bootstrap after total principal loss. B-1 makes both
administrative paths untrusted as currently frozen.

## Enrollment threat model

The same-user agent can target the unprotected admin writer/store/config. It
can inject a principal or credential mapping or select a mechanism/config it
controls. The contract's self-enrollment prohibition has no independent
enforcement boundary. This independently reproduces B-1.

## Configuration authority

Repository configuration is prohibited from setting registry location,
mechanism, UV, or assurance. Deployment/user admin configuration owns them.
No protected resolution path, ownership/ACL model, immutable allowlist, or
separate principal is specified, so “deployment-level” does not mean
“agent-unwritable” under the same-user threat.

## Assurance level

The enum is `ASSERTED`, `PRESENCE_GATED`, and
`HARDWARE_BACKED_PRESENCE_GATED`; the real local-CLI minimum is only
`PRESENCE_GATED`. `ASSERTED` correctly never qualifies. The lower software
alternative is underdefined and inherits B-1/B-2: an OS-mediated presence
gate is secure only if its trusted UI, secret/biometric handling, and config
root are independently protected from the same-user agent.

## Mechanism fallback

No automatic fallback exists. FIDO2 unavailable means failure unless an
explicit deployment-selected mechanism meeting the minimum is configured.
There is no fallback to approver strings, OS username, ordinary confirmation,
CHGR, agent identity, or HATP. The explicit software alternative remains
blocked by the missing trust/UI contract above.

## HATP separation

Option B is structurally clear: low-level FIDO2 verification libraries,
COSE/public-key parsing, resolver patterns, and atomic-store idioms may be
reused; registry, principal namespace, challenge namespace, credential ID,
and authority semantics may not. HATP proofs cannot satisfy HPAC and vice
versa. The problem is not domain aliasing; it is HPAC's omission of HATP's
load-bearing protected-admin boundary.

## Credential reuse

The same physical credential may be cross-enrolled, with distinct IDs and
domain-specific challenges. Domain replay remains forbidden. This is
consistent if each domain independently resolves its own registry and
verification context.

## Registry/ID separation

The HPAC registry document, principal namespace, credential IDs, and
challenge namespace are separate from HATP. A HATP principal ID never
automatically becomes an HPAC principal ID.

## RIHAC compatibility

RIHAC's new proof conjunction points toward HPAC correctly, but is not
compatible as frozen because of B-4/B-5 and the replay lifecycle below.
RIHAC's MINOR selection is also a MUST-FIX version defect.

## RIASC compatibility

RIASC v2.0 has the correct top-level and provenance cardinality and a valid
Draft 2020-12 schema. It can carry IDs/digests needed by HPAC, but B-4's
reference-name and missing proof-store/schema contract make the composition
incomplete.

## RIASC cardinality

| Version | Top-level required | Subject | Provenance required |
|---|---:|---:|---:|
| v1.0 | 16 | 5 | 5 |
| v2.0 | 16 | 5 | 7 |

v1.0 provenance retired `approver_id` and `identity_evidence_kind`; v2.0
adds `principal_id`, `authentication_mechanism_id`, `credential_id`, and
`authentication_proof_ref`, retaining three fields.

## Subject-vs-provenance

The five invocation facts remain approval subject. Principal, mechanism,
credential, proof reference, approval mechanism, preview digest, and producer
are provenance. No accidental subject expansion occurred.

## PBRD compatibility

PB appropriately receives only approval ID/digest plus a validator-owned
evidence projection digest; it needs no raw FIDO2 material. **BLOCKING B-6:**
PBRD's normative header still pins RIHAC-001 v1.0, so the active contract
graph permits the insecure pre-HPAC authority version rather than requiring
the new conjunction.

## RDGO compatibility

The eleven-gate count and order can conceptually accommodate authentication
inside gates 3/5 without adding a gate. **BLOCKING B-6:** RDGO's normative
header still pins RIHAC-001 v1.0 and RIASC-001 v1.0. The active version graph
is therefore not unambiguous.

**BLOCKING B-7:** HPAC consumes the challenge/nonce atomically when gate 5
verification succeeds. RIHAC consumes the approval only at gate 9 and
requires full approval revalidation after restart/drift before gate 9; RDGO
likewise permits the same unconsumed approval only after full revalidation.
HPAC-REQ-058 requires every consumption to re-run verification, but the
second gate-5 pass must reject the already-consumed nonce as replay. Skipping
the proof check violates HPAC/RIHAC; performing it makes the required resume
path impossible. The contracts do not define a coherent lifecycle.

## RPAC compatibility

RPAC remains provider-neutral and preserves approval before preflight,
explicit target, one-shot request identity, PB/RE separation, and HATP
non-reinterpretation. No RPAC schema/gate amendment is required for the
authentication evidence itself. Its consumers must, however, pin the repaired
authority contract set after B-6 is resolved.

## N2 closure

**N2 CONTRACT GAP: OPEN / NOT CLOSED.** A caller-supplied plausible RIASC
v2 object alone is correctly insufficient. But the same-user agent can still
control the unfrozen registry/config/bootstrap boundary (B-1), obtain a blind
touch without informed approval evidence (B-3), and exploit underdefined
proof resolution (B-4). Therefore the frozen chain does not make human
confirmation provenance unequivocally non-caller-manufacturable.

The mandatory scenario—legitimate-looking principal/mechanism/credential/
caller-created proof reference without valid protected HPAC verification—has
no trusted approval under the intended prose, but the inputs needed to decide
“protected/canonical/valid” are not themselves frozen safely enough to make
that result implementable.

## B1/B7/N1 enabling conditions

| Finding | Contract-level status | Future implementation requirement |
|---|---|---|
| B1 copyable trusted seals | Partially enabling; anti-forgery text is good, but verifier root untrusted | Opaque verifier-produced handle backed by protected registry/config and fresh revalidation; never a copyable field/sentinel |
| B7 registry bypass | Still open in implementation; HPAC does not repair attempt identity registry | Independently resolve canonical attempt identity and canonical HPAC principal/credential state |
| N1 bare approval accepted | Still open in implementation | Canonical approval-store resolution in addition to canonical proof-store/registry resolution |
| N2 caller-manufacturable human provenance | Contract gap remains open | Repair B-1 through B-7, then implement and independently verify |

## Full trust conjunction

The intended conjunction is:

```text
RIASC structural validity
+ exact subject/scope/context binding
+ canonical approval-store resolution and digest
+ current freshness/expiry/one-shot state
+ protected HumanPrincipalRegistry resolution
+ canonical proof-store resolution
+ current HPAC assertion/UP/UV/nonce/subject verification
+ trusted-construction-only authority projection
-> eligible human authority evidence (not PB/RE/process permission)
```

The freeze text contains most terms, but “protected registry/configuration,”
canonical proof-store semantics, informed human intent, coherent replay
consumption, current revocation, and consistent companion versions are absent
or contradictory.

## Replay scenarios

| Scenario | Required | Contract result | Verdict |
|---|---|---|---|
| proof -> different invocation | fail | preview/subject digest mismatch | PASS |
| proof -> different repository | fail | subject digest mismatch | PASS |
| proof -> different task | fail | subject digest mismatch | PASS |
| proof -> different target | fail | subject digest mismatch | PASS |
| proof after nonce expiry | fail | freshness step | PASS |
| proof after credential revocation, not previously validated | fail | live registry check | PASS |
| already-validated approval after credential revocation | fail required | explicitly remains valid | **BLOCKING B-5** |
| HATP proof -> HPAC | fail | registry/domain/namespace separation | PASS |
| HPAC proof -> HATP | fail | registry/domain/namespace separation | PASS |
| pre-gate-9 approval revalidation | coherent fresh validation required | nonce already consumed at first gate 5 | **BLOCKING B-7** |

## Malicious repository scenarios

| Scenario | Required result | Frozen result | Verdict |
|---|---|---|---|
| repo supplies fake registry | cannot influence trusted path | repository path prohibited, but same-user store/config unprotected | BLOCKING B-1 |
| repo changes authenticator config | cannot lower | prohibited in prose; protected resolution absent | BLOCKING B-1 |
| repo lowers UV/assurance | cannot lower | contract minimum fixed, config root unprotected | BLOCKING B-1/B-2 |
| repo injects credential mapping | cannot write registry | no same-user-resistant ownership/ACL boundary | BLOCKING B-1 |
| repo generates fake proof ref | canonical trusted resolution must reject | canonical store/path/schema missing | BLOCKING B-4 |

## Audit/privacy

Audit excludes PINs, private keys, raw biometric templates, raw challenges,
and unnecessary personal data. It records opaque principal/credential/
challenge references, result, time, and verifier version. This is adequate at
the contract level subject to defining the missing canonical stores.

## Offline/portability

Primary FIDO2 verification is local/offline and platform-neutral across macOS
and Linux. No API/provider/network path is made ready. Network egress,
credentials for runtime providers, Shell Gate, and Runtime Enforcement remain
unresolved and unavailable.

## Delegated-agent separation

Agent/delegated-agent identity is explicitly distinct from a human principal;
no parent-context or delegation authority inheritance exists. “Not delegated”
is never evidence of humanity.

## Session caching

No authentication caching exists in v1; every invocation requires a fresh
challenge and proof. The gate-5/gate-9 contradiction is not caching—it is an
inconsistent placement of proof and approval consumption.

## Contract versions

| Contract | Claimed active | Verification |
|---|---|---|
| RIHAC-001 | 1.1 | NOT VERIFIED; version defect + cross-contract blockers |
| RIASC-001 | 2.0 | schema/version delta VERIFIED; composition NOT VERIFIED |
| HPAC-001 | 1.0 | NOT VERIFIED |
| PBRD-001 | 1.1 | content unchanged; stale RIHAC reference |
| RDGO-001 | 2.0 | content unchanged; stale RIHAC/RIASC references + replay contradiction |
| RPAC-001 | 1.0 | unchanged and compatible in scope/order |

## Static verification

Fresh suite:
`tests/test_runtime_human_principal_contract_freeze_verification_3w1r2b1.py`.
It validates fixed-history deltas, active/historical versions, RIASC Draft
2020-12 shape, 16/5/5->7 cardinality, missing/unknown fields, exact HPAC
requirement sequence, identity/domain/replay invariants, HATP separation,
trust-root omissions, blind-touch/UP limitations, proof-store/reference
contradictions, revocation, gate-5/gate-9 lifecycle, companion versions, and
unchanged production v1 implementation. Result: **39 passed**.

## Findings

### BLOCKING

1. **B-1 — Principal registry/bootstrap/configuration trust root is not
   same-user-agent resistant.** Location and “non-agent-invocable” convention
   do not replace protected ownership/ACL/separate-principal enforcement.
2. **B-2 — UP-only overclaims a named authenticated human.** UV is optional
   and no exclusive credential custody is frozen.
3. **B-3 — Blind touch can substitute for informed approval.** No
   non-forgeable confirmation evidence or trusted subject display is bound.
4. **B-4 — Proof schema/store/reference contract is incomplete and
   internally inconsistent.** Canonical resolution cannot be implemented
   uniquely.
5. **B-5 — Revocation does not invalidate an outstanding gate-5-validated,
   unconsumed approval.** Current-principal assurance can go stale before
   dispatch.
6. **B-6 — PBRD/RDGO still normatively pin RIHAC/RIASC v1.0.** The active
   contract graph is ambiguous and permits the insecure predecessor.
7. **B-7 — Proof nonce consumption at gate 5 contradicts mandatory
   pre-gate-9 approval revalidation.** The frozen lifecycle is not
   implementable consistently.

### MUST-FIX

1. **M-1 — RIHAC v1.1 should be a new MAJOR.** The change is mandatory and
   semantically incompatible, not optional evidence or mere clarification.
2. **M-2 — Internal cross-references are stale/mistargeted.** Examples:
   HPAC references nonexistent §39–§41 and mispoints fallback sections;
   RIHAC calls software fallback HPAC §15 although §15 is domain separation.

### NON-BLOCKING

None separately classified. The positive invariants above are retained, but
every identified defect affects authority semantics, implementability, or
the active version graph.

### OBSERVATION

The normative schema intentionally accepts syntactically plausible
principal/credential/proof IDs; only cross-field verification can confer
trust. This is correct and should remain true after repair.

### DEFERRED-IMPLEMENTATION

B1, B7, N1, and N2 implementation repair; executable HPAC/RIASC schema;
registry/proof stores; authenticators; enrollment; PB/RE/Shell Gate; POL-005
evolution; runtime activation; network/provider credentials. None is
authorized here.

## Required matrices

### Matrix A — Principal trust

| Stage | Authority source | Trust proof | Caller forgeable? | Verdict |
|---|---|---|---|---|
| principal ID allocation | bootstrap admin | asserted local ceremony | yes under same-user root | BLOCKING |
| credential enrollment | admin writer + election ref | unverified ref + registry write | yes under same-user root | BLOCKING |
| challenge | trusted coordinator | nonce + preview digest + domain | no if coordinator/config trusted | CONDITIONAL |
| assertion | enrolled credential | signature + UP (+ optional UV) | not without gesture; blind touch possible | BLOCKING intent |
| verification | approval validator | ten-step conjunction | inputs/stores underdefined | BLOCKING |
| authority projection | validator-only handle | successful current verification | structurally non-copyable by contract | PASS conditional on prior stages |

### Matrix B — FIDO2 assurance

| Property | Required/optional | What it proves | Threat covered |
|---|---|---|---|
| cryptographic assertion | required | enrolled key signed challenge | proof integrity if registry trusted |
| UP | required | someone physically interacted with authenticator | unattended agent cannot touch directly |
| UV | optional | authenticator verified a user via PIN/biometric | named-user distinction when enabled |
| trusted semantic display | absent | would prove informed subject review | blind-touch threat not covered |
| exclusive credential custody | absent | would support principal mapping under UP-only | shared-touch threat not covered |

### Matrix C — Cross-domain separation

| Domain | Registry | Principal namespace | Challenge namespace | Credential reuse | Replay possible? |
|---|---|---|---|---|---|
| HPAC runtime approval | separate `HumanPrincipalRegistry` | HPAC-local | `hpac.runtime_invocation_approval.v1` | physical key may be cross-enrolled; distinct ID | no by contract |
| HATP rollback/signing | HATP `registry.json` + hardware store | HATP-local | HATP operation/binding domain | same physical key possible | no by contract |
| publication/CHGR | separate authority family | separate | separate | not an HPAC mechanism | no structural substitution |

### Matrix D — Authentication proof

| Field | Source | Trust before verification | Validation |
|---|---|---|---|
| `proof_id` | proof producer/store | untrusted | canonical uniqueness not frozen (B-4) |
| `mechanism_id` | mechanism result | untrusted | resolve trusted descriptor + assurance |
| `principal_id` | claimed result | untrusted | active registry lookup |
| `credential_id` | claimed result | untrusted | active mapping under principal |
| `challenge_digest` | producer | untrusted | recompute from exact trusted challenge |
| `assertion` | authenticator | untrusted | cryptographic verification + flags |
| `authenticated_at` | producer/authenticator | untrusted | trusted-clock freshness |
| `verifier_version` | producer | untrusted | supported verifier version; rule underdefined |

### Matrix E — Contract compatibility

| Concept | HPAC | RIHAC 1.1 | RIASC 2.0 | PBRD | RDGO | Consistent? |
|---|---|---|---|---|---|---|
| principal/proof provenance | owner | required | represented | projection only | gate 5 | partial |
| canonical approval store | no ownership | required | path frozen | reference | gate 5 | yes |
| canonical proof store | mentions only | assumes | reference only | opaque | gate 5 | **no** |
| proof replay | consume on verify | reject replay | cross-check | opaque | revalidate before gate 9 | **no** |
| revocation | validated approval survives | same | not represented | opaque | no late recheck | **no** |
| active versions | 1.0 | 1.1 | 2.0 | pins RIHAC 1.0 | pins RIHAC/RIASC 1.0 | **no** |

### Matrix F — Threat verification

| Threat | Required result | Contract mechanism | Verdict |
|---|---|---|---|
| caller strings only | no authority | proof conjunction | PASS in intended prose |
| same-user registry/config tamper | impossible | location/convention only | BLOCKING B-1 |
| self-enrollment | denied | election prose, unverified ref | BLOCKING B-1 |
| blind touch | no informed approval | digest binding, no trusted display evidence | BLOCKING B-3 |
| wrong human touches UP-only key | not named principal | registry mapping, UV optional | BLOCKING B-2 |
| proof cross-invocation/repo/task/target | reject | preview digest | PASS |
| HATP/HPAC replay | reject | domain/registry/ID separation | PASS |
| proof reference fabrication | canonical reject | store/path/schema missing | BLOCKING B-4 |
| revocation before dispatch | reject | only new validations reject | BLOCKING B-5 |

### Matrix G — Open findings

| Finding | Contract-level status | Future implementation requirement |
|---|---|---|
| B1 | enabling text only; still open | trusted-construction handle + protected roots |
| B7 | unaffected/open | durable attempt-identity re-resolution |
| N1 | unaffected/open | canonical approval-store lookup |
| N2 | **OPEN** | repair seven contract blockers before planning implementation |

## Freeze verdict

```text
HUMAN-PRINCIPAL AUTHENTICATION CONTRACT FREEZE: NOT VERIFIED
RIHAC-001 v1.1: NOT VERIFIED (MUST-FIX VERSION DEFECT)
RIASC-001 v2.0: VERSION/SCHEMA DELTA VERIFIED; SYSTEM COMPOSITION NOT VERIFIED
HPAC-001 v1.0: NOT VERIFIED
N2 CONTRACT GAP: OPEN
SAME-USER AGENT THREAT: NOT COVERED
HUMAN PRINCIPAL TRUST ROOT: NOT SUFFICIENTLY DEFINED
FIRST-PRINCIPAL ENROLLMENT: NOT TRUSTED / NOT NON-CIRCULAR ENOUGH
HPAC PROOF: NOT IMPLEMENTABLY NON-CALLER-MANUFACTURABLE
HATP: SEPARATE AUTHORITY DOMAIN (VERIFIED)
NEW BLOCKING: 7
```

## Implementation readiness

**HUMAN-PRINCIPAL AUTHENTICATION CONTRACTS — IMPLEMENTATION READY: NO.**
An implementation phase must not begin against the current freeze.

## Current authority-foundation status

```text
B1: OPEN
B7: OPEN
N1: OPEN
N2: CONTRACT GAP OPEN; IMPLEMENTATION REPAIR NOT PERFORMED
AUTHORITY/PB FOUNDATION: NOT VERIFIED
READY FOR RUNTIME ENFORCEMENT: NO
REAL EXECUTION: UNAVAILABLE
```

## Recommendation

Recommend exactly one next phase, not begun:

**149O.20L.7O.3W.1R.2B.1R — Runtime Invocation Human-Principal
Authentication Contract Freeze Blocking Repair.**

That phase should repair only B-1 through B-7 and M-1/M-2: freeze a real
same-user-resistant registry/config/bootstrap trust root; bind informed
approval to a trustworthy human-visible ceremony; state honest UP/UV
principal assurance; freeze proof schema/store/reference resolution; make
revocation current at dispatch; reconcile PBRD/RDGO version references; and
choose coherent proof/approval consumption semantics. It must remain
contract-only, then undergo a fresh independent verification before any
implementation-planning phase.

## Human decision required

Stop after this verification. Do not begin repair or implementation without
new human authorization.

## Canonical phase-report facts

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1`
- **Status:** complete — NOT VERIFIED
- **Completeness:** complete
- **Verification-entry SHA:** `1991726db1db1504c9ad7e98b321b1dc3859fab7`
- **v0.4.3:** unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6`
- **Runtime:** `Observed` / `observe` / `unavailable`
- **Production source modified:** NO
- **Hardware touched:** NO
- **Execution activated:** NO
- **POL-005:** unchanged hard DENY
- **Article:** stopped and untouched
- **Private research:** untouched
- **Authority/PB foundation:** NOT VERIFIED
- **Tests:** fresh static/adversarial suite, 39 passed
- **Historical-suite attribution:** 126 passed / 8 failed across the older
  3V.1 and 3V.1R.1 contract suites; all eight pin superseded contract or
  inventory state and are classified as historical-suite drift
- **Repository-wide suite limitation:** xdist collection is nondeterministic
  because existing UUID-valued parameter IDs differ by worker; a serial run
  reached 43 passed with no failure before being stopped after 167.88 seconds
- **BLOCKING:** 7
- **MUST-FIX:** 2
- **NON-BLOCKING:** 0
- **Commits/push:** finalized through governed close; see canonical metadata
- **Exact next:** `149O.20L.7O.3W.1R.2B.1R`, contract-repair-only
- **Human decision:** required
