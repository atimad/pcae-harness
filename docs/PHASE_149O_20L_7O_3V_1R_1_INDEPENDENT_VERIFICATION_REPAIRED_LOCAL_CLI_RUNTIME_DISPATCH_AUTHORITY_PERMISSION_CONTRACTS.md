# Phase 149O.20L.7O.3V.1R.1 — Independent Verification of Repaired
# Local-CLI Runtime Dispatch Authority and Permission Contracts

## 1. Objective

Independently verify Phase 149O.20L.7O.3V.1R's claim that it closed both
BLOCKING findings identified by Phase 149O.20L.7O.3V.1 against the Phase
149O.20L.7O.3V local-CLI runtime dispatch authority/permission contract
freeze:

- **B-149O.20L.7O.3V.1-1** — RDGO-001 v1.0's gate 3/gate 4 relative order
  contradicted RPAC-REQ-042.
- **B-149O.20L.7O.3V.1-2** — PBRD-001 v1.0's twelve-fact `runtime_dispatch`
  request lacked mandatory `attempt_id`/`idempotency_key` binding.

This is verification-only. No approval storage, approval validation,
`runtime_dispatch` production wiring, POL-005 relaxation, Runtime
Enforcement activation, Shell Gate activation, external process, or real
execution occurs.

## 2. Independence

This verification does **not** rerun or import
`tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py` (3V.1R's own test
module). A fresh module,
`tests/test_phase_149o_20l_7o_3v_1r_1_contract_verification.py` (51 tests,
0 failed), was written from scratch, reconstructing repaired semantics
directly from RPAC-001, PBRD-001, RDGO-001, RIHAC-001, and RIASC-001
contract text, plus a read-only cross-check against existing `src/pcae`
mock/dry production source (`runtime_invocation.py`, `runtime_adapter.py`).
No 3V.1R prose is treated as authoritative; every claim below is checked
against primary contract text.

## 3. Baseline

```text
git status --short:                clean
git status --branch --short:       ## main...origin/main
origin/main..HEAD (pre-phase):     0
HEAD == origin/main (pre-phase):   9a645154fc35d41e6a1d7a95bc73245e89082ffe
v0.4.3 tag commit:                 63580893b1de4782a694ab802ff7bdebdf29b0e6
pcae health:                       healthy, git clean, agent lock available
pcae check:                        passed
pcae status coherence:             coherent
pcae push check:                   nothing_to_push, mode=nothing_to_push
pcae runtime inspect:               not_implemented / Observed / observe /
                                    unavailable, 0 plugins, 0 capabilities
pcae notify status:                Telegram configured/enabled/ready
```

`pcae doctor task-memory` reported only pre-existing, long-standing
`tasks/done/` vs `tasks/DONE.md` synchronization warnings unrelated to this
phase or to 3V.1R (same class of warning present at every recent phase
boundary; not attributable to this verification).

Runtime confirmed `Observed` / `observe` / `unavailable` throughout.
v0.4.3 (`63580893b1de4782a694ab802ff7bdebdf29b0e6`) unchanged.

## 4. Repair delta

3V.1R phase-entry SHA: `7806927f` (3V.1's own commit, the state 3V.1R
started from). Repair commits: `fa51c1bc` (contract repair itself),
`dca371c1` (pre-push wording sync), `39b97d1e`/`9a645154` (evidence
staging/close-out). Final repaired-contract SHA at this phase's start:
`9a645154fc35d41e6a1d7a95bc73245e89082ffe`.

`git diff --stat 7806927f..9a645154` shows exactly these changed files:

```text
.pcae/phase-completion-metadata.json
.pcae/phase-completion-report.md
CHANGELOG.md
PROJECT_STATUS.md
docs/PHASE_149O_20L_7O_3V_1R_..._RECONCILIATION_AND_REPAIR.md   (new)
docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md
docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md
docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md
docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md
tasks/DONE.md
tasks/TODO.md
tasks/active/... (task lifecycle files)
tests/test_phase_149o_20l_7o_3v_1r_contract_repair.py            (new)
```

**Independently confirmed: zero `src/pcae/**` paths appear in this diff.**
No production runtime behavior changed. Every changed file is contract
Markdown, governance metadata/task-lifecycle bookkeeping, or a fresh test
module. No executable behavior change occurred — this finding is
**NOT BLOCKING**.

## 5. RPAC requirements (re-read from primary text)

Re-read directly (not from 3V.1R prose): RPAC-REQ-025, 026, 028 (canonical
request/immutability), RPAC-REQ-042 through 048 (gate ordering, PB gap
acknowledgment, Runtime Enforcement), RPAC-REQ-064 through 072 (attempt
identity, idempotency, collision, persistent record, restart/replay,
retry). Full text confirmed at `docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md`.

**RPAC-REQ-042 exact text (primary source):**

```text
1. resolve authoritative repository/task/session and create PromptArtifact;
2. construct immutable request and explicit target selection;
3. obtain human InvocationApproval;
4. resolve descriptor/config and perform fact-only status/capability preflight;
5. obtain Permission Broker permission for adapter dispatch and each requested
   effect class;
6. revalidate mutable status/config/HEAD facts for freshness;
7. obtain the final Runtime Enforcement decision immediately before dispatch;
8. durably create the attempt record and atomically mark dispatch intent;
9. call the one selected adapter;
10. capture result and submit any proposed changes through generic intake.
```

