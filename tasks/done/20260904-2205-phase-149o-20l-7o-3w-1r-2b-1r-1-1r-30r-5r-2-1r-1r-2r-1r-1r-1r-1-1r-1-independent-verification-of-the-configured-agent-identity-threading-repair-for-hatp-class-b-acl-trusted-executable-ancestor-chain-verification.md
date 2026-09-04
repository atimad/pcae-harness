# Task Contract

## Task ID

20260904-2205-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-1r-1-1r-1-independent-verification-of-the-configured-agent-identity-threading-repair-for-hatp-class-b-acl-trusted-executable-ancestor-chain-verification

## Title

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1: Independent Verification of the Configured-Agent-Identity Threading Repair for HATP Class-B ACL / Trusted-Executable / Ancestor-Chain Verification

## Status

done

## Mode

implementation

## Goal

Independently verify (verification-only) the configured-agent-identity threading repair in src/pcae/core/hatp_class_b_topology_verifier.py from commits 8407dd24/8521b9c0 (predecessor phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R). Must independently reconstruct consumer inventory/classification, prove no root bypass/allowlist, prove ACL/mode/group/ancestor/PATH semantics correct, prove no arbitrary subject substitution, adjudicate VERIFIED/NOT VERIFIED and F-5 continuation readiness. No production repair, no F-5 continuation, no host mutation, no protected-root/PPA action, no human/YubiKey ceremony in this phase.

## Allowed Files

- src/pcae/core/hatp_class_b_topology_verifier.py
- src/pcae/core/hpac_foundation.py
- tests/**
- docs/**
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/**
- .pcae/**

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

- Repair independently classified VERIFIED or NOT VERIFIED with full consumer inventory and evidence
- No production source modified
- No host/protected-root mutation performed

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-09-04T22:05:54.641782+02:00
