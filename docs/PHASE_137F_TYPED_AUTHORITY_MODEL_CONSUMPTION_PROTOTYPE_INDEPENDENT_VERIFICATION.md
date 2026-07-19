# Phase 137F — Typed Authority Model Consumption Prototype Independent Verification

## Verification identity

**Phase:** 137F
**Subject:** the Phase 137E TAMP-001 explicit-artifact inspector
(`prototypes/typed_authority_inspector.py`,
`tests/test_typed_authority_inspector_137e.py`)
**Governing artifacts:** TAMC-001 v1.0, TAMP-001 v1.0, Stage 3 frozen Typed
Authority Model (`src/pcae/cltr/authority/*`, `src/pcae/schema_runtime/*`,
`src/pcae/schema_resources/cltr_cutover/**`), live repository state at commit
`3100aa47`.
**Method:** independent re-derivation and adversarial testing. Phase 137E's
tests, dispatch table, claims, and metrics were not accepted as an oracle;
each conclusion below was re-derived from the contracts and re-checked
against live code, or freshly exercised with adversarial inputs constructed
for this phase.
**Runtime posture during this phase:** Observed / observe / unavailable
(unchanged; verified before and after review, see §11).

## 1. Prototype scope

Independently confirmed:

- Exactly one prototype consumer exists: `inspect_explicit_artifact()` in
  `prototypes/typed_authority_inspector.py`. No second consumer, wrapper, or
  CLI was introduced.
- The prototype lives at repository-root `prototypes/`, outside
  `src/pcae/` (the packaged production source tree; `pyproject.toml` scopes
  `packages = ["src/pcae"]`, so `prototypes/` is not shipped as part of the
  `pcae` package).
- `git diff --stat` across the full 137D→137E commit range touches only
  `prototypes/typed_authority_inspector.py`, its test file, documentation,
  and task/status bookkeeping files. No file under `src/pcae/` was added or
  modified.

## 2. Stage 3 reuse

Read `prototypes/typed_authority_inspector.py` line by line against its
imports:

- Typed models: imported directly from `pcae.cltr.authority` (all sixteen
  family classes plus `OpaqueJsonValue`), used via their existing
  `from_dict`/`to_dict` boundaries only. No model class or validation
  method is redefined locally.
- Registry: `pcae.schema_runtime.build_offline_registry`, called unchanged.
- Manifest: `pcae.schema_runtime.load_and_verify_manifest`, called unchanged.
- Serializers: `pcae.cltr.authority.serialization.to_canonical_bytes`,
  `OpaqueJsonValue.to_json()`, both existing owners.
- Validators: `pcae.schema_runtime.validate_record_shape` (Draft 2020-12),
  called unchanged.

No Stage 3 logic is copied. The module's only local logic is: byte-type/
JSON-shape gating before dispatch, a static family→model dict (data, not
behavior), a stack-based provenance-field collector, and dataclass result
construction. None of this duplicates schema shape, registry resolution,
manifest verification, or model construction rules.

## 3. Consumer boundary

- `grep -rl "typed_authority_inspector" src/pcae/` returns no matches.
- The one substring hit for `"prototypes"` inside `src/pcae/cli.py:4507` is
  an unrelated help string for a pre-existing "Repository Intelligence
  prototypes" surface, not a reference to this module — verified by reading
  the surrounding line directly, not by the test's assumption.
- No entry in `src/pcae/commands/` imports, calls, or registers the
  inspector.
- No dynamic import, entry-point, plugin registration, or string-based
  dispatch to the module exists anywhere in `src/pcae/`.
- No dependency inversion: the dependency graph is one-directional
  (inspector → Stage 3 owners → stdlib); Stage 3 modules do not import the
  prototype.

Independent conclusion: the prototype is isolated. No hidden activation
path was found.

## 4. TAMC-001 compliance re-derivation

Re-derived category by category, independent of Phase 137E's own table:

