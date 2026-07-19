# Phase 137G: Typed Authority Model Prototype Review and Production Integration Architecture

## Status

**Phase:** 137G — architecture only.
**Governing artifacts reconciled:** Phase 137A (`docs/PHASE_137_TYPED_AUTHORITY_MODEL_CONSUMPTION_ARCHITECTURE.md`),
TAMC-001 v1.0 (`docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`),
Phase 137C independent verification, TAMP-001 v1.0
(`docs/implementation/TYPED_AUTHORITY_MODEL_CONSUMPTION_PROTOTYPE_PLAN.md`),
Phase 137E implementation (`prototypes/typed_authority_inspector.py`,
`docs/implementation/TYPED_AUTHORITY_MODEL_CONSUMPTION_PROTOTYPE_IMPLEMENTATION.md`),
Phase 137F independent verification, Phase 137F.1 lifecycle repair, Phase
137F.1V independent verification and repairs, Stage 3 schemas/models/
registry/manifest/serializers/validators, current production source-tree
boundaries (`src/pcae/**`, `pyproject.toml`), and live repository state at
the commit preceding this phase.
**This phase performs:** no implementation, no production import, no
command registration, no schema/model/registry/manifest change, no
authority/lifecycle/runtime/persistence/publication/recovery/cutover/
compatibility/quarantine activation.
**Runtime posture, unaffected by this document:**

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

This document is the canonical architecture for the first production Typed
Authority Model consumer. It answers whether, and how, but does not itself
authorize implementation.

---

## 1. Executive Verdict

**SUITABLE WITH REQUIRED ARCHITECTURAL CHANGES.**

Three distinct claims must not be conflated, per this phase's own
instructions:

- **Prototype correctness:** confirmed. Phase 137F independently
  re-derived the Phase 137E prototype as TAMC-001- and TAMP-001-compliant,
  read-only, deterministic, provenance-complete, authority-neutral,
  lifecycle-neutral, runtime-neutral, and isolated, with no Blocking
  finding and two Non-Blocking observations (NB-1, NB-2). Nothing in this
  phase's review contradicts that verdict.
- **Production suitability:** partial. The prototype's *data flow*,
  *ownership boundaries*, *failure taxonomy*, and *provenance model* are
  directly reusable as the reference design. Its *placement*
  (repository-root `prototypes/`, outside the packaged wheel), *input
  form* (in-memory bytes plus caller-supplied filesystem paths to the
  schema package), and *result-mutability boundary* (NB-1) are
  prototype-only and must not move into `src/pcae` unchanged. Section 2
  and Section 14 detail exactly what changes.
- **Production authorization:** not granted here. This document defines
  architecture only. TAMC-001 v1.0 (TAMC-REQ-073) and TAMP-001 v1.0 both
  already state that conformance and prototype verification do not
  themselves authorize implementation. Section 22 lists the explicit
  preconditions that remain before any implementation phase may begin.

A positive architectural verdict is a statement about design fitness, not
a grant of implementation authority. 137H (contract freeze) and 137I
(independent contract verification) must both complete, per Section 25,
before 137J/137K implementation planning or coding begins.

---

## 2. Prototype Review

### 2.1 Against TAMC-001

The prototype (`prototypes/typed_authority_inspector.py`) implements
exactly one Allowed `inspection` consumer (TAMC-REQ-012). Phase 137F's
independent re-derivation (not accepted here as an oracle, but re-checked
against the live file) confirms:

- one function, `inspect_explicit_artifact()`, returns a value and
  registers nothing;
- Stage 3 ownership is respected line-for-line — parsing
  (`parse_strict_json`), registry (`build_offline_registry`), manifest
  (`load_and_verify_manifest`), schema validation
  (`validate_record_shape`), and typed-model construction/serialization
  (`<Family>.from_dict`/`.to_dict`, `to_canonical_bytes`) are all called
  through their existing owners, never reimplemented;
- the unconditional representation-only disclosure
  (`REPRESENTATION_ONLY_DISCLOSURE`) is a dataclass default, not a
  computed branch, so no input can suppress it;
- `to_dict()` hardcodes `"semantic"`, `"lifecycle"`, `"governance"` as
  `"not_performed"`, keeping the five validation classes distinct
  (TAMC-REQ-039–041);
- failure precedence is frozen (parse → provenance context → registry →
  manifest → family/version/identity → schema → model → lossless
  round-trip), matching TAMP-001 §4/§7 exactly.

### 2.2 Against TAMP-001

The four planned components (orchestrator, family dispatch, provenance
assembler, immutable result model) map exactly onto
`inspect_explicit_artifact`/`_MODEL_BY_FAMILY`/`_provenance_bundle`/
`InspectionSuccess`+`InspectionFailure`. No undocumented component exists.
This is the strongest evidence that the *shape* of the design (not
necessarily its exact file) is sound and reusable.

### 2.3 Against Stage 3 ownership boundaries

`_MODEL_BY_FAMILY` binds all sixteen frozen families to their existing
`pcae.cltr.authority.*` classes; no schema, validator, registry, or model
logic is duplicated. This ownership discipline is the single most
important property to carry into production unchanged.

### 2.4 Against production packaging conventions

`pyproject.toml` scopes the wheel to `packages = ["src/pcae"]`. The
prototype deliberately lives at repository-root `prototypes/`, which is
**not** part of the installed package — confirmed by Phase 137F §1 and
re-confirmed here (`packages = ["src/pcae"]`, no reference to
`prototypes/` anywhere in `pyproject.toml`). This means, as a plain fact
independent of any authority question: **the prototype does not exist for
anyone who installs the `pcae` wheel.** A production consumer that must
work for an installed user cannot be "the same file" as the prototype; it
must live inside `src/pcae` and resolve the Stage 3 package
(`src/pcae/schema_resources/cltr_cutover/`) as packaged data, not as a
caller-supplied `Path`.

### 2.5 Against CLI conventions

This repository already has two precedents for exactly this kind of
graduation, both instructive but neither directly reusable as-is:

- `pcae cltr-prototype ...` (`src/pcae/commands/cltr_prototype.py`) —
  namespaced deliberately distinct from any future production `pcae cltr
  ...` family, printing an explicit `-- PROTOTYPE ONLY --` boundary
  banner on every invocation.
- `pcae cltr shadow ...` (`src/pcae/commands/cltr_shadow.py`,
  `src/pcae/cltr/inspection.py`) — a **production**, read-only,
  non-authoritative CLI surface, namespaced under the production `cltr`
  command family but distinguished by the `shadow` subcommand and an
  unconditional `NON_AUTHORITY_DISCLOSURE` dict (`shadow_mode: true`,
  `authoritative: false`, `mutation: "none"`) in every JSON payload.

The `cltr shadow` precedent is the closer analog for *disclosure
convention and CLI ergonomics* (`--json`, sorted key rendering, a fixed
non-authority banner, exit code tied to outcome). It is **not** a template
for *invocation semantics*: `cltr shadow`'s underlying
`observe_finalized_transition()` is called ambiently, automatically, by
every production finalization entry point, constructing its own record
from live transition state. TAMC-001 and TAMP-001 categorically forbid
that shape of consumption for Typed Authority Model records — ambient
discovery, "latest" resolution, and non-explicit input are all Forbidden
(TAMC-REQ-005 Scope note aside, see TAMP-001 §1.3, §3.1). The first
production TAM consumer must remain explicit-artifact-only, unlike
`cltr shadow`.

### 2.6 Against testing conventions

`tests/test_typed_authority_inspector_137e.py` establishes the fixture and
adversarial-test conventions (per-family fixtures, malformed/duplicate-key
JSON, forged authority-looking claims, monkeypatched registry/manifest
failures with message-leak checks). These conventions transfer directly;
Section 20 requires **fresh** fixtures rather than reuse, per Phase 137F.1V's
own demonstrated lesson (§6.1 below) that reusing a predecessor's fixture
table can miss live defects a fresh adversarial derivation catches.

### 2.7 Against lifecycle and runtime boundaries

Confirmed unaffected in Sections 15–16.

### 2.8 Against provenance and security requirements

Confirmed largely reusable in Sections 11–12, with two required hardening
items carried from Phase 137F's NB-1/NB-2 (Section 14).

### 2.9 Reusable components

- The nine-step read-only data flow (parse → provenance context →
  registry → manifest → family/version/identity dispatch → schema →
  model → lossless round-trip → immutable result).
