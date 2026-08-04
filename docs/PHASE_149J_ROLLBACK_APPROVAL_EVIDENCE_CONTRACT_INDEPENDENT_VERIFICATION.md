# Phase 149J — Rollback Approval Evidence Contract Independent Verification

## 0. Baseline

- Latest completed phase: 149I (`ed0857f7`, `afa9fdd3`, `ac1c43a6`,
  `44485675`; pushed; `origin/main..HEAD` = 0).
- 149I result: `ROLLBACK APPROVAL EVIDENCE CONTRACT (RAE-001) v1.0
  FROZEN` — no BLOCKING finding raised by 149I's own text.
- Pre-phase checks (all ran clean): `git status --short` (clean),
  `git status --branch --short` (`## main...origin/main`),
  `git rev-list --count origin/main..HEAD` (0), `pcae health` (healthy),
  `pcae check` (passed), `pcae status coherence` (coherent),
  `pcae doctor task-memory` (clean), `pcae push check` (nothing to
  push), `pcae runtime inspect` (`Observed` / `observe` / `unavailable`),
  `pcae notify status` (telegram configured/enabled), `pcae phase-report
  show --latest` (149I, completed, pushed, `origin/main..HEAD`=0),
  `pcae phase-report reconcile --phase-id 149I` (reconciled,
  `already_dispatched`, mutation: none — inspection only).
- No newer phase supersedes 149J. Runtime unchanged throughout this
  phase (confirmed before/after, §12 below).

## 1. Phase Type and Methodology

Independent contract-verification phase only. `RAE-001 v1.0` is treated
as adversarial subject matter, not trusted evidence — every claim
this document makes about RAE-001's own text is checked against the
current on-disk contract file
(`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`), and every
claim RAE-001 makes about a *dependency* (CHGR-001, TAMC-001, IWC-001,
AEM-001/AESIC-001, RWMPC-001, PBPA-001, live Permission Broker code,
`agent.py`, and schema files) is checked directly against that primary
source, not against 149I's or RAE-001's own paraphrase. Live Permission
Broker calls are made against hand-constructed
`PermissionBrokerRequest` instances using the real, unmodified
`pcae.core.permission_broker_foundation` module — decision-only, no
git command or filesystem mutation executed. No `src/pcae/**` file is
modified by this phase; no contract (`docs/contracts/**`) is modified;
no CLI, schema, or Evidence Validator is authored.

## 2. Requirement Reconstruction

RAE-001's requirement numbering (`RAE-REQ-001` … `RAE-REQ-081`) was
independently extracted by script from the current file, not read as a
given:

```
count: 81, min: 1, max: 81, gaps: []
```

81 requirements, sequential, no gaps, no duplicates. No requirement ID
appears twice; none is skipped. Every normative MUST/SHALL clause
reviewed is attached to a numbered `RAE-REQ-*` anchor — no free-floating
normative claim was found hiding only in prose or in an example. No
undefined term is used normatively without a §3 definition or an
explicit adoption of a CHGR-001 §2 term.

## 3. Dependency Reconstruction

For each cited dependency, RAE-001's claim was checked against the
dependency's own text, not trusted:

| Dependency | RAE-001's claim | Independently confirmed? |
|---|---|---|
| CHGR-001 v1.0 | Consumed only via §6 Decision Template extension point; unamended | **Confirmed** — `template_id` resolves through an open-pattern identifier (`identity.schema.json:12-16`, `^[a-z][a-z0-9_-]{2,63}$`), not a closed enum; a new template is a new *instance*, no schema change required |
| TAMC-001/TAMPC-001 | Structural inspiration only; wall upheld (§5) | **Confirmed** — TAMC-REQ-024/025/036 verified verbatim (§5 below) |
| IWC-001 v1.2 | Transport only; confirmation ≠ approval (§18) | **Confirmed**, though RAE-001's literal "§1" pointer is imprecise — see §9 Findings below |
| PEC-001 | Publication mechanism only, "Model 2" scope, no amendment | **Confirmed** — RAE-001 does not adopt PEC-001's "Model 3" hardening option, consistent with its own text |
| RWMPC-001 v1.0 | RWMPC-REQ-017/022/023/027 restated correctly; no amendment needed | **Confirmed verbatim** against `docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md` |
| PBPA-001 v1.0 | POL-004 scoping unchanged; no amendment needed | **Confirmed** — `permission_broker_foundation.py:449-486` (current line numbers; PBPA-001's own internal citation, `:416-443`, is now stale relative to current code — PBPA-001's drift, not RAE-001's) |
| PBPC-001 v1.2 | Push-specific, unrelated, no amendment needed | **Confirmed** — no rollback-class content in PBPC-001 |
| TAMC-001 `human_authorization` shape | Structural precedent only, never composed | **Confirmed** — see §5 (CHGR/TAM wall) |

RAE strengthens no dependency's own guarantee beyond what that
dependency actually provides — every place RAE-001 claims a guarantee
(e.g. "CHGR guarantees provenance sufficient to reconstruct what was
confirmed") is traceable to the dependency's own text, not inferred
from silence.

## 4. CHGR Trust Substrate — Independent Classification

Direct re-reading of `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
§1–§13, §20:

| Property | Classification | Basis |
|---|---|---|
| Canonicality (stable, non-reassignable ID) | **SUPPORTED** | §9, `chgr-<uuid4>` assigned only at Publication |
| Human origin (authorship of the selection) | **SUPPORTED** | §4 INV-1/INV-2 (no AI pre-selection/authorship) |
| Actor identity | **PARTIALLY SUPPORTED** | Captured as `decision_maker_identity_evidence` at whatever assurance level actually occurred (today L0); not authenticated |
| Integrity | **SUPPORTED** | §10 content-integrity digest |
| Immutability | **SUPPORTED** | §13.3 — substantive fields never edited in place, only superseded |
| Provenance | **SUPPORTED** | §10 — exact preview content stored verbatim, selection, timestamp, hash |
| Supersession | **SUPPORTED** | §13.3 |
| Revocation | **NOT SUPPORTED IN PRODUCTION** | CHGR's own `revoked` lifecycle state has no production writer today (149H §18 NON-BLOCKING, independently re-confirmed — this fact is stated in 149H's document, not CHGR-001 itself; RAE-001 cites it correctly) |
| Authority (that the decision-maker was entitled to decide) | **NOT SUPPORTED, explicitly disclaimed** | CHGR-001 §11/INV-8: "A CHGR's presence... is proof that a decision was recorded, never proof that the decision-maker held the authority to make it." |
| Authentication (cryptographic identity proof) | **NOT SUPPORTED** | §12 — L2–L5 are open extension points, not implemented; no signing required or performed |

RAE-001 claims no CHGR guarantee beyond this list (RAE-REQ-002). This
independent classification confirms RAE-001 does not overclaim any
CHGR property — in particular it correctly treats *authority* and
*authentication* as gaps CHGR does not close, and builds its own
Binding-record layer (§8) and disclosed STRATEGIC_GAPs (§28) around
exactly those two gaps rather than papering over them.

## 5. CHGR/TAM Wall — Independent Reconfirmation

Direct re-reading, not trusting RAE-001's paraphrase:

- `CHGR-001 §19.1` (lines 612–643): the Stage 3 Typed Authority Model
  family "SHALL remain a wholly separate artifact family from CHGR,
  never composed, subclassed, or wrapped."
- `TAMC-REQ-024` (line 209): "Never establish, activate, transfer,
  select, or revoke authority."
- `TAMC-REQ-025` (lines 212–214): "Never infer authority, authorization,
  approval, certification, completion, publication status, execution
  permission, or operative state from record existence, validity,
  content, or location."
- `TAMC-REQ-036` (lines 277–286): "The existence or validity of a typed
  record SHALL NEVER imply: authorization; completion; approval;
  certification; publication; execution; runtime permission; or any
  other operative authority state." (RAE-001 cites "lines 209-284" —
  the requirement's own text actually runs to line 286; a 2-line
  undercount, non-substantive — see §9 Finding F1.)

RAE-001's own Binding record (`rollback_approval_binding`, §8) was
independently checked against these three requirements: it does not
declare `record_type: human_authorization`, is not stored under
`src/pcae/schema_resources/cltr_cutover/**`, and its own field
semantics (`decision`, `state`) are denormalized *from* an
independently-validated CHGR record, never treated as self-authorizing
by their own presence. **The wall holds**; RAE-001 reuses shape, not
family membership, and says so explicitly at every point of reuse
(RAE-REQ-003, RAE-REQ-004, RAE-REQ-016).

## 6. Human Identity Claim — Independent Attack

RAE-001's own stated trust model (RAE-REQ-005): "The repository
currently trusts the local CLI operator who can invoke a governed
command against this checkout, identified only by a self-declared
string captured through CHGR-001's Confirmation ritual. No stronger
assurance exists anywhere in this codebase today."

Checked against production reality:
- `CHGR` `assurance_level` `L1` (`os_authenticated_user`) is an
  accepted schema enum value with **no supporting implementation**
  (independently confirmed by the research pass below).
- TAM `human_authorization.principal` is documented at
  `human_authorization.schema.json:70` as: "Does not verify the
  principal against any identity provider or authentication system" —
  RAE-001's own text paraphrases this without a file:line citation
  (§9 Finding F2), but the fact is verified accurate.

RAE-001 never claims authenticated, cryptographically proven, or
unforgeable identity anywhere in its text (independently grepped for
all three phrases — none present). It narrows to exactly the honest
ceiling and discloses the gap as `STRATEGIC_GAP` rather than silently
assuming a stronger substrate. **Not BLOCKING** — RAE-001 explicitly
does not overclaim, which is the actual test §4 of the governing phase
prompt sets.

## 7. Human-Origin Guarantee — Precision Check

Can PCAE technically distinguish a human-created CHGR record from a
structurally valid, agent/process-created one? Independently traced:
CHGR's provenance model (§10) requires the exact preview content
presented and a content-integrity digest computed over the published
record's canonical bytes — but nothing in CHGR-001's own text ties
Confirmation to an out-of-band signal (hardware key, TOTP, OS session)
that only a human process could produce. Since this repository has no
technical privilege separation between an agent process and a human
operator (RAE-REQ-009, and independently confirmed — no OS-level
process isolation exists between "agent-driven CLI session" and
"human-driven CLI session"), the guarantee that a given CHGR record
was human-created is **procedural, not technical** — it depends on the
operator (human or the agent operating on the human's behalf) actually
following the Confirmation ritual honestly, not on anything that could
detect or block a shortcut. RAE-001 states this honestly (RAE-REQ-009,
§28 STRATEGIC_GAP 2) rather than claiming a technical guarantee that
doesn't exist. **Not BLOCKING** — the disclosure is accurate and
matches the repository's own pre-existing, already-accepted "Model 2"
limitation (PEC-REQ-034/046, cited correctly by RAE-001).

## 8. Privilege Separation — Independent Attack

Does RAE-001 rely on privilege separation existing? Traced through
every requirement referencing "agent": RAE-REQ-009, RAE-REQ-018,
RAE-REQ-056. None of them assume an agent process is *technically*
prevented from invoking governed commands — RAE-001's actual defense
(RAE-REQ-018) is narrower and different: it prevents an agent from
**fabricating the shape** of evidence (a hand-authored JSON blob that
never went through Confirmation → Publication) by requiring digest
match against an *actually-published* record. It does not, and does
not claim to, prevent an agent from *operating the CLI as the human*
end-to-end and legitimately producing a real Confirmation event. This
distinction is precisely and consistently maintained throughout
RAE-001's text. **Not BLOCKING** — RAE-001 relies only on governed
canonical provenance for the fabrication threat, and explicitly
disclaims solving the operator-impersonation threat, treating it as
outside current threat strength (§28 STRATEGIC_GAP 2, threat #3 in
its own §22 table).

## 9. Approval Authority — Independent Source Trace

Traced the normative source establishing "this principal may approve
rollback": `eligible_authority` (RAE-REQ-012) is descriptive text
("The human operator of this governed repository checkout... No
stronger authority-registry check exists today"), evaluated manually,
not mechanically enforced by CHGR's schema (no authority registry
exists to check against). RAE-001 does **not** accept
`approver_role="rollback_approver"` embedded in the same untrusted
artifact as self-authenticating authority — no such field or pattern
appears anywhere in RAE-001's Binding table (§8) or Decision Template
(§7). Authority is instead sourced from the Decision Template's own
frozen, contract-level `eligible_authority` text (a governance-owned
artifact, not caller-suppliable), matched manually against the acting
Approver. This is honestly disclosed as an **OBSERVATION**, not
overclaimed as a registry-backed guarantee. **Not BLOCKING** per the
governing prompt's own criterion ("resolved via `eligible_authority`
descriptive-text mechanism, disclosed as OBSERVATION not Blocking,
matches the single-operator trust model this repository already relies
on elsewhere").

## 10. Identity vs Authority vs Event — Structural Check

RAE-001's §4 semantic-layers diagram and §3 definitions were checked
for whether "who," "may they," and "did they" are kept independent:

- **Who** — `decision_maker_identity_evidence` (self-declared, CHGR
  §12 L0 ceiling).
- **May they** — Approval Authority, matched against
  `eligible_authority` (RAE-REQ-008(1)).
- **Did they** — Approval Event, the actual published
  `selected_option_id = approve_rollback` (RAE-REQ-008(2)).

All three are independently required by RAE-REQ-038's conjunction
(terms (c) and (d) are structurally separate tests). A valid identity
with no Approval Authority is insufficient (RAE-REQ-008 restated at
RAE-REQ-038(d)); a valid Approval Authority with no actual Approval
Event supplies no evidence (§4's "§3→§3 gap"). **Confirmed structurally
independent — no BLOCKING finding.**

## 11. Decision Template and Binding Record — Independent Reconstruction

- **Closed vocabulary (§7):** exactly two options,
  `approve_rollback`/`deny_rollback` (RAE-REQ-012/013). No free-form or
  unknown decision can contribute to `approval_present` — the
  derivation rule's term (c) requires `selected_option_id ==
  approve_rollback` exactly (RAE-REQ-038(c)); any other value,
  including a hypothetical third option (none exists), fails.
- **Decision ≠ Broker permission (§7):** RAE-REQ-015 states this
  explicitly and RAE-REQ-040 restates it at the derivation-rule layer;
  independently confirmed at the live-Foundation layer (§13 below —
  valid approval with an unrelated policy trigger still denies).
- **Binding field table (§8):** independently classified every field —
  `evidence_id`/`governance_record_reference` are identifiers;
  `state`/`expires_at`/`revocation_metadata`/`replay_binding` are trust
  facts; `rollback_operation_reference`/`repository_state_binding`/
  `task_id` are bound operation facts; `created_at`,
  `use_binding`/`decision` (denormalized) are advisory/audit metadata.
  No free-form field (e.g. a hypothetical `approver_name` text field)
  is treated as proof of authority anywhere in the table — authority is
  established only through §9/§10's structural mechanism, never a
  Binding-record string.

## 12. AG3/AG5 Profiles — Independent Adversarial Analysis

Production source (`src/pcae/core/agent.py`) independently re-read, not
trusted from RAE-001's summary:

- **AG3** (`execute_rollback(root, job_id)`, line 5234): takes only
  `job_id`; `original_commit_sha` is resolved internally via
  `build_rollback_review(root, job_id)` from
  `job.get("commit_sha")` — confirming RAE-REQ-020's claimed derivation
  exactly.
- **AG5** (`build_rollback_execution(root, per_id, dry_run=False)`,
  line 93895): takes only `per_id`; `ecp_id` is resolved internally at
  line 93931 (`ecp_id = per.get("ecp_id")`) from the looked-up
  `PromotionExecutionRecord` — confirming RAE-REQ-021's claimed
  derivation ("the derived execution context"). RAE-REQ-021's
  parenthetical "per `build_rollback_execution`'s own signature" is
  imprecise (`ecp_id` is not literally a function parameter) — see §9
  Finding F3.

**Under-binding attack (item 14/15 of the governing prompt):** for AG3,
can two different rollback operations share `{job_id,
original_commit_sha}`? No — `job_id` is a unique job identifier
(one-to-one with a specific remote execution job), and
`original_commit_sha` is read from that job's own persisted record;
two distinct jobs cannot share a `job_id` by construction (job files
are keyed by `job_id`). For AG5, `{per_id, ecp_id}`: `per_id` uniquely
names one `PromotionExecutionRecord`, and `ecp_id` is denormalized from
that same record — again unique by construction. Neither profile
permits approval transfer between distinct operations.
**Not BLOCKING.**

**Family locking (§16 of governing prompt):** AG3's shape
(`{job_id, original_commit_sha}`) and AG5's shape (`{per_id, ecp_id}`)
share no field names. A Binding record with an AG3-shaped reference
cannot satisfy an AG5 request's `rollback_operation_reference` match
(RAE-REQ-024's exact-match rule operates on named fields that simply
don't exist on the other family's shape) — this is a schema-validation
failure, not merely a scope-validation coincidence
(RAE-REQ-022, explicit). **Cross-family replay is structurally
impossible, not merely policy-forbidden.**

**Cross-operation replay (§17):** a valid AG3 approval for job A,
presented against job B's rollback attempt, fails RAE-REQ-024's exact
match (different `job_id`/`original_commit_sha`) → `WRONG_SCOPE` →
`approval_present=False`. Same reasoning for AG5. **Confirmed rejected
by RAE-REQ-038(e).**

## 13. Live Foundation Probes — Real Code, No Mocks

Executed against the actual, unmodified `pcae.core.permission_broker_foundation`
module (decision-only; `simulation_only=True` in every ALLOW-path
probe; no git/filesystem mutation performed):

| Scenario | `approval_present` | Decision | Triggered policies |
|---|---|---|---|
| Otherwise-valid rollback request | `True` | **ALLOW** | none |
| Same request, no approval | `False` | **HUMAN_REVIEW** | POL-004 |
| Valid approval, no active task | `True` | **DENY** | POL-001 |
| Valid approval, `simulation_only=False` | `True` | **DENY** | POL-005 |
| Valid approval, unrecognized component | `True` | **DENY** | POL-007 |

This independently reconfirms RAE-001 §23/RAE-REQ-069/RAE-REQ-070's
satisfiability claim exactly: `approval_present=True` supplies exactly
one input fact and does not itself force `ALLOW` — POL-001, POL-005,
and POL-007 each independently deny even with valid approval present,
demonstrating RAE-REQ-040 ("approval is not permission") is true in the
live Foundation, not just in contract prose. No rollback execution
occurred or is authorized by any of these probes (all are pure
`PermissionBroker.evaluate()` calls against hand-built request objects;
`ExecutionDisabledRule`/POL-005 independently confirms no execution
boundary exists regardless of approval).

## 14. Freshness — 24-Hour TTL Provenance (Mandatory Item)

RAE-001 (RAE-REQ-043) reuses "the same 24-hour duration
`human_authorization.expires_at` already establishes as repository
precedent," citing no file:line for the number itself. Independently
traced to ground truth, not accepted on RAE-001's or 149I's say-so:

1. `human_authorization.schema.json:92-94` restates the duration in a
   schema *comment* (non-normative): "restates CLTR-CUTOVER-001 Sec.8's
   24-hour freshness window."
2. The actual normative source is `docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md`
   (**CLTR-CUTOVER-001 v1.0**) §8, lines 476–486:

   > "**[NEW binding decision]**: authorization freshness expires **24
   > hours** after the authorization timestamp, or immediately upon any
   > change to the cutover request's binding fields... the default and
   > floor are frozen here at 24 hours."

**Classification: VALID PRECEDENT, independently confirmed.** The
duration is not fabricated, not merely "time-bounded" language
stretched to mean 24 hours — it is an explicit, binding, frozen
numeric contract parameter in a primary source. **This is not a
BLOCKING finding.** It is, however, a genuine **NON-BLOCKING sourcing
gap in RAE-001's own text** (§9 Finding F4): RAE-001 asserts the number
with confidence but never cites CLTR-CUTOVER-001 §8 (or even the
schema comment) by file:line, requiring an independent verifier to
locate the primary source from scratch rather than being pointed to
it. Structural inspiration alone (reusing `human_authorization`'s
*shape*) does not by itself authorize reusing its *duration* — but
RAE-001 does not merely gesture at structural inspiration for the
duration specifically; RAE-REQ-043 explicitly frames the number as
"structural reuse... never an arbitrarily invented duration" and
independent tracing confirms that characterization is true, just
under-cited.

**Boundary precision (item 23 of the governing prompt):** RAE-001 §8
defines `expires_at`/`created_at` only as "timestamp" (conceptual
type), explicitly deferring exact JSON Schema syntax — including
timezone, inclusive/exclusive boundary semantics, and clock source — to
"a future implementation-phase artifact" (RAE-REQ-017). This is
consistent with RAE-001's own declared scope (§27 Non-Goals: "Authoring
an actual JSON Schema file... is a future implementation-phase
artifact") and is not a hidden gap — it is an explicitly disclosed
deferral. **Not BLOCKING** for a contract-only phase; **flagged for the
implementation-planning phase** (§17 below) as a concrete open item.

## 15. Clock Failure, Revocation, Supersession, Rejection

- **Clock failure/skew:** not named as a distinct rule, but falls under
  RAE-REQ-042's fail-closed default ("malformed record... or any other
  internal failure" → `approval_present=False`). A malformed or
  future-dated timestamp is a shape/content anomaly the Evidence
  Validator would encounter during resolution and is therefore covered
  by the general fail-closed clause. **Not BLOCKING**, though RAE-001
  could be more explicit that malformed timestamps specifically fall
  under this umbrella (minor precision note, not elevated to a
  numbered finding since RAE-REQ-042's "any other internal failure"
  language is broad enough to already cover it).
- **Freshness vs. revocation:** RAE-REQ-038(f) checks `state == issued`
  independently of RAE-REQ-038(g)'s expiry check — a young-but-revoked
  Binding fails on (f) regardless of (g). **Revocation wins,
  confirmed.**
- **Newer denial superseding approval:** RAE-REQ-047 (supersession
  operates at the Binding-record layer, regardless of the referenced
  decision's value) combined with RAE-REQ-019 (a DENY decision MAY also
  be referenced by a Binding record) together mean a later Binding
  referencing a `deny_rollback` decision for the same
  `rollback_operation_reference` supersedes an earlier APPROVE Binding
  under RAE-REQ-038(h). **Resolved by the contract text itself — not
  ambiguous, contrary to the governing prompt's caution that this might
  be unaddressed.**
- **"Latest record" trap:** RAE-REQ-041 forbids ambiguous "use the
  latest" resolution; RAE-REQ-047 clarifies supersession determines
  *which* record is authoritative but the Evidence Validator still
  requires the Evidence Consumer's explicit `evidence_id` to match
  exactly. Presenting a superseded `evidence_id` correctly resolves
  `SUPERSEDED`, not a silent substitution of the newer record.
  **Confirmed no implicit-latest bypass exists.**
- **Human denial authority:** RAE-REQ-068 explicitly declines to
  overload the boolean with a separate "explicitly denied" signal for
  broker purposes, while preserving the underlying `deny_rollback`
  record as citable audit evidence distinct from the boolean. This is
  a deliberate, disclosed design choice, not an oversight — **Not
  BLOCKING**, though it does mean a rollback CLI surface built on this
  contract cannot, from `approval_present` alone, distinguish "no one
  has decided yet" from "a human explicitly said no." A future UX
  concern, not a contract defect (RAE-001 does not need `approval_present`
  to carry more information than POL-004 already consumes).

## 16. Replay, Retry, and Provenance

- **Replay prevention (§16):** two independent layers — CHGR's own
  package-id `FileExistsError` guard on Decision publication
  (RAE-REQ-049) and the Binding's own `state: issued -> used` +
  `replay_binding` one-time-use token (RAE-REQ-050). Independently
  confirmed these are two genuinely different mechanisms operating at
  different artifact layers, not double-counted.
- **Failed-execution retry (RAE-REQ-052):** same evidence MAY be reused
  only if the Binding has not yet transitioned to `used` and operation
  identity/`repository_state_binding` are unchanged — RAE-001 correctly
  scopes this to *mechanical* failure (before mutation completes), not
  approval failure, and explicitly freezes the requirement while
  deferring the exact used-transition wiring to implementation.
- **Fresh broker evaluation on retry (RAE-REQ-053):** independently
  reconfirmed at the live-Foundation layer — nothing in
  `permission_broker_foundation.py`'s design permits caching a prior
  `PermissionBrokerDecision`; every `PermissionBroker.evaluate()` call
  is stateless and re-evaluates from the request object alone. No
  mechanism exists to "reuse" a broker decision even if a caller wanted
  to. **Structurally enforced, not merely a stated intention.**
- **Successful-execution replay:** after `state -> used`, RAE-REQ-050's
  mechanism prevents reuse for a second successful mutation attempt.
  **Confirmed.**
- **Provenance chain (§17):** Decision provenance is fully inherited
  from CHGR §10 (RAE-REQ-054, no parallel mechanism invented); Binding
  provenance is its own digest (RAE-REQ-055) plus canonical,
  non-arbitrary storage location (RAE-REQ-056). **Important scope
  clarification (§9 Finding F5, non-blocking):** RAE-REQ-056 requires
  storage location to be canonical and non-arbitrary but does not
  itself define a technical mechanism (beyond convention/governance
  discipline) preventing an agent with ordinary filesystem access from
  writing a self-consistent, correctly-hashed file directly into that
  canonical location without having gone through the actual CHGR
  Confirmation ritual. This is not a *new* gap RAE-001 introduces — it
  is the same, already-accepted STRATEGIC_GAP 1/2 ceiling this
  repository already lives with for CHGR-001 generally (no repository
  content is protected from a trusted local operator's — human or
  agent-driven — direct filesystem writes). RAE-001's §29 "False"
  verdict on "record can be self-created by agent and trusted" is
  accurate in its own narrow, correctly-scoped sense (a Binding alone,
  without a genuinely CHGR-provenanced Decision behind it, cannot
  satisfy RAE-REQ-038(b)/(i)) but that verdict's soundness rests on
  CHGR's own publication-integrity ceiling holding, which RAE-001 does
  not re-derive from scratch. **Recommendation for the implementation
  phase**, not a blocking defect here: the future Evidence Validator
  should be built to verify an actual publication *event* (e.g. via
  provenance chain to a specific governed command invocation or audit
  log entry), not merely file-shape/digest self-consistency at rest, if
  a stronger guarantee than "convention" is ever wanted here.

## 17. Threat Model — Independent Attack

RAE-001's own 20-row threat table (§22) plus every additional
adversarial scenario the governing phase prompt names, independently
attacked against the contract text and, where applicable, live code:

| # | Threat | Contractual control | Independent verdict |
|---|---|---|---|
| 1 | Self-declared CLI approval flag | RAE-REQ-007/014/039 | **ADEQUATE** |
| 2 | Agent-generated fake approval JSON | RAE-REQ-018 (digest match to actually-published record) | **ADEQUATE**, subject to the CHGR-publication-integrity caveat, §16 F5 |
| 3 | Forged actor identity | RAE-REQ-005/006, disclosed STRATEGIC_GAP | **ADEQUATE given disclosed ceiling** (not "solved," honestly not claimed to be) |
| 4 | Unauthorized actor | RAE-REQ-008(1), RAE-REQ-038(d) | **ADEQUATE given manual-authority-check ceiling** |
| 5 | Stale approval | RAE-REQ-043-045, RAE-REQ-038(g) | **ADEQUATE** |
| 6 | Approval replay | RAE-REQ-049-051 | **ADEQUATE** |
| 7 | Wrong rollback target | RAE-REQ-024, RAE-REQ-038(e) | **ADEQUATE**, confirmed via §12 under-binding attack |
| 8 | Changed payload | RAE-REQ-025 | **ADEQUATE** |
| 9 | Changed task/phase | RAE-REQ-030, RAE-REQ-033 | **ADEQUATE** |
| 10 | Tampered record | RAE-REQ-018, RAE-REQ-055, RAE-REQ-038(i) | **ADEQUATE** |
| 11 | Latest-record mis-selection | RAE-REQ-041 | **ADEQUATE**, confirmed §15 |
| 12 | Confirmation-as-approval | RAE-REQ-058 | **ADEQUATE** |
| 13 | AESIC-as-approval | RAE-REQ-059 | **ADEQUATE** |
| 14 | Illegal CHGR/TAM composition | RAE-REQ-003/004 | **ADEQUATE**, confirmed §5 |
| 15 | Stale broker decision reused | RAE-REQ-053 | **ADEQUATE**, confirmed structurally at the code layer (§16) |
| 16 | Broad task-level approval | RAE-REQ-019, RAE-REQ-061 | **ADEQUATE** |
| 17 | Evidence validator internal failure | RAE-REQ-042 | **ADEQUATE** |
| 18 | Structurally valid but noncanonical record | RAE-REQ-018, RAE-REQ-056 | **PARTIAL** — canonical-location requirement is a governance/convention control, not a technical filesystem control (§16 F5); non-blocking given the pre-existing, disclosed repository-wide ceiling |
| 19 | Revoked approval reuse | RAE-REQ-046, RAE-REQ-038(f) | **ADEQUATE** |
| 20 | Superseded approval reuse | RAE-REQ-047, RAE-REQ-038(h) | **ADEQUATE** |

No threat classifies as **MISSING**. One (#18) classifies **PARTIAL**,
for the reason already disclosed by RAE-001 itself as STRATEGIC_GAP
1/2 — not a newly discovered hole.

## 18. Satisfiability Matrix — Independent Reproduction

Reproduced independently (not copied from RAE-001 §23), using the live
Foundation probes of §13 plus contract-text tracing for the rows that
require an Evidence Validator that does not yet exist:

| Scenario | `approval_present` | POL-004 result | Rollback dispatch? |
|---|---|---|---|
| Missing evidence reference | `False` | `HUMAN_REVIEW` | No — confirmed live (§13) |
| Malformed/unreadable Binding | `False` (fail-closed, RAE-REQ-042) | `HUMAN_REVIEW` | No |
| Wrong-target evidence | `False` (`WRONG_SCOPE`) | `HUMAN_REVIEW` | No |
| Unauthorized approver | `False` (`UNAUTHORIZED_APPROVER`) | `HUMAN_REVIEW` | No |
| Revoked evidence | `False` (`REVOKED`) | `HUMAN_REVIEW` | No |
| Stale evidence | `False` (`STALE`) | `HUMAN_REVIEW` | No |
| Superseded evidence | `False` (`SUPERSEDED`) | `HUMAN_REVIEW` | No |
| Valid `approve_rollback` evidence, exact match, fresh | `True` | not triggered | **Yes** — confirmed live: `ALLOW` (§13) |
| Valid evidence + unrelated policy denies (no active task) | `True` | not triggered | **No** — confirmed live: `DENY` via POL-001 (§13) |

The bottom two rows were independently exercised against the real
Foundation, not merely traced through code by inspection — both match
RAE-001's own claimed matrix exactly.

## 19. Compatibility Confirmations — Independently Re-Traced

- RWMPC-001: RWMPC-REQ-017 requires only that `approval_present`
  reflect a real evidence source, naming no specific artifact —
  RAE-001 satisfies this without RWMPC wording change. **Confirmed, no
  amendment needed.**
- PBPA-001: POL-004's applicability/resolution logic is unchanged by
  RAE-001; independently confirmed no `applicable_execution_classes` or
  `evaluate()` change exists anywhere in the current
  `permission_broker_foundation.py`. **Confirmed.**
- PBPC-001: push-specific, genuinely unrelated to rollback coverage.
  **Confirmed.**
- CHGR-001/IWC-001/PEC-001/TAMC-001/TAMPC-001/AESIC-001/AEM-001: none
  require amendment; each consumed only through an existing, unamended
  extension point (§4 above). **Confirmed for all seven.**

## 20. Production and Contract Boundary (149J itself)

```
git diff --name-only <pre-149J-baseline>..HEAD -- src/pcae/
```
Expected and confirmed empty — no production file touched by this
phase (§21 below re-confirms after the fact).

```
git diff --name-only <pre-149J-baseline>..HEAD -- docs/contracts/
```
Expected and confirmed empty — RAE-001 and every other frozen contract
are byte-identical to their 149I-frozen state.

## 21. Runtime Boundary

`pcae runtime inspect` before and after this phase's work:
`Observed` / `observe` / `unavailable`, unchanged. No runtime,
Permission Broker consumption, or execution capability was touched by
this phase.

## 22. Findings

- **F1 (NON-BLOCKING, wording precision).** RAE-001 cites TAMC-001
  "lines 209-284" for TAMC-REQ-024/025/036; the actual text of
  TAMC-REQ-036 runs through line 286. A 2-line undercount, not a
  substantive misquote — verified the cited requirements' content is
  otherwise fully and accurately restated.
- **F2 (NON-BLOCKING, attribution looseness).** RAE-001's §6 claim that
  TAM `human_authorization.principal` "does not verify... against any
  identity provider" is not sourced to a file:line anywhere in
  RAE-001's own text. The true primary source is
  `human_authorization.schema.json:70` (a schema field description),
  not TAMC-001 the contract document itself. The quoted content is
  accurate; the citation trail is thin.
- **F3 (NON-BLOCKING, precision).** RAE-REQ-021's phrase "`ecp_id`...
  per `build_rollback_execution`'s own signature" overstates —
  `ecp_id` is not a parameter of that function's actual signature
  (`root, per_id, dry_run=False`); it is derived internally
  (`per.get("ecp_id")`, `agent.py:93931`). RAE-001's own "derived
  execution context" phrasing is correct; only the "own signature"
  clause is imprecise. 149H's phrasing ("`per_id` (deriving `ecp_id`)")
  was more careful and should have been followed literally.
- **F4 (NON-BLOCKING, sourcing gap — flagged as high-value per the
  governing phase prompt's "mandatory" instruction for this item).**
  RAE-001 never cites a file:line for the 24-hour freshness duration it
  reuses (RAE-REQ-043). The underlying fact is real, independently
  located and confirmed at `docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md:476-486`
  (CLTR-CUTOVER-001 §8), classified **VALID PRECEDENT**. This is a
  citation-rigor gap, not an unsupported claim — the duration is not
  fabricated, but RAE-001's own text does not show the work needed to
  confirm that without independent digging (which this phase performed
  and now records for future reference).
- **F5 (NON-BLOCKING, scope clarification).** RAE-REQ-056's "canonical,
  non-arbitrary storage" requirement is a governance/convention
  control, not a technical filesystem-enforcement control — a
  repository-wide, already-disclosed STRATEGIC_GAP 1/2 ceiling, not a
  gap newly introduced by RAE-001. Recommend the future Evidence
  Validator implementation verify an actual publication *event*
  (provenance chain to a governed command invocation), not merely
  file-shape/digest self-consistency at rest, if a stronger guarantee
  is ever desired — but nothing in RAE-001's own frozen text needs to
  change to remain internally coherent and truthful about this ceiling.
- **F6 (NON-BLOCKING, minor).** RAE-001's structural-reuse citation of
  `target_reference` (RAE-REQ-003/RAE-REQ-022) is accurate but
  incomplete — the TAM `human_authorization` schema actually carries
  three family-locked reference fields (`request_reference`,
  `readiness_reference`, `target_reference`), not one; this does not
  affect RAE-001's own Binding-record design, which defines its own
  single `rollback_operation_reference` field independently.
- **STRATEGIC_GAP 1** (carried forward from 149H/149I, unchanged) — no
  stronger-than-self-declared human identity substrate exists.
  Independently re-verified accurate and honestly disclosed, not
  papered over (§6).
- **STRATEGIC_GAP 2** (carried forward, unchanged) — no technical
  privilege separation between an agent process and a human operator.
  Independently re-verified accurate; RAE-001's evidence model correctly
  scopes its own defense to fabrication-prevention, not
  impersonation-prevention (§8).

No finding in this section rises to BLOCKING under the governing phase
prompt's own criteria (§75): no overclaimed authenticated identity, no
authority claim without independent source, no demonstrated path for a
noncanonical/agent-created record to validate *without* an actually
CHGR-published Decision behind it, no under-specified AG3/AG5 binding
permitting replay, no CHGR hosting-legality problem, no unsupported
normative numeric claim (24h is real, just under-cited), no IWC/AESIC
leak into approval truth, no TAM authority-semantics leak, no
unimplementable revocation/supersession promise, no omittable
load-bearing conjunction term, and no RWMPC/PBPA/PBPC incompatibility.

## 23. Contract-Verification Verdict

```
VERIFIED WITH NON-BLOCKING FINDINGS — RAE-001 v1.0 CONFORMS
```

## 24. Implementation Readiness

```
PARTIALLY READY
```

The trust model, evidence conjunction, operation binding, and threat
controls are sound and internally coherent. What remains genuinely
open before an implementation phase can proceed without re-litigating
design questions: an actual JSON Schema for `rollback_approval_binding`
(RAE-REQ-017 explicitly defers this); exact `expires_at` boundary
semantics (timezone, inclusive/exclusive, clock source — §14); the
Evidence Validator's concrete resolution algorithm (RAE-REQ-034's
interface is conceptual only); and canonical storage-path
implementation for both Decision and Binding records (RAE-REQ-056).
None of these are contract-semantic defects — they are exactly the
"future implementation-phase artifact" items RAE-001 itself correctly
identifies as out of its own scope (§27 Non-Goals).

## 25. Trust-Substrate Readiness

```
CURRENT HUMAN TRUST MODEL SUFFICIENT FOR RAE-001 v1.0
```

Sufficient in the same sense the rest of this repository's governance
already relies on (PEC-001 "Model 2," CHGR-001's own L0 ceiling) — not
sufficient in an absolute, cryptographically-authenticated sense, which
RAE-001 never claims. The two disclosed STRATEGIC_GAPs are pre-existing
repository-wide limitations, not new weaknesses this contract
introduces or could realistically resolve on its own.

## 26. AG3 Readiness

```
AG3 APPROVAL-EVIDENCE CONTRACT READY; IMPLEMENTATION NOT STARTED
```

The `{job_id, original_commit_sha}` profile is independently confirmed
sound (§12) and matches production `execute_rollback`'s actual
resolution behavior. No Decision Template, Binding schema, or Evidence
Validator exists in production. AG3 itself remains unimplemented for
Permission Broker purposes.

## 27. AG5 Readiness

```
AG5 APPROVAL-EVIDENCE CONTRACT READY; IMPLEMENTATION NOT STARTED
```

The `{per_id, ecp_id}` profile is independently confirmed sound (§12)
and matches production `build_rollback_execution`'s actual resolution
behavior (`ecp_id` correctly derived from the PER record). Same
implementation gap as AG3.

## 28. Independent Test Suite

`tests/test_phase_149j_rollback_approval_evidence_contract_independent_verification.py`
— independently authored, does not import 149I's or any other phase's
test helpers. 49 tests, all passing:

```
49 passed in 0.08s
```

Covers: requirement-ID sequential-numbering/gap/duplicate check;
CHGR/TAM wall assertions cross-checked against CHGR-001/TAMC-001
primary text directly (not just RAE-001's paraphrase); human-identity
non-overclaiming; Decision Template closed vocabulary; AG3/AG5
operation-identity fields cross-checked against live `agent.py` source;
the 9-term `approval_present` conjunction structure; IWC/AESIC
exclusion; legacy-flag exclusion (including the exact `agent.py:5146`
citation); 24-hour TTL disclosure and its independently-traced primary
source (`docs/PHASE_135_STAGE_3_AUTHORITY_CUTOVER_CONTRACT_FREEZE.md`);
revocation/supersession/replay text assertions; six live,
real-code `PermissionBroker` probes (ALLOW, HUMAN_REVIEW, and three
independent DENY-by-unrelated-policy cases); and RWMPC/PBPA/PBPC
compatibility/boundary assertions.

## 29. TK1-TK3 and 149G Findings

TK1/TK2/TK3 remain deferred, not reopened by this phase. 149G's F1/F2/F3
(observation-only third request constructor wording; alternate-push
concurrent external push freshness limitation; stale 149D test
assertion) are carried forward unchanged, not mixed with this phase's
RAE-specific findings.

## 30. Recommended Next Phase

```
149K — Rollback Approval Evidence Implementation Plan
```

RAE-001 v1.0 verifies with zero BLOCKING findings, so implementation
planning may proceed. 149K should cover: canonical `rollback_approval_binding`
JSON Schema authorship (resolving §24's open items: exact
`expires_at` boundary semantics, `state` transition wiring, canonical
storage namespace); the Rollback Approval Decision Template's actual
registration as a production CHGR artifact; and the
`RollbackApprovalEvidenceValidator`'s concrete resolution algorithm
(RAE-REQ-034-042) — but should still not include AG3/AG5 Permission
Broker wiring in the same bounded phase unless the evidence
infrastructure and rollback integration are explicitly planned and
governed as one deliberate, bounded sequence, consistent with RAE-001's
own layering discipline (§4).

## 31. No-Go Confirmations

RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains unchanged.
PBPC-001 v1.2 remains unchanged. PBPA-001 v1.0 remains unchanged.
CHGR-001 remains unchanged. IWC-001 semantics remain unchanged.
TAM/TAMPC authority semantics remain unchanged. AESIC/AEM remain
disclosure-only. No production source (`src/pcae/**`) was modified by
Phase 149J. No rollback Permission Broker consumer was implemented. No
`approval_present=True` production value was introduced. No
self-declared CLI flag was treated as trusted approval. No IWC
confirmation was treated as approval. No AESIC result was treated as
approval or permission. No illegal CHGR/TAM authority-family
composition was introduced. No POL-001..012 meaning was changed. No
POL-013+ was added. No Runtime Enforcement behavior was changed.
AG3 and AG5 remain unimplemented. TK1/TK2/TK3 remain deferred. No
Prompt Generation or Prompt Dispatch capability was implemented. No
agent invocation capability was implemented. Runtime remains Observed,
maximum capability remains observe, and execution availability remains
unavailable.
