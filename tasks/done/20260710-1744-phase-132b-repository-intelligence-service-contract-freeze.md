# Task Contract

## Task ID

20260710-1744-phase-132b-repository-intelligence-service-contract-freeze

## Title

Phase 132B Repository Intelligence Service Contract Freeze

## Status

done

## Mode

architecture

## Goal

Transform the approved 132A architecture into the authoritative implementation contract for Track 132: freeze 18 contract sections (purpose, scope, authority, consumer, lifecycle, request, response, composition, provenance, evidence, boundary, determinism, identity, failure, governance, compatibility, extensibility, versioning), perform an internal consistency review, and re-evaluate inherited technical debt without repairing. No implementation, no modification to Unified Query/Repository Intelligence/schemas/source/test code, no networking/REST/GraphQL/execution/Decision Evaluation/Permission Broker/runtime plugin changes.

## Allowed Files

- docs/PHASE_132_REPOSITORY_INTELLIGENCE_SERVICE_CONTRACT.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md

## Forbidden Files

- TBD


## Allowed Zones

- docs
- tasks

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

- Freezes purpose, scope (no hidden expansion), authority (every RI artifact and Unified Query remain authoritative/derivative; Service never becomes an evidence source), consumer (conceptual only, no integration), and lifecycle (nine stages, no hidden stages) contracts
- Freezes request (entity/artifact/scoped/composite, no schema/protocol), response (provenance/evidence/uncertainty/limitations/boundary disclosures preserved, no synthesized conclusions), composition (compose never reinterpret, deterministic), provenance (no loss, no strengthening), and evidence (unchanged, no inferred evidence) contracts
- Freezes boundary (derivative/read-only/deterministic/non-authoritative/non-executing), determinism (no entropy), identity (reuse existing resolution, no aliases/fuzzy/probabilistic/silent-merge), and failure (fail-closed, explicitly incorporating the 131F silent-omission lesson) contracts
- Freezes governance, compatibility (Tracks 119-131, consumed not redefined), extensibility, and versioning (backward compatibility unless governed breaking-change process) contracts; performs internal consistency review (authority leakage, responsibility overlap, hidden execution path, governance conflict, lifecycle ambiguity) and technical debt review without repairing
- Confirms PFN-001, no implementation occurred, no runtime behavior changed, execution remains unavailable; recommends 132C next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T17:44:41.974714+02:00
