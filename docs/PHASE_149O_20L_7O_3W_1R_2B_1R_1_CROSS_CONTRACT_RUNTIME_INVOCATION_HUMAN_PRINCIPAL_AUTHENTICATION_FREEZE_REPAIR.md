# Phase 149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime Invocation Human-Principal Authentication Freeze Repair

## 1. Objective

Close exactly seven BLOCKING and two MUST-FIX findings by coherently evolving
RIHAC, RIASC, HPAC, PBRD, and RDGO, without changing RPAC or production. The
semantic walls remain: authentication, presence, verification, informed
intent, authority provenance, PB permission, capability, and execution are
distinct.

## 2. Baseline

| Fact | Entry state |
|---|---|
| Phase-entry SHA | `64e045efdcbe9a95f678e5bc450da51a9b1dbabd` |
| `origin/main` / ahead | same / `0` |
| Worktree | clean |
| Release | `v0.4.3` at `63580893b1de4782a694ab802ff7bdebdf29b0e6` |
| Runtime | `Observed / observe / unavailable`; 0 plugins/capabilities |
| Governance | healthy; check passed; coherent; historical task-memory warnings only |
| Notification | configured, enabled, ready |

No private research, article, hardware, provider credential, network, or
runtime source was accessed.

## 3. Nine findings

Both primary artifacts were read completely before any contract edit. They
contain exactly seven BLOCKING and two MUST-FIX findings.

### Matrix A — Nine findings

| ID | Severity | Exact wording | Contract repair | Verdict |
|---|---|---|---|---|
| B-1 | BLOCKING | **B-1 — Principal registry/bootstrap/configuration trust root is not same-user-agent resistant.** Location and “non-agent-invocable” convention do not replace protected ownership/ACL/separate-principal enforcement. | HPAC v2 protected administration root, path/ACL/owner resolution, external bootstrap anchor | CLOSED |
| B-2 | BLOCKING | **B-2 — UP-only overclaims a named authenticated human.** UV is optional and no exclusive credential custody is frozen. | UP and UV distinct; both mandatory; exact credential-bound terminology | CLOSED |
| B-3 | BLOCKING | **B-3 — Blind touch can substitute for informed approval.** No non-forgeable confirmation evidence or trusted subject display is bound. | `TrustedApprovalPresentation`, protected channel, exact challenge binding | CLOSED |
| B-4 | BLOCKING | **B-4 — Proof schema/store/reference contract is incomplete and internally inconsistent.** Canonical resolution cannot be implemented uniquely. | HPAC-PROOF/2.0 exact fields/store/lifecycle; RIASC exact `proof_id`/`proof_digest` | CLOSED |
| B-5 | BLOCKING | **B-5 — Revocation does not invalidate an outstanding gate-5-validated, unconsumed approval.** Current-principal assurance can go stale before dispatch. | Current registry/proof revalidation; every unconsumed layer invalidated | CLOSED |
| B-6 | BLOCKING | **B-6 — PBRD/RDGO still normatively pin RIHAC/RIASC v1.0.** The active contract graph is ambiguous and permits the insecure predecessor. | PBRD v2 and RDGO v3 pin the repaired graph | CLOSED |
| B-7 | BLOCKING | **B-7 — Proof nonce consumption at gate 5 contradicts mandatory pre-gate-9 approval revalidation.** The frozen lifecycle is not implementable consistently. | Gate 5 verifies/binds idempotently; gate 9 atomically consumes proof+approval | CLOSED |
| M-1 | MUST-FIX | **M-1 — RIHAC v1.1 should be a new MAJOR.** The change is mandatory and semantically incompatible, not optional evidence or mere clarification. | RIHAC v2.0; v1.x has no migration | CLOSED |
| M-2 | MUST-FIX | **M-2 — Internal cross-references are stale/mistargeted.** Examples: HPAC references nonexistent §39–§41 and mispoints fallback sections; RIHAC calls software fallback HPAC §15 although §15 is domain separation. | Version/section/reference audit and repaired citations | CLOSED |

Inventory columns additionally required by the entry rule:

