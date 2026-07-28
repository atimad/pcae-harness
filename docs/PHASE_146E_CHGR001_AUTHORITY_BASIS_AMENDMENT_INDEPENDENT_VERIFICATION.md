# Phase 146E — CHGR-001 Authority-Basis Amendment Independent Verification

## 0. Purpose and Boundary

Per explicit human authorization, this phase independently verifies
whether Phase 146D's CHGR-001 §28 amendment (v1.1 → v1.2; CHGR-REQ-207
through CHGR-REQ-209) correctly resolves the Blocking finding Phase 146C
independently identified (CHGR-REQ-199 vs. CHGR-REQ-204 vs.
`human_governance_record.schema.json`'s pre-146D `required` array). This
phase does not trust Phase 146D's own §28.6 self-verification narrative;
every claim below was independently re-derived from primary sources —
contract text, schema files, `manifest.json`, `record.py` — or produced
by live re-execution (digest recomputation, JSON Schema validation
against constructed fixtures, the existing CHGR test suite, `git diff` of
the actual 146D commit). No implementation work is authorized or
performed. Runtime baseline: Observed / observe / unavailable,
unchanged.

## 1. Bootstrap

```
git status --short          -> (clean)
git branch --show-current   -> main
git rev-list --count origin/main..HEAD -> 0
git rev-list --count HEAD..origin/main -> 0
pcae session bootstrap --agent-id claude-local -> Health: healthy, Check: passed,
    lock held by claude-local, latest completed phase 146D (report: complete)
pcae check     -> PCAE check passed
pcae health    -> Overall status: healthy, git status clean
pcae doctor task-memory -> Task memory: clean, no inconsistencies
pcae runtime inspect    -> not_implemented / Observed / unavailable / observe (unchanged)
pcae push check          -> nothing_to_push
```

Repository clean at bootstrap; `origin/main..HEAD` and `HEAD..origin/main`
both 0; runtime unchanged; no active governed phase held (idle placeholder
`20260728-1914-idle-awaiting-next-governed-phase-post-146d`, transitioned
to this phase's own task via `pcae task transition` before any
verification work began, mirroring 146C's and 146D's own bootstrap
discipline). `tasks/TODO.md` itself names `PROJECT_STATUS.md` as
authoritative over itself; no conflict was found between the two.

## 2. Independent Reconstruction

Read directly, not through 146A–146D's own summaries:

- **CHGR-001** (`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`):
  §11 Authority Contract (CHGR-REQ-096/097), §12 Assurance Contract, §26
  (v1.1 revision, CHGR-REQ-194–206), §28 (v1.2 revision, CHGR-REQ-207–209)
  in full.
- **PEC-001** (`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`) §20.2,
  PEC-REQ-111–117, in particular PEC-REQ-115 verbatim.
- **IWPC-001** (`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`)
  §29 Conflict and Findings Register, row C-1.
- **Schema family**: `human_governance_record.schema.json` (current, on
  disk) and its `git show 6794c0f5 --` diff against the pre-146D version;
  `envelope.schema.json`'s shared `chgr_envelope` definition (source of
  the `contract_version` const).
- **`manifest.json`** (current) and the actual `git diff` of its
  146D-touched entry.
- **`record.py`** (`src/pcae/governance/publication/record.py`), read in
  full, unmodified by 146D.

**Independently reconstructed authority semantics:** authority is
established only by the conjunction of valid human action and the
applicable governing authority model (CHGR-REQ-096); any gap between the
two SHALL be surfaced, never silently resolved in the record's favor
(CHGR-REQ-097). `authority_basis_claimed` is a *claim*, never a verified
grant — the schema's own Phase 143E description already said so before
146B or 146D existed. PEC-REQ-115 (Phase 144F, i.e. *after* the 143E
schema freeze) makes construction of this field a conditional **MAY**,
contingent on a Decision Template `eligible_authority` citation
resolving — never a MUST, never an invention. No such citation is
constructible anywhere in this repository today (IWPC-001 §31 C-1,
disclosed Non-Blocking).

