# Pilot Proposal & Authorization Contract

## Contract identity and status

**Contract:** PPA-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 138F — Advisory Pilot Authorization Contract Freeze
**Architecture basis:** Phase 138E — Advisory Pilot Authorization Architecture
(`docs/PHASE_138E_ADVISORY_PILOT_AUTHORIZATION_ARCHITECTURE.md`)
**Governed subject:** whether a future candidate initiative may proceed
toward a GAC-001 §6 pilot designation (GAC-REQ-017–025)

PPA-001 v1.0 is the sole normative authority governing **how a future
Advisory Governance Pilot candidate is proposed, reviewed, authorized,
deferred, rejected, required to supply additional evidence, or had its
consideration suspended** — a decision layer sitting strictly upstream of,
and additive to, GAC-001 §6's already-frozen pilot-designation act. It does
not govern GAC-001's own designation act, GAC-001 §7's pilot execution,
PGP-001's observation/evidence/assessment machinery, or GAC-001 §9's
Stage-6 governance decision, all of which remain exclusively those
contracts' domain (§2 below).

Phase 138E's architecture is the approved design basis for this contract.
This contract derives every requirement below from that architecture's
content; it does not perform new evidence-gathering and it does not invent
an obligation Phase 138E's architecture does not support. Where this
contract and the Phase 138E architecture document differ in force, this
contract is normative for compliance-evaluation purposes, and any such
difference is itself a defect to be resolved by a governed contract
revision, not by silently preferring one document over the other in
practice.

This is contract text only. It authorizes no pilot, designates no pilot,
executes no pilot, and modifies no provision of GLP-001, GAC-001, or
PGP-001. Runtime remains Observed / observe / unavailable throughout every
operation governed by this contract.

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative, with the meanings given in
GLP-001 §0, adopted unchanged by GAC-001 §0 and PGP-001 §0; this contract
adopts the same meanings unchanged.

A **PPA-governed candidate** is any prospective pilot initiative that has
not yet been designated under GAC-001 §6. This contract's obligations
attach only to a candidate's proposal, eligibility review, authorization
review, decision, boundary, and suspension/withdrawal activity, before
designation; it imposes no obligation on ordinary phase or task work that
is not a PPA-governed candidate, and no obligation whatsoever on any
initiative once it has actually been designated (§2 below).

## 1. Purpose

PPA-REQ-001: This contract exists to convert Phase 138E's Advisory Pilot
Authorization Architecture — an Authorization Philosophy, a Pilot Proposal
Architecture, an Eligibility Review Architecture, an Authorization Review
sequence, a Decision Architecture, a Risk Review, a Pilot Boundary
Architecture, a Suspension and Withdrawal Architecture, and a Governance
Independence Architecture (138E §1–§9) — into a binding, falsifiable set of
obligations that a future candidate's authorization process SHALL satisfy
before that candidate may proceed toward GAC-001 §6 designation.

PPA-REQ-002: This contract governs the **pre-designation decision
machinery** for a future Advisory Governance Pilot candidate: how a
candidate's rationale becomes a proposal, how that proposal is reviewed for
eligibility and governance impact, how a decision among five permitted
outcomes is reached and justified, how the resulting authorization is
bounded, and how it may be suspended, withdrawn, or cancelled before
designation. It does not govern the eligibility test's own content beyond
reusing PGP-001 §4's existing checklist (§3 below), and it does not govern
designation itself, which remains GAC-001 §6's exclusive authority
(GAC-REQ-023).

PPA-REQ-003: This contract does not itself authorize any pilot candidate,
designate any pilot, or execute any pilot activity. "Authorize planning"
(§7 below) is permission to proceed toward GAC-001 §6 designation, not a
substitute for it (GAC-REQ-023); designation remains a distinct, separate
act performed by the candidate's own future Architecture-stage document
(GAC-REQ-030). Execution oversight remains GAC-001 §7's exclusive authority
(GAC-REQ-026–033); observation, evidence, and assessment remain PGP-001
§7–§13's exclusive authority.

PPA-REQ-004: Conformance with PPA-001 grants no execution, lifecycle,
governance, or runtime capability. It governs only how one specific
candidate's pre-designation decision is produced, justified, and bounded.

## 2. Scope and Non-Goals

PPA-REQ-005: This contract applies to every future PPA-governed candidate's
proposal preparation, eligibility review, authorization review, decision,
boundary enforcement, and suspension/withdrawal/cancellation activity,
strictly before GAC-001 §6 designation occurs.

