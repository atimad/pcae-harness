# Phase 137Q — Canonical Phase ID Parsing Contract Freeze

## Purpose

Phase 137Q transforms the approved Phase 137P Canonical Phase ID Parsing
Architecture into CPIPC-001 v1.0 (Canonical Phase ID Parsing Contract),
the immutable, normative contract governing all Phase ID parsing
throughout PCAE.

This phase is contract-freeze-only. It does not implement a parser,
modify any existing regex or comparison function, migrate any consumer,
or change runtime, lifecycle, or governance behavior.

Runtime remains:

- State: Observed
- Maximum capability: observe
- Execution availability: unavailable

## Governing authority

Treated as authoritative for this freeze, per the governing task brief:

- Phase 137P — Canonical Phase ID Parsing Architecture
  (`docs/PHASE_137P_CANONICAL_PHASE_ID_PARSING_ARCHITECTURE.md`)
- PFR-001
- Canonical Lifecycle Architecture (134A–134F)
- Whole Lifecycle Verification (135A–135Z)
- Stage 3 Lifecycle Architecture (136A–136Z)

The contract in this phase derives its content from Phase 137P's approved
architecture. It does not redesign that architecture.

## Contract Freeze Context

Phase 137P independently inventoried fifteen distinct, mutually
disagreeing Phase ID recognition/comparison definitions across ten files
in `src/pcae/`, established the root cause (no shared authority — every
call site independently reinvents "interpret a Phase ID"), and defined
the canonical architecture: a single grammar (§4), a single canonical
representation (§5), exclusive parser ownership (§3, §10), parsing and
comparison semantics (§6–§7), a conceptual API surface (§8), a closed
error taxonomy (§9), and a per-consumer lifecycle-integration inventory
(§10) — all issued architecture-only, with no implementation authorized.

Phase 137Q freezes that architecture as a binding contract, in the same
normative-requirement style already established by this repository's
prior contract freezes (e.g. `TAMC-001`, `docs/contracts/
TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`), so a future
implementation phase (137R) has one unambiguous specification to
implement against, and a future independent verification phase (137S)
has one specification to verify against.

## Deliverable

`docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md` — CPIPC-001 v1.0.

The contract freezes, as normative `SHALL`/`SHALL NOT` requirements
(CPIPC-REQ-001 through CPIPC-REQ-075):

- **Scope** — every consumer category Phase 137P §2.1/§10 inventoried,
  and any future equivalent consumer.
- **Terminology** — Phase ID, series, branch, exceptional branch,
  subphase segment, `PhaseId` value, `normalized_text`,
  `comparison_identity`, token scanner, "not comparable."
- **Canonical grammar** (§4) — the full EBNF and whole-string form frozen
  without modification from Phase 137P §4.2, plus supported, reserved,
  and invalid form classification and case-sensitivity rules.
- **Canonical representation** (§5) — the seven-field semantic model,
  with `comparison_identity` and `serialization_identity` bound to equal
  `normalized_text` in content, by requirement, not convention.
- **Parser ownership** (§6) — the highest-priority section: exactly one
  subsystem owns interpretation; no lifecycle component may parse,
  define grammar, normalize, or compare independently.
- **Parser responsibilities** (§7) — what the parser SHALL and SHALL NOT
  own, including an explicit prohibition on the parser performing its
  own file/repository access.
- **Parser API contract** (§8) — `parse`, `is_valid`, `normalize`,
  `format`, `validate`, token scanning, and comparison helpers, specified
  as observable behavior only.
- **Parsing semantics** (§9) — whitespace, case, normalization,
  acceptance/rejection, ambiguity handling, and an explicit prohibition
  on heuristic parsing.
- **Comparison semantics** (§10) — equality, branch-aware rollover
  ordering, the exceptional-branch exclusion, the mandatory
  "not comparable" outcome, and an explicit prohibition on introducing an
  artificial total ordering.
- **Error taxonomy** (§11) — the closed nine-kind set frozen from Phase
  137P §9, each with a fixed, deterministic meaning.
- **Compatibility guarantees** (§12) — mandatory backward compatibility
  as a grammar property, plus the named reserved-form extension points.
- **Migration obligations** (§13) — mandatory migration for every
  existing consumer, no flag-day cutover, per-consumer replacement, and
  outright removal (not deprecation) of duplicate grammar definitions.
- **Lifecycle integration** (§14) — the ten-consumer-group inventory
  frozen without modification from Phase 137P §10, each mapped to the
  specific canonical-parser operations it SHALL delegate to.
