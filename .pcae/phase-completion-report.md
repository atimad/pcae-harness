# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 — Protected Helper Admission Provenance and Configured-Agent Exclusion Production Repair

Alias: **N16-5-F-5-TB-HELPER-ADMISSION-PROVENANCE-REPAIR**. Terminal technical verdict: **COMPLETE — BLOCKED / ADMISSION NOT REPAIRED**. Governed lifecycle status: completed only upon successful `pcae phase complete`; this document supplies the truthful blocked technical disposition for that lifecycle.

## Identity and preflight

Actual latest completed predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1` (HELPER-WRITER-AUTHORITY-IMPL), COMPLETE — BLOCKED / IMPLEMENTATION NOT VERIFIED. Predecessor final commit and source baseline: `fabbfac07276b7e9b44b25295943d24e77a27229`. Entry branch main, HEAD == origin/main, origin/main..HEAD = 0, clean worktree. PROJECT_STATUS, completed metadata, latest report, done task and git history independently agree. No implementation-IV successor began.

FOUNDATION-REPAIR was **PRE-ACTIVATION PREFLIGHT STOP / NOT A GOVERNED PHASE COMPLETION**. No non-idle task/report, completion metadata, commit, push or notification for it exists; last-notified still named the implementation predecessor at entry. Recommendation strings in old idle tasks are not phase activation. Its former candidate ID was never reserved.

CPIPC independently derived through `pcae.core.phase_id`: predecessor + one numeric child segment, valid parse, normalized equality, child's subphase[:-1] == predecessor subphase, same series/branch, comparison less, unequal identities, zero exact token collisions in git log --all. This phase activated only after sections 0–6 preflight succeeded, via governed task lifecycle. Long canonical title exceeded filename limit in task transition after idle closure; recovered using a short filename and full canonical title, matching existing repository practice. Phase start reported already-held codex-local lock; bootstrap preserved the lock; `pcae session write` refreshed task continuity after the canonical title was set. The first commit was correctly rejected for stale session-task binding, then succeeded after that governed refresh. No bypass flag was used.

## Findings and blocking adjudication

**B1 — admission omitted (reproduced, unrepaired).** `main → build_helper_context → run_one_shot → handle_one_request → dispatch → validate_and_admit → handler`. The helper never obtains its channel peer or resolves the configured agent. `HelperContext` has only replay_ledger, evidence_stager, supported_operations, store. `validate_and_admit` advances REQUEST_AUTHENTICATED based on a comment that the caller already authenticated. All five operations inherit this missing prerequisite, including both reads.

Launcher graph: `launch_and_exchange → verify_helper_executable → execute_verified → channel.accept_one → authenticate_peer → send request`. `authenticate_peer(configured_agent=None)` does not resolve any identity and skips exclusion. The launcher supplies no configured_agent. Real Linux SO_PEERCRED returned uid/gid/pid from a socketpair; None accepted; explicit same uid rejected; explicit distinct identity accepted. Explicit identity objects in this probe are descriptive fixture inputs, NOT trusted canonical admission evidence. No repaired admission is claimed.

**B2 — frozen installation identity contradiction, requiring contract reconciliation before source repair.** HELPER REQ-021 prescribes `^hpahi-[0-9a-f]{32}$` and simultaneously requires equality to PAWA's root installation ID. PAWA §14 and its validator instead prescribe `hpawi-<hex32>`. These disjoint grammars cannot be equal. HELPER REQ-021/022 also require dedicated `pawa-helper` registration/current-generation records and schemas; the source baseline contains no `HPAC-PAWA-HELPER-INSTALLATION/1.0` implementation. The current launcher, read adapter, Model E authority currentness and all three store-side families use `ProtectedPresentationInstallationStore`, whose ID grammar is `hppi-*` and whose generation is the PPA presentation lineage. A fixture-backed real store predicate rejects an hpahi helper ID with descriptor_installation_mismatch. Equating any of these lineages would silently change normative and Model E semantics.

**B3 — predecessor read-path separation claim is too broad.** `resolve_launcher_deployment_metadata → ProtectedPresentationInstallationStore.resolve_current_generation → HPACStoreAuthority.verify_record → _ensure_root → _validate_production_boundary`. Genuine Linux canonical-root validation reproduces the owner/configured-agent fallback failure during metadata READ, before any final store mutation. Both hpahi and current hppi Model E attempts fail at that earlier provenance-read boundary. The same failure is reproduced by direct `_ensure_root(create=True)` on a 0700 deployment-owner-owned root. Do not claim all reads avoid this boundary. Not every read has been exhaustively traced.

The initial narrow draft used the existing PPA resolver for request currentness. Independent review exposed B2; primary re-read all contracts and validators and corrected an initial hpahi/hpawi conflation. The draft was removed in full. **No production or contract changes remain.** No permissive fallback was landed. Per authorization §4(C), §7, §18/19 and §74, the admissible result is BLOCKED: contract/installation binding reconciliation is needed, while changing Model E or foundation here is prohibited. This is an activated phase with a blocked outcome, distinct from the previous unactivated foundation attempt.

## Normative requirements and trust reconstruction

Exact unchanged requirement text:

- **HPAC-PAWA-HELPER-REQ-031.** After it is `exec`'d and before it admits any
  operation, the helper SHALL run, **in its own interpreter**, HPAC-PAWA-001
  §33 **steps 1–8** verbatim as required conjuncts: canonical
  `<HPAC_PROTECTED_ROOT>` resolution and symlink rejection (§25);
  `HPAC-PAWA-AGENT-EXCLUSION/1.0` load + live account resolution +
  `live uid == provisioned_uid` + live group enumeration (§32A) yielding
  `ConfiguredAgentAuthorityIdentity`; the configured-agent exclusion negative
  boundary (`_effective_write_access` / `_ancestor_chain_safe` **against the
  configured-agent identity**, not `os.geteuid()` — finding F-1); `{device,
  inode}` root-identity binding; descriptor trust (closed schema / digest /
  `protected_root_identity` / ownership / mode / `provenance_ref` /
  `state == ACTIVE`); `current-generation.json` incl. `agent_exclusion_digest`
  with `descriptor.generation == current_generation`; the not-configured-agent
  current-context check (§31); the `O_EXCL | O_NOFOLLOW` positive write probe
  under `.authority/` (§28). Removing any one re-opens a named §20 threat; no
  single conjunct is sufficient (HPAC-PAWA-001 PAWA-INV-3).
- **HPAC-PAWA-HELPER-REQ-032.** **Configured-agent identity vs ambient root
  (finding F-1 / F-5-B1, preserved and executed inside the helper).** The
  helper process principal is the deployment owner and MAY run with elevated
  (`sudo` / root EUID) privilege. The **negative boundary** in step 3 / step 7
  SHALL still be evaluated against the **configured PCAE agent principal**
  resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0` — **never** against
  `os.geteuid()`, an ambient root EUID, a `SUDO_*` variable, or a caller
  parameter. `euid == 0` inside the helper mints **nothing** (HPAC-PAWA-001 §34,
  PAWA-INV-1). The helper SHALL distinguish `helper process principal` from
  `configured PCAE agent principal` and SHALL NOT treat ambient EUID root as
  proof that the configured agent cannot write protected state — that fact comes
  only from the live `_effective_write_access` / `_ancestor_chain_safe`
  evaluation against the resolved agent identity.


