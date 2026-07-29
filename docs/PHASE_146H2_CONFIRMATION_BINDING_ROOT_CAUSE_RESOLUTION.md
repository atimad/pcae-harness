# Phase 146H.2 — Confirmation Binding Root-Cause Resolution

**Mode:** Independent Root-Cause Investigation (documentation-only; no
implementation repair authorized or performed)
**Predecessor:** 146H.1 (Governance Verification Schema-Version Support
Repair), which independently discovered and documented, but was not
authorized to repair, the `CONFIRMATION_UNBOUND` Blocking finding
investigated here (146H.1 §9 Finding 3).

---

## 1. Executive Summary

A real, schema-valid, correctly-146G-constructed `human_governance_record`
bundle is rejected by `governance/verification.py`'s `confirmation_binding`
check with `CONFIRMATION_UNBOUND` whenever verified together with its own
real sibling artifacts. This phase independently reproduced the failure
from scratch (not by re-running 146H.1's evidence) using the actual
production construction function (`build_publication_record`, Phase 146G)
and the actual production CLI verification path (`pcae governance-record
verify --related ...`).

**Root cause, independently established:** `governance/verification.py`'s
`_confirmable_content_digest_of()` and its use in the `confirmation_binding`
check implement the *original* Phase 143E design, in which
`human_confirmation_evidence.confirmed_content_digest` was expected to
equal a digest recomputed over the `human_governance_record`'s own
stripped JSON fields. That design was superseded at Phase 146B, when
CHGR-REQ-201 froze a different, incompatible construction rule:
`confirmed_content_digest` is populated **verbatim** from
`PublicationReadinessPackage.preview_digest` — a digest computed upstream,
in `interactive_workflow`, over the rendered *Preview* object (a
structurally different document: `schema_version`, `preview_id`,
`session_id`, `preview_timestamp`, `transition_sequence_number`,
`evidence_refs`, `clarification_refs`, `audit_refs`,
`transition_summary`, `rendered_content`, `metadata`), never over the
`human_governance_record`'s own fields. Phase 146G's construction code
(`record.py`) was updated to follow CHGR-REQ-201 and was independently
verified compliant (146H). `verification.py`'s check was never updated to
match. The two digests being compared are computed over disjoint inputs
and can never coincide for any conforming bundle, tampered or not.

This is classified **Resolution A — Verification implementation defect. No
contract issue exists.** The contract (CHGR-REQ-201, CHGR-REQ-085, §10
Provenance Contract) is internally consistent, was independently verified
at freeze (146C), and is correctly implemented by construction (146G,
independently confirmed by 146H). Only the verifier is stale.

**Final Verdict: ROOT CAUSE ESTABLISHED.**

No repair was performed. No contract, schema, verifier, or Publication
Coordinator file was modified by this phase, consistent with its Scope
Boundary and No-Go Boundary.

---

## 2. Independent Reproduction

Reproduction did not rely on 146H.1's report text, hand-authored fixtures,
or any pre-existing test. It used the real production construction
function and the real production CLI verification command.

### 2.1 Construction (real production path)

`pcae.governance.publication.record.build_publication_record` — the sole
production function Phase 146G's Publication Coordinator calls to
construct the four CHGR-001 sibling artifacts — was invoked directly with
a `PublicationReadinessPackage` (the same production dataclass the
Coordinator receives from `interactive_workflow`) carrying
`preview_digest = "c" * 64`. This produced a genuinely
146G-constructed, schema-shape-valid four-artifact bundle
(`human_governance_record`, `human_confirmation_evidence`,
`governance_record_provenance`, `governance_record_integrity`) — not a
hand-authored fixture.

### 2.2 Verification (real production CLI path)

The four artifacts were written to disk and verified with the actual
production CLI command:

```
pcae governance-record verify hgr.json \
  --related conf.json --related prov.json --related integ.json
```

Result (exit code 1):

```
outcome: rejected
error_code: CONFIRMATION_UNBOUND
message: The confirmation evidence's confirmed_content_digest does not
  match this record's recomputed confirmable content -- the record
  changed after confirmation, or the confirmation was replayed against
  different content.
checks:
  schema_shape                  passed
  digest_self_consistency       passed
  lifecycle_structural_legality passed
```

This independently confirms 146H.1's finding: the bundle is schema-valid,
internally digest-consistent, and lifecycle-legal, yet is unconditionally
rejected at the `confirmation_binding` check.

### 2.3 Digest tracing (root-level evidence)

Direct inspection of the constructed bundle and of `verification.py`'s own
recomputation:

| Field | Value |
|---|---|
| `package.preview_digest` | `cccc...cccc` (64 hex chars) |
| `human_confirmation_evidence.confirmed_content_digest` | `cccc...cccc` — **identical** to `preview_digest` |
| `governance_record_provenance.preview_content_digest` | `cccc...cccc` — **identical** to `preview_digest` |
| `human_confirmation_evidence.preview_rendering_digest` | `cccc...cccc` — **identical** to `preview_digest` |
| `verification._confirmable_content_digest_of(human_governance_record)` | a **distinct** SHA-256 value computed over the record's own stripped canonical JSON (e.g. `5f4bdbde2...` in a control run) |

The three fields sourced from `package.preview_digest` are, by
construction, always byte-identical to one another and to
`preview_digest` itself. `_confirmable_content_digest_of()`'s output is
computed over an entirely different document (the finalized
`human_governance_record`'s own fields, JSON-canonicalized) and has no
mathematical relationship to `preview_digest`. The check at
`verification.py:379` compares the first family of values against the
second; they are drawn from disjoint input spaces and cannot coincide for
any conforming bundle.

---

## 3. Root-Cause Investigation

### 3.1 Contract (CHGR-REQ-201, CHGR-001 §10, CHGR-REQ-085)

`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`:

- **CHGR-REQ-085** (§23, restating the Provenance Contract): "Every
  published CHGR SHALL carry, verbatim, the exact preview content the
  human actually confirmed."
- **§10 Provenance Contract**: provenance evidence must be sufficient to
  reconstruct "... the exact preview content the human actually
  confirmed, stored verbatim ...".
- **CHGR-REQ-201** (frozen Phase 146B, §26): "The `human_confirmation_evidence`
  sibling artifact SHALL populate `confirmed_content_digest`/
  `preview_rendering_digest` from the Package's own `preview_digest`
  (verbatim) ...".

These three passages are mutually consistent and unambiguous:
`confirmed_content_digest` is a verbatim copy of the Package's
`preview_digest` — a digest over the *preview*, not a digest to be
independently recomputed from the final record's own content.

Searching the entire contract document for the verifier's own internal
vocabulary (`CONFIRMATION_UNBOUND`, `confirmation_binding`,
`confirmable_content`) returns **zero matches**. The contract does not
name, specify, or constrain the verifier's cross-artifact comparison
algorithm at all; that check is purely an implementation artifact of
`verification.py`, introduced ad hoc at Phase 143E, and was never
promoted into, or reconciled with, contract text.

### 3.2 Schema (`human_confirmation_evidence.schema.json`)

The `confirmed_content_digest` field's `description` reads: "Digest
computed over the literal preview payload the human confirmed
(CHGR-REQ-085). A HumanGovernanceRecord's confirmation is unbound
(CONFIRMATION_UNBOUND) at verification if this digest does not match the
record's own recomputed content digest."

This single description string is internally self-contradictory: its
first sentence agrees with CHGR-REQ-085/201 (digest over the *preview*
payload); its second sentence describes the verifier's *actual* (stale)
behavior (comparison against "the record's own recomputed content
digest"). `git log --follow` shows this file has exactly one commit in
its entire history — Phase 143E — and has never been touched since,
including when CHGR-REQ-201 was frozen (146B) or implemented (146G). The
description's second sentence is leftover documentation of the pre-146B
design, never reconciled with the field's own first sentence or with
CHGR-REQ-201.

Per the contract's own §0 authority statement, "CHGR-001 v1.0 is the sole
normative authority governing the Canonical Human Governance Record
artifact class"; JSON Schema `description` strings carry no independent
contractual force. This is the same class of drift Phase 146D
independently examined for a different field
(`authority_basis_claimed`'s `required` entry, also frozen at 143E and
inconsistent with a later, more specific 146B/144F requirement) and
resolved by treating the later, more specific frozen requirement as
authoritative over unrevised 143E-era schema text — precedent directly
applicable here.

### 3.3 Construction (`governance/publication/record.py`, Phase 146G)

```python
"confirmed_content_digest": package.preview_digest,
"preview_rendering_digest": package.preview_digest,
...
"preview_content_digest": package.preview_digest,
```

`git log --follow` shows this file's history is Phase 144C → 144F → 146G;
the `confirmed_content_digest = package.preview_digest` line was
introduced at **146G**, i.e. after and in direct implementation of
CHGR-REQ-201 (frozen 146B). Phase 146H independently traced and confirmed
this mapping as "Satisfied" against CHGR-REQ-201 in its own requirement
table. This phase independently re-confirmed it by direct construction
(§2.1 above) rather than trusting either prior phase's claim.

The construction-time fail-closed gate (CHGR-REQ-204/205,
`chgr_envelope.validate_chgr_artifact`) is schema-*shape* validation only
(`validate_record_shape`); it never invokes `confirmation_binding` or any
cross-artifact digest comparison. This means real Publications always
succeed at construction time — the defect is invisible until a bundle is
later independently *verified* with its siblings supplied, exactly the
scenario 146H.1 first exercised and this phase independently reproduced.

### 3.4 Verification (`governance/verification.py`)

```python
def _confirmable_content_digest_of(record: dict[str, Any]) -> str:
    excluded = {"record_digest", "confirmation_evidence_ref", "provenance_ref", "integrity_ref"}
    stripped = {k: v for k, v in record.items() if k not in excluded}
    return hashlib.sha256(_canonical_bytes(stripped)).hexdigest()
...
confirmable_digest = _confirmable_content_digest_of(record)
...
if confirmation.get("confirmed_content_digest") != confirmable_digest:
    return _fail("CONFIRMATION_UNBOUND", ...)
```

`git log --follow` shows this function and its use in the
`confirmation_binding` check date to **Phase 143E** and have never been
modified since (146H.1's own change to this file touched only the
unrelated `schema_version` comparison). At 143E, no CHGR-REQ-201 existed;
`confirmed_content_digest` was, by the original 143E design (independently
confirmed: every hand-authored 143E-era fixture's `confirmed_content_digest`
is a digest of the record's own content, matching this function exactly),
meant to be exactly what `_confirmable_content_digest_of()` recomputes.
146B's CHGR-REQ-201 silently superseded that design for construction
without any corresponding update to verification.

The existing test suite never exercises this defect because every test
that supplies related siblings to `verify_artifact_at_path`
(`test_chgr_authority_boundary.py`, `test_chgr_143f_independent_verification.py`)
uses the same 143E-era hand-authored fixtures, which were built to satisfy
`_confirmable_content_digest_of()` by construction and therefore never
exercise a genuinely 146G-constructed bundle. Phase 146H's own
reproduction (146H.1 §9 Finding 3) "never supplied related artifacts, so
it never reached this check" — confirming why this defect survived 146B
through 146H without detection.

### 3.5 Fixture history

`FIXTURES/valid_confirmation_evidence.json` and siblings under
`tests/fixtures/chgr/` are 143E-era hand-authored artifacts, pre-dating
CHGR-REQ-201 by three phases (146B/146C/146D intervene). They encode the
pre-146B design assumption and are not representative of what Phase 146G
production code actually constructs. This phase did not modify them
(no-go boundary); their continued presence and passing status is a
historical-fixture-assumption artifact, not evidence against the root
cause identified above — it explains *why* the defect was never caught,
not an alternative cause of the defect itself.

### 3.6 Phase 143 architecture / Phase 146 implementation

Phase 143A (`PHASE_143A_..._ARCHITECTURE.md`) and 143E predate the
Preview/Confirmation split formalized later in the Interactive Workflow
chapter (143G–143P) and the Publication CLI Transport chapter (145A–145I).
CHGR-REQ-201 (146B) is the first point at which the contract explicitly
ties `confirmed_content_digest` to `PublicationReadinessPackage.preview_digest`
rather than to the CHGR record's own content — a deliberate architectural
narrowing made possible only once the Preview object existed as a
first-class, independently-digestable artifact (Phase 143J/143N). This is
consistent with §26.3 of the 146B contract-freeze report characterizing
CHGR-REQ-201/202 as concretizing, not narrowing, the pre-existing
Provenance Contract (§10) — i.e., 146B's specific construction rule is a
legitimate refinement of §10's general "verbatim preview content"
obligation, not a contradiction of it.

---

## 4. Evidence Matrix

| Claim | Evidence | Method |
|---|---|---|
| A genuinely 146G-constructed, schema-valid bundle is rejected `CONFIRMATION_UNBOUND` when verified with real siblings | §2.1–2.2 | Live execution: `build_publication_record` → `pcae governance-record verify --related ...` (CLI) |
| `confirmed_content_digest`, `preview_content_digest`, `preview_rendering_digest` are all verbatim copies of `package.preview_digest` | §2.3 | Direct field inspection of constructed bundle |
| `_confirmable_content_digest_of()` computes a structurally unrelated digest | §2.3 | Direct invocation of the verifier's own function against the constructed record |
| Contract (CHGR-REQ-201/085/§10) mandates verbatim preview-digest propagation, not record-content recomputation | §3.1 | Contract citation, direct text |
| Contract never specifies the verifier's `confirmation_binding`/`CONFIRMATION_UNBOUND` algorithm | §3.1 | Exhaustive grep of contract text (zero matches) |
| Schema's field `description` is internally self-contradictory and unrevised since 143E | §3.2 | `git log --follow`, direct text comparison |
| Construction (`record.py`) implements CHGR-REQ-201 correctly, introduced at 146G | §3.3 | `git log --follow`, source citation |
| Construction-time gate never invokes the cross-artifact check that fails | §3.3 | Source citation (`chgr_envelope.validate_chgr_artifact`) |
| Verifier's check is unmodified 143E logic, predates CHGR-REQ-201 by three phases | §3.4 | `git log --follow`, source citation |
| Existing tests never exercise this path with real 146G-constructed bundles | §3.4 | Fixture/test inspection |
| No repository/governance state was altered by this investigation | §5 | `git status --short` (clean) before and after; `pcae check`/`health`/`doctor task-memory`/`runtime inspect`/`push check` all pass unchanged |

---

## 5. Architectural Analysis

The CHGR-001 pipeline has two independent producers of
`confirmed_content_digest`-adjacent values and one consumer:

```
interactive_workflow.preview.builder.PreviewBuilder.compute_digest(preview)
        │  (digest over Preview's own canonical payload: schema_version,
        │   preview_id, session_id, preview_timestamp,
        │   transition_sequence_number, evidence_refs, clarification_refs,
        │   audit_refs, transition_summary, rendered_content, metadata)
        ▼
PublicationReadinessPackage.preview_digest  (verbatim carry-through)
        ▼
governance.publication.record.build_publication_record()  [Phase 146G,
        implements CHGR-REQ-201]
        │  copies package.preview_digest verbatim into THREE sibling
        │  fields: confirmed_content_digest, preview_rendering_digest
        │  (both in human_confirmation_evidence), and
        │  preview_content_digest (in governance_record_provenance)
        ▼
governance.verification.verify_artifact_at_path()  [Phase 143E,
        NEVER updated for CHGR-REQ-201]
        │  recomputes _confirmable_content_digest_of(human_governance_record)
        │  -- a digest over the RECORD's own stripped fields, an entirely
        │  different document than the Preview -- and compares it against
        │  confirmed_content_digest
        ▼
        CONFIRMATION_UNBOUND, unconditionally, for every conforming bundle
```

The architecture already carries the information a correct cross-artifact
check would need: three sibling fields (`confirmed_content_digest`,
`preview_rendering_digest`, `preview_content_digest`) are all verbatim
copies of the same upstream value and are therefore mutually comparable
for internal consistency. The verifier does not use this available
signal; instead it recomputes a value that was never meant to equal any
of them, because the record's own content and the Preview's content are,
by design, two different documents captured at two different pipeline
stages (rendered-preview-time vs. finalized-record-time).

## 6. Authority Analysis

- **Contract (CHGR-001, CHGR-REQ-201, CHGR-REQ-085, §10):** frozen at
  146B, independently verified at 146C, internally consistent, never
  contradicted by any later phase. **Authoritative.**
- **Construction (`record.py`, 146G):** independently verified compliant
  with CHGR-REQ-201 at 146H; independently re-confirmed by direct
  execution in this phase (§2.1, §3.3). **Correct, and in step with the
  authoritative contract.**
- **Schema field `description` (`human_confirmation_evidence.schema.json`):**
  non-normative documentation string, frozen at 143E, never revised for
  146B; self-contradictory on its own terms. **Stale documentation, not
  an independent authority** (per the contract's own §0 statement of sole
  normative authority).
  Recommendation, not authorization: whichever phase repairs the
  verifier should also revise this description string so it no longer
  contradicts CHGR-REQ-085's own text, since leaving it as-is would
  continue to mislead future readers even after the code is fixed.
- **Verifier (`verification.py`, 143E, never updated):** implements a
  design that predates, and is now incompatible with, the authoritative
  frozen contract. **Not authoritative; the outlier requiring repair.**
- **Historical fixtures (`tests/fixtures/chgr/*`):** encode the
  pre-146B/143E-era assumption; explain why the defect went undetected;
  **not evidence of a correct design**, since they predate CHGR-REQ-201
  by three phases and were never re-derived from it.

No component among contract, schema-envelope requirements, or
Publication Coordinator construction logic requires modification. The
defect is fully contained within `governance/verification.py`'s
`confirmation_binding` check.

---

## 7. Findings

1. **(Independently reproduced, Blocking)** A genuinely 146G-constructed,
   schema-valid `human_governance_record` bundle is unconditionally
   rejected `CONFIRMATION_UNBOUND` when verified with real siblings via
   the production CLI path (`pcae governance-record verify --related`).
   Reproduced from first principles in this phase (§2), independently of
   146H.1's own reproduction.
2. **(Root cause)** `verification.py`'s `confirmation_binding` check
   compares `confirmed_content_digest` against
   `_confirmable_content_digest_of(record)` — logic dating to Phase 143E,
   never updated when CHGR-REQ-201 (Phase 146B) redefined
   `confirmed_content_digest`'s construction rule to be a verbatim copy
   of `PublicationReadinessPackage.preview_digest`, a digest over a
   structurally different document (§3.1–3.4).
3. **(Contract status)** CHGR-REQ-201, CHGR-REQ-085, and §10 of the CHGR-001
   contract are mutually consistent, unambiguous, and contain no
   specification of the verifier's comparison algorithm at all — the
   contract does not require, and never required, the check that is
   currently failing (§3.1).
4. **(Construction status)** Phase 146G's construction correctly
   implements CHGR-REQ-201; this was independently confirmed twice now
   (146H, and this phase's own direct execution) (§3.3).
5. **(Detection gap)** No existing test exercises `confirmation_binding`
   against a genuinely 146G-constructed bundle; all passing tests that
   exercise this check use 143E-era hand-authored fixtures built to
   satisfy the stale check by construction (§3.4, §3.5).
6. **(Documentation defect, non-blocking)** The
   `confirmed_content_digest` schema field's own `description` is
   internally self-contradictory and has not been revised since 143E,
   independent of but related to the code defect (§3.2).

---

## 8. Recommended Resolution

**Classification: A — Verification implementation defect. No contract
issue exists. Implementation repair recommended.**

The `confirmation_binding` check in `governance/verification.py` should
be reconciled with CHGR-REQ-201's already-frozen construction rule. This
phase does not prescribe the exact replacement algorithm (that judgment,
and any consequent code change, belongs to the repair phase this finding
authorizes), but the architecture already exposes the needed signal: the
three verbatim-propagated sibling fields identified in §5 are internally
comparable for consistency without recomputing anything from the
record's own finalized content. The schema field description
(§3.2, §6) should also be reconciled with CHGR-REQ-085 as part of the
same repair, since it documents the defective behavior as if it were
intended.

No contract amendment is required or recommended.

---

## 9. Scope Boundary Compliance

This phase did not modify any contract, schema, production code,
verifier, or Publication Coordinator file. All bundle construction and
verification described above was executed in-memory and against
scratch-directory files outside the repository
(`$SCRATCHPAD/chgr_repro/*.json`); no repository file was created,
modified, or deleted by this investigation. `git status --short` is
identical (clean) before and after this phase's work. `pcae check`,
`pcae health`, `pcae doctor task-memory`, `pcae runtime inspect`, and
`pcae push check` all report unchanged, healthy state (§10).

---

## 10. Governance Validation

Run before and after the investigation, both times with identical
results:

```
git status --short          -> (clean)
pcae check                  -> PCAE check passed.
pcae health                 -> Overall status: healthy; Git status: clean
pcae doctor task-memory     -> Task memory: clean. No inconsistencies detected.
pcae runtime inspect        -> Runtime status: not_implemented; Execution
                                capability: unavailable (unchanged, observe-only)
pcae push check             -> Nothing to push. Mode: nothing_to_push
```

No governance state, strategic-lineage data, or runtime capability was
altered by this phase.

---

## 11. Overall Verdict

**ROOT CAUSE ESTABLISHED.**

The `CONFIRMATION_UNBOUND` defect is independently, directly, and
reproducibly demonstrated to originate solely in
`governance/verification.py`'s `confirmation_binding` check — specifically
`_confirmable_content_digest_of()` and its comparison at
`verification.py:379` — which implements a Phase-143E-era design
superseded, without corresponding update, by CHGR-REQ-201 at Phase 146B.
The contract, the schema-envelope requirements, and the Phase 146G
construction implementation are all correct and mutually consistent; none
require amendment. Classification **A**.

---

## 12. Recommended Next Phase

**146H.3 — Confirmation Binding Verification Repair**, authorized
narrowly to modify `governance/verification.py`'s `confirmation_binding`
check (and, as a directly consequential documentation fix, the
`confirmed_content_digest` field description in
`human_confirmation_evidence.schema.json`) to correctly reconcile
verification with CHGR-REQ-201's already-frozen construction rule,
without redesigning the verification subsystem, broadening acceptance
beyond what CHGR-REQ-201/085/§10 already require, or touching any other
check. This recommendation is not an authorization; per this phase's own
Human Authorization, no repair is enacted here.
