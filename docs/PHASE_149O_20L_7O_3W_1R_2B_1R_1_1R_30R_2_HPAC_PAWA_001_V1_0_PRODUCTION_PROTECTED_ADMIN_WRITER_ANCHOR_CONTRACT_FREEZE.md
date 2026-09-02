# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2 — HPAC-PAWA-001 v1.0 Production Protected-Admin Writer Anchor Contract Freeze

**Status: COMPLETE — HPAC-PAWA-001 v1.0 FROZEN AS THE SOLE NORMATIVE DELTA.**
Not BLOCKED. `git diff <phase-entry> HEAD -- src/pcae` is **empty**;
`git diff --name-only <phase-entry> HEAD -- docs/contracts` names **exactly one
new file** (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`)
and no existing contract. HPAC-001 stays v2.1; RHAMP-001 stays v1.0
byte-unchanged; HBDC-001 stays v1.2. Runtime `Observed` / `observe` /
`unavailable`; first external effect **ABSENT**. **N-16-5: WRITER-ANCHOR
CONTRACT FROZEN — IMPLEMENTATION PENDING — NOT CLOSED.**

- **Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2`
- **Phase title:** HPAC-PAWA-001 v1.0 Production Protected-Admin Writer Anchor
  Contract Freeze
- **Phase-entry SHA:** `5373ee2115f4eb73101fc86b47b78be4135d4450`
  (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2: open HPAC-PAWA-001 v1.0
  contract-freeze phase task`; `git rev-list --count origin/main..HEAD = 0` at
  entry after the immediate task-open commit; the true baseline tree is the
  `.1R.30R.1` finalized head `91741564`).
- **Phase type:** governed contract-freeze / primary-source analysis /
  contract-versioning re-derivation / decision-freezing / documentation phase.
  Contract-only. No writer-anchor mechanism implemented; no `HumanPrincipalRegistryStore`
  production writer; no FIDO2; no credential / counter sidecars; no
  enrollment / bootstrap tooling; no protected presentation; no real approval
  proof; no N-16-6 / N-16-7; no Slice C; no first external effect; no execution
  enablement.
- **Authorization:** explicit single-phase human authorization for `.1R.30R.2`
  only (phase ID recommended, NOT reserved).
- **Production source diff:** `git diff 91741564 HEAD -- src/pcae` is **empty**.
- **Normative contract diff:** `git diff --name-only 91741564 HEAD --
  docs/contracts` names exactly `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`.

---

## 1. Current verified baseline (phase prompt §1) — CONFIRMED

| Item | State at phase entry |
|---|---|
| N-16-3 | CLOSED (`.1R.23` IV) |
| N-16-4 | CLOSED (`.1R.27R` IV) |
| N-16-5 | NOT CLOSED — adjudication VERIFIED (`.1R.30R.1`); contract-freeze pending (this phase); implementation not begun |
| RHAMP-001 v1.0 | FROZEN, byte-unchanged since `.1R.29` |
| HPAC-001 | v2.1, FROZEN |
| historical `.1R.30` | BLOCKED / IMMUTABLE — never reused, never resumed |
| `.1R.30R` | ADJUDICATED (NEW COMPANION CONTRACT verdict) |
| `.1R.30R.1` | ADJUDICATION VERIFIED (3 non-blocking findings F-1 / F-2 / F-3) |
| writer anchor | NOT IMPLEMENTED |
| HPAC-PAWA-001 | NOT YET AUTHORED (before this phase) |
| Runtime | `not_implemented` / `Observed` / `observe` / `unavailable`; 0 plugins / 0 capabilities |
| First external effect | ABSENT — no `adapter.dispatch(` call site; no Slice C |
| `origin/main..HEAD` | 0 |

### 1.1 Initial repository inspection (phase prompt §5)

| Command | Result |
|---|---|
| `git status --branch --short` | `## main...origin/main` — clean |
| `git rev-list --count origin/main..HEAD` | `0` at entry |
| `git log --oneline` head | `91741564` — `.1R.30R.1` push-state reconcile |
| `git log --oneline origin/main..HEAD` | empty |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae doctor task-memory` | warning-only pre-existing `tasks/DONE.md`-omission hygiene debt from earlier phases; no current-phase error |
| `pcae push check` | `nothing_to_push`; phase report trust passed; phase report identity passed |
| `pcae runtime inspect` | `not_implemented` / `Observed` / `observe` / `unavailable`; registry empty; 0 plugins / 0 capabilities; Permission Broker `execution_unavailable`; governance posture `non-executing` |
| `pcae notify status` | Telegram configured / enabled / outbound-ready |
| `pcae phase-report show --latest` | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1 (completed, report: complete)` |

`.1R.30R.1` is the latest completed phase; `origin/main..HEAD = 0`; no active
governed phase before startup; runtime `Observed` / `observe` / `unavailable`;
first external effect absent.

---

## 2. Frozen adjudication implemented (phase prompt §2) + F-1 / F-2 / F-3 (§3)

HPAC-PAWA-001 v1.0 freezes exactly the `.1R.30R` adjudication verdict as
independently verified by `.1R.30R.1`:

- **Preferred positive anchor (Candidate E, composed):** OS filesystem write
  authority on the out-of-band-provisioned `<HPAC_PROTECTED_ROOT>`; the
  configured agent principal provably excluded; a root-identity-bound
  `.authority/` deployment-owner descriptor; a positive write-authority probe
  against the exact canonical namespace; an explicit not-configured-agent check;
  a `PRODUCTION` writer factory in a non-agent-importable module; an exact
  consumer-inventory guard; a short-lived / process-local / non-bearer
  `HPACWriterCapability`; a one-time out-of-band administrative bootstrap;
  HBDC-001 v1.2 Class-B as **precedent**, re-applied under HPAC's independent
  namespace.
- **Contract verdict:** NEW COMPANION CONTRACT REQUIRED — `HPAC-PAWA-001 v1.0`.
  HPAC-001 stays v2.1; RHAMP-001 stays v1.0.

### F-1 disposition — INCORPORATED

`HPAC-PAWA-001` §10 freezes a **per-predicate identity matrix**: every
recognition predicate names exactly which identity it is evaluated against
(the configured agent principal / the current invoking OS process / the
protected-root owner / the descriptor owner / the importing source module / a
fixed compiled-in path), its authority source, whether it is caller-controlled,
and its failure behaviour. §9 fixes the configured agent principal's source of
truth = **canonical PCAE agent configuration / lock semantics** (HBDC-001 §3
`PCAE_AGENT_PRINCIPAL`), **never** `os.geteuid()`, never `--agent-id`, never
caller input; unresolvable → `agent_principal_unknown` fail closed; no
`agent_id=None` bypass. §26 / §62: the *negative* boundary check on the
production-writer path keys off the **configured agent principal's** ids
(`_effective_write_access` already parameterises `uid` / `gids`); the *positive*
write probe (§28) keys off the **invoking process's** live capability —
different identities, both well-defined. §27 bans "current user" as an authority
term. `.1R.30R.1` classified F-1 NON-BLOCKING (a localized implementation
obligation, trust root unaffected); this contract discharges the "state which
identity each predicate is evaluated against" obligation.

### F-2 disposition — INCORPORATED (documentation correction recorded)

`HPAC-PAWA-001` §77 (`HPAC-PAWA-REQ-146`) records: **`.1R.30R.3`, NOT
`.1R.30R.2`, is the fresh implementation successor.** `.1R.30R.2` (this phase)
is the contract-freeze phase; implementation needs the frozen contract first
(`.1R.30R` §21.1 precondition 1). The `.1R.30R` doc's §21.4 heading and §24
summary line (which said `.1R.30R.2` = implementation) are erroneous; the
dominant statement (`.1R.30R` §21.5 table, §24 downstream-sequence line,
PROJECT_STATUS, completion metadata) and the `.1R.30R.1` IV (§21, §27.4) are
correct. **No `.1R.30R` doc edit is required or made by this phase** — the
`.1R.30R` and `.1R.30` canonical artifacts are byte-unchanged. §92 PAWA-INV-11
freezes: historical `.1R.30` is immutable BLOCKED, never reused, never resumed.

### F-3 disposition — INCORPORATED

`HPAC-PAWA-001` §14 adds `generation` (non-negative integer ≥ 1) and a closed
`supersedes` object to the `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` schema. §20
(`HPAC-PAWA-REQ-047..050`) freezes: `generation` is **monotonic,
installation-local, strictly increasing**; initial = exactly 1; every rotation
= `previous + 1`; unique per `installation_id`; the **current generation** is
anchored by a new protected `HPAC-PAWA-CURRENT-GENERATION/1.0` record
(`current-generation.json`), create-only at provisioning, updated only by a
deployment-owner **atomic replace** whose new value is exactly `old + 1`;
recognition requires `descriptor.generation == current_generation` and a digest
match; `generation` is **not advisory**; if monotonic atomic-replace with
read-back is unavailable the implementing phase STOPS (BLOCKED). §21
(`HPAC-PAWA-REQ-051..053`): a previously superseded valid descriptor SHALL NOT
become current merely because its bytes are restored — a bytes-only rollback to
`generation N` while `current_generation` is `M > N` →
`descriptor_generation_stale`; a full paired rollback requires being the
deployment owner (in the model's trust boundary — the contract does not and
need not prevent the deployment owner reverting their own installation); a
restored old whole root is additionally caught by the `{device, inode}` binding.

---

## 3. Primary sources (phase prompt §4)

Read in full or to complete relevant scope before any contract clause:

| Source | Scope read | Purpose |
|---|---|---|
| `PROJECT_STATUS.md` (head) | current-phase block + N-16 gate-chain state | baseline confirmation |
| `.1R.30R` adjudication artifact | **full (1064 lines)** | the frozen verdict this contract implements; §7 capability semantics; §8–§12 candidate analysis; §14 bootstrap; §15 minting/scope/failure/audit; §16 versioning; §17 preferred anchor; §18 claim boundary; §19 relationships; §20 attack matrix; §21 phase-ID derivation |
| `.1R.30R.1` IV artifact | **full (1549 lines)** | F-1 (§11.1, §15.1, §26), F-2 (§21, §27.4, §996-block), F-3 (§18.3, §26); the per-conjunct Candidate E justification (§17.5); the independently-reconstructed preferred-anchor verdict (§27.2); the verdict block (§29) |
| historical `.1R.30` canonical BLOCKED artifact | scope relevant to the gap statement + immutability | preserve immutable BLOCKED; F-2 |
| `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.1) | **§7 HPAC-REQ-021/022/023/024 in full; §8 HPAC-REQ-025..031; §28 HPAC-REQ-079/080; §37 versioning; §38 HPAC-REQ-089** | the policy this contract supplies the mechanism for; the extension points; the canonicalisation rule; the versioning discipline |
| `docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md` (RHAMP-001 v1.0) | **§1 companion framing; §14 RHAMP-REQ-047..050 bootstrap authority; §15 RHAMP-REQ-051/052 evidence; §17 sidecar; §21–§22 counter-state; §49 the 41-code `terminal_reason_code` table in full; §50 terminal semantics; §61 protected admin enrollment; §64 RHAMP-REQ-156 decomposition; §65 N-16-6/7 separation; §68 traceability obligation; §70 versioning; §71 RHAMP-INV-005/006/010/014** | the anchor RHAMP-REQ-047 points to; the exact failure-code mapping targets (#1 / #2 / #40 / #41); the sidecar / counter-state stores a `PRODUCTION` writer authorizes; the decomposition |
| `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.2) | **full (397 lines)** — §3 terminology (`PCAE_AGENT_PRINCIPAL`); §4 threat model; §7 HBDC-REQ-001..005 principal model; §8–§9 authority; §10–§11 HBDC-REQ-011..021 Protected Root; §16.1 HBDC-REQ-056..066 producer / non-agent-importable; §18 root-compromise limit; §19 CBD invariants; §16.2 vocabulary precedent | the IV'd precedent for the two-OS-principal protected-root writer boundary; the non-agent-importable + consumer-inventory guard pattern; the "precedent not shared authority root" boundary |
| `docs/contracts/CANONICAL_PHASE_ID_PARSING_CONTRACT.md` (CPIPC-001 v1.0) | §3 terminology; §4 grammar (EBNF + whole-string form); §4.2 reserved; §10 comparison | `.1R.30R.2` / `.1R.30R.3` are valid `numeric-segment` forms; historical `.1R.30` immutability |
| `src/pcae/core/hpac_foundation.py` | **full (782 lines) — read as evidence only, NOT modified** | `HPACStoreAuthority` (`writer()` `raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")` L420-421; `_validate_production_boundary` L351-367; `_ensure_root`; `_relative_record_path` production branch; `_root_identity` `{device, inode}` L342-344; `store_id` manifest binding L400-415); `HPACWriterCapability` (`__slots__` L225; `_seal is not _WRITER_CONSTRUCTOR_SEAL` L236; `__reduce__` raises L243-244); `HPACAuthorityClass` (`FIXTURE_NON_REAL` / `PRODUCTION`); `ProtectedAdminCapability` ("can never authorize a production store"); `require_writer` seal-identity + role/subject + class checks L440-449; `record_write` / `verify_record` `HPAC-WRITER-PROVENANCE/1.0` closed schema; `write_atomic_create_only` `os.link(..., follow_symlinks=False)` + dir-`fsync`; `_AUTHORITY_DIR = ".authority"`; `resolve_hpac_protected_root()` fixed macOS + Linux paths, no input |
| `src/pcae/core/hatp_class_b_topology_verifier.py` | (via `.1R.30R` / `.1R.30R.1` reconstruction + `hpac_foundation.py` imports) | `_current_agent_identity()` == live `os.geteuid()` / groups (the F-1 basis); `_effective_write_access(path, uid, gids)` parameterised; `_ancestor_chain_safe`; `_FORBIDDEN_SELF_ELEVATION_ATTRS` / `_SUSPICIOUS_ENV_KEY_SUBSTRINGS` bans |
| `scripts/hatp_deployment_binding_admin.py` | module docstring + producer/rotation/revocation structure | the frozen PCAE precedent: a separate non-agent-importable admin writer module; "Real security boundary: OS filesystem write permission … never an in-process check" |
| repository inspection commands (phase prompt §5) | full | phase-entry baseline (§1.1) |

**Not read to completion** (not required; the contract-freeze conclusion does
not depend on them): RIHAC-001 v2.0 / RIASC-001 v3.0 / HPSE-001 v1.1 / HHCE-001
full text (their disposition is "unaffected — §12 cond 7 consumes HPAC
evidence, wire shape unchanged, namespace precedent only"), the Gate-5 / Gate-9
consumption schema, `approval_presentation.py`, `hpac_lifecycle.py`,
`human_authentication_proof.py`, the HATP FIDO2 provider. These govern the
presentation / proof-lifecycle / gate-consumption half that this phase does not
touch.

---

## 4. HPAC-PAWA contract identity / version

- **Contract:** HPAC-PAWA-001
- **Version:** 1.0 (initial freeze)
- **File:** `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
- **Namespace:** independent `HPAC-PAWA-REQ-###` (HPSE-001 / RHAMP-001
  precedent); `HPAC-PAWA-REQ-001..163`, sequential, no gaps, no duplicates
  (verified mechanically); `PAWA-INV-1..11`.
- **Companion of:** HPAC-001 v2.1 (fills its §7 mechanism gap; changes none of
  its text). **Precedent:** REPRC-001 v1.0 / PBNDE-001 v1.0 / RHAMP-001 v1.0
  (companion born to avoid a parent cascade).
- **Not** an HMIC-001 bound contract; bytes participate in no
  `implementation_scope_digest` (HBDC-REQ-047..049 disposition precedent;
  revisable only by a future amendment).

---

## 5. What HPAC-PAWA-001 v1.0 freezes — section index

| # | Topic | HPAC-PAWA-REQ |
|---|---|---|
| §1 | Companion, not amendment — the exact HPAC-001 gap filled | 001–005 |
| §2 | Terminology (configured agent principal ≠ `geteuid()`) | — |
| §3 | Scope / non-goals | 006–009 |
| §4 | Trust root = OS filesystem write authority on the protected root | 010–012 |
| §5 | Walls preserved (15-line block) | 013–014 |
| §6 | Contract-home / companion determination | 015–016 |
| §7 | Contract purpose (normative) | 017 |
| §8 | Trusted computing base + threat model | 018–020 |
| §9 | Configured agent principal — source of truth (F-1) | 021–025 |
| §10 | Per-predicate identity matrix (F-1) | 026–027 |
| §11 | Protected root | 028–030 |
| §12 | `.authority/` namespace | 031–033 |
| §13 | Descriptor identity (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`) | 034–035 |
| §14 | Closed descriptor schema (incl. `generation`, `supersedes`) | 036–038 |
| §15 | Descriptor ≠ human identity | 039 |
| §16 | Root / installation identity binding (`{device, inode}`) | 040–041 |
| §17 | Descriptor ownership / mode (fail closed on weakening) | 042–043 |
| §18 | No path-only trust | 044 |
| §19 | Descriptor provenance (`HPAC-WRITER-PROVENANCE/1.0`; no new key) | 045–046 |
| §20 | Descriptor generation — monotonic, anchored (F-3) | 047–050 |
| §21 | Descriptor rollback prevention (F-3) | 051–053 |
| §22 | Machine migration / reprovisioning vs. rollback | 054–055 |
| §23 | Initial out-of-band bootstrap (non-circular) | 056–057 |
| §24 | Bootstrap repeatability (no silent reset) | 058–059 |
| §25–§32 | Recognition predicates 1–6 + positive validation sequence | 060–075 |
| §34 | No `sudo` / `euid` shortcut | 076–077 |
| §35 | Wrong privileged principal (OS-authority construct) | 078–080 |
| §36–§39 | Writer factory / module boundary / consumers / guard | 081–090 |
| §40–§44 | `HPACWriterCapability` class / issuance inputs / operation / principal / credential scope | 091–100 |
| §45–§49 | Process-local / non-bearer / non-serializable / restart-invalid / one-operation | 101–108 |
| §50–§53 | Rotation / revocation / recovery / clone-snapshot | 109–115 |
| §54–§55 | Audit evidence (`HPAC-PAWA-ISSUANCE-EVIDENCE/1.0`) — not capability | 116–120 |
| §56 | Failure taxonomy — 21 closed `pawa_failure_code` values | 121–122 |
| §57 | RHAMP §49 mapping — #1 / #2 / #40 / #41; NO new code | 123–125 |
| §58 | PAWA failure ≠ runtime denial | 126 |
| §59–§60 | Out-of-band bootstrap audit / root TCB claim boundary | 127–128 |
| §61 | Same-UID / two-principal requirement (fail closed) | 129–130 |
| §62–§64 | Local / offline; macOS/Linux abstraction; no keychain / signing key | 131–133 |
| §65–§66 | HBDC precedent boundary (not a shared authority root) | 134–135 |
| §67–§68 | No runtime human approval; no PB / RE override | 136–137 |
| §69 | No FIDO2 requirement for first bootstrap (non-circular) | 138 |
| §70–§72 | Future implementation / FIDO2 enrollment / recovery flows | 139–141 |
| §73–§76 | Contract-production traceability / source boundary / consumer guards / IV requirements | 142–145 |
| §77–§79 | `.1R.30R.3` successor (F-2); downstream sequence; N-16-6/7 order | 146–150 |
| §80–§84 | Versioning; byte identity; no source / no test | 151–158 |
| §85–§89 | Runtime; first effect; N-16-5 status; N-16-6/7; N-23-1/2 | 159–163 |
| §90–§96 | Verdict / inventory / invariants / self-consistency / next phase | — |

---

## 6. Per-clause disposition of the phase prompt's required freezes (§94 sequence)

Every numbered required-completion item was checked against actual contract
text:

| Prompt step | Contract location | Status |
|---|---|---|
| 7 freeze PAWA TCB | §8 (`REQ-018..020`) | ✅ |
| 8 configured-agent identity source | §9 (`REQ-021..025`) | ✅ (F-1) |
| 9 per-predicate identity matrix | §10 (`REQ-026..027`) | ✅ (F-1) |
| 10 protected root | §11 (`REQ-028..030`) | ✅ |
| 11 `.authority` namespace | §12 (`REQ-031..033`) | ✅ |
| 12 descriptor identity / schema | §13–§14 (`REQ-034..038`) | ✅ |
| 13 descriptor non-human-identity | §15 (`REQ-039`) | ✅ |
| 14 root / install identity | §16 (`REQ-040..041`) | ✅ |
| 15 owner / mode | §17 (`REQ-042..043`) | ✅ |
| 16 provenance | §19 (`REQ-045..046`) | ✅ (no new key) |
| 17 generation | §20 (`REQ-047..050`) | ✅ (F-3) |
| 18 rollback prevention | §21 (`REQ-051..053`) | ✅ (F-3) |
| 19 migration / reprovisioning | §22 (`REQ-054..055`) | ✅ |
| 20 bootstrap | §23 (`REQ-056..057`) | ✅ (non-circular) |
| 21 duplicate-bootstrap | §24 (`REQ-058..059`) | ✅ |
| 22 canonical-root recognition | §25 (`REQ-060`) | ✅ |
| 23 agent exclusion | §26 (`REQ-061..063`) | ✅ (F-1) |
| 24 descriptor validation | §27 (`REQ-064`) | ✅ |
| 25 positive write authority | §28 (`REQ-065..066`) | ✅ (`O_EXCL\|O_NOFOLLOW`) |
| 26 write-probe target | §29 (`REQ-067..068`) | ✅ (ephemeral sentinel) |
| 27 TOCTOU assumptions | §30 (`REQ-069..070`) | ✅ (re-verify at write time) |
| 28 not-agent current-context | §31 (`REQ-071..072`) | ✅ |
| 29 authorized-consumer predicate | §32 (`REQ-073`) | ✅ |
| 30 positive validation sequence | §33 (`REQ-074..075`) | ✅ (11 steps) |
| 31 sudo / euid prohibition | §34 (`REQ-076..077`) | ✅ (PAWA-INV-1) |
| 32 privileged-wrong-principal boundary | §35 (`REQ-078..080`) | ✅ |
| 33 writer factory | §36 (`REQ-081..083`) | ✅ (no new token) |
| 34 module boundary | §37 (`REQ-084..086`) | ✅ |
| 35 consumer inventory | §38–§39 (`REQ-087..090`) | ✅ (exact, no wildcard) |
| 36 existing-capability use | §40 (`REQ-091..092`) | ✅ |
| 37 issuance bindings | §41 (`REQ-093..094`) | ✅ (least authority) |
| 38 operation scope | §42 (`REQ-095..097`) | ✅ (5 closed classes) |
| 39 principal scope | §43 (`REQ-098`) | ✅ |
| 40 credential scope | §44 (`REQ-099..100`) | ✅ (transaction binding for enroll) |
| 41 process-local | §45 (`REQ-101`) | ✅ |
| 42 non-bearer | §46 (`REQ-102`) | ✅ |
| 43 non-serializability | §47 (`REQ-103..104`) | ✅ |
| 44 restart invalidation | §48 (`REQ-105`) | ✅ |
| 45 one-operation lifetime | §49 (`REQ-106..108`) | ✅ (`.1R.30R.3` invariant stated) |
| 46 rotation | §50 (`REQ-109..110`) | ✅ |
| 47 revocation | §51 (`REQ-111..112`) | ✅ (`{ACTIVE, SUPERSEDED, REVOKED}`) |
| 48 recovery | §52 (`REQ-113..114`) | ✅ (no repo / config recovery) |
| 49 clone / snapshot | §53 (`REQ-115`) | ✅ |
| 50 audit evidence | §54 (`REQ-116..117`) | ✅ (not capability) |
| 51 failure taxonomy | §56 (`REQ-121..122`) | ✅ (21 codes) |
| 52 map failures to RHAMP | §57 (`REQ-123..125`) | ✅ (#1 / #2 / #40 / #41; NO new code) |
| 53 root TCB claim boundary | §60 (`REQ-128`) | ✅ |
| 54 two-principal deployment requirement | §61 (`REQ-129..130`) | ✅ (fail closed) |
| 55 local / offline profile | §62 (`REQ-131`) | ✅ |
| 56 macOS / Linux abstraction | §63 (`REQ-132..133`) | ✅ (property first) |
| 57 no-keychain / no-signing-key | §64 (`REQ-133`) | ✅ |
| 58 HBDC precedent boundary | §65–§66 (`REQ-134..135`) | ✅ |
| 59 no runtime approval | §67 (`REQ-136`) | ✅ (PAWA-INV-2) |
| 60 no PB / RE override | §68 (`REQ-137`) | ✅ (PAWA-INV-8) |
| 61 bootstrap non-circularity | §23, §69 (`REQ-056`, `REQ-138`) | ✅ (PAWA-INV-4) |
| 62 future implementation flow | §70 (`REQ-139`) | ✅ |
| 63 FIDO2 enrollment relationship | §71 (`REQ-140`) | ✅ |
| 64 recovery relationship | §72 (`REQ-141`) | ✅ (no fallback from failed approval) |
| 65 contract-production traceability | §73 (`REQ-142`) | ✅ |
| 66 future implementation source boundary | §74 (`REQ-143`) | ✅ |
| 67 future consumer guards | §75 (`REQ-144`) | ✅ |
| 68 future IV requirements | §76 (`REQ-145`) | ✅ (≥ 24 cases) |
| 69 `.1R.30R.3` successor | §77 (`REQ-146..147`) | ✅ (F-2) |
| 70 downstream sequence | §78 (`REQ-148..149`) | ✅ |
| 71 N-16-6 / N-16-7 ordering | §79 (`REQ-150`) | ✅ (N-16-7 last) |
| 72 PAWA versioning rules | §80 (`REQ-151..154`) | ✅ |
| 73 author HPAC-PAWA-001 v1.0 | this phase | ✅ |
| 74 existing contracts unchanged | §7 below | ✅ |
| 75 production source unchanged | §7 below | ✅ |

---

## 7. Existing-contract byte identity + production-source diff (phase prompt §81–§83)

- `git diff 91741564 HEAD -- src/pcae` — **empty** (`HPAC-PAWA-REQ-156`).
- `git diff --name-only 91741564 HEAD -- docs/contracts` — names **exactly**
  `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (new HPAC-PAWA-001 v1.0), **no existing contract** (`HPAC-PAWA-REQ-003`,
  `HPAC-PAWA-REQ-157`).
- Byte-unchanged (proven at finalization): HPAC-001 v2.1; RHAMP-001 v1.0;
  RIHAC-001 v2.0; RIASC-001 v3.0; HPSE-001 v1.1; HHCE-001;
  `HPAC-AUTHORITY-CONSUMPTION` (`/2.1`); HBDC-001 v1.2; REPRC-001 v1.0;
  PBNDE-001 v1.0; RDGO-001 v3.1; RPAC-001 v1.0; the RE No-Go Registry; every
  other contract.
- No MAJOR or MINOR bump on any existing contract. HPAC-001 stays **v2.1**;
  `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`; RHAMP-001 stays **v1.0**. The only
  version movement is **HPAC-PAWA-001 v1.0 (initial freeze)**.

---

## 8. Runtime state / first external effect / N-16 status (phase prompt §85–§89)

| Item | State (byte-unchanged by `.1R.30R.2`) |
|---|---|
| Runtime state | `Observed` |
| Maximum capability | `observe` |
| Execution availability | `unavailable` |
| Plugins | 0 |
| Capabilities | 0 |
| First external effect | **ABSENT** — no `adapter.dispatch()` call site; no Slice C |
| N-16-5 | **WRITER-ANCHOR CONTRACT FROZEN — IMPLEMENTATION PENDING — NOT CLOSED** |
| N-16-3 / N-16-4 | CLOSED (carried) |
| N-16-6 / N-16-7 | OPEN, untouched; N-16-7 strictly last |
| N-23-1 | INFO (carried unchanged) |
| N-23-2 | INFO / DEFERRED NORMALIZATION DEBT (carried unchanged) |
| `DELEGATED .3 FINALIZATION / COMMIT / PUSH` | **UNAUTHORIZED** — preserved |

---

## 9. Valid early-STOP conditions (phase prompt) — NONE TRIGGERED

Each of the phase prompt's BLOCKED conditions was checked:

| Condition | Result |
|---|---|
| HPAC-PAWA-001 cannot be frozen without modifying HPAC-001 v2.1 | **not triggered** — HPAC-001 §7 froze the *policy*; the mechanism is additive and authority-preserving; companion-contract precedent (REPRC-001 / PBNDE-001 / RHAMP-001) avoids the bump (§1, §5, §6) |
| RHAMP-001 v1.0 must change to support the writer anchor | **not triggered** — RHAMP-REQ-047 externalises the anchor mechanics by its own text; the failure taxonomy maps onto §49 codes #1/#2/#40/#41 with no new `terminal_reason_code` (§57) |
| HBDC-001 Class-B assumptions cannot be expressed safely under HPAC's separate namespace | **not triggered** — HPAC has its own root, namespace, descriptor, capability, consumer inventory, audit lifecycle; HBDC is precedent, not a shared authority root (§65–§66) |
| the contract cannot define the positive anchor without treating euid/root/sudo alone as authority | **not triggered** — §34 prohibits it explicitly; PAWA-INV-1; the trust root is OS filesystem write authority, not `euid` |
| the configured agent-principal exclusion cannot be stated precisely enough to be implementable | **not triggered** — §9 fixes the canonical source of truth; `_effective_write_access` already parameterises `uid` / `gids`; §26 states the exact check (F-1) |
| descriptor generation / rollback semantics cannot be frozen without a larger protected-root lifecycle contract change | **not triggered** — §20 adds a scoped `HPAC-PAWA-CURRENT-GENERATION/1.0` record under the existing `.authority/` namespace using the existing atomic-replace idiom; no protected-root lifecycle contract is amended (F-3) |
| a positive write probe cannot be specified without TOCTOU/aliasing ambiguity that requires broader architecture | **not triggered** — §28–§30: `O_EXCL\|O_NOFOLLOW` create-and-unlink after symlink-component rejection; re-verified at every `record_write` / `_write`; trusted OS boundary + fail-closed conditions defined; no promise of absolute TOCTOU elimination |
| the capability cannot be constrained to process-local / non-bearer / narrow operation scope without changing existing `HPACWriterCapability` semantics | **not triggered** — §40, §45–§49: reuses the existing seal / `__reduce__` / per-instance-identity discipline; the `PRODUCTION` capability is *strictly narrower* (operation-scoped, single-use); single-use is an additive `.1R.30R.3` invariant (a spent flag), never a weakening |
| the out-of-band bootstrap procedure remains circular | **not triggered** — §23, §69: filesystem provisioning by the OS deployment owner; no existing `HPACWriterCapability`, no FIDO2, no prior PCAE principal required (PAWA-INV-4) |
| a machine migration / reprovisioning rule cannot distinguish legitimate rotation from rollback | **not triggered** — §22: legitimate migration = new `installation_id` + fresh root identity + `generation` 1 + explicit out-of-band act; rollback = restore without those → caught by §16/§20/§21 |
| consumer-inventory / non-agent-importable guarantees cannot be stated normatively using existing PCAE guard patterns | **not triggered** — §37–§39: the HBDC-REQ-056/066 text-scan + "not a CLI subcommand" pattern, exact enumeration, no wildcard (`.1R.30R.1` §15.2 confirmed feasible) |
| the contract would accidentally authorize runtime approval, PB, Runtime Enforcement, runtime capability, or execution | **not triggered** — §5, §14, §58, §67, §68, §85, §86; PAWA-INV-2, PAWA-INV-8; the 15-line walls block; the `PRODUCTION` writer authorizes only the 5 closed registry / sidecar / counter-state mutation classes |

**No BLOCKED condition applies.** The contract is frozen; governed finalization
proceeds.

---

## 10. Governance (phase prompt §92, §93)

- **`.3` governance incident (phase prompt §92):** `DELEGATED .3 FINALIZATION /
  COMMIT / PUSH: UNAUTHORIZED` — **preserved verbatim.**
- **Governance rules (phase prompt §93):** no raw `git commit` / `git push`, no
  `--no-verify`, no force push, no history rewrite, no hook bypass. Governed
  `pcae` lifecycle only. This canonical phase document, the HPAC-PAWA-001 v1.0
  contract, the `PROJECT_STATUS.md` / `CHANGELOG.md` / `tasks/DECISIONS.md`
  prose, the task lifecycle, and the completion metadata / report were authored
  and committed by the primary human-authorized operator for `.1R.30R.2` through
  the governed `pcae` lifecycle. No delegated worker committed, finalized, or
  pushed. Only the primary human-authorized operator holds `.1R.30R.2` lifecycle
  authority.

---

## 11. Verdict block

```
HPAC-PAWA-001 v1.0 PRODUCTION PROTECTED-ADMIN WRITER ANCHOR CONTRACT FREEZE:

  HPAC-PAWA-001 v1.0:                 FROZEN (sole normative delta;
                                     HPAC-PAWA-REQ-001..163, PAWA-INV-1..11)
  HPAC-001 v2.1:                      UNCHANGED (no bump)
  RHAMP-001 v1.0:                     UNCHANGED (byte-identical)
  HBDC-001 v1.2:                      UNCHANGED (precedent only)
  PRODUCTION PROTECTED-ADMIN WRITER ANCHOR:  CONTRACT FROZEN -- NOT IMPLEMENTED

  TRUST ROOT   = OS filesystem write authority on the out-of-band-provisioned
                 <HPAC_PROTECTED_ROOT>, configured agent principal provably
                 excluded (F-1)
  RECOGNITION  = fixed-root + not-(configured-)agent-writable + safe ancestors
                 + root-identity-bound .authority/ deployment-owner descriptor
                 (closed schema; monotonic generation + anchored current-
                 generation record + rollback prevention -- F-3)
                 + O_EXCL|O_NOFOLLOW positive write probe
                 + not-(configured-)agent current-context
                 + authorized-factory-consumer     [six, all required; 11 steps]
  ISSUER       = new PRODUCTION writer factory in a non-agent-importable module,
                 EXACT consumer-inventory guarded (no wildcard)
  SCOPE        = one operation, one principal/credential, process-local,
                 non-serializable, non-bearer, restart-invalid, one-operation
  BOOTSTRAP    = one-time out-of-band deployment-owner provision; create-only;
                 non-recurring; not agent-reachable; NON-CIRCULAR
  ROTATION     = explicit; generation += 1; monotonic current-generation anchor
  REVOCATION   = deployment-owner filesystem replace/remove/mark;
                 {ACTIVE, SUPERSEDED, REVOKED}; revoked -> fail closed
  FAILURE      = 21 closed pawa_failure_code; deterministic map onto RHAMP-001
                 v1.0 section 49 codes #1 / #2 / #40 / #41 -- NO new code
  SAME-UID     = no write + no importability + seal identity + __reduce__ raise
                 + live re-probe; single-account host -> no PRODUCTION root ->
                 writer unavailable (fail closed, PAWA-INV-7)

  FINDINGS INCORPORATED:
    F-1  per-predicate identity matrix (contract section 10); negative boundary
         keys off the CONFIGURED agent principal, not os.geteuid(), on the
         writer path (sections 9, 26, 62)
    F-2  .1R.30R.3 (not .1R.30R.2) is the implementation successor
         (contract section 77); historical .1R.30 immutable BLOCKED
    F-3  explicit monotonic descriptor generation + current-generation anchor
         record + rollback-prevention rule (contract sections 20, 21)

  HISTORICAL .1R.30:                  immutable BLOCKED -- never reused/resumed
  FRESH IMPLEMENTATION SUCCESSOR:     149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3
  DOWNSTREAM: .1R.30R.3 (impl) -> .1R.30R.4 (IV) -> .1R.30R.5 (protected
    presentation + real-assurance wiring) -> .1R.30R.6 (IV + real CTAP2
    hardware + N-16-5 closure) -> N-16-6 -> N-16-7 (strictly last).
    No Slice C until N-16-3..7 all close. No phase auto-authorized.

  NO production source change. NO existing-contract change. NO HPAC-001 bump.
  NO writer-anchor implementation. NO HumanPrincipalRegistryStore production
  writer. NO FIDO2. NO credential/counter sidecars. NO enrollment/bootstrap
  tooling. NO protected presentation. NO real approval proof. NO N-16-6/N-16-7.
  NO Slice C. NO first external effect. NO execution enablement.
  Runtime not_implemented / Observed / observe / unavailable; 0 plugins /
  0 capabilities. First external effect ABSENT. N-16-5 NOT CLOSED.
  N-16-6 / N-16-7 OPEN, untouched, N-16-7 last. N-23-1 / N-23-2 carried.

  RECOMMENDED NEXT PHASE: 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3 -- N-16-5
    Production Protected-Admin Writer Anchor + Real FIDO2 Credential Registry
    and Authentication Mechanism Implementation. Own explicit human
    authorization required. Do not begin it.

  DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED -- preserved.

  B30R1 = 91741564  (.1R.30R.1 finalized head / .1R.30R.2 baseline tree)
  E30R2 = 5373ee21  (.1R.30R.2 phase-entry, task-open commit)
```