**Independently reconstructed schema semantics:** the 143E schema's
`required` array is a flat, undifferentiated list — it does not, and
never did, distinguish "always populatable" fields from "conditionally
populatable, disclosed-if-absent" fields. `rationale`, `conditions`, and
`governing_references` already demonstrate the schema family's own
precedent for the latter category (simply optional).

**Independently reconstructed validation semantics:** CHGR-REQ-204/205
(Phase 146B) establish a fail-closed conformance gate — no CHGR is
created on any non-conformant construction. This gate did not exist
before 146B; it is what turned the latent tension between an
unconditionally-required field and a conditionally-constructible value
into an active, permanent contradiction.

These three reconstructions match 146D's own §28.1 account of the
governing architecture. No divergence was found between an independent
first-principles reading and 146D's own narrative at this stage.

## 3. Root-Cause Verification

Each of 146D's own five candidates was independently re-evaluated against
primary-source text (not against 146D's own reasoning about the text):

- **(A) CHGR-REQ-199 is incorrect.** Independently rejected. CHGR-REQ-199
  restates PEC-REQ-115 (verified verbatim above) and CHGR-REQ-096/097
  (verified verbatim above) unchanged. Reworking it to require
  fabrication where no citation resolves would directly contradict
  CHGR-REQ-097's "never silently resolved in the record's favor" text —
  confirmed by direct reading, not by trusting 146D's characterization.
- **(B) The frozen schema's `required` array is incorrect.**
  Independently accepted. Confirmed by `git log` that the schema file was
  last substantively frozen at Phase 143E (predates PEC-REQ-115, which is
  144F, and CHGR-REQ-199/204, which are 146B) and by direct inspection
  that `rationale`/`conditions`/`governing_references` already sit
  outside `required` on the same schema — an existing, load-bearing
  precedent for "not always populatable," independently confirmed rather
  than taken on 146D's word.
- **(C) Chapter sequencing is wrong; the authority model must be built
  first.** Independently rejected as out of proportion, not because 146D
  said so but because IWPC-001 §31 row C-1, read directly, explicitly
  scopes that model-building as a distinct, larger, currently
  undertaken-nowhere initiative — confirmed by direct table read, not
  paraphrase.
- **(D) A canonical non-fabricated sentinel value.** Independently
  rejected. A fixed placeholder string is itself indistinguishable, to a
  downstream consumer, from a real claim — this is a straightforward
  consequence of the field's own `type: string` shape and was verified
  by direct schema inspection: nothing in the schema marks a sentinel
  value as semantically different from a real one.
- **(E) No other candidate found.** One additional candidate not named
  by 146D was independently considered and is reported as a non-blocking
  finding in §8 below: a `type: ["string", "null"]` widening with
  `required` retained, using `null` in place of omission. Rejected on
  the same fabrication-adjacent-signal grounds as (D), and because it is
  strictly more complex than removing the field from `required` for no
  compatibility benefit `required`-array removal does not already
  provide (§28.8's non-invalidation guarantee already covers every
  document that used to carry a populated string).

**Independent conclusion: Candidate (B), confirmed** — not merely
accepted on trust. The `required` array is a sequencing artifact: it
predates the PEC-REQ-115 conditional-construction rule and the
CHGR-REQ-204 fail-closed gate that made the omission unconditionally
load-bearing.

## 4. Amendment Verification

- **CHGR-REQ-207–209 internal consistency:** independently confirmed.
  CHGR-REQ-207 states the mechanical schema change; CHGR-REQ-208 ties
  omission to a disclosure obligation via the same fail-closed gate
  CHGR-REQ-204/205 already establish (not yet implemented in code — see
  §5); CHGR-REQ-209 is a closed, checkable "no prior requirement changed"
  claim, independently spot-checked against CHGR-REQ-096/097/199/204/205
  (all unchanged text, confirmed by direct comparison against §11/§23
  quoted above).
- **Schema matches contract:** `git show 6794c0f5 -- .../human_governance_record.schema.json`
  shows exactly one `required`-array entry removed (`authority_basis_claimed`,
  no reordering of the remaining 17 entries) and one property description
  string appended — independently diffed, not asserted from 146D's report.
- **Manifest correctness:** independently recomputed
  `sha256(records/human_governance_record.schema.json)` on the file
  currently on disk:
  `1a59e2931c4e4b6c654f25823f0dc6d533e13bd015eb8bfe70e36bd878cdce58` —
  matches `manifest.json`'s entry exactly. `schema_version` reads
  `"1.1"` in both the manifest entry and the file's own envelope
  composition. No other manifest entry differs from the pre-146D
  manifest (confirmed via `git show`).
- **Schema versioning coherence:** `contract_version` is a single const
  defined once in `envelope.schema.json`'s `chgr_envelope` `$defs` block
  and composed into every `records/*.schema.json` file via `allOf`;
  independently confirmed by direct read of `envelope.schema.json` and
  by grepping every `records/*.schema.json` file — each repeats the
  identical `"const": "CHGR-001/1.0"`. Leaving this const unbumped is
  therefore not an oversight: attempting a per-file override would make
  the field unsatisfiable under `allOf` (two conflicting consts on one
  property cannot be jointly satisfied by any value) — independently
  confirmed by reasoning about `allOf` const composition, not merely by
  reading 146D's own §28.6.1 account of catching this during drafting.
  The const documents *schema-generation lineage* (143E), not *current
  contract text version*, and additive amendments correctly do not
  disturb it, per the same reasoning already applied at v1.0 → v1.1.
- **No hidden contradictions:** none found. `manifest.json`'s top-level
  `contract_version` field (`"CHGR-001/1.0"`) is the package-level analog
  of the same const and is consistently left unbumped for the same
  reason.

## 5. Blocking Finding Reproduction

Independently re-derived, by live JSON Schema validation (Draft 2020-12,
`jsonschema` + `referencing`, loading the actual on-disk schema files —
not a re-statement of 146D's §28.6.3/28.6.4 narrative) against four
constructed fixtures:

| Case | Construction | Result |
|---|---|---|
| 1 | Envelope + all currently-required fields, `authority_basis_claimed` omitted | **Valid** (0 errors) |
| 2 | Same as (1), `authority_basis_claimed` present with a non-empty string | **Valid** (0 errors) |
| 3 | Same as (1), `decision_subject` (a genuinely still-required field) also omitted | **Invalid** — `'decision_subject' is a required property` |
| 4 | Same as (1), `authority_basis_claimed` present but `""` (empty string) | **Invalid** — `'' should be non-empty` (minLength:1 still enforced when present) |

Cases 1–2 independently demonstrate the CHGR-REQ-199/CHGR-REQ-204
contradiction 146C identified **no longer reproduces**: a construction
that correctly omits `authority_basis_claimed` (per CHGR-REQ-199, because
no citation resolves) now validates. Case 3 independently confirms
CHGR-REQ-204's fail-closed gate still refuses genuinely incomplete
constructions — it was narrowed by exactly one field, not weakened
generally. Case 4 independently confirms the field remains fully typed
and validated (`string`, `minLength: 1`, `maxLength: 500`) whenever it
*is* present — CHGR-REQ-207 makes it optional, not unconstrained.

**CHGR-REQ-208's own enforcement mechanism** (the fail-closed gate
additionally checking that `limitations` names the omission) is,
independently confirmed by grep of
`src/pcae/governance/publication/*.py` and
`src/pcae/interactive_workflow/publication_handoff/*.py`, **not yet
implemented anywhere in code** — correctly so, since this phase and 146D
are both contract/schema-only and no CHGR-REQ-204/205 gate of any kind
exists in the codebase yet (`record.py` still builds a pre-conformance,
non-schema-shaped payload; the schema-conformant construction path itself
is unbuilt). CHGR-REQ-208 is a specification for a future implementation
phase (146F), not a claim that it already runs today. `record.py`'s
existing `_KNOWN_LIMITATIONS` tuple (unmodified since Phase 144F) already
carries a disclosure sentence for `authority_basis_claimed`'s absence,
confirming the *intent* CHGR-REQ-208 will operationalize was already
present in working (if non-schema-conformant) code before 146B's gate or
146D's amendment existed.

**Conclusion:** the original contradiction (CHGR-REQ-199 ∧ CHGR-REQ-204 ∧
pre-146D schema = unsatisfiable for every construction) is independently
confirmed resolved. CHGR-REQ-195 is unaffected by this amendment (it
governs sibling-artifact identity independence, not `authority_basis_claimed`'s
requiredness) and was independently reconfirmed unchanged by both the
contract diff and the schema diff.

## 6. Regression Analysis

Independently checked, each against direct evidence rather than 146D's
own §28.7 table:

- **Authority leakage / fabricated authority:** none possible. No
  construction path exists (confirmed: `record.py` grep, PEC-REQ-115 text)
  by which `authority_basis_claimed` could be populated except from an
  already-resolved template citation; making the field optional narrows
  what may appear, never widens it. Making omission schema-valid removes
  any structural incentive to invent a placeholder merely to pass
  CHGR-REQ-204 — confirmed by Case 1/4 above (omission validates; a
  fabricated non-empty string would also have validated before *and*
  after, so the amendment's actual anti-fabrication effect is removing
  pressure, not adding a new technical barrier — this is a precise
  characterization, not an overclaim).
- **Weakened fail-closed validation:** none. Case 3 above independently
  confirms every other required field is still enforced.
- **Lifecycle regression:** none. `lifecycle_state` and its governing
  CHGR-REQ-198 are untouched by the diff (confirmed by `git show`).
- **Schema ambiguity / identity ambiguity:** none. CHGR-REQ-195–197
  (independent sibling identity, digest algorithm) name no field this
  revision touches; confirmed by direct re-read of §26.2's text against
  the diff.
- **Provenance regression:** none. `governance_record_provenance`'s
  `available: false` disclosure pattern (CHGR-REQ-202) is untouched;
  confirmed no other schema file changed in the 146D diff.
- **Compatibility regression:** none found — see §7.

## 7. Compatibility Review

- **PEC-001:** unmodified by 146D (confirmed: `git show --stat` lists no
  `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` change). PEC-REQ-115's
  own conditional-MAY text (independently quoted in §2 above) is exactly
  what CHGR-REQ-207 makes schema-satisfiable — not narrowed or widened.
- **IWPC-001 / IWC-001:** unmodified by 146D. §31 C-1 remains named
  Non-Blocking, Observation, untouched — independently confirmed by
  direct read of the current C-1 row, unchanged from the text quoted in
  §2.
- **Typed Authority Model (TAMC-001/TAMPC-001):** structurally disjoint
  per CHGR-001 §19.1; no file under either contract's scope appears in
  the 146D diff.
- **CHGR schema family:** `human_confirmation_evidence.schema.json`,
  `governance_record_provenance.schema.json`,
  `governance_record_integrity.schema.json`, and every `shared/*.schema.json`
  file are byte-identical to pre-146D — independently confirmed via
  `git show --stat 6794c0f5`, which lists exactly two schema-family files
  touched (`records/human_governance_record.schema.json`,
  `manifest.json`).
- **Publication Coordinator / Interactive Workflow / Publication
  Ownership:** `src/pcae/governance/publication/**` and
  `src/pcae/interactive_workflow/**` are absent from the 146D diff
  (independently confirmed by the same `git show --stat`); `record.py`
  read in full (§2) and confirmed unmodified since Phase 144F.
- **Existing CHGR test suite:** `pytest tests/test_chgr_schema_family.py
  tests/test_chgr_authority_boundary.py tests/test_chgr_verification.py
  tests/test_chgr_packaging.py tests/test_chgr_inspection.py
  tests/test_chgr_phase_separation.py tests/test_chgr_143f_independent_verification.py`
  run live: **127 passed, 2 failed**. Both failures
  (`test_143e_wheel_contains_all_six_chgr_record_schemas`,
  `test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv`)
  independently root-caused to a pre-existing, environment-local
  limitation (`python -m build` — the PEP 517 build frontend — is not
  installed in this sandbox and no network access exists to fetch it),
  reproduced directly by running `python -m build --wheel` standalone
  and observing the identical `ModuleNotFoundError`; unrelated to any
  content this revision changed. No CHGR fixture in `tests/fixtures/chgr/`
  asserts `authority_basis_claimed`'s prior requiredness (all 18
  fixtures still carry a populated value, matching Case 2's confirmed
  backward-compatible validity); no stale test assertion was found.

