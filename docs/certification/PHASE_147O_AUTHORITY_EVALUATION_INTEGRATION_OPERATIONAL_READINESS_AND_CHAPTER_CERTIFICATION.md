# Phase 147O: Authority Evaluation Integration Operational Readiness and Chapter Certification

**Phase ID:** 147O
**Mode:** Operational Readiness Assessment and Chapter Certification (assessment-only; no production code changes)
**Implementation baseline:** Phase 147M (`d0c1008a`)
**Independent verification baseline:** Phase 147N (`53c6a86f`)
**Normative contract:** AESIC-001 v1.3 (frozen, Phase 147K/147L.1/147L.3/147L.5)
**Architecture baseline:** Phase 147J
**Runtime baseline:** Observed / observe / unavailable (unchanged throughout)

---

## 1. Executive Summary

This phase independently assesses whether the Authority Evaluation Integration
chapter (147G–147N) is operationally ready and eligible for whole-chapter
certification. It does not treat Phase 147M's implementation report or Phase
147N's "VERIFIED WITH NON-BLOCKING FINDINGS" verdict as automatic
certification; it re-derives the chapter's readiness from primary evidence —
the frozen AESIC-001 v1.3 contract text, the production source tree, the two
disclosed 147N findings, and fresh source-level and test-level reproduction.

**Two findings anchor this assessment:**

1. **AESIC-N-01** (Major, disclosed by 147N): the AER store's lower-level
   `read_canonical`/`read_record` API does not validate a pointer's embedded
   `package_id` against the query key, so a filesystem-tampered pointer could
   silently resolve to a different package's AER. Independently reconfirmed
   at `src/pcae/aesic/storage.py:166-197,147-156`. Independently reconfirmed
   **unreachable** through AES's own public interface: `evaluate_stage_2`
   (`src/pcae/aesic/service.py:280-286`) always constructs
   `CanonicalPointer(package_id=package_id, ...)` from its own argument, never
   from a value read back out of storage, so no production code path through
   AES can ever produce a mismatched pointer. Containment is demonstrated by
   construction, not merely asserted.

2. **AESIC-O-01** (new, this phase — Major, production-path reachability):
   independent inspection of the entire production call graph shows **the
   Authority Evaluation Service is never actually constructed or invoked on
   any real, running production path.** `src/pcae/commands/decision_session.py:208`,
   the sole production instantiation site of `SessionApplicationService`,
   calls `SessionApplicationService(session_coordinator)` — it does not pass
   an `authority_evaluation_service` argument, so the optional collaborator
   defaults to `None` (`session_service.py:314,322`). A repository-wide
   search confirms this is the *only* production constructor call
   (`grep -rn "SessionApplicationService(" src/pcae` → one hit, in
   `decision_session.py`) and that `authority_evaluation_service=` is never
   supplied anywhere outside `session_service.py`'s own signature
   (`grep -rn "authority_evaluation_service" src/pcae` → matches only inside
   `session_service.py` itself). `AuthorityEvaluationService(...)`,
   `AuthorityEvaluationRecordStore(...)`, and `FilesystemAuthorityRegistry(...)`
   are constructed **only inside test files** anywhere in the repository.
   Section 6 (Production-Path Reachability) treats this as the chapter's
   central operational-readiness fact: Stage 1 and Stage 2 are fully
   implemented, independently verified, safe, and non-gating library code —
   but as shipped, they are dead code on the actual `pcae decision-session`
   CLI surface today. This is exactly the "library-complete but not
   production-reachable" scenario this phase's charter asked to be stated
   explicitly if found (§6), and it is found.

Everything else this phase examined — persistence durability, restart and
crash recovery, threaded concurrency, the closed error taxonomy, non-gating
semantics, CHGR citation-only integration, runtime preservation, and
architecture-policy conformance — independently holds up. The chapter is a
correct, safe, well-tested library capability. It is not yet an operating
production capability, and AESIC-N-01 remains an open (contained) integrity
gap in the storage layer it would activate.

**Operational Readiness Verdict: AUTHORITY EVALUATION INTEGRATION NOT
OPERATIONALLY READY** (§39, driven by AESIC-O-01).

**Chapter Certification Verdict: AUTHORITY EVALUATION INTEGRATION CHAPTER
NOT CERTIFIED** (§40).

**Recommended next phase:** 147O.1 — Authority Evaluation Production Wiring
(composition-root activation only, no AESIC-001 amendment), followed by
147O.2 — Canonical Pointer Cross-Key Binding Repair (AESIC-N-01), then a
147O.3 re-certification pass. See §41.

---

## 2. Scope

In scope: independent assessment of chapter 147G–147N against AESIC-001
v1.3, production-path reachability, persistence/restart/concurrency/security
readiness, non-gating and runtime-preservation certification criteria, and
production of this certification document plus ordinary governance
bookkeeping. Out of scope, per the phase's own no-go boundary (§37 of the
authorizing prompt, reproduced at §41 below): no change to `src/pcae/**`, no
repair of AESIC-N-01 or AESIC-O-01, no contract amendment, no architecture
redesign, no runtime-capability change, no new CLI command, no test
weakening. All findings that would require production changes are
documented and deferred to named follow-up phases.

---

## 3. Assessment Method

**Bootstrap (before this investigation began).**

```
pcae session bootstrap --agent-id claude-local --sync-lock
pcae check
pcae health
pcae doctor task-memory
pcae runtime inspect
pcae push check
```

Results: agent lock held by `claude-local`; health `healthy`; check
`passed`; task memory `clean`; latest completed phase 147N; recommended
next phase 147O; runtime `not_implemented` / Runtime state `Observed` /
Execution capability `unavailable` / Maximum plugin capability `observe`
(unchanged baseline); git working tree clean, `origin/main` synchronized,
nothing to push. Readiness was initially reported `blocked` only because
the active task was the post-147N idle placeholder; `pcae task transition`
closed that task and opened the 147O task contract before this assessment
began.

**Independent inspection performed** (not reused from predecessor reports):
direct reading of AESIC-001 v1.3 (2930 lines), the Phase 147J architecture
report, the Phase 147M implementation report, the Phase 147N verification
report; direct reading of every file in `src/pcae/aesic/` and the frozen
`src/pcae/authority_evaluation/`; `grep`/`git log`/`git show --stat` reproduction
of every claim in this report rather than trusting predecessor prose; direct
reading of `.pcae/policy.toml` (the actual architecture-policy artifact,
not a hypothetical one); direct reading of the specific test classes cited
below to confirm they exist and test what they claim to test; a full
`fast_green` run and the four-file Authority Evaluation chapter suite run
(§36).

---

## 4. Chapter Reconstruction

The chapter comprises six non-overlapping components (AESIC-REQ-004):
Interactive Workflow (caller), AES (`src/pcae/aesic/service.py`, sole
orchestrator), Decision Template Resolution (`resolution.py`, internal-only),
Registry (`registry_filesystem.py`, concrete filesystem adapter over the
frozen `authority_evaluation.registry.AuthorityRegistry` ABC), Evaluator
(the frozen, byte-for-byte-unchanged-since-147H `pcae.authority_evaluation`
package), and Publication Coordinator (consumer of an already-produced AER
reference only).

`src/pcae/aesic/` contains: `__init__.py` (public re-exports:
`AuthorityEvaluationService`, `AuthorityEvaluationRecord`,
`Stage1EvaluationResult`), `service.py` (AES:
`evaluate_stage_1`/`evaluate_stage_2`/`_resolve_and_evaluate`/
`_validate_stage_1_handoff`), `resolution.py` (`DecisionTemplateResolution`,
not re-exported — internal per AESIC-REQ-027), `template_store.py`
(concrete filesystem Decision Template store), `registry_filesystem.py`
(`FilesystemAuthorityRegistry`), `records.py` (value types +
(de)serialization + digest verification), `storage.py`
(`AuthorityEvaluationRecordStore`, two-tier AER + canonical pointer
persistence), `errors.py` (closed exception taxonomy, distinct from
`authority_evaluation.errors`), `diagnostics.py` (read-only inspection:
`show_evaluations_for_package`, `summarize_package`,
`show_ineligible_outcomes` — Python functions only, **no CLI command wraps
any of them**; `grep -rn "aesic\|authority_evaluation" src/pcae/commands/*.py
src/pcae/cli.py` returns zero matches).

