# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R — HPAC-REQ-022/023 Production Protected-Admin Writer Anchor: Architecture and Contract Adjudication

**Status: COMPLETE — ADJUDICATED.** Not BLOCKED. No production source changed;
no normative contract authored or modified. The adjudication verdict is a
**new companion contract (recommended `HPAC-PAWA-001 v1.0`)**, authored by a
recommended contract-freeze successor, followed by a fresh implementation
successor. Historical `.1R.30` is preserved immutable BLOCKED.

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R`
- **Phase title:** HPAC-REQ-022/023 Production Protected-Admin Writer Anchor: Architecture and Contract Adjudication
- **Phase-entry SHA:** `8e65529596fc351face4b83c4b5d08573326d034`
  (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30: reconcile governed push state in BLOCKED completion metadata`)
- **Phase type:** governed architecture / trust-boundary / contract-adjudication
  phase. Adjudication only. No writer-anchor mechanism implemented; no contract
  authored; no FIDO2; no credential store; no enrollment; no protected
  presentation; no approval proof; no N-16-6 / N-16-7; no Slice C; no first
  external effect; no execution enablement.
- **Authorization:** explicit single-phase human authorization for `.1R.30R`
  only (phase ID recommended, NOT reserved).
- **Production source diff:** `git diff 8e655295 HEAD -- src/pcae` is **empty**.
- **Normative contract diff:** `git diff 8e655295 HEAD -- docs/contracts` is
  **empty**.

---

## 1. Current state (phase prompt §1) — CONFIRMED, treated as current

| Item | State at phase entry |
|---|---|
| N-16-3 | CLOSED (`.1R.23` IV) |
| N-16-4 | CLOSED (`.1R.27R` IV) |
| N-16-5 | CONTRACT PROFILE FROZEN (RHAMP-001 v1.0) / IMPLEMENTATION PENDING — NOT CLOSED |
| N-16-6 | OPEN, not begun |
| N-16-7 | OPEN, not begun, strictly last |
| RHAMP-001 v1.0 | FROZEN, byte-unchanged since `.1R.29` |
| HPAC-001 | v2.1, FROZEN |
| `.1R.30` | HISTORICALLY BLOCKED — absent positive HPAC-REQ-022/023 protected-admin writer anchor |
| Real FIDO2 implementation | NOT BEGUN |
| Protected approval presentation | NOT IMPLEMENTED |
| Runtime | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities |
| First external effect | ABSENT — no `adapter.dispatch(` call site; no Slice C |
| `origin/main..HEAD` | 0 |

### 1.1 Initial repository inspection (phase prompt §4)

| Command | Result |
|---|---|
| `git status --branch --short` | `## main...origin/main` — clean working tree |
| `git rev-list --count origin/main..HEAD` | `0` |
| `git log --oneline` head | `8e655295` — `.1R.30` BLOCKED-finalization push-state reconcile |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warning-only pre-existing `tasks/DONE.md`-omission hygiene debt from earlier phases; **no current-phase error** |
| `pcae push check` | `nothing_to_push`; phase report trust passed; phase report identity passed |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; registry empty; 0 plugins / 0 capabilities; Permission Broker `execution_unavailable`; governance posture `non-executing` |
| `pcae notify status` | Telegram configured / enabled / outbound-ready |
| `pcae phase-report show --latest` | `149O.20L.7O.3W.1R.2B.1R.1.1R.30 (completed, report: complete)` |

`.1R.30` is the latest completed historical phase; its recorded status is
BLOCKED; there is no production or contract change from `.1R.30`; runtime is
`Observed` / `observe` / `unavailable`; the first external effect is absent.

---

## 2. Historical `.1R.30` preservation (phase prompt §2, §53)

`149O.20L.7O.3W.1R.2B.1R.1.1R.30` remains **BLOCKED**, immutable. This phase
does **not** rewrite it as resumed, repaired, superseded-success, or completed
implementation, and does **not** reuse its phase identity for future
implementation. The future implementation uses a fresh successor ID derived in
§21 from canonical PCAE phase-ID rules (CPIPC-001 v1.0 §4 grammar).

The `.1R.30` canonical BLOCKED artifact
(`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30_N_16_5_REAL_FIDO2_CREDENTIAL_REGISTRY_AND_AUTHENTICATION_MECHANISM_IMPLEMENTATION.md`),
its `PROJECT_STATUS.md` / `CHANGELOG.md` / `tasks/DECISIONS.md` prose, and its
completion metadata / report are all left byte-unchanged by `.1R.30R`.

---

## 3. Primary sources (phase prompt §3)

Read in full or to complete relevant scope before any adjudication conclusion:

| Source | Scope read | Purpose |
|---|---|---|
| `PROJECT_STATUS.md` (head) | current-phase block + N-16 gate-chain state | baseline confirmation |
| `.1R.30` canonical BLOCKED artifact | full | exact gap statement, primary-source list, early-STOP classification |
| `.1R.29` canonical artifact (RHAMP-001 v1.0 freeze) | §1 (companion-contract framing), front matter | companion-contract precedent for the versioning verdict |
| `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md` (RHAMP-001 v1.0) | **full — all 72 sections, RHAMP-REQ-001..169, all 18 invariants** | §14 bootstrap authority, RHAMP-REQ-047/048/049/050, RHAMP-INV-005; §68/§70 versioning; §64 decomposition |
| `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.1) | **full — all 44 sections, HPAC-REQ-001..105** | §7 (HPAC-REQ-021/022/023/024), §8 (HPAC-REQ-025..029), §28 (HPAC-REQ-079/080), §37 versioning, §32 reuse map |
| `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.2) | §0–§7, §10–§11 (Protected Root ownership), §13–§14 (environment lock), §16, §18 (root-compromise limit), threat model §4 | the existing, independently-verified PCAE precedent for a two-OS-principal protected-root writer boundary |
| `src/pcae/core/hpac_foundation.py` | **full (782 lines)** | `HPACStoreAuthority`, `HPACWriterCapability`, `ProtectedAdminCapability`, `production()` / `writer()` / `_validate_production_boundary` / `require_writer` / `record_write` / `verify_record` / `resolve_record`; the constructor seals |
| `src/pcae/core/human_principal_registry.py` | **full (578 lines)** | `HumanPrincipalRegistryStore`, `_writer()` mutation gate, `_write()` transaction, `production()`, `fixture_admin_writer()`, `CredentialRecord` (byte-frozen 9-field) |
| `src/pcae/core/hpac_verifier.py` | seams (`_ELIGIBLE_MECHANISM_IDS` L128, `_verify_assertion_material` L429, `require_real_assurance` L339/L508/L705, `_authority_class_of`) | to confirm the writer anchor is the sole `.1R.30` blocker and the verifier seams are otherwise ready |
| `src/pcae/core/hatp_class_b_topology_verifier.py` | `_current_agent_identity` (L143), `_effective_write_access` (L487), `_ancestor_chain_safe` (L526), `_symlink_effective_write_access`, `_resolve_trusted_executable*`, `_FORBIDDEN_SELF_ELEVATION_ATTRS` / `_SUSPICIOUS_ENV_KEY_SUBSTRINGS` (L694–695), `_FORBIDDEN_MUTATION_ATTRS` | the implemented **negative-half** primitives and the frozen PCAE precedent that OS filesystem permission — never `euid`/`sudo`/env — is the trust basis |
| `src/pcae/core/hatp_deployment_binding_admin.py` | module docstring + producer/rotation/revocation structure | the frozen PCAE precedent: a **separate, non-agent-importable admin writer module** invoked by an operator under the protected-admin OS principal; "Real security boundary: OS filesystem write permission on the Protected Root, never an in-process check" |
| `docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md` (CPIPC-001 v1.0) | §3 terminology, §4 grammar (§4 EBNF + whole-string form), §4.2 reserved, §10 comparison | successor phase-ID derivation |
| Repository inspection commands (phase prompt §4) | full | phase-entry baseline (§1.1) |

**Not read to completion** (not required for this adjudication, and the
adjudication conclusion does not depend on them): RIHAC-001 v2.0, RIASC-001
v3.0, HPSE-001 v1.1, HHCE-001, the Gate-5/Gate-9 consumption schema,
`approval_presentation.py`, `hpac_lifecycle.py`, `human_authentication_proof.py`,
the HATP FIDO2 provider. These govern the presentation / proof-lifecycle /
gate-consumption half that `.1R.30R` does not touch.

---

## 4. Exact HPAC-REQ-022/023 gap (phase prompt §5)

