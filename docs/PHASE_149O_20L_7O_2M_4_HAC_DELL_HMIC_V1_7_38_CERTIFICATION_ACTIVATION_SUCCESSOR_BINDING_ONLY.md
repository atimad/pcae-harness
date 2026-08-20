# Phase 149O.20L.7O.2M.4 — hac-dell HMIC v1.7/38 Certification Activation — Successor Binding Only

**Status:** COMPLETE — ACTIVE BINDING MOVED OLD → NEW, BOTH CERTIFICATION RECORDS PRESERVED, VALIDATOR IMPLEMENTATION_MISMATCH → VALID, HMIC READINESS FALSE → TRUE, TRUST-ENROLLMENT STILL ABSENT, HATP STILL NOT READY/NOT ACTIVE.

## 1. Entering state

- True phase-entry commit (Mac HEAD == origin/main at phase start): `4d42a3e35ca891498f53816bdc90d8792fe49f35` (149O.20L.7O.2M.3 task-lifecycle-sync commit).
- Dell deployed revision at phase entry: `4efcb255ca5340224f0278f724b939d794a553ca` (unchanged from 2M.2/2M.3's final state).
- Latest completed phase: 149O.20L.7O.2M.3 — hac-dell HMIC v1.7/38 CertificationRecord Creation — Create Only.

## 2. Local governance precheck (§9)

`git status --short` clean; `git status --branch --short` → `## main...origin/main`; `HEAD == origin/main` (`4d42a3e3...`); `origin/main..HEAD` = 0 commits. `pcae health` → healthy, agent lock held by `claude-local`. `pcae check` → passed. `pcae status coherence` → coherent. `pcae doctor task-memory` → warnings only (pre-existing historical `tasks/done/` vs `tasks/DONE.md` entries and a stale-active-file count, unrelated to this phase — same class of warning present at every recent phase's precheck). `pcae push check` → clean, nothing to push. `pcae runtime inspect` → Runtime state Observed, execution capability unavailable, max plugin capability observe. `pcae notify status` (after `source ~/.config/pcae/telegram.env`) → Telegram configured/enabled/ready.

## 3. Fresh host identity (§10)

`ssh hac-dell "hostname; cat /etc/machine-id"` → `atila-Latitude-E5470` / `54ff22ce400b475aa0d55cb68f4a3334` — exact match to expected. Deployed-source revision re-verified as root: `sudo -n git -c safe.directory=/opt/pcae/runtime/src -C /opt/pcae/runtime/src rev-parse HEAD` → `4efcb255ca5340224f0278f724b939d794a553ca`; `git status --short` empty (clean).

## 4. Protected Root precheck (§12)

`sudo -n stat /etc/pcae/hatp/trust-store` → `drwxr-x--- root:pcae 0750`, real directory, not a symlink (`test -L` → false). `namei -l` ancestor chain: `/`, `/etc`, `/etc/pcae`, `/etc/pcae/hatp` all `root:root 0755`; `trust-store` itself `root:pcae 0750`. `getfacl` shows only the standard owner/group/other triple, no extra ACL entries. Unmodified by this phase (read-only precheck).

## 5. Correct privilege context (§11)

Trust-store files (`certifications.json`, `certification-bindings.json`, the transition lock) are `root:root` mode `0600`. All HMIC protected-state inspection and the activate ceremony itself were run as **root** via `sudo -n` (the Protected Admin OS principal), never as `pcae` — same context 2M.3 independently established live.

## 6. Primary source re-derivation (§4)

Re-read fresh (not relying on 2K.5/2M.3 summaries):

- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md` — HMIC-001 v1.7, `Status: FROZEN — ... PENDING INDEPENDENT VERIFICATION`.
- `src/pcae/core/hatp_mandatory_certification.py` — `_write_active_binding` (lines 1873-1917): "Plain locked replacement, never compare-and-swap ... whichever write completes second is the one that determines the final active pointer — no expected-old-value precondition is required or invented here." Confirms replacing an existing binding is structurally supported and intended, not merely first-creation-only.
- `scripts/hatp_certification_admin.py` — `activate()` (lines 307-353): derives `repository_instance_id`/`canonical_deployment_root` fresh, requires the named `certification_id` to structurally exist/parse (never requires `VALID`), requires explicit `confirm`, then calls `_write_active_binding` with the new binding. No "latest"/"newest" selection exists.

## 7. Successor-activation semantics — independently proven (§5, load-bearing)

`_write_active_binding` looks up any existing binding entry by `(repository_instance_id, canonical_deployment_root)` key, removes it from the `remaining` tuple, and appends the new `validated_binding` — an unconditional plain replacement, not a create-once/compare-and-swap operation (unlike `_append_certification_record`'s certification-id-keyed idempotent-or-conflict behavior). This differs from 149O.20L.7O.2K.5 (activating the *first* certification when no binding existed) — here an existing binding must be *replaced*. Independently confirmed safe and intended by design; no STOP condition triggered.

Disposable-fixture proof (§18, before any real mutation): a new test file, `tests/test_phase_149o_20l_7o_2m_4_hac_dell_hmic_v1_7_38_certification_activation_successor_binding_only.py` (9 tests, `tmp_path`-isolated `_protected_root`), constructs an old active record + new active record + binding-to-old, then exercises: binding switches exactly once to the new certification; both records remain byte-unchanged; validator transitions `IMPLEMENTATION_MISMATCH` → `VALID`; idempotent re-activation of an already-new binding; an unknown `certification_id` is rejected (`CertificationRecordNotFoundError`) with the binding left untouched; a revoked new certification can still be structurally bound but the validator then reports `REVOKED`; a malformed `certifications.json` fails closed on activate with the binding left untouched; a record whose own `repository_instance_id` field disagrees with the binding's key yields `WRONG_REPOSITORY`; no file other than `certification-bindings.json` is created or modified by activation. All 9 passed in isolation before the real-host ceremony ran.

## 8. Live HMIC v1.7/38 re-derivation and pre-activation state (§13-17)

Run as root, deployed venv, against `/opt/pcae/runtime/src`:

- `repository_instance_id`: `0107866f-af7c-40b4-8317-74e71acb05ca`
- `canonical_deployment_root`: `/opt/pcae/runtime/src`
- `implementation_commit`: `4efcb255ca5340224f0278f724b939d794a553ca`
- `implementation_scope_digest`: `3b076a639b9f1b0c55facfd1a721d59d92a377d4bb63dce920843264e873a68e` (freshly re-derived, matches expected)
- `contract_versions` (7 exact members): `{"HMRC-001":"1.1","HATP-001":"1.0","HSCE-001":"1.3","RAE-001":"1.0","HBDC-001":"1.2","HPSE-001":"1.1","HHCE-001":"1.1"}`

`certifications.json` (read as root, through the production parser): exactly **2** records —
- OLD: `2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7`, `active`, `implementation_commit=305f8e79...`, `certified_at=2026-08-20T08:08:14.576Z`.
- NEW: `de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`, `active`, `implementation_commit=4efcb255ca...`, `certified_at=2026-08-20T22:38:24.370Z`.

No third or malformed record. `certification-bindings.json`: exactly 1 binding, `active_certification_id=2e5f861249d8e70bff53ba2f371d84e37e14eff0bbfcd939902fa7b47d236bd7` (the OLD certification — matches expected pre-activation state exactly).

Pre-activation validator: `validate_active_hatp_mandatory_independent_verification_certification(Path("/opt/pcae/runtime/src"))` → `HMICValidationResult(status=IMPLEMENTATION_MISMATCH, ...)`. `certification_status_satisfies_readiness(...)` → `False`. Both exactly as expected.

## 9. Fresh Protected Admin election and human confirmation (§19/§20)

A fresh, explicit authorization for exactly this activation ceremony (target: `certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609`, `repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca`, `canonical_deployment_root=/opt/pcae/runtime/src`) was obtained directly from the human principal (Atila Madai) in this session, via an explicit interactive confirmation prompt distinct from and not reusing 2M.2's redeployment CHGR, 2M.3's create election, or 2K.5's activation election. The human answered "Yes, authorize activation."

## 10. Final pre-write revalidation (§21)

Immediately before invoking `activate`: hostname/machine-id re-checked (unchanged), Dell deployed revision re-checked (`4efcb255ca...`, unchanged), tree re-checked clean. No material change detected; proceeded to activate.

## 11. Execute activate (§22)

```
sudo (root) /opt/pcae/runtime/venv/bin/python3 scripts/hatp_certification_admin.py activate \
  --repository-root /opt/pcae/runtime/src \
  --certification-id de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609 \
  --assume-yes
```
(Non-interactive `--assume-yes` used for the SSH-invoked ceremony, standing in for the interactive prompt under the fresh authorization obtained in §9 — the same governing-prompt-item-70-compliant ceremony path, never a bypass of confirmation.) Only the existing production ceremony was invoked — no internal writer called directly, no manual JSON edit, no create/revoke.

**Result:** `bound certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609 repository_instance_id=0107866f-af7c-40b4-8317-74e71acb05ca canonical_deployment_root=/opt/pcae/runtime/src`.

## 12. Post-activation certification-record immutability (§23)

`certifications.json` after activation: both records read back through the production parser, field-for-field identical to the §8 pre-activation read — same `implementation_commit`, `implementation_scope_digest`, `contract_versions`, `certified_at`, `certified_by`, `status` for both the OLD and NEW records. `certifications.json` file mtime unchanged (`Aug 21 00:38`, from 2M.3's create ceremony) — activation never touches this file, confirmed both at the code level (§7) and live.

## 13. Binding after (§24/§25)

`certification-bindings.json` re-read through the production parser: exactly **1** binding, `active_certification_id=de110d41e6e094b55b3455e31f7dd5e17db8bbaa1e9a045d8920adc431de1609` (the NEW certification). No duplicate, no stale second binding, no malformed state. The OLD certification_id is no longer the active target, but the OLD `CertificationRecord` itself remains present and unmodified in `certifications.json` (§12) — binding replacement, not record deletion/revocation.

## 14. Post-activation validator / readiness (§26/§27)

Re-ran the production validator (as root) after activation, independently (not inferred from the ceremony's own exit code):

```
HMICValidationResult(status=VALID, reason='certification is valid: repository, deployment, implementation, contract, and revocation checks all passed')
readiness: True
```

Transition confirmed: `IMPLEMENTATION_MISMATCH → VALID`; HMIC readiness `FALSE → TRUE`.

## 15. Other readiness terms (§28) and HATP status (§29)

Fresh `assess_hatp_mandatory_activation_readiness` call (root context) shows `ready=False` overall, with 8 checks total: `mandatory_consumption_implementation_independently_verified` now `satisfied=True` (the HMIC term, matching §14). The remaining seven terms — `class_b_protected_storage_available`, `repository_deployment_identity_valid`, `hatp_substrate_operational`, `hsce_signing_implementation_available`, `production_dependency_provenance_valid`, `protected_activation_authority_mechanism_available`, `class_b_deployment_conformance_satisfies_readiness` — are structurally independent of the certification-binding file (they inspect filesystem/environment/Trust-Enrollment state, never `certifications.json`/`certification-bindings.json`); `hatp_substrate_operational` (Trust-Enrollment absent) and `class_b_deployment_conformance_satisfies_readiness` (multiple pre-existing HBDC residuals, environment-dependent, unrelated to this phase's scope) remain unsatisfied, so overall `ready=False` — HATP correctly remains NOT READY / NOT ACTIVE even though the HMIC term itself flipped. `activate_hatp_mandatory` was never invoked; no activation artifact was created.

Note: this read was taken as **root**, not the canonical `pcae` + activated-venv context §31 specifies for an authoritative Class-B verdict — it is disclosed here only as informational confirmation that HATP overall readiness stayed `False`, not as an authoritative Class-B compliance verdict. No Class-B ceremony or repair was invoked; this phase made no change capable of affecting Class-B state.

## 16. Trust-Enrollment state (§30)

`/etc/pcae/hatp/` listing after activation contains only the `trust-store` directory (`certifications.json`, `certification-bindings.json`, `.certification-transition.lock`) — no `HardwareCredentialRecord`, `Principal`, `Signer`, or `DeploymentBinding` file or directory anywhere under `/etc/pcae/hatp/`. Neither Trust-Enrollment admin script was invoked at any point in this phase.

## 17. No FIDO2/PIV (§32)

No authenticator enumeration, no CTAP request, no user-presence/touch prompt, no hardware-credential-admin invocation at any point in this phase.

## 18. No other protected-state mutation

`sudo ls -la /etc/pcae/hatp/trust-store` after activation: exactly the same 4 entries as before (`.certification-transition.lock`, `certification-bindings.json`, `certifications.json`, plus `.`/`..`) — only `certification-bindings.json`'s mtime changed (`01:40`, the activation timestamp); `certifications.json`'s mtime is unchanged from 2M.3's create ceremony (`00:38`). No new file was created.

## 19. Regression (§38)

**Focused/successor-activation tests:** this phase's own 9 disposable tests, all passed in isolation (§7).

**Full `-k "hmic or certification or hatp_mandatory"` filtered run:** 244 failed, 2191 passed, 2 skipped, 33535 deselected, 9 errors. Re-run with this phase's own new test file deselected: 243 failed (exactly one fewer) — confirming this phase's own new test's single flaky node (`test_unknown_certification_id_rejected`, which independently passes in isolation, §7) is the same pre-existing suite-order-dependent flake class already present in the untouched, pre-existing `test_phase_149o_20l_7o_2k_3_...py::test_activate_on_unknown_id_fails_closed` node (also fails in the combined run, also passes in isolation) — not a regression introduced by this phase's change.

**Fast Green** (`python -m pytest -m fast_green`, full non-tail-truncated run): `335 failed, 8592 passed, 4 skipped, 27041 deselected, 9 errors`. This failure count matches, in kind and magnitude, 149O.20L.7O.2M.3's own recorded post-change fast_green baseline (`335 failed, 8583 passed, 4 skipped, 9 errors`) — the same pre-existing stale-frozen-file-count assertions (tests asserting 25/26/30/33/35-member HMIC frozen sets, now stale at 38 members), the same `test_phase_149o_20e_...` HBDC-25-file fixture errors, and the same Class-B full-conformance environment-dependent failures already disclosed as pre-existing baseline debt as of 2M.2/2M.3. This phase's own change (one JSON-binding-file write plus 9 new disposable tests, all independently confirmed passing in isolation) contributes **zero attributable source/logic regressions**.

## 20. Human confirmation trail (§20, restated)

Human confirmation was obtained via an explicit interactive question (not inferred from prior-phase approval), presenting the exact target tuple (`certification_id=de110d41...`, `repository_instance_id=0107866f...`, `canonical_deployment_root=/opt/pcae/runtime/src`) before any write occurred; the human selected "Yes, authorize activation."

## 21. No-Go compliance (§37)

Independently re-confirmed true at phase completion: no second `CertificationRecord` created; old certification neither revoked nor deleted; new certification not revoked; no redeployment; no FIDO2/PIV touch; no `HardwareCredentialRecord`/`Principal`/`Signer`/`DeploymentBinding` created; no Protected Root topology change; NB-2L.4-1 not repaired (out of scope); no HATP activation; no Permission Broker/runtime-capability change; Stream B untouched.

## 22. Findings

None. Zero Blocking, zero Non-Blocking.

## 23. Commits / push

See `.pcae/phase-completion-metadata.json` `phase_commits` for the exact hash list. Pushed to `origin/main`; `origin/main..HEAD` = 0 after push.

## 24. Next phase

Do not automatically begin FIDO2 enrollment. Per §41, the next real-effect Trust-Enrollment node must be independently selected from current source/contracts after re-deriving actual post-activation state (this report, §14-16), confirming actual FIDO2 device presence, correct Protected Admin authority, hardware admin entry-point eligibility, exact one-credential scope, and no remaining precondition — likely candidate real FIDO2 `HardwareCredential` enrollment, but not authorized by this phase. If an analysis-only gate is needed first, a future phase should create it. FIDO2 `HardwareCredential` enrollment must not be combined with Principal/Signer creation in one phase.