- The frozen failure taxonomy and its precedence ordering.
- The `_MODEL_BY_FAMILY` explicit-dispatch pattern (data, not behavior).
- The provenance bundle shape (`origin`, `record_identity`,
  `copied_provenance_values`, `complete_typed_record_claims`,
  `derivation`, `authority_neutrality`).
- The unconditional representation-only disclosure as a non-suppressible
  default.
- The `OpaqueJsonValue`-backed nested immutability.

### 2.10 Prototype-only components (must not move unchanged)

- `ExplicitArtifactContext.package_root` / `.manifest_path` as caller-
  supplied `Path` values — a production consumer cannot ask an ordinary
  CLI user to supply the internal schema package location; it must
  resolve the packaged, installed Stage 3 bundle itself (Section 5, 19).
- The bytes-only input surface — a CLI needs a file-path argument or
  stdin, not an in-process `bytes` parameter (Section 8).
- `InspectionSuccess`/`InspectionFailure` as plain
  `@dataclass(frozen=True)` — NB-1 shows top-level fields remain mutable
  via `object.__setattr__`; acceptable for a prototype return value used
  only inside isolated tests, not sufficient for a value that a production
  CLI formatter and, later, other in-process callers will hold (Section
  14).
- The manifest-entry-count assumption (NB-2) — acceptable as a fail-closed
  dependency in a prototype exercised only against a fixture package;
  requires an explicit, tested precondition statement in production
  (Section 14).
- The physical module location and its exclusion from `__all__`-driven
  package import — the prototype's isolation *depended on* living outside
  `src/pcae`; that exact isolation property will no longer hold once a
  production consumer is added, so the boundary must be re-established
  architecturally (Section 5), not merely re-hoped-for.

### 2.11 Assumptions valid only outside the production source tree

- That nothing imports the module (true only because it sits outside
  `src/pcae`; once a production consumer exists inside `src/pcae`, import
  isolation must be enforced by *review and test*, not by physical
  location).
- That test-only fixture package roots stand in for "the" Stage 3 package
  (production must resolve the one real, installed package).
- That CLI ergonomics (help text, exit codes, `--json`) are out of scope
  (a production consumer has exactly these concerns and TAMP-001
  deliberately deferred them, TAMP-001 §2 row "CLI display").

### 2.12 Dependencies that become riskier in production

- Filesystem path handling: a real CLI user supplies an arbitrary path
  argument, unlike a test harness's controlled fixture path. Section 8
  and Section 12 define the fail-closed input contract this requires
  (symlinks, directories, oversized files, non-files).
- Error-message content: Phase 137F §12 already found and required
  sanitizing a monkeypatched exception's leaked path string; a production
  CLI is the first place where end-user-visible error text is a real
  surface, not a test assertion (Section 10, Section 12).
- Process exit status: the prototype has none; a production CLI's exit
  code is consumed by scripts and CI, and must be as stable as the
  failure taxonomy itself (Section 8, Section 10).

### 2.13 Missing production concerns

Packaging/offline resolution of the Stage 3 bundle (Section 19), CLI
argument parsing and help text (Section 5, 8), exit-status contract
(Section 10), and TAMC compliance evidence *for a distinct production
module* rather than the prototype module (Section 21) — none of these
existed in scope for 137D/137E/137F and must be originated by this
architecture, not inherited by assumption.

---

## 3. First Production Consumer Selection

**Selected: a dedicated, read-only CLI inspection command,
`pcae authority inspect <path>`.**

| Candidate | Disposition |
|---|---|
| Dedicated read-only CLI inspection command | **Selected.** Smallest unit that demonstrates real production consumption: one user invokes one command against one explicit file, gets one observation, process exits. No ambient state, no persistence, no integration with any other governed surface. |
| Diagnostic subsystem integration (`pcae doctor ...`) | Rejected for first consumer. `pcae doctor` surfaces are already governed diagnostic actors with their own remediation-adjacent conventions (e.g., `pcae doctor task-memory`); coupling the first TAM consumer to that surface risks the reader inferring a health/remediation relationship the record does not have. TAMP-001's own candidate table rejected "diagnostics" for the same reason ("risks expanding ... into recommendations"). |
| Reporting integration (PFR-001 phase reports, Architecture Status) | Rejected for first consumer. Reporting surfaces are independently governed persistence owners (TAMC-REQ-014); introducing TAM content there first would require solving the outer-persistence boundary *and* the consumption boundary simultaneously. TAMP-001 rejected this for the prototype for the same reason; the same reasoning holds for the first production consumer. |
| Bootstrap/session-state integration | Rejected for first consumer. `pcae session bootstrap` is lifecycle-adjacent, high-traffic, and already the subject of two recent lifecycle-integrity incidents (137F.1, 137F.1V). Coupling the first, still-unproven production TAM path to that surface maximizes blast radius for no architectural benefit. |
| Repository inspection / discovery integration | Rejected categorically, not merely for the first consumer. Any "find the latest record" or "scan for TAM artifacts" behavior is ambient discovery, explicitly forbidden by TAMP-001 §1.3 ("will not scan the repository, discover a 'latest' record") and by TAMC-REQ-054's prohibition on ambient dereferencing. |

The selected consumer:

- demonstrates real production consumption (a real, installed,
  `pyproject.toml`-packaged command reachable by `pcae authority inspect`);
- remains observational (prints an observation, returns an exit status);
- creates no authority, lifecycle mutation, or runtime capability;
- preserves explicit-artifact input (one path argument, no discovery);
- avoids ambient repository scanning;
- minimizes coupling (no dependency from any other production module onto
  this one; Section 5).

Exactly one consumer is authorized by this architecture. No second
consumer (a second command, a report integration, a bootstrap hook) may
be introduced under this document.

---

## 4. Consumer Purpose and Non-Goals

**Purpose.** `pcae authority inspect <path>` accepts exactly one
caller-supplied filesystem path to a serialized Typed Authority Model
record, reads it, and prints a provenance-complete, representation-only
observation of that single record to stdout, with a process exit status
reflecting success or a stable failure category.

**Non-goals — the consumer will not:**

- infer authority, authorization, approval, certification, publication,
  execution permission, or any operative state from the record
  (TAMC-REQ-025);
- infer or report on lifecycle state or progression (TAMC-REQ-026);
- discover, enumerate, or select a "latest" record from the repository —
  the path argument is the only record identity source;
- ambiently dereference any `*_reference`/`*_references` field;
- mutate, persist, cache, or write any file, `.pcae/` state, task, phase,
  session, report, receipt, marker, checkpoint, or pointer;
- automatically repair, coerce, or fill absent required record content;
- publish, execute, recover, roll back, or quarantine anything;
- dispatch a notification as a consequence of inspection (an operator may
  separately choose to paste command output into a notification through
  an unrelated, independently governed channel; the consumer itself never
  calls a notification path).

The consumer remains explicit-input only, read-only, deterministic,
idempotent, side-effect free in its consumption behavior, provenance
preserving, authority neutral, lifecycle neutral, and runtime neutral —
restating TAMC-REQ-002 as this consumer's own binding self-description,
not a new obligation.

---

## 5. Production Boundary

### 5.1 Package/module boundary

| Concern | Location |
|---|---|
| Orchestration (production analog of `inspect_explicit_artifact`) | New module `src/pcae/cltr/authority_inspection.py` — placed beside the existing `src/pcae/cltr/inspection.py` (the `cltr shadow` read-only inspection module), inside the packaged production tree, distinct from `src/pcae/cltr/authority/` (the frozen Stage 3 typed models themselves, which remain untouched). |
| CLI wiring | New module `src/pcae/commands/authority_inspect.py`, following the existing one-module-per-command-group convention (`src/pcae/commands/runtime_inspect.py`, `src/pcae/commands/cltr_shadow.py`). |
| Command registration | A new `authority` subcommand group in `src/pcae/cli.py`'s subparser table, with exactly one subcommand: `inspect`. Full form: `pcae authority inspect <path> [--json]`. |

### 5.2 Public API boundary

`src/pcae/cltr/authority_inspection.py` exposes exactly one public
orchestration entry point (naming to be fixed at contract-freeze, e.g.
`inspect_artifact_at_path(path: Path, *, json_output: bool) -> InspectionOutcome`)
plus the immutable result/failure types it returns. No other module may
import individual internal helpers (family dispatch table, provenance
collector) — those remain module-private, exactly as `_MODEL_BY_FAMILY`
and `_provenance_bundle` are private in the prototype today.