| Category | Independent finding |
|---|---|
| Consumer Classification (001–021) | Exactly one Allowed `inspection` operation. It returns a value; it registers nothing; it has no CLI, report, reconciliation, or migration behavior. Classified Allowed under TAMC-REQ-012, not Future or Forbidden. |
| Consumer Invariants (022–032) | Confirmed by direct adversarial replay (see §6–7): byte-identical repeated output, no mutation, deterministic ordering (`sorted()` used explicitly in the provenance collector and manifest-entry filter), explainable output (`record_claims` vs. `provenance` fields are explicitly separated). |
| Ownership (033–034) | Verified above (§2): every responsibility in TAMC-001's ownership table is called through its sole owner. |
| Authority (035–038) | Adversarially probed (§9): no representation, including a forged `is_authoritative: true` claim, produces an operative field or changes the unconditional disclosure. |
| Validation (039–041) | `to_dict()` hardcodes `"semantic": "not_performed"`, `"lifecycle": "not_performed"`, `"governance": "not_performed"` and keeps `schema`/`model` outcomes in separate keys — verified directly in code and by test, not assumed. |
| Provenance (042–045) | Verified field-by-field in §8. |
| Runtime (046–048) | Verified in §11: `pcae runtime inspect` unchanged before/after; static scan (below) finds no runtime import. |
| Lifecycle (049–051) | Verified in §10: no task/session/report import; live governance state unchanged after exercising the module. |
| Error Handling (052–055) | Verified in §12 with fresh adversarial fixtures, not only the shipped ones. |
| Extensibility (056–059) | `_MODEL_BY_FAMILY` is a static dict of exactly 16 entries matching the manifest's 16 record-family entries (independently counted from `manifest.json`, §13). An unrecognized `record_type` fails `unknown_record_family` with no dynamic import or filename inference. |
| Security (060–064) | Recursive immutability of nested content confirmed via `OpaqueJsonValue`/`MappingProxyType`; one non-blocking observation on the *outer* result dataclass, see §14 finding NB-1. |
| Compatibility (065–067) | `TAMC_CONTRACT_VERSION`, `SUPPORTED_SCHEMA_VERSION`, `SUPPORTED_MODEL_VERSION` are all pinned literals (`"1.0"`); mismatches fail closed (verified in §12), no nearby-version fallback exists in the code. |
| No-Go (068–069) | Independent AST-level import scan (reproduced myself, not reusing the shipped test) finds no runtime, subprocess, socket, network, lifecycle, or commands import. See below. |

Independent static scan reproduced directly (not trusting the shipped test):

```
$ python - <<'EOF'
import ast
tree = ast.parse(open("prototypes/typed_authority_inspector.py").read())
names = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        names.update(a.name for a in n.names)
    elif isinstance(n, ast.ImportFrom) and n.module:
        names.add(n.module)
print(sorted(names))
EOF
['__future__', 'dataclasses', 'hashlib', 'pathlib', 'pcae.cltr.authority',
 'pcae.cltr.authority.errors', 'pcae.cltr.authority.serialization',
 'pcae.schema_runtime', 'typing']
```

No runtime, lifecycle, commands, subprocess, socket, or network module is
imported. This independently reproduces (rather than assumes) the No-Go and
Runtime/Lifecycle evidence claimed in the Phase 137E documentation.

## 5. TAMP-001 compliance

Compared the implementation against TAMP-001 §3–§5 component-by-component:

- The four planned components (orchestrator, family dispatch, provenance
  assembler, immutable result model) map onto
  `inspect_explicit_artifact`/`_MODEL_BY_FAMILY`/`_provenance_bundle`/
  `InspectionSuccess`+`InspectionFailure` exactly as planned. No additional
  component (e.g., a renderer, cache, or CLI) was introduced.
- The read-only data flow in TAMP-001 §4 (parse → registry → manifest →
  dispatch → schema → model → provenance → result) matches the code's
  actual control flow exactly, confirmed by reading the function body
  top to bottom (§ code walk above, lines 288–465 of the module).
