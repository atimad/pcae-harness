# Phase 128B - Historical Memory Review & Hardening Contract Freeze

## 1. Purpose

Phase 128B freezes the canonical hardening contract for the complete
Historical Memory subsystem (Track 127: 127A-127F), operationalizing
128A's review-and-hardening architecture into binding, normative
requirements.

The objective is quality, consistency, determinism, and
maintainability only. No capability expansion.

The contract governs review and hardening scope and behavior, not new
implementation. It is binding for:

- 128C - Historical Memory Review & Hardening Contract Verification;
- 128D - Historical Memory Hardening Plan;
- 128E - Historical Memory Hardening Implementation;
- 128F - Historical Memory Hardening Verification.

128B is documentation only. It performs no repair, no implementation,
no schema modification, no source code change, no test code change,
and no runtime behavior change.

## 2. Contract Authority

This document is the canonical Track 128 hardening contract unless
explicitly superseded by a future governed contract-amendment phase.
It operates inside, and does not amend:

- the 125B Next Architecture Direction Contract;
- the 127B Historical Memory Contract (still fully binding and
  unchanged by this document);
- the already-frozen 119Q `historical_memory_snapshot.schema.json`
  (unchanged by this contract).

Later Track 128 phases may verify, plan, and implement only inside
this contract's constraints. No later phase may silently reinterpret
this contract as authorizing capability expansion, runtime behavior
change, execution capability, or a schema change without its own
separate, explicitly scoped governed contract-amendment phase.

## 3. Scope

The contract applies to the complete Historical Memory subsystem
produced by Track 127:

- Historical Memory Builder (`historical_builder.py`);
- Timeline generation;
- Event generation;
- Transition generation;
- Evidence mapping;
- Temporal reconstruction (`git_source.py`);
- Serialization (`persistence.py`);
- CLI integration (`pcae repository-intelligence historical-memory
  generate`);
- Validation (`historical_validation.py`);
- Persistence layout;
- Documentation (127A-127F, and this chapter's own 128A-128F
  documents).

## 4. Hardening Responsibility Contract

Hardening may improve only:

- implementation consistency;
- terminology consistency;
- persistence consistency;
- evidence consistency;
- limitation propagation consistency;
- boundary disclosure consistency;
- serialization consistency;
- deterministic behavior;
- interface consistency;
- documentation consistency;
- governance consistency;
- testing consistency.

Hardening shall not expand functionality. This restates 128A's own
"Hardening Architecture" section as a binding normative requirement:
no future 128D-128E phase may add a new artifact family, new event
type, new relationship type, new CLI capability, new consumer
integration, or any other functional surface beyond what 127A-127F
already implemented. A hardening change that would require a schema
amendment, a new capability, or a change to `event_type`/
`relationship_type`/`verification_state` semantics is out of scope for
this contract and requires its own separate, explicitly scoped
governed phase.

## 5. Cross-Track Consistency Contract

Track 128 hardening shall preserve compatibility with, and modify none
of:

- **Track 119 executable schemas** - the already-frozen
  `historical_memory_snapshot.schema.json` (`119Q.1.0-json-schema`);
  no schema change is authorized by this contract.
- **Track 120 Repository Knowledge Snapshot** - Historical Memory's
  only Repository Intelligence input, reached exclusively through the
  Track 121 Query Layer; not modified by Track 128.
- **Track 121 Query Layer** - Historical Memory's exclusive access
  path into Repository Intelligence content; not modified by Track
  128. Task-contract/git-history discovery remains its own, separate,
  equally bounded, non-Query-Layer path (128A's Architecture category
  finding, re-affirmed here as binding).
- **Track 122 Advisory Context** - not modified; Historical Memory's
  eventual consumption by Advisory remains unscoped and unauthorized
  by Track 128.
- **Track 123 Change Impact** - not modified; the same unscoped/
  unauthorized status applies.
- **Track 126 Dependency Knowledge Graph** - not modified; the
  optional structural cross-reference input (Section 10's
  documentation finding) remains unexercised and unauthorized for
  wiring by this contract.
- **Track 127 Historical Memory** - the subject of this hardening
  chapter; 127A-127F's own architecture, contract, plan,
  implementation, and verification documents remain unchanged
  historical record, never retroactively edited.

