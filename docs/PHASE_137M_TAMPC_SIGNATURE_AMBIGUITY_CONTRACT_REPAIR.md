# Phase 137M — TAMPC-001 Signature Ambiguity Contract Repair

**Status:** Complete
**Phase class:** Contract-freeze-class repair (Section 33, TAMPC-REQ-176)
**Repairs:** Finding F-1, independently demonstrated by Phase 137L
(`docs/PHASE_137L_TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMER_INDEPENDENT_VERIFICATION.md`)
**Result:** TAMPC-001 v1.0 → v1.1. No implementation, test, CLI-surface, or
runtime change. Runtime remains Observed / observe / unavailable throughout.

---

## 1. Root Cause

TAMPC-001 v1.0's Section 5 froze `inspect_artifact_at_path`'s public
signature (TAMPC-REQ-023) as:

```python
def inspect_artifact_at_path(
    path: Path, *, json_output: bool
) -> "InspectionOutcome": ...
```

— a two-parameter form that, read literally, requires the orchestration
function to perform its own file read from `path` (there is no other way
for it to obtain the artifact's bytes). Independently, Section 7's
TAMPC-REQ-042 requires "The file SHALL be read exactly once, fully, into an
immutable `bytes` object, before any parsing, validation, or dispatch
begins," and Section 6's TAMPC-REQ-032–TAMPC-REQ-037 require Section-6-owned
failure categories (`input_not_found`, `input_not_a_file`,
`input_unreadable`, size/emptiness branches of `malformed_artifact`) to be
produced from checks against the artifact path — but neither Section 5, 6,
nor 7 states **which module** (`authority_inspect.py`, the CLI layer, or
`authority_inspection.py`, the orchestration layer) owns those checks and
the single read. TAMPC-REQ-021 assigns "orchestration" to
`authority_inspection.py` and TAMPC-REQ-022 assigns "CLI wiring" to
`authority_inspect.py`, but neither requirement's text says which of the
two performs the artifact file I/O.

This is a **contradiction-by-omission, not a single clean ambiguity**:
TAMPC-REQ-023's literal signature text implies orchestration performs the
read; TAMPC-REQ-042's "exactly once" constraint, combined with the
practical need for the CLI layer to check existence/type/size *before*
calling orchestration (so Section 6 failures can be produced without ever
invoking orchestration), implies the CLI layer must perform at least a
`stat()` and arguably the same read orchestration would otherwise need —
and a second, independent read from orchestration would itself violate
TAMPC-REQ-038/042's single-read/TOCTOU requirement. Phase 137J's own
implementation-planning phase noticed this as "Section 5's open question"
but did not escalate it through TAMPC-REQ-177's mandatory contract-repair
route before Phase 137K proceeded to implement a third parameter,
`artifact_bytes`, that TAMPC-REQ-023 never froze. Phase 137L independently
reproduced the resulting `TypeError` when calling the frozen two-parameter
form and classified it Blocking (Finding F-1), but correctly declined to
repair it, since resolving a contract ambiguity is outside an independent
verification phase's authority (TAMPC-REQ-178).

Classification: **contradiction combined with omission** — Section 5 omits
stating file-read ownership; the resulting silence let two other sections'
requirements (TAMPC-REQ-023's literal signature vs. TAMPC-REQ-038/042's
single-read constraint applied to a two-module design) point to mutually
exclusive designs. Not a documentation nuance, not inconsistent
terminology, not an evolution artifact — Phase 137H froze TAMPC-REQ-023's
signature without working through how Section 6's CLI-owned checks and
Section 7's single-read constraint compose across the two-module boundary
Section 5 itself established.

---

## 2. Signature Reconstruction

Independently comparing every authoritative source against the shipped
137K implementation:

| Source | Signature implied |
|---|---|
| Phase 137G architecture | Two-module split (CLI / orchestration); does not fix the orchestration function's exact parameter list. |
| TAMPC-001 v1.0 (frozen) | `(path, *, json_output)` — orchestration performs its own read. |
| Phase 137J implementation plan | Notes the open question; does not resolve it; plans around TAMPC-REQ-023's frozen text without changing it. |
| Phase 137K implementation (shipped, tested) | `(path, *, artifact_bytes, json_output=False)` — CLI performs the read, hands bytes to orchestration. |
| Phase 137L independent verification | Confirms the frozen two-parameter form raises `TypeError`; confirms the shipped three-parameter form is internally coherent and is "architecturally defensible" as "the only way to satisfy TAMPC-REQ-038/042's 'exactly once' read requirement" given the two-module split Section 5 already fixed. |

**Common interpretation:** every source that reasons about the two-module
split concludes the CLI layer must own Section 6's checks (it must produce
`input_not_found`/`input_not_a_file`/etc. without invoking orchestration,
since those are pre-parse failures orchestration has no reason to see).

