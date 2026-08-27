# Phase 149O.20L.7O.3V.2 — Local-CLI Real-Runtime Dispatch Implementation Planning

## 1. Objective

Produce an implementation-ready sequence for the **authority** (RIHAC-001
v1.0 / RIASC-001 v1.0) and **permission** (PBRD-001 v1.1) portion of the
future local-CLI real-runtime dispatch path, bounded to the smallest safe
first-implementation slice. This phase is planning-only: it modifies no
`src/pcae` source, no tests, and no production behavior. POL-005
(`ExecutionDisabledRule`) continues to hard-deny every real
(`simulation_only=False`) request; Runtime Enforcement and Shell Gate are
not activated; no process is spawned.

## 2. Baseline

| Fact | Value |
|---|---|
| Repository | `~/repos/pcae-harness` |
| Working tree | clean at entry |
| `origin/main..HEAD` | 0 at entry |
| `HEAD` at entry | `3482d8cf92eeb352f94f68ca0f478924d69b442b` |
| `v0.4.3` tag commit | `63580893b1de4782a694ab802ff7bdebdf29b0e6` (unchanged) |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warnings only — pre-existing `tasks/DONE.md` sync debt across dozens of historical tasks, unrelated to this phase, not repaired here (out of scope) |
| `pcae push check` | clean, nothing to push |
| `pcae runtime inspect` | `Observed` / `observe` / `unavailable`, 0 plugins, 0 capabilities, `not_implemented` |
| Telegram notification | configured, enabled, ready |
| Active governed phase at entry | none (idle task, human-decision hold) |

All baseline preconditions in the governing instructions were satisfied
before this phase began.

## 3. Verified contracts (read directly, this phase)

- **RIHAC-001 v1.0** — `docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` — FROZEN, unchanged by 3V.1R.
- **RIASC-001 v1.0** — `docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` — FROZEN normative schema; no executable schema exists.
- **PBRD-001 v1.1** — `docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` — FROZEN, repaired by 3V.1R (added `attempt_id`/`idempotency_key`).
- **RDGO-001 v2.0** — `docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` — FROZEN, repaired by 3V.1R (gate 3/4 transposition).
- **RPAC-001 (Runtime / Provider Adapter Contract)** — `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md` — companion contract governing invocation identity, dispatch envelope, and the existing mock/dry conformance target.
- Production source read: `src/pcae/core/permission_broker_foundation.py`, `src/pcae/core/permission_broker.py`, `src/pcae/core/runtime_invocation.py`, `src/pcae/core/runtime_adapter.py`, `src/pcae/core/runtime_dry_consumption.py`.
- Prior phase report read: `docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md` (source of the two MUST-FIX findings, §32 below).

Planning below is derived from these primary sources, not from prior
phase prose alone.

## 4. The 14 PBRD-001 v1.1 request facts (exact, from contract §4)

| # | Field | Source | Type | Required? | Trust owner | Construction point | Validation point | Persistence/reference |
|---:|---|---|---|---|---|---|---|---|
| 1 | `invocation_id` | Trusted invocation coordinator | `inv-<32-hex>` | Yes | PCAE coordinator | Gate 2 | Gates 2–11 | Invocation record item 1 |
| 2 | `attempt_id` | Trusted invocation coordinator | `att-<32-hex>` | Yes | PCAE coordinator | Gate 2 | Gates 2–11 | Invocation record item 1 |
| 3 | `idempotency_key` | Trusted invocation coordinator (RPAC-REQ-065) | 64-hex SHA-256 | Yes | PCAE coordinator | Gate 2 | Gates 2/6/9 (collision checks) | Invocation record item 1 |
| 4 | `repository_identity` | git-root fingerprint helper | 64-hex SHA-256 | Yes | Repository context resolver | Gate 2 (snapshot) | Gates 5/8/9 | Invocation record item 2 |
| 5 | `task_id` | Active task contract | non-empty string | Yes | Task lifecycle | Gate 2 | Gates 5/8/9 | Invocation record item 2 |
| 6 | `lifecycle_context` | Active governed lifecycle/session state | closed object (`phase_id` required, `session_id` conditional) | Yes | Lifecycle/session owner | Gate 2 | Gates 5/8/9 | Invocation record item 2 |
| 7 | `runtime_target_id` | Explicit target selection | exact non-empty ID | Yes | Target selector + registry | Gate 2 | Gates 2–11 | Invocation record item 3 |
| 8 | `adapter_descriptor_binding` | Registry/config preflight | closed object | Yes | Runtime Registry/config owner | Gate 4 (static preflight) | Gates 4/8 | Invocation record item 3 |
| 9 | `prompt_hash` | `pcae.prompt-semantic.v1` canonicalizer | 64-hex SHA-256 | Yes | Prompt builder | Gate 1 | Gates 1/5/8/9 | Invocation record item 4 |
| 10 | `requested_capability` | Governed invocation request | non-empty ID | Yes | Integration contract/coordinator | Gate 2 | Gate 6 | request digest |
| 11 | `transport_type` | Contract-fixed | const `local_cli` | Yes | PBRD-001 integration | fixed | Gate 6 | request digest |
| 12 | `network_requirement` | Target descriptor + static preflight | const `false` | Yes | Registry/preflight owner | Gate 4 | Gates 4/8 | request digest |
| 13 | `filesystem_scope_ref` | Governed isolated-worktree/scope owner | immutable ID/digest | Yes | Filesystem-scope owner | Gate 2 | Gate 8 | request digest |
| 14 | `human_authority_binding` | RIHAC validator | closed object (approval ID/digest + validation-evidence digest) | Yes | Human-authority validator | Gate 5 | Gates 5/9 | Invocation record item 5 |

`lifecycle_context` and `human_authority_binding` each count as **one**
fact despite closed subfields (contract §4, explicit convention).
Cardinality confirmed: **14**. Do not change without direct contract
evidence.

## 5. The 16 RIASC-001 v1.0 required fields

`schema_id`, `schema_version`, `contract_version`, `record_type`,
`approval_id`, `record_digest`, `created_at`, `expires_at`, `subject`,
`governance_context`, `prompt_hash_profile`, `approval_scope`,
`adapter_binding`, `freshness_snapshot`, `provenance`, `attempt_limit`
(contract §2). Cardinality confirmed: **16**.

**Exact five-member `subject`** (contract §3): `invocation_id`,
`runtime_target_id`, `prompt_hash`, `repository_identity`, `task_id`.

| Subject field | Planned implementation source |
|---|---|
| `invocation_id` | `pcae.core.runtime_invocation.new_invocation_id()` — already `inv-<32-hex>`, directly reusable |
| `runtime_target_id` | Runtime Registry explicit-target resolver (`src/pcae/core/runtime_registry.py`), no fallback |
| `prompt_hash` | New `pcae.prompt-semantic.v1` canonicalizer (does not exist yet; distinct from `PromptArtifact.content_digest` used by the dry path) |
| `repository_identity` | Existing `compute_repo_fingerprint` helper (git-root fingerprint, already used elsewhere in the repo) |
| `task_id` | Active task contract resolver (existing task-lifecycle machinery) |

## 6. The 11 RDGO-001 v2.0 gates