PPA-REQ-006: This contract does not apply to, and imposes no obligation on,
any PCAE phase or task that is not a PPA-governed candidate, nor to any
initiative once it has actually been designated under GAC-001 §6 — from
that point forward, GAC-001 §7–§10 and PGP-001 §5–§13 govern exclusively,
unaffected by this contract's existence (§12 below).

PPA-REQ-007: This contract SHALL NOT be read as, and does not:

- authorize a pilot;
- designate a pilot initiative;
- execute a pilot;
- modify GLP-001 v1.0's text (any correction remains available only
  through GLP-001's own §13 extensibility mechanism, independent of this
  contract);
- modify GAC-001 v1.0's text (any correction remains available only
  through GAC-001's own §18 extensibility mechanism, independent of this
  contract);
- modify PGP-001 v1.1's text (any correction remains available only
  through PGP-001's own §16 extensibility mechanism, independent of this
  contract);
- narrow, reweight, or restate GAC-001 §6's eligibility test as a new test
  (§3 below reuses PGP-001 §4 verbatim as the eligibility-evidence
  component of the proposal package);
- add a sixth authorization outcome beyond the five §7 below freezes, or a
  sixth GAC-001 §9 Stage-6 outcome (§7.3 below; the two outcome sets remain
  distinct and this contract adds to neither);
- implement, automate, or enforce proposal review, eligibility review, or
  decision-making in tooling — every obligation below is discharged by a
  human authority or independent reviewer using existing PCAE artifacts,
  never by a new compliance-checking apparatus (mirrors GAC-REQ-054,
  PGP-REQ-007 item 5);
- change runtime, lifecycle, or governance capability (Runtime remains
  Observed / observe / unavailable throughout);
- retrospectively reclassify, invalidate, or re-score any completed
  initiative, including any initiative Phase 137V–138E studied or produced
  (§12).

## 3. Terminology

PPA-REQ-008: The following terms are normative and SHALL be used with
exactly the meaning given here by every document or phase that invokes this
contract, in addition to the terms GLP-001 §4, GAC-001 §3, and PGP-001 §3
already define, which this contract adopts unchanged:

- **Pilot proposal** — the candidate-facing document a prospective sponsor
  prepares before authorization review begins, containing the nine
  components §4.1 below freezes (138E §2).
- **Proposer** — the individual or role preparing a candidate's pilot
  proposal, distinct from the independent reviewer (§5 below) and the
  authorizing human authority (§7 below).
- **Independent reviewer** — the party conducting eligibility review (§5)
  and Authorization Review (§6), distinct from the proposer per §11.2
  below.
- **Authorizing human authority** — the party (or explicitly named
  delegate, per the GAC-REQ-023 pattern) who selects one of the five §7.1
  decision outcomes.
- **Authorization** — the "authorize planning" decision outcome (§7.1 item
  1) and the bounded permission it grants (§9 below), distinct from
  GAC-001 §6 designation.
- **Comparison baseline** — the historical corpus (137V) and existing
  frozen contract text (GLP-001, GAC-001, PGP-001) against which a
  proposal's own eligibility claims are independently checked (§5.2 below).

## 4. Pilot Proposal Contract

PPA-REQ-009: This section freezes the mandatory proposal contents 138E §2
defines as new architectural content — GAC-001 §14 (GAC-REQ-064) names
evidence categories generically but does not define a pre-designation
proposal document; this contract supplies that missing document format.

### 4.1 Required proposal package contents

PPA-REQ-010: A pilot proposal SHALL contain each of the following nine
components, each independently checkable, none satisfied by narrative
assertion alone (138E §2.1):

1. **Candidate rationale** — why this specific initiative is being
   proposed as a pilot candidate now, stated before any eligibility
   argument is made.
2. **Eligibility evidence** — the candidate's own answers to PGP-001
   §4.1's four-item suitability checklist (applicability, representative
   complexity, not-mid-flight, willing sponsor) and §4.2's exclusion pass,
   each answer citing a specific artifact or fact, not an assertion of
   qualification.
3. **Expected objectives** — what the pilot is intended to test about
   GLP-001, phrased as a testable claim, not as a foregone conclusion (an
   objective phrased as "prove GLP-001 works" is malformed).
4. **Success criteria** — stated in terms of PGP-001 §9's already-frozen
   success-metric table; the proposal does not invent new success metrics.
5. **Failure criteria** — stated in terms of PGP-001 §10's already-frozen
   failure conditions; same reuse discipline as item 4.
6. **Scope** — the candidate's own stated boundary: which GLP-001 §5.1
   applicability criterion (or criteria) it claims to meet, and an estimate
   of its own expected phase count.
