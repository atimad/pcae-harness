# Phase 145D — SessionRepository Concrete Filesystem Implementation

**Status:** Complete.
**Mode:** Implementation, converting IWPC-001 v1.1 §13's frozen
`SessionRepository` storage contract (IWPC-REQ-066–077) into production
code.
**Governing authority:**
`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
(IWPC-001 v1.1, FROZEN §13, §19.1, §21, §22, §23),
`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.1, §4.10
persistence boundary), `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`
(PEC-001, atomic-write precedent only), Phase 143K (`SessionRepository`
ABC), Phase 145A/145B/145C.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Deliverable:**
`src/pcae/interactive_workflow/persistence/filesystem_repository.py`
(new module, `FilesystemSessionRepository`), two new error classes in
`src/pcae/interactive_workflow/errors.py`
(`SessionAlreadyExistsError`, `SessionStoreCorruptError`, the latter
explicitly named-but-undefined by IWPC-REQ-075),
`tests/test_phase_145d_session_repository_filesystem_implementation.py`
(43 new tests), this phase report.

---

## 1. Scope

This phase implements exactly one class: `FilesystemSessionRepository`,
the first concrete storage backend for the `SessionRepository` ABC
(`interactive_workflow/persistence/repository.py`, Phase 143K, unmodified
by this phase). No CLI command, transport adapter, Pending-Readiness
Store, publication orchestration, application service,
governance-record publish, or engineering execution capability was
implemented. No contract text (IWC-001, PEC-001, CHGR-001, IWPC-001) was
changed.

## 2. Placement Decision

IWPC-REQ-067 assigns ownership of the concrete implementation to "the
CLI/transport layer (this contract), not `SessionCoordinator`." No
CLI/transport package exists yet in this repository (its implementation
is explicitly out of this phase's scope, and out of 145D's No-Go list),
so there is no existing location to place it that matches that ownership
statement literally. Given the repository's own flat-module-per-concern
convention (`interactive_workflow/persistence/{repository.py,
migration.py}`), and since the ABC itself already lives in this package,
the new concrete class is placed as a sibling module,
`interactive_workflow/persistence/filesystem_repository.py`. This is a
placement judgment call, not an architectural reinterpretation: the class
still depends on nothing outside serialization and stdlib filesystem
primitives (§5 below), so IWPC-REQ-067's ownership statement is satisfied
functionally (no coupling to `SessionCoordinator` or any workflow
controller) even though the file does not physically live under a
not-yet-existing CLI/transport package. A future CLI/transport phase MAY
relocate or re-export this class without changing its behavior.

## 3. Wire Format Decision

IWPC-REQ-074 requires a store-level `schema_version`
(`"decision-session-store/1.0"`), "independent of and in addition to"
`Session`'s own `schema_version`
(`"interactive-workflow-session/0.1"`, produced by
`serialization.schema.to_payload`). Flattening both into one JSON object
would collide on the `schema_version` key. This phase resolves that by
nesting: the persisted file is
`{"schema_version": "decision-session-store/1.0", "session_id": "<id>",
"session": {...to_payload(session)...}}`. The top-level `session_id` is
redundant with the nested payload's own `session_id` by construction, but
is deliberately duplicated as a cheap identity check on `load` (§6
below) — a corrupt/mismatched top-level `session_id` is detected as
`SessionStoreCorruptError` before the nested payload is even parsed.

## 4. Storage Layout

- `.pcae/decision-sessions/<session_id>.json` (IWPC-REQ-068, 070), one
  flat directory, no sharding.
- Filename is exactly `<session_id>.json`, `session_id` used verbatim
  (IWPC-REQ-069).
- Default umask-governed permissions; no restrictive mode enforced
  (IWPC-REQ-071), verified by a dedicated test asserting no world-writable
  bit.
- Constructor rejects (`ValueError`) a `root` that equals or nests under
  `CHGR_STORAGE_PREFIX` (`.pcae/governance-records/`), independently
  enforcing IWC-001 v1.1 §4.10 / IWC-REQ-049 beyond the default root's own
  correctness.

## 5. Atomic Persistence

`create`/`persist` both route through a private `_write_atomic`: a
`tempfile.mkstemp` in the same directory, write, `flush`,
`os.fsync`, `os.replace`, with `finally`-block cleanup of any leftover
temp file (IWPC-REQ-072, IWPC-REQ-155, IWPC-REQ-161) — mirroring
`cltr/persistence.py`'s `_write_atomic` and
`governance/publication/storage.py`'s `_write_atomic_json`, this
repository's strongest existing durable-write precedent, per IWPC-REQ-072
itself. `json.dumps(..., indent=2, sort_keys=True, default=str)` matches
the transport/persistence canonicalization convention (IWPC-REQ-045/057).
Any `OSError` during the write is mapped to `PersistenceUnavailableError`
without a raw exception string reaching the caller (IWPC-REQ-135–137).
Tests verify: no leftover temp file after a normal write; an injected
`os.replace` failure leaves the prior record completely intact (no
partial write ever lands at the final path) and leaves no temp file
behind; an orphaned pre-existing temp file does not block subsequent
enumeration, load, or persist.

## 6. Corruption Detection and Version Validation

