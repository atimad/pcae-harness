# Canonical Phase ID Parser — Migration Record (Phase 137R)

This document records the per-consumer migration decisions made while
implementing CPIPC-001 v1.0 (`docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md`)
in Phase 137R, per CPIPC-REQ-051 ("every existing consumer SHALL
migrate") and CPIPC-REQ-054 ("document every decision; no silent
duplication").

The canonical parser lives at `src/pcae/core/phase_id.py`. It is the
sole owner of Phase ID recognition, validation, normalization,
formatting, comparison, and error classification (CPIPC-001 §6).

## Consumer-by-consumer disposition

Per CPIPC-001 §14's ten-row inventory:

| # | Consumer | Disposition | Delegates to |
|---|---|---|---|
| 1 | `core/phase_reports.py` — canonical title extraction | **Migrated** | `canonical_phase_id.match_leading_token` (heading-prefix location stays local; ID recognition is canonical) |
| 2 | `core/phase_reports.py` — `_PHASE_ID_SHAPE_RE` / `_parse_phase_id_shape` / `_is_exception_branch` / `is_phase_id_backward` | **Migrated, removed** | `canonical_phase_id.parse` + `canonical_phase_id.compare` |
| 3 | `core/phase_reports.py` — commit-subject phase-token scanning | **Migrated** | `canonical_phase_id.match_leading_token` ("Phase " prefix location stays local; ID recognition is canonical) |
| 3b | `core/phase_reports.py` — `_is_milestone_phase_id` | **Migrated** | `canonical_phase_id.parse` |
| 4 | `core/check.py` — `PROJECT_STATUS.md` current-phase / title extraction | **Migrated, `_PHASE_CODE_RE` removed** | `canonical_phase_id.find_first_token` / `match_leading_token` |
| 5 | `core/architecture_status.py` — `parse_phase_id`, `is_valid_phase_id`, `phase_sort_key`, in-progress trailing-parenthetical extraction | **Migrated, `PHASE_ID_RE`/`_SUBPHASE_PART_RE` removed** | `canonical_phase_id.parse` (public `PhaseIdKey` tuple shape preserved; see Known Narrowing below) |
| 6 | `core/context.py` — bootstrap ambiguity detection, TODO.md staleness | **Migrated, inline regexes removed** | `canonical_phase_id.find_first_token`, `match_leading_token`, `same_branch` |
| 7 | `core/agent.py` — `_TSA_PHASE_CODE_RE` (duplicate of `check._PHASE_CODE_RE`) | **Migrated, removed outright** (CPIPC-REQ-052) | `canonical_phase_id.find_first_token` / `match_leading_token` |
| 7b | `core/agent.py` — `_SIT_PHASE_ID_GRAMMAR_RE` / `_sit_phase_id_grammar_valid` | **Migrated, regex removed** | `canonical_phase_id.is_valid` |
| 8 | `cltr_prototype/identity.py` — `PHASE_ID_RE` / `_validate_phase_id` | **Migrated, `PHASE_ID_RE` removed** | `canonical_phase_id.is_valid` (plus a module-local, non-grammar "no incidental whitespace" round-trip check — see Known Narrowing) |
| 9 | `cltr_prototype/compatibility.py` — `_TITLE_PHASE_TOKEN_RE` | **Migrated, removed** | `canonical_phase_id.find_first_token` |
| 10 | `cltr/authority/identity.py` — `PhaseIdentity` / `_PHASE_IDENTITY_PATTERN` | **Deliberately deferred** | Not migrated — see Deferred Consumer below |
| 11 | `commands/phase.py` — `_VALID_PHASE_ID_RE` (queue validation) | **Migrated, removed** | `canonical_phase_id.is_valid` |
| 12 | `commands/phase.py` — `_PHASE_ID_RE` / `_expand_phase_range` / `_parse_multi_phase_ids*` | **Migrated, removed** | `canonical_phase_id.parse` / `is_valid` (range-arithmetic stays local — CPIPC-001 §7, lifecycle judgment) |
| 13 | `commands/push.py` — `_PHASE_TOKEN_RE` | **Migrated, removed** | `canonical_phase_id.match_leading_token` ("Phase " prefix location stays local) |
| 14 | `core/repository_transition_integration.py` — `parse_phase_id_from_text` | **Migrated** (the one consumer CPIPC-001 §13 flagged as still carrying the unrepaired truncation defect) | `canonical_phase_id.find_first_token` |

Two duplicate-literal pairs identified by Phase 137P (`check._PHASE_CODE_RE`
== `agent._TSA_PHASE_CODE_RE`) are eliminated outright, not carried
forward (CPIPC-REQ-052): both call sites now delegate to the canonical
parser, and neither regex exists anywhere in the codebase any more.

## Deferred consumer: `cltr/authority/identity.PhaseIdentity`

**Not migrated in this phase.** `_PHASE_IDENTITY_PATTERN` (`^[A-Za-z0-9.]{1,16}$`)
is an opaque wire-format/charset boundary check bound to
`identity.schema.json`'s own pattern, not a Phase ID structural grammar
— the module's own docstring states it "validates only the
contract-authorized local syntax ... never performs target lookup,
repository access, existence assertion, or authority inference."

Phase 137P §15 explicitly named this the open "charset-reservation
risk": the wrapper's pattern is broader in charset (digits permitted
anywhere) but narrower in structure (no grammar, just charset+length)
and narrower in length (16-character cap) than CPIPC-001 §4's grammar,
which imposes no branch-letter-length cap. Migrating this wrapper to
construct from a parsed `PhaseId` requires its own compatibility check
against any already-persisted 16-character-max artifact — explicitly
flagged as unresolved implementation work, not decided by the
architecture (137P) or the contract freeze (137Q), and out of this
phase's scope to resolve unilaterally without breaking existing
wire-format compatibility and the dedicated boundary tests in
`tests/test_cltr_authority_136z_shared_core.py`.

