# Task Contract

## Task ID

20260710-1738-phase-132a-repository-intelligence-service-architecture

## Title

Phase 132A Repository Intelligence Service Architecture

## Status

done

## Mode

architecture

## Goal

Design the internal Repository Intelligence Service architecture: an internal, governed, read-only consumption layer over Unified Query (not REST/HTTP/networking/RPC/external API/dashboard). Define purpose, PCAE layering position, responsibilities and prohibitions, consumer model (Advisory/Repository Skills/CLI tooling/reporting/future services), conceptual service lifecycle (9 stages), conceptual request/response models (no schema), authority model, relationship to Unified Query (compose/normalize/present vs locate/correlate/aggregate/expose/reference), determinism, failure model, governance guarantees, extensibility strategy, and the Track 132 roadmap. Architecture only -- no implementation, no schema changes, no runtime behavior changes.

## Allowed Files

- docs/PHASE_132_REPOSITORY_INTELLIGENCE_SERVICE_ARCHITECTURE.md
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

- Defines purpose (why Unified Query alone is insufficient for higher-level consumers), PCAE architectural layering (Repository -> Repository Intelligence -> Unified Query -> Repository Intelligence Service -> Consumers), and responsibilities/prohibitions (compose/normalize/present/preserve governance guarantees; never create knowledge/become authoritative/reason/infer/recommend/rank/evaluate/authorize/mutate/execute)
- Defines consumer model (Advisory, Repository Skills, CLI tooling, Reporting, future internal services), conceptual 9-stage service lifecycle, and conceptual request/response models (entity/artifact/scoped/composite requests; complete Repository Intelligence package response) with no schema
- Defines authority model (derivative, read-only, non-authoritative, never supersedes artifacts), relationship to Unified Query (Service consumes but never replaces it), determinism guarantees, and fail-closed failure model (unresolved entity, unsupported request, unavailable/incompatible artifact, ambiguous request)
- Defines governance guarantees (observe-only, execution unavailable, auditability, explainability, reproducibility, provenance, evidence, PFN-001), extensibility strategy, strict non-goals (no networking/REST/GraphQL/HTTP/dashboards/execution/Decision Evaluation changes/Permission Broker changes/runtime plugins), and the Track 132 roadmap (132A-132F)
- Confirms PFN-001, no implementation occurred, no runtime behavior changed, execution remains unavailable; recommends 132B next

## Acceptance Checks

- TBD

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-10T17:38:57.800465+02:00
