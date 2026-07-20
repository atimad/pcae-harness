# Typed Authority Model Production Consumption Contract

## Contract identity and status

**Contract:** TAMPC-001
**Version:** 1.1
**Status:** FROZEN
**Frozen by:** Phase 137H — Typed Authority Model Production Consumption
Contract Freeze
**Revised by:** Phase 137M — TAMPC-001 Signature Ambiguity Contract Repair
(Section 36; repairs Finding F-1 from Phase 137L, no semantic expansion)

TAMPC-001 v1.1 is the sole authoritative contract governing implementation
and verification of the first production Typed Authority Model consumer,
`pcae authority inspect <path>`. Future implementation phases SHALL cite
TAMPC-001 and SHALL NOT reinterpret Phase 137G's architecture, or TAMC-001,
or TAMP-001, locally.

The Phase 137G production-integration architecture
(`docs/PHASE_137G_TYPED_AUTHORITY_MODEL_PROTOTYPE_REVIEW_AND_PRODUCTION_INTEGRATION_ARCHITECTURE.md`)
is the approved design basis for this contract. Where architecture prose and
this contract differ in force, this contract is normative. TAMC-001 v1.0
remains the sole authoritative contract for consumption behavior in general;
TAMPC-001 governs only how the one production consumer selected by Phase
137G Section 3 implements that behavior. TAMP-001 v1.0 remains the
authoritative plan for the Phase 137E prototype; TAMPC-001 does not amend
it, and the prototype module is unaffected by this contract. Stage 3
schemas, typed models, registry, and manifest remain authoritative for
schema shape, typed representation, and package content; TAMPC-001 governs
only how the production consumer may read and represent them.

This is contract text only. It does not implement, activate, authorize, or
integrate the production consumer. It grants no runtime, lifecycle, or
authority capability, and it does not itself authorize the implementation
phase (137J/137K) — Section 31 fixes the exact preconditions that remain.

Runtime posture, unaffected by this contract:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, and **MAY**
are normative. `SHALL` and `MUST` state binding requirements; `SHALL NOT`
and `MUST NOT` state binding prohibitions; `MAY` states a permission within
all other requirements. `MAY NOT` is used only as a synonym for `SHALL NOT`
where grammatically clearer, never to express a weaker prohibition. This
contract does not use `SHOULD`: every mandatory behavior is stated as
`SHALL`/`SHALL NOT`, and every discretionary behavior is stated as `MAY`.

Every mandatory behavior receives a unique, sequential, stable,
non-reused, independently traceable requirement identifier of the form
`TAMPC-REQ-###`. Identifiers are never renumbered or reused across
revisions (Section 33).

## 1. Purpose

TAMPC-REQ-001: This contract SHALL govern the first production Typed
Authority Model consumer, `pcae authority inspect <path>`, across: production
package placement; command identity; explicit artifact input; loading;
family resolution; registry and manifest resolution; validation;
typed-model construction; provenance preservation; observation
construction; output rendering; failure behavior; security; packaging;
testing; authority neutrality; lifecycle neutrality; and runtime
neutrality.

TAMPC-REQ-002: An implementation conforming to TAMPC-001 SHALL also conform
to every TAMC-001 requirement applicable to an Allowed `inspection`
consumer. TAMPC-001 narrows and operationalizes TAMC-001 for this one
consumer; it SHALL NOT relax any TAMC-001 requirement.

TAMPC-REQ-003: Conformance with TAMPC-001, alone, SHALL NOT authorize
implementation. Section 31 states the complete precondition set.

## 2. Scope

TAMPC-REQ-004: This contract SHALL freeze exactly one production consumer:
`pcae authority inspect <path>`. No additional production consumer is in
scope of TAMPC-001 v1.0.

TAMPC-REQ-005: The command SHALL inspect exactly one explicitly supplied
local artifact per invocation.

TAMPC-REQ-006: This contract SHALL apply to: command parsing; artifact
loading; Stage 3 resource resolution; validation; deserialization;
observation creation; rendering; exit status; and failure reporting, for
the one consumer named in Section 2's TAMPC-REQ-004.

TAMPC-REQ-007: This contract SHALL apply to all sixteen frozen Typed
Authority Model record families defined by TAMC-REQ-005: `authority_epoch`,
`authority_state`, `certification`, `compatibility_state`,
`concurrency_conflict`, `cutover_candidate`, `cutover_request`,
`human_authorization`, `marker_authority_binding`,
`notification_authority_binding`, `publication_attempt`,
`publication_evidence`, `quarantine_record`, `readiness_package`,
`receipt_authority_binding`, and `recovery_journal_entry`.

## 3. Non-Goals

TAMPC-REQ-008: An implementation conforming to TAMPC-001 SHALL NOT
introduce a second production consumer, a generic multi-consumer
framework, or a plugin-style family-dispatch registry.

TAMPC-REQ-009: An implementation SHALL NOT perform ambient repository
scanning, artifact discovery, recursive directory scanning, or "latest"
record resolution of any kind.

TAMPC-REQ-010: An implementation SHALL NOT infer authority or infer
lifecycle state from any input.

TAMPC-REQ-011: An implementation SHALL NOT mutate lifecycle state, activate
authority, activate runtime capability, execute, publish, recover, roll
back, cut over, execute compatibility behavior, or execute quarantine
behavior.

TAMPC-REQ-012: An implementation SHALL NOT dispatch a notification as a
consequence of inspection, perform automatic repair, persist any artifact
or state, make a semantic decision, retrieve a remote artifact, or perform
network access.

## 4. Command Identity Contract

TAMPC-REQ-013: The command form SHALL be exactly:

```
pcae authority inspect <path> [--json]
```

TAMPC-REQ-014: The command hierarchy SHALL be a new top-level subcommand
group `authority` registered in `src/pcae/cli.py`'s subparser table, with
exactly one subcommand, `inspect`.

TAMPC-REQ-015: `inspect` SHALL accept exactly one required positional
argument, `path`, and exactly one optional flag, `--json`. No other
positional argument and no other flag SHALL be accepted by the v1.0
implementation.

TAMPC-REQ-016: The implementation SHALL NOT introduce a command alias for
`authority` or for `inspect`.

TAMPC-REQ-017: The implementation SHALL NOT accept more than one path
argument, a glob, a directory argument, `--latest`, or `--phase-id`.

TAMPC-REQ-018: `pcae authority --help` and `pcae authority inspect --help`
SHALL print usage text describing the single positional `path` argument,
the `--json` flag, and the representation-only disclosure required by
Section 16.

TAMPC-REQ-019: `pcae --version`/`pcae authority inspect --version`
behavior SHALL be identical to every other existing `pcae` subcommand's
version behavior; the consumer SHALL NOT introduce a distinct version
scheme.

TAMPC-REQ-020: Exit-status, stdout, and stderr behavior SHALL be exactly as
fixed by Sections 16–18.

## 5. Production Package Boundary

TAMPC-REQ-021: Orchestration SHALL be implemented in a new module,
`src/pcae/cltr/authority_inspection.py`. Per TAMPC-REQ-179–TAMPC-REQ-182
(Section 5.1), orchestration's ownership begins at Section 7 (parsing) and
SHALL NOT include performing the artifact file read itself; the artifact
bytes are supplied to it by the CLI layer.

TAMPC-REQ-022: CLI wiring SHALL be implemented in a new module,
`src/pcae/commands/authority_inspect.py`. Per TAMPC-REQ-179 (Section 5.1),
CLI wiring's ownership includes the Section 6 explicit-input checks and the
Stage 1 bounded artifact read.

TAMPC-REQ-023: `src/pcae/cltr/authority_inspection.py` SHALL expose exactly
one public orchestration entry point:

```python
def inspect_artifact_at_path(
    path: Path, *, artifact_bytes: bytes, json_output: bool = False
) -> "InspectionOutcome": ...
```

