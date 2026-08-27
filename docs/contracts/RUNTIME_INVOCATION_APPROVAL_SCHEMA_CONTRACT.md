# RIASC-001 v1.0 — RuntimeInvocationApproval Schema Contract

## Contract identity and status

**Contract:** RIASC-001  
**Version:** 1.0  
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3V  
**Semantic authority:** RIHAC-001 v1.0  
**Artifact type:** `runtime_invocation_approval`  
**Scope:** Normative Markdown schema contract for future local-CLI-v1
approval artifacts.

This phase intentionally does not add an executable schema under
`src/pcae/schema_resources/**`: repository precedent treats those files,
their manifests, and validation wiring as production behavior. The complete
Draft 2020-12 shape is frozen below so a later implementation can transcribe
it under separately authorized governance without redesigning it.

## 0. Non-authority rule

Schema conformance, digest agreement, storage presence, and identifier shape
do not independently create human authority. Authority exists only through
RIHAC-001's explicit human act plus successful current validation.

No field named `approved`, `authorized`, `permission`, `pb_allow`, or an
equivalent authority shortcut is permitted. `additionalProperties:false`
applies recursively to every object.

## 1. Schema identity and versioning

| Field | Frozen value/meaning |
|---|---|
| `$id` | `https://pcae.local/contracts/runtime-invocation-approval/1.0/schema.json` |
| `schema_id` | const `RIASC-001` |
| `schema_version` | const `1.0` (MAJOR.MINOR) |
| `contract_version` | const `RIHAC-001/1.0` |
| `record_type` | const `runtime_invocation_approval` |

Unknown versions and unknown fields fail closed. V1 has no free-form
extension container. An additive future field requires a new schema MINOR
version and explicit reader opt-in; an authority-widening, required-field
removal, type/meaning change, or subject relaxation requires a new MAJOR.
No version may retrospectively widen an existing artifact.

## 2. Required field inventory

Exactly these sixteen top-level fields are required:

1. `schema_id`
2. `schema_version`
3. `contract_version`
4. `record_type`
5. `approval_id`
6. `record_digest`
7. `created_at`
8. `expires_at`
9. `subject`
10. `governance_context`
11. `prompt_hash_profile`
12. `approval_scope`
13. `adapter_binding`
14. `freshness_snapshot`
15. `provenance`
16. `attempt_limit`

## 3. Exact subject and immutable identifiers

The closed `subject` object contains exactly the five 3U-selected members:

| Field | Type | Meaning |
|---|---|---|
| `invocation_id` | `^inv-[0-9a-f]{32}$` | PCAE-generated logical invocation identity |
| `runtime_target_id` | non-empty string, max 128 | Exact selected target; no fallback |
| `prompt_hash` | 64 lowercase hex | `pcae.prompt-semantic.v1` semantic prompt digest |
| `repository_identity` | 64 lowercase hex | Existing git-root repository fingerprint |
| `task_id` | non-empty string, max 256 | Exact active task |

`approval_id` uses `^ria-[0-9a-f]{32}$`, is allocated by the trusted approval
coordinator, and is immutable/non-reusable. Neither identifier is supplied by
the external runtime or adapter.

## 4. Governance context

`governance_context.phase_id` is required for the governed-phase local-CLI
v1 path. `session_id` is optional and SHALL be present if and only if the
invocation occurs inside an explicitly session-scoped interactive workflow.
Absence means “not session-scoped,” never unknown or defaulted.

## 5. Scope and adapter binding

`approval_scope` binds requested capability, local transport, one bounded
process-dispatch effect, dispatch limit one, no network requirement,
filesystem-scope reference, and process-containment-profile reference.
References are closed ID/digest pairs and grant no permission by themselves.

`adapter_binding` binds stable adapter identity, descriptor version/digest,
and target-configuration digest. Executable identity is deliberately absent:
it is descriptor-pinned and live-preflight verified immediately before
dispatch under RDGO-001.

## 6. Freshness snapshot

The immutable snapshot contains:

- `head_commit`;
- `task_contract_digest`;
- `task_state` fixed to `active`; and
- `policy_version` observed at approval creation.

Prompt, target, repository, and task IDs are in the subject; adapter
configuration is in `adapter_binding`; expiry is top-level. Together these
encode all seven RIHAC-001 freshness conditions. Policy drift invalidates
cached PB/Runtime Enforcement decisions and blocks dispatch until fresh
decisions exist; it does not rewrite the historical approval record.

