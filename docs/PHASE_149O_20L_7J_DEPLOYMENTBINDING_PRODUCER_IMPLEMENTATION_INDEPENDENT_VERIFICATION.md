# Phase 149O.20L.7J — DeploymentBinding Producer Implementation Independent Verification

## 0. Status

**Verification-only.** No producer implementation modified. No HBDC-001 text amended. No real `DeploymentBinding` created. No repository identity created on Dell. No `pcae init` run on Dell. No Dell mutation of any kind. No first-use election initiated. No CHGR published for first use. No Boundary C work. No HMIC certification. No HATP activation. Companion test module: `tests/test_phase_149o_20l_7j_deploymentbinding_producer_implementation_independent_verification.py` — independent oracle, reconstructs facts from primary source (contract text, production source, git history, live adversarial execution against disposable trust stores), does not import or trust 7I's own test module or report as ground truth.

## 1. Purpose and Method

Independently reconstruct and adversarially verify the `DeploymentBinding` producer (`create_deployment_binding`/`rotate_deployment_binding`/`revoke_deployment_binding`, `src/pcae/core/hatp_deployment_binding_admin.py`, plus `scripts/hatp_deployment_binding_admin.py`) implemented by Phase 149O.20L.7I against HBDC-001 v1.1 §16.1 (`HBDC-REQ-056..070`), independently verified by 149O.20L.7H. Every claim below was independently re-derived this phase by reading primary source and running live adversarial code against disposable trust stores/repositories — 7I's own requirement matrix and test suite were read for orientation but never used as the oracle for any claim in this report.

## 2. True Phase-Entry Commit

`8ef3d2b3` (Phase 149O.20L.7I finalization: "sync idle-task allowed-file list post-finalization"). Working tree clean at entry, `main` in sync with `origin/main` (`git rev-list --count origin/main..HEAD` = 0, independently re-run this phase, not merely re-quoted from the prior session).

## 3. Immutable Pre-7I Baseline and Exact Production Diff