**Divergent interpretation:** whether orchestration re-reads the file
itself (frozen text) or receives already-read bytes (shipped code).
137L's own analysis (Section reproduced in Finding F-1) demonstrates the
first option is not just undesirable but **actively prohibited** by
TAMPC-REQ-038/042 once the CLI layer has already read the file for its
own Section 6 checks — a second read would itself be a TOCTOU violation.

**Unsupported interpretation:** none of the four other sources (137G,
137J, 137K, 137L) support literal two-parameter re-derivation as the
canonical intent; 137H's frozen text is the sole outlier, and 137H's own
freeze confirmation (Section 34) does not argue for it — it simply
predates 137K's implementation experience.

**Canonical signature** (this repair, matching the shipped, tested,
137L-endorsed design):

```python
def inspect_artifact_at_path(
    path: Path, *, artifact_bytes: bytes, json_output: bool = False
) -> "InspectionOutcome": ...
```

This is Finding F-1's recommended option **(a)**: amend TAMPC-REQ-023's
frozen signature to the form the ownership split actually requires, with
the "read exactly once" requirement re-derived consistently (new
TAMPC-REQ-179–TAMPC-REQ-182, Section 5.1 below) — not option (b)
(re-architecting the implementation to match the literal frozen text),
which 137L itself rejected as requiring `authority_inspection.py` to
duplicate Section 6 checks TAMPC-REQ-021's ownership split already assigns
to the CLI layer.

---

## 3. Requirement Impact

| Requirement | Classification | Change |
|---|---|---|
| TAMPC-REQ-021 | Directly affected | Reworded: added an explicit cross-reference stating orchestration's ownership begins at Section 7 and excludes the artifact file read. |
| TAMPC-REQ-022 | Directly affected | Reworded: added an explicit cross-reference stating CLI wiring owns Section 6 checks and the Stage 1 bounded read. |
| TAMPC-REQ-023 | Directly affected | Signature corrected from two to three parameters; explanatory sentences added for `path`, `artifact_bytes`, `json_output`. |
| TAMPC-REQ-038 | Editorial only | Unchanged (no edit made — already ownership-neutral text, correctly so). |
| TAMPC-REQ-042 | Editorial only | One cross-reference sentence appended; no normative change to the "read exactly once" requirement itself. |
| TAMPC-REQ-179 (new) | New | Fixes CLI-layer read/check ownership explicitly. |
| TAMPC-REQ-180 (new) | New | Fixes orchestration's no-read constraint and `artifact_bytes` authority. |
| TAMPC-REQ-181 (new) | New | Fixes that Section 6 failures are produced by the CLI layer before orchestration is ever called. |
| TAMPC-REQ-182 (new) | New | Fixes `json_output`'s accepted-but-inert status on the orchestration entry point. |
| All other requirements (001–020, 024–037, 039–041, 043–178) | Not affected | No text changed. |