7. **Governance impact** — what, if anything, about existing PCAE
   governance, contracts, or lifecycle mechanics the candidate's own
   subsystem work touches.
8. **Risks** — the candidate's own disclosure of risks specific to its
   proposed subject matter, feeding into, but not replacing, the
   independent Risk Review (§8 below).
9. **Expected evidence** — which of PGP-001 §8.2's minimum evidence
   categories the candidate expects to be able to produce, and which — if
   any — it anticipates being thin or unavailable, disclosed in advance.

### 4.2 Proposal completeness rule

PPA-REQ-011: A proposal missing any of the nine §4.1 components is
incomplete and SHALL NOT proceed past the Authorization Review's first step
(§6.1 below). This is a structural, not a discretionary, gate — completeness
is checked before eligibility is evaluated (138E §2.2).

### 4.3 Reuse discipline

PPA-REQ-012: This section introduces no new evidence *artifact* beyond what
PGP-001 §8 and GAC-001 §14 already define; it defines only the
pre-designation document that organizes a candidate's own claims about that
evidence before any of it has actually been produced. No pilot proposal, by
itself, constitutes pilot evidence under PGP-001 §8 — proposal content
becomes evidence only once the candidate is designated and its own
Architecture stage begins producing PGP-001-governed artifacts (138E §2.3).

## 5. Eligibility Review Contract

PPA-REQ-013: This section freezes the reviewer-facing procedure 138E §3
defines for evaluating a proposal's own §4.1 item 2 eligibility evidence.
GAC-001 §6 already freezes the eligibility test as binding contract text,
and PGP-001 §4 already operationalizes it into a checklist; this contract
adds no new eligibility criterion and narrows none of them.

### 5.1 Excluded-class fast check

PPA-REQ-014: Before any other eligibility question is applied, the
independent reviewer SHALL confirm the candidate does not fall into any of
PGP-001 §4.2's five excluded classes (emergency repairs, production
hotfixes, documentation corrections, repository maintenance, unrelated
runtime work). A candidate failing this fast check is rejected (§7 below)
without proceeding to §5.2.

### 5.2 Mandatory review questions

PPA-REQ-015: For each of PGP-001 §4.1's four checklist items, the
independent reviewer SHALL answer the following, in order, recording the
answer against the proposal's own cited evidence, never against the
proposal's own summary of that evidence (138E §3.1):

1. **Applicability** — does the candidate's own cited evidence
   independently establish at least one GLP-001 §5.1 criterion, using only
   the artifact the proposal cites?
2. **Representative complexity** — does the candidate's own stated phase
   count estimate place it credibly between the smallest
   technically-qualifying initiative and the repository's largest, using
   the reviewer's own independent comparison against the historical corpus
   (137V)?
3. **Not already mid-flight** — can the reviewer independently confirm,
   from `git log` or the candidate's own existing phase history, that no
   Architecture-stage document already exists for this initiative under an
   informal, undesignated pattern?
4. **Willing sponsor** — does the proposal name a specific human authority
   who has, in fact, agreed to designate the candidate and to accept its
   disclosed ceremony cost as a deliberate tradeoff?

### 5.3 Objective-evidence requirement

PPA-REQ-016: Every §5.2 answer SHALL cite the specific artifact, file path,
phase ID, or named individual's own statement it is drawn from. An answer
supported only by the reviewer's own restatement of the proposal's own
claim is not an independent review and SHALL NOT be recorded as having
satisfied this section (138E §3.2).

### 5.4 Rejection of implicit qualification

PPA-REQ-017: A candidate SHALL NOT be treated as eligible merely because no
§5.2 question was answered "no" — every question SHALL be answered
affirmatively, with cited evidence, before eligibility is confirmed.
Silence, an unanswered question, or an answer of "presumably yes" is
equivalent to "no" for the purpose of this section (138E §3.3).

## 6. Authorization Review Contract

PPA-REQ-018: This section freezes the ordered review sequence 138E §4
defines as new architectural content — neither GLP-001 nor GAC-001 nor
PGP-001 defines an ordered review procedure preceding designation. No step
may be skipped, and no step's conclusion may be asserted rather than
evaluated.

PPA-REQ-019: The review sequence SHALL proceed through the following five
steps, in order, before any decision (§7 below) is reached:

1. **Proposal completeness** — confirm the proposal contains all nine §4.1
   components. An incomplete proposal is returned for completion
   (equivalent to "request additional evidence," §7.1 item 4) before any
   further review step begins.
