# Pilot Governance Protocol Contract

## Contract identity and status

**Contract:** PGP-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 138B — Advisory Governance Pilot Contract Freeze
**Architecture basis:** Phase 138A — Advisory Governance Pilot Architecture
(GLP-001 Validation)
(`docs/PHASE_138A_ADVISORY_GOVERNANCE_PILOT_ARCHITECTURE.md`)
**Governed subject:** a future GLP-001 advisory pilot, as authorized by
GAC-001 §6

PGP-001 v1.0 is the sole normative authority governing **how a future
GLP-001 advisory pilot is observed, evidenced, reported, assessed, and fed
into a governance decision**: pilot eligibility (operationalized from
GAC-001 §6), observation discipline, evidence collection, success and
failure criteria, bias mitigation, assessment-package assembly, and the
governance-decision inputs those packages supply. It does not govern
GLP-001's own subject matter (lifecycle sequencing of a GLP-designated
initiative, GLP-001's exclusive domain) and it does not govern GAC-001's own
subject matter (the adoption stage progression, eligibility gate,
governance-decision outcome set, or rollback authority, all of which remain
GAC-001's exclusive domain, §2).

Phase 138A's architecture is the approved design basis for this contract.
This contract derives every requirement below from that architecture's
content; it does not perform new evidence-gathering and it does not invent
an obligation Phase 138A's architecture does not support. Where this
contract and the Phase 138A architecture document differ in force, this
contract is normative for compliance-evaluation purposes, and any such
difference is itself a defect to be resolved by a governed contract
revision, not by silently preferring one document over the other in
practice.

This is contract text only. It authorizes no pilot, executes no pilot,
designates no pilot initiative, and modifies no provision of GLP-001 or
GAC-001. Runtime remains Observed / observe / unavailable throughout every
operation governed by this contract.

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative, with the meanings given in
GLP-001 §0 and adopted unchanged by GAC-001 §0; this contract adopts the
same meanings unchanged.

A **PGP-governed pilot** is any pilot initiative designated under GAC-001
§6 (GAC-REQ-017–025). This contract's obligations attach only to a
PGP-governed pilot's observation, evidence, reporting, assessment, and
governance-decision-input activity; it imposes no obligation on ordinary
phase or task work that is not part of a designated pilot.

## 1. Purpose

PGP-REQ-001: This contract exists to convert Phase 138A's evidence-derived
evaluation architecture — an Observation Architecture, an Evidence
Collection Architecture, a Success & Failure Framework, an Assessment
Preparation procedure, a Governance Decision connective layer, a Comparison
Architecture, and a Bias Mitigation Architecture (138A §4–§11) — into a
binding, falsifiable set of obligations that a future GAC-001-designated
pilot SHALL satisfy when it is observed, evidenced, reported, and assessed.

PGP-REQ-002: This contract governs the **evaluation machinery** for a
future GLP-001 advisory pilot: how a pilot's raw activity becomes tagged
observations, categorized evidence, a measured success/failure outcome, an
assembled assessment package, and a set of governance-decision inputs. It
does not govern pilot eligibility determination itself beyond
operationalizing GAC-001 §6's existing test into a checklist (§4 below); it
does not govern the pilot's own domain subsystem work, which remains
governed by whatever contract that pilot's own Contract Freeze stage
produces (GAC-REQ-056).

PGP-REQ-003: This contract does not itself designate any pilot candidate,
authorize any pilot to begin, or execute any pilot activity. Designation
remains GAC-001 §6's exclusive authority (GAC-REQ-017, GAC-REQ-023);
execution oversight remains GAC-001 §7's exclusive authority
(GAC-REQ-026–033). This contract governs only how that already-authorized
activity is observed and turned into decision-ready evidence.

PGP-REQ-004: Conformance with PGP-001 grants no execution, lifecycle,
governance, or runtime capability. It governs how one specific pilot's
evaluation evidence is produced and organized.

## 2. Scope and Non-Goals

PGP-REQ-005: This contract applies to every future PGP-governed pilot's
observation activity, evidence collection, success/failure measurement,
bias-mitigation discipline, assessment-package assembly, and the inputs it
supplies to a GAC-001 §9 governance decision.

PGP-REQ-006: This contract does not apply to, and imposes no obligation on,
any PCAE phase or task that is not part of a GAC-001-designated pilot.
Ordinary engineering work is governed exclusively by its own existing
contracts and lifecycle governance, unaffected by this contract's
existence (§14).

PGP-REQ-007: This contract SHALL NOT be read as, and does not:

- execute a pilot;
- authorize a pilot;
- designate a pilot initiative;
- modify GLP-001 v1.0's text (any correction remains available only
  through GLP-001's own §13 extensibility mechanism, independent of this
  contract);
- modify GAC-001 v1.0's text (any correction remains available only
  through GAC-001's own §18 extensibility mechanism, independent of this
  contract);
- implement, automate, or enforce observation, evidence collection, or
  assessment in tooling — every obligation below is discharged by a
  human participant or assessor using existing PCAE artifacts (phase
  reports, contracts, commits), never by a new compliance-checking
  apparatus (mirrors GAC-REQ-006, GAC-REQ-054);
- change runtime, lifecycle, or governance capability (Runtime remains
  Observed / observe / unavailable throughout);
- add a sixth Stage 6 governance-decision outcome to GAC-001 §9's five
  frozen outcomes, or reweight them (138A §8; GAC-REQ-042);
- retrospectively reclassify, invalidate, or re-score any completed
  initiative, including any initiative Phase 137V, 137W, 137X, 137Y,
  137Z, 137ZA, or 138A studied or produced (§14).

## 3. Terminology

