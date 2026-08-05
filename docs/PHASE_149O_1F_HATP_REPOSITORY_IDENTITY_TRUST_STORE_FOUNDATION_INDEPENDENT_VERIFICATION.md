# Phase 149O.1F — HATP Repository Identity + Trust-Store Foundation Independent Verification

## Methodology

Independent adversarial reconstruction of the Wave 1 (`repository_identity.py`)
and Wave 2 (`hatp_bootstrap.py`) foundation implemented by Phase 149O.1E.
No 149O.1E test file was modified. No production source
(`src/pcae/**`) was modified by this phase — confirmed empty via
`git diff --name-only HEAD -- src/pcae/`. HATP-001 v1.0 was not touched —
confirmed empty via `git diff --name-only HEAD -- docs/contracts/`.

Rather than trusting the 149O.1E report's claimed coverage, source was
read directly, the Wave-1/Wave-2 requirement span was independently
re-derived from HATP-001 + the 149O.1D plan, and a new adversarial suite
(`tests/test_phase_149o_1f_hatp_repository_identity_trust_store_foundation_independent_verification.py`,
22 tests) was authored to attack the actual implementation rather than
re-assert its own unit tests.

## Production diff reconstruction (`a278cd93..21107ade`)

| File | Classification |
|---|---|
| `src/pcae/core/repository_identity.py` (new) | CRI (Layer 1) |
| `src/pcae/core/hatp_bootstrap.py` (new) | BOOTSTRAP_MODEL / TRUST_STORE / DEPLOYMENT_BINDING / READINESS |
| `src/pcae/commands/init.py` | CRI_INIT |
| `src/pcae/core/templates.py` | CRI_GITIGNORE (adds `repository-identity.json` to `.pcae/.gitignore`; no other change) |
| `.pcae/.gitignore` | CRI_GITIGNORE (this repo's own local file, mirrors the template) |
| `tests/conftest.py` | TEST_SUPPORT (registers the two new deterministic test modules as `fast_green`) |
| `tests/test_repository_identity.py`, `tests/test_hatp_bootstrap_foundation.py`, `tests/test_phase_149o_1e_*.py` | TEST_SUPPORT |

No `UNRELATED` hunk found. `pyproject.toml`/lockfile diff for the same
range is empty — no dependency was added.

## Wave requirement reconstruction

Independently re-derived from HATP-001 (`HATP-REQ-046..051`, `-052..066`,
`-030..045`, `-086..089`, `-107`) and the 149O.1D plan's Wave 1/2
boundary. All Wave-1/2 requirements identified have an implementation
owner in the diff above; none identified as required-but-unowned.

## Repository identity model (as implemented, not as planned)

`RepositoryIdentity(schema_version: int, repository_instance_id: str,
created_at: str)`. Closed field set (`_REQUIRED_FIELDS`), strict
validation (`validate_repository_identity_document`): unknown fields,
missing fields, non-UUID4 `repository_instance_id`, unsupported
`schema_version`, or a non-timezone-aware `created_at` all raise
`RepositoryIdentityMalformedError`. Storage: `.pcae/repository-identity.json`,
atomic write (temp file + `fsync` + `os.replace`), symlink write refused
both before and after the write (`_reject_symlink` called twice around
`_write_atomic`).

- **ID generation**: `uuid.uuid4()` — random, not derived from path, git
  remote, or hostname. Verified by direct inspection of
  `_generate_repository_identity`.
- **No caller-controlled ID parameter** exists on `ensure_repository_identity`
  or `read_repository_identity` (verified by `inspect.signature`,
  `test_no_production_api_accepts_a_caller_supplied_id`).
- **Idempotent**: existing valid identity is returned unchanged by
  `ensure_repository_identity`; no regeneration path when valid.
- **Malformed is never auto-healed**: `ensure_repository_identity` calls
  `read_repository_identity` first and re-raises
  `RepositoryIdentityMalformedError` rather than falling through to
  generation — confirmed in the 149O.1E suite
  (`test_missing_and_malformed_are_distinct_outcomes`) and not
  contradicted by any code path.
- **Symlink write attack**: `_reject_symlink` runs both before opening the
  temp file and immediately before `os.replace`; an attacker-planted
  symlink at the target path is refused, not followed.
- **Gitignored**: `git check-ignore -v .pcae/repository-identity.json`
  resolves against `.pcae/.gitignore:4`, confirmed directly against this
  repository's own committed ignore file, not inferred from comments
  (`test_clone_does_not_propagate_committed_identity`).
- **Templates carry no static/hardcoded identity**: `templates.py`'s diff
  is exactly one `.gitignore` line; no `repository_instance_id` or
  `uuid.UUID(` literal exists in that module
  (`test_no_static_or_hardcoded_identity_in_templates`).
- **ID regeneration after deletion**: an ordinary caller can delete the
  identity file and re-init to receive a new ID. This is allowed — the
  identity is non-authoritative by itself — but the new ID has no
  enrollment matching the old ID's binding
  (`test_id_regeneration_after_deletion_loses_any_enrollment_match`).
- **ID theft without root match**: copying a known ID into a different
  repository, or a different root, leaves the copy unauthorized against
  a real binding
  (`test_repository_id_theft_without_root_match_remains_unauthorized`,
  and the 149O.1E suite's `test_full_copy_attack_no_matching_deployment`).
- **Worktree**: reproduced independently — a real `git worktree add`
  receives an `ensure_repository_identity` result distinct from the main
  tree's, because `.pcae/` is an ordinary gitignored working-tree file,
  not shared object-database state (149O.1E's own
  `test_worktree_receives_distinct_repository_identity`, re-verified by
  reading the implementation and confirming no worktree-common-dir
  special-casing exists in `repository_identity.py`).
- **No authority logic anywhere**: `grep`-level search of both new
  modules for `if repository_id`/`trusted =`-shaped logic found none;
  `repository_identity.py` has zero import of `hatp_bootstrap`,
  `rollback_approval_evidence`, `permission_broker*`, or `agent*`.

## Trust-store model (as implemented)

`HATPTrustStore` — read-only lookup façade. Registry document: JSON with
top-level `registry_version`, `principals[]`, `signers[]`,
`deployment_bindings[]`, `authorities[]`; all strictly validated, closed
field sets, duplicate keys rejected outright
(`_parse_registry_document` raises on any repeated
principal_id/signer_key_id/repository_id/(principal_id,repository_id)
key — **not** resolved by mtime, file order, or "last wins"; confirmed
by source inspection, `grep`-checked absence of `st_mtime`/`getmtime`/
`sorted(files`/`max(files` in the module, and independently reproduced
for signer records in
`test_duplicate_signer_records_rejected_not_silently_merged`).

`resolve_deployment_authorization` requires **both** `repository_id`
(Layer 1) and `canonical_deployment_root` (Layer 2) to match an
`active` (non-revoked) binding — same-ID/wrong-root, same-root/wrong-ID,
and revoked bindings all independently reproduced to return `None`.
`resolve_canonical_deployment_root` canonicalizes via
`Path.normpath` + `Path.resolve(strict=True)`; `.`/`..` aliases and a
symlinked path to the same physical directory canonicalize identically
(`test_dot_and_dotdot_aliases_canonicalize_identically`, mirrors
149O.1E's `test_canonical_root_resolves_symlink`).

No public mutation method (`enroll`/`grant`/`revoke`/`rotate`/`write`/
`save`) exists on `HATPTrustStore`; the public symbol set was
independently enumerated
(`test_public_api_enumeration_has_no_unexpected_authority_mutation`) and
contains only the fields and read accessors documented above — no
undisclosed authority-mutation surface.

## Production trust-store path resolution — BLOCKING FINDING

`HATPTrustStore.production()` → `_default_production_trust_root()` →
`Path.home() / ".pcae-hatp" / "trust-store"`.

The module's own docstring and the 149O.1E report both assert: *"the
production trust-store location is never caller-selectable: no
constructor parameter, CLI flag, or environment variable accepted by
`HATPTrustStore.production()`"*, and the 149O.1E adversarial test
(`test_production_ignores_environment_overrides`) checked four
HATP-specific guessed variable names (`PCAE_HATP_TRUST_STORE`,
`HATP_TRUST_STORE`, `HATP_TRUSTED_KEY`, `PCAE_HATP_TRUSTED_KEY`) and
found no effect — correctly, since none of those are consulted.

`Path.home()` on POSIX, however, is not caller-independent: it consults
`$HOME` (via `os.path.expanduser`). This phase directly verified:

```
os.environ['HOME'] = '/tmp/attacker-controlled-home'
Path.home()  # -> PosixPath('/tmp/attacker-controlled-home')
```

and reproduced the full consequence in
`test_home_environment_variable_redirects_production_trust_store` and
`test_home_redirection_enables_self_authored_deployment_authorization`:
an ordinary process-environment mutation — something any autonomous
agent's own process can always perform, no privilege escalation
required — relocates `HATPTrustStore.production()`'s root to an
attacker-chosen directory. The agent then authors its own
`registry.json` there containing a self-declared `active`
`deployment_binding` for its own (freshly, legitimately generated)
`repository_instance_id` and its own canonical root, and
`resolve_deployment_authorization` returns a real, non-`None`
`DeploymentBinding` — structurally indistinguishable from a
legitimately admin-provisioned one.

`inspect_bootstrap_environment` on that same redirected store still
correctly reports `UNSAFE_CONFIGURATION` /
`agent_and_admin_share_os_principal` (the same-user check is sound and
unconditional on its own terms) — but **`resolve_deployment_authorization`
does not consult `environment_status()`/`inspect_bootstrap_environment`
at all**, and no Wave-1/2 API forces a future caller to compose the two.
Today, with no Wave 3–7 consumer wired to `approval_present`, this alone
produces no trusted HATP approval anywhere in production. But it means
the foundational "trust anchor lives outside repo-writable, agent-
controlled state" guarantee — the property every later wave is meant to
build on — does not actually hold as implemented: the *effective*
non-redirectability of `HATPTrustStore.production()`'s root depends
entirely on the deployment process's `$HOME` being itself
administratively protected, a precondition never checked, declared, or
enforced anywhere in the Wave-1/2 code or its own claimed invariants.

`XDG_CONFIG_HOME`/`XDG_DATA_HOME` are not consulted at all (clean
negative control,
`test_xdg_variables_have_no_effect_observation`), and current working
directory has no effect
(`test_cwd_has_no_effect_on_production_path`) — the exposure is
specific to `$HOME`.

## Readiness / same-user / root reconstruction

Live, independent reproduction on this repository's actual deployment:
`inspect_bootstrap_environment` against `~/.pcae-hatp/trust-store`
(present or absent) never returns `READY`; under every
agent-controllable permission mode (`0o700`, `0o600`, `0o400`, `0o755`)
applied to a test-owned store, the same-user check still fires and
`READY` is never returned. `os.getuid() == 0` was probed via
monkeypatch (cannot run as real root in this environment); the
same-user branch is keyed off `store_stat.st_uid == current_uid`, so a
root agent against a root-owned store still reports
`UNSAFE_CONFIGURATION` — the check is genuinely OS-principal-based, not
merely non-zero-UID-based. No sudo-capability blind spot beyond what the
149O.1D plan already disclosed as a deployment-verification obligation
deferred to Wave 7; this phase does not claim to close it.

## No premature activation

- No `approval_present`, `HATP_TRUSTED_OPERATIONAL`, or `verify_*` symbol
  exists in either module (independently re-enumerated via `dir()`,
  filtered to module-native definitions —
  `test_public_api_enumeration_has_no_unexpected_authority_mutation`,
  `test_no_proof_or_verifier_symbols_exist_yet`).
- No wildcard/global authority fallback in `hatp_bootstrap.py`
  (`test_no_wildcard_or_global_fallback_in_source`).
- `rollback_approval_evidence.py`, `permission_broker.py`,
  `permission_broker_foundation.py`, `mutation_permission.py`,
  `agent.py`, `commands/agent.py` are byte-identical to
  `a278cd93` (pre-149O.1B.3 freeze) —
  `test_rae_permission_broker_agent_still_byte_unchanged_since_freeze`.
- `repository_identity` also appears, unrelated, as a pre-existing plain
  string field name in `cltr`/`cltr_prototype`/`repository_intelligence`
  canonical-report schemas (a phase-identity string, nothing to do with
  HATP). Confirmed via `grep` that none of those modules import
  `pcae.core.repository_identity` — a naming collision, not a
  cross-module authority leak
  (`test_repository_identity_string_elsewhere_in_codebase_is_unrelated_namesake`).

## Regressions

- `tests/test_repository_identity.py`, `tests/test_hatp_bootstrap_foundation.py`,
  `tests/test_phase_149o_1e_hatp_repository_identity_trust_store_foundation.py`:
  **51 passed** (matches 149O.1E's claimed entering result exactly).
- `tests/test_phase_149o_1c_human_approval_trusted_provenance_contract_independent_verification.py`:
  **95 passed**.
- `tests/test_phase_149o_1d_human_approval_trusted_provenance_implementation_plan.py`:
  **32 passed**.
- `tests/test_permission_broker*.py tests/test_rollback_approval_evidence_*.py
  tests/test_phase_149j*.py tests/test_phase_149m*.py tests/test_phase_149n*.py
  tests/test_phase_149o*.py`: **1243 passed, 4 failed**. The 4 failures
  are `test_phase_149o_rollback_approval_evidence_canonical_provenance_hardening_independent_verification.py`'s
  B-149O-1..4 reproductions — expected, pre-existing, and unrelated to
  this phase's or 149O.1E's diff (`rollback_approval_evidence.py` is
  byte-unchanged since the freeze). This is the same still-open-findings
  result the 149O.1E report itself recorded.
- New independent suite: **22 passed** (this phase's own).
- Fast Green (`python -m pytest -m fast_green -n auto -q`): **4431
  passed** — identical to the entering baseline reported by 149O.1E; no
  new fast_green tests were registered by this verification phase, no
  regression.

## Governance validation

`pcae health` — healthy. `pcae check` — passed. `pcae status coherence`
— coherent. `pcae doctor task-memory` — clean. `pcae push check` —
clean (`nothing_to_push`; branch is ahead-by-0 of `origin/main` at time
of writing, before this phase's own commit). `pcae runtime inspect` —
`Observed` / `observe` / `unavailable`, unchanged before and after.
`pcae notify status` — Telegram configured/enabled.

## Findings

### BLOCKING

1. **HOME-based production trust-store redirection.** `HATPTrustStore.production()`'s
   claimed environment-independence does not hold: `$HOME` (an ordinary,
   agent-controllable process environment variable) fully determines the
   resolved trust-store root via `Path.home()`. An agent that controls
   its own `HOME` can redirect the "authoritative" store to a directory
   it owns and author a self-consistent, structurally valid
   `deployment_binding` that `resolve_deployment_authorization` returns
   as a real match. No Wave-1/2 API composes this lookup with the
   same-user readiness check, so nothing in the current foundation
   itself prevents a future consumer from trusting a `HOME`-redirected
   binding. This directly matches the verification principle's named
   BLOCKING criterion: *"If HOME/XDG/environment can redirect the
   authoritative production trust store."*
   **Recommend**: a narrow 149O.1F.1 repair phase that hardens
   `_default_production_trust_root()` against `$HOME` redirection (e.g.
   resolving the deployment admin's home directory via
   `pwd`/`os.path.expanduser` against a fixed, non-environment-derived
   UID such as the store-creating principal recorded at first
   provisioning, or documenting and enforcing an explicit
   process-environment integrity precondition before `production()` is
   ever called) before Wave 3 proceeds. Do not repair in this phase per
   the 149O.1F charter.

### NON-BLOCKING

None identified beyond the observations below that do not weaken a
load-bearing trust property.

### OBSERVATION

1. `resolve_deployment_authorization` and `environment_status()` are
   independent calls; a future Wave 4+ verifier must explicitly compose
   both (readiness *and* binding match) rather than treating a resolved
   binding as sufficient on its own — worth stating explicitly as a Wave
   3/4 design constraint given finding 1 above.
2. Filesystem TOCTOU between a permission/symlink check and the
   subsequent read (`_load_registry`, `read_repository_identity`) is
   theoretically possible under local, same-machine adversary
   conditions; bounded by ordinary filesystem race windows, not
   practically demonstrated here, and not overclaimed as race-free.
3. `repository_identity` is also used, unrelated, as a plain string
   field name elsewhere in the codebase (`cltr`/`cltr_prototype`); purely
   a naming coincidence, already confirmed not to be a cross-module
   import.

### DEFERRED

None beyond what 149O.1D/149O.1E already deferred (Waves 3–7, Class-B OS
provisioning).

## B-149O status

`B-149O-1` through `B-149O-4` remain OPEN, reproduced identically by the
regression run above; `rollback_approval_evidence.py` is byte-unchanged
by this phase and by 149O.1E.

## F1/F2 status

`F-149O.1C-1` remains pending actual Wave-3 proof-schema implementation
(closed only at plan-disposition level). `F-149O.1C-2` remains a
retained editorial observation (117 remains the authoritative
requirement count throughout this phase's own artifacts).

## Verification verdict

**NOT VERIFIED — BLOCKING HATP FOUNDATION FINDINGS**

The BLOCKING finding above (`$HOME`-based production trust-store
redirection) falls squarely within the verification principle's named
BLOCKING criterion for environment-controlled redirection of the
authoritative trust store. Every other attacked property — caller-
controlled ID injection, malformed-identity auto-heal, symlink writes,
static template IDs, clone/worktree/copy/move identity propagation,
same-ID-wrong-root and same-root-wrong-ID matching, canonical-path
aliasing, duplicate/ordering ambiguity, wildcard fallback, same-user and
root-agent readiness, public mutation-API absence, activation-symbol
absence, and RAE/Permission-Broker/Agent/contract byte-boundaries — held
under independent attack with no counterexample found.

## Foundation readiness

**FOUNDATION SOFTWARE: NOT READY** pending the narrow trust-store path
hardening repair identified above. All other Wave-1/2 properties
independently verified sound.

## Production readiness

**HATP PRODUCTION: NOT READY.** Waves 3–7 (proof schema, canonical proof
serialization, verifier, hardware/FIDO2/PIV providers, human-approval
and admin-enrollment CLIs, RAE integration, Class-B OS deployment
provisioning) remain unimplemented regardless of this phase's verdict.

## Confirmations

HATP-001 v1.0 remained byte-unchanged. No production source was modified
by Phase 149O.1F. Wave 1 and Wave 2 were independently reconstructed
rather than accepted from 149O.1E's summary. No HATP proof schema/model,
canonical proof serialization, proof verifier, real FIDO2 provider, real
PIV provider, or human-presence signer was implemented. No Class-B OS
security boundary was provisioned. Current HATP deployment remains NOT
READY. No production HATP proof can become VALID from Wave-1/2 state. No
production rollback request consumes HATP to derive
`approval_present=True`. `B-149O-1` through `B-149O-4` remain OPEN.
`F-149O.1C-1` remains pending actual Wave-3 proof-schema implementation
despite being closed at plan-disposition level. `F-149O.1C-2` remains
editorial debt only. No RAE production integration, no AG3 Permission
Broker integration, and no AG5 Permission Broker integration were
implemented. No rollback execution behavior changed. RAE-001 v1.0,
RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001 v1.0, and CHGR-001 remain
unchanged. IWC confirmation remains distinct from approval. AESIC/AEM
remain disclosure-only. No illegal CHGR/TAM composition was introduced.
No POL-001..012 meaning was changed; no POL-013+ was added. TK1/TK2/TK3
remain deferred. No Runtime Enforcement behavior changed. No Prompt
Generation, Prompt Dispatch, or agent invocation capability was
implemented. Runtime remains Observed, maximum capability remains
observe, and execution availability remains unavailable.

## Recommended next phase

Because a BLOCKING finding was identified, per the 149O.1F charter this
phase does not recommend proceeding to Wave 3
(`149O.1G — HATP Proof Models + Canonical Serialization Implementation`).

**Recommended next phase: 149O.1F.1 — HATP Production Trust-Store Path
Hardening (narrow repair)**, scoped to `_default_production_trust_root()`
in `src/pcae/core/hatp_bootstrap.py` only: eliminate or bind down the
`$HOME`-environment dependency so that `HATPTrustStore.production()`'s
resolved root is genuinely independent of any value the agent's own
process environment can set, and add a regression test asserting that
property directly. Wave 3 (149O.1G) should follow only after that
repair is independently re-verified.