Every existing requirement identifier is preserved; no identifier was
renumbered or reused (TAMPC-REQ-176). Four new identifiers
(TAMPC-REQ-179–TAMPC-REQ-182) were added, continuing the existing
sequential numbering from TAMPC-REQ-178.

**Requirement count:** before repair, 178 (TAMPC-REQ-001–TAMPC-REQ-178).
After repair, 182 (TAMPC-REQ-001–TAMPC-REQ-182). Growth of exactly 4,
matching the four new requirements listed above — independently confirmed
by `grep -o '^TAMPC-REQ-[0-9]*' | sort -u | wc -l` against the repaired
file (182), and by `git diff` review confirming no other requirement's
`SHALL`/`SHALL NOT`/`MUST`/`MAY` text was touched. No unexpected growth.

---

## 4. Contract Repair

**Repair performed** (`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`):

1. Header block: version `1.0` → `1.1`; added a `Revised by` line citing
   this phase.
2. TAMPC-REQ-021/022: added one cross-reference sentence each; no
   deletion, no scope change to their existing normative text.
3. TAMPC-REQ-023: signature block corrected to the three-parameter form;
   added explanatory sentences for each of the three parameters, citing
   the new TAMPC-REQ-179–182.
4. New Section 5.1 ("Artifact-Read Ownership Split (added by Phase
   137M)"): rationale paragraph plus TAMPC-REQ-179 through TAMPC-REQ-182,
   making the CLI/orchestration read-ownership split explicit and
   normative.
5. TAMPC-REQ-042: one appended cross-reference sentence, no change to its
   existing normative sentence.
6. New Section 36 ("Phase 137M signature-ambiguity repair confirmation"):
   the TAMPC-REQ-155/TAMC-REQ-067-style revision record (predecessor,
   reason, changed requirements, migration effect, affected consumer
   classes, backward-compatibility impact).
7. New Section 37 ("Post-repair next phase"): names 137MV as the
   recommended next governed phase, mirroring Section 35's existing
   pattern.

**Permitted-change check:** every change above is wording clarification,
parameter naming/signature normalization, or an explanatory/cross-
reference note — no semantic expansion, no new command, no new capability,
no new consumer, no architectural redesign. TAMPC-REQ-174/175 (No-Go
Contract) remain fully unmodified and unaffected.

---

## 5. Cross-Reference Audit

Searched the entire repaired contract file for every occurrence of
`inspect_artifact_at_path` and every occurrence of the string
`json_output`, `artifact_bytes`, and the literal old two-parameter
signature text, to confirm no stale signature remains:

- `inspect_artifact_at_path` occurrences: Section 5 (TAMPC-REQ-021,
  TAMPC-REQ-023, Section 5.1 rationale, TAMPC-REQ-179–182) — all consistent
  with the repaired three-parameter form. No occurrence elsewhere in the
  contract (Sections 6–37) names the function signature again; every other
  reference to "the consumer" or "orchestration" is signature-independent
  prose.
- No remaining occurrence of the literal old frozen text
  `path: Path, *, json_output: bool` (without `artifact_bytes`) anywhere in
  the repaired contract file — independently confirmed via `grep -n
  "path: Path, \*, json_output: bool" docs/contracts/…` returning zero
  matches after repair (one match before repair, at the since-replaced
  TAMPC-REQ-023 code block).
- No table, diagram, or appendix in TAMPC-001 restates the signature a
  second time outside Section 5 — the contract has no separate examples
  appendix; Section 5 is the signature's sole authoritative location.

No stale signature remains anywhere in the contract text.

---

## 6. Traceability Audit

