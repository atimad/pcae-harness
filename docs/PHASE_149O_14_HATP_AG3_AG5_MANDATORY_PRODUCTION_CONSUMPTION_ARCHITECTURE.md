# Phase 149O.14 — HATP AG3/AG5 Mandatory Production Consumption Architecture

Phase type: **ARCHITECTURE ONLY**. No production source under `src/pcae/` was
modified by this phase. No contract (`HSCE-001`, `HATP-001`, `RAE-001`) was
modified. Pre-phase HEAD: `def1621e4d2fb9c8f297a3fefa0f11fa7863d78d`.

## 0. Baseline

- Latest completed phase: 149O.13 — HATP Signing Ceremony + Evidence Store
  Independent Implementation Verification. Verdict: VERIFIED WITH
  NON-BLOCKING FINDINGS — HSCE-001 v1.1 CONFORMS. HATP signing surface
  independently verified as **evidence creation only** — not rollback
  authorization or execution.
- AG3 mandatory HATP consumption: NOT IMPLEMENTED.
- AG5 mandatory HATP consumption: NOT IMPLEMENTED.
- HATP production state: NOT READY.
- Runtime: Observed / observe / unavailable. Permission Broker:
  `execution_unavailable`. Governance posture: non-executing.
- B-149O-1..4: INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY —
  SYSTEM EXECUTION CLOSURE DEFERRED. This phase does not close them.

## 1. Current AG3 call graph (reconstructed by direct source reading)

Entry: `pcae remote rollback execute <job_id>` (`cli.py:4174-4188`,
`remote_rollback_execute_parser`, no `--hatp-evidence-id`/`--hatp-evidence`/
`--hatp-proof` flag exists) → `commands/agent.py:run_remote_rollback_execute`
(`commands/agent.py:2236-2244`) → `core.agent.execute_rollback(root, job_id)`
called with **no HATP keyword arguments** → `core/agent.py:5234-5373`.

Inside `execute_rollback`:

1. `hatp_evidence_id` optional param (default `None`, `agent.py:5238`). The
   real CLI call site never supplies it (confirmed at `commands/agent.py:2238`
   — call is `execute_rollback(HarnessPath.cwd(), args.job_id)`, positional
   only, zero keywords).
2. If `hatp_evidence_id is not None` (never true for the current production
   caller), a purely **additive** block (`agent.py:5277-5302`) calls
   `hatp_ag_authority.resolve_ag3_gated_rollback_authority(...)` and stores
   the result under `hatp_authority` in the return dict. This never affects
   control flow before it.
3. Real dispatch precondition, unconditional on the block above:
   `rollback_approval_state` is read from the job file
   (`agent.py:5323`, `job.get("rollback_approval_state", "pending")`).
   `"pending"` → `ValueError` (must call `pcae remote rollback approve`
   first); `"denied"` → `ValueError`; anything other than `"approved"` →
   `ValueError`.
4. Additional structural preconditions: `rollback_eligible`
   (`agent.py:5339`), `rollback_mode_recommendation == "revert_commit"`
   (`agent.py:5346`), clean working tree (`agent.py:5354`), original commit
   reachable from HEAD (`agent.py:5361`).
5. Real effect: `_run_git_revert(original_commit_sha, ...)` at
   `agent.py:5367` — an actual `git revert --no-edit` subprocess call that
   mutates the repository.
6. Permission Broker is **never consulted** on this path unless the inert
   `hatp_evidence_id`-supplied branch runs, and even then its result is
   attached to the return value for audit only — it does not gate step 5.

**Conclusion**: AG3's sole real production dispatch precondition today is
`rollback_approval_state == "approved"`, set exclusively by
`approve_rollback` (`agent.py:5146-5182`, `pcae remote rollback approve`,
`commands/agent.py:2198-2214`). HATP evidence, even if supplied, is
observational only on this path today.

## 2. Current AG5 call graph (reconstructed by direct source reading)

Entry: `pcae rollback --per-id <id> [--dry-run]` (`cli.py:3035-3055`, no
HATP flag exists) → `commands/agent.py:run_rollback`
(`commands/agent.py:16258-16259`, `build_rollback_execution(HarnessPath.cwd(),
args.per_id, dry_run=args.dry_run)` — no HATP keywords) →
`core/agent.py:build_rollback_execution` (`agent.py:93952-94179`).

Inside `build_rollback_execution`:

1. `hatp_evidence_id` optional param (default `None`, `agent.py:93957`).
   Never supplied by the real CLI call site (confirmed by direct read of
   `commands/agent.py:16259`).
2. If supplied (never true today) and the PER resolves
   (`agent.py:93980-93981`), an additive block calls
   `hatp_ag_authority.resolve_ag5_gated_rollback_authority(...)` and attaches
   `hatp_authority` to the return dict — again never gates anything below it.
3. Real structural preconditions, unconditional on the HATP block: PER must
   exist (`agent.py:94006-94013`); `per.status` must be in
   `_RER_PER_ELIGIBLE_STATUSES = {"completed", "partial"}`
   (`agent.py:93781`, `94014-94020`); `per.rollback_payload_available` must
   be `True` (`agent.py:94021-94027`); ECP must resolve
   (`agent.py:94029-94037`); no RER already `in_progress` for this PER
   (`agent.py:94039-94047`); divergence check must be non-blocking
   (`agent.py:94089-94097`).
4. If `dry_run`, returns a preview with `execution_allowed: False` and
   writes nothing (`agent.py:94052-94065`).
5. **If not `dry_run` and all structural preconditions pass, real file
   mutation occurs unconditionally**: for each entry in `file_plan`,
   `full_path.write_bytes(...)` / `full_path.write_text(...)` /
   `full_path.unlink()` (`agent.py:94108-94147`) — an actual filesystem
   mutation that restores or removes production-tree files. The result dict
   still carries the label `"execution_allowed": False`
   (`agent.py:94173`), but that label is descriptive metadata, not a gate:
   nothing in the function checks it before performing the writes.
6. Permission Broker is never consulted on the real-mutation path unless the
   inert HATP block ran, and even then only advisory.

**Conclusion**: AG5's real production dispatch preconditions today are the
PER-status/divergence/payload-availability structural checks in step 3 —
there is **no human-approval gate on AG5 at all today** (no analogue of
`rollback_approval_state` exists for AG5; PER eligibility is a structural,
not an approval, fact).

## 3. The "PB advisory problem" — investigated, not assumed

The governing prompt requires this be independently investigated rather
than inferred from PB's `execution_unavailable` label. Findings above show:

- AG3 performs a real `git revert` subprocess mutation
  (`_run_git_revert`, `agent.py:5367`) gated only by legacy
  `rollback_approval_state` + structural checks — **not** by Permission
  Broker.
- AG5 performs real file-level mutation (write/unlink,
  `agent.py:94108-94147`) gated only by PER-status/divergence structural
  checks — **not** by Permission Broker, and with no human-approval gate
  of any kind today.
- Permission Broker's `execution_unavailable` / POL-005 status governs
  only the **advisory evaluation path inside `hatp_ag_authority`**
  (invoked with `simulation_only=True`,
  `hatp_ag_authority.py:172`, so POL-005 itself never triggers there
  either — `ExecutionDisabledRule.evaluate` short-circuits to
  `_not_triggered` when `simulation_only`). PB's advisory status says
  nothing about, and does not gate, the real AG3/AG5 mutation paths above.

