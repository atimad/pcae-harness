# Canonical Phase ID Parsing Contract

## Contract identity and status

**Contract:** CPIPC-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 137Q — Canonical Phase ID Parsing Contract Freeze
**Architecture basis:** Phase 137P — Canonical Phase ID Parsing Architecture

CPIPC-001 v1.0 is the sole normative authority governing Phase ID grammar,
parser ownership, parser responsibilities, normalization, comparison
semantics, validation, serialization, error handling, and lifecycle
integration for the canonical Phase ID parser. Every future implementation
of, or consumer of, Phase ID parsing SHALL conform to this contract.

The Phase 137P architecture is the approved design basis for this contract.
This contract derives every requirement below from that architecture; it
does not redesign it. Where this contract and the Phase 137P architecture
document differ in force, this contract is normative for implementation
purposes, and any such difference is itself a defect to be resolved by a
governed contract revision, not by silently preferring one document over
the other in practice.

This is contract text only. It does not implement a parser, does not
replace or modify any existing regex or comparison logic, does not migrate
any consumer, and does not change runtime, lifecycle, or governance
capability.

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative. `SHALL` and `MUST` state binding
requirements; `SHALL NOT` and `MUST NOT` state binding prohibitions;
`SHOULD` states a requirement from which deviation requires explicit
governed justification; and `MAY` states a permission within all other
requirements.

A **consumer** is any component, module, function, or lifecycle subsystem
that recognizes, validates, normalizes, formats, serializes, deserializes,
compares, or orders a Phase ID, or that extracts a candidate Phase ID
substring from free text. A component that also owns an independently
governed side effect (reporting, notification, governance decision, file
mutation) SHALL keep that side effect outside its Phase ID parsing
operation.

## 1. Purpose

CPIPC-REQ-001: Every present and future Phase ID parsing implementation and
every consumer of Phase ID text SHALL conform to the grammar, ownership,
responsibility, semantic, error-handling, compatibility, migration, and
lifecycle-integration requirements of this contract.

CPIPC-REQ-002: This contract exists to end the defect class independently
inventoried by Phase 137P (§2): fifteen distinct, independently drifting
regex/comparison definitions across ten files, none byte-identical, with
no shared authority. CPIPC-001 is the single normative specification every
implementation and every consumer is measured against.

CPIPC-REQ-003: Conformance with CPIPC-001 grants no execution, lifecycle,
governance, or runtime capability. It governs interpretation of text only.

## 2. Scope

CPIPC-REQ-004: This contract applies to recognition, validation,
normalization, formatting, serialization, comparison, and ordering of PCAE
Phase ID text, and to extraction of a candidate Phase ID substring from
free text (titles, commit subjects, report prose, `PROJECT_STATUS.md`
content).

CPIPC-REQ-005: This contract applies, without limitation, to every
consumer category identified in Phase 137P §2.1 and §10, and to any future
consumer performing an equivalent operation:

1. canonical-title Phase ID extraction (`core/phase_reports.py`);
2. Phase-ID shape parsing for comparison (`core/phase_reports.py`);
3. commit-subject Phase ID token scanning (`core/phase_reports.py`);
4. `PROJECT_STATUS.md` current-phase code extraction (`core/check.py`);
5. architecture-status Phase ID parsing and ordering
   (`core/architecture_status.py`);
6. bootstrap phase-ambiguity detection (`core/context.py`);
7. task-state-alignment phase-code recognition (`core/agent.py`);
8. session-identity-token phase-ID grammar recognition (`core/agent.py`);
9. CLTR prototype phase identity validation
   (`cltr_prototype/identity.py`);
10. CLTR prototype title-token scanning
    (`cltr_prototype/compatibility.py`);
11. typed Phase Identity wrapper construction
    (`cltr/authority/identity.py`);
12. phase-queue Phase ID validation (`commands/phase.py`);
13. commit-message phase-range expansion (`commands/phase.py`);
14. push-command done-task Phase ID token scanning (`commands/push.py`);
15. repository-transition-integration Phase ID text parsing
    (`core/repository_transition_integration.py`).

CPIPC-REQ-006: Scope is independent of surface or implementation language.
It includes CLI, reporting, bootstrap, session-state, check/health,
governance, phase-report, and push-command consumers, and any future
tooling that recognizes, compares, or formats Phase ID text.

