# Phase 149O.20L.7O.1 — RepositoryIdentity + DeploymentBinding First-Use Proposition Preparation Independent Verification

## 0. Status

**Verification-only.** No RepositoryIdentity created (real Dell or local). No DeploymentBinding created. No producer `create`/`rotate`/`revoke` invoked against Dell or any real trust store. No human election initiated. No CHGR published. No HMIC certification performed. No Boundary C, no Boundary A, no HATP_MANDATORY activation. All Dell access this phase was strictly read-only (SSH `git rev-parse`, `ls`, `cat`, all via `sudo -n` as `codex`; no write verb issued). Every disposable simulation ran against `tempfile.TemporaryDirectory()` locations, never this repository's own `.pcae/` and never the real Protected Root.

**Phase-entry commit:** `d4d5614d` (`Phase 149O.20L.7O: sync active task allowed-file list`). `origin/main == HEAD`, 0 commits ahead/behind, working tree clean at entry.

**Method.** 7O's report (`docs/PHASE_149O_20L_7O_...md`) was read only *after* the independent reconstruction below (§3-§15) was substantially complete, per this phase's own instruction not to treat it as an oracle. Where this document's independent conclusion matches 7O's, that is stated as independent re-derivation. One genuinely new primary-source finding not cited by 7O is disclosed in §6. One refinement to 7O's audit-durability-gap disposition, found only by actually executing the failure (not merely reasoning about it), is disclosed in §11.

## 1. Entry Checks (read-only)

```
git status --short                    → (clean)
git status --branch --short           → ## main...origin/main
git log --oneline -10                 → HEAD = d4d5614d, linear 149O chain
git log --oneline origin/main..HEAD   → (empty)
git rev-list --count origin/main..HEAD → 0
pcae health                           → healthy, git clean, agent lock held by claude-local
pcae check                            → passed
pcae status coherence                 → coherent
pcae doctor task-memory               → warnings (pre-existing: 29 active-looking done/ entries
                                          missing from tasks/DONE.md, all predating this phase;
                                          identical, carried-forward disposition to 7O's own entry;
                                          outside this phase's allowed-file scope)
pcae push check                       → clean, nothing_to_push
pcae runtime inspect                  → Observed / observe / unavailable
pcae notify status                    → telegram configured/enabled
pcae phase-report show --latest       → 149O.20L.7O canonical report; recommended next phase =
                                          149O.20L.7O.1 (this phase)
pcae phase-report reconcile --phase-id 149O.20L.7O
                                       → reconciled, 2 generations promoted, marker
                                          already_dispatched, checkpoint completed, receipt
                                          finalized, mutation: none
```

`pcae task transition --next "Phase 149O.20L.7O.1: ..."` closed the stale idle task
(`20260818-0518-idle-awaiting-next-governed-phase-post-149o-20l-7o`) and opened the active
task for this phase. No raw git commit/push used; governed CLI only throughout.

## 2. RepositoryIdentity Source Reconstruction (Primary Read)

Read `src/pcae/core/repository_identity.py` in full, independently. Confirmed:

- **Schema (closed set, 3 fields):** `schema_version` (int, must equal `1`), `repository_instance_id` (str, must be UUID4 canonical lowercase form), `created_at` (str, must parse as a timezone-aware ISO-8601 timestamp via a fail-closed local parser deliberately duplicated from `rollback_approval_evidence.py`, not imported).
- **Path:** `.pcae/repository-identity.json`, relative to `HarnessPath.root`.
- **Read (`read_repository_identity`)**: returns `None` only on genuine absence; raises `RepositoryIdentityMalformedError` on any other deviation (bad JSON, unknown field, missing field, wrong schema version, invalid UUID4, invalid timestamp). Rejects symlinks at both the target and its immediate parent before reading.
- **Write (`_write_atomic`)**: `tempfile.mkstemp` in the same directory → write → `flush` → `fsync` → symlink-recheck → `os.replace`. Directory `mkdir(parents=True, exist_ok=True)`. This is POSIX-atomic; there is no window in which a partially-written file is visible at the final path.
- **`ensure_repository_identity`**: read first; return unchanged if present and valid; generate + atomically write if genuinely absent; propagate `RepositoryIdentityMalformedError` uncaught if present-but-invalid (never auto-repairs, never silently regenerates).
- Module docstring states the frozen invariant verbatim: "possession, knowledge, copying, or modification of the identifier defined here SHALL NOT by itself grant any approval authority" (citing HATP-REQ-051/063) and states the module "has no knowledge of HATP, the Permission Broker, RAE, or any other authority concept, and imports none of them" — verified true by import inspection: the module's only imports are `json`, `os`, `tempfile`, `uuid`, stdlib `dataclasses`/`datetime`/`pathlib`/`typing`, and `pcae.core.paths.HarnessPath`.

## 3. UUID Generation Proof

`_generate_repository_identity()` (lines 202-208):

```python
def _generate_repository_identity(now: Optional[datetime] = None) -> RepositoryIdentity:
    timestamp = now or datetime.now(timezone.utc)
    return RepositoryIdentity(
        schema_version=SCHEMA_VERSION,
        repository_instance_id=str(uuid.uuid4()),
        created_at=timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )
```

Confirmed by direct read: `uuid.uuid4()`, no caller-supplied value anywhere in the module's public or private surface, no deterministic seed, no dry-run/reservation mode, no `preview_ensure_repository_identity` equivalent. `ensure_repository_identity(root)` takes exactly one parameter (`root: HarnessPath`) — there is no parameter through which a caller could inject or preview a UUID.

## 4. Idempotency — Disposable Proof

Executed against a fresh `tempfile.TemporaryDirectory()`, not this repository's `.pcae/`:

```python
root = HarnessPath(d)
ri.read_repository_identity(root)          # → None (genuinely absent)
id1 = ri.ensure_repository_identity(root)  # → generates + persists
id2 = ri.ensure_repository_identity(root)  # → id2 == id1, same UUID, no re-generation
```

Result: `id1.repository_instance_id == id2.repository_instance_id` → `True`. File exists at
`<root>/.pcae/repository-identity.json`, mode `0o600` (from `tempfile.mkstemp`'s own default —
no explicit `chmod` is issued anywhere in the module), owned by the invoking user/group (uid 501,
gid 20 on this Mac — i.e. whoever runs the process, not a fixed principal; relevant to §9-§10).

## 5. Partial-Failure Behavior — Disposable Attacks

Four attacks executed, all against disposable temp directories:

1. **Write fails after generation** (`.pcae/` made mode `0500`, no write bit): `ensure_repository_identity` raises `PermissionError` uncaught; **no file is created** (confirmed via `os.path.exists`). Retry after restoring write access succeeds and generates a **fresh** UUID — this is safe, not a duplicate-visibility bug, because nothing was ever persisted by the failed attempt; there is no state to diverge from.
2. **File exists, malformed JSON**: `RepositoryIdentityMalformedError` raised; a second call raises the identical error — confirmed **no silent auto-repair or regeneration** ever occurs.
3. **File exists, valid JSON, one unrecognized extra field**: `validate_repository_identity_document`'s closed-field-set check rejects it (`RepositoryIdentityMalformedError: ... unrecognized fields: ['extra']`) — strict schema, no permissive coercion.
4. **Symlink attack** (identity path replaced with a symlink to a file outside `.pcae/`): `RepositoryIdentitySymlinkError` raised, refused rather than followed.

**Conclusion, independently proven:** multiple UUIDs can never become materially visible across retries. Because `_write_atomic` uses `mkstemp`+`fsync`+`os.replace`, there is no partial-write state observable by a reader, and because `ensure_repository_identity` always re-reads existing state first, a retry after any failure mode either (a) sees the same persisted identity and returns it unchanged, or (b) sees nothing and generates exactly one new one — never two live identities for one repository.

## 6. Semantic Subject and Authority-Conferral Consumer Inventory

