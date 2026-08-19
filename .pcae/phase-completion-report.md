# Phase 149O.20L.7O.2J Completion Report

**Verdict:** PREMISE FALSIFIED BY PRIMARY EVIDENCE — PROTECTED ROOT
ALREADY PROVISIONED AND VERIFIED HBDC-REQ-011..018 COMPLIANT ON
HAC-DELL — NO CREATION AUTHORIZATION ISSUED OR REQUIRED — NARROW
READ-ONLY RE-VERIFICATION ENVELOPE FROZEN — PREREQUISITE DAG CORRECTED

Authorization/planning-only phase. Independently re-derived Protected
Root's exact resolution path and full HBDC-REQ-011..021 requirement set
directly from HBDC-001 v1.2 and production source, rather than from
149O.20L.7O.2I's prose.

Discovered, from primary evidence already committed to this repository
(149O.20L.7E/7N.5/7O.2A.5/7O.2B/7O.2B.1, dated 2026-08-15 through
2026-08-18 — five real, unmocked, read-only hac-dell inspections),
that 149O.20L.7O.2I's central claim — Protected Root existence on
hac-dell is ABSENT — is false: Protected Root already exists at
`root:pcae` mode `750`, ACL `user::rwx group::r-x other::---` (no extra
grants), not a symlink, with fully safe `root:root 755` ancestors, and
already independently satisfies HBDC-REQ-011 through HBDC-REQ-018 in
full. The sole residual Class-B conformance failure on the most recent
real measurement (149O.20L.7O.2B.1, 2026-08-18) is `HBDC-REQ-042`
(`no_active_deployment_binding_matches_repository_and_root`), a
RepositoryIdentity/DeploymentBinding gap unrelated to Protected Root.

Because Protected Root requires no creation, this phase issued no
creation authorization. Instead it froze a narrow read-only
re-verification envelope (an exact `stat`/`getfacl`/`find` precheck set
with an explicit pass/fail/existing-path-state matrix) for any future
real-effect phase that relies on Protected Root's state, and corrected
149O.20L.7O.2I's prerequisite DAG: the true first unmet DAG node is now
either HMIC `CertificationRecord` creation or hardware-credential
(FIDO2) enrollment, with the choice deferred to the next phase.

11-test focused evidence suite passed. Fast_green raw comparison against
a git-stash baseline was identical (327 failed/12 errors both with and
without this phase's changes; the only delta was the 11 new passing
tests), so zero attributable regressions were introduced. HMIC-001 v1.6
(36/7) and HBDC-001 v1.2 remain byte-unchanged.

No SSH connection to hac-dell was opened. No `mkdir`/`chown`/`chmod`/
`setfacl` on hac-dell occurred. No Protected Root mutation, no `pcae`
user creation, no HMIC certification, no Trust-Enrollment record, no
DeploymentBinding, no readiness/activation change, and no Permission
Broker change occurred. Runtime remains Observed / observe / unavailable.

Recommended next phase: **149O.20L.7O.2K — HATP Prerequisite DAG
Correction and Next Real-Effect Node Selection (HMIC Certification vs.
Hardware-Credential Enrollment)** — analysis-only, not started, not
authorized.

Full detail: `docs/PHASE_149O_20L_7O_2J_HATP_CLASS_B_REAL_HOST_PROTECTED_ROOT_PROVISIONING_AUTHORIZATION.md`.
