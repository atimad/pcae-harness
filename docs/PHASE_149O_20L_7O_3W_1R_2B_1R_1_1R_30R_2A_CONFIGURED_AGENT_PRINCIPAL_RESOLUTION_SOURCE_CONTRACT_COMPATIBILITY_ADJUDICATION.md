# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A — Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication

**Status: COMPLETE — ADJUDICATED.** Verdict: **B — HPAC-PAWA-001 v1.1 MINOR required.**
Analysis only. No `src/pcae` change; no normative-contract change; no implementation.
HPAC-PAWA-001 v1.0 is **not edited** by this phase — v1.1 is a separate, later,
append-only contract-freeze phase.

**Phase-entry SHA (A):** `5b45aa7b444f15852c51985879570b8913fedbe4`
(`Phase …1R.30R.2: reconcile governed push state in HPAC-PAWA-001 completion metadata`).

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 1. Why this phase exists

Full primary-source reconstruction for the planned PAWA implementation
(`.1R.30R.3.1`, the writer-anchor slice) discovered that HPAC-PAWA-001 v1.0
requires the production `production_writer` recognition sequence (§33) to evaluate
protected-root write authority **held by the CONFIGURED PCAE agent principal**
(HPAC-PAWA-REQ-021 / 022 / 026 / 061 / 062 / 063; finding F-1 of `.1R.30R.1` §11.1)
— explicitly **not** `os.geteuid()` of the invoking process — while current
production code has **no canonical bridge** from PCAE's configured logical agent
identity (`claude-local`, …) to an enforceable OS principal identity `(uid, gids)`.

This phase resolves that trust-source gap **before** any PAWA production
implementation begins.

---

## 2. Exact discovered gap — independently CONFIRMED

The reconstruction claim was independently re-derived from source, not accepted
from prior prose.

**HPAC-PAWA-001 v1.0 requires** (read in full at A):
- **§9 / HPAC-PAWA-REQ-021.** "The configured agent principal SHALL be resolved
  from **canonical PCAE agent configuration / lock semantics**, never from caller
  input, an environment variable, a CLI flag, `--agent-id`, repository state, or
  the live `os.geteuid()` of the running process. … the implementation SHALL name
  the exact canonical resolution source in its `.1R.30R.3` contract-production
  traceability (§73)."
- **§9 / HPAC-PAWA-REQ-022.** Identity form: "a `(uid, gids)` pair on POSIX … resolved
  from the configured principal, **not** the invoking process's live ids."
- **§10 / HPAC-PAWA-REQ-026** (per-predicate identity matrix, finding F-1): the
  `configured-agent exclusion` predicate's **Authority source** column reads
  *"canonical PCAE agent configuration / lock (§9)"*.
- **§26 / HPAC-PAWA-REQ-061.** `_effective_write_access(root, configured_agent_uid,
  configured_agent_gids)` returns `False` **and** `_ancestor_chain_safe(root,
  configured_agent_uid, configured_agent_gids)` returns `True`.
- **§9 / HPAC-PAWA-REQ-023.** "If the configured agent principal is unavailable,
  ambiguous, or cannot be mapped to an OS principal where the check needs one, the
  recognition SHALL **fail closed** (`agent_principal_unknown`, §56). It SHALL NOT
  default to `os.geteuid()`, to 'no agent', or to a permissive outcome."

**Current production code provides** (each read in full at A):

| Source | What it stores / returns | OS identity? | Configured (vs. live)? |
|---|---|---|---|
| `policy.py` `DEFAULT_AGENT_REGISTRY` / `agent.py` `KNOWN_AGENTS` | `agent_id` string + `kind` + `roles`/`capabilities` | **no** | logical only |
| `.pcae/agent-lock.json` (`agent.py` `AgentLock`, `build_agent_lock_data`) | `agent_id`, `acquired_at`, `git_branch`, `active_task` | **no** | logical only; `agent.py` comment: *"agent_id is descriptive only … non-authenticating, non-authorizing"* |
| `hatp_class_b_topology_verifier._current_agent_identity()` | `(os.geteuid(), frozenset(os.getgroups()) \| {os.getegid()})` | yes | **live invoking process** — NOT configured |
| `hatp_bootstrap.inspect_bootstrap_environment` | compares `os.getuid()` (live) vs. store `st_uid`; **persists nothing** | yes | live; ephemeral |
| `hatp_environment_lock_verifier._check_*` | takes `agent_uid, agent_gids` **as parameters** — supplied from `_current_agent_identity()` at call sites | yes | **live** |
| `DeploymentBinding` / HATP `manifest.json` (`hatp_bootstrap`, `hatp_deployment_binding_admin`) | `repository_id`, `canonical_deployment_root`, HATP/HPAC `principal_id` (opaque), `{device,inode}` `root_identity`, `store_id` | **no OS uid** | — |
| `HPAC-STORE-AUTHORITY/1.0` manifest (`hpac_foundation`) | `schema_version`, `store_id`, `authority_class`, `root_identity` `{device,inode}` | **no OS uid** | — |
| provenance (`provenance.py`, `derive_producer_provenance`) | logical `producer_component` constant | **no** | HPAC-REQ-007 forbids deriving `principal_id` from it |