REQ-042 requires actual channel peer UID == filesystem deployment-owner UID and != canonical configured-agent UID; REQ-043 makes this mandatory before any request-driven protected read. PAWAH-INV-3 preserves conjunctive integrity; PAWAH-INV-8 separates OS peer identity from human approval. PAWA-INV-3 forbids dropping recognition conjuncts; PAWA-INV-7 rejects absent two-account topology; PAWA-INV-12 requires live groups and binding integrity.

Canonical configured-agent source is `hpac_pawa_agent_exclusion.resolve_configured_agent_identity`: canonical protected `.authority/agent-exclusion.json`, closed schema, digest, PAWA installation and root binding, anchor agent_exclusion_digest, symbolic account live lookup, provisioned_uid equality and live group enumeration. It needs no legacy writer factory. Agent lock, request strings, argv and environment are not substitutes. Unknown identity must deny; same-identity topology must deny. Current source does not consume this chain in the helper.

Proposed, **not frozen/implemented**: sealed process-local VerifiedHelperAdmission with actual socket identity, kernel peer, resolved agent, PID, exact request digest, installation/generation and currentness. Construction follows helper-local steps 1–8 and peer checks; dispatch revalidates OS/root facts, not merely a Python seal. Context is non-bearer and grants no writer authority, PB, runtime or external effect. Copy/pickle/JSON/restart would not carry active admission. Admission would gate all five operations before any applicable replay reservation, preserving durable replay and certification_read's existing reservation exemption. Structural request parsing may precede peer authentication; no request-driven store read or operation may do so. Channel A must not authorize B. The lineage contradiction prevents finalizing binding semantics, so this design is NOT production authority.