PGP-REQ-008: The following terms are normative and SHALL be used with
exactly the meaning given here by every document or phase that invokes this
contract, in addition to the terms GLP-001 §4 and GAC-001 §3 already
define, which this contract adopts unchanged:

- **Objective evidence** — a claim directly checkable against a specific
  artifact, phase report, commit, or file (138A §4.2 kind 1).
- **Subjective experience** — a participant's or observer's own
  first-person account, explicitly attributed and dated (138A §4.2 kind
  2).
- **Hypothesis** — an observer's own interpretive claim not directly
  attributable to an artifact or a named participant's statement (138A
  §4.2 kind 3).
- **Evidence category** — one of the four categories in §8.2 below
  (Architectural, Governance, Operational, Qualitative), each drawn from
  138A §5.
- **Comparison baseline** — one of the four reference points in §8.4 below
  against which a pilot's evidence is measured (138A §9).
- **Assessment package** — the six-part compiled evidence bundle defined
  in §12 below, the direct input to GAC-001 §8's independent assessment.
- **Pilot participant** — any Architecture author, Contract author,
  Implementer, Independent verifier, Hardening owner, or Certification
  authority acting within a PGP-governed pilot's own designated lifecycle
  (GLP-001 §8, GAC-REQ-027).
- **Assessor** — the Stage 5 independent-assessment party, distinct from
  every pilot participant (GAC-REQ-035).

## 4. Pilot Eligibility Contract

PGP-REQ-009: This section operationalizes GAC-001 §6's already-frozen
eligibility test (GAC-REQ-017–025) into a usable pre-designation checklist.
It adds no eligibility criterion beyond what GAC-001 §6 already freezes and
narrows none of them; it restates 138A §1 as binding contract text (138A
§1.1, §1.2).

### 4.1 Suitability checklist

PGP-REQ-010: Before a human authority designates a PGP-governed pilot
candidate, the candidate SHALL be checked against each of the following, in
order, with the check itself recorded in the candidate's own
Architecture-stage document (GAC-REQ-030):

1. **Applicability** — the candidate independently meets at least one of
   GLP-001 §5.1's four criteria (new binding technical contract;
   cross-cutting/global blast radius; track-closing; accumulating
   sibling-drift risk), evaluated on the candidate's own merits before
   GLP-001 is mentioned at all (GAC-REQ-022).
2. **Representative complexity** — the candidate is neither the smallest
   initiative that would technically qualify nor the single largest
   available initiative (GAC-REQ-018 item 2).
3. **Not already mid-flight** — the candidate's own Architecture stage has
   not yet begun under an informal, un-designated pattern (GAC-REQ-018
   item 3).
4. **Willing sponsor** — a human authority exists who will explicitly
   designate the candidate (GAC-REQ-023) and accepts the pilot's ceremony
   cost as a disclosed, deliberate tradeoff (GAC-REQ-020 item 3).

PGP-REQ-011: A candidate that fails any one of the four §4.1 checks is not
eligible for designation at that time. This contract does not rank
candidates that pass all four against one another; the final choice among
eligible candidates remains GAC-001's own reserved discretion (GAC-REQ-023).

### 4.2 Excluded candidate classes

PGP-REQ-012: The following candidate classes SHALL NOT be designated a
PGP-governed pilot, restating GLP-001 §5.2 (GLP-REQ-011) and GAC-REQ-019
with the concrete examples 138A §1.2 records:

| Excluded class | Example | Why excluded |
|---|---|---|
| Emergency repairs | An incident fix restoring a broken governance gate | Presumes time to complete Architecture before code exists; no repair phase in the 137V corpus used a full Architecture stage |
| Production hotfixes | A one-line correction to a misbehaving CLI flag | Localized bug fix — GLP-REQ-011 |
| Documentation corrections | Fixing a stale citation in an existing contract | Documentation-only work — GLP-REQ-011, GAC-REQ-019; also GAC-001 §13's own citation-repair exception (GAC-REQ-061) |
| Repository maintenance | Dependency version bumps, dead-code removal with no behavior change | Routine maintenance — GLP-REQ-011 |
| Unrelated runtime work | Any initiative touching runtime execution capability | Out of scope for GLP-001 entirely; PCAE runtime remains Observed / observe / unavailable (GAC-REQ-081) |

PGP-REQ-013: The exclusion pass (§4.2) and the suitability checklist (§4.1)
SHALL both be applied, and recorded, **before** candidate selection, never
as after-the-fact justification of an already-favored candidate
(GAC-REQ-022). This ordering is the primary structural defense against
pilot bias (§11 below).

PGP-REQ-014: This contract does not designate an actual pilot candidate. No
initiative is named, evaluated, or pre-selected by this contract.

## 5. Pilot Scope Contract

PGP-REQ-015: This section freezes the scope boundaries a PGP-governed
pilot's designation SHALL respect, restating 138A §2 as binding contract
text. It adds no boundary beyond what GAC-001 §6.6 and §7 already imply
(GAC-REQ-024–025, GAC-REQ-030) and narrows none of them.

### 5.1 Entry conditions

PGP-REQ-016: A pilot begins at the moment its Architecture-stage document
states, in its Governing Authority or Objective section, the §4.1 rationale
and the specific GLP-001 §5.1 criterion (or criteria) it meets
(GAC-REQ-030). Before that statement exists, no activity SHALL be treated
as pilot activity, however GLP-001-adjacent it may appear.

### 5.2 Exit conditions

PGP-REQ-017: A pilot's designated lifecycle (the mandatory four-stage core,
plus any conditional stage whose entry criteria the pilot independently
meets, per GLP-001 §6) reaching a recorded GLP-001 §11 compliance outcome,
followed by the completion of GAC-001 §8's independent assessment, is the
pilot's exit condition (GAC-REQ-024). Completion does not require a
"Compliant" outcome (§9–§10 below; 138A §2).

