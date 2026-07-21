# Phase 138E — Advisory Pilot Authorization Architecture

## Status

Architecture only. This phase does not authorize a pilot, does not
designate a pilot, and does not execute a pilot. It defines only the
authorization *lifecycle* — the governed sequence by which a pilot
proposal may be reviewed and decided upon. No provision of GLP-001,
GAC-001, or PGP-001 is modified, reinterpreted, or extended; every
mechanism below is additive and strictly upstream of what those three
contracts already authorize. No production code touched. Runtime remained
Observed / observe / unavailable throughout.

## Objective

Design the governance architecture governing how an Advisory Governance
Pilot may be **proposed, reviewed, approved, rejected, deferred,
suspended, or cancelled** — a structured decision process that sits
immediately upstream of GAC-001 §6's already-frozen pilot-designation act
(GAC-REQ-017–025), so that when a real candidate eventually exists, the
question "should we even consider designating this candidate" is answered
through an evidence-driven, falsifiable procedure rather than an
undocumented, ad hoc judgment call.

This phase defines the authorization lifecycle only. It does not
authorize a pilot, does not designate a pilot, and does not execute a
pilot.

## Governing Authority

- GLP-001 v1.0 (`docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
  frozen by Phase 137W, independently verified by Phase 137X — VERIFIED
  WITH NON-BLOCKING FINDINGS)
- GAC-001 v1.0 (`docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`, frozen
  by Phase 137Z, independently verified by Phase 137ZA — VERIFIED WITH
  NON-BLOCKING FINDINGS) — the sole normative authority for GLP-001's own
  adoption progression, including pilot eligibility (§6), pilot execution
  (§7), independent assessment (§8), the governance decision (§9), and
  rollback (§10). This architecture operates strictly upstream of, and
  without narrowing, §6's designation act.
- PGP-001 v1.1 (`docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
  frozen by Phase 138B, revised by Phase 138C.1, independently verified by
  Phase 138C.2 — VERIFIED) — the sole normative authority for how an
  already-designated pilot is observed, evidenced, and assessed. This
  architecture does not duplicate or narrow PGP-001's observation (§7),
  evidence (§8), or assessment-preparation (§12) machinery; it governs a
  temporally earlier question (should the candidate be authorized to
  proceed toward designation at all).
- Phase 138D — Governance Framework Readiness Review & Pilot Readiness
  Assessment (`docs/PHASE_138D_GOVERNANCE_FRAMEWORK_READINESS_REVIEW.md`)
  — Decision: READY FOR PILOT AUTHORIZATION PLANNING. Treated as
  authoritative regarding framework maturity per this phase's own
  governing prompt; not re-derived or re-argued here.
- PFR-001 (`docs/specifications/PFR-001_CANONICAL_PHASE_REPORT_CONTRACT.md`)
- Existing PCAE governance, referenced only as an existing surface this
  architecture does not alter.

## Purpose

Design the governance process that controls **entry into the first
advisory pilot**. The architecture governs decisions about whether a
candidate may proceed toward pilot designation; it does not govern the
pilot's own execution once designated (that remains GAC-001 §7 and
PGP-001 §5–§13's territory) and it does not itself perform, or replace,
GAC-001 §6's designation act.

## Method

This phase does not re-derive GLP-001, GAC-001, PGP-001, or 138D's own
evidence. It treats their content as settled input and asks a question
none of them fully answers: **GAC-001 §6 already freezes an eligibility
test and states that designation "SHALL be an explicit human authority
decision" (GAC-REQ-023) — but it does not specify a *proposal format*, a
*review sequence*, a *set of intermediate decision outcomes* (defer,
request more evidence, suspend), or a *risk-review discipline* for
reaching that decision. This document supplies exactly that missing
layer, and no more of it.**

Three things are explicitly out of scope for re-derivation, cited rather
than re-argued:

1. **The eligibility test itself** — fully specified by GAC-001 §6.1–§6.2
   (GAC-REQ-018–019) and already operationalized into a checklist by
   PGP-001 §4.1–§4.2 (PGP-REQ-010–013). This document does not restate the
   eligibility criteria as new criteria; §2 below reuses PGP-001 §4
   verbatim as the eligibility-evidence component of the proposal package.
2. **Who may designate a pilot, and that designation is a human authority
   act** — fully specified by GAC-REQ-023. This document does not transfer,
   automate, or narrow that authority; §5 below explicitly defines
   "authorize planning" as permission to proceed toward the GAC-REQ-023
   designation act, not a substitute for it.