2. **Eligibility confirmation** — apply §5.1's excluded-class fast check,
   then §5.2's four mandatory questions. A candidate failing the fast check
   or any one of the four questions does not proceed to step 3.
3. **Governance review** — using the proposal's own §4.1 item 7
   (governance impact) disclosure as a starting point, the independent
   reviewer confirms: (a) no requirement of GLP-001, GAC-001, or PGP-001
   would be modified, reinterpreted, or narrowed by the candidate's
   proposed subject matter; (b) the candidate's proposed subject matter
   does not itself touch runtime execution capability; (c) no existing
   PCAE governance surface (a contract, `PROJECT_STATUS.md`,
   `CHANGELOG.md`, `.pcae/**` policy configuration) would need to change as
   a precondition of the candidate proceeding.
4. **Readiness confirmation** — confirm, independently, that Phase 138D's
   own readiness determination (READY FOR PILOT AUTHORIZATION PLANNING)
   has not been superseded by any later framework change — i.e., that
   GLP-001, GAC-001, and PGP-001 remain in the same frozen/verified state
   138D found them in, checkable by `git log` on `docs/contracts/`.
5. **Authorization recommendation** — only after steps 1–4 each
   independently conclude favorably does the independent reviewer produce a
   recommendation for the Decision Contract (§7). The recommendation is
   advisory input to the decision, not the decision itself.

PPA-REQ-020: **No automatic approval.** Completing steps 1–4 favorably does
not, by itself, authorize anything. No accumulation of favorable review
steps SHALL cause an "authorize planning" outcome to occur automatically;
§7 below requires an explicit, separate, recorded decision act, mirroring
GAC-REQ-043's and PGP-REQ-054's identical prohibition on automatic
adoption, applied here to authorization (138E §4.5).

## 7. Decision Contract

PPA-REQ-021: This section freezes the five permitted authorization outcomes
138E §5 defines as new architectural content, distinct from and temporally
prior to GAC-001 §9's five Stage-6 outcomes.

### 7.1 Permitted decisions

PPA-REQ-022: Following Authorization Review (§6), an authorizing human
authority (or an explicitly named delegate, per the GAC-REQ-023 pattern)
SHALL select exactly one of the following five outcomes. None is
privileged by default; a proposal producing unfavorable review findings is
exactly as architecturally complete, by this contract's own standard, as
one producing favorable findings (mirrors GAC-REQ-042, PGP-REQ-056):

1. **Authorize planning** — the candidate may proceed toward GAC-001 §6
   designation. This decision does not itself designate the candidate;
   designation remains a distinct, separate act the candidate's own future
   Architecture-stage document performs (GAC-REQ-030). "Authorize
   planning" only removes this contract's own gate; it supplies no new
   authority GAC-001 §6 does not already grant, and it does not shorten,
   waive, or pre-satisfy any GAC-001 §6 requirement.
2. **Defer** — the review is inconclusive or the candidate is plausible
   but not yet ready. Deferral names the specific condition that, once
   resolved, would allow re-review; it is not an indefinite non-answer.
3. **Reject** — the candidate fails §5's eligibility test, §6 step 3's
   governance review, or is independently judged disproportionate to its
   own disclosed scope. Rejection is a final decision for this candidate in
   its current form; it does not preclude a materially different future
   proposal for the same underlying initiative.
4. **Request additional evidence** — step 1 (completeness) or step 2
   (eligibility) found the proposal's own citations insufficient to
   support a conclusion either way. This decision names the specific §4.1
   component or §5.2 question the proposal must strengthen before
   re-review.
5. **Suspend consideration** — authorization review has begun but an
   external condition makes reaching any of outcomes 1–4 premature.
   Suspension is distinct from deferral: deferral names a specific missing
   condition *for the review itself* to complete; suspension pauses the
   review because a precondition for reviewing at all has itself become
   unstable.

### 7.2 Explicit rationale requirement

PPA-REQ-023: Every decision, of every one of the five §7.1 outcomes, SHALL
be recorded with explicit rationale citing the specific Authorization
Review step (§6) and proposal component (§4.1) it is based on. A decision
recorded without rationale, or with rationale that restates the outcome
rather than justifying it, is not compliant with this contract (138E §5.2).

### 7.3 Relationship to GAC-001 §9

PPA-REQ-024: This decision is distinct from, and temporally prior to,
GAC-001 §9's five Stage-6 outcomes (Adopt / Continue pilot / Continue
advisory use / Revise / Reject). GAC-001 §9 decides GLP-001's *wider*
future after a pilot has run and been assessed; this section decides only
whether a single candidate may *begin* that pilot process. "Authorize
planning" has no relationship to, and does not predetermine, any future
GAC-001 §9 outcome for the resulting pilot (138E §5.3).

