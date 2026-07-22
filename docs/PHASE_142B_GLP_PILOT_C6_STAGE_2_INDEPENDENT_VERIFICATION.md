# Phase 142B — GLP-PILOT-C6 Stage 2 Independent Verification

**Status:** Complete (independent verification phase only — no governance,
lifecycle, runtime, authority, or implementation changes)
**Mode:** Independent verification of GPC6-001 v1.0 against GLP-001 v1.0,
GAC-001 v1.0, PGP-001 v1.1, PPA-001 v1.0, AGOC-001 v1.0, and Phase 139F's
Architecture-stage design, treating GPC6-001 and Phase 142A as evidence of
intent only, never as authority
**Governing authority:** GLP-001, GAC-001, PGP-001, PPA-001, AGOC-001, and
Phase 139F (source of truth for this verification); GPC6-001 v1.0
(verification target); Phase 142A (context only, not trusted)
**Runtime:** Observed / observe / unavailable (unchanged by this phase)
**Verdict:** **VERIFIED AFTER REPAIR (citation-only repairs) WITH
NON-BLOCKING FINDINGS**
**Deliverable:** This report; citation-only repairs to
`docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md` (internal section
cross-references and one requirement-ID misattribution; no obligation,
invariant, boundary, or authority assignment changed)

## 0. Purpose and Boundary

This phase independently re-derives the Stage 2 (Contract Freeze) contract
that GPC6-001 v1.0 claims to freeze for `GLP-PILOT-C6`, starting from
`docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md` and the five
framework contracts' own text — not from GPC6-001's or Phase 142A's prose —
and then compares that independent derivation against GPC6-001 to find
missing obligations, contradictory provisions, responsibility conflicts,
authority/lifecycle/runtime/implementation leaks, ambiguous language,
unverifiable requirements, hidden assumptions, incompatible clauses,
citation defects, and compliance gaps. GPC6-001 is treated throughout as the
verification target, never as the source of truth. This is a verification
phase only: no pilot architecture is redesigned, no governance, lifecycle,
runtime, or authority behavior is modified, no implementation is performed,
and `GLP-PILOT-C6` is not advanced beyond Stage 2 (Contract Freeze).

## 1. Method

1. Independently re-read, in full, `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md`
   (477 lines) and the five framework contracts —
   `docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md` (753 lines),
   `docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md` (909 lines),
   `docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md` (981 lines),
   `docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md` (751 lines),
   `docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md` (809 lines)
   — extracting the exact requirement IDs, quoted stage definitions, and
   invariant/boundary text relevant to a pilot instance's own Stage 2
   Contract Freeze, before re-reading GPC6-001 in detail.
2. Re-read `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md` (857 lines, 85
   requirements, GPC6-001 v1.0) in full.
3. Compared every GPC6-001 requirement, section by section (§1 Purpose
   through §17 Security and Governance Considerations, plus §18-§22),
   against the independently-extracted source text, spot-checking every
   citation to a 139F subsection or a framework-contract requirement ID
   directly against that source's actual wording — not against GPC6-001's
   own paraphrase of it.
4. Independently confirmed three factual claims GPC6-001 makes about
   repository state rather than accepting them on narrative: (a)
   `pyproject.toml`'s `[project] version` field and `[build-system]`/
   `[tool.hatch.build.targets.wheel]` configuration (GPC6-REQ-007–008,
   GPC6-REQ-012); (b) that no phase between 139F and 142A modified or
   contested 139F's design, via `git log --oneline` on
   `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md` and a targeted
   read of Phase 139G's own treatment of 139F (GPC6-REQ-043); (c) that
   Phase 142A's own commit touched only its four declared deliverable files
   with no `src/pcae/**` or other `docs/contracts/**` file modified, via
   `git show --stat` on the 142A contract-freeze commit (GPC6-001 §19-§20).
5. Performed an adversarial pass explicitly looking for: missing pilot
   obligations, contradictory provisions, responsibility conflicts,
   authority/lifecycle/runtime/implementation leaks, ambiguous language,
   unverifiable requirements, hidden assumptions, incompatible clauses,
   internal cross-reference/citation defects, and compliance gaps.
