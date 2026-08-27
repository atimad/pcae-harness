# RIHAC-001 v1.0 — Runtime Invocation Human Authority Contract

## Contract identity and status

**Contract:** RIHAC-001  
**Version:** 1.0  
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3V — Local-CLI Runtime Dispatch Authority
and Permission Contract Freeze  
**Scope:** One future, explicitly human-authorized, bounded local-CLI
runtime invocation attempt.  
**Schema companion:** RIASC-001 v1.0  
**Related contracts:** RPAC-001 v1.0, PBRD-001 v1.1, RDGO-001 v2.0.
**Reference note (149O.20L.7O.3V.1R):** PBRD-001 and RDGO-001 were repaired
to v1.1/v2.0 to close two BLOCKING findings independently identified against
this contract's companions. RIHAC-001 itself is UNCHANGED: its authority
subject remains bound to `invocation_id`, not to `attempt_id`, because
approval authorizes at most one attempt via `attempt_limit=1`
(one-shot, §4) rather than naming a specific attempt in advance — an
`attempt_id` is minted per dispatch try at RDGO-001 gate 2, after the
approval subject model was already frozen, and does not change what the
human approved.

RIHAC-001 is the sole normative authority for the human-authority artifact
needed by a future real local-CLI runtime dispatch. It freezes authority
semantics only. It does not implement approval creation, validation,
storage, Permission Broker behavior, Runtime Enforcement, process
containment, adapter dispatch, result acceptance, or execution.

Runtime remains `Observed` / `observe` / `unavailable`.

## 0. Normative language

`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY`
are normative. An ambiguity at any authority boundary SHALL fail closed.

## 1. Purpose and semantic walls

A `RuntimeInvocationApproval` records an identified human's explicit,
bounded authority for PCAE to proceed toward one exact local-CLI invocation
attempt. It is not a general consent record and is not reusable task,
session, or phase authority.

The following distinctions are immutable:

```text
human approval != PB permission
PB ALLOW != runtime capability
runtime capability != Runtime Enforcement approval
Runtime Enforcement ALLOW != process permission
process permission != dispatch completion
dispatch completion != accepted change
runtime result != task completion
```

The approval artifact and the PB decision SHALL remain separate artifacts.
They MAY cite one another by immutable reference and digest; they SHALL NOT
combine provenance or become a single authority/permission token.

## 2. Scope and exclusions

RIHAC-001 v1.0 applies only to one bounded local external process invocation
through an explicitly selected local-CLI runtime target.

It excludes API providers, OpenRouter, provider SDKs, network egress,
provider/model universal fields, credential architecture, parallel
invocations, automatic retries, background or unattended execution,
multiple external dispatches, unrestricted shell access, arbitrary child
process trees, and multi-repository execution.

`RuntimeInvocationApproval` SHALL NOT grant network, credential,
filesystem-mutation, arbitrary-process, publication, push, rollback, or task
completion authority.

## 3. Authority source and approving subject

Authority originates only from a distinct, deliberate, non-defaultable
human confirmation over the exact approval preview. Silence, timeout,
inactivity, a default response, prompt preparation, target selection,
preflight, artifact production, schema validity, or producer identity SHALL
NOT create authority.

The approving human SHALL be identified by provenance evidence. The
component that renders or persists the artifact is the artifact producer,
not the approving human. Producer identity SHALL NOT be substituted for the
approver's identity.

The v1 approval mechanism is `interactive_local_cli_confirmation`. This is
a dedicated runtime-invocation confirmation mechanism. It is not CHGR
Confirmation, an Interactive Decision Session, a task/phase lifecycle
decision, or a Typed Authority Model `human_authorization` record.

## 4. One-shot authority

Exactly one `RuntimeInvocationApproval` authorizes at most one bounded
invocation attempt:

```text
one RuntimeInvocationApproval -> one bounded invocation attempt
```

`attempt_limit` and `dispatch_limit` SHALL both equal `1`. No session-wide
or phase-wide reusable authority exists in v1. A consumed approval SHALL
NEVER authorize a second attempt, including a retry of an apparently
identical prompt and target.

## 5. Exact approval subject

Phase 3U selected the exact five-member subject:

```text
(invocation_id, runtime_target, prompt_hash, repo_identity, task_id)
```

The RIASC-001 wire vocabulary represents it as:

```text
(invocation_id, runtime_target_id, prompt_hash, repository_identity, task_id)
```

All five members are one indivisible subject. A mismatch in any member
invalidates the approval for dispatch. No member is a hint and no
best-effort rebinding is permitted.

## 6. Invocation identity

The trusted PCAE coordinator SHALL allocate `invocation_id` before the
approval preview is rendered, using the existing opaque `inv-<32-hex>`
identity convention. Neither the external runtime, adapter, caller payload,
nor approval producer may choose or rewrite it.

The approval, PB request, Runtime Enforcement projection, durable
`RuntimeInvocationRecord`, dispatch envelope, receipt, and result SHALL cite
the same `invocation_id`. The approval remains a sibling artifact and SHALL
NOT be embedded inside the invocation record. A retry is a new logical
invocation with a new `invocation_id` and new approval.

## 7. Repository binding

`repository_identity` SHALL use the existing trusted git-derived repository
fingerprint mechanism (`compute_repo_fingerprint`: SHA-256 of the sorted
root-commit hashes). A raw or resolved filesystem path SHALL NOT be the
repository identity and SHALL NOT be an authority input.

The following behavior is frozen:

- Copying an approval artifact alone never grants authority. The destination
  must independently reproduce the exact fingerprint and all other subject,
  provenance, freshness, and consumption checks.
- Renaming or moving the same checkout does not invalidate solely because
  its path changed; path is non-authoritative.
- A sibling repository with a different git-root fingerprint is a subject
  mismatch and fails closed.
- A changed root-history identity is a subject mismatch and fails closed.
- A same-history clone has the same identity under the existing fingerprint
  mechanism. It is therefore the same repository lineage for this one
  field, but multi-repository/concurrent execution remains excluded; the
  exact task, invocation, HEAD, storage, and one-shot checks still apply.
- An unavailable or unverifiable fingerprint fails before approval creation
  where possible and always fails approval validation.

## 8. Task, phase, and session binding

The task authority source is PCAE's active task contract, resolved by the
trusted coordinator rather than supplied by an adapter or runtime. The
approval subject carries the exact active `task_id`; its freshness snapshot
carries the exact task-contract digest and active state. Approval for task A
SHALL NOT authorize task B.

`phase_id` is required governance context when an invocation occurs inside a
governed phase. `session_id` is required only when the invocation is actually
inside an explicitly session-scoped interactive workflow. Neither expands
the five-member approval subject; both are additional context bindings and
must match when applicable. A phase-only invocation SHALL NOT fabricate a
session ID.

## 9. Runtime-target and adapter binding

The approval binds the exact `runtime_target_id`. No target fallback,
provider fallback, model fallback, case folding, whitespace repair, alias
selection, or nearest-match behavior is permitted.

The artifact additionally snapshots stable adapter identity,
descriptor digest, and target-configuration digest. Adapter-configuration
drift invalidates dispatch readiness. Adapter executable identity/hash is
not a human-authority subject member; it is descriptor-pinned and must be
revalidated by live preflight immediately before process creation.

## 10. Prompt/instruction binding

`prompt_hash` SHALL be computed with profile `pcae.prompt-semantic.v1` over
the semantically load-bearing resolved prompt the adapter will actually
receive.

Canonicalization is frozen as follows:

1. Build an ordered list of every instruction/context component that will
   be delivered or can change runtime behavior. Each component has a stable
   `kind` and its exact `content`; array order is delivery order.
2. Normalize every string to Unicode NFC and normalize `CRLF`/bare `CR` to
   `LF`. Preserve all other whitespace, blank lines, punctuation, ordering,
   and case. Do not trim or collapse.
3. Exclude only transport/display material that is neither delivered nor
   behaviorally operative: ANSI decoration, terminal wrapping, display-only
   headings, and ephemeral timestamps/request IDs/host paths used solely for
   presentation.
4. If nominally host- or runtime-specific material is delivered to the
   runtime or can affect behavior, include it. Ambiguous inclusion fails
   closed; it is never guessed away as cosmetic.
5. Serialize the semantic document as UTF-8 compact JSON, recursively sorting
   object keys by ASCII lexicographic order while preserving array order.
6. Hash the exact canonical bytes with SHA-256 and encode as 64 lowercase
   hexadecimal characters.

