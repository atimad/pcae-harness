# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 — N-16-5 PAWA Production Protected-Admin Writer Anchor Implementation (Slice 1)

**Status:** COMPLETE — HPAC-PAWA-001 v1.1 **IMPLEMENTED FOR SLICE 1 — IV
(`.1R.30R.3.2`) PENDING — N-16-5 NOT CLOSED.**
FIDO2-free. Atomic unit A1: the exclusion resolver ships together with the
writer factory.

- **Phase-entry SHA `A`:** `1793a75a73c54c6f6687bc830664caeac5aeaa66`
  (== finalized `.1R.30R.2A.3` head).
- **`B30`:** `8e65529596fc351face4b83c4b5d08573326d034` (immutable `.1R.30`
  BLOCKED — never reused, never resumed; PAWA-INV-11).
- **`H30R` / `V` (`.1R.30R.1` baseline):**
  `ca0d42873f14bb94e8eb4ef7a27e1b456324cd2a`.
- **`J` (`.1R.30R.2A.1` baseline):**
  `1dbd41cb5b9fb428ce7eb0b9ff80d6b48d3fbd4a`.
- `origin/main..HEAD` at entry: **0**.

## 1. Governing baseline (binding)

HPAC-PAWA-001 **v1.1** (FROZEN, `.1R.30R.2A.2`; independently VERIFIED WITH
NON-BLOCKING FINDINGS by `.1R.30R.2A.3`) — including
`HPAC-PAWA-AGENT-EXCLUSION/1.0`, `symbolic_account` + `provisioned_uid`
(R1-HYBRID), live `getpwnam` uid pin, live primary+supplementary groups,
`agent_exclusion_digest`, the `HPAC-PAWA-CURRENT-GENERATION/1.0` binding, the
21 closed `pawa_failure_code` values, the descriptor schema **unchanged**,
the 11-step §33 recognition model with v1.1 substeps, the
`O_EXCL|O_NOFOLLOW` positive probe, the process-local / non-bearer /
restart-invalid / one-operation capability, the finite consumer inventory,
the two-principal requirement, and the offline / local OS-administration
TCB. Implementation is driven by the v1.1 contract, not the phase prompt,
where they differ.

## 2. Production files changed