CPIPC-REQ-007: A wrapper, adapter, cache, renderer, or downstream consumer
of a Phase ID parsing result SHALL NOT evade this contract by re-deriving
Phase ID structure independently. An output remains governed by this
contract while it carries or derives from Phase ID recognition.

## 3. Terminology

CPIPC-REQ-008: The following terms are normative and SHALL be used with
exactly the meaning given here by every conforming implementation and
every document that describes one:

- **Phase ID** — text denoting a PCAE phase, subject to the grammar in
  §4.
- **canonical parser** — the single component that owns recognition,
  validation, normalization, formatting, comparison, and error
  classification for Phase ID text, per §6.
- **series** — the leading one-or-more-digit numeric component of a Phase
  ID (the `series` grammar production, §4.2).
- **branch** — the one-or-more-letter component immediately following
  `series` (the `branch` grammar production, §4.2), canonically
  uppercased.
- **exceptional branch** — the existing `"X"` branch convention (e.g.
  `113X.1`, `113X.2`) denoting a self-contained excursion not comparable
  to a mainline lettered branch in the same series (§10).
- **subphase segment** — a single dotted component following `series` and
  `branch`, either a `numeric-segment` or a `letter-segment` (§4.2).
- **numeric-segment** — a subphase segment of digits with an optional
  trailing letters suffix (e.g. `10`, `2`, `1V`).
- **letter-segment** — a subphase segment of letters only, with no
  leading digit (e.g. the `.R` repair-suffix form).
- **PhaseId value** — the canonical, immutable parsed representation of a
  successfully recognized Phase ID, per §5.
- **normalized_text** — the canonical, uppercased, `.`-joined
  serialization of a `PhaseId` value.
- **comparison_identity** — the `(series: int, branch: str, subphase:
  tuple)` tuple used for equality and ordering, per §10.
- **token scanner** — the distinct, explicitly-named operation that
  locates a candidate Phase ID substring inside free text and hands that
  substring to `parse`; it is not part of `parse` and has no independent
  acceptance rule (§8).
- **not comparable** — the first-class outcome of a comparison between
  two Phase IDs that do not share a comparable family (different
  `series`, or one mainline and one exceptional branch in the same
  series), per §10.

## 4. Canonical Grammar

CPIPC-REQ-009: The following grammar, frozen without modification from
Phase 137P §4.2, is the sole normative grammar for Phase ID recognition.
No consumer SHALL interpret Phase ID text under any other grammar, any
narrower grammar, or any wider grammar.

```ebnf
phase-id        = series , branch , { "." , subphase-segment } ;

series          = digit , { digit } ;
                  (* one or more decimal digits; no leading-zero
                     restriction is imposed *)

branch          = letter , { letter } ;
                  (* one or more ASCII letters; no upper bound on
                     length is imposed *)

subphase-segment
                = numeric-segment
                | letter-segment ;

numeric-segment = digit , { digit } , [ letter , { letter } ] ;
                  (* a dotted sub-phase number with an optional trailing
                     verification/repair-letter suffix *)

letter-segment  = letter , { letter } ;
                  (* a dotted segment that is letters only, with no
                     leading digit *)

digit           = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
letter          = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
```

Whole-string form (`fullmatch` target), provided for direct implementation
reference without committing to a particular regex engine's syntax:

```
^ [0-9]+ [A-Za-z]+ ( \. ( [0-9]+ [A-Za-z]* | [A-Za-z]+ ) )* $
```

### 4.1 Supported forms

CPIPC-REQ-010: **Supported** is exactly the set of text accepted by §4's
grammar. This set is the union of every form independently confirmed
historically valid by Phase 137P §2.1 and §4.1. No implementation SHALL
accept a narrower or wider set as "supported."

### 4.2 Reserved forms

CPIPC-REQ-011: The following forms are **reserved**: syntactically
plausible under a future grammar extension, not accepted today, and not
to be silently coerced into a nearby supported form:

- a bare numeric series with no branch letter at all (`"134"`);
- a leading-zero series (`"007A"`).

CPIPC-REQ-012: A future revision of this contract, not an implementation
detail and not an ad hoc caller decision, SHALL decide whether a reserved
form is promoted to supported or fixed as permanently invalid. Until such
a revision exists, an implementation SHALL classify a reserved-form input
as `reserved_syntax` or `missing_branch` per the error taxonomy in §11 and
SHALL NOT accept it as valid.

### 4.3 Invalid forms