**Architecture inconsistency, honestly documented**: today's real AG3/AG5
production effects are **not** blocked by "PCAE execution capability
unavailable" — that label describes the *separate*, not-yet-built
`COMP-002`/PB-enforcement boundary, and Permission Broker's advisory
`execution_unavailable` posture has no causal relationship to whether
`git revert` or file writes actually happen. AG3/AG5 dispatch is governed
today exclusively by the legacy preconditions identified in §1/§2. This is
precisely the gap this architecture closes for the **human-approval
source**, while explicitly leaving PB **execution enforcement**
(COMP-002) to a separate, later track (§13).

## 4. Current Wave-7 HATP hook inventory

| Location | Parameter | Classification |
|---|---|---|
| `agent.py:5238` `execute_rollback` | `hatp_evidence_id: str \| None = None` | Optional, unsupplied by real caller; future locator hook |
| `agent.py:5239` `execute_rollback` | `hatp_proof: object \| None = None` | Optional, unsupplied; legacy raw-proof compatibility hook |
| `agent.py:5240` `execute_rollback` | `hatp_evidence: object \| None = None` | Optional, unsupplied; legacy raw-evidence compatibility hook |
| `agent.py:93957-93959` `build_rollback_execution` | same 3 params | Same classification, AG5 side |
| `hatp_ag_authority.py:185-186,232-233` | `hatp_proof`, `hatp_evidence` (required kwargs on the adapter itself) | Non-authority-bearing by themselves — passed through to `resolve_rollback_approval_evidence_with_hatp`, which still requires a valid RAE binding + fresh `verify_hatp_proof` result to produce `approval_present=True` |
| `hatp_ag_authority.py:184,231` | `evidence_id: str` (required) | Currently unused for loading — no envelope-store `load()` call exists anywhere in `hatp_ag_authority.py` today; it is accepted but not dereferenced against `HATPEvidenceStore` |

None of these are authority-bearing on the real production dispatch paths
today (§1, §2). All are test-only/future-hook in effect, since no real
caller supplies them.

**Key gap found**: `hatp_ag_authority.py`'s `_resolve_gated_approval`
accepts `hatp_proof`/`hatp_evidence` directly rather than loading a
persisted `HATPSignedEvidenceEnvelope` via `HATPEvidenceStore.load
(evidence_id)`. It never calls `HATPEvidenceStore.load` at all. This is the
central seam §7/§8 below must close: today's Wave-7 adapter and the
149O.12 HSCE evidence store are two structurally separate mechanisms that
happen to share an `evidence_id`-shaped parameter name but are not wired
together.

## 5. Current HSCE evidence store / signing APIs (unchanged by this phase)

- `HATPEvidenceStore.load(self, evidence_id: str) -> HATPSignedEvidenceEnvelope`
  (`hatp_evidence_store.py:149`). Explicit ID only — no "latest"/glob
  lookup method exists on the class. Raises `EvidenceNotFoundError` (subclass
  of `HATPEvidenceStoreError`) on a missing ID; performs no HATP
  verification and derives no approval — purely a keyed file read +
  envelope parse.
- `build_hatp_signed_evidence_envelope(...)` /
  `parse_hatp_signed_evidence(...)` / `HATPSignedEvidenceEnvelope`
  (`hatp_signed_evidence.py:181-345`) — the canonical persisted evidence
  artifact and its parser/serializer. Closed schema; digest-bound;
  version-checked (`UnsupportedEvidenceVersionError`); malformed input fails
  closed (`MalformedEvidenceEnvelopeError`, `InvalidEvidenceEnvelopeSchemaError`,
  `EvidenceIdDigestMismatchError`).
- `pcae hatp sign rollback --site {ag3,ag5} --job-id/--per-id ...`
  (`cli.py:10528-10556`, `commands/hatp.py:run_hatp_sign_rollback`) is
  registered and is the sole production signing entry point. Its own
  module docstring and 149O.13's verification confirm it creates evidence
  only — never mutates `rollback_approval_state`, never calls Permission
  Broker, never dispatches rollback.

## 6. Current gated-authority adapter API (Wave 7, unchanged by this phase)

`resolve_ag3_gated_rollback_authority` / `resolve_ag5_gated_rollback_authority`
(`hatp_ag_authority.py:177-264`) accept, per site: the operation locator
(`job_id`+`original_commit_sha` for AG3; `per_id`+`ecp_id` for AG5),
`task_id`, `repository_state: RepositoryStateBinding`, `evidence_id: str`,
`hatp_proof: Optional[HumanApprovalProvenanceProof]`,
`hatp_evidence: HATPVerificationEvidence`, plus optional `evaluation_time`,
`evidence_store`, `publication_root` overrides (RAE evidence *location*
overrides, not trust/authority — F-2 already closed: no `hatp_provider`/
`hatp_trust_store` parameter exists anywhere on this surface; those are
resolved internally from `HATPTrustStore.production()` and
`create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`,
`hatp_ag_authority.py:124-125`). They return `GatedRollbackAuthorityResult`
(`approval_evidence: HATPIntegratedApprovalEvidence`,
`permission_decision: PermissionBrokerDecision`). Internally they call
`resolve_rollback_approval_evidence_with_hatp` (`rollback_approval_evidence.py:1517`),
which validates the RAE binding, runs `verify_hatp_proof` fresh
(`human_approval_trusted_provenance.py:762`), and cross-checks
Decision/Binding digests before deriving `approval_present`. **They accept
raw `hatp_proof`/`hatp_evidence` directly — they do not call
`HATPEvidenceStore.load(evidence_id)` internally.** This is the load-bearing
gap this architecture resolves.

## 7. Gap decomposition

| Gap | Description |
|---|---|
| G1 | No production caller ever supplies `hatp_evidence_id` — the hook exists but is dead on real paths. |
| G2 | `hatp_ag_authority` accepts raw proof/evidence, not a loaded, digest-bound `HATPSignedEvidenceEnvelope` — the HSCE evidence store and the Wave-7 adapter are unwired. |
| G3 | AG3's real dispatch gate is legacy `rollback_approval_state`, entirely independent of HATP. |
| G4 | AG5 has no human-approval gate at all — only structural PER checks. |
| G5 | No CLI surface exists to pass an evidence reference into either rollback path. |
| G6 | No cutover mechanism exists to ever make HATP the exclusive authority source. |
| G7 | Permission Broker's advisory posture is unrelated to the real production mutation boundary (§3) — the mutation boundary itself is not currently PB-mediated at all, by design deferred to COMP-002, but the *human-approval-fact* boundary (this phase's actual scope) is independently closable now. |

## 8. Architecture alternatives considered

**A. CLI-level evidence verification only.** Verify the evidence at the CLI
handler (`run_remote_rollback_execute`/`run_rollback`) before calling into
`core.agent`. **Rejected.** `execute_rollback`/`build_rollback_execution`
are directly importable and callable from `pcae.core.agent` by any Python
caller (tests, other commands, future integrations) without going through
`cli.py` at all — confirmed by direct import graph inspection
(`commands/agent.py:153,382` import them directly; nothing prevents a third
call site from doing the same). A CLI-only check is trivially bypassed by
any direct-function caller, violating MC-11 (every effectful production
caller covered) and BLOCKING-condition "CLI-only gating with direct
function bypass" (§164).

