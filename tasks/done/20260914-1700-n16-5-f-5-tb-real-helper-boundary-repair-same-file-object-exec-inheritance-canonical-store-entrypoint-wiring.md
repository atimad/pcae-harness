# Task Contract

## Task ID

20260914-1700-n16-5-f-5-tb-real-helper-boundary-repair-same-file-object-exec-inheritance-canonical-store-entrypoint-wiring

## Title

N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR: Same-File-Object Exec Inheritance + Canonical-Store Entrypoint Wiring

## Status

done

## Mode

implementation

## Goal

Repair exactly (1) the O_CLOEXEC/os.set_inheritable same-file-object-exec defect in hpac_pawa_helper_os.py::execute_verified and (2) the hpac_pawa_helper_entrypoint.main() hardcoded-ProtectedStoreFoundation wiring gap, per governed authorization for phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (alias N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR). Narrow scope only; no writer-authority contract evolution, no caller migration, no packaging/deployment.

## Allowed Files

- src/pcae/core/hpac_pawa_helper_os.py
- src/pcae/core/hpac_pawa_helper_entrypoint.py
- tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py
- tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py
- PROJECT_STATUS.md
- CHANGELOG.md
- .pcae/phase-completion-metadata.json
- .pcae/phase-completion-report.md
- .pcae/fast-green-attribution/*
- docs/PHASE_N16_5_F_5_TB_REAL_HELPER_BOUNDARY_REPAIR.md
- tasks/active/20260914-1700-n16-5-f-5-tb-real-helper-boundary-repair-same-file-object-exec-inheritance-canonical-store-entrypoint-wiring.md
- tasks/done/20260913-2050-idle-post-n16-5-f-5-tb-real-helper-store-launcher-iv-complete-not-verified-blocked-same-file-object-exec-defect-found-narrow-repair-phase-next-not-begun-n-16-5-not-closed.md

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Same-file-object fd inheritance repaired narrowly on Linux; no pathname reopen
- Real helper entrypoint wired to existing canonical-store adapter; NON_REAL profile remains explicit test-only; no caller-selectable profile/root
- Blocked write operations remain blocked; REQ-033 satisfied; no second writer mint path
- Fresh repair-IV successor derived but NOT begun

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-14T17:00:55.942254+02:00