CPIPC-REQ-013: Every input that is neither supported (§4.1) nor reserved
(§4.2) is **invalid**, including: the empty string; whitespace-only text;
a branch with no series (`"A"`); a subphase segment mixing digits and
letters in an order other than digits-then-letters (`"134E.V1"`); any
character outside `[0-9A-Za-z.]`; a leading or trailing `.`; and two
consecutive `.` separators.

### 4.4 Case sensitivity

CPIPC-REQ-014: The grammar accepts either letter case at the lexical
level. Recognition SHALL always be immediately followed by uppercasing;
there is no supported path that yields a non-uppercased `PhaseId` value.
Two inputs differing only in letter case SHALL be recognized as the same
Phase ID.

## 5. Canonical Representation

CPIPC-REQ-015: A successfully parsed Phase ID SHALL be representable by
exactly the following semantic fields. This contract specifies field
semantics only; it does not prescribe a class definition, type system, or
implementation language construct.

| Field | Meaning | Derived from |
|---|---|---|
| `series` | The numeric phase-family identity | `series` production |
| `branch` | The mainline branch letters, canonically uppercased | `branch` production |
| `subphase` | An ordered sequence of parsed segments, each either `(number, letters)` for a numeric-segment or `(None, letters)` for a letter-segment | each `subphase-segment` |
| `normalized_text` | The canonical serialization: uppercased, `.`-joined, exactly reproducing `series + branch + subphase` with no incidental whitespace | derived, not stored input |
| `comparison_identity` | `(series: int, branch: str, subphase: tuple)`, numeric sub-components compared as integers, not strings | derived |
| `serialization_identity` | The wire-form string used when a Phase ID is written back into a report, filename, or commit subject; identical in content to `normalized_text` | derived |
| `source_text` | The original, unnormalized text that was parsed, retained for diagnostics/error messages only | input, as-provided |

CPIPC-REQ-016: `comparison_identity` and `serialization_identity` SHALL be
equal in content to `normalized_text`. An implementation SHALL NOT
maintain them as independently computed values. This requirement exists
specifically because this repository's own defect history (Phase 137P
§2) is the result of comparison and serialization drifting into separate
representations across separate files.

CPIPC-REQ-017: `source_text` SHALL NOT be used for comparison, equality,
or serialization. It exists for diagnostics only.

## 6. Parser Ownership

This section states the highest-priority requirement of this contract.

CPIPC-REQ-018: Exactly one subsystem — the canonical parser — SHALL own
interpretation of Phase ID text: recognition, validation, normalization,
formatting, comparison support, and serialization. No second
implementation of any part of this list SHALL exist anywhere in the PCAE
codebase.

CPIPC-REQ-019: Every lifecycle subsystem that needs to recognize,
validate, normalize, format, or compare a Phase ID SHALL consume the
canonical parser's authority for that operation. No lifecycle component
SHALL implement independent Phase ID parsing logic.

CPIPC-REQ-020: No lifecycle component SHALL define an independent Phase
ID grammar, whether by regular expression, hand-written scanner, or any
other mechanism.

CPIPC-REQ-021: No lifecycle component SHALL normalize a Phase ID
independently of the canonical parser's normalization operation (§9).

CPIPC-REQ-022: No lifecycle component SHALL compare Phase IDs
independently of the canonical parser's comparison operations (§10),
including by ad hoc string-prefix checks, hand-rolled tuple comparisons,
or locally reimplemented branch-letter-count assumptions.

CPIPC-REQ-023: Parser ownership is exclusive; it is not divided by
consumer category, by lifecycle subsystem, by file, or by operation.
Recognition alone SHALL NOT be centralized while comparison, normalization,
or formatting remains distributed.

CPIPC-REQ-024: Once a piece of text has been recognized as a Phase ID, it
SHALL be represented as a canonical, immutable `PhaseId` value (§5), not
passed onward as a bare string that invites re-parsing by a downstream
consumer.

## 7. Parser Responsibilities

CPIPC-REQ-025: The canonical parser SHALL own, and SHALL be the sole
owner of:

- parsing (recognition against the grammar in §4);
- validation (classification of success or a specific error, §11);
- normalization (case and structural canonicalization, §9);
- formatting (canonical text production from a structured value, §8);
- comparison support (equality and ordering primitives, §10);
- serialization (canonical text production for reports, filenames, and
  commit subjects, §5, §8);
- error generation (classified failure per the taxonomy in §11).

