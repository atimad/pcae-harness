# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-CALLER-INTEGRATION-ARCH)

**Caller / Client Integration Architecture for Privileged Helper Consumption.**

Architecture-only. No production caller code, helper code, replay code,
contract, schema, or dependency changed. No macOS implementation. No
packaging/install/live-host mutation. No real ceremony.

## 0. Governance / phase identity

- Predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
  (alias `N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN`), COMPLETE, commit
  `102c91e3` (pushed as of `3be2b318`). Confirmed via `PROJECT_STATUS.md`,
  `.pcae/phase-completion-metadata.json` (`status: completed`), the
  canonical predecessor Phase Report, and governed task state, all
  agreeing.
- CPIPC validation, independently re-derived via `pcae.core.phase_id`
  (`parse`/`is_valid`/`normalize`/`same_series`/`same_branch`/`compare`),
  not trusted from the authorization prompt's precomputed successor text:
  the successor is the predecessor with exactly one appended `.1`
  segment (60 → 61 subphase segments), `is_valid` True, same series `149`
  / branch `O`, `compare` = less (strict forward ordering), `git log
  --all -F --grep` returned no collision at entry, no conflicting active
  governed phase (`pcae health`: healthy, agent lock held by
  `claude-local`, no other phase in progress).
- Entry state: branch `main`, HEAD == `origin/main` == `3be2b318`,
  `origin/main..HEAD` = 0, tree clean.
- Contract baseline captured before any work: HPAC-PAWA-001 v2.0
  (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`),
  HPAC-PAWA-HELPER-001 v1.0
  (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`),
  HPAC-PPA-001 v2.0
  (`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`) —
  all three byte-unchanged at phase end (`git diff origin/main -- docs/contracts/`
  empty).

## 1. Purpose

Design (architecture only) the caller/client integration that will
eventually migrate existing in-process HPAC privileged-authority callers
onto the independently verified out-of-process helper
(HPAC-PAWA-HELPER/1.0) path, without implementing any of it. This phase
answers the questions in Sections 3–52 of the authorization prompt and
produces the canonical deliverables of its Section 50.

## 2. Method

The bulk of the source inventory and architecture drafting (Sections
4–13, 15–52 below) was performed by a bounded delegated research worker
(§63 of the authorization prompt: read-only, no repository mutation, no
commit/push/task authority). The primary operator (this session)
independently re-verified every load-bearing factual claim directly
against source before accepting it — see §3 (Independent Verification
Log). No claim in this report rests solely on the delegated worker's
say-so.

The delegated worker's full research document is preserved at
`/tmp/n16_5_caller_integration_arch_research.md` (not a repository path;
ephemeral scratch artifact, not committed — its content is fully
reproduced/condensed into this canonical report).

## 3. Independent verification log (primary operator, direct source)

The primary operator independently re-executed the following checks
against live source, not the delegated worker's report:

1. `grep -rliE "hpac|pawa|rhamp|gate5" src/pcae/cltr src/pcae/commands
   src/pcae/governance src/pcae/interactive_workflow src/pcae/cli.py` →
   **zero matches** — confirmed there are no orchestration-layer callers
   of the HPAC/PAWA subsystem today.
2. `ls scripts/ | grep -i hpac` → confirmed exactly the four standalone
   admin launchers claimed (`hpac_certification_admin.py`,
   `hpac_principal_admin.py`, `hpac_protected_presentation_admin.py`,
   `hpac_protected_root_admin.py`).
3. Read `src/pcae/core/hpac_protected_admin_writer.py` function/symbol
   list directly (`grep -n "^def \|_CONSUMERS"`) — confirmed the four
   factory functions (`production_writer`, `certification_writer`,
   `recognized_certification_read_authority`,
   `mint_protected_presentation_evidence_writer`) and the three consumer
   allowlists (`AUTHORIZED_FACTORY_CONSUMERS`,
   `CERTIFICATION_FACTORY_CONSUMERS`, `READ_AUTHORITY_CONSUMERS`) exist
   exactly as claimed.
4. `grep -rn "certification_writer(\|recognized_certification_read_authority(\|mint_protected_presentation_evidence_writer(\|production_writer("` across `src/` and `scripts/` — confirmed
   the exact call-site inventory in §4.2–§4.6 below, including that
   `production_writer` has exactly the two claimed callers
   (`hpac_rhamp_enrollment.py`, `hpac_protected_presentation_admin.py`)
   and `mint_protected_presentation_evidence_writer` has exactly one
   (`protected_presentation.py`).
5. `grep -rn "hpac_certification_coordinator" src/ scripts/` restricted
   to actual imports/calls (excluding docstrings/comments/allowlist
   string literals) → **zero hits** — independently confirmed
   `hpac_certification_coordinator.py` has no live production caller
   today, which the delegated worker's report also stated.
6. Read `pyproject.toml` lines 50–75 directly — confirmed `packages =
   ["src/pcae"]` and the anchored sdist `include` list omit `scripts/`
   entirely; the four admin launchers are packaged in neither the wheel
   nor the sdist.
7. Read `src/pcae/core/hpac_pawa_helper_protocol.py` lines 40–70 and
   510–522 directly — confirmed the exact 21-value `PAWA_FAILURE_CODES`
   tuple (with its own `assert len(...) == 21` guard) and the exact
   5-value `ReplayOutcome` enum (`FRESH`, `CONSUMED`,
   `DUPLICATE_IN_FLIGHT`, `EXPIRED`, `CONFLICTING`).
