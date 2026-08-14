# Phase 149O.20L.7 — Class-B Real Host Provisioning Execution — Stopped Before Mutation (Target Changed to Dell)

## 0. Phase Identity and Type

**Phase:** 149O.20L.7
**Type:** EXECUTION ATTEMPT, STOPPED BEFORE ANY MUTATION. This phase was
governed as the real Class-B host provisioning execution phase (Boundary
P), entering under CHGR `chgr-d4343fa51b9743f3abaeb87a881a78b1`. No real OS
principal was created. No Protected Root was created. No `chmod`/`chown`/
ACL mutation occurred. No Python environment was provisioned. No launch
configuration was written. No SSH connection to any remote host was made.
This document, its companion test file, and ordinary task/lifecycle/report
bookkeeping are the only artifacts this phase produces.
**Basis:** the CHGR itself (`.pcae/publication-execution/records/
chgr-d4343fa51b9743f3abaeb87a881a78b1.json`), re-read directly; `docs/
PHASE_149O_20L_5A_CLASS_B_PROVISIONING_TARGET_ENVIRONMENT_SELECTION_AND_
PREFLIGHT.md` §18 (Authorization Invalidation Rules); an explicit human
decision, obtained during this phase, changing the provisioning target
from the Mac to a different, previously-excluded host.

## 1. Entering State (Independently Reconfirmed)

```
$ git status --short                → (clean)
$ git status --branch --short       → ## main...origin/main
$ git log --oneline origin/main..HEAD → (empty)
$ git rev-list --count origin/main..HEAD → 0
```

- `pcae health`: healthy. Required PCAE files: all present. Policy
  validation: valid. Git status: clean. Agent lock: stale
  (`claude-code-session`, pre-existing, not remediated by this phase — no
  file in this phase's own scope governs lock staleness).
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing, historical
  `tasks/done/` entries missing from `tasks/DONE.md`, predating this phase
  by many prior phases (149O.1H.4 onward). Unrelated to Class-B
  provisioning; outside this phase's allowed-file scope; not remediated
  here.
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest`: 149O.20L.6A's canonical report,
  consistent; recommended next phase named this phase (149O.20L.7),
  conditional on independent re-verification at this phase's own entry —
  exactly what §2 below performs.
- `pcae phase-report reconcile --phase-id 149O.20L.6A`: status
  `delivery_recorded_bookkeeping_incomplete` (pre-existing receipt
  bookkeeping gap, mutation none — read-only reconciliation only, per this
  phase's own instruction not to mutate L.6/L.6A records). L.6/L.6A
  records were not modified by this phase.

Entering authority state, reconfirmed at this phase's own entry, before
any human instruction was received this phase:

```
Boundary P: INDEPENDENTLY VERIFIED AUTHORIZED BY CHGR chgr-d4343fa51b9743f3abaeb87a881a78b1
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

## 2. CHGR Re-Verification At Phase Entry (Independent, Not Assumed From L.6A)

`pcae governance-record inspect` and `pcae governance-record verify` were
re-run live against
`.pcae/publication-execution/records/chgr-d4343fa51b9743f3abaeb87a881a78b1.json`
this phase's own session:

- `inspect`: `outcome: inspected`, `record_family:
  human_governance_record`, `schema_version: 1.1`, digest
  `413e846f630b26add18a8ff70f0e432a19264f70743218a14565c6f8da8f37aa`.
- `verify`: `outcome: verified` — `schema_shape`: passed,
  `digest_self_consistency`: passed, `lifecycle_structural_legality`:
  passed; `confirmation_binding`/`provenance_consistency`/
  `integrity_consistency`/`template_resolution`: skipped (no related
  artifacts supplied to this single-file invocation — matches the known,
  already-adjudicated shape from L.6A, not a new finding).
- Direct field re-read of the record itself (not phase-report prose):
  - `lifecycle_state`: `published`.
  - `selected_option_id`: `approve`.
  - `decision_subject`: *"Boundary-P provisioning authorization for
    Class-B target Option B (dedicated principal/clone/venv on
    Atilas-MacBook-Pro.local), per L.5A doc §19 proposition ..."* — the
    record's own subject text names the Mac by hostname explicitly.
  - `conditions`: *"... One-shot, plan/commit-bound (Git commit
    2e97651ef9366e6427b26ea061deac827b6485e9, HMIC-001 v1.3, HMRC-001
    v1.1, HBDC-001 v1.0) — material drift before provisioning invalidates
    this authorization per L.5A §18."* — the record's own text names its
    own invalidation rule.
  - No `revocation_ref`/`superseded_by`/`deprecated_by` field present; it
    remains the only `chgr-*.json` record in the repository.

**Conclusion of this section:** as of entry, the CHGR was still
structurally valid, unrevoked, and unsuperseded, and remained bound to the
Mac target exactly as L.6A had found. §3 below records why this no longer
matters for real-host execution this phase.