3. **What happens after a pilot is designated** — fully specified by
   GAC-001 §7–§10 and PGP-001 §5–§13. This document's boundary (§9) is
   drawn exactly at the point GAC-REQ-023's designation statement is
   written; everything after that point is out of scope here.

What this document adds, as genuinely new architectural content: a Pilot
Proposal Architecture (§2) — GAC-001 names required evidence categories
generically (§14) but does not define a candidate-facing proposal
document); an Eligibility Review Architecture (§3) that turns PGP-001
§4's checklist into a reviewer-facing question set; an Authorization
Review sequence (§4) — neither GLP-001 nor GAC-001 nor PGP-001 defines an
ordered review procedure preceding designation; a Decision Architecture
(§5) with five outcomes distinct from, and temporally prior to, GAC-001
§9's five Stage-6 outcomes; a Risk Review (§6) scoped to the authorization
decision itself, distinct from PGP-001 §11's pilot-evaluation bias
classes; a Pilot Boundary Architecture (§7); a Suspension and Withdrawal
Architecture (§8) for the authorization itself, distinct from GAC-001
§10's rollback of an already-designated pilot; and a Governance
Independence Architecture (§9) separating authorization authority from
every downstream role.

---

## 1. Authorization Philosophy

Every authorization decision under this architecture SHALL be:

- **evidence-driven** — a decision cites specific, checkable artifacts
  (file paths, phase IDs, requirement IDs), never an unattributed
  narrative claim, consistent with the citation discipline GLP-REQ-028,
  GAC-REQ-065, and PGP-REQ-034 already establish throughout the framework;
- **reversible** — no authorization decision is permanent or
  self-executing; every decision (§5) remains open to a later suspension,
  withdrawal, or re-review (§8) without requiring a contract revision;
- **explicit** — a decision is a recorded act with a stated rationale
  (§5), never inferred from silence, elapsed time, or accumulated informal
  momentum;
- **independent** — the reviewer(s) evaluating a proposal are not its
  proposer, mirroring GAC-REQ-035's existing requirement that a pilot's
  Stage 5 assessor be distinct from its participants, applied here one
  stage earlier (§9);
- **proportional** — the depth of authorization review scales with the
  candidate's own claimed applicability and blast radius (GLP-001 §7,
  GAC-REQ-008 item 2), never applied as uniform ceremony regardless of
  scope;
- **bounded** — authorization decides one thing only: whether the
  candidate may proceed toward GAC-001 §6 designation. It decides nothing
  about the candidate's own subsystem correctness, GLP-001's eventual
  wider adoption (GAC-001 §9), or any matter reserved to a later stage;
- **governance-neutral** — the authorization process itself takes no
  position on whether GLP-001 should ultimately be adopted, continued
  as advisory-only, revised, or rejected (GAC-001 §9); it only gates
  entry into planning, exactly as this document's own Purpose states.

**Authorization is permission to begin planning a pilot — not proof that
a pilot should occur.** An authorized candidate that later fails
GAC-001's own eligibility gate (§6.2), or that a human authority declines
to actually designate (GAC-REQ-023), has not thereby falsified this
architecture; authorization and designation remain two distinct,
independently reversible acts.

---

## 2. Pilot Proposal Architecture

A pilot proposal is the candidate-facing document a prospective sponsor
prepares before authorization review begins (§4). It is a new artifact
type this architecture introduces — GAC-001 §14 (GAC-REQ-064) names
evidence *categories* required before a Stage 6 decision, but nothing in
GLP-001, GAC-001, or PGP-001 defines a pre-designation proposal document.

### 2.1 Required proposal package contents

A pilot proposal SHALL contain each of the following nine components,
each independently checkable, none satisfied by narrative assertion
alone:

1. **Candidate rationale** — why this specific initiative is being
   proposed as a pilot candidate now, stated before any eligibility
   argument is made (mirrors PGP-REQ-013's ordering requirement: rationale
   first, eligibility argument second, never reversed to justify an
   already-favored candidate after the fact).
2. **Eligibility evidence** — the candidate's own answers to PGP-001
   §4.1's four-item suitability checklist (PGP-REQ-010: applicability,
   representative complexity, not-mid-flight, willing sponsor) and §4.2's
   exclusion pass (PGP-REQ-012), each answer citing a specific artifact or
   fact, not an assertion of qualification.