### 5.3 CLI boundary

Exactly one command surface: `pcae authority inspect <path> [--json]`.
No `--latest`, no `--phase-id`, no directory or glob argument, unlike
`cltr shadow show --latest`/`--phase-id` — those flags exist there because
`cltr shadow` already owns a governed persistence root
(`.pcae/cltr-shadow/`) to resolve against; the TAM consumer owns no such
root and must not invent one.

### 5.4 Dependency direction

```
src/pcae/commands/authority_inspect.py   (CLI: argument parsing, exit code)
        |
        v
src/pcae/cltr/authority_inspection.py    (production orchestration)
        |
        v
pcae.schema_runtime.*                    (parser, registry, manifest, validator — frozen, Stage 3)
        |
        v
pcae.cltr.authority.*                    (typed models, serialization — frozen, Stage 3)
        |
        v
standard library only
```

### 5.5 Allowed imports

`authority_inspection.py` may import: `pcae.cltr.authority` (all sixteen
family classes, `OpaqueJsonValue`), `pcae.cltr.authority.errors`,
`pcae.cltr.authority.serialization`, `pcae.schema_runtime` (parser,
registry, manifest, validator, `OutcomeStatus`), and standard library
(`dataclasses`, `hashlib`, `pathlib`, `importlib.resources` or equivalent
packaged-data resolution, `typing`).

### 5.6 Forbidden imports

`authority_inspection.py` and `authority_inspect.py` (the CLI wiring)
SHALL NOT import: anything from `pcae.core.tasks`, `pcae.core.session`,
`pcae.commands` (other than being imported *by* the CLI dispatcher, never
importing another command module), `pcae.cltr.shadow`, `pcae.cltr.migration`,
`pcae.cltr_prototype`, any lifecycle/runtime/notification/publication/
recovery module, or `prototypes/typed_authority_inspector.py` itself. The
production module is architecturally independent of the prototype module;
it does not wrap, subclass, or delegate to it (Section 2.10, 2.11).

### 5.7 Registry/manifest access boundary

The production consumer resolves the Stage 3 package root and manifest
path from the **installed package's own data** (`src/pcae/schema_resources/
cltr_cutover/`, already wheel-packaged per `pyproject.toml`
`packages = ["src/pcae"]`), computed once, deterministically, from the
package's own `__file__`/`importlib.resources` location — never from a
caller-supplied path, environment variable, or working-directory-relative
guess. This is the one deliberate, architected difference from the
prototype's caller-supplied `package_root`/`manifest_path` (Section 2.4,
Section 19).

### 5.8 Serialization/deserialization boundary

Reused unchanged from `pcae.cltr.authority.serialization` and each
family's `from_dict`/`to_dict`, exactly as the prototype does.

### 5.9 Validation boundary

Reused unchanged from `pcae.schema_runtime.validate_record_shape` and each
model's own `__post_init__`, exactly as the prototype does.

### 5.10 Output boundary

Stdout only (human-readable by default, `--json` for machine-readable),
no file write, no return value consumed by any other production module in
this phase (Section 4, Section 9).

No circular dependency is introduced: no Stage 3 module, no lifecycle
module, and no runtime module imports `authority_inspection.py` or
`authority_inspect.py`. No lifecycle-to-consumer authority inversion and
no runtime-to-consumer execution path exists, by construction of Sections
5.5–5.6.

---

## 6. Ownership Architecture

One owner per responsibility, carried forward from TAMC-001 §6 and TAMP-001
§5.4, restated for the production module:

| Responsibility | Owner |
|---|---|
| Artifact loading (reading bytes from the caller-supplied path) | `authority_inspect.py` (CLI layer) reads the file; `authority_inspection.py` receives bytes plus the resolved path identity, mirroring the existing parse-first step |
| Family resolution | `authority_inspection.py`'s explicit dispatch table (production analog of `_MODEL_BY_FAMILY`) |
| Schema resolution | `pcae.schema_runtime` offline registry (frozen, Stage 3) |
| Deserialization | Each frozen `pcae.cltr.authority.*` model's `from_dict` |
| Typed-model construction | Same as above |
| Structural validation | `pcae.schema_runtime.validate_record_shape` (frozen, Stage 3) |
| Model validation | Each model's own `__post_init__` (frozen, Stage 3) |
| Provenance extraction | `authority_inspection.py`'s provenance assembler (production analog of `_provenance_bundle`) |
| Observation construction | `authority_inspection.py`'s immutable result types |
| Output rendering | `authority_inspect.py` (CLI layer): human-readable text and `--json` |
| Failure classification | `authority_inspection.py`'s frozen failure taxonomy (Section 10) |
| CLI argument parsing | `authority_inspect.py` / `src/pcae/cli.py` subparser wiring |
| Process exit status | `authority_inspect.py` |

The production consumer does not duplicate any Stage 3 owner: schema
shape, registry lookup, manifest integrity, schema conformance, and model
invariants all remain exactly where TAMC-001 §6 places them.

---

## 7. Data Flow

```
explicit CLI path argument
  -> bounded artifact read (authority_inspect.py, fail-closed on non-file/oversized/symlink-escaping input)
  -> strict JSON parse (pcae.schema_runtime.parse_strict_json)                         [owner: schema_runtime; failure: malformed_artifact]
  -> family identification (record["record_type"] against explicit dispatch table)    [owner: authority_inspection.py; failure: unknown_record_family]
  -> registry resolution (pcae.schema_runtime.build_offline_registry, package-resolved) [owner: schema_runtime; failure: registry_failure / registry_entry_missing]
  -> manifest verification (pcae.schema_runtime.load_and_verify_manifest)              [owner: schema_runtime; failure: manifest_failure / manifest_entry_missing]
  -> schema validation (pcae.schema_runtime.validate_record_shape, Draft 2020-12)       [owner: schema_runtime; failure: schema_validation_failed]
  -> deserialization (Family.from_dict)                                                [owner: pcae.cltr.authority.*; failure: model_validation_failed]
  -> typed-model validation (lossless to_dict round-trip == input record)              [owner: pcae.cltr.authority.*; failure: required_provenance_failed]
  -> provenance-preserving observation (authority_inspection.py provenance assembler)  [owner: authority_inspection.py; no failure — assembly only on prior success]
  -> deterministic rendering (authority_inspect.py: text or --json)                    [owner: authority_inspect.py]
  -> exit status (0 = inspected, 1 = any InspectionFailure category)                   [owner: authority_inspect.py]
