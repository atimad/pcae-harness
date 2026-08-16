# Phase 149O.20L.7G — DeploymentBinding Producer Contract/Schema Evolution and Implementation Planning

## 0. Status

**Contract/schema evolution + implementation planning only.** No `DeploymentBinding` producer implemented. No `DeploymentBinding` created. No repository identity created on Dell. No `pcae init` run on Dell. No Dell mutation of any kind (no Dell SSH session opened). No trust store modified. No repository onboarded. No HMIC certification requested or granted. No Boundary C or Boundary A action. No Cutover Record created. No first-use human election initiated. No Permission Broker change.

**Phase entry commit:** `01a47f05` (`Phase 149O.20L.7F: sync phase-completion metadata to post-push state`), `origin/main` == `HEAD`, 0 commits ahead, working tree clean at entry.

**Reconciliation:** `pcae phase-report reconcile --phase-id 149O.20L.7F` → `reconciled`, 2 generations promoted, marker `already_dispatched`, mutation `none`.

## 1. Purpose and Method

Phase 149O.20L.7F reconstructed, from primary source, the complete architecture connecting repository identity, `DeploymentBinding`, HBDC-REQ-042, and HMIC certification, and concluded that `DeploymentBinding` has a canonical schema and read/match consumers but **no production create/register/enroll producer** — and named two blocking findings for any future producer: F3 (`DeploymentBinding`/`CertificationRecord` cross-consistency) and F4 (rotation/revocation lifecycle gap).

This phase does not accept 7F's conclusions as oracle. §2 below independently re-derives every load-bearing claim directly from current primary source (contracts, production code, the governing CHGR) before building on it. Only after that independent reconstruction does this phase (§3 onward) turn the architecture into normative contract text (an HBDC-001 amendment, §5) and an implementation plan (§9), without writing or authorizing any producer code.

## 2. Independent Reconstruction of 7F's Load-Bearing Claims

Each claim below was re-derived this phase directly against current production source/contract text — not copied from the 7F report.

