# Phase 145E — Pending-Readiness Store Concrete Filesystem Implementation

**Status:** Complete.
**Mode:** Implementation, converting IWPC-001 v1.1 §14's frozen
Pending-Readiness Store contract (IWPC-REQ-078–092) into production code.
**Governing authority:**
`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
(IWPC-001 v1.1, FROZEN §14, §15, §17, §19.1, §21, §22, §23, §25),
`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.2, §26
provenance widening), `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`
(PEC-001, non-authoritative-store precedent only), Phase 143O
(`PublicationReadinessPackage`, `publication_handoff_schema`), Phase
144F (provenance widening), Phase 145D (`FilesystemSessionRepository`,
the sibling store this phase mirrors).
**Runtime:** Observed / observe / unavailable, confirmed unchanged
before and after this phase (`pcae runtime inspect --json`).
**Deliverable:**
`src/pcae/interactive_workflow/persistence/filesystem_pending_readiness_store.py`
(new module, `FilesystemPendingReadinessStore`), six new error classes in
`src/pcae/interactive_workflow/errors.py`
(`PendingReadinessPackageNotFoundError`,
`PendingReadinessPackageAlreadyExistsError`,
`PendingReadinessStoreCorruptError`,
`PendingReadinessDigestMismatchError`,
`PendingReadinessAttemptConflictError`,
`PendingReadinessAlreadyConsumedError`),
`tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`
(74 new tests), this phase report.

---

## 1. Scope

This phase implements exactly one class: `FilesystemPendingReadinessStore`,
the concrete filesystem backend for the Pending-Readiness Store IWPC-001
v1.1 §14 defines. No CLI command, transport adapter, decision-session
command handler, application service, publication orchestration,
governance-record publish behavior, or engineering execution capability
was implemented. No contract text (IWC-001, PEC-001, CHGR-001, IWPC-001)
was changed. `SessionRepository`/`FilesystemSessionRepository` behavior
was not modified.

## 2. No Abstract Base Class Exists for This Store

Unlike Phase 145D (`FilesystemSessionRepository`, a concrete
implementation of the pre-existing `SessionRepository` ABC, Phase 143K),
IWPC-001 v1.1 §14 defines no separate interface or ABC for the
Pending-Readiness Store, and none exists anywhere else in this
repository. `FilesystemPendingReadinessStore` is therefore the sole
concrete class -- there is no ABC to implement against, and this phase
does not invent one (inventing an ABC nobody else consumes would be an
unrequested abstraction). Its public method surface is derived directly
from §14's IWPC-REQ-078–092 and the "Required Store Operations" section
of this phase's governing prompt: `create`, `load`, `exists`,
`list_package_ids`, `find_by_session_id`, and
`record_publication_attempt` (the single method covering both attempt
linkage, IWPC-REQ-087, and success/failure disposition, IWPC-REQ-086/
088/089 -- combined because the contract ties them together as one
atomic disposition transition, not two independent operations).

## 3. Placement Decision

Mirrors Phase 145D §2's reasoning exactly: IWPC-REQ-067's CLI/transport
ownership statement has no existing physical package to live under (no
CLI/transport package exists yet), so the module is placed as a sibling
of `filesystem_repository.py` in
`interactive_workflow/persistence/`. Functional ownership is satisfied
independent of physical location -- the module depends only on
`PublicationReadinessPackage`, its existing serialization, stdlib
filesystem primitives, and `session.identity` (for validating the
embedded `session_id`), never on `SessionCoordinator`, the Publication
Coordinator, or any workflow controller.

## 4. Storage Layout

- `.pcae/decision-sessions/pending-packages/<package_id>.json` --
  packages not yet successfully published (IWPC-REQ-088).
- `.pcae/decision-sessions/pending-packages/consumed/<package_id>.json`
  -- packages moved here (`os.replace`, never deleted) on successful
  publication (IWPC-REQ-088).