- **Extensibility rules** (§15) — additive-only, centrally-implemented,
  automatically-inherited grammar growth; no consumer-specific grammar
  extensions.
- **Security requirements** (§16) — deterministic, side-effect-free,
  stateless, thread-safe, runtime-neutral, authority-neutral; no
  filesystem, repository, network, or governance access.
- **Compliance requirements** (§17) — the eleven-area evidence checklist
  a future implementation (137R) must satisfy.
- **Traceability** (§18) — the explicit 137P → CPIPC-001 → 137R → 137S
  chain, with a requirement that no architectural decision from 137P be
  lost or silently altered.
- **Non-goals** (§19) — restated from Phase 137P §16, including the four
  risks Phase 137P §15 left open and the still-unrepaired
  `repository_transition_integration.py` truncation defect.

## Validation

Independent derivation check performed against Phase 137P before freeze:

- Every architectural principle in Phase 137P §3 is represented as a
  `SHALL`/`SHALL NOT` requirement in CPIPC-001 §6–§7 (ownership,
  types-not-strings, fail-closed-on-ambiguity, single-place grammar
  evolution, lifecycle-inert parser).
- The grammar in CPIPC-001 §4 is copied verbatim (EBNF and whole-string
  form) from Phase 137P §4.2, with no semantic drift; supported/
  reserved/invalid classification (§4.3 there, §4.1–§4.3 here) and case
  rules (§4.4 there, §4.4 here) are preserved.
- Comparison semantics in CPIPC-001 §10 preserve every rule from Phase
  137P §7: series-only comparability, spreadsheet-column branch
  rollover, exceptional-branch exclusion, element-wise numeric-first
  subphase comparison, and the mandatory "not comparable" outcome —
  including the explicit prohibition on an artificial total ordering,
  which this contract adds as CPIPC-REQ-042 to make Phase 137P §7's
  prose rule independently enforceable.
- The error taxonomy in CPIPC-001 §11 reproduces all nine kinds from
  Phase 137P §9 verbatim, with no kind added, removed, or renamed.
- The lifecycle-integration table in CPIPC-001 §14 reproduces all ten
  consumer rows from Phase 137P §10 verbatim, including the still-open
  `repository_transition_integration.py` truncation defect note.
- No implementation decision (class definitions, function signatures,
  a specific regex engine, a specific programming language construct)
  appears anywhere in CPIPC-001, matching Phase 137P's own architecture-
  only scope (§16 there) and this phase's own governing brief.
- Every inventoried parser consumer (fifteen call sites across ten files,
  Phase 137P §2.1) is covered by CPIPC-001's ownership requirements
  (§6) and lifecycle-integration inventory (§14): the fifteen call sites
  map onto the ten consumer groups in §14 exactly as Phase 137P §10
  grouped them.

No semantic drift, no lost architectural decision, and no leaked
implementation decision was found.

## Non-Goals

This phase does not:

- Implement, replace, or delete any regex, module, class, or function.
- Migrate any existing Phase ID parsing consumer.
- Introduce any execution capability.
- Change the runtime state (`Observed` / `observe` / `unavailable`
  throughout).
- Change any existing public CLI behavior or output.
- Resolve the risks Phase 137P §15 recorded.
- Decide the specific order in which the ten lifecycle consumer groups
  are migrated.
- Repair `repository_transition_integration.py`'s open truncation
  defect.

## Governance

This phase used governed PCAE workflows only (`pcae task new`, `pcae
phase start`, `pcae phase complete`). No raw `git commit` or `git push`
was used outside the governed commit/push flow. No production code was
modified.

## Success Criteria

- [x] CPIPC-001 v1.0 is internally consistent.
- [x] All architectural decisions from Phase 137P are preserved (see
      Validation, above).
- [x] Parser ownership is frozen as a normative `SHALL` (CPIPC-001 §6).
- [x] Grammar is fully specified (CPIPC-001 §4).
- [x] Comparison semantics are fully frozen, including the explicit
      prohibition on an artificial total ordering (CPIPC-001 §10).
- [x] Compatibility guarantees are explicit (CPIPC-001 §12).
- [x] Migration obligations are defined (CPIPC-001 §13).
- [x] Implementation independence is preserved — no parser code, no
      migration, no production behavior change.

## Recommended Next Phase

**137R — Canonical Phase ID Parser Implementation**

Implement the canonical parser defined by CPIPC-001 v1.0, migrate the
inventoried parser consumers (CPIPC-001 §14) to the shared
implementation while preserving behavior, eliminate duplicated parsing
logic, and verify that all historical Phase IDs remain compatible with
no runtime, lifecycle, or governance regressions.
