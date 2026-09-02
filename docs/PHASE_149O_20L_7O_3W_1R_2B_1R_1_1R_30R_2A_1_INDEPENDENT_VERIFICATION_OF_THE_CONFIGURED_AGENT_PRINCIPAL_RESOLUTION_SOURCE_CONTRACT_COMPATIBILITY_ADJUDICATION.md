# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1 — Independent Verification of the Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication

**Status: COMPLETE — ADJUDICATION VERIFIED WITH CORRECTIONS** (not BLOCKED).
Verification only. No `src/pcae` change; no normative-contract change; no
HPAC-PAWA-001 v1.1 authoring; no implementation. The sole deliverables are this
document, a new read-only IV test suite, and the governed status / decisions /
task-memory / completion artifacts.

**Verification-entry SHA (V):** `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a`
(== J, the finalized `.1R.30R.2A` head; `origin/main..HEAD = 0` at entry).

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 1. Scope and method

`.1R.30R.2A.1` independently re-derives — from HPAC-PAWA-001 v1.0, HPAC-001 v2.1,
RHAMP-001 v1.0, HBDC-001 v1.2, CPIPC-001 v1.0, and `src/pcae` production source,
read as primary evidence, **not** from the `.1R.30R.2A` adjudication prose —
every load-bearing `.1R.30R.2A` claim:

1. the F-1 configured-agent-principal resolution-source gap exists;
2. no canonical logical-agent → OS-`(uid, gids)` binding exists in `src/pcae`;
3. the three F-1 predicates are distinct and must not be collapsed;
4. `_current_agent_identity()` is the live invoking process, not a configured id;
5. R1 (a protected `.authority/agent-exclusion.json`, symbolic OS account name,
   `(uid, gids)` resolved live) is the preferred resolution;
6. R1 survives the group-drift, group-removal, UID-reuse, account
   deletion / recreation, account-rename, rollback, machine-migration, and
   same-UID-topology adversaries;
7. R2, R3, and R4 are correctly rejected;
8. adding the exclusion record is a **new authority input** — a normative delta;
9. the contract verdict is **B — HPAC-PAWA-001 v1.1 MINOR** (no MAJOR trigger);
10. HPAC-001 v2.1 and RHAMP-001 v1.0 need not change;
11. configured-agent resolution is atomic with the §33 recognition unit;
12. the D1 phase decomposition is valid under CPIPC-001 §4;
13. `.1R.30R.2A.2` is the correct contract-freeze successor.

**Verification principle:** RE-DERIVE, DO NOT TRUST. Each claim is treated as a
hypothesis and checked against source.

---

## 2. Immutable SHAs (independently derived at V)

| Symbol | SHA | Meaning |
|---|---|---|
| B30 | `8e65529596fc351face4b83c4b5d08573326d034` | finalized historical `.1R.30` **BLOCKED** head (immutable; never reused) |
| H30R | `ca0d42873f14bb94e8eb4ef7a27e1b456324cd2a` | finalized `.1R.30R` head |
| H30R1 | `91741564035cb441c0e2b16760c1997afddd4394` | finalized `.1R.30R.1` head |
| **A** | `5b45aa7b444f15852c51985879570b8913fedbe4` | finalized `.1R.30R.2` head (HPAC-PAWA-001 v1.0 freeze) — also the `.1R.30R.2A` phase-entry |
| **J** | `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` | finalized `.1R.30R.2A` head (adjudication) |
| **V** | `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` | `.1R.30R.2A.1` verification-entry (== J) |

Derived by `git rev-parse` / `git log --format=%s` on the finalization commits
(`… reconcile governed push state … (pushed; origin/main..HEAD = 0)`), not read
from prose. `git diff A J -- src/pcae` and `git diff A J -- docs/contracts` are
both **empty** (the `.1R.30R.2A` adjudication changed neither) — independently
re-confirmed.

---

## 3. F-1 gap — independently reproduced

### 3.1 What the frozen contract requires

Read in full at V, HPAC-PAWA-001 v1.0:

- **§2 Terminology** — *"Configured agent principal — the OS identity under which
  the autonomous PCAE agent/runtime is configured to execute for this
  deployment, resolved from canonical PCAE agent configuration (HBDC-001 §3's
  `PCAE_AGENT_PRINCIPAL` for a Class-B deployment; §9). It is **not**
  `os.geteuid()` of whatever process happens to be running (finding F-1)."*
- **§9 / HPAC-PAWA-REQ-021** — resolved from *"canonical PCAE agent configuration /
  lock semantics, never from caller input, an environment variable, a CLI flag,
  `--agent-id`, repository state, or the live `os.geteuid()`"*; *"the
  implementation SHALL name the exact canonical resolution source in its
  `.1R.30R.3` contract-production traceability (§73)."*
- **§9 / HPAC-PAWA-REQ-022** — identity form `(uid, gids)` on POSIX, *"resolved
  from the configured principal, **not** the invoking process's live ids"*;
  *"`_effective_write_access` already accepts `uid` / `gids` as parameters, so the
  negative boundary check SHALL be evaluated against the configured agent
  principal's ids on the production-writer path."*
- **§9 / HPAC-PAWA-REQ-023** — unresolvable / ambiguous / unmappable ⇒ **fail
  closed** (`agent_principal_unknown`); *"SHALL NOT default to `os.geteuid()`."*
- **§10 / HPAC-PAWA-REQ-026** — the per-predicate identity matrix names the
  `configured-agent exclusion` predicate's **Authority source** as *"canonical
  PCAE agent configuration / lock (§9)."*
- **§26 / HPAC-PAWA-REQ-061** — `_effective_write_access(root,
  configured_agent_uid, configured_agent_gids)` returns `False` **and**
  `_ancestor_chain_safe(root, configured_agent_uid, configured_agent_gids)`
  returns `True`.
- **§33 / HPAC-PAWA-REQ-074 steps 2, 3, 7** — the frozen recognition sequence
  resolves the configured agent principal (step 2), evaluates the
  configured-agent exclusion (step 3), and checks the not-configured-agent
  current context (step 7).

### 3.2 What production source provides — read at V

| Source (read in full / relevant scope) | Stores / returns | OS identity? | Configured vs. live? |
|---|---|---|---|
| `core/policy.py` `DEFAULT_AGENT_REGISTRY` / `core/agent.py` `KNOWN_AGENTS` (`AgentEntry`) | `agent_id` string + `agent_type` + `role` + `capabilities` | **no** | logical only |
| `.pcae/agent-lock.json` (`core/agent.py` `AgentLock`, `build_agent_lock_data`) | `agent_id`, `acquired_at`, `git_branch`, `active_task` | **no** | logical only; `agent.py:106-107` comment: *"agent_id is descriptive only … the non-authenticating, non-authorizing governance semantics this label carries"* |
| `core/hatp_class_b_topology_verifier._current_agent_identity()` (line 143) | `(os.geteuid(), frozenset(os.getgroups()) \| {os.getegid()})` | yes | **live invoking process** — docstring: *"Live process identity — never a caller-supplied value"* |
| `core/hpac_foundation.HPACStoreAuthority._validate_production_boundary()` (line 351) | calls `_current_agent_identity()` → `_effective_write_access` / `_ancestor_chain_safe` | yes | **live** |
| `core/hatp_bootstrap.py` | `pwd.getpwuid(os.geteuid())` in a **comment only** (line 220); `inspect_bootstrap_environment` compares live `os.getuid()` vs. store `st_uid`, **persists nothing** | yes | live; ephemeral |
| `DeploymentBinding` / HATP `manifest.json`; `HPAC-STORE-AUTHORITY/1.0` manifest | `repository_id`, `{device,inode}` root identity, opaque `principal_id`, `store_id` | **no OS uid** | — |
| `provenance.py` `derive_producer_provenance` | logical `producer_component` constant | **no** | — |