Contract home: HELPER owns helper registration/request/admission; PAWA owns configured-agent resolution and PAWA root lineage; PPA owns presentation lineage. REQ-031/032/042/043 themselves are sufficient; REQ-021's cross-contract identity equality is contradictory. No contract version changed: HELPER v3.0, PAWA v2.0, PPA v2.0 retained byte-identical. PAWA trusted-consumer semantics and PPA ownership/election semantics are unchanged. REQ-033's legacy-factory prohibition remains load-bearing; no new identity vocabulary, generic context or trust root was introduced.

## Baselines and preservation

| File | SHA-256 (entry = final) |
|---|---|
| `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `21e18a872d90cf89892e44b6ee612ba1359e828d46aa13aecb8c6b5dc0561a55` |
| `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |
| `src/pcae/core/hpac_foundation.py` | `2a33d7e9238f135ae3a034372b88b0b47e96545d88d1229dbf3518a73b5442f9` |
| `src/pcae/core/hpac_protected_admin_writer.py` | `28c02d5a7525e466933fb2c2403ea6188e66d981bd2642d14bb20c6d767721ef` |
| `src/pcae/core/hpac_pawa_helper_writer_authority.py` | `4a81aecfced8fb22367a72eaf7fec59e102632ed4cb76c31c112f6dcfb9a401c` |

Every production `src/` file is byte-identical to baseline (git diff empty). No symbols changed. Model E authority families, facades, exact-family sink recognition, presentation operation_scope_invalid mapping, same-file-object execution, and durable replay remain unchanged. Legacy factory imported only by a separate disposable provisioning subprocess in the Linux experiment, never the helper/probe process. No active admission exported to IPC/disk/logs because none was implemented.

Source delta inventory: **NONE**. Added evidence suite and documentation only. Traceability: REQ-031/032 → entrypoint/context omission tests + canonical resolver reconstruction; REQ-042/043 → None/exclusion source evidence and genuine kernel peer probe; REQ-021/022 → disjoint grammar/schema/currentness tests; no-authority-export → no production or protocol changes.

## Validation and genuine Linux evidence

Fresh evidence suite: 13 passed. Model E: 44 passed unchanged. Contract repair IV: 40 passed unchanged. Contract repair: 48 passed unchanged. Historical failed-IV: 24 passed unchanged. Combined focused run: 169 passed. Governance/report/notification/transition tests: 162 passed. Bootstrap reporting: 43 passed. Helper boundary: 97 passed / 1 skipped (Linux-specific fexecve-equivalent path on macOS), 0 failed. Exact results are persisted under `docs/evidence/helper-admission-provenance/`. An intermediate unlanded draft broke two legacy None-peer fixtures; after full draft removal the final helper suite passed. Those failures are not exclusions or evidence of a landed repair.

Linux host hac-dell, genuine Linux kernel. Private mount namespace with private propagation; `/etc` bound to a disposable directory containing copies of passwd/group/nsswitch only. Canonical root `/etc/pcae/hpac/protected-root` exists only in that namespace, mode 0700, owner/helper uid 0, configured-agent nobody uid 65534. No accounts created or modified. Provisioning runs separately, then a fresh interpreter verifies legacy factory absent. PPA test records were seeded with the existing disclosed fixture topology seam; **seed setup is NON_REAL test provisioning, not genuine certified installation**. Subsequent kernel and production root-boundary probes use actual OS facts without topology mocks.

`linux-probe.json` contains actual peer credentials, PAWA/PPA IDs plus two attempted Model E admin ID cases (hpahi and hppi), the metadata-read exception and the direct foundation exception. `linux_probe.py` is the exact probe. Same-account explicit identity: DENY. None: incorrectly ACCEPT (baseline defect remains). Distinct explicit identity: peer primitive PASS only, **not verified end-to-end admission**. Forged-context/direct-entrypoint/wrong-agent/copy/restart/all-five repaired-denial and valid read/write dispatch criteria: **NOT IMPLEMENTED / NOT VERIFIED**, blocked by B2/B3; never reported as passing. Neither attempted Model E admin write succeeded; certification and presentation write paths were not exercised in this probe. Disposable setup removed; host canonical root remains absent; cleanup recorded in linux-cleanup.txt. Live protected-host writes = 0.