plus the public result types `InspectionObservation`, `InspectionFailure`,
the type alias `InspectionOutcome = Union[InspectionObservation,
InspectionFailure]`, and the module constants `CONSUMER_ID`,
`TAMC_CONTRACT_VERSION`, `TAMPC_CONTRACT_VERSION`,
`SUPPORTED_SCHEMA_VERSION`, `SUPPORTED_MODEL_VERSION`. No other name SHALL
be part of the module's public API; every other helper (the family dispatch
table, the provenance assembler) is module-private (a leading-underscore
name), exactly as `_MODEL_BY_FAMILY` and `_provenance_bundle` are private in
the Phase 137E prototype. `path` is the caller-supplied path identity, used
by this function only as a display/provenance value and never re-read by
it (TAMPC-REQ-180). `artifact_bytes` is the exact, already-read bytes this
function treats as authoritative for that invocation (TAMPC-REQ-181).
`json_output` SHALL be accepted but SHALL NOT alter the returned value's
content (TAMPC-REQ-182).

### 5.1 Artifact-Read Ownership Split (added by Phase 137M)

This subsection resolves Finding F-1 (Phase 137L): TAMPC-001 v1.0 froze
`inspect_artifact_at_path`'s signature as `(path, *, json_output)`, which a
literal reading requires the function to perform its own file read, while
Section 6's failure categories and TAMPC-REQ-042's "read exactly once"
requirement are silent on which module performs that read. Phase 137K
implemented a CLI-owned Stage 1 bounded read with the bytes handed to
orchestration via a third parameter, `artifact_bytes`, not present in the
frozen signature — an undocumented but architecturally necessary deviation,
since the alternative (orchestration re-reading the file) would violate
TAMPC-REQ-038/042's single-read/TOCTOU requirement once the CLI layer has
already read it for its own Section 6 checks. TAMPC-REQ-179–TAMPC-REQ-182
make this split explicit and normative, matching the shipped, verified
137K implementation exactly; no implementation change is required by this
repair (Section 36).

TAMPC-REQ-179: `src/pcae/commands/authority_inspect.py` SHALL own the
Section 6 explicit-input checks (existence, file-type, readability, size)
and SHALL perform the single full artifact read into an immutable `bytes`
object, exactly once per invocation, before calling
`inspect_artifact_at_path`. This read, and no other, satisfies
TAMPC-REQ-042's "read exactly once" requirement.

TAMPC-REQ-180: `inspect_artifact_at_path` SHALL perform no filesystem read
of the artifact at `path`; it SHALL treat the caller-supplied
`artifact_bytes` as the exact, complete bytes of that artifact and SHALL
NOT re-stat, re-open, or re-read `path` for that invocation. This does not
relax TAMPC-REQ-042/TAMPC-REQ-038's single-read/TOCTOU requirement — it
assigns the one permitted read to the CLI layer (TAMPC-REQ-179) rather than
to orchestration.

TAMPC-REQ-181: A read-failure category from Section 6/17
(`input_not_found`, `input_not_a_file`, `input_unreadable`, or the
size/emptiness branches of `malformed_artifact`) SHALL be produced by the
CLI layer, before `inspect_artifact_at_path` is ever called, using the
same `InspectionFailure` type and the same failure-category identifiers
Section 17 fixes; `inspect_artifact_at_path` is never invoked for an
artifact that fails a Section 6 check.

TAMPC-REQ-182: `json_output`, present in `inspect_artifact_at_path`'s
signature for CLI-caller symmetry and future-caller compatibility only,
SHALL NOT select, branch, or otherwise change any part of the returned
`InspectionOutcome`'s content, restating TAMPC-REQ-105's human/JSON field-
parity requirement as a binding constraint on this parameter specifically.
Output-mode rendering remains owned exclusively by the CLI layer
(Section 16).

TAMPC-REQ-024: No module other than `src/pcae/commands/authority_inspect.py`
and test modules SHALL import an internal (leading-underscore) name from
`src/pcae/cltr/authority_inspection.py`.

TAMPC-REQ-025: The dependency direction SHALL be exactly:

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

TAMPC-REQ-026: `src/pcae/cltr/authority_inspection.py` SHALL NOT import
`src/pcae/commands/authority_inspect.py` or any other command module. No
Stage 3 module (`pcae.schema_runtime.*`, `pcae.cltr.authority.*`) SHALL
import `src/pcae/cltr/authority_inspection.py` or
`src/pcae/commands/authority_inspect.py`. No circular import SHALL exist.

TAMPC-REQ-027: `authority_inspection.py` MAY import: `pcae.cltr.authority`
(all sixteen family classes and `OpaqueJsonValue`),
`pcae.cltr.authority.errors`, `pcae.cltr.authority.serialization`,
`pcae.schema_runtime` (parser, registry, manifest, validator,
`OutcomeStatus`, `limits`), `pcae.schema_resources` (for
`cltr_cutover_root`, Section 8), and the standard library only
(`dataclasses`, `hashlib`, `pathlib`, `types.MappingProxyType`, `typing`).

TAMPC-REQ-028: `authority_inspection.py` and `authority_inspect.py` SHALL
NOT import: `pcae.core.tasks`, `pcae.core.session`, any other module under
`pcae.commands`, `pcae.cltr.shadow`, `pcae.cltr.inspection`,
`pcae.cltr.migration`, `pcae.cltr_prototype`,
`prototypes.typed_authority_inspector`, or any lifecycle, runtime,
notification, or publication module. The production module SHALL NOT wrap,
subclass, delegate to, or otherwise depend on the Phase 137E prototype
module.

## 6. Explicit-Input Contract

TAMPC-REQ-029: The consumer SHALL require exactly one explicit,
caller-supplied local artifact path per invocation, supplied as the
`path` positional argument.

TAMPC-REQ-030: The consumer SHALL NOT search for an artifact, infer a
default artifact, inspect repository state automatically, derive a path
from lifecycle or task state, use current-phase metadata as input,
dereference an unrelated record, or follow an ambient `*_reference`/
`*_references` value as an additional input source.

TAMPC-REQ-031: A missing `path` argument SHALL cause `argparse`-level
usage failure with a non-zero exit status distinct in kind from every
`InspectionFailure` category (Section 18).

TAMPC-REQ-032: A nonexistent path SHALL produce failure category
`input_not_found` (Section 17).

TAMPC-REQ-033: A directory path, FIFO, socket, or device-file path SHALL
produce failure category `input_not_a_file`, determined via
`Path.is_file()` before any `open()` call.

TAMPC-REQ-034: A symlink path SHALL be checked using its OS-resolved real
path for size and type; no elevated trust SHALL be given to a symlink
target, and no dedicated "symlink" failure category SHALL exist — a
symlink resolving to a regular, readable, correctly sized file SHALL be
inspected exactly as any other path; a symlink resolving to a missing,
non-regular, or unreadable target SHALL produce `input_not_found`,
`input_not_a_file`, or `input_unreadable` respectively, matching the
target's actual condition. A broken symlink SHALL produce
`input_not_found`.

TAMPC-REQ-035: An unreadable file (`PermissionError`/`OSError` at read
time) SHALL produce failure category `input_unreadable`, with the
underlying OS error text never echoed (Section 22).

TAMPC-REQ-036: An empty file (zero bytes) SHALL produce failure category
`malformed_artifact`, since a zero-length input can never be a strict JSON
object.

TAMPC-REQ-037: An oversized file (Section 7) SHALL produce failure
category `malformed_artifact`, determined before the file is read into
memory.

TAMPC-REQ-038: A file that changes on disk during or after the single read
performed by this consumer SHALL have no effect on that invocation's
result (Section 7, TOCTOU policy); no re-read, re-stat, or partial-read
retry SHALL occur.

## 7. Artifact Read Contract