8. `grep -n "approved\|human_present\|authenticated"
   src/pcae/core/hpac_pawa_helper_operations.py` — confirmed the exact
   forbidden-key set `{"approved", "verified", "human_present",
   "authenticated"}` in the `presentation_evidence_write` handler,
   matching HPAC-PAWA-HELPER-REQ-071.

No discrepancy was found between the delegated worker's claims and
direct source re-inspection on any of the above. The remaining
architecture content below (design recommendations, migration slices,
threat matrix) is drafting, not verifiable fact, and is presented as
such.

## 4. Current production caller inventory (from direct source)

### 4.0 Top-line finding

There are **no orchestration-layer (CLI/agent-reachable) production
callers of the HPAC/PAWA/RHAMP subsystem at all**. The entire subsystem
lives inside `src/pcae/core/hpac_*.py`, `human_*.py`,
`approval_presentation*.py`, `protected_presentation*.py`,
`runtime_dispatch_gate5.py`/`gate9.py`/`gate10_eligibility.py`,
`runtime_authority.py`, and `human_authenticator_fido2.py` — a
self-contained "core" island — plus four standalone,
non-agent-importable `scripts/hpac_*.py` administration launchers. The
caller inventory below is therefore "which core-module functions
currently obtain privileged authority in-process," since those are
exactly the call sites a future client library replaces.

### 4.1 The four legacy factory functions (`src/pcae/core/hpac_protected_admin_writer.py`)

| # | Factory | Mechanism | Protected effect | Helper op | Role (if `certification_write`) |
|---|---|---|---|---|---|
| 1 | `production_writer(...)` | `_detect_caller_module` + `_verified_production_caller_name` (frame code-object/globals pinning) + `AUTHORIZED_FACTORY_CONSUMERS` allowlist | Mints `ProductionWriterHandle`/`HPACWriterCapability` for the admin-mutation family | `admin_mutation` | n/a |
| 2 | `certification_writer(...)` | same check vs. `CERTIFICATION_FACTORY_CONSUMERS = {"pcae.core.hpac_certification_coordinator"}` | Mints `CertificationWriterHandle` for one of the 5 closed roles | `certification_write` | one of the closed 5 |
| 3 | `recognized_certification_read_authority(...)` | same check, `READ_AUTHORITY_CONSUMERS = CERTIFICATION_FACTORY_CONSUMERS` | Mints `CertificationReadAuthority` for the closed typed read set | `certification_read` (+ `ceremony_entry` hand-off) | n/a |
| 4 | `mint_protected_presentation_evidence_writer(...)` | same check | Mints the sole `HPAC-PRESENTATION-EVIDENCE/2.0` writer | `presentation_evidence_write` | n/a |

All four share `_detect_caller_module`/`_verified_production_caller_name`
— the exact frame-pinning mechanism the predecessor lineage
(N16-5-F5B2R2-IMPL) proved insufficient (`gc.get_objects()`/
`gc.get_referrers()` reach the minted object regardless; `exec()` can
inject a new code object into an already-trusted module's own
`__dict__`). This is precisely the defect HPAC-PAWA-001 v2.0 §33C /
HPAC-PAWA-HELPER-001 exist to replace.

### 4.2 `production_writer` — exactly two callers

| Caller module | Effect | Lifecycle | Migration priority | Old-path disposition |
|---|---|---|---|---|
| `hpac_rhamp_enrollment.py` (~L188, ~L447) | RHAMP-001 principal/credential bootstrap enrollment (real FIDO2 CTAP2 path exists) | production, reachable only from `scripts/hpac_principal_admin.py` | **HIGH** — first real bootstrap path a human operator uses | superseded by `admin_mutation`; removal is a later governed slice, not this one |
| `hpac_protected_presentation_admin.py` (~L114) | presentation-mechanism install/rotate/revoke | production, reachable only from `scripts/hpac_protected_presentation_admin.py` | MEDIUM — infrequent, install-time-only | same disposition |

### 4.3 `certification_writer` / `recognized_certification_read_authority` — exactly one consumer

`hpac_certification_coordinator.py` is the sole authorized consumer of
both (enforced by the two allowlists above). It dispatches per role to:

| Role | Downstream writer module |
|---|---|
| `hpac_challenge_coordinator` | `hpac_lifecycle.py` (genesis writer role) |
| `hpac_assertion_recorder` | `hpac_lifecycle.py` (assertion writer role) via `hpac_rhamp_assertion_verify.py` |
| `human_authentication_proof_verifier` | `human_authentication_proof.py` (proof writer) |
| `hpac_gate5_binder` | `hpac_lifecycle.py` (bound writer role), consumed by `runtime_dispatch_gate5.py` |
| `hpac_rhamp_counter_state_verifier` | `hpac_rhamp_counter_state.py` (counter-state verifier role) |

`hpac_certification_coordinator.py` itself has **no live caller anywhere
in the repository** (independently confirmed, §3.5). `scripts/hpac_certification_admin.py`
exists but today only exposes `describe` and `status` (both read-only);
it does not call `certification_writer`. The real end-to-end
certification ceremony that would invoke the coordinator is deferred to
the not-yet-begun N16-5-FINAL-CERT phase. `hpac_lifecycle_terminator` is
confirmed **not** part of the certification-write role family (matches
§8 of the authorization prompt) — no evidence of any lifecycle-terminal
protected write was found requiring a sixth role; lifecycle termination,
where it exists, is a separate concern from the 5-role certification
family and is out of scope for this phase.

### 4.4 `mint_protected_presentation_evidence_writer` — exactly one caller