Step 3 (human approval) strictly precedes step 4 (preflight). This is the
literal authority for the gate-order repair.

**RPAC-REQ-064:** opaque `invocation_id` before approval; each dispatch try
has a unique `attempt_id`.
**RPAC-REQ-065:** `idempotency_key` = SHA-256 over canonical content
excluding timestamps/attempt-specific facts.
**RPAC-REQ-066:** same ID + same content → resume; same ID + different
content → hard collision, fail closed.
**RPAC-REQ-072:** every retry needs a new `attempt_id`, fresh PB/RE
decisions, and fresh human authorization unless covered by the prior
approval's limit/expiry; changed prompt/target/repo/task/effects/budget
needs a new logical invocation and approval.

## 6. PBRD-001 versioning

Confirmed current normative version: **v1.1**, `Status: FROZEN`.
`v1.0` remains identified only as a superseded historical artifact
(`**Supersedes:** PBRD-001 v1.0 (frozen 2060ebd4)...`), distinguishable
by explicit version/commit citation. No duplicate active v1.1 exists (one
file, one contract identity block). RDGO-001, RIHAC-001, and RIASC-001 all
cite `PBRD-001 v1.1` in their "Related contracts" / reference-note
sections — references point to the current version.

## 7. RDGO-001 versioning

Confirmed current normative version: **v2.0**, `Status: FROZEN`. The MAJOR
bump is explicitly justified as a semantic **ordering correction**
(gate 3/4 transposition), citing RDGO-001 v1.0 §21's own rule that
reordering gates requires a new MAJOR with migration and independent
verification. `v1.0` remains historical-only, cited by frozen commit hash
`2060ebd4`. No other current normative document contains a conflicting
gate 3 = preflight / gate 4 = approval claim (independently swept — see
§35).

## 8. PBRD request-field reconstruction (fourteen facts, independently counted)

Recovered directly from the `## 4.` table in PBRD-001 v1.1 (not assumed):

| # | Field | Required | Trust owner |
|---:|---|---|---|
| 1 | `invocation_id` | Yes | PCAE coordinator |
| 2 | `attempt_id` | Yes | PCAE coordinator |
| 3 | `idempotency_key` | Yes | PCAE coordinator |
| 4 | `repository_identity` | Yes | Repository context resolver |
| 5 | `task_id` | Yes | Task lifecycle |
| 6 | `lifecycle_context` | Yes (session conditional) | Lifecycle/session owner |
| 7 | `runtime_target_id` | Yes | Target selector + registry |
| 8 | `adapter_descriptor_binding` | Yes | Runtime Registry/config owner |
| 9 | `prompt_hash` | Yes | Prompt builder |
| 10 | `requested_capability` | Yes | Integration contract/coordinator |
| 11 | `transport_type` | Yes | PBRD-001 integration |
| 12 | `network_requirement` | Yes | Registry/preflight owner |
| 13 | `filesystem_scope_ref` | Yes | Filesystem-scope owner |
| 14 | `human_authority_binding` | Yes | Human-authority validator |

Independently counted: **14 rows**, matching the contract's own claim.
`attempt_id` (fact 2) and `idempotency_key` (fact 3) are both present and
both marked required. `lifecycle_context` and `human_authority_binding`
remain single facts despite closed subfields (per v1.0 convention,
carried forward honestly).

## 9. `attempt_id` semantics (independently derived)

- **Definition:** identifies exactly one concrete dispatch try under one
  logical invocation.
- **Creator/owner:** trusted invocation coordinator, minted at RDGO-001
  gate 2, cryptographically strong random identity, `att-<32-hex>`.
- **Lifetime:** immutable from minting (gate 2) through result capture
  (gate 11); unconditionally bound at gate 9 (durable record).
- **Uniqueness:** unique per concrete try; NOT reusable — a consumed
  `attempt_id` cannot authorize a second try (RDGO §10a, §19 table).
- **Relation to one external-effect attempt:** exactly one `attempt_id` per
  attempted gate-10 dispatch.
- **Not synonymous with:** `invocation_id` (stable logical invocation
  across attempts), `approval_id` (human-authority artifact identity),
  `task_id` (PCAE task), `idempotency_key` (below). Cross-checked against
  the existing production `src/pcae/core/runtime_invocation.py`
  `new_invocation_id()`/`new_attempt_id()` functions, which already use
  exactly this `inv-`/`att-` convention (read-only cross-check; this
  module is out of this phase's scope and was not modified).

## 10. `idempotency_key` semantics (independently derived)

- **Definition:** identifies the logical dispatch operation's canonical
  content, not one concrete attempt.
- **Creator/owner:** trusted invocation coordinator, minted at gate 2,
  SHA-256 digest per RPAC-REQ-065.
- **Scope:** repository fingerprint/base commit, `task_id`, `prompt_hash`,
  `runtime_target_id`, adapter/descriptor/config digests, requested effect
  profiles, approval scope — excludes timestamps and attempt-specific
  mutable observations.
- **Replay/dedup role:** two attempts of the same unchanged logical
  request share the same `idempotency_key`; a different `idempotency_key`
  presented under the same `invocation_id` is a hard collision
  (RPAC-REQ-066, RDGO §19 table).
- **Not merely a second invocation identifier:** confirmed — it is a
  content digest, not an allocated random ID, and it is explicitly
  excluded from the TOCTOU mutable-fact table because it is immutable
  identity, not drifting state (RDGO §15).

## 11. Distinction verdict

**SEMANTICALLY DISTINCT: YES.**

| Scenario | `attempt_id` | `idempotency_key` |
|---|---|---|
| A) first attempt | new | new (function of content) |
| B) safe retry, same logical op | new | same as A |
| C) different target | new | new (target is in the digest) |
| D) different prompt | new | new (prompt_hash is in the digest) |
| E) different repo/task | new (new invocation, new approval too) | new |