**B. Effect-boundary mandatory adapter.** Place mandatory,
evidence-ID-driven, fresh-verifying HATP consumption immediately adjacent
to the actual effect boundary inside `core.agent.execute_rollback` /
`core.agent.build_rollback_execution` themselves (i.e., inside the same
function that performs `_run_git_revert` / the file-write loop), so every
caller — CLI or direct function call — passes through the identical gate.
**SELECTED.** This is the only alternative that structurally cannot be
bypassed by a direct-call caller, since the gate lives inside the one
function every caller (CLI and non-CLI) must call to cause the effect.

**C. Persistent approval-state conversion.** Have signing (`pcae hatp sign
rollback`) or a follow-up step directly write a new
`hatp_approval_present=True`-shaped field onto the job/PER record, and have
AG3/AG5 read that persisted field instead of `rollback_approval_state`.
**Rejected.** This reintroduces exactly the cached/stale-approval problem
HSCE-001 and this phase's MC-1..MC-13 forbid: a persisted boolean cannot
reflect signer revocation, Binding/Decision mutation, or evidence deletion
that occurs after the field is written, and it re-creates a second
authority-bearing field parallel to `rollback_approval_state` (dual
authority, a BLOCKING condition per §164). Every consumption must
re-verify fresh (MC-2/MC-3).

**D. Command-session capability token.** Issue a short-lived, in-process
capability token after a prior verification step, redeemable once for
dispatch. **Not evaluated as primary** — no existing PCAE architecture
supports session/capability tokens (no such primitive exists in
`permission_broker_foundation.py`, `hatp_ag_authority.py`, or elsewhere),
and it reintroduces a cache (token = cached ALLOW) that fails MC-3 unless
redemption itself re-verifies, at which point it degenerates to option B
with extra machinery. Deferred/rejected as unnecessary complexity relative
to B.

**Selected: B — effect-boundary mandatory adapter**, with explicit evidence
ID, fresh HATP verification on every attempt, and a protected one-way
cutover gating when the adapter becomes exclusively authoritative.

## 9. Target authority chain (normative)

```
rollback command (CLI or any direct function caller)
  → explicit evidence_id (caller-supplied locator, no default)
  → HATPEvidenceStore.load(evidence_id)          [existing API, §5 — reused, not reimplemented]
  → HATPSignedEvidenceEnvelope                    [existing model, §5]
  → mandatory consumption-time verification via resolve_rollback_approval_evidence_with_hatp
      → resolve_rollback_approval_evidence (RAE)  [existing, §6 — reused]
      → verify_hatp_proof(...)                    [existing engine, §5/§6 — reused, no second verifier]
      → Decision/Binding digest cross-check        [existing, §6]
      → current-state readiness/revocation check   [existing, inspect_hatp_verification_substrate_readiness]
  → approval_present: bool                        [derived fact, HATPIntegratedApprovalEvidence]
  → Permission Broker request (build_permission_broker_request + PermissionBroker().evaluate)
  → PB decision: ALLOW | DENY | HUMAN_REVIEW       [PB remains sole decision engine]
  → existing effect boundary (git revert / file-restore), gated per §12 cutover semantics
```

No alternate authority chain exists. Raw proof/evidence objects never enter
this chain directly on a mandatory-consumption path (§11).

## 10. Evidence reference design — frozen CLI syntax

- AG3: `pcae remote rollback execute <job_id> --hatp-evidence-id <evidence_id>`
- AG5: `pcae rollback --per-id <per_id> --hatp-evidence-id <evidence_id>`

Rationale: `--hatp-evidence-id` mirrors the exact term `evidence_id` already
used throughout HSCE-001/`hatp_evidence_store.py`/`hatp_ag_authority.py`,
and mirrors the naming convention of existing locator flags (`--per-id`,
`--job-id`, `--rer-id`) already present in `cli.py`. **Forbidden on this
flag surface** (§164, explicitly frozen now, not left TBD): no raw evidence
file path flag; no inline proof JSON flag; no provider/trust-store override
flag; no `--approved`/`--approval-present`/`--human-approved` boolean flag.
ID only. `evidence_id` is a **locator, not authority** (MC-1) — supplying it
only identifies which envelope to load; every use still requires fresh
consumption-time verification (§11/§13).

## 11. Canonical consumption object and raw-proof-hook disposition (§16/§17/§18)

**Decision (§16 option A, selected):** mandatory production consumption
accepts **`evidence_id` only** at the command surface. The command layer
never accepts a raw proof or raw evidence object. Internally, the effect-
boundary adapter (§9) loads the canonical `HATPSignedEvidenceEnvelope` via
`HATPEvidenceStore.load(evidence_id)` and derives `hatp_proof`/
`hatp_evidence` **from the loaded, digest-bound envelope only** before
calling the existing `resolve_rollback_approval_evidence_with_hatp` engine
— the existing engine's raw-parameter shape (§6) is reused as an internal
implementation detail behind the loader, never as an independently
caller-authoritative input.

**Legacy hook disposition (§18), decided individually — no hook is left
"still accepted and maybe authoritative":**

| Parameter | Disposition |
|---|---|
| `execute_rollback`'s / `build_rollback_execution`'s `hatp_evidence_id: str \| None` | **Retained as the sole production-facing hook**, becomes mandatory (no longer optional) once cutover applies to a given deployment (§13); pre-cutover, retained exactly as-is (additive, optional) for LEGACY_COMPATIBLE deployments. |
| `execute_rollback`'s / `build_rollback_execution`'s `hatp_proof: object \| None` | **Removed from the mandatory-consumption path.** Internal-only: retained solely as a private/test-only construction seam one layer below the public function (e.g., usable by unit tests that need to bypass the store), never independently authoritative once cutover applies. On a HATP_MANDATORY deployment, a future contract-freeze phase (149O.15) must specify that the public function signature either ignores this parameter or rejects a caller-supplied value outright when `hatp_evidence_id` is also present, to prevent ambiguity — 149O.14 selects "internal-only, non-authoritative" as the target disposition and defers the exact mechanical rejection to 149O.15. |
| `execute_rollback`'s / `build_rollback_execution`'s `hatp_evidence: object \| None` | Same disposition as `hatp_proof` above — internal/test-only, non-authoritative. |
| `hatp_ag_authority.resolve_ag3/ag5_gated_rollback_authority`'s `hatp_proof`/`hatp_evidence` required kwargs | **Retained internally** as the adapter's own interface to the existing verification engine (§6), but the *effect-boundary adapter* (§9, the new code this architecture calls for) becomes the only production caller of these functions, and it derives both values from the loaded envelope — never forwards a caller-supplied raw value. |

This closes §17's requirement precisely: production command surface is
`evidence_id`-only; the production authority adapter resolves the envelope
internally; raw `hatp_proof`/`hatp_evidence` are no longer independently
caller-authoritative on any mandatory production path.

## 12. Fresh verification semantics (MC-2/MC-3, §10 of governing prompt)

Every consumption attempt — first or repeated, across processes, across
worktrees — re-runs the full chain in §9 from a fresh
`HATPEvidenceStore.load` through a fresh `verify_hatp_proof` call with
`evaluation_time` bound to the current attempt. No persisted
`approval_present`, no persisted `verified=True`, no persisted PB `ALLOW`
is ever read back and reused (MC-3). This requires no new caching
component to be built — it requires the target architecture to **not**
introduce one; the existing `resolve_rollback_approval_evidence_with_hatp`
already takes `evaluation_time` as a mandatory explicit parameter
(`rollback_approval_evidence.py:1517-1546`) precisely so no internal
`datetime.now()` caching can occur — this discipline is reused unchanged.

