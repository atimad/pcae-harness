# Phase 149O.19.4 — HATP Mandatory Independent-Verification Certification Implementation Plan

**Phase type:** IMPLEMENTATION PLAN ONLY. This phase modifies no `src/
pcae/**` file and no contract file. It produces this planning document
and a mechanical planning-completeness test only.

**Governing contract:** HMIC-001 v1.0 (`docs/contracts/
HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`),
status **REPAIRED — INDEPENDENTLY RE-VERIFIED** as of Phase
149O.19.3R.1.

---

## 1. Baseline (Initial Inspection)

Confirmed directly against live repository state at phase entry (commit
`19ed7cab`):

- `git status --short`: clean. `origin/main..HEAD`: 0 commits.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent.
- `pcae doctor task-memory`: warnings only — pre-existing `tasks/done/`
  entries missing from `tasks/DONE.md`, predating this phase, outside
  this phase's allowed-file scope, not remediated here (§14).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: Runtime state **Observed**, maximum capability
  **observe**, execution capability **unavailable**.
- `pcae notify status`: Telegram configured, enabled, ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.19.3R.1`: latest completed phase is 149O.19.3R.1
  (status `completed`, report `complete`); reconciliation confirms
  `status: reconciled`, `mutation: none (inspection only)`.

## 2. HMIC Contract State (Restated)

- **HMIC-001 v1.0**: FROZEN — REPAIRED (149O.19.3R), **INDEPENDENTLY
  RE-VERIFIED** (149O.19.3R.1). Depends on, unamended and byte-unchanged:
  HMRC-001 v1.0, HATP-001 v1.0, HSCE-001 v1.1, RAE-001 v1.0.
- **B-149O.19.3-1** (original 18-file frozen-set under-binding of the
  provider layer): **INDEPENDENTLY CONFIRMED CLOSED** — qualifier
  "frozen implementation identity transitive under-binding repaired."
  The repaired, independently re-verified 22-file frozen set (HMIC-REQ-
  050) is the one this plan uses throughout (§9 below); no prior-phase
  table is trusted as source of truth — the file list below is
  transcribed directly from the live contract text read by this phase.
- **HMRC-001's own `mandatory_consumption_implementation_independently_
  verified`** input fact remains the literal `False` constant at
  `hatp_mandatory_cutover.py` (current line numbers ~836-853; see §9.1).
- **B-149O-1..4**: remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
  IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL
  ACTIVATION DEFERRED, unchanged by this phase (HMIC-REQ-142).

## 3. Current Real State (Independently Re-Confirmed Against Live Source)

- No `certifications.json` or `certification-bindings.json` exists
  anywhere in the repository or under any protected root.
- No certification writer, admin tool, or validator module exists in
  `src/pcae/**` or elsewhere in this repository.
- No production, agent-reachable API named `create_certification`,
  `activate_certification`, `revoke_certification`, or equivalent
  exists (grep of `src/pcae/**` for these symbols returns nothing).
- The hard-coded `mandatory_consumption_implementation_independently_
  verified = False` constant is unchanged and remains the sole current
  value of that readiness term.

## 4. Critical Self-Reference / Validator-Trust Rule (Governs Wave Sequencing)

This is this plan's single most consequential design decision (§10
below expands it in full). Stated up front because it governs every
subsequent wave boundary:

**`hatp_mandatory_cutover.py` is itself item 1 of HMIC-REQ-050's 22-file
frozen set** — the file containing the readiness ceiling this
certification ultimately gates is already inside its own certified
scope. By the identical logic, once a new validator module executes the
comparison logic that decides `VALID`/not-`VALID` and that decision
directly flips real readiness (Wave F, §10 below), that validator
module's own bytes must also be inside the frozen scope — otherwise an
agent could edit the validator to unconditionally return `VALID`
without touching any frozen file, defeating the entire certification
with a change invisible to `implementation_scope_digest`. This is
resolved as a **hard sequencing gate** (§10), not a contract-repair
STOP: Waves A–E build and thoroughly test the new module while it has
zero effect on real readiness (the `False` literal is untouched); a
dedicated HMIC-001 v1.1 contract-amendment phase adds the new module's
files to a repaired HMIC-REQ-050 enumeration and is itself independently
verified; only then may Wave F wire the validator into
`hatp_mandatory_cutover.py`.

## 5. Current HATP Production State (Restated)

HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**. No Class-B provisioning has occurred beyond
the existing 149O.1B.1 admin-principal foundation. No real
`HATP_MANDATORY` activation exists.

---

## 6. HMIC-REQ-001..144 Traceability Table

Ownership legend — modules/roles: `MODEL` = data-model, closed-schema
parsing, and canonical-serialization portion of new
`hatp_mandatory_certification.py` (Wave A); `IDENT` = implementation/
repository/deployment/contract identity-derivation portion of the same
module (Wave B); `STORE` = protected-store read/write/locking portion of
the same module (Wave C); `VALID` = the production validation-algorithm
portion of the same module (Wave D); `ADMIN` = new, separate
`scripts/hatp_certification_admin.py` (Wave E, never imported by `cli.py`
or `commands/agent.py`); `CUT` = modification to existing
`hatp_mandatory_cutover.py` (Wave F, the only wave touching an existing
frozen file); `DOC` = scope/terminology/versioning statement with no
production code owner, satisfied structurally by this plan and by
review discipline in every wave that touches the relevant area; `EXIST`
= an existing, unmodified frozen module reused by name (never
reimplemented).

Every requirement appears exactly once as **primary** owner below; the
`Independent-verification obligation` implicit in every row is carried
by 149O.19.6 (§16), not restated per row.

| Req | Normative meaning (compressed) | Primary owner | Failure/behavior | Test owner | Attack(s) | Wave |
|---|---|---|---|---|---|---|
| 001 | Contract governs only the certification described in §2, no other term/operation class | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 002 | Does not own/redefine Cutover Model, HATP-001, HSCE-001, RAE-001, PBPA/PBPC-001, RWMPC-001 | DOC | n/a — scope statement | Contract byte-identity test | — | N/A |
| 003 | References frozen authorities by exact name; no duplicate parallel implementation | IDENT, STORE | Structural (no parallel impl created) | Wave B/C test modules | — | B, C |
| 004 | Supplies exactly one readiness input fact; does not own the other five HMRC terms | CUT | Structural (single-term wiring only) | Cutover-integration test module | — | F |
| 005 | Not a general software-release/deployment-signing mechanism | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 006 | `activate_hatp_mandatory`, Cutover Record, POL-005, COMP-002 unaffected by this contract | CUT | Structural (no coupling) | Assembled attack suite | 32 | F |
| 007 | Frozen terminology table (Certification, Certification Record, Active-Certification Pointer, etc.) | MODEL | n/a — naming discipline | Model test module docstring/vocabulary assertions | — | A |
| 008 | "Certified"/"certification" never means phase-report/test-pass/commit/status-file completion | DOC, VALID | Structural (validator never consults these) | Validation test module | 1, 2, 3 | D |
| 009 | Semantic walls (§5 list) not collapsed by any implementation, log, status field, or text | MODEL, CUT | Structural vocabulary discipline | Assembled attack suite | 4 | A, F |
| 010 | No `VALID_WITH_WARNING`/partial-credit status satisfies readiness | MODEL | Rejected — enum has no such member | Model test module | — | A |
| 011 | Threat-A capability list (agent can edit/commit/push/call functions/invoke CLI) | DOC | n/a — threat-model statement | Assembled attack suite | 1-7, 27 | G |
| 012 | Agent cannot write Protected Root, cannot forge signature, cannot supply authority value | STORE, ADMIN | Rejected (OS permission boundary) | Store + Admin test modules | 27, 28 | C, E |
| 013 | Class-B Protected Administrator definition (reuses 149O.1B.1) | ADMIN | n/a — principal identity restated | Admin writer test module | — | E |
| 014 | Root/platform compromise (Threat-B) explicitly out of scope | DOC | n/a — scope statement | Planning-completeness test | — | N/A |
| 015 | No overclaim on transitive dependencies; residual limitation named, not hidden | IDENT | n/a — documented limitation | Identity test module docstring | 29 | B |
| 016 | Sole certification authority is Protected Admin Authority (§7, HMIC-REQ-013) | ADMIN | Rejected for any other caller | Admin writer test module | 27 | E |
| 017 | Explicit rejection list: agent principal, same-user CLI, phase code, tests, hooks, env, flag, username, git author, ownership | ADMIN | Rejected — none of these establish authority | Admin writer test module | 5, 6 | E |
| 018 | Agent OS principal has no effective write permission; no in-process authority-check substitute | ADMIN | Structural (OS-level only) | Admin writer test module | 27 | E |
| 019 | Read Authority — agent/runtime MAY read certification files; read ≠ write authority | VALID | n/a — read-only posture | Validation test module | — | D |
| 020 | No application-level fake admin (username/env/flag/ownership/git-author) | ADMIN | Rejected | Admin writer test module | 5, 6 | E |
| 021 | Protected Root is exactly `HATPTrustStore.production().root`; no second root | STORE | Structural (single root resolution) | Store test module | 28 | C |
| 022 | Certification files live under existing root; never merged into `registry.json`/`cutover-record.json` | STORE | Structural (separate files) | Store test module | 7 | C |
| 023 | No env var/CLI flag/config resolves an alternate root | STORE, VALID | Rejected — no such parameter exists | Store + Validation test modules | 28 | C, D |
| 024 | Certification model: protected registry entry (append-only records + separate active-pointer file) | MODEL | n/a — model selection | Model test module | — | A |
| 025 | Exactly two files, frozen names: `certifications.json`, `certification-bindings.json` | STORE | Rejected (no third file introduced) | Store test module | — | C |
| 026 | Both files keyed by `(repository_instance_id, canonical_deployment_root)` per entry | STORE | Structural (keyed dict, not flat slot) | Store + multi-repo test modules | 8, 9, 30 | C |
| 027 | Deliberate improvement over Cutover Record's flat single-slot topology | STORE | n/a — design rationale | Multi-repo test module | 8, 9, 30 | C, G |
| 028 | Local-only; no import/export API; copying files does not certify the copy target | STORE | Rejected via binding checks | Multi-repo test module | 8, 9, 30 | C, G |
| 029 | No cryptographic signature added in v1.0 | MODEL | n/a — design decision, no signature field | Model test module | — | A |
| 030 | No hardware/FIDO2 touch required for certification validation | VALID | n/a — design decision, no HATP proof call | Validation test module | — | D |
| 031 | `certifications.json` schema/version closed: unknown fields, duplicate keys, boolean version all rejected | MODEL | Rejected | Model test module | 16, 17, 18 | A |
| 032 | Exact `CertificationRecord` field set, no more no fewer | MODEL | Rejected on extra/missing field | Model test module | 16 | A |
| 033 | `version` strict positive integer; boolean rejected | MODEL | Rejected | Model test module | 18 | A |
| 034 | `status`/`revoked_at` validated together (mirrors `_require_revoked_at_consistency`) | MODEL | Rejected on inconsistent pair | Model test module | 16 | A |
| 035 | Every field but `status`/`revoked_at` immutable once created; recertify always creates new record | STORE | Structural (append-only, no in-place mutation) | Store test module | — | C |
| 036 | `certification-bindings.json` same closed-schema discipline | MODEL | Rejected | Model test module | 21 | A |
| 037 | `active_certification_id` is the exact `certification_id` string, no path/partial value | MODEL | Rejected on malformed pointer value | Model test module | 21 | A |
| 038 | `certification_id` is SHA-256 hex over canonical serialization of authority-sensitive fields | IDENT | n/a — derivation algorithm | Identity test module | — | B |
| 039 | `certification_id` never caller-supplied free-form; always tool-derived | ADMIN | Rejected (no such admin input) | Admin writer test module | — | E |
| 040 | Self-consistency check: validation re-derives `certification_id`, rejects mismatch as `MALFORMED` | VALID | `MALFORMED` | Validation test module | 16 | D |
| 041 | Every write uses `json.dumps(document, indent=2, sort_keys=True) + "\n"`, UTF-8, `\n` endings | MODEL | Structural | Model test module | — | A |
| 042 | All digest inputs use this exact canonical form; no alternate whitespace/ordering | MODEL, IDENT | Rejected (byte-exact requirement) | Model + Identity test modules | — | A, B |
| 043 | `repository_instance_id` derived exactly as `repository_identity.py`'s existing CRI Layer 1 | IDENT | Structural (calls existing function, no reimplementation) | Identity test module | — | B |
| 044 | `canonical_deployment_root` derived exactly as `hatp_bootstrap.py::resolve_canonical_deployment_root` | IDENT | Structural (calls existing function) | Identity test module | — | B |
| 045 | Both identifiers derived read-only by admin tool at certify time and re-derived read-only by validator | ADMIN, VALID | Rejected as caller input on either path | Admin + Validation test modules | — | E, D |
| 046 | `implementation_commit` is `git rev-parse HEAD` (or equivalent) at certify time | IDENT | n/a — derivation | Identity test module | — | B |
| 047 | Commit SHA alone explicitly insufficient as authority; digest is the load-bearing term | IDENT | n/a — design statement | Identity test module | — | B |
| 048 | Commit-changed, bytes-same ⇒ `IMPLEMENTATION_MISMATCH` | VALID | `IMPLEMENTATION_MISMATCH` | Validation test module | 12 | D |
| 049 | Bytes-changed, commit-same (dirty tree) ⇒ `IMPLEMENTATION_MISMATCH` | VALID | `IMPLEMENTATION_MISMATCH` | Validation test module | 11, 13 | D |
| 050 | Exact 22-file frozen enumeration (HMIC-REQ-050, repeated verbatim from contract text) | IDENT | n/a — literal constant | Identity test module (byte-for-byte match vs. contract) | — | B |
| 051 | Enumeration embedded in contract itself, not an external agent-editable manifest | IDENT | Structural (constant embedded in module source) | Identity test module | — | B |
| 052 | Transitive-dependency closure rule (what must be included/excluded and why) | IDENT | n/a — closure rationale, already applied by contract §17/§49 | Identity test module docstring citing §49's table | — | B |
| 053 | Contract bytes participate directly in digest, distinct from `contract_versions` field | IDENT | Structural (two independent bindings) | Identity test module | — | B |
| 054 | File digest algorithm: SHA-256 over raw on-disk bytes at digest-computation time | IDENT | n/a — algorithm | Identity test module | — | B |
| 055 | Path canonicalization: repo-relative, POSIX separator, case-sensitive, no `..`/absolute | IDENT | Rejected on non-canonical path | Identity test module | — | B |
| 056 | File order: exact lexicographic order of canonical path strings | IDENT | n/a — deterministic order | Identity test module | — | B |
| 057 | Per-file record domain: `path + "\0" + hex_digest + "\n"` | IDENT | n/a — anti-ambiguity framing | Identity test module | — | B |
| 058 | `implementation_scope_digest` = SHA-256 of concatenated ordered per-file records (two-level) | IDENT | n/a — derivation | Identity test module | — | B |
| 059 | Missing frozen file ⇒ creation fails / validation `IMPLEMENTATION_MISMATCH` | IDENT, VALID | Fail closed | Identity + Validation test modules | — | B, D |
| 060 | Extra non-frozen files never affect the digest in either direction | IDENT | n/a — named limitation | Identity test module | — | B |
| 061 | Symlinked frozen file rejected (path or any parent component) | IDENT | Rejected | Identity test module | 19 | B |
| 062 | Non-regular frozen file (dir/FIFO/device/socket) rejected identically to symlink | IDENT | Rejected | Identity test module | 19 | B |
| 063 | Import-shadowing/executed-code binding explicitly out of scope, v1.0 — named, not hidden | IDENT | n/a — documented residual limitation | Identity test module docstring | 29 | B |
| 064 | Scoped exclusively to editable-install/source-checkout topology; wheel mode unsupported | IDENT | n/a — documented scope limit | Identity test module docstring | — | B |
| 065 | Digest does not bind interpreter version, third-party packages, or unlisted transitive imports | IDENT | n/a — documented boundary | Identity test module docstring | — | B |
| 066 | Overclaim restated — stronger than bare commit SHA, consistent with Cutover Record's own trust model | IDENT | n/a — design statement | Identity test module docstring | — | B |
| 067 | Minimal sufficient `contract_versions` set: HMRC-001, HATP-001, HSCE-001, RAE-001 | IDENT | n/a — set definition | Identity test module | — | B |
| 068 | RWMPC-001/PBPA-001/PBPC-001 explicitly excluded from `contract_versions` (PB module bytes still digest-bound) | IDENT | n/a — exclusion rationale | Identity test module | — | B |
| 069 | Contract drift: any `contract_versions` mismatch ⇒ `CONTRACT_MISMATCH`, no compatibility table | VALID | `CONTRACT_MISMATCH` | Validation test module | 14 | D |
| 070 | Future contract-freeze phase MAY widen `contract_versions`; not overbound by default | DOC | n/a — forward-looking statement | Planning-completeness test | — | N/A |
| 071 | `verification_record_digest` is audit/traceability metadata only | MODEL | n/a — schema field | Model test module | — | A |
| 072 | `verification_record_digest`/phase identifier never sufficient/fallback for `VALID` | VALID | Structural (never inspected as authority input) | Validation test module | 2 | D |
| 073 | Phase ID standing alone MAY be descriptive metadata; never a validity condition alone | MODEL | n/a — schema statement | Model test module | 2 | A |
| 074 | Closed prohibition list — repo-local signals never consulted by validation, directly or indirectly | VALID | Structural (validator never reads these paths) | Validation test module | 1, 2, 3 | D |
| 075 | No future implementation replaces `False` with hard-coded `True`; readiness derives only from fresh validator call | CUT | Rejected — no such literal introduced | Cutover-integration test module | 4 | F |
| 076 | Creation-ceremony 7-step sequence (report review → admin tool → tool-derived tuple → confirm → append → distinct activate) | ADMIN | n/a — ceremony sequence | Admin writer test module | — | E |
| 077 | Minimized human-entered authority-sensitive input — no typed repo ID/digest/commit/boolean | ADMIN | Rejected as CLI input | Admin writer test module | — | E |
| 078 | Certifier input minimized — confirmation + `certified_by` + optional verification-record locator only | ADMIN | Rejected on extra authority-bearing input | Admin writer test module | — | E |
| 079 | Writer is a separate admin/deployment tool, not a `pcae` CLI subcommand | ADMIN | Structural (standalone script, outside `src/pcae/`) | Admin writer test module + CLI-surface-absence test | 27 | E |
| 080 | Admin tool resolves Protected Root exactly as production code does; no `--root` override in production mode | ADMIN | Rejected (no override flag) | Admin writer test module | 28 | E |
| 081 | Ordinary `pcae` CLI MUST NOT expose write/revoke; read-only inspection MAY be added later, non-misleading | ADMIN | Structural (no CLI wiring in any wave) | CLI-surface-absence test module | 27 | E |
| 082 | No agent-reachable write API of any name; only path is the separate admin tool | ADMIN | Structural (no such symbol exported from `src/pcae/`) | Admin writer + CLI-surface-absence test modules | 27 | E |
| 083 | Every write uses `mkstemp` + `fsync` + `os.replace` atomic idiom (mirrors `_atomic_write_json`) | STORE | Structural (no partial write observable) | Store test module | — | C |
| 084 | Create-once for immutable records; write fails (never silently overwrites) on conflicting content | STORE | Rejected (conflicting content) / no-op (identical content) | Store + concurrency test modules | 26 | C, G |
| 085 | `certification-bindings.json` is the only way a validator learns the active certification; no implicit-latest | VALID | Structural (no sort-by-`certified_at`) | Validation test module | 22 | D |
| 086 | Creating a record does not auto-activate it; activation requires a second explicit admin write | ADMIN, STORE | Structural (two distinct write operations) | Admin + Store test modules | 32 | E, C |
| 087 | Recertification creates a new record; old record never mutated to reflect new implementation | ADMIN | Structural (append-only) | Admin writer test module | 10 | E |
| 088 | Making a new certification active requires a separate explicit admin write | ADMIN | Structural | Admin writer test module | — | E |
| 089 | Old-implementation/old-contract replay rejected purely by §33 comparison steps, no special-cased flag | VALID | `IMPLEMENTATION_MISMATCH` / `CONTRACT_MISMATCH` | Validation test module | 10, 14 | D |
| 090 | Only the Active-Certification Pointer's named record is ever consulted, even with multiple records present | VALID | Structural | Validation test module | 22 | D |
| 091 | Revocation is field mutation (`status`/`revoked_at`), never deletion | ADMIN | Structural (record remains present) | Admin writer test module | — | E |
| 092 | Revocation names the exact `certification_id`; no "revoke latest/active" implicit form | ADMIN | Rejected (no implicit-selection API) | Admin writer test module | — | E |
| 093 | Revocation requires the same Protected-Root write access as creation | ADMIN | Rejected for non-admin caller | Admin writer test module | 27 | E |
| 094 | Revoked active certification ⇒ validation `REVOKED`; revoked non-active record has no readiness effect | VALID | `REVOKED` | Validation test module | 23 | D |
| 095 | Revocation/drift after `HATP_MANDATORY` never causes a mode downgrade — no reverse transition edge exists | CUT | Structural (HMRC's own transition graph, unmodified) | Cutover-integration regression test | 11 | F |
| 096 | Post-activation invalid certification MAY feed a future diagnostic signal; not implemented this contract | DOC | n/a — explicitly deferred, not scheduled in any wave | Planning-completeness test | — | N/A |
| 097 | Dedicated `.certification-transition.lock` under Protected Root, distinct from `.cutover-transition.lock` | STORE | Structural (separate lock file) | Store test module | — | C |
| 098 | Creation race deterministic — second writer observes first's committed state via precondition check | STORE | No-op or fail, never silent overwrite | Concurrency test module | 26 | G |
| 099 | Supersession race deterministic — later write wins, no ambiguous intermediate state | STORE | Deterministic final pointer | Concurrency test module | 26 | G |
| 100 | Revocation race fail-safe ordering — later write observes earlier's already-written state | STORE | Deterministic, never half-applied | Concurrency test module | 26 | G |
| 101 | Certification read-only validation does not acquire `.certification-transition.lock`; no nesting with cutover lock | VALID | Structural (lockless read path) | Validation + cutover-integration test modules | — | D, F |
| 102 | Lock file path fixed under Protected Root; no caller-suppliable lock path | STORE | Rejected (no such parameter) | Store test module | 28 | C |
| 103 | 12-step validation algorithm, executed fresh every invocation | VALID | n/a — algorithm | Validation test module | — | D |
| 104 | Steps evaluated in exact order; first failing step determines status; no skip-ahead | VALID | Structural (ordered short-circuit) | Validation test module | — | D |
| 105 | Root/file access failure ⇒ `MISSING` (absence) or `ACCESS_ERROR` (I/O error); no auto-provisioning | VALID | `MISSING` / `ACCESS_ERROR` | Validation test module | 15, 20 | D |
| 106 | Closed Validation Status vocabulary (9 values); unrecognized future value treated as failure | MODEL | Rejected (fails closed on unknown) | Model test module | 18 | A |
| 107 | Readiness mapping — exactly `VALID` maps `True`; every other status maps `False` | MODEL, VALID | Structural binary mapping | Model + Validation test modules | — | A, D |
| 108 | No partial certification; non-blocking diagnostic detail never substitutes for binary status | MODEL | Structural (no such field influences readiness) | Model test module | — | A |
| 109 | Conceptual production validation entrypoint signature `(repository_root: Path) -> <typed result>` | VALID | n/a — API shape | Validation test module | — | D |
| 110 | No caller-suppliable authority input (`implementation_digest=`, precomputed commit/contract versions) | VALID | Rejected (no such parameter) | Validation test module | 27 | D |
| 111 | Production root resolution closed — no caller-suppliable root override | VALID | Rejected (no override parameter) | Validation test module | 28 | D |
| 112 | Test seam accepts explicit `protected_root: Path`; production entrypoints never accept it | VALID | Structural (internal-only parameter) | Validation test module | — | D |
| 113 | No validity cache — every readiness assessment re-runs the full algorithm | VALID | Structural (no memoization) | Validation test module | 24, 31 | D |
| 114 | Replace literal `False` with a call to the validation entrypoint, mapped per HMIC-REQ-107 | CUT | Structural (single call-site replacement) | Cutover-integration test module | 4 | F |
| 115 | Locked recheck inside `activate_hatp_mandatory` via existing `readiness_check` hook, no new lock/hook signature | CUT | Structural (reuses existing hook exactly) | Cutover-integration test module | 26 | F |
| 116 | Earlier advisory `ready=True` mints no token/capability; a later `activate_hatp_mandatory` recomputes fresh | CUT | Structural (no carry-forward authority) | Cutover-integration test module | 31 | F |
| 117 | Revocation/working-tree change between advisory call and locked activation is observed fresh | CUT, VALID | Fail closed on drift observed at recheck time | Cutover-integration test module | 24, 25 | F |
| 118 | `CERTIFY` and `ACTIVATE` remain separate ceremonies, same principal, never combined | ADMIN, CUT | Structural (no combined API) | Assembled attack suite | 32 | E, F |
| 119 | Admin MAY certify without activating (certify well ahead of cutover window) | ADMIN | n/a — permitted workflow | Admin writer test module | — | E |
| 120 | `VALID` certification satisfies one term only; does not itself cause `PREPARED → HATP_MANDATORY` | CUT | Structural (readiness conjunction unchanged otherwise) | Cutover-integration test module | 34 (analog) | F |
| 121 | No code path invoked by `activate_hatp_mandatory` creates/activates/revokes a certification | CUT | Structural (no writer import in cutover module) | Cutover-integration test module | 32 | F |
| 122 | No certification operation constructs or evaluates a Permission Broker request | MODEL, STORE, VALID, ADMIN | Structural (no PB import anywhere in new module/script) | Assembled attack suite | — | A-E |
| 123 | No certification operation writes/derives/influences `rollback_approval_state` or any RAE artifact | MODEL, STORE, VALID, ADMIN | Structural (no RAE import) | Assembled attack suite | — | A-E |
| 124 | No certification operation creates/grants/influences runtime execution capability, COMP-002, or COMP-008 | MODEL, STORE, VALID, ADMIN | Structural (no such side effect) | Assembled attack suite | — | A-E |
| 125 | POL-005/COMP-002 unaffected; certification validity does not change PB `ALLOW`/`DENY`/`HUMAN_REVIEW` | CUT | Structural (no PB coupling in Wave F) | Cutover-integration test module | — | F |
| 126 | Bootstrap circularity forbidden — certification authority never requires an already-activated deployment | ADMIN | Structural (admin tool has no dependency on cutover mode) | Admin writer test module | — | E |
| 127 | Certification ceremony does not require/invoke/depend on real or simulated AG3/AG5 execution | ADMIN | Structural (no rollback-execution import) | Admin writer test module | — | E |
| 128 | Symlink rejection for Protected Root, every parent, and both certification files | STORE | Rejected | Store test module | 19 | C |
| 129 | No path traversal via `certification_id`; structurally eliminated (single shared files, no per-cert path) | STORE, IDENT | Structural (no path built from the ID) | Store test module | — | C |
| 130 | `certified_at`/`certified_by` are informational/audit metadata only, not standalone authority | MODEL | n/a — schema statement | Model test module | — | A |
| 131 | `certified_by` is not cryptographic proof of identity | MODEL | n/a — documented limitation | Model test module docstring | — | A |
| 132 | Any future inspection surface's wording SHALL NOT read "certification valid" as "rollback permitted" | DOC | n/a — deferred (no inspection surface scheduled this plan) | Planning-completeness test | — | N/A |
| 133 | `CertificationRecord` contains no secret material — identity/digest/timestamp/reference fields only | MODEL | Rejected on secret-shaped field | Model test module | — | A |
| 134 | HMIC-001 owns certification only; HMRC/HATP/RAE/PBPA/PBPC ownership unmodified | DOC | n/a — statement | Contract byte-identity test | — | N/A |
| 135 | HMIC-001 supplies exactly one input fact; not wired to influence the other five HMRC terms | CUT | Structural (single-term wiring, verified in Wave F) | Cutover-integration test module | — | F |
| 136 | No activation-contract redefinition — Cutover Model/transition graph/HMRC requirement unchanged | CUT | Structural (no edit to transition graph) | Cutover-integration regression test | — | F |
| 137 | No PB-contract redefinition — PBPA-001/PBPC-001 vocabulary/rules unmodified | DOC | n/a — statement | Contract byte-identity test | — | N/A |
| 138 | No general-deployment-certification overreach — scope stays narrowly HMRC-001 consumption | DOC | n/a — statement | Planning-completeness test | — | N/A |
| 139 | Contract frozen as HMIC-001 v1.0 | DOC | n/a — identity statement | Contract byte-identity test | — | N/A |
| 140 | Unknown future HMIC-001 version fails closed | MODEL | Rejected | Model test module | 18 | A |
| 141 | Implementation readiness statement — every referenced area frozen, no authority-sensitive TBD | DOC | n/a — readiness statement, satisfied by this plan's own §6-§10 | Planning-completeness test (this phase) | — | N/A |
| 142 | B-149O-1..4 closure criteria — not met by contract freeze/repair/this plan alone | DOC | n/a — closure-criteria statement | 149O.19.6 + future certification-ceremony phase | — | N/A |
| 143 | Contract self-consistency search performed — no contradictory authority statement found | DOC | n/a — self-consistency statement | Contract byte-identity + planning-completeness tests | — | N/A |
| 144 | No self-certification path — CIVC-12 restated | ADMIN, VALID | Structural (agent principal has no write path, validator never trusts stored claims) | Assembled attack suite | 1-7, 27 | E, D |

**Coverage check (mechanical, encoded in §12's planning-verification
test):** 144/144 requirement IDs appear in the table above exactly once
in the "Req" column (001–144, contiguous, no gaps, no duplicates — these
IDs are mechanically re-extracted from HMIC-001's own live contract
text, `\*\*HMIC-REQ-(\d{3})\b`, not copied from this plan's prose).

---

## 7. CIVC-1..12 Traceability Table

| Invariant | Production enforcement point | Test owner | Attack(s) | Wave | Independent-verification obligation |
|---|---|---|---|---|---|
| CIVC-1 (repo-local metadata non-authoritative) | `VALID` — validator's §31 algorithm never opens `PROJECT_STATUS.md`/`tasks/**`/`CHANGELOG.md`/any phase report/`.pcae/**`/test results/env vars | Validation test module | 1, 2, 3 | D | 149O.19.6 greps the merged validator for any read of these paths |
| CIVC-2 (only Protected Admin Authority creates/activates/revokes) | `ADMIN` — sole writer, outside agent-reachable `pcae` CLI, gated by real OS permissions | Admin writer + CLI-surface-absence test modules | 27 | E | 149O.19.6 attempts every write op as the ordinary agent OS principal |
| CIVC-3 (exact repository/deployment match) | `IDENT` derives, `VALID` step 7 compares | Identity + Validation test modules | 8, 9 | B, D | 149O.19.6 exercises copied-certification cross-repo/cross-deployment scenarios |
| CIVC-4 (exact implementation match, both terms) | `IDENT` derives fresh, `VALID` step 9 compares | Identity + Validation test modules | 10, 11, 12, 13 | B, D | 149O.19.6 mutates each of the 22 frozen files individually and re-validates |
| CIVC-5 (contract versions match current headers) | `IDENT` derives, `VALID` step 10 compares | Identity + Validation test modules | 14 | B, D | 149O.19.6 mutates each of the 4 bound contracts' version headers in an isolated copy |
| CIVC-6 (exactly one authoritative cert via explicit pointer, no implicit latest) | `STORE` (pointer file), `VALID` step 4/85 (only consults explicit pointer) | Store + Validation test modules | 22 | C, D | 149O.19.6 populates multiple records and confirms only the pointed-to one is ever read |
| CIVC-7 (fresh revalidation every call, no cache) | `VALID` — no memoized status anywhere in the module | Validation test module | 24, 25, 31 | D | 149O.19.6 confirms via direct-call repeat-attempt tests across a state change |
| CIVC-8 (fail closed, no partial credit) | `VALID` — every non-`VALID` branch maps to `False` | Validation test module | 15-21 | D | 149O.19.6 exercises each of the 8 non-`VALID` status branches individually |
| CIVC-9 (VALID necessary, never sufficient, never auto-causes activation/PB/capability) | `CUT` — Wave F wiring touches only the one readiness term | Cutover-integration test module | 32 | F | 149O.19.6 confirms a `VALID` certification alone does not flip any other readiness term |
| CIVC-10 (no source constant/env/caller boolean substitutes for validated certification) | `VALID`, `MODEL` — no such parameter/constant exists | Model + Validation test modules | 4, 5, 6 | A, D | 149O.19.6 inspects signatures directly (`inspect.signature`) for forbidden parameters |
| CIVC-11 (revocation after activation never downgrades mode) | `CUT` — HMRC-001's own transition graph has no reverse edge; Wave F adds nothing to it | Cutover-integration regression test | 11 (structural) | F | 149O.19.6 re-confirms the transition graph is byte-identical to HMRC-001's frozen shape |
| CIVC-12 (no self-certification — agent cannot derive authority from any agent-writable artifact) | `ADMIN`, `VALID` — structurally independent write path; validator re-derives, never trusts stored claims | Assembled attack suite | 1-7, 27 | E, D | 149O.19.6 attempts every §41 self-certification-class attack directly against merged code |

**Coverage check:** 12/12 invariants present, each with at least one
concrete production enforcement point and at least one wave.

---

## 8. 32-Attack Traceability Table

| # | Attack (compressed) | Expected result | Test file (planned) | Wave |
|---|---|---|---|---|
| 1 | Fake `PROJECT_STATUS.md` completion entry | No effect — CIVC-1 | `tests/test_hmic_attack_matrix.py::test_fake_project_status_no_effect` | G |
| 2 | Fake/forged phase-report document | No effect — CIVC-1 | `tests/test_hmic_attack_matrix.py::test_fake_phase_report_no_effect` | G |
| 3 | Fabricated passing test-suite output | No effect — CIVC-1 | `tests/test_hmic_attack_matrix.py::test_fake_test_results_no_effect` | G |
| 4 | Source edit replacing `False` ceiling with `True` | Forbidden by HMIC-REQ-075; not certification | `tests/test_hmic_attack_matrix.py::test_hardcoded_true_forbidden_by_review_discipline` | G |
| 5 | Environment variable asserting "verified" | Structurally impossible — no such input | `tests/test_hmic_attack_matrix.py::test_env_var_no_effect` | G |
| 6 | CLI boolean flag asserting "verified" | Structurally impossible — no such input | `tests/test_hmic_attack_matrix.py::test_cli_boolean_no_effect` | G |
| 7 | Repo-local fabricated certification JSON under `.pcae/` | No effect — never read from `.pcae/` | `tests/test_hmic_attack_matrix.py::test_repo_local_fake_cert_no_effect` | G |
| 8 | Wrong-repository certification (copied repo A → repo B) | Rejected — `WRONG_REPOSITORY` | `tests/test_hmic_multi_repository.py::test_wrong_repository_rejected` | G |
| 9 | Wrong-deployment certification (same repo, different root) | Rejected — `WRONG_DEPLOYMENT` | `tests/test_hmic_multi_repository.py::test_wrong_deployment_rejected` | G |
| 10 | Old-implementation replay (cert X presented for modified impl Y) | Rejected — `IMPLEMENTATION_MISMATCH` | `tests/test_hmic_attack_matrix.py::test_old_implementation_replay_rejected` | G |
| 11 | Dirty frozen file, incl. a hardware-provider file (e.g. `hatp_fido2_provider.py` unconditional `True`) | Rejected — `IMPLEMENTATION_MISMATCH` | `tests/test_hatp_mandatory_certification_identity.py::test_each_of_22_files_dirty_rejected` | B, G |
| 12 | Commit changed, frozen-file bytes unchanged | Rejected — `IMPLEMENTATION_MISMATCH` | `tests/test_hatp_mandatory_certification_validation.py::test_commit_changed_bytes_same_rejected` | D |
| 13 | Commit unchanged, frozen-file bytes changed | Rejected — `IMPLEMENTATION_MISMATCH` | `tests/test_hatp_mandatory_certification_validation.py::test_commit_same_bytes_changed_rejected` | D |
| 14 | Contract-version replay (bound contract revised, stale cert re-applied) | Rejected — `CONTRACT_MISMATCH` | `tests/test_hatp_mandatory_certification_validation.py::test_contract_drift_rejected` | D |
| 15 | Missing certification (no record for pointer's ID) | `MISSING` | `tests/test_hatp_mandatory_certification_validation.py::test_missing_record_rejected` | D |
| 16 | Corrupt certification record (malformed JSON, unknown field) | `MALFORMED` | `tests/test_hatp_mandatory_certification_models.py::test_malformed_record_rejected` | A |
| 17 | Duplicate JSON keys in either file | `MALFORMED` | `tests/test_hatp_mandatory_certification_models.py::test_duplicate_keys_rejected` | A |
| 18 | Unknown/future schema version | `MALFORMED`/unsupported | `tests/test_hatp_mandatory_certification_models.py::test_unknown_version_rejected` | A |
| 19 | Symlinked certification file, pointer file, or Protected Root/parent | Rejected | `tests/test_hatp_mandatory_certification_store.py::test_symlink_rejected` | C |
| 20 | Missing Active-Certification Pointer entirely | `MISSING` | `tests/test_hatp_mandatory_certification_validation.py::test_missing_pointer_rejected` | D |
| 21 | Corrupt Active-Certification Pointer file | `MALFORMED` | `tests/test_hatp_mandatory_certification_models.py::test_malformed_pointer_rejected` | A |
| 22 | Implicit-latest attempt (sort by `certified_at`, select newest) | Structurally impossible | `tests/test_hatp_mandatory_certification_validation.py::test_no_implicit_latest_selection` | D |
| 23 | Revoked active certification | `REVOKED` | `tests/test_hatp_mandatory_certification_validation.py::test_revoked_active_cert_rejected` | D |
| 24 | Certification deleted after earlier advisory check, retried before activation | Fresh recheck `MISSING`, fails | `tests/test_hatp_mandatory_cutover_certification_integration.py::test_deleted_between_advisory_and_activation` | F |
| 25 | Certification superseded between earlier check and later activation attempt | Fresh recheck sees current pointer | `tests/test_hatp_mandatory_cutover_certification_integration.py::test_superseded_between_advisory_and_activation` | F |
| 26 | Concurrent revoke and activate/create race | Deterministic via `.certification-transition.lock` | `tests/test_hmic_concurrency.py::test_revoke_activate_race_deterministic` | G |
| 27 | Agent attempts to call a certification writer/writer API directly | No such production-reachable API exists | `tests/test_hmic_attack_matrix.py::test_no_agent_reachable_writer_api` | G |
| 28 | Attacker-controlled alternate root injection | Production validator always resolves `HATPTrustStore.production().root` | `tests/test_hatp_mandatory_certification_validation.py::test_no_root_override_accepted` | D |
| 29 | Import-shadowing / `sitecustomize` / `PYTHONPATH` injection | Named residual limitation — out of scope v1.0, not silently claimed solved | `tests/test_hatp_mandatory_certification_identity.py::test_residual_limitation_documented_not_solved` | B |
| 30 | Certification files copied between two different Protected Roots/deployments | Rejected via repository/deployment binding (#8/#9) | `tests/test_hmic_multi_repository.py::test_copy_attack_rejected` | G |
| 31 | Stale readiness token reuse (earlier `ready=True` presented at later activation) | Rejected — activation always recomputes under lock, no token minted | `tests/test_hatp_mandatory_cutover_certification_integration.py::test_no_stale_token_carry_forward` | F |
| 32 | Certification creation auto-activates, or activation auto-creates a certification | Structurally impossible — no coupling code path | `tests/test_hmic_attack_matrix.py::test_certify_and_activate_never_coupled` | G |

**Coverage check:** 32/32 attacks present, each with a concrete
(planned) test file and implementation wave; no attack depends only on
documentation.

---

## 9. Selected Module Architecture

### 9.1 Reused vs. New Primitives

| Concept | Reused from (unmodified) |
|---|---|
| Repository identity (CRI Layer 1) | `repository_identity.py` |
| Deployment identity (CRI Layer 2) | `hatp_bootstrap.py::resolve_canonical_deployment_root` / `DeploymentBinding` |
| Protected root | `HATPTrustStore.production().root` (`hatp_bootstrap.py`) |
| Strict timestamp grammar | `hatp_mandatory_cutover.py::_TIMESTAMP_PATTERN` (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`) |
| Atomic write / symlink rejection idiom | `hatp_mandatory_cutover.py::_atomic_write_json` / `_reject_symlink` pattern (`mkstemp`+`fsync`+`os.replace`) |
| Status/`revoked_at` consistency | `hatp_bootstrap.py::_require_revoked_at_consistency` pattern |
| `certified_by`-style authority string | `CutoverRecord.activated_by` (caller-supplied, no default, no env/process derivation) |
| Locked-recheck hook shape | `hatp_mandatory_cutover.py::_write_cutover_transition`'s `readiness_check: Callable[[], ...]` hook (call site ~lines 669-681) |
| Test-only root seam | `HATPTrustStore.__init__`'s `_test_only_root` parameter pattern |
| Canonical serialization | `json.dumps(document, indent=2, sort_keys=True) + "\n"` (used verbatim by `repository_identity.py` and `hatp_mandatory_cutover.py`) |

Only new artifacts: `certifications.json`, `certification-bindings.json`
(both under the existing `HATPTrustStore.production().root` — no second
protected root; confirmed distinct from, and not to be confused with,
`HATPHardwareCredentialStore`'s own sibling `hardware-credentials` root),
`.certification-transition.lock`, and the code implementing them.

### 9.2 Module Decomposition — One New Core Module, One Separate Admin Script

**Decision: a single new core module**, `src/pcae/core/
hatp_mandatory_certification.py`, mirroring `hatp_mandatory_cutover.py`'s
own precedent of housing model, identity-derivation, storage, locking,
and validation logic for one authority concern in one file (that
existing module is ~980 lines and is the direct, closest analog — same
authority tier, same Protected Root, same principal). Splitting into
multiple core modules was considered and rejected: HMIC-001's storage
topology (§9, HMIC-REQ-024-027) is explicitly modeled as one concern
with two files, not several independently-versioned concerns, so a
single owning module is the more accurate reflection of the contract's
own boundary, not merely convenience.

**Decision: a second, separate file outside `src/pcae/`**, `scripts/
hatp_certification_admin.py`, implementing the create/activate/revoke
admin ceremony (HMIC-REQ-079). This is a standalone script — never
imported by `cli.py`, `commands/agent.py`, or any other `src/pcae/**`
module — invoked manually (`python scripts/
hatp_certification_admin.py create|activate|revoke ...`) by an operator
running under the Class-B admin OS principal, the only principal with
real write access to `HATPTrustStore.production().root`. It imports
`hatp_mandatory_certification`'s internal (non-`__all__`-exported)
writer functions directly; it is not packaged, not installed as a
console-script entry point, and not reachable from any agent-executable
code path. This resolves HMIC-REQ-079-082 (writer surface / no
agent-reachable write API) exactly as HMIC-REQ-079's own module-docstring
citation of `hatp_mandatory_cutover.py`'s "no in-process authority-check"
conclusion requires: the real enforcement boundary is OS file
permissions on the Protected Root, not an in-process gate inside the
agent-reachable `pcae` binary.

### 9.3 `hatp_mandatory_certification.py` — Internal Structure (by Wave)

```
Wave A  — CertificationStatus (9-value enum, HMIC-REQ-106)
          CertificationRecord (frozen dataclass, HMIC-REQ-032)
          CertificationBinding (frozen dataclass, HMIC-REQ-036)
          _load_json_no_duplicate_keys-style strict parser (closed schema)
          _canonical_serialize(document) -> bytes  (HMIC-REQ-041)
          no filesystem I/O; pure functions and types only

Wave B  — _FROZEN_AUTHORITY_BEARING_FILES: tuple[str, ...]  (HMIC-REQ-050,
              literal 22-path constant, transcribed byte-for-byte from
              the contract; see §9.4)
          derive_repository_instance_id() -> str      (calls repository_identity.py)
          derive_canonical_deployment_root() -> str    (calls hatp_bootstrap.py)
          derive_implementation_commit() -> str        (git rev-parse HEAD)
          derive_implementation_scope_digest() -> str  (HMIC-REQ-054-062)
          derive_contract_versions() -> dict[str, str] (reads 4 contract headers)
          derive_certification_id(record_fields) -> str (HMIC-REQ-038)

Wave C  — _certification_transition_lock(protected_root) -> contextmanager
              (fcntl.flock on ".certification-transition.lock")
          _read_certifications(protected_root) -> ...
          _read_certification_bindings(protected_root) -> ...
          _append_certification_record(...)     [internal, admin-only caller]
          _write_active_binding(...)             [internal, admin-only caller]
          _write_revocation(...)                 [internal, admin-only caller]
          all writers use the mkstemp+fsync+os.replace atomic idiom (§9.1)

Wave D  — validate_active_hatp_mandatory_independent_verification_certification(
              repository_root: Path,
          ) -> HMICValidationResult
          _validate_at_root(protected_root: Path, repository_instance_id: str,
              canonical_deployment_root: str) -> HMICValidationResult
              [test-only seam accepting explicit protected_root; the
              public wrapper above always resolves
              HATPTrustStore.production().root internally]
          implements the exact 12-step algorithm (HMIC-REQ-103), no cache
```

`hatp_mandatory_certification.py` never imports `permission_broker.py`,
`permission_broker_foundation.py`, `rollback_approval_evidence.py`, or
any AG3/AG5 execution path (HMIC-REQ-122-124).

### 9.4 22-File Manifest Ownership

`_FROZEN_AUTHORITY_BEARING_FILES` is an **immutable source constant
derived directly from the contract freeze** (prompt-option "a" of the
candidate mechanisms), embedded as a literal Python tuple in
`hatp_mandatory_certification.py`, not a generated file and not an
externally-editable manifest. A dedicated Wave B test
(`test_hatp_mandatory_certification_identity.py::
test_manifest_matches_contract_enumeration_exactly`) asserts this
constant is string-for-string identical to HMIC-REQ-050's literal
22-path list, re-extracted from the live contract text at test time —
so any future contract/code drift fails a test immediately rather than
silently diverging. This choice was preferred over a "generated
constant with contract-backed test" because the file list changes only
on a contract amendment (a rare, already-governed event, per HMIC-REQ-
051), and a literal constant is simpler and equally safe under that
event frequency.

### 9.5 Admin Input Surface (Wave E)

Per HMIC-REQ-077-078, `scripts/hatp_certification_admin.py` accepts,
interactively, only: (a) confirmation of the tool-derived target tuple
it displays; (b) `certified_by` (free-text operator identity string,
audit metadata only); (c) an optional verification-record locator if
not auto-derivable. It never accepts a repository ID, digest, commit
SHA, or a "verified=True"-shaped boolean as input.

### 9.6 Read-Only Inspection Surface

**Not scheduled in any 149O.19.5* wave.** HMIC-REQ-081 permits, but does
not require, a future read-only `pcae`-CLI inspection command. Per
prompt-section-52 guidance ("do not add unless useful/contract-owned"),
this plan does not schedule one; if a future phase adds it, HMIC-REQ-132
already frozen the exact wording constraint that phase must honor
("certification valid" must never read as "rollback permitted").

---

## 10. Self-Reference Disposition & HMIC v1.1 Amendment Sequencing (Wave Gate)

This section resolves prompt items 16-17 (self-reference of future HMIC
code / implementation-scope evolution) and prompt items 105-106,
133-136 (stop conditions) concretely, using the exact HMIC contract
interpretation — not an improvised default.

### 10.1 The Precedent Already in the Contract

HMIC-REQ-050's frozen 22-file set already includes `core/
hatp_mandatory_cutover.py` as its **first** entry — the exact file that
contains the readiness ceiling this certification gates, and the exact
file `activate_hatp_mandatory` lives in. This is not an oversight: it
establishes the contract's own precedent that **the code enforcing a
readiness gate must itself be inside the scope that certification
protects.** §49's own "Future HMIC validator self-reference /
circularity disposition" paragraph makes this precedent explicit:
"self-binding a validator to the identity it computes is not
automatically circular — `hatp_mandatory_cutover.py` already binds
itself into HMRC-001's own implicit trust boundary the same way." §49
explicitly defers the *timing and mechanism* of applying this precedent
to the new HMIC validator's own future implementation phase — this
plan is that phase.

### 10.2 The Concrete Risk If Left Unresolved

`hatp_mandatory_certification.py`'s `validate_active_hatp_mandatory_
independent_verification_certification(...)` function is what Wave F
wires directly into the (currently `False`) readiness term. If that
function's own bytes are never bound by any digest, an agent could edit
its comparison logic — e.g. replace step 9's byte-comparison with an
unconditional `return HMICValidationResult(status=VALID, ...)` — and
this edit would be **invisible** to `implementation_scope_digest`,
because that module is not itself a member of `_FROZEN_AUTHORITY_
BEARING_FILES`. This is a strictly analogous risk to the one B-149O.19.3-1
found and 149O.19.3R repaired for the hardware-provider layer (§49) —
except here the vulnerable code is the validator itself, not a
transitive dependency of it.

### 10.3 Resolution — Hard Sequencing Gate, Not a Contract-Repair STOP

This is answerable without an ambiguous or missing contract clause
(so prompt item 133's STOP condition is **not triggered**), because the
contract already supplies the precedent (§10.1) and already anticipates
this exact question deferring only its *timing* (§49). This plan
resolves the timing as follows:

1. **Waves A-E** (§9.3) build `hatp_mandatory_certification.py` and
   `scripts/hatp_certification_admin.py` completely, and Wave G tests
   them exhaustively — including all 32 attacks — **while
   `hatp_mandatory_cutover.py`'s `False` literal remains untouched.**
   During this window the new module has **zero effect on real
   readiness**; an edit to it (malicious or accidental) changes nothing
   observable in production, because nothing calls it yet. No STOP
   condition applies to this window.
2. **Before Wave F may begin**, a dedicated **HMIC-001 v1.1
   contract-amendment phase** (recommended name: `149O.19.4A — HMIC-001
   v1.1 Validator Self-Binding Amendment`, or repository-conventional
   equivalent) SHALL widen HMIC-REQ-050's frozen enumeration to add
   `src/pcae/core/hatp_mandatory_certification.py` (and, if by that time
   any additional new production file exists, e.g. a future shared
   helper), and that amendment phase SHALL itself be independently
   verified before Wave F starts. This satisfies prompt item 17 exactly:
   HMIC v1.0 did not already define future-implementation-source
   ownership (§49 says so explicitly), so a v1.1 amendment is required,
   not optional, before the file set that decides `VALID`/non-`VALID`
   is allowed to actually gate real readiness.
3. **Wave F itself** (§9's `CUT` wiring) SHALL NOT be started until step
   2's amendment is both merged and independently verified. This is
   recorded as this plan's own explicit **Stop Condition W-1** (§13).
4. `scripts/hatp_certification_admin.py` (the admin writer) is
   **explicitly not required** to join the frozen set — see §10.4.

### 10.4 Admin-Writer Trust Disposition (Prompt Item 106)

The admin writer does not need certified-scope protection because the
validator (§9.3 Wave D) never trusts anything the writer wrote at face
value: HMIC-REQ-103 step 9 recomputes `implementation_commit`/
`implementation_scope_digest` fresh from the current working tree and
*compares* against the stored record; step 10 recomputes
`contract_versions` fresh and compares; step 11 re-derives
`certification_id` and compares. A compromised or buggy writer can at
worst produce a record that **fails to validate** (a denial, safe) —
it cannot produce a record that validates `VALID` without the writer
having actually run the same real derivation logic the validator itself
re-runs, because the validator never accepts the writer's own computed
values as authoritative (HMIC-REQ-107-110, "validator must re-derive").
This is proven structurally, not merely asserted: no field of
`HMICValidationResult` construction in Wave D ever reads a boolean or
digest directly out of the loaded `CertificationRecord` and returns it
as the outcome without an independent recomputation and comparison
first.

### 10.5 Executed-Source Binding (Prompt Items 23-25) — Explicitly Out of Scope, Not Solved Here

HMIC-REQ-063 already names import-shadowing / executed-code-resolution
binding as an explicit v1.0 residual limitation, not silently claimed
solved. This plan implements no `importlib.util.find_spec`-based
origin check in v1.0, consistent with the contract's own disposition —
adding one would be implementing a check the frozen contract explicitly
declines to require, and no wave in this plan does so. Attack #29
(§8) is deliberately mapped to "named residual limitation, documented,
not solved" rather than to a passing defense test.

---

## 11. Test Plan Summary

| Test module (new) | Wave | Scope |
|---|---|---|
| `tests/test_hatp_mandatory_certification_models.py` | A | Schema closure, strict parsing, canonical serialization, status enum |
| `tests/test_hatp_mandatory_certification_identity.py` | B | Repo/deployment/commit/digest/contract-version derivation, 22-file manifest byte-match, residual-limitation docstring presence |
| `tests/test_hatp_mandatory_certification_store.py` | C | Atomicity, create-once, symlink rejection, locking, path-traversal-freedom |
| `tests/test_hatp_mandatory_certification_validation.py` | D | Full 12-step algorithm, all 9 status outcomes, no-cache, no-override |
| `tests/test_hatp_certification_admin.py` | E | Ceremony steps, minimized input, no auto-activate, no PB/RAE/AG3/AG5 coupling |
| `tests/test_hatp_mandatory_cutover_certification_integration.py` | F | `False`→validator wiring, locked recheck, freshness consequences |
| `tests/test_hmic_attack_matrix.py` | G | Attacks 1-7, 27, 29 (documented-not-solved), 32 |
| `tests/test_hmic_concurrency.py` | G | Attacks 26, 98-100-class races |
| `tests/test_hmic_multi_repository.py` | G | Attacks 8, 9, 30 |
| (independent verification, no new production code) | 149O.19.6 | Re-derivation of all tables directly from merged code, not this plan |

All write-path tests use isolated `tmp_path`-style protected roots
(§9.3's `_test_only_root`/`protected_root` seam); no test ever writes
`HATPTrustStore.production().root`.

---

## 12. Planning Verification Test (This Phase's Own Deliverable)

`tests/test_phase_149o_19_4_hmic_implementation_plan_completeness.py`
(created by this phase) mechanically verifies, by parsing the actual
files rather than trusting this document's prose:

- Exactly 144 requirement rows, 001-144, contiguous, no duplicates, in
  §6's table, matching a fresh `\*\*HMIC-REQ-(\d{3})\b` extraction from
  the live contract text.
- Exactly 12 CIVC rows in §7, matching a fresh extraction of `**CIVC-`
  entries from the live contract text.
- Exactly 32 attack rows in §8, matching HMIC-001 §41's own table.
- Every requirement/attack row has a non-empty owner, test file, and
  wave column.
- §15's file ownership matrix names every file referenced by §6/§9.
- `git diff --name-only <entry-commit>..HEAD -- src/pcae/` is empty.
- All 8 upstream contracts (HMIC-001, HMRC-001, HATP-001, HSCE-001,
  RAE-001, RWMPC-001, PBPA-001, PBPC-001) are byte-unchanged since phase
  entry.
- This document declares "IMPLEMENTATION PLAN ONLY" and states the
  frozen plan verdict string (§18).
- Stop Condition W-1 (§13) is present in the document text.

---

## 13. Implementation Stop Conditions (Confirmed Applicable, None Blocking *This* Phase)

| ID | Condition (from HMIC-001 / governing prompt) | Disposition for waves A-G |
|---|---|---|
| S-1 (validator identity) | If validator code can be modified without being protected by certification trust | **Resolved, not triggered** — §10.3's HMIC-001 v1.1 amendment gate (Stop Condition W-1 below) closes this before Wave F |
| S-2 (admin principal) | If agent/admin writer authority cannot be separated | **Not triggered** — Class-B OS-permission separation already exists (149O.1B.1); §9.2's standalone-script design preserves it |
| S-3 (executed source) | If runtime-source binding cannot prove certified source executes | **Named, not solved** (§10.5) — contract itself defers this (HMIC-REQ-063); not a blocker for v1.0 |
| S-4 (locking) | If revocation/supersession/activation cannot be linearized safely | **Not triggered** — single dedicated lock file with a strict, contract-frozen ordering rule (HMIC-REQ-097-102) |
| S-5 (protected root) | If production wrapper would accept attacker-selected root/env redirection | **Not triggered** — §9.3 Wave D's production entrypoint has no such parameter, by construction |
| S-6 (contract drift) | If implementation reveals HMIC v1.0 ambiguity requiring contract repair | **Not triggered this phase** — no ambiguity found during this planning pass; §10's self-reference question was resolved using the contract's own explicit precedent/deferral (§49), not an improvised default |
| **W-1 (this plan's own gate, §10.3)** | **Wave F (hard-coded-`False` replacement) SHALL NOT begin until a HMIC-001 v1.1 contract amendment adds `hatp_mandatory_certification.py` to the frozen file set, and that amendment is independently verified.** | **Binding on all future implementation phases; not satisfied by this plan alone** |

No stop condition blocks Waves A-E, G, or 149O.19.6 from proceeding once
separately scoped as their own governed phases. Only Wave F is gated,
and only on W-1.

---

## 14. Historical Debt (Restated, Not Inherited, Not Remediated Here)

- `pcae doctor task-memory` warnings (multiple `tasks/done/` entries
  predating this phase, missing from `tasks/DONE.md`) — pre-existing,
  outside this phase's allowed-file scope, not remediated here.
- HMRC's own flat single-slot Cutover Record topology limitation
  (HMIC-REQ-027 restates this as the exact defect HMIC's own
  repository/deployment-keyed design deliberately avoids repeating) —
  historical, not this phase's concern to fix in `hatp_mandatory_
  cutover.py` itself.
- The optional, non-blocking documentation gap noted at the close of
  149O.19.3R.1 (an explicit HMIC contract-repair-history table row for
  `hatp_signing_ceremony.py`) — recorded, not addressed by this
  planning-only phase; not authority-sensitive, per that phase's own
  finding.
- The double-`Z` CPython 3.9 `fromisoformat` parser debt (149O.16.2
  lineage) — unrelated repository-wide parser debt; `_TIMESTAMP_
  PATTERN` reuse (§9.1) inherits the same, already-hardened pattern
  `hatp_mandatory_cutover.py` uses today, not the older permissive one.

---

## 15. Production File Forecast and Ownership Matrix

| File | New/Modify | Requirements owned (ranges) | Invariants owned | Attacks covered | Wave | Reason |
|---|---|---|---|---|---|---|
| `src/pcae/core/hatp_mandatory_certification.py` | NEW | 007-010, 019, 024-045 (model+identity portion), 046-073, 083-094 (store portion), 097-113 (lock+validation portion), 122-124, 128-129, 130-131, 133, 140, 144 (validation portion) | CIVC-3 – CIVC-8, CIVC-10 (model/identity/store/validation portions), CIVC-12 (validation portion) | 8-26, 28-30 | A, B, C, D | Sole owner of certification model, identity derivation, protected store, and validation engine |
| `scripts/hatp_certification_admin.py` | NEW | 012-013, 016-020, 039, 045, 076-082, 086-088, 091-093, 118-119, 126-127, 144 (admin portion) | CIVC-2, CIVC-12 (admin portion) | 5, 6, 27 | E | Sole owner of the protected create/activate/revoke ceremony; not agent-reachable |
| `src/pcae/core/hatp_mandatory_cutover.py` | MODIFY (Wave F only, gated by W-1, §13) | 004, 006, 075, 095, 101 (cutover portion), 114-117, 120-121, 125, 135-136 | CIVC-9, CIVC-11 | 4, 11 (structural), 24-26, 31-32, 34-analog | F | Sole call site of the readiness-term wiring; **only** existing frozen file this plan's waves modify, and only after W-1 clears |
| `src/pcae/core/repository_identity.py` | **NOT MODIFIED** | n/a (reused by IDENT via public API) | CIVC-3 (reused) | — | n/a | CRI Layer 1 identity already correct and frozen |
| `src/pcae/core/hatp_bootstrap.py` | **NOT MODIFIED** | n/a (reused by IDENT/STORE via public API) | CIVC-3 (reused) | — | n/a | `HATPTrustStore.production()`/`resolve_canonical_deployment_root` already sufficient |
| `src/pcae/core/hatp_ag_authority.py`, `hatp_rollback_consumption.py`, `human_approval_trusted_provenance.py`, `rollback_approval_evidence.py`, `hatp_evidence_store.py`, `hatp_signed_evidence.py`, `agent.py`, `commands/agent.py`, `cli.py`, `permission_broker.py`, `permission_broker_foundation.py`, `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`, `hatp_hardware_credentials.py` | **NOT MODIFIED** | n/a (they are the *subject* of certification, per HMIC-REQ-050, not an implementation target) | — | 11 (their dirtiness is what attack 11 exercises against the digest, not against their own code) | n/a | These 15 files plus the 4 contract files ARE the frozen 22-file certified subject; HMIC's implementation hashes them, never edits them (§17, HMIC-REQ-050) |
| `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` (HMIC-001) | **NOT MODIFIED this phase** — a future v1.1 amendment phase (W-1, §10.3) modifies it before Wave F | n/a | — | — | (pre-F gate) | Amendment is a separate, dedicated future phase, not this plan |

No file above lacks normative ownership; no requirement/invariant/attack
lacks a file. This matrix is the same information as §6-§10, restated in
file-first order for the required final-report field.

---

## 16. Independent Verification Strategy (149O.19.6, Reserved)

149O.19.6 must, independently (not by trusting this plan's own tables):

- Re-derive all 144 requirements, 12 invariants, and 32 attacks directly
  from HMIC-001's live text (mirroring 149O.19.3/149O.19.3R.1's own
  mechanical-extraction method), then independently map each to the
  actual merged production code — not to this plan document.
- Independently re-walk the 22-file transitive-dependency closure
  (mirroring 149O.19.3R's own `ast`-based re-walk) against whatever
  `hatp_mandatory_certification.py`/`scripts/
  hatp_certification_admin.py` actually import, confirming neither
  introduces a new unbound authority-sensitive dependency the contract
  did not already name.
- Confirm the HMIC-001 v1.1 amendment (W-1, §10.3) was itself
  independently verified, byte-for-byte, before Wave F merged — this is
  the single highest-priority check, since it is the one this plan's
  own self-reference resolution depends on entirely.
- Independently attempt all 32 attack scenarios against the real merged
  code, including at least one genuine direct-writer-import bypass
  attempt and one genuine "edit the validator, don't touch a frozen
  file" attempt (expected: rejected once W-1's amendment is in force;
  this is the concrete test of §10.2's risk).
- Exhaustively inventory every caller of `validate_active_hatp_mandatory_
  independent_verification_certification` — a fresh grep-based audit,
  not a citation of this plan's assumption that only `hatp_mandatory_
  cutover.py` calls it.
- Formally re-assess B-149O-1..4 closure; expected still unmet (no real
  certification, no Class-B provisioning, no activation planned by
  149O.19.5A-G).

---

## 17. Retained Findings (Restated, Unchanged by This Phase)

- **B-149O.19.3-1** — INDEPENDENTLY CONFIRMED CLOSED (149O.19.3R.1),
  unchanged.
- **149O.19.3R.1's optional documentation gap** (`hatp_signing_
  ceremony.py` contract-repair-history table row) — non-blocking,
  restated (§14), not addressed here; not authority-sensitive.
- **`pcae doctor task-memory` warnings** — pre-existing, unchanged
  (§14).
- **B-149O-1..4** — remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
  IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL
  ACTIVATION DEFERRED, unchanged.
- **New (149O.19.4, informational only, not a numbered finding):** this
  plan's own Stop Condition W-1 (§13) — recorded explicitly so 149O.19.4A
  and 149O.19.6 do not have to rediscover the validator-self-reference
  sequencing requirement independently; they must still *independently
  verify* it holds, not merely cite this row.

---

## 18. Plan Verdict

```
HMIC-001 IMPLEMENTATION PLAN:
COMPLETE
— READY FOR BOUNDED IMPLEMENTATION
```

All 144 requirements, 12 invariants, and 32 attacks are mapped to a
concrete module/script, test file, and implementation wave. No
authority-sensitive decision is left for implementation to improvise:
the one genuinely novel authority-sensitive question this phase found
— future-validator self-reference (§10) — is resolved with a concrete,
contract-grounded answer (a HMIC-001 v1.1 amendment gate, Stop Condition
W-1) rather than deferred again. Waves A-E and G may begin as soon as
each is separately scoped as its own governed phase; Wave F is
additionally gated on W-1 clearing first.

## 19. Recommended Next Phase

**149O.19.5A — HMIC Certification Data Models + Canonical Parsing.**
This is the correct base layer: it depends on nothing new (pure
dataclasses/enums/parsers, §9.3 Wave A), blocks nothing else from being
independently testable, and every downstream wave (B's identity
derivation, C's store, D's validator) needs its types first. This plan
does **not** authorize 149O.19.5B-G in advance — each subsequent wave,
and the W-1 v1.1 amendment phase before Wave F, should be proposed and
scoped as its own governed phase once the prior wave is independently
verified complete.

## 20. Final Confirmations

No `src/pcae/**` production source was modified this phase. HMIC-001
remained byte-unchanged. HMRC-001 remained byte-unchanged. HATP-001
remained byte-unchanged. HSCE-001 remained byte-unchanged. RAE-001
remained byte-unchanged. RWMPC-001/PBPA-001/PBPC-001 remained
byte-unchanged. The hardcoded `False` readiness ceiling remained
unchanged. No certification artifact/pointer/revocation state was
created. No Cutover Record/activation marker was created or modified.
No real `HATP_MANDATORY` activation occurred. No Class-B provisioning
occurred. No Permission Broker behavior changed. `POL-005` remained
unchanged. No `COMP-002` capability was implemented. B-149O.19.3-1
remains independently closed. B-149O-1..4 remain independently closed
at the system implementation/enforcement boundary with deployment/
operational activation deferred. HATP production remains **NOT READY**.
Runtime remains **Observed / observe / unavailable**.

**Recommended next phase: 149O.19.5A — HMIC Certification Data Models +
Canonical Parsing.**
