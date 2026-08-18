# Phase 149O.20L.7O.2A.4 Complete — RepositoryIdentity Write-Path Remediation Execution

**Phase ID:** 149O.20L.7O.2A.4
**Mode:** governed real-host execution (exactly one authorized Dell mutation)
**Predecessor:** 149O.20L.7O.2A.3 (RepositoryIdentity Write-Path Remediation Authority Independent Verification — completed; AUTHORIZED AND INDEPENDENTLY VERIFIED — READY FOR CHMOD EXECUTION)
**Date:** 2026-08-18
**Status:** completed
**Verdict:** `PERMISSION REMEDIATION EXECUTED SUCCESSFULLY — INDEPENDENT VERIFICATION PENDING. Executed exactly chmod 1770 /opt/pcae/runtime/src/.pcae on hac-dell under chgr-86aeb5cfa7c44020ad002bc9f80c5856, exit status 0. RepositoryIdentity/DeploymentBinding remain absent (not created, as required). Not claimed as independently verified — that determination is reserved for 149O.20L.7O.2A.5.`
**No-Go Confirmations (this phase):** `Exactly one host state change (mode 0750 -> 1770 on /opt/pcae/runtime/src/.pcae). No RepositoryIdentity/DeploymentBinding/certification created. No Boundary C/A or HATP activation. No source/venv/wrapper/Permission Broker mutation. No new CHGR published; no election re-run. No recursive/chown/setfacl. No synthetic sticky-bit test file created.`
**True phase-entry commit:** `8fbdf18e (Phase 149O.20L.7O.2A.3: repair pushed_status/pcae_push_check trust fields post-push). git status clean, pcae check passed at entry.`
**Governing CHGR:** `chgr-86aeb5cfa7c44020ad002bc9f80c5856`
**Human-confirmed preview digest:** `616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd`
**Decision session:** `CDS-bc9a70fc-3913-4c8b-b95e-50ca0c26091c`
**CHGR immediate pre-mutation verification:** `pcae governance-record verify` with all three related artifacts supplied (confirmation, provenance, integrity) → `outcome: verified`; every applicable check passed (`schema_shape`, `digest_self_consistency`, `lifecycle_structural_legality`, `confirmation_binding`, `assurance_truthfulness`, `provenance_consistency`, `integrity_consistency`); `template_resolution` skipped, same disclosed legitimate skip as 7O.2A.3. Uniqueness re-confirmed: sole record (of six published, none revoked) naming `/opt/pcae/runtime/src/.pcae`.
**Fresh Dell preflight (live, this phase, before mutation):** `hostname atila-Latitude-E5470; machine-id 54ff22ce400b475aa0d55cb68f4a3334; source SHA b0840e96a7ffb12308e95828aa5927c3e7c770c0 (detached, clean); .pcae root:pcae 0750, no extended ACL; RepositoryIdentity/DeploymentBinding absent; Protected Root empty; no certification artifact; HMIC digest 65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8 exact match; canonical HBDC NON_COMPLIANT, sole residual HBDC-REQ-042, HBDC-REQ-036 True — exact match. Zero drift.`
**Exact target path:** `/opt/pcae/runtime/src/.pcae` (absolute, no glob, directory, not a symlink)
**Exact pre-state:** `owner root, group pcae, mode 0750, no extended ACL`
**Executing principal:** `codex (SSH session user) via sudo -n as root`
**Independent command safety review (pre-mutation):** `Absolute path exact; target confirmed a directory, not a symlink; no -R; no chown; no setfacl; 1770 = sticky(1) + owner-rwx(7) + group-rwx(7) + other-none(0), matching the CHGR exactly; single target, cannot affect Protected Root or any unrelated path. No technical objection found.`
**Exact mutation command:** `sudo -n chmod 1770 /opt/pcae/runtime/src/.pcae`
**Exit status:** `0`
**Timestamps:** `pre-mutation 2026-08-18T11:27:28.649460109Z; post-mutation 2026-08-18T11:27:28.661248436Z`
**Immediate stat read-back:** `owner=root group=pcae mode=1770 type=directory` — exact match to authorized post-state.
**getfacl read-back:** `# owner: root / # group: pcae / # flags: --t / user::rwx / group::rwx / other::---` — no unintended extended ACL entries.
**Existing-entry preservation:** `All 17 pre-existing root-owned .pcae entries (.gitignore, architecture-history.json, audit/, authority-evaluation/, decision-sessions/, exports/, fleet-exports/, fleet.json, phase-completion-metadata.json, phase-completion-report.md, phase-metadata-repairs.log, policy.toml, publication-execution/, repository-intelligence/, skills/, strategic-lineage.json, strategic_reviews.json) retained their own owner/group/mode exactly. Only the parent directory's own mode changed.`
**RepositoryIdentity absence:** `Confirmed absent from the post-mutation .pcae inventory. Not created this phase, as required.`
**DeploymentBinding absence:** `/etc/pcae/hatp/trust-store confirmed still empty (only ./..), live, post-mutation. Not created this phase.`
**Protected Root state:** `Unchanged — empty before and after.`
**Source SHA/cleanliness (post-mutation):** `b0840e96a7ffb12308e95828aa5927c3e7c770c0, unchanged; git status --porcelain empty (clean).`
**HMIC digest (post-mutation):** `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` — unchanged, recomputed live via the deployed package's own `derive_implementation_scope_digest`.
**Venv/wrapper state:** `Launch wrapper /opt/pcae/runtime/bin/pcae-launch sha256 b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32 (unchanged, fixed constant across every 149O.20L.7* Dell phase); owner/group/mode root:pcae 750 unchanged. venv/bin/python3 unchanged symlink to /usr/bin/python3.`
**Canonical HBDC post-state:** `NON_COMPLIANT, sole residual HBDC-REQ-042 (no_repository_identity_present); HBDC-REQ-036 confirmed True; 34 total checks evaluated — identical to the pre-mutation baseline. The chmod did not itself satisfy HBDC-REQ-042 and introduced no new failing requirement.`
**Rollback:** `Not triggered. Every postcondition matched its expected value exactly; rollback was not performed.`
**Mutation inventory:** `Exactly one host state change: /opt/pcae/runtime/src/.pcae mode 0750 -> 1770 (owner root, group pcae, extended ACL — all unchanged). Nothing else.`
**architecture-history.json correction carried forward:** `P-A' fixes 38 of the 39 declared write-required .pcae artifacts. Does NOT fix architecture-history.json (deferred, separate producer/write-pattern issue). This execution does not solve the complete .pcae write architecture.`
**Sticky-bit evidence qualification:** `Linux sticky-bit semantics (S_ISVTX / check_sticky() / fs/namei.c) are REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCES. Not empirically tested using synthetic root-owned files on hac-dell this phase. No empirical-host-verification claim is made.`

