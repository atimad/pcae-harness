# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3 — Canonical Human-Principal,
# Protected-Presentation, and HPAC Proof-Lifecycle Foundation Implementation

## 1. Objective

Implement the first bounded implementation slice (plan §37/§52's "Phase
1") of the eight-layer HPAC-001 v2.0 implementation plan produced by
149O.20L.7O.3W.1R.2B.1R.1.1R.2: canonical models/stores for
`HumanPrincipalRegistry`, `TrustedApprovalPresentationEvidence`,
`HumanAuthenticationProof`, and the HPAC hash-chained lifecycle, plus
deterministic non-real `HumanAuthenticator`/
`ProtectedApprovalPresentationMechanism` implementations and the inert
Gate-9 consumption model/store primitives, plus adversarial/trust-forgery
test coverage. No PB integration, no `runtime_authority.py` production
change, no B1/B7/N1/N2 repair, no real FIDO2, no real UI, no hardware, no
Gate-5/9 wiring.

## 2. Baseline

`phase_entry_sha = f64dd95a16b1b7db2b5c1ce74b7ea402fcf82505` (clean, zero
commits ahead of `origin/main`). `v0.4.3` release commit
`63580893b1de4782a694ab802ff7bdebdf29b0e6` unchanged and unreferenced by
this phase's own diff. Runtime confirmed `not_implemented` /
`Observed` / `observe` / `unavailable` via `pcae runtime inspect` before
any code was written, and untouched by every file this phase changed
(confirmed by `git status --short`/`git diff --stat`: zero
`src/pcae/core/runtime_*.py` files appear in this phase's changed-file
list). `pcae health`/`pcae check`/`pcae status coherence` all passed at
entry.

## 3. Verified contract baseline

RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, PBRD-001 v2.0, RDGO-001
v3.0, RPAC-001 v1.0 — the exact set independently verified by
149O.20L.7O.3W.1R.2B.1R.1.1R.1 (7/7 original BLOCKING closed, 2/2
MUST-FIX closed, 0 new BLOCKING, N2 contract gap closed, implementation
readiness YES). HPAC-001 v2.0 was re-read in full for this phase
(`docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`, all 1201
lines), focusing on §4-§9 (principal/registry), §10-17 (authenticator
interface, challenge, proof), §38-40 (canonical subject, presentation
evidence, lifecycle), and §41 (Gate-9 consumption). No normative contract
file was modified by this phase (`git status --short` shows zero changes
under `docs/contracts/`).

## 4. Planning baseline

149O.20L.7O.3W.1R.2B.1R.1.1R.2's full planning document (1115 lines) was
read in full, not summarized. This phase implements exactly its §37/§52
"Phase 1" scope: the file plan in §34's Phase-1 rows, the component
inventory of §6, the reuse audit of §35, the genesis-authority design of
§19, and the narrow transition API of §20. No later layer (verifier,
B1/B7/N1/N2 repair, real FIDO2, real UI, PB integration, Gate 5/9 wiring)
was collapsed into this phase.

## 5. Scope

Implemented exactly the ten items listed in the governing phase prompt
§"Exact implementation scope": `HumanPrincipalRegistry` model+store,
`TrustedApprovalPresentationEvidence` model+store,
`HumanAuthenticationProof` model+store, HPAC lifecycle model+store,
deterministic non-real `HumanAuthenticator`, deterministic non-real
`ProtectedApprovalPresentationMechanism`, bounded supporting
validators/helpers (`hpac_foundation.py`), and adversarial tests. The
inert Gate-9 `RuntimeInvocationAuthorityConsumption` model+store was also
implemented per plan §34's file-plan (`runtime_invocation_authority_
consumption.py` listed as New/Phase-1) and per phase-prompt §32's
explicit allowance ("If the first slice explicitly includes the Gate-9
consumption record model/store: implement... inert model/store
primitives. No RDGO wiring.").

Not implemented (confirmed absent from `git status --short`): real
FIDO2, real authenticator enumeration, physical security-key
interaction, real protected UI, approval CLI, enrollment CLI, PB
runtime-dispatch integration, B1/B7/N1/N2 repair, Runtime Enforcement,
Shell Gate, Gate-9 runtime dispatch, external runtime execution.

## 6. Reuse audit

- `runtime_authority.compute_canonical_digest` (already public) reused
  directly by `hpac_foundation.canonical_digest` for every HPAC-001
  digest computation (HPAC-REQ-089's exact canonicalization rule) —
  no reimplementation, no modification to `runtime_authority.py`.
- Atomic-write idiom (temp file same directory, fsync, `os.replace`)
  mirrored from `repository_identity._write_atomic`, split into two
  variants in `hpac_foundation.py`: `write_atomic_replace` (mutable
  whole-document rewrite, registry) and `write_atomic_create_only`
  (`O_CREAT|O_EXCL` single-winner create-only, presentation/proof/
  lifecycle/consumption).
- Parsing discipline (`_reject_symlink`, `_require_nonempty_str`,
  `_require_timestamp`, `_require_revoked_at_consistency`,
  reject-on-any-anomaly closed-schema parsing) mirrored as a *pattern*
  from `hatp_bootstrap.py`, reimplemented independently in
  `hpac_foundation.py`/`human_principal_registry.py` under HPAC-001's own
  entirely separate namespace (HPAC-REQ-018) — no import of, or call
  into, `hatp_bootstrap.py` itself.
- `hatp_providers.TestHATPProofVerifierProvider`'s simulation-only
  tagging precedent reused as the pattern for
  `DeterministicTestHumanAuthenticator.SIMULATION_ONLY` /
  `DeterministicTestPresentationMechanism.SIMULATION_ONLY`.
- `hatp_providers.HATPHardwareSigner`'s `Protocol` shape reused as the
  pattern for `HumanAuthenticator`/`ProtectedApprovalPresentationMechanism`.
- No existing shared canonical-store primitive module existed before this
  phase; `hpac_foundation.py` is the one new bounded-helpers module this
  phase adds beyond plan §34's file list, justified by phase-prompt item
  9 ("bounded supporting validators/helpers required by those
  components") to avoid duplicating identical atomic-write/symlink-reject/
  ID-generation code across six store modules.

## 7. File plan

| File | Status | Responsibility |
|---|---|---|
| `src/pcae/core/hpac_foundation.py` | New (323 lines) | Shared bounded helpers: `ProtectedAdminCapability` marker, canonical digest re-export, protected-root resolver, symlink/ID/timestamp validators, atomic-write primitives |
| `src/pcae/core/human_principal_registry.py` | New (512 lines) | `PrincipalRecord`/`CredentialRecord` + `HumanPrincipalRegistryStore` |
| `src/pcae/core/human_authenticator.py` | New (130 lines) | `HumanAuthenticator` Protocol, `MechanismDescriptor`/`MechanismStatus`/`Challenge`/`ProofMaterial` |
| `src/pcae/core/human_authenticator_deterministic.py` | New (140 lines) | `DeterministicTestHumanAuthenticator` |
| `src/pcae/core/approval_presentation.py` | New (424 lines) | `CanonicalRuntimeApprovalSubject`, `ProtectedApprovalPresentationMechanism` Protocol, `PresentationMechanismDescriptor`+store, `TrustedApprovalPresentationEvidence`+store |
| `src/pcae/core/approval_presentation_deterministic.py` | New (172 lines) | `DeterministicTestPresentationMechanism` |
| `src/pcae/core/human_authentication_proof.py` | New (170 lines) | `HumanAuthenticationProof` + `HumanAuthenticationProofStore` |
| `src/pcae/core/hpac_lifecycle.py` | New (416 lines) | `LifecycleEvent` + `HPACLifecycleStore` (narrow transition API, hash chain) |
| `src/pcae/core/runtime_invocation_authority_consumption.py` | New (212 lines) | Inert `RuntimeInvocationAuthorityConsumption` + store |
| `tests/test_hpac_principal_registry.py` | New (297 lines, 16 tests) | Registry adversarial coverage |
| `tests/test_hpac_authenticator_deterministic.py` | New (136 lines, 11 tests) | Deterministic authenticator coverage |
| `tests/test_hpac_approval_presentation.py` | New (240 lines, 17 tests) | Presentation evidence/store coverage |
| `tests/test_hpac_authentication_proof.py` | New (186 lines, 14 tests) | Proof store coverage |
| `tests/test_hpac_lifecycle.py` | New (317 lines, 15 tests) | Lifecycle hash-chain coverage |
| `tests/test_hpac_authority_consumption.py` | New (144 lines, 7 tests) | Gate-9 inert store coverage |

Zero files under `src/pcae/core/runtime_authority.py`,
`runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`,
`permission_broker_foundation.py`, `hatp_bootstrap.py`,
`hatp_fido2_provider.py`, `hatp_providers.py`, or any
`docs/contracts/*.md` file appear in this phase's `git status --short`.

## 8. HumanPrincipalRegistry model

`PrincipalRecord` (`principal_id`, `status`, `enrollment_provenance_ref`,
`enrolled_at`, `revoked_at`) and `CredentialRecord` (`credential_id`,
`principal_id`, `mechanism_id`, `public_key`, `assurance_capabilities`,
`status`, `enrollment_provenance_ref`, `enrolled_at`, `revoked_at`) —
HPAC-REQ-013's exact closed field sets, no third record kind. No
`display_name`/`email`/personal metadata field exists anywhere on either
dataclass (HPAC-REQ-010). `CredentialRecord` has no private-key/PIN/
biometric/path field (structurally impossible to add one by accident,
since the dataclass itself has no such slot).

## 9. Principal registry store

`HumanPrincipalRegistryStore(root: Path)`: whole-document
read-modify-atomic-rewrite (`write_atomic_replace`) with read-back
verification, sorted-list serialization (HPAC-REQ-016), schema-version
gate failing closed on unknown versions, reject-on-any-anomaly parsing
(unknown field, duplicate ID, credential naming an unknown principal).
Mutation (`enroll_principal`/`revoke_principal`/`enroll_credential`/
`revoke_credential`) requires an explicit `ProtectedAdminCapability`
marker; every mutation has a corresponding never-writes preview method
(`preview_enroll_principal` etc.) returning a closed
would-enroll/already-enrolled/conflict/would-revoke/already-revoked/
not-found classification (HPAC-REQ-026).

## 10. Registry trust boundary

**Canonical registry mechanics implemented; real trusted enrollment not
implemented** — stated in the module's own docstring. `ProtectedAdminCapability`
is explicitly documented as *not* a real ceremony: "Constructing this
object is deliberately trivial and grants no real-world authority
whatsoever." The store never treats "file exists" as "trusted principal"
— resolution always re-parses and re-validates the full closed schema on
every call; there is no cached/short-circuit trust path.

## 11. Principal fixtures

Tests construct fixture principals only through
`HumanPrincipalRegistryStore.enroll_principal`/`enroll_credential`
gated behind `ProtectedAdminCapability()` — never by hand-constructing a
`PrincipalRecord` and expecting it to resolve
(`test_caller_constructed_equivalent_object_is_not_canonical` proves a
hand-built lookalike never resolves). Eligibility is structural (the
capability-marker parameter), not a magic string.

## 12. Presentation evidence model

`TrustedApprovalPresentationEvidence` implements HPAC-REQ-091's exact
thirteen closed top-level fields plus the exact thirteen
`human_visible_facts` sub-fields, validated by `_validate_evidence_document`.
`CanonicalRuntimeApprovalSubject` implements HPAC-REQ-089's exact six
fields. Binding among canonical subject, presentation, mechanism identity,
challenge correlation, and election is enforced at
`resolve_structural`, not merely declared: subject-digest equality,
approval_preview_digest == human_visible_representation_digest
(HPAC-REQ-092), election-ordering (`occurred_at >= presented_at`), and
attestation-object digest self-consistency are all independently
re-derived and compared on every read.

## 13. Presentation evidence store

`TrustedApprovalPresentationStore(root)`: create-only
(`write_atomic_create_only`, `O_CREAT|O_EXCL`), atomic, lookup only by
the closed `(presentation_id, presentation_digest)` pair. Corruption,
duplicate ID, symlinked root/path, and digest mismatch all fail closed
(tests: `test_symlinked_presentation_store_path_rejected`,
`test_truncated_json_fails_closed`,
`test_replay_duplicate_presentation_id_rejected`).

## 14. Presentation trust

Honest boundary, stated in the module docstring:
`resolve_structural` performs only structural/shape checks — field-set
closure, digest self-consistency, election ordering — and **explicitly
does not** perform cryptographic `mechanism_attestation` signature
verification against a real installed verifier configuration (that is
HPAC-018 step 5, Phase 3, out of scope). This phase does **not** repeat
the B-3 defect class: a schema-valid evidence object with a
self-consistent-but-unbound `mechanism_attestation_digest` is rejected
(`test_public_digest_recomputation_alone_is_not_authority` proves a
forged `approval_id` breaks the attestation-object binding even though
the outer document's own digest recomputes correctly).

## 15. Presentation mechanism interface

`ProtectedApprovalPresentationMechanism` Protocol (`descriptor()`,
`present()`) — HPAC-001 §11's non-collapse requirement kept as a
*separate* Protocol from `HumanAuthenticator`, in a separate module, per
plan §6.

## 16. Deterministic presentation mechanism

`DeterministicTestPresentationMechanism` (172 lines): `SIMULATION_ONLY:
Final[bool] = True`, `MECHANISM_ID = "hpac.deterministic.presentation.
test-only.v1"` (never `hpac.fido2.uv_presence.v2`-equal). Parameterized
via `fault` to produce: `digest_mismatch`, `ordering_violation`,
`forged_attestation`, `blind_touch` (degenerate zero'd election id) — all
four independently tested and independently rejected by
`resolve_structural`.

## 17. Real-eligibility wall

`MECHANISM_ID` is a fixed `Final` class constant with no constructor
override; `descriptor().verifier_kind` is hardcoded
`"deterministic-test-fixture"`. A future real-dispatch allowlist (not
built in this phase) checking `mechanism_id` against a real-mechanism set
structurally excludes this fixture, since its ID is namespaced
`*.test-only.*` and never equals a real mechanism's frozen ID.

## 18. Authentication proof model

`HumanAuthenticationProof` implements HPAC-REQ-052's exact fourteen
closed fields. `up`/`uv` are structurally enforced `const true` at
`_validate_proof_document` (a proof recording `up=False` or `uv=False`
is rejected by the store, honestly documenting that a real verifier —
Phase 3 — would have rejected it even earlier).

## 19. Proof store

`HumanAuthenticationProofStore(root)`: create-only, atomic,
canonical-lookup-only by `proof_id`, digest recomputation on every
create/resolve. `test_raw_proof_object_never_produced_by_authenticator_
alone` proves a hand-built lookalike proof never resolves unless
explicitly submitted via `create()`.

## 20. Lifecycle model

`LifecycleEvent` implements HPAC-REQ-095's exact fifteen closed fields
plus the nine-field closed `binding` sub-object. States:
`CHALLENGE_CREATED` → `ASSERTION_RECEIVED` → `PROOF_VERIFIED` →
`PROOF_VERIFIED_AND_BOUND`, or terminal `EXPIRED`/`REVOKED`/`REJECTED` —
exactly HPAC-REQ-095's table, no invented state.

## 21. Hash chain

`event_digest` is self-excluding SHA-256 over canonical bytes;
`previous_event_digest` chains strictly (null only at sequence 0).
`_load_chain` independently recomputes every event's digest and hash
link on every read (not only at write time) — `test_broken_hash_link_
detected` tampers `previous_event_digest` post-write and proves the
*reader* catches it, not only the writer's own discipline.

## 22. Genesis authority

`open_challenge` (sequence 0) requires the caller to pass an already
`resolve_structural`-resolved `TrustedApprovalPresentationEvidence` whose
own `approval_id`/`approval_subject_digest` are cross-checked against the
challenge being opened (`test_genesis_rejects_wrong_approval_id`). There
is no code path that creates sequence 0 from a bare `approval_id` string.
This is the structural (not merely checkable-field) genesis gating plan
§19 specifies — **hash consistency != canonical authority**, stated
verbatim in the module docstring and demonstrated by
`test_caller_cannot_construct_lifecycle_event_directly_and_have_it_
accepted`, which shows a hand-tampered-onto-disk chain still parses as
"chain-integrity valid" while explicitly documenting that no production
caller reaches that file without direct filesystem tampering, since
`open_challenge` is the only writer and it enforces the antecedent.

## 23. Transition API

Exactly plan §20's five methods: `open_challenge`, `record_assertion`,
`record_verified`, `bind_gate5`, `terminate`. No generic "append any
event" method exists. Each enforces HPAC-REQ-095's entry-condition table
(`test_invalid_predecessor_record_assertion_before_challenge`,
`test_invalid_predecessor_verified_before_assertion`).

## 24. Fork detection

Second genesis for the same `proof_id`
(`test_alternate_chain_second_genesis_rejected`), drifted-binding repeat
(`test_fork_drifted_binding_repeat_rejected`), sequence gap
(`test_gap_in_sequence_rejected`), duplicate sequence
(`test_duplicate_sequence_rejected`) — all `HPACLifecycleForkError`/
`HPACLifecycleGapError`, fail closed.

## 25. Replay semantics

`bind_gate5` is idempotent only for a byte-identical same-binding
approval_digest (`test_bind_gate5_idempotent_same_binding` — no new event
appended); a different `approval_digest` raises
`HPACLifecycleForkError` (`test_bind_gate5_cross_binding_rejected`).
`DeterministicTestHumanAuthenticator.verify_response` independently
rejects a repeated `(challenge_digest, response)` pair
(`test_replay_same_challenge_response_pair_rejected`).

## 26. Authenticator interface

`HumanAuthenticator` Protocol: `describe`, `status`, `prepare_challenge`,
`verify_response`, `resolve_principal` — exactly plan §9's five
responsibilities, zero authority-validation/PB/registry-mutation logic
inside the interface module.

## 27. Deterministic authenticator

`DeterministicTestHumanAuthenticator` (140 lines): independently
parameterizable `up`/`uv`/`credential_matches`/`principal_matches`/
`revoked`/`challenge_response_mode` (`match`/`stale`/`foreign`), replay
detection via an internal consumed-pairs set. `MECHANISM_ID =
"hpac.deterministic.test-only.v1"`, `SIMULATION_ONLY: Final[bool] = True`.

## 28. UP/UV

`test_up_and_uv_are_independently_settable` and
`test_up_and_uv_not_hardcoded_true_on_success` prove all four
combinations (`True/True`, `True/False`, `False/True`, `False/False`) are
faithfully reproduced, not coerced to `True/True` on any code path.

## 29. Same-user-agent limitation

Documented, not claimed solved: the deterministic authenticator's
docstring and this document both state it does **not** prove
same-user-agent resistance (HPAC-REQ-086 is explicitly a Phase 3.1
verification obligation, out of this phase's scope). No test in this
phase asserts same-user-agent resistance; that would be a false claim
this phase does not make.

## 30. Approval integration boundary

`runtime_authority.py` is **not modified** by this phase (confirmed:
absent from `git status --short`). No caller in this phase's new modules
imports `runtime_authority.create_runtime_invocation_approval` or
`validate_approval`; the only `runtime_authority` import anywhere in the
new modules is the pure, pre-existing-public
`compute_canonical_digest` function.

## 31. PB boundary

`runtime_dispatch_permission.py` and `permission_broker_foundation.py`
are **not modified** (confirmed: absent from `git status --short`). No
new module imports either.

## 32. Gate-5/9 boundary

`RuntimeInvocationAuthorityConsumptionStore` is reachable only from test
code calling `new_inert_consumption_record`/`.create()` directly — there
is no Gate-9 caller anywhere in this phase's diff, and RDGO-001's gate
files are untouched.

## 33. Import/global-state

`python -c "import ..."` for all nine new modules succeeds with no
filesystem write, directory creation, network call, or hardware
enumeration (verified directly, §5 below). No module holds a mutable
module-level canonical-authority cache; every store is an explicit
object constructed with a caller-supplied `root: Path`.

## 34. Filesystem confinement

Tested per store: malformed ID grammar
(`test_malformed_id_grammar_rejected`), traversal
(`test_traversal_in_presentation_id_rejected`,
`test_traversal_in_proof_id_rejected`), symlinked root
(`test_symlinked_registry_path_rejected`,
`test_symlinked_presentation_store_path_rejected`), truncated JSON
(`test_truncated_json_fails_closed`), unknown schema version
(`test_unknown_schema_version_fails_closed`, both registry and
presentation/proof variants). All fail closed.

## 35. Repository isolation

`resolve_hpac_protected_root()` takes zero arguments and performs no
repository/cwd/environment lookup at all —
`test_registry_path_resolution_ignores_env_and_cwd` monkeypatches `HOME`
and a plausible `PCAE_HPAC_ROOT` env var and proves the resolved path is
unaffected. `test_repository_path_substitution_is_structurally_
impossible` proves two stores constructed against two different roots
never see each other's records — nothing in any store API accepts a
repository-derived override.

## 36. Fixture isolation

`DETERMINISTIC_MECHANISM_ID` and `DETERMINISTIC_PRESENTATION_MECHANISM_ID`
are fixed module-level `Final` constants outside any real-mechanism
namespace; `SIMULATION_ONLY` is a `Final[bool]` dataclass field with no
constructor parameter capable of setting it `False`. No accidental
upgrade path exists — a real mechanism would need its own distinct class,
not a flag flip on the fixture.

## 37. Contract-to-code map

See Matrix E below.

## 38. Tests

80 new tests across six files (16+11+17+14+15+7), all passing
(§ below). Categories: registry (valid/malformed/duplicate/revoked/
credential-mapping/repository-substitution), presentation
(subject-binding/challenge-binding/fake-evidence/mechanism-mismatch/
replay/fixture-ineligibility), proof (valid/UP-false/UV-false/
wrong-principal/wrong-credential/wrong-challenge/wrong-presentation/
malformed/replay), lifecycle (valid-genesis/valid-transition/
invalid-predecessor/alternate-chain/fork/corruption/duplicate-transition).

## 39. Trust-forgery regressions

Explicitly tested per store, per phase-prompt §41's named defect family:

- **dataclass-replace forgery**: `test_dataclass_replace_forgery_never_
  becomes_canonical` (registry), `test_dataclass_replace_forgery_never_
  becomes_trusted` (presentation), `test_dataclass_replace_forgery_
  never_becomes_canonical` (proof), `test_dataclass_replace_forgery_on_
  proof_material_does_not_change_authenticator_state` (authenticator).
- **copied trusted-looking record**: `test_caller_constructed_
  equivalent_object_is_not_canonical` (registry),
  `test_raw_proof_object_never_produced_by_authenticator_alone` (proof).
- **public digest recomputation**: `test_public_digest_recomputation_
  alone_is_not_authority` (presentation) — proves a self-consistent
  recomputed outer digest still fails the independent
  attestation-object-binding check.
- **caller-constructed equivalent object**: `test_caller_cannot_
  construct_lifecycle_event_directly_and_have_it_accepted` (lifecycle) —
  documents that direct-filesystem construction bypassing
  `open_challenge` is unreachable from any production caller, since it
  is the only writer and enforces the genesis antecedent.

None of these produce accepted trusted state in any store.

## 40. No-effect evidence

```
runtime subprocess = 0
network = 0
provider calls = 0
credential reads = 0
hardware calls = 0
Runtime Enforcement calls = 0
Shell Gate calls = 0
```

Confirmed by source grep (no `subprocess`/`socket`/`http`/`urllib`/`hid`/
`usb`/`ctap` reference in any new module) and by the import-side-effect
check (§33). No new module imports `runtime_enforcement*` or
`shell_gate*`.

## 41. Compatibility

- **Dry-runtime**: `tests/test_session_bootstrap_dry_runtime_3s2.py`
  (part of the 366-test PB/dry-runtime slice, §44) — all pass.
- **PB**: `tests/test_permission_broker_foundation.py`,
  `tests/test_permission_broker.py`,
  `tests/test_permission_broker_policy_rule_framework.py` — all pass.
- **runtime_authority/HATP**: `tests/test_runtime_authority_*.py` (341
  tests across 7 files), `tests/test_hatp_bootstrap_foundation.py`,
  `tests/test_hatp_canonical_serialization.py` (55 tests) — all pass.

## 42. Regression attribution

`fast_green` (`python -m pytest -m "fast_green" -n auto`) was run twice:
once as a `git stash push -u` baseline (no phase changes) and once
against this phase's candidate tree, per the safe partitioned-comparison
discipline the phase prompt requires (no custom process-group tooling
invented).

```
baseline:  341 failed, 8816 passed, 5 skipped, 9 errors
candidate: 356 failed, 8801 passed, 5 skipped, 9 errors
delta:      +15 failed,  -15 passed,  0 skipped,  0 errors
```

`diff` of the sorted `FAILED` line lists shows the delta is **exactly**
15 tests, all of the form "no `src/pcae` file is dirty in the working
tree" / "git status touches no `src/pcae`/contract file" self-checks
belonging to fifteen unrelated historical phases (149O.14, 1G, 20A, 20B,
20C, 20D, 20D.1, 20E, 20H, 20K, 20K.1, 20L.1, 20L.7D.9, 20L.7D.10,
20L.7E) — literal `git status`/`git diff` scanners that fail on **any**
new file anywhere under `src/pcae/core`, not specifically on HPAC
content. This is the "historical self-check" attribution category the
phase prompt names; it is pre-existing repo debt (any future phase
adding any `src/pcae` file trips these same fifteen checks), not a
functional regression in the code any of those fifteen tests actually
exercises. The 9 errors are identical, same file
(`test_phase_149o_20e_hmic_v1_2_hbdc_bound_contract_identity_
independent_verification.py`, a scratch-tree fixture-count issue),
in both baseline and candidate — environment/test-infrastructure,
unrelated to this phase.

**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS: 0.**

Every new test lives in its own new file (six files, zero shared/
pre-existing test files edited), per plan §51's collision-avoidance
recommendation.

## 43. Contract integrity

`git status --short` and `git diff --stat` show zero changes under
`docs/contracts/`. All six verified contracts remain byte-identical
through this phase.

## 44. Findings

No genuine contract ambiguity or contradiction was encountered requiring
a STOP. Two implementation-level design decisions were made where the
contract left an evidence-shape choice open (both consistent with plan
§35/§6, neither a contract deviation):

1. `HPAC_PROTECTED_ROOT` filesystem layout: `<root>/principals/
   principal-registry.json`, `<root>/presentations/v2/<id>/presentation.json`,
   `<root>/presentation-mechanisms/v2/<id>/descriptor.json`, `<root>/proofs/
   v2/<id>/{proof.json,lifecycle/NNNN.json,consumption.json}` — directly
   transcribed from the contract's own explicit path citations
   (HPAC-REQ-053/090/093/094/098), not invented.
2. `hpac_foundation.py` as a ninth module beyond plan §34's eight-file
   list, justified by phase-prompt item 9's "bounded supporting
   validators/helpers" allowance (§6/§44 above) to avoid duplicating
   atomic-write/symlink/ID-generation code six times.

## 45. Foundation verdict

```
HumanPrincipalRegistry model/store:              IMPLEMENTED
TrustedApprovalPresentationEvidence model/store:  IMPLEMENTED
HumanAuthenticationProof model/store:             IMPLEMENTED
HPAC lifecycle:                                   IMPLEMENTED
deterministic presentation mechanism:             IMPLEMENTED / NON-REAL
deterministic authenticator:                      IMPLEMENTED / NON-REAL
public-digest-as-trust:                           ABSENT
canonical-store trust:                            EXPLICIT
hardware:                                         NOT TOUCHED
real authentication:                              NOT IMPLEMENTED
real presentation:                                NOT IMPLEMENTED
PB integration:                                   NOT PERFORMED
B1/B7/N1/N2 production repair:                    NOT PERFORMED
runtime:                                          Observed / observe / unavailable
```

## 46. Recommended next phase

**149O.20L.7O.3W.1R.2B.1R.1.1R.3.1 — Independent Verification of
Canonical Human-Principal, Protected-Presentation, and HPAC
Proof-Lifecycle Foundation.** This phase does not self-certify. Do not
proceed directly to Layer 3-5 (verifier, B1/B7/N1/N2 repair, real FIDO2,
real presentation UI).

## 47. Human decision required

A human MUST authorize 149O.20L.7O.3W.1R.2B.1R.1.1R.3.1 (independent
verification) before any further layer is implemented. In particular the
human should confirm: (a) the `hpac_foundation.py` ninth-module addition
(§44 item 2) is an acceptable, non-scope-expanding design choice; (b) the
honest "structural-only, not cryptographic" boundary on presentation
attestation (§14) is acceptable for this foundation phase; and (c) the
`ProtectedAdminCapability` non-production marker (§10) is an acceptable
stand-in until the real ceremony (deferred to Phase 5/6+) is authorized.

---

### Matrix A — Implemented components

| Component | Contract owner | Production/test | Real-runtime eligible? |
|---|---|---|---|
| `PrincipalRecord`/`CredentialRecord` | HPAC-001 §4-5 | Production | N/A (data model) |
| `HumanPrincipalRegistryStore` | HPAC-001 §5,7-9,21-22 | Production | N/A (store; mutation gated by non-production marker) |
| `HumanAuthenticator` Protocol | HPAC-001 §10-11 | Production (interface) | N/A |
| `DeterministicTestHumanAuthenticator` | HPAC-001 §10 (plan §11) | Test fixture | No — structurally excluded (`mechanism_id`, `SIMULATION_ONLY`) |
| `CanonicalRuntimeApprovalSubject` | HPAC-001 §38 | Production | N/A |
| `ProtectedApprovalPresentationMechanism` Protocol | HPAC-001 §39.1 (plan §12) | Production (interface) | N/A |
| `PresentationMechanismDescriptor`+store | HPAC-001 §39.1 | Production | N/A (installation gated) |
| `TrustedApprovalPresentationEvidence`+store | HPAC-001 §39.2-39.3 | Production | No (structural-only trust, §14 above) |
| `DeterministicTestPresentationMechanism` | HPAC-001 §39 (plan §13) | Test fixture | No — structurally excluded |
| `HumanAuthenticationProof`+store | HPAC-001 §17 | Production | No (verifier does not exist yet) |
| `LifecycleEvent`+`HPACLifecycleStore` | HPAC-001 §40 | Production | No (genesis-gated, no verifier) |
| `RuntimeInvocationAuthorityConsumption`+store | HPAC-001 §41 | Production (inert) | No — unreachable from any dispatch path |

### Matrix B — Stores

| Store | Scope | Writer | Reader | Trust root | Atomicity |
|---|---|---|---|---|---|
| `HumanPrincipalRegistryStore` | Deployment/user-scoped (`resolve_hpac_protected_root()`) | `ProtectedAdminCapability`-gated | Any caller | Fixed platform path, zero repo input | Whole-document atomic replace + read-back |
| `TrustedApprovalPresentationStore` | Deployment-scoped | `create()` only | `resolve_structural()` | Create-only exclusivity | `O_CREAT\|O_EXCL` create-only, read-back |
| `HumanAuthenticationProofStore` | Deployment-scoped | `create()` only | `resolve()` | Create-only exclusivity | `O_CREAT\|O_EXCL` create-only, read-back |
| `HPACLifecycleStore` | Deployment-scoped, per `proof_id` | Five narrow transition methods only | `resolve_chain()` | Genesis gated by resolved presentation | Per-event `O_CREAT\|O_EXCL`, hash-chained |
| `RuntimeInvocationAuthorityConsumptionStore` | Deployment-scoped, per `proof_id` | `create()` only (inert, test-reachable only) | `resolve()` | Create-only exclusivity | `O_CREAT\|O_EXCL`, single atomic commit |

### Matrix C — Deterministic mechanisms

| Mechanism | Purpose | UP | UV | Presentation trust | Real eligible? |
|---|---|---|---|---|---|
| `hpac.deterministic.test-only.v1` | Authenticator fixture | Parameterizable | Parameterizable | N/A | No |
| `hpac.deterministic.presentation.test-only.v1` | Presentation fixture | N/A | N/A | Structurally valid or one of four injectable faults | No |

### Matrix D — Trust-forgery tests

| Attack | Required result | Observed |
|---|---|---|
| `dataclasses.replace()` forgery (registry/presentation/proof/authenticator) | Store/resolve reflects only what was actually written | PASS (4 tests) |
| Copied trusted-looking record (registry/proof) | Never resolves unless explicitly created via the store | PASS (2 tests) |
| Public digest recomputation (presentation) | Self-consistent outer digest still fails independent attestation binding | PASS (1 test) |
| Caller-constructed equivalent object (lifecycle) | Unreachable from any production caller; documented, not merely asserted | PASS (1 test) |

### Matrix E — Requirement coverage

| Requirement (representative) | Component | Test | Status |
|---|---|---|---|
| HPAC-REQ-007-011 (principal identity) | `PrincipalRecord` | `test_valid_principal_record_enrolls_and_resolves` | DONE |
| HPAC-REQ-012-017 (registry shape/atomicity) | `HumanPrincipalRegistryStore` | `test_malformed_record_unknown_field_rejected`, `test_duplicate_principal_id_rejected` | DONE |
| HPAC-REQ-021/022/079/080 (scope/trust root) | `resolve_hpac_protected_root` | `test_registry_path_resolution_ignores_env_and_cwd`, `test_repository_path_substitution_is_structurally_impossible` | DONE |
| HPAC-REQ-026/027 (enrollment preview/guard) | `HumanPrincipalRegistryStore` | `test_enroll_credential_against_missing_principal_fails_closed` | DONE |
| HPAC-REQ-030/031 (credential multiplicity) | `HumanPrincipalRegistryStore` | `test_credential_mapping_one_principal_many_credentials` | DONE |
| HPAC-REQ-032-035 (authenticator interface, non-collapse) | `HumanAuthenticator` | Protocol structural conformance assertion | DONE |
| HPAC-REQ-052/053 (proof structure/storage) | `HumanAuthenticationProof`+store | `test_valid_deterministic_proof_creates_and_resolves` | DONE |
| HPAC-REQ-059/060 (assurance model, UP/UV floor) | `AssuranceLevel`, deterministic authenticator | `test_up_and_uv_are_independently_settable` | DONE |
| HPAC-REQ-061/062 (monotonic revocation) | `HumanPrincipalRegistryStore` | `test_revoked_principal_is_monotonic_and_idempotent` | DONE |
| HPAC-REQ-089 (canonical subject) | `CanonicalRuntimeApprovalSubject` | Used by all presentation/lifecycle tests | DONE |
| HPAC-REQ-090-093 (presentation mechanism/evidence/store) | `approval_presentation.py` | 17 tests in `test_hpac_approval_presentation.py` | DONE |
| HPAC-REQ-094-096 (lifecycle record form, genesis) | `hpac_lifecycle.py` | 15 tests in `test_hpac_lifecycle.py` | DONE |
| HPAC-REQ-097 (Gate-5 binding) | `HPACLifecycleStore.bind_gate5` | `test_bind_gate5_idempotent_same_binding`, `test_bind_gate5_cross_binding_rejected` | DONE (store-level; no real Gate-5 caller — deferred to Phase 5) |
| HPAC-REQ-098-100 (Gate-9 consumption) | `runtime_invocation_authority_consumption.py` | 7 tests in `test_hpac_authority_consumption.py` | DONE (inert primitives only — no gate-9 wiring, deferred to Phase 5) |
| HPAC-REQ-005/006 (non-authority rule, forbidden shortcuts) | All stores | Matrix D's four trust-forgery tests | DONE |
| HPAC-REQ-018-020, 084 (HATP separation) | `hpac_foundation.resolve_hpac_protected_root`, distinct namespace | Distinct path constants; zero import of `hatp_bootstrap`/`hatp_providers`/`hatp_fido2_provider` | DONE |
| HPAC-REQ-023/024/028/029 (real ceremony) | N/A | N/A | NOT IMPLEMENTED (deferred to Phase 5/6, honestly stated §10) |
| HPAC-REQ-039-046, 082-083 (real FIDO2 mechanism) | N/A | N/A | NOT IMPLEMENTED (deferred to Phase 3) |
| HPAC-REQ-086 (same-user-agent resistance) | N/A | N/A | NOT IMPLEMENTED (deferred to Phase 3.1, §29 above) |

No requirement assigned to this phase's slice (plan §37/§52 "Phase 1")
was left unmapped.
