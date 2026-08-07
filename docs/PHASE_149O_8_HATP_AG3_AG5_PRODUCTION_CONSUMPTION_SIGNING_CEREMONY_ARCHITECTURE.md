# Phase 149O.8 — HATP AG3/AG5 Production Consumption + Signing-Ceremony Architecture

**Phase type:** architecture only. No production implementation, no contract
change, no CLI implementation, no hardware provisioning, no signing
execution, no Permission Broker enforcement implementation, no rollback
behavior change.

## 0. Baseline

Confirmed at phase start (see final report for exact command output):

- Repository clean, `origin/main..HEAD` = 0.
- Latest completed phase: 149O.7 (HATP Class-B Deployment / Activation
  Independent Verification) — `status: completed`, `report completeness:
  complete`, pushed.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy / passed
  / coherent.
- `pcae doctor task-memory`: pre-existing warnings only (a stale duplicate
  `tasks/active/*post-149o-6*.md` file and several `tasks/done/` entries
  missing from `tasks/DONE.md`), unrelated to and not introduced by this
  phase; not remediated here (out of this phase's allowed-file scope).
- `pcae runtime inspect`: `Observed / observe / unavailable`,
  `Permission Broker status: execution_unavailable`.
- HATP production: **NOT READY** —
  `inspect_hatp_verification_substrate_readiness(...).operational == False`
  on this deployment (same-OS-principal deployment; Class-B boundary not
  provisioned).
- B-149O-1..4: `INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY —
  SYSTEM EXECUTION CLOSURE DEFERRED` (149O.7).

## 1. Problem Statement

Waves 1-7 built a complete, independently-verified HATP proof/verification
substrate and a correct AG3/AG5 gated-authority adapter
(`src/pcae/core/hatp_ag_authority.py`) that derives a truthful
`approval_present` fact and forwards it to Permission Broker. Three things
are still missing, and 149O.8's job is to decide their target architecture
without implementing any of them:

1. **Evidence acquisition gap** — no CLI or other surface exists anywhere
   under `src/pcae/commands/` that lets a human produce a
   `HumanApprovalProvenanceProof` (zero references to
   `HumanApprovalProvenanceProof`, `hatp_evidence_id`, or
   `request_signature(` in `src/pcae/commands/`, confirmed by 149O.7 and
   re-confirmed here).
2. **Production consumption gap** — `pcae remote rollback approve` /
   `pcae remote rollback execute` (`src/pcae/commands/agent.py:2198`,
   `:2236`) never construct or pass `hatp_evidence_id` /
   `hatp_proof` / `hatp_evidence` to `agent.py`'s `execute_rollback` /
   `build_rollback_execution`, so the correct gated-authority adapter is
   never reached by the real CLI dispatch path. Real dispatch is governed
   solely by the pre-HATP preconditions: `rollback_approval_state ==
   "approved"` (a bare on-disk string mutated by `approve_rollback`,
   `agent.py:5146`, with no evidence, no identity check, no HATP, no PB
   call) for AG3, and PER status/divergence for AG5
   (`build_rollback_execution`, `agent.py:93952`).
3. **Execution enforcement gap** — even when the gated adapter *is*
   invoked directly (as Wave 6/7's own test suites do), its Permission
   Broker request is built with `simulation_only=True` unconditionally
   hardcoded (`hatp_ag_authority.py:153-174`), because Permission Broker
   Foundation has no execution boundary (`COMP-002`, `"Execution
   Boundary"`, `not_implemented`, `permission_broker_foundation.py:70`)
   anywhere in PCAE. POL-005 (`ExecutionDisabledRule`,
   `permission_broker_foundation.py:489-518`) unconditionally `DENY`s any
   `simulation_only=False` request, system-wide, not specific to HATP or
   rollback. So even a genuine `HATP VALID` + `PB ALLOW` result today is
   architecturally a policy simulation, never an executable grant.

These three gaps are independent and must not be conflated (§5).
Separately, a **deployment certification gap** exists: this repository's
own HATP substrate is `NOT_READY` (no Class-B host, no enrolled hardware
signer), which is out of scope for 149O.8 and constrains — but does not
block — the architecture decided here (§21).

## 2. Current Real Workflow (AG3 / AG5, as of 149O.7 baseline)

**AG3 (`agent.py`, `src/pcae/commands/agent.py`):**

```
pcae remote rollback approve <job-id>
  → approve_rollback(root, job_id)                     agent.py:5146
  → job["rollback_approval_state"] = "approved"
  → _write_job(...)                                     (bare on-disk mutation,
                                                          no identity check,
                                                          no evidence, no PB call)

pcae remote rollback execute <job-id>
  → run_remote_rollback_execute                         commands/agent.py:2236
  → execute_rollback(root, job_id)                       agent.py:5234
      preconditions: rollback_approval_state == "approved",
      eligibility, revert_commit mode, clean tree,
      commit reachability
  → git revert dispatch
```

The CLI wrapper calls `execute_rollback(HarnessPath.cwd(), args.job_id)`
with **no** `hatp_evidence_id` / `hatp_proof` / `hatp_evidence` arguments,
even though `execute_rollback`'s signature already accepts them
(keyword-only, default `None`). The function *can* take HATP inputs; the
CLI simply never supplies them.

**AG5:**

```
rollback request → PromotionExecutionRecord (PER) checks
  → build_rollback_execution(root, per_id, dry_run=False)   agent.py:93952
      precondition: PER status in _RER_PER_ELIGIBLE_STATUSES,
      divergence checks
  → dispatch
```

Same shape: `build_rollback_execution` accepts optional
`hatp_evidence_id` / `hatp_proof` / `hatp_evidence`, but nothing in the
current call graph supplies them.

## 3. Current Gated (HATP) Workflow — Where It Terminates

```
hatp_evidence_id, hatp_proof, hatp_evidence  (caller-supplied to
                                               execute_rollback /
                                               build_rollback_execution,
                                               if present)
  → resolve_ag3_gated_rollback_authority /
    resolve_ag5_gated_rollback_authority        hatp_ag_authority.py:177 / 224
      → resolves HATPTrustStore.production() +
        create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
        internally (NOT caller-injectable — F-2 closure)
      → resolve_rollback_approval_evidence_with_hatp   rollback_approval_evidence.py:1517
          → verify_hatp_proof(...)                     human_approval_trusted_provenance.py:762
          → approval_present = rae_approval_present
                                AND hatp_status == VALID
                                AND activation_operational
      → build_permission_broker_request(
            approval_present=approval_evidence.approval_present,
            simulation_only=True,                        # hardcoded
        )
      → PermissionBroker().evaluate(request)              → advisory decision only
  → GatedRollbackAuthorityResult{approval_evidence, permission_decision}
  → attached to execute_rollback / build_rollback_execution's RETURN VALUE
    ONLY, after the git revert / dispatch decision has already been made
    by the pre-existing precondition logic (additive, non-gating).
```

This path is **complete and independently verified through Permission
Broker decision provenance**, and terminates there: it is never invoked
by the real CLI, and even when invoked directly it cannot become an
executable grant (`simulation_only=True` is unconditional).

## 4. Gap Analysis (kept explicitly separate, per governing prompt §5)

| Gap | Description | Current state | What closes it |
|---|---|---|---|
| Evidence acquisition | No CLI/ceremony produces a `HumanApprovalProvenanceProof` | Absent entirely | §6-§14 (signing ceremony architecture) |
| Production consumption | Real CLI dispatch never calls the gated adapter | Gated adapter exists but is dead code on the real path | §16-§18 (AG3/AG5 mandatory consumption architecture) |
| Execution enforcement | PB decision cannot gate real dispatch | Blocked by `COMP-002 not_implemented`, system-wide | §19-§20 (deferred; depends on a separate initiative) |
| Deployment certification | This deployment's HATP substrate is `NOT_READY` | No Class-B host, no enrolled hardware signer | Out of scope for 149O.8 (§21, §26) |

The first two gaps can be closed **without** COMP-002 and without real
Class-B/hardware provisioning existing on this or any deployment — the
signing ceremony, evidence store, and mandatory-consumption code can all
be built and independently verified using the existing test-provider
seams already used by Wave 4-7 (outside the production code path). The
third gap is architecturally separate and explicitly deferred. The fourth
is an operational/certification concern, not a code architecture concern.

## 5. Signing-Ceremony Ownership (Q6, Q22, Q55-Q63)

**Decision: a dedicated command family, `pcae hatp sign ...`, separate
from `pcae remote rollback approve`.**

Evaluated against 149O.1D §71-72 ("Administrative Surface / Human
Approval Surface Naming... not decided by this plan, only that such
surfaces are architecturally separate from the agent's normal command
path") and against §32 of this plan ("Provider Replacement Prevention" —
the trusted provider profile must come from protected configuration, not
a runtime CLI parameter reachable by the agent).

Rejected alternatives:

- **B. `pcae remote rollback approve --hatp ...`** — folds a
  human-presence hardware ceremony into a command whose current identity
  is "flip an on-disk flag." Conflates *evidence creation* with
  *rollback authorization intent*, and makes it harder to keep "signing
  produced evidence" cleanly separate from "rollback dispatch consumed
  evidence" (§21 below explicitly requires this separation).
- **C. Fold into `pcae decision-session`** — `decision-session`
  (`src/pcae/commands/decision_session.py`) is IWC-001's human-in-the-loop
  ceremony, and its `preview → confirm(--preview-digest)` "no blind
  confirm" pattern is a useful **UX precedent** (§7 below reuses it), but
  its identity model is a **self-asserted `--as-identity` claim**,
  compared only against the session's own prior binding at the
  application layer (`decision_session.py:301-332`) — never against a
  protected trust store or OS principal. This is structurally weaker
  than HATP requires (HATP-REQ-077: signer/principal identity must always
  be cross-checked against the protected registry, never proof
  self-assertion). Reusing `decision-session`'s command surface would
  invite exactly the caller-supplied-identity pattern HATP-001 forbids.
- **D. Separate bootstrap/admin ceremony tool (outside `pcae`)** —
  rejected: it would fragment PCAE's single governed CLI surface and
  duplicate configuration/trust-store discovery logic that
  `hatp_bootstrap.py` already owns.

`pcae hatp sign` is chosen because: (a) it is naturally namespaced next
to the already-existing, non-CLI-exposed `HATPTrustStore.production()` /
`create_production_hardware_provider()` machinery (`hatp_providers.py`,
`hatp_bootstrap.py`) — i.e. it becomes the *first* CLI surface for a
component whose non-CLI-input resolution pattern already exists and is
independently verified; (b) it is unambiguously separate from the agent
command path (`pcae remote ...`, `pcae agent ...`), signalling
"admin/human surface" by naming convention alone; (c) it composes cleanly
per rollback site (`--site ag3` / `--site ag5`) without inventing a new
top-level namespace per site.

## 6. Human Initiation Boundary (Q7)

The signing ceremony's only entry point is an interactive, foreground
terminal invocation by a human: `pcae hatp sign rollback --site {ag3|ag5}
...`. No API, cron entry, daemon, or agent-invocable code path may call
into the hardware-signing step. This is already structurally enforced one
layer down: `HATPHardwareSigner.request_signature` "MUST NOT accept or
honor any caller-supplied presence boolean" (`hatp_providers.py:308`) and
the FIDO2 provider maps `human_presence_proven` directly to CTAP2's
`AuthenticatorData.FLAG.UP`, re-evaluated by the authenticator hardware on
every call (`hatp_fido2_provider.py:34-53`) — there is no in-process
value an agent could set to fake it. The architecture decision here is
process-level, not just protocol-level: the signing command must never be
invocable as a subprocess target from `agent.py`'s own dispatch code (no
`subprocess.run(["pcae", "hatp", "sign", ...])` anywhere in agent-facing
code), so an autonomous agent cannot even *attempt* silent signing and
have it fail loudly — it must have no code path that tries at all.
Stored reusable approval tokens are prohibited by the same reasoning as
HATP-REQ-017 ("unlock once, sign many" is explicitly non-compliant): each
signing invocation performs exactly one hardware touch producing exactly
one proof for exactly one operation.

## 7. Blind-Touch Defense / Proof Construction Ownership (Q9, Q10, Q11)

`pcae hatp sign rollback` owns proof construction and must reuse
`decision-session`'s **preview-then-confirm** pattern rather than
inventing a new one: the command first reconstructs the canonical
operation payload from durable state, displays it in full to the human,
and only requests the hardware touch after the human has seen exactly
what will be signed (149O.1D §29-32, "blind-touch defense" — never sign
an opaque agent-provided digest).

`HumanApprovalProvenanceProof` fields and their sources (all derived,
never typed by the human — see §8):

| Field | Source |
|---|---|
| `repository_instance_id` / `repository_id` | Resolved from the local repository's own identity record, the same source `verify_hatp_proof`'s `current_repository_id` parameter already uses today. Never CLI input. |
| `decision_record_id`, `decision_record_digest` | The CHGR Decision record governing this rollback, looked up from durable governance state (RAE Binding / rollback approval evidence), digested with the existing canonicalization used by RAE/CHGR. Never CLI input. |
| `binding_id`, `binding_digest` | The RAE `RollbackApprovalBinding` for this exact operation (`rollback_approval_evidence.py`), read live at signing time — not supplied by the caller. |
| `principal_id`, `signer_key_id` | Resolved by asking the hardware provider "who is signing" via its own credential/attestation exchange (FIDO2 `getAssertion` returns a credential ID that maps to a `principal_id` through the protected trust store — the same `HATPTrustStore.production()` mapping `verify_hatp_proof` already trusts), never a `--principal-id` flag. |
| `provider_profile` | Fixed to whatever `create_production_hardware_provider` resolved (`HATP_HARDWARE_PROVIDER_V1`, closed allowlist, `hatp_providers.py:353-391`); not selectable. |
| `operation_reference` (`job_id`+`original_commit_sha` for AG3; `per_id`+`ecp_id` for AG5) | Derived from the live job/PER record on disk, addressed by the one CLI argument the human *does* supply — the job/PER identifier — never free-typed digests or commit SHAs (§9). |
| `issued_at` | Wall-clock time at proof construction, supplied internally, never caller input (mirrors `verify_hatp_proof`'s existing discipline of never calling `datetime.now()` internally — the signing command is the one place a real clock read belongs). |

## 8. No User-Typed Security Fields (Q10)

The only CLI-supplied identifier for `pcae hatp sign rollback` is the
non-security-sensitive **operation locator** (`--job-id` for AG3,
`--per-id`/`--ecp-id` for AG5) — the same identifiers already used by
`pcae remote rollback approve`/`execute` today. Every digest, every
identity, every provider selection is derived server-side (i.e.
command-side, reading durable repository/trust-store state), exactly as
listed in §7. This eliminates `--decision-digest`, `--binding-digest`,
`--repository-id`, `--signer-key-id` as CLI surface entirely — there is
no legitimate reason for a human to type a digest by hand, and doing so
would reopen exactly the "proof self-assertion" failure mode HATP-REQ-077
forbids.

## 9. Operation Context Derivation (Q11)

For AG3: `job_id` is CLI input (locator only); `original_commit_sha` is
read from the job record itself (the same record `execute_rollback`
already reads for its own preconditions), never independently supplied.
For AG5: `per_id` is CLI input (locator only); `ecp_id` is read from the
live `PromotionExecutionRecord`. In both cases the human selects *which
operation* to sign for (by ID, exactly as they already do with `approve
<job-id>` today) but cannot select *what gets bound into the proof* for
that operation — the binding is mechanically derived, closing the
"human select arbitrary operation binding" risk named in §11 of the
governing prompt.

## 10. Signer / Provider Resolution (Q12, Q13)

Both delegate to existing, non-CLI-exposed production resolution and
introduce **no new selection surface**:

- Signer: resolved via the hardware provider's own credential exchange
  cross-checked against `HATPTrustStore.production()`'s trusted-approver
  mapping — the same mapping `resolve_ag3/ag5_gated_rollback_authority`
  already trust exclusively (`hatp_ag_authority.py:106-150`, no
  `hatp_trust_store` parameter exists on those functions at all). The
  signing command must call the identical `HATPTrustStore.production()`
  entry point, never construct its own trust store.
- Provider: `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`
  (`hatp_providers.py:353-391`) is the *only* resolution path the signing
  command may call. No `--provider test`/`--provider software`/arbitrary
  plugin-name flag may exist on `pcae hatp sign`, mirroring the fact that
  no such flag exists anywhere in `src/pcae/commands/` today (confirmed
  by grep). `TestHATPProofVerifierProvider` must never become reachable
  from this command, in any build configuration, environment variable, or
  flag (§59).

## 11. Evidence Output & Schema (Q14, Q86)

**Decision: reuse HATP-001's existing `HumanApprovalProvenanceProof` +
its provider `HATPVerificationEvidence` (the assertion bytes) as a single
combined evidence envelope, without a new schema.** Section 86 of the
prompt explicitly directs "prefer reuse... do not create HATP v2 schema
without contract need," and there is no contract need here: HATP-001's
proof already carries every replay-defense field consumption requires
(§ the contract summary above), and the provider assertion bytes are
already the thing `verify_hatp_proof` needs as `evidence.assertion`. The
signing command's output artifact is therefore:

```
HATPSignedEvidenceEnvelope = {
    proof: HumanApprovalProvenanceProof,     # canonical JSON, HATP-001 schema, unchanged
    provider_assertion: bytes,                # opaque to everything except the provider
    evidence_id: str,                         # see §12
}
```

No Wave-3 canonical signed payload byte layout changes.

## 12. Evidence Storage & ID Semantics (Q15, Q16, Q18, Q40, Q41)

**Storage: repository-local**, mirroring the architecture RAE-001 already
uses successfully (`rollback_approval_evidence.py`, `_DEFAULT_EVIDENCE_ROOT
= .pcae/rollback-approval-evidence/`, subdirectories `bindings/`,
`revocations/`, `creation-registry/`, exclusive-create writes via
`O_CREAT|O_EXCL`, atomic-write elsewhere). Proposed:

```
.pcae/hatp-evidence/
  envelopes/{evidence_id}.json        # HATPSignedEvidenceEnvelope, one file
  creation-registry/{evidence_id}     # empty marker file, O_CREAT|O_EXCL
```

This satisfies §71's framing directly: the location need not be secret —
integrity comes from the proof's own signature, not from filesystem
confidentiality (HATP-REQ-049: `repository_id` in the proof is "not a
secret and not a trust root"). Availability is not guaranteed (an agent
with file-modify capability could delete the envelope), which is
acceptable: deletion must result in **no approval** (§72), never a
fallback to a weaker path — this falls out for free, since a missing
`evidence_id` simply fails lookup and `resolve_*_gated_rollback_authority`
already treats missing evidence as `approval_present=False`
(`rollback_approval_evidence.py`'s existing fail-closed behavior).

**Evidence ID: `evidence_id = digest_hatp_proof_payload(proof)`** — the
proof's own canonical SHA-256 content digest
(`human_approval_trusted_provenance.py`'s existing
`digest_hatp_proof_payload`), not a freshly minted UUID. Rationale:

- **What it identifies**: exactly one immutable, canonical proof payload
  — content-addressed, so "the evidence" and "its identifier" cannot
  diverge.
- **Uniqueness**: guaranteed by the digest function already used
  elsewhere in HATP (SHA-256 collision-resistant); the
  `creation-registry/{evidence_id}` exclusive-create file provides a
  second, filesystem-level duplicate guard.
- **Immutable**: by construction — any mutation changes the digest,
  hence changes the ID, hence is a *different* evidence record, never an
  edit of an existing one. This directly satisfies §17 ("if file may be
  edited, signature verification must detect mutation") at the ID layer,
  before signature verification is even reached.
- **Lookup**: `evidence_id → envelopes/{evidence_id}.json`, O(1), exact
  match only. No "latest approval" lookup exists (§18 explicitly
  forbids this unless the contract permits it; HATP-001 does not).
- **Repository/deployment scoping**: the proof's own `repository_id`
  field (and eventual deployment-registration field) is already checked
  by `verify_hatp_proof`'s `current_repository_id`/`canonical_deployment_root`
  parameters at consumption time — the evidence ID itself does not need
  to be scoped, because the *content* it addresses is.
- **Multiple valid proofs for one operation** (§41): can occur (e.g. the
  human re-signs after a transient failure, producing a proof with a
  different `issued_at`). Selection semantics: **the consuming command
  must always be given an explicit `--hatp-evidence <id>`**; there is no
  implicit "pick the newest" behavior anywhere in the architecture. This
  also closes §40 (whether a user may select evidence ID: yes, but the
  consuming path re-verifies that the selected evidence's `operation_reference`
  matches the operation being dispatched — an explicit ID is never
  trusted blindly).

## 13. Evidence Mutability, Replay, Expiry (Q17, Q19, Q20, Q42-46)

- **Mutability**: immutable by the digest-as-ID design above (§12).
- **Replay defenses preserved unchanged**: Decision digest, Binding
  digest, operation reference, `repository_id`, `issued_at` — all already
  verified by `verify_hatp_proof` (`human_approval_trusted_provenance.py:762-926`)
  and the additional live-Binding cross-check in
  `resolve_rollback_approval_evidence_with_hatp`
  (`rollback_approval_evidence.py:1517-1635`). 149O.8 changes none of
  this logic; it only decides where the proof/evidence the CLI now
  produces gets consumed from.
- **Expiry**: governed by RAE-001's existing 24h `expires_at` TTL
  (HATP-REQ-084 — HATP does not introduce a second, independent TTL).
  If evidence has expired by the time `pcae remote rollback execute
  --hatp-evidence <id>` runs, `resolve_*_gated_rollback_authority`
  already yields `approval_present=False` through the existing RAE
  freshness check — no new expiry logic is required, only the wiring
  in §16-18. **No stale cached success**: because `approval_present` is
  recomputed on every consumption attempt (never persisted as a boolean
  anywhere), a Decision supersession, Binding supersession, signer
  revocation, or authority revocation *after* signing is caught at
  consumption time automatically (Q42-46) — this is already true of the
  existing gated-authority machinery and 149O.8 introduces no new caching
  layer that could undermine it.

## 14. Signing vs. Execution Separation (Q21, Q62-64)

**Decision: signing and execution remain separate lifecycle steps.**
`pcae hatp sign rollback` only ever writes an evidence envelope; it never
calls `execute_rollback` / `build_rollback_execution`, and the reverse
command never performs a hardware touch. This is evaluated against
just-in-time signing (touch-immediately-before-execute) and rejected as
the *default* model for these reasons:

- **Auditability**: a separate signing step produces one artifact whose
  existence is itself an audit record, independent of whether execution
  ever happens or succeeds. JIT signing folded into `execute` would mean
  a failed execute after a successful touch either discards the proof
  (wasting a scarce physical-presence event) or requires the execute
  command to also own evidence persistence, blurring ownership.
- **Freshness**: already governed by RAE's 24h TTL (§13) — the
  separation does not create a materially larger freshness risk, since
  expired evidence fails at consumption regardless of how close together
  the two steps happened to occur.
- **Human intent clarity**: a distinct "I am approving this operation"
  action (signing) is easier to reason about, log, and — eventually —
  subject to its own PB `POL-004` evaluation, than an approval implicitly
  bundled inside a dispatch command whose primary job is "make the
  change happen now."
- **Replay resistance**: unaffected either way (proof structure carries
  the same fields).
- **Operational ergonomics**: the cost is one extra command invocation,
  which is a deliberate friction point commensurate with rollback being a
  human-approval-gated, security-relevant action (POL-004's entire
  purpose).

**Offline/pre-signed approval is explicitly permitted** by this
architecture (§13; HATP-001 does not require same-session
production/consumption — see contract summary). A future execute-time
`--wait-for-touch` convenience flag that internally invokes sign-then-execute
in one interactive session may be layered on top later without changing
this separation at the architecture level, but is not designed here.

## 15. `pcae remote rollback approve` — Future Disposition (Q22, Q23)

**Decision: (D) deprecated, on a defined migration timeline, replaced by
`pcae hatp sign rollback`.** Not (A) hard-replaced immediately (would
break today's only working rollback path the instant this phase's
follow-on implementation ships, before Class-B/hardware is provisioned
anywhere — see §21's deployment-conditional cutover), not (B) an
orchestration wrapper around HATP signing (would reintroduce a
"one-command ceremony" that this architecture explicitly avoids for
auditability reasons, §14), not (C) "remain for legacy/non-HATP workflows
indefinitely" (would create a permanent second authority path — forbidden
by §56/§98), not (E) alone (metadata-only retention needs an explicit
sunset, not just a relabeling).

**`rollback_approval_state`'s future semantics** (Q23): three-stage,
matching §57's migration-order guidance and §98's "no dual authority"
constraint:

1. **Today → mandatory-consumption ships**: sole authority, unchanged.
2. **Mandatory-consumption ships, this deployment's HATP substrate still
   `NOT_READY`**: `rollback_approval_state` remains the sole *effective*
   authority (§21 — HATP structurally cannot ever be `VALID` on a
   `NOT_READY` substrate, so there is no live second path, only a
   dormant one), but `pcae remote rollback approve` now emits a
   deprecation warning on every invocation, and `execute` begins
   accepting (but not yet requiring) `--hatp-evidence`.
3. **This deployment's HATP substrate reaches `operational=True`** (a
   fact derived from `inspect_hatp_verification_substrate_readiness`,
   never a caller flag): a **one-way governance latch** flips (§21) —
   from that point forward, `execute` refuses dispatch without valid
   `--hatp-evidence`, and `rollback_approval_state` becomes
   **metadata-only** (informational field on the job record, no longer
   read by any precondition). The latch does not un-flip if the substrate
   later regresses to `NOT_READY` (e.g., hardware revoked) — regression
   should *block* rollback entirely, not silently reopen the weaker path.

`pcae remote rollback approve` itself is removed (hard deprecation, not
kept indefinitely as a no-op) once stage 3 is reached for a given
deployment, since a command whose entire effect is "flip a field that
dispatch no longer reads" is actively misleading to keep around.

## 16. AG3 Target Production-Consumption Architecture (Q24)

```
pcae hatp sign rollback --site ag3 --job-id <id>
  → preview canonical operation payload (job_id, original_commit_sha,
    Decision, Binding — all derived, §7-9)
  → human confirms preview
  → hardware touch (production provider only, §10)
  → HATPSignedEvidenceEnvelope written to
    .pcae/hatp-evidence/envelopes/{evidence_id}.json           (§12)
  → prints: "HATP proof created: <evidence_id>"

pcae remote rollback execute <job-id> --hatp-evidence <evidence_id>
  → run_remote_rollback_execute (commands/agent.py)
  → execute_rollback(root, job_id,
        hatp_evidence_id=<evidence_id>,      # NOW SUPPLIED BY THE CLI —
        hatp_proof=<loaded from envelope>,    # this is the wiring gap
        hatp_evidence=<loaded from envelope>) # this phase identifies;
                                               # implementation is a
                                               # later phase (§27)
  → resolve_ag3_gated_rollback_authority(...)              (unchanged)
  → approval_present derived, PB evaluated (advisory, unchanged)
  → PRECONDITION (post-mandatory-consumption, §15 stage 3):
        require approval_present == True
        (rollback_approval_state no longer read)
  → git revert dispatch (unchanged mechanism; gate changes, not the
    dispatch mechanism itself)
```

Before the deployment-conditional latch flips (§15 stage 2), `--hatp-evidence`
is accepted and its `permission_decision`/`approval_evidence` are recorded
for observability (as Wave 6/7 already do), but the dispatch precondition
remains `rollback_approval_state == "approved"` — no behavior change
until the latch flips.

## 17. AG5 Target Production-Consumption Architecture (Q25)

Same shape, different operation locator and eligibility check — AG3 and
AG5 storage/command surfaces are **not** assumed identical (per the
governing prompt's explicit instruction):

```
pcae hatp sign rollback --site ag5 --per-id <id> --ecp-id <id>
  → (ecp_id may be auto-derived from the live PER record rather than
     requiring the human to supply it separately, if the PER
     unambiguously identifies one ECP; TBD at contract-freeze time, §27)
  → same preview/touch/persist flow as AG3

<AG5 execution entry point, currently build_rollback_execution,
 exposed via whatever CLI wraps it — inspect at contract-freeze time
 whether a `pcae remote rollback execute` equivalent exists for AG5 or
 whether AG5 dispatch is reached through a different command; this
 phase confirms build_rollback_execution's Python signature already
 accepts hatp_evidence_id/hatp_proof/hatp_evidence (agent.py:93952) but
 does not confirm which CLI entry point calls it — that inventory is
 §27 work, not resolved here>
  → resolve_ag5_gated_rollback_authority(...)
  → PER-status/divergence precondition, extended post-latch with
    approval_present requirement, exactly mirroring AG3's stage 3
```

## 18. Missing / Invalid Evidence, NOT_READY Behavior (Q26-28, Q74-76)

All three follow the existing, already-verified vocabulary — 149O.8 adds
no new status enum (§75's instruction: "do not invent one giant status
enum unnecessarily"), only decides how the *CLI* surfaces the outcome:

| Condition | HATP/RAE fact | PB outcome (existing, unchanged) | CLI/dispatch behavior (this phase's decision) |
|---|---|---|---|
| No `--hatp-evidence` supplied, post-latch | `approval_present = False` | `HUMAN_REVIEW` (POL-004) | `execute` refuses dispatch, exit non-zero, message distinguishes "no evidence supplied" from other failures — never silently falls back to `rollback_approval_state` |
| `--hatp-evidence` points to non-`VALID` proof (any of the 13 HATP-001 verification statuses) | `approval_present = False` | `HUMAN_REVIEW` | `execute` refuses dispatch; error message surfaces the specific HATP status (`MALFORMED`, `EXPIRED`, `REVOKED_SIGNER`, etc.) — not collapsed into one generic "invalid" |
| Substrate `NOT_READY` (`inspect_hatp_verification_substrate_readiness().operational == False`) | HATP status cannot reach `VALID` structurally | `HUMAN_REVIEW` | Pre-latch: irrelevant (legacy path still authoritative). Post-latch: `execute` refuses unconditionally — this is the expected, correct outcome of §15's one-way latch design, not a bug to work around |

`HATP VALID` never directly decides execution (§27, reaffirming
HATP-REQ-102/104): every one of these rows still routes through
`approval_present` → Permission Broker, even though PB itself remains
advisory until COMP-002 exists (§19).

## 19. Permission Broker: Advisory → Enforced Transition (Q29-38, Q79-82)

**149O.8 does not modify `ExecutionDisabledRule`/POL-005, `simulation_only`,
or any Permission Broker behavior** (explicit prompt constraint, §32).
This section defines *prerequisites* for a future change only.

**COMP-002** (Q30, Q80): defined in the `COMPONENT_REGISTRY`
(`permission_broker_foundation.py:70`) as `"Execution Boundary"`,
`not_implemented`, system-wide — not HATP-specific, not rollback-specific.
It is the single blocker `permission_broker_foundation.py`'s own module
docstring and `hatp_ag_authority.py`'s own module docstring both name as
the reason PB is advisory everywhere in PCAE today, not just for
rollback. `hatp_ag_authority.py` actually requests component
`COMP-008` ("Rollback Boundary", also `not_implemented`) — a distinct,
narrower registry entry.

**Q81 (execution-gate ownership — wait for general COMP-002, or introduce
a rollback-specific enforcement adapter earlier?): recommendation is to
wait for COMP-002.** Reasoning: POL-005's `ExecutionDisabledRule`
(`permission_broker_foundation.py:489-518`) checks `request.simulation_only`
unconditionally and is not parameterized by `requested_component` — it
denies *any* real request system-wide, citing invariant `NG-025` and
component `COMP-002` specifically, not `COMP-008`. A "rollback-only"
enforcement adapter that flips `simulation_only=False` for rollback
requests while POL-005 still fires as written would simply be denied by
POL-005 — it would not bypass it (which is correct and safe), but it also
would not actually enable rollback enforcement. The *only* way to enable
rollback-specific enforcement earlier than general COMP-002 would be to
narrow POL-005 itself (e.g., scope its invariant to component-specific
execution boundaries), which is a **policy change** requiring its own
governance review — explicitly out of scope here (§32) and, more
importantly, would weaken a system-wide invariant (`NG-025`) for the
narrow benefit of one execution class, which this architecture does not
recommend absent a dedicated review of that trade-off. **Therefore: PB
enforcement for rollback waits for general COMP-002**, tracked as a
dependency, not built as a rollback-specific shortcut.

**Future enforced target** (Q31, unchanged from today's semantics, simply
finally live once COMP-002 exists): `PB ALLOW → execution may continue`;
`PB DENY → execution blocked`; `PB HUMAN_REVIEW → execution blocked,
held for human resolution` (§35 below).

**Failure at the PB boundary** (Q34): broker unavailable, exception,
unknown decision, or missing policy must all resolve to **no rollback
dispatch** once enforcement exists — fail-closed, consistent with PB
Foundation's existing fail-closed empty-registry behavior
(`permission_broker_foundation.py`, decision composition precedence
`DENY > HUMAN_REVIEW > ALLOW`).

## 20. HUMAN_REVIEW Handoff (Q35, Q36)

HATP signing establishes **approval evidence only**; it does not itself
resolve `HUMAN_REVIEW`, because PB independently evaluates every
applicable policy (POL-001 through POL-012), several of which are
unrelated to approval (missing active task, missing evidence, unknown
capability/component). A `VALID` HATP proof satisfies POL-004
specifically; `HUMAN_REVIEW` can still legitimately fire for other
reasons even with perfect HATP evidence present. This phase does not
design the human-facing `HUMAN_REVIEW` resolution workflow (no such
workflow exists yet for *any* PB-gated action in PCAE, not just
rollback) — it notes this as an explicit dependency for the future
enforcement phase (§27, item G/H) rather than inventing one now, since
inventing it prematurely risks conflicting with whatever general PB
human-review UX PCAE eventually adopts for non-rollback actions.

## 21. Deployment-Conditional Cutover / Cross-Principal Flow (Q28, Q50, Q66-70)

This is the single most important operational constraint this
architecture must respect: **this repository's own HATP substrate is
`NOT_READY` today**, and there is no other deployment where it is ready.
If the mandatory-consumption cutover (§15 stage 3) were unconditional
rather than latched on live substrate readiness, shipping the
implementation phases (§27) would **permanently disable all rollback
capability** the moment they merged, since `approval_present` could never
become `True` anywhere. This is why §15's latch is keyed to
`inspect_hatp_verification_substrate_readiness().operational`, a fact
derived from protected trust-store state — not a code-deploy event and
not a caller-settable flag — and why §50's tension ("should the ceremony
refuse early, or allow proof creation with later non-operational
verification?") resolves in favor of: **the signing command may still
attempt to produce a cryptographic proof even when the substrate is
`NOT_READY`** (useful for testing/dry-run against a synthetic conformant
substrate, exactly as Wave 6/7's own test suites already do), but
production approval remains unavailable — `approval_present` stays
`False` — until the substrate genuinely reaches `operational=True`. The
alternative (refuse proof creation outright when `NOT_READY`) would block
legitimate pre-provisioning rehearsal/testing without adding any real
security benefit, since `approval_present` is independently re-derived
at consumption time regardless of what happened at signing time.

**Cross-principal flow (Q66-70)**: Class-B means the human/admin
principal differs from the agent principal. The signing ceremony runs
under the **human/admin OS principal**, not the agent's. This repository
currently violates that separation (same-OS-principal deployment, which
is precisely why substrate is `NOT_READY` — HATP-REQ-029/092). The
architecture must therefore assume, for any deployment where signing
*does* work, that `pcae hatp sign` executes on a workstation or under an
OS account the agent process cannot write to, and that evidence produced
there needs to reach the agent-facing PCAE process. **This phase does not
select a specific IPC mechanism** (protected spool vs. explicit file
handoff vs. local service) — per §69's explicit "do not implement yet,"
this is deferred to the deployment-certification track (§26/§95), since
it depends on the concrete Class-B topology being provisioned, which is
out of scope here. The trust assumption is stated for later phases to
build against: evidence itself can move over an untrusted channel (its
integrity comes from the signature, not the channel — §70), but the
protected trust-store/provider configuration that produced it must never
cross that channel in the reverse direction.

## 22. Migration Strategy & Feature-Flag Constraint (Q55-58)

Sequence (also see §27's phase breakdown):

1. Build the signing/evidence surface (`pcae hatp sign`, evidence store) —
   inert until wired to consumption.
2. Wire `pcae remote rollback execute` to accept and evaluate
   `--hatp-evidence` (observability only, dispatch precondition
   unchanged) — this is stage 2 of §15.
3. Keep PB advisory throughout (unaffected by COMP-002 status).
4. The one-way latch (§21) removes legacy `rollback_approval_state`
   authority *per deployment*, automatically, once that deployment's
   substrate reaches `operational=True` — no flag, no manual "enable
   HATP" switch that could be left off in production or defaulted on
   in an unready environment.
5. Implement PB execution enforcement only once COMP-002 exists
   (separate track, §19).
6. Independently verify each stage before the next ships (§27).
7. Provision real Class-B + hardware per deployment (operational
   concern, not a code phase).
8. Certify production per deployment.

**No feature flag is introduced that can disable HATP enforcement once
the latch has flipped for a given deployment.** Any flag this
architecture does introduce (e.g., a `--dry-run`/synthetic-substrate
testing mode for `pcae hatp sign`, useful pre-provisioning) must only
ever make behavior *stricter or equivalent*, never weaker than what the
live substrate state would otherwise produce — consistent with §58's
"any flag must fail toward stronger governance, not weaker," and
explicitly ruling out anything resembling a `PCAE_DISABLE_HATP=1`
production escape hatch.

## 23. Audit, Secrets, Non-Interactive Use (Q47-49, Q77-78)

- **Audit events** (Q47): signing attempt, successful signing, failed
  signing, verification, PB evaluation, and dispatch decision should each
  produce a durable, append-only record — reusing PCAE's existing
  provenance-event mechanism (the same one `pcae session bootstrap`
  already reports event counts from) rather than inventing a parallel
  audit log. Logs are not authority (§47 explicit instruction) — the
  evidence envelope and PB decision remain the sole authoritative
  artifacts; audit events are observational.
- **Secret handling** (Q48): no private key or PIN is ever stored in the
  proof/evidence envelope, ever passed as a CLI argument, ever written to
  a repo file, log, or phase report. If the hardware provider requires a
  PIN, it must be collected through the provider's own out-of-band secure
  input path (the same mechanism FIDO2/CTAP2 already uses for PIN entry
  at the OS/authenticator level), never through `pcae`'s own argument
  parsing or stdin capture in a way that could be logged.
- **Hardware absent** (Q49): `pcae hatp sign` must report "no hardware
  provider available" clearly (mirrors `discover_hardware_providers()`'s
  existing availability reporting, `hatp_providers.py:312-350`) with no
  software fallback of any kind.
- **Automation/non-interactive use** (Q77-78): because HATP requires
  fresh physical presence per signing (§6-8), no autonomous or
  unattended rollback path can ever complete signing itself. Once the
  mandatory-consumption latch flips for a deployment (§15 stage 3), fully
  unattended production rollback becomes structurally impossible without
  a prior, separately-timed human signing step — this is a deliberate
  consequence of the architecture, not a gap to close. The PCAE v0.2
  autonomy contract's treatment of human-approval-gated actions already
  anticipates exactly this shape (approval as an explicit, non-bypassable
  human checkpoint); 149O.8 does not need to amend it, only confirms
  rollback now has a concrete instance of that checkpoint once these
  phases ship.

## 24. Trust-Boundary Diagram (Q89)

```
┌─────────────────────────────┐
│ Human / Admin Principal      │  human-controlled
│  (distinct OS principal,     │
│   Class-B deployments)       │
└──────────────┬───────────────┘
               │ invokes (foreground, interactive only)
               ▼
┌─────────────────────────────┐
│ pcae hatp sign rollback      │  human-controlled process,
│  (new, this architecture)    │  root/admin-adjacent config access
└──────────────┬───────────────┘
               │ resolves (no caller input accepted)
               ▼
┌─────────────────────────────┐
│ HATPTrustStore.production()  │  root/admin-controlled
│ create_production_hardware_  │  (protected trust store,
│  provider()                  │   hatp_bootstrap.py)
└──────────────┬───────────────┘
               │ requests touch
               ▼
┌─────────────────────────────┐
│ Hardware provider            │  hardware-controlled
│  (FIDO2 authenticator)       │  (physical presence, non-exportable key)
└──────────────┬───────────────┘
               │ produces
               ▼
┌─────────────────────────────┐
│ HATPSignedEvidenceEnvelope   │  public/untrusted artifact
│  (.pcae/hatp-evidence/)      │  (integrity via signature only;
│                               │   agent-writable location, agent
│                               │   CANNOT forge valid contents)
└──────────────┬───────────────┘
               │ referenced by --hatp-evidence <id>
               ▼
┌─────────────────────────────┐
│ pcae remote rollback execute │  agent-controlled invocation,
│  → resolve_*_gated_authority │  but derives, never accepts,
│  → verify_hatp_proof         │  approval_present
└──────────────┬───────────────┘
               │ approval_present (trusted derived fact)
               ▼
┌─────────────────────────────┐
│ Permission Broker             │  sole permission-decision engine
│  (advisory until COMP-002)   │  (permission decision, not authority
└──────────────┬───────────────┘   over execution capability itself)
               │ decision (ALLOW/DENY/HUMAN_REVIEW)
               ▼
┌─────────────────────────────┐
│ Execution Enforcement         │  future: root/admin-controlled
│  Boundary (COMP-002)          │  execution boundary (not built yet)
└──────────────┬───────────────┘
               │ (today: no gate here — dispatch proceeds on legacy
               │  precondition; future: gated on PB decision)
               ▼
┌─────────────────────────────┐
│ Rollback Dispatch             │  effect (git revert / file restore)
│  (execute_rollback /          │
│   build_rollback_execution)  │
└───────────────────────────────┘
```

## 25. Dataflow Table (Q90)

| Item | Producer | Consumer | Trust classification | Persistence | Mutation authority |
|---|---|---|---|---|---|
| `HumanApprovalProvenanceProof` | `pcae hatp sign` (human + hardware) | `verify_hatp_proof` | Untrusted claim until verified | `.pcae/hatp-evidence/envelopes/{id}.json` | None post-write (immutable by digest-ID design) |
| Provider assertion (evidence bytes) | Hardware provider | `verify_hatp_proof` via `evidence.assertion` | Untrusted claim until verified | Same envelope file | None post-write |
| `evidence_id` | `digest_hatp_proof_payload(proof)` | CLI (`--hatp-evidence`), evidence store lookup | Derived, content-addressed | Filename/registry key | Immutable (content-addressed) |
| Decision digest, Binding digest | CHGR / RAE (existing) | `verify_hatp_proof`, live Binding cross-check | Trusted governance fact | Existing CHGR/RAE stores, unchanged | Governed by CHGR/RAE lifecycle, unchanged |
| `approval_present` | `resolve_*_gated_rollback_authority` (recomputed every call) | `build_permission_broker_request` | Trusted derived fact | Never persisted as a standalone boolean | N/A — always recomputed |
| PB decision | `PermissionBroker().evaluate()` | Dispatch precondition (future, post-COMP-002) | Permission decision | Not persisted as authority (may be logged for audit) | N/A |
| Execution authorization | Future COMP-002 boundary | Dispatch | Runtime fact, separate from PB decision | N/A — does not exist yet | N/A |
| Dispatch (git revert) | `execute_rollback` / `build_rollback_execution` | Repository state | Effect | Git history | Governed by existing rollback mechanics, unchanged |

## 26. Authority Table (Q91)

| Concept | What it is | What it is NOT |
|---|---|---|
| `HumanApprovalProvenanceProof` | A claim/evidence artifact — cryptographic proof a specific human touched hardware for a specific operation | Not itself authority; not permission; not approval until verified |
| HATP `VALID` | A verified trust fact about the proof (structural + cryptographic + identity + operation-binding correctness) | Not a permission decision; does not map directly to PB `ALLOW` (HATP-REQ-102) |
| `approval_present` | A RAE/HATP-activation-derived governance fact, computed fresh on every evaluation | Not cached, not itself a dispatch decision |
| PB decision (`ALLOW`/`DENY`/`HUMAN_REVIEW`) | Permission Broker's own decision, combining `approval_present` with all other applicable policies | Not an execution capability; today, always advisory (`simulation_only=True`) |
| Execution capability (COMP-002) | A separate, system-wide runtime fact about whether real execution can happen at all | Not owned by HATP, not owned by rollback; a PCAE-wide dependency |
| Dispatch | The effect (git revert / file restore) | The only thing all of the above exist to gate correctly |

## 27. Implementation Phase Breakdown (Q92) and Dependency Graph (Q93)

```
149O.8   Architecture (this phase) ─────────────────────────────┐
                                                                    │
149O.9   HATP Signing Ceremony + Evidence Store Contract Freeze   │  depends on: 149O.8,
         (freeze command surface, envelope schema — reuses         │  HATP-001 (Waves 1-7)
          HATP-001, no new proof/verification contract)            │
              │                                                    │
              ▼                                                    │
149O.10  Signing Ceremony Implementation                          │  depends on: 149O.9,
         (pcae hatp sign rollback, evidence store code;             │  hatp_providers.py,
          no dispatch wiring)                                      │  hatp_bootstrap.py
              │                                                    │
              ▼                                                    │
149O.11  Signing Ceremony Independent Verification                │  depends on: 149O.10
              │
              ▼
149O.12  AG3/AG5 Mandatory HATP Consumption Contract               depends on: 149O.11,
         (freeze: execute --hatp-evidence wiring, latch semantics,  hatp_ag_authority.py
          rollback_approve deprecation timeline)                   (Wave 6/7, unchanged)
              │
              ▼
149O.13  AG3/AG5 Mandatory Consumption Implementation               depends on: 149O.12
         (execute wiring both stages of §15's latch;
          rollback approve deprecation warnings, then removal
          once a given deployment's latch flips)
              │
              ▼
149O.14  Independent Verification                                  depends on: 149O.13
         (adversarial: confirm legacy bypass impossible once
          latched; confirm B-149O-1..4 progress — see §28)

── separate, parallel track, not blocking 149O.9-149O.14 ──

[COMP-002 initiative]  Execution Boundary                          depends on: (its own,
   (owned outside HATP/rollback; see §19)                           PCAE-wide track)
              │
              ▼
[PB-ENF-A]  PB Execution-Gate Architecture (design, post-COMP-002) depends on: COMP-002 existing
              │
              ▼
[PB-ENF-B]  Enforcement Implementation                              depends on: PB-ENF-A,
                                                                      149O.13 (so there is
                                                                      something to enforce)
              │
              ▼
[PB-ENF-C]  Independent Verification of enforcement                 depends on: PB-ENF-B

── separate, per-deployment, not a numbered code phase ──

[DEPLOY-A]  Real Class-B + Hardware Deployment Certification         depends on: 149O.14
             (per deployment; unblocks that deployment's §21 latch)
```

## 28. B-149O-1..4 System-Closure Gate (Q53, Q94)

All of the following are required, and none alone is sufficient:

1. Signing/evidence-acquisition surface exists (149O.10-11).
2. AG3 mandatorily consumes gated approval — no bypass path — for at
   least one deployment whose latch has flipped (149O.13-14).
3. AG5 mandatorily consumes gated approval, same condition.
4. Legacy `rollback_approval_state` cannot independently authorize once
   latched (149O.13, one-way latch design, §15).
5. Historical B-149O-1..4 attacks demonstrated blocked through the
   **actual CLI workflow** (not just the gated-authority function
   directly, as Wave 6/7 tested) — this is the specific gap 149O.7 named
   ("real CLI dispatch path never reaches the gated adapter").
6. Independent adversarial verification confirms 1-5 (149O.14).

Meeting 1-6 **without** PB enforcement (i.e., before COMP-002 exists)
justifies a new, more precise intermediate adjudication:

```
B-149O-1..4:
INDEPENDENTLY VERIFIED AT MANDATORY CONSUMPTION BOUNDARY
— PB EXECUTION ENFORCEMENT DEFERRED (COMP-002)
```

— one notch stronger than today's `HATP-GATED AUTHORITY BOUNDARY`
language, since the real CLI would by then require the gated path rather
than merely offering it. Full closure —

```
B-149O-1..4:
INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM EXECUTION BOUNDARY
```

— additionally requires PB `DENY`/`HUMAN_REVIEW` to actually block real
dispatch (PB-ENF-A/B/C above), which depends on COMP-002 and is not
targeted by any 149O.9-14 phase.

## 29. HATP Production-Certification Gate (Q95, kept separate from B-149O-1..4 closure)

Distinct from code-architecture closure above; required per deployment
before that deployment's `operational=True` (and hence its §21 latch)
can honestly flip:

- Real Class-B OS-principal separation provisioned.
- Real hardware signing device enrolled.
- Credential enrollment completed against the protected trust store.
- Hardware non-exportability evidence obtained.
- Real physical-touch test executed (not synthetic/test-provider).
- Production trust-store provisioning completed.
- Production credential-store provisioning completed.
- Repository binding (`repository_id`) established for that deployment.
- A real signing ceremony successfully produces `VALID` evidence.
- Mandatory consumption (149O.13) already shipped.
- PB enforcement, where the architecture requires it (post-COMP-002),
  already shipped for that deployment's execution boundary.
- Independent verification of all of the above for that specific
  deployment.

Implementation-complete (149O.9-14 shipped) is **not** the same as
production-certified (this list, per deployment) — the two must never be
conflated in status reporting.

## 30. Blocking-Architecture Self-Check (§98 of governing prompt)

Explicitly confirmed this architecture proposes none of the following:

- Caller-supplied `approval_present` as authority — never; always
  recomputed from verified facts (§7, §26).
- Legacy OR HATP dual authority — the one-way latch (§15, §21, §22)
  ensures exactly one live authority at any time, chosen by
  non-caller-controlled substrate state.
- Software/test provider production fallback — never reachable from
  `pcae hatp sign` (§10).
- Agent-completable approval without human touch — structurally
  impossible (§6).
- Automatic/silent agent signing — no code path exists for it (§6).
- Cached HATP `VALID` as persistent authority — `approval_present`
  recomputed every evaluation, never cached (§13, §26).
- Storing PB `ALLOW` and trusting it later without reevaluation — not
  proposed; PB is (and remains) evaluated fresh at consumption.
- Direct HATP `VALID` → dispatch, or direct `approval_present` → dispatch
  without PB — both explicitly routed through PB in every flow described
  (§16-18).
- PB `ALLOW` bypassing execution-capability checks — future enforcement
  explicitly gated on COMP-002 (§19), not designed to bypass it.
- Weakening POL-005 to make rollback work — explicitly rejected (§19,
  Q81 analysis).
- Environment flags disabling HATP enforcement — explicitly rejected
  (§22).
- Missing evidence falling back to legacy approval — explicitly refused,
  fail-closed (§18).
- "Latest arbitrary evidence" without exact operation binding — explicit
  ID required, re-checked against operation reference (§12).
- Real deployment claimed ready without Class-B + hardware evidence —
  §29's gate kept explicitly separate from code-architecture closure.

## 31. Risks

- **Operational risk of a botched latch condition**: if
  `inspect_hatp_verification_substrate_readiness` ever has a bug that
  reports `operational=True` prematurely, the latch (§15/§21) would
  irreversibly disable legacy rollback approval on a deployment that
  isn't actually ready, with no automatic path back. Mitigation: this
  function is already independently verified (Wave 4/7) as a pure,
  non-caller-influenced conjunction; 149O.11/149O.14 should include a
  dedicated adversarial test of the latch transition itself, not just
  the individual HATP checks.
- **AG5 CLI entry-point inventory gap**: this phase confirms
  `build_rollback_execution`'s Python signature already accepts HATP
  parameters, but did not exhaustively confirm which CLI command(s)
  reach it in production (§17 notes this explicitly as deferred to
  149O.9-12 contract-freeze work). Treat as an open item, not an
  assumption.
- **IPC/cross-principal mechanism undecided**: §21 explicitly defers the
  concrete evidence-handoff channel for genuinely cross-principal
  deployments; any future phase implementing this must revisit trust
  assumptions once a specific mechanism is chosen.
- **COMP-002 timeline unknown**: PB enforcement (§19, §28's full closure)
  has no committed timeline; rollback's mandatory-consumption work
  (149O.9-14) should proceed independently rather than being blocked on
  it, per this phase's explicit recommendation.

## 32. Retained Findings (not closed by this phase)

- B-149O.3-1, B-149O.3-3, B-149O.3-8 — NON-BLOCKING (149O.7).
- F-3 — stale boundary-test debt, still open (carried since 149O.5).
- Python 3.9 `datetime.fromisoformat` portability debt (149O.7).
- xdist infrastructure debt (pre-existing).
- Real hardware not exercised (unchanged — no hardware touched this
  phase, architecture only).
- B-149O-1..4 — remain `INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED` (unchanged by this
  phase; §28 defines the path to the next, stronger adjudication).

## 33. Recommended Next Phase

Per the governing prompt's own decision logic: a coherent
signing/production-consumption architecture *was* selected (§5-§27)
without weakening any existing HATP/PB/runtime boundary (§30 self-check
passed), and it depends on freezing a new signing/evidence CLI contract
before any implementation — so the next phase should **not** jump to
implementation.

**Recommended: 149O.9 — HATP Signing Ceremony + Evidence Store Contract
Freeze.** Scope: freeze the exact `pcae hatp sign rollback` CLI surface
(flags, exit codes per §18's table, error vocabulary per Q74), the
`HATPSignedEvidenceEnvelope` file format and `.pcae/hatp-evidence/`
layout (§11-12), and the AG5 CLI entry-point inventory left open in §17
— all still architecture/contract work, no implementation, consistent
with 149O.8's own no-code mandate carrying forward one more phase before
code is written. The COMP-002-dependent PB enforcement track (§19, §27)
is independent and should not gate 149O.9's start.
