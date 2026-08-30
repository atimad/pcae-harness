# RIASC-001 v3.0 — RuntimeInvocationApproval Schema Contract

## Contract identity and status

**Contract:** RIASC-001  
**Version:** 3.0
**Status:** FROZEN  
**Frozen by:** Phase 149O.20L.7O.3W.1R.2B.1R.1 — Cross-Contract Runtime
Invocation Human-Principal Authentication Freeze Repair
**Supersedes:** RIASC-001 v1.0 and v2.0. V1/v2 artifacts are historical only
and SHALL NOT satisfy RIHAC-001 v2.0 authority; no migration exists.
**Semantic authority:** RIHAC-001 v2.0
**Artifact type:** `runtime_invocation_approval`  
**Scope:** Normative Markdown schema contract for future local-CLI-v1
approval artifacts.

This phase intentionally does not add an executable schema under
`src/pcae/schema_resources/**`: repository precedent treats those files,
their manifests, and validation wiring as production behavior. The complete
Draft 2020-12 shape is frozen below so a later implementation can transcribe
it under separately authorized governance without redesigning it.

**Reference note (149O.20L.7O.3V.1R):** PBRD-001 (now v1.1) and RDGO-001
(now v2.0) were repaired to close two BLOCKING findings from Phase
149O.20L.7O.3V.1. Those repairs left RIASC-001 v1.0 itself UNCHANGED: the
sixteen required top-level fields, the five-member `subject`, and
`attempt_limit: {"const": 1}` already correctly bound approval to one
invocation and one attempt-slot, not to a specific `attempt_id`.
`attempt_id`/`idempotency_key` are dispatch-layer identifiers minted at
RDGO-001 gate 2 and belong in the PBRD-001 request and the future
`RuntimeInvocationRecord`, not in the approval schema; expanding `subject`
or adding these fields here would be unnecessary widening. **That
determination is unaffected by, and reaffirmed by, this v2.0 amendment**:
`subject` still has exactly five members (§3, unchanged).

**Reference note (149O.20L.7O.3W.1R.2B, v2.0 — why MAJOR, not MINOR).**
Phase 149O.20L.7O.3W.1R.2A independently found finding **N2**: v1.0's
`provenance.approver_id` was an unauthenticated caller-supplied string, and
`provenance.identity_evidence_kind` was checked only for enum-membership,
never for whether the claimed evidence actually existed
(`src/pcae/core/runtime_authority.py:858-860`, read this phase and
149O.20L.7O.3W.1R.2A alike). Closing N2 requires retiring both fields'
existing meaning, not merely adding new ones alongside them: `approver_id`
(a free string) is replaced by `principal_id` (a registry-bound identifier,
meaningless without a successful `HumanPrincipalRegistry` lookup), and
`identity_evidence_kind`'s two-member claim-only enum is replaced by
`authentication_mechanism_id` (a reference to a verified, assurance-rated
mechanism, HPAC-001 §10/§14). Per this contract's own §1 versioning rule —
"an authority-widening, required-field removal, type/meaning change, or
subject relaxation requires a new MAJOR" — a required field's meaning being
redefined (not merely supplemented) is exactly this case, independently of
whether the *literal field name* changes. Retaining `approver_id` alongside
new fields was considered and rejected: an unauthenticated legacy field left
present, even if unused for trust purposes, would perpetuate exactly the
"valid provenance-shaped data != authenticated human provenance" hazard this
freeze exists to close, and would require every future reader to know, out
of band, that one required field is authoritative and a sibling required
field of the same object is not. RIASC-001 therefore evolves to **v2.0**,
The subsequent independent verification correctly found RIHAC v1.1 itself
required a MAJOR. This v3 repair pins RIHAC-001 v2.0 and changes proof and
presentation semantics incompatibly; companion versions remain independently
derived rather than forced to match numerically.

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
| `$id` | `https://pcae.local/contracts/runtime-invocation-approval/3.0/schema.json` |
| `schema_id` | const `RIASC-001` |
| `schema_version` | const `3.0` (MAJOR.MINOR) |
| `contract_version` | const `RIHAC-001/2.0` |
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

**v3.0 shape.** The closed `provenance` object's required-field set remains
re-derived, not carried forward unchanged. v1.0 had five required
`provenance` subfields; v2.0 has seven. Two are retired
(`approver_id`, `identity_evidence_kind`) and four are added (`principal_id`,
`authentication_mechanism_id`, `credential_id`, `authentication_proof_ref`);
three carry forward unchanged in meaning (`approval_mechanism`,
`approval_preview_digest`, `producer_component`).

