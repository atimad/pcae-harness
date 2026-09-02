# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2 Complete — HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2
**Type:** governed contract freeze / primary-source analysis / v1.0→v1.1 semantic-delta derivation / decision-freezing / documentation
**Status:** HPAC-PAWA-001 v1.1 FROZEN AS THE SOLE NORMATIVE DELTA (MINOR) — N-16-5 PAWA v1.1 CONFIGURED-AGENT RESOLUTION CONTRACT FROZEN — DEDICATED CONTRACT IV (.1R.30R.2A.3) PENDING — IMPLEMENTATION NOT BEGUN — NOT CLOSED
**Phase-entry SHA:** `164ecef8` (task-open commit); baseline tree = the `.1R.30R.2A.1` finalized head `3f23d6fd`; `origin/main..HEAD = 0` at entry
**Production source changed:** none (`git diff 164ecef8 HEAD -- src/pcae` empty)
**Normative contracts changed:** exactly one existing contract evolved in place — `git diff --name-only 164ecef8 HEAD -- docs/contracts` names only `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (HPAC-PAWA-001 v1.0 → v1.1, MINOR); **no other contract edited and no second new contract**; HPAC-001 stays v2.1; RHAMP-001 stays v1.0 (byte-unchanged); HBDC-001 stays v1.2 (precedent only, NOT amended); the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema is byte-unchanged
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT AND UNREACHABLE; execution NOT enabled

## Summary

This phase turned the `.1R.30R.2A` adjudication (verdict **B — HPAC-PAWA-001
v1.1 MINOR**; resolution **R1**), as independently **VERIFIED WITH CORRECTIONS**
by `.1R.30R.2A.1` (**C-1** R1-HYBRID identity model, **C-2** anchor-digest
rollback binding, **C-3** dedicated contract IV, **S-1** explicit MINOR rule),
into frozen normative contract text — evolving
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` in
place from **HPAC-PAWA-001 v1.0 → v1.1** (`HPAC-PAWA-REQ-164..218` sequential, no
gaps, no duplicates; `PAWA-INV-12`). The v1.0 freeze record is **not** rewritten;
v1.1 is append-only evolution of the canonical contract file.

Primary sources read to complete relevant scope: the `.1R.30R.2A` adjudication
artifact **in full** (579 lines); the `.1R.30R.2A.1` IV artifact **in full**
(969 lines); the `.1R.30R.2` v1.0 freeze doc; HPAC-PAWA-001 **v1.0 in full**
(1775 lines); HPAC-001 v2.1 (§7 relationship); RHAMP-001 v1.0 (RHAMP-REQ-047
externalises the anchor; §49 41-code vocabulary); HBDC-001 v1.2 (§3
`PCAE_AGENT_PRINCIPAL` terminology; §13 environment-lock scope; §18
root-compromise limit — **precedent only, not amended**, exactly why R2 was
rejected); CPIPC-001 v1.0 §4. Production source read **as evidence only**
(not modified): `hpac_foundation.py` (`_validate_production_boundary` keys off
live `_current_agent_identity()` == `os.geteuid()`; `writer()` raises for every
non-fixture class), `hatp_class_b_topology_verifier.py`, `agent.py`. A
whole-tree scan for a `getpwnam` / `PCAE_AGENT_PRINCIPAL` configured-agent bridge
or a `production_writer` mint path returns **nothing** — the F-1 gap is
independently re-confirmed.

## What HPAC-PAWA-001 v1.1 freezes

- **§7A** — an explicit v1.0 → v1.1 normative delta table (Area / v1.0 / v1.1 /
  Compatibility / Reason).
- **§9.1 (`HPAC-PAWA-REQ-164..167`)** — names the concrete canonical resolution
  source: the `HPAC-PAWA-AGENT-EXCLUSION/1.0` protected record. No other source
  (`os.geteuid()`, `.pcae/agent-lock.json`, the agent registry,
  `PCAE_AGENT_PRINCIPAL` from `os.environ`, a systemd `User=` / launchd
  `UserName` / `run_as` fact, `DeploymentBinding`, the store manifest) is the
  source. `production_writer(...)` carries no account-name / uid / gids
  parameter; one leading-underscore documented fixture-only seam, guard-checked.