| Claim | Independently re-verified against | Result |
|---|---|---|
| `ensure_repository_identity()` exists, is idempotent-preserve, fail-closed on malformed | `src/pcae/core/repository_identity.py:211-229` read directly this phase | Confirmed unchanged |
| Wired into `pcae init` | `src/pcae/commands/init.py:41-45`: `identity = ensure_repository_identity(root)` inside `run_init()`, non-dry-run path | Confirmed unchanged |
| `DeploymentBinding` schema: 9 fields, no HMIC/host/digest field | `src/pcae/core/hatp_bootstrap.py:127-137` (dataclass) and `:351-395` (`_parse_deployment_binding`, closed field set) read directly | Confirmed unchanged, byte-identical to 7F's reconstruction |
| `HATPTrustStore` has zero write methods | `src/pcae/core/hatp_bootstrap.py:513-607` read in full this phase: `load_repository_enrollment`, `lookup_principal`, `lookup_signer`, `lookup_authority`, `signer_revoked`, `resolve_deployment_authorization`, `environment_status` — all read-only; class docstring (`:514-520`) states no method mutates state | Confirmed; independently re-swept, not re-cited |
| Registry parser rejects a second `deployment_bindings` entry for the same `repository_id` | `src/pcae/core/hatp_bootstrap.py:435-440`: `if record.repository_id in deployment_bindings: raise HATPTrustStoreMalformedError(...)` | Confirmed — **at most one binding entry per `repository_id`, regardless of status**, is schema-enforced, not a convention |
| HBDC-REQ-042 text and CBD-5 binding | `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` §16/§19, read directly this phase | Confirmed verbatim |
| HBDC-001 is currently v1.0, last requirement is HBDC-REQ-055 | §24 traceability table, `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, read directly | Confirmed — next available ID is **HBDC-REQ-056** |
| HBDC-001 is already one of HMIC-001's 28 frozen, digest-participating files | `src/pcae/core/hatp_mandatory_certification.py:990-993` (`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`), comment: "The fifth contract entry, `HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001), was added at v1.2 by the 149O.20D.1 content-identity binding repair... and aligned... by Phase 149O.20F" | Confirmed — **new HBDC-001 text is automatically digest-bound; a brand-new contract file would not be**, without its own future HMIC binding amendment |
| `repository_identity.py` and `hatp_bootstrap.py` are both members of the 22-file `_FROZEN_SRC_PCAE_RELATIVE_FILES` set | `src/pcae/core/hatp_mandatory_certification.py:953-976`, read directly | Confirmed — both participate in `implementation_scope_digest` already |
| HMIC-REQ-043/044/045: `repository_instance_id`/`canonical_deployment_root` derived read-only, exactly as `DeploymentBinding`/`repository_identity.py` already define them, at both certify time and validation time | `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §15, read directly | Confirmed verbatim |
| **New evidence beyond 7F's own citations:** HMIC's 12-step validation algorithm (§31, HMIC-REQ-103) does **not** consult `HATPTrustStore`/`DeploymentBinding.status` at validation time at all — step 7 only compares the certification's stored `repository_instance_id`/`canonical_deployment_root` against freshly re-derived values from `repository_identity.py` + `hatp_bootstrap.resolve_canonical_deployment_root`, never against a live binding's `status` field | `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §31 (HMIC-REQ-103), read directly this phase | **New finding, not in 7F** — see §4.3 below (F3-residual) |
| `hatp_bootstrap.py`'s timestamp parser (`_parse_iso_timestamp`) is more permissive than the hardened `_TIMESTAMP_PATTERN` grammar (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) used by `hatp_mandatory_cutover.py`/`hatp_mandatory_certification.py`, and was **deliberately left untouched** by the 149O.1H timestamp-hardening wave | `src/pcae/core/hatp_bootstrap.py:78-94` (`_parse_iso_timestamp`, uses `datetime.fromisoformat` after a bare `Z`-suffix replace — accepts non-`Z` offsets, arbitrary fractional precision) vs. `src/pcae/core/hatp_mandatory_cutover.py:101`/`hatp_mandatory_certification.py:207`; `docs/PHASE_149O_1H_1_...md:410`: "`src/pcae/core/hatp_bootstrap.py`: empty (Wave 1/2 untouched)" | **New finding, not in 7F** — see §8.6 below |
| CHGR condition 6 verbatim text | `.pcae/publication-execution/records/chgr-0e37ed1340b14311826722c4dbf3e856.json`, `conditions` field, read directly this phase via `python3 -c "json.load(...)"` | Confirmed byte-identical to 7F's quotation |
| No cycle: DeploymentBinding creation requires neither certification nor HBDC COMPLIANT | `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §23 (creation ceremony reads an *existing* binding, does not create one) and HBDC-001 §17 (HBDC-REQ-049, certification not gated by HBDC conformance) both read directly | Confirmed — no cycle |

No 7F conclusion was found to be wrong this phase. All are independently re-affirmed on fresh evidence, with two additional findings (F3-residual, §4.3; timestamp-grammar gap, §8.6) that 7F did not name.

## 3. Selected Normative Contract Home

**Selected: Model A — extend HBDC-001 in place (v1.0 → v1.1).**

Rationale:

1. **Existing ownership.** HBDC-001 §16 already normatively owns `DeploymentBinding`'s authority relationship (HBDC-REQ-042..046: what it means, how worktrees/clones/host-migration/backup-restore interact with it). Producer/lifecycle requirements are a direct continuation of the same subject, not a new one.
2. **Digest-binding economy.** HBDC-001 is already one of HMIC-001's 28 frozen, digest-participating files (§2 above). Extending it means the new producer requirements are automatically covered by the existing binding without a second, future, separately-governed "bind DBPC-001 into HMIC's contract set" phase — the exact kind of extra prerequisite step a dedicated contract (Model B) would create and this phase's own charter (item 71) warns against casually introducing.
3. **Repository precedent.** This codebase's own convention for an evolving concern already owned by one contract is amendment-in-place (HMIC-001 itself: v1.0 → v1.1 → v1.2 → v1.3, four in-place amendment waves, §50-52 of the HMIC contract, rather than spawning a new contract per new requirement cluster). No existing precedent favors a contract-per-producer split.
4. **Scope fit.** HBDC-001 §2 already scopes itself to "deployment topology and environment configuration for a Class-B PCAE deployment under Model A" and §16 already discusses binding lifecycle-adjacent concepts (worktree/clone/migration). Producer creation/rotation/revocation is within that same topic, not a scope departure requiring a differently-scoped contract.

**Rejected — Model B (dedicated `DBPC-001` producer contract):** would fragment `DeploymentBinding`'s normative home across two documents (HBDC-001: what a binding means for compliance; DBPC-001: how one is created) and would require a *second*, not-yet-scheduled HMIC-001 amendment before the new contract's bytes carry the same digest-binding weight HBDC-001 already has. No architecture precedent in this repository favors this split.

**Rejected — Model C (an existing canonical contract already owns producer responsibility):** does not apply. No contract — HATP-001, HMIC-001, HMRC-001, HSCE-001 — defines a `DeploymentBinding` creation ceremony anywhere (independently re-confirmed by the sweep in §2).

The amendment is **HBDC-001 v1.0 → v1.1**, mirroring HMIC-001's own amendment-history section convention (a new `## <n>. Contract Amendment History — Phase 149O.20L.7G (v1.1)` section, requirements numbered from **HBDC-REQ-056**, no renumbering of HBDC-REQ-001..055).

## 4. Existing DeploymentBinding Schema — Frozen As-Is

Reconstructed directly from `src/pcae/core/hatp_bootstrap.py:127-137` and `:351-395` this phase (not copied from 7F):

```
repository_id              str, UUID4 (is_valid_repository_instance_id), required
canonical_deployment_root  str, non-empty, resolve_canonical_deployment_root() output, required
principal_id                str, non-empty, required
signer_key_id                str, non-empty, required
provider_profile             str, non-empty, required
authority_scope               str, non-empty, required
valid_from                    str, timezone-aware ISO-8601 (permissive grammar, §8.6), required
status                         "active" | "revoked", closed vocabulary, required
revoked_at                    required iff status == "revoked"; forbidden otherwise
```

### 4.1 F3 — DeploymentBinding / CertificationRecord Cross-Consistency: Exact Reconstruction

`CertificationRecord` (`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` §11, HMIC-REQ-032) independently stores its own `repository_instance_id` and `canonical_deployment_root` fields — it does **not** store a `DeploymentBinding` identifier or digest. HMIC-REQ-043/044/045 (§15) require both fields to be **derived read-only, exactly as `DeploymentBinding`/`repository_identity.py` already define them**, at both certify time (creation ceremony, HMIC-REQ-076 step 4) and validation time (HMIC-REQ-103 step 2-3). This is already, today, **Option "independently reconstruct matching fields"** from item 10 of the governing prompt — not a stored reference, not a digest.

