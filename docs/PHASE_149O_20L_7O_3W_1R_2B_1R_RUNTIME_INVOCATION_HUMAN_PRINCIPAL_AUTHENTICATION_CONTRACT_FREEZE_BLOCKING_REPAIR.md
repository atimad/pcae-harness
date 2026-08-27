# Phase 149O.20L.7O.3W.1R.2B.1R — Runtime Invocation Human-Principal Authentication Contract Freeze Blocking Repair

## 1. Objective

Repair exactly the seven BLOCKING and two MUST-FIX findings from the primary
3W.1R.2B.1 independent verification, using only the contract scope authorized
for this phase. The phase reached its mandatory scope-sufficiency gate and
**STOPPED BEFORE CONTRACT EDITS**: B-6 necessarily requires normative changes
to PBRD-001 and RDGO-001, both explicitly outside the allowed repair set.

## 2. Baseline

| Fact | Phase-entry result |
|---|---|
| Entry SHA | `88056f36a2e47d48e3f1467d71c6746ceb378074` |
| `origin/main` | same SHA |
| `origin/main..HEAD` | `0` |
| Working tree | clean |
| Release | `v0.4.3` -> `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime | `Observed` / `observe` / `unavailable` |
| Registry | 0 plugins / 0 capabilities |
| Governance | healthy / check passed / coherent |
| Task memory | historical `tasks/DONE.md` warnings only |
| Push | clean / nothing to push |
| Notification | configured, enabled, outbound-ready |

No private research, article, hardware, provider, credential, runtime, or
network source was accessed.

## 3. Independent-verification verdict

The complete primary artifact was read before any proposed contract change:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1_INDEPENDENT_VERIFICATION_RUNTIME_INVOCATION_HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT_FREEZE.md`.
It contains exactly seven BLOCKING and two MUST-FIX findings. The prior verdict
is `NOT VERIFIED`; N2 remains `CONTRACT GAP OPEN`.

## 4. Nine finding recovery

The following wording is preserved verbatim from the primary artifact.

| ID | Severity | Exact wording | Contract/section | Verification scenario | Unsafe/incorrect result |
|---|---|---|---|---|---|
| B-1 | BLOCKING | **B-1 — Principal registry/bootstrap/configuration trust root is not same-user-agent resistant.** Location and “non-agent-invocable” convention do not replace protected ownership/ACL/separate-principal enforcement. | HPAC §§7–8, §28; HPAC-REQ-022–029 | Same-UID agent invokes writer or replaces/redirects registry/config and enrolls its credential. | Agent-controlled mapping becomes the alleged trust root. |
| B-2 | BLOCKING | **B-2 — UP-only overclaims a named authenticated human.** UV is optional and no exclusive credential custody is frozen. | HPAC §14, §20; HPAC-REQ-040/042/059–060 | Someone other than the mapped natural person touches a shared credential while UV is disabled. | Output is named `AuthenticatedHumanPrincipal` although only credential use plus presence was shown. |
| B-3 | BLOCKING | **B-3 — Blind touch can substitute for informed approval.** No non-forgeable confirmation evidence or trusted subject display is bound. | HPAC §§14–16; RIHAC §3/§12; RIASC §7/§11 | Agent says “touch your key” while its hidden challenge authorizes another repo/task/target/prompt. | A signature over an opaque digest is treated as informed approval. |
| B-4 | BLOCKING | **B-4 — Proof schema/store/reference contract is incomplete and internally inconsistent.** Canonical resolution cannot be implemented uniquely. | HPAC §§17–19; RIHAC §16 step 4; RIASC §7/§10–12 | Implementers choose different proof bytes, paths, keys, and resolution rules; caller supplies plausible reference. | No unique canonical proof or caller-resistant resolution exists. |
| B-5 | BLOCKING | **B-5 — Revocation does not invalidate an outstanding gate-5-validated, unconsumed approval.** Current-principal assurance can go stale before dispatch. | HPAC §21/REQ-063; RIHAC §14 | Credential is revoked after gate 5 but before gate 9. | Approval can proceed without current active principal/credential status. |
| B-6 | BLOCKING | **B-6 — PBRD/RDGO still normatively pin RIHAC/RIASC v1.0.** The active contract graph is ambiguous and permits the insecure predecessor. | PBRD header `Related contracts`; RDGO header `Related contracts` | Consumer selects versions exactly permitted by normative headers. | Pre-HPAC RIHAC/RIASC authority remains contract-permitted. |
| B-7 | BLOCKING | **B-7 — Proof nonce consumption at gate 5 contradicts mandatory pre-gate-9 approval revalidation.** The frozen lifecycle is not implementable consistently. | HPAC §§16/18/19/24; RIHAC §§16–19; RDGO §§6/17–18 | Gate 5 verifies and consumes nonce; restart before gate 9 requires full revalidation. | Revalidation either rejects as replay or improperly skips proof verification. |
| M-1 | MUST-FIX | **M-1 — RIHAC v1.1 should be a new MAJOR.** The change is mandatory and semantically incompatible, not optional evidence or mere clarification. | RIHAC header, §§12/16/21 | A v1.0 implementation/artifact lacks mandatory cryptographic proof and registry dependency. | Incompatible authority semantics are mislabeled as a compatible minor. |
| M-2 | MUST-FIX | **M-2 — Internal cross-references are stale/mistargeted.** Examples: HPAC references nonexistent §39–§41 and mispoints fallback sections; RIHAC calls software fallback HPAC §15 although §15 is domain separation. | HPAC §§1/36–38; RIHAC §§12/22 | Implementer follows cited section to find normative requirements. | Citation is nonexistent or resolves to unrelated semantics. |