6. Repaired only the defects confirmed to be citation-only errors (§3.2
   below) — internal section cross-references and one requirement-ID
   misattribution — no architectural, obligation, or boundary change,
   consistent with the citation-repair exception this framework's own
   contracts already establish for wording/citation-only fixes (GAC-REQ-061;
   applied in-phase at Phase 141C for an analogous defect class).
7. Confirmed, before writing this document, that `GLP-PILOT-C6` remains at
   Stage 1 of 4 complete / Stage 2 Contract Freeze recorded, and that the
   Advisory Governance Framework's certification scope (Phase 140B) is
   unchanged.

## 2. Independent Re-Derivation Summary

Full extraction detail is not reproduced in full here; this section
summarizes what was independently established directly from 139F and the
five framework contracts' own text, before GPC6-001's specific wording was
relied upon.

### 2.1 Domain Scope (§2–§7 basis)

139F §3.1–§3.3 independently confirmed to state: a single-source-of-truth
version field with a deferred versioning-scheme choice and a
human-authority-only release trigger (§3.1); a retained `hatchling` build
backend, a build step producing wheel+sdist, a manual-only publish step,
and a deferred publish-target sequencing choice (§3.2); a deferred digest
algorithm, a mandatory manual checksum-confirmation step, and an explicit,
categorical exclusion of CI enforcement and signing (§3.3). Each subsection
states its own non-goals and at least one considered-and-rejected
alternative, independently confirmed present at 139F §3.1–§3.3 as read.

### 2.2 Pilot-Instance Scope (§8–§17 basis)

AGOC-001 §2 (ten invariants), §3 (role table), §4 (invocation), §5
(evidence), §6 (improvement), §7 (operational boundary), §8 (compliance),
§9 (compatibility), §10 (security/governance) independently confirmed to be
the closest existing precedent for a pilot-instance-scoped restatement of
the same invariant/boundary/evidence/compliance shape, applied to a single
designated pilot (`GLP-PILOT-C6`) rather than framework-wide. GLP-001 §6.1
Stage 2's own entry/exit criteria text was independently extracted verbatim
for cross-check against GPC6-REQ-043–044 (§3.1 below).

### 2.3 GLP-001 §6.1 Stage 2 — exact text

Independently re-read from `docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`
lines 243–257:

- *Entry criteria*: "an architecture exists and has not been contested; the
  obligations to be frozen can be stated as falsifiable requirements."
- *Exit criteria*: "a contract with zero ambiguous requirements as
  independently confirmed by a contract-verification pass."
- *Required outputs*: "a numbered contract document."

GPC6-REQ-043 and GPC6-REQ-044 quote this text verbatim and correctly. This
is the standard this verification phase itself applies to reach the verdict
in §4 below.

## 3. Comparison Against GPC6-001 and Adversarial Review

### 3.1 Confirmed consistent

