# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R — Configured-Agent-Identity Threading Repair for `hatp_class_b_topology_verifier.py`'s ACL Ancestor-Chain Trust Check

**Verdict: CONFIGURED-AGENT-IDENTITY THREADING REPAIR: IMPLEMENTED — FRESH INDEPENDENT VERIFICATION REQUIRED.**

F-5 remains **OPEN / BLOCKED PENDING REPAIR IV**. N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.

## CPIPC lineage

Exact valid successor of `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1` (the F-5
deployment-preparation retry, BLOCKED). No CPIPC discrepancy — the requested ID is the
recommended-next-phase token verified from `pcae phase-report show --latest` at bootstrap.

Repair-entry SHA `R = 5568b5abb578c6072afc3b790aa59223d4f2c73c`.

## Primary defect

The canonical HPAC-PPA registration path (`hpac_protected_admin_writer.py`, §33 STEP 3) already
threads the CONFIGURED PCAE agent principal's resolved `(uid, gids)` — obtained from
`hpac_pawa_agent_exclusion.resolve_configured_agent_identity()`, never `os.geteuid()` (F-1,
HPAC-PAWA-REQ-022) — through `_effective_write_access`/`_ancestor_chain_safe` for the Protected
Root and its ancestor chain. Both call sites, and `hpac_foundation.py`'s
`_validate_production_boundary`/`_relative_record_path`, were independently confirmed **already
correctly threaded** before this repair began (primary-source inspection, no change required
there).

The actual defect lived one layer deeper: the ACL branch of `_effective_write_access`
(`_acl_grants_agent_write` → `_acl_grants_agent_write_linux`/`_acl_grants_agent_write_macos`)
resolves its own ACL-inspection tool (`getfacl`/`ls`) via `_resolve_trusted_executable`, which
derives its subject from the **ambient** `_current_agent_identity()` (the live invoking process)
instead of the `(agent_uid, agent_gids)` subject already passed to the ACL helper. When the
canonical registration path runs as root (the legitimate deployment owner), root-owned,
owner-writable system directories such as `/usr/bin` misclassify as "agent[=root]-writable" under
that ambient-identity question, `_resolve_trusted_executable` returns `None` (untrusted) for
`ls`/`getfacl`, and every Protected-Root ancestor's ACL check becomes `acl_inspection_unavailable`
(indeterminate) — exactly the `protected_root_untrusted: indeterminate permissions:
acl_inspection_unavailable` failure the predecessor F-5 retry hit.

## Blast-radius / consumer inventory

All production consumers of `_current_agent_identity`, `_effective_write_access`,
`_ancestor_chain_safe`, `_resolve_trusted_executable` were enumerated (`git grep`) and classified:

| Consumer | Semantics required | Disposition |
|---|---|---|
| `hpac_protected_admin_writer.py` §33 STEP 3 (root-write / ancestor-chain check) | CONFIGURED_AGENT | Already correct — unchanged |
| `hpac_protected_admin_writer.py` §33 STEP 7 (current-context-is-agent check) | LIVE_PROCESS (deliberate — compares invoking context against the resolved configured agent) | Already correct — unchanged |
| `hpac_foundation.py::_validate_production_boundary` | CONFIGURED_AGENT (falls back to live-process only when unbound; documented dead path in production) | Already correct — unchanged |
| `hpac_foundation.py::_relative_record_path` | CONFIGURED_AGENT (same fallback pattern) | Already correct — unchanged |
| `hatp_class_b_topology_verifier.py::_acl_grants_agent_write_linux`/`_macos` | CONFIGURED_AGENT (must resolve `getfacl`/`ls` against the same subject already passed in) | **DEFECT — repaired here** |
| `hatp_environment_lock_verifier.py` (venv/site-packages/PYTHONPATH/.pth/git-trust checks) | LIVE_PROCESS (own-environment self-check; no configured-agent notion exists here) | Legitimately unchanged |
| `hatp_class_b_conformance.py` (Model-A deployment-identity check) | LIVE_PROCESS (diagnostic-only, non-authoritative, not in the F-5 path) | Legitimately unchanged |