- No undocumented expansion found: the module contains no additional public
  function, class, or side channel beyond what TAMP-001 §3.2 specifies the
  inspector "SHALL expose."
- No architectural drift: dependency direction, physical single-module
  layout, and extension point (dispatch-table-only) all match TAMP-001 §5.

## 6. Determinism

Independently re-ran the shipped replay test's fixture twice in a fresh
process and separately constructed a new adversarial record
(`authority_state` with an internally consistent but not previously used
combination of fields) and inspected it twice:

- Identical input bytes → byte-identical `to_canonical_bytes()` output on
  both occasions.
- Identical malformed input (`b"{"`, duplicate-key JSON, non-JSON) →
  identical failure category and message on repeat.
- The manifest-entry filter and provenance-field collector both call
  `sorted(...)` explicitly (verified at lines 222 and 231, and 361–365 use
  a list comprehension over a manifest document whose entry order is fixed
  by the frozen, git-tracked `manifest.json`), so ordering does not depend
  on filesystem traversal order.

No wall-clock, randomness, or ambient state dependency was found in the
source.

## 7. Read-only verification (mutation attempts)

Independently attempted, all failed as required:

- Recorded SHA-256 of every file in the Stage 3 fixture package root before
  and after two consecutive inspections of a `certification` record: hashes
  identical.
- Compared the exact input `bytes` object before and after inspection:
  unchanged.
- Attempted direct field assignment on a returned `InspectionSuccess`
  (`res.record_family = "tampered"`): raised
  `dataclasses.FrozenInstanceError`, blocked as required.
- Confirmed via `pcae health`/`pcae check`/`pcae status coherence` before
  and after exercising the module that no lifecycle, session, or task state
  changed (see §10, §15).

No write, persistence, or lifecycle update was achieved by any attempt.

## 8. Provenance verification

Verified field-by-field against TAMC-REQ-042–045 using a fresh
`certification` fixture, reading `to_dict()` output directly rather than
trusting the shipped assertions:

- `source_artifact_identity`, `source_location`, `schema_package_identity`
  are preserved verbatim from the caller-supplied context.
- `input_digest` (derived, labeled distinctly) and `declared_record_digest`
  (copied from the record) are two separate fields; the code never
  overwrites one with the other (confirmed at lines 109/115, 469/475).
- `record_family`, `record_identity`, `schema_identity`, `schema_version`,
  `model_version` are all populated from validated record content, not
  inferred.
- `manifest_entry` and `registry_resource` are reported as observations
  (raw dict copies), not authority.
- `record_claims` holds the complete lossless typed record
  (`typed_wire == record` is enforced as a precondition at line 446 before
  a success can be returned at all — a forged or lossy round trip cannot
  produce a success result).
- `provenance.copied_provenance_values` independently walks the record for
  `limitations`, `authority_disclosure`, `derivation`, `extensions`,
  `opaque`, `uncertainty`, and any `*_reference(s)` key — verified this
  captures `/candidate_reference`, `/limitations`, and
  `/authority_disclosure` for a `certification` fixture, matching what
  TAMC-REQ-042 requires preserved.
- The unconditional disclosure string is present in both
  `InspectionSuccess.disclosure` and `provenance.authority_neutrality`.

No provenance loss was demonstrated in any attempt.

## 9. Authority verification (adversarial)

Constructed adversarial payloads attempting to make the result look
operative:

- **Attempt 1:** an `authority_state` record with
  `authority_disclosure.is_authoritative: true` and `verification_state:
  "verified"`. Result: `InspectionFailure` with `schema_validation_failed`.
  Independent inspection of the frozen Stage 3 schema files
  (`authority_epoch.schema.json`, `authority_state.schema.json`, etc.)
  shows `is_authoritative` is declared `"const": false` in the shared
  `authority_disclosure` definition for every record family except
  `publication_evidence`, where it is still unconditionally `const false`
  per that schema's own text. This means a forged authoritative claim is
  rejected by the frozen Stage 3 schema itself, before the prototype's own
  logic is reached — a stronger authority-neutrality guarantee than the
  prototype alone provides, and consistent with TAMC-REQ-035/036.
