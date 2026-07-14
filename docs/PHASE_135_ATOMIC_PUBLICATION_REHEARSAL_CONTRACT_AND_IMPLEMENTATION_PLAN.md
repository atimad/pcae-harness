# Phase 135Q — Atomic Publication Rehearsal Contract and Implementation Plan

**Phase classification:** architecture, contract freeze, implementation planning, Stage 2 readiness definition.
**Not:** Stage 2 implementation, combined-generation publication implementation, authoritative pointer publication, CLTR authority cutover, legacy demotion, legacy retirement, notification migration implementation, marker/receipt migration implementation, production finalization modification.

**Binding semantic authority:** CLTR-001 v1.0 (frozen, 135B; verified 135C, 135D, 135G).
**Production wire contract:** CLTR-SCHEMA-001 v1.0.1 (frozen 135I; amended 135J).
**Verified Stage 1 migration contract:** 135M (as repaired by 135N, F-135N-1).
**Verified Stage 1 implementation:** 135O, independently verified by 135P (VERIFIED WITH NON-BLOCKING FINDINGS; zero Blocking findings; commit `d2dbff1a`).

No production lifecycle behavior changes in this phase. This document freezes the contract and implementation plan for Stage 2 — Atomic Publication Rehearsal, Legacy Authority — the stage 135M named but explicitly declined to design in detail (135M §14/§15, §21 steps 10–18). It does not implement that plan.

---

## 1. Executive summary

Track 135 has, through 135P, frozen a semantic contract (CLTR-001 v1.0), a wire contract (CLTR-SCHEMA-001 v1.0.1), a verified six-stage migration contract (135M, repaired by 135N), and a verified Stage 1 implementation (135O, verified by 135P) that independently derives a CLTR record from the same shared, immutable transition-input package legacy uses, compares the two derivations, and persists migration evidence — all while legacy remains the sole production authority and CLTR remains derivative. Zero Blocking defects survive Stage 1; four Non-Blocking findings (F-135P-1 through F-135P-4) remain open and are dispositioned in §3.

135Q answers the question 135M deferred and 135P recommended addressing next: *what, precisely, is rehearsed at Stage 2, and what must be built, in what order, with what safety contract, before any candidate publication transaction may run?* This document freezes: a Stage 2 authority matrix; a rehearsal-generation identity; an isolated non-authoritative storage namespace; a complete candidate-artifact inventory with per-artifact contracts; a manifest and generation-digest contract; a deterministic assembly sequence; a precondition and mismatch policy; an atomic rehearsal-pointer contract; a crash matrix and recovery contract; idempotency, conflicting-replay, and quarantine contracts; a rollback-rehearsal and roll-forward contract; a split-brain-prevention contract; behavior across all four production entry points and all recovery paths; an explicit 135H.1-escape-resistance proof; a feature-configuration and invalid-configuration matrix; a security/containment and no-execution boundary; a planned package structure, integration points, test plan, fault-injection plan, and acceptance criteria; and a full inherited-finding and risk register.

135Q dispositions all four open 135P Non-Blocking findings explicitly (§3), and re-surfaces the still-relevant 135N and 135J findings that bear on Stage 2 (§54).

**Conclusion:** This document freezes a complete, internally consistent Stage 2 contract and implementation plan with zero unresolved Blocking gaps for the planning phase itself. It recommends **135R — Atomic Publication Rehearsal Contract Verification** as the next phase, which must independently re-derive and verify this contract before any Stage 2 implementation begins (§59/§60). No Stage 2 implementation occurred in 135Q.

---

## 2. Current verified starting state

Confirmed by direct inspection at the start of 135Q (read-only governance commands, no mutation):

- Repository clean; `origin/main..HEAD` = 0; nothing to push.
- `pcae health`: healthy. `pcae check`: passed. `pcae doctor task-memory`: clean.
- `pcae runtime inspect`: runtime state Observed, maximum capability observe, execution capability unavailable, registry empty, 0 plugins, governance posture non-executing.
- `pcae notify status`: Telegram configured, enabled, outbound-only; auto-finalization hook available.
- `pcae phase-report show --latest`: 135P canonical report present, consistent, recommends 135Q next.
- `pcae phase-report reconcile --phase-id 135P` (read-only): reconciled; promoted generations 1; marker already_dispatched; checkpoint completed; receipt finalized; mutation none.
- Authoritative 135P commit: `d2dbff1a`. Stage 1 dual derivation remains legacy-authoritative. `production_authority` is hardcoded `LEGACY` throughout `src/pcae/cltr/migration/`; no code path resolves to `CLTR`.
- Binding contracts unchanged: CLTR-001 v1.0, CLTR-SCHEMA-001 v1.0.1, PFN-001, PFR-001, the verified 135M/135N migration contract, and the 135P-verified Stage 1 implementation.

135P's inherited evidence (not rerun in 135Q, cited as evidence of record): 101/101 combined migration tests, 386/386 combined CLTR tests, 117/117 affected finalization regressions, 4391/4391 Fast Green, zero Blocking findings.

---

## 3. Exact 135P finding dispositions

All four 135P Non-Blocking findings, located directly in `docs/PHASE_135_SHARED_TRANSITION_INPUT_AND_DUAL_DERIVATION_INDEPENDENT_VERIFICATION.md` and cross-checked against current source.

### F-135P-1 — Two entry points fall back to generic recovery classification

- **Description:** `phase_report_create` and `notify_send_report` are absent from `_ENTRY_POINT_RECOVERY_CLASSIFICATION` (`finalization_transaction.py:986-989`) and silently fall back to `ordinary_finalization` instead of `REPORT_CREATE_RECOVERY`/`MANUAL_RECOVERY`.
- **Affected Stage 1 component:** `src/pcae/core/finalization_transaction.py`, entry-point wiring consumed by `src/pcae/cltr/migration/assembly.py`'s recovery-classification field.
- **Relevance to Stage 2:** High. §36 requires all four entry points to share one rehearsal coordinator with no entry-point-specific publication semantics; §37/§39 (ordinary/recovery-path behavior, four-entry-point behavior) and §22 (mismatch policy) depend on recovery classification being truthful, since Stage 2's candidate-preparation sequence (§20) consumes the same shared input the classification lives on.
- **Atomicity relevance:** Low directly — the field is descriptive evidence, not a control input to the atomic-replace mechanism.
- **Split-brain relevance:** Moderate — an untruthful recovery classification could, in principle, let a rehearsal generation record itself as "ordinary" when it was actually a recovery attempt, weakening §35's split-brain detection if recovery-path detection is ever used as a gating signal.
- **Recovery relevance:** High — §24/§27 rehearsal recovery and quarantine states are keyed partly by recovery classification for evidence-truthfulness purposes.
- **Exactly-once relevance:** Low — exactly-once identity (§25) is keyed on `transition_id`, not recovery classification.
- **Required resolution before Stage 2 implementation:** Yes. Must be repaired (or explicitly re-scoped as non-gating) before Stage 2 implementation begins, because Stage 2's §36/§39 four-entry-point/recovery-path guarantees would otherwise rest on an untruthful classification field.
- **Required resolution before authority cutover (Stage 3):** Yes, must remain resolved.
- **Planned phase:** A small, focused hardening phase before or during 135R's contract verification (135R may re-derive this as an explicit Stage 2 implementation prerequisite, not a Stage 2 contract gap — 135Q's contract does not require the fix to be already applied, only disclosed and scheduled).
- **Acceptance evidence:** A regression test asserting `phase_report_create` and `notify_send_report` map to their dedicated classifications, plus confirmation that no currently-passing Stage 1 test depended on the incorrect fallback.
- **Classification:** must resolve before Stage 2 implementation.

### F-135P-2 — Two comparison-result classes are declared but unreachable

- **Description:** `TEMPORAL_ORDER_MISMATCH` and `EXPECTED_REPRESENTATION_DIFFERENCE` are declared `ComparisonResultClass` wire identifiers in `src/pcae/cltr/migration/comparison.py` with no field-comparison logic capable of ever producing them, undisclosed as unreachable.
- **Affected Stage 1 component:** `src/pcae/cltr/migration/comparison.py`.
- **Relevance to Stage 2:** High. §22 (mismatch policy) and §32/§28 (rehearsal comparison, progression eligibility) both extend the Stage 1 comparison-result vocabulary; an unreachable class silently absent from real comparisons could mask an actual future rehearsal-specific mismatch (e.g. expected differences between a report candidate and the authoritative report, per §28) if the implementation mistakenly assumes the class already has logic.
- **Atomicity relevance:** None directly.
- **Split-brain relevance:** Low.
- **Recovery relevance:** Low.
- **Exactly-once relevance:** None.
- **Required resolution before Stage 2 implementation:** Partial — `EXPECTED_REPRESENTATION_DIFFERENCE` becomes directly load-bearing for Stage 2 (§28 requires classifying comparisons that cannot match because an external effect has not occurred as "expected rehearsal differences," which is exactly this class). It must be wired with real logic, or Stage 2 must define its own distinct rehearsal-scoped enum value and leave the Stage 1 class formally retired/disclosed-unreachable. `TEMPORAL_ORDER_MISMATCH` is not required by Stage 2's contract areas and may remain unreachable through Stage 2, disclosed as such.
- **Required resolution before authority cutover:** `EXPECTED_REPRESENTATION_DIFFERENCE` (or its Stage 2 successor) must be reachable and tested by Stage 3. `TEMPORAL_ORDER_MISMATCH` should be resolved or formally retired no later than Stage 3 contract freeze (135S).
- **Planned phase:** Stage 2 implementation phase (successor to 135R) wires `EXPECTED_REPRESENTATION_DIFFERENCE` or defines a rehearsal-scoped equivalent; disposition of `TEMPORAL_ORDER_MISMATCH` deferred to 135S.
- **Acceptance evidence:** A rehearsal-comparison test exercising an artifact expected to differ solely because of unoccurred external effects (e.g. notification-intent candidate vs. authoritative notification result) and asserting it classifies as an expected difference, not a fabricated match or an unclassified mismatch.
- **Classification:** may remain during Stage 2 rehearsal for `TEMPORAL_ORDER_MISMATCH`; must resolve before Stage 2 implementation for `EXPECTED_REPRESENTATION_DIFFERENCE`'s Stage-2-facing successor.

### F-135P-3 — `derive_cltr` would crash on non-empty commit ownership

- **Description:** `derive_cltr` (`cltr_derivation.py:123`) forwards the shared input's raw `phase_commit_ownership` tuple of bare commit-hash strings directly into `ProductionCltrRecord.phase_commit_ownership`, typed `tuple[CommitOwnershipEntry, ...]`. The `CLTR-COMMIT-2` invariant evaluator dereferences `.certification_state` and raises `AttributeError` for any non-empty value. Dormant today only because the sole production call site (`finalization_transaction.py:1014`) hardcodes `phase_commit_ownership=()`.
- **Affected Stage 1 components:** `src/pcae/cltr/migration/cltr_derivation.py`, `src/pcae/cltr/invariants.py`.
- **Relevance to Stage 2:** Critical. §9/§16 require the candidate artifact inventory to include a commit-attribution representation, and §54's cross-reference notes CLTR-001's `phase_commit_ownership` binding is required content (§6.2). If Stage 2 candidate assembly ever passes a non-empty commit-ownership tuple (which becomes more likely as Stage 2 exercises real finalization paths more completely per §36–39), the crash becomes live rather than dormant.
- **Atomicity relevance:** High — an uncaught `AttributeError` mid-derivation, before any artifact write, must not corrupt or partially publish a rehearsal generation. §17 preconditions and §23 crash matrix must treat this as a possible failure at the "derive CLTR record" step.
- **Split-brain relevance:** Low directly, but an uncaught crash during derivation that left a half-written candidate directory could contribute to split-brain risk if not contained by §4/§17.
- **Recovery relevance:** High — must be a modeled candidate-incomplete state (§24), not an unhandled exception escaping the coordinator.
- **Exactly-once relevance:** Moderate — a crash must not consume the idempotency key (§25); a retried rehearsal request with the same transition ID must be able to proceed once the underlying defect is fixed or the offending input is quarantined (§27).
- **Required resolution before Stage 2 implementation:** Yes, must be fixed (either `derive_cltr` normalizes raw commit-hash strings into `CommitOwnershipEntry` values, or the shared input is required to already carry typed entries) before any Stage 2 candidate-assembly code path exercises non-empty commit ownership.
- **Required resolution before authority cutover:** Yes, must remain fixed and covered by regression tests.
- **Planned phase:** Stage 2 implementation phase; fix should land alongside the commit-attribution candidate representation (§9), with a regression test using a non-empty commit-ownership tuple.
- **Acceptance evidence:** A test deriving a CLTR record from a shared input with at least one non-empty `phase_commit_ownership` entry, asserting successful derivation and correct `CLTR-COMMIT-2` evaluation (not a crash).
- **Classification:** must resolve before Stage 2 implementation.

### F-135P-4 — `NON_AUTHORITY_DISCLOSURE` hardcoded five times

