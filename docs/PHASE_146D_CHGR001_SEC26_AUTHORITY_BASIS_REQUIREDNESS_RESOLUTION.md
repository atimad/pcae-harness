# Phase 146D — CHGR-001 Sec.26 Authority-Basis Requiredness Resolution

## 0. Purpose and Boundary

Authorized, per explicit human instruction, on the strength of Phase
146C's independent, authoritative `NOT VERIFIED` verdict: determine the
architectural root cause of the Blocking contractual inconsistency 146C
found (CHGR-REQ-199 / CHGR-REQ-204 / `human_governance_record.schema.json`'s
`required` array cannot be jointly satisfied) and produce the minimum
necessary amendment. **This phase does not implement Publication
Coordinator changes, does not modify runtime behavior or lifecycle
sequencing, does not add execution capability, does not change authority
ownership, does not begin implementation planning, and does not certify
Chapter 146.** Predecessor: Phase 146C (Independent Verification, `NOT
VERIFIED`). Runtime baseline at both start and close of this phase:
`Observed` / `observe` / `unavailable` (unchanged — confirmed in §8).

The goal is architectural correctness, not implementation convenience:
this phase does not begin by assuming the schema is wrong, and does not
begin by assuming CHGR-REQ-199 is wrong. §2–§3 below reconstruct the
governing intent from primary sources before §4 selects an amendment.

---

## 1. Bootstrap

- `git status --short`: clean.
- `git branch --show-current`: `main`.
- `git log --oneline --decorate -20`: HEAD at `4dd68cb3` (Phase 146C
  close), `origin/main`/`origin/HEAD` at the same commit.
- `git rev-list --count origin/main..HEAD`: `0`.
- `git rev-list --count HEAD..origin/main`: `0`.
- `pcae session bootstrap --agent-id claude-local`: lock already held by
  `claude-local`; health healthy; check passed; latest completed phase
  146C (report: complete); recommended next phase 146D (explicitly
  flagged "a recommendation, not an authorization; this phase's own NOT
  VERIFIED verdict does not authorize 146D or any repair of the Blocking
  finding" — human authorization for this specific phase was supplied
  explicitly in the phase prompt, not inferred from the recommendation
  alone); readiness `blocked` solely because the active task at bootstrap
  time was still the post-146C idle placeholder — resolved by
  `pcae task transition --next "Phase 146D: ..."` before any repair file
  was edited.
- `pcae check` / `pcae health`: healthy, git clean, session continuity
  verified.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae runtime inspect`: `Runtime state: Observed`, `Execution
  capability: unavailable`, `Maximum plugin capability: observe`, eleven
  Runtime Principles frozen.
- `pcae push check`: working tree clean, 0 unpushed commits, `Mode:
  nothing_to_push`.

`PROJECT_STATUS.md` treated as authoritative throughout (unambiguous with
`tasks/TODO.md` for this phase's scope).

---

## 2. Independent Root-Cause Reconstruction

Read directly, not summarized secondhand, before selecting a repair:
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §11
(Authority Contract), §12 (Assurance Contract), §22 (Amendment Contract),
§23.11 (CHGR-REQ-090–097), §23.21 (CHGR-REQ-180–188), and §26 in full
(v1.1, the frozen text this phase amends); `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`
PEC-REQ-115; `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` §26 (the
Phase 144D/144E finding that first surfaced the missing-fields gap);
`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
§29 (Conflict and Findings Register, item C-1) and §31; the entire frozen
schema family (`src/pcae/schema_resources/chgr/records/*.schema.json`,
`shared/*.schema.json`, `manifest.json`, `manifest.schema.json`); the
current implementation (`src/pcae/governance/publication/record.py`,
including its own `_KNOWN_LIMITATIONS` disclosure text); and
`docs/PHASE_146C_CHGR001_SCHEMA_ENVELOPE_CONTRACT_INDEPENDENT_VERIFICATION.md`
§3–§6 (the Blocking finding and its own evidence trail, re-verified
directly against the cited primary sources rather than trusted as
secondhand summary).

**Why `authority_basis_claimed` exists.** CHGR-001 §11 (Authority
Contract) freezes: "authority derives solely from the valid human
governance act performed by the appropriate authority within scope,"
established "only by the conjunction of valid human action ... and the
applicable governing authority model — the eligible-authority rule the
record's own Decision Template names." `authority_basis_claimed` is the
field that carries this citation. CHGR-REQ-182 requires a verifier be
able to determine, from a CHGR alone, "under what authority the decision
was made." The field exists to make that determination possible.