| # | Gate | Current state | First implementation (authority/PB) | Later phase |
|---:|---|---|---|---|
| 1 | Prompt preparation | Dry-path prompt hashing exists (`PromptArtifact`); real `pcae.prompt-semantic.v1` profile does not | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (new canonicalizer) | — |
| 2 | Target selection + request-identity minting | `new_invocation_id`/`new_attempt_id`/`compute_idempotency_key` ALREADY EXIST in `runtime_invocation.py` for the dry path | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (reuse existing generators; extend request identity to the new real-dispatch shape) | — |
| 3 | Human authority creation | Does not exist | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (`RuntimeInvocationApproval` model/store/creation) | — |
| 4 | Static preflight | Adapter descriptor/config preflight machinery exists for the dry path (`runtime_adapter.py`) | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (adapt existing preflight to run after gate 3, non-executing facts only) | — |
| 5 | Approval validation | Does not exist | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (RIHAC-001 12-step validator) | — |
| 6 | Permission Broker | `PermissionBrokerRequest`/policy registry exist; `runtime_dispatch` action does not | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE (new action vocabulary + request architecture; POL-005 still denies) | — |
| 7 | Runtime Enforcement | Coordinator exists but is internal/mock-only (3S.2.1 §64) | ALREADY EXISTS (mock-only) — real projection wiring NOT in first phase | IMPLEMENTED IN LATER RE PHASE |
| 8 | Process containment + live preflight | Does not exist | — | IMPLEMENTED IN SHELL/CONTAINMENT PHASE |
| 9 | Durable pre-dispatch record | Atomic create-only store pattern exists (`RuntimeInvocationStore._write_create_only`) but not for the real-dispatch 8-item record | IMPLEMENTED IN FIRST AUTHORITY/PB PHASE *only as a staged, non-consuming projection* (see §16) — full gate-9 consumption semantics wait for gates 8/10 to exist | Completed together with Shell Gate phase |
| 10 | Adapter dispatch | Mock adapter only | — | IMPLEMENTED IN SHELL/CONTAINMENT PHASE + first real adapter phase |
| 11 | Result capture/intake | Mock result capture exists; MUST-FIX #1 (malformed-result crash) is here | — | IMPLEMENTED IN SHELL/CONTAINMENT PHASE (repair MUST-FIX #1 no later than first non-mock adapter) |

Cardinality confirmed: **11**. Classification above is mandatory per
governing instructions §5.

## 7. The 8 durable-before-effect items (RDGO-001 gate 9, §10)

| # | Item | Existing artifact | New artifact | Reference/hash | Implementation phase |
|---:|---|---|---|---|---|
| 1 | Invocation identity (`invocation_id`, `attempt_id`, `idempotency_key`) | `new_invocation_id`/`new_attempt_id`/`compute_idempotency_key` (dry path) | Real-dispatch request-identity wrapper | direct values | First authority/PB phase |
| 2 | Repository/task binding | `compute_repo_fingerprint`, task contract digest helpers | none needed | fingerprint + digest | First authority/PB phase |
| 3 | Target binding | Adapter descriptor/config preflight | Live executable-identity observation (gate 8) | descriptor/config digests | First authority/PB phase (static) + Shell Gate phase (live) |
| 4 | Prompt binding | dry `PromptArtifact.content_digest` (different profile) | `pcae.prompt-semantic.v1` hash | sha256 | First authority/PB phase |
| 5 | Approval binding | none | `RuntimeInvocationApproval` ID/digest | ria-id + digest | First authority/PB phase |
| 6 | PB binding | `PermissionBrokerDecision` (existing shape) | `runtime_dispatch` decision instance | decision digest | First authority/PB phase |
| 7 | Runtime Enforcement binding | Mock evaluator only | Real RE decision | decision digest | Later RE phase |
| 8 | Dispatch intent/state (`dispatch_attempted` marker) | `_write_create_only` atomic pattern | New durable record type | marker + timestamp | Shell Gate phase (true consumption requires gates 8/10 to exist — see §16 staging) |

Cardinality confirmed: **8** (unchanged by v2.0; item 1 enriched per
RDGO-001 §10a). Items 1–6 have a real implementation surface in the
first authority/PB phase; items 7–8 cannot be truthfully completed until
RE and Shell Gate exist. This asymmetry is deliberately staged (§16, §28).

## 8. The 7 TOCTOU mutable facts (RDGO-001 §15)

| Fact | Snapshot mechanism | Recheck-before-PB mechanism | Recheck-before-dispatch mechanism | Fail-closed invalidation | Belongs in first authority/PB phase? |
|---|---|---|---|---|---|
| HEAD | `freshness_snapshot.head_commit` at approval creation | Re-read + compare | Re-read + compare | Approval stale; no dispatch | Yes (snapshot + gate-5 recheck) |
| Task state/contract | `task_contract_digest` + `task_state=active` | Re-read + compare | Re-read + compare | Approval stale; no dispatch | Yes |
| Prompt | `subject.prompt_hash` | Recompute + compare | Recompute + compare | Subject mismatch; fresh invocation/approval | Yes |
| Runtime target | `subject.runtime_target_id` | Recompute + compare | Recompute + compare | Subject mismatch; no fallback | Yes |
| Adapter configuration | `adapter_binding` descriptor/config digests | Recompute + compare | Recompute + compare | Approval stale; no dispatch | Yes |
| Adapter executable identity | Descriptor-pinned only (not approval-bound) | N/A beyond descriptor facts | Resolve + hash exact executable | No dispatch; repair/reselect target | No — live-preflight-only, belongs to Shell Gate phase (gate 8) |
| Policy version | `freshness_snapshot.policy_version` | Current PB/RE re-evaluation only | Current PB/RE re-evaluation only | Cached PB/RE invalid; re-evaluate | Yes (snapshot + PB evaluation-time recheck); RE recheck deferred |

Cardinality confirmed: **7**. `attempt_id`/`idempotency_key` are
intentionally excluded (identity, not TOCTOU-mutable state).

## 9. Existing-code reuse audit

Before proposing new code, the following existing PCAE patterns were
located and are the preferred reuse targets:

- **Atomic create-only JSON persistence:** `RuntimeInvocationStore._write_create_only` (`src/pcae/core/runtime_invocation.py:850`) — `tmp = path.with_suffix(".tmp"); tmp.write_text(...); tmp.replace(path)`. Directly reusable pattern for the approval store (§12); the new store MUST additionally sanitize the identifier against path traversal (MUST-FIX #2, §32) rather than repeating the existing gap.
- **Identifier generation:** `new_invocation_id()` (`inv-<32-hex>`) and `new_attempt_id()` (`att-<32-hex>`) in `runtime_invocation.py:54,60` already match RIASC-001/PBRD-001's exact ID grammar. `compute_idempotency_key` (`runtime_invocation.py:471`) already computes a canonical-content SHA-256 digest excluding `attempt_id`, structurally the same shape RDGO-001 §10a requires. These SHOULD be reused/extended, not reimplemented, for the real-dispatch path — with the caveat that the *canonical content* they hash today is the dry-path's `InvocationRequest` shape, not the future 14-fact PBRD shape, so the hashing function needs a new canonical-projection input, not a new hashing algorithm.
- **Canonical JSON serialization:** `_canonical_json` (`runtime_invocation.py:46`) — `json.dumps(value, sort_keys=True, separators=(",", ":"))`. Matches RIASC-001 §8's canonicalization rule (sorted keys, compact UTF-8 JSON) closely enough to reuse directly for `record_digest` computation, after adding the NFC-normalization step RIASC-001 requires.
- **Typed ID validation:** `is_valid_generated_id(value, prefix=...)` (`runtime_invocation.py:65`) — reusable for `inv-`/`att-`/future `ria-` prefix validation.
- **`PermissionBrokerRequest`/`PolicyRule`/`PolicyResult` machinery** (`permission_broker_foundation.py`) — the policy evaluation engine, precedence composition, and `PolicyRegistry` are reusable as-is; only the request *shape* needs to grow (§17) and a new `PolicyRule` subclass is needed only if a new policy is required (none is — POL-004/POL-005 already apply generically to `execution_class=adapter`, confirmed by reading `MissingHumanApprovalRule`/`ExecutionDisabledRule` source, §17).
- **Governance/task/phase authority resolution:** existing active-task-contract resolver and phase/session context resolution (used throughout `pcae` CLI) — reusable for `task_id`/`lifecycle_context` construction; no new resolver needed.
- **Fingerprint validation:** existing `compute_repo_fingerprint` helper — reusable as-is for `repository_identity`.
- **CHGR storage / canonical artifact stores:** RIHAC-001 §15 explicitly forbids storing the approval in CHGR or embedding it in the invocation record, so CHGR's storage *pattern* is a precedent for atomic append-only artifact storage, but the approval MUST live in its own canonical path (`.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json`), not inside CHGR itself.

No whole subsystem is cloned. The new surface is additive: one new
approval model/store/validator module family, one new PB request
architecture decision (§17), and one new canonicalizer for
`pcae.prompt-semantic.v1`.

## 10. Human authority implementation footprint

Smallest production surface for `RuntimeInvocationApproval`:

- Immutable frozen-dataclass model matching RIASC-001's 16 fields exactly (no `approved`/`authorized`/`permission` convenience flags — explicitly forbidden by RIASC-001 §0).
- Schema validation: structural (16 required fields, closed objects, `additionalProperties: false` recursively) plus the cross-field checks in RIASC-001 §11 (expiry ordering, digest recomputation, subject equality, etc. — these are NOT expressible in JSON Schema alone and must be a separate validator layer).
- Canonical serialization + `record_digest` computation, reusing `_canonical_json` plus NFC normalization (§9).
- Trust/provenance validation per RIHAC-001 §12 (schema + subject/scope binding + identified-human provenance + canonical-storage lookup + digest recomputation + freshness/consumption state).
- Store: create-only, path-confined, canonical-location-only lookup (§11).
- Lookup by `approval_id` only — never a caller-supplied arbitrary path (RIHAC-001 §15).
- Subject matching against the current invocation request (five-member equality).
- Freshness validation against all seven RIHAC-001 conditions (§13).
- Consumed/revoked/expired state handling: v1 has no mutable `revoked` field; "consumed" is proven only by the separately durable gate-9 record (§16), never by a flag on the approval artifact itself.

This matches existing PCAE governance/store conventions (create-only,
atomic, canonical-path-resolved, digest-verified) rather than inventing
a new persistence paradigm.

## 11. Approval model

Exact 1:1 representation of RIASC-001's frozen JSON Schema (§10 of that
contract): one frozen dataclass (or nested frozen dataclasses for
`subject`, `governance_context`, `approval_scope`, `adapter_binding`,
`freshness_snapshot`, `provenance`) mirroring the 16 top-level fields and
their exact nested shapes. No additional fields. No boolean authority
shortcuts (`approved=True` style) anywhere in the model — RIASC-001 §0
explicitly forbids a field named `approved`/`authorized`/`permission`/
`pb_allow` or equivalent, and this extends to internal representations
consumed as if they conferred authority.

## 12. Approval store

Canonical location (RIHAC-001 §15 / RIASC-001 §12):

```text
.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json
```