No consumer was left `AMBIGUOUS_REQUIRES_CONTRACT_DERIVATION`.

## Repair design

`_resolve_trusted_executable` itself was deliberately left **completely untouched** — not
refactored into a shared implementation, not given an extra optional parameter — because it is
independently frozen by two earlier phases' own guard tests:

- 149O.20J.1's `test_resolve_trusted_executable_base_primitive_unchanged` (source-content
  assertion: must remain ACL-unaware, mode+group only).
- 149O.20J.2's `test_resolve_trusted_executable_base_primitive_unchanged_since_pre_repair`
  (`git diff -G'def _resolve_trusted_executable\('` pickaxe against that phase's own pre-repair
  baseline commit — a literal-def-line-unchanged guard).

Both were reconfirmed green (independently re-derived, not merely trusted, in the fresh test
suite) after this repair.

Instead, a new sibling primitive was added:
`_resolve_trusted_executable_for_subject(name, agent_uid, agent_gids)` — identical
PATH-precedence-aware algorithm to `_resolve_trusted_executable`, but evaluated against an
explicit subject with no ambient fallback (no default parameters, never calls
`_current_agent_identity()`). `_acl_grants_agent_write_linux`/`_acl_grants_agent_write_macos` now
call it with the same `(agent_uid, agent_gids)` they already receive, instead of the
ambient-identity `_resolve_trusted_executable`.

`_resolve_trusted_executable` continues to serve its one existing caller that legitimately needs
live-process semantics: `_resolve_trusted_executable_with_effective_access`, consumed only by
`hatp_environment_lock_verifier.py`'s own-environment self-check (dev-time diagnostic; no
configured-agent notion applies there).

No root special-case, no hardcoded system-directory allowlist, no PATH-precedence weakening, no
ACL-check bypass, no contract change, no dependency change.

## Historical-defect reproduction

`_resolve_trusted_executable("ls")` (the untouched ambient primitive) resolves the real system
`ls` under a simulated non-owning ambient subject (uid 999999) but fails closed (`None`) under a
simulated root-like ambient subject (uid 0) on this host, because `/usr/bin` is root-owned and
owner-writable — reproducing the exact symptom the predecessor F-5 retry hit. The repaired
`_acl_grants_agent_write_macos`/`_linux`, by contrast, resolve deterministically against their
real explicit `(agent_uid, agent_gids)` subject regardless of what a poisoned ambient identity
returns (`tests/test_phase_...1_1R_configured_agent_identity_threading_repair.py::
test_root_executor_no_longer_poisons_configured_agent_acl_check` and
`::test_before_repair_semantics_reproduced_from_primary_source`).

## Test reconciliation (disclosed, non-weakening)

Three pre-existing tests depended on the exact ambient-identity side effect this repair corrects
— on this dev host, a user-writable Homebrew `PATH` entry precedes the system tools, so the
*ambient* real-user identity used to fail closed to `acl_inspection_unavailable` (`None`) for a
fictitious `agent_uid=999999` subject's ACL check, which `_effective_write_access` propagates as
"not proven safe" and made these assertions pass by accident rather than by genuine ACL evidence.
After the repair, tool resolution is correctly evaluated against the fictitious subject (who does
not own the Homebrew directory), so it resolves the real system tool and correctly, not
accidentally, reports no ACL grant. Each was updated to mock `_effective_write_access`
deterministically instead (matching the pattern their own sibling tests in the same files already
use), isolating each test's actual regression concern from real host ACL/PATH specifics:

- `tests/test_phase_149o_20j_1_class_b_deployment_verifier_narrow_defect_repair.py::test_pth_ordinary_path_line_still_evaluated_as_path`
- `tests/test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_detection_macos_narrow_repair.py::test_acl_inspection_tool_unavailable_fails_closed` (monkeypatch target updated to the new function name)
- `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_implementation_verification.py::test_pth_path_injection_is_rejected`