## 8. Risk Review Contract

PPA-REQ-025: This section freezes the five risk categories 138E §6 defines
as new architectural content, scoped to the authorization decision itself
and distinct from PGP-001 §11's pilot-evaluation bias classes. Every
authorization decision SHALL be preceded by an explicit assessment of each
category below; an assessment that skips a category, or restates the
category name without evaluating it against the specific candidate, does
not satisfy this section.

PPA-REQ-026: The following five risk categories SHALL each be assessed:

1. **Governance risk** — does authorizing this candidate create any
   ambiguity about which contract governs which decision? Evaluated using
   §6 step 3's governance-review findings.
2. **Operational risk** — does the candidate's own disclosed scope and
   phase-count estimate suggest ceremony that could stall, consume
   disproportionate agent-hours, or block other governed work?
3. **Evidence risk** — does the candidate's own §4.1 item 9 (expected
   evidence) disclosure suggest a real risk that PGP-001 §8.2's minimum
   evidence categories will be thin or unavailable for this specific
   candidate? A candidate at high evidence risk is not automatically
   rejected, but the risk SHALL be disclosed as part of the decision
   rationale (§7.2).
4. **Bias risk** — does the proposal itself show signs of the pilot-bias
   pattern GAC-REQ-018 item 1 and GAC-REQ-022 already name — a candidate
   selected first and an eligibility argument constructed afterward,
   contrary to §4.1 item 1's required ordering? This category is evaluated
   at the authorization stage specifically because it is the last point
   before a candidate accrues sunk-cost momentum toward designation;
   PGP-001 §11's bias-mitigation table governs bias risk *during* an
   already-designated pilot's evaluation, a later and different concern
   this section does not duplicate.
5. **Scope risk** — does the candidate's own stated scope carry a
   plausible risk of expanding past what its own proposal describes, once
   underway? This anticipates PGP-REQ-022's own scope-expansion guard by
   asking the same question one stage earlier.

## 9. Boundary Contract

PPA-REQ-027: This section freezes the boundaries an "authorize planning"
decision (§7.1 item 1) establishes for the candidate going forward, per
138E §7.

### 9.1 Approved scope

PPA-REQ-028: The approved scope is exactly what the proposal's §4.1 item 6
(scope) stated and the Authorization Review (§6) evaluated — no more. An
authorization decision SHALL name the specific GLP-001 §5.1 criterion (or
criteria) and the specific phase-count estimate it is approving; a
decision that authorizes "the candidate generally" without restating this
boundary is incomplete.

### 9.2 Prohibited expansion

PPA-REQ-029: Once authorized, the candidate's actual scope SHALL NOT
exceed the §9.1 boundary without a fresh authorization decision. This
mirrors PGP-REQ-022 one stage earlier: PGP-REQ-022 treats
post-*designation* scope growth as a GAC-001 rollback trigger; this section
treats post-*authorization*, pre-*designation* scope growth the same way —
a candidate whose actual Architecture-stage proposal (once written)
differs materially from its authorized §9.1 boundary requires renewed
authorization review, not silent absorption into an already-favorable
decision.

### 9.3 Review checkpoints