TAMPC-REQ-039: The supported encoding SHALL be UTF-8 only; a decode
failure SHALL produce `malformed_artifact`.

TAMPC-REQ-040: The supported serialization format SHALL be exactly one
strict JSON object per artifact, parsed via
`pcae.schema_runtime.parse_strict_json(..., require_top_level_object=True)`,
unchanged from the Phase 137E prototype's own reuse of that parser.

TAMPC-REQ-041: The maximum input size SHALL be
`pcae.schema_runtime.limits.DEFAULT_MAX_INPUT_BYTES` (5 MiB at the time of
this freeze), enforced via `os.stat()`/`Path.stat()` on the resolved path
**before** the file's bytes are read into memory. A file whose reported
size exceeds this ceiling SHALL fail as `malformed_artifact` without an
`open()` call.

TAMPC-REQ-042: The file SHALL be read exactly once, fully, into an
immutable `bytes` object, before any parsing, validation, or dispatch
begins. No transition after this read SHALL touch the filesystem again for
that invocation (TOCTOU policy, restating TAMPC-REQ-038). This single read
is owned by the CLI layer per TAMPC-REQ-179; orchestration's receipt of
the resulting bytes via the `artifact_bytes` parameter (TAMPC-REQ-180) is
not a second read.

TAMPC-REQ-043: Duplicate JSON object keys SHALL be rejected by
`parse_strict_json`'s existing strict, duplicate-key-rejecting behavior,
unchanged; a duplicate key SHALL produce `malformed_artifact`.

TAMPC-REQ-044: Malformed Unicode SHALL produce `malformed_artifact`.

TAMPC-REQ-045: Trailing data after the top-level JSON value SHALL produce
`malformed_artifact`, per `parse_strict_json`'s existing behavior.

TAMPC-REQ-046: The only supported top-level JSON type is a single JSON
object; any other top-level type (array, string, number, boolean, null)
SHALL produce `malformed_artifact`.

TAMPC-REQ-047: The consumer SHALL NOT perform any automatic normalization,
coercion, or partial interpretation of a malformed artifact. Every
malformed-input path SHALL fail closed with no partial output (Section 16).

## 8. Stage 3 Resource Resolution Contract

TAMPC-REQ-048: The consumer SHALL resolve the Stage 3 schema package root
and manifest exclusively via the existing packaged-resource helper
`pcae.schema_resources.cltr_cutover_root()` (a context manager already
shipped in the wheel, defined in `src/pcae/schema_resources/__init__.py`,
resolving `importlib.resources.files(__package__) / "cltr_cutover"`). The
manifest path SHALL be `cltr_cutover_root() / "manifest.json"`, and the
manifest schema identity SHALL be the frozen constant
`"https://pcae.local/schemas/cltr_cutover/manifest.schema.json"`. No new
resolution helper SHALL be authored; this consumer is the first real
production caller of `cltr_cutover_root()`, and 137J/137K SHALL reuse it
exactly as fixed here.

TAMPC-REQ-049: The consumer SHALL NOT accept a caller-supplied schema
package path, registry path, manifest path, model module path, class name,
or import path via any CLI flag, environment variable, or configuration
file. This is the one deliberate, architected departure from the Phase
137E prototype's caller-supplied `package_root`/`manifest_path` (Phase
137G Section 2.4, Section 5.7).

TAMPC-REQ-050: Resource resolution SHALL work identically offline, from a
built wheel, from an sdist-installed package, and from an editable
install (`pip install -e .`), with no network access at any point.

TAMPC-REQ-051: If `cltr_cutover_root()` cannot yield a usable path (the
packaged resource is missing or the package installation is corrupted),
the consumer SHALL fail closed as `registry_failure`, with no raw
`ImportError`/`FileNotFoundError` text echoed (Section 22).

TAMPC-REQ-052: A corrupted manifest or registry resource (failing its own
`ManifestIntegrityError`/`SchemaRegistryError` verification, unchanged
Stage 3 behavior) SHALL fail closed as `manifest_failure` or
`registry_failure` respectively (Section 17), never partially trusted.

TAMPC-REQ-053: The consumer SHALL NOT implement a filesystem-search
fallback or a dynamic import driven by any value read from the artifact
being inspected.

## 9. Family Resolution Contract

TAMPC-REQ-054: The family discriminator SHALL be the artifact's own
`record_type` field, a JSON string, read only after schema-independent
strict JSON parsing succeeds (Section 7).