A semantic prompt modification changes the digest and invalidates the
approval. Host formatting that satisfies the exclusion rule does not.
The existing dry `PromptArtifact.content_digest` behavior is unchanged;
this profile governs only the future real local-CLI path.

## 11. Approval scope

The exact approved scope SHALL include:

- requested capability;
- transport `local_cli`;
- effect class `bounded_local_process_dispatch`;
- one dispatch only;
- `network_required=false`;
- declared filesystem-scope reference;
- declared process-containment-profile reference; and
- stable adapter/configuration binding.

This scope describes what the human approved. It does not grant the
corresponding PB, Runtime Enforcement, process, filesystem, network, or
credential permission.

## 12. Provenance and trust

Every approval SHALL record who approved, when, the mechanism used, the
digest of the exact approval preview, and the trusted producer component.
Identified human provenance and producer provenance are separate fields.

V1 trust is the conjunction of:

1. strict RIASC-001 schema validation;
2. exact subject and scope binding;
3. identified-human provenance;
4. canonical-storage lookup rather than a caller-supplied arbitrary path;
5. record-digest recomputation and exact comparison; and
6. current freshness and consumption-state validation.

No cryptographic signature is required for v1. Schema validity or digest
agreement alone SHALL NOT imply authority. A caller-supplied boolean or
authority-shaped field cannot create authority.

## 13. Freshness and invalidation

All seven 3U conditions are mandatory for v1:

| Condition | Bound fact | Dispatch consequence | Fresh approval? |
|---|---|---|---|
| HEAD changes | `freshness_snapshot.head_commit` | Approval is stale; no dispatch | Yes |
| Task state/contract changes | active state + task-contract digest | Approval is stale; no dispatch | Yes |
| Prompt changes | subject `prompt_hash` | Different subject; no dispatch | Yes |
| Runtime target changes | subject `runtime_target_id` | Different subject; no fallback | Yes |
| Adapter configuration changes | descriptor/config digests | Approval is stale; no dispatch | Yes |
| Policy version changes | policy snapshot | Cached PB/RE decisions invalid; no dispatch until both are freshly evaluated | Not solely for policy drift, unless current policy changes the approved scope or requires it |
| Timeout/expiry | `expires_at` | Approval expired; no dispatch | Yes |

Policy drift is deliberately classified as decision freshness, not a
retroactive erasure of the human act. It still blocks dispatch and cannot be
auto-refreshed by reusing an old PB/RE decision.

## 14. Expiry, revocation, and cancellation

V1 requires both one-shot consumption and an explicit wall-clock
`expires_at`. This contract freezes no arbitrary duration. A future
approval-creation implementation must present the expiry to the human and
enforce separately governed bounds; `expires_at` must be later than
`created_at` and is evaluated against a trusted current clock.

The immutable approval artifact has no mutable `revoked` field and v1 does
not require an explicit revocation command. An unconsumed approval can be
made unusable by cancelling the pending invocation workflow or by allowing
it to expire; any future explicit early-revocation mechanism must be a
separate append-only, digest-bound artifact and requires its own governed
contract amendment. Missing, removed, quarantined, or unreadable approval
evidence fails closed; deletion is not treated as successful audit-preserving
revocation.

## 15. Canonical storage

The canonical v1 pattern is:

```text
.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json
```

The approval document is create-only, immutable, canonical JSON, and written
atomically in the repository's `.pcae` governance store. The trusted
validator resolves it by `approval_id`; callers SHALL NOT supply an arbitrary
path. Symlinks, traversal, duplicate conflicting IDs, non-canonical copies,
and digest mismatches fail closed.

The approval SHALL NOT be stored in CHGR, embedded in a
`RuntimeInvocationRecord`, placed in arbitrary temporary storage, or treated
as a Typed Authority Model record. Consumption is proven by the separately
stored durable invocation state described in §17.

## 16. Validation order

Validation SHALL execute in this fail-closed order:

1. resolve the canonical `approval_id` reference;
2. load exactly one canonical artifact;
3. validate RIASC-001 identity, version, required fields, closed-field policy,
   and types;
4. recompute and compare the record digest, then validate producer and human
   provenance;
5. bind repository, task, phase, and conditional session context;
6. bind `invocation_id` and exact runtime target;
7. bind prompt hash and canonicalization profile;
8. bind requested capability, effect scope, adapter descriptor, and target
   configuration;