- **Description:** The `NON_AUTHORITY_DISCLOSURE` dict is independently hardcoded five times (`evidence.py`, `coordinator.py`, `persistence.py`, `status.py`, `reconciliation.py`) with no shared source of truth, creating drift risk for future editors.
- **Affected Stage 1 components:** all five modules listed.
- **Relevance to Stage 2:** High — §6 (Stage 2 authority matrix), §5 (candidate vs. authoritative terminology), and every candidate contract (§9–§16) require a consistent non-authority disclosure string/structure on every rehearsal artifact and evidence record (§30). Stage 2 will add at least six more modules that need the same disclosure (report, metadata, Architecture Status, checkpoint, notification, marker, receipt candidates, manifest, evidence record) — hardcoding it a sixth through sixteenth time compounds the drift risk rather than resolving it.
- **Atomicity relevance:** None.
- **Split-brain relevance:** Low — a drifted disclosure string does not itself cause a split-brain condition, but it could mask one if two representations disagree about their own non-authoritative status due to independent edits.
- **Recovery relevance:** None.
- **Exactly-once relevance:** None.
- **Required resolution before Stage 2 implementation:** Yes — Stage 2 implementation must introduce one shared constant (e.g. `src/pcae/cltr/migration/rehearsal/disclosure.py` or a promotion of the existing Stage 1 constant to a common module imported by both Stage 1 and Stage 2 code) rather than hardcoding an eleventh–sixteenth copy. This is a hygiene prerequisite, not a semantic gap, but it must be resolved before Stage 2 implementation to avoid compounding the finding.
- **Required resolution before authority cutover:** Yes, must remain a single source of truth.
- **Planned phase:** Stage 2 implementation phase, first commit (introduces the shared constant before any candidate module is written).
- **Acceptance evidence:** `grep -r "NON_AUTHORITY_DISCLOSURE\s*=" src/pcae/cltr/` shows exactly one definition; all consumers import it.
- **Classification:** must resolve before Stage 2 implementation.