| File | Change |
|---|---|
| `src/pcae/core/hpac_pawa_schemas.py` | **NEW.** Closed `HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0` (§14, 13-field, shape byte-unchanged from v1.0), v1.1 closed **7-field** `HPAC-PAWA-CURRENT-GENERATION/1.0` (§20A — adds `agent_exclusion_digest`; schema id `/1.0` kept), `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` (§55). Pure schema / self-excluding-digest / grammar helpers. Reads no OS, resolves no root, mints nothing. |
| `src/pcae/core/hpac_pawa_agent_exclusion.py` | **NEW.** Closed **12-field** `HPAC-PAWA-AGENT-EXCLUSION/1.0` + trusted load/validate + `resolve_configured_agent_identity()` (R1-HYBRID: protected record → `symbolic_account` → live `pwd.getpwnam` + `os.getgrouplist` → `(uid, gids)`; `live uid == provisioned_uid` pin; live groups; `agent_exclusion_digest` currentness; fail-closed → `AgentExclusionError` → `agent_principal_unknown`). Inside the non-agent-importable fence. |
| `src/pcae/core/hpac_protected_admin_writer.py` | **NEW.** §33 **11-step** positive recognition sequence (steps 2/3/7 = atomic exclusion substeps); `production_writer` factory (§36); one-operation `ProductionWriterHandle` (§49); closed **21-value** `PAWA_FAILURE_CODES` + `RHAMP_TERMINAL_REASON_MAP` (§56/§57 — no new code); `_positive_write_probe` (`O_CREAT\|O_EXCL\|O_NOFOLLOW` + random sentinel + write + fsync + close + unlink, §28/§29); exact `AUTHORIZED_FACTORY_CONSUMERS` frozenset (no wildcard, PAWA-INV-9); protected `.authority/` record I/O; bounded principal-admin ops (`enroll_principal_via_pawa` / `revoke_*`); out-of-band `provision_protected_root` / `set_agent_exclusion` / `rotate_descriptor` / `revoke_anchor` (filesystem primitives, no `HPACWriterCapability`, no FIDO2 — non-circular, PAWA-INV-4). Inside the non-agent-importable fence. |
| `src/pcae/core/hpac_foundation.py` | **MODIFIED (additive).** `_PRODUCTION_WRITER_FACTORY_SEAL` + `_mint_production_writer_capability` (seal-guarded, reachable only from the fence). `HPACWriterCapability.__slots__` += `_single_use` / `_spent` (never caller-resettable; `_mark_spent` seal-guarded; `record_write` sets it after one mutation; `require_writer` rejects a spent capability). `_validate_production_boundary` / `_relative_record_path` re-scoped per **F-1**: on the production-writer path the negative boundary keys off the resolved configured-agent identity, falling back to the live process only when none is bound. Single `HPACWriterCapability(` construction site preserved (a shared `_new_capability` helper). `writer()` still raises for every non-`FIXTURE_NON_REAL` class (HPAC-PAWA-REQ-092). Disclosed test-only `_production_test_fixture` / `_topology_probe` seams (§72/§73, guard-checked). |
| `src/pcae/core/human_principal_registry.py` | **MODIFIED (additive).** `_writer` / `_write` thread a `PRODUCTION` subject scope through `require_writer` (§43/§44/§60 — a capability minted for principal A cannot write B). The `FIXTURE_NON_REAL` path and `CredentialRecord` schema are byte-unchanged. |
| `scripts/hpac_protected_root_admin.py` | **NEW.** Standalone CLI wrapper (`provision` / `set-agent-exclusion` / `rotate` / `revoke` / `enroll-principal` / `revoke-principal`); resolves `--agent-account` against the OS account DB; not a `pcae` subcommand, not on any dispatch table. |

## 3. Contract → source → test → guard traceability (load-bearing clauses)

