# GLP-PILOT-C6 Stage 2 Contract

## Contract identity and status

**Contract:** GPC6-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 142A — GLP-PILOT-C6 Stage 2 Contract Freeze
**Architecture basis:** Phase 139F — Controlled Advisory Pilot Execution,
GLP-001 §6.1 Stage 1 — Architecture
(`docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md`)
**Governed subject:** `GLP-PILOT-C6`'s (External Packaging / Release
Hardening) own Stage 2 obligations — the release/versioning policy, PyPI
packaging, and manual checksum-verification obligations Phase 139F's
Architecture stage scoped, converted into a numbered, falsifiable
contract per GLP-001 §6.1 Stage 2 — plus the pilot-instance governance
obligations (invariants, responsibilities, stage progression, evidence,
validation, boundaries, compliance, compatibility, future-stage, and
security provisions) this Contract Freeze phase is separately instructed
to freeze for `GLP-PILOT-C6` specifically.

GPC6-001 v1.0 is the sole normative authority governing **`GLP-PILOT-C6`'s
own Stage 2 (Contract Freeze) obligations**: the release/versioning,
packaging, and checksum-verification obligations Phase 139F's Architecture
scoped (§1–§7 below), and the pilot-instance governance obligations this
phase's governing instruction separately requires (§8–§14 below). It does
not govern any other GLP-designated initiative, does not redefine GLP-001,
GAC-001, PGP-001, PPA-001, or AGOC-001 (collectively, "the framework
contracts"), and does not narrow or supersede anything the framework
contracts already freeze. Where this contract cites a framework-contract
provision, the citation illustrates an obligation this contract itself
imposes on `GLP-PILOT-C6`; it does not redefine the underlying framework
rule (mirrors AGOC-001 §1 AGOC-REQ-002's identical illustrative-citation
discipline).

Phase 139F's Architecture stage is the approved design basis for §1–§7 of
this contract. This contract independently re-derives every requirement
below directly from `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md`,
`docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
`docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`,
`docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
`docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md`, and
`docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md`, per this
phase's own governing instruction to treat the completed Advisory
Governance chapter (138A–141G) and Phase 139F as evidence, never authority.
Where this contract and any of those documents differ in force, this
contract is normative for `GLP-PILOT-C6` Stage 2 compliance-evaluation
purposes only, and any such difference is itself a defect to be resolved
by a governed contract revision, not by silently preferring one document
over another in practice.

This is contract text only. It redesigns no pilot architecture, modifies
no governance behavior, modifies no lifecycle behavior, modifies no
runtime behavior, modifies no authority ownership, performs no
implementation, and introduces no execution capability. It preserves every
provision of GLP-001, GAC-001, PGP-001, PPA-001, and AGOC-001, and every
architectural invariant Phases 139E–139F and 138A–141G established,
unchanged. Runtime remains Observed / observe / unavailable throughout
every operation this contract governs.

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**,
**SHOULD**, **SHOULD NOT**, and **MAY** are normative, with the meanings
given in GLP-001 §0, which this contract adopts unchanged.

This contract does not itself perform, and is not evidence of, any Stage 3
(Implementation) or Stage 4 (Independent Verification) act. No provision
below builds, packages, publishes, or checksums any artifact; advances
`GLP-PILOT-C6` past Stage 2; or makes a GAC-001 §9 Stage 6 governance
decision.

---

## 1. Contract Purpose

**GPC6-REQ-001 (purpose).** This contract exists to convert Phase 139F's
evidence-derived Architecture-stage design (139F §3.1–§3.3) into binding,
falsifiable `SHALL`/`SHALL NOT` obligations, per GLP-001 §6.1 Stage 2's own
definition ("convert the approved architecture into a small number of
binding, falsifiable obligations... required outputs: a numbered contract
document"), and to freeze the pilot-instance governance obligations this
Contract Freeze phase's own governing instruction separately requires.

**GPC6-REQ-002 (scope).** This contract governs exactly two things, and no
more:

1. **Domain scope (§2–§7)**: the release/versioning policy, PyPI packaging,
   and manual checksum-verification obligations for `GLP-PILOT-C6`'s
   approved scope (139E §4), converting 139F's three Architecture
   subsections into numbered obligations. Per PGP-REQ-020 ("a pilot's own
   subsystem work SHALL be governed by whatever domain contract its own
   Contract Freeze stage produces"), this is the contract GLP-001, GAC-001,
   and PGP-001 anticipate this stage will produce.
2. **Pilot-instance governance scope (§8–§14)**: the invariants,
   responsibilities, stage-progression rules, evidence obligations,
   validation obligations, operational boundaries, compliance rules,
   compatibility guarantees, future-stage prerequisites, and security
   considerations that apply to `GLP-PILOT-C6` specifically, as distinct
   from AGOC-001's identically-shaped but framework-wide obligations.

**GPC6-REQ-003 (applicability).** This contract applies exclusively to
`GLP-PILOT-C6`. It creates no obligation on any other GLP-designated
initiative, any future pilot, or ordinary (non-pilot) PCAE work. It does
not apply retrospectively: Phase 139F's already-completed Architecture
stage is not reclassified, invalidated, or held to a standard this
contract introduces (mirrors GLP-REQ-040, AGOC-REQ-003's identical
prospective-only, non-retrospective rule).

**GPC6-REQ-004 (intended pilot boundaries).** This contract's boundaries
are exactly `GLP-PILOT-C6`'s own designated scope (139E §4): a
release/versioning policy, PyPI packaging (build + publish workflow)
design, and manual release-checksum verification. Docker, Homebrew, CI
release signing, and migration tooling remain outside this contract's
scope, exactly as they were excluded from 139E §4 and 139F §2.

**GPC6-REQ-005 (explicit non-goals).** This contract explicitly does
**not**:

1. Redefine, narrow, or supersede any requirement of GLP-001, GAC-001,
   PGP-001, PPA-001, or AGOC-001 (GPC6-REQ-002).
2. Redesign `GLP-PILOT-C6`'s pilot architecture. 139F's Architecture-stage
   design (139F §3) is treated as approved and uncontested input, per this
   phase's own governing instruction and per GLP-001 §6.1 Stage 2's own
   entry criterion ("an architecture exists and has not been contested").
3. Modify governance behavior, lifecycle behavior, runtime behavior, or
   authority ownership (§10).
4. Introduce execution capability of any kind (§10). No packaging, build,
   publish, or checksum command is executed by this contract or by the
   phase that froze it.
5. Advance `GLP-PILOT-C6` past Stage 2 of GLP-001 §6.1's four-stage core.
   This contract's own freeze does not, by itself, satisfy Stage 2's exit
   criteria (§4.2 below) — that requires a future, separate Independent
   Contract Verification pass (§11).
6. Select a versioning scheme's calendar/semantic details beyond what
   §2 below freezes, invent a signing mechanism, or introduce any CI
   enforcement — each remains explicitly excluded (§2.3, §3.3, §4).
7. Perform, authorize, or be read as authorizing any GAC-001 §9 Stage 6
   governance decision, or extend `GLP-PILOT-C6`'s designation to any
   scope beyond 139E §4.

**GPC6-REQ-006 (Stage 2 only).** This contract governs `GLP-PILOT-C6`
Stage 2 (Contract Freeze) only. Stage 1 (Architecture, Phase 139F, complete)
is treated as approved input; Stage 3 (Implementation) and Stage 4
(Independent Verification) are future, separately-governed phases this
contract does not perform, begin, or authorize (§11).

---

## 2. Release/Versioning Policy Contract

Converts 139F §3.1's Architecture-stage design into numbered obligations.

**GPC6-REQ-007 (single source of truth).** `pyproject.toml`'s `[project]
version` field SHALL be the sole authoritative version identifier for
`GLP-PILOT-C6`'s packaging scope. No duplicate version string SHALL be
introduced elsewhere in the tree by any future Stage 3 Implementation
under this contract (139F §3.1, primitive 1).

**GPC6-REQ-008 (versioning scheme).** Version bumps SHALL follow Semantic
Versioning 2.0.0 (`MAJOR.MINOR.PATCH`). This freezes the specific scheme
139F §3.1 explicitly deferred to this Contract Freeze stage ("the specific
scheme — e.g. Semantic Versioning — is a Contract Freeze decision, not
decided by this Architecture stage"). SemVer is selected over CalVer or an
unversioned scheme because it is the de facto standard for PyPI-distributed
Python packages and requires no new repository-local convention beyond
what `pyproject.toml`'s existing `[project] version = "0.2.0"` field
already implies (a three-component dotted version, verified this phase via
direct read of `pyproject.toml`).

**GPC6-REQ-009 (release-trigger definition).** A release SHALL be
triggered only by an explicit, human-authority-initiated action (a manual
version bump commit followed by a manual publish invocation, §3 below). No
automated, unattended, or schedule-driven release trigger SHALL be
introduced (139F §3.1, primitive 3; consistent with runtime remaining
Observed / observe / unavailable — GPC6-REQ-046).

**GPC6-REQ-010 (non-goal — changelog format).** This contract does not
define a changelog format or an enforcement mechanism for one. `CHANGELOG.md`
continues to be maintained under its own existing, pre-existing repository
convention, unmodified by this contract (139F §3.1, non-goals).

**GPC6-REQ-011 (non-goal — no governance-zone entanglement).** No provision
of this contract touches `docs/contracts/**` or freezes any obligation
outside `GLP-PILOT-C6`'s own domain scope. This restates 139F §3.1's own
non-goal as binding text.

---

## 3. PyPI Packaging Contract

Converts 139F §3.2's Architecture-stage design into numbered obligations.

**GPC6-REQ-012 (build backend retained).** The existing `hatchling` build
backend, and the existing `[tool.hatch.build.targets.wheel]` scoping to
`src/pcae` (Phase 106D), SHALL be retained. No future Stage 3
Implementation under this contract SHALL reconsider or replace the build
backend; backend selection remains outside 139E §4's approved scope (139F
§3.2, alternative 1).

**GPC6-REQ-013 (build step).** A build step SHALL produce a wheel and an
sdist from the existing `hatchling` configuration, using no new build
backend and no new build-system declaration beyond what `pyproject.toml`
already contains (139F §3.2, primitive 1).

**GPC6-REQ-014 (manual publish only).** The publish step SHALL be
human-invoked (e.g. a manually run `twine upload` or equivalent). No
CI-triggered, automated, or unattended publish workflow SHALL be
introduced by any future Stage 3 Implementation under this contract. This
freezes 139E §4's exclusion of "signed releases / checksums-in-CI" as a
binding prohibition on automated publish specifically, not only on
checksum automation (139F §3.2, primitive 2, alternative 2).

**GPC6-REQ-015 (publish target).** The publish target SHALL be PyPI,
optionally preceded by a TestPyPI rehearsal step at the implementer's
discretion. No other package index SHALL be a publish target under this
contract's scope (139F §3.2, primitive 3).

**GPC6-REQ-016 (non-goal — no CI workflow file).** No CI workflow file
implementing packaging or publishing SHALL be created by this Contract
Freeze phase. Any future CI workflow file is Stage 3 (Implementation) work,
gated behind this contract's own freeze (139F §3.2, non-goals) — and, per
GLP-REQ-016, behind this contract's own Independent Contract Verification
(§11 below).

**GPC6-REQ-017 (non-goal — no credential handling defined).** This
contract defines no credential, token, or publish-target-configuration
mechanism. Any such mechanism is Stage 3 Implementation's own
responsibility, subject to ordinary PCAE secret-handling discipline, not a
new mechanism this contract invents (139F §3.2, non-goals).

---

## 4. Checksum Verification Contract

Converts 139F §3.3's Architecture-stage design into numbered obligations.

**GPC6-REQ-018 (digest algorithm).** Checksum generation SHALL use SHA-256
over each built artifact (wheel, sdist). This freezes the specific
algorithm 139F §3.3 explicitly deferred to this Contract Freeze stage ("the
specific algorithm choice is a Contract Freeze decision, not fixed here"),
selected because it is the digest `pip`, `twine`, and PyPI's own published
metadata already use natively, requiring no new tooling dependency.

**GPC6-REQ-019 (manual confirmation step).** A human authority SHALL
compare the generated SHA-256 checksum against the artifact retrieved from
the publish target before the release is treated as verified. This
confirmation SHALL NOT be automated, scripted into an unattended step, or
delegated to a CI gate (139F §3.3, primitive 2).

**GPC6-REQ-020 (no CI enforcement).** No CI-enforced checksum-verification
gate SHALL be introduced under this contract, regardless of whether it is
paired with signing. 139E §4's exclusion of "signed releases / checksum
verification in CI" is treated, per 139F §3.3's own alternative-1 analysis,
as a single excluded category — automating checksum verification in CI
without signing remains inside that excluded text (139F §3.3, alternative
1).

**GPC6-REQ-021 (no signing).** No signing key, signature format, or
signature-verification mechanism SHALL be designed or implemented under
this contract. Signing remains categorically excluded by 139E §4 (139F
§3.3, non-goals).

**GPC6-REQ-022 (checksum step is mandatory, not optional).** A future Stage
3 Implementation SHALL NOT omit the checksum-verification step as
redundant with the publish step. 139E §4 lists manual checksum verification
as its own included, separately-designated activity (139F §3.3,
alternative 2).

---

## 5. Domain Evidence Contract

**GPC6-REQ-023 (traceability to architecture).** Every obligation in §2–§4
above traces to a specific 139F §3.1–§3.3 subsection, cited inline. No
obligation in §2–§4 was invented without a corresponding Architecture-stage
primitive, non-goal, or alternatives-considered analysis (GLP-001 §9,
Contract Freeze evidence expectation: "normative obligations, each
traceable to the frozen architecture").

**GPC6-REQ-024 (no scope expansion).** No obligation in §2–§4 exceeds
139E §4's approved scope. Docker, Homebrew, CI release signing, and
migration tooling remain excluded from every domain section above,
verified section-by-section against 139E §4 and 139F §2's own exclusion
table.

---

## 6. Domain Compatibility Contract

**GPC6-REQ-025 (139F conformance).** §2–§4 above convert 139F §3's design
without narrowing or contradicting any primitive, non-goal, or alternative
139F recorded. Where this contract makes a Contract-Freeze-stage decision
139F explicitly deferred (versioning scheme, digest algorithm), §2 and §4
above state that decision and its rationale explicitly, rather than
silently assuming one.

**GPC6-REQ-026 (139E conformance).** Every obligation in §2–§4 remains
inside 139E §4's approved scope (release/versioning policy; PyPI packaging
build configuration and publish workflow design; manual release-checksum
verification), with no element added.

---

## 7. Domain Boundary Contract

**GPC6-REQ-027 (not a general PCAE release policy).** §2–§4 above bind
`GLP-PILOT-C6`'s own packaging scope only. This contract does not establish
a general PCAE-wide release or versioning policy applicable to any other
subsystem, contract, or artifact family. Generalizing §2–§4 beyond
`GLP-PILOT-C6`'s scope requires a separate, explicitly-scoped governance
act.

**GPC6-REQ-028 (Docker/Homebrew/signing/migration remain excluded).** No
obligation anywhere in §2–§4 SHALL be read as implicitly authorizing
Docker packaging, a Homebrew formula, CI-based release signing, or
migration tooling. These remain excluded exactly as 139E §4 and 139F §2
excluded them.

---

## 8. Pilot Invariants

The following properties are frozen as mandatory and non-negotiable for
every act performed under, or in furtherance of, `GLP-PILOT-C6`'s Stage 2
and any future stage. Each is independently re-derived from the framework
contracts' own text and from 139E–139F's own governing instructions, not
invented by this contract (mirrors AGOC-001 §2's identical invariant-freeze
discipline, applied here to a single pilot instance rather than the whole
framework).

**GPC6-REQ-029 (advisory-only pilot).** `GLP-PILOT-C6` remains advisory
throughout Stage 2: this contract grants no execution, lifecycle,
governance, or runtime capability, and creates no obligation on any
subsequent phase beyond the obligations this contract itself states
(GLP-REQ-004; AGOC-REQ-007).

**GPC6-REQ-030 (deterministic governance).** Every compliance evaluation of
this contract's obligations SHALL be independently reproducible by a future
reader applying this contract's text to the same cited evidence (mirrors
GLP-001 §11's per-stage compliance model and AGOC-REQ-009).

**GPC6-REQ-031 (evidence-first operation).** No act that advances
`GLP-PILOT-C6` past Stage 2, or that revises this contract's own text, may
occur without cited, reproducible evidence meeting §9 below (extends
AGOC-REQ-008 and PGP-REQ-036's no-improvement-assumption rule to this
pilot instance specifically).

**GPC6-REQ-032 (authority neutrality).** No provision of this contract
grants any role authority beyond what GLP-001 §8, GAC-001 §7–§9, PGP-001
§3, PPA-001 §3/§11, or AGOC-001 §3 already assign. This contract creates
no new authority and redistributes none of the existing authority those
sections assign (mirrors AGOC-REQ-010).

**GPC6-REQ-033 (lifecycle neutrality).** No provision of this contract
changes which PCAE phase types exist, how they sequence outside
`GLP-PILOT-C6`'s own designated lifecycle, or any lifecycle stage, phase
type, or compliance outcome defined elsewhere in PCAE governance (mirrors
GLP-REQ-007, AGOC-REQ-011).

**GPC6-REQ-034 (runtime neutrality).** No provision of this contract
changes runtime capability. Runtime remains Observed / observe /
unavailable throughout (GLP-REQ-044; AGOC-REQ-012).

**GPC6-REQ-035 (implementation neutrality).** This contract performs no
implementation work and transfers no implementation ownership. The
Implementer role (GLP-001 §8) remains the sole owner of `GLP-PILOT-C6`'s
future Stage 3 implementation content; freezing this contract does not
transfer that ownership (mirrors AGOC-REQ-013).

**GPC6-REQ-036 (reproducibility).** Every evidence item cited in support of
a `GLP-PILOT-C6` Stage 2 act SHALL cite a specific, checkable source — a
file path, phase ID, or requirement ID (PGP-REQ-034; GLP-REQ-028;
AGOC-REQ-014).

**GPC6-REQ-037 (traceability).** Every `GLP-PILOT-C6` Stage 2 act's
evidentiary basis SHALL be traceable to the specific stage, phase report,
or artifact it is drawn from, carrying PGP-001 §7.2's objective/subjective/
hypothesis tag (PGP-REQ-031; AGOC-REQ-015).

**GPC6-REQ-038 (auditability).** Every `GLP-PILOT-C6` Stage 2 act SHALL
leave a record sufficient for a future Independent Verifier or Independent
Assessor to reconstruct what evidence was cited, which provision it was
evaluated against, and what outcome resulted, without relying on the acting
party's own narrative alone (AGOC-REQ-016).

**GPC6-REQ-039 (invariants are mandatory).** GPC6-REQ-029 through
GPC6-REQ-038 are mandatory and non-negotiable. No act, however evidenced,
may waive, suspend, or narrow any of them; a proposed exception is itself
evidence of a defect in this contract requiring a governed revision under
§14, not a basis for a one-time waiver (mirrors AGOC-REQ-017).

---

## 9. Pilot Responsibilities

**GPC6-REQ-040 (one owner per responsibility).** Every responsibility below
has exactly one owning role. No two roles share ownership of the same
concern (GLP-REQ-026; AGOC-REQ-018).

| Role | Responsibility | Contract basis |
|---|---|---|
| **Release/Versioning Policy Owner** (a future Stage 3 Implementer) | Implements §2's obligations (SemVer scheme, single-source-of-truth version field, human-triggered release) without reopening any Contract Freeze decision. | §2 above; GLP-001 §8 (Implementers) |
| **Packaging Owner** (a future Stage 3 Implementer) | Implements §3's build/publish obligations, retaining the frozen `hatchling` backend and the manual-publish-only primitive. | §3 above; GLP-001 §8 |
| **Checksum-Verification Owner** (a future Stage 3 Implementer) | Implements §4's SHA-256 manual-confirmation procedure, introducing no CI gate or signing mechanism. | §4 above; GLP-001 §8 |
| **Independent Contract Verifier** | Performs `GLP-PILOT-C6` Stage 2's own exit-criteria evaluation (§11 below) — independently confirming zero ambiguous requirements in §2–§4 — distinct from any role that authored this contract. | GLP-001 §6.1 Stage 2 exit criteria; §11 below |
| **Independent Implementation Verifier** | Performs `GLP-PILOT-C6` Stage 4 (Independent Verification of Stage 3 Implementation), when that future phase runs; distinct from the Implementer and from the Independent Contract Verifier above. | GLP-001 §6.1 Stage 4; §12 below |
| **Human Authority** | Sole authority for every election no other role may make: authorizing Stage 3 to begin (§12 below), authorizing Stage 4, any future rollback (GAC-001 §10), and any GAC-001 §9 Stage 6 governance decision touching `GLP-PILOT-C6`. | GLP-001 §8; GAC-001 §9–§10; 139E §6 |

**GPC6-REQ-041 (no new role).** This contract introduces no role beyond
those already named in GLP-001 §8 and AGOC-001 §3. It merely names, for
`GLP-PILOT-C6` specifically, which of those existing roles owns which of
this contract's own obligations (AGOC-REQ-020's identical no-new-role
discipline).

**GPC6-REQ-042 (non-overlap is falsifiable).** A future phase that
encounters genuine ambiguity about which role in GPC6-REQ-040's table owns
a specific `GLP-PILOT-C6` act has identified evidence of a gap in this
contract, admissible as a §14-qualifying improvement trigger — not license
to informally reassign responsibility (AGOC-REQ-019).

---

## 10. Stage Progression Contract

**GPC6-REQ-043 (Stage 2 entry criteria — met).** GLP-001 §6.1 Stage 2's
entry criteria are: "an architecture exists and has not been contested; the
obligations to be frozen can be stated as falsifiable requirements."
Independently confirmed this phase: Phase 139F's Architecture stage exists,
has not been contested by any later phase (verified: no phase between 139F
and 142A modifies or disputes 139F's design — `git log --oneline` shows no
such phase), and §2–§4 above demonstrate the obligations are statable as
falsifiable `SHALL`/`SHALL NOT` requirements.

**GPC6-REQ-044 (Stage 2 completion criteria).** Per GLP-001 §6.1 Stage 2's
own exit criteria — "a contract with zero ambiguous requirements as
independently confirmed by a contract-verification pass" — this contract's
freeze (this phase, 142A) is **not itself** sufficient to satisfy Stage 2's
exit criteria. Completion requires a future, separate Independent Contract
Verification phase (§11 below) confirming zero ambiguous requirements
across §2–§14. Until that verification completes, `GLP-PILOT-C6` remains
in "Contract Freeze in progress," not "Contract Freeze complete."

**GPC6-REQ-045 (permitted transitions).** From this contract's frozen
state, the only permitted forward transition is to `GLP-PILOT-C6` Stage 2
Independent Contract Verification (§11 below). No other forward transition
is permitted until that verification reaches a determinate outcome.

**GPC6-REQ-046 (prohibited transitions).** The following transitions are
explicitly prohibited:

1. Beginning Stage 3 (Implementation) directly from this freeze, skipping
   Independent Contract Verification — this would violate GLP-REQ-016's
   "Implementation SHALL NOT begin against an ambiguous contract" and
   GLP-001 §6.1 Stage 3's entry criterion ("a contract is frozen and
   unambiguous"), since unambiguity here is established only by
   verification, not by the freeze act alone (GLP-REQ-016 of GLP-001; 137L's
   own precedent of declining to resolve a contract ambiguity itself,
   restated at GLP-001 §6.1 Stage 3 entry criteria).
2. Treating this contract's own freeze as itself constituting Stage 2's
   completion — GLP-001 §6.1 Stage 2's exit criteria require independent
   confirmation, not merely a published document (GLP-REQ-036's identical
   principle, restated here for this pilot).
3. Any reordering of GLP-001 §6.1's four core stages with respect to
   `GLP-PILOT-C6` (GLP-REQ-016).
4. Treating any advisory citation of this contract elsewhere in the
   repository as advancing `GLP-PILOT-C6` beyond its current stage
   (AGOC-REQ-027 item 5's identical prohibition, restated here as binding
   on this contract specifically).

**GPC6-REQ-047 (rollback expectations).** GAC-001 §10's rollback contract
governs `GLP-PILOT-C6` unchanged by this contract. If a future Independent
Contract Verification finds this contract's obligations genuinely
ambiguous or misfit to the pilot's actual shape, the correct response,
per GAC-REQ-045 item 2, is to pause the pilot, record the misfit as pilot
evidence, and treat "the Contract Freeze needed revision before
Implementation could begin" as a legitimate, informative outcome — not a
concealed failure. This contract introduces no new rollback mechanism
beyond GAC-001 §10.

**GPC6-REQ-048 (dependency requirements).** Stage 3 (Implementation) SHALL
depend on: (a) this contract's own Independent Contract Verification (§11)
reaching a determinate "zero ambiguous requirements" finding, and (b) an
explicit human-authority election to proceed (§12 below). Neither
dependency may be satisfied by the other; verification alone does not
authorize Stage 3 to begin absent the human-authority election, and the
election alone does not substitute for verification (GLP-REQ-003;
GAC-REQ-023).

---

## 11. Domain and Instance Evidence Contract

**GPC6-REQ-049 (acceptable evidence — categories).** Evidence for any act
under this contract is limited to PGP-001 §8.2's seven categories:
architectural evidence, contract evidence, verification evidence,
governance observations, participant observations, metrics, and lessons
learned (PGP-REQ-032), scoped to `GLP-PILOT-C6` specifically.

**GPC6-REQ-050 (minimum evidence quality).** Every evidence item SHALL
state its provenance (PGP-REQ-031) and cite a specific, checkable source —
file path, phase ID, or requirement ID (PGP-REQ-034). An unattributed
narrative claim is not admissible evidence under this contract.

**GPC6-REQ-051 (evidence retention).** No new retention mechanism is
introduced. Evidence persists under existing PCAE version control and
phase-report conventions (mirrors AGOC-REQ-032, GAC-REQ-048/PPA-REQ-036's
requirement that evidence survive even a future rollback).

**GPC6-REQ-052 (evidence required before Stage progression).** No
transition described in §10 above may occur without cited evidence meeting
GPC6-REQ-049–051. Absence of such evidence is itself evidence for retaining
`GLP-PILOT-C6` at its current stage (mirrors AGOC-REQ-037).

---

## 12. Validation Contract

**GPC6-REQ-053 (mandatory validation — operational).** Every future phase
acting under this contract SHALL run the governed validation workflow
applicable to that phase (`pcae check`, `python -m pytest -n auto`, `git
status`) before claiming completion, per this repository's standing
governance rules and PFR-001's own reporting discipline.

**GPC6-REQ-054 (mandatory validation — evidence review).** Every future
phase SHALL independently review its own cited evidence against GPC6-REQ-049–052
before asserting a stage-progression claim, not merely restate a prior
phase's own summary (mirrors PPA-REQ-016's independent-review standard).

**GPC6-REQ-055 (mandatory validation — governance review).** Every future
phase SHALL confirm, at minimum: scope remains within 139E §4 and this
contract's own §1–§7 boundaries; authorization (139D) and designation
(139E) remain unamended and unsuperseded; and no governance file
(`docs/contracts/**`, `.pcae/**` policy configuration) or runtime file
(`src/pcae/**`) was modified outside that phase's own authorized scope
(mirrors 139F §4's own governance-checkpoint table, restated as binding for
every future stage).

**GPC6-REQ-056 (mandatory validation — independent verification).** No
Stage 2 completion claim, and no future Stage 3 completion claim, is valid
without the corresponding independent verification this contract requires:
§11's Independent Contract Verification for Stage 2, and GLP-001 §6.1
Stage 4's Independent Verification for Stage 3 (GLP-REQ-016).

**GPC6-REQ-057 (completion requirements).** A stage is complete under this
contract only when: its own GLP-001 §6.1 exit criteria are independently
confirmed (not self-asserted); its evidence package meets §11 above; its
governance checkpoints (GPC6-REQ-055) pass; and the repository is clean,
checked, tested, and pushed through the governed workflow, per this
repository's standing procedure.

---

## 13. Operational Boundary Contract

`GLP-PILOT-C6`, under this contract, SHALL never become:

**GPC6-REQ-058 (not execution authority).** Grant, simulate, or imply any
execution capability. Runtime remains Observed / observe / unavailable
throughout every operation this contract governs (GLP-REQ-044; AGOC-REQ-045).

**GPC6-REQ-059 (not runtime authority).** Change, gate, or condition
runtime capability. No provision of this contract, nor any `GLP-PILOT-C6`
stage conducted under it, changes runtime capability (GLP-REQ-044;
AGOC-REQ-047).

**GPC6-REQ-060 (not lifecycle authority).** Control, gate, or block any
phase's execution outside `GLP-PILOT-C6`'s own designated lifecycle. A PCAE
phase not part of `GLP-PILOT-C6` is unaffected by this contract's existence
(GLP-REQ-007; AGOC-REQ-048).

**GPC6-REQ-061 (not implementation authority).** Perform, substitute for,
or transfer ownership of implementation work. The Implementer role
(GLP-001 §8) remains the sole owner of any future Stage 3 implementation
content (AGOC-REQ-046).

**GPC6-REQ-062 (not architectural authority).** Reopen, redesign, or
reinterpret Phase 139F's Architecture-stage design. This contract converts
that design into obligations (§2–§4); it does not re-derive or re-litigate
it (AGOC-REQ-049's identical principle, applied here to 139F specifically
rather than to a citing initiative's own architecture in general).

**GPC6-REQ-063 (preservation of existing authority owners).** No boundary
above transfers any authority away from the role that already holds it
under GLP-001 §8, GAC-001 §7–§9, PGP-001 §3, PPA-001 §3/§11, or AGOC-001
§3. This contract preserves, and does not redistribute, every existing
authority assignment (AGOC-REQ-051).

---

## 14. Compliance Contract

**GPC6-REQ-064 (documentation obligations).** Any compliance-relevant act
under this contract SHALL be recorded in a PFR-001-conformant phase report
or equivalent governed document (GAC-REQ-052; AGOC-REQ-052). No
`GLP-PILOT-C6`-specific report template is introduced beyond what GAC-001
§5–§9 and PGP-001 §5.6 already require.

**GPC6-REQ-065 (review obligations).** Any act that escalates
`GLP-PILOT-C6` beyond its current stage (Independent Contract Verification,
Stage 3 authorization, Stage 4 Independent Verification, any future
Independent Assessment) SHALL undergo the specific review the corresponding
framework contract already requires (GLP-001 §10; GAC-001 §8; PPA-001
§5–§7) — this contract adds no additional review gate to that existing
sequence (AGOC-REQ-054).

**GPC6-REQ-066 (evidence obligations).** Compliance with §8's invariants
and §10's stage-progression rules SHALL be evaluated against the evidence
standard in §11, not against narrative assertion alone (AGOC-REQ-053).

**GPC6-REQ-067 (deviation handling).** A deviation from this contract's
domain obligations (§2–§7) or pilot-instance invariants (§8) or boundaries
(§13) is not an acceptable deviation under any circumstance (GPC6-REQ-039).
A deviation elsewhere in this contract's descriptive text, if genuinely
non-normative, carries no governance consequence beyond visibility on
inspection (mirrors AGOC-REQ-055's identical two-tier deviation model).

**GPC6-REQ-068 (compliance interpretation).** Where this contract's text
is genuinely ambiguous between two readings, the ambiguity is itself
admissible evidence under §14's own future-revision process (§14 below,
GPC6-REQ-071) for a future contract-repair proposal (mirrors AGOC-REQ-057).
Pending such a repair, the reading that imposes the narrower obligation and
preserves the greater number of existing invariants (§8) and boundaries
(§13) SHALL govern.

**GPC6-REQ-069 (non-compliance handling).** A finding of non-compliance
with this contract does not itself invalidate GLP-001, GAC-001, PGP-001,
PPA-001, or AGOC-001, mirroring PGP-001 §10's principle that pilot failure
"never automatically invalidates GLP-001" (PGP-REQ-042–044; AGOC-REQ-056).

---

## 15. Compatibility Contract

**GPC6-REQ-070 (backwards compatibility).** Any future revision of this
contract SHALL remain backward compatible unless it explicitly states its
compatibility impact and supersedes a named requirement (mirrors GLP-REQ-043,
AGOC-REQ-058).

**GPC6-REQ-071 (additive evolution).** A future revision MAY add an
obligation, a role responsibility, or an evidence category; it SHALL NOT
silently remove or narrow one without explicitly naming the removed or
narrowed provision and its rationale (mirrors GLP-REQ-041–042,
AGOC-REQ-059).

**GPC6-REQ-072 (framework compatibility).** This contract complements
GLP-001, GAC-001, PGP-001, PPA-001, and AGOC-001; it does not replace,
redefine, or weaken any of them (GLP-REQ-038; AGOC-REQ-002).

**GPC6-REQ-073 (versioning expectations).** This contract carries its own
version identifier (GPC6-001 v1.0), independent of the framework contracts
it operationalizes for `GLP-PILOT-C6`. A future revision is recorded as a
new version of this same document, not as a silent in-place edit erasing
this version's own record (AGOC-REQ-061).

**GPC6-REQ-074 (migration expectations).** Every provision of this
contract applies prospectively only, per GPC6-REQ-003. No migration of
Phase 139F's already-produced evidence to a new standard is required or
implied.

---

## 16. Future Stage Contract

**GPC6-REQ-075 (Stage 3 prerequisites).** Stage 3 (Implementation) MAY
begin only after: (a) §11's Independent Contract Verification reaches a
determinate finding that §2–§14 above contain zero ambiguous requirements
(GLP-001 §6.1 Stage 2 exit criteria); and (b) an explicit human-authority
election to proceed, distinct from and not implied by (a) (GLP-REQ-003;
GAC-REQ-023).

**GPC6-REQ-076 (required evidence for Stage 3).** Any phase claiming Stage
3 has begun SHALL cite: this contract's own frozen text (this document),
its Independent Contract Verification's determinate finding (§11), and the
specific human-authority election authorizing Stage 3 to begin, per §11
above's citation discipline.

**GPC6-REQ-077 (authorization requirements).** No accumulation of
Independent Contract Verification passes, evidence, or elapsed time,
however extensive, authorizes Stage 3 to begin by itself. GPC6-REQ-075(b)'s
human-authority election is required in every case (mirrors AGOC-REQ-042's
identical no-substitute-for-election rule).

**GPC6-REQ-078 (independent verification expectations for later stages).**
Stage 4 (Independent Verification of Stage 3's Implementation) SHALL be
performed by a party distinct from Stage 3's own Implementer and from
§11's own Independent Contract Verifier, mirroring GLP-001 §8's
re-derive/do-not-trust discipline and AGOC-REQ-065's role-separation
restatement.

**GPC6-REQ-079 (no automatic progression).** No stage transition described
in §10 or this section occurs automatically. Every transition requires the
specific dependency (§10, GPC6-REQ-048) and, where stated, the explicit
human-authority election this section requires. This restates GLP-REQ-003
and GAC-REQ-043's "automatic adoption is forbidden" principle as binding on
every `GLP-PILOT-C6` stage transition specifically, not only on GAC-001 §9
Stage 6.

---

## 17. Security and Governance Considerations

**GPC6-REQ-080 (governance integrity).** No act under this contract may
alter, bypass, or substitute for the compliance-evaluation mechanism
GLP-001 §11 already defines. Integrity is preserved by GPC6-REQ-046's
prohibition on skipped or reordered transitions and GPC6-REQ-066's
evidence-based compliance standard.

**GPC6-REQ-081 (separation of responsibilities).** The role separations
GPC6-REQ-040's table establishes are binding on every act under this
contract: the Independent Contract Verifier (§11) SHALL NOT be this
contract's own author; the Independent Implementation Verifier (Stage 4)
SHALL NOT be Stage 3's own Implementer or §11's own Independent Contract
Verifier (mirrors GAC-REQ-035, AGOC-REQ-065).

**GPC6-REQ-082 (conflict prevention).** No single role under GPC6-REQ-040
may hold two separated responsibilities for `GLP-PILOT-C6`'s Stage 2 and
Stage 4 verification. A proposed exception is a disqualifying conflict, not
a waivable convenience (AGOC-REQ-066).

**GPC6-REQ-083 (auditability).** Every act under this contract SHALL remain
independently auditable per GPC6-REQ-038 without reliance on the acting
party's own summary (AGOC-REQ-068).

**GPC6-REQ-084 (transparency).** Every citation, evidence item, or decision
under this contract SHALL be recorded in a location and form a future
reader can locate and inspect directly (§14's documentation requirement),
never only referenced from memory or informal channels (AGOC-REQ-069).

**GPC6-REQ-085 (accountability).** Every act's outcome under this contract
is attributable to the specific role in GPC6-REQ-040 responsible for it; an
outcome with no attributable owning role is itself non-compliant
(AGOC-REQ-070).

---

## 18. Non-Goals (restated for completeness)

See §1. This contract freezes `GLP-PILOT-C6` Stage 2 domain obligations
(release/versioning, packaging, checksum verification) and pilot-instance
governance obligations. It does not implement, automate, or enforce them in
tooling; it does not change runtime, lifecycle, or governance capability;
it does not retrospectively reclassify Phase 139F or any other prior
phase; it does not advance `GLP-PILOT-C6` past Stage 2 by itself; and it
does not perform, authorize, or substitute for any GAC-001 §9 Stage 6
governance decision.

## 19. Validation

Confirmed at this phase's own start and throughout drafting:

- **Independent re-derivation.** Every requirement above (GPC6-REQ-001
  through GPC6-REQ-085) was independently re-derived from direct re-read
  of `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md`,
  `docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
  `docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`,
  `docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
  `docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md`, and
  `docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md` at this
  phase's start, with the completed Advisory Governance chapter (138A–141G)
  treated as evidence of contract shape and discipline, never as authority
  for any specific requirement's wording.
- **Determinism.** Every invariant in §8 and every domain obligation in
  §2–§4 is stated as a falsifiable, binary property, independently
  checkable by inspecting `pyproject.toml`, `.github/workflows/`, git
  history, and role assignments — not a subjective judgment call.
- **No governance authority expansion.** §13 and §17 restate, without
  narrowing or broadening, the boundary provisions already frozen by
  GLP-REQ-004/044/045, GAC-REQ-013/055, and AGOC-REQ-045–051.
- **No lifecycle behavior change.** §10 restates GLP-001 §6.1's existing
  four-stage order for `GLP-PILOT-C6` specifically; no new phase type or
  lifecycle stage is added anywhere in this contract.
- **No runtime behavior change.** `pcae health`/`pcae runtime inspect`
  were confirmed unchanged at this phase's start and remain Observed /
  observe / unavailable; no file under `src/pcae/` is created, modified, or
  deleted by this phase.
- **No authority ownership change.** No role in §9 gains authority beyond
  what GLP-001 §8, GAC-001 §7–§9, PGP-001 §3, PPA-001 §3/§11, or AGOC-001
  §3 already grant it (GPC6-REQ-032, GPC6-REQ-063).
- **No implementation responsibility change.** No file under `src/pcae/**`
  is touched by this phase; the Implementer role's exclusive ownership of
  `GLP-PILOT-C6`'s future Stage 3 content is restated, not transferred
  (GPC6-REQ-035, GPC6-REQ-061).
- **Stage 2 remains advisory only.** GPC6-REQ-029, GPC6-REQ-044, and §13
  together confirm no designation, authorization, or Stage 6 decision is
  made or authorized by this contract; `GLP-PILOT-C6` remains at Stage 1 of
  4 complete, Stage 2 in progress (frozen, not yet independently verified),
  until §11's Independent Contract Verification runs.
- **No execution capability introduced.** GPC6-REQ-058 and GPC6-REQ-059
  bind this contract to introduce none; no packaging, build, publish, or
  checksum command was executed by this phase.
- `git status --short` at phase start showed no file under
  `docs/PHASE_139F_CONTROLLED_ADVISORY_PILOT_EXECUTION.md`,
  `docs/contracts/GOVERNANCE_LIFECYCLE_PATTERN_CONTRACT.md`,
  `docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md`,
  `docs/contracts/PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`,
  `docs/contracts/PILOT_PROPOSAL_AUTHORIZATION_CONTRACT.md`, or
  `docs/contracts/ADVISORY_GOVERNANCE_OPERATIONAL_CONTRACT.md` modified by
  this phase.
- `pcae check` passed and `pcae health` reported the expected active-task
  state at phase start (confirmed before this document was written).

## 20. No-Go

Confirmed not done by this phase:

- No governance contract (GLP-001, GAC-001, PGP-001, PPA-001, AGOC-001) was
  modified by this phase.
- `GLP-PILOT-C6`'s pilot architecture (139F) was not redesigned by this
  phase.
- No governance behavior was modified by this phase.
- No lifecycle behavior was modified by this phase.
- No runtime behavior was modified by this phase.
- No authority ownership was modified by this phase.
- No implementation was performed or modified by this phase.
- No execution capability was introduced by this phase.
- `GLP-PILOT-C6` was not advanced beyond Stage 2 (Contract Freeze, this
  phase) by this phase — Stage 2's own exit criteria remain unmet pending
  §11's future Independent Contract Verification.
- No GAC-001 §9 Stage 6 governance decision was made or attempted by this
  phase.
- No new compliance-checking role, tool, or apparatus was introduced by
  this phase.
- Production code (`src/pcae/**`) was not modified by this phase.

## 21. Phase 142A Freeze Confirmation

Phase 142A freezes §1–§7 (Domain Contract: Purpose, Release/Versioning
Policy, PyPI Packaging, Checksum Verification, Domain Evidence, Domain
Compatibility, Domain Boundary) and §8–§17 (Pilot-Instance Contract:
Invariants, Responsibilities, Stage Progression, Evidence, Validation,
Operational Boundary, Compliance, Compatibility, Future Stage, Security and
Governance Considerations) above as GPC6-001 v1.0 — the authoritative
Stage 2 Contract governing `GLP-PILOT-C6`. No implementation is authorized
by this freeze. No governance behavior changes. No lifecycle enforcement is
introduced. No production code is touched. Runtime remains Observed /
observe / unavailable. `GLP-PILOT-C6` remains at Stage 2 (Contract Freeze
recorded, not yet independently verified) — not advanced to Stage 3.

## 22. Recommended Next Phase

**142B — GLP-PILOT-C6 Stage 2 Independent Verification.**

Purpose: independently re-derive GPC6-001 without trusting Phase 142A's own
narrative. Attempt to falsify every normative obligation above against
Phase 139F's Architecture-stage text and against the framework contracts'
own text; confirm zero ambiguous requirements remain across §2–§17
(GLP-001 §6.1 Stage 2's own exit criterion); confirm no unnecessary
ceremony was introduced; confirm §9's role table remains non-overlapping;
and validate that §13's operational boundaries and §8's invariants are
fully consistent with GLP-001, GAC-001, PGP-001, PPA-001, and AGOC-001 as
currently frozen. Repair only independently demonstrated Blocking contract
defects. No implementation or governance behavior changes are authorized.
Only upon a determinate "zero ambiguous requirements" finding does
`GLP-PILOT-C6` Stage 2 reach GLP-001 §6.1's own exit criteria; Stage 3
(Implementation) remains a distinct, separately-authorized future phase
(§16 above).