- **Attempt 2:** a `human_authorization` record with `state: "issued"` (a
  legitimately schema-valid claim). Result: `InspectionSuccess`, but the
  top-level output has no `approved`/`authoritative`/`ready`/`active`/
  `executable`/`complete`/`authorized` key, and `disclosure` is the fixed
  representation-only text regardless of the claim. The "issued" value is
  reachable only inside `record_claims`, i.e., as a copied claim, not an
  operative field.
- No combination of registry membership, manifest membership, or successful
  schema/model validation produced an authority-implying field. The
  representation-only disclosure is unconditional in every success path
  (it is a dataclass default, not a computed branch), so it cannot be
  suppressed by any input.

Every attempt to derive authority failed.

## 10. Lifecycle verification

- `pcae health`, `pcae check`, `pcae status coherence`, and
  `pcae doctor task-memory` were run before this verification began and
  after multiple inspector invocations (including with a `cutover_request`,
  `certification`, and `human_authorization` fixture, all fields
  suggestive of an in-progress lifecycle transition). No task, session,
  phase, or health state changed as a result of the exercises.
- No import of `pcae.core.tasks`, `pcae.core.session`, `pcae.commands`,
  or phase-report modules exists in the prototype (§4 static scan).
- No lifecycle-shaped field (`state: "pending"`, `state: "issued"`,
  `authorization_requirement: True`) altered which branch of the code ran;
  these values only ever reach `record_claims` as copied data.

No lifecycle completion, authorization, certification, publication,
recovery, or cutover was demonstrated.

## 11. Runtime verification

`pcae runtime inspect` output, captured immediately before and after
running the full adversarial exercise in this phase:

```
Runtime status:            not_implemented
Runtime state:             Observed
Execution capability:      unavailable
Maximum plugin capability: observe
```

Identical both times. No execution, activation, execution adapter, or
capability escalation was reachable — confirmed both by the static import
scan (§4) and by this live before/after comparison.

## 12. Error handling (fresh adversarial fixtures)

Constructed and ran fixtures not present in the shipped test suite, in
addition to confirming the shipped ones pass:

- Truncated/duplicate-key/non-object JSON (`b"{"`, `{"x":1,"x":2}`,
  `b"[]"`, `b"not-json"`): `malformed_artifact`, stable on replay.
- `record_type` set to an unregistered value: `unknown_record_family`,
  no dynamic import attempted.
- `schema_version`/`contract_version` set to `"2.0"`: rejected as
  `unsupported_schema_version` / `unsupported_model_version`, no
  nearby-version selection.
- Empty `source_artifact_identity` in the caller context:
  `required_provenance_failed`, fails before any Stage 3 owner is invoked.
- Forged `authority_disclosure.is_authoritative: true` (adversarial,
  independently constructed for this phase): `schema_validation_failed` —
  fails closed rather than silently accepting or coercing the claim.
- Monkeypatched `build_offline_registry`/`load_and_verify_manifest` to
  raise with an ambient-looking path string in the exception message:
  confirmed the returned failure message does not leak that string
  (`registry_failure`/`manifest_failure`, sanitized).

All failures were stable, closed, and free of retry/fallback/coercion
behavior.

## 13. Repository boundary

- `git status`: clean.
- `git diff --stat` across the full 137D–137E range: only
  `prototypes/typed_authority_inspector.py`,
  `tests/test_typed_authority_inspector_137e.py`, documentation, and
  task/status bookkeeping files changed. No file under
  `src/pcae/cltr/authority/`, `src/pcae/schema_runtime/`, or
  `src/pcae/schema_resources/cltr_cutover/` was touched.
