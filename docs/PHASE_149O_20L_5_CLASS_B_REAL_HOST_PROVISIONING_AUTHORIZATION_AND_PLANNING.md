# Phase 149O.20L.5 — Class-B Real Host Provisioning Authorization & Planning

## 0. Phase Identity and Type

**Phase:** 149O.20L.5
**Type:** PLANNING / AUTHORIZATION-BOUNDARY ONLY. No `src/pcae/**` change. No
`scripts/**` change. No contract (HMIC-001/HMRC-001/HBDC-001/HATP-001) change.
No real OS-principal creation, no Protected Root creation, no `chmod`/`chown`/
ACL mutation, no Python-environment lockdown, no Cutover Record, no
certification, no `HATP_MANDATORY` activation, no runtime-capability change.
This document, its companion test file, and ordinary task/lifecycle/report
bookkeeping are the only artifacts this phase produces.
**Basis:** `docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_IMPLEMENTATION_PLAN.md`
§32 (Real Authorization Boundaries) and §33 (Stop Conditions CBV-S1..S12),
read directly and re-derived in this phase, not assumed from any later
phase's summary of them; `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(HBDC-001 v1.0, all 55 requirements re-read directly); the live production
verifier source (`src/pcae/core/hatp_class_b_topology_verifier.py`,
`hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py`,
`hatp_mandatory_cutover.py`); `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`
(the cited GPC6-REQ-075(b) precedent, read directly); `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
(CHGR-001, the repository's own canonical human-decision-artifact
architecture); a real, unmocked, read-only invocation of
`verify_class_b_deployment_conformance()` and
`assess_hatp_mandatory_activation_readiness()` performed by this phase
against this actual development host; and direct, read-only inspection of
this host's OS/filesystem/Python-environment state.

## 1. Entering State (Independently Reconfirmed, Not Assumed From L.4)

- Repo clean, `origin/main..HEAD` = 0, `pcae health`/`pcae check`/`pcae status
  coherence` all healthy/passed/coherent, `pcae push check` clean
  (`nothing_to_push`), `pcae doctor task-memory` warnings (pre-existing,
  historical `tasks/active/`/`tasks/DONE.md` bookkeeping drift, unrelated to
  this phase, not remediated here — outside this phase's allowed-file scope),
  `pcae runtime inspect` Observed / observe / unavailable, `pcae notify
  status` Telegram configured/enabled, `pcae phase-report reconcile
  --phase-id 149O.20L.4` → reconciled, mutation none (inspection only, no
  redispatch).
- CBV-S1 (positive Class-B verifier authority source outside HMIC identity):
  independently reconfirmed **CLOSED** as of 149O.20K.3's HMIC v1.3 28-file
  identity alignment (independently re-verified 149O.20K.1/149O.20J.8 lineage)
  and its integration confirmed by 149O.20L.4. Not reopened by this phase.
- CBV-S10 (no contract-defined readiness integration point exists):
  independently reconfirmed **CLOSED** by 149O.20L (HMRC-001 v1.1 eighth
  readiness term) and 149O.20L.3/149O.20L.4 (production integration +
  independent verification). Not reopened by this phase.
- Class-B: **NOT PROVISIONED**. Real host: `verify_class_b_deployment_conformance()`
  independently re-invoked live by this phase, unmocked — returns
  `NON_COMPLIANT` (full reason inventory, §4 below). HATP: **NOT READY**
  (`assess_hatp_mandatory_activation_readiness()` independently re-invoked
  live — `ready=False`, all eight terms inspected, §4 below). Runtime:
  Observed / observe / unavailable, reconfirmed by `pcae runtime inspect`.
- `git status --short` confirmed clean immediately after every real-host
  read-only call made by this phase — no provisioning side effect.

## 2. Section 32/33 Reconstruction (Independently Re-Derived)

Read directly from `docs/PHASE_149O_20H_...IMPLEMENTATION_PLAN.md` §32–§33
(not from any intervening phase's paraphrase of them):

**§32, Real Authorization Boundaries (verbatim scope), explicitly forbids —
for this phase and for any future phase this plan itself would authorize —
without a separately, explicitly authorized governed phase:** real Class-B
provisioning; real OS principal/user/group creation; real Protected Root
creation/chown/chmod/ACL mutation; real Python-environment change; real HMIC
certification/binding/revocation state creation; real `HATP_MANDATORY`
activation; real Cutover Record/activation-marker creation; PB behavior
change; POL-005 change; COMP-002 implementation; runtime-state change. This
list is the direct textual source for §42 of this document's mandatory
non-authorizations table.

**§33, Stop Conditions:** of CBV-S1..S12, exactly two — CBV-S1 and CBV-S10 —
were ever found genuinely triggered by the chosen Class-B architecture (both
independently reconfirmed closed above, §1). The other ten (S2–S9, S11, S12)
were not-triggered/mitigated by construction at planning time and remain so:
this phase's own read-only inspection (§4) found no new evidence reopening
any of them (in particular CBV-S2/S3/S4/S6/S11, which concern the *verifier's
own* effective-access/ancestor/hard-link/Git-trust/platform logic — not the
unprovisioned host state, which is the *expected* NON_COMPLIANT signal those
checks are designed to produce).

**What this phase independently derives (not assumed from §32's own framing
alone):**
- *Actions explicitly requiring a later governed authorization:* every item
  in §32's list above, none of which this phase or its own plan may perform
  or pre-authorize.
- *Actions forbidden before that authorization:* identical set — §32 draws
  no distinction between "forbidden until authorized" and "forbidden
  outright"; nothing in HBDC-001, HMIC-001, or HMRC-001 grants any phase the
  power to self-authorize real provisioning by producing a plan document,
  however complete (HBDC-REQ-050/051, independently re-read, §5 of
  HBDC-001).
- *Human decision required:* an explicit, dated, first-person election by
  the human governance authority — not a phase-report recommendation, not
  conversational approval buried in an unrelated instruction, not inferred
  from progression through prior phases (§8–§11 below, mirroring
  GPC6-REQ-075(b) precedent).
- *Evidence required before authorization can be requested:* the complete
  mutation inventory (§6), current NON_COMPLIANT reason inventory (§4), host
  eligibility determination (§7), rollback/idempotency/ordering plan (§9–§11),
  and privilege classification (§12) this document itself supplies — i.e.,
  authorization is requested *with* a reviewed plan attached, not in the
  abstract.

## 3. Authority Wall (Preserved Throughout This Phase)

`confirmed ≠ authorized ≠ permitted ≠ capable ≠ executed`. `COMPLIANT ≠
authorized`. `ready ≠ activated`. `planning ≠ authorization`. `authorization ≠
execution`. No finding closure from 149O.20K/149O.20L/149O.20L.1–.4
(HMIC v1.3, HMRC-001 v1.1, CBV-S1/S10 closure) confers any authority to
mutate the real host. This phase's own act of writing this plan likewise
confers none (§20, §21 below make this explicit and structural, not just
asserted in prose).

## 4. Real Host — Independently Re-Invoked, Read-Only, This Phase's Own Evidence

`verify_class_b_deployment_conformance()` invoked live (no mock, no fixture,
`git status --short` clean before and immediately after):

```
STATUS: NON_COMPLIANT
```

23 unmet requirement IDs, each independently captured with its own machine
reason code and safe evidence (paths/uids/mode octals, never secret
material): `HBDC-REQ-001, 002, 007, 013, 014, 015, 016, 017, 018, 019, 020,
022, 025, 026, 027, 029, 030, 031, 035, 036, 038, 039, 042`. The remaining
32 of 55 requirements are either satisfied by construction on any host
(`HBDC-REQ-004, 005, 008, 011, 012, 021, 028, 032, 033, 034, 037` — all pure
verifier-design/negative-assertion checks that do not depend on real
provisioning) or are MANUAL/contract-governance rows with no runtime check
(HBDC-001 §2's classification, independently re-cross-checked against the
live 23-item NON_COMPLIANT reason list — no MANUAL-classed requirement
appears among the 23 mutation-relevant failures, confirming the failures are
genuinely provisioning-shaped, not process-discipline gaps).

`assess_hatp_mandatory_activation_readiness()` invoked live: `ready=False`,
all eight terms inspected — `class_b_protected_storage_available`,
`repository_deployment_identity_valid`, `hatp_substrate_operational`,
`mandatory_consumption_implementation_independently_verified`, and
`class_b_deployment_conformance_satisfies_readiness` unsatisfied;
`hsce_signing_implementation_available` and
`production_dependency_provenance_valid` satisfied (module-importability and
trust-store-resolution facts that hold on any correctly-checked-out
repository, independent of provisioning); `protected_activation_authority_
mechanism_available` unsatisfied (Protected Root absent). Confirms §21 of the
149O.20H plan: `COMPLIANT` alone would still leave three other terms
(`repository_deployment_identity_valid`, `hatp_substrate_operational`,
`mandatory_consumption_implementation_independently_verified`) independently
gated by CRI/HMIC-certification state this phase's plan does not touch.

## 5. HBDC Requirement → Mutation Mapping (§4/§6 of the Governing Prompt)

Every one of the 23 live-failing requirements, traced to a category, a real
host action, and a classification:

| Requirement | Live reason (this phase's own call) | Category | Real action required | Classification |
|---|---|---|---|---|
| HBDC-REQ-001/002 | `protected_root_absent_not_provisioned` / `protected_root_absent` | OS principal | Create a second, distinct OS principal (admin) | Mutation-required |
| HBDC-REQ-007/013/014/015/016/017/018/019/020 | `protected_root_absent(_or_unsafe)` (×9) | Protected Root | Create Protected Root, admin-owned, mode ≤0750, ACL/group/ancestor-chain closed | Mutation-required (depends on admin principal existing) |
| HBDC-REQ-025 | `interpreter_or_venv_not_admin_provisioned` | Python env | Provision an admin-owned production interpreter/venv | Mutation-required |
| HBDC-REQ-026 | `no_venv_detected_not_provisioned` | Python env | Create admin-owned production venv | Mutation-required |
| HBDC-REQ-027 | `agent_is_owner_with_write_bit` (interpreter: `/opt/homebrew/...python3.14`, uid=501, mode 0o755) | Python env | Lock interpreter path to admin ownership/agent-unwritable | Mutation-required (conflicts with Homebrew dev workflow, §8) |
| HBDC-REQ-029 | `agent_is_owner_with_write_bit` (`~/Library/Python/3.14/lib/python/site-packages`, uid=501) | Python env | Disable user-site or prove agent-unwritable | Mutation-required (conflicts with `pip install --user`) |
| HBDC-REQ-030 | `customization_module_agent_writable` (Homebrew Cellar `sitecustomize.py`, uid=501) | Python env | Admin-lock or remove | Mutation-required |
| HBDC-REQ-031 | `unsafe_pth_file_present` (`_editable_impl_pcae_harness.pth`, uid=501, points at **this** repo's `src/`) | Python env | Admin-lock the editable-install `.pth` | Mutation-required — **this is the live pointer ordinary `pip install -e .` development depends on**, §8 |
| HBDC-REQ-036 | `agent_is_owner_with_write_bit` (`pcae` launcher script resolves inside the agent-owned venv) | Launcher | Downstream of venv lock (HBDC-REQ-025/026); no independent mutation | Mutation-required (bundled with venv lock) |
| HBDC-REQ-038 | `git_executable_not_trustworthy_resolvable` | Launch environment | `/opt/homebrew/bin` (agent-writable, admin-group) precedes `/usr/bin/git` (root-owned) on live `PATH`; admin-controlled launch `PATH` must not place an agent-writable directory before the trusted `git` | Mutation-required, but **PATH/launch-config only** — no chmod/chown of `git` itself, which is already root-owned and correctly resolved today |
| HBDC-REQ-039 | `venv_lock_not_established_dependency_boundary_unproven` | Python env | Satisfied jointly by HBDC-REQ-025..027 venv lock (verifier design, §2 of 149O.20H plan) — no separate action | Mutation-required (bundled) |
| HBDC-REQ-022/035 | `pcae_distribution_metadata_not_found` | Packaging/metadata | `importlib.metadata.distribution("pcae")` cannot resolve a distribution for this checkout | **Observation-only** — a packaging/build-metadata condition, not fixable by chown/chmod/user-creation; §6 below |
| HBDC-REQ-042 | `no_repository_identity_present` (`.pcae/repository-identity.json` absent) | Deployment identity (CRI Layer 1) | Run the existing, separate, agent-writable-by-design repository-identity bootstrap flow (HATP-001 §17) | **Observation-only relative to Class-B provisioning** — this is ordinary CRI bootstrap state, not an OS-principal/Protected-Root/environment-lock mutation, and is not gated behind Boundary P at all; §6 below |

**Coverage check:** 23/23 live-failing requirement IDs mapped above; every
mutation-classed row cites its governing `HBDC-REQ-###`; no mutation is
proposed without a normative requirement backing it (§4 of the governing
prompt — no over-provisioning).