- **§2–§4 (Domain Contract)** — every GPC6-REQ-007 through GPC6-REQ-022
  obligation traces to a specific, independently re-checked 139F §3.1–§3.3
  primitive, non-goal, or alternative. No obligation exceeds 139E §4's
  approved scope (Docker, Homebrew, CI signing, and migration tooling
  remain excluded throughout, matching 139F §2's exclusion table).
  `pyproject.toml` independently confirmed (this phase) to declare
  `version = "0.2.0"`, `build-backend = "hatchling.build"`, and a
  `[tool.hatch.build.targets.wheel]` section carrying the Phase 106D
  rationale comment GPC6-REQ-012 cites — GPC6-REQ-007, GPC6-REQ-008, and
  GPC6-REQ-012's factual claims are accurate.
- **§8 Pilot Invariants** — all ten invariants (GPC6-REQ-029–038) have a
  direct, independently-verifiable counterpart in GLP-001, GAC-001,
  PGP-001, PPA-001, or AGOC-001's own text, correctly cited in every
  instance checked. No invariant is missing; none is broadened beyond its
  cited source.
- **§9 Pilot Responsibilities** — the role table (GPC6-REQ-040) introduces
  no role beyond GLP-001 §8 and AGOC-001 §3; every responsibility maps to
  an existing authority holder. No two roles share ownership of the same
  concern.
- **§10 Stage Progression Contract** — GPC6-REQ-043's entry-criteria finding
  is independently reproduced: `git log --oneline` on
  `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md` shows exactly
  one commit (the phase's own authoring commit); Phase 139G's own text
  (§1.7–§1.8) independently confirms 139F's Stage 1 was not contested,
  redesigned, or rolled back by any later phase. GPC6-REQ-044's exit
  criteria finding — that the freeze alone does not satisfy Stage 2 — is
  the correct, GLP-001-consistent reading; GPC6-REQ-045–048's permitted/
  prohibited-transition and dependency rules are internally consistent
  with GAC-REQ-043, GLP-REQ-003, and GAC-REQ-023 as cited.
- **§13 Operational Boundary Contract** — GPC6-REQ-058–063 restate, without
  narrowing or broadening, the boundary provisions already frozen by
  GLP-REQ-004/044/045 and AGOC-REQ-045–051, correctly scoped to
  `GLP-PILOT-C6` specifically.
- **§19–§20 (Validation, No-Go)** — independently re-confirmed this phase:
  `git show --stat` on Phase 142A's own contract-freeze commit
  (`4a3efebe`) shows exactly four files changed
  (`CHANGELOG.md`, `PROJECT_STATUS.md`,
  `docs/PHASE_142A_GLP_PILOT_C6_STAGE_2_CONTRACT_FREEZE.md`,
  `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md`); no `src/pcae/**` file
  and no other `docs/contracts/**` file was touched, matching §19–§20's own
  claims exactly.

### 3.2 Findings (repaired — citation-only defects)

**Finding 1 (repaired — systemic internal cross-reference defect).**
GPC6-001, as originally frozen, cited "(§11 below)" or "§11" in
approximately fourteen locations (GPC6-REQ-005 item 5, GPC6-REQ-006,
GPC6-REQ-016, the §9 role table's three "Independent Contract Verifier" /
"Independent Implementation Verifier" / "Human Authority" rows,
GPC6-REQ-044, GPC6-REQ-045, GPC6-REQ-048, GPC6-REQ-056, GPC6-REQ-075,
GPC6-REQ-076, GPC6-REQ-078, GPC6-REQ-081, and the §19/§20 Validation/No-Go
bullets) intending to point to the future Independent Contract Verification
phase's own scope or to the role that performs it. Independent re-read of
§11's actual heading and content
(`docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md` line 492, "## 11. Domain
and Instance Evidence Contract", GPC6-REQ-049–052) found that §11 defines
only evidence-category, evidence-quality, and evidence-retention rules — it
does not define, scope, or discuss the Independent Contract Verification
phase itself, which is instead substantively discussed in §10 ("Stage
Progression Contract", GPC6-REQ-043–048) and, for Stage 3/Stage 4
authorization and role-identity matters, in §9 ("Pilot Responsibilities",
the role table) and §16 ("Future Stage Contract", GPC6-REQ-075–079). A
reader following "(§11 below)" to find what Independent Contract
Verification itself requires would instead find only evidence-provenance
rules — a genuine, independently-confirmable cross-reference error, though
one that does not itself render any `SHALL`/`SHALL NOT` obligation
ambiguous, since every affected provision's own substantive text (e.g.
GPC6-REQ-044's "Completion requires a future, separate Independent
Contract Verification phase...") is clear independent of the wrong section
number. A separate, related defect in the same family: line 133's original
text cited "(§4.2 below)" for Stage 2's exit criteria — no subsection
numbered "4.2" exists anywhere in this single-level-numbered document
(§1–§22, confirmed via `grep -n "^## "` over the full file); the exit
criteria in question are GPC6-REQ-044, in §10.

**Repair made:** every "(§11 below)"/"(§11)"/"§11's" cross-reference that
referred to the Independent Contract Verification phase or act was
corrected to "§10" (its actual location); references to the Independent
Contract Verifier's/Independent Implementation Verifier's role identity
were corrected to "§9" (the role table's actual location); references to
Stage 3/Stage 4 human-authority-election and authorization mechanics were
corrected to "§16" (Future Stage Contract, its actual location); the
orphan "(§4.2 below)" citation was removed (the surrounding sentence
already correctly states the substance without needing a forward pointer,
since GPC6-REQ-044 in §10 states it directly). Three references that were
already correct (evidence-standard citations at what is now confirmed to be
legitimate §11 usage — GPC6-REQ-057's "its evidence package meets §11
above", GPC6-REQ-066's "standard in §11", and GPC6-REQ-076's "per §11
above's citation discipline") were left unchanged, since §11 does in fact
define the evidence/citation-quality rules those three provisions
correctly invoke. This is a citation-only repair: no obligation, invariant,
boundary, role assignment, or stage-progression rule changed in force or
meaning; every affected provision's normative text is identical before and
after the repair. Classified as the citation-repair exception (GAC-REQ-061's
pattern, applied in-phase at Phase 141C for an analogous single-citation
defect; this repair covers a larger but textually identical class of
defect within one document).

**Finding 2 (repaired — requirement-ID misattribution).** GPC6-REQ-009, as
originally frozen, cited "GPC6-REQ-046" as the basis for "consistent with
runtime remaining Observed / observe / unavailable." Independent re-read of
GPC6-REQ-046 (§10, "prohibited transitions" — skipping Independent Contract
Verification, treating the freeze as completion, reordering stages, or
treating advisory citation as advancement) found no relationship to runtime
neutrality; the correct requirement is GPC6-REQ-034 (§8, "runtime
neutrality" — "No provision of this contract changes runtime capability.
Runtime remains Observed / observe / unavailable throughout"). GPC6-REQ-046
is, separately, correctly cited elsewhere in the document (GPC6-REQ-080,
"Integrity is preserved by GPC6-REQ-046's prohibition on skipped or
reordered transitions" — accurate, left unchanged). **Repair made:**
GPC6-REQ-009's citation corrected from GPC6-REQ-046 to GPC6-REQ-034. This is
a citation-only repair: GPC6-REQ-009's own normative text (no automated,
unattended, or schedule-driven release trigger) is unchanged; only the
supporting cross-reference is corrected.

### 3.3 Adversarial checks that did not surface a finding

- **Authority leaks:** none found — every GPC6-001 role-table entry (§9)
  maps to an existing GLP-001 §8 / AGOC-001 §3 authority holder; no new
  authority is created (GPC6-REQ-032, GPC6-REQ-063 hold).
- **Lifecycle leaks:** none found — no new phase type, lifecycle stage, or
  compliance outcome is introduced anywhere in GPC6-001 (GPC6-REQ-033
  holds); §10's stage-progression rules restate, and do not reorder,
  GLP-001 §6.1's existing four-stage core as applied to `GLP-PILOT-C6`.
- **Runtime leaks:** none found — `pcae health` at this phase's start
  confirmed runtime remains Observed / observe / unavailable; no GPC6-001
  provision purports to change this, and no packaging, build, publish, or
  checksum command was executed by Phase 142A or by this phase.
- **Implementation leaks:** none found — no file under `src/pcae/**` is
  touched by GPC6-001 or by this phase; GPC6-REQ-035/GPC6-REQ-061 correctly
  restate, without transferring, the Implementer role's exclusive Stage 3
  ownership.
- **Contradictory provisions between GPC6-001 and 139F or the five
  framework contracts:** none found beyond the citation defects repaired in
  §3.2 — no GPC6-001 normative obligation contradicts 139F's Architecture-
  stage design or any framework-contract requirement's actual force.
- **Scope expansion beyond 139E §4:** none found — Docker, Homebrew, CI
  release signing, and migration tooling remain excluded throughout §2–§7
  and restated as excluded at §7 (Domain Boundary Contract).
- **Speculative/premature governance or architectural evolution:** GPC6-001
  performs none; §15–§16 correctly gate all future contract-text change and
  Stage 3 progression behind evidence and an explicit human-authority
  election, and this phase neither proposes nor performs any such change.
- **Compliance gaps:** GPC6-001 §14 correctly limits itself to existing
  phase-review mechanisms, introducing no new compliance-checking role,
  tool, or apparatus (GPC6-REQ-064–069 confirmed against
  GAC-REQ-006/GAC-REQ-054's identical prohibition, inherited via
  AGOC-REQ-050).
- **Role-separation conflicts (§17):** GPC6-REQ-081–082 correctly bar the
  Independent Contract Verifier from being this contract's own author, and
  the Independent Implementation Verifier from being Stage 3's own
  Implementer or the Independent Contract Verifier — consistent with
  GAC-REQ-035/AGOC-REQ-065's pattern extended to a single pilot instance.
  This verification phase itself satisfies that separation: it is not
  Phase 142A (this contract's own author).

## 4. Verification Verdict

**VERIFIED AFTER REPAIR (citation-only repairs) WITH NON-BLOCKING FINDINGS.**

Per GLP-001 §6.1 Stage 2's own exit criteria ("a contract with zero
ambiguous requirements as independently confirmed by a contract-verification
pass"): every normative `SHALL`/`SHALL NOT` obligation in GPC6-001 §2–§17
was independently re-derived and found traceable, non-contradictory, and
unambiguous in its own substantive text. The two defect classes found and
repaired in §3.2 (a systemic internal-cross-reference error and one
requirement-ID misattribution) were citation-quality defects only — neither
rendered any obligation's normative force ambiguous, and both are now
corrected. No Blocking defect was found. `GLP-PILOT-C6` Stage 2's own exit
criteria are, as of this phase, independently confirmed met: GPC6-001 §2–§17
contains zero ambiguous requirements as this independent
contract-verification pass finds them.

| Finding | Severity | Evidence | Rationale | Disposition |
|---|---|---|---|---|
| 1 — systemic §11/§10/§9/§16 cross-reference defect | Non-blocking (citation-only) | `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md`, ~14 locations, pre-repair; §11 heading vs. cited content mismatch confirmed via direct read | Cited section did not contain the content the citation claimed it did; obligation text itself remained unambiguous throughout | Repaired this phase |
| 2 — GPC6-REQ-009's GPC6-REQ-046 misattribution | Non-blocking (citation-only) | `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md`, GPC6-REQ-009, pre-repair; GPC6-REQ-046's actual text (prohibited transitions) confirmed via direct read | Cited requirement ID did not support the claim ("runtime neutrality") it was cited for; correct requirement (GPC6-REQ-034) independently identified | Repaired this phase |

## 5. Validation

- Independent re-derivation of the domain-scope basis (139F §3.1–§3.3) and
  the pilot-instance-scope basis (the five framework contracts' invariant,
  responsibility, evidence, boundary, and compliance provisions) was
  completed directly from those documents' own text (§2 above) before
  GPC6-001's specific wording was treated as authoritative for any finding.
- Every GPC6-001 citation to a 139F subsection or a framework-contract
  requirement ID that was spot-checked was found accurate, with the two
  citation-only defects recorded and repaired in §3.2; no other citation
  inaccuracy was found.
- Three independent factual checks (pyproject.toml state, 139F's
  uncontested/unmodified status, Phase 142A's own commit scope) were
  performed directly against the repository, not accepted from GPC6-001's
  own narrative; all three were confirmed accurate.
- No missing pilot invariant, responsibility, or domain obligation was
  found (§3.1, §3.3).
- No authority, lifecycle, runtime, or implementation expansion was found
  (§3.3).
- `GLP-PILOT-C6`'s pilot architecture (Phase 139F) was not redesigned,
  reopened, or re-litigated by this phase.
- No provision of GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001 was
  modified by this phase.
- `GLP-PILOT-C6` remains at Stage 2 (Contract Freeze) — this phase's
  VERIFIED-AFTER-REPAIR finding satisfies GLP-001 §6.1 Stage 2's own exit
  criteria; Stage 3 (Implementation) is not begun, authorized, or
  implied by this phase. No GAC-001 §9 Stage 6 decision was made or
  attempted.
- No execution capability was introduced; `pcae health` reconfirmed at this
  phase's start and remains Observed / observe / unavailable; no file
  under `src/pcae/**` was touched.
- `git status --short` at phase start showed only this phase's own task
  contract as a new file under `tasks/active/`; the only file modified by
  this phase's repairs is `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md`
  (20 lines changed, all citation-only — confirmed via `git diff --stat`).
- `pcae check` passed and `pcae health` reported the expected active-task
  state at phase start (confirmed before this document was written).

## 6. No-Go

Confirmed not done by this phase:

- No provision of GLP-001, GAC-001, PGP-001, PPA-001, or AGOC-001 was
  modified by this phase.
- `GLP-PILOT-C6`'s pilot architecture (Phase 139F) was not redesigned by
  this phase.
- No governance, lifecycle, runtime, or authority behavior was modified by
  this phase.
- No implementation was performed by this phase.
- No execution capability was introduced by this phase.
- `GLP-PILOT-C6` was not advanced beyond Stage 2 (Contract Freeze) by this
  phase — Stage 3 (Implementation) remains a distinct, separately-
  authorized future phase requiring both this phase's own determinate
  finding and an explicit human-authority election (GPC6-REQ-075).
- No GAC-001 §9 Stage 6 governance decision was made or attempted by this
  phase.
- No new compliance-checking role, tool, or apparatus was introduced by
  this phase.
- Production code (`src/pcae/**`) was not modified by this phase.
- No GPC6-001 invariant (§8), boundary (§13), or role authority (§9) was
  narrowed, broadened, or removed by this phase's citation-only repairs.

## 7. Compatibility

- **GLP-001/GAC-001/PGP-001/PPA-001/AGOC-001:** unchanged; this phase
  modified none of their text.
- **GPC6-001 v1.0:** two citation-only repairs applied (§3.2 Findings 1–2);
  every normative obligation, invariant, boundary, and role assignment is
  unchanged in force and meaning. GPC6-001 remains v1.0 — this is treated
  as the same graded, citation-repair-only exception GAC-REQ-061 already
  establishes for wording/citation-only fixes, not a contract-text revision
  requiring its own Architecture stage.
- **Phase 139F / Phase 142A:** not reopened; this phase's findings are
  recorded as evidence for this repair and as context for any future
  §15-qualifying improvement proposal, not as a retroactive judgment on
  139F's or 142A's own compliance.
- **Phase 140B:** this phase does not reopen, narrow, or broaden 140B's
  certification scope (the governance-lifecycle dimension only).
- **Repository governance:** this phase modified only files within its own
  task contract's allowed zones (`docs`, `tasks`, `config`).

## 8. Deliverables

- **This verification report** —
  `docs/PHASE_142B_GLP_PILOT_C6_STAGE_2_INDEPENDENT_VERIFICATION.md`.
- **Citation-only repairs** to
  `docs/contracts/GLP_PILOT_C6_STAGE2_CONTRACT.md` (§3.2 Findings 1–2).

## 9. Recommended Next Phase

**142C — GLP-PILOT-C6 Stage 3 Pilot Preparation.**

Purpose: with GPC6-001's Stage 2 (Contract Freeze) now independently
verified and GLP-001 §6.1 Stage 2's own exit criteria met (§4 above),
prepare — but do not begin — `GLP-PILOT-C6` Stage 3 (Implementation).
Per GPC6-REQ-075, Stage 3 MAY begin only after (a) this phase's own
determinate "zero ambiguous requirements" finding, now satisfied, and (b)
an explicit, separate human-authority election to proceed, not implied by
(a). 142C should therefore confine itself to naming the specific human-
authority election required, restating the §9 role assignments (Release/
Versioning Policy Owner, Packaging Owner, Checksum-Verification Owner) that
would own Stage 3's work, and confirming no scope expansion beyond
GPC6-001 §2–§4's frozen obligations — without itself performing any
packaging, build, publish, or checksum command, and without itself
constituting the human-authority election GPC6-REQ-075(b) requires.