**Exhaustive absence search, re-run at V:**

```
grep -rn --include='*.py' -E "getpwnam|getpwuid|getgrnam|getgrgid|getgrouplist|getgrall|import pwd|import grp" src/pcae | grep -vi test
  → hatp_bootstrap.py:220           (a COMMENT, not code)
  → hatp_class_b_topology_verifier.py:315-316,323,328
      import grp / import pwd, then `pwd.getpwnam(name).pw_uid == agent_uid`
      and `grp.getgrnam(name).gr_gid in agent_gids` — inside
      `_acl_grants_agent_write_macos`, resolving an ACL-entry NAME against an
      ALREADY-KNOWN live `agent_uid` / `agent_gids`. NOT a configured-agent
      source: it consumes ids it is given, it does not produce a configured id.

grep -rn --include='*.py' -E "PCAE_AGENT_PRINCIPAL|AGENT_PRINCIPAL|configured_agent|production_writer|HPACAuthorityClass\.PRODUCTION" src/pcae | grep -vi test
  → 0 matches for PCAE_AGENT_PRINCIPAL / AGENT_PRINCIPAL / configured_agent
  → 0 `production_writer` factory
  → HPACAuthorityClass.PRODUCTION appears only in CONSUMPTION / comparison
    checks (runtime_authority.py, hpac_foundation.py, hpac_verifier.py,
    runtime_dispatch_gate5.py) — never a mint path
```

`HBDC-001 v1.2 §13` (environment lock, HBDC-REQ-025..039) is scoped to the
Python execution environment (interpreter, venv, `PYTHONPATH`, user-site, import
hooks); it defines **no stored agent-principal OS-identity record**.
`PCAE_AGENT_PRINCIPAL` (HBDC-001 §3 / `149O.1B.1 §4` terminology) is a
**conceptual role name**, not an implemented resolution mechanism.

### 3.3 `HPACStoreAuthority._validate_production_boundary()` — read at V

```python
def _validate_production_boundary(self) -> None:
    if self.root != resolve_hpac_protected_root().absolute():
        raise HPACAuthorityError("production HPAC authority cannot be redirected")
    from pcae.core.hatp_class_b_topology_verifier import (
        _ancestor_chain_safe, _current_agent_identity, _effective_write_access,
    )
    agent_uid, agent_gids = _current_agent_identity()          # ← LIVE os.geteuid()
    writable, reason, _ev = _effective_write_access(self.root, agent_uid, agent_gids)
    ancestors_safe, diag  = _ancestor_chain_safe(self.root, agent_uid, agent_gids)
    if writable is not False or ancestors_safe is not True:
        raise HPACAuthorityError("production HPAC root is not protected from the current agent …")
```

The negative boundary is evaluated against the **live invoking process**. On a
compliant two-OS-principal deployment the production writer tool runs **as the
deployment owner** (admin uid); `os.geteuid()` is then the admin uid;
`_effective_write_access(root, admin_uid, …)` returns `True`; the boundary
**raises for a legitimate admin invocation** — it answers *"can the admin
write?"*, not *"can the configured agent write?"*. This is exactly `.1R.30R.1`
finding F-1 and exactly the gap `.1R.30R.2A` claims.

### 3.4 `HPACStoreAuthority.writer()` — read at V

```python
def writer(self, role: str, *, subject: Optional[str] = None) -> HPACWriterCapability:
    …
    raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")
```

No positive `PRODUCTION` mint path exists — consistent with HPAC-PAWA-001
§1 / HPAC-PAWA-REQ-002(c) and the historical `.1R.30` BLOCKED finding.

### 3.5 Verdict on the gap

**F-1 GAP: CONFIRMED — independently reproduced.** No canonical, non-caller,
agent-unwritable, repository-independent source anywhere in `src/pcae` binds the
configured PCAE agent principal to an OS `(uid, gids)` for protected-root
authorization. Every existing OS-identity resolution in the HBDC / HPAC
production-boundary apparatus evaluates the **live invoking process**.
`.1R.30R.2A` **does not misstate F-1** (no early-stop condition).

---

## 4. Three-predicate separation — independently verified

HPAC-PAWA-001 §10 matrix + §26 / §28 / §31 + §33 steps 3 / 7 / 8, read at V:

| # | Predicate | Subject identity | Authority source | Live or configured | Substitutable? |
|---|---|---|---|---|---|
| 1 | `agent_has_protected_write_authority` (§26, REQ-061/063) | the **configured** PCAE agent principal | canonical PCAE agent config / lock (§9) | **configured** | **NO** |
| 2 | `current_context_is_agent` (§31, REQ-071) | the **current invoking OS process** vs. the configured agent principal | §9 source **+** live process identity | both operands | **NO** |
| 3 | positive write probe (§28, REQ-065/066) | the **current invoking OS process** | a live `O_EXCL\|O_NOFOLLOW` create-and-unlink under `.authority/` | **live** (`os.geteuid()` correct here) | it is an operation, not a claim |

- #1 asks *"would the configured agent be able to mutate the anchor?"* — a
  property of a **stored/configured** identity.
- #2 asks *"is this call being made **as** the configured agent?"* — a
  comparison of the **live** process against the configured identity.
- #3 asks *"does this process **actually** hold write authority **now**?"* — an
  operation.

None substitutes for another: #3 passing does not establish #1 (a
mis-configured host where the agent *also* has write would pass #3 as the admin
yet fail #1); #1 holding does not establish #2 (a compliant deployment could
still be invoked *as* the agent by mistake — #2 catches it); #2 holding does not
establish #3 (the admin context must still prove live write). `.1R.30R.2A` §3 /
§12 keeps them distinct. **VERIFIED.**

---

## 5. `_current_agent_identity()` — independently verified

`hatp_class_b_topology_verifier.py:143`:

```python
def _current_agent_identity() -> "tuple[int, frozenset[int]]":
    """Live process identity — never a caller-supplied value (plan §7)."""
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}
```

- **Returns:** the live effective uid + (supplementary ∪ effective) gids of the
  running process.
- **Historical validity (HBDC):** every HBDC Class-B conformance check and
  `hpac_foundation._validate_production_boundary` answer *"can **this process**
  write X?"* — for those, the live identity is the correct subject.
- **Invalid for PAWA §26:** §26 asks about the **configured** agent principal,
  which on a two-principal deployment is a *different* account than the invoking
  (admin) process. Reusing `_current_agent_identity()` there evaluates the wrong
  subject (§3.3).
- **Correct future PAWA use:** `_current_agent_identity()` is the subject of the
  §28 positive write probe and **one operand** of the §31 comparison — never the
  §26 operand.

`.1R.30R.2A` §4 states exactly this. **VERIFIED.**

---

## 6. Existing-canonical-mapping search — result: NONE

The §3.2 absence search is exhaustive over the production tree and canonical
configuration. The nearest constructs and why each fails:

- **agent registry / `.pcae/agent-lock.json`** — logical strings; explicitly
  *non-authenticating, non-authorizing*.
- **`_current_agent_identity()`** — live process, not configured.
- **`DeploymentBinding` / HATP trust store** — opaque `principal_id` + a
  deployment root; no OS uid.
- **`HPAC-STORE-AUTHORITY/1.0` manifest** — `{device,inode}` + `store_id`; no
  owner uid, and its owner is the *deployment owner*, not the agent.
- **HBDC environment lock** — interpreter / venv / path integrity; no agent-uid
  record.
- **`hatp_bootstrap.inspect_bootstrap_environment`** — a live, ephemeral
  same-account check; persists nothing.

**No overlooked binding exists** (no early-stop condition). `.1R.30R.2A` §5.
**VERIFIED.**

---

## 7. R1 adversarial analysis — independently re-derived

R1 as adjudicated (`.1R.30R.2A` §7.1 / §12.2): a protected record
`<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`, closed schema
`HPAC-PAWA-AGENT-EXCLUSION/1.0`, storing the **symbolic OS account name** of the
configured agent principal (**no uid integer**) + `installation_id` +
`{device,inode}` + `generation` + provenance + digest + `state`; provisioned
out-of-band by the deployment owner alongside `deployment-owner.json`;
agent-unwritable (`.authority/` mode `0700`, deployment-owner-owned); `(uid,
gids)` resolved **live** from `pwd` / `grp` at every §33 recognition.

### 7.1 Symbolic-identity trust (prompt §13)

- **Who provisions the name?** The deployment owner, out-of-band, via filesystem
  write to `.authority/` — the same authority that installs `deployment-owner.json`
  (HPAC-PAWA-REQ-056). The configured agent principal provably lacks write to
  `.authority/` (§12 / §17 / §32 of the contract; enforced identically to the
  descriptor). **Not agent-controlled.**
- **Env / caller override?** The production `production_writer(...)` signature
  carries no account-name / uid / gids parameter (`.1R.30R.2A` §10); a mutable
  environment variable MAY at most *locate* protected configuration, never *be*
  the identity (contract §11 / REQ-029 discipline extended). **Not
  caller/env-controlled.**
- **Repository content?** The record lives outside every repository, under the
  compiled-in protected root (contract §11 / REQ-028). **Not repo-controlled.**

R1's symbolic account string is **not** caller / environment / repository
controlled (no early-stop condition). **VERIFIED.**

### 7.2 uid resolution (prompt §14)

`pwd.getpwnam(symbolic_account).pw_uid` (or the platform equivalent). Failure
cases and required behaviour:

| Case | Required behaviour | Basis |
|---|---|---|
| account name unknown (`KeyError`) | `agent_principal_unknown` — fail closed | HPAC-PAWA-REQ-023 |
| lookup raises (`OSError` / NSS failure) | `agent_principal_unknown` — fail closed | REQ-023, §0 fail-closed |
| duplicate / inconsistent passwd entry | `agent_principal_unknown` — fail closed | REQ-023 |
| account deleted after provisioning | name no longer resolves → `agent_principal_unknown` | §6 table |