PPA-REQ-030: An authorization decision remains valid only up to the
candidate's own GAC-001 §6 designation act. If a materially different
amount of time elapses between authorization and the candidate actually
being designated (no fixed calendar bound is imposed, consistent with
GAC-REQ-024's own refusal to impose one on pilot duration), the human
authority SHOULD re-confirm §6 step 4's readiness-confirmation step before
designation proceeds.

### 9.4 Termination conditions

PPA-REQ-031: An authorization terminates, without requiring a formal
withdrawal decision (§10 below), at the first of the following:

1. the candidate is actually designated under GAC-001 §6 (authorization
   has discharged its purpose and the candidate is now governed by
   GAC-001/PGP-001's own machinery instead);
2. the named sponsor (§4.1 item 6, §5.2 item 4) withdraws before
   designation occurs;
3. a §10 suspension or withdrawal decision is recorded.

## 10. Suspension Contract

PPA-REQ-032: This section freezes the conditions for suspension,
withdrawal, and cancellation of a pre-designation authorization, distinct
from GAC-001 §10's rollback contract, which governs an already-*designated*
pilot (138E §8).

### 10.1 When authorization may be suspended

PPA-REQ-033: An "authorize planning" decision MAY be suspended when:

1. a Governance Review finding (§6 step 3) that was not present at the
   time of the original decision is later discovered — e.g., a subsequent
   contract revision to GLP-001, GAC-001, or PGP-001 changes the basis on
   which the original decision was made;
2. the candidate's actual pre-designation activity diverges materially
   from its §9.1 approved scope;
3. the named sponsor becomes unavailable or withdraws support, short of a
   full withdrawal (§10.2) if the candidate's proposer believes a
   replacement sponsor may be found.

### 10.2 When authorization may be withdrawn or cancelled

PPA-REQ-034: An "authorize planning" decision MAY be withdrawn (by the
authorizing human authority) or cancelled (by the candidate's own proposer
or sponsor) when:

1. the candidate is no longer intended to proceed toward designation at
   all;
2. a suspension condition (§10.1) is not resolved within a period the
   authorizing human authority judges reasonable, converting suspension
   into withdrawal;
3. a Risk Review finding (§8) that was not adequately weighed in the
   original decision is identified on reconsideration.

### 10.3 Required justification

PPA-REQ-035: Every suspension, withdrawal, or cancellation SHALL be
documented, stating the specific §10.1 or §10.2 trigger that applies and
citing the original authorization decision (§7.2) it reverses or pauses.
Silent suspension or withdrawal is prohibited, mirroring GAC-REQ-047's
identical requirement for pilot rollback.

### 10.4 Effect on evidence

PPA-REQ-036: A suspended, withdrawn, or cancelled authorization does not
retroactively invalidate any artifact the proposal or review process
itself produced (the proposal document, the review findings, the risk
assessment). These remain available, unmodified, as informative input to
any future proposal for the same or a related candidate, mirroring
GAC-REQ-048's identical evidence-preservation principle.

## 11. Governance Independence Contract

PPA-REQ-037: This section freezes the role separations 138E §9 defines as
new architectural content, extending GAC-REQ-035's existing
distinct-parties principle one stage earlier.

### 11.1 Separation from implementation

PPA-REQ-038: The authorization decision-maker (§7) SHALL NOT be the
candidate's own proposed Implementer (GLP-001 §8). Authorizing planning
for one's own implementation work is the same conflict GAC-REQ-035 already
prohibits for Stage 5 assessment, applied one stage earlier.

### 11.2 Separation from verification

PPA-REQ-039: The Authorization Review's independent reviewer (§6) SHALL NOT
be the candidate's own proposed Independent verifier (GLP-001 §8) for the
same candidate.

### 11.3 Separation from pilot execution

PPA-REQ-040: Authorization decision-making authority is distinct from, and
does not transfer to, any role a designated pilot's own participants hold
under GLP-001 §8 or GAC-REQ-027. Authorizing a candidate confers no
execution role on the authorizer; it confers no participant role on the
candidate's own future Architecture, Contract Freeze, Implementation, or
Independent Verification authors either.

### 11.4 Separation from outcome assessment

PPA-REQ-041: The authorization decision-maker (§7) SHALL NOT be the
candidate's own future Stage 5 independent assessor (GAC-001 §8,
GAC-REQ-035) if and when the candidate is later designated and runs a
pilot. This prevents the same party from both gating entry and grading the
outcome.

### 11.5 Decision authority distinct from pilot participation

PPA-REQ-042: No individual or role who authorized a candidate's planning
(§7) may subsequently claim that authorization as evidence of the
candidate's eventual pilot success, and no pilot participant may claim
their own participation as evidence that the original authorization was
correct. The two acts — authorizing entry, and succeeding once entered —
remain independently evaluable.

## 12. Compatibility Contract

PPA-REQ-043: This contract complements existing PCAE governance, GLP-001,
GAC-001, PGP-001, and PFR-001; it does not replace, redefine, or weaken any
of them.

PPA-REQ-044: **Additive governance.** This contract adds no new phase type,
no new contract concept, and no new compliance-checking apparatus beyond
what GLP-001, GAC-001, PGP-001, and existing PCAE governance already define
(GAC-REQ-008 item 6). Every review, decision, and boundary obligation above
reuses ordinary PFR-001-conformant phase reports and existing artifacts.

PPA-REQ-045: **Backward compatibility.** This contract is compatible with
GLP-001 v1.0 as frozen (137W) and verified (137X), GAC-001 v1.0 as frozen
(137Z) and verified (137ZA), and PGP-001 v1.1 as frozen (138B), revised
(138C.1), and verified (138C.2), without requiring any change to any of
their text. A future revision to GLP-001, GAC-001, or PGP-001 remains
independently governed by that contract's own extensibility mechanism, not
by this contract.

PPA-REQ-046: **No retrospective application.** No provision of this
contract SHALL be applied retroactively to any initiative completed before
this contract's own freeze, including Phase 138E itself and every
initiative it or 137V–138D studied. This contract applies prospectively
only, mirroring GAC-REQ-071 and PGP-REQ-060.

PPA-REQ-047: **Preservation of existing authority.** No prior binding PCAE
contract — PFR-001, the Canonical Phase ID Parsing Contract, the Typed
Authority Model Consumption Contract, GLP-001, GAC-001, PGP-001 — loses any
authority as a result of this contract's existence (mirrors GAC-REQ-075,
PGP-REQ-061).

