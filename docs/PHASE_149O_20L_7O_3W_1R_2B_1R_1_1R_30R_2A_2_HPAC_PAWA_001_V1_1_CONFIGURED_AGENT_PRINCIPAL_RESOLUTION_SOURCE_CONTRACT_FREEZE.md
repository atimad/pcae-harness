# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.2 — HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze

**Status: COMPLETE — HPAC-PAWA-001 v1.1 FROZEN** as the sole normative delta
(**MINOR**). Contract-freeze / primary-source analysis / semantic-delta
derivation / decision-freezing / documentation only. **No `src/pcae` change.**
**No HPAC-001 bump.** **RHAMP-001 v1.0 byte-unchanged.** **No new
`pawa_failure_code`.** **No descriptor schema change.** The v1.0 freeze record is
**not** rewritten — v1.1 is append-only evolution of the canonical contract file.

**Phase-entry SHA:** `164ecef8` (task-open commit); baseline tree = the
`.1R.30R.2A.1` finalized head `3f23d6fd`; `git rev-list --count origin/main..HEAD`
= 0 at entry.

**Type:** governed contract-freeze phase (one existing normative contract evolved
in place: `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`,
HPAC-PAWA-001 v1.0 → v1.1).

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 1. Why this phase exists

Full primary-source reconstruction for the planned PAWA implementation
(`.1R.30R.3.1`, the writer-anchor slice) discovered that HPAC-PAWA-001 v1.0
requires the production `production_writer` recognition sequence (§33) to
evaluate protected-root write authority **held by the CONFIGURED PCAE agent
principal** — explicitly **not** `os.geteuid()` of the invoking process — while
current production code has **no canonical bridge** from PCAE's configured
logical agent identity to an enforceable OS principal identity `(uid, gids)`
(finding **F-1** of `.1R.30R.1` §11.1).

- `.1R.30R.2A` **adjudicated** the gap: verdict **B — HPAC-PAWA-001 v1.1 MINOR**;
  resolution **R1** — a dedicated protected `.authority/agent-exclusion.json`
  record (`HPAC-PAWA-AGENT-EXCLUSION/1.0`), symbolic OS account name, `(uid,
  gids)` resolved live.
- `.1R.30R.2A.1` independently **VERIFIED WITH CORRECTIONS**: the R1 *direction*
  (protected record + live resolution) is sound; R2 / R3 / R4 are correctly
  rejected; the change is a normative delta; the bump is **MINOR** with no MAJOR
  trigger; HPAC-001 v2.1 and RHAMP-001 v1.0 need no change; the resolution is
  atomic with §33; the D1 decomposition is CPIPC-001-valid. Four corrections:
  **C-1** (R1-PURE → R1-HYBRID identity model), **C-2** (anchor-digest rollback
  binding), **C-3** (dedicated contract IV), **S-1** (explicit MINOR rule).

This phase turns that verdict, as corrected, into frozen normative contract text.

---

## 2. Deliverable — the v1.0 → v1.1 evolution (in place)

`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` is
evolved in place from **v1.1**-titled with:

| Addition | Location | Requirements |
|---|---|---|
| v1.0 → v1.1 normative delta table | **§7A** | (table, no new REQ) |
| named resolution source in §9 | **§9.1** | `HPAC-PAWA-REQ-164..167` |
| per-predicate matrix rows for the exclusion source | **§10** | (matrix rows) |
| `agent_exclusion_digest` on `HPAC-PAWA-CURRENT-GENERATION/1.0` (**C-2**) | **§20A** | `HPAC-PAWA-REQ-168..172` |
| `HPAC-PAWA-AGENT-EXCLUSION/1.0` — closed schema, `symbolic_account`, `provisioned_uid`, live resolution, deletion / recreation / UID-reuse / rename, live groups, group drift / removal, OS-account-DB TCB, no env / no caller / no euid | **§32A** | `HPAC-PAWA-REQ-173..193` |
| provisioning / account selection / duplicate bootstrap / rotation / migration of the exclusion record | **§32B** | `HPAC-PAWA-REQ-194..198` |
| coordinated / full-root rollback boundary | **§32C** | `HPAC-PAWA-REQ-199..200` |
| §33 recognition sequence — 11 steps unchanged; steps 2 / 3 / 7 gain explicit atomic `HPAC-PAWA-AGENT-EXCLUSION/1.0` substeps | **§33** | `HPAC-PAWA-REQ-074` (reworded), `HPAC-PAWA-REQ-075` (extended) |
| not-configured-agent current-context comparison — concrete (v1.1) | **§31** | `HPAC-PAWA-REQ-201` |
| v1.1 rejection cases → the existing 21 codes | **§42A** | `HPAC-PAWA-REQ-202..203` |
| RHAMP mapping unchanged (v1.1) | **§57** | `HPAC-PAWA-REQ-204` |
| same-UID / two-principal requirement not weakened | **§61** | `HPAC-PAWA-REQ-205` |
| macOS / Linux normative properties for the resolution | **§63** | `HPAC-PAWA-REQ-206` |
| contract-production traceability (v1.1 clauses) | **§73** | `HPAC-PAWA-REQ-207` |
| future source surface (`hpac_pawa_agent_exclusion.py`) | **§74** | `HPAC-PAWA-REQ-208` |
| future consumer / source guards | **§75** | `HPAC-PAWA-REQ-209` |
| dedicated v1.1 contract IV requirement (**C-3**) | **§76** | `HPAC-PAWA-REQ-210` |
| explicit MINOR versioning rule (**S-1**) + v1.1 MAJOR-trigger review | **§80.1** | `HPAC-PAWA-REQ-211..213` |
| existing-contract byte identity / no-src-change / contract-scope (v1.1) | **§81 / §82 / §83** | `HPAC-PAWA-REQ-214..216` |
| no test implementation (v1.1) | **§84** | `HPAC-PAWA-REQ-217` |
| N-16-5 status (v1.1) | **§87** | `HPAC-PAWA-REQ-218` |
| `PAWA-INV-12` | **§92** | (invariant) |
| v1.1 requirement / invariant inventory | **§91** | `218` requirements, `12` invariants |
| v1.1 contract-freeze verdict blocks | **§90.1 / §95.1** | — |
| R1 / R2 / R3 / R4 append-only design disposition | **§95A** | (table) |
| v1.1 versioning history | **§94** | — |
| recommended next phase (`.1R.30R.2A.3`) | **§96A** | — |

**Requirement inventory:** `HPAC-PAWA-REQ-001` through `HPAC-PAWA-REQ-218`,
sequential, no gaps, no duplicates (v1.0 additions were 001..163; v1.1 additions
are 164..218). Invariants `PAWA-INV-1` through `PAWA-INV-12`.

---

## 3. Primary sources (read to complete relevant scope, as evidence)

- `.1R.30R.2A` adjudication artifact **in full** (579 lines).
- `.1R.30R.2A.1` IV artifact **in full** (969 lines) — C-1 / C-2 / C-3 / S-1.
- `.1R.30R.2` HPAC-PAWA-001 v1.0 freeze doc.
- HPAC-PAWA-001 **v1.0 in full** (1775 lines) — §2, §9, §10, §14, §16, §17,
  §19, §20, §21, §22, §23, §24, §25–§33, §34, §35, §42–§49, §56, §57, §61,
  §63, §73–§80, §90–§96.
- HPAC-001 v2.1 (`HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`) — §7 relationship;
  byte-unchanged.
- RHAMP-001 v1.0 (`REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md`)
  — RHAMP-REQ-047 externalises the anchor; §49 41-code vocabulary;
  byte-unchanged.