`src/pcae/core/protected_presentation.py` (~L646–649), inside the
HPAC-PPA-001 ceremony flow. Per HPAC-PPA-001 v2.0, this call site's
*effect* (minting a presentation-evidence writer) is now specified to
move **inside** the verified presentation helper itself;
`protected_presentation.py` remains the ceremony launcher/mediator but
is no longer the evidence-writer issuer. Migration priority **HIGH**.

### 4.5 Bearer-typed-capability-accepting modules (operation-internal, not separate callers)

`hpac_lifecycle.py`, `human_authentication_proof.py`,
`human_principal_registry.py`, `hpac_rhamp_credential_sidecar.py`,
`hpac_rhamp_counter_state.py`, `approval_presentation.py`,
`protected_presentation_installation.py` all accept an already-minted
`HPACWriterCapability`/`HPACStoreAuthority` as a parameter. None import
the four factories directly — they are downstream of the coordinator or
enrollment/admin chain already covered above, i.e. operation-internal to
one of the 5 closed operations, not separate callers needing their own
mapping.

### 4.6 `hpac_verifier.py` — read-only consumer

908-line module, `verify_human_authentication(...)` entry point
(HPAC-PAWA-HELPER-REQ-097). Reads resolved records to check
`authority_class is PRODUCTION`; maps onto the `certification_read`
enumerated set. Imported by `runtime_authority.py`,
`protected_presentation.py`, `runtime_dispatch_gate5.py`,
`human_authenticator_fido2.py` — all still inside `core/`, still zero
orchestration-layer callers.

### 4.7 Standalone launcher scripts (current actual "callers")

| Script | Effect | Packaged? |
|---|---|---|
| `scripts/hpac_protected_root_admin.py` | protected-root provisioning/rotation/revocation | NO |
| `scripts/hpac_principal_admin.py` | RHAMP enrollment via `production_writer` | NO |
| `scripts/hpac_protected_presentation_admin.py` | presentation-mechanism install/rotate/revoke via `production_writer` | NO |
| `scripts/hpac_certification_admin.py` | read-only today (`describe`/`status`) | NO |

**Packaging fact (independently confirmed, §3.6):** `scripts/` is
excluded from both wheel (`packages = ["src/pcae"]`) and sdist
(anchored `include` list). All four admin launchers exist only in a
source checkout — never in a `pip install`ed artifact. Today there is no
packaged launcher at all, real or fixture.

### 4.8 Summary — five helper operations vs. current in-process equivalents

| Helper operation | Current factory | Current caller(s) | R/W | Migration priority |
|---|---|---|---|---|
| `admin_mutation` | `production_writer` | `hpac_rhamp_enrollment.py`, `hpac_protected_presentation_admin.py` | write | HIGH |
| `certification_write` | `certification_writer` | `hpac_certification_coordinator.py` (itself uncalled) | write | LOW-until-FINAL-CERT |
| `certification_read` | `recognized_certification_read_authority` | `hpac_certification_coordinator.py` (uncalled), `hpac_verifier.py` | read | MEDIUM — best first slice |
| `ceremony_entry` | (implicit hand-off pre-v2.0) | `hpac_certification_coordinator.py` (uncalled) | n/a | LOW-until-FINAL-CERT |
| `presentation_evidence_write` | `mint_protected_presentation_evidence_writer` | `protected_presentation.py` | write | HIGH |

Every one of the 5 closed helper operations maps cleanly onto an
existing in-process factory/consumer pair. **No caller was found
requiring a sixth operation.**

## 5. Legacy in-process authority mechanism inventory

