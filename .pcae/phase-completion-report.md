# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1 — Dedicated Independent Verification of HPAC-PAWA-001 v2.0 and HPAC-PAWA-HELPER-001 v1.0

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-CONTRACT-IV** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE — NOT VERIFIED / BLOCKED**
- Predecessor: **N16-5-F-5-TB-CONTRACT** (COMPLETE — CONTRACT FROZEN), canonical finalizing HEAD `3cdc3c08` (also this phase's entry HEAD)
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `validate` no error; `format(parse(candidate)) == candidate`; `compare` == `less`; same series `149`; same branch `O`; exactly one appended `.1` segment; exact canonical text; unique against `git log --all` and `docs/` / `tasks/` / `.pcae/`; no conflicting active governed phase); alias display-only, no discrepancy

## Verdict

- **N16-5-F-5-TB-CONTRACT-IV: COMPLETE — NOT VERIFIED / BLOCKED.**
- **Mandatory HPAC-PPA-001 evidence-writer-delivery adjudication: B — HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED.** HPAC-PAWA-HELPER-001 v1.0 §17 (HPAC-PAWA-HELPER-REQ-070) freezes `presentation_evidence_write` as *invoked by the HPAC-PPA-001 presentation helper itself*, which materially conflicts with HPAC-PPA-001 v1.0 HPAC-PPA-REQ-041 (*"held only by the trusted launcher mediator … never sent to the helper"*), HPAC-PPA-REQ-054 (*"evidence producer is only the launcher mediator"*), HPAC-PPA-REQ-052 (a distinct evidence-writer-issuer module), and PPA-INV-2 (helper response and evidence writer are distinct trust actions with no authority transfer). Moving the writer-holder is a MAJOR-class change under HPAC-PPA-REQ-069, not a within-properties platform adapter (HPAC-PPA-REQ-070). §25 / §45 of the authorizing prompt forbid a third "deferred" outcome. Per §45, option B ⇒ this IV is NOT VERIFIED / BLOCKED.
- **Required successor (derived, NOT begun):** a fresh governed HPAC-PPA-001 contract-evolution phase moving its presentation-evidence-writer authority out of process (into the verified presentation helper), aligned with HPAC-PAWA-001 v2.0 §42F / HPAC-PAWA-HELPER-001 §17.
- **Every other load-bearing IV criterion was independently established** from primary contract text (see the canonical Phase Report §41 roll-up). The v2.0 PAWA-side authority model is sound; the block is the un-adjudicated HPAC-PPA-001 dependency of one operation-vocabulary member. **This IV edits no normative contract.**
- **F-5-B2: BLOCKED.** **F-5: CERTIFICATION BLOCKED.** **N-16-5: NOT CLOSED.** **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last).** **REPORTING-UX-1: open, non-blocking.**

## Entry state and predecessor confirmation

Branch `main`; HEAD == `origin/main` == `3cdc3c08`; `origin/main..HEAD` = 0;
working tree clean; no conflicting active governed phase. Predecessor
**N16-5-F-5-TB-CONTRACT** confirmed COMPLETE (contract frozen) from
`PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`
(`status: completed`), `.pcae/phase-completion-report.md`, the canonical report
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_N16_5_F_5_TB_CONTRACT.md`, and
the governed done task.

## Byte baselines

- **HPAC-PAWA-001 v2.0** — blob `c5bf6dc1…`, header `# HPAC-PAWA-001 v2.0 —`, `**Version:** 2.0`, `**Status:** FROZEN`. Requirement ids contiguous `HPAC-PAWA-REQ-001` … `HPAC-PAWA-REQ-340` (340, no gaps, no duplicates); v2.0 additions exactly 310–340. Invariants `PAWA-INV-1` … `PAWA-INV-17`, each once. Every v1.0–v1.4 requirement body survives byte-verbatim (commit `b34cc348` reverted a transient mid-list edit to keep every v1.x body verbatim; supersession expressed only by appended notes + the §7D delta table).
- **HPAC-PAWA-HELPER-001 v1.0** — blob `bbf8c1d3…`, header `# HPAC-PAWA-HELPER-001 v1.0 —`, `**Version:** 1.0`, `**Status:** FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING`. Requirement ids contiguous `HPAC-PAWA-HELPER-REQ-001` … `HPAC-PAWA-HELPER-REQ-114` (114, no gaps). Invariants `PAWAH-INV-1` … `PAWAH-INV-10`, each once.
- **`git diff --name-only 3cdc3c08 HEAD -- docs/contracts`** — EMPTY (this IV edits no contract byte).
- **Sibling contracts byte-unchanged** since the v2.0 freeze commit: HPAC-001 v2.1, RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1, and the protected-root schemas.

