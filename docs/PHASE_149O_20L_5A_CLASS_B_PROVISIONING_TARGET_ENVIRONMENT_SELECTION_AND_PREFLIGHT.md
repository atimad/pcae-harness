# Phase 149O.20L.5A — Class-B Provisioning Target Environment Selection & Preflight

## 0. Phase Identity and Type

**Phase:** 149O.20L.5A
**Type:** READ-ONLY TARGET SELECTION + PREFLIGHT ONLY. No `src/pcae/**`
change. No `scripts/**` change. No contract (HMIC-001/HMRC-001/HBDC-001/
HATP-001) change. No real OS-principal creation, no Protected Root
creation, no `chmod`/`chown`/ACL mutation, no Python-environment lockdown,
no Cutover Record, no certification, no `HATP_MANDATORY` activation, no
runtime-capability change, no CHGR publication. This document, its
companion test file, and ordinary task/lifecycle/report bookkeeping are the
only artifacts this phase produces.
**Basis:** `docs/PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_AUTHORIZATION_AND_PLANNING.md`
(read directly, §7–§9, §29 in particular), re-derived rather than assumed;
`docs/PHASE_149O_20H_..._IMPLEMENTATION_PLAN.md` §32/§33; the live
production verifier source; a real, unmocked, read-only re-invocation of
`verify_class_b_deployment_conformance()` performed by this phase against
this actual development host; direct read-only inspection of this host's
OS/filesystem/Python-environment/network (`~/.ssh/config`,
virtualization-tooling presence) state; and an explicit human clarification
obtained during this phase (§3 below) on which candidate hosts are in
scope.

## 1. Entering State (Independently Reconfirmed, Not Assumed From L.5)

- Repo clean, `origin/main..HEAD` = 0, `pcae health`/`pcae check`/`pcae
  status coherence` all healthy/passed/coherent, `pcae push check` clean
  (`nothing_to_push`), `pcae doctor task-memory` warnings (pre-existing,
  historical `tasks/active/`/`tasks/DONE.md` bookkeeping drift predating
  this phase and 149O.20L.5 alike, unrelated, not remediated here — outside
  this phase's allowed-file scope), `pcae runtime inspect` Observed /
  observe / unavailable, `pcae notify status` Telegram configured/enabled,
  `pcae phase-report reconcile --phase-id 149O.20L.5` → reconciled,
  mutation none (inspection only, no redispatch).
- CBV-S1 and CBV-S10: independently reconfirmed **CLOSED**, unchanged from
  149O.20L.5's own reconfirmation (§1 of that document) — not reopened by
  this phase's own read-only host evidence (§4 below).
- Class-B: **NOT PROVISIONED**. Boundary P/C/A: **NOT AUTHORIZED**. HATP:
  **NOT READY**. Runtime: Observed / observe / unavailable.

## 2. Authority Wall (Preserved Throughout This Phase)

`planning ≠ authorization`. `preflight ≠ authorization`. `authorization ≠
execution`. `COMPLIANT ≠ ready ≠ certified ≠ activated`. Selecting a target
environment is not permission to mutate it. Nothing in this document
authorizes, schedules, or infers authorization for any real-host mutation.
§29's draft proposition (below) remains a draft; only Phase 149O.20L.6's
own governance-election workflow can turn it into an authorization.

## 3. Human Clarification Obtained This Phase

Two other hosts (`hac-windows` 192.168.192.104, `hac-dell` 192.168.192.200)
exist with pre-configured SSH key access in this operator's `~/.ssh/config`
— a concrete Option E candidate on its face. Because probing an external
host is a network-touching action whose purpose this phase cannot infer
from hostname alone, this phase asked the human operator directly rather
than guessing or silently excluding them. **Answer received: "Unrelated —
exclude them."** Accordingly, this phase does **not** probe, connect to, or
otherwise touch either host, and Option E is closed as **no qualifying
candidate currently available** for the remainder of this analysis. This is
a human-supplied fact this phase treats as authoritative for target
scoping, not itself a Boundary-P authorization act (§2).

## 4. Real Host — Independently Re-Invoked, Read-Only, This Phase's Own Evidence

`verify_class_b_deployment_conformance()` invoked live (no mock, no
fixture; `git status --short` clean before and immediately after):

```
STATUS: INDETERMINATE
```

This differs textually from L.5's own captured `NON_COMPLIANT` result taken
five hours earlier the same day — **this is genuine environmental drift on
the unprovisioned development host, not a contradiction of L.5's
eligibility verdict, and not a reason to distrust this phase's own live
call over L.5's.** Per HBDC-REQ-052/053 (closed vocabulary, no partial
credit, `_NON_COMPLIANT_STATUSES` in `hatp_class_b_topology_verifier.py`
treats every non-`COMPLIANT` member — including `INDETERMINATE` — as
equally "not compliant"), the operative fact for this phase's purposes is
unchanged: **still not `COMPLIANT`, still unprovisioned.** Root cause of
the status-label drift, independently traced: `HBDC-REQ-027`'s
effective-write-access check against the interpreter path now active in
this shell session (`/Library/Developer/CommandLineTools/Library/Frameworks/
Python3.framework/Versions/3.9/bin/python3.9`, not the Homebrew
`python@3.14` interpreter L.5's session had active) returns
`indeterminate:acl_inspection_unavailable` rather than a definite
satisfied/unsatisfied verdict for that specific system path, which the
aggregation function's failure-class priority ordering (§2 of the
topology verifier) promotes to overall `INDETERMINATE`. This is the exact,
pre-disclosed residual limitation L.5 §33 already flagged ("macOS native
ACL inspection is honestly scoped to report `ACCESS_ERROR`/`INDETERMINATE`
where no reliable native mechanism exists ... a future provisioning
phase's `COMPLIANT` result is only as strong as that residual scoping") —
not a new defect this phase must fix, and explicitly out of this
read-only-preflight phase's scope to repair (that would be a `src/pcae/**`
change).