- Directory: one directory per `approval_id`, under the fixed store root.
- Filename identity: `approval.json`, fixed name inside the approval's own directory (avoids needing to sanitize a filename derived from caller input).
- Atomic writes: reuse the `tmp`-then-`replace()` pattern from `_write_create_only`.
- Lookup: by `approval_id` only, resolved to the fixed canonical path — never a caller-supplied path (this directly avoids repeating MUST-FIX #2's path-traversal gap, §32).
- Uniqueness: create-only; a second write to the same `approval_id` is a hard integrity failure (mirrors `InvocationIntegrityError`), never a silent overwrite — approvals are immutable per RIHAC-001 §1.
- Duplicate behavior: reject (unlike the dry path's idempotent-resume-on-identical-content behavior — an approval is a one-shot human act, not a replayable request, so RIASC-001 §9 and RIHAC-001 §4 make duplicate creation always an error, never an idempotent no-op).
- Malformed artifact behavior: fail closed — `json.loads` with no silent fallback, structural validation before trust, digest mismatch rejected.
- Path confinement: validate `approval_id` against the exact `^ria-[0-9a-f]{32}$` pattern *before* constructing any path from it, and never construct a path from any other caller-supplied string. This is a direct, explicit repair-by-design of MUST-FIX #2's class of gap, scoped to the new store from day one.

## 13. Approval creation

| Option | Description | Recommendation |
|---|---|---|
| A | Internal API/test-only first | **Recommended for first implementation.** Verifies the contract (model, validator, store) without expanding UX prematurely. A test harness can construct approvals directly via the trusted coordinator's internal API. |
| B | Explicit CLI approval creation | Deferred. Needs its own UX design (§14) and is not required to validate the frozen contracts. |
| C | Interactive workflow integration | Deferred further — RIHAC-001 §3 explicitly distinguishes the v1 `interactive_local_cli_confirmation` mechanism from CHGR Confirmation / Interactive Decision Sessions; folding it into the existing Interactive Workflow surface would risk conflating two mechanisms the contract keeps deliberately separate. |

Option A is the smallest implementation that verifies the frozen
contracts without prematurely expanding UX, consistent with §59's
"smallest safe subset" framing.

## 14. Human authority UX (deferred target, since CLI is deferred)

If/when a CLI is added (later phase), the approval-preview MUST display
at minimum, per RIHAC-001 §3/§11:

- repository (fingerprint + human-readable hint, e.g. current branch/HEAD short SHA);
- task ID;
- runtime target ID;
- prompt identity/hash (and ideally a human-legible summary, since a raw hash is not reviewable, though RIHAC-001 does not mandate prompt *content* display — only that the digest correspond to what will be delivered);
- invocation identity;
- one-shot semantics (`attempt_limit=1`, `dispatch_limit=1`, explicit expiry).

This is documented here as a target; no CLI surface is built in the
first implementation phase (§13).

## 15. Approval validation

Exact ordered validation, reproducing RIHAC-001 §16 verbatim (no
reordering, since the contract's order is normative):

1. resolve the canonical `approval_id` reference;
2. load exactly one canonical artifact;
3. validate RIASC-001 identity, version, required fields, closed-field policy, and types;
4. recompute and compare the record digest, then validate producer and human provenance;
5. bind repository, task, phase, and conditional session context;
6. bind `invocation_id` and exact runtime target;
7. bind prompt hash and canonicalization profile;
8. bind requested capability, effect scope, adapter descriptor, and target configuration;
9. validate all seven freshness conditions with the policy-drift disposition in RIHAC-001 §13;
10. validate `created_at`/`expires_at` against a trusted clock;
11. inspect canonical durable invocation state for prior consumption, cancellation, uncertainty, or completion;
12. emit an immutable validated-authority evidence projection bound to all checked facts.

No later step runs as a shortcut when an earlier step fails (fail-closed,
short-circuit on first failure).

## 16. Approval invalidation

All seven RIHAC-001 §13 conditions are implemented, none deferred:

1. HEAD change → stale, no dispatch, requires fresh approval.
2. Task state/contract digest change → stale, no dispatch, fresh approval.
3. Prompt hash change → subject mismatch, no dispatch, fresh invocation+approval.
4. Runtime target change → subject mismatch, no fallback, fresh invocation+approval.
5. Adapter configuration digest change → stale, no dispatch, fresh approval.
6. Policy version change → cached PB/RE decisions invalid; re-evaluate; does not retroactively erase the human act, but blocks dispatch until fresh decisions exist.
7. Timeout/expiry (`expires_at`) → expired, no dispatch.

## Approval consumption staging

Per governing instructions §16: **do NOT implement approval consumption
at real dispatch in this phase**, since gates 8/9's full durable
pre-dispatch record and Shell Gate do not yet exist.

Correct intermediate behavior: the approval artifact and its validator
CAN be created and validated end-to-end in tests (proving RIHAC-001
validation order end-to-end), but the *durable, atomic, gate-9
`dispatch_attempted` write that actually marks an approval consumed*
(RIHAC-001 §17) is **not implemented** in this first phase, because it
requires gate 8 (containment evidence) as an input and gates 10/11 to
give the marker operational meaning. Validating an approval MUST NOT be
conflated with consuming it — RIHAC-001 §17 is explicit that validation,
PB ALLOW, and Runtime Enforcement ALLOW are all non-consuming
observations. First-phase tests exercise "approval validated N times
without being consumed" as an explicit adversarial case (§26/§38).

## 17. PB request architecture

`PermissionBrokerRequest` (`permission_broker_foundation.py:142`) is
today a flat `@dataclass(frozen=True)` with exactly 12 fixed fields and
no extension container — it cannot naively grow 14 new runtime-only
fields without breaking every existing action type's assumptions about a
uniform, small envelope.

| Option | Description | Assessment |
|---|---|---|
| A | Optional action-specific fields added directly to `PermissionBrokerRequest` | Rejected: pollutes the shared envelope for all 30+ existing action types with runtime-dispatch-only optional fields; violates the existing dataclass's "canonical, evaluate-only request" simplicity. |
| B | Nested runtime-dispatch context object | **Recommended.** Add one new optional field, e.g. `runtime_dispatch_context: RuntimeDispatchRequestFacts | None = None`, holding a new frozen dataclass with exactly the 14 PBRD-001 facts. Existing action types never populate it (stays `None`); `runtime_dispatch` requests always populate it. Backward compatible: existing `build_permission_broker_request` callers are unaffected since the new field has a default. |
| C | Typed action payload (generic discriminated-union payload field for every action type) | Rejected as premature: would require refactoring all existing action types' request construction in the same phase, far exceeding "smallest safe subset." Worth reconsidering only if a *second* action type needs a similarly large bespoke payload in the future. |

**Decision: Option B.** Minimal, additive, backward-compatible, and
matches PBRD-001 §5's "only a trusted, contract-fixed PCAE integration
point may construct this request" — a nested, separately-typed object is
easier to keep write-once/immutable than 14 loose optional fields on the
shared envelope.

## 18. `runtime_dispatch` action implementation (planning only — not implemented in 3V.2)

- Exact constant: `ACTION_TYPE_RUNTIME_DISPATCH = "runtime_dispatch"`, alongside existing `ACTION_TYPE_*` constants in `permission_broker_foundation.py`.
- Execution class: reuse existing `EXECUTION_CLASS_ADAPTER` (PBRD-001 §1 — no new execution class needed; confirmed against `MissingHumanApprovalRule.applicable_execution_classes` already including `EXECUTION_CLASS_ADAPTER`).
- Compatibility: purely additive; `UnknownCapabilityRule` (POL-006) already generically rejects unrecognized `action_type`/`execution_class` combinations, so adding one new recognized pair requires only a registry-side allow-list update, not new policy logic.
- Policy matching: POL-004 (`MissingHumanApprovalRule`) and POL-005 (`ExecutionDisabledRule`) already apply generically to any request with `execution_class=adapter` / `simulation_only=False` — confirmed by reading both rules' `evaluate()` implementations. No new policy rule is structurally required for the first phase; POL-005 continues to unconditionally deny (§24).

## 19. `attempt_id` implementation (planning only)

- Generation: reuse `new_attempt_id()` (`runtime_invocation.py:60`) — already produces `att-<32-hex>` via `uuid.uuid4().hex`, matching PBRD-001 exactly.
- Type: opaque string, PCAE-owned.
- Ownership: trusted invocation coordinator only; never adapter/runtime/caller-supplied (PBRD-001 §4a).
- Persistence: bound into the future real-dispatch request's `runtime_dispatch_context` (§17) and, once gate 9 exists, the durable pre-dispatch record item 1.
- Validation: `is_valid_generated_id(value, prefix="att")` (already exists) plus construction-point trust check (reject caller-supplied values, PBRD-001 §15).
- Lifecycle: minted once per gate-2 pass; a retry mints a new `attempt_id` even when `idempotency_key` is unchanged (RDGO-001 §10a). Not conflated with `invocation_id` (stable across attempts) or `approval_id` (human-authority artifact identity).

## 20. `idempotency_key` implementation (planning only)

- Generation/derivation: extend `compute_idempotency_key` (`runtime_invocation.py:471`) to accept the future real-dispatch canonical-content projection (repository fingerprint/base commit, `task_id`, `prompt_hash`, `runtime_target_id`, adapter/descriptor/config digests, requested effect profiles, approval scope) per RPAC-REQ-065 — the *function shape* (SHA-256 over sorted-key canonical JSON, excluding `attempt_id` and timestamps) is reusable; the *input projection* must be widened to the real-dispatch fact set.
- Logical request binding: same key across safe retries of the same unchanged logical request.
- Payload binding: any change to prompt/target/repo/task/effects/budget changes the key (and mints a new `invocation_id`).
- Replay behavior: same `idempotency_key` + same `invocation_id` = safe retry (new `attempt_id`, same key); same `idempotency_key` + different `invocation_id` = reject (PBRD-001 §15 — distinct logical invocations never share a key by construction).
- Storage: durable request record, mirroring `create_request_record`'s existing idempotent-resume-vs-hard-collision logic (`runtime_invocation.py:858`).
- Collision/conflict detection: reuse the existing `InvocationIntegrityError("id_collision_conflicting_content:...")` pattern for a same-ID-different-content collision.

## 21. Attempt/idempotency adversarial tests (planned, not written in 3V.2)

1. Same `attempt_id`, changed payload → hard collision, reject (RPAC-REQ-066).
2. Same `idempotency_key`, changed `runtime_target_id` → this is actually a contradiction under RDGO-001 §10a (the key is a pure function of target among other fields) — test that changing the target necessarily produces a *different* key, and that presenting an old key with a new target is rejected as tampered/mismatched, not silently accepted.
3. Same `idempotency_key`, changed `prompt_hash` → same reasoning as (2): must be structurally impossible for the key to stay the same; test rejects any caller attempt to force it.
4. Stale approval + new attempt → approval invalidated (RIHAC-001 §13), fresh approval required before any new attempt proceeds.
5. Replayed PB decision (reusing a decision from a prior `attempt_id`) → rejected; PBRD-001 §10 — a changed `attempt_id` always invalidates any prior PB decision even with unchanged `idempotency_key`.
6. Uncertain previous attempt (`DISPATCH_UNCERTAIN`) followed by a same-`idempotency_key` retry → requires a brand-new `attempt_id` through a fresh gate-2 pass and a fresh human approval (RDGO-001 §10a); no automatic reuse.

## 22. PB approval evidence projection

Architecture: the trusted RIHAC-001 validator (gate 5) is the *only*
producer of the projection that later sets `approval_present=true`
(PBRD-001 §7). It is never `caller passes approval_present=True`. Concretely:

- Gate 5's validator emits an immutable "validated-authority evidence projection" (RIHAC-001 §16 step 12) containing approval ID/digest, subject/scope binding digest, provenance verdict, freshness verdict, expiry verdict, consumption-state verdict.
- The trusted PB request builder (the same contract-fixed integration point that owns the other 13 facts) reads *only* this projection — never raw approval prose, never a caller assertion — and sets `human_authority_binding` (fact 14) plus derives `approval_present` from it.
- `approval_present` remains a derived Foundation input for POL-004, never itself authority and never caller-settable (PBRD-001 §7).

## 23. POL-004 integration

`MissingHumanApprovalRule` (`permission_broker_foundation.py:449`)
already triggers `HUMAN_REVIEW` whenever `approval_present` is falsy, for
any request with `execution_class` in `{shell, backend, adapter,
rollback}` — `adapter` is already included. No change to POL-004's logic
is required: only the trusted request builder's construction of
`approval_present` for `runtime_dispatch` needs the projection described
in §22. This must not globally suppress `HUMAN_REVIEW`: a request built
*without* valid approval evidence still produces `approval_present=false`
and POL-004 still fires normally.

## 24. POL-005 staging boundary (critical)

`ExecutionDisabledRule` (`permission_broker_foundation.py:489`) denies
unconditionally whenever `request.simulation_only` is falsy — it has no
awareness of `action_type` at all. The first authority/PB implementation
phase should:

- Add the `runtime_dispatch` action/execution-class vocabulary (§18).
- Add `RuntimeInvocationApproval` model/store/validator (§10–16).
- Add the PB request architecture extension (§17) and approval projection (§22).
- Exercise PB evaluation for `runtime_dispatch` requests **with
  `simulation_only=True`** (or an equivalent non-real evaluation mode) so
  the full request/decision machinery is testable.
- Leave POL-005 completely untouched in source. Any `runtime_dispatch`
  request constructed with `simulation_only=False` in a test MUST still
  observe `DENY` from POL-005, proving the hard-deny survives the new
  action vocabulary unchanged.

This is achievable without contradiction: PBRD-001 §1 already frames
`runtime_dispatch` as reusing the existing `adapter` execution class, and
`simulation_only` is already an independent field on the existing
request dataclass — nothing in the contract requires POL-005's logic to
change to add the new action type.

## 25. PB policy phase split

**Recommended: yes, two phases**, matching PBRD-001 §12's own staged
eligibility list.

- **Phase A (this planning's recommended next implementation phase, §59):** request/action vocabulary + approval integration while POL-005 remains a hard, unconditional deny for every non-simulation request, including `runtime_dispatch`.
- **Phase B (future, after RE/Shell Gate prerequisites exist):** a narrowly scoped POL-005 eligibility rule for the exact local-CLI `runtime_dispatch` profile — never a blanket bypass, never a deletion of POL-005, never an inference that `simulation_only=false` alone is permission (PBRD-001 §12, explicit).

This is evidence-derived, not a default assumption: PBRD-001 §12 lists
11 separately-implemented-and-independently-verified prerequisites before
POL-005 may be narrowly evolved, and most of them (RE real gate, Shell
Gate, executable supply-chain identity, atomic durable-before-effect
state, the two 3S.2.1 repairs at their required reachability point,
runtime-inspect repair, independent verification) are untouched by Phase
A's scope.

## 26. Real-dispatch PB testing without real dispatch

Planned test matrix (implementation deferred to the first implementation
phase):

- Valid request (valid approval projection, `simulation_only=True`) → `ALLOW` (contingent on no other rule firing).
- Missing approval → `approval_present=false` → POL-004 `HUMAN_REVIEW`.
- Stale approval → RIHAC validator fails at gate 5 before request construction even completes; PB never sees `approval_present=true`.
- Mismatched approval (wrong subject) → same as above — gate 5 rejects before PB.
- `simulation_only=False` (real) with everything else valid → POL-005 `DENY`, unconditionally, precedence `DENY > HUMAN_REVIEW > ALLOW` preserved.
- HUMAN_REVIEW vs DENY precedence when both POL-004 and POL-005 would independently trigger.
- Attempt/idempotency replay scenarios (§21).

All tests run entirely in-process against the policy registry; zero
subprocess, zero network, zero external effect (§37).

## 27. Invocation-record integration plan

`RuntimeInvocationStore`/`InvocationRequest` (dry-path, mock-v1) SHOULD
**not** be extended with `attempt_id`/`idempotency_key` because it
**already has them** (`runtime_invocation.py:416-417`) — that store is
specific to the mock-v1 dry-consumption path and stays untouched
(PBRD-001 §13 explicitly forbids migrating the dry path). A **separate**
future `RuntimeInvocationRecord` store for real-dispatch gains
`attempt_id`, `idempotency_key`, approval ref, and PB decision ref only
when gate 9 is truthfully implementable (§28) — not in this phase.

## 28. Durable-state staging

Because gate 9 (durable pre-dispatch record) depends on gate 8
(containment evidence) which does not exist yet, the first
authority/PB implementation phase must not falsely claim the
durable-before-effect contract is fully implemented:

| Artifact | State after first authority/PB phase |
|---|---|
| Approval artifact (create/validate/store) | implemented |
| PB request/decision (`runtime_dispatch`, non-real) | implemented |
| Dispatch-attempt durable record (gate 9, 8-item write, real consumption) | later (Shell Gate phase) |

## 29. Runtime Enforcement future projection

The future coordinator projects to Runtime Enforcement (per PBRD-001
§14 / RDGO-001 §8): the full immutable request (14 facts), PB decision +
policy IDs/version/digest, validated approval reference + freshness
digest, and static/live preflight facts — by reference/digest, never
duplicating the raw approval or PB internals wholesale. This phase
documents the adapter shape only; it does **not** implement it and does
**not** create a new engine. The existing RE Decision Engine/Coordinator
contracts (`docs/PHASE_102_RUNTIME_ENFORCEMENT_DECISION_ENGINE_CONTRACT_FREEZE.md`,
`docs/PHASE_103_RUNTIME_ENFORCEMENT_COORDINATOR_CONTRACT_FREEZE.md`) are
the target integration surface for a future RE phase — confirmed still
`internal/mock-only` on the runtime-dispatch path per 3S.2.1 §64.

## 30. Runtime Enforcement implementation dependency

RE cannot be truthfully activated for `runtime_dispatch` until the
authority/PB foundation (this phase's recommended next implementation
phase) has produced: the full 14-fact request, a real PB decision
(`ALLOW`/`DENY`/`HUMAN_REVIEW`) with policy version/digest, and a
validated approval reference with freshness-verdict digest. These are
exactly items 1–3 of PBRD-001 §14's projection list — RE has nothing
truthful to evaluate without them.

## 31. Shell Gate dependency

Shell Gate (gate 8) needs, at minimum, from the authority/PB foundation
and RE: the bound `adapter_descriptor_binding` (fact 8) and
`filesystem_scope_ref` (fact 13) to re-resolve/verify at live preflight,
and a positive, single-attempt RE decision (gate 7 output) as its
precondition to even attempt containment establishment (RDGO-001 §9).
Not activated in this phase.

## 32. Two 3S.2.1 MUST-FIX findings (verbatim recovery)

Source: `docs/PHASE_149O_20L_7O_3S_2_1_INDEPENDENT_END_TO_END_PRODUCTION_DRY_LIFECYCLE_RUNTIME_ADAPTER_CONSUMPTION_VERIFICATION.md` §62.

> **MUST-FIX: 2** (both non-blocking to the production-consumption verdict — neither is reachable through the current production entry point today)
>
> 1. **Malformed adapter result crashes uncaught instead of failing closed cleanly.** `simulate_invocation` (`runtime_adapter.py` line ~501) calls `store.write_result(...)` on whatever `adapter.collect()` returns, without validating it is a `RuntimeInvocationResult` first; a non-conforming return value (e.g. a plain `dict`) raises an uncaught `AttributeError` inside `RuntimeInvocationStore.write_result` (`runtime_invocation.py` line ~923) rather than producing a `FAILURE_MALFORMED_RESULT` `SimulationOutcome`. **Effect on trust:** none observed — no `result.json` or `intake-handoff.json` is ever persisted when this occurs (verified empirically), so no false-success state is reachable. **Reachability:** none in current production — `_run_with_context` only ever instantiates `MockDryRuntimeAdapter()`, which always returns a well-formed `RuntimeInvocationResult`; this gap only matters for a future, non-mock adapter implementation.
> 2. **`RuntimeInvocationStore` does not sanitize `invocation_id` against path traversal.** `_invocation_dir`/`_write_create_only` join the raw `invocation_id` string onto the store root with no normalization or confinement check; a crafted ID (e.g. containing `../../..`) resolves completely outside `.pcae/runtime-invocations/mock-v1/`, demonstrated directly against the store. **Reachability:** none in current production — both public entry points (`run_production_dry_invocation`, `resolve_dry_consumer_context`) take no `invocation_id` parameter; it is always internally generated via `new_invocation_id()` (confirmed via `inspect.signature`, `test_production_entry_point_never_lets_caller_choose_invocation_id`). Recorded as defense-in-depth debt for any future caller of the store that might ever relay this field from less-trusted input.

**Reachability assessment for the planned first authority/PB
implementation phase:**

- **Finding 1 (malformed result / `simulate_invocation`, `runtime_adapter.py`):** NOT made reachable by the authority/PB phase, since gate 10/11 (dispatch + result capture) are not implemented there — only mock adapter dispatch exists, unchanged. **No repair required before/within the first authority/PB phase.** Must be repaired no later than the first non-mock adapter phase (Layer F), per RDGO-001 §12's explicit note that this contract "does not repair the existing 3S.2.1 malformed-result finding; that repair is blocking before the first non-mock adapter becomes reachable."
- **Finding 2 (`RuntimeInvocationStore` path traversal, mock-v1 store):** NOT made reachable by the authority/PB phase either — the new approval store (§12) is a **separate** store from `RuntimeInvocationStore`, and this phase's planning already designs the new store with `approval_id`-pattern validation *before* path construction (§12), so the new store does not inherit this gap by construction. The **existing** `RuntimeInvocationStore` gap remains open and unrepaired; it should be folded into whichever future phase next touches `RuntimeInvocationStore` itself (per 3S.2.1 §67's own recommendation), which is not this phase's scope (this phase does not modify `runtime_invocation.py`).

Neither MUST-FIX finding becomes reachable by the recommended first
implementation phase; neither requires repair before/within it.

## 33. Runtime inspect limitation

Carried forward: `TRUTHFUL_WITH_LIMITATION` (3S.2.1 §61) — `pcae runtime
inspect` does not surface the dry-consumption capability that already
exists. The authority/PB implementation does not change this limitation's
urgency: it adds no new adapter registration and makes no new
availability claim. It remains — as before — a repair required before
the *first real adapter* registration/availability claim (Layer F), not
before the authority/PB foundation.

## 34. Production dry path protection (regression plan)

- `pcae session bootstrap --compact --dry-runtime --runtime-target <id>` MUST remain byte/behavior-identical.
- `adapter_invocation` / `simulation_only=true` MUST NOT be migrated to `runtime_dispatch` (PBRD-001 §13, explicit).
- The dry path's `InvocationRequest`/`RuntimeInvocationStore` (mock-v1) MUST NOT be required to carry the new real-dispatch-specific fields beyond what they already have.
- Regression test: full dry-path E2E suite (existing `tests/test_runtime_dry_consumption_3s2.py`, `tests/test_session_bootstrap_dry_runtime_3s2.py`, etc.) re-run unchanged and green after the future implementation phase.

## 35. Existing PB regression protection

Focused regression plan for the future implementation phase: rerun
existing rollback, publication, push, and other mutation-action PB test
suites unchanged; assert byte-identical decisions for every pre-existing
`action_type`/`execution_class` pair given unchanged inputs, proving the
new optional `runtime_dispatch_context` field (§17, Option B) and new
action constant do not alter any existing action's evaluation.

## 36. Failure semantics (fail-closed table)

| Failure | Outcome |
|---|---|
| Invalid approval schema | No validated-authority projection; no dispatch |
| Missing approval | `approval_present=false`; POL-004 `HUMAN_REVIEW` |
| Stale approval | Fail at gate 5; no dispatch |
| Subject mismatch | Fail at gate 5; no dispatch |
| Unknown runtime target | Fail at gate 2/4; no dispatch |
| Invalid attempt ID | Construction-time rejection |
| Idempotency conflict | Hard collision, reject (RPAC-REQ-066) |
| PB malformed request | No dispatch |
| PB exception | No dispatch (treated as failure, not silent allow) |
| POL-005 deny | No dispatch (always, for every real request) |

## 37. No external effect invariant

All authority/PB implementation tests for the future phase must prove,
via Matrix-D-style side-effect counting (as 3S.2.1 did): `subprocess = 0`,
`network = 0`, `credential access = 0`, `external runtime = 0`, `repo
mutation by runtime = 0`. This phase's own planning-only work already
satisfies this trivially (no code changes at all).

## 38. Security threat tests (planned)

Forged approval; copied approval from sibling repository (repository
fingerprint mismatch, RIHAC-001 §7); task swap; runtime-target swap;
prompt swap; approval replay (reuse after gate-9 consumption, deferred
until gate 9 exists — meanwhile: reuse after *validation*, which must
succeed repeatedly without being treated as consumption, §16); attempt
replay; idempotency collision; caller-supplied `approval_present`
shortcut (must be rejected at request-construction time, PBRD-001 §15);
PB decision replay across a changed `attempt_id` (must be rejected,
PBRD-001 §10).

## 39. Approval tampering

Trust/tamper tests based on `record_digest` recomputation-and-compare
(RIASC-001 §8), the same canonical-JSON-then-SHA-256 pattern already
used elsewhere in the repo. No signature required — RIASC-001 §0/§7
explicitly does not require cryptographic signing for v1.

## 40. Atomicity

Approval-store atomic write/failure tests: assert no half-written valid
artifact is ever observable (verify via the same `tmp`-then-`replace()`
pattern already proven atomic for `RuntimeInvocationStore`, §9); a crash
mid-write leaves at most an orphaned `.tmp` file.

## 41. Restart behavior

- Approval persists across restart (plain file read).
- Validated subject remains stable (deterministic recomputation from stored fields).
- Stale conditions re-evaluated fresh on every validation call — never cached.
- PB decision is never cached across restart or across any of the seven freshness conditions (RIHAC-001 §13, PBRD-001 §10).

## 42. Policy-version freshness

PB re-evaluates whenever `policy_version` differs from the approval's
`freshness_snapshot.policy_version`; a real-dispatch `ALLOW` is never
reused across a policy-version change (RIHAC-001 §13's explicit
"Not solely for policy drift, unless current policy changes the approved
scope or requires it" caveat is honored by re-evaluating rather than
blanket-invalidating on any version bump).

## 43. Prompt freshness

Test: approval created → semantic prompt content changes (even a single
character, per RIHAC-001 §10's no-trim/no-collapse rule) → recomputed
`pcae.prompt-semantic.v1` hash differs → approval invalid at gate 5.

## 44. Repository freshness

Test: repository fingerprint/HEAD changes after approval creation (new
commit, rebase, etc.) → `freshness_snapshot.head_commit` mismatch → stale,
no dispatch (RIHAC-001 §13 row 1).

## 45. Task-state freshness

Exact transitions that invalidate approval, per RIHAC-001 §8/§13: task
contract digest change, task no longer `active` (closed/completed/
reassigned). Approval for task A never authorizes task B.

## 46. Runtime target freshness

Target mismatch always fails; there is no fallback target, no
case-folding, no nearest-match (RIHAC-001 §9, RDGO-001 §3).

## 47. Adapter config freshness

Adapter-configuration drift invalidates dispatch readiness at approval
level (descriptor/config digest mismatch). Live executable identity is
NOT approval-bound (RIHAC-001 §9) — it is descriptor-pinned and must be
revalidated by live preflight (gate 8) immediately before process
creation; that later live check is out of scope for this phase and
belongs to the Shell Gate phase, documented here as the ownership
boundary.

## 48. Command-zone design

If a future first implementation phase exposes any CLI (deferred per
§13's Option A recommendation), the command layer may only: parse
arguments; resolve PCAE-owned task/repo context (via existing resolvers);
call the core service; render output. No authority logic in the command
module — mirrors the existing repo-wide command/core separation pattern
already used throughout `src/pcae/commands/*` vs `src/pcae/core/*`.

## 49. Core service boundaries (proposed module names)

- `runtime_authority.py` — `RuntimeInvocationApproval` model + RIHAC-001 validator (approval creation/validation logic).
- `runtime_invocation_approval_store.py` — canonical store (create-only, path-confined, per §12).
- `runtime_dispatch_permission.py` — the `runtime_dispatch` PB request architecture extension (§17), action constant (§18), and approval-projection adapter (§22).

These three modules keep authority (RIHAC/RIASC), permission (PBRD), and
storage concerns separable for audit, matching the existing
one-concern-per-module convention in `src/pcae/core/`. No existing module
is renamed or merged; `permission_broker_foundation.py` gains one new
optional field and one new action constant only.

## 50. Production file plan (for the future implementation phase — none created in 3V.2)

| File | New/Modify | Responsibility | Contract requirements |
|---|---|---|---|
| `src/pcae/core/runtime_authority.py` | New | `RuntimeInvocationApproval` model + RIHAC-001 validator | RIHAC-001, RIASC-001 |
| `src/pcae/core/runtime_invocation_approval_store.py` | New | Canonical create-only approval store | RIHAC-001 §15, RIASC-001 §12 |
| `src/pcae/core/runtime_dispatch_permission.py` | New | `runtime_dispatch` action/request architecture, approval projection adapter | PBRD-001 |
| `src/pcae/core/permission_broker_foundation.py` | Modify (additive) | New optional `runtime_dispatch_context` field + new action constant | PBRD-001 §4/§5 |
| `src/pcae/core/runtime_invocation.py` | Modify (additive, minimal) | Extend `compute_idempotency_key`'s canonical-projection input for real-dispatch use, or add a sibling function — decision left to implementation phase | RDGO-001 §10a |

## 51. Test file plan

| Test file | Unit/Integration/E2E | Coverage |
|---|---|---|
| `tests/test_runtime_authority_model.py` | Unit | RIASC-001 schema shape, digest canonicalization, closed-field policy |
| `tests/test_runtime_authority_validation.py` | Unit/Integration | RIHAC-001 12-step ordered validation, all seven freshness conditions |
| `tests/test_runtime_invocation_approval_store.py` | Unit | Atomicity, path confinement, create-only/duplicate-reject, malformed artifact |
| `tests/test_runtime_dispatch_permission.py` | Integration | PBRD-001 14-fact request construction, `approval_present` projection, POL-004/POL-005 interaction, precedence |
| `tests/test_runtime_dispatch_attempt_idempotency.py` | Unit/Integration | §21 adversarial matrix |
| `tests/test_runtime_dispatch_no_external_effect.py` | Integration | §37 side-effect invariant (0 subprocess/network/credential) |
| `tests/test_runtime_dispatch_regression_dry_path.py` | Regression | §34 dry-path protection |
| `tests/test_runtime_dispatch_regression_pb_actions.py` | Regression | §35 existing-action protection |

## 52. Contract-to-code matrix

| Contract Req | Implementation surface | Test | Phase |
|---|---|---|---|
| RIHAC-001 §4 one-shot | `runtime_authority.py` validator + store consumption staging | `test_runtime_authority_validation.py` | First authority/PB phase (validation); Shell Gate phase (true consumption) |
| RIHAC-001 §7 repository binding | `runtime_authority.py` subject binding | `test_runtime_authority_validation.py` | First authority/PB phase |
| RIHAC-001 §10 prompt canonicalization | New `pcae.prompt-semantic.v1` canonicalizer | `test_runtime_authority_model.py` | First authority/PB phase |
| RIHAC-001 §13 freshness (7 conditions) | `runtime_authority.py` validator | `test_runtime_authority_validation.py` | First authority/PB phase |
| RIASC-001 §2 16 required fields | `runtime_authority.py` model | `test_runtime_authority_model.py` | First authority/PB phase |
| RIASC-001 §8 digest canonicalization | `runtime_authority.py` (reuse `_canonical_json`) | `test_runtime_authority_model.py` | First authority/PB phase |
| PBRD-001 §4 14 facts | `runtime_dispatch_permission.py` | `test_runtime_dispatch_permission.py` | First authority/PB phase |
| PBRD-001 §4a attempt/idempotency minting | `runtime_invocation.py` extension | `test_runtime_dispatch_attempt_idempotency.py` | First authority/PB phase |
| PBRD-001 §7 approval projection | `runtime_dispatch_permission.py` | `test_runtime_dispatch_permission.py` | First authority/PB phase |
| PBRD-001 §8 POL-004 semantics | `permission_broker_foundation.py` (unchanged logic, new caller) | `test_runtime_dispatch_permission.py` | First authority/PB phase |
| PBRD-001 §12 POL-005 boundary | `permission_broker_foundation.py` (unchanged) | `test_runtime_dispatch_permission.py` | First authority/PB phase (verify unchanged); Phase B (future eligibility rule) |
| RDGO-001 gates 8-11 | Shell Gate / RE / adapter | — | Later phases |

## 53. Gate implementation matrix

(Restated from §6 for the report's required table.)

| Gate | Current state | First implementation | Later phase |
|---:|---|---|---|
| 1 | Dry-path hashing exists, real profile missing | Yes | — |
| 2 | ID generators exist | Yes | — |
| 3 | Missing | Yes | — |
| 4 | Preflight machinery exists for dry path | Yes | — |
| 5 | Missing | Yes | — |
| 6 | PB machinery exists, action missing | Yes | — |
| 7 | Mock-only coordinator exists | No | Yes (RE phase) |
| 8 | Missing | No | Yes (Shell Gate phase) |
| 9 | Atomic-write pattern exists, real record missing | Staged/non-consuming only | Yes (full consumption, Shell Gate phase) |
| 10 | Mock adapter only | No | Yes (Shell Gate + first real adapter phase) |
| 11 | Mock capture exists (MUST-FIX #1 here) | No | Yes (Shell Gate phase; repair MUST-FIX #1 no later than here) |

## 54. Identifier matrix

| ID | Created by | Stored where | Used by | Reusable? |
|---|---|---|---|---|
| `invocation_id` | Trusted coordinator (`new_invocation_id`, existing) | Future `RuntimeInvocationRecord`; approval `subject` | Gates 2–11 | Yes — reuse existing generator |
| `attempt_id` | Trusted coordinator (`new_attempt_id`, existing) | Future record; PB request | Gates 2–11 | Yes — reuse existing generator |
| `idempotency_key` | Trusted coordinator (extend `compute_idempotency_key`) | Future record; PB request | Gates 2–11 | Partially — reuse hashing shape, widen input projection |
| `approval_id` | New RIHAC-001 coordinator | Approval store (`ria-<32-hex>`) | Gates 3/5/9 | No — new |
| PB decision ID | Existing `PermissionBrokerDecision` shape | PB decision record | Gates 6/7/9 | Yes — existing decision model |
| RE decision ID | Existing RE contract shape (not yet production-consumed here) | Future RE decision record | Gates 7/9 | Yes (contract shape) — not implemented this phase |

## 55. Persistence matrix

| Artifact | Current | Planned first phase | Later |
|---|---|---|---|
| Approval | None | `.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json`, create-only | — |
| Invocation (real-dispatch) | None (dry-path store is separate, untouched) | Not created — deferred | New store, Shell Gate phase |
| PB decision | Existing `PermissionBrokerDecision` (in-memory/evaluation-time) | Same shape reused for `runtime_dispatch` | Durable persistence with gate 9, later |
| RE decision | Not production-consumed | Not created | RE phase |
| Dispatch attempt (gate 9, 8-item durable record) | None | Not created (staging only, no consumption claim) | Shell Gate phase |

## 56. Stop conditions

Any future authority/PB implementation phase must STOP and return to
governance if it discovers a need to: change RIHAC/PBRD/RDGO/RIASC
semantics; activate Runtime Enforcement; activate Shell Gate; relax
POL-005 for actual dispatch; spawn a process; access credentials; enable
network; introduce provider/model execution; invent broader human
authority (e.g. reusable/session-wide approval). None of these are
required by the scope defined in §57–59 below; if implementation reveals
otherwise, that is itself the stop signal.

## 57. Implementation sequence

Derived, not copied blindly, and confirmed consistent with source
structure read in this phase:

1. **Stage 1** — `RuntimeInvocationApproval` model + RIASC-001 schema validator + canonical store (§10–12).
2. **Stage 2** — Authority creation/validation service; internal-API-only creation (Option A, §13); full RIHAC-001 ordered validator (§15).
3. **Stage 3** — Attempt/idempotency primitives: extend existing `new_attempt_id`/`compute_idempotency_key` for the real-dispatch fact set (§19–20).
4. **Stage 4** — PB `runtime_dispatch` request shape/action vocabulary: `runtime_dispatch_context` field (Option B, §17), action constant (§18).
5. **Stage 5** — Trusted approval projection into PB (§22).
6. **Stage 6** — PB evaluation while POL-005 remains hard deny (§24); verify precedence and existing-action regressions (§35).
7. **Stage 7** — Focused E2E across the full stage-1-through-6 chain, no external effect (§37).
8. **Stage 8** — Independent verification (separate phase, §60).

This order is used as given; nothing in the source structure read this
phase contradicts it (the dry-path's existing ID generators and atomic
store pattern slot naturally into stages 1/3, confirming the sequence is
buildable in this order without forward references to unbuilt pieces).

## 58. Commit plan

Recommended logical commits for the future implementation phase (kept
separable for audit, per governing instructions §58):

1. `runtime_authority.py` model + schema validator (Stage 1, part 1).
2. Approval store (Stage 1, part 2).
3. Authority validation service (Stage 2).
4. Attempt/idempotency extension to `runtime_invocation.py` (Stage 3).
5. `runtime_dispatch_permission.py` + PB foundation additive field/constant (Stage 4–5).
6. PB evaluation tests + POL-005/POL-004 regression proof (Stage 6).
7. Full E2E + no-external-effect proof (Stage 7).

Authority-layer commits (1–3) and PB-layer commits (4–6) are kept
separable so either can be independently reviewed/reverted without
touching the other.

## 59. First implementation phase scope

**Recommended name:** *Runtime Invocation Authority + PB Dispatch
Request Foundation Implementation.*

Scope: Stages 1–7 of §57 — approval artifact/store/validation, attempt/
idempotency identities, `runtime_dispatch` request/action representation,
PB evaluation plumbing — while leaving: POL-005 real-deny intact
(verified by regression test, not just left alone); Runtime Enforcement
not activated; Shell Gate not activated; process spawn impossible (no
adapter dispatch code path added or touched).

## 60. Independent verification after implementation

Required, as a **separate** phase — not self-certified within the
implementation phase itself, matching this repo's established pattern
(every implementation phase in this project's history has been followed
by an independent-verification phase before further build-out, e.g.
3V→3V.1, 3V.1R→3V.1R.1, 3S→3S.1, 3S.2→3S.2.1). Authority/PB
implementation and RE integration MUST NOT be planned or self-certified
in one phase.

## 61. Later dependency sequence

Re-derived, preserving staged trust, not merely repeated:

```text
Authority/PB foundation (implementation)
  -> Independent verification
  -> Runtime Enforcement real-gate implementation
  -> Independent verification
  -> Shell Gate/process containment implementation
     (repair MUST-FIX #2 class of gap in the real-dispatch record store
      here if not already addressed; repair MUST-FIX #1 no later than
      the first non-mock adapter)
  -> Independent verification
  -> Runtime inspect reconciliation (repair TRUTHFUL_WITH_LIMITATION,
     §33, before any real-adapter availability claim)
  -> Deterministic fixed-argv real local-process fixture (first real
     process — generic, non-AI, per §62)
  -> Independent verification
  -> Codex/Claude adapter planning
```

## 62. First real process fixture

Carried forward from 3T: the first real process should be a **generic
local fixed-argv deterministic non-AI fixture**, not Codex or Claude —
this validates process governance without model/provider complexity.
Not implemented in 3V.2; recommendation only.

## 63. API/network boundary

Out of scope. No OpenRouter/API/provider implementation planning beyond
acknowledging it as future dependency (RIHAC-001 §2 / PBRD-001 §11 both
explicitly exclude API/provider transports from local-CLI-v1 scope).

## 64. Release implications

No release in this phase. `v0.4.3` (`63580893...`) is unchanged. The
runtime chapter may eventually justify a `v0.5.0`, but no version is
frozen or implied here.

## 65. Final verdict

Planning complete. Zero `src/pcae` production changes. Zero test changes.
Zero execution activation. All four verified contracts (RIHAC-001 v1.0,
RIASC-001 v1.0, PBRD-001 v1.1, RDGO-001 v2.0) read directly and used as
the sole normative source for every field/gate/fact table above. Both
3S.2.1 MUST-FIX findings recovered verbatim and confirmed not reachable
by the recommended first implementation phase.

## 66. Exact next phase

**Runtime Invocation Authority + PB Dispatch Request Foundation
Implementation** (§59) — an implementation phase covering Stages 1–7 of
§57, followed mandatorily by a separate independent-verification phase
(§60) before any Runtime Enforcement work begins.

## 67. Human decision required

This phase does not authorize or begin the recommended next
implementation phase. A human decision is required to proceed.
