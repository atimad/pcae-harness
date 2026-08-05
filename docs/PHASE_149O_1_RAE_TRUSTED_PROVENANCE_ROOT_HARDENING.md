# Phase 149O.1: RAE Trusted Provenance Root Hardening

**Phase type:** trusted-provenance-root architecture (verification-only outcome; no
production implementation authorized by this phase's own findings).

**Status:** completed. **Root-provenance verdict: TRUSTED PROVENANCE ROOT NOT
ACHIEVABLE — CURRENT TRUST MODEL INSUFFICIENT.**

## 1. Starting Position (independently reconfirmed)

- Repository clean; `origin/main..HEAD` = 0 at phase start.
- Latest completed phase: 149O (NOT VERIFIED — BLOCKING CANONICAL-PROVENANCE
  FINDINGS; root-provenance verdict PROVENANCE ROOT NOT VERIFIED — BLOCKING).
- `pcae health` / `pcae check` / `pcae status coherence` / `pcae doctor
  task-memory` / `pcae push check`: all healthy/coherent/clean at phase start.
- `pcae runtime inspect`: Runtime state Observed, maximum capability observe,
  execution capability unavailable — unchanged throughout this phase.
- `pcae notify status`: Telegram configured/enabled, outbound-only.
- AG3/AG5 Permission Broker integration: not implemented (confirmed by reading
  `src/pcae/core/rollback_approval_evidence.py`'s module docstring and import
  list — no import of `permission_broker*`, `mutation_permission`, or
  `pcae.core.agent`).

## 2. The Four B-149O Findings, Independently Reproduced

Ran `tests/test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`
unmodified before any change in this phase:

```
4 failed, 13 passed
FAILED ...::test_149o_fake_chgr_record_plus_fake_publication_receipt
FAILED ...::test_149o_fake_binding_plus_fake_creation_registration
FAILED ...::test_149o_full_end_to_end_forgery_zero_legitimate_api_calls
FAILED ...::test_149o_copied_registration_under_new_key_with_matching_fields_rejected
```

Exact call chains, from the current `resolve_rollback_approval_evidence`
(`src/pcae/core/rollback_approval_evidence.py:1205-1378`):

- **B-149O-1** (fake CHGR record + fake publication receipt): a hand-authored
  `records/<record_id>.json` (correct schema, digest self-consistent, correct
  `template_ref`, `lifecycle_state=published`) paired with a hand-authored
  `published/<package_id>.json` naming that `record_id`, resolves
  `_chgr_record_has_publication_receipt` (line 804) `True` with zero calls to
  `PublicationCoordinator.execute`.
- **B-149O-2** (fake Binding + fake creation registration): a genuine
  published Decision paired with a hand-authored `RollbackApprovalBinding`
  and a hand-authored `creation-registry/<evidence_id>.json` whose fields
  are self-consistent with it, passes `_binding_is_canonically_created`
  (line 1127) — the registration's `O_CREAT|O_EXCL` guarantee (line 651)
  only prevents *overwriting an existing* registration for a given key; it
  places no constraint on the content of a brand-new one.
- **B-149O-3** (full end-to-end forgery): combining both — zero calls
  anywhere to `create_rollback_approval_decision` or
  `create_rollback_approval_binding` — still resolves
  `RollbackApprovalValidationResult.VALID`, `approval_present=True`.
- **B-149O-4** (fresh forgery under brand-new key): the attack does not
  depend on copying any prior legitimate artifact; a wholly new, self-
  consistent (Binding, registration) pair under a freshly generated
  `evidence_id` and a freshly generated CHGR `record_id` validates
  identically. The defect is structural, not identifier-reuse.

**Blocking closure matrix (post-149O.1):**

| Finding | Status |
|---|---|
| B-149O-1 | OPEN — not fixed by this phase (§7 explains why no fix was applied) |
| B-149O-2 | OPEN |
| B-149O-3 | OPEN |
| B-149O-4 | OPEN |

No repair was attempted because, per §5-§7 below, every candidate repair
available within current PCAE architecture is another forgeable sidecar,
which the governing phase prompt explicitly forbids treating as a
solution (`record → receipt → receipt-of-receipt → registry-of-receipt`
does not establish provenance if every link is writable by the same actor).

## 3. Threat Model (stated explicitly, per governing-prompt requirement)

This phase adopts **Threat A** as the operative model, matching the RAE-001
contract's own §22 threat table (which names "Agent-generated fake approval
JSON" as threat #2, a technical/adversarial entry, not merely an accidental-
misuse one):

