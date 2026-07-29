# Phase 146I — CHGR-001 Schema-Envelope Operational Readiness Assessment

**Mode:** Operational Readiness Assessment only. No production code,
contract, schema, manifest, fixture, or test file was modified, and none
is authorized by this phase. **Predecessor:** 146H.3V (VERIFIED WITH
NON-BLOCKING FINDINGS). **Runtime baseline:** Observed / observe /
unavailable (confirmed unchanged, before and after this assessment).

This phase does not authorize any repair, redesign, execution-capability
change, or Chapter 146 closure. The verdict below is a recommendation,
not an authorization.

---

## 1. Executive Summary

The CHGR-001 schema-envelope capability's full operational path —
readiness package → human confirmation → CHGR artifact construction →
schema-envelope validation → publication → persistence → post-publication
verification → inspection — was independently reconstructed from primary
sources and exercised live, end to end, through the real `pcae
decision-session` / `pcae governance-record` CLI, producing a genuine
four-artifact bundle, a successful verify/inspect pass, and a correct
digest-mismatch tamper rejection.

Construction, publication, persistence, and inspection are functionally
complete, deterministic, atomic, and fail-closed, matching CHGR-REQ-194
through CHGR-REQ-208. However, this assessment found that the
independent verification path's cross-artifact binding check
(`governance/verification.py`'s `_find_related`) matches a supplied
sibling artifact by `record_id` + `record_type` only and **never
cross-checks the referencing artifact's own declared `record_digest`**
against the sibling actually selected. Because `record_id` is disclosed
in plaintext inside the primary artifact (not a secret), this assessment
was able to fabricate a wholly unrelated confirmation artifact — different
subject, different confirmer, different content — relabel its `record_id`
to match, and have `pcae governance-record verify` report
`confirmation_binding: passed`. This is a new finding (Finding C, this
phase), and it directly changes the risk calculus underlying 146H.3V's
Non-Blocking classification of Finding A (order-dependent duplicate-
`record_id` resolution): 146H.3V's rationale rested on `record_id` being
"unguessable," which this assessment shows does not hold operationally.

**Overall verdict: NOT OPERATIONALLY READY**, scoped narrowly to the
independent verification/audit function within the CHGR-001 operational
path. Construction, publication, and persistence remain sound. No
production change was made; a narrowly-scoped repair phase is
recommended (§19).

---

## 2. Scope and Authorization

Authorized by the human-supplied Phase 146I prompt following Phase
146H.3V's completion. This is an assessment phase: read, exercise, and
classify actual behavior of the currently authorized CHGR-001
schema-envelope role. Explicitly **not** authorized: production code
change, verification/inspection code change, contract/schema/manifest/
fixture change, test repair, redesign of publication/identity/
relationships/lifecycle/authority, execution-capability addition, policy
or strategic-lineage change, or silent closure of the 146H.3V findings.
Section 11 (No-Go Boundary) below confirms none of this occurred.

### Bootstrap confirmation

- `git status --short`: clean throughout. `git rev-list --count
  origin/main..HEAD` = 0, `git rev-list --count HEAD..origin/main` = 0
  at phase start.
- `pcae session bootstrap --agent-id claude-code` (lock already held by
  this agent from the prior turn in this session; re-acquiring under
  `claude-local` correctly refused with "Agent lock already held by
  claude-code," confirming the lock-conflict guard functions): health
  healthy, check passed, task memory clean. Latest completed phase:
  146H.3V (completed, report: complete). Readiness reported "blocked"
  for the three routine, self-comparison reasons this chapter's prior
  assessments have already documented as cosmetic (stale active-task
  self-comparison, idle task not naming a phase, handoff predating the
  latest report) — none substantive.
- `pcae check` / `pcae health` / `pcae doctor task-memory`: passed /
  healthy / clean.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`,
  execution capability unavailable, 0 plugins, 0 capabilities.
- `pcae push check`: working tree clean, 0 unpushed commits, phase report
  trust and identity both passed, mode `nothing_to_push`.

**Bootstrap conclusion:** repository clean, branch `main`, local and
remote synchronized, no active governed phase in conflict, runtime
unchanged. A task contract scoped to this phase's assessment-only file
set was opened via `pcae task new` prior to any file write.

---

## 3. Authoritative Baseline Reconstruction

Reconstructed independently from primary sources (contracts, schema
resource files, source code, and phase reports used only as historical
cross-reference, never as a substitute for direct inspection). Full
detail preserved in the underlying evidence file produced during this
assessment (`phase146i_evidence.md`, retained under this session's
scratch directory, not part of the repository).

**Contracts (read directly, not from citation):**
- `CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (CHGR-001, **Version
  1.1**, FROZEN by 143B, revised by 146B §26). §26 holds
  CHGR-REQ-194–206 (13 requirements; CHGR-REQ-207/208 were added by
  146D's amendment). The requirement space runs 194–208, not to 209 as
  the phase-prompt range suggested — no requirement above 208 exists in
  this repository.
- `PUBLICATION_EXECUTION_CONTRACT.md` (PEC-001) — `PublicationCoordinator`
  is confirmed, by direct import-list inspection, to be the sole
  Publication Execution component (its own docstring cites PEC-REQ
  numbers verbatim, matched against the contract text).
- `INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001) — governs session/
  evidence/preview/confirmation/handoff; `coordinator.py`'s only
  dependency on this module is `PublicationHandoff`/
  `PublicationReadinessPackage`/`PublicationHandoffIncompleteError`,
  confirmed by direct import read.
- `INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md` (IWPC-001)
  — governs the `pcae decision-session` / `pcae governance-record
  publish` CLI surface; `commands/governance_record.py` cites IWPC-001
  §6/REQ-026/027/030/124/127/128/156 verbatim, matched against the
  contract.

**Requirement table (CHGR-REQ-194–206, from 146B §26, cross-checked
against 146F's implementation-responsibility mapping and 146G's actual
implementation):**

| ID | Area | Requirement |
|---|---|---|
| 194 | Schema Envelope | `schema_id`/`schema_version` sourced from `manifest.json`; `contract_version` unchanged |
| 195 | Canonical Identity | Four independently identified artifacts, never identity-sharing |
| 196 | Canonical Identity | Family-prefixed `record_id`, assigned atomically with Publication |
| 197 | Schema Envelope | SHA-256/canonical-JSON digest, computed independently per artifact |
| 198 | Lifecycle Integration | `lifecycle_state` fixed to `"published"` at construction |
| 199 | Coordinator Responsibilities | `authority_basis_claimed` remains correctly absent |
| 200 | Coordinator Responsibilities | `assurance_level` derived from `evidence_kind` (L0/L1 only) |
| 201 | Provenance / Schema Envelope | `human_confirmation_evidence` construction rule |
| 202 | Provenance / Schema Envelope | `governance_record_provenance` construction rule |
| 203 | Schema Envelope | `governance_record_integrity` construction rule |
| 204 | Validation | Fail-closed conformance gate before atomic write |
| 205 | Validation | Gate placement: construction-time, not post-hoc-only |
| 206 | Compatibility | Additive-only; §1–§25 unchanged |
| 207/208 | Requiredness (146D amendment) | `authority_basis_claimed` no longer unconditionally `required` in schema |

**Chapter history (146A→146H.3V), independently cross-checked:** 146C's
independent verification of 146B found a Blocking contradiction (schema
`required`-ness of `authority_basis_claimed` vs. CHGR-REQ-199's
permanent-absence rule); 146D resolved it; 146E independently verified
the resolution. 146G implemented the plan from 146F
(`governance/publication/record.py`: `build_publication_record`,
`_validate_chgr_bundle`; schema bump to `1.1`). 146H's independent
verification of 146G found the pre-existing, unmodified
`governance/verification.py` did not recognize the new `1.1` schema
version (Blocking), separately from a confirmation-binding defect; 146H.1
repaired the schema-version recognition (comparing against the
manifest's own per-family version instead of a hardcoded constant);
146H.2 root-caused and 146H.3 repaired the confirmation-binding defect;
146H.3V independently verified both repairs with two residual findings
(Finding A, Non-Blocking; Finding B, Informational) — the findings
re-examined by this phase.

**Schema resources** (`src/pcae/schema_resources/chgr/`, 12 manifest
entries): `human_governance_record` is the only family at schema version
**1.1**; all five other record families and the shared sub-schemas
remain at `1.0` — confirming 146G's bump and 146H's defect were scoped
to exactly this one family. The module's own `README.md` still states
"Not implemented here: ... production `create`/`confirm`/`publish`
commands" — this is now **stale documentation**: those commands are
implemented (Phase 145G onward) and were exercised live in §4. This is a
documentation-drift observation, not a functional defect.

**Direct code inspection confirmed, not merely cited:**
- `inspection.py` (334 lines): hardcodes
  `"validation": {"schema": "shape_conformant", "authority":
  "not_performed", "verification": "not_performed"}` unconditionally —
  no code path can make inspection claim authority or verification.
- `coordinator.py` (354 lines): its only `interactive_workflow` imports
  are the two publication-handoff types plus the incomplete-handoff
  error — matching its documented exclusion of session/orchestration/
  evidence/clarification/preview/confirmation internals.
- `verification.py:224`: the 146H.1 fix (`record.get("schema_version")
  != entries[0].get("schema_version")`, manifest-driven) is present, no
  hardcoded version constant remains in this module.
- `verification.py:349-355`: `_find_related` — see §5 and §10, Finding
  C.
- `inspection.py:42,328`: `SUPPORTED_SCHEMA_VERSION = "1.0"` — dead, see
  §13, Finding B.

---

## 4. End-to-End Operational Scenario

Performed live, entirely through real `python -m pcae ...` subprocess
invocations, from a clean scratch working directory (fresh `.pcae/`
state), reconstructing the full chain from the actual CLI test files
that exercise it (`tests/test_phase_145g3_decision_session_identity_binding.py`).

### 4.1 Commands and outcomes

```
decision-session create   --template-ref tmpl-1 --subject-ref subj-1 --owner-id alice
  -> session_id = CDS-94ec7956-ec2f-4927-8110-dce40d134f77
decision-session evidence  --declare ev-1 --as-identity alice
  -> EvidenceReady
decision-session select    --option-id opt-a --options-presented opt-a --options-presented opt-b
                            --template-version 1.0 --as-identity alice --rationale "because"
  -> DecisionSelected
decision-session preview   --as-identity alice
  -> preview_digest = 68a5210c...19cde
decision-session confirm   --preview-digest 68a5210c... --statement "confirmed" --as-identity alice
  -> Confirmed
decision-session readiness --as-identity alice
  -> package_id = prp-41596d88d6bf4d6684d1d1fd10a23c82, disposition: pending
governance-record publish prp-41596d88... --operator-id bob
  -> success: true, record_id = chgr-34fa3b983fe04b419e564b5118a7f83c
```

One reproducible operational-usability gap surfaced incidentally while
reconstructing this scenario: an out-of-format `--template-version v1`
(the schema requires `^[0-9]+\.[0-9]+$`) is accepted without complaint by
`decision-session select` and only rejected four commands later, at
`governance-record publish`, and the CLI surfaces a generic
`"internal_error"` rather than the specific, already-available
`ChgrSchemaConformanceError` naming the exact failing field/pattern. This
is recorded as Finding D (§13), not part of Findings A/B/C.

### 4.2 Persisted artifacts

Four files under `.pcae/publication-execution/records/`, one per family,
matching CHGR-REQ-195 ("four independently identified artifacts, never
identity-sharing"):

| record_id | record_type | schema_version |
|---|---|---|
| `chgr-34fa3b98...` | human_governance_record | **1.1** |
| `chgrconf-58cac80d...` | human_confirmation_evidence | 1.0 |
| `chgrintg-1c7b911b...` | governance_record_integrity | 1.0 |
| `chgrprov-baf3b501...` | governance_record_provenance | 1.0 |

The persisted `human_governance_record` carries `lifecycle_state:
"published"`, `assurance_level: "L0"`, `authority_basis_claimed` absent
(with an explicit `limitations` disclosure citing CHGR-REQ-199/207/208),
and correctly populated `*_ref` objects (`record_id`, `record_family`,
`record_digest`) for confirmation, provenance, and integrity.

### 4.3 Verification and inspection outcomes

- `pcae governance-record verify <HGR> --related <conf> --related <prov>
  --related <intg> --json` → `outcome: verified`, all seven checks
  (`schema_shape`, `digest_self_consistency`,
  `lifecycle_structural_legality`, `confirmation_binding`,
  `assurance_truthfulness`, `provenance_consistency`,
  `integrity_consistency`) `passed`; `template_resolution` `skipped`
  (no decision-template artifact exists in this Publication path).
  Exit 0.
- `verify` with **zero** `--related` siblings: `outcome: verified`
  (standalone checks only), the four cross-artifact checks explicitly
  `skipped` with a reason string — never silently treated as passed.
- `pcae governance-record inspect <HGR> --json` → `outcome: inspected`,
  `validation.authority: "not_performed"`, `validation.verification:
  "not_performed"` — inspection never over-claims.

### 4.4 Tamper and rejection

A field-level tamper (`rationale` edited post-persistence) re-verified
against the actual persisted file produced `outcome: rejected,
error_code: DIGEST_MISMATCH`, exit 1, with a message naming the exact
failure mode. `verify` performed no write or repair — confirmed
read-only by both code inspection and live behavior.

**Conclusion:** the entire construction → publication → persistence →
standalone-verification → inspection → tamper-rejection path was
exercised live through real production code end to end, with no
fallback to reimplementation. The one gap requiring adversarial artifact
fabrication (§5, §10) necessarily mixed CLI execution with direct
artifact construction — inherent to constructing an attack input, not a
substitute for exercising the verification code itself, which was run
through the real CLI/API in every case.

---

## 5. Functional Completeness Assessment

| Requirement | Status |
|---|---|
| Construct every required CHGR artifact | Satisfied — 4/4 artifacts constructed and persisted live (§4.2) |
| Correct schema identities/versions | Satisfied — `schema_id`/`schema_version` sourced from manifest per family, confirmed matching `manifest.json` exactly |
| Correct record/content digests | Satisfied for the primary record's own self-consistency (`digest_self_consistency` passed; tamper correctly rejected, §4.4). **Not fully satisfied** for cross-artifact digest binding — see Finding C (§10) |
| Cross-artifact bindings preserved | **Not satisfied** in the verification layer — `*_ref.record_digest` fields are populated at construction (matches CHGR-REQ-197/201/202/203) but are never read back by `verification.py`, making the "binding" check weaker than its name implies (§10) |
| Validate before persistence | Satisfied — malformed input (`template_version: "v1"`) is rejected by `_validate_chgr_bundle` before any `write_record` call; nothing partially persists (§10 in the underlying evidence; confirmed by code read of `coordinator.py`'s catch-before-write-loop structure) |
| Publish atomically | Satisfied — see §7 |
| Verify persisted artifacts afterward | Satisfied with limitations — standalone and self-consistency checks are sound; cross-artifact binding checks are not, per Finding C |
| Inspect without assuming authority | Satisfied — §4.3, §8 |
| Fail closed on invalid input | Satisfied for every construction/publication-time failure tested (§6); **not fully satisfied** for the specific verification-time binding-forgery case in §10 |

No CHGR-REQ-194–208 requirement was found unimplemented. The gap found
is in `governance/verification.py`, a pre-existing, unmodified module
that was never itself in Chapter 146's implementation scope but is a
required part of the operational path this phase was asked to assess
end to end.

---

## 6. Failure-Containment Assessment

All triggered against the real CLI/API against the live bundle from §4,
plus a second independently-published bundle (owner `carol`, subject
`subj-2`) for cross-bundle tests.

| Scenario | Result | Persisted? |
|---|---|---|
| Invalid readiness package (`template_version: "v1"`) | Rejected before publish; CLI surfaces generic `internal_error` (real cause available internally but swallowed by CLI error-mapping — Finding D) | No |
| Unsupported schema version (forced `9.9`) | `rejected`, `SCHEMA_INVALID` | N/A (verify read-only) |
| Malformed schema identity | `rejected`, `UNREGISTERED_SCHEMA` | N/A |
| Digest mismatch (primary tamper) | `rejected`, `DIGEST_MISMATCH` | N/A |
| Confirmation-binding mismatch (self-inconsistent forged sibling) | `rejected`, `CONFIRMATION_UNBOUND` | N/A |
| Provenance / integrity mismatch | Rejected by design (code-confirmed at `verification.py:414-435`, `:452`) | N/A |
| Missing sibling artifact | `verified`, cross-checks explicitly `skipped` — correct, not a false pass | N/A |
| Substituted sibling, real but wrong `record_id` (cross-bundle) | `verified`; `confirmation_binding: skipped` — correctly treated as absent | N/A |
| **Substituted sibling, forged `record_id` (impersonation)** | **`verified`; `confirmation_binding: passed`** for a wholly unrelated, content-mismatched artifact | N/A — **Finding C** |
| Duplicate sibling `record_id` (Finding A) | Outcome flips between `verified` and `rejected(CONFIRMATION_UNBOUND)` purely by `--related` argument order | N/A — **Finding A**, reassessed §10 |
| Reordered siblings, non-conflicting case | Identical outcome regardless of order | N/A |
| Tampering after publish | `rejected`, `DIGEST_MISMATCH`, tampered bytes remain on disk (verify does not repair — expected for a read-only tool) | N/A |

No partial canonical persistence, no lifecycle bypass, and no authority
escalation were observed in any scenario. The one false-success class
observed (forged-`record_id` impersonation, duplicate-order flip) is
confined to the standalone `verify`/`inspect` audit path, not the
publication/persistence path itself.

---

## 7. Atomicity and Persistence Assessment

`grep -rn "publication-execution/records" src/pcae` returns exactly one
writer: `PublicationRecordStore.write_record`
(`governance/publication/storage.py:89`), called only from
`coordinator.py`'s `execute()` bundle-write loop. `_validate_chgr_bundle`
raises before this loop runs for any invalid input (§6), so no partial
bundle is ever written for a rejected construction. Stable identifiers
(`uuid4()`-derived `record_id`s, §10) and final digests are assigned at
construction and never mutated afterward. `.pcae/publication-execution/
attempts/*.json` records an audit trail per attempt (PEC-REQ-043/105/106)
independent of the record store itself. No orphaned authoritative
artifact and no unverifiable successful publication were observed in any
live run in this assessment.

---

## 8. Verification and Auditability Assessment

An operator can locate persisted artifacts (`.pcae/publication-execution/
records/`), identify schema family/version from each artifact's own
`schema_id`/`schema_version` fields, and independently run `verify`/
`inspect` against them via CLI or the underlying API. Standalone checks
(`schema_shape`, `digest_self_consistency`, `lifecycle_structural_
legality`) are sound and were confirmed to fail closed under tampering.
**Cross-artifact checks are not fully trustworthy as evidence of
binding**: `confirmation_binding: passed` proves only that the *supplied*
candidate is internally self-consistent (its own `confirmed_content_
digest == preview_rendering_digest`), not that it is the specific
artifact the primary record's `confirmation_evidence_ref` names by
digest — because `record_digest` in every `*_ref` object is populated at
construction but never read back during verification (Finding C, §10).
A secondary, narrower instance of the same pattern was found in
`integrity_ref.record_digest`, which the primary artifact's own
`limitations` array already discloses as "a verification-layer
responsibility, never a schema-layer guarantee" — and which this
assessment confirms verification does not, in fact, discharge for that
particular field either (the check that does run,
`integrity.get("payload_digest") != declared_digest`, cross-checks a
different field, not `integrity_ref.record_digest` itself). This means an
operator or audit process currently **cannot** distinguish, from a
`verified` outcome alone, "this is genuinely the confirmation that was
bound at publication time" from "this is a self-consistent artifact
someone supplied with a matching label."

---

## 9. Determinism Assessment

Canonical serialization, digest computation, and standalone verification
results were confirmed stable across repeated runs and across CLI/API
invocation. Sibling argument ordering is **not** stable when siblings
conflict: identical duplicate-`record_id` sibling files, supplied in
reversed `--related` order, flip the outcome between `verified` and
`rejected(CONFIRMATION_UNBOUND)` (§10) — a pure function of argument
order, not flakiness. For the non-conflicting case (real, distinct
siblings in any order), results were confirmed identical regardless of
order. Repeated-process behavior (same input, separate process
invocations) was stable in every case observed.

---

## 10. Known-Finding Reassessment (§10 continues into Finding C, new)

### Finding A — Duplicate related `record_id`

**Mechanism (confirmed, `verification.py:349-355`):** `_find_related` is
a linear first-match scan over `related_records`, itself built in
`--related` argument order with no dedup or ambiguity check anywhere
upstream.

**Live reproduction:** two duplicate-`record_id` confirmation files
(one content-consistent "good," one content-mismatched "bad"), same two
files, reversed order:
- `bad, good` → `rejected, CONFIRMATION_UNBOUND`
- `good, bad` → `verified`

Identical inputs, reversed order, opposite outcome — deterministic, not
racy.

**Can normal production construction create true duplicates?** No —
every `record_id` is `uuid.uuid4().hex`-derived
(`governance/publication/record.py:88`), 122 bits of randomness, never
reused by construction.

**Can an operator/attacker supply duplicates to the CLI?** Yes — `
--related` accepts arbitrary caller-supplied file paths with no
provenance check, and nothing rejects two files sharing a manually-edited
`record_id` before `_find_related`'s selection point.

**Reassessment against 146H.3V's own rationale:** 146H.3V classified this
Non-Blocking on the premise that exploiting it "requires an attacker who
already possesses (or fabricates) two distinct artifacts sharing the
exact same `record_id` (... unguessable ... never reused by
construction)." This assessment's Finding C (below) shows that premise
does not hold operationally: the `record_id` an attacker needs is not
secret — it is disclosed in plaintext inside the very primary artifact
`verify` requires as input (`confirmation_evidence_ref.record_id`, etc.,
visible in §4.2's persisted JSON). Anyone who can read a published HGR
can read the exact `record_id` its confirmation sibling is expected to
carry, then fabricate a sibling with that ID copied in — no guessing,
brute force, or prior possession of a colliding artifact is required.
Combined with `record_digest` being unchecked (Finding C), the real
exploitable precondition is materially weaker than 146H.3V believed: "can
read one published HGR and can supply arbitrary files to `--related`" —
the tool's entire normal operating mode, not an edge case.

**Reclassification: Blocking** (revised from Non-Blocking). This
directly meets the Blocking criteria in this phase's own governing
instructions: "invalid artifacts can be accepted as valid" and "required
cross-artifact binding can be bypassed." Not repaired in this phase.

### Finding B — Dead inspection constant

`grep -n "SUPPORTED_SCHEMA_VERSION" src/pcae/governance/inspection.py`
returns exactly two lines: the definition (line 42) and its `__all__`
re-export (line 328). It participates in no comparison, gate, or
decision path anywhere in the 334-line file;
`inspect_artifact_at_path`'s schema-version handling relies entirely on
JSON-Schema validation plus a manifest-entry lookup. Confirmed dead code
with no operational effect, present in a read-only, non-authoritative
inspection module.

**Classification: Informational** (unchanged from 146H.3V). Risk:
none to current readiness; low future-maintenance risk (a future editor
could mistake it for load-bearing and wire it into a gate incorrectly,
or fail to update it if a real second-supported-version need arises).
Not repaired in this phase.

### Finding C — Cross-artifact `record_digest` not verified (new, this phase)

**Mechanism:** every `*_ref` object populated by
`build_publication_record` (`confirmation_evidence_ref`,
`provenance_ref`, `integrity_ref`) carries a `record_digest` field
(CHGR-REQ-197/201/202/203), but `verification.py`'s cross-artifact checks
never read `ref.get("record_digest")` at any point — confirmed by
reading the full 510-line file. `_find_related` matches on `record_id` +
`record_type` only; once a candidate is selected, `confirmation_binding`
checks only the *candidate's own* internal self-consistency
(`confirmed_content_digest == preview_rendering_digest`), never that the
candidate's own `record_digest` equals the value the primary record's
`confirmation_evidence_ref.record_digest` declares.

**Live demonstration:** a confirmation artifact from an entirely
different, independently-published bundle (different subject, different
confirmer identity, different rationale) — internally self-consistent on
its own terms — had only its `record_id` field rewritten to match
bundle 1's real confirmation `record_id`, with `record_digest`
recomputed for its own self-consistency (not to match bundle 1's
`confirmation_evidence_ref.record_digest`, which was left mismatched).
Verifying bundle 1's HGR with this forged file as `--related` produced
`outcome: verified`, `confirmation_binding: passed`.

**Assessment against this phase's own Blocking criteria:** this
satisfies "required cross-artifact binding can be bypassed" and "invalid
artifacts can be accepted as valid" directly. The `confirmation_binding`
check's name promises more than the code delivers: a `passed` result
does not prove the confirmation evidence supplied is the one the
publication actually bound, only that whatever was supplied is
self-consistent and correctly labeled.

**Classification: Blocking.** Scoped strictly to the independent
verification/audit function (`governance/verification.py`); does not
affect construction, publication, or persistence, which correctly
compute and record all `record_digest` values at write time — the gap is
that a *later, independent* verification pass does not read them back.
Not repaired in this phase.

---

## 11. Security and Authority Assessment

- Inspection never claims authority from schema validity —
  `InspectionObservation.to_dict()` hardcodes `authority:
  "not_performed"` unconditionally, confirmed by code read and live
  output (§4.3).
- `PublicationCoordinator` is confirmed the sole writer to
  `.pcae/publication-execution/records/` (single-writer grep, §7); no
  bypass path exists for CLI or Interactive Workflow code to write
  directly.
- No runtime execution capability was added, exercised, or observed;
  `pcae runtime inspect` reported the identical baseline before and
  after this assessment (§1 bootstrap, §17 close).
- Findings A and C together mean an artifact-*verification* consumer
  (not the publication path itself) can be induced to certify a forged
  binding — this is an authority-adjacent finding (a false
  `confirmation_binding: passed` could mislead a human or downstream
  process relying on `verify`'s output as evidence of actual
  confirmation), which is why both are classified Blocking rather than
  a narrower "verification cosmetics" issue.
- No schema-valid artifact was observed to self-authorize; every
  authority-relevant field (`authority_basis_claimed`) remained
  correctly and permanently absent in every construction path exercised.

---

## 12. Operational Usability Assessment

CLI JSON output is structured and consistent across `create` /
`evidence` / `select` / `preview` / `confirm` / `readiness` / `publish` /
`verify` / `inspect`, with explicit `skipped`-vs-`passed`-vs-`failed`
disclosure for cross-artifact checks and clear `error_code` values for
rejections (`DIGEST_MISMATCH`, `SCHEMA_INVALID`, `UNREGISTERED_SCHEMA`,
`CONFIRMATION_UNBOUND`) — an operator can generally understand a
rejection's cause from the JSON alone. The one usability gap found
(**Finding D**): a malformed `template_ref.version` (e.g., `"v1"`) is
silently accepted through four successive commands and only surfaces,
opaquely, as a generic `"internal_error"` at the final `publish` step,
even though the real cause (`ChgrSchemaConformanceError`, naming the
exact JSON-Pointer path and failing pattern) is available inside the
raised exception and is simply not propagated through the CLI's
error-mapping layer. **Classification: Non-Blocking** — no artifact is
persisted, no false success occurs, but diagnosability is materially
worse than it needs to be for a common operator mistake.

---

## 13. Compatibility and Regression Assessment

`fast_green` marker suite: **4391 passed, 0 failed** (107.41s). Targeted
sweep `-k "chgr or publication or governance or verification or
interactive_workflow"`, run to completion twice (parallel and serial):
9–10 failures out of ~4000 collected, **every one independently
root-caused** to either (a) a `python -m build`-availability mismatch
between `sys.executable` and the `PATH`-resolved interpreter on this
machine (affects only wheel/sdist packaging tests in
`test_chgr_packaging.py` and unrelated pre-Chapter-146 files such as
`test_cltr_authority_136ah_publication.py`), or (b) one pre-existing,
already-disclosed Group-10 naming-drift test
(`test_136u_no_runtime_code_references_group10_families_outside_schema_
resources`), or (c) one order/parallelism-dependent flake in an unrelated
prototype-introspection test, present only in the serial run. **Zero**
failures touch `governance/inspection.py`, `governance/verification.py`,
`governance/publication/*`, or `interactive_workflow/**`. This
corroborates rather than contradicts 146H.3V's own characterization of
the packaging-test class as environment-dependent; this assessment
additionally root-caused the specific interpreter-mismatch mechanism,
which 146H.3V's environment did not happen to trigger. A full
whole-repository unfiltered sweep was not run in this phase — a
disclosed scope limitation (§16), not a glossed-over gap — given
`fast_green`'s clean result and the targeted sweep's zero CHGR-attributable
failures.

CHGR schema-resource packaging (`chgr_root()`, `build_offline_registry()`,
`load_and_verify_manifest()`) was exercised directly in a fresh
interpreter: 12 manifest entries resolved cleanly, no
`SchemaRegistryError`/`ManifestIntegrityError`/`OSError`.

---

## 14. Readiness Criteria Matrix

| # | Criterion | Status |
|---|---|---|
| 1 | Contract implementation completeness | Satisfied |
| 2 | Schema and manifest coherence | Satisfied |
| 3 | Construction correctness | Satisfied |
| 4 | Cross-artifact binding correctness | **Not satisfied** — Finding C |
| 5 | Pre-persistence validation | Satisfied |
| 6 | Atomic persistence | Satisfied |
| 7 | Post-publication verifiability | **Not satisfied** — Findings A, C |
| 8 | Inspection availability | Satisfied |
| 9 | Deterministic behavior | Satisfied with limitations — nondeterministic only in the conflicting-duplicate-sibling case (Finding A) |
| 10 | Fail-closed behavior | Satisfied with limitations — fails closed in every scenario except the forged-binding case (Findings A, C) |
| 11 | Authority-boundary preservation | Satisfied |
| 12 | Operational error clarity | Satisfied with limitations — Finding D |
| 13 | Regression acceptability | Satisfied |
| 14 | Packaging/resource availability | Satisfied (environment-dependent packaging-test flakiness noted, not attributable to CHGR code, §13) |
| 15 | Recovery and troubleshooting adequacy | Satisfied with limitations — Finding D |
| 16 | Known-finding risk acceptability | **Not satisfied** — Finding A's original risk premise does not hold (§10); Finding C independently meets Blocking criteria |

---

## 15. Findings

| ID | Summary | Classification |
|---|---|---|
| A | Duplicate-`record_id` sibling resolution is first-match/argument-order-dependent; `record_id` is not secret, so this is operator/attacker-triggerable without prior possession of a colliding artifact | **Blocking** (revised from Non-Blocking) |
| B | `inspection.py`'s `SUPPORTED_SCHEMA_VERSION` constant is dead code, no decision-path effect | Informational (unchanged) |
| C | `verification.py` never cross-checks a `*_ref.record_digest` against the sibling artifact actually selected, so a forged, content-mismatched sibling with a copied `record_id` is accepted as bound | **Blocking** (new) |
| D | Malformed `template_ref.version` is accepted silently for four CLI steps, then rejected only as a generic `internal_error` at `publish`, though the specific cause is available internally | Non-Blocking |
| E | `src/pcae/schema_resources/chgr/README.md`'s "not implemented" disclosure is stale relative to the current, working `publish` pipeline (145G+, 146G) | Informational |

Findings A and C are closely related (both stem from `_find_related`'s
identity-only matching) but are reported separately: A is the
previously-known finding under reassessment; C is this phase's own new
discovery of the underlying mechanism that changes A's risk calculus. No
repair was made to either in this phase, per the No-Go Boundary.

---

## 16. Limitations

- A full, unfiltered whole-repository `pytest` sweep was not run
  (§13) — a scope/time-budget decision, not a hidden gap; the covered
  `fast_green` and targeted sweeps produced zero CHGR-attributable
  failures.
- The forged-sibling and duplicate-sibling adversarial cases required
  direct construction of attacker-style input files (there is no CLI
  verb to "fabricate a malicious artifact" — that is the nature of an
  attack input); every check that accepted or rejected these files ran
  through the real, unmodified `verify_artifact_at_path`/CLI, never a
  reimplementation.
- Decision-template artifact construction was not exercised
  (`template_resolution` reported `skipped` in every live run) — the
  currently authorized Publication path does not produce a
  `decision_template` CHGR artifact, so this is expected, not a gap in
  this assessment's coverage.
- This assessment did not attempt to measure or characterize
  concurrent/simultaneous publication attempts (race conditions across
  two simultaneous `publish` calls); the atomicity assessment (§7) rests
  on single-writer code structure, not a live concurrency stress test.

---

## 17. No-Go Confirmation

`git status --short` was re-run after every write in this phase and
confirms only the following file classes were touched: this canonical
report (`docs/PHASE_146I_*.md`), task-lifecycle files
(`tasks/active/**`, `tasks/DONE.md`), `PROJECT_STATUS.md`,
`CHANGELOG.md`, and `.pcae/phase-completion-metadata.json`/
`phase-completion-report.md` — the standard governance-bookkeeping set.
No production code (`src/pcae/**`), contract (`docs/contracts/**`),
schema/manifest (`src/pcae/schema_resources/**`), or test
(`tests/**`) file was modified. `.pcae/strategic-lineage.json` was not
written to. `pcae runtime inspect` reports the identical baseline at
close (§18) as at bootstrap (§3). No finding from 146H.3V (or this
phase's new Finding C) was silently closed — both are explicitly carried
forward with an explicit classification.

---

## 18. Governance Validation (re-run at close)

- `pcae check`: passed.
- `pcae health`: healthy, git status clean.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae runtime inspect`: `Observed` / `observe` / `unavailable`,
  execution capability unavailable, 0 plugins, 0 capabilities —
  unchanged from bootstrap.
- `pcae push check`: re-run after this report and task-lifecycle files
  are staged, confirming readiness before the commit/push sequence.
- No policy or strategic-lineage change occurred.

---

## 19. Overall Verdict

**NOT OPERATIONALLY READY**

This verdict applies only to the currently authorized CHGR-001
schema-envelope role, and specifically to its independent
verification/audit function. Construction, publication, and persistence
were independently exercised live and found functionally complete,
atomic, and fail-closed. The verification path
(`governance/verification.py`, pre-existing and not itself part of
Chapter 146's implementation scope, but a required stage of the
operational path this phase was asked to assess) contains two Blocking
findings (A, reclassified; C, new) that together mean a `verified`
outcome for `confirmation_binding` can be produced for a forged sibling
artifact, given only read access to one published Human Governance
Record and the ability to supply arbitrary files to `--related` — the
tool's normal operating mode, not a privileged or unlikely precondition.

This verdict does not imply any runtime execution capability, autonomous
authority, or broader Interactive Workflow / Publication chapter
readiness beyond the CHGR-001 schema-envelope role specifically assessed
here.

---

## 20. Recommended Next Phase

**146J — CHGR Verification Cross-Artifact Digest-Binding Root-Cause
Resolution** (or equivalently-named narrowly-scoped repair phase),
addressing, at minimum:

1. `_find_related` (or its caller) cross-checking a selected sibling's
   own `record_digest` against the referencing `*_ref.record_digest`
   before treating any cross-artifact check as `passed` (closes Finding
   C and, as a direct consequence, Finding A's exploitable path).
2. An explicit ambiguity/duplicate-`record_id` guard in the
   `--related` ingestion path, independent of (1), as defense in depth.
3. Root-causing the same pattern for `integrity_ref.record_digest`
   (§8), which this assessment found is separately never independently
   verified.

Recommended scope explicitly excludes: publication/coordinator/identity/
lifecycle redesign, schema/contract amendment, and Findings B/D/E (which
remain open as Informational/Non-Blocking housekeeping items, to be
tracked and disposed of at whatever phase ultimately assesses Chapter
146 closure — not this one).

This recommendation is not an authorization.