TAMPC-REQ-055: Family resolution SHALL use a static, private,
module-level dict literal in `authority_inspection.py` (the production
analog of the prototype's `_MODEL_BY_FAMILY`), binding each of the sixteen
family strings in Section 2 (TAMPC-REQ-007) to its existing, frozen
`pcae.cltr.authority.*` model class. No dynamic class resolution, string-to-import-path
construction, or `getattr` chain SHALL be used.

TAMPC-REQ-056: A `record_type` value that is not a string, or that is a
string absent from the dispatch table, SHALL produce failure category
`unknown_record_family`.

TAMPC-REQ-057: A missing `record_type` field SHALL also produce
`unknown_record_family` (a missing discriminator is a special case of an
unrecognized one, not a distinct category).

TAMPC-REQ-058: After family resolution, the consumer SHALL filter the
verified manifest's `entries` list to those whose `family` field equals
the resolved family and whose `file_path` begins with `records/`. Exactly
one such entry SHALL resolve; zero or more than one SHALL fail closed as
`manifest_entry_missing`, unchanged from the Phase 137E prototype's own
behavior and Phase 137G's NB-2 disposition (Section 17, TAMPC-REQ-108).

TAMPC-REQ-059: The one-entry-per-family invariant SHALL be checked
explicitly by the count assertion in TAMPC-REQ-058, never assumed
implicitly; 137J/137K SHALL add a dedicated regression test asserting this
invariant against the live manifest (Section 29).

TAMPC-REQ-060: A `schema_id` declared on the artifact that does not equal
the resolved manifest entry's `schema_id` SHALL fail closed as
`family_identity_mismatch`.

## 10. Validation Ownership Contract

TAMPC-REQ-061: The consumer SHALL perform exactly two of TAMC-001's five
validation classes: **schema validation** (via
`pcae.schema_runtime.validate_record_shape`, Draft 2020-12, frozen Stage 3
owner) and **model validation** (via each family's own frozen
`from_dict`/`__post_init__` construction, frozen Stage 3 owner, plus the
consumer's own lossless `to_dict()` round-trip equality check).

TAMPC-REQ-062: The consumer SHALL NOT perform, and SHALL NOT claim to have
performed, semantic validation, lifecycle validation, or governance
validation. Every output (Section 16) SHALL report these three classes as
the literal string `"not_performed"`, unconditionally, exactly as the
Phase 137E prototype's `to_dict()` already hardcodes them.

TAMPC-REQ-063: The consumer SHALL NOT substitute model validation for
schema validation, or schema validation for provenance checks. Each of the
two performed validation classes SHALL be reported as a distinct,
separately labeled output field (Section 16).

TAMPC-REQ-064: Exactly one owner is assigned per validation step: schema
validation is owned by `pcae.schema_runtime.validate_record_shape`; model
validation is owned by the resolved family's own `from_dict`/
`__post_init__`; the lossless round-trip check is owned by
`authority_inspection.py` itself, comparing `model.to_dict()` against the
originally parsed record for exact equality.

## 11. Deserialization Contract

TAMPC-REQ-065: Schema validation SHALL occur before model construction is
attempted; a schema validation failure SHALL short-circuit before
`Family.from_dict()` is ever called.

TAMPC-REQ-066: Model construction SHALL use the family resolved in Section
9 (TAMPC-REQ-055); no other model class SHALL ever be constructed for a
given artifact.

TAMPC-REQ-067: `schema_version` SHALL be compared, as an exact string
equality, against the frozen literal `SUPPORTED_SCHEMA_VERSION = "1.0"` and
against the resolved manifest entry's own `schema_version`; any mismatch
SHALL produce `unsupported_schema_version`.

TAMPC-REQ-068: `contract_version` (the typed-model contract version) SHALL
be compared, as an exact string equality, against the frozen literal
`SUPPORTED_MODEL_VERSION = "1.0"`; any mismatch SHALL produce
`unsupported_model_version`.

TAMPC-REQ-069: An unknown field present in the artifact SHALL be handled
exactly as the frozen Stage 3 schema and model already handle it (rejected
by schema validation if the schema is `additionalProperties: false`, or
preserved verbatim if the schema permits it); the consumer SHALL NOT add
its own unknown-field policy layered on top of the frozen Stage 3 behavior.

TAMPC-REQ-070: A missing required field SHALL be rejected by schema
validation (`schema_validation_failed`) or by model construction
(`model_validation_failed`), per the frozen Stage 3 owner's own existing
behavior; the consumer SHALL NOT fill, infer, or default a missing
required field.

TAMPC-REQ-071: An extension field (`extensions`, `opaque`, `limitations`,
`uncertainty`) present in the artifact SHALL be copied verbatim into
`record_claims`/`provenance` (Section 14) and never interpreted.

TAMPC-REQ-072: The consumer SHALL NOT perform type conversion (e.g.
string-to-number coercion) on any field value; a type mismatch SHALL be
rejected by schema validation exactly as the frozen schema already
specifies.

TAMPC-REQ-073: The consumer SHALL NOT supply a default value for any
field the frozen Stage 3 model does not itself define a default for.

TAMPC-REQ-074: After model construction succeeds, `model.to_dict()` SHALL
be compared for exact equality against the originally parsed record; any
inequality SHALL produce `required_provenance_failed` (a lossless
round-trip failure), unchanged from the Phase 137E prototype.

## 12. Observation Contract

TAMPC-REQ-075: The consumer's exposed observation types,
`InspectionObservation` and `InspectionFailure`, SHALL be implemented as
`@dataclass(frozen=True, slots=True)` value objects.

TAMPC-REQ-076: Every nested, JSON-shaped field on `InspectionObservation`
(`manifest_entry`, `registry_resource`, `schema_validation`,
`model_validation`, `record_claims`, `provenance`) SHALL be an
`OpaqueJsonValue` instance (the existing, frozen, deeply immutable Stage 3
carrier type), never a raw `dict`/`list`, unchanged from the Phase 137E
prototype's own use of `OpaqueJsonValue` for the identical purpose.

TAMPC-REQ-077: Every list-shaped, non-`OpaqueJsonValue`-wrapped field, if
any is introduced by 137J/137K, SHALL be a `tuple`, never a `list`.

TAMPC-REQ-078: `InspectionObservation` and `InspectionFailure` SHALL each
define an explicit `__setattr__` and `__delattr__` override that
unconditionally raises `dataclasses.FrozenInstanceError`, in addition to
(not instead of) `frozen=True`. This is defense-in-depth against a future
refactor accidentally weakening `frozen=True`; it does not, and is not
claimed to, prevent a caller who deliberately invokes
`object.__setattr__(instance, ...)`. That residual bypass is explicitly
out of TAMC-001's threat model (restating the Phase 137F NB-1 disposition
verbatim: it requires a downstream caller intentionally reaching for
`object.__setattr__`, an adversarial or grossly negligent act, not an
accidental one) and is not required to be defeated by TAMPC-001 v1.0.
Section 29 requires a mutation-attempt test proving the ordinary-assignment
path (`instance.field = value`) is blocked; it does not require a test
proving `object.__setattr__` itself is blocked, since no pure-Python
mechanism can guarantee that without abandoning `dataclass` ergonomics
entirely, which Phase 137G's own Section 14 explicitly permits avoiding.

TAMPC-REQ-079: No caller-visible mutable alias SHALL be returned: every
accessor either returns an immutable value directly (`str`, `OpaqueJsonValue`,
`tuple`) or is itself immutable.

TAMPC-REQ-080: `InspectionObservation` and `InspectionFailure` SHALL define
deterministic `__eq__` and `__repr__` (the `dataclass`-generated
implementations, unmodified), so that two observations of byte-identical
input are equal and render identically.

## 13. Observation Meaning Contract

TAMPC-REQ-081: A successful observation (`outcome: "inspected"`, exit code
0) SHALL mean only: the explicit artifact was read; its family was
recognized; supported schema and model versions were resolved; schema
validation and model construction (including the lossless round-trip)
succeeded; provenance was preserved per Section 14; and a deterministic
observation was produced.

TAMPC-REQ-082: A successful observation SHALL NOT mean: the artifact is
authoritative; the represented event occurred; any authorization,
certification, or publication referenced in the artifact is valid or
effective; any cutover or recovery referenced in the artifact is approved
or permitted; lifecycle state changed; or runtime permission exists.

TAMPC-REQ-083: Every invocation, success or failure, SHALL print the fixed,
unconditional, non-suppressible representation-only disclosure string as a
dataclass default (never a computed branch), exactly as the Phase 137E
prototype's `REPRESENTATION_ONLY_DISCLOSURE` default.

## 14. Provenance Contract

TAMPC-REQ-084: The consumer SHALL preserve, for every successful
observation, at minimum: source artifact identity (the caller-supplied
path, copied); artifact digest (`input_digest`, SHA-256 of the exact bytes
read); record identity (`record_id`, copied); family identity
(`record_type`, copied); schema identity and version (`schema_id`/
`schema_version`, copied); model identity and version (model class name,
derived from dispatch; `contract_version`, copied); registry identity
(the resolved `resource_info`, reported as an observation); manifest
identity (the resolved manifest entry, reported as an observation);
derivation steps (an explicit `derivation` map distinguishing copied from
derived fields); validation outcomes (distinct schema/model outcome
objects, plus the fixed `"not_performed"` markers for semantic/lifecycle/
governance); and limitations/uncertainty (any `limitations`,
`uncertainty`, `opaque`, `extensions`, or `*_reference(s)` field present in
the artifact, copied verbatim).

TAMPC-REQ-085: Each provenance field SHALL be classified, in this
contract, as exactly one of: **sourced** (copied unchanged from the
artifact or the CLI invocation), **deterministically derived** (computed
by this consumer or a frozen Stage 3 owner from sourced values), or
**unavailable/prohibited from inference** (absent from the artifact,
reported as absent, never fabricated). The classification for every field
in TAMPC-REQ-084 is: source artifact identity — sourced; artifact digest
— derived; record/family/schema/model identity and version — sourced;
registry/manifest identity — derived; derivation steps — derived;
validation outcomes for schema/model — derived; validation outcomes for
semantic/lifecycle/governance — unavailable/prohibited from inference
(fixed as `"not_performed"`); limitations/uncertainty — sourced if present,
unavailable if absent.

TAMPC-REQ-086: No provenance field listed in TAMPC-REQ-084 SHALL be
silently discarded by any output mode (Section 16); this table is
definitionally exhaustive for what the consumer touches, and no field SHALL
be added later without a governed contract revision (Section 33).

## 15. Digest Contract

TAMPC-REQ-087: The digest algorithm SHALL be SHA-256.

TAMPC-REQ-088: `input_digest` SHALL be computed over the exact `bytes`
object read from the artifact path (Section 7, TAMPC-REQ-042), before any
parsing, and SHALL never be recomputed from reserialized or canonicalized
content.

TAMPC-REQ-089: If the underlying file changes after the single read
(Section 7 TOCTOU policy), `input_digest` SHALL reflect only the bytes
actually read for that invocation; no re-read or re-digest SHALL occur.

TAMPC-REQ-090: `input_digest` SHALL be encoded as lowercase hexadecimal,
matching `hashlib.sha256(...).hexdigest()`'s existing output convention,
unchanged from the Phase 137E prototype.

TAMPC-REQ-091: `declared_record_digest` (the artifact's own self-declared
`record_digest` field) SHALL be reported as a distinct field, copied
verbatim, never merged with or compared against `input_digest`. These two
fields measure different things — the transport bytes versus the record's
self-declared digest — and TAMPC-001 v1.0 defines no comparison between
them; there is no `digest_mismatch` failure category for this pair.

TAMPC-REQ-092: Manifest digest verification (comparing each schema
resource file's actual SHA-256 against the manifest's claimed
`file_digest`) remains owned, unchanged, by
`pcae.schema_runtime.load_and_verify_manifest`; a manifest digest
mismatch SHALL surface through that owner's existing
`ManifestIntegrityError`, mapped to failure category `manifest_failure`
(Section 17). The consumer SHALL NOT independently recompute or verify a
manifest entry's digest.

## 16. Output Contract

TAMPC-REQ-093: v1.0 SHALL support both human-readable output (default) and
machine-readable JSON output (`--json`), matching the existing `cltr
shadow`/`cltr-prototype` CLI convention.

TAMPC-REQ-094: JSON output SHALL be rendered via
`json.dumps(payload, indent=2, sort_keys=True, default=str)`, matching
`cltr_shadow.py`'s existing convention exactly.

TAMPC-REQ-095: Human-readable output SHALL iterate fields in a fixed,
contract-frozen order (matching the field order of TAMPC-REQ-084), never
Python dict insertion order.

TAMPC-REQ-096: `copied_provenance_values` and every other list-valued
field SHALL be sorted deterministically, by `instance_path`, exactly as
the Phase 137E prototype's `_collect_named_values`.

TAMPC-REQ-097: The output schema version SHALL be reported explicitly as
the TAMC contract version (`"1.0"`) and, once fixed, the TAMPC output
contract version (`"1.0"`); a future contract revision that changes output
shape SHALL bump the relevant value.

TAMPC-REQ-098: An absent optional field SHALL be reported as an explicit
absence marker (the frozen `"unavailable"` sentinel, unchanged from the
Phase 137E prototype's `UNAVAILABLE` constant), never omitted silently and
never rendered as JSON `null` in place of that sentinel.

TAMPC-REQ-099: Output SHALL never include raw OS exception text, an
internal package-root or manifest path, or any secret-shaped value
(Section 22).

TAMPC-REQ-100: Every provenance field required by Section 14 SHALL be
rendered in both output modes, including `input_digest` and
`declared_record_digest` as two distinct, separately labeled fields
(Section 15).

TAMPC-REQ-101: `schema_version` and `model_version` (the typed-model
contract version) SHALL always be shown, on both success and, where known,
on failure.

TAMPC-REQ-102: Schema and model validation outcomes SHALL be shown as two
distinct keys (`validation.schema`, `validation.model`), plus the fixed
`"not_performed"` markers for `validation.semantic`,
`validation.lifecycle`, and `validation.governance`, unchanged from the
prototype's `to_dict()`.

TAMPC-REQ-103: Output SHALL disclose, in every invocation: that it
inspects exactly one explicit file; that it performs no repository
discovery; and that the representation is not an authority determination
(the fixed disclosure string, TAMPC-REQ-083).

TAMPC-REQ-104: Output SHALL NOT imply authority, approval, authorization,
certification effectiveness, lifecycle completion, or runtime permission,
restating TAMPC-REQ-082 as a binding output-rendering constraint.

TAMPC-REQ-105: Human-readable and `--json` output SHALL carry identical
field content; only presentation SHALL differ between the two modes. There
is no "success with warning" state: an invocation is either `inspected`
(exit 0) or one `InspectionFailure` category (exit 1); no third,
ambiguous state SHALL exist.

TAMPC-REQ-106: Machine-readable (`--json`) output is the stable, versioned
contract surface (TAMPC-REQ-097); human-readable output SHALL NOT be
treated as canonical evidence by any future integration.

## 17. Error Taxonomy Contract

TAMPC-REQ-107: The consumer SHALL use the existing repository convention
of stable, lowercase, `snake_case` failure-category identifiers (matching
`pcae.schema_runtime`'s and the Phase 137E prototype's own already-frozen
taxonomy strings), rather than introducing a new `UPPER_SNAKE_CASE`
convention. The frozen v1.0 failure categories, and the category each
maps to when compared against the governing phase brief's illustrative
list, are:

| Stable identifier | Meaning | Brief's illustrative category (if distinct) |
|---|---|---|
| `input_not_found` | Path does not exist, or resolves to a broken symlink | `INPUT_NOT_FOUND` |
| `input_not_a_file` | Path is a directory, FIFO, socket, or device file | `INPUT_IS_DIRECTORY` / `INPUT_TYPE_UNSUPPORTED` |
| `input_unreadable` | `PermissionError`/`OSError` at read time | `INPUT_UNREADABLE` |
| `malformed_artifact` | Oversized, empty, non-UTF-8, non-JSON, non-object, duplicate-key, or trailing-data input | `INPUT_TOO_LARGE` / `ARTIFACT_EMPTY` / `ARTIFACT_ENCODING_INVALID` / `ARTIFACT_JSON_INVALID` / `ARTIFACT_DUPLICATE_KEY` |
| `unknown_record_family` | `record_type` missing, non-string, or not in the dispatch table | `FAMILY_MISSING` / `FAMILY_UNKNOWN` |
| `manifest_entry_missing` | Zero or more than one manifest entry resolves for the declared family | `FAMILY_AMBIGUOUS` |
| `unsupported_schema_version` | `schema_version` is not the pinned supported literal | `SCHEMA_VERSION_UNSUPPORTED` |
| `unsupported_model_version` | `contract_version` is not the pinned supported literal | `MODEL_VERSION_UNSUPPORTED` |
| `registry_failure` | The offline registry cannot be built, or the packaged Stage 3 resource is missing/corrupted | `REGISTRY_RESOURCE_MISSING` |
| `registry_entry_missing` | The registry has no entry for the declared `schema_id` | `REGISTRY_MISMATCH` |
| `manifest_failure` | The manifest fails frozen shape/digest/completeness verification | `MANIFEST_RESOURCE_MISSING` / `MANIFEST_MISMATCH` / `DIGEST_MISMATCH` (manifest-entry digest only, Section 15) |
| `family_identity_mismatch` | Declared `record_type`/`schema_id` disagree with the resolved manifest entry | Not separately named in the brief; treated as an `INTERNAL_CONTRACT_VIOLATION` subtype |
| `schema_validation_failed` | Draft 2020-12 shape validation fails | `SCHEMA_VALIDATION_FAILED` |
| `model_validation_failed` | Typed-model construction (`from_dict`) fails | `MODEL_VALIDATION_FAILED` |
| `required_provenance_failed` | Lossless round-trip inequality, or a required identity/version/digest field is unavailable after construction | `PROVENANCE_INVALID` |

TAMPC-REQ-108: `MANIFEST_FAMILY_DUPLICATE` and `INTERNAL_CONTRACT_VIOLATION`
from the governing brief's illustrative list are not separate stable
identifiers in v1.0: a duplicate family entry is a `manifest_entry_missing`
case (TAMPC-REQ-058, more-than-one-entry branch), and no other internal
contract violation is reachable given TAMPC-REQ-055's static dispatch
table; this equivalence is an explicit, governed design decision, not an
omission.

TAMPC-REQ-109: For every failure category in TAMPC-REQ-107: the stable
identifier SHALL be the process's only public description of the failure
kind; the exit code SHALL be `1`; failure output SHALL go to stdout in
`--json` mode and to stdout in human-readable mode (matching the existing
`cltr_shadow.py` convention of writing outcome content, success or
failure, to stdout, with a non-zero exit code as the machine-checkable
signal — no separate stderr channel is introduced for this consumer);
detail exposure SHALL follow the "details exposed" column already fixed by
Phase 137G Section 10 (path-only, generic-description-only, or
owner-provided-structured-issues, per category); no partial output SHALL
be produced for any failure; and every raw OS/library exception SHALL be
suppressed and replaced by the category's fixed, generic message, except
where the category's detail is itself the artifact's own declared value
(e.g. `unknown_record_family` MAY report the declared family string,
since that string originates from the artifact the user themselves
supplied, not from an internal exception).

TAMPC-REQ-110: No silent fallback and no automatic repair SHALL exist for
any failure category.

TAMPC-REQ-111: Failure precedence SHALL be fixed as: input existence/type/
readability checks (Section 6) → bounded read and parse (Section 7) →
explicit CLI-supplied context validation → registry resolution (Section
8) → manifest verification (Section 8) → family/version/identity
resolution (Sections 9, 11) → schema validation (Section 10) → model
validation (Section 10) → lossless round-trip check (Section 11). An
artifact with multiple simultaneous defects SHALL always produce the
failure category of the first check in this order that it fails, on every
run.

## 18. Exit-Code Contract

TAMPC-REQ-112: Exit code `0` SHALL mean, and only mean, `outcome:
"inspected"` (Section 13).

TAMPC-REQ-113: Exit code `1` SHALL mean any `InspectionFailure` category
from Section 17.

TAMPC-REQ-114: A distinct exit code for invalid CLI invocation (missing
`path` argument, unknown flag) SHALL be whatever `argparse`'s existing
usage-error exit code already is for every other `pcae` subcommand
(conventionally `2`); this is unchanged, existing CLI framework behavior,
not a new contract obligation.

TAMPC-REQ-115: No distinct exit code per `InspectionFailure` category
SHALL exist in v1.0; a richer, per-category exit-code scheme is future
extensibility and is not authorized by this contract.

TAMPC-REQ-116: The consumer SHALL NOT expose a Python exception type,
traceback, or exception class name as part of the public exit-code
contract; every reachable exception SHALL be caught and translated to one
of Sections 17–18's stable outcomes before the process exits.

## 19. Determinism Contract

TAMPC-REQ-117: Identical unchanged artifact bytes, an identical installed
`pcae` version, and identical invocation options SHALL produce
semantically identical output on every invocation, on every supported
platform.

TAMPC-REQ-118: Field ordering, family resolution, registry ordering,
manifest ordering, validation-error ordering, provenance ordering,
error-code selection, rendering, and exit status SHALL each be
deterministic, per Sections 9, 16, and 17's fixed rules.

TAMPC-REQ-119: No deterministic observation output SHALL include a
timestamp, a random identifier, a process identifier, environment-
dependent ordering, or locale-dependent formatting. No network-dependent
behavior SHALL exist anywhere in the consumer.

TAMPC-REQ-120: Two different paths containing byte-identical artifact
content SHALL produce identical `record_claims`/provenance/validation
output; only `source_artifact_identity` (the path itself) SHALL differ.

## 20. Idempotence and Replay Contract

TAMPC-REQ-121: Repeated inspection of the same unchanged artifact SHALL
produce no mutation, no persistence, no additional authority, no
lifecycle effect, no runtime effect, and semantically identical output on
every invocation.

TAMPC-REQ-122: The consumer SHALL NOT record, anywhere, that a given
artifact was inspected. No in-memory or on-disk cache SHALL exist across
invocations; each invocation is a fresh process with no carried state.

## 21. Side-Effect Contract

TAMPC-REQ-123: Inspection consumption SHALL be side-effect free. The only
permitted process effects are: reading the one explicit artifact path
(Section 6); reading installed Stage 3 package resources (Section 8);
writing output to stdout (Section 16); and returning a process exit
status (Section 18).

TAMPC-REQ-124: The consumer SHALL NOT write a file, change a file's
permissions or metadata, acquire a lifecycle lock, write a log that
becomes authority evidence, send a notification, perform network activity,
spawn a subprocess, mutate an environment variable, mutate any repository
state, or create a cache of any kind.

## 22. Security Contract

TAMPC-REQ-125: The artifact at the caller-supplied path is untrusted local
input; it SHALL be size-checked (Section 7) and type-checked (Section 6)
before any parse is attempted.

TAMPC-REQ-126: Parser safety SHALL be inherited unchanged from
`pcae.schema_runtime.parse_strict_json`; no new parser SHALL be authored.

TAMPC-REQ-127: Duplicate JSON keys SHALL be rejected (TAMPC-REQ-043).

TAMPC-REQ-128: No unsafe dynamic import and no unsafe class resolution
from artifact-controlled data SHALL exist; family dispatch SHALL remain a
static dict literal (TAMPC-REQ-055).

TAMPC-REQ-129: No unsafe deserialization mechanism (e.g. `pickle`,
`eval`, `exec`) SHALL be used anywhere in the consumer.

TAMPC-REQ-130: Symlink targets SHALL receive no elevated trust
(TAMPC-REQ-034); the consumer opens exactly one resolved path once and
never walks a directory tree, so multi-file symlink-traversal attacks do
not apply.

TAMPC-REQ-131: Path disclosure in output SHALL be limited to the one path
the invoking user themselves supplied on their own command line; internal
package-root, registry, or manifest paths SHALL never be echoed.

TAMPC-REQ-132: Exception text from `OSError`, `ManifestIntegrityError`,
`SchemaRegistryError`, `TypedModelError`, or any other library exception
SHALL never be echoed verbatim; each failure category (Section 17) carries
a fixed, generic, pre-written message.

TAMPC-REQ-133: Denial-of-service resistance SHALL be provided by the fixed
input-size ceiling (TAMPC-REQ-041), enforced before any bytes are handed
to the parser or the JSON-schema validator, independent of whatever
internal limits `pcae.schema_runtime.limits` already applies for its own
callers.

TAMPC-REQ-134: The registry and manifest SHALL be resolved only from the
installed package's own location (TAMPC-REQ-048); there SHALL be no CLI
flag, environment variable, or configuration mechanism to point the
consumer at an alternate schema package root, closing the substitution
vector the Phase 137E prototype's caller-suppliable `package_root`
deliberately left open for test isolation.

TAMPC-REQ-135: Schema substitution SHALL be prevented by the same
mechanism (TAMPC-REQ-134).

TAMPC-REQ-136: Provenance forgery resistance SHALL be inherited unchanged
from the frozen Stage 3 schema's `const: false` constraint on any
authority-disclosure field claiming `is_authoritative: true`; a forged
claim fails schema validation itself, independent of this consumer's own
logic.

TAMPC-REQ-137: Digest substitution SHALL be prevented by keeping
`input_digest` and `declared_record_digest` two distinct, never-merged
fields (Section 15).

TAMPC-REQ-138: No environment variable, working directory, or locale
setting SHALL influence dispatch, validation, or output content; only the
one OS-level file read (Section 6) touches the filesystem, and only for
the one caller-supplied path.

TAMPC-REQ-139: The consumer SHALL never execute artifact-controlled code,
and SHALL never gain write, network, or execution capability by virtue of
reading a record, restating TAMC-REQ-063.

## 23. Lifecycle Neutrality Contract

TAMPC-REQ-140: The consumer SHALL NOT determine phase completion, create
or write a phase report, modify `.pcae/phase-completion-metadata.json` or
any other phase-completion metadata, modify task state, write a marker or
receipt, authorize or send a notification, alter Architecture Status, or
participate in a finalization gate.

TAMPC-REQ-141: The consumer SHALL NOT import `pcae.core.tasks`,
`pcae.core.session`, any phase-report module, or any notification-dispatch
module (restating TAMPC-REQ-028).

TAMPC-REQ-142: Inspection output SHALL NOT be accepted as lifecycle
evidence merely because validation succeeded; the consumer itself asserts
no such acceptance, and no future surface may treat exit code 0 as a
completion signal without its own separately governed contract.

## 24. Runtime Neutrality Contract

TAMPC-REQ-143: The consumer SHALL NOT register an execution adapter,
become a runtime plugin, request execution permission via
`PermissionBroker`, activate a capability, dispatch work, schedule work,
mutate runtime context, or participate in a runtime enforcement decision.

TAMPC-REQ-144: The consumer SHALL NOT import
`pcae.core.runtime_introspection`, `pcae.core.runtime_snapshot`, any
`RuntimeRegistry` type, or any `PermissionBroker` module.

TAMPC-REQ-145: Runtime SHALL remain Observed / observe / unavailable both
before and after this contract's implementation; production packaging of
the consumer inside `src/pcae` SHALL NOT, by itself, alter runtime
capability.

## 25. Authority Neutrality Contract

TAMPC-REQ-146: Representation SHALL never establish authority. The
consumer SHALL NOT infer authority from record family, from successful
validation, from registry membership, from manifest membership, from
digest validity, or from provenance completeness; SHALL NOT calculate,
persist, resolve, transfer, or activate authority.

TAMPC-REQ-147: No output field (Section 16) SHALL be phrased or
structured in a way that could be misread as an authority signal; Section
13's meaning contract is the binding, exhaustive statement of what a
successful observation does and does not mean.

## 26. Compatibility and Versioning Contract

TAMPC-REQ-148: v1.0 SHALL support exactly schema version `"1.0"` and
typed-model contract version `"1.0"`, for all sixteen families, pinned as
literal constants (`SUPPORTED_SCHEMA_VERSION`, `SUPPORTED_MODEL_VERSION`),
unchanged from the Phase 137E prototype.

TAMPC-REQ-149: An unknown future schema or model version SHALL be
rejected (`unsupported_schema_version`/`unsupported_model_version`); no
nearby-version fallback or permissive-parsing behavior SHALL exist.

TAMPC-REQ-150: A new family SHALL require, in order: a new manifest entry,
schema, and model (Stage 3's own governed process), and then a separate,
governed revision to this consumer's dispatch table (TAMPC-REQ-055); until
both exist, the family produces `unknown_record_family`.

TAMPC-REQ-151: Adding a new family SHALL NOT change behavior or
classification for any already-supported family.

TAMPC-REQ-152: The consumer's own identity SHALL be reported in every
output as `CONSUMER_ID = "pcae-authority-inspect-v1"`.

TAMPC-REQ-153: Output SHALL explicitly include the TAMC contract version
(`"1.0"`) and the TAMPC output-contract version (`"1.0"`); a future
contract revision that changes output shape SHALL bump the relevant
value (restating TAMPC-REQ-097).

TAMPC-REQ-154: The failure-category strings fixed by Section 17 are the
stable contract surface; renaming one SHALL require a governed contract
revision (Section 33), never a silent code change.

TAMPC-REQ-155: A future TAMPC-001 revision SHALL identify its predecessor,
version, changed requirements, migration effect, affected consumer
classes, and backward-compatibility impact, per TAMC-REQ-067's process,
applied identically to TAMPC-001 itself. This consumer's contract does not
locally supersede TAMC-001.

## 27. Packaging Contract

TAMPC-REQ-156: `authority_inspection.py` and `authority_inspect.py` SHALL
be included in the built wheel and the sdist by virtue of residing under
`src/pcae/`, already covered by `pyproject.toml`'s `packages =
["src/pcae"]` scope; no `pyproject.toml` change is required for the module
files themselves.

TAMPC-REQ-157: The CLI SHALL be immediately available after
`pip install pcae-harness` with no additional setup step.

TAMPC-REQ-158: The consumer SHALL resolve `src/pcae/schema_resources/
cltr_cutover/` as packaged data via `cltr_cutover_root()`
(TAMPC-REQ-048), which already works under an editable install, a normal
install, and a built wheel per its own existing docstring guarantee.

TAMPC-REQ-159: No new runtime dependency SHALL be introduced; the
consumer SHALL use only what `pcae.schema_runtime`/`pcae.cltr.authority`
already require (`jsonschema`, already declared in `pyproject.toml`).

TAMPC-REQ-160: No production Python-version compatibility change SHALL be
required beyond what `pyproject.toml` already declares.

TAMPC-REQ-161: The consumer SHALL NOT rely on any repository-root-relative
path; all resource resolution SHALL be package-relative
(TAMPC-REQ-048–TAMPC-REQ-050).

TAMPC-REQ-162: `import pcae.cltr.authority_inspection` and `import
pcae.commands.authority_inspect` SHALL succeed with no lifecycle, runtime,
or notification side import (TAMPC-REQ-026, TAMPC-REQ-028), verifiable by
a static import-scan test (Section 29).

## 28. Python Environment Contract

TAMPC-REQ-163: All Python-based development, testing, packaging, and
verification for 137J/137K/137L SHALL use the repository virtual
environment explicitly: `.venv/bin/python`, `.venv/bin/python -m pytest`,
`.venv/bin/python -m pip`, `.venv/bin/python -m build`.

TAMPC-REQ-164: `/usr/bin/python3`, bare `python`, bare `python3`, bare
`pip`, bare `pytest`, a globally installed `pytest`, and dependency
installation into system Python SHALL NOT be used.

TAMPC-REQ-165: Before any Python validation step, interpreter provenance
SHALL be recorded via `.venv/bin/python -c 'import sys;
print(sys.executable); print(sys.prefix)'`, and the resolved interpreter
and prefix SHALL be confirmed to resolve inside the repository `.venv`.

TAMPC-REQ-166: If `.venv` is missing or unusable, implementation and
verification work SHALL stop and report the environment defect; no
dependency SHALL be installed until interpreter provenance is verified,
and no silent fallback to a different interpreter SHALL occur.

## 29. Testing Contract

TAMPC-REQ-167: 137J/137K/137L SHALL provide, at minimum: command-parsing
tests; one successful-inspection fixture per family for all sixteen
families, freshly constructed rather than reused verbatim from
`tests/test_typed_authority_inspector_137e.py`; malformed-input tests
(truncated, duplicate-key, non-object JSON); missing-input tests;
unsupported-file-type tests (directory, special file); symlink tests;
oversized-input tests; unknown-family tests; unsupported-version tests
(schema and model); registry-mismatch tests; manifest-mismatch tests;
manifest one-entry-per-family regression tests (TAMPC-REQ-059);
digest tests (both `input_digest` derivation and the
non-comparison stated in TAMPC-REQ-091); schema-validation tests;
model-validation tests; provenance-preservation tests (field-by-field
against Section 14's table); deep-immutability/mutation-attempt tests
(TAMPC-REQ-078's ordinary-assignment path); deterministic-output tests;
repeated-invocation tests; authority-neutrality tests (adversarial records
with `is_authoritative: true`/operative-looking `state` values); lifecycle-
neutrality tests (`pcae health`/`pcae check`/`pcae status coherence`/`pcae
doctor task-memory` unchanged before/after); runtime-neutrality tests
(`pcae runtime inspect` output identical before/after); side-effect tests;
exception-sanitization tests; wheel tests; sdist tests; offline-install
tests; editable-install tests; CLI exit-code tests; a Fast Green
regression pass; and directly-affected full-suite evidence.

TAMPC-REQ-168: Every fixture required by TAMPC-REQ-167 SHALL be freshly,
independently authored for 137K, not copied verbatim from
`tests/test_typed_authority_inspector_137e.py`'s existing fixture table,
per the demonstrated Phase 137F.1V lesson that a fresh, independently
authored fixture found live gaps a predecessor's own fixture table missed.

TAMPC-REQ-169: The implementation's own expected-value table SHALL NOT be
the sole oracle for any test in TAMPC-REQ-167; independent test authorship
is required.

## 30. Compliance Evidence Contract

TAMPC-REQ-170: 137J/137K/137L SHALL produce a traceability matrix mapping
every TAMPC-001 requirement ID, every applicable TAMC-001 requirement ID,
the corresponding Phase 137G architectural control, the implementation
component, the test evidence, the packaging evidence, and the verification
evidence.

TAMPC-REQ-171: No TAMPC-001 requirement SHALL be marked compliant without
concrete, cited evidence (a test name, a static-scan result, a packaging
run, or an equivalent artifact).

TAMPC-REQ-172: The traceability matrix SHALL cover every TAMC-001
requirement in the category ranges Phase 137G Section 21 already fixed
(001–021 Consumer Classification, 022–032 Consumer Invariants, 033–034
Ownership, 035–038 Authority, 039–041 Validation, 042–045 Provenance,
046–048 Runtime, 049–051 Lifecycle, 052–055 Error Handling, 056–059
Extensibility, 060–064 Security, 065–067 Compatibility, 068–069 No-Go,
070–076 Compliance/Verification), with no requirement ID from 001 through
076 left unmapped.

## 31. Production Integration Preconditions

TAMPC-REQ-173: Implementation (137J/137K) SHALL NOT begin until: TAMPC-001
v1.0 is frozen (this document); TAMPC-001 is independently verified
(137I) with no Blocking finding remaining; command identity is fixed
(Section 4); package boundary is fixed (Section 5); input contract is
fixed (Sections 6–7); output contract is fixed (Section 16); error
taxonomy is fixed (Section 17); exit codes are fixed (Section 18);
provenance contract is fixed (Section 14); deep immutability is fixed
(Section 12); manifest uniqueness validation is fixed (TAMPC-REQ-059);
security contract is fixed (Section 22); packaging contract is fixed
(Section 27); Python environment contract is fixed (Section 28); complete
traceability exists (Section 30); and runtime remains Observed / observe /
unavailable.

## 32. No-Go Contract

TAMPC-REQ-174: 137J/137K/137L SHALL NOT introduce: more than one
production consumer; a generic consumer framework; ambient artifact
discovery; repository-wide scanning; a caller-supplied schema, registry,
or manifest path; dynamic class loading; an authority resolver, pointer,
persistence mechanism, or activation path; lifecycle mutation; phase-
report creation; notification dispatch; runtime capability, an execution
adapter, or execution; publication, recovery, rollback, cutover,
compatibility execution, or quarantine execution; a semantic decision
engine; permissive unknown-version parsing; mutable public observation
state; a network dependency; or a repository-root-relative path
dependency.

TAMPC-REQ-175: Renaming, wrapping, splitting, deferring, or making
conditional any operation listed in TAMPC-REQ-174 SHALL NOT make it
compliant.

## 33. Contract Evolution

TAMPC-REQ-176: Any normative change to TAMPC-001 SHALL require a governed
contract revision: a version increment, an impact analysis, independent
verification, a compatibility assessment, and an updated traceability
matrix (Section 30).

TAMPC-REQ-177: Implementation phases (137J/137K) SHALL NOT reinterpret an
ambiguity in TAMPC-001 locally. Any ambiguity discovered during
implementation SHALL be returned to a dedicated contract-repair phase
before implementation proceeds past the ambiguous point.

TAMPC-REQ-178: A future TAMPC-001 revision SHALL NOT be introduced by any
phase whose authority is limited to production implementation
(137J/137K) or to independent verification (137I/137L); a contract
revision requires its own, separately authorized contract-freeze-class
phase.

## 34. Phase 137H freeze confirmation

Phase 137H freezes command identity, production package and dependency
boundaries, the explicit-input contract, the Stage 3 resource-resolution
mechanism (`pcae.schema_resources.cltr_cutover_root()`), family
resolution, validation ownership, deserialization behavior, the
immutability-hardening mechanism, provenance and digest behavior, output
and failure-taxonomy behavior, exit codes, determinism and replay
behavior, side-effect and security requirements, lifecycle/runtime/
authority neutrality, compatibility and versioning, packaging, the Python
environment requirement, testing and compliance-evidence requirements,
production-integration preconditions, No-Go conditions, and contract
evolution process, as TAMPC-001 v1.0.

No implementation is authorized by this freeze. No production consumer is
added. No `src/pcae/cltr/authority_inspection.py`,
`src/pcae/commands/authority_inspect.py`, CLI registration, production
test, Stage 3 schema, Stage 3 typed model, Stage 3 registry, Stage 3
manifest, TAMC-001, TAMP-001, or Phase 137E prototype file is created or
modified by this freeze. Runtime remains Observed / observe / unavailable.

## 35. Post-freeze next phase

**137I — Typed Authority Model Production Consumption Contract Independent
Verification** is the recommended next governed phase. It does not begin
through this contract; it requires a separately authorized task, and shall
independently re-derive and adversarially verify TAMPC-001 v1.0 — not
accepting this document's own claims as an oracle — before implementation
planning (137J) or production code (137K) is authorized.

## 36. Phase 137M signature-ambiguity repair confirmation

**Version:** 1.1
**Predecessor:** TAMPC-001 v1.0 (Phase 137H)
**Repaired by:** Phase 137M — TAMPC-001 Signature Ambiguity Contract Repair
**Reason:** Independently demonstrated Finding F-1 (Phase 137L, NOT
VERIFIED verdict) — TAMPC-REQ-023's frozen two-parameter signature
(`path`, `json_output`) does not match the shipped, tested, previously
verified-in-all-other-respects Phase 137K implementation's three-parameter
signature (`path`, `artifact_bytes`, `json_output`), a genuine ambiguity in
TAMPC-001 v1.0 never routed through TAMPC-REQ-177's contract-repair
process before 137K proceeded.

**Changed requirements:** TAMPC-REQ-021 (reworded, ownership cross-
reference added), TAMPC-REQ-022 (reworded, ownership cross-reference
added), TAMPC-REQ-023 (signature corrected to three parameters; explanatory
sentences added), TAMPC-REQ-042 (cross-reference sentence added, no
normative change). New requirements TAMPC-REQ-179 through TAMPC-REQ-182
(Section 5.1) added, making the CLI/orchestration artifact-read ownership
split explicit and normative. No other requirement (001–020, 024–041,
043–178) was modified.

**Migration effect:** None. This revision brings the contract text into
conformance with the already-shipped, already-tested 137K implementation
(Compatibility Review Outcome A, Section 5.1); it does not require any
change to `src/pcae/cltr/authority_inspection.py`,
`src/pcae/commands/authority_inspect.py`, or their test suites.

**Affected consumer classes:** None beyond the single production consumer
this contract already governs (TAMPC-REQ-004); no second consumer is
authorized by this revision (TAMPC-REQ-174 unchanged).

**Backward-compatibility impact:** None. The public CLI surface
(`pcae authority inspect <path> [--json]`), its output shape, its failure
taxonomy, and its exit codes are unchanged. The only surface previously
undocumented is `inspect_artifact_at_path`'s own Python signature, which
this revision now documents accurately.

No implementation, activation, or runtime-capability change is authorized
by this revision. Runtime remains Observed / observe / unavailable.

## 37. Post-repair next phase

**137MV — TAMPC-001 Signature Ambiguity Contract Repair Independent
Verification** is the recommended next governed phase. It shall
independently re-derive TAMPC-001 v1.1 from Finding F-1 and this repair's
own stated rationale — not accepting this document's own claims as an
oracle — confirm no second valid interpretation of
`inspect_artifact_at_path`'s signature remains, and confirm the Phase 137K
implementation now conforms to TAMPC-001 v1.1 with no Blocking finding
before Operational Readiness Review proceeds.