3. **Expected objectives** — what the pilot is intended to test about
   GLP-001 (per 138A's own Purpose: "validation, not adoption" — an
   objective phrased as "prove GLP-001 works" is malformed; "test whether
   GLP-001's four-stage core measurably reduces duplicated lifecycle
   decisions for this initiative" is well-formed).
4. **Success criteria** — stated in terms of PGP-001 §9's already-frozen
   success-metric table (PGP-REQ-038–041); the proposal does not invent
   new success metrics, it states which of PGP-001's seven mapped criteria
   the candidate expects to be most informative for its own shape.
5. **Failure criteria** — stated in terms of PGP-001 §10's already-frozen
   failure conditions (PGP-REQ-042–044); same reuse discipline as item 4.
6. **Scope** — the candidate's own stated boundary: which GLP-001 §5.1
   applicability criterion (or criteria) it claims to meet, and — per
   PGP-REQ-018 — an estimate of its own expected phase count, so the
   ceremony-to-blast-radius ratio (GAC-REQ-036 item 3) has a stated
   baseline before the pilot begins, not only a post-hoc count.
7. **Governance impact** — what, if anything, about existing PCAE
   governance, contracts, or lifecycle mechanics the candidate's own
   subsystem work touches, so the Governance Review step (§4.3) has a
   concrete starting point rather than a blank search.
8. **Risks** — the candidate's own disclosure of risks specific to its
   proposed subject matter, feeding into, but not replacing, the
   independent Risk Review (§6).
9. **Expected evidence** — which of PGP-001 §8.2's minimum evidence
   categories (architectural, contract, verification, governance
   observations, participant observations, metrics, lessons learned) the
   candidate expects to be able to produce, and which — if any — it
   anticipates being thin or unavailable, disclosed in advance rather than
   discovered during Stage 5 assessment (mirrors PGP-REQ-036's
   no-improvement-assumption rule, applied here to evidence
   *availability* rather than evidence *content*).

### 2.2 Proposal completeness rule

A proposal missing any of the nine §2.1 components is incomplete and
SHALL NOT proceed past the Authorization Review's first step (§4.1). This
is a structural, not a discretionary, gate — completeness is checked
before eligibility is evaluated, mirroring PGP-REQ-013's ordering
principle applied one layer earlier.

### 2.3 Reuse discipline

This section introduces no new evidence *artifact* beyond what PGP-001
§8 and GAC-001 §14 already define; it defines only the pre-designation
document that organizes a candidate's own claims about that evidence
before any of it has actually been produced. No pilot proposal, by
itself, constitutes pilot evidence under PGP-001 §8 — proposal content
becomes evidence only once the candidate is designated and its own
Architecture stage begins producing PGP-001-governed artifacts.

---

## 3. Eligibility Review Architecture

GAC-001 §6 already freezes the eligibility test as binding contract text,
and PGP-001 §4 already operationalizes it into a checklist. This section
adds nothing to that test; it defines how a reviewer — as distinct from
the proposer — evaluates the proposal's own §2.1 item 2 eligibility
evidence.

### 3.1 Mandatory review questions

For each of PGP-001 §4.1's four checklist items, the reviewer SHALL
answer the following, in order, recording the answer against the
proposal's own cited evidence:

1. **Applicability** — does the candidate's own cited evidence
   independently establish at least one GLP-001 §5.1 criterion, using
   only the artifact the proposal cites — not the proposal's own summary
   of that artifact? (Reject implicit qualification: a proposal that
   asserts "this is track-closing" without citing what tracks depend on
   it, or what makes it terminal, fails this question regardless of how
   plausible the assertion reads.)
2. **Representative complexity** — does the candidate's own stated phase
   count estimate (§2.1 item 6) place it credibly between the smallest
   technically-qualifying initiative and the repository's largest, using
   the reviewer's own independent comparison against the historical
   corpus (137V's own studied initiatives), not the proposal's own
   self-characterization?
3. **Not already mid-flight** — can the reviewer independently confirm,
   from `git log` or the candidate's own existing phase history, that no
   Architecture-stage document already exists for this initiative under an
   informal, undesignated pattern?
4. **Willing sponsor** — does the proposal name a specific human authority
   who has, in fact, agreed to designate the candidate and to accept its
   disclosed ceremony cost (§2.1 item 6) as a deliberate tradeoff, not
   merely a proposer's own hope that a sponsor will emerge later?

### 3.2 Objective-evidence requirement

Every §3.1 answer SHALL cite the specific artifact, file path, phase ID,
or named individual's own statement it is drawn from. An answer supported
only by the reviewer's own restatement of the proposal's own claim is not
an independent review — it is a re-reading, and SHALL NOT be recorded as
having satisfied this section. This mirrors GLP-001's own
re-derive/do-not-trust discipline (GLP-REQ-030 pattern), applied here to
the eligibility-review step specifically, and PGP-REQ-050's identical
requirement for Stage 5 assembly.

### 3.3 Rejection of implicit qualification

A candidate SHALL NOT be treated as eligible merely because no §3.1
question was answered "no" — every question SHALL be answered
affirmatively, with cited evidence, before eligibility is confirmed.
Silence, an unanswered question, or an answer of "presumably yes" is
equivalent to "no" for the purpose of this section. This is the direct
extension of PGP-REQ-013's ordering principle (checks applied *before*
selection) into a falsifiability requirement: an eligibility conclusion
not independently checkable against cited evidence is not a conclusion
this architecture recognizes.

### 3.4 Excluded-class fast check

Before §3.1's four questions are even applied, the reviewer SHALL confirm
the candidate does not fall into any of PGP-001 §4.2's five excluded
classes (PGP-REQ-012: emergency repairs, production hotfixes,
documentation corrections, repository maintenance, unrelated runtime
work). A candidate failing this fast check is rejected (§5) without
proceeding to §3.1.

---

## 4. Authorization Review

The review sequence a proposal moves through, in order, before any
decision (§5) is reached. No step may be skipped, and no step's
conclusion may be asserted rather than evaluated.

### 4.1 Step 1 — Proposal completeness

Confirm the proposal contains all nine §2.1 components. An incomplete
proposal is returned for completion (equivalent to "request additional
evidence," §5.4) before any further review step begins.

### 4.2 Step 2 — Eligibility confirmation

Apply §3's excluded-class fast check, then §3.1's four mandatory
questions. A candidate failing the fast check or any one of the four
questions does not proceed to Step 3.

### 4.3 Step 3 — Governance review

Using the proposal's own §2.1 item 7 (governance impact) disclosure as a
starting point, an independent reviewer confirms:

1. no requirement of GLP-001, GAC-001, or PGP-001 would be modified,
   reinterpreted, or narrowed by the candidate's proposed subject matter
   (mirrors GAC-REQ-006, PGP-REQ-007);
2. the candidate's proposed subject matter does not itself touch runtime
   execution capability (GAC-REQ-081; the candidate's own subject matter,
   as distinct from the fact that it happens to be a GLP-001 pilot, must
   independently respect Runtime remaining Observed / observe /
   unavailable);
3. no existing PCAE governance surface (a contract, `PROJECT_STATUS.md`,
   `CHANGELOG.md`, `.pcae/**` policy configuration) would need to change
   as a precondition of the candidate proceeding — if one would, that is
   itself a scope-boundary problem to be resolved before authorization,
   not during it.

### 4.4 Step 4 — Readiness confirmation

Confirm, independently, that Phase 138D's own readiness determination
(READY FOR PILOT AUTHORIZATION PLANNING) has not been superseded by any
later framework change — i.e., that GLP-001, GAC-001, and PGP-001 remain
in the same frozen/verified state 138D found them in (`docs/contracts/`
unchanged since 138D's own §10 validation, checkable by `git log` on
those three files). This step exists so that authorization review does
not silently rely on a readiness finding that may have gone stale between
138D and the review itself.

### 4.5 Step 5 — Authorization recommendation

Only after Steps 1–4 each independently conclude favorably does the
reviewer produce a recommendation for the Decision Architecture (§5). The
recommendation is advisory input to the decision, not the decision
itself — the two are kept distinct so that a human authority's actual
decision (§5) is never merely a rubber-stamp of the reviewer's own
recommendation without independent judgment.

**No automatic approval.** Completing Steps 1–4 favorably does not, by
itself, authorize anything. No accumulation of favorable review steps
SHALL cause an "authorize planning" outcome to occur automatically; §5
below requires an explicit, separate, recorded decision act, mirroring
GAC-REQ-043's and PGP-REQ-054's identical prohibition on automatic
adoption, applied here to authorization rather than adoption.

---

## 5. Decision Architecture

### 5.1 Permitted decisions

Following Authorization Review (§4), a human authority (or a delegate the
human authority explicitly names, per the pattern GAC-REQ-023 already
establishes for designation) SHALL select exactly one of the following
five outcomes. None is privileged by default; a proposal producing
unfavorable review findings is exactly as architecturally complete, by
this document's own standard, as one producing favorable findings
(mirrors GAC-REQ-042's identical non-preference statement for Stage 6,
and PGP-REQ-056's restatement of it).

1. **Authorize planning** — the candidate may proceed toward GAC-001 §6
   designation (GAC-REQ-023). This decision does not itself designate the
   candidate — designation remains a distinct, separate act the candidate's
   own future Architecture-stage document performs, per GAC-REQ-030.
   "Authorize planning" only removes this architecture's own gate; it
   supplies no new authority GAC-001 §6 does not already grant, and it
   does not shorten, waive, or pre-satisfy any GAC-001 §6 requirement.
2. **Defer** — the review is inconclusive or the candidate is
   plausible but not yet ready (e.g., Step 4's readiness confirmation
   finds the framework has changed since 138D and needs re-assessment
   before any candidate proceeds). Deferral names the specific condition
   that, once resolved, would allow re-review; it is not an indefinite
   non-answer.
3. **Reject** — the candidate fails §3's eligibility test, §4.3's
   governance review, or is independently judged disproportionate to its
   own disclosed scope (§2.1 item 6). Rejection is a final decision for
   this candidate in its current form; it does not preclude a materially
   different future proposal for the same underlying initiative.
4. **Request additional evidence** — Step 1 (completeness) or Step 2
   (eligibility) found the proposal's own citations insufficient to
   support a conclusion either way. This decision names the specific §2.1
   component or §3.1 question the proposal must strengthen before
   re-review.
5. **Suspend consideration** — authorization review has begun but an
   external condition (e.g., the named sponsor is no longer available, or
   the candidate's own scope has begun shifting before a decision is
   reached) makes reaching any of outcomes 1–4 premature. Suspension is
   distinct from deferral: deferral names a specific missing condition
   *for the review itself* to complete; suspension pauses the review
   because a precondition for reviewing at all has itself become unstable.

### 5.2 Explicit rationale requirement

Every decision, of every one of the five §5.1 outcomes, SHALL be recorded
with explicit rationale citing the specific Authorization Review step
(§4.1–§4.5) and proposal component (§2.1) it is based on. A decision
recorded without rationale, or with rationale that restates the outcome
rather than justifying it ("rejected because it was not authorized"), is
not compliant with this architecture.

### 5.3 Relationship to GAC-001 §9

This decision is distinct from, and temporally prior to, GAC-001 §9's
five Stage-6 outcomes (Adopt / Continue pilot / Continue advisory use /
Revise / Reject). GAC-001 §9 decides GLP-001's *wider* future after a
pilot has run and been assessed; this section decides only whether a
single candidate may *begin* that pilot process. "Authorize planning"
here has no relationship to, and does not predetermine, any future
GAC-001 §9 outcome for the resulting pilot.

---

## 6. Risk Review

Every authorization decision SHALL be preceded by an explicit assessment
of each of the following five risk categories. An assessment that skips
a category, or restates the category name without evaluating it against
the specific candidate, does not satisfy this section.

### 6.1 Governance risk

Does authorizing this candidate create any ambiguity about which contract
governs which decision (mirrors 138D §1's own "authority conflict" check,
applied prospectively to a specific candidate rather than retrospectively
to the framework as a whole)? Evaluated using §4.3's governance-review
findings.

### 6.2 Operational risk

Does the candidate's own disclosed scope (§2.1 item 6) and phase-count
estimate suggest ceremony that could stall, consume disproportionate
agent-hours, or block other governed work (mirrors PGP-REQ-042 item 2's
disproportionate-overhead failure condition, evaluated here before the
pilot begins rather than after).

### 6.3 Evidence risk

Does the candidate's own §2.1 item 9 (expected evidence) disclosure
suggest a real risk that PGP-001 §8.2's minimum evidence categories will
be thin or unavailable for this specific candidate — for instance, an
initiative too small to produce a meaningful Independent Verification
stage, or one whose Contract Freeze stage is expected to be trivial? A
candidate at high evidence risk is not automatically rejected, but the
risk SHALL be disclosed as part of the decision rationale (§5.2).

### 6.4 Bias risk

Does the proposal itself show signs of the pilot-bias pattern GAC-REQ-018
item 1 and GAC-REQ-022 already name — a candidate selected first and an
eligibility argument constructed afterward, contrary to §2.1 item 1's
required ordering (rationale, then eligibility evidence, never reversed)?
This category is evaluated at the authorization stage specifically
because it is the last point before a candidate accrues sunk-cost
momentum toward designation; PGP-001 §11's own bias-mitigation table
governs bias risk *during* an already-designated pilot's evaluation, a
later and different concern this section does not duplicate.

### 6.5 Scope risk

Does the candidate's own stated scope (§2.1 item 6) carry a plausible
risk of expanding past what its own proposal describes, once underway?
This anticipates PGP-REQ-022's own scope-expansion guard (which treats
post-designation scope growth as a rollback trigger under GAC-REQ-045
item 1) by asking the same question one stage earlier, when a narrower
or more precisely bounded initial scope statement is still cheap to
negotiate.

---

## 7. Pilot Boundary Architecture

Defines the boundaries an "authorize planning" decision (§5.1 item 1)
establishes for the candidate going forward.

### 7.1 Approved scope

The approved scope is exactly what the proposal's §2.1 item 6 (scope)
stated and the Authorization Review (§4) evaluated — no more. An
authorization decision SHALL name the specific GLP-001 §5.1 criterion (or
criteria) and the specific phase-count estimate it is approving; a
decision that authorizes "the candidate generally" without restating
this boundary is incomplete.

### 7.2 Prohibited expansion

Once authorized, the candidate's actual scope SHALL NOT exceed the §7.1
boundary without a fresh authorization decision. This mirrors PGP-REQ-022
one stage earlier: PGP-REQ-022 treats post-*designation* scope growth as
a GAC-001 rollback trigger; this section treats post-*authorization*,
pre-*designation* scope growth the same way — a candidate whose actual
Architecture-stage proposal (once written) differs materially from its
authorized §7.1 boundary requires renewed authorization review, not
silent absorption into an already-favorable decision.

### 7.3 Review checkpoints

An authorization decision remains valid only up to the candidate's own
GAC-001 §6 designation act (GAC-REQ-023). If a materially different
amount of time elapses between authorization and the candidate actually
being designated (no fixed calendar bound is imposed, consistent with
GAC-REQ-024's own refusal to impose one on pilot duration), the human
authority SHOULD re-confirm §4.4's readiness-confirmation step before
designation proceeds, since the framework's own frozen/verified state
(the exact thing 138D found ready) is itself checkable and could in
principle change between authorization and designation.

### 7.4 Termination conditions

An authorization terminates, without requiring a formal withdrawal
decision (§8), at the first of the following:

1. the candidate is actually designated under GAC-001 §6 (authorization
   has discharged its purpose — permission to proceed — and the candidate
   is now governed by GAC-001/PGP-001's own machinery instead);
2. the named sponsor (§2.1 item 6, §3.1 item 4) withdraws before
   designation occurs;
3. a §8 suspension or withdrawal decision is recorded.

---

## 8. Suspension and Withdrawal

Distinct from GAC-001 §10's rollback contract, which governs an
already-*designated* pilot. This section governs suspension or withdrawal
of an authorization that has not yet resulted in designation.

### 8.1 When authorization may be suspended

An "authorize planning" decision MAY be suspended when:

1. a Governance Review finding (§4.3) that was not present at the time of
   the original decision is later discovered — e.g., a subsequent
   contract revision to GLP-001, GAC-001, or PGP-001 changes the basis on
   which the original decision was made;
2. the candidate's actual pre-designation activity diverges materially
   from its §7.1 approved scope (§7.2);
3. the named sponsor becomes unavailable or withdraws support, short of a
   full withdrawal (§8.2) if the candidate's proposer believes a
   replacement sponsor may be found.

### 8.2 When authorization may be withdrawn or cancelled

An "authorize planning" decision MAY be withdrawn (by the authorizing
human authority) or cancelled (by the candidate's own proposer or
sponsor) when:

1. the candidate is no longer intended to proceed toward designation at
   all (proposer- or sponsor-initiated cancellation);
2. a suspension condition (§8.1) is not resolved within a period the
   authorizing human authority judges reasonable, converting suspension
   into withdrawal;
3. a Risk Review finding (§6) that was not adequately weighed in the
   original decision is identified on reconsideration.

### 8.3 Required justification

Every suspension, withdrawal, or cancellation SHALL be documented,
stating the specific §8.1 or §8.2 trigger that applies and citing the
original authorization decision (§5.2) it reverses or pauses. Silent
suspension or withdrawal — reversing a decision without recording why —
is prohibited, mirroring GAC-REQ-047's identical requirement for pilot
rollback, applied here to the earlier authorization decision.

### 8.4 Effect on evidence

A suspended, withdrawn, or cancelled authorization does not retroactively
invalidate any artifact the proposal or review process itself produced
(the proposal document, the review findings, the risk assessment). These
remain available, unmodified, as informative input to any future proposal
for the same or a related candidate, mirroring GAC-REQ-048's identical
evidence-preservation principle for rolled-back pilots.

---

## 9. Governance Independence

### 9.1 Separation from implementation

The authorization decision-maker (§5) SHALL NOT be the candidate's own
proposed Implementer (GLP-001 §8). Authorizing planning for one's own
implementation work is the same conflict GAC-REQ-035 already prohibits
for Stage 5 assessment, applied one stage earlier.

### 9.2 Separation from verification

The Authorization Review's independent reviewer (§4) SHALL NOT be the
candidate's own proposed Independent verifier (GLP-001 §8) for the same
candidate. This mirrors GAC-REQ-035's distinct-party requirement and
PGP-REQ-050's assembly-independence rule, applied at the authorization
stage.

### 9.3 Separation from pilot execution

Authorization decision-making authority is distinct from, and does not
transfer to, any role a designated pilot's own participants hold under
GLP-001 §8 or GAC-REQ-027. Authorizing a candidate confers no execution
role on the authorizer; it confers no participant role on the candidate's
own future Architecture, Contract Freeze, Implementation, or Independent
Verification authors either — those roles remain governed exactly as
GLP-001 §8 already assigns them, unaffected by who authorized entry into
planning.

### 9.4 Separation from outcome assessment

The authorization decision-maker (§5) SHALL NOT be the candidate's own
future Stage 5 independent assessor (GAC-001 §8, GAC-REQ-035) if and when
the candidate is later designated and runs a pilot. This prevents the
same party from both gating entry and grading the outcome, a conflict
none of GLP-001, GAC-001, or PGP-001 currently addresses because none of
them defines an authorization-stage role for this conflict to attach to
before now.

### 9.5 Decision authority distinct from pilot participation

No individual or role who authorized a candidate's planning (§5) may
subsequently claim that authorization as evidence of the candidate's
eventual pilot success, and no pilot participant may claim their own
participation as evidence that the original authorization was correct.
The two acts — authorizing entry, and succeeding once entered — remain
independently evaluable, mirroring GLP-001's own core principle
(GLP-REQ-030 pattern: an implementing phase's own report is not itself
evidence of correctness) applied to the relationship between
authorization and outcome.

---

## 10. Traceability

Every authorization requirement in this document SHALL trace to GLP-001,
GAC-001, PGP-001, or Phase 138D. This document introduces no
authorization rule that those four sources do not already support or
leave a specifically bounded gap for.

### 10.1 Traceability matrix

| §138E section | Governing basis | Relationship |
|---|---|---|
| §1 Authorization Philosophy | GAC-001 §4 (GAC-REQ-008–009); GLP-001 §7 | Restates existing adoption/proportionality principles, applied to a new decision point |
| §2 Pilot Proposal Architecture | GAC-001 §14 (GAC-REQ-064); PGP-001 §4 (PGP-REQ-010–013) | New: pre-designation proposal document; reuses existing eligibility/evidence-category content without altering it |
| §3 Eligibility Review Architecture | GAC-001 §6 (GAC-REQ-017–025); PGP-001 §4 (PGP-REQ-009–014) | Operationalizes an existing, already-operationalized checklist into a reviewer procedure; adds no criterion |
| §4 Authorization Review | GAC-REQ-023 (designation is a human authority decision); Phase 138D §6–§7 (readiness criteria, pilot preconditions) | New: ordered review sequence culminating in, but distinct from, GAC-REQ-023's designation act |
| §5 Decision Architecture | GAC-REQ-023; GAC-001 §9 (GAC-REQ-042, by contrast — distinct outcome set) | New: five authorization outcomes, explicitly distinguished from GAC-001 §9's five Stage-6 outcomes |
| §6 Risk Review | GAC-REQ-018 item 1 (pilot bias), GAC-REQ-069 (non-adoption conditions); PGP-001 §11 (bias, by contrast) | New: five risk categories scoped to the authorization decision, distinct from PGP-001's pilot-evaluation bias table |
| §7 Pilot Boundary Architecture | PGP-REQ-022 (scope-expansion guard, by extension); GAC-REQ-024 (duration) | Extends an existing post-designation guard to the pre-designation authorization period |
| §8 Suspension and Withdrawal | GAC-001 §10 (GAC-REQ-045–049, by extension) | Extends an existing post-designation rollback contract to the pre-designation authorization decision |
| §9 Governance Independence | GAC-REQ-035 (Stage 5 assessor independence, by extension); GLP-001 §8 (role responsibilities) | Extends existing role-separation principles to a newly-defined authorization role |
| §10 Traceability | Governing prompt | Self-referential completeness check |

GAC-001 §9's five Stage-6 outcomes and PGP-001 §11's bias-mitigation table
are cited above as **contrast**, not basis — this document's §5 and §6 are
new content addressing a different decision point and a different risk
scope, not restatements of those existing sections.

---

## 11. Deliverables

- **Advisory Pilot Authorization Architecture** — this document in its
  entirety.
- **Proposal Architecture** — §2.
- **Eligibility Review Architecture** — §3.
- **Decision Architecture** — §5.
- **Risk Review Architecture** — §6.
- **Boundary Architecture** — §7.
- **Suspension Architecture** — §8.
- **Traceability Matrix** — §10.1.

---

## 12. Validation

- **No pilot authorized**: §5.1 defines "authorize planning" as a future,
  candidate-specific decision this document does not itself make; no
  candidate is named, evaluated, or authorized anywhere in this document.
- **No pilot designated**: §5.3 explicitly distinguishes authorization
  from GAC-001 §6/§9 designation and decision acts; neither occurs here.
- **No pilot executed**: this document governs a pre-designation decision
  process only; no pilot activity occurs as a result of this phase.
- **No governance changed**: no provision of GLP-001, GAC-001, or PGP-001
  is modified — every citation above is read-only reuse of already-frozen
  text; `git diff` confirms zero changes to any file under
  `docs/contracts/`.
- **Compatibility preserved**: §10's traceability matrix confirms every
  requirement here either operationalizes existing frozen text (§2, §3) or
  fills a specifically bounded, previously-unaddressed gap (§4–§9) without
  narrowing, reweighting, or contradicting any existing `GLP-REQ-*`,
  `GAC-REQ-*`, or `PGP-REQ-*` obligation.
- **Runtime unchanged**: Observed / observe / unavailable, confirmed via
  `pcae runtime inspect` before and unaffected by this phase's work.

---

## 13. No-Go

This phase did not, and does not authorize any future phase acting solely
on this document's authority to:

- No pilot was authorized by this phase.
- No pilot was designated by this phase.
- No pilot was executed by this phase.
- No provision of GLP-001 was modified by this phase.
- No provision of GAC-001 was modified by this phase.
- No provision of PGP-001 was modified by this phase.
- No governance rule was changed by this phase.
- No runtime functionality was added by this phase.
- No production code was modified by this phase.
- No new compliance-checking apparatus, tool, or role was introduced by
  this phase beyond the review procedure defined in §3–§4, which reuses
  existing PGP-001/GAC-001 checklist content and existing PFR-001-
  conformant reporting exclusively.

Architecture only.

---

## 14. Success Criteria

This phase succeeds only if, and this document confirms, each of the
following holds:

- **The authorization lifecycle is fully specified** — §2 (proposal) →
  §3 (eligibility review) → §4 (authorization review sequence) → §5
  (decision) → §7 (boundary) → §8 (suspension/withdrawal) form a complete,
  ordered lifecycle with no undefined transition.
- **Decision responsibilities are explicit** — §5.2 requires rationale for
  every decision; §9 assigns and separates every relevant role.
- **Pilot entry remains evidence-based** — §2.1's nine-component proposal
  package and §3.2's objective-evidence requirement together prohibit an
  authorization decision resting on unattributed narrative claims.
- **Governance independence is preserved** — §9's five subsections
  separate authorization authority from implementation, verification,
  pilot execution, and outcome assessment.
- **No authorization is granted** — confirmed at §12 and §13.
- **Runtime remains unchanged** — confirmed at §12.

---

## 15. Recommended Next Phase

**138F — Advisory Pilot Authorization Contract Freeze (PPA-001 v1.0)**,
per the governing prompt's own recommendation, if the human authority
elects to proceed. Purpose: transform this document's Pilot Proposal
Architecture (§2), Eligibility Review Architecture (§3), Authorization
Review (§4), Decision Architecture (§5), Risk Review (§6), Pilot Boundary
Architecture (§7), Suspension and Withdrawal Architecture (§8), and
Governance Independence Architecture (§9) into a small number of binding,
falsifiable obligations — analogous to how Phase 138B froze Phase 138A's
evaluation architecture into PGP-001 — while explicitly preserving
GLP-001, GAC-001, and PGP-001's existing text unchanged. No pilot
authorization or execution is permitted during 138F if commissioned; none
is permitted or performed by this phase.