Stable terminology across this chapter and Track 127: Historical
Memory Snapshot, Historical Event, Historical Timeline, Historical
Transition, Historical Relationship, Historical Context, Historical
Evidence, phase lineage, release lineage, source attribution,
verification state, snapshot limitations, boundary disclosures,
unknown, unverified.

## 6. Determinism Contract

Equivalent repository state shall continue producing equivalent
Historical Memory output. No additional entropy.

This restates 127B Section 11 and 128A's "Determinism Architecture"
section as binding for every phase this contract governs:

- Given the same source inputs (Repository Knowledge Snapshot content,
  governed phase-completion metadata, commit history at a fixed
  point), the Historical Memory Builder must continue to produce
  byte-equal output (modulo the two approved non-load-bearing
  timestamp fields: `envelope.generated_at_utc` and
  `snapshot_identity.snapshot_created_at_utc`) after any 128D-128E
  hardening change.
- No historical claim, event, or relationship may be created by
  inference, heuristic guessing, probabilistic scoring, or AI-based
  interpretation, before or after hardening.
- Stable identifiers (`event_id`, `claim_id`, `relationship_id`, and
  every other record's own identifier field) must remain deterministic
  functions of their underlying source content, unchanged by
  hardening.
- Hardening may improve *how* determinism is achieved or documented
  (e.g. clarifying the identifier scheme's own documentation, adding
  test coverage for previously-untested sortable collections) but
  shall never change *what* deterministic output equivalent input
  produces.

## 7. Evidence Contract

Evidence attribution shall remain unchanged. Evidence shall never be
inferred.

This restates 127B Section 7 and 128A's "Evidence Architecture"
section as binding:

- Every event, claim, lineage record, decision record, repair/
  hardening record, supersession/correction record, and relationship
  continues to require `source_attribution` citing specific source
  content - never a generic citation.
- Hardening may correct an attribution's own *description* where it
  is demonstrably stale or inaccurate (as 127F's Defect 1 fix did -
  the underlying attribution was always evidence-based; only its
  self-description was momentarily stale) but shall never attach
  evidence to a claim that lacked direct, deterministic source support
  before hardening.
- No future 128D-128E phase may reinterpret attribution as proof of
  historical truth, merge records in a way that loses per-record
  provenance, or convert a historical evidence gap into evidence
  support.

## 8. Temporal Contract

Chronological ordering shall remain deterministic. No inferred
chronology.

This restates 127B Section 6 and 128A's "Temporal Consistency
Architecture" section as binding:

- Every `historical_event` continues to order by its own declared
  `event_time`; every `historical_claim` remains scoped to its
  declared `historical_period`.
- Hardening may improve *how clearly* the ordering rule is documented
  or tested (128A's Testing category named the
  `release_lineage`/`repair_hardening_history` coverage gap 127F
  already closed within Track 127 as a worked example of the kind of
  gap this category watches for) but shall never introduce a
  heuristic, estimated, or inferred time reference where the
  underlying source data does not already deterministically establish
  one.
- Regeneration continues to extend, never retroactively edit, the
  historical record (127B Section 6's "Regeneration extends, never
  retroactively edits" rule, unchanged).

## 9. Read-Only Contract

Hardening shall never modify:

- repository contents (source files, working tree content);
- git history (no commit, no ref move, no tag creation, beyond the
  governed lifecycle commands this phase itself uses to record its own
  documentation change);
- the Repository Knowledge Snapshot (read-only via the Track 121 Query
  Layer);
- the Dependency Knowledge Graph (not consumed in v1; would remain
  read-only if and when a future, separately governed phase wires the
  optional cross-reference);
- task contracts, other than the task contract this phase itself
  creates and completes under normal governed lifecycle operation.

This restates 127B Section 8 and 128A's "Read-Only Architecture"
section, independently re-verified via direct checksum/HEAD comparison
in 127F, as binding unchanged for all Track 128 hardening work.

## 10. Serialization Contract

Hardening may improve serialization consistency while preserving
backward compatibility.

This restates 128A's "Serialization Architecture" section as binding:

- `serialize_deterministic_json` reuse remains unchanged; no future
  128D-128E phase may reintroduce parallel serialization logic.
- Deterministic key sorting, pretty/compact mode consistency, and
  explicit-request-only persistence all remain unchanged.
- The `graphs/`-vs-`snapshots/` persistence subdirectory-naming
  inconsistency 128A found (Section 13's Documentation Findings below)
  is a candidate for a future 128D plan to evaluate - but any such
  change is scoped to Historical Memory's own persistence module only,
  never a change to Dependency Knowledge Graph's own directory (out of
  Track 128's scope by definition; a change there requires its own
  separately governed Track 126 phase), and never a change to the
  frozen 119Q/119O/119S schema versions or the
  `serialize_deterministic_json` helper's own behavior.
- No hardening change may alter the on-disk or wire-format
  compatibility of an already-generated artifact in a way that breaks
  an existing consumer's ability to read it.

## 11. Failure Contract

Hardening shall preserve fail-closed behavior. No fail-open paths may
be introduced.

This restates 127B Section 9 and 128A's "Failure Architecture" section
as binding: every one of the 12 fail-closed categories 127F
independently verified (missing source, corrupted source, incompatible
version, duplicate identifiers, missing evidence/limitations/boundary,
missing task history, chronology violation, and their siblings) must
remain fail-closed after any future 128D-128E hardening change.
Hardening must never relax a failure condition into a warning, a
default value, or a silently degraded artifact.

## 12. Governance Contract

Track 128 hardening shall preserve, binding for every phase this
contract governs:

- **observe-only runtime** - runtime state remains `Observed`, maximum
  plugin capability remains `observe`;
- **execution unavailable** - execution capability remains
  `unavailable`; no phase this contract binds (128C-128F) may change
  this boundary;
- **reproducibility** - Section 6;
- **auditability** - every phase produces a complete,
  metadata-consistent canonical phase report; every Historical Memory
  artifact remains independently inspectable;
- **explainability** - every event, claim, and relationship continues
  to trace to specific source content and, where a transformation was
  required, an explicit derivation rule.

Hardening must not make Historical Memory appear more complete,
authoritative, current, or actionable than its sources and limitations
support - restated from 124A/128A's identical principle. In
particular, hardening must never reclassify an `event_type: unknown`
record into a more specific type without new, genuinely deterministic
source support - doing so is functionality expansion, explicitly out
of Track 128's scope, not hardening.

## 13. Documentation Findings Carried Forward

128A found two genuine, concrete, non-blocking documentation-debt
items via direct source inspection. Both are carried forward here as
hardening candidates only - neither is repaired in 128B, and neither
is authorized for repair by this contract alone; a future 128D plan
must explicitly scope any repair before 128E may implement it:

1. **Persistence subdirectory naming inconsistency** - Repository
   Knowledge Snapshot and Historical Memory Snapshot both write
   timestamped files under a `snapshots/` subdirectory, but Dependency
   Knowledge Graph Snapshot writes under `graphs/` (confirmed by
   direct inspection of all three `persistence.py` modules'
   `DEFAULT_OUTPUT_SUBDIR` constants). Cosmetic, not functional - no
   cross-family artifact confusion results, since each family already
   writes to its own distinct `DEFAULT_OUTPUT_SUBDIR`. A future 128D
   plan may evaluate standardizing Historical Memory's own convention,
   or documenting the divergence permanently; it may not unilaterally
   rename Dependency Knowledge Graph's `graphs/` directory, which
   belongs to Track 126 and requires its own separately governed
   phase.
2. **Optional Dependency Knowledge Graph CLI input scope** - 127D
   scoped an optional Dependency Knowledge Graph structural
   cross-reference input that exists in the Historical Memory
   builder's own data model (`historical_relationship`'s `artifact`
   reference type) but has no CLI entry point (no `--dependency-graph`
   or similarly named option), and is confirmed unexercised in the
   v1 prototype. Not a defect - omitting an unused flag is honest, not
   incomplete. A future 128D plan may decide whether to add the CLI
   option or to explicitly close the gap in documentation instead.

## 14. Deferred Capabilities

Explicitly deferred, not authorized by this contract or any phase it
binds (128C-128F):

- historical reasoning;
- causal reasoning;
- predictive history;
- recommendations;
- Decision Evaluation (integration);
- graph traversal;
- AI interpretation;
- execution planning;
- execution capability;
- new Historical Memory artifact families;
- Dependency Knowledge Graph expansion;
- Advisory reasoning;
- runtime plugins;
- AI provider integration;
- external API integration;
- repository scanning beyond what 127E already performs;
- new schemas.

Any future work in these areas requires its own separate, explicitly
scoped governed architecture and contract path outside this contract's
authorization.

## 15. Known Inherited Issues

Carried forward unchanged, not repaired in this phase:

- 119Q report-generation-ordering defect: lifecycle/tooling debt,
  non-blocking for this contract freeze.
- 119AB phase-id comparison bug: lifecycle/tooling debt, non-blocking
  for this contract freeze.
- Recurring `pending_final_telegram_delivery` reporting detail:
  lifecycle/tooling debt, non-blocking when final report delivery is
  explicitly verified.

**Not inherited defects - do not reintroduce**: 126G (Telegram
Canonical Report Dispatch Repair) and 126G.1 (Telegram Commit Trust
Metadata Repair) are closed, verified repairs, excluded from this
list; neither 128C-128F may reintroduce either as if unresolved.

## 16. Technical Debt Classification

This phase classifies inherited and 128A-identified technical debt
only. It repairs none of it. Only the following categories are
recognized under this contract:

- **Documentation debt**: the two findings in Section 13 above
  (persistence subdirectory naming; optional Dependency Knowledge
  Graph CLI input scope).
- **Implementation debt**: none identified beyond what 127F already
  found and closed within Track 127 itself (resolved, not open debt).
- **Testing debt**: none identified as genuinely missing; the
  synthetic-git-repo fixture asymmetry 128A noted is an expected
  consequence of Historical Memory being the only artifact family with
  a temporal/git-history dimension, not a coverage gap.
- **Governance debt**: none identified - every 127A-127F and 128A
  canonical report reached full trust completeness.
- **Lifecycle/tooling debt**: Section 15's three inherited items.

No repairs occur during 128B. A future 128D plan classifies which of
Section 13/15's items, if any, are worth scoping for 128E repair.

## 17. Strict Non-Goals

This phase does not implement: historical reasoning; causal inference;
recommendations; Decision Evaluation; execution planning; execution
capability; runtime plugins; schema changes; source code; test code.

## 18. Governance Rules

Every phase this contract binds (128C-128F) must:

- follow PCAE governance;
- use governed lifecycle commands only (`pcae task`, `pcae phase`,
  `pcae commit`, `pcae push`) - no raw `git commit`, no raw `git
  push`;
- never force-push;
- never use `--no-verify`;
- preserve the execution boundary (runtime `Observed`, execution
  `unavailable`, maximum plugin capability `observe`);
- produce complete, metadata-consistent canonical phase reports.

## 19. Relationship to Future Phases

- **128C - Historical Memory Review & Hardening Contract
  Verification**: independently re-verify this contract's every
  restated requirement against 127A-127F's and 128A's own source
  documents and, where a requirement cites real code behavior (e.g.
  `DEFAULT_OUTPUT_SUBDIR` constants, `serialize_deterministic_json`
  reuse), directly re-inspect the actual source files rather than
  re-citing this contract's or 128A's own quoted text.
- **128D - Historical Memory Hardening Plan**: define the bounded
  hardening plan inside this contract, including an explicit decision
  on whether either Section 13 finding is worth scoping for repair.
- **128E - Historical Memory Hardening Implementation**: implement
  only the bounded hardening authorized by 128B-128D.
- **128F - Historical Memory Hardening Verification**: independently
  verify 128E's implementation (if any) against this contract and the
  128D plan, and confirm no functionality expansion occurred.

No 128C work begins in this phase.

## 20. Acceptance

128B is complete when this contract is frozen, project memory reflects
128B completion, runtime remains `Observed` / `observe` / execution
unavailable, no implementation has occurred, and the recommended next
phase is 128C - Historical Memory Review & Hardening Contract
Verification.