| Requirement | Negative / protective half present? | Positive recognition half present? | Implementation symbol | Contract authority | Gap? |
|---|---|---|---|---|---|
| **HPAC-REQ-022** — protected root owned/writable only by an OS/equivalent protected administration principal unavailable to same-user agent execution | **YES** — `HPACStoreAuthority._validate_production_boundary()` (`hpac_foundation.py:351`) calls `hatp_class_b_topology_verifier._effective_write_access` / `_ancestor_chain_safe` and raises `HPACAuthorityError` unless the root is provably **not** agent-writable with safe ancestors | **N/A** (this requirement is purely a boundary) | `_validate_production_boundary`, `_relative_record_path` production branch | HPAC-001 v2.1 §7 | no — implemented and correct |
| **HPAC-REQ-023** — first-principal bootstrap anchored by an externally established deployment-owner administration principal; that principal SHALL launch a non-defaultable ceremony, verify the FIDO2 registration response, atomically create the first records | **YES** (indirectly — the same negative boundary) | **NO** — no PCAE mechanism recognises the external principal and produces a `PRODUCTION` writer | absent `HPACStoreAuthority.production_writer(...)` / protected-admin-authentication factory | HPAC-001 v2.1 §7 froze the *policy*, not the *mechanism* | **YES — the anchor's positive half** |
| **HPACWriterCapability issuance for `HPACAuthorityClass.PRODUCTION`** | — | **NO** — `HPACStoreAuthority.writer()` (`hpac_foundation.py:417–431`) categorically `raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")` for every non-`FIXTURE_NON_REAL` class; class docstring `hpac_foundation.py:301`: "There is intentionally no public production-writer factory in this phase" | `HPACStoreAuthority.writer` (fixture-only), `_WRITER_CONSTRUCTOR_SEAL` | HPAC-001 v2.1 §7; not frozen at mechanism level | **YES** |
| **`HumanPrincipalRegistryStore` production writer path** | — | **NO** — every `enroll_*` / `revoke_*` routes through `_writer()` (`human_principal_registry.py:332`); a real `HPACWriterCapability` path calls `require_writer()` (needs a `PRODUCTION` writer that cannot be obtained), otherwise falls through to `legacy_fixture_writer()` (forces `FIXTURE_NON_REAL`) | `HumanPrincipalRegistryStore._writer` / `._write` | HPAC-001 v2.1 §5/§8; RHAMP-REQ-043/047 | **YES** (transitively — no writer to hand it) |
| **External deployment-owner protected administration principal (RHAMP-REQ-047)** | — | **NO** — `grep -rn "HPACAuthorityClass.PRODUCTION" src/pcae` and `grep -rln "deployment.owner|production_writer|ProductionWriter" src/pcae`: no consumable representation of the external principal exists anywhere in `src/pcae` | — | HPAC-REQ-023; RHAMP-REQ-047; RHAMP-INV-005 | **YES** |

### 4.1 Gap, stated precisely