This is a documented, deliberate exception (CPIPC-REQ-054), not silent
duplication: `PhaseIdentity` does not implement Phase ID grammar, so it
is not "a second implementation of Phase ID parsing" in the sense
CPIPC-REQ-018 forbids — it is a distinct, narrower wire-boundary type
that happens to share a name with the concept. A future phase should
resolve the charset-reservation risk explicitly before migrating it.

## Known, deliberate narrowings and widenings

Migrating fifteen independently-drifted grammars onto one canonical
grammar necessarily changes behavior at a small number of edge cases
that were themselves defects (narrower or looser acceptance than the
union CPIPC-001 §4 establishes). Each is a direct consequence of
adopting the single frozen grammar, not an incidental side effect:

- **Multi-letter subphase verification suffixes now accepted.**
  `architecture_status.py`'s prior `_SUBPHASE_PART_RE` capped a
  subphase's trailing letters at one character. CPIPC-001's
  `numeric-segment` production allows a run of one-or-more letters.
  `"134E.8VV"` is now valid; a legacy test asserting its rejection
  (`tests/test_architecture_status_generation_independent_verification_134e8v.py`)
  was updated to assert acceptance, with an explanatory comment.
- **Bare numeric series is `reserved`, not accepted.** Any prior
  consumer that treated `"134"` (no branch letter) as valid now
  correctly rejects it (CPIPC-001 §4.2). No inventoried consumer's
  real, historical input data used this form.
- **`architecture_status.parse_phase_id`'s `PhaseIdKey` cannot
  represent a letter-only subphase segment** (e.g. `"113D.R"`): its
  `tuple[int, str]`-per-segment shape has no numeric analogue for a
  letter-segment. `parse_phase_id` returns `None` for such input,
  identical to its pre-migration behavior (this shape was never
  accepted before either, since the old regex required a leading digit
  per segment) — recognition is now canonical, but this call site's
  narrower *return type* still cannot represent every form the
  canonical grammar accepts.
- **`cltr_prototype/identity.py`'s explicit-only round-trip guarantee
  is preserved as a local, non-grammar check.** CPIPC-REQ-032 mandates
  the canonical parser strip incidental whitespace before matching.
  This module's own design intent (CLTR-001 §5, the 135D.1 lesson —
  "no fuzzy/prefix match") requires rejecting a declared `phase_id`
  that carries any leading/trailing whitespace at all. `_validate_phase_id`
  therefore performs `raw.strip() != raw` as an explicit, local,
  non-grammar business rule layered on top of the canonical parser's
  structural recognition — not a second grammar definition.
