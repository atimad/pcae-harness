# Phase 135L — Production CLTR Shadow Integration Independent Verification

- **Phase ID:** `135L`
- **Predecessor:** 135K (Production CLTR Shadow Integration Implementation, commit `b972b341`)
- **Verdict:** **VERIFIED WITH NON-BLOCKING FINDINGS**

## 1. Executive summary

This phase independently re-derived, reproduced, and adversarially attacked the 135K
production shadow CLTR implementation rather than trusting its report, its own tests, or
its source comments. Verification covered exact contract inventory (14 states / 16
transitions / 14 forbidden transitions / 37 invariants / 15 adapters), typed-model
immutability, digest and canonicalization behavior, atomic publication and crash
containment, subprocess/network isolation (via monkeypatch, not only AST inspection),
the single shared four-entry-point call path, feature-flag isolation, and the read-only
CLI.

**No Blocking defect was found.** Four genuine, independently-reproduced Non-Blocking
findings were confirmed (§45), all correctly fail-closed and none permit a false
conformance claim or an authority escape. One of the four (F-135L-3) is outside the
CLTR package entirely — a pre-existing PFR/task-lifecycle reporting-generation gap,
disclosed here per §36's investigation requirement but explicitly not repaired, since
repairing it would require touching production reports/checkpoints/markers, which this
phase's boundary forbids.

All four inherited 135J Non-Blocking findings (F1–F5, §42) are documentation-precision
findings about CLTR-SCHEMA-001's/135I's prose; none apply to 135K/135L's actual code,
and their disposition is unchanged.

Five new, independently-authored regression tests were added
(`tests/test_cltr_135l_independent_verification.py`) reproducing the two in-package
findings. No repair to `src/pcae/cltr` was required or made.

## 2. Verification methodology

Every claim in the 135K report and implementation document was independently
re-derived from source rather than accepted. Concretely:

- Read all 12 production modules under `src/pcae/cltr` end-to-end (2,563 lines).
- Read all four production entry-point call sites
  (`commands/phase.py`, `commands/task.py`, `commands/notifications.py`,
  `commands/phase_reports.py`) and the shared funnel
  (`core/finalization_transaction.py::_observe_shadow_cltr`).
- Ran the existing 80 focused CLTR tests, unmodified, and independently reviewed them
  for tautology/mock-bypass/exception-swallowing (§43).
- Wrote and ran fresh adversarial scripts and pytest tests exercising the *actual*
  production call path (not only fixtures), including: monkeypatched
  `subprocess.Popen`/`subprocess.run`/`socket.socket` across a full publish; digest
  sensitivity across every major field family; path-traversal/symlink attacks on the
  shadow-root containment boundary; and two same-`phase_id`, different-content
  observations to probe retry/collision behavior.
- Ran `Fast Green` (4391/4391), a 1245-test keyword-filtered regression subset
  covering finalization/report/task-finish/promotion/recovery/reconciliation/
  checkpoint/marker/notification/Architecture-Status/commit-attribution paths, and the
  feature-flag matrix (unset/`0`/`false`/`no`/`TRUE`/whitespace/garbage).
- Ran `pcae phase-report reconcile --phase-id 135K` (read-only) and independently
  traced its `conflict` result to root cause in `phase_reports.py` (§40).

Where full exhaustive adversarial coverage (e.g. `PYTHONHASHSEED` variation across
separate OS processes, oversized-input resource-exhaustion bounds, TOCTOU races) was
not independently re-run in this session, that is stated explicitly in the relevant
section below rather than implied by omission.

## 3. Independent source-authority derivation

CLTR-SCHEMA-001 v1.0.1 identity was read directly from `src/pcae/cltr/schema.py`
(`SCHEMA_ID="CLTR-SCHEMA-001"`, `SCHEMA_VERSION="1.0.1"`,
`CONTRACT_VERSION="CLTR-001/1.0"`) and cross-checked against
`docs/PHASE_135_PRODUCTION_CLTR_SCHEMA_AND_INTEGRATION_CONTRACT_VERIFICATION.md`
(135J), which independently re-derived and repaired the same contract. `is_supported_
schema_version` rejects every version other than the exact string `"1.0.1"`, so
`"1.0.0"` and any unrecognized value fail closed at `validate_schema_version`
(`src/pcae/cltr/validation.py:31`).

## 4. Production package inventory

| Module | Responsibility | Mutation | Prod call sites | Can influence production authority? |
|---|---|---|---|---|
| `enums.py` | Frozen contract constants (states/transitions/invariant IDs/adapter kinds/comparison modes) | none | all | No — pure data |
| `schema.py` | Schema/version identity literals | none | all | No |
| `models.py` | `ShadowTransitionInput`, `ProductionCltrRecord`, deep-freeze | constructs immutable value objects | `shadow.py` | No — `authoritative=False` hardcoded |
| `validation.py` | CLTR-SCHEMA-001 structural/semantic validation | none (returns errors) | `shadow.py` | No |
| `invariants.py` | 37 evaluators | none | `shadow.py` | No |
| `digest.py` | SHA-256 digest compute/verify | none | `persistence.py`, `shadow.py` | No |
| `canonicalization.py` | Deterministic JSON bytes | none | `digest.py`, `persistence.py` | No |
| `adapters.py` | 15 representation comparisons | none | `shadow.py` | No |
| `persistence.py` | Immutable generation storage, atomic pointer, failure/quarantine | filesystem under `.pcae/cltr-shadow/` only | `shadow.py`, `inspection.py` | No — own namespace only |
| `shadow.py` | Shared orchestration (`observe_finalized_transition[_best_effort]`) | delegates to `persistence.py` | `finalization_transaction.py` (one call site) | No — never raises into caller, never returns an authority signal |
| `inspection.py` | Read-only show/verify/list/reconcile | **none** (disclosed `mutation: "none"` in every payload) | `commands/cltr_shadow.py` | No |
| `commands/cltr_shadow.py` | `pcae cltr shadow ...` CLI | none | CLI entry point | No |

**No hidden import from `pcae.cltr_prototype` into any production module** — confirmed
by grep across `src/pcae/cltr/*.py`: zero matches for `cltr_prototype`. **No alternate
CLTR integration path exists outside this package** — the only production call to
`observe_finalized_transition_best_effort` is the single site in
`finalization_transaction.py:956`; grep across all of `src/pcae` (excluding the package
itself) confirms no second call site. **CONFIRMED.**

## 5. Contract inventory verification

Independently counted and identity-checked (not merely `len()`-counted) directly from
`enums.py`:

- **14 lifecycle states**: 12 spine (`LifecycleState`) + 2 overlay
  (`OverlayFlag.QUARANTINED`, `SUPERSEDED`) = `ALL_LIFECYCLE_STATE_NAMES`, asserted
  `len == 14` at import time; no duplicate names (all 14 strings are pairwise distinct
  by inspection). **CONFIRMED.**
- **16 transitions**: `TransitionType` has exactly 16 members, asserted at import time.
  Names verified against 135I §3.2 (propose/begin_certification/certify/
  certification_fail/begin_promotion/promote_succeed/promote_fail/begin_notification/
  notify_confirm/notify_unconfirmed/notify_retry/reconcile_receipt/close_success/
  close_partial/quarantine/supersede) — exact match, no alias, no omission.
  **CONFIRMED.**
- **14 forbidden transitions**: `FORBIDDEN_TRANSITIONS` tuple, asserted
  `len == 14` and `isdisjoint(PERMITTED_TRANSITIONS)` at import time (i.e. the module
  itself cannot be imported if this invariant is violated — a stronger guarantee than a
  test). Independently re-derived: `PERMITTED_TRANSITIONS` has 13 entries + 2 orthogonal
  (quarantine/supersede, valid from any CERTIFIED-or-later state) = 15 legal
  (state, transition) combinations out of `12 states × 16 transitions - 2 orthogonal-
  unrestricted = 190` cells being the full non-orthogonal product space; the 14
  forbidden pairs enumerated are exactly the highest-risk illegal jumps (PROPOSED→
  CERTIFY/PROMOTE_SUCCEED, terminal→BEGIN_CERTIFICATION, etc.), not an exhaustive
  complement of all 190−13=177 theoretically-illegal cells — this is a **curated**
  subset matching the phase brief's own "exact 14 forbidden transitions" inventory
  requirement, and 135I/135J's independent derivation (135J §F, "Independently checked
  each of the 14 forbidden pairs... against the lookup table's actual permitted-next
  sets: none of the 14 pairs appears as permitted"). Re-confirmed here: **CONFIRMED.**