Count: **7 BLOCKING + 2 MUST-FIX = 9**, exactly matching the primary report.

## 5. Finding reproduction

- B-1 reproduces from HPAC-REQ-022's location claim, HPAC-REQ-023's physical
  control assumption, HPAC-REQ-024's “non-agent-invocable” label, and
  HPAC-REQ-028's explicitly unverified election reference. None supplies an
  enforcement principal distinct from the same-UID agent.
- B-2 reproduces because HPAC-REQ-042 states UP alone is the minimum and UV
  is optional, while the result is named `AuthenticatedHumanPrincipal`.
- B-3 reproduces because HPAC-REQ-046 binds touch to challenge bytes but no
  trusted presentation receipt or confirmation proof exists in HPAC, RIHAC,
  or RIASC.
- B-4 reproduces from HPAC-REQ-052's prose-only eight fields, RIHAC's
  undefined `challenge_subject`, RIASC prose `(proof_id, proof_digest)`, and
  RIASC schema `artifact_id`/`artifact_digest`.
- B-5 reproduces verbatim from HPAC-REQ-063 and RIHAC §14.
- B-6 reproduces directly from PBRD's `RIHAC-001 v1.0` header pin and RDGO's
  `RIHAC-001 v1.0, RIASC-001 v1.0` header pins.
- B-7 reproduces from HPAC-REQ-050/071 consumption on successful verification
  and RIHAC §19/RDGO §17–18 mandatory full revalidation before gate 9.
- M-1 reproduces because RIHAC v1.1 retires “No cryptographic signature is
  required” and makes cryptographic proof plus registry lookup mandatory.
- M-2 reproduces because HPAC ends at §38, not §41, and HPAC §15 is domain
  separation, not the software fallback named by RIHAC §12.

All reproductions are static contract reads. No authenticator was enumerated,
enrolled, touched, or invoked.

## 6. Root-cause grouping

| Root cause | Findings affected | Contracts requiring change |
|---|---|---|
| Trust is asserted by location/convention rather than an enforced independent root | B-1 | HPAC |
| Presence, credential-bound identity, and intent are collapsed | B-2, B-3 | HPAC, RIHAC; RIASC if a presentation reference is carried |
| Proof persistence and state machine are not normatively modeled | B-4, B-5, B-7 | HPAC, RIHAC, RIASC |
| Active dependency graph was not evolved atomically | B-6 | **PBRD, RDGO**, plus repaired RIHAC/RIASC identities |
| Version/citation hygiene did not follow semantic changes | M-1, M-2 | RIHAC, HPAC, RIASC references as applicable |