## 6. Mutation-Required vs. Observation-Only (§6 of the Governing Prompt)

- **Mutation-required (genuine host provisioning):** HBDC-REQ-001/002 (OS
  principal), HBDC-REQ-007/013–021 (Protected Root), HBDC-REQ-025/026/027/029/
  030/031/036/039 (Python environment lock), HBDC-REQ-038 (trusted launch
  `PATH`). Nine distinct real actions after de-duplicating bundled checks
  (§9 below).
- **Observation-only / not fixable by provisioning alone:**
  - HBDC-REQ-022/035 (`pcae_distribution_metadata_not_found`): this is a
    packaging/build condition — `importlib.metadata` cannot resolve a `pcae`
    distribution for the current editable checkout on this interpreter.
    Chowning or admin-locking the `.pth` file (HBDC-REQ-031's action) does
    not by itself fix this; it may require a corrected editable-install
    invocation or `pyproject.toml` metadata investigation, which is outside
    this phase's planning-only scope to diagnose further and is **not**
    included in the provisioning command plan (§9) as a chmod/chown step —
    flagged here as a residual limitation (§34) instead.
  - HBDC-REQ-042 (`no_repository_identity_present`): CRI Layer 1
    (`repository_instance_id`) is explicitly agent-writable-by-design
    (HATP-001 §17, HBDC-REQ-042 itself: "confers no authority alone"). Its
    absence here reflects that this repository has never run the ordinary,
    separate repository-identity bootstrap step — not a Class-B topology
    defect. It is not part of the provisioning mutation set.

No mutation is planned for either of these two conditions; both are
explicitly excluded from §9's command plan.

## 7. Host Eligibility for HBDC Model A (§7/§25 of the Governing Prompt)

Direct, read-only inspection performed by this phase:

- **OS/filesystem:** macOS 26.6.1 (Darwin 25.6.0), APFS root filesystem.
  `_default_production_trust_root()` already commits to macOS
  (`/Library/Application Support/PCAE/HATP/trust-store`) and Linux — this
  host's platform is supported by the frozen resolver (149O.20H §27); the
  gap is provisioning state, not platform support.
- **Principal topology:** `id` reports a single account, `uid=501
  (atilamadai)`, member of `staff`, `admin`, and numerous macOS system
  groups. **No second OS principal exists on this host at all** — there is
  no "agent" account distinct from an "admin" account; the same account that
  would run PCAE *is* the account that owns every candidate admin-controlled
  resource (Homebrew install, developer venv, user site-packages).
  `dscl . -list /Users` / `/Groups` show no `pcae`-designated principal or
  group of any kind.
- **Filesystem ownership of every candidate environment-lock resource:**
  repo (`.` → `atilamadai:staff 755`), `.venv` (`atilamadai:staff`),
  `/opt/homebrew` (`atilamadai:admin 755`), Homebrew site-packages
  (`atilamadai:admin`), the editable `.pth` pointer (agent-writable, points
  at *this* checkout's `src/`) — **all owned by the single developer
  account**, none by a distinct admin principal.
- **Git/PATH:** the live `PATH` places `/opt/homebrew/bin`
  (`atilamadai:admin`, agent-writable) ahead of `/usr/bin` (where the
  actually-resolved, root-owned `git` lives) — an ordinary Homebrew-first
  `PATH`, not evidence of compromise, but exactly the shape HBDC-REQ-038
  is designed to flag.

**Determination:** this development host, in its current, everyday
configuration, is **not currently eligible** for HBDC-001 Model-A Class-B
provisioning **without** first introducing a genuinely distinct admin OS
principal and a genuinely distinct, admin-owned Python execution environment
— it does not fail on platform/filesystem/ACL-model grounds (macOS/APFS is
supported), it fails on **principal-topology** grounds (§8 below explains
why fixing this on the developer's own daily-driver account is
architecturally undesirable, not merely inconvenient).

## 8. Development-Host vs. Deployment-Host (§7, §24–§26 of the Governing Prompt)

Every mutation-required action in §6 targets a resource this developer
actively depends on for ordinary, unrelated work on this machine: the
Homebrew-managed Python interpreter (`brew upgrade python@3.14` would
conflict with an admin-lockdown of its owning directory), the repo-local/
user-site Python package install paths (`pip install --user`,
`pip install -e .` — the very `.pth` file HBDC-REQ-031 flags **is** this
repository's own editable-install pointer), and the account's own admin-
group membership (already used for routine macOS system administration
unrelated to PCAE).

HBDC-REQ-026 is explicit that a developer-writable repo-local `.venv` "is
non-compliant for production Class-B deployment **regardless of the source
tree's own certification status**" — i.e., the contract itself anticipates
and rejects exactly this host shape as a production target. Locking down
this account's Homebrew install, user-site, and editable `.pth` pointer to
satisfy Class-B would either (a) break this developer's ability to do
ordinary Python development on this machine, or (b) require running a
second, parallel, admin-owned Python installation alongside the existing
one — itself a nontrivial provisioning undertaking with its own collision
and workflow risk (§22 below).

**Recommendation (not a decision — a recommendation for the human
authorization decision in §13–§15 to weigh):** HBDC-001 Model A does not
require the *developer's* interactive workstation to become the Class-B
host; it requires *some* host where the canonical repository working tree
is checked out under editable install with a genuinely separate admin
principal. A dedicated deployment host or VM — not this everyday development
machine — is the architecturally cleaner target, and this phase recommends
it be the default assumption for any future provisioning phase, subject to
the human authorizer's explicit override if they instead prefer a
parallel-environment approach on this same host.

## 9. Provisioning Command Plan (Future Phase Only — Not Executed Here)

Nine bundled real actions, each recorded as: purpose / privilege /
precondition / postcondition / verification / rollback. **No command below
is run by this phase.** Dependency ordering follows §11.

1. **Create admin OS principal.** *Purpose:* HBDC-REQ-001/002/004/005 —
   establish a second, distinct OS account. *Privilege:* root/sudo
   (`sysadminctl -addUser` on macOS / `useradd` on Linux). *Precondition:*
   preflight confirms no existing account/UID collision with the intended
   name/UID (§17 below). *Postcondition:* a new `uid` distinct from the
   agent's, group membership limited to what HBDC-001 requires (no
   unnecessary `admin`/`sudo` grant beyond what Protected-Root/venv
   ownership needs). *Verification:* `dscl . -read /Users/<name> UniqueID`
   (or `id <name>`) resolves the new distinct uid; live re-run of
   `verify_class_b_topology_conformance()`'s principal-distinctness check.
   *Rollback:* `sysadminctl -deleteUser` / `userdel`, only if no
   dependent resource (Protected Root, venv) has yet been created.
2. **Create Protected Root.** *Purpose:* HBDC-REQ-011–014. *Privilege:*
   sudo, executed *as* the new admin principal or by an operator acting on
   its behalf. *Precondition:* step 1 complete; target path
   (`/Library/Application Support/PCAE/HATP/trust-store` on macOS)
   confirmed absent (preflight). *Postcondition:* directory exists, owned
   by admin uid, mode `0750`. *Verification:* live
   `verify_class_b_topology_conformance()` re-run;
   HBDC-REQ-011/012/013/014 rows flip to `satisfied=True`. *Rollback:*
   `rm -rf` the created directory (safe — nothing else in the filesystem
   references it yet at this stage).
3. **Configure Protected Root ACL/group/ancestor chain.** *Purpose:*
   HBDC-REQ-015–020. *Privilege:* sudo. *Precondition:* step 2 complete.
   *Postcondition:* no agent group/ACL grants write; every ancestor up to
   the first non-agent-writable directory is confirmed non-writable (§10
   of the 149O.20H plan's ancestor-walk design). *Verification:* live
   effective-access/ancestor-chain checks (`_effective_write_access`,
   `_ancestor_chain_safe`, both already implemented and directly
   re-invocable read-only). *Rollback:* revert any ACL/group entries added
   in this step only (does not require deleting the root itself).
4. **Provision admin-owned production venv/interpreter.** *Purpose:*
   HBDC-REQ-025–027, 036, 039. *Privilege:* sudo (creation + chown) then
   admin-uid ownership going forward. *Precondition:* step 1 complete;
   target production path distinct from this repo's own `.venv` and from
   the developer's Homebrew install (§8 — do not reuse either). *Postcondition:*
   interpreter/venv/site-packages/launcher script all owned by admin uid,
   mode excludes agent write. *Verification:* live
   `verify_environment_lock_conformance()` HBDC-REQ-025/026/027/036 rows.
   *Rollback:* `rm -rf` the newly created venv tree (safe, isolated from
   the developer's own `.venv`/Homebrew install by construction of step 4's
   own precondition).
5. **Lock `sitecustomize`/`usercustomize`/`.pth` inside the new venv.**
   *Purpose:* HBDC-REQ-030/031/035. *Privilege:* sudo/admin-uid.
   *Precondition:* step 4 complete; the editable-install pointer is created
   fresh *inside the new admin-owned venv*, distinct from this repo's
   existing developer-owned `.pth` (§8 — the developer's own `.pth` is left
   untouched by this plan). *Postcondition:* all such files, if present,
   admin-owned/agent-unwritable. *Verification:* live
   `verify_environment_lock_conformance()` corresponding rows.
   *Rollback:* remove the files (contained within the step-4 venv tree,
   removable together).
6. **Lock down `PYTHONPATH`/user-site for the production launch
   environment.** *Purpose:* HBDC-REQ-028/029/037 (028/037 already pass
   generically; 029 needs an explicit disable for the *production* launch
   context). *Privilege:* admin-controlled launch configuration (no root
   required if scoped to a launch wrapper, not the developer's own shell
   profile). *Precondition:* step 4 complete. *Postcondition:*
   `PYTHONNOUSERSITE=1` (or equivalent) set in the production launch
   configuration only — the developer's own interactive shell/user-site is
   never touched. *Verification:* live HBDC-REQ-029 row. *Rollback:*
   remove the launch-configuration entry.
7. **Configure trusted-`git` launch `PATH`.** *Purpose:* HBDC-REQ-038.
   *Privilege:* admin-controlled launch configuration only — no chmod/chown
   of `git` itself (already root-owned, §5). *Precondition:* step 4/6's
   launch-configuration mechanism exists. *Postcondition:* the production
   launch `PATH` never places an agent-writable directory ahead of the
   resolved `git`. *Verification:* live
   `_resolve_trusted_executable_with_effective_access("git")` (already
   implemented, directly re-invocable). *Rollback:* revert the launch `PATH`
   entry.
8. **(Excluded from this plan)** HBDC-REQ-022/035 packaging-metadata
   condition and HBDC-REQ-042 repository-identity bootstrap — §6 — no
   command is planned for either; both require separate diagnosis/workflow
   outside Class-B host provisioning.
9. **Final full-verifier confirmation.** *Purpose:* close the loop.
   *Privilege:* none (read-only). *Precondition:* steps 1–7 complete.
   *Postcondition:* none (read-only). *Verification:* fresh
   `verify_class_b_deployment_conformance()` — target `COMPLIANT` (§18
   below). *Rollback:* n/a (no mutation).

No step above includes `activate_hatp_mandatory`, any
`hatp_mandatory_certification.py` write path, or any Cutover Record
mutation — confirmed by inspection of the actual call graph (§19–§21).

## 10. Pre-Provisioning Backup/Snapshot Requirements

For every mutable resource identified in §9, a future provisioning phase
must capture, before any mutation:

- **Admin principal (step 1):** whether the target account name/uid/gid
  already exists (it must not); no prior state to snapshot beyond
  non-existence confirmation.
- **Protected Root (step 2):** confirmed absent beforehand (no prior state
  to restore beyond deletion on rollback).
- **Production venv/interpreter/launcher/`.pth`/customization files (steps
  4–5):** created fresh at a new path distinct from the developer's
  existing `.venv`/Homebrew install (§8) — again, confirmed-absent
  precondition, not an in-place mutation of existing state, so "restore
  prior state" reduces to "delete what step 4/5 created."
- **`PYTHONPATH`/user-site/launch-`PATH` configuration (steps 6–7):**
  because these target a *new, admin-controlled launch configuration file*
  rather than the developer's interactive shell profile, the pre-mutation
  snapshot is simply "this launch-configuration file did not exist / did
  not contain this entry."

**Key structural property of this plan:** because §8's recommendation
(new venv, new interpreter path, new launch configuration, new admin
principal — never the developer's own existing `.venv`/Homebrew/user-site)
is followed, every mutation in §9 targets *newly created* resources rather
than *modifying* resources the developer's ordinary workflow depends on.
This eliminates the highest-risk class of "restore exact prior state"
problem (mutating a live, in-use resource) by construction, at the cost of
requiring a dedicated environment rather than reusing the developer's own.
If a future authorizer instead elects to reuse the developer's existing
`.venv`/Homebrew install (rejecting §8's recommendation), that authorization
must separately require full ownership/mode/ACL/hash snapshots of every
touched file before mutation — this plan does not design that riskier path
in detail, consistent with recommending against it.

## 11. Dependency Ordering

```
[preflight: full read-only inventory + collision detection]  (§17)
        |
        v
1. create admin OS principal
        |
        +---------------------+
        v                      v
2. create Protected Root      4. provision admin-owned venv/interpreter
        |                      |
        v                      +----------+----------+
3. Protected Root ACL/         v          v           v
   group/ancestor chain    5. lock       6. lock      7. configure
        |                  .pth/site    PYTHONPATH/   trusted-git
        |                  customize    user-site     launch PATH
        |                      |          |            |
        +----------------------+----------+------------+
                                |
                                v
                    9. final full-verifier re-check
```

No circular dependency: step 1 (principal) is the sole root prerequisite for
both branches (Protected Root, environment lock); the environment-lock
sub-steps (5/6/7) depend only on step 4, not on each other in a cycle; step
9 depends on all prior steps and mutates nothing.

## 12. Partial-Failure Semantics

**Fail-closed, immediate local rollback of the failed step, retain
already-verified earlier steps.** Rationale: because §11's ordering makes
each step's postcondition independently re-verifiable (every step lists its
own "Verification" in §9), a failure at step N does not require unwinding
steps 1..N-1 if those steps' own postconditions still independently hold —
each already-completed step is re-checked, not merely assumed, before
deciding whether to proceed, retry step N, or abort. If step N's own
rollback (as specified in §9) cannot cleanly succeed (e.g., a partially
created venv that resists `rm -rf` due to an unexpected permission state),
the future execution phase MUST stop and escalate to a separate governed
recovery path rather than attempting further automated mutation — mirroring
this repository's existing fail-closed idiom (`hatp_mandatory_cutover.py`'s
own `except Exception: ... = False` pattern, never silent retry-with-force).

## 13. Idempotency

Every step in §9 is designed as **inspect → compare → mutate only if needed
→ verify**, reusing the exact same read-only checks
(`verify_class_b_topology_conformance()`, `verify_environment_lock_conformance()`,
`verify_class_b_deployment_conformance()`) both to decide whether a step is
already satisfied and to confirm it after mutation — the identical function
this phase itself called read-only in §4. A future execution phase re-run
against an already-provisioned host should find every step's precondition
already met and perform zero mutation on the second run.

## 14. Preflight (Read-Only, No Mutation)

A future provisioning phase's preflight stage must perform, before any step
in §9: the exact full inventory this phase already performed in §4/§7 —
`verify_class_b_deployment_conformance()`, `assess_hatp_mandatory_activation_readiness()`,
principal/group enumeration (`dscl`/`id` or platform equivalent),
target-path existence checks for Protected Root and the new venv location,
`PATH`/launch-environment inspection, and the host-eligibility determination
of §7. Detected conflicts (existing account/group name collision, an
already-present but non-conformant Protected Root, an unsupported platform)
MUST abort before any mutation — no step in §9 may proceed on an
unresolved preflight finding.

## 15. Per-Step Postcondition Verification

Already specified per-step in §9's "Verification" column — each step
verifies its own narrow postcondition via a direct re-invocation of the
relevant existing, already-implemented verifier check (never waiting for
the final aggregate call in step 9 to discover an earlier step's silent
failure), satisfying the governing prompt's §17 requirement directly.

## 16. Final Provisioning Verification and Post-Provisioning Readiness

Step 9 (§9) requires a fresh, live `verify_class_b_deployment_conformance()`
call; target `COMPLIANT` (exact-identity comparison against
`ClassBConformanceStatus.COMPLIANT`, per the frozen positive rule, HBDC-001
§20/149O.20H plan §6 — never truthiness, never partial credit). **Even a
`COMPLIANT` result at this point does not authorize activation (§20/§21
below).** If `COMPLIANT` is reached, a future phase (not this one, and not
automatically chained from provisioning) SHOULD run
`assess_hatp_mandatory_activation_readiness()` read-only to determine which
of the *other* seven readiness terms — `repository_deployment_identity_valid`,
`hatp_substrate_operational`, `mandatory_consumption_implementation_
independently_verified` in particular, per §4's live evidence — still
block full HATP readiness. Class-B `COMPLIANT` is necessary but, per HBDC-REQ-055
and this phase's own §4 live evidence, not remotely sufficient for full
readiness.

## 17. OS Principal Risk Analysis

- **Collision:** preflight (§14) MUST enumerate existing accounts/UIDs/GIDs
  before selecting a name/identifier for the new admin principal — this
  host's `dscl . -list /Users`/`/Groups` currently shows no
  `pcae`-designated principal, so no collision exists *today*, but a future
  execution phase must re-check at execution time, not trust this
  planning-time snapshot.
- **UID/GID reuse:** macOS/`dscl`-based account creation should let the OS
  assign a fresh UID rather than hand-picking one, avoiding accidental reuse
  of a deleted former account's UID (a real macOS footgun — a reused UID can
  inherit a stale account's file ownership).
- **Supplementary-group side effects:** the new admin principal should be
  granted *only* the group memberships HBDC-001 actually requires (Protected
  Root's read-traversal group, §11 of 149O.20H's design) — not blanket
  `admin`/`sudo`, which would exceed HBDC-REQ-009/010's "admin write
  authority ≠ runtime execution authority" discipline and needlessly widen
  blast radius.
- **Login/shell behavior:** the new principal is an admin-role account, not
  an interactive daily-driver account — a future phase should disable
  interactive login shell/password login where the platform allows, since
  its only purpose is to own protected resources, not to be logged into
  routinely.
- **Developer workflow impact:** because §8/§9's design creates a *new*
  principal and a *new* venv rather than repurposing the developer's own
  account or `.venv`, ordinary development on this host is structurally
  unaffected by principal creation itself.
- **`sudo` interaction:** creating the account requires `sudo`/root once;
  ongoing HBDC-001 operation does not require the developer's own account
  to gain new `sudo` rights.

## 18. Protected Root Risk Analysis

- **Proposed path:** `/Library/Application Support/PCAE/HATP/trust-store`
  (macOS, per `_default_production_trust_root()` — no override path exists,
  HBDC-REQ-011, independently confirmed absent from any CLI/env-var/config
  surface by this phase's own reading of the resolver).
- **Current existence:** confirmed absent on this host by this phase's own
  live verifier call (§4, `HBDC-REQ-001` reason `protected_root_absent_not_
  provisioned`) — nothing to overwrite.
- **Existing contents / owner / mode / ACL:** n/a (absent).
- **Ancestor trust requirements:** `/Library/Application Support` on this
  host is `root:admin`, mode `755` (spot-checked via `stat` on `/Library`
  during §7's inspection) — a plausible non-agent-writable ancestor already,
  but the future execution phase's own ancestor-chain walk (HBDC-REQ-017,
  already implemented) must re-derive this live at execution time, not
  trust this planning-time observation.
- **Effect on normal development:** none — this path is outside any
  directory the developer's ordinary tooling reads or writes.
- **Not created by this phase.**

## 19. Repository Ownership / Permission Risk

HBDC-001 does not require changing ownership or permissions on the
*developer's checked-out repository itself* — `resolve_canonical_
deployment_root`/`deployment_binding_matches` (HBDC-REQ-042–046) operate on
the repository's *identity*, not its filesystem permissions, and Model A
explicitly runs PCAE from the canonical repository working tree via editable
install (HBDC-REQ-022). §9's plan changes *only* the production
interpreter/venv/launch environment used to *execute* PCAE authority code —
it does not chown/chmod the repository directory, Git operations, editor
access, or CI/local test tooling. This directly avoids the "renders normal
development unusable" failure mode the governing prompt's §24 warns against,
by design (§8's dedicated-environment recommendation is precisely what
achieves this).

## 20. No Automatic Cutover / No Automatic Certification (Frozen, Structural)

Independently confirmed by direct inspection of the actual call graph (not
merely asserted): `hatp_mandatory_cutover.py`'s `_write_cutover_transition`
and `activate_hatp_mandatory` functions, and `scripts/hatp_certification_
admin.py`'s `certify`/`activate`/`revoke` entry points, are **not called
anywhere in §9's command plan**, and none of the three Class-B verifier
modules (`hatp_class_b_topology_verifier.py`, `hatp_environment_lock_
verifier.py`, `hatp_class_b_conformance.py`) imports or calls any of them
(149O.20H plan §19, independently re-confirmed unmodified by this phase's
own read of the live source in §2 of this document). Step 9 of §9 (final
verification) is explicitly read-only. **Provisioning completion → STOP.**
No future provisioning phase this plan itself would authorize may call
`activate_hatp_mandatory` or write a real Cutover Record; that requires a
separately, explicitly authorized future **activation** phase (Boundary A,
§21).

## 21. Boundary P vs. Boundary A (Mandatory Separation)

- **Boundary P — Provisioning authorization.** Authorization to perform
  §9's real-host mutations (OS principal creation, Protected Root creation,
  Python-environment-lock provisioning, trusted-launch-`PATH`
  configuration) to bring this host's Class-B topology from NON_COMPLIANT
  toward COMPLIANT. This phase (149O.20L.5) concerns **only** Boundary P —
  it defines what Boundary P authorization would need to say, but does not
  itself grant it.
- **Boundary A — Activation authorization.** Authorization to perform real
  `HATP_MANDATORY` activation (`activate_hatp_mandatory`, real Cutover
  Record creation) — required only after provisioning (Boundary P),
  independent verification of that provisioning, HMIC certification
  issuance (a further boundary, §22 below), and every other readiness term
  in §4/§16 are separately satisfied and separately authorized.
- **These are never combined.** A human authorizing Boundary P authorizes
  *only* the mutations in §9 — nothing in that authorization extends to
  activation. §29's exact authorization-proposition wording (below) makes
  this textually explicit, not merely implied, mirroring the governing
  prompt's own worked example ("...without activating HATP").

## 22. Provisioning vs. Certification (Also Separate)

Provisioning (§9) changes host *state* (creates a principal, a Protected
Root, a locked environment). HMIC certification (`scripts/hatp_certification_
admin.py`'s `certify`/`activate` commands, independently inspected by this
phase — `certify` creates a `CertificationRecord`, `activate` explicitly
*binds* an existing one, both operator-invoked, both requiring `--assume-yes`
or an interactive confirmation prompt by design) *evaluates and binds
evidence about* that state. Nothing in §9's plan calls `certify` or
`activate`. Whether certification requires its own governed phase/boundary:
**yes** — this phase determines, from the existing separation already
visible in the certification-admin script's own command structure (`create`
→ separate `activate`, itself distinct from Class-B `verify`), that HMIC
certification is a **third**, independent boundary (call it Boundary C, not
requested by name in the governing prompt but structurally required by
this analysis) beyond Boundary P and Boundary A — provisioning authorization
does not, and must not, be read as pre-authorizing it.

## 23. Human Authorization Precedent (GPC6-REQ-075(b))

`docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`, read directly by this
phase (not from any summary), establishes the repository's own working
precedent for what an "explicit human authorization" record looks like:
first-person ("I, Atila Madai, act in the human-authority capacity..."),
explicitly disclaiming AI/automated origin, citing the specific evidence
considered, naming a bounded "Election" with an explicit enumerated
non-extension list ("does not itself begin Stage 3...does not authorize
implementation..."), a separately-addressed open-question resolution
(GAC-001 §9 applicability), a "Mandatory Boundaries" section restating
runtime/lifecycle non-change, and a signed "Human Decision Record" with
named decision-maker, date, rationale, explicit conditions/limitations, and
an explicit confirmation sentence ("I confirm this is my human governance
decision under GPC6-REQ-075(b)").

**What this establishes for L.5's own model:**
- Simple conversational approval embedded in an unrelated instruction is
  **not** sufficient — the precedent is a dedicated, standalone, signed
  document.
- A canonical governance artifact **is** required — and this repository has
  since built exactly that mechanism generically (CHGR-001, §24 below),
  superseding the need to hand-author a bespoke markdown file the way
  GPC6-REQ-075(b) did.
- Authorization must name exact mutation classes (mirrors the precedent's
  explicit non-extension list) — §29's proposition follows this directly.
- Scope/target/time must be bound (mirrors the precedent's explicit
  evidence-citation and dated signature) — §32/§35 below.
- Authorization is revocable — CHGR-001 explicitly provides `revoked`/
  `superseded` states (§24 below); GPC6-REQ-075(b) itself does not exercise
  revocation but does not preclude it.

## 24. Authorization Artifact — Reuse CHGR-001, Do Not Invent a New Mechanism

`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (CHGR-001,
currently v1.3) already defines the repository's canonical mechanism for
exactly this class of artifact: a durable, canonical representation of a
bounded act of human governance authority, with a decision-template/
interactive-confirmation workflow (`pcae decision-session create/evidence/
select/clarify/preview/confirm/readiness`, independently confirmed present
in the live CLI by this phase), publication into a CHGR
(`pcae governance-record publish`), and read-only inspection/verification
(`pcae governance-record inspect/verify`) — all independently confirmed
present and callable in the live CLI by this phase, not assumed from the
contract text alone. CHGR-001 already specifies (independently spot-read by
this phase, §1053/§1129/§1282/§1298/§1371 and neighboring provisions):
supersession/suspension/revocation semantics (CHGR-REQ-114/155/159/178),
prevention of stale/expired-record reuse (CHGR-REQ-159), and a digest/
`integrity_ref`/`provenance_ref` binding model (§9, CHGR-REQ-075–082,
CHGR-REQ-197/210–212) suitable for binding a specific reviewed plan/commit.

**Determination:** PCAE does **not** need a new, competing authorization
artifact for Class-B provisioning. A future Boundary-P authorization SHOULD
be captured as a CHGR via the existing `pcae decision-session` →
`pcae governance-record publish` workflow, using this document (149O.20L.5's
own planning artifact) as the cited evidence/plan-digest basis, exactly as
GLP-PILOT-C6's Stage 3 election cited its own phase history. This phase does
not invoke `decision-session`/`governance-record publish` itself (that would
itself be, or immediately precede, the human authorization act this phase is
forbidden from performing on the human's behalf, §26/§40) — it only
determines and records that the mechanism exists and should be reused.

## 25. Plan Immutability

A future Boundary-P authorization (§21, §29) must bind the *specific*
reviewed provisioning plan — concretely, this document's own content
(identified by its file path and the Git commit at which it was authorized)
and, per CHGR-001's own digest-binding model (§24), a `record_digest`/
`provenance_ref` over that exact plan text. If the provisioning plan changes
materially after authorization (e.g., a different target host, a different
principal-naming scheme, an added mutation category), the prior
authorization SHALL NOT be read as covering the revised plan — a renewed
authorization (a new CHGR, or an explicit supersession per CHGR-REQ-114) is
required, mirroring CHGR-001's own supersession discipline rather than
silently reusing a stale approval.

## 26. Host Identity Binding

The strongest non-invasive host-identity facts this phase can honestly cite,
without claiming solved cryptographic runtime attestation (HMIC-REQ-063
remains OPTION C, not solved — HBDC-REQ-040/041 independently re-confirmed
unmodified by this phase): OS/platform identity (`uname`/`sw_vers`, §7), the
canonical repository working-tree path this authorization would apply to
(`resolve_canonical_deployment_root`'s output for this checkout), and — once
provisioned — the CRI Layer 2 `DeploymentBinding` record HBDC-REQ-042–046
already require independently of this plan. This phase does **not** claim
any stronger runtime host-attestation than what `hatp_bootstrap`/
`repository_identity` already produce; a future authorization proposition
should cite exactly these facts, no more, and should state explicitly (as
this document does) that host identity here is filesystem/OS-observable
identity, not cryptographic attestation of what actually executes.

## 27. Source Identity Binding

A future provisioning phase must bind to: the current Git commit at
authorization time (`implementation_commit`, via the existing, already
HBDC-REQ-038-governed trusted-`git` resolution), the HMIC-001 contract
version and `implementation_scope_digest` in force at that commit (v1.3, 28
files / 5 contracts, independently reconfirmed current by 149O.20L.4), and
HBDC-001's own version (v1.0, unmodified by this phase, §2 of this
document). If any of these three changes materially between authorization
and execution (a new commit lands, HMIC is amended, HBDC-001 is amended),
the authorization SHOULD be treated as stale per §25/§28 rather than
silently carried forward.

## 28. Authorization Freshness / Revocation

Per §23/§24's precedent and mechanism review, and per the governing prompt's
own preference for narrow scope: this phase recommends Boundary-P
authorization be **one-shot and plan/commit-bound** (§25/§27), not
open-ended or "valid until revoked" — narrower authority is preferable
absent an affirmative reason to grant standing authority, matching this
repository's existing GPC6-REQ-075(b) precedent's own narrow, single-election
framing. CHGR-001's `revoked`/`superseded` states (§24) provide the
mechanism to withdraw or supersede it if circumstances change before
execution.

## 29. The Exact Authorization Proposition (Draft, for a Future Human Decision)

The following is the precise proposition a human governance authority would
later elect on — drafted here per the governing prompt's explicit
instruction, not itself an authorization (§40):

> *Authorize a separately governed future phase to provision [a
> to-be-identified dedicated host, per §8's recommendation against reusing
> this development workstation] to HBDC-001 v1.0 Model-A Class-B
> requirements, executing exactly the nine bundled actions of
> `docs/PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_AUTHORIZATION_AND_
> PLANNING.md` §9 (OS admin-principal creation; Protected Root creation and
> ACL/group/ancestor-chain configuration; admin-owned production venv/
> interpreter provisioning; `sitecustomize`/`.pth` lockdown; user-site
> disablement for the production launch context; trusted-`git` launch-`PATH`
> configuration; final read-only verification), bound to the Git commit and
> HMIC-001/HBDC-001 contract versions in force at the time of this
> authorization (§27), subject to the rollback plan of that document's §9/
> §10/§12, fail-closed on any step or preflight failure (§12/§14), without
> authorizing HMIC certification (§22), without authorizing real
> `HATP_MANDATORY` activation (§20/§21, Boundary A), and excluding any change
> to Permission Broker behavior, POL-005, or COMP-002.*

## 30. Authorization Artifact Requirements (Restated)

Per §24, expressed as the fields a CHGR capturing this proposition would
need: subject (Boundary-P provisioning of a named target host under
HBDC-001 v1.0), the exact mutation-scope list (§9's nine actions, no more),
purpose (§29), explicit non-authorizations (§38), rollback commitment (§9/
§10/§12), plan digest/`provenance_ref` (§25), host identity fields (§26),
source/contract-version binding (§27), decision-maker identity, date, and
explicit confirmation sentence (mirroring GPC6-REQ-075(b)'s own closing
line), and freshness/revocability disposition (§28).

## 31. Host / Source / Contract Binding — Summary

Already stated individually in §26/§27; restated together because the
governing prompt's required-report list names them separately: a future
Boundary-P authorization binds **(a)** host identity (§26, OS/platform +
canonical-deployment-root, non-cryptographic), **(b)** source identity
(§27, exact commit + HMIC/HBDC contract versions), and **(c)** this specific
reviewed plan document (§25, digest/`provenance_ref`) — all three together,
not any one alone.

## 32. Risks

- **Highest-impact risk:** provisioning on the *wrong* host (this
  development workstation) would degrade or block the developer's own
  ordinary Python/Homebrew workflow — mitigated structurally by §8's
  dedicated-environment/dedicated-host recommendation, not merely flagged.
- **OS-principal collision/misconfiguration risk:** mitigated by §14/§17's
  mandatory preflight detection, never assumed-safe naming.
- **Partial-failure risk:** a provisioning run that creates an admin
  principal but fails before completing environment lock leaves a
  half-provisioned host — mitigated by §12's fail-closed/re-verify-before-
  proceeding discipline and by every resource being newly created (§10),
  so cleanup is deletion, not un-mutation of live state.
- **ACL-model risk (macOS):** 149O.20J/149O.20J.5/149O.20J.7/149O.20J.8's
  own history (native macOS ACL semantics required several narrow verifier
  repairs) means a future execution phase should re-confirm the *current*
  verifier's ACL check behavior against the *actual* target host's ACL
  configuration in preflight, not assume this planning phase's own
  observations on this development host transfer unchanged to a different
  target host.
- **Packaging-metadata risk (HBDC-REQ-022/035):** unresolved by this plan
  (§6) — if the future provisioning phase's target host exhibits the same
  `pcae_distribution_metadata_not_found` condition, `COMPLIANT` may remain
  unreachable even after every other mutation succeeds, until that
  packaging condition is separately diagnosed. Flagged as a residual
  limitation (§34), not silently assumed away.

## 33. Residual Limitations (Honestly Disclosed)

- HMIC-REQ-063 remains OPTION C (environment-lock mitigation), not solved
  cryptographic executed-source attestation — HBDC-REQ-040/041 unchanged by
  this phase, and no future provisioning phase this plan authorizes may
  represent Class-B `COMPLIANT` as such attestation.
- HBDC-REQ-009 (admin exclusively holds write authority) remains, per the
  149O.20H plan's own §9 disposition, satisfied-by-construction from
  HBDC-REQ-001+013 rather than independently agent-provable — this phase
  does not revisit that design decision.
- macOS native ACL inspection (§10 of the 149O.20H plan) is honestly scoped
  to "reports `ACCESS_ERROR`/`INDETERMINATE` where no reliable native
  mechanism exists" — a future provisioning phase's `COMPLIANT` result is
  only as strong as that residual scoping.
- The `pcae_distribution_metadata_not_found` condition (§6) is unresolved
  by this plan and may block reaching `COMPLIANT` on any host until
  separately diagnosed.
- This phase's host-eligibility determination (§7) is based on inspecting
  *this* development host; it does not inspect any actual future deployment
  target, which does not yet exist.

## 34. CBV-S1 / CBV-S10 Regression Status

Independently re-checked by this phase (§1): **neither is reopened.**
CBV-S1 remains closed at the HMIC v1.3 28-file identity boundary; CBV-S10
remains closed at the HMRC-001 v1.1 eight-term readiness-integration
boundary. This phase's own read-only host calls (§4) produced the expected
NON_COMPLIANT/not-ready signal on an unprovisioned host — this is the
*correct* behavior of already-closed, already-verified checks, not evidence
of regression.

## 35. Class-B / HATP / Runtime State (Phase Exit)

```
CBV-S1:   CLOSED (unchanged)
CBV-S10:  CLOSED (unchanged)
Class-B:  NOT PROVISIONED — PROVISIONING PLAN / AUTHORIZATION BOUNDARY DEFINED
HATP:     NOT READY
Runtime:  Observed / observe / unavailable
```

## 36. Real-Host-Unchanged Confirmation

`git status --short` confirmed clean immediately after every real-host
read-only call this phase made (§4, §7); no OS user/group was created; no
Protected Root, venv, ACL, or launch-configuration file was created or
modified; `verify_class_b_deployment_conformance()`'s own result carries no
mutation side effect by design (149O.20H plan §18/§19, independently
re-confirmed unmodified source in §2 of this document).

## 37. Tests

`tests/test_phase_149o_20l_5_class_b_real_host_provisioning_authorization_and_planning.py`
(new, planning/contract-only, no production host mutation test) verifies:
every one of this phase's own live-captured 23 NON_COMPLIANT reason codes
is mapped in this document's §5 table; every mutation-classed row in §5/§6
cites a real `HBDC-REQ-###` ID; every mutation action in §9 has a
corresponding rollback description; §9 contains no `activate_hatp_mandatory`/
certification-write reference anywhere in its text; §29's authorization-
proposition text explicitly excludes activation and certification; §21's
Boundary P/Boundary A separation is textually present and distinct;
`git status --short` is clean at test time (repo-hygiene smoke check, not a
host-mutation test).

## 38. Explicit Non-Authorizations (This Phase and Any Future Boundary-P
Authorization Drafted From §29)

Real Class-B provisioning; real OS principal/user/group creation; real
Protected Root creation/chown/chmod/ACL mutation; real Python-environment
change; real HMIC certification/binding/revocation state creation
(Boundary C, §22); real `HATP_MANDATORY` activation (Boundary A, §20/§21);
real Cutover Record/activation-marker creation; Permission Broker behavior
change; POL-005 change; COMP-002 implementation; runtime-state change;
unrelated system hardening; arbitrary package updates; unrelated repository
changes.

## 39. Next Executable Phase

Per §24/§29–§30: the plan produced by this phase is complete enough to be
*attached to* a future Boundary-P authorization request, but that
authorization is itself a human governance act (§40) this phase cannot
perform or pre-schedule. The correct next **executable** governed phase is
therefore not "149O.20L.6 — Class-B Real Host Provisioning Execution"
directly (that would require Boundary-P authorization to already exist,
which it does not yet), but rather:

**Recommended: Phase 149O.20L.6 — Class-B Provisioning Authorization Record
Capture.** A dedicated, narrowly-scoped phase whose *only* substantive
output is running the existing `pcae decision-session` →
`pcae governance-record publish` workflow (§24) to let the human governance
authority actually elect on (or decline, or amend) §29's proposition,
producing a published CHGR — mirroring exactly how GPC6-REQ-075(b) required
its own dedicated record rather than being inferred from adjacent phase
progress. Only if and after that CHGR is published with an affirmative
election should a subsequent phase (149O.20L.7 or later, renumbered as
appropriate at that time) attempt real provisioning execution against
§9's plan, itself re-verified fresh (not assumed unchanged) at that later
phase's own entry.

## 40. This Prompt Is Not Human Authorization (Explicit Acknowledgement)

The user's instruction to run 149O.20L.5's planning work is authorization to
perform **planning only**. It is not authorization to mutate the real host,
and this phase draws no such inference from: approval of this phase's
existence, prior phase progression (149O.20L–149O.20L.4), or CBV-S1/CBV-S10
closure. Actual provisioning requires the later explicit decision this
phase's own §29/§39 describe but do not perform.

## 41. Plan Verdict

```
CLASS-B REAL HOST PROVISIONING AUTHORIZATION & PLANNING:
COMPLETE
— 23/23 LIVE NON_COMPLIANT REASONS MAPPED TO A DISPOSITION (MUTATION OR OBSERVATION-ONLY)
— HOST ELIGIBILITY DETERMINED: THIS DEVELOPMENT HOST NOT RECOMMENDED AS TARGET
— BOUNDARY P / BOUNDARY A / BOUNDARY C EXPLICITLY SEPARATED
— EXACT AUTHORIZATION PROPOSITION DRAFTED (§29)
— CANONICAL AUTHORIZATION ARTIFACT MECHANISM IDENTIFIED (CHGR-001, REUSED NOT INVENTED)
— NO REAL PROVISIONING AUTHORIZED
— NO REAL ACTIVATION AUTHORIZED
— REAL HOST STATE UNCHANGED
```

## 42. Recommended Next Phase

**Phase 149O.20L.6 — Class-B Provisioning Authorization Record Capture**
(§39). Must not itself provision, activate, or certify anything; its sole
substantive output is a published CHGR (or an explicit decline/amendment)
recording the human governance authority's election on this phase's §29
proposition.
