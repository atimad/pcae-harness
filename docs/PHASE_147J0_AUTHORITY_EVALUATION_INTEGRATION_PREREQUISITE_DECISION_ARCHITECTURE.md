# Phase 147J.0: Authority Evaluation Integration Prerequisite Decision Architecture

**Phase ID:** 147J.0
**Mode:** Architecture (architecture only — no implementation, no contract amendments, no runtime changes, no lifecycle changes)
**Baseline:** Phase 147I (Authority Evaluation Model Core Operational Readiness Assessment)
**Date:** 2026-07-31

---

## Authorization

Phase 147I concluded **CORE OPERATIONALLY READY — INTEGRATION ARCHITECTURE NOT READY**: the standalone `pcae.authority_evaluation` package is fully implemented and independently verified, but integration architecture (a future 147J) could not be authorized because five architectural ownership questions were unresolved (147I §31). This phase is authorized, by explicit human instruction, to resolve those prerequisite architectural decisions. This phase remains architecture-only throughout: no `src/pcae/**` change, no contract amendment, no runtime change, no lifecycle change.

### Bootstrap

Bootstrap was run against a clean, synchronized repository before this phase's task contract was opened:

```
pcae session bootstrap --agent-id claude-code --sync-lock
  -> healthy; latest completed phase 147I; recommended next: a narrowly scoped
     prerequisite-decision phase (exactly this phase); readiness "blocked" only
     because the post-147I idle placeholder task was still active — the expected
     pre-phase-start state
pcae check              -> passed (after opening the 147J.0 task contract)
pcae health              -> healthy; all required files present; policy valid; git clean
pcae doctor task-memory  -> clean, no inconsistencies
pcae runtime inspect     -> Runtime state Observed; Execution capability unavailable;
                            Registry status empty; Plugin count 0; Governance posture
                            non-executing (unchanged from 147I)
pcae push check          -> nothing_to_push, health healthy, check passed
```

Confirmed: repository clean; branch synchronized (0 ahead / 0 behind `origin/main`); no other active governed phase; the Phase 147H/147I-verified `src/pcae/authority_evaluation/**` implementation unchanged since 147I; runtime unchanged (Observed / observe / unavailable). A governed task contract (`tasks/active/20260731-0141-phase-147j-0-authority-evaluation-integration-prerequisite-decision-architecture.md`) was opened, scoped to this report plus ordinary task/phase bookkeeping files only.

Research for this phase was performed by two parallel, read-only research passes: one reconstructing the actual `pcae.authority_evaluation`/`interactive_workflow`/`governance.publication`/`cltr`/Decision-Template-schema code with file:line citations, and one extracting exact requirement text from all nine governing contracts (`docs/contracts/`). Both are synthesized directly into this report; no finding below is delegated to an agent's own synthesis.

---

## 1. Executive Summary

Phase 147I found the standalone Authority Evaluation Model implementation operationally ready but flagged four genuinely open architectural questions blocking integration architecture: (A) where `claimed_identity` comes from, (B) where Decision Template resolution (and therefore `citation_text`) happens, (C) whether `evidence_kind` is compatible across the nine governing contracts, and (D) whether a two-stage (advisory + fresh pre-publication) evaluation model is necessary and how it behaves.

This phase's re-grounded research — reading the actual AEMIC-001 v1.2 and CHGR-001 v1.2 contract text directly, not only 147I's paraphrase of v1.0/v1.1 — finds that **two of these four questions are substantially more resolved by already-frozen contract text than 147I characterized them**:

- **Decision A is effectively pre-decided by AEM-REQ-014 and AEMIC-REQ-019**: the contract already names `Session.owner_identity` ("`--owner-id`, IWPC-REQ-015; IWC-001's session-owner concept") as `claimed_identity`'s source, explicitly stating "this package collects nothing." What remained undecided was not *which field* — it was *whether this repository should architecturally ratify that adoption* and *who reads it*. This phase performs that ratification.
- **Decision C dissolves rather than requires a mapping**: AEM-001/AEMIC-001 define no `evidence_kind` concept at all (zero occurrences in either contract or in `src/pcae/authority_evaluation/`). CHGR-001/IWC-001/PEC-001's `evidence_kind` (a closed two-value identity-assurance label, `typed_confirmation_only`/`os_authenticated_user`) is a different field on a different object serving a different purpose. There is no incompatibility to repair because the two concepts never currently intersect.
- **Decision B (Decision Template resolution) remains the single genuinely unbuilt prerequisite** — no code anywhere resolves a `template_ref`/`template_version` pair to a Decision Template document and reads its `eligible_authority` field, though the schema itself is already used for standalone structural validation via `pcae governance-record template-inspect`/`verify --related`. This phase determines the resolution architecture (not the implementation).
- **Decision D (two-stage evaluation)** is confirmed necessary, now with contract-grounded reasoning: IWPC-001 §21 (IWPC-REQ-144/147) establishes that everything upstream of Publication's own `O_CREAT|O_EXCL` commit point is explicitly "not authority-relevant" (last-write-wins), meaning any evaluation performed before that point is provisional by the pipeline's own design — an independent contract-level confirmation of 147I's staleness concern.

This phase resolves all four decisions at the architecture level (§3–§6), maps their dependencies (§7), defines the Registry boundary without designing the Registry itself (§8), produces an authoritative evaluator-input ownership table (§9), compares three integration strategies (§10), and selects a preferred direction (§11). **Overall verdict: INTEGRATION PREREQUISITES RESOLVED WITH OBSERVATIONS** (§15) — a small number of items remain open, but none of them blocks 147J from starting; they are 147J's own architecture-phase work, not further prerequisite-decision work.

