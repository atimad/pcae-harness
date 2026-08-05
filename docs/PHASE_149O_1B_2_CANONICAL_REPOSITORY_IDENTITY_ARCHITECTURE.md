# Phase 149O.1B.2: Canonical Repository Identity Architecture

**Phase type:** repository-identity architecture only (blocking
prerequisite for HATP-001 freeze, flagged by 149O.1B.1). No
implementation, no `.pcae` initialization change, no OS changes, no
contract freeze.

**Status:** completed. **Architecture verdict: CANONICAL REPOSITORY
IDENTITY ARCHITECTURE DEFINED — READY TO RESUME HATP CONTRACT FREEZE.**

## 1. Starting Position (independently reconfirmed)

- `git status --short`: clean. `git status --branch --short`:
  `## main...origin/main`. `git rev-list --count origin/main..HEAD`: 0.
- Latest completed phase: 149O.1B.1 — **HUMAN APPROVAL BOOTSTRAP
  AUTHORITY ARCHITECTURE DEFINED — REPOSITORY IDENTITY PREREQUISITE
  REMAINS**, commits `63caaee2`, `de59c8f6`, pushed.
- `pcae health` / `pcae check` / `pcae status coherence` / `pcae doctor
  task-memory`: healthy / passed / coherent / clean. `pcae push check`:
  nothing to push. `pcae runtime inspect`: Observed / observe /
  unavailable. `pcae notify status` (after `source
  ~/.config/pcae/telegram.env`): Telegram configured, enabled, ready.
  `pcae phase-report reconcile --phase-id 149O.1B.1`: reconciled,
  receipt finalized, mutation none.
- HATP Root 1 (hardware-backed signing + non-exportable key + fresh
  physical human-presence event), Root 2A (externally anchored device
  attestation, conceptual), and Root 2B (Bootstrap Model Class B,
  two-principal topology: Agent OS principal vs. combined
  Human-Approver/Bootstrap-Admin OS principal) are all selected and are
  **not reopened** by this phase.
- Actual current deployment: same OS user for human and agent — HATP
  bootstrap environment **NOT READY**. This phase does not provision
  the OS boundary; that remains future deployment work, unchanged.
- This phase does **not** implement repository IDs, does not touch
  `src/pcae/**`, does not change `.pcae` initialization behavior, does
  not create OS users/ACLs, does not freeze HATP-001.

## 2. Scope Discipline

Per the governing prompt, 149O.1B.1's Root 1 / Root 2A / Root 2B
selections are frozen inputs to this phase, not reopened. This phase's
entire job is the one prerequisite 149O.1B.1 flagged as BLOCKING and
left unresolved: what constitutes *one PCAE repository instance* for
the purpose of scoping HATP repository-specific rollback-approval
authority, how that identity is created, how it survives legitimate
moves, and when it must intentionally *not* survive copying/cloning.

## 3. Primary-Source Reconstruction (independently rechecked, this phase)

149O.1B.1's conclusion ("no suitable stable canonical repository
identity exists") was independently rechecked rather than trusted.
Grep sweep across `src/pcae/**` and `.pcae/**` for `repository_id`,
`repo_id`, `repository_identity`, `project_id`, `workspace_id`,
`installation_id`, `instance_id`, `root_id`, `uuid`, `origin_url`,
`remote_url`, `git_dir` found every existing candidate:

| Candidate | Location | What it actually is |
|---|---|---|
| `repository_identity` (CLTR schema field) | `src/pcae/cltr_prototype/identity.py:98`, `cltr_prototype/models.py:254`, `cltr/models.py:49,97,174` | Required string field, populated in production as `repository_identity=phase_id` (`core/finalization_transaction.py:934,966`; `cltr/migration/cltr_derivation.py:63,150`) — the phase/task label, not a repository fact. Changes every phase. |
| `repository_identity` (snapshot builder) | `.pcae/repository-intelligence/latest.json:592`, built by `src/pcae/repository_intelligence/snapshot_builder.py:518-522` | `{"identity_type": "repository_name", "identity_value": <pyproject.toml [project] name, or literal "pcae-harness" fallback>}`. Human-editable config string. |
| `project_id` | `src/pcae/core/memory_snapshot.py:136` | Hardcoded literal `"pcae-harness"`. Not read from any config; a constant. |
| `_git_origin_count`, `_git_head_commit`, `_git_branch` | `core/memory_snapshot.py`, `core/project_state.py`, `core/gate_dry_run_context.py`, `core/governance_timeline.py`, `core/commit_push_preflight.py` | Live git facts used for status/health snapshots (dirty tree, branch, ahead/behind count). Never persisted as a stable ID. |
| `git_dir` | `core/tasks.py:1067`, `commands/task.py:1496-1516` | `.git` directory existence/writability check for preflight diagnostics only — not an identity value. |
| UUID generation | `core/human_approval_gate.py:177-179` (`chgr-<uuid4>`) | Scoped to individual approval requests/decisions/audit records — session/event-scoped, not repository-scoped. |
| `repo_root` / `root_id` | scattered across `src/pcae/**` | Always the `Path` variable name for "repository root directory" — a filesystem path, not an identity field. |