> **HPAC-001 v2.1 §7 froze the *policy* of the production protected-admin writer
> anchor — who owns the root (an OS/equivalent protected administration
> principal), that they are unavailable to same-user agent execution
> (HPAC-REQ-022), that they alone may configure (HPAC-REQ-080), that the
> mutation is never an ordinary `pcae` CLI / hook / agent tool (HPAC-REQ-024),
> and what the bootstrap ceremony must *do* (HPAC-REQ-023). It did **not**
> freeze the *mechanism*: the concrete way PCAE code (a) recognises that it is
> executing on behalf of that external principal and not the agent principal,
> and (b) produces a `PRODUCTION` `HPACWriterCapability` that
> `HumanPrincipalRegistryStore._writer()` will accept.** `hpac_foundation.py`
> implemented only the negative half (`_validate_production_boundary`) and
> deliberately deferred the positive half ("real enrollment/writer ceremony is
> still deferred"; "There is intentionally no public production-writer
> factory in this phase"). `.1R.30` correctly STOPPED (BLOCKED) at this gap per
> RHAMP-REQ-049 / RHAMP-INV-005 and phase-prompt §18.

---

## 5. Proof the current positive path is absent (phase prompt §6)

**Every production constructor / minting path for a `PRODUCTION`
`HPACWriterCapability` was traced:**

1. `HPACWriterCapability.__init__` requires `_seal is _WRITER_CONSTRUCTOR_SEAL`
   — a module-private `object()`. A caller cannot construct one
   (`"HPAC writer capabilities cannot be caller-constructed"`).
2. `HPACWriterCapability.__reduce__` raises `TypeError` — it is non-serializable
   and cannot be pickled / `deepcopy`-reconstructed with a real seal.
3. The **only** in-module call site of `HPACWriterCapability(... _seal=_WRITER_CONSTRUCTOR_SEAL)`
   is inside `HPACStoreAuthority.writer()`, which returns early with
   `raise HPACAuthorityError(...)` for any `authority_class` other than
   `FIXTURE_NON_REAL`.
4. `HPACStoreAuthority.legacy_fixture_writer()` delegates to `.writer()` — same
   refusal; and its gate object `ProtectedAdminCapability` is documented
   "intentionally public and reproducible, and for exactly that reason can
   never authorize a production store".
5. `HPACStoreAuthority.__init__` requires `_seal is _AUTHORITY_CONSTRUCTOR_SEAL`;
   the only factories are `fixture(root)` (labels `FIXTURE_NON_REAL`) and
   `production()` (labels `PRODUCTION` but exposes no writer factory).
6. `HumanPrincipalRegistryStore.production()` builds a `PRODUCTION` authority,
   but `fixture_admin_writer()` is the only writer accessor and it calls
   `self._authority.writer(...)` → refusal for a `PRODUCTION` authority.

**Therefore:** an ordinary caller, a same-UID process, an agent, a repository,
an OS username, an environment variable, a cwd, or a session identity **cannot
legitimately mint a `PRODUCTION` `HPACWriterCapability`.** And there is
**currently no intended positive path at all** — not for the external
deployment-owner admin principal, not for anyone. The negative boundary is a
wall with no door.

This is the correct *fail-closed* state for a not-yet-adjudicated anchor. It is
not a defect; it is a deliberate deferral (`hpac_foundation.py` docstring). The
job of `.1R.30R` is to adjudicate the door.

---

## 6. Writer-anchor threat model (phase prompt §7)

**Frozen for the recommended companion contract.** The attacker MAY control:
repository content; the agent process; any same-UID process; environment
variables; cwd; CLI arguments; writable user configuration
(`~/.config/pcae/**`); task metadata; agent identity (`--agent-id`); session
metadata; and Git state.

**The attacker MUST NOT be able to mint a `PRODUCTION`
`HPACWriterCapability`, write the `HumanPrincipalRegistry`, or create /
replace / revoke any protected artifact under `HPAC_PROTECTED_ROOT`.**

**Assumptions the model is permitted to make** (each already established, and
independently verified, by HBDC-001 for the HATP domain — the direct
precedent):

- The protected root and every ancestor **can** be outside same-UID write
  authority: HBDC-REQ-011..021 provision the Protected Root **out of band**,
  owned by the admin OS principal, agent-unwritable; `_effective_write_access`
  / `_ancestor_chain_safe` verify this and are already wired into
  `_validate_production_boundary`.
- The deployment has (or, for headless-single-account hosts, may lack — see
  §14) a **distinct admin OS principal** (HBDC-REQ-001: "Exactly two OS
  principals are required"). Where the two-principal topology is not
  established, production writer authority is simply **unavailable** and the
  registry cannot be mutated — the fail-closed outcome, not a downgrade.
- An **explicit local human administrative invocation** run under that admin
  OS principal crosses a privilege boundary the agent process cannot cross,
  **because the admin principal holds real filesystem write access to the
  protected root that the agent principal provably does not** — not because of
  `euid`, `sudo`, a token, or any in-process claim.

**Explicitly out of the model's trust basis** (PCAE frozen precedent —
`hatp_class_b_topology_verifier._FORBIDDEN_SELF_ELEVATION_ATTRS` bans `setuid`
/ `seteuid` / `setreuid` / …; `_SUSPICIOUS_ENV_KEY_SUBSTRINGS` bans reasoning
from `ADMIN` / `USER` / `SUDO` / `LOGNAME` / `IDENTITY` env keys): `euid == 0`;
a `sudo` invocation; any environment variable; any repository / task / Git
signature; the OS username; the first process or user to run enrollment.

**Root-compromise limit** (inherited from HBDC-001 §18): the anchor does not
claim resistance to a fully compromised OS root/admin account. A compromised
admin OS principal can write the protected root by definition; that is the
deployment's trust root, out of scope to defend here.

---

## 7. `HPACWriterCapability` purpose and semantics (phase prompt §9)

Reconstructed from `hpac_foundation.py`:

- `HPACWriterCapability` is **opaque, non-serializable, authority-instance-bound**
  (`__slots__ = ("_authority_seal", "role", "subject", "authority_class")`;
  `__reduce__` raises). Its `_authority_seal` is the specific
  `HPACStoreAuthority` instance's private `self._seal` `object()` — a capability
  is bound to **one** authority instance in **one** process (`require_writer`
  checks `writer._authority_seal is not self._seal`).
- It is **role-scoped** and **subject-scoped**: `require_writer(writer, role,
  subject=...)` rejects on any role/subject mismatch.
  `HumanPrincipalRegistryStore` uses role `"human_principal_registry_admin"`.
- It is **assurance-class-bound**: `require_writer` rejects if
  `writer.authority_class is not self.authority_class`.
- It is **process-local**: not serializable, not replayable across processes,
  invalidated by process restart (a new `HPACStoreAuthority` has a fresh
  `self._seal`).
- It is **not** operation-scoped or TTL-bound today — a fixture writer can
  drive multiple `_write()` calls within one process.

**Frozen determinations for the `PRODUCTION` capability** (least authority):

| Property | Frozen value |
|---|---|
| Store(s) it may authorize | exactly `HumanPrincipalRegistry` writes (role `human_principal_registry_admin`) and the two RHAMP-001 protected per-credential artifacts (sidecar §17, counter-state §21) under their own writer roles — never proof / lifecycle / consumption records (those remain the trusted verifier's, `is_verifier_authenticated_principal` boundary, RHAMP-REQ-125) |
| Operation-scoped | **YES** (new) — a `PRODUCTION` capability SHALL be minted per administrative operation (`enroll_principal` \| `revoke_principal` \| `enroll_credential` \| `revoke_credential` \| the enrollment sidecar/counter-state creates for one credential) and SHALL NOT be reused for a second operation |
| Principal-scoped | **YES** where the operation targets a principal/credential — bound to the exact `principal_id` / `credential_id` |
| Process-local | **YES** — unchanged from the fixture semantics; `__reduce__` raises; restart invalidates |
| Serializable | **NO** — structurally (no change) |
| Replayable | **NO** — operation-scoped + process-local + the registry's own `expected_current` compare-and-write already rejects a stale second write |
| TTL | process lifetime only; additionally the enclosing admin tool is short-lived (one operation per invocation) |
| Reused across operations | **NO** (new constraint vs. the fixture writer) |

---

## 8. Candidate A — root/admin-owned protected descriptor (phase prompt §10)

**Shape:** an administrator-installed canonical authority record at
`<HPAC_PROTECTED_ROOT>/.authority/` (the `_AUTHORITY_DIR` already used for the
store-identity manifest and writer-provenance), naming the deployment-owner
authority.

| Dimension | Assessment |
|---|---|
| Who can create it | only a principal with filesystem write to `<HPAC_PROTECTED_ROOT>/.authority/` — i.e. the admin OS principal (HBDC-provisioned). The agent principal cannot (`_effective_write_access` → `False`). |
| Who can modify it | same |
| Provenance | the existing `HPAC-WRITER-PROVENANCE/1.0` idiom + root-identity manifest binding (`root_identity` = `{device, inode}`, rejects copy/replace) |
| Ownership / mode | `_ensure_root` / `_validate_production_boundary` / `_relative_record_path` production branch already enforce not-agent-writable + safe ancestors + `0700` |
| Symlink / path attack | `reject_symlink` on every component; `_reject_symlink_components`; create-only `os.link` with `O_NOFOLLOW` |
| Same-UID agent access | **cannot create or modify** the descriptor (no filesystem write); **cannot forge** one that resolves (root-identity manifest + provenance digest + not-agent-writable ancestor checks) |
| Bootstrap circularity | **none** — the descriptor is installed by the admin OS principal out of band (HBDC-REQ-011..021 precedent), before any PCAE principal exists |
| Portability | macOS `/Library/Application Support/PCAE/HPAC/protected-root`, Linux `/etc/pcae/hpac/protected-root` — already resolved by `resolve_hpac_protected_root()` |
| Revocation | replace/remove the descriptor (admin filesystem operation); `.authority/` content is authority-bearing state |
| Auditability | every `record_write` emits provenance; enrollment emits the RHAMP-REQ-051 evidence record |

**Verdict:** viable **as one conjunct**, but a bare descriptor is
**path-only authority** unless its integrity is bound (§39). The descriptor's
real value is that its *writability* is the proof — only the admin principal
can install it. It is **not** a bearer secret.

---

## 9. Candidate B — privilege-gated (`sudo`/root) invocation context (phase prompt §11)

| Dimension | Assessment |
|---|---|
| What OS privilege proves | that the *current process* runs with elevated OS rights **now** |
| What it does NOT prove | *which human* elevated; that the deployment-owner authorised *this* operation; that the caller is not an automated `sudo`-NOPASSWD agent job; that `euid == 0` was reached legitimately |
| Same-UID exclusion | **weak** — a same-UID agent with a `sudo` NOPASSWD rule, or any `setuid` helper, would pass a naive `euid == 0` check |
| Deployment-owner binding | **none** — `euid` carries no identity beyond "root" |
| Cross-platform | `sudo` semantics, `SUDO_USER`, and audit trails differ macOS vs. Linux; `SUDO_USER` is attacker-influenceable env (`_SUSPICIOUS_ENV_KEY_SUBSTRINGS` bans it) |
| PCAE precedent | **explicitly rejected** — `hatp_class_b_topology_verifier._FORBIDDEN_SELF_ELEVATION_ATTRS` bans `setuid`/`seteuid`/…; the whole Class-B model is filesystem-permission-based, never `euid`-based |

**Verdict:** **REJECTED as a standalone authority.** `euid == 0` SHALL NOT
mint a `PRODUCTION` writer (phase prompt §38). It MAY appear only as a
*non-authoritative* audit annotation. The real boundary is filesystem write
access to the protected root, which an admin principal has **without** needing
to be root at all.

---

## 10. Candidate C — administrator-signed installation record + protected pinned key (phase prompt §12)

**Shape:** an out-of-band admin-signed canonical authority record verified
against a verification key pinned under `<HPAC_PROTECTED_ROOT>/.authority/`.

| Dimension | Assessment |
|---|---|
| Key bootstrap | the pinned public key must itself be installed by the admin principal into the protected root → **collapses to Candidate A** (the protected-root write is the real anchor); the signature adds nothing the filesystem ownership does not already give |
| Signing-key custody | introduces a **new persistent private key** the admin must guard — a new bearer-authority surface with no threat-model gain in the local-interactive topology (RHAMP-INV-014) |
| Same-UID accessibility | if the signing key lives on the same host, a compromised admin session can read it; if it lives elsewhere, that is remote infrastructure (phase prompt §19 — out of scope) |
| macOS/Linux storage | no portable answer without a keychain/keyring (Candidate D's problems) |
| Offline | yes, but see key custody |

**Verdict:** **REJECTED for v1.** It moves the trust-root problem into an
unexplained key (phase prompt §12 warning) and adds a persistent bearer
secret (phase prompt §40, RHAMP-INV-006 spirit). A future MAJOR profile MAY
add signing if a remote/multi-host topology is authorised (phase prompt §55).

---

## 11. Candidate D — OS keychain / keyring admin key (phase prompt §13)

| Dimension | Assessment |
|---|---|
| Portability | macOS Keychain vs. Linux `keyctl` / Secret Service / gnome-keyring — **materially different**, would need two adapters |
| Interactive unlock | headless hosts cannot unlock; conflicts with the "usable at the local interactive control-plane host" model but adds a second interactive gate |
| Same-UID agent accessibility | a same-UID agent process can often read the **same user's** keyring items — **this is the exact same-UID threat the anchor exists to close** |
| Persistent secret risk | yes — a stored reusable credential accessible to same-UID processes (phase prompt early-STOP condition: "cannot store a reusable bearer secret accessible to ordinary same-UID PCAE/agent processes") |
| Recovery | keyring loss / re-image = full re-provision |

**Verdict:** **REJECTED for v1.** A user-keyring item is same-UID-readable,
which fails the core requirement, and it is not portable. It also conflicts
with the local-interactive-only assumption without adding assurance.

---

## 12. Candidate E — composed installation + privilege model (phase prompt §14)

**Shape:**
```
admin-installed protected authority descriptor under <HPAC_PROTECTED_ROOT>/.authority/
  + the process holds real filesystem write access to <HPAC_PROTECTED_ROOT>
    (positive probe) AND the agent-identity check proves it is NOT the agent principal
  + a non-agent-importable admin writer module (consumer-inventory guarded)
  + exact operation / principal / credential binding
  -> a short-lived, process-local, operation-scoped PRODUCTION HPACWriterCapability
```

| Dimension | Assessment |
|---|---|
| Trust root | **OS filesystem write authority on the out-of-band-provisioned protected root** — identical to HBDC-001's frozen, IV'd Class-B model; not a new subsystem |
| Same-UID exclusion | the agent principal provably lacks write access (`_effective_write_access` → `False`), so it cannot install the descriptor, cannot pass the positive write probe, and — via the consumer-inventory guard — cannot even import the writer module |
| Bootstrap circularity | **none** — the descriptor + protected root are provisioned by the admin OS principal before any PCAE principal (HBDC-REQ-011..021 precedent) |
| Repo / env / cwd influence | **none** — `resolve_hpac_protected_root()` takes no input; the descriptor path is fixed; the write probe is against the fixed root |
| Portability | fixed macOS + Linux paths already defined |
| Non-bearer | the capability is process-local, non-serializable, operation-scoped; nothing durable is a bearer token |

**Verdict:** **SELECTED (§17).** This is not "stronger because it sounds
stronger" — it is the **exact composition HBDC-001 already froze and
independently verified** for the structurally identical HATP protected-root
writer boundary, re-applied under HPAC-001's separate registry / namespace /
trust domain (HPAC-REQ-018/019/020 keep the domains separate; HPAC-REQ-019 and
§32 explicitly authorise reusing the *pattern* and the atomic-write idiom).

---

## 13. Existing PCAE trust precedent (phase prompt §15)

| Pattern | Existing PCAE location | Reuse for the writer anchor |
|---|---|---|
| Two-OS-principal protected-root writer boundary | HBDC-001 v1.2 §7, §10–§11; `hatp_deployment_binding_admin.py` | **direct precedent** — "Real security boundary: OS filesystem write permission on the Protected Root, never an in-process check" |
| Separate, non-agent-importable admin writer module | `hatp_deployment_binding_admin.py`, `hatp_mandatory_certification.py`, `scripts/hatp_certification_admin.py` | the `PRODUCTION` writer factory lives here, not in an agent-reachable module |
| Consumer-inventory guard (module never imported by agent code) | HBDC-REQ-056/066; guarded in `tests/` (`hatp_deployment_binding_admin` import-boundary tests) | a `.1R.30R.*` guard asserts the new writer module is imported by no `cli.py` / `commands/**` / `core/agent.py` path |
| Not-agent-writable + safe-ancestor filesystem check | `hatp_class_b_topology_verifier._effective_write_access` / `_ancestor_chain_safe` | already wired into `HPACStoreAuthority._validate_production_boundary`; add the **positive** probe (writable by *this* invocation) as its mirror |
| Root-identity binding (copy/replace detection) | `hpac_foundation.HPACStoreAuthority._root_identity` (`{device, inode}`) + manifest | descriptor + provenance reuse it unchanged |
| Atomic create-only / atomic-replace write + read-back | `hpac_foundation.write_atomic_create_only` / `write_atomic_replace` | RHAMP-REQ-057/069 sidecar + counter-state writes; registry `_write` |
| Constructor seal / process-local non-bearer capability | `hpac_foundation._WRITER_CONSTRUCTOR_SEAL`, `HPACWriterCapability.__reduce__` | the `PRODUCTION` capability reuses the exact seal discipline |
| Admin ceremony pattern (enroll/revoke + preview, typed errors) | `hatp_principal_signer_admin.py`; HPSE-001 | the enrollment tool's shape |

**Conclusion:** the anchor needs **no new subsystem**. It is the HBDC-001
Class-B pattern, already proven and independently verified, applied to
`hpac_foundation.py`'s production branch.

---

## 14. Same-UID-agent exclusion / repo-env-cwd independence / offline / portability / bootstrap-root / deployment-owner recognition / human-auth requirement (phase prompt §16–§24)

### 14.1 Same-UID-agent exclusion (§16)

For the SELECTED architecture, for each attack the agent (same OS user in a
single-account dev host, or the distinct agent principal in a Class-B
deployment) could attempt:

| Agent attempt | Result | Why |
|---|---|---|
| Create / modify the `.authority/` descriptor | **denied** | no filesystem write to the protected root (Class-B) / `_validate_fixture_permissions` + not-agent-writable ancestor checks reject a group/world-writable dev fixture; a single-account dev host simply has **no `PRODUCTION` root** and the writer is unavailable |
| Invoke the `PRODUCTION` writer factory | **denied** | it lives in a module the consumer-inventory guard proves is not importable from any agent path |
| Forge invocation metadata | **denied** | there is no metadata to forge — the check is a live filesystem write probe against a fixed path |
| Copy / deserialize a capability | **denied** | `__reduce__` raises; `_authority_seal` is a per-instance `object()`; a new process has a fresh seal |
| Reconstruct via `object.__new__` + known fields | **denied for use** | `require_writer` checks `writer._authority_seal is self._seal` (identity, not value); `record_write` / `_write` re-probe the root |

### 14.2 Repository / environment / cwd independence (§17, §18)

`resolve_hpac_protected_root()` accepts **no** input. The descriptor path is a
fixed subpath of that root. The positive write probe is against that fixed
root. `HPAC-REQ-079/080` already forbid repository / task / agent / cwd /
environment influence, and `_validate_production_boundary` already rejects
`"production HPAC authority cannot be redirected"`. Environment variables MAY
NOT establish authority; at most a future MINOR could let the admin point at
an *already-protected* canonical location, but the SELECTED design does not
even do that — the path is compiled in.

### 14.3 Offline (§19)

Fully offline. No identity provider, no token service, no network. The write
probe and descriptor read are local filesystem operations.

### 14.4 macOS / Linux portability (§20)

One contract, two already-defined fixed roots. `_effective_write_access` /
`_ancestor_chain_safe` already handle both (POSIX mode bits + group +
platform-gated ACL). No OS-specific adapter. HBDC-001 already spans both.

### 14.5 Bootstrap root — the first-install problem (§21)

The deployment owner performs an explicit privileged **out-of-band**
installation, exactly as HBDC-REQ-011..021 already require for the HATP
Protected Root:

1. **Command / process:** an operator, logged in as the admin OS principal
   (or, on a single-account host, as the sole user with a documented
   understanding that the agent is not sandboxed from it), runs a
   PCAE-provided admin provisioning step (recommended:
   `scripts/hpac_protected_root_admin.py provision`, a new non-agent-importable
   script) that creates `<HPAC_PROTECTED_ROOT>` `0700`, writes the
   `.authority/` store-identity manifest and the deployment-owner authority
   descriptor, and records a durable provenance entry.
2. **Privilege boundary:** the operating-system filesystem permission model —
   the created tree is owned by the admin principal and is **not** writable by
   the agent principal.
3. **Canonical record created:** `HPAC-STORE-AUTHORITY/1.0` manifest (exists
   today) + a new `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` record (recommended).
4. **Provenance / audit:** a durable `append_provenance_event` entry against
   the deployment tree (the HBDC idiom).
5. **How future invocations recognise it:** the `PRODUCTION` writer factory
   reads the descriptor, verifies root-identity + provenance + not-agent-writable
   ancestors, **and** performs a positive write probe proving the current
   invocation can write the protected root.

**No circular requirement for an existing `HPACWriterCapability`** — the
bootstrap is a filesystem provisioning act by the OS admin principal, outside
PCAE's authority model entirely.

### 14.6 Deployment-owner recognition semantics (§22)

"PCAE recognises the external deployment-owner protected administration
principal" means exactly: **a process that (a) can write
`<HPAC_PROTECTED_ROOT>` and its `.authority/` subtree, (b) is provably not the
agent principal per `_current_agent_identity` / `_effective_write_access`, and
(c) presents a valid, root-identity-bound `.authority/` authority descriptor.**
PCAE does **not** need a persistent cryptographic principal identity, an
enrolled FIDO2 credential, or a civil identity for the *admin* principal — it
needs the **filesystem-ownership role**. (The *human principal* being enrolled
still needs the full FIDO2 credential — that is RHAMP-001's job, unchanged.)

### 14.7 Is human authentication required for the writer anchor itself? (§23)

**Adjudicated: NO — the `PRODUCTION` writer capability issuance requires
installation-authority proof (filesystem role) + explicit local
administrative invocation, NOT a real FIDO2 human authentication of the admin
principal.** Requiring FIDO2 for the *admin* principal would create the exact
circular dependency phase prompt §23 warns against (FIDO2 enrolment needs the
writer; the writer would need FIDO2). The *human principal being enrolled*
still performs UP+UV `makeCredential` during the ceremony (RHAMP-REQ-048) —
that is credential *registration*, not admin *authentication*.

### 14.8 First-bootstrap exception (§24)

The one-time provisioning in §14.5 **is** the bootstrap exception, and it is
already bounded: explicit; privileged (filesystem); local; non-agent (separate
script, consumer-inventory guarded); auditable (provenance entry); **cannot
silently recur** (create-only manifest — a second `provision` against an
existing root is a no-op or a fail-closed conflict, mirroring
`hatp_deployment_binding_admin`'s idempotency discipline); **cannot be
triggered by repository content** (not an agent-reachable code path); **does
not create runtime execution authority** (§48).

---

## 15. Capability minting / scope / currentness / non-bearer / rotation / failure / audit (phase prompt §25–§31)

### 15.1 Minting (§25)

| Field | Frozen |
|---|---|
| Issuer | the new `PRODUCTION` writer factory (recommended `HPACStoreAuthority.production_writer(operation, *, principal_id=None, credential_id=None)`) in a **non-agent-importable** module |
| Constructor / seal | the existing `_WRITER_CONSTRUCTOR_SEAL` + per-instance `_authority_seal`; unchanged discipline |
| Inputs | the resolved `PRODUCTION` `HPACStoreAuthority`; the `.authority/` descriptor resolution result; the positive write-probe result; the operation enum; optional `principal_id` / `credential_id` |
| Scope | one operation, one target principal/credential |
| Expiry / lifetime | process lifetime; the admin tool exits after one operation |
| Operation ID | recorded in writer provenance (`writer_role` already carries the role; add the operation to the RHAMP-REQ-051 evidence) |
| Principal / anchor binding | `subject` = `principal_id` or `credential_id`; `_authority_seal` binds the authority instance |
| Non-serializability | `__reduce__` raises — unchanged |
| Non-transferability | per-instance seal identity check — unchanged |
| Replay | operation-scoped + `expected_current` compare-and-write + create-only provenance |

### 15.2 Scope (§26)

The `PRODUCTION` capability binds: the **mutation type** (one of
`enroll_principal` / `revoke_principal` / `enroll_credential` /
`revoke_credential`); the **target principal / credential id** where
applicable; the **protected-root target** (the fixed registry path + the
per-credential sidecar/counter-state paths); **one invocation**. It is
**not** an "HPAC admin forever" capability.

### 15.3 Currentness (§27)

The capability is short-lived / process-local, so anchor revocation
propagation is trivial: a revoked `.authority/` descriptor → the next
`production_writer()` call fails closed; no long-lived capability survives to
be stale. No durable capability is contemplated. (This mirrors
`authority_generation` currentness for proofs, RHAMP-REQ-118 — but the writer
capability itself needs no generation marker because it never persists.)

### 15.4 Copy / reconstruction (§28)

`copy.copy` / `deepcopy` / `pickle` → `__reduce__` raises. `object.__new__` +
known fields → the object exists but `require_writer` /
`record_write` reject it (identity check on `_authority_seal`; live re-probe of
the root). Known seal / known descriptor digest → the seal is a per-process
`object()`, not a value. Process restart → fresh authority, fresh seal, the
old capability is inert. **Structure is not authority** — enforced by the
existing seal-identity + live-re-probe discipline.

### 15.5 Anchor revocation / rotation (§29)

- Replace the deployment-owner descriptor: an admin filesystem write to
  `.authority/`.
- Revoke it: remove / mark it (admin filesystem operation); the next
  `production_writer()` fails closed.
- Reinstall / machine migration / protected-root recreation: re-run the §14.5
  provisioning; the root-identity manifest (`{device, inode}`) will differ, so
  a copied root is rejected (`"HPAC root was copied or replaced"`) — a genuine
  re-provision writes a fresh manifest.
- Historical audit (provenance entries, enrollment evidence) remains **evidence
  only**, never reusable authority.

### 15.6 Failure taxonomy (§30) — fail-closed, no implicit fallback

| Category | Trigger | Outcome |
|---|---|---|
| `anchor_descriptor_missing` | no `.authority/` deployment-owner descriptor | no `PRODUCTION` writer; `bootstrap_authority_unproven` at the ceremony |
| `anchor_descriptor_malformed` | closed-schema / canonical-byte failure | fail closed |
| `anchor_descriptor_untrusted` | root-identity / provenance-digest mismatch | fail closed |
| `protected_root_ownership_invalid` | root or ancestor agent-writable / indeterminate | fail closed (`_validate_production_boundary` already) |
| `positive_write_probe_failed` | current invocation cannot write the protected root | no `PRODUCTION` writer (this invocation is not the admin principal) |
| `agent_identity_is_writer` | `_current_agent_identity` indicates the caller *is* the agent principal | fail closed |
| `operation_scope_mismatch` | capability used for a different operation / target | `require_writer` rejects |
| `anchor_revoked` | descriptor removed/revoked after mint | next call fails closed; in-flight `expected_current` write rejects on any registry drift |
| `duplicate_bootstrap` | second provision against an existing root | no-op / fail-closed conflict |
| `stale_capability` | reused after operation / after restart | seal-identity check rejects |
| `reconstruction_attempt` | forged/deserialized capability | `__reduce__` raises / seal-identity rejects |
| `internal_verification_error` | any unexpected fail-closed error | no authority |

Maps onto RHAMP-001 §49's `terminal_reason_code` set via
`bootstrap_authority_unproven` (#1), `enrollment_not_protected_admin` (#2), and
`protected_root_invalid` (#40) — **no new `terminal_reason_code` is required**
(the companion contract may note this alignment; RHAMP-INV-010 unchanged).

### 15.7 Audit evidence (§31)

Durably recorded: **initial anchor installation** (provenance entry at
provision time); **anchor replacement** (provenance entry); **capability
issuance** (writer provenance `HPAC-WRITER-PROVENANCE/1.0` — exists);
**administrative mutation** (the registry write + the RHAMP-REQ-051 enrollment
evidence). **Audit evidence is not reusable writer authority** — a provenance
record proves a write happened; it does not mint a capability.

---

## 16. Contract-versioning adjudication (phase prompt §32–§36, §56)

### 16.1 HPAC-001 (§32)

The four options:

- **A** — HPAC already defines the trust semantics sufficiently, leaving
  positive recognition fully implementation-defined. *Partly true* — §7 froze
  the policy — *but* the concrete recognition mechanism (filesystem-role trust
  root, the non-agent-importability requirement, the `PRODUCTION` capability
  scope/lifetime, the bootstrap exception bounds, the failure taxonomy) are
  **normative trust decisions** that phase prompt §35 forbids hiding in code.
- **B** — HPAC defines the principal but not the authority-recognition
  semantics → a MINOR is required. *Rejected* — a MINOR to HPAC-001 forces
  re-independent-verification of an actively-referenced frozen contract and
  invites a parent cascade (RIHAC-001 §12 cond 7 names "HPAC-001 v2.1"
  literally; RHAMP-001 pins "HPAC-001 v2.1").
- **C** — MAJOR. *Rejected* — nothing is removed, relaxed, widened, or
  re-meant; the negative boundary and every wall are preserved.
- **D — SELECTED** — a **new companion contract** freezes the anchor without
  an HPAC-001 bump. This is the **exact REPRC-001 / PBNDE-001 / RHAMP-001
  precedent** ("companion born to avoid a parent cascade"). HPAC-001 stays
  **v2.1**; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`.

### 16.2 RHAMP-001 (§33)

RHAMP-REQ-047 references **HPAC-REQ-023** and frames the anchor as the trust
anchor while leaving its mechanics **external** ("This is the trust anchor; it
terminates bootstrap without circular PCAE self-authorization"). RHAMP-REQ-049
already prescribes the STOP-when-absent behaviour `.1R.30` exercised. **No
RHAMP-001 change is needed or authorised.** The companion contract satisfies
the anchor RHAMP-REQ-047 points to; RHAMP-001 v1.0 stays byte-unchanged. This
phase does **not** edit RHAMP-001 (phase prompt §33).

### 16.3 New companion contract option (§34)

**Recommended identity: `HPAC-PAWA-001 v1.0` — HPAC Production Protected
Administration Writer Anchor Contract** (repository naming: an independent
`HPAC-PAWA-REQ-###` namespace, HPSE-001 precedent; file
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`).
It would define **only**:

- deployment-owner recognition = filesystem write authority on the protected
  root + not-agent-principal + a root-identity-bound `.authority/` descriptor;
- the one-time out-of-band installation / bootstrap procedure and its bounds;
- the `.authority/` deployment-owner authority descriptor schema
  (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`, closed, canonicalised per
  HPAC-REQ-089);
- positive validation (descriptor + root-identity + provenance + not-agent
  ancestors + positive write probe);
- `PRODUCTION` `HPACWriterCapability` minting, operation/principal scope,
  process-local non-bearer lifetime, non-serializability, restart invalidation;
- revocation / rotation / machine migration;
- the non-agent-importable admin writer module + consumer-inventory guard
  obligation;
- the failure taxonomy (§15.6) and its mapping onto RHAMP-001 §49;
- audit evidence semantics;
- the security-claim boundaries (§18).

Per phase prompt §60, **this phase does not author `HPAC-PAWA-001`.** It
recommends a dedicated contract-freeze successor (§21).

### 16.4 Pure-implementation option (§35)

**Rejected as the primary verdict** precisely because it would hide the
normative trust decisions above in `hpac_foundation.py`. (If the recommended
contract-freeze phase, on its own primary-source reconstruction, concludes
every one of those decisions is *already* normative somewhere — it is not —
it may downgrade to pure implementation. The adjudication here says: author
the companion contract.)

### 16.5 Versioning matrix (§36)

| Artifact | Current version | Gap | Semantic change? | Required action | Reason |
|---|---|---|---|---|---|
| HPAC-001 | v2.1 | mechanism of the §7 positive anchor | **no** — policy already frozen; mechanism is additive, widens no authority | **none** (stays v2.1) | companion-contract precedent avoids a parent cascade |
| RHAMP-001 | v1.0 | none — RHAMP-REQ-047 points to an external anchor | **no** | **none** (stays v1.0, byte-unchanged) | anchor mechanics are external to RHAMP by its own text |
| human-principal registry contract (HPAC-001 §5 / `human_principal_registry.py`) | HPAC-001 v2.1 | none — `CredentialRecord` byte-unchanged; only the writer *path* is exercised | **no** | **none** | RHAMP-REQ-055 already froze the schema |
| writer-capability contract (`HPACWriterCapability`, HPAC-001 foundation) | HPAC-001 v2.1 | `PRODUCTION` minting path + scope semantics | **no** — additive; non-bearer/seal discipline preserved | **new companion** `HPAC-PAWA-001 v1.0` | normative trust decisions must be contract text |
| protected-root contract (HPAC-REQ-021/022; HBDC-001) | HPAC-001 v2.1 / HBDC-001 v1.2 | positive write-probe mirror of the negative check | **no** | **none** to HBDC-001; **new companion** covers the HPAC positive side | HBDC pattern reused, not amended |
| RIHAC-001 | v2.0 | none | no | none | §12 cond 7 consumes HPAC evidence, unaffected |
| RIASC-001 | v3.0 | none | no | none | wire shape unaffected |
| HPSE-001 | v1.1 | none | no | none | pattern precedent only |
| HHCE-001 | current | none | no | none | pattern precedent only |

### 16.6 Contract-adjudication verdict (§56)

> **B. NEW COMPANION CONTRACT REQUIRED** — `HPAC-PAWA-001 v1.0`, authored by a
> recommended contract-freeze successor phase. **Not A** (would hide normative
> trust decisions in code). **Not C / D (HPAC MINOR / MAJOR)** (would force a
> parent-contract cascade for an additive, authority-preserving mechanism).
> **Not E (BLOCKED)** — the trust root is non-circular, same-UID-agent-safe,
> offline, portable, and directly precedented by HBDC-001; no human
> adjudication beyond this phase is required to *proceed*.

---

## 17. Preferred anchor architecture — the verdict (phase prompt §37, §57)

> **TRUST ROOT:** OS filesystem write authority on the out-of-band-provisioned,
> deployment-scoped protected root `<HPAC_PROTECTED_ROOT>` (macOS
> `/Library/Application Support/PCAE/HPAC/protected-root`, Linux
> `/etc/pcae/hpac/protected-root`), owned by an admin OS principal, provably
> **not** writable by the agent principal. Identical trust root to HBDC-001's
> Class-B Protected Root.
>
> **POSITIVE RECOGNITION:** (a) resolve a root-identity-bound `.authority/`
> deployment-owner authority descriptor (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`);
> (b) `_validate_production_boundary` passes (root + ancestors not
> agent-writable); (c) a **positive write probe** proves the current invocation
> can atomically create-and-remove a sentinel under `<HPAC_PROTECTED_ROOT>/.authority/`;
> (d) `_current_agent_identity()` does not identify the caller as the agent
> principal. All four required; any failure → no `PRODUCTION` writer.
>
> **CAPABILITY ISSUER:** a new `PRODUCTION` writer factory (recommended
> `HPACStoreAuthority.production_writer(operation, *, principal_id=None,
> credential_id=None)`) exported **only** from a new non-agent-importable
> module (recommended `src/pcae/core/hpac_protected_admin_writer.py`), enforced
> by a `.1R.30R.*` consumer-inventory guard (HBDC-REQ-056/066 precedent).
>
> **CAPABILITY SCOPE:** one administrative operation; one target
> principal/credential; the fixed registry + per-credential sidecar/counter-state
> paths; process-local; non-serializable (`__reduce__` raises); restart-invalid;
> not reusable for a second operation.
>
> **BOOTSTRAP:** a one-time out-of-band `scripts/hpac_protected_root_admin.py
> provision` step run by the admin OS principal — creates the `0700` root,
> the store-identity manifest, the deployment-owner descriptor, and a durable
> provenance entry. Create-only; non-recurring; not agent-reachable.
>
> **REVOCATION:** admin filesystem replace/remove of the `.authority/`
> descriptor; the next `production_writer()` fails closed. Root copy/replace is
> caught by the `{device, inode}` root-identity manifest.
>
> **SAME-UID AGENT EXCLUSION:** the agent principal cannot write the protected
> root (so cannot install the descriptor, cannot pass the write probe), cannot
> import the writer module (consumer-inventory guard), and cannot forge/replay a
> capability (per-instance seal identity + `__reduce__` raising + live re-probe).
> On a single-account dev host there is **no `PRODUCTION` root at all** and the
> writer is unavailable — the correct fail-closed outcome.
>
> **PORTABILITY:** one companion contract, two already-defined fixed roots;
> `_effective_write_access` / `_ancestor_chain_safe` already span macOS + Linux;
> no OS-specific adapter.

### 17.1 Rejected alternatives (explicit)

- **Candidate B (`sudo`/`euid` gate) — REJECTED:** OS privilege ≠ human /
  deployment-owner identity; same-UID `sudo` NOPASSWD / `setuid` bypass; PCAE
  frozen precedent (`_FORBIDDEN_SELF_ELEVATION_ATTRS`) already rejects it.
- **Candidate C (admin-signed record + pinned key) — REJECTED for v1:** moves
  the trust root into an unexplained key; adds a persistent bearer secret; no
  portable key store; collapses to Candidate A anyway.
- **Candidate D (OS keychain/keyring) — REJECTED for v1:** user-keyring items
  are same-UID-readable (the exact threat); not portable; adds a second
  interactive gate.
- **Bare Candidate A (descriptor by path alone) — REJECTED:** path-only
  authority; must be composed with the write probe + not-agent-identity check
  + integrity binding (→ Candidate E).
- **Pure implementation (no contract) — REJECTED as primary verdict:** hides
  normative trust decisions in code (phase prompt §35).
- **BLOCKED — REJECTED:** no circularity, no MAJOR redesign, no remote
  infrastructure, no reusable same-UID bearer secret; HBDC-001 is a direct,
  independently-verified precedent.

---

## 18. Security-claim boundaries (phase prompt §58)

The anchor SHALL claim **only**:

- The `PRODUCTION` writer is available **only** to an invocation with real
  filesystem write authority on the out-of-band-provisioned protected root that
  the agent principal provably lacks.
- The registry / sidecar / counter-state stores cannot be mutated by any
  same-UID agent code path, by repository / environment / cwd / caller input,
  or by a forged / copied / deserialized capability.

The anchor SHALL NOT claim: that `sudo` or `root` proves human or
deployment-owner identity; that a descriptor file's presence proves current
human presence; that the writer capability is approval authority; that the
protected-admin writer authority can approve runtime effects; resistance to a
fully compromised admin OS account (HBDC-001 §18 limit, inherited).

**Frozen walls (all preserved):**
```
root / euid 0            != deployment-owner human principal
sudo invocation          != human principal
OS username              != human principal
same UID                 != protected-admin authority
agent identity           != human principal
session identity         != protected-admin authority
file under protected root != trusted provenance
valid descriptor         != trusted anchor (needs root-identity + write probe + not-agent-identity)
trusted writer capability != approval authority
writer capability        != PB permission != Runtime Enforcement != runtime capability != execution
```

---

## 19. Store-writer / enrollment / recovery / N-16 relationships (phase prompt §43–§48)

### 19.1 Store-writer relationship (§43)

```
admin OS principal provisions <HPAC_PROTECTED_ROOT> + .authority/ descriptor (out of band, one time)
  -> operator (admin principal) runs the non-agent enrollment tool
  -> tool calls production_writer(operation, principal_id/credential_id)
       -> resolves descriptor + root-identity + provenance
       -> _validate_production_boundary passes
       -> positive write probe passes; caller != agent principal
       -> mints a scoped, process-local PRODUCTION HPACWriterCapability
  -> HumanPrincipalRegistryStore.enroll_credential(capability, ...) verifies the
     capability via require_writer(role, subject) and performs the exact
     atomic mutation under writer_transaction (expected_current compare-and-write,
     read-back verified)
  -> capability is discarded; the tool process exits
```

`HumanPrincipalRegistryStore._writer()` performs **no weaker independent admin
test** — it delegates entirely to `require_writer`, which for a `PRODUCTION`
authority now has a real capability to check. (`legacy_fixture_writer` /
`ProtectedAdminCapability` remain fixture-only, unchanged.)

### 19.2 Enrollment relationship (§44)

The future FIDO2 first-credential enrollment (recommended `.1R.30R.3`) consumes
**this same** bounded writer capability boundary. It embeds **no** second
admin-authority model — it obtains a `PRODUCTION` capability from
`production_writer('enroll_credential', credential_id=...)` and passes it to
`enroll_credential`.

### 19.3 Recovery relationship (§45)

Total-principal-loss recovery = repeat the bootstrap ceremony (HPAC-REQ-065,
RHAMP-REQ-050), which requires the admin OS principal + a `PRODUCTION` writer
via the same anchor. The writer anchor is **not** itself approval authority for
runtime effects — it can create/revoke registry records, nothing else.

### 19.4 N-16-5 relationship (§46)

The anchor is a **prerequisite** for N-16-5 enrollment implementation. It does
**not** authenticate ordinary runtime approvals, does **not** satisfy
RHAMP-001's real human-auth mechanism, and does **not** by itself close
N-16-5.

### 19.5 N-16-6 / N-16-7 separation (§47) and static no-effect boundary (§48)

Protected-admin writer authority `!=` adapter admission `!=` runtime
capability. `.1R.30R` and its recommended successors introduce **no**
`adapter.dispatch()`, no runtime plugin capability, no external / network call,
no runtime effect adapter, no shell execution authority, no N-16-7 state
transition. Runtime stays `Observed` / `observe` / `unavailable`.

---

## 20. Attack matrix (phase prompt §49)

| # | Attack | Expected | Rationale |
|---:|---|---|---|
| 1 | same-UID agent calls the admin CLI / writer factory | **fail** | writer factory module not importable from any agent path (consumer-inventory guard); positive write probe fails for the agent principal |
| 2 | same-UID agent copies the protected `.authority/` descriptor into a repo / temp path | **fail** | resolution is against the fixed `<HPAC_PROTECTED_ROOT>` only; `_validate_production_boundary` rejects any redirect; root-identity `{device, inode}` mismatch |
| 3 | repo creates a fake `.authority/` descriptor | **fail** | repo has no write to the protected root; a repo-local file is never resolved |
| 4 | env var redirects the protected root | **fail** | `resolve_hpac_protected_root()` takes no input; `"production HPAC authority cannot be redirected"` |
| 5 | cwd symlink trick | **fail** | `reject_symlink` / `_reject_symlink_components` on every component; `O_NOFOLLOW` |
| 6 | direct `root` invocation of the writer factory | **fail unless** the root user also has legitimate filesystem write to the admin-owned protected root **and** presents a valid descriptor **and** is not the agent principal; `euid == 0` alone mints nothing |
| 7 | `sudo` invocation by a wrong local admin | **fail** | `sudo` carries no authority in the model; only filesystem write to the specific admin-owned root counts; a different admin without write access to *this* root fails the probe |
| 8 | copied capability object (`copy.copy`) | **fail** | `__reduce__` raises; per-instance `_authority_seal` |
| 9 | deserialized capability (`pickle`) | **fail** | `__reduce__` raises |
| 10 | stale capability after anchor rotation | **fail** | operation-scoped + process-local; a rotated descriptor fails the next `production_writer()`; in-flight `expected_current` write rejects on registry drift |
| 11 | machine-cloned anchor | **fail** | `{device, inode}` root-identity manifest mismatch (`"HPAC root was copied or replaced"`) |
| 12 | protected-root mode weakened to group/world-writable | **fail** | `_effective_write_access` returns `True` for the agent → `_validate_production_boundary` raises → no writer |
| 13 | descriptor digest valid but provenance invalid | **fail** | `verify_record` checks the `HPAC-WRITER-PROVENANCE/1.0` closed schema + digest + store-id + root-identity-digest |
| 14 | anchor descriptor missing | **fail** | `bootstrap_authority_unproven`; ceremony STOPS |
| 15 | duplicate bootstrap (second `provision`) | **fail-closed / no-op** | create-only manifest; idempotency-conflict discipline |
| 16 | rollback to an old anchor descriptor | **fail** | provenance + root-identity binding; a stale descriptor without a matching provenance record is rejected |
| 17 | repo-supplied `principal_id` overrides ownership | **fail** | verification resolves the principal from the credential record, not caller input (RHAMP-REQ-114); `credential_principal_mismatch` |
| 18 | OS username spoof / rename | **fail** | username is never consulted (`HPAC-REQ-007`; `_SUSPICIOUS_ENV_KEY_SUBSTRINGS`) |
| 19 | agent session-identity spoof (`--agent-id`) | **fail** | `--agent-id` is not consulted for writer authority |
| 20 | process restart after capability mint | **fail** | fresh authority instance → fresh `_seal`; old capability inert |
| 21 | capability used for the wrong principal | **fail** | `require_writer(role, subject=<principal/credential id>)` mismatch |
| 22 | capability used for the wrong mutation class | **fail** | operation binding mismatch |
| 23 | capability replay for a second write | **fail** | operation-scoped; `expected_current` compare-and-write rejects a stale/duplicate mutation |
| 24 | writer store called directly, bypassing the anchor | **fail** | `HumanPrincipalRegistryStore._writer()` requires a valid `PRODUCTION` `HPACWriterCapability`; there is no other path |
| 25 | enrollment tool bypasses the writer anchor | **fail** | the tool has no other way to obtain a writer; `enroll_credential` rejects a fixture/absent capability against a `PRODUCTION` authority |

---

## 21. Implementation prerequisites / test plan / IV requirement / phase-ID derivation (phase prompt §50–§55)

### 21.1 Implementation preconditions (§50), frozen

Before the fresh implementation successor begins:

1. `HPAC-PAWA-001 v1.0` frozen (recommended contract-freeze successor) —
   descriptor schema, positive-recognition sequence, capability scope/lifetime,
   bootstrap procedure, failure taxonomy, security-claim boundaries.
2. The `<HPAC_PROTECTED_ROOT>/.authority/` deployment-owner descriptor schema
   frozen (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`, closed, HPAC-REQ-089
   canonicalisation).
3. Protected-root location frozen — **already fixed** (`resolve_hpac_protected_root()`).
4. Capability semantics frozen (§7, §15).
5. Bootstrap / provisioning procedure frozen (§14.5).
6. macOS / Linux behaviour frozen — **already** via `_effective_write_access` /
   `_ancestor_chain_safe`.
7. The consumer-inventory guard obligation frozen (the writer module is
   imported by no agent-reachable path).
8. The tests / IV plan frozen (§21.2).

### 21.2 Future test plan (§51) — no implementation in `.1R.30R`

- canonical bootstrap success (admin principal, descriptor present, probe
  passes → `PRODUCTION` writer minted, one `enroll_principal` succeeds);
- same-UID denial (agent principal / no protected root → writer unavailable);
- repo / environment / cwd redirect denial;
- invalid ownership / mode (group/world-writable root → fail);
- malformed / untrusted descriptor;
- stale / rotated descriptor;
- capability scope (wrong operation / wrong principal → reject);
- copy / `pickle` / `object.__new__` reconstruction denial;
- restart invalidation;
- direct store bypass (`HumanPrincipalRegistryStore` without a valid
  capability);
- enrollment-boundary reuse (the FIDO2 first-credential tool consumes the same
  capability boundary);
- recovery boundary (re-bootstrap requires the anchor);
- macOS / Linux `_effective_write_access` behaviour parity;
- **no runtime / effect change** (runtime posture + first-effect-absent guards
  unchanged);
- the consumer-inventory guard (writer module not importable from `cli.py` /
  `commands/**` / `core/agent.py`).

### 21.3 Independent-verification requirement (§52)

**A dedicated IV of this adjudication IS required** before implementation,
because it establishes a new production trust root. Frozen sequence:
`.1R.30R` adjudication → `.1R.30R.1` **dedicated IV of the adjudication** →
recommended `HPAC-PAWA-001 v1.0` contract-freeze → implementation → its IV →
presentation → closure IV. `.1R.30R` does **not** begin the IV.

### 21.4 Historical `.1R.30` successor rule (§53) + phase-ID derivation (§54)

CPIPC-001 v1.0 §4 grammar: a `subphase-segment` is a `numeric-segment`
(`digit{digit}[letter{letter}]`) or a `letter-segment` (`letter{letter}`).
`.1R.30` is the `numeric-segment` `30`; `.1R.30R` is the `numeric-segment`
`30R` (digits `30` + repair-letter suffix `R`). Repository precedent for a
repair/adjudication phase and its IV: `.1R.19R` → `.1R.19R.1`; `.1R.22R` →
`.1R.22R.1`; `.1R.26R` → … → `.1R.26R.1R.1R.1`; `.1R.27R`. The established
pattern is: **repair/adjudication phase carries the `R` suffix; its IV and
successors append `.N` numeric segments.**

- **Historical `.1R.30` = immutable BLOCKED.** It SHALL NOT be reused,
  resumed, or relabelled. "Resume `.1R.30`" is prohibited.
- **Fresh implementation successor ID = `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2`**
  (a new `numeric-segment` `2` appended after `.1R.30R.1`, the adjudication
  IV). It is a genuinely fresh identity that never collides with the immutable
  `.1R.30`.

### 21.5 Downstream phase-ID sequence (§55), re-derived under actual lifecycle rules

The stale RHAMP-REQ-156 tail (`.1R.31` / `.1R.32` / `.1R.33`) was
**recommended, NOT reserved** and assumed `.1R.30` would complete. Because
`.1R.30` is immutable BLOCKED, the tail is re-derived entirely under
`.1R.30R.*` (each its own explicitly human-authorized phase; IDs recommended,
NOT reserved):

| Recommended ID | Scope | Replaces |
|---|---|---|
| `.1R.30R` | **this phase** — writer-anchor architecture + contract adjudication | (new) |
| `.1R.30R.1` | **IV of `.1R.30R`** — independently re-derive the gap, the threat model, the candidate rejections, the verdict, and the phase-ID derivation | (new) |
| `.1R.30R.2` | **`HPAC-PAWA-001 v1.0` companion contract freeze** — contract-only, no `src/pcae`, no HPAC-001 bump (RHAMP-001 / REPRC-001 precedent) | (new) |
| `.1R.30R.3` | **Real FIDO2 credential registry + authentication mechanism + writer-anchor implementation** — the historical `.1R.30` scope (RHAMP-REQ-156 `.1R.30` row) resumed from the adjudicated + frozen baseline: the `PRODUCTION` writer factory + non-agent module + consumer-inventory guard; `HumanPrincipalRegistryStore` production path exercised; the §17 sidecar + §21 counter-state stores; the protected-admin enrollment + first-credential bootstrap tool; `FIDO2HumanAuthenticator`; real CTAP2 assertion verification in `hpac_verifier` (§37) incl. `FLAG.UV`; `_ELIGIBLE_MECHANISM_IDS += {hpac.fido2.uv_presence.v2}`; `terminal_reason_code` wiring. **No protected approval UI. No real approval-authority production path yet.** | old `.1R.30` + old `.1R.31`-preceding scope |
| `.1R.30R.4` | **IV of `.1R.30R.3`** — broad fixed-SHA A/B; the `.1R.28` §31 IV requirements | old `.1R.31` |
| `.1R.30R.5` | **Protected human-approval presentation + real approval-proof integration** — the process-isolated helper; `renderer_profile`; helper integrity (§30); explicit Approve/Reject; `verifier_kind = pcae-protected-local-presentation/1.0`; wire `require_real_assurance = True` through Gate 5 / Gate 9; a `PRODUCTION` `AuthenticatedHumanPrincipal` becomes obtainable for exactly one bound approval | old `.1R.32` |
| `.1R.30R.6` | **IV of `.1R.30R.5` + mandatory real-CTAP2-hardware verification (RHAMP-REQ-152) + N-16-5 closure** | old `.1R.33` |

Then N-16-6 → N-16-7 (strictly last). **No Slice C** until N-16-3..7 all
close. The IV pairing may be folded (e.g. `.1R.30R.2`'s contract-freeze IV
into `.1R.30R.4`) at the authorizing operator's discretion, matching the
`.1R.29` precedent — but a dedicated `.1R.30R.1` IV of *this adjudication* is
recommended not folded, given it establishes a new production trust root.

---

## 22. Runtime state / first external effect / carried findings (phase prompt §63–§68)

| Item | State (byte-unchanged by `.1R.30R`) |
|---|---|
| Runtime state | `Observed` |
| Maximum capability | `observe` |
| Execution availability | `unavailable` |
| Plugins | 0 |
| Capabilities | 0 |
| First external effect | **ABSENT** — no `adapter.dispatch()` call site; no Slice C |
| N-16-5 | **BLOCKED IMPLEMENTATION PREREQUISITE ADJUDICATED — IMPLEMENTATION NOT RESUMED — NOT CLOSED** |
| N-16-3 / N-16-4 | CLOSED (carried) |
| N-16-6 / N-16-7 | OPEN, untouched; N-16-7 strictly last |
| N-23-1 | INFO (carried unchanged) |
| N-23-2 | INFO / DEFERRED NORMALIZATION DEBT (carried unchanged) |
| `DELEGATED .3 FINALIZATION / COMMIT / PUSH` | **UNAUTHORIZED** — preserved |

---

## 23. Governance (phase prompt §61, §62, §69)

- **Production source policy (§61):** `git diff 8e655295 HEAD -- src/pcae` is
  **empty**. No production implementation. No non-production metadata-only
  source file was needed or added.
- **Normative contract edit policy (§60) / contract byte review (§62):**
  `git diff 8e655295 HEAD -- docs/contracts` is **empty**. No normative
  contract changed. RHAMP-001 v1.0 byte-identical to its `.1R.29` freeze;
  HPAC-001 stays v2.1; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`. The verdict
  is a **recommendation** to author `HPAC-PAWA-001 v1.0` in a dedicated
  contract-freeze successor — no contract authored here.
- **Governance rules (§69):** no raw `git commit` / `git push`, no
  `--no-verify`, no force push, no history rewrite, no hook bypass. Governed
  `pcae` lifecycle only. This adjudication document, the `PROJECT_STATUS.md` /
  `CHANGELOG.md` / `tasks/DECISIONS.md` prose, the task lifecycle, and the
  completion metadata / report were authored and committed by the primary
  human-authorized operator for `.1R.30R` through the governed `pcae`
  lifecycle. No delegated worker committed, finalized, or pushed. Only the
  primary human-authorized operator holds `.1R.30R` lifecycle authority.

---

## 24. Adjudication verdict

```
HPAC-REQ-022/023 PRODUCTION PROTECTED-ADMIN WRITER ANCHOR:

  GAP:      HPAC-001 v2.1 §7 froze the anchor POLICY (HPAC-REQ-022/023/024/080)
            and the NEGATIVE boundary (_validate_production_boundary). The
            POSITIVE half -- how PCAE recognises the external deployment-owner
            admin principal and mints a PRODUCTION HPACWriterCapability -- was
            deliberately deferred by hpac_foundation.py and is absent.

  NOT BLOCKED. The trust root is non-circular (OS filesystem write authority on
  an out-of-band-provisioned protected root), same-UID-agent-safe, offline,
  macOS+Linux portable, and directly precedented by the independently-verified
  HBDC-001 Class-B Protected-Root writer boundary.

  PREFERRED ANCHOR (Candidate E, composed):
    trust root       = OS filesystem write authority on <HPAC_PROTECTED_ROOT>,
                       agent principal provably excluded
    positive recog.  = root-identity-bound .authority/ deployment-owner
                       descriptor + _validate_production_boundary + positive
                       write probe + not-agent-identity
    capability issuer= new PRODUCTION writer factory in a non-agent-importable
                       module, consumer-inventory guarded
    capability scope = one operation, one principal/credential, process-local,
                       non-serializable, restart-invalid, non-reusable
    bootstrap        = one-time out-of-band admin provisioning; create-only;
                       non-recurring; not agent-reachable
    revocation       = admin filesystem replace/remove of the descriptor
    same-UID exclusn = no write access + no importability + seal identity +
                       __reduce__ raising + live re-probe

  CONTRACT VERDICT: B -- NEW COMPANION CONTRACT REQUIRED.
    Recommended: HPAC-PAWA-001 v1.0, authored by a dedicated contract-freeze
    successor. HPAC-001 stays v2.1 (no bump); RHAMP-001 stays v1.0
    (byte-unchanged). Companion-contract precedent: REPRC-001 / PBNDE-001 /
    RHAMP-001.

  HISTORICAL .1R.30: immutable BLOCKED -- never reused, never resumed.
  FRESH IMPLEMENTATION SUCCESSOR: 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2
  DEDICATED IV OF THIS ADJUDICATION: 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1
  DOWNSTREAM SEQUENCE: .1R.30R.1 (IV) -> .1R.30R.2 (HPAC-PAWA-001 freeze) ->
    .1R.30R.3 (mechanism + registry + writer-anchor impl) -> .1R.30R.4 (IV) ->
    .1R.30R.5 (protected presentation + real-assurance wiring) ->
    .1R.30R.6 (IV + real CTAP2 hardware + N-16-5 closure) -> N-16-6 -> N-16-7.

  NO production source change. NO contract authored. NO FIDO2. NO credential
  store. NO enrollment. NO protected presentation. NO approval proof.
  NO N-16-6 / N-16-7. NO Slice C. NO first external effect. NO execution
  enablement. Runtime Observed / observe / unavailable. First external effect
  ABSENT. N-16-5 NOT CLOSED.

  DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED -- preserved.
```