## Governance Results

- **pcae_check:** passed
- **pcae_doctor_task_memory:** warnings (pre-existing, unrelated -- historical tasks/done/ entries predating this phase, not remediated here -- outside this phase's allowed-file scope)
- **pcae_health:** healthy
- **pcae_notify_status:** telegram configured/enabled
- **pcae_permission_broker_status:** execution_unavailable, no enforcement
- **pcae_push_check:** clean
- **pcae_runtime_inspect:** Observed / observe / unavailable
- **pcae_status_coherence:** coherent
- **telegram_runtime:** loaded

## Test Results

- **fast_green:** Deselected confirmation run (270 deselects: the full HEAD failing/erroring node-id set at true phase-entry commit `8fbdf18e`, plus one test independently confirmed flaky under `-n auto` parallel load) → **7894 passed, 5 skipped, 0 failed, 1 error** (pre-existing fido2-import collection failure, present identically at phase-entry baseline, not deselectable via node id). Phase-entry worktree baseline (`8fbdf18e`, live `git worktree` A/B): 259 failed, 10 errors, 7869 passed. This phase's HEAD: 260 failed, 10 errors, 7895 passed — exactly **1 new failure**, individually diffed and attributed (`149O.20L.7N.1::TestCandidateCurrentness::test_head_equals_origin_main`, a pre-existing `HEAD == origin/main` assertion, expected to resolve at push time — same disclosed category as every prior `149O.20L.7*` phase). Zero baseline failures flipped. One additional test (`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`) flaked to failing only during the deselected-confirmation run itself (absent from both the HEAD and baseline capture runs), independently reconfirmed passing in isolated rerun (8.74s). None of the delta touches any `src/pcae/**`, `scripts/**`, `docs/contracts/**`, or `schemas/**`/`pyproject.toml` file.
- **report_notification_tests:** not_applicable_this_phase
- **bootstrap_session_reporting_tests:** not_applicable_this_phase
- **new_phase_test_suite:** `tests/test_phase_149o_20l_7o_2a_4_repositoryidentity_write_path_remediation_execution.py` — 27 tests, all passing.

## Recommended Next Phase

**149O.20L.7O.2A.5 — RepositoryIdentity Write-Path Remediation Independent Real-Host Verification.** From a fresh session, must independently verify exact `1770` mode, owner/group, ACL, preserved root-owned `.pcae` entries, source/HMIC, HBDC baseline, `RepositoryIdentity` absence, `DeploymentBinding` absence, Protected Root, CHGR integrity, and this phase's mutation inventory. Only after a clean `7O.2A.5` may a `RepositoryIdentity` creation retry begin under a new phase. The strategic breakpoint before Boundary C (DeepSeek Harness comparative study, PCAE Runtime Adapter/Plugin architecture) remains preserved and is not begun this phase.