## 13. AG3 target consumption flow

```
pcae remote rollback execute <job_id> --hatp-evidence-id <evidence_id>
  → run_remote_rollback_execute (CLI handler) passes hatp_evidence_id through, unchanged shape
  → execute_rollback(root, job_id, hatp_evidence_id=...)
      → [existing structural preconditions unchanged: eligibility, revert-mode, clean tree, ancestor commit]
      → [NEW, effect-boundary-adjacent] mandatory evidence load + fresh verification (§9)
          via a new internal loader step ahead of hatp_ag_authority.resolve_ag3_gated_rollback_authority
      → approval_present derived
      → Permission Broker request/decision (existing resolve_ag3_gated_rollback_authority call, unchanged)
      → dispatch gating per §21 cutover-state rules
      → _run_git_revert (existing, unchanged)
```

Direct-function callers (non-CLI) hit the identical gate because it lives
inside `execute_rollback` itself, immediately ahead of the existing
`_run_git_revert` call — not in `commands/agent.py` or `cli.py`.

## 14. AG5 target consumption flow

```
pcae rollback --per-id <per_id> --hatp-evidence-id <evidence_id>
  → run_rollback (CLI handler) passes hatp_evidence_id through
  → build_rollback_execution(root, per_id, hatp_evidence_id=..., dry_run=...)
      → [existing structural preconditions unchanged: PER exists/status/payload/ECP/no-in-progress-RER/divergence]
      → [NEW, effect-boundary-adjacent] mandatory evidence load + fresh verification (§9)
      → approval_present derived
      → Permission Broker request/decision (existing resolve_ag5_gated_rollback_authority call, unchanged)
      → dispatch gating per §21 cutover-state rules
      → file write/unlink loop (existing, unchanged)
```

Same direct-call-bypass-proof placement rationale as AG3 (§8 option B).

## 15. Effect-boundary placement and direct-call coverage (MC-11)

The mandatory gate must sit inside `core.agent.execute_rollback` and
`core.agent.build_rollback_execution` themselves, immediately ahead of
`_run_git_revert` (AG3) and the file write/unlink loop (AG5) respectively —
**not** in `commands/agent.py`, **not** only in `cli.py`. Both the remote
CLI path and any local/direct function-call path converge on these same two
functions (confirmed: no second implementation of rollback dispatch exists
anywhere in the codebase — `execute_rollback`/`build_rollback_execution`
are each defined exactly once, `agent.py:5234`/`93952`). This satisfies the
governing prompt's requirement that "if rollback can be invoked through
both a remote command path and a local function path, both must converge
on the exact same mandatory effect boundary."

## 16. Legacy `approve` command disposition (§21)

**Pre-cutover (LEGACY_COMPATIBLE):** `pcae remote rollback approve` retains
its exact current behavior (§16 option B analogue for the pre-cutover
window) — it remains the operative authority source for AG3 on any
deployment that has not transitioned.

**Post-cutover (HATP_MANDATORY):** selected disposition is **§21 option C**
— the command remains registered and visible, but deterministically emits a
non-mutating deprecation failure explaining that HATP signing
(`pcae hatp sign rollback`) plus explicit `--hatp-evidence-id` consumption
is now required; it must not mutate `rollback_approval_state` at all once
mandatory mode applies for that deployment. Option A (remove entirely) is
rejected for this phase because removing a command is an implementation
action, not architecture, and because a hard removal is a harsher
transition than necessary — a clear deterministic error preserves
discoverability. Option D (convert into a signing alias) is rejected per
the governing prompt's own steer — the architecture already has a
dedicated, independently-verified signing surface (`pcae hatp sign
rollback`), and conflating "approve" with "sign" would blur the exact
principal-separation distinction §26 relies on.

## 17. `rollback_approval_state` future semantics (§22)

- **Pre-cutover:** unchanged — authority-bearing dispatch precondition for
  AG3, exactly as today (§1).
- **Post-cutover:** becomes **migration-compatibility / historical
  metadata only**. It continues to be read and displayed (for audit
  continuity and to avoid deleting historical data), but it MUST NOT
  independently authorize dispatch. The mandatory boundary (§9/§13) does
  not consult it as an authority input once a deployment is
  `HATP_MANDATORY`. This is a "deprecated metadata" disposition, not "field
  removed" (removal is left to a later phase if ever desired) and not
  "historical/display-only" in the sense of being scrubbed of meaning — it
  remains a legitimate, inspectable trace of what happened under the prior
  regime.

## 18. AG5 PER-status / structural precondition classification (§23/§24)

Mandatory HATP evidence replaces **only** the human-approval authority
source. It explicitly does not, and per the target architecture must not,
override any of AG5's existing structural/safety preconditions:

| Precondition | Classification | Survives cutover unchanged? |
|---|---|---|
| PER exists | Structural | Yes |
| `per.status in {"completed","partial"}` | Structural/safety | Yes |
| `per.rollback_payload_available is True` | Structural/safety | Yes |
| ECP resolves | Structural | Yes |
| No RER already `in_progress` for this PER | Structural/safety (concurrency) | Yes |
| Divergence check non-blocking | Structural/safety (drift detection) | Yes |
| (AG3 only) `rollback_approval_state == "approved"` | **Human-approval authority** | **No** — this is exactly the field superseded post-cutover (§17); it is the only precondition in either call graph that is a human-approval source rather than a structural/safety fact |

AG5 has no existing human-approval-authority precondition at all today
(§2) — mandatory HATP consumption is a strictly additive human-approval
gate for AG5, not a replacement of any existing AG5 check.

## 19. One-way cutover state machine (§25-32)

**States (smallest sufficient machine):**

- `LEGACY_COMPATIBLE` — default state for every existing deployment,
  including the current local development host. Legacy
  `rollback_approval_state`/AG3 and structural-only/AG5 remain fully
  operative exactly as today. HATP evidence, if supplied, is evaluated
  advisory-only (§20) and never gates.
- `PREPARED` — an intermediate, still-non-authoritative state indicating a
  deployment has satisfied every prerequisite for cutover (Class-B
  substrate operational, HSCE signing available, mandatory-consumption
  implementation present and independently verified, HATP-gated authority
  independently verified) but has not yet been activated by protected
  administrative action. Legacy authority remains fully operative in this
  state — `PREPARED` is informational/gating-readiness only, never itself
  a trigger.
- `HATP_MANDATORY` — legacy `rollback_approval_state`
  (AG3)/no-equivalent-existed-anyway (AG5) is no longer consulted as an
  authority source (§17/§18); `--hatp-evidence-id` becomes a **required**
  argument on both `pcae remote rollback execute` and `pcae rollback`for
  this deployment; missing/invalid/corrupt evidence fails closed with no
  legacy fallback (§20/§22 below).

**Transitions:** `LEGACY_COMPATIBLE → PREPARED → HATP_MANDATORY` only. No
transition moves backward under any ordinary agent/runtime/CLI/env-var
mechanism (irreversible for ordinary principals, §19 requirement below).