- **§20A (`HPAC-PAWA-REQ-168..172`, C-2)** —
  `HPAC-PAWA-CURRENT-GENERATION/1.0`'s closed field set gains **exactly one**
  additive field, `agent_exclusion_digest` (the exclusion record's
  `record_digest`); schema id kept `/1.0` (an internal installation-local
  monotonic anchor whose required shape the contract version governs — §29
  adjudication); a v1.1 recognition requires the field, a record missing it
  fails closed; recognition requires the loaded exclusion record's digest to
  equal `current-generation.agent_exclusion_digest`; bare `generation`-integer
  equality is **not** an acceptable substitute.
- **§32A (`HPAC-PAWA-REQ-173..193`)** — `HPAC-PAWA-AGENT-EXCLUSION/1.0` at
  `<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`: a load-bearing
  protected recognition input, one canonical record per installation, a
  **sibling** of `deployment-owner.json` (the descriptor schema is
  **byte-unchanged**). Closed schema: `artifact_schema_version`, `record_digest`,
  `symbolic_account` (OS account **name**), `provisioned_uid` (integrity pin,
  not the authority basis), `installation_id`, `protected_root_identity`
  (`{device, inode}`), `authority_namespace`, `generation`, `created_at`,
  `supersedes`, `provenance_ref`, `state`. **No group snapshot as authority.**
  **R1-HYBRID (C-1):** at every §33 recognition resolve `symbolic_account` live
  and require `live uid == provisioned_uid` (else `agent_principal_unknown`),
  then enumerate the account's **current** primary + supplementary groups
  **live** for the effective-write-access check. **Deletion / recreation under a
  new uid / UID reuse / rename** all fail closed to `agent_principal_unknown`
  (no silent rebind); **group drift** → `agent_has_protected_write_authority`
  → fail closed; **group removal** recovers without reprovision. The OS account
  database is inside PAWA's OS TCB (no hostile-root claim). No environment /
  caller / current-euid authority.
- **§32B (`HPAC-PAWA-REQ-194..198`)** — provisioning creates the record
  create-only alongside the descriptor (non-circular — a filesystem write + an
  OS-account-DB read); explicit `--agent-account <name>` protected-admin input;
  duplicate bootstrap fails closed or enters rotation; rotation is an explicit
  deployment-owner action (`generation += 1`, new `agent_exclusion_digest` via
  atomic anchor replace); migration re-provisions freshly under the new
  `installation_id` + `{device, inode}`.
- **§32C (`HPAC-PAWA-REQ-199..200`)** — independent exclusion-record rollback is
  **impossible** once C-2 is in effect; the full-set rollback boundary is
  unchanged from v1.0 (the single monotonic anchor + `{device, inode}` root
  identity) and is stated, not overclaimed.
- **§33 (`HPAC-PAWA-REQ-074` reworded, `HPAC-PAWA-REQ-075` extended)** — the
  recognition sequence is **still 11 steps** with unchanged required ordering;
  the v1.1 delta is that steps 2 / 3 / 7 gain explicit atomic
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` substeps. Configured-agent resolution is
  **inside atomic unit A1**. The `O_EXCL|O_NOFOLLOW` positive write probe is
  **unchanged**.
- **§31 (`HPAC-PAWA-REQ-201`)** — the not-configured-agent current-context
  comparison is concrete: live `_current_agent_identity()` vs. the resolved
  `ConfiguredAgentAuthorityIdentity`; distinct from
  `agent_has_protected_write_authority` — the **three F-1 predicates stay
  distinct**.
- **§42A (`HPAC-PAWA-REQ-202..203`)** — every v1.1 rejection maps onto an
  existing `pawa_failure_code` (#3 / #4 / #14 / #19 / #21). The taxonomy stays
  **21 closed values — no new code**.
- **§57 (`HPAC-PAWA-REQ-204`)** — the PAWA → RHAMP §49 map (#1 / #2 / #40 / #41)
  is **unchanged**; RHAMP-001 v1.0 byte-unchanged.
- **§61 / §63 (`HPAC-PAWA-REQ-205..206`)** — the two-OS-principal requirement is
  not weakened; the cross-platform normative properties are frozen (adapter
  detail: `pwd` / `grp` / `os.getgrouplist` on Linux, the macOS equivalent).
- **§73–§76 (`HPAC-PAWA-REQ-207..210`)** — future traceability (v1.1 clause →
  `hpac_pawa_agent_exclusion.py` symbol → test → guard); the new
  non-agent-importable module surface; the exclusion-record-writer /
  non-agent-importable guards; and the **dedicated `.1R.30R.2A.3` contract IV**
  requirement (**C-3**).
- **§80.1 (`HPAC-PAWA-REQ-211..213`, S-1)** — the explicit MINOR versioning rule
  plus a full HPAC-PAWA-REQ-152 MAJOR-trigger review — **none fires**.
- **§81–§84 / §87–§89 (`HPAC-PAWA-REQ-214..218`)** — v1.1 finalization
  obligations, no-test-implementation discipline, N-16-5 status.
- **`PAWA-INV-12`** — the resolution source is `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  and nothing else.
- **§95A** — append-only R1 / R2 / R3 / R4 disposition (R1-PURE → R1-HYBRID
  refinement; R2 / R3 / R4 rejected); the historical `.1R.30R.2A` verdict prose
  is not rewritten.