| v1.1 clause | Symbol | Durable artifact | `pawa_failure_code` | Fresh test |
|---|---|---|---|---|
| §32A.1 closed schema | `validate_agent_exclusion_record` | `.authority/agent-exclusion.json` | `agent_principal_unknown` | `test_03` / `test_16` |
| §9.1 / HPAC-PAWA-REQ-164 named source | `resolve_configured_agent_identity` | — | `agent_principal_unknown` | `test_05` / `test_19` |
| §32A.4 / C-1 uid pin | `_live_identity_from_os` (`live uid == provisioned_uid`) | — | `agent_principal_unknown` | `test_07` / `test_09` / `test_10` / `test_11` |
| §32A.5 deletion | `_live_identity_from_os` (`KeyError`) | — | `agent_principal_unknown` | `test_08` |
| §32A.6 live groups + drift | `os.getgrouplist` + §33 step 3 | — | `agent_has_protected_write_authority` | `test_12` / `test_13` / `test_14` |
| §32A.6 group removal recovery | live re-resolution every call | — | — | `test_15` |
| §20A / C-2 anchor-digest bind | `validate_current_generation` + step 6 digest check | `current-generation.json` `agent_exclusion_digest` | `agent_principal_unknown` | `test_25` / `test_26` / `test_93` |
| §21 descriptor rollback | step 6 `descriptor.generation < current_generation` | — | `descriptor_generation_stale` | `test_27` |
| §28/§29 positive probe | `_positive_write_probe` | `.probe-<hex>` sentinel (removed) | `write_probe_failed` | `test_29`-`test_33` |
| §31 / HPAC-PAWA-REQ-201 not-agent context | step 7 `live_uid == configured_agent.uid` | — | `current_context_is_agent` | `test_18` |
| §10 three distinct F-1 predicates | steps 3 / 7 / 8 | — | — | `test_17` |
| §61 two-principal | step 3 `_effective_write_access` | — | `agent_has_protected_write_authority` | `test_20` |
| §33 step 9 consumer | `AUTHORIZED_FACTORY_CONSUMERS` + `_detect_caller_module` | — | `unauthorized_factory_consumer` | `test_40` / `test_41` |
| §36/§41 mint + seal | `_mint_production_writer_capability` (seal identity) | — | `internal_fail_closed` | `test_36` / `test_54` / `test_55` |
| §45-§47 process-local / non-bearer / non-serializable | `__slots__` + `__reduce__` | — | `reconstruction_attempt` | `test_56`-`test_58` / `test_66` |
| §48 restart invalidation | fresh `_seal` per `HPACStoreAuthority` | — | `capability_stale` | `test_59` |
| §49/§107 one-operation | `_spent` + `ProductionWriterHandle.consume` | — | `capability_stale` | `test_60` / `test_68` |
| §42-§44 scope | `_validate_operation_inputs` + `require_writer` subject | — | `operation_scope_invalid` / `target_scope_invalid` | `test_61`-`test_63` |
| §55 issuance evidence | `_record_issuance_evidence` | `.authority/issuance-evidence/<op>.json` | — | `test_64` |
| §60 registry consumption | `HumanPrincipalRegistryStore._writer` / `_write` | `principals/principal-registry.json` | — | `test_53` / `test_65` / `test_69` |
| §23/§32B provisioning | `provision_protected_root` / `set_agent_exclusion` | manifest + descriptor@1 + current-generation@1 + agent-exclusion + provenance | `duplicate_bootstrap` | `test_44`-`test_48` |
| §50/§51 rotation / revocation | `rotate_descriptor` / `revoke_anchor` | — | `descriptor_generation_stale` / `descriptor_revoked` | `test_47` / `test_49` |
| §56 taxonomy | `PAWA_FAILURE_CODES` (21, closed) | — | — | `test_51` / `test_52` |
| §57 RHAMP map | `RHAMP_TERMINAL_REASON_MAP` (no new code) | — | — | `test_52` |
| §37-§39 fence | module docstring + guard test | — | — | `test_39` / `test_42` / `test_43` |
| §16 test seam | `_protected_root` / `_configured_agent_identity_source` / `_topology_probe` (leading-underscore, documented) | — | — | `test_05` (no account param) |

## 4. §33 recognition sequence (as implemented)

`_run_recognition_sequence`, run **fresh on every `production_writer(...)`
call** (HPAC-PAWA-REQ-075; no caching — `test_94`), inside one atomic unit
with the mint (PAWA-INV-3):

1. resolve canonical `<HPAC_PROTECTED_ROOT>` (no input); reject
   symlink / non-dir / group-or-other-writable / absent `.authority/` →
   `protected_root_missing` / `protected_root_untrusted`;
2–4 preload: `HPAC-STORE-AUTHORITY/1.0` manifest + `{device,inode}` root
   identity + `.authority/` ownership/mode; the descriptor (closed schema,
   self-excluding digest, `protected_root_identity`, ownership/mode,
   provenance, `state == ACTIVE`); the current-generation anchor (v1.1
   7-field, digest, `installation_id`, `descriptor.generation ==
   current_generation`, digest match, monotonicity);
5. **step 2 (v1.1 substeps):** load `agent-exclusion.json` no-follow;
   ownership/mode; `resolve_configured_agent_identity` (closed schema,
   self-excluding digest, `installation_id` + `{device,inode}` binding,
   `record_digest == current-generation.agent_exclusion_digest`,
   `state == ACTIVE`, `symbolic_account` grammar, live `getpwnam`,
   `live uid == provisioned_uid`, live groups); provenance verify. Any
   fault → `agent_principal_unknown`;
6. **step 3:** `_effective_write_access(root, configured_uid,
   configured_gids) == False` **and** `_ancestor_chain_safe(...) == True`
   against the resolved configured-agent identity (F-1, **not**
   `_current_agent_identity()`); indeterminate → `protected_root_untrusted`;
   agent-writable / drift → `agent_has_protected_write_authority`;
