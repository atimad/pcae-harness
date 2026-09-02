# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3 — Independent Verification of the HPAC-PAWA-001 v1.1 Configured-Agent-Principal Resolution Source Contract Freeze

**Status: COMPLETE — HPAC-PAWA-001 v1.1 VERIFIED WITH NON-BLOCKING FINDINGS.**
Independent, re-derived-from-primary-source verification of the v1.1 contract
frozen by `.1R.30R.2A.2` (finding **C-3** — a dedicated contract IV for the new
`HPAC-PAWA-AGENT-EXCLUSION/1.0` protected authority-input artifact).

**VERIFICATION ONLY.** No `src/pcae` change. No normative-contract edit. No
`HPAC-PAWA-AGENT-EXCLUSION/1.0` / `resolve_configured_agent_identity()` /
writer-anchor / FIDO2 / protected-presentation implementation. No runtime change.
First external effect ABSENT AND UNREACHABLE.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

---

## 1. Phase identity and entry state

| Field | Value |
|---|---|
| Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2A.3` |
| Verification-entry SHA (`V`) | `6c62a323cccda56e969128d4b6e01f98d53630ce` (== `F`) |
| `A` — finalized `.1R.30R.2A.1` head | `3f23d6fd4a6812cdb4d2f6f7d2c0e2edd2511667` |
| `F` — finalized `.1R.30R.2A.2` head (v1.1 freeze) | `6c62a323cccda56e969128d4b6e01f98d53630ce` |
| `B30` — immutable `.1R.30` BLOCKED head | `8e65529596fc351face4b83c4b5d08573326d034` |
| `J` — finalized `.1R.30R.2A` head | `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a` |
| `origin/main..HEAD` at entry | `0` |
| Active governed phase at entry | none (idle) |
| Runtime at entry | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities |
| First external effect at entry | ABSENT |

**SHA derivation.** `V == F` because `.1R.30R.2A.2` finalized with
`origin/main..HEAD = 0` and no commit preceded this phase's task-open. `A` is the
`.1R.30R.2A.1` "reconcile governed push state" head; `F` is the `.1R.30R.2A.2`
"reconcile governed push state" head — both independently confirmed by
`git log -1 --format=%s`. `B30`'s subject contains `1R.30:` and `BLOCKED`;
historical `.1R.30` is immutable **BLOCKED** (`PAWA-INV-11`), neither reused nor
resumed by any part of the `.2A*` chain.

---

## 2. Primary sources read (as read-only evidence)

- **HPAC-PAWA-001 v1.1** — `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (2604 lines), read in full for §2, §7A, §9.1, §10, §14, §20, §20A, §21, §26,
  §27, §28, §31, §32, §32A, §32B, §32C, §33, §34, §42A, §56, §57, §61, §63,
  §73–§76, §80/§80.1, §81–§85, §87–§89, §90/§90.1, §91–§96/§96A.
- The complete `git diff 164ecef8 6c62a323 -- <contract>` (the entire v1.0 → v1.1
  patch — 881 insertions, 51 deletions) — re-derived line by line.
- `.1R.30R.2A.2` freeze artifact **in full** (426 lines).
- `.1R.30R.2A.1` IV artifact — §7.7 (C-1), §7.11 (C-2), §10.2 (S-1), §13.2 (C-3).
- `.1R.30R.2A` adjudication artifact — verdict B, resolution R1.
- `.1R.30R.2` HPAC-PAWA-001 v1.0 freeze doc.
- HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, CPIPC-001 v1.0 — headers +
  last-touch commits.
- HPAC-PAWA-001 §14 (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema) and §56
  (`pawa_failure_code` table) — full text, both compared byte-for-byte across the
  v1.0 → v1.1 window.
- `.1R.30R.1` and `.1R.30R.2A.1` IV suites — read to identify the point-in-time
  guards the freeze doc scheduled for re-baselining here (Finding F-1 below).

Production source was **not** read for this phase (contract-level IV; the
`.1R.30R.2A.1` IV already re-confirmed the F-1 gap in `src/pcae`, and this phase
verifies frozen text, not implementation). `git diff <V> HEAD -- src/pcae` is
independently confirmed empty.

---

## 3. Exact v1.0 → v1.1 normative delta (independently re-derived)

The sole changed normative file is the PAWA contract, evolved **in place**. The
delta is confined to these sections; nothing else in the contract moved.

| # | Section | v1.0 | v1.1 | Security effect | Compatibility | Verified |
|---|---|---|---|---|---|---|
| 1 | Title / §"Contract identity" | `v1.0` | `v1.1`, `Evolved to v1.1 by .2A.2`, delta pointer, adjudication baseline | none (metadata) | MINOR | ✅ |
| 2 | §7A (new) | — | v1.0 → v1.1 delta table | documents the delta | MINOR | ✅ |
| 3 | §2 terminology | "not `os.geteuid()`" | + names `HPAC-PAWA-AGENT-EXCLUSION/1.0` as the concrete source; + `ConfiguredAgentAuthorityIdentity` term (authority basis = live effective write access, never the uid) | tightens F-1 predicate | MINOR | ✅ |
| 4 | §9.1 (new) | — | `HPAC-PAWA-REQ-164..167` — the named resolution source; no other source; `production_writer` carries no account param; one fixture-only seam | resolves an unresolvable predicate | MINOR (S-1) | ✅ |
| 5 | §10 matrix | 6 predicate rows | + "agent-exclusion record trust" row; the exclusion row's source column made concrete (`symbolic_account` + `provisioned_uid`, `(uid,gids)` live) | per-predicate identity clarity | MINOR | ✅ |
| 6 | §20A (new) | `HPAC-PAWA-CURRENT-GENERATION/1.0` closed 6-field set | closed **7**-field set — adds `agent_exclusion_digest`; schema id kept `/1.0`; `HPAC-PAWA-REQ-168..172` | binds exclusion-record currentness into the single monotonic anchor (**C-2**) | additive; MINOR (§29 adjudication) | ✅ |
| 7 | §31 | negative assertion vs configured principal | + `HPAC-PAWA-REQ-201` — concrete: live `_current_agent_identity()` uid vs resolved configured uid; no `agent_id` label; group-set equality alone ≠ identity; distinct from predicate A | keeps predicate B distinct | MINOR | ✅ |
| 8 | §32A (new) | — | `HPAC-PAWA-REQ-173..193` — the closed `HPAC-PAWA-AGENT-EXCLUSION/1.0` schema (§32A.1, 12 fields), `symbolic_account` (§32A.2), `provisioned_uid` (§32A.3, C-1), live resolution (§32A.4), deletion / recreation / UID-reuse / rename (§32A.5), live groups + drift + removal (§32A.6), OS-account-DB TCB (§32A.7), no env / no caller / no euid (§32A.8) | **the freeze** | MINOR (S-1) | ✅ |
| 9 | §32B (new) | — | `HPAC-PAWA-REQ-194..198` — provisioning, account selection, duplicate-bootstrap, rotation, migration of the exclusion record | additive lifecycle | MINOR | ✅ |
| 10 | §32C (new) | — | `HPAC-PAWA-REQ-199..200` — independent-rollback impossibility; full-set rollback boundary stated, not overclaimed | tightening + honesty | MINOR | ✅ |
| 11 | §33 | 11-step sequence | **11 steps** — steps 2 / 3 / 7 gain explicit atomic `HPAC-PAWA-AGENT-EXCLUSION/1.0` substeps; `HPAC-PAWA-REQ-074` reworded, `-075` extended | no step-count change; atomic | MINOR | ✅ |
| 12 | §42A (new) | — | `HPAC-PAWA-REQ-202..203` — every v1.1 rejection → existing `pawa_failure_code` #3/#4/#14/#19/#21; no new code; genuine unmappable case ⇒ BLOCKED | no vocabulary expansion | MINOR | ✅ |
| 13 | §57 | 41-code RHAMP map, 4 target codes | + `HPAC-PAWA-REQ-204` — map unchanged; RHAMP-001 v1.0 byte-unchanged | none | no change | ✅ |
| 14 | §61 | two-OS-principal requirement | + `HPAC-PAWA-REQ-205` — same-UID / group-drift coincidence ⇒ `agent_has_protected_write_authority` ⇒ fail closed; a concrete source is not a reason to relax | not weakened | no change | ✅ |
| 15 | §63 | cross-platform `_effective_write_access` | + `HPAC-PAWA-REQ-206` — freezes the properties (name lookup, uid pin, live group enumeration, write-authority eval), not one OS API | portable | MINOR | ✅ |
| 16 | §73–§76 | v1.0 IV / traceability spec | + `HPAC-PAWA-REQ-207` (v1.1 clause → symbol → test map), `-208` (new `hpac_pawa_agent_exclusion.py`), `-209` (guards, no wildcard), `-210` (dedicated IV — this phase) | spec for `.1R.30R.3.1` | additive | ✅ |
| 17 | §80 / §80.1 | `HPAC-PAWA-REQ-151/152/153` | + `-211` (S-1 rule), `-212` (MAJOR-trigger review — none fires), `-213` (MAJOR triggers preserved) | codifies MINOR | additive | ✅ |
| 18 | §81–§84 | v1.0 byte-identity / no-src / scope / no-test | + `-214..217` — v1.1 equivalents; one point-in-time req-count assertion MAY be reconciled | tightens finalization proof | additive | ✅ |
| 19 | §87 | N-16-5 v1.0 status | + `-218` — v1.1 status: contract-level gap closed, dedicated IV + implementation pending, **NOT CLOSED** | status | additive | ✅ |
| 20 | §90.1 / §95.1 (new) | v1.0 verdict blocks | v1.1 verdict blocks | summary | additive | ✅ |
| 21 | §91 | 163 requirements / 11 invariants | **218** requirements (`001..218`, sequential, no gaps) / **12** invariants; `PAWA-INV-12` (§92) | inventory | additive | ✅ |
| 22 | §92 | `PAWA-INV-1..11` | + `PAWA-INV-12` — the resolution source is `HPAC-PAWA-AGENT-EXCLUSION/1.0` and nothing else | codifies the freeze | additive | ✅ |
| 23 | §93 | self-consistency (v1.0) | reworded for v1.1: 001..218 sequential; descriptor schema untouched | statement | additive | ✅ |
| 24 | §94 | v1.0 history | + v1.1 history paragraph — MINOR, append-only, dedicated IV before `.1R.30R.3.1` | history | additive | ✅ |
| 25 | §95A (new) | — | R1-PURE (superseded by C-1) / R1-HYBRID (FROZEN) / R2 (rejected — HBDC amendment + wrong namespace) / R3 (rejected as resolution; retained as test seam) / R4 (rejected — no superior source) | design record | append-only | ✅ |
| 26 | §96A (new) | v1.0 recommended next | recommends `.1R.30R.2A.3` (this phase), then `.1R.30R.3.1..6` → N-16-6 → N-16-7 | recommendation | additive | ✅ |