| ID | Contract section | Failure scenario | Root cause |
|---|---|---|---|
| B-1 | HPAC §§7–8/28 | same-UID agent redirects store/enrolls | convention substituted for protected root |
| B-2 | HPAC §§14/20 | shared credential touched without UV | assurance properties collapsed |
| B-3 | HPAC §§14–16; RIHAC §§3/12 | false-pretext touch signs hidden subject | no trusted display evidence |
| B-4 | HPAC §§17–19; RIASC §§7/12 | plausible ref resolves differently | no normative artifact model |
| B-5 | HPAC §21; RIHAC §14 | revoke after gate 5 | stale validation treated as durable trust |
| B-6 | PBRD/RDGO headers | consumer selects v1 graph | non-atomic companion evolution |
| B-7 | HPAC §§18/24; RDGO §§6/17 | restart revalidation sees consumed nonce | verification conflated with consumption |
| M-1 | RIHAC §§12/16/21 | v1 artifact lacks mandatory proof | incompatible semantics mislabeled MINOR |
| M-2 | HPAC/RIHAC references | implementer follows wrong section | citation drift |

## 4. Finding reproduction

All nine findings were **REPRODUCED** before editing: B-1 through HPAC's
location/convention writer; B-2 through optional UV; B-3 through absence of a
trusted receipt; B-4 through mismatched reference keys and missing schema/
store; B-5 through the explicit survival rule; B-6 through normative headers;
B-7 through gate-5 nonce consumption plus pre-gate-9 full revalidation; M-1
through retired no-signature semantics; M-2 through nonexistent/mistargeted
sections. No discrepancy required a stop.

## 5. Root causes

```text
convention-only trust root -> B-1 -> HPAC
assurance/intent collapse -> B-2/B-3 -> HPAC/RIHAC/RIASC
missing proof state model -> B-4/B-5/B-7 -> HPAC/RIHAC/RIASC/RDGO
non-atomic contract graph -> B-6 -> PBRD/RDGO
version/citation hygiene -> M-1/M-2 -> all five repaired contracts
```

## 6. Contract ownership

### Matrix C — Cross-contract ownership

| Concept | HPAC | RIHAC | RIASC | PBRD | RDGO |
|---|---|---|---|---|---|
| HumanPrincipal / registry / mechanism / UP / UV | **owner** | consumes result | carries IDs | none | sequences |
| challenge / authentication proof | **owner** | validates conjunction | proof reference | opaque | sequences state |
| informed presentation / approval intent | **evidence owner** | **authority meaning owner** | carries digest/ref linkage | none | ceremony ordering |
| RuntimeInvocationApproval | no | **owner** | **wire-shape owner** | reference only | lifecycle |
| validated authority projection | inputs | **owner** | no | consumes typed evidence | sequences |
| PB authority evidence / decision | no | supplies projection | no | **owner** | sequences |
| dispatch gate order / one-shot consumption | proof transition | authority transition | immutable artifact | never consumes | **owner** |

Every concept has one primary owner; companions reference rather than redefine.

## 7. Authentication semantics

`AuthenticatedHumanPrincipal` means successful current verification of an
active credential enrolled to an opaque PCAE `principal_id`, under the
required assurance profile and protected registry. It does not assert legal,
civil, biological, OS, Git, agent, producer, or runtime identity.

## 8. UP

UP evidence is the verified authenticator UP flag. It proves an active
presence event at the enrolled authenticator. It does not prove which human,
UV, presentation, intent, PB permission, or execution.

## 9. UV

UV evidence is the verified authenticator UV flag. It proves authenticator-
local user verification. For the first real-runtime profile UP and UV are
both mandatory; UP-only may be recorded as credential presence but cannot
authorize runtime. No deployment or repository may lower the floor.

## 10. Informed intent

The defensible property is: the human was given a trusted opportunity to
inspect the exact canonical invocation subject and performed an explicit,
non-defaultable, UP+UV-authenticated approval act cryptographically bound to
it. PCAE does not claim to prove comprehension or consequences understood.

## 11. Trusted presentation

`TrustedApprovalPresentation` is HPAC-owned protected evidence. Its channel
must prevent the requesting same-user agent from substituting displayed
canonical values. Ordinary agent-controlled stdout/stdin and repository-
authored labels are insufficient. Implementation may later select protected
TTY/UI, authenticator display, or out-of-band channel without changing the
contract property.

## 12. Blind touch