7. **step 7:** live `_current_agent_identity()` uid `==` configured-agent
   uid → `current_context_is_agent`;
8. **step 8:** `O_CREAT|O_EXCL|O_NOFOLLOW` write probe of a random
   `.probe-<hex>` under `.authority/` + write + fsync + close + unlink;
   any failure or un-removable sentinel → `write_probe_failed`;
9. calling module ∈ `AUTHORIZED_FACTORY_CONSUMERS` (exact, no wildcard)
   → else `unauthorized_factory_consumer`;
10. bind the configured-agent identity into the authority (so every
    subsequent `_validate_production_boundary` / `record_write` re-run
    keys the negative boundary off the configured agent — F-1), then
    `_mint_production_writer_capability` (single `HPACWriterCapability(`
    site; `single_use=True`);
11. `HPAC-PAWA-ISSUANCE-EVIDENCE/1.0` durable audit (never capability,
    PAWA-INV-10).

Any unexpected exception anywhere → `internal_fail_closed` (§0).

## 5. `no sudo / euid` shortcut

Static (`test_34`): no `geteuid() == 0` / `getuid() == 0` / `SUDO_USER` /
`SUDO_UID` string in any new module's code. `os.geteuid()` is used **only**
as the step-8 probe subject and one operand of the step-7 comparison —
never the operand of `agent_has_protected_write_authority` (F-1). No
`os.access()` as authority proof (`test_30`).

## 6. One-operation semantics (§49 / §107)

Additive `_spent` flag on `HPACWriterCapability` (`__slots__` extended by
`_single_use` / `_spent` — no existing semantics weakened,
HPAC-PAWA-REQ-082). `record_write` calls `_mark_spent(_WRITER_CONSTRUCTOR_SEAL)`
after one successful mutation; `require_writer` then raises →
`HumanPrincipalRegistryError`. The factory-layer `ProductionWriterHandle.consume`
additionally raises `PawaError("capability_stale")` on a second call.
`test_60` proves both layers.

## 7. Positive isolated admin fixture (§71)

`test_36` / `test_53`: a `_production_test_fixture` protected root
(disclosed test-only, `_PRODUCTION_TEST_FIXTURE_SEAL`), a valid
descriptor / current-generation / exclusion set, a synthetic configured
agent that resolves to a distinct account with no protected-root write
authority, an authorized consumer, a deterministic `TopologyProbe`
(the platform ACL adapter is unavailable in sandboxed CI —
HPAC-PAWA-REQ-132/166) → a **PRODUCTION** `HPACWriterCapability` is
minted and drives exactly one bounded registry mutation.

## 8. Guard reconciliation (point-in-time, phase-aware)

**No `def test_` renamed, removed, skipped, or xfailed** (verified against
the `.1R.19R` / `.1R.22R1` / `.1R.23` no-test-weakening scanners).

| Suite | Test(s) | Reconciliation |
|---|---|---|
| `.1R.30R.1` IV | `test_no_src_pcae_change_since_b30` | upper bound `HEAD` → `_2A3_FINALIZED_HEAD` (immutable SHA `1793a75a`) |
| `.1R.30R.1` IV | `test_no_production_writer_factory_symbols_anywhere_in_src`, `test_writer_refuses_non_fixture_class`, `test_registry_writer_gate_has_no_third_path` | split: `git show H30R:...` historical assertion + current-state counterpart (the PAWA fence + the two hook points) |
| `.1R.30R.2A.1` IV | `test_validate_production_boundary_uses_live_identity`, `test_no_getpwnam_configured_agent_bridge_in_production`, `test_no_pcae_agent_principal_symbol_in_production` | split: `git show J:...` historical assertion + current-state; `hpac_pawa_agent_exclusion.py` recorded as the sanctioned v1.1 bridge |
| `.1R.3.1` / `.1R.3.2` / `.1R.3.2.1` HPAC consumer-inventory | `test_new_hpac_modules_have_zero_preexisting_production_consumers`, `test_hpac_repair_has_zero_preexisting_production_consumers`, `test_foundation_has_no_production_consumers_or_gate_wiring` | `AUTHORIZED_CONSUMERS` widened by the exact 4 `(file, module)` tuples — no wildcard |
| `.1R.8` / `.1R.11.7` / `.1R.17` / `.1R.19R` | `test_isolation_only_three_production_files_changed_since_baseline`, `test_production_file_allowlist_matches_frozen_phase_matrix`, `test_production_scope_since_baseline_is_the_single_new_file`, `test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap` | authorized-file subset invariant widened by the exact five-file PAWA set — no wildcard |

