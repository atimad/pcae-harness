# PFR-001 — Canonical Phase Report Specification

## 1. Purpose

Every architectural contract, verification methodology, and runtime
governance rule in PCAE is now itself governed by an explicit written
specification — except the phase report, the single artifact that
carries all of that governance work outward to an operator, to future
phases, and to the historical record. Phase report *content* has so
far been convention only: each phase produced a report that looked
roughly like its predecessors because the prompt for that phase said
so, not because a specification defined it. Recent phases (through
Track 132) demonstrate this drift concretely — engineering quality
stayed high while report structure, section coverage, and level of
detail varied phase to phase, driven by prompt wording rather than a
binding contract.

**PFR-001** closes this gap: it is the first canonical specification
governing what every PCAE phase report shall contain, independent of
which phase produced it or how that phase's own prompt was worded.

This phase (133A) is architecture-only. It defines PFR-001. It does
not implement it, does not modify report-generation code, and does not
modify PFN-001.

## 2. Why a Report Specification Is Necessary Now

- **Reports are no longer disposable status text.** They serve as
  operator communication (mobile notification, PFN-001), historical
  engineering evidence (the only durable record of what a phase
  actually did, once the chat that produced it is gone), architectural
  traceability (which contract clause a phase satisfied, which
  boundary it preserved), verification evidence (what was
  independently re-derived, not merely asserted), and project audit
  history (`.pcae/phase-reports/`, `PROJECT_STATUS.md`,
  `CHANGELOG.md`).
- **Six report types already coexist informally**: architecture
  reports, contract-freeze reports, contract-verification reports,
  prototype-plan reports, prototype-implementation reports, and
  independent-verification reports (Sections 131A-131F, 132A-132F are
  direct precedent for all six). Each type currently improvises its
  own section list from the immediately preceding phase's own
  document, with no shared specification to converge on.
  Section 9 below defines how PFR-001 relates to phase-class
  variation.
- **A report shall remain understandable months later without
  requiring the original chat** (Section 14). This is only achievable
  if every report, regardless of phase or author, contains the same
  minimum structure — an operator (or a future phase) who has never
  seen the originating conversation must still be able to reconstruct
  what happened, why it mattered, and what remains true or false about
  the system as a result.

## 3. Position within PCAE Governance

PFR-001 sits alongside, not beneath, the architectural contracts it
describes:

- It governs the **document produced at the end of every governed
  phase** — the same phase lifecycle (architecture, contract freeze,
  contract verification, prototype plan, prototype implementation,
  independent verification) every track since 119 has followed.
- It does not govern any track's own subject matter (Repository
  Intelligence, Unified Query, the Repository Intelligence Service,
  runtime governance, or any future track) — a report about Track 132
  still reports on Track 132's own architecture; PFR-001 only
  constrains the *shape* of that reporting, never its *content*.
- It is authored the same way every other architectural specification
  in this lineage has been: a dedicated architecture phase (133A),
  followed in the same governed lifecycle by a contract freeze (133B)
  and independent contract verification (133C), per Section 16.

## 4. Relationship to PFN-001

**PFN-001 governs delivery. PFR-001 governs content. The two
specifications are intentionally independent.**

- PFN-001 (`docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`
  Section 4): *"Every terminal phase outcome shall produce exactly one
  trusted canonical phase report delivered to the configured
  notification sink. Notification delivery — or an explicit, durable
  delivery-failure record — is a mandatory component of governed phase
  finalization. Silent notification omission is prohibited."* PFN-001
  answers **whether** a report reaches the operator and **how many**
  times.
- PFR-001 answers **what the report says** once it exists — the
  section structure and content obligations a phase report must
  satisfy before it is fit to be the "trusted canonical phase report"
  PFN-001 already requires to exist and be delivered.
- **Neither weakens the other.** A report can satisfy PFN-001's
  delivery guarantee while still being a poor report under PFR-001 (a
  vague summary, a missing verification section) — that gap is exactly
  the "gradual report drift" this phase's own Context describes.
  Conversely, a PFR-001-conformant report is not itself notified
  unless PFN-001's own delivery machinery runs; PFR-001 does not touch
  dispatch, sinks, retries, or failure-recording, all of which remain
  entirely PFN-001's concern (PFN-001 Sections 7-9).
- **This phase does not modify PFN-001's own contract text.** PFN-001
  Section 4's invariant is restated here for reference only, not
  amended.

## 5. Canonical Report Structure — The Twelve Required Sections

Every phase report shall contain all twelve of the following sections,
by content, not necessarily under these exact headings (a report may
use phase-specific section numbering and titles, matching the existing
precedent in 131A-132F's own documents, provided each of the twelve
obligations below is satisfiably present somewhere in the document).
Section 9 defines which sections may be answered with an explicit
"not applicable to this phase class" statement rather than substantive
content, and under what conditions.