No `def test_` renamed or removed; no `skip`/`xfail` added; no assertion weakened — each still
asserts the same unsafe-`.pth`-file-is-rejected property, now via deterministic evidence.

## Production diff

`git diff --stat R -- src/`: exactly `src/pcae/core/hatp_class_b_topology_verifier.py`. No other
`src/pcae` file changed. No `scripts/` file changed. No `docs/contracts/` file changed. No
`pyproject.toml` change.

## Regression evidence

- Fresh phase-specific suite (`tests/test_phase_...1_1R_configured_agent_identity_threading_repair.py`): 30/30 passed.
- Targeted 149O.20J* / topology / ACL / environment-lock suite (9 files, 481 tests): identical
  failure set to a `git stash`-reverted baseline run at `R`, except the 3 disclosed test
  reconciliations above (now passing) and one transient pre-commit `git status`-dirty check
  (`test_phase_149o_20j_8...::test_real_host_class_b_result_is_non_compliant_and_repo_unmutated`,
  resolves once this phase's commit lands — confirmed).
- Broad regression sweep (`pytest tests/ -k "149o_20j or class_b or topology or
  hatp_environment_lock or pawa or ppa or protected_presentation or rhamp or hpac_verifier or
  gate5 or gate9"`, ~41000 tests collected/deselected): zero new failures beyond the pre-existing
  baseline set, other than the same class of transient pre-commit `git status`/"no src file
  changed" point-in-time guards (14 of them) — all attributable to this phase's own still-uncommitted
  diff at scan time, none functional, all confirmed to resolve identically to how every prior
  `src/pcae/core/hatp_class_b_topology_verifier.py`-touching phase in this lineage (149O.20J.1
  through .20J.8) also transiently tripped the same class of guards mid-phase.

## No-Go confirmations

No F-5 deployment retry performed. No protected-root provisioning rerun. No helper reinstall. No
generation reset. No PPA registration. No protected-root mutation. No administrator credentials
requested. No protected human election. No YubiKey interaction. No FIDO2 PIN request. No
presentation evidence created. No PRODUCTION principal minted. No Gate 5 final certification. No
N-16-5 closure. No N-16-6/N-16-7 work. No Slice C. No runtime execution enabled. No first governed
runtime effect implemented or invoked. No FIDO2/local-TTY made globally mandatory. No mobile-only
future path foreclosed. No delegated worker performed finalization/commit/push. No raw `git
commit`/`git push`, no `--no-verify`, no force push, no history rewrite.

## Host state (read-only final check)

Confirmed unchanged from the predecessor's evidence: PAWA protected root present, generation 1,
symbolic account `atilamadai` / uid 501, helper present with SHA-256
`933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182` unchanged, PPA presentation
mechanism still absent, PPA current-generation descriptor still absent, no new partial
registration. This repair phase performed no filesystem write outside test-owned `tmp_path`
fixtures.

## Runtime (final check)

`pcae runtime inspect`: `not_implemented` / `Observed` / `observe` / execution `unavailable`; 0
plugins; 0 capabilities. First governed runtime external effect: ABSENT / UNREACHABLE (no new
`adapter.dispatch`, `DispatchEnvelope`, runtime plugin/capability, or effect path introduced or
made reachable).

## Successor

If independently confirmed, the exact next phase is:

**Independent Verification of the Configured-Agent-Identity Threading Repair for HATP Class-B
ACL / Trusted-Executable / Ancestor-Chain Verification** — must independently reconstruct the
principal semantics and consumer classification from primary source, not begun by this phase.

Only after a clean fresh repair IV may F-5 continue (retrying only the previously blocked
`hpac_protected_presentation_admin.py install` step against the *existing* generation-1
protected-root/helper state — no reprovisioning). A separate deployment-state IV is required
after that, before any real approval ceremony, before N-16-5 closure can be adjudicated.
