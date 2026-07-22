# Phase 139F — Controlled Advisory Pilot Execution

**Status:** Complete (GLP-001 Stage 1 — Architecture, for `GLP-PILOT-C6`;
no Contract Freeze, Implementation, or Independent Verification performed
by this phase)
**Mode:** First governed execution phase of the designated Advisory Pilot,
under GAC-001 §7 (Pilot Execution Contract)
**Governing authority:** GLP-001 v1.0, GAC-001 v1.0 §7, PGP-001 v1.1,
PPA-001 v1.0, Phase 139D Authorization Decision, Phase 139E Designation
(`docs/PHASE_139E_ADVISORY_PILOT_DESIGNATION.md`), existing PCAE
governance, PFR-001
**Runtime:** Observed / observe / unavailable (unchanged by this phase)

## 0. GLP-001 Designation Rationale (GAC-REQ-030 restatement)

Per GAC-REQ-030, this Architecture-stage phase report restates the
designation and its GLP-001 §5.1 rationale in its own Governing Authority
/ Objective section. `GLP-PILOT-C6` (External Packaging / Release
Hardening) was designated in Phase 139E under GAC-001 §6, on the
authorization of Phase 139D, claiming GLP-001 §5.1 criterion 1 (it
introduces a new binding technical contract — a release/versioning policy
every future release will depend on) and criterion 3 (it is track-closing
— the terminal phase group for Production v1's external distribution
readiness). This restatement does not re-derive or re-litigate the
designation; per 139E §7, it is complementary to, not a substitute for,
139E's own designation record.

## 1. Purpose and Boundary

This phase conducts the first governed activity of `GLP-PILOT-C6`:
GLP-001 §6.1 **Stage 1 — Architecture**, applied to the pilot's approved
scope (139E §4): a release/versioning policy, PyPI packaging design, and
manual release-checksum verification. Per GLP-REQ-016, Contract Freeze
(Stage 2) SHALL NOT begin before this Architecture stage produces a
stable design; this phase produces that design and stops there.