| v1.0 field | v2.0 disposition |
|---|---|
| `approver_id` | **Retired.** Replaced by `principal_id` — a registry-bound identifier, meaningless without a successful `HumanPrincipalRegistry` lookup (HPAC-001 §5), not a free string. |
| `identity_evidence_kind` | **Retired.** Its two-member claim-only enum (`typed_confirmation_only`, `os_authenticated_user`) described an evidentiary *claim*; replaced by `authentication_mechanism_id`, which names a specific, assurance-rated, verifiable mechanism (HPAC-001 §10/§14). |
| `approval_mechanism` | **Changed in v3.0** to const `trusted_subject_bound_confirmation`; ordinary agent-controlled terminal confirmation is insufficient. |
| `approval_preview_digest` | Unchanged — still the exact rendered approval-preview digest. |
| `producer_component` | Unchanged — still the const `pcae.trusted_runtime_approval_coordinator`. |
| `principal_id` | **New.** Non-empty string, resolved against `HumanPrincipalRegistry`; HPAC-001 §7's grammar and immutability rules apply. |
| `authentication_mechanism_id` | Non-empty string naming one HPAC-001 v2.1 §10 mechanism descriptor (the primary v2 hardware-FIDO2 mechanism is in §14). |
| `credential_id` | **New.** Non-empty string; the exact enrolled credential (HPAC-001 §9) used to produce the proof, distinct from `principal_id` (a principal MAY own more than one credential, HPAC-001 §9). |
| `authentication_proof_ref` | Exact closed pair (`proof_id`, `proof_digest`) pointing to HPAC-PROOF/2.0 protected canonical storage. It is not the generic `artifact_ref` and never contains a path. |

V3 is a MAJOR because the required `contract_version`, approval-mechanism
meaning, and proof-reference type are incompatible with v2.0 artifacts.
There is no free-form authority claim anywhere in `provenance`. A
cryptographic signature or assertion is now required for every trusted
approval (RIHAC-001 v2.0 §12 condition 7): the v1.0 sentence "v1 does not
require a cryptographic signature" is retired by this amendment.

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

**Errata note (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — V-3;
non-normative, no version change).** The completed-record `record_digest`
(this contract, §2 item 6 / §8) and the `HPAC-APPROVAL-SUBJECT/2.0` digest
(HPAC-001 v2.1 §38 `HPAC-REQ-089`) are **distinct commitments** and are not
interchangeable. The `HPAC-APPROVAL-SUBJECT/2.0` digest is the *subject*
commitment fixed into the v2 challenge at RDGO-001 gate 3 and bound by HPAC
lifecycle sequence 3 `PROOF_VERIFIED_AND_BOUND`. The completed-record
`record_digest` is a separate commitment over the finished
`RuntimeInvocationApproval` and is carried in the RIHAC-001 v2.0
validated-authority projection and consumed at RDGO-001 gate 9 (RDGO-001
v3.1 §10 item 5). HPAC lifecycle sequence 3 does **not** bind
`record_digest`; RDGO-001 v3.1 §4 is corrected accordingly (it previously
read "over the completed approval digest").

## 10. Normative Draft 2020-12 shape

The following JSON Schema is normative contract text. It is not registered or
production-consumed by this phase.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://pcae.local/contracts/runtime-invocation-approval/3.0/schema.json",
  "title": "PCAE RuntimeInvocationApproval",
  "description": "RIASC-001 v3.0 one-shot authority artifact. Shape validity does not establish authority; protected HPAC v2 proof and trusted presentation validation are mandatory.",
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
    },
    "authentication_proof_ref": {
      "type": "object",
      "additionalProperties": false,
      "required": ["proof_id", "proof_digest"],
      "properties": {
        "proof_id": {
          "type": "string",
          "pattern": "^hap-[0-9a-f]{32}$"
        },
        "proof_digest": { "$ref": "#/$defs/sha256" }
      }
    }
  },
  "properties": {
    "schema_id": { "const": "RIASC-001" },
    "schema_version": { "const": "3.0" },
    "contract_version": { "const": "RIHAC-001/2.0" },
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
        "principal_id",
        "authentication_mechanism_id",
        "credential_id",
        "authentication_proof_ref",
        "approval_mechanism",
        "approval_preview_digest",
        "producer_component"
      ],
      "properties": {
        "principal_id": { "$ref": "#/$defs/nonempty_id" },
        "authentication_mechanism_id": { "$ref": "#/$defs/nonempty_id" },
        "credential_id": { "$ref": "#/$defs/nonempty_id" },
        "authentication_proof_ref": { "$ref": "#/$defs/authentication_proof_ref" },
        "approval_mechanism": {
          "const": "trusted_subject_bound_confirmation"
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
- approval-preview digest correspondence to the protected human-visible
  presentation and canonical challenge subject;
- producer identity distinct from approving human identity; and
- HPAC-001 v2.1 principal/credential/proof verification
  (RIHAC-001 v2.0 §16 step 4): `principal_id` resolves to an `active`
  `HumanPrincipalRegistry` record; `credential_id` resolves to that
  principal's `active`, non-revoked credential; `authentication_mechanism_id`
  meets the minimum required assurance level; the referenced
  `HumanAuthenticationProof` binds to this exact `approval_preview_digest`;
  the proof's signature/assertion verifies against the credential's public
  material; required UP and UV are present; protected presentation evidence
  resolves and matches; and proof lifecycle is fresh or bound only to this
  approval, never consumed, revoked, or replayed.

Failure of any check yields no validated-authority projection and no real
dispatch.

## 12. Storage and reference contract

Canonical storage is:

```text
.pcae/runtime-invocation-approvals/v2/<approval_id>/approval.json
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

**RIASC-001 v3.0 schema contract: FROZEN; v1/v2 have no authority migration.
Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 added a non-normative §9 errata note
(V-3: `record_digest` vs `HPAC-APPROVAL-SUBJECT/2.0` digest are distinct) and
refreshed two HPAC cross-references to v2.1; no version change, no schema
change.**
**Executable production schema: NOT IMPLEMENTED / NOT AUTHORIZED.**  
**Real execution: UNAVAILABLE.**