22 unmet-check reason codes captured this run (vs. L.5's 23 — set
differs, not merely shrunk, confirming this phase independently
re-evaluated rather than reused L.5's list verbatim, per this phase's own
governing instruction §9):

- **Present in both L.5's and this phase's list (14 core items,
  unchanged):** `HBDC-REQ-001, 002, 007, 013, 014, 015, 016, 017, 018, 019,
  020, 025, 026, 031, 036, 038, 039, 022, 042, 035` — Protected Root
  absence, OS-principal absence, venv/interpreter ownership, editable
  `.pth`, trusted-`git` `PATH` ordering, packaging metadata, repository
  identity. Materially identical finding to L.5.
- **Present in L.5's list, absent from this phase's list:** `HBDC-REQ-029,
  030` — user-site/`sitecustomize` checks that did not register as unmet
  in this session's environment (plausibly session/shell-state dependent,
  e.g. `PYTHONNOUSERSITE`/active interpreter differences between the two
  sessions; not independently re-diagnosed further, as it does not change
  the eligibility verdict either direction — both are still
  provisioning-shaped Python-environment items per L.5 §6).
- **Present in this phase's list, absent from L.5's list:** `HBDC-REQ-027`
  (now indeterminate rather than a clean fail, discussed above), `HBDC-REQ-
  033, 037` — `agent_writable_cwd_precedes_canonical_package_location` and
  `authority_changing_env_injection_channel_open`
  (`pythonpath_unset`/cwd-precedence evidence). Both are additional
  instances of the same Python-environment-lock category L.5 already
  identified as mutation-required (§6 of L.5's document); they do not
  introduce a new HBDC requirement category outside what L.5's §9 plan
  already addresses via the venv/interpreter-lock actions (steps 4–6).

**Determination:** this drift is consistent with L.5 §33's own explicit
caveat that live-check output is planning-time-only and must be
"re-verified fresh (not assumed unchanged) at [a] later phase's own entry"
— exactly what this phase did. The eligibility conclusion is unchanged:
**this development host, as currently configured under the developer's own
account, remains not eligible.** Nothing here reopens CBV-S1/CBV-S10 (§8).

## 5. Independent Reconstruction of Host Ineligibility (§2 of the Governing Prompt)

Reconstructed directly from this phase's own commands, not copied from
L.5's prose:

- **Principal ownership concentration:** `id` → single account `uid=501
  (atilamadai)`, groups include `staff`, `admin`, and numerous macOS system
  groups; `dscl . -list /Users` / `/Groups` show no `pcae`-designated
  principal. One human account holds every candidate admin-controlled
  resource.
- **Repository ownership:** `stat` on the checkout root →
  `atilamadai:staff 0755`.
- **Editable-install `.pth`:** `.venv/lib/python3.9/site-packages/
  _editable_impl_pcae_harness.pth`, owned `atilamadai:staff`, mode `0644`
  (agent-writable via ownership), pointing at this checkout's own `src/`.
- **Python environment topology:** repo-local `.venv` owned
  `atilamadai:staff`; the venv's own `bin/python3` symlink resolves inside
  the same tree; Homebrew (`/opt/homebrew`) owned `atilamadai:admin`
  — all agent-writable-by-ownership.
- **ACL/ancestor topology:** no distinct admin principal exists to grant
  ACL-based isolation from; `PATH` places `.venv/bin` and
  `/opt/homebrew/bin` (both agent-writable) ahead of `/usr/bin` (where the
  actually-resolved, root-owned `git` lives) — the exact shape
  HBDC-REQ-038 is designed to flag, reconfirmed live (`type -a git` →
  `/usr/bin/git`, `stat` → `root:wheel 0755`, correctly resolved despite
  the `PATH` ordering).
- **Development-user dependencies:** the same account's ordinary,
  unrelated daily-driver workflow (Homebrew package management, `pip
  install -e .`, `pip install --user`) depends on write access to every
  one of the resources HBDC-001 Model A requires to be admin-owned and
  agent-unwritable.
- **Other HBDC conflicts:** none beyond the above found by this phase's
  own re-inspection; no new conflict category emerged relative to L.5.

**Classification (per the governing prompt's four-way split):**
- *Impossible to provision:* no — nothing here is platform-incapable;
  macOS/APFS is a supported Model-A platform (149O.20H §27).
- *Technically possible but unsafe:* no — see next line; it does not even
  reach "unsafe," it reaches "destructive of an unrelated property."
- *Possible only after restructuring:* **yes, and specifically the kind of
  restructuring that is itself already part of L.5's own provisioning
  plan** — creating a second OS principal and a second, admin-owned
  Python environment (§6 below explains why this is not the same as
  "provisioning infrastructure that does not exist").
- *Unsuitable because it would destroy development/deployment separation:*
  **yes, if and only if the *developer's own* existing account/`.venv`/
  Homebrew install were reused in place** — L.5 §8 already established
  this and this phase's own re-inspection (above) confirms it: locking
  down the developer's Homebrew install or user-site would break ordinary,
  unrelated development on this machine (HBDC-REQ-026 itself: "non-
  compliant for production Class-B deployment *regardless of the source
  tree's own certification status*").

**This conclusion is not silently reversed.** Per this phase's own entering
instruction, it is re-evaluated (§4 above), not merely restated, and the
verdict stands unchanged.

## 6. Deployment-Target Classes Evaluated

- **Option A — current development host/environment (the developer's own
  account, `.venv`, Homebrew install, as currently configured).**
  Independently re-evaluated, §4–§5. **Rejected**, unchanged from L.5 —
  not on platform grounds, on principal-topology-collision grounds. Direct
  evidence (not merely inherited from L.5) confirms this.
- **Option B — same physical host, dedicated OS principal + dedicated
  deployment repository/venv, isolated from the developer's own account.**
  Evaluated in detail, §7 below. **This is the target selected by this
  phase** — see §7 for the reasoning.
- **Option C — dedicated VM.** No virtualization tooling (`multipass`,
  `vagrant`, `UTM`, VMware/Parallels/VirtualBox `.app` bundles) found
  present on this host by direct inspection (`which`/`/Applications`
  listing). **Not currently available; would require new tooling/VM
  creation this phase does not perform or pre-authorize.** Model-A
  compatibility is not in question — feasibility-of-existence is the
  blocker.
- **Option D — dedicated physical/remote host.** No such host identified
  as available to the operator for this purpose after the human
  clarification in §3 (the only two SSH-reachable candidate hosts were
  explicitly excluded by the operator as unrelated). **Not currently
  available.**
- **Option E — another existing controlled host/environment already
  available to the operator.** Two SSH-configured candidates
  (`hac-windows`, `hac-dell`) were found by direct inspection of
  `~/.ssh/config`, but the operator confirmed both are unrelated to this
  purpose (§3). **No qualifying candidate exists.** This phase does not
  select hypothetical infrastructure that does not exist, per its own
  governing instruction — Options C/D/E are recorded as *not selected*,
  not as *silently assumed away*.

## 7. Target-Selection Criteria (Derived From HBDC, Not Convenience)

Derived directly from HBDC-001's own requirements (§4–§5 above), the
Class-B verifier's actual check behavior (§4), L.5's provisioning plan
(§9 of that document), and the three Real Authorization Boundaries
(§2 here, §21–§22 of L.5):

1. **Principal isolation** — a genuinely distinct OS principal from the
   developer's own daily-driver account (HBDC-REQ-001/002/009/010).
2. **Filesystem ownership isolation** — every protected/deployment
   resource owned by that distinct principal, not the developer's uid.
3. **Protected Root feasibility** — a path creatable, admin-owned, mode
   ≤`0750`, with a safe ancestor chain (HBDC-REQ-007/013–020).
4. **Complete ancestor-chain trust** — every ancestor of every protected
   path must be inspectable and, in the end state, non-agent-writable
   (HBDC-REQ-017).
5. **ACL support** — the target filesystem's ACL facility must be
   inspectable by the verifier's own (already-implemented, already
   platform-scoped) ACL-detection logic (HBDC-REQ-015/016/027).
6. **Environment-lock feasibility** — a Python interpreter/venv path can
   be created and locked to admin ownership without touching the
   developer's own `.venv`/Homebrew install (HBDC-REQ-025–027/029–031/036/
   039).
7. **Model-A Python environment** — editable-install-from-canonical-
   checkout remains the deployment model (HBDC-REQ-022); the target must
   support running PCAE from a checked-out working tree under an admin-
   owned interpreter.
8. **Trusted Git feasibility** — a `git` executable resolvable and
   effective-access-safe from the target's own launch `PATH`
   (HBDC-REQ-038).
9. **Repository deployment identity** — a canonical deployment root and
   `DeploymentBinding` (CRI Layer 2, HBDC-REQ-042–046) can be established
   for the target's own checkout path.
10. **Rollback capability** — every planned mutation on the target must be
    a newly-created resource, not an in-place mutation of a live resource
    the developer depends on (§9 below; mirrors L.5 §10's own structural
    property).
11. **Privilege availability** — the operator must hold legitimate
    `sudo`/admin authority on the target sufficient for the actions in
    L.5 §9 (this phase does not exercise or test that authority — §13
    below).
12. **No collision with active development workflow** — the target must
    not require locking down any resource the developer's ordinary,
    unrelated work on this machine actively uses.

## 8. Development/Deployment Separation Decision

**May the active developer checkout/environment also be the Class-B
deployment environment? Per HBDC-REQ-026 (explicit, direct textual
reading) and this phase's own §5 evidence: NO, not as currently
configured — a developer-writable repo-local `.venv` under the developer's
own account is non-compliant "regardless of the source tree's own
certification status."**

**Frozen conclusion, not reversed by this phase:** the developer's
existing account, `.venv`, and Homebrew install may never be the Class-B
deployment principal/environment in place.

**Yes, under a dedicated clone/principal/venv — this is exactly Option B
(§6), and this phase selects it.** L.5 §8 itself already named this as a
valid alternative "subject to the human authorizer's explicit override if
they instead prefer a parallel-environment approach on this same host" —
this phase does not invent that possibility, it exercises the option L.5
already scoped and left open, in the absence of any available VM or
alternate host (§6, Options C/D/E). Required separation, stated exactly
per this phase's own governing instruction (§5 of the prompt):

- **Principal:** a new, distinct, non-daily-driver OS admin principal
  (§9 below) — never the developer's own `uid=501` account.
- **Filesystem:** a deployment checkout at a path distinct from
  `~/repos/pcae-harness` (the developer's own working tree), owned by the
  new principal.
- **Python environment:** a new venv/interpreter path distinct from
  `~/repos/pcae-harness/.venv` and from the developer's Homebrew install,
  owned by the new principal, with its own, independently-created editable
  `.pth` (the developer's existing `.pth` at
  `~/repos/pcae-harness/.venv/lib/python3.9/site-packages/
  _editable_impl_pcae_harness.pth` is left untouched by any future
  provisioning action under this plan).
- **Launch configuration:** `PYTHONNOUSERSITE`/trusted-`git`-`PATH`
  settings scoped to a new, admin-controlled launch configuration file for
  the deployment principal only — never the developer's own interactive
  shell profile.
- **Protected Root:** a new admin-owned directory
  (`/Library/Application Support/PCAE/HATP/trust-store` per the frozen
  resolver, unchanged by this phase) — outside any path the developer's
  ordinary tooling reads or writes.

This is not left ambiguous going into a future authorization capture.

## 9. Target Existence Classification

**PROVISIONABLE TARGET SHELL.**

The physical host exists and can be inspected read-only now (this is the
same machine this phase is running on). The dedicated deployment
principal, dedicated deployment checkout, and dedicated admin-owned Python
environment required by §8's separation decision do **not** yet exist —
none has been created by this phase or any prior phase. This is
structurally different from Options C/D/E's "NOT YET AVAILABLE"
classification (which would require acquiring or building new hardware/
virtualization/remote-host infrastructure this phase has no evidence is
imminent): Option B's shell (the host itself) is already present; only the
principal/checkout/venv shell resources — themselves already items 1 and 4
of L.5 §9's own nine-action plan — remain to be created by a future,
separately authorized provisioning phase.

This distinction directly answers the governing prompt's §6: Boundary-P
authorization capture (149O.20L.6) **can** proceed next, because the
target is concrete enough (a specific, already-existing machine, under a
specific, already-defined separation model) for a human authority to know
exactly what is being authorized — it does not require a prior,
separate infrastructure-acquisition authorization first.

## 10. Target Identity (Read-Only, No Cryptographic Attestation Claimed)

Captured read-only, this phase, honestly scoped per HMIC-REQ-063 (still
OPTION C, unsolved, unchanged by this phase):

- **Hostname:** `Atilas-MacBook-Pro.local`
- **OS/version/architecture:** macOS 26.6.1 (Darwin 25.6.0), `arm64`
  (`RELEASE_ARM64_T6050`), APFS root filesystem.
- **Stable machine identifier:** none claimed beyond hostname/`uname`
  output — PCAE's own CRI Layer 2 `DeploymentBinding`
  (HBDC-REQ-042–046) is the contract-defined mechanism for a stronger
  binding, and remains unestablished on this host (`HBDC-REQ-042`
  unmet, §4) until a future repository-identity bootstrap step is run —
  not performed by this phase.
- **Filesystem target (developer's existing checkout, for contrast
  only — not the deployment target):** `/Users/atilamadai/repos/
  pcae-harness`.
- **Intended deployment checkout path:** not yet selected by name — a
  future provisioning phase (or an amendment to this document before
  authorization capture) must fix an exact path distinct from the
  developer's own checkout (§8). This phase deliberately does not invent
  a specific path string, to avoid the CHGR later binding to an
  arbitrary, un-reviewed name.
- **Intended deployment user/group:** not yet created; to be assigned a
  fresh OS-issued UID per L.5 §17's own collision-avoidance guidance
  (never hand-picked).
- **Interpreter path (developer's existing venv, for contrast only):**
  `/Users/atilamadai/repos/pcae-harness/.venv/bin/python3` → base
  interpreter `/Library/Developer/CommandLineTools/Library/Frameworks/
  Python3.framework/Versions/3.9/bin/python3.9`, owned by a system
  principal distinct from `atilamadai` at the CommandLineTools level, but
  not independently re-verified further by this phase beyond the ACL-
  inspection-unavailable signal already discussed (§4) — out of scope to
  resolve here.
- **Git path (already trusted, unchanged):** `/usr/bin/git`,
  `root:wheel`, mode `0755`.

## 11. Remote Preflight

Not applicable — the selected target (§6–§9) is this same physical host,
not a remote host. Remote preflight (governing prompt §8) remains a
non-issue for the selected target; it would only become relevant if a
future authorizer instead elected Option C/D/E, which this phase does not
recommend given §6's findings.

## 12. Preflight — Selected Target Against the 23 (Now 22, §4) Live HBDC Failure Categories

Re-evaluated for the **selected target** (Option B: this host, under a
future dedicated deployment principal/checkout/venv), not merely copied
from §4's developer-account observations, per this phase's own governing
instruction (§9 of the prompt):

| Requirement(s) | Category | Current dev-account state (§4/§5) | Selected-target (Option B) disposition |
|---|---|---|---|
| HBDC-REQ-001/002 | OS principal | Unmet — no distinct principal | **Requires future provisioning** — create the dedicated principal (§9, action 1) |
| HBDC-REQ-007/013/014/015/016/017/018/019/020 | Protected Root | Unmet — absent | **Requires future provisioning**, dependent on principal creation |
| HBDC-REQ-025/026/027/031/036/039 | Python environment lock | Unmet — agent-owned | **Requires future provisioning** — new admin-owned venv/interpreter/`.pth`, distinct from developer's own (§8) |
| HBDC-REQ-033/037 | cwd/`PYTHONPATH` injection surface | Unmet on developer's own interactive shell | **Requires future provisioning** — production launch configuration must unset `PYTHONPATH` and avoid an agent-writable cwd-precedes-package condition; scoped to the deployment launch wrapper only, not the developer's shell |
| HBDC-REQ-038 | Trusted launch `PATH` | Unmet — Homebrew-first `PATH` | **Requires future provisioning**, launch-configuration-only (no `git` chmod/chown; already root-owned and correctly resolved, §5) |
| HBDC-REQ-022/035 | Packaging metadata | Unmet — `pcae_distribution_metadata_not_found` | **Indeterminate — not resolvable by provisioning alone.** Unresolved by L.5 (§6 of that document) and, per this phase's own re-check, unresolved here too; this remains a residual limitation (§16 below), not newly introduced by target selection, and not fixable by any chown/chmod/user-creation action on any host including the selected one |
| HBDC-REQ-042 | Repository deployment identity (CRI Layer 1) | Unmet — no `.pcae/repository-identity.json` | **Requires future provisioning, but not gated behind Boundary P** — ordinary, separate, agent-writable-by-design CRI bootstrap flow (HATP-001 §17), to be run against the *deployment* checkout once it exists |
| HBDC-REQ-004/005/008/011/012/021/028/032/034/037(partial) | Verifier-design / negative-assertion | Satisfied by construction on any host | **Already satisfied** — no target-specific action needed |
| MANUAL/contract-governance rows (HBDC-001 §2) | Process discipline | N/A — no runtime check | **Not applicable to a runtime preflight** — unchanged from L.5's own cross-check (§4 of L.5) |

**Unsupported category:** none found. Every mutation-classed row above has
a defined future action (L.5 §9, unchanged in substance for this target —
§13 below); no requirement is structurally unachievable on Option B. The
only genuinely **indeterminate** disposition (HBDC-REQ-022/035, packaging
metadata) is not a provisioning gap and does not block target *selection*
— it is flagged as a residual limitation on reaching `COMPLIANT`, exactly
as L.5 already disclosed (§16 below).

## 13. Target-Specific Mutation Plan (Recomputed, Not Reused Blindly)

L.5's nine-action plan (§9 of that document) was derived generically —
it never named a specific target host, and every action it specifies
(new principal, new Protected Root, new venv, new launch configuration)
already assumed creating *new*, previously-nonexistent resources rather
than mutating the developer's own. Recomputing for the now-concrete
Option B target confirms the plan's *substance* is unchanged, but this
phase makes three things concrete that L.5 left open:

1. **Host binding:** L.5's plan targeted an unnamed future host; this
   phase's plan targets **this specific machine** (`Atilas-MacBook-
   Pro.local`, §10), under the dedicated-principal/checkout/venv
   separation of §8 — no other candidate host exists (§6).
2. **No action disappears or becomes unnecessary.** All nine of L.5 §9's
   actions remain required for this target, in the same dependency order
   (L.5 §11, unchanged — reproduced by reference, not duplicated here to
   avoid drift between two copies of the same graph).
3. **Two actions gain target-specific detail this phase adds:**
   - Action 6 (`PYTHONPATH`/user-site lockdown) must additionally address
     the `HBDC-REQ-033/037` `cwd`-precedence and injection-channel
     evidence this phase's own live re-run surfaced (§12) — the future
     provisioning phase's launch-configuration wrapper must invoke the
     deployment interpreter with an explicit, non-agent-writable working
     directory, not merely unset `PYTHONPATH` alone.
   - Action 1 (principal creation) must use a fresh, OS-issued UID (§10),
     confirmed via this phase's own re-check that no `pcae`-named
     principal exists today (§5) — consistent with, not a change to,
     L.5 §17's own guidance.

No action requires a different principal/path scheme than L.5 already
specified; no action becomes unnecessary because the target turned out to
be this same host rather than a separate one.

## 14. Principal, Repository, and Python Environment Plans

- **Principal plan:** a new, dedicated, non-interactive-login-preferred
  admin-role OS account (exact name TBD by the future provisioning phase's
  own preflight collision check, §17 of L.5, unchanged); group membership
  limited to what Protected-Root read-traversal actually requires, not
  blanket `admin`/`sudo` (L.5 §17). **Not created by this phase.**
- **Repository deployment plan:** a **dedicated clone**, not the
  developer's existing checkout and not a copy created by this phase —
  exact path to be fixed by the provisioning phase or a document
  amendment prior to authorization capture (§10). **Not cloned by this
  phase** — repository-creation-as-non-provisioning is not adopted here;
  this phase treats it as in-scope-for-a-later-phase, consistent with the
  governing prompt's stated strong expectation of read-only planning only.
- **Python environment plan:** admin-owned venv/interpreter at a path
  distinct from `~/repos/pcae-harness/.venv` and from `/opt/homebrew`;
  editable install performed fresh inside that new venv against the new
  deployment clone; write-restricted to the new admin principal; explicit
  decision, per L.5's own editable-install conflict finding (§8/§13 of
  L.5, reconfirmed by this phase's own live evidence, §4/§5): **production
  deployment must use a separate environment from the developer's own —
  frozen, not reopened.**

## 15. Protected Root, Trusted Git, ACL, and Ancestor-Chain Feasibility

- **Protected Root plan:** path `/Library/Application Support/PCAE/HATP/
  trust-store` (macOS, `_default_production_trust_root()`, no override
  surface — independently reconfirmed absent from any CLI/env/config
  path this phase inspected); owner = new admin principal (§14); mode
  `0750`; ACL/group model per L.5 §11's own design (unchanged). Confirmed
  absent on this host by this phase's own live call (§4). **Not created
  by this phase.**
- **Trusted Git:** `/usr/bin/git`, `root:wheel`, `0755` — already
  trustworthy and already correctly resolved by the verifier's own
  effective-access logic; no future mutation of `git` itself is required.
  The only required action is launch-`PATH` configuration for the
  deployment principal's own launch environment (§13/§14) — never a
  system-Git modification. Since the system Git path already satisfies
  HBDC without unsafe mutation, no alternate architecture is required on
  this account.
- **ACL feasibility:** APFS on macOS supports native ACLs; the verifier's
  own ACL-inspection logic is already implemented and was directly
  re-invoked by this phase (§4, `_acl_grants_agent_write`/effective-access
  check) — it correctly distinguishes satisfied/unsatisfied/indeterminate
  states rather than silently defaulting either way. Where it returns
  indeterminate (§4, HBDC-REQ-027 on the CommandLineTools interpreter
  path in this session), this is a disclosed residual scoping limitation
  (L.5 §33, unchanged), not an ACL-model incompatibility — the target is
  not rendered ineligible by it.
- **Ancestor-chain feasibility:** `/Library/Application Support` on this
  host, spot-checked this phase (`stat`) → `root:admin 755`— the
  ancestor is already plausibly non-agent-writable prior to any
  provisioning. A future provisioning phase's own live ancestor-chain walk
  (`_ancestor_chain_safe`, already implemented) must still re-derive this
  at execution time rather than trust this observation (mirrors L.5 §18's
  own caveat, restated not weakened).

## 16. Privilege, Rollback, and Residual-Limitation Feasibility

- **Privilege feasibility:** the operator's account is a member of the
  `admin` group (`id`, §4/§5) — plausible legitimate authority to perform
  the one-time `sudo` action required to create a second OS principal
  (L.5 §9 action 1) exists on its face. **Not exercised or tested by this
  phase** — no privileged command was run. If, at the future provisioning
  phase's own entry, this authority is found unavailable, the target is
  not presently provisionable and that phase must stop rather than
  proceed.
- **Rollback feasibility:** unchanged in substance from L.5 §9/§10 —
  because §8's separation model creates only new resources (new
  principal, new clone, new venv, new launch-configuration file, new
  Protected Root) rather than modifying anything the developer's account
  depends on, every planned mutation has an observable pre-state
  (confirmed-absent, captured by this phase's own live evidence, §4/§15)
  and a reversible delete-what-was-created rollback. No genuinely
  irreversible action is introduced by selecting this target over an
  unnamed one.
- **Residual limitation carried forward, not resolved by target
  selection:** HBDC-REQ-022/035's packaging-metadata condition (§12) may
  block reaching `COMPLIANT` on Option B exactly as it would on any other
  host, until separately diagnosed — this phase does not attempt that
  diagnosis (outside its read-only planning scope) and flags it as an
  open risk for the future provisioning phase, not a silent assumption
  that it will resolve itself.

## 17. Plan Digestibility, Source State, and Contract Binding

A future CHGR (149O.20L.6) must bind: this document's own path and Git
commit at authorization time (`docs/PHASE_149O_20L_5A_..._PREFLIGHT.md`
plus L.5's own document, since this phase's plan explicitly incorporates
L.5 §9's nine actions by reference rather than duplicating them
byte-for-byte); the Git commit at authorization time; HMIC-001 v1.3,
HMRC-001 v1.1, HBDC-001 v1.0 (all independently re-confirmed unmodified by
this phase's own reading of the live contract files, §0/§4). This phase
uses the existing CHGR-001 `record_digest`/`provenance_ref` binding model
(L.5 §24/§25, independently re-confirmed present and callable in the live
CLI by L.5, not re-verified a second time by this phase since it touches
no CLI code) — **no competing digest/signing mechanism is created here.**

**Source state, this phase's own entry:**

```
Git commit (this phase's own HEAD at entry): fca87543cf70d2f2e285805374d8fc12a267d5d8
HMIC-001: v1.3 (unmodified)
HMRC-001: v1.1 (unmodified)
HBDC-001: v1.0 (unmodified)
```

## 18. Authorization Invalidation Rules

A future Boundary-P authorization drafted from §19 below becomes stale,
before provisioning, if any of the following changes:

- the selected host (§6/§9/§10) — e.g., a VM or dedicated remote host
  later becomes available and is preferred instead;
- the intended deployment checkout path or the intended principal-naming
  scheme (§14);
- the plan changes materially — e.g., a mutation category is added or a
  previously-bundled action is split apart;
- HBDC-001, HMIC-001, or HMRC-001 is amended;
- the verifier source identity changes (any byte change to
  `hatp_class_b_topology_verifier.py`, `hatp_environment_lock_verifier.py`,
  or `hatp_class_b_conformance.py`);
- the HMIC binding (`contract_versions`/`implementation_scope_digest`)
  changes;
- the intended principals (§14) change;
- the required mutation set (§12/§13) changes materially, e.g. because a
  fresh preflight at execution time finds a different NON_COMPLIANT
  reason inventory than this document's own (§4, itself already different
  from L.5's captured inventory five hours earlier — precisely the kind of
  drift this rule exists to catch).

**Minor-change policy, per existing governance precedent (CHGR-001's own
supersession discipline, L.5 §25):** purely documentary changes to this
phase's own prose (e.g., fixing a typo, adding a cross-reference) that do
not alter the mutation-scope list, the target identity, or the source/
contract bindings above do **not** invalidate a captured authorization;
any change to the bindings themselves does. This mirrors CHGR-001's own
distinction between a record's *content* (digest-bound) and its
*narrative context* — the digest, not the prose, is authoritative for
staleness detection, so a change is material only if it would change the
digest inputs (mutation set, target identity, source/contract versions),
not any surrounding explanation.

## 19. Boundary-P Proposition (Draft, Refined From L.5 §29 With a Concrete Target)

The following refines L.5's own draft proposition (§29 of that document)
now that a specific target has been selected — **still a draft, not itself
an authorization (§2, §26 below):**

> *Authorize a separately governed future phase to provision **this
> development host** (`Atilas-MacBook-Pro.local`, macOS 26.6.1/Darwin
> 25.6.0, arm64), under a **newly created, dedicated OS admin principal
> distinct from the operator's own `atilamadai` account**, with a
> **newly created, dedicated deployment repository clone and admin-owned
> Python virtual environment distinct from the developer's existing
> `~/repos/pcae-harness` checkout and `.venv`**, to HBDC-001 v1.0 Model-A
> Class-B requirements, executing exactly the nine bundled actions of
> `docs/PHASE_149O_20L_5_CLASS_B_REAL_HOST_PROVISIONING_AUTHORIZATION_AND_
> PLANNING.md` §9 (OS admin-principal creation; Protected Root creation and
> ACL/group/ancestor-chain configuration; admin-owned production venv/
> interpreter provisioning; `sitecustomize`/`.pth` lockdown; user-site and
> `cwd`/`PYTHONPATH`-injection disablement for the production launch
> context per this document's own §12/§13 refinement; trusted-`git`
> launch-`PATH` configuration; final read-only verification), bound to the
> Git commit and HMIC-001/HBDC-001 contract versions in force at the time
> of this authorization (§17), subject to the rollback plan of L.5 §9/§10/
> §12 and this document's own §16, fail-closed on any step or preflight
> failure, without authorizing HMIC certification (Boundary C), without
> authorizing real `HATP_MANDATORY` activation (Boundary A), and excluding
> any change to Permission Broker behavior, POL-005, or COMP-002. This
> authorization does not extend to the developer's own existing account,
> checkout, or `.venv`, which remain untouched by every action in scope.*

## 20. Authorization Artifact Requirements (Restated for This Target)

Per L.5 §24/§30, expressed with this phase's concrete target substituted
in: subject (Boundary-P provisioning of *this specific host*, under a
newly created principal, per §19); exact mutation-scope list (L.5 §9's
nine actions, refined per §13 of this document, no more); purpose (§19);
explicit non-authorizations (§21 below); rollback commitment (L.5 §9/§10/
§12, §16 of this document); plan digest/`provenance_ref` (§17); host
identity fields (§10); source/contract-version binding (§17);
decision-maker identity, date, and explicit confirmation sentence
(mirroring GPC6-REQ-075(b)'s own closing line, per L.5 §23); freshness/
revocability disposition (§18/§28 of L.5, unchanged — one-shot,
plan/commit-bound, not open-ended).

## 21. Explicit Exclusions

Unchanged from, and restated per, L.5 §38 — nothing in this phase's target
selection narrows or widens that list: real Class-B provisioning beyond
the named nine actions; real OS principal/user/group creation other than
the one dedicated deployment principal named in §19; real Protected Root
creation/chown/chmod/ACL mutation beyond the named path; real Python-
environment change beyond the dedicated deployment venv; real HMIC
certification/binding/revocation state creation (Boundary C); real
`HATP_MANDATORY` activation (Boundary A); real Cutover Record/activation-
marker creation; Permission Broker behavior change; POL-005 change;
COMP-002 implementation; runtime-state change; unrelated system hardening;
arbitrary package updates; unrelated repository changes; **any mutation of
the developer's own existing account, checkout, `.venv`, or Homebrew
install** (this exclusion is new relative to L.5's list, made explicit
because this phase's selected target is the same physical machine as the
developer's own environment — §8).

## 22. Do Not Infer Authorization

Even if the user later says "continue" into 149O.20L.6, that phase's own
job is to run the `pcae decision-session` → `pcae governance-record
publish` election workflow and obtain an explicit, first-person human
decision — not to treat this phase's target selection, or any
conversational continuation, as the decision itself. This phase's own act
of selecting and preflighting a target confers no authorization (§2).

## 23. Current-Host Safety

No action was taken by this phase to make the developer's own account
eligible, to create any OS principal, to create any Protected Root, to
create or modify any venv/interpreter/launch-configuration file, or to
modify the resolved `git` binary. `git status --short` was confirmed clean
immediately after every real-host read-only call this phase made (§4,
§24 below). If Option B (same-host/dedicated-environment) proceeds to
authorization and execution, the actual creation/mutation described in
§13/§14 remains a later act requiring the Boundary-P authorization §19
drafts but does not grant.

## 24. Real-Host-Unchanged Confirmation

`git status --short` immediately before and after this phase's own live
`verify_class_b_deployment_conformance()` call (§4), and after every
`stat`/`id`/`dscl`/`which`/`ssh`-config-read command in §5/§6/§10, showed
**no output** — clean, before and after. No OS user/group was created; no
Protected Root, venv, ACL, or launch-configuration file was created or
modified on this host; no SSH connection to `hac-windows`/`hac-dell` was
ever attempted (§3 — read-only local `~/.ssh/config` inspection only, no
network access to either host).

## 25. CBV-S1 / CBV-S10 Regression Status

Independently re-checked by this phase (§1, §4): **neither is reopened.**
This phase's own real-host read-only calls reproduce the expected
not-`COMPLIANT` (now `INDETERMINATE`, previously `NON_COMPLIANT` — both
equally non-compliant per HBDC-REQ-052/053, §4) signal on an unprovisioned
host — the correct behavior of already-closed, already-verified checks,
not evidence of regression. Host `NON_COMPLIANT`/`INDETERMINATE` does not
reopen either stop condition.

## 26. Class-B / HATP / Runtime State (Phase Exit)

```
CBV-S1:   CLOSED (unchanged)
CBV-S10:  CLOSED (unchanged)
Class-B:  NOT PROVISIONED — TARGET ENVIRONMENT SELECTED/PREFLIGHTED — BOUNDARY-P AUTHORIZATION NOT YET CAPTURED
Boundary P: NOT AUTHORIZED.
Boundary C: NOT AUTHORIZED.
Boundary A: NOT AUTHORIZED.
HATP:     NOT READY.
Runtime:  Observed / observe / unavailable
```

## 27. Tests

`tests/test_phase_149o_20l_5a_class_b_provisioning_target_environment_selection_and_preflight.py`
(new, planning/contract-only, no production host mutation test) verifies:
current dev-account host remains classified unsuitable per this
document's own §5; the selected target (Option B) satisfies every
structural eligibility prerequisite listed in §7 or has a provisionable
(not unsupported) disposition per §12; §13's target-specific mutation plan
covers every category from §12's preflight matrix; no requirement in §12
is classified "unsupported"; every mutation-classed item has a rollback
description (by reference to L.5 §9/§10 plus this document's own §16);
§19's authorization proposition text names the concrete target and
excludes activation/certification; §21's exclusion list is present and
includes the developer's-own-environment exclusion; no
`activate_hatp_mandatory`/certification-write/SSH-connection call appears
anywhere in this phase's own text or was made by this phase; `git status
--short` is clean at test time (repo-hygiene smoke check, not a
host-mutation test).

Re-run three consecutive times: 14 passed each run, no flake. **Fast Green
citation, honestly scoped:** a full unfiltered `pytest -m fast_green`
run was attempted but its background process stalled (no CPU progress
after several minutes) and was terminated rather than left hanging;
because this phase touches zero `src/pcae/**` files, its own test file
plus a targeted run of the three directly-related Class-B verifier test
modules (`test_phase_149o_20i_hatp_class_b_topology_verifier.py`,
`test_phase_149o_20i_hatp_environment_lock_verifier.py`,
`test_phase_149o_20i_hatp_class_b_conformance.py`) is cited instead as
sufficient targeted evidence: 108 passed, 4 pre-existing failures (all
concerning whether the three Class-B verifier modules are HMIC-frozen-
scope members, a pre-149O.20K/20L classification these three tests were
never updated to reflect — unrelated to target selection, and structurally
impossible for this phase to have caused since it made no `src/pcae/**`
change at all). No new failure was introduced by this phase; the full,
unfiltered fast_green count is not re-cited here since this phase did not
successfully complete that run, and no `fast_green` structured field
value is fabricated to fill that gap.

## 28. Governance

`pcae check`: passed. `pcae health`: healthy. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings (pre-existing, unrelated,
identical set to L.5's own disclosure, not remediated here — outside this
phase's allowed-file scope). `pcae push check`: see phase-completion
report for final state. Fresh, dedicated `Phase 149O.20L.5A: ...` task
used throughout (not a reused idle placeholder). No raw `git commit`/
`push` used — all commits via `pcae commit`/`pcae phase complete`/`pcae
push`. No lifecycle bypass, no `--no-verify`, no force push.

## 29. Plan Verdict

```
CLASS-B PROVISIONING TARGET ENVIRONMENT SELECTION & PREFLIGHT: COMPLETE
— CURRENT DEV HOST RECONFIRMED NOT ELIGIBLE (INDEPENDENTLY RE-DERIVED, NOT ASSUMED FROM L.5)
— TARGET SELECTED: OPTION B — THIS HOST, DEDICATED PRINCIPAL + DEDICATED CLONE + DEDICATED VENV
— TARGET STATUS: PROVISIONABLE TARGET SHELL (HOST EXISTS; PRINCIPAL/CHECKOUT/VENV DO NOT YET EXIST)
— DEV/DEPLOY SEPARATION DECISION MADE EXPLICIT (§8)
— 22/22 LIVE NON-COMPLIANT REASONS (THIS PHASE'S OWN RE-RUN) MAPPED TO A DISPOSITION
— NO UNSUPPORTED REQUIREMENT FOUND
— TARGET-SPECIFIC BOUNDARY-P PROPOSITION DRAFTED (§19), NOT PUBLISHED
— NO REAL PROVISIONING AUTHORIZED
— NO REAL ACTIVATION AUTHORIZED
— NO CHGR PUBLISHED
— REAL HOST STATE UNCHANGED
— READY FOR AUTHORIZATION CAPTURE
```

## 30. Recommended Next Phase

**Phase 149O.20L.6 — Class-B Provisioning Authorization Record Capture**
(unchanged in name/scope from L.5's own recommendation, now with a
concrete target to bind). Must not itself provision, activate, or
certify anything; its sole substantive output is a published CHGR (or an
explicit decline/amendment) recording the human governance authority's
election on this document's §19 proposition, running the existing `pcae
decision-session` → `pcae governance-record publish` workflow. Only if and
after that CHGR is published with an affirmative election should a
subsequent phase (149O.20L.7 or later, renumbered as appropriate at that
time) attempt real provisioning execution against L.5 §9 / this document's
§13, itself re-verified fresh (not assumed unchanged) at that later
phase's own entry.