`attempt_id` answers "which concrete try"; `idempotency_key` answers
"which logical request is this a (possibly repeated) attempt of."
Confirmed directly from RDGO-001 §10a's own framing, independently
re-derived by table above rather than copied.

## 12. Ownership

Both identifiers are PCAE-coordinator-owned, minted at gate 2, before
approval (gate 3). PBRD-001 §5 and §15 explicitly forbid the adapter,
runtime, provider, caller payload, or approval producer from setting,
echoing, or influencing either field — violation is a reject-at-construction
security invariant (`Caller sets/influences attempt_id or idempotency_key`
→ `Reject request construction`). Confirmed independently: neither field's
"Source" column in the fact table names anything other than "Trusted
invocation coordinator."

## 13. Authority/schema impact (RIHAC/RIASC)

RIHAC-001 v1.0 is **unchanged** and remains sufficient: the approval
subject is bound to `invocation_id`, not `attempt_id`, because
`attempt_limit`/`dispatch_limit` both equal `1` — approval authorizes at
most one attempt-slot without needing to name a specific `attempt_id` in
advance (an `attempt_id` is minted per dispatch try at gate 2, which is
*before* approval creation at gate 3, so the approval could not have named
it even if the model wanted to). This is architecturally coherent: the
approval says "one attempt only," and the gate-9 durable write is what
actually binds the specific `attempt_id` that was consumed. No RIHAC
change is required by the PBRD repair, and none was silently omitted — the
repaired PBRD-001 v1.1 §4a text explicitly states the ownership/minting
point without asking RIHAC to change.

RIASC-001 v1.0 similarly needs no change: `attempt_id`/`idempotency_key`
are dispatch-layer identifiers that belong in the PBRD-001 request and the
future `RuntimeInvocationRecord`, not in the human-facing approval schema.
Adding them to `subject` would be unnecessary widening of what a human is
asked to approve (the human approves an invocation/target/prompt/repo/task
tuple, not a specific retry attempt).

## 14. Invocation-record impact

RDGO-001 §10 (gate 9, durable pre-dispatch record) item 1 now
unconditionally binds `invocation_id`, `attempt_id`, and `idempotency_key`
together (previously "`attempt_id` where used" in v1.0 — the exact defect
identified by Finding B-2). Items 2–8 (repo/task, target, prompt, approval,
PB, RE, dispatch-intent bindings) are unchanged in count and content. No
production schema was implemented — this remains a frozen conceptual
description only, consistent with RPAC-REQ-067's "conceptual minimum
fields" framing.

## 15. Retry semantics

Per RDGO §10a/§18 and RPAC-REQ-072, independently re-derived:

| Retry class | New `attempt_id`? | `idempotency_key` | Fresh approval? | PB/RE re-eval? |
|---|---|---|---|---|
| Same logical op, covered by prior approval's limit/expiry | Yes (fresh gate-2 pass) | Same | No (existing approval reused if unconsumed) | Yes, always |
| Same logical op, prior approval consumed/expired/exceeded limit | Yes | Same | Yes | Yes |
| Changed prompt/target/provider/repo/task/effects/budget | Yes | New (new invocation) | Yes | Yes |
| Post-uncertain-dispatch resume | Yes | Same (if content unchanged) | Yes (existing key alone never authorizes redispatch) | Yes |

No automatic retry exists in any class; every row requires an explicit
fresh pass.

## 16. Uncertain-dispatch semantics

Test scenario (dispatch may have occurred, completion unprovable):
`DISPATCH_UNCERTAIN` is explicit RDGO/RIHAC state. Confirmed: "No replay"
and "no automatic retry" language present; attempt identity remains
preserved (the consumed `attempt_id` stays consumed); `idempotency_key`
does not imply exactly-once — RDGO §17 explicitly states "Exactly-once
execution is not promised... At-most-once attempt is enforced where
durable state proves it; otherwise uncertainty is explicit." Fresh
authority rule remains coherent: a same-`idempotency_key` retry after
uncertainty still needs a brand-new `attempt_id` and, per RPAC-REQ-072, a
fresh approval.

## 17. Replay threat scenarios (independently checked against security tables)

| Threat | Contract | Result |
|---|---|---|
| Same `attempt_id` + modified payload | PBRD §15, RDGO §19 | Hard collision; reject |
| Same `attempt_id` + different target | Same subject-mismatch rule | Reject |
| Same `idempotency_key` + different prompt | Content changed → different digest → not a valid replay | Reject as new request, new approval needed |
| Same `idempotency_key` + different repo/task | Same | Reject |
| Old PB ALLOW replayed against new attempt | PBRD §10: "A changed `attempt_id`... always invalidates any prior PB decision" | Reject |
| Old approval replayed against new attempt | RIHAC one-shot consumption; RDGO §19 | Reject (approval already consumed or subject-mismatched) |
| New `attempt_id` with stale approval | RIHAC freshness (§13) | Reject |
| Replay after uncertain dispatch | RDGO §17/§19 | No replay; fresh approval required |