CPIPC-REQ-026: The canonical parser SHALL NOT own, and no implementation
SHALL extend it to own:

- lifecycle decisions (which phase is "current," "next," "stale," or
  "governed");
- governance determinations;
- reporting;
- notifications;
- authorization;
- repository mutation, including reading or writing
  `PROJECT_STATUS.md`, `tasks/`, or any other repository file.

CPIPC-REQ-027: A consumer that reads a file to obtain candidate Phase ID
text (e.g. `PROJECT_STATUS.md`'s current-phase extraction, bootstrap's
ambiguity detection) SHALL perform that file access itself and SHALL hand
only the resulting text to the canonical parser. The canonical parser
SHALL NOT perform the file access on the consumer's behalf.

CPIPC-REQ-028: Lifecycle judgments built on top of a parsed Phase ID
(whether a given Phase ID is active, next, stale, governed, or
authorized) remain the responsibility of the calling lifecycle subsystem.
This contract governs recognition, validation, normalization, formatting,
and comparison only; it does not, and no future revision of the canonical
parser under this contract may, absorb lifecycle judgment.

## 8. Parser API Contract

CPIPC-REQ-029: The canonical parser SHALL expose, at minimum, operations
observably equivalent to the following. This contract freezes observable
behavior only; it does not freeze implementation signatures, argument
order, or a specific programming-language calling convention.

- **`parse`** — the sole entry point that turns `source_text` into either
  a canonical `PhaseId` value or a classified error (§11). Every other
  operation is built on this one.
- **`is_valid`** — a boolean convenience defined strictly as "did `parse`
  succeed." It SHALL NOT be implemented as an independent check with its
  own acceptance logic.
- **`normalize`** — given a successfully-parsed `PhaseId`, or raw text
  that parses successfully, returns `normalized_text`.
- **`format`** — given a `PhaseId` value however obtained (constructed
  from known components, not only round-tripped from `parse`), produces
  its canonical text. `normalize` and `format` SHALL converge on the same
  output for the same identity.
- **`validate`** — `parse` used for its classified-error behavior at call
  sites that need the failure reason but not necessarily the success
  value.
- **token scanning** — a distinct operation, not part of `parse`, that
  locates a candidate Phase ID substring within a longer string (a
  commit subject, task title, or report heading) and defers the actual
  accept/reject decision to `parse`. Token scanning SHALL NOT implement
  its own competing acceptance rule; it only ever locates a candidate
  span.
- **comparison helpers** — `equals`, `compare` (returning
  less/greater/equal/not-comparable per §10), `same_series`,
  `same_branch`. Each SHALL operate only on already-parsed `PhaseId`
  values' `comparison_identity` fields; none SHALL re-parse text or
  reimplement ordering logic locally.

CPIPC-REQ-030: No consumer SHALL synthesize Phase ID text by hand (e.g.
string concatenation of `f"{series}{branch}"`). Every consumer that needs
Phase ID text SHALL obtain it from the canonical parser's `format`
operation, even when the consumer already holds the structured value.

## 9. Parsing Semantics

CPIPC-REQ-031: Recognition SHALL be `fullmatch`-based (whole-input, not
"find something that looks right inside a larger string") wherever the
source text is already known to be exactly a Phase ID. Substring
extraction from free text SHALL be performed only by the distinct token
scanner operation (§8), layered on top of the same grammar, never as a
second grammar of its own.

CPIPC-REQ-032: Leading and trailing ASCII whitespace SHALL be stripped
before matching. Internal whitespace SHALL NEVER be valid; its presence
is a rejection (`invalid_syntax`, §11), not silent removal.

CPIPC-REQ-033: Case is accepted in either form at the lexical level and
SHALL be normalized to uppercase on every successful parse, per §4.4.

CPIPC-REQ-034: Normalization SHALL happen exactly once, as the last step
of a successful parse, producing `normalized_text`. There SHALL NOT be a
separate "normalize an already-parsed value" re-entry point that could
drift from the parse path.

CPIPC-REQ-035: `normalized_text` (§5) SHALL be the only sanctioned way to
turn a parsed Phase ID back into text.

CPIPC-REQ-036: Rejection SHALL always yield a classified error from the
closed taxonomy in §11 — never a bare `None`/`False` with no indication
of why, and never a silently-truncated success. Silent truncation of a
too-long suffix into a shorter, still-valid-looking match is the specific
defect class (Phase 137P §2.2, the 137F.1V/137MV.1/
`repository_transition_integration.py` defect) this contract exists to
foreclose, and it SHALL NOT be reachable in any conforming implementation.

