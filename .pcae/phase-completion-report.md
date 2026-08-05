# Phase 149O.1A Complete — Human Approval Trusted Provenance Contract & Trust-Boundary Architecture

**Phase ID:** 149O.1A
**Mode:** Human-approval trust-boundary architecture plus normative contract
design (contract freeze deferred — architecture resolved, one load-bearing
bootstrap decision remains)
**Predecessor:** 149O.1 (RAE Trusted Provenance Root Hardening — completed,
TRUSTED PROVENANCE ROOT NOT ACHIEVABLE — CURRENT TRUST MODEL INSUFFICIENT)
**Date:** 2026-08-05
**Status:** completed
**Pushed:** pending

This is the lightweight staging header for `pcae phase complete`. The
full document
(`docs/PHASE_149O_1A_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_AND_TRUST_BOUNDARY_ARCHITECTURE.md`)
is the canonical artifact of this phase.

---

## Executive Summary

Phase 149O.1A independently re-verified 149O.1's trust inventory
(`PublicationCoordinator.authorize()`/`execute()`, `acquire_agent_lock()`,
a repo-wide grep for signing/hardware/credential primitives, and
`pyproject.toml` dependencies) from primary source, finding no
discrepancy with 149O.1's summary.

It confirmed, by reading RAE-001 §22/§6 directly, that RAE-001 threat #2
("Agent-generated fake approval JSON," citing RAE-REQ-018) makes a
genuine technical claim distinct from threat #3's already-disclosed
identity gap, and found no primary-source contradiction licensing a
downgrade to procedural-only provenance.

It evaluated five candidate trust models (A: hardware-backed external
signing key; B: OS keychain with fresh per-use presence; C: external
approval service; D: separate local privileged approver; E:
procedural-only) against the mandatory dual-attack acceptance model,
self-enrollment attack, and verifier-key-replacement attack, and selected
**HATP MODEL A** for Root 1 (proof-production): a hardware security
device whose firmware enforces a fresh physical touch per signing
operation, which the autonomous agent cannot satisfy regardless of this
repository's lack of OS-level human/agent separation.

Root 2 (verification/bootstrap) splits into two sub-facts: device
genuineness (resolved — a fixed, externally-published vendor attestation
root) and approver-authorization mapping (**unresolved** in this
repository's actual current deployment — no OS-user separation, no
verified external service, no verified external review gate exists
today). Per the governing phase prompt's own decision rule ("If
proof-production root is strong but verifier/bootstrap root remains
agent-writable → do not freeze"), this phase does **not** freeze
`HATP-001` and does not create a contract file.

The full architecture document specifies the required proof payload
(bound to Decision digest, Binding digest, AG3/AG5 operation identity,
approver principal, `issued_at`, proof version), the trust capability
matrix, layering compatibility (RAE-001/CHGR-001/IWC-001/AESIC-001/
PBPC-001/PBPA-001 all `COMPATIBLE AS-IS`, unamended), and thirteen future
acceptance tests for the eventual implementation phase.

**Architecture verdict: HUMAN APPROVAL TRUST BOUNDARY ARCHITECTURE
DEFINED — CONTRACT FREEZE REQUIRES FOLLOW-UP.**

No production code changed this phase (`git status --short` confirms
zero `src/pcae/**` diff). B-149O-1..4 remain OPEN, unchanged. AG3/AG5
remain unwired. RAE-001/RWMPC-001/PBPC-001/PBPA-001/CHGR-001 all remain
byte-unchanged. Fast Green: 4391 passed, exact match to entering
baseline. Runtime remains Observed / observe / unavailable throughout.

**Recommended next phase:** 149O.1B — Human Approval Trusted Provenance
Contract Freeze (select and independently verify exactly one bootstrap-
boundary mechanism for Root 2, then freeze `HATP-001 v1.0`).

See `docs/PHASE_149O_1A_HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT_AND_TRUST_BOUNDARY_ARCHITECTURE.md`
for the full architecture.