## 3. Material Target Change (Human-Directed, This Phase)

Before any preflight, verifier re-run, rollback-baseline capture, or
mutation was attempted, the human governance authority (Atila Madai)
issued an explicit instruction changing the provisioning target:

> PCAE development remains on the MacBook. The Dell Ubuntu machine becomes
> the current PCAE deployment target. The Dell may host other development
> projects under separate Unix accounts; PCAE must use its own isolated
> deployment account and resources on it. For the current product model,
> PCAE is usable separately per repository — centralized multi-repository
> governance is deferred. This is a material target change that
> invalidates the current Mac-specific Boundary-P execution path. Stop
> Phase 149O.20L.7 before mutation and recommend a target-reselection/
> read-only Dell preflight phase. Do not provision the Dell yet and do not
> reuse the existing Mac-target CHGR as authority for Ubuntu.

This is a genuine, first-person, explicit human decision — not an
assumption or inference by this phase (§22 of L.5A's own governing rule:
"even if the user later says 'continue' ... that is not the decision
itself" — symmetrically, an explicit *stop-and-redirect* instruction is
exactly the kind of first-person act that rule contemplates being able to
receive).

**Direct consequence, applying L.5A §18 literally:** "the selected host
... changes" is listed by name as an authorization-invalidating condition.
The CHGR's own `decision_subject` (§2 above) names `Atilas-MacBook-Pro.
local` specifically, not "a host" generically. The instant the target
changes to a different physical machine (the Dell Ubuntu host, previously
identified in L.5A §3/§6 as `hac-dell`, 192.168.192.200 — a host L.5A's
own human clarification at that time had *excluded* as "unrelated," now
explicitly *un-excluded* by this phase's own human instruction, which this
phase treats as authoritative for target scoping exactly as L.5A treated
the original exclusion), the CHGR no longer authorizes anything. It was
never bound to "any host the operator later prefers" — it was bound to
one, named, specific machine.

**This phase draws no distinction between "the CHGR is revoked" and "the
CHGR no longer applies to the only host this phase is now permitted to
touch."** Both reach the same operative conclusion: no real-host mutation
of any kind may occur this phase, on the Mac or on the Dell.

## 4. Explicit Non-Actions This Phase (Per the Human Instruction)

Per the human instruction (§3), this phase did **not**:

- run `sysadminctl`, `useradd`, `dscl -create`, or any other
  principal-creation command on the Mac or the Dell;
- create, `chmod`, `chown`, or ACL-mutate any Protected Root, on the Mac
  or the Dell;
- create or modify any venv, interpreter, `.pth`, or launch-configuration
  file, on the Mac or the Dell;
- open an SSH connection or any other network connection to the Dell
  (`hac-dell`, 192.168.192.200) or to `hac-windows` (192.168.192.104);
- run any read-only preflight, `id`/`dscl`-equivalent inspection, or
  `verify_class_b_deployment_conformance()` re-invocation *against the
  Dell* — the human instruction explicitly reserves that to a future,
  separately governed phase ("recommend the appropriate
  target-reselection/read-only Dell preflight phase"), not this one;
- draft, publish, or reuse any CHGR for the Dell target;
- treat `chgr-d4343fa51b9743f3abaeb87a881a78b1` as authority for anything
  beyond what it already was (Mac-target Boundary-P provisioning, now
  moot).

`verify_class_b_deployment_conformance()` was **not** re-invoked this
phase against either host — the fresh-preflight step (L.7's own governing
prompt §4–§6) is superseded by the target change before it was reached;
running it against the Mac would produce a result for a target this phase
no longer has authority to provision, and running it against the Dell
would be exactly the read-only-but-target-touching action the human
instruction reserves for a future phase.

## 5. Rollback / Nine-Action Plan

Not entered. No rollback baseline was captured because no mutation was
attempted or planned against any host this phase. The nine-action plan
(L.5 §9, refined by L.5A §13) remains bound to the Mac target and is not
carried forward to the Dell by this phase — a future Dell-target planning
phase must independently re-derive its own mutation plan against that
host's own topology, not assume L.5/L.5A's Mac-specific plan transfers
unchanged (per L.5A §18's own drift rule, applied here by analogy: a
different host can have a different collision set, different ancestor
chain, different ACL facility, different available privilege model —
Ubuntu is not macOS, `useradd`/`usermod`/POSIX ACLs or `setfacl` are not
`sysadminctl`/macOS ACLs, and the Protected Root default resolver path
itself is platform-conditional).

## 6. Boundary and Class-B State (Phase Exit)

```
Boundary P: NOT AUTHORIZED (for any current target — the sole existing
            CHGR is Mac-bound and material target drift has occurred;
            it does not authorize Dell provisioning, and it no longer
            usably authorizes Mac provisioning since Mac is not the
            currently intended deployment target)