## Corrections incorporated

- **C-1 — R1-PURE → R1-HYBRID.** The record stores `symbolic_account` **and**
  `provisioned_uid`; every §33 recognition requires
  `pwd.getpwnam(name).pw_uid == provisioned_uid` (else `agent_principal_unknown`),
  groups still resolved live. Closes the account
  deletion → recreation-under-a-new-uid silent-rebind path; resolves the
  adjudication's §6-vs-§12.2 internal inconsistency. Additive one field; MINOR;
  the uid is **not** the authority basis (live effective write access is).
- **C-2 — anchor-digest rollback binding.** `agent_exclusion_digest` is bound
  into `HPAC-PAWA-CURRENT-GENERATION/1.0`; the adjudication's "extend the anchor
  **or** require `generation ==`" is resolved to the anchor-digest option.
- **C-3 — dedicated contract IV.** `.1R.30R.2A.3` is the recommended default;
  folding into `.1R.30R.3.2` is permitted **only** at explicit operator
  discretion. **Disclosed, NOT authorized.**
- **S-1 — explicit MINOR rule.** Codified in §80.1 / `HPAC-PAWA-REQ-211`.

## Every valid early-STOP condition checked — NONE triggered

Canonical doc §8 walks each of the phase prompt's BLOCKED conditions; none
applies. R1-HYBRID is expressible without touching HPAC-001 v2.1 or RHAMP-001
v1.0; `symbolic_account` + `provisioned_uid` safely represents an account
instance within the frozen OS-account-DB TCB; live supplementary-group
resolution is a portable normative property; deletion / recreation / UID reuse
is unambiguous after the uid-pin; the exclusion record's rollback is prevented
by binding `agent_exclusion_digest` into the current-generation anchor without
changing another contract; `HPAC-PAWA-CURRENT-GENERATION/1.0` accepts the
additive field under v1.1 semantics (`/1.0` id kept — §29 adjudication); the
artifact is a MINOR, not a MAJOR; no new `pawa_failure_code`; the descriptor
schema is unchanged; R1-HYBRID needs no environment / caller / repository
authority input; no implementation was needed to resolve a normative ambiguity;
the dedicated contract-IV phase `.1R.30R.2A.3` is derived cleanly under
CPIPC-001 §4.

## Governance