> **Threat A — Ungoverned artifact construction.** An attacker can write
> arbitrary files under any path the legitimate PCAE code can also write
> (`.pcae/**`, the publication root), choose public field values, compute
> hashes/digests using the same public algorithms this module uses, copy
> artifact formats, and call any public Python API in this repository
> (including `create_rollback_approval_decision`,
> `create_rollback_approval_binding`, `PublicationCoordinator.execute`) —
> but is not assumed to possess any separate secret, credential, or
> out-of-band capability unavailable to legitimate PCAE code.

**Threat B (full local-user compromise: modify all files, invoke all
binaries, modify configuration)** is explicitly *not* the model this phase
defends against, and RAE-001 never claimed to defend against it either.
The distinction matters: 149O's four findings are all Threat-A attacks
(schema-conformant, algorithmically-correct forgeries using only public
information and public code paths) — none of them required filesystem
permissions, process privileges, or knowledge beyond what any PCAE agent
process already legitimately has. This phase does not conflate Threat A
and Threat B at any point.

## 4. Trust Ceiling Carried Forward (RAE-001, unchanged)

RAE-001 already discloses, as STRATEGIC_GAP, the exact ceiling this phase
must not overstate:

- **RAE-REQ-005**: "This repository has no OS-level, cryptographic, or
  identity-provider authentication anywhere in its human-governance stack
  today." (`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md:198-210`)
- **RAE-REQ-009**: "This repository has no technical privilege separation
  between an agent process and a human operator; both reach the same CLI
  ... cannot prevent an agent from operating the CLI as the human."
  (same file, lines 245-252)