## 7. Scope sufficiency

| Finding | Repairable by RIHAC/RIASC/HPAC only? | Result |
|---|---|---|
| B-1 | YES | HPAC can require an OS/equivalent protected administration principal and store/config root. |
| B-2 | YES | HPAC can define honest UP and UV assurance profiles and terminology. |
| B-3 | YES, if HPAC owns a protected approval-intent presentation contract | Freeze presentation evidence and subject binding. |
| B-4 | YES | HPAC can freeze schemas/store/resolution; RIASC can use one exact reference vocabulary. |
| B-5 | YES | HPAC/RIHAC can require current registry validation until gate-9 consumption. |
| B-6 | **NO** | The defective normative text is physically in PBRD and RDGO. |
| B-7 | YES for proof semantics, but RDGO consistency must also be verified | Keep proof bound but unconsumed until gate 9; reverify immutable bytes/current registry without replay-consuming twice. |
| M-1 | YES | RIHAC must become a MAJOR. |
| M-2 | YES | Correct citations in the three core contracts. |

The user's explicit rule states: if PBRD/RDGO/RPAC evolution becomes
necessary, **STOP before editing those contracts and report why the phase
scope is insufficient**. B-6 makes PBRD and RDGO changes logically necessary;
therefore no contract in this phase was edited. Partial repair would leave one
of seven BLOCKING findings open and falsely present an internally inconsistent
freeze.

## 8. RIHAC version repair

Authority valid under RIHAC v1.0 would **not** remain authority-valid under the
authenticated-principal requirements: v1.0 explicitly permits no
cryptographic signature and has no mandatory HPAC registry/proof conjunction.
The repository-correct prospective version is **RIHAC-001 v2.0**, not v1.1.
This determination is complete; the edit is deferred by the STOP.

## 9. RIHAC compatibility

Prospective RIHAC v2.0 must supersede v1.0 and the defective v1.1 freeze.
RIHAC v1.x approvals remain historical evidence only and are **not sufficient
for future real-runtime authority**. There is no silent upgrade or migration:
a v2 approval must be newly created under v2 semantics with a current HPAC
proof. Unknown or v1.x versions fail the v2 authority gate closed.

## 10. RIASC impact

RIASC v2.0's provenance shape was a correctly chosen MAJOR relative to v1.0,
but a repaired schema must change the required `contract_version` constant
from `RIHAC-001/1.1` to `RIHAC-001/2.0` and must resolve proof-reference
semantics. Because existing v2.0 artifacts would fail the new required const
and may need a new presentation/proof reference meaning, the conservative
repository-correct prospective version is **RIASC-001 v3.0**. No edit was
made.

## 11. HPAC version repair

B-1 through B-5/B-7 change load-bearing trust, assurance, proof schema, and
lifecycle semantics. These are not clarifications. The prospective repaired
contract is **HPAC-001 v2.0**, with independently versioned proof and registry
schemas. No edit was made.

## 12. Same-user-agent threat

The normative attacker is an autonomous process under the human's OS account.
UID, username, environment, filesystem ownership, stdin, Git identity, and
agent/session identity are insufficient. A conforming future design requires
an administration/presentation authority the same-UID process cannot invoke,
modify, replace, redirect, downgrade, or convincingly spoof.

## 13. Assurance decomposition

`AUTHENTICATOR USER PRESENCE != AUTHENTICATED PRINCIPAL IDENTITY != INFORMED
APPROVAL INTENT`.

| Property | Evidence | Verifier | Invalidation | Threat addressed |
|---|---|---|---|---|
| User presence | Valid authenticator assertion with UP | HPAC verifier | bad signature, absent UP, stale/wrong challenge | unattended proof production |
| Credential-bound principal identity | active protected-registry mapping plus valid assertion; UV when named-user assurance is claimed | HPAC verifier | mapping/credential/principal revocation, missing required UV | caller-supplied identity and wrong-user gesture |
| Informed approval intent | integrity-protected presentation receipt bound to exact canonical subject and same challenge | HPAC/RIHAC validator | display mismatch, untrusted presenter, missing acknowledgement | blind touch and semantic substitution |