| Mechanism | Location | Reachable? | Bearer? | Temporarily required? | Removable after | Risk if dual-path persists |
|---|---|---|---|---|---|---|
| `_detect_caller_module` / `_verified_production_caller_name` (frame code-object/globals pinning) | `hpac_protected_admin_writer.py` | YES, all 4 factories | n/a (identity check) | YES, until real helper replaces admission | real helper implemented AND all factory callers migrated | HIGH — exactly the mechanism independently proven insufficient by N16-5-F5B2R2-IMPL |
| `AUTHORIZED_FACTORY_CONSUMERS` / `CERTIFICATION_FACTORY_CONSUMERS` / `READ_AUTHORITY_CONSUMERS` (closed dotted-module allowlists) | same file | YES | n/a | YES (shape preserved conceptually by helper's operation vocabulary) | once in-process enforcement point is retired | LOW on its own; the enumerated-allowlist *shape* is not the vulnerability |
| `_authority_seal`/`_seal` constructor-seal family | `hpac_foundation.py` | YES | non-bearer, explicitly documented insufficient on its own | YES — useful defence-in-depth against accidental misuse even post-migration | never fully — remains a disclosed non-production seam per HPAC-PAWA-HELPER-REQ-096 | MEDIUM if ever mistaken for a real trust boundary |
| `ProductionWriterHandle` / `CertificationWriterHandle` / `CertificationReadAuthority` (bearer capability objects) | `hpac_protected_admin_writer.py` | YES | **bearer** | YES until every consumer in §4.5 is migrated | only after all bearer-typed call sites migrated (large, multi-module slice) | **HIGH** — HPAC-PAWA-001 v2.0 / HPAC-PAWA-HELPER-001 §24 (PAWAH-INV-1) name these three types by name as forbidden cross-boundary exports; the single largest concrete legacy artifact |
| `HPACStoreAuthority.production()`/`.fixture()` | `hpac_foundation.py` + 7+ modules | YES | n/a (authority-class marker, not a writer) | YES — also the primitive the helper process itself will reuse | retiring in-process **callers**, not the constructor | LOW-MEDIUM |
| Disclosed test-only seams (`_production_test_fixture`, `_topology_probe`, etc.) | scattered, `hpac_pawa_helper_*.py` | test-only by construction | n/a | must remain for deterministic/Linux CI even post-implementation | N/A — contract legitimizes continued existence as test seams only | LOW, contingent on existing guard tests continuing to pass |

No orphaned/undocumented legacy mechanism was found beyond what the
frozen contracts already name as either "to be superseded by §33C" or "a
disclosed non-production seam."

## 6. Contract facts governing the architecture (independently verified, §3)

- Closed 5-operation vocabulary, closed request/response schemas, no
  generic/prefix/wildcard dispatch (HPAC-PAWA-HELPER-001 §11–§13).
- 21-value closed `pawa_failure_code` vocabulary — independently
  confirmed byte-for-byte in source (§3.7); v2.0 introduces zero new
  codes.
- 5-value closed `ReplayOutcome` — independently confirmed in source
  (§3.7): `FRESH | CONSUMED | DUPLICATE_IN_FLIGHT | EXPIRED |
  CONFLICTING`.
- Closed typed `certification_read` set (principal/credential records,
  RHAMP sidecar + counter-state read, presentation installation/
  mechanism descriptor, PAWA anchor/descriptor/agent-exclusion records)
  — no wildcard/generic/OS-secret/private-key/unrelated-principal read
  ever permitted.
- `admin_mutation` is metadata-only by construction — confirmed the
  production `handle_admin_mutation` never creates/copies helper bytes
  and never chmod/chowns a path.
- `presentation_evidence_write` forbidden-key set independently
  confirmed in source (§3.8): `{"approved", "verified", "human_present",
  "authenticated"}` — a caller cannot self-assert human approval/UP/UV.
- State-transition model: `REQUEST_RECEIVED → REQUEST_AUTHENTICATED →
  OPERATION_ADMITTED → MUTATION_ATTEMPT_STARTED (no-auto-retry boundary)
  → MUTATION_COMMITTED → EVIDENCE_WRITTEN → RESPONSE_EMITTED`. A crash
  between `MUTATION_COMMITTED` and `EVIDENCE_WRITTEN` is
  INDETERMINATE/RECONCILIATION-REQUIRED, never silent success, never
  auto-retried.

## 7. Replay integration surface (`src/pcae/core/hpac_pawa_helper_replay_state.py`)

A future client/transport library integrates against:
`open_durable_replay_ledger(...)` (the only sanctioned production entry
point — a bare `ReplayLedger()` is in-memory-only and cannot enforce
replay across the one-shot helper process lifetime),
`DurableReplayStore.check_and_reserve` (the single admission decision,
returning one of `FRESH`/`CONFLICTING`/`EXPIRED`/`CONSUMED`/
`DUPLICATE_IN_FLIGHT`), `.transition` (forward-only, illegal transitions
raise `ReplayStateCorruption` rather than rewriting history),
`.release_reservation` (only releases this process's own unspent
reservation), `.read_record`/`.iter_records` (reconciliation reads — a
corrupt record raises rather than being silently skipped),
`.prune_expired` (deployment-owner maintenance only, never reachable
from any of the 5 operations), `record_exports_no_authority` (defence-
in-depth token scan). The replay decision is a privileged-side
responsibility: the store must be opened from inside the one-shot helper
process itself, never from the launcher or ordinary interpreter code.

## 8. Architecture design (Sections 13–37 of the authorization prompt)

### 8.1 Client-side request builder

Typed domain wrappers, never a caller-facing generic
`call_helper(operation, params)`. One typed function per current
factory-replacement need (e.g. `request_enroll_principal(...)`,
`request_certification_write(role, subject, session_id)`,
`request_certification_read(record_type, record_key, session_id)`,
`request_ceremony_entry(session_id, ceremony_request_digest)`). Each
wrapper hard-codes its own `operation`/`operation_version`/
`operation_params` shape — it must be structurally impossible for a
caller to pass an arbitrary `operation_params` dict (this is
PAWAH-INV-5's "no generic privileged broker" invariant applied one layer
up, to the client, not just the helper). Wrappers generate `request_id`,
`nonce`, `expiry`, and the self-excluding `request_digest` themselves —
never caller-supplied raw values echoed unvalidated. Lives in a new,
non-agent-importable module (never imported by `cli.py`, `commands/**`,
or `core/agent.py`), matching the existing fence around
`hpac_rhamp_enrollment.py`/`hpac_protected_presentation_admin.py`.

### 8.2 Transport client (one-shot process model)

launch → one private channel → one request → one response → exit,
matching the existing `hpac_pawa_helper_os.OneShotChannel`/
`verify_helper_executable`/`execute_verified` pattern (already
implemented, Linux-only for `execute_verified`). Obligations: build
exactly one request via a typed wrapper; verify the executable
(same-file-object, no re-open after validation) before any exec, STOP
BLOCKED on a platform without substitution-free exec (today: everywhere
but Linux); create the channel, exec, send one request, block for one
response with a bounded timeout; on timeout/crash/malformed response,
fail closed and treat as INDETERMINATE — never retry the same
`(request_id, nonce)`; exit holding no state beyond what reconciliation
needs.

### 8.3 Launcher (research only — not implemented this phase)

Evolves the existing 4 `scripts/hpac_*.py` launchers (or adds new ones)
to build a request (§8.1), run the transport client (§8.2), and
act on the typed response — never a new generic "run any operation"
launcher. Constrained by the packaging fact in §4.7: a real launcher
usable outside a source checkout requires either accepting
source-checkout-only privileged deployment (status quo) or a future
explicit packaging decision to add a launcher entry point. The launcher
holds no authority object ever — only the request it built and the
response it received.

### 8.4 Platform model

- **Linux**: conforming — `execute_verified` supports substitution-free
  exec; `get_kernel_peer_credential` supports `SO_PEERCRED`.
- **macOS**: `get_kernel_peer_credential` already has a
  `_peer_credential_darwin` path, but `execute_verified` raises
  `UnsupportedPlatformProfile` on any non-Linux platform — **macOS
  cannot run a real helper today, by design, not by omission**. This
  status is preserved unchanged by this phase.
- **Deterministic NON_REAL test fixture**: the existing
  `hpac_pawa_helper_operations.py`/`hpac_pawa_helper_protocol.py`
  in-process dispatch table, usable for development/CI on any platform
  including macOS.
- **Absolute rule**: a caller-supplied `real=True`-shaped flag (or any
  request field) must never be able to upgrade deterministic/fixture
  execution into production authority. Already frozen
  (HPAC-PAWA-HELPER-REQ-095/096/097): production authority requires (1)
  the integrity-verified out-of-band executable, (2) launch by an
  enumerated deployment-owner launcher, (3) a deployment-owner peer
  credential — all three are OS/filesystem facts, never request fields.
  The client library must have no code path accepting a caller-chosen
  "treat this as real" flag.

### 8.5 Request identity / currentness / replay binding

**Caller-generated**: `request_id`, `nonce`, `expiry`,
`operation`/`operation_version`/`operation_params`, `session_id`,
principal/credential/proof binding, echoed `installation_id`/
`generation`, `request_digest`. **Helper-verified, never
caller-asserted**: actual expiry-in-future per trusted clock; whether
`installation_id`/`generation` match the live root;
fresh/consumed/duplicate/conflicting via
`DurableReplayStore.check_and_reserve`; peer credential is the
deployment owner; the executed binary is the verified one. Even
idempotent `certification_read` re-runs full validation every call — no
previously-established session is trusted.

### 8.6 Timeout / no-auto-retry semantics

Once `MUTATION_ATTEMPT_STARTED` is crossed, `(request_id, nonce)` is
spent unconditionally; a timeout/crash/lost response after that point is
never grounds for resending the same identity. The client library must
expose two distinct operations: `send_request(...)` (one-shot, may time
out) and `reconcile(...)` (reads the durable replay/evidence record for
the true outcome). A caller that reacts to a timeout by silently minting
a new `(request_id, nonce)` for "the same logical operation" without
reconciling first risks a double-mutation attempt that only
`certification_read`'s idempotency can safely tolerate.

### 8.7 Error mapping

All rejections collapse onto the existing 21 `pawa_failure_code` values
— the client library maps each to a caller-facing exception class but
invents no new caller-visible error category (that would itself trigger
a contract-evolution requirement). Informative grouping: admission
failures, request-shape failures, freshness/replay failures,
trust-root/descriptor failures, internal. None are ever silently
retried by the client.

### 8.8 Response trust ("structurally valid != trusted helper result")

Mirrors the replay-record validation discipline already implemented.
Beyond schema-valid parsing, the client must verify
`protocol_version`/`request_id`/`nonce` echo the sent request,
`response_digest` recomputes, and — if `decision == PERFORMED` —
`evidence_digest` matches a later reconciliation read of the protected
root (the actual trust anchor; the response itself is a convenience). A
response failing any check is treated identically to "no response
received."

### 8.9 No-authority-export

The client's public API returns only: a `decision` enum, a
`terminal_code` on rejection, an `evidence_ref`/`evidence_digest` pair,
and (for `certification_read`/`ceremony_entry`) the typed
`result_payload`. Never `HPACWriterCapability`, `HPACStoreAuthority`,
`ProductionWriterHandle`, `CertificationWriterHandle`, or
`CertificationReadAuthority` (HPAC-PAWA-HELPER-REQ-091's forbidden-export
list, named by type) — enforced at the client API boundary as defence in
depth on top of the wire-protocol-level enforcement.

### 8.10 Gate5 / RHAMP / challenge / assertion / proof-verifier — semantic walls

All contract-named semantic walls are preserved verbatim by the client
API's design (no shortcut implying any of the following are the same
thing): OS peer credential != human identity != human approval; YubiKey
touch (UP) != approval; deterministic proof != real authentication;
ceremony entry != approval != authentication != Gate-5 ALLOW != PB
permission != execution; challenge issuance != human approval != proof
validity != Gate 5; recorded assertion != valid assertion; Gate5 ALLOW
!= PB permission != human approval != consumed authority != runtime
capability != adapter admission != external-effect permission; counter
evidence != human approval != PB permission != execution; presentation
evidence != authentication proof; APPROVE != authenticated principal.
Practical enforcement: five separate typed result classes (one per
operation), never one generic `Result` with optional fields, so a future
caller cannot mistake one operation's result for another's by
structural accident.