---

## 2. Problem Statement

Phase 147I identified that three of `evaluate()`'s seven inputs had no clear lawful source in the current lifecycle: `claimed_identity` (no defined source), `declaration` (blocked on a nonexistent concrete `AuthorityRegistry`), and `citation_text` (blocked on a nonexistent Decision Template resolution mechanism) — and that a fourth question, `evidence_kind` compatibility across contracts, required direct textual confirmation 147I's own research did not complete. A fifth item, explicit sign-off on a proposed two-stage evaluation timing model, was also flagged as outstanding.

Proceeding directly to a 147J-style integration-architecture-freeze phase without resolving these would force that phase to either invent sourcing decisions without dedicated deliberation, or silently narrow its scope mid-phase — both worse than naming the gap and resolving it first, per 147I §32 item 14's "no implementation-critical choice hidden" discipline. This phase is the narrowly scoped, human-authorized prerequisite-decision phase 147I itself recommended (147I §36).

This phase does not implement any of the following: a concrete `AuthorityRegistry`, a Decision Template resolution mechanism, any Session/readiness-package schema change, any orchestration component, or any contract amendment. It decides their architecture so that a future 147J can freeze it without inventing it.

---

## 3. Decision A — `claimed_identity` Ownership

### 3.1 Grounding

- **AEM-REQ-014** (`AUTHORITY_EVALUATION_MODEL_CONTRACT.md:355-363`): "The sole evidentiary input to evaluation is the claimed decision-maker identity already collected by IWC-001/IWPC-001 at `decision-session create` (`--owner-id`, IWPC-REQ-015; IWC-001's session-owner concept). This contract introduces no new evidence collection of any kind."
- **AEMIC-REQ-019**'s parameter table (`AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md:381`): `claimed_identity`'s source is "Already-collected `Session.owner_identity` (or an equivalent already-collected value a future caller supplies) — AEM-REQ-014; this package collects nothing."
- **IWC-REQ-036/037** (`INTERACTIVE_WORKFLOW_CONTRACT.md:1089-1093`): "A Decision Session SHALL be bound at creation to the identity of the human who created it," and "A resumption request from an identity other than the one bound at creation SHALL be rejected, fail closed." `Session.owner_identity` is therefore immutable for the session's lifetime, not merely "usually stable."
- **IWPC-001 §3 role definitions** (`INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md:176-186`) distinguish three identity roles across the pipeline: **decision maker** (`--owner-id` at creation), **confirmer** (at `decision-session confirm`), and **authorizing principal** (`--operator-id` at `governance-record publish`) — three distinct, independently-bound identities.
- **AEM-001 §D-6** (referenced in 147I and confirmed present in AEM-001's decision log) scopes evaluation to the decision-maker role only, not the confirmer or authorizing principal.
- `Session.owner_identity` is validated only for non-emptiness (`src/pcae/interactive_workflow/models/session.py:105-106`) and carries no other semantic constraint.

### 3.2 Candidate evaluation

| Candidate | Ownership | Replay | Persistence | Determinism | Auditability | Coupling | Security | Restart | Transaction span | Disclosure-only compatibility |
|---|---|---|---|---|---|---|---|---|---|---|
| **Session (Interactive Workflow)** | Already sole owner per IWC-REQ-036/037; contract-named source (AEM-REQ-014/AEMIC-REQ-019) | Trivial — immutable field, no recomputation needed | Already persisted, already restart-durable | Fixed at session creation, never recomputed | Session already audited via existing evidence/audit mechanisms | None added — reads an existing field, adds no new write path | Bound at creation, rejection on identity mismatch (IWC-REQ-037) already closes impersonation at resumption | Trivially restart-equivalent — a persisted field, not a computed one | N/A — no transaction, a read | Fully compatible — a read-only consumption of already-disclosed Session state |
| Readiness Package | Would require a new field; docstring (`publication_handoff/models.py:12-14`) explicitly forbids adding an authority-token field | N/A (new) | Would duplicate Session's own field | N/A | Duplicative audit surface | New coupling to Session at readiness-build time (already exists structurally, but for a new purpose) | No new risk beyond Session's, but a second copy is a second thing that can drift | Restart-durable, same as Session | N/A | Compatible, but redundant — same information, later copy |
| Publication Coordinator | Would violate PEC-REQ-116 (no independent judgment beyond `PublicationHandoff.build_package` verbatim conformance) if it re-derived identity itself | N/A | N/A | N/A | N/A | Couples Publication to an identity concept it does not currently need | High — Coordinator picking up a new identity-shaped responsibility it was never scoped for | N/A | Would risk pulling identity resolution inside the Coordinator's exactly-once transaction | At risk — closest component to where a gating temptation could form |
| Dedicated Authority Evaluation Service | Reads Session's field, does not own it | Trivial (reads, does not compute) | N/A — stateless read | Deterministic | Can log what it read | Minimal — one new read dependency on Session | No new risk — reads an already-immutable field | Trivially restart-equivalent | N/A | Fully compatible |
| New orchestration layer | Same as dedicated service, generic name for the same role | Same | Same | Same | Same | Same | Same | Same | Same | Same |

### 3.3 Determination

**Owner: `Session` (Interactive Workflow), via the existing `owner_identity` field, exactly as AEM-REQ-014/AEMIC-REQ-019 already name it.** No new Session field is introduced. `claimed_identity`'s *value* is `Session.owner_identity`, read (never re-derived, never independently collected) by whichever orchestration component performs evaluation (Decision D). This is not a new architectural decision so much as this phase's explicit **ratification** of what the frozen contract text already specifies — 147I's characterization of `owner_identity` as merely "a distinct, unverified analog" understated how directly AEM-REQ-014/AEMIC-REQ-019 already point at it. The Readiness Package, Publication Coordinator, and any new orchestration layer are all inferior because each would either duplicate Session's own field (redundant, a second source of drift), violate an existing prohibition (readiness package's own docstring; PEC-REQ-116's no-independent-judgment rule), or add no value the direct Session read does not already provide.

**Residual, explicitly non-blocking caveat:** "session owner" (who created/administers the session) and "authority claimant" (who is claiming eligibility under a Decision Template's governing rule) are conceptually distinct ideas that happen to be the same field today because AEM-001 chose to scope evaluation to the decision-maker role only (§D-6) and IWC-001 already treats the decision maker as the session's bound owner. If a future contract ever wanted evaluation to apply to the confirmer or authorizing-principal role instead of (or in addition to) the decision maker, that would be a new AEM-001 requirement, not a consequence of this decision. This phase does not open that question; it is explicitly out of scope, per §D-6 as already frozen.

---

## 4. Decision B — Decision Template Resolution

### 4.1 Grounding

- The Decision Template JSON Schema (`src/pcae/schema_resources/chgr/records/decision_template.schema.json`) defines `template_id`, `version`, `authoritative_basis`, `eligible_authority` (free text, ≤500 chars), `subject_binding_rule`, `options[]`, `supersession_rules`, `revocation_rules`, `status`.
- **The schema is not wholly unused**, correcting 147I's framing: it is validated as one of six known CHGR record-family shapes (`governance/verification.py:74`, `governance/inspection.py:56`), and the CLI's `pcae governance-record template-inspect` command validates a user-supplied file against it; `pcae governance-record verify <path> --related <path>`'s `template_resolution` check (`governance/verification.py:596-614`) structurally validates a caller-supplied related Decision Template document and checks `selected_option_id` against its `option_ids` — but only when the caller manually supplies `--related`; it is skipped, not failed, otherwise.
- **No code path automatically resolves `template_ref`/`template_version` to a Decision Template document.** `grep -n "decision_template\|eligible_authority" src/pcae/authority_evaluation/*.py` returns nothing — the package has zero awareness of Decision Templates.
- AEMIC-REQ-019's `citation_text` row (`AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md:385`): "Sourced by the caller, verbatim, from the Decision Template's own `eligible_authority` field ... never evaluated, interpreted, or verified by this package."
- `evaluate()` itself never performs I/O and never calls `AuthorityRegistry.resolve()` (AEMIC-REQ-076/077, reconfirmed unaffected by both the v1.1 and v1.2 repairs) — resolution, of any kind, is categorically a caller-side, pre-evaluation step, never inside the evaluator.
- 147I's own Registry analysis (147I §9) already identified that a schema-artifact Registry (Option C — resolving `EligibleAuthorityDeclaration` from a resolved Decision Template) "would also solve the `citation_text` sourcing problem in the same stroke" and that "these two questions ... may turn out to be the same underlying design decision" — this phase confirms and adopts that unification.

### 4.2 Candidate evaluation

| Candidate | Assessment |
|---|---|
| **Before evaluator** (a pre-evaluation resolution step, caller-side) | Required by AEMIC-REQ-076/077 — this is not one option among several, it is the only lawful placement class; the remaining question is *which* caller performs it |
| During evaluator | Forbidden — `evaluate()` is a pure function with no I/O; AEMIC-REQ-076/077 are structural, not a design preference this phase could override even if desired |
| Registry (folded into `AuthorityRegistry.resolve()`) | Attractive but narrower than needed alone — `resolve()`'s return type is `Optional[EligibleAuthorityDeclaration]`, which has no field for `eligible_authority`/citation text (§1.4 of research); Registry resolution alone supplies `declaration`, not `citation_text`. A single component can *perform both* (resolve the Decision Template once, derive both the Declaration and the citation from it), but the `AuthorityRegistry` ABC's own single-method shape should not be widened to also return citation text — that would break its "read-only, pure function of two inputs" contract-declared shape (AEM-001 §4.5) for a second, unrelated purpose |
| Workflow (Session/Interactive Workflow) | Same over-coupling and gating-confusion risk 147I already identified for Registry placement inside Interactive Workflow (147I §10) — Session's proximity to Confirmation makes accidental gating easier to introduce by accident, and Session already has enough responsibilities |
| Publication (Coordinator) | PEC-REQ-115/116 already forbid the Coordinator from performing any independent resolution or judgment beyond citing an already-resolved value verbatim — resolving a Decision Template *is* exactly the kind of independent, discretionary step PEC-REQ-116 forecloses |
| **Dedicated orchestration layer** | Cleanest fit — the same component identified in 147I §10/§11 Candidate A as the sole Registry caller can, without expanding its public contract, also be the sole Decision Template resolver, since both are pre-evaluation, caller-side, read-only lookups keyed by the same `(template_ref, template_version)` pair |

### 4.3 Preferred architecture

**A single, dedicated "Decision Template & Declaration Resolution" capability, owned by the same orchestration component identified in Decision D (§6), resolves a canonical Decision Template document once per evaluation attempt, using the existing schema-validation logic the CLI's `template-inspect`/`verify --related` commands already exercise (not new validation logic — reuse of the existing structural check), and derives from that single resolved document both:**
1. **`citation_text`** — the resolved document's own `eligible_authority` field, copied verbatim (never re-derived, never summarized).
2. **The `EligibleAuthorityDeclaration` the Registry's `resolve()` returns** — if the concrete Registry implementation is the schema-artifact-backed option (147I §9 Option C), this becomes the same read as (1); if a filesystem-backed Option B Registry is chosen instead, this remains a *separate* lookup against separate storage, and (1) and (2) may diverge in provenance even though they should never diverge in content for a well-formed template.

This directly answers the prompt's requirement that `template_ref`, `template_version`, and `citation_text` "remain canonical and singular": because both the Declaration and the citation are derived from **one resolved document**, read **once**, by **one component**, there is no path by which two independently-populated copies could silently drift — the single-copy-propagation discipline 147I's §13 flagged as a "necessary future contract rule" for `template_ref`/`template_version` extends naturally to `citation_text` under this design, provided the eventual concrete Registry implementation is the schema-artifact option (Option C) rather than a wholly separate filesystem Option B store. **This phase therefore recommends Option C (schema-artifact Registry) over Option B (independent filesystem-backed Registry) specifically because Option C is the only option that structurally guarantees this singularity without a separate consistency-check mechanism.** If Option C proves infeasible for reasons outside this phase's scope, Option B remains lawful but would additionally require an explicit cross-check between the Registry's declaration and the separately-resolved citation's template version — added complexity Option C avoids by construction.

---

## 5. Decision C — `evidence_kind` Compatibility

### 5.1 Grounding

Direct grep of all nine contracts and the `authority_evaluation` package:

| Source | Field | Type | Values | Enum closure |
|---|---|---|---|---|
| AEM-001 / AEMIC-001 / `pcae.authority_evaluation` | *(none exists)* | — | — | Concept entirely absent — zero occurrences |
| CHGR-001 (`identity.schema.json:22-44`) | `decision_maker_identity_evidence.evidence_kind` | JSON Schema string enum | `typed_confirmation_only`, `os_authenticated_user` | Closed, 2 values |
| IWC-001 / `Session.decision_maker_evidence_kind` | (field name differs slightly from CHGR's path but same value space) | Python `str`, validated | Same 2 values | Closed, 2 values, matches CHGR |
| IWPC-001 / PEC-001 (`decision_maker_identity_evidence["evidence_kind"]`) | dict key | str | Same 2 values | Closed via `_ASSURANCE_LEVEL_BY_EVIDENCE_KIND` lookup dict (`governance/publication/record.py:72-75`); unrecognized value refused, not guessed |
| `pcae.core.agent` (Phase 49D CLI evidence framework) | `evidence_kind` | str | `governance, runtime, validation, consensus, arbitration, provenance` | Closed, 6 values — unrelated domain (CLI evidence classification, not identity) |
| `pcae.cltr` (`EvidenceReference.evidence_kind`) | free-text | str | Unconstrained (e.g. `"test_suite"`) | Open — unrelated domain (CLTR migration evidence, not identity) |

AEM-001's own §5.1 answer to "What evidence establishes authority?" (`AUTHORITY_EVALUATION_MODEL_CONTRACT.md:353-365`) states the contract "introduces no new evidence collection of any kind" and names `claimed_identity` — not `evidence_kind` in any form — as the sole evidentiary input (AEM-REQ-014/015).

### 5.2 Compatibility determination

**Already aligns — but not because the concepts were reconciled; because they never intersect.** CHGR-001, IWC-001, and PEC-001/IWPC-001 share one consistent two-value `evidence_kind` concept (a confirmation-mechanism/identity-assurance label, mapped to CHGR's `L0`/`L1` `assurance_level`). AEM-001/AEMIC-001 define no `evidence_kind` concept whatsoever — not a differently-scoped one, an **absent** one. There is therefore no mapping to design, no future amendment required to reconcile a conflict, and no new abstraction needed, because there is no cross-contract disagreement to resolve. The two unrelated repository usages (the Phase 49D CLI evidence-classification framework and CLTR's free-text evidence field) are different domains entirely and are not candidates for this compatibility question — they were checked and explicitly excluded, not overlooked.

### 5.3 Compatibility matrix (per prompt requirement)

| Contract pair | Compatible? | Basis |
|---|---|---|
| AEMIC-001 ↔ AEM-001 | N/A (same absence, both define no `evidence_kind`) | Both scope evidentiary input to `claimed_identity` only (AEM-REQ-014) |
| AEMIC-001 ↔ IWPC-001 | Already aligns (no conflict — no shared field) | AEMIC-001 never references `evidence_kind`; IWPC-001 never references AEMIC's evaluator inputs |
| AEMIC-001 ↔ PEC-001 | Already aligns (no conflict — no shared field) | Same reasoning; PEC-001's `evidence_kind` usage is confined to `assurance_level` derivation (CHGR-REQ-200), unrelated to evaluation |
| AEMIC-001 ↔ CHGR-001 | Already aligns (no conflict — no shared field) | CHGR-001's `evidence_kind` feeds `assurance_level` only; `authority_basis_claimed` is populated from `citation_text` (Decision B), never from `evidence_kind` |

**No amendment is required or recommended by this phase.** If a future, separately governed AEM-001 revision ever wants evaluation outcomes to factor in identity-assurance level, that is new evaluator-input scope requiring its own AEM-REQ addition and its own AEM-REQ-003-style disclosure-only re-justification — not a "compatibility fix," because there is nothing currently incompatible to fix.

---

## 6. Decision D — Two-Stage Evaluation

### 6.1 Grounding

- **IWPC-001 §21 Concurrency Contract, IWPC-REQ-144** (`INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md:1407-1415`): "PEC-001's own `os.O_CREAT | os.O_EXCL` idempotency marker (`commit_publication`) already provides the one place in this entire chain with real mutual exclusion."
- **IWPC-REQ-141/143/147** (`:1381-1437`): everything upstream of that commit point (session store, pending-readiness store) is last-write-wins and explicitly disclosed as "not authority-relevant."
- **IWC-REQ-026** (`INTERACTIVE_WORKFLOW_CONTRACT.md:1054-1055`): "Reaching `Confirmed` SHALL NEVER, by itself, prove the human held eligible authority under the bound template" — IWC-001 itself already treats Confirmation as non-authoritative, consistent with an advisory-only evaluation at that stage.
- **PEC-REQ-115/116**: the Coordinator may only cite an already-verbatim value, never perform evaluation or independent judgment itself — placing any evaluation *inside* the Coordinator's own exactly-once transaction is foreclosed.
- **CHGR-REQ-097** (`CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md:1066-1068`): "Any gap between valid human action and eligibility under the applicable governing authority model SHALL be surfaced, never silently resolved in the record's favor."
- **AEM-REQ-003/037**: gating is forbidden at every stage named (Confirmation, Readiness construction, Authorization, Publication); this constrains *how* two-stage evaluation may be consumed, not whether it may exist.

### 6.2 Determinations

- **Necessity: Confirmed necessary.** The pipeline's own concurrency design (IWPC-REQ-144/147) already establishes that nothing before Publication's commit point is authority-relevant/stable — an evaluation performed once, early, and never refreshed would be evaluating against data the pipeline itself does not guarantee is still current by the time Publication occurs. This is now a contract-grounded conclusion, not only an architectural inference.
- **Timing:** Stage 1 (advisory) at or before Confirmation — consistent with IWC-REQ-026's own framing of Confirmation as non-authoritative, so an advisory-only evaluation at this point introduces no new authority claim the workflow doesn't already disclaim. Stage 2 (fresh, citation-binding) immediately before CHGR construction, performed by the dedicated orchestrator (never the Coordinator itself), consuming only its own output — never re-entering the Coordinator's `O_CREAT|O_EXCL` transaction.
- **Replay:** Since `evaluate()` is deterministic and side-effect-free, both stages are safely replayable from persisted inputs. A retried Publication attempt (per IWPC-001 §20's replay-protection classification) may legitimately trigger a fresh Stage 2 recomputation; this must be tolerated and disclosed as expected behavior, not treated as an error, mirroring 147I §16's restart-equivalence finding.
- **Persistence:** Stage 2's inputs and outcome are persisted together as an immutable artifact (per §8/§9); Stage 1 remains ephemeral/advisory Session or Preview state, not a governance artifact.
- **Stale declaration/template handling:** If the Registry's declaration or the resolved Decision Template's `eligible_authority` text changed between Stage 1 and Stage 2, Stage 2's result governs and the disagreement must be surfaced, never silently resolved — directly required by CHGR-REQ-097.
- **Registry updates:** Out of scope for this decision — governed by whatever concrete Registry write path a future Registry-implementation phase defines (§8). This phase only requires that Stage 2 always reads the Registry's *current* state at Stage 2 time, never a cached Stage 1 read.
- **Authority semantics:** Disclosure-only is preserved at both stages; neither stage's outcome may block, gate, suppress, or delay any pipeline step (AEM-REQ-003/037), including a disagreement between the two stages — disagreement is surfaced to the human, never converted into an automatic block.
- **Explicit determination — does Stage 2 always supersede Stage 1?** **Yes, unconditionally, for citation purposes.** Only Stage 2's outcome is ever cited into `authority_basis_claimed` (via PEC-REQ-115). Stage 1 exists solely to inform the human decision-maker earlier in the workflow; it is never itself a citation source and is never treated as equally authoritative to Stage 2, even if the two agree.

---

## 7. Decision Interaction Matrix

| | A depends on | B depends on | C depends on | D depends on |
|---|---|---|---|---|
| **A (claimed_identity)** | — | Independent | Independent | A's output (`claimed_identity` value) is a required input to every Stage 1/Stage 2 evaluation call |
| **B (Template resolution / Registry)** | Independent | — | Independent | B's output (`declaration`, `citation_text`) is a required input to every Stage 1/Stage 2 evaluation call; B also determines the orchestrator's identity, which D adopts |
| **C (evidence_kind)** | Independent | Independent | — | Independent — C's resolution (no compatibility issue) does not affect D's design at all |
| **D (Two-stage timing)** | Consumes A | Consumes B | Does not consume C | — |

**Dependency graph (textual):**

```
Decision C (evidence_kind) ──── resolved independently, no downstream dependency

Decision A (claimed_identity) ──┐
                                 ├──► Decision D (two-stage evaluation) ──► future 147J
Decision B (template/Registry) ─┘         (orchestrator identity also
     (foundational — also                  flows from B's resolution)
      determines orchestrator
      ownership)
```

**Foundational decision: Decision B.** Decision A is nearly cost-free to resolve (it ratifies an already-contract-named field). Decision C requires no design work at all (no incompatibility exists). Decision D cannot be designed concretely until both A and B supply their inputs, and D's orchestrator-ownership question is answered by whichever component B's resolution architecture designates as the resolver. Decision B is therefore the load-bearing decision of this phase: it is the only one of the four that both (a) required genuine architectural design rather than ratification or dissolution, and (b) determines a structural property (single-resolution-point, orchestrator identity) that the other three decisions build on or are constrained by.

---

## 8. Future Registry Architecture

This phase does not design the Registry itself. It states what a future, separately governed Registry-implementation phase must take as given:

- **Minimum required capability:** exactly the `AuthorityRegistry.resolve(template_ref, template_version) -> Optional[EligibleAuthorityDeclaration]` shape already frozen by AEM-001 §4.5 — no additional public method. Per Decision B, the concrete implementation should be the schema-artifact option (147I §9 Option C): resolving from the same canonical Decision Template document the citation-resolution step reads, not a wholly independent store.
- **Ownership:** the single dedicated orchestration component identified in Decision D is the Registry's sole caller — this closes the caller-fabricated-declaration threat 147I §28 already flagged, and requires no new access-control mechanism beyond "only one component imports the concrete Registry class."
- **Lifecycle:** read-mostly. Population is a governance-authoring act (whoever authors/versions Decision Templates), not a per-session or per-evaluation write. No write path is designed by this phase.
- **Persistence expectations:** filesystem-backed, following the house style both research passes independently confirmed already exists twice in this codebase — `src/pcae/cltr/persistence.py`'s content-addressed, atomic-write, digest-verified generation store with an atomically-rewritten `current` pointer, and `src/pcae/governance/publication/storage.py`'s `PublicationRecordStore` (write-once records, `O_CREAT|O_EXCL` idempotency markers). A future Registry implementation should follow this same pattern, not invent a new one.
- **Lookup semantics:** keyed by `(template_ref, template_version)`, no first-match-among-duplicates resolution (AEMIC-REQ-045's prohibition, reconfirmed unaffected by both v1.1/v1.2 repairs) — a filesystem store keyed by this pair can enforce uniqueness at write time.
- **Failure model:** `AuthorityRegistryUnavailableError` (storage could not be consulted) and `AuthorityRegistryCorruptError` (storage answered, but the record is malformed or duplicate) must remain distinguishable from each other and from `INDETERMINATE` (an ordinary, non-error `None` return) — AEM-001 §11.3 already warns against conflating an infrastructure failure with a legitimate "no declaration found" result.
- **Abstraction boundary:** the `AuthorityRegistry` ABC itself (one abstract method) is not widened by this phase and should not be widened by a future Registry phase either — citation-text resolution is a related but structurally separate concern that the orchestrator coordinates alongside, not through, `resolve()`.

**What remains entirely for a later Registry architecture phase:** the exact on-disk storage layout; the Decision Template authoring/versioning workflow (who writes templates, how `supersession_rules` is enforced); the concrete `AuthorityRegistry` subclass and its tests; the digest/provenance scheme for citation-provenance binding (147I §15); duplicate-detection write-time enforcement mechanics; and migration/versioning tooling for `DECLARATION_SCHEMA_VERSION` changes. None of this is decided here.

---

## 9. Input Ownership Matrix

| Evaluator input | Owner | Persistence | Validation | Replay | Future schema impact |
|---|---|---|---|---|---|
| `template_ref` | `Session` (originates), copied forward to `PublicationReadinessPackage` | Already persisted (Session + readiness package) | Session's existing non-emptiness validation | Trivial — stable field | None — already exists both places; 147I's explicit-equality-check requirement (147I §13) still applies |
| `template_version` | `Session` (originates), copied forward to `PublicationReadinessPackage` | Already persisted | Same | Trivial | None |
| `claimed_identity` | `Session.owner_identity` (Decision A) | Already persisted, already restart-durable | IWC-REQ-036/037's creation-time binding | Trivial — immutable per session | **None** — no new field, only an explicit read-path adoption |
| `declaration` | Registry (Decision B/§8), sole caller = dedicated orchestrator | New — Registry storage (§8), not yet built | `AuthorityRegistry.resolve()`'s own contract (pure, non-raising for the "no match" case) | Deterministic given fixed Registry content at read time | Registry storage schema — new, future phase |
| `evaluated_at` | Whichever stage's orchestrator step is executing (Decision D) | Only as part of the persisted evaluation artifact (§6.2) | ISO-8601 well-formedness (`EligibleAuthorityDeclaration.declared_at` precedent) | Trivial — recorded, not recomputed | None |
| `evaluator_version` | The `authority_evaluation` package itself (`EVALUATOR_VERSION` constant) | Persisted as part of the outcome | N/A — package-published constant | Trivial | None |
| `citation_text` | Decision Template resolution (Decision B), sole caller = dedicated orchestrator | New — persisted as part of the Stage 2 immutable evaluation artifact (§6.2) | `evaluate()`'s own `MissingCitationTextError` invariant; upstream, the resolved document's own schema validation | Deterministic given the resolved document's content at read time, which Stage 2 always re-reads fresh (Decision D) | Decision Template resolution mechanism — new, this phase's architecture; concrete code deferred |

Every input has exactly one owner, satisfying the prompt's requirement. Four of seven (`template_ref`, `template_version`, `evaluated_at`, `evaluator_version`) require no new schema or storage work at all. Two (`declaration`, `citation_text`) both resolve through the same Decision-B resolution point and both require new, but unified, storage (§8). One (`claimed_identity`) requires no new storage — only an explicit architectural read-path adoption of an existing field.

---

## 10. Candidate Integration Strategies

### A — Dedicated Authority Evaluation Service

A new, narrowly scoped component is the sole caller of `AuthorityRegistry.resolve()`, the sole performer of Decision Template resolution, and the sole invoker of `evaluate()` at both Stage 1 and Stage 2.

- **Coupling:** Lowest — one new component with a clean, single-purpose boundary; Session and the readiness package are read-only inputs to it, never the reverse.
- **Replay:** Strongest — designed for idempotent recomputation from the start, matching `evaluate()`'s own purity guarantee.
- **Determinism:** Preserved fully — no ambient state beyond what it explicitly reads (Session's `owner_identity`, the Registry, the resolved template).
- **Authority semantics:** Cleanest disclosure-only boundary — the service has no other responsibility to blur evaluation into, unlike Workflow (Confirmation proximity) or Publication (PEC-REQ-115/116 proximity).
- **Complexity:** Moderate — one new component, but it is genuinely new surface area (new service, new artifact store).
- **Schema impact:** Minimal and unified — only the new evaluation-artifact storage (§8/§9); no `src/pcae/interactive_workflow` or `governance/publication` schema is touched beyond an eventual reference field.
- **Restart:** Strong — independently restartable, independently testable, exactly as isolated as `pcae.authority_evaluation` itself already is.
- **Audit:** Strong — a single place to log every resolution and evaluation event.

### B — Workflow-Owned Orchestration

Interactive Workflow becomes the Registry caller and Decision Template resolver, embedding evaluation into Session transitions.

- **Coupling:** Moderate-high — Session already owns Confirmation, Evidence, Clarification, and Audit; adding Registry/template-resolution access widens its blast radius for no clear benefit.
- **Replay:** Tied to Session's existing persistence guarantees — workable, but not designed for this purpose.
- **Determinism:** Preserved, but the *evaluation trigger* becomes entangled with workflow transition logic, increasing the surface where a future change could accidentally introduce state-dependence.
- **Authority semantics:** At meaningful risk — proximity to Confirmation is exactly the gating-confusion risk 147I §10/§11 (Candidate B) and this phase's §3.2 both flag; a future maintainer extending Session's transition logic could accidentally condition a transition on the evaluation outcome without a dedicated architectural boundary preventing it.
- **Complexity:** Higher over-coupling risk for no offsetting architectural benefit.
- **Schema impact:** Largest — Session would need both new input-adjacent state and outcome storage.
- **Restart:** Session is already restart-durable, so this is workable, but conflates two independently-restartable concerns into one.
- **Audit:** Workflow's existing audit trail exists but is not scoped for evaluation-specific events; would need extension.

### C — Publication-Owned Orchestration

The Publication Coordinator becomes the Registry caller and evaluator invoker.

- **Coupling:** High — couples Publication's exactly-once transaction to Registry/template-resolution availability at the most time-pressured point in the pipeline.
- **Replay:** Complicated — Publication's exactly-once semantics (IWPC-REQ-144) make retrying an evaluation-inclusive transaction awkward; a failed evaluation inside a publish attempt would need to be distinguished from a failed publish itself.
- **Determinism:** Preserved in principle, but evaluation becoming part of the Coordinator's transaction risks blurring "evaluation completed" with "publication committed."
- **Authority semantics:** **Directly forbidden as currently scoped** — PEC-REQ-115/116 explicitly prohibit the Coordinator from performing independent evaluation or judgment; this strategy would require a PEC-001 amendment merely to become lawful, which this architecture-only phase cannot authorize and does not recommend.
- **Complexity:** Highest — conflates two concerns (publication commit, evaluation) inside one exactly-once boundary.
- **Schema impact:** High — would require a PEC-001 amendment.
- **Restart:** Restart-equivalence for the Coordinator's own transaction is already well-defined; adding evaluation to it risks weakening that guarantee's clarity.
- **Audit:** Coordinator's existing audit trail exists but was not scoped for evaluation, and PEC-001 already explicitly disclaims this responsibility (PEC-REQ-115).

### Selection

**Strategy A (Dedicated Authority Evaluation Service) is selected**, unambiguously. Strategy C is not merely a worse fit — it would require a contract amendment (PEC-001) this phase is expressly forbidden from making, and even a future phase authorized to amend PEC-001 would be trading away PEC-REQ-115/116's clean citation-only boundary for no architectural gain the dedicated service doesn't already provide more cleanly. Strategy B introduces meaningful over-coupling risk to Interactive Workflow for no corresponding benefit. This selection is consistent with, and further grounds, 147I §11 Candidate A / §29 Architecture A's own conclusion.

---

## 11. Preferred Direction

A single, dedicated Authority Evaluation Service (Decision-B-defined, Strategy-A-shaped) is:

- The sole caller of `AuthorityRegistry.resolve()` and the sole performer of Decision Template resolution (Decision B, §4.3), reading `template_ref`/`template_version` from Session and deriving both `declaration` and `citation_text` from one resolved document.
- The sole reader of `Session.owner_identity` as `claimed_identity` (Decision A, §3.3) — no new Session field, a read-path adoption only.
- The sole invoker of `evaluate()`, at two timing points (Decision D, §6.2): Stage 1 (advisory, at or before Confirmation) and Stage 2 (fresh, immediately before CHGR construction, outside the Publication Coordinator's own transaction), with Stage 2 always superseding Stage 1 for citation purposes.
- The producer of a standalone immutable evaluation artifact per stage (persisted only for Stage 2, per §6.2/§9), referenced — never embedded — by the readiness package, following this codebase's existing `{record_id, record_digest, record_family}` sibling-reference pattern.
- The upstream, citation-only source for CHGR's `authority_basis_claimed`, populated by the Publication Coordinator strictly per PEC-REQ-115's existing verbatim-citation mechanism — requiring no CHGR-001 amendment, since CHGR-REQ-207/208 (v1.2) already made the field schema-optional and already require a `limitations` disclosure when absent.
- Consistent with `evidence_kind` remaining entirely outside evaluation's scope (Decision C, §5) — this service never reads or produces an `evidence_kind` value of any kind.

This direction requires: (a) no `src/pcae/authority_evaluation/**` change (the standalone core stays exactly as verified in 147H), (b) no `Session` schema change, (c) no `PublicationReadinessPackage` schema change beyond an eventual reference field, (d) no `AuthorityRegistry` ABC change, (e) no CHGR-001, PEC-001, IWC-001, or IWPC-001 amendment for the citation-only integration path described here. It requires new code only: the dedicated service itself, its Decision-Template-resolution logic, its concrete (Option C) Registry implementation, and its own evaluation-artifact storage — all net-new components, not modifications of existing frozen contracts or their implementations.

---

## 12. Open Questions

Items not resolved by this phase, none of which blocks 147J from starting — each is 147J's own architecture-freeze work:

1. The exact shape and digest scheme of the standalone immutable evaluation artifact (147I §24), and its reference field name/placement on the readiness package.
2. The precise Decision-Template-resolution component's internal design: how it locates candidate template documents on disk, exact error translation for a missing/malformed template, and how it interacts with `supersession_rules`/`revocation_rules`.
3. The exact concrete `AuthorityRegistry` subclass design and its test strategy (deferred to a Registry-implementation phase per §8).
4. The precise Stage-1-vs-Stage-2 disagreement disclosure UX/mechanism (147I §29) — *that* Stage 2 always wins is decided (§6.2); *how* a human is shown a disagreement is not.
5. Whether `Session.owner_identity` should eventually be supplemented by a distinct `claimed_identity`-labeled field for clarity, even though this phase determined no new field is *required* (§3.3) — a naming-clarity question, not a blocking sourcing question.

None of these require further human-governance deliberation before 147J begins; they are ordinary architecture-phase design decisions 147J is authorized to make within the boundaries this phase has already fixed (Decisions A–D, the selected Strategy A, and the no-amendment constraint set).

---

## 13. Readiness Reassessment

147I's five listed prerequisites (147I §31), reassessed:

| # | 147I prerequisite | Status after this phase |
|---|---|---|
| 1 | Decision on `claimed_identity` sourcing | **Resolved** (§3.3) — `Session.owner_identity`, no new field |
| 2 | Decision on, and interface-level design for, Decision Template resolution | **Resolved** (§4.3) — single dedicated resolution capability, co-located with Registry resolution, Option C preferred |
| 3 | Decision on which concrete Registry option to build first | **Resolved at the architecture level** (§4.3/§8) — Option C (schema-artifact) preferred over Option B; concrete implementation itself correctly deferred to a future Registry-implementation phase, as 147I §9 already anticipated |
| 4 | Confirmation of `evidence_kind` compatibility | **Resolved** (§5) — no incompatibility exists; the concept does not intersect AEM-001/AEMIC-001 at all |
| 5 | Explicit human/governance sign-off on the two-stage model | **Substantively addressed, formally outstanding** — this phase, itself human-authorized, determines Architecture D's two-stage model as the preferred direction with contract-grounded reasoning (§6); the human authorization that opened this phase authorized *resolving* these prerequisites, which this document does, but does not by itself constitute a separate, later sign-off specifically on 147J's eventual freeze — that remains 147J's own normal phase-authorization step, exactly as every phase in this repository requires |

Four of five prerequisites are now resolved at the architecture level. The fifth is addressed by this phase's own determination but, like every phase in this repository, 147J will still require its own human authorization to begin — this is the ordinary governance gate every phase passes through, not a special additional blocker beyond what already applies uniformly.

---

## 14. No-Go Confirmation

No `src/pcae/**` file was modified. No production test was modified. No Registry was implemented. `.pcae/policy.toml` was not modified. No schema was modified. `Session` was not modified. Readiness packages were not modified. Interactive Workflow was not modified. Publication Coordinator was not modified. CHGR construction was not modified. No CLI was added. No runtime plugin was added. Execution was not enabled. AEM-001 was not amended. AEMIC-001 was not amended. IWC-001 was not amended. IWPC-001 was not amended. PEC-001 was not amended. CHGR-001 was not amended. TAMC-001 was not amended. TAMPC-001 was not amended. GAC-001 was not amended. No gate was introduced. No integration artifact was created. No orchestration service was built. Integration implementation was not begun. Confirmed by `git status --short` showing only this report and ordinary task/phase bookkeeping files as changed throughout this phase.

---

## 15. Overall Verdict

**INTEGRATION PREREQUISITES RESOLVED WITH OBSERVATIONS.**

All four architectural prerequisites named in the authorization (`claimed_identity` ownership, Decision Template resolution ownership, `evidence_kind` compatibility, two-stage evaluation model) are resolved at the architecture-decision level, each grounded in exact, cited contract text rather than inference. The "with observations" qualifier reflects §12's open items — none of which is a further prerequisite decision; each is ordinary architecture-phase design work that 147J itself is the correct venue to complete, and none reopens any of Decisions A–D.

---

## 16. Recommended Next Phase

**147J — Authority Evaluation Integration Architecture.** That phase shall define only the architecture for integrating the verified standalone Authority Evaluation Model into PCAE — orchestration ownership (Strategy A, a dedicated Authority Evaluation Service, per §10/§11), Registry interaction (the schema-artifact/Option-C-preferred boundary of §8), lifecycle boundaries (Decision D's two-stage timing, §6), persistence (the standalone immutable evaluation artifact of §9/§12 item 1), replay semantics (§6.2), schema impacts (§9's ownership table — minimal, no existing contract amendment required for the citation-only path this phase identified), and consumption rules (disclosure-only, citation-only at CHGR via PEC-REQ-115, per §5/§11). It shall remain architecture-only and must not implement integration or amend contracts.

This recommendation is not an authorization.