**Transition trigger (`PREPARED → HATP_MANDATORY`):** must be caused by
**protected Class-B deployment/administrative authority**, never by: an
ordinary agent, a per-command caller, an environment variable, a CLI force
flag, or any repository-writable config file that an agent process can
edit. This derives directly from the existing Class-B activation
architecture already established in 149O.6/149O.7 (Class-B Deployment
Activation Implementation/Independent Verification) — this phase does not
invent a new activation mechanism, it reuses that existing
protected-activation authority model and applies it to this specific
transition. No automatic, readiness-triggered transition is permitted
(explicit protected-admin activation is strongly favored over any
automatic trigger, precisely to prevent a deployment from surprising an
operator by silently losing legacy rollback capability the moment
architecture code lands — this explicitly protects the current local
development host, which remains `LEGACY_COMPATIBLE` indefinitely unless a
real Class-B protected-activation event occurs for it).

**Cutover state storage:** must live in the Class-B protected
deployment/trust-root model, **not** in agent-writable `.pcae/`. This
mirrors the existing HATP trust-store/repository-identity storage
discipline (`HATPTrustStore.production()`,
`read_repository_identity`) rather than inventing new storage. Exact
storage location/schema is deferred to 149O.15 (contract freeze) — this
phase freezes only the state names and the storage-authority requirement
("Class-B protected, not agent-writable"), not a byte-level schema.

**Cutover record conceptual fields** (frozen at concept level only, per
§ "if a cutover record concept is used"): `version`,
`repository_instance_id`/deployment identity, `activated_at`,
`activating_authority` (identifies the protected principal, not an agent
identity), `mode` (`PREPARED`/`HATP_MANDATORY`). No signed-envelope schema
is invented here — that is explicitly deferred to 149O.15.

**Irreversibility:** no ordinary reversion path exists for an agent or
runtime process. No `--legacy`/`--skip-hatp`/environment-variable override
of any kind is permitted anywhere in the target architecture (explicitly
forbidden, §164's "reversible cutover by ordinary agent" is a BLOCKING
condition). If administrative disaster-recovery reversion is ever needed,
it must be a **separately governed mechanism** under the same or stronger
protected authority as forward cutover — 149O.14 explicitly defers
designing that mechanism rather than inventing one now.

## 20. Migration-mode / advisory HATP inspection (pre-cutover)