## 14. UP semantics

UP proves only presence-gated use of the enrolled credential for the signed
challenge. It does not prove which natural person touched, that the subject
was understood, or that approval was intended.

## 15. UV semantics

UV proves the authenticator locally verified a user according to FIDO2
semantics. A future contract may distinguish an honest UP-only
`credential_presence` profile from a UV-required `principal_verified`
profile. Registry path, mechanism allowlist, minimum UV policy, and downgrade
floor must be controlled by the protected deployment authority, never repo or
same-UID agent. Whether UP-only may qualify for real runtime must be decided
explicitly; it cannot yield named-person assurance as currently worded.

## 16. Principal identity semantics

The safe exact meaning is “successful current verification of a credential
enrolled to an opaque PCAE `principal_id` under a protected registry and an
assurance profile whose requirements were met.” It is credential-bound PCAE
identity, not biological, civil, or legal identity.

## 17. Informed human intent

Authentication proof must also serve as, or reference, an approval-intent
proof bound to the exact invocation subject. Authentication alone is not
approval. The verifier needs evidence that the protected ceremony presented
the canonical facts and accepted the human's non-defaultable election.

## 18. Human-visible ceremony

The minimum presentation contains repository identity, task ID, runtime
target, prompt/instruction digest and recognizable fingerprint, invocation
ID, effect class/scope, expiry, and one-shot nature. Values originate from
trusted PCAE canonical state, not repository-authored labels.

## 19. Blind-touch attack

“Touch your security key” while signing another subject must fail. UP without
a protected, challenge-bound presentation receipt is insufficient. The human
must acknowledge a independently derived subject fingerprint or trusted
display whose digest is included in the signed challenge.

## 20. Challenge/display binding

The challenge must bind a versioned canonical approval-subject digest and a
versioned presentation digest derived from exactly the visible canonical
facts. Any display/challenge mismatch invalidates the proof.

## 21. Trusted presentation

Ordinary agent-controlled terminal output is not sufficient under this threat.
A future contract must select a protected PCAE TTY/UI running under an
OS-separated authority, an authenticator display, or an out-of-band display;
alternatively it may use an independently derived human-verifiable code only
if the trusted source and comparison ceremony are explicit. No current
component is certified to provide this function.

## 22. Registry trust root

“Outside the repository” is necessary but insufficient. The prospective root
requires an OS/equivalent protected storage and configuration domain owned by
a principal unavailable to ordinary same-UID agent execution, with protected
ancestor/path resolution, no symlink traversal, no delete/replace, atomic
writes, and read-back verification.

## 23. Configuration authority

Only the protected deployment administration authority may set registry path,
mechanism allowlist, credential mapping, assurance/UV floor, proof-store path,
and presentation mechanism. Immutable contract minima cannot be lowered.

## 24. Malicious repo

A repository must be unable to provide an alternate registry/proof store,
change principal mapping, lower assurance, select a weak mechanism, enroll a
credential, replace trust configuration, or supply trusted display labels.

## 25. First-principal bootstrap

The first entry must originate in a non-circular deployment-owner ceremony
outside autonomous-agent execution. It needs an externally established
protected admin execution principal or equivalent protected device/out-of-band
authority; “physical control of the machine” alone is not a verifier.

## 26. Enrollment ceremony

Prospective enrollment requires protected-admin invocation, fresh
non-defaultable presence/verification, exact operation preview, FIDO2
registration, protected atomic registry write, and durable enrollment
provenance that the writer verifies rather than merely records.

## 27. Enrollment attack

A same-UID agent invoking enrollment unattended must be structurally denied.
The ordinary `pcae` CLI cannot expose the mutation. Possession of an agent-
controlled credential plus filesystem write access is never bootstrap
authority.

## 28. Credential registration

The registry needs credential ID, public verification key, principal mapping,
mechanism ID, supported assurance/UV capability, status/timestamps, and
verified enrollment-provenance reference. It stores no private key, PIN, or
biometric secret.