Boundary C: NOT AUTHORIZED
Boundary A: NOT AUTHORIZED
Class-B:    NOT PROVISIONED
HATP:       NOT READY
Runtime:    Observed / observe / unavailable
```

`chgr-d4343fa51b9743f3abaeb87a881a78b1` itself is **not modified, revoked,
or superseded** by this phase — no mutating governance-record command
exists to do so in this repository's current increment besides `publish`,
which was not invoked. It remains on record, unrevoked, as history: a
real, valid, human-elected Boundary-P authorization for the Mac target,
now superseded in practical effect by the human's own subsequent target
change, not by any artifact-level act.

## 7. Developer-Environment and Real-Host-Unchanged Confirmation

`git status --short` was clean before and after this phase's own work.
No OS principal, Protected Root, venv, ACL, or launch-configuration file
was created or modified on the Mac. No network connection was made to the
Dell or to `hac-windows`. The developer's own `atilamadai` account,
`~/repos/pcae-harness` checkout, and `.venv` are unchanged.

## 8. Recommended Next Phase

**Phase 149O.20L.7A — Class-B Target Re-Selection & Dell Read-Only
Preflight.** Must, at minimum:

1. Independently re-derive target eligibility for the Dell Ubuntu host
   (previously `hac-dell`, 192.168.192.200) using L.5A's own eligibility
   criteria (§7 of that document) adapted to Linux/Ubuntu — principal
   isolation, filesystem ownership isolation, Protected Root feasibility,
   ancestor-chain trust, ACL support (POSIX ACLs / `setfacl`, not macOS
   ACLs), environment-lock feasibility, Model-A Python environment
   support, trusted-`git` feasibility, repository deployment identity,
   rollback capability, privilege availability, no collision with other
   development projects/accounts already on that machine.
2. Obtain the operator's own account/privilege details on the Dell (SSH
   access, sudo/admin authority) — not assumed from the Mac session.
3. Perform read-only inspection only (no mutation) — this may include the
   first legitimate SSH connection to the Dell for this purpose, which
   this phase (149O.20L.7) explicitly did not perform.
4. Re-run `verify_class_b_deployment_conformance()` (or the
   Linux-appropriate equivalent path) against the Dell, live, no mock.
5. Recompute a target-specific nine-action (or however many actions are
   actually required on Ubuntu) mutation plan — not a copy of the Mac
   plan.
6. Draft a **new** Boundary-P proposition naming the Dell specifically —
   this phase's own §3 finding means the existing CHGR is not reusable as
   authority for it; a fresh `pcae decision-session` →
   `pcae governance-record publish` election is required before any real
   Dell mutation, exactly mirroring L.5→L.6's own workflow but for the new
   target.
7. Explicitly preserve, unchanged: PCAE remains a per-repository tool (no
   centralized multi-repository/company governance in scope); other
   projects/accounts that may already exist on the Dell are out of scope
   and must not be touched; Boundary C and Boundary A remain unavailable
   throughout.

Only after that phase's own CHGR is published with an affirmative
election should a subsequent phase attempt real Dell provisioning
execution — itself re-verifying freshness at its own entry, exactly as
this phase (149O.20L.7) was required to and did (§2), before any human
target-change instruction arrived.

## 9. Governance

`pcae check`: passed. `pcae health`: healthy. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings (pre-existing, unrelated,
not remediated here — outside this phase's allowed-file scope). `pcae
push check`: see phase-completion report for final state. Fresh, dedicated
`Phase 149O.20L.7: ...` task used throughout (not a reused idle
placeholder). No raw `git commit`/`push` used — all commits via `pcae
commit`/`pcae phase complete`/`pcae push`. No lifecycle bypass, no
`--no-verify`, no force push. No real host mutation, on any host,
occurred at any point in this phase.

## 10. Phase Verdict

```
CLASS-B REAL HOST PROVISIONING EXECUTION: NOT PERFORMED — STOPPED BEFORE MUTATION
REASON: MATERIAL TARGET CHANGE (MAC → DELL), HUMAN-DIRECTED, MID-PHASE
CHGR chgr-d4343fa51b9743f3abaeb87a881a78b1: STILL VALID/UNREVOKED AS A MAC-TARGET RECORD, NOT REUSABLE FOR DELL
NO OS PRINCIPAL CREATED — NEITHER HOST
NO PROTECTED ROOT CREATED — NEITHER HOST
NO ACL/CHMOD/CHOWN MUTATION — NEITHER HOST
NO SSH CONNECTION MADE TO THE DELL
NO NEW CHGR PUBLISHED
CLASS-B: NOT PROVISIONED
BOUNDARY P: NOT AUTHORIZED (for any current target)
BOUNDARY C: NOT AUTHORIZED
BOUNDARY A: NOT AUTHORIZED
REAL HOST STATE UNCHANGED (BOTH HOSTS)
RECOMMENDED NEXT PHASE: 149O.20L.7A — CLASS-B TARGET RE-SELECTION & DELL READ-ONLY PREFLIGHT
```
