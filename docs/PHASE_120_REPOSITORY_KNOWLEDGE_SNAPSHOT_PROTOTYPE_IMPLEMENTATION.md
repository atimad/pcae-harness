# Phase 120E - Repository Knowledge Snapshot Prototype: Read-Only Generator

## 1. Implementation Overview

Phase 120E implements the first Track 120 read-only Repository
Intelligence generator: a deterministic, source-attributed Repository
Knowledge Snapshot generator that produces artifacts conforming to
`schemas/repository_intelligence/artifacts/repository_knowledge_snapshot.schema.json`.
This is intentionally the only artifact family implemented; no other
Repository Intelligence generator exists as a result of this phase.

Every boundary reaffirmed in 120A-120D is preserved: read-only,
deterministic, observe-only, no execution, no repository/runtime
mutation, no AI inference, no network access, no Advisory/Decision
Evaluation integration.

## 2. Generator Architecture

New package: `src/pcae/repository_intelligence/`

- `__init__.py` — package docstring restating the frozen boundaries.
- `source_inventory.py` — read-only source discovery (120D pipeline
  stages 1-2): deterministic git commit/branch lookup, sorted
  top-level directory listing, narrow `pyproject.toml [project]`
  field parsing, `PROJECT_STATUS.md` "## Current Phase" line reading.
  Raises `SourceInventoryError` when a required source (the git
  commit) cannot be observed.
- `attribution.py` — Source Attribution Record and Uncertainty/
  Verification State builders (120D pipeline stage 3), shaped exactly
  to `source_attribution_record.schema.json` and
  `uncertainty_verification_state.schema.json`.
- `snapshot_builder.py` — extraction, normalization, assembly, schema
  alignment, limitation/unknown capture, and boundary attachment
  (120D pipeline stages 4-9), producing the full snapshot dict.
  Raises `SnapshotGenerationError` (fail-closed) if no architectural
  entities can be observed.
- `persistence.py` — writes the completed snapshot to `latest.json`
  and a timestamped file under `snapshots/` (120D pipeline stage 10).
  Performs no reads for extraction purposes; write-only.
- `snapshot_generator.py` — the single public entry point,
  `generate_snapshot(repo_root, output_dir=None, pretty=False)`,
  orchestrating the above and returning generation metadata (not the
  snapshot content itself).

New CLI command: `src/pcae/commands/repository_intelligence.py`,
wired into `src/pcae/cli.py` as
`pcae repository-intelligence snapshot generate` (with `--output`,
`--pretty`, `--json`), following the same nested-subparser pattern
already used for `pcae backend adapter approval show` and similar
three/four-level command groups. No query, reporting, or graph
subcommand was added.

## 3. Generation Pipeline

Implements the eleven-stage pipeline planned in 120D Section 5,
collapsed into the module boundaries above:

1. **Repository source discovery** — `source_inventory.list_top_level_entries`
   for `src/pcae`, plus fixed checks for `tests/` and
   `schemas/repository_intelligence/`.
2. **Source eligibility evaluation** — only the fixed, allowed
   locations named in 120D Section 4 are read; nothing else is
   consulted.
3. **Attribution assignment** — every discovered source is wrapped in
   a `source_attribution_record` via `attribution.file_path_attribution`
   or `attribution.commit_attribution` before any claim about it is
   made.
4. **Repository knowledge extraction** — `snapshot_builder._build_architectural_entities`,
   `_build_subsystems`, `_build_knowledge_claims` apply only
   deterministic filesystem/text observation (path existence, a
   narrow `pyproject.toml` regex, a `PROJECT_STATUS.md` section
   reader) — no code execution, no AI inference.
5. **Knowledge normalization** — collections are sorted by stable
   keys (`TopLevelEntry.relative_path`, dict key sorting via
   `sorted(seen)` in `_collect_knowledge_sources`) so output order
   never depends on filesystem iteration order, per the 120D
   determinism-drift risk mitigation.
6. **Repository Knowledge Snapshot assembly** — `snapshot_builder.build_snapshot_content`
   assembles `snapshot_identity`, `snapshot_subject`, `snapshot_scope`,
   `architectural_entities`, `capabilities`, `subsystems`,
   `knowledge_relationships`, `knowledge_claims`, `knowledge_sources`.