“Touch your key” plus a valid hidden assertion is non-authority. Missing
protected presentation, missing explicit election, or any display/challenge
mismatch fails before approval creation.

## 13. Presentation/challenge binding

```text
human-visible canonical facts == trusted_presentation_digest
canonical approval subject == approval_subject_digest
both digests + principal/credential + nonce + domain/version == signed challenge
```

Mismatch at any equality invalidates proof and approval.

## 14. Bootstrap trust

The non-circular v2 root is an externally established OS/equivalent
deployment-owner administration principal unavailable to ordinary same-UID
agent execution. It runs the protected first-enrollment ceremony; no prior
PCAE principal is assumed.

## 15. Enrollment

Only protected administration may enroll/revoke. It requires protected exact
operation presentation, fresh non-defaultable UP+UV, verified registration,
atomic read-back-verified write, and durable provenance/audit. Same-user agent
invocation is denied before hardware registration or mutation.

## 16. Principal registry

The deployment-scoped registry is outside repositories in a protected root
whose owner/ACL/ancestor/path/delete/replace/symlink properties are verified.
It stores closed principal and credential records, public verification key,
mechanism/assurance capability, status/timestamps, mapping, and verified
enrollment provenance; never secrets.

## 17. Repository independence

Repository/task/agent/environment/cwd state cannot select or alter registry,
proof store, mapping, mechanism, assurance/UV floor, enrollment, or trusted
presentation. Detected influence invalidates authority.

## 18. Mechanism downgrade

Required mechanism unavailable means approval unavailable. No automatic or
software/UP-only downgrade qualifies for first real runtime.

## 19. Challenge

Closed canonical challenge fields are domain, challenge/proof versions,
principal, credential, subject digest, presentation digest, coordinator-
generated nonce, issue time, and expiry. Canonical compact NFC JSON is hashed
with SHA-256; callers do not select nonce or domain.

## 20. Domain separation

The signed domain is `pcae.hpac.runtime-invocation-approval.v2`. HATP,
publication/signing, Class-B, and other authority domains use separate
registries, IDs, roles, audits, and challenge domains.

## 21. Replay

HATP→HPAC, HPAC→HATP, invocation A→B, repo A→B, task A→B, target A→B,
prompt A→B, expired nonce, and consumed proof all reject. Same-binding
pre-gate-9 revalidation is idempotent verification, not replay or consumption.

## 22. Authentication proof

HPAC-PROOF/2.0 has exact closed fields and canonical digest rules. Protected
storage is `<HPAC_PROTECTED_ROOT>/proofs/v2/<proof_id>/proof.json`; reference
is exactly `(proof_id, proof_digest)`. Serialized bytes are always untrusted
until canonical resolution and full verification.

## 23. Trusted principal

`AuthenticatedHumanPrincipal` is ephemeral, non-serializable verifier output.
Caller-created objects, copied fields, public digests, booleans, and sentinels
are non-authority. Persisted proof is re-resolved against current registry.

## 24. Approval creation

```text
canonical invocation subject
-> protected presentation
-> explicit election + UP + UV
-> domain/subject/presentation-bound assertion
-> protected proof verification/binding
-> ephemeral authenticated principal
-> trusted coordinator creates RIASC v3 approval
```

No caller-created trusted approval path exists.

## 25. Canonical provenance

RIHAC resolves one immutable canonical approval from
`.pcae/runtime-invocation-approvals/v2/<approval_id>/approval.json` and
recomputes its digest. HPAC proof alone cannot make arbitrary approval bytes
canonical; this preserves N1 closure-enabling provenance.

## 26. RIHAC repair

RIHAC is v2.0. A v1-valid approval can lack every new authenticated-principal
and intent property, so the change is MAJOR. V1.x is historical only, not
migrated, upgraded, or authority-valid under v2.

## 27. RIASC repair

RIASC is v3.0. It incompatibly pins RIHAC/2.0, changes the required approval
mechanism, and changes proof-reference meaning to exact proof keys. The
five-member subject and sixteen top-level field count remain unchanged.

## 28. HPAC repair

HPAC is v2.0 because trust-root, enrollment, assurance, presentation, proof
schema/store, revocation, and lifecycle meanings are incompatible with v1.

## 29. PBRD repair