## MAJOR (S-4) classification — VERIFIED

Independently re-walked `HPAC-PAWA-REQ-152` (verbatim MAJOR triggers) with the
**closed** `HPAC-PAWA-REQ-153` MINOR-permit enumeration and §80. v2.0 replaces a
normative recognition predicate (§32 predicate 6 / §33 step 9) and restructures
the authority-delivery model (§36–§38 / §41 / §42B / §42D / §33B) — outside every
§153 permit; §153's *"provided no meaning above changes"* clause is not
satisfied. The *"replacing an unsound predicate with a stronger one is a §153
tighten-a-bound"* counter-argument is **rejected** (a tightening keeps the same
predicate and narrows its acceptance set; this substitutes a structurally
different out-of-process predicate and changes which OS actor performs the
operation). `configure_privileged_helper` alone would be a permissible §153
metadata-mutation family; it rides along with the MAJOR. **No §152 verbatim
trigger fires literally** — the one-shot channel is a **local** private
parent/child pipe / `AF_UNIX` socket (not remote / network / cloud); the trust
root is unchanged (PAWA-INV-17); `helper_sha256` is a content-integrity digest
(not a cryptographic authority key) and is defense-in-depth *in addition to,
never a substitute for* the filesystem properties (PAWAH-INV-3); the consumer
inventory is not widened by wildcard but **replaced by the stronger**
`exec`'d-from-the-verified-helper property. **MAJOR (S-4) is the only sound
classification.** A dedicated IV is mandatory (§80 / §80.5 / `HPAC-PAWA-REQ-330`;
not foldable) — this phase is that IV.

## §33C `TrustedProtectedAuthorityConsumer` conjunction — VERIFIED

`HPAC-PAWA-REQ-311` composes the frozen replacement for §32 predicate 6 / §33
step 9 as a **13-conjunct AND** (RegisteredGenerationMatch;
ProtectedHelperFilesystemPropertiesValid; HelperIntegrityBindingValid;
VerifiedExecutionObjectValid; ProtectedProcessPrincipalValid; PrivateChannelValid;
PeerCredentialValid; PAWAOSRecognitionValid; ConfiguredAgentIdentityBindingValid;
RequestSchemaValid; ClosedOperationMembershipValid;
OperationSpecificAuthorityPredicatesValid; FreshnessAndReplayPredicatesValid),
admitted **iff ALL** hold, failure of **ANY** a hard **DENY / fail-closed**
(§42H), **no** single conjunct sufficient (`HPAC-PAWA-REQ-312` — not the channel
fd, not `euid == 0` / `sudo`, not an env var, not the executable path, not the
helper hash alone, not the launcher identity alone, not the peer credential
alone), **no** caller self-assertion, **no** in-process fallback, runs fresh on
every `exec`. The canonical Phase Report carries the full per-conjunct matrix
(what each proves, what it does not prove, its §42H failure code, whether
caller-controlled, whether bypassable). **NO SINGLE CONJUNCT IS SUFFICIENT
AUTHORITY.**

## Same-interpreter production predicate — ELIMINATED (VERIFIED)

`HPAC-PAWA-REQ-315` — under v2.0 the ordinary PCAE interpreter contains **no**
`HPACWriterCapability` / `HPACStoreAuthority` / `CertificationReadAuthority` /
`ProductionWriterHandle` for any `PRODUCTION` class, and the recognition
predicate is **not** `_verified_production_caller_name` / `_detect_caller_module`
/ the `_PINNED_*` dicts / an in-process `_PRODUCTION_WRITER_FACTORY_SEAL` check.
`HPAC-PAWA-REQ-316` — trust rests on none of: module / function name;
`__module__` / `__file__`; `inspect.stack()` textual identity; `sys.modules`
keys; mutable module globals; closure hiding; in-process bearer-object
possession; a filesystem path alone; digest consistency alone. No hidden
normative fallback remains; the compatibility-shim prohibition appears ≥ 3×. The
*physical* removal of the in-process mechanism from `src/pcae` is a later
governed slice; the **normative text** no longer sanctions it as a production
authority root.