All eight scenarios independently confirmed rejected by explicit contract
text (not inferred).

## 18. PB cardinality

**PRE-REPAIR PB FIELD COUNT: 12** (3U-selected, per PBRD-001's own
"Supersedes" note citing the v1.0 twelve-fact claim).
**POST-REPAIR PB FIELD COUNT: 14** (independently counted from the current
`## 4.` table, §8 above). `lifecycle_context` and `human_authority_binding`
remain single facts despite closed subfields — this nested-representation
convention is unchanged from v1.0 and does not inflate the count.
A full-repository sweep (`grep -rn "twelve" docs/contracts/*.md`) found
every remaining "twelve" occurrence in PBRD-001 is explicitly scoped as
historical ("v1.0", "superseded", "selected in 3U", "the other twelve
facts [in §5, referring to the original 12]") — no current unscoped claim
of "twelve" as the present PB field count exists anywhere in the
repository's normative contracts.

## 19. Shared-request compatibility

PBRD-001 §13 explicitly states the extension "SHALL NOT change behavior
for rollback, push, publication, source/docs mutation, backend invocation,
existing adapter actions, or any other known action," and that the
existing dry path (`adapter_invocation`, `simulation_only=true`) "SHALL NOT
be required to carry `attempt_id` or `idempotency_key`." No contract
wording implies any other action must adopt these fields. Confirmed no
production PB action definition elsewhere in the repository was touched by
this diff (§4).

## 20. `approval_present` / HUMAN_REVIEW semantics

PBRD §7 preserves: only successful RIHAC-001 validation may set
`approval_present=true`; it is not caller-settable; missing/stale/expired/
tampered evidence yields `false` or construction failure. §8 preserves the
precedent that valid approval satisfies `MissingHumanApprovalRule`
specifically without suppressing other independently applicable
HUMAN_REVIEW-producing policies — no global "approval erases all
HUMAN_REVIEW" claim exists; the text explicitly says "Other applicable
policies remain free to produce `DENY` or `HUMAN_REVIEW`; valid human
authority does not suppress them." The `attempt_id`/`idempotency_key`
addition touches neither `approval_present` nor POL-004 semantics.

## 21. POL-005

Confirmed unchanged: PBRD §12 states POL-005 "is unchanged in production by
this freeze. It remains universal and denies every truthful non-simulation
request, including `runtime_dispatch`." Freeze verdict line: "**POL-005
production behavior: UNCHANGED.**" No contract repair language anywhere
implies execution enablement.

## 22. RDGO reconstruction (gate order)

**PRE-REPAIR (v1.0) GATE 3/4 ORDER:** Gate 3 = Static preflight; Gate 4 =
Human authority creation (per 3V.1's finding text, independently
consistent with what a "static preflight before human approval" efficiency
rationale from 3U/3V would produce).

**POST-REPAIR (v2.0) GATE ORDER (verbatim, independently re-read from the
`## 1.` table):**

```text
1  Prompt preparation
2  Explicit target selection and request construction
3  Human authority creation
4  Static preflight
5  Approval validation
6  Permission Broker
7  Runtime Enforcement
8  Process containment and live preflight
9  Durable pre-dispatch record
10 Adapter dispatch                 <- first external effect
11 Result capture and intake
```

Exact transposition: gates 3 and 4 (only) swapped; gates 1, 2, 5–11 keep
their number, owner, and content. Confirmed both by table order (§1) and
by explicit contract prose ("gates 3 and 4 are transposed relative to
v1.0... No other gate's number, owner, or content changed.").

## 23. RPAC-REQ-042 verdict

**CONSISTENT.**

RDGO-001 v2.0's gate 3 (Human authority creation) precedes gate 4 (Static
preflight), an exact literal match to RPAC-REQ-042 steps 3 and 4
(`3. obtain human InvocationApproval; 4. resolve descriptor/config and
perform fact-only status/capability preflight`). Gates 5–10 likewise map
1:1 onto RPAC-REQ-042 steps 5–10 (approval-validation-adjacent revalidation
folds into gate 5/6, PB into gate 6, Runtime Enforcement into gate 7,
durable record into gate 9, dispatch into gate 10, intake into gate 11).
This is one of the two primary verification gates for this phase and is
independently confirmed CONSISTENT, not merely asserted by 3V.1R.

## 24. Repaired Gate 3/4 semantics

Gate 3 ("human authority creation") is exactly RIASC-001's
`RuntimeInvocationApproval` creation act — a distinct, non-defaultable
human confirmation. Gate 4 ("static preflight") is a fact-only,
non-executing capability/config check (registry/descriptor presence,
`transport_type=local_cli`, declared capability, `network_requirement=false`,
etc. — RDGO §5's explicit enumerated list, none of which launches a
process or accesses credentials). These names are read directly from the
RDGO v2.0 table headers, not inferred from 3U's earlier numbering scheme
(3U's original scheme had preflight *before* approval, which is precisely
what caused Finding B-1).

## 25. Approval/PB/RE ordering trade-off

3U's original rationale (avoid asking a human to approve a target later
found structurally unavailable) is explicitly acknowledged and explicitly
overridden by RPAC-REQ-042's fixed order (RDGO §5: "This is a deliberate
consequence of RPAC-REQ-042's fixed order: an approval that never reaches
gate 6 because gate 4 failed is unconsumed, imposes no cost beyond an
unused artifact, and grants no capability by itself"). Normative
consistency (matching the frozen RPAC-001 requirement) correctly wins over
the human-friction optimization. This is architecturally sound: RIHAC-001
§1/§20 already establishes "approval never implies capability," so an
approval whose target later fails preflight costs nothing beyond an unused
artifact — the tradeoff is honestly documented, not hidden.