## 29. Domain separation

The signed challenge includes an explicit versioned HPAC runtime-approval
domain distinct from HATP, publication/signing, Class-B, and other approval
domains. Domain is data in the canonical challenge bytes, not prose.

## 30. Replay

HATP→HPAC, HPAC→HATP, invocation A→B, repo A→B, and task A→B all reject due
to domain or exact subject mismatch. A copied proof/reference does not bypass
canonical resolution or current verification.

## 31. Nonce

Nonce is trusted-coordinator-generated, cryptographically random, unique,
expiring, and caller-independent. Prospective lifecycle should mark the proof
`BOUND` to exactly one approval at creation/validation, but mark it consumed
only atomically with gate-9 approval consumption. Revalidation before gate 9
checks identical binding/current state without attempting a second consume.

## 32. Proof lifecycle

Prospective minimal state machine:
`CHALLENGE_CREATED -> ASSERTION_RECEIVED -> PROOF_VERIFIED_AND_BOUND ->
PROOF_CONSUMED_WITH_APPROVAL` or `EXPIRED/REVOKED/REJECTED`. Verification is
repeatable only for the same canonical bytes/binding before gate 9; consumption
is one atomic gate-9 transition.

## 33. Proof anti-forgery

Trust requires canonical proof bytes, digest recomputation, canonical protected
store resolution, protected registry/config resolution, cryptographic
verification, current state, exact subject/presentation binding, and lifecycle
state. A digest, boolean, sentinel, copied field, or caller path is non-authority.

## 34. Trusted-principal anti-forgery

`AuthenticatedHumanPrincipal` is ephemeral verifier output and not
serializable authority. Caller-created lookalikes and deserialized fields are
untrusted; persisted proof must be re-resolved and reverified.

## 35. Session caching

No authentication or approval caching in v1/v2 initial implementation. Every
`RuntimeInvocationApproval` requires a fresh presence-gated, subject-bound
proof and informed-intent ceremony.

## 36. Approval-vs-authentication proof

Authentication proof establishes credential/principal assurance. Approval
proof establishes that the authenticated act covered this exact subject and
presentation. One assertion may carry both only when its challenge binds both
domains/semantics explicitly and the validator verifies both.

## 37. Revocation

Revocation invalidates unused challenges, verified-but-not-materialized
approvals, every unconsumed approval, and its PB projection. Gate-5 and every
pre-gate-9 revalidation must re-check current principal/credential status.
Only gate-9 atomic consumption ends the outstanding state.

## 38. HATP separation

Only low-level parsing/verification and atomic-store concepts may be reused.
HPAC registry, IDs, credential roles, challenge domain, audit, proof store, and
authority semantics remain separate. No implicit principal mapping exists.

## 39. Credential reuse

Prospective policy retains Option 1: the same physical FIDO2 credential may be
registered independently in both domains, with separate records, IDs, roles,
challenge domains, and audits. Cross-domain proof reuse always fails.

## 40. Trust chain

Prospective repaired chain and named validation mechanisms:

```text
protected deployment-owner ceremony
  --protected-admin authentication/authorization-->
protected HumanPrincipalRegistry/config
  --canonical protected resolution-->
canonical approval challenge
  --versioned subject + presentation digest-->
protected human-visible intent presentation
  --non-defaultable acknowledgement + FIDO2 UP/required UV-->
signed assertion
  --signature/domain/nonce/subject/presentation verification-->
canonical bound HPAC proof
  --protected-store resolution + current-registry verification-->
ephemeral authenticated-principal result
  --RIHAC v2 conjunction-->
canonical RuntimeInvocationApproval
  --approval-store resolution + full validation-->
trusted PB projection
```

## 41. N2 closure

N2 is **NOT CLOSED BY THIS STOPPED PHASE**. The prospective design would
close it only when a caller cannot make authority from plausible IDs/refs/
fields without a protected-registry-rooted, exact-subject/presentation-bound,
non-replayable proof. Because B-6 remains open and no contracts changed, the
current status stays `CONTRACT GAP OPEN`.