### 5.3 Duration boundary

PGP-REQ-018: No fixed calendar duration is imposed (GAC-REQ-024). A pilot's
phase count SHOULD be visible and estimable from its own Architecture
stage, so that the ceremony-to-blast-radius evaluation (GAC-REQ-036 item 3;
§9 below) has a stated baseline to measure actual cost against, not only a
post-hoc count.

### 5.4 Artifact boundary

PGP-REQ-019: Every artifact a pilot produces (source, tests, contracts,
phase reports) is an ordinary PCAE artifact governed by its own existing
rules (GAC-REQ-056). This contract does not carve out a separate pilot-only
artifact namespace; a pilot's artifacts are distinguished from any other
phase's artifacts only by the designation statement (§5.1) that marks them
as pilot evidence.

### 5.5 Governance boundary

PGP-REQ-020: A pilot's own subsystem work SHALL be governed by whatever
domain contract its own Contract Freeze stage produces (GAC-REQ-056);
GLP-001, GAC-001, and this contract govern only the pilot's lifecycle
sequencing and evaluation, never its subsystem's technical content.

### 5.6 Reporting boundary

PGP-REQ-021: Every phase inside a pilot SHALL produce its own ordinary
PFR-001-conformant report (GAC-REQ-030). This contract adds no new report
type; §12 below defines how evidence is drawn from those reports, not a new
report they must additionally produce.

### 5.7 Maximum expansion limit

PGP-REQ-022: A pilot's scope SHALL remain fixed as stated at entry (§5.1)
unless explicitly re-authorized. If a pilot's actual scope grows past what
its Architecture-stage designation stated, that growth is itself a
rollback trigger under GAC-REQ-045 item 1 — the correct response is
renewed designation review, not silent scope creep absorbed into the
existing designation.

## 6. Advisory Application Contract

PGP-REQ-023: This section freezes how GLP-001 SHALL be applied within a
PGP-governed pilot, restating GAC-001 §5 (Advisory Stage Contract) and §7
(Pilot Execution Contract) as the operative model, per 138A §3. It adds no
new obligation beyond what GAC-001 already freezes.

PGP-REQ-024: **Required.**

1. **Advisory recommendations only** — within the pilot, each stage's own
   participant applies GLP-001's stage-specific exit criteria (GLP-001
   §6.1) as guidance for how to run their own stage, exactly as any other
   contract's exit criteria guide a phase, with no additional compliance
   apparatus (GAC-REQ-054).
2. **Optional adoption** — nothing in this contract, GAC-001, or GLP-001
   requires any other concurrent or future PCAE initiative to apply
   GLP-001. Pilot designation binds only the designated initiative
   (GAC-REQ-021).
3. **Explicit documentation** — the designation-rationale statement (§5.1)
   plus each stage's own ordinary PFR-001 report is the complete
   documentation surface; no pilot-specific template is introduced
   (GAC-REQ-030, GAC-REQ-052).
4. **Observation logging** — every pilot stage SHALL be observed per §7
   below; observation is not optional for a designated pilot.

PGP-REQ-025: **Prohibited.**

1. **Mandatory compliance** — GLP-001's stage-specific exit criteria are
   never binding on the pilot's own future phases or on any other
   initiative by virtue of the pilot running (GAC-REQ-006, GAC-REQ-013).
2. **Enforcement** — no compliance-checking apparatus, tool, or dedicated
   review role beyond ordinary phase-review mechanisms is introduced by a
   pilot's own execution (GAC-REQ-055, GAC-REQ-054).
3. **Authority transfer** — a pilot's own participants hold exactly the
   responsibilities GLP-001 §8 already assigns to each role; this contract
   assigns no additional role and narrows no existing one (GAC-REQ-027).
4. **Governance reinterpretation** — no pilot stage, observation, or
   assessment activity reinterprets, extends, or narrows GLP-001's or
   GAC-001's own frozen text (§2 above).

## 7. Observation Contract

PGP-REQ-026: This section freezes the observation discipline 138A §4
introduces as new architectural content — GAC-REQ-028 requires only that
observation confirm stage ordering and exit-criteria evaluation occurred;
this contract specifies *how*.

### 7.1 Observation categories

PGP-REQ-027: Every pilot observation SHALL be classified into exactly one
of the following five categories (138A §4.1):

1. **Architectural observations** — whether each stage's actual output
   matches its GLP-001 §6.1 "required outputs" definition.
2. **Governance observations** — whether the pilot's stage sequence
   matched GLP-REQ-016's required order with no reordering, and whether
   each stage's exit criteria were independently evaluated rather than
   self-asserted (GAC-REQ-028 item 2).
3. **Participant observations** — whether each stage's own participant
   could name their stage's exit criteria without consulting GLP-001's
   full text (137Y §6.2), recorded as a direct report from that
   participant, not inferred by an observer on the participant's behalf.
4. **Verification observations** — whether the pilot's Independent
   Verification stage correctly scoped itself to Scope A only, or also
   claimed Scope B coverage it was not separately commissioned to provide
   (GLP-REQ-033, GAC-REQ-036 item 4).
5. **Unexpected outcomes** — any pilot event that does not fit categories
   1–4 (a stage taking materially longer or shorter than expected, a
   participant raising a concern about GLP-001's own text, a rollback
   trigger firing) SHALL be recorded as its own item rather than forced
   into another category.

### 7.2 Mandatory objective/subjective/hypothesis separation

PGP-REQ-028: Every observation recorded under §7.1 SHALL be tagged as
exactly one of the following three kinds (138A §4.2):