PPA-REQ-048: **Preservation of runtime behavior.** This contract, and any
proposal, review, decision, boundary, or suspension activity performed
under it, SHALL NOT change runtime capability. Runtime remains Observed /
observe / unavailable throughout (§15 below).

## 13. Traceability Contract

PPA-REQ-049: Every SHALL in this contract SHALL trace to GLP-001, GAC-001,
PGP-001, or Phase 138E's architecture. This contract introduces no
authorization rule that Phase 138E's architecture does not already
support, and no eligibility, execution, or Stage-6-decision rule that
GAC-001 or PGP-001 does not already freeze. No orphan contractual
obligation exists in this document.

### 13.1 Traceability matrix

| PPA-001 obligation | 138E section | GLP-001 / GAC-001 / PGP-001 basis |
|---|---|---|
| Pilot Proposal Contract (§4, PPA-REQ-009–012) | §2 | GAC-001 §14 (GAC-REQ-064); PGP-001 §4 (PGP-REQ-010–013) |
| Eligibility Review Contract (§5, PPA-REQ-013–017) | §3 | GAC-001 §6 (GAC-REQ-017–025); PGP-001 §4 (PGP-REQ-009–014) |
| Authorization Review Contract (§6, PPA-REQ-018–020) | §4 | GAC-REQ-023; Phase 138D §6–§7 (readiness criteria) |
| Decision Contract (§7, PPA-REQ-021–024) | §5 | GAC-REQ-023; GAC-001 §9 (GAC-REQ-042, by contrast) |
| Risk Review Contract (§8, PPA-REQ-025–026) | §6 | GAC-REQ-018 item 1, GAC-REQ-022, GAC-REQ-069; PGP-001 §11 (by contrast) |
| Boundary Contract (§9, PPA-REQ-027–031) | §7 | PGP-REQ-022 (by extension); GAC-REQ-024 |
| Suspension Contract (§10, PPA-REQ-032–036) | §8 | GAC-001 §10 (GAC-REQ-045–049, by extension) |
| Governance Independence Contract (§11, PPA-REQ-037–042) | §9 | GAC-REQ-035 (by extension); GLP-001 §8 |
| Compatibility Contract (§12, PPA-REQ-043–048) | §12 (Validation) | GLP-001 §12; GAC-001 §17; PGP-001 §14 |
| Extensibility Contract (§14, PPA-REQ-050–053) | — | GLP-001 §13; GAC-001 §18; PGP-001 §16 |
| Security Considerations (§15, PPA-REQ-054–055) | §12 (Validation) | GLP-001 §14; GAC-001 §19; PGP-001 §17 |

## 14. Extensibility Contract

PPA-REQ-050: Future evolution of this contract SHALL proceed only through
additive revisions, each stating explicitly what it adds or narrows and its
compatibility impact, per the same discipline GLP-REQ-041, GAC-REQ-076, and
PGP-REQ-064 establish.

PPA-REQ-051: A future revision SHALL itself receive independent
verification before being treated as binding, mirroring GLP-001's own
treatment by Phase 137X, GAC-001's own treatment by Phase 137ZA, and
PGP-001's own treatment by Phase 138C/138C.2.

PPA-REQ-052: A future revision MAY be authorized only by explicit governed
process (a dedicated contract-repair or contract-revision phase), never by
silent reinterpretation of this contract's existing text during an
unrelated phase. Every future revision's rationale SHALL be documented,
including the specific evidence that justifies it — not elapsed time or
aesthetic preference.

PPA-REQ-053: Backward compatibility with this contract's v1.0 is mandatory
for any future revision unless that revision explicitly states its
compatibility impact and supersedes a named requirement, mirroring
GLP-REQ-043, GAC-REQ-080, and PGP-REQ-067.

## 15. Security Considerations