`load` raises `SessionStoreCorruptError` (newly defined per
IWPC-REQ-075, mapped conceptually to `persistence_corrupt`, §19.1) for:
malformed/truncated JSON, an unrecognized store `schema_version`, a
missing/malformed nested `session` payload, a mismatched top-level vs.
nested `session_id`, or any `SerializationFailureError` raised by
`from_payload` while parsing the nested `Session` payload. No
partial/best-effort recovery is attempted in any case — a corrupt file is
left byte-for-byte as found. An unrecognized *`Session`-level*
`schema_version` (as opposed to the store-level wrapper's) surfaces as
`from_payload`'s own `UnsupportedVersionError`, propagated unchanged
(143K's existing, still-correct behavior for that layer).

## 7. Security

- **Identifier validation** (IWPC-REQ-163): every `session_id` passed to
  `load`/`persist`/`exists`/`create` is validated via the existing
  `session.identity.validate_session_id` (`CDS-<uuid4>` regex) before any
  filesystem path is constructed; a non-conforming value raises
  `InvalidIdentifierError` and never reaches `open`/`os.replace`.
  Parametrized tests cover `../etc/passwd`, embedded `..`, embedded `/`
  and `\`, malformed suffixes, and the empty string.
- **Containment** (IWPC-REQ-162): the constructed path's parent is
  compared against the repository's own root before any I/O.
- **Symlink rejection** (IWPC-REQ-162): `load`/`create`/`persist` all
  refuse (`PersistenceUnavailableError`) to operate on a path that is
  itself a symlink, whether it points to another session file or outside
  the storage root entirely; a storage root that is itself a symlink is
  likewise refused. Both scenarios are directly tested.
- **`list_session_ids`** silently skips dotfiles, non-`.json` entries,
  subdirectories, symlinks, and any filename whose stem does not parse as
  a valid session id — it never loads a session body to decide whether to
  include it (verified by a test that fails the run if `from_payload` is
  ever called during enumeration).

## 8. Concurrency

No locking primitive (`fcntl`, `portalocker`, `filelock`) is present in
the module (asserted by a dedicated test), consistent with IWPC-REQ-073.
`persist` is last-write-wins at the filesystem layer (IWPC-REQ-141):
two sequential `persist` calls leave only the second writer's state, with
no error and no merge — the disclosed, accepted v1.0 behavior, not a
gap this phase silently introduced.

## 9. Test Strategy and Results

`tests/test_phase_145d_session_repository_filesystem_implementation.py`
— 43 tests: interface conformance (2), repository operations
(create/load/persist/exists/list, 10), storage layout / wire format (5),
atomicity (5), corruption detection (6), security (path traversal
parametrized + symlink handling + permissions, 9), concurrency (2),
round-trip compatibility (1), and a dependency-boundary AST-based
forbidden-import test (1) enforcing that the module never imports
`pcae.cli`, `pcae.commands`, `pcae.governance.publication`,
`pcae.lifecycle`, or the Permission Broker modules.

Regression: `tests/test_iwc_143k_session_infrastructure.py` and every
other interactive-workflow/IWC test module re-run unmodified alongside
this phase's suite — all passed. Full repository `python -m pytest` and
the `fast_green` marker suite both run at validation time (results below).
No file under `src/pcae/interactive_workflow/persistence/repository.py`,
any orchestration/session/state_machine/evidence/clarification/preview/
confirmation module, or `src/pcae/governance/**` was modified, so no
prior phase's certification is affected by construction.

## 10. Requirement Traceability (selected)

| Requirement | Satisfied by |
|---|---|
| IWPC-REQ-066 | `FilesystemSessionRepository` implements exactly `create`/`load`/`persist`/`exists`/`list_session_ids`; no `delete`/`cleanup` method exists. |
| IWPC-REQ-067 | §2 above; module depends only on serialization + stdlib. |
| IWPC-REQ-068–071 | §4 above. |
| IWPC-REQ-072 | §5 above. |
| IWPC-REQ-073 | §8 above; no locking primitive in the module. |
| IWPC-REQ-074 | §3 above. |
| IWPC-REQ-075 | §6 above; `SessionStoreCorruptError` newly defined in `errors.py`. |
| IWPC-REQ-076 | `load` performs no staleness computation; returns the loaded `Session` unchanged. |
| IWPC-REQ-077 | No delete/cleanup method exists; sessions accumulate as durable artifacts. |
| IWPC-REQ-135–137 | Every raised exception carries a human-readable sentence, the known `session_id`, and no raw exception text/traceback/path. |
| IWPC-REQ-141, 147 | §8 above. |
| IWPC-REQ-148, 150, 155 | §5 above; interrupted-write tests. |
| IWPC-REQ-160–163 | §7 above. |

## 11. No-Go — Confirmed Not Done By This Phase

- No CLI command was implemented.
- No transport adapter was implemented.
- No Pending-Readiness Store was implemented.
- No publication orchestration, application service, or
  governance-record publish behavior was implemented.
- No engineering execution capability was introduced; `pcae runtime
  inspect` remains Observed / observe / unavailable before and after this
  phase.
- No compare-and-set / expected-version mechanism was added; IWPC-REQ-141
  disclosed last-write-wins is preserved exactly, not silently upgraded.
- IWC-001, PEC-001, CHGR-001, IWPC-001 contract text was not modified.
- `SessionRepository`'s existing responsibility was not broadened; the
  new class implements exactly the ABC's five existing abstract methods.

## 12. Recommended Next Phase

**145E — Pending-Readiness Store Concrete Filesystem Implementation**
(IWPC-001 v1.1 §14, IWPC-REQ-078–092), the sibling store this phase's own
governing prompt names. This recommendation does not authorize 145E.
