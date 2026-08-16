# Phase 149O.20L.7I — DeploymentBinding Producer Implementation

## 0. Status

**Governed production implementation — capability only.** Implements
`create_deployment_binding()`, `rotate_deployment_binding()`, and
`revoke_deployment_binding()` per HBDC-001 v1.1 §16.1 (HBDC-REQ-056..070).
No real `DeploymentBinding` created. No real `RepositoryIdentity` created
on Dell. No Dell SSH session opened. No Dell mutation of any kind. No
first-use human election initiated. No Boundary C or Boundary A action.
No HMIC certification computed, requested, or granted. `HATPTrustStore`
still exposes zero write methods — every mutation added by this phase
lives in a new, separate, non-agent-writable sibling module.

**Phase-entry commit:** `e9cad634` (`Phase 149O.20L.7H: sync push-state
trust fields for finalization gate`), `origin/main` == `HEAD`, 0 commits
ahead, working tree clean at entry (verified: `git status --short`,
`git log --oneline origin/main..HEAD`, `git rev-list --count
origin/main..HEAD` all empty/zero).

**Reconciliation:** `pcae phase-report reconcile --phase-id
149O.20L.7H` → `reconciled`, 2 generations promoted, marker
`already_dispatched`, mutation `none` (inspection only).

## 1. HBDC-REQ-056..070 Implementation Matrix

Reconstructed directly from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
§16.1 (not from 7G's/7H's own prose summaries) before any implementation
began.

