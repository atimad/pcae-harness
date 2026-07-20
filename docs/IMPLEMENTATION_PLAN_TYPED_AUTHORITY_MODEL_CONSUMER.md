# Implementation Plan: Typed Authority Model Production Consumer

## Plan identity and status

**Plan:** IPTAMC-001
**Version:** 1.0
**Status:** Planning artifact — governs Phase 137K (implementation) and
137L (independent verification).
**Governed by:** TAMPC-001 v1.0 (`docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`),
FROZEN, independently verified VERIFIED AFTER REPAIR by Phase 137I
(`docs/PHASE_137I_TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT_INDEPENDENT_VERIFICATION.md`).
**Architectural basis:** Phase 137G
(`docs/PHASE_137G_TYPED_AUTHORITY_MODEL_PROTOTYPE_REVIEW_AND_PRODUCTION_INTEGRATION_ARCHITECTURE.md`).
**Reference implementation (non-authoritative, structurally instructive
only):** `prototypes/typed_authority_inspector.py`, independently verified
by Phase 137F/137F.1V.

This document is a plan. It authorizes nothing by itself. It does not
create, modify, or import `src/pcae/cltr/authority_inspection.py`,
`src/pcae/commands/authority_inspect.py`, any CLI registration, any Stage 3
artifact, TAMC-001, TAMP-001, TAMPC-001, or the Phase 137E prototype. No
production behavior changes. No CLI command is registered. No runtime
capability changes.

Runtime posture, unaffected by this plan:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

Where this plan and TAMPC-001 differ in force, TAMPC-001 is normative
(TAMPC-001 §0, restated). This plan does not reinterpret an ambiguity in
TAMPC-001; none was found during planning (Section 21 confirms this
explicitly). If Phase 137K discovers an ambiguity TAMPC-001 does not
resolve, TAMPC-REQ-177 requires returning to a dedicated contract-repair
phase before proceeding past the ambiguous point — this plan does not
pre-empt that requirement.

---

## 1. Implementation Scope

### Exact deliverable

One production CLI command, `pcae authority inspect <path> [--json]`
(TAMPC-REQ-013), implemented across exactly two new production modules and
one CLI-registration edit:

- `src/pcae/cltr/authority_inspection.py` — orchestration (TAMPC-REQ-021).
- `src/pcae/commands/authority_inspect.py` — CLI wiring (TAMPC-REQ-022).
- `src/pcae/cli.py` — a new top-level `authority` subparser group with
  exactly one subcommand, `inspect` (TAMPC-REQ-014).

### Explicit non-goals (restating TAMPC-001 §3, binding on 137K)

- No second production consumer, generic multi-consumer framework, or
  plugin-style family-dispatch registry (TAMPC-REQ-008).
- No ambient repository scanning, artifact discovery, or "latest" record
  resolution (TAMPC-REQ-009).
- No authority or lifecycle-state inference (TAMPC-REQ-010).
- No lifecycle mutation, authority activation, runtime-capability
  activation, execution, publication, recovery, rollback, cutover,
  compatibility execution, or quarantine execution (TAMPC-REQ-011).
- No notification dispatch, automatic repair, persistence, semantic
  decision, remote-artifact retrieval, or network access (TAMPC-REQ-012).

### Implementation boundaries

Dependency direction is fixed and one-way (TAMPC-REQ-025):

```
src/pcae/commands/authority_inspect.py
        |
        v
src/pcae/cltr/authority_inspection.py
        |
        v
pcae.schema_runtime.*  (parser, registry, manifest, validator)
        |
        v
pcae.cltr.authority.*  (typed models, serialization)
        |
        v
standard library only
```

No Stage 3 module, lifecycle module, or runtime module may import either
new module (TAMPC-REQ-026). No module other than
`src/pcae/commands/authority_inspect.py` and test modules may import an
internal (leading-underscore) name from `authority_inspection.py`
(TAMPC-REQ-024).

### Expected repository changes