1. **Objective evidence** — directly checkable against a specific
   artifact, phase report, commit, or file; carries the same citation
   discipline GLP-REQ-028 already requires throughout GLP-001.
2. **Subjective experience** — a participant's or observer's own
   first-person account, explicitly attributed to that person and dated.
   Not downgraded to less-than-evidence status (137Y §11 already treats
   qualitative signals as legitimate) but never silently merged with
   objective evidence in a summary.
3. **Hypothesis** — an observer's own interpretive claim not directly
   attributable to either an artifact or a named participant's own
   statement. SHALL be labeled as such in every evidence package (§12)
   and SHALL NOT be presented to Stage 5 or Stage 6 as if it were
   objective evidence or subjective experience.

PGP-REQ-029: Every observation SHALL identify its provenance: which pilot
stage produced it, and which artifact, phase report, or named participant
it is drawn from. An observation with no stated provenance is not
admissible into the assessment package (§12).

## 8. Evidence Contract

PGP-REQ-030: This section freezes the minimum required evidence categories
138A §5 defines, decomposing GLP-001 §9's evidence expectations and GAC-001
§14's evidence-type table (GAC-REQ-064) into the four operational
categories 138A introduces, plus the comparison-baseline requirement 138A
§9 introduces. This contract adds no new evidence *artifact* requirement
beyond what GLP-001 §9 (GLP-REQ-027) and GAC-001 §7 (GAC-REQ-029) already
require; it defines only the categories used to organize that evidence.

### 8.1 Provenance requirement

PGP-REQ-031: Every evidence item, in every category below, SHALL identify
its provenance: which pilot stage produced it, which phase report or
artifact it is drawn from, and which §7.2 tag (objective / subjective /
hypothesis) applies. An evidence item with no stated provenance is not
admissible into the assessment package (§12).

### 8.2 Minimum evidence categories

PGP-REQ-032: The following minimum evidence categories SHALL be populated
for every PGP-governed pilot (138A §5):

1. **Architectural evidence** — lifecycle clarity (did the pilot's
   participants need to re-derive a stage sequence GLP-001 already
   specifies); contract quality (did Contract Freeze produce zero
   ambiguous requirements on first attempt); requirement traceability
   (can every implementation decision be traced to a specific frozen
   requirement).
2. **Contract evidence** — the pilot's own domain-specific Contract Freeze
   deliverable, plus its documented exit-criteria evaluation (mirrors §12
   item 2 below).
