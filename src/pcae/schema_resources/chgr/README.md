# CHGR schema resources (Phase 143E)

Canonical Human Governance Record (CHGR) schema family, per
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (CHGR-001
v1.0). Implements the schema/artifact foundation only: representation,
shape validation, and read-only inspection/verification against explicit
caller-supplied paths.

**Not implemented here or by any code that consumes these schemas:**
interactive decision workflows, substantive decision capture, human
confirmation UX, production `create`/`confirm`/`publish`/`suspend`/
`supersede`/`revoke`/`import` commands, `.pcae/governance-records/` storage
or a registry/index, legacy election import, signing, external identity
integration, runtime consumption, or authority resolution. See
`docs/PHASE_143E_CANONICAL_HUMAN_GOVERNANCE_RECORD_SCHEMA_AND_ARTIFACT_FOUNDATION_IMPLEMENTATION.md`
for the full disposition.

**Successful schema validation means only that an artifact conforms to the
CHGR representation contract. It does not establish that the represented
governance act was valid, applicable, current, or performed by an
authorized human.**

## Layout

- `manifest.json` / `manifest.schema.json` — deterministic tamper-evidence
  manifest over this package's own schema files, loaded via
  `src/pcae/schema_runtime/manifest.py:load_and_verify_manifest`.
- `shared/*.schema.json` — reusable building blocks (digest, envelope,
  identity, references, limitations, enums). Independently defined from
  `src/pcae/schema_resources/cltr_cutover/shared/*` per CHGR-001
  Sec.16/Sec.19.1's no-composition-across-artifact-families rule.
- `records/*.schema.json` — the six implemented CHGR artifact types:
  `decision_template`, `human_governance_record`,
  `human_confirmation_evidence`, `governance_record_provenance`,
  `governance_record_integrity`, `governance_record_lifecycle_event`.

Loaded via `pcae.schema_resources.chgr_root()` (mirrors
`pcae.schema_resources.cltr_cutover_root()`) and
`pcae.schema_runtime.build_offline_registry()`/`validate_record_shape()`
unchanged -- no `schema_runtime` code was modified.