- **Gate5** (`hpac_gate5_binder`): the request/response flow consumes
  already-valid authenticated/protected evidence; it never becomes the
  place that invents that evidence. No Gate5 certification is performed
  in this phase.
- **RHAMP counter** (`hpac_rhamp_counter_state_verifier`): authentication
  assertion accepted != counter state verified != approval. No real
  YubiKey/counter mutation in this phase.
- **Challenge coordinator** (`hpac_challenge_coordinator`): challenge
  issuance never itself authenticates the principal; canonical challenge
  id generation, subject/principal binding, expiry, and single-use
  semantics are helper-side.
- **Assertion recorder** (`hpac_assertion_recorder`): accepts assertion
  data but the caller cannot self-assert successful UP/UV.
- **Proof verifier** (`human_authentication_proof_verifier`): current
  FIDO2 mechanism is supported, not exclusive — the interface stays
  mechanism-neutral to support future mobile-only mechanisms.

### 8.11 Installation / generation binding

Every request echoes `installation_id`/`generation`; a mismatch is
`CONFLICTING`, never `FRESH` (already implemented in
`DurableReplayStore.check_and_reserve`) — a generation rotation
partitions the replay keyspace so a stale-generation request cannot
resurrect against the new generation's history. The client must always
read the live current-generation record immediately before building a
request, never cache it across a long-lived process.