## 26. Containment

Gate 8 (process containment and live preflight) remains positioned
strictly after Runtime Enforcement (gate 7) and strictly before the durable
record (gate 9) and dispatch (gate 10) — unchanged by the gate 3/4
transposition, since only gates 3 and 4 moved. Confirmed by table row
numbers 7/8/9/10 all unchanged from v1.0.

## 27. Durable-before-effect

Gate 9 (durable pre-dispatch record) remains strictly before gate 10
(adapter dispatch/first external effect). The eight-item durable record
(§14/§18 below) is unchanged in count; item 1 is enriched (now
unconditionally binding all three identifiers) but the gate-9-before-gate-10
ordering itself is untouched by the repair.

## 28. Approval consumption

RIHAC-001 §17 (unchanged v1.0 text) still places consumption exactly at
gate 9's durable `dispatch_attempted` write, synchronized with the same
durable boundary RDGO-001 v2.0 still uses at gate 9. No new gap was
introduced between consumption, durability, and effect — the repair moved
gates 3/4 relative to each other, not gate 9's position relative to gate
10.

## 29. First external effect

Gate 10 (adapter dispatch) is confirmed as the sole first-external-effect
gate across RPAC (step 9), RIHAC (§19, "Dispatch may have happened"),
PBRD (§3, "The external process shall be created only after RDGO-001
gates 1–9 succeed"), and RDGO itself (table column "External effect?" =
"Yes — first external execution effect" only at row 10). Fully consistent
across all four contracts.

## 30. At-most-once semantics

Crash analysis re-run under the repaired ordering: once gate 9's
`dispatch_attempted` marker is durable, the `attempt_id` is consumed
regardless of whether gate 10 is later proven to have started
(`DISPATCH_NOT_STARTED_AFTER_ATTEMPT_MARKER`) or remains unprovable
(`DISPATCH_UNCERTAIN`) — RDGO §10a explicitly states "Neither state
permits reuse of the same `attempt_id`." No exactly-once promise exists
anywhere in the repaired text; RDGO §17 states this in plain language.
Approval reuse after an uncertain effect is explicitly forbidden (RIHAC
§19). This is unchanged in substance by the gate-order repair — the repair
did not touch gate 9/10/11 or the crash-state table.

## 31. Durable cardinality

