# Phase 149O.20L.7O — RepositoryIdentity + DeploymentBinding First-Use Proposition Preparation

## 0. Status

**Proposition preparation / architecture materialization only.** No RepositoryIdentity created (real Dell or local). No DeploymentBinding created. No producer `create`/`rotate`/`revoke` invoked against Dell or against any real trust store. No human election initiated. No CHGR published. No HMIC certification performed. Boundary C, Boundary A, and HATP_MANDATORY activation remain untouched and **NOT AUTHORIZED**. All Dell access this phase was strictly read-only (SSH `git rev-parse`/`git status`/`ls`/`cat` and read-only Python imports/function calls, all via `sudo -n` as either `codex` or the `pcae` OS principal — never a write, never `create_deployment_binding`, never `ensure_repository_identity`). No `src/pcae/**`, `scripts/**`, `docs/contracts/**`, or `schemas/**`/`pyproject.toml` file was modified.

**Phase-entry commit:** `4bb04018` (`Phase 149O.20L.7N.5: sync phase_commits list and task allowed-file list`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

**Entering independently verified state (carried forward from 149O.20L.7N.5, re-confirmed live this phase, §5 below):**

| Fact | Value |
|---|---|
| Dell source (`/opt/pcae/runtime/src`) | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` — **INDEPENDENTLY VERIFIED DEPLOYED** |
| Dell Boundary-P physical state | **INDEPENDENTLY VERIFIED** (unchanged since 149O.20L.7E/7D.11) |
| HMIC-001 | v1.4, 30-member frozen source set |
| `implementation_scope_digest` | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` — **IMPLEMENTATION/SOURCE IDENTITY INDEPENDENTLY VERIFIED DEPLOYED — NOT CERTIFIED** |
| Live HBDC diagnostic | `NON_COMPLIANT`, sole residual `HBDC-REQ-042: no_repository_identity_present` (re-confirmed live, §5.3) |
| RepositoryIdentity | Absent |
| DeploymentBinding | Absent |
| Certification | Absent |
| Boundary C / Boundary A / HATP | Not authorized / not authorized / not ready |
| Runtime | Observed / observe / unavailable |

## 1. Purpose and Method

Phase 149O.20L.7M selected the **two-transition model** for Transition 2 (RepositoryIdentity + DeploymentBinding first use): Transition 1 (source redeployment, now complete per 7N–7N.5) is fully independent of Transition 2. This phase does not rely on 7M's prose as an oracle — every load-bearing claim below (`_generate_repository_identity`'s use of `uuid.uuid4()`, `ensure_repository_identity`'s idempotency, `preview_create_deployment_binding`'s dependency on a pre-existing identity, HBDC-REQ-042's evaluation logic, CHGR condition-6-equivalent text, HMIC's own dependency on `RepositoryIdentity`) was independently re-read from the current production source in this session and, where feasible, independently exercised in a disposable local simulation and confirmed live on Dell read-only. Where this phase's findings match 7M's, that is stated as independent re-confirmation, not inheritance. Where this phase's conclusion differs from 7M's plan (§8 below), that is stated explicitly as a deviation, with reasoning.

This phase prepares — but does not publish or elect — the exact first-use proposition for RepositoryIdentity + DeploymentBinding creation, and stops before any Boundary C activity.

## 2. Entry Checks (read-only)

```
cd ~/repos/pcae-harness
git status --short                          → (clean)
git status --branch --short                 → ## main...origin/main
git log --oneline -180                      → HEAD = 4bb04018, linear 149O chain
git log --oneline origin/main..HEAD          → (empty)
git rev-list --count origin/main..HEAD       → 0
pcae health                                  → healthy, git clean, agent lock held by claude-local
pcae check                                   → passed
pcae status coherence                        → coherent
pcae doctor task-memory                      → warnings (pre-existing: historical tasks/done/ entries
                                                predating this phase not listed in tasks/DONE.md; carried
                                                forward unrepaired, outside this phase's allowed-file scope,
                                                identical disposition to 149O.20L.7N.5's own entry)
pcae push check                              → clean, nothing_to_push
pcae runtime inspect                         → Observed / observe / unavailable
pcae notify status                           → telegram configured/enabled
pcae phase-report show --latest              → 149O.20L.7N.5 canonical report consistent; recommended
                                                next phase = 149O.20L.7O (this phase)
pcae phase-report reconcile --phase-id 149O.20L.7N.5
                                              → reconciled, 2 generations promoted, marker
                                                already_dispatched, checkpoint completed, receipt
                                                finalized, mutation: none (inspection only)
```

No mutation performed by any of the above.

## 3. Transition-2 Architecture Reconstructed From Primary Source (Dependency Order)