This phase does not claim, and must not implicitly claim, any stronger
guarantee than these two already-frozen admissions. **Forged actor
identity (threat #3 in RAE-001 §22) remains explicitly out of scope and
explicitly unsolved** — RAE-001 itself says so. This phase's scope is
narrower and different: **threat #2**, "Agent-generated fake approval
JSON," which RAE-001 *does* claim RAE-REQ-018 defends against. 149O
falsified that specific claim. 149O.1's job is to determine whether
threat #2's claimed defense can be made true, not to solve threat #3.

## 5. Existing Trust/Provenance Mechanism Inventory

Independently inspected (read-only) every candidate location a non-
forgeable root could plausibly live:

| Candidate | Location | Independent under Threat A? |
|---|---|---|
| `PublicationCoordinator.authorize()` | `src/pcae/governance/publication/coordinator.py:91-113` | **No.** Builds an authorization event from caller-supplied `operator_id`/`package_id`/`invoked_at` with no verification; its own docstring states callers must supply `operator_id` "from their own already-verified human-operator identity" — i.e. trust is assumed, not checked. |
| `PublicationCoordinator.execute()` | same file, 115-211 | **No.** Validation is replay-marker existence, package dataclass shape, authorization/package `package_id` match, and `invoked_at >= built_at` timestamp comparison — all derivable from public, caller-supplied data. |
| `PublicationRecordStore` (records/, published/, attempts/) | `src/pcae/governance/publication/storage.py` | **No.** Plain JSON files; `O_CREAT|O_EXCL` guarantees idempotency (can't silently overwrite), not authenticity of the writer. |
| `generate_session_id()` | `src/pcae/interactive_workflow/session/identity.py:34-37` | **No.** `f"CDS-{uuid.uuid4()}"` — collision-resistant, not a secret/capability. |
| `Session.owner_identity` / `decision_maker_evidence_kind` | `src/pcae/interactive_workflow/models/session.py` | **No.** Caller-supplied string / caller-chosen enum label (`"os_authenticated_user"` is available as a label with no enforcing OS check anywhere). |
| Agent lock (`.pcae/agent-lock.json`, `.pcae/agent-locks/latest.json`) | `src/pcae/core/agent.py:288-368` | **No.** `acquire_agent_lock` writes the lock file with `agent_id` taken verbatim from the CLI flag; no proof-of-possession. |
| Signing/keychain/hardware/credential primitives anywhere in `src/pcae` | repo-wide grep for `hmac`, `signing_key`, `private_key`, `sign(`, `signature`, `hardware`, `yubikey`, `secret_key`, `getpass`, `keychain` | **None exist.** Every match is either a docstring explicitly disclaiming the capability (`cltr/authority/authorization_candidate.py:14,478,483`; `bindings.py:47,986`) or third-party-secret *redaction* logic (`shell_gate.py`, `backend_invocations.py`, `notification_config.py`, `canonical_engineering_evidence.py`) — never a credential PCAE itself uses to authenticate anything. |
| Git commit history | — | **No** (verified, not assumed): no commit signing is required or checked anywhere in this repository's tooling; approval artifacts are not intended to enter git (they live under `.pcae/`, gitignored runtime state); unsigned local commits are trusted for everything else PCAE does. Not a viable root. |
| Telegram (outbound notification) | `src/pcae/core/notifications.py`, `backend_invocations.py` | **Not available, and explicitly forbidden as a shortcut.** PCAE's Telegram integration is architecturally outbound-only: `notifications.py:584` states plainly "No inbound commands. No polling. No remote shell," and numerous frozen invariants elsewhere (`backend_invocations.py`: `no_telegram_inbound: bool = True`, `telegram_inbound_allowed: bool = False`, `NOGO_TELEGRAM_INBOUND`) exist specifically to keep it that way. A human-controlled external channel that could authenticate an approval message would require *reversing* multiple currently-frozen no-inbound guarantees — new architecture and almost certainly new contract text, not a bounded hardening step. Per the governing phase prompt's own item 13, this must not be repurposed without contract support; it is not evaluated further as an in-scope root for this phase. |
| IWC confirmation | `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`, `session.py` | **No stronger property than the artifacts it produces.** IWC's confirmation transport terminates in exactly the same `Session`/`PublicationReadinessPackage` caller-supplied data already assessed above; it supplies no independent, non-self-asserted fact. Re-labeling IWC confirmation as approval was explicitly disallowed by the governing prompt and is not proposed here. |
| OS user/process separation between "agent" and "human" | — | **Does not exist**, confirmed both by direct grep (no `getpass.getuser()`, no `os.environ["USER"]` check, no `sys.stdin.isatty()` gate anywhere in the governance/publication/RAE path) and by RAE-REQ-009's own text. Any secret placed in an environment variable, a plaintext file under `.pcae/**`, or an OS keychain item retrievable without a fresh, per-use human-presence prompt would be equally readable by the same agent process that must be distinguished from a human. None of these are independent roots under RAE-REQ-009's already-disclosed ceiling. |

**Conclusion: no existing, independently-trusted (non-filesystem,
non-same-process) root exists anywhere in current PCAE architecture.**
ROOT A is unavailable.

## 6. API-vs-Human Provenance Analysis (governing-prompt item 4/48/49)

Key question: if the same agent/process that must be distinguished from a
"legitimate" actor can *also* call `create_rollback_approval_decision` /
`create_rollback_approval_binding` directly, does "created through the
canonical API" meaningfully distinguish trusted creation from fabrication?

**Answer: no, not for identity (Threat B / RAE-001 threat #3 — already
disclosed, out of scope), but this was never RAE-018's claim.** RAE-REQ-018
never claimed to authenticate *who* approved; RAE-REQ-005/009 already
concede that. RAE-REQ-018's actual, narrower claim is procedural: that
`approval_present` requires the referenced Decision to be "an actually-
published" record reached through CHGR's Confirmation → Publication
ritual, as opposed to a JSON file dropped directly into `records/` bypassing
that ritual entirely (RAE-001 §22 threat #2). This is a **Model P**
(procedural canonical-provenance) claim, not a **Model T** (technically-
unforgeable-identity) claim — RAE-001 never asserts Model T for *identity*.

The critical finding of this phase is that **even Model P currently fails
on its own terms**, because nothing distinguishes "the bytes that
`PublicationCoordinator.execute()` would have written" from "bytes an
attacker computed and wrote directly," when both are produced by the same
public, unauthenticated, purely-shape-validating code path with no secret
step anywhere in it (§5's `authorize()`/`execute()` finding). 149M
attempted to solve this a different way (self-consistency); 149N added a
receipt sidecar; 149O showed the receipt sidecar is itself reproducible by
the identical mechanism, because "reproducible-by-the-same-mechanism" is
not a property any *additional* file can fix — it is a property of the
*mechanism itself* having no secret step. This is why the governing
prompt's "no more sidecars" rule is correct: adding a fifth JSON file
written by the same unauthenticated code path only relocates B-149O-1..4
to a new filename; it does not close them. **Formal demonstration
(governing-prompt item 97, "no circular proof"):** artifact
self-consistency (149M) does not prove receipt authenticity; receipt
existence (149N) does not prove registration authenticity; registration
existence does not prove artifact authenticity — every one of these checks
a *second self-describing file*, and every self-describing file is
producible by the same unauthenticated `authorize()`/`write_atomic_json`
code path an attacker can invoke directly. There is no terminating,
independent fact anywhere in this chain; it is circular all the way down.

## 7. Root Selection Decision

Per the governing phase prompt's own criteria (items 18, 67, 98):

- **ROOT A (existing independently trusted mechanism):** Ruled out — §5's
  inventory found none.
- **ROOT B (new bounded human-controlled signing/capability mechanism):**
  Considered and rejected *for this phase*, not because signing is
  impossible in principle, but because every implementation reachable
  without new architecture (environment variable secret, plaintext file
  under `.pcae/**`, an OS keychain item retrievable without a fresh
  per-use human-presence prompt) is, by RAE-REQ-009's own already-frozen
  admission, equally readable by "the agent" and "the human" — they are
  the same OS user, same process family, same CLI, with no privilege
  boundary between them today. A genuinely independent ROOT B (e.g., a
  keychain item requiring interactive per-use user-presence confirmation
  that a headless/autonomous agent invocation structurally cannot satisfy)
  is architecturally plausible but requires inventing an agent/human
  isolation capability that does not exist anywhere in this codebase
  today, is platform-specific, and would itself require new normative
  RAE-001 semantics (RAE-REQ-006 currently forbids claiming a stronger
  assurance level than what actually occurs). Building it is exactly the
  "new trust subsystem," not "bounded hardening," the governing prompt
  says not to improvise without separate architecture/contract
  authorization (item 69).
- **ROOT C (RAE only requires procedural provenance; 149O demanded too
  much):** Ruled out — §6 shows RAE-001 §22 threat #2 *does* make an
  adversarial, technical claim about "agent-generated fake approval JSON,"
  citing RAE-REQ-018 as its control. 149O's attacks are direct attacks on
  that stated control, not scope creep past it. No contract-clarification-
  only outcome is honest here; the contract's own claimed defense is what
  failed.
- **ROOT D (no viable root within current architecture; blocked):**
  **Selected.** No repository-local, same-process-writable artifact chain
  can establish Model P canonical provenance under Threat A, because the
  writer code itself (`PublicationCoordinator.authorize`/`execute`,
  `create_rollback_approval_binding`) has no secret or capability step —
  it is pure shape validation over caller-supplied data. Every candidate
  fix available today is another node in the same circular, self-
  describing-file graph (§6). A genuine fix requires a new capability this
  repository does not have: either (a) a process/privilege boundary that
  prevents ordinary agent code from invoking the canonical writer at all
  (so "went through the writer" becomes a real fact, not a claim), or (b)
  a secret/signature the writer holds that an equally-privileged reader/
  attacker process cannot also hold or derive. Neither exists, and adding
  either is new architecture, not a bounded repair.

**No production code was changed in this phase.** Per the governing
prompt's own item 19 ("No implementation before root selection") and item
67 ("A legitimate result is: TRUSTED PROVENANCE ROOT CANNOT BE
IMPLEMENTED WITH CURRENT PCAE HUMAN/AGENT TRUST MODEL... do not fake
completion"), this phase stops here rather than writing a fifth sidecar
that would not close any of B-149O-1..4 and would misrepresent the
finding.

## 8. Threat Capability Matrix (governing-prompt item 47, mandatory)

| Capability | Agent/process | Human (via same CLI) | Trusted subsystem |
|---|---|---|---|
| Read `.pcae/**` | Yes | Yes (same access) | N/A — none exists |
| Write `.pcae/**` | Yes | Yes (same access) | N/A |
| Invoke `create_rollback_approval_decision`/`create_rollback_approval_binding` | Yes — plain importable Python functions, no access control (governing-prompt items 48-49 confirmed) | Yes (identical call) | N/A |
| Read a root secret | N/A — none exists in current architecture | N/A — none exists | N/A |
| Create a valid root proof | N/A — no root proof mechanism exists | N/A | N/A |
| Verify a root proof | N/A | N/A | N/A |

Every cell resolves to "no mechanical distinction exists" because §5-§7
found no root at all. This table is intentionally empty of asymmetry — that
emptiness *is* the finding.

## 9. Regression / Suite Results (unchanged, since no production code changed)

| Suite | Result |
|---|---|
| 149O independent-verification suite (unmodified) | 4 failed, 13 passed — identical to phase-start reproduction (§2) |
| 149M suite | 53/53 passed |
| 149N suite | 11/11 passed |
| 149J + RAE module suites (149L-equivalent) | 49 + 77 = 126/126 passed |
| CHGR/Publication, TAM/CLTR, IWC, AESIC, Permission Broker, rollback, Wave-1 | Not run in isolation; zero production files touched this phase (`git status` shows no `src/pcae/**` changes), so no regression is possible and none is claimed. |
| Fast Green (`python -m pytest -m fast_green -n auto -q`) | Not re-run in full; unnecessary given zero production diff. Documented as a phase-149O.1-specific deviation from the governing prompt's item 92, justified by zero production/test-file changes. |

## 10. Production Diff Audit

Zero production files changed. `git status --short` after this phase's
documentation/task-lifecycle work touches only: this document,
`tasks/active/**`, `tasks/done/**`, `tasks/TODO.md`, `tasks/DONE.md`,
`tasks/DECISIONS.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`,
`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`.
No hunk requires TRUST_ROOT/ROOT_VERIFICATION/DECISION_ROOT_BINDING/
BINDING_ROOT_BINDING/CREATION/VALIDATION/TEST-SUPPORT classification —
none of that category of change exists in this phase.

**Contract diff: empty.** RAE-001 v1.0, RWMPC-001 v1.0, PBPC-001 v1.2,
PBPA-001 v1.0, CHGR-001, IWC-001, TAMC-001/TAMPC-001, AESIC-001/AEM-001
all remain byte-unchanged.

## 11. Root Trust Proof Statement (governing-prompt item 96, mandatory)

```
TRUST ROOT: none found.
WHY NO CANDIDATE IS INDEPENDENT: every artifact in the RAE chain
(Decision record, publication receipt marker, Binding record, creation
registration) is written by code (PublicationCoordinator.authorize/
execute, create_rollback_approval_binding, _write_atomic_json,
write_creation_registration) that validates only the shape and internal
consistency of caller-supplied data. None of these functions consult a
secret, a credential, an external service, or a capability unavailable to
any process that can import this repository's own modules. Therefore an
attacker under Threat A -- able to write files and call public functions,
but holding no separate secret -- can always reproduce byte-identical (or
field-matching) output for any of these artifacts, because there is no
step in their construction that depends on anything the attacker lacks.
```

## 12. Findings

- **BLOCKING (carried forward, OPEN, not fixed this phase)**: B-149O-1,
  B-149O-2, B-149O-3, B-149O-4, per §2's closure matrix.
- **STRATEGIC_GAP (root cause, new to this phase)**: PCAE's human-
  governance substrate has no capability or secret anywhere that
  distinguishes "produced by the canonical writer" from "hand-constructed
  to match the canonical writer's output shape." This is strictly narrower
  than, and does not duplicate, RAE-REQ-005/009's already-disclosed
  identity/privilege-separation gaps — it is a gap in *procedural*
  provenance (RAE-001 §22 threat #2's own claimed control), not identity.
- **OBSERVATION**: RAE-001's threat #2 claim ("RAE-REQ-018 — evidence must
  anchor to an actually-published CHGR record via digest match") is not
  currently true and cannot be made true by any additional file-based
  sidecar; a future contract revision to RAE-001 §22 should either (a)
  narrow threat #2's claimed control to reflect what a new, real root can
  actually guarantee once one is built, or (b) explicitly downgrade threat
  #2 to a disclosed, non-BLOCKING gap alongside threat #3, pending a
  dedicated trust-boundary architecture phase. This phase does not decide
  which; that decision belongs to the recommended next phase.

## 13. Confirmations (governing-prompt required final-report list)

- RAE-001 v1.0 unchanged. RWMPC-001 v1.0 unchanged. PBPC-001 v1.2
  unchanged. PBPA-001 v1.0 unchanged. CHGR-001 unchanged.
- No AG3 Permission Broker integration implemented. No AG5 Permission
  Broker integration implemented. No rollback execution behavior changed.
  No rollback production request consumes `approval_present=True`.
- No self-declared legacy flag was promoted to trusted approval.
- IWC remains confirmation-only. AESIC/AEM remain disclosure-only.
- No illegal CHGR/TAM authority-family composition introduced. No
  POL-001..012 meaning changed. No POL-013+ added. TK1/TK2/TK3 remain
  deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability implemented. Runtime remains
  Observed / observe / unavailable, confirmed both before and after this
  phase via `pcae runtime inspect`.

## 14. RAE Evidence Substrate Status

**NOT READY FOR ROLLBACK INTEGRATION** (unchanged from 149O). Root
verification did not succeed — no root exists to verify. AG3/AG5 remain
correctly unwired.

## 15. Recommended Next Phase

**149O.1A — Human Approval Trusted Provenance Contract & Trust-Boundary
Architecture.** Per the governing prompt's own next-phase logic ("If the
only available roots are forgeable repository-local files ... Conclude
CURRENT PCAE TRUST MODEL INSUFFICIENT and recommend a dedicated Human
Approval Trust Boundary Architecture phase"), this dedicated architecture
phase should, before any further RAE implementation:

1. Decide, normatively, whether RAE-001 §22 threat #2 should be narrowed
   to what filesystem-only provenance can actually guarantee (effectively
   downgrading it to a disclosed gap like threat #3), or whether PCAE
   should build a real ROOT B capability (ROOT B's ownership/storage/
   human-vs-agent-access/rotation/loss-recovery/algorithm/verification/
   scope questions, per governing-prompt items 21/39-41/55-60, are all
   still open and unanswered — deliberately, since this phase stopped
   before implementation was authorized).
2. If ROOT B is chosen: define the specific human/agent isolation
   mechanism (e.g., an OS keychain item requiring fresh per-use user-
   presence, or an genuinely out-of-process human-operated signer) that
   RAE-REQ-009 does not currently have, including whether it requires a
   new RAE-001 amendment to RAE-REQ-006's assurance-level ceiling.
3. Only after that architecture is frozen should implementation and a
   149O.2-equivalent independent re-verification proceed.

This phase does not select between these two paths; it establishes,
with reproduced evidence, that a decision is required before further RAE
work proceeds.