**Summary:** F-135P-1, F-135P-3, and F-135P-4 must resolve before Stage 2 implementation begins (none are Blocking for 135Q's contract-freeze itself, since 135Q performs no implementation). F-135P-2 is split: its `EXPECTED_REPRESENTATION_DIFFERENCE` half must resolve before Stage 2 implementation; its `TEMPORAL_ORDER_MISMATCH` half may remain unreachable through Stage 2, disclosed as such, and must resolve or be formally retired no later than 135S. None of the four findings weakens single-authority, exactly-once, or no-execution guarantees, and none is reclassified as Blocking for 135Q's own contract-freeze scope; all four are reclassified as **Blocking prerequisites for Stage 2 implementation** (not for 135Q, not for continued Stage 1 operation).

---

## 4. Stage 2 definition

Per 135M §6, Stage 2 is **Dual Publication Rehearsal** (this document's operative name: **Atomic Publication Rehearsal, Legacy Authority**). Legacy remains exclusively authoritative throughout Stage 2. 135Q freezes exactly what Stage 2 rehearses and what it explicitly does not.

**Rehearsed:**

1. Complete candidate-generation assembly — deriving every representation CLTR-SCHEMA-001 §5 names, from one immutable shared transition-input package, into an isolated candidate directory.
2. Deterministic artifact derivation — legacy-normalized and CLTR-derived views of the same input, per representation kind's comparison mode (CLTR-SCHEMA-001 §21.4).
3. Manifest construction — a rehearsal manifest binding every candidate artifact, its digest, and generation-level metadata (§18).
4. Digest verification — per-artifact and generation-level SHA-256 verification before any artifact becomes visible (§16, CLTR-SCHEMA-001 §15).
5. Local failure handling — precondition, mismatch, crash, and quarantine policy for the local candidate-assembly and pointer-publication path only (§18–§27).
6. Rehearsal pointer publication — one atomic, non-authoritative pointer replacement pointing at a fully verified rehearsal generation (§20–§21).
7. Read-only post-publication verification — status and reconciliation commands planned (not implemented) in §31/§32.
8. Reconciliation — comparing the rehearsal generation against the authoritative legacy result that actually governed the transition (§28).
9. Rollback rehearsal — rehearsing pointer rollback to a prior verified rehearsal generation, without touching production (§33).

**Not rehearsed:**

- Authoritative production pointer replacement.
- External notification dispatch (Telegram or any sink).
- Production marker creation.
- Production receipt finalization.
- CLTR lifecycle authority.
- Legacy demotion.
- Legacy retirement.

This mirrors 135M §21's framing precisely: steps 1–9 of the candidate-preparation sequence apply from Stage 1 onward; steps 10–18 in fully atomic, joint-generation form apply only from Stage 2 onward, and "only at Stage 2 does 'one candidate publication transaction' begin to jointly include both legacy and CLTR artifacts" — but the transaction's *authoritative outcome* remains whatever legacy already determined before Stage 2's candidate assembly even begins. Stage 2 proves the publication mechanism; it does not prove, and must not be read as proving, CLTR's fitness to govern that mechanism (135M §6, Stage 2 row).

---

## 5. Stage 2 authority matrix

| Representation | Stage 0–2 authority | Stage 2 rehearsal role | Authoritative today? |
|---|---|---|---|
| Legacy canonical phase report | Legacy (S per CLTR-001 role model, R in CLTR-SCHEMA-001 §5) | Compared against by report candidate | Yes |
| Legacy completion metadata | Legacy (R) | Compared against by metadata candidate | Yes |
| Legacy Architecture Status | Legacy (D, generated from legacy) | Compared against by Architecture Status candidate | Yes |
| Legacy checkpoint | Legacy (E) | Compared against by checkpoint candidate | Yes |
| Legacy marker | Legacy (D) | Compared against by marker candidate | Yes |
| Legacy receipt | Legacy (E) | Compared against by receipt candidate | Yes |
| Legacy notification dispatch | Legacy (R+E) | Compared against by notification-intent candidate (no dispatch) | Yes |
| CLTR record (Stage 1 dual-derived) | Non-authoritative (D, migration evidence) | Included in candidate generation, unchanged role | No |
| Rehearsal generation (new, Stage 2) | Non-authoritative | The subject being rehearsed | No — explicitly never |
| Rehearsal pointer (new, Stage 2) | Non-authoritative | Points at latest verified rehearsal generation | No — explicitly never |
| Migration evidence (Stage 1 + Stage 2) | Evidence only (E) | Consumed as precondition input, extended with rehearsal evidence | No |

Every row confirms: legacy remains the sole production authority; the rehearsal generation and rehearsal pointer are non-authoritative by construction (never merely by policy); migration status (including a fully successful rehearsal) cannot establish lifecycle truth; comparison results cannot overrule production; and no rehearsal artifact may be consumed as authoritative input by ordinary production recovery (`pcae phase-report reconcile`, `pcae task finish` state resolution, etc. — all of which read only legacy/`current` production pointers, never the rehearsal namespace defined in §7).

---

## 6. Rehearsal generation identity

One stable rehearsal-generation identity, `rehearsal_generation_id`, is required per finalized rehearsal generation. It is a deterministic composite, computed (not randomly generated, not timestamp-only) from:

- `migration_epoch` (135M §17; carried unchanged from the Stage 1 shared-input package).
- `authority_epoch` (135M §40; identifies the legacy-authoritative segment in force).
- `transition_id` (design-B, 135N/135O; the same UUID4 Stage 1 already assigned to this transition — a rehearsal generation never mints its own transition identity).
- `shared_input_package_id` (the Stage 1 `SharedTransitionInputPackage`'s own identity, both `PRE_TRANSACTION` and `LEGACY_COMPLETION` stages bound).
- `final_input_revision_digest` (SHA-256 of the fully-enriched, post-`LEGACY_COMPLETION` shared input package — the last point at which the input is guaranteed complete and immutable).
- `phase_id` (permanently separate, per CLTR-001 §5.1 and 135N's design-B resolution).
- `task_id`, where applicable (may be absent for phase-scoped entry points).
- `schema_versions` (CLTR-SCHEMA-001 version and rehearsal-manifest schema version, §18).
- `rehearsal_stage` (a fixed literal, `"stage_2_atomic_publication_rehearsal"`, distinguishing it from any future Stage 3+ generation identity scheme).
- `production_authority_disclosure` (fixed literal `"legacy"` for the entire lifetime of Stage 2 — never varies within Stage 2).

`rehearsal_generation_id = sha256(canonical_json({migration_epoch, authority_epoch, transition_id, shared_input_package_id, final_input_revision_digest, phase_id, task_id, schema_versions, rehearsal_stage, production_authority_disclosure}))`, using CLTR-SCHEMA-001 §14's canonical serialization rules (sorted keys, NFC-normalized strings, compact JSON). This makes the identity retry-safe: re-running rehearsal candidate assembly against the same, unchanged shared input reproduces the same `rehearsal_generation_id`; any change to a bound field produces a different identity, which §26 (conflicting replay) governs.

---

## 7. Rehearsal namespace

Following the existing convention (`.pcae/cltr-shadow/` for Stage 0, `.pcae/cltr-migration/` for Stage 1 evidence — 135P §40 confirms these are separate root namespaces preventing duplicate-record presentation), Stage 2 freezes a third, equally separate root:

```
.pcae/cltr-migration/
  epochs/
    <migration-epoch>/
      transitions/                      # existing Stage 1 evidence (unchanged)
        <transition-id>/...
      rehearsals/                       # new, Stage 2 only
        <transition-id>/
          candidates/
            <rehearsal-generation-id>/  # in-progress candidate, pre-finalization
              cltr_record.json
              report_candidate.json
              metadata_candidate.json
              architecture_status_candidate.json
              checkpoint_candidate.json
              notification_intent_candidate.json
              marker_candidate.json
              receipt_candidate.json
              commit_attribution_candidate.json
              repository_transition_candidate.json
              manifest.json
          generations/
            <rehearsal-generation-id>/  # finalized, immutable rehearsal generation
              ... (same file set, immutable after finalization)
          failures/
            <rehearsal-generation-id>-<attempt>/
              failure_record.json
          quarantine/
            <rehearsal-generation-id>/
              quarantine_record.json
          current-rehearsal              # atomic, non-authoritative pointer file
  status/
    current-evidence                     # existing Stage 1 pointer (unchanged)
    current-rehearsal-evidence           # new Stage 2 evidence pointer
```

Requirements, all normative:

- Nested under the existing `.pcae/cltr-migration/` root (`DEFAULT_MIGRATION_ROOT`), not a new top-level directory — repository-contained, matching Stage 1's precedent.
- `rehearsals/` is a sibling of `transitions/` under the same `<migration-epoch>`, never nested inside it, so no rehearsal artifact can be mistaken for Stage 1 migration evidence by path alone.
- Separate from `.pcae/cltr-shadow/` (Stage 0) and from any future production `current`/`generations` pointer layout.
- Separate from promoted `.pcae/phase-reports/` (legacy authoritative reports).
- `generations/<id>/` is immutable once written (finalize via the same `os.replace`-based rename Stage 1's `persistence.py:137-233` already uses — no in-place mutation after finalization).
- No symlink escape: every path component is validated against an allow-listed character set (matching `transition_id`/`rehearsal_generation_id` hex/UUID shape) before being joined to the root; no path segment may contain `..`, and the constructed path must resolve (via `Path.resolve()`) to a descendant of the root before any write.
- No path traversal: identical validation applied to `migration_epoch`, `phase_id`, and `task_id` path segments, all of which are attacker-adjacent only in the sense that they originate from configuration/environment, never from unsanitized external input — validated anyway, fail-closed on any invalid character.
- No historical rewrite: `generations/` and `failures/` are append-only; only `current-rehearsal` may be atomically replaced, and its prior valid target is never deleted (superseded generations remain on disk as evidence until an explicit, separately-governed retention phase, mirroring `pcae runtime snapshot retention --dry-run`'s advisory-only precedent).

---

## 8. Candidate versus authoritative artifact terminology

Frozen vocabulary, used consistently across every Stage 2 contract area:

- **Production authoritative artifact** — a legacy-produced representation currently governing lifecycle truth (the canonical report, completion metadata, Architecture Status, checkpoint, marker, receipt, or notification result actually written by the existing production path). Lives under existing production paths (`.pcae/phase-reports/`, etc.), never under `.pcae/cltr-migration/epochs/*/rehearsals/`.
- **Rehearsal candidate artifact** — any artifact written under `rehearsals/<transition-id>/candidates/` or, once finalized, `rehearsals/<transition-id>/generations/`. Always non-authoritative. Every candidate artifact's own JSON body carries a `non_authority_disclosure` field (§4 F-135P-4's shared constant) making this true even if the artifact is copied out of its namespace.
- **Copied evidence artifact** — a byte-identical copy of a production authoritative artifact, embedded in a rehearsal generation purely as comparison input (e.g. the copy of the authoritative report used in §11's comparison). Tagged `artifact_role: "copied_evidence"`; never re-derived, never re-serialized, digest must match the original's digest exactly.
- **Normalized legacy representation** — a re-derivation of a legacy artifact through the same `legacy_derivation.py`-style pure normalization Stage 1 already performs, used to make legacy output comparable to a CLTR-derived candidate under CLTR-SCHEMA-001 §21.4's `normalized_semantic` comparison mode. Tagged `artifact_role: "normalized_legacy"`.
- **CLTR-derived representation** — a candidate built via the CLTR derivation path (extending `cltr_derivation.py`). Tagged `artifact_role: "cltr_derived"`.
- **External-effect intent** — a durable record of what an external effect *would* contain if dispatched (notification-intent candidate, §14), explicitly marked `dispatch_attempted: false` and never confused with a dispatch confirmation.
- **Unverifiable artifact** — a candidate whose derivation inputs were incomplete (mirroring Stage 1's `unverifiable` adapter outcome, F-135L-2) — tagged `verification_status: "unverifiable"`, excluded from digest-backed comparison, never silently treated as a pass.
- **Projected artifact** — a candidate for a representation that has no independent identity of its own in production (Architecture Status, per CLTR-SCHEMA-001 §5's "D, no own identity" role) — tagged `artifact_role: "projected"`, always non-authoritative, always derived deterministically from already-bound identities, never assigned a new identity of its own.

No rehearsal artifact identifier or path may reuse a production identifier's namespace, format signature that implies production authority, or shared prefix with `.pcae/phase-reports/latest`, `.pcae/cltr-shadow/current`, or any production `current` pointer file name. Rehearsal identifiers are always prefixed or namespaced under `rehearsal_generation_id`/`rehearsals/`.

---

## 9. Complete candidate artifact inventory

One candidate generation contains, at minimum, all of the following (mapping directly to CLTR-SCHEMA-001 §5's 15 representation kinds plus rehearsal-specific additions):

| # | Artifact | Source kind (§8 terminology) | CLTR-SCHEMA-001 §5 role |
|---|---|---|---|
| 1 | Canonical CLTR record | CLTR-derived | R (record-bound) |
| 2 | Canonical phase report candidate | CLTR-derived, compared against copied evidence | R |
| 3 | Completion metadata candidate | CLTR-derived | R |
| 4 | Architecture Status projection candidate | Projected | D, no own identity |
| 5 | Checkpoint candidate | CLTR-derived | E |
| 6 | Notification-intent candidate | External-effect intent | R+E (intent only) |
| 7 | Marker-state candidate | CLTR-derived | D |
| 8 | Receipt-state candidate | CLTR-derived | E |
| 9 | Commit-attribution representation | Normalized legacy / CLTR-derived (fixes F-135P-3) | bound to CLTR-001 §6.2 `phase_commit_ownership` |
| 10 | Repository-transition representation | Observational (V) | V |
| 11 | Git attribution view | Observational (V) | V |
| 12 | Compatibility/legacy-format view | CLTR-derived, optional | D, optional |
| 13 | Diagnostic envelope | CLTR-derived, optional | D |
| 14 | Reconciliation view | Observational (V) | V |
| 15 | Shared transition-input package references | Copied evidence (reference only, not re-embedded) | n/a — Stage 1 artifact, referenced by ID + digest |
| 16 | Migration evidence (Stage 1) | Copied evidence (reference only) | E |
| 17 | Comparison results | CLTR-derived (Stage 2 rehearsal comparison, §28) | n/a |
| 18 | Manifest | CLTR-derived | n/a |
| 19 | Per-artifact digests | Computed | n/a |
| 20 | Generation digest | Computed | n/a |
| 21 | Migration epoch / authority epoch | Copied from shared input | n/a |
| 22 | Limitations | CLTR-derived | n/a |
| 23 | Non-authority disclosure | Constant (§4 F-135P-4 fix) | n/a |

Items 15–16 are **references** (identity + digest), never re-embedded copies, so a rehearsal generation can never drift from the Stage 1 evidence it was built on without the reference digest failing verification.

---

## 10. Report candidate contract

- Derived from the same shared transition-input package (§6) as the CLTR record; bound to the same `transition_id`.
- Preserves PFR-001's 13 mandatory sections structurally — the candidate is a structurally complete canonical-report-shaped document, since PFR-001 governs content, not which system produced it.
- Preserves report identity semantics (CLTR-001 §5.1: `report_id` once-bound, immutable, transition-scoped) — the candidate's own `report_id` is distinct from, and never equal to, the authoritative report's `report_id`; it is a rehearsal-scoped identity (§6's `rehearsal_generation_id` bound into it).
- Preserves report digest semantics (CLTR-SCHEMA-001 §15) — computed the same way, over the candidate's own content.
- Deterministic wherever PFR-001 permits (PFR-001 governs section presence/disjointness, not exact prose — the candidate's structured/quantitative fields, e.g. test counts and governance results, must be byte-reproducible from the same input; free-text narrative sections are exempt from bit-for-bit determinism, consistent with PFR-001 §3/§4's content-not-formatting scope).
- Remains non-authoritative: never written to `.pcae/phase-reports/`, never referenced by `pcae phase-report show --latest`.
- Does not trigger Telegram (§14 external-effects boundary).
- Discloses rehearsal status via the shared `non_authority_disclosure` field and an explicit `report_role: "rehearsal_candidate"` field absent from any authoritative report schema.
- Comparison against the actual authoritative report (§28): `exact_identity_digest` comparison mode is not directly applicable (identities differ by design), so comparison is field-wise on content after excluding identity fields — mismatches in quantitative/structural content are `authority_relevant_mismatch` candidates (blocking, §22); mismatches attributable solely to identity-field differences are expected and excluded from mismatch classification entirely (not even "expected difference" — they are structurally guaranteed to differ and are excluded from comparison scope, not merely tolerated).

---

## 11. Completion metadata candidate contract

- **Candidate identity:** its own metadata identity distinct from the authoritative `metadata_id`, bound to `rehearsal_generation_id`.
- **Field mapping:** one-to-one with the authoritative completion-metadata schema fields, sourced from the shared transition-input package's `LEGACY_COMPLETION`-stage fields plus the CLTR-derived record.
- **Phase binding:** `phase_id`, unchanged, always present (CLTR-001 §5.1).
- **Transition binding:** `transition_id`, identical to the transition this rehearsal is for (never independently generated).
- **Report digest binding:** binds the report candidate's digest (§10), never the authoritative report's digest, unless used explicitly as copied-evidence comparison input.
- **Generation binding:** binds `rehearsal_generation_id`.
- **Absent/null semantics:** any field the shared input package could not populate (e.g. a field only known after an external effect, such as confirmed notification delivery) is explicitly `null` with a `reason: "external_effect_not_occurred"` marker — never fabricated, never silently omitted (mirrors PFN-001 §4's "silent omission prohibited" principle, applied to candidate data rather than notification).
- **Comparison with authoritative metadata:** same field-wise approach as §10; identity fields excluded from comparison scope; content fields compared under `authority_relevant_mismatch` policy.
- **Stale-metadata behavior:** if the shared input package's `LEGACY_COMPLETION` stage was captured against a metadata state that has since been superseded (detectable via the authoritative metadata's own generation/revision marker, per the 135D.1 staleness guard precedent), the candidate is quarantined (§27), never silently regenerated against newer state (which would violate §6's determinism — the candidate must reflect the same input the CLTR record was derived from, not a re-fetched newer state).
- **Rehearsal-only disclosure:** same shared constant as §8.

It must not become metadata authority: no code path may read a completion-metadata candidate as if it were `.pcae/completion-metadata.json` (or the project's equivalent authoritative path); this is enforced structurally by namespace separation (§7), not by convention alone.

---

## 12. Architecture Status candidate contract

Deterministic projection, sourced only from explicit governed inputs already bound in the shared transition-input package or the CLTR record — never from titles, prose, or document headings (matching 135M's existing prohibition against narrative-inference-prone derivation, and directly addressing F-135N-3's caution about narrative-inference risk):

- **Completed phase:** `phase_id` + `transition_status` from the shared input, verbatim.
- **No active phase after completion:** derived boolean, true whenever the bound `transition_type` is a terminal type (CLTR-SCHEMA-001 §3's 16 `transition_type` values) and no successor task/phase identity is bound.
- **Planned successor:** sourced only from an explicit `recommended_next_phase` field bound into the shared input or CLTR record at capture time (never parsed from report prose) — if absent, the candidate's successor field is explicitly `null`, never inferred.
- **Runtime state:** copied verbatim from `pcae runtime inspect`'s already-governed output at capture time (Observed/observe/unavailable) — never re-derived independently within the candidate.
- **Chapter grouping:** presentation-only, if the underlying production Architecture Status uses chapter/track grouping; carried through unchanged, never used as an identity or gating input.
- **Transition binding / generation binding:** `transition_id` and `rehearsal_generation_id`, as in every other candidate.
- **Limitations:** explicit list of what this projection cannot guarantee (e.g. "successor phase is advisory, not binding," matching `pcae roadmap next`'s existing advisory-only precedent).

The candidate must not replace the generated production Architecture Status; it is written only under the rehearsal namespace (§7) and is never consumed by any command that generates or displays the authoritative Architecture Status.

---

## 13. Checkpoint candidate contract

Candidate states, mirroring 135M §21/CLTR-SCHEMA-001 §17's nine-step atomic publication sequence but scoped to rehearsal only:

1. `generation_preparation` — candidate directory created, no artifacts written yet.
2. `generation_verified` — all artifacts written and individually digest-verified, manifest not yet written.
3. `rehearsal_pointer_unpublished` — generation finalized (immutable), manifest written and verified, pointer not yet touched.
4. `rehearsal_pointer_publication_attempted` — atomic replace of `current-rehearsal` initiated but not confirmed.
5. `rehearsal_pointer_published` — atomic replace confirmed (§20).
6. `comparison_completed` — §28 comparison against authoritative legacy output performed and recorded.
7. `rehearsal_terminal_state` — evidence record (§30) finalized; rehearsal request considered complete (successful or not).
8. `failure` — any step 1–6 failed; see §23 crash matrix for exact per-step failure semantics.
9. `rollback_rehearsal` — a rollback rehearsal (§33) was requested and executed against this generation's pointer history.

The rehearsal checkpoint is explicitly not production recovery authority: `pcae phase-report reconcile`, `pcae task finish`/`pcae phase complete` recovery-state resolution, and any other production recovery path must never read rehearsal checkpoint state as an input (enforced by namespace separation, §7; the production recovery code paths identified in §46's research have no reference to `.pcae/cltr-migration/epochs/*/rehearsals/` anywhere).

---

## 14. Notification-intent candidate contract

A durable notification-intent candidate, without dispatch, binding:

- `notification_id` — a rehearsal-scoped identity, distinct from any real `notification_id`.
- `phase_id`, `transition_id` — as elsewhere.
- `report_id`, `report_digest` — bound to the report candidate (§10), never the authoritative report.
- `rehearsal_generation_id` — as elsewhere.
- `intended_channel` — copied from configuration (e.g. `"telegram"`) as data only, never used to actually address a sink.
- `idempotency_key` — computed deterministically per PFN-001 §8's existing idempotency-key contract, scoped so it can never collide with a real production idempotency key (namespaced with a `rehearsal:` prefix or equivalent, and never written to the production idempotency-key ledger).
- `delivery_attempted: false` — always, throughout Stage 2.
- `rehearsal_only_status: true` — always.

No real secrets: `PCAE_TELEGRAM_BOT_TOKEN`/`PCAE_TELEGRAM_CHAT_ID` (or equivalent) values are never read into a candidate artifact; the candidate's `intended_channel` is a channel-type string only, never a credential or destination address. No dispatch: the rehearsal coordinator (§17 sequence) never imports or calls the Telegram sink module. No production notification marker: this candidate is never written to, or merged with, the production notification-marker path.

---

## 15. Marker candidate contract

Records what a future CLTR-authoritative marker *would* bind, without being one:

- `marker_candidate_id` — rehearsal-scoped, distinct from any production `marker_id`.
- `rehearsal_generation_id` binding.
- `report_digest_binding` — the report candidate's digest.
- `notification_intent_binding` — the notification-intent candidate's `notification_id`.
- `state` — one of the candidate-scoped states mirroring CLTR-SCHEMA-001's marker state vocabulary, prefixed or tagged to make rehearsal scope unmistakable (e.g. `state: "rehearsal_candidate_dispatched_simulated"`, never a bare production state value like `already_dispatched`).
- `uncertainty_semantics` — inherits the same `NOTIFIED`/`NOTIFIED_UNCONFIRMED` distinction CLTR-SCHEMA-001 §19 defines, applied to the simulated intent rather than a real dispatch.
- `non_authority_disclosure` — as elsewhere.

Never written to the production marker location; namespace-separated per §7.

---

## 16. Receipt candidate contract

- No claim of external delivery — `delivery_confirmed: false` always.
- No claim of production completion authority — an explicit `production_completion_authority: "legacy"` field on every receipt candidate, never `"cltr"` or `"rehearsal"`.
- Explicit rehearsal state — `receipt_role: "rehearsal_candidate"`.
- `rehearsal_generation_id`, `transition_id` bindings.
- `marker_candidate_binding` — the marker candidate's identity (§15).
- `notification_intent_candidate_binding` — the notification-intent candidate's identity (§14).
- Unresolved/uncertain fields where real terminal effects did not occur: any field that in a real receipt would reflect a confirmed external effect (e.g. delivery timestamp) is explicitly `null` with `reason: "rehearsal_no_external_effect"`.

A rehearsal receipt must never use the literal value `"finalized"` (or any production-authoritative terminal-state literal) in its `state` field; it uses a distinct rehearsal-scoped vocabulary (e.g. `"rehearsal_recorded"`) so no downstream consumer can mistake it for `pcae phase-report reconcile`'s `Receipt: finalized` output.

---

## 17. External effects boundary

Frozen boundary: **local rehearsal generation assembly and pointer publication ≠ external terminal delivery.**

Stage 2 may create notification intent as data (§14). Stage 2 may not:

- Dispatch Telegram (no import of, or call into, the sink module from any rehearsal module).
- Create delivery confirmation.
- Create a production marker.
- Finalize a production receipt.
- Suppress authoritative delivery (the rehearsal coordinator never sets `notification_suppressed: true` on any production artifact — it has no code path that touches a production artifact at all).
- Cause resend (no rehearsal code path calls the production notification-dispatch function).
- Modify PFN-001 behavior (PFN-001 governs the legacy/production notification path exclusively; Stage 2 introduces no new notification-eligible terminal outcome).

---

## 18. Manifest contract

The rehearsal manifest (`manifest.json` within each candidate/generation directory) binds, at minimum:

- `manifest_schema_version` (new, starts at `1.0.0`, follows CLTR-SCHEMA-001 §2's semver rules independently — a Stage 2-specific schema family, e.g. `pcae.cltr.rehearsal.v1`, distinct from `pcae.cltr.v1` so a MAJOR bump in one never silently affects the other).
- `rehearsal_generation_id` (§6).
- `migration_epoch`, `authority_epoch`.
- `transition_id`.
- `shared_input_package_id`, `final_input_revision_digest`.
- `artifact_inventory` — array of `{artifact_kind, path, digest, artifact_role (§8), verification_status}` for all 23 items in §9.
- `generation_digest` (§19).
- `derivation_sources` — which shared-input capture stage (`PRE_TRANSACTION`/`LEGACY_COMPLETION`) fed each artifact.
- `comparison_results` — summary of §28's comparison, referencing but not duplicating the full comparison record.
- `verification_status` — generation-level rollup (`verified`/`unverifiable`/`quarantined`).
- `limitations`.
- `candidate_or_authoritative_role` — always `"rehearsal_candidate_generation"` for the whole manifest.
- `pointer_target_data` — the exact bytes the rehearsal pointer would reference if this generation is selected as current (does not itself publish the pointer).
- `non_authority_disclosure`.

Manifest verification does not depend on any mutable "latest" file: it is verified entirely from the immutable `generations/<rehearsal-generation-id>/` directory's own contents plus the (separately, atomically published) `current-rehearsal` pointer, which itself only ever names a `rehearsal_generation_id`, never inlines mutable content.

---

## 19. Generation digest contract

- **Canonical artifact ordering:** artifacts are digested in the fixed order given by §9's table (items 1–23), never directory-listing order (which is not guaranteed stable across filesystems).
- **Manifest coverage:** the generation digest covers every artifact's own digest (nested digest binding, not raw bytes, to keep the generation digest computation independent of each artifact's internal serialization details) plus `rehearsal_generation_id`, `migration_epoch`, `authority_epoch`, `transition_id`.
- **Excluded self-referential fields:** the manifest's own `generation_digest` field is excluded from its own input (CLTR-SCHEMA-001 §15 precedent).
- **Digest algorithm:** SHA-256, matching CLTR-SCHEMA-001 §15 exactly.
- **Algorithm identifier:** an explicit `digest_algorithm: "sha256"` field on the manifest — required so a future algorithm change is detectable rather than silently assumed.
- **Canonical byte input:** UTF-8 compact JSON, sorted keys recursively, NFC-normalized strings (CLTR-SCHEMA-001 §14, applied identically to rehearsal artifacts).
- **Nested artifact digest binding:** each artifact's digest is computed independently first (over that artifact's own canonical bytes), then the generation digest is computed over the ordered list of those digests plus the four identity fields above — this ensures a single-artifact tamper is detectable without recomputing the whole generation from scratch, and mirrors the same nested-digest pattern CLTR-SCHEMA-001 already uses between a generation's `record_digest` and `manifest_digest`.
- **Tamper behavior:** any post-finalization modification to any artifact's bytes changes that artifact's digest, which changes the generation digest; verification (§17 sequence step 14) recomputes both and fails closed on any mismatch, quarantining the generation (§27).
- **Unsupported algorithm behavior:** a manifest declaring any `digest_algorithm` other than `"sha256"` is rejected outright (fail-closed), matching CLTR-SCHEMA-001 §2.7's unknown-version-fails-closed precedent.

Changing any authority-relevant candidate artifact changes the generation digest by construction, since every artifact in §9's inventory is included in digest coverage (no artifact is excluded from the manifest's `artifact_inventory`).

---

## 20. Candidate assembly sequence

Deterministic Stage 2 sequence (extends 135M §21 steps 10–18 into full detail):

1. Verify Stage 1 migration evidence exists and is valid for this `transition_id` (reads `.pcae/cltr-migration/epochs/<epoch>/transitions/<transition_id>/evidence/`, never mutates it).
2. Resolve `migration_epoch` and `authority_epoch` from configuration and Stage 1 evidence; reject on mismatch.
3. Load the verified, immutable `SharedTransitionInputPackage` for this transition (the same object Stage 1 already assembled — never re-assembled independently).
4. Verify the package's `LEGACY_COMPLETION` stage is present (the final required input revision) — a package still only at `PRE_TRANSACTION` cannot proceed (§21 precondition).
5. Derive the CLTR record (reuses Stage 1's `derive_cltr`, with the F-135P-3 fix applied).
6. Derive all rehearsal candidates (§9 items 2–14) from the same package and CLTR record.
7. Normalize authoritative legacy outputs for comparison (reuses Stage 1's `legacy_derivation.py` pattern, extended to cover report/metadata/Architecture-Status/checkpoint/marker/receipt/notification content, not just the fields Stage 1 already normalizes).
8. Compare candidates with authoritative outputs (§28).
9. Classify mismatches (§22, using the comparison-result vocabulary extended per F-135P-2's disposition).
10. Apply Stage 2 rehearsal policy (§22 — authority-relevant mismatch blocks; non-authority difference recorded only if explicitly permitted).
11. Create the isolated candidate directory (`rehearsals/<transition-id>/candidates/<rehearsal-generation-id>/`), validated per §7's containment rules.
12. Write all artifacts (§9).
13. Write the manifest (§18).
14. Verify every artifact and digest (§19) — recompute and compare, fail closed on any mismatch.
15. Finalize the immutable rehearsal generation (atomic rename from `candidates/` to `generations/`, mirroring Stage 1's `persistence.py:137-233` pattern).
16. Atomically publish the rehearsal pointer (§20 pointer contract — separate step from generation finalization, so a finalized-but-unpublished state is representable, §13 checkpoint state 3).
17. Verify the pointer target (read back `current-rehearsal`, confirm it resolves to the just-finalized generation).
18. Persist the rehearsal result / evidence record (§30).
19. Expose read-only status/reconciliation (§31/§32 — planned commands, not implemented in this phase or the Stage 2 implementation phase's first cut unless explicitly scoped in; the sequence ends at evidence persistence).

No production pointer or terminal effect appears anywhere in this sequence — confirmed by construction, since no step references any production path outside read-only comparison input (step 7 reads production artifacts; it never writes them).

---

## 21. Precondition contract

Stage 2 rehearsal prerequisites, all must hold before step 1 of §20 proceeds past its checks:

- Valid Stage 1 configuration (`PCAE_CLTR_DUAL_DERIVATION_ENABLED=1`, valid `PCAE_CLTR_MIGRATION_STAGE`, valid `PCAE_CLTR_MIGRATION_EPOCH` — Stage 2 cannot run without Stage 1 already active for this transition).
- Verified shared input (package present, `LEGACY_COMPLETION` stage bound, deep-immutability intact — re-verified via the package's own frozen-dataclass guarantee).
- Valid migration evidence (Stage 1 evidence record for this `transition_id` exists and its own digest verifies).
- Migration progression eligibility (Stage 1's own eligibility signal, per 135M §14/§15's evidence-window concept, must not itself be blocked — e.g. no Stage 1 quarantine for this transition).
- No authority-relevant Stage 1 mismatch for this transition (a Stage 1 `authority_relevant_mismatch` blocks Stage 2 rehearsal for that transition specifically, though it never blocked Stage 1's own migration-evidence recording).
- Compatible `migration_epoch` (matches the Stage 2 rehearsal namespace's own epoch scoping).
- Compatible `authority_epoch` (must be a legacy-authoritative epoch; a CLTR-authoritative epoch value, which does not exist yet, would be rejected outright).
- Supported schema versions (CLTR-SCHEMA-001 ≥ 1.0.1 and < the next MAJOR; rehearsal manifest schema as declared in §18).
- Explicit Stage 2 rehearsal flag set (§42 — `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED=1`).
- Legacy authority active (always true throughout Stage 2 by construction — `production_authority` remains hardcoded `LEGACY`).
- No cutover approval implied by rehearsal success (rehearsal evidence, however clean, never substitutes for the explicit 135M §41 approval artifact Stage 3 requires).
- No unresolved Stage 2 Blocking finding (per §3's dispositions — F-135P-1, F-135P-3, F-135P-4, and F-135P-2's `EXPECTED_REPRESENTATION_DIFFERENCE` half must already be resolved in the codebase before the Stage 2 rehearsal flag may even be turned on in any environment beyond isolated testing).

If any precondition fails, no rehearsal generation is published — the coordinator records a precondition-failure evidence entry (§30) and stops before step 11 of §20 (no candidate directory is even created), so no partial candidate exists to quarantine.

---

## 22. Mismatch policy

- An `authority_relevant_mismatch` (or any mismatch class 135M §12 already designates authority-relevant) blocks rehearsal pointer publication for that generation — the candidate may still be finalized as evidence (§20 step 15) but §20 step 16 (pointer publication) is skipped, and the generation is recorded as `blocked_by_mismatch`, distinct from `quarantined` (§27) — a mismatch is expected migration evidence, not tampering.
- An unverifiable critical artifact (any of §9's items 1–14, the record-bearing/derivative kinds) blocks rehearsal pointer publication; unverifiable observational-kind artifacts (items 10, 11, 14 — the V-role views) do not block, since CLTR-SCHEMA-001 §5 already treats observational views as non-authoritative by design.
- A non-authority difference (a difference in a field CLTR-SCHEMA-001 §21.4 marks `normalized_semantic` or `presentation_only`) may be recorded only if explicitly permitted by the manifest's declared comparison mode for that artifact kind — never silently dropped, never silently promoted to a blocking mismatch.
- Every mismatch, of every class, is preserved in the comparison record (§28) — none are discarded even if non-blocking.
- Authoritative production completion remains governed by legacy path regardless of any Stage 2 mismatch outcome — the mismatch policy governs only whether the rehearsal pointer moves, never whether the transition itself succeeded in production.
- A failed rehearsal (blocked or quarantined) cannot become `current-rehearsal` — the pointer-publication step (§20 step 16) is simply never reached.
- A failed rehearsal cannot advance migration progression — the evidence record (§30) marks `progression_eligibility: false` for that generation (§29).
- A mismatch cannot trigger repair through inference — no code path "fixes" a mismatch by re-deriving with adjusted assumptions; the only remedies are (a) accept as an already-classified expected difference per an explicit, pre-declared comparison-mode rule, or (b) quarantine and require governed human review.

---

## 23. Rehearsal pointer contract

One atomic, non-authoritative pointer, `current-rehearsal` (§7), requirements:

- Separate file from any production pointer (`.pcae/phase-reports/latest.json`, `.pcae/cltr-shadow/current`, any future production `current`).
- Targets exactly one verified rehearsal generation (`rehearsal_generation_id` + `generation_digest`, mirroring CLTR-SCHEMA-001 §16's 4-field `current` pointer shape, adapted with rehearsal-scoped field names, e.g. `{rehearsal_generation_id, migration_epoch, authority_epoch, generation_digest}`).
- Atomically replaceable via `os.replace` onto the same filesystem, same mechanism as Stage 1's `persistence.py:137-233`.
- Validates the target generation exists, is finalized (immutable, under `generations/` not `candidates/`), and its digest verifies, before the replace is attempted.
- Preserves the prior valid pointer content until the replace syscall itself completes (write-to-temp-then-rename, never truncate-in-place).
- Rejects a dangling target (generation directory does not exist).
- Rejects wrong `migration_epoch`.
- Rejects wrong `authority_epoch`.
- Rejects wrong `transition_id` (a rehearsal pointer is scoped per-transition under `rehearsals/<transition-id>/`; there is one `current-rehearsal` per transition directory, not one global rehearsal pointer across all transitions — this follows directly from §7's layout and prevents one transition's rehearsal from ever appearing to supersede another's).
- Rejects a digest mismatch between the pointer's recorded `generation_digest` and the target generation's actual, recomputed digest.
- Rejects a quarantined generation as a publication target.
- Remains read-only to inspection commands (§31/§32 — planned commands only read `current-rehearsal`, never write it outside the coordinator's own publication step).
- No automatic inference repair: if `current-rehearsal` is found corrupt or unreadable on inspection, the recovery contract (§24) governs; no code path silently rewrites it based on a guess.

The pointer's own filename and any identifier fields it contains explicitly disclose rehearsal status (e.g. literal field name `current-rehearsal`, never `current`, and a `non_authority_disclosure` field within the pointer file's own JSON body).

---

## 24. Atomicity scope

"Atomic publication rehearsal" means, precisely:

- All local candidate artifacts (§9, all 23 items) are complete, individually verified, and included in a verified manifest before the rehearsal generation becomes visible at all (i.e., before it is renamed into `generations/`).
- Pointer replacement (`current-rehearsal`'s atomic rename) is the sole visibility boundary for "this is now the latest rehearsal" — nothing before that rename is externally observable as current.
- Partial candidates (anything still under `candidates/`, or a `generations/` entry with a failed manifest-verification) are never `current rehearsal` — the pointer can only ever be replaced to target a generation that has already passed step 14 of §20.
- The prior `current-rehearsal` target remains valid (its `generations/` directory is never deleted or mutated) until the pointer is successfully replaced to a new target.
- External effects (§17) are wholly excluded from this atomicity boundary — the atomicity guarantee covers only local filesystem state under `rehearsals/<transition-id>/`.
- Production pointers remain untouched — no code path in the rehearsal coordinator opens any production pointer file for writing, ever.
- Production authority remains unchanged regardless of rehearsal outcome.

This document does not claim multi-filesystem or external-service atomicity anywhere; §25 states filesystem assumptions explicitly, and §17 states the external-effects exclusion explicitly, precisely to prevent that overclaim.

---

## 25. Filesystem assumptions

- Same-filesystem atomic rename (`os.replace`) is required between the candidate directory, the finalized generation directory, and the `current-rehearsal` pointer file — all three must reside under the same `.pcae/cltr-migration/` mount; the implementation must reject (fail closed) if `.pcae/` is detected to span a different filesystem than a configured alternate temp location (mirroring the existing cross-device-rename caution already implicit in Stage 1's `persistence.py`).
- Temporary directory/file location: always a sibling of the final target within the same parent directory (e.g. `candidates/.tmp-<rehearsal-generation-id>/` renamed to `generations/<rehearsal-generation-id>/`), never a system-wide temp directory, to guarantee same-filesystem rename.
- Directory synchronization: after writing all files in a candidate directory and before the finalizing rename, the implementation should `fsync` each file and the containing directory where the platform supports it (best-effort on platforms where directory fsync is unsupported, e.g. some Windows filesystems — disclosed as a platform limitation, not silently assumed).
- File synchronization: each artifact file is fsynced after write and before its digest is computed for the manifest, to avoid digesting content still buffered but not yet durable.
- Permission errors: any `PermissionError` during candidate write aborts the rehearsal attempt, recorded as a failure (§23 crash matrix row "during candidate write"), never partially retried in place.
- Disk-full behavior: an `OSError` (`ENOSPC`) during write aborts identically; the partially-written candidate directory is left in place under `candidates/` (not deleted) as failure evidence, quarantined on next inspection (§27).
- Cross-device rename: explicitly unsupported; detected and rejected at configuration/precondition time (§21), not discovered mid-sequence.
- Windows/macOS/Linux differences: directory-fsync semantics differ (see above); `os.replace` is atomic on all three for same-volume renames, which is relied upon; path length and reserved-character differences on Windows are handled by the same identifier-character allow-listing already required by §7.
- Symlink handling: candidate directories and all artifact files are created fresh (never symlinked); any pre-existing symlink found at a target path during candidate creation causes the attempt to abort rather than to write through the link.
- Immutable-generation expectations: once a `generations/<id>/` directory is finalized, no code path in the rehearsal or Stage 1 packages ever opens a file under it for writing again — enforced by convention plus a best-effort read-only file-permission set after finalization (`chmod` to remove write bits), not solely relied upon as the sole enforcement mechanism (belt-and-suspenders, since the primary guarantee is "no code path ever attempts the write").

Platform limitations are stated honestly rather than assumed away: directory fsync durability guarantees are weaker on some platforms, and this document does not claim POSIX-strength durability guarantees on all supported platforms uniformly.

---

## 26. Crash matrix

| Crash point | Prior current-rehearsal | Candidate state | Failure artifact | Retry eligible | Reconciliation | Quarantine | Production-authority impact |
|---|---|---|---|---|---|---|---|
| Before candidate creation | unchanged | none | precondition-failure record (§21) | yes | n/a | no | none |
| During CLTR record write | unchanged | incomplete, under `candidates/` | failure record, step="cltr_record" | yes, same generation id if input unchanged | marks incomplete | on next inspection if abandoned | none |
| During report-candidate write | unchanged | incomplete | failure record, step="report_candidate" | yes | marks incomplete | on next inspection | none |
| During metadata-candidate write | unchanged | incomplete | failure record, step="metadata_candidate" | yes | marks incomplete | on next inspection | none |
| During Architecture Status candidate write | unchanged | incomplete | failure record, step="arch_status_candidate" | yes | marks incomplete | on next inspection | none |
| During checkpoint candidate write | unchanged | incomplete | failure record, step="checkpoint_candidate" | yes | marks incomplete | on next inspection | none |
| During notification-intent candidate write | unchanged | incomplete | failure record, step="notification_intent_candidate" | yes | marks incomplete | on next inspection | none |
| During marker/receipt candidate write | unchanged | incomplete | failure record, step="marker_receipt_candidate" | yes | marks incomplete | on next inspection | none |
| During manifest write | unchanged | complete artifacts, no manifest | failure record, step="manifest" | yes | marks "candidate complete, unverified" | on next inspection | none |
| Before verification | unchanged | complete + manifest, unverified | failure record, step="pre_verification" | yes | marks unverified | possible | none |
| During verification | unchanged | complete + manifest, verification incomplete | failure record, step="verification" | yes | re-verify from scratch | possible if digests fail | none |
| After verification, before finalization | unchanged | verified, still under `candidates/` | checkpoint state "generation_verified" | yes | resume at finalize | no | none |
| After finalization, before pointer temp write | unchanged (finalization complete, pointer untouched) | finalized, under `generations/` | checkpoint state "rehearsal_pointer_unpublished" | n/a (generation already valid) | resume at pointer publish | no | none |
| During pointer temp write | unchanged (temp file only) | finalized | checkpoint state "rehearsal_pointer_publication_attempted" | n/a | verify temp file, retry replace | no | none |
| Before atomic replace | unchanged | finalized | same as above | n/a | retry replace | no | none |
| During replace | uncertain (rename is atomic at the OS level; "during" means the syscall itself, which cannot leave a half-written pointer file, but the *process* may crash immediately before or after without the caller observing which) | finalized | checkpoint state "rehearsal_pointer_publication_attempted", `outcome: uncertain` | read back `current-rehearsal` on recovery to determine actual outcome, then reconcile | reconcile via read-back, never retry blindly | no | none |
| After replace | now targets new generation | finalized | checkpoint state "rehearsal_pointer_published" | n/a | resume at result recording | no | none |
| During result recording | targets new generation | finalized, published | evidence record incomplete | yes, re-record from durable pointer + manifest state | reconstructible from pointer + manifest alone | no | none |

Production-authority impact is "none" in every row by construction — no row in this matrix involves a write to any production path.

---

## 27. Rehearsal recovery

Recovery is entirely state-based, using recorded evidence (checkpoint states from §13/§26), never inference from titles, Git history, latest files, or stale metadata (matching 135D.1's staleness-guard precedent and 135H.2's exactly-once recovery precedent, applied here to rehearsal state).

States:

- `no_candidate` — no candidate directory exists for this generation id; safe to start fresh.
- `candidate_incomplete` — some artifacts written, manifest absent or incomplete; resume from the last completed artifact-write step, or restart candidate assembly from scratch if the shared input package is unchanged (idempotent either way, per §25).
- `candidate_complete_unverified` — all artifacts + manifest present, verification not yet run; run verification (§20 step 14).
- `candidate_verified_not_finalized` — verified, still under `candidates/`; finalize (§20 step 15).
- `generation_finalized_unpublished` — under `generations/`, pointer not yet touched; proceed to pointer publication (§20 step 16).
- `pointer_publication_not_attempted` — as above.
- `pointer_publication_uncertain` — crash during/around the atomic replace; read back `current-rehearsal` to determine ground truth, then reconcile the checkpoint to match reality (never re-attempt the replace blindly, since a second replace to the same target is idempotent but a second replace after an already-successful first one to a *different* target would be wrong).
- `pointer_published` — terminal success state; proceed to result recording if not yet done.
- `result_record_incomplete` — evidence record (§30) not yet finalized; reconstruct from the durable pointer + manifest state and finalize it.
- `quarantine_required` — a digest, epoch, or transition mismatch was detected; move to quarantine (§27's own quarantine section, sibling of recovery), never auto-repaired.
- `rollback_rehearsal_requested` — an explicit, separately-governed rollback-rehearsal request is pending; see §33.

No recovery step ever reads a phase-report title, a Git commit message, or `tasks/DONE.md` prose to decide state — only the rehearsal namespace's own recorded checkpoint/evidence files and the durably-written pointer file itself.

---

## 28. Idempotency

- **Rehearsal request:** idempotency key = `rehearsal_generation_id` itself (§6) — re-requesting rehearsal for the same transition with an unchanged shared input and unchanged candidate derivation logic reproduces the same identity and is a no-op if already finalized.
- **Candidate generation:** re-running candidate assembly against an already-`candidate_complete_unverified` or further-along state resumes rather than restarts from zero (§27), and produces byte-identical artifacts given identical inputs (deterministic derivation, §6/§10).
- **Artifact derivation:** each artifact derivation function is a pure function of the shared input package plus (where applicable) the CLTR record — no artifact derivation reads mutable global state.
- **Manifest:** deterministic given the same ordered artifact digest list (§19); re-writing the manifest against unchanged artifacts reproduces the same `generation_digest`.
- **Generation finalization:** the finalizing rename is naturally idempotent at the filesystem level (renaming into an already-existing target directory is rejected, not silently overwritten) — a second finalization attempt against an already-finalized generation is detected and treated as a no-op success, not an error, not a duplicate.
- **Rehearsal pointer publication:** publishing the same target a second time is a no-op (the pointer already points there); publishing a *different* target requires a fresh, explicit publication step, never implicit.
- **Result recording:** the evidence record (§30) uses the same `rehearsal_generation_id` as its own key; re-recording against an unchanged generation is idempotent (overwrite-with-identical-content, verified by digest before considering the write necessary at all).
- **Reconciliation:** read-only, naturally idempotent (§32).
- **Rollback rehearsal:** idempotent per rollback target — rolling back to the same prior generation twice produces the same pointer state (§33).

Stable identities (per §6/§8) and idempotency keys derived from them prevent duplicate logical rehearsal publication — there is no path by which the same logical rehearsal (same transition, same input, same candidate content) can produce two different `rehearsal_generation_id` values, and no path by which two different rehearsal attempts for the same transition with the same input can both become `current-rehearsal` simultaneously (the pointer is a single file, atomically replaced).

---

## 29. Conflicting replay

| Scenario | Behavior |
|---|---|
| Same transition ID, same generation content | Idempotent no-op; existing generation reused, not regenerated (§28). |
| Same transition ID, changed artifact | Different `rehearsal_generation_id` (§6, since `final_input_revision_digest` or downstream content changed) — a new generation is candidate-assembled; the old one remains as evidence, un-superseded automatically (only the pointer, if explicitly republished, moves). |
| Same generation ID, changed digest | Fail closed — a `rehearsal_generation_id` collision with a differing recomputed digest is treated as tampering or a digest-computation defect, never silently accepted; quarantined (§27). |
| Prior migration epoch | Rejected at precondition stage (§21) — rehearsal only proceeds for the currently-configured `migration_epoch`. |
| Prior authority epoch | Rejected identically. |
| Stale Stage 1 evidence | Rejected at precondition stage (§21) — the Stage 1 evidence must itself be current for this transition. |
| Changed schema version | Rejected if outside supported range (§18/§21); a supported MINOR/PATCH bump within CLTR-SCHEMA-001's compatibility rules proceeds, disclosed in the manifest. |
| Repeated pointer publication | Idempotent no-op if the target is unchanged (§28); a fresh, explicit publication if the target changed. |
| Retry after uncertain replacement | Read back `current-rehearsal` first (§27's `pointer_publication_uncertain` state), reconcile to ground truth, only then decide whether a retry is needed — never blindly retries the replace. |

Conflicting immutable content (a `rehearsal_generation_id` whose recomputed digest disagrees with its manifest's recorded digest) fails closed in every case — never resolved by silently picking one version.

---

## 30. Quarantine

Quarantine applies to:

- Invalid candidate (fails structural validation).
- Tampered artifact (digest mismatch against manifest).
- Digest mismatch (generation-level).
- Manifest mismatch (manifest's own recorded digests disagree with recomputed artifact digests).
- Wrong epoch (migration or authority epoch mismatch discovered post-hoc).
- Wrong transition (a generation somehow bound to a `transition_id` inconsistent with its own directory location — should be structurally impossible given §7's layout, but checked anyway).
- Invalid pointer target (§23's rejection conditions, if somehow bypassed and later detected).
- Unsupported schema/manifest version.
- Failed verification (any of §20 step 14's checks).
- Conflicting replay (§29's "same generation ID, changed digest" row).

Quarantined generations:

- Remain as evidence (moved to, or marked within, `quarantine/`, never deleted — §7).
- Never become `current-rehearsal` (enforced by §23's explicit rejection of quarantined targets).
- Cannot receive migration progression credit (§29's eligibility field is forced `false`).
- Cannot be silently repaired (no automated "fix and retry" path exists; remediation requires a fresh candidate generation from corrected input, governed explicitly, never an in-place patch of quarantined content).
- Cannot be consumed by later-stage (Stage 3+) planning as a successful rehearsal (the evidence record, §30, explicitly marks quarantined generations as such, and any future Stage 2→3 readiness tooling must exclude them from its evidence count).

---

## 31. Rehearsal comparison

Comparisons performed at §20 step 8, against the authoritative production artifact that actually governed this transition:

| Comparison | Notes |
|---|---|
| Authoritative report vs. report candidate | Identity fields excluded from scope (§10); content fields compared under `authority_relevant_mismatch` policy. |
| Authoritative metadata vs. metadata candidate | Per §11. |
| Authoritative Architecture Status vs. projected candidate | Per §12; only explicit governed-input fields compared, since the candidate never attempts to reproduce presentation-only formatting. |
| Authoritative checkpoint vs. checkpoint candidate | Checkpoint *state semantics* compared (did the same lifecycle events occur in the same order), not the checkpoint's own storage format. |
| Authoritative notification result vs. notification-intent candidate | **Expected difference, not a mismatch** — the candidate never attempted dispatch, so fields like delivery timestamp are definitionally absent (§4 F-135P-2 disposition: classified via the (to-be-wired) `EXPECTED_REPRESENTATION_DIFFERENCE` class, never fabricated as a match). |
| Authoritative marker vs. marker candidate | Same expected-difference treatment for any field dependent on the (unattempted) notification. |
| Authoritative receipt vs. receipt candidate | Same expected-difference treatment. |
| Authoritative commit attribution vs. CLTR-bound attribution | Compared under `commit_ownership_mismatch` (135M §12's existing class), now exercised with the F-135P-3 fix in place so a non-empty ownership tuple can actually be compared rather than crashing. |

Fields that cannot match because an external effect has not occurred are always classified as expected rehearsal differences, never as fabricated matches (which would falsely inflate rehearsal-success evidence) and never as unclassified/silently-dropped mismatches (which would hide real information).

---

## 32. Progression eligibility

Stage 2 progression eligibility (feeding a future Stage 2→3 evidence-window calculation per 135M §14/§15) is `false` whenever:

- Stage 1 evidence for the transition is invalid.
- An `authority_relevant_mismatch` was recorded for this generation.
- A critical (record-bearing/derivative-kind) artifact was unverifiable.
- Generation verification failed.
- Pointer publication failed or is uncertain (unresolved `pointer_publication_uncertain` state).
- Wrong `migration_epoch` or `authority_epoch`.
- A digest mismatch occurred anywhere in the chain.
- A split-brain condition was detected (§34).
- The generation is quarantined.
- Entry-point coverage for the evidence window is incomplete (per 135M §15's requirement that all four entry points, plus at least one recovery path, be independently covered — never averaged into one aggregate count).
- A required recovery drill (§33/§34's rollback-rehearsal drill) is incomplete.
- An inherited Stage 2 prerequisite finding (§3) remains unresolved in the running codebase.

Eligibility remains advisory migration evidence only — consistent with `pcae roadmap next`'s existing advisory, non-binding precedent. No automatic Stage 3 progression occurs based on eligibility; 135M §41's explicit approval-artifact requirement for Stage 3 entry is unchanged and unaffected by anything in this document.

---

## 33. Stage 2 evidence record

One rehearsal evidence record per rehearsal attempt (successful or not), binding:

- `evidence_id` (deterministic, derived from `rehearsal_generation_id` + attempt sequence).
- `schema_version` (evidence-record schema, versioned independently per CLTR-SCHEMA-001 §2's rules).
- `migration_stage` — fixed literal `"stage_2_atomic_publication_rehearsal"`.
- `migration_epoch`, `authority_epoch`.
- `production_authority` — fixed `"legacy"`.
- `transition_id`.
- `shared_input_identity` — `shared_input_package_id` + `final_input_revision_digest`.
- `stage_1_migration_evidence_identity` — reference to the Stage 1 evidence this rehearsal built on.
- `rehearsal_generation_id`.
- `manifest_digest`, `generation_digest`.
- `pointer_result` — one of the §13/§26 terminal outcomes.
- `comparison_summary` — §31's results, summarized.
- `mismatch_classes` — every mismatch class encountered, per §22's preservation requirement.
- `crash_recovery_state` — if applicable, which §26 row was hit and how it resolved.
- `rollback_readiness` — whether this generation is a valid rollback target (§33/§34).
- `progression_eligibility` — §32's boolean.
- `limitations`.
- `record_digest` (self-exclusion, as elsewhere).
- `non_authority_disclosure`.

---

## 34. Read-only status plan

Future command (**not implemented in 135Q**): `pcae cltr migration rehearsal status`.

Planned to report: Stage 2 enabled; production authority; migration epoch; authority epoch; latest rehearsal generation; pointer validity; manifest validity; generation digest validity; artifact inventory summary; comparison summary; blockers; quarantine count; progression eligibility; `mutation: none`. Modeled directly on the existing `pcae cltr migration status`/`pcae runtime inspect` read-only presentation pattern.

---

## 35. Read-only reconciliation plan

Future command (**not implemented in 135Q**): `pcae cltr migration rehearsal reconcile --phase-id <PHASE_ID>`.

Planned to inspect: Stage 1 evidence; candidate history; finalized generations; the rehearsal pointer; artifact digests; the manifest; mismatch results; failures; quarantine; recovery state; production artifacts by reference only (never by copy-and-mutate); blockers. `mutation: none` — modeled directly on `pcae phase-report reconcile`'s existing read-only precedent (confirmed in §2 to already report `Mutation: none (inspection only)`). Must not create, repair, replay, publish, dispatch, or mutate anything.

---

## 36. Rollback rehearsal

May rehearse:

- Retaining the prior rehearsal pointer (the trivial no-op case).
- Switching the rehearsal pointer to a prior verified rehearsal generation (an explicit, atomic replace targeting an older `generations/<id>/` entry, using the same §23 pointer contract).
- Recording rollback evidence (a `rollback_rehearsal` evidence record, §33-shaped, noting the prior and new targets).
- Invalidating migration progression for the newer candidate being rolled back from (its `progression_eligibility` is set/confirmed `false`).
- Changing `migration_epoch` where required (if the rollback crosses an epoch boundary — e.g. rolling back to a generation from a prior epoch requires explicit epoch reconciliation, not silent epoch-mixing).
- Preserving all generations and evidence (nothing is deleted by a rollback rehearsal).

Must not:

- Change production pointers.
- Roll back the production report.
- Undo external delivery (there is none to undo, per §17).
- Alter the production marker.
- Alter the production receipt.
- Rewrite history (append-only `generations/`/`failures/`, per §7).

---

## 37. Roll-forward preference

Stage 2 should prefer reconciliation or roll-forward over pointer rollback whenever:

- Pointer replacement uncertainty occurred but the read-back (§27) shows the replace actually succeeded — reconcile the checkpoint to reality rather than rolling back a successful publication.
- Pointer replacement succeeded but result recording (§30) is incomplete — roll forward by completing the evidence record, never roll back the already-successful pointer.
- Irreversible production effects have already been performed by the legacy path (which is always true by the time Stage 2 rehearsal runs, since the shared input's `LEGACY_COMPLETION` stage is captured only after legacy's sequential path completes, per 135N's F-135N-1 repair) — the rehearsal layer has no production effect to roll back in the first place.
- Production completion is already visible (`pcae phase-report show --latest` already reflects it).
- Notification was already delivered by the authoritative path.

The rehearsal layer must never pretend production was rolled back: no rollback-rehearsal evidence record or CLI output may use language implying a production effect was undone, since none ever occurred within the rehearsal boundary.

---

## 38. Split-brain prevention

Blocked before rehearsal pointer publication whenever any of the following is detected:

- Rehearsal report candidate and metadata candidate derived from different input revisions.
- Report candidate and CLTR record bound to different `transition_id` values.
- Candidate checkpoint referencing a different `rehearsal_generation_id` than the one being finalized.
- Notification-intent candidate referencing a different report digest than the report candidate's own.
- Marker candidate referencing a different notification identity than the notification-intent candidate's own.
- Receipt candidate referencing a different marker identity than the marker candidate's own.
- Rehearsal pointer referencing a different `migration_epoch` than the transition's own current epoch.
- Stage 1 evidence and Stage 2 generation binding different `shared_input_package_id`/digest values.
- Production comparison (§31) referencing a stale authoritative artifact (detected via the same staleness-guard technique 135D.1 established, applied to the copied-evidence artifacts used as comparison input).

Every one of these is checked structurally at manifest-verification time (§20 step 14) by confirming every cross-reference field in every candidate artifact resolves to the *same* `transition_id`/`rehearsal_generation_id`/digest pair before the manifest is considered valid. Any split-brain condition blocks rehearsal pointer publication (the generation may still finalize as evidence, quarantined, per §27).

---

## 39. Four-entry-point behavior

All four production finalization entry points — confirmed exact call sites:

- `run_phase_complete` (`src/pcae/commands/phase.py:494`, `entry_point="phase_complete"`).
- `run_task_finish` (`src/pcae/commands/task.py:891`, `entry_point="task_finish"`).
- `run_phase_report_create` (`src/pcae/commands/phase_reports.py:227`, `entry_point="phase_report_create"`).
- `run_notify_send_report` (`src/pcae/commands/notifications.py:305`, `entry_point="notify_send_report"`).

All four funnel through `run_finalization_transaction()` (`src/pcae/core/finalization_transaction.py`). Stage 2 requires each to use:

- The same shared transition-input package (already true from Stage 1).
- The same design-B `transition_id` (already true from Stage 1/135N).
- The same Stage 1 migration-evidence contract (unchanged).
- The same rehearsal coordinator (new in Stage 2 — a single `rehearsal/coordinator.py` invoked identically regardless of `entry_point` value).
- The same candidate inventory (§9, identical for all four).
- The same verification (§20 step 14, identical logic).
- The same pointer contract (§23, identical logic).
- The same failure policy (§22/§26/§27, identical logic).
- The same non-authority disclosure (§4 F-135P-4's fixed shared constant).

No entry-point-specific publication semantics — the only entry-point-specific data is the `entry_point` string itself, which is carried through as an ordinary field (once F-135P-1 is fixed so it is truthful for all four).

---

## 40. Ordinary and recovery paths

- **Ordinary finalization** (`phase_complete`, `task_finish` under normal conditions): full §20 sequence runs.
- **Task finish / phase complete:** identical treatment via the shared coordinator.
- **Report-create recovery / `--allow-partial-report`:** the shared input's recovery classification (once F-135P-1 is fixed) marks this correctly; a partial report accepted under `--allow-partial-report` is itself evidence of an incomplete legacy outcome — the rehearsal candidate is still assembled and compared (so the mismatch/comparison record captures the partial nature honestly), but §41 governs its inability to succeed as a clean rehearsal.
- **Governed manual recovery** (`notify_send_report`): identical treatment.
- **Paused task, stale metadata conflict, promotion uncertainty, missing terminal report:** all detected upstream by Stage 1's already-existing recovery classification and staleness guard; Stage 2 rehearsal for a transition in one of these states inherits the corresponding non-`ordinary_finalization` recovery classification, which the mismatch policy (§22) and precondition contract (§21) both consume — none of these states is silently treated as ordinary.
- **Rejected candidate / partial candidate:** must not produce a successful rehearsal generation — see §41.
- **Reconciliation-only path** (`pcae phase-report reconcile`, `pcae cltr migration rehearsal reconcile` once implemented): read-only, never itself triggers a new rehearsal attempt.

---

## 41. 135H.1 escape resistance

A rejected recovery candidate (the scenario 135H.1 investigated and repaired — a missing terminal report / failed delivery recovery) cannot:

- **Satisfy Stage 2 preconditions** — §21 requires valid, non-stale Stage 1 evidence and a `LEGACY_COMPLETION`-stage shared input; a rejected candidate's legacy path never reached a clean completion, so the shared input's `LEGACY_COMPLETION` enrichment either never occurs or is itself marked with the rejection/failure classification, which §21's precondition check reads and fails closed on.
- **Produce a valid final shared-input revision** — the `final_input_revision_digest` bound into §6's generation identity would reflect the incomplete/rejected state, and the precondition check in §21 (step 4 of §20) blocks proceeding past candidate derivation.
- **Produce a valid report candidate** — §10's report candidate derivation depends on the same shared input; an incomplete input produces, at best, an artifact marked `verification_status: "unverifiable"` (§8), which §22 treats as blocking.
- **Produce a successful rehearsal manifest** — §18's manifest-verification step (§20 step 14) fails closed on any unverifiable critical artifact.
- **Become `current-rehearsal`** — §23 rejects any target whose generation is not fully verified.
- **Receive progression credit** — §32 forces `progression_eligibility: false` for any generation tied to a failed precondition, unverifiable artifact, or blocked mismatch.
- **Trigger notification** — Stage 2 never dispatches regardless (§17); this holds a fortiori for a rejected candidate.
- **Create marker or receipt** — only candidate marker/receipt artifacts are ever created (§15/§16), and only within a candidate/generation directory that itself must pass verification to be published — a rejected candidate's marker/receipt candidates remain quarantined evidence, never promoted.
- **Establish metadata authority** — §11 explicitly forbids any code path from reading a metadata candidate as authoritative; this holds regardless of the candidate's underlying legacy state.

---

## 42. Exactly-once preservation

Exactly-once identity is defined for: rehearsal request (§6's `rehearsal_generation_id`), candidate generation (same), generation finalization (idempotent rename, §28), rehearsal pointer publication (idempotent per-target, §28), rehearsal evidence (`evidence_id`, §33), rollback rehearsal (per-rollback-target idempotency, §36), and reconciliation (naturally idempotent, read-only, §35).

Confirmed by construction that Stage 2 cannot cause a duplicate: authoritative report (Stage 2 never writes to `.pcae/phase-reports/`); production promotion (no code path touches the production promotion mechanism); checkpoint (production checkpoint namespace untouched); notification (§17 — no dispatch capability exists in the rehearsal coordinator at all); marker (production marker namespace untouched); receipt (production receipt namespace untouched); lifecycle completion (the rehearsal coordinator never calls, imports, or otherwise invokes `run_finalization_transaction()`'s production-completion code paths — it only *reads* their already-produced output, per §31, as comparison input).

---

## 43. Notification isolation

Frozen: no dispatch from Stage 2; no network call; no Telegram invocation; no production notification-intent mutation; no delivery confirmation; no resend; no suppression; no Telegram inbound capability. Stage 2 may only derive a local, non-authoritative notification-intent candidate (§14). This is enforced structurally: the planned `src/pcae/cltr/migration/rehearsal/` package (§55) imports nothing from the Telegram sink module, and a planned no-go test (§57) asserts this via both static import-graph inspection and a monkeypatched-socket/subprocess containment test, mirroring Stage 1's existing no-go tests (per 135P's confirmed "subprocess/socket monkeypatch tests" precedent).

---

## 44. Marker and receipt isolation

Frozen: no production marker creation; no production marker mutation; no production receipt creation; no production receipt mutation; no uncertainty strengthening (a rehearsal candidate never converts a production `NOTIFIED_UNCONFIRMED` into a `NOTIFIED`, or vice versa); no terminal-success claim from rehearsal evidence (§16's explicit vocabulary separation from production terminal-state literals).

---

## 45. Feature configuration

Separate Stage 2 configuration, distinct from Stage 1's flags:

```
PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED     # new, Stage 2 master switch, default: unset/0 (disabled)
PCAE_CLTR_MIGRATION_STAGE              # existing (Stage 1), must equal a Stage-2-compatible value
                                        # when rehearsal is enabled (e.g. "dual_derivation_legacy_authority"
                                        # remains valid; a Stage-3+ value is rejected, §21)
PCAE_CLTR_MIGRATION_EPOCH              # existing (Stage 1), reused unchanged, required non-empty
```

Requirements: disabled by default; valid only with Stage 1 prerequisites already satisfied (§21); incompatible with any CLTR-authority/Stage-3 flag (none exists yet, but the precondition check explicitly rejects one if ever introduced prematurely); cannot activate Stage 3 under any combination; visible in `pcae cltr migration rehearsal status` (§34, planned) exactly like Stage 1's flags are visible in `pcae cltr migration status` today; invalid combinations fail closed (§46); no single Boolean changes lifecycle authority — `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED=1` alone can never make CLTR authoritative, since `production_authority` remains a separate, hardcoded `LEGACY` literal untouched by any Stage 2 flag.

---

## 46. Invalid configuration

Fail-closed behavior, checked at precondition time (§21):

- Rehearsal enabled without Stage 1 (`PCAE_CLTR_DUAL_DERIVATION_ENABLED` unset) → rejected.
- Missing `migration_epoch` → rejected.
- Wrong `authority_epoch` (any value implying non-legacy authority) → rejected.
- Unsupported `PCAE_CLTR_MIGRATION_STAGE` value → rejected.
- A Stage 3 authority flag present (should none exist yet, any future flag matching a Stage-3-reserved name pattern) → rejected.
- Inconsistent schema versions (rehearsal manifest schema vs. CLTR-SCHEMA-001 incompatible pairing) → rejected.
- Notification migration enabled (no such flag exists; if one is ever introduced prematurely, its mere presence alongside rehearsal enablement is rejected, since §43 requires notification isolation to hold unconditionally through all of Stage 2) → rejected.
- Production pointer target configured as the rehearsal pointer (a configuration error pointing `current-rehearsal`'s path at a production pointer path) → rejected at path-containment validation (§7).
- Missing Stage 1 evidence → rejected.
- Incompatible feature combination generally → rejected, with a specific diagnostic identifying which combination failed (never a generic "invalid configuration" with no detail, matching the existing `pcae check`/`pcae health` diagnostic-detail precedent).

---

## 47. Security and containment

- Path traversal: blocked by §7's identifier allow-listing and resolved-path containment check.
- Symlink escape: blocked by §7/§25 (no symlinks created; pre-existing symlinks at target paths abort the write).
- Pointer substitution: blocked by §23's target-validation checks (epoch, transition, digest).
- Manifest substitution: blocked by §19's generation-digest recomputation at every read.
- Generation substitution: blocked identically.
- Artifact substitution: blocked by per-artifact digest verification (§19).
- Wrong phase / wrong transition: blocked by §38's split-brain cross-reference checks.
- Wrong input revision: blocked by §6's `final_input_revision_digest` binding.
- Wrong migration/authority epoch: blocked by §21/§23.
- Digest substitution: blocked by §19/§29 (fail-closed on any digest mismatch).
- Replay: blocked by §29's conflicting-replay table.
- Duplicate pointer publication: idempotent, never harmful (§28).
- Quarantine bypass: no code path exists to promote a quarantined generation to `current-rehearsal` (§23 rejects it explicitly; there is no override flag).
- Oversized artifact/resource exhaustion: candidate artifacts are bounded by the same size expectations as existing production artifacts (phase reports, metadata); no rehearsal artifact type introduces unbounded-size content (e.g. no raw log dumps); a reasonable size ceiling (matching existing production report size norms) is enforced at write time, aborting the attempt with a clear diagnostic if exceeded, rather than silently truncating.
- Stale authoritative comparison source: detected via the same staleness-guard technique as 135D.1, applied to the copied-evidence comparison input (§31/§38).

---

## 48. No-execution boundary

Preserved unchanged through Stage 2: no subprocess; no shell; no sockets/network; no backend invocation; no execution adapter; no command mediation; no automatic apply; no commit/push authority; no Telegram inbound; runtime remains Observed / observe / execution unavailable. Filesystem rehearsal persistence (writing candidate/generation/manifest/pointer files under `.pcae/cltr-migration/epochs/*/rehearsals/`) is explicitly the only kind of "capability" Stage 2 adds, and it is allowed only in the future Stage 2 implementation phase, not in 135Q.

---

## 49. Planned package structure

```
src/pcae/cltr/migration/rehearsal/
  __init__.py
  models.py                    # RehearsalGeneration, RehearsalManifest, dataclasses for all §9 candidates
  configuration.py             # §45/§46 flags and validation
  candidates.py                # shared candidate-derivation scaffolding, artifact_role tagging (§8)
  report_candidate.py          # §10
  metadata_candidate.py        # §11
  architecture_status_candidate.py   # §12
  checkpoint_candidate.py       # §13
  notification_candidate.py    # §14
  marker_candidate.py           # §15
  receipt_candidate.py          # §16
  disclosure.py                 # shared NON_AUTHORITY_DISCLOSURE constant (fixes F-135P-4)
  manifest.py                    # §18
  digest.py                      # §19, reuses CLTR-SCHEMA-001 canonicalization from src/pcae/cltr/canonicalization.py
  persistence.py                 # §7 namespace, atomic writes/renames
  pointer.py                     # §23
  verification.py                # §20 step 14, §19, §38
  coordinator.py                  # §20 full sequence orchestration
  recovery.py                     # §27
  status.py                       # §34 (planned command backing, not wired to CLI in this phase)
  reconciliation.py               # §35 (planned command backing, not wired to CLI in this phase)
```

Names and split follow the existing `src/pcae/cltr/migration/` (Stage 1) convention directly (`assembly.py`, `coordinator.py`, `status.py`, `reconciliation.py`, `persistence.py`, `evidence.py` already exist there with matching responsibilities) rather than inventing an unrelated structure.

---

## 50. Integration-point plan

- Stage 1 evidence becomes available: after `complete()` in Stage 1's `coordinator.py` returns for a transition (i.e., only once Stage 1's own dual-derivation and comparison has already finished).
- Authoritative legacy outputs become complete enough to compare: at the same point Stage 1's `enrich_legacy_completion` already captures `LEGACY_COMPLETION`, i.e. after legacy's existing sequential path completes within `run_finalization_transaction()`.
- Rehearsal generation assembly begins: only after both of the above, invoked as a new, optional step within `run_finalization_transaction()` gated entirely by `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` (§45) — if disabled, zero rehearsal code executes, matching Stage 1's existing gating pattern.
- Rehearsal verification occurs: synchronously within the same invocation, per §20 steps 11–14.
- Rehearsal pointer publication occurs: synchronously, §20 steps 15–17, immediately following verification, within the same governed call.
- Result evidence is persisted: §20 step 18, immediately after, before `run_finalization_transaction()` returns.

The future coordinator never runs at a point where a required field is unavailable, because it is invoked strictly after the same `_complete_stage1_migration` call site Stage 1 already uses (`finalization_transaction.py`), guaranteeing the shared input's `LEGACY_COMPLETION` stage is already bound before rehearsal candidate assembly's first step even begins.

---

## 51. Planned tests

Focused test modules (naming follows the `tests/test_cltr_migration_*.py` convention already established):

- `tests/test_cltr_rehearsal_configuration.py` — §45/§46.
- `tests/test_cltr_rehearsal_preconditions.py` — §21.
- `tests/test_cltr_rehearsal_candidate_models.py` — §9 dataclasses.
- `tests/test_cltr_rehearsal_report_candidate.py` — §10.
- `tests/test_cltr_rehearsal_metadata_candidate.py` — §11.
- `tests/test_cltr_rehearsal_architecture_status_candidate.py` — §12.
- `tests/test_cltr_rehearsal_checkpoint_candidate.py` — §13.
- `tests/test_cltr_rehearsal_notification_candidate.py` — §14/§43.
- `tests/test_cltr_rehearsal_marker_candidate.py` — §15/§44.
- `tests/test_cltr_rehearsal_receipt_candidate.py` — §16/§44.
- `tests/test_cltr_rehearsal_manifest.py` — §18.
- `tests/test_cltr_rehearsal_digest.py` — §19.
- `tests/test_cltr_rehearsal_filesystem_containment.py` — §7/§25/§47 path-traversal/symlink tests.
- `tests/test_cltr_rehearsal_atomic_pointer.py` — §23/§24.
- `tests/test_cltr_rehearsal_fault_injection.py` — §26/§52.
- `tests/test_cltr_rehearsal_recovery.py` — §27.
- `tests/test_cltr_rehearsal_idempotency.py` — §28/§29.
- `tests/test_cltr_rehearsal_quarantine.py` — §30.
- `tests/test_cltr_rehearsal_comparison.py` — §31.
- `tests/test_cltr_rehearsal_four_entry_points.py` — §39 (mirroring 135P's precedent of a single test driving all four real entry points end-to-end).
- `tests/test_cltr_rehearsal_ordinary_and_recovery_paths.py` — §40/§41.
- `tests/test_cltr_rehearsal_status_reconciliation_readonly.py` — §34/§35 backing logic (CLI wiring itself may be deferred).
- `tests/test_cltr_rehearsal_no_go_boundary.py` — §43/§48, monkeypatched subprocess/socket containment, mirroring Stage 1's existing no-go tests.

---

## 52. Fault-injection plan

Injectable boundaries, one per §20 sequence step from candidate-write onward:

- Every candidate artifact write (§9 items, one injection point per artifact type).
- Manifest write.
- Verification (both "artifact digest fails" and "cross-reference/split-brain check fails" sub-cases).
- Generation finalization (rename failure, e.g. simulated `OSError`).
- Pointer temp write.
- Atomic replace (simulated crash immediately before/after the `os.replace` call, using a monkeypatch that raises after performing the real replace, to test the "uncertain outcome, read-back reconciles" path from §26/§27).
- Result recording.

Expected state after each fault: exactly the corresponding row of §26's crash matrix — verified by asserting (a) the prior `current-rehearsal` target is unchanged unless the fault point is at or after "during replace," (b) no production path was touched, (c) the correct checkpoint/failure state is recorded, and (d) a subsequent recovery pass (§27) reaches the correct terminal state without manual intervention.

---

## 53. Acceptance criteria

Stage 2 implementation shall not be considered complete unless:

- All local candidates derive from one verified input (§6/§20).
- The complete generation verifies before visibility (§20/§24).
- Pointer update is atomic (§23).
- The prior valid rehearsal remains available on failure (§24/§26).
- A partial candidate never becomes `current-rehearsal` (§23/§24).
- No production pointer changes (§42, verified structurally by import/call-graph inspection, not just by test coverage).
- No terminal side effects occur (§17/§43/§44).
- All four entry points are covered (§39).
- Recovery is state-based (§27).
- Rejected candidates cannot succeed (§41).
- Exactly-once production behavior is unchanged (§42).
- No execution capability is introduced (§48).
- Zero unresolved Blocking defects remain (all four §3 findings resolved, per their "must resolve before Stage 2 implementation" classification).

---

## 54. Inherited-finding review

135P's four findings are dispositioned in full in §3. Below: the still-open items from 135N and 135J that bear on Stage 2.

- **135N F-135N-2** (Non-Blocking): §8.1's shared-input field list initially omitted predecessor transition identity. **Status:** resolved — confirmed present in 135O's implementation (`assembly.py` captures `predecessor_transition_id`/`successor_transition_id` per 135N §8.3's correction model). **Stage 2 relevance:** low, already closed; Stage 2's own generation identity (§6) does not itself need predecessor/successor binding beyond what the shared input already carries. **No action required.**
- **135N F-135N-3** (Non-Blocking): §35's Git-attribution row overstates present risk (wording issue only; actual attribution is explicit-list-based and fail-closed since 134E.10.1.1). **Status:** open, editorial. **Stage 2 relevance:** low — Stage 2's own commit-attribution candidate (§9 item 9) inherits the same actual (correct) attribution mechanism, not the mis-described one; the wording fix remains a 135M-document edit, not a code change. **Required resolution timing:** before or during a future "135S" editorial-hygiene pass, per 135N's own recommendation — not gating for Stage 2 implementation. **Owner phase:** 135S (as 135N already recommended) or an equivalent editorial pass. **Not reclassified as Blocking.**
- **135N — 5 unnamed Non-Blocking table rows** (terminology gloss gap; 135D.1 incident-description mismatch; "narrative-prose-parsing" mischaracterization; wrong-subsection citation; no explicit mismatch-class precedence rule): the last of these (**no explicit precedence rule for co-occurring mismatch classes**) is Stage-2-relevant — §22's mismatch policy in this document adopts 135N's own recommendation ("135O should allow multi-class recording") by requiring every mismatch of every class to be preserved (§22's "every mismatch, of every class, is preserved" rule), closing this item for Stage 2's purposes. The remaining four are purely editorial, non-Stage-2-relevant, deferred to a future editorial pass.
- **135J F3** (Non-Blocking): `delivery_recorded_bookkeeping_incomplete` never defined in prose. **Status:** open. **Stage 2 relevance:** low-moderate — Stage 2's receipt candidate (§16) and evidence record (§33) use a distinct rehearsal-scoped vocabulary specifically to avoid ambiguity with this and other production `reconciliation_outcome` values; this finding does not block Stage 2 but the prose gap should be closed before or during Stage 3 contract work (135S), since Stage 3's CLTR-authoritative reconciliation will need this value fully specified. **Owner phase:** 135S.
- **135J F4** (Non-Blocking): the 37-invariant crosswalk doesn't enumerate all 37 IDs in one table. **Status:** open, editorial. **Stage 2 relevance:** none directly (Stage 2 reuses Stage 1's invariant evaluators unchanged). **Owner phase:** unscheduled editorial pass, non-gating.
- **135J F5** (Non-Blocking/context): three-outcome commit-ownership verification model and atomic `latest.md`/`latest.json` publication remain unimplemented. **Status:** partially closes with Stage 2 — 135M §20 explicitly states atomic publication "post-cutover, no component may independently publish a 'latest' artifact outside the generation transaction," which is exactly what Stage 2's atomic rehearsal pointer (§23) begins to prove out (for the rehearsal namespace only, not yet for production). **Stage 2 relevance:** high, this is precisely what Stage 2 exists to rehearse. **Required resolution timing:** the *rehearsal* mechanism must prove this pattern during Stage 2; the *production* atomic-publication cutover itself remains Stage 3's responsibility (135M §20/§21), not Stage 2's. **Not reclassified as Blocking for Stage 2** (Stage 2 rehearses the mechanism; it does not need production's own atomic-publication gap closed first, since Stage 2 never touches production pointers at all).

No inherited finding has been silently dropped; every item above carries an explicit disposition and owner phase or "non-gating, unscheduled" status.

---

## 55. Risk register

| Risk | Likelihood | Impact | Prevention | Detection | Response | Acceptance criterion |
|---|---|---|---|---|---|---|
| Rehearsal pointer mistaken for authority | Low | High | §7 namespace separation, §23 naming discipline, §8 disclosure fields | Static grep for any production code path reading `current-rehearsal`; code review | Remove/rename the offending reference | Zero production code paths reference `current-rehearsal` |
| Candidate artifact mistaken for production output | Low | High | §8 terminology, §9 inventory, disclosure fields on every artifact | Manifest/artifact schema requires `non_authority_disclosure` and `artifact_role` on every artifact; test asserts presence | Reject artifacts missing the field at write time | 100% of candidate artifacts carry the disclosure field, enforced by test |
| Incomplete candidate visibility | Low | Medium | §20/§24 — visibility gated on full verification | Fault-injection tests (§52) | Quarantine incomplete generation | §52's fault-injection suite passes for every injection point |
| Split-brain generation | Low | High | §38 cross-reference checks | Verification step (§20 step 14) | Block publication, quarantine | §38 test suite covers every listed split-brain scenario |
| Stale Stage 1 evidence | Low | Medium | §21 precondition, staleness-guard technique (135D.1) | Precondition check | Reject rehearsal attempt | Precondition tests cover staleness explicitly |
| Wrong input revision | Low | High | §6 identity binds `final_input_revision_digest` | Digest verification | Reject/quarantine | §19/§29 tests cover digest mismatch |
| Mismatch normalization overclaiming a match | Low | High | §22/§31 explicit expected-difference classification, never fabricated match | Comparison test suite (§51) asserts no field is silently marked matching when it structurally cannot be | Correct classification logic, add regression test | §31 comparison tests include at least one case per representation kind with an unattempted-external-effect field |
| External-effect atomicity overclaim | Low | High | §24/§25 explicit scope/assumption statements | Documentation review (135R) | Revise document language | 135R confirms no overclaiming language present |
| Duplicate authoritative terminal effects | Very low | Critical | §42 — no code path touches production completion mechanisms | Import/call-graph static check + no-go test | Remove offending call | §42/§48 no-go tests pass |
| Pointer publication uncertainty | Medium (inherent to crash timing) | Medium | §26/§27 read-back-and-reconcile model | Fault injection (§52) | Reconcile from ground truth, never blind retry | §52 "during replace" fault-injection case passes |
| Invalid rollback semantics | Low | Medium | §36/§37 explicit scope and roll-forward preference | Test suite | Correct rollback logic before merge | §36 tests cover all listed rollback scenarios |
| Recovery inference (guessing state from titles/history) | Low | High | §27 explicit state-based-only recovery contract | Code review; test asserting no `git log`/title parsing in recovery module | Remove inference code path | Recovery module has zero dependencies on Git history or document titles |
| Quarantine bypass | Very low | High | §23 explicit rejection of quarantined targets, no override flag | Test suite | Remove any override path found | §30 quarantine tests confirm no bypass exists |
| Feature-flag confusion | Low | Medium | §45/§46 explicit separate flags, fail-closed invalid combinations | Configuration test suite | Correct flag validation logic | §46 invalid-configuration tests cover every listed case |
| Entry-point drift (one entry point behaving differently) | Low | Medium | §39 shared coordinator, no entry-point branching beyond the label | Test suite (§39 four-entry-point test) | Fix drift, add regression test | Single test drives all four entry points identically |
| Historical evidence rewrite | Very low | High | §7 append-only `generations/`/`failures/` | File-permission enforcement + code review | Restore from evidence, treat rewrite as an incident | No code path opens a finalized generation file for writing |
| Premature Stage 3 assumptions | Low | High | §4/§21 explicit "no cutover approval implied" language | 135R review | Revise document | 135R confirms no Stage 3 authority implication present |

---

## 56. Cross-reference matrix

| Stage 2 contract rule | CLTR-001 | CLTR-SCHEMA-001 v1.0.1 | 135D | 135H | 135H.2 | 135M | 135N | 135O | 135P | PFN-001 | PFR-001 | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| §4 Stage 2 scope (rehearsed/not rehearsed) | — | — | — | — | — | §6, §21 | — | — | §55 recommendation | — | — | Stage 2 clarification |
| §5 authority matrix | §4.1 | §5 | — | — | — | §6 | — | (production_authority=LEGACY) | — | — | — | Inherited semantic rule |
| §6 rehearsal generation identity | §5.1 | §16 | — | — | — | §17, §20, §40 | design-B resolution | transition_identity.py | — | — | — | Rehearsal encoding |
| §7 rehearsal namespace | — | §16 | — | — | — | — | — | persistence.py precedent | — | — | — | Implementation guidance |
| §8 terminology | §4.1 (roles) | §5 (roles) | — | — | — | — | — | — | F-135P-4 | — | — | Rehearsal encoding |
| §9 candidate inventory | §6.2 | §5 | — | — | — | §18 | — | — | F-135P-3 (item 9) | — | — | Rehearsal encoding |
| §10 report candidate | §5.1 | §5, §15 | — | — | — | — | — | — | — | — | §3, §4 | Rehearsal encoding |
| §11 metadata candidate | §5.1 | §5 | — | — | — | — | — | — | — | — | — | Rehearsal encoding |
| §12 Architecture Status candidate | — | §5 | — | — | — | — | F-135N-3 caution | — | — | — | — | Rehearsal encoding |
| §13 checkpoint candidate | — | §5, §17 | — | — | §recovery model | §21 | — | — | — | — | — | Rehearsal encoding |
| §14 notification-intent candidate | — | §19 | — | — | — | §19 | — | — | — | §8 (idempotency key) | — | Rehearsal encoding |
| §15 marker candidate | — | §5, §19 | — | — | — | — | — | — | — | — | — | Rehearsal encoding |
| §16 receipt candidate | — | §5, §18 | — | §recovery model | §7 (`reconciliation_outcome`) | — | — | — | — | — | — | Rehearsal encoding |
| §17 external-effects boundary | — | §19 | — | — | — | §19 | — | — | — | §4, §5, §6 | — | Inherited semantic rule |
| §18 manifest | — | §14, §15, §16 | — | — | — | §20 | — | — | F-135P-4 | — | — | Stage 2 clarification |
| §19 generation digest | — | §15 | — | — | — | — | — | — | — | — | — | Inherited semantic rule |
| §20 assembly sequence | — | §17 | — | — | — | §21 | — | coordinator.py pattern | — | — | — | Implementation guidance |
| §21 preconditions | — | §2.7 | — | — | — | §7 (Stage 1→2 gate) | — | configuration.py pattern | F-135P-1, -3, -4 | — | — | Stage 2 clarification |
| §22 mismatch policy | — | §21.4 | — | — | — | §12, §13 | precedence-rule recommendation | comparison.py pattern | F-135P-2 | — | — | Stage 2 clarification |
| §23 rehearsal pointer | — | §16 | — | — | — | §22 | — | — | — | — | — | Rehearsal encoding |
| §24 atomicity scope | — | §17 | — | — | — | §19 | — | — | — | — | — | Stage 2 clarification |
| §25 filesystem assumptions | — | — | — | — | — | — | — | persistence.py precedent | — | — | — | Implementation guidance |
| §26 crash matrix | — | §17, §18 | temporal/state models | — | recovery hardening | §23–§26 | — | — | — | — | — | Stage 2 clarification |
| §27 recovery | — | §18 | staleness guard | — | exactly-once promotion | §25 | — | — | — | — | — | Inherited semantic rule |
| §28 idempotency | — | — | — | — | exactly-once model | §26 | — | transition_identity.py | — | — | — | Inherited semantic rule |
| §29 conflicting replay | — | §2.7 | — | — | — | — | — | replay lookup registry | — | — | — | Stage 2 clarification |
| §30 quarantine | — | §18 | overlay flags | — | — | — | — | — | — | — | — | Stage 2 clarification |
| §31 rehearsal comparison | — | §21.4 | — | — | — | §12 | — | comparison.py | F-135P-2 | — | — | Stage 2 clarification |
| §32 progression eligibility | — | — | — | — | — | §14, §15 | — | — | — | — | — | Stage 3 prerequisite |
| §33 evidence record | — | — | — | — | — | §17 | — | evidence.py pattern | — | — | — | Implementation guidance |
| §34/§35 status/reconciliation plans | — | — | — | — | reconcile precedent | §46, §47 | — | status.py/reconciliation.py | — | — | — | Implementation guidance |
| §36/§37 rollback/roll-forward | — | — | replay/retry model | — | — | — | — | — | — | — | — | Stage 2 clarification |
| §38 split-brain prevention | §4.1 | — | state-machine model | — | — | — | — | — | — | — | — | Inherited semantic rule |
| §39 four entry points | — | — | — | §integration plan | — | §21 | four-entry-point verification | wiring | four-entry-point test | — | — | Inherited semantic rule |
| §40 ordinary/recovery paths | — | §18 | recovery model | 135H.1 | recovery hardening | — | — | recovery classification | F-135P-1 | — | — | Stage 2 clarification |
| §41 135H.1 escape resistance | — | — | — | 135H.1 | — | — | — | — | — | §4 | — | Stage 3 prerequisite |
| §42 exactly-once | — | — | — | — | exactly-once promotion | §26 | — | — | — | §8 | — | Inherited semantic rule |
| §43 notification isolation | — | §19 | — | — | — | §19 | — | no-go tests | — | §4, §5 | — | Inherited semantic rule |
| §44 marker/receipt isolation | — | §5 | — | — | — | — | — | — | — | — | — | Inherited semantic rule |
| §45/§46 feature configuration | — | — | — | — | — | §42 | — | configuration.py pattern | — | — | — | Implementation guidance |
| §47 security/containment | — | — | — | — | — | — | — | — | — | — | — | Implementation guidance |
| §48 no-execution boundary | — | — | — | — | — | — | — | no-go tests | — | — | — | Inherited semantic rule |

No unsupported semantic invention was identified: every rule above traces to an inherited semantic rule, an explicit 135M/135N clarification, a rehearsal-specific encoding of an already-frozen concept, implementation guidance following existing repository convention, or an explicit Stage 3 prerequisite deferred, not decided, by this document.

---

## 57. Explicit non-goals

135Q does not: implement Stage 2; modify production source; modify production tests; create rehearsal generations; create rehearsal pointers; add a Stage 2 CLI; implement atomic pointer replacement; modify production pointers; modify report generation; modify completion metadata; modify Architecture Status; modify checkpoint behavior; modify notification behavior; modify markers; modify receipts; cut over authority; demote legacy authority; retire legacy authority; add execution; add backend invocation; add shell mediation; add Telegram inbound control.

---

## 58. Governance results

- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean.
- `pcae push check`: clean (nothing to push, prior to this phase's own commit).
- `pcae runtime inspect`: Observed / observe / execution unavailable.
- `pcae notify status`: Telegram configured, enabled, outbound-only.
- `pcae phase-report show --latest`: 135P canonical report present, consistent.
- `pcae phase-report reconcile --phase-id 135P`: reconciled, mutation none (read-only).
- No production source file under `src/` was modified. No production test file was modified. Only `docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_CONTRACT_AND_IMPLEMENTATION_PLAN.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, and `tasks/DONE.md` were changed, plus this phase's task contract.
- Inherited evidence, not rerun: 135P's 101/101 combined migration tests, 386/386 combined CLTR tests, 117/117 affected finalization regressions, 4391/4391 Fast Green, cited as evidence of record for the unchanged production/Stage-1 codebase.

---

## 59. Stage 2 implementation-readiness conclusion

This document freezes a complete, internally consistent Stage 2 contract and implementation plan. Zero unresolved Blocking gaps remain for the planning phase itself. Four inherited findings (F-135P-1, F-135P-3, F-135P-4, and the `EXPECTED_REPRESENTATION_DIFFERENCE` half of F-135P-2) are explicitly reclassified as Blocking prerequisites for Stage 2 *implementation* (§3) — not for this contract-freeze phase, and not for continued Stage 1 operation, which is unaffected. Every one of the 45 required contract areas (§4–§48) is addressed with a concrete, testable rule; the planned package structure, integration points, test plan, fault-injection plan, and acceptance criteria (§49–§53) give an implementer a complete, unambiguous starting point. No Stage 2 implementation, rehearsal generation, rehearsal pointer, production pointer change, authority cutover, legacy demotion, legacy retirement, or execution capability was introduced by 135Q.

---

## 60. Recommended next phase

**135R — Atomic Publication Rehearsal Contract Verification.** 135R must independently re-derive and verify this Stage 2 contract — including re-locating and re-reading CLTR-001, CLTR-SCHEMA-001 v1.0.1, 135D, 135H/135H.2, 135M, 135N, 135O, 135P, PFN-001, and PFR-001 firsthand rather than relying on this document's summaries — before any Stage 2 implementation begins. 135Q does not begin Phase 135R.