Read directly this session (not from 7M's citations):

1. **`src/pcae/core/repository_identity.py`** — `RepositoryIdentity` (CRI Model A Layer 1). `ensure_repository_identity(root)`: idempotent — reads existing identity first; only generates+writes if genuinely absent; fails closed (`RepositoryIdentityMalformedError`) if present-but-invalid; never silently regenerates. `_generate_repository_identity()` calls `uuid.uuid4()` directly — no parameter anywhere accepts a caller-supplied or preselected UUID. Confers no authority by itself (module docstring, HATP-REQ-051/063: "possession, knowledge, copying, or modification of the identifier defined here SHALL NOT by itself grant any approval authority"). Path: `.pcae/repository-identity.json`, git-ignored (`.pcae/.gitignore` line 4).
2. **`src/pcae/core/hatp_bootstrap.py`** — CRI Layer 2. Defines `DeploymentBinding` (9 fields, §9 below), `HATPTrustStore` (read-only production interface, zero write methods), `deployment_binding_matches()` (the copy/clone/theft defense: requires `status == "active"` and both `repository_id` and `canonical_deployment_root` to match), `resolve_canonical_deployment_root()`, and the fixed Protected Root paths (`/etc/pcae/hatp/trust-store` on Linux, never derived from `$HOME`/env/CLI).
3. **`src/pcae/core/hatp_deployment_binding_admin.py`** (Phase 149O.20L.7I) — the producer: `create_deployment_binding`, `rotate_deployment_binding`, `revoke_deployment_binding`, plus read-only `preview_create_deployment_binding`/`preview_rotate_deployment_binding`/`preview_revoke_deployment_binding`. `_resolve_repository_id()` calls `read_repository_identity()` only — **never** `ensure_repository_identity()` — and raises `RepositoryIdentityMissingError` if absent. This is the single most important dependency-order fact: **the producer will never create an identity as a side effect; RepositoryIdentity must already exist, as a separate, prior step, before any binding operation (including preview) can run at all.**
4. **`src/pcae/core/hatp_class_b_conformance.py`** — `verify_class_b_deployment_conformance()` / `_check_deployment_identity()` (HBDC-REQ-042..046): reads `RepositoryIdentity`, then `HATPTrustStore.production().load_repository_enrollment(...)`, then calls `deployment_binding_matches()` unchanged. On a host with no identity, reports `NON_COMPLIANT`/`no_repository_identity_present` — never `COMPLIANT` by default. Strictly read-only, non-authoritative (own docstring: "MUST NOT be consumed by `hatp_mandatory_cutover.py`... until a future, separately-governed phase evolves HMIC's source scope").
5. **`src/pcae/core/hatp_mandatory_certification.py`** — HMIC certification's own repository-identity resolver (`_resolve_current_repository_instance_id` equivalent) also calls `read_repository_identity()` and fails closed (`RepositoryIdentityUnavailableError`) if absent — a second, independent downstream consumer confirming RepositoryIdentity must exist before certification, not merely before binding.
6. **`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`** — HBDC-REQ-042 ("`repository_instance_id` confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding`"), HBDC-REQ-064/065/066 (fresh-election-evidence requirement, election-reference recorded as audit metadata only, admin-OS-principal-only writer), HBDC-REQ-069 ("does not itself satisfy... any governing-CHGR-instance's own election-condition text... e.g. a condition excluding `DeploymentBinding` creation without a fresh, separate election").

**Dependency order, confirmed:** RepositoryIdentity (unelected, idempotent, host-local) → DeploymentBinding (elected, admin-only, requires #1 already persisted) → HBDC-REQ-042 evaluation (requires #1+#2 both present and matching) → HMIC certification (requires #1 present; separately requires HBDC/topology/environment-lock evidence; not attempted this phase or authorized by this phase).

## 4. RepositoryIdentity Generation Semantics — Independently Reconfirmed

Read `_generate_repository_identity()` directly (`repository_identity.py:202-208`):

```python
def _generate_repository_identity(now: Optional[datetime] = None) -> RepositoryIdentity:
    timestamp = now or datetime.now(timezone.utc)
    return RepositoryIdentity(
        schema_version=SCHEMA_VERSION,
        repository_instance_id=str(uuid.uuid4()),
        created_at=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )
```

Confirmed:
- **`uuid.uuid4()`, no caller-supplied UUID** — no parameter anywhere in `repository_identity.py` accepts a preselected value.
- **No deterministic seed.**
- **No persist-free preview mode** — `ensure_repository_identity()` is the only production entry point; generation and atomic persistence happen in the same call, unconditionally, the first time it is invoked on a repository lacking an identity. There is no `preview_ensure_repository_identity` or equivalent anywhere in the module.
- **No "prepare then publish" API.**

Semantics are unchanged since 7M (§35 of that document reached the identical conclusion; this is independent re-confirmation, not inheritance — verified by direct source read and by the disposable simulation in §7 below, which reproduced `RepositoryIdentityMissingError` before identity creation and confirmed idempotency across two calls).

## 5. Read-Only Dell Preview Feasibility (Producer Now Deployed)

Dell (`hac-dell`) was reachable this session over SSH. Every command below is read-only; none mutated Dell.

### 5.1 Source/git state (as `codex`, no privilege needed for these)

```
$ ssh hac-dell 'cd /opt/pcae/runtime/src && git rev-parse HEAD'
→ Permission denied (root:pcae 0750, codex not in pcae group)
```

Re-run via `sudo -n` (codex has passwordless `(ALL:ALL) NOPASSWD:ALL`; only read verbs were ever issued):

```
$ sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
b0840e96a7ffb12308e95828aa5927c3e7c770c0        # exact match to entering state, §0
$ sudo -n git -C /opt/pcae/runtime/src status --porcelain=v1
(empty — clean)
$ sudo -n git -C /opt/pcae/runtime/src symbolic-ref -q HEAD
(exit 1 — detached, no symbolic ref, as expected)
```

### 5.2 Identity / binding absence (read-only inspection)

```
$ sudo -n ls -la /opt/pcae/runtime/src/.pcae/repository-identity.json
ls: cannot access ...: No such file or directory        # absent, confirmed
$ sudo -n ls -la /etc/pcae/hatp/trust-store
drwxr-x--- 2 root pcae 4096 Aug 15 08:55 .
drwxr-xr-x 3 root root 4096 Aug 15 08:55 ..              # exists, empty, admin-owned as expected
$ sudo -n cat /etc/pcae/hatp/trust-store/registry.json
cat: ...: No such file or directory                       # absent → DeploymentBinding absent
```

### 5.3 Producer availability + HBDC diagnostic (as the real `pcae` OS agent principal, via the production launcher's own PATH convention)

The agent OS principal on Dell is `pcae` (uid 1004, `/usr/sbin/nologin`, group-readable access to `/opt/pcae/runtime/**`). Running as `codex`/root directly (via bare `sudo -n python3 -c ...`) produces **spurious** extra environment-lock failures (`agent_is_owner_with_write_bit` etc.) because root satisfies "owner" conditions the check is not designed to evaluate against — this is not a real state finding, it is an artifact of invoking the diagnostic as the wrong OS identity, and an early attempt in this session reproduced exactly that artifact before being corrected. The correct read is `sudo -n -u pcae`, from the deployed repository root, with `PATH` including the venv's `bin/` (matching `HBDC-REQ-036`'s `shutil.which("pcae")` launcher-detection check):

```
$ sudo -n -u pcae bash -c 'cd /opt/pcae/runtime/src && \
    PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
    /opt/pcae/runtime/venv/bin/python3 -c "
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
r = verify_class_b_deployment_conformance()
print(str(r.status))
for c in r.checks:
    if not c.satisfied: print(c.check_id, c.status)
print(\"#\", len(r.checks))
"'
ClassBConformanceStatus.NON_COMPLIANT
HBDC-REQ-042 no_repository_identity_present
# 34
```

**34 checks total, exactly one failing (`HBDC-REQ-042`)** — independently re-derived, matches 149O.20L.7N.5's own finding exactly, no drift.

```
$ sudo -n -u pcae /opt/pcae/runtime/venv/bin/python3 -c "
from pcae.core import hatp_deployment_binding_admin as m
print(m.__file__)
print(hasattr(m, 'create_deployment_binding'), hasattr(m, 'preview_create_deployment_binding'))
"
/opt/pcae/runtime/src/src/pcae/core/hatp_deployment_binding_admin.py
True True
$ sudo -n /opt/pcae/runtime/venv/bin/python3 /opt/pcae/runtime/src/scripts/hatp_deployment_binding_admin.py --help
usage: hatp_deployment_binding_admin.py [-h] {create,rotate,revoke} ...
Protected-admin HBDC-001 v1.1 DeploymentBinding create/rotate/revoke ceremony.
Not reachable from the ordinary pcae CLI or any agent-executed code path...
```

**Producer confirmed physically present and importable on Dell. Admin script confirmed present, `--help` only invoked — no `create`/`rotate`/`revoke` ever called.**

### 5.4 What can and cannot be previewed on Dell today

- **Possible today (read-only, no identity needed):** target root (`/opt/pcae/runtime/src`, confirmed resolvable), current trust-store state (exists, empty, correct ownership `root:pcae 0750`), producer/admin-script presence and importability, expected mutation shape (schema, field provenance — §9).
- **Impossible today, because `repository_id` is missing:** an *exact* `preview_create_deployment_binding()` call on Dell — it calls `_resolve_repository_id()` first, which raises `RepositoryIdentityMissingError` before any preview logic runs. Confirmed directly in the disposable simulation (§7) by reproducing the identical exception locally against a synthetic repository with no identity. **This is the load-bearing fact of the Repository-ID Preview Problem (§6): there is no way, today, to preview even the shape of a real Dell `DeploymentBinding` without first creating a real Dell `RepositoryIdentity`.**

No RepositoryIdentity, DeploymentBinding, or trust-store write was performed against Dell at any point in §5.

## 6. The Repository-ID Preview Problem — RI-A/B/C/D Analysis

### 6.1 Facts established (§4, §5.4, §7)

- `repository_id` is generated by `uuid.uuid4()` with no caller input, no seed, no persist-free mode (§4).
- `ensure_repository_identity()` is idempotent: exists → returned unchanged; missing → generated once, atomically; malformed → fails closed, never silently regenerated (§4, §7).
- The producer's `preview_create_deployment_binding()` — the only read-only preview capability that exists — requires an *already-persisted* `RepositoryIdentity`; it never calls `ensure_repository_identity()` itself (§3 item 3, §7).
- Consequently: **there is currently no code path, anywhere in this repository, that can produce an exact preview of a future `DeploymentBinding.repository_id` before a real `RepositoryIdentity` has actually been created.**

### 6.2 Candidate models, scored on authority precision (§7 of the governing prompt: target repository, exact mutation path, identity-generation mechanism, exact resulting `repository_id`, exact `DeploymentBinding.repository_id`, exact deployment root, principal, signer, provider profile, authority scope, timestamp-generation semantics, expected HBDC result)

| Field | RI-A (rule-only) | RI-D (identity created first, unelected) |
|---|---|---|
| Target repository | Known | Known |
| Exact mutation path | Known (file paths, functions) | Known |
| Identity-generation mechanism | Known (the rule) | Known, **and already executed** |
| Exact `repository_id` value | **Unknown at election time** | **Known at election time** (real value, read back) |
| Exact `DeploymentBinding.repository_id` | Unknown (bound by equality invariant only) | Known exactly |
| Exact `canonical_deployment_root` | Unknown pre-deployment (host-dependent) — but **known now**, since source is already deployed (§5.1) and can be resolved read-only | Known exactly |
| Principal / signer / provider / scope | Must still be resolved as enrollment context (§9.3-9.6) — same under both models | Same |
| Timestamp semantics | Rule only (`_canonical_timestamp_now()` at execution) | Rule only (identical — `valid_from` is always execution-time, regardless of when identity was created) |
| Expected HBDC result | `COMPLIANT`, modeled (§8, §11) | `COMPLIANT`, modeled — identical |

**RI-A is strictly less precise than RI-D on exactly one dimension that matters most: the concrete `repository_id`/`canonical_deployment_root` values a human would see in the proposition.** Every other field is resolved identically under both models. RI-B and RI-C are addressed for completeness:

- **RI-B (build a persist-free preview capability first):** would require new production code (`preview_ensure_repository_identity` or equivalent) that does not exist today (§4). This is an implementation-phase undertaking, not something this proposition-preparation phase may build (out of scope: "must not... invoke create/rotate/revoke", and no implementation work was authorized). Rejected for *this* phase on scope grounds, not on merits — it is not architecturally wrong, merely not something 7O may build.
- **RI-C (three-transition model: a first, dedicated election solely to authorize RepositoryIdentity creation, then a second, separate election for the binding):** RepositoryIdentity creation independently reconfirmed (§4, docstring text: "possession, knowledge, copying, or modification of the identifier defined here SHALL NOT by itself grant any approval authority") to confer **no authority whatsoever** by itself. Requiring a full election for a mutation that is defined, in the production code's own governing invariant, to carry zero authority would not be more careful — it would be governance theater around a fact the architecture itself has already settled. Rejected: unnecessary election overhead with no precision benefit RI-D does not already deliver for free.
- **RI-D (the model demonstrated by current architecture — selected, §6.3):** RepositoryIdentity creation is an **unelected administrative prerequisite step** (confirmed to require no election, §4, §6.1), performed once — idempotently, so a retry never produces a second, different identity (§7) — immediately before the `DeploymentBinding` proposition is drafted against the now-real, known value. Exactly **one** election is then required, and it governs `DeploymentBinding` creation only, with full precision on every field the current architecture is capable of resolving in advance.

### 6.3 Selected model: **RI-D**

RI-D is not chosen to minimize phase count (the governing prompt explicitly forbids that reasoning) — it is chosen because it is the only one of the four that delivers an **exact**, not rule-bound, proposition without requiring new production code (RI-B) or an authority-free election (RI-C). This independently re-derives 7M §15/§19/§27/§29's own conclusion (the "two-transition model," internally two-part: unelected identity step, then elected binding step) from primary source in this session, rather than inheriting it.

### 6.4 Downstream equality invariant (still required, defense-in-depth)

Even under RI-D, the future execution step must still enforce: **the `repository_id` read back immediately after identity creation MUST be the exact value used, unchanged, as `DeploymentBinding.repository_id`.** `create_deployment_binding()`'s own implementation already enforces this by construction — it calls `_resolve_repository_id()` internally and never accepts a caller-supplied `repository_id` for the binding (§3 item 3) — so this invariant is structurally guaranteed by the producer's own signature, not merely a documentation promise. No separate enforcement code is needed; this is confirmed, not assumed, by reading `create_deployment_binding`'s signature (`repository_root`, `authority`, `_protected_root` only — no `repository_id` parameter at all).

### 6.5 Generation count / idempotency (§47-48 of the governing prompt)

Confirmed by direct source read and by the disposable simulation (§7): **exactly one `uuid.uuid4()` generation attempt is ever made per repository**, by construction — `ensure_repository_identity()` reads existing state first and only generates on genuine absence; a retry after a partial failure (identity created, binding not yet attempted) re-reads the *same* persisted identity rather than generating a new one. This makes RI-D **safe under retry**: a first-use execution phase that fails after identity creation but before binding creation, and is then retried, will encounter the same `repository_id` both times — no re-generation, no drift.

## 7. Disposable Local Simulation (No Dell Mutation)

Executed entirely against throwaway `tempfile.mkdtemp()` directories on this Mac (`/private/var/folders/.../pcae-7o-sim-repo-*`, `/private/var/folders/.../pcae-7o-sim-trust-*`), using the producer's own private `_protected_root=` test-only seam — never the real Protected Root, never this repository's own `.pcae/`. Both directories deleted at the end of the run.

Sequence and results:

1. `read_repository_identity()` on the empty synthetic repo → `None`.
2. `preview_create_deployment_binding(...)` before identity exists → **`RepositoryIdentityMissingError`** (exact reproduction of the Dell-today constraint, §5.4).
3. `ensure_repository_identity(...)` → synthetic identity generated (`364d91d4-37f2-41d0-bb0d-ed478c5fb738`, schema_version 1, strict-grammar `created_at`).
4. `ensure_repository_identity(...)` called again → **identical value returned**, confirming idempotency (§6.5).
5. `preview_create_deployment_binding(...)` now succeeds → `kind=WOULD_CREATE`, exact candidate binding shown (all 9 fields populated, `authority_scope`/`principal_id`/etc. as supplied, `repository_id` matching step 3 exactly).
6. `create_deployment_binding(...)` → `outcome=CREATED`, binding persisted and read back.
7. HBDC-REQ-042's own matching function, `deployment_binding_matches()`, run directly against the synthetic pair → **`True`** — the exact mechanism that flips the residual, exercised, not merely reasoned about.
8. `create_deployment_binding(...)` retried with identical authority fields → `outcome=ALREADY_SATISFIED`, same `valid_from` as step 6 (no silent refresh) — confirms the producer's own idempotent-preserve comparison discipline (HBDC-REQ-059) live.

Full script and output are reproducible; not committed to the repository (disposable scratch artifact, synthetic values clearly labeled throughout, per governing-prompt §34).

## 8. Deviation From 7M's Literal Phase Sketch — Disclosed

7M §48 step 6 (its own hypothetical "7R") described RepositoryIdentity creation as occurring **inside** the proposition-preparation phase, immediately before drafting the binding proposition — i.e., 7M's own plan would have had *this* phase (7O) create the real Dell RepositoryIdentity to achieve RI-D's full precision now. **This phase's own governing prompt explicitly forbids that** ("It must not: create RepositoryIdentity... invoke create/rotate/revoke against the real Dell trust store"), which is a stricter, more conservative boundary than 7M anticipated.

Consequence: RI-D's full-precision benefit (§6.2 table) is **not yet realized by this phase** — it remains available to whichever future phase is authorized to perform the unelected identity-creation step. §10 revises 7M §48's phase decomposition to insert that step explicitly as its own governed sub-phase (still pre-election, still no election required per §6.3, but its own dedicated phase boundary and independent verification, consistent with this project's unbroken pattern of never combining a real mutation with its own independent verification, 7M §49).

This phase's own proposition (§9-10) is therefore an **exact specification of the generation rule + downstream equality invariant**, not (yet) a proposition naming the literal generated UUID — full RI-D precision is deferred to the sub-phase in §10 step 1, not abandoned.

## 9. DeploymentBinding Field Resolution

Schema (`hatp_bootstrap.DeploymentBinding`, unchanged by the producer per its own module docstring, "this phase adds zero fields"):

```python
@dataclass(frozen=True)
class DeploymentBinding:
    repository_id: str                 # (1)
    canonical_deployment_root: str     # (2)
    principal_id: str                  # (3)
    signer_key_id: str                 # (4)
    provider_profile: str              # (5)
    authority_scope: str               # (6)
    valid_from: str                    # (7)
    status: str                        # (8)
    revoked_at: Optional[str] = None   # (9)
```

1. **`repository_id`** — not knowable exactly until identity creation (§6); the generation rule + downstream equality invariant (§6.4) is what this proposition binds today. Not RI-A's "unbindable" weakness — it is a defense-in-depth invariant the producer already enforces structurally (§6.4), layered on top of §10's revised sequencing which resolves it exactly before election.
2. **`canonical_deployment_root`** — `resolve_canonical_deployment_root(Path("/opt/pcae/runtime/src"))`. Read-only-resolvable *today* (source already deployed, §5.1) — this is the one field 7M could not resolve exactly (source not yet deployed at 7M's time) that this phase now can. Confirmed the target is `/opt/pcae/runtime/src` (the PCAE runtime's own deployed checkout) — **not** a future managed-project repository (7M §39/7F §18/§42, re-confirmed: no such concept exists in current architecture).
3. **`principal_id`** — **not resolvable from source; no canonical derivation formula, registry, or fixed vocabulary exists anywhere in this repository** for this value (HBDC-REQ-058 explicitly draws it from "the admin's own enrollment context," cross-validation against any `principals`/`signers` registry explicitly deferred, 149O.20L.7H finding). Must be resolved as a genuine administrative enrollment decision by whichever future phase drafts the exact binding proposition — **not assumed equal to a Unix username or any other convenient stand-in.** This document does not invent a value.
4. **`signer_key_id`** — same disposition as (3): no current candidate value exists in the architecture; must be resolved administratively, not invented here.
5. **`provider_profile`** — same disposition.
6. **`authority_scope`** — same disposition; explicitly **no wildcard/broader default** — the producer validates only non-empty-string shape (§3 item 3), so a narrow, explicit scope must be chosen deliberately by the enrollment decision, not defaulted.
7. **`valid_from`** — `_canonical_timestamp_now()`, generated fresh at the moment of execution, strict grammar (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`, HBDC-REQ-067). Not knowable as an exact future wall-clock value pre-election; the proposition must bind the **generation rule**, not a fabricated exact timestamp (§37 of 7M, re-confirmed here — no code path accepts a caller-supplied `valid_from`).
8. **`status`** — `"active"` on first creation. Confirmed the only two values the schema's `_STATUS_VALUES` frozenset allows are `{"active", "revoked"}`; creation always sets `"active"`.
9. **`revoked_at`** — `None` on first creation (`_require_revoked_at_consistency`: status `"active"` requires `revoked_at is None`, enforced on read *and* on write). Only a later `revoke_deployment_binding()` call sets it.

## 10. Revised Future Phase Decomposition

Revises 7M §48 to reflect §8's disclosed deviation (identity creation deferred out of *this* phase) while preserving 7M's own "never combine mutation with its own independent verification" discipline (7M §49):

1. **149O.20L.7O** *(this phase)* — architecture reconstruction, RI-model selection, field resolution, disposable simulation, read-only Dell preview feasibility. No mutation. *(Complete.)*
2. **149O.20L.7O.1** — Independent verification of this phase's factual claims (mirrors 7N→7N.1's pattern). Read-only.
3. **149O.20L.7O.2** — **RepositoryIdentity creation on Dell** (administrative, unelected step — confirmed to require no election, §6.1/§6.3) immediately followed by drafting an **exact** `DeploymentBinding` proposition against the now-real `repository_id` (resolving `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` as a genuine enrollment decision, §9). This is the one real mutation in this entire chain prior to election — it is authority-free by construction (§6.1) but is still its own dedicated, independently-verified phase, never combined with the election that follows.
4. **149O.20L.7O.3** — Independent verification of 7O.2's exact proposition (repository_id read back matches; canonical_deployment_root matches; every other field traceable to a real enrollment decision, not invented).
5. **149O.20L.7O.4** — Human election (APPROVE/DECLINE/AMEND) + CHGR publication for `DeploymentBinding` creation only. Publication only, no Dell mutation in the same phase (mirrors `chgr-0e37ed...`'s own rationale).
6. **149O.20L.7O.5** — First-use execution: real `create_deployment_binding()` call, immediate audit-record-presence re-verification (carried-forward finding, §11), live HBDC re-adjudication against §11's expected `COMPLIANT`, STOP-and-adjudicate per §11.2 if it differs.
7. **149O.20L.7O.6** — Independent real-host verification of 7O.5's outcome.
8. **149O.20L.7O.7** — Boundary-C preparation. Only after step 7 confirms `COMPLIANT` — still not Boundary-C authorization itself.

Exact letter/number assignment is left to whichever phase actually opens 7O.1, per this project's convention of assigning at task-creation time.

## 11. Disposable HBDC Simulation and Expected Post-First-Use State

### 11.1 Modeled result (§7's simulation; not a live Dell claim)

Once (a) candidate source is deployed on Dell (**already true**, §0/§5.1), (b) a valid `RepositoryIdentity` exists there, and (c) a valid, active, matching `DeploymentBinding` exists in the Protected Root, and Boundary-P physical state remains intact (independently verified unchanged, §0) — the disposable simulation (§7 step 7) directly exercised the exact `deployment_binding_matches()` logic `HBDC-REQ-042`'s check calls and confirmed it flips to `True` under a matching synthetic pair. Combined with the live Dell diagnostic (§5.3: 34 checks, only `HBDC-REQ-042` failing today), the expected live post-first-use `verify_class_b_deployment_conformance()` result is **`COMPLIANT`** — modeled, not measured; only a future live measurement (7O.6) can establish it for real.

### 11.2 Unexpected-HBDC policy

If a future first-use execution phase's live HBDC result differs from §11.1's expected `COMPLIANT` (including: `HBDC-REQ-042` still failing, any other requirement newly failing, a repository-ID mismatch, a binding mismatch, or an unexpected malformed trust-store state), that phase must **STOP**, not certify, not repair, and not broaden authority to explain the discrepancy — mirroring `chgr-0e37ed...`'s own condition-5 STOP-for-read-only-adjudication pattern, independently re-affirmed here.

### 11.3 HBDC-COMPLIANT does not trigger anything automatically

`verify_class_b_deployment_conformance()`'s own module docstring states its result "MUST NOT be consumed by `hatp_mandatory_cutover.py` or any other authority-bearing production code path" until a future, separately-governed phase evolves HMIC's source scope to include it — confirmed unchanged this session. A `COMPLIANT` result remains **evidence only**; it does not itself authorize certification, Boundary C, or activation.

## 12. RepositoryIdentity Artifact — Location, Cleanliness, HMIC-Digest Consequence

- **Path (production):** `/opt/pcae/runtime/src/.pcae/repository-identity.json`.
- **Schema:** `{"schema_version": 1, "repository_instance_id": "<uuid4>", "created_at": "<ISO-8601Z, ms precision>"}` — closed field set, unknown fields rejected on read (`validate_repository_identity_document`).
- **Ownership/mode:** `tempfile.mkstemp` default (`0600`) via `_write_atomic`; no explicit `chmod` is issued — no group/world-readable mode is deliberately set.
- **Atomicity/idempotency/failure behavior:** `mkstemp` in the same directory → `fsync` → `os.replace`; symlink rejection on target and parent, both before and after write (§4). Exists+valid → unchanged; missing → generated once; exists+malformed → fails closed, never auto-repaired.
- **Audit/provenance:** none beyond the file write itself — `ensure_repository_identity()` performs no separate `append_provenance_event` call (confirmed: no such import in `repository_identity.py`).
- **Git-ignore/cleanliness:** confirmed this session — `.pcae/.gitignore` line 4 lists `repository-identity.json` verbatim. **Expected effect after creation: `git status --short` on Dell remains unchanged** (the file is untracked and ignored) and the tracked-byte identity of this Mac repository's own `.pcae/` tree is unaffected — no `git status` delta is expected from RepositoryIdentity creation on Dell, ever.
- **HMIC-digest consequence:** `.pcae/repository-identity.json` is git-ignored and never enters this repository's tracked tree; `implementation_scope_digest` is computed only over the 30-member frozen *tracked source* set (`_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`), which does not and cannot include a git-ignored runtime artifact. **Proven, not assumed:** RepositoryIdentity bytes are structurally outside the 30-member HMIC digest scope by the same mechanism (git-tracked-file enumeration) that scopes the digest at all — there is no code path by which an untracked file could ever be included.
- **DeploymentBinding registry** (`registry.json`) is even further outside scope: it lives at `/etc/pcae/hatp/trust-store`, entirely outside this repository's filesystem tree — not merely untracked, but not even a candidate path the digest computation ever walks.

## 13. RepositoryIdentity Rollback / Retention Policy

If identity creation succeeds but binding creation subsequently fails: **retain the identity.** Derived, not assumed — the schema (§4) has no source-SHA field and no binding-linkage field; the identity is source-version-agnostic and semantically stable regardless of what happens afterward with the binding. Deleting a legitimately generated, stable identifier would be actively wrong (it is designed to be a durable, host-local fact, §4's docstring: "repository-local, randomly generated, persistent `repository_instance_id`") and would only be justified by an explicit, separately governed decision to do so — never as an automatic side effect of an unrelated later failure. This matches 7M §30's "leave once legitimately created" principle, independently re-derived here from the schema's own field set rather than inherited from that document's prose.

## 14. Failure / Retention Matrix

| Failure point | Retention policy | Basis |
|---|---|---|
| RepositoryIdentity creation fails | No binding mutation possible (producer never reached) | `create_deployment_binding` is a separate, later call |
| RepositoryIdentity created, binding creation fails before durable write | Identity remains (§13); binding: nothing to roll back, `create_deployment_binding` never wrote | Producer's own validate→mutate→read-back→audit ordering (§15) |
| Binding durable-write succeeds, audit emission fails after | **Binding remains valid/published.** Execution must report `MUTATION DURABLE — AUDIT FAILURE`, STOP, no automatic deletion; reconcile out of band in a later repair/audit-reconciliation phase | Producer module docstring, own explicit disposition (§15) |
| HBDC evaluation fails/unexpected after valid binding creation | Do not automatically delete/revoke; STOP for diagnosis (§11.2). If later a genuine revocation decision is made, use `revoke_deployment_binding()` (field-mutate to `revoked`, never delete) | §11.2, 7M §44 re-confirmed |
| Source rollback after identity/binding mutation | **Never authorized as part of first-use failure handling.** Source redeployment (Transition 1) is independently verified and complete (§0); Transition 2 must never roll source back to `28bf137b...` | Explicit exclusion, this phase's governing prompt §40, consistent with two-transition model's own rollback-isolation property (7M §28 table) |

## 15. Audit-Durability Gap — First-Use Classification

Carried finding (149O.20L.7J §17, re-confirmed present in current source this session, §3 item 3/§15 of `hatp_deployment_binding_admin.py`'s own module docstring): `create_deployment_binding` can durably mutate the trust store while an unrelated exception in the audit-emission path propagates uncaught, leaving zero audit record for a real mutation. The module's own docstring names this explicitly as "a known, named limitation of composing two independently atomic storage systems without a real two-phase commit, not an oversight" — not silently accepted, disclosed at the point of implementation.

**Classification for first real use: ACCEPTABLE NON-BLOCKING FIRST-USE RISK, conditional on §10 step 6's discipline being followed** (immediate audit-presence re-verification after any real `create_deployment_binding` call; a missing-audit/present-mutation state must STOP for read-only adjudication, exactly as an unexpected HBDC result would, §11.2). This is not automatically carried forever without re-examination — it is re-classified here, for this specific first use, on the following grounds: (a) this is the *first* binding for this repository, so there is no pre-existing valid state a silent audit failure could obscure; (b) the mutation itself is independently, exactly re-verifiable via `read_repository_identity`/`HATPTrustStore.production().load_repository_enrollment()` regardless of whether the audit record exists, so the STOP-and-adjudicate step (§10 step 6) has a real, independent verification path available to it; (c) blocking first use entirely on this gap would leave HBDC permanently `NON_COMPLIANT` with no path forward, which is a worse outcome than accepting a bounded, well-understood, independently-detectable risk with a defined STOP procedure.

## 16. Other Carried-Forward Gaps

- **Timestamp-parser gap** (`hatp_bootstrap._parse_iso_timestamp` more permissive than the strict producer-output grammar): scoped to the *consumer* read path only. The producer (`_canonical_timestamp_now()`) always emits strict-grammar timestamps (asserted against its own regex at generation time, §9 item 7) — first-use generated artifacts are protected on the write side. **Operationally acceptable for first use**, because only the producer writes and the trust store is admin-protected (only the admin OS principal can write a malformed timestamp there in the first place). Not repaired; not blocking.
- **HMIC-REQ-103** (revoking a binding after certification leaves certification `VALID`): irrelevant to initial creation — no certification exists yet to be left stale by it. A later-lifecycle concern, correctly out of scope here. Not repaired.
- **HMIC-REQ-063** (executed-byte provenance: `implementation_scope_digest` proves on-disk byte identity, not that the running interpreter resolves imports to those exact files): no overclaim made in this document. §5.3's live HBDC read confirmed diagnostic *behavior*, not cryptographic executed-code attestation — that distinction is preserved here exactly as 7M preserved it.

## 17. Protected Root Current State

`/etc/pcae/hatp/trust-store` on Dell: exists, `drwxr-x--- 2 root pcae`, empty (no `registry.json`) — confirmed read-only, §5.2. No mutation performed or proposed.

## 18. CHGR Condition-6-Equivalent Text — Direct Re-Read

The specific numbered "condition 6" the governing prompt refers to belongs to the *source-redeployment* CHGR (`chgr-0e37ed1340b14311826722c4dbf3e856`), re-read directly this session from `.pcae/publication-execution/records/`:

> **6)** "No venv reinstall, no wrapper mutation, no DeploymentBinding, no Boundary C, no Boundary A, no Cutover Record, no Permission Broker/POL-005/COMP-002 change, and no repository onboarding are authorized by this election, in this or any future phase, without a fresh, separate election."

This is an exhaustive six-category exclusion list; `RepositoryIdentity` is not named (consistent with §6.1's independent finding that identity creation carries no authority and needs no election at all — its omission from condition 6 is not a gap, it is consistent with identity requiring no election in the first place). The **current, most-recent** CHGR (`chgr-71bd24f9d3d742d6baac772e480fc876`, the source-redeployment-execution authorization) carries its own condition 17, re-read directly this session:

> **17)** "First-use transition (RepositoryIdentity + DeploymentBinding) remains separately gated — a distinct future phase, its own proposition, verification, election, and CHGR."

Both are satisfied by this phase's own disposition: no election initiated, no CHGR published, RepositoryIdentity/DeploymentBinding both still absent (§0).

## 19. New Election Authority Required

Neither of the two CHGRs cited in §18 authorizes RepositoryIdentity or DeploymentBinding creation — both explicitly reserve that decision to a future, dedicated election. `chgr-71bd24f9d3d742d6baac772e480fc876`'s scope (per its own `decision_subject`, re-read this session) is the source-redeployment execution only. **Transition 2 requires its own, new CHGR — no reuse of either existing record.**

## 20. Human Proposition Scope (Future 7O.4 Election)

The future election (§10 step 5) should authorize only: (1) `DeploymentBinding` creation, against the exact, already-real `repository_id`/`canonical_deployment_root` resolved in §10 step 3 (7O.2); (2) read-back verification; (3) HBDC re-adjudication. Explicitly **not**: source redeployment (already separately elected and executed, 7N–7N.5), certification, or activation. The proposition's `decision_subject` must name the specific repository, root, and binding fields explicitly — no generic "initialize deployment" language (governing prompt §60).

## 21. Exact Future Commands (Partitioned)

**Read-only preflight** (7O.1/7O.3, and immediately before 7O.5's execution):
```
sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
sudo -n git -C /opt/pcae/runtime/src status --porcelain=v1
sudo -n ls -la /opt/pcae/runtime/src/.pcae/repository-identity.json
sudo -n ls -la /etc/pcae/hatp/trust-store
sudo -n cat /etc/pcae/hatp/trust-store/registry.json
sudo -n -u pcae bash -c 'cd /opt/pcae/runtime/src && PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin /opt/pcae/runtime/venv/bin/python3 -c "from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance as v; r=v(); print(r.status); [print(c.check_id,c.status) for c in r.checks if not c.satisfied]"'
```

**RepositoryIdentity mutation** (7O.2, unelected administrative step, first mutation boundary — §22):
```
sudo -n -u pcae /opt/pcae/runtime/venv/bin/python3 -c "
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity
identity = ensure_repository_identity(HarnessPath('/opt/pcae/runtime/src'))
print(identity)
"
```

**Identity read-back** (immediately after, same step):
```
sudo -n -u pcae /opt/pcae/runtime/venv/bin/python3 -c "
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import read_repository_identity
print(read_repository_identity(HarnessPath('/opt/pcae/runtime/src')))
"
```

**DeploymentBinding preview** (7O.2, still read-only, against the now-real identity):
```
sudo -n -u pcae /opt/pcae/runtime/venv/bin/python3 -c "
from pathlib import Path
from pcae.core.hatp_deployment_binding_admin import AuthorityEvidence, preview_create_deployment_binding
p = preview_create_deployment_binding(
    repository_root=Path('/opt/pcae/runtime/src'),
    authority=AuthorityEvidence(
        principal_id='<resolved 7O.2>', signer_key_id='<resolved 7O.2>',
        provider_profile='<resolved 7O.2>', authority_scope='<resolved 7O.2>',
        election_reference='<CHGR id, filled in at 7O.4>',
    ),
)
print(p)
"
```

**DeploymentBinding mutation** (7O.5, second mutation boundary — §22, only after election/CHGR):
```
sudo -n -u pcae /opt/pcae/runtime/venv/bin/python3 -c "
from pathlib import Path
from pcae.core.hatp_deployment_binding_admin import AuthorityEvidence, create_deployment_binding
r = create_deployment_binding(
    repository_root=Path('/opt/pcae/runtime/src'),
    authority=AuthorityEvidence(
        principal_id='<resolved 7O.2>', signer_key_id='<resolved 7O.2>',
        provider_profile='<resolved 7O.2>', authority_scope='<resolved 7O.2>',
        election_reference='<real CHGR id>',
    ),
)
print(r.outcome, r.binding)
"
```
(The intended real invocation surface is `scripts/hatp_deployment_binding_admin.py create`, run by the Protected Admin OS principal — the ad hoc Python shown here is for preview/verification parity only, matching what this phase itself used read-only.)

**Binding read-back:** `HATPTrustStore.production().load_repository_enrollment(repository_id)`.

**HBDC diagnostic** (immediately after, 7O.5/7O.6): the same `verify_class_b_deployment_conformance()` invocation shown in §5.3/§21 preflight block.

**Failure STOP paths:** any command above returning an exception other than the expected `RepositoryIdentityMissingError` (pre-identity preview only) must halt the phase and report the exact exception type/message — no retry-with-different-parameters, no silent fallback.

## 22. First and Second Mutation Boundaries

1. **First mutation boundary:** `ensure_repository_identity()` on Dell (7O.2) — writes `.pcae/repository-identity.json`. Unelected (§6.1/§6.3), but still a real filesystem mutation, still gated behind its own dedicated phase with independent verification (§10).
2. **Second mutation boundary:** `create_deployment_binding()` on Dell (7O.5) — writes to the Protected Root's `registry.json`. **This** is the one requiring a fresh, separate election (§18-20) and the one governed by HBDC-REQ-064/066 (admin-OS-principal-only, out-of-band from any agent-invoked path).

## 23. Independent Systems Review Requirement (Carried Forward)

Per this project's own prior lesson (Claude SSH issue, referenced by the governing prompt): the executing agent in every future execution phase (7O.2, 7O.5) must independently inspect and understand the exact commands in §21 before running them against real Dell state — governance authority constrains *what* execution is authorized, it does not substitute for the executing agent's own technical verification of *how* that execution behaves. Recorded here as an execution-procedure requirement for future phases, not a new authorization concept.

## 24. Exclusions (Explicit, All Verified Held This Phase)

No RepositoryIdentity created (real or Dell). No DeploymentBinding created. No producer `create`/`rotate`/`revoke` invoked. No human election initiated. No CHGR published. No HMIC certification performed. No Boundary C. No Boundary A / HATP activation. No source mutation (no `git fetch`/`checkout`/`chown`/`chmod` — Dell source untouched, §5.1 confirms identical SHA and clean tree, before and after this phase's read-only inspection). No venv/wrapper changes. No Permission Broker change. No project onboarding.

## 25. Exact Post-Success State (Future, Not This Phase)

If the full sequence in §10 succeeds: RepositoryIdentity present and independently readable; exactly one active, matching DeploymentBinding; HBDC expected `COMPLIANT` (§11.1, modeled); HMIC certification still absent; Boundary C not authorized; HATP not ready. A dedicated independent real-host verification phase (7O.6) is required before any Boundary-C preparation may begin (7O.7).

## 26. Final Verdict

**FIRST-USE ARCHITECTURE REQUIRES SEPARATE IDENTITY TRANSITION** — but narrowly: not because RI-D is architecturally wrong (it is the selected, evidence-supported model, §6.3), but because *this specific phase's* governing prompt excludes real RepositoryIdentity creation from its own scope (§8), which prevents this phase from delivering a proposition with the exact `repository_id` value RI-D is capable of providing. §10 names the exact one additional, narrowly-scoped, unelected administrative sub-phase (149O.20L.7O.2) required to close that gap before the binding election (149O.20L.7O.4) can be drafted with full precision. This is **not** the three-election RI-C model (§6.2) — RepositoryIdentity creation still requires no election of its own — it is RI-D's own two-part internal structure (unelected identity step, then one elected binding step), executed one governed sub-phase later than 7M's original sketch assumed, because this phase's own boundary is stricter than 7M's.

**Exactly one future election is required** (149O.20L.7O.4), and it will be drafted against real, exact values (149O.20L.7O.2/7O.3), not a generation rule with an unknown value — full authority precision is achievable, just not achieved by this phase alone.

## 27. Recommended Next Phase

**149O.20L.7O.1 — RepositoryIdentity + DeploymentBinding First-Use Proposition Preparation Independent Verification** (mirrors 7N→7N.1's pattern: independently re-derive this phase's factual claims — RI-model selection reasoning, field-resolution completeness, disposable-simulation reproducibility, read-only Dell preview results — without trusting this document, this session, or 7M as an oracle). Then, per the revised decomposition in §10: 7O.2 (RepositoryIdentity creation, unelected, + exact binding proposition drafting) → 7O.3 (independent verification of that exact proposition) → 7O.4 (human election + CHGR) → 7O.5 (first-use execution + HBDC re-adjudication) → 7O.6 (independent real-host verification) → only then 7O.7 (Boundary-C preparation).

## 28. Proof — No Authority-Bearing Action Taken This Phase

- **No Dell mutation:** every SSH command issued (§5, §21 preflight block) used only `git rev-parse`/`git status`/`git symbolic-ref`/`ls`/`cat`/read-only Python imports and function calls (`verify_class_b_deployment_conformance`, `hasattr`, `--help`). Confirmed via a second `git status --porcelain=v1`/SHA read after this phase's Dell access (§5.1 shown; re-verifiable by any future phase) showing no drift.
- **No RepositoryIdentity:** `sudo -n ls` confirmed absent both at phase entry and was never subsequently created (§5.2); the only identity ever generated was the synthetic, disposable one in §7's local tempdir, deleted at the end of that run.
- **No DeploymentBinding:** `sudo -n cat registry.json` confirmed absent (§5.2); only ever created against the synthetic, disposable local trust store in §7.
- **No election:** no APPROVE/DECLINE/AMEND presented anywhere in this document.
- **No CHGR:** no `pcae governance-record`/publication-execution write performed; §18-19 only *read* existing CHGR records.
- **No certification:** `hatp_mandatory_certification.py` was read (§3 item 5) but no certification function was invoked.

## 29. Tests / Governance Results

No new test module was added this phase (proposition-preparation/architecture-materialization only, no production code changed). Verification was performed via the disposable simulation script (§7, not committed — scratch artifact) and live read-only Dell commands (§5). Governance commands and results:

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — identical historical `tasks/done/`/`DONE.md` sync gap already carried forward by 149O.20L.7N.5; not remediated here, outside this phase's allowed-file scope)
- `pcae_push_check`: clean
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: telegram configured/enabled
- `pcae_phase_report_reconcile_149O_20L_7N_5`: reconciled, mutation none
- `dell_read_only_preview`: passed — exact SHA/tree/identity-absence/binding-absence match expected baseline; HBDC diagnostic 34/34 checks, single expected residual `HBDC-REQ-042`
- `disposable_local_simulation`: passed — pre-identity preview failure reproduced, idempotency confirmed twice, preview-then-create-then-match-then-idempotent-retry sequence all behaved exactly as the production code's own docstrings specify
- `no_dell_mutation_no_repositoryidentity_no_deploymentbinding_no_election_no_chgr_no_certification`: passed (§28)
- `fast_green`: not run this phase — no `src/pcae/**` file was modified; per this phase's own allowed-file scope (doc-only), no code-path change exists for the suite to regress against. (Recorded as `not_applicable_this_phase` in phase-completion metadata, matching the convention used by 149O.20L.7N/7M for doc-only phases.)

## 30. Commits / Push / origin..HEAD

See phase-completion metadata for the exact commit list. `origin/main..HEAD` and push status recorded at finalization (§ below, after `pcae phase complete`/`pcae push`).

## 31. Exact Recommended Next Phase

**149O.20L.7O.1 — RepositoryIdentity + DeploymentBinding First-Use Proposition Preparation Independent Verification.** Recommendation only — not initiated in this phase.