| Requirement | Normative text (summary) | Production responsibility | Implementation |
|---|---|---|---|
| HBDC-REQ-056 | Writer SHALL be a separate, non-agent-writable admin tool, never a `pcae` CLI subcommand | Caller boundary | `scripts/hatp_deployment_binding_admin.py` — standalone script outside `src/pcae/`, never imported by `cli.py`/`commands/agent.py`/`core/agent.py` (verified by static scan, `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py::TestNotAgentReachable`) |
| HBDC-REQ-057 | `repository_id`/`canonical_deployment_root` derived read-only, never free-form caller input | Input resolution | `_resolve_repository_id()` (reads existing `RepositoryIdentity` only), `_resolve_canonical_root()` (calls unmodified `hatp_bootstrap.resolve_canonical_deployment_root`) — neither function is caller-suppliable; public functions accept only `repository_root` (a locator) |
| HBDC-REQ-058 | `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` drawn from admin enrollment context | Authority input | `AuthorityEvidence` dataclass, validated for shape only (`_validate_authority_evidence`), never cross-validated against a vocabulary registry (149O.20L.7H's deferred-vocabulary finding, disposed of conservatively — see §8) |
| HBDC-REQ-059 | Create fails closed on conflicting existing entry; idempotent no-op on identical | Uniqueness/idempotency | `create_deployment_binding()`: `_binding_fields_equal_for_idempotency()` compares canonical_deployment_root/principal_id/signer_key_id/provider_profile/authority_scope (excludes `valid_from` — see §9 for rationale); exact match → `ALREADY_SATISFIED`; mismatch → `DuplicateConflictingBindingError` |
| HBDC-REQ-060 | Rotate/revoke are distinct explicit operations, never implicit via re-running create | API shape | Three distinct public functions, never collapsed; `create_deployment_binding()` never transitions an existing entry's status |
| HBDC-REQ-061 | Revoke = field mutation (`status`→`revoked`, `revoked_at` set), never deletion; rotate = in-place overwrite of mutable fields | Lifecycle mutation | `revoke_deployment_binding()` uses `dataclasses.replace(existing, status="revoked", revoked_at=...)`; `rotate_deployment_binding()` constructs a full replacement `DeploymentBinding` and writes it back under the same `repository_id` key — exactly one entry, never two |
| HBDC-REQ-062 | Every operation SHALL produce an audit record in existing governance/provenance infrastructure; no bespoke mechanism | Audit evidence | `_audit()` calls `pcae.core.provenance.append_provenance_event()` (this repository's one existing, generically-named provenance mechanism) against the target repository's own tree — see §10 for the alternative considered and rejected |
| HBDC-REQ-063 | Writer SHALL reuse `repository_identity.py::_write_atomic`'s exact idiom (mkstemp/fsync/os.replace, symlink rejection before and after) | Atomicity | `_atomic_write_registry()` — same idiom, one documented deviation (never `mkdir`s the Protected Root itself — see §11) |
| HBDC-REQ-064 | Writer SHALL require explicit fresh-election evidence, never a bare boolean | Authority gate | `AuthorityEvidence.election_reference` / `revoke_deployment_binding(election_reference=...)`, required non-empty string, validated by `_require_nonempty_str(..., error_type=AuthorityEvidenceMissingError)` |
| HBDC-REQ-065 | Election-evidence reference recorded as audit metadata, not cryptographically verified | Evidentiary recording | `election_reference` embedded verbatim in the `_audit()` summary string; never parsed, verified, or dereferenced |
| HBDC-REQ-066 | Writer invocable only by admin OS principal, never agent-reachable | Real security boundary | OS filesystem write permission on `HATPTrustStore.production().root` (unchanged, HBDC-REQ-009/012); `_require_trust_store_available()` fails closed if the root is absent/non-dir/symlink — a structural precondition check, not an authority substitute |
| HBDC-REQ-067 | Writer output SHALL use the strict `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$` grammar | Timestamp generation | `_TIMESTAMP_PATTERN` (identical regex, duplicated from `hatp_mandatory_cutover.py`/`hatp_mandatory_certification.py`) + `_canonical_timestamp_now()`, which self-asserts its own output against the pattern before returning |
| HBDC-REQ-068 | Repository-identity creation not gated by this section's election requirement | Prerequisite separation | `create_deployment_binding()`/`rotate_deployment_binding()`/`revoke_deployment_binding()` all call `_resolve_repository_id()`, which calls `read_repository_identity()` only — never `ensure_repository_identity()` (verified: zero `ast.Call` nodes to `ensure_repository_identity` in the producer module) |
| HBDC-REQ-069 | This amendment does not itself satisfy CHGR condition 6's election requirement | No self-authorization | Producer never launches a decision session, never infers approval, never accepts `approved=True`, never mints a CHGR (module docstring states this explicitly; verified by AST scan for literal `approved=True` assignments/keywords — none exist) |
| HBDC-REQ-070 | Amendment bytes automatically participate in `implementation_scope_digest` | Digest binding | Structural fact, unchanged by this phase: HBDC-001 remains one of HMIC-001's `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`; no producer code is needed to "pick up" this requirement (verified: `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` still named in `hatp_mandatory_certification.py`) |

## 2. Existing Architecture Reconstruction

Read directly from primary source this phase (not accepted from 7G's/7H's
own citations):

- `src/pcae/core/hatp_bootstrap.py:127-137` (`DeploymentBinding` dataclass,
  9 fields, unchanged) and `:351-395` (`_parse_deployment_binding`, closed
  field set, unchanged).
- `src/pcae/core/hatp_bootstrap.py:513-607` (`HATPTrustStore`): confirmed
  zero write methods before this phase and — critically — **still zero
  write methods after this phase**, since every new writer lives in a new
  sibling module, `hatp_deployment_binding_admin.py`, not inside
  `HATPTrustStore` or `hatp_bootstrap.py` itself.
- `src/pcae/core/hatp_bootstrap.py:435-440`: registry parser schema-enforces
  at most one `deployment_bindings` entry per `repository_id`, regardless
  of status — confirmed unchanged; this is the uniqueness key the producer
  honors.
- `src/pcae/core/repository_identity.py:153-174` (`_write_atomic`):
  the exact atomic-write idiom HBDC-REQ-063 requires the producer to
  reuse — mkstemp in the same directory, fsync, symlink rejection before
  and after, `os.replace`.
- `src/pcae/core/hatp_mandatory_certification.py` Wave C
  (`_atomic_write_protected_json`, `_certification_transition_lock`,
  `_append_certification_record`, `_write_active_binding`,
  `_write_revocation`) and `scripts/hatp_certification_admin.py`: the
  closest existing precedent for an admin-only, non-agent-writable
  writer surface over a Protected Root — this phase's own module and
  script mirror that shape (typed ceremony results, `_protected_root`
  test-only seam, `--assume-yes`/interactive-confirm CLI pattern,
  `ConfirmationDeclinedError`) without importing anything from
  `hatp_mandatory_certification.py` itself (HBDC and HMIC remain
  independent modules, per `hatp_bootstrap.py`'s own stated boundary).
- `src/pcae/core/provenance.py` (`append_provenance_event`,
  `build_provenance_event`): this repository's one existing, generic,
  generically-named ("provenance") append-only audit-history mechanism,
  used as HBDC-REQ-062's audit-record target — see §10 for the reasoning
  and the alternative (CHGR/publication-execution ceremony machinery)
  considered and rejected as the wrong shape for a per-operation audit
  trail.

## 3. Production Files Changed

```
src/pcae/core/hatp_deployment_binding_admin.py     (new — producer module)
scripts/hatp_deployment_binding_admin.py            (new — admin-tool CLI entrypoint)
tests/test_hatp_deployment_binding_admin.py         (new — 55 unit/adversarial/round-trip tests)
tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py  (new — 41 independent phase-evidence tests)
docs/PHASE_149O_20L_7I_DEPLOYMENTBINDING_PRODUCER_IMPLEMENTATION.md (new — this document)
PROJECT_STATUS.md, CHANGELOG.md, tasks/**, .pcae/phase-completion-*.json/.md (governance bookkeeping)
```

**Zero existing `src/pcae/**` files are modified.** `hatp_bootstrap.py`
and `repository_identity.py` are byte-unchanged (verified:
`tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py::TestNoSchemaDrift`).
No contract file (`docs/contracts/**`) is modified — HBDC-001 remains
exactly v1.1, byte-unchanged since 7H.

## 4. Producer Public API

```python
def create_deployment_binding(*, repository_root: Path, authority: AuthorityEvidence,
                               _protected_root: Optional[Path] = None) -> DeploymentBindingOperationResult

def rotate_deployment_binding(*, repository_root: Path, authority: AuthorityEvidence,
                               _protected_root: Optional[Path] = None) -> DeploymentBindingOperationResult

def revoke_deployment_binding(*, repository_root: Path, election_reference: str,
                               _protected_root: Optional[Path] = None) -> DeploymentBindingOperationResult
```

Three distinct semantic operations, never collapsed into a generic
`write_binding()`. `_protected_root` is a private, underscore-prefixed,
non-CLI test-only seam (mirrors `HATPTrustStore.__init__`'s own
`_test_only_root` and `scripts/hatp_certification_admin.py`'s own
`_protected_root` pattern) — never populated by the admin script's
`main()`.

Read-only preview helpers (`preview_create_deployment_binding`,
`preview_rotate_deployment_binding`, `preview_revoke_deployment_binding`)
are also implemented — HBDC-REQ item-47 names preview as `SHOULD`, not a
numbered `SHALL`; implemented because it fits cleanly and never writes
(verified by dedicated tests confirming no registry mutation across every
preview kind).

## 5. Caller/Persistence Layering

```
scripts/hatp_deployment_binding_admin.py   (trusted caller/coordinator; interactive confirmation)
        ↓
pcae.core.hatp_deployment_binding_admin    (DeploymentBinding producer; validation, lifecycle rules)
        ↓
hatp_bootstrap._parse_registry_document / _atomic_write_registry (validated trust-store persistence)
```

The CLI script never serializes or writes a raw trust-store record
itself — it only calls the three public producer functions. Every
registry read inside the producer module round-trips through
`hatp_bootstrap._parse_registry_document`, the exact same parser
`HATPTrustStore`'s own read path already uses — guaranteeing no
producer-only representation can exist.

## 6. Authority-Input Handling

The producer receives an already-resolved `AuthorityEvidence` — it never
infers, verifies, or derives `principal_id`/`signer_key_id`/
`provider_profile`/`authority_scope`/`election_reference` itself. It:

- Validates shape only (non-empty string) — never cross-validates against
  a signer/provider-profile vocabulary registry (149O.20L.7H's own named,
  deferred finding on HBDC-REQ-058's silence; this phase's conservative
  choice: preserve the caller-supplied value exactly, never widen or
  transform it — verified by `test_authority_fields_never_widened_or_transformed`).
- Requires `election_reference` (HBDC-REQ-064) as a non-empty string,
  never a boolean.
- Never launches a decision session, infers approval, accepts a bare
  `approved=True`, treats root/admin UID as governance authority, or
  mints its own CHGR (verified by AST-precise scans in the companion
  test module — not mere substring search, to avoid false positives from
  this module's own extensive prose explaining what it deliberately does
  *not* do).
- The real invocation boundary remains OS filesystem write permission on
  the Protected Root (HBDC-REQ-066) — `_require_trust_store_available()`
  is a structural precondition check (root exists, is a directory, is
  not a symlink), never a substitute authority check.

## 7. RepositoryIdentity Prerequisite Behavior

`_resolve_repository_id()` calls `read_repository_identity()` only. A
missing identity raises `RepositoryIdentityMissingError` — fails closed,
deterministic, before any trust-store mutation. `ensure_repository_identity()`
is never called by any code path in the producer module (verified by an
AST scan for `ast.Call` nodes naming that function — zero found). This
preserves HBDC-REQ-068's explicit separation: repository-identity
creation is not folded into binding creation as an implicit side effect.

## 8. Canonical-Root Behavior

`_resolve_canonical_root()` calls the unmodified
`hatp_bootstrap.resolve_canonical_deployment_root()` — the identical
function `HATPTrustStore`'s own consumer chain and HMIC-REQ-043/044 both
already use. A path that cannot be resolved (e.g. does not exist) raises
`DeploymentRootUnresolvableError` (wrapping the underlying `OSError`).
No alternate canonicalization logic exists anywhere in the producer.

## 9. Idempotency Implementation Choice (149O.20L.7H finding, disposed of)

**Chosen:** compare `canonical_deployment_root`, `principal_id`,
`signer_key_id`, `provider_profile`, `authority_scope` — the
authority-bearing fields — for exact equality; `valid_from` is
deliberately excluded.

**Rationale:** `valid_from` is producer-generated freshness metadata
(always "now" at every call), not caller-supplied authority content.
Including it in the idempotency comparison would make the
`ALREADY_SATISFIED` outcome unreachable by construction — every repeated
create call would produce a different `valid_from` and therefore always
appear "different," defeating HBDC-REQ-059's stated idempotent-preserve
requirement. This mirrors `ensure_repository_identity()`'s own
discipline of never comparing its analogous `created_at` field. This is
an implementation-level conservative choice, not new normative contract
text — documented here per the governing instructions' explicit
requirement to name, not silently resolve, this class of ambiguity.

## 10. Audit-Evidence Mechanism Choice (HBDC-REQ-062, disposed of)

**Chosen:** `pcae.core.provenance.append_provenance_event()`, called
against the target repository's own tree (`repository_root`), with
`agent_id` always passed explicitly as `f"admin:{principal_id}"` — so
`read_agent_lock()` is never invoked and the audit path carries no
runtime dependency on any PCAE agent-lock state.

**Alternative considered and rejected:** constructing a full CHGR /
`governance/publication` record for every producer operation. Rejected
because: (a) CHGR records model human governance *decisions*, not
producer write-audit trails — reusing that machinery for a
create/rotate/revoke log entry would overload its intended shape, not
reuse it faithfully; (b) HBDC-REQ-062 explicitly forbids introducing "a
bespoke audit mechanism," and `pcae.core.provenance` is the one
genuinely pre-existing, generically-named, already-repository-wide
mechanism whose stated purpose already matches "audit trail of what
happened" (the same mechanism `pcae session bootstrap` itself reports
event counts from). This is documented as this phase's own
implementation choice, not new normative HBDC-001 text.

## 11. Atomic-Publication Implementation

`_atomic_write_registry()` reuses `repository_identity.py::_write_atomic`'s
exact idiom: `tempfile.mkstemp` in the same directory as `registry.json`,
write + `flush` + `fsync`, symlink rejection immediately before the write
and again immediately before `os.replace` (TOCTOU-safe), then
`os.replace`. **One documented deviation:** unlike
`repository_identity.py::_write_atomic`, this function never `mkdir`s
its own containing directory — the Protected Root's existence is a
strict precondition (`_require_trust_store_available`, checked before
the transition lock is even acquired), never auto-provisioned by this
module, mirroring `hatp_bootstrap.py`'s own stated "this module never
creates it" discipline for the Protected Root (HATP-REQ-030).

## 12. Fault-Injection Results

`tests/test_hatp_deployment_binding_admin.py`:

- `test_interrupted_write_before_rename_leaves_no_partial_registry`:
  `os.replace` monkeypatched to raise mid-operation → `registry.json`
  remains absent, no leaked `.tmp-deployment-binding-*` temp file.
- `test_readback_mismatch_function_detects_real_corruption` /
  `test_readback_mismatch_is_treated_as_failure`: a forced read-back
  mismatch raises `DeploymentBindingReadbackMismatchError` — success is
  never reported on a rename alone.
- Symlink substitution: `test_trust_store_root_symlink_rejected`,
  `test_registry_path_symlink_substitution_rejected`,
  `test_lock_file_path_symlink_rejected` — all three fail closed with
  `HATPTrustStoreSymlinkError`.
- Malformed/duplicate registry: `test_malformed_registry_document_fails_closed_not_repaired`,
  `test_duplicate_registry_records_fail_closed` — both fail closed via
  the unmodified `hatp_bootstrap._parse_registry_document`; the producer
  never "repairs" a malformed registry.

All 9 outcomes: **PASS.**

## 13. Concurrency Strategy and Results

Non-normative implementation hardening (149O.20L.7H's named absence of a
concurrency-lock requirement): an internal `fcntl.flock`-based exclusive
single-writer lock, `.deployment-binding-transition.lock`, fixed name
directly under the Protected Root, mirroring
`hatp_mandatory_certification.py`'s own `.certification-transition.lock`
pattern. Every read of current registry state that determines a
create/rotate/revoke outcome happens *inside* this lock's critical
section, re-read fresh from disk (TOCTOU discipline — §14).

Tests: `test_concurrent_create_produces_exactly_one_deterministic_active_entry`
(8 threads racing an identical create — exactly one `CREATED`, the rest
`ALREADY_SATISFIED`, zero errors, exactly one registry entry) and
`test_concurrent_rotate_vs_revoke_yields_one_deterministic_final_state`
(concurrent rotate/revoke against the same entry — final on-disk state
always fully self-consistent, never torn, `revoked_at` present iff
`status == "revoked"`). Both: **PASS.**

## 14. TOCTOU Protection

Every public function's validation (existing-entry lookup, idempotency
comparison, revoked-entry check) happens after acquiring
`_deployment_binding_transition_lock` and reads the registry document
fresh from disk at that point — never validated once outside the lock
and then blindly written. This is the same section the atomic write and
read-back both execute inside.

## 15. Registry Round-Trip

`test_create_round_trip_through_production_consumer_chain`,
`test_rotate_round_trip_exactly_one_entry_old_no_longer_matches`,
`test_revoke_round_trip_consumer_no_longer_matches`: producer output →
`HATPTrustStore(_test_only_root=...)` (test-only construction of the
exact production read path) → `load_repository_enrollment()` →
`deployment_binding_matches()` — proven `True` for an active binding
with matching `repository_id`/`canonical_deployment_root`, and `False`
once revoked. No producer-only representation exists anywhere in the
chain. All: **PASS.**

## 16. Strict Timestamp Generation and Adversarial Results

`_canonical_timestamp_now()` emits `YYYY-MM-DDTHH:MM:SS.fffZ` (millisecond
precision), self-asserted against `_TIMESTAMP_PATTERN`
(`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) before ever being
returned — the writer never relies on `hatp_bootstrap.py`'s more
permissive read-path parser to accept a noncanonical form.
`test_noncanonical_timestamp_forms_never_emitted` documents, and confirms
the strict regex rejects, exactly the four noncanonical forms 7G/7H
named: non-`Z` offset, >6-digit fraction, space-separated date/time, and
a bare missing-`Z` form. **`hatp_bootstrap.py`'s permissive read-path
parser (`_parse_iso_timestamp`) is not modified by this phase** — carried
forward as a named, deferred, non-blocking finding (§21).

## 17. Signer/Provider/Principal/Scope Handling

No registry vocabulary exists for `signer_key_id`/`provider_profile` in
this codebase today (149O.20L.7H's own named finding: HBDC-REQ-058 is
silent on cross-validation). This phase's conservative choice: validate
shape only (non-empty string), preserve the caller-supplied value
exactly, never transform or widen it into broader authority.
`principal_id` and `authority_scope` are handled identically — no
numeric-UID substitution, no wildcard injection, no scope-widening logic
anywhere in the producer.

## 18. Ownership/Mode/ACL/Symlink Handling

Real enforcement remains OS-level file permissions on the Protected
Root, unchanged (HBDC-REQ-066/HATP-REQ-030 precedent). This module adds
no redundant in-process UID/ACL check beyond `_require_trust_store_available()`'s
structural existence/directory/non-symlink precondition — consistent
with the instruction not to weaken *or* invent filesystem/OS controls.
Symlink defenses (`_reject_symlink`, mirroring
`repository_identity.py::_reject_symlink` exactly — immediate target +
immediate parent, per HBDC-REQ-063's explicit citation of that module's
idiom) are applied to the store root, the registry path, and the
transition-lock path, each checked immediately before every disk
operation.

## 19. Result/Error Model

`DeploymentBindingOutcome` (`CREATED`, `ALREADY_SATISFIED`, `ROTATED`,
`REVOKED`, `ALREADY_REVOKED`) is the success-outcome vocabulary, returned
inside `DeploymentBindingOperationResult(outcome, binding,
previous_binding)`. Failure/conflict/not-found/invalid conditions are
raised as a typed exception hierarchy rooted at
`HATPDeploymentBindingAdminError` — mirroring this codebase's existing
convention throughout `hatp_mandatory_certification.py`/
`scripts/hatp_certification_admin.py` (typed exceptions, not a single
overloaded enum) rather than inventing a new pattern.

## 20. Preview Capability

Implemented (`SHOULD`, per 7H). Three read-only functions compute the
exact outcome kind (`WOULD_CREATE`, `WOULD_NOOP_ALREADY_SATISFIED`,
`WOULD_CONFLICT`, `WOULD_ROTATE`, `WOULD_FAIL_NOT_FOUND`,
`WOULD_FAIL_REVOKED`, `WOULD_REVOKE`, `WOULD_NOOP_ALREADY_REVOKED`)
without acquiring the transition lock or touching disk. Never a
first-use election mechanism — it only computes and reports.

## 21. 7H Finding Dispositions (carried forward, not silently closed)

| Finding | Disposition this phase |
|---|---|
| Idempotency-comparison field-set ambiguity (REQ-059) | Resolved at the implementation layer: authority-bearing fields only, excludes `valid_from` (§9). Not new contract text. |
| Signer/provider-profile vocabulary cross-validation silence (REQ-058) | Deferred, as 7H named it: shape-only validation, exact value preserved (§17). |
| Rotate/revoke-on-nonexistent-entry underspecification (REQ-060/061) | Resolved conservatively: both fail closed, never create/degrade (§ Creation semantics table). |
| Audit-write-ordering silence (REQ-062) | Resolved at the implementation layer: validate → mutate → read-back-verify → audit → return; documented in the producer module's own docstring as a named, non-normative choice. |
| Fail-closed-on-absent-identity in prose, not RFC-2119 text (REQ-057) | Unchanged — carried forward as a documentation-only gap in the contract itself, not something an implementation phase can or should silently promote to normative text. |
| Preview architecture `SHOULD`, not `SHALL` | Implemented anyway (§20); still not claimed as satisfying a `SHALL`. |
| Absence of a concurrency-lock requirement (cf. HMIC-REQ-097) | Implementation hardening added (§13) — explicitly documented as non-normative, not new HBDC-001 text. |

## 22. HMIC Revocation-Validation Gap (F3-residual) — Carried, Untouched

`HMIC-REQ-103`'s 12-step validation algorithm is not modified by this
phase. `hatp_mandatory_certification.py`,
`HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`, and
`CertificationRecord`'s schema are all byte-unchanged. This phase's
producer implementation does not, and does not claim to, cause a revoked
`DeploymentBinding` to invalidate any existing certification under
current HMIC-001 text — that gap remains exactly as 7G/7H described it,
unresolved, out of scope for HBDC-001.

## 23. Timestamp-Parser Gap — Carried, Untouched

`hatp_bootstrap.py::_parse_iso_timestamp`/`_require_timestamp` are
byte-unchanged. The producer's own output is bound to the strict grammar
regardless (§16) — HBDC-REQ-067 is satisfied without touching the
read-path parser. Whether to also harden the read-path parser itself
remains named, deferred future work, not resolved here (per 7G's own
explicit disposition, unaffected by this phase).

## 24. Proof HBDC-001 v1.1 Unchanged

`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` is byte-identical
to its state at phase entry (`git diff --name-only
<7H-entry-sha>..HEAD -- docs/contracts` is empty; verified by
`TestContractUnchanged` in the companion test module). No `HBDC-REQ-###`
text was added, removed, or altered. Requirement-ID set remains exactly
1..70, gapless.

## 25. Proof of No Dell Side Effects

- No Dell SSH session was opened this phase.
- No `.pcae/repository-identity.json` was created in this repository's
  own working tree (verified:
  `test_no_real_repository_identity_leaked_into_this_repositorys_working_tree`).
- No `.pcae/registry.json` was created under a production-looking path in
  this repository.
- Every test in `tests/test_hatp_deployment_binding_admin.py` and
  `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py`
  uses only disposable `tmp_path` repositories and trust stores via the
  `_protected_root`/repository-root test seams — never
  `HATPTrustStore.production()`'s real path.
- No `AuthorityEvidence` with `approved=True` or an unverified boolean
  exists anywhere in the codebase (AST-verified).
- No CHGR record was minted by this phase.
- No first-use election was initiated. CHGR condition 6 remains
  unsatisfied, as intended.

## 26. Boundary State

```
Boundary C     NOT AUTHORIZED
Boundary A     NOT AUTHORIZED
HATP           NOT READY
Runtime        Observed / observe / unavailable (unchanged)
```

## 27. Tests

- `tests/test_hatp_deployment_binding_admin.py`: **55 passed, 0 failed**
  — create/rotate/revoke happy paths; idempotency; conflict/not-found/
  revoked fail-closed paths; `RepositoryIdentity` prerequisite (missing,
  malformed, never-implicitly-created); authority-evidence validation;
  canonical-root/malformed-registry/duplicate-registry/trust-store-
  availability/symlink adversarial paths; fault injection (interrupted
  write, read-back mismatch); concurrency (8-way race, rotate-vs-revoke
  race); producer/consumer round-trip (create/rotate/revoke); multi-
  repository and multi-root isolation; strict timestamp grammar +
  adversarial noncanonical forms; schema-preservation proof (exactly 9
  fields, no forbidden new fields); no-agent-reachable-surface proof;
  preview (never writes); audit-evidence content and count; no real
  `RepositoryIdentity` leaked into this repository.
- `tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py`:
  **41 passed, 0 failed** — independent phase-evidence module (does not
  import the unit-test module as an oracle): contract byte-unchanged;
  three distinct public functions with the expected signatures; no
  generic `write_binding()`; no schema drift; `HATPTrustStore` still zero
  write methods; not agent-reachable (static + AST scans); no Dell side
  effects; full HBDC-REQ-056..070 requirement-to-code traceability
  matrix.
- **Combined new tests this phase: 96 passed, 0 failed.**

## 28. Regression Classification

**Targeted HATP/HBDC/HMIC/repository-identity subset**
(`pytest tests/ -k "hatp or hbdc or hmic or repository_identity"`,
`test_phase_149o_7_...` excluded — pre-existing, unrelated
`ModuleNotFoundError: fido2` collection error, reproduced identically at
baseline):

- **Baseline** (this phase's new files moved out of the working tree,
  true `origin/main`/`HEAD` state): 212 failed, 4142 passed, 5 skipped,
  9 errors.
- **With this phase's changes restored:** 229 failed, 4202 passed, 5
  skipped, 9 errors.
- **Delta (exact, node-ID diffed via `comm`):** 0 resolved, **17 new
  failures**, zero unexplained. Every one of the 17 is a historical
  phase-pin assertion from an *earlier* phase's own companion test module
  (149O.1E, 149O.1G, 149O.14, 149O.19.5G, 149O.20A, 149O.20B, 149O.20C,
  149O.20D, 149O.20D.1, 149O.20E, 149O.20K, 149O.20K.1, 149O.20L.1)
  checking either "no `src/pcae/**`/`scripts/**` file changed since *my*
  phase entry" or (one case, 149O.19.5G) a substring scan for HMIC
  writer-primitive names anywhere in `src/pcae/**` source text. Both
  failure shapes are individually confirmed (spot-checked: `test_only_
  expected_production_files_changed`, `test_no_scripts_files_dirty_in_
  working_tree`, `test_no_production_src_pcae_file_calls_the_writer_
  primitives`) to trip purely because this phase adds two *new* files
  under `src/pcae/core/` and `scripts/` — not because any *existing*,
  previously-frozen file changed. This is a structural, unavoidable
  consequence of any future phase ever adding a new file to those trees
  under this repository's own frozen-phase-pin testing convention — the
  same "tests require migration, not a contradiction" class 7G's own
  report named for its 37-failure HBDC-version-pin class. **Remediation:**
  out of this phase's allowed-file scope (would require touching a dozen
  historical phase test modules spanning 149O.1E through 149O.20L.1);
  named here explicitly, not concealed, mirroring 7G's/7H's own
  precedent of naming rather than silently absorbing pre-existing
  out-of-scope red gates.

**3 pre-existing 7G/7H self-pins, also confirmed (not new — these
concern 7G's/7H's own "no producer exists yet" assumption, necessarily
falsified by this phase's intentional, in-scope implementation, exactly
analogous to 7G's own precedent for its own 37-failure class):**
`test_phase_149o_20l_7g_...py::TestNoImplementationNoMutation::
test_no_deployment_binding_admin_script_created`,
`test_phase_149o_20l_7h_...py::TestImplementationPlanMapping::
test_no_admin_tool_script_created_yet`,
`test_phase_149o_20l_7h_...py::TestNoImplementationNoBindingNoMutation::
test_no_write_function_added_anywhere_in_src_pcae`.

**Full `pytest -m fast_green -n auto` sweep, run twice this phase, full
untruncated logs captured and node-ID diffed via `comm`**
(`--continue-on-collection-errors` for the one pre-existing, unrelated
`fido2` collection error, reproduced identically at both baseline and
with-phase-changes):

- **Baseline** (this phase's four new files moved out of the working
  tree, true `origin/main`/`HEAD` state): summary line `220 failed, 7445
  passed, 5 skipped, 10 errors`; 212 unique `FAILED` node IDs captured
  (the 8-node discrepancy between the summary count and the unique
  node-ID count is a known `pytest-xdist` worker-retry reporting
  artifact, present identically in both runs' measurement method, so it
  does not affect the diff below).
- **With this phase's changes restored:** summary line `231 failed, 7530
  passed, 5 skipped, 10 errors`; 231 unique `FAILED` node IDs (the
  discrepancy above does not recur in this run).
- **Delta (exact, `comm -13`/`comm -23` on the sorted node-ID lists):
  23 new failures, 4 resolved, zero unexplained.**
  - **23 new failures**, all individually confirmed the same two
    mechanical classes already established in the targeted-subset
    analysis above: 20 are the "new file present under `src/pcae/**` or
    `scripts/**`" historical-pin class, spanning phases 149O.1G,
    149O.14, 149O.19.5G, 149O.20A, 149O.20B, 149O.20C, 149O.20D,
    149O.20D.1, 149O.20E, 149O.20H, 149O.20K, 149O.20K.1, 149O.20L.1,
    149O.20L.7D.9, 149O.20L.7D.10, 149O.20L.7E (a wider set than the
    13-phase targeted-subset sample, since the full fast_green sweep
    includes many more historical phase-pin modules than the
    HATP/HBDC/HMIC-keyword-filtered subset); the remaining 3 are the
    already-named 7G/7H self-pins (§ above) asserting "no producer
    exists yet," necessarily falsified by this phase's own intentional,
    in-scope implementation.
  - **4 resolved** (baseline-failing, now passing):
    `test_backend_cli.py::Test96DConnectedDemo::test_demo_save_and_show`,
    `test_backend_cli.py::Test96EConnectedHardeningCLI::test_json_verify_latest_contract`,
    `test_backend_cli.py::TestApplyPlanShow::test_show_after_create`,
    `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`.
    None of the four touch HATP/HBDC/HMIC/repository-identity/provenance
    code in any way; all four are subprocess-driven CLI tests already
    named in `tests/conftest.py`'s own fast-green-selection docstring as
    a known source of parallel-worker timing flakiness under `-n auto`
    ("subprocess-heavy tests ... spawn a pcae subprocess per test").
    Classified as pre-existing test flakiness, not an effect of this
    phase's changes.

## 29. 7H Non-Blocking Findings — Final Status

All seven of 149O.20L.7H's non-blocking findings are individually
disposed of in §21, none silently closed through implementation choice
without being named.

## 30. Final Verdict

**IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.**

All of HBDC-REQ-056..070's behavior is implemented with no known
Blocking defect. No contract or schema contradiction was discovered
during implementation. This phase does not claim to be independently
verified — that is 149O.20L.7J's job.

```
HBDC-001                            v1.1 — INDEPENDENTLY VERIFIED CONTRACT (149O.20L.7H, unchanged)
DeploymentBinding producer          IMPLEMENTED — INDEPENDENT VERIFICATION PENDING
Create capability                   Implemented, not exercised against real deployment
Rotate capability                   Implemented, not exercised against real deployment
Revoke capability                   Implemented, not exercised against real deployment
RepositoryIdentity producer         EXISTING — UNCHANGED
Dell RepositoryIdentity             ABSENT
Dell DeploymentBinding              ABSENT
Dell source                         Old deployed implementation relative to new Mac HEAD (unchanged this phase)
Boundary P                          Physical host provisioning remains independently verified (149O.20L.7E, unchanged)
Boundary C                          NOT AUTHORIZED
Boundary A                          NOT AUTHORIZED
HATP                                NOT READY
Runtime                             Observed / observe / unavailable
```

## 31. Recommended Next Phase

**149O.20L.7J — DeploymentBinding Producer Implementation Independent
Verification.** Must independently reconstruct the implementation from
primary source (not accept this phase's own report or test module as an
oracle) and adversarially verify: all of HBDC-REQ-056..070; create;
rotate; revoke; atomicity; lifecycle semantics; idempotency; concurrency;
audit evidence; strict timestamps; `RepositoryIdentity` prerequisite;
producer/consumer round-trip; no schema drift; no authority bypass; the
two implementation-level choices this phase documented but did not
freeze as new contract text (§9's idempotency field-set exclusion, §10's
audit-mechanism choice) — including whether either should itself become
new normative HBDC-001 text or remain implementation-only. No Dell
binding and no election in 7J.

## 32. Governance Results

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated —
  historical `tasks/done/`/`tasks/DONE.md` entries prior phases already
  carried forward; outside this phase's allowed-file scope; not
  remediated here)
- **pcae_push_check:** clean (nothing_to_push, at phase entry)
- **pcae_runtime_inspect:** Observed / observe / unavailable (unchanged)
- **pcae_notify_status:** telegram configured/enabled
- **pcae_phase_report_reconcile (149O.20L.7H):** reconciled, mutation none

## 33. Governance

Governed PCAE lifecycle used throughout: `pcae task new`/`pcae task
update --allowed-file`, `pcae commit implementation`, `pcae task
transition`, `pcae phase complete --stage-pending-report` then `pcae
push` then `pcae phase complete` (promote). No raw `git commit`/`git
push`. No `--no-verify`. No force push. No hook bypass.