CPIPC-REQ-037: The grammar in §4 is unambiguous by construction (each
production has a unique first-token/greedy parse). `ambiguous_syntax`
(§11) is reserved for inputs that would require lookahead a future
grammar extension might introduce; it is not reachable under the grammar
as frozen by this contract, and it SHALL NOT be triggered by any input
valid or invalid under §4 as it stands.

CPIPC-REQ-038: The parser SHALL NOT guess at a "likely intended" Phase ID
from malformed input. No fuzzy correction, typo repair, or
prefix-matching against known phase series is permitted. Heuristic
extraction of a plausible token from free text is exclusively the token
scanner operation (§8), and even the token scanner SHALL hand its
candidate substring only to the strict `fullmatch` grammar — it SHALL NOT
have its own accept/reject logic.

## 10. Comparison Semantics

CPIPC-REQ-039: Two Phase IDs are equal if and only if their
`comparison_identity` tuples (§5) are equal. Equality SHALL be defined on
canonical, normalized structure, not on `source_text`. `"137mv"` and
`"137MV"` SHALL be treated as the same Phase ID; `"137F.1V"` and
`"137F.1"` SHALL NOT — a real, load-bearing distinction preserved from
this repository's own history.

CPIPC-REQ-040: Ordering SHALL be supported only within a comparable
family, generalizing (not replacing) the existing branch-aware logic
this repository already established in `phase_reports.is_phase_id_backward`:

- Two Phase IDs SHALL be considered comparable only if they share the
  same `series`.
- Within a series, `branch` values SHALL be compared as an ordered
  sequence following spreadsheet-column rollover (`A < B < ... < Z < AA
  < AB < ... < AZ < BA < ...`), never as plain lexical string order
  (which would wrongly rank `"AA"` before `"B"`).
- The exceptional branch (`"X"`, e.g. `113X.1`, `113X.2`) SHALL be
  treated as a self-contained excursion, not a point in the ordinary
  lettered sequence, and is NOT comparable to a mainline branch in the
  same series.
- Within the same `(series, branch)`, `subphase` tuples SHALL be
  compared element-wise, the numeric sub-component first as an integer
  (never as a string, so `"134E.10"` orders after `"134E.2"`), then the
  segment's trailing letters (if any) lexically.

CPIPC-REQ-041: Two Phase IDs that are not comparable by the rules of
CPIPC-REQ-040 (different series, or one mainline and one exceptional
branch) SHALL report **"not comparable"** as a first-class outcome. An
implementation SHALL NOT coerce a not-comparable pair into a
`True`/`False` "is it earlier" answer by falling back to lexical
comparison.

CPIPC-REQ-042: This contract explicitly forbids introducing an artificial
total ordering over all Phase IDs. Comparability is a partial relation by
design (CPIPC-REQ-040, CPIPC-REQ-041), not an implementation limitation
to be worked around.

CPIPC-REQ-043: "Same series" (equal `series` fields) and "same branch"
(equal `series` and `branch` fields) SHALL each be first-class comparison
operations (`same_series`, `same_branch`, §8), not reconstructed ad hoc
by callers via string-prefix checks.

## 11. Error Taxonomy

CPIPC-REQ-044: The following closed, canonical error set is frozen.
Every rejection SHALL map to exactly one of these kinds; no
implementation SHALL introduce an additional error kind without a
governed revision of this contract.

| Error kind | Meaning | Example input |
|---|---|---|
| `empty_input` | Input was empty, `None`, or whitespace-only after stripping | `""`, `"   "` |
| `invalid_syntax` | Input does not match the grammar at all | `"abc"`, `"A134"` |
| `missing_branch` | A numeric series was present with no branch letters at all | `"134"` |
| `malformed_subphase` | A dotted segment does not fit either subphase form | `"134E.V1"` |
| `unsupported_syntax` | Lexically well-formed by a plausible superset grammar but excluded by an explicit rule of this contract | reserved leading-zero series (§4.2) |
| `reserved_syntax` | Matches a form this contract explicitly reserves for future use (§4.2) rather than accepting or rejecting outright | bare numeric series `"134"` (kept distinct from `missing_branch` per CPIPC-REQ-012) |
| `ambiguous_syntax` | Input matches more than one interpretation under a grammar extension | not reachable under the grammar frozen by this contract (§9) |
| `truncated_extraction` | The token scanner found a candidate span that itself fails `parse` because it was cut off by adjacent punctuation/newline — a classified, surfaced failure, not a silently shortened success | a commit subject ending mid-ID |
| `unexpected_suffix` | Trailing characters remain after an otherwise-valid `series + branch + subphase` prefix | `"137N-extra"` |