**What HMIC-REQ-103's 12-step validation algorithm actually checks against a live `DeploymentBinding` at validation time: nothing.** Step 7 ("validate `repository_instance_id` + `canonical_deployment_root` match") compares the certification's *stored* values against values *freshly re-derived from the repository-identity file and the filesystem path* — never against `HATPTrustStore.load_repository_enrollment()`'s current `status`. **A `DeploymentBinding` that is later revoked, with its `repository_id`/`canonical_deployment_root` values otherwise unchanged, would not cause an existing `CertificationRecord`'s validation to fail** under HMIC-REQ-103 as currently frozen. This is a real, previously-unnamed gap (§4.3, F3-residual) — but it lives entirely inside HMIC-001's own validation algorithm, not in `DeploymentBinding`'s schema or producer, and this phase does not amend HMIC-001 (out of scope — no HMIC v1.2/v1.4 amendment is authorized here).

### 4.2 F3 Normative Resolution (this phase)

**Selected: value-derived consistency (existing model), reaffirmed, no schema change to either record.**

- `DeploymentBinding`'s schema (§4) is **not** amended with a `certification_id`, `certification_digest`, or any HMIC-facing field. HMIC certification's own contract (HMIC-REQ-043..045, unmodified) already requires the *opposite* dependency direction — certification reads from the binding, never the reverse (§19 of 7F, re-confirmed §2 above, no cycle).
- The new HBDC-001 producer requirements (§5) normatively bind the producer to write `canonical_deployment_root`/`repository_id` values computed by the **exact same functions** HMIC-REQ-043/044 already cite (`repository_identity.py`, `hatp_bootstrap.resolve_canonical_deployment_root`) — this is a textual cross-reference, not new code, and guarantees the two records can never disagree on *how* their shared keys are computed, only (potentially) on *current binding status*, which is F3-residual's separate, narrower concern.
- **F3 disposition:** RESOLVED NORMATIVELY for the producer's own responsibilities (the producer must not invent an alternate identity/root derivation). The narrower validation-time cross-check gap (F3-residual, §4.3) is named, not resolved, and is explicitly out of this phase's scope (would require an HMIC-001 amendment, not an HBDC-001 one).

### 4.3 F3-Residual (New Finding, Non-Blocking, Deferred)

HMIC-001's validation algorithm (HMIC-REQ-103) does not re-check `DeploymentBinding.status == "active"` at validation time — a revoked binding does not, by itself, invalidate an already-issued certification under current contract text. This is architecturally consistent with HMIC-REQ-095 ("never downgrades mode") but means a stale-but-formerly-correct certification could coexist with a currently-revoked binding without HMIC's own validator surfacing that fact. **Deferred, non-blocking, out of scope for HBDC-001**: a future HMIC-001 amendment phase should decide whether to add a live binding-status cross-check to HMIC-REQ-103, or to rely exclusively on HBDC-REQ-042's own separate, already-existing binding-status check to surface this (they are already two independent verifiers over related but non-identical concerns, per §30/§43 of 7F, and this phase does not need to unify them to close HBDC-REQ-042).

### 4.4 F4 — Rotation/Revocation Lifecycle: Exact Reconstruction

Independently reconfirmed (§2): `status` vocabulary is a closed two-value set (`"active"`, `"revoked"`); `_require_revoked_at_consistency` fully implements read/validate for both; **no write path of any kind exists** (§2's registry-parser finding is the crux): only **one** `deployment_bindings` entry may exist per `repository_id`, of either status, simultaneously — the schema has no history array, no superseded-record list, and no mechanism analogous to `CertificationRecord`'s append-only-plus-active-pointer model.

### 4.5 F4 Normative Resolution (this phase)

**Selected: NO SCHEMA CHANGE.** The existing two-state vocabulary and single-entry-per-`repository_id` constraint are sufficient, given the following normatively frozen semantics (full producer contract text in §5):

- **Revocation** = an in-place field mutation of the sole existing entry: `status` → `"revoked"`, `revoked_at` set, all other fields (`repository_id`, `canonical_deployment_root`, `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope`, `valid_from`) unchanged. This mirrors `CertificationRecord`'s own revocation discipline (HMIC-REQ-091: "field mutation, not deletion") even though the storage shapes differ (single-slot vs. append-only) — the *revocation act* is analogous: never destructive deletion, always an auditable field transition on the surviving record.
- **Rotation** = a full in-place overwrite of the sole entry's mutable fields (new `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope`/`canonical_deployment_root` as applicable, new `valid_from`, `status` reset to `"active"`, `revoked_at` cleared). The schema retains **no history** of the prior field values inside the trust store itself — this is a deliberate, evidence-based choice, not an oversight: the trust store's own job (HBDC-REQ-009-021) is current authoritative state, not history; **history is the job of this repository's existing governance/provenance/audit-record infrastructure** (CHGR / publication-execution records — the same machinery already used for every other authority-bearing decision in this repository), which the producer's audit-evidence requirement (§5, HBDC-REQ-062) binds to explicitly.
- **F4 disposition:** RESOLVED NORMATIVELY — IMPLEMENTATION PENDING. No schema evolution needed; full lifecycle semantics (create, rotate, revoke — all three as in-place, atomically-written, audited overwrites of the single registry entry) are frozen by §5's new requirement text.

## 5. New Normative Requirements — HBDC-001 §16 Extension (v1.0 → v1.1)

Full contract text is applied to `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` in this phase's commit (see §12 for the exact diff summary). Requirements **HBDC-REQ-056** through **HBDC-REQ-070** are added; HBDC-REQ-001..055 are unmodified (immutable, per this contract's own §0 discipline: "a superseded requirement is marked superseded, not renumbered or deleted" — none of the 55 are superseded here).

Summary of the 15 new requirements (full RFC-2119 text is in the contract file itself):

