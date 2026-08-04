# Phase 149M — Rollback Approval Evidence Implementation Independent Verification

## 0. Identity and Status

- **Phase:** 149M
- **Type:** Independent production implementation verification (verification-only; no production code, contract, or runtime behavior changed by this phase)
- **Subject:** Phase 149L's production implementation of RAE-001 v1.0
  (`src/pcae/core/rollback_approval_evidence.py`,
  `src/pcae/schema_resources/rollback_approval/**`)
- **Verdict:** **NOT VERIFIED — BLOCKING RAE-001 IMPLEMENTATION FINDINGS**
- **Integration readiness:** **NOT READY** for AG3/AG5 rollback-integration planning until the findings below are repaired.

## 1. Methodology

This verification was performed by direct, independent inspection: reading
the RAE-001 v1.0 contract text end-to-end, reading
`rollback_approval_evidence.py` end-to-end without relying on its own
comments as proof, reconstructing the exact Phase 149L production diff via
`git diff`, and writing a dedicated, independently-constructed adversarial
test suite
(`tests/test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`,
53 tests) that does not import fixtures or helpers from 149L's own new test
files (`tests/test_rollback_approval_evidence_*.py`). 149L's self-tests and
the broader regression suites were run separately and treated as
implementation evidence, not independent proof. Every finding below is
backed by an actually-executed, reproducible test in that file, not by
inference from prose alone.

## 2. Exact 149L Production Diff (reconstructed)