**Explicitly outside the chapter** (AESIC-001 §2, AESIC-REQ-001/002): the
internal implementation of `pcae.authority_evaluation` itself (frozen,
governed by the separate AEMIC-001 contract), the exact Interactive
Workflow call site (named out-of-scope in the contract's own no-go
boundary — see §6's discussion of why AESIC-O-01 is a readiness gap rather
than a contract violation), concrete Registry storage-layout security
beyond the two documented failure classes, and UX presentation of Stage 1
disagreement.

---

## 5. Requirement Closure

AESIC-001 v1.3 defines 131 requirements (`AESIC-REQ-001`–`131`, numbers
never reused — only text repaired in place across 147L.1/147L.3/147L.5,
new requirements appended). Rather than repeating Phase 147M's
requirement-by-requirement traceability matrix, this phase reconstructs a
chapter-level closure classification, independently re-derived:

| Requirement band | Area | Classification |
|---|---|---|
| 001, 004–006, 016, 017 | AES sole-orchestrator ownership, closed error taxonomy | Implemented, independently verified, operationally exercised (unit/integration tests) |
| 002–003, 007–015 | AES construction/statelessness/dependency isolation | Implemented, independently verified. **Not operationally exercised in production** — see §6 |
| 018, 020–026 | Registry ABC shape, isolation edges | Implemented, independently verified (static import-graph tests, `TestArchitecturalLeakage`) |
| 027–039 | Decision Template Resolution | Implemented, independently verified, operationally supportable (no cache/retry footguns) |
| 040–049 | Registry concrete adapter | Implemented, independently verified against real filesystem attacks; one requirement (duplicate detection, REQ-044) satisfied only by structural argument, not an executable scan — see §8 |
| 050–117 (aggregated band) | Prose/definitional/evidentiary obligations | Implemented, verified as emergent behavior of the mechanisms above (147N's own disclosed methodological limitation, §5 line 134-147 of that report) |
| 051–057, 082–086, 118, 119, 122 | AER/pointer shape, digest ownership | Implemented, independently verified via digest tamper and truncation tests |
| 058, 059, 067, 109 | CHGR citation-only integration | Implemented, independently verified, **operationally unreachable in production today** (citation fields are always `None` on the live path — see §6, §21) |
| 064, 080 | Stage 1 never independently persisted | Implemented, independently verified |
| 091, 095, 097 | Non-gating advisory Stage 1; diagnostics read-only | Implemented, independently verified by source inspection and dynamic test; diagnostics operationally supportable only via custom Python (no CLI) — see §18 |
| 098 | `evaluation_id` uniqueness | Implemented, independently verified |
| 120 | Disclosed last-write-wins pointer concurrency | Implemented, independently verified via real threads; **not verified under multi-process concurrency** (disclosed gap, both by 147M and reconfirmed here — see §14) |
| 121, 129 | Idempotency-equivalence field set | Implemented, independently verified (6-test exhaustive matrix) |
| 123, 124 | Stage 1 handoff validation | Implemented, independently verified against forged/cross-session/malformed evidence |
| 126, 127, 130, 131 | Canonical pointer digest verification, fail-closed corruption, pointer-write-failure handling | **Partially verified — one gap (AESIC-N-01)**, contained as described in §15 |

No requirement is found violated or newly not-implemented by this phase.
The chapter-level gap this phase adds is not a requirement violation but an
**operational deployment fact** external to any single requirement:
AESIC-001 itself explicitly scopes "the exact IW call site" as out of its
own normative boundary (§2), so the absence of production wiring does not
violate the contract — it is a readiness gap the contract was never written
to guarantee against.

---

## 6. Production-Path Reachability

Traced flow, with production evidence at each arrow:

```
Interactive Workflow (pcae decision-session CLI)
        |  src/pcae/commands/decision_session.py:208
        |  SessionApplicationService(session_coordinator)  <-- NO authority_evaluation_service argument
        v
SessionApplicationService.__init__  (session_service.py:314,322)
        |  self._authority_evaluation_service = None  (the injected default)
        v
evaluate_authority_stage_1 (session_service.py:1092-1095)
        |  if self._authority_evaluation_service is None: return None   <-- always taken in production
        v
construct_readiness_package -> Stage 2 block (session_service.py:1166-1181)
        |  if self._authority_evaluation_service is not None: ...        <-- never taken in production
        v
AER persistence / canonical pointer / Publication handoff / CHGR citation
        (never reached; authority_evaluation_ref and citation_text remain
         None on every real invocation today)
```

**Verified directly:**

- `grep -rn "SessionApplicationService(" src/pcae --include="*.py" | grep -v test`
  → exactly one production hit, `decision_session.py:208`, no
  `authority_evaluation_service=` keyword supplied.
- `grep -rn "authority_evaluation_service" src/pcae --include="*.py" | grep -v "/aesic/"`
  → six matches, all inside `session_service.py` itself (signature, storage,
  and the two `if ... is None` / `is not None` guards). Zero matches
  elsewhere in `src/pcae`, including `decision_session.py`,
  `src/pcae/commands/`, `src/pcae/cli.py`, or any bootstrap/composition-root
  module.
- `grep -n "evaluate_authority_stage_1\|evaluate_stage" src/pcae/commands/decision_session.py`
  → zero matches: the CLI command never even calls the Stage 1 entry point,
  independent of the constructor question.
- `grep -rn "AuthorityEvaluationService(\|AuthorityEvaluationRecordStore(\|FilesystemAuthorityRegistry("`
  across `src` and `tests` → every construction call site outside the
  `aesic` package's own class bodies is inside a test file
  (`tests/test_phase_147m_...py`, `tests/test_phase_147n_...py`). No
  production code anywhere constructs these types.

**Entry points, dependency construction, adapter instantiation, and storage
paths are all fully implemented** (§4) — the gap is specifically that
nothing in the shipping composition root assembles and injects them. This
is not a missing capability; it is a missing wire. No test-only wiring
trick is required to make the capability work (the 147M/147N test suites
construct real objects against real storage, not mocks) — but equally, no
production trick exists to activate it. Optional behavior (defaulting to
`None`) is intentional and documented (`session_service.py:318-321`:
"When absent (the default — every pre-Phase-147M caller), Stage 1/Stage 2
are never invoked and existing behavior is byte-for-byte unchanged.") —
the intent was clearly a safe, additive rollout mechanism, not an oversight
in the mechanism itself. What was never done is the follow-up step of
actually flipping it on anywhere.

**Conclusion, stated explicitly per this phase's charter:** the Authority
Evaluation Integration is **library-complete and independently verified,
but not production-reachable.** No end user or operator running
`pcae decision-session ...` today can cause Stage 1 or Stage 2 evaluation
to execute, an AER to be written, a canonical pointer to be created, or a
citation to reach a CHGR record. This is the single fact this report
treats as decisive for the operational-readiness and certification verdicts
(§39/§40).

---

## 7. Configuration Readiness

No environment-variable configuration exists anywhere in `src/pcae/aesic/**`
or `src/pcae/authority_evaluation/**` (`grep` for `environ`/`getenv` in both
packages: zero matches). All paths are plain Python default-argument
constants, each independently injectable at construction time:

- `AuthorityEvaluationRecordStore(root=DEFAULT_STORAGE_ROOT)`,
  `DEFAULT_STORAGE_ROOT = Path(".pcae/authority-evaluation/records")`
  (`storage.py:42,98-99`).
- `FilesystemAuthorityRegistry(root=DEFAULT_REGISTRY_ROOT)`,
  `DEFAULT_REGISTRY_ROOT = Path(".pcae/authority-evaluation/registry")`
  (`registry_filesystem.py:26,41-42`).
- `template_store.read_template/write_template(root=DEFAULT_TEMPLATE_ROOT)`,
  `DEFAULT_TEMPLATE_ROOT = Path(".pcae/authority-evaluation/templates")`
  (`template_store.py:28`), threaded through
  `DecisionTemplateResolution.__init__`'s `template_root` and
  `AuthorityEvaluationService.__init__`'s optional `template_root=None`
  kwarg.

**Determinations:** default behavior is a fixed, versioned-in-code
filesystem layout under `.pcae/`; missing-configuration behavior is simply
"use the default path, which is created on first write" (no distinct
"unconfigured" error state exists, because there is no configuration
surface to leave unset); invalid configuration (e.g. an unwritable root)
surfaces as an ordinary `OSError`/`AuthorityRegistryUnavailableError`, not
a silent fallback; configuration is not persistent across restarts as
*configuration* — it is simply a constructor argument the (currently
nonexistent) composition root would need to supply consistently on every
process start; no secrets are involved; operators cannot inspect "active
configuration" through any CLI surface (consistent with §18's diagnostics
finding) — only by reading source or constructor arguments directly. No
configuration path was found that silently falls back to unsafe behavior;
the absence of configuration is symmetric with the absence of wiring
described in §6.

---

## 8. Registry Readiness

`FilesystemAuthorityRegistry` (`registry_filesystem.py`), one JSON file per
`(template_ref, template_version)` under
`.pcae/authority-evaluation/registry/<template_ref>/<template_version>.json`.

- **Empty registry / missing directory**: `resolve()` (`:44-56`) —
  `if not path.exists(): return None`. Both cases collapse to the same
  `None` branch; this matches AESIC-REQ-041's framing of absence as an
  "ordinary, expected outcome, not an error," but means operators cannot
  distinguish "registry never provisioned" from "no entry for this key"
  without inspecting the filesystem directly.
- **Malformed entry**: any parse/shape failure raises
  `AuthorityRegistryCorruptError` (`:58-65`, blanket `except Exception`,
  explicitly commented "every parse/shape failure is corruption").
- **Duplicate entry**: `resolve()` checks the parsed declaration's own
  embedded `(template_ref, template_version)` against the requested key and
  raises `AuthorityRegistryCorruptError` on disagreement (`:67-72`) — but
  the module's own docstring states this exists only because "the pair is
  definitionally the storage key... the filesystem itself admits at most
  one file per key." **No executable duplicate-scan mechanism exists**;
  AESIC-REQ-044 is satisfied by structural argument, not by code that could
  ever actually execute the "duplicate" branch in this concrete adapter.
  This is a documented, deliberate design choice, not an oversight, but it
  means the requirement is formally unverifiable against this
  implementation (there is no way to construct the state REQ-044
  describes).
- **Permission failure**: any `OSError` (including `PermissionError`) is
  re-raised as `AuthorityRegistryUnavailableError` (`:48-56`).
- **Restart equivalence / offline operation**: purely filesystem-backed,
  no network calls, no in-memory cache — restart-durable and
  offline-capable by construction.
- **Observability**: **none**. `registry_filesystem.py` has no `logging`
  import and makes no `logger.*` calls anywhere — all disclosure is via
  exception type/message only, unlike `service.py` (see §19).
- **Operator repair procedure**: none documented or tooled; repair means
  directly editing/removing JSON files on disk with no CLI assistance.
- **write_declaration** (an authoring convenience, never called by
  `resolve()`/Resolution/AES): its own docstring claims it "refuses to
  overwrite an existing, differently-keyed-but-colliding file," but the
  implementation (`:75-88`) unconditionally calls `path.write_text(...)`
  with no existence check or exclusive-create — the docstring and code
  disagree. This function is out of the certifiable read path (never
  invoked by AES), so it does not affect the operational-readiness verdict,
  but it is recorded in the limitations register (§32) as a
  documentation/code mismatch worth correcting.

**Determination:** the Registry is suitable for the chapter's narrow,
intended operational scope (a small, hand-provisioned, rarely-changing set
of Decision Template declarations) but not for any broader registry
capability (dynamic registration, bulk import, conflict reporting,
operator-visible listing) — none of which this implementation provides or
this phase certifies.

---

## 9. Decision Template Readiness

`template_store.py` (concrete store) + `resolution.py`
(`DecisionTemplateResolution`, internal-only per AESIC-REQ-027, not
re-exported from `aesic/__init__.py`). Layout:
`.pcae/authority-evaluation/templates/<template_ref>/<template_version>.json`.
`read_template` raises `DecisionTemplateNotFoundError` (missing file),
`DecisionTemplateMalformedError` (parse failure, non-dict payload,
missing/empty identity fields, path/embedded-field mismatch, non-str
`eligible_authority`), or `DecisionTemplateCitationEmptyError`
(empty/whitespace `eligible_authority`). No cache (module docstring), no
retry, exactly one Registry call per `resolve()`, version is a plain
string path component — there is no "latest" resolution logic and no
separate version index. Template evolution therefore **cannot** silently
alter historical AER meaning: because Stage 2 always resolves
`(template_ref, template_version)` at evaluation time and embeds the
resulting `citation_text` verbatim into the immutable AER, a later edit to
a template file changes only future evaluations against that same
`(ref, version)` pair — it does not and cannot retroactively alter any
already-persisted AER (immutability is enforced independently by
`storage.py`'s exclusive-create semantics, §12). Stale-template and
duplicate-template behavior at the Registry layer are as described in §8.
Rollback of a template is simply restoring the prior file — no migration
tooling exists, none is required given the immutable-AER guarantee.

---

## 10. Stage 1 Readiness

Optional and advisory-only by construction: `evaluate_authority_stage_1`
(`session_service.py:1092-1095`) short-circuits to `None` when
`self._authority_evaluation_service is None` — which is every production
invocation today (§6). Result is never persisted (`records.py` has no
store method accepting a bare `Stage1EvaluationResult`; confirmed by
`TestStage1AdvisorySemantics.test_stage_1_creates_no_aer_and_no_pointer`,
147N suite). Restart behavior is trivial (nothing is persisted, so there
is nothing to recover). Failure behavior: `_validate_stage_1_handoff`
(§11) rejects a malformed/mismatched caller-supplied Stage 1 result with a
typed `Stage1HandoffInvalidError` before any Registry/store access — it
does not propagate as a bare exception into Confirmation/readiness/
publication/execution (`TestNonGating`, 147N suite, confirms no downstream
gating). Compatibility with sessions that never run Stage 1 and sessions
created before Phase 147M is total, since the collaborator's absence
(`None`) has always been the default and is architecturally the
*only* state every existing session has ever been in.

---

## 11. Stage 2 Readiness

Fresh evaluation on every invocation (AESIC-REQ-121/023: `service.py:248`
always calls `_resolve_and_evaluate` before comparing against the current
canonical AER — no reuse-without-reevaluation shortcut). Registry/template
dependencies as in §8/§9. Stage 1 validation happens first and is
independent of Stage 1's presence or absence
(`TestStage2Ordering.test_stage_1_handoff_validation_happens_before_any_registry_or_store_access`).
Idempotent retry: identical outcome + identical (or equivalently-absent)
Stage 1 evidence is a no-op returning the existing canonical AER
(`service.py:247-256`); a changed outcome persists a new AER and advances
the pointer (`:259-286`) — this is supersession, not authorization or
mutation of history. Refusal/failure behavior: `CanonicalPointerUpdateFailedError`
if the pointer write fails after a successful AER commit (never after a
failed one — the AER commit happens first and is what makes the operation
safely retryable, §13). Persistence and pointer publication as in §12.
Downstream handoff is citation-only (§14/§21). Stage 2 cannot become
authorization or publication-eligibility logic: `evaluation_result`
(ELIGIBLE/INELIGIBLE) is never branched on by any downstream consumer
(§9/§28) — only `citation_text`'s truthiness gates whether a citation
string is forwarded, never whether the readiness package or publication
proceeds.

---

## 12. Persistence Durability

`storage.py`, two-tier layout:
`records/<package_id>/<evaluation_id>.json` (primary, immutable,
exclusive-create) and `pointers/<package_id>.json` (canonical, atomic
replace).

- **Directory creation**: `mkdir(parents=True, exist_ok=True)` in both
  `_write_atomic_json` and `_write_exclusive_json` — no separate
  provisioning step required.
- **Create-only AER semantics**: `_write_exclusive_json` uses
  `os.open(path, O_CREAT | O_EXCL | O_WRONLY)`. `write_record` treats
  `FileExistsError` as "compare digests" — identical content is a
  no-op, differing content raises `AuthorityEvaluationRecordConflictError`
  (`:109-135`). AERs are never overwritten, independently confirmed by
  reading the code directly (not merely trusting the docstring).
- **Pointer atomicity**: `_write_atomic_json` — `tempfile.mkstemp` in the
  same directory, write + `fsync`, `os.replace` (atomic rename on POSIX
  filesystems), `finally`-block cleanup of any leftover temp file. This is
  the same pattern already used by `src/pcae/cltr/persistence.py` and
  `src/pcae/governance/publication/storage.py` — reused, not reinvented.
- **Partial-write handling**: `os.replace` guarantees the pointer file is
  either the old complete content or the new complete content, never a
  partial write, on any POSIX filesystem providing atomic rename (an
  environment assumption — §25).
- **Corruption handling**: digest mismatch on read raises
  `AuthorityEvaluationRecordCorruptError` / `CanonicalPointerCorruptError`
  (fail-closed — never silently returns mismatched content).
- **Backup/restore/migration**: no explicit tooling exists; the layout is
  plain JSON files under a documented root, so ordinary filesystem
  backup/restore applies without special handling, but this is an
  assumption, not a tested guarantee.
- **Disk-full behavior**: not safely testable in this environment; the
  `OSError` path in `write_pointer`/`evaluate_stage_2` (§13) would apply,
  but no dedicated disk-full simulation test exists in the suite.
- **Path stability**: `_safe_name` sanitizes `package_id`/`evaluation_id`
  into filesystem-safe path components (`registry_filesystem.py`,
  `storage.py`) — no path-traversal characters survive into a path
  segment (see §20).

**Determination:** every implementation guarantee this phase could verify
rests on ordinary POSIX filesystem semantics (atomic rename, `O_EXCL`
exclusivity, `fsync` durability) — none of which are exotic, but none of
which are re-documented as an explicit operational/deployment requirement
anywhere outside source comments (see §25).

---

## 13. Restart and Recovery

The material restart points named in this phase's charter were exercised
directly by the 147N suite and reconfirmed by this phase's source reading
(not merely re-run):

- **After AER commit / before pointer update**: `service.py:277-296` — if
  `write_pointer` raises `OSError`, `evaluate_stage_2` logs
  `authority_evaluation.pointer_update_failed` and raises
  `CanonicalPointerUpdateFailedError` with a message stating the AER
  **was** committed and remains durable, and that the pointer update
  failed — the exception message itself is the operator-facing recovery
  signal.
- **Reproduced from a fresh process/service instance**:
  `TestCrashRecovery.test_recovery_creates_a_second_distinct_aer_rather_than_rediscovering_the_orphan`
  (`tests/test_phase_147n_...py:836+`) monkeypatches `write_pointer` to
  raise, then constructs a **new** `AuthorityEvaluationRecordStore`/
  `AuthorityEvaluationService` instance over the same root directory
  (simulating a fresh process) and retries. Result: exactly one valid
  canonical pointer after recovery, the pre-crash orphaned AER remains
  durably present and auditable (never deleted), and a second retry is
  independently idempotent
  (`test_repeated_recovery_attempts_are_each_individually_idempotent_once_pointer_exists`).
- **Operator capability assessment**: an operator **can** recognize the
  failure state (the raised exception names both the committed AER and the
  failure), **can** safely retry (retry is idempotent by construction —
  it either finds the existing canonical AER via equivalence-comparison or
  supersedes it), **can** distinguish update failure
  (`CanonicalPointerUpdateFailedError`) from corruption
  (`CanonicalPointerCorruptError`, a different type) by exception type
  alone, but **cannot** confirm successful recovery through any operator
  tool — confirmation requires either the caller's own retry succeeding
  silently or direct inspection via the Python-only `diagnostics.py`
  functions (§18), since no CLI exposes them. No documented procedure
  tells an operator "run X to confirm recovery."
- This finding (AESIC-N-02, informational) is about a labeling nuance in
  this exact scenario — see §16 — not a correctness gap; this phase found
  no correctness gap in the restart/recovery mechanism itself.

---

## 14. Concurrency

`TestConcurrency` (`tests/test_phase_147n_...py:900+`) uses real
`threading.Thread` (8 threads) for two scenarios:
`test_concurrent_equivalent_invocations_converge_to_one_valid_current_effective_pointer`
and `test_concurrent_distinct_supersessions_leave_exactly_one_valid_pointer`.
Both independently reconfirmed to exist and test what they claim.

- **Supported concurrency assumption**: single-process, multi-threaded,
  shared GIL. `write_pointer`'s last-write-wins semantics
  (`_write_atomic_json`, no compare-and-swap) is explicitly disclosed as
  the concurrency model (AESIC-REQ-120) — not accidental.
- **Conflict behavior**: whichever write's `os.replace` executes last wins;
  no conditional-write mechanism exists to detect or reject a lost update.
- **Cross-process / multi-instance use of the same store**: **not
  exercised by any test**. The 147M implementation report itself discloses
  this gap (`docs/implementation/PHASE_147M_...md:490-493`): "No live
  multi-process concurrency stress test... a disclosed, non-blocking gap."
  This phase independently confirms no such test exists anywhere in the
  four chapter test files (`grep -n "multiprocessing\|subprocess"` across
  all four returns no concurrency-relevant hits).
- **External coordination**: none is required or assumed for the
  single-process case; for genuine multi-process/multi-host concurrent
  writers, the last-write-wins pointer semantics mean no external lock is
  enforced, and data loss (a lost supersession, not corruption — the AER
  itself is never lost, only the pointer might not reflect the most recent
  write) is the disclosed, accepted risk.

**Determination:** concurrency is bounded and understood for the tested
case (single-process, multi-threaded); multi-process concurrency is an
explicitly disclosed, untested limitation, consistent with a filesystem
store with no lock file or advisory-lock mechanism.

---

## 15. AESIC-N-01 Assessment

Independently reproduced and inspected (not merely re-quoted).

- **Exact affected API**: `AuthorityEvaluationRecordStore.read_canonical`
  (`storage.py:166-190`) and `read_record` (`:147-156`). `read_canonical`
  reads the pointer at the query key's path, then uses **the pointer
  content's own** `pointer.package_id`/`pointer.evaluation_id` fields — not
  the caller's `package_id` argument — to locate the referenced AER via
  `self.read_record(pointer.package_id, pointer.evaluation_id)`. It
  verifies the referenced AER's `record_id` and recomputed digest against
  the pointer, but never compares `pointer.package_id` against the
  `package_id` argument the caller originally supplied. `read_record` has
  the mirror gap: it verifies the AER's own digest but never checks the
  payload's embedded `package_id`/`evaluation_id` fields against the two
  path-determining arguments.
- **Exact preconditions**: a pointer or record file whose *filesystem
  location* (which key it was written under) disagrees with its own
  *embedded content* (which key it claims to be for) — both internally
  self-consistent and digest-valid, just misfiled.
- **Reachability by ordinary production callers**: **not reachable**.
  Independently reconfirmed at `service.py:280-286`: the only production
  writer of a `CanonicalPointer` is `evaluate_stage_2`, which always
  constructs `CanonicalPointer(package_id=package_id, ...)` from its own
  method argument — never from a value read back out of storage. No code
  path through AES's public interface (`evaluate_stage_1`/`evaluate_stage_2`)
  can produce a pointer whose embedded `package_id` disagrees with its own
  storage location. The reproduction test itself
  (`test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected`,
  `tests/test_phase_147n_...py:720`) writes the misfiled pointer directly
  to disk, not via any AES method — confirming the precondition requires
  out-of-band filesystem access.
- **Untrusted callers / future internal callers**: an untrusted caller
  with filesystem write access to the AER store directory could exploit
  this today. A future internal caller could accidentally reach it only by
  introducing a new code path that constructs a `CanonicalPointer` from
  read-back rather than caller-supplied data — no such path exists today,
  but nothing in `storage.py`'s own API prevents one from being added
  later without noticing the gap, since the store itself does not enforce
  the invariant.
- **Persisted corruption exploiting it**: yes — this is precisely the
  scenario the reproduction test constructs; ordinary bit-rot or a bad
  manual edit that happens to preserve digest validity while changing
  location would not be caught.
- **Operator tools triggering it**: none exist that write pointers (no
  CLI writes to this store at all, consistent with §18) — an operator
  could trigger it only via direct manual file manipulation.
- **Diagnostics detecting it**: `summarize_package`'s `pointer_ok` field
  (`diagnostics.py:44-49`) would catch this indirectly *if* the mismatch
  also broke a check that IS performed (record-id/digest agreement) —
  but a specifically crafted cross-key relocation with a self-consistent
  digest, as the reproduction test constructs, is not distinguished from
  a healthy pointer by any existing diagnostic.
- **Architectural policy preventing misuse**: `registry_filesystem.py`
  already applies the equivalent discipline (`resolve()` checks the
  parsed declaration's embedded key against the requested key, §8) —
  this is a real, load-bearing precedent for what `storage.py` should also
  do, and its absence in `storage.py` is an inconsistency within the same
  codebase, not a novel pattern being asked for.
- **Direct AESIC-001 violation**: yes, of §18's fail-closed pointer
  integrity language ("no corrupted pointer may silently resolve") — the
  cross-key case is a corrupted pointer that does silently resolve.
- **Certification-blocking on its own**: **no**, given demonstrated
  containment (write-path guarantee above) — but it remains an open
  requirement gap that should be repaired, not left indefinitely, because
  the containment argument depends entirely on no future code path ever
  writing a pointer from read-back data, which `storage.py` itself does
  nothing to enforce.

**Disposition: certification permitted with explicit operational
constraint** — specifically, the constraint that `write_pointer`/
`write_record` are never called with caller-supplied, non-evaluate_stage_2-
derived data in any deployment of this chapter, and that this gap is
repaired in a narrowly-scoped follow-up (§41) rather than deferred
indefinitely. This finding, alone, would not block certification. It is
AESIC-O-01 (§6), not AESIC-N-01, that drives this phase's overall verdict.

---

## 16. AESIC-N-02 Assessment

Independently reviewed. The finding describes a labeling/terminology
precision matter: post-crash retry (§13) produces a second,
content-equivalent AER with a fresh `evaluation_id` rather than literally
"rediscovering" the pre-crash orphan under its original `evaluation_id`,
because idempotency dedup is keyed against the *canonical pointer*
(absent, by definition, in exactly this crash window) rather than a
compound-key history scan. Reproducibility: confirmed, same test cited by
§13. Operational impact: none observed — exactly one valid pointer results,
no data loss, the orphan remains durably auditable. Maintainability impact:
none. Future risk: none identified beyond the documentation-precision point
already named. Documentation is sufficient as disclosed by 147N; no
follow-up work is required. This phase does not inflate this into a
blocker — there is no evidence to support doing so.

---

## 17. Failure Handling

Operational failure matrix (closed taxonomy, `errors.py`; consistent with
§13/§15's exception-type-based recovery signals):

| Failure class | Detection | Error type | Operator signal | Retry safety | Data-loss risk |
|---|---|---|---|---|---|
| Registry unavailable | `OSError` on path access | `AuthorityRegistryUnavailableError` | Exception message | Safe (no write attempted) | None |
| Registry ambiguous/malformed | Parse/shape failure | `AuthorityRegistryCorruptError` | Exception message | Safe (read-only failure) | None |
| Template missing | File absent | `DecisionTemplateNotFoundError` | Exception message | Safe | None |
| Template malformed | Parse/shape/identity failure | `DecisionTemplateMalformedError` | Exception message | Safe | None |
| Template empty citation | Empty/whitespace `eligible_authority` | `DecisionTemplateCitationEmptyError` | Exception message | Safe | None |
| Stage 1 malformed/mismatch | 4-reason closed enum check | `Stage1HandoffInvalidError` + `Stage1HandoffInvalidReason` | Reason enum + message | Safe (checked before any write) | None |
| AER conflict | Digest mismatch on exclusive-create collision | `AuthorityEvaluationRecordConflictError` | Exception message | Not retryable as-is (real conflict) | None (existing AER untouched) |
| AER corruption (read) | Digest mismatch on read | `AuthorityEvaluationRecordCorruptError` | Exception message | N/A (fail-closed read refusal) | None additional (original bytes untouched) |
| Pointer corruption (cross-key or digest) | Digest/record-id mismatch on read; **not** cross-key without digest break (§15) | `CanonicalPointerCorruptError` | Exception message | N/A (fail-closed) | None additional |
| Pointer update failure | `OSError` on `write_pointer` | `CanonicalPointerUpdateFailedError` | Exception message names the already-committed AER | Safe — retry is idempotent | None (AER durable, only pointer lags) |
| Serialization failure | Canonicalization bug | `AuthorityEvaluationSerializationError` | Exception message | Not retryable without a code fix | None (no partial write, §12) |
| Permission failure | `OSError` subtype `PermissionError` | Folded into Registry/store's `OSError` handling | Exception message | Depends on cause | None |
| Disk/filesystem failure | `OSError` at write time | Folded into pointer-update-failure / registry-unavailable paths | Exception message | Safe for pointer path; untested for disk-full specifically (§12) | Untested |

No automated recovery mechanism exists for any class above beyond the
built-in idempotent-retry safety of `evaluate_stage_2` itself; all recovery
is "the caller (or an operator manually invoking the same call) retries."
No escalation path (alerting, paging) is wired to any of these exceptions —
they are ordinary Python exceptions with no logging-to-alerting bridge
(see §19).

---

## 18. Diagnostics and Inspection

`diagnostics.py` provides `show_evaluations_for_package`,
`summarize_package`, `show_ineligible_outcomes` — all read-only, all
Python functions. **No CLI command exposes any of them**: independently
confirmed by `grep -rn "aesic\|authority_evaluation" src/pcae/commands/*.py
src/pcae/cli.py` → zero matches. An operator wishing to inspect AES
availability, active Registry source, Decision Template resolution, Stage
1 status, AER identity/digest, current pointer, pointer integrity,
current-effective AER, history, no-op reuse, supersession, recovery
attempts, corruption, or update failure **must write custom Python**
importing `pcae.aesic.diagnostics`/`pcae.aesic.storage` directly, or read
the JSON files under `.pcae/authority-evaluation/` by hand. AESIC-001 does
not require a CLI (out of its own scope, §2), so this is not a contract
violation, but it is an operational-supportability gap: combined with
§6's finding that the capability is not even wired into the CLI today,
there is currently no supported operator-facing way to observe this
chapter's behavior at all, in either its dormant or (hypothetically)
active state.

---

## 19. Logging and Audit

`service.py` logs at `logger.info` for `authority_evaluation.stage_2_idempotent_noop`
and `authority_evaluation.aer_committed`, and `logger.warning` for
`authority_evaluation.pointer_update_failed` — each entry includes
`evaluation_id`, `package_id`, and `record_id` as correlation identifiers
(no `session_id` in these specific log lines, though `session_id` is
carried inside `Stage1EvaluationResult` itself). `registry_filesystem.py`
and `template_store.py` have **no logging at all** (§8). No sensitive data
(credentials, PII) is logged — `citation_text`/`eligible_authority` strings
are governance metadata, not secrets. No retention policy is documented
for these log lines specifically (they flow into whatever the process's
general logging configuration captures). The distinction between advisory
disclosure (Stage 1, never logged as a gating event because it never gates
anything) and authorization is preserved: no log line anywhere in this
chapter reads as an authorization/denial decision — every one is a
descriptive fact about resolution or persistence.

---

## 20. Security

| Threat | Disposition |
|---|---|
| Fabricated Stage 1 results | Prevented — `_validate_stage_1_handoff`'s 4-reason closed check (§11) |
| Session/identity substitution | Prevented — part of the same handoff validation |
| Template substitution | Contained by Registry/store identity checks (§8); not prevented at the filesystem-write layer itself |
| Registry poisoning | Detected (malformed → `AuthorityRegistryCorruptError`); not prevented at the OS-permission layer, which is an environment assumption (§25) |
| Path traversal | Prevented — `_safe_name` sanitizes both `package_id`/`evaluation_id` (storage) and template ref/version (registry) into filesystem-safe segments |
| Symlink attacks | **Unmitigated / unverified** — no test or code inspects for symlinked targets before `os.open`/`os.replace`; not evaluated by 147M/147N or this phase |
| Permission misconfiguration | Detected as `OSError` → typed unavailability errors; not prevented |
| Pointer rollback | **Unmitigated** — last-write-wins (§14); a stale write racing a fresher one can roll the pointer backward with no version check |
| Pointer cross-key confusion | Contained (AESIC-N-01, §15) — not reachable via AES public API, but the storage-layer gap itself is unmitigated |
| Cross-session AER selection | Prevented — compound-key storage plus Stage 1 handoff validation |
| Stale Registry/template replay | Prevented at the resolution layer (no cache, always re-reads) but not prevented if the underlying file itself is stale (that is a provisioning/deployment concern, §9) |
| Malformed persisted artifacts | Detected — fail-closed digest/shape checks throughout |
| Denial of service | **Unmitigated / not evaluated** — no rate limiting or resource bounding exists or was tested |
| Unauthorized filesystem modification | Operator-mitigated only — relies entirely on OS file permissions; no application-layer access control exists (none is claimed by the contract) |
| Authority confusion | Prevented for the in-scope non-gating framing — Stage 2 output cannot itself confer authorization (§9/§28) |

**Deployment assumptions required for security**: the process running AES
must have exclusive, correctly-permissioned filesystem access to its
`.pcae/authority-evaluation/**` root; no other process or user should have
write access to that tree; the filesystem must support atomic rename and
`O_EXCL`. None of these assumptions are novel to this chapter (they mirror
the rest of the repository's filesystem-backed persistence, §12), but none
are independently documented as a deployment requirement outside source
comments.

---

## 21. Backward Compatibility

Every pre-Phase-147M caller of `SessionApplicationService` — which is
**every current production caller**, since §6 established the collaborator
is never supplied — receives `authority_evaluation_service=None` and
therefore byte-for-byte unchanged behavior, independently confirmed by
source reading of the two guard branches (`session_service.py:1092-1095,
1166-1181`). Existing `Session` objects, readiness packages without
Authority Evaluation fields, publication handoffs without references, CHGR
records without `authority_basis_claimed`, and existing persisted
publication records all continue to work unmodified: the CHGR population
logic (`governance/publication/record.py:266-277`) only ever adds
`authority_basis_claimed` when both `package.authority_evaluation_ref` and
`package.citation_text` are truthy — otherwise it inserts a disclosed
limitation string, which is the **only** behavior every existing (and,
today, every new) CHGR record actually exhibits. No migration is required
for any existing artifact, session, or workflow path — none of them ever
touch this chapter's storage.

---

## 22. Forward Compatibility

The chapter's stable boundaries: AES's two-collaborator construction rule
(AESIC-REQ-015 — exactly `registry` and `aer_store`, no ambient global
state), the closed error taxonomy (§17), the compound-key AER storage
scheme, and the citation-only CHGR contract (§9/§21) should all remain
fixed points for any future Registry adapter, template-versioning scheme,
formal AER JSON Schema, CLI diagnostics command, alternative storage
backend, or multi-process orchestration layer to build against. This phase
does not certify any hypothetical future implementation of these — only
that the current concrete Registry/storage adapters and the AES
orchestrator satisfy the frozen contract as written today.

---

## 23. Rollout

**Current default state: fully disabled** — not by an explicit feature
flag, but by the simple absence of production wiring (§6). This is,
functionally, the safest possible rollout starting point: zero risk, zero
behavior change, because the capability cannot execute. There is, however,
**no defined rollout model** for turning it on — no staged-rollout plan,
no dry-run/observation mode distinct from "fully wired," no documented
procedure for a follow-up phase to safely construct and inject a real
`AuthorityEvaluationService` into `decision_session.py`. Compatibility
with old artifacts is total (§21). No operator training or
monitoring/alerting exists because there is nothing yet to monitor. Known
constraint: any future wiring phase must also address the two open
findings (AESIC-N-01 containment depends on AES's write-path guarantee
continuing to hold; AESIC-N-02 has no action item) and should introduce
at minimum a CLI-observable activation state, since none currently exists.
Evaluation remains disclosure-only throughout — nothing in the current
code would need to change to preserve that property during a future
rollout, since no consumer branches on `evaluation_result` (§9/§28).

---

## 24. Rollback

Rollback today is trivial and already the default: doing nothing leaves
the capability permanently inactive. If a future phase wires AES into
`decision_session.py` and a rollback is later needed, code rollback (
reverting the composition-root change) is sufficient — no data cleanup is
required, since immutable AERs and canonical pointers persisted while the
capability was active remain valid, readable artifacts afterward (nothing
in the read path depends on AES being currently wired; `diagnostics.py`
and `read_canonical`/`read_record` work against whatever is already on
disk regardless of whether new evaluations are being produced).
Readiness artifacts and CHGR records that already contain
`authority_evaluation_ref`/`authority_basis_claimed` citations remain
readable and valid after a code rollback — nothing about disabling future
Stage 1/Stage 2 calls invalidates past ones. No immutable historical
artifact requires deletion to roll back behavior, satisfying the
mandatory rollback-safety property named in this phase's charter.

---

## 25. Environment Assumptions

| Assumption | Classification |
|---|---|
| Filesystem supports atomic `os.replace` (POSIX rename) | Required |
| Filesystem supports `O_CREAT \| O_EXCL` exclusive-create | Required |
| Single host, single writer process at a time (for pointer freshness guarantees) | Recommended (not enforced — §14/§20) |
| Directory permissions restrict `.pcae/authority-evaluation/**` to the intended process/user | Required, but unenforced by the application itself |
| Clock usage | Not load-bearing (`evaluated_at` is descriptive metadata, not used for ordering/locking decisions) |
| Stable locale/encoding | Required — `utf-8` is hardcoded in every read/write call, so this is actually enforced, not merely assumed |
| Offline operation | Supported — no network calls anywhere in the chapter |
| Package installation / repository layout | Standard `src/pcae/aesic` + `src/pcae/authority_evaluation` layout; no special installation step |
| Registry/template provisioning | Unverified — no provisioning tooling or procedure exists; entirely manual today |

---

## 26. Performance and Capacity

No dedicated benchmark suite exists for this chapter; no production-scale
guarantee is invented here. Structurally: Registry lookup and template
resolution are each a single file read with no cache (by design, §8/§9) —
cost scales with however many packages/templates exist, not with request
volume, since nothing is cached across calls. AER write is one exclusive-
create; pointer write is one atomic replace — both are O(1) filesystem
operations independent of history size. `read_canonical`/`show_evaluations_for_package`
history-listing calls (`list_evaluation_ids`) scale linearly with the
number of prior evaluations for a given `package_id` (a directory listing),
which is the most likely long-run scaling boundary if a single package
accumulates a very large evaluation history — no pagination or archival
mechanism exists for that case (see §27).

---

## 27. Data Retention

No AER, pointer, or superseded-history deletion/archival/compaction
mechanism exists anywhere in this chapter — every AER ever written is kept
forever under its compound key, and superseded AERs remain durably
readable via `show_evaluations_for_package`/`list_evaluation_ids` even
after the canonical pointer moves on. This is the correct default for an
audit-oriented capability (no deletion policy can silently break
auditability, because no deletion policy exists), but it also means there
is currently no retention/cleanup story at all for long-running
deployments, and no test-artifact isolation concern applies since
production has never yet written any real data here (§6).

---

## 28. Non-Gating Certification

Independently demonstrated by source inspection, not merely re-asserted
from 147N:

- `construct_readiness_package`'s Stage 2 block
  (`session_service.py:1164-1181`) has no branch on
  `aer.outcome.evaluation_result` that raises, blocks, or denies — the
  only conditional governs whether a citation is forwarded, not whether
  the readiness package is constructed. `PublicationHandoff().build_package(...)`
  is called unconditionally regardless of evaluation outcome.
- `evaluate_authority_stage_1` has no exception path tied to the
  evaluation result itself.
- CHGR construction (`governance/publication/record.py:266-277`) checks
  only for presence of a ref/citation, never for
  `evaluation_result == ELIGIBLE` — an INELIGIBLE outcome with a non-empty
  `citation_text` would still populate `authority_basis_claimed`.
- `src/pcae/governance/publication/coordinator.py` — repository-wide
  substring search for `AuthorityEvaluation`/`evaluation_result`/`aesic`
  returns **zero matches**. The Publication Coordinator's `execute()`
  transaction contains no reference to Authority Evaluation at all,
  independently confirming AESIC-REQ-026 structurally, not just by
  convention.
- Dedicated adversarial test:
  `TestNonGating.test_ineligible_stage_2_outcome_does_not_prevent_readiness_package_construction`
  (`tests/test_phase_147n_...py:968-970+`), independently confirmed to
  exist.
- Diagnostics are independently confirmed read-only/non-gating
  (`TestDiagnosticsAreReadOnlyAndNeverGate`, same file).

**No branch anywhere in the production consumption chain
(`session_service.py` → `PublicationHandoff` → `record.py` → `coordinator.py`)
blocks, denies, or alters control flow based on `evaluation_result`.**
Combined with §6, Authority Evaluation is both architecturally non-gating
(by code inspection) and operationally inert (never invoked) in the
current production surface — the strongest possible form of "does not
gate," precisely because it does not run at all today.

---

## 29. Runtime Preservation

```
$ git log --oneline -- src/pcae/runtime      (no such directory exists; "runtime"
                                               concepts live in src/pcae/core/runtime_*.py
                                               and src/pcae/commands/runtime_inspect.py)
$ git show --stat d0c1008a | grep -i runtime  (147M — no output)
$ git show --stat 53c6a86f | grep -i runtime  (147N — no output)
$ git show --stat 01e6cb6c | grep -i runtime  (147J — no output)
$ grep -rn "aesic\|authority_evaluation" src/pcae/core/runtime_context.py \
    src/pcae/core/advisory_runtime.py src/pcae/core/runtime_introspection.py \
    src/pcae/core/runtime_registry.py src/pcae/commands/runtime_inspect.py
                                               (no output — zero matches)
```

None of the 147J/147M/147N commits touch any runtime-concept file. Live
`pcae runtime inspect` (re-run in §3) reports Runtime status
`not_implemented`, Runtime state `Observed`, Execution capability
`unavailable`, Maximum plugin capability `observe`, Registry status
`empty`, Plugin count `0` — identical to the pre-147G baseline. No
Authority Evaluation output influences runtime capability (§28 already
establishes no output gates anything, which necessarily includes runtime
capability). **Mandatory criterion met.**

---

## 30. Architecture Policy

The actual architecture-policy artifact is `.pcae/policy.toml` (not a
YAML/import-linter file — corrected from an earlier pass of this
investigation that searched only source-code grep patterns and missed the
TOML config). Relevant declarations:

```
authority_evaluation = ["authority_evaluation"]
aesic = ["aesic", "authority_evaluation", "interactive_workflow", "governance"]
interactive_workflow = ["interactive_workflow", "governance", "aesic"]
```

Enforcement mode: `mode = "advisory"` (`.pcae/policy.toml:149`) — consistent
with `pcae health`'s "Latest enforcement mode: advisory" reported at
bootstrap (§3). Real enforcement machinery exists
(`src/pcae/core/architecture.py:analyze_changed_python_dependencies`,
invoked from `src/pcae/core/check.py`) and evaluates changed files against
these declared zone dependency lists — it is not merely a declarative
document nobody reads, but its findings are advisory (reported, not
build-blocking) at the current enforcement mode.

**Edge-by-edge verification against real imports:**

- `aesic -> authority_evaluation`: present, heavy, matches declaration
  (`service.py`, `registry_filesystem.py`, `resolution.py`, `records.py`,
  `template_store.py` all import from `pcae.authority_evaluation.*`).
- `aesic -> interactive_workflow`: present but narrow — exactly one import,
  `service.py:45`, `from pcae.interactive_workflow.models.session import Session`
  (a value type only, for type-checking, not orchestration).
- `aesic -> governance`: present but narrow — `records.py:21`,
  `compute_record_digest` reuse only.
- `interactive_workflow -> aesic`: present, exactly one call site,
  `session_service.py:73`, independently confirmed the only such import in
  the package by a dedicated `ast`-based test
  (`TestArchitecturalLeakage.test_only_session_service_in_interactive_workflow_imports_aesic`,
  147N suite).

**No edge is broader than its declared scope.** The bidirectional
`interactive_workflow <-> aesic` relationship (declared both directions in
`.pcae/policy.toml`) is real but each direction is narrow and
single-purpose: `interactive_workflow -> aesic` is exactly one orchestration
call site, `aesic -> interactive_workflow` is exactly one value-type
import with no orchestration behavior aesic invokes back into. No
circular-import failure exists (both directions import distinct,
non-overlapping symbols: `AuthorityEvaluationService` one way, `Session`
the other). This creates a documented, narrow maintenance coupling — a
future change to `Session`'s shape could ripple into `aesic`, and a future
change to AES's public interface could ripple into `session_service.py` —
but it does not create a cycle and does not blur conceptual ownership:
`interactive_workflow` still owns orchestration, `aesic` still owns
evaluation mechanics. Advisory enforcement (three targeted `ast`-based
unit tests, not a general-purpose architecture-linting tool) is adequate
for this narrow surface but would not scale to a much larger set of zones
without becoming a maintenance burden of its own — noted as a limitation,
not a defect.

---

## 31. Test Sufficiency

Collected item counts (`pytest --collect-only`):

| File | Items |
|---|---|
| `tests/test_phase_147g_authority_evaluation.py` | 93 |
| `tests/test_phase_147h_authority_evaluation_independent_verification.py` | 90 |
| `tests/test_phase_147m_authority_evaluation_integration.py` | 59 |
| `tests/test_phase_147n_authority_evaluation_integration_independent_verification.py` | 64 |
| **Total** | **306** |

This reconciles the "183 standalone Authority Evaluation tests" figure
named in this phase's authorizing prompt: 93 + 90 = 183 (the standalone
147G/147H evaluator-chain tests), plus 59 + 64 = 123 (the 147M/147N
integration-chain tests), totaling 306 — internally consistent with both
147N's own reported combined run and this phase's own re-run (§36). One
genuine, minor documentation inaccuracy was found and is recorded in §32:
`docs/implementation/PHASE_147M_...md:482-486` mislabels
`test_phase_147g_authority_evaluation.py` alone as having "183 tests,"
when the true 183 spans two files, not one.

**Coverage assessment**: unit behavior, persistence, corruption, restart/
recovery (single-process), non-gating, and compatibility are all covered
by tests independently confirmed to exist and exercise real behavior (not
mocks) against a real filesystem. **Meaningful gaps**, independently
identified: no multi-process concurrency test (§14, disclosed by 147M
itself); no CLI-level test of the actual `decision_session` production
composition root with Authority Evaluation wired in — because it never is
(§6), no test exercises the chapter through its real, shipping entry
point at all; no disk-full/resource-exhaustion test; no symlink-attack
test (§20). Test count (306, or 123 for the integration chapter
specifically) is not, on its own, proof of production readiness — the
tests exhaustively exercise the library in isolation, which is real and
valuable evidence, but they do not and cannot substitute for a test that
exercises the actual CLI wiring, because that wiring does not exist.

---

## 32. Known Limitations Register

| ID | Source | Description | Severity | Component | Operational impact | Mitigation | Certification effect |
|---|---|---|---|---|---|---|---|
| AESIC-N-01 | Phase 147N | Canonical pointer read path (`read_canonical`/`read_record`) does not validate embedded `package_id` against the query key | Major | `storage.py` | Silent cross-key resolution possible only via filesystem tampering | Unreachable via AES public API (write-path guarantee); repair recommended | Contained; repair required before final certification (§41) |
| AESIC-N-02 | Phase 147N | Post-crash retry produces a second content-equivalent AER rather than literally rediscovering the orphan under its original `evaluation_id` | Informational | `service.py`/`storage.py` | None observed | None required | No effect |
| AESIC-O-01 | Phase 147O (this phase) | AES is never constructed or invoked on any production path; `decision_session.py:208` never supplies `authority_evaluation_service` | Major | `decision_session.py` / composition root | Chapter is fully inert in the shipping product today | None currently — capability is simply dormant, which is safe | **Blocks certification** (§40); repair = wiring phase (§41) |
| AESIC-O-02 | Phase 147O (this phase) | No CLI exposes `diagnostics.py`; operator inspection requires custom Python | Minor | Operational supportability | Cannot observe chapter behavior without writing code | None; out of AESIC-001's own scope | Does not block; recorded as observation |
| AESIC-O-03 | Phase 147O (this phase) | `FilesystemAuthorityRegistry.write_declaration`'s docstring claims overwrite-refusal it does not implement | Minor | `registry_filesystem.py` | None on the certifiable read path (never called by AES) | Documentation/code correction recommended | Does not block |
| AESIC-O-04 | Phase 147O (this phase) | No multi-process concurrency test; last-write-wins pointer semantics unverified across processes/hosts | Minor–Major depending on deployment | `storage.py` | Possible lost supersession under true multi-process concurrency | Documented as disclosed constraint (single-writer-process assumption) | Does not block for single-process deployment; would need addressing before any multi-process rollout |
| AESIC-O-05 | Phase 147O (this phase) | `PHASE_147M_...md:482-486` states 183 tests for one file; true figure spans two files | Informational | Documentation only | None | Correct the sentence if the report is ever revised | No effect |
| AESIC-O-06 | Phase 147O (this phase) | `Registry` adapter's duplicate-detection requirement (AESIC-REQ-044) is satisfied only by structural argument, not an executable scan | Minor | `registry_filesystem.py` | Requirement is formally unfalsifiable against this concrete adapter | None needed given the structural guarantee holds for a real filesystem | Does not block |

---

## 33. Certification Criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Architecture complete | Met |
| 2 | Contract frozen and independently verified | Met |
| 3 | Implementation complete | Met |
| 4 | Implementation independently verified | Met |
| 5 | Production path reachable | **Not met** (§6, AESIC-O-01) |
| 6 | Persistence durable | Met |
| 7 | Restart safe | Met |
| 8 | Recovery safe | Met |
| 9 | Concurrency bounded and understood | Met with observation (single-process only, §14) |
| 10 | Security posture acceptable | Met with observation (§20 — several unmitigated-but-disclosed items, none exploitable via the public API) |
| 11 | Diagnostics sufficient | Met with observation (no CLI, §18) |
| 12 | Failure recovery supportable | Met with observation (manual retry only, no automated recovery/alerting) |
| 13 | Backward compatibility preserved | Met |
| 14 | Rollback possible | Met |
| 15 | Disclosure-only semantics preserved | Met |
| 16 | Non-gating guarantees demonstrated | Met |
| 17 | Runtime capability unchanged | Met |
| 18 | No unresolved Blocking finding | Met (AESIC-N-01/AESIC-O-01 are classified Major, not Blocking) |
| 19 | Any unresolved Major finding is repaired or explicitly accepted with demonstrated containment | **Not met** — AESIC-N-01 is contained and acceptable to defer; **AESIC-O-01 has no containment argument to accept, because there is nothing to contain against — it is an absence of activation, not a risk being managed.** It is not "acceptable as-is" in the sense §19 requires for a Major finding to permit certification; it is a readiness gap that must be closed by a wiring phase, not merely accepted. |
| 20 | Known limitations documented | Met (§32) |

**18 of 20 criteria met or met-with-observation; 2 not met (#5, #19), both
tracing to the same root cause (AESIC-O-01).**

---

## 34. Findings

| Finding | Severity | Evidence | Affected criterion | Containment | Certification effect |
|---|---|---|---|---|---|
| AESIC-N-01 | Major | §15 | #19 (partially — this finding alone is containable) | Demonstrated by construction (`service.py:280-286`) | Does not by itself block; repair still recommended |
| AESIC-O-01 | Major | §6 | #5, #19 | None applicable — dormancy, not a managed risk | **Blocks certification** |
| AESIC-O-02 | Minor | §18 | #11 | N/A | Does not block |
| AESIC-O-03 | Minor | §8 | — | N/A | Does not block |
| AESIC-O-04 | Minor (single-process); would be Major for multi-process rollout | §14 | #9 | Disclosed constraint | Does not block current (single-process) scope |
| AESIC-O-05 | Informational | §31 | — | N/A | Does not block |
| AESIC-O-06 | Minor | §8 | #21 (Registry) area | Structural guarantee | Does not block |

No Blocking-severity finding was identified. AESIC-O-01 is classified Major
rather than Blocking because it represents an absence of risk (a dormant,
byte-for-byte-unchanged system), not an active defect — but it
independently fails a named mandatory certification criterion (#5) in a
way this phase's own charter (§33: "these are not interchangeable" —
implemented, independently verified, operationally reachable, operationally
supportable, certifiable) anticipated as possible and asked to be stated
explicitly rather than smoothed over.

---

## 35. Operational Readiness Verdict

**AUTHORITY EVALUATION INTEGRATION NOT OPERATIONALLY READY.**

The chapter is implemented, independently verified, and would be safe to
activate — persistence, restart, recovery, single-process concurrency,
non-gating semantics, and runtime preservation all independently hold up
under this phase's own fresh inspection. It is not operationally ready
today because it is not operational at all: no production entry point
constructs or invokes it (§6). "Operationally ready" requires more than
"safe if it ran" — it requires that it can run, through a supported path,
which it currently cannot.

---

## 36. Chapter Certification Verdict

**AUTHORITY EVALUATION INTEGRATION CHAPTER NOT CERTIFIED.**

Absence of a Blocking finding is not treated as automatic certification,
per this phase's own charter. Certification-with-observations was
considered and rejected: the conditions that permit it (§40 of the
authorizing prompt — no Blocking finding remains; any unresolved Major
finding is demonstrably contained; the public production path cannot
reach the defect; operational constraints are explicit; no integrity/
authorization/execution guarantee is silently weakened; a follow-up
repair is clearly recorded) are satisfied for **AESIC-N-01 alone**, but
**AESIC-O-01 has no analogous containment argument available** — there is
no "public production path" for it to be safely unreachable through,
because there is no production path for it to be part of at all. A
chapter with zero production reachability is not a certified capability
with an accepted residual risk; it is a verified, dormant library
awaiting activation. This phase declines to certify a chapter that cannot
currently be exercised by any real user or operator action, consistent
with the certification criteria table (§33, criterion #5) and this
phase's explicit charter to state a library-complete-but-not-reachable
finding rather than certify around it.

---

## 37. Recommended Next Phase

**147O.1 — Authority Evaluation Production Wiring.** Narrowly scoped:
construct a real `AuthorityEvaluationService` (with a real
`FilesystemAuthorityRegistry` and `AuthorityEvaluationRecordStore`) in
`src/pcae/commands/decision_session.py`'s composition root and pass it as
`SessionApplicationService(session_coordinator,
authority_evaluation_service=...)`; add the corresponding
`evaluate_authority_stage_1` call at the appropriate CLI point named by
AESIC-001 §9.1. Should not redesign AES, amend AESIC-001, or change
external behavior beyond activating the already-implemented, already-
verified mechanism. Should include: a real end-to-end CLI-level test
exercising the wired path (closing the coverage gap named in §31); a
minimal Registry/template provisioning procedure (closing part of §8/§9's
operational gaps); and, given §18's finding, consideration of whether a
minimal read-only diagnostics CLI command is warranted at the same time
(optional, not required by AESIC-001 itself).

**147O.2 — Canonical Pointer Cross-Key Binding Repair (AESIC-N-01).**
As specified by this phase's authorizing prompt: narrowly scoped to
repairing AESIC-N-01 by enforcing storage-layer compound-key binding
during canonical-pointer reads and writes in `storage.py`
(`read_canonical`/`read_record`), without redesigning AES or changing
external behavior. Should include: root-cause reconstruction (already
performed at §15 of this report and directly reusable), a bounded
implementation repair (an embedded-`package_id`/`evaluation_id`
consistency check mirroring `registry_filesystem.py`'s existing pattern),
direct lower-level API tests, cross-key substitution tests, persistence
regression tests, and an independent-verification recommendation.

**147O.3 — Authority Evaluation Integration Chapter Re-Certification.**
Following both of the above, re-run this phase's own assessment
(§5-§34) against the wired, repaired system and issue a fresh
certification verdict. This recommendation is not itself authorization
for any of the above phases; each requires its own separate human
authorization before implementation work begins.