PBRD is v2.0. Its header pins RIHAC v2/RIASC v3/HPAC v2/RDGO v3. The required
`human_authority_binding` meaning changes from a generic validation digest to
a closed RIHAC v2 authority projection, so v1.1 requests do not migrate.

## 30. PB authority evidence

The closed binding contains approval ID/digest, authority projection ID/
digest, const `RIHAC-001/2.0`, proof-validation digest, and request-binding
digest. PB verifies binding and policy, never human identity, FIDO2, registry,
raw proof, or a raw approval boolean.

## 31. RDGO repair

RDGO is v3.0 with the same eleven gates/order and gate 10 first effect. Gate
3 owns ceremony/creation, gate 5 current canonical validation and proof
binding, gate 6 PB, and gate 9 atomic approval+proof consumption. The v2
state-machine contradiction makes v3 a MAJOR.

## 32. RPAC no-change proof

RPAC-001 v1.0 remains byte-identical (SHA-256
`395f6b9d3f1779fb312f66e06819176417db6380193d1f5fee52668d43260c89`).
It already owns provider-neutral target/adapter boundaries, approval before
preflight, unique invocation/attempt/idempotency, PB/RE separation, and the
gate-10 effect boundary. Authentication mechanism internals do not belong in
RPAC; no requirement or schema changes.

## 33. Cross-contract trace

```text
HPAC proof --current protected verification--> RIHAC authority validation
RIHAC validation --wire conformance--> RIASC approval artifact
canonical approval --fresh re-resolution--> RIHAC trusted projection
trusted projection --typed binding--> PBRD request evidence
PBRD evidence + policy --PB decision--> RDGO continuation
RDGO gates 7/8/9 --independent RE/containment/durable consume--> gate 10 eligibility
```

Each arrow is owned by the contract on its right; no transition implies the
next decision.

## 34. HUMAN_REVIEW

Valid authenticated authority prevents only the intended
`MissingHumanApprovalRule` trigger for that exact request. Other policies may
still DENY or HUMAN_REVIEW. HUMAN_REVIEW never authorizes dispatch and is not
a second implicit approval ceremony.

## 35. POL-005

POL-005 remains an unchanged universal hard DENY for truthful non-simulation
requests. These contracts neither relax it nor imply eligibility.

## 36. One-shot

Authentication and gate-5 validation do not consume. PB evaluation does not
consume. Gate 9 atomically binds the durable `dispatch_attempted` marker and
transitions approval plus its proof to consumed. No automatic retry.

## 37. Revocation

Current principal, credential, proof lifecycle, approval freshness, and
registry state are revalidated through gate 9. Revocation invalidates unused
challenge, verified/bound proof, unmaterialized or unconsumed approval, and
PB projection. No stale cache survives.

## 38. Same-user-agent proof obligation

Future verification must demonstrate that an autonomous agent under the same
OS account cannot enroll, reconfigure, spoof presentation, or create valid
real-runtime approval without the protected UP+UV+intent ceremony.

## 39. Informed-intent proof obligation

Future verification must establish:
`WHAT HUMAN WAS SHOWN == WHAT HUMAN AUTHENTICATED == WHAT PCAE AUTHORIZES`
at the canonical semantic subject level.

## 40. B1

Fresh PB projection requires canonical approval and HPAC proof re-resolution,
current registry validation, and trusted construction. No transferable seal.

## 41. B7

Attempt/dispatch identity remains PCAE-owned and registry/canonical-state
verified. Human authentication cannot substitute for attempt identity.

## 42. N1

Canonical approval-store provenance is mandatory in addition to HPAC proof.
Arbitrary in-memory approval validation cannot yield trusted authority.

## 43. N2

Caller-supplied principal, credential, mechanism, proof reference, approval
fields, booleans, or projection-shaped objects have zero authority. Without
protected-root resolution and a genuine exact-subject/presentation-bound proof
the chain fails. **N2 CONTRACT GAP: CLOSED.**

## 44. Seven blocker closure

