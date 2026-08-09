# Phase 149O.19.2 — HATP Mandatory Independent-Verification Certification Contract Freeze

**Phase type:** Contract-freeze only. No `src/pcae/**` file, and no
existing contract file (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`,
`RWMPC-001`, `PBPA-001`, `PBPC-001`), was created, amended, or modified
to produce this phase. No certification artifact, active-certification
pointer, or revocation record was created. No `HATP_MANDATORY`
activation occurred. The current hard-coded `mandatory_consumption_
implementation_independently_verified = False` ceiling
(`hatp_mandatory_cutover.py:842-853`) is unchanged.

---

## 0. Baseline (Confirmed by Direct Inspection)

At phase entry: repo clean except this phase's own task-lifecycle
transition; `origin/main..HEAD = 0`; `pcae health`/`pcae check` passed;
`pcae push check` reported `nothing_to_push`. Latest completed phase was
149O.19.1 — **HATP Mandatory Activation Independent-Verification
Certification Architecture** — verdict **SELECTED — READY FOR CONTRACT
FREEZE**, recommending exactly this phase (149O.19.2) next. B-149O-1..4
remain **INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/
ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED**.
HATP production remains **NOT READY**. Runtime remains **Observed /
observe / unavailable**.

## 1. What This Phase Builds On

149O.19.1 selected, without leaving any authority-sensitive item open,
every architectural decision this phase needed to freeze into normative
contract text:

- Authority principal: `PCAE_BOOTSTRAP_ADMIN_PRINCIPAL` (same as
  HMRC-001's Protected Activation Authority).
- Protected root: reuse `HATPTrustStore.production().root` — no new
  root.
- Certification model: a protected registry entry (append-only keyed
  `CertificationRecord` entries plus a separate explicit active-pointer
  file), not a single flat artifact and not a monotonic latch.
- Two files, repository/deployment-keyed from the start:
  `certifications.json`, `certification-bindings.json`.
- Implementation identity: git commit SHA **plus** a canonical digest
  over an explicit, frozen authority-bearing file set — with an
  honestly-disclosed residual transitive-dependency/import-shadowing
  limitation, not claimed solved.
- Minimal contract binding set: HMRC-001, HATP-001, HSCE-001, RAE-001
  (RWMPC-001/PBPA-001/PBPC-001 explicitly excluded from the version-
  binding field, though PB module *bytes* remain in the frozen file
  set).
- Local-only, unsigned (v1.0), no hardware-touch requirement.
- Explicit active-certification pointer — no implicit-latest selection,
  ever.
- Separate CERTIFY/ACTIVATE ceremonies; a separate, non-agent-writable
  admin writer tool; no agent-reachable write API.
- Revocation as field mutation (never deletion); never causes a
  `HATP_MANDATORY` mode downgrade.
- No cache, fresh validation on every readiness/activation call, with
  the certification check folded into the existing locked
  `_write_cutover_transition` recheck hook.

This phase's job was to take every one of these selections — several of
which 149O.19.1 explicitly deferred in *exact* mechanism form (the
digest algorithm; the frozen file-set enumeration; the typed failure
vocabulary) — and freeze them as gapless, numbered, normative
requirements, resolving every remaining ambiguity 149O.19.1 flagged but
intentionally left open for this phase.

## 2. Central Ambiguities This Contract Had to Resolve

Three items 149O.19.1 explicitly deferred, resolved here:

1. **Exact digest algorithm and concatenation domain.** 149O.19.1 said
   only "a canonical SHA-256 digest computed over the sorted,
   concatenated byte contents" — a scheme vulnerable to concatenation
   ambiguity (two different file-content splits could hash
   identically). This contract freezes a two-level construction
   instead: hash each frozen file's bytes first, then hash the ordered,
   null-byte-and-newline-delimited list of `path\0digest\n` records
   (HMIC-REQ-054-058). This is self-delimiting and eliminates the
   ambiguity without weakening anything 149O.19.1 selected.
2. **Exact frozen authority-bearing file-set enumeration.** This
   contract embeds a literal, 18-file list (HMIC-REQ-050) — the union of
   149O.19.1 §9's own core set and this phase's governing instruction's
   named minimum transitive-dependency evaluation list — directly in
   the contract text, not in a separately-versioned external manifest,
   so no agent-editable list can silently narrow certified scope
   (HMIC-REQ-051).
3. **Exact typed failure vocabulary.** 149O.19.1 §19 presented a
   non-frozen concept. This contract freezes a nine-value closed
   vocabulary (`MISSING | MALFORMED | WRONG_REPOSITORY |
   WRONG_DEPLOYMENT | IMPLEMENTATION_MISMATCH | CONTRACT_MISMATCH |
   REVOKED | ACCESS_ERROR | VALID`) with an exact 12-step validation
   algorithm ordering (§31 of the contract) and a binary readiness
   mapping (exactly `VALID` → `True`; everything else → `False`).

## 3. What Was Frozen

`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
CONTRACT.md` — **HMIC-001 v1.0**, status `FROZEN — READY FOR
INDEPENDENT CONTRACT VERIFICATION`. 144 sequential, gap-free numbered
requirements (`HMIC-REQ-001`–`HMIC-REQ-144`), 12 security invariants
(`CIVC-1`–`CIVC-12`), and a 32-scenario mandatory attack matrix. Full
requirement categories are indexed in the contract's own §39.

Every governing-prompt item (1–175 of the phase instruction) maps to at
least one contract clause; none was silently dropped. In particular:

- Semantic walls extending HMRC-001 §5: contract §5.
- Threat model, authority principal, write/read authority: contract
  §6-7.
- Protected root, storage topology, multi-repository keying: contract
  §8-9.
- Certification/active-pointer schema, closed-field discipline, version
  strictness: contract §11-13.
- Certification-ID derivation, canonical serialization: contract §13-14.
- Implementation identity in full — commit component, frozen file set,
  digest algorithm, path canonicalization, file order, per-file record
  domain, missing/extra/symlink/non-regular file handling, and the
  named import-shadowing/editable-install/wheel residual limitations:
  contract §16-19.
- Contract binding set and drift detection: contract §20.
- Verification-record reference as evidentiary-only metadata: contract
  §21.
- The closed prohibition list (`PROJECT_STATUS.md`, `tasks/TODO.md`,
  `CHANGELOG.md`, test results, commit-message strings, environment
  variables, CLI booleans, source constants): contract §22.
- Creation ceremony, writer surface, agent-write prohibition: contract
  §23-24.
- Storage write safety/atomicity: contract §25.
- Active-certification binding / no-implicit-latest: contract §26.
- Supersession, revocation, post-activation-loss behavior: contract
  §27-29.
- Concurrency and lock ordering (including the certification-lock vs.
  cutover-transition-lock deadlock hazard): contract §30.
- The 12-step validation algorithm, closed status vocabulary, binary
  readiness mapping: contract §31-32.
- Validation API shape, freshness discipline, activation-readiness
  integration, and the locked recheck: contract §33-34.
- Explicit CERTIFY/ACTIVATE non-causation, including bootstrap-
  circularity and PB/POL-005/COMP-002 non-interaction: contract §35.
- Path safety and certification-ID validation: contract §36.
- Audit-metadata semantics and inspection-output wording constraints:
  contract §37.
- Cross-contract relationship and explicit non-redefinition of HMRC-001/
  HATP-001/RAE-001/PBPA-001/PBPC-001: contract §38.
- The 12 security invariants and the 32-scenario attack matrix: contract
  §40-41.
- Contract self-consistency statement, verdict, and next-phase
  recommendation: contract §45-47.

## 4. What Was Explicitly Not Done

No `src/pcae/**` file was created or modified. No existing contract
file (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`, `RWMPC-001`,
`PBPA-001`, `PBPC-001`) was modified — independently confirmed byte-
unchanged (§6 below). No certification artifact, active-certification
pointer, or revocation record was created under any protected root. No
Cutover Record or activation marker was created or modified. No real
`HATP_MANDATORY` activation occurred. No Class-B provisioning occurred.
No Permission Broker behavior changed. `POL-005` was not touched.
`COMP-002` was not implemented. The hard-coded `False` readiness
ceiling was not replaced with `True` or with any other stand-in.

## 5. Carried-Forward, Non-Blocking Items

- The residual transitive-dependency/import-shadowing limitation named
  by 149O.19.1 §9 is carried forward, unresolved, and explicitly named
  in the frozen contract itself (HMIC-REQ-063) rather than hidden or
  silently claimed solved. It is deferred, not blocking, per 149O.19.1's
  own disposition.
- B-149O-1..4 remain independently closed at the system implementation/
  enforcement boundary with deployment/operational activation deferred,
  unchanged by this phase (contract §44, HMIC-REQ-142).
- HATP production remains NOT READY; runtime remains Observed / observe
  / unavailable — unchanged by this phase (contract §48).

## 6. Contract Verification Performed This Phase

A dedicated test module,
`tests/test_phase_149o_19_2_hatp_mandatory_independent_verification_
certification_contract_freeze.py`, independently re-verifies — by
direct document and source inspection, not by trusting the contract's
own prose:

- the frozen contract identity, version, and status string;
- the requirement-ID sequence (001–144, gap-free, no duplicates);
- the exact `CIVC-1`..`CIVC-12` invariant set and count;
- the exact 32-row, sequentially-numbered attack matrix;
- that every one of the 18 frozen authority-bearing file-set paths
  (HMIC-REQ-050) exists on disk today (existence only — this does not,
  and cannot, certify their bytes);
- that the four bound contracts' own current version headers still
  match the `contract_versions` values this contract freezes
  (`HMRC-001` 1.0, `HATP-001` 1.0, `HSCE-001` 1.1, `RAE-001` 1.0);
- that this phase's own commits touched no `src/pcae/**` file and no
  existing contract file (`HMRC-001`, `HATP-001`, `HSCE-001`, `RAE-001`,
  `RWMPC-001`, `PBPA-001`, `PBPC-001`);
- self-consistency: no dual/OR legacy-fallback language, no implicit-
  latest language, no partial-credit validation status.

## 7. Required Final Report

See the phase-completion report/metadata staged alongside this
document for the exact commit, test, and push accounting.

**Contract verdict:**

```
HMIC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION
```

**Recommended next phase:** `149O.19.3` — HATP Mandatory Independent-
Verification Certification Contract Independent Verification.

**B-149O-1..4:** remain INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM
IMPLEMENTATION/ENFORCEMENT BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION
DEFERRED.

**HATP production:** remains NOT READY.

**Runtime:** remains Observed / observe / unavailable.