**Semantic subject:** `repository_instance_id` identifies **this specific on-disk deployment/checkout** of the PCAE repository (a "repository-local, randomly generated, persistent" fact per the module's own docstring), not the abstract Git repository (a clone/fork gets its own, per HATP-REQ-058/059), not the host, and not a particular commit (survives commit/branch/legitimate-move activity per HATP-REQ-047). This matters directly for §7: creating it identifies *a deployment*, but identifying something is not the same as authorizing anything about it.

**Consumer inventory** (all files that `import` `repository_identity`, found via `grep -l "from pcae.core.repository_identity"` / `import repository_identity`, cross-checked against every hit's actual usage — false-positive matches on unrelated `repository_id` concepts in `cltr/`, `repository_intelligence/`, etc. were excluded):

| Consumer | Usage | Authority-changing? |
|---|---|---|
| `hatp_class_b_conformance.py` (`_check_deployment_identity`) | Reads identity; if absent → `HBDC-REQ-042 = False / no_repository_identity_present`. If present → looks up `HATPTrustStore.production().load_repository_enrollment(id)` and requires `deployment_binding_matches()` to be `True`. | **No.** Identity presence alone only changes the *failure reason string* (`no_repository_identity_present` → `no_active_deployment_binding_matches_repository_and_root`); `satisfied` stays `False` either way absent a real binding. Empirically confirmed, §8. |
| `hatp_deployment_binding_admin.py` (`_resolve_repository_id`) | Reads identity via `read_repository_identity` only (never `ensure_...`); raises `RepositoryIdentityMissingError` if absent. Gates whether `preview_create_deployment_binding`/`create_deployment_binding` can run *at all*. | **No new authority granted**, but identity existence is a **structural precondition** for the binding producer to run — this is the "authority-free prerequisite" relationship RI-D depends on, confirmed by reading the function body: it never calls `ensure_repository_identity()` as a side effect. |
| `hatp_mandatory_certification.py` (`derive_repository_instance_id`) | Same read-only dependency; raises `CertificationMalformedError`-family error if absent. Certification cannot even be *attempted* without identity. | **No.** Same structural-precondition relationship as above; no certification logic branches on identity's mere presence to grant `VALID`. |
| `hatp_mandatory_cutover.py` (`_resolve_current_repository_instance_id`, `_resolve_cutover_mode_at_root`) | Uses identity presence/absence to select which **fail-closed reason** (`REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY = "fail_closed_no_local_repository_identity_provisioned"`) to report, and to look up a cutover-activation-marker record keyed by the identity value. | **No.** Absence produces a fail-closed refusal reason; presence alone does not activate `HATP_MANDATORY` — deeper checks (marker/record matching) still gate. |
| `hatp_signing_ceremony.py`, `hatp_ag_authority.py`, `hatp_rollback_consumption.py`, `human_approval_trusted_provenance.py` | All read `repository_instance_id` purely as a **locator/lookup key** (analogous to a foreign key) into other, independently-gated stores (evidence store, hardware-provider context, rollback-approval records). None grants a capability from identity's existence alone. | **No.** |
| `commands/init.py` | `ensure_repository_identity(root)` is the only production call site that *creates* one — invoked by `pcae init`, an ordinary, already-existing, non-privileged repository-bootstrap command with no election gate today. | Creates the artifact; confers no authority per the analysis above. |

**Verdict: no code path in this repository treats RepositoryIdentity's mere existence as sufficient to authorize execution, satisfy a permission check, grant scope, satisfy certification, satisfy HBDC, unlock DeploymentBinding *matching* (only DeploymentBinding *lookup-by-key* — matching still requires a real, separately-created, field-equal binding), or change runtime capability.** Every consumer either (a) uses identity purely as a lookup key into a separately-gated store, or (b) uses identity's *absence* to select a specific fail-closed reason string, never uses its *presence* to grant anything.

## 7. HATP-REQ-048/051 — and a Stronger Primary-Source Finding (HBDC-REQ-068)

Read directly from `docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`:

> **HATP-REQ-048.** A future PCAE identity-aware initialization MAY generate `repository_id` without requiring human approval, because identity creation alone grants no HATP authority.
>
> **HATP-REQ-051. (Mandatory statement, verbatim requirement.)** Possession, knowledge, copying, or modification of `repository_id` SHALL NOT by itself grant HATP approval authority.

Independently interpreted: HATP-REQ-048 is phrased as a **MAY** — permissive, not itself a blocking mandate that no election can ever be required — but its stated *reason* ("because identity creation alone grants no HATP authority") is exactly the finding independently reproduced by the consumer inventory in §6.

**A stronger statement than either 7O or the governing prompt cited was found directly in `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, not previously flagged in this document's own prior draft-in-progress:**

> **HBDC-REQ-068.** Repository identity (Layer 1) creation is not itself gated by HBDC-REQ-056..066's election requirement (those requirements govern `DeploymentBinding` only); nothing in this amendment alters HATP-REQ-048's existing disposition that repository-identity creation confers no authority and needs no approval.

This is a **normative SHALL-equivalent contract statement** (framed as fact/disposition, not a MAY), explicitly and directly settling the question this entire phase exists to verify: RepositoryIdentity creation "needs no approval." It is more direct and load-bearing than HATP-REQ-048/051 alone, and it directly rebuts RI-C (a dedicated election for identity creation) as unnecessary, on primary-source authority, independent of any inference from the consumer inventory.

## 8. RepositoryIdentity Governance Classification

Given §6 (no authority-conferral consumer found) and §7 (HBDC-REQ-068's explicit disposition), classification:

**A. Non-authority descriptive/bootstrap state — no human election required.**

Not B, because no explicit operator authorization/change record is contractually required for identity creation (HBDC-REQ-068 explicitly excludes it from the election requirement that governs DeploymentBinding). Not C, because no dedicated election is required. Not D — the architecture is not ambiguous here; HBDC-REQ-068 is unambiguous normative text, independently located and read this phase.

This does **not** mean identity creation is an *ungoverned* mutation in the operational sense (§9-§10 below): it is still a real filesystem write, still requires the correct OS principal on Dell's root:pcae topology, and still warrants its own dedicated, independently-verified phase before the binding proposition is drafted — "no election required" and "no governance discipline at all" are kept distinct, per this phase's own instruction not to conflate them.

## 9. Human-Owner Authorization vs. PCAE Internal Governance — Kept Distinct

- **Real-world host authorization:** the human (Atila Madai) owns `hac-dell` outright; nothing about PCAE's internal governance model is needed to authorize the human from ever running arbitrary commands on their own machine as themselves.
- **PCAE internal governance semantics:** independent of host ownership, PCAE's own architecture (HATP/HBDC contracts) defines what counts as an authority-bearing *PCAE-tracked* mutation and what evidence trail it requires. HBDC-REQ-068 settles that RepositoryIdentity creation needs no PCAE-internal election; it says nothing about, and does not substitute for, the separate real-world fact that only the correct OS principal (root, or a `pcae`-group member) can physically write to `/opt/pcae/runtime/src/.pcae/` on Dell's actual filesystem (§10). Both layers were kept analytically separate throughout this document; neither is used to answer the other's question.

## 10. Filesystem Trust, Root-Owned Deployment Compatibility, Path — Live Dell Read

SSH to `hac-dell` (`atila-Latitude-E5470`, machine-id `54ff22ce400b475aa0d55cb68f4a3334`, confirmed matching) as user `codex`, read-only throughout:

```
$ ssh hac-dell 'cd /opt/pcae/runtime/src && git rev-parse HEAD'
Permission denied            # codex has no direct read access — confirms real topology below

$ sudo -n ls -ld /opt/pcae/runtime/src
drwxr-x--- 14 root pcae 4096 Aug 17 22:20 /opt/pcae/runtime/src

$ id
uid=1003(codex) gid=1003(codex) groups=1003(codex),27(sudo),100(users)   # codex NOT in group pcae

$ sudo -n git -C /opt/pcae/runtime/src rev-parse HEAD
b0840e96a7ffb12308e95828aa5927c3e7c770c0

$ sudo -n ls -la /opt/pcae/runtime/src/.pcae/repository-identity.json
ls: cannot access ...: No such file or directory     # confirmed absent

$ sudo -n ls -la /etc/pcae/hatp/trust-store/
drwxr-x--- 2 root pcae ...                             # exists, empty
$ sudo -n cat /etc/pcae/hatp/trust-store/registry.json
cat: ... No such file or directory                     # confirmed absent — DeploymentBinding absent
```

**Path independently derived and confirmed:** `/opt/pcae/runtime/src/.pcae/repository-identity.json` — matches the task's expected conceptual location exactly, confirmed live, not trusted from any prior document.

**Filesystem trust / root-owned compatibility — independently determined, not assumed:**

- `/opt/pcae/runtime/src` is `root:pcae`, mode `0750` (owner rwx, group r-x, other none). The disposable-simulation-observed default output of `ensure_repository_identity` (§4) is mode `0600`, owned by whichever OS principal *runs the process* (uid/gid of the caller) — the module never issues an explicit `chmod`, `chown`, or group-write bit.
- **Codex (uid 1003, groups `codex`,`sudo`,`users`) cannot write into `/opt/pcae/runtime/src/.pcae/` at all** — not a member of group `pcae`, and the directory has no world-write or group-write-for-non-owner bit. This was directly observed (`Permission denied` on a bare `ssh ... git rev-parse`, before `sudo -n` was applied) — not inferred.
- **Who must execute identity creation, determined from live topology, not assumed:** either `root` (via `sudo`) or the `pcae` OS principal itself (uid 1004, confirmed to exist and to have group-readable/writable access to `/opt/pcae/runtime/**` per its listing ownership) — matching 7O's own §5.3 finding that the correct read-only diagnostic invocation on Dell must run as `sudo -n -u pcae`, not as bare root/codex (running as root produces spurious extra check failures, an artifact of the wrong OS identity, not a real state finding — independently corroborated by this phase's own topology read).
- **Ownership outcome if created naively:** if a future execution phase runs `ensure_repository_identity()` as `root` directly (e.g. bare `sudo python3 -c ...`) rather than as the `pcae` principal, the resulting file would be owned `root:root` (or `root:pcae` if the process's default group resolves that way) at mode `0600` — **not group-`pcae`-readable by the `pcae` agent principal that the rest of the runtime executes as**, since `0600` grants zero access to group or other regardless of group ownership. **This is a real, concrete compatibility gap independently identified this phase**, not previously named this explicitly in 7O's own report: unless the future 7O.2-equivalent execution step is run *as* the `pcae` principal specifically (as 7O's own §5.3 diagnostic invocation already had to do for read access), the created `repository-identity.json` could become unreadable by the very `pcae` principal that needs to read it back later via `read_repository_identity()`, `_check_deployment_identity()`, etc. — because those all execute as `pcae`, and `0600` root-owned excludes them entirely.
  - **Disposition:** non-blocking for *this* verification phase (no mutation occurs here), but this is a concrete, actionable requirement for whichever phase performs real identity creation on Dell: it **must** execute as the `pcae` OS principal (mirroring the pattern 7O's own §5.3 diagnostic command already used, `sudo -n -u pcae ...`), not as bare root, or the created file will not satisfy `0600`-owner-readable-by-pcae and every downstream consumer (`_check_deployment_identity`, HMIC's identity resolver, etc., all of which run as `pcae`) will see it as *effectively* absent (permission-denied on read, which `read_repository_identity`'s own `OSError` handling converts to `RepositoryIdentityMalformedError` — a fail-closed, not fail-open, outcome, but still an avoidable operational mistake worth flagging explicitly for 7O.2).

## 11. Git Cleanliness

`.pcae/.gitignore` line 4: `repository-identity.json` (confirmed directly, `grep -n "repository-identity" .pcae/.gitignore`). The artifact is untracked and ignored; creating it produces no `git status` delta and does not alter this (or any) repository's tracked Git identity. Confirmed structurally, not merely by inference: the file never enters the working tree's tracked-object graph regardless of content.

## 12. HMIC Digest Consequence — Disposable Before/After Proof

`derive_implementation_scope_digest()` (`hatp_mandatory_certification.py`) hashes exactly the 30 canonical paths returned by `_frozen_canonical_paths()` — independently enumerated this phase and confirmed to be 30 source `.py`/contract `.md` paths under `docs/contracts/`, `scripts/`, `src/pcae/**`. `.pcae/repository-identity.json` is **not** among them (by construction — it is not a tracked source file at all).

Disposable proof (rsync of only `docs/`, `scripts/`, `src/` into a temp dir, no `.git`):

```
before = derive_implementation_scope_digest(root)  → 65ff8ab0...15b8
ensure_repository_identity(root)                    → writes .pcae/repository-identity.json
after  = derive_implementation_scope_digest(root)   → 65ff8ab0...15b8
before == after                                     → True
```

The digest value obtained (`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`) **exactly matches** the deployed HMIC digest recorded in this task's entering state — independently reconfirming that value as well, since Mac HEAD has zero `src/pcae/**` drift from the deployed candidate SHA (§14).

## 13. HBDC Before/After-Identity Disposable Result

Isolated `_check_deployment_identity(root)` call (not the full aggregator, to isolate the identity-specific check):

```
before identity: satisfied=False, status='no_repository_identity_present'
ensure_repository_identity(root)
after identity:  satisfied=False, status='no_active_deployment_binding_matches_repository_and_root'
```

**Exact vocabulary independently confirmed**, matching the task prompt's own predicted phrase precisely. `satisfied` remains `False` in both cases — only the failure-reason string changes; this is the concrete evidence for §6's "no authority conferred" conclusion.

Note independently established: `_check_deployment_identity` calls `HATPTrustStore.production()` — a **fixed, real production trust-store root** (`_default_production_trust_root()`, platform-keyed constant, never derived from the disposable `root` argument) — so this before/after test, even in a disposable *repository* directory, reads the real (empty, on this Mac) production trust store for the binding-lookup half of the check. This is correct production behavior (the trust store is intentionally repository-independent), not a simulation artifact, and was confirmed by reading `HATPTrustStore.__init__`/`production()` directly.

## 14. Full HBDC Aggregator Disposable Simulation — Limitations

Running `verify_class_b_deployment_conformance()` (the full 34-check aggregator) against a disposable temp repo returns `NON_COMPLIANT` with **20 of 34 checks failing**, not just `HBDC-REQ-042`. Independently confirmed these are exactly the topology/environment-lock checks (`HBDC-REQ-001..039`) that are inherently tied to the **real, admin-provisioned Dell deployment topology** (protected root existence, admin-owned venv, ownership/write-bit configuration) — a throwaway temp directory on a developer Mac cannot and should not satisfy them; this is a genuine simulation limitation, not a defect. Only `HBDC-REQ-022` (Model-A editable-install detection — true here because this actual dev checkout genuinely is `pip install -e`) and `HBDC-REQ-042` (identity/binding — exercised in §13) produce meaningful, host-independent disposable results. **Full `COMPLIANT` cannot be meaningfully simulated off Dell; this is expected and was independently confirmed, not merely assumed.**

## 15. RI-A/B/C/D — Independent Model Comparison (Derived Before Re-Reading 7O's Own Framing in Detail)

- **RI-A (single election binds generation rule + binding):** would require electing on an *unknown* `repository_id` value (identity doesn't exist yet at election time) — the binding proposition could only bind a *rule* ("whatever UUID gets generated"), not an exact value, weakening auditability of exactly what was elected. Disadvantage: less precise; advantage: fewer phases. Given HBDC-REQ-068 (§7) already establishes identity creation needs no election at all, folding it into a binding election adds friction without adding protection.
- **RI-B (persist-free preview/materialization mode):** confirmed absent from production (§3 — no such function exists in `repository_identity.py`). Would require new code this phase (and 7O before it) is expressly forbidden from writing. Not inherently wrong, merely out of scope for a verification-only or proposition-preparation phase.
- **RI-C (fully separate RepositoryIdentity election):** independently rejected on the same primary-source ground as 7O: HBDC-REQ-068 already, explicitly, settles that no election is needed for identity creation. Requiring one anyway would be governance ceremony around a fact the architecture's own normative text has already closed — not "more careful," merely redundant.
- **RI-D (identity created first, unelected administrative prerequisite; exact value then read back into an exact binding election):** independently derived as superior on authority precision (the binding proposition can name the real `repository_id` and, since source is already deployed, the real `canonical_deployment_root`, rather than a generation rule), failure isolation (identity creation and binding creation are independently retryable — §5's partial-failure proof shows identity creation is itself safe under retry), and auditability (exactly one election is needed, and it can be drafted against real values). Complexity cost is one extra unelected administrative phase, judged acceptable given it requires no election and is independently verifiable on its own (§8).

**Model verdict, independently reached: RI-D.** This matches 7O's own selection. Because the reasoning is independently reconstructed from primary source (contract text HBDC-REQ-068 in particular, which is *stronger* evidence than what 7O's own document cited for this specific point) and reaches the same conclusion, **7O's RI-D selection is independently verified, not merely repeated.**

## 16. RepositoryIdentity Transition Semantics (If RI-D Wins)

Per §8's classification (Category A), the next identity-creation mutation phase should be an **explicit, dedicated, administratively-executed, non-election lifecycle operation** — not a full election (no authority to elect over, per HBDC-REQ-068), not silently folded into `pcae init`'s existing ordinary invocation (Dell's deployment identity creation is a deliberate first-use act on a specific, sensitive, root:pcae-owned production checkout, warranting its own governed phase boundary and independent verification even though no election gate applies), and not ordinary unattended automation (§10's ownership-compatibility finding means it specifically requires execution as the `pcae` OS principal, a deliberate operational choice each time). "Unelected" is not synonymous with "uncontrolled" here: the phase boundary, independent-verification requirement, and correct-principal-execution requirement are all still real governance discipline, just not an election.

A **separate independent-verification phase after identity creation but before the binding proposition** is still required (matching 7O's §10 decomposition and this phase's own instruction, §32 of the governing prompt), verifying: identity exists; schema valid; exact UUID value; exactly one generation occurred (no evidence of regeneration); ownership/mode as expected for the `pcae` principal (§10); Git remains clean (§11); HMIC digest unchanged (§12); HBDC transitions to exactly `no_active_deployment_binding_matches_repository_and_root` (§13).

## 17. DeploymentBinding Schema — 9 Fields, Independently Read

From `hatp_bootstrap.DeploymentBinding` (referenced, unchanged, by `hatp_deployment_binding_admin.py` per that module's own docstring: "this phase adds zero fields"):

```python
@dataclass(frozen=True)
class DeploymentBinding:
    repository_id: str
    canonical_deployment_root: str
    principal_id: str
    signer_key_id: str
    provider_profile: str
    authority_scope: str
    valid_from: str
    status: str                 # {"active", "revoked"} only (_STATUS_VALUES)
    revoked_at: Optional[str]   # None iff status == "active"; required iff "revoked"
```

Field-by-field, independently resolved:

1. **`repository_id`** — unavailable now (RI-D defers exact value to a future identity-creation step); the producer's own signature (`create_deployment_binding(*, repository_root, authority, _protected_root=None)`) **never accepts a caller-supplied `repository_id`** — it is always derived internally via `_resolve_repository_id()`, which reads the persisted identity. This is a structural guarantee, confirmed by reading the function signature directly, that the eventual binding's `repository_id` cannot diverge from whatever `RepositoryIdentity` actually exists at creation time — the "downstream equality invariant" is enforced by the producer's own type signature, not merely a documentation promise.
2. **`canonical_deployment_root`** — `resolve_canonical_deployment_root(Path("/opt/pcae/runtime/src"))`. Read-only resolvable today (source is deployed, §14 of this document / §5.1 of 7O). Independently confirmed this is the PCAE runtime's own deployed checkout, not a future managed-project-repository concept (no such concept was found anywhere in the current source tree during this phase's own search).
3. **`principal_id`** — **searched exhaustively this phase** (grep across `src/pcae/core/*.py`, `tests/`, `docs/contracts/`) for a canonical derivation formula or fixed vocabulary. **None exists.** `HBDC-REQ-058` states these fields are drawn "from the admin's own enrollment context, not from repository-local state or agent-supplied input," and cross-validation against any `principals`/`signers` registry entry is explicitly, contractually deferred (149O.20L.7H finding, confirmed still current in the module's own docstring). **Independently confirmed via live Dell read (§10): `/etc/pcae/hatp/trust-store/registry.json` is absent — the production trust store has zero enrolled principals, signers, authorities, or bindings of any kind today.** There is no existing registry entry to reference even if cross-validation were performed. This value must be a genuine, fresh administrative enrollment decision; this document does not invent one.
4. **`signer_key_id`** — same disposition as (3), same empty-registry confirmation. No canonical value exists to read.
5. **`provider_profile`** — same disposition as (3)/(4) as far as the *DeploymentBinding* schema's own validation goes (non-empty-string shape only, HBDC-REQ-058). One partial, non-authoritative data point independently found this phase: `HATP_HARDWARE_PROVIDER_V1` is a real production constant (`src/pcae/core/hatp_providers.py`) used consistently, without exception, everywhere a concrete hardware-provider profile string appears in this codebase's own production code (`hatp_ag_authority.py`, `hatp_rollback_consumption.py`) and its entire test suite. This is suggestive of the value a human administrator would plausibly choose for a hardware-provider-backed binding, but it is **not** a value the `DeploymentBinding`/HBDC schema itself derives, requires, or cross-validates — it remains an administrative choice, not invented as canonical here.
6. **`authority_scope`** — searched the same way; only one non-test-fixture value pattern was found anywhere in the codebase (`"rollback"`, used in HATP rollback-consumption test fixtures) and the contract text (`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) is **silent** on an enumerated vocabulary for this field beyond "from the admin's own enrollment context." No wildcard, no default, no minimum-scope constant exists in source. Must be a genuine, narrow, deliberate administrative choice.
7. **`valid_from`** — `_canonical_timestamp_now()`: `datetime.now(timezone.utc)` formatted to millisecond precision with a trailing `Z`, asserted at generation time against the module's own strict regex (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`). No caller-supplied override exists (confirmed: `create_deployment_binding`'s signature has no `valid_from` parameter). Only the **generation rule** is knowable pre-election; the exact value is inherently execution-time.
8. **`status`** — `"active"` on `create_deployment_binding`; the schema's own status-set validator (`_STATUS_VALUES` / `_require_status`, read directly) allows only `{"active", "revoked"}`.
9. **`revoked_at`** — `None` on creation; `_require_revoked_at_consistency` enforces, on both read and write, that `revoked_at is None` iff `status == "active"` and is required iff `status == "revoked"`. Only `revoke_deployment_binding()` ever sets it.

## 18. Field-Resolution Verdict

**BINDING PROPOSITION STILL BLOCKED ON FIELD RESOLUTION** — independently confirmed, separate from RI-D's validity (§15, which is independently verified valid). Four of nine fields (`repository_id`, `principal_id`, `signer_key_id`, `valid_from`) are inherently unresolvable until a real identity-creation execution step runs; two more (`provider_profile`, `authority_scope`) have **no canonical source-derivable value** and, per the live Dell registry read (§10/§17), **no existing enrollment record to reference either** — they require a genuine, fresh, human administrative decision that this document does not manufacture.

## 19. Signer/Provider Prerequisite Chain

Because the production trust-store registry on Dell is completely empty (§10, §17) — no `principals`, no `signers`, no `authorities`, no `deployment_bindings` array present at all, not merely no binding for this repository — resolving `principal_id`/`signer_key_id` is not simply "look up an existing registry row." **A prerequisite enrollment decision (who the administrative principal is, what signer key backs them, per what provider) must be made and recorded before an exact `DeploymentBinding` proposition naming real, non-placeholder values for those two fields can be drafted**, independent of and prior to whatever future phase performs the identity-creation step. Identity creation itself remains independently useful and correctly sequenced first regardless (§16) — this prerequisite chain blocks the *binding proposition's exact field values*, not the identity-creation step.

## 20. Producer Preview Requirement — Reproduced

```
preview_create_deployment_binding(repository_root=<no identity yet>, ...)
  → RepositoryIdentityMissingError                      # confirmed, before identity exists

ensure_repository_identity(root)                          # identity now exists
preview_create_deployment_binding(repository_root=..., ...)
  → DeploymentBindingPreviewKind.WOULD_CREATE             # confirmed, becomes available
```

Independently reproduced exactly as predicted: the preview function's *first* internal call is `_resolve_repository_id()`, which itself calls `read_repository_identity()` and raises before any preview logic executes if identity is absent — confirmed by reading the function body, not merely by observing the exception.

## 21. Disposable Simulation Reproduction (Full Sequence, From Scratch)

Executed against two disposable directories (`tempfile.TemporaryDirectory()`), a synthetic repository root and a synthetic Protected Root passed via the producer's own private `_protected_root=` test-only seam — never this repository's `.pcae/`, never the real Dell trust store:

```
1. read_repository_identity(root)                        → None
2. preview_create_deployment_binding(...)                → RepositoryIdentityMissingError
3. ensure_repository_identity(root)                       → generated (repeat call, same UUID)
4. preview_create_deployment_binding(...)                 → WOULD_CREATE, candidate binding shown
5. create_deployment_binding(...)                          → outcome=CREATED
6. HATPTrustStore(_test_only_root=...).load_repository_enrollment(id)
                                                            → binding loaded, status='active'
7. hatp_bootstrap.deployment_binding_matches(binding, repository_id=id, canonical_deployment_root=root)
                                                            → True
8. create_deployment_binding(... same authority ...) retried
                                                            → outcome=ALREADY_SATISFIED (idempotent)
```

Every step behaved exactly as the production code's own signatures/docstrings specify. This independently reproduces every claim in 7O §7 from a fresh script written for this phase, not reused from 7O's own (uncommitted, disposable) simulation script.

## 22. Full HBDC Simulation — Result and Limitation (Restated Precisely)

See §14. `verify_class_b_deployment_conformance()` cannot reach `COMPLIANT` off real Dell topology by construction (20/34 checks are topology-specific); only the identity/binding-specific check (`HBDC-REQ-042`) and the Model-A editable-install check are meaningfully exercisable in a disposable local simulation, and both were independently exercised (§13, §14).

## 23. Audit-Durability Gap — Reproduced by Actual Execution

Located the exact code path (`hatp_deployment_binding_admin.py::create_deployment_binding`): validate → resolve → acquire lock → write registry atomically → read back and verify → **release lock** → emit audit event (`_audit()`, calling `append_provenance_event`) → return. If `_audit()` raises, the exception propagates uncaught — by this point the trust-store mutation is already durable, verified, and outside the lock.

**Reproduced by actually monkeypatching `append_provenance_event` to raise, not merely by reading the docstring's own description:**

```
hdba.append_provenance_event = <raises RuntimeError>
create_deployment_binding(...) → RuntimeError propagates to caller, uncaught
# but:
registry read back directly → binding present, status == 'active'
parsed via hatp_bootstrap._parse_registry_document(raw) → binding.status == 'active'
```

**Confirmed: the binding is durably active despite the caller receiving an exception that looks like total failure.** This exact scenario is real and reproducible, not hypothetical.

**One refinement beyond 7O's own disposition, found only by executing (not reasoning about) the retry path:** `_COMPARED_AUTHORITY_FIELDS` (the tuple `create_deployment_binding` uses for its idempotency comparison) is `("canonical_deployment_root", "principal_id", "signer_key_id", "provider_profile", "authority_scope")` — **`election_reference` is not among them.** A retry of `create_deployment_binding` with a fresh `election_reference` (e.g. a genuinely new CHGR id, if an operator mistakenly believed the first attempt failed outright and re-ran it under a fresh election) against an otherwise-field-identical candidate will silently return `ALREADY_SATISFIED` and emit only a `deployment_binding_create_noop` audit event — **the original `created` audit event, with the original `election_reference`, is never recovered; it simply never existed.** The registry itself does not store `election_reference` at all (only the audit trail would have; confirmed by reading `_deployment_binding_to_document`, which serializes only the 9 schema fields). This is a genuine, permanent evidentiary gap for that one specific creation event's election linkage — narrower than "the whole audit trail is lost" (the binding's *current authority-bearing content* is always exactly reconstructable from the live registry, per §21 step 6-7), but real.

## 24. Audit-Gap First-Use Severity — Independent, Conservative Verdict

Can future execution always determine whether the binding became durable after such an exception? **Yes** — `HATPTrustStore.production().load_repository_enrollment(repository_id)` (or the raw registry read used in §23) always reflects true, durable, current state regardless of the audit path's outcome; this was directly exercised, not assumed. Can it reconstruct *sufficient* evidence afterward? **Partially**: the authority-bearing state itself is always exactly reconstructable and never ambiguous (HBDC/consumers will correctly treat the binding as active); the specific *election_reference* tied to the original creation call can be permanently lost if audit emission fails and no compensating record is made before any retry occurs (§23's refinement).

Being conservative, as instructed: this is a genuine, disclosed (by the module's own docstring) gap against `HBDC-REQ-062`'s "every operation... SHALL emit exactly one... audit record" language. It is not silent to the *immediate operator* — the exception is loud, uncaught, and unambiguous — but it is silent to *future automated or delegated review* that trusts the audit trail as complete without independently cross-checking the live registry.

**Verdict: NON-BLOCKING FOR FIRST USE**, conditional on a concrete, named procedural mitigation that 7O's own §15 gestures at but does not spell out to this level of precision: whichever future execution phase performs the real `create_deployment_binding()` call **must**, regardless of whether the call raises or returns normally, immediately (a) read back the live registry entry directly, (b) independently confirm whether the corresponding audit/provenance record exists, and (c) if the mutation is durable but the audit record is absent, **manually write a compensating provenance note recording the true `election_reference` and outcome before any retry of `create_deployment_binding` is attempted** — because a retry's own idempotent-noop audit event will not backfill the original election linkage (§23). This is a sharper, execution-actionable version of 7O's own "immediate audit-presence re-verification" condition, not a contradiction of it.

**Rationale for non-blocking rather than blocking:** (a) this is the *first* binding for this repository — no pre-existing valid state a silent failure could obscure or corrupt; (b) the durable authority state is always independently and exactly re-verifiable regardless of audit-path outcome (§23, §21); (c) the risk is scoped to *evidentiary linkage* for one specific field, not to authority correctness or HBDC-decision correctness, both of which remain exactly right in all observed cases; (d) blocking first use entirely on this gap, given (a)-(c), would leave HBDC permanently `NON_COMPLIANT` for a risk that is real but narrow and independently detectable — a worse outcome on net.

## 25. Contract Compliance of Missing Audit

`HBDC-REQ-062` ("every operation... emits exactly one... audit record") is a genuine `SHALL`-class contract requirement that this producer's current implementation **can** violate under the exact reproduced failure mode (§23). This is a real, disclosed, unrepaired gap against normative contract text — correctly named by 7O as a "known, named limitation... not an oversight," and independently reconfirmed here by actual execution rather than by trusting that characterization. It does not, on the evidence gathered this phase, rise to blocking-before-first-use severity (§24), but it is not fully compliant either, and should be named as an open item for a future hardening phase (a real two-phase-commit, or an automatic compensating-audit-write on `_audit()` failure) before high-volume or unattended `create_deployment_binding` use — first use specifically remains acceptable under the procedural mitigation named in §24.

## 26. Immediate Audit-Presence Verification Sufficiency

Detection (an after-the-fact registry read-back) does not *prevent* the audit-record-missing state from having occurred — it can only surface it after the fact. Independently, conservatively assessed: detection alone is **not** sufficient to fully close the gap (it cannot recover a lost `election_reference` if a retry has already happened without the §24 procedural step), but it **is** sufficient to make the *first-use* risk acceptable, because it guarantees the gap, if it occurs, is caught before it can compound (no second, uninformed retry silently papering over it) — provided the §24 procedure is actually followed by whichever phase executes the real mutation. This is the same conclusion 7O reached, reached here independently and with the added precision of the election_reference-specific failure mode.

## 27. Audit-Gap Verdict

**NON-BLOCKING FOR FIRST USE.** Contractual rationale: §24-§26.

## 28. Timestamp Parser Gap

`hatp_bootstrap._parse_iso_timestamp` (the consumer/read-path parser) is more permissive than the strict producer-output grammar (`_TIMESTAMP_PATTERN` in `hatp_deployment_binding_admin.py`) used by `_canonical_timestamp_now()`. Independently reconfirmed scoped to the *read* path only: the producer always emits strict-grammar timestamps, asserted against its own regex at generation time (`assert _TIMESTAMP_PATTERN.fullmatch(value)`), and the trust store is admin-write-protected (only the correct principal, §10, can ever write a malformed timestamp there). **Operationally acceptable for first use**, not repaired here (no code changed this phase).

## 29. HMIC-REQ-103 Consequence

Read directly: "HATP-001 introduces no change to `pcae push` consumption of the Permission Broker Foundation (PBPC-001 v1.2, unamended)." **Confirmed irrelevant** to RepositoryIdentity/DeploymentBinding first use — it concerns `pcae push`/Permission Broker consumption, an unrelated subsystem. Carried forward as not-applicable, independently reconfirmed by reading the requirement text directly rather than trusting its prior characterization.

## 30. HMIC-REQ-063 Consequence

Read directly (`HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`): the named residual limitation is import-shadowing/executed-code-binding — `implementation_scope_digest` proves on-disk byte identity of the frozen set, not that the running interpreter actually resolves imports to those exact files at runtime; explicitly out-of-scope, not solved, by design ("Option C... explicitly preserved, not solved"). **Confirmed irrelevant to initial DeploymentBinding creation specifically** — it is a certification-time/executed-source-attestation concern, not a binding-creation concern; this document (like 7O before it) makes no attestation claim beyond diagnostic *behavior*.

## 31. Fresh Read-Only Dell State (This Session)

Independently re-confirmed live, this session (§10):

- Candidate SHA at `/opt/pcae/runtime/src`: `b0840e96a7ffb12308e95828aa5927c3e7c770c0` — matches entering state exactly.
- RepositoryIdentity: absent (`.pcae/repository-identity.json` — no such file).
- DeploymentBinding: absent (`/etc/pcae/hatp/trust-store/registry.json` — no such file); trust-store directory exists, empty, correctly `root:pcae 0750`.
- No write command of any kind was issued against Dell this phase — only `git rev-parse`, `ls`, `cat`, `id`, `sudo -n true`, all via `sudo -n` as `codex`.

## 32. Source Currentness Result

```
Mac HEAD:  d4d5614db89a8f1bb40d5886059e2e0fb6351489
Deployed:  b0840e96a7ffb12308e95828aa5927c3e7c770c0
git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -- src/pcae/
  → (no output — zero bytes of src/pcae/** drift)
```

10 commits separate Mac HEAD from the deployed candidate (all from Phase 149O.20L.7O itself: docs, `.pcae/` metadata, `tasks/`, `CHANGELOG.md`/`PROJECT_STATUS.md` — none under `src/pcae/`, `scripts/`, `docs/contracts/`, or `schemas/`). **Source remains current: no authority-bearing drift exists between the deployed candidate and Mac HEAD.** No redeployment is required before Transition 2 may proceed on source-currentness grounds. This independently reconfirms the HMIC digest match in §12 as well (identical digest is only possible because no frozen-set file changed).

## 33. Existing Source-CHGR Scope Result

Both cited CHGRs read directly from `.pcae/publication-execution/records/`:

- **`chgr-0e37ed1340b14311826722c4dbf3e856`** (2026-08-15, superseded source-transition election): condition 6 is an exhaustive six-category exclusion ("no venv reinstall, no wrapper mutation, no DeploymentBinding, no Boundary C, no Boundary A, no Cutover Record, no Permission Broker/POL-005/COMP-002 change, and no repository onboarding... without a fresh, separate election"). **`RepositoryIdentity` is not named in this list** — independently confirmed consistent with §7-§8's finding that identity creation needs no election in the first place (its absence from an election-requiring exclusion list is not a gap; nothing here requires that exclusion to exist).
- **`chgr-71bd24f9d3d742d6baac772e480fc876`** (2026-08-17, current, governs the *now-deployed* source transition): condition 7, read verbatim: "No RepositoryIdentity creation authorized: no `pcae init`, no `ensure_repository_identity()`, no `.pcae/repository-identity.json` write, on Dell or elsewhere." Condition 8: "No DeploymentBinding creation, rotation, or revocation authorized... producer presence does not authorize invocation." Condition 17: "First-use transition (RepositoryIdentity + DeploymentBinding) remains separately gated — a distinct future phase, its own proposition, verification, election, and CHGR."

**Independently confirmed: neither CHGR is authority for RepositoryIdentity or DeploymentBinding creation.** Condition 7's explicit prohibition proves this CHGR is *not authority for the mutation* — as this phase's own governing instruction correctly anticipated, this does **not** by itself prove an election *is* required for RepositoryIdentity specifically (that question is independently settled, separately, by HBDC-REQ-068 in §7-§8, on stronger grounds than mere absence-from-a-CHGR). Condition 17's bundling of "RepositoryIdentity + DeploymentBinding" under one description of a future gated "election" is read as referring to the *binding* election that transition as a whole culminates in, not as itself establishing that identity creation individually requires a vote — that reading would contradict HBDC-REQ-068's own unambiguous text, which this document treats as controlling on this specific question since it is the more specific, more recent, and more directly on-point normative statement.

## 34. Generic Init/Bootstrap Authority Result

`pcae init` (`commands/init.py`) already calls `ensure_repository_identity()` today as an ordinary, non-privileged, already-existing repository-bootstrap operation with no election gate — independently confirmed by reading the command's source. This is a real, existing generic-authority precedent for identity creation requiring no dedicated election, consistent with (not merely parallel to) HBDC-REQ-068's explicit disposition.

## 35. Preview Behavior

See §20 — reproduced exactly: preview fails with `RepositoryIdentityMissingError` before identity exists, succeeds (`WOULD_CREATE`) immediately after.

## 36. Independent Disposable Simulation

See §21 — full from-scratch reproduction, fresh script, not reused from 7O's own.

## 37. Full HBDC Simulation Limitations/Result

See §14, §22.

## 38. Future Phase Decomposition — Independently Assessed

7O's §10 decomposition (7O.2 identity-creation-and-proposition-drafting → 7O.3 independent verification → 7O.4 election+CHGR → 7O.5 execution → 7O.6 independent real-host verification → 7O.7 Boundary-C prep) is **independently assessed as correctly shaped**, given: RI-D is independently confirmed valid (§15), field resolution is independently confirmed still blocked pending a genuine enrollment decision (§18-§19), and the audit-durability procedural mitigation (§24) is a natural addition to whichever step actually executes `create_deployment_binding` (7O.5-equivalent) rather than requiring its own phase. This document's own recommended next-phase numbering follows §41 below, using the ID this project's task-creation convention will actually assign (mirroring how 7O.1's own ID was assigned at the moment this phase was opened, not predicted in advance).

## 39. Strategic Breakpoint

Preserved, unchanged, per the governing prompt's own §60: after first-use `DeploymentBinding` + HBDC reaches clean, independently-verified `COMPLIANT` on real Dell, pause before Boundary C, then begin (1) DeepSeek Harness vs. PCAE comparative architecture study, (2) PCAE Runtime Adapter + Plugin Architecture. Not reached or altered by this phase.

## 40. Proof — No Authority-Bearing Action Taken This Phase

- **No RepositoryIdentity:** confirmed absent both at phase entry and phase end via live Dell read (§10, §31); the only identities ever generated anywhere this phase were synthetic, disposable, local-tempdir values (§4, §21), all deleted with their containing `TemporaryDirectory`.
- **No DeploymentBinding:** confirmed absent both at phase entry and phase end (§10, §31); the only bindings ever created were synthetic, disposable, local-tempdir values (§21, §23), never against the real Protected Root.
- **No election:** no APPROVE/DECLINE/AMEND presented anywhere in this document.
- **No CHGR:** no publication-execution write performed this phase; §33 only *read* existing CHGR records.
- **No certification:** `hatp_mandatory_certification.py` was read (§12) but no certification function was invoked; only `derive_implementation_scope_digest` (a pure read-only digest function) was called, and only against disposable copies.
- **No Dell mutation:** every SSH/`sudo -n` command issued this phase (§10, §31) was `git rev-parse`, `ls`, `cat`, `id`, `sudo -n true` — no `git fetch`/`checkout`/`chown`/`chmod`, no `python3 -c "...ensure_repository_identity..."` or `...create_deployment_binding...` was ever run against Dell's real filesystem or trust store.

## 41. Tests / Governance Results

No new test module was added or existing test modified this phase (verification-only; no production code changed). Verification performed via fresh disposable Python scripts (§4-§5, §12-§14, §20-§23) and live read-only Dell SSH commands (§10, §31), all shown inline above rather than committed as scratch artifacts.

- `pcae_check`: passed
- `pcae_health`: healthy
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — identical historical `tasks/done/`/`DONE.md` sync gap carried forward from 7O and earlier phases; not remediated here, outside this phase's allowed-file scope)
- `pcae_push_check`: clean (at entry)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: telegram configured/enabled
- `pcae_phase_report_reconcile_149O_20L_7O`: reconciled, 2 generations promoted, marker already_dispatched, checkpoint completed, receipt finalized, mutation none
- `dell_read_only_preview`: passed — exact SHA/identity-absence/binding-absence match expected baseline
- `disposable_local_simulation`: passed — idempotency, partial-failure, preview-gating, create/match/idempotent-retry, HMIC-digest-invariance, and audit-durability-gap reproduction all behaved exactly as independently read from production source
- `no_dell_mutation_no_repositoryidentity_no_deploymentbinding_no_election_no_chgr_no_certification`: passed (§40)
- `report_notification_tests`: not_applicable_this_phase (no production notification-path code changed)
- `bootstrap_session_reporting_tests`: not_applicable_this_phase (no production bootstrap/session-reporting code changed)
- `fast_green`: deselected confirmation run 7789 passed, 5 skipped, 0 failed, 0 errors (raw unfiltered run: 258 failed, 7789 passed, 5 skipped, 26620 deselected, 10 errors — all independently confirmed pre-existing and unattributable to this phase; `git diff --stat b0840e96a7ffb12308e95828aa5927c3e7c770c0..HEAD -- src/pcae/ tests/` returns empty, so nothing this phase touched could have caused any of them. The 10 errors are one missing-dependency collection failure — `ModuleNotFoundError: No module named 'fido2'`, a local venv/environment gap, not a code change — plus 9 fixture-setup errors within that same file. The 258 failures are dominated by `test_phase_149o_20e_...py` and several `test_phase_149o_20l_7*.py` modules asserting stale, superseded snapshot values (e.g. HBDC contract pinned to v1.0, HMIC pinned to v1.2, a 25-file frozen set) that later, already-landed phases legitimately advanced (HBDC now v1.1, HMIC now v1.4, 30-file frozen set) — this is drift in already-completed prior phases' own test fixtures, not a regression this phase introduced.

## 42. Commits / Push / origin..HEAD

Recorded in `.pcae/phase-completion-metadata.json` at finalization, per the governed `pcae phase complete`/`pcae push`/`pcae promote` sequence. See phase-completion metadata for the exact commit list, pushed status, and `origin/main..HEAD` count as of finalization.

## 43. Final Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — RI-D VALID.**

RI-D is independently re-derived and confirmed as the correct model (§15), on primary-source grounds that are, on one specific point (HBDC-REQ-068, §7), *stronger* than what 7O's own document cited — an independent strengthening of 7O's conclusion, not merely a repetition of it. RepositoryIdentity creation is confirmed to confer no authority (§6) and to require no election (§7-§8, §33-§34). Field resolution for the eventual `DeploymentBinding` proposition remains genuinely blocked pending a real administrative enrollment decision for `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` (§17-§19) — this is a separate, orthogonal finding from RI-D's validity, exactly as the governing prompt anticipated it should be kept separate. Two bounded, non-blocking findings were independently surfaced this phase, both narrower refinements of gaps 7O already disclosed, not new categories of risk: (a) the `pcae`-principal execution requirement for identity creation on Dell's root:pcae topology (§10), not previously named this explicitly; (b) the `election_reference`-specific evidentiary-loss mechanism within the already-known audit-durability gap (§23-§24), found only by actually executing the failure rather than reasoning about it.

RepositoryIdentity remains absent. DeploymentBinding remains absent. No election has occurred. HBDC remains `NON_COMPLIANT` with sole residual `HBDC-REQ-042`. HMIC remains not certified. Boundary C/A remain not authorized.

## 44. Recommended Next Phase

**149O.20L.7O.2 — RepositoryIdentity Creation on Dell (unelected, administrative, `pcae`-principal-executed) + Exact DeploymentBinding Proposition Drafting**, per 7O's own §10 decomposition (independently assessed correct, §38), with two concrete additions this phase's own findings require folding in: (1) the identity-creation step must execute as the `pcae` OS principal specifically, not bare root (§10); (2) the enrollment-decision prerequisite for `principal_id`/`signer_key_id`/`provider_profile`/`authority_scope` (§17-§19) must be resolved as part of that phase's own proposition-drafting work, since no existing registry entry exists to reference. Recommendation only — not initiated in this phase.