**No unrelated semantic change exists.** Every hunk in `git diff 164ecef8
6c62a323` maps to a row above. The v1.0 requirement bodies `001..163` are
byte-unchanged except `HPAC-PAWA-REQ-074` (reworded to say "11 steps" and add the
step-2 substeps) and `-075` (one extended clause) — both consistent with the
delta table and neither changing step count, ordering, or any failure mapping.

---

## 4. Contract identity — VERIFIED

`HPAC-PAWA-001 v1.1` is consistently identified in: the H1 title; the "Contract
identity and status" block (`**Version:** 1.1`, `**Status:** FROZEN`); §7A; §80
(`v1.1 is a MINOR evolution`); §91 (requirement inventory); §94 (history); the
`.1R.30R.2A.2` freeze artifact; `PROJECT_STATUS.md`; `CHANGELOG.md`;
`tasks/DECISIONS.md`. The v1.0 verdict block (§90) and v1.0 recommended-next
(§96) are retained verbatim beside their v1.1 counterparts (§90.1 / §96A) — the
v1.0 freeze record is **not** rewritten. No stale normative v1.0 self-reference
alters semantics: every remaining "v1.0" mention is historical/append-only.

---

## 5. `HPAC-PAWA-AGENT-EXCLUSION/1.0` closed-schema field matrix — VERIFIED (closed)

| Field | Required | Meaning | Authority-bearing | Caller-controlled | Currentness role | Digest-covered |
|---|---|---|---|---|---|---|
| `artifact_schema_version` | yes | const `HPAC-PAWA-AGENT-EXCLUSION/1.0` | no (schema gate) | no | — | yes |
| `record_digest` | yes | self-excluding SHA-256 over canonical bytes (HPAC-REQ-089) | no (integrity) | no | binds record bytes; must equal `current-generation.agent_exclusion_digest` | self |
| `symbolic_account` | yes | provisioned OS account **name**; grammar `^[A-Za-z_][A-Za-z0-9_.-]{0,63}$` | **indirectly** — resolves live to `(uid,gids)` | **no** (protected admin only) | resolved live every §33 | yes |
| `provisioned_uid` | yes | numeric uid at provisioning time — **account-instance continuity pin, not the authority basis** | **no** (integrity pin) | no | `live getpwnam(name).pw_uid == provisioned_uid` every §33 | yes |
| `installation_id` | yes | `hpawi-<hex32>`; MUST equal descriptor + current-generation `installation_id` | no | no | equality every validation | yes |
| `protected_root_identity` | yes | `{device, inode}` of `<HPAC_PROTECTED_ROOT>` | no | no | equality with live root + store manifest | yes |
| `authority_namespace` | yes | const `.authority` | no | no | — | yes |
| `generation` | yes | int ≥ 1 — provision/rotation generation | no | no | monotonic; `supersedes` shape-checked | yes |
| `created_at` | yes | RFC3339 UTC from a trusted clock | no | no | — | yes |
| `supersedes` | yes | `null` at first generation; else `{previous_generation, previous_record_digest}` | no | no | monotonicity check | yes |
| `provenance_ref` | yes | `HPAC-WRITER-PROVENANCE/1.0` record key for this write | no | no | resolves to a valid provenance record for the current root | yes |
| `state` | yes | closed token `{ACTIVE, SUPERSEDED, REVOKED}` | no (gate: only `ACTIVE` recognised) | no | `state == ACTIVE` required | yes |

**Closed.** `set(document) != {…}` → the record is faulted (`agent_principal_unknown`,
§42A). `HPAC-PAWA-REQ-176` explicitly bars: a persisted group snapshot as an
authority input; a free-form "authorized" string; operator name / email / civil
identity; `is_admin`; a capability field; a `deployment_owner` field; any path
other than the const `authority_namespace`. **No authority-relevant field is left
ambiguous or caller-controlled.** `HPAC-PAWA-REQ-177` enumerates the full
validation. **VERIFIED — no early-STOP condition (no authority-critical field is
ambiguous or caller-controlled).**

---

## 6. Identity-model challenges — R1-HYBRID VERIFIED

| Prompt challenge | Frozen behaviour (contract clause) | Verdict |
|---|---|---|
| **`symbolic_account` source** (§9) | established **only** by out-of-band protected administration (§32A.2 / §32B.2); **not** caller / env / repo / current-euid / shell-username / agent-lock-label-derived; grammar-bounded name, not a uid / display-name / path | **VERIFIED** |
| **`provisioned_uid` role** (§10) | numeric uid captured at protected provisioning from the trusted account-DB lookup of `symbolic_account`; an **integrity / continuity pin**, explicitly **not** the sole identity, **not** live authority state, **not** human identity; authority basis stays live effective filesystem write access (§32A.3) | **VERIFIED** |
| **live uid equality** (§11) | every §33 recognition: lookup succeeds **and** `live uid == provisioned_uid`, else `agent_principal_unknown`; **no alternate fallback**; not cached across calls (§32A.4) | **VERIFIED** |
| **account deletion** (§12) | `symbolic_account` absent ⇒ `agent_principal_unknown` ⇒ no writer; **no fallback to `provisioned_uid` alone** (`HPAC-PAWA-REQ-183`) | **VERIFIED** |
| **same-name recreation, new uid** (§13) | `live uid != provisioned_uid` ⇒ reject (`agent_principal_unknown`) ⇒ deliberate protected reprovision (§32B.4); **no silent rebind** — this is exactly the R1-PURE sharp edge C-1 closes (`HPAC-PAWA-REQ-184`) | **VERIFIED** |
| **UID reuse** (§14) | name lookup mandatory; **no reverse-uid fallback** ("find the account whose uid == `provisioned_uid`" is forbidden); the original name is deleted or resolves to a different uid ⇒ reject (`HPAC-PAWA-REQ-185`) | **VERIFIED** |
| **account rename** (§15) | old `symbolic_account` no longer resolves ⇒ reject (`agent_principal_unknown`); explicit reprovision required; **no fallback to `provisioned_uid`**; implementation SHALL NOT silently follow the old uid to a new name (`HPAC-PAWA-REQ-186`) | **VERIFIED** |
| **live group resolution** (§16) | current primary **and** supplementary groups enumerated **live** every §33 recognition, fed as `gids` to `_effective_write_access` / `_ancestor_chain_safe`; **never persisted as authoritative current state** (`PAWA-INV-12`); the *property* is frozen, not one OS API (`HPAC-PAWA-REQ-187`) | **VERIFIED** |
| **group drift** (§17) | agent added post-provisioning to a root-writable group ⇒ next §33 sees it live ⇒ `_effective_write_access` returns `True` ⇒ `agent_has_protected_write_authority` ⇒ **fail closed**; stated as the *load-bearing reason* a name is stored and groups resolved live — **normative, not explanatory prose** (`HPAC-PAWA-REQ-188`) | **VERIFIED** |
| **group removal** (§18) | live resolution reflects the lower authority at the next recognition; the deployment **MAY become eligible again with no reprovision**, provided every other §33 predicate is current; a strengthening change needs no currentness/rotation event (`HPAC-PAWA-REQ-189`) | **VERIFIED — immediate recovery explicitly allowed** |
| **OS account DB — TCB** (§19) | `pwd` / `grp` / NSS (or platform equivalent) is **inside PAWA's OS TCB**, exactly as the filesystem protection model; the contract SHALL NOT claim resistance to a hostile OS root / account-DB administrator — already outside the threat model (`HPAC-PAWA-REQ-190`). **No overclaim.** | **VERIFIED** |
| **logical → OS bridge** (§20) | exact bridge: *configured PCAE logical principal → protected provisioned `symbolic_account` binding → `provisioned_uid` continuity → live group authority resolution*; §33 evaluates the resolved OS authority identity, **never** the `agent_id` label; no `agent_id string == OS username` assumption (`HPAC-PAWA-REQ-179`) | **VERIFIED** |