- HBDC-001 v1.2 (`HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) — §3 `PCAE_AGENT_PRINCIPAL`
  terminology; §13 environment lock (Python-execution-environment scope only);
  §18 root-compromise limit; **precedent only, not amended** — this is precisely
  why R2 was rejected.
- CPIPC-001 v1.0 (`CANONICAL_PHASE_ID_PARSING_CONTRACT.md`) — §4 grammar;
  `.1R.30R.2A` / `.2A.1` / `.2A.2` / `.2A.3` are grammar-valid `numeric-segment`
  (`2` + `A`) with dotted children; historical `.1R.30` immutable BLOCKED.
- Production source read **as evidence only** (not modified):
  `src/pcae/core/hpac_foundation.py` (`HPACStoreAuthority._validate_production_boundary`
  keys off live `_current_agent_identity()` == `os.geteuid()`; `writer()` raises
  for every non-fixture class), `src/pcae/core/hatp_class_b_topology_verifier.py`
  (`_current_agent_identity()` docstring "Live process identity"),
  `src/pcae/core/agent.py` (`agent_id` "non-authenticating, non-authorizing").
  A whole-tree scan for a `getpwnam` / `PCAE_AGENT_PRINCIPAL` configured-agent
  bridge or a `production_writer` mint path returns **nothing** — the F-1 gap is
  independently re-confirmed.

---

## 4. The authoritative design — R1-HYBRID (C-1)

`<HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json`, closed schema
**`HPAC-PAWA-AGENT-EXCLUSION/1.0`** (§32A.1), a protected, deployment-owner-
provisioned, agent-unwritable, installation- and generation-bound record that
stores:

- **`symbolic_account`** — the provisioned OS account **name** of the configured
  PCAE agent principal (§32A.2). Established only by out-of-band protected
  administration; not caller-, environment-, or repository-controlled.
- **`provisioned_uid`** — the numeric uid resolved for `symbolic_account` at
  provisioning time (§32A.3). An **account-instance continuity pin**, not the
  authority basis. It does **not** reintroduce "uid as an authority input"
  (HPAC-PAWA-REQ-037 sense): the authority basis remains live effective
  filesystem write access.
- `installation_id`, `protected_root_identity` (`{device, inode}`), `generation`,
  `created_at`, `supersedes`, `provenance_ref`, `record_digest`, `state`.
- **No persisted group snapshot** as authority (§32A.6, PAWA-INV-12).

**At every §33 PAWA production recognition** (§33 steps 2 / 3 / 7 substeps):

1. load the trusted current exclusion record no-follow; validate its closed
   schema / digest / ownership / mode / `installation_id` / `{device, inode}` /
   `state == ACTIVE`;
2. verify `record_digest` == `current-generation.json`'s `agent_exclusion_digest`
   (C-2, §20A);
3. resolve `symbolic_account` live through the OS account database; require
   `live uid == provisioned_uid` (C-1) — else `agent_principal_unknown`;
4. enumerate the account's **current** primary + supplementary groups live;
5. evaluate the resolved `(uid, gids)` against the canonical protected root:
   `_effective_write_access(root, …) == False` **and** `_ancestor_chain_safe(root,
   …) == True` — else `agent_has_protected_write_authority`, fail closed;
6. compare live `_current_agent_identity()` against the resolved configured-agent
   `(uid, gids)` — equal ⇒ `current_context_is_agent`, fail closed.

**Rollback binding (C-2):** `agent_exclusion_digest` is added to
`HPAC-PAWA-CURRENT-GENERATION/1.0` (§20A). A restored older exclusion record
whose digest ≠ the anchor's fails closed; independent rollback is impossible
without forging the monotonic anchor (deployment-owner / root write, in the TCB).
Bare `generation`-integer equality is **not** an acceptable substitute.

---

## 5. Adversarial behaviour — frozen (§32A.5 / §32A.6)

| Adversary | Frozen behaviour |
|---|---|
| Account deletion | `symbolic_account` absent ⇒ `agent_principal_unknown` ⇒ deny. No fallback to `provisioned_uid` alone. |
| Recreation under a **different** uid | live uid ≠ `provisioned_uid` ⇒ `agent_principal_unknown` ⇒ deliberate protected reprovision (§32B.4). **No silent rebind** (this is the R1-PURE sharp edge C-1 closes). |
| UID reuse (uid reassigned to another account) | name lookup mandatory; no reverse-uid fallback ⇒ deny. |
| Account rename | old `symbolic_account` unresolvable ⇒ `agent_principal_unknown` ⇒ explicit reprovision. No silent follow of the old uid. |
| Group drift (agent added to a root-writable group) | live group enumeration sees it ⇒ `agent_has_protected_write_authority` ⇒ fail closed. **This is the load-bearing reason a name is stored and groups are resolved live rather than snapshotted.** |
| Group removal | reflected live; the deployment MAY become eligible again **with no reprovision** if every other §33 predicate is current — a reduction in the agent's authority strictly strengthens the exclusion property. |
| Restored superseded exclusion record | digest ≠ `current-generation.agent_exclusion_digest` ⇒ fail closed (C-2). |
| Copied exclusion record from another installation | `installation_id` / `{device, inode}` mismatch ⇒ fail closed (PAWA-INV-5, PAWA-INV-12). |
| Hostile OS root altering the account database | outside the threat model — the OS account database is inside PAWA's TCB (§32A.7, PAWA-INV-6). No overclaim. |
| Single-account host / agent has ACL/group write to the root | resolved configured-agent `(uid, gids)` can write ⇒ `agent_has_protected_write_authority` ⇒ REAL `PRODUCTION` writer issuance INELIGIBLE, fail closed — never a downgrade (§61 / HPAC-PAWA-REQ-205, PAWA-INV-7). |

---

## 6. Three F-1 predicates — kept distinct (§10 / §31 / §33)

| # | Predicate | Subject | Source | Live / configured |
|---|---|---|---|---|
| A | `agent_has_protected_write_authority` (§26, step 3) | the **configured** PCAE agent principal | `HPAC-PAWA-AGENT-EXCLUSION/1.0` → `ConfiguredAgentAuthorityIdentity` | **configured** |
| B | `current_context_is_agent` (§31, step 7) | the **current invoking OS process** vs. the configured agent principal | live `_current_agent_identity()` **+** the resolved configured identity | both operands |
| C | positive write probe (§28, step 8) | the **current invoking OS process** | a live `O_EXCL\|O_NOFOLLOW` create-and-unlink under `.authority/` | **live** (`os.geteuid()` correct here) |

None substitutes for another. `os.geteuid()` is the subject of C and one operand
of B — **never** the operand of A (finding F-1; §33 / §10 / HPAC-PAWA-REQ-193 /
HPAC-PAWA-REQ-201).

---

## 7. Contract-version verdict — MINOR (S-1, §80.1)

**No HPAC-PAWA-REQ-152 MAJOR trigger fires** (§80.1 / HPAC-PAWA-REQ-212): the
authority basis stays live effective filesystem write access; the exclusion is
*implemented*, not collapsed; same-UID still fails closed; fully local (`pwd` /
`grp` are local NSS reads); the capability semantics are untouched; the bootstrap
trust root is unchanged; C-2 *binds into* the generation / rollback protection; no
signing key / pinned key / keychain is added; the consumer inventory is not
wildcarded.

**S-1 rule frozen (HPAC-PAWA-REQ-211):** *adding a closed, generation-bound,
deployment-owner-provisioned, agent-unwritable protected recognition-input
artifact that concretely resolves — but does not widen, weaken, or redefine — an
authority predicate the frozen contract already requires is a MINOR evolution.*
Direct precedent: HPAC-001 v2.1 was itself a MINOR that "adds one closed binding
object … widens no authority."

**No new `pawa_failure_code`** (§42A): every v1.1 rejection maps onto existing
#3 `agent_principal_unknown` / #4 `agent_has_protected_write_authority` / #14
`current_context_is_agent` / #19 `duplicate_bootstrap` / #21 `internal_fail_closed`.
The PAWA → RHAMP §49 map (#1 / #2 / #40 / #41) is unchanged; RHAMP-001 v1.0 is
byte-unchanged (§57 / HPAC-PAWA-REQ-204).

**`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema is byte-unchanged.** The account
identity lives in the sibling `HPAC-PAWA-AGENT-EXCLUSION/1.0` record; the
descriptor's frozen `configured_agent_exclusion_binding` still records only
*kind* + *basis* (§32A / HPAC-PAWA-REQ-174; HPAC-PAWA-REQ-037 preserved).

**`HPAC-PAWA-CURRENT-GENERATION/1.0` gains exactly one field**,
`agent_exclusion_digest`, keeping its `/1.0` schema id (an internal
installation-local monotonic anchor whose required shape the contract version
governs — §20A / HPAC-PAWA-REQ-169; §29 adjudication).

---

## 8. Every valid early-STOP / BLOCKED condition checked — NONE triggered

| Prompt BLOCKED condition | Result |
|---|---|
| R1-HYBRID cannot be expressed without modifying HPAC-001 v2.1 | **not triggered** — R1-HYBRID lives entirely in HPAC-PAWA-001's own namespace; HPAC-001 §7 already defers the mechanism. |
| RHAMP-001 v1.0 must change | **not triggered** — RHAMP-REQ-047 externalises the anchor; the §49 map already covers `agent_principal_unknown` / `agent_has_protected_write_authority`. |
| `symbolic_account` + `provisioned_uid` cannot safely represent an account instance under the frozen macOS/Linux TCB | **not triggered** — the OS account database is already inside PAWA's TCB (HPAC-PAWA-REQ-018); the name + uid-pin is a strict tightening. |
| live supplementary-group resolution cannot be specified portably | **not triggered** — §63 / HPAC-PAWA-REQ-206 freezes the property, not one API (`os.getgrouplist` on Linux, the `grp` equivalent on macOS). |
| deletion/recreation or UID reuse remains ambiguous after symbolic-account + `provisioned_uid` equality | **not triggered** — C-1's `live uid == provisioned_uid` pin makes every case a clean fail-closed (§32A.5). |
| agent-exclusion rollback cannot be prevented without changing another contract | **not triggered** — `agent_exclusion_digest` extends only `HPAC-PAWA-CURRENT-GENERATION/1.0`, an internal anchor (§20A). |
| `HPAC-PAWA-CURRENT-GENERATION/1.0` cannot accept the additive digest field under v1.1 semantics | **not triggered** — §29 adjudication: an internal monotonic anchor whose shape the contract version governs; additive closed field, `/1.0` id kept. |
| the new record introduces a MAJOR rather than MINOR authority change | **not triggered** — §80.1 / HPAC-PAWA-REQ-212: no MAJOR trigger fires. |
| a new `pawa_failure_code` is required | **not triggered** — §42A: all map onto the existing 21. |
| the descriptor schema must change incompatibly | **not triggered** — descriptor byte-unchanged. |
| R1-HYBRID requires environment/caller/repository authority inputs | **not triggered** — §32A.8 / HPAC-PAWA-REQ-191..193: none permitted; a single fixture-only seam, guard-checked. |
| implementation would need to begin to resolve a normative ambiguity | **not triggered** — every normative property is stated in text; `.1R.30R.3.1` implements, it does not decide. |
| the dedicated contract-IV phase cannot be derived cleanly under CPIPC rules | **not triggered** — `.1R.30R.2A.3` is grammar-valid (§76 / §96A; CPIPC-001 §4). |

---

## 9. Governance

- `pcae health` **healthy** · `pcae check` **passed** · `pcae status coherence`
  **coherent** · `pcae doctor task-memory` warning-only historical `tasks/DONE.md`
  omissions (pre-existing hygiene debt from earlier phases; no current-phase
  error) · `pcae push check` `nothing_to_push` (before the governed push) ·
  `pcae runtime inspect` `not_implemented` / `Observed` / `observe` /
  `unavailable`, 0 plugins / 0 capabilities.
- **Test evidence.** No functional implementation test authored; no functional
  success evidence manufactured (HPAC-PAWA-REQ-217). One **point-in-time**
  assertion in the `.1R.30R.2A.1` IV suite that pinned the v1.0 requirement
  total (`163`) was reconciled to also accept the v1.1 total (`218`) — a
  mechanical maintenance edit; **no `def test_` renamed, removed, skipped, or
  xfailed**. `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_configured_agent_resolution_source_iv.py`
  is **56 passed, 0 failed** against the v1.1 contract.
- **Regression attribution.** Two `.1R.30R.1` IV guards
  (`test_no_contract_change_since_b30`, `test_only_iv_artifacts_changed_since_v`)
  fail — they are **pre-existing** point-in-time guards that broke when
  `.1R.30R.2` / `.1R.30R.2A` legitimately added `docs/` artifacts since the
  B30 / V baselines; they reproduce **identically** with this phase's changes
  stashed (`git stash` A/B confirmed: `2 failed, 33 passed` both ways). A wider
  A/B over the `pawa` / `hpac`+`contract` / `contract_identity` / `writer_anchor`
  selection reproduces **`46 failed, 214 passed, 9 errors` identically** with and
  without this phase's changes — **zero regression attributable to
  `.1R.30R.2A.2`.** These stale guards are re-baselined by `.1R.30R.2A.3` (the
  dedicated v1.1 contract IV).
- **DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** — preserved. Only
  the primary human-authorized operator holds `.1R.30R.2A.2` lifecycle
  authority. Governed `pcae` lifecycle only — no raw `git commit` / `git push`,
  no `--no-verify`, no force push, no history rewrite, no hook bypass.

---

## 10. Boundaries held

- `git diff 164ecef8 HEAD -- src/pcae` → **empty**.
- `git diff --name-only 164ecef8 HEAD -- docs/contracts` → names **exactly**
  `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v1.1) and **no other contract**.
- HPAC-001 v2.1, RHAMP-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPSE-001 v1.1,
  HHCE-001, `HPAC-AUTHORITY-CONSUMPTION` (`/2.1`), HBDC-001 v1.2, REPRC-001 v1.0,
  PBNDE-001 v1.0, RDGO-001 v3.1, RPAC-001 v1.0, CPIPC-001 v1.0, the RE No-Go
  Registry, and every other unrelated contract: **byte-unchanged**.
- `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema: **byte-unchanged**.
- No `hpac_pawa_agent_exclusion.py`, no `resolve_configured_agent_identity()`,
  no `HPAC-PAWA-AGENT-EXCLUSION/1.0` schema helper, no `pwd` / `grp` call, no
  writer-anchor implementation, no `HumanPrincipalRegistryStore` production
  writer path, no FIDO2 / CTAP / WebAuthn code, no `_ELIGIBLE_MECHANISM_IDS`
  change, no `verifier_kind` addition, no sidecar / counter-state store, no
  enrollment / bootstrap tool, no protected presentation helper, no approval
  proof, no `PRODUCTION` `AuthenticatedHumanPrincipal`, no `require_real_assurance`
  wiring, no provisioning-script change. No hardware accessed, enumerated, or
  prompted; no CTAP device I/O.
- Historical `.1R.30` (immutable BLOCKED), `.1R.30R`, `.1R.30R.1`, `.1R.30R.2`,
  `.1R.30R.2A`, `.1R.30R.2A.1` records: **byte-unchanged**. HPAC-PAWA-001 v1.0
  freeze record not rewritten — v1.1 is append-only.
- **N-16-5:** NOT CLOSED — the configured-agent-principal resolution-source gap
  is closed **at the contract level** by `HPAC-PAWA-AGENT-EXCLUSION/1.0`;
  closure still requires the dedicated `.1R.30R.2A.3` contract IV, `.1R.30R.3.*`
  implementation, `.1R.30R.4` composite IV, `.1R.30R.5` presentation +
  `require_real_assurance` wiring, and `.1R.30R.6` (IV + mandatory
  real-CTAP2-hardware verification).
  **N-16-3 / N-16-4:** CLOSED, not reopened. **N-16-6 / N-16-7:** OPEN,
  untouched, N-16-7 strictly last. **N-23-1 / N-23-2:** carried unchanged.
  **No Slice C.**
- **Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins / 0 capabilities — byte-unchanged.
- **First external effect:** ABSENT AND UNREACHABLE. No `adapter.dispatch(`
  path added; no subprocess / Popen / os.system / socket / http / provider path
  introduced. No execution enabled.

---

## 11. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` — Independent Verification of the
HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze**
(finding **C-3**; ID recommended, **NOT reserved**; requires its own separate
explicit human authorization). A fold into `.1R.30R.3.2` is permitted **only at
the authorizing operator's explicit discretion**. Minimum scope: HPAC-PAWA-REQ-210
— independently verify the closed `HPAC-PAWA-AGENT-EXCLUSION/1.0` schema and the
`agent_exclusion_digest` current-generation delta; the R1-HYBRID identity model;
that account deletion / recreation-under-a-new-uid / UID reuse / rename each fail
closed; that group drift is detected and group removal recovers without
reprovision; that the three F-1 predicates stay distinct; that no new
`pawa_failure_code` and no RHAMP edit is required; that the descriptor schema is
byte-unchanged; that HPAC-001 v2.1 / RHAMP-001 v1.0 / HBDC-001 v1.2 are
byte-unchanged; that the v1.1 delta is MINOR under §80; and that `git diff
<2A.2-entry> HEAD -- src/pcae` is empty.

Then `.1R.30R.3.1` (Slice 1 — PAWA production writer anchor +
`hpac_pawa_agent_exclusion.py` + `resolve_configured_agent_identity()`; atomic
unit A1) → `.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4` (Slice 2 / IV) →
`.1R.30R.3.5` / `.3.6` (Slice 3 / IV) → `.1R.30R.4` (composite IV) → `.1R.30R.5`
(protected presentation + `require_real_assurance` wiring through Gate 5 / Gate 9)
→ `.1R.30R.6` (IV + mandatory real-CTAP2-hardware verification + **N-16-5
closure**) → N-16-6 → N-16-7 (strictly last).

**Do not begin `.1R.30R.2A.3`. Do not begin `.1R.30R.3.1`. Do not begin N-16-6 /
N-16-7 / Slice C. Do not implement or call the first external effect. Do not
enable execution.**

---

## 12. Verdict block

```
HPAC-PAWA-001 v1.1 CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE CONTRACT FREEZE
(.1R.30R.2A.2)

FINAL VERDICT            HPAC-PAWA-001 v1.1 — FROZEN (MINOR; sole normative delta)

PHASE-ENTRY SHA         164ecef8 (task-open); baseline tree 3f23d6fd
                        (.1R.30R.2A.1 finalized head); origin/main..HEAD = 0 at entry
RESOLUTION SOURCE       HPAC-PAWA-AGENT-EXCLUSION/1.0 at
                        <HPAC_PROTECTED_ROOT>/.authority/agent-exclusion.json (§32A)
IDENTITY MODEL          R1-HYBRID (C-1) — symbolic_account + provisioned_uid;
                        live getpwnam(name).pw_uid == provisioned_uid;
                        live primary + supplementary group enumeration;
                        authority basis = live effective filesystem write access
CLOSED SCHEMA           §32A.1 — 12 fields, no group snapshot as authority
DELETE / RECREATE       symbolic_account absent -> agent_principal_unknown;
(NEW UID) / UID REUSE   live uid != provisioned_uid -> agent_principal_unknown
/ RENAME                (deliberate reprovision) — all fail closed, no silent rebind
GROUP DRIFT             detected via live groups -> agent_has_protected_write_authority
GROUP REMOVAL           reflected live; recovers with no reprovision
OS ACCOUNT DB           inside PAWA's OS TCB — no hostile-root claim
ROLLBACK (C-2)          agent_exclusion_digest bound into
                        HPAC-PAWA-CURRENT-GENERATION/1.0 (§20A); restored
                        superseded record -> fail closed; independent rollback
                        IMPOSSIBLE without forging the monotonic anchor
CURRENT-GEN SCHEMA      +1 field (agent_exclusion_digest); schema id kept /1.0
                        (§20A / §29 adjudication)
DESCRIPTOR SCHEMA       BYTE-UNCHANGED
THREE F-1 PREDICATES    DISTINCT — agent_has_protected_write_authority (configured),
                        current_context_is_agent (live vs configured), positive
                        write probe (live operation)
§33 SEQUENCE            11 steps unchanged; steps 2/3/7 gain explicit atomic
                        HPAC-PAWA-AGENT-EXCLUSION/1.0 substeps
NO ENV / CALLER / EUID  frozen (§32A.8) — one fixture-only seam, guard-checked
PAWA FAILURE TAXONOMY   21 closed codes UNCHANGED; v1.1 rejections -> #3/#4/#14/#19/#21
RHAMP MAPPING           #1/#2/#40/#41 UNCHANGED; RHAMP-001 v1.0 byte-unchanged
POSITIVE WRITE PROBE    O_EXCL|O_NOFOLLOW — UNCHANGED
MAJOR TRIGGER           none fires (§80.1 / HPAC-PAWA-REQ-212)
VERSIONING RULE         S-1 codified (§80.1 / HPAC-PAWA-REQ-211)
HPAC-001 / RHAMP-001 /  byte-unchanged
HBDC-001
R1 / R2 / R3 / R4       R1-HYBRID FROZEN; R1-PURE superseded (C-1); R2 rejected
                        (needs HBDC amendment, wrong namespace); R3 rejected as
                        the resolution (test-seam only); R4 no superior option
DEDICATED CONTRACT IV   .1R.30R.2A.3 (C-3) — recommended default; fold into
                        .1R.30R.3.2 only at explicit operator discretion
D1 DECOMPOSITION        VALID (CPIPC-001 §4); .2A/.2A.1/.2A.2/.2A.3 grammar-valid;
                        historical .1R.30 immutable BLOCKED (PAWA-INV-11)
REQUIREMENT INVENTORY   HPAC-PAWA-REQ-001..218 sequential no gaps; PAWA-INV-1..12
NO src/pcae CHANGE      git diff 164ecef8 HEAD -- src/pcae : empty
CONTRACT DIFF           git diff --name-only 164ecef8 HEAD -- docs/contracts :
                        exactly HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md
RUNTIME                 not_implemented / Observed / observe / unavailable ; 0/0
FIRST EXTERNAL EFFECT   ABSENT AND UNREACHABLE
N-16-5                  NOT CLOSED (contract-level gap closed; dedicated contract
                        IV + implementation pending)
N-16-6 / N-16-7         OPEN, untouched, N-16-7 strictly last ; NO Slice C
N-23-1 / N-23-2         carried unchanged
GOVERNANCE INCIDENT     DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved

RECOMMENDED NEXT PHASE  149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3 — Independent
                        Verification of the HPAC-PAWA-001 v1.1 Configured-Agent-
                        Principal Resolution Source Contract Freeze. Own explicit
                        human authorization required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

See `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
(HPAC-PAWA-001 v1.1) and the `.1R.30R.2A` / `.1R.30R.2A.1` artifacts.