| File | Change | Governed by |
|---|---|---|
| `src/pcae/cltr/authority_inspection.py` | New file | TAMPC-REQ-021 |
| `src/pcae/commands/authority_inspect.py` | New file | TAMPC-REQ-022 |
| `src/pcae/cli.py` | New `authority` subparser group (one `inspect` subcommand) | TAMPC-REQ-014 |
| `tests/test_authority_inspect_137k.py` (or equivalent fresh name, 137K's choice) | New file, freshly authored fixtures (TAMPC-REQ-168) | TAMPC-REQ-167 |
| `docs/COMMANDS.md` | Regenerated (existing repository convention for every new CLI surface, confirmed by grep of prior phases' `PROJECT_STATUS.md` entries, e.g. Phase 52N/52M) | Packaging/documentation convention, not a TAMPC requirement |
| `docs/PHASE_137K_*.md`, `docs/PHASE_137L_*.md` | New phase-report docs (137K, 137L's own governed artifacts) | Standard governed-phase convention |
| Traceability matrix document (137K deliverable, Section 16) | New file | TAMPC-REQ-170 |

### Expected production modules

Confirmed: the only new production modules are exactly

```
src/pcae/cltr/authority_inspection.py
src/pcae/commands/authority_inspect.py
```

No additional production package is justified. `src/pcae/cli.py` is
edited, not created. No new package directory, no new `pcae.cltr.authority.*`
family module, no new `pcae.schema_runtime` module, and no new
`pcae.schema_resources` resource are required — every dependency this
consumer needs already exists and is frozen (TAMPC-REQ-027).

---

## 2. Requirement Traceability

Every TAMPC-001 requirement is mapped to an owning module/function,
expected verification, and expected test evidence. Requirements sharing an
identical owner and test story are grouped into rows; every requirement ID
still appears at least once so none is ownerless.

Legend for "owning function": `iaap` = `inspect_artifact_at_path`
(the public orchestration entry point, Section 5); `_read` = the private
bounded-read helper; `_dispatch` = the private family dispatch table;
`_provenance` = the private provenance assembler; `_render`/`main` = the
CLI layer functions in `authority_inspect.py`.

| TAMPC-REQ | Owning module | Owning function | Verification | Unit test | Integration test | Negative test | Doc evidence |
|---|---|---|---|---|---|---|---|
| 001–003 | N/A (scope/authorization statements) | N/A | Static reading of this plan and TAMPC-001 | — | — | — | This document, Section 19 |
| 004, 008, 016, 017, 174, 175 | `cli.py` | subparser registration | Static scan: exactly one `authority` group, one `inspect` subcommand, no alias | `test_cli_authority_registration` | `test_no_second_consumer_reachable` | `test_unknown_authority_flag_rejected` | Traceability matrix |
| 005, 029–031 | `authority_inspect.py` | `main`/argparse config | argparse contract test | `test_requires_path_positional` | CLI invocation test | `test_missing_path_exits_usage_error` | Traceability matrix |
| 006, 007, 055–057 | `authority_inspection.py` | `_dispatch` (module-level dict) | Static count of 16 keys; equality against TAMPC-REQ-007's list | `test_dispatch_table_has_sixteen_families` | one fixture per family (16x) | `test_unknown_family`, `test_missing_record_type`, `test_non_string_record_type` | Traceability matrix |
| 009–012 | `authority_inspection.py`, `authority_inspect.py` | whole module (absence property) | Static import-scan test (no forbidden import) | `test_no_forbidden_imports` (AST-based) | — | — | Traceability matrix |
| 013–015, 018–020 | `cli.py`, `authority_inspect.py` | argparse config | Help-text snapshot test | `test_help_text_contents` | `pcae authority --help`, `pcae authority inspect --help` smoke | `test_extra_positional_rejected` | Traceability matrix |
| 021–028 | `authority_inspection.py` | module-level `__all__`/imports | Static AST scan of imports and public names | `test_public_api_surface` (exact `__all__` match) | — | `test_internal_name_not_importable_externally` (via `pcae.commands` scan) | Traceability matrix |
| 029–038 | `authority_inspect.py` | `_read` | Fresh adversarial fixtures per TAMPC-REQ-168 | `test_missing_path`, `test_directory_path`, `test_symlink_to_missing`, `test_unreadable_file`, `test_empty_file`, `test_oversized_file`, `test_toctou_no_reread` | — | Each maps 1:1 to its failure category | Traceability matrix |
| 039–047 | `authority_inspection.py` (via `pcae.schema_runtime.parse_strict_json`) | `iaap` (parse step) | Reuse of frozen Stage 3 parser; no new parser | `test_non_utf8`, `test_duplicate_key`, `test_trailing_data`, `test_non_object_top_level` | — | Each → `malformed_artifact` | Traceability matrix |
| 048–053, 158, 161 | `authority_inspection.py` | `iaap` (resource resolution step, via `cltr_cutover_root()`) | Static scan: no caller-suppliable resource path; live resolution against installed package | `test_resolves_installed_manifest` | wheel/sdist/editable install tests (Section 11) | `test_corrupted_manifest_fails_closed`, `test_missing_packaged_resource_fails_closed` | Traceability matrix |
| 054–060 | `authority_inspection.py` | `iaap` (family + manifest-entry resolution) | Live check against current `manifest.json` | `test_manifest_one_entry_per_family` (TAMPC-REQ-059's dedicated regression test) | — | `test_schema_id_mismatch_family_identity_mismatch` | Traceability matrix |
| 061–064 | `pcae.schema_runtime.validate_record_shape` (schema); each `Family.from_dict` (model); `authority_inspection.py` (round trip) | `iaap` | Distinct-outcome assertions | `test_schema_and_model_validation_distinct_keys` | — | `test_semantic_lifecycle_governance_always_not_performed` | Traceability matrix |
| 065–074 | `authority_inspection.py`, `pcae.cltr.authority.*` | `iaap` | Reuse of frozen Stage 3 owners only | `test_schema_version_mismatch`, `test_model_version_mismatch`, `test_unknown_field_rejected_or_preserved_per_schema`, `test_missing_required_field`, `test_extension_field_copied_verbatim`, `test_no_type_coercion` | — | `test_lossless_roundtrip_failure` | Traceability matrix |
| 075–080 | `authority_inspection.py` | `InspectionObservation`, `InspectionFailure` dataclasses | Mutation-attempt test | `test_frozen_setattr_raises`, `test_frozen_delattr_raises`, `test_no_mutable_alias_returned` | — | `test_ordinary_assignment_blocked` (TAMPC-REQ-078) | Traceability matrix |
| 081–083 | `authority_inspection.py` | `iaap` (meaning contract) | Documentation + disclosure-default test | `test_disclosure_present_on_success_and_failure` | — | `test_disclosure_is_dataclass_default_not_computed` | Traceability matrix |
| 084–086 | `authority_inspection.py` | `_provenance` | Field-by-field table test (Section 8) | 11 field-presence tests (one per Section 14 table row) | full-record fixture per family | `test_no_provenance_field_silently_dropped` | Traceability matrix |
| 087–092 | `authority_inspection.py` | `_provenance` (digest) | Digest derivation test | `test_input_digest_sha256_of_exact_bytes`, `test_declared_vs_input_digest_never_merged` | — | `test_toctou_digest_reflects_only_bytes_read` | Traceability matrix |
| 093–106 | `authority_inspect.py` | `_render` | Output-parity test (human vs `--json`) | `test_json_output_sorted_keys_indent_2`, `test_human_output_fixed_field_order`, `test_absent_optional_field_shows_unavailable_sentinel` | golden-output regression per family | `test_human_and_json_field_parity` | Traceability matrix |
| 107–111 | `authority_inspection.py` | `iaap` (failure dispatch) | One fixture per failure category (14 categories) | 14 category tests | — | `test_failure_precedence_order` (multi-defect fixture) | Traceability matrix |
| 112–116 | `authority_inspect.py` | `main` | Exit-code test | `test_exit_0_on_inspected`, `test_exit_1_on_any_failure`, `test_argparse_usage_exit_code` | — | `test_no_exception_traceback_leaked` | Traceability matrix |
| 117–120 | `authority_inspection.py` | `iaap` | Repeated-invocation equality test | `test_repeated_invocation_identical_output` | — | `test_two_paths_same_content_identical_except_identity` | Traceability matrix |
| 121–122 | `authority_inspection.py` | `iaap` | Process-isolation test (fresh subprocess per invocation) | `test_no_cache_across_invocations` | — | — | Traceability matrix |
| 123–124 | `authority_inspection.py`, `authority_inspect.py` | whole module | Side-effect test (filesystem snapshot before/after) | `test_no_file_written`, `test_no_env_mutation` | `pcae health`/`pcae check` unchanged before/after | — | Traceability matrix |
| 125–139 | `authority_inspect.py`, `authority_inspection.py` | `_read`, `iaap` | Security fixture suite (Section 9) | see Section 9 below | — | see Section 9 below | Traceability matrix |
| 140–142 | `authority_inspection.py`, `authority_inspect.py` | whole module (absence property) | Static import-scan (`pcae.core.tasks`, `pcae.core.session`, phase-report, notification modules absent) | `test_no_lifecycle_import` | `pcae health`/`check`/`status coherence`/`doctor task-memory` unchanged | — | Traceability matrix |
| 143–145 | `authority_inspection.py`, `authority_inspect.py` | whole module (absence property) | Static import-scan (`runtime_introspection`, `runtime_snapshot`, `RuntimeRegistry`, `PermissionBroker` absent) | `test_no_runtime_import` | `pcae runtime inspect` output identical before/after | — | Traceability matrix |
| 146–147 | `authority_inspection.py`, `authority_inspect.py` | `iaap`, `_render` | Adversarial authority-claim test | `test_forged_is_authoritative_true_rejected_by_schema` | — | `test_no_output_field_reads_as_authority_signal` | Traceability matrix |
| 148–155 | `authority_inspection.py` | module constants | Literal-equality test | `test_supported_versions_pinned`, `test_consumer_id_literal` | — | `test_unknown_future_version_rejected` | Traceability matrix |
| 156–162 | packaging (`pyproject.toml`, unchanged) | N/A | Build + install test | `test_wheel_contains_new_modules`, `test_sdist_contains_new_modules` | editable/wheel/sdist install + run (Section 11) | `test_import_has_no_side_import` | Traceability matrix |
| 163–166 | development process | N/A | Interpreter-provenance confirmation (Section 20) | — | — | — | This document, Section 20; 137K/137L session logs |
| 167–169 | test suite | N/A | Fresh-fixture authorship confirmation | Every test in this table | — | — | Traceability matrix |
| 170–172 | 137K deliverable | N/A | Matrix completeness scan (all 178 IDs present) | — | — | — | 137K's own traceability matrix document |
| 173, 176–178 | this plan, 137H, 137I | N/A | Precondition confirmation (Section 21) | — | — | — | This document, Section 21 |

No TAMPC-001 requirement ID from 001 through 178 is left without an
assigned owner, verification method, and test category above.

---

## 3. Module Design — `src/pcae/cltr/authority_inspection.py`

Responsibilities only; no implementation is produced by this plan.

- **Orchestration.** One function, `inspect_artifact_at_path`, drives the
  fixed nine-stage pipeline (Section 6) end to end and returns exactly one
  `InspectionOutcome` value. It performs no I/O itself beyond what Section
  6 assigns to this layer (resource resolution); the artifact bytes
  themselves are supplied by the caller per TAMPC-REQ-021's ownership split
  described in Phase 137G §6 ("Artifact loading ... `authority_inspect.py`
  (CLI layer) reads the file; `authority_inspection.py` receives bytes plus
  the resolved path identity"). This plan fixes that split as binding:
  `authority_inspect.py` performs the bounded read (Section 6, Stage 1);
  `authority_inspection.py` receives the resulting `bytes` (or the failure
  already classified by the read) and owns every stage from parsing
  onward.
- **Validation ordering.** Enforces the exact TAMPC-REQ-111 precedence:
  input checks (owned by the CLI layer before this function is even
  called) → parse → registry resolution → manifest verification → family/
  version/identity resolution → schema validation → model validation →
  lossless round-trip. No stage is reordered, parallelized, or
  short-circuited out of this order.
- **Provenance generation.** A private `_provenance_bundle`-equivalent
  helper (module-private, TAMPC-REQ-023) assembles the Section 14/TAMPC §14
  provenance table from the successfully constructed typed model, mirroring
  the prototype's `_provenance_bundle` in shape (`origin`, identity fields,
  `copied_provenance_values`, `complete_typed_record_claims`, `derivation`,
  `authority_neutrality`) but sourcing `origin`/`source_location` from the
  CLI-supplied path rather than a caller-supplied `ExplicitArtifactContext`
  (which does not exist in production — Section 5, TAMPC-REQ-049).
- **Model construction.** Delegates to the resolved family's own
  `from_dict`; never constructs a model directly from a raw dict without
  going through the dispatch-resolved class.
- **Immutable observation construction.** Assembles `InspectionObservation`
  or `InspectionFailure` (Section 7) as the function's only return values,
  via the module's own construction path — never via an intermediate
  mutable dict that outlives the function.
- **Renderer invocation.** None — rendering is explicitly out of this
  module's scope (Section 4); `authority_inspection.py` returns a value,
  `authority_inspect.py` renders it. TAMPC-REQ-025's dependency direction
  forbids the reverse.
- **Failure translation.** Every reachable exception from a Stage 3 owner
  (`SchemaRegistryError`, `ManifestIntegrityError`, `TypedModelError`,
  `OSError` from resource resolution) is caught inside this module and
  translated to the matching `InspectionFailure` category (Section 8);
  none propagates to the CLI layer as a raw exception (TAMPC-REQ-116).

Module-private helpers (leading underscore, TAMPC-REQ-023):
family-dispatch dict, provenance assembler, and any bounded-parsing helper
this module itself needs beyond what `authority_inspect.py` already
performed. No other module may import these (TAMPC-REQ-024).

---

## 4. CLI Design — `src/pcae/commands/authority_inspect.py`

- **Argument parsing.** Registered from `src/pcae/cli.py` following the
  existing nested-subparser convention already used for `pcae cltr shadow`
  (`src/pcae/cli.py` lines ~10515–10557): a new `authority_parser =
  subparsers.add_parser("authority", ...)`, `authority_subparsers =
  authority_parser.add_subparsers(dest="authority_command", required=True)`,
  and exactly one `inspect_parser = authority_subparsers.add_parser("inspect", ...)`
  with one required positional `path` and one optional `--json` flag
  (`action="store_true"`), matching `cltr_shadow_status_parser`'s existing
  `--json` pattern exactly. `inspect_parser.set_defaults(handler=run_authority_inspect)`.
- **Output selection.** A private `_render(observation_or_failure, *,
  as_json: bool) -> None` function, structurally parallel to
  `cltr_shadow.py`'s `_print` helper: `--json` → `json.dumps(payload,
  indent=2, sort_keys=True, default=str)` (TAMPC-REQ-094); default →
  fixed-field-order human-readable text (TAMPC-REQ-095), never Python dict
  iteration order.
- **Exit handling.** `run_authority_inspect(args) -> int` performs the
  bounded read (Section 6, Stage 1 — this is the CLI layer's one
  filesystem responsibility per Section 3's ownership split), calls
  `inspect_artifact_at_path`, renders the result, and returns `0` if the
  outcome is `InspectionObservation` (`outcome: "inspected"`), else `1`
  (TAMPC-REQ-112–113). argparse's own usage-error path (missing `path`,
  unknown flag) exits with argparse's existing code (conventionally `2`,
  TAMPC-REQ-114) without this function ever being called.
- **CLI responsibility boundary.** `authority_inspect.py` contains no
  business logic beyond: reading bytes from the one supplied path (with
  the Section 6 Stage 1 fail-closed checks), calling
  `inspect_artifact_at_path`, and rendering/exiting. Every classification
  decision (family resolution, validation, provenance) happens inside
  `authority_inspection.py`. This mirrors `cltr_shadow.py`'s existing
  discipline of calling into `pcae.cltr.inspection` for all substantive
  logic.

---

## 5. Public API

Frozen per TAMPC-REQ-023:

```python
def inspect_artifact_at_path(
    path: Path, *, json_output: bool
) -> "InspectionOutcome": ...
```

- **Parameters.** `path: Path` — the one caller-supplied artifact path,
  already resolved by the CLI layer's bounded read (the function receives
  either the read bytes via a second, currently-unstated parameter, or the
  CLI layer's already-classified failure; 137K must decide the exact
  calling convention consistent with TAMPC-REQ-021's ownership split and
  document it in the traceability matrix — this plan does not fix a
  parameter beyond what TAMPC-REQ-023 already fixes verbatim, since
  inventing one would be local reinterpretation of an ambiguity TAMPC-001
  itself leaves to the implementation's own internal wiring, not a
  contract-level concern). `json_output: bool` — selects nothing about
  *content* (TAMPC-REQ-105 requires field parity); it exists only so a
  future internal caller (none exists today) could request the same
  outcome value regardless of rendering, though in 137K's actual call
  graph `authority_inspect.py` always renders itself and this flag may be
  unused by `iaap`'s own logic — 137K must confirm at implementation time
  whether `json_output` affects `iaap`'s return value at all (TAMPC-001
  does not require it to) and, if not, treat it as accepted-but-inert
  exactly as declared by TAMPC-REQ-023's fixed signature.
- **Return model.** `InspectionOutcome = Union[InspectionObservation,
  InspectionFailure]` (TAMPC-REQ-023). Exactly one of the two, never a
  third state (TAMPC-REQ-105).
- **Exceptions.** None escape `inspect_artifact_at_path` under normal
  operation; every reachable Stage 3 exception is caught and translated
  (TAMPC-REQ-116). A programming defect (e.g. `TypeError` from a truly
  malformed internal call) is not a contract-governed outcome and is out
  of TAMPC-001's scope to specify — 137K's tests target only the
  documented exception classes named in Section 2 of this plan.
- **Deterministic guarantees.** Identical bytes at an identical installed
  `pcae` version produce semantically identical output on every call
  (TAMPC-REQ-117–120).
- **Ownership.** `authority_inspection.py` owns this function exclusively;
  no other module redefines or wraps it under a different name.

---

## 6. Validation Pipeline

The precise execution sequence, extending the prototype's data flow
(Phase 137G §7) with the two new filesystem-boundary stages a real path
argument requires:

```
Stage 1 — bounded artifact read (authority_inspect.py)
  in:  caller-supplied path string
  out: bytes, or a classified read failure
  failures: input_not_found, input_not_a_file, input_unreadable,
            malformed_artifact (oversized, checked via stat before open)
  owner: authority_inspect.py (CLI layer; Section 3's fixed split)

        |
        v

Stage 2 — strict JSON parse (pcae.schema_runtime.parse_strict_json)
  in:  bytes
  out: dict, or malformed_artifact
  owner: schema_runtime (frozen, reused unchanged)

        |
        v

Stage 3 — resource resolution (pcae.schema_resources.cltr_cutover_root())
  in:  none (package-relative, deterministic)
  out: filesystem path to the installed cltr_cutover root, or registry_failure
  owner: authority_inspection.py, calling the existing packaged helper only

        |
        v

Stage 4 — registry build (pcae.schema_runtime.build_offline_registry)
  in:  resolved package root
  out: SchemaRegistry, or registry_failure
  owner: schema_runtime (frozen, reused unchanged)

        |
        v

Stage 5 — manifest verification (pcae.schema_runtime.load_and_verify_manifest)
  in:  manifest path (cltr_cutover_root() / "manifest.json"), registry
  out: VerifiedManifest, or manifest_failure
  owner: schema_runtime (frozen, reused unchanged)

        |
        v

Stage 6 — family + identity resolution (authority_inspection.py)
  in:  parsed record dict, verified manifest
  out: resolved family class + manifest entry, or
       unknown_record_family / manifest_entry_missing /
       unsupported_schema_version / unsupported_model_version /
       family_identity_mismatch / registry_entry_missing
  owner: authority_inspection.py (static dispatch dict, TAMPC-REQ-055)

        |
        v

Stage 7 — schema validation (pcae.schema_runtime.validate_record_shape)
  in:  record dict, resolved schema_id, registry
  out: shape-conformant confirmation, or schema_validation_failed
  owner: schema_runtime (frozen, reused unchanged)

        |
        v

Stage 8 — typed model construction (Family.from_dict) + lossless round trip
  in:  record dict
  out: typed model + model.to_dict() == record, or
       model_validation_failed / required_provenance_failed
  owner: pcae.cltr.authority.* (frozen, reused unchanged) for construction;
         authority_inspection.py for the round-trip equality check

        |
        v

Stage 9 — immutable observation construction (authority_inspection.py)
  in:  typed model, provenance-bearing values, resolved manifest/registry info
  out: InspectionObservation (frozen)
  owner: authority_inspection.py

        |
        v

Stage 10 — rendering (authority_inspect.py)
  in:  InspectionOutcome
  out: stdout text (human or --json)
  owner: authority_inspect.py

        |
        v

Stage 11 — exit status (authority_inspect.py)
  in:  InspectionOutcome
  out: process exit code 0 or 1
  owner: authority_inspect.py
```

Every stage has exactly one owner, one input shape, one output shape, and
a fixed set of failure categories, matching TAMPC-REQ-111's precedence
exactly. No stage retries, coerces, or substitutes a default.

---

## 7. Error Mapping

Deterministic one-to-one mapping from internal condition to public
outcome, per TAMPC-001 §17:

| Internal condition | Validation stage | Failure identifier | CLI message shape | Exit code |
|---|---|---|---|---|
| `Path` does not resolve, or resolves through a broken symlink | 1 | `input_not_found` | Fixed generic text + the one supplied path | 1 |
| `Path.is_file()` false (directory, FIFO, socket, device) | 1 | `input_not_a_file` | Fixed generic text + the one supplied path | 1 |
| `PermissionError`/`OSError` at read time | 1 | `input_unreadable` | Fixed generic text, no OS errno text | 1 |
| `stat().st_size` exceeds `DEFAULT_MAX_INPUT_BYTES` | 1 | `malformed_artifact` | Fixed generic text | 1 |
| Zero-byte file | 1 | `malformed_artifact` | Fixed generic text | 1 |
| Non-UTF-8 bytes / non-JSON / non-object top-level / duplicate key / trailing data | 2 | `malformed_artifact` | Fixed generic text | 1 |
| `cltr_cutover_root()`/`build_offline_registry` raises `OSError`/`SchemaRegistryError`/`ValueError` | 3–4 | `registry_failure` | Fixed generic text, no path/traceback | 1 |
| `load_and_verify_manifest` raises `OSError`/`ManifestIntegrityError`/`SchemaRegistryError`/`ValueError` | 5 | `manifest_failure` | Fixed generic text, no path/traceback | 1 |
| `record_type` missing or not in dispatch table | 6 | `unknown_record_family` | Fixed text + the artifact's own declared family string (TAMPC-REQ-109 exception) | 1 |
| Manifest entries for the family ≠ 1 | 6 | `manifest_entry_missing` | Fixed generic text | 1 |
| `schema_version` ≠ `"1.0"` or ≠ manifest entry's own version | 6 | `unsupported_schema_version` | Fixed text + the declared version string | 1 |
| `contract_version` ≠ `"1.0"` | 6 | `unsupported_model_version` | Fixed text + the declared version string | 1 |
| `schema_id` ≠ resolved manifest entry's `schema_id` | 6 | `family_identity_mismatch` | Fixed text + both declared identities | 1 |
| `registry.resource_info(schema_id)` raises `SchemaRegistryError` | 6 | `registry_entry_missing` | Fixed generic text | 1 |
| `validate_record_shape` infrastructure failure | 7 | `registry_failure` | Fixed generic text | 1 |
| `validate_record_shape` shape-invalid | 7 | `schema_validation_failed` | Owner-provided structured issues (already sanitized by `schema_runtime`) | 1 |
| `Family.from_dict` raises `TypedModelError`/`TypeError`/`ValueError` | 8 | `model_validation_failed` | Fixed generic text + model class name | 1 |
| `model.to_dict() != record` | 8 | `required_provenance_failed` | Fixed generic text | 1 |
| A required identity/version/digest field absent post-construction | 8 | `required_provenance_failed` | Fixed generic text | 1 |
| Missing `path` CLI argument / unknown flag | — (argparse, before Stage 1) | N/A (argparse usage error) | argparse's own usage text | argparse's existing usage-error code (conventionally `2`) |

Every category above traces to Section 17 of TAMPC-001 with no renaming
and no consolidation beyond what TAMPC-REQ-107/108 already fix.

---

## 8. Provenance Planning

Provenance object construction happens once, only on the success path
(Stage 9), from the fully constructed typed model (`typed_wire =
model.to_dict()`), never from the raw pre-validation dict — this mirrors
the prototype's `_provenance_bundle(typed_wire, ...)` call exactly.

| Provenance field | Classification (TAMPC-REQ-085) | Source |
|---|---|---|
| `source_artifact_identity` (the path) | sourced | CLI invocation |
| `input_digest` | derived | SHA-256 of the exact bytes read (Stage 1), computed once, before parsing |
| `record_identity` (`record_id`) | sourced | Copied from `typed_wire` |
| `record_family` (`record_type`) | sourced | Copied from `typed_wire` |
| `schema_identity`/`schema_version` | sourced | Copied from `typed_wire` |
| `model_version` (`contract_version`) | sourced | Copied from `typed_wire` |
| `declared_record_digest` (`record_digest`) | sourced | Copied from `typed_wire`, never compared against `input_digest` (TAMPC-REQ-091) |
| `manifest_entry` | derived | The one resolved manifest entry (Stage 6), wrapped as `OpaqueJsonValue` |
| `registry_resource` | derived | `registry.resource_info(schema_id)` fields, wrapped as `OpaqueJsonValue` |
| `schema_validation`/`model_validation` outcome objects | derived | Constructed from Stage 7/8 results |
| `validation.semantic`/`validation.lifecycle`/`validation.governance` | unavailable/prohibited from inference | Fixed literal `"not_performed"`, never computed |
| `copied_provenance_values` | sourced (where present) | Named-field walk over `typed_wire` (`authority_disclosure`, `derivation`, `extensions`, `limitations`, `opaque`, `uncertainty`, any `*_reference`/`*_references`), sorted by `instance_path` |
| `complete_typed_record_claims` | sourced | The full `typed_wire` dict, wrapped as `OpaqueJsonValue` |
| `derivation` map | derived | Explicit `copied_fields`/`derived_fields`/`external_references_followed: False` record |
| `authority_neutrality` disclosure | sourced (fixed constant) | `REPRESENTATION_ONLY_DISCLOSURE` |

**Digest calculation timing.** `input_digest` is computed once, at the end
of Stage 1, over the exact `bytes` object read — before any parse,
validation, or dispatch begins (TAMPC-REQ-088). No later stage
recomputes it.

**Registry/schema references.** Reported as observations only (the
resolved `resource_info` and manifest entry), never re-derived or
re-verified by this consumer beyond what Stage 4/5's frozen owners already
did.

**Limitations/uncertainty disclosures.** Any `limitations`, `uncertainty`,
`opaque`, `extensions`, or `*_reference(s)` field present in the record is
copied verbatim into `copied_provenance_values`/`complete_typed_record_claims`;
absence is reported as absence, never fabricated (TAMPC-REQ-085).

No inferred authority: no field in this table is computed from anything
other than a sourced value, a frozen Stage 3 owner's own output, or a
fixed literal.

---

## 9. Immutability Plan

- **Immutable observation.** `InspectionObservation` and
  `InspectionFailure` are `@dataclass(frozen=True, slots=True)`
  (TAMPC-REQ-075).
- **Immutable collections.** Every nested JSON-shaped field
  (`manifest_entry`, `registry_resource`, `schema_validation`,
  `model_validation`, `record_claims`, `provenance`) is an `OpaqueJsonValue`
  instance, never a raw `dict`/`list` (TAMPC-REQ-076). Any additional
  list-shaped field introduced during 137K is a `tuple`, never a `list`
  (TAMPC-REQ-077).
- **Nested ownership.** `OpaqueJsonValue` already deep-freezes its input
  recursively (`pcae.cltr.authority.opaque.freeze_json_value`, reused
  unchanged); `authority_inspection.py` does not reimplement freezing.
- **Defensive copying.** `OpaqueJsonValue.to_json()` already returns a
  fresh, independent, mutable copy on each call (existing frozen Stage 3
  behavior) — callers reading an observation's fields for display never
  receive a shared mutable reference back into the observation's own
  frozen state.
- **`__setattr__`/`__delattr__`.** Both `InspectionObservation` and
  `InspectionFailure` define an explicit override that unconditionally
  raises `dataclasses.FrozenInstanceError`, in addition to (not instead
  of) `frozen=True` (TAMPC-REQ-078). This is the exact 137H-fixed
  hardening mechanism for Phase 137F's NB-1 observation.
- **Residual limitation, documented exactly as frozen.** This is
  defense-in-depth against an accidental future refactor weakening
  `frozen=True`; it does not, and is not claimed to, prevent a caller who
  deliberately invokes `object.__setattr__(instance, ...)`. That residual
  bypass is explicitly out of TAMC-001's threat model (an adversarial or
  grossly negligent act, not an accidental one) and TAMPC-001 v1.0 does
  not require it to be defeated (TAMPC-REQ-078, restated verbatim per this
  plan's own obligation not to relax the contract). 137K's mutation test
  (Section 11) proves only the ordinary-assignment path
  (`instance.field = value`) is blocked; it does not attempt to prove
  `object.__setattr__` itself is blocked.

---

## 10. Package Resources

- **Invocation.** `authority_inspection.py` calls
  `pcae.schema_resources.cltr_cutover_root()` exactly as it exists today
  (a context manager yielding a real filesystem `Path`,
  `resources.files(__package__) / "cltr_cutover"` resolved via
  `importlib.resources.as_file`). No new resolution helper is authored
  (TAMPC-REQ-048).
- **Lookup.** The manifest path is `cltr_cutover_root() / "manifest.json"`;
  the manifest schema identity is the frozen constant
  `"https://pcae.local/schemas/cltr_cutover/manifest.schema.json"`
  (unchanged from the prototype's `MANIFEST_SCHEMA_ID`).
- **Caching policy.** None. Each invocation is a fresh process
  (TAMPC-REQ-122); `cltr_cutover_root()` is called once per invocation,
  inside the `with` block for the duration of Stages 3–7, and the yielded
  path is not persisted beyond the invocation.
- **Offline behavior.** `cltr_cutover_root()` already performs no network
  access and already works identically from an editable install, a built
  wheel, or an sdist install (existing docstring guarantee, unchanged).
  137K's packaging tests (Section 11) confirm this live rather than assume
  it, per the Phase 106D packaging-incident precedent Phase 137G §19/22
  already cites.
- **Repository-root lookups.** Forbidden — `authority_inspection.py` never
  computes a path relative to the current working directory, an
  environment variable, or a repository-root guess (TAMPC-REQ-161).

---

## 11. Testing Strategy

Complete testing hierarchy for 137K (design only; no test is written by
this plan):

- **Unit.** `inspect_artifact_at_path` and the private provenance
  assembler, tested directly against in-memory `bytes`/`Path` fixtures,
  independent of the CLI layer.
- **Integration.** Full CLI-to-orchestration round trip via
  `subprocess`/`CliRunner`-equivalent invocation of
  `pcae authority inspect <fixture-path>`.
- **CLI.** Argument parsing, help text, `--json` flag, exit codes,
  matching the existing `tests/` convention for other `pcae` subcommands.
- **Package installation.** A genuine `pip install` into an isolated
  environment followed by running `pcae authority inspect` against a
  fixture record (Phase 106D-style packaging-smoke-test discipline).
- **Editable install.** `pip install -e .` followed by the same smoke
  invocation.
- **Wheel install.** `python -m build --wheel` then install-and-run.
- **sdist install.** `python -m build --sdist` then install-and-run.
- **Offline.** All of the above executed with network access disabled
  (or in an environment with no reachable network), confirming no
  resolution step silently depends on connectivity.
- **Failure injection.** Monkeypatched `SchemaRegistryError`/
  `ManifestIntegrityError`/`OSError` raised from the frozen Stage 3 owners,
  confirming translation to the correct failure category with no leaked
  exception text (mirroring Phase 137F §12's monkeypatch discipline).
- **Determinism.** Repeated invocation of the same fixture produces
  byte-identical `--json` output; two different paths with byte-identical
  content produce identical output except `source_artifact_identity`.
- **Property tests (where useful).** A property test asserting that for
  every one of the sixteen dispatch-table families, a schema-valid,
  freshly generated fixture record always reaches `outcome: "inspected"`
  — bounded to the sixteen known families only, not a general fuzz of
  arbitrary `record_type` strings (which is already covered by the
  `unknown_record_family` fixture).
- **Adversarial cases.** Forged `is_authoritative: true`, operative-looking
  `state` values, oversized nested JSON near
  `DEFAULT_MAX_RECORD_DEPTH`/`DEFAULT_MAX_NESTING_DEPTH`, duplicate keys,
  symlink targets in every combination of missing/non-regular/unreadable.
- **Regression suites.** One golden fixed-output fixture per family
  (sixteen total), diffed byte-for-byte on every future change to catch
  accidental output-shape drift.
- **Freshness requirement.** Every fixture above is freshly,
  independently authored for 137K, never copied verbatim from
  `tests/test_typed_authority_inspector_137e.py` (TAMPC-REQ-168), per the
  demonstrated Phase 137F.1V lesson that a fresh, independently authored
  fixture found live gaps a predecessor's fixture table missed. The
  implementation's own expected-value table is not the sole oracle for
  any test (TAMPC-REQ-169) — expected values are independently computed
  from the frozen schemas/models, not copied from what
  `authority_inspection.py` itself happens to produce.
- **Neutrality regression.** `pcae runtime inspect` output identical
  before/after; `pcae health`/`pcae check`/`pcae status coherence`/
  `pcae doctor task-memory` unchanged before/after.
- **Fast Green regression pass and directly-affected full-suite evidence**,
  per this repository's own existing verification convention
  (`.venv/bin/python -m pytest -n auto`).

---

## 12. Security Review

Planned validation only; no implementation:

| Threat | Planned defense | Test category |
|---|---|---|
| Malformed JSON | Reused `parse_strict_json` (no new parser) | Malformed-input fixtures |
| Duplicate keys | Reused strict-parser rejection | Duplicate-key fixture |
| Oversized files | `stat()`-based size gate before any `open()`/read | Oversized-file fixture (just above `DEFAULT_MAX_INPUT_BYTES`) |
| Unsupported versions | Exact-literal comparison, no nearby-version fallback | Version-mismatch fixtures (schema and model) |
| Unknown families | Static dispatch dict, `unknown_record_family` fail-closed | Unknown/missing/non-string `record_type` fixtures |
| Malformed paths | `Path.is_file()` check before `open()`; no path-string parsing beyond `pathlib` | Directory/FIFO/socket/device-file fixtures |
| Special files | Same `Path.is_file()` gate | Special-file fixture (platform-conditional, skipped where unsupported) |
| Symlinks | OS-resolved real path used for size/type checks; no elevated trust to target; single resolved-path read, no directory walk | Symlink-to-missing, symlink-to-directory, symlink-to-oversized, symlink-to-valid fixtures |
| TOCTOU | Single full read into immutable `bytes` before any processing; no re-stat/re-read | Fixture that mutates the file between stat and a simulated second read attempt (asserting no second read occurs) |
| Hostile manifests | `load_and_verify_manifest`'s existing digest/shape verification, unchanged; failure maps to `manifest_failure` | Monkeypatched manifest-corruption fixture |
| Hostile registry entries | `build_offline_registry`'s existing verification, unchanged; failure maps to `registry_failure`/`registry_entry_missing` | Monkeypatched registry-corruption fixture |

No implementation is authorized by this section; 137K performs the actual
coding against this design.

---

## 13. Performance Expectations

- **Expected complexity.** O(n) in artifact byte size for parsing and
  digesting (n ≤ `DEFAULT_MAX_INPUT_BYTES` = 5 MiB); O(1) family dispatch
  (dict lookup); O(m) manifest-entry filter where m = manifest entry count
  (currently 16, fixed by the frozen manifest); O(k) schema validation
  where k is bounded by `DEFAULT_MAX_RECORD_DEPTH`/`DEFAULT_MAX_ISSUE_COUNT`
  (frozen Stage 3 limits, unchanged).
- **Expected filesystem operations.** Exactly one `stat()` (size check),
  one `open()`/read (the artifact), and whatever `cltr_cutover_root()`'s
  existing `importlib.resources.as_file` resolution performs internally
  (already fixed, frozen behavior) per invocation. No repeated reads, no
  directory traversal.
- **Expected manifest lookups.** Exactly one manifest load/verify per
  invocation (Stage 5), followed by one in-memory filter over its
  `entries` list (Stage 6) — no repeated manifest re-parsing.
- **Expected registry lookups.** Exactly one `build_offline_registry` call
  and one `registry.resource_info(schema_id)` call per invocation.

No premature optimization is planned: every operation above is already
bounded by existing frozen Stage 3 limits, and the consumer processes
exactly one artifact per process invocation (TAMPC-REQ-005), so there is
no loop or batch path to optimize.

---

## 14. Packaging

- **Editable install.** `pip install -e .` must expose `pcae authority
  inspect` immediately, resolving `cltr_cutover_root()` against the
  repository checkout's own `src/pcae/schema_resources/cltr_cutover/`.
- **Wheel.** `python -m build --wheel` must include
  `authority_inspection.py`, `authority_inspect.py` (already covered by
  `packages = ["src/pcae"]`, no `pyproject.toml` change needed —
  TAMPC-REQ-156), and the unchanged, already-included
  `schema_resources/cltr_cutover/` tree.
- **sdist.** `python -m build --sdist` must include the same files; a
  dedicated sdist-content test (`tar tzf` or equivalent) confirms this,
  directly modeled on the Phase 106D sdist-scoping incident this
  repository's own `pyproject.toml` comment already references.
- **Offline execution.** A wheel installed into a fresh virtual
  environment with network access disabled must run
  `pcae authority inspect <fixture>` successfully end to end.
- **No repository dependency.** Confirmed by running the installed-wheel
  smoke test from a working directory outside the repository checkout
  entirely (e.g. a temp directory), proving no repository-root-relative
  path assumption survived (TAMPC-REQ-161).

---

## 15. CLI UX

- **stdout.** Both success and failure output go to stdout in both human
  and `--json` mode, matching `cltr_shadow.py`'s existing convention of
  writing outcome content (success or failure) to stdout with the exit
  code as the machine-checkable signal (TAMPC-REQ-109). No separate
  stderr channel is introduced for outcome content.
- **stderr.** Reserved for argparse's own usage-error output only (missing
  `path`, unknown flag) — unchanged, existing `argparse` behavior, not a
  new contract obligation.
- **Exit codes.** `0` = `inspected`; `1` = any `InspectionFailure`
  category; argparse's own usage-error code (conventionally `2`) for CLI
  misuse.
- **Machine-readable output.** `--json` → `json.dumps(payload, indent=2,
  sort_keys=True, default=str)`.
- **Human-readable output.** Fixed field order matching TAMPC-REQ-084's
  field order, one `key: value` line per field, plus the unconditional
  disclosure line printed first (mirroring `cltr_shadow.py`'s
  `_DISCLOSURE_LINE` placement).
- **Error formatting.** Failure output uses the same rendering path as
  success output (same `_render` function), so a failure's fixed fields
  (Section 7's table) appear with identical formatting discipline.
- **Help text.** `pcae authority --help` and `pcae authority inspect --help`
  describe the single positional `path`, the `--json` flag, and state the
  representation-only disclosure (TAMPC-REQ-018).
- **Examples (illustrative only, not implementation):**

  ```
  $ pcae authority inspect ./epoch.json
  [representation-only, non-authoritative — see disclosure]
    outcome: inspected
    consumer_identity: pcae-authority-inspect-v1
    ...

  $ pcae authority inspect ./epoch.json --json
  {
    "outcome": "inspected",
    ...
  }

  $ pcae authority inspect ./missing.json
  [representation-only, non-authoritative — see disclosure]
    outcome: input_not_found
    ...
  $ echo $?
  1
  ```

No implementation is produced by these examples; they illustrate the
planned shape only.

---

## 16. Verification Plan

What Phase 137K's implementation must prove, and what Phase 137L must
independently re-verify (not accepting 137K's own claims as an oracle,
per the Phase 137F/137F.1V precedent):

| Area | Required evidence | Required tests | Required artifacts | Required regressions | Required negative cases |
|---|---|---|---|---|---|
| Command identity | `pcae authority --help`/`pcae authority inspect --help` live output | CLI registration tests | Help-text snapshot | Snapshot diff on future change | Unknown flag, extra positional, alias attempt |
| Package boundary | Static import-scan result | AST-based import test | Import-scan report in traceability matrix | Re-run on every future PR touching these modules | Forbidden-import fixture (a deliberately bad import, confirming the scan catches it) |
| Input contract | All Section 6 Stage-1 fixtures pass | Path-boundary test suite | Fixture directory | Golden fixture set | Missing/directory/special-file/symlink/unreadable/oversized/empty |
| Output contract | Field-parity diff (human vs `--json`) | Output-parity tests | Golden output per family | Byte-diff regression | Field omitted in one mode but not the other (should be unreachable; test proves it) |
| Failure taxonomy | One fixture per category, 14 total | Category tests | Fixture-to-category map | Re-run whole map on every change | Multi-defect fixture (precedence test) |
| Exit codes | 0/1/argparse-code confirmed live | Exit-code tests | CI log excerpt | — | Non-file path, missing path |
| Provenance | Field-by-field table match | Provenance tests (11+ fields) | Field-presence matrix | Golden fixture | Field absent in source record → `"unavailable"` sentinel, never fabricated |
| Immutability | Mutation-attempt failure confirmed | `test_ordinary_assignment_blocked` | — | Re-run on every dataclass field addition | Attempted mutation of every field, not just one |
| Security | Adversarial/monkeypatch suite green | Section 12's fixture table | — | Re-run on Stage 3 owner upgrades | Forged authority claim, corrupted manifest, corrupted registry |
| Packaging | Wheel/sdist/editable/offline install-and-run all succeed | Section 11's install tests | Build artifacts (wheel/sdist file listing) | Re-run before every release | Missing packaged resource (simulated) |
| Lifecycle neutrality | `pcae health`/`check`/`status coherence`/`doctor task-memory` unchanged before/after | Before/after diff test | Before/after output capture | Re-run in 137L | — |
| Runtime neutrality | `pcae runtime inspect` output identical before/after | Before/after diff test | Before/after output capture | Re-run in 137L | — |
| Determinism | Repeated-invocation byte-identical output | Determinism test | — | Re-run on every change | — |

---

## 17. Increment Planning

Bounded, independently reviewable implementation groups for 137K:

- **Group 1 — Production module skeleton.** Create
  `authority_inspection.py` and `authority_inspect.py` with module
  constants (`CONSUMER_ID`, version literals), the `InspectionObservation`/
  `InspectionFailure` dataclass shells (Section 9's immutability hardening
  included from the start), and stub orchestration returning only
  `malformed_artifact` for any input (no CLI registration yet). Reviewable
  in isolation: confirms import boundaries (TAMPC-REQ-024–028) before any
  real logic exists.
- **Group 2 — Resource resolution.** Wire `cltr_cutover_root()`,
  `build_offline_registry`, `load_and_verify_manifest` into the
  orchestration function (Stages 3–5); tests confirm resolution against
  the live installed package. No family/schema logic yet.
- **Group 3 — Validation pipeline.** Implement Stages 6–8 (family
  dispatch, schema validation, model construction, lossless round trip)
  for all sixteen families at once (the dispatch table is a single
  literal; splitting families across groups would create sixteen
  arbitrary sub-boundaries with no independent value). Tests: one fixture
  per family plus every Section 7 failure category.
- **Group 4 — Immutable observation + provenance.** Implement the
  provenance assembler and full `InspectionObservation` construction
  (Stage 9). Tests: field-by-field provenance assertions, mutation-attempt
  tests.
- **Group 5 — Rendering.** Implement `_render` (human + `--json`) in
  `authority_inspect.py`. Tests: output-parity, sorted-key, fixed-field-
  order tests.
- **Group 6 — CLI integration.** Register the `authority`/`inspect`
  subparser in `src/pcae/cli.py`, wire `run_authority_inspect` end to end,
  including the Stage 1 bounded read. Tests: full CLI invocation,
  exit-code tests, help-text tests.
- **Group 7 — Verification.** Packaging tests (wheel/sdist/editable/
  offline), lifecycle/runtime-neutrality tests, security/adversarial
  suite, determinism suite, Fast Green regression, traceability matrix
  completion (Section 2 of this plan, filled in with real evidence
  citations).

Each group is independently reviewable: Groups 1–2 introduce no user-
visible behavior; Group 3 is the only group touching all sixteen
families and is reviewed as one unit precisely because TAMPC-REQ-150/151
require additive-only, non-family-differentiated behavior; Groups 4–6
each add exactly one layer (data shape, then presentation, then CLI
surface); Group 7 adds no new production code, only verification
artifacts.

---

## 18. Risk Register

| Risk | Class | Likelihood | Impact | Mitigation | Verification |
|---|---|---|---|---|---|
| A fixture reused from `tests/test_typed_authority_inspector_137e.py` masks a live gap (repeating the Phase 137F.1V lesson) | High | Medium | High | TAMPC-REQ-168 mandates fresh authorship; this plan's Section 11 states the requirement explicitly for every fixture category | 137L independently re-derives fixtures rather than trusting 137K's fixture table |
| `authority_inspection.py`'s calling convention for the bounded read (Section 5's open question) is implemented inconsistently with TAMPC-REQ-021's ownership split | Medium | Low | Medium | Group 1 review explicitly checks the read boundary before Group 2 begins; TAMPC-001 itself does not fix the exact parameter shape beyond the frozen signature, so 137K's choice must be documented in the traceability matrix, not silently assumed | Static review in Group 1; traceability matrix entry |
| Packaging drift (wheel missing the new modules or the resource tree) | Medium | Low | High | Section 11/14 require genuine build-and-install tests, not assumption, directly following the Phase 106D precedent | Wheel/sdist content tests in Group 7 |
| A future manifest edit silently introduces a second entry for one family, only caught by the fail-closed `manifest_entry_missing` path in the field | Low | Low | Medium | TAMPC-REQ-059 dedicated regression test, planned in Section 2's row 054–060 | `test_manifest_one_entry_per_family` run against the live manifest |
| An adversarial record with an operative-looking claim is misread as an authority signal by a future caller of this CLI's output | Medium | Low | High | TAMPC-REQ-146/147 and Section 12's adversarial suite; disclosure line is a non-suppressible dataclass default | Authority-neutrality tests, both automated and human-readable-output manual read |
| Exception text leak (a raw `OSError`/library message reaching stdout) | Medium | Low | Medium | TAMPC-REQ-132's fixed-message-per-category discipline; direct precedent from Phase 137F §12's found-and-fixed leak | Exception-sanitization tests per category |
| `object.__setattr__` bypass is later mistaken for "fixed" by a future reader | Low | Low | Low | This plan and TAMPC-REQ-078 both document the residual limitation exactly, with no overstated claim | Documentation review only; no test can prove a negative here per TAMPC-001's own stated scope |
| Scope creep: a reviewer or implementer adds a second CLI flag or a convenience default "while already in the file" | Medium | Low | High | TAMPC-REQ-015/017 fix the exact flag set; Section 1's non-goals restate it; Group 6 review checks the parser definition against TAMPC-REQ-013 verbatim | CLI registration test asserts exactly one positional, exactly one optional flag |

---

## 19. No-Go Confirmation

This plan does not introduce, and 137K/137L must not introduce under this
plan's authority:

- **Authority** — no authority calculation, persistence, resolution,
  transfer, or activation (TAMPC-REQ-146).
- **Execution** — no execution adapter, no runtime plugin registration, no
  `PermissionBroker` request (TAMPC-REQ-143–144).
- **Runtime capability** — Runtime remains Observed / observe /
  unavailable both before and after 137K's eventual implementation
  (TAMPC-REQ-145).
- **Generic framework** — no plugin-style family-dispatch registry, no
  multi-consumer abstraction (TAMPC-REQ-008).
- **Lifecycle mutation** — no phase-report write, no completion-metadata
  write, no task-state write, no marker/receipt write (TAMPC-REQ-140–141).
- **Notification** — no notification dispatch as a consequence of
  inspection (TAMPC-REQ-012).
- **Publication** — no publication action or publication-state mutation
  (TAMPC-REQ-011).
- **Recovery** — no recovery action (TAMPC-REQ-011).
- **Rollback** — no rollback action (TAMPC-REQ-011).
- **Semantic decision engine** — no semantic, lifecycle, or governance
  validation is performed or claimed; all three are hardcoded
  `"not_performed"` (TAMPC-REQ-062).

This plan itself performs none of the above; it is documentation only.

---

## 20. Governance

Interpreter provenance is confirmed before any Python validation step in
137K/137L, per TAMPC-REQ-165:

```
.venv/bin/python -c 'import sys; print(sys.executable); print(sys.prefix)'
```

The resolved interpreter and prefix must resolve inside this repository's
`.venv`. All Python-based development, testing, packaging, and
verification for 137J/137K/137L uses `.venv/bin/python`,
`.venv/bin/python -m pytest`, `.venv/bin/python -m pip`,
`.venv/bin/python -m build` exclusively (TAMPC-REQ-163). `/usr/bin/python3`,
bare `python`/`python3`/`pip`/`pytest`, a globally installed `pytest`, and
system-Python dependency installation are not used (TAMPC-REQ-164). If
`.venv` is missing or unusable, work stops and the environment defect is
reported; no dependency is installed and no silent fallback to a
different interpreter occurs (TAMPC-REQ-166).

Only governed PCAE workflows are used for commit/push in every phase this
plan governs (`pcae commit`/`pcae push`-equivalent governed commands); no
raw `git commit`/`git push`.

This phase (137J) itself is documentation-only and modifies no production
module.

---

## 21. Validation

- **Every TAMPC requirement mapped.** Section 2's table spans TAMPC-REQ-001
  through TAMPC-REQ-178 with no gap; Section 16's verification plan
  restates the evidence categories for the highest-risk areas.
- **Every module has bounded responsibility.** Sections 3–4 assign
  Section 6's ownership table exactly, restating TAMPC-001 §6/Phase 137G
  §6 with no reassignment.
- **Every public interface frozen.** Section 5 freezes
  `inspect_artifact_at_path`'s signature exactly as TAMPC-REQ-023 states
  it; no parameter is added, removed, or renamed.
- **Every implementation area testable.** Section 11 (testing strategy)
  and Section 16 (verification plan) jointly cover unit, integration,
  CLI, packaging (all four install modes), offline, failure-injection,
  determinism, property, adversarial, and regression testing.
- **No architecture drift.** This plan introduces no component, dependency,
  or CLI surface beyond what Phase 137G's architecture (Sections 3–21) and
  TAMPC-001 (Sections 1–33) already fix. Section 5's "open question" about
  the exact internal parameter shape for the bounded-read handoff is
  explicitly named as an implementation-detail choice within TAMPC-REQ-023's
  frozen signature, not an architectural addition — TAMPC-REQ-023 fixes
  the *public* signature exactly; it does not fix every private internal
  calling convention inside `authority_inspection.py`/`authority_inspect.py`,
  and this plan does not manufacture a contract-level ambiguity out of an
  implementation-only degree of freedom.
- **No contract drift.** No TAMPC-001 requirement is relaxed, renamed, or
  reinterpreted by this plan; every table in this document cites the exact
  requirement ID it implements. Independent review during planning found
  no genuine ambiguity requiring TAMPC-REQ-177's contract-repair escalation
  — the one internal-parameter degree of freedom noted in Section 5 is,
  as stated there, not a contract ambiguity, since TAMPC-REQ-023 already
  fixes the entire public contract surface exactly and leaves internal
  wiring to implementation by design (matching the same discretion the
  prototype's own internal helpers, `_MODEL_BY_FAMILY`/`_provenance_bundle`,
  already exercised without any contract naming their exact call shape
  either).

---

## Success Criteria Confirmation

- Implementation scope is frozen (Section 1). ✅
- Every TAMPC requirement has an owner (Section 2, all 178 IDs mapped). ✅
- Implementation sequence is deterministic (Section 6, Section 17). ✅
- Module responsibilities are fixed (Sections 3–4, 6). ✅
- Public API is frozen (Section 5). ✅
- Validation pipeline is frozen (Section 6). ✅
- Testing strategy is complete (Section 11). ✅
- Security review is complete (Section 12). ✅
- Verification evidence is defined (Section 16). ✅
- No production code has been written by this phase. ✅
- No runtime capability changes. ✅
- No contract drift (Section 21). ✅
- Runtime remains Observed / observe / unavailable. ✅

## Recommended Next Phase

**137K — Typed Authority Model Production Consumer Implementation.**

This phase (137J) converts TAMPC-001 v1.0 into a bounded,
implementation-ready plan with no Blocking finding and no unresolved
contract ambiguity (Section 21). 137K may proceed to implement exactly
`authority_inspection.py`, `authority_inspect.py`, and the `authority`
CLI registration, per this plan and TAMPC-001, with no architectural
expansion or contract change except for an independently demonstrated
documentation defect unrelated to planning. 137K itself still requires
its own separately authorized task; this recommendation grants no
implementation authority by itself.