All other point-in-time "no working-tree `src/pcae` diff" guards
(`.1R.17R`, `.1R.15.3`, HSCE, HMRC) **self-resolve on commit**. The
`.1R.18` / `.1R.19R` / `.1R.20` meta-guards that re-run the reconciled
guards at HEAD recover once the reconciliations are committed.

## 9. Fixed-SHA A/B attribution

`A = 1793a75a` (phase entry), `B = HEAD` (candidate). Targeted affected
scope: 61 suites (every test importing `hpac_foundation` /
`human_principal_registry` / the new PAWA modules, plus every
`no-src-change` / consumer-inventory / no-test-weakening guard).

- **Candidate-only unexplained functional failures: 0.**
- Every candidate-only guard failure was a documented point-in-time
  scope-fence trip and is reconciled above (32 auto-resolved on commit,
  6 reconciled in `tests/`).
- **Pre-existing, `git stash`-identical failures — NOT attributable to
  `.1R.30R.3.1`** (reproduce byte-identically on `A`):
  - `test_hpac_foundation_independent_verification_3w1r2b1r111r31.py` — 8
    `test_blocking_reproduction_*` + `test_deterministic_authenticator...`
    (historical `.1R.3.1` blocking-finding demonstrations);
  - `test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` — 2
    (`object.__new__` forge findings);
  - `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`
    — 4 (`absolute proof_id` / non-canonical demonstrations);
  - `test_n16_3_reconciliation_iv_3w1r2b1r1_1r22r1.py` — 4 (contracts
    legitimately moved by `.1R.30R.2` / `.2A.2` / RHAMP / RE phases, all
    after that guard's baseline);
  - class-B topology-verifier suites (`.1R.20I`-`.1R.20L`) — the macOS
    sandbox lacks a trusted `getfacl` / `ls` on `PATH` so
    `_effective_write_access` returns indeterminate;
  - `test_hpac_trust_root_repair_independent_verification_...::test_concurrent_conflicting_successors_have_one_canonical_winner`
    — a `ThreadPoolExecutor` timing flake (3/3 pass in isolation on both
    `A` and `B`).

## 10. Scope-fence proof (Slice-1 non-implementation)

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py`
— **95 passed, 0 failed**:

- FIDO2-free: no `import fido2` / `Ctap2` / `CtapHidDevice` / `CoseKey` /
  `AuthenticatorData` in new code (`test_78`);
- no `RHAMP-FIDO2-CREDENTIAL/1.0` / `RHAMP-COUNTER-STATE/1.0` file or
  symbol; no `rhamp_fido2_credential.py` / `rhamp_counter_state.py`
  (`test_79`);
- no enrollment ceremony, no `FIDO2HumanAuthenticator`, no `makeCredential`
  / `getAssertion` (`test_80`);
- `src/pcae/core/hpac_verifier.py` `git diff --stat A HEAD` **empty**
  (`test_81`); `_ELIGIBLE_MECHANISM_IDS` unchanged, no
  `hpac.fido2.uv_presence.v2` (`test_82`);
- no protected presentation, no `require_real_assurance` (`test_83`);
- `runtime_dispatch_gate5.py` / `runtime_dispatch_gate9.py`
  `git diff --stat A HEAD` **empty** (`test_84`);
- `pcae runtime inspect`: Runtime state `Observed`, Execution capability
  `unavailable`, Plugin count `0`, Capability count `0` (`test_85`);
- no `adapter.dispatch(` / `DispatchEnvelope` / `subprocess` / `socket` /
  `Popen` / `os.system` / `RPAC-REQ-095` in new code (`test_86`);
  no `requests` / `urllib` / `asyncio` (`test_92`);
- `git diff --name-only A HEAD -- docs/contracts` **empty** (`test_87`);
- one `HPACWriterCapability(` construction site, in `hpac_foundation.py`
  (`test_88`); `writer()` still raises for non-fixture classes
  (`test_89`);
- `runtime_dispatch_gate10_eligibility.py` / `permission_broker.py` /
  `runtime.py` `git diff --stat A HEAD` **empty** — N-16-6 / N-16-7
  untouched (`test_91`).

## 11. Runtime / first-effect / N-16 status

- Runtime: `not_implemented` / `Observed` / `observe` / `unavailable`;
  0 plugins / 0 capabilities. **UNCHANGED.**
- First external effect: **ABSENT AND UNREACHABLE.** The only filesystem
  writes are bounded PAWA administrative state under
  `<HPAC_PROTECTED_ROOT>/.authority/` and the protected registry.
- **N-16-5 — NOT CLOSED.** `.1R.30R.3.2` (IV) → `.1R.30R.3.3` / `.3.4`
  (Slice 2 — RHAMP credential registry + `RHAMP-FIDO2-CREDENTIAL/1.0` +
  `RHAMP-COUNTER-STATE/1.0` + enrollment / IV) → `.1R.30R.3.5` / `.3.6`
  (Slice 3 — `FIDO2HumanAuthenticator` + native CTAP2 + `_ELIGIBLE_MECHANISM_IDS`
  widening + 41-code wiring / IV) → `.1R.30R.4` (composite IV) →
  `.1R.30R.5` (protected presentation + `require_real_assurance` through
  Gate 5 / Gate 9) → `.1R.30R.6` (IV + mandatory real-CTAP2-hardware +
  **N-16-5 closure**).
- **N-16-6 / N-16-7 — OPEN, untouched, N-16-7 strictly last.** No Slice C.
- **N-23-1 (INFO) / N-23-2 (INFO / DEFERRED)** — carried unchanged.

## 12. Slice-1 implementation verdict

```
HPAC-PAWA-001 v1.1:                                 IMPLEMENTED FOR SLICE-1 — IV PENDING
CONFIGURED-AGENT RESOLUTION (R1-HYBRID):            IMPLEMENTED — IV PENDING
PRODUCTION PROTECTED-ADMIN WRITER ANCHOR:           IMPLEMENTED — IV PENDING
PRODUCTION HPACWriterCapability:                    IMPLEMENTED — IV PENDING
HumanPrincipalRegistryStore production consumption: IMPLEMENTED — IV PENDING
RHAMP credential / enrollment:                      NOT IMPLEMENTED
Real FIDO2 authentication:                          NOT IMPLEMENTED
Protected presentation:                             NOT IMPLEMENTED
N-16-5:                                             NOT CLOSED
Runtime:                                            Observed / observe / unavailable
First external effect:                              ABSENT
Contract byte identity:                             HPAC-PAWA-001 v1.1 / HPAC-001 v2.1 /
                                                    RHAMP-001 v1.0 / HBDC-001 v1.2 — UNCHANGED
No new pawa_failure_code. No new terminal_reason_code. Descriptor schema unchanged.
```

## 13. Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.2`** — Independent Verification of
the N-16-5 PAWA Production Protected-Admin Writer Anchor Implementation
(Slice 1). Own explicit human authorization required (ID recommended, NOT
reserved). Need not re-verify the v1.1 architecture beyond normal
contract-production equivalence (C-3 discharged by `.1R.30R.2A.3`). Do not
begin it.

## 14. Governance

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.
Governed PCAE lifecycle only: no raw `git commit` / `git push`, no
`--no-verify`, no force push, no history rewrite, no hook bypass.