No hits at all for `repo_id`, `workspace_id`, `installation_id`,
`instance_id` as identity concepts. No code anywhere reads `git remote
get-url origin` and persists it as an identity value.

**Independent verdict: confirmed.** Every field literally named
`repository_identity` in this codebase today is either the current
phase's own label (changes every phase) or a human-editable
`pyproject.toml` string with a hardcoded fallback. Neither is
mechanically derived, protected, content-addressed, or instance-scoped.
149O.1B.1's finding stands.

## 4. Candidate Classification

| Candidate | Classification | Why |
|---|---|---|
| `repository_identity`=`phase_id` (CLTR) | TASK_SCOPED, MUTABLE, UNSUITABLE | Changes every phase; never meant to identify a repository instance. |
| `repository_identity`=`pyproject.toml` name | CALLER_CONTROLLED, MUTABLE, COPYABLE, UNSUITABLE | Human-editable; identical across every clone/copy/fork by construction. |
| `project_id`="pcae-harness" constant | CALLER_CONTROLLED, UNSUITABLE | Hardcoded; identical for every checkout of this codebase, including forks. |
| Git remote URL | GIT_DERIVED, MUTABLE, COPYABLE, UNSUITABLE alone | Mutable (`git remote set-url`), absent for offline/local repos, identical across clone/fork by construction. |
| Git HEAD / initial commit | GIT_DERIVED, COPYABLE, UNSUITABLE alone | Identical across every clone and fork by construction — the opposite of instance-scoping. |
| `.git` object graph | GIT_DERIVED, COPYABLE, UNSUITABLE alone | Same lineage shared by clones/forks/worktrees; does not distinguish instances. |
| Absolute filesystem path | PATH_DERIVED, MUTABLE, UNSUITABLE alone | Fails the explicit "must survive legitimate move" requirement if used as sole identity. |
| Session ID / agent-lock ID | SESSION_SCOPED, UNSUITABLE | Rotates per session; not repository-scoped. |
| CHGR `uuid4` audit IDs | ARTIFACT_SCOPED, UNSUITABLE | Scoped to one approval record, not the repository. |
| **A newly minted random repository-instance UUID (not yet implemented)** | Would be STABLE, not CALLER_CONTROLLED, not PATH_DERIVED, not GIT_DERIVED if generated once and persisted | The only candidate shape that can satisfy §5 below — but does not exist in the codebase today (§107: repository identity remains NOT IMPLEMENTED). |

No existing field satisfies HATP's authority-scoping requirement. This
confirms, rather than merely repeats, 149O.1B.1's blocking finding.

## 5. Required Identity Properties

A canonical PCAE repository identity must be:

1. Unique with negligible collision probability.
2. Created once, under a defined lifecycle event (not implicitly, not
   on every read).
3. Stable across normal filesystem path moves and renames.
4. Not derived solely from current path.
5. Not derived solely from Git remote URL.
6. Not derived solely from current HEAD or object graph.
7. Not caller-selectable at approval time.
8. Not silently regenerated during normal operation.
9. Not silently shared by unrelated PCAE repository instances.
10. Parseable and versioned (schema-tagged).
11. Usable as a HATP repository-authority *scope key* — but, per §9
    below, **not usable as authority proof by itself**.

No existing candidate in §3/§4 satisfies more than one or two of these
simultaneously; several (path, remote URL, HEAD) actively violate
property 3, 4/5/6, or 9.

## 6. Random vs. Deterministic Identity