## 7. Provenance

The closed provenance object records:

- `approver_id` — identified human, not artifact producer;
- `identity_evidence_kind` — `typed_confirmation_only` or
  `os_authenticated_user`;
- `approval_mechanism` — const `interactive_local_cli_confirmation`;
- `approval_preview_digest` — exact rendered approval-preview digest; and
- `producer_component` — const
  `pcae.trusted_runtime_approval_coordinator`.

There is no free-form authority claim. Human identity evidence strength is
recorded honestly; v1 does not require a cryptographic signature.

## 8. Canonicalization and tamper detection

Before computing `record_digest`:

1. remove only the top-level `record_digest` field;
2. normalize every string to Unicode NFC;
3. serialize as UTF-8 compact JSON;
4. recursively sort object keys by ASCII lexicographic order;
5. preserve array order (this schema currently contains no arrays); and
6. compute SHA-256, encoded as 64 lowercase hexadecimal characters.

The stored `record_digest` SHALL exactly match recomputation. Digest mismatch,
duplicate conflicting identity, non-canonical encoding, or partial content
fails closed. Digest validity does not prove authority.

## 9. Time, consumption, and revocation representation

`created_at` and `expires_at` use UTC RFC 3339 with required `Z`, seconds,
and optional 1–6 fractional digits. Validation additionally requires
`expires_at > created_at` and current time before `expires_at`; JSON Schema
shape alone cannot prove those relations.

There is deliberately no mutable `consumed`, `used`, or `revoked` field.
One-shot scope is frozen by `attempt_limit=1` and
`approval_scope.dispatch_limit=1`; actual consumption is the separately
durable gate-9 `dispatch_attempted` record linked by approval ID/digest.
Explicit revocation is deferred as RIHAC-001 specifies.

## 10. Normative Draft 2020-12 shape