```

Every transition is a value passed to, or a result returned by, an
existing owner or the new orchestration/CLI layer. No transition mutates
state, writes a file, or performs a side effect. No transition may
establish authority: schema/model success proves only schema/model
validity (Section 8 of TAMC-001; restated in Section 8 below).

---

## 8. Input Contract

| Concern | Requirement |
|---|---|
| Explicit path requirement | Exactly one CLI positional argument, a filesystem path. No default, no discovery, no stdin fallback in this first consumer (stdin support is future extensibility, not authorized here). |
| Supported file format | UTF-8-encoded strict JSON object, one record. |
| Encoding | UTF-8 only; a decode failure is `malformed_artifact`. |
| Maximum input size | A fixed, conservative byte ceiling (frozen at contract-freeze, e.g. the same order of magnitude as existing Stage 3 schema-resource size limits in `pcae.schema_runtime.limits`) enforced **before** parsing; oversized input fails closed as `malformed_artifact`, not a resource-exhaustion crash. |
| Symlink behavior | The resolved, real path is used for size/type checks (`Path.resolve()` + `os.path.realpath` semantics); a symlink pointing outside expected bounds is not specially "followed further" — it is simply the file the OS resolves to, checked by the same size/type gate as any other path. No elevated trust is given to a symlink target. |
| Directory rejection | A directory argument fails closed (`malformed_artifact` or a dedicated `input_not_a_file` category fixed at contract-freeze) before any read is attempted. |
| Special-file rejection | Non-regular files (FIFOs, device files, sockets) fail closed the same way, checked via `Path.is_file()` before open. |
| Path traversal concerns | The path is used exactly as supplied (resolved for the checks above); there is no repository-relative or "safe root" confinement, because this consumer has no notion of a project root to confine within — it inspects whatever file the invoking user names, the same trust boundary as any other local file-reading CLI tool the user already runs with their own privileges. |
| Missing files | `FileNotFoundError` at read time maps to a stable `input_not_found` failure category. |
| Unreadable files | `PermissionError`/`OSError` at read time maps to a stable `input_unreadable` failure category; the underlying OS error text is not echoed verbatim (Section 12). |
| Concurrent file changes | The file is read once, fully, into an immutable `bytes` object before any processing begins; a TOCTOU change after that read has no effect on the single in-process inspection, matching the prototype's existing bytes-in contract. No re-read, re-stat, or partial-read retry occurs. |
| Malformed JSON | `malformed_artifact`, reusing `pcae.schema_runtime.parse_strict_json`'s existing duplicate-key-rejecting strict parser unchanged. |
| Duplicate keys | Rejected by the existing strict parser (unchanged reuse), same as the prototype. |
| Unknown families | `unknown_record_family`, unchanged from the prototype's taxonomy. |
| Unsupported versions | `unsupported_schema_version` / `unsupported_model_version`, unchanged. |

The architecture remains fail-closed throughout: every branch above has
exactly one deterministic outcome, and no branch retries, coerces, or
substitutes a default.

---

## 9. Output Contract

Output is **both** human-readable (default) and machine-readable
(`--json`), matching the existing `cltr shadow`/`cltr-prototype` CLI
convention of a `--json` flag with sorted-key rendering.

| Concern | Requirement |
|---|---|
| Field ordering | JSON output uses `sort_keys=True` (matching `cltr_shadow.py`'s existing `json.dumps(payload, indent=2, sort_keys=True, default=str)` convention); human-readable output iterates fields in a fixed, contract-frozen order, not dict insertion order. |
| Collection ordering | `copied_provenance_values` and any list-valued field are already sorted deterministically by the prototype's `_collect_named_values` (`sorted(..., key=lambda item: item["instance_path"])`); the production version preserves this. |
| Failure codes | The frozen failure taxonomy (Section 10), stable strings, never renumbered or renamed without a governed contract revision. |
| Exit codes | `0` for `inspected`; `1` for every `InspectionFailure` category (matching the existing `cltr_shadow.py` convention of `0 if payload.get(...) else 1`); no distinct exit code per failure category in this first consumer (a richer exit-code scheme is future extensibility, not authorized here). |
| Redaction | Error text never includes raw OS exception strings, absolute ambient paths beyond the one path the user themselves supplied, or any secret-shaped value (Section 12; Phase 137F §12 already demonstrated this exact leak risk with a monkeypatched registry exception). |
| Provenance display | Every field TAMC-REQ-042 requires is rendered, including declared vs. derived digest as two distinct labeled fields, exactly as the prototype's `input_digest`/`declared_record_digest` split. |
| Schema/model version display | `schema_version` and `model_version` (contract version) are always shown, both on success and, where known, on failure. |
| Digest display | Both `input_digest` (derived) and `declared_record_digest` (copied) are shown, never merged into one field. |
| Validation status | Schema and model validation outcomes are shown as two distinct keys, plus the fixed `"not_performed"` markers for semantic/lifecycle/governance, unchanged from the prototype. |
| Limitations | This is a description of the CLI's own limitations, not a Stage 3 `limitations.py` field. Its own output must disclose: it inspects one explicit file only; it performs no repository discovery; the representation is not an authority determination. |

Output must not imply authority, approval, authorization, certification
effectiveness, lifecycle completion, or runtime permission — restating
TAMC-REQ-036/038 as this consumer's binding self-description. The
unconditional representation-only disclosure line is printed in every
invocation, success or failure, exactly as the prototype's
`REPRESENTATION_ONLY_DISCLOSURE` default guarantees today.

---

## 10. Failure Taxonomy

The production failure taxonomy is the prototype's taxonomy, extended by
exactly the new input-boundary categories a real filesystem path
introduces (Section 8) that an in-memory `bytes` parameter never needed:

| Failure | Details may be exposed? | Stable code | Exit behavior | Partial output allowed? | Raw exception suppressed? |
|---|---|---|---|---|---|
| input-not-found | Path only (the one the user supplied) | `input_not_found` | 1 | No | Yes |
| unsupported-input-type (directory/special file) | Path only | `input_not_a_file` | 1 | No | Yes |
| unreadable-input | Path only, no OS errno text | `input_unreadable` | 1 | No | Yes |
| malformed-artifact | Generic parse-failure description | `malformed_artifact` | 1 | No | Yes |
| unknown-family | Declared family string (from the record itself) | `unknown_record_family` | 1 | No | N/A |
| unsupported-schema-version | Declared version string | `unsupported_schema_version` | 1 | No | N/A |
| unsupported-model-version | Declared version string | `unsupported_model_version` | 1 | No | N/A |
| registry-mismatch | Generic description, no path leakage | `registry_failure` / `registry_entry_missing` | 1 | No | Yes |
| manifest-mismatch | Generic description, no path leakage | `manifest_failure` / `manifest_entry_missing` | 1 | No | Yes |
| digest-mismatch (round-trip inequality) | Generic description | `required_provenance_failed` | 1 | No | N/A |
| schema-validation-failure | Owner-provided structured issues (schema_runtime's own, already sanitized) | `schema_validation_failed` | 1 | No | N/A |
| model-validation-failure | Generic description, model class name | `model_validation_failed` | 1 | No | N/A |
| provenance-failure | Generic description | `required_provenance_failed` | 1 | No | N/A |
| internal-contract-violation (e.g. `family_identity_mismatch`) | Declared identities involved | `family_identity_mismatch` | 1 | No | N/A |

No silent fallback and no automatic repair exist anywhere in this table,
matching TAMP-001 §7/§3.5 exactly. Failure ordering (Section 7) is frozen
so that an input with multiple simultaneous defects produces the same
primary failure on every run — a direct extension of the prototype's
already-frozen precedence, with the two new filesystem-boundary checks
(`input_not_found`, `input_not_a_file`, `input_unreadable`) inserted
**before** the parse step, since they must be resolved before bytes even
exist to parse.

---

## 11. Provenance Architecture

Mandatory preservation, unchanged in kind from TAMC-REQ-042 and the
prototype's existing `_provenance_bundle`, restated for the production
consumer's input shape:

| Provenance item | Sourced directly | Derived deterministically | Unavailable / prohibited from inference |
|---|---|---|---|
| Source artifact identity | The path argument as supplied by the caller | — | — |
| Artifact digest | — | SHA-256 of the exact bytes read (`input_digest`) | — |
| Record identity | `record_id` field, copied | — | — |
| Family identity | `record_type` field, copied | — | — |
| Schema identity and version | `schema_id`/`schema_version` fields, copied | — | — |
| Model identity and version | `contract_version` field, copied; model class name derived from dispatch | — | — |
| Registry identity | — | Resolved `resource_info` from the offline registry, reported as an observation | — |
| Manifest identity | — | Resolved manifest entry, reported as an observation | — |
| Derivation steps | — | Explicit `derivation` map distinguishing `complete_typed_record_claims`/`copied_provenance_values` (copied) from `derived_input_digest` (derived) | — |
| Validation results | — | Distinct schema/model outcome objects | Semantic/lifecycle/governance validation: explicitly `"not_performed"`, never silently omitted |
| Limitations and uncertainty | Any `limitations`/`uncertainty`/`opaque`/`extensions`/`*_reference(s)` field present in the record, copied verbatim | — | Any item absent from the record is reported as absent, never fabricated |

This table is definitionally exhaustive for what the production consumer
touches: no item may be added later by "convenience" without an
explicit, governed contract revision (TAMC-REQ-067).

---

## 12. Security Architecture

| Concern | Production requirement |
|---|---|
| Untrusted local artifacts | Treated as untrusted input at the CLI boundary: size-checked and type-checked (Section 8) before any parse is attempted. |
| Parser safety | Reused unchanged from `pcae.schema_runtime.parse_strict_json` — no new parser is written. |
| Resource exhaustion | A fixed maximum input size (Section 8) enforced prior to read-into-memory; the registry/manifest/schema resources are themselves fixed, small, packaged, frozen files, not attacker-influenced. |
| Oversized payloads | Rejected before parsing (Section 8). |
| Symlink attacks | No elevated trust for symlink targets (Section 8); the consumer does not walk a directory tree, so classic symlink-traversal attacks on multi-file scans do not apply — it opens exactly one resolved path once. |
| TOCTOU | The file is read fully into `bytes` once; every subsequent step operates on that immutable value, never re-touching the filesystem (Section 8). |
| Path disclosure | Error text names only the one path the invoking user themselves supplied on their own command line — this is not a disclosure to an untrusted party, since the operator is both the input author and the output reader. Internal package-root/manifest paths are never echoed (Section 9). |
| Exception-data leakage | Raw `OSError`/library exception text is never echoed verbatim; each failure category carries a fixed, generic, pre-written message, exactly as Phase 137F §12 required and verified for the prototype's `registry_failure`/`manifest_failure` categories. |
| Provenance forgery | A forged `authority_disclosure.is_authoritative: true` claim fails Draft 2020-12 schema validation itself (the shared schema definition declares that field `const: false`), independently confirmed by Phase 137F §9 — a stronger guarantee than the consumer's own logic provides, inherited unchanged in production. |
| Digest substitution | `input_digest` (derived) and `declared_record_digest` (copied) remain two distinct fields; neither replaces the other (Section 11). |
| Registry/manifest substitution | The production consumer resolves the registry/manifest from the installed package's own location only (Section 5.7, 19) — there is no CLI flag to point it at an arbitrary alternate package root, closing off a substitution vector the prototype's caller-suppliable `package_root` deliberately left open for test isolation. |
| Unsafe dynamic imports | None; `_MODEL_BY_FAMILY`-equivalent dispatch is a static dict literal, exactly as the prototype's is. |
| Unsafe class resolution | None; no `record_type` string is ever used to construct an import path or `getattr` chain — only as a dict key into the static table. |
| Privilege escalation | None; the consumer never gains write, network, or execution capability by virtue of reading a record — restating TAMC-REQ-063. |
| Environment-dependent behavior | None; no environment variable, working directory, or wall clock affects dispatch, validation, or output content (only the OS-level file read touches the filesystem, and only for the one caller-supplied path). |

The design introduces no dynamic code execution.

---

## 13. Determinism and Replay

| Concern | Requirement |
|---|---|
| Repeated invocations | Identical file content at the same path produces byte-identical `to_canonical_bytes()`/`--json` output, or an identical failure category and message, on every run — unchanged from the prototype's already-demonstrated (Phase 137F §6) determinism. |
| Process restarts | No in-memory or on-disk cache exists; each invocation is a fresh process with no carried state. |
| Equivalent file paths | Two different paths containing byte-identical content produce identical `record_claims`/`provenance`/validation output; only `source_artifact_identity`/`source_location` (the path itself) differs, as expected and correct. |
| Registry ordering | `build_offline_registry`'s resolution is unchanged, frozen Stage 3 behavior. |
| Manifest ordering | The manifest-entry filter uses the same `sorted()`-free but git-tracked-fixed-order `manifest.json`, matching Phase 137F §6's confirmation that entry order is fixed by the frozen, git-tracked file, not filesystem traversal. |
| Mapping ordering | `copied_provenance_values` remains explicitly `sorted(..., key=lambda item: item["instance_path"])`, unchanged. |
| Failure formatting | Frozen message templates per category (Section 10), never string-interpolated with unsorted collections. |
| Platform differences | No platform-conditional branch exists; path handling uses `pathlib.Path` uniformly, matching existing repository convention. |

Replay neutrality: inspecting the same unchanged artifact under the same
supported package version produces semantically identical output,
including identical failure classification, on every invocation, on every
supported platform.

---

## 14. Immutability Boundary

Reviewing the two Phase 137F Non-Blocking observations for production
relevance:

| Observation | Classification for production | Rationale |
|---|---|---|
| NB-1 — top-level frozen-dataclass fields remain mutable via `object.__setattr__` | **Required before production implementation.** | The prototype's own verification correctly scoped this as out of TAMC-001's threat model *for an isolated test harness* ("would require a downstream caller intentionally reaching for `object.__setattr__`, which is out of scope"). A production result value is different: it will be held, formatted, and potentially passed between the CLI layer and (in a later phase, not this one) other in-process callers within the same repository's own codebase, where an accidental or convenience-driven `object.__setattr__` is a realistic authorship mistake, not merely an adversarial one. Production hardening (to be specified exactly in 137H/137J, not built here) should adopt one of: private construction via a module-level factory function only, `MappingProxyType`-wrapped `__dict__` access, or an explicit `__setattr__` override that raises unconditionally — whichever preserves `dataclass`'s existing equality/repr ergonomics with the least new surface. |
| NB-2 — implicit dependency on the manifest one-entry-per-family invariant | **Recommended hardening, with the existing fail-closed behavior as an acceptable interim floor.** | The prototype already fails closed (`manifest_entry_missing`) rather than silently picking one of several matching entries if the invariant is ever violated — this is the correct behavior and requires no *functional* change. The recommended hardening is documentation and a dedicated regression test asserting the manifest's one-entry-per-family invariant explicitly (rather than only implicitly relying on it via the dispatch filter), so a future manifest change that violates it is caught by that new test rather than discovered only via the fail-closed path in the field. This is not a security or correctness gap; it is an explicitness improvement. |

Defensive copying, tuples/frozen collections for nested list output, and
mapping proxies for the outer dataclasses are all **recommended
hardening** consistent with NB-1's remediation; explicit uniqueness
validation of the manifest is **recommended hardening** consistent with
NB-2. No prototype assumption is silently inherited: both are named,
classified, and assigned a concrete disposition above rather than carried
forward by default.

---

## 15. Lifecycle Boundary

The consumer's relationship to every lifecycle-adjacent artifact is
**inspect only, never own**:

- **Phase reports** — the consumer may be *invoked by* an operator who is
  separately, manually preparing a phase report and wants to quote its
  output as supporting evidence; the consumer itself never writes
  `.pcae/phase-reports/*.json` and has no import of any phase-report
  module.
- **Completion metadata** — no import of, or write to,
  `.pcae/phase-completion-metadata.json`. Phase 137F.1's own incident is
  the concrete cautionary precedent: that gap existed because a task-closure
  command silently skipped canonical-report/metadata generation; this
  consumer must never be positioned as any kind of closure or completion
  step, so that failure mode cannot recur through it.
- **Task state** — no import of `pcae.core.tasks`; the consumer cannot
  determine phase completion (Primary Question resolved: it does not).
- **Receipts / markers / notifications** — no import of any binding or
  dispatch module; a `receipt_authority_binding`/`marker_authority_binding`/
  `notification_authority_binding` record, if inspected, is reported purely
  as `record_claims`, never acted on.
- **Architecture Status / bootstrap / session reporting** — none of these
  surfaces import this consumer in this phase; any future integration of
  TAM content *into* one of those surfaces (Section 5.1 of TAMC-001 already
  lists them as separately Allowed categories) is out of this document's
  scope and would need its own contract/architecture treatment for *that*
  surface's own persistence boundary, per TAMC-REQ-014.

The consumer does not determine phase completion, create canonical
reports, mutate lifecycle state, authorize notification, alter metadata,
become a finalization gate, or become lifecycle authority.

---

## 16. Runtime Boundary

Production placement inside `src/pcae` does not, by itself, change
runtime capability, because:

- the consumer registers no execution adapter — it is a CLI subcommand
  that returns a value and an exit code, structurally identical in kind
  to `pcae runtime inspect` itself, which Section 10 of TAMC-001 already
  names as an Allowed consumer that does not change runtime posture;
- it does not become a runtime plugin — no import of
  `pcae.core.runtime_introspection`, `pcae.core.runtime_snapshot`, or any
  `RuntimeRegistry` type exists;
- it requests no permissions — no `PermissionBroker` import or call;
- it activates no capability, dispatches no work, schedules no work,
  mutates no runtime context, and participates in no execution decision.

Runtime remains Observed / observe / unavailable both before and after
this architecture is adopted, and will remain so after the eventual
implementation phase, verified live exactly as Phase 137F §11 verified it
for the prototype (`pcae runtime inspect` output compared before/after).

---

## 17. Authority Boundary

Restated and operationalized for this specific consumer:

**Representation never establishes authority.** For
`pcae authority inspect <path>`:

Inspection success (`outcome: inspected`, exit code 0) means only:

- the explicit file at the supplied path was read and parsed as strict
  JSON;
- it satisfied Draft 2020-12 schema conformance and its frozen typed
  model's own construction invariants;
- an observation was produced and printed.

Inspection success does **not** mean:

- the record is authoritative;
- the represented event (an epoch transition, a certification, a
  publication) occurred;
- any authorization referenced in the record is valid;
- any certification referenced in the record is effective;
- any publication referenced in the record succeeded;
- any recovery referenced in the record is permitted;
- any cutover referenced in the record is approved;
- lifecycle state changed in any way as a result of running the command.

Every invocation — success or failure — prints the fixed
representation-only disclosure, unconditionally, as a non-suppressible
default, exactly as the prototype already guarantees via
`REPRESENTATION_ONLY_DISCLOSURE`'s dataclass-default status.

---

## 18. Compatibility and Versioning

| Concern | Requirement |
|---|---|
| Supported Stage 3 versions | Exactly schema version `"1.0"` and typed-model contract version `"1.0"` for all sixteen families, pinned as literals — unchanged from the prototype's `SUPPORTED_SCHEMA_VERSION`/`SUPPORTED_MODEL_VERSION`. |
| Unknown-version rejection | `unsupported_schema_version`/`unsupported_model_version`, unchanged; no nearby-version fallback. |
| Future family behavior | A new family requires a new manifest entry, schema, and model (Stage 3's own governed process) **and** a governed revision to this consumer's explicit dispatch table before it is recognized; until then, `unknown_record_family`. |
| Additive evolution | Adding a family must not change behavior or classification for any already-supported family (TAMC-REQ-056/059), restated as this consumer's own binding property. |
| Consumer versioning | The consumer's own `CONSUMER_ID` (production analog of the prototype's `"tamp-001-explicit-artifact-inspector"`, to be fixed at contract-freeze, e.g. `"pcae-authority-inspect-v1"`) is reported in every output. |
| Output versioning | The JSON output includes the TAMC contract version (`"1.0"`) explicitly; a future contract revision that changes output shape must bump this value. |
| Error-code versioning | The failure-category strings in Section 10 are the stable contract; renaming one requires a governed contract revision, not a silent code change. |
| Contract revision handling | Per TAMC-REQ-067, any revision must identify its predecessor, version, changed requirements, migration effect, affected consumer classes, and backward-compatibility impact; this consumer does not locally supersede TAMC-001. |

No permissive parsing of unknown future versions is permitted anywhere in
this design.

---

## 19. Packaging and Distribution

This section is the architecture's most consequential departure from the
prototype, because the prototype was never required to work for an
installed user and the production consumer must.

- **Package inclusion.** `authority_inspection.py` and
  `authority_inspect.py` live under `src/pcae/`, already covered by
  `pyproject.toml`'s `packages = ["src/pcae"]` wheel scope — no
  `pyproject.toml` change is needed for the module files themselves.
- **Installation behavior.** The consumer must work immediately after
  `pip install pcae-harness` with no additional setup step, unlike the
  prototype which only ever ran from a repository checkout with a
  caller-supplied `package_root`.
- **Offline resource access.** `src/pcae/schema_resources/cltr_cutover/`
  (manifest, schemas) is already part of the packaged wheel (it is
  physically inside `src/pcae`); the production consumer resolves this
  location via a package-relative computation (e.g.
  `Path(__file__).resolve().parent.parent / "schema_resources" /
  "cltr_cutover"`, or `importlib.resources`-based resolution if the
  existing `pcae.schema_runtime` loader already has an established
  pattern for this — to be confirmed and fixed exactly at contract-freeze
  by inspecting how `pcae.schema_runtime.loader` currently locates this
  same directory for its own existing callers) — never from a `--package-root`
  CLI flag, environment variable, or working-directory guess.
- **Registry/manifest resource resolution.** Identical frozen resolution
  logic to whatever `pcae.schema_runtime` callers already use internally
  today for locating `cltr_cutover/` — this consumer must not invent a
  second resolution strategy; it must call the same package-location
  logic Stage 3 itself already relies on, if such a shared helper exists,
  or, if it does not yet exist as a shared helper, 137H must specify
  exactly where the one non-duplicated resolution helper lives.
- **Wheel/sdist expectations.** No change to `[tool.hatch.build.targets.wheel]`
  or `[tool.hatch.build.targets.sdist]` is anticipated, since the new
  files sit inside the already-included `src/pcae` tree; a packaging test
  (Section 20) must confirm this rather than assume it.
- **Editable-install expectations.** Must work identically under
  `pip install -e .` and a built wheel — this is exactly the kind of
  packaging drift Phase 106D's own sdist-scoping incident (referenced in
  `pyproject.toml`'s own comment) demonstrates can silently diverge if
  untested.
- **Import stability.** `pcae.cltr.authority_inspection` must be importable
  without triggering any lifecycle, runtime, or notification side import —
  the same static-import-scan discipline Phase 137F §4 applied to the
  prototype applies here, but now scanning a module that *is* shipped.
- **Optional dependency policy.** No new dependency is introduced; the
  consumer uses only what `pcae.schema_runtime`/`pcae.cltr.authority`
  already require (`jsonschema`, already a core dependency per
  `pyproject.toml`).

Production integration must remain functional offline — the design
introduces no network resolution of any kind, matching the existing
offline-only registry discipline.

---

## 20. Testing Architecture

Required test categories for the future implementation phase (137K),
each requiring **fresh adversarial fixtures**, not a copy of
`tests/test_typed_authority_inspector_137e.py`'s fixture table, per the
concrete lesson of Phase 137F.1V (a fresh, independently authored fixture
found two live gate bypasses that a predecessor's own fixture table had
missed — Section 25's sequencing exists precisely so this lesson is
applied here too):

- **Unit tests** for the orchestration function and provenance assembler,
  independent of the CLI layer.
- **All sixteen family tests** — one successful inspection fixture per
  family, freshly constructed, not reused verbatim from 137E's fixtures.
- **Malformed-input tests** — truncated/duplicate-key/non-object JSON,
  freshly constructed.
- **Unknown-version tests** — schema and model version mismatches.
- **Provenance tests** — field-by-field assertions for every item in
  Section 11's table, including the digest-pair distinction.
- **Deterministic-output tests** — repeated-run byte-identical output,
  order-randomization has no effect.
- **Mutation tests** — attempted `object.__setattr__` against the
  production result type must be blocked by the Section 14 hardening
  (this is a **new** test category relative to 137E, since NB-1 requires
  a stronger guarantee here than the prototype provided).
- **Security/path tests** — missing file, directory argument, special
  file, oversized file, symlink target, unreadable file, each mapping to
  the exact Section 10 failure category.
- **Packaging tests** — a genuine `pip install` (or equivalent build +
  install in an isolated environment) followed by running
  `pcae authority inspect` against a fixture record, proving offline
  resource resolution works from an installed wheel, not only from a
  repository checkout (directly modeled on the existing Phase 106D
  packaging-smoke-test discipline referenced in `pyproject.toml`).
- **Wheel/sdist tests** — confirm the new modules are present in a built
  wheel and that `schema_resources/cltr_cutover/` remains present and
  unchanged.
- **CLI tests** — argument parsing, help text, `--json` flag, exit codes
  0/1, matching the existing `tests/` convention for other `pcae`
  subcommands.
- **Regression tests** — golden output for at least one fixed record per
  family, to catch accidental output-shape drift across future changes.
- **Stage 3 compatibility tests** — confirm behavior against the live,
  current `manifest.json`/schemas, not only isolated test fixtures (as
  Phase 137F did independently for the prototype, e.g. its manifest
  entry-count check in §13).
- **Runtime-neutrality tests** — `pcae runtime inspect` output identical
  before/after exercising the new command, exactly as Phase 137F §11.
- **Lifecycle-neutrality tests** — `pcae health`/`pcae check`/`pcae status
  coherence`/`pcae doctor task-memory` unchanged before/after, exactly as
  Phase 137F §10/§15.
- **Authority-neutrality tests** — adversarial records with
  operative-looking claims (`is_authoritative: true`, `state: "issued"`)
  never produce an operative-looking output field, exactly as Phase 137F
  §9, freshly re-derived rather than assumed to still hold.

---

## 21. Compliance Traceability

Every TAMC-001 requirement maps to an architectural control already fixed
in this document, a future implementation component, and future
verification evidence. Organized by TAMC-001's own thirteen categories
(the same organizing structure TAMP-001 §6 and Phase 137E's own compliance
table already use for this exact contract, preserving consistency with
prior practice) so that all seventy-six requirement IDs are covered
without omission:

| TAMC requirement range | Category | Architectural control (this document) | Future implementation component | Future verification evidence |
|---|---|---|---|---|
| 001–021 | Consumer Classification | Section 3 (exactly one Allowed `inspection` consumer selected); Section 4 (non-goals exclude Future/Forbidden behavior) | `authority_inspection.py`, `authority_inspect.py` | Static import/reachability scan (Section 20) proving no report/CLI-migration/reconciliation/semantic/shadow surface exists |
| 022–032 | Consumer Invariants | Section 13 (determinism/replay); Section 14 (immutability hardening); Section 7 (explainability via derivation map) | Immutable result types with Section 14 hardening | Replay-equality tests, mutation-attempt tests (Section 20) |
| 033–034 | Ownership | Section 6 (one owner per responsibility, table) | Dispatch table + orchestration function only | Dependency review confirming no duplicated schema/validation/authority logic |
| 035–038 | Authority | Section 17 (authority boundary operationalized for this consumer) | Unconditional disclosure default, no operative output field | Adversarial authority-claim tests (Section 20) |
| 039–041 | Validation | Section 7 (data flow keeps five validation classes distinct); Section 9 (`"not_performed"` markers) | Separate schema/model outcome objects | Distinct-outcome tests |
| 042–045 | Provenance | Section 11 (full provenance table) | Provenance assembler (production analog of `_provenance_bundle`) | Field-by-field provenance tests (Section 20) |
| 046–048 | Runtime | Section 16 (runtime boundary) | No runtime import (Section 5.6) | Static scan + live `pcae runtime inspect` before/after (Section 20) |
| 049–051 | Lifecycle | Section 15 (lifecycle boundary) | No lifecycle import (Section 5.6) | Static scan + live `pcae health`/`check`/`status coherence` before/after (Section 20) |
| 052–055 | Error Handling | Section 10 (failure taxonomy); Section 8 (input contract) | Frozen failure-category dispatch | One fixture per failure class, replayed for exact equality (Section 20) |
| 056–059 | Extensibility | Section 18 (compatibility/versioning); Section 5.2 (explicit dispatch, private helpers) | Static dispatch table, no dynamic discovery | Unknown-family test, frozen golden results (Section 20) |
| 060–064 | Security | Section 12 (security architecture); Section 14 (immutability hardening) | Hardened result types, bounded input read | Mutation/adversarial/side-effect tests (Section 20) |
| 065–067 | Compatibility | Section 18 | Pinned version literals | Compatibility corpus tests (Section 20) |
| 068–069 | No-Go | Section 5.6 (forbidden imports); Section 4 (non-goals) | N/A — absence of forbidden components is the control | Static architecture scan + negative reachability tests (Section 20) |
| 070–076 | Compliance / Verification process | This entire document (070–073 apply to the future implementation; 074–076 apply to the future 137I contract-verification phase, not to 137G) | The 137J/137K implementation's own compliance-evidence document | 137I independent contract verification; 137L independent implementation verification |

No TAMC requirement ID from 001 through 076 is left without an
architectural control, a designated future component, and a designated
future verification path in the table above.

---

## 22. Production Integration Preconditions

Mandatory before implementation may begin:

- 137G architecture (this document) approved.
- Production contract frozen (137H — TAMC-001-successor or companion
  contract fixing the exact CLI shape, module names, dispatch-entry
  naming, and Section 14 hardening approach as normative text, not
  architectural prose).
- Contract independently verified (137I).
- Consumer identity fixed: `pcae authority inspect`, exactly one
  subcommand, no second consumer introduced alongside it.
- Source-tree boundary fixed: `src/pcae/cltr/authority_inspection.py` +
  `src/pcae/commands/authority_inspect.py` (Section 5), or whatever exact
  paths 137H normatively fixes if it revises this proposal.
- Input/output contracts fixed (Sections 8–9).
- Failure taxonomy fixed (Section 10).
- Ownership fixed (Section 6).
- Security requirements fixed (Section 12, including the Section 14
  immutability hardening approach chosen).
- Packaging requirements fixed (Section 19), including the exact
  offline-resource-resolution mechanism.
- TAMC traceability complete (Section 21).
- No unresolved Blocking finding remains from 137F or 137F.1V (both
  confirmed clear at the time of this document; re-confirmed live in
  Section "Governance" below).
- Runtime remains Observed / observe / unavailable.

---

## 23. No-Go Conditions

Implementation must not begin while any of the following remain
unresolved:

- ambiguous consumer identity (more than one plausible CLI shape still
  under debate at 137H time);
- more than one consumer in scope (a second command, or a report/bootstrap
  integration, proposed alongside the CLI);
- authority implication in any drafted output field;
- lifecycle coupling (any import of `pcae.core.tasks`/session/phase-report
  modules);
- runtime coupling (any import of runtime introspection/snapshot/registry
  modules);
- ambient repository discovery (any "latest"/glob/scan behavior);
- unbounded dereferencing (any code path that follows a `*_reference`
  value);
- duplicated Stage 3 ownership (a local schema/validator/registry
  reimplementation);
- provenance loss (any Section 11 item silently dropped);
- non-deterministic output (any wall-clock, randomness, or unordered
  traversal dependency);
- silent fallback (any retry/coercion/default-substitution branch);
- unknown-version acceptance (any nearby-version fallback);
- unclear package boundary (no fixed answer for offline resource
  resolution, Section 19);
- unresolved immutability risk (Section 14's NB-1 hardening not yet
  chosen/specified by 137H);
- unresolved manifest uniqueness dependency (NB-2's regression test not
  yet specified by 137H, though the existing fail-closed behavior is
  already an acceptable interim floor per Section 14);
- incomplete TAMC traceability (any of the 76 requirement IDs unmapped);
- incomplete security model (any Section 12 row unresolved);
- unresolved Blocking lifecycle/reporting defects (none known at this
  writing; must be re-checked live before 137H begins).

---

## 24. Migration and Rollback Architecture

- **Parallel prototype and production existence.** `prototypes/
  typed_authority_inspector.py` and its test file may remain in place,
  unmodified, after the production consumer exists — they are
  architecturally independent (Section 5.6: no import relationship either
  direction) and serve as an independent reference implementation until a
  future phase explicitly decides to retire one.
- **Comparison strategy.** If desired, a future (not this phase's)
  verification step could run both the prototype and the production
  consumer against the same fixture set and diff their observations for
  parity, purely as an offline developer/reviewer exercise — this is not
  the TAMC-REQ-015/017 "shadow comparison" Future Consumer category
  (which concerns production-path legacy-vs-typed comparison), since
  nothing here is a live production path being compared; it would be a
  one-time developer verification aid, not a standing consumer, and does
  not need to be built now.
- **Promotion criteria.** The production consumer is considered
  promoted/stable once 137L's independent implementation verification
  concludes VERIFIED with no Blocking finding, mirroring the exact
  standard already applied to the prototype at 137F.
- **Prototype retirement criteria.** Retiring `prototypes/
  typed_authority_inspector.py` is optional and out of scope for 137G;
  if pursued, it would itself be a small, separately governed deletion
  task (not an architecture phase) once the production consumer has
  its own independent verification, since nothing production depends on
  the prototype module (Section 5.6).
- **Rollback to prototype-only state.** If the production consumer is
  found defective post-implementation, rollback is: remove the `authority`
  CLI subparser registration and delete the two new production modules;
  this reduces the repository to exactly its pre-137K state, since no
  other production module will depend on these two files (Section 5.6
  forbids any other module from importing them).
- **Package rollback.** A wheel rebuild without the two new files is a
  strict subset of the current package; no data migration is implied
  because the consumer persists nothing.
- **CLI rollback.** Removing the `authority` subparser is a pure
  argparse-registration change with no state to reconcile.
- **Output compatibility.** N/A for a first release; future compatibility
  constraints begin applying once the consumer ships (Section 18).

No migration or rollback execution is authorized by this phase; the above
is architecture for a future scenario, not an action taken now.

---

## 25. Future Phase Sequence

The default sequence proposed by this phase's own brief is adopted
unchanged, since nothing in this review surfaces a reason to deviate:

- **137H — Production Consumption Contract Freeze.** Converts this
  architecture into normative TAMC-successor (or companion) contract
  text: exact module/function names, exact CLI flag set, exact failure
  category strings, exact Section 14 immutability-hardening mechanism,
  exact offline-resource-resolution mechanism.
- **137I — Production Consumption Contract Independent Verification.**
  Independently re-derives 137H, adversarially tests its boundaries
  (mirroring Phase 137C's treatment of TAMC-001), and does not accept
  137H's own claims as an oracle.
- **137J — Production Consumer Implementation Planning.** The production
  analog of TAMP-001: a concrete implementation blueprint against the
  now-frozen 137H contract, including exact test fixture design.
- **137K — First Production Read-Only Consumer Implementation.**
  Implements exactly `authority_inspection.py` + `authority_inspect.py` +
  CLI registration + tests, per 137J, with no architectural expansion —
  the same discipline TAMP-001 §10.1 already required of Phase 137E.
- **137L — First Production Consumer Independent Verification.**
  Independently re-derives 137K from 137H/137I and live repository state,
  adversarially tests it (mirroring Phase 137F's treatment of the
  prototype and, especially, Phase 137F.1V's demonstrated value of fresh
  adversarial fixtures over reused ones), and confirms Runtime remains
  Observed / observe / unavailable throughout.

No phase in this sequence may be skipped; contract freeze and independent
verification are not optional shortcuts, per both this document's own
governing brief and TAMC-REQ-018's existing requirement that any Future
Consumer complete a dedicated architecture phase *and* a dedicated
contract-freeze phase before becoming Allowed.

---

## Required Review — Findings and Resulting Architectural Changes

Performed as a final, explicit pass before finalizing the document above,
checking for the fourteen concern categories the governing brief names:

| Concern | Finding | Resulting change |
|---|---|---|
| Prototype assumptions leaking into production | The prototype's caller-supplied `package_root`/`manifest_path` is the single largest such leak — a production CLI cannot ask an ordinary user to supply internal package paths. | Section 5.7/19 fix package-relative resolution as the one architected difference from the prototype. |
| Unnecessary abstraction | An early draft of this review considered a "generic consumer framework" spanning multiple future surfaces (CLI, diagnostics, reporting) at once. | Rejected — Section 3 selects exactly one consumer; TAMC-REQ-058's explicit-opt-in-per-family discipline is preserved, but no generic multi-surface abstraction is introduced. |
| Premature generic frameworks | Considered whether the dispatch table should become a plugin-style registry to ease future family additions. | Rejected — Section 5.2/18 keep the dispatch table a private, static dict literal; TAMC-REQ-058 requires explicit governed opt-in per family, which a plugin registry would weaken. |
| Hidden authority semantics | Checked whether any proposed output field (`schema_validation`, `model_validation`) could be misread as an authority signal. | None found beyond what TAMC-001 already addresses; Section 17 restates the exact non-implications explicitly for this consumer's own output. |
| Hidden lifecycle semantics | Checked whether CLI exit code 0/1 could be misread as a lifecycle gate (e.g., used in a CI check as a completion signal). | Section 9/15 explicitly disclose that exit status reflects inspection outcome only, never phase completion; no lifecycle import exists to make this a real risk, only a documentation risk, now addressed. |
| Hidden runtime semantics | Checked whether "production command" framing could be misread as granting execution capability. | Section 16 explicitly distinguishes "lives in the packaged CLI" from "grants runtime capability" — the two are unrelated, and this document says so directly. |
| Ambient repository coupling | Checked whether packaging-relative resolution (Section 19) itself constitutes forbidden "discovery." | It does not — resolving the *installed package's own* fixed data location is not repository discovery of a *record*; the record identity always remains the one explicit CLI path argument. Distinguished explicitly in Section 5.7 to prevent this being misread later. |
| Duplicated validation | Checked whether any new component reimplements schema/model validation. | None — Section 6/Section 5.5 keep all validation calls delegated to existing Stage 3 owners. |
| Provenance loss | Checked whether human-readable (non-JSON) output could drop a field for brevity. | Section 9 requires both output modes to carry every Section 11 item; no brevity exception is granted. |
| Output ambiguity | Checked whether human-readable and `--json` output could diverge in content, not just format. | Section 9 requires field parity between the two modes; only presentation differs. |
| Failure ambiguity | Checked whether the three new filesystem-boundary failure categories (Section 10) could collide in meaning with existing Stage 3 categories. | No collision — they are ordered strictly before the parse step (Section 7), so precedence is unambiguous. |
| Packaging fragility | Checked whether the offline-resource-resolution approach is provably robust to editable installs vs. built wheels. | Not provable at the architecture stage; Section 20 requires a genuine packaging test (install + run) rather than assuming symmetry, directly following the Phase 106D packaging-incident precedent already documented in this repository's own `pyproject.toml`. |
| Security gaps | Checked whether a maliciously large or deeply nested JSON record could cause resource exhaustion before the existing Stage 3 size limits apply. | Section 8/12 require a CLI-level size gate applied before any bytes are handed to the parser, closing this gap explicitly rather than relying solely on whatever internal limits `pcae.schema_runtime.limits` already provides for its own callers. |
| Future extensibility risk | Checked whether today's design would need to be reworked to add a second future consumer (e.g., a report integration) later. | Section 5's dependency direction (nothing else imports `authority_inspection.py`; it only imports downward) means a second, later consumer can be added independently without modifying this one — confirmed as a design property, not merely hoped for. |

No finding above required reopening a settled Primary Question (Section
"Primary Questions" of the governing phase brief, all ten of which are
answered across Sections 1–25); each finding either confirmed an existing
architectural decision or added a specific, named constraint already
folded into the section it concerns.

---

## Governance

Confirmed at the time of finalizing this document:

- Repository: clean (`git status`).
- `origin/main..HEAD`: 0.
- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae doctor task-memory`: clean.
- `pcae push` (readiness check only; no push performed by this phase):
  clean.
- `pcae status coherence`: coherent.
- Canonical 137F report present and consistent (recovered per 137F.1/
  137F.1V and independently re-confirmed present at
  `.pcae/phase-reports/20260719-173711-137F.json` during this phase's own
  research).
- 137F.1 repair report present
  (`docs/PHASE_137F1_CANONICAL_REPORT_FINALIZATION_RECOVERY_AND_PUSH_SEMANTICS_REPAIR.md`).
- 137F.1V verification report present
  (`docs/PHASE_137F1V_CANONICAL_REPORT_FINALIZATION_RECOVERY_AND_PUSH_SEMANTICS_INDEPENDENT_VERIFICATION.md`).
- Bootstrap recommended 137G at session start.
- Runtime: Observed / observe / unavailable.

## Success Criteria Confirmation

- The verified prototype receives a clear production-suitability verdict:
  **SUITABLE WITH REQUIRED ARCHITECTURAL CHANGES** (Section 1). ✅
- Exactly one first production consumer is selected: `pcae authority
  inspect <path>` (Section 3). ✅
- Production package and dependency boundaries are defined (Sections 5,
  19). ✅
- Input and output contracts are architecturally fixed (Sections 8–9). ✅
- Failure taxonomy is defined (Section 10). ✅
- Ownership is unambiguous (Section 6). ✅
- Provenance requirements are complete (Section 11). ✅
- Security requirements are complete (Section 12). ✅
- Determinism and immutability requirements are defined (Sections 13–14).
  ✅
- Lifecycle, runtime, and authority boundaries remain intact (Sections
  15–17). ✅
- TAMC traceability is complete (Section 21, all 76 requirement IDs
  mapped). ✅
- Production implementation preconditions are explicit (Section 22). ✅
- No production code is implemented by this phase. ✅
- Runtime remains Observed / observe / unavailable. ✅
- No Blocking finding remains (Section "Required Review" above; none
  surfaced). ✅

## Recommended Next Phase

**137H — Typed Authority Model Production Consumption Contract Freeze.**

This phase (137G) concludes that the verified prototype is suitable, with
the explicitly identified architectural changes in Sections 2.10, 14, and
19, for a single bounded production read-only consumer:
`pcae authority inspect <path>`. Proceeding to 137H is authorized by this
conclusion; 137H itself still requires its own separately authorized task
contract, and grants no implementation authority by virtue of this
recommendation alone.