3. **Verification evidence** — decision consistency (stage transitions
   followed GLP-REQ-016's required order without exception); review
   quality (exit-criteria evaluation came from an independent check, not
   the producing participant's own assertion); verification outcomes (the
   pilot's own Independent Verification verdict and defect count, taken
   directly from that stage's own phase report).
4. **Governance observations** — every §7.1 category-2 observation
   recorded during the pilot, carrying its §7.2 tag.
5. **Participant observations** — every §7.1 category-3 observation, plus
   §8.2 item 6's qualitative accounts, each carrying its §7.2 tag.
6. **Metrics** — effort (phase count and, where recorded, elapsed time per
   stage); complexity (the pilot's own Architecture-stage scope statement,
   used as the baseline against which actual complexity is compared, §5.3
   above); documentation overhead (page/section count of the pilot's own
   contract and phase reports relative to a comparable non-GLP
   initiative, per §8.4 below).
7. **Lessons learned** — any §7.1 category-5 "unexpected outcomes" entry,
   plus any rollback event and its GAC-REQ-047 documentation.

PGP-REQ-033: **Qualitative accounts** (a component of evidence categories
5 and part of the required minimum, 138A §5.4) SHALL include: reviewer
experience (the Independent Verification participant's own first-person
account of whether GLP-001's exit criteria were usable without full-text
consultation); author experience (the Architecture and Contract Freeze
participants' own first-person accounts of the same question for their own
stages); and, where a Scope B check is separately commissioned
(GLP-REQ-034), verifier experience (that verifier's own account of whether
the Scope A/Scope B distinction was usable in practice).

### 8.3 Reproducibility requirement

PGP-REQ-034: Evidence collected under this contract SHALL be reproducible:
every evidence item SHALL cite a specific, checkable source (file path,
phase ID, requirement ID), consistent with GLP-REQ-028 of GLP-001 and the
citation discipline GAC-001 adopts throughout (GAC-REQ-037, GAC-REQ-053,
GAC-REQ-065). An unattributed narrative claim is not sufficient evidence
for any purpose under this contract.

### 8.4 Comparison baseline requirement

PGP-REQ-035: A pilot's §8.2 evidence SHALL be compared against the
following baselines, each already available in the repository without new
instrumentation (138A §9):

1. **Historical PCAE initiatives** — the corpus Phase 137V studied
   (`docs/PHASE_137V_GOVERNANCE_LIFECYCLE_PATTERN_ARCHITECTURE.md`),
   specifically the subset that met GLP-001 §5.1 applicability criteria
   before GLP-001 existed and so ran under an informally-reinvented
   lifecycle.
2. **Equivalent architecture phases run without GLP-001** — any concurrent
   or near-concurrent PCAE initiative of comparable scope that does not
   cite GLP-001, if one exists during the pilot's own window.
3. **Governance outcomes before GLP-001** — the repair/incident corpus
   GLP-REQ-012 already cites, as the baseline rate and shape of
   governance-tooling defects that occurred without any GLP-001-style
   lifecycle discipline in force.
4. **Verification quality trends** — Independent Verification defect
   counts and verdict distribution across the same historical corpus, as
   the baseline for the "marginal defect-discovery rate" metric (§9 below).

PGP-REQ-036: **No-improvement-assumption rule.** The assessment package's
comparison against §8.4's baselines SHALL report the result as found,
including a result showing no measurable difference from baseline, or a
result showing the pilot performed worse than baseline on one or more
dimensions. A comparison that only ever reports improvement is itself a
form of confirmation bias baked into the evaluation architecture (§11
below), not a defect introduced by an individual assessor, and is
prohibited.

PGP-REQ-037: A pilot's comparison against §8.4's baselines is necessarily
n=1 relative to a multi-phase baseline (137Y §6.2's own disclosure). This
contract does not overstate what a single pilot's comparison can establish;
§13 (Governance Decision Contract) preserves "Continue pilot" (GAC-001 §9
outcome (b)) as available whenever the evidence is inconclusive or
insufficiently representative.

## 9. Success Criteria Contract

PGP-REQ-038: This section freezes the measurable success indicators 138A
§6.1 defines, mapping GAC-001 §15's seven already-frozen adoption-process
success criteria (GAC-REQ-067) to the evidence category (§8) that supplies
each. This contract does not restate GAC-001 §15's criteria as new
criteria; it adds no eighth criterion.

PGP-REQ-039: Each success criterion SHALL be supplied from the stated
evidence source:

| GAC-001 §15 criterion | Supplied by |
|---|---|
| Pilot completion rate | §8.2 item 4 (governance observations — recorded compliance outcome) |
| Compliance-model determinacy | §8.2 item 4 (governance observations — verification outcomes) |
| Marginal defect-discovery rate | §8.2 item 1 (architectural — contract quality) + item 3 (verification outcomes) |
| Ceremony-to-blast-radius ratio | §8.2 item 6 (metrics — effort, complexity) |
| Reduced duplicated lifecycle decisions | §8.2 item 1 (architectural — lifecycle clarity) |
| No increase in reported governance defects attributable to adoption | §8.2 item 4, cross-checked against §8.2 item 5 (qualitative accounts) |
| Positive independent assessment | Stage 5's own output (GAC-REQ-038), not itself a pilot-evidence category |

PGP-REQ-040: **Acceptable governance overhead** (improved governance
clarity, improved architectural consistency, improved traceability,
improved verification quality, and acceptable governance overhead, per the
governing prompt's own examples) requires **objective justification**:
overhead is acceptable when the pilot's §8.2 item 6 (metrics) evidence
shows phase count and elapsed time proportionate to the applicability
criterion (§4.1 item 1) the candidate was designated under — a
track-closing or cross-cutting initiative justifies more ceremony than a
narrowly-scoped one meeting only the sibling-drift criterion. This contract
does not set a numeric threshold, consistent with GLP-REQ-024's own
explicit refusal to set one; Stage 5 judges proportionality qualitatively
against the pilot's own stated scope (§5), not against a fixed number.

PGP-REQ-041: Success requires benefit exceeding cost: a pilot that
completes with a "Compliant" GLP-001 §11 outcome but whose §8.2 item 6
evidence shows disproportionate ceremony is not, by that fact alone, a
success signal — GAC-REQ-069 item 3 already names disproportionate
governance cost as independently sufficient to override an otherwise
favorable recommendation (§10, §13 below).

## 10. Failure Criteria Contract

PGP-REQ-042: This section freezes the measurable failure conditions 138A
§6.2 defines as new architectural content, bounded so as not to contradict
GAC-REQ-032 (a failed pilot is reported exactly as candidly as a successful
one) or GAC-REQ-069 (which already treats several of the following as
override conditions for the Stage 6 decision, not as "failure" per se).

PGP-REQ-043: A pilot exhibits a failure condition when its §8 evidence
shows any of the following:

1. **Governance inflation** — the pilot's own participants introduce a new
   compliance-checking role, tool, or apparatus beyond what GAC-REQ-054
   already permits reusing.
2. **Disproportionate overhead** — the pilot's §8.2 item 6 (metrics)
   evidence shows phase count or elapsed time out of proportion to its
   designated applicability criterion (§4.1 item 1) — restates
   GAC-REQ-069 item 3.
3. **Ambiguity** — the pilot's GLP-001 §11 compliance outcome is genuinely
   contested between two of the four outcome categories, with Stage 5
   unable to resolve it from GLP-001's existing text alone (mirrors
   GAC-REQ-036 item 2).
4. **Inconsistent advisory use** — different pilot stages interpret the
   same GLP-001 requirement differently, with no single determinate
   reading recoverable from GLP-001's own text.
5. **Unverifiable outcomes** — a pilot stage's own claimed exit-criteria
   satisfaction cannot be independently checked from artifacts (violates
   the §7.2 objective-evidence standard).
6. **Insufficient evidence** — a required §8.2 evidence category is
   missing, or a majority of the pilot's participants could not name
   their own stage's exit criteria without consulting GLP-001's full text
   (contradicts the 137Y §6.2 fourth success signal — "poor usability").

PGP-REQ-044: **Failure shall never automatically invalidate GLP-001.**
Pilot failure against one or more of §10's criteria has still discharged
the pilot's purpose — testing GLP-001, not proving it correct, per 138A's
own Purpose section — and its evidence remains fully valid input to §12
and §13 below, exactly as GAC-REQ-032 and 137Y §6.5 already establish for a
"Non-compliant" or rolled-back pilot outcome. A failed pilot is one
determinate outcome among the range this contract evaluates, never itself
a verdict on GLP-001's substance; only a governed Stage 6 decision under
GAC-001 §9, informed by §13 below, may reach a conclusion about GLP-001
itself.

## 11. Bias Mitigation Contract

PGP-REQ-045: This section freezes protections against the bias classes
138A §10 identifies as new architectural content beyond GAC-001's single
named "pilot bias" (GAC-REQ-018 item 1, GAC-REQ-022, mitigated by the §4
pre-selection checks).

PGP-REQ-046: The following bias classes SHALL each be mitigated by the
stated mechanism, and no mechanism below SHALL be omitted from a pilot's
evaluation:

| Bias | Mitigation |
|---|---|
| Confirmation bias | §7.2's mandatory objective/subjective/hypothesis tagging forces every claim to cite a checkable source or be labeled as unattributed interpretation; §8.4's comparison baselines are fixed in advance of pilot execution, not chosen after outcomes are known |
| Novelty bias | §8.4 item 2 (equivalent non-GLP phases run concurrently) provides a control not subject to the same attention; §8.2 item 5 qualitative evidence explicitly asks participants whether GLP-001 itself, versus increased scrutiny generally, drove any observed effect |
| Author bias | GAC-REQ-035 already requires the Stage 5 assessor to be distinct from pilot participants; §12's assembly rule additionally requires the assessor to compile the package directly from artifacts, not from a participant's own narrative summary |
| Reviewer bias | §7.1 governance observations explicitly check whether exit criteria were independently evaluated, not self-asserted, giving Stage 5 a check on the reviewer's own rigor independent of the reviewer's own report |
| Survivorship bias | GAC-REQ-032 already requires a stalled, descoped, or failed pilot to be reported exactly as candidly as a successful one; §10's final paragraph removes the incentive to bury an unfavorable pilot |
| Selective evidence | §8.1's provenance requirement makes every evidence item individually traceable to a specific stage/artifact, so an assembled package (§12) can be checked for omissions by comparing it against the pilot's own full phase-report history |

PGP-REQ-047: **Disclosure of limitations is required.** Stage 5's
independent assessment output SHALL explicitly disclose its own
limitations — which of the §11 bias classes it could not fully rule out,
and why — as a stated part of its findings, not left implicit. This
mirrors GAC-REQ-065's existing "unattributed narrative claim is not
sufficient evidence" standard, applied reflexively to the assessment's own
self-description.

## 12. Assessment Preparation Contract

PGP-REQ-048: This section freezes the deliverables required for a future
independent Stage 5 assessment (GAC-001 §8), assembling GAC-001 §14's
already-frozen evidence-type table (GAC-REQ-064) into the operational
procedure 138A §7 defines as new content — operational detail GAC-001
itself deliberately leaves unspecified (GAC-REQ-068).

PGP-REQ-049: The required assessment package SHALL contain exactly the
following six inputs, assembled by the assessor from artifacts already
produced during the pilot (no new artifact type is created solely for
assembly):

1. **Evidence** — the pilot's own Architecture-stage design document, plus
   its designation-rationale statement (§5.1).
2. **Contracts** — the pilot's own domain-specific Contract Freeze
   deliverable, plus its documented exit-criteria evaluation.
3. **Findings** — the pilot's own Independent Verification phase report,
   with its verdict, defect list, and Scope A/B disclosure (GLP-REQ-033),
   plus every §7 observation and §8.2 item 5 qualitative account, each
   carrying its §7.2 tag.
4. **Metrics** — the §9 success-metric mapping table, populated with the
   pilot's own actual values per category, plus the §8.4 comparison
   result.
5. **Limitations** — the §11 disclosure-of-limitations statement.
6. **Traceability** — every evidence item's §8.1 provenance record, so the
   package's completeness can itself be checked against the pilot's own
   full phase-report history.

PGP-REQ-050: **Assembly rule.** The assessor — who SHALL be someone other
than the pilot's own participants (GAC-REQ-035) — SHALL compile the
package directly from the six inputs above, never by re-summarizing a
pilot participant's own narrative account of their own success. This
mirrors GLP-001's own re-derive/do-not-trust discipline (GLP-REQ-030
pattern) applied to package assembly itself, not only to the assessment
that follows it.

PGP-REQ-051: The assembled package is the direct input to GAC-001 §8's
independent assessment (GAC-REQ-036's seven evaluation items) and, through
it, to GAC-001 §14's evidence table (GAC-REQ-064) for the Stage 6 decision.
This contract adds no new evaluation criterion beyond GAC-REQ-036's
existing seven.

## 13. Governance Decision Contract

PGP-REQ-052: This section freezes the contractual inputs a future
governance decision requires, restating GAC-001 §9's already-frozen
outcome set and input list (GAC-REQ-040–044) as the terminus this
contract's evidence machinery feeds. This contract does not add a sixth
outcome, does not reweight the five GAC-001 already defines, and does not
narrow GAC-REQ-041's input list.

PGP-REQ-053: The possible governance-decision outcomes remain exactly the
five GAC-001 §9 (GAC-REQ-042) already freezes:

1. **Continue advisory evaluation** — restates GAC-001 outcome (b),
   "Continue pilot": run one or more additional pilots before deciding, if
   the §12 assessment package finds the existing evidence inconclusive or
   insufficiently representative.
2. **Revise protocol** — a future revision to this contract's own
   evaluation machinery, per §16 (Extensibility Contract) below, if a
   defect is found in how observation, evidence, or assessment
   preparation itself was specified — distinct from a revision to GLP-001.
3. **Revise GLP** — restates GAC-001 outcome (d), "Revise": amend GLP-001
   per its own extensibility rules (GLP-REQ-041–043) before any wider use
   is authorized, if the §12 assessment package finds a defect in
   GLP-001's applicability criteria or compliance model.
4. **Recommend adoption** — restates GAC-001 outcome (a), "Adopt": expand
   GLP-001 to a defined class of future initiatives, or to a wider model,
   per an explicit, separately-governed contract revision.
5. **Reject adoption** — restates GAC-001's fifth outcome, "Reject":
   decline to expand GLP-001's role beyond its current frozen, verified,
   advisory-eligible state, with no further pilot planned, if the §12
   assessment package finds the ceremony cost disproportionate or the
   pilot evidence unfavorable.

PGP-REQ-054: **Automatic adoption is prohibited.** No principle in this
contract, individually or in combination, and no accumulation of §7
observations, §8 evidence, or §9 success signals SHALL, by itself, cause
outcome 4 (Recommend adoption) to occur. Outcome 4 requires the explicit,
documented GAC-001 §9 governance decision, informed by a completed §12
assessment package (GAC-REQ-039, GAC-REQ-043).

PGP-REQ-055: The §12 assembled package is the complete input to GAC-REQ-041
items 1–4 (compliance outcome, Stage 5 findings, compatibility, ceremony
cost); GAC-REQ-041 items 5–6 (governance burden on future initiatives;
alternatives including deferring the decision) remain, as GAC-001 already
states, matters for the Stage 6 decision-makers' own judgment at decision
time, not something a pilot's own evidence package can supply in advance
(138A §8).

PGP-REQ-056: This contract explicitly does not prefer any of the five §13.2
outcomes. A pilot that produces unfavorable evidence is exactly as
architecturally complete, by this contract's own standard, as one that
produces favorable evidence (§10 final paragraph).

## 14. Compatibility Contract

PGP-REQ-057: This contract complements existing PCAE governance, GLP-001,
GAC-001, and PFR-001; it does not replace, redefine, or weaken any of them.

PGP-REQ-058: **Additive governance.** This contract adds no new phase type,
no new contract concept, and no new compliance-checking apparatus beyond
what GLP-001, GAC-001, and existing PCAE governance already define
(GAC-REQ-008 item 6). Every observation, evidence, and assessment
obligation above reuses ordinary PFR-001-conformant phase reports and
existing artifacts (§5.6, §12).

PGP-REQ-059: **Backward compatibility.** This contract is compatible with
GLP-001 v1.0 as frozen (137W) and verified (137X), and with GAC-001 v1.0 as
frozen (137Z) and verified (137ZA), without requiring any change to either
contract's text. A future revision to GLP-001 or GAC-001 remains
independently governed by that contract's own extensibility mechanism
(GLP-001 §13, GAC-001 §18), not by this contract.

PGP-REQ-060: **No retrospective application.** No provision of this
contract SHALL be applied retroactively to any initiative completed before
this contract's own freeze, including Phase 138A itself and every
initiative it or 137V–137Z studied. Advisory use, pilot designation, and
evaluation under this contract apply prospectively only, mirroring
GAC-REQ-071.

PGP-REQ-061: **Preservation of existing authority.** No prior binding PCAE
contract — PFR-001, the Canonical Phase ID Parsing Contract, the Typed
Authority Model Consumption Contract, GLP-001, GAC-001 — loses any
authority as a result of this contract's existence (mirrors GAC-REQ-075).

PGP-REQ-062: **Preservation of runtime behavior.** This contract, and any
observation, evidence-collection, or assessment activity performed under
it, SHALL NOT change runtime capability. Runtime remains Observed / observe
/ unavailable throughout (§17 below).

## 15. Traceability Contract

PGP-REQ-063: Every SHALL in this contract SHALL trace to GLP-001, GAC-001,
or Phase 138A's architecture. This contract introduces no evaluation rule
that Phase 138A's architecture does not already support, and no
eligibility, execution, or decision rule that GAC-001 does not already
freeze. No orphan contractual obligation exists in this document.

### 15.1 Traceability matrix

| PGP-001 obligation | 138A section | GLP-001 / GAC-001 basis |
|---|---|---|
| Pilot Eligibility Contract (§4, PGP-REQ-009–014) | §1 | GAC-001 §6 (GAC-REQ-017–025); GLP-001 §5 |
| Pilot Scope Contract (§5, PGP-REQ-015–022) | §2 | GAC-001 §6.6 (GAC-REQ-024–025), §7 (GAC-REQ-030) |
| Advisory Application Contract (§6, PGP-REQ-023–025) | §3 | GAC-001 §5, §7 (GAC-REQ-010–016, 026–033) |
| Observation Contract (§7, PGP-REQ-026–029) | §4 | GAC-001 §7 (GAC-REQ-028) |
| Evidence Contract (§8, PGP-REQ-030–037) | §5, §9 | GLP-001 §9 (GLP-REQ-027–028); GAC-001 §7 (GAC-REQ-029), §14 (GAC-REQ-064–065) |
| Success Criteria Contract (§9, PGP-REQ-038–041) | §6.1 | GAC-001 §15 (GAC-REQ-067–068) |
| Failure Criteria Contract (§10, PGP-REQ-042–044) | §6.2 | GAC-001 §16 (GAC-REQ-069) |
| Bias Mitigation Contract (§11, PGP-REQ-045–047) | §10 | GAC-001 §6.1 item 1 / §6.4 (GAC-REQ-018, GAC-REQ-022) |
| Assessment Preparation Contract (§12, PGP-REQ-048–051) | §7 | GAC-001 §8 (GAC-REQ-034–039), §14 (GAC-REQ-064) |
| Governance Decision Contract (§13, PGP-REQ-052–056) | §8 | GAC-001 §9 (GAC-REQ-040–044) |
| Compatibility Contract (§14, PGP-REQ-057–062) | §13, §16 | GLP-001 §12; GAC-001 §17 (GAC-REQ-071–075) |
| Extensibility Contract (§16, PGP-REQ-064–067) | — | GLP-001 §13 (GLP-REQ-041–043); GAC-001 §18 (GAC-REQ-076–080) |
| Security Considerations (§17, PGP-REQ-068–069) | §13 (Validation) | GLP-001 §14; GAC-001 §19 (GAC-REQ-081–083) |

PGP-REQ-064 is intentionally not present in this table; see §16 below,
which begins the Extensibility Contract's own requirement numbering.

## 16. Extensibility Contract

PGP-REQ-064: Future evolution of this contract SHALL proceed only through
additive revisions, each stating explicitly what it adds or narrows and its
compatibility impact, per the same discipline GLP-REQ-041 of GLP-001 and
GAC-REQ-076 of GAC-001 establish.

PGP-REQ-065: A future revision SHALL itself receive independent
verification before being treated as binding, mirroring GLP-001's own
treatment by Phase 137X and GAC-001's own treatment by Phase 137ZA.

PGP-REQ-066: A future revision MAY be authorized only by explicit governed
process (a dedicated contract-repair or contract-revision phase), never by
silent reinterpretation of this contract's existing text during an
unrelated phase. Every future revision's rationale SHALL be documented,
including the specific evidence (a completed pilot, a disclosed defect, a
discovered applicability-boundary case) that justifies it — not elapsed
time or aesthetic preference.

PGP-REQ-067: Backward compatibility with this contract's v1.0 is mandatory
for any future revision unless that revision explicitly states its
compatibility impact and supersedes a named requirement, mirroring
GLP-REQ-043 of GLP-001 and GAC-REQ-080 of GAC-001.

## 17. Security Considerations

PGP-REQ-068: This contract, and any observation, evidence-collection,
assessment-preparation, or governance-decision-input activity performed
under it, SHALL NOT change runtime capability. Runtime remains Observed /
observe / unavailable throughout.

PGP-REQ-069: This contract grants no execution, lifecycle, or governance
authority to any role named in §6–§13 above beyond what GLP-001 §8 and
GAC-001 §7–§9 already grant. This contract only organizes how that
already-granted activity is observed, evidenced, and assessed.

## 18. Validation

PGP-REQ-070: The following properties are confirmed by this contract's own
text and SHALL hold for every future PGP-governed pilot:

- **Advisory-only preserved** — §6 restates, and adds no exception to,
  GAC-REQ-006/013/055's prohibition on enforcement or mandatory compliance.
- **No pilot authorized** — §4.2 explicitly states no candidate is
  designated by this contract.
- **No pilot executed** — this contract governs evaluation machinery only;
  no pilot activity occurs as a result of this freeze (§1–§2).
- **No governance changes** — this contract modifies no provision of
  GLP-001 or GAC-001 (§2, §14).
- **No enforcement introduced** — §6, §11, and §12 all restate existing
  GLP-001/GAC-001 enforcement prohibitions rather than introducing a new
  compliance-checking mechanism (GAC-REQ-054).
- **No runtime changes** — §17 restates Runtime remains Observed / observe
  / unavailable.
- **Compatibility preserved** — §14 confirms compatibility with GLP-001,
  GAC-001, PFR-001, and existing PCAE governance.

## 19. Deliverables

PGP-REQ-071: This contract's freeze produces the following deliverables,
each a section of this single document, mirroring the GLP-001/GAC-001
single-consolidated-contract-file precedent (no separate phase narrative
document):

- **PGP-001 v1.0** — this document in its entirety.
- **Pilot Eligibility Contract** — §4.
- **Observation Contract** — §7.
- **Evidence Contract** — §8.
- **Assessment Preparation Contract** — §12.
- **Governance Decision Contract** — §13.
- **Compatibility Contract** — §14.
- **Traceability Matrix** — §15.1.

## 20. No-Go

This phase did not, and does not authorize any future phase acting solely
on this document's authority to:

- No pilot was executed by this phase.
- No pilot was authorized by this phase.
- No pilot initiative was designated by this phase.
- No provision of GLP-001 was modified by this phase.
- No provision of GAC-001 was modified by this phase.
- No governance rule was changed by this phase.
- No lifecycle semantics were changed by this phase.
- No enforcement mechanism was introduced by this phase.
- No runtime functionality was added by this phase.
- No production code was modified by this phase.
- No new compliance-checking apparatus, tool, or role was introduced by
  this phase, beyond the assembly procedure in §12, which reuses existing
  phase-report artifacts exclusively.

Contract only.

## 21. Phase 138B freeze confirmation

Phase 138B freezes the pilot eligibility checklist, the pilot scope
boundaries, the advisory application model, the observation discipline
(objective/subjective/hypothesis tagging), the evidence collection
categories and comparison-baseline requirement, the success and failure
criteria, the bias mitigation table, the assessment preparation assembly
procedure, the governance-decision connective layer, the compatibility
guarantees, the traceability matrix, the extensibility rules, and the
security considerations derived from Phase 138A as PGP-001 v1.0.

No pilot is executed by this freeze. No pilot is authorized by this
freeze. No pilot initiative is designated by this freeze. No provision of
GLP-001 is modified. No provision of GAC-001 is modified. No governance
behavior changes. No enforcement is introduced. No production code is
touched. Runtime remains Observed / observe / unavailable.

## 22. Recommended next phase

**138C — Pilot Governance Protocol Independent Verification.**

Purpose: independently re-derive and verify PGP-001 v1.0 without trusting
Phase 138B. Validate every contractual obligation, eligibility rule,
observation requirement, evidence requirement, assessment input,
governance-decision constraint, compatibility guarantee, and traceability
relationship. Confirm that PGP-001 faithfully implements the Phase 138A
architecture while preserving GLP-001's advisory-only philosophy. No pilot
authorization, execution, governance changes, or runtime modifications are
permitted.