**Exhaustive absence search** (commands run at A, all empty of a bridge):
```
grep -rn "getpwnam|getpwuid|getgrnam|getgrgid|getgrouplist" src/pcae --include=*.py | grep -v test
  → only hatp_class_b_topology_verifier.py:323/328 — resolve an ACL-entry NAME
    against the ALREADY-KNOWN live agent_uid/agent_gids; NOT a configured-agent source
grep -rn "PCAE_AGENT_PRINCIPAL|AGENT_PRINCIPAL|agent_os_principal|configured_agent" src/pcae --include=*.py | grep -v test
  → 0 matches
grep -rn "HPACAuthorityClass.PRODUCTION|production_writer|ProductionWriter|deployment.owner" src/pcae --include=*.py | grep -v test
  → no PRODUCTION HPACWriterCapability mint path; no consumable deployment-owner object
```

**`HBDC-001 v1.2 §13` (environment lock)** was read: HBDC-REQ-025..039 scope it to
the **Python execution environment** (interpreter, venv, `PYTHONPATH`, user-site,
import hooks). It defines **no stored agent-principal OS-identity record**. The
term `PCAE_AGENT_PRINCIPAL` (HBDC-001 terminology, `149O.1B.1 §4`) is a
**conceptual role name**, not an implemented resolution mechanism.

**Conclusion:** the F-1 gap is **CONFIRMED**. There is no canonical, non-caller,
agent-unwritable, repository-independent source anywhere in `src/pcae` that binds
the configured PCAE agent principal to an OS `(uid, gids)` suitable for
protected-root authorization evaluation. Every existing OS-identity resolution in
the HBDC/HPAC production-boundary apparatus evaluates against the **live invoking
process**, never a configured identity.

---

## 3. F-1 requirement — re-derived (prompt §5)

| Predicate | Subject identity evaluated | Authority basis | Same as the other? |
|---|---|---|---|
| **`agent_has_protected_write_authority`** (§26, HPAC-PAWA-REQ-061/063) | the **configured PCAE agent principal** — a *stored/configured* identity, resolved to `(uid, gids)` | proof the agent *would* be unable to write `<HPAC_PROTECTED_ROOT>` + safe ancestors (`_effective_write_access == False` ∧ `_ancestor_chain_safe == True`) | **NO** |
| **`current_context_is_agent`** (§31, HPAC-PAWA-REQ-071) | the **current invoking OS process** compared against the configured agent principal | negative assertion that this call is *not being made as* the configured agent principal | **NO** |
| **positive write probe** (§28, HPAC-PAWA-REQ-065/066) | the **current invoking OS process** | an `O_EXCL\|O_NOFOLLOW` create-and-unlink operation under `.authority/` — an operation, not a claim | (uses live identity, legitimately) |

**These are three distinct predicates and SHALL NOT be collapsed.** Both #1 and #2
require *"the configured agent principal"* as their reference identity; #2 and the
probe additionally read the live process. Finding F-1's split is: the **probe**
keys off the live invoking process (correct — `os.geteuid()` is fine there); the
**negative boundary (§26)** and the **not-agent-context check (§31)** key off the
**configured agent principal** — the identity this phase must find a source for.

---

## 4. `_current_agent_identity()` semantics (prompt §6)

`hatp_class_b_topology_verifier.py:143-155`:
```python
def _current_agent_identity() -> "tuple[int, frozenset[int]]":
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}
```
- **Means:** the **live invoking process** identity (effective uid + effective +
  supplementary groups). Docstring confirms: *"Live process identity — never a
  caller-supplied value."*
- **Historical use:** every HBDC Class-B conformance check, the
  `hatp_environment_lock_verifier`, and `hpac_foundation._validate_production_boundary`
  — all answer *"can the **current process** write X"*.
- **Reusing it for PAWA §26 VIOLATES F-1.** On a compliant two-principal
  deployment the writer tool runs **as the deployment owner** (admin uid), so
  `os.geteuid()` is the admin uid, and `_effective_write_access(root, admin_uid, …)`
  returns **`True`** → `_validate_production_boundary` **raises for a legitimate
  admin invocation**. It answers *"can the admin write"*, not *"can the agent
  write"* — the wrong question (`.1R.30R.1` §11.1).
- **Correct future PAWA use:** `_current_agent_identity()` is the identity of the
  **positive write probe (§28)** and one operand of the **`current_context_is_agent`
  comparison (§31)** — never the `agent_has_protected_write_authority` operand.

---

## 5. Existing-canonical-mapping search (prompt §7) — result: NONE

No existing PCAE source stores or binds a uid / username / supplementary groups /
OS account identity / installation principal identity to a configured agent ID.
Exact absence recorded in §2. The nearest constructs and why each fails:

- **Agent registry / lock** — logical strings only; explicitly non-authorizing.
- **`_current_agent_identity()`** — live process, not configured (F-1).
- **`DeploymentBinding` / HATP trust store** — names an HPAC/HATP *principal_id*
  (opaque, not an OS principal) and a deployment root; no OS uid.
- **`HPAC-STORE-AUTHORITY/1.0` manifest** — `{device,inode}` root identity + a
  `store_id`; no owner uid, and its owner is the *deployment owner*, not the agent.
- **HBDC environment lock** — interpreter/venv/path integrity; no agent-uid record.
- **`hatp_bootstrap.inspect_bootstrap_environment`** — a live, ephemeral
  same-account check; persists nothing.

---

## 6. uid vs. `(uid, gids)`; currentness; UID reuse; group drift; rename (prompt §8, §9, §21–§23)

`_effective_write_access(path, uid, gids)` (`hatp_class_b_topology_verifier.py:487`)
tests owner-write (`st_uid == uid`), **group-write (`st_gid in gids`)**, other-write,
plus a platform ACL sub-check. **A uid alone is insufficient** — PAWA needs
`(uid, gids)`, and the gids set must reflect the agent account's **current**
group membership.

| Threat | If a **static `(uid, gids)` snapshot** is persisted | If a **symbolic account name** is persisted + resolved **live** |
|---|---|---|
| **Group drift** — agent added to a root-writable group after provisioning | **UNSAFE** — snapshot is stale; PAWA would not detect the new write path | **SAFE** — live enumeration of the account's current groups sees it → `agent_has_protected_write_authority` fires |
| **UID reuse** — agent account deleted, uid reassigned to another account | **UNSAFE** — persisted uid silently identifies the wrong principal | **SAFE(er)** — name no longer resolves, or resolves to a different uid than any bound expectation → `agent_principal_unknown` (fail closed) |
| **Account rename** — same uid, new name | n/a | name lookup fails → fail closed → deliberate re-provision (consistent with PAWA "migration is always a deliberate act", §22) |
| **Restored stale record** | caught only if bound to the generation anchor | caught by the generation anchor (§20/§21) |