PPA-REQ-054: This contract, and any proposal, review, decision, boundary,
or suspension activity performed under it, SHALL NOT change runtime
capability. Runtime remains Observed / observe / unavailable throughout.

PPA-REQ-055: This contract grants no execution, lifecycle, or governance
authority to any role named in §5–§11 above beyond what GLP-001 §8 and
GAC-001 §6–§9 already grant. This contract only organizes how a candidate's
pre-designation proposal, review, and decision are produced and bounded.

## 16. Validation

PPA-REQ-056: The following properties are confirmed by this contract's own
text and SHALL hold for every future PPA-governed candidate:

- **No pilot authorized** — §7.1 item 1 explicitly states "authorize
  planning" does not itself designate a candidate; no candidate is named,
  evaluated, or authorized anywhere in this document.
- **No pilot designated** — §7.3 explicitly distinguishes authorization
  from GAC-001 §6/§9 designation and decision acts; neither occurs here.
- **No pilot executed** — this contract governs a pre-designation decision
  process only; no pilot activity occurs as a result of this freeze.
- **No governance changes** — this contract modifies no provision of
  GLP-001, GAC-001, or PGP-001 (§2, §12); `git diff` confirms zero changes
  to any pre-existing file under `docs/contracts/`.
- **No enforcement introduced** — §6, §8, and §11 all restate existing
  GLP-001/GAC-001/PGP-001 enforcement prohibitions rather than introducing
  a new compliance-checking mechanism (GAC-REQ-054).
- **No runtime changes** — §15 restates Runtime remains Observed / observe
  / unavailable.
- **Compatibility preserved** — §12 confirms compatibility with GLP-001,
  GAC-001, PGP-001, PFR-001, and existing PCAE governance.

## 17. Deliverables

PPA-REQ-057: This contract's freeze produces the following deliverables,
each a section of this single document, mirroring the
GLP-001/GAC-001/PGP-001 single-consolidated-contract-file precedent (no
separate phase narrative document):

- **PPA-001 v1.0** — this document in its entirety.
- **Pilot Proposal Contract** — §4.
- **Eligibility Review Contract** — §5.
- **Authorization Review Contract** — §6.
- **Decision Contract** — §7.
- **Risk Review Contract** — §8.
- **Boundary Contract** — §9.
- **Suspension Contract** — §10.
- **Governance Independence Contract** — §11.
- **Traceability Matrix** — §13.1.

## 18. No-Go

This phase did not, and does not authorize any future phase acting solely
on this document's authority to:

- No pilot was authorized by this phase.
- No pilot was designated by this phase.
- No pilot was executed by this phase.
- No provision of GLP-001 was modified by this phase.
- No provision of GAC-001 was modified by this phase.
- No provision of PGP-001 was modified by this phase.
- No governance rule was changed by this phase.
- No lifecycle semantics were changed by this phase.
- No enforcement mechanism was introduced by this phase.
- No runtime functionality was added by this phase.
- No production code was modified by this phase.
- No new compliance-checking apparatus, tool, or role was introduced by
  this phase, beyond the review procedure in §5–§6, which reuses existing
  PGP-001/GAC-001 checklist content and existing PFR-001-conformant
  reporting exclusively.

Contract only.

## 19. Phase 138F freeze confirmation

Phase 138F freezes the pilot proposal contents, the eligibility review
procedure, the authorization review sequence, the five-outcome decision
architecture, the risk review categories, the pilot boundary rules, the
suspension/withdrawal/cancellation conditions, the governance-independence
role separations, the compatibility guarantees, the traceability matrix,
the extensibility rules, and the security considerations derived from
Phase 138E as PPA-001 v1.0.

No pilot is authorized by this freeze. No pilot is designated by this
freeze. No pilot initiative is executed by this freeze. No provision of
GLP-001 is modified. No provision of GAC-001 is modified. No provision of
PGP-001 is modified. No governance behavior changes. No enforcement is
introduced. No production code is touched. Runtime remains Observed /
observe / unavailable.

## 20. Recommended next phase

**138G — Pilot Proposal & Authorization Contract Independent
Verification.**

Purpose: independently re-derive and verify PPA-001 v1.0 without trusting
Phase 138F. Confirm that every contractual obligation governing proposal,
eligibility review, authorization decisions, suspension, withdrawal,
governance independence, and traceability is justified, internally
consistent, compatible with GLP-001, GAC-001, and PGP-001, and introduces
no unsupported authority or governance expansion. No pilot authorization,
designation, execution, governance changes, or runtime modifications are
permitted.