## 8. Findings

- **Non-Blocking (informational).** §3's Candidate (E) — a
  `type: ["string", "null"]` widening with `required` retained — was not
  enumerated by 146D's own five-candidate list. Independently evaluated
  here and rejected on the merits (strictly more complex than array
  removal, no compatibility benefit array removal doesn't already
  provide, and a `null` value is exactly as fabrication-adjacent a signal
  as Candidate (D)'s sentinel string). Does not change the verdict;
  recorded because the phase's own authorization explicitly required not
  assuming Candidate B without independently checking the candidate
  space, not merely re-scoring 146D's five.
- **Non-Blocking (informational).** CHGR-REQ-208's fail-closed
  disclosure-check has no implementation anywhere in the codebase yet, as
  expected for a contract/schema-only phase; flagged here only so
  Phase 146F's own planning phase does not have to independently
  rediscover this gap before scoping the implementation.

No Blocking findings.

## 9. Overall Verdict

**VERIFIED.**

The Blocking finding Phase 146C independently identified (CHGR-REQ-199 ∧
CHGR-REQ-204 ∧ the pre-146D schema's `required` array = unsatisfiable for
every construction) is independently confirmed resolved by live JSON
Schema validation against the actual on-disk schema, not by trusting
146D's own report. The amendment (CHGR-REQ-207–209): correctly identifies
and repairs the root cause (a sequencing artifact in the frozen 143E
schema's flat `required` array, independently reconfirmed against all
five — now six, with this phase's own addition — candidate explanations);
preserves architectural intent (the field remains a claim, never a
verified grant, and remains fully typed/validated whenever present);
preserves authority neutrality (CHGR-REQ-096/097 unweakened; no new
fabrication path opened, and the one plausible fabrication-adjacent
alternative this phase separately considered was independently rejected);
and introduces no regressions across lifecycle, identity, provenance,
compatibility, or the existing CHGR test suite (127/127 content-relevant
tests pass; the 2 unrelated failures are a pre-existing sandbox/build-tool
limitation, independently root-caused and reproduced standalone).

## 10. Governance Validation (post-verification)

```
pcae check     -> PCAE check passed
pcae health    -> Overall status: healthy, git status clean
pcae doctor task-memory -> Task memory: clean, no inconsistencies
pcae runtime inspect    -> not_implemented / Observed / unavailable / observe (unchanged)
pcae push check          -> nothing_to_push
git status --short       -> (clean, prior to this phase's own doc/task-lifecycle commit)
```

Runtime unchanged; no policy changes; no strategic-lineage changes; no
production code, schema, or manifest file modified by this phase (this
document, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`, and
`.pcae/phase-completion-*` are the only files this phase's own task
contract permits).

## 11. No-Go Boundary Confirmation

This phase modified no contract, schema, or manifest file (CHGR-REQ-207–209
and the amended schema/manifest were already committed by Phase 146D,
prior to this phase's authorization); modified no production code;
implemented no CHGR construction; changed no runtime behavior; altered no
lifecycle sequencing or authority ownership; added no execution
capability. Independent-verification artifacts only.

## 12. Final Verdict

**VERIFIED.**

## 13. Recommended Next Phase

**146F — CHGR-001 Schema-Envelope Implementation Planning.** This is a
recommendation, not an authorization; it does not itself authorize any
implementation of CHGR-REQ-194–209's construction rules.
