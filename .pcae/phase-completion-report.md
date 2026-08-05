# Phase 149O.1B Complete — Human Approval Trusted Provenance Contract Freeze

**Phase ID:** 149O.1B
**Mode:** Normative-contract freeze attempt, Root 2B (bootstrap/authorization
trust) resolution
**Predecessor:** 149O.1A (Human Approval Trusted Provenance Contract &
Trust-Boundary Architecture — completed, HUMAN APPROVAL TRUST BOUNDARY
ARCHITECTURE DEFINED — CONTRACT FREEZE REQUIRES FOLLOW-UP)
**Date:** 2026-08-05
**Status:** completed
**Pushed:** pending

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1B_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_FREEZE.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1B's job was Root 2B only: what independently protected fact
tells PCAE that a particular hardware-backed signing key belongs to a
principal authorized to approve rollback for this repository. It did not
reopen the Model A/B/C/D/E signer-model comparison 149O.1A already
resolved.

This phase investigated, with primary-source evidence rather than
architectural assumption, all three of 149O.1A's candidate
bootstrap-boundary mechanisms against this repository's actual current
deployment:

1. **Distinct OS user/principal** — confirmed absent (`whoami`/`git
   config user.email` show the agent process and the human operator both
   run as OS user `atilamadai`).
2. **External service/KMS enrollment** — confirmed absent (repo-wide
   grep for signing/hardware/credential primitives and `pyproject.toml`
   dependencies unchanged from 149O.1A; no cryptography dependency, no
   external service anywhere).
3. **External human-authenticated review gate** — this is the one
   149O.1A could not verify. This phase queried the actual GitHub
   repository directly (`gh api repos/atimad/pcae-harness/branches/main/
   protection`, `.../collaborators`, `ssh-add -l`) and found: branch
   protection exists nominally, but `enforce_admins` is `false` (the
   repository owner can push directly to `main`, exactly as this
   repository's own commit history shows), the sole collaborator is the
   repository owner (no second human account exists to be a reviewer),
   and the SSH credential used for `git push` is the same key present on
   this machine that the agent process also has access to. Mechanism 3 is
   therefore not merely unconfigured — it is **structurally insufficient**
   for this deployment.

**Bootstrap model class selected:** Class B (separate OS security
context) — a dedicated OS principal owning the trusted approver registry,
distinct from the agent's own OS principal — chosen over Class A
(hardware-mediated enrollment alone, which does not by itself answer
where the enrollment record lives) and Class C (external
registry/review-gate, rejected per finding 3 above and per the absence of
any provisioned external service). This is a selection of target
architecture, not a claim that the boundary exists today.

Because no distinct OS principal currently exists in this repository's
real deployment, the Bootstrap Trust Statement's mandatory field ("why
the autonomous agent cannot enroll itself") cannot be filled in
concretely for the current state of this repository. Per the governing
contract template's own instruction ("if any field cannot be filled
concretely: DO NOT FREEZE") and the phase's own decision rule ("if
approver authorization remains agent-writable → do not freeze"), **this
phase does not freeze `HATP-001`** and does not create
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`.

Self-enrollment and verifier-key-replacement attacks were re-analyzed
against this phase's concrete findings and confirmed **not blocked** in
the repository's current, real deployment — sharper and more conclusive
than 149O.1A's "unverified" characterization of the same gap.

**Contract freeze verdict: HATP-001 NOT FROZEN — BOOTSTRAP /
AUTHORIZATION TRUST GAP CONFIRMED, NOW WITH CONCRETE PRIMARY-SOURCE
EVIDENCE.**

No production code changed this phase (`git status --short` confirms
zero `src/pcae/**` and zero `docs/contracts/**` diff). No GitHub
repository configuration was modified — branch protection and
collaborators were inspected read-only via `gh api` only. B-149O-1..4
remain OPEN, unchanged. AG3/AG5 remain unwired. RAE-001/RWMPC-001/
PBPC-001/PBPA-001/CHGR-001 all remain byte-unchanged (headers confirmed
FROZEN this phase). Fast Green: 4391 passed on stable rerun, exact match
to entering baseline (one flaked-and-passed-in-isolation result on the
first run, `tests/test_backend_cli.py::TestBackendReviewCreate::
test_create_persists_to_latest`, a parallel-worker test-isolation flake
unrelated to this phase's doc-only diff, not a regression). Runtime
remains Observed / observe / unavailable throughout.

**Recommended next phase:** 149O.1B.1 — Human Approval Bootstrap
Authority Architecture (design, not implement, the concrete Class-B OS
security-context mechanics for this deployment: dedicated OS principal
creation, registry ownership/ACL specification, human-authentication
procedure for first enrollment). Only after that architecture is defined
and actually established/independently verified should a later phase
re-attempt `HATP-001 v1.0` freeze.

See `docs/PHASE_149O_1B_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_FREEZE.md`
for the full analysis.