7. **Schema alignment** — field names, `$defs` shapes, and enum
   values were verified directly against the schema file during
   implementation (Section 9 below), not assumed from 120B/120D prose.
8. **Limitation capture** — `unknowns` and `snapshot_limitations`
   arrays, plus per-record `limitations`, are populated with honest,
   specific text (Section 7).
9. **Boundary attachment** — `boundary_disclosures` and `disclaimers`
   (module-level constants in `snapshot_builder.py`) are attached
   verbatim, copied from the schema's own `const` values.
10. **Persistence** — `persistence.write_snapshot` writes both files
    only through explicit calls from `generate_snapshot`; no implicit
    or background write occurs.
11. **Human review** — out of scope for automated code; the generated
    artifact is committed through the governed PCAE lifecycle for
    human review, exactly as every other phase artifact in this
    track.

## 4. Attribution Model

Every content-bearing record (`architectural_entity`, `subsystem_summary`,
`knowledge_claim`) carries a non-empty `source_attribution` array.
Two attribution builders are used:

- `file_path_attribution` — for filesystem paths, using
  `locator_type: file_path`, `source_type: file`,
  `source_verification_state: verified` (existence, not content, was
  verified), with an explicit `source_limitations` entry disclosing
  that only existence was observed.
- `commit_attribution` — for the generation commit itself, using
  `locator_type: commit_sha`, `source_type: commit`.

`_collect_knowledge_sources` deduplicates every source used anywhere
in the snapshot (by `source_id`) into the top-level `knowledge_sources`
array (required, `minItems: 1`), and the envelope's own
`source_attribution` reuses the same deduplicated list. A fact that
cannot be attributed is never asserted: `_build_architectural_entities`
raises `SnapshotGenerationError` if the required top-level locations
yield zero entities, rather than persisting a snapshot with an empty
`architectural_entities` array (which would violate the schema's
`minItems: 1`).

## 5. Persistence Behavior

Default output location: `.pcae/repository-intelligence/` (the
location selected in 120D Section 10), overridable via `--output` for
testing and alternate deployments. Two files are written per run:

- `latest.json` — overwritten every run.
- `snapshots/<UTC-timestamp-with-microseconds>.json` — one new file
  per run, never overwritten or deleted. Microsecond precision was
  added to the filename slug (distinct from the second-precision
  `generated_at_utc` field inside the artifact) after testing showed
  two runs within the same second would otherwise collide on
  filename and silently overwrite each other's history file — an
  approved, non-substantive metadata refinement, not a change to
  the artifact's substantive content.

Both files are always byte-identical to each other for a given run
(same serialized content). Serialization is deterministic
(`json.dumps(..., sort_keys=True)`, with `--pretty` controlling only
indentation, never content or key order).

Persistence is write-only through `persistence.py`; the module never
reads an existing snapshot back for extraction, so a generator run is
never influenced by a prior run's output.

## 6. Deterministic Guarantees

Verified directly (Section 10) rather than assumed: two generator
runs against the same commit produce byte-for-byte identical output
once `envelope.generated_at_utc` and
`snapshot_identity.snapshot_created_at_utc` are excluded — the only
two approved non-substantive metadata fields, per 120B Section 6.
`artifact_id` and `snapshot_id` are themselves derived deterministically
from the commit SHA (`repository_knowledge_snapshot:<sha>`,
`rks-<sha>`), not from a random UUID, so they are also stable across
runs at a fixed commit. No probabilistic reasoning, sampling, or AI
inference exists anywhere in the pipeline.

## 7. Boundary Guarantees

- **Read-only**: the package contains no file-write call outside
  `persistence.write_snapshot`, and that call only ever writes to the
  generator's own designated output directory.
- **No execution**: the only `subprocess` calls in the package are
  read-only `git` invocations (`rev-parse HEAD`, `branch
  --show-current`) in `source_inventory.py`, matching the same
  pattern already used throughout `src/pcae/core/` (e.g.
  `memory_snapshot.py`, `architecture.py`) for read-only git
  metadata lookups — not new shell-mediation capability.
- **No AI inference / no network access**: no HTTP client, model
  client, or external API call exists anywhere in the package.
- **No Advisory / Decision Evaluation integration**: no import of, or
  reference to, any Advisory or Decision Evaluation module exists in
  the package.
