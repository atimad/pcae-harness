# Phase 137P — Canonical Phase ID Parsing Architecture

**Status:** Complete
**Phase class:** Architecture only. No production code, no parser
implementation, no regex replacement, no runtime behavior change.
**Runtime:** Observed / observe / unavailable (unchanged)

This document defines the canonical architecture for Phase ID parsing
across the PCAE lifecycle. It does not implement that architecture. It
establishes the single grammar, the single set of parser responsibilities,
and the boundary every lifecycle consumer must observe once the
architecture is realized in a later, implementation-scoped phase
(137Q and beyond).

---

## 1. Motivation

Three independent repairs — 137F.1 → 137F.1V, then 137MV.1, and the
still-open `repository_transition_integration.py` sibling — fixed the
*same* defect class in three *different* files: an unquantified or
under-quantified letter-suffix group in a phase-ID regex silently
truncated multi-letter branch suffixes (`"137MV"` → `"137M"`,
`"137F.1V"` → `"137F.1"`). Each repair fixed its own file's regex and
left the others untouched, because no file was authoritative over any
other. The repair pattern itself — copy the fix from whichever sibling
regex already got it right — is the symptom. The disease is that this
repository has never had one component whose job is "interpret a Phase
ID"; it has had `N` components that each independently reinvent that
job, `N` regexes that drift out of sync a little differently each time,
and a `git grep`-and-imitate workflow standing in for a real contract.

This phase eliminates that architecture, not the individual bugs. It is
issued architecture-only, exactly as 134A–134F (Canonical Lifecycle
Architecture) and 135A–135Z (Whole Lifecycle Verification) preceded
their own implementation phases, so the grammar and ownership model can
be reviewed and frozen (137Q) before any of the eleven-plus existing
call sites are touched.

---

## 2. Defect-Class Analysis

### 2.1 Independent inventory (not trusting the task brief's three examples)

The task brief names three confirmed occurrences
(`phase_reports.py`, `push.py`, `repository_transition_integration.py`).
An independent `grep` sweep of `src/pcae/` for phase-ID regexes and
grammar predicates found **thirteen** distinct definitions across **ten**
files — more than four times the brief's count. None of the thirteen are
byte-identical to any other.

