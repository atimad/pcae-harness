# Phase 149O.20L.7O.2K.3 — HATP HMIC CertificationRecord Real-Host Creation — Source-Parity Revalidated

## 1. Result

**SUCCESS — exactly one HMIC `CertificationRecord` created on hac-dell. No activation, no binding, no other protected-state mutation.**

- **Phase-entry commit (Mac):** `03b51f12c8a94f14ad62a183b46474408b17c013`
- **Dell deployed revision (unchanged by this phase):** `305f8e7913bac76941dade6ff4e018c74533f062`
- **certification_id:** `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`

## 2. Source-freshness classification (spec §2-4)

`git diff --name-status 305f8e79..origin/main` (7 commits, all from
149O.20L.7O.2K.2's own finalization) touched only: `.pcae/authority-evaluation/**`,
`.pcae/decision-sessions/**`, `.pcae/publication-execution/**`,
`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`,
`CHANGELOG.md`, `PROJECT_STATUS.md`, `tasks/DONE.md`, `tasks/active/**`,
`tasks/done/**`, one new `docs/` phase report, one new `tests/` file.

None of these paths intersect the 36 HMIC frozen files, the 7 bound
contract files, `src/pcae/core/hatp_mandatory_certification.py`,
`scripts/hatp_certification_admin.py`, or any deployment/root/repository-
identity behavior. Classification: **Category B only (non-authority-
bearing documentation/governance artifacts). No redeployment required.**

Independently confirmed by re-deriving `implementation_scope_digest` and
`contract_versions` on the Mac working tree at current HEAD
(`03b51f12`): both values are byte-identical to the same derivation run
live on Dell against `305f8e79` (§6). Authority-bearing bytes are
unchanged across the newer Mac HEAD.

## 3. Fresh host identity (spec §8)

- `machine-id`: `54ff22ce400b475aa0d55cb68f4a3334` — matches.
- `hostname`: `atila-Latitude-E5470` — matches.
- `uname`: `Linux ... 7.0.0-28-generic ... x86_64` — matches expected.
- SSH login identity: `codex` (uid 1003, groups codex/sudo/users).
- `RepositoryIdentity`: `repository_instance_id = 0107866f-af7c-40b4-8317-74e71acb05ca` — matches.

## 4. Fresh deployment source check (spec §9)

- Deployed `git rev-parse HEAD` (via `sudo -n git -C /opt/pcae/runtime/src`): `305f8e7913bac76941dade6ff4e018c74533f062` — exact match.
- `git status --short`: clean.
- `git diff --stat HEAD`: no drift.
- Tracked file count: `4402` (matches 2K.2's established parity count).
- No untracked files under the tree.

## 5. Live HMIC re-derivation on Dell (spec §10)

Executed under the deployed venv (`/opt/pcae/runtime/venv/bin/python3`), against `/opt/pcae/runtime/src`:

| Field | Value |
|---|---|
| `repository_instance_id` | `0107866f-af7c-40b4-8317-74e71acb05ca` |
| `canonical_deployment_root` | `/opt/pcae/runtime/src` |
| `implementation_commit` | `305f8e7913bac76941dade6ff4e018c74533f062` |
| `implementation_scope_digest` | `cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f` |
| frozen member count | `36` |
| `contract_versions` | HMRC-001 1.1, HATP-001 1.0, HSCE-001 1.3, RAE-001 1.0, HBDC-001 1.2, HPSE-001 1.1, HHCE-001 1.1 (7 identities) |

## 6. Mac ↔ Dell identity comparison (spec §11)

Same derivation run locally on the Mac repository at HEAD `03b51f12`
(no `RepositoryIdentity` needed for this comparison — only the digest
and contract-version derivations, which do not depend on it):

- `implementation_scope_digest` (Mac): `cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f` — **exact match** to Dell.
- `contract_versions` (Mac): identical 7-entry mapping — **exact match** to Dell.

## 7. Protected Root check (spec §12)

- `/etc/pcae/hatp/trust-store`: exists, real directory, not a symlink, `root:pcae 0750`, no ACL entries.
- Ancestor chain: `/etc/pcae/hatp` and `/etc/pcae` both `root:root 0755`.
- **Compliant, unchanged from 2K/2K.1/2K.2's frozen envelope.**

## 8. Pre-mutation protected state (spec §13-14)

- `certifications.json`, `certification-bindings.json`: both **absent** (trust-store directory empty except for `.`/`..`).
- Production validator (`validate_active_hatp_mandatory_independent_verification_certification`) pre-run status: **`MISSING`**.
- HardwareCredentialRecord, Principal, Signer, DeploymentBinding: all absent (wider `/etc/pcae` search, zero matches).

## 9. Verification-record resolution (spec §15)

Per HMIC-REQ-071, `verification_record_digest` must reference "the
canonical phase-report artifact (e.g. the 149O.19-class independent-
verification phase report) this certification attests to." The current
HMIC-001 v1.6 implementation's own independent-verification report is
`docs/PHASE_149O_20L_7O_2H_3_HMIC_PATHS_SOURCE_SCOPE_AND_SEVEN_CONTRACT_CONSISTENCY_INDEPENDENT_VERIFICATION.md`
("VERIFIED WITH NON-BLOCKING FINDINGS — HMIC-001 v1.6 REPAIR COMPLETE"),
the exact independent-verification phase for the current bound contract
version set. Its digest is identical on Mac and Dell (byte-for-byte,
confirmed by `sha256sum`):
`b49cabe2717529273c3c463e752bfa8b423350b47e0fa77ffcfba605e0b7b0e9`.
This is the value the ceremony itself computed and stored (§13).

## 10. Implementation commit / certification identity (spec §16-17)

`implementation_commit` is tool-derived from the deployment root's own
git HEAD (`305f8e7913bac76941dade6ff4e018c74533f062`), never from the
newer Mac HEAD — consistent with the frozen 2K/2K.1/2K.2 architecture.
`certification_id` was tool-derived (never human-supplied) from the
full field tuple at invocation time.

## 11. Protected Admin Authority election / human confirmation (spec §18-19)

A fresh election was obtained for this exact operation (create-only,
not activate/revoke/generic-admin). The precomputed target tuple (§5,
§9-10) was presented to the human in-chat immediately before invocation;
the human (Atila Madai) genuinely reviewed and confirmed it and supplied
`certified_by="Atila Madai"` themselves — not inferred from any prior
chat approval, not fabricated. `--assume-yes` was used for the
non-interactive SSH invocation only after this real confirmation was
already obtained at the ceremony boundary, per HMIC-REQ-076 step 5's
substance (the script's own module docstring names `--assume-yes`
"for non-interactive/scripted admin invocation only").

## 12. Final pre-write revalidation (spec §20)

Immediately before invoking `create`, host identity, deployed source
revision/cleanliness, and Protected Root state (§3-4, §7) were rechecked
fresh and found unchanged.

## 13. Real-effect command (spec §21-22)

```
sudo -n /opt/pcae/runtime/venv/bin/python3 \
  /opt/pcae/runtime/src/scripts/hatp_certification_admin.py create \
  --repository-root /opt/pcae/runtime/src \
  --certified-by "Atila Madai" \
  --verification-record-path /opt/pcae/runtime/src/docs/PHASE_149O_20L_7O_2H_3_HMIC_PATHS_SOURCE_SCOPE_AND_SEVEN_CONTRACT_CONSISTENCY_INDEPENDENT_VERIFICATION.md \
  --assume-yes
```

Output: `certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7 already_existed=False` (exit 0).

## 14. Immediate persisted-record verification (spec §23-24)

Read back through `load_certification()` (production reader):

| Field | Value |
|---|---|
| `certification_id` | `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` |
| `repository_instance_id` | `0107866f-af7c-40b4-8317-74e71acb05ca` |
| `canonical_deployment_root` | `/opt/pcae/runtime/src` |
| `implementation_commit` | `305f8e7913bac76941dade6ff4e018c74533f062` |
| `implementation_scope_digest` | `cd021db4b6b74d6d62420be7f74f3791e759a72f142ffb151640d2b88d39412f` |
| `contract_versions` | (all 7, exact match to §5) |
| `verification_record_digest` | `b49cabe2717529273c3c463e752bfa8b423350b47e0fa77ffcfba605e0b7b0e9` |
| `certified_at` | `2026-08-20T08:08:14.576Z` |
| `certified_by` | `Atila Madai` |
| `status` | `active` |
| `revoked_at` | `None` |

Every field matches the precomputed target exactly. `certifications.json` contains exactly one record (byte-verified count).

## 15. Active binding after (spec §25)

`certification-bindings.json`: **does not exist**. No active binding — as authorized.

## 16. HMIC validator after (spec §26)

`validate_active_hatp_mandatory_independent_verification_certification()`: **`MISSING`** (a stored-but-inactive record does not satisfy validation without a binding).

## 17. Readiness after (spec §27)

`certification_status_satisfies_readiness(MISSING)` → **`False`**. The readiness term is derived dynamically from the fresh validator call (no hardcoded ceiling flip occurred, none was touched).

## 18. HATP state after (spec §28)

No `activate_hatp_mandatory` call occurred; no cutover/activation artifact exists anywhere under `/etc/pcae`. **NOT READY / NOT ACTIVE.**

## 19. Class-B diagnostic after (spec §29)

Re-run under the exact established precedent invocation (`sudo -u pcae`, clean `env -i`, `verify_class_b_deployment_conformance()` with no repository-root override — recovered from `docs/PHASE_149O_20L_7D_11_...md` §28):

**`NON_COMPLIANT`** — 32/33 checks satisfied; sole residual **`HBDC-REQ-042` (`no_active_deployment_binding_matches_repository_and_root`)** — exactly the expected pre-DeploymentBinding residual. (An earlier read-only probe run as root via `sudo -n` directly, not matching this precedent invocation, produced a spurious wider failure set purely as an artifact of uid=0 tripping agent/admin-co-mingling checks; discarded once the correct `sudo -u pcae` invocation was used.)

## 20. No-touch confirmations (spec §31-33, §37)

- No FIDO2/CTAP enumeration or touch.
- No HardwareCredentialRecord, Principal, Signer, or DeploymentBinding created (confirmed absent both before and after, wider `/etc/pcae` search).
- No source redeployment — Dell `git rev-parse HEAD` unchanged at `305f8e79` throughout.
- No Protected Root topology mutation — perms/ownership/ACL unchanged (`root:pcae 750`, ancestor chain `root:root 755`); only new files created *inside* the existing directory by the ceremony itself (`.certification-transition.lock`, `certifications.json`).
- Runtime unchanged: `Observed / observe / unavailable` (`pcae runtime inspect`).

## 21. Disposable phase-local tests (spec §38)

Two layers, neither touching the real Protected Root:

1. Ad hoc script (`/tmp/test_2k3_disposable.py`, not committed) against a `tempfile.TemporaryDirectory()` root with `derive_*` functions patched to fixed values: confirm-declined → no write; confirm-accepted → single active record; exact-byte-identical replay → idempotent, no duplicate; `activate` on an unknown ID → fails closed with `CertificationRecordNotFoundError`.
2. Committed suite `tests/test_phase_149o_20l_7o_2k_3_...py` (6 tests, all passing) — the same writer-behavior coverage plus static checks that the admin script's import lines never reach `hatp_mandatory_cutover`, `permission_broker`, FIDO2, `DeploymentBinding`, `Principal`, or `Signer`.

## 22. Fast Green (spec §39)

Ran `pytest -m fast_green -n auto` on the phase tree (before the real
mutation) and, separately, on a disposable `git worktree` pinned to the
phase-entry commit `03b51f12` (identical source — this phase made no
`src/`/`scripts/`/contract changes). Concurrent execution of both
suites produced shared-audit-directory interference in
`tests/test_shell_gate.py::TestAuditPersistence` (opposite members of
that class failing in each run) — resolved by a clean solo re-run.

**Solo-run classification (phase tree vs. baseline worktree, both clean single-process runs):**

- Baseline: 332 failed, 8337 passed, 4 skipped, 9 errors.
- Phase tree: 332 failed, 8337 passed, 4 skipped, 9 errors — **identical count**, and the failing node sets differ by exactly one substitution:
  - **New:** `test_phase_149o_20l_7d_11_..._execution.py::TestNoBoundaryCOrAThisPhase::test_no_certification_artifact_created_this_phase` — a historical phase's own `git status --short` substring guard (`assert "certification" not in line.lower()`) tripping on this phase's own task-file name (`...certificationrecord-real-host-creation...`), which is untracked at the time the suite ran (before the real mutation). A false-positive keyword collision from a prior phase's overly literal self-check, not a code regression — the same category already documented for `no_go_confirmation` keyword collisions elsewhere in this repository's history.
  - **Resolved:** `test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record` — only appeared under the concurrent dual-suite run; confirmed flaky/non-deterministic due to shared real audit-directory state, not attributable to this phase.

**Zero attributable regressions.** All 332 baseline failures are pre-existing and unrelated (predominantly other phases' own "byte-unchanged-since-entry"/"no drift since election" self-referential guards, which trip for any phase whose entry commit differs from theirs — an inherent, long-documented property of this repository's test suite, not something this phase caused or could remediate within its own narrow scope).

## 23. Governance results (spec §44)

- `pcae health`: healthy (after task-file allowed-files were widened to include the moved idle-task file).
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings only — pre-existing historical `tasks/DONE.md` sync backlog (dozens of entries, unrelated to and pre-dating this phase; not touched here).
- `pcae push check`: clean prior to this phase's own commit.
- `pcae runtime inspect`: `Observed / observe / unavailable`, unchanged.
- Telegram notification sink: configured and enabled.

## 24. No-Go confirmations

- No redeployment of any kind was performed.
- No certification was activated.
- No FIDO2 hardware was touched.
- No HardwareCredentialRecord was created.
- No Principal was created.
- No Signer was created.
- No DeploymentBinding was created.
- No Protected Root topology mutation occurred.
- No readiness change occurred (readiness remains `False`).
- No HATP activation occurred.
- No Permission Broker change occurred.
- No runtime capability change occurred.

## 25. Next DAG node

Do not pre-authorize. With exactly one `CertificationRecord` now present
(inactive, no binding), the plausible next real-effect nodes are HMIC
certification **activation** (binding this exact `certification_id`) or
**FIDO2 hardware-credential enrollment** — the actual next-node choice
should be re-derived fresh from real state by a future phase, not
assumed here.
