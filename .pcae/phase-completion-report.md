# PCAE Phase Completion Report

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R`
- Status: **COMPLETE — CONFIGURED-AGENT-IDENTITY THREADING REPAIR IMPLEMENTED — FRESH INDEPENDENT VERIFICATION REQUIRED**
- F-5: **OPEN / BLOCKED PENDING REPAIR IV**
- N-16-5: **NOT CLOSED**

Repaired the defect the predecessor F-5 deployment-preparation retry discovered:
`_acl_grants_agent_write_linux`/`_acl_grants_agent_write_macos` already receive
the CONFIGURED PCAE agent principal's resolved `(uid, gids)` from their caller,
but resolved their own ACL-inspection tool (`getfacl`/`ls`) via the
ambient-identity `_resolve_trusted_executable` instead of that same subject —
so on the canonical root-owned registration path, root-owned owner-writable
system directories misclassified as agent-writable and every ancestor's ACL
check came back indeterminate. A new sibling primitive,
`_resolve_trusted_executable_for_subject(name, agent_uid, agent_gids)`, is now
used instead, with no ambient fallback; the original `_resolve_trusted_
executable` is left completely untouched, independently frozen by two earlier
phases' own guard tests (both reconfirmed green).

`hpac_protected_admin_writer.py`'s §33 STEP 3/7 and `hpac_foundation.py`'s
`_validate_production_boundary`/`_relative_record_path` were independently
confirmed already correctly threaded before this repair began — no change
required there; production diff confirms neither file changed.

Fresh 30-test phase-specific suite: 30 passed. Targeted 149O.20J*/topology/
ACL/environment-lock scope (9 pre-existing files + fresh suite, 511 tests):
477 passed, 33 failed — byte-identical by node id to a `git stash`-reverted
baseline run at repair-entry SHA `R`, zero attributable regression. Broad
regression sweep (~41000 collected/deselected, `149o_20j`/`class_b`/
`topology`/`hatp_environment_lock`/`pawa`/`ppa`/`protected_presentation`/
`rhamp`/`hpac_verifier`/`gate5`/`gate9` scope): zero new functional failures
beyond the pre-existing baseline.

Three pre-existing tests needed disclosed, non-weakening reconciliation — each
depended on this dev host's real Homebrew-preceding-system-tools `PATH` quirk
combined with the pre-repair ambient-identity bug to accidentally produce an
indeterminate (fail-closed) result that looked like a genuine detection. Each
was updated to mock `_effective_write_access` deterministically instead
(matching the pattern their own sibling tests already use). No `def test_`
renamed or removed; no skip/xfail added.

Production diff bounded to exactly `src/pcae/core/hatp_class_b_topology_
verifier.py`. No `scripts/`, `docs/contracts/`, or `pyproject.toml` change.
Host state (PAWA protected root, generation 1, helper bytes, PPA absence)
confirmed read-only unchanged.

Runtime remains `not_implemented / Observed / observe / unavailable`, zero
plugins/capabilities, first effect absent. N-16-6/N-16-7 untouched.

Recommended next, not begun: Independent Verification of the
Configured-Agent-Identity Threading Repair for HATP Class-B ACL /
Trusted-Executable / Ancestor-Chain Verification.

Governed push and canonical report promotion pending.