## 42. B1 closure-enabling

Future PB projection must freshly resolve canonical approval and HPAC proof
through protected roots. A transferable sentinel never qualifies. Contract
repair is not yet frozen.

## 43. B7 closure-enabling

Attempt identity remains PCAE-owned and independently registry/canonical-
state verified. Human proof cannot substitute for dispatch identity ownership.

## 44. N1 closure-enabling

Canonical approval-store provenance remains mandatory in addition to HPAC
proof. An arbitrary in-memory approval remains non-authority.

## 45. Cross-contract consistency

RIHAC/RIASC/HPAC require coordinated major versions. PBRD must pin repaired
RIHAC; RDGO must pin repaired RIHAC/RIASC and express the coherent proof
lifecycle; RPAC requires no semantic change. PB continues to consume only a
validated projection, not FIDO2 material.

## 46. RDGO implications

No twelfth gate is required: presentation/authentication belongs inside
human authority creation and approval validation. The eleven-gate order can
remain. However, RDGO's normative dependencies and pre-gate-9 revalidation
wording must be amended. That is exactly why the current phase stops.

## 47. Security invariants

- caller principal/proof reference -> non-authority;
- valid FIDO2 assertion without protected registry mapping -> non-authority;
- mapping without valid assertion -> non-authority;
- assertion without exact subject/presentation binding -> non-authority;
- UP without informed ceremony -> insufficient;
- repository-controlled trust/display configuration -> invalid;
- agent-driven ordinary CLI confirmation -> insufficient;
- revoked credential or replayed assertion -> non-authority;
- HATP assertion -> invalid for HPAC;
- authenticated principal with wrong invocation -> non-authority; and
- valid approval plus PB DENY -> no dispatch.

## 48. Seven Blocking repairs

### Matrix A — Nine findings

| ID | Severity | Exact finding | Root cause | Contract repair | Verdict |
|---|---|---|---|---|---|
| B-1 | BLOCKING | Principal registry/bootstrap/configuration trust root is not same-user-agent resistant. | Convention-only trust root | Protected admin/store/config requirements in HPAC | NOT APPLIED — STOP |
| B-2 | BLOCKING | UP-only overclaims a named authenticated human. | Assurance collapse | Honest UP/UV profiles and credential-bound terminology | NOT APPLIED — STOP |
| B-3 | BLOCKING | Blind touch can substitute for informed approval. | No trusted presentation evidence | Protected presentation/intent binding | NOT APPLIED — STOP |
| B-4 | BLOCKING | Proof schema/store/reference contract is incomplete and internally inconsistent. | Prose-only artifact model | Normative schemas/store/reference algorithm | NOT APPLIED — STOP |
| B-5 | BLOCKING | Revocation does not invalidate an outstanding gate-5-validated, unconsumed approval. | Revocation not live through consumption | Current recheck and projection invalidation | NOT APPLIED — STOP |
| B-6 | BLOCKING | PBRD/RDGO still normatively pin RIHAC/RIASC v1.0. | Non-atomic version graph | Amend PBRD and RDGO pins | **OUT OF SCOPE; STOP TRIGGER** |
| B-7 | BLOCKING | Proof nonce consumption at gate 5 contradicts mandatory pre-gate-9 approval revalidation. | Verification conflated with consumption | Bound-before-gate-9, consume atomically at gate 9 | NOT APPLIED — STOP |
| M-1 | MUST-FIX | RIHAC v1.1 should be a new MAJOR. | Incorrect compatibility classification | RIHAC v2.0 supersession | NOT APPLIED — STOP |
| M-2 | MUST-FIX | Internal cross-references are stale/mistargeted. | Citation drift | Correct every normative reference | NOT APPLIED — STOP |

All seven remain open because a partial freeze was forbidden.

## 49. Two MUST-FIX repairs

M-1 root cause is semantic incompatibility mislabeled as MINOR; prospective
repair is RIHAC v2.0 with explicit v1 non-migration. M-2 root cause is
unvalidated citation drift; prospective repair is a complete section/requirement
ID audit. Neither was applied due to the scope STOP.