- This nests inside the same parent directory `FilesystemSessionRepository`
  uses for its own flat session-file layout (IWPC-REQ-070). This is
  explicitly frozen by IWPC-REQ-088's own literal path, not a layout
  choice made here, and does not create a functional overlap:
  `FilesystemSessionRepository.list_session_ids` already skips directory
  entries (`entry.is_dir()`), so `pending-packages/` is invisible to
  session enumeration by construction. A regression test
  (`test_store_never_writes_under_chgr_storage_prefix` alongside a manual
  verification that `FilesystemSessionRepository.list_session_ids`
  ignores the nested directory) confirms no cross-store interference.
- Default umask-governed permissions; no restrictive mode enforced
  (mirroring IWPC-REQ-071's session-store precedent), verified by a
  dedicated no-world-writable-bit test.
- Constructor rejects (`ValueError`) a `root` that equals or nests under
  `.pcae/governance-records/` (`CHGR_STORAGE_PREFIX`), independently
  enforcing IWC-001 v1.1 §4.10 / IWC-REQ-049, mirroring Phase 145D's own
  guard.

## 5. Package-Identifier Format Decision (Disclosed)

IWPC-REQ-163 anticipates validating `package_id` against "the
package-id format `PublicationHandoff.build_package` produces" --
but `build_package` accepts `package_id` as a caller-supplied string
parameter with no fixed shape (only "non-empty", enforced by
`PublicationReadinessPackage.__post_init__`); no `package_id`-generation
scheme exists anywhere in this repository as of this phase (deferred to
a future CLI/transport phase that would assign package ids). This is a
disclosed gap in the current implementation state, not a contradiction
in the frozen contract text itself -- IWPC-REQ-163's own wording already
anticipates a format that does not yet exist. Per this phase's own
Findings and Defect Handling guidance ("If the frozen contract is
discovered to contain a Blocking contradiction... document the
contradiction... otherwise fail the phase closed and recommend a bounded
contract-repair phase" and "classify... Non-Blocking"), this is
classified **Non-Blocking**: the underlying security intent (reject
anything that is not a safe path component before it is ever joined into
a filesystem path) is fully satisfiable without the not-yet-defined
specific format, so `is_valid_package_id` validates the generic shape --
non-empty, ≤200 characters, `[A-Za-z0-9][A-Za-z0-9._-]*`, no path
separator, no bare `.`/`..` -- rather than a specific generated-id regex.
A future phase that defines the actual `package_id` generation scheme
MAY narrow this validator additively without changing this store's
public interface.

## 6. Wire Format

`STORE_SCHEMA_VERSION = "pending-readiness-store/1.0"` (IWPC-REQ-111's
own named example value), nested exactly as IWPC-REQ-111 specifies --
wrapping, never replacing, `publication_handoff_schema.to_payload`'s
existing output:

```json
{
  "schema_version": "pending-readiness-store/1.0",
  "package_id": "...",
  "session_id": "...",
  "package_digest": "<sha256 hex>",
  "persisted_at": "...",
  "disposition": "pending" | "consumed",
  "record_id": null | "...",
  "publication_attempt_id": null | "...",
  "consumed_at": null | "...",
  "attempts": [{"attempt_id": "...", "outcome": "succeeded"|"failed", "timestamp": "..."}],
  "package": { ...publication_handoff_schema.to_payload(package)... }
}
```

The top-level `package_id`/`session_id` are redundant with the nested
package's own fields by construction, but deliberately duplicated as a
cheap self-consistency check on `load` -- a mismatch is
`PendingReadinessStoreCorruptError` before any further trust is placed
in the file (IWPC-REQ-082's session-binding verification, satisfied at
this self-consistency layer since no external comparison value is
supplied to `load(package_id)`).

## 7. Package Digest (IWPC-REQ-081, IWPC-REQ-057, IWPC-REQ-165)

A whole-package SHA-256 content digest is computed at `create` time over
`json.dumps(publication_handoff_schema.to_payload(package), sort_keys=True,
default=str)` -- the exact canonicalization convention IWPC-REQ-057
mandates for persisted-artifact digesting, matching
`preview.builder.PreviewBuilder.compute_digest`'s own established
pattern in this repository. `load` always recomputes the digest and
compares it to the persisted value, raising
`PendingReadinessDigestMismatchError` (mapped to
`artifact_binding_mismatch`) on any mismatch -- the store never trusts a
persisted digest without recomputation (IWPC-REQ-165). This is exercised
by dedicated tests: a tampered package field, a tampered stored digest
value, and a manually injected extra field, all detected identically.

## 8. Publication Attempt Binding and Disposition (IWPC-REQ-086–089)

`record_publication_attempt(package_id, attempt_id, outcome, timestamp,
record_id=None, publication_attempt_id=None)` is the single entry point
for both attempt-linkage recording and disposition transition, since the
contract ties them to one invocation ("every `publish` invocation...
MUST append an attempt-linkage record", IWPC-REQ-087, immediately
followed by the disposition consequence, IWPC-REQ-088/089):

- **Idempotent replay** (same `attempt_id`, same `outcome`): a no-op,
  returns the existing record unchanged -- no duplicate attempt entry,
  no re-write.
- **Conflicting replay** (same `attempt_id`, different `outcome`):
  `PendingReadinessAttemptConflictError`.
- **New attempt against an already-`consumed` package**:
  `PendingReadinessAlreadyConsumedError` -- a consumed package's
  disposition is terminal (IWPC-REQ-088's "moved, not deleted"
  retention guarantee; in practice this path is expected to be
  preempted by PEC-001's own exclusive-create idempotency marker,
  IWPC-REQ-144, before this store's attempt-binding is even called, but
  the store still fails closed defensively rather than silently
  accepting a write into a consumed record).
- **`outcome="succeeded"`**: requires `record_id` (raises `ValueError`
  otherwise -- a basic call-shape validation, not a persistence-layer
  failure); appends the attempt entry, sets `disposition="consumed"`,
  `record_id`, `publication_attempt_id`, `consumed_at`, writes the
  complete new wrapper atomically to `consumed/<package_id>.json`, then
  removes the pending-location file (IWPC-REQ-088's literal "moved" --
  content-preserving copy-then-unlink rather than a bare `os.rename`,
  because the write must also *change* the wrapper content, unlike a
  pure rename).
- **`outcome="failed"`**: appends the attempt entry only; the package
  file is rewritten atomically in place at its existing pending-location
  path, `disposition` remains `"pending"` (IWPC-REQ-089) -- unmoved, so a
  retry attempt (a later call with a new `attempt_id`) still finds it.

## 9. Recovery Semantics for the Two-Step Success Move (IWPC-REQ-154)

The "succeeded" path is two filesystem operations (atomic consumed-file
write, then pending-file unlink), not a single atomic cross-directory
rename, because the write must also transform the wrapper content
(new disposition, new metadata) rather than relocate identical bytes.
This phase resolves the resulting interruption window exactly as
IWPC-REQ-154 anticipates ("an interruption... leaves the package still
in `pending-packages/` even though publication succeeded; the next
`publish` invocation MUST detect this via PEC-001's own replay/
idempotency-marker check... before this store's disposition is
consulted"): `load` always checks the `consumed/` location *first*, and
only falls back to the pending location if no consumed record exists.
If both a consumed record and a stale pending duplicate happen to
coexist post-interruption, the consumed record is authoritative and the
stale pending copy is functionally invisible to `list_package_ids`/
`find_by_session_id` (both explicitly exclude any `package_id` that also
exists under `consumed/`) -- no ambiguity, no silent data loss, no
requirement for a background sweep. This is directly exercised by
`test_recovery_prefers_consumed_over_stale_pending_duplicate`.

## 10. Corruption Detection and Version Validation

`load` raises `PendingReadinessStoreCorruptError` for: malformed/
truncated JSON, a non-object top-level payload, an unrecognized store
`schema_version`, a mismatched top-level vs. nested `package_id`, a
mismatched top-level vs. nested `session_id`, a missing/malformed nested
`package` payload (including any `UnsupportedVersionError` or
`PublicationHandoffSerializationError` the existing
`publication_handoff_schema.from_payload` raises), a missing/malformed
`persisted_at`, an unrecognized `disposition` value, or malformed
attempt-linkage entries. `PendingReadinessDigestMismatchError` is raised
separately (not folded into the generic corruption error) so a caller
can distinguish "this file is structurally broken" from "this file is
structurally well-formed but its content does not match its recorded
digest" -- the latter is the artifact-tampering signal IWPC-REQ-165
specifically calls out. No partial/best-effort recovery is attempted in
any case; a corrupt file is left byte-for-byte as found.

## 11. Security

- **Identifier validation** (IWPC-REQ-163): every `package_id` is
  validated via `is_valid_package_id` before any filesystem path is
  constructed; a non-conforming value raises `ValueError` and never
  reaches `open`/`os.replace`. Parametrized tests cover `../etc/passwd`,
  absolute paths, embedded `/` and `\`, bare `.`/`..`, the empty string,
  and an oversized identifier.
- **`session_id` validation**: every `session_id` supplied to `create`/
  `find_by_session_id` is validated via the existing
  `session.identity.validate_session_id` (`CDS-<uuid4>` regex), reused
  unchanged from Phase 145D -- no second session-id validator was
  written.
- **Containment** (IWPC-REQ-162): each constructed path's parent is
  compared against the store's own pending/consumed root before any I/O.
- **Symlink rejection** (IWPC-REQ-162): `load`/`create`/
  `record_publication_attempt` all refuse
  (`PersistenceUnavailableError`) to operate on a path that is itself a
  symlink, whether it points to another package file or outside the
  storage root entirely; a storage root that is itself a symlink is
  likewise refused. Both scenarios are directly tested.
- **`list_package_ids`** silently skips dotfiles, non-`.json` entries,
  subdirectories, symlinks, and any filename whose stem does not parse
  as a valid package id, and never loads a full package body to decide
  inclusion (verified by a test that fails the run if
  `_package_from_payload` is ever called during enumeration).

## 12. Concurrency

No locking primitive (`fcntl`, `portalocker`, `filelock`) is present in
the module (asserted by a dedicated test), consistent with IWPC-REQ-073's
repository-wide convention. `create` provides real mutual exclusion for
initial creation (exclusive existence check before write, matching
`SessionRepository.create`'s own semantics -- a conflicting duplicate
`create` always fails, deterministically, regardless of content
equality). `record_publication_attempt` is idempotent by `attempt_id`,
which is this store's practical answer to IWPC-REQ-144's "the second of
two concurrent `publish` invocations... MUST receive
`publication_already_completed`... never a double-published CHGR" at the
store layer: a replayed identical `(attempt_id, outcome)` pair is a safe
no-op, and PEC-001's own exclusive-create idempotency marker remains the
authoritative mutual-exclusion mechanism this contract relies on
(IWPC-REQ-144, unmodified, not re-implemented here).

## 13. Test Strategy and Results

`tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`
-- 74 tests: store identity/default location (3), core operations
(create/load/exists/list/find, 15), exact artifact preservation (4),
digest verification (4), duplicate/conflict behavior (7), publication
disposition (5), atomicity (5), corruption detection (10), security
(path-traversal parametrized + symlink handling + permissions, 9),
concurrency (2), recovery (3), and a dependency-boundary AST-based
forbidden-import test (1) enforcing that the module never imports
`pcae.cli`, `pcae.commands`, `pcae.governance.publication`,
`pcae.lifecycle`, the Permission Broker modules, or
`interactive_workflow.orchestration`/`session.coordinator`. All 74 pass.

Regression: `tests/test_phase_145d_session_repository_filesystem_implementation.py`
(43 tests) re-run unmodified alongside this phase's suite -- all pass
(117 total across both modules). The full `interactive_workflow`/`iwc_`/
`publication`/`serialization`/`persistence`-scoped test selection (1723
tests) passes except two pre-existing, reproduced-on-clean-`main`
wheel-packaging failures unrelated to this phase
(`test_cltr_authority_136ah_publication.py`,
`test_cltr_authority_136ai_publication_independent.py`, both asserting
about `pcae/cltr/authority/bindings.py`'s wheel inclusion -- confirmed
via `git stash` to fail identically before this phase's changes). The
`fast_green` marker suite (`python -m pytest -m fast_green -n auto`)
passes at 4391 (baseline 4390 plus this phase's own fast-green-eligible
additions). Full-repository `python -m pytest -n auto`: **26424 passed,
39 failed, 10 skipped** (1947.53s). All 39 failures were independently
reproduced against unmodified `main` (`git stash`, re-run of the exact
39 failing node ids: 37/39 failed identically in isolation; the
remaining 2 -- `test_136al_package_import_is_side_effect_free`,
`test_audit_verify_cli` -- are order/parallelism-dependent flakes,
confirmed present on `main` as well when accounting for xdist worker
scheduling, not a regression introduced by this phase). None of the 39
touch `interactive_workflow`, `persistence`, `publication_handoff`,
`serialization`, or this phase's own module -- they span wheel-packaging
assertions (`test_cltr_authority_*`), `shell_gate`, notification
authority-binding modules, `finalization_transaction`,
`test_rendering_134e5`, migration verification
(`test_cltr_135o_integration`, `test_cltr_migration_135p_verification`),
`test_phase_reports`, and `test_bootstrap_todo_consistency` (the latter
reacts to whichever task/roadmap state is currently active, not to this
phase's own code).

## 14. Requirement Traceability

| Requirement | Satisfied by |
|---|---|
| IWPC-REQ-078 | `FilesystemPendingReadinessStore.create`/`load`, storing a durable copy spanning process boundaries under `.pcae/decision-sessions/pending-packages/`. |
| IWPC-REQ-079 | §1/§8 above; the store never evaluates authorization, never decides publication success -- `record_publication_attempt` records caller-supplied `record_id`/`publication_attempt_id`/`outcome` verbatim, never derives them. |
| IWPC-REQ-080 | `package.package_id` used verbatim as the storage key (`<package_id>.json`); no second identifier assigned. |
| IWPC-REQ-081 | §7 above. |
| IWPC-REQ-082 | §6 above (self-consistency check) plus `find_by_session_id` (session_id → package lookup) and `load` (package_id → package lookup) as the two distinct lookup paths the contract names. |
| IWPC-REQ-083 | No separate confirmation-binding field added; `confirmation_request_id`/`confirmation_response_id`/`confirmation_statement`/`confirmation_timestamp` round-trip verbatim as part of the nested package payload (already required non-empty by `PublicationReadinessPackage.__post_init__`). |
| IWPC-REQ-084 | `built_at` preserved verbatim inside the nested package; `persisted_at` recorded separately by the store at `create` time. |
| IWPC-REQ-085 | No time-based expiry field or check exists in this store; staleness is explicitly out of this store's scope (a future `publish` command's responsibility, checking the bound session's live state). |
| IWPC-REQ-086 | `record_id`/`publication_attempt_id` are `None` until a `succeeded` `record_publication_attempt` call sets them; never present before, never mutating the underlying `PublicationReadinessPackage` object. |
| IWPC-REQ-087 | §8 above; `attempts` tuple, append-only, idempotent-by-key. |
| IWPC-REQ-088 | §8/§9 above. |
| IWPC-REQ-089 | §8 above (`outcome="failed"` path). |
| IWPC-REQ-090 | `load` on a `consumed/` record returns the exact, unmodified persisted package -- never reconstructed from session fields. |
| IWPC-REQ-091 | §1 module docstring, §6/§9 above; `test_package_payload_unchanged_after_metadata_update` and `test_consumed_package_payload_unchanged` directly verify the package payload is byte-identical after metadata-only updates. |
| IWPC-REQ-092 | No automatic deletion of `consumed/` packages; no cleanup method exists on this store. |
| IWPC-REQ-093–100 (§15 Artifact Binding) | Package/session/digest self-consistency verified on every `load` (§6); `test_cross_session_reuse_of_package_id_fails_closed`, `test_package_id_mismatch_raises_store_corrupt`, `test_session_id_binding_mismatch_raises_store_corrupt` cover fail-closed behavior at this store's layer of the chain. |
| IWPC-REQ-107 | `find_by_session_id` is the mechanism `decision-session readiness` construction would use to check "no existing pending package for that session_id" before calling `create`. |
| IWPC-REQ-108, 115 | This store adds, removes, or overrides no decision-content field; it persists exactly what `to_payload(package)` already serializes. |
| IWPC-REQ-109 | `package_id` never reassigned once created (`create` raises `PendingReadinessPackageAlreadyExistsError` on any second `create` for the same id, regardless of content). |
| IWPC-REQ-110, 111 | §6/§7 above. |
| IWPC-REQ-112 | This entire implementation. |
| IWPC-REQ-113 | §9 above; `test_consumed_package_still_loadable_for_replay`. |
| IWPC-REQ-114 | Explicitly out of this store's scope (§ IWPC-REQ-085 above); no staleness check added here. |
| IWPC-REQ-135–137 | Every raised exception carries a human-readable sentence, the known `package_id`/`session_id`, and no raw exception text/traceback/path. |
| IWPC-REQ-141, 144, 147 | §12 above. |
| IWPC-REQ-148–156 (§22 Recovery) | §9 above; `test_interrupted_create_leaves_no_package_file`, `test_interrupted_disposition_update_leaves_prior_record_intact`, `test_restart_after_completed_publication_reports_consumed`, `test_restart_after_failed_publication_reports_pending`, `test_recovery_prefers_consumed_over_stale_pending_duplicate`. |
| IWPC-REQ-157–165 (§23 Security) | §11 above. |
| IWPC-REQ-174–177 (§25 Dependency Contract) | This module imports only `PublicationReadinessPackage`, `publication_handoff_schema`, `session.identity`, and stdlib; the forbidden-import AST test enforces no coupling to CLI, commands, governance/publication, lifecycle, Permission Broker, or orchestration/session-coordination modules. |

## 15. No-Go — Confirmed Not Done By This Phase

- No CLI command was implemented.
- No transport adapter was implemented.
- No decision-session command handler was implemented.
- No application service, publication orchestration, or
  governance-record publish behavior was implemented.
- The Publication Coordinator was not invoked, imported, or modified.
- No engineering execution capability was introduced; `pcae runtime
  inspect --json` remains `Observed`/`observe`/`unavailable` before and
  after this phase.
- No automatic authorization or automatic publication was added.
- No background worker or scheduled cleanup was added.
- `SessionRepository`/`FilesystemSessionRepository` was not modified.
- IWC-001, PEC-001, CHGR-001, IWPC-001 contract text was not modified.

## 16. Recommended Next Phase

**145F — Interactive Workflow + Publication Application/Transport
Boundary Implementation Planning or Implementation**, the phase this
phase's own governing prompt names as likely-next, now that both
concrete persistence components (`FilesystemSessionRepository`,
Phase 145D, and `FilesystemPendingReadinessStore`, this phase) exist for
the CLI/transport layer to build against. This recommendation does not
authorize 145F.
