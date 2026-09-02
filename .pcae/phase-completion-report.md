# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A Complete — Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A
**Type:** governed trust-source / contract-compatibility adjudication phase (adjudication only)
**Status:** COMPLETE — ADJUDICATED (not BLOCKED)
**Verdict:** **B — HPAC-PAWA-001 v1.1 MINOR required. Selected resolution: R1.**
**Phase-entry SHA:** `5b45aa7b444f15852c51985879570b8913fedbe4` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff 5b45aa7b HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff 5b45aa7b HEAD -- docs/contracts` empty); HPAC-PAWA-001 stays v1.0; HPAC-001 stays v2.1; RHAMP-001 stays v1.0; HBDC-001 stays v1.2
**Tests changed:** none (`git diff 5b45aa7b HEAD -- tests` empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

Full primary-source reconstruction for the planned PAWA writer-anchor
implementation (`.1R.30R.3.1`) discovered that **HPAC-PAWA-001 v1.0 §33 + finding
F-1** (`.1R.30R.1` §11.1) require the production `production_writer` recognition
sequence to evaluate protected-root write authority held by the **CONFIGURED PCAE
agent principal** (HPAC-PAWA-REQ-021 / 022 / 026 / 061 / 062 / 063) — explicitly
**not** `os.geteuid()` of the invoking process — while current production code has
**no canonical bridge** from PCAE's configured logical agent identity
(`claude-local`, …) to an enforceable OS `(uid, gids)`.

This adjudication independently **CONFIRMED** the gap, re-derived the F-1
predicates, analysed the identity-model threat space (group drift, UID reuse,
account rename, rollback, same-UID topology), compared **R1 / R2 / R3** and an
**R4** search, selected one production-safe canonical source, and determined the
exact HPAC-PAWA-001 contract impact.

## Confirmed gap (independently, from source)

| Source read | What it carries | Configured OS identity? |
|---|---|---|
| `policy.py` `DEFAULT_AGENT_REGISTRY` / `agent.py` `KNOWN_AGENTS` | logical `agent_id` + `kind` + `roles` | **no** |
| `.pcae/agent-lock.json` (`agent.py` `AgentLock` / `build_agent_lock_data`) | `agent_id`, `acquired_at`, `git_branch`, `active_task` | **no** — *"descriptive only … non-authenticating, non-authorizing"* |
| `hatp_class_b_topology_verifier._current_agent_identity()` | `(os.geteuid(), os.getgroups() \| {os.getegid()})` | **live process, not configured** |
| `hatp_bootstrap.inspect_bootstrap_environment` | `os.getuid()` compare; persists nothing | live; ephemeral |
| `hatp_environment_lock_verifier._check_*` | takes `agent_uid, agent_gids` as **parameters** (from `_current_agent_identity()`) | **live** |
| `DeploymentBinding` / `HPAC-STORE-AUTHORITY/1.0` manifest / HBDC-001 §13 env lock | deployment root, `{device,inode}`, HPAC/HATP `principal_id` | **no OS uid** |

`grep -rn "getpwnam\|getpwuid\|getgrnam\|getgrgid\|getgrouplist" src/pcae | grep -v test`
→ only `hatp_class_b_topology_verifier.py:323/328` (resolve an ACL-entry *name*
against the already-known **live** `agent_uid` — not a configured-agent source).
`grep -rn "PCAE_AGENT_PRINCIPAL\|configured_agent" src/pcae | grep -v test` → 0.
`grep -rn "HPACAuthorityClass.PRODUCTION\|production_writer" src/pcae | grep -v test`
→ no PRODUCTION `HPACWriterCapability` mint path; no consumable deployment-owner object.

## F-1 predicates — re-derived, kept distinct

| Predicate | Subject identity | Same as the others? |
|---|---|---|
| `agent_has_protected_write_authority` (§26) | the **configured** PCAE agent principal, resolved to `(uid,gids)` | **NO** |
| `current_context_is_agent` (§31) | the **live invoking OS process** vs. the configured principal | **NO** |
| positive write probe (§28) | the **live invoking OS process** — an operation, not a claim | (`os.geteuid()` legitimate here) |

## Adjudication result

**Not BLOCKED.** A production-safe, source-supported, additive resolution exists.

**Selected: R1** — a new protected artifact
`<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`, closed schema
**`HPAC-PAWA-AGENT-EXCLUSION/1.0`** (final wording frozen by `.1R.30R.2A.2`):
`configured_agent_account` (the **symbolic OS account name** — *no uid integer*),
`installation_id` (== the descriptor's), `protected_root_identity` (`{device,inode}`),
`generation`, `created_at`, `provenance_ref`, `state`, `record_digest`.
Deployment-owner provisioned by `scripts/hpac_protected_root_admin.py` (create-only
per generation, alongside `deployment-owner.json`); agent-unwritable
(`.authority/` mode `0700`); **non-circular** bootstrap (no capability, no FIDO2,
no prior principal — PAWA-INV-4); `(uid, gids)` resolved **live** from `pwd`/`grp`
at every §33 recognition — the only model that detects post-provision
privilege-group drift and UID reuse; rollback caught by the
`HPAC-PAWA-CURRENT-GENERATION/1.0` anchor exactly as a superseded descriptor is
(§21); **separate record, transitively bound** — the frozen descriptor
`configured_agent_exclusion_binding` (kind + basis) is **unchanged** and the
descriptor schema is **not touched**.

**Rejected:** **R2** (HBDC env-lock binding — would need an HBDC-001 amendment, a
second frozen contract whose own v1.1/v1.2 amendments are PENDING IV; violates
HPAC-PAWA-REQ-134 namespace independence). **R3** as the resolution (ship with no
production mapping — fail-closed-safe but **permanently non-production**; `.3.1`
could only be partial and the blocker resurfaces at `.1R.30R.6`, which the phase
prompt forbids deferring; the fixture seam is retained as the **test strategy**).
**No superior R4** (no existing installation principal record; folding the name
into the closed descriptor contradicts §14 / HPAC-PAWA-REQ-037).

## Contract verdict — B: HPAC-PAWA-001 v1.1 MINOR

None of HPAC-PAWA-REQ-152's MAJOR triggers apply (all are
weakening / widening / redesign). R1 does not change the trust root, weakens no
wall, and **implements** a recognition input the frozen contract already requires
and §9 / §73 already anticipate the implementing phase naming. **No new
`pawa_failure_code`** (reuses `#3 agent_principal_unknown`,
`#4 agent_has_protected_write_authority`); the 21-code taxonomy and the
PAWA→RHAMP `#1/#2/#40/#41` map are unchanged; HPAC-001 v2.1 and RHAMP-001 v1.0
byte-unchanged; **no descriptor schema change**. Structurally the same move as
HPAC-001 v2.1's own MINOR ("adds one closed binding object … widens no authority").
Not A (a new protected recognition input is normative, not implementation
detail — HPAC-PAWA-REQ-001). Not E (a resolution exists).