- **Pre-7I baseline commit:** `e9cad634` (Phase 149O.20L.7H's last finalization commit — "sync push-state trust fields for finalization gate"). Independently confirmed via `git log --oneline -- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (only two commits ever touch the contract file: `66c97470` v1.0 freeze, `0b530959` v1.1 amendment by 7G) and `git diff e9cad634 c46d4db4 -- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (empty — 7H made zero contract edits).
- **7I's sole implementation commit:** `f38e0741` ("DeploymentBinding Producer Implementation"). `git show --stat f38e0741` independently re-run this phase: exactly five files added, zero modified, zero deleted —
  - `docs/PHASE_149O_20L_7I_DEPLOYMENTBINDING_PRODUCER_IMPLEMENTATION.md` (622 lines, doc)
  - `scripts/hatp_deployment_binding_admin.py` (245 lines, new admin CLI)
  - `src/pcae/core/hatp_deployment_binding_admin.py` (953 lines, new producer module)
  - `tests/test_hatp_deployment_binding_admin.py` (885 lines, 55 tests)
  - `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py` (305 lines, 41 tests)
- **Production-file diff scope:** `git diff --stat 0b530959^ f38e0741 -- src/pcae scripts schemas` independently re-run — exactly two production files, both new: `scripts/hatp_deployment_binding_admin.py` (+245) and `src/pcae/core/hatp_deployment_binding_admin.py` (+953). No `src/pcae/**` file was modified (only added). No `schemas/**` file touched. No unrelated production change is hidden in the commit.
- **`hatp_bootstrap.py` / `repository_identity.py` byte-identity:** independently confirmed by `git hash-object`, not diff inference — `git hash-object src/pcae/core/hatp_bootstrap.py` at HEAD (`cda8e518d5d8794922ebdcd195c3886228fe8f2f`) is byte-identical to `git show e9cad634:src/pcae/core/hatp_bootstrap.py | git hash-object --stdin` (same hash); identical result for `repository_identity.py` (`eae1db10dcc0c6cdf9267574f60615fdbda55143`, both sides). **`HATPTrustStore` still exposes zero write methods** — independently re-enumerated its public method set (`environment_status`, `load_repository_enrollment`, `lookup_principal`) — all read-only.

## 4. HBDC-001 Contract Immutability

`git diff c46d4db4 HEAD -- docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (7H's own verified-baseline commit to current HEAD) returns empty, independently re-run this phase. HBDC-001 v1.1's text is byte-identical to the text 7H independently verified. No normative modification occurred during implementation.

## 5. Requirement-to-Code Traceability (HBDC-REQ-056..070)

Independently re-read every requirement's text from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` §16.1 and matched it against the actual implementation, not 7I's own matrix:

| Req | Normative rule | Implementation function/path | Adversarial verification this phase |
|---|---|---|---|
| 056 | Writer is a separate, non-agent-writable admin tool | `src/pcae/core/hatp_deployment_binding_admin.py` (sibling module) + `scripts/hatp_deployment_binding_admin.py` (standalone script, no console-script entry) | §7 reachability grep across entire `src/pcae` tree; `pyproject.toml` `[project.scripts]` inspection |
| 057 | `repository_id`/`canonical_deployment_root` derived read-only | `_resolve_repository_id()` (calls `read_repository_identity`, never `ensure_repository_identity`), `_resolve_canonical_root()` (calls `resolve_canonical_deployment_root`) | §9, §10 — absent/malformed/spoofed identity attacks, symlink/relative canonical-root attacks, live |
| 058 | Authority fields from admin enrollment context, not repo-local/agent state | `AuthorityEvidence` dataclass, `_validate_authority_evidence()` | §11 — principal_id/authority_scope pass-through-unchanged assertions, live |
| 059 | Fail-closed on conflict; idempotent no-op on identical create | `create_deployment_binding()`'s `_binding_fields_equal_for_idempotency()` branch | §12 — valid_from temporal attack, conflicting-field attack, live |
| 060 | Rotation/revocation distinct explicit operations, never implicit | Three distinct public functions, no create-time "if exists, rotate" branch | Read-confirmed; `rotate`/`revoke` never called from `create_deployment_binding` |
| 061 | Revoke = field mutation, never delete; rotate = in-place overwrite, no history | `replace(existing, status="revoked", ...)` (revoke); full new `DeploymentBinding(...)` construction (rotate) | §13 — F4 lost-history reconstruction, live |
| 062 | Every operation produces an audit record | `_audit()` called at the end of every code path in all three functions, including both no-op outcomes | §14 — every-operation-emits-one-record, audit-failure-after-mutation, live |
| 063 | Reuse `repository_identity.py::_write_atomic` idiom exactly | `_atomic_write_registry()` — `mkstemp` same dir, `fsync`, `os.replace`, `_reject_symlink` before/after | §15 — fault injection (fsync failure, rename failure), symlink-swap race, live |
| 064 | Explicit fresh-election evidence required, no bare boolean | `AuthorityEvidence.election_reference` mandatory non-empty string, `_require_nonempty_str` | Read-confirmed; no boolean/`approved` parameter exists anywhere in the public API |
| 065 | Election reference recorded as audit metadata only, not cryptographically verified | `_audit()` summary strings interpolate `election_reference` verbatim; no verification call anywhere | Read-confirmed; grep for signature-verification/CHGR-lookup calls in the module returns none |
| 066 | Admin-OS-principal-only invocation, never agent-reachable | No import from `cli.py`/`commands/agent.py`/`core/agent.py`; not a console-script entry point | §7 — full-tree reachability grep, live CLI invocation against real (absent) production root |
| 067 | Strict producer-output timestamp grammar | `_canonical_timestamp_now()` + self-asserting `_TIMESTAMP_PATTERN.fullmatch` | §16 — generated-timestamp grammar check, live; §17 — permissive-consumer-vs-strict-producer, live |
| 068 | Repository-identity creation not gated by this section | Producer never calls `ensure_repository_identity()` (not imported) | §9 — instrumented-spy call-count = 0 during create/rotate/revoke, live |
| 069 | Amendment doesn't itself satisfy a governing CHGR's election condition | No CLI/API path claims election sufficiency beyond recording the reference | Read-confirmed; `ConfirmationDeclinedError` path in the CLI is a local confirm-prompt, not a CHGR/election mechanism |
| 070 | Amendment bytes participate in `implementation_scope_digest` automatically | N/A to this module (property of the contract file's existing HMIC-frozen status, §26 below) | §26 — HMIC frozen-file-set analysis |

Every one of HBDC-REQ-056..070 traced to a concrete implementation site and independently exercised. **Zero Blocking implementation defects found.**

## 6. Public API Reconstruction

Independently enumerated the module's public surface (not copied from 7I's docstring): `create_deployment_binding`, `rotate_deployment_binding`, `revoke_deployment_binding`, `preview_create_deployment_binding`, `preview_rotate_deployment_binding`, `preview_revoke_deployment_binding`, plus the `AuthorityEvidence`/`DeploymentBindingOperationResult`/`DeploymentBindingPreview` data types and a nine-member typed error hierarchy rooted at `HATPDeploymentBindingAdminError`. No generic "write arbitrary field" or "patch registry" bypass API exists anywhere in the module — every write path is one of the three named semantic operations, each fully re-deriving its own candidate record rather than accepting a caller-supplied document fragment.

## 7. Layering and Agent Reachability

Independently grepped for `hatp_deployment_binding_admin` across the **entire** `src/pcae` tree (not merely the three files 7I's own test checks) — the only match is the module's own file. `pyproject.toml`'s `[project.scripts]` defines exactly one console-script entry point, `pcae = "pcae.cli:main"`; the admin script is not installed, not imported by `cli.py`, `commands/agent.py`, or `core/agent.py`, and not reachable through any advisory command path or plugin registry (`pcae runtime inspect` independently re-run this phase: `Registry status: empty`, `Plugin count: 0`). Layering is confirmed as designed: trusted privileged OS caller → `scripts/hatp_deployment_binding_admin.py` → `src/pcae/core/hatp_deployment_binding_admin.py` → `_atomic_write_registry` → filesystem. `HATPTrustStore` (the read consumer) has zero write methods (§3). No CLI/script bypass of producer validation exists — the script imports only the module's public functions, never touches `registry.json` directly.

## 8. Administrative Invocation Boundary

Read `scripts/hatp_deployment_binding_admin.py` in full. It accepts `--repository-root` (a neutral locator for the repo whose identity is being bound — not the trust store) but exposes **no `--protected-root`, `--store-root`, or equivalent flag** anywhere in its argument parser (independently confirmed both by static reading of `_build_parser()` and by live `--help` invocation, §19 below). The only production-path root resolution is `_resolve_protected_root(None) → HATPTrustStore.production().root`, a fixed, non-overridable filesystem path. Live-invoked the real script (no monkeypatching) against this repository with `create --preview`: it correctly resolved the real production Protected Root (`/Library/Application Support/PCAE/HATP/trust-store`), found it absent, and failed closed with `DeploymentBindingTrustStoreUnavailableError`, writing nothing anywhere. `_protected_root` exists only as a private, non-CLI-exposed Python keyword argument on the three module functions (test-only seam) — the production CLI path cannot reach it. Filesystem write permission on the real Protected Root is confirmed as the actual, sole security boundary; nothing in this module or script substitutes for it.

## 9. Producer Self-Authorization Attack

Independently confirmed by full source read: the module never imports or calls `pcae.core.decision_session` or any CHGR-minting function; never calls `ensure_repository_identity()` (not imported at all — confirmed both by import-statement inspection and by an instrumented monkeypatch spy around `repository_identity.ensure_repository_identity` that recorded **zero calls** during a live create→rotate→revoke sequence); accepts no boolean "approved" parameter anywhere in `AuthorityEvidence` or the CLI's argparse definitions; and treats `election_reference` purely as an opaque audit-metadata string, never inspecting or dereferencing it as an authority object. Election/authority references are metadata only, exactly as HBDC-REQ-064/065 require.

## 10. RepositoryIdentity Prerequisite

Live-tested against disposable repositories:

- **Absent identity:** `RepositoryIdentityMissingError` raised before any trust-store access; no registry write occurs.
- **Malformed identity** (`.pcae/repository-identity.json` containing invalid JSON): a `RepositoryIdentityMalformedError` from `read_repository_identity` propagates uncaught; fails closed.
- **Copied/spoofed identity** (byte-copying repo A's `.pcae/` tree into a distinct path, repo B): the producer — by design (§57, read-only derivation from whatever identity file is on disk) — reports repo B's `repository_instance_id` as identical to repo A's, since it does not independently re-derive identity from anything except the file's own content. This is a **known, disclosed trust boundary**, not an unexpected defect: HBDC-REQ-057 requires the writer to derive `repository_id` "read-only, from the target repository's existing `RepositoryIdentity`" — it does not require the writer to detect that a `RepositoryIdentity` file has been copied out of its originating repository (that would require cryptographic binding to filesystem/host state the identity schema does not currently carry — a `RepositoryIdentity`-schema-level property, out of this producer's scope and out of HBDC-001's scope). Practical consequence verified live: because `canonical_deployment_root` (repo B's own distinct filesystem path, independently re-derived per-call, never copied) is one of the compared authority-bearing fields, attempting `create_deployment_binding` for the spoofed repo B against an existing repo A binding deterministically raises `DuplicateConflictingBindingError` (repeated twice, same result both times) — fail-closed, never an incorrect distinct-entry creation and never a silent `ALREADY_SATISFIED` masking two different physical locations sharing one `repository_id`.
- **Supplied repository-ID mismatch:** not applicable — the public API accepts no caller-supplied `repository_id` parameter at all (§057's own design), so this specific attack surface does not exist to attack.

## 11. Canonical Root Derivation

Live-attacked: redundant relative-path segments (`repo/./../repo`) resolve to the identical canonical root as the direct path; a symlinked repository root resolves, via `resolve_canonical_deployment_root`, to the same real underlying canonical path as the direct path, and a `create_deployment_binding` call made through the symlink converges on the exact same `repository_id`/`canonical_deployment_root` pair (idempotent-preserve, not a second entry) — confirmed exactly one registry entry afterward. Producer and the existing `resolve_canonical_deployment_root` consumer function necessarily agree, since the producer calls that exact function rather than reimplementing canonicalization.

## 12. Create Semantics and the Idempotency Temporal Attack (Item 17)

Live-verified valid creation produces exactly one registry entry, `status="active"`, `revoked_at=None`, a canonical `valid_from`, readable by both `HATPTrustStore.load_repository_enrollment` and `deployment_binding_matches`.

**Idempotency valid_from exclusion — independently adjudicated, not accepted from 7I's rationale.** Read `_binding_fields_equal_for_idempotency()` directly: it compares exactly `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` — `valid_from` is excluded. Live-attacked: called `create_deployment_binding` twice with byte-identical authority evidence, ~10ms apart (different wall-clock instants, hence different `_canonical_timestamp_now()` outputs). Result: second call returns `ALREADY_SATISFIED`, and — critically — the **persisted `valid_from` remains the first call's value**, not the second's (the code path for `already_satisfied` returns `existing`, never constructing or writing a new record). Exactly one registry entry after the repeat.

**Classification: CORRECT CONSERVATIVE IMPLEMENTATION**, independently reasoned as follows. `valid_from` is producer-generated freshness metadata, not caller-supplied authority content — HBDC-REQ-059's "identical field values" is naturally read as referring to the *authority-bearing* fields a caller/election actually asserts (root, principal, signer, provider, scope), not a timestamp the producer itself mints on every call. Including `valid_from` in the comparison would make `ALREADY_SATISFIED` unreachable by construction (two real invocations are never simultaneous to microsecond precision), silently collapsing HBDC-REQ-059's two-branch design (idempotent-preserve vs. conflict) into a single always-conflict branch — that would be the actual specification violation. This mirrors `ensure_repository_identity`'s own established precedent of excluding its analogous `created_at` field from its own idempotency check, an existing, already-accepted discipline in this codebase. Contract text does not explicitly enumerate the compared field set (7H's own named, carried-forward "idempotency field-set ambiguity" finding, non-blocking) — this remains a real, textually-unresolved ambiguity at the *contract* level, but the *implementation's* specific resolution of it is the conservative, correct one and does not itself constitute a defect.

## 13. Idempotent Persistence, Conflicting Create, Create-Over-Revoked

- **Exact semantic repeat:** `ALREADY_SATISFIED`, no duplicate entry, `valid_from` unchanged (§12), one audit no-op record emitted (`deployment_binding_create_noop`).
- **Conflicting create** (same `repository_id`, differing `authority_scope`): live-attacked — `DuplicateConflictingBindingError`, no overwrite, original entry unchanged on disk.
- **Create over revoked state:** live-attacked via the official test fixture pattern and independently reasoned from source — an existing `status="revoked"` entry causes `create_deployment_binding` to raise `DuplicateConflictingBindingError` unconditionally (checked before the field-equality comparison), never resurrecting or overwriting the revoked record. Only `rotate_deployment_binding` may return a `repository_id` to `active`.

## 14. Rotate Semantics

Live-verified: rotation requires an existing entry (`DeploymentBindingNotFoundError` if absent — never creates), writes exactly one replacement current-state record (full field overwrite: `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope`, fresh `valid_from`, `status` reset to `"active"`, `revoked_at` cleared), never produces two current records for the same `repository_id` (registry-document rebuild always replaces, never appends, the existing entry for that key — `_registry_document_with_binding`'s list-comprehension exclusion followed by single-item append). Rotation against an already-`revoked` entry raises `DeploymentBindingRevokedError` — revoked authority is never silently reactivated by rotate; only an explicit, distinct rotate call against a still-`active` entry succeeds. External audit history (provenance events) is preserved regardless, since the trust-store overwrite never touches the separate provenance log.

## 15. Revoke Semantics

Live-verified: active → revoked is a field mutation (`dataclasses.replace`), same `repository_id`/`canonical_deployment_root`/`principal_id`/etc. retained unchanged, `revoked_at` becomes canonical, no entry deletion (confirmed: registry entry count unchanged before/after revoke). Post-revoke, `HATPTrustStore.load_repository_enrollment` still returns the record (revoked, not absent), and `deployment_binding_matches()` independently correctly returns `False` against it (its own `status != "active"` check). Revoke against a nonexistent entry: `DeploymentBindingNotFoundError`, no tombstone created. Revoke against an already-revoked entry: deterministic `ALREADY_REVOKED`, and live-verified the **original** `revoked_at` is preserved byte-for-byte across a second revoke call (first-recorded-revocation-wins), with a `deployment_binding_revoke_noop` audit record still emitted for the no-op.

## 16. F4 Lost-History Reconstruction (Item 27)

Live-executed create(pA) → rotate(pB) → revoke sequence against a disposable repository. Confirmed the trust store afterward holds **only the final revoked state** — no trace of the intermediate `pA` principal or the original creation timestamp survives in `registry.json`. Independently read `read_provenance_history` afterward: three ordered events (`deployment_binding_created`, `deployment_binding_rotated`, `deployment_binding_revoked`), each with a distinct human-readable summary. The `created` event's summary contains `principal_id=pA`; the `rotated` event's summary contains both `previous_principal_id=pA` and `new_principal_id=pB` — an **explicit A→B linkage**, stronger than 7H's own carried finding anticipated ("the one fact not explicitly guaranteed is an explicit A→B linkage" — 7H §16). This phase's implementation resolves that specific residual gap as a matter of fact (not by contract obligation) via the rotate audit summary's own wording. Full reconstruction (A existed, who authorized it, when it was replaced, why, and by whom) is achievable purely from the provenance log, independent of trust-store state. F4 is **safely realized in the implementation**, exceeding the contract's own minimum guarantee.

## 17. Audit Ordering, Audit-Failure-Before/After-Mutation

Read the actual code path in `create_deployment_binding` (mirrored in rotate/revoke): validate authority/identity/root → acquire lock → read fresh registry state → decide outcome → (if mutating) atomic write → read-back verify → release lock → `_audit()` → return. Independently confirmed via source-position inspection that `_atomic_write_registry` always executes strictly before the `_audit()` call within each function body. There is no "audit-must-succeed-before-mutation" prerequisite anywhere in the design — mutation happens first, audit happens last, by explicit implementation choice (7H's own finding: HBDC-REQ-062 is silent on ordering; this is the implementation's disposition of that silence, not a violation of any explicit contract clause).

**Audit failure after durable mutation — live fault-injected.** Monkeypatched `_audit` to raise unconditionally, then called `create_deployment_binding`. Result: the `RuntimeError` propagates uncaught out of the public function (never swallowed); **the trust-store mutation is nonetheless durable and correct on disk** (`registry.json` shows the new active entry) — but **zero audit records exist** for that operation (`read_provenance_history` returns an empty event list). This is a real, load-bearing consequence exactly as the module's own docstring discloses: composing two independently atomic systems (trust-store file, provenance log) without a real two-phase commit means a caller who receives this exception must reconcile the missing audit record out of band — the caller cannot infer "nothing happened" from the exception, since something durable did happen. This is accurately described by the implementation (no false "rolled back" claim is made anywhere), and the exception type (bare `RuntimeError`/whatever the audit backend raises, not a `DeploymentBindingAdminError` subtype) does correctly signal "this is not one of the module's own typed fail-closed outcomes" to a careful caller — but the module provides no purpose-built exception subtype distinguishing "mutation succeeded, audit failed" from an audit failure that occurred with no prior mutation (revoke/create no-op paths audit only, no mutation). **Named as a real, non-blocking finding**: a future hardening pass could give this specific case (durable mutation + audit failure) its own distinguishable exception type so callers do not need to independently re-read the trust store to learn whether the mutation actually landed.

## 18. Atomic Write and Directory Durability

Read `_atomic_write_registry` directly: `tempfile.mkstemp` in the same directory as the target (`store_root`), write + `flush()` + `os.fsync(fd)`, a second `_reject_symlink` check on the target path immediately before `os.replace`, then atomic rename, with a `finally`-block cleanup of any leftover temp file. This is confirmed to be exactly `repository_identity.py::_write_atomic`'s idiom (byte-for-byte comparable control flow), with the one documented, deliberate deviation that it never `mkdir`s the store root (existence is a strict precondition, `DeploymentBindingTrustStoreUnavailableError` otherwise) — independently confirmed correct against HBDC-REQ-063's "no new idiom" requirement and the module's own stated Protected-Root-never-auto-provisioned discipline.

**Directory durability:** independently confirmed by source inspection — **neither this module's `_atomic_write_registry` nor the reused `repository_identity.py::_write_atomic` fsyncs the containing directory after `os.replace`.** This is a real limitation under HBDC-REQ-063's "atomic-write discipline," but it is an **exactly-inherited** characteristic of the primitive HBDC-REQ-063 itself mandates reusing verbatim ("no new idiom SHALL be invented") — not a defect newly introduced by this implementation. Recorded precisely: on most POSIX filesystems a crash between `os.replace` and the next directory fsync (by any process) can, in principle, leave the rename un-durable despite the file's own `fsync`; this exposure is identical in kind and degree to every other consumer of `_write_atomic` already in this codebase, and is not amplified by this module.

## 19. Fault-Injection Matrix

Live fault-injected against disposable stores:

| Fault | Result |
|---|---|
| `os.fsync` raises | `OSError` propagates; no `registry.json` written; no leftover temp file (finally-block cleanup confirmed) |
| `os.replace` raises | `OSError` propagates; no `registry.json` written; no leftover temp file |
| Read-back mismatch (`_read_back_and_verify`) | `DeploymentBindingReadbackMismatchError` (existing test suite's `test_readback_mismatch_function_detects_real_corruption`, independently re-run, confirms real corruption is actually detected, not merely a mocked assertion) |
| Registry-path symlink swap between an initial create and a subsequent rotate | `HATPTrustStoreSymlinkError`; symlink target file never written to |
| Lock-file path symlinked | `HATPTrustStoreSymlinkError` (existing suite, independently re-run) |

No ambiguous-success case found: every injected fault either leaves the trust store in its pre-operation state (with a clean, uncorrupted `registry.json` or none at all) or is caught by read-back verification.

## 20. Symlink, ACL, Ancestor-Writability Attacks

Registry-path symlink-swap race (§19) fails closed. `_require_trust_store_available` independently confirmed, by source inspection, to check only `store_root.is_symlink()` and existence/directory-ness of `store_root` itself — it does **not** walk the ancestor chain for group-writable, ACL-only-writable, or untrusted-owner topology, unlike the deeper Class-B verifier machinery elsewhere in this repository (`hatp_class_b_topology_verifier.py`) which HBDC-REQ-063 does not require this module to duplicate. This is consistent with the module's own stated security boundary (§8): real OS filesystem write permission on the Protected Root is the actual control; this module was never designed to independently re-verify ancestor-directory trust topology beyond the direct symlink checks HBDC-REQ-063 names. Not a new finding — this is the same scope HBDC-REQ-063 itself defines (`repository_identity.py::_write_atomic`'s idiom, immediate target + immediate parent only), and the same scope the sibling Class-B verifier machinery already exists separately to cover for the different, broader HDA-REQ concerns that machinery serves.

## 21. Lock Implementation and Lock-File Trust Attack

Read `_deployment_binding_transition_lock` directly: `os.open(lock_path, O_CREAT | O_RDWR, 0o600)` under `store_root`, `fcntl.flock(LOCK_EX)`, released in a `finally` block (`LOCK_UN` + `close`) regardless of exception. `_reject_symlink(lock_path)` runs before the lock file is opened — a symlinked lock path fails closed (existing suite, independently re-run, confirms this). The lock file itself lives under the same Protected Root the trust store lives under — an attacker who can write there already has the maximal privilege level this architecture defines (§8); the lock provides no additional trust boundary and does not claim to — it is explicitly documented, and independently confirmed, as non-normative implementation hardening for a concurrency scenario HBDC-001 itself does not require a lock for (7H's own carried finding).

## 22. Multi-Process Concurrency, TOCTOU, Crash-With-Held-Lock

Live-tested with **real separate OS processes** (`multiprocessing.Process`, not threads): six concurrent processes issuing byte-identical `create_deployment_binding` calls against one disposable trust store converged on **exactly one** registry entry. Read `create_deployment_binding`'s structure to confirm TOCTOU discipline: the registry document is loaded fresh from disk (`_load_raw_registry_document`) **inside** the `_deployment_binding_transition_lock` critical section, immediately before the existence/conflict decision — no pre-lock read is ever used to decide an outcome. **Crash-with-held-lock:** live-tested — spawned a separate process that acquired the transition lock and then `SIGKILL`ed itself while holding it; a subsequent writer in the parent process proceeded within ~10ms (no hang), confirming the OS releases `flock` state automatically on process death and the design carries no stale-lock-file failure mode.

## 23. Timestamp Generation and Caller Injection

Live-verified `_canonical_timestamp_now()`'s output against `HBDC-REQ-067`'s exact grammar (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) across repeated calls; the function additionally self-asserts its own output against the same pattern (defense in depth against a future accidental format change). Searched every public function signature: no parameter anywhere accepts a caller-supplied `valid_from` or `revoked_at` — both are always producer-generated via `_canonical_timestamp_now()`, never caller input, so there is no timestamp-injection attack surface to exploit in the current API shape (this is a stronger posture than HBDC-REQ-067 strictly requires, which only constrains the format of whatever the writer *does* emit).

## 24. Permissive Consumer / Strict Producer Asymmetry (Items 43-44)

Independently re-read `hatp_bootstrap.py::_parse_iso_timestamp`: it accepts any `datetime.fromisoformat`-parseable string after a trailing-`Z`→`+00:00` substitution — strictly broader than the producer's own `_TIMESTAMP_PATTERN`. Confirmed unchanged since 7H (byte-identical file, §3) — this phase repairs nothing here, as directed. Live-attacked: hand-placed a noncanonical `valid_from` (`"2026-01-01T00:00:00+00:00"`, no fractional-second component, non-`Z`-suffixed) directly into a disposable `registry.json`, bypassing the producer entirely. `HATPTrustStore.load_repository_enrollment` accepted it without error. The producer's own `_TIMESTAMP_PATTERN` independently confirmed to reject that exact string. **Finding carried forward unchanged**: the producer correctly constrains its own output (HBDC-REQ-067 satisfied); the consumer's read-path trust boundary remains permissive to hand-placed data — but exploiting this requires the same maximal write access the legitimate admin writer itself requires (7H's own risk analysis, independently re-affirmed: not a privilege-escalation path, a hygiene gap).

## 25. Signer/Provider/Principal/Scope Semantics

Live-verified: `principal_id` is preserved unchanged end-to-end from `AuthorityEvidence` through to the persisted, then re-loaded, `DeploymentBinding` — no case-folding, no UID/username conversion. `authority_scope` passed through unchanged with no wildcard or default-privilege broadening (a non-default value, `"rollback"`, round-trips exactly). No normalization of `provider_profile`/`signer_key_id` was found anywhere in the module (confirmed by source read: values flow from `AuthorityEvidence` straight into the `DeploymentBinding` constructor with no transformation function applied). Malformed-shape rejection (empty string) is enforced by `_validate_authority_evidence`; no cross-validation against `hatp_providers.py`'s controlled `provider_profile` vocabulary is performed — carried forward unchanged from 7H's own named, deferred finding (contract silence on this specific cross-validation, HBDC-REQ-058).

## 26. Schema Preservation and Registry Serialization

Independently re-read the `DeploymentBinding` dataclass in `hatp_bootstrap.py`: exactly the same nine fields present before 7G (`repository_id`, `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope`, `valid_from`, `status`, `revoked_at`) — confirmed both by direct reading and by the byte-hash identity proof in §3 (the file defining this dataclass never changed). `_deployment_binding_to_document` independently confirmed to serialize exactly these nine keys, no more, no fewer, no hidden `binding_id`/digest/host-identity field. `registry.json` is written with `json.dumps(..., indent=2, sort_keys=True)` — deterministic key ordering for stable diffs/equality checks; `deployment_bindings` list entries are additionally sorted by `repository_id`, so document-level ordering is fully deterministic across writes. `_parse_registry_document` (the shared parser both producer and consumer use) is confirmed, by reading its call sites, to reject unknown top-level shapes rather than silently ignore extra fields (pre-existing, unchanged parser behavior).

## 27. Round-Trip Verification (Create/Rotate/Revoke) and REQ-042 Integration

Live-executed the full producer → persistent registry → `HATPTrustStore` load → `DeploymentBinding` decode → `deployment_binding_matches` chain against a disposable repository with a real `RepositoryIdentity`:

- **Create round trip:** producer-created binding satisfies `deployment_binding_matches` for the correct `(repository_id, canonical_deployment_root)` pair; a copied `repository_id` presented against the wrong root does **not** match (theft defense, HATP-REQ-057-063); the right root with a wrong `repository_id` does **not** match.
- **Rotate round trip:** consumer sees only the current (post-rotate) state; the prior principal is not separately matchable through the live consumer path (only through the provenance log, §16).
- **Revoke round trip:** post-revoke, `deployment_binding_matches` independently confirmed to return `False` — the binding no longer satisfies the active-match predicate the HBDC-REQ-042 path relies on.

This constitutes the disposable REQ-042 integration this phase's governing scope calls for; no Dell state was touched at any point.

## 28. Multi-Repository and Same-Repository/Multi-Root Semantics

Live-verified two independent disposable repositories (A, B) receive distinct `repository_id`s and independent trust-store entries; revoking A's binding leaves B's untouched (`active`). **Same-repository-identity-at-a-second-root** (simulating host migration without issuing a new `RepositoryIdentity`, by copying A's `.pcae/` tree to a second path): the schema and registry, independently confirmed, permit this — `rotate_deployment_binding` at the second root succeeds and overwrites `canonical_deployment_root` in place (single global entry keyed only by `repository_id`, no host/root component in the key). This operationally confirms 7H's own named finding ("7H's schema has no host identity") in a live setting: the registry's uniqueness key is `repository_id` alone, so a copied identity at a different root is treated as the same logical subject upon rotate, and as `ALREADY_SATISFIED`/conflict upon create depending on field equality (§10). This matches the verified contract's own disposition (HBDC-REQ-057/059 define uniqueness by `repository_id`, not by the `(repository_id, root)` pair) — **not Blocking**, since it is the contract's own chosen design, independently re-confirmed rather than newly discovered.

## 29. Admin Script Analysis

Read `scripts/hatp_deployment_binding_admin.py` in full: it delegates every mutation to the three imported producer functions — no duplicated mutation logic exists in the script itself. Preview mode (`--preview`) independently confirmed, both by source reading and live invocation, to compute and print the target only, calling only the `preview_*` functions, never acquiring the transition lock, never touching disk. Mutation mode requires an explicit subcommand (`create`/`rotate`/`revoke`) and an interactive `yes` confirmation (or `--assume-yes`); there is no default/ambiguous invocation that mutates when arguments are omitted (`argparse` `required=True` on every authority field; `dest="ceremony", required=True` on the subparser). Live-invoked the real script's `create --preview` against this repository with no monkeypatching: it correctly resolved and reported the real, absent production Protected Root and exited non-zero having written nothing.

## 30. Arbitrary-Root / Test-Seam Analysis

Independently confirmed, by both static reading of `_build_parser()` and a live `--help` invocation of every subcommand, that the CLI exposes no `--protected-root`/`--store-root` flag or any other caller-reachable override of `HATPTrustStore.production().root`. The `_protected_root` keyword parameter exists solely on the three Python-level producer functions and the CLI script never passes anything but the default (`None`) for it — confirmed by reading every call site in `scripts/hatp_deployment_binding_admin.py`. No production option lets a normal caller reinterpret an arbitrary directory as Protected-Root authority.

## 31. HMIC Frozen-Source-Membership Analysis (Items 65-67) — Named Finding

Independently read `hatp_mandatory_certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES` (22 entries) and `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` (6 entries, including `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` **and** `scripts/hatp_certification_admin.py` — the directly analogous, precedent-setting admin script for the sibling HMIC certification writer) — 28 entries total, `assert`-pinned at exactly 28.

**Neither `src/pcae/core/hatp_deployment_binding_admin.py` nor `scripts/hatp_deployment_binding_admin.py` appears in this frozen set.** This is a real, notable asymmetry: the direct precedent this new admin script mirrors (`scripts/hatp_certification_admin.py`) **is** bound into HMIC's `implementation_scope_digest`; the new `DeploymentBinding` admin script and its privileged core producer module — a newly created privileged trust-store writer — are **not**. HBDC-001's contract *text* (which normatively describes producer behavior) is already frozen since 149O.20D.1/149O.20F (HBDC-REQ-070); the producer's actual *code* is not.

**Classification (per this phase's own required disposition menu): HMIC source-scope gap**, not intentional and not irrelevant. Precedent (`hatp_certification_admin.py` being frozen) shows this codebase's own established discipline is that a privileged admin-tool script performing authority-bearing trust-store writes belongs in the frozen set; this repository's own history (149O.20D → 149O.20E → 149O.20F → 149O.20G, and again 149O.20K → 149O.20K.1 → 149O.20K.2 → 149O.20K.3) shows the established pattern for closing exactly this kind of gap is a dedicated, separately-governed HMIC-001 contract-amendment phase (bumping the frozen-file count, e.g. 28 → 30) followed by its own independent verification — not a decision this verification-only phase can or should make unilaterally.

**Disposition:** this is a **non-blocking finding for HBDC-REQ-056..070 implementation-correctness specifically** (nothing in HBDC-001 §16.1 requires HMIC frozen-set membership; no real certification exists yet to be affected; the gap concerns a *different* contract, HMIC-001, not this one) — but it **must** be closed, via a dedicated future phase, before any real HMIC certification is claimed to meaningfully cover this producer's code. Recommend a future phase (naming deferred to primary status at the time, mirroring 149O.20D/149O.20K's own naming pattern) to formally add both files to `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` before any certification following this producer's introduction is relied upon.

## 32. Admin-Script Identity Scope

The privileged script is not itself identity-bound anywhere in the codebase (no signature, no digest pin analogous to `implementation_scope_digest`, independent of the §31 HMIC gap). Its ability to safely invoke the producer depends entirely on (a) the real OS filesystem permission on the Protected Root (§8's confirmed actual security boundary) and (b) — until §31's gap is closed — informal trust in the installed source tree, since HMIC certification does not yet cover it. This is consistent with, and does not add risk beyond, §31's own finding; recorded here as its own explicit item per the governing scope's checklist, not a new independent defect.

## 33. Dell Staleness Consequence

Independently confirmed via `git log`/`git diff` that Dell's currently deployed source (per 149O.20L.7D.11's last redeployment) predates both HBDC-001 v1.1 and this producer's existence. Dell consumes neither the amended contract text nor any producer code. No redeployment occurred this phase. No claim is made about Dell's live behavior beyond what was already independently verified as of its last redeployment.

## 34. Boundary-P Consequence

149O.20L.7E's Boundary-P (physical host provisioning) verdict concerns OS accounts, filesystem permissions, and deployed-source byte-identity to a specific, older SHA — entirely independent of HBDC-001's version number or this producer's existence. Physical provisioning state remains independently verified and unaffected; it says nothing about conformance to the new producer contract, which Dell does not yet run.

## 35. Regression Baseline and Net-New Failure Classification

Independently reconstructed a comparable pre-7I baseline using an immutable `git worktree` at `e9cad634` (§3) — not merely re-quoting 7I's own reported counts. Ran the project's actual phase-completion gate (`pytest -m fast_green --continue-on-collection-errors`, serial, no `-n auto`) on both sides this phase, in full:

- **Pre-7I baseline (`e9cad634`):** 208 failed, 7457 passed, 5 skipped, 10 errors (26298 deselected).
- **HEAD (`8ef3d2b3`):** 216 failed, 7545 passed, 5 skipped, 10 errors (26298 deselected).

(One collection error, `tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py` — missing optional `fido2` dependency — is a pre-existing local-environment gap present identically on both sides, `--continue-on-collection-errors` used to route around it on both runs; not attributable to this phase.)

Diffed the full sorted `FAILED`/`ERROR` node-ID sets (`comm -23`/`comm -13`) rather than trusting the aggregate counts alone: **exactly 8 net-new failures, 0 resolved failures.** (216 − 208 = 8, independently reconciled against the full-list diff, not just the arithmetic.) Individually inspected every one of the 8:

| Test | Assertion that failed | Classification |
|---|---|---|
| `test_phase_149o_19_5e_3_...::test_no_scripts_file_changed_since_phase_entry` | Historical self-pin: "no file under `scripts/` changed since this earlier phase's entry" | Historical phase-pin, expected |
| `test_phase_149o_19_5f_...::TestProductionDiffClassification::test_no_scripts_file_changed` | Same pattern | Historical phase-pin, expected |
| `test_phase_149o_19_5g_...::TestAdminAgentReachability::test_no_production_src_pcae_file_calls_the_writer_primitives` | Whole-tree literal-substring scan for HMIC writer-primitive names (e.g. `_write_revocation`); tripped by this module's own **docstring prose** describing that it mirrors `hatp_mandatory_certification.py::_write_revocation`'s discipline — a textual mention, not an actual call. Independently confirmed by reading the module: `revoke_deployment_binding` never calls `_write_revocation` or any HMIC writer primitive; it uses its own local `dataclasses.replace` | Lexical false positive from descriptive prose, not a real reachability violation — independently confirmed non-blocking |
| `test_phase_149o_20f_...::test_no_scripts_file_changed_since_phase_entry` | Historical self-pin | Historical phase-pin, expected |
| `test_phase_149o_20k_2_...::test_no_scripts_file_changed_since_phase_entry` | Historical self-pin | Historical phase-pin, expected |
| `test_phase_149o_20l_7g_...::TestNoImplementationNoMutation::test_no_deployment_binding_admin_script_created` | 7G's own "no admin script exists yet" self-pin — the exact phase-precursor assertion this implementation is expected to invalidate | Historical phase-pin, expected (named as the direct predecessor of this producer) |
| `test_phase_149o_20l_7h_...::TestImplementationPlanMapping::test_no_admin_tool_script_created_yet` | Same pattern, 7H's own self-pin | Historical phase-pin, expected |
| `test_phase_149o_20l_7h_...::TestNoImplementationNoBindingNoMutation::test_no_write_function_added_anywhere_in_src_pcae` | 7H's own "no `def create_deployment_binding`/etc. exists anywhere in `src/pcae`" self-pin | Historical phase-pin, expected (named as the direct predecessor of this producer) |

**All 8 are historical, self-referential "as of phase X, this thing does not exist yet" pin assertions from seven distinct earlier phases**, each invalidated by the mere fact that this producer (correctly) now exists — none represent a genuine new authority/security-gate failure; none were dismissed without individually reading the actual assertion and, for the one lexical case, independently confirming by source inspection that the underlying security property it is trying to protect (no cross-module writer-primitive invocation) still holds. **Zero resolved failures** — this phase's serial (non-`-n auto`) run does not exercise the subprocess-CLI parallel-flakiness class 7I separately reported resolving under `-n auto`; not attempted or claimed here.

**Verdict: REGRESSION CLEAN WITH EXPECTED HISTORICAL PIN MIGRATION** — independently established via full-list diff and per-failure inspection, not asserted from a red aggregate count alone.

## 36. Historical Security Regression Re-Check

Independently re-ran the existing symlink/ACL/ancestor-writability/timestamp-canonicalization/authority-source-identity test modules this producer's code path touches or is adjacent to (`tests/test_hatp_bootstrap_foundation.py` — 26 passed; `tests/test_hatp_deployment_binding_admin.py` — 55 passed; `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py` — 41 passed). No prior Class-B security finding was reopened by this producer's presence; §35's full-suite diff independently confirms no unrelated security-gate test moved from pass to fail.

## 37. 7H Findings Disposition — Independently Re-Adjudicated

| 7H Finding | Disposition at implementation layer, independently re-checked this phase |
|---|---|
| Idempotency field-set ambiguity (REQ-059) | Conservatively addressed in implementation: `valid_from` excluded, live-verified correct (§12). Contract text itself remains silent — still a real, non-blocking *contract-level* ambiguity, unresolved by code choice per this phase's own instruction not to treat implementation choice as contract closure |
| Vocabulary cross-validation gap (REQ-058) | Still deferred, unchanged — no cross-validation against `hatp_providers.py` performed (§25) |
| Rotate/revoke-on-nonexistent-entry (REQ-060/061) | Conservatively addressed: both fail closed, live-verified (§14, §15) |
| Audit-write-ordering silence (REQ-062) | Implementation's explicit choice (mutate-then-audit) independently confirmed and analyzed for its failure-mode consequence (§17); contract remains silent, non-blocking |
| REQ-057 fail-closed-on-absent-identity living in architecture prose, not RFC-2119 text | Unchanged — still a documentation-placement gap in the contract itself, not addressed (and not addressable) by this implementation phase |
| Preview "SHOULD" not "SHALL" | Implemented anyway (§29), exceeding the non-mandatory prose; contract text itself unchanged |
| No concurrency-lock requirement (vs. HMIC-REQ-097) | Addressed as non-normative implementation hardening (`fcntl.flock`), live-verified under real multi-process concurrency (§22); contract text itself still names no such requirement |
| F3-residual (HMIC-REQ-103 doesn't live-check binding status) | Out of this producer's scope, unchanged, correctly not addressed here (belongs to a future HMIC-001 amendment) |
| Permissive read-path timestamp parser | Unchanged, independently re-confirmed live (§24); correctly not repaired this phase |

No 7H finding was closed merely because the implementation happened to choose one interpretation — each is individually re-evaluated above against what the *contract text* itself still does or does not require.

## 38. Final Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR FIRST-USE PREPARATION.**

Every one of HBDC-REQ-056..070 independently traced, reconstructed, and adversarially exercised against live disposable trust stores and repositories, with zero Blocking defects found. The implementation is conservative everywhere its own choices go beyond contract text (valid_from-exclusion, revoke/rotate-on-missing/revoked fail-closed behavior, F4 audit linkage, real multi-process concurrency safety) and introduces no new security-boundary weakness beyond what HBDC-REQ-063's mandated idiom reuse and the module's own disclosed OS-permission-is-the-real-boundary design already accept. Findings carried and newly named this phase (§31's HMIC frozen-source-scope gap being the most consequential; §17's audit-failure-after-mutation exception-type gap; the unchanged 7H findings in §37) are all explicitly bounded, non-blocking to HBDC-REQ-056..070 compliance specifically, and require future, separately-governed phases to close — §31 in particular should be closed before any real HMIC certification is claimed to cover this producer.

## 39. Proof of No Operational Progression

- **No code repair occurred:** `git status --short` clean throughout; `src/pcae/core/hatp_deployment_binding_admin.py` and `scripts/hatp_deployment_binding_admin.py` untouched this phase (only this doc and the companion test module were added).
- **No real `DeploymentBinding` exists:** every producer call this phase targeted a disposable `tempfile.TemporaryDirectory()`-based trust store; `HATPTrustStore.production().root` was touched exactly once, read-only, by the live CLI `--preview` invocation (§8), which found it absent and wrote nothing.
- **No Dell mutation, no Dell access:** zero SSH/network calls made this phase; all verification is local-disposable.
- **No election initiated, no CHGR published, no Boundary C, no HMIC certification, no HATP activation:** none of this phase's commands touch `decision-session`, `governance-record publish`, or any certification/activation command surface.

## 40. Runtime State

`pcae runtime inspect` (re-run this phase): `Runtime status: not_implemented`, `Runtime state: Observed`, `Execution capability: unavailable`, `Registry status: empty`, `Plugin count: 0` — unchanged from entry.

## 41. Tests

Companion module `tests/test_phase_149o_20l_7j_deploymentbinding_producer_implementation_independent_verification.py` encodes this phase's independent findings as permanent regression-guard assertions (contract byte-identity, `hatp_bootstrap.py`/`repository_identity.py` byte-identity, zero-write-method `HATPTrustStore`, full-tree agent-unreachability, HMIC frozen-set non-membership finding, idempotency valid_from-exclusion behavior, F4 audit-linkage content, audit-failure-after-mutation durability, multi-process concurrency convergence, canonical-root symlink convergence). Existing suites independently re-run and green: `tests/test_hatp_deployment_binding_admin.py` (55 passed), `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py` (41 passed), `tests/test_hatp_bootstrap_foundation.py` (26 passed).

## 42. Governance Results

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`: coherent. `pcae doctor task-memory`: pre-existing warnings only (25 active-task-file/DONE.md-sync warnings spanning phases back to 149O.1H.3, unrelated to this phase, not newly introduced). `pcae push check` at phase entry: clean, nothing to push.

## 43. Commits, Pushed Status, origin/main..HEAD

See finalization commits below this report's own staging; `git rev-list --count origin/main..HEAD` = 0 at phase entry (§2).

## 44. Recommended Next Phase

**149O.20L.7K — HMIC Frozen-Source-Scope Amendment for the DeploymentBinding Producer** (exact canonical title to be derived from primary status at the time, mirroring 149O.20D/149O.20K's own precedent naming): close §31's named gap by formally adding `src/pcae/core/hatp_deployment_binding_admin.py` and `scripts/hatp_deployment_binding_admin.py` to HMIC-001's frozen authority-bearing file set (28 → 30 entries), with its own independent verification to follow. This should be sequenced **before**, not combined with, any future phase addressing the changed Mac-vs-Dell deployment state or a real first-use proposition — a privileged producer's code should be inside its certification's own digest scope before that certification is ever relied upon to say anything about it. A later, separate phase must still decide how to sequence: redeploying HBDC-001 v1.1 + the verified producer source to Dell; Dell repository-identity creation; a real `DeploymentBinding` first-use proposition; the fresh election CHGR condition 6 requires; independent authority verification; producer invocation; HBDC re-adjudication — none of that is this phase's or 7K's scope.