9. validate all seven freshness conditions with the policy-drift disposition
   in §13;
10. validate `created_at`/`expires_at` against a trusted clock;
11. inspect canonical durable invocation state for prior consumption,
    cancellation, uncertainty, or completion; and
12. emit an immutable validated-authority evidence projection bound to all
    checked facts.

No later step runs as an authority shortcut when an earlier step fails.
Validation evidence is not PB permission or Runtime Enforcement approval.

## 17. Consumption point

Approval consumption occurs exactly with gate 9's atomic, durable
`dispatch_attempted` state transition. The same durable write SHALL bind the
approval ID/digest and the minimum eight RDGO-001 pre-effect items.

The approval SHALL NOT be consumed at prompt generation, target selection,
static preflight, approval creation, approval validation, PB ALLOW, Runtime
Enforcement ALLOW, or containment setup. It SHALL NOT wait until after
process creation either.

Once the durable marker exists, the approval is consumed even if later
evidence proves the process was never spawned. This deliberately preserves
at-most-once safety over convenience.

## 18. Missing, stale, mismatched, or tampered authority

The following all produce `no real dispatch`:

- no approval;
- missing canonical artifact;
- unsupported version or unknown field;
- stale or expired approval;
- subject, scope, repository, task, phase/session, target, prompt, adapter,
  or configuration mismatch;
- untrusted or incomplete provenance;
- record-digest mismatch;
- already consumed, cancelled, uncertain, or completed approval binding; or
- inability to determine the state uniquely.

There is no auto-refresh, best-effort rebinding, fallback target, permissive
default, or authority inference.

## 19. Crash, recovery, and retry

- **Before gate 9:** no external effect has occurred and approval remains
  unconsumed. Resume MAY use the same unexpired approval only when canonical
  state proves no `dispatch_attempted` marker exists and the complete
  validation, live preflight, PB, and Runtime Enforcement sequence is run
  again successfully.
- **After approval validation, PB, or Runtime Enforcement but before gate
  9:** those decisions are observations, not consumption. They SHALL be
  revalidated/re-evaluated; no cached permission or approval verdict is
  trusted.
- **After gate 9 but proven before process creation:** record
  `DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`; no external effect is claimed,
  but the approval remains consumed. A new attempt requires a new invocation
  and approval.
- **Dispatch may have happened:** record `DISPATCH_UNCERTAIN`. Never replay
  automatically and never claim completion.
- **Result captured:** record `RESULT_CAPTURED_UNTRUSTED`; capture does not
  accept changes or complete the task.

An uncertain or failed real dispatch SHALL NOT retry automatically. V1 retry
requires a new invocation identity and fresh human approval. Exactly-once
execution is not promised. The honest guarantee is at-most-once attempt where
PCAE can prove durable state, plus explicit uncertainty where it cannot.

## 20. Failure behavior and security invariants

Every error fails closed without external dispatch. At minimum:

- no valid approval -> no real dispatch;
- stale/expired approval -> no real dispatch;
- mismatched approval -> no real dispatch;
- target/prompt/repository/task mismatch -> no real dispatch;
- adapter cannot self-authorize;
- approval cannot substitute for PB ALLOW, capability, Runtime Enforcement,
  or containment;
- a runtime result remains untrusted; and
- runtime result capture cannot complete a task.

## 21. Versioning and evolution

RIHAC-001 uses contract `MAJOR.MINOR`. Additive clarification or optional
evidence may increment MINOR only when it does not widen existing authority.
A subject-member removal, one-shot relaxation, required-field removal,
semantic redefinition, or trust weakening is incompatible and requires a new
MAJOR plus explicit migration and independent verification.

Existing approvals SHALL always be interpreted under the exact contract and
schema version they declare. Unknown versions fail closed. No future version
may retrospectively widen an already-created approval.

## 22. Non-goals and implementation boundary

This freeze does not add an executable schema package, approval CLI,
approval store, validator, PB field, Runtime Enforcement integration, Shell
Gate, adapter, process launch, credential access, network capability, or
execution availability. It does not modify CHGR, Interactive Workflow, HATP,
HMIC, Class-B, CLTR, the dry adapter consumer, or POL-005.

## 23. Freeze verdict

**RIHAC-001 v1.0: FROZEN for local-CLI-v1 contract purposes.**  
**Real execution: UNAVAILABLE.**