- **Random persistent UUID, created once at initialization, persisted
  thereafter.** Simple, independent of Git/path, stable under moves,
  negligible collision probability. Risk: a copied working tree copies
  the UUID verbatim (§12, §26) — this risk is real but, per §9, is a
  problem for the *authority layer*, not a reason to reject the
  identity layer.
- **Deterministic Git-derived identity** (remote URL / initial commit /
  object graph). Rejected as primary identity: forks and clones share
  these by construction (§4), remote URLs mutate, and offline/local
  repos may have no remote at all (§18). Insufficient alone.
- **External/bootstrap-assigned identity** (issued by the protected
  HATP bootstrap authority itself). Would work but unnecessarily
  couples general-purpose PCAE repository identity to HATP deployment
  specifically (§100/§56 below argue identity generation itself should
  require no privilege, which an HATP-issued ID would forfeit).
  Rejected as the *primary* mechanism; the protected HATP registry
  instead *binds* an independently generated ID (§9).

**Selected primitive: random persistent PCAE repository-instance
UUID**, generated once at a defined initialization event and persisted
in repository-local, agent-readable, non-privileged metadata.

## 7. Repository Instance vs. Repository Lineage

Distinguished explicitly: **Git repository identity** (remote URL,
`.git` object graph, HEAD, branch, commit history — *lineage*) is not
the same concept as **PCAE repository-instance identity** (one
concrete, currently-existing working tree that PCAE governs — *
instance*). Two clones share lineage but must not, by default, share
instance identity, because HATP authority must not silently duplicate
across them (§26/§78/§79). HATP needs **instance** identity. Verified:
none of the git-derived facts in §3/§4 are instance-scoped, so this
distinction is load-bearing, not academic — it is the reason §3's
Git-derived candidates are rejected even though they are individually
"stable."

## 8. The Mandatory Copy/Clone Attack — and Why a Bare UUID Is Not Enough

Mandatory attack model (governing prompt §26/§77/§78/§79/§87/§88),
restated precisely:

```
Repository A: authorized, repository_id = X
Protected HATP registry: X -> Alice authorized
Agent copies all of Repository A (including repository_id = X)
  to Repository B (`cp -R`, `git clone` that happens to carry
  the file, or manual duplication)
Does Repository B now carry Repository A's approval authority?
```

**If HATP authority were looked up by `repository_id` alone: yes, and
that is unacceptable.** A UUID is an *identifier*, not a *credential*
(§48/§82) — the same conceptual class of mistake 149O and 149O.1
already corrected for approval receipts elsewhere in this
architecture's history (rollback-evidence canonical-provenance
hardening). Repeating it here for repository identity would silently
reopen a rollback-approval authority-transfer hole. Therefore
repository-instance identity **alone cannot be the HATP authority
root**. A second, protected layer is mandatory.

## 9. Two-Layer Model (selected)