The following JSON Schema is normative contract text. It is not registered or
production-consumed by this phase.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://pcae.local/contracts/runtime-invocation-approval/1.0/schema.json",
  "title": "PCAE RuntimeInvocationApproval",
  "description": "RIASC-001 v1.0 local-CLI one-shot human-authority artifact. Shape validity does not establish authority.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_id",
    "schema_version",
    "contract_version",
    "record_type",
    "approval_id",
    "record_digest",
    "created_at",
    "expires_at",
    "subject",
    "governance_context",
    "prompt_hash_profile",
    "approval_scope",
    "adapter_binding",
    "freshness_snapshot",
    "provenance",
    "attempt_limit"
  ],
  "$defs": {
    "sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "timestamp": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{1,6})?Z$"
    },
    "nonempty_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "pattern": "^[^\\s].*[^\\s]$|^[^\\s]$"
    },
    "artifact_ref": {
      "type": "object",
      "additionalProperties": false,
      "required": ["artifact_id", "artifact_digest"],
      "properties": {
        "artifact_id": { "$ref": "#/$defs/nonempty_id" },
        "artifact_digest": { "$ref": "#/$defs/sha256" }
      }
    }
  },
  "properties": {
    "schema_id": { "const": "RIASC-001" },
    "schema_version": { "const": "1.0" },
    "contract_version": { "const": "RIHAC-001/1.0" },
    "record_type": { "const": "runtime_invocation_approval" },
    "approval_id": {
      "type": "string",
      "pattern": "^ria-[0-9a-f]{32}$"
    },
    "record_digest": { "$ref": "#/$defs/sha256" },
    "created_at": { "$ref": "#/$defs/timestamp" },
    "expires_at": { "$ref": "#/$defs/timestamp" },
    "subject": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "invocation_id",
        "runtime_target_id",
        "prompt_hash",
        "repository_identity",
        "task_id"
      ],
      "properties": {
        "invocation_id": {
          "type": "string",
          "pattern": "^inv-[0-9a-f]{32}$"
        },
        "runtime_target_id": {
          "type": "string",
          "minLength": 1,
          "maxLength": 128,
          "pattern": "^[^\\s].*[^\\s]$|^[^\\s]$"
        },
        "prompt_hash": { "$ref": "#/$defs/sha256" },
        "repository_identity": { "$ref": "#/$defs/sha256" },
        "task_id": { "$ref": "#/$defs/nonempty_id" }
      }
    },
    "governance_context": {
      "type": "object",
      "additionalProperties": false,
      "required": ["phase_id"],
      "properties": {
        "phase_id": { "$ref": "#/$defs/nonempty_id" },
        "session_id": { "$ref": "#/$defs/nonempty_id" }
      }
    },
    "prompt_hash_profile": { "const": "pcae.prompt-semantic.v1" },
    "approval_scope": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "requested_capability",
        "transport_type",
        "effect_class",
        "dispatch_limit",
        "network_required",
        "filesystem_scope_ref",
        "process_profile_ref"
      ],
      "properties": {
        "requested_capability": { "$ref": "#/$defs/nonempty_id" },
        "transport_type": { "const": "local_cli" },
        "effect_class": { "const": "bounded_local_process_dispatch" },
        "dispatch_limit": { "const": 1 },
        "network_required": { "const": false },
        "filesystem_scope_ref": { "$ref": "#/$defs/artifact_ref" },
        "process_profile_ref": { "$ref": "#/$defs/artifact_ref" }
      }
    },
    "adapter_binding": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "adapter_id",
        "descriptor_version",
        "descriptor_digest",
        "target_config_digest"
      ],
      "properties": {
        "adapter_id": { "$ref": "#/$defs/nonempty_id" },
        "descriptor_version": { "$ref": "#/$defs/nonempty_id" },
        "descriptor_digest": { "$ref": "#/$defs/sha256" },
        "target_config_digest": { "$ref": "#/$defs/sha256" }
      }
    },
    "freshness_snapshot": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "head_commit",
        "task_contract_digest",
        "task_state",
        "policy_version"
      ],
      "properties": {
        "head_commit": {
          "type": "string",
          "pattern": "^[0-9a-f]{40,64}$"
        },
        "task_contract_digest": { "$ref": "#/$defs/sha256" },
        "task_state": { "const": "active" },
        "policy_version": { "$ref": "#/$defs/nonempty_id" }
      }
    },
    "provenance": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "approver_id",
        "identity_evidence_kind",
        "approval_mechanism",
        "approval_preview_digest",
        "producer_component"
      ],
      "properties": {
        "approver_id": { "$ref": "#/$defs/nonempty_id" },
        "identity_evidence_kind": {
          "enum": ["typed_confirmation_only", "os_authenticated_user"]
        },
        "approval_mechanism": {
          "const": "interactive_local_cli_confirmation"
        },
        "approval_preview_digest": { "$ref": "#/$defs/sha256" },
        "producer_component": {
          "const": "pcae.trusted_runtime_approval_coordinator"
        }
      }
    },
    "attempt_limit": { "const": 1 }
  }
}
```

## 11. Cross-field validation beyond JSON Schema

Schema-shape validation is necessary but insufficient. The future validator
SHALL additionally enforce:

- `expires_at > created_at` and current trusted time before expiry;
- canonical record-digest recomputation;
- exact five-member subject equality with the invocation request;
- exact governance-context applicability and equality;
- approval scope equality with PB request and containment plan;
- descriptor/config digest equality and freshness;
- all seven RIHAC-001 invalidation conditions;
- canonical storage path/identity and exactly one matching artifact;
- no prior gate-9 consumption/cancellation/uncertainty/completion binding;
- approval-preview digest correspondence to what the human reviewed; and
- producer identity distinct from approving human identity.

Failure of any check yields no validated-authority projection and no real
dispatch.

## 12. Storage and reference contract

Canonical storage is:

```text
.pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json
```

References use the pair `(approval_id, record_digest)`. The approval is
create-only, immutable, atomically persisted, never embedded in CHGR or the
invocation record, and never loaded from a caller-selected arbitrary path.

## 13. Compatibility and implementation boundary

RIASC-001 is a separate schema family from CHGR, Typed Authority Model,
HATP, CLTR, PB, and the existing mock/dry runtime artifacts. No schema or
record from those families may be accepted as a `RuntimeInvocationApproval`
by structural similarity.

This freeze creates no executable schema resource, manifest entry, validator,
fixture, storage writer, CLI, or production behavior. A future executable
schema implementation must reproduce this frozen shape exactly and undergo
independent verification before production consumption.

## 14. Freeze verdict

**RIASC-001 v1.0 schema contract: FROZEN.**  
**Executable production schema: NOT IMPLEMENTED / NOT AUTHORIZED.**  
**Real execution: UNAVAILABLE.**