## 50. New attack sweep

The prospective design was challenged for bootstrap circularity, authenticator
downgrade, blind touch, registry substitution, enrollment abuse, challenge
replay, proof copying, stale principal cache, domain confusion, repository-
controlled display, and spoofed principal metadata. The current freeze remains
vulnerable as already classified. No new independently distinct BLOCKING
finding is asserted because repair text was not frozen and thus cannot be
verified. **New BLOCKING count: 0; original open BLOCKING count: 7.**

## 51. Static verification

Fresh suite:
`tests/test_runtime_human_principal_contract_freeze_blocking_repair_3w1r2b1r.py`.
It checks the exact 7+2 inventory, fixed contract checksums, each reproduced
contradiction, and the PBRD/RDGO scope collision. Result: **15 passed**.

### Matrix B — Assurance properties

| Property | Evidence | Required? | What it proves | What it does NOT prove |
|---|---|---|---|---|
| Credential possession/use | Valid enrolled-key assertion | yes | enrolled credential signed | human presence, named user, intent |
| UP | authenticator UP flag | yes | physical interaction occurred | which human or comprehension |
| UV | authenticator UV flag | profile-dependent; required for named-user claim | local user verification | approval intent |
| Principal mapping | protected current registry | yes | credential maps to PCAE principal | legal/biological identity or intent |
| Informed approval | protected presentation receipt bound to challenge | yes | exact subject was presented/elected | PB permission or execution |

### Matrix C — Trust root

| Component | Controlled by | Mutable by repository? | Trust basis |
|---|---|---|---|
| Registry/config | protected deployment admin | no | OS/equivalent separate authority and protected path |
| Proof store | trusted coordinator under protected policy | no | canonical create-only bytes/digest/state |
| Mechanism allowlist/UV floor | contract + protected admin | no | immutable minimum, no downgrade |
| Approval subject | trusted PCAE coordinator | no | canonical repo/task/target/prompt state |
| Presentation | protected presentation component | no | integrity-bound canonical facts |

### Matrix D — Approval ceremony

| Human-visible fact | Canonical source | Challenge-bound? | Integrity requirement |
|---|---|---|---|
| Repository identity | trusted repository identity | yes | no repo display-name substitution |
| Task | active task contract ID/digest | yes | exact current task |
| Runtime target | explicit trusted target selection | yes | no fallback/alias |
| Prompt identity | semantic prompt digest/fingerprint | yes | canonical bytes/profile |
| Invocation identity | trusted coordinator | yes | caller-independent |
| Effect class/scope | canonical request/approval scope | yes | exact bounded effects |

### Matrix E — Replay/domain separation

| Source proof/domain | Attempted target domain | Expected |
|---|---|---|
| HATP | HPAC runtime approval | reject |
| HPAC runtime approval | HATP | reject |
| HPAC invocation A | invocation B | reject |
| HPAC repo A | repo B | reject |
| HPAC task A | task B | reject |

### Matrix F — Contract versions

| Contract | Pre-repair | Post-repair | Reason |
|---|---|---|---|
| RIHAC | 1.1 | **not applied; prospective 2.0** | mandatory incompatible authority semantics |
| RIASC | 2.0 | **not applied; prospective 3.0** | incompatible required contract-version/proof meaning |
| HPAC | 1.0 | **not applied; prospective 2.0** | load-bearing trust/proof/lifecycle redesign |
| PBRD | 1.1 | **required but out of scope** | must pin repaired RIHAC |
| RDGO | 2.0 | **required but out of scope** | must pin repaired RIHAC/RIASC and lifecycle |
| RPAC | 1.0 | unchanged | provider/gate architecture remains compatible |

### Matrix G — Threat closure