**Layer 1 — PCAE repository-instance identity** (this phase's subject):
a repository-local, random, persisted `repository_id`
(`PCAERepositoryIdentity.repository_id`, conceptual — not implemented
this phase). Agent-readable. Confers **no authority by itself**.

**Layer 2 — HATP protected deployment binding** (Root 2B's admin-owned,
agent-unwritable trust store; already established conceptually by
149O.1B.1, not reopened here): an admin-owned record binding

```
repository_id
  -> canonical local deployment root (resolved, symlink-free path)
  -> authorized approver principal / key
  -> authority scope
  -> status
```

HATP authority exists **only** where Layer 2 explicitly says so. Layer
1 alone establishes nothing. This directly answers §8: Repository B
carries `repository_id = X`, but Layer 2's protected registry maps `X`
only to Repository A's canonical deployment root; Repository B's root
does not match, so the lookup fails closed. **Copying the identifier
does not copy the binding**, because the binding lives in Class-B
admin-owned, agent-unwritable storage that a same-user agent copy
operation cannot read, let alone reproduce, at the correct protected
path.

This is **CRI Model A** per the governing prompt's §90 framing.
Alternatives briefly compared and rejected: **Model B** (pure
Git-derived identity, §6/§4 — rejected, forks/clones share it
mechanically); **Model D** (pure path-derived identity — rejected,
fails the explicit move-survival requirement and is trivially spoofed
by `cp -R` to any path). **Model C** (externally/HATP-assigned
identity) is subsumed by Layer 2 rather than rejected outright: Layer
2's binding *is* the externally-assigned-authority layer; Layer 1 stays
general-purpose and HATP-independent so other PCAE subsystems (audit,
artifact lineage — §51) can use it without any HATP coupling.

**CANONICAL REPOSITORY IDENTITY MODEL A SELECTED.**

## 10. Mandatory Security Statements

> Knowledge or possession of a repository identifier does not grant
> HATP authority. Authority exists only when the protected bootstrap
> registry binds that repository identity to the current enrolled
> deployment and authorized approver.

> Copying or cloning repository-local identity metadata SHALL NOT by
> itself transfer human-approval authority.

> Repository identity remains stable across a legitimate move, but HATP
> deployment authorization may require bootstrap-admin re-binding when
> the protected deployment locator changes.

All three are load-bearing normative statements for the future CRI/
HATP contract text; none are implemented this phase.

## 11. Path Move, Rename, Restore, Copy, Clone, Fork, Worktree — Scenario Matrix

| Scenario | Repository ID (Layer 1) | HATP enrollment/authority (Layer 2) |
|---|---|---|
| Path rename (`mv repo repo2`, same parent) | preserved (moved with repo) | requires admin re-bind (canonical root changed) |
| Path move (`mv /old/repo /new/repo`) | preserved | requires admin re-bind (canonical root changed) |
| Normal commit | unchanged | unchanged |
| Branch switch | unchanged | unchanged |
| Remote URL change (`git remote set-url`) | unchanged | unchanged (remote URL is never part of the binding, §18) |
| `git clone` (fresh clone, no `.pcae` identity metadata carried — normal convention, §12/§13) | **new** ID generated at that clone's own future initialization | none until independently enrolled |
| `git clone` in a hypothetical convention where `.pcae` identity metadata *is* tracked/copied (§14) | copied verbatim — **architecturally unacceptable** unless re-identified | must **not** be authorized automatically; requires explicit re-identify/re-enrollment before any authority exists (§9 Layer 2 lookup still fails on canonical-root mismatch even if ID matches) |
| Full directory copy (`cp -R repo repo-copy`) | copied verbatim | Layer 2 fails closed: canonical root of `repo-copy` does not match the bound root of `repo` |
| Fork (GitHub/Git, shared history) | fork's own future identity, independent of upstream | none inherited; fork lineage ≠ PCAE repository identity |
| `git worktree add` | **distinct** — each worktree independently initialized/enrolled (§61 decision below) | distinct; enrolled separately if needed |
| Backup restore to the *same* expected canonical deployment root | preserved | may remain valid if Layer 2's canonical-root check still matches (§64) |
| Backup restore to a *different* path | preserved (ID) | requires admin re-bind, same as path move |
| Explicit re-identify (future governed operation, not implemented) | **new** ID generated, old binding invalidated | must be re-enrolled from scratch |

No cell is left ambiguous, per the governing prompt's requirement.

## 12. Git Clone / Tracked-Metadata Question (verified, not assumed)

The prompt explicitly required verifying, not assuming, whether `.pcae`
identity metadata would actually be carried by a normal `git clone` in
this repository's conventions. Checked this phase:

```
git check-ignore -v .pcae/agent-lock.json .pcae/phase-completion-metadata.json .pcae/repository-intelligence/latest.json
```

`.pcae/` is **not** globally gitignored in this repository — several
`.pcae/**` artifacts (e.g. phase-completion metadata, this phase's own
architecture doc's supporting files) are tracked and committed as part
of the governed phase-completion lifecycle. This means a hypothetical
future `.pcae/repository-identity.json` **could** end up tracked and
therefore cloned/forked automatically unless the architecture
explicitly prevents it. **This is exactly the failure mode this
architecture must not create.** Conclusion (binding on any future
implementation phase, not decided as code this phase): a repository-
instance identity file **must not be committed to Git**; it must be
repository-local, untracked, filesystem-only state (consistent with
how `.pcae/agent-lock.json` and other instance-local state are already
handled, per 149O.1B.1 §3's reading of `acquire_agent_lock()`) —
otherwise §14's silent-propagation risk becomes automatic on every
clone and fork, defeating property 9 in §5 outright. Any future
implementation phase must add this file to VCS-ignore rules as part of
its own scope; this phase does not modify any ignore file.

## 13. Git Worktree Decision

`git worktree add` shares the object database but has a distinct
working path and distinct working state. **Decision: distinct
repository-instance identity per worktree.** Rationale: HATP authority
must be deployment-root-scoped (§9 Layer 2), and a worktree is, for
Layer 2's purposes, a distinct canonical root exactly like a full copy
— the same-host copy-isolation argument (§8) applies identically to a
worktree pointed at a different path. Using a single shared lineage
identity across worktrees would reopen a copy-shaped hole between
worktrees of the same clone. Each worktree independently initializes
(and, if HATP-authorized, independently enrolls) its own identity.
Operational cost (separate enrollment per worktree) is accepted as the
safer default; this is a deliberate simplicity-over-convenience choice
per §90's requirement to select exactly one model, not two ID fields.

## 14. Single-ID vs. Dual-ID (lineage + instance) Model

Compared per governing prompt §62: a `lineage_id` + `instance_id`
dual-field model was considered and rejected as unnecessary complexity
for v1 — HATP's actual authority need (§9) is instance-scoped only; no
requirement in this phase's scope calls for lineage-level tracking
across clones. **Selected: single repository-instance
`repository_id`** (§6/§9), consistent with the governing prompt's
stated strong preference and with the minimum-necessary principle
already applied to the Root 2B two-vs-three-principal decision in
149O.1B.1.

## 15. Attack Matrix

| Attack | Expected future result |
|---|---|
| Copy `repository_id` value alone into an unauthorized repo | No authority: Layer 2 binding keys on canonical deployment root, which does not match |
| Copy entire repository (including identity metadata) to an unauthorized path | No authority: canonical-root mismatch (§9, §11 full-directory-copy row) |
| `git clone` an authorized repository | No authority: per §12, identity metadata is untracked/local-only by architectural requirement, so a normal clone does not even carry the ID; even in the tracked-metadata counterfactual, canonical-root mismatch still blocks authority |
| Copy a valid HATP proof into another repository | Invalid: proof binds `repository_id` (§20/§21 below); cross-repository replay fails at signature/binding verification, independent of Layer 1 |
| Set an untrusted repo's `repository_id` to a known-authorized ID | No authority gained: Layer 2 still requires the untrusted repo's canonical root to match the bound root for that ID; it does not |
| Change (mutate) `repository_id` in place | Fails closed: existing Layer 2 binding no longer matches; HATP becomes unavailable for that repository until re-enrolled — not a fallback, not silently permissive |
| Delete `repository_id` | Fails closed: HATP unavailable, same as above |
| Change protected deployment root binding | Not agent-executable (Class-B, admin-owned, agent-unwritable, per 149O.1B.1 Root 2B) — mandatory; agent cannot rebind itself (§37/§38 of governing prompt) |
| Symlink/alias path substitution | Canonical-root comparison must resolve symlinks and normalize `..`/case per platform (§19 below) before any Layer 2 match; a raw unresolved alias must not pass |

Every attack in the governing prompt's mandatory list (§77–§89) is
covered and fails closed under Model A's two-layer design.

## 16. Repository ID Mutation, Deletion, Theft — Fail-Closed Statement

Because authority lives entirely in the protected Layer 2 binding
(§9), the repository-local `repository_id` value itself does **not**
need write protection for HATP *security* purposes: an agent that
mutates, deletes, or overwrites it with a stolen ID gains nothing,
because Layer 2's canonical-root check still fails (§15). This is a
useful simplification (governing prompt §54/§55/§97) — repository-ID
*generation* is not itself a sensitive operation and needs no human
approval (§96), while an eventual governed *reidentify* operation
(§17, not implemented) remains operationally sensitive because it
invalidates existing enrollment and must be explicit, not silent.
PCAE-lifecycle *consistency* (not HATP security) may still prefer the
value be treated as effectively immutable once set, to avoid confusing
non-HATP consumers (§51); this is a UX/consistency preference for a
future implementation phase, not a security requirement of this
architecture.

## 17. Identity Creation, Reinitialization, Reidentity, Migration

- **Creation event:** general PCAE initialization/adoption (`pcae
  init`-equivalent lifecycle event), not an HATP-specific event —
  keeps Layer 1 HATP-independent per §9/§51. Not implemented this
  phase.
- **Reinitialization (`pcae init` when an identity already exists):**
  must be **idempotent-preserve**, never silently regenerate — a silent
  regeneration would invalidate every existing Layer 2 binding for that
  repository without any operator signal.
- **Existing-repository migration:** repositories that predate this
  architecture have no identity. First identity-aware initialization
  generates one — but generation **must not** itself grant HATP
  authority (§16); Layer 2 enrollment remains a separate, explicit,
  bootstrap-admin action. No historical-approval-shaped data may be
  retroactively treated as authorizing evidence for the newly minted ID
  (governing prompt §103/§104/§105/§106 — no GitHub-remote-ownership
  shortcut, no path-based auto-enrollment, no clone auto-enrollment).
- **Explicit re-identify (future, ungoverned by this phase):**
  conceptually a governed operation (`pcae repository reidentify` or
  equivalent) for a legitimately-copied repository that should become
  independently authorized. Deliberately sensitive (§16) — not
  implemented, not named as a frozen command surface this phase.

## 18. Canonical Root Comparison Requirements

Layer 2's canonical-root binding (§9) must compare a **resolved**
filesystem root: absolute path, symlinks resolved, `..` components
removed, platform-appropriate case normalization. An unresolved,
caller-supplied, or symlinked alias path must not be accepted as
matching the bound canonical root. OS inode/device identity and
filesystem UUIDs were considered (governing prompt §40/§41) as
possible *additional* root-binding strengtheners and rejected as the
*sole* mechanism — neither is portable, both change across restore/
copy on some filesystems, and overfitting to them would make the
architecture platform-fragile without closing any attack §15 doesn't
already close via path comparison. Left as an implementation-detail
option for a future phase to evaluate, not decided here.

## 19. HATP Trust-Store / Signed-Proof Relationship

Future HATP proofs should bind `repository_id` (Layer 1) as one signed
field. Per §84 of the governing prompt, raw local filesystem paths
should **not** be embedded in a portable signed proof (portability/
privacy); instead, the *verifier* performs the protected Layer-2
canonical-root lookup locally, out of band from the proof itself.
Recommended future verification flow (conceptual, not implemented):

```
load local repository_id
  -> resolve current canonical root (§18)
  -> read protected HATP registry (Layer 2, admin-owned)
  -> find enrollment matching repository_id AND canonical root
  -> verify signer authority against that enrollment
  -> verify HATP proof binds repository_id
```

Cross-repository replay (§87/§88) fails at either the `repository_id`
binding check or the canonical-root match, independently — two
independent failure points, not one.

## 20. Contract Ownership Decision

**Decision: CRI architecture is sufficient as a HATP dependency; no
separate Canonical Repository Identity contract is required before
HATP-001 freeze.** Justification: every normative statement this
architecture needs (§10's three mandatory statements, the two-layer
separation of §9, the fail-closed rules of §15/§16) is scoped entirely
to how HATP consumes a repository-instance identifier — it does not
establish general cross-subsystem identity semantics that other
non-HATP contracts already depend on today. Per governing-prompt §100
("avoid premature contract explosion"), a same-document HATP-embedded
definition is the minimum sufficient normative home; broadening into an
independent generic PCAE identity contract is deferred until a second
consumer (audit records, artifact lineage — noted as future value in
§51 of the governing prompt, not committed to this phase) actually
needs one.

## 21. HATP Freeze Readiness — Explicit Answer

**Can HATP-001 now normatively express repository-specific authority
without silently transferring authority across clones/copies?**

**YES.** The two-layer model (§9) makes repository-instance possession
(Layer 1) insufficient for authority by construction; authority exists
only at the protected, admin-owned, agent-unwritable Layer-2 binding,
which independently verifies canonical deployment root. Every mandatory
attack in §15 fails closed. No cell in the §11 scenario matrix is
ambiguous. No path-only, remote-URL-only, or bare-UUID-only identity is
proposed as sufficient by itself — all three were explicitly
considered and rejected as insufficient alone (§4/§6).

## 22. Findings

**Non-Blocking / Resolved this phase:**

- Repository-instance identity now has one concrete, evidence-checked
  selected model (Model A, §9) rather than an open question.
- The copy/clone authority-transfer hole (§8) is closed at the
  architecture level by the two-layer design — not by making the
  identifier itself secret or unforgeable, which would have been the
  wrong fix (§48/§82).
- `git worktree` semantics are resolved (§13): distinct identity per
  worktree.
- Tracked-vs-untracked `.pcae` metadata convention was independently
  checked, not assumed (§12) — repository-instance identity metadata
  must be untracked/local-only, a concrete constraint on the eventual
  implementation phase.

**Observation (carried forward, not newly blocking):**

- HATP bootstrap environment remains NOT READY (same OS user for
  human and agent) — unchanged from 149O.1B.1; still deployment work,
  still out of architecture scope.
- An eventual `pcae repository reidentify`-equivalent governed
  operation is named conceptually (§17) but not specified or
  implemented; a future phase must define its governance (approval
  requirements, audit trail) before implementation.

**Deferred:**

- Exact `.pcae` storage filename/schema fields for the identity record
  (§66/§67 of the governing prompt) are noted as likely candidates
  (`.pcae/repository-identity.json`; `schema_version`,
  `repository_id`, `created_at`) but intentionally not frozen this
  phase — implementation-planning-phase decision.
- Exact protected Layer-2 registry schema (§81 of the governing
  prompt) is sketched conceptually in §9 but not frozen — HATP
  contract-freeze-phase decision.

No finding in this phase is Blocking for HATP-001 freeze.

## 23. Governance Validation (rerun, this phase)

```
pcae health                -> healthy, git status clean
pcae check                 -> passed
pcae status coherence      -> coherent
pcae doctor task-memory    -> clean
pcae push check             -> clean, nothing_to_push
pcae runtime inspect        -> Observed / observe / unavailable (unchanged)
pcae notify status          -> telegram configured/enabled
pcae phase-report reconcile --phase-id 149O.1B.1 -> reconciled, mutation none
```

## 24. Production / Contract / OS Boundary

```
git status --short                                      -> only this phase's
                                                             own docs/**,
                                                             tasks/**,
                                                             PROJECT_STATUS.md,
                                                             CHANGELOG.md,
                                                             .pcae/phase-
                                                             completion-*
                                                             changed
git diff --name-only <start>..HEAD -- src/pcae/          -> (empty)
git diff --name-only <start>..HEAD -- docs/contracts/    -> (empty)
```

No repository-identity implementation was created. No `.pcae`
initialization behavior was changed. No OS user was created. No ACL,
sudoers, or filesystem-ownership configuration was changed. No HATP
trust store was created. No AG3/AG5 wiring occurred. No Permission
Broker change was made. No RAE-001 change was made.

## 25. Runtime Boundary

`pcae runtime inspect` before and during this phase: Observed / observe
/ unavailable — unchanged.

## 26. Chapter 149 Status

Outstanding, sharpened this phase:

- HATP Root 2B establishment (distinct OS principal — deployment work,
  still not performed)
- HATP contract freeze (no longer blocked on repository identity;
  ready to resume)
- HATP contract independent verification
- HATP implementation planning
- HATP implementation
- HATP independent verification
- Canonical repository-identity implementation (this phase's own
  recommended future implementation work, not yet scheduled)
- RAE HATP integration
- RAE re-verification
- AG3/AG5 integration planning
- AG3/AG5 integration
- integration verification
- TK1/TK2/TK3 re-affirmation

## 27. Confirmations (governing-prompt required final-report list)

- No production repository-identity implementation was created.
- No HATP implementation was created. HATP-001 remains unfrozen during
  this architecture phase.
- B-149O-1 through B-149O-4 remain OPEN.
- No OS account or security configuration was changed.
- No AG3 Permission Broker integration was implemented.
- No AG5 Permission Broker integration was implemented.
- No rollback execution behavior changed.
- RAE-001 v1.0 remains unchanged. RWMPC-001 v1.0 remains unchanged.
  PBPC-001 v1.2 remains unchanged. PBPA-001 v1.0 remains unchanged.
  CHGR-001 remains unchanged.
- IWC confirmation remains distinct from approval. AESIC/AEM remain
  disclosure-only.
- No POL-001..012 meaning was changed. No POL-013+ was added.
- TK1/TK2/TK3 remain deferred.
- No Runtime Enforcement behavior changed. No Prompt Generation, Prompt
  Dispatch, or agent invocation capability was implemented. Runtime
  remains Observed, maximum capability remains observe, and execution
  availability remains unavailable (confirmed via `pcae runtime
  inspect` before and during this phase).

## 28. Recommended Next Phase

Per §21's YES answer and §20's contract-ownership decision:

**149O.1B.3 — Human Approval Trusted Provenance Contract Freeze**,
resuming HATP-001 freeze with Root 1 resolved, Root 2A resolved, Root
2B resolved, and repository identity now resolved (this phase).