| ID | Statement |
|---|---|
| HBDC-REQ-056 | The `DeploymentBinding` creation/rotation/revocation writer SHALL be a separate, non-agent-writable admin tool — never a subcommand of the ordinary agent-reachable `pcae` CLI (mirrors HMIC-REQ-079/081/082 exactly). |
| HBDC-REQ-057 | The writer SHALL derive `repository_id` and `canonical_deployment_root` read-only, from the target repository's existing `RepositoryIdentity` and `resolve_canonical_deployment_root()` respectively — never as free-form caller input (mirrors HMIC-REQ-045). |
| HBDC-REQ-058 | `principal_id`, `signer_key_id`, `provider_profile`, `authority_scope` SHALL be drawn from the admin's own enrollment context, not from repository-local state or agent-supplied input. |
| HBDC-REQ-059 | Creation SHALL fail closed if an entry for the target `repository_id` already exists with different field values (conflicting), and SHALL be a safe no-op if an entry exists with identical field values (idempotent-preserve, mirroring `ensure_repository_identity`'s own discipline). |
| HBDC-REQ-060 | Rotation and revocation are each a distinct, explicit admin operation from creation — never implicit, never triggered by re-running the create operation against an existing entry. |
| HBDC-REQ-061 | Revocation SHALL be performed by field mutation (`status` → `"revoked"`, `revoked_at` set) on the existing single registry entry for that `repository_id`; the record SHALL NOT be deleted. |
| HBDC-REQ-062 | Every writer operation (create, rotate, revoke) SHALL produce an audit record in this repository's existing governance/provenance/publication-execution infrastructure; no bespoke audit mechanism SHALL be introduced. |
| HBDC-REQ-063 | The writer SHALL use the same atomic-write discipline (`mkstemp`/`fsync`/`os.replace`, same-directory temp file, symlink rejection before and after the write race window) already established by `repository_identity.py::_write_atomic`; no new idiom SHALL be invented. |
| HBDC-REQ-064 | The writer SHALL require explicit evidence of a fresh, separate human election authorizing the specific binding proposition (repository, root, principal, scope) before writing; it SHALL NOT accept an unverified boolean or free-form "approved" string as sufficient authority. |
| HBDC-REQ-065 | The election-evidence reference (e.g., a governance-decision-session/CHGR identifier) SHALL be recorded as audit metadata on the resulting operation; it is evidentiary, not itself cryptographically verified by this writer (mirrors HMIC-REQ-078's own disposition: the tool does not overclaim verification it does not perform). |
| HBDC-REQ-066 | The writer SHALL be invocable only by the admin OS principal, out of band from any PCAE-agent-invoked code path — never agent-invocable, directly or indirectly, mirroring HBDC-REQ-009/012's existing Protected-Root-creation discipline. |
| HBDC-REQ-067 | A future writer implementation's own `valid_from`/`revoked_at` output SHALL conform to the strict `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$` grammar already used by `hatp_mandatory_cutover.py`/`hatp_mandatory_certification.py`, even though `hatp_bootstrap.py`'s current *read-path* parser (`_parse_iso_timestamp`) remains more permissive as of this amendment (§8.6) — the writer SHALL NOT rely on read-path permissiveness to emit a noncanonical timestamp form. |
| HBDC-REQ-068 | Repository identity (Layer 1) creation is not itself gated by this section's election requirement (HBDC-REQ-056..066 govern `DeploymentBinding` only); nothing in this amendment alters HATP-REQ-048's existing disposition that repository-identity creation confers no authority and needs no approval. |
| HBDC-REQ-069 | This amendment does not alter, and is not itself, the CHGR condition 6 election required before any real `DeploymentBinding` is created (governing-CHGR-instance-specific, not a standing contract requirement) — a future, separate, real election remains required regardless of this contract text existing. |
| HBDC-REQ-070 | This amendment's own bytes participate in `implementation_scope_digest` per HBDC-001's existing HMIC-bound-file status (§17, unchanged); any future certification issued after this amendment reflects the amended text automatically, with no separate HMIC action required to "pick up" the change. |

Security invariants **CBD-9** ("no `DeploymentBinding` write path is agent-reachable, directly or indirectly") and **CBD-10** ("`DeploymentBinding` revocation is field mutation, never deletion") are added to §19, extending CBD-1..8 without renumbering them.

## 6. Producer Responsibilities (Normative Summary)

Restated from §5's requirement text in the 14-step form the governing prompt's §20 anticipates, each step now traceable to a specific `HBDC-REQ-0##`:

1. Resolve subject (target repository) — admin-supplied path, not agent-supplied (HBDC-REQ-066).
2. Load `RepositoryIdentity`, read-only (HBDC-REQ-057).
3. Validate `canonical_deployment_root` via `resolve_canonical_deployment_root` (HBDC-REQ-057).
4. Validate `principal_id` against admin enrollment context (HBDC-REQ-058).
5. Validate `signer_key_id`/`provider_profile` against admin enrollment context (HBDC-REQ-058).
6. Validate `authority_scope` against admin enrollment context (HBDC-REQ-058).
7. Inspect existing binding entry for this `repository_id`, if any (HBDC-REQ-059).
8. Enforce uniqueness/idempotency (create: no-op on identical, fail on conflicting; HBDC-REQ-059).
9. Validate election evidence (HBDC-REQ-064/065).
10. Construct the binding record (closed schema, §4, unchanged).
11. Serialize canonically (existing `json.dumps(..., indent=2, sort_keys=True) + "\n"` convention, unchanged, matches HMIC-REQ-041's identical convention for the sibling record type).
12. Persist atomically (HBDC-REQ-063).
13. Verify read-back (implied by HBDC-REQ-063's atomicity discipline; explicit read-back check named in §9's implementation plan).
14. Emit audit evidence (HBDC-REQ-062).

## 7. Caller Architecture and Authority Model

**Caller:** a dedicated, non-agent-writable admin tool — mirroring HMIC-001's own `scripts/hatp_certification_admin.py`-class writer (§24 of the HMIC contract), never a `pcae` CLI subcommand an agent process routinely invokes. `pcae deployment binding {inspect|list}` (read-only) MAY exist on the ordinary CLI per HBDC-REQ-081-class reasoning already established for certification inspection; `create`/`rotate`/`revoke` MUST NOT.

**Human authority input model (item 22-24 of the governing prompt):** mirrors HMIC-REQ-076/077/078 exactly — the human never types a repository ID, root path, or an "approved=True" boolean. The tool derives every authority-sensitive field read-only and presents a computed target for human confirmation; the only human-entered fields are confirmation and a governance-decision reference string (e.g. a CHGR ID) recorded as audit metadata (HBDC-REQ-065), not cryptographically verified by the writer itself — the writer does not overclaim verification of the CHGR's own authenticity, scope, or currentness; that verification is a separate, existing governance-process concern (out-of-band human/admin judgment, exactly as HMIC-REQ-076 step 2 already frames "Protected Admin Authority reviews... out of band; human judgment; not this contract's concern").

**Authority-verification boundary:** the writer trusts the OS-level fact that only the admin principal can invoke it and write the Protected Root (HBDC-REQ-009, unmodified) as the actual enforcement boundary — identical to HMIC-REQ-079's own conclusion that the real boundary is OS file permissions, not an in-process check. The writer records the election reference; it does not itself authenticate the CHGR record's scope, target, or currentness.

## 8. Remaining Frozen Decisions

### 8.1 Repository Identity Prerequisite

`ensure_repository_identity()` remains a **separate**, non-election-gated operation (HBDC-REQ-068). The `DeploymentBinding` writer reads an *existing* `RepositoryIdentity` (HBDC-REQ-057) — it does not itself call `ensure_repository_identity()`. If none exists for the target tree, the writer fails closed (`repository_identity_missing`, §9's error taxonomy) rather than silently creating one. This preserves the explicit separation the governing prompt's item 25 requires: binding creation is a distinct, separately-governed election; repository-identity creation is not folded into it as an implicit side effect.

### 8.2 Repository-Identity Creation Authority Classification (Runtime Checkout)

Re-derived, not merely re-cited: HATP-REQ-048 ("identity creation alone grants no HATP authority... needs no human approval") and CHGR condition 6's exclusion list (verbatim, §2 above) — which names DeploymentBinding, Boundary C, Boundary A, Cutover Record, Permission Broker/POL-005/COMP-002, and repository onboarding, but **not** repository-identity creation — are unchanged by this phase. **Classification: routine repository initialization, not an authority-bearing mutation, not a prerequisite mutation requiring its own election.** Running `pcae init` (or `ensure_repository_identity`) against `/opt/pcae/runtime/src` remains, as an architecture fact, something a future phase *could* do without a fresh election — but this phase does not do it, and does not decide whether that future phase should combine it with the binding election (§8.3) or keep them separate; that is a first-use-workflow-design decision for the phase that actually drafts the election proposition, not a producer-contract decision.

### 8.3 Should Identity + Binding Share One Election?

**Recommendation, not a binding decision (out of this phase's authority to decide unilaterally): keep them separate.** Repository-identity creation needs no election at all (§8.2); bundling it into the binding election would suggest, incorrectly, that identity creation is itself authority-bearing. A future first-use proposition SHOULD state plainly "identity creation is a non-authority-bearing prerequisite step performed first; the election covers only the binding" rather than asking a human to approve both as one undifferentiated act.

### 8.4 Runtime-Source Subject (Unchanged)

The first real `DeploymentBinding`, when eventually created under a future election, would bind the PCAE runtime's own deployed source checkout (`/opt/pcae/runtime/src` on Dell) — the same tree HBDC-REQ-042's verifier already evaluates (7F §17, independently reconfirmed §2 above, unchanged by this phase). This does **not** onboard `/opt/pcae/projects/<repo-slug>/repo` — that remains a distinct, not-yet-designed future architecture area (7F §18, F2, unchanged, non-blocking).

### 8.5 Multi-Repository / Multi-Host Semantics (Unchanged)

The registry's `deployment_bindings` dict already supports many independently-keyed `repository_id` entries sharing one Protected Root (7F §21/§41, re-confirmed §2 above). No global "one active binding total" invariant is introduced by this amendment. A given `repository_id`'s single entry may bind at most one `canonical_deployment_root` at a time (schema-enforced, §2) — the same repository identity deployed to two hosts requires two independent `repository_instance_id`s (fresh `pcae init` per instance, unchanged CRI Model A rule), each with its own independent binding entry, not one binding entry naming two roots.

### 8.6 Timestamp Grammar Gap (New Finding, Non-Blocking, Deferred)

`hatp_bootstrap.py`'s `_parse_iso_timestamp`/`_require_timestamp` (used to validate `DeploymentBinding.valid_from`/`revoked_at` on **read**) accepts a materially looser grammar than the hardened `_TIMESTAMP_PATTERN` regex the 149O.1H phases established for `CutoverRecord`/`CertificationRecord` — and this looseness was **deliberate**, not an oversight: 149O.1H's own phase docs record `hatp_bootstrap.py` as explicitly out of that hardening wave's scope ("Wave 1/2 untouched"). This phase does not modify `hatp_bootstrap.py` (no `src/pcae/**` file is touched, §12). **Disposition:** HBDC-REQ-067 (§5) normatively binds the *future producer's own output* to the strict grammar regardless of the read-path's current permissiveness, so no real binding will ever be written in a noncanonical form even before the read-path itself is hardened. Whether to also tighten `_require_timestamp`'s read-path parsing to reject what it currently accepts is named here as **future work**, not resolved — it is a `src/pcae/**` code change, out of this phase's scope, and does not block this contract's freeze (no real binding exists yet for the looseness to have affected).

## 9. Implementation Plan (No Code Written This Phase)

### 9.1 Proposed Surfaces (names only, not committed to)

- **Core producer module:** a new function set in `hatp_bootstrap.py` (or a new sibling module, e.g. `hatp_deployment_binding_admin.py`, if keeping the read-only `HATPTrustStore` module byte-stable is preferred at implementation time — an open question for that phase, not decided here) implementing `create_deployment_binding()`, `rotate_deployment_binding()`, `revoke_deployment_binding()`.
- **Admin tool entrypoint:** `scripts/hatp_deployment_binding_admin.py`, mirroring `scripts/hatp_certification_admin.py`'s existing shape (HMIC-REQ-079's precedent) — a separate script, not a `pcae` CLI subcommand.
- **Read-only CLI additions (optional, later):** `pcae deployment binding {inspect|list}`, wrapping existing `HATPTrustStore` lookups; no write verb on the ordinary CLI (HBDC-REQ-056).
- **Schema changes:** none (§4.2, §4.5).
- **Tests:** unit tests for the producer's validation/idempotency/uniqueness/atomicity logic (isolated `tmp_path` trust-store fixtures, mirroring `test_hatp_bootstrap_foundation.py`'s existing fixture pattern); a producer→`HATPTrustStore`→`deployment_binding_matches()` round-trip test (§9.3); adversarial tests (§9.4).
- **Governance integration:** the admin tool's audit-evidence emission target is this repository's existing publication-execution/CHGR/governance-record infrastructure (HBDC-REQ-062) — no new audit schema.
- **Report integration:** a future implementation phase's canonical phase report should cite HBDC-REQ-056..070 by ID in its acceptance evidence, mirroring this phase's own citation discipline.

### 9.2 Error/Result Taxonomy (proposed, not frozen as production API)

`repository_identity_missing`, `authority_evidence_missing`, `authority_evidence_malformed`, `deployment_root_unresolvable`, `duplicate_conflicting_binding`, `binding_already_identical` (idempotent no-op, not an error), `signer_unknown`, `provider_profile_unknown`, `authority_scope_invalid`, `atomic_publication_failed`, `readback_mismatch`, `non_admin_caller` (defense-in-depth check; primary enforcement remains OS permissions per HBDC-REQ-066). Named here as a starting proposal for the implementation phase to adopt or revise — not frozen production vocabulary, unlike HBDC-REQ-042's own six-outcome vocabulary (§5 of 7F), which **is** frozen because it already exists in shipped code.

### 9.3 Producer/Consumer Round-Trip Test Plan

A future implementation phase's test suite MUST include: producer output → `HATPTrustStore.production()`-equivalent (test-only root) read → `_parse_deployment_binding` decode → `deployment_binding_matches()` → `True`, with the exact same `repository_id`/`canonical_deployment_root` pair the producer was given — proving no translation ambiguity between what the producer writes and what the existing, unmodified consumer chain already expects. **This phase does not modify `deployment_binding_matches()`, `_parse_deployment_binding`, or any other existing consumer** (item 62 of the governing prompt, honored).

### 9.4 Adversarial Test Plan (names only)

Missing `RepositoryIdentity`; malformed `RepositoryIdentity`; deployment-root mismatch; principal mismatch; duplicate active binding (conflicting); duplicate active binding (identical, idempotent); revoked-binding overwrite attempt without an explicit rotate operation; malformed registry document; unknown signer; unknown provider profile; invalid authority scope; malformed/noncanonical timestamp on writer input; symlink substitution on the registry path or its parent (reusing `_reject_symlink`'s existing discipline); interrupted atomic publication (crash between temp-write and rename); read-back mismatch; non-admin invocation attempt.

### 9.5 Preview/Dry-Run

A future producer implementation SHOULD support a read-only preview mode (exact target mutation, computed field values, existing-entry conflict/no-op classification, expected `deployment_binding_matches()` outcome) presentable to the human **before** the election is finalized — mirroring HMIC-REQ-076 step 5's "presents this computed tuple to the human for confirmation (a target, not a blank form)" pattern exactly. Not implemented this phase.

## 10. First-Use Workflow (Conceptual, Unexecuted)

1. Verify Boundary-P state (already independently established, 7E; not re-measured this phase, §2).
2. Verify `RepositoryIdentity` prerequisite/current absence for `/opt/pcae/runtime/src` (currently absent, unchanged).
3. Materialize the exact identity + binding proposition (a future phase's job).
4. Human election (fresh, separate, per CHGR condition 6).
5. Separate confirmation.
6. Publish CHGR.
7. Independently verify authority (a future, separately-governed step).
8. Create repository identity, if the election's own scoping treats it as a preceding routine step (§8.3's recommendation: keep separate from the binding election itself, though it may still be sequenced immediately before it procedurally).
9. Create `DeploymentBinding` atomically (admin tool, per §5-§7, once implemented and independently verified — §11).
10. Read back.
11. Re-run HBDC (Action 9).
12. Require the expected `deployment_binding_matches_repository_and_root`/`COMPLIANT`-contributing result.
13. Independent verification of the whole sequence.
14. Only then progress toward Boundary C preparation.

No step in this sequence is executed by this phase.

## 11. Recommended Next Phase

**149O.20L.7H — DeploymentBinding Producer Contract Independent Verification.** Must independently reconstruct and adversarially verify: HBDC-REQ-056..070's producer responsibilities; the F3/F4 resolutions in §4 (including whether "no schema change" truly holds under adversarial pressure); the lifecycle model (§4.5); active-binding uniqueness (unchanged, §4); the authority-input/verification-boundary model (§7); the `RepositoryIdentity`-prerequisite decision (§8.1); the binding-before-certification sequencing (unchanged from 7F, re-confirmed §2); and this implementation plan's sufficiency (§9) — including whether the proposed error taxonomy and test plan are adequate before any implementation phase begins. **No implementation in 7H.** Only after a clean 7H should an implementation phase build the producer, and that implementation would require its own separate independent verification before any first-use election (§10) may even be drafted.

## 12. Exact Changed Files (this phase)

```
docs/PHASE_149O_20L_7G_DEPLOYMENTBINDING_PRODUCER_CONTRACT_SCHEMA_EVOLUTION_AND_IMPLEMENTATION_PLANNING.md   (new — this document)
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md                                                            (amended — v1.0 -> v1.1, HBDC-REQ-056..070 added, CBD-9/CBD-10 added, §0/§27/§28/§29 updated)
tests/test_phase_149o_20l_7g_deploymentbinding_producer_contract_schema_evolution.py                          (new)
PROJECT_STATUS.md, CHANGELOG.md, tasks/**, .pcae/phase-completion-*.json/.md                                  (governance bookkeeping)
```

**Zero `src/pcae/**` files are modified.** No CLI file is modified. No schema-implementation code (`hatp_bootstrap.py`, `repository_identity.py`) is modified — only the *contract text describing future producer requirements* changes; the frozen `DeploymentBinding` dataclass and its validators are untouched, confirming §4.2/§4.5's "no schema change" conclusion is literally true at the code level, not merely at the narrative level.

## 13. Proof of No Producer Implementation, No DeploymentBinding Creation, No Dell Mutation

- No SSH session to any Dell host was opened this phase.
- `git diff --name-only <phase-entry>..HEAD -- src/pcae/` is empty (verified at commit time, §12).
- No `create_deployment_binding`, `rotate_deployment_binding`, `revoke_deployment_binding`, or any equivalently-named function was added anywhere in `src/pcae/**`.
- No `.pcae/repository-identity.json` was created (still absent in this repository's own working tree; never touched on Dell — no Dell access occurred).
- No `DeploymentBinding` was created (no write path exists in production code to have used, before or after this phase).
- No `scripts/hatp_deployment_binding_admin.py` or equivalent admin-tool file was created (§9.1 names it only as a future proposal).
- No CLI command was added. No Permission Broker, POL-005, or COMP-002 change was made. No HMIC certification was computed, requested, or granted. No Cutover Record was created. No Boundary C or Boundary A action was taken. No fresh, separate election for `DeploymentBinding` creation was initiated — CHGR condition 6 remains unsatisfied, as intended.

## 14. HBDC-REQ-042 State (Unchanged By This Phase)

**OPEN — SOLE HBDC RESIDUAL.** Live Dell reason, as last measured by 149O.20L.7E and not re-measured this phase (no Dell access occurred): `no_repository_identity_present`. Contract text now normatively defines how a `DeploymentBinding` would eventually be produced, but no real repository identity or binding exists on Dell or anywhere else as a result of this phase. This phase's changes do not, and are not claimed to, alter live HBDC state in any way.

## 15. Findings Disposition (All Prior + New)

| ID | Finding | 7F status | This phase's disposition |
|---|---|---|---|
| F1 | HBDC-REQ-042 text vs. verifier's stronger positive check — implicit mapping | Non-Blocking | Unchanged; not addressed by this amendment (out of this phase's charter, which is producer contract text, not REQ-042's own text) |
| F2 | No architecture connects HBDC-REQ-042 to a "managed application repository" concept | Non-Blocking (for REQ-042); Blocking (for future multi-repo work) | Unchanged; §8.4/§8.5 reaffirm the runtime-checkout-only subject explicitly |
| F3 | `DeploymentBinding`/`CertificationRecord` cross-consistency | Non-Blocking (REQ-042); Blocking (Boundary C design) | **RESOLVED NORMATIVELY** — value-derived consistency reaffirmed, no schema change (§4.1-4.2); narrower validation-time gap split out as F3-residual (§4.3, new, deferred, non-blocking) |
| F4 | No rotation/revocation write-path; schema-ready but unimplemented | Blocking (for any producer design) | **RESOLVED NORMATIVELY — IMPLEMENTATION PENDING** — full lifecycle model frozen (§4.4-4.5, HBDC-REQ-060/061), no schema change |
| F5 | `hatp_class_b_conformance.py` module docstring stale re: HMIC 28-file scope | Non-Blocking, documentation only | Unchanged; not touched (no `src/pcae/**` file modified this phase, §12) |
| F6 | No `DeploymentBinding` producer/creation mechanism exists | Blocking (for creation) | Unchanged as a code fact — still true after this phase (§13); now has a full normative contract (§5-§9) an implementation phase can build against, closing the *specification* gap without closing the *code* gap (deliberately — that is 7H/implementation's job, not this phase's) |
| F7 | No repository-identity rotate/revoke/repair/import/migrate mechanism | Non-Blocking | Unchanged; explicitly out of this phase's scope (§3's contract-home decision only concerns `DeploymentBinding`, not repository identity's own lifecycle gaps) |
| F3-residual | HMIC-REQ-103 validation does not re-check live `DeploymentBinding.status` | (new, this phase) | Named, deferred, non-blocking (§4.3) |
| Timestamp-grammar gap | `hatp_bootstrap.py`'s read-path timestamp parser is looser than the hardened grammar, deliberately, since 149O.1H | (new, this phase) | Named, deferred, non-blocking; producer's own future output bound to the strict grammar regardless (HBDC-REQ-067, §8.6) |

## 16. Governance Results (this phase)

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_status_coherence:** coherent
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated — same historical `tasks/done/`/`tasks/DONE.md` entries prior phases already carried forward; outside this phase's allowed-file scope; not remediated here)
- **pcae_push_check:** clean (nothing_to_push, at phase entry)
- **pcae_runtime_inspect:** Observed / observe / unavailable (unchanged)
- **pcae_notify_status:** telegram configured/enabled
- **pcae_phase_report_reconcile (149O.20L.7F):** reconciled, mutation none

## 17. Test Results

- **This phase's own companion module** (`tests/test_phase_149o_20l_7g_deploymentbinding_producer_contract_schema_evolution.py`): 68 passed, 0 failed — independently re-derived from primary source (contract text, `hatp_bootstrap.py`, `repository_identity.py`, `hatp_mandatory_cutover.py`, the CHGR record), not from this phase's own architecture document or from 7F's test module.
- **Full repository-wide `pytest -m fast_green` sweep, run twice this phase** to isolate this phase's own effect precisely:
  - **Baseline** (this phase's changes `git stash`-ed, i.e. `origin/main`/pre-phase state): **181 failed, 9 errors, 7406 passed** (`python -m pytest -m fast_green -q --tb=no`, full log captured).
  - **With this phase's changes restored**: **218 failed, 9 errors, 7437 passed** (companion module's 32 new-file-relative passes plus this delta account for the `+31` beyond `7406`; the 68-test companion module reports separately above because it is counted inside both runs' totals — the `+31` passed delta net of the 68 new passing tests and the 37 newly-failing ones nets out consistently with `7437 - 7406 = 31 = 68 - 37`).
  - **Delta analysis (exact, both full logs diffed by test node ID):** all pre-existing baseline failures (181/9) persist unchanged, confirmed by `comm -23` producing an empty result (nothing that failed at baseline now passes, and nothing baseline-passing silently vanished). Exactly **37 new failures** appear, and **zero** are unexplained: every one of the 37 is a historical phase-specific regression assertion of the form "the HBDC-001 contract file's bytes/version/requirement-count are unchanged since *that phase's own* entry" (e.g. `test_hbdc_contract_byte_unchanged_in_working_tree`, `test_hbdc_contract_still_declares_v1_0`, `test_55_unique_gapless_requirement_ids`, `test_hbdc_contract_byte_identical_since_phase_entry`, spanning `test_phase_149o_20b_*` through `test_phase_149o_20l_7e_*`). **Classification (per this phase's charter, item 86): tests require migration, not a contradiction.** Every one of these tests encoded an implicit assumption — "this contract's bytes/version will never change" — that was always going to be falsified by any legitimate future HBDC-001 amendment, exactly as already happened repeatedly to the sibling HMIC-001 contract's own v1.0→v1.1→v1.2→v1.3 amendment history (§50-52 of the HMIC contract) without those older HMIC-pinning tests being treated as revealing a defect. None of the 37 failures assert anything about `DeploymentBinding`'s schema, `HATPTrustStore`'s write-method count, or any other fact this phase's own contract text claims — they assert only "no HBDC-001 edit has yet occurred," which this phase's intentional, in-scope v1.1 amendment necessarily falsifies.
  - **Remediation:** out of this phase's allowed-file scope (updating dozens of `tests/test_phase_149o_*.py` files spanning 149O.20B through 149O.20L.7E is not on this task's allowed-file list and would be a large, unrelated, cross-cutting change). Named here explicitly, not concealed, as **future work** for a dedicated test-migration phase (or folded into 149O.20L.7H's own scope if that phase's charter is written to include it) — mirroring how prior phases (7E, 7F) named, rather than silently absorbed or remediated, pre-existing red gates outside their own allowed-file scope.
- **No other regression class exists.** No test outside the 37-item byte/version-pinning set changed status in either direction.

Also reflected in this phase's canonical report (`.pcae/phase-completion-report.md`) and `pcae phase-report show --latest`.

## 18. Expected Clean Outcome (this phase's exit state)

```
Dell Boundary P                    INDEPENDENTLY VERIFIED PROVISIONED (149O.20L.7E, unchanged)
HBDC                                NON_COMPLIANT — SOLE RESIDUAL HBDC-REQ-042
RepositoryIdentity producer         EXISTING — UNCHANGED
DeploymentBinding producer contract FROZEN / DEFINED (HBDC-001 v1.1, HBDC-REQ-056..070)
DeploymentBinding producer impl.    NOT IMPLEMENTED
RepositoryIdentity artifact (Dell)  NOT CREATED
DeploymentBinding (Dell)            NOT CREATED
HMIC                                 DEPLOYED SOURCE IDENTITY NOT CERTIFIED
Boundary C                          NOT AUTHORIZED
Boundary A                          NOT AUTHORIZED
HATP                                 NOT READY
Runtime                              Observed / observe / unavailable
```

## 19. Final Verdict

**CONTRACT/SCHEMA EVOLUTION COMPLETE — READY FOR INDEPENDENT VERIFICATION.**

The normative producer model (caller, inputs, validation, uniqueness, idempotency, atomicity, fail-closed rules, audit evidence, authority-input boundary, lifecycle) is complete and implementation-ready (§5-§9). No schema change to `DeploymentBinding` or `CertificationRecord` was required (§4.2, §4.5) — both existing schemas, as independently re-verified this phase (§2), are sufficient to express the frozen semantics. No architecture contradiction was found; every 7F conclusion re-derived this phase held (§2), with two additional, non-blocking findings named (§4.3, §8.6) that do not change this verdict.