| Threat | Repair | Remaining dependency |
|---|---|---|
| same-UID registry/config mutation | protected admin/root | OS/equivalent enforcement implementation |
| wrong-user UP gesture | honest profile + required UV for named identity | authenticator UV capability |
| blind touch | protected subject presentation | trusted UI/out-of-band architecture |
| proof fabrication/copy | canonical schema/store/current verification | future implementation |
| stale revocation | recheck through gate 9 | future implementation |
| active-version downgrade | PBRD/RDGO pins | **scope authorization** |
| replay/revalidation conflict | split binding from consumption | coordinated RDGO text |

## 52. Contract versions

No contract version changed. Current failed freeze remains RIHAC v1.1,
RIASC v2.0, HPAC v1.0, PBRD v1.1, RDGO v2.0, RPAC v1.0. Prospective
evidence-derived repair requires at least RIHAC v2.0, RIASC v3.0, HPAC v2.0,
plus explicit PBRD/RDGO evolution in a newly authorized scope.

## 53. Implementation status

```text
human-principal authentication implementation: NOT IMPLEMENTED
FIDO2 for HPAC: NOT IMPLEMENTED / HARDWARE NOT TOUCHED
B1/B7/N1/N2 implementation repair: NOT PERFORMED
production source modified: NO
POL-005: UNCHANGED HARD DENY
runtime: Observed / observe / unavailable
real execution: NOT ACTIVATED
```

## 54. Final verdict

```text
HUMAN-PRINCIPAL AUTHENTICATION CONTRACT REPAIR: STOPPED — SCOPE INSUFFICIENT
NINE FINDINGS RECOVERED: 7 BLOCKING + 2 MUST-FIX
ORIGINAL BLOCKING CLOSED: 0 / 7
MUST-FIX CLOSED: 0 / 2
B-6: REQUIRES PBRD/RDGO EVOLUTION OUTSIDE AUTHORIZED SCOPE
CONTRACTS MODIFIED: NONE
N2 CONTRACT GAP: OPEN
IMPLEMENTATION READY: NO
HARDWARE: NOT TOUCHED
RUNTIME: Observed / observe / unavailable
REAL EXECUTION: NOT ACTIVATED
```

## 55. Recommended next phase

Recommend exactly, not begun:

**149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime Invocation
Human-Principal Authentication Freeze Repair**, explicitly authorized to
evolve RIHAC, RIASC, HPAC, PBRD, and RDGO together while leaving RPAC and
production source unchanged, followed by independent verification.

## 56. Human decision required

Stop. Do not broaden this phase, edit contracts, begin implementation, touch
hardware, or start the recommended successor without explicit human
authorization.

## Canonical phase-report facts

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R`
- **Status:** complete — STOPPED / SCOPE INSUFFICIENT
- **Completeness:** complete
- **Phase-entry SHA:** `88056f36a2e47d48e3f1467d71c6746ceb378074`
- **v0.4.3:** unchanged at `63580893b1de4782a694ab802ff7bdebdf29b0e6`
- **Runtime:** `Observed` / `observe` / `unavailable`
- **All seven BLOCKING:** recovered verbatim; 0 closed
- **Both MUST-FIX:** recovered verbatim; 0 closed
- **Root causes:** trust-root convention, assurance/intent collapse,
  incomplete proof lifecycle, non-atomic version graph, version/citation drift
- **RIHAC:** remains v1.1; prospective correct repair v2.0
- **RIASC:** remains v2.0; prospective correct repair v3.0
- **HPAC:** remains v1.0; prospective correct repair v2.0
- **Same-user-agent resistance / informed intent:** not established in current freeze
- **PBRD impact:** change required; out of scope; not modified
- **RDGO impact:** change required; out of scope; not modified
- **RPAC impact:** no change required
- **N2:** contract gap open
- **B1/B7/N1:** implementation repair not performed
- **New BLOCKING:** 0 (no repaired text was frozen)
- **Production source modified:** NO
- **Hardware touched:** NO
- **Execution activated:** NO
- **POL-005:** unchanged
- **Release/article/private research:** unchanged / stopped / untouched
- **Tests:** fresh STOP-gate static suite, 15 passed
- **Commits/push:** finalized through governed close; see canonical metadata
- **Exact next:** `149O.20L.7O.3W.1R.2B.1R.1`, broadened contract-only repair
- **Human decision:** required