Per GAC-001 §7 (GAC-REQ-033), this contract governs only that the stage
occurs, in order, with GLP-001 §9's required evidence — it provides no
implementation guidance. Consistent with the phase's own governing
instruction ("Runtime shall remain: State Observed, Maximum Capability
observe, Execution Availability unavailable" and "The pilot does not
validate runtime capability"), this phase produces a **design document
only**. No `pyproject.toml` edit, no CI workflow file, no packaging
command, and no checksum-generation command was run. Architecture-stage
outputs are, by GLP-001 §6.1's own definition, a design document — not
code, not a frozen contract, and explicitly not a verdict.

This phase SHALL NOT, and does not:

- perform Contract Freeze, Implementation, or Independent Verification
  (Stages 2–4) — those are separate, future phases;
- execute any packaging, build, publish, or checksum command;
- modify governance (`docs/contracts/**`, `.pcae/**` policy
  configuration);
- modify runtime (`src/pcae/**`);
- touch Docker, Homebrew, CI release signing, or migration tooling
  (139E §4 exclusions);
- change runtime capability. Runtime remains Observed / observe /
  unavailable throughout.

## 2. Scope Enforcement

Every activity below is checked against 139D §9.2 / 139E §4's approved
scope before being performed. No activity outside that scope was
attempted.

| Approved scope element (139E §4) | Addressed by this phase? | How |
|---|---|---|
| Release/versioning policy Contract Freeze deliverable | Not yet — this phase performs Architecture (§6.1 Stage 1), the stage that precedes Contract Freeze | §3.1 below establishes the design this future contract will freeze |
| PyPI packaging: build configuration and publish workflow design | Yes — Architecture-level design only | §3.2 below |
| Manual release-checksum verification | Yes — Architecture-level design only | §3.3 below |
| GLP-001 §6.1 core stages applied to items 1–3 | Stage 1 only, this phase | §3 below |

Explicitly prohibited and confirmed not performed:

- Docker work — none. No `Dockerfile` was created or referenced as a
  deliverable.
- Homebrew work — none. No formula was created or referenced.
- CI release signing — none. §3.2 below explicitly designs a *manual*
  publish step, not CI-enforced signing.
- Migration tooling — none.
- Scope expansion — none. §2 above traces every element of this phase's
  work back to 139E §4 with no addition.

No scope-expansion trigger fired; the pilot was not terminated.

## 3. Pilot Activities — Architecture Stage Design Document

### 3.1 Release/versioning policy — architecture

**Objective:** establish the scope, primitives, and non-goals of a
release/versioning policy, ahead of a future Contract Freeze phase that
converts this design into binding `SHALL`/`SHALL NOT` obligations.

**Current state (verified this phase, not assumed):** `pyproject.toml`
declares `version = "0.2.0"` under `[project]`, with no companion
versioning-policy document anywhere in `docs/` or `docs/contracts/`.
`git log --all` shows no prior release/versioning policy contract.

**Primitives identified:**

- A single authoritative version field (`pyproject.toml`'s `[project]
  version`), not a duplicated version string elsewhere in the tree.
- A version-bump discipline (the specific scheme — e.g. Semantic
  Versioning — is a Contract Freeze decision, not decided by this
  Architecture stage, consistent with GLP-001 §6.1 Stage 1's own
  boundary: architecture states scope and primitives, not the frozen
  obligations themselves).
- A release-trigger definition: what repository event (tag, manual
  dispatch, phase-driven decision) constitutes "cut a release," scoped
  to human-authority action only, consistent with runtime remaining
  Observed / observe / unavailable — no automated, unattended release
  trigger is in scope.

**Non-goals (explicit, per GLP-001 §6.1 Stage 1's required output):**

- This Architecture stage does not select a specific versioning scheme
  (e.g., SemVer vs. CalVer) — that choice, with its rationale, belongs
  to the future Contract Freeze stage.
- It does not define a changelog format or enforcement mechanism.
- It does not touch `docs/contracts/**` or freeze any obligation — no
  file under that path was created or modified by this phase.

**Alternatives considered (GLP-001 §6.1 Stage 1 evidence expectation —
architectural rationale, including alternatives considered):**

1. *Defer the versioning-policy question entirely to the packaging
   Contract Freeze stage, folding it into a single combined contract.*
   Considered and not selected for this Architecture record: 139E §4
   lists the release/versioning policy as its own included activity,
   distinct from PyPI packaging; keeping them as separately traceable
   Architecture-stage subsections (§3.1 vs. §3.2 here) preserves that
   distinction for the future Contract Freeze phase, rather than
   collapsing two of 139B §3.1's four listed items into one.
2. *Adopt an existing external versioning standard by reference only
   (e.g., "we follow SemVer 2.0.0"), with no repository-local
   elaboration.* Considered; a bare external reference does not by
   itself establish a release-trigger or a single-source-of-truth
   primitive, both of which are unresolved in the current repository
   state (no policy document exists at all). Rejected as insufficient
   for this Architecture stage's own "explicit scope boundaries"
   requirement.

### 3.2 PyPI packaging — architecture

**Objective:** establish scope, primitives, and non-goals for PyPI build
configuration and publish workflow, ahead of Contract Freeze.

**Current state (verified this phase):** `[build-system]` in
`pyproject.toml` already declares `hatchling` as the build backend, and
`[tool.hatch.build.targets.wheel]` already scopes the wheel to
`src/pcae`, with a documented rationale (Phase 106D comment, in-file)
for restricting sdist scope after a prior over-inclusion defect. No
PyPI-publish CI workflow exists (`.github/workflows/` contains only
`pcae-governance.yml`); no `twine` or equivalent publish step exists
anywhere in the tree (verified via `find .github -iname "*.yml"` and a
grep of workflow content this session).

**Primitives identified:**

- A build step, producing a wheel and sdist from the existing hatchling
  configuration — no new build backend is proposed; the existing choice
  is treated as an accepted precondition, not reopened.
- A **manual** publish step (human-invoked `twine upload` or equivalent),
  consistent with 139E §4's exclusion of "signed releases / checksum
  verification in CI" — automated, unattended publish-on-tag is
  explicitly out of scope for this pilot's first iteration.
- A publish-target primitive (which package index — PyPI itself, or a
  TestPyPI rehearsal step first) — the specific target sequencing is a
  Contract Freeze decision.

**Non-goals (explicit):**

- No CI workflow file is designed or created by this phase. "Publish
  workflow design" (139B §3.1 item 2) is architecture-level scope
  description only; the concrete workflow (if any) is Implementation
  stage (Stage 3) work, gated behind Contract Freeze.
- No package was built, and no build command was executed — runtime
  Execution Availability is `unavailable`; this phase performed no
  tooling invocation.
- No credential, token, or publish-target configuration was created or
  referenced.

**Alternatives considered:**

1. *Switch build backends (e.g., to `setuptools` or `poetry-core`)
   instead of retaining `hatchling`.* Considered; rejected for this
   Architecture record — the existing `hatchling` configuration is
   already in place, already scoped correctly (per the in-file Phase
   106D rationale), and re-litigating the build-backend choice is
   outside 139E §4's approved scope, which names "PyPI packaging: build
   configuration and publish workflow design," not build-backend
   selection.
2. *Design a fully automated (CI-triggered) publish workflow now, since
   a workflow file already exists for governance (`pcae-governance.yml`)
   and the pattern is familiar.* Rejected: 139E §4 explicitly excludes
   "signed releases / checksums-in-CI," and CI-triggered publish
   without human confirmation would blur into that excluded category.
   The manual-publish primitive above was chosen specifically to keep
   this pilot's first iteration inside the authorized boundary.

### 3.3 Manual release-checksum verification — architecture

**Objective:** establish scope, primitives, and non-goals for a manual
(not CI-enforced) checksum-verification procedure.

**Primitives identified:**

- A checksum-generation step over the built artifact(s) (wheel, sdist),
  using a standard, widely available digest (e.g., SHA-256) — the
  specific algorithm choice is a Contract Freeze decision, not fixed
  here.
- A manual confirmation step: a human authority compares the generated
  checksum against the artifact retrieved from the publish target,
  before treating the release as verified.
- Explicitly **not** an automated CI gate — 139E §4 excludes "signed
  releases / checksum verification in CI"; this primitive is scoped to
  a human-run, on-demand procedure only.

**Non-goals (explicit):**

- No signing key, signature format, or CI enforcement mechanism is
  designed — all three fall under the explicitly excluded "signed
  releases" category.
- No script or tooling was written or executed by this phase.

**Alternatives considered:**

1. *Design an automated checksum-verification CI step now, deferring
   only the signing question.* Rejected: 139E §4's exclusion reads
   "signed releases / checksum verification in CI" as a single excluded
   category, not two severable sub-items; automating checksum
   verification in CI without signing would still fall inside the
   excluded text.
2. *Skip checksum verification design entirely, treating it as
   redundant with the publish step.* Rejected: 139E §4 lists manual
   checksum verification as its own included activity (139B §3.1 item
   3); omitting it would under-deliver the designated scope.

## 4. Governance Compliance

Verified at this checkpoint, per the phase's own instruction to verify
at every governance checkpoint:

| Check | Finding |
|---|---|
| Scope remains valid | **Yes.** §2 above traces every activity to 139E §4 with no addition. |
| Authorization remains applicable | **Yes.** No later phase has superseded, revised, or repealed 139D's Authorization Decision or 139E's Designation (verified: `git log --oneline -- docs/PHASE_139D_ADVISORY_PILOT_AUTHORIZATION_RE_REVIEW.md docs/PHASE_139E_ADVISORY_PILOT_DESIGNATION.md` shows each as a single, unamended authoring commit as of this phase). |
| Designation remains current | **Yes.** `GLP-PILOT-C6`'s lifecycle state was `Designated` (139E §6) entering this phase; no rollback (GAC-001 §10) has occurred. |
| Authority boundaries remain intact | **Yes.** No governance file (`docs/contracts/**`, `.pcae/**` policy configuration) or runtime file (`src/pcae/**`) was modified by this phase — confirmed by `git status` at phase close (§9 below). |

Per GAC-REQ-028, this checkpoint confirms (1) the pilot's mandatory core
stages occur in GLP-001 §6.1's required order — this phase performs only
Stage 1, the first stage, so no reordering is possible — and (2) this
stage's own exit criteria are evaluated, not merely asserted: see §8
below for that evaluation, performed against GLP-001 §6.1 Stage 1's exit
criteria text, not this phase's own self-assessment alone.

## 5. Evidence Collection

Per PGP-001 §8.2 and GAC-REQ-029 (no new evidence artifact type beyond
what GLP-001 §9 already specifies), collected below, organized by 139B
§4's four sub-areas:

### 5.1 Governance Observation Log

- Stage sequence: this phase performed exactly one stage (Architecture),
  the first of GLP-001 §6.1's four mandatory stages, satisfying
  GLP-REQ-016's ordering requirement trivially (nothing preceded it that
  could be out of order).
- Exit-criteria evaluation: performed against GLP-001 §6.1's own text
  (§8 below), not merely self-asserted — this document cites the exact
  exit-criteria language it is being checked against.
- Designation-rationale restatement: present in §0 above, per
  GAC-REQ-030.
- No governance file was touched (§4 above, §9 below) — a directly
  observable, objective governance fact for this checkpoint.

### 5.2 Operational Observation Log

- Participant count: one (this phase's own author/agent, under the
  sponsor's — Atila Madai's — standing authority per 139C.1/139D §2).
  Per 139B §1.9 row 5, this is disclosed in advance as a source of
  thin, not absent, participant-observation evidence for this stage —
  consistent with that disclosed risk, not a new finding.
- Elapsed scope: a single phase (139F) covering Stage 1 only, consistent
  with 139E §4's 4–6 phase estimate (one stage per phase, plus at most
  one repair-class phase) — no compression of multiple stages into this
  phase occurred.
- Documentation overhead: this document is the sole artifact produced;
  no `pyproject.toml`, workflow file, or script was created, keeping
  overhead proportionate to an Architecture-only stage.
- No unexpected outcome or rollback event occurred during this phase
  (PGP-001 §7.1 category 5) — a valid, if less informative, outcome per
  139B §4.3's own disclosure that an event-free pilot produces thin but
  not absent category-5 evidence.

### 5.3 Review Evidence

Not yet applicable — Independent Verification (Stage 4) has not been
reached; this stage's own exit-criteria evaluation (§8 below) is not a
substitute for a future Stage 4 pass on later stages' outputs, only for
this stage's own GLP-001 §6.1-defined exit criteria.

### 5.4 Traceability

Every evidence item above cites: (1) which pilot stage produced it —
Architecture, this phase; (2) which artifact it is drawn from — this
document, or a direct repository check (`pyproject.toml`,
`.github/workflows/`, `git log`) run this session; (3) its §7.2-class
tag — objective (repository-state checks, stage-count, file-touch
checks) throughout this section; no subjective or hypothesis-class claim
is asserted as objective evidence here.

## 6. Decision Register

Every governance-relevant decision made by this phase, with rationale,
evidence, and governing authority:

| # | Decision | Rationale | Evidence | Governing authority |
|---|---|---|---|---|
| 1 | Perform only GLP-001 Stage 1 (Architecture) in this phase, not the full four-stage core | GLP-REQ-016 requires stages in strict order; 139E §6 names 139F specifically as the phase that "begins the pilot's own GLP-001 §6.1 Architecture stage," not one that completes all four stages | 139E §6, §14; GLP-001 GLP-REQ-016 | GLP-001 §6.1 |
| 2 | Produce a design document only, with no packaging/build/publish/checksum command executed | Runtime instruction: "State: Observed, Maximum Capability: observe, Execution Availability: unavailable"; "The pilot does not validate runtime capability" | This phase's own governing prompt | GAC-001 §7 (GAC-REQ-033 — this contract provides no implementation guidance) |
| 3 | Treat "publish workflow design" (139B §3.1 item 2) as excluding any CI-triggered publish, retaining a manual-only publish primitive | 139E §4 excludes "signed releases / checksums-in-CI"; CI-triggered publish without human confirmation risks blurring into that excluded category | §3.2 above, alternative 2 | 139E §4; PGP-REQ-022 / PPA-REQ-026 item 5 (scope-expansion prohibition) |
| 4 | Retain the existing `hatchling` build backend rather than reconsidering build-backend choice | Backend selection is not named in 139E §4's scope ("build configuration and publish workflow design" presumes the existing backend, does not invite reselection); re-litigating it would exceed the designated scope | §3.2 above, alternative 1 | 139E §4 |
| 5 | Defer versioning-scheme selection (SemVer/CalVer/etc.) to the future Contract Freeze phase | GLP-001 §6.1 Stage 1's own definition: Architecture establishes scope/primitives/non-goals, not frozen obligations | §3.1 above, non-goals | GLP-001 §6.1 Stage 1 |

## 7. Risk Monitoring

| Risk category | Observation | Status |
|---|---|---|
| Technical | None — no tooling was executed; no build, publish, or checksum command ran. | No risk materialized. |
| Governance | 139B §1.8 flagged "a natural tendency to expand toward the explicitly excluded items... once underway." Checked explicitly in §2 above; not observed this phase. | Monitored, not triggered. |
| Operational | Reproducibility risk (139B §1.8 item 2) is not yet exercised — no external tooling (`build`, `twine`, PyPI) was invoked this phase. | Not yet applicable; deferred to Implementation stage. |
| Evidence quality | Single-participant thinness (139B §1.9 row 5), disclosed in advance. | Present, as disclosed — not a new or escalating risk. |
| Scope integrity | Verified via §2's element-by-element trace. | Intact. |

No risk category blocks continuation. No rollback trigger (GAC-001 §10)
fired.

## 8. Exit-Criteria Evaluation (GLP-001 §6.1 Stage 1)

Per GAC-REQ-028 item 2 and 139D/139E's own discipline of independent, not
self-asserted, exit-criteria checks, evaluated directly against GLP-001
§6.1 Stage 1's own text (quoted, not paraphrased, for checkability):

| GLP-001 §6.1 Stage 1 requirement | Independent finding |
|---|---|
| "Required outputs: a design document with explicit scope boundaries and an explicit statement that it is not a verdict" | **Met.** §3 above is a design document; §2 states explicit scope boundaries; this statement itself, and §11 below, explicitly state this document is not a verdict. |
| "Entry criteria: the problem is understood well enough to state a scope boundary and non-goals; no prior architecture already covers this scope" | **Met.** §3.1–§3.3 each state explicit non-goals; §3.2 confirms via direct repository check that no prior PyPI-publish workflow or release/versioning policy exists. |
| "Exit criteria: a stable design with no unresolved scope contradiction, evidenced by a cross-proposal synthesis review where competing designs were considered when more than one was proposed" | **Met, single-reviewer caveat disclosed.** §3.1–§3.3 each include an "Alternatives considered" subsection weighing at least one rejected alternative against the selected design, with stated rationale — satisfying the "competing designs were considered" text. The synthesis review is performed by this phase's single participant (§5.2), not a cross-participant board; this is the same single-participant thinness already disclosed in 139B §1.9 row 5, not a new gap. |
| "Evidence expectations: architectural rationale, including any alternatives considered" | **Met.** §3.1–§3.3 each state rationale and alternatives; §6 (Decision Register) restates each decision's rationale and governing authority. |

**Finding: GLP-001 §6.1 Stage 1 exit criteria are met**, with the single
disclosed caveat above (single-participant synthesis) — the same
disclosed risk 139B already named in advance, not a new finding.

## 9. Validation

Confirmed at phase close:

| Check | Result | Evidence |
|---|---|---|
| Governance unchanged | **Confirmed.** | `git status` shows no change under `docs/contracts/` or `.pcae/**` policy configuration. |
| Runtime unchanged | **Confirmed.** | No file under `src/pcae/` modified; `pcae health` reports unchanged runtime state. |
| Scope unchanged | **Confirmed.** | §2's element-by-element trace; no activity outside 139E §4. |
| No execution authority introduced | **Confirmed.** | No packaging, build, publish, or checksum command was executed; Execution Availability remains `unavailable`. |
| No lifecycle changes | **Confirmed.** | This phase performed Stage 1 only; `GLP-PILOT-C6`'s permitted-transition sequence (139E §6) is unaltered — this phase is the first of the transitions 139E already named as permitted (`Designated` → `Architecture in progress`). |
| Repository clean / pushed / `origin/main..HEAD = 0` | To be confirmed at phase completion via governed workflow (§12 below) | `pcae check`, `git status`, `pcae push check` |

## 10. Deliverables

- **Pilot Execution Report** — this document (§0–§11), covering the
  Architecture-stage execution.
- **Evidence Package** — §5 (Governance Observation Log, Operational
  Observation Log, Review Evidence, Traceability).
- **Governance Observation Log** — §5.1.
- **Operational Observation Log** — §5.2.
- **Decision Register** — §6.
- **Risk Summary** — §7.
- **Traceability Report** — §5.4, cross-referenced against 139E §8's
  chain, extended one link:

```
...
139E Advisory Pilot Designation
  (GLP-PILOT-C6 identity, governance binding, lifecycle entry recorded;
  Designated, not activated)
        |
        v
139F Controlled Advisory Pilot Execution (this phase)
  (GLP-001 §6.1 Stage 1 — Architecture — for GLP-PILOT-C6's approved
  scope: release/versioning policy, PyPI packaging design, manual
  checksum verification; design document produced, exit criteria met;
  Stage 2 Contract Freeze not yet begun)
        |
        v
139G Advisory Pilot Assessment & Governance Effectiveness Review
  (recommended next, not started)
```

## 11. No-Go

Confirmed not done by this phase:

- Contract Freeze, Implementation, or Independent Verification (GLP-001
  §6.1 Stages 2–4) were not performed. Only Stage 1 (Architecture) was
  performed.
- No packaging, build, publish, or checksum command was executed. No
  `pyproject.toml` edit, workflow file, or script was created.
- Docker, Homebrew, CI release signing, and migration tooling were not
  touched.
- Governance (`docs/contracts/**`, `.pcae/**` policy configuration) was
  not modified.
- Runtime (`src/pcae/**`) was not modified. Runtime state remains
  Observed / observe / unavailable.
- The pilot's designation (139E) was not reopened, re-derived, or
  re-litigated — treated as authoritative per this phase's own
  governing instruction.
- This document is explicitly **not a verdict** (GLP-001 §6.1 Stage 1
  required-output text) — it is a design document; no GLP-001 §11
  compliance outcome is declared by this phase.

## 12. Success Criteria Confirmation

- The authorized pilot's first stage was completed — §3, §8 (exit
  criteria met).
- Every governance checkpoint applicable to this stage was exercised —
  §4 (scope, authorization, designation, authority-boundary checks).
- Evidence is complete for this stage, with disclosed, not concealed,
  thinness — §5, cross-referenced to 139B §1.9's advance disclosure.
- Authority boundaries were preserved — §2, §9, §11.
- No unauthorized work occurred — §2, §7 (scope-integrity risk:
  monitored, not triggered).
- Governance remains unchanged — §9.
- Runtime remains unchanged — §9.

## 13. Compatibility

- **GLP-001 conformance:** this phase's sole activity is GLP-001 §6.1
  Stage 1, performed in the mandatory order (GLP-REQ-016), producing the
  exact required outputs (§8).
- **GAC-001 conformance:** GAC-REQ-027 (responsibilities — this phase
  introduces no new role), GAC-REQ-028 (observation — §4), GAC-REQ-029
  (evidence capture — §5), GAC-REQ-030 (reporting — §0 designation
  restatement, this document itself a PFR-001-conformant phase report),
  GAC-REQ-033 (no implementation guidance implied — this phase provides
  design scope only, no technical "how").
- **PGP-001 conformance:** evidence categories organized per PGP-001
  §8.2 (§5 above); §7.2 provenance-tagging discipline applied (§5.4).
- **139D/139E:** this phase treats both as authoritative and does not
  re-derive or re-litigate either (§0, §4, §11).
- **Repository governance:** this phase modified only files within its
  own task contract's allowed zones (`docs`, `tasks`, `config`); no
  `docs/contracts/**` file or `.pcae/**` policy configuration was
  touched; no `src/pcae/**` file was touched.

## 14. Recommended Next Phase

**139G — Advisory Pilot Assessment & Governance Effectiveness Review**,
per this phase's own governing instruction, is the recommended next
phase.

However, per GLP-REQ-016's mandatory stage ordering, `GLP-PILOT-C6`'s own
next lifecycle step — before any Stage 5 (GAC-001 §8) independent
assessment could meaningfully evaluate a completed pilot — is its own
**GLP-001 §6.1 Stage 2 (Contract Freeze)**: converting §3 above's
Architecture-stage design into a numbered, falsifiable
release/versioning + packaging + checksum-verification contract. A
Stage-5-style effectiveness review (139G) run before Stages 2–4 exist
would have only a single completed stage's worth of evidence to assess,
which 139B §1.9 already anticipated could be an early, disclosed
limitation rather than a defect. This observation is recorded for the
human authority's own next-phase decision and does not itself select
139G over a further pilot-execution phase (e.g., a "139F.1" or "139G"
continuing Stage 2) — that selection remains a human-authority act, not
one this phase makes on its own.