While `LEGACY_COMPATIBLE` or `PREPARED`, if `--hatp-evidence-id` is
supplied to either command (optional, exactly as today's Wave-7 hook
behaves), the resulting HATP verification/approval-derivation result is
**advisory only** — attached to the response for audit/observability
(exactly as today's `hatp_authority` result field, §1/§2 step 2) and never
an alternate authority source. Dispatch continues to be gated solely by
the pre-cutover preconditions in §1/§2. This is unchanged from today's
actual behavior — 149O.14 formalizes it as the explicit target semantics
for the `LEGACY_COMPATIBLE`/`PREPARED` states rather than changing it.

## 21. Dual-authority boundary precision (post-cutover)

Once `HATP_MANDATORY` applies to a deployment, there is **no OR condition**
between legacy-approved and HATP-approved. The mandatory boundary (§9)
becomes the **sole** source of the human-approval fact; legacy
`rollback_approval_state`/the (nonexistent, for AG5) legacy human-approval
field are not consulted at all as authority inputs (§17/§18). This is a
hard replacement, not a fallback chain — required by BLOCKING condition
"post-cutover legacy OR HATP authority" (§164).

## 22. Evidence-missing / invalid / expired / revoked semantics

**Pre-cutover:** irrelevant to dispatch — HATP evaluation, if attempted, is
advisory only (§20); a missing/invalid/expired/revoked evidence reference
simply yields `approval_present=False` in the advisory field, exactly as
`resolve_rollback_approval_evidence_with_hatp`'s existing fail-closed
umbrella already guarantees (unchanged code, §6).

**Post-cutover:** fail closed, no exceptions, for every case: missing
evidence (`EvidenceNotFoundError` from `HATPEvidenceStore.load`), corrupt
evidence (`MalformedEvidenceEnvelopeError`/`InvalidEvidenceEnvelopeSchemaError`),
digest mismatch (`EvidenceIdDigestMismatchError`), unsupported version
(`UnsupportedEvidenceVersionError`), invalid provider-assertion structure,
expired proof (`HATPVerificationStatus.EXPIRED`), revoked signer
(`HATPVerificationStatus.REVOKED_SIGNER`) — every one of these terminates
the mandatory-consumption chain with `approval_present=False` and the
rollback command fails; there is no legacy fallback available once
`HATP_MANDATORY` applies (§21). Repeated attempts (§ "repeated-execution-
attempt behavior") always re-run the full chain fresh — no result of a
prior attempt, successful or not, is cached or reused (§12).

## 23. Wrong-operation / cross-family / wrong-repository / wrong-deployment handling

All rejected via the **existing** HATP operation-binding machinery already
present in `resolve_rollback_approval_evidence_with_hatp`
(`_hatp_expected_operation_for(binding)`,
`rollback_approval_evidence.py:1579`) and `verify_hatp_proof`'s
`expected_operation`/`current_repository_id` parameters
(`human_approval_trusted_provenance.py:762` region) — no new binding logic
is designed by this phase. AG3-evidence-for-AG5 and AG5-evidence-for-AG3
both fail via this existing operation-family binding. Wrong-repository/
wrong-deployment evidence fails via the existing
`current_repository_id`/`canonical_deployment_root` binding already
threaded through `_resolve_gated_approval` (`hatp_ag_authority.py:106-150`).
Repository move/clone/worktree scenarios rely on this same existing
identity-binding mechanism, unchanged.

## 24. Decision/Binding replay prevention

Reuses the existing Decision/Binding digest cross-check already present in
`resolve_rollback_approval_evidence_with_hatp` (§6/§9) — a Decision or
Binding mutated after signing fails fresh consumption because that check
re-runs on every attempt (§12), against the current on-disk Decision/
Binding, not a value cached at signing time.

## 25. Permission Broker handoff (§ PB as sole decision engine)

`approval_present` is an **input fact**, never a decision. The mandatory
boundary always constructs a Permission Broker request via the existing
`build_permission_broker_request`/`PermissionBroker().evaluate` machinery
(`permission_broker_foundation.py`, already invoked internally by
`hatp_ag_authority._evaluate_rollback_permission`, §6) and always
**consults** PB — post-cutover, the `if hatp_valid: dispatch()` shortcut is
explicitly forbidden (BLOCKING condition, §164). PB may still return
`HUMAN_REVIEW` or `DENY` even given `approval_present=True` — rollback
logic must not treat a valid HATP fact as itself sufficient; only a PB
decision matters for what rollback logic does next, and PB's own
`ALLOW` remains distinct from actual execution capability
(`implementation_status="execution_unavailable"` while `COMP-002` does not
exist, §3/§26).

Diagnostic layering (kept distinct, never collapsed into one "approval
failed" message, per governing-prompt requirement): (1) evidence-load
error (`HATPEvidenceStoreError` subclasses), (2) HATP verification status
(`HATPVerificationStatus` vocabulary), (3) approval-derivation result
(`RollbackApprovalValidationResult`/`HATPIntegratedApprovalEvidence.
approval_present`), (4) PB decision (`DECISION_ALLOW`/`DECISION_DENY`/
`DECISION_HUMAN_REVIEW`), (5) rollback command failure (the CLI-level
error/exit code). Each layer surfaces its own vocabulary; none is
re-labeled as another.

## 26. PB / COMP-002 separation — intermediate milestone

This phase defines, but does not implement, an intermediate milestone:
**"MANDATORY HATP CONSUMPTION BOUNDARY"** — the state in which real AG3/AG5
permission evaluation obtains the human-approval fact *only* through fresh
HATP-gated evidence consumption (§9-§14), while the actual PB decision may
remain advisory/non-executing under the current architecture (PB `ALLOW`
still carries `implementation_status="execution_unavailable"` until
`COMP-002` exists). Reaching this milestone does **not** claim full system
execution closure. PB execution enforcement (`COMP-002`) is an explicitly
separate, deferred track this phase does not attempt to solve.

**Future finding language, once the milestone above is implemented and
independently verified** (not yet — this phase does not implement it):
`"MANDATORY CONSUMPTION BOUNDARY — PB EXECUTION ENFORCEMENT DEFERRED"` for
an intermediate B-149O-1..4 adjudication tier, to be used only by a future
implementation+verification phase pair, never claimed by this
architecture-only phase.

## 27. Principal separation, freshness, and remaining confirmations

- **Signing vs. consumption principal separation:** signing
  (`pcae hatp sign rollback`) occurs under a human/admin principal at
  ceremony time; consumption occurs under the agent/runtime principal at
  dispatch time. No assumption that file ownership of the evidence artifact
  establishes authority — the mandatory boundary trusts only the loaded,
  digest-verified envelope content, never filesystem metadata.
- Evidence signed **before** cutover remains consumable **after** cutover
  by default, provided it still independently verifies fresh at
  consumption time (no cutover-time-binding requirement is introduced —
  consumption always reverifies current state per §12, so pre- vs.
  post-cutover signing time is irrelevant to validity).
- Evidence created **after** cutover is normal and expected.
- Human signing need not happen in the same process/invocation as
  consumption (Class-B separation preserved, consistent with the existing
  ceremony architecture where `pcae hatp sign rollback` and the rollback
  command are already separate CLI invocations today).
- Multiple valid evidence artifacts for the same operation always require
  explicit `--hatp-evidence-id` selection — never automatic best-choice
  (§11 forbids implicit selection categorically).
- Concurrent/multi-process invocations and multiple worktrees/repository
  identities are handled correctly because no process-local cached boolean
  exists anywhere in this design (§12) and repository/deployment identity
  binding is the existing mechanism (§23) — no new concurrency-control
  logic is introduced.
- Signer rotation: a newly authorized signer is fine under the current
  trust state without changing cutover mode; a *revoked* prior signer's
  evidence still fails fresh verification (`HATPVerificationStatus.
  REVOKED_SIGNER`) regardless of cutover state.
- Disaster recovery: loss of hardware under `HATP_MANDATORY` fails closed —
  rollback becomes unavailable rather than silently re-enabling legacy
  authority. Recovery is deferred to a separately governed administrative
  mechanism (§19).

## 28. Current NOT_READY-deployment compatibility and pending legacy approvals at cutover

Every deployment defaults to `LEGACY_COMPATIBLE` (§19); a deployment whose
HATP substrate is `NOT READY` (like the current repository) simply never
becomes eligible for `PREPARED`, let alone `HATP_MANDATORY` — it is not
"bricked" by this architecture landing, because the transition is opt-in
and protected-admin-triggered, never automatic. Any
`rollback_approval_state == "approved"` job pending at the moment of a
hypothetical future cutover retains its legacy-approved status as
historical metadata (§17) but cannot be used to dispatch AG3 post-cutover —
it must be re-authorized via a fresh signed evidence artifact and explicit
`--hatp-evidence-id` consumption, exactly like any other post-cutover
dispatch attempt (§21, no grandfathering of pending legacy approvals into
mandatory-mode authority, since that would reintroduce the exact
legacy-OR-HATP dual-authority condition §21/§164 forbid).

## 29. Contract ownership, future production files, and traceability

### 29.1 Traceability table (§159)

| Concern | Current implementation | Target architecture | Owning future contract | Future production owner | Verification obligation |
|---|---|---|---|---|---|
| Evidence reference | none (no `--hatp-evidence-id` CLI flag) | `--hatp-evidence-id`, ID-only, both AG3/AG5 (§10) | 149O.15 (HATP Mandatory Production Consumption Contract Freeze) | `cli.py` parser additions | Independent verification: flag exists, no forbidden alternates registered |
| Load | none wired (`hatp_ag_authority` never calls `HATPEvidenceStore.load`) | Mandatory `HATPEvidenceStore.load(evidence_id)` call inside the effect-boundary adapter (§9/§11) | 149O.15 | `hatp_ag_authority.py` (or a new adapter module it delegates to) | Fail-closed load-error handling independently verified |
| Verify | `verify_hatp_proof` exists, unused by real callers | Same function, invoked fresh every attempt (§9/§12) | 149O.15 | unchanged (`human_approval_trusted_provenance.py`) | Re-verification-on-every-attempt independently confirmed (no cache) |
| Approval derivation | `resolve_rollback_approval_evidence_with_hatp` exists, unused by real callers | Same function, canonical, reused unchanged (§9/§15) | 149O.15 | unchanged (`rollback_approval_evidence.py`) | Single canonical derivation function confirmed (no duplicate logic) |
| PB handoff | `hatp_ag_authority._evaluate_rollback_permission` exists, unused by real callers | Same function, mandatory post-cutover, PB always consulted (§25) | 149O.15 | unchanged (`hatp_ag_authority.py`) | PB-always-consulted / no-shortcut independently confirmed |
| AG3 gate | `rollback_approval_state` only (§1) | Mandatory HATP boundary supersedes it post-cutover (§13/§21) | 149O.15 + implementation phase | `agent.py:execute_rollback` | Direct-call-bypass-proof placement independently confirmed |
| AG5 gate | none (structural only, §2) | Mandatory HATP boundary added post-cutover (§14/§21) | 149O.15 + implementation phase | `agent.py:build_rollback_execution` | Same as above |
| Legacy cutover | none exists | 3-state machine, protected-admin-triggered, one-way (§19) | 149O.15 (state model) + Class-B activation extension | Class-B deployment/activation subsystem (149O.6/149O.7 lineage) | Independent verification of irreversibility + no-agent-writable-storage |
| Cutover state | n/a | Stored in Class-B protected deployment/trust-root model (§19) | 149O.15 | new module, ownership TBD at contract freeze | Storage-authority (not `.pcae/`) independently confirmed |
| Legacy approve | Mutates `rollback_approval_state` unconditionally | Pre-cutover unchanged; post-cutover deterministic non-mutating deprecation error (§16) | 149O.15 | `commands/agent.py:run_remote_rollback_approve`, `agent.py:approve_rollback` | Post-cutover non-mutation independently confirmed |
| Direct callers | Unmediated (`execute_rollback`/`build_rollback_execution` callable directly) | Covered by the same in-function gate as CLI (§15) | 149O.15 | `agent.py` | Direct-function-call test independently confirms gate applies |
| Failure modes | Ad hoc / fail-closed umbrella only | Layered diagnostics (§25), all fail-closed, no fallback post-cutover (§22) | 149O.15 | multiple, per layer | Attack matrix (§30) independently reproduced |

### 29.2 Future production files (anticipated, not created by this phase)

- `src/pcae/core/hatp_ag_authority.py` — extended to call
  `HATPEvidenceStore.load` internally (§11) and to enforce cutover-state
  mandatoriness (§21).
- `src/pcae/core/agent.py` — `execute_rollback`/`build_rollback_execution`
  extended to make `hatp_evidence_id` conditionally required based on
  cutover state, at the exact pre-`_run_git_revert`/pre-file-write
  location (§13/§14/§15).
- `src/pcae/commands/agent.py`, `src/pcae/cli.py` — `--hatp-evidence-id`
  flag registration on `remote rollback execute` and `rollback` (§10).
- A new cutover-state module/record location under Class-B protected
  storage (§19) — exact file/module TBD at 149O.15.
- `src/pcae/commands/agent.py:run_remote_rollback_approve` /
  `src/pcae/core/agent.py:approve_rollback` — post-cutover deprecation-error
  branch (§16).

None of these were touched by 149O.14.

## 30. Future mandatory attack matrix (≥45 scenarios, per §133)

All rows below describe **target post-cutover behavior** the 149O.15
contract must freeze and a future implementation+verification phase pair
must independently reproduce. None are exercised against production code
by this architecture-only phase.

| # | Attack | Required outcome |
|---|---|---|
| 1 | Missing evidence ID | Fail closed — `EvidenceNotFoundError` surfaces as evidence-load-error layer |
| 2 | Malformed evidence envelope | Fail closed — `MalformedEvidenceEnvelopeError` |
| 3 | Digest mismatch | Fail closed — `EvidenceIdDigestMismatchError` |
| 4 | Wrong operation (evidence signed for a different job/PER) | Fail closed via operation binding (§23) |
| 5 | AG3 evidence used for AG5 dispatch | Fail closed via operation-family binding (§23) |
| 6 | AG5 evidence used for AG3 dispatch | Fail closed via operation-family binding (§23) |
| 7 | Wrong repository | Fail closed via repository-identity binding (§23) |
| 8 | Wrong deployment | Fail closed via canonical-deployment-root binding (§23) |
| 9 | Expired proof | Fail closed — `HATPVerificationStatus.EXPIRED` |
| 10 | Revoked signer | Fail closed — `HATPVerificationStatus.REVOKED_SIGNER` |
| 11 | Revoked authority/substrate readiness lost | Fail closed via readiness re-check (§9) |
| 12 | Decision changed after signing | Fail closed via digest cross-check (§24) |
| 13 | Binding changed after signing | Fail closed via digest cross-check (§24) |
| 14 | Fresh unregistered key | Fail closed — not in trust store, `MISSING`/`UNKNOWN_SIGNER`-class status |
| 15 | Forged signer | Fail closed — `INVALID_SIGNATURE`/`INVALID_ATTESTATION` |
| 16 | Caller-supplied `approval_present=True` | Structurally impossible — no such parameter exists anywhere on the mandatory path (§10 forbids the flag; internal functions have no such override) |
| 17 | Caller-supplied HATP `VALID` spoof | Structurally impossible — verification always re-runs internally (§12); no caller-supplied status parameter exists |
| 18 | Test-provider injection | Structurally impossible — F-2 closure preserved, no provider parameter exists on the production path (§6, unchanged) |
| 19 | Arbitrary trust-store injection | Structurally impossible — same F-2 closure (§6, unchanged) |
| 20 | Legacy-approved + missing HATP evidence, post-cutover | Fail closed — legacy state not consulted post-cutover (§21) |
| 21 | Legacy-approved + invalid HATP evidence, post-cutover | Fail closed — same (§21) |
| 22 | Delete cutover record | Must fail closed / require re-establishing protected state, never silently revert to `LEGACY_COMPATIBLE` for ordinary principals (§19 irreversibility) — exact mechanics for detecting deletion vs. genuine pre-cutover state deferred to 149O.15 |
| 23 | Attempt CLI-flag downgrade to legacy (e.g. omit `--hatp-evidence-id` post-cutover) | Rejected — flag becomes required once `HATP_MANDATORY` applies (§19/§21) |
| 24 | Alternate production effect caller bypass (direct function call skipping CLI) | Fail closed — gate lives inside `execute_rollback`/`build_rollback_execution` themselves (§15) |
| 25 | Cached previous `VALID` reused | Structurally impossible — no cache exists (§12) |
| 26 | Cached previous PB `ALLOW` reused | Structurally impossible — PB always re-evaluated (§25) |
| 27 | Evidence deleted after a prior successful attempt, retry | Fail closed on retry — every attempt reloads (§12/§22) |
| 28 | Evidence modified after a prior successful attempt, retry | Fail closed — digest mismatch on reload (§12/§22) |
| 29 | Two valid evidence IDs exist, no ID supplied | Rejected — explicit selection required, no implicit choice (§11) |
| 30 | Old raw `hatp_proof` parameter bypass attempt | Rejected — non-authoritative on mandatory path (§11) |
| 31 | Old `hatp_evidence` parameter bypass attempt | Rejected — non-authoritative on mandatory path (§11) |
| 32 | PB returns `HUMAN_REVIEW` despite valid HATP | Rollback does not dispatch — PB decision governs, not HATP validity alone (§25) |
| 33 | PB returns `DENY` despite valid HATP | Rollback does not dispatch (§25) |
| 34 | PB `ALLOW` under current `execution_unavailable` capability | Remains non-execution — `ALLOW` ≠ executed (§26) |
| 35 | Evidence created under `LEGACY_COMPATIBLE`, consumed post-cutover | Allowed if it still verifies fresh (§27, no cutover-time binding) |
| 36 | Signing and consumption in the same process/invocation, attempted shortcut | No special-cased shortcut exists — same fresh-verification path applies regardless (§27) |
| 37 | Repository moved/cloned/re-worktreed, evidence reused | Fail closed via existing repository/deployment identity binding unless identity genuinely matches (§23/§27) |
| 38 | Concurrent multi-process dispatch attempts with same evidence ID | Each independently reverifies fresh — no process-local cache to race on (§27) |
| 39 | Env-var override attempt (`--legacy`/`--skip-hatp`/similar) | Structurally forbidden — no such flag/env var exists anywhere in the target design (§19) |
| 40 | Repo-writable marker file claiming `HATP_MANDATORY` | Rejected — cutover state lives in Class-B protected storage, not `.pcae/` (§19) |
| 41 | Agent attempts to self-activate cutover | Structurally impossible — activation requires protected Class-B admin authority the agent principal does not hold (§19) |
| 42 | Unsupported evidence-envelope version | Fail closed — `UnsupportedEvidenceVersionError` |
| 43 | Invalid provider-assertion structure | Fail closed — existing envelope-schema validation (§5/§22) |
| 44 | Divergence-blocking AG5 file state combined with valid HATP evidence | AG5's existing structural divergence check still blocks — HATP validity never overrides structural/safety preconditions (§18) |
| 45 | `rollback_approval_state == "denied"` combined with valid HATP evidence, post-cutover | Legacy field not consulted at all post-cutover (§21) — dispatch proceeds only through the mandatory HATP+PB chain; denial as a legacy field carries no post-cutover meaning, consistent with §17 (a future contract-freeze phase should consider whether a *separate*, still-authoritative "explicit deny" concept is warranted, but 149O.14 does not invent one — out of scope) |

## 31. MC-1..MC-13 security invariants

- **MC-1** — Evidence ID is a locator only; it never itself constitutes
  approval, verification, or permission.
- **MC-2** — Every mandatory consumption attempt re-verifies current HATP
  state fresh; no attempt trusts a prior attempt's result.
- **MC-3** — No cached verification result, no cached `approval_present`,
  no cached PB decision is ever stored or reused.
- **MC-4** — Post-cutover, missing or invalid evidence cannot fall back to
  legacy approval under any circumstance.
- **MC-5** — Post-cutover, a caller-supplied approval boolean is
  structurally absent and therefore non-authoritative.
- **MC-6** — Only protected Class-B cutover state (never an agent-writable
  file) determines whether mandatory mode applies to a deployment.
- **MC-7** — Cutover is one-way for any ordinary agent/runtime principal;
  reversion requires a separately governed administrative mechanism.
- **MC-8** — AG3 and AG5 each bind to the exact operation they were signed
  for; no generic "any rollback" evidence exists.
- **MC-9** — Cross-family evidence (AG3-for-AG5 or AG5-for-AG3) cannot
  authorize, by construction of the existing operation-binding check.
- **MC-10** — Derived approval always passes through Permission Broker;
  it is never wired directly to dispatch.
- **MC-11** — Every effectful production caller (CLI and direct function
  call alike) is covered by the identical mandatory boundary, placed at
  the effect boundary itself, not at any single entry point.
- **MC-12** — Permission Broker `ALLOW` remains distinct from actual
  execution capability; `COMP-002` is a separate, later track.
- **MC-13** — Evidence creation itself (signing) never changes authority —
  signing only ever produces a consumable artifact; it never mutates
  `rollback_approval_state`, PER status, or any approval field (unchanged
  from 149O.13's independently verified finding).

## 32. Threat model under mandatory consumption

An ordinary agent principal, under the target `HATP_MANDATORY` architecture,
**can**: read evidence artifacts it has access to; supply any `evidence_id`
it knows of via `--hatp-evidence-id`; attempt dispatch as many times as it
wants (each attempt independently fails or succeeds on fresh
verification); observe PB decisions and diagnostic layers.

An ordinary agent principal **cannot**: cause a `LEGACY_COMPATIBLE` or
`PREPARED` deployment to become `HATP_MANDATORY` (protected admin-only,
§19); cause a `HATP_MANDATORY` deployment to revert (irreversible for this
principal, §19); supply a raw proof/evidence object that bypasses the
envelope/store (§11); supply an `approval_present` boolean directly (no
such parameter exists, §10); select a provider or trust store (F-2
closure, unchanged, §6); cause PB to be skipped (§25); reuse a cached
verification or decision result (§12); use evidence signed for a different
operation, repository, or deployment (§23); sign evidence itself acting
under the agent/runtime principal in a way that also grants it consumption
authority beyond what the envelope itself independently proves (principal
separation, §27) — signing still requires the same hardware/credential
ceremony as today (`pcae hatp sign rollback`, unaffected by this phase).

## 33. B-149O-1..4 → target consumption path mapping

B-149O-1..4 were independently verified (149O.5 lineage, reconfirmed
149O.13) at the **HATP-gated authority boundary** — i.e., that
`hatp_ag_authority`'s gated-authority functions correctly derive
`approval_present` from RAE+HATP when invoked. This architecture's target
consumption path (§9/§13/§14) is precisely what makes that already-verified
boundary the *exclusive, mandatory* human-approval source for real AG3/AG5
dispatch, by relocating the (currently dead, §1/§2) call into the
effect-boundary itself and making it conditionally required per cutover
state (§19/§21). B-149O-1..4 remain **not closed** by this phase (§169) —
they close only once (a) mandatory consumption is implemented and
independently verified against the attack matrix (§30), and (b) a
deployment has genuinely reached `HATP_MANDATORY` — neither has happened
yet.

## 34. 149O.13 non-blocking findings — disposition

| 149O.13 finding | Disposition under this architecture |
|---|---|
| Pre-existing 149O.6 Wave-7 hook clarification (`hatp_evidence_id`/`hatp_proof`/`hatp_evidence` inert on real dispatch) | **Directly resolved by this architecture's design** — §9/§13/§14 relocate the hook to the effect boundary and make it the mandatory gate post-cutover; §11 disposes of the raw-parameter forms individually. Not yet implemented. |
| Precondition resolution-order finding (RAE Binding resolved before repository identity, both map to same exit code) | **Out of scope for this phase** — belongs to `hatp_signing_ceremony.py` (signing-time), not to the consumption architecture. Carried forward unresolved; recommend 149O.15 note it as a candidate for a future signing-ceremony refinement, not a consumption-architecture concern. |
| TOCTOU error-type discriminator (Binding-revocation TOCTOU surfaces `BindingUnavailableError` rather than `EvidenceSerializationFailureError`) | **Out of scope for this phase** — signing-time TOCTOU, not consumption. Carried forward unresolved; no disposition change. |
| 3 stale boundary tests (`149O.9/10/10.1/10.2`'s own "no HATP CLI exists yet" snapshot assertions, now false) | **Out of scope for this phase's allowed-file set** (fixing them touches pre-existing test files unrelated to 149O.14's own new deliverables) — carried forward unresolved, recommend a follow-up widening phase as 149O.13 already recommended. Not a blocker for 149O.15. |

## 35. Python 3.9 repair placement (§167)

**Selected: Option A.** `149O.12B-Obs-PY39-1` (missing Z-suffix
normalization in `pcae.governance.publication.coordinator._parse_timestamp`,
blocking creation of new CHGR Decisions/RAE Bindings on Python 3.9/3.10)
does **not** block 149O.15 contract freeze. No evidence found in this
phase's source inspection that 149O.15 itself needs to create fresh CHGR
Decisions/RAE Bindings on Python 3.9/3.10 — 149O.15 is a documentation/
contract-freeze phase, not an implementation phase that mints new
governance artifacts. The repair should be scheduled as a narrow follow-up
**before mandatory-consumption implementation begins** (i.e., before the
first implementation phase that follows 149O.15), since that
implementation phase will need to create/consume fresh Decisions/Bindings
in its own verification work, potentially on those interpreters.

## 36. Retained findings, verdict, and next phase

- HATP production: remains **NOT READY**.
- B-149O-1..4: remain **INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED**.
- Runtime: remains **Observed / observe / unavailable**.

**ARCHITECTURE VERDICT: HATP AG3/AG5 MANDATORY PRODUCTION CONSUMPTION
ARCHITECTURE: SELECTED.** Key properties: explicit evidence ID (§10);
canonical envelope load (§11); fresh HATP verification every attempt (§12);
canonical gated RAE/HATP approval derivation reused unchanged (§9/§15); PB
remains permission-decision owner (§25); protected one-way cutover (§19);
legacy pre-cutover compatibility only (§20); no legacy fallback post-cutover
(§21/§22); effect-boundary coverage, not CLI-only (§15); PB execution
enforcement remains a separate, deferred COMP-002 track (§26).

**Recommended next phase: 149O.15 — HATP Mandatory Production Consumption
Contract Freeze.** Must freeze: evidence-reference syntax (§10); consumption
API shape (§9/§11); cutover state model and storage schema (§19); protected
activation authority mechanics (§19); legacy-fallback prohibition (§21/§22);
AG3/AG5 mandatory wiring points (§13/§14/§15); old-hook disposition (§11,
§18); failure semantics (§22/§25); PB handoff (§25); direct-call-bypass
prevention (§15); the full attack matrix (§30). Implementation must not
begin before contract freeze and independent verification of that freeze.