CPIPC-REQ-045: Every taxonomy entry SHALL have a fixed, deterministic
meaning: the same input SHALL always produce the same error kind,
independent of which lifecycle subsystem invoked the parser.

CPIPC-REQ-046: An implementation SHALL NOT collapse two distinct error
kinds into one, and SHALL NOT report a kind not present in this table.

## 12. Compatibility Guarantees

CPIPC-REQ-047: Every historically-valid PCAE Phase ID — the full union
independently confirmed by Phase 137P §2.1 across all fifteen inventoried
call sites — SHALL remain valid under this contract's grammar (§4). No
migration step, implementation, or future revision under this contract
SHALL make a previously-valid Phase ID invalid.

CPIPC-REQ-048: Backward compatibility is mandatory and is a property of
the grammar itself (§4.1's union derivation), not a compatibility shim
layered around the parser for old inputs.

CPIPC-REQ-049: Forms accepted by one narrow historical consumer but
excluded by this contract's grammar do not exist, by construction of the
union derivation in Phase 137P §4.1.

CPIPC-REQ-050: Future extension points are explicitly reserved, so a
later grammar revision has a defined place to attach without
re-litigating this contract: the reserved bare-number form and the
reserved leading-zero form (§4.2); the currently-unbounded branch-letter
length, which imposes no cap because no historical evidence motivates
one, though a future revision MAY choose to impose one as a narrowing
that does not itself constitute a grammar rewrite.

## 13. Migration Obligations

CPIPC-REQ-051: Every existing Phase ID parsing consumer identified in §2
SHALL migrate to the canonical parser. Independent parser implementations
SHALL be deprecated upon migration.

CPIPC-REQ-052: Duplicate grammar definitions SHALL be removed outright
after migration, not carried forward as a second "for compatibility"
path. The exact-duplicate pairs identified in Phase 137P §2.1
(`check.py`'s `_PHASE_CODE_RE` and `agent.py`'s `_TSA_PHASE_CODE_RE`)
have no independent reason to exist once the canonical parser exists.

CPIPC-REQ-053: There SHALL be no flag-day cutover. The canonical parser
SHALL be introduced as a new, additive module first, provably matching
(via characterization tests derived from the §2 inventory) the union
behavior described in §4, before any existing call site is touched.

CPIPC-REQ-054: Migration SHALL proceed per-consumer, not per-file wrap.
Each consumer in §14's table SHALL be migrated independently, in its own
governed phase or commit, by replacing that consumer's local
regex/comparison logic with a call into the canonical parser — never by
leaving the old regex in place and routing only its output through a
compatibility shim, since a shim around a still-present duplicate regex
preserves the defect class (two implementations that can still disagree)
rather than eliminating it.

CPIPC-REQ-055: Migration order SHALL preserve behavioral compatibility at
every step. A partially-migrated state, in which some consumers use the
canonical parser and others still use local logic, is a known, accepted
transient risk of a non-flag-day migration (Phase 137P §15) and SHALL be
minimized by governed, deliberate migration-order sequencing, not treated
as an acceptable steady state.

CPIPC-REQ-056: The order in which the ten consumer groups in §14 are
migrated is a future-phase decision, not fixed by this contract. This
contract notes, without prescribing timing, that
`core/repository_transition_integration.py`'s `parse_phase_id_from_text`
is the one inventoried consumer still carrying an unrepaired truncation
defect at the time this contract is frozen, making it a natural
candidate for early migration once implementation is authorized.

## 14. Lifecycle Integration

CPIPC-REQ-057: The following inventory, frozen without modification from
Phase 137P §10, is normative. Every consumer identified here SHALL use
the canonical parser for the operations listed. No exception is
permitted without explicit architectural approval through a governed
contract revision.

| Consumer | Current behavior | SHALL delegate to canonical parser for |
|---|---|---|
| `core/phase_reports.py` (report title extraction, commit-subject scanning, backward-ordering check) | 3 separate regex definitions | `parse` (title extraction), token scanning (commit-subject), `compare`/`same_series` (`is_phase_id_backward`) |
| `core/check.py` (`PROJECT_STATUS.md` current-phase extraction) | 1 regex, unstructured tail | token scanning + `parse` |
| `core/architecture_status.py` (`parse_phase_id`, ordering, freshness) | 1 regex + hand-rolled comparison tuple | `parse`, `compare` |
| `core/context.py` (bootstrap ambiguity detection, TODO.md staleness) | 2 inline regexes + hand-rolled base-phase prefix comparison | `parse`, `same_branch` |
| `core/agent.py` (`_TSA_*`, `_SIT_*` duplicated helpers) | 2 regex definitions duplicating `check.py`/`phase_reports.py` | `parse`, `is_valid` (duplication removed outright — no delegation target needed once retired) |
| `cltr_prototype/identity.py` + `cltr_prototype/compatibility.py` | 2 regex definitions, explicit-only identity model | `parse` (identity.py's validation becomes a thin wrapper; compatibility.py's title scan becomes token scanning) |
| `cltr/authority/identity.py` (`PhaseIdentity` wrapper) | opaque 16-char charset check, no structure | `parse`; construction becomes "construct from a successfully-parsed `PhaseId`" |
| `commands/phase.py` (queue validation, commit-message phase-range parsing) | 2 regex definitions, both narrower than the union grammar | `is_valid` (queue validation), `parse` + range-aware comparison helpers (commit-range expansion) |
| `commands/push.py` (`_PHASE_TOKEN_RE`, done-task phase extraction) | 1 regex, the site of the 137MV.1 repair | token scanning + `parse` |
| `core/repository_transition_integration.py` (`parse_phase_id_from_text`) | 1 regex, still carrying an unrepaired truncation defect at contract-freeze time | token scanning + `parse` |

CPIPC-REQ-058: Once integration per this section is complete, no
lifecycle subsystem SHALL own grammar; every row above SHALL stop
defining its own pattern for Phase ID recognition.

CPIPC-REQ-059: Lifecycle decisions built on top of a parsed Phase ID
(which phase is "current," whether a task is "stale," whether a report
"matches" a task) remain exactly where they are today, in each consumer.
This contract centralizes recognition, validation, normalization,
formatting, and comparison only, per §7.

## 15. Extensibility Rules

CPIPC-REQ-060: Future grammar extensions SHALL be additive only. They
SHALL NOT alter the meaning, classification, or accepted/rejected status
of any input already supported, reserved, or invalid under §4 as frozen
by this contract, except by an explicit governed revision that states its
compatibility impact per §12.

CPIPC-REQ-061: Every future grammar extension SHALL be backward
compatible with this contract's frozen grammar (§4) unless a governed
revision explicitly supersedes a requirement and states its compatibility
impact.

CPIPC-REQ-062: Every future grammar extension SHALL be implemented
centrally, in the canonical parser alone (§6). No consumer-specific
grammar extension is permitted.

CPIPC-REQ-063: Every consumer SHALL inherit a grammar extension
automatically the next time it calls `parse`/`is_valid`/`compare`,
because no consumer holds its own copy of the grammar to fall out of
sync. This is the direct operationalization of Phase 137P §3 principle 4
and §13.

## 16. Security Requirements

CPIPC-REQ-064: The canonical parser SHALL be deterministic: identical
input SHALL always yield an identical result. No randomness and no
environment-dependent behavior is permitted.

CPIPC-REQ-065: The canonical parser SHALL be side-effect free and
stateless: `parse`/`is_valid`/`compare`/`format` SHALL be pure functions
of their arguments; no module-level mutable state, and no caching keyed
on ambient time or process state.

CPIPC-REQ-066: The canonical parser SHALL be authority-neutral: it SHALL
NOT consult or assert anything about lock ownership, governance state,
task state, or phase activation. It SHALL answer only "does this text
mean a Phase ID, and if so what does it structurally mean."

CPIPC-REQ-067: The canonical parser SHALL be runtime-neutral: it SHALL
perform the same recognition regardless of the harness's
Observed/Bounded/Unbounded runtime state, and its existence and use SHALL
change none of them. Runtime remains Observed / observe / unavailable
throughout every operation governed by this contract.

CPIPC-REQ-068: The canonical parser SHALL be thread-safe by virtue of
statelessness: no shared mutable data to race on.

CPIPC-REQ-069: The canonical parser SHALL NOT access repositories, the
filesystem, or the network; SHALL NOT invoke governance; and SHALL NOT
change runtime capability. It accepts text (or, for token scanning, a
string already read by its caller) and returns a value; it SHALL NOT read
`PROJECT_STATUS.md`, `tasks/`, or git state itself. File access remains
entirely in lifecycle-specific callers, which hand the text they read to
the parser (§7, CPIPC-REQ-027).

## 17. Compliance Requirements

CPIPC-REQ-070: Every future implementation of, or migration to, the
canonical parser SHALL provide traceable evidence of compliance with:

1. Parser Ownership (§6);
2. Parser Responsibilities (§7);
3. Parser API Contract (§8);
4. Parsing Semantics (§9);
5. Comparison Semantics (§10);
6. Error Taxonomy (§11);
7. Compatibility Guarantees (§12);
8. Migration Obligations (§13);
9. Lifecycle Integration (§14);
10. Extensibility Rules (§15);
11. Security Requirements (§16).

CPIPC-REQ-071: Compliance evidence SHALL identify the applicable CPIPC
requirement IDs, inputs, expected output or deterministic failure,
characterization-test coverage against the §2 inventory, and negative
tests demonstrating no truncation, no heuristic acceptance, no artificial
total ordering, and no lifecycle/governance/runtime leakage.

CPIPC-REQ-072: An implementation SHALL be non-conformant if any mandatory
evidence is absent, any requirement of this contract is weakened locally,
any consumer retains independent parsing/grammar/normalization/comparison
logic after that consumer's migration is declared complete, or any
behavior forbidden by §16 is reachable.

CPIPC-REQ-073: Conformance to CPIPC-001 does not itself authorize
implementation. Each implementation phase still requires an explicit
governed phase with an in-scope task contract.

## 18. Traceability

CPIPC-REQ-074: Every architectural principle, grammar production, error
kind, comparison rule, and lifecycle-integration row in this contract
SHALL be traceable to its origin in Phase 137P. This contract introduces
no grammar production, error kind, comparison rule, or consumer-inventory
entry that Phase 137P did not already establish; it freezes what Phase
137P proposed, and only that.

The lifecycle is:

```
137P Architecture (proposed)
        |
        v
CPIPC-001 Contract (frozen, this document)
        |
        v
137R Implementation (future, governed separately)
        |
        v
137S Independent Verification (future, governed separately)
```

CPIPC-REQ-075: No architectural decision recorded by Phase 137P (§3
through §17 of that document) may be lost, weakened, or silently altered
by this contract or by any future revision that does not explicitly
identify the change and its compatibility impact per §12.

## 19. Non-Goals

CPIPC-001 SHALL NOT be read as, and does not:

- implement, replace, or delete any regex, module, class, or function;
- migrate any existing consumer;
- introduce any execution capability;
- change the runtime state (`Observed` / `observe` / `unavailable`
  throughout);
- change any existing public CLI behavior or output;
- resolve the risks Phase 137P §15 recorded (grammar
  under-specification, migration-ordering, comparison-scope, and
  `PhaseIdentity` charset-reservation risk) — they remain open for the
  phases that perform implementation and migration work;
- decide the specific order in which §14's ten consumer groups are
  migrated;
- repair `repository_transition_integration.py`'s open truncation defect
  — noted in §13 as a natural early migration candidate, not fixed here.

## 20. Phase 137Q freeze confirmation

Phase 137Q freezes the canonical grammar, canonical representation
semantics, parser ownership, parser responsibilities, parser API
behavior, parsing semantics, comparison semantics, error taxonomy,
compatibility guarantees, migration obligations, lifecycle-integration
inventory, extensibility rules, security requirements, and compliance
requirements derived from Phase 137P as CPIPC-001 v1.0.

No production implementation is authorized by this freeze. No parser
code is introduced. No existing regex, module, or comparison function is
modified, migrated, or deleted. No runtime behavior changes. Runtime
remains Observed / observe / unavailable.

## 21. Recommended next phase

**137R — Canonical Phase ID Parser Implementation.**

Purpose: implement the canonical parser defined by CPIPC-001 v1.0,
migrate the inventoried parser consumers (§14) to the shared
implementation while preserving behavior, eliminate duplicated parsing
logic, and verify that all historical Phase IDs remain compatible with no
runtime, lifecycle, or governance regressions.