Fast Green pre-push checkpoint: governed baseline-versus-candidate comparison PASS, **0 attributable regressions**, baseline `fabbfac07276b7e9b44b25295943d24e77a27229`, candidate `96b561b1fc5fd65de316a6873ecf9dbad96508b7`. Baseline method: parent of oldest phase-attributed commit. Raw candidate failures 352, errors 9; pre-existing exclusions 360, environment exclusions 0, expected pre-push artifacts 1. Exact machine evidence is linked by digest in completion metadata. Final pushed-HEAD attribution and post-push checks belong to the generated final lifecycle supplement. An earlier run correctly refused evidence when HEAD moved; only the completed fixed-HEAD run is used. No unit-only success claim.

## Scope walls and outcome

Caller migration = NOT BEGUN. Legacy retirement = NOT BEGUN. Foundation repair = NOT BEGUN. Admission repair = NOT LANDED. Live deployment/packaging unchanged. Real FIDO2, real protected presentation, real certification = NOT PERFORMED. macOS real helper execution remains FAIL-CLOSED / NOT IMPLEMENTED. Runtime inspection: Observed / observe / unavailable; plugins/capabilities 0/0; first governed runtime external effect ABSENT / UNREACHABLE. F-5-B2 remains blocked pending prerequisite repairs and fresh IV; F-5 CERTIFICATION BLOCKED; N-16-5 NOT CLOSED; N-16-6 OPEN/UNTOUCHED; N-16-7 OPEN/UNTOUCHED, STRICTLY LAST.

Recommended exactly one successor (NOT begun): `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1` — **N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR**, a bounded contract reconciliation of helper/PAWA/PPA lineage and admission bootstrap dependencies before another production admission repair. Derived as one CPIPC child, normalized and collision-free. No admission-repair IV is proposed as though a repair succeeded. Foundation repair and all IV/implementation successors remain unstarted.

## Governance evidence

Entry check passed, health healthy, status coherent, push clean/0. Doctor reports pre-existing task-memory warnings; no historical memory cleanup folded in. Repository transition validator is exercised by governance tests and governed phase completion; its known lack of complete ancestry verification remains unchanged, with CPIPC independently checked. Final post-push check/health/coherence/push count, final Fast Green candidate, canonical completed state and completion notification receipt are finalized by governed lifecycle and reported with the final delivery; pending states must not be interpreted as results.

Historical states preserved: CONTRACT-IV COMPLETE — NOT VERIFIED / BLOCKED; CONTRACT-REPAIR COMPLETE / CONTRACT REPAIRED — PENDING INDEPENDENT RE-VERIFICATION; CONTRACT-REPAIR-IV COMPLETE / INDEPENDENTLY VERIFIED; WRITER-AUTHORITY-IMPL COMPLETE — BLOCKED / IMPLEMENTATION NOT VERIFIED.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED

One bounded worker assisted read-only reconstruction and baseline evidence tests only. Primary independently reviewed source and every retained test, discovered/corrected the PAWA hpawi grammar detail, added dynamic currentness/read-boundary tests, performed Linux validation, removed the draft, and alone handles lifecycle/commit/push/notification.


Finalization tooling observation: the initial attribution CLI defaulted to `local_only`, but completion's live push reconciliation uses `not_pushed`. The pending-report attempt correctly quarantined the mismatched evidence; no canonical report promotion or notification occurred. Its command nevertheless printed `Phase complete` and released the lock because `stage_pending_report` contributes to the command's logical return path even when staging fails. The primary reacquired the lock through governed bootstrap, refreshed the session, and regenerated attribution with explicit `--pushed-status not_pushed`. This is recorded as existing tooling behavior, not repaired or bypassed in this phase.

## Final lifecycle validation supplement

The exact final pushed HEAD, full phase commit list, final-HEAD governed Fast Green result and byte-identical machine evidence archive, final post-push checks, canonical completion state, and notification receipt are recorded after push in `.pcae/phase-reports/helper-admission-final-validation.json`. This generated report-output supplement is part of the final report; keeping final-HEAD evidence in the generated report namespace avoids embedding a Git commit's own hash in that commit. The committed metadata contains the earlier technical evidence snapshot, explicitly superseded only for final lifecycle observations by the supplement. No source/test result is altered by that archival step.

Governed attribution checkpoint `bec131195caaaa6607653a256c12c880ec70dde4`: PASS, 0 attributable regressions, 353 raw failures / 9 raw errors, 361 baseline-proven exclusions, 0 environment exclusions, 1 expected pre-push artifacts. Artifact `.pcae/fast-green-attribution/b04f99d3a7f2098c7191b0bbde9287d3c416652073b5f548aecc683c62d98226.json`. The original technical report's earlier checkpoint remains historical evidence; this entry is the newer lifecycle checkpoint.