| # | Location | Pattern (abbreviated) | Branch letters | Subphase form |
|---|----------|------------------------|-----------------|----------------|
| 1 | `core/phase_reports.py:_CANONICAL_TITLE_PHASE_ID_RE` | `\d+[A-Z]+(?:\.\d+[A-Za-z]?)*` | one-or-more, uppercase only | `.N` + optional 1 letter |
| 2 | `core/phase_reports.py:_PHASE_ID_SHAPE_RE` | `(\d+)([A-Za-z]*)((?:\.\d+)*)` | zero-or-more, mixed case | `.N`, no trailing letter |
| 3 | `core/phase_reports.py:_COMMIT_SUBJECT_PHASE_TOKEN_RE` | `\d+[A-Za-z]+(?:\.\d+[A-Za-z]?)*` (case-insensitive) | one-or-more | `.N` + optional 1 letter |
| 4 | `core/check.py:_PHASE_CODE_RE` | `\d+[A-Z][\d.A-Z]*` | exactly one leading, then a free-form `[\d.A-Z]*` tail (not segment-structured) | unstructured tail |
| 5 | `core/architecture_status.py:PHASE_ID_RE` | `(\d+)([A-Za-z]+)((?:\.\d+[A-Za-z]?)*)` | one-or-more | `.N` + optional 1 letter |
| 6 | `core/context.py` (`_detect_phase_ambiguity`, inline) | `\d+[A-Z]+(?:\.\d+)*` | one-or-more, uppercase only | `.N`, no trailing letter |
| 7 | `core/agent.py:_TSA_PHASE_CODE_RE` | `\d+[A-Z][\d.A-Z]*` | exactly one leading + free tail | unstructured tail (duplicate of #4) |
| 8 | `core/agent.py:_SIT_PHASE_ID_GRAMMAR_RE` | `\d+[A-Za-z]*(?:\.\d+)*(?:\.[A-Za-z]+)?` | zero-or-more | `.N`* then at most one trailing `.letters` segment |
| 9 | `cltr_prototype/identity.py:PHASE_ID_RE` | `(\d+)([A-Za-z])((?:\.\d+[A-Za-z]?)*)` | **exactly one** | `.N` + optional 1 letter |
| 10 | `cltr_prototype/compatibility.py:_TITLE_PHASE_TOKEN_RE` | `\d+[A-Za-z](?:\.\d+[A-Za-z]?)*` | exactly one (token-extraction, validated against #9 after) | `.N` + optional 1 letter |
| 11 | `cltr/authority/identity.py:_PHASE_IDENTITY_PATTERN` | `[A-Za-z0-9.]{1,16}` | unconstrained charset, no structure at all | none (opaque 1–16 chars) |
| 12 | `commands/phase.py:_VALID_PHASE_ID_RE` | `\d+[A-Z]+(?:\.\d+)?` | one-or-more | **at most one** `.N` segment |
| 13 | `commands/phase.py:_PHASE_ID_RE` (range expansion) | `(\d+)([A-Z])(?:\.(\d+))?` | **exactly one** | at most one `.N` segment |
| 14 | `commands/push.py:_PHASE_TOKEN_RE` | `\d+[A-Za-z]*(?:\.\d+[A-Za-z]*)*` (case-insensitive) | zero-or-more | `.N` + zero-or-more trailing letters |
| 15 | `core/repository_transition_integration.py:parse_phase_id_from_text` | `\d+[A-Za-z](?:\.\d+[A-Za-z]?)*` (case-insensitive) | **exactly one** | `.N` + optional 1 letter |

(Numbering runs to 15 because two pairs — `check.py`/`agent.py` #4/#7,
and `phase_reports.py` title-RE/`agent.py` — are exact textual
duplicates pasted into a second module rather than imported, which is
itself evidence of the same "no shared authority" defect: even
*identical* code was independently duplicated rather than referenced.)

### 2.2 What this proves

- **No two of the fifteen call sites are guaranteed to accept the same
  input set.** `#9`/`#10`/`#13`/`#15` require *exactly* one branch
  letter and would reject `"136AX"` outright (not truncate it — reject
  it), while `#1`/`#3`/`#5`/`#6`/`#12` accept one-or-more letters, and
  `#2`/`#8`/`#14` accept zero. A phase ID that is valid to one consumer
  can be invalid, or silently mis-parsed, to another, in the same
  process, on the same input, at the same time.
- **Silent truncation is a structural property of this design, not a
  one-off bug.** Every regex that uses an unquantified or
  narrowly-quantified capture group inside a `re.search`/`re.match`
  call (rather than a `fullmatch` with an explicit failure path)
  degrades a too-long suffix into a shorter, *still-valid-looking*
  match instead of rejecting it. 137F.1V and 137MV.1 each closed one
  instance of this; `repository_transition_integration.py`'s
  `parse_phase_id_from_text` (#15) still has it, unrepaired, at the
  time of this phase.
- **Structural fidelity varies independently of acceptance width.**
  Even among sites that accept the same input, only some (`#1`, `#5`,
  `#9`, `#15`) parse it into a segment-structured dotted-subphase
  interpretation; others (`#4`, `#7`) capture an unstructured
  `[\d.A-Z]*` tail with no segment boundaries at all, `#11` treats the
  whole ID as an opaque 16-character bag with no structure whatsoever,
  and `#12`/`#13` cap the dotted subphase at a single segment.
- **Comparison and ordering are duplicated separately from parsing.**
  `architecture_status.parse_phase_id` and
  `phase_reports._parse_phase_id_shape` /
  `is_phase_id_backward` independently reimplement "parse into
  (series, branch, subphase) and compare" with different subphase
  shapes (`(number, verification_letter)` tuples vs. plain integers) —
  a second axis of the same defect class, one level up from lexical
  recognition.
- **Grammar knowledge is duplicated in prose, not just in code.** At
  least six of the fifteen sites carry a comment re-explaining why the
  branch letter must be one-or-more (citing Phase 136AX), each written
  independently at the point that file was patched. The comments agree
  with each other; the regexes next to them do not.

### 2.3 Root cause

There is no data type in this codebase that *means* "a PCAE Phase ID."
Every call site treats a phase ID as a plain `str` and reaches for
`re.compile` locally, because there is nothing else to reach for. The
137F.1/137F.1V/137MV.1 repair sequence, and the open
`repository_transition_integration.py` sibling, are the observable
consequence of that absence, not the disease.

---

## 3. Architectural Principles

1. **Single authority.** Exactly one component (the *canonical parser*)
   owns the grammar, and every other lifecycle component that needs to
   recognize, validate, normalize, format, or compare a Phase ID does so
   only by calling into it. No second implementation of any part of
   this list is permitted to exist anywhere in `src/pcae/`.
2. **Types, not strings, cross boundaries.** Once a piece of text has
   been recognized as a Phase ID, it is represented as a canonical,
   immutable value (a `PhaseId`, in the sense the existing
   `pcae.cltr.authority.identity` wrapper-type family already
   establishes for other identifiers — see §12), not passed onward as a
   bare `str` that invites re-parsing.
3. **Fail closed on ambiguity, never truncate.** Every recognition
   operation is `fullmatch`-based (whole-input, not "find something that
   looks right inside a larger string") wherever the source text is
   already known to be exactly a Phase ID, and returns an explicit,
   classified failure — never a shorter, silently-accepted substring —
   whenever the input does not fit the grammar exactly. Substring
   extraction from free text (titles, commit subjects, prose) is a
   distinct, explicitly-named operation (a *token scanner*, §8), layered
   on top of the same grammar, never a second grammar of its own.
4. **Grammar evolution happens in one place.** Historical experience
   (136AX's single-letter → one-or-more-letter branch expansion) shows
   the grammar *will* need to grow again. The architecture is built so
   that a future grammar extension is a change to the canonical parser
   alone; every consumer inherits it automatically without being
   touched.
5. **The parser is lifecycle-inert.** It answers "is this text a valid
   Phase ID, and if so what does it mean structurally" and nothing else.
   It has no opinion on whether a given Phase ID is *active*, *next*,
   *stale*, *governed*, or *authorized* — those are lifecycle
   judgments made by callers using the structured value the parser
   returns.

---

## 4. Canonical Grammar

### 4.1 Design constraint

The grammar must accept every form independently confirmed as
historically valid in §2.1 (rows 1–15's *union*, not intersection — a
form need only be accepted by *some* existing consumer to be historically
valid, since narrower consumers were themselves defects, not intentional
restrictions) and must accept nothing that no existing consumer accepts
today, so that adopting the canonical parser is never itself a breaking
change for a real, previously-valid ID. It is derived directly from the
observed shapes in `docs/`, `tasks/DONE.md`, and commit-subject
conventions (e.g. `92A`, `96D`, `119AB`, `135H`, `137N`, `137MV`,
`119AC`, `136AY`, `134E.10`, `135H.2`, `137F.1V`, `134E.10.1V`,
`134E.10.1.1`, `113X.1`, `113X.2`, and the single-dotted-letter
"repair suffix" form `113D.R` documented in `agent.py`'s `_SIT`
grammar comment), not by wrapping the union of the fifteen regexes
verbatim.

### 4.2 EBNF

```ebnf
phase-id        = series , branch , { "." , subphase-segment } ;

series          = digit , { digit } ;
                  (* one or more decimal digits; no leading-zero
                     restriction is imposed — none has ever been
                     observed, and none is excluded by any existing
                     consumer *)

branch          = letter , { letter } ;
                  (* exactly the "mainline branch" concept: one or more
                     ASCII letters. Historically single-letter (92A,
                     96D) through the observed rollover into
                     multi-letter suffixes once a series exhausts
                     single letters A-Z (136Z -> 136AA -> ... -> 136AX,
                     136AY; also 119AB, 119AC, 137MV). No upper bound
                     on length is imposed by any historical evidence;
                     none is fixed here. *)

subphase-segment
                = numeric-segment
                | letter-segment ;

numeric-segment = digit , { digit } , [ letter , { letter } ] ;
                  (* a dotted sub-phase number, with an optional
                     trailing verification/repair-letter suffix:
                     "10" (134E.10), "2" (135H.2), "1V" (137F.1V),
                     "1" (134E.10.1.1's third segment) *)

letter-segment  = letter , { letter } ;
                  (* a dotted segment that is letters only, with no
                     leading digit -- the standalone repair-suffix
                     form documented for _SIT ("113D.R"). Rare, but
                     independently attested by an existing consumer
                     (#8) and excluded by no other. *)

digit           = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
letter          = "A" | "B" | ... | "Z" | "a" | "b" | ... | "z" ;
```

Whole-string form (`fullmatch` target), for direct implementation
reference without committing to a particular regex engine's syntax:

```
^ [0-9]+ [A-Za-z]+ ( \. ( [0-9]+ [A-Za-z]* | [A-Za-z]+ ) )* $
```

### 4.3 Supported / reserved / invalid

- **Supported** — anything the grammar in §4.2 accepts. This is the
  entire union of historically valid forms established in §4.1.
- **Reserved** (syntactically well-formed under a *plausible* future
  extension, but not accepted today, and not silently coerced into a
  nearby supported form): a bare numeric series with no branch letter
  at all (`"134"`) — explicitly called out as invalid by
  `architecture_status.py`'s own existing comment, and never observed
  as a real Phase ID; and a leading-zero series (`"007A"`) — never
  observed, not excluded by the grammar's digit rule, but reserved
  rather than declared supported because no historical evidence
  motivates committing to its semantics (does `"007A"` sort before or
  equal to `"7A"`?) one way or the other. A future revision of this
  document, not an implementation detail, decides reserved forms —
  see §15.
- **Invalid** — everything else: empty string, whitespace-only,
  branch-only with no series (`"A"`), a subphase segment that mixes
  digits and letters in an order other than digits-then-letters
  (`"134E.V1"`), any character outside `[0-9A-Za-z.]`, a trailing or
  leading `.`, or two consecutive `.` separators.

### 4.4 Case sensitivity

Historical Phase IDs are written with uppercase branch/suffix letters
in every governed artifact this repository has produced
(`137N`, not `137n`; `137F.1V`, not `137f.1v`). The grammar in §4.2
accepts either case at the lexical level (several existing consumers —
#3, #10, #14, #15 — are case-insensitive at the regex layer), but
**normalization is mandatory and case is not semantically distinctive**:
recognition, followed immediately by uppercasing, is the only path to a
canonical `PhaseId` value. Two inputs that differ only in letter case
denote the *same* Phase ID.

---

## 5. Canonical Representation

The parsed model — semantics, not a committed class definition (per the
architect-only scope of this phase):

| Field | Meaning | Derived from |
|---|---|---|
| `series` | The numeric phase-family identity | `series` production |
| `branch` | The mainline branch letters, canonically uppercased | `branch` production |
| `subphase` | An ordered sequence of parsed segments, each either `(number, letters)` for a numeric-segment or `(None, letters)` for a letter-segment | each `subphase-segment` |
| `normalized_text` | The canonical serialization: uppercased, with `.`-joined segments, exactly reproducing `series + branch + subphase` with no incidental whitespace | derived, not stored input |
| `comparison_identity` | `(series: int, branch: str, subphase: tuple)` — the tuple used for equality/ordering (§9); numeric sub-components compared as integers, not strings, so `"134E.2"` and `"134E.10"` order correctly | derived |
| `serialization_identity` | The wire-form string used when a Phase ID is written back into a report, filename, or commit subject: identical to `normalized_text` | derived |
| `source_text` | The original, unnormalized text that was parsed, retained for diagnostics/error messages only, never compared or serialized | input, as-provided |

`comparison_identity` and `serialization_identity` are documented as
*equal in content* to `normalized_text` deliberately: this repository's
own defect history (§2) is largely the result of comparison and
serialization drifting into separate representations across separate
files. The canonical model rules that out structurally by defining them
as the same derived value, not two independently-computed ones.

---

## 6. Parsing Semantics

- **Acceptance**: a `fullmatch` (whole-string, whitespace-stripped
  first) against the grammar of §4.2 succeeds.
- **Rejection**: `fullmatch` fails. Rejection always yields a
  classified error (§11), never a partial/best-effort value.
- **Whitespace**: leading and trailing ASCII whitespace is stripped
  before matching; internal whitespace is never valid and is a
  rejection (`invalid syntax`), not silently removed.
- **Case sensitivity**: per §4.4 — accepted in either case, normalized
  to uppercase on success.
- **Normalization**: happens exactly once, as the last step of a
  successful parse, producing `normalized_text`. There is no separate
  "normalize an already-parsed value" re-entry point that could drift
  from the parse path itself.
- **Canonical serialization**: `normalized_text` (§5) is the only
  sanctioned way to turn a parsed Phase ID back into text. No consumer
  synthesizes Phase ID text by hand (e.g. string concatenation of
  `f"{series}{branch}"`) — it asks the canonical parser's formatting
  operation (§10) to produce it, even when the consumer already holds
  the structured value, so a future grammar change cannot leave one
  serialization path unaware of it.
- **Error handling**: every rejection path returns a value from the
  closed error taxonomy in §11 — never a bare `None` with no
  indication of *why*, and never a silently-truncated success (the
  specific failure mode of the 137F.1V/137MV.1/§2.2 defect class).
- **Ambiguity handling**: the grammar in §4.2 is unambiguous by
  construction (each production has a unique first-token/greedy
  parse), so "ambiguous syntax" (§11) is reserved for inputs that would
  require lookahead a future grammar *extension* might introduce (e.g.
  if a reserved form from §4.3 is later promoted to supported in a way
  that overlaps an existing supported form) — not reachable under the
  grammar as specified in this phase, but named now so extension design
  in 137Q+ has a slot to use instead of inventing a new failure kind
  ad hoc, the same way ad hoc regexes were invented ad hoc.
- **No heuristic parsing**: the parser never guesses at a "likely
  intended" Phase ID from malformed input (e.g. no fuzzy correction of
  `"137Mv"`-with-a-typo, no prefix-matching against known phase
  series). Heuristic *extraction* of a plausible token out of free text
  is the separate, explicitly-scoped token-scanner operation (§8), and
  even the token scanner only ever hands its candidate substring to the
  same strict `fullmatch` grammar — it never has its own accept/reject
  logic.

---

## 7. Comparison Semantics

- **Identity / equality**: two Phase IDs are equal iff their
  `comparison_identity` tuples (§5) are equal. This means equality is
  defined on canonical, normalized structure, not on `source_text` —
  `"137mv"` and `"137MV"` are the same Phase ID; `"137F.1V"` and
  `"137F.1"` are not (a real, load-bearing distinction: 137F.1 and
  137F.1V are different phases in this repository's own history).
- **Ordering**: **supported, but only within a comparable family**,
  generalizing the existing branch-aware logic in
  `phase_reports.is_phase_id_backward` (independently arrived at by
  1̶3̶X̶.̶3̶ Phase 113X.3) rather than inventing a new rule:
  - Two Phase IDs are comparable only if they share the same `series`.
  - Within a series, `branch` values are compared as an ordered
    sequence following the spreadsheet-column rollover this
    repository's own numbering already uses (`A < B < ... < Z < AA <
    AB < ... < AZ < BA < ...`), not plain lexical string order (which
    would wrongly rank `"AA"` before `"B"`).
  - An explicitly-designated **exceptional branch** (the existing `"X"`
    convention, e.g. `113X.1`, `113X.2`) is a self-contained excursion,
    not a point in the ordinary lettered sequence, and is *not*
    comparable to a mainline branch in the same series — this is the
    exact rule `is_phase_id_backward` already encodes and that this
    architecture generalizes rather than replaces.
  - Within the same `(series, branch)`, `subphase` tuples are compared
    element-wise, numeric sub-component first (as an integer, never as
    a string — so `"134E.10"` orders after `"134E.2"`), then the
    segment's trailing letters (if any) lexically.
  - Two Phase IDs that are not comparable by the rules above (different
    series, or one-mainline-one-exceptional) report **"not
    comparable"** as a first-class outcome — never coerced into a
    `True`/`False` "is it earlier" answer by fallback lexical
    comparison. This is the direct architectural fix for the historical
    defect 113X.3 itself repaired (naive lexicographic ordering
    treating `"113D" < "113X.2"` as meaningful when the two IDs are not
    on the same branch at all).
- **Prefix / series relationships**: a "same series" predicate
  (`series` fields equal) and a "same branch" predicate (`series` and
  `branch` both equal) are both first-class comparison operations, not
  reconstructed ad hoc by callers via string-prefix checks (the pattern
  `context.py`'s `_detect_phase_ambiguity` and `agent.py`'s two
  `_re.match(r"(\d+[A-Z]+)", ...)` calls currently use, each with its
  own copy of the branch-letter-count assumption).

---

## 8. Parser API Architecture

Conceptual surface only — no signatures, no implementation classes,
per phase scope.

- **`parse`** — the sole entry point that turns `source_text` into
  either a canonical `PhaseId` value or a classified error (§11). The
  foundation every other operation is built on.
- **`is_valid`** — a boolean convenience over `parse`, for call sites
  that only need a yes/no answer (e.g. form/field validation) and do
  not need the error detail or the parsed structure. Defined strictly
  as "did `parse` succeed," never as an independent check.
- **`normalize`** — given a successfully-parsed `PhaseId`, or raw text
  that parses successfully, returns `normalized_text`. For call sites
  that hold text and want canonical text back, without needing the
  structured value themselves.
- **`format`** — the inverse of `parse` at the structural level: given
  a `PhaseId` value (however a caller obtained one — constructed from
  known components, not just round-tripped from `parse`), produce its
  canonical text. `normalize` and `format` converge on the same output
  for the same identity, by construction (§6).
- **`validate`** — distinguished from `is_valid` by scope: `is_valid`
  asks "is this syntactically a Phase ID at all," `validate` is the
  operation lifecycle-integration call sites use when they additionally
  need the classified reason on failure (i.e. it is `parse` used for
  its error-reporting behavior at sites that don't need the success
  value).
- **Token scanning** (the free-text-extraction operation named in §6):
  a distinct, explicitly-named operation — not part of `parse` — for
  the specific, narrower job the current `_COMMIT_SUBJECT_PHASE_TOKEN_RE`,
  `_PHASE_TOKEN_RE` (push.py), and `_TITLE_PHASE_TOKEN_RE`
  (`cltr_prototype/compatibility.py`) call sites actually do: find the
  substring in a commit subject, task title, or report heading that
  looks like a Phase ID reference, then hand that substring to `parse`.
  This keeps "recognize a whole string as a Phase ID" (strict,
  `fullmatch`) architecturally separate from "locate a Phase ID
  mentioned inside a longer string" (necessarily some form of
  `search`), so the strict grammar in §4.2 is never weakened to
  accommodate free-text scanning, and free-text scanning never grows
  its own competing acceptance rules — it only ever locates a candidate
  span and defers the actual accept/reject decision to `parse`.
- **Comparison helpers** — `equals`, `compare` (returning
  less/greater/equal/not-comparable per §7), `same_series`,
  `same_branch`. Each is a thin operation over two already-parsed
  `PhaseId` values' `comparison_identity` fields; none re-parses text
  or reimplements ordering logic locally.

---

## 9. Error Taxonomy

A closed, canonical set — every rejection maps to exactly one of these,
and every existing ad hoc failure mode identified in §2 maps onto one:

| Error kind | Meaning | Example input |
|---|---|---|
| `empty_input` | Input was empty, `None`, or whitespace-only after stripping | `""`, `"   "` |
| `invalid_syntax` | Input does not match the grammar at all — no recognizable series/branch structure | `"abc"`, `"A134"` |
| `missing_branch` | A numeric series was present with no branch letters at all (the explicitly-reserved bare-number form, §4.3) | `"134"` |
| `malformed_subphase` | A dotted segment does not fit either subphase form (digits-then-letters, or letters-only) | `"134E.V1"` |
| `unsupported_syntax` | Lexically well-formed by a plausible superset grammar but excluded by an explicit rule in this document (distinct from `invalid_syntax`'s "not a Phase ID shape at all") | reserved leading-zero series (§4.3), pending a future revision |
| `reserved_syntax` | Matches a form this document explicitly reserves for future use (§4.3) rather than accepting or rejecting outright | bare numeric series `"134"` classifies here rather than `missing_branch` once/if a future revision promotes it to reserved status — kept distinct from `missing_branch` today only because no historical form needs it; this row documents the taxonomy's extension point, not a currently-reachable case |
| `ambiguous_syntax` | Input matches more than one interpretation under a grammar extension (§6) | not reachable under the base grammar in this phase |
| `truncated_extraction` | The token-scanner (§8) found a candidate span that itself fails `parse` because it was cut off by adjacent punctuation/newline (distinct from the historical *silent* truncation defect — this is a *classified*, surfaced failure, not a shortened success) | a commit subject ending mid-ID |
| `unexpected_suffix` | Trailing characters remain after an otherwise-valid `series + branch + subphase` prefix | `"137N "` before whitespace-stripping is accounted for, or `"137N-extra"` |

Every taxonomy entry has a fixed, deterministic meaning: the same input
always produces the same error kind, independent of which lifecycle
subsystem invoked the parser.

---

## 10. Lifecycle Integration

Every current consumer identified in §2.1, and what it is expected to
delegate to the canonical parser once implementation begins (137Q+):

| Consumer | Current behavior | Delegates to canonical parser for |
|---|---|---|
| `core/phase_reports.py` (report title extraction, commit-subject scanning, backward-ordering check) | 3 separate regex definitions | `parse` (title extraction target), token scanning (commit-subject), `compare`/`same_series` (`is_phase_id_backward`) |
| `core/check.py` (`PROJECT_STATUS.md` current-phase extraction) | 1 regex, unstructured tail | token scanning + `parse` |
| `core/architecture_status.py` (`parse_phase_id`, ordering, freshness) | 1 regex + hand-rolled comparison tuple | `parse`, `compare` |
| `core/context.py` (bootstrap ambiguity detection, TODO.md staleness) | 2 inline regexes + hand-rolled base-phase prefix comparison | `parse`, `same_branch` |
| `core/agent.py` (`_TSA_*`, `_SIT_*` duplicated helpers) | 2 regex definitions duplicating `check.py`/`phase_reports.py` | `parse`, `is_valid` (removes the duplication outright — no delegation target needed once these are retired) |
| `cltr_prototype/identity.py` + `cltr_prototype/compatibility.py` | 2 regex definitions, explicit-only identity model | `parse` (identity.py's `_validate_phase_id` becomes a thin wrapper; compatibility.py's title scan becomes token scanning) |
| `cltr/authority/identity.py` (`PhaseIdentity` wrapper) | opaque 16-char charset check, no structure | `parse`; `PhaseIdentity.__post_init__` becomes "construct from a successfully-parsed `PhaseId`," giving this wrapper type real structural validation instead of an opaque bag-of-characters check |
| `commands/phase.py` (queue validation, commit-message phase-range parsing) | 2 regex definitions, both narrower than the union grammar | `is_valid` (queue validation), `parse` + range-aware comparison helpers (commit-range expansion) |
| `commands/push.py` (`_PHASE_TOKEN_RE`, done-task phase extraction) | 1 regex, the site of the 137MV.1 repair | token scanning + `parse` |
| `core/repository_transition_integration.py` (`parse_phase_id_from_text`) | 1 regex, **still carrying the exactly-one-letter truncation defect today** | token scanning + `parse` — this is the specific, concrete repair this architecture unblocks without itself performing it (out of scope here; see §14) |

**No lifecycle subsystem owns grammar** once this integration is
complete: every row above stops defining its own `re.compile` pattern
for phase-ID recognition. Lifecycle *decisions* built on top of a parsed
Phase ID (which phase is "current," whether a task is "stale," whether a
report "matches" a task) remain exactly where they are today, in each
consumer — the architecture only centralizes recognition, validation,
normalization, formatting, and comparison, per the boundary in §3
principle 5.

---

## 11. Migration Strategy

Principles, not a schedule (no implementation is authorized by this
phase):

- **No flag-day cutover.** The canonical parser is introduced as a new,
  additive module first, provably matching (via characterization tests
  derived from §2.1's inventory) the *union* behavior described in §4,
  before any existing call site is touched.
- **Per-consumer replace, not per-file wrap.** Each row in §10's table
  is migrated independently, in its own governed phase/commit, by
  replacing that consumer's local regex/comparison logic with a call
  into the canonical parser — never by leaving the old regex in place
  and merely routing its *output* through a compatibility shim, since a
  shim around a still-present duplicate regex would preserve the
  defect class (two implementations that can still disagree) rather
  than eliminate it.
- **Duplicate definitions are removed outright, not deprecated.** The
  exact-duplicate pairs identified in §2.1 (`check.py`'s
  `_PHASE_CODE_RE` and `agent.py`'s `_TSA_PHASE_CODE_RE`) have no
  independent reason to exist once the canonical parser exists; they
  are deleted in the same change that introduces the delegation, not
  carried forward as a second "for compatibility" path.
- **Backward compatibility is a grammar property, not a migration
  shim.** Because §4's grammar is defined as the union of every
  historically-valid form (§4.1), no migration step can make a
  previously-valid Phase ID invalid — compatibility is guaranteed by
  the grammar accepting everything it already accepted, not by
  layering exception-handling around the new parser for old inputs.
- **Order of migration is a future-phase decision**, but this
  architecture notes that `repository_transition_integration.py`
  (§2.1 row 15) is the one row still carrying an *unrepaired* instance
  of the truncation defect at the time of this phase, making it the
  natural first candidate once implementation is authorized.

---

## 12. Compatibility

- Every form independently confirmed valid in §2.1 (the union across
  all fifteen existing call sites) remains valid under §4.2's grammar.
  No valid historical Phase ID becomes invalid.
- Forms accepted by one narrow existing consumer but excluded by this
  grammar do not exist — §4.1's derivation method (union, not
  intersection) rules this out by construction.
- **Future extension points**, named now so a later grammar revision
  has a place to attach without re-litigating this document: the
  reserved bare-number form and reserved leading-zero form (§4.3);
  the currently-unbounded branch-letter length (no historical evidence
  motivates a cap, so none is imposed, but a future revision could
  choose to impose one without breaking this document's own
  reasoning, since it would be a *narrowing* of a currently-unbounded
  rule, not a grammar rewrite).
- **Reserved syntax**, restated from §4.3 for completeness: bare
  numeric series with no branch (`"134"`), and leading-zero series
  (`"007A"`). Both parse to `reserved_syntax`/`missing_branch`
  failures (§9), not silent acceptance and not a hard `invalid_syntax`
  that would foreclose a future decision either way.

---

## 13. Extensibility

- All future grammar growth (the next `136Z → 136AA`-style rollover
  event, a hypothetical third dotted-segment kind, a future
  double-letter verification suffix) is a change to §4.2's production
  rules and the canonical parser's implementation of them — nothing
  else. Every consumer inherits the new capability automatically the
  next time it calls `parse`/`is_valid`/`compare`, because none of them
  hold their own copy of the grammar to fall out of sync (this is the
  architectural property that principle 4 in §3 states and this section
  operationalizes).
- The `letter-segment` and reserved-form provisions in §4.2/§4.3 exist
  specifically so that the *next* rollover-style discovery (the way
  136AX discovered the one-or-more-letter branch requirement) has
  someplace to land as a grammar revision to one document and one
  module, instead of triggering another 137F.1-style repair sequence
  scattered across ten files.

---

## 14. Security

The canonical parser, as architected:

- Is **deterministic** — identical input always yields an identical
  result (§6); no randomness, no environment-dependent behavior.
- Is **side-effect free** and **stateless** — `parse`/`is_valid`/
  `compare`/`format` are pure functions of their arguments; no module-
  level mutable state, no caching keyed on ambient time or process
  state.
- Is **authority-neutral** — it never consults or asserts anything
  about lock ownership, governance state, task state, or phase
  activation; it answers only "does this text mean a Phase ID, and if
  so what does it structurally mean."
- Is **runtime-neutral** — it performs the same recognition regardless
  of the harness's Observed/Bounded/Unbounded runtime state, and its
  existence changes none of them (this phase's own runtime remains
  Observed / observe / unavailable throughout, unchanged).
- Is **thread-safe** by virtue of statelessness — no shared mutable
  data to race on.
- Performs **no filesystem access, no repository access, and no
  lifecycle mutation** — it accepts text (or, for token scanning,
  a string already read by its caller) and returns a value; it never
  reads `PROJECT_STATUS.md`, `tasks/`, or git state itself. (Contrast
  with several existing consumers — e.g. `check.py`'s
  `_extract_phase_code_from_project_status`, `context.py`'s
  `_extract_recommended_next_phase` — which *do* read files today; in
  the canonical architecture, file access remains entirely in those
  lifecycle-specific callers, which then hand the *text* they read to
  the parser. The parser's boundary, restated from §3 principle 5, is
  what makes this separation possible: it is inert with respect to
  everything except the text it is given.)

---

## 15. Risks

- **Grammar under-specification risk**: §4's grammar is derived from
  observed historical forms, not from a formal specification document
  that predates this repository's phase-numbering practice (none
  exists). A currently-unobserved but plausible future form (e.g. a
  three-level-deep letter-then-number-then-letter nesting) may not be
  cleanly classifiable as clearly supported, reserved, or invalid under
  §4.3 without a grammar revision. Mitigated by §13's extension
  mechanism, but not eliminated by this phase.
- **Migration-ordering risk**: §11 deliberately leaves per-consumer
  migration order to future phases. If migration phases are done out
  of dependency order, a partially-migrated state could (transiently)
  have some consumers on the canonical parser and others still on
  their local regex — reproducing, temporarily, exactly the
  cross-consumer disagreement this architecture exists to end. This is
  a known, accepted risk of *any* non-flag-day migration (§11
  explicitly rules out flag-day for compatibility reasons) and is a
  scheduling concern for 137Q+, not resolved here.
- **Comparison-scope risk**: §7's "not comparable" outcome for
  cross-series or mainline-vs-exceptional-branch comparisons is a
  faithful generalization of `is_phase_id_backward`'s existing rule,
  but no lifecycle consumer currently *handles* a "not comparable"
  result as anything other than "treat as not-backward" (i.e. the
  existing code already collapses it to a boolean). Callers migrating
  to the canonical `compare` operation will need to decide, per call
  site, what "not comparable" should mean for their specific lifecycle
  decision — this architecture makes the distinction available; it does
  not resolve every caller's response to it.
- **Charset-reservation risk for `cltr/authority/identity.PhaseIdentity`**:
  that wrapper's current pattern (`[A-Za-z0-9.]{1,16}`) is *broader*
  than §4.2's grammar in charset (digits allowed anywhere) but
  *narrower* in structure (no grammar at all, just a charset+length
  bound) and narrower in length for unbounded-branch-letter forms this
  document declines to cap (§4.2). Migrating this wrapper to construct
  from a parsed `PhaseId` (per §10) needs its own compatibility check
  against any already-persisted 16-character-max artifact — flagged
  here, not resolved, since resolving it is implementation work.

---

## 16. Non-Goals

This architecture does not:

- Modify lifecycle behavior, governance, reporting, or notifications.
- Change the runtime state (`Observed` / `observe` / `unavailable`
  throughout, per governance for this phase class).
- Introduce any execution capability.
- Change any existing public CLI behavior or output.
- Implement, replace, or delete any regex, module, or class.
- Resolve the risks named in §15 — they are recorded for the phases
  that do implementation and migration work.
- Decide the specific order in which §10's ten consumers are migrated.
- Repair `repository_transition_integration.py`'s still-open
  truncation defect (§2.1 row 15) — noted as the natural first
  migration candidate in §11, not fixed here.

---

## 17. Validation

Independent review of all fifteen parser locations identified in §2.1
against this architecture's responsibility assignment (§3, §8, §10):

| Responsibility | Assigned owner under this architecture | Currently duplicated at (count) |
|---|---|---|
| Lexical recognition | Canonical parser, `parse`/`fullmatch` | 15 locations (all of §2.1) |
| Validation | Canonical parser, `is_valid`/`validate` | 15 locations |
| Normalization | Canonical parser, `normalize` | Only 4 of 15 currently normalize case at all (`#3`, `#10`, `#14`, `#15`); the rest are case-sensitive with no normalization step, a second, narrower instance of the same "no shared authority" defect |
| Structured representation | Canonical parser, `PhaseId` value (§5) | 2 locations independently define a parsed tuple shape (`architecture_status.parse_phase_id`, `phase_reports._parse_phase_id_shape`), with two *different* shapes |
| Canonical formatting | Canonical parser, `format` | 0 locations define this today — every consumer that needs Phase ID text re-derives it via string interpolation ad hoc (e.g. `commands/phase.py`'s `f"{start_num}{chr(c)}"` in `_expand_phase_range`) |
| Comparison semantics | Canonical parser, `compare`/`equals`/`same_series`/`same_branch` | 2 locations (`is_phase_id_backward`, `architecture_status.parse_phase_id`'s callers), plus at least 2 more ad hoc prefix-comparison call sites (`context.py`'s `_detect_phase_ambiguity`, duplicated reasoning in `agent.py`) |
| Error classification | Canonical parser, closed taxonomy (§9) | 0 locations today — every existing site returns `None`/`False`/silently-skips on failure, with no classified reason anywhere in the codebase |

**Remaining duplicated parsing responsibility after this architecture
is adopted**: none, by definition — §3 principle 1 and §10's per-consumer
table jointly require every one of the fifteen locations to delegate
fully. The table above documents the *current* state (what is duplicated
today) precisely so a future implementation phase can verify, consumer
by consumer, that the count reaches zero.

---

## 18. Success Criteria — self-assessment

- [x] One authoritative parsing architecture is defined (§3–§10).
- [x] One canonical grammar is defined (§4), derived independently
      (§4.1) rather than by wrapping existing regexes.
- [x] Parser ownership is singular (§3 principle 1, §10).
- [x] Lifecycle ownership boundaries are explicit (§3 principle 5,
      §14's filesystem/repository-access boundary).
- [x] A migration strategy is defined (§11).
- [x] Historical compatibility is preserved by construction (§4.1, §12).
- [x] Duplicated parser ownership is eliminated *architecturally*
      (§10's table leaves no consumer with local grammar ownership);
      elimination *in code* is explicitly out of scope (§16) and is
      137Q+ work.
- [x] No implementation decisions leak into the architecture — §8 is
      conceptual only, §5 specifies semantics without a class
      definition, and no regex, module, or function signature is
      introduced by this phase.

---

## Recommended Next Phase

**137Q — Canonical Phase ID Parsing Contract Freeze**, per the governing
brief for this phase: transform this architecture into the binding
lifecycle contract (in the same style as TAMPC-001) governing every
future Phase ID parser implementation, freezing the grammar (§4),
responsibilities (§3, §8), normalization/comparison rules (§6, §7),
error taxonomy (§9), compatibility guarantees (§12), and migration
obligations (§11) before any production implementation begins.