**PRE-REPAIR DURABLE ITEM COUNT: 8** (v1.0, item 1 = "`attempt_id` where
used," a weaker binding).
**POST-REPAIR DURABLE ITEM COUNT: 8** (unchanged; item 1 enriched to
unconditionally bind `invocation_id`, `attempt_id`, and `idempotency_key`
together — no new item was added, existing item 1 was strengthened).
Independently counted from the RDGO `## 10.` numbered list: items 1–8
(invocation identity; repo/task binding; target binding; prompt binding;
approval binding; PB binding; RE binding; dispatch intent/state). Both
`attempt_id` and `idempotency_key` belong in durable pre-effect state
(item 1) — confirmed necessary, since gate 9 is the approval-consumption
and at-most-once-guard boundary and must be able to prove which exact
attempt was consumed.

## 32. TOCTOU cardinality

**PRE-REPAIR TOCTOU FACT COUNT: 7.**
**POST-REPAIR TOCTOU FACT COUNT: 7 (unchanged).**
Independently counted from the RDGO `## 15.` table: HEAD, task
state/contract, prompt, runtime target, adapter configuration, adapter
executable identity, policy version. `attempt_id`/`idempotency_key` are
explicitly and correctly excluded — RDGO §15 states plainly: "`attempt_id`
and `idempotency_key` are not TOCTOU-mutable facts: both are minted once at
gate 2 and held immutable through gate 11... They are identity, not state
subject to drift." This is the correct classification, not an
undercounting: identity facts that never change after minting do not
belong in a mutable-fact drift table, and inflating the count merely
because new fields exist would be the actual error.

## 33. RIASC cardinality

**"16 required fields, 5 subject fields" — CONFIRMED CORRECT, unchanged.**
Independently counted from RIASC-001's `## 2. Required field inventory`
(16 numbered items) and the JSON Schema `subject.required` array (5
members: `invocation_id`, `runtime_target_id`, `prompt_hash`,
`repository_identity`, `task_id`). Explanation for why unchanged is
correct: `attempt_id`/`idempotency_key` are dispatch-layer (PBRD/RDGO)
identifiers minted after approval-subject binding was already frozen at
RIHAC/RIASC v1.0 — adding them to the human-facing approval subject would
be unnecessary widening of what a human reviews, not a required
consequence of the PBRD/RDGO repair.

## 34. Approval-subject cardinality

**5-member subject, independently confirmed** (see §33). No hidden
sixth/seventh member was introduced by the repair — `attempt_limit` is a
separate top-level required field (16th field), not a subject member, and
remains `const: 1`. `attempt_id` does not appear anywhere in the RIASC-001
JSON Schema (independently grepped: zero occurrences of the literal string
`"attempt_id"`).

## 35. Numeric sweep

Full-repository search of `docs/contracts/*.md` for stale count claims:

- **PB field count:** all "twelve" occurrences in PBRD-001 are explicitly
  historical/scoped (§18 above); no other contract file claims a PB
  runtime-dispatch field count.
- **Gate count:** no file besides RDGO-001/PBRD-001 mentions "gate 3"/
  "gate 4" together; RDGO-001 itself is internally consistent (11 gates,
  independently counted from its own table, §22).
- **Durable-item count:** "8" is the only current claim (RDGO §21 freeze
  verdict line and §10 table), independently recounted matching.
- **TOCTOU count:** "7" is the only current claim (RDGO §21 freeze
  verdict line and §15 table), independently recounted matching.
- **RIASC required-field count:** "sixteen" is the only current claim
  (RIASC §2), independently recounted matching (16 numbered items).
- **Approval-subject count:** "five" (RIHAC §5, RIASC §3), independently
  recounted matching (5 JSON Schema `required` entries).

No stale numeric claim was found in any current normative document.

## 36. Cross-contract identifier matrix

Independently reconstructed (not copied verbatim from RDGO §16, though
consistent with it):

| Concept | RPAC | RIHAC | RIASC | PBRD v1.1 | RDGO v2.0 | Consistent? |
|---|---|---|---|---|---|---|
| `invocation_id` | REQ-064 opaque, pre-approval | `subject.invocation_id` | `subject.invocation_id` (`^inv-[0-9a-f]{32}$`) | fact 1 | gates 2–11 | YES |
| `attempt_id` | REQ-064 unique per try | not a subject member (attempt_limit=1) | not present (by design) | fact 2, minted gate 2 | gates 2–11 | YES |
| `idempotency_key` | REQ-065 content digest | not a subject member | not present (by design) | fact 3, minted gate 2 | gates 2–11 | YES |
| `repository_identity`/fingerprint | git-root fingerprint | `subject.repository_identity` | `subject.repository_identity` | fact 4 | gates 5/8/9 | YES |
| `task_id` | task lifecycle binding | `subject.task_id` | `subject.task_id` | fact 5 | gates 5/8/9 | YES |
| `runtime_target_id` | explicit target only, no fallback | `subject.runtime_target_id` | `subject.runtime_target_id` | fact 7 | gates 2–11 | YES |
| `prompt_hash` | `pcae.prompt-semantic.v1` | `subject.prompt_hash` | `subject.prompt_hash` | fact 9 | gates 1/5/8/9 | YES |
| Approval ref | RIHAC/RIASC artifact | `approval_id`/`record_digest` | `approval_id` field | fact 14 (`human_authority_binding`) | gates 3/5/9 | YES |
| PB decision ref | REQ-044 gap acknowledged, now closed for identity | n/a | n/a | request/decision digests | gates 6/7/9 | YES |
| RE decision ref | REQ-045/046/047 | n/a | n/a | projected evidence only | gates 7/9 | YES |

No inconsistency found across any row; every contract's terminology for
each concept resolves to the same underlying identity.

## 37. Terminology

Independently audited: `invocation` (stable logical unit, `invocation_id`),
`attempt` (one concrete dispatch try, `attempt_id`), `dispatch` (gate 10's
external effect), `execution` (used loosely as a synonym for dispatch/
runtime activity — no separate technical meaning introduced), `retry` (a
fresh gate-2 pass reusing the same `idempotency_key`), `replay` (an
unauthorized/rejected reuse of a stale identifier or decision — always
negative/rejected in these contracts, never a sanctioned mechanism),
`idempotency` (content-based dedup via `idempotency_key`), `approval`
(RIHAC/RIASC human-authority artifact only), `permission` (PB `ALLOW`
decision only), `authorization` (used both generically in prose and
specifically for "human authorization" — classified as an intentional,
consistently-scoped overload rather than an accidental collision, since
every normative use is immediately qualified, e.g. "human authorization,"
"Runtime Enforcement... final whether-to-invoke"). No unqualified,
ambiguous overload was found.

## 38. Security scenarios

All independently re-tested against explicit contract text (see the fresh
test module for exact assertions):

```text
valid approval + PB DENY                      -> no dispatch   CONFIRMED
PB ALLOW + no approval                        -> no dispatch   CONFIRMED
valid approval + PB ALLOW + RE DENY           -> no dispatch   CONFIRMED
runtime unavailable                           -> no dispatch   CONFIRMED (gate 4/8)
same attempt_id + changed payload             -> reject        CONFIRMED
same idempotency_key + changed target         -> reject        CONFIRMED (content changes -> different digest -> new request)
uncertain prior dispatch                      -> no auto retry CONFIRMED
```

## 39. Dry compatibility

Traced the current production dry consumer
(`src/pcae/core/runtime_dry_consumption.py` → `simulate_invocation` in
`src/pcae/core/runtime_adapter.py`, read-only, not modified). Confirmed:

- The dry PB request still uses `action_type=ACTION_ADAPTER_INVOCATION`,
  `simulation_only=True`, with **no** `attempt_id`/`idempotency_key` fields
  in the PB call — exactly matching PBRD-001 §13's claim that the dry path
  is unmigrated and does not carry these fields.
- **Notable independent finding (strengthens implementation readiness):**
  the existing production `simulate_invocation()` gate sequence already
  binds `SIM_APPROVAL_BOUND` strictly before `SIM_CAPABLE` (approval
  binding before capability/preflight check) — i.e., the shipped mock-v1
  code was *already* RPAC-REQ-042-consistent in this relative ordering,
  independent of and prior to this contract repair. This is corroborating
  evidence that RDGO-001 v2.0's gate 3/4 order is not an invented
  preference but matches existing, tested, shipped PCAE behavior for the
  mock path.
- No runtime behavior change: the dry path was not touched by the 3V.1R
  diff (§4), and this phase did not modify it either.

## 40. PB compatibility

No current PB action definition outside PBRD-001's own future
`runtime_dispatch` proposal references `attempt_id` or `idempotency_key`.
Rollback, push, publication, and existing adapter/backend actions are
unaffected — confirmed no other contract file was touched by the 3V.1R
diff, and PBRD §13 explicitly disclaims any behavior change to those
actions.

## 41. Existing MUST-FIX findings

The two pre-existing 3S.2.1 findings — (1) invocation-store path
confinement gap (not reachable via current production entry point) and
(2) malformed-adapter-result / corrupted-`request.json` fail-closed-but-
not-graceful-quarantine gap — are **unchanged in reachability and remain
explicit prerequisites**. RDGO-001 v2.0 §12 (gate 11) explicitly carries
this forward verbatim: "This contract does not repair the existing 3S.2.1
malformed-result finding; that repair is blocking before the first
non-mock adapter becomes reachable." The 3V.1R repair phase's own document
does not claim to have closed either finding, and this phase's fresh test
suite confirms that language is still present post-repair.

## 42. Runtime inspect limitation

`TRUTHFUL_WITH_LIMITATION` carried forward. `pcae runtime inspect`
reported `not_implemented` at both entry and close of this phase (§3, §57).
No repaired contract text claims or depends on runtime inspect already
exposing real adapter availability — RIASC-001/RIHAC-001/PBRD-001/RDGO-001
all describe a *future* implementation boundary, never a currently
satisfied one.

## 43. API/network boundary

Confirmed unchanged: `API/PROVIDER: NOT FROZEN`; `NETWORK EGRESS:
UNRESOLVED`. `network_requirement` remains `const: false` in both
PBRD-001 fact 12 and RIASC-001's `approval_scope.network_required`. No
contamination of local-CLI-v1 scope by network/provider concerns was found
in the repaired text.

## 44. Version matrix

| Contract | Before repair | After repair | Current normative | Verdict |
|---|---|---|---|---|
| RIHAC-001 | 1.0 | 1.0 | 1.0 | UNCHANGED — CORRECT (no repair required) |
| RIASC-001 | 1.0 | 1.0 | 1.0 | UNCHANGED — CORRECT (no repair required) |
| PBRD-001 | 1.0 | 1.1 | 1.1 | REPAIRED — MINOR (additive facts), verified against §16 versioning rule |
| RDGO-001 | 1.0 | 2.0 | 2.0 | REPAIRED — MAJOR (gate reorder), verified against §21 versioning rule |

Independently verified from each contract's own `**Version:**` line, not
assumed.

## 45. Provenance/supersession

`PBRD-001 v1.1` explicitly supersedes/corrects `v1.0` (frozen `2060ebd4`),
citing `Finding B-149O.20L.7O.3V.1-2` by exact ID. `RDGO-001 v2.0`
explicitly supersedes `v1.0` (frozen `2060ebd4`), citing
`Finding B-149O.20L.7O.3V.1-1` by exact ID. No ambiguity: both supersession
notes name the exact frozen commit and the exact finding they close. RIHAC/
RIASC both carry an explicit "Reference note (149O.20L.7O.3V.1R)" pointing
readers at the current PBRD/RDGO versions.

## 46. Normative-vs-implemented

| Capability | Frozen contract | Production implementation |
|---|---|---|
| `RuntimeInvocationApproval` schema | RIASC-001 v1.0 FROZEN | NOT IMPLEMENTED |
| Approval store | RIHAC-001 §15 FROZEN | NOT IMPLEMENTED |
| Approval validator | RIHAC-001 §16 FROZEN | NOT IMPLEMENTED |
| `runtime_dispatch` PB action | PBRD-001 v1.1 FROZEN | NOT IMPLEMENTED |
| `attempt_id`/`idempotency_key` binding (dispatch-layer) | PBRD-001 v1.1/RDGO-001 v2.0 §10a FROZEN | NOT IMPLEMENTED for `runtime_dispatch`; **already implemented and shipped** for the unrelated mock/dry `InvocationRequest` model (`src/pcae/core/runtime_invocation.py`), which independently corroborates the semantics without constituting the future action's implementation |
| POL-005 evolution | PBRD-001 §12 FROZEN (boundary only) | NOT IMPLEMENTED (POL-005 unchanged) |
| RE projection | RDGO-001 §8/§14 FROZEN | NOT IMPLEMENTED |
| Shell Gate | RPAC-REQ-047/048 | NOT IMPLEMENTED (simulation-only) |
| Real adapter | RPAC-001 | NOT IMPLEMENTED |

Production implementation remains mostly NO, as expected. The one
noteworthy nuance (recorded honestly, not glossed over) is that the
*identifier conventions* (`inv-`/`att-` prefixes, SHA-256 idempotency
digest excluding attempt-specific facts) already exist in shipped mock/dry
code for an unrelated purpose (RPAC-001 v1.0 base compliance in the mock
path) — this is corroborating precedent, not a completed implementation of
the `runtime_dispatch` action itself.

## 47. Implementation readiness

**LOCAL-CLI AUTHORITY/PERMISSION IMPLEMENTATION READY: YES.**

Both 3V.1 blockers are independently confirmed closed (§48). No new
normative contradiction was found across any of the 60 sections/checks
performed. All identifiers and counts reconcile exactly (§18, §31–§35).
No new authority semantics need to be invented during implementation — the
attempt/idempotency model is fully specified (owner, minting point,
format, digest scope, retry/replay rules) and is even already precedented
by shipped mock code using the identical ID conventions. This does not
mean real execution is ready — see §48.

## 48. Real-runtime readiness

**REAL-RUNTIME READY: NO.**

Every real-dispatch prerequisite remains unimplemented: approval store/
validator, `runtime_dispatch` PB action, Runtime Enforcement real gate,
Shell Gate, real adapter, POL-005 eligibility change, and the two 3S.2.1
MUST-FIX repairs (§41) all remain outstanding. Runtime remains `Observed`/
`observe`/`unavailable` (§3, §57).

## 49. Findings

**BLOCKING: 0.**

**MUST-FIX: 0 new** (the two pre-existing 3S.2.1 findings are carried
forward unchanged as DEFERRED-REAL-RUNTIME prerequisites, not newly
discovered or newly reachable by this repair — see §41; they are not
double-counted here since they were not introduced or altered by 3V.1R or
this verification).

**NON-BLOCKING: 1.**
- `NB-149O.20L.7O.3V.1R.1-001`: PBRD-001 §17's freeze verdict block and
  §16 versioning text are internally consistent, but the contract family
  would benefit from a single canonical "current field count" restatement
  near the top of the document (currently requires reading §4's table plus
  the "twelve superseded by fourteen" prose in §4 to reconstruct the
  count with full confidence). Cosmetic; does not block implementation.

**OBSERVATION: 2.**
- The existing production mock/dry `simulate_invocation()` gate order
  already matches RPAC-REQ-042's approval-before-preflight ordering,
  independently corroborating the RDGO-001 v2.0 repair (§39).
- The existing production `runtime_invocation.py` `InvocationRequest`
  model already implements `attempt_id`/`idempotency_key` with matching ID
  conventions and idempotency-digest exclusion rules, independently
  corroborating the PBRD-001 v1.1/RDGO-001 v2.0 §10a semantics (§9, §46).

**DEFERRED-REAL-RUNTIME: 2** (the two pre-existing 3S.2.1 MUST-FIX
findings, §41 — explicit prerequisites before the first non-mock adapter
becomes reachable; unchanged by this phase).

## 50. Final verdict

```text
REPAIRED LOCAL-CLI AUTHORITY/PERMISSION CONTRACTS: INDEPENDENTLY VERIFIED
3V.1 BLOCKING 1 (RDGO gate order vs RPAC-REQ-042): CLOSED
3V.1 BLOCKING 2 (PBRD attempt/idempotency binding): CLOSED
PBRD-001: v1.1 VERIFIED, attempt_id: BOUND/VERIFIED, idempotency_key: BOUND/VERIFIED
RDGO-001: v2.0 VERIFIED, RPAC-REQ-042: CONSISTENT
RIHAC-001: v1.0 VERIFIED (unchanged, correctly so)
RIASC-001: v1.0 NORMATIVE SCHEMA VERIFIED (unchanged, correctly so)
PRODUCTION ENFORCEMENT NOT IMPLEMENTED
DRY PATH: UNCHANGED
POL-005: UNCHANGED
LOCAL-CLI AUTHORITY/PERMISSION IMPLEMENTATION READY: YES
REAL-RUNTIME READY: NO
BLOCKING: 0
MUST-FIX: 0 new (2 pre-existing 3S.2.1 findings unchanged, deferred-real-runtime)
NON-BLOCKING: 1
```

## 51. Recommended next phase

**149O.20L.7O.3V.2 — Local-CLI Real-Runtime Dispatch Implementation
Planning** (a bounded implementation-*plan* phase converting the now
implementation-ready PBRD-001 v1.1 / RDGO-001 v2.0 / RIHAC-001 v1.0 /
RIASC-001 v1.0 contract set into a concrete implementation blueprint —
approval store/validator, `runtime_dispatch` PB action wiring, Runtime
Enforcement real gate, Shell Gate — while explicitly sequencing the two
pre-existing 3S.2.1 MUST-FIX repairs (path confinement, malformed-result
handling) as prerequisites before any real adapter becomes reachable, and
explicitly excluding any POL-005 relaxation or execution activation from
its own scope. This is a planning phase, not implementation directly, and
still requires its own human authorization before implementation begins.

**Not authorized to begin automatically. Stop after 3V.1R.1.**

## 52. Human decision required

**HUMAN DECISION: REQUIRED.** This phase performs independent verification
only. It does not authorize, plan, or begin implementation of the
`runtime_dispatch` action, approval storage/validation, POL-005 evolution,
or any real-execution capability. A human must explicitly authorize
149O.20L.7O.3V.2 (or an alternative next step) before any further governed
phase in this track begins.
