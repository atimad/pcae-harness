# Phase 147B — Authority Evaluation Model Contract Freeze

## 0. Purpose and Boundary

This phase is authorized, per human instruction, to freeze the
architectural contract governing the Authority Evaluation Model for
Decision Templates (informally, "C-1"), the capability Phase 147A
selected as Chapter 147's objective. This is a **Contract Freeze phase**:
it produces `docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`
(AEM-001 v1.0) and this report; it does not implement any evaluation
function, Registry, Declaration store, CLI command, or Publication
Coordinator change; it does not modify `src/pcae/**` of any kind; it does
not change runtime, Permission Broker, CHGR-001, IWPC-001, IWC-001,
PEC-001, TAMC-001, TAMPC-001, GAC-001, or GLP-001; it does not authorize
automation. Predecessor: Phase 147A (Next Strategic Capability
Architecture Reassessment, complete). Runtime baseline at both the start
and close of this phase: `Observed` / `observe` / `unavailable`
(unchanged — confirmed §1, §11).

---

## 1. Bootstrap

Run at the start of this phase, from `~/repos/pcae-harness`:

- `git status --short`: clean (no output) at bootstrap.
- `git branch --show-current`: `main`.
- `git log --oneline -5`: HEAD at `cf2b2387` ("Phase 147A: close
  push-and-promote task, open idle placeholder"), matching
  `origin/main`/`origin/HEAD`.
- `git rev-list --count origin/main..HEAD`: `0`.
- `git rev-list --count HEAD..origin/main`: `0`.
- `pcae session bootstrap --agent-id claude-local`: lock already held by
  `claude-local`; backend lock rehydrated; health healthy; check passed;
  active task at bootstrap time was the post-147A idle placeholder
  (expected); recommended next phase reported as 147B, matching this
  phase's own authorization.
- `pcae task transition --next "Phase 147B: Authority Evaluation Model
  Contract Freeze"`: closed the idle placeholder task, opened this
  phase's own task contract
  (`tasks/active/20260730-1310-phase-147b-authority-evaluation-model-contract-freeze.md`),
  status coherence passed, health healthy, check passed.

**Confirmed**: repository clean; correct branch (`main`); local and
remote synchronized (0 ahead, 0 behind); no active governed phase existed
prior to this one; runtime unchanged from every prior chapter's baseline.

---

## 2. Architectural Context

Phase 147A independently reconstructed PCAE's full strategic state and
selected the Authority-Evaluation Model for Decision Templates ("C-1") as
Chapter 147's objective, finding it named as a standing, correctly
undischarged deferral by three independent chapters:

- **IWC-001** (§6, §11 Human Responsibility Contract): repeatedly refers
  to "the eligible Human Authority the bound Decision Template names"
  without ever defining what that means mechanically.
- **IWPC-001** (§4.1 Authority Neutrality, §18 Authorization Input
  Contract, §29 Conflict Register item C-1, §31 Non-Goals): IWPC-REQ-009
  forbids inventing an authority-evaluation policy; IWPC-REQ-119/123
  disclose that no `authority_basis_claimed` field exists to populate and
  that "no existing contract assigns [authority-evaluation]
  responsibility to anything in this repository"; §31's own closing
  Non-Goal names resolving C-1 as explicitly out of scope, "pending a
  future, separately governed initiative."
- **CHGR-001** (§11 Authority Contract, §20.5, CHGR-REQ-096/097/199,
  PEC-REQ-115): §11 states authority is established "only by the
  conjunction of valid human action... and the applicable governing
  authority model — the eligible-authority rule the record's own
  Decision Template names" — the exact phrase this phase's contract now
  gives concrete shape to. CHGR-REQ-199 requires
  `authority_basis_claimed` to "remain correctly and permanently absent
  — never fabricated — for as long as no Decision Template
  `eligible_authority` citation exists anywhere in this repository."
  PEC-REQ-115 (Phase 146K) already anticipates the exact mechanism this
  contract defines: "a claim citing the bound Decision Template's own
  `eligible_authority` field... the Coordinator MAY construct
  `authority_basis_claimed` solely from that already-verbatim citation,
  never from an independent judgment of whether the claim is actually
  valid."

This phase's own independent reconstruction, performed directly against
the primary contract text (not Phase 147A's summary of it — see §3
below), confirms every one of these citations verbatim and additionally
confirms, by direct source inspection, that no `eligible_authority` field,
Decision Template class, or evaluation mechanism of any kind exists
anywhere in `src/pcae/**` today: `Session.template_ref`
(`src/pcae/interactive_workflow/models/session.py:87`) is a bare,
unvalidated `str`, consumed only as an opaque pass-through identifier by
`PublicationHandoff.build_package`
(`src/pcae/interactive_workflow/publication_handoff/handoff.py:168`).
There is, today, no Decision Template *object* for an `eligible_authority`
field to attach to — only an opaque reference string.

---

## 3. Independent Reconstruction

Per instruction, this phase did not begin from Phase 147A's own summary
of the gap. The following primary sources were independently re-read in
full or by targeted section during this phase:

- `docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
  (IWPC-001 v1.4): §§1–13 read in full (Purpose, Scope, Terminology,
  Architecture Invariants, Command Contracts, Input/Output/Transport/
  Versioning, State/Repository Contracts); §18 (Authorization Input
  Contract, IWPC-REQ-116–124) and §29–§31 (Conflict Register, Amendment,
  Non-Goals) read in full and cited verbatim above.
- `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
  (CHGR-001): §11 (Authority Contract), §12 (Assurance Contract), §13
  (Record Lifecycle Contract), §20 (Governance Responsibility Contract)
  and §20.5 (runtime-consumption judgment call, read as a structural
  precedent for how this contract's own Registry-mechanics deferral, §4.6
  of AEM-001, should be reasoned and disclosed rather than silently
  left open), §21 (Audit Contract), and §26 (the Phase 146K revision
  introducing CHGR-REQ-194–206, `authority_basis_claimed`/
  `assurance_level`'s actual construction rules and the 146K judgment
  call splitting the two fields' dependency graphs) read in full.
- `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` (PEC-001): §20.2
  (PEC-REQ-111–117, the Phase 146K widening that introduces PEC-REQ-115's
  citation rule) read in full.
- `docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
  (TAMC-001): read for its own definition of "authority"
  (`authority_epoch`/`authority_state`, TAMC-REQ-009/020/025/034/035,
  §7 Authority Contract) and independently compared, term-by-term,
  against CHGR-001 §11's `eligible_authority` concept; confirmed
  structurally unrelated (§9 of AEM-001).
- `docs/contracts/GOVERNANCE_ADOPTION_CONTRACT.md` (GAC-001): §9
  (Governance Decision Contract, GAC-REQ-040–044) read in full and
  independently compared against this chapter's own authority-evaluation
  question; confirmed structurally unrelated (§10 of AEM-001) — GAC-001
  §9 governs a one-time, pilot-scoped adoption decision, not a
  per-decision eligibility check.
- `PROJECT_STATUS.md`'s `## Current Phase` section (the sole live-status
  source, per the standing precedent reconfirmed at 144I/146A/147A).
- `docs/PHASE_147A_NEXT_STRATEGIC_CAPABILITY_ARCHITECTURE_REASSESSMENT.md`
  itself, treated as evidence of architectural intent (§6's Proposed
  Chapter, §6.2's explicitly-deferred gating-vs-disclosure judgment call,
  §8's risk table), never as contractual authority in its own right.
- Direct source inspection: `grep`-based confirmation that no
  `eligible_authority`, `DecisionTemplate`, or authority-evaluation
  mechanism exists anywhere under `src/pcae/`; confirmation that
  `Session.template_ref` and `IWPC-REQ-192`'s `--template-version` are
  the only Decision-Template-adjacent artifacts that exist in code or
  frozen contract text today.

### 3.1 Every place authority is referenced but intentionally deferred

| Source | Reference | Deferral disposition |
|---|---|---|
| IWC-001 §6, §11 | "the eligible Human Authority the bound Decision Template names" | Never defined mechanically; adopted unchanged as this contract's own starting phrase (AEM-001 §3, §4.1). |
| IWPC-001 §4.1 (IWPC-REQ-009) | "SHALL NOT... invent an authority-evaluation policy that does not already exist upstream" | Restated and extended at AEM-001 §2.2/AEM-REQ-003/AEM-REQ-004. |
| IWPC-001 §18 (IWPC-REQ-119, 123) | "no `authority_basis_claimed` field exists to populate"; "the CLI MUST NOT decide whether... substantively authorized" | Directly answered by AEM-001 §5–§7: a concrete evaluation function and citation-population rule now exists, at the contract level. |
| IWPC-001 §29 C-1, §31 | Named, disclosed, explicitly out of scope for IWPC-001 itself | This is the gap AEM-001 exists to close, at the contract level; IWPC-001's own text is unmodified (AEM-001 §0, §15). |
| CHGR-001 §11 | "the eligible-authority rule the record's own Decision Template names" | Given a concrete, frozen shape for the first time (AEM-001 §4). |
| CHGR-001 §20.5 | Runtime-consumption ownership "explicitly declined... rather than silently defaulting" | Read as the structural precedent for AEM-001 §4.6's own disclosed Registry-mechanics deferral. |
| CHGR-REQ-199 | `authority_basis_claimed` "correctly and permanently absent... for as long as no... citation exists" | Preserved unweakened: AEM-001 §5.4/§7 defines `indeterminate` precisely to keep this true wherever no Declaration exists. |
| PEC-REQ-115 | "MAY construct `authority_basis_claimed` solely from that already-verbatim citation" | AEM-001 §7 supplies the concrete citation source PEC-REQ-115 anticipated but could not yet name. |
| GAC-001 §9 | Stage 6 governance-adoption decision, undischarged | Confirmed unrelated and undischarged by this contract's existence (AEM-001 §10). |
| TAMC-001 §7 | A distinct "Authority Contract" for CLTR lifecycle-transition authority | Confirmed unrelated (AEM-001 §9), despite the shared English term. |

---

## 4. Authority Model

Frozen at AEM-001 §3–§5. Summary: authority evaluation is a deterministic,
pure function consuming (a) a claimed decision-maker identity already
collected by IWC-001/IWPC-001 (`--owner-id`), and (b) an Eligible
Authority Declaration resolved, by exact `(template_ref,
template_version)` key, through a new Decision Template Authority
Registry whose lookup contract (not storage mechanics) this phase freezes.
The function produces exactly one immutable `AuthorityEvaluationOutcome`
carrying a closed three-valued result (`eligible` / `ineligible` /
`indeterminate`).

## 5. Eligible Authority Contract

Frozen at AEM-001 §4. An Eligible Authority Declaration is the narrowest
construct that satisfies CHGR-001 §11's existing text: a closed,
non-empty set of literal claimed-identity strings, bound immutably to one
`(template_ref, template_version)` pair (AEM-001 §4.1–§4.2, AEM-REQ-006–
009). No role, scope, time-bounding, or exception mechanism is defined
(§4.4's judgment call, reasoned against the scope-creep risk Phase 147A
§8 flagged). Registry storage/authoring mechanics are explicitly deferred
to Implementation Planning (§4.6's judgment call), disclosed as a
narrower freeze than IWPC-001 §13 achieved for `SessionRepository`,
because no pre-existing Decision Template artifact exists in this
repository for this phase to extend the way IWPC-001 extended the
pre-existing `SessionRepository` ABC.

## 6. Evaluation Semantics

Frozen at AEM-001 §5. Evaluation is total (never raises for well-formed
input, AEM-REQ-016), deterministic (AEM-REQ-009), and produces exactly one
of three outcomes (AEM-REQ-020): `eligible`, `ineligible`, or
`indeterminate` (the "no Declaration exists" case — deliberately
distinguished from `ineligible`, AEM-REQ-017, so that "unknown authority"
is never conflated with "evaluated and found unfavorable"). Evaluation
scope is limited to the decision-maker role (`--owner-id`) only; the
authorizing principal (`--operator-id`) is explicitly named as a future,
undefined extension (§12 of AEM-001).

## 7. Evidence Requirements

Frozen at AEM-001 §5.1. The sole evidentiary input is the already-existing
claimed decision-maker identity; this contract introduces no new evidence
collection, credential, signature, or assurance-level upgrade
(AEM-REQ-014), mirroring IWPC-REQ-007/008's transport-only discipline
applied to evaluation. No authority evidence is mandatory to attempt
Confirmation, Readiness, or Publication (AEM-REQ-015) — this restates the
disclosure-only decision (§16 of AEM-001, §9 below).

## 8. Failure Model

Frozen at AEM-001 §6. Evaluation raises only for malformed structural
input (empty/malformed claimed identity, empty template identifiers, or a
structurally invalid empty-set Declaration, AEM-REQ-023); every
substantive outcome, including an unfavorable one, is a successful,
disclosed result, never an exception (AEM-REQ-024). Fail-closed discipline
is restated at AEM-REQ-032: a malformed or ambiguous input can never
resolve to `eligible` or citation population.

## 9. Interaction Matrix

| Interacting system | Relationship | AEM-001 reference |
|---|---|---|
| IWC-001 | Adopts "eligible Human Authority" phrase unchanged; introduces no session/template semantic change | §0, §3 |
| IWPC-001 | Restates and extends IWPC-REQ-002/003/009's policy-invention prohibition; defines no new CLI/transport surface (deferred to a future IWPC-001 revision) | §11.2, AEM-REQ-038 |
| PEC-001 | Supplies the concrete citation source PEC-REQ-115 anticipated; Coordinator remains sole authorizer/executor, never imports this contract's evaluation function directly | §7, AEM-REQ-026–029 |
| CHGR-001 | Populates only the already-reserved `authority_basis_claimed` field, per its existing "MAY, never fabricate" rule (CHGR-REQ-199); `assurance_level`'s own CHGR-REQ-200 derivation is untouched (it does not depend on `eligible_authority`) | §7, §14 (D-conflicts) |
| TAMC-001 / TAMPC-001 | Confirmed structurally unrelated ("authority" names two different concepts) | §9 |
| GAC-001 / GLP-001 | Confirmed structurally unrelated (per-decision eligibility vs. one-time governance-process adoption); this contract's existence does not discharge GAC-001 §9 | §10 |
| Runtime / Permission Broker | No relationship; not gated by, not gating; runtime unaffected throughout | §2.2, §12 |
| Verification (Independent Contract/Implementation Verifier) | MAY verify conformance of an evaluation's derivation; MAY NOT adjudicate substantive eligibility | §11.3 |
| Inspection (`decision-session status`/`readiness`, `governance-record inspect`) | MAY report an already-computed outcome verbatim; MAY NOT compute or infer one | §11.4 |

## 10. Security Considerations

- **Fail-closed by construction** (AEM-REQ-032): malformed input can never
  produce `eligible`; there is no discretionary or best-effort evaluation
  path.
- **No new evidence-collection surface** (AEM-REQ-014): this contract adds
  no new credential channel, so it introduces no new shell-history,
  transport, or storage exposure beyond what IWPC-001 §23 already
  discloses for `--owner-id`/`--operator-id`.
- **Immutability of Declarations once evaluated against** (AEM-REQ-008)
  prevents a retroactive eligibility change from silently altering the
  meaning of an already-produced `AuthorityEvaluationOutcome` — an
  analogue of CHGR-001 §13.3's substantive-immutability discipline applied
  one layer earlier, closing a tamper vector a mutable Declaration would
  otherwise open.
- **No enforcement surface exists to attack** (AEM-REQ-003): because
  evaluation cannot gate anything in v1.0, there is no way for a forged or
  manipulated evaluation outcome to block or force a governance act; the
  worst-case consequence of a defective evaluation implementation is a
  misleading disclosure, not an unauthorized action — a deliberately
  narrow blast radius, consistent with Phase 147A §8's own risk framing.
- **Residual, disclosed risk**: because Registry storage mechanics are
  deferred (§4.6 of AEM-001), this phase cannot yet assess concrete
  tampering/concurrency risk for however a future implementation persists
  Declarations; that assessment necessarily belongs to Implementation
  Planning (147D) and its own Independent Verification pass, mirroring
  how IWPC-001 §21's Concurrency Contract had to wait for its own
  Contract Freeze phase to name the stores it would govern.

## 11. Future Extension Points

Frozen at AEM-001 §12.1: `EvaluationResult` MAY widen under a future major
revision; `EligibleAuthorityDeclaration` MAY gain optional fields under a
future additive revision; the Registry lookup contract is
storage-agnostic by design so any future concrete implementation may
satisfy it; and a future, separately governed contract revision MAY adopt
an enforcement/gating policy, with its own explicit reasoning distinct
from this v1.0 contract's disclosure-only decision (§16 of AEM-001).

## 12. No-Go Confirmation

This phase did not modify production code, verification/inspection code,
any existing contract, schema, manifest, or test. `docs/contracts/
AUTHORITY_EVALUATION_MODEL_CONTRACT.md` is a wholly new file; IWC-001,
IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, GAC-001, and GLP-001
remain byte-for-byte unmodified (confirmed via `git diff` scope at §14
below — no file under `docs/contracts/` other than the new
`AUTHORITY_EVALUATION_MODEL_CONTRACT.md` was touched). No `.pcae/
policy.toml` edit occurred. No `src/pcae/**` file was touched. No
execution capability was implemented, enabled, or authorized. No
enforcement or gating behavior was adopted (§16 of AEM-001 explicitly
adopts disclosure-only). No strategic-lineage modification occurred
beyond the standard task/phase bookkeeping this phase's own task contract
authorizes. Runtime unchanged throughout (§13 below).

## 13. Validation

Re-run at the close of this phase:

- `pcae check`: passed.
- `pcae health`: healthy.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae runtime inspect`: `Runtime status: not_implemented`, `Runtime
  state: Observed`, `Execution capability: unavailable`, `Maximum plugin
  capability: observe`, `Registry status: empty`, `Plugin count: 0` —
  identical to §1's start-of-phase reading. Runtime unchanged.
- `pcae push check`: working tree state confirmed against only this
  phase's authorized files (the two documents above, task-contract
  lifecycle files, `tasks/DONE.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`,
  `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-
  report.md`) — no other file touched.

**Confirmed**: runtime unchanged; repository healthy; no policy change;
no strategic-lineage change beyond ordinary task/phase bookkeeping; no
production modification of any kind.

(Full command output transcribed in §14 of this report at close-out, per
this repository's standing convention for the "Governance" validation
section of a Contract Freeze phase.)

---

## 14. Overall Verdict

**CONTRACT FROZEN**

AEM-001 v1.0 independently reconstructs and closes the authority-
evaluation gap ("C-1") named as a standing, correctly-undischarged
deferral by three independent chapters, without weakening, narrowing, or
modifying any of IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
TAMPC-001, GAC-001, or GLP-001. It resolves the one genuine judgment call
this phase inherited (gating vs. disclosure-only) with explicit,
independently-derived reasoning (§16 of AEM-001), and discloses, rather
than silently omits, the one place its own freeze is narrower than its
nearest precedent (IWPC-001 §13's `SessionRepository`) — the Registry's
storage/authoring mechanics, deferred to Implementation Planning because,
unlike `SessionRepository`, no pre-existing Decision Template artifact
exists anywhere in this repository to extend. Zero items in the Conflict
and Findings Register (§14 of AEM-001) are Blocking. Runtime remained
`Observed`/`observe`/`unavailable` throughout, confirmed unchanged at both
open and close.

---

## 15. Recommended Next Phase

**147C — Authority Evaluation Model Contract Independent Verification.**
Independently re-derives AEM-001's requirements from IWC-001/IWPC-001/
CHGR-001/PEC-001 primary text (not this report's own summary of them);
checks for ambiguity, internal consistency, and conflict with frozen
invariants — especially IWPC-REQ-002/003's prohibition on inventing an
authority-evaluation *policy*, as distinct from an evaluation
*mechanism*, and the disclosure-only judgment call at §16 of AEM-001,
which independent verification should re-examine on its own terms rather
than defer to this phase's reasoning. No implementation may begin until
the contract has been independently verified. This is a recommendation,
not an authorization: a human decision point governs whether and how
Phase 147C begins, exactly as every predecessor Contract Freeze phase's
own recommendation did not itself authorize the phase it named.

Separately, and independent of Chapter 147's own sequence, Phase 147A's
own three standalone candidates — a re-derivation of the Phase 107A
execution-capability gap analysis, roadmap-tracking reconciliation, and
GLP-PILOT-C6 Stage 3 resumption (blocked on the still-undischarged GAC-001
§9 Stage 6 decision) — remain open, disclosed, and unscheduled; nothing in
this phase resolves, folds in, or forecloses any of them.