All fail closed. `.1R.30R.2A` §12.2 (`UID HANDLING`: *"never persisted as
authority; resolved live; unresolvable name → `agent_principal_unknown`"`).
**VERIFIED.**

### 7.3 group resolution (prompt §15)

The check needs **all** groups that affect protected-root access, not merely the
primary gid. `_effective_write_access` already tests group-write via
`st_gid in agent_gids`, so the resolved `agent_gids` must be the account's
**current** primary + supplementary set. The platform-appropriate enumeration
(`os.getgrouplist(name, pw_gid)` on Linux; `grp.getgrall()` scan or the
equivalent on macOS) is an adapter detail; the **normative property** — "the
account's current full group membership" — is what v1.1 freezes (HPAC-PAWA-REQ-132
discipline: properties, not command syntax). `.1R.30R.2A` §6 / §12.2
(`GROUP HANDLING`: *"live enumeration of the account's current primary +
supplementary groups at each recognition"*). **VERIFIED.**

### 7.4 group-drift adversary (prompt §16) — DECISIVE for the live model

Scenario: at provisioning the configured agent account lacks any root-writable
group. Later an operator adds the agent account to a group that grants write to
`<HPAC_PROTECTED_ROOT>` (or a safe ancestor).

- **Static `(uid, gids)` snapshot:** stale — the new group is invisible; §26
  passes incorrectly; a `PRODUCTION` writer is minted for a deployment where the
  agent **can** now reach the anchor. **UNSAFE.**
- **R1 live resolution:** the next §33 recognition enumerates the account's
  **current** groups, sees the new group, `_effective_write_access(root,
  agent_uid, agent_gids)` returns `True` → `agent_has_protected_write_authority`
  → fail closed, no writer. **SAFE.**

This is the load-bearing reason R1 stores a name and resolves live rather than
snapshotting. `.1R.30R.2A` §6 states it correctly. Group drift is **detected**
(no early-stop condition). **VERIFIED.**

### 7.5 group-removal (prompt §17)

If the agent account **loses** a group, live resolution reflects the lower
authority at the next recognition; the deployment may become eligible again
**with no reprovision**. This is acceptable under the threat model: group
membership is managed by the OS account administrator (in the TCB,
HPAC-PAWA-REQ-018); a reduction in the agent's authority strictly *improves* the
exclusion property, and §26 is a *live* effective-access test by design. No
"currentness event" is required for a strengthening change. `.1R.30R.2A` §6 is
consistent (the table's "SAFE" entries are symmetric). **VERIFIED** — no
correction.

### 7.6 UID-reuse adversary (prompt §18)

Scenario: the agent account `A` is deleted; its numeric uid is later reassigned
to a different account `B`.

- R1 resolves **by name** `A`. After deletion, `getpwnam("A")` fails →
  `agent_principal_unknown` → fail closed. The stale uid is **never** trusted on
  its own. **SAFE.**
- If `A` is later **recreated** (same name, possibly a new uid): see §7.7.

`.1R.30R.2A` §6 (`UID reuse` row: *"name no longer resolves … →
`agent_principal_unknown` (fail closed)"`). **VERIFIED** for the
deletion-then-reuse-by-another-name case.

### 7.7 account deletion / recreation (prompt §19) — **CORRECTION C-1**

Scenario: the symbolic account `A` is deleted, then **recreated under the same
name `A` with a different uid** (e.g. a rebuild, a directory-service
re-sync, or an attacker with account-management authority — the last being
outside the stated TCB, but the benign cases are real).

- **Pure-symbolic R1 (as adjudicated):** `getpwnam("A")` now resolves cleanly to
  the **new** uid. Recognition proceeds and silently treats the new principal
  instance as the excluded configured agent. If the new `A` happens to hold
  protected-root write authority, §26 catches it (`agent_has_protected_write_authority`);
  but if it does not, the deployment **silently rebinds** to a different OS
  principal instance with no fail-closed signal and no reprovision.
- **`.1R.30R.2A` is internally inconsistent here.** §6's `UID reuse` row says
  the live-resolved uid is checked against *"any bound expectation"* — but §7.1 /
  §8 / §12.2 freeze *"the symbolic OS account name … **no uid integer**"*. A
  pure-symbolic record has **no bound expectation** to compare against. The
  adjudication's own threat narrative presumes a pinned uid its selected schema
  does not carry.

**C-1 — the v1.1 freeze SHOULD adopt the R1-HYBRID model:** store the symbolic
account name **and** the `provisioned_uid` observed at provisioning time; at
every §33 recognition require `pwd.getpwnam(name).pw_uid == provisioned_uid`
(mismatch → `agent_principal_unknown`, fail closed), and still enumerate groups
**live** for the effective-access check. This:

- closes the deletion → recreation-under-new-uid silent-rebind path with an
  explicit fail-closed mismatch → deliberate reprovision (consistent with
  HPAC-PAWA-REQ-054/055: "migration is always a deliberate act");
- makes account rename a clean lookup failure **and** a uid mismatch;
- leaves group-drift detection **unchanged** (only the uid is pinned; groups
  stay live);
- resolves `.1R.30R.2A`'s §6-vs-§12.2 internal inconsistency;
- is **additive** (one extra field in the closed schema) and
  **authority-preserving** — it *tightens* a bound, which HPAC-PAWA-REQ-153
  explicitly permits for a MINOR. It does **not** reintroduce a
  "uid as an authority input" in the REQ-037 sense: `provisioned_uid` is an
  *integrity pin on the name resolution*, not the authority basis (the authority
  basis remains OS filesystem effective-write-access, evaluated live).

**C-1 is a refinement, not a blocker.** Pure-symbolic R1 is still *fail-closed
safe within the stated OS-account-DB TCB* (only root / the account administrator
can recreate accounts, and that party is trusted — HPAC-PAWA-REQ-018,
PAWA-INV-6); the hybrid simply removes a silent-rebind sharp edge and fixes an
internal contradiction. The R1 *direction* (protected record + live resolution)
is verified; the *identity granularity* is corrected from R1-PURE to **R1-HYBRID**.

### 7.8 account rename (prompt §20)

Same uid, new name. `getpwnam(old_name)` fails → `agent_principal_unknown` →
fail closed → deliberate reprovision by the deployment owner. There is **no
silent fallback to uid**. `.1R.30R.2A` §6 (`Account rename` row) states exactly
this. Under C-1 the hybrid additionally requires a matching `provisioned_uid`,
which does not weaken the rename outcome. **VERIFIED** (no early-stop condition —
rename semantics are unambiguous and fail closed).

### 7.9 OS account database trust (prompt §21)

Both `.1R.30R.2A` §6 and this IV state the OS account database (`pwd` / `grp` /
NSS) is **part of the OS TCB** (HPAC-PAWA-REQ-018: *"The OS filesystem
protection model … is part of the trusted computing base"*; PAWA-INV-6). R1
does **not** claim resistance to a hostile root altering the account database —
a hostile root is already outside the threat model (HPAC-PAWA-REQ-128,
HBDC-001 §18 inherited). No overclaim. **VERIFIED.**

### 7.10 installation binding (prompt §22)

R1 binds the exclusion record to `installation_id` (== the descriptor's) +
`protected_root_identity` `{device,inode}` (== live root + manifest) +
`generation`. A record copied from another installation carries a non-matching
`installation_id` / `{device,inode}` → reject (mirrors HPAC-PAWA-REQ-041 /
PAWA-INV-5). `.1R.30R.2A` §7.1 / §12.2. **VERIFIED.**

### 7.11 generation relationship + rollback (prompt §23 / §24) — **CORRECTION C-2**

`.1R.30R.2A` §7.1 / §9 / §12.2 offers **two alternatives** for binding the
exclusion record's currentness: (a) *"extend the `HPAC-PAWA-CURRENT-GENERATION/1.0`
anchor with an `agent_exclusion_digest` field"*; or (b) *"require the exclusion
record's `generation == current_generation`."*

Option (b) alone is **insufficient** to prevent an independent rollback: if a
future rotation advances the descriptor generation **without** re-writing the
exclusion record (a legitimate case — the agent account did not change), then
after the rotation `current_generation` moves ahead and a *stale* exclusion
record at the old generation would be rejected — but also a *legitimate current*
exclusion record must then be re-stamped every rotation, which the adjudication
does not require. Conversely, if the exclusion record shares the generation
integer, a superseded exclusion record from a *prior* installation state that
coincidentally carries the current integer is not distinguished by a bare
number.

**C-2 — the v1.1 freeze SHALL bind the exclusion record's `record_digest` into
the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor** (option (a), the
`agent_exclusion_digest` field), so the single monotonic atomic-replace anchor
record is authoritative for *both* the descriptor and the exclusion record.
Restoring an old `agent-exclusion.json` whose digest does not match the anchor's
`agent_exclusion_digest` → fail closed, exactly as a superseded descriptor is
rejected (HPAC-PAWA-REQ-051). This makes independent rollback of the exclusion
record **impossible** without also forging the protected, monotonic
current-generation anchor (which requires deployment-owner / root write — in the
TCB). Option (b) is **not** an acceptable substitute and the "or" in
`.1R.30R.2A` should be resolved to (a).

**C-2 is a refinement, not a blocker** — `.1R.30R.2A` already identifies the
correct mechanism (the current-generation anchor); it merely leaves the weaker
alternative on the table. No early-stop condition (the exclusion artifact
*cannot* be rolled back independently once C-2 is frozen; and even under the
adjudication's weaker option (b), a rollback still requires `.authority/` write
authority the agent lacks).

### 7.12 machine migration (prompt §25)

Fresh `installation_id` + fresh `{device,inode}` on the new host ⇒ the exclusion
record is re-provisioned deliberately alongside the descriptor; copying it alone
never validates (HPAC-PAWA-REQ-054/055, PAWA-INV-5). `.1R.30R.2A` §7.1 / §9.
**VERIFIED.**

### 7.13 bootstrap non-circularity (prompt §26)

Provisioning writes: the protected root, the manifest, `deployment-owner.json`
at generation 1, `current-generation.json` at 1, **and** `agent-exclusion.json`
— all filesystem primitives by the OS deployment owner. No `HPACWriterCapability`,
no FIDO2, no existing HPAC principal is consulted (PAWA-INV-4). Resolving the
name requires only a read of the OS account database. **Non-circular.**
`.1R.30R.2A` §7.1 / §9. **VERIFIED.**

### 7.14 currentness model (prompt §27)

Every §33 recognition requires: protected record present + canonical bytes +
digest OK + owned by the deployment owner + mode excludes group/other/agent
write + `installation_id` match + `{device,inode}` match + currentness bound to
the generation anchor (C-2) + `state == ACTIVE` + symbolic name resolves +
(C-1) live uid == `provisioned_uid` + live groups enumerated + resolved agent
`(uid, gids)` fails `_effective_write_access` / passes `_ancestor_chain_safe` +
the current process is **not** the agent account + single-account topology
absent. Any failure → the mapped `pawa_failure_code` → fail closed.
`.1R.30R.2A` §9 / §12.2. **VERIFIED** (with C-1 / C-2 folded in).

---

## 8. R2 / R3 / R4 — independently re-adjudicated

### 8.1 R2 — HBDC environment-lock binding — REJECTED (verified)

- HBDC-001 §13 (HBDC-REQ-025..039) scopes the environment lock to **Python
  execution-environment integrity**, not authority-principal identity. Making it
  authoritative for PAWA's exclusion predicate needs an **HBDC-001 amendment** —
  a second frozen contract evolving (and HBDC's own v1.1 / v1.2 amendments are
  *"PENDING INDEPENDENT VERIFICATION"*). Two contracts move instead of one.
- Violates **HPAC-PAWA-REQ-134**: *"HPAC-PAWA-001 has its **own** protected root
  and namespace … **no cross-subsystem bearer authority**."* PAWA's exclusion
  source belongs in PAWA's own `.authority/`.
- A bare `PCAE_AGENT_PRINCIPAL=<name>` from the mutable process environment must
  never be trust (prompt §14); R2 only satisfies this by putting the name in
  protected canonical state anyway — which R1 does more cleanly, in the right
  namespace.

R2 is **not materially safer or simpler** than R1. `.1R.30R.2A` §7.4.
**REJECTION VERIFIED.**

### 8.2 R3 — ship with no production mapping, fixture seam only — REJECTED (verified)

- `production_writer()` would always return `agent_principal_unknown` on a real
  root; tests inject `(uid, gids)` via a fixture seam.
- **Fail-closed safe but NOT production-complete.** HPAC-PAWA-001 §77 / §87 /
  §96 and RHAMP-REQ-156 name `.1R.30R.3` (its slice `.3.1`) *"**Production**
  Protected-Admin Writer Anchor … Implementation"*. R3 leaves the anchor
  **permanently production-unsatisfiable** ⇒ `.3.1` could only ever be a
  partial / non-production implementation and **cannot establish the production
  writer anchor N-16-5 requires**.
- **The blocker resurfaces at `.1R.30R.6`** (N-16-5 closure): RHAMP-REQ-152
  requires a real end-to-end `PRODUCTION` `AuthenticatedHumanPrincipal` ⇒ a real
  `PRODUCTION` `HPACWriterCapability` ⇒ a resolved configured-agent identity. The
  phase prompt (and this one, §29) is explicit: *"Do not defer an unavoidable
  blocker."*
- Would R3 make `.3.1` honestly *"PRODUCTION PAWA WRITER ANCHOR IMPLEMENTED"*?
  **No.** Safe `!=` complete.

The fixture seam is **retained** — under R1 it is still needed as the **test
strategy** (`.1R.30R.2A` §10; prompt §32). R3-as-the-resolution is
**REJECTED — VERIFIED.** (No early-stop condition: R3 does not satisfy
production-completeness, so it was not incorrectly rejected.)

### 8.3 R4 search — no superior source-supported option (verified)

Re-searched at V for a better existing protected principal mapping:

- **existing protected installation-principal record?** `DeploymentBinding` and
  the `HPAC-STORE-AUTHORITY/1.0` manifest name no OS principal — none.
- **derive the agent OS identity from protected-root installation metadata?**
  the manifest carries `{device,inode}` but no owner uid; adding one names the
  *deployment owner*, not the agent, and is a schema change to an
  actively-referenced frozen artifact — larger than a clean sibling record.
- **a canonical deployment manifest naming the excluded agent OS principal?**
  does not exist.
- **"any OS principal that is not the deployment owner and not root"?**
  underspecified / unsafe — a third host account is misclassified.
- **fold the account name into `deployment-owner.json`?** §14 froze it **closed**;
  HPAC-PAWA-REQ-037 forbids "no uid / gid integer as an authority input", and
  the contract's own design records the exclusion binding as *kind* + *basis*,
  signalling the id belongs elsewhere.
- **install / service-account config (`run_as`, systemd unit `User=`, launchd
  `UserName`)?** these are deployment-specific external facts, not canonical PCAE
  state, and are exactly the caller/environment-controlled inputs
  HPAC-PAWA-REQ-021 forbids as the resolution source. Not superior.

**No R4 superior to R1** (no early-stop condition — none is materially safer or
simpler). `.1R.30R.2A` §7.6. **VERIFIED.**

### 8.4 Comparative matrix (independently constructed)

| Property | R1-PURE (adjudicated) | **R1-HYBRID (this IV)** | R2 | R3 | R4 |
|---|---|---|---|---|---|
| canonical PCAE state | yes | yes | via HBDC (wrong namespace) | n/a | — |
| agent-unwritable | yes | yes | yes | n/a | — |
| PAWA-owned namespace | yes | yes | **no** (REQ-134) | n/a | — |
| detects live group drift | yes | yes | yes | n/a | — |
| detects UID reuse (by another name) | yes | yes | yes | n/a | — |
| detects recreation under a new uid | **no** (silent rebind) | **yes** (uid-pin mismatch) | no | n/a | — |
| account rename → fail closed | yes | yes | yes | n/a | — |
| independent rollback prevented | only with C-2 | **yes** (C-2) | needs its own | n/a | — |
| machine migration deliberate | yes | yes | yes | n/a | — |
| macOS + Linux portable | yes | yes | yes | n/a | — |
| contract clarity | §6-vs-§12.2 inconsistency | **consistent** | 2 contracts | leaves input unresolved | muddies frozen object |
| production-complete | yes | yes | yes | **no** | maybe |
| cross-subsystem coupling | none | none | **HBDC coupling** | none | manifest coupling |
| **selected** | direction only | **✔ SELECTED** | ✗ | ✗ (test strategy only) | ✗ |

---

## 9. New authority input — independently verified

- HPAC-PAWA-001 §14 froze `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` as a **closed**
  object and §12 enumerates the `.authority/` canonical members.
- §10's per-predicate identity matrix names the `configured-agent exclusion`
  authority source as *"canonical PCAE agent configuration / lock (§9)"* — a
  source §3 establishes **does not exist**.
- §9 / HPAC-PAWA-REQ-021 says the implementation *"SHALL name the exact canonical
  resolution source"* — but there is nothing to name; the resolution source must
  be **created**, and it is a **protected trust artifact a §33 recognition
  predicate consults**.
- HPAC-PAWA-REQ-001 forbids hiding a normative trust decision in code; §73 demands
  the source be named in traceability.

⇒ Introducing `HPAC-PAWA-AGENT-EXCLUSION/1.0` **changes the closed set of PAWA
security-critical authority inputs** — a **normative delta**, not implementation
detail. `.1R.30R.2A` §7.2. **VERIFIED.** (This is why option A — "leave it
implementation-defined" — is correctly rejected.)

---

## 10. Contract versioning — independently determined

### 10.1 MAJOR-trigger review (HPAC-PAWA-REQ-152, read at V)

| MAJOR trigger | R1-HYBRID? |
|---|---|
| making `sudo` / `euid` / an env var sufficient authority | **no** — authority basis stays OS filesystem effective-write-access, evaluated live |
| collapsing / removing the configured-agent exclusion | **no** — R1 *implements* it (strengthens a previously unresolvable input) |
| permitting a same-principal agent / deployment-owner topology | **no** — same-UID still fails closed (§7.14; PAWA-INV-7) |
| a remote / network / cloud authority service or transport | **no** — fully local; `pwd` / `grp` are local NSS reads |
| making the capability bearer / durable / serialisable / reusable | **no** — capability semantics untouched |
| broadening the capability into runtime approval / PB / RE / execution | **no** |
| **changing the bootstrap trust root away from OS filesystem write authority** | **no** — the exclusion record is provisioned by the deployment owner via filesystem write; resolution reads the OS account DB, already in the TCB; the trust root is unchanged |
| removing `generation` / rollback-prevention protection | **no** — C-2 *binds into* it |
| **adding a signing key / pinned key / keychain requirement as an authority input** | **no** — a symbolic name in a protected file + `pwd`/`grp`; no key, no signature, no secret |
| widening the authorized-consumer inventory by wildcard / prefix / glob | **no** |

**No MAJOR trigger fires.** `.1R.30R.2A` §7.3. **VERIFIED.**

### 10.2 MINOR fit (HPAC-PAWA-REQ-153)

REQ-153 permits a MINOR to *"re-state verified behaviour; add a `pawa_failure_code`
for a genuinely new terminal path without removing or re-meaning an existing
one …; add an authorized-consumer category by explicit enumeration; **tighten
(never loosen) a bound**; **clarify a platform-adapter detail**; or add an
additional macOS / Linux adapter within the frozen normative properties."*

- R1 adds **no** new `pawa_failure_code`: an unresolvable / mismatched account
  name maps to the existing **#3 `agent_principal_unknown`**; an agent that can
  write maps to existing **#4 `agent_has_protected_write_authority`**. The
  21-code taxonomy and the PAWA→RHAMP `#1 / #2 / #40 / #41` map (§57) are
  **unchanged** — independently confirmed against the §56 / §57 tables.
- R1 **tightens** the §26 predicate from "unresolvable (no source exists)" to
  "resolved against a protected, generation-bound record" — a strict tightening.
- The `pwd` / `grp` resolution is a **platform-adapter detail** within the frozen
  normative property (§63 / REQ-132).
- **Direct precedent:** HPAC-001 v2.1 was itself a MINOR that *"adds one closed
  binding object … widens no authority … possession or reconstruction grants
  nothing."* R1 is structurally the same move — one closed protected artifact,
  bound to existing anchors, widening no authority.

**Soft point (surfaced, non-blocking):** REQ-153's enumerated MINOR-permits list
does **not** literally include the phrase *"add a new protected
recognition-input artifact with a closed schema."* The MINOR classification
therefore rests on **(a)** no MAJOR trigger firing and **(b)** the HPAC-001 v2.1
precedent — a sound but *derived* argument rather than a verbatim contract
permission.

**S-1 — the `.1R.30R.2A.2` v1.1 freeze SHOULD add an explicit versioning-rule
line** recording that "adding a closed, generation-bound protected
recognition-input artifact that resolves — but does not widen — an authority
input the frozen contract already requires" is a **MINOR**, so future readers do
not have to re-derive this from the absence of a MAJOR trigger. (`.1R.30R.2A`
§7.3 makes the argument but does not propose codifying it.)

### 10.3 HPAC-001 / RHAMP-001 impact

- **HPAC-001 v2.1** — no core human-principal semantic change; HPAC-001 §7
  deferred the *mechanism* and HPAC-PAWA-001 is its companion. R1 lives entirely
  inside HPAC-PAWA-001's namespace. **Byte-unchanged — VERIFIED.**
- **RHAMP-001 v1.0** — RHAMP-REQ-047 externalises the anchor (*"This is the trust
  anchor; it terminates bootstrap"*) and does not specify the configured-agent
  resolution mechanism; the PAWA→RHAMP §49 map (#1 `bootstrap_authority_unproven`,
  #2 `enrollment_not_protected_admin`, #40, #41) already covers
  `agent_principal_unknown` and `agent_has_protected_write_authority`.
  **Byte-unchanged — VERIFIED.**
- **HBDC-001 v1.2** — precedent only; R1 does **not** amend it (that is precisely
  why R2 was rejected). **Byte-unchanged — VERIFIED.**

### 10.4 Versioning verdict

**B — HPAC-PAWA-001 v1.1 MINOR REQUIRED.** Not A (a new protected recognition
input is normative — §9). Not C (no MAJOR trigger — §10.1). Not D (no other
contract need evolve under R1 — §10.3). Not E (a production-safe,
source-supported, additive resolution exists — R1-HYBRID). `.1R.30R.2A` §12.1.
**VERIFIED.**

---

## 11. Atomicity — independently verified

HPAC-PAWA-001 §33 / HPAC-PAWA-REQ-074 lists, in the **single frozen recognition
sequence**: step 2 (resolve the configured agent principal), step 3
(configured-agent exclusion + safe ancestors), step 6 (current-generation
check), step 7 (not-configured-agent current context), step 8 (positive write
probe), step 10 (mint). HPAC-PAWA-REQ-075: *"The sequence SHALL run fresh on
**every** `production_writer(...)` call. No result is cached across calls."*
PAWA-INV-3: correct path + valid structure is never a trusted descriptor —
"configured-agent exclusion + positive write probe + not-configured-agent
context are all additionally required."

⇒ configured-agent resolution (incl. C-1's uid pin and C-2's generation-anchor
check on the exclusion record) is **inside atomic unit A1** of `.1R.30R.3.1`,
alongside descriptor / current-generation / write-probe / mint. It **cannot** be
split such that a `PRODUCTION` capability exists without the resolution having
run. `.1R.30R.2A` §12.3. **VERIFIED.** (No early-stop condition — the source is
atomic with §33.)

---

## 12. D1 phase decomposition — independently verified against CPIPC-001 §4

CPIPC-001 v1.0 §4 (CPIPC-REQ-009), read at V — the frozen EBNF:

```
phase-id        = series , branch , { "." , subphase-segment } ;
subphase-segment = numeric-segment | letter-segment ;
numeric-segment = digit , { digit } , [ letter , { letter } ] ;
letter-segment  = letter , { letter } ;
```

For `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1`:

| Segment | Production | Precedent |
|---|---|---|
| `30R` | `numeric-segment` (`30` + `R`) | the `.1R` repair-letter idiom throughout this chain |
| `2A` | `numeric-segment` (`2` + `A`) | `.1R.2A` / `.2B` / `.2C` (CPIPC §9 confirmed-forms set) |
| `2A.1`, `2A.2` | dotted `numeric-segment` children of `2A` | `.1R.5.2.1` (dotted numeric children) |
| `2A.3` (recommended, §14) | dotted `numeric-segment` child | same |

`2A` is digits-then-letters (valid); `2A.1` is a child segment (valid). No
segment mixes letters-then-digits. `.1R.30R.2A` is a **distinct identity** from
`.1R.30` and from `.1R.30R` (different `comparison_identity` tuples). Historical
`.1R.30` is not reused, resumed, or relabelled — PAWA-INV-11 upheld. The
`.2A` / `.2A.1` / `.2A.2` chain and the `.3.1 … .3.6` / `.4` / `.5` / `.6`
downstream are grammar-valid and collide with nothing in HPAC-PAWA-001 §78.

**D1 DECOMPOSITION: VALID — VERIFIED.** `.1R.30R.2A` §12.4 / §14. (No early-stop
condition — CPIPC-001 permits the proposed decomposition.)

---

## 13. Contract-freeze successor + contract-freeze IV — independently assessed

### 13.1 `.1R.30R.2A.2` is the correct contract-freeze successor — VERIFIED

The adjudication selects a **production trust input** and mandates a **contract
version bump**. It is not a trivial implementation detail — it changes the
closed authority-input set of a frozen contract (§9). Precedent:
`.1R.30R` adjudication → `.1R.30R.1` dedicated IV → `.1R.30R.2` dedicated
contract freeze. Symmetry ⇒ `.1R.30R.2A` adjudication → `.1R.30R.2A.1` dedicated
IV (this phase) → `.1R.30R.2A.2` dedicated contract freeze. A fold-in of the
contract change into `.1R.30R.3.1` is **not** justified. `.1R.30R.2A` §12.6.
**VERIFIED.**

### 13.2 Contract-freeze IV (prompt §47) — **CORRECTION C-3**

`.1R.30R.2A` §12.6 says the v1.1 contract-freeze IV *"MAY fold into
`.1R.30R.3.2`"* (the Slice-1 IV), citing the `.1R.29 → folded-IV` precedent.

**C-3 — a dedicated `.1R.30R.2A.3` contract IV is the safer default and SHOULD
be recommended,** with folding into `.1R.30R.3.2` acceptable only at the
authorizing operator's explicit discretion. Reasoning:

- `HPAC-PAWA-AGENT-EXCLUSION/1.0` is a **new protected authority-input
  artifact** — a production trust input, not a prose restatement. The
  `.1R.29 → .1R.31` precedent it cites was a companion-contract freeze whose IV
  folded into the *implementation* IV; but here the parallel structure
  (`.1R.30R` adjudication got `.1R.30R.1`; `.1R.30R.2` freeze's IV *was itself*
  deferrable into `.1R.30R.4`) actually cuts **toward** a dedicated IV: every
  prior link in this exact chain that introduced a normative artifact received
  its own IV phase.
- `.1R.30R.2A` itself concluded (§12.5) that this adjudication *"is not a trivial
  implementation detail … a fold-in is not justified"* for the **adjudication**
  IV — the same logic applies to the **contract-freeze** IV of the artifact the
  adjudication produces.

**C-3 is a recommendation, not a blocker.** Folding remains structurally
permissible (HPAC-PAWA-001 §18 / §94 explicitly allow a folded contract-freeze
IV); this IV simply records that the dedicated form is preferable for a new
protected authority input and should be the stated default.

---

## 14. Findings

All three are **non-blocking refinements** for the `.1R.30R.2A.2` contract
freeze (and, where noted, `.1R.30R.3.1` implementation). None reaches an
early-stop / BLOCKED condition.

| ID | Finding | Disposition |
|---|---|---|
| **C-1** | Adopt **R1-HYBRID** (symbolic account name **+** `provisioned_uid`, with a live `getpwnam(name).pw_uid == provisioned_uid` equality check; groups still resolved live). Closes the account deletion → recreation-under-new-uid silent-rebind path and resolves `.1R.30R.2A`'s §6-vs-§12.2 internal inconsistency ("bound expectation" vs. "no uid integer"). Additive one field; MINOR (tightens a bound, REQ-153); does **not** make uid the authority basis (effective-write-access remains the basis, evaluated live). | → `.1R.30R.2A.2` schema; `.1R.30R.3.1` resolution logic + a `test_recreated_account_new_uid_mismatch_fails_closed` case |
| **C-2** | The exclusion record's currentness **SHALL** bind into the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor via an `agent_exclusion_digest` field — resolve `.1R.30R.2A`'s "extend the anchor **or** require `generation ==`" to the anchor-digest option. A bare generation-integer equality does not make independent rollback impossible; the anchor-digest binding does. | → `.1R.30R.2A.2` freezes `HPAC-PAWA-CURRENT-GENERATION/1.0` v1.1 with `agent_exclusion_digest`; `.1R.30R.3.1` rollback test |
| **C-3** | Recommend a **dedicated `.1R.30R.2A.3` contract IV** of HPAC-PAWA-001 v1.1 as the default (folding into `.1R.30R.3.2` only at explicit operator discretion), because the artifact is a new protected authority input, matching every prior link in this chain. | → operator decision at `.1R.30R.2A.2` authorization; disclosed, NOT authorized |
| **S-1** | The `.1R.30R.2A.2` freeze SHOULD add an explicit **versioning-rule line** stating that adding a closed, generation-bound protected recognition-input artifact that resolves (not widens) an already-required authority input is a MINOR — so the classification is verbatim, not re-derived from the absence of a MAJOR trigger. | → `.1R.30R.2A.2` §80-adjacent text |

---

## 15. Verdicts

### 15.1 Final verification verdict

**ADJUDICATION VERIFIED WITH CORRECTIONS.** Every load-bearing `.1R.30R.2A`
conclusion is independently re-derived and holds: the F-1 gap is real and
correctly stated; no existing canonical mapping was overlooked; the three F-1
predicates are distinct; R1's *direction* (protected record + live resolution)
is sound; R2 / R3 / R4 are correctly rejected; the change is a normative delta;
the version bump is **MINOR** with no MAJOR trigger; HPAC-001 v2.1 and RHAMP-001
v1.0 need no change; the resolution is atomic with §33; the D1 decomposition is
CPIPC-001-valid; `.1R.30R.2A.2` is the right contract-freeze successor. Three
additive corrections (C-1 hybrid identity, C-2 anchor-digest rollback binding,
C-3 dedicated contract IV) and one soft point (S-1) refine — but do not
overturn — the adjudication.

### 15.2 Selected identity model verdict

**R1-HYBRID** — a protected, deployment-owner-provisioned, agent-unwritable,
installation- and generation-bound `HPAC-PAWA-AGENT-EXCLUSION/1.0` record storing
the **symbolic OS account name** **and** the **`provisioned_uid`**; at every §33
recognition, `pwd.getpwnam(name).pw_uid` MUST equal `provisioned_uid` (else
`agent_principal_unknown`), the account's **current** primary + supplementary
groups are enumerated live, and the resolved `(uid, gids)` is fed to
`_effective_write_access` / `_ancestor_chain_safe`; the record's digest is bound
into the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor.

### 15.3 Contract verdict

**HPAC-PAWA-001 v1.1 — MINOR — REQUIRED.** No new `pawa_failure_code`. No
descriptor schema change. `HPAC-PAWA-CURRENT-GENERATION/1.0` gains one field
(`agent_exclusion_digest`). HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2
byte-unchanged. HPAC-PAWA-001 v1.0 is **not** rewritten — v1.1 is append-only.

### 15.4 Atomicity / D1 / chain

Atomicity **CONFIRMED**. D1 decomposition **VALID** (CPIPC-001 §4). `.2A` /
`.2A.1` / `.2A.2` (`+` recommended `.2A.3`) chain **grammar-valid**; historical
`.1R.30` preserved immutable BLOCKED (PAWA-INV-11).

---

## 16. Boundaries held

- `git diff 1dbd41cb HEAD -- src/pcae` → **empty**.
- `git diff 1dbd41cb HEAD -- docs/contracts` → **empty** (HPAC-PAWA-001 v1.0,
  HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, CPIPC-001 v1.0 all
  byte-unchanged).
- No HPAC-PAWA-001 v1.1 authored. No `agent-exclusion.json` schema helper, no
  `resolve_configured_agent_identity()`, no writer-anchor implementation, no
  provisioning script.
- No FIDO2 / CTAP / WebAuthn code; no `_ELIGIBLE_MECHANISM_IDS` change; no
  `verifier_kind` addition; no sidecar / counter-state store; no enrollment /
  bootstrap tool; no protected presentation helper; no approval proof; no
  `PRODUCTION` `AuthenticatedHumanPrincipal`; no `require_real_assurance` wiring.
- No hardware accessed, enumerated, or prompted; no CTAP device I/O.
- No guard reconciled (no `src/pcae` change → no point-in-time scope fence
  tripped). One new read-only IV test file; no existing test modified, renamed,
  removed, skipped, or xfailed.
- Historical `.1R.30` (immutable BLOCKED), `.1R.30R`, `.1R.30R.1`, `.1R.30R.2`,
  `.1R.30R.2A` records **byte-unchanged**.
- **N-16-5:** NOT CLOSED — adjudication VERIFIED WITH CORRECTIONS; contract
  freeze pending; implementation not begun.
  **N-16-3 / N-16-4:** CLOSED. **N-16-6 / N-16-7:** OPEN, untouched, N-16-7
  strictly last. **N-23-1 / N-23-2:** carried unchanged. **No Slice C.**
- **Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins / 0 capabilities — byte-unchanged.
- **First external effect:** ABSENT AND UNREACHABLE. No `adapter.dispatch(`
  path added; the only such call site remains the deterministic simulation
  harness in `runtime_adapter.py`. No subprocess / Popen / os.system / socket /
  http / provider path introduced. No execution enabled.
- Governed `pcae` lifecycle only — no raw `git commit` / `git push`, no
  `--no-verify`, no force push, no history rewrite, no hook bypass. Only the
  primary human-authorized operator holds `.1R.30R.2A.1` lifecycle authority.
  `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 17. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2` — HPAC-PAWA-001 v1.1 Configured-Agent-Principal
Resolution Source Contract Freeze** (ID recommended, NOT reserved; requires its
own separate explicit human authorization). Contract-only: no `src/pcae`, no
HPAC-001 bump, RHAMP-001 v1.0 byte-unchanged. It SHALL append to HPAC-PAWA-001 a
`HPAC-PAWA-AGENT-EXCLUSION/1.0` section and the resolution-source naming in
§9 / §10, incorporating **C-1** (hybrid `symbolic_account` + `provisioned_uid`,
live equality check, live groups), **C-2** (`agent_exclusion_digest` bound into
`HPAC-PAWA-CURRENT-GENERATION/1.0`), and **S-1** (explicit MINOR versioning-rule
line). **No new `pawa_failure_code`. No descriptor schema change.** Then, at the
authorizing operator's discretion, **`.1R.30R.2A.3`** (dedicated HPAC-PAWA-001
v1.1 contract IV — **C-3**; disclosed, NOT authorized) or a fold of that IV into
`.1R.30R.3.2`; then `.1R.30R.3.1` (Slice 1 — PAWA production writer anchor +
`hpac_pawa_agent_exclusion.py` + `resolve_configured_agent_identity()`) →
`.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4` (Slice 2 / IV) → `.1R.30R.3.5` /
`.3.6` (Slice 3 / IV) → `.1R.30R.4` (composite IV) → `.1R.30R.5` (protected
presentation + `require_real_assurance` wiring) → `.1R.30R.6` (IV + mandatory
real-CTAP2-hardware verification + N-16-5 closure) → N-16-6 → N-16-7 (strictly
last). **Do not begin N-16-6 / N-16-7 / Slice C; do not implement or call the
first external effect; do not enable execution.**

---

## 18. Verdict block

```
IV OF THE CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE ADJUDICATION (.1R.30R.2A.1)

FINAL VERDICT            ADJUDICATION VERIFIED WITH CORRECTIONS — NOT BLOCKED

F-1 GAP                  CONFIRMED — independently reproduced from HPAC-PAWA-001
                        §9/§10/§26/§31/§33 + hpac_foundation._validate_production_boundary
                        (live _current_agent_identity == os.geteuid()); agent_id
                        registry / lock non-authorizing; no getpwnam/PCAE_AGENT_PRINCIPAL
                        bridge; no production_writer mint path
THREE PREDICATES        DISTINCT — VERIFIED (§10 matrix; none substitutable)
EXISTING MAPPING        NONE — no canonical logical-agent → OS-(uid,gids) binding
                        overlooked
SELECTED MODEL          R1-HYBRID — protected symbolic account name + provisioned_uid,
                        live getpwnam equality + live group enumeration, digest
                        bound into the current-generation anchor
                        (.1R.30R.2A selected R1-PURE; corrected here — C-1)
GROUP DRIFT             detected (live groups) — VERIFIED
GROUP REMOVAL           reflected live; no reprovision required for a strengthening
                        change — VERIFIED
UID REUSE (other name)  fail closed (getpwnam fails) — VERIFIED
DELETE / RECREATE       R1-PURE silently rebinds under a new uid; R1-HYBRID
                        fails closed on the uid-pin mismatch — CORRECTION C-1
ACCOUNT RENAME          fail closed (lookup failure) — VERIFIED
OS ACCOUNT DB           OS TCB — no overclaim — VERIFIED
INSTALLATION BINDING    installation_id + {device,inode} + generation — VERIFIED
ROLLBACK                bind exclusion-record digest into HPAC-PAWA-CURRENT-
                        GENERATION/1.0 (agent_exclusion_digest); bare generation-
                        integer equality is insufficient — CORRECTION C-2
MIGRATION               deliberate reprovision; copy alone never validates — VERIFIED
BOOTSTRAP               non-circular (no capability, no FIDO2, no prior principal) — VERIFIED
R2                      REJECTED — needs an HBDC-001 amendment; wrong namespace
                        (REQ-134) — VERIFIED
R3                      REJECTED as the resolution — permanently non-production;
                        defers an unavoidable blocker to .1R.30R.6 — VERIFIED;
                        retained only as the test-seam strategy
R4                      none superior — VERIFIED
NEW AUTHORITY INPUT     YES — normative delta, not hidden in code — VERIFIED
CONTRACT VERDICT        B — HPAC-PAWA-001 v1.1 MINOR REQUIRED — VERIFIED
                        (no REQ-152 MAJOR trigger; additive/authority-preserving;
                        no new pawa_failure_code; no descriptor schema change;
                        HPAC-CURRENT-GENERATION/1.0 gains one field — C-2)
                        SOFT POINT S-1: codify the MINOR rule explicitly in v1.1
HPAC-001 / RHAMP-001    byte-unchanged — VERIFIED
ATOMICITY               CONFIRMED — inside §33 atomic unit A1
D1 DECOMPOSITION        VALID — CPIPC-001 §4; .2A/.2A.1/.2A.2 grammar-valid;
                        historical .1R.30 immutable BLOCKED (PAWA-INV-11)
CONTRACT-FREEZE PHASE   .1R.30R.2A.2 — VERIFIED
CONTRACT-FREEZE IV      recommend a dedicated .1R.30R.2A.3 (fold into .3.2 only
                        at operator discretion) — CORRECTION C-3
NO src/pcae CHANGE      git diff 1dbd41cb HEAD -- src/pcae : empty
NO CONTRACT CHANGE      git diff 1dbd41cb HEAD -- docs/contracts : empty
RUNTIME                 not_implemented / Observed / observe / unavailable ; 0/0
FIRST EXTERNAL EFFECT   ABSENT AND UNREACHABLE
N-16-5                  NOT CLOSED
N-16-6 / N-16-7         OPEN, untouched, N-16-7 strictly last ; NO Slice C

RECOMMENDED NEXT PHASE  149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2 — HPAC-PAWA-001 v1.1
                        Configured-Agent-Principal Resolution Source Contract
                        Freeze (incorporating C-1 / C-2 / S-1; then C-3's
                        .1R.30R.2A.3 dedicated contract IV, or a folded IV at
                        operator discretion). Own explicit human authorization
                        required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```