- **Fail-closed**: `SnapshotGenerationError` is raised, and nothing is
  persisted, if the git commit cannot be determined or if zero
  architectural entities can be observed — verified by
  `test_invalid_input_handling_non_git_directory` and
  `test_fail_closed_no_persistence_on_failure`.

## 8. Limitations

This is an intentionally narrow first prototype:

- `capabilities` and `knowledge_relationships` are always empty
  arrays; this prototype does not yet extract capability or
  relationship data. Both omissions are explicitly declared in the
  snapshot's `unknowns` array rather than silently left unexplained.
- Only a fixed set of top-level locations is observed (`src/pcae`
  direct children, `tests/`, `schemas/repository_intelligence`,
  `pyproject.toml`, `PROJECT_STATUS.md`). No recursive directory
  traversal, file-content parsing, import analysis, or symbol
  extraction is performed.
- `subsystems` covers only two directories
  (`schemas/repository_intelligence` classified `schema`, `docs`
  classified `documentation`) using directory-name-based
  classification, not semantic analysis.
- Evidence integration is a single `evidence_gap_marker` at the
  envelope level; no real Evidence subsystem link exists (correctly,
  since this prototype does not integrate with Evidence).

All of the above are declared in the artifact itself
(`unknowns`, `snapshot_limitations`, per-record `limitations`), not
silently omitted.

## 9. Schema Verification Performed During Implementation

Before writing the generator, the actual on-disk schema files were
read directly (not trusted from 120B/120D prose) to confirm exact
field names, `required` arrays, and enum values, including the
`unknowns` (not `unknowns_gaps`) field-name clarification already
flagged in 120C. This confirmed:

- `repository_knowledge_snapshot.schema.json`'s 16 top-level required
  fields, its ten `$defs` (`snapshot_identity`, `architectural_entity`,
  `entity_type`, `capability_summary`, `subsystem_summary`,
  `knowledge_relationship`, `knowledge_claim`, `command_surface`,
  `contract_reference`, `documentation_reference`, `ownership_marker`).
- `common_artifact_envelope.schema.json`'s 20 required fields,
  including the exact `read_only_boundary`, `decision_boundary`, and
  `execution_boundary` const strings, copied verbatim into
  `snapshot_builder.py`.
- `boundary_disclosure.schema.json`'s nine required boolean-`true`
  fields, `disclaimer.schema.json`'s five required const strings, and
  `source_attribution_record.schema.json`'s / `evidence_link_record.schema.json`'s
  / `limitation_record.schema.json`'s / `uncertainty_verification_state.schema.json`'s
  required fields and enum values — all copied verbatim, not
  paraphrased.

## 10. Future Extension Points

Explicitly deferred, consistent with 120D Section 17 and this phase's
own strict non-goals — none implemented here:

- capability extraction (populating the `capabilities` array)
- relationship extraction (populating `knowledge_relationships`)
- recursive/deeper source parsing (imports, symbols, test coverage)
- additional artifact families (Historical Memory Snapshot,
  Dependency Knowledge Graph Snapshot, Change Impact Report, Advisory
  Intelligence Context Package, Query Result, Repository Intelligence
  Package)
- a conformant JSON Schema validator (this phase's tests use the same
  scripted `required`/`additionalProperties` structural checks used
  throughout 119/120, not a full validator)
- a query or reporting command surface
- any execution capability

Any of the above requires its own new, separately scoped contract
phase, per 120B Section 3/18.

## 11. Known Inherited Issues

Carried forward, unchanged in classification, from 119AC/120A/120B/120C/120D:

- **119Q report-generation-ordering defect**: non-blocking.
- **`is_phase_id_backward()` phase-id comparison bug**: non-blocking
  for 120E; should still be tracked before a letter-length transition
  occurs within the 120 series.
- **Recurring `report_notification_tests: pending_final_telegram_delivery`
  reporting detail**: non-blocking, well-understood, and consistently
  handled.

None of these three issues is repaired by this phase.

## 12. Recommended Next Phase

Recommended next phase:

`120F - Repository Knowledge Snapshot Prototype Verification`

Reason: the generator is implemented, its output structurally
validated against the frozen schema, its determinism verified, and
its boundaries confirmed by focused tests. 120F should now
independently verify this implementation against the full acceptance
criteria set in 120D Section 15, exactly as 120C independently
verified the 120B contract before implementation began.