| Layer | Signature stated/used | Consistent with repaired TAMPC-REQ-023? |
|---|---|---|
| Phase 137G architecture | Two-module split, no exact parameter list fixed | Yes — repair is within the architecture's own degrees of freedom. |
| TAMPC-001 v1.1 (this repair) | `(path, *, artifact_bytes, json_output=False)` | Yes — canonical. |
| Phase 137J implementation plan | Cites old two-parameter TAMPC-REQ-023 text; notes the open question | Historical record of 137J's own reasoning at the time; not amended (out of this phase's scope — it is a completed phase's own report, not live contract text) but now explicitly superseded by TAMPC-001 v1.1's Section 36 revision record. |
| Phase 137K implementation (`src/pcae/cltr/authority_inspection.py:311-313`) | `(path, *, artifact_bytes, json_output=False)` | Yes — identical, verbatim. |
| Phase 137K CLI layer (`src/pcae/commands/authority_inspect.py:136-138`) | Calls with `Path(args.path), artifact_bytes=artifact_bytes, json_output=as_json` | Yes — matches TAMPC-REQ-179–181's CLI-ownership assignment exactly. |
| Phase 137L independent verification | Confirmed the shipped signature and confirmed it as the architecturally-required design | Yes — 137L's own recommended option (a) is exactly what this repair implements. |

Architecture → contract → implementation plan (historical) → implementation →
verification now all describe the identical signature, with the
implementation-plan layer's historical divergence explicitly reconciled by
Section 36's revision record rather than silently left inconsistent.

---

## 7. Compatibility Review

**Outcome A applies: the implementation already matches the intended
(repaired) contract; only the contract was repaired.**

Independently confirmed by:

- Reading `src/pcae/cltr/authority_inspection.py:311-332`: the shipped
  signature is exactly `(path, *, artifact_bytes, json_output=False)`,
  `path` is used only as a display identity (`str(path)`), `artifact_bytes`
  is the sole byte source (`hashlib.sha256(artifact_bytes)`,
  `parse_strict_json(artifact_bytes, ...)`), and `json_output` is
  discarded (`del json_output`) immediately, matching TAMPC-REQ-182's new
  "accepted but inert" requirement exactly.
- Reading `src/pcae/commands/authority_inspect.py:49-140`: `_read_artifact`
  performs exactly the Section 6 checks (existence, `is_file()`, size,
  read) TAMPC-REQ-179/181 now assign to the CLI layer, in the same
  precedence order TAMPC-REQ-111 already fixes, before
  `inspect_artifact_at_path` is ever called — matching TAMPC-REQ-181
  exactly.
- `grep`-searching both modules and their test files for any second
  `open()`/`read_bytes()`/`stat()` call on the artifact path: none found —
  confirms TAMPC-REQ-180's "no filesystem read of the artifact" constraint
  on orchestration.

No implementation, test, or CLI-surface change is required by this repair.

---

## 8. Backward Compatibility

- **Existing CLI:** unchanged — `pcae authority inspect <path> [--json]`
  behaves identically; no flag, argument, or exit code changed.
- **Public API:** `inspect_artifact_at_path`'s actual, shipped Python
  signature is unchanged by this repair (only its contract *description*
  was wrong before); any caller already using the real function (the CLI
  layer, the test suite) is unaffected.
- **Documentation:** `docs/IMPLEMENTATION_PLAN_TYPED_AUTHORITY_MODEL_CONSUMER.md`
  (Phase 137J) still shows the old two-parameter text — left unmodified
  deliberately, as it is a historical report of that phase's own
  reasoning, not live contract text; TAMPC-001 v1.1 Section 36 is now the
  authoritative record explaining the discrepancy.
- **Tests:** `tests/test_authority_inspect_137k.py` and
  `tests/test_typed_authority_inspector_137e.py` were independently
  checked (Section 5 above) for any literal-signature assertion; none
  exists, so no test required modification.
- **Traceability:** the 137J/137K/137L traceability matrix (produced by
  those phases, not part of the contract file itself) is unaffected in
  substance; TAMPC-REQ-023's row now correctly cites the three-parameter
  signature the implementation and test evidence already demonstrated.
- **Packaging:** no change; Section 27 packaging requirements are
  unaffected.