## No authority-object export · closed operation vocabulary · single trust root — VERIFIED

- **PAWA-INV-15 / -16 / -17**, §42F `HPAC-PAWA-REQ-322`, HELPER §24 / PAWAH-INV-1: no production privileged authority object crosses the helper boundary **by name and by semantic equivalence** (including "any reconstructable field set from which a bearer writer could be recreated outside the helper"). The caller receives only `decision` + `evidence_ref` / `evidence_digest` + (for `certification_read` / `ceremony_entry`) `result_payload` = enumerated §42D record contents / an acknowledgement — *"Nothing else."*
- Closed five-member operation vocabulary (`admin_mutation` | `certification_write` over the closed five roles | `certification_read` over the enumerated §42D set | `ceremony_entry` | `presentation_evidence_write`); unknown / prefix / wildcard / unrecognized-version → DENY; `operation_params` a closed typed struct per operation; `supported_operations` gating.
- `configure_privileged_helper` (§42G) is metadata-only — cannot create / copy / `chmod` / `chown` / execute helper bytes; driven through the §33C helper boundary itself; non-circular bootstrap; `PawaOperation` count 6 → 7. The helper registration is an integrity-pinned artifact of the existing kind, **not** a second trust root.

## Helper protocol — VERIFIED

Same-file-object anti-TOCTOU **property** (mechanism = platform profile;
substitution-free exec or **STOPS BLOCKED**) feasible on both the macOS
development host (`LOCAL_PEERCRED` / `getpeereid`; `fexecve`) and the Linux
deployment target (`SO_PEERCRED`; `execveat(AT_EMPTY_PATH)` / `fexecve`);
kernel-authenticated peer-credential authentication preceding operation
admission **and** any protected-store read, never from a peer-supplied field,
deployment-owner and not the configured agent principal; configured-agent
identity resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0`, never `os.geteuid()`
/ ambient root / `SUDO_*` (`euid == 0` mints nothing); closed request / response
schemas with self-excluding digests, unknown-field fail-closed, no
trust-asserting fields; freshness / replay with fresh / consumed / duplicate /
expired / unknown / conflicting-replay all distinct and a lost response never
freeing a spent one-shot; the seven-state transition model with the no-auto-retry
boundary at `MUTATION_ATTEMPT_STARTED`; the explicit **INDETERMINATE /
RECONCILIATION-REQUIRED** state; evidence durably staged before the mutation,
finalized after commit (a staged-write failure aborts before any mutation).

## Certification closure · typed reads · ceremony entry · failure codes — VERIFIED

Exact five-role certification closure (`hpac_lifecycle_terminator` excluded; the
per-role authority table byte-unchanged in substance; the generic outer
`certification_write` operation does not erase internal role restrictions);
§42D typed reads that **cannot** be iterated into a generic read broker or
reconstruct unrestricted store authority (contents returned, not a handle; every
read session/subject-scoped; no secret / keychain / FIDO2 PIN / private key; no
write reachable); `ceremony_entry` as a bounded non-authoritative hand-off
(returns an acknowledgement, never the outcome; every wall verbatim); every v2.0
rejection mapping deterministically and unambiguously onto the existing 21
`pawa_failure_code` (no new code; no overloaded code hiding a security-critical
distinction) and the existing 41 RHAMP `terminal_reason_code` (RHAMP-001 v1.0
byte-unchanged; no helper operation bypasses the RHAMP verifier; a caller cannot
self-assert counter ACCEPT).

## Walls · deterministic-vs-real · mechanism neutrality · runtime posture — VERIFIED

§68C `HPAC-PAWA-REQ-338` preserves every §5 / §68 / §68A / §68B human-authentication
/ approval / PB / POL / Runtime-Enforcement / runtime-capability / dispatch /
external-effect wall verbatim — the certification-authority path terminates no
later than the bounded Gate-5 assurance result; nothing enables
`adapter.dispatch()`. The deterministic-vs-real wall is permanent (a fixture
helper / launcher / peer / authenticator remains permanently unable to produce
`PRODUCTION` authority; `require_real_assurance` unchanged). Mechanism neutrality
and the mobile-only / passkey future are preserved (no YubiKey / FIDO2 / USB /
AAGUID / TTY hardcoded). Bounded security claims — no overclaiming (does NOT
claim protection against a hostile root, a compromised kernel, a compromised
registered helper binary, a whole-machine snapshot restore, or a single-account
host). Runtime `not_implemented` / Observed / observe / unavailable; 0 plugins /
0 capabilities; first governed runtime external effect **ABSENT / UNREACHABLE**;
N-16-6 / N-16-7 untouched.

## HPAC-PPA-001 evidence-writer adjudication — B (the blocker)

See **Verdict** above and the canonical Phase Report §21 / §45. The
determination is **B — HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED**, on
HPAC-PPA-REQ-041 (*"never sent to the helper"*), HPAC-PPA-REQ-054 (*"evidence
producer is only the launcher mediator"*), HPAC-PPA-REQ-052 (a distinct issuer
module), PPA-INV-2 (helper response ≠ evidence writer), and HPAC-PPA-REQ-069 /
HPAC-PPA-REQ-070 (moving the writer-holder is MAJOR-class, not a within-properties
adapter). The v2.0 `presentation_evidence_write` design is the correct security
direction but is not authorized by HPAC-PPA-001 v1.0 as frozen; it is **not
silently reinterpreted** and **not edited** in this IV.

## Verification

- `pcae check` passed; `pcae health` healthy; `pcae status coherence` passed; `pcae doctor task-memory` warning-only pre-existing DONE.md omissions (unrelated completed F-5 / F-5-B2 tasks), no errors, no "2 active task files".
- New independent contract-IV suite `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_1_n16_5_f_5_tb_contract_iv.py` — **62 tests, 62 passed, 0 failed** (static / read-only; independently encodes the IV criteria and the BLOCKED verdict).
- Predecessor N16-5-F-5-TB-CONTRACT contract-verification suite re-run at this HEAD — **45 passed, 0 failed** (regression lock).
- `git diff --name-only 3cdc3c08 HEAD -- src/pcae scripts pyproject.toml schemas docs/contracts` — EMPTY.
- No protected-root or helper-installation artifact; no ceremony; no protected-host write.

## Recommended next (derived, NOT begun)

A **fresh governed HPAC-PPA-001 contract-evolution phase** is required first
(own explicit human authorization; id NOT reserved): move HPAC-PPA-001's
presentation-evidence-writer authority **out of process** — into the verified
presentation helper — explicitly re-meaning HPAC-PPA-REQ-041 / HPAC-PPA-REQ-054 /
HPAC-PPA-REQ-052 / PPA-INV-2, aligned with HPAC-PAWA-001 v2.0 §42F /
HPAC-PAWA-HELPER-001 §17 (likely MAJOR for HPAC-PPA-001 under HPAC-PPA-REQ-069;
the evolution phase decides and carries its own IV). THEN a fresh or scoped
contract-IV of the resolved point. THEN, each subject to its own fresh human
authorization: the `HPAC-PAWA-REQ-340` implementation sequence — a privileged
helper + `HPAC-PAWA-HELPER/1.0` protocol implementation; caller integration;
in-process authority-path removal (no compatibility shim may preserve the
insecure in-process path); packaging / clean-install; a dedicated independent
security IV; production deployment; and only then a fresh **N16-5-FINAL-CERT**
on a fresh CPIPC-valid successor id (never reuse a completed or blocked
certification identity). **Do NOT begin the HPAC-PPA-001 evolution phase, any
implementation slice, N-16-6, or N-16-7.**

## Historical governance integrity

Preserved exactly: N16-5-F-5-B2 NOT VERIFIED / BLOCKED; N16-5-F-5-B2R-IV NOT
VERIFIED / BLOCKED; N16-5-F-5-B2R2-IMPL COMPLETE — BLOCKED; N16-5-F-5-TB-ARCH
COMPLETE; N16-5-F-5-TB-CONTRACT COMPLETE / CONTRACT FROZEN; DELEGATED .3
FINALIZATION / COMMIT / PUSH: UNAUTHORIZED. Historical HPAC-PAWA-001 v1.0 / v1.1
/ v1.2 / v1.3 / v1.4 freeze records and their independent verifications remain
immutable; v2.0 is append-only. No retroactive authorization or reinterpretation.