- `pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent
  · `pcae doctor task-memory` warning-only historical `tasks/DONE.md` omissions
  (pre-existing hygiene debt; no current-phase error; single active task) ·
  `pcae push check` `nothing_to_push` (before the governed push) ·
  `pcae runtime inspect` `not_implemented / Observed / observe / unavailable`,
  0/0.
- **Test evidence.** No functional implementation test authored; no functional
  success evidence manufactured. One point-in-time assertion in the
  `.1R.30R.2A.1` IV suite that pinned the v1.0 requirement total (`163`) was
  reconciled to also accept the v1.1 total (`218`) — a mechanical maintenance
  edit; **no `def test_` renamed, removed, added, skipped, or xfailed**. That
  suite is **56 passed, 0 failed** against the v1.1 contract. Two `.1R.30R.1` IV
  guards fail — **pre-existing** point-in-time guards that broke when
  `.1R.30R.2` / `.1R.30R.2A` legitimately added `docs/` artifacts since the
  B30 / V baselines; a `git stash` A/B reproduces them identically
  (`2 failed, 33 passed` both ways), and a wider `pawa` / `hpac`+`contract`
  A/B reproduces `46 failed, 214 passed, 9 errors` identically — **zero
  regression attributable to `.1R.30R.2A.2`**; re-baselined by `.1R.30R.2A.3`.
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved.
  Only the primary human-authorized operator holds `.1R.30R.2A.2` lifecycle
  authority. Governed `pcae` lifecycle only.
- No STOP / BLOCKED condition reached.

## Verdict

**HPAC-PAWA-001 v1.1: FROZEN** as the sole normative delta (MINOR).

- **N-16-5: PAWA v1.1 CONFIGURED-AGENT RESOLUTION CONTRACT FROZEN — DEDICATED
  CONTRACT IV (`.1R.30R.2A.3`) PENDING — IMPLEMENTATION NOT BEGUN — NOT CLOSED.**
- **CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE: CONTRACT FROZEN — NOT
  IMPLEMENTED.** R1-HYBRID (C-1) FROZEN. AGENT-EXCLUSION ROLLBACK BINDING (C-2)
  FROZEN. S-1 MINOR RULE FROZEN. THREE F-1 PREDICATES DISTINCT. NO ENVIRONMENT /
  CALLER / CURRENT-EUID SHORTCUT. NO NEW `pawa_failure_code`. NO MAJOR TRIGGER.
- **HPAC-001: v2.1 (NO bump). RHAMP-001: v1.0 (byte-unchanged). HBDC-001: v1.2
  (precedent only). `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema: byte-unchanged.
  Every other existing contract: byte-unchanged. `src/pcae/**`: unchanged.**
- **C-1 / C-2 / S-1: INCORPORATED. C-3 (`.1R.30R.2A.3`): RECOMMENDED, NOT
  AUTHORIZED.**

**Runtime: not_implemented / Observed / observe / unavailable. First external
effect: ABSENT AND UNREACHABLE. Execution enabled: NO. N-16-3 / N-16-4: CLOSED.
N-16-6 / N-16-7: OPEN, untouched, N-16-7 last. N-23-1 / N-23-2: carried. No
Slice C.**

## Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` — **Independent Verification of the
HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract
Freeze** (finding C-3; ID recommended, NOT reserved; requires its own separate
explicit human authorization; foldable into `.1R.30R.3.2` only at explicit
operator discretion). Then `.1R.30R.3.1` (Slice 1 — PAWA production writer
anchor + `hpac_pawa_agent_exclusion.py` + `resolve_configured_agent_identity()`;
atomic unit A1) → `.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4` (Slice 2 / IV) →
`.1R.30R.3.5` / `.3.6` (Slice 3 / IV) → `.1R.30R.4` (composite IV) →
`.1R.30R.5` (protected presentation + `require_real_assurance` wiring) →
`.1R.30R.6` (IV + mandatory real-CTAP2-hardware verification + N-16-5 closure)
→ N-16-6 → N-16-7 (strictly last). **Do not begin `.1R.30R.2A.3`. Do not begin
`.1R.30R.3.1`. Do not modify `src/pcae`. Do not modify normative contracts. Do
not implement `HPAC-PAWA-AGENT-EXCLUSION/1.0` or `resolve_configured_agent_identity()`.
Do not implement real FIDO2 / WebAuthn / CTAP. Do not access hardware
authenticators. Do not provision or write any protected root. Do not begin
N-16-6 / N-16-7 / Slice C. Do not implement or call the first external effect.
Do not enable execution.**

See `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_2A_2_HPAC_PAWA_001_V1_1_CONFIGURED_AGENT_PRINCIPAL_RESOLUTION_SOURCE_CONTRACT_FREEZE.md`
and `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