### 8.12 Configured-agent identity

Must call the existing `resolve_configured_agent_identity`/
`resolve_live_authority_identity` (`hpac_pawa_agent_exclusion.py`) —
never derive from `os.geteuid()`/`USER`/`LOGNAME`/`SUDO_USER` (the
module's own docstring states this explicitly). The helper independently
resolves the configured-agent principal live from
`HPAC-PAWA-AGENT-EXCLUSION/1.0`; it is not a request field at all (not in
the closed §11 field set).

### 8.13 Peer-credential semantics

Kernel-authenticated `(uid[, gid, pid])` evaluated by the helper against
"= deployment owner AND != configured agent principal," already
implemented cross-platform (`get_kernel_peer_credential`). The client
(launcher) side has no role beyond being the actual OS process that
connects — it cannot spoof or supply an alternate peer credential.

### 8.14 One-shot process model

Preserved: one helper process per protected operation. No long-lived
generic privileged daemon. `launch → one private channel → one request →
one response → helper exit.`

### 8.15 Multi-operation workflow orchestration / cross-operation binding

A future orchestrator (e.g. `ceremony_entry` → human APPROVE via
HPAC-PPA-001 → `certification_write` for `hpac_gate5_binder`) treats
each operation as an independent, freshly-authenticated invocation — no
session-level "already authorized, proceed" shortcut
(HPAC-PAWA-HELPER-REQ-062: "a PERFORMED certification_write does not
permit the coordinator to remint, delegate, or convert to generic
authority; a second certification_write re-runs the full sequence in a
fresh helper process"). Cross-operation binding uses only immutable IDs/
digests (`session_id`, `certification_session_id`, `evidence_ref`/
`evidence_digest`, ceremony `result_payload.ceremony_reference`) — never
a shared in-memory object or capability.

### 8.16 Partial-workflow failure semantics

If step N of a multi-step flow fails or times out, steps 1..N-1's
`PERFORMED` results and their evidence remain valid and durable/spent —
there is no "roll back the ceremony" operation, since each step is
already committed and audited independently. Recourse for step N is
reconciliation (§8.6) followed by a fresh request (new id/nonce) only if
reconciliation shows no effect occurred; steps 1..N-1 are never undone
or replayed.

## 9. No-fallback rule (normative, Section 39 of the authorization prompt)

If the helper path is unsupported, unavailable, rejects the request,
fails provenance, fails peer credentials, reports replay conflict, or
reports indeterminate, the caller **must not** fall back to the legacy
in-process authority path. Architecturally enforced by ensuring the
future client module and the legacy factory module
(`hpac_protected_admin_writer.py`) are never imported together in any
migrated call path — a static guard test (mirroring the existing
"no non-test module is a member of the certification consumer
allowlist" pattern already used in this codebase) is the recommended
durable enforcement mechanism for the future implementation phase.

## 10. Legacy path retirement plan

For each mechanism in §5: last production caller and removability are
tied to migration completion of that caller. Concretely: the frame-check
mechanism and the three bearer capability types become removable only
after every consumer in §4.2/§4.3/§4.4/§4.5 is migrated to the client
library and a guard test can assert none of the `AUTHORIZED_FACTORY_CONSUMERS`
names are reachable via the legacy path any more. The constructor-seal
family and `.production()`/`.fixture()` constructors are not removed —
only their in-process **callers** are retired; the primitives themselves
remain reusable inside the future helper process. Nothing is deleted in
this phase.

## 11. Migration order (derived from §4/§5, not assumed)

1. **Slice 1** (read-only, no macOS dependency): typed
   `certification_read` client library wrapping the existing
   deterministic dispatch (`handle_certification_read`); migrate
   `hpac_verifier.py`'s read path onto it. Safest first slice — no
   mutation/replay-spend risk, fully exercisable on Linux CI and macOS's
   deterministic path.
2. **Slice 2**: real Linux out-of-process transport + launcher for
   `certification_read` only, verified on a real Linux host (macOS
   remains fail-closed, non-blocking).
3. **Slice 3**: migrate `admin_mutation`, starting with
   `hpac_rhamp_enrollment.py`'s `production_writer` call sites (highest
   priority — the bootstrap path, already exercising real FIDO2
   hardware via `hpac_rhamp_ctap2.py`).
4. **Slice 4**: migrate `presentation_evidence_write` — gated on
   resolving the still-open HPAC-PPA-001 packaging/launcher question for
   `pcae.protected_presentation_helper`, since the write now happens
   inside that helper per HPAC-PPA-001 v2.0.
5. **Slice 5**: migrate `certification_write` + `ceremony_entry`
   together (shared sole consumer) — naturally gated on N16-5-FINAL-CERT's
   real-ceremony design, since `hpac_certification_coordinator.py` has
   no live caller to migrate against yet.
6. **Slice 6 (last)**: remove the four legacy factories and the
   frame-pinning machinery, once every consumer above is migrated and a
   guard test proves no remaining reachability.

### 11.1 Read-only-first evaluation

Chosen deliberately, not by default: `certification_read` has no write
dependency to sequence around, exercises the full
client/transport/request/response architecture with zero protected
mutation, and is the lowest-risk path to validate before any
mutating operation is attempted.

### 11.2 First recommended implementation slice (concrete)

- **New module**: `src/pcae/core/hpac_pawa_helper_client.py` — typed
  request builders (§8.1) + a `CertificationReadClient` wrapping the
  existing deterministic dispatch for slice 1; the not-yet-implemented
  real-transport path stubbed to raise `NotImplementedError`/
  `UnsupportedPlatformProfile` explicitly, never silently falling back.
- **New tests**: typed-request construction rejects unknown fields; the
  client never accepts a free-form `operation_params` dict; response
  validation rejects a tampered `response_digest`; `REJECTED` maps to
  the correct one of the 21 failure-code exception classes;
  reconciliation reads agree with the in-process dispatch result; no
  forbidden-authority token appears in any client-returned value.
- **Migration target**: `hpac_verifier.py`'s read-only consumption of
  `recognized_certification_read_authority`.
- **No-legacy-fallback test**: guard test asserting the new client
  module never imports `hpac_protected_admin_writer`'s factories.
- **Replay/no-auto-retry test**: guard asserting no client method
  reuses `(request_id, nonce)` after a timeout/indeterminate result.
- **Verification phase afterward**: an independent-verification phase is
  recommended before slice 2 begins, per this repository's established
  discipline of not self-closing findings.

### 11.3 macOS dependency adjudication

**YES — slice 1 can proceed without real macOS helper execution.** It
only needs the platform-neutral deterministic dispatch table (already
implemented) plus Linux-only real-transport work deferred to slice 2.
No live macOS protected effect is claimed or required.

## 12. Real-host verification / packaging / deployment / real-certification prerequisites

- **Real-host verification** becomes mandatory starting at slice 2: a
  real Linux host with a provisioned protected root, a real
  deployment-owner OS account distinct from the configured agent,
  `SO_PEERCRED`-capable sockets, and a filesystem supporting
  `link()`/`O_NOFOLLOW`/`fsync`; genuine FIDO2/CTAP2 hardware is
  additionally required starting at slice 3.
- **Packaging boundary** (open question, not a blocker): no helper
  executable exists yet to package; `scripts/` (the launchers) is
  excluded from both wheel and sdist today (§4.7) — whether a real
  deployment runs from an installed wheel (requiring a packaged launcher
  entry point) or always from a source checkout (status quo) is an
  explicit decision the future implementation phase must make, not
  assumed here.
- **Deployment boundary**: install verified helper bytes; register
  generation; provision replay namespace; set ownership/mode; bind
  descriptor metadata; verify same-file-object execution; verify peer
  credential topology; verify no legacy-path fallback remains possible.
  None of this is performed in this phase.
- **Real F-5 certification preconditions** (unchanged, restated):
  caller migration completed; legacy authority path
  removed/unreachable; helper installed/registered; required platform
  execution path available for the chosen certification host;
  replay/provenance/peer properties verified in deployment; real
  protected-presentation and real-authenticator paths available; real
  certification orchestration complete. **Not scheduled by this phase.**

## 13. Threat matrix (20 attacks, Section 51 of the authorization prompt)

| # | Attack | Boundary | Expected failure | Future test |
|---|---|---|---|---|
| 1 | Arbitrary operation string | closed 5-op enum | `operation_scope_invalid` | reject any string outside the 5, incl. near-miss prefixes |
| 2 | Invented role | closed 5-role allowlist | `operation_scope_invalid` | reject `hpac_lifecycle_terminator` and any made-up role |
| 3 | Invented configured-agent identity | helper resolves live from agent-exclusion record, never a request field | not a valid field; smuggled key → `operation_scope_invalid` | assert schema rejects any agent-identity-shaped key |
| 4 | Claimed human APPROVE | forbidden-key check on `presentation_evidence_write` | `operation_scope_invalid` | extend forbidden-key check to client-side pre-validation |
| 5 | Claimed UP/UV | same forbidden-fact set | `operation_scope_invalid` | same as #4 |
| 6 | Replay of successful request | `DurableReplayStore` → `CONSUMED` | `capability_stale` | already covered by 76 replay-repair tests; extend to real transport |
| 7 | Retry after timeout | no-auto-retry rule | client refuses; server-side re-presentation → `CONSUMED`/`DUPLICATE_IN_FLIGHT` | assert client has no `retry()` reusing `(request_id, nonce)` |
| 8 | Retry after indeterminate | reconciliation-only path | client requires explicit reconciliation before any new request | assert no silent auto-generation of a new id/nonce after INDETERMINATE |
| 9 | Fallback to legacy path on rejection | absolute no-fallback rule | architecturally impossible, not policy | guard test: client module never imports legacy factories |
| 10 | Reuse response as bearer authority | response carries no capability | client returns only typed result | assert typed result classes grant no further authority |
| 11 | Substitute deterministic helper for real | same-file-object + hash + owner/mode check | STOP BLOCKED | existing `verify_helper_executable` tests, extended end-to-end |
| 12 | Alternate helper executable | same as #11 | same | same |
| 13 | Stale generation metadata | generation cross-check | `descriptor_generation_stale`/`CONFLICTING` | already covered by replay-repair generation-mismatch tests |
| 14 | Trust arbitrary JSON response | response-trust model (§8.8) | reject on digest/echo mismatch, treat as no-response | tampered-response-bytes test |
| 15 | Compose typed ops into generic broker | typed wrapper design (§8.1) | structurally impossible | guard test: no client function accepts a raw dict as `operation_params` |
| 16 | Bypass replay store | store is helper-internal, mandatory | production code must not call bare `ReplayLedger()` | extend existing replay-repair guard to the new client module |
| 17 | Directly import legacy writer factory | closed allowlists | `unauthorized_factory_consumer`; client module never added to any allowlist | guard test: client module not a member of any consumer allowlist |
| 18 | Use environment identity | explicit prohibition in `hpac_pawa_agent_exclusion.py` | client must not read `geteuid`/`USER`/`LOGNAME`/`SUDO_USER` | grep-based guard test on the new client module |
| 19 | Treat peer credential as human identity | PAWAH-INV-8 | never surfaced as a human/approval fact | assert typed results have no human-identity field derived from peer credential |
| 20 | Unsupported macOS path silently downgrades | `execute_verified` raises `UnsupportedPlatformProfile`, never silent fallback | STOP BLOCKED, loudly | extend existing test to the new client's real-transport path |

## 14. Potential architecture blockers — none found

Every one of the 5 helper operations maps cleanly onto an existing
in-process factory/consumer pair (§4.8). No caller requires a read
outside the closed typed set (§6). No caller performs an operation
outside the closed 5. No contract/schema gap was discovered.

Two **non-blocking** items are flagged for the next phase's attention:

1. `hpac_certification_coordinator.py` has zero current callers
   (independently confirmed, §3.5) — by design (real ceremony deferred
   to N16-5-FINAL-CERT), but slices 3 and 5 cannot be validated against
   a real existing caller today; they need a synthetic/test-only driver
   until N16-5-FINAL-CERT begins.
2. HPAC-PPA-001 v2.0's evidence-writer-delivery resolution is
   contract-frozen but its dedicated independent verification
   (`N16-5-F-5-PPA-CONTRACT-IV`) has not yet been performed. Any work
   touching `presentation_evidence_write` (slice 4) should treat this as
   contract-frozen-but-not-independently-verified, and ideally that IV
   should land before slice 4 begins.

## 15. Architecture validation (Section 57 checklist)

Every production caller accounted for (§4); every protected write maps
to exactly one helper operation (§4.8); every certification write maps
to a valid role from the closed 5-role family (§4.3); every protected
read maps to the closed typed read set (§6); no sixth operation
required; no generic broker introduced (§8.1); no legacy fallback
permitted (§9); deterministic vs. production separated (§8.4); replay
semantics preserved (§7, §8.5); timeout/indeterminate behavior safe
(§8.6); macOS unsupported status preserved unchanged (§8.4); no caller
gains an authority object (§8.9); retirement sequence complete (§10).

## 16. Files changed this phase

- `docs/PHASE_N16_5_F_5_TB_CALLER_INTEGRATION_ARCH.md` (new, this file)
- `PROJECT_STATUS.md` (Current Phase section updated)
- `CHANGELOG.md` (entry added)
- `.pcae/phase-completion-metadata.json`
- `.pcae/phase-completion-report.md`
- `.pcae/fast-green-attribution/*.json` (new evidence file)
- `tasks/active/*.md` / `tasks/done/*.md` (task lifecycle)

**Production source changes: NONE.** **Contracts changed: NONE.**
**Schemas changed: NONE.** **Dependencies changed: NONE.** **Live
protected-host writes: 0.** **Real ceremony: NOT PERFORMED.**

## 17. Runtime / effect wall (unchanged)

Runtime state: Observed. Maximum capability: observe. Execution
availability: unavailable. Plugins: 0. Capabilities: 0. First governed
runtime external effect: ABSENT / UNREACHABLE. No adapter.dispatch. No
Gate10 effect.

## 18. Status wall

- F-5-B2: BLOCKED PENDING REMAINING PLATFORM / CALLER MIGRATION /
  PACKAGING SLICES.
- F-5: CERTIFICATION BLOCKED.
- N-16-5: NOT CLOSED.
- N-16-6: OPEN / UNTOUCHED.
- N-16-7: OPEN / UNTOUCHED — strictly last.

## 19. Recommended successor

An implementation phase for **Slice 1** exactly as specified in §11.2
(`hpac_pawa_helper_client.py`, `CertificationReadClient`, migrating
`hpac_verifier.py`'s read path, with the full guard-test suite named
above). Not begun. Requires fresh explicit human authorization.

## 20. Historical governance integrity preserved

`N16-5-F-5-TB-HELPER-IV`: COMPLETE — NOT VERIFIED / BLOCKED
(historical, unchanged). `N16-5-F-5-TB-HELPER-IV-R`: COMPLETE /
INDEPENDENTLY VERIFIED (unchanged). `N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN`:
COMPLETE (unchanged). No retroactive reinterpretation performed.

## 21. Verdict

**N16-5-F-5-TB-CALLER-INTEGRATION-ARCH: COMPLETE.** Caller/client
integration architecture: DEFINED / READY FOR IMPLEMENTATION. Production
caller migration: NOT BEGUN. Legacy authority retirement: PLANNED / NOT
BEGUN. macOS protected-helper execution: FAIL-CLOSED / NOT IMPLEMENTED
(unchanged). Helper foundation: INDEPENDENTLY VERIFIED (unchanged).
Replay durability: VERIFIED / HARDENED (unchanged).