- Independently parsed `manifest.json`: 23 total entries, exactly 16 with
  `file_path` under `records/`, one per family, matching the frozen
  family inventory with no ambiguity. This is a manifest invariant the
  inspector relies on (its manifest-entry filter assumes exactly one
  matching entry) but does not itself enforce or alter — it fails closed
  (`manifest_entry_missing`) if that invariant is ever violated, so no
  the inspector doesn't silently trust an untested assumption.
- No TAMC-001 or TAMP-001 document was modified by Phase 137E (confirmed
  both are unchanged since their respective freeze/publish commits, per
  `git log -p` scoped to those two files showing no post-freeze commits
  touching them within the 137D–137E range).

## 14. Adversarial review — findings

| ID | Severity | Finding |
|---|---|---|
| NB-1 | NON-BLOCKING | `InspectionSuccess`/`InspectionFailure` are ordinary `@dataclasses.dataclass(frozen=True)` objects. Their *top-level scalar fields* can be mutated via `object.__setattr__(result, "record_family", "tampered")`, which succeeds (verified directly). This is standard Python `frozen=True` behavior, not a defect introduced by this implementation, and it does not affect the *nested* nested content, which is protected by the stronger `OpaqueJsonValue`/`MappingProxyType` freezing Stage 3 already uses. TAMC-REQ-060 binds what a *consumer* must not do to bypass immutability (of Stage 3 records); it does not require the consumer's own transient return value to resist a determined in-process caller. No exploitation path exists through the inspector's own public API — this would require a downstream caller intentionally reaching for `object.__setattr__`, which is out of scope for TAMC-001's threat model of ambient/production consumption. Recorded as a documentation-worthy observation, not a contract violation. |
| NB-2 | NON-BLOCKING | The manifest-entry lookup (`inspect_explicit_artifact`, lines 361–365) assumes the verified manifest contains exactly one entry per record family under `records/`. This is true of the live, frozen `manifest.json` (independently confirmed, §13) and is enforced only by the prototype's own `manifest_entry_missing` fallback if violated in the future (i.e., it fails closed, it does not silently pick one of several). No live defect exists today; flagged only as an implicit dependency on a manifest invariant that the manifest owner, not the inspector, is responsible for guaranteeing. |

No BLOCKING finding was found in any of the fourteen required verification
areas. No hidden authority leakage, lifecycle leakage, runtime leakage,
provenance leakage, ownership violation, implementation shortcut,
undocumented assumption (beyond NB-2, which is disclosed above),
architectural drift, or hidden coupling was discovered.

## 15. Governance state

Checked independently, not assumed from Phase 137E's own report:

- Repository: clean (`git status`).
- `origin/main..HEAD`: 0 (fetched `origin/main` and compared).
- `pcae health`: healthy (idle).
- `pcae check`: passed.
- `pcae doctor task-memory`: clean, no inconsistencies.
- `pcae status coherence`: coherent.
- `pcae push`: nothing to push.
- `pcae runtime inspect`: Observed / observe / unavailable, unchanged
  before and after this verification (§11).

## 16. Verdict

**VERIFIED**

The Phase 137E prototype independently re-derives as TAMC-001 compliant and
TAMP-001 compliant. It is read-only, deterministic, provenance-complete,
authority-neutral, lifecycle-neutral, runtime-neutral, and isolated from
production. No Blocking finding was discovered under adversarial testing
constructed independently of Phase 137E's own evidence. Two Non-Blocking
observations (NB-1, NB-2) are recorded for future reference; neither
requires repair, and no documentation or implementation repair is made in
this phase since no Blocking defect was found.

Runtime remains:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## Recommended next phase

**137G — Typed Authority Model Prototype Review and Production Integration
Architecture**, to determine whether this verified prototype is suitable
for production integration and to define the architecture for a first
governed production consumer without expanding runtime capabilities. This
phase (137F) authorizes only its own verification review; it does not
authorize 137G's scope, design, or implementation.