**Why it is required (in the schema's original, Phase 143E, sense).**
`human_governance_record.schema.json`'s own top-of-file description
(unchanged since Phase 143E) is explicit that the field is a *claim*
("authority_basis_claimed is explicitly named 'claimed', never
'verified'"), never a verified grant. At Phase 143E, before any
Publication pipeline existed, the schema's `required` array was drafted
to name every substantive field CHGR-001 §9–§12 describes a complete
record carrying — `authority_basis_claimed` included, undifferentiated
from fields with no such caveat.

**Why PEC-REQ-115 (Phase 144F) prohibited unconditional population.**
PEC-REQ-115 states the Coordinator "**MAY** construct
`authority_basis_claimed` solely from that already-verbatim citation,
never from an independent judgment of whether the claim is actually
valid" — a conditional MAY, contingent on the Package's `template_ref`
resolving to the template's own `eligible_authority` text. No Decision
Template model carrying `eligible_authority` exists anywhere in this
repository (`interactive_workflow`'s `Session.template_ref` is an opaque
identifier only — independently confirmed by reading
`src/pcae/interactive_workflow/models/session.py` and
`src/pcae/governance/publication/record.py`'s own docstring). CHGR-REQ-097
("[a]ny gap between valid human action and eligibility ... SHALL be
surfaced, never silently resolved in the record's favor") is what makes
inventing a citation to fill the gap a prohibited, not merely
discouraged, act.

**Why fail-closed validation (CHGR-REQ-204, Phase 146B) exists.** CHGR-001
§18 (Security Contract) and `docs/ROADMAP.md`'s "Fail closed" principle
require that a non-conformant construction never silently proceed to a
write. CHGR-REQ-204 is a correct, independently-necessary requirement in
isolation — 146C's own Requirement Verification Matrix (§3) confirmed
this ("The fail-closed principle itself is sound ... the defect is not in
this requirement's own text but in what it necessarily does once
CHGR-REQ-199/the schema's `required` array are held fixed"). This phase
independently reconfirms that conclusion: CHGR-REQ-204 did not create the
underlying contradiction; it made a previously latent, inert
over-requirement in the Phase 143E schema load-bearing for the first
time.

---

## 3. Candidate Evaluation

Each candidate the authorizing prompt named was independently evaluated
against direct evidence, not assumed in advance:

**Candidate A — CHGR-REQ-199 is incorrect.** *Rejected.* CHGR-REQ-199
restates PEC-REQ-115 (frozen, Phase 144F) and CHGR-REQ-096/097 (frozen,
Phase 143B) unchanged, "one layer later." Reworking it to require
fabricating `authority_basis_claimed` where no citation resolves would
directly contradict CHGR-REQ-097's "never silently resolved in the
record's favor" rule and would narrow the Authority Contract (§11) — a
regression this phase's own No-Go Boundary and CHGR-001 §22's Amendment
Contract discipline both forbid without a far larger, separately
authorized undertaking.

**Candidate B — the frozen schema's requiredness is incorrect.**
*Accepted.* The `required` array was frozen at Phase 143E, before
PEC-REQ-115 (144F) or CHGR-REQ-199/204 (146B) existed to establish that
this specific field's construction is conditional. The contradiction is a
sequencing artifact: a later-established conditional-construction rule
was never reconciled against an earlier, undifferentiated schema
requirement. This is not a new design judgment invented by this phase —
it matches an already-existing convention on the very same schema, where
`rationale`, `conditions`, and `governing_references` (all substantively
similar "may not be populatable" fields) are already absent from
`required`.

**Candidate C — chapter sequencing is incorrect; the authority model must
exist first.** *Rejected as disproportionate.* Resolving IWPC-001 §31 C-1
first would dissolve the tension without any schema or contract change,
but requires designing and implementing a Decision Template
`eligible_authority` model — explicitly out of scope for CHGR-001 (§26.3(b))
and for IWPC-001 itself (§31 C-1, independently re-read: "Non-Blocking,
Observation ... not remedied by this contract; remains a named, disclosed
gap outside this contract's scope"). This is a categorically larger
undertaking than the "minimum necessary amendment" this phase is
authorized to produce.

**Candidate D — the architecture already defines a canonical
non-fabricated value satisfying both.** *Rejected as the direct repair,
informative as precedent.* No existing convention defines a sentinel
*string* for "claimed but deliberately absent" on this field; inventing
one now would itself risk exactly the fabrication CHGR-REQ-097 forbids,
since a populated string is not distinguishable, by a downstream
consumer, from an actual claim. The nearest real precedent —
`governance_record_provenance.schema.json`'s `repository_provenance:
{available: false, ...}` wrapper — models "structurally disclosed
absence" correctly, but retrofitting `authority_basis_claimed` from a
plain string into an object shape is a larger, non-additive type change
for no benefit `required`-array removal does not already provide. (This
candidate's evaluation is also what caught and reverted a drafting
mistake during this phase's own verification step — see §5's Amendment
Rationale and the amended contract's §28.6.1.)

**Candidate E — another independently derived explanation.** None found
beyond Candidate B.

**Determination: Candidate B.** The defect is in
`human_governance_record.schema.json`'s `required` array, which never
distinguished "always-populatable" fields from "conditionally-populatable,
disclosed-if-absent" fields.

---

## 4. Architectural Decision

Remove `authority_basis_claimed` from `human_governance_record.schema.json`'s
`required` array, making it optional (present only when a citation
resolves per PEC-REQ-115; correctly and permanently absent otherwise per
CHGR-REQ-199), and add a normative requirement tying disclosure
(`limitations` array entry naming the absence) to the same fail-closed
CHGR-REQ-204/205 enforcement mechanism, so an undisclosed omission is
refused exactly as a schema non-conformance would be — never merely a
documentation convention.

This decision:

- Preserves architectural intent: `authority_basis_claimed` remains
  exactly as usable, and exactly as schema-validated when present, as
  before — CHGR-REQ-207 makes it optional, it does not remove, retype, or
  cap it.
- Preserves authority boundaries: no path exists by which the field can
  be populated with anything other than a verbatim, already-resolved
  template citation (PEC-REQ-115, unchanged); making it optional narrows
  what can appear, it does not widen it.
- Preserves lifecycle invariants: CHGR-REQ-198 (`lifecycle_state`) is
  untouched.
- Preserves fail-closed validation: CHGR-REQ-204/205 remain in force,
  strengthened (not weakened) by the new disclosure-enforcement clause
  (CHGR-REQ-208).
- Preserves provenance and deterministic behavior: no field's
  construction algorithm, digest computation, or identity assignment rule
  changes.

---

## 5. Amendment Rationale

See `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §28.1–§28.2
for the full, independently-derived reasoning (reproduced in condensed
form in §2–§3 above). One additional disclosure belongs here: an initial
draft of the schema edit also bumped `human_governance_record.schema.json`'s
local `contract_version` const from `"CHGR-001/1.0"` to `"CHGR-001/1.2"`,
reasoning (by analogy to §26.3(c)'s own "the const identifies which
version of CHGR-001 the schema files themselves were generated against"
language) that a schema file which actually changed should say so. Loading
the amended schema and inspecting its `allOf` composition showed this is
wrong: `contract_version` is defined once, in `envelope.schema.json`'s
shared `chgr_envelope` `$defs` entry, and composed into every
`records/*.schema.json` file (this one included) via `allOf` — a
conflicting local const for the same property makes the schema
unsatisfiable by any value (no string can equal two different JSON Schema
`const`s simultaneously). This was caught during this phase's own
verification (§7 below), reverted before being included in the amendment,
and is recorded in the contract's own §28.6.1 and §28.5 so a future phase
does not repeat the same mistake. `contract_version` therefore remains
`"CHGR-001/1.0"`, exactly as §26.3(c) already established for the v1.1
revision, for the same underlying reason (the shared, family-wide const is
not a per-file override point) — not because this revision fails to
change the schema (it does), but because that specific const is
architecturally incapable of expressing a per-file revision marker.

---

## 6. Normative Amendment

Added to `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` as
new §28 ("Phase 146D contract revision — authority-basis requiredness
resolution," version 1.2) and new §29 ("Post-revision next phase"),
inserted after the existing §27:

- **CHGR-REQ-207.** `human_governance_record.schema.json`'s `required`
  array SHALL NOT include `authority_basis_claimed`; the field remains
  defined, typed, and schema-validated when present, becoming optional
  like `rationale`/`conditions`/`governing_references`.
- **CHGR-REQ-208.** The CHGR-REQ-204/205 fail-closed gate SHALL
  additionally verify that an absent `authority_basis_claimed` is named
  in the record's own `limitations` array, tying CHGR-REQ-199's existing
  disclosure sentence to the same enforcement mechanism.
- **CHGR-REQ-209.** No requirement in §1–§26 (CHGR-REQ-001–206) is
  narrowed, superseded, or reworded; CHGR-REQ-207–208 are additive.

Implementing files changed to match:

- `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`:
  `authority_basis_claimed` removed from the top-level `required` array
  (18 entries → 17); its property `description` extended with one
  sentence disclosing the Phase 146D optionality and disclosure
  obligation. No other property, `const`, `$ref`, or structural element
  changed.
- `src/pcae/schema_resources/chgr/manifest.json`: the
  `human_governance_record` entry's `schema_version` bumped `"1.0"` →
  `"1.1"` and `file_digest` recomputed to
  `1a59e2931c4e4b6c654f25823f0dc6d533e13bd015eb8bfe70e36bd878cdce58`
  (SHA-256 of the amended file's raw bytes, matching exactly the
  algorithm `src/pcae/schema_runtime/loader.py` uses). No other manifest
  entry changed.

---

## 7. Verification of the Amendment

Independently demonstrated live, not merely argued:

- **Manifest integrity.** `src/pcae/schema_runtime/manifest.py:load_and_verify_manifest`
  run directly against the amended schema file and updated manifest
  entry: **passed**, 12 entries confirmed both shape-valid (against
  `manifest.schema.json`) and digest-matched against the files actually
  on disk.
- **Schema satisfiability.** Amended `required` array independently
  diffed against the pre-146D array: exactly one entry removed
  (`authority_basis_claimed`), none added, none reordered; every other
  required field, `const`, and `$ref` resolution
  (`envelope.schema.json`, `identity.schema.json`, `digest.schema.json`,
  `enums.schema.json`, `references.schema.json`,
  `limitations.schema.json`) unchanged.
- **Contradiction resolved.** A construction that (a) omits
  `authority_basis_claimed` (satisfying CHGR-REQ-199) and (b) carries a
  `limitations` entry naming that omission (satisfying CHGR-REQ-199's
  disclosure sentence and CHGR-REQ-208) now validates against the amended
  schema's `required` array. CHGR-REQ-204's fail-closed gate no longer
  refuses every Publication attempt permanently.
- **Publication Coordinator / ownership.** `src/pcae/governance/publication/**`
  and `src/pcae/interactive_workflow/**` independently reconfirmed
  unmodified (Forbidden Files for this phase, per its own No-Go
  Boundary); no field ownership, lifecycle transition, or Coordinator
  responsibility changes.
- **CHGR architecture / future authority evolution.** When the IWPC-001
  §31 C-1 deferral is eventually resolved, `authority_basis_claimed`
  remains exactly as usable as before — still schema-validated when
  present, unchanged type/length bounds — CHGR-REQ-207 makes it optional,
  never retypes or caps it.
- **Test regression.** `python -m pytest tests/test_chgr_schema_family.py
  tests/test_chgr_packaging.py tests/test_chgr_authority_boundary.py
  tests/test_chgr_143f_independent_verification.py` and the broader
  `-k "chgr or publication or 146"` sweep: 896 passed, 1 skipped, 4 failed
  (all four pre-existing, environment-only `python -m build: No module
  named build` failures, independently confirmed identical on the
  unmodified `main` HEAD via `git stash` before/after comparison — none
  touch any file this phase changed, none regress).

---

## 8. Governance Validation

- `pcae check`: passed.
- `pcae health`: healthy, git status showing exactly the files this
  phase's own Allowed Files list names.
- `pcae doctor task-memory`: clean.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable` —
  unchanged from phase start.
- `pcae push check`: readiness confirmed before push (see task closure).
- `.pcae/policy.toml`: not touched.
- `.pcae/strategic-lineage.json`: not touched.

No production runtime code (`src/pcae/governance/publication/**`,
`src/pcae/interactive_workflow/**`) was modified. No authority ownership
was altered. No execution capability was added. No implementation of
CHGR-REQ-194–209's construction rules was begun.

---

## 9. No-Go Boundary Confirmation

Per this phase's own authorization: no Publication Coordinator changes
were implemented; no runtime behavior was modified; no lifecycle
sequencing was modified; no execution capability was added; no authority
ownership was changed; no implementation planning was begun; Chapter 146
is not certified by this phase. This phase's own diff is confined to:
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (new §28,
§29), `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`
(`required` array, one property description), `src/pcae/schema_resources/chgr/manifest.json`
(one entry's `schema_version`/`file_digest`), this report, and the
governed task/status/metadata files this phase's own workflow requires.

---

## 10. Regression Analysis

See `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §28.7
for the full analysis. Summary: no authority leakage (no new population
path exists); no fabricated authority (omission is now schema-valid,
removing pressure to invent a placeholder); no lifecycle regression
(CHGR-REQ-198 untouched); no schema ambiguity (§7's diff confirms exactly
one array entry changed); no identity ambiguity (CHGR-REQ-195–197
untouched); no compatibility regression (§28.5); no weakening of
validation (CHGR-REQ-204/205 strengthened by CHGR-REQ-208, not weakened).

---

## 11. Compatibility Analysis

See `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` §28.5.
Summary: compatible with PEC-001 v1.1 (PEC-REQ-115's own conditional text
is what CHGR-REQ-207 finally makes schema-satisfiable); compatible with
IWC-001 v1.2 / IWPC-001 v1.4 (the §31 C-1 deferral is neither resolved nor
expanded by this revision); compatible with TAMC-001/TAMPC-001
(structurally disjoint, untouched); the three sibling record schemas and
all `shared/*.schema.json` files are unmodified; `contract_version`
remains the shared-envelope-frozen const `"CHGR-001/1.0"` (§5 above
explains why a per-file override was drafted, found unsatisfiable, and
reverted).

---

## 12. Requirement Traceability

| New Req | Resolves | Traces to |
|---|---|---|
| CHGR-REQ-207 | 146C §4 Blocking finding (schema `required` vs. CHGR-REQ-199) | Phase 143E schema freeze (`human_governance_record.schema.json`), CHGR-REQ-199, PEC-REQ-115, the existing `rationale`/`conditions`/`governing_references` optional-field convention on the same schema |
| CHGR-REQ-208 | 146C §4's disclosure-enforcement gap (textual-only "never silently omitted" sentence) | CHGR-REQ-199's own disclosure sentence, CHGR-REQ-204/205's fail-closed gate |
| CHGR-REQ-209 | Amendment Contract (§22) additive-only discipline | CHGR-REQ-206's identical precedent from the v1.1 revision |

CHGR-REQ-194–198, 200–203, 205–206 (146C-confirmed correct, necessary,
complete, consistent, implementable) are unaffected and untouched by this
revision. CHGR-REQ-199 and CHGR-REQ-204's own text are unchanged — 146C's
Blocking finding was never in either requirement's own wording, only in
the unmodified schema's `required` array read against both; CHGR-REQ-207
corrects that.

---

## 13. Executive Summary

Phase 146D independently reconstructed the governing design for
`authority_basis_claimed` from primary sources — CHGR-001 §11/§12/§22, the
Phase 143E schema's own top-of-file description, PEC-REQ-115 (Phase
144F), CHGR-REQ-096/097 (Phase 143B), IWPC-001 §31 C-1's disclosed
deferral, and `record.py`'s own already-existing disclosure text — rather
than assuming the schema or CHGR-REQ-199 was wrong at the outset. Five
candidate root causes were independently evaluated; Candidate B (the
frozen schema's `required` array never distinguished always-populatable
fields from conditionally-populatable, disclosed-if-absent fields — a
sequencing artifact predating PEC-REQ-115 and CHGR-REQ-199/204 by one and
three phases respectively) was accepted, and the other four rejected with
direct evidence, not assumption. The minimum necessary amendment —
removing `authority_basis_claimed` from `human_governance_record.schema.json`'s
`required` array, adding CHGR-REQ-207–209 to CHGR-001 (now v1.2), and
tying the field's existing disclosure obligation to the CHGR-REQ-204/205
fail-closed gate via CHGR-REQ-208 — was independently verified, live, to
resolve 146C's Blocking finding without weakening fail-closed validation,
without fabricating authority, and without touching Publication
Coordinator, Interactive Workflow, runtime, or authority-ownership code.
One drafting error (an unsatisfiable `contract_version` override) was
independently caught and reverted during this phase's own verification
step before being included in the amendment — disclosed in §5 and in the
contract's own §28.6.1, not hidden.

**Final Verdict: AMENDMENT COMPLETE.**

---

## 14. Recommended Next Phase

Per this phase's own authorization, a recommendation only, not itself an
authorization:

**146E — CHGR-001 Authority-Basis Amendment Independent Verification.** A
future phase should independently re-derive CHGR-REQ-207–209 from this
contract's own amended text and the amended schema/manifest files, without
trusting this phase's own self-report, mirroring Phase 146C's role for the
v1.1 revision — before any implementation phase (widening
`build_publication_record`, adding the CHGR-REQ-204/205/208 gate, adding
the CHGR-REQ-203 rendering function) is authorized. This phase does not
authorize 146E, and does not authorize any implementation of the
CHGR-REQ-194–209 construction rules CHGR-001 as a whole now specifies.