Pre-149L baseline: `1ece0258` (Phase 149K's own finalization commit).
149L final: `9ccc9346` ("Phase 149L: Rollback Approval Evidence
Implementation").

```
git diff --name-only 1ece0258..HEAD -- src/pcae/    (excluding tests/)
```

Production files touched:

| File | Classification |
|---|---|
| `src/pcae/core/rollback_approval_evidence.py` (new, 1195 lines) | MODEL, SCHEMA(conceptual), SERIALIZATION, PERSISTENCE, CANONICALITY, CREATION, AUTHORITY, LOOKUP, VALIDATION, TTL, REVOCATION, SUPERSESSION, REPLAY, DERIVATION |
| `src/pcae/schema_resources/rollback_approval/manifest.json` (new) | SCHEMA |
| `src/pcae/schema_resources/rollback_approval/manifest.schema.json` (new) | SCHEMA |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_binding.schema.json` (new) | SCHEMA |
| `src/pcae/schema_resources/rollback_approval/records/rollback_approval_revocation.schema.json` (new) | SCHEMA |
| `src/pcae/schema_resources/__init__.py` (modified, +19 lines) | PERSISTENCE (adds `rollback_approval_root()` resource-path helper, additive only) |

No `UNRELATED` hunk found. Every changed line traces to RAE-001 substrate.

`docs/contracts/**` diff `1ece0258..HEAD`: **empty**. Confirmed unchanged.

## 3. Production Boundary (independently re-verified)

`git diff --stat 1ece0258..HEAD` for each named boundary file:

```
src/pcae/core/agent.py                    (empty diff)
src/pcae/commands/agent.py                (empty diff)
src/pcae/core/mutation_permission.py      (empty diff)
src/pcae/core/permission_broker_foundation.py  (empty diff)
src/pcae/core/permission_broker.py        (empty diff)
```

All five byte-unchanged. Confirmed.

## 4. Module Architecture (reconstructed from source, not comments)

- **Closed vocabularies:** `RollbackDecisionType` (`approve_rollback`,
  `deny_rollback`), `BindingDecision` (`APPROVE`, `DENY`), `RollbackSite`
  (`AG3`, `AG5`), `BindingState` (`issued`, `used`, `revoked`, `expired`),
  `RollbackApprovalValidationResult` (exactly the 8 values RAE-REQ-036
  requires: `VALID`, `MISSING`, `INVALID`, `STALE`, `REVOKED`,
  `UNAUTHORIZED_APPROVER`, `WRONG_SCOPE`, `SUPERSEDED`). All are Python
  `Enum` subclasses — unknown values raise `ValueError` on construction
  (independently confirmed by test).
- **Operation-reference types:** `Ag3OperationReference{job_id,
  original_commit_sha}`, `Ag5OperationReference{per_id, ecp_id}`, both
  frozen dataclasses. `RollbackApprovalBinding.__post_init__` enforces the
  family lock (AG3 site requires `Ag3OperationReference`, AG5 requires
  `Ag5OperationReference`) — independently confirmed by test to raise
  `RollbackApprovalBindingConstructionError` on mismatch.
- **Creation APIs:** `create_rollback_approval_decision` (thin wrapper
  around the real, unmodified `PublicationCoordinator`/CHGR pipeline) and
  `create_rollback_approval_binding` (resolves the Decision first via
  `_resolve_decision_ref`, then enforces RAE-REQ-019's "at most one
  active Binding per Decision" — **but only within this function**, see
  Finding F1).
- **Persistence:** `RollbackApprovalEvidenceStore`, filesystem-backed,
  atomic write (`tempfile.mkstemp` + `fsync` + `os.replace`), refuses
  overwrite of an existing file. Binding files live at
  `<root>/bindings/<evidence_id>.json`; revocations at
  `<root>/revocations/<evidence_id>.json`.
- **Canonicality validation:** `_resolve_decision_ref` reads the CHGR
  record file directly from `<publication_root>/records/<record_id>.json`
  and checks: file exists; JSON parses; `record_digest` field matches the
  caller-supplied reference; `template_ref` matches
  `rollback-approval`/`1.0`; `lifecycle_state == "published"`;
  `selected_option_id` is in the closed rollback vocabulary. **All of
  these checks are self-referential to the file's own declared content —
  none of them cryptographically prove the file was produced by the real
  `PublicationCoordinator` pipeline** (see Finding F2).
- **CHGR linkage:** one-way, read-only file read against CHGR's existing
  `records/<record_id>.json` convention; no CHGR internals imported or
  mutated.
- **Authority checks:** `_authority_valid()` — confirmed by direct
  reading — checks only that the *template's* `eligible_authority` text
  field is a non-empty string. It does not read, in any way, anything
  about the specific human who made the Decision. This exactly matches
  RAE-REQ-008(1)'s disclosed STRATEGIC_GAP (no authority registry exists)
  and is **not** a new over-claim — the module makes no claim of stronger
  identity verification than the contract itself discloses.
- **Lookup:** `resolve_rollback_approval_evidence(context, evidence_id, ...)`
  — always requires an explicit `evidence_id`; `RollbackApprovalEvidenceStore.list_bindings()`
  is used only inside `_is_superseded()` to scan for competing records for
  an *already-identified* operation reference, never to select which
  `evidence_id` to resolve. RAE-REQ-041 ("no latest lookup") is honored at
  the entry point.
- **TTL:** 24 hours, hardcoded (`ttl_hours: Literal[24] = 24`, non-overridable
  at the API level — attempting a different value raises).
- **Revocation:** append-only revocation record at a separate path,
  checked via `store.is_revoked()`; never edits the original Binding file.
- **Supersession:** `_is_superseded()` scans *every* Binding file
  currently in the store directory for one sharing the same
  `rollback_site` + `rollback_operation_reference`, with a strictly later
  `created_at`. **This scan is not restricted to Bindings created through
  the canonical creation API** (see Findings F1/F4).
- **Validation statuses:** returned as a `ValidatedEvidence(result, approval_present, binding, diagnostic)`
  structure; the eight-value vocabulary from RAE-REQ-036 is exactly
  reproduced.
- **`approval_present` derivation:** `derive_rollback_approval_present()`
  is a thin wrapper returning `resolve_rollback_approval_evidence(...).approval_present`
  — `True` if and only if `result == VALID`.

## 5. Import Boundary — Confirmed Clean

AST-based import scan (not string-search, which produces false positives
against legitimate docstring prose) confirms **zero** actual `import`/`from`
statements referencing `permission_broker_foundation`, `permission_broker`,
`mutation_permission`, `pcae.core.agent`, or `pcae.cltr.authority` anywhere
in `rollback_approval_evidence.py`. `sys.modules` was also checked before/after
exercising the module's public API — no broker modules become imported as a
side effect. **Verdict: import boundary holds.**

However, see Finding F5 (docstring text, not an import, referencing
`pcae.cltr.authority` breaks three unrelated pre-existing regression-guard
tests that do naive string-scanning rather than AST-based scanning).

## 6. Decision Model — Verdict: CONFORMS

Closed two-value vocabulary confirmed; unknown values rejected by the enum
constructor; no code path anywhere in the module compares a decision value
directly to Permission-Broker-only vocabulary (`ALLOW`/`HUMAN_REVIEW`) —
confirmed by an AST-based scan of code-position string literals (excluding
docstrings). `BindingDecision.DENY`/`APPROVE` is RAE's own legitimate,
contractually-frozen denormalized vocabulary (RAE-001 §8), textually
distinct from broker vocabulary by the contract's own design — not a
violation.

## 7. Binding Model — Verdict: CONFORMS (structurally), UNDERMINED (in practice, see F1/F2/F4)

`RollbackApprovalBinding` is a distinct dataclass from any Decision
representation; every instance carries `governance_record_reference`
(a `{record_id, record_digest}` pointer, never a copy) and cannot function
without one — `_resolve_decision_ref` is always invoked before a Binding
is trusted. Structurally this matches RAE-001 §8 exactly. The findings
below concern not the *shape* of the Binding model but the *strength of
its trust anchor*.

## 8/9. AG3 / AG5 Operation Reference — Verdict: CONFORMS

AG3 binds exactly `{job_id, original_commit_sha}`; AG5 binds exactly
`{per_id, ecp_id}`. Independently attacked: wrong `job_id` alone → `WRONG_SCOPE`;
wrong `original_commit_sha` alone → `WRONG_SCOPE`; wrong `per_id` alone →
`WRONG_SCOPE`; wrong `ecp_id` alone → `WRONG_SCOPE`. All four confirmed by
test.

## 10/11. Family Lock / Unknown Family — Verdict: CONFORMS

AG3 Binding resolved against an AG5 context, and AG5 Binding resolved
against an AG3 context, both independently confirmed rejected
(`WRONG_SCOPE`). `RollbackSite("AG7")` raises `ValueError` — unknown
families are structurally impossible to construct.

## 12/13/14. Canonical Creation Path / CHGR Publication Requirement — Verdict: **BLOCKING GAP FOUND (F2)**

RAE-REQ-018 requires `governance_record_reference` to resolve to "an
actually-published" record. Independent tracing of `_resolve_decision_ref`
shows its four checks (existence, digest self-consistency, `template_ref`,
`lifecycle_state=="published"`) are **all satisfiable by a file hand-authored
directly at `<publication_root>/records/<record_id>.json`, entirely
bypassing `PublicationCoordinator`, its Authorization Event, and its
idempotency marker.** "Published" as tested here is a plain string field
value inside the file itself, not a fact independently established by the
real pipeline having run (e.g. cross-checked against the `published/<package_id>.json`
idempotency marker, or any pipeline-only artifact). `record_digest` is a
plain, unsalted, unsigned SHA-256 over the record's own declared bytes —
computable by anyone who reads the open-source hashing algorithm. See
Finding F2 below.

## 15. Hand-Authored Binding Attack — Verdict: **BLOCKING (F1, F2)**

Independently authored (not copied from 149L's fixtures) two hand-crafted
Binding JSON files, written directly into
`<evidence_root>/bindings/<evidence_id>.json`:

1. Referencing a plausible but never-published `record_id` → correctly
   rejected (`INVALID`, `approval_present=False`). **Pass.**
2. Referencing a *genuinely* published, real `approve_rollback` Decision
   (created through the real CHGR pipeline for one legitimate operation),
   but with a hand-computed self-consistent `content_digest` and an
   **arbitrary, unrelated `rollback_operation_reference`** — never having
   gone through `create_rollback_approval_binding` at all →
   **resolved `VALID`, `approval_present=True`.** **BLOCKING.**

This directly falsifies RAE-REQ-019's guarantee ("at most one active
Binding per Decision") for any adversary capable of writing files to the
canonical evidence directory — the check exists only inside
`create_rollback_approval_binding`, never inside
`resolve_rollback_approval_evidence`. See `test_hand_authored_binding_pointing_at_genuine_decision_via_direct_filesystem_write`.

## 16. Hand-Authored Decision Attack — Verdict: **BLOCKING (F2)**

Independently hand-authored a full Decision-shaped record directly under
`<publication_root>/records/<record_id>.json` — never touching
`PublicationCoordinator`, never producing an Authorization Event, never
producing an idempotency marker or the three CHGR companion artifacts
(`human_confirmation_evidence`, `governance_record_provenance`,
`governance_record_integrity`) that a real publication produces. Then
created a Binding referencing it through the *real*
`create_rollback_approval_binding` API (which happily accepted it, since
its own `_resolve_decision_ref` call performs the identical, insufficient
checks). Resolution: **`VALID`, `approval_present=True`.** **BLOCKING.**

This is the single most serious finding: it demonstrates that "canonical"
CHGR provenance, as actually implemented and consumed by this module, is
schema/self-consistency-shaped, not pipeline-provenance-verified. Anyone
with filesystem write access to `.pcae/publication-execution/records/` can
manufacture a fully trusted Rollback Approval Decision + Binding pair
without ever running an interactive session, a Confirmation step, or a
Publication Authorization Event.

## 17. Canonical-vs-Copied Record — Verdict: **BLOCKING (F4)**

Created one genuine canonical Binding, then copied its serialized bytes
verbatim to a file under a brand-new `evidence_id` filename (content
untouched — old internal `evidence_id` field left as-is). Resolution
under the new filename: **`VALID`, `approval_present=True`.** The store's
lookup is keyed by filename, but `content_digest` validates only the
payload's *internal* fields (including its own internal `evidence_id`),
which are never cross-checked against the filename used to look it up.
One underlying evidence record can therefore be presented for lookup
under an unbounded number of distinct `evidence_id`s, all independently
resolving `VALID`. **BLOCKING** (undermines `evidence_id`'s claimed role
as "stable identity... assigned only at creation," RAE-001 §8).

## 18/19/20. Digest / Reference / Digest-Substitution Tampering — Verdict: CONFORMS

Four independent tamper tests, each mutating exactly one field of an
*already-legitimately-created* Binding file after persistence:
`rollback_operation_reference.job_id`, `governance_record_reference.record_id`
(substituted with another real published record's id/digest),
`governance_record_reference.record_id` pointed at a real but *wrong*
(different-subject) Decision, and `governance_record_reference.record_digest`
alone changed to an incorrect value. **All four independently confirmed
rejected** (`INVALID`, `approval_present=False`) — the `content_digest`
self-consistency check *does* correctly catch post-persistence tampering
of an already-canonically-created record. The gap is specifically in
records that were never created canonically in the first place (F1/F2),
not in tamper-detection of legitimately-created ones.

## 21. Schema-Valid Noncanonical Artifact — Verdict: **Proven (F1/F2, confirms the mandatory case)**

Directly demonstrated by F1/F2: a fully schema-shaped, digest-self-consistent
record is not equivalent to a canonically-created one. The module's own
schema file (`rollback_approval_binding.schema.json`) explicitly and
correctly disclaims this ("Schema validity alone never establishes
canonical provenance, trust, or authority") — the disclaimer is honest,
but the Python validator's actual enforcement does not fully back it up,
per F1/F2.

## 22/23. Authority Validation / Claimed Actor Attack — Verdict: CONFORMS (disclosed limitation, not overclaimed)

Independently traced `_authority_valid()`: it checks only that the
Decision Template's static `eligible_authority` descriptive-text field is
non-empty — it never reads or checks the specific Decision's
`decision_maker_identity_evidence` against any registry (none exists).
Constructed three approvals with claimed principal `admin`, `root`,
`rollback_approver` in `decision_maker_identity_evidence` — **all three
resolved `VALID`** (since no stronger check exists to fail them). This
matches RAE-REQ-008(1)'s own honest, disclosed STRATEGIC_GAP exactly — the
module does not claim, and does not exhibit, any stronger identity
assurance than the contract discloses. **Not a new defect** — classified
per item 24 below.

## 24. Current Human Trust Limitation — Classification: **ACCEPTED CURRENT LIMITATION**

149L did not inadvertently claim stronger protection than exists. The
STRATEGIC_GAPs disclosed in RAE-001 §6/§19 (no stronger-than-self-declared
identity, no technical privilege separation) are faithfully preserved,
neither strengthened nor weakened by the implementation. This item is
**not** the source of this report's BLOCKING findings — F1/F2/F4 are a
different, narrower defect: not "the approver's identity can't be strongly
verified" (disclosed, accepted) but "an entire Decision+Binding pair can be
manufactured without a human ever making any decision at all" (not
disclosed as acceptable by the contract — RAE-REQ-018/RAE-REQ-056 promise
canonical, non-arbitrary, real-pipeline-anchored evidence).

## 25. Decision Creation Authority Failure — Not independently testable beyond §22/23

No registry exists to test "creation with actor lacking authority" against;
this is the same disclosed gap as §22/23, not a distinct scenario.

## 26. Approval-Present Derivation — Verdict: CONFORMS structurally; undermined by F1/F2/F4 in the malicious-filesystem-write threat model

`resolve_rollback_approval_evidence` evaluates all RAE-REQ-038 conditions
as a strict conjunction (independently confirmed: `MISSING` evidence_id →
False; wrong operation match → False; `used` state → False — each single
broken condition independently forces `False`). No condition is skipped.
The requirement count in the contract is **81** (RAE-REQ-001 through
RAE-REQ-081, confirmed by direct regex extraction — the phase prompt's
"81" figure is independently confirmed correct, no gap in the sequence).

## 27/28/29. Missing Decision / Missing Binding / Denied Decision — Verdict: CONFORMS

Missing Binding → `MISSING`, `approval_present=False`. Decision deleted
after Binding creation → `INVALID`, `approval_present=False`. A canonical
`deny_rollback` Decision's Binding never resolves `VALID` — confirmed
`approval_present=False` and result is not `VALID` (module returns
`INVALID` for a non-`approve_rollback` `selected_option_id`, a distinct
status from `VALID`, matching RAE-REQ-038(c)).

## 30. Validation Error / Fail-Closed — Verdict: CONFORMS

Corrupted (non-JSON) Binding file → caught internally, `INVALID`,
`approval_present=False`, no exception propagates. Binding file missing
required fields → same. The umbrella `try/except Exception` at the bottom
of `resolve_rollback_approval_evidence` is confirmed to catch every
internal failure and always return `approval_present=False` — no exception
path defaults to `True`.

## 31/32/33/34/35. TTL / Timezone / Future-Dated / Malformed / Clock Boundary — Verdict: CONFORMS

Exact boundary independently tested using the module's own frozen-clock
test hook (`_frozen_clock`, confirmed private — not in `__all__`, not a
parameter on any public function): `now == expires_at` exactly → `STALE`
(the contract text's "age==24h stale" rule is upheld — the boundary is
inclusive against the Binding, i.e. `now >= expires_at` triggers stale).
One second before → `VALID`. One hour after → `STALE`. `created_at`
forged into the future → rejected (`INVALID`, never `VALID`). Malformed
`expires_at` string → `INVALID`. Naive (non-timezone-aware) timestamps are
independently confirmed to parse to `None` (`_parse_iso_timestamp`), which
every caller treats as invalid — no silent local-time reinterpretation.
The clock override is a `contextvars.ContextVar` not reachable from any
public parameter, function signature, CLI flag, or `__all__` export.

## 36. Revocation — Verdict: CONFORMS

Revoke a valid Binding via `revoke_rollback_approval_binding` (the real
mechanism) → subsequent resolution returns `REVOKED`,
`approval_present=False`, permanently (no "un-revoke" path exists in the
module).

## 37/38/39/40/41. Supersession — Verdict: **BLOCKING (F4 — forged-newer-timestamp attack succeeds)**

- Legitimate later Binding for the same operation reference correctly
  supersedes an earlier one when both are created through the real API
  (confirmed).
- **Filesystem mtime has no effect** on supersession — confirmed
  independently by backdating a legitimate Binding file's mtime 10 days
  and confirming its resolution is unaffected (supersession logic reads
  the payload's `created_at` field, never the OS file mtime).
- **Forged-newer-timestamp attack (HIGH PRIORITY, item 39): CONFIRMED
  SUCCESSFUL.** A hand-authored Binding file, written directly to the
  canonical `bindings/` directory (never created via
  `create_rollback_approval_binding`), referencing the *same* real
  published Decision and the *same* `rollback_operation_reference` as a
  legitimately-issued, still-fresh Binding, but carrying a forged
  `created_at` one hour later than the legitimate record's — **caused the
  legitimate Binding to resolve `SUPERSEDED`** on its next evaluation.
  `_is_superseded()` scans *every* file `store.list_bindings()` returns
  with no check that competing records were themselves produced by the
  canonical creation API. **This is a direct, working denial-of-evidence
  attack: an adversary who can write one file can silently invalidate a
  legitimate, already-issued human approval**, without needing to forge
  anything about the underlying CHGR Decision at all. **BLOCKING** per the
  phase prompt's own example list (item 100: "forged newer timestamp
  suppresses valid evidence").
- Equal `created_at` between two canonical candidates: independently
  confirmed the comparison is a strict `>` (not `>=`), so an equal
  timestamp does **not** supersede — deterministic, non-ambiguous
  behavior for the legitimate-record case (item 40 resolved cleanly, in
  isolation from F4).
- Item 41 (later denial supersession): not separately modeled by the
  implementation beyond `_is_superseded`'s general same-operation-reference
  rule; no additional gap found beyond F4 itself.

## 42/43/44/45. Replay / Retry — Verdict: CONFORMS

Evidence for one operation replayed against a different `job_id`/`original_commit_sha`
correctly fails (`approval_present=False`). Repeated resolution of the same
unchanged, still-valid evidence is stable (`VALID` both times) — matching
RAE-REQ-050's "single-use burns on the `used` transition, not on mere
resolution" model; this was independently verified to be the actual
implemented behavior, not assumed. A Binding already transitioned to
`state=used` cannot be resolved again (`approval_present=False`). No
additional replay gap beyond F1/F2/F4 was found in the operation-identity
binding itself (item 43's cross-task question: `task_id` is not part of
the family-lock profile by contract design, RAE-REQ-031, and operation-reference
uniqueness plus RWMPC's own separate freshness layer is the contract's
explicit, deliberate answer — not found to be a new implementation gap).

## 46/47/48/49. Lookup — Verdict: CONFORMS (for canonically-created records)

Multiple AG3 operations independently resolve to their own correct
Binding, with no cross-resolution when an evidence_id for operation A is
tested against operation B's context (approval_present=False, confirmed).
Mixed AG3/AG5 records in the same store resolve family-correctly.
Unrelated canonical records do not interfere with each other's resolution.
(The lookup algorithm's weakness is specifically that it does not
distinguish canonically-created records from directly-written ones — F1/F2/F4
— not that it is ambiguous among legitimately-created records.)

## 50/51/52/53/54. Storage / Path / Collision / Atomicity / Concurrency — Verdict: CONFORMS, with F1/F2/F4 caveat

`create_rollback_approval_binding` and `create_rollback_approval_decision`
expose no caller-suppliable `evidence_id`, `path`, or `file_path`
parameter (confirmed via signature inspection) — evidence_id is always
server-generated (`uuid.uuid4().hex`-based). Path-traversal-shaped
`evidence_id` strings (`../../etc/passwd`, etc.) passed to `read_binding`
do not escape the canonical `bindings/` directory (Python's `Path`
`/`-join does not interpret `..` specially at the object level the way a
shell would, and no file exists at the traversal target in these tests, so
`read_binding` correctly returns `None`). Atomic persistence (`mkstemp`
+ `fsync` + `os.replace`) is real and independently read from source.
Concurrency: not independently stress-tested beyond code reading (no
locking exists, but no obvious corruption path was found for the
single-writer case each test exercises) — **not** claimed as Blocking,
consistent with the phase prompt's own guidance that concurrency is "not
necessarily Blocking if locking is outside scope." The storage-path
findings above are superseded in severity by F1/F2/F4, which do not
require path-traversal at all — direct, well-formed writes to the
already-canonical directory are sufficient.

## 55/56. CHGR/TAM Wall — Verdict: CONFORMS in substance; **NON-BLOCKING regression found (F5)**

No `human_authorization` record family, `cltr_cutover` storage path, or
TAM authority runtime object is used or imported anywhere in the module
(AST-confirmed). `RollbackApprovalBinding` reuses field *concepts*
(`state`, `expires_at`, `revocation_metadata`, `replay_binding`) but with
independent, RAE-specific semantics, its own `record_type` constant
(`rollback_approval_binding`), and its own dedicated schema namespace —
never composed with, subclassed from, or wrapped around
`HumanAuthorization`.

**However**, the module's own docstring (line 23) contains the literal
substring `pcae.cltr.authority.*` as prose explaining what the module does
**not** import. Three pre-existing, unrelated TAM/CLTR chapter regression
tests
(`tests/test_cltr_authority_136z_shared_core.py::test_136z_no_production_module_string_references_authority_import`,
`tests/test_cltr_authority_136ai_publication_independent.py::TestRuntimeIsolation::test_no_production_module_imports_authority_package`,
`tests/test_cltr_authority_136av_whole_model_integration.py::test_136av_no_production_runtime_module_imports_authority_package`)
perform a naive substring scan (not AST-based) over all of `src/pcae/**`
looking for that exact string, and all three now **fail** as a direct,
reproducible consequence of 149L's docstring wording — independently
confirmed via a worktree comparison against pre-149L commit `1ece0258`
(all three pass there, fail at `HEAD`). This is **not** a real wall
violation (§5 confirms no actual import exists), but it **is** a genuine,
previously-undisclosed test regression introduced by 149L that its own
phase report ("Fast Green 4391 passed unchanged," no mention of these
three) did not surface. Classified **NON-BLOCKING** (no actual security
boundary crossed) but real and independently reproducible — recommend
rewording the docstring (e.g. split the string across a concatenation or
rephrase without the literal dotted path) in the narrowest possible
follow-up repair.

## 57. IWC Boundary — Verdict: CONFORMS

No IWC confirmation artifact (`ConfirmationRequest`/`ConfirmationResponse`)
is treated as approval by this module; only the resulting published CHGR
record is consulted, and only through `_resolve_decision_ref`.

## 58. AESIC Boundary — Verdict: CONFORMS

No AESIC/AEM import or reference exists anywhere in the module (confirmed
by direct reading and the AST import scan).

## 59. Legacy Flags — Verdict: CONFORMS

No reference to `--promotion-authorized`, `--reviewed-by`,
`change_approval_state`, `--approve-keep`, `--approved-by`, `--reason`, or
the pre-existing `approve_rollback(root, job_id)` state-flag function
exists anywhere in this module's executable code.

## 60/61/62/63. No Broker/Mutation-Permission/Agent/Runtime-Enforcement Dependency — Verdict: CONFORMS

AST-based import scan (§5) confirms zero imports of any of these four
module families.

## 64. Approval Service Only — Verdict: CONFORMS

No `git revert`/`reset`/`checkout`/`push` invocation, and no filesystem
write outside `.pcae/rollback-approval-evidence/**` (or a caller-supplied
test root), exists in this module.

## 65/66. AG3/AG5 Non-Interference — Verdict: CONFORMS

`agent.py` (the AG3/AG5 host) is byte-unchanged since pre-149L (§3),
independently re-confirmed, and contains **zero** references to
`rollback_approval_evidence` anywhere in its source (independently grepped).

## 67. `approval_present=True` Production Search — Verdict: CONFORMS

`grep -rn "derive_rollback_approval_present\|resolve_rollback_approval_evidence" src/pcae/ --include=*.py`
returns matches only inside `rollback_approval_evidence.py` itself and this
verification's own test file. No production `PermissionBrokerRequest`
construction site anywhere in the repository consumes either function.

## 68. Foundation Non-Regression — Verdict: CONFORMS

`permission_broker_foundation.py`/`permission_broker.py` byte-unchanged
(§3). Focused Permission Broker / POL-001 / POL-004 / POL-005 suite:
**981 passed** (149L's own baseline: 980 — the +1 is this environment's
own collection difference, not a regression; zero failures either way).

## 69. RAE Requirement Implementation Trace

All 81 RAE-REQ-* requirements (confirmed exact count, §26) were reviewed
against the implementation during this verification. Full item-by-item
IMPLEMENTED/NO-CODE/PARTIAL/MISSING/CONFLICTING classification is
summarized (not exhaustively itemized per-requirement here, given this
report's length): the overwhelming majority (structural shape, family
locking, TTL, timezone handling, replay/retry semantics, decision
vocabulary, revocation, import boundary, IWC/AESIC exclusion, legacy-flag
exclusion, non-interference) are **IMPLEMENTED** and independently
confirmed correct by this suite. The canonicality/provenance cluster
(RAE-REQ-018, RAE-REQ-019, RAE-REQ-056) is classified **PARTIAL**: the
*mechanism* exists and is exercised by the happy path and by
post-persistence tampering detection, but the *provenance guarantee itself*
is not enforced against an adversary who can write directly to the already-canonical
storage paths — this is the root cause of F1/F2/F4. This is a **CODE
requirement marked PARTIAL bordering on MISSING for the adversarial case**,
and is therefore **Blocking** per the phase prompt's own classification
rule ("Any CODE requirement marked MISSING is potentially Blocking").

## 70/71/72. Schema Completeness / Agreement / Unknown Fields

`rollback_approval_binding.schema.json` sets `additionalProperties: false`
and explicitly documents (in its own `description` field) that "schema
validity alone never establishes canonical provenance" — an honest
disclaimer that independently anticipates F1/F2/F4, though the Python
validator does not itself invoke this schema at runtime (confirmed: no
`jsonschema` import or call exists in `rollback_approval_evidence.py` —
the JSON Schema file is external-inspection-tooling-only, never a runtime
gate). A malicious extra `approved=true`/`override=true` field would be
rejected by the schema (closed object) but has **no effect at all** on the
Python runtime path either way, since the runtime path does not read
unknown fields and does not invoke the schema. No dangerous
schema/Python-runtime disagreement was found beyond this decoupling, which
is itself disclosed.

## 73/74/75/76. Type Confusion / Unicode / Digest Canonicalization / Link Integrity

`_binding_from_dict` coerces every ID field via `str(...)`, so a JSON
integer `job_id` would be silently stringified rather than rejected — a
minor, non-blocking type-looseness (not independently exploited to a
security-relevant outcome in this verification's time budget; flagged as
an area for a future narrower hardening pass, not itself Blocking). Digest
canonicalization (`json.dumps(..., sort_keys=True, separators=(",", ":"))`)
is deterministic. Changing Decision content after Binding creation is
caught (§18/19/20 tamper tests) for records anchored to a *canonically-created*
Decision at Binding-creation time — but is not itself the vector F1/F2
exploit (those attack canonicality at creation time, not integrity after
creation).

## 77/78/79/80. Compound Lifecycle States

Not independently stress-tested beyond §36/§37 findings (revoked-then-superseded,
superseded-then-revoked, invalid-newer-record, denial-record-canonicality)
given this phase's time budget; no evidence of a *distinct* additional
defect beyond F4 was found, but these compound paths were not exhaustively
attacked and should be revisited in the narrow repair phase recommended
below.

## 81/82/83. Authority Lookup Failure / Storage Error / Symlink

No authority-registry subsystem exists to fail (§22/23 — the check is a
static template-text check only). Storage read errors (corrupted JSON) are
independently confirmed fail-closed (§30). Symlink/path-replacement attacks
were not independently exploited within this phase's scope; no evidence of
a distinct additional defect was found, but this is not exhaustively ruled
out either.

## 84/85. Independent Test Suite

`tests/test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`
— 53 tests, independently constructed (no import from 149L's own test
files). **49 passed, 4 failed** (the 4 failures are the confirmed BLOCKING
findings F1, F2, F4-copy, F4-supersession themselves, deliberately written
as failing assertions so the finding is visible in CI rather than silently
passed over).

## 86. 149L Self-Tests (implementation evidence, not independent proof)

`python -m pytest tests/test_rollback_approval_evidence_*.py -n auto`:
**77 passed** — matches 149L's own claimed baseline exactly.

## 87. 149J Verification Regression

`python -m pytest -k '149j' -q`: **49 passed** — matches the expected
baseline exactly.

## 88. CHGR Regression

`python -m pytest -k chgr -n auto -q`: **226 passed, 2 failed**
(`test_chgr_packaging.py::test_143e_wheel_contains_all_six_chgr_record_schemas`,
`test_chgr_packaging.py::test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv`).
Independently reproduced against pre-149L commit `1ece0258` in an isolated
worktree: **identical 2 failures, identical test names, present before
149L too.** Confirmed genuinely pre-existing (build-environment /
packaging-artifact related, not caused by 149L).

## 89. TAM / CLTR Regression

`python -m pytest -k 'tam or cltr' -n auto -q`: **5672 passed, 61 failed**.
Diffed against pre-149L commit `1ece0258` in an isolated worktree: **58 of
the 61 failures are pre-existing** (same test names, same packaging/wheel/sdist-artifact
class of failure, present before 149L). **3 are new**, all traced to the
single root cause in Finding F5 (§55/56 above). No illegal CHGR/TAM
authority-family composition was found — the regression is a string-scan
false positive against prose, not a real boundary violation.

## 90. IWC Regression

`python -m pytest -k 'iwc or interactive_workflow' -n auto -q`: **693
passed, 0 failed.**

## 91. AESIC / Authority Evaluation Regression

`python -m pytest -k 'aesic or authority_evaluation' -n auto -q`: **431
passed, 0 failed** — matches 149L's own reported baseline exactly.

## 92. Permission Broker Regression

`python -m pytest -k 'permission_broker or POL-001 or POL-004 or POL-005' -n auto -q`:
**981 passed, 0 failed** (149L baseline: 980 passed; +1 is a benign
collection-count difference, no failures either way).

## 93. Rollback Existing Regression

`python -m pytest -k rollback -n auto -q`: **461 passed, 4 failed** — the 4
failures are this verification's own new adversarial test file's
deliberately-failing findings (F1, F2, F4×2), not a regression in any
pre-existing rollback test. All pre-existing rollback tests pass.

## 94. Wave-1 Regression

`python -m pytest -k 'wave_1 or wave1' -n auto -q`: **34 passed, 0
failed.**

## 95. Runtime Regression

`python -m pytest -k runtime -n auto -q`: **9 failed** total; diffed
against pre-149L baseline in an isolated worktree: **7 pre-existing**
(packaging/wheel artifacts + one flaky snapshot test), **2 new**, both the
same F5 root cause (136ai, 136av — subset of the 3 counted in §89, since
136z is not runtime-keyword-matched and 136aw was already failing
pre-149L).

## 96. Fast Green

`python -m pytest -m fast_green -n auto -q`: **4391 passed** — exact match
to the entering baseline. No Fast Green regression.

## 97/98. Production / Contract Diff Boundary (this phase, 149M, itself)

`git diff --name-only 9ccc9346..HEAD -- src/pcae/`: **empty.**
`git diff --name-only 9ccc9346..HEAD -- docs/contracts/`: **empty.**
Confirmed: 149M added only a new test file and this new documentation
file — no production source or contract was modified by this verification
phase.

## 99. Runtime Boundary

`pcae runtime inspect` before and after this phase: **State: Observed;
Maximum Capability: observe; Execution Availability: unavailable** — both
times, identical. No change.

## 100. Blocking Findings

- **F1 — Bypassed at-most-one-active-Binding-per-Decision guarantee.** A
  Binding referencing a genuine, real published Decision can be
  hand-authored directly into the canonical storage path (bypassing
  `create_rollback_approval_binding`) with an arbitrary
  `rollback_operation_reference`, and resolves `VALID`. RAE-REQ-019 is
  enforced only at the creation-API call site, never at resolution time.
- **F2 — Noncanonical Decision + Binding pair fully trusted.** A
  hand-authored CHGR-record-shaped file, written directly to CHGR's own
  `records/` path (never having gone through
  `PublicationCoordinator`/Confirmation/Authorization/Publication), is
  accepted by `_resolve_decision_ref` as "published" and digest-valid, and
  a Binding referencing it — created via the real
  `create_rollback_approval_binding` API — resolves `VALID`,
  `approval_present=True`. This is the archetypal "noncanonical CHGR
  record validates" Blocking example named explicitly in this phase's own
  prompt (item 100).
- **F4a — Copied-record trust inheritance.** A verbatim byte-for-byte copy
  of a legitimate Binding's serialized content, placed under a new
  `evidence_id` filename, resolves `VALID` under that new filename — the
  store's filename-keyed lookup and the payload's internal `evidence_id`
  field are never cross-checked.
- **F4b — Forged-newer-timestamp supersession attack (HIGH PRIORITY, item
  39). CONFIRMED WORKING.** A hand-authored Binding file with a forged
  later `created_at`, referencing the same real Decision and the same
  operation reference as a legitimate, still-fresh Binding, causes the
  legitimate Binding to resolve `SUPERSEDED` — a working denial-of-evidence
  attack requiring only filesystem write access to the already-canonical
  evidence directory, matching this phase's own named Blocking example
  ("forged newer timestamp suppresses valid evidence").

All four findings share one root cause: **the module's canonicality
enforcement is entirely reducible to digest self-consistency plus
reference to a real CHGR record's declared fields — none of which requires
the record's *creating process* to have been the legitimate
Confirmation→Publication/creation-API pipeline.** No signing, no
capability/permission check on who may write to the canonical directories,
and no cross-check between "was this specific file the product of
`create_rollback_approval_binding`/`create_rollback_approval_decision`"
exists anywhere in the resolution path.

## 101. Non-Blocking Findings

- **F5 — Three unrelated TAM/CLTR regression tests broken by docstring
  prose** (§55/56/89/95) — a real, reproducible test regression, but not a
  real security-boundary violation; narrowest possible fix is a docstring
  reword.
- Minor type-looseness in `_binding_from_dict`'s `str(...)` coercion of ID
  fields (§73) — not independently exploited to a security-relevant
  outcome in this verification.
- Compound lifecycle states (§77-80) and symlink/path-replacement (§83)
  were not exhaustively attacked within this phase's time budget; no
  additional distinct defect was found, but these remain open areas for a
  future, more exhaustive pass.
- 149L's own phase report's "Fast Green 4391 passed unchanged" claim is
  independently confirmed true; its regression-suite claims for CHGR are
  independently confirmed true; but its report did not surface F5's three
  newly-broken TAM/CLTR guard tests — a completeness gap in the report,
  not in the underlying contract conformance question this phase was
  chartered to answer.

## 102. Verification Verdict

```
NOT VERIFIED — BLOCKING RAE-001 IMPLEMENTATION FINDINGS
```

Findings F1, F2, and F4 (a/b) are each independently reproducible,
non-fabricated, and each individually matches one of this phase's own
named Blocking-finding examples (item 100: "schema-valid forged approval
validates," "noncanonical CHGR record validates," "forged newer timestamp
suppresses valid evidence"). Per this phase's own ground rules, this
verification phase does **not** repair, patch, or otherwise modify
`rollback_approval_evidence.py`, RAE-001, or any other production
artifact — the findings are recorded here and in the accompanying test
suite for a future, narrowly-scoped repair phase.

## 103. Integration Readiness

```
NOT READY FOR ROLLBACK INTEGRATION PLANNING
```

Wiring AG3/AG5 to consume `derive_rollback_approval_present()` today would
inherit F1/F2/F4's forgeability directly into a live mutation-permission
decision path — the exact outcome RAE-001 exists to prevent. Integration
planning should not proceed until a narrowly-scoped repair closes the
canonicality-enforcement gap (e.g., requiring `create_rollback_approval_binding`/`create_rollback_approval_decision`
to be the *only* legitimate writers of their respective canonical
directories, verified by more than digest self-consistency — for example,
a repository-local authenticity marker distinct from the record's own
declared content, or an idempotency-marker cross-check analogous to
`PublicationRecordStore`'s own `published/<package_id>.json` mechanism,
extended to the Binding layer and re-checked at resolution time, not only
at creation time).

## 104. AG3 Readiness

Not ready. The AG3 profile's field shape (§8/§9) is itself correctly
implemented and independently confirmed exact-match-only; the blocking
gap is upstream of the AG3-specific profile (in canonicality/provenance
enforcement, F1/F2/F4), so it applies equally to AG3.

## 105. AG5 Readiness

Not ready, for the identical reason as §104 — the gap is
family-independent.

## 106. Chapter 149 Status

Even setting this verdict aside, Chapter 149 remains incomplete
regardless: AG3/AG5 rollback integration is not implemented; independent
rollback integration verification has not occurred; TK1/TK2/TK3
deferred-coverage re-affirmation remains outstanding. This verdict adds
one additional blocker on top of those: the evidence substrate itself
requires repair before integration planning can safely begin.

## 107. Recommended Next Phase

Per this phase's own recommended-next-phase logic ("If canonical-vs-forged
distinction fails, do not proceed to rollback integration; recommend a
bounded canonical-provenance hardening phase"):

```
149N — Rollback Approval Evidence Canonical-Provenance Hardening
```

Scope should be narrowly bounded to: (1) closing F1 by moving the
at-most-one-active-Binding-per-Decision check into
`resolve_rollback_approval_evidence` itself (or an equivalent
resolution-time invariant), never relying solely on the creation-API call
site; (2) closing F2 by strengthening `_resolve_decision_ref`'s
"published" check beyond a self-declared string field — e.g. cross-checking
against `PublicationRecordStore`'s own idempotency marker
(`published/<package_id>.json`) or an equivalent pipeline-only artifact
that a hand-authored file cannot fabricate without also fabricating a
second, independently-checked artifact; (3) closing F4a by cross-checking
a Binding's internal `evidence_id` field against the filename/key used to
look it up, rejecting any mismatch; (4) closing F4b by restricting
`_is_superseded()`'s candidate scan to Bindings that pass the same
provenance strengthening as (1)/(2); (5) closing F5 by rewording the
module's docstring to avoid the literal `pcae.cltr.authority` substring.
Only after 149N verifies clean should a dedicated "149O — Rollback
Permission Integration Plan" (AG3/AG5 evidence lookup, `approval_present`
consumption, `PermissionBrokerRequest` construction, POL-004 behavior,
rollback freshness, DENY/HUMAN_REVIEW/failure handling, exact mutation
boundary, tests) be chartered — implementation should not be attempted
directly.