| Finding | Root cause | Contract(s) changed | Closure invariant |
|---|---|---|---|
| B-1 | convention trust | HPAC | protected external admin/root required |
| B-2 | assurance collapse | HPAC | UP+UV distinct and mandatory |
| B-3 | no intent evidence | HPAC/RIHAC/RIASC/RDGO | protected display equals challenge subject |
| B-4 | incomplete artifact | HPAC/RIASC/RIHAC | exact schema/store/reference resolution |
| B-5 | stale revocation | HPAC/RIHAC/RDGO/PBRD | all unconsumed authority revalidated |
| B-6 | stale graph pins | PBRD/RDGO | only repaired active versions permitted |
| B-7 | consume/verify conflict | HPAC/RIHAC/RDGO | bind at gate 5; consume once at gate 9 |

## 45. MUST-FIX closure

| Finding | Root cause | Contract change | Closure |
|---|---|---|---|
| M-1 | incompatible semantics mislabeled minor | RIHAC v2.0 supersession/non-migration | CLOSED |
| M-2 | reference drift | corrected versions, sections, proof keys, fallback citations | CLOSED |

## 46. Version matrix

### Matrix D — Version evolution

| Contract | Before | After | Reason |
|---|---|---|---|
| RIHAC | 1.1 | 2.0 | old approval no longer authority-valid |
| RIASC | 2.0 | 3.0 | required const/type/meaning changes |
| HPAC | 1.0 | 2.0 | trust/proof/intent/lifecycle redesign |
| PBRD | 1.1 | 2.0 | required authority-binding meaning changes |
| RDGO | 2.0 | 3.0 | incompatible gate-5/gate-9 state semantics |
| RPAC | 1.0 | 1.0 unchanged | provider/gate abstraction remains sufficient |

## 47. Vocabulary

`asserted principal` = caller claim; `enrolled principal` = protected active
registry record; `authenticated principal` = ephemeral verified result;
`approval intent` = protected subject-bound election; `approval artifact` =
canonical RIASC bytes; `trusted authority` = freshly validated RIHAC
projection; `PB authority evidence` = typed projection binding. These terms
are not synonyms.

### Matrix B — Trust properties

| Property | Evidence | Contract owner | Required for real runtime? |
|---|---|---|---|
| enrolled credential | protected registry public key/mapping | HPAC | yes |
| UP | verified authenticator flag | HPAC | yes |
| UV | verified authenticator flag | HPAC | yes |
| authenticated principal | full current proof verification | HPAC | yes |
| informed intent | protected presentation/election bound to challenge | HPAC/RIHAC | yes |
| authority provenance | canonical approval + current proof projection | RIHAC | yes |

## 48. Cross-references

Normative active pins are RIHAC 2.0, RIASC 3.0, HPAC 2.0, PBRD 2.0, RDGO
3.0, and RPAC 1.0. HPAC no longer cites nonexistent §§39–41; RIHAC no longer
misidentifies HPAC domain separation as software fallback. Historical
supersession prose is explicitly version-qualified.

## 49. Static verification

Fresh suite:
`tests/test_runtime_human_principal_cross_contract_freeze_repair_3w1r2b1r1.py`.
It checks exact 7+2 recovery, versions/supersession, RIASC JSON, HPAC proof/
registry/domain/assurance/presentation/replay/revocation, PBRD evidence and
POL-005/HUMAN_REVIEW, RDGO order/lifecycle, RPAC checksum, report structure,
and no-go state. Final result is recorded at close.

## 50. New attack sweep

### Matrix E — Human presentation

| Displayed fact | Canonical source | Challenge binding | Tamper authority |
|---|---|---|---|
| repository | trusted fingerprint + human-usable identity | subject/presentation digests | none for repo |
| task | active canonical task ID/digest | both | none for task/agent |
| runtime target | trusted target selection | both | none for adapter |
| operation/effect/scope | canonical request/approval scope | both | none for repo |
| prompt/instruction | semantic digest + recognizable fingerprint | both | none for display text |
| invocation/expiry/one-shot | coordinator canonical state | both | none for caller |

### Matrix F — Threat closure

| Threat | Contract defense | Residual dependency |
|---|---|---|
| blind touch | protected presentation + explicit election + signed binding | trusted UI implementation |
| enrollment self-authorization | external protected admin + UP/UV | protected admin implementation |
| registry replacement | protected owner/ACL/path resolution | OS/equivalent enforcement |
| UV downgrade | immutable UP+UV minimum | verifier implementation |
| replay/domain confusion | v2 domain + nonce/binding lifecycle | protected store implementation |
| stale registry | current re-resolution through gate 9 | validator implementation |
| forged projection/raw boolean | trusted RIHAC construction + typed PBRD binding | B1 production repair |
| gate contradiction | bind at 5, consume at 9 | RDGO implementation |

