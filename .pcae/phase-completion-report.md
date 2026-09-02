# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1 Complete — Independent Verification of the Configured-Agent-Principal Resolution Source Contract-Compatibility Adjudication

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.1
**Type:** governed independent verification of a trust-source / contract-compatibility adjudication (verification only)
**Status:** COMPLETE — ADJUDICATION VERIFIED WITH CORRECTIONS (not BLOCKED; four non-blocking findings → `.1R.30R.2A.2`)
**Verification-entry SHA (V):** `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` (== J, finalized `.1R.30R.2A` head; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff 1dbd41cb HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff 1dbd41cb HEAD -- docs/contracts` empty); HPAC-PAWA-001 stays v1.0; HPAC-001 stays v2.1; RHAMP-001 stays v1.0; HBDC-001 stays v1.2; CPIPC-001 stays v1.0. No HPAC-PAWA-001 v1.1 authored.
**Tests changed:** one new verification-only IV suite (56 tests, all passing); no existing test modified, renamed, removed, skipped, or xfailed
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; the only `adapter.dispatch(` call site is the deterministic simulation harness; real first external effect ABSENT AND UNREACHABLE; execution NOT enabled

## Immutable SHAs

| Symbol | SHA | Meaning |
|---|---|---|
| B30 | `8e65529596fc351face4b83c4b5d08573326d034` | finalized historical `.1R.30` **BLOCKED** head (immutable; never reused) |
| A | `5b45aa7b444f15852c51985879570b8913fedbe4` | finalized `.1R.30R.2` head (HPAC-PAWA-001 v1.0 freeze) — also the `.1R.30R.2A` phase-entry |
| J | `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` | finalized `.1R.30R.2A` head (adjudication) |
| V | `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` | `.1R.30R.2A.1` verification-entry (== J) |

## Summary

`.1R.30R.2A.1` independently re-derived — from HPAC-PAWA-001 v1.0, HPAC-001 v2.1,
RHAMP-001 v1.0, HBDC-001 v1.2, CPIPC-001 v1.0, and `hpac_foundation.py` /
`hatp_class_b_topology_verifier.py` / `agent.py` read as read-only evidence, not
from the `.1R.30R.2A` adjudication prose — every load-bearing conclusion.

**F-1 gap reproduced.** `HPACStoreAuthority._validate_production_boundary`
(`hpac_foundation.py:351`) evaluates the negative protected-root boundary against
`agent_uid, agent_gids = _current_agent_identity()` — which returns
`(os.geteuid(), frozenset(os.getgroups()) | {os.getegid()})`, the **live invoking
process** (docstring: *"Live process identity — never a caller-supplied value"*).
It takes **no** configured-principal parameter. On a compliant two-OS-principal
deployment the writer runs *as the deployment owner*, so this boundary would
**raise for a legitimate admin invocation** — the wrong subject. The agent
registry and `.pcae/agent-lock.json` carry logical `agent_id` strings documented
*"non-authenticating, non-authorizing"*; a whole-tree scan finds **no**
`getpwnam` / `PCAE_AGENT_PRINCIPAL` configured-agent → OS-`(uid,gids)` bridge and
**no** `production_writer` mint path (`writer()` raises
*"no production HPAC writer is implemented in this foundation phase"*).

**Three F-1 predicates distinct** (HPAC-PAWA-001 §10 matrix):
`agent_has_protected_write_authority` (the **configured** principal),
`current_context_is_agent` (the **live** process vs. the configured principal),
and the positive write probe (the **live** process, an operation). None
substitutes for another.

**R2 / R3 / R4 correctly rejected.** R2 needs an HBDC-001 amendment and violates
HPAC-PAWA-REQ-134 namespace independence. R3 (ship with no production mapping) is
fail-closed safe but permanently non-production — `.1R.30R.3.1` could never
establish the production anchor, and the blocker resurfaces at `.1R.30R.6`;
retained only as the fixture-seam test strategy. No R4 superior.

**Contract verdict B — HPAC-PAWA-001 v1.1 MINOR — confirmed.** No
HPAC-PAWA-REQ-152 MAJOR trigger fires (trust root stays OS filesystem write
authority; no signing / pinned / keychain key; the exclusion is implemented, not
collapsed). No new `pawa_failure_code` (existing #3 `agent_principal_unknown` /
#4 `agent_has_protected_write_authority` cover it). HPAC-001 v2.1 and RHAMP-001
v1.0 byte-unchanged.

**Atomicity CONFIRMED** — the resolution sits inside the §33 recognition
sequence (HPAC-PAWA-REQ-074 steps 2/3/7, REQ-075 *"fresh on every
`production_writer(...)` call"*), atomic unit A1. **D1 decomposition VALID** —
CPIPC-001 §4 EBNF admits `2A` (`numeric-segment` digit+letter) and `2A.1` /
`2A.2` (dotted numeric children); historical `.1R.30` stays immutable BLOCKED
(PAWA-INV-11).

## Verdicts

| Question | Verdict |
|---|---|
| Final verification | **ADJUDICATION VERIFIED WITH CORRECTIONS** (not BLOCKED; four non-blocking findings) |
| F-1 gap | **CONFIRMED — independently reproduced** |
| Three F-1 predicates | **DISTINCT** — not substitutable |
| Selected identity model | **R1-HYBRID** — protected symbolic account name **+** `provisioned_uid`, live `getpwnam` equality + live group enumeration, digest bound into the current-generation anchor (`.1R.30R.2A` selected R1-PURE; corrected here by C-1 + C-2) |
| R2 / R3 / R4 | **REJECTED** — verified (R2 needs an HBDC amendment / wrong namespace; R3 permanently non-production; R4 none superior) |
| New authority input | **YES** — normative delta, not implementation detail |
| Contract | **HPAC-PAWA-001 v1.1 MINOR REQUIRED** — no MAJOR trigger; no new `pawa_failure_code`; no descriptor schema change; `HPAC-PAWA-CURRENT-GENERATION/1.0` gains one field (C-2); HPAC-001 v2.1 / RHAMP-001 v1.0 byte-unchanged |
| Atomicity | **CONFIRMED** — §33 unit A1 |
| D1 decomposition | **VALID** — CPIPC-001 §4 |
| Contract-freeze successor | **`.1R.30R.2A.2`** |
| Historical `.1R.30` | immutable BLOCKED — byte-unchanged; never reused, never resumed |

## Non-blocking findings (→ `.1R.30R.2A.2`)

- **C-1 — adopt R1-HYBRID.** Store the symbolic OS account name **and** a
  `provisioned_uid`; at every §33 recognition require
  `pwd.getpwnam(name).pw_uid == provisioned_uid` (else `agent_principal_unknown`),
  with groups still enumerated **live**. Closes the account
  deletion → recreation-under-a-new-uid **silent-rebind** path and resolves
  `.1R.30R.2A`'s §6-vs-§12.2 internal inconsistency ("bound expectation" vs.
  "no uid integer"). Additive one field; MINOR (tightens a bound, REQ-153); the
  authority basis stays live effective-write-access, not the uid.
- **C-2 — bind rollback into the generation anchor.** The exclusion record's
  `record_digest` SHALL be bound into `HPAC-PAWA-CURRENT-GENERATION/1.0` via an
  `agent_exclusion_digest` field — resolve `.1R.30R.2A`'s "extend the anchor
  **or** require `generation ==`" to the anchor-digest option. A bare
  generation-integer equality does not make independent rollback impossible; the
  anchor-digest binding does.
- **C-3 — dedicated contract IV as the default.** Recommend `.1R.30R.2A.3` (a
  dedicated HPAC-PAWA-001 v1.1 contract IV) rather than folding that IV into
  `.1R.30R.3.2`, because the artifact is a **new protected authority input** —
  matching every prior link in this chain. Folding remains acceptable at the
  authorizing operator's explicit discretion.
- **S-1 — codify the MINOR rule.** The `.1R.30R.2A.2` freeze SHOULD add an
  explicit versioning-rule line stating that adding a closed, generation-bound
  protected recognition-input artifact that resolves (not widens) an
  already-required authority input is a **MINOR**, so the classification is
  verbatim rather than re-derived from the absence of a MAJOR trigger.

## Evidence

New IV suite `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_configured_agent_resolution_source_iv.py`
— **56 tests, all passing** — verification-only: reads production source,
contracts, and git history as read-only evidence; imports no production module
(AST-checked); changes no `src/pcae` / `docs/contracts` / runtime state; removes
/ renames / skips / xfails no `def test_` (AST-checked). `git diff 1dbd41cb HEAD
-- src/pcae` and `-- docs/contracts` are both **empty**. 11 pre-existing
repo-wide failures reproduce **identically** with this phase's changes removed
via `git stash -u` — the `.1R.31` `hpac_foundation` independent-verification
`test_blocking_reproduction_*` group (9),
`test_current_module_not_in_hmic_frozen_scope`, and two now-stale `.1R.30R.1`
point-in-time IV guards (`test_no_contract_change_since_b30`,
`test_only_iv_artifacts_changed_since_v`) that broke when `.1R.30R.2`
legitimately froze HPAC-PAWA-001 v1.0 (a future `.1R.30R.4` composite IV
re-baselines the latter per HPAC-PAWA-REQ-145). **Zero regression attributable
to `.1R.30R.2A.1`.**

## Scope discipline

No writer-anchor mechanism, no HPAC-PAWA-001 v1.1 text, no
`hpac_pawa_agent_exclusion.py`, no `resolve_configured_agent_identity()`, no
provisioning / `set-agent-exclusion` script, no FIDO2 / CTAP, no
`_ELIGIBLE_MECHANISM_IDS` change, no `verifier_kind` addition, no sidecar /
counter-state store, no enrollment / bootstrap tool, no protected presentation
helper, no approval proof, no `PRODUCTION` `AuthenticatedHumanPrincipal`, no
`require_real_assurance` wiring, no guard reconciliation, no hardware access. No
N-16-6 / N-16-7 / Slice C work; no real `adapter.dispatch()` call site added; no
real first external effect; no execution enablement. Historical `.1R.30`
preserved byte-unchanged and immutable BLOCKED.

## Carried findings

N-16-3 CLOSED. N-16-4 CLOSED. **N-16-5: RESOLUTION-SOURCE ADJUDICATION VERIFIED
WITH CORRECTIONS — CONTRACT FREEZE PENDING — IMPLEMENTATION NOT BEGUN — NOT
CLOSED.** N-16-6 / N-16-7 OPEN, not begun (N-16-7 strictly last). N-23-1 INFO;
N-23-2 INFO / DEFERRED — carried unchanged. `DELEGATED .3 FINALIZATION / COMMIT
/ PUSH: UNAUTHORIZED` — preserved.

## Governance

`pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent
· `pcae doctor task-memory` warning-only historical `DONE.md` omissions
(pre-existing hygiene debt; no current-phase error; one active task) · `pcae
runtime inspect` `not_implemented / Observed / observe / unavailable`, 0/0.
Governed `pcae` lifecycle only — no raw `git commit` / `git push`, no
`--no-verify`, no force push, no history rewrite, no hook bypass. Only the
primary human-authorized operator holds `.1R.30R.2A.1` lifecycle authority.

## Verdict

```
IV OF THE CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE ADJUDICATION (.1R.30R.2A.1):
                              ADJUDICATION VERIFIED WITH CORRECTIONS — NOT BLOCKED
                              (four non-blocking findings -> .1R.30R.2A.2)
F-1 GAP                        CONFIRMED — independently reproduced
                               (_validate_production_boundary uses live
                               _current_agent_identity == os.geteuid(); no
                               getpwnam/PCAE_AGENT_PRINCIPAL bridge; no
                               production_writer mint path)
THREE PREDICATES               DISTINCT — not substitutable
SELECTED MODEL                 R1-HYBRID (symbolic account name + provisioned_uid,
                               live getpwnam equality + live groups, digest bound
                               into the current-generation anchor)
R2 / R3 / R4                   REJECTED — verified
NEW AUTHORITY INPUT            YES — normative delta
CONTRACT VERDICT               HPAC-PAWA-001 v1.1 MINOR REQUIRED — no MAJOR
                               trigger; no new pawa_failure_code
HPAC-001 / RHAMP-001           byte-unchanged
ATOMICITY                      CONFIRMED — §33 unit A1
D1 DECOMPOSITION               VALID — CPIPC-001 §4; historical .1R.30 immutable
                               BLOCKED (PAWA-INV-11)
CONTRACT FREEZE                149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2
CONTRACT-FREEZE IV             recommend a dedicated .1R.30R.2A.3 (C-3)
NO src/pcae CHANGE             git diff 1dbd41cb HEAD -- src/pcae : empty
NO CONTRACT CHANGE             git diff 1dbd41cb HEAD -- docs/contracts : empty
RUNTIME                        not_implemented / Observed / observe / unavailable
FIRST EXTERNAL EFFECT          ABSENT AND UNREACHABLE
N-16-5                         NOT CLOSED
DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved
```

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2` — HPAC-PAWA-001 v1.1
Configured-Agent-Principal Resolution Source Contract Freeze** (ID recommended,
NOT reserved; requires its own separate explicit human authorization).
Contract-only: no `src/pcae`, no HPAC-001 bump, RHAMP-001 v1.0 byte-unchanged. It
SHALL append a `HPAC-PAWA-AGENT-EXCLUSION/1.0` section and the resolution-source
naming in §9 / §10, incorporating **C-1** (R1-HYBRID: `symbolic_account` +
`provisioned_uid`, live equality check, live groups), **C-2**
(`agent_exclusion_digest` bound into `HPAC-PAWA-CURRENT-GENERATION/1.0`), and
**S-1** (explicit MINOR versioning-rule line). No new `pawa_failure_code`. No
descriptor schema change. Then, at the authorizing operator's discretion,
**`.1R.30R.2A.3`** (dedicated HPAC-PAWA-001 v1.1 contract IV — **C-3**; disclosed,
NOT authorized) or a fold of that IV into `.1R.30R.3.2`; then `.1R.30R.3.1`
(Slice 1) → `.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4` (Slice 2 / IV) →
`.1R.30R.3.5` / `.3.6` (Slice 3 / IV) → `.1R.30R.4` (composite IV) →
`.1R.30R.5` (protected presentation + `require_real_assurance` wiring) →
`.1R.30R.6` (IV + mandatory real-CTAP2-hardware verification + N-16-5 closure) →
N-16-6 → N-16-7 (strictly last). Do not begin N-16-6 / N-16-7 / Slice C; do not
implement or call the first external effect; do not enable execution.

Full analysis:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_1_INDEPENDENT_VERIFICATION_OF_THE_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_COMPATIBILITY_ADJUDICATION.md`.