**Adjudicated identity model:** the canonical source stores the **symbolic OS
account name** of the configured agent principal (plus installation / root-identity
/ generation / provenance binding), and resolves `(uid, gids)` **live** at every
§33 recognition (`pwd.getpwnam(name).pw_uid`; supplementary + primary groups via
the platform group database). This is the only model that detects group drift and
UID reuse. Trust rests on the **protected record** (agent-unwritable, canonical
bytes, root-identity-bound) **plus the OS account database** — which is already
inside the TCB (HPAC-PAWA-REQ-018: "The OS filesystem protection model … is part
of the trusted computing base"). It is portable: `pwd` / `grp` exist on macOS and
Linux (HPAC-PAWA-REQ-132 freezes normative properties, not command syntax).

---

## 7. Option assessments

### 7.1 R1 — dedicated protected exclusion record (prompt §10–§12)

`<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`, closed schema
**`HPAC-PAWA-AGENT-EXCLUSION/1.0`**, fields (proposed for the v1.1 freeze;
final wording is `.1R.30R.2A.2`'s):
`artifact_schema_version` (const), `record_digest` (self-excluding SHA-256),
`configured_agent_account` (symbolic OS account name; grammar-bounded; **no uid
integer**), `installation_id` (== the descriptor's), `protected_root_identity`
(`{device,inode}`, == live root + manifest), `generation` (== the descriptor
generation it was provisioned alongside), `created_at` (trusted clock),
`provenance_ref` (`HPAC-WRITER-PROVENANCE/1.0` key), `state`
(`{ACTIVE, SUPERSEDED, REVOKED}`).

| Dimension | Assessment |
|---|---|
| Provisioned by | `scripts/hpac_protected_root_admin.py` (`provision` writes it alongside `deployment-owner.json`; a `set-agent-exclusion` subcommand rotates it) — out-of-band, by the deployment owner, create-only per generation |
| Who can mutate | only a party with filesystem write to `.authority/` — i.e. the deployment owner (or root, in the TCB) |
| Agent-writable? | no — `.authority/` mode `0700`, deployment-owner-owned; enforced exactly as the descriptor is (§12, §17) |
| Bootstrap | **non-circular** — filesystem write + a read of the OS account database; no `HPACWriterCapability`, no FIDO2, no existing HPAC principal (PAWA-INV-4 preserved) |
| Group currentness | record stores the **name**; `(uid,gids)` resolved live → group drift detected (§6) |
| Rollback | bound to `installation_id` + `{device,inode}` + `generation`; the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor (extended with an `agent_exclusion_digest` field, or by requiring the exclusion record's `generation == current_generation`) rejects a restored superseded record exactly as §21 rejects a restored superseded descriptor |
| Host migration | fresh `installation_id` + fresh `{device,inode}` ⇒ re-provisioned like the descriptor; copying it alone never validates (PAWA-INV-5) |
| macOS / Linux | `pwd`/`grp` on both; normative property frozen, adapter per-OS (§63) |
| Descriptor relationship | **separate record, transitively bound** by shared `installation_id` + generation; the descriptor's frozen `configured_agent_exclusion_binding` keeps recording *kind* + *basis* only (**unchanged**); the account name lives in this sibling record. Descriptor schema is **not touched** |

### 7.2 R1 authority-input question (prompt §11) — DECISIVE

**Does adding `HPAC-PAWA-AGENT-EXCLUSION/1.0` change the closed set of PAWA
security-critical authority inputs? — YES.**

- §14 froze `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` as a **closed** object and §12
  enumerates the `.authority/` canonical members (`manifest.json`,
  `provenance/<key>.json`, `deployment-owner.json`).
- §10's per-predicate identity matrix names the `configured-agent exclusion`
  authority source as *"canonical PCAE agent configuration / lock (§9)"* — a source
  that, as §2 establishes, **does not exist**.
- Introducing a **new protected trust artifact that a §33 recognition predicate
  consults** is a **new recognition input**. HPAC-PAWA-REQ-001 forbids hiding a
  normative trust decision in code; §73 demands the resolution source be named
  explicitly in traceability.

⇒ **A normative contract delta is required. It SHALL NOT be hidden in
implementation.**

### 7.3 R1 versioning (prompt §12) — HPAC-PAWA-001 **v1.1 (MINOR)**

HPAC-PAWA-001 uses `MAJOR.MINOR` only (HPAC-PAWA-REQ-151 — **there is no PATCH**).

- **HPAC-PAWA-REQ-152 (MAJOR triggers)** are all *weakening / widening / redesign*:
  making `sudo`/`euid`/env-var sufficient; collapsing or removing the
  configured-agent exclusion; permitting a same-principal topology; a
  remote/network authority service; a bearer/durable/reusable capability;
  broadening the capability into runtime approval; **changing the bootstrap trust
  root away from OS filesystem write authority**; removing generation/rollback
  protection; adding a signing/pinned/keychain key as an authority input;
  wildcarding the consumer inventory. **R1 does none of these.**
- **HPAC-PAWA-REQ-153 (MINOR permits):** "re-state verified behaviour; add a
  `pawa_failure_code` for a genuinely new terminal path **without** removing or
  re-meaning an existing one …; add an authorized-consumer **category** by
  explicit enumeration; tighten (never loosen) a bound; **clarify a
  platform-adapter detail**".
- R1 is **additive and authority-preserving**: it does not change the trust root
  (still OS filesystem write authority on the protected root), weakens no wall,
  and *implements* — does not alter — a recognition input the frozen contract
  **already requires** and §9/§73 **already anticipate the implementing phase
  naming**. It adds one protected artifact with a closed schema, binds it to the
  existing installation/generation anchors, and names the resolution source.
- **Direct precedent:** HPAC-001 **v2.1** was a MINOR that "adds one closed
  binding object … **widens no authority** … possession or reconstruction grants
  nothing". R1 is structurally the same move.
- No new `pawa_failure_code` is needed: an unresolvable account name maps to the
  existing **#3 `agent_principal_unknown`**; an agent that *can* write maps to
  existing **#4 `agent_has_protected_write_authority`**. The 21-code taxonomy and
  the PAWA→RHAMP `#1/#2/#40/#41` map are **unchanged**.

⇒ **R1 → HPAC-PAWA-001 v1.1, MINOR.**

### 7.4 R2 — HBDC environment-lock binding (prompt §13–§15) — REJECTED

Same symbolic-name-plus-live-resolution mechanics as R1, but the name is stored in
an HBDC environment-lock config rather than a PAWA record.

- HBDC-001's environment lock (§13, HBDC-REQ-025..039) is scoped to **Python
  execution-environment integrity**, not authority-principal identity. Making it
  authoritative for PAWA's exclusion predicate requires an **HBDC-001 amendment**
  — a *second* frozen contract evolving (and HBDC's v1.1/v1.2 amendments are
  themselves *"PENDING INDEPENDENT VERIFICATION"*). Strictly worse than R1's
  single MINOR.
- Violates HPAC-PAWA-REQ-134: *"HPAC-PAWA-001 has its **own** protected root and
  namespace … **no cross-subsystem bearer authority**"* — PAWA's exclusion source
  should live in PAWA's own `.authority/`.
- Environment-independence (prompt §14): a bare `PCAE_AGENT_PRINCIPAL=<name>` from
  the mutable process environment must **never** be trust; R1 and R2 both satisfy
  this only by putting the name in protected canonical state — which R1 does more
  cleanly.

⇒ **R2 rejected.** (If forced, it would be at least MINOR to *both* HPAC-PAWA-001
and HBDC-001.)

### 7.5 R3 — ship with no production mapping; fixture-seam only (prompt §16, §17) — REJECTED AS THE RESOLUTION

`production_writer()` always returns `agent_principal_unknown` on a real root;
automated tests inject `(uid,gids)` through a fixture seam.

- **Safe (fail-closed) but NOT production-complete.** `.1R.30R.3` / its slice
  `.3.1` is *"N-16-5 **Production** Protected-Admin Writer Anchor … Implementation"*
  (HPAC-PAWA §87, §96; RHAMP-REQ-156). R3 leaves the anchor **permanently
  production-unsatisfiable** ⇒ `.3.1` could only ever be classified a
  **partial / non-production** implementation and **cannot establish the
  production writer anchor N-16-5 requires**.
- **The blocker would resurface at `.1R.30R.6`** (N-16-5 closure): RHAMP-REQ-152
  requires a real `PRODUCTION` `AuthenticatedHumanPrincipal` end-to-end ⇒ a real
  `PRODUCTION` `HPACWriterCapability` ⇒ a resolved configured-agent identity. The
  phase prompt is explicit: **"Do not defer an unavoidable blocker to `.30R.6`."**
- **Retained** only as the **test strategy** — the fixture seam is needed under
  R1 too (prompt §38; see §10).

⇒ **R3 rejected as the resolution.**

### 7.6 R4 search (prompt §18) — no superior source-supported option

- **Existing protected installation principal record?** No — `DeploymentBinding`
  and the store manifest name no OS principal.
- **Derive agent OS identity from protected-root installation metadata?** The
  `HPAC-STORE-AUTHORITY/1.0` manifest carries `{device,inode}` but no owner uid;
  adding one would name the *deployment owner*, not the agent, and would be a
  schema change to an actively-referenced frozen artifact — larger than a clean
  sibling record.
- **A canonical deployment manifest naming the excluded agent OS principal?** Does
  not exist.
- **"Any OS principal that is not the deployment owner and not root"?**
  Underspecified / unsafe — a third account on the host would be misclassified.
- **Fold the account name into `deployment-owner.json`?** Rejected — §14 froze it
  **closed** and HPAC-PAWA-REQ-037 forbids "no uid / gid integer as an authority
  input"; even a *name* string added to the closed descriptor muddies the frozen
  object, and the contract's own design ("the exclusion binding records *kind* and
  *basis*, not a mutable id") signals the id belongs **elsewhere**.

⇒ **No R4 superior to R1.**

---

## 8. Desired security property (prompt §19)

> **`ConfiguredAgentAuthorityIdentity`** — the canonical OS authority identity
> `(uid, gids)` that corresponds to the configured PCAE agent principal for the
> purpose of evaluating protected-root write authority in HPAC-PAWA-001 §33
> steps 3 and 7.
>
> It is resolved **live** from a **protected, deployment-owner-provisioned,
> agent-unwritable, installation-bound record** naming the agent's **symbolic OS
> account**. It is **NOT**: the current invoking process identity; the
> deployment-owner identity; a human principal; a logical `agent_id`;
> caller-supplied metadata; a mutable environment variable; a static
> `(uid, gids)` snapshot.

---

## 9. Stored-vs-live, bootstrap, rotation, descriptor relationship, rollback, same-UID (prompt §20, §25–§31)

| Aspect | Frozen conceptual behaviour (final wording = `.1R.30R.2A.2`) |
|---|---|
| **Stored** | symbolic OS account name + `installation_id` + `{device,inode}` + `generation` + provenance + digest |
| **Resolved live** | `(uid, gids)` at every §33 recognition, from `pwd`/`grp` |
| **Bootstrap** | out-of-band, deployment-owner, alongside the descriptor at generation 1; create-only; non-circular (no capability, no FIDO2, no prior principal) |
| **Rotation / reprovision** | agent OS account change ⇒ new exclusion record at the **next generation**, in lockstep with a descriptor rotation (or its own generation increment tracked by the current-generation anchor); never a silent in-place edit |
| **Descriptor relationship** | **separate record**, transitively bound by shared `installation_id` + generation; descriptor `configured_agent_exclusion_binding` (kind + basis) is **unchanged**; **descriptor schema is not modified** |
| **Rollback** | a restored superseded exclusion record is rejected exactly as a superseded descriptor is (§20/§21) — via the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor (extend with `agent_exclusion_digest`, or require `exclusion.generation == current_generation`) |
| **Two-principal proof (§25)** | the resolved configured-agent `(uid,gids)` must satisfy `_effective_write_access(root, …) == False` ∧ `_ancestor_chain_safe == True`; else `agent_has_protected_write_authority` → fail closed |
| **Current-context check (§26 of the prompt / §31 of the contract)** | compare live `_current_agent_identity()` against the resolved configured-agent `(uid,gids)`; equal ⇒ `current_context_is_agent` → fail closed. **No descriptive agent-ID label is used to distinguish processes at an identical OS authority boundary.** |
| **Same-UID human/agent topology (§31)** | resolved configured-agent authority == deployment-owner effective authority ⇒ `_effective_write_access(root, agent_uid, …) == True` ⇒ **`agent_has_protected_write_authority` ⇒ PRODUCTION writer issuance INELIGIBLE, fail closed** (PAWA-INV-7; HPAC-PAWA-REQ-025 / 129 / 130) |
| **Fail-closed conditions** | record absent / malformed / wrong owner / wrong mode / installation mismatch / generation stale / `state != ACTIVE` / account name unresolvable / resolved agent can write the root or a safe ancestor / current process resolves to the agent account / single-account topology |

---

## 10. No env / no caller / no euid (prompt §35–§37); test seam (prompt §38)

- **No env-only trust.** The account name comes **only** from the canonical-bytes
  protected record. A mutable environment variable MAY at most *locate* protected
  configuration — never *be* the identity. (v1.0 §29 already forbids env/CLI
  redirect of the root; v1.1 extends the same discipline to the exclusion record.)
- **No caller injection.** The production `production_writer(...)` signature
  carries **no** `configured_agent_uid` / `configured_agent_gids` / account-name
  parameter. Resolution is internal.
- **No current-euid substitution.** `os.geteuid()` is **never** the answer to
  `agent_has_protected_write_authority`. It remains the identity of the **positive
  write probe** and one operand of `current_context_is_agent`.
- **Test seam (fixture-only, guarded).** A single keyword-only
  `_configured_agent_identity_source: … | None = None` (leading underscore,
  documented fixture-only; `None` in production ⇒ resolve from the protected
  record), mirroring the repo's existing `_protected_root=` / `_test_only_root=`
  idiom. A guard test asserts no non-test module ever passes it. This lets
  `.1R.30R.3.1` tests exercise: agent identity A vs. admin identity B;
  same-principal failure; group-drift; unknown account — without any production
  authority-source change.

---

## 11. Contract-compatibility matrix (prompt §32)

| Option | New authority input? | Changes §33 recognition semantics? | PAWA version | HPAC-001 | RHAMP-001 | Bootstrap | Rollback | Production-complete? | Recommended? |
|---|---|---|---|---|---|---|---|---|---|
| **R1** dedicated `.authority/agent-exclusion.json` | **yes** (one protected record) | **implements** an unresolved input; adds no new *step* | **v1.1 MINOR** | none | none | non-circular; +1 provision write | covered by current-generation anchor | **YES** | **YES** |
| R2 HBDC env-lock binding | yes | same | v1.1 MINOR **+ HBDC-001 amendment** | none | none | non-circular | needs its own currentness | yes | no — 2 contracts, wrong namespace |
| R3 no production source; fixture seam | no | leaves the input permanently unresolved | none | none | none | n/a | n/a | **NO** — permanently non-production | no (retained as test strategy only) |
| R4 fold into descriptor / manifest | yes | schema change to a frozen closed object | v1.1 MINOR–MAJOR (muddier) | none | none | non-circular | shared | yes | no — contra §14 / REQ-037 design |

---

## 12. Verdicts

### 12.1 Contract verdict (prompt §33)

**B — HPAC-PAWA-001 v1.1 MINOR required.**
(Not A: a new protected recognition input is normative, not implementation
detail. Not C: no weakening / widening / redesign — none of the REQ-152 MAJOR
triggers. Not D: no other contract need evolve under R1. Not E: a
production-safe, source-supported, additive resolution exists.)

### 12.2 Selected resolution (prompt §34)

| | |
|---|---|
| **CANONICAL SOURCE** | `<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`, closed schema `HPAC-PAWA-AGENT-EXCLUSION/1.0` (frozen by `.1R.30R.2A.2`), storing the **symbolic OS account name** of the configured PCAE agent principal + installation / root-identity / generation / provenance / digest binding |
| **PROVISIONED BY** | `scripts/hpac_protected_root_admin.py` (`provision` writes it at generation 1; a `set-agent-exclusion` subcommand rotates it) — out-of-band, deployment owner, create-only per generation |
| **LIVE VS STORED** | **stored** = symbolic account name + bindings; **resolved live** = `(uid, gids)` at every §33 recognition |
| **UID HANDLING** | never persisted as authority; resolved live; unresolvable name → `agent_principal_unknown` (fail closed) |
| **GROUP HANDLING** | live enumeration of the account's current primary + supplementary groups at each recognition (detects post-provision privilege-group drift) |
| **CURRENTNESS** | bound to `installation_id` + `{device,inode}` + `generation`; tracked by the `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor |
| **ROLLBACK** | restored superseded exclusion record rejected via the current-generation anchor, exactly as a superseded descriptor is (§21) |
| **MIGRATION** | fresh `installation_id` + fresh `{device,inode}` ⇒ re-provisioned deliberately; copying alone never validates |
| **FAIL-CLOSED CONDITION** | record absent/malformed/wrong-owner/wrong-mode/installation-mismatch/generation-stale/`state != ACTIVE` / name unresolvable / resolved agent can write root or safe ancestor / current process is the agent account / single-account topology |

### 12.3 Atomicity (prompt §40) — CONFIRMED

Configured-agent resolution + the `agent_has_protected_write_authority` and
`current_context_is_agent` evaluations **MUST** be inside the **same atomic §33
recognition unit** as descriptor validation, current-generation checking, the
write probe, and the capability mint. Omitting any of them leaves a §33 conjunct
unfulfilled → PAWA-INV-3 violated. It is part of atomic unit **A1** of the
`.1R.30R.3.1` plan.

### 12.4 D1 phase-decomposition (prompt §41) — VALIDATED, refined

CPIPC-001 v1.0 §4 grammar (`subphase-segment = numeric-segment | letter-segment`;
`numeric-segment = digit{digit}[letter{letter}]`) admits:
- `…1R.30R.2A` — `numeric-segment` `2` + letter `A` (precedent: `.1R.2A/.2B/.2C`);
- `…1R.30R.2A.1`, `…1R.30R.2A.2` — dotted `numeric-segment` children;
- `…1R.30R.3.1` … `…1R.30R.3.6` — dotted `numeric-segment` children (precedent:
  `.1R.5.2.1`);
- `…1R.30R.4` — sibling `numeric-segment`.

No collision with HPAC-PAWA-001 §78's frozen downstream (`.1R.30R.4` IV,
`.1R.30R.5` presentation, `.1R.30R.6` closure). All IDs are **recommended, NOT
reserved** (HPAC-PAWA-REQ-148/149); each needs its own explicit human
authorization. **D1 VALID**, refined to insert the `.2A` adjudication track ahead
of `.3.1`.

### 12.5 Dedicated IV for this adjudication (prompt §42) — YES

This adjudication selects a **production trust input** and mandates a **contract
version bump**. It is **not** a trivial implementation detail (it changes the
closed authority-input set of a frozen contract). Precedent: `.1R.30R` adjudication
→ `.1R.30R.1` dedicated IV. A fold-in is **not** justified.
⇒ **`.1R.30R.2A.1` — Independent Verification of this adjudication.**

### 12.6 Contract-freeze successor (prompt §43) — YES

⇒ **`.1R.30R.2A.2` — HPAC-PAWA-001 v1.1 Contract Freeze**
(adds the `HPAC-PAWA-AGENT-EXCLUSION/1.0` section; names the resolution source in
§9/§10/§14-adjacent; **no new `pawa_failure_code`**; **no descriptor schema
change**; HPAC-001 v2.1 and RHAMP-001 v1.0 byte-unchanged; `.1R.30R.2`'s v1.0
freeze record is **not rewritten** — v1.1 is append-only evolution, prompt §44).
Its own contract-freeze IV **MAY fold into `.1R.30R.3.2`** (the Slice-1 IV), per
the `.1R.29`→folded-IV precedent HPAC-PAWA-001 §18 itself cites, at the
authorizing operator's discretion.

---

## 13. Updated `.1R.30R.3.1` conceptual surface (prompt §39) — no implementation here

**New production module:**
- `src/pcae/core/hpac_pawa_agent_exclusion.py` — `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  schema helper + `resolve_configured_agent_identity()` (protected record →
  symbolic name → live `pwd`/`grp` → `(uid, gids)`; fail-closed on every
  ambiguity). Placed inside the non-agent-importable consumer-inventory fence
  with `hpac_protected_admin_writer.py`.

**New script surface:**
- `scripts/hpac_protected_root_admin.py` gains `set-agent-exclusion
  --agent-account <name>` and writes the record as part of `provision`.

**Modified (within `.3.1`, not now):**
- `hpac_protected_admin_writer.py` §33: step 3 calls
  `resolve_configured_agent_identity()` then
  `_effective_write_access` / `_ancestor_chain_safe` against the **resolved
  configured-agent** `(uid,gids)`; step 7 compares live `_current_agent_identity()`
  against the resolved configured-agent identity.
- **No reuse of `_current_agent_identity()` for the negative boundary.**

**Tests (in `.3.1`):** `test_configured_agent_source_is_the_protected_record_not_geteuid`,
`test_unresolvable_account_name_fails_closed`, `test_group_drift_detected`,
`test_uid_reuse_mismatch_fails_closed`, `test_same_uid_topology_ineligible`,
`test_restored_stale_exclusion_record_rejected`,
`test_exclusion_record_not_agent_writable`,
`test_no_caller_uid_injection_on_production_api`,
`test_fixture_seam_is_test_only`.

**Guards (in `.3.1`):** new exclusion-record-writer inventory guard;
`hpac_pawa_agent_exclusion` added to the non-agent-importable fence and the
consumer-inventory guard.

---

## 14. Derived successor sequence (prompt §43, §48)

| ID | Scope | Kind |
|---|---|---|
| `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A` | **this phase** — resolution-source adjudication | adjudication |
| `…1R.30R.2A.1` | **RECOMMENDED NEXT** — Independent Verification of this adjudication | IV |
| `…1R.30R.2A.2` | HPAC-PAWA-001 **v1.1** contract freeze (`HPAC-PAWA-AGENT-EXCLUSION/1.0`) | contract freeze |
| `…1R.30R.3.1` | Slice 1 — PAWA production writer anchor implementation (consumes v1.1) | implementation |
| `…1R.30R.3.2` | IV of `.3.1` (MAY fold the v1.1 contract-freeze IV) | IV |
| `…1R.30R.3.3` / `.3.4` | Slice 2 — RHAMP credential registry + sidecar/counter stores + enrollment/bootstrap tool / its IV | impl / IV |
| `…1R.30R.3.5` / `.3.6` | Slice 3 — real FIDO2 authenticator + native CTAP2 verify + mechanism allowlist + terminal-reason wiring / its IV | impl / IV |
| `…1R.30R.4` | composite IV + broad fixed-SHA A/B (per HPAC-PAWA-REQ-145) | IV |
| `…1R.30R.5` | protected presentation + `require_real_assurance` through Gate 5/9 (**unchanged**, HPAC-PAWA §78) | implementation |
| `…1R.30R.6` | IV + mandatory real-CTAP2-hardware + **N-16-5 closure** (**unchanged**) | IV + closure |

**RECOMMENDED NEXT PHASE: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1` — Independent
Verification of the Configured-Agent-Principal Resolution Source
Contract-Compatibility Adjudication.** Requires its own separate explicit human
authorization. **Do not begin it.**

---

## 15. Boundaries held (prompt §44–§46)

- **Historical preservation:** `.1R.30` (immutable BLOCKED), `.1R.30R`,
  `.1R.30R.1`, `.1R.30R.2` records **unchanged**. HPAC-PAWA-001 **v1.0**
  freeze record is not rewritten; v1.1 will be append-only evolution.
- `git diff 5b45aa7b HEAD -- src/pcae` → **empty**.
- `git diff 5b45aa7b HEAD -- docs/contracts` → **empty** (HPAC-PAWA-001 v1.0
  byte-unchanged; HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2 byte-unchanged).
- **N-16-5:** NOT CLOSED. **N-16-3 / N-16-4:** CLOSED. **N-16-6 / N-16-7:** OPEN,
  untouched, N-16-7 strictly last. **N-23-1 / N-23-2:** carried unchanged.
- **Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins / 0 capabilities — byte-unchanged.
- **First external effect:** ABSENT. No `adapter.dispatch(` path; no Slice C; no
  human authenticated; no approval; no PB permission; no Runtime Enforcement
  change; no execution enablement.

---

## 16. Adjudication verdict

```
CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE — ADJUDICATED

GAP                     CONFIRMED — no canonical logical-agent → OS-principal
                        binding exists anywhere in src/pcae; every existing
                        OS-identity resolution keys off the LIVE invoking process
F-1 PREDICATES          agent_has_protected_write_authority (configured principal)
                        and current_context_is_agent (live process vs configured)
                        are DISTINCT and must not be collapsed
IDENTITY MODEL          store a symbolic OS account name in a protected record;
                        resolve (uid, gids) LIVE (detects group drift + UID reuse)
SELECTED RESOLUTION     R1 — <HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json
                        (HPAC-PAWA-AGENT-EXCLUSION/1.0), deployment-owner
                        provisioned, generation-bound, agent-unwritable
R2 / R3 / R4            rejected (R2: needs HBDC amendment + wrong namespace;
                        R3: permanently non-production, defers an unavoidable
                        blocker; R4: no superior source-supported option)
NEW AUTHORITY INPUT?    YES — normative delta required, not hidden in code
CONTRACT VERDICT        B — HPAC-PAWA-001 v1.1 MINOR
                        (no MAJOR trigger; additive, authority-preserving;
                        HPAC-001 v2.1 / RHAMP-001 v1.0 byte-unchanged;
                        no new pawa_failure_code; no descriptor schema change)
ATOMICITY               CONFIRMED — resolution is inside atomic §33 unit A1
D1 DECOMPOSITION        VALIDATED (CPIPC-001 §4); .2A track inserted ahead of .3.1
DEDICATED IV            YES — .1R.30R.2A.1
CONTRACT-FREEZE PHASE   YES — .1R.30R.2A.2 (HPAC-PAWA-001 v1.1); its IV MAY fold
                        into .1R.30R.3.2
NO src/pcae CHANGE      git diff 5b45aa7b HEAD -- src/pcae : empty
NO CONTRACT CHANGE      git diff 5b45aa7b HEAD -- docs/contracts : empty
RUNTIME                 not_implemented / Observed / observe / unavailable
FIRST EXTERNAL EFFECT   ABSENT
N-16-5                  NOT CLOSED

RECOMMENDED NEXT PHASE  149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1 — Independent
                        Verification of this adjudication. Own explicit human
                        authorization required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```