- **`_detect_phase_ambiguity`'s current-phase base-comparison branch
  was already unreachable dead code for real content before this
  migration** (`PROJECT_STATUS.md`'s "## Current Phase" line always
  begins with the literal word `"Phase "`, so the pre-migration
  anchored `re.match(r"(\d+[A-Z]+)", current_phase)` could never match
  — it always requires a leading digit at position 0). The migration
  preserves this exact behavior byte-for-byte via
  `canonical_phase_id.match_leading_token`, which has the same
  anchored-at-position-0 semantics; the branch remains effectively
  unreachable for realistic `PROJECT_STATUS.md` content. This is a
  faithful preservation of existing (latent) behavior, not a fix — a
  behavior change here would be out of this implementation phase's
  scope.
- **`cltr_prototype/compatibility.py`'s narrative title extraction
  and `push.py`'s done-task phase extraction now correctly recognize
  multi-letter mainline branches** (e.g. `"136AX"`) that the
  pre-migration single-letter-branch or truncating regexes could not.
  This directly closes real historical defect classes (the 136AX
  branch-letter rollover gap; the 137F.1V/137MV.1 truncation defects)
  that CPIPC-001 exists to foreclose (§9, `truncated_extraction`
  taxonomy entry) — an intended outcome of this migration, not a
  side effect.

## Residual, out-of-scope duplication (not part of CPIPC-001 §14's inventory)

Phase 137P's independent inventory (§2.1) additionally found several
narrower, purpose-specific phase-ID-shaped regexes inside
`core/phase_reports.py` beyond the three operations named in CPIPC-001
§14's table for that file (`_LEADING_PHASE_REFERENCE_RE` /
`resolve_canonical_phase_identity`; `_leading_phase_id` /
`_parenthetical_phase_id` closures inside the Architecture Status
consistency checker; `_COMPLETED_PHASE_HEADER_RE` and sibling title/
section regexes feeding `_match_current_phase_declaration`; an inline
commit-message-vs-report-phase check; an informational-only
`rec_id_match`). These were flagged by Phase 137P as evidence of the
same defect class but were never part of the fifteen-call-site,
ten-consumer-group formal inventory this contract's migration
obligation (CPIPC-REQ-051, §14) is scoped to. They are out of this
phase's scope (137R implements exactly the frozen §14 inventory; "no
grammar expansion... no consumer-specific parsing" per this phase's
own governing brief) and are recorded here so a future governed phase
can decide whether to fold them into CPIPC-001's inventory via a
contract revision.

## Removed duplicate definitions

The following module-level regex objects were removed outright
(CPIPC-REQ-052), with no compatibility shim left in their place:

- `phase_reports._CANONICAL_TITLE_PHASE_ID_RE` (replaced by a narrower
  `_CANONICAL_TITLE_PREFIX_RE` that only locates the heading text; the
  actual identifier grammar is `canonical_phase_id`'s)
- `phase_reports._PHASE_ID_SHAPE_RE`
- `phase_reports._COMMIT_SUBJECT_PHASE_TOKEN_RE` (replaced by a
  narrower `_COMMIT_SUBJECT_PHASE_PREFIX_RE`, same pattern as above)
- `check._PHASE_CODE_RE`
- `architecture_status.PHASE_ID_RE`, `architecture_status._SUBPHASE_PART_RE`
- `context._LEADING_PHASE_NUMBER_RE`
- `agent._TSA_PHASE_CODE_RE`, `agent._SIT_PHASE_ID_GRAMMAR_RE`
- `cltr_prototype.identity.PHASE_ID_RE`
- `cltr_prototype.compatibility._TITLE_PHASE_TOKEN_RE`
- `commands.phase._VALID_PHASE_ID_RE`, `commands.phase._PHASE_ID_RE`
- `commands.push._PHASE_TOKEN_RE` (replaced by a narrower
  `_PHASE_TOKEN_PREFIX_RE`, same pattern as above)

After this migration, no lifecycle subsystem in the migrated set
defines its own Phase ID grammar (CPIPC-REQ-058), except the
deliberately-deferred `cltr/authority/identity.PhaseIdentity`
documented above.