Adversarial review found no new contract-level BLOCKING issue. Mechanism-
neutral protected-presentation requirements are complete enough for
implementation without prematurely selecting UI technology.

## 51. Freeze verdict

```text
CROSS-CONTRACT HUMAN-PRINCIPAL AUTHENTICATION FREEZE REPAIR: COMPLETE
ORIGINAL BLOCKING: 7 / 7 CLOSED
MUST-FIX: 2 / 2 CLOSED
NEW BLOCKING: 0
N2 CONTRACT GAP: CLOSED
PBRD: CONSISTENT
RDGO: CONSISTENT
RPAC: UNCHANGED / CONSISTENT
SAME-USER AGENT RESISTANCE: CONTRACTED
BLIND TOUCH: INSUFFICIENT
TRUSTED PRESENTATION: REQUIRED
```

## 52. Implementation readiness

**CROSS-CONTRACT AUTHENTICATION/AUTHORITY FREEZE: IMPLEMENTATION READY? YES.**
This is contract readiness only, not authority-foundation or real-runtime
readiness.

## 53. Current authority status

### Matrix G — Open implementation findings

| Finding | Contract enabled? | Production repair later required? |
|---|---|---|
| B1 copyable authority seal | yes | yes |
| B7 attempt identity registry bypass | yes | yes |
| N1 bare approval provenance | yes | yes |
| N2 human provenance | contract gap closed | yes, full HPAC implementation |

```text
B1/B7/N1/N2 implementation: NOT YET REPAIRED
AUTHORITY/PB FOUNDATION: NOT YET VERIFIED
REAL-RUNTIME READY: NO
production source modified: NO
hardware touched: NO
execution activated: NO
POL-005: UNCHANGED HARD DENY
runtime: Observed / observe / unavailable
release: v0.4.3 unchanged
article: stopped
private research: untouched
```

## 54. Recommended next phase

Exactly **149O.20L.7O.3W.1R.2B.1R.1.1 — Independent Verification of
Cross-Contract Runtime Invocation Human-Principal Authentication Freeze
Repair**. Verification only; do not proceed directly to implementation.

## 55. Human decision required

Stop after this phase. Independent verification requires explicit human
authorization. Do not implement, activate runtime, touch hardware, relax
POL-005, or begin the successor automatically.

## Canonical phase-report facts

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1`
- **Status/completeness:** complete / complete
- **Phase-entry SHA:** `64e045efdcbe9a95f678e5bc450da51a9b1dbabd`
- **Versions:** RIHAC 2.0; RIASC 3.0; HPAC 2.0; PBRD 2.0; RDGO 3.0; RPAC 1.0 unchanged
- **UP/UV:** distinct; both required
- **Authenticated principal:** active enrolled credential verified under current protected state and required assurance; not legal/OS identity
- **Intent/presentation:** protected opportunity-to-inspect plus explicit subject-bound act; blind touch insufficient
- **Registry/bootstrap/enrollment:** protected external deployment-owner root, non-circular, repository-independent, UP+UV gated
- **Domain/replay:** v2 signed domain; bind at gate 5; consume at gate 9
- **B1/B7/N1/N2:** contract-enabling complete; implementation not performed
- **Blocking/MUST-FIX/new:** 7/7 closed; 2/2 closed; 0 new
- **PBRD/RDGO/RPAC:** consistent / consistent / unchanged-consistent
- **HUMAN_REVIEW/POL-005:** narrow missing-approval behavior / unchanged hard DENY
- **Implementation readiness:** contract freeze YES; real runtime NO
- **Production source modified:** NO
- **Hardware touched:** NO
- **Execution activated:** NO
- **Runtime:** `Observed / observe / unavailable`
- **Release/article/private research:** unchanged / stopped / untouched
- **Checks/tests/commits/push/ahead:** populated by governed finalization evidence
- **Exact next:** `149O.20L.7O.3W.1R.2B.1R.1.1`
- **Human decision:** required