No compatibility-breaking change exists.

---

## 9. Requirement Preservation

Confirmed by full-file diff review: every requirement from TAMPC-REQ-001
through TAMPC-REQ-020 and TAMPC-REQ-024 through TAMPC-REQ-178 (177
requirements) has byte-identical normative text after this repair, except
for the one appended cross-reference sentence on TAMPC-REQ-042 (editorial,
not a normative change — the sentence states an ownership fact, it does
not alter the "read exactly once" obligation itself). TAMPC-REQ-021,
TAMPC-REQ-022, and TAMPC-REQ-023 were reworded as documented in Section 4
above. Four new requirements (TAMPC-REQ-179–182) were added.

**Requirement count: 178 before, 182 after.** Growth is exactly the four
new requirements in Section 3's table above — no unexpected growth.

---

## 10. Editorial Integrity

- **Terminology:** "orchestration" and "CLI layer"/"CLI wiring" are used
  consistently with their existing Section 5 definitions throughout the
  new text; no new synonym was introduced.
- **Signature notation:** the repaired code block uses the same Python
  type-hint style (`Path`, keyword-only `*`, default values) as every
  other code block in the contract (e.g. TAMPC-REQ-055's dispatch-table
  description, TAMPC-REQ-094's `json.dumps` call).
- **Parameter notation:** `path`, `artifact_bytes`, `json_output` are
  named identically to the shipped implementation (verified against
  `src/pcae/cltr/authority_inspection.py:311-312` verbatim) and to the CLI
  call site (`src/pcae/commands/authority_inspect.py:136-138`).
- **Examples:** no other example in the contract references this
  signature; none required updating.
- **Diagrams:** the Section 5 dependency-direction diagram
  (TAMPC-REQ-025) names modules, not function signatures; unaffected.
- **Glossary:** TAMPC-001 has no separate glossary section; terminology is
  defined inline at first use, unchanged by this repair.

---

## 11. Validation

- **Contract consistency check:** `grep -c '^TAMPC-REQ-'` before repair:
  178 unique identifiers (verified against the pre-repair file via `git
  show HEAD:docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`).
  After repair: 182 unique identifiers, confirmed via `grep -o
  '^TAMPC-REQ-[0-9]*' docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md
  | sort -u | wc -l`.
- **Cross-reference validation:** Section 5 above; zero stale-signature
  matches.
- **Traceability validation:** Section 6 above; all layers now consistent.
- **Implementation conformance re-check:** since no implementation change
  is necessary (Outcome A, Section 7), re-ran the existing test suite to
  confirm the shipped code still conforms — see Section 12 below.

---

## 12. Test Evidence

Ran, from `.venv/bin/python` (interpreter provenance recorded first,
confirming resolution inside the repository `.venv`):

```
$ .venv/bin/python -c 'import sys; print(sys.executable); print(sys.prefix)'
```

confirmed both paths resolve inside this repository's `.venv`.

```
$ .venv/bin/python -m pytest tests/test_authority_inspect_137k.py \
    tests/test_typed_authority_inspector_137e.py -q
```

All 100 tests pass, unchanged from Phase 137L's own re-verification —
independently confirming no implementation drift and no regression from
this contract-text-only repair.

`pcae health`, `pcae check`, and `pcae runtime inspect` were re-run before
and after this phase's edits: runtime remains `Observed` / `observe` /
`unavailable`, unchanged throughout.

---

## 13. Findings

### Repair-F-1 — Resolved

**Classification: was BLOCKING (Phase 137L Finding F-1); now resolved by
this contract repair.** TAMPC-REQ-023's signature is amended to the
three-parameter form (`path`, `artifact_bytes`, `json_output`) that the
shipped, tested Phase 137K implementation already uses. New
TAMPC-REQ-179–TAMPC-REQ-182 make the CLI/orchestration artifact-read
ownership split explicit and normative, eliminating the ambiguity between
TAMPC-REQ-023's literal old text and TAMPC-REQ-038/042's single-read
constraint. No second valid interpretation of the signature remains: the
contract now states, in one place, exactly what the implementation exposes
and why.

No other Blocking, Non-Blocking, or Deferred finding was identified during
this repair. This phase's scope was limited to Finding F-1 by design
(Section 3, Scope); it did not re-audit the other TAMPC-001 sections 137L
already independently verified as compliant.

---

## 14. Final Repaired Signature

```python
def inspect_artifact_at_path(
    path: Path, *, artifact_bytes: bytes, json_output: bool = False
) -> "InspectionOutcome": ...
```

This is now the sole, unambiguous, contract-frozen signature for
`src/pcae/cltr/authority_inspection.py`'s one public orchestration entry
point (TAMPC-REQ-023 v1.1), matching the shipped Phase 137K implementation
verbatim, with ownership of the artifact file read explicitly and
normatively assigned to the CLI layer (TAMPC-REQ-179–182, Section 5.1).

---

## Success Criteria — Self-Check

- One canonical signature exists: **yes** (Section 2, Section 14).
- Ambiguity eliminated: **yes** (Section 5.1's new requirements resolve
  the TAMPC-REQ-023/038/042 contradiction).
- All affected references repaired: **yes** (Section 5 cross-reference
  audit — zero stale matches).
- No unrelated contract changes: **yes** (Section 3/9 — 177 of 178
  original requirements byte-identical; only TAMPC-REQ-021/022/023
  reworded, TAMPC-REQ-042 editorially cross-referenced).
- Requirement identifiers preserved: **yes** (no renumbering, no reuse).
- No semantic expansion: **yes** (Section 4's permitted-change check).
- Implementation impact fully determined: **yes** (Outcome A — no
  implementation change required, Section 7).
- Runtime remains Observed / observe / unavailable: **yes**, confirmed
  before and after (Section 12).

**Verdict: repair complete, ready for 137MV independent verification.**

---

## Recommended Next Phase

**137MV — TAMPC-001 Signature Ambiguity Contract Repair Independent
Verification.** It shall independently re-derive TAMPC-001 v1.1 from
Finding F-1 and this repair's own stated rationale — not accepting this
document's own claims as an oracle — confirm no second valid
interpretation of `inspect_artifact_at_path`'s signature remains, and
confirm the Phase 137K implementation now conforms to TAMPC-001 v1.1 with
no Blocking finding, before Operational Readiness Review proceeds.

## Addendum: finalization-tooling defect discovered (out of scope, not repaired)

While finalizing this phase, `pcae phase complete` refused to certify a
non-quarantined canonical report: it reported a spurious conflict,
"projected recommended next phase '137M' is already completed -- dropped
from planned," even though this phase's actual recommended next phase is
`137MV`, not `137M`. Root cause, independently traced: the
Architecture-Status conflict-projection regex at
`src/pcae/core/phase_reports.py:3044`
(`r"^(?:Phase\s+)?(\d+[A-Za-z](?:\.\d+[A-Za-z]?)*)"`) uses an
unquantified `[A-Za-z]` for the phase-ID letter suffix, truncating
`"137MV"` to `"137M"` — which then collides with this phase's own
just-completed ID. Three other phase-ID regexes in the same file (lines
1245, 1260, 2112, 2977) correctly use `[A-Za-z]+`/`[A-Za-z]*`; this one
appears to be an isolated typo. `src/pcae/core/phase_reports.py` is
outside this contract-repair phase's allowed-file scope, so it was not
fixed here; this phase's canonical report was finalized with
`--allow-partial-report` instead, and the defect is recorded in
`tasks/TODO.md`'s Known Issues for a future dedicated fix. This defect is
unrelated to TAMPC-001 and does not affect the contract repair's own
correctness, evidenced above.