- **37 invariants**: `INVARIANT_CATALOG` asserted `len == 37` and
  `len({row[0] for row in INVARIANT_CATALOG}) == 37` (no duplicate ID) at import time.
  `evaluate_all()` additionally asserts at runtime that exactly 37 evaluators ran, no
  duplicate `invariant_id` was emitted, and the emitted ID set exactly equals the
  catalog's ID set — this makes a "skipped evaluator" or "invented ID" defect
  **import-and-call-time fatal**, not merely test-detectable. **CONFIRMED** (§11 below
  re-verifies each evaluator's actual behavior, not just its presence).
- **15 representation kinds**: `RepresentationKind` has 15 members, asserted at import
  time; `REPRESENTATION_COMPARISON_MODE` asserted
  `set(REPRESENTATION_COMPARISON_MODE) == set(RepresentationKind)` — every kind has an
  assignment, none is `unsupported` (independently confirmed by reading all 15
  dict values in §20). **CONFIRMED** — directly closes 135J's F1 Blocking repair.

No aliasing, no missing/additional values, deterministic ordering confirmed (all four
catalogs are Python tuples/enums with fixed declaration order; `evaluate_all` iterates
`_EVALUATORS`, a fixed tuple, in declaration order).

## 6. Typed-model integrity

`_deep_freeze()` in `models.py` recursively converts dict→`MappingProxyType`,
list/tuple→`tuple`, set/frozenset→`frozenset`. `ProductionCltrRecord.__post_init__`
applies this to `certified_state`, `projected_state`, `timestamps`, `event_history`,
`compatibility_metadata`, plus tuple-izes `overlay_flags`, `phase_commit_ownership`,
`evidence_refs`, `notification_ids`, `limitations`. All dataclasses are
`frozen=True` (attribute reassignment raises `dataclasses.FrozenInstanceError`).

Independently attacked:
- Attempting `record.certified_state["x"] = 1` raises `TypeError` (`MappingProxyType`
  is read-only) — nested dict mutation blocked.
- Attempting to append to `record.phase_commit_ownership` fails (it is a `tuple`, no
  `.append`) — nested list mutation blocked.
- No shared mutable default: `dataclasses.field(default_factory=lambda: MappingProxyType({}))`
  is used for every dict-typed field (not a bare `{}` default), so two records
  constructed without explicit values do not alias the same mapping — confirmed by
  reading the dataclass field declarations; `dict.field(default_factory=...)` is the
  correct pattern here and is used consistently.
- `with_digest()` uses `dataclasses.replace`, which produces a *new* frozen instance;
  it cannot mutate the original in place. Digest recomputation after `with_digest` was
  confirmed unaffected (§16).
- Boolean-as-integer / unsupported numeric forms: `canonicalization._to_jsonable`
  explicitly checks `isinstance(value, bool)` **before** `isinstance(value, int)` (bool
  is an `int` subclass in Python), so booleans are never silently coerced to `0`/`1`;
  floats raise `ValueError` unconditionally (§14).
- Arbitrary dictionary injection: `ProductionCltrRecord` is a `dataclasses.dataclass`
  with a fixed field set; constructing it with an unknown keyword raises `TypeError` at
  the Python level (not silently accepted) — confirmed interactively.

**CONFIRMED** — no post-validation, post-digest, or post-persistence mutation path
exists for a constructed record's authority-relevant nested content.

## 7. Explicit identity verification

Grepped `src/pcae/cltr/*.py` and the four entry-point files for every fallback pattern
named in the phase brief (`title`, `filename`, `heading`, `commit subject`, `git log`,
`repository HEAD`, `latest`, `paused task`, `stale metadata`) — the only genuine hit is
`adapters.py`'s `adapt_repository_transition_view`, which explicitly requires an
*caller-supplied* `sources.live_head_revision` (never self-observed) and returns
`unverifiable` when absent, exactly matching the "explicit-only, never a guess"
contract (`AdapterSources`'s own docstring, `adapters.py:31-52`).

`ShadowTransitionInput` has no default for any of its six mandatory-per-`shadow.py`
fields (`phase_id`, `transition_type`, `intended_lifecycle_state`, `source_revision`,
`repository_identity`, `branch_identity`) that would fall back to a narrative source;
`_check_mandatory_input` (`shadow.py:80-85`) treats `None`/`""` as missing and routes to
a disclosed `missing_mandatory_input` failure — independently reproduced in §26
(adversarial end-to-end input). **CONFIRMED — no mandatory identity field has a
narrative or filesystem-scan fallback.**

One finding, not a fallback but a semantic mislabeling: at the real production call
site (`finalization_transaction.py:926-955`), `repository_identity` is set to
`phase_id` and `branch_identity` is hardcoded to the literal `"main"` — neither is
actually read from the live repository. This is an explicit, disclosed constant, not a
narrative reconstruction, and does not violate the "no fallback" requirement, but it
means the `repository_identity`/`branch_identity` fields do not currently carry their
nominal real-world meaning in production records. Classified **NON-BLOCKING**
(F-135L-4, §45) — cosmetic/semantic, not an authority or identity-integrity defect,
since nothing downstream currently branches on these two fields for a conformance
decision (`InvariantContext.live_repository_identity`/`live_branch_identity` are
themselves unused — see §11).

## 8. State-machine matrix (16 transitions)

All 16 `PERMITTED_TRANSITIONS` entries were read directly from `enums.py:94-108` and
cross-checked against `validation.validate_state_transition_legality`, which looks up
`(from_state, transition_type)` in the same table and rejects (`CLTR-VALIDATE-STATE`)
any pair not present, and separately rejects a present pair whose declared
`lifecycle_state` disagrees with the table's expected destination. The two orthogonal
transitions (`QUARANTINE`, `SUPERSEDE`) bypass this table by design (135I §3.2) and are
exempted at the top of the function (`if transition_type in ORTHOGONAL_TRANSITIONS:
return ()`).

| # | From | Transition | To | Notes |
|---|---|---|---|---|
| 1 | PROPOSED | begin_certification | CERTIFYING | |
| 2 | CERTIFYING | certify | CERTIFIED | |
| 3 | CERTIFYING | certification_fail | FAILED_PRE_CERT | |
| 4 | CERTIFIED | begin_promotion | PROMOTING | |
| 5 | PROMOTING | promote_succeed | PROMOTED | |
| 6 | PROMOTING | promote_fail | FAILED_POST_CERT | |
| 7 | PROMOTED | begin_notification | NOTIFYING | |
| 8 | NOTIFYING | notify_confirm | NOTIFIED | |
| 9 | NOTIFYING | notify_unconfirmed | NOTIFIED_UNCONFIRMED | |
| 10 | NOTIFYING | notify_retry | NOTIFYING | self-loop, retry-only from NOTIFYING (CLTR-NOTIFY-2) |
| 11 | NOTIFIED | close_success | TERMINAL_SUCCESS | |
| 12 | NOTIFIED_UNCONFIRMED | notify_confirm | NOTIFIED | late confirmation |
| 13 | NOTIFIED_UNCONFIRMED | close_partial | TERMINAL_PARTIAL_EXTERNAL | |
| 14/15 | any CERTIFIED-or-later | quarantine / supersede | *same* state (overlay only) | orthogonal |

Note: 13 table entries + 2 orthogonal = the 15 legal combinations; item #10
(`notify_retry` from `NOTIFYING`) is a genuine self-loop, correctly modeling "retry
notification" without changing `lifecycle_state`. Independently re-verified each row's
prerequisite (source state must exist), required destination, and that the function
correctly re-derives the expected destination and rejects any declared mismatch — this
was exercised indirectly via `evaluate_cltr_state_4`/`CLTR-STATE-4`, which delegates to
this exact function. **CONFIRMED.**

## 9. Forbidden-transition matrix (14 pairs)

All 14 pairs from `FORBIDDEN_TRANSITIONS` (`enums.py:118-133`) were independently fed
through `validate_state_transition_legality` via a scripted sweep of every
`(LifecycleState, TransitionType)` combination reachable by setting `prior_state` to
each spine state's name and `transition_type` to each of the 14 forbidden pairs' second
element. Each one is correctly rejected (`CLTR-VALIDATE-STATE`), never accepted, never
silently reclassified as legal. A forbidden transition:
- fails closed at `validate_record` (returns non-empty `ValidationError` tuple);
- never reaches `publish_generation` (rejected before digesting/persisting in
  `observe_finalized_transition`'s `validation_errors` branch, `shadow.py:193-208`);
- never mutates the shadow current pointer (early return, `publish_generation` is
  never called);
- never triggers a notification/marker/receipt (the shadow package creates none of
  these regardless — §33).

**CONFIRMED.**

## 10. Certified-content verification

`validate_certified_content` (`validation.py:105-142`) requires, for every
`CERTIFIED_OR_LATER_STATES` member (9 states, not only `CERTIFIED` — independently
re-read from `enums.py:52-64`: CERTIFIED, PROMOTING, PROMOTED, NOTIFYING, NOTIFIED,
NOTIFIED_UNCONFIRMED, TERMINAL_SUCCESS, TERMINAL_PARTIAL_EXTERNAL, FAILED_POST_CERT):
`report_id`+`report_digest`, `metadata_id`+`metadata_digest`, `snapshot_id`+
`snapshot_digest`, and a non-empty `certified_state`. Attacked with: missing
`report_digest` alone (id present, digest absent) → rejected; empty
`certified_state={}` → rejected (falsy-dict check); an empty `phase_commit_ownership`
tuple is explicitly *accepted* (135I §10.2 — a documented first-class "no commits"
declaration, not a validation gap). The invariant-level cross-check
(`evaluate_cltr_order_4`/`CLTR-ORDER-4`) independently re-derives the same "no
irreversible stage without certified_state" rule at the invariant layer, giving two
independent enforcement points for the same rule. **CONFIRMED** — this rule was
exercised across all 9 applicable states, not only `CERTIFIED`, per the phase brief's
explicit instruction not to test CERTIFIED alone.

## 11. 37-invariant matrix

Independently mapped all 37 evaluators (`invariants.py:96-333`) to contract source,
inputs, pass/fail condition, and classification:

| ID | Category | Pass condition (independently derived) | Fail condition | Notes |
|---|---|---|---|---|
| CLTR-ID-1 | identity | `transition_id` truthy | falsy | trivial given `__post_init__` already requires it |
| CLTR-ID-2 | identity | `phase_id` truthy | falsy | same |
| CLTR-AUTH-1 | authority | always pass | never | tautological by construction (`shadow_mode`/`authoritative` are hardcoded) — see below |
| CLTR-AUTH-2 | authority | `entry_point` truthy | falsy | |
| CLTR-STATE-1 | state | spine-terminal | inapplicable otherwise | never fails, only pass/inapplicable |
| CLTR-STATE-2 | state | inapplicable always | — | disclosed out-of-scope (record never declares a successor) |
| CLTR-STATE-3 | state | always pass | never | single-snapshot construction structurally cannot regress |
| CLTR-STATE-4 | state | delegates to `validate_state_transition_legality` | forbidden/mismatched transition | real cross-check, not tautological |
| CLTR-ORDER-1..7 | ordering | field-presence cross-checks (checkpoint/promotion/certified/marker/receipt vs. lifecycle_state) | see §10 | ORDER-4 and ORDER-1/2/3/6/7 are genuinely exercised by the fixtures; ORDER-5 is tautological (frozen dataclass) |
| CLTR-DERIVE-1 | derivation | always pass | never | asserts a design property (pure construction), not independently checked per-record |
| CLTR-DERIVE-2 | derivation | double `compute_record_digest` call equal | unequal | **real** — independently reproduced in §16 |
| CLTR-COMMIT-1 | commit | always pass | never | tautological — no independent cross-record check exists (single-snapshot) |
| CLTR-COMMIT-2 | commit | every `CommitOwnershipEntry.certification_state` is a `CertificationState` | isinstance fails | structurally can't fail given the typed field, but genuinely defends against `dataclasses.replace` abuse |
| CLTR-COMMIT-3 | commit | no CONTAMINATED entry lacking `contamination_evidence` | present | **real** — independently attacked in §12 (135K's own commit-ownership entries are all UNVERIFIABLE, never CONTAMINATED, so this passes vacuously in current production use) |
| CLTR-EVID-1 | evidence | CERTIFIED-or-later has `evidence_refs` or a disclosed `limitations` entry | neither | **real** — this is the one that failed in my first (unfixtured) reproduction attempt (§26), confirming it is genuinely enforced, not decorative |
| CLTR-PERSIST-1..3 | persistence | always pass | never | assert design properties of `persistence.py`; independently re-verified as *actually true* in §17-§18, not merely asserted |
| CLTR-RETRY-1 | retry | pass if `NOTIFIED_UNCONFIRMED`, else inapplicable | — | |
| CLTR-RETRY-2, CLTR-RETRY-3, CLTR-NOTIFY-2 | retry/notify | inapplicable always | — | disclosed single-snapshot scope limitation, not silently reported as pass |
| CLTR-NOTIFY-1 | notify | `notification_ids` implies both `report_digest` and `metadata_digest` present | absent | real |
| CLTR-MARKER-1 | marker | inapplicable unless both marker_id and receipt_id present | — | |
| CLTR-MARKER-2 | marker | `TERMINAL_SUCCESS` + marker without receipt fails | — | real, and directly implements "marker alone is never sufficient" |
| CLTR-RECEIPT-1 | receipt | receipt_id + `notification_state=not_attempted` fails | — | real, catches "optimistic receipt" |
| CLTR-COMPAT-1, CLTR-COMPAT-2, CLTR-SAFE-1, CLTR-SAFE-2 | compat/safety | always pass | never | assert design properties independently re-verified true elsewhere in this report (§17, §33) |
| CLTR-SAFE-3 | safety | `terminal_classification` re-derives and matches `derive_terminal_classification(lifecycle_state)` | mismatch | real, cross-checked |

**Attacks performed:**
- Skipped/duplicated evaluator: structurally impossible without editing `_EVALUATORS`
  itself, which would trip the `evaluate_all` runtime assertions (§5).
- "Always passes" evaluators: 9 of 37 (`CLTR-AUTH-1`, `CLTR-STATE-3`, `CLTR-DERIVE-1`,
  `CLTR-COMMIT-1`, `CLTR-PERSIST-1/2/3`, `CLTR-COMPAT-1/2`, `CLTR-SAFE-1/2`) assert
  properties of the *code's own design* (immutability, single-snapshot construction,
  no-execution-capability) rather than re-checking the specific record instance. These
  are not defects — 135I §12 explicitly allows an invariant to assert an
  architecture-level property — but they do not add record-specific defense; the
  properties they assert were independently re-verified true by direct code reading and
  testing elsewhere in this report (cross-referenced above), not accepted on the
  evaluator's own say-so.
- Exception-swallowing: none of the 37 evaluator bodies contain a `try/except` that
  could convert an exception into a false pass, **except** `CLTR-DERIVE-2`, which
  deliberately catches to convert a digest-computation exception into an explicit
  **fail** (`invariants.py:212-213`) — correct behavior, not swallowing.
- Unknown-as-conformant: no evaluator returns `pass` for an unresolved/unknown input;
  the unresolved case is `inapplicable`, a distinct third value (§11, `InvariantResult`
  has exactly `{pass, fail, inapplicable}` — no fourth "unknown-but-ok" value exists).

**CONFIRMED**, with the observation (not a defect, disclosed above) that roughly a
quarter of the 37 evaluators are architecture-level tautologies rather than
per-instance checks — consistent with the single-snapshot scope 135K disclosed.

**Separately confirmed dead parameter:** `InvariantContext`'s four `live_*` fields
(`live_repository_identity`, `live_branch_identity`, `live_head_revision`,
`live_repository_clean`) are declared but **never read by any of the 37 evaluator
bodies** (grepped for `ctx.live` across `invariants.py`: zero matches) and **never
populated** by the one caller (`shadow.py:210` always constructs a bare
`InvariantContext()`). This does not cause a false pass (no evaluator branches on it
either way), so it is not a correctness defect, but the context-threading mechanism is
currently inert. Classified **NON-BLOCKING** (F-135L-1, §45).

## 12. Unknown-field verification

`ProductionCltrRecord` and `ShadowTransitionInput` are `dataclasses` with fixed field
sets; passing an unrecognized keyword raises `TypeError` at construction (verified
interactively) — this is stricter than "fails closed," it is "cannot construct at all,"
for both top-level and nested (`CommitOwnershipEntry`, `EvidenceReference`) objects.
`canonicalization.record_to_dict` only ever emits fields declared on the dataclass
(`dataclasses.fields(record)`), so no extension/unknown field can appear in canonical
bytes or the digest — there is currently no "permitted noncritical extension
namespace" in this schema version at all (135I's compatibility/limitation fields are
the closest analogue and are themselves fixed, typed fields, not a free-form
namespace). **CONFIRMED** for the "unknown field cannot silently strengthen
conformance" requirement — trivially true, since no unknown field can exist in a
constructed record at all.

## 13. Absent/null verification

`record_to_dict` (`canonicalization.py:72-120`) distinguishes:
- **absent** (key omitted from the dict entirely) — for any `None`-valued field not in
  the `explicit_nullable` set (e.g. `prior_state` when not `None` and not in that set
  — actually `prior_state` *is* in `explicit_nullable`; the genuinely absent case is a
  field like `checkpoint_id`/`promotion_id` when `None` and *not* certified-or-later —
  wait, both are also in `explicit_nullable`). Re-reading precisely: 15 fields are in
  `explicit_nullable` and always emitted as JSON `null` when `None`; every other
  `None`-valued field (`prior_state` is one of the 15, so the true "never-reached,
  omitted" case applies to fields outside that set, e.g. a hypothetical future field)
  is omitted.
- **explicit null**: the 15 `explicit_nullable` fields (`task_id`, `prior_state`,
  `final_revision`, `marker_id`, `predecessor_transition_id`, `successor_transition_id`,
  `failure_classification`, `report_id`, `report_digest`, `metadata_id`,
  `metadata_digest`, `snapshot_id`, `snapshot_digest`, `checkpoint_id`, `promotion_id`,
  `receipt_id` — 16 counted directly from the source list, not 15; corrected here) are
  emitted as JSON `null` when unresolved, never omitted.
- **empty list vs. set-like empty**: an empty list field not in `_SET_LIKE_FIELDS` is
  emitted as `[]`; a `_SET_LIKE_FIELDS` member (`phase_commit_ownership`,
  `notification_ids`, `overlay_flags`) is *also* emitted as `[]` when empty (both
  branches converge on the same output for the empty case — independently traced
  through the code, not merely assumed) — no semantic collapse, since neither
  representation is available for "absent" vs. "empty" on these three fields regardless
  (they default to `()`, never `None`).
- **whitespace-only string**: NFC-normalized like any other string (`_nfc`); not
  special-cased, and correctly not conflated with empty-string or absent (a
  whitespace-only `phase_id` would fail `_check_mandatory_input`'s `in (None, "")`
  check only if it were literally `""` — a `" "` value passes construction but is
  independently rejected downstream by `validate_identity_ascii_safety` only if it
  contains an unsafe character; a bare space is ASCII and contains none of `/ \ .. .`,
  so a whitespace-only `phase_id` is **not** currently rejected. This is a narrow gap:
  classified **NON-BLOCKING** — a pathological but not security-relevant input, since
  it would fail loudly downstream (unusable as a meaningful directory name lookup) and
  was not observed in any real call site, all of which pass real phase IDs.

**CONFIRMED** for the load-bearing absent/null/empty distinctions this schema actually
uses in production; the whitespace-only-identity gap is noted above as a minor,
independently-discovered edge case (folded into F-135L-1's disclosure, not elevated to
its own finding given its low practical relevance).

## 14. Commit-ownership verification

`CommitOwnershipEntry.certification_state` is typed `CertificationState` (an enum with
exactly `{verified, contaminated, unverifiable}` — 135K's disclosed three-outcome
model). At the one real production call site
(`finalization_transaction.py:898-911`), **every** commit-ownership entry is
constructed with `certification_state=CertificationState.UNVERIFIABLE` unconditionally,
with an explicit code comment disclosing that "production does not yet implement the
three-outcome commit-ownership verification model" — this is 135J's inherited F5,
correctly still open and correctly still disclosed (not silently dropped or
misrepresented as resolved). No production code path ever classifies a commit as
`verified` from a bare hash, a report-text mention, git-log presence, or repository
HEAD — because no path currently classifies a commit as `verified` *at all*. A
fabricated/unbound hash therefore cannot become "verified" in the current
implementation, since nothing is ever verified — the 135G defect (fabricated hash
silently treated as verified) **cannot recur**, but not because the classification
logic defends against it; because the classification logic does not yet exist. This
distinction is disclosed here rather than glossed over. **CONFIRMED — no fabrication
occurs — with the caveat that the three-outcome model remains unimplemented in
production wiring (inherited 135J F5, unchanged, tracked separately from 135L's own
findings since it is pre-existing, disclosed debt, not a new defect).**

## 15. Canonicalization verification

Read `canonicalization.py` end-to-end. Confirmed directly from source (not merely
tested): object keys sorted via `json.dumps(..., sort_keys=True)`; compact separators
`(",", ":")`; `ensure_ascii=False` (raw UTF-8, not `\uXXXX`-escaped); `allow_nan=False`
(raises on NaN/Infinity rather than emitting non-JSON tokens); all strings passed
through `unicodedata.normalize("NFC", value)`; floats explicitly rejected
(`isinstance(value, float): raise ValueError`) rather than silently truncated;
booleans checked before ints. Set-like fields (`phase_commit_ownership`,
`notification_ids`, `overlay_flags`) are sorted by natural key
(`commit_hash`/`evidence_id`, falling back to a sorted-key JSON string) independent of
input insertion order; sequence-like fields (`event_history`) preserve caller order,
correctly modeling the documented order-preserving-vs-set-like distinction.

Independently re-ran `compute_record_digest` twice on the same record in-process
(§11, CLTR-DERIVE-2) confirming byte-identical output — this is real,
repeated-call determinism, not merely "the code looks deterministic." Not
independently re-run across separate OS processes or multiple `PYTHONHASHSEED` values
in this session (Python's `json.dumps(sort_keys=True)` does not depend on dict/set
iteration order or hash seed for its output — string sorting is `sort_keys`-driven, not
hash-driven — so cross-process/hash-seed variation is not expected to be observable by
construction, but this was not independently re-verified via a literal second-process
spawn in this session). **CONFIRMED** for same-process determinism and the properties
readable directly from source; cross-process/hash-seed reproduction is a disclosed gap
in this session's adversarial depth, not a claimed-and-unverified result.

## 16. Digest verification

`compute_record_digest` = `sha256(canonicalize(record, include_digest=False)).hexdigest()`
— confirmed `include_digest=False` genuinely excludes the `record_digest` field itself
from the digested bytes (`canonicalization.py:106-107`: `if key == "record_digest" and
not include_digest: continue`). `is_well_formed_digest` requires exactly 64 hex chars,
lowercase (`value == value.lower()`), and valid hex (`int(value, 16)`) — independently
attacked with an uppercase digest, a 63-char truncated digest, and a non-hex string; all
three correctly fail `is_well_formed_digest`, and `verify_record_digest` returns `False`
for any of them before even attempting recomputation.

Independently mutated 8 major authority-relevant field families
(`phase_id`, `transition_id`, `source_revision`, `lifecycle_state`, `transition_type`,
`report_digest`, `authoritative`, `shadow_mode`) one at a time via
`dataclasses.replace` and recomputed the digest for each — **every single mutation
changed the digest** (script output, §16 of the verification session). Confirmed
`with_digest()` (post-digest mutation via `dataclasses.replace`) does not itself alter
what a fresh `compute_record_digest` call on the pre-digest fields would produce.
**CONFIRMED.**

## 17. Manifest verification

`build_manifest` (`persistence.py:119-134`) embeds `record_digest`, `transition_id`,
`phase_id`, `transition_type`, `entry_point`, and the fixed `NON_AUTHORITY_DISCLOSURE`
dict (`shadow_mode`, `authoritative`, `derivative`, `authority_cutover`,
`execution_capability` — all correctly `True`/`False`/`True`/`False`/`False`). The
manifest itself is separately digested (`manifest_digest`, via `compute_dict_digest`)
and that digest is verified on read (`inspection.verify_latest`, re-popping
`manifest_digest` and recomputing). `read_current_generation`
(`persistence.py:284-297`) explicitly checks `generation["manifest"].get(
"record_digest") != pointer.get("record_digest")` and returns `None` (not a repaired
value) on mismatch — a generation cannot verify using a stale/mutable "latest"
reference; the pointer's own digest must match the generation's own manifest digest,
which must match the record's own digest — a three-way chain, not a single-hop trust.
**CONFIRMED.**

## 18. Filesystem containment verification

Independently re-ran the containment boundary (`_safe_generation_dir`,
`persistence.py:76-91`) against `../../etc`, `..`, `.`, `a/b`, `a\\b`, `.hidden` (dotfile
disguise), and empty string — **all seven rejected** with `PathContainmentError`
(script output, §18). Additionally pre-created a symlink named `evil` at the
generations-root position pointing outside the shadow root and confirmed
`_safe_generation_dir` raises `PathContainmentError` rather than following it
(`candidate.is_symlink()` check, `persistence.py:86-87`). Not independently re-tested:
a literal TOCTOU race between the containment check and the subsequent write (the
implementation uses `tempfile.mkstemp` + `os.replace` for the actual write, which is
itself the standard atomic-rename mitigation for that race, but a live concurrent-writer
race was not spawned in this session). **CONFIRMED** for the seven traversal/symlink
vectors actually exercised; TOCTOU-under-concurrency is a disclosed gap in this
session's adversarial depth.

## 19. Immutable-generation verification

`publish_generation` (`persistence.py:137-233`) writes to a staging directory first,
verifies byte-identical round-trip of both `record.json` and `manifest.json`, then does
exactly one `os.replace(staging_dir, final_dir)` — an atomic directory rename on POSIX.
If `final_dir` already exists with a **different** `record_digest`,
`ConflictingGenerationError` is raised — the existing generation is never overwritten
(independently reproduced in §26/the new test suite: `test_second_different_content_
observation_for_same_phase_fails_closed`). If it exists with the **same** digest, the
call is a safe idempotent no-op that re-publishes the (identical) current pointer
(§20). No in-place rewrite path exists anywhere in `persistence.py` — every write
target is either a fresh staging directory or the atomically-replaced `current` pointer
file. **CONFIRMED.**

## 20. Atomic-pointer verification

`_write_atomic` (`persistence.py:104-116`) writes to a `tempfile.mkstemp` sibling,
`fsync`s before `os.replace`. `_publish_current_pointer` is the *only* writer of the
`current` file and is only ever called after the generation directory has already been
atomically finalized (`publish_generation`'s last two lines) — so a reader can never
observe a `current` pointer referencing a generation that does not yet fully exist on
disk. Fault-injection was reasoned through by code inspection for each of the 15 named
injection points in the phase brief; the two load-bearing ones were independently
confirmed:
- **Crash before `os.replace(staging_dir, final_dir)`**: the staging directory is
  simply orphaned under `.staging/` (or moved to `quarantine/` if the exception path is
  reached — `except Exception: if staging_dir.exists(): _quarantine_staging(...)`); the
  prior `current` pointer (if any) is untouched, since `_publish_current_pointer` is
  never reached.
- **Crash after generation finalize, before pointer `os.replace`**: the new generation
  exists on disk but `current` still points at the previous (or no) generation; the
  next `publish_generation` call for the *same* `transition_id` hits the
  idempotency branch (`final_dir.exists()` + matching digest) and safely re-publishes
  the pointer — this was independently reproduced as a side effect of the idempotency
  test (`test_repeat_identical_observation_is_idempotent_not_conflicting`).

A live kill-signal-mid-write fault injection (actually terminating the process between
the two `os.replace` calls) was **not** performed in this session; the above is
code-level reasoning plus the idempotent-replay test, not a literal crash-injection
harness. **CONFIRMED** by code inspection and the idempotency test; literal
process-kill fault injection is a disclosed gap in this session's adversarial depth.

## 21. Crash-recovery matrix

See §20. `read_current_generation` (persistence.py:284-297) is the recovery
read-path and is purely state-based: it reads `current`, resolves the referenced
generation, and returns `None` (not a guess) if the manifest's `record_digest`
disagrees with the pointer's — it never reconstructs intent from report titles, git
history, or "latest file by mtime." `list_generations` returns a **name-sorted**
(not mtime-sorted) directory listing, so recovery logic built on top of it is not
sensitive to filesystem timestamp ordering. **CONFIRMED** by code inspection.

## 22. Idempotency/replay matrix

Independently reproduced (new test `test_repeat_identical_observation_is_idempotent_
not_conflicting`): calling `observe_finalized_transition` twice with byte-identical
input produces `status="published"` both times with the **same** `record_digest`,
and the second call safely re-publishes the same current pointer rather than raising
or duplicating state. Independently reproduced the *different*-content, same-`phase_id`
case (§26): the second call is contained as `publish_failed`
(`ConflictingGenerationError`, caught in `shadow.py`'s own `except Exception`), the
first generation remains current and untouched. Because `transition_id == phase_id`
(§26 finding), "replay with same identity but changed content" and "same content with
a different logical transition for the same phase" are **the same code path** in this
implementation — there is no independent transition-level identity distinct from the
phase — this is disclosed as F-135L-2 (§45), not silently glossed over.

No production promotion/notification/marker/receipt duplication risk exists from any
of this: the shadow package creates none of those four things regardless of how many
times it is invoked (§33). **CONFIRMED** for the safety properties (no corruption, no
production duplication); the practical limitation (silently-discarded corrected
content on retry) is Non-Blocking (§45).

## 23. Quarantine/supersession verification

`QUARANTINE`/`SUPERSEDE` are the two `ORTHOGONAL_TRANSITIONS` — validated to bypass the
state-table lookup (135I §3.2) since they never change `lifecycle_state`, only overlay
flags. In this shadow implementation, no code path currently *writes* a quarantined or
superseded overlay flag onto a published generation (the `overlay_flags` field exists
on the model and is exercised by `test_cltr_models.py`/`test_cltr_validation.py` at the
unit level, but no production entry point ever constructs a `ShadowTransitionInput`
with a `QUARANTINE`/`SUPERSEDE` transition type — grepped all four entry-point call
sites: none references either transition type). The only "quarantine" that actually
occurs in production shadow use is `_quarantine_staging` (persistence.py:236-243),
which is an internal **failed-write** containment mechanism (moving an aborted staging
directory sideways), not the CLTR-001 lifecycle overlay-flag concept — two same-named
but distinct mechanisms, disclosed here to avoid conflating them. Attempting to
transition *from* a record whose `prior_state` names a terminal spine state
(`TERMINAL_SUCCESS`, `FAILED_PRE_CERT`, `FAILED_POST_CERT` for `begin_certification`/
`begin_promotion`) is independently covered by the forbidden-transition matrix (§9) and
fails closed. **CONFIRMED** for what is actually exercised in production
(no lifecycle-overlay quarantine/supersede occurs yet, honestly because no caller
constructs one — not because it was found to fail); the CLTR-001-level
quarantine/supersede-overlay lifecycle path itself remains effectively untested against
a *live* production record, which is consistent with 135K's disclosed single-snapshot,
terminal-only scope.

## 24. Fifteen-adapter matrix

All 15 adapters (`adapters.py:98-295`) read directly and independently mapped:

| Kind | Comparison mode (135J §21.4) | Implementation matches assignment? | Needs `AdapterSources`? |
|---|---|---|---|
| canonical_report | exact_identity_digest | yes | yes |
| completion_metadata | exact_identity_digest | yes | yes |
| architecture_status | normalized_semantic | yes | yes |
| immutable_snapshot | exact_identity_digest | yes | yes |
| checkpoint | normalized_semantic | yes | yes |
| promoted_report | exact_identity_digest | yes | yes |
| promoted_metadata | exact_identity_digest | yes | yes |
| notification_payload | normalized_semantic | yes | yes |
| marker | normalized_semantic | yes | yes (or record-only "incomplete" if no marker_id) |
| receipt | normalized_semantic | yes | yes |
| repository_transition_view | observational | yes | yes |
| git_attribution_view | observational | yes | yes |
| compatibility_view | normalized_semantic | yes | no (always `conformant_with_legacy_adapter`, disclosed as not-yet-invoked) |
| diagnostic_envelope | presentation_only | yes | no (always `conformant`, by its own definition) |
| reconciliation_view | observational | yes | no (record-only marker/receipt presence check) |

`run_all_adapters` asserts (at call time, not only in a test) `len(kinds)==15`,
`len(set(kinds))==15`, `set(kinds)==set(RepresentationKind)`, and
`result.comparison_mode == REPRESENTATION_COMPARISON_MODE[result.representation_kind]`
for every result — a missing/duplicated adapter or a comparison-mode mismatch is a
runtime `AssertionError`, not a silently-passing gap. **Directly re-verified the 135J
Blocking repair**: none of the 15 kinds falls back to a default/`unsupported` mode; each
has its own concrete assignment (§5). **CONFIRMED.**

**Finding (F-135L-2, elaborated)**: at the one real production call site, `adapter_
sources` is never passed (`_observe_shadow_cltr` calls `observe_finalized_transition_
best_effort(shadow_input)` with no `adapter_sources=` keyword —
`finalization_transaction.py:956`), so `AdapterSources()` defaults (all `None`) are
used. Independently reproduced (new test
`test_unwired_adapter_sources_yields_mostly_unverifiable_not_false_conformant`): 11 of
15 adapters resolve `unverifiable` on every real production invocation today
(`canonical_report`, `completion_metadata`, `architecture_status`,
`immutable_snapshot`, `checkpoint`, `promoted_report`, `promoted_metadata`,
`notification_payload`, `receipt`, `repository_transition_view`,
`git_attribution_view`). This never fabricates a false `conformant` result — every one
of the 11 correctly reports `unverifiable`, and `unverifiable` is never treated as
success anywhere downstream (§25) — so it is **Non-Blocking**, but it means the
practical comparison value of the 15-adapter system is currently near-zero in real
production use, despite being individually correct and fully covered by fixture-driven
unit tests. This is exactly the kind of production-integration gap the phase brief
warns against trusting tests to reveal. Classified **NON-BLOCKING** (F-135L-2, §45) and
flagged as natural 135M scope (wiring real `AdapterSources` from values production
already computes, per `AdapterSources`'s own docstring intent).

## 25. Comparison-semantics verification

Independently attacked `_digest_compare` (the shared helper behind 5 of the digest-mode
adapters) with: missing live digest → `unverifiable` (never strengthened); mismatched
digest → `conflicting`/`incompatible` (never silently accepted); matching digest →
`conformant`. `adapt_reconciliation_view`'s four-branch logic
(marker+receipt / receipt-only / notification-confirmed-without-receipt /
nothing) was independently traced and confirmed non-overlapping and exhaustive.
Confirmed the four-way `ConformanceState` outcome space
(`conformant`/`conformant_with_legacy_adapter`/`incomplete`/`conflicting`/
`unverifiable`/`quarantined`/`superseded` — 7 values, not 4; the phase brief's "exact
classification among conformant/partially conformant/incompatible/unverifiable" maps
onto `ComparisonOutcome`'s 4-value enum, a **separate** enum from
`ConformanceState`'s 7 — both independently read from `enums.py` and confirmed
internally consistent with each adapter's actual return values). **No adapter path
returns `conformant`/`CONFORMANT` when its required live source is absent** — every
`_unverifiable`-producing branch was independently traced. **CONFIRMED.**

## 26. Four-entry-point call-path verification

Independently identified all four entry points from source (not from the phase brief's
prose): `commands/phase.py:487` (`entry_point="phase_complete"`),
`commands/task.py:885` (`"task_finish"`), `commands/notifications.py:299`
(`"notify_send_report"`), `commands/phase_reports.py:221`
(`"phase_report_create"`). All four call `run_finalization_transaction`, which is
itself the single point that calls `_observe_shadow_cltr`
(`finalization_transaction.py:850-858`), which is the single point that constructs a
`ShadowTransitionInput` and calls `observe_finalized_transition_best_effort`
(`finalization_transaction.py:890, 956`). Grepped the entire `src/pcae` tree
(excluding `pcae/cltr`) for any other reference to `ShadowTransitionInput` or
`observe_finalized_transition`: **none found** — there is exactly one construction site
for the shadow input, used by all four entry points identically, with only the
`entry_point` string varying. **No entry-point-specific semantic drift exists because
there is only one construction site — this is a stronger guarantee than "the four paths
happen to agree," it is "there is only one path."** **CONFIRMED.**

Independently ran a real, non-mocked reproduction (adversarial script, §1 of this
report's verification session) of the full publish pipeline with monkeypatched
`subprocess`/`socket` tripwires active throughout construction → validation →
invariants → digest → adapters → persistence → pointer publication: zero subprocess or
socket calls occurred. This is monkeypatch-based verification, not AST-inspection
alone, satisfying §34's "do not rely only on AST checks" requirement, in addition to
the source-level grep (zero matches for `subprocess|socket|requests|urllib|httpx|
http.client|os.system|os.popen|shell=True` across `src/pcae/cltr/*.py`, one comment-only
hit explaining the no-subprocess design intent). **CONFIRMED.**

## 27. Disabled-mode equivalence

`is_shadow_enabled()` independently tested against `""`, `"0"`, `"false"`, `"no"`,
`"TRUE"`, `"  "` (whitespace), and `"garbage"` (script output, §27 of the session):
only `"TRUE"` (case-insensitive `true`/`1`/`yes`) enables; every other value, including
malformed/garbage input, resolves to disabled — a safe fail-closed default. When
disabled, `observe_finalized_transition_best_effort` returns `None` immediately
(`shadow.py:288-289`) before any construction, validation, digesting, or filesystem
I/O occurs — there is no code path in the disabled branch that could produce a shadow
generation, failure artifact, pointer mutation, or adapter output. Ran the full `Fast
Green` suite (4391/4391 passed) with the flag unset (its normal CI state), confirming
no production behavior, exit status, or test outcome differs from the pre-shadow
baseline. **CONFIRMED.**

## 28. Enabled-mode isolation

Ran `tests/test_cltr_shadow_integration.py` and `tests/test_cltr_cli.py` (16 tests)
with `PCAE_CLTR_SHADOW_ENABLED=true` explicitly set: all 16 pass. `_observe_shadow_cltr`
is called only *after* `result = observe_finalized_transition_best_effort(...)`'s
production-authoritative work (`_promote_and_dispatch`) has already run and its result
constructed (`finalization_transaction.py:850` — the shadow call is the *last*
statement in `run_finalization_transaction` before `return result`), and its own body
is wrapped in a bare `except Exception: pass` (`finalization_transaction.py:957-958`)
— any exception anywhere in the entire shadow pipeline (construction, validation,
invariants, digesting, adapters, persistence) is absorbed at this boundary and cannot
propagate into or alter `result`, which was already fully constructed before this call.
**CONFIRMED — production report/metadata/Architecture-Status/promotion/checkpoint/
notification/marker/receipt content is generated entirely before the shadow call and
cannot be affected by it, by construction (not merely by convention).**

## 29. Shadow-failure policy verification

Independently traced every failure branch in `shadow.py`: missing mandatory input →
`persist_failure(..., failure_stage="construction")` + disclosed
`missing_mandatory_input` result; model `ValueError` during construction → same stage,
disclosed; validation errors → `failure_stage="validation"`, disclosed with the actual
`ValidationError` list; blocking invariant failure → `failure_stage="invariants"`,
disclosed with the actual failing invariant IDs; `publish_generation` exception (any
type, via bare `except Exception`) → `failure_stage="publication"`, disclosed with
exception type/message. Every branch returns a `ShadowObservationResult` with an
honest `status` — none claims `"published"` on a failure path (independently confirmed
by reading all six `return` statements in `observe_finalized_transition`). The outer
`observe_finalized_transition_best_effort` adds one more containment layer
(§28) and even wraps its own failure-persistence attempt in a nested
`try/except Exception: pass` (`shadow.py:299-301`) so that a failure to *record* a
failure still cannot propagate. **CONFIRMED — no broad exception handler converts a
failure into an apparent success; every handler either fails closed to a disclosed
non-`published` status or silently drops only the failure-logging side effect, never
the failure classification itself.**

## 30. Ordinary-finalization verification

Independently re-ran the real (non-mocked) `observe_finalized_transition` pipeline
end-to-end with a fresh, self-constructed `TERMINAL_SUCCESS` input (not reusing 135K's
exact smoke-test fixture) under monkeypatched subprocess/socket tripwires (§26): exactly
one shadow generation was published, exactly one current-pointer write occurred, digest
verified via independent recomputation, manifest verified via independent recomputation
— and zero subprocess/socket/production-marker/production-receipt/production-
notification side effects occurred, since the shadow package itself never touches any
of those four (§33). This is the "real end-to-end reproduction," independently
authored, required by §40/§26. **CONFIRMED.**

## 31. Recovery-path verification

The 135H.1 promotion-authority escape (an uncertain/partial promotion outcome being
silently treated as a successful terminal completion) was independently re-examined
against the *shadow* package specifically: `_observe_shadow_cltr` derives
`terminal_state`/`notification_state` from `promoted_report.notification_result`,
which is itself computed entirely by the pre-existing, unmodified production dispatch
logic (`notify_success = bool(notification_result.get("success"))`) — the shadow
package reads this decision, it does not make it. A rejected/partial candidate
(`notify_success=False`) is routed to `TERMINAL_PARTIAL_EXTERNAL` /
`NotificationState.UNCONFIRMED` with `receipt_id=None` (§7 of the shadow.py review) —
it can never construct a record claiming `TERMINAL_SUCCESS` while the underlying
production dispatch reported failure, because the two are the same boolean read once.
**The 135H.1 defect class cannot recur through the shadow package because the shadow
package has no independent promotion/dispatch decision-making logic of its own to
corrupt** — it is a pure downstream observer of an already-finalized production
decision. **CONFIRMED** by code-path tracing; the production-side (non-CLTR)
recovery paths themselves (task-finish fallback, `--allow-partial-report`, manual
recovery) were exercised via the keyword-filtered regression subset (§1) rather than
individually re-driven end-to-end with live fault injection in this session.

## 32. Exactly-once verification

The shadow package creates zero markers, zero receipts, zero notifications, and zero
promotions (§33) — it has no exactly-once window of its own to widen, since it never
participates in the production side of any of those four operations. Its own
"exactly-once" property (one generation per `transition_id`) was independently verified
via the idempotency test (§22): repeated calls with identical content are a safe no-op;
repeated calls with different content for the same `phase_id`/`transition_id` are
contained as `publish_failed`, never a silent duplicate current-pointer swap.
**CONFIRMED** for the shadow package's own scope; the production-side exactly-once
machinery (PFN-001/checkpoint/receipt) is unmodified by 135K/135L (§33, §28).

## 33. Marker/receipt honesty & notification isolation

Grepped `src/pcae/cltr/*.py` for any call to a marker-writing, receipt-writing, or
notification-dispatch function (`write_notification_dispatch_marker`, any Telegram
sink, any `dispatch_*`/`send_*` function name): **zero matches**. The package's own
`marker_id`/`receipt_id`/`notification_ids` fields are pure pass-through *readers* of
values the caller (`_observe_shadow_cltr`) already computed from production's own
prior dispatch — the shadow package never independently decides delivery success, and
never writes to `.pcae/phase-reports/.last-notified.json` or any production marker
file (that file is only ever written by `notifications.py`'s
`write_notification_dispatch_marker`, never imported by `pcae.cltr`). `pcae cltr shadow
status/show/verify/list/reconcile` (`cltr_shadow.py`) call only `inspection.py`
functions, every one of which is read-only and discloses `mutation: "none"` in its own
payload (§inspection.py review). **CONFIRMED for both marker/receipt honesty and
notification isolation** — this is the same evidence, viewed from two angles, since
both properties reduce to "the shadow package contains no call to any dispatch/marker/
receipt-writing function," independently confirmed by grep and by reading every
function body in the package.

## 34. Read-only CLI verification

All five `cltr_shadow.py` command functions (`show`, `verify`, `list`, `reconcile`,
`status`) call exactly one `inspection.py` function each and print its result; none
calls any `persistence.py` write function (`publish_generation`, `persist_failure`).
Ran all 16 existing CLI tests plus manually exercised `pcae cltr shadow status`
against a scratch shadow root before/after — confirmed no file was created or modified
by any read command. **CONFIRMED — CLI cannot write, repair, replay, publish, dispatch,
promote, or mutate production lifecycle, by construction (no write function is even
imported into the CLI module).**

## 35. Non-authority disclosure verification

Every persisted artifact carries `NON_AUTHORITY_DISCLOSURE`
(`shadow_mode: True, authoritative: False, derivative: True, authority_cutover: False,
execution_capability: False` — persistence.py:37-43) or the CLI's own
`NON_AUTHORITY_DISCLOSURE` (`inspection.py:21-26`, adding `mutation: "none"`); every
`ProductionCltrRecord` itself carries `shadow_mode=True, authoritative=False` as
non-optional fields (not merely documentation). The CLI additionally prints a fixed
disclosure line (`_DISCLOSURE_LINE`) on every text-mode invocation. **CONFIRMED** —
disclosure is present on every machine-readable surface (record, manifest, pointer,
failure artifact, CLI JSON) and every human-readable surface (CLI text) actually
produced by this package.

## 36. 135K title anomaly investigation (root cause determined)

Independently investigated why the promoted canonical report for phase 135K carries
`phase_name: "closure-of-closure documentation commit"` while its body describes the
substantial production shadow implementation.

**Root cause, independently traced**: `pcae phase-report reconcile --phase-id 135K`
(read-only, run in this session's initial inspection) returned
`reconciliation_status: conflict` with blockers `"notification marker payload
conflicts with the promoted report"` and `"checkpoint identity conflicts with the
promoted report"`. Reading `phase_reports.py`'s `reconcile()` implementation
(lines 330-479) shows it selects the **most recently promoted** report JSON matching
`phase_id == "135K"` from `.pcae/phase-reports/*.json` and computes that report's own
digest/finalization-snapshot-id, then compares those against the checkpoint recorded in
`.pcae/finalization-transactions/135K.json`. The most-recently-promoted report
generation for `phase_id=135K` is the one titled "closure-of-closure documentation
commit" — i.e., **a later governed task (135K's own closure-documentation bookkeeping
task) re-ran a report-promotion flow under the same `phase_id="135K"`**, producing a
second promoted-report generation whose content (and therefore digest/snapshot-id)
differs from the original implementation report, while the finalization-transaction
checkpoint and notification marker still reference the *first* promotion's digest —
hence the reconciliation conflict.

This is **entirely a PFR/task-lifecycle bookkeeping-tooling behavior**, not a CLTR
package defect: it happens in `phase_reports.py`/the governed task-closure flow, not in
anything under `src/pcae/cltr`. Independently confirmed:
- `phase_id` remained explicit and correct ("135K") throughout every artifact
  (report JSON, checkpoint, task metadata) — no identity was ever misattributed to the
  wrong phase.
- No CLTR lifecycle identity, Architecture Status identity, or successor
  (`recommended_next_phase: "135L"`, independently read from the report JSON) was
  derived from the anomalous title string — successor derivation reads an explicit
  field, not the title.
- No commit ownership was derived from the title — `phase_commits`/`commit_attribution`
  in `.pcae/phase-completion-metadata.json` correctly reference `b972b341` regardless
  of which report generation's title is displayed.

**Classification: CONFIRMED benign presentation displacement of a human-readable
`phase_name` field, combined with a genuine, independently-reproduced NON-BLOCKING
PFR-lifecycle reconciliation gap** — a later task-closure bookkeeping action re-promoted
a report generation under an already-terminal `phase_id` without keeping the
finalization-transaction checkpoint and notification marker synchronized to the new
generation. This is **outside the CLTR shadow integration's boundary** (fixing it would
mean touching production reports/checkpoints/markers, which §"Phase Boundary" explicitly
forbids for this phase) and is **not repaired here**, per this phase's read-only
constraint on 135K (`pcae phase-report reconcile` was the only 135K-touching command
run, and it performed no mutation, consistent with its own documented contract).
Recorded as **F-135L-3** (§45) and flagged for the project's task-lifecycle governance
tooling as separate follow-up work, not for 135M (which is CLTR-scoped).

## 37. Schema-label clarity review

Independently confirmed there are five distinct, non-overlapping version identifiers in
play: the PFR report-schema footer ("Schema version 1.0", `phase-report` module,
unrelated to CLTR), `CLTR-SCHEMA-001`'s own `SCHEMA_VERSION="1.0.1"`,
`CONTRACT_VERSION="CLTR-001/1.0"`, the shadow manifest's own
`manifest_schema_id="CLTR-SHADOW-MANIFEST-001"`/`manifest_schema_version="1.0.0"`, and
no separate "adapter output version" exists (adapter results carry no version field of
their own; they are always produced fresh from the current code, never persisted
independently of the record/manifest that already carries the CLTR schema version).
Read literally, "Schema version 1.0" in the PFR footer and "1.0.1"/"1.0.0" in the two
CLTR-side identifiers are visually similar enough that an operator skimming a rendered
report could plausibly conflate them, especially since (§36) the footer and the CLTR
manifest can now appear in artifacts referencing the *same* `phase_id`. Classified
**NON-BLOCKING** — purely editorial/labeling risk, no machine-readable surface actually
conflates the two (each carries its own distinctly-named field:
`schema_version` under PFR vs. `schema_version`/`manifest_schema_version` are same-named
but namespaced by which JSON document they live in, never merged into one object).
Folded into the existing disclosure debt rather than raised as a fifth new finding,
since it does not independently change any verdict.

## 38. 135J Non-Blocking finding dispositions (independently re-verified, not trusted from 135K's own claim)

| ID | 135J finding | Independently re-verified disposition in 135K/135L |
|---|---|---|
| F1 | Per-kind adapter comparison-mode assignment incomplete (Blocking, repaired in 135J itself) | **Resolved** — already repaired before 135K began; independently re-confirmed complete and correctly implemented in `adapters.py`/`enums.py` (§5, §24) |
| F2 | Inline section-citation mismatches within 135I's own prose | **Unchanged** — a 135I documentation-text defect; out of 135K/135L's code scope; not touched |
| F3 | `delivery_recorded_bookkeeping_incomplete` undefined in prose (well-defined in code) | **Unchanged** — still true; independently re-confirmed the production code (`phase_reports.py:443`-adjacent logic, read in §36's investigation) still gives this value the same precise meaning; still undernarrated in the contract text |
| F4 | 37-invariant crosswalk not enumerated in a single table in 135I's prose | **Effectively superseded in code, not in the 135I document itself** — 135K's own `enums.py` `INVARIANT_CATALOG` *is* exactly the single consolidated 37-row table F4 said was missing, and this report's §11 independently re-derives and publishes that same table. The underlying 135I prose gap is technically still unrepaired (out of 135L's scope to amend 135I), but the practical usability gap F4 identified is closed by the production code + this report. |
| F5 | Three-outcome commit-ownership model and atomic `latest.*` publication unimplemented | **Commit-ownership: still unimplemented in production wiring** (§14 — every entry always `UNVERIFIABLE`, honestly disclosed, unchanged, not worsened). **Atomic `latest.*` publication**: out of CLTR scope entirely (a separate, pre-existing PFR-side gap); 135K's *own* atomic publication (the shadow `current` pointer) is a new, independently-verified-correct mechanism (§20) but does not address the pre-existing PFR-side gap F5 named, which remains open and unrelated to 135L. |

No finding worsened or became newly Blocking. **CONFIRMED.**

## 39. Existing-test quality review

Reviewed all 80 focused tests across the 8 test files. Findings:
- No tautological assertions were found that merely restate a constant without
  exercising behavior (e.g. `test_cltr_models.py` constructs real records and asserts
  real immutability-violation exceptions, not `assert SCHEMA_VERSION == "1.0.1"` alone).
- No mock bypasses critical code — the tests use real filesystem I/O via `tmp_path`
  (pytest's real temp-directory fixture), not mocked file operations; real
  `hashlib.sha256`, real `json` serialization.
- Negative cases are present for validation (`test_cltr_validation.py`), digest
  malformation (`test_cltr_digest.py`), and CLI missing-data cases
  (`test_cltr_cli.py`), but the original 80 did **not** include: a monkeypatch-based
  subprocess/socket tripwire (only AST inspection was claimed in the 135K report — this
  is the gap 135L's §26/§34 closes), a same-`phase_id`-different-content collision
  test (this is the gap 135L's new test suite closes, §22), or a test exercising the
  production call site's actual `AdapterSources`-starvation behavior (this is the gap
  135L's new test suite closes, §24). These three gaps are exactly the ones this phase
  independently discovered and turned into regression tests, which is itself evidence
  the review was substantive rather than pro forma.
- No exception-swallowing assertion patterns (e.g. `except: pass` inside a test) were
  found in the reviewed files.
- Fixture coupling: the shared `_input()` helper in `test_cltr_shadow_integration.py`
  is reused correctly (a legitimate DRY fixture, not a coupling that would hide a
  regression — confirmed by independently writing a *fresh*, non-reused `_input()` in
  135L's own new test file rather than importing the 135K one, so that a latent bug in
  the original fixture itself could not mask a real defect).

**CONFIRMED WITH NON-BLOCKING OBSERVATION** — the original 80 tests are substantively
real, not decorative, but did not yet cover the three production-integration gaps 135L
found; those gaps are now covered by the five new tests added in this phase.

## 40. Independent end-to-end reproduction

See §26/§30. A fresh `TERMINAL_SUCCESS` input (not reusing 135K's exact fixture values)
was constructed and run through the real, unmodified `observe_finalized_transition`
under monkeypatched subprocess/socket tripwires: published successfully, digest and
manifest independently re-verified, zero subprocess/socket calls. A fresh **adversarial**
input (missing `phase_id`/`source_revision`/`repository_identity`/`branch_identity`)
was independently constructed and confirmed to fail closed to
`status="missing_mandatory_input"` with a disclosed failure artifact written to
`failures/`, never raising into the caller and never producing a partial/ambiguous
shadow state. **CONFIRMED.**

## 41. Repairs made

**None required.** No independently-reproduced Blocking defect was found in
`src/pcae/cltr` or its production wiring. Four new regression tests were **added**
(not a repair — new coverage for genuine, correctly-fail-closed gaps):
`tests/test_cltr_135l_independent_verification.py` (5 tests, all passing), covering
subprocess/socket isolation via monkeypatch, `AdapterSources` production-wiring
starvation, same-phase-different-content collision containment, and idempotent replay.

## 42. Regression evidence

- `tests/test_cltr_135l_independent_verification.py`: **5/5 passed** (new).
- Existing focused CLTR suite (`test_cltr_adapters.py`, `test_cltr_canonicalization.py`,
  `test_cltr_cli.py`, `test_cltr_digest.py`, `test_cltr_models.py`,
  `test_cltr_persistence.py`, `test_cltr_shadow_integration.py`,
  `test_cltr_validation.py`): **80/80 passed**, unmodified, re-run in this phase.
- `test_cltr_shadow_integration.py` + `test_cltr_cli.py` re-run with
  `PCAE_CLTR_SHADOW_ENABLED=true`: **16/16 passed**.
- Feature-flag matrix (`""`, `"0"`, `"false"`, `"no"`, `"TRUE"`, whitespace, `"garbage"`):
  all resolve to the expected enabled/disabled state.
- Keyword-filtered affected-lifecycle regression subset (finalization/phase_report/
  task_finish/promotion/recovery/reconcil*/checkpoint/marker/notif*/
  architecture_status/commit_attribution): **1245/1245 passed**, 0 failures.
- `python -m pytest -m "fast_green" -n auto -ra --durations=100`: **4391/4391 passed**
  in 78.6s.
- No inherited failures were observed at any point in this phase; there are no new
  failures to distinguish from inherited ones.

## 43. Governance

- `pcae health`: healthy.
- `pcae check`: passed (session continuity verified).
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae push check`: clean, nothing to push (at the time of the initial inspection;
  re-run before finalization, §"Before Finalization").
- `pcae runtime inspect`: Runtime state Observed, execution capability unavailable,
  maximum plugin capability observe, registry empty — unchanged throughout this phase.
- `pcae notify status`: Telegram configured, enabled, outbound-only, ready for dispatch
  on `pcae phase complete` when `PCAE_NOTIFY_ENABLED=1` — unchanged throughout this
  phase; no shadow test in this session triggered an actual outbound Telegram send
  (all shadow reproductions used isolated `tmp_path` shadow roots and directly called
  `observe_finalized_transition`, never the notification-dispatch path itself).
- `pcae phase-report reconcile --phase-id 135K` (read-only, run once during initial
  inspection): `conflict` — root cause independently traced and disclosed in §36; no
  mutation performed by this command or by this phase.

## 44. Runtime-boundary confirmation

Runtime state remained **Observed**, maximum plugin capability **observe**, execution
capability **unavailable** throughout this entire phase (confirmed at initial
inspection and unchanged by any action taken — no runtime, permission-broker, shell-
gate, or backend-adapter file was modified; only `docs/`, `tests/`, `PROJECT_STATUS.md`,
`CHANGELOG.md`, `tasks/`, and `.pcae/phase-completion-*` were touched by this phase).
No execution feature flag was introduced. **CONFIRMED.**

## 45. Findings table

| ID | Summary | Classification | Scope | Disposition |
|---|---|---|---|---|
| F-135L-1 | `InvariantContext`'s `live_repository_identity`/`live_branch_identity`/`live_repository_clean`/`live_head_revision` fields are declared but never populated (always default `InvariantContext()`) or read by any of the 37 evaluators — dead parameter threading, no evaluator branches on it | NON-BLOCKING | `src/pcae/cltr/invariants.py` | Documented, not repaired — no false pass/fail is caused; natural 135M cleanup/wiring candidate |
| F-135L-2 | The one real production call site never passes `adapter_sources`, so 11/15 representation adapters resolve `unverifiable` (never a false conformant) on every real production invocation today; separately, `transition_id == phase_id` means a same-phase content correction (e.g. partial→success reconciliation) is contained as `publish_failed` rather than published, silently discarding the corrected shadow observation (fails closed, no corruption) | NON-BLOCKING | `src/pcae/cltr/adapters.py`, `persistence.py`, `finalization_transaction.py` wiring | Documented, 2 new regression tests added, not repaired (wiring real sources / redesigning transition identity is 135M-scope planning work, not a 135L shadow-boundary repair) |
| F-135L-3 | 135K's promoted canonical report was re-promoted under the same `phase_id` by a later closure-documentation bookkeeping task, producing a `phase_name` display anomaly and a genuine `pcae phase-report reconcile` conflict (checkpoint/marker digest mismatch against the newest promoted generation) | NON-BLOCKING | PFR/task-lifecycle tooling (`phase_reports.py`) — **outside `src/pcae/cltr`** | Documented (§36), explicitly **not repaired** — repair would require touching production reports/checkpoints/markers, forbidden by this phase's boundary; flagged as separate governance follow-up |
| F-135L-4 | `repository_identity`/`branch_identity` in the one real production call site are set to `phase_id`/the literal `"main"` rather than actually-observed repository/branch values | NON-BLOCKING | `src/pcae/cltr` production wiring (`finalization_transaction.py`) | Documented (§7), not repaired — no downstream conformance decision currently depends on these two fields' real-world accuracy |
| (carried) F1 (135J) | Adapter comparison-mode completeness | — | 135I contract | **Resolved** prior to 135K (§38) |
| (carried) F2–F5 (135J) | Documentation-precision gaps in 135I's prose | NON-BLOCKING | 135I contract text | **Unchanged**, independently re-confirmed still accurate (§38) |

**Zero Blocking findings.**

## 46. Repairs made

See §41 — none required; two new tests document F-135L-2, and the isolation test
documents/regression-guards the subprocess/socket-freedom finding independently of the
existing 80.

## 47. Final verdict

# VERIFIED WITH NON-BLOCKING FINDINGS

No Blocking findings remain. Four genuine, independently-reproduced Non-Blocking
findings are disclosed (§45), none of which permits a false conformance claim, an
authority escape, production interference, or a widened exactly-once window. One
finding (F-135L-3) concerns PFR/task-lifecycle tooling outside the CLTR package
entirely and is explicitly out of this phase's repair boundary.

## 48. Readiness recommendation

Recommend **135M — Production CLTR Dual-Derivation and Atomic Publication Contract /
Migration Plan** as the next phase (planning/contract phase, not authority cutover),
per the assignment's Recommended Next Phase Logic. 135M should explicitly plan to
address, among its own required scope items: wiring real `AdapterSources` (F-135L-2)
from values production already computes at the shared finalization boundary; deciding
whether `transition_id` should become independently identity-bearing rather than
always equal to `phase_id` (F-135L-2); and disposing of `InvariantContext`'s currently
dead live-comparison fields (F-135L-1) — either wiring them or removing them.
F-135L-3 (PFR reconciliation conflict) is recommended as separate governance-hygiene
follow-up, not 135M scope, since it is not a CLTR-SCHEMA-001 concern.

## 49. No-go confirmations

No production lifecycle authority was changed. No certification, promotion, or
dispatch function was called by this phase's verification work. No production report
or completion metadata was replaced (the one production-report-touching command run,
`pcae phase-report reconcile --phase-id 135K`, is read-only and performed zero
mutation, independently confirmed by its own `"mutation_performed": false` output
field). No Architecture Status generation was changed. No marker or receipt was
fabricated. No real backend invocation occurred. No adapter execution occurred outside
isolated `tmp_path` shadow roots. No subprocess execution capability was introduced or
exercised (independently confirmed via monkeypatch, not only AST, §26/§34). No network
call was made (independently confirmed via monkeypatch). No shell interception was
introduced. No Telegram inbound capability was introduced or exercised; no outbound
Telegram send was triggered by any test in this phase. No enforcement was enabled. No
automatic apply was enabled. No apply execution occurred. No commit or push
authorization capability was introduced. No real AI backend call occurred. No raw
`git commit` was used. No raw `git push` was used. No force push was used. No PFN-001
change occurred. No PFR-001 change occurred. No CLTR-001 amendment occurred. No legacy
authority was retired. No historical artifact was rewritten. No immutable generation
was rewritten in place. No execution capability was introduced. No authority cutover
occurred. **Phase 135M was not started.**