---

## 7. Three F-1 predicates — DISTINCT, none substitutes (VERIFIED)

| # | Predicate | Subject | Trusted source | Failure code | Substitutable? |
|---|---|---|---|---|---|
| A | `agent_has_protected_write_authority` (§26, step 3) | the **configured** PCAE agent principal | `HPAC-PAWA-AGENT-EXCLUSION/1.0` → `ConfiguredAgentAuthorityIdentity` `(uid, gids)`; basis = live effective write access | `agent_has_protected_write_authority` (#4) | **no** |
| B | `current_context_is_agent` (§31, step 7) | the **current invoking OS process** vs. the configured principal | live `_current_agent_identity()` `(uid, gids)` **+** the step-2 resolved configured identity | `current_context_is_agent` (#14) | **no** |
| C | positive write probe (§28, step 8) | the **current invoking OS process** | live `O_EXCL \| O_NOFOLLOW` create-and-unlink under `.authority/` — an operation, not a claim | `write_probe_failed` (#11) | **no** |

- **Current-context comparison** (§22): `HPAC-PAWA-REQ-201` is concrete — live uid
  **equals** resolved configured-agent uid ⇒ `current_context_is_agent` ⇒ fail
  closed. **SHALL NOT** use a descriptive `agent_id` label; **SHALL NOT** treat
  group-set equality alone as identity. Explicitly stated **distinct** from
  predicate A. **VERIFIED.**
- **Current-euid prohibition** (§23): `HPAC-PAWA-REQ-193` — the current process's
  `os.geteuid()` / `os.getgroups()` are **not** the
  `ConfiguredAgentAuthorityIdentity` and SHALL NOT substitute for it in §33 step
  3; they remain the subject of C and one operand of B, **never** the operand of
  A. `os.geteuid()` is **never** the `agent_has_protected_write_authority`
  operand. **VERIFIED — no semantic ambiguity.**
- **Two-principal invariant** (§24): `HPAC-PAWA-REQ-205` — where the resolved
  configured-agent `(uid, gids)` and the deployment owner's effective write
  authority coincide (single-account host, or group drift),
  `_effective_write_access` returns `True` ⇒ `agent_has_protected_write_authority`
  ⇒ fail closed, no writer. "The existence of a concrete resolution source is
  **not** a reason to relax the two-OS-principal requirement." **VERIFIED — no
  exception because the exclusion mapping now exists.**

---

## 8. Generation / rollback semantics — C-2 VERIFIED

- **Installation / root binding** (§25): the record carries `installation_id`
  (== descriptor + current-generation) and `protected_root_identity`
  `{device, inode}` (== live root + `HPAC-STORE-AUTHORITY/1.0` manifest). A copied
  record from another installation carries a non-matching pair →
  `agent_principal_unknown` — it **never validates** (`HPAC-PAWA-REQ-198`,
  `PAWA-INV-5`, `PAWA-INV-12`). **VERIFIED.**
- **Generation semantics** (§26): the exclusion record participates in the
  **same** PAWA generation model as the descriptor — one monotonic
  atomic-replace `HPAC-PAWA-CURRENT-GENERATION/1.0` anchor is authoritative for
  **both**, via `descriptor_digest` and the new `agent_exclusion_digest`. No
  advisory generation (`HPAC-PAWA-REQ-172` extends the `-050` BLOCKED discipline).
  **VERIFIED.**
- **Current-generation schema** (§27): `HPAC-PAWA-REQ-168` — the closed field set
  becomes **exactly** `{artifact_schema_version, record_digest, installation_id,
  current_generation, descriptor_digest, agent_exclusion_digest, updated_at}`
  (7 fields, no additional, no missing). `HPAC-PAWA-REQ-169` — the schema id stays
  `HPAC-PAWA-CURRENT-GENERATION/1.0`, **explicitly valid** under PAWA rules
  because it is a purely internal, installation-local monotonic anchor never
  cross-referenced by an opaque schema id and never copied between installations
  as an authority claim; **HPAC-PAWA-001 v1.1 is the authority for its required
  shape**. A record missing the field is a v1.0-era anchor ⇒ **fail closed**
  (`agent_principal_unknown`), never a silent downgrade. This matches the §29
  adjudication (an internal anchor whose shape the contract version governs).
  **VERIFIED — not under-versioned.**
- **`agent_exclusion_digest`** (§28): 64-lowercase-hex SHA-256 `record_digest` of
  the current exclusion record; mandatory; validated **before** configured-agent
  authority evaluation (§33 step 2 substep); §33 requires the *currently loaded
  and validated* record's digest to equal the anchor's. **No optional / advisory
  use.** **VERIFIED.**
- **Independent rollback** (§29): a restored older `agent-exclusion.json` whose
  `record_digest != current-generation.agent_exclusion_digest` **fails closed**
  (`agent_principal_unknown`, `HPAC-PAWA-REQ-171` / `-199`); re-writing the anchor
  needs `.authority/` write authority the configured agent provably lacks. Bare
  `generation`-integer equality is **not** an acceptable substitute (C-2).
  **Independent rollback is IMPOSSIBLE. VERIFIED.**
- **Coordinated / full-set rollback boundary** (§30): `HPAC-PAWA-REQ-200` — what
  prevents rollback of the full old set (`deployment-owner.json` +
  `current-generation.json` + `agent-exclusion.json` together) is **unchanged
  from v1.0**: the single monotonic atomic-replace anchor (§20 / §21) + the
  protected-root `{device, inode}` binding (§16). C-2 does **not** claim to
  prevent a party who already holds `.authority/` write authority (the deployment
  owner, or root in the TCB) from deliberately reverting their own installation.
  **The boundary is stated, not overclaimed. TCB boundary is precise. VERIFIED.**

---

## 9. Provisioning / rotation / migration / bootstrap — VERIFIED

| Prompt § | Frozen behaviour | Verdict |
|---|---|---|
| **rotation** (§31) | explicit deployment-owner action: new record at `generation = old + 1` with `supersedes`; new provenance; atomic anchor replace with new `agent_exclusion_digest`; old record `SUPERSEDED` and no longer satisfies §33 (`HPAC-PAWA-REQ-197`) | **VERIFIED** |
| **account rename / reprovision** (§32) | explicit reprovision / rotation, never silent name migration (`HPAC-PAWA-REQ-186` / `-197`) | **VERIFIED** |
| **machine migration** (§33) | fresh exclusion binding under the new `installation_id` + `{device, inode}`; a copied file alone never validates (`HPAC-PAWA-REQ-198`) | **VERIFIED** |
| **initial bootstrap** (§34) | out-of-band `provision` also creates `agent-exclusion.json` **create-only** + writes `agent_exclusion_digest` into the anchor; requires **no** `HPACWriterCapability`, **no** FIDO2, **no** enrolled principal — a filesystem write + an OS-account-DB read, both outside PCAE's authority model (`HPAC-PAWA-REQ-194`, `PAWA-INV-4`). **Non-circular.** | **VERIFIED** |
| **provisioning account selection** (§35) | explicit `--agent-account <name>` protected-admin input; **not** current euid / `USER` / `LOGNAME` / `SUDO_USER` / repo / agent-lock label (`HPAC-PAWA-REQ-195`) | **VERIFIED** |
| **duplicate bootstrap** | a second `provision` over a live valid `ACTIVE` record fails closed (`duplicate_bootstrap`, #19) or enters rotation; byte-identical repeat is an idempotent no-op only; **never a silent authority reset** (`HPAC-PAWA-REQ-196`) | **VERIFIED** |
| **group-snapshot prohibition** (§36) | provision-time gid list SHALL NOT become current authority; a retained list, if any, is explicitly non-authoritative and SHALL NOT live in the closed record (`HPAC-PAWA-REQ-176` / `-187`, `PAWA-INV-12`) | **VERIFIED** |
| **environment prohibition** (§37) | `PCAE_AGENT_PRINCIPAL` / `USER` / `LOGNAME` / `SUDO_USER` / `SUDO_UID` SHALL NOT be the trust source and SHALL NOT override the record; an env var MAY at most *locate* protected config (`HPAC-PAWA-REQ-191`) | **VERIFIED** |
| **caller-input prohibition** (§38) | production `production_writer(...)` carries **no** `configured_agent_uid` / `configured_agent_gids` / `symbolic_account` / `agent_account` / account-name parameter; a single leading-underscore documented fixture-only keyword-only seam is the only permitted injection point, guard-checked (`HPAC-PAWA-REQ-166` / `-192`) | **VERIFIED** |

---

## 10. Failure vocabulary — 21 codes, RHAMP map unchanged (VERIFIED)

- **§39 completeness.** Every enumerated v1.1 rejection maps deterministically
  onto an existing `pawa_failure_code` (§42A / `HPAC-PAWA-REQ-202`):

  | v1.1 rejection | existing code |
  |---|---|
  | exclusion record missing / malformed / closed-field-set / digest / grammar fault | `agent_principal_unknown` (#3) |
  | `.authority/` not deployment-owner-owned / group-/other-/ACL-agent-writable | `agent_principal_unknown` (#3) |
  | `installation_id` / `{device,inode}` mismatch (incl. copied record) | `agent_principal_unknown` (#3) |
  | digest ≠ anchor `agent_exclusion_digest`; restored superseded record | `agent_principal_unknown` (#3) |
  | `state != ACTIVE` | `agent_principal_unknown` (#3) |
  | `symbolic_account` unknown / lookup raises / duplicate passwd / deleted | `agent_principal_unknown` (#3) |
  | live uid ≠ `provisioned_uid` (recreate-new-uid / rename / UID reuse) | `agent_principal_unknown` (#3) |
  | resolved configured-agent `(uid,gids)` can write root / safe ancestor (incl. group drift) | `agent_has_protected_write_authority` (#4) |
  | current invoking process resolves to the configured agent account | `current_context_is_agent` (#14) |
  | second `provision` writes a differing record over a live valid installation | `duplicate_bootstrap` (#19) |
  | unexpected fail-closed error in exclusion resolution | `internal_fail_closed` (#21) |

  The `pawa_failure_code` table (§56) is **byte-unchanged** — 21 numbered rows,
  `1..21`, independently re-parsed. `HPAC-PAWA-REQ-203` — a genuinely unmappable
  future case is **BLOCKED-on-contract-compatibility**, not a silent addition.
  **No condition lacks a semantically valid code. VERIFIED.**
- **§40 RHAMP mapping.** `HPAC-PAWA-REQ-204` — the §57 PAWA → RHAMP table is
  **unchanged**; RHAMP-001 v1.0 §49's **41**-code `terminal_reason_code`
  vocabulary is byte-unchanged; RHAMP-001 is not edited. The four target RHAMP
  codes remain `bootstrap_authority_unproven` (1), `enrollment_not_protected_admin`
  (2), `protected_root_invalid` (40), `internal_verification_error` (41) — every
  v1.1 rejection resolves to a PAWA code already on a §57 row. **VERIFIED — no new
  RHAMP terminal reason.**
  - *Non-blocking documentation nit (Finding F-2 below):* `HPAC-PAWA-REQ-204`'s
    inline prose lists "`agent_principal_unknown` / #3" mixing the PAWA-code
    ordinal (#3 in §56) with RHAMP-code ordinals (#1/#2/#41) in one sentence. The
    normative §57 table it defers to is correct and unchanged; the sentence is
    imprecise notation, not a normative defect.

---

## 11. Descriptor schema — BYTE-UNCHANGED (VERIFIED)

`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` (§14) — closed 13-field set — is
**byte-unchanged**. `git diff 164ecef8 6c62a323 -- <contract>` contains no hunk
touching the §13–§15 region. `configured_agent_exclusion_binding` still records
only `{excluded_principal_kind: "PCAE_CONFIGURED_AGENT_PRINCIPAL",
exclusion_basis: "OS_FILESYSTEM_WRITE_AUTHORITY"}` — **no** `symbolic_account`,
**no** uid / gid integer, **no** account name (`HPAC-PAWA-REQ-037` preserved). The
account identity lives in the sibling `HPAC-PAWA-AGENT-EXCLUSION/1.0` record.
**VERIFIED — no descriptor change contrary to the freeze; nothing sneaked in.**

---

## 12. Recognition sequence — 11 steps, atomic (VERIFIED)

- **§42 / §43.** `HPAC-PAWA-REQ-074` — the frozen order is **11 steps**; the
  numbered list has a step 11 and no step 12 (independently re-parsed). The v1.1
  delta is that steps 2 / 3 / 7 gain explicit atomic
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` substeps *inside step 2* — not new top-level
  steps. No conflicting 15-step normative list exists. **VERIFIED — no order
  ambiguity.**
- **Atomicity.** `HPAC-PAWA-REQ-075` (extended) — the exclusion-record load, live
  account resolution, uid-pin equality, and live group enumeration are **inside
  the same atomic recognition unit** as descriptor validation, current-generation
  checking, the write probe, and the mint; they cannot be split such that a
  `PRODUCTION` capability exists without them having run (`PAWA-INV-3`,
  `PAWA-INV-12`; atomic unit A1 of `.1R.30R.3.1`). No path where descriptor valid
  + probe succeeds + exclusion unresolved ⇒ mint. **VERIFIED.**
- **§44 write probe unchanged.** §7A row 7 — the `O_EXCL | O_NOFOLLOW`
  create-and-unlink positive probe against the live invoking process is
  **unchanged**; no `os.access()` substitution; the configured-agent mapping does
  **not** replace the probe; §34 ("No sudo / euid shortcut") is intact.
  **VERIFIED.**

---

## 13. Versioning — v1.1 MINOR VERIFIED

- **§45 R1/R2/R3/R4 disposition** (§95A, append-only): **R1-PURE** superseded by
  the independently-verified R1-HYBRID correction (C-1 — pure-symbolic silently
  rebinds on recreate-under-new-uid and contradicts the adjudication's own §6
  "bound expectation"); **R1-HYBRID** FROZEN (§32A, §20A); **R2** REJECTED (needs
  an HBDC-001 amendment — a second frozen contract evolving, and violates
  `HPAC-PAWA-REQ-134`, PAWA's source belongs in its own `.authority/` namespace);
  **R3** REJECTED as the resolution (fail-closed-safe but permanently
  production-unsatisfiable — the blocker would resurface at `.1R.30R.6`), retained
  only as the test-seam strategy (needed under R1-HYBRID too); **R4** REJECTED (no
  superior source-supported option — `DeploymentBinding` / store manifest name no
  OS principal; folding into `deployment-owner.json` is contra §14; a systemd
  `User=` / launchd `UserName` / `run_as` fact is exactly the caller/environment
  input `HPAC-PAWA-REQ-021` forbids). The historical `.1R.30R.2A` verdict prose is
  **not** rewritten. **DISPOSITION SOUND — VERIFIED.**
- **§46 S-1 wording** (`HPAC-PAWA-REQ-211`): the rule is *"adding a **closed,
  generation-bound, deployment-owner-provisioned, agent-unwritable protected
  recognition-input artifact** that concretely **resolves** — but does not widen,
  weaken, or redefine — an authority predicate the frozen contract **already
  requires** is a MINOR evolution."* Every qualifier is constraining: closed,
  generation-bound, protected, agent-unwritable, resolves-an-already-required
  predicate, no widening/weakening/redefinition. It does **not** license
  arbitrary future authority-input additions — a *new* predicate, a *widening*, or
  a *caller/env* input is out of its scope and remains governed by
  `HPAC-PAWA-REQ-152`. Direct precedent: HPAC-001 v2.1 (a MINOR that "adds one
  closed binding object … widens no authority"). **No loophole. VERIFIED.**
- **§47 MAJOR-trigger review** (`HPAC-PAWA-REQ-212`): independently evaluated
  every `HPAC-PAWA-REQ-152` trigger — **none fires**:
  - `sudo` / `euid` / env var sufficient authority → **no** (authority basis
    stays live effective filesystem write access);
  - collapse / remove the configured-agent exclusion → **no** (it is *implemented*);
  - same-principal topology permitted → **no** (§61 / `-205`, still fail closed);
  - remote / network / cloud authority service → **no** (fully local; `pwd` / `grp`
    are local NSS reads);
  - capability made bearer / durable / serialisable / reusable → **no**;
  - capability broadened into runtime approval / PB / RE / runtime capability /
    execution → **no**;
  - bootstrap trust root changed → **no** (still OS filesystem write authority on
    the out-of-band-provisioned protected root);
  - `generation` / rollback-prevention removed → **no** (C-2 *binds into* it);
  - signing key / pinned key / keychain added as an authority input → **no** (a
    symbolic name in a protected file + `pwd` / `grp`; no key, no signature, no
    secret);
  - authorized-consumer inventory widened by wildcard / prefix / glob → **no**
    (`HPAC-PAWA-REQ-209` bars wildcards).
  **⇒ HPAC-PAWA-001 v1.1 — MINOR. VERIFIED.** `HPAC-PAWA-REQ-213` preserves the
  MAJOR triggers unchanged.
- **§48 HPAC-001 compatibility**: HPAC-001 v2.1 byte-unchanged (last touched
  `.1R.15.4`); §7 already defers the mechanism to an implementation-profile
  companion. **VERIFIED — no change required.**
- **§49 RHAMP compatibility**: RHAMP-001 v1.0 byte-unchanged (last touched
  `.1R.29`); RHAMP-REQ-047 externalises the anchor; v1.1 changes only
  administrative enrollment-authority *resolution*, not authentication /
  protected-presentation semantics. **VERIFIED.**
- **§50 HBDC compatibility**: HBDC-001 v1.2 byte-unchanged (last touched
  `149O.20L.7O.2D`); precedent only (§3 `PCAE_AGENT_PRINCIPAL` terminology); **no
  normative runtime dependency on HBDC state** — R2 was rejected precisely to
  avoid amending it. **VERIFIED.**
- **CPIPC-001 v1.0** byte-unchanged (last touched `137Q`).

---

## 14. Implementability, atomicity, fixture seam, guards, traceability — VERIFIED

| Prompt § | v1.1 requirement | Future symbol / module | Existing primitive | Ambiguity | STOP |
|---|---|---|---|---|---|
| 51 | schema load / validate | `hpac_pawa_agent_exclusion.py` closed-schema helper | canonical-bytes / digest idiom (HPAC-REQ-089; descriptor helper) | none | no |
| 51 | account lookup + uid pin | `resolve_configured_agent_identity()` | `pwd.getpwnam` (stdlib) | none (property, not API, frozen — §63) | no |
| 51 | live groups | group-resolution symbol | `os.getgrouplist` (Linux) / `grp` scan (macOS) | none (§63 / `HPAC-PAWA-REQ-206`) | no |
| 51 | root authority eval | `_effective_write_access` / `_ancestor_chain_safe` | **already exist** in `hpac_foundation.py`, span both OSes | none | no |
| 51 | digest / current-generation validation | current-generation schema helper | descriptor-anchor idiom (§20) | none | no |
| 51 | provisioning / rotation | `scripts/hpac_protected_root_admin.py` `provision` / `set-agent-exclusion --agent-account` | existing `provision` entrypoint | none | no |
| 51 | test seam | `_configured_agent_identity_source` keyword-only, `None` in production | fixture pattern (`_validate_production_boundary` seam precedent) | none | no |
| 52 | atomicity | `.1R.30R.3.1` A1 lands resolver **with** the writer factory; no partial `production_writer` | `PAWA-INV-3` / `-12`; §33 / `HPAC-PAWA-REQ-075` | none | no |
| 53 | fixture-only resolver substitution without normative caller injection | one leading-underscore documented seam; guard test asserts no non-test module passes it | `HPAC-PAWA-REQ-166` / `-192` / §75 | none | no |
| 54 | future guards | `HPAC-PAWA-REQ-209` — exclusion-record writers; resolver consumers; no production identity override; writer-factory consumers; **no wildcard / prefix / fnmatch / glob** | consumer-inventory fence (§39, existing) | none | no |
| 55 | traceability | `HPAC-PAWA-REQ-207` — v1.1 clause → symbol → test → guard map; no prose-only guarantee | §73 discipline (existing) | none — no load-bearing phrase left undefined (`ConfiguredAgentAuthorityIdentity` is defined in §2) | no |

**Every new v1.1 requirement has a coherent implementation interpretation. No
requirement forces implementation to begin to resolve a normative ambiguity.
VERIFIED — PAWA Slice-1 implementation surface is unambiguous.**

---

## 15. D1 decomposition & contract-IV role — VERIFIED

- **§56 D1 decomposition** (§77–§78 / §96A): `.1R.30R.3.1` (impl) → `.3.2` (IV)
  → `.3.3` / `.3.4` (Slice 2 / IV) → `.3.5` / `.3.6` (Slice 3 / IV) → `.1R.30R.4`
  (composite IV) → `.1R.30R.5` → `.1R.30R.6` (IV + real-CTAP2-hardware +
  N-16-5 closure). `HPAC-PAWA-REQ-149` — **no ID is reserved or auto-authorized**
  (CPIPC-001 §4; `PAWA-INV-11`). `.2A` / `.2A.1` / `.2A.2` / `.2A.3` are
  grammar-valid `numeric-segment` (`2` + `A`) with dotted children; historical
  `.1R.30` remains immutable **BLOCKED**. **CPIPC-001-valid. VERIFIED.**
- **§57 contract-IV role**: this phase satisfies **C-3** as the dedicated
  contract IV (`HPAC-PAWA-REQ-210`). It is clean ⇒ `.1R.30R.3.1` may be
  recommended next. `.1R.30R.3.2` need not re-verify v1.1 beyond normal
  contract-production equivalence. **VERIFIED.**

---

## 16. Fresh contract-IV suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_3_v1_1_contract_freeze_iv.py`
— **72 tests, 72 passed, 0 failed**. Verification-only: imports no `pcae`
module; adds no skip / xfail / skipif; reads contracts + git history as evidence;
each assertion re-derives a freeze claim from primary source. Covers all 56
checkpoint areas the phase prompt enumerates: immutable SHAs; v1.1 identity;
exact v1.0→v1.1 delta (§7A rows); closed AGENT-EXCLUSION schema (12 fields, no
group snapshot, full validation); `symbolic_account` protected source;
`provisioned_uid` pin; live uid equality; deletion / recreation / UID reuse /
rename fail-closed; live groups / drift / removal; OS-account-DB TCB;
logical→OS bridge; three F-1 predicates; current-context comparison; no
current-euid substitution; two-principal invariant; installation binding;
generation relationship; current-generation 7-field schema + `/1.0` id validity;
`agent_exclusion_digest` mandatory/pre-authority; independent rollback impossible;
coordinated-rollback boundary not overclaimed; rotation / reprovision / migration
/ bootstrap non-circularity; account selection; no static-group / env / caller
authority; 21-code failure completeness; RHAMP map unchanged (41 codes);
descriptor schema byte-unchanged (§14 region + git); 11-step recognition
sequence + atomicity; write probe unchanged; R1/R2/R3/R4 disposition; S-1 wording
narrowness; MAJOR-trigger review; HPAC-001 / RHAMP-001 / HBDC-001 / CPIPC-001
byte-identity (git, three baselines each); implementation surface; future guards;
traceability; dedicated-IV role; D1 decomposition; no `src/pcae` diff; contract
diff = exactly one file; v1.0 freeze record not rewritten; runtime unchanged;
first effect absent; N-16-5 status; fixed-SHA attribution; and this phase's own
no-test-weakening audit.

---

## 17. No-test-weakening audit

This phase's `git diff <F> HEAD -- tests`:

1. **New file** — the `.2A.3` IV suite (did not exist at `F`; `git cat-file -e
   F:<path>` fails). 72 new `def test_`.
2. **`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py`**
   — 2 point-in-time guards reconciled (`test_no_contract_change_since_b30`,
   `test_only_iv_artifacts_changed_since_v`). **No `def` renamed, removed,
   skipped, or xfailed.** `test_no_contract_change_since_b30` now asserts the only
   contract file touched since `B30` is the PAWA writer-anchor contract itself
   (created by `.1R.30R.2`, evolved by `.2A.2`) **and** that the `.1R.30R.1`
   phase's own entry→verification-entry window is contract-clean — a *stronger*
   assertion than the vacuous `== ""` it replaced.
   `test_only_iv_artifacts_changed_since_v` now pins its upper bound to the
   `.1R.30R.1` finalized head (the phase's own window) rather than a drifting
   `HEAD`.
3. **`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_1_configured_agent_resolution_source_iv.py`**
   — 3 point-in-time guards re-pinned from a drifting `HEAD` to the fixed
   `.1R.30R.2A.1` finalized head `FINALIZED_2A1_HEAD` (a new module constant):
   `test_no_contract_change_since_phase_entry`,
   `test_this_suite_is_the_only_tests_change_since_phase_entry`,
   `test_no_existing_def_test_removed_or_renamed_repo_wide_since_phase_entry`.
   **No `def` renamed, removed, skipped, or xfailed.** All 56 tests now pass
   (the freeze doc §9 claimed this; it is now true — see Finding F-1).

Scanner semantics: `re.findall(r"^-\s*def (test_\w+)", diff)` over the phase diff
returns `[]`; no `pytest.skip` / `pytest.xfail` / `@pytest.mark.skip` / `skipif`
added on any `+` line; `new.count("def test_") >= old.count("def test_")` for
every touched file. The new suite's own
`test_this_phase_removes_or_renames_no_test_def`,
`test_no_skip_xfail_added_anywhere_in_this_phase_diff`, and
`test_stale_pointintime_guards_reconciled_not_deleted` enforce this in CI.

---

## 18. Broad relevant-suite results & fixed-SHA attribution

- **`.1R.30R.1` IV suite** (`..._1r_30r_1_writer_anchor_adjudication_iv.py`):
  **35 passed, 0 failed** (was 33 passed / 2 failed on `F` — the two stale
  point-in-time guards, now reconciled).
- **`.1R.30R.2A.1` IV suite against v1.1**: **56 passed, 0 failed** (was 55
  passed / 1 failed on `F`).
- **`.2A.3` fresh contract-IV suite**: **72 passed, 0 failed**.
- **Broader `-k "pawa or writer_anchor or configured_agent or contract_identity"`
  selection**: on `F` (this phase's changes absent) — `37 failed, 250 passed, 1
  skipped, 9 errors`; on the `.2A.3` candidate — the 3 PAWA-related failures
  become passes; the remaining `34 failed, 9 errors` reproduce **identically**.
  Those are pre-existing HMIC / HBDC / HATP contract-identity digest guards from
  unrelated phases (`149o_20l_1b`, `20e`, `20l_2`, `7e`) — **zero attributable to
  `.2A.3`**, which changes no `src/pcae`, no contract, and no HMIC-bound file.
- **Fixed-SHA A/B.** `A = F = 6c62a323` (finalized `.1R.30R.2A.2` head);
  `B = .2A.3` candidate:
  - `git diff --stat F HEAD -- src/pcae` → **empty** (production delta **0**).
  - `git diff --name-only F HEAD -- docs/contracts` → **empty** (contract delta
    **0**).
  - Candidate-only changes: the new IV suite, 5 reconciled point-in-time guard
    bodies across 2 pre-existing IV suites, this doc, `PROJECT_STATUS.md`,
    `CHANGELOG.md`, `tasks/**`, `.pcae/**`. **No candidate-only functional
    regression outside verification artifacts.**

---

## 19. Boundaries held

- `git diff <V> HEAD -- src/pcae` → **empty**. No `hpac_pawa_agent_exclusion.py`,
  no `resolve_configured_agent_identity()`, no schema helper, no `pwd` / `grp`
  call, no writer-anchor / provisioning-script change.
- `git diff --name-only <V> HEAD -- docs/contracts` → **empty**. HPAC-PAWA-001
  v1.1 is **byte-unchanged from `.2A.2`**. HPAC-001 v2.1, RHAMP-001 v1.0,
  HBDC-001 v1.2, CPIPC-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPSE-001 v1.1,
  HHCE-001, `HPAC-AUTHORITY-CONSUMPTION` (`/2.1`), REPRC-001 v1.0, PBNDE-001 v1.0,
  RDGO-001 v3.1, RPAC-001 v1.0, the RE No-Go Registry, and every other contract:
  **byte-unchanged**.
- `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema (§14): **byte-unchanged**.
- No FIDO2 / WebAuthn / CTAP code; no `_ELIGIBLE_MECHANISM_IDS` change; no
  `verifier_kind` added; no sidecar / counter-state store; no enrollment /
  bootstrap tool; no protected-presentation helper; no approval proof; no
  `PRODUCTION` `AuthenticatedHumanPrincipal`; no `require_real_assurance` wiring.
  No hardware accessed, enumerated, or prompted.
- Historical `.1R.30` (immutable BLOCKED), `.1R.30R`, `.1R.30R.1`, `.1R.30R.2`,
  `.1R.30R.2A`, `.1R.30R.2A.1`, `.1R.30R.2A.2` canonical records: **not edited**.
  The HPAC-PAWA-001 v1.0 freeze record is **not** rewritten.
- **Runtime:** `not_implemented` / `Observed` / `observe` / `unavailable`; 0
  plugins / 0 capabilities — unchanged.
- **First external effect:** ABSENT AND UNREACHABLE. No `adapter.dispatch(` call
  site; no subprocess / Popen / os.system / socket / http / provider path
  introduced (the only subprocesses this phase ran were read-only `git`
  inspection, `pcae` governance CLI checks, and read-only `pytest` runs). No
  execution enabled. **No Slice C.**
- **N-16-3 / N-16-4:** CLOSED, not reopened. **N-16-6 / N-16-7:** OPEN,
  untouched, N-16-7 strictly last. **N-23-1 / N-23-2:** carried unchanged.
- Gate 5 / 6 / 7 / 8 / 9 boundaries, the Slice-A / Slice-B verdicts, and the
  N-16-3 / N-16-4 closures: **not reopened**.
- No human approval treated as a policy or enforcement override.

---

## 20. Findings (non-blocking)

### Finding F-1 — the `.1R.30R.2A.2` freeze doc §9 test-evidence count was inaccurate (classification: **lifecycle / test-evidence**)

**Evidence.** The `.1R.30R.2A.2` freeze artifact §9 states: *"…`iv.py` is **56
passed, 0 failed** against the v1.1 contract."* On `F` (`6c62a323`, clean tree)
the actual result is **55 passed, 1 failed** — the failing test is
`test_no_contract_change_since_phase_entry`, a point-in-time guard in that same
suite that pins the PAWA contract to the `.1R.30R.2A` head `J` and legitimately
broke when `.2A.2` evolved the contract v1.0 → v1.1. The freeze doc §9 *did*
anticipate re-baselining stale guards in this phase, but enumerated only the two
`.1R.30R.1` guards (`test_no_contract_change_since_b30`,
`test_only_iv_artifacts_changed_since_v`) — it missed this third guard of the
same class in the `.2A.1` suite (and, transitively, two further self-guards in
the `.2A.1` suite that this phase's reconciliation of the first would have
tripped: `test_this_suite_is_the_only_tests_change_since_phase_entry`,
`test_no_existing_def_test_removed_or_renamed_repo_wide_since_phase_entry`).

**Impact.** **None on the contract.** All affected tests are point-in-time
*freshness* guards, not substantive contract-correctness checks; the v1.1
contract text is independently verified sound. The inaccuracy is confined to one
sentence of the freeze completion report.

**Disposition (this phase).** All five point-in-time guards across the two
pre-existing IV suites are re-baselined here — exactly the "re-baselined by
`.1R.30R.2A.3`" the freeze doc scheduled — by re-pinning each drifting `HEAD`
bound to the owning phase's own finalized head (or, for
`test_no_contract_change_since_b30`, to a stronger "only the PAWA contract moved"
assertion). No `def` renamed, removed, skipped, or xfailed (§17). The
`.1R.30R.1` and `.1R.30R.2A.1` suites are now **35/35** and **56/56**. Because
the fix belongs to this phase and the underlying contract is unaffected, F-1 is
**non-blocking** and needs **no successor repair phase**.

### Finding F-2 — `HPAC-PAWA-REQ-204` inline ordinal notation is imprecise (classification: **documentation**)

`HPAC-PAWA-REQ-204`'s prose ("…resolves to `agent_principal_unknown` / #3, or
`agent_has_protected_write_authority` / #2, or …") mixes the §56 PAWA-code
ordinal (`agent_principal_unknown` is PAWA code **#3**) with §57 RHAMP-code
ordinals (`#1`, `#2`, `#41`) in a single sentence. The **normative** §57 PAWA →
RHAMP table it defers to is correct and byte-unchanged, and the substantive
claim (every v1.1 rejection resolves to an existing §57 row; RHAMP's 41-code
vocabulary is byte-unchanged; RHAMP-001 is not edited) is **VERIFIED**. This is
a notation blemish in one requirement's explanatory prose, **not** a normative
defect. **No contract edit is performed** (this is a VERIFICATION-ONLY phase);
a future MINOR housekeeping pass, or `.1R.30R.3.2`, may tidy the sentence at
operator discretion. **Non-blocking.**

---

## 21. Verdicts

| Verdict area | Result |
|---|---|
| **Final contract verdict (§66)** | **HPAC-PAWA-001 v1.1 — VERIFIED WITH NON-BLOCKING FINDINGS** (F-1 lifecycle/test-evidence, discharged here; F-2 documentation, deferred) |
| **Identity-model verdict (§67)** | **R1-HYBRID — VERIFIED** — symbolic-account protection + `provisioned_uid` continuity + live-group currentness + anchor-digest rollback binding all survive independent challenge |
| **Versioning verdict (§68)** | **v1.1 MINOR — VERIFIED** — no `HPAC-PAWA-REQ-152` MAJOR trigger fires; S-1 is sufficiently narrow |
| **Implementation-readiness verdict (§69)** | **PAWA SLICE-1 IMPLEMENTATION READY** — contract verified; no unresolved authority-input ambiguity; rollback semantics verified; failure vocabulary complete; account-currentness semantics complete; atomicity clear; implementation surface unambiguous |
| **N-16-5 status (§70)** | **N-16-5 — PAWA v1.1 CONTRACT VERIFIED — SLICE-1 IMPLEMENTATION READY — NOT CLOSED.** Closure still requires `.1R.30R.3.*` implementation, `.1R.30R.4` composite IV, `.1R.30R.5` presentation + `require_real_assurance` wiring, and `.1R.30R.6` (IV + mandatory real-CTAP2-hardware verification). |

**No valid early-STOP / BLOCKED condition was reached.** Every BLOCKED condition
in the phase prompt was checked against primary source: R1-HYBRID *is* frozen as
`.1R.30R.2A.1` described; no authority-critical field is ambiguous or
caller-controlled; `symbolic_account` + `provisioned_uid` closes silent
deletion/recreation/UID-reuse; live supplementary-group currentness is
normatively required at every recognition; account rename cannot continue under
stale UID trust; `agent_exclusion_digest` prevents independent rollback;
current-generation schema evolution is internally consistent and appropriately
versioned; the three F-1 predicates do not collapse; `os.geteuid()` is never a
substitute for predicate A; no new `pawa_failure_code` is required; RHAMP's map
represents all v1.1 rejection classes; the descriptor schema is unchanged;
HPAC-001 / RHAMP-001 semantics need no change; no `HPAC-PAWA-REQ-152` MAJOR
trigger fires; S-1 is consistent with the contract's versioning taxonomy; the
11-step recognition sequence is non-contradictory and atomic; `.1R.30R.3.1` can
satisfy v1.1 without another normative decision; CPIPC-001 supports the D1
structure.

---

## 22. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1` — N-16-5 PAWA Production Protected-Admin
Writer Anchor Implementation (Slice 1)** — own explicit human authorization
required; ID recommended, **NOT reserved**. Scope fence (record for the
successor, from §72 of the phase prompt and §74 / §78 / §95A of the contract):

`.1R.30R.3.1` **may** implement only:
- `src/pcae/core/hpac_pawa_agent_exclusion.py` (closed `HPAC-PAWA-AGENT-EXCLUSION/1.0`
  schema helper + trusted load/validate + `symbolic_account` resolution +
  `provisioned_uid` equality + live group enumeration + digest/currentness
  validation + `resolve_configured_agent_identity()`), placed inside the
  non-agent-importable consumer-inventory fence;
- `hpac_pawa_schemas.py` / the current-generation 7-field schema helper;
- `hpac_protected_admin_writer.py` (production writer factory + §33 recognition
  sequence);
- `scripts/hpac_protected_root_admin.py` `provision` / `set-agent-exclusion
  --agent-account <name>` / rotate / revoke tooling;
- `PRODUCTION` `HPACWriterCapability` production issuance + one-operation
  semantics;
- `HumanPrincipalRegistryStore` production writer consumption;
- the exact 21-value PAWA failure vocabulary and the exact consumer/source
  guards (no wildcard);
- atomic unit A1 lands the resolver **together with** the writer factory.

`.1R.30R.3.1` **must NOT** implement: RHAMP FIDO2 sidecar; `RHAMP-COUNTER-STATE`;
enrollment ceremony; `FIDO2HumanAuthenticator`; the `hpac_verifier` real-mechanism
branch; `_ELIGIBLE_MECHANISM_IDS` widening; protected presentation; Gate
real-assurance wiring; N-16-6 / N-16-7; Slice C. It stays **FIDO2-free** and
limited to Slice 1.

Then `.1R.30R.3.2` (IV — MAY absorb no additional v1.1 contract re-verification
beyond normal contract-production equivalence, since C-3 is discharged here) →
`.1R.30R.3.3` / `.3.4` (Slice 2) → `.1R.30R.3.5` / `.3.6` (Slice 3) → `.1R.30R.4`
(composite IV) → `.1R.30R.5` (protected presentation + `require_real_assurance`
through Gate 5 / Gate 9) → `.1R.30R.6` (IV + mandatory real-CTAP2-hardware
verification + **N-16-5 closure**) → N-16-6 → N-16-7 (strictly last).

**Do not begin `.1R.30R.3.1`. Do not modify `src/pcae`. Do not modify normative
contracts. Do not implement `HPAC-PAWA-AGENT-EXCLUSION/1.0` or
`resolve_configured_agent_identity()`. Do not implement FIDO2 / WebAuthn / CTAP.
Do not implement protected presentation. Do not begin N-16-6 / N-16-7. Do not
begin Slice C. Do not implement or call the first external effect. Do not enable
execution.**

---

## 23. Governance

- `pcae health` **healthy** · `pcae check` **passed** · `pcae status coherence`
  **coherent** · `pcae doctor task-memory` **warning-only** (historical
  `tasks/DONE.md` omissions — pre-existing hygiene debt from earlier phases; no
  current-phase error; this phase adds its own `tasks/done/` entry to
  `tasks/DONE.md`) · `pcae push check` `nothing_to_push` before the governed push
  · `pcae runtime inspect` `not_implemented` / `Observed` / `observe` /
  `unavailable`, 0 plugins / 0 capabilities.
- **Test evidence.** New `.2A.3` contract-IV suite: **72 passed, 0 failed**. Two
  pre-existing IV suites reconciled and green (**35/35**, **56/56**). No
  functional implementation test authored; no functional success evidence
  manufactured. Five point-in-time guard bodies reconciled — **no `def test_`
  renamed, removed, skipped, or xfailed**.
- **Regression attribution.** Zero regression attributable to `.2A.3`:
  `git diff --stat F HEAD -- src/pcae` and `git diff --name-only F HEAD --
  docs/contracts` are both empty; the broader pre-existing HMIC/HBDC failures
  reproduce identically with this phase's changes absent.
- **`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`** — preserved. Only
  the primary human-authorized operator holds `.1R.30R.2A.3` lifecycle
  authority. Governed `pcae` lifecycle only — no raw `git commit` / `git push`,
  no `--no-verify`, no force push, no history rewrite, no hook bypass.

---

## 24. Verdict block

```
HPAC-PAWA-001 v1.1 CONFIGURED-AGENT-PRINCIPAL RESOLUTION SOURCE CONTRACT FREEZE —
INDEPENDENT VERIFICATION (.1R.30R.2A.3)

FINAL CONTRACT VERDICT   HPAC-PAWA-001 v1.1 — VERIFIED WITH NON-BLOCKING FINDINGS
IDENTITY MODEL           R1-HYBRID — VERIFIED
VERSIONING               v1.1 MINOR — VERIFIED (no HPAC-PAWA-REQ-152 trigger; S-1 narrow)
SLICE-1 READINESS        PAWA SLICE-1 IMPLEMENTATION READY
N-16-5                   PAWA v1.1 CONTRACT VERIFIED — SLICE-1 IMPLEMENTATION READY — NOT CLOSED

VERIFICATION-ENTRY SHA   6c62a323cccda56e969128d4b6e01f98d53630ce (== F)
A (.2A.1 finalized head) 3f23d6fd4a6812cdb4d2f6f7d2c0e2edd2511667
F (.2A.2 finalized head) 6c62a323cccda56e969128d4b6e01f98d53630ce
V (.2A.3 phase entry)    6c62a323cccda56e969128d4b6e01f98d53630ce
B30 (.1R.30 BLOCKED)     8e65529596fc351face4b83c4b5d08573326d034 — immutable

V1.0 -> V1.1 DELTA        §7A, §9.1, §10, §20A, §31, §32A, §32B, §32C, §33, §42A,
                         §57, §61, §63, §73-76, §80.1, §81-84, §87-89, §90.1,
                         §91-95A, §96A ; HPAC-PAWA-REQ-164..218 ; PAWA-INV-12 ;
                         no unrelated semantic change
CONTRACT IDENTITY        HPAC-PAWA-001 v1.1 — consistent title / status / §7A /
                         §80 / §91 / §94 / freeze artifact / PROJECT_STATUS /
                         CHANGELOG ; v1.0 record NOT rewritten (append-only)
AGENT-EXCLUSION SCHEMA    §32A.1 — 12-field CLOSED ; no group snapshot as
                         authority ; full validation enumerated (REQ-177)
symbolic_account         VERIFIED — protected out-of-band admin only ; not
                         caller / env / repo / euid / shell / agent-lock
provisioned_uid          VERIFIED — account-instance continuity pin ; NOT the
                         authority basis (live effective write access is)
LIVE UID EQUALITY        VERIFIED — every §33 recognition ; no fallback ; not cached
ACCOUNT DELETION         VERIFIED — symbolic_account absent -> agent_principal_unknown
ACCOUNT RECREATION       VERIFIED — live uid != provisioned_uid -> reject ; no
(NEW UID)                silent rebind (C-1 closes R1-PURE sharp edge)
UID REUSE                VERIFIED — name lookup mandatory ; no reverse-uid fallback
ACCOUNT RENAME           VERIFIED — old name unresolvable -> reject ; no uid follow
LIVE GROUP SEMANTICS     VERIFIED — current primary+supplementary enumerated live
                         every recognition ; never persisted as authority (INV-12)
GROUP DRIFT              VERIFIED — normative, decisive -> agent_has_protected_write_authority
GROUP REMOVAL            VERIFIED — reflected live ; recovers with NO reprovision
OS ACCOUNT DB TCB        VERIFIED — inside PAWA's OS TCB ; no hostile-root claim
LOGICAL -> OS BRIDGE     VERIFIED — precise ; §33 evaluates resolved OS identity,
                         never the agent_id label
THREE F-1 PREDICATES     DISTINCT — A (configured identity) / B (live vs
                         configured) / C (live write probe) ; none substitutes
CURRENT-CONTEXT COMPARE  VERIFIED (REQ-201) — live uid == configured uid ->
                         current_context_is_agent ; groups alone != identity
CURRENT-EUID PROHIBITION VERIFIED (REQ-193) — os.geteuid() never operand of A
TWO-PRINCIPAL INVARIANT  VERIFIED (REQ-205) — coincidence -> fail closed ; a
                         concrete source is NOT a reason to relax
INSTALLATION / ROOT BIND VERIFIED — installation_id + {device,inode} ; copied
                         record never validates
GENERATION SEMANTICS     VERIFIED — same monotonic anchor for descriptor + record
CURRENT-GEN SCHEMA       VERIFIED — closed 7-field set ; +agent_exclusion_digest ;
                         schema id /1.0 kept (internal anchor ; contract governs
                         shape) ; v1.0-era anchor -> fail closed
agent_exclusion_digest   VERIFIED — mandatory ; validated before authority eval ;
                         no advisory use
INDEPENDENT ROLLBACK     IMPOSSIBLE — restored superseded record fails closed ;
                         bare generation-int equality NOT a substitute (C-2)
COORDINATED ROLLBACK     BOUNDARY STATED, NOT OVERCLAIMED — bounded by the single
                         monotonic anchor + {device,inode}, exactly as v1.0
ROTATION / REPROVISION   VERIFIED — explicit ; generation += 1 ; atomic anchor
                         replace ; old record SUPERSEDED, no longer satisfies §33
MIGRATION                VERIFIED — fresh installation_id + {device,inode} ; copy
                         alone never validates
BOOTSTRAP                VERIFIED — create-only alongside deployment-owner.json ;
                         NON-CIRCULAR (no capability / FIDO2 / prior principal)
ACCOUNT SELECTION        VERIFIED — explicit --agent-account admin input
STATIC-GROUP PROHIBITION VERIFIED — provision-time gid list never current authority
ENVIRONMENT PROHIBITION  VERIFIED — PCAE_AGENT_PRINCIPAL / USER / LOGNAME /
                         SUDO_USER never the trust source, never an override
CALLER-INPUT PROHIBITION VERIFIED — production_writer carries no uid/gids/account
                         param ; one guard-checked fixture-only seam
PAWA FAILURE COVERAGE    VERIFIED — 21 closed codes UNCHANGED ; v1.1 rejections
                         -> #3 / #4 / #14 / #19 / #21
RHAMP MAPPING            VERIFIED — §57 table unchanged ; 41-code vocab
                         byte-unchanged ; RHAMP-001 not edited
DESCRIPTOR SCHEMA        BYTE-UNCHANGED — §14 13-field closed set ; kind+basis
                         only ; no account name / uid sneaked in
RECOGNITION SEQUENCE     VERIFIED — 11 steps ; steps 2/3/7 gain atomic substeps ;
                         resolution atomic with the mint (unit A1)
11-STEP CONSISTENCY      VERIFIED — step 11 present, no step 12 ; no 15-step list
WRITE PROBE              UNCHANGED — O_EXCL|O_NOFOLLOW ; no os.access() ; §34 intact
R1 / R2 / R3 / R4        VERIFIED — R1-HYBRID FROZEN ; R1-PURE superseded (C-1) ;
                         R2 rejected (HBDC amendment, wrong namespace) ; R3
                         rejected as resolution (test-seam only) ; R4 no superior
S-1 VERDICT              VERIFIED — narrow (closed / generation-bound / protected /
                         resolves-an-already-required-predicate ; no widening) ;
                         no loophole
MAJOR-TRIGGER REVIEW     NONE FIRES — all 10 HPAC-PAWA-REQ-152 triggers checked
HPAC-001 COMPATIBILITY   VERIFIED — v2.1 byte-unchanged ; §7 defers the mechanism
RHAMP COMPATIBILITY      VERIFIED — v1.0 byte-unchanged ; only enrollment-authority
                         resolution changes
HBDC COMPATIBILITY       VERIFIED — v1.2 byte-unchanged ; precedent only ; no
                         normative runtime dependency
IMPLEMENTATION MAPPING   VERIFIED — every v1.1 requirement -> coherent future
                         symbol ; _effective_write_access / _ancestor_chain_safe
                         already exist ; NO STOP
ATOMICITY                VERIFIED — A1 lands resolver WITH the writer factory ;
                         no partial production writer
FIXTURE SEAM             VERIFIED — one leading-underscore documented seam ;
                         guard-checked ; simulates all adversarial cases without
                         touching real host accounts
FUTURE GUARD REQS        VERIFIED — REQ-209 ; no wildcard / prefix / fnmatch / glob
TRACEABILITY             VERIFIED — REQ-207 ; no load-bearing phrase undefined
D1 DECOMPOSITION         VERIFIED — CPIPC-001 §4 ; no ID reserved ;
                         .2A/.2A.1/.2A.2/.2A.3 grammar-valid ; .1R.30 BLOCKED
FRESH IV SUITE           72 passed, 0 failed
NO-TEST-WEAKENING AUDIT  PASS — 0 def removed / renamed / skipped / xfailed ;
                         5 point-in-time guard bodies reconciled (bounds re-pinned)
BROAD SUITE / FIXED-SHA  pre-existing HMIC/HBDC failures reproduce identically ;
                         zero attributable to .2A.3
CONTRACT BYTE IDENTITY   HPAC-PAWA-001 v1.1 byte-unchanged from .2A.2 ; HPAC-001
                         v2.1 / RHAMP-001 v1.0 / HBDC-001 v1.2 byte-unchanged
PRODUCTION DIFF          git diff <V> HEAD -- src/pcae : EMPTY
RUNTIME                  not_implemented / Observed / observe / unavailable ; 0/0
FIRST EXTERNAL EFFECT    ABSENT AND UNREACHABLE ; no Slice C
FINDINGS                 F-1 (lifecycle/test-evidence — freeze doc §9 count
                         inaccurate ; discharged here, no successor phase) ;
                         F-2 (documentation — REQ-204 ordinal notation ; deferred,
                         no contract edit this phase)

RECOMMENDED NEXT PHASE   149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 — N-16-5 PAWA
                         Production Protected-Admin Writer Anchor Implementation
                         (Slice 1 ; FIDO2-free). Own explicit human authorization
                         required. Do not begin it.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED — preserved.
```

See `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
(HPAC-PAWA-001 v1.1), the `.1R.30R.2A` / `.1R.30R.2A.1` / `.1R.30R.2A.2`
artifacts, and
`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_2a_3_v1_1_contract_freeze_iv.py`.