## Atomicity, decomposition, successors

- **Atomicity CONFIRMED:** configured-agent resolution + the §26/§31 evaluations
  are inside the same atomic §33 recognition unit as descriptor /
  current-generation / write-probe / mint (PAWA-INV-3) — atomic unit **A1** of
  `.1R.30R.3.1`.
- **D1 phase decomposition VALIDATED** (CPIPC-001 v1.0 §4 grammar) and refined:
  `.1R.30R.2A` → **`.2A.1` (dedicated IV)** → `.2A.2` (HPAC-PAWA-001 v1.1 freeze;
  its IV MAY fold into `.3.2`) → `.3.1` (Slice 1: PAWA production writer anchor) →
  `.3.2` (IV) → `.3.3`/`.3.4` (Slice 2: RHAMP credential registry +
  sidecar/counter stores + enrollment/bootstrap tool / IV) → `.3.5`/`.3.6`
  (Slice 3: real FIDO2 authenticator + native CTAP2 verify + mechanism allowlist
  + terminal-reason wiring / IV) → `.4` (composite IV + broad fixed-SHA A/B) →
  `.5` (protected presentation + `require_real_assurance` — unchanged) → `.6`
  (IV + mandatory real-CTAP2-hardware + N-16-5 closure — unchanged).
- **Dedicated IV = YES** (`.1R.30R.2A.1`); **contract-freeze successor = YES**
  (`.1R.30R.2A.2`).

## Boundaries held

`git diff 5b45aa7b HEAD -- src/pcae` empty; `-- docs/contracts` empty;
`-- tests` empty. HPAC-PAWA-001 v1.0 **not edited**; historical `.1R.30`
immutable BLOCKED; `.1R.30R` / `.1R.30R.1` / `.1R.30R.2` records unchanged.
Runtime `not_implemented / Observed / observe / unavailable`; 0 plugins / 0
capabilities. FIRST EXTERNAL EFFECT: ABSENT. No human authenticated; no
approval; no PB permission; no Runtime Enforcement change; no execution was enabled.
N-16-5 **NOT CLOSED**. N-16-3 / N-16-4 CLOSED. N-16-6 / N-16-7 OPEN, untouched,
N-16-7 strictly last. N-23-1 / N-23-2 carried unchanged.

## Recommended next phase (exactly one)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1` — Independent Verification of the
Configured-Agent-Principal Resolution Source Contract-Compatibility
Adjudication.** Requires its own separate explicit human authorization
(ID recommended, NOT reserved). **Do not begin it.**

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