### 5.1 Phase Identity

Mandatory, always fully populated:

- Phase ID
- Status
- Report completeness
- Files changed
- Tests executed
- Commits
- Push status
- Repository state (clean/dirty, `origin/main..HEAD` count)

This section corresponds directly to the trust-critical and
non-fatal trust fields the canonical report artifact already carries
(`src/pcae/core/phase_reports.py`'s `PhaseReport` dataclass:
`phase_id`, `phase_name`, `status`, `summary`, `files_changed`,
`tests_run`, `commits`, `pushed_status`, `origin_main_head_count`,
`report_completeness`) — PFR-001 does not introduce new fields here;
it makes explicit, as a content obligation, that a phase report's
prose must state these facts plainly, not merely leave them to be
inferred from the trust-assessment JSON sitting beside it.

### 5.2 Executive Summary

A concise but complete summary describing:

- objective
- major result
- architectural significance
- important discoveries
- implementation status
- verification outcome
- runtime impact

**Avoid vague summaries.** A summary that says "the phase was
completed successfully" without stating what was built, decided, or
found fails this section. A conforming summary states the concrete
result in the same sentence as the claim of success (precedent:
131F's own summary — "one BLOCKING defect was found and repaired... a
one-line fix" — not merely "verification passed").

### 5.3 Architectural Findings

Applicable to architecture, contract, planning, implementation, and
verification phases (Section 9 governs which phase classes this
section is mandatory for). Describes:

- architectural decisions
- contracts established
- boundaries preserved
- new architectural knowledge
- interactions with previous tracks

### 5.4 Implementation Findings

When applicable, describes:

- implementation strategy
- important implementation choices
- reuse of existing architecture
- deterministic guarantees
- compatibility
- preserved invariants

**Documentation-only phases explicitly state that no implementation
occurred** — this is itself the required content for this section on
such phases, not an omission of the section. (This phase, 133A, is
itself such a phase — see Section 12.)

### 5.5 Verification Findings

Verification phases shall document:

- methodology
- independently re-derived evidence
- dimensions verified
- BLOCKING findings
- NON-BLOCKING findings
- repaired defects
- remaining observations

**Verification shall never simply report "verified."** It shall
explain what was independently confirmed — precedent: 131F Section 1's
own methodology statement ("Re-derive. Never trust the implementation
simply because it exists"), 132F's eight fresh silent-omission probes
each individually documented with their own concrete result, not
summarized as a single "silent omission: none found" line.

### 5.6 Technical Debt Review

Re-evaluates inherited technical debt:

- reviewed items
- classification
- changes in status
- newly discovered debt
- repairs performed
- repairs intentionally deferred

Precedent: the Change Impact (123)/Advisory Context (122)
schema-vs-real-generator-output divergence, independently re-confirmed
and re-classified NON-BLOCKING in every verification phase since 131C
— this is exactly the discipline this section makes a permanent,
named obligation rather than an ad hoc habit.

### 5.7 Governance Results

Mandatory, always fully populated:

- `pcae_health`
- `pcae_check`
- `doctor` (task-memory)
- `push check`
- `runtime inspection`
- `notification status`

This maps directly to `_REQUIRED_GOVERNANCE_KEYS` in
`src/pcae/core/phase_reports.py`
(`pcae_health`, `pcae_check`, `pcae_doctor_task_memory`,
`pcae_push_check`, `telegram_runtime`) plus the runtime-inspection
result these keys do not yet separately capture — PFR-001 requires the
report's own prose to state each result explicitly, not merely rely on
the trust-assessment JSON's own key/value pairs being present.

### 5.8 Test Results

Documents:

- executed suites
- regression coverage
- fast_green
- compile verification
- dedicated tests
- verification probes

**Summarize significant coverage** — total counts (e.g. "179 combined
regression tests, 4390-test fast_green") plus what those counts
actually cover (which tracks' suites, which new dedicated tests), not
a bare pass/fail flag.

### 5.9 No-Go Confirmation

Explicitly confirms prohibited capabilities remain absent. Examples:

- execution
- reasoning
- inference
- schema modification
- runtime expansion
- unauthorized architectural change

This is a **confirmation of absence**, stated affirmatively — "no
execution capability was introduced," not silence on the topic.
Precedent: every 13xA architecture doc's own "Strict Non-Goals"
section, and every verification phase's own "Confirmations" section
(e.g. 132F Section 18).

### 5.10 Architectural Boundary Confirmation

Confirms preserved boundaries. Examples:

- authority
- determinism
- provenance
- evidence
- execution boundary
- governance boundary

Distinct from Section 5.9: No-Go Confirmation states what capability
was *not added*; Architectural Boundary Confirmation states what
existing structural guarantee was *not weakened* — a phase can
introduce zero new capability (satisfying 5.9) while still, in
principle, eroding an existing boundary (e.g. weakening a provenance
guarantee without adding new authority) — the two confirmations are
independent and both mandatory.

### 5.11 Track Progress

States clearly:

- phase completion
- track status
- chapter status
- overall architectural significance

**This section shall explain what the completed phase means within
PCAE** — not merely that it finished, but what its completion changes
about the state of the system (precedent: 131F Section 21's "Overall
Track 131 Completion Assessment," 132F Section 20's equivalent).

### 5.12 Next Phase

Provides:

- recommended next phase
- rationale
- readiness assessment

**If no recommendation exists, explicitly state why** — e.g. a
verification phase's own governing instruction not to begin the next
track automatically (precedent: 131F Section 22, 132F Section 21, both
of which state a next-chapter *context* without a binding
recommendation, and both explain why: the phase spec itself forbids
starting the next track).

## 6. Content Governance, Not Formatting Governance

**The specification governs content rather than formatting.** PFR-001
does not mandate:

- exact heading text or numbering scheme (a report may number sections
  1-23 as 131F/132F's own documents do, or use any other consistent
  scheme, provided all twelve content obligations are met);
- exact section ordering (though the order in Section 5 is
  recommended as the default, matching existing precedent);
- markdown vs. any other document format;
- exact prose length — Section 14's "concise without omitting
  engineering evidence" principle governs length, not a word count.

What PFR-001 does mandate is that all twelve obligations are
**satisfiably present as content** somewhere in the document, in a
form a reader could locate and act on without needing the original
authoring conversation.

## 7. Report Quality Principles

Every phase report shall be:

- **historically useful** — legible and load-bearing to a reader
  encountering it for the first time, long after the phase completed;
- **technically complete** — every claim traceable to a concrete
  mechanism, file, test, or command, not an unsupported assertion;
- **operator focused** — written for a human deciding what to do next,
  not merely for an internal audit trail;
- **concise without omitting engineering evidence** — brevity is a
  virtue only until it starts hiding the evidence a claim depends on;
- **deterministic** — two independent authors given the same
  underlying phase evidence should produce reports that agree on every
  fact, even if their prose differs;
- **self-contained** — Section 14 restates this as the governing test.

## 8. Applicability

PFR-001 applies to every governed phase class currently in use across
PCAE's phase lifecycle:

- architecture phases
- contract phases (freeze and verification)
- planning phases (prototype plan)
- implementation phases (prototype implementation)
- review phases
- hardening phases

**The specification may define optional sections for different phase
classes while preserving one canonical structure.** Section 9 defines
this precisely: the twelve sections in Section 5 are the fixed,
canonical structure; individual phase classes determine which sections
carry substantive content versus an explicit "not applicable" statement,
never whether a section may be silently omitted.

## 9. Applicability by Phase Class

| Section | Architecture | Contract Freeze | Contract Verification | Prototype Plan | Prototype Implementation | Independent Verification |
|---|---|---|---|---|---|---|
| 5.1 Phase Identity | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.2 Executive Summary | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.3 Architectural Findings | mandatory | mandatory | mandatory | mandatory | mandatory (as reused/inherited architecture) | mandatory (as re-derived conformance) |
| 5.4 Implementation Findings | "no implementation occurred" | "no implementation occurred" | "no implementation occurred" | "no implementation occurred" (a plan, not code) | mandatory | mandatory (re-derived, not implemented by this phase) |
| 5.5 Verification Findings | not applicable, state why | not applicable, state why | mandatory | not applicable, state why | mandatory (regression evidence) | mandatory (primary content) |
| 5.6 Technical Debt Review | mandatory (inherited items) | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.7 Governance Results | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.8 Test Results | mandatory (may be "no new tests, doc-only") | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.9 No-Go Confirmation | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.10 Architectural Boundary Confirmation | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.11 Track Progress | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory |
| 5.12 Next Phase | mandatory | mandatory | mandatory | mandatory | mandatory | mandatory (may be non-binding context only, per phase instruction) |

A cell reading "not applicable, state why" is itself a mandatory
content obligation — the section is never silently absent; it
explicitly states that the phase class does not produce that content
and briefly why (e.g. an architecture phase performs no independent
verification of prior work, so Section 5.5 states this directly rather
than being omitted).

## 10. Relationship to Existing Report Precedent

This specification does not invalidate any report produced before
133A. 131A-131F and 132A-132F, read against Section 5's twelve
obligations, already satisfy PFR-001 in substance — they were the
precedent this specification generalizes from, not a body of work this
specification retroactively invalidates. PFR-001's purpose is to make
that already-good practice a binding, named contract instead of an
unstated convention that could quietly erode, exactly as this phase's
own Context describes having begun to happen.

## 11. Future Specification Family

PFR-001 is the first of a reserved family of Phase Finalization Report
specifications:

- **PFR-001** — Canonical Phase Report (this specification)
- **PFR-002** — Milestone Report (reserved, not defined)
- **PFR-003** — Release Report (reserved, not defined)
- **PFR-004** — Verification Report (reserved, not defined)
- Future PFR specifications, numbered sequentially as needed

**No additional PFR specification is created or defined during this
phase.** These identifiers are reserved to prevent numbering
collisions in future tracks, not scoped, drafted, or committed to in
any way beyond their name and a one-line placeholder purpose above.

## 12. Confirmation: No Implementation Occurred

This phase produces only this specification document and the standard
governance-doc updates (`PROJECT_STATUS.md`, `CHANGELOG.md`,
`tasks/DONE.md`, the active task contract). Specifically, this phase:

- does **not** modify `src/pcae/core/phase_reports.py` or any other
  report-generation code;
- does **not** modify any notification code
  (`src/pcae/core/notification_certification.py` or any Telegram/sink
  implementation);
- does **not** modify PFN-001's own contract text
  (`docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`);
- does **not** introduce a report template into implementation code —
  PFR-001 is a content specification for human/agent authors to write
  against, not a rendering template consumed by code;
- does **not** alter Repository Intelligence, Unified Query, the
  Repository Intelligence Service, or any other track's own subject
  matter;
- does **not** alter governance behavior of any kind.

**Confirmed via `git diff --stat`: zero `src/` files touched by this
phase.**

## 13. Confirmation: Runtime Behavior Unchanged

- Runtime state: `Observed` (unchanged).
- Maximum plugin capability: `observe` (unchanged).
- Execution availability: `unavailable` (unchanged).

This phase introduces a documentation specification only; it grants no
new capability of any kind and does not touch
`src/pcae/core/runtime_context.py` or any runtime-governing module.

## 14. Self-Containment Test

A report shall remain understandable months later without requiring
the original chat. This is the practical test for whether a given
report satisfies PFR-001: a reader with no memory of the originating
conversation, given only the report and read access to the repository
at the commit it describes, must be able to answer, from the report
alone:

- what changed, and why it was done;
- what was verified, and how (not merely that it was);
- what remains true or false about the system's boundaries as a
  result;
- what should happen next, and why (or why nothing is recommended).

## 15. Strict Non-Goals

This phase does not:

- modify report generation code;
- modify notification code;
- modify PFN-001;
- introduce templates into implementation;
- change runtime behavior;
- alter Repository Intelligence;
- alter governance behavior.

This phase creates only the governing specification (Section 5) and
its applicability rules (Section 9).

## 16. Track 133 Roadmap

PFR-001's own governed lifecycle mirrors every prior architectural
specification in this repository:

- **133A** — PFR-001 Canonical Phase Report Specification (this
  phase) — architecture only.
- **133B** — PFR-001 Contract Freeze — converts this architecture into
  a frozen, clause-by-clause binding contract (mirroring 131A→131B,
  132A→132B).
- **133C** (anticipated, not committed to by this phase) — PFR-001
  Contract Verification, independently re-deriving 133B's contract
  against this architecture and real precedent reports, per the same
  "re-derive, never trust" discipline this specification itself
  documents in Section 5.5.

This phase does not commit to phases beyond 133B; per this phase's own
governing instruction, it stops after 133A.

## 17. Governance

- Repository remains clean, pushed, `origin/main..HEAD = 0`.
- Runtime remains `Observed`, execution unavailable (Section 13).
- PFN-001 remains mandatory and unmodified (Section 4).

## 18. Confirmations

- No implementation changes occurred (Section 12).
- No runtime behavior changed (Section 13).
- PFN-001 is unchanged; PFR-001 is a new, independent, content-only
  specification (Section 4).
- No additional PFR specification beyond PFR-001 was defined (Section
  11).

## 19. Conclusion

PFR-001 establishes the first canonical specification governing PCAE
phase report content, closing the gap between PCAE's mature
architectural, verification, and runtime governance and its
previously convention-only reporting standard. It defines twelve
mandatory content obligations (Section 5), governs content rather than
formatting (Section 6), states explicit applicability rules across six
existing phase classes (Section 9), and cleanly separates itself from
PFN-001's delivery guarantee (Section 4) without amending it. It
reserves, but does not define, a future PFR family (Section 11). This
phase makes no implementation change and no runtime change.

Recommended next phase: **133B — PFR-001 Contract Freeze.**
