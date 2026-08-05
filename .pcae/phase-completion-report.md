# Phase 149O.1B.1 Complete — Human Approval Bootstrap Authority Architecture

**Phase ID:** 149O.1B.1
**Mode:** Trust-boundary architecture only (Root 2B bootstrap mechanics)
**Predecessor:** 149O.1B (Human Approval Trusted Provenance Contract
Freeze — completed, HATP-001 NOT FROZEN — BOOTSTRAP / AUTHORIZATION
TRUST GAP CONFIRMED)
**Date:** 2026-08-05
**Status:** completed
**Pushed:** pending

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1B.1's job was Root 2B *mechanics*: given 149O.1B's selection
of Bootstrap Model Class B (separate OS security context) as the target
architecture, design the concrete security-principal topology,
filesystem/ownership model, and workflow set that would actually
establish it. It did not reopen the Class A/B/C bootstrap-model-class
selection 149O.1B already made, nor the Model A/B/C/D/E signer-model
comparison 149O.1A already resolved.

**Principal topology:** selected a **two-principal model** for HATP
v1 — a dedicated agent OS principal, and a combined human-approver/
bootstrap-admin OS principal — over a three-principal split, because
the governing Threat A model (an unattended software agent with no
separate secret or out-of-band human capability) gives the extra human-
side split no additional attack coverage; a three-principal split would
only reduce blast radius under Threat B (compromised human-side
context), which remains out of scope.

**Trust-store ownership model:** the HATP trust store is owned by the
human/admin OS principal, located outside the agent-writable repository
tree, with the agent principal granted read-only access to public
verification material and no write/enroll/revoke/rotate capability.
Repository-local trust configuration is explicitly prohibited as
authoritative. The agent principal is required to hold no
privilege-escalation path (`sudo`/root-equivalent) that could reach the
admin principal's security context.

**Mechanical attack proofs produced (architecture-level, not
implemented):** self-enrollment, verifier-key replacement, registry
deletion, permission-weakening, parent-directory replacement, and
environment-variable/CLI trust-store-path overrides are all shown to
terminate at an OS-permission denial once the boundary described above
actually exists — not at another self-authored repository file or a
policy convention (the mandatory root-termination statement).

**Repository-identity investigation:** searched this codebase for any
existing, stable, protected repository-identity primitive suitable as
the trust store's authority-scope anchor. Found none: every existing
`repository_identity`-named field (`src/pcae/cltr_prototype/**`,
`src/pcae/cltr/**`, repository-intelligence metadata) is a
caller-declared plain string used for an unrelated purpose, never
derived from any protected, mechanical, or hardware-anchored fact.
Flagged this as a new, narrow, **BLOCKING** prerequisite for
`HATP-001` contract freeze, rather than silently weakening
repository-specific authority to a global scope.

**Architecture verdict: HUMAN APPROVAL BOOTSTRAP AUTHORITY ARCHITECTURE
DEFINED — REPOSITORY IDENTITY PREREQUISITE REMAINS.**

No production code changed this phase (`git status --short` confirms
zero `src/pcae/**` and zero `docs/contracts/**` diff). No OS account,
ACL, or sudoers configuration was created or changed — the distinct OS
principal this architecture requires remains unprovisioned in this
repository's actual, current deployment; establishing it is deployment
work, explicitly out of this architecture-only phase's scope. B-149O-
1..4 remain OPEN, unchanged. AG3/AG5 remain unwired. RAE-001/RWMPC-001/
PBPC-001/PBPA-001/CHGR-001 all remain byte-unchanged. Fast Green: 4391
passed on stable rerun, exact match to entering baseline (one
flaked-and-passed-in-isolation result on the first parallel run,
`tests/test_backend_cli.py::TestBackendReviewCreate::
test_create_persists_to_latest`, a parallel-worker test-isolation flake
unrelated to this phase's doc-only diff, not a regression — the same
flake 149O.1B also observed and classified). Runtime remains Observed /
observe / unavailable throughout.

**Recommended next phase:** 149O.1B.2 — Canonical Repository Identity
Architecture (design, not implement, a repository-identity mechanism
suitable as the HATP trust-store's authority-scope anchor, reusing this
phase's own admin-owned/agent-unwritable trust-store boundary rather
than inventing a second protection mechanism). Only after that
architecture exists, and after the OS-principal separation this phase
requires is also actually established and independently verified,
should a later phase re-attempt `HATP-001 v1.0` freeze.

See `docs/PHASE_149O_1B_1_HUMAN_APPROVAL_BOOTSTRAP_AUTHORITY_ARCHITECTURE.md`
for the full analysis.
