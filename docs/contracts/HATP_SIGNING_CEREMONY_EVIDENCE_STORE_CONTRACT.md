# HATP Signing Ceremony + Evidence Store Contract

## Contract identity and status

**Contract:** HSCE-001
**Version:** 1.3
**Status:** FROZEN — v1.3 REPAIR PENDING INDEPENDENT VERIFICATION
**Frozen by:** Phase 149O.9 — HATP Signing Ceremony + Evidence Store Contract
Freeze
**Revised by:** Phase 149O.10.1 — HSCE-001 Narrow Contract Repair (§44
below; repairs Finding 149O.10-F-3, the sole Blocking finding from Phase
149O.10's Independent Verification, by replacing HSCE-REQ-052's
check-then-`os.replace` publication algorithm with an atomic hard-link
exclusive-publish primitive; also folds in non-blocking Finding F-1
(requirement-count correction) and F-2 (wording clarification), and
non-blocking Obs-2 (attack-matrix addition); no semantic narrowing of any
other existing provision, and no other section reopened)
**Further revised by:** Phase 149O.20L.7O.2F.2 — FIDO2 Signing-Time
Credential Resolution Repair (§46 below; repairs BF-1/BF-2, the two
Blocking findings from Phase 149O.20L.7O.2F.1's Independent Verification,
by replacing §11's provider-credential-exchange signer resolution with
durable-registry (`DeploymentBinding`) signer resolution — Model B; no
other section reopened)
**Further revised by:** Phase 149O.20L.7O.2F.4 — Durable-Registry Signer
Cross-Record Consistency and TOCTOU Repair (§48 below; repairs
B-149O.20L.7O.2F.3-1/2 and minimally clarifies HSCE-REQ-080/083 without
changing Model B)
**Depends on:** HATP-001 v1.0 (`HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`,
unamended), RAE-001 v1.0 (`ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`,
unamended)
**Architecture basis:** `docs/PHASE_149O_8_HATP_AG3_AG5_PRODUCTION_CONSUMPTION_SIGNING_CEREMONY_ARCHITECTURE.md`
(149O.8, §5-§27), `docs/PHASE_149O_9_HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT_FREEZE.md`
(this phase's report). Where this contract's own text diverges from
149O.8's architecture prose, this contract is normative for the
signing-ceremony/evidence-store surface specifically; no divergence is
introduced by this freeze — this contract formalizes 149O.8's
selections, it does not reopen them.

HSCE-001 v1.3 is the normative contract answering: what is the exact
`pcae hatp sign rollback` CLI surface, what is the exact
`HATPSignedEvidenceEnvelope` file format, and what are the exact
storage/lookup/failure semantics of `.pcae/hatp-evidence/`? It is
additive to HATP-001 and RAE-001 — it amends neither, and neither
requires amendment to be consumed by this contract (§4). This is
contract text only. It defines a CLI argument surface, a file format,
and a closed error vocabulary as normative prose; it does not
implement the CLI, does not perform hardware signing, does not create
evidence, and does not wire AG3/AG5 dispatch preconditions to this
contract's outputs. It grants no runtime, lifecycle, or execution
capability, and it does not activate HATP production.

## 0. Normative Language

The key words "SHALL", "SHALL NOT", "MUST", "MUST NOT", "REQUIRED",
"SHOULD", "SHOULD NOT", "MAY", and "OPTIONAL" in this document are to
be interpreted per RFC 2119. Every normative sentence carries a unique
requirement ID, `HSCE-REQ-###`, sequential from 001, no gaps, no
duplicates (§26).

## 1. Purpose

**HSCE-REQ-001.** This contract exists to close the two gaps 149O.8
identified and explicitly deferred to this phase (149O.8 §33): the
absence of a frozen CLI surface for HATP evidence acquisition, and the
open question of which production CLI entry point(s), if any, reach
AG5's `build_rollback_execution`. It freezes the exact command syntax,
evidence-envelope format, evidence-store layout, and closed
error/exit-code vocabulary a future implementation phase (149O.10)
must build to, with no ambiguity left for that phase to resolve.

**HSCE-REQ-002.** This contract does not decide, and explicitly defers
to a future contract (149O.12, per 149O.8 §27), how or when AG3/AG5
dispatch preconditions come to depend on the evidence this contract's
surface produces. `pcae hatp sign rollback` writes an evidence
envelope; nothing more.

## 2. Scope

**HSCE-REQ-003.** HSCE-001 SHALL govern: the `pcae hatp sign rollback`
CLI command's exact flags, argument validation, and exit-code/error
vocabulary; the `HATPSignedEvidenceEnvelope` file format and its
closed-schema validation rules; the `.pcae/hatp-evidence/` storage
layout, write semantics (atomicity, no-clobber), and lookup semantics;
and the canonical source of every field the signing command writes
into a `HumanApprovalProvenanceProof`.

**HSCE-REQ-004.** HSCE-001 SHALL NOT govern: HATP proof verification
semantics (owned exclusively by HATP-001 §21-§26, unamended); RAE
Binding/Decision lifecycle semantics (owned exclusively by RAE-001,
unamended); Permission Broker decisions or execution enforcement
(COMP-002, a separate track, 149O.8 §19); AG3/AG5 dispatch-precondition
wiring to `--hatp-evidence` (deferred to 149O.12, per HSCE-REQ-002);
or real Class-B host/hardware provisioning (an operational
certification concern, 149O.8 §29, unaffected by this contract).

## 3. Definitions

**HSCE-REQ-005.** The following terms are frozen for this contract:

- **Operation locator** — the single, non-security-sensitive CLI
  argument identifying which AG3/AG5 operation to sign for (`--job-id`
  for AG3, `--per-id` for AG5). Never a security-sensitive field (§6).
- **`HATPSignedEvidenceEnvelope`** — this contract's evidence-storage
  artifact (§14), distinct from and never a modification of HATP-001's
  `HumanApprovalProvenanceProof` (§4).
- **Evidence store** — the repository-local, agent-writable,
  non-authoritative artifact directory `.pcae/hatp-evidence/` (§16).
- **Signing ceremony** — one interactive, foreground, human-initiated
  invocation of `pcae hatp sign rollback` from proof-preview through
  hardware touch through evidence persistence (149O.8 §6-§7).

## 4. Relationship to HATP-001 and RAE-001

**HSCE-REQ-006.** HATP-001 remains authoritative, unchanged, for:
`HumanApprovalProvenanceProof`'s shape (HATP-001 §19-§20), the
canonical payload and its digest (`canonicalize_hatp_proof_payload`,
`digest_hatp_proof_payload`), the closed verification-status vocabulary
and `verify_hatp_proof` (HATP-001 §22), provider requirements
(HATP-001 §10), human presence (HATP-001 §9), repository/deployment
binding (HATP-001 §17-§18), freshness (HATP-001 §23), and RAE
integration (HATP-001 §29). No byte of HATP-001 v1.0 is amended by this
contract.

**HSCE-REQ-007.** RAE-001 remains authoritative, unchanged, for:
`RollbackApprovalBinding`'s shape and lifecycle, the RAE evidence store
(`.pcae/rollback-approval-evidence/`), and the 24-hour freshness window
(RAE-REQ-043). This contract's evidence store is a distinct,
separately-rooted directory from RAE's own (§16); the two are never
merged or cross-addressed.

**HSCE-REQ-008.** This contract governs exclusively: human-facing
signing initiation, proof-field derivation at signing time, hardware
provider invocation, signed-evidence packaging, evidence storage, and
evidence lookup. No conflicting semantics with HATP-001 or RAE-001 are
introduced; where this contract references a proof field, a Decision,
or a Binding, it reads that value from the canonical source HATP-001/
RAE-001 already define, never redefining it.

## 5. Signing Command — Exact CLI Surface

**HSCE-REQ-009.** The signing command family is frozen as exactly:

```
pcae hatp sign rollback --site {ag3|ag5} [locator flags] [--json]
```

No alternative verb, no `pcae hatp sign` without a `rollback`
subcommand, and no per-site top-level subcommand (e.g. no
`pcae hatp sign rollback-ag3`) — `--site` is a required flag, not a
positional submode, matching 149O.8 §5's selection and this contract's
own §6 additional locator-flag decision below.

**HSCE-REQ-010.** `--site` SHALL accept exactly the closed values
`ag3` and `ag5` (case-sensitive, lowercase). Any other value SHALL be
rejected as a CLI argument-parsing error before any HATP/RAE state is
touched (argparse `choices=["ag3", "ag5"]` or repository-conventional
equivalent).

**HSCE-REQ-011.** `--json` SHALL print machine-readable JSON output on
success and on error, mirroring the existing `pcae remote rollback
approve/deny/execute --json` and `pcae rollback --json` convention
(`src/pcae/commands/agent.py`). Human-readable text output is the
default when `--json` is omitted.

**HSCE-REQ-012.** No `--dry-run` flag exists on `pcae hatp sign
rollback`. Rationale: the mandatory preview-before-touch step (§9,
"blind-touch defense") already produces the human-visible preview a
dry-run mode would otherwise exist to provide, and the command already
never gates hardware-touch invocation on substrate operational
readiness (§21 — 149O.8 §21's own decision, carried forward
unmodified); a separate dry-run mode would add CLI surface without a
distinct behavior to gate.

## 6. AG3 Operation Locator

**HSCE-REQ-013.** For `--site ag3`, the signing command SHALL accept
exactly one required flag: `--job-id <id>`. No other AG3-specific flag
exists. `original_commit_sha` SHALL be read from the live job record
(the same record `execute_rollback` already reads for its own
preconditions, `src/pcae/core/agent.py`), never accepted as a CLI
argument.

## 7. AG5 CLI Entry-Point Inventory (closes 149O.8's open question)

**HSCE-REQ-014.** The following is the exact, exhaustive inventory of
every production source location that calls `build_rollback_execution`,
established by direct grep of `src/pcae/` (excluding `tests/`) at this
phase's start:

| Call site | Kind | HATP params supplied? |
|---|---|---|
| `src/pcae/commands/agent.py:16259`, `run_rollback(args)` | **Real production CLI handler**, registered as the top-level `pcae rollback --per-id <id> [--dry-run] [--json]` command (`src/pcae/cli.py:3035-3055`, `subparsers.add_parser("rollback", ...)`) | No — calls `build_rollback_execution(HarnessPath.cwd(), args.per_id, dry_run=args.dry_run)` with no `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` |
| `src/pcae/core/agent.py:93952`, `def build_rollback_execution(...)` | Function definition itself (not a call site) | N/A |
| `src/pcae/core/agent.py:27055`, `build_rollback_execution_pilot()` | A distinct, differently-named function (Phase-69O-era design-preview pilot); does **not** call `build_rollback_execution` | N/A — false-positive name collision, confirmed by reading both definitions |
| `src/pcae/commands/agent.py:6853`, `run_...` (pilot handler) | Calls `build_rollback_execution_pilot()`, not `build_rollback_execution` | N/A |
| `tests/test_agent.py`, `tests/test_phase_149d_rwmpc_contract_independent_verification.py`, `tests/test_phase_149j_rollback_approval_evidence_contract_independent_verification.py`, `tests/test_phase_149o_6_hatp_wave7_class_b_deployment_activation.py` | Test-only call sites | Varies per test; not production dispatch |

**HSCE-REQ-015.** **Corrected finding, superseding 149O.8 §17's open
question:** a real production CLI entry point exists and reaches
`build_rollback_execution` today: `pcae rollback --per-id <id>
[--dry-run] [--json]` (`run_rollback`, `src/pcae/commands/agent.py:16258`,
registered `src/pcae/cli.py:3035`). It is a distinct top-level command
from `pcae remote rollback approve/deny/execute` (which govern AG3's
`rollback_approval_state`, `src/pcae/cli.py:4106-4188`) and from
`pcae rollback-execution show/list/mark-interrupted` (which inspect,
never dispatch, `RollbackExecutionRecord`s, `src/pcae/cli.py:3057-3104`).
`run_rollback` calls `build_rollback_execution` with no HATP arguments,
confirming 149O.8's gap analysis (production consumption gap) was
correct in substance — the gated adapter is unreached by real
dispatch — even though 149O.8's own text understated the finding as
"which CLI command(s), if any" (149O.8 §17, §95, §97) rather than
naming `pcae rollback` explicitly. No fake CLI is invented by this
requirement; `pcae rollback` already exists in production today.

**HSCE-REQ-016.** For `--site ag5`, the signing command SHALL accept
exactly one required flag: `--per-id <id>`. No `--ecp-id` flag exists.
`ecp_id` SHALL be read directly from the live `PromotionExecutionRecord`
identified by `--per-id` (the same record's `ecp_id` field
`run_promotion_execution_list`/`build_rollback_execution` already read,
`src/pcae/core/agent.py`) — every `PromotionExecutionRecord` carries
exactly one `ecp_id`, so no disambiguation input is needed from the
human. This resolves 149O.8 §17's "TBD at contract-freeze time"
placeholder in favor of full auto-derivation, consistent with §8's "no
user-typed security fields" principle.

## 8. No User-Typed Security Fields

**HSCE-REQ-017.** The only CLI-supplied identifiers anywhere on `pcae
hatp sign rollback` are the two closed-form operation locators
(`--job-id`, `--per-id`) and the required `--site` selector. No flag
for `principal_id`, `signer_key_id`, `provider_profile`,
`repository_id`, `decision_record_id`, `decision_record_digest`,
`binding_id`, `binding_digest`, `ecp_id`, `original_commit_sha`,
`issued_at`, or `--provider`/`--signer`/`--force`/`--overwrite`/
`--output` exists on this command, ever (§18, §22 below elaborate the
prohibited flags explicitly).

## 9. Proof Field-Source Table

**HSCE-REQ-018.** Every `HumanApprovalProvenanceProof` field the
signing command constructs SHALL be derived exclusively from the
canonical source in this table. A future implementation (149O.10)
SHALL NOT accept caller input for any row marked "No":

| Field | Canonical producer | May user supply? | Failure if unavailable |
|---|---|---|---|
| `proof_version` | Fixed constant `1` | No | N/A — always set |
| `repository_id` | The local repository's own identity record (`pcae.core.repository_identity.read_repository_identity`, the same source `resolve_ag3/ag5_gated_rollback_authority` already use) | No | `repository_identity_unavailable` (§22) |
| `decision_record_id`, `decision_record_digest` | The CHGR Decision record referenced by the RAE `RollbackApprovalBinding` matching this operation, looked up live (§10) | No | `decision_unavailable` (§22) |
| `binding_id`, `binding_digest` | The RAE `RollbackApprovalBinding` for this exact operation (`rollback_approval_evidence.py`), read live at signing time (§10) | No | `binding_unavailable` (§22) |
| `principal_id`, `signer_key_id` | **[Revised, v1.2, §46 — BF-1 repair.]** Resolved exclusively from this repository's own durable `DeploymentBinding` (`HATPTrustStore.resolve_deployment_authorization`, `hatp_bootstrap.py`, the frozen Layer-1 `repository_id` + Layer-2 `canonical_deployment_root` match, HATP-REQ-057-063), cross-checked against `HATPTrustStore.production()`'s `SignerRecord`/`PrincipalRecord` (both `active`) and the protected `HardwareCredentialRecord` registry (`active`, matching `provider_profile`) — never from the hardware provider's own credential exchange (§80) | No | `no_authorized_signer` (§22) |
| `provider_profile` | Fixed to whatever `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` resolves (`hatp_providers.py`) | No | `provider_unavailable` (§22) |
| `rollback_site` | Derived from `--site` | Indirectly (via `--site`, a non-security-sensitive routing choice, not itself a signed-authority claim) | N/A — CLI validation error if `--site` is malformed |
| `operation_reference` (`job_id`+`original_commit_sha` for AG3; `per_id`+`ecp_id` for AG5) | `job_id`/`per_id`: the operation locator (§6, §7). `original_commit_sha`/`ecp_id`: read live from the job/PER record | Locator only (`job_id`/`per_id`); never the derived half | `operation_not_found` (§22) |
| `issued_at` | Wall-clock read internally at proof-construction time, never `datetime.now()` called anywhere but this one site (mirrors `verify_hatp_proof`'s existing no-hidden-clock discipline) | No | N/A — always set at signing time |

**HSCE-REQ-019.** Human presence itself (the fact bound into the
provider assertion, not a proof field) is never a caller-suppliable
boolean, per HATP-REQ-016/HATP-REQ-018 and 149O.8 §6 — the signing
command has no code path that could set it.

## 10. Decision/Binding Lookup

**HSCE-REQ-020.** The signing command SHALL locate the
`RollbackApprovalBinding` matching the given operation locator by
scanning the RAE evidence store's existing bindings
(`RollbackApprovalEvidenceStore.list_bindings_with_keys()`,
`rollback_approval_evidence.py`) and selecting the Binding whose
`rollback_operation_reference` structurally matches the given
`rollback_site` and operation locator (`job_id`/`original_commit_sha`
for AG3, `per_id`/`ecp_id` for AG5), applying the same
at-most-one-active-Binding supersession discipline that function's own
docstring already documents (never an implicit "pick the newest" rule
across genuinely distinct operations — only supersession-aware
selection *within* one already-identified operation).

**HSCE-REQ-021.** If no matching, non-superseded Binding exists for the
given operation locator, signing SHALL fail with `binding_unavailable`
(§22) before any hardware provider is invoked. A missing Binding is a
precondition failure, not a reason to sign an underspecified proof.

## 11. Signer / Provider Resolution

**HSCE-REQ-022.** The signing command SHALL call
`create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)`
(`hatp_providers.py`) as its only provider-resolution path. No
`--provider` flag, environment variable, or configuration override
selects a different provider. `TestHATPProofVerifierProvider` SHALL
NOT be reachable from this command under any flag, environment
variable, or build configuration (mirrors 149O.8 §10, HATP-REQ-022).

**HSCE-REQ-023.** The signing command SHALL call
`HATPTrustStore.production()` (`hatp_bootstrap.py`) as its only
trust-store-resolution path. No `--hatp-trust-store`/`--trusted-key`
flag exists (mirrors HATP-REQ-035).

**HSCE-REQ-024.** **[Revised, v1.2, §46 — BF-1 repair.]** No `--signer`
flag exists. If this repository's `DeploymentBinding`-resolved
`signer_key_id` (§80) has no matching `active` `SignerRecord`/
`PrincipalRecord`/`HardwareCredentialRecord`, or a `provider_profile`
mismatch is found at any of those three checks, signing SHALL fail with
`no_authorized_signer` (§22) — the signing command never lets the human
select an unauthorized signer identity by flag, and never lets the
hardware provider select governance identity either (§80/§82).

## 12. Substrate Readiness Is Not a Signing Precondition

**HSCE-REQ-025.** Reaffirming 149O.8 §21 verbatim (not reopened by this
contract): `pcae hatp sign rollback` MAY attempt to produce a
cryptographic proof even when
`inspect_hatp_verification_substrate_readiness(...).operational ==
False` for this deployment. The command does not call that function as
a precondition gate. Production approval remains unavailable
(`approval_present` stays `False`) regardless, because that fact is
independently re-derived at consumption time (HATP-001 §22, §29). This
is distinct from hardware-provider *availability* (§13 below), which
IS a hard precondition — the substrate-readiness conjunction (trust-
store ownership, OS-principal separation, etc.) is not.

**HSCE-REQ-026.** No `--force`/`--ignore-not-ready`/`--dev`/
`--software-provider` flag exists, and none may be added by a future
implementation without a governed contract amendment (mirrors
HATP-REQ-numbered override prohibitions and 149O.8 §22's "no
production escape hatch" constraint).

## 13. Human Presence, Hardware Absence, Cancellation

**HSCE-REQ-027.** `pcae hatp sign rollback` SHALL invoke the resolved
production hardware provider's `request_signature(...)` (Wave 5,
`hatp_providers.py`) to obtain a fresh, hardware-enforced human-presence
signing operation over exactly the canonical payload bytes
(`canonicalize_hatp_proof_payload(proof)`, §15) — never a
pre-digested value, never a caller-supplied presence boolean.

**HSCE-REQ-028.** If no hardware provider is available (`discover_
hardware_providers()` reports no usable provider, or
`create_production_hardware_provider` raises
`HATPProviderUnavailableError`), signing SHALL fail with
`provider_unavailable` (§22), reported clearly, with no software
fallback of any kind (mirrors HATP-REQ-021, 149O.8 §23).

**HSCE-REQ-029.** If the human cancels the touch/PIN operation, or it
times out (`HATPProviderCancelledError`), signing SHALL fail with
`human_signing_cancelled` (§22). No evidence is persisted. No
approval/authority state is mutated anywhere.

**HSCE-REQ-030.** A genuine hardware/transport fault
(`HATPProviderDeviceError`) SHALL fail with `hardware_device_fault`
(§22). Distinct from `human_signing_cancelled` — the two are never
collapsed into one generic failure.

## 14. `HATPSignedEvidenceEnvelope` — Definition

**HSCE-REQ-031.** The signing command's output artifact type is frozen
as `HATPSignedEvidenceEnvelope`, distinct from and never a
modification of `HumanApprovalProvenanceProof` (HATP-REQ-067 remains
exclusively HATP-001's). The provider signature/assertion binds the
Wave-3 canonical proof payload (`canonicalize_hatp_proof_payload`); the
envelope itself is transport/storage packaging, not a new
cryptographically-signed object — the envelope's own bytes are never
themselves signed or claimed to be content-addressed as a whole (§18).

**HSCE-REQ-032.** The envelope's closed field set is exactly:

```
HATPSignedEvidenceEnvelope = {
    evidence_version: 1,                # int, see §15
    evidence_id: <sha256-hex>,           # see §17-18
    proof: <HumanApprovalProvenanceProof canonical document>,
                                          # hatp_proof_to_document(proof) --
                                          # HATP-001 schema, byte-for-byte
                                          # unchanged
    provider_assertion: <base64 string>, # see §16
}
```

No other top-level field exists. This directly reuses HATP-001's
existing proof shape and Wave-5's existing `ProviderAssertion.evidence`
bytes (149O.8 §11 — "no new schema... no contract need").

## 15. Envelope Version

**HSCE-REQ-033.** `evidence_version` SHALL be the integer `1`.
Construction SHALL explicitly reject `bool` (Python's `isinstance(True,
int) == True` pitfall) using the identical pattern
`human_approval_trusted_provenance.py::_require_proof_version` already
uses for `proof_version` — `isinstance(value, bool)` checked
independently before the `isinstance(value, int)` check is trusted.
Parsing an envelope with any `evidence_version` other than `1` SHALL be
rejected as `unsupported_envelope_version`, closed, no silent
best-effort acceptance (mirrors HATP-REQ-117/§28's amendment
discipline).

## 16. Provider Evidence Representation

**HSCE-REQ-034.** `provider_assertion` SHALL be the standard
Base64 (RFC 4648 §4, `base64.b64encode`/`base64.b64decode`, matching
this repository's existing bytes-in-JSON convention,
`src/pcae/core/agent.py`) encoding of exactly
`ProviderAssertion.evidence` (`hatp_providers.py`) — the raw opaque
bytes the hardware provider itself produced, unparsed and
unreinterpreted by the envelope layer. The envelope does not decode,
re-encode, or otherwise reinterpret this provider-specific
serialization; it stores it opaquely (mirrors 149O.8's `provider_
assertion: bytes` design, §11, and HATP-001's own "opaque to Wave-4"
framing of `ProviderAssertion`).

**HSCE-REQ-035.** At load time, the envelope's `provider_assertion`
SHALL be decoded from Base64 and wrapped as `HATPVerificationEvidence
(assertion=<decoded bytes>)` (`human_approval_trusted_provenance.py`)
for consumption by `verify_hatp_proof`/`resolve_ag3/ag5_gated_rollback_
authority` — no other transformation occurs between storage and
verification-time use.

## 17. Evidence ID — Exact Formula

**HSCE-REQ-036.** `evidence_id = digest_hatp_proof_payload(proof)` —
the proof's own canonical SHA-256 hex content digest
(`human_approval_trusted_provenance.py`), lowercase, 64 hex characters,
no algorithm prefix (matching this project's existing plain-hex digest
convention). Never a freshly minted UUID, never caller-selected.

## 18. Content-Addressing Precision (mandatory disambiguation)

**HSCE-REQ-037.** **Mandatory statement, closing 149O.8's own open
question (149O.8 §12's `evidence_id` bullet, governing-prompt §27-§28):**
`evidence_id` addresses **the canonical proof payload
(`canonicalize_hatp_proof_payload(proof)`) only** — it does NOT address
the complete envelope byte sequence, and it does NOT address
`provider_assertion` at all. The envelope is not "content-addressed" as
a whole; only the embedded `proof` is.

**HSCE-REQ-038.** **Same-`evidence_id`-different-`provider_assertion`
case, mandatory resolution:** because `evidence_id` depends solely on
the proof digest, two distinct, independently-valid provider
assertions (e.g. from two separate hardware-touch attempts that happen
to sign an identical proof payload — same `job_id`, same
`decision_record_digest`/`binding_digest`, same `issued_at` millisecond)
could in principle exist for the same `evidence_id`. This contract
resolves the case exactly as follows (§19): the **first** envelope
durably persisted under a given `evidence_id` is canonical; any
subsequent write attempt under the same `evidence_id` is compared
byte-for-byte against the persisted envelope (§19's no-clobber rule) —
byte-identical is idempotent success, byte-different (including a
differing `provider_assertion` alone) is a hard `evidence_conflict`
rejection, never a silent overwrite and never an implicit "latest
wins."

## 19. Immutability / No-Clobber / Idempotent Write

**HSCE-REQ-039.** **CREATE-ONCE / NO-CLOBBER is frozen as the exact
write rule.** If `.pcae/hatp-evidence/envelopes/{evidence_id}.json`
already exists at write time:

- **(A)** the new envelope is byte-for-byte identical to the persisted
  file (after canonical JSON serialization, §24) — the write SHALL be
  treated as an idempotent success, no error, no duplicate write.
- **(B)** the new envelope differs in any byte — the write SHALL be
  rejected as `evidence_conflict` (§22). The existing file SHALL NOT be
  overwritten, ever, under any flag (§26 — no `--force`/`--overwrite`
  exists to bypass this).

**HSCE-REQ-040.** The envelope is immutable by construction: because
`evidence_id` is a pure function of `proof` alone (§17), any mutation
of `proof` after signing produces a *different* `evidence_id`, hence a
*different* file — never an in-place edit of an existing evidence
record (mirrors RAE-001's own `_write_atomic_json`/creation-registry
no-overwrite discipline, `rollback_approval_evidence.py`).

## 20. Evidence Store Root and Layout

**HSCE-REQ-041.** The evidence store root is frozen as exactly
`.pcae/hatp-evidence/`, resolved relative to the repository root
(the same root-resolution convention `RollbackApprovalEvidenceStore`
and every other `.pcae/`-rooted PCAE store already use, e.g.
`HarnessPath.cwd()` / an explicit repository-root parameter) — never
resolved relative to an arbitrary current working directory captured
ambiguously.

**HSCE-REQ-042.** The exact file layout is frozen as:

```
.pcae/hatp-evidence/
  envelopes/{evidence_id}.json
```

One canonical file per evidence ID. No `creation-registry/` marker
subdirectory is required for this store (unlike RAE's own two-file
creation-registration pattern) — the no-clobber write itself (§19),
performed via the atomic-create-or-compare procedure in §24, is
sufficient because there is no second, independently-writable
`bindings/`-style directory this store needs to cross-validate against
(distinguishing this contract's simpler single-artifact-per-ID shape
from RAE-001's Binding/registration split, which exists specifically to
detect a Binding written outside `create_rollback_approval_binding`'s
own call path — no equivalent bypass path exists for this store,
because the envelope's own identity IS the content it stores).

**HSCE-REQ-043.** No other file or directory under
`.pcae/hatp-evidence/` is defined by this contract. A future
implementation SHALL NOT add sibling files (e.g. an index, a `latest`
symlink, a manifest) without a governed contract amendment, because any
such artifact risks becoming an informal second lookup path this
contract's explicit-ID-only rule (§21) forbids.

## 21. Evidence Lookup Semantics

**HSCE-REQ-044.** Evidence lookup SHALL be **explicit `evidence_id`
only** — `envelopes/{evidence_id}.json`, exact match, O(1). No
"latest", "newest", "first match", glob, or single-file-fallback lookup
mode exists anywhere in this contract's surface, matching HATP-001's
own operation-binding discipline and 149O.8 §12's explicit rejection of
implicit "latest approval" selection.

**HSCE-REQ-045.** A future consuming command accepting
`--hatp-evidence <id>` (149O.12, out of this contract's scope to
implement) SHALL treat the supplied ID as a locator only, never as
authority — full HATP verification (HATP-001 §22) is mandatory at
consumption regardless of how the ID was obtained (mirrors HATP-REQ-102/
104's "VALID does not itself decide").

## 22. Closed Error Vocabulary and Exit-Code Mapping

**HSCE-REQ-046.** Exit codes are frozen as a small, closed set of
integer categories, mirroring this repository's existing
`decision_session.py` IWPC-001-style exit-code-category convention
(`src/pcae/commands/decision_session.py::_EXIT_CODE_BY_ERROR_TYPE`)
rather than inventing one numeric code per error concept:

```
EXIT_SUCCESS                    = 0
EXIT_GENERIC_SIGNING_FAILURE    = 1
EXIT_OPERATION_NOT_FOUND        = 2
EXIT_GOVERNANCE_STATE_UNAVAILABLE = 3
EXIT_SUBSTRATE_UNAVAILABLE      = 4
EXIT_HUMAN_CANCELLED            = 5
EXIT_PROVIDER_FAILURE           = 6
EXIT_EVIDENCE_CONFLICT          = 7
EXIT_PERSISTENCE_FAILURE        = 8
```

**HSCE-REQ-047.** The closed error-vocabulary-to-exit-code mapping is
frozen as:

| `error_type` | Exit code | Meaning |
|---|---|---|
| `repository_identity_unavailable` | 3 (`EXIT_GOVERNANCE_STATE_UNAVAILABLE`) | No repository identity provisioned (§9) |
| `operation_not_found` | 2 (`EXIT_OPERATION_NOT_FOUND`) | Job/PER record for the given locator does not exist |
| `decision_unavailable` | 3 | No CHGR Decision resolvable for the matched Binding (§9-10) |
| `binding_unavailable` | 3 | No matching, non-superseded RAE Binding for this operation (§10) |
| `no_authorized_signer` | 4 (`EXIT_SUBSTRATE_UNAVAILABLE`) | **[Revised, v1.2, §46.]** No usable `DeploymentBinding`-resolved signer for this repository, or its `SignerRecord`/`PrincipalRecord`/`HardwareCredentialRecord`/`provider_profile` cross-checks fail (§11) |
| `provider_unavailable` | 4 | No hardware provider discoverable/resolvable (§13) |
| `hardware_device_fault` | 6 (`EXIT_PROVIDER_FAILURE`) | Genuine hardware/transport fault during signing (§13) |
| `human_signing_cancelled` | 5 (`EXIT_HUMAN_CANCELLED`) | Human cancelled touch/PIN, or timeout (§13) |
| `provider_signature_failure` | 6 | Provider-reported signature/assertion failure not covered by cancellation/device-fault |
| `evidence_serialization_failure` | 1 (`EXIT_GENERIC_SIGNING_FAILURE`) | Envelope construction/serialization failed structurally |
| `evidence_conflict` | 7 (`EXIT_EVIDENCE_CONFLICT`) | Same `evidence_id`, different envelope bytes already persisted (§18-19) |
| `evidence_persistence_failure` | 8 (`EXIT_PERSISTENCE_FAILURE`) | Atomic write/rename failed at the filesystem layer (§24) |

**HSCE-REQ-048.** This vocabulary is closed. A future implementation
SHALL NOT introduce an `error_type` outside this table without a
governed contract amendment. Every `error_type` maps to exactly one
exit code (mirrors IWPC-REQ-052's "every taxonomy member maps to
exactly one exit class" discipline, even for members not yet reachable
by an initial implementation).

**HSCE-REQ-049.** Signing errors are never expressed using
`HATPVerificationStatus` vocabulary (HATP-001 §22) — `provider_
unavailable` is not `INVALID_SIGNATURE`; the two vocabularies remain
structurally distinct, mirroring HATP-REQ-078's own separation
discipline (§4 of the governing prompt reflected here).

## 23. Secret Handling and Logging

**HSCE-REQ-050.** No private key, PIN, or other provider secret SHALL
ever appear in: the persisted envelope, a CLI argument, an environment
variable read by this command, stdout/stderr logging, or a phase
report. If the hardware provider requires PIN entry, it SHALL be
collected exclusively through the provider's own out-of-band secure
input path (the OS/authenticator-level mechanism FIDO2/CTAP2 already
uses), never through `pcae`'s own argument parsing or stdin capture.

**HSCE-REQ-051.** Diagnostic logging/audit events MAY reference:
`evidence_id`, the operation locator, `provider_profile`, and the
success/failure `error_type` category. Diagnostic output SHALL NOT
include private key material, raw protected trust-store content, or
provider secret state (mirrors HATP-REQ verifier-side read-only
discipline extended to this command's own output).

## 24. Atomic Write, File Mode, Directory Creation

**HSCE-REQ-052.** **[Repaired, Phase 149O.10.1, §44 — supersedes the
check-then-`os.replace` algorithm this requirement originally specified
in HSCE-001 v1.0.]** Phase 149O.10 independently demonstrated (Finding
149O.10-F-3, BLOCKING) that a preceding `path.exists()` check followed by
an unconditional `os.replace` cannot guarantee SC-7 under concurrent
writers: `os.replace` is unconditional on POSIX and provides no
exclusivity of its own, so two concurrent writers can each observe
"destination absent," each proceed, and the second writer's `os.replace`
silently overwrites the first writer's envelope even when the two differ
byte-for-byte. Envelope persistence SHALL instead use **atomic hard-link
publication** as the exclusive-create primitive that establishes the
canonical winner for a given `evidence_id`, exactly as follows: **(1)**
serialize the candidate envelope to canonical bytes per §53; **(2)**
create a uniquely-named temporary file in the same `envelopes/` directory
(mirroring `rollback_approval_evidence.py::_write_atomic_json`'s
temp-file-in-same-directory discipline — the technique, not a literal
unmodified call to that helper, since it lacks the symlink checks §57-58
separately require); **(3)** write the complete canonical bytes to the
temp file, `flush()`, then `os.fsync(fd)` — the identical durability
level `_write_atomic_json` already provides; no stronger crash-durability
claim is introduced by this repair; **(4)** attempt `os.link(temp_path,
final_path)` — a single atomic filesystem operation that either creates a
new directory entry at `final_path` pointing at the already-fully-written,
already-fsynced temp file's inode, or fails, with no partially-written
file ever visible at `final_path` (preserving §38 attack-matrix item 15's
guarantee under this primitive); **(5)** if `os.link` succeeds, this
writer is the exclusive-publication **winner** — canonical status for
`evidence_id` is established by that single successful call, never by
any earlier check — and the now-redundant temp file is unlinked
(removal, or a failure to remove it, is non-authoritative); **(6)** if
`os.link` raises `FileExistsError`, this writer has **lost** the
exclusive-publication race; before reading anything, the writer SHALL
check whether `final_path` is a symlink (`os.path.islink`) — if it is,
the write SHALL be rejected as `evidence_persistence_failure` per §57
rather than being treated as an ordinary loser (no read-through-symlink
comparison is ever performed); otherwise the writer SHALL read the
already-persisted canonical envelope at `final_path` and compare its
canonical bytes (§53) against its own candidate's canonical bytes:
byte-identical is idempotent success, no error, no duplicate write
(§19(A)); byte-different is `evidence_conflict` (§19(B), §22) — the
persisted winner is never overwritten, under any condition; the losing
writer's own temp file is unlinked in either case; **(7)** if `os.link`
raises any `OSError` other than `FileExistsError` (e.g. a cross-device
temp/destination pair, or a filesystem/platform that does not support
hard links), the write SHALL fail closed as `evidence_persistence_failure`
(§22) — there is no fallback to `os.replace`, or to any other
overwrite-capable primitive, under any condition. On both platforms this
repository supports (macOS/APFS, Linux/ext4 and equivalent journaling
filesystems), `os.link` within a single directory on the evidence
store's own filesystem provides this identical atomic, exclusive-create
guarantee; this repair defines no Windows-specific semantics, matching
this contract's existing platform scope (§20, unamended by this repair).
This exact sequence is the sole normative description of "the
check-then-compare, atomic-create-or-compare procedure" §20 and §24's own
heading refer to; no other passage in this contract's non-normative
prose or examples describes `os.replace` as a winner-publication
mechanism as of v1.1.

**Winner/loser state-machine restatement (non-normative summary of (1)-(7)
above, no independent normative force beyond what they already state):**
for any `evidence_id` not yet persisted, exactly one concurrent writer's
`os.link` call succeeds and that writer's bytes become canonical
(`ABSENT` → `CANONICAL(bytes)`); every other concurrent writer's `os.link`
call fails, and each such writer independently resolves to idempotent
success or `evidence_conflict` by comparing against the now-established
canonical bytes — this generalizes without modification to any number of
concurrent writers (not only two), because each writer's `os.link` attempt
is independently exclusive against the filesystem, not against any other
writer's in-process state. `CANONICAL(bytes)` never transitions to
`CANONICAL(other_bytes)` for `bytes != other_bytes` — no writer, winning
or losing, may replace an established canonical envelope; "delete the
existing file, then create a new one" is explicitly not a compliant
implementation of "exclusive" (this would forfeit the atomic-create
guarantee between the delete and the create, reopening the same race
§19-§26 close). A crash before step (4)'s `os.link` call leaves no
canonical final artifact — the temp file is not authority-bearing, and
retry is unconstrained. A crash after step (4)'s successful `os.link`
leaves the canonical final artifact intact regardless of whether the
subsequent temp-file cleanup (step (5)/(6)) completes; that cleanup
failure is never authoritative.

**HSCE-REQ-053.** The evidence-store JSON encoding SHALL be: UTF-8,
`sort_keys=True`, no `NaN`/`Infinity` (`allow_nan=False`), duplicate
JSON keys rejected on parse (reusing
`human_approval_trusted_provenance.py::_reject_duplicate_keys`'s
`object_pairs_hook` technique) — this is the canonical storage
serialization used for the byte-comparison in §19, distinct from and
never confused with HATP-001's own signed canonical payload
serialization (`canonicalize_hatp_proof_payload`), which remains solely
what the hardware provider signs.

**HSCE-REQ-054.** File mode SHALL be ordinary repository-private
artifact mode, matching this repository's other `.pcae/`-rooted store
conventions. File mode establishes no authority — authority comes
solely from the proof's signature and protected trust-store state (§27).

**HSCE-REQ-055.** The signing command MAY create `.pcae/hatp-evidence/`
and `.pcae/hatp-evidence/envelopes/` if absent (`mkdir(parents=True,
exist_ok=True)`, mirroring RAE-001's own directory-creation
convention). This is ordinary repository-local artifact storage, not a
protected trust-bootstrap operation.

## 25. Path Validation, Traversal, Symlinks

**HSCE-REQ-056.** `evidence_id` SHALL be validated as exactly a
lowercase, 64-character hexadecimal string before any path is
constructed from it (reusing
`human_approval_trusted_provenance.py::_SHA256_HEX_RE`-equivalent
validation). Any value containing `../`, `/`, `\`, whitespace,
uppercase hex characters, a partial-length digest, or any other
non-conforming character SHALL be rejected before filesystem access,
never sanitized-and-retried.

**HSCE-REQ-057.** If the computed destination path
(`envelopes/{evidence_id}.json`) already exists as a symlink, the write
SHALL be rejected (`evidence_persistence_failure`) rather than
following the symlink to write through it — mirrors HATP-REQ's
symlink-rejection discipline for the (higher-trust) bootstrap store,
applied here even though this store is untrusted (§27), specifically to
prevent a corrupted symlink from redirecting a write outside the
repository.

**HSCE-REQ-058.** If any path component of `.pcae/hatp-evidence/` or
`envelopes/` is a symlink escaping the repository root, the operation
SHALL fail closed (`evidence_persistence_failure`) rather than
following it. This store's untrusted classification (§27) changes the
*consequence* of compromise, not the requirement to avoid writing
outside the repository.

## 26. Case Sensitivity

**HSCE-REQ-059.** `evidence_id` SHALL always be lowercase, both as
produced by `digest_hatp_proof_payload` (already lowercase hex,
`hashlib.hexdigest()`'s own convention) and as accepted on any future
consumption-side `--hatp-evidence` input (§21, §45) — no
case-insensitive lookup, no uppercase alias, to avoid cross-platform
filesystem aliasing ambiguity.

## 27. Storage Trust Classification

**HSCE-REQ-060.** `.pcae/hatp-evidence/` is agent-writable, repository-
local, **untrusted** storage — not an authority root. Security comes
exclusively from: the proof's own signature (verified by
`verify_hatp_proof`), protected signer/trust-store state
(`HATPTrustStore.production()`), the repository/deployment binding
check (HATP-001 §18), and consumption-time re-verification (never
cached). Deletion or corruption of any envelope file results in **no
approval** for that `evidence_id` — never an execution-blocking bug to
work around, never a fallback to a weaker authority path.

**HSCE-REQ-061.** **Forbidden pattern, explicitly prohibited by this
contract:** no future code may treat evidence-file existence, or a
valid-looking `evidence_id` string alone, as approval (`if
evidence_file.exists(): approval_present = True` and equivalents are
explicitly non-compliant). Only a full `verify_hatp_proof` call,
against the untouched embedded `proof`, decides trust.

## 28. Envelope Load-Time Validation

**HSCE-REQ-062.** On load, the consuming code SHALL: (a) parse the
envelope's closed schema (§14, unknown fields rejected, missing
required fields rejected, wrong types rejected, unknown
`evidence_version` rejected, duplicate JSON keys rejected — §53); (b)
recompute `digest_hatp_proof_payload(proof)` from the embedded `proof`
and compare it against the envelope's own `evidence_id` field; a
mismatch SHALL be rejected as `evidence_id_digest_mismatch`, treated as
an invalid envelope, never trusted, never repaired in place.

**HSCE-REQ-063.** Envelope parsing (§62) establishes structural
validity only — it does NOT establish provider-assertion validity or
proof trust. Only a subsequent `verify_hatp_proof` call, supplying the
parsed `proof` and the decoded `HATPVerificationEvidence`, establishes
trust (mirrors HATP-001's own parse-vs-verify separation, §21-§22).

**HSCE-REQ-064.** Missing evidence (`evidence_id` has no corresponding
file) and corrupt evidence (file exists but fails §62's parse/digest
checks) both SHALL result in the future consuming path deriving
`approval_present = False` — HATP-001's own `MISSING`/`MALFORMED`
status vocabulary already covers exactly this outcome (HATP-REQ-042,
HATP-REQ-090); this contract introduces no new evidence-store-specific
status enum for it, only a distinct `error_type` (`evidence_not_found`)
for the CLI-level lookup failure prior to verification ever running.

## 29. Authority Semantics

**HSCE-REQ-065.** Exit code `0` (`EXIT_SUCCESS`) from `pcae hatp sign
rollback` means exactly: a structurally valid `HATPSignedEvidenceEnvelope`
was durably persisted under `evidence_id`. It does NOT mean: rollback
approved; Permission Broker `ALLOW`; rollback executed; or HATP status
`VALID` was independently re-confirmed post-write (mirrors HATP-REQ-104
and 149O.8 §26's authority table).

**HSCE-REQ-066.** Success output (`--json` or text) SHALL display, at
minimum, `evidence_id` and the canonical evidence path. It SHALL NOT
display `approved=True`, `permission=ALLOW`, or `executed=True` — no
field resembling those SHALL appear anywhere in this command's output
schema (mirrors 149O.8 §59's explicit instruction).

## 30. Signing vs. Execution Separation

**HSCE-REQ-067.** Reaffirming 149O.8 §14 (not reopened by this
contract): `pcae hatp sign rollback` never calls `execute_rollback` or
`build_rollback_execution`, and no rollback-dispatch command performs a
hardware touch. The two remain separate lifecycle steps, connected only
by an `evidence_id` string passed between them by the human/operator.

## 31. Timestamp Generation and Clock Source

**HSCE-REQ-068.** `issued_at` SHALL be generated using this
repository's existing canonical timestamp convention (millisecond
precision, UTC, matching `_canonical_timestamp_string`'s exact
rendering in `human_approval_trusted_provenance.py`) — reused, not
reimplemented, by the signing command. The signing command SHALL NOT
accept a caller-supplied clock value in production; a non-production
deterministic-clock test seam, if any, is out of this contract's
production-surface scope.

## 32. Operation-Snapshot / TOCTOU / Post-Sign Recheck

**HSCE-REQ-069.** The signing command SHALL capture Decision/Binding/
operation context once, at proof-construction time (§9-10), and bind it
into the signed proof. This captured snapshot is what the human reviews
during the mandatory preview step (§33).

**HSCE-REQ-070.** Before final envelope persistence (after the hardware
touch, before the atomic write in §24), the signing command SHALL
re-read the same Decision/Binding/operation state it captured at §69
and compare it against the freshly re-read state. If the state has
changed (Decision superseded, Binding superseded/revoked, PER/job
record status changed) since the preview was shown, the signing command
SHALL discard the freshly-produced provider assertion, persist no
evidence, and fail with `evidence_serialization_failure` (a discarded,
now-stale signing attempt) — never publish evidence known to be stale
at the moment of publication. This is a UX/audit-quality improvement
only; HATP-001's own consumption-time re-verification (§21-§22,
HATP-REQ-072/073) remains the actual security boundary regardless of
whether this recheck runs.

## 33. Blind-Touch Defense

**HSCE-REQ-071.** The signing command SHALL display, in full, the
reconstructed canonical operation payload (every field from §9's table)
to the human and require explicit confirmation before requesting the
hardware touch — reusing `decision-session`'s preview-then-confirm UX
pattern (`decision_session.py`) as a UX precedent only, never its
self-asserted-identity model (149O.8 §5, rejected alternative C). The
human never signs a digest or payload they have not seen rendered in
full.

## 34. Constructor/Parser Domain Equivalence

**HSCE-REQ-072.** `HATPSignedEvidenceEnvelope`'s public constructor (if
implemented as a typed model, not only a dict) and its parser SHALL
enforce the identical structural-validation domain — no envelope
constructible directly that the parser would reject, and vice versa
(mirrors the B-149O.1H-2 lesson HATP-001's own
`HumanApprovalProvenanceProof.__post_init__` already applies, §21 of
this contract's basis document).

## 35. Immutability of the Envelope Model

**HSCE-REQ-073.** If implemented as a typed model, `HATPSignedEvidenceEnvelope`
SHALL be immutable/frozen (e.g. `@dataclass(frozen=True)`), matching
every other HATP-001/RAE-001 evidence-bearing type's convention.

## 36. `pcae remote rollback approve` Interoperability

**HSCE-REQ-074.** Reaffirming 149O.8 §15 (not reopened): `pcae remote
rollback approve` is deprecated on a defined three-stage migration
timeline and is not modified by this contract. This contract's signing
command and evidence store are additive, inert surfaces until a future
consuming phase (149O.12-13) wires `--hatp-evidence` into dispatch
preconditions. `rollback_approval_state` remains sole authority until
that wiring ships and a deployment's substrate reaches
`operational=True` (149O.8 §15 stages 1-3, unchanged).

## 37. Security Invariants

**HSCE-REQ-075.** The following invariants are frozen and MUST be
preserved by any future implementation:

- **SC-1.** Only the operation locator (`--job-id`/`--per-id`) may be
  human-selected on `pcae hatp sign rollback`. Every other proof field
  is derived (§9).
- **SC-2.** All signed governance fields derive from canonical current
  state at signing time (§9-10), never from caller input.
- **SC-3.** The provider is always production-resolved (§11); no
  test/software provider is reachable from this command.
- **SC-4.** Human presence is always provider-derived (§13); no caller
  boolean exists.
- **SC-5.** `evidence_id` derives only from the canonical proof payload
  (§17), never from `provider_assertion` or any other envelope field.
- **SC-6.** Evidence lookup is always explicit-`evidence_id`-only (§21);
  no implicit "latest" selection exists anywhere.
- **SC-7.** Existing evidence can never be silently overwritten (§19);
  a same-ID conflicting write is always rejected, never replaced.
- **SC-8.** Envelope corruption or missing evidence never falls back to
  legacy `rollback_approval_state` authority (§28, §36) — it always
  resolves to no HATP approval for that `evidence_id`.
- **SC-9.** Evidence file existence, alone, is never treated as
  approval (§27, explicit forbidden-pattern statement).
- **SC-10.** Signing success (`EXIT_SUCCESS`) is never Permission Broker
  permission or rollback execution (§29).
- **SC-11.** Secrets (PIN, private key material) never enter persisted
  evidence, logs, or `argv` (§23).
- **SC-12.** Consumption always re-verifies current protected trust-
  store/repository/deployment state (§21, deferring to HATP-001 §21-22)
  — a signing-time-valid proof is never trusted without fresh
  consumption-time verification.

## 38. Mandatory Future Attack Matrix

**HSCE-REQ-076.** The following attacks are frozen as the minimum set a
future implementation's independent verification (149O.11) MUST
exercise against this contract's own surface, each with the stated
expected outcome:

1. `evidence_id` containing `../` or an absolute path &rarr; rejected
   before filesystem access (§25).
2. `evidence_id` with uppercase hex characters &rarr; rejected, no
   case-insensitive alias (§26).
3. Existing `evidence_id`, byte-identical envelope re-write &rarr;
   idempotent success, no error (§19(A)).
4. Existing `evidence_id`, differing envelope bytes (including only a
   differing `provider_assertion`) &rarr; `evidence_conflict`, no
   overwrite (§19(B), §18).
5. Envelope JSON with a duplicate top-level key &rarr; rejected at parse
   (§53, §62).
6. Envelope with an unknown top-level field &rarr; rejected, closed
   schema (§14, §62).
7. Envelope with `evidence_version` other than integer `1` (including
   `true`/`false`) &rarr; rejected, `unsupported_envelope_version`
   (§15).
8. Envelope missing a required field &rarr; rejected at parse (§62).
9. `evidence_id` not matching `digest_hatp_proof_payload(proof)` of the
   embedded `proof` &rarr; rejected, `evidence_id_digest_mismatch`
   (§62).
10. Corrupt/truncated `provider_assertion` bytes &rarr; envelope parses
    (structural validity, §63) but `verify_hatp_proof` fails at
    verification time, never treated as `VALID` by construction.
11. Signing attempted against an operation profile string other than
    `HATP_HARDWARE_PROVIDER_V1` &rarr; unreachable — no `--provider`
    flag exists to request one (§22 of this contract, §11).
12. Wrong operation (envelope produced for one `job_id`, referenced for
    another) &rarr; caught at consumption by HATP-001's own
    `WRONG_OPERATION` (HATP-REQ-083), unaffected by this contract's
    storage layer.
13. `evidence_id` symlinked to a path outside the repository &rarr;
    rejected, write refuses to follow (§25(2)).
14. `.pcae/hatp-evidence/` itself replaced by a symlink escaping the
    repository &rarr; rejected, write refuses (§25(3)).
15. Partial/interrupted write (process killed mid-write) &rarr; no
    partial file discoverable at the canonical path — atomic
    temp-file + rename discipline (§24) guarantees only a complete file
    or no file is ever visible at `envelopes/{evidence_id}.json`.
16. Human cancels touch &rarr; no evidence file written, exit code 5
    (§13, §29).
17. Hardware device absent &rarr; `provider_unavailable`, exit code 4,
    no software fallback (§13).
18. Post-preview Decision/Binding mutation before touch completes
    &rarr; discarded, no evidence persisted (§32).
19. Attempted signing with no matching RAE Binding &rarr;
    `binding_unavailable`, exit code 3, before any hardware touch is
    requested (§10, §21).
20. `--per-id` for a PER whose `ecp_id` cannot be resolved &rarr;
    `operation_not_found`, exit code 2 (§7).
21. **[Added, Phase 149O.10.1, Obs-2 — the AG3 analogue of item 20,
    independently observed missing by Phase 149O.10.]** `--job-id` for a
    job whose `original_commit_sha` cannot be resolved from the live job
    record &rarr; `operation_not_found`, exit code 2 (§6) — resolution
    fails before any hardware touch, before any proof is constructed, and
    before any envelope is persisted, mirroring item 20's AG5 outcome
    exactly.

## 39. Contract Ownership and Versioning

**HSCE-REQ-077.** This contract was originally versioned `1.0`, frozen
because every blocking-contract-condition named in the governing phase
prompt (§40 below) was resolved. It is now versioned `1.1` (§44),
narrowly repaired by Phase 149O.10.1 to close Finding 149O.10-F-3
(BLOCKING, §52) while every other v1.0 selection is carried forward
unamended. A future amendment beyond the scope of §44's repair (e.g. to
add a second provider profile's envelope encoding, or to define the
cross-principal IPC mechanism 149O.8 §21 explicitly deferred) SHALL
proceed through a governed contract-amendment phase, never through
silent reinterpretation of this text.

**HSCE-REQ-078.** **[Corrected, Phase 149O.10.1, Finding F-1 — this
requirement originally read "through `HSCE-REQ-078` inclusive (this
requirement)," an editorial miscount independently caught by Phase
149O.10: `HSCE-REQ-079` exists below in §40, contradicting the original
text. No requirement was renumbered, added, or removed to fix this — the
sequence was already 001..079, gapless, this sentence's own count was
simply wrong.]** **[Further updated, Phase 149O.20L.7O.2F.2, §46 — five
requirements (`HSCE-REQ-080`..`HSCE-REQ-084`) were appended by §46's
BF-1/BF-2 repair; no existing requirement was renumbered, added
mid-sequence, or removed.]** This contract defines requirements
`HSCE-REQ-001` through `HSCE-REQ-084` inclusive, sequential, no gaps, no
duplicates, mirroring HATP-001's own numbering convention.

## 40. Blocking-Condition Check

**HSCE-REQ-079.** Independently checked against every ambiguity named
blocking by the governing phase prompt (§114-§115 of the prompt):

| Blocking condition | Resolved? | Where |
|---|---|---|
| Exact CLI command syntax | Yes — `pcae hatp sign rollback --site {ag3\|ag5} [locator] [--json]`, no dry-run | §5 |
| AG3 locator | Yes — `--job-id` only | §6 |
| AG5 locator / production entry point | Yes — `--per-id` only, `ecp_id` auto-derived; `pcae rollback --per-id` identified as the real AG5 entry point | §7 |
| Proof-field canonical sources | Yes — full table, no ambiguity | §9 |
| Provider resolution | Yes — `create_production_hardware_provider` only | §11 |
| Signer resolution | Yes — protected trust-store cross-check only | §11 |
| Evidence envelope field set | Yes — closed 4-field schema | §14 |
| Evidence encoding | Yes — Base64 `provider_assertion`, canonical sorted-key JSON | §16, §24 |
| Evidence ID formula | Yes — `digest_hatp_proof_payload(proof)` | §17 |
| Same-ID/different-provider-evidence behavior | Yes — first-write-canonical, byte-compare, conflict on mismatch | §18-19 |
| Overwrite/no-clobber semantics | Yes — CREATE-ONCE, no `--force` | §19 |
| Store root | Yes — `.pcae/hatp-evidence/` | §20 |
| Filename | Yes — `envelopes/{evidence_id}.json` | §20 |
| Path traversal handling | Yes | §25 |
| Lookup semantics | Yes — explicit ID only | §21 |
| Error vocabulary | Yes — closed 12-member table | §22 |
| Exit-code semantics | Yes — closed 9-value set | §22 |
| Human cancellation | Yes | §13 |
| Secret handling | Yes | §23 |
| Signing-success authority meaning | Yes — not approval/ALLOW/execution | §29 |
| Missing/corrupt evidence behavior | Yes — `approval_present=False`, no fallback | §28 |
| Legacy fallback prohibition | Yes | §27, §36 |

No condition in this list is unresolved. This contract is FROZEN v1.0.

## 41. Contract Freeze Verdict

```
HSCE-001 v1.0 FROZEN
— HATP SIGNING CEREMONY + EVIDENCE STORE CONTRACT COMPLETE
```

## 42. Implementation Readiness Status

```
HATP-001 contract:                     FROZEN (unchanged, unamended)
HSCE-001 contract:                     FROZEN (this contract, Phase 149O.9)
Signing CLI implementation:            NOT IMPLEMENTED
Evidence store implementation:         NOT IMPLEMENTED
AG3/AG5 mandatory-consumption wiring:  NOT IMPLEMENTED (149O.12-13)
HATP production:                       NOT READY
```

This contract's freeze does not imply implementation exists. No `pcae
hatp sign` command, no evidence-store code, and no envelope
serializer/parser is implemented in production by this phase. No
production source file was modified. No hardware was touched. No
rollback dispatch behavior changed.

## 43. Recommended Next Phase

```
149O.10 — HATP Signing Ceremony + Evidence Store Contract Independent
Verification
```

The independent verifier SHALL attack, at minimum, every item in §38's
mandatory attack matrix, re-confirm §7's AG5 CLI entry-point inventory
against the then-current source tree, and re-confirm no production
source or HATP-001/RAE-001 contract text was modified by this phase.
Only after independent verification should signing-ceremony
implementation begin (149O.8's own phase-breakdown table, §27, numbered
this "149O.10 — Signing Ceremony Implementation"; the current governing
prompt for this phase inserts a dedicated contract-verification step
ahead of it, so implementation now follows one phase later than 149O.8's
original sketch — a sequencing refinement, not a scope change).

## 44. Phase 149O.10.1 contract repair — HSCE-REQ-052 exclusive-publish repair

**Version:** 1.1
**Predecessor:** HSCE-001 v1.0 (Phase 149O.9)
**Repaired by:** Phase 149O.10.1 — HSCE-001 Narrow Contract Repair

**Reason:** Phase 149O.10's Independent Verification independently
demonstrated Finding 149O.10-F-3 (BLOCKING): HSCE-REQ-052's v1.0
check-then-`os.replace` publication algorithm does not mechanically
guarantee SC-7 under concurrent writers. `os.replace` is unconditional on
POSIX and carries no exclusivity of its own; a preceding `path.exists()`
check cannot close the window between two concurrent writers each
observing "destination absent" for the same `evidence_id`. Concretely:
Writer A observes the destination absent, Writer B observes the
destination absent, Writer A publishes its envelope, Writer B's
unconditional `os.replace` then silently replaces Writer A's envelope —
violating CREATE-ONCE, NO-CLOBBER, and FIRST-WRITE-CANONICAL even though
§18-19's *prose* already stated those rules correctly. RAE-001's own
`RollbackApprovalEvidenceStore.write_creation_registration`
(`rollback_approval_evidence.py`) already demonstrates a true exclusive-create
primitive (`os.open(path, O_CREAT | O_EXCL | O_WRONLY)`) in production in
this exact codebase, confirming the fix pattern was available and simply
not selected for HSCE-REQ-052 at freeze time.

**Selected design and rejected alternative:** Two candidate designs were
considered, per this repair's governing prompt: (A) atomic hard-link
publication, and (B) a separate exclusive-claim/creation-registry
directory mirroring RAE-001's two-file (`bindings/` +
`creation-registry/`) split. **(A) was selected.** RAE-001's split exists
specifically to detect a Binding written outside
`create_rollback_approval_binding`'s own call path — a bypass concern
that does not apply here, because HSCE-001 §20 (HSCE-REQ-042, unamended
by this repair) already establishes that this store has no second,
independently-writable directory an envelope needs to be cross-validated
against; the envelope's own identity IS the content it stores. Introducing
a creation-registry directory now would both reopen §20 (outside this
repair's narrow scope — this repair amends HSCE-REQ-052 only) and add a
second persistent state machine (registry-claim lifecycle, orphan-claim
handling, claim-vs-envelope crash recovery) this repair's own governing
prompt's minimality principle explicitly disfavors when a simpler
primitive suffices. Atomic hard-link publication adds no new directory,
no new file kind, and no second state machine: a single `os.link` call
against the existing `envelopes/{evidence_id}.json` path is simultaneously
the exclusivity check and the publication act, with the identical
temp-file-plus-fsync durability step §24 already required. It is
therefore the smaller, self-consistent repair.

**Changed requirements:** `HSCE-REQ-052` (§24) — replaced in full; see
the requirement text itself for the repaired algorithm. `HSCE-REQ-077`,
`HSCE-REQ-078` (§39) — reworded for the version bump and the F-1 count
correction (below); no requirement was renumbered, added, or removed by
either edit. §38's attack matrix — widened from 20 to 21 items (Obs-2,
below); no existing item's text was changed. No other `HSCE-REQ-###` was
touched. §§1-23, §25-38 (except the one added attack item), and §§40-43
are byte-identical to v1.0.

**F-1 disposition (requirement-count correction, non-blocking):**
**CLOSED.** HSCE-REQ-078 (originally: "this contract defines requirements
HSCE-REQ-001 through HSCE-REQ-078 inclusive (this requirement)")
undercounted by one — HSCE-REQ-079 already existed in §40 at v1.0 freeze
time. Corrected to "through HSCE-REQ-079 inclusive." No requirement was
renumbered or the sequence altered; the actual defined range was always
001..079, gapless, no duplicates — only the self-referential count
statement was wrong.

**F-2 disposition (`_write_atomic_json` reuse wording, non-blocking):**
**CLOSED.** v1.0's HSCE-REQ-052 claimed reuse of
`_write_atomic_json`
"already uses" verbatim, but that function performs no symlink check, so
literal unmodified reuse cannot itself satisfy HSCE-REQ-057/058. The
repaired HSCE-REQ-052 no longer claims literal reuse of that helper at
all — step (2) of the repaired algorithm explicitly states it mirrors
`_write_atomic_json`'s "temp-file-in-same-directory discipline... the
technique, not a literal unmodified call to that helper, since it lacks
the symlink checks §57-58 separately require." This closes F-2 as a
byproduct of the F-3 repair, not through a separate wording patch.
HSCE-REQ-057 and HSCE-REQ-058 (§25) are byte-unchanged and are explicitly
cross-referenced, unweakened, by the repaired HSCE-REQ-052 (step (6)).

**149O.10-F-3 disposition (atomic no-clobber publication race,
BLOCKING):** **REPAIRED AT CONTRACT LEVEL, PENDING INDEPENDENT
RE-VERIFICATION.** Not independently closed by this repair phase (§62
below) — a future phase (§45) must independently re-verify the repaired
algorithm before HSCE-001 v1.1 can be called VERIFIED.

**Obs-2 disposition (AG3 `original_commit_sha`-resolution attack-matrix
gap, non-blocking):** **CLOSED.** §38 item 21 added, the AG3 analogue of
item 20 (AG5 `ecp_id`-resolution failure): a job-locator that resolves
but whose `original_commit_sha` cannot be resolved from the live job
record fails closed with `operation_not_found` (exit code 2, §6) before
any hardware touch, proof construction, or evidence persistence — no new
`error_type` was needed; the existing vocabulary already covered this
case unambiguously, only the attack-matrix enumeration was incomplete.

**Regression review:** independently reconfirmed unchanged by this
repair — the CLI grammar (§5-§8, byte-unchanged), the AG3/AG5 locators
(§6-§7, byte-unchanged, including the production entry-point inventory
finding), the proof field-source table (§9, byte-unchanged), Decision/
Binding lookup (§10, byte-unchanged), provider/signer resolution
(§11, byte-unchanged), substrate-readiness non-precondition (§12,
byte-unchanged), human-presence/cancellation/device-fault handling (§13,
byte-unchanged), the envelope's closed four-field schema (§14-§16,
byte-unchanged), the evidence-ID formula and content-addressing
precision (§17-§18, byte-unchanged prose — only the *mechanism* enforcing
§19's rule changed, not §19's own stated rule), the evidence-store root
and layout (§20, byte-unchanged — no creation-registry directory
introduced), evidence lookup semantics (§21, byte-unchanged), the closed
error vocabulary and exit-code mapping (§22, byte-unchanged — no new
`error_type` or exit code introduced), secret handling (§23,
byte-unchanged), path validation/traversal/symlink rejection (§25,
byte-unchanged and explicitly reaffirmed by the repaired HSCE-REQ-052),
case sensitivity (§26, byte-unchanged), storage trust classification
(§27, byte-unchanged), envelope load-time validation (§28,
byte-unchanged), authority semantics (§29, byte-unchanged), signing/
execution separation (§30, byte-unchanged), timestamp generation (§31,
byte-unchanged), TOCTOU/post-sign recheck (§32, byte-unchanged),
blind-touch defense (§33, byte-unchanged), constructor/parser domain
equivalence (§34, byte-unchanged), envelope immutability (§35,
byte-unchanged), `pcae remote rollback approve` interoperability (§36,
byte-unchanged), and all twelve security invariants SC-1 through SC-12
(§37) — SC-7's own *statement* is unchanged ("existing evidence can never
be silently overwritten... always rejected, never replaced"); only the
mechanism that mechanically delivers it was repaired.

**Compatibility review:** independently confirmed. HATP-001 v1.0 and
RAE-001 v1.0 remain byte-unchanged (§4, §6-§7, unamended); this repair
touches only HSCE-001's own text. No new capability is introduced: the
repaired algorithm produces the identical set of externally observable
outcomes (`EXIT_SUCCESS` for the winner, idempotent `EXIT_SUCCESS` for a
byte-identical loser, `EXIT_EVIDENCE_CONFLICT` for a differing loser,
`EXIT_PERSISTENCE_FAILURE` for an unsupported filesystem) the v1.0 text
already named as the correct outcomes in §18-§19's prose — it only
repairs the *mechanism* that reliably produces them under concurrency,
which v1.0's mechanism did not.

**Migration effect:** None. No signing-CLI or evidence-store
implementation exists as of this revision (independently reconfirmed —
this repair phase implements nothing; see the No-Go list in this
contract's governing phase report). No in-flight evidence file, schema,
or code path is affected by this documentation-only correction.

**Backward-compatibility impact:** None beyond the publication mechanism
itself. The `HATPSignedEvidenceEnvelope` schema (§14), the evidence-ID
formula (§17), the storage layout (§20), and the lookup semantics (§21)
are byte-identical to v1.0; a hypothetical v1.0-conformant implementation
description that already treated "existing evidence can never be
silently overwritten" as its actual behavioral target (as §18-§19's prose
always required) needs no behavioral change beyond swapping its
publication primitive — which it was already obligated to get right.

No implementation of the signing ceremony or evidence store is
authorized, performed, or implied by this repair. No `pcae hatp sign`
command, no evidence-store code, and no envelope serializer/parser is
implemented in production by this phase. No production source file
(`src/pcae/**`) was modified. HATP-001 v1.0 and RAE-001 v1.0 remain
byte-unchanged. No hardware was touched. No rollback dispatch behavior
changed. No Permission Broker behavior changed. Runtime remains State:
Observed, Maximum Capability: observe, Execution Availability:
unavailable, unchanged before and after this repair.

## 45. Post-repair next phase

The expected next phase is **149O.10.2 — HSCE-001 Atomic No-Clobber
Repair Independent Re-Verification**, mirroring this repository's
repair-then-reverify precedent (143H→143I.1→143I.2 for IWC-001's own
state-transition-table repair; 138C.1→138C.2; 137M→137MV). That phase
should focus narrowly on: the exclusive-publication race itself (identical
concurrent writers, differing concurrent writers, many-writer races, not
only the two-writer case), crash-before-publish and crash-after-publish
semantics, unsupported-filesystem fail-closed behavior, symlink/path
preservation under the new primitive (§57-§58 unweakened), canonical
byte-comparison semantics (§53, unchanged), the version/count corrections
(F-1), the AG3 attack-matrix addition (Obs-2), and non-regression of
every HSCE-001 section this repair did not touch. This recommendation
does not authorize 149O.10.2. HSCE-001 v1.1 is **REPAIRED AT CONTRACT
LEVEL — READY FOR INDEPENDENT RE-VERIFICATION**, not VERIFIED; HATP
production remains NOT READY until that re-verification (and the
149O.12-13 consumption wiring §36 already describes) completes.

## 46. Phase 149O.20L.7O.2F.2 contract repair — signing-time credential resolution repair (BF-1/BF-2)

**Version:** 1.2
**Predecessor:** HSCE-001 v1.1 (Phase 149O.10.1)
**Repaired by:** Phase 149O.20L.7O.2F.2 — FIDO2 Signing-Time Credential
Resolution Repair

**Reason.** Phase 149O.20L.7O.2F.1's Independent Verification found two
Blocking findings against the Trust-Enrollment implementation capability:

- **BF-1.** Production signing (`hatp_signing_ceremony.py::_resolve_signer`,
  called unconditionally from `sign_rollback_evidence`) depended on
  `provider.credential_identity()` to resolve `principal_id`/
  `signer_key_id` — exactly what v1.1's HSCE-REQ-018/HSCE-REQ-024 named
  as the canonical resolution mechanism. `Fido2HardwareProvider.
  credential_identity()` unconditionally raises `HATPProviderUnavailableError`
  (confirmed unchanged by re-reading `hatp_fido2_provider.py:307-313`
  directly in this phase) — independent of device presence. No enrolled
  FIDO2 signer could ever reach production signing.
- **BF-2.** `Fido2HardwareProvider.enroll_credential()`'s CTAP2
  `make_credential` call (`hatp_fido2_provider.py:361-367`) passes no
  `options` map at all — confirmed by re-reading the call site directly
  in this phase — so no `rk`/resident-key flag is requested; CTAP2
  authenticators default `rk` to `false`, producing a non-resident
  (non-discoverable) credential. `credential_identity()`'s own docstring
  (v1.1-era, unchanged) explicitly assumed a "discoverable/resident
  credential" — a structural mismatch between what enrollment produces
  and what signing-time identity resolution (as v1.1 specified it) could
  ever discover.

**Model evaluated and rejected: Model A (authenticator rediscovery).**
Would require repairing `enroll_credential()` to request `rk=true` and
repairing `credential_identity()` to enumerate resident credentials via a
live CTAP2 `getAssertion`/credential-enumeration call, with ambiguous
multiple-resident-credential enumeration failing closed. Rejected because:
(a) it requires a live hardware touch merely to discover *who* is
signing, before the human has seen anything to confirm (directly in
tension with HSCE-REQ-071's blind-touch defense, which requires the full
preview — including `principal_id`/`signer_key_id` — to be shown *before*
any hardware touch); (b) resident-credential capacity is a real,
authenticator-model-dependent CTAP2 limitation this repository cannot
verify without physical hardware (the governing prompt's own no-go list
forbids provisioning real hardware in this phase); (c) it would require
`enroll_credential()`'s already-implemented, tested, deployed behavior to
change, re-touching Surface A, which Phase 149O.20L.7O.2F.1 verified
clean and this phase's own governing prompt instructs not to reopen
without new evidence — Model A supplies exactly that "new evidence
requires it" trigger only if selected, so selecting it would itself
create the reopening it is supposed to justify, a circular
justification this phase declines to accept without a stronger reason
than "it is the more literally spec-shaped CTAP2 usage."

**Model selected: Model B (durable-registry signer resolution).** This
repository's `HATPTrustStore` (`hatp_bootstrap.py`) already carries
exactly the durable, non-hardware-derived signer-identity source Model B
needs: `DeploymentBinding` (HATP-REQ-057-063) already binds exactly one
`(principal_id, signer_key_id, provider_profile)` tuple to exactly one
`(repository_id, canonical_deployment_root)` pair, keyed uniquely (one
`DeploymentBinding` per `repository_id` in the registry's own dict-keyed
storage, `hatp_bootstrap.py::_ParsedRegistry.deployment_bindings`).
`Fido2HardwareProvider.request_signature()` (unchanged, re-read directly
in this phase, `hatp_fido2_provider.py:397-450`) already accepts an
explicit `signer_key_id` parameter and uses it as CTAP2 `get_assertion`'s
`allow_list` credential id — it has never depended on resident-credential
discovery; it already works correctly against a non-resident credential
today. Model B therefore requires no change to `enroll_credential()`, no
change to `request_signature()`, and no new provider method: the entire
repair is confined to `_resolve_signer`'s *source* of `signer_key_id`,
replacing a hardware call with a registry read. This is the smaller,
self-consistent repair, mirroring §44's own minimality precedent.

**HSCE-REQ-080.** `principal_id`/`signer_key_id` (HSCE-REQ-018's table,
revised above) SHALL be resolved exclusively as follows, in this exact
order, before any hardware touch (HSCE-REQ-071's blind-touch defense is
therefore satisfiable: every field below is knowable pre-touch):

1. Resolve `canonical_deployment_root` for the local repository root
   (`hatp_bootstrap.resolve_canonical_deployment_root`).
2. Call `HATPTrustStore.production().resolve_deployment_authorization(
   repository_id=..., canonical_deployment_root=...)`. If this returns
   `None`, fail `no_authorized_signer`.
3. The returned `DeploymentBinding`'s `provider_profile` MUST equal the
   resolved production provider's own profile
   (`HATP_HARDWARE_PROVIDER_V1`, HSCE-REQ-022); a mismatch fails
   `no_authorized_signer`.
4. `HATPTrustStore.production().lookup_signer(binding.signer_key_id)`
   MUST return a `SignerRecord` with `status == "active"`, identical
   `signer_key_id`, `principal_id == binding.principal_id`, and
   `provider_profile` matching step 3's value; otherwise
   `no_authorized_signer`. These are consumer-time checks: producer-time
   validation does not authorize trusting historically persisted
   cross-record relationships without revalidation.
5. `HATPTrustStore.production().lookup_principal(binding.principal_id)`
   MUST return a `PrincipalRecord` with `status == "active"` and
   `principal_id == binding.principal_id`; otherwise
   `no_authorized_signer`.
6. `HATPHardwareCredentialStore.production().lookup_credential(
   binding.signer_key_id)` MUST return a `HardwareCredentialRecord` with
   `status == "active"`, `signer_key_id == binding.signer_key_id`, and
   `provider_profile` matching step 3's value; otherwise
   `no_authorized_signer`.

The hardware provider's own credential-identity/discovery operation
(`credential_identity()`, whatever name a future provider gives it, per
HPSE-REQ-059) is never called by this resolution path (BF-1 repair).

**HSCE-REQ-081.** Multiple-signer behavior is fully determined by
`DeploymentBinding`'s own existing structural uniqueness (HATP-REQ-057-063,
unamended): the registry stores at most one `DeploymentBinding` per
`repository_id` (`hatp_bootstrap.py::_ParsedRegistry.deployment_bindings`
is a `dict[str, DeploymentBinding]`, not a list — a second `create_
deployment_binding` call for the same `repository_id` is already a
`DuplicateConflictingBindingError` at the writer layer,
`hatp_deployment_binding_admin.py`, unamended by this repair). There is
therefore no "multiple active signers for one deployment" state HSCE-REQ-080
must itself disambiguate — deployment-binding rotation
(`hatp_deployment_binding_admin.py::rotate_deployment_binding`, unamended)
is the sole mechanism that ever changes which signer a deployment resolves
to, and it is administrative-surface-only, never CLI-reachable from `pcae
hatp sign rollback`. No `--signer` flag is introduced (HSCE-REQ-024,
unchanged in this respect) and none is needed: the deterministic binding
HSCE-REQ-081 relies on already existed before this repair; the repair
only teaches the signing command to read it.

**HSCE-REQ-082.** Registry identity resolution (HSCE-REQ-080) is
distinct from, and never a substitute for, cryptographic possession
proof. This repair does not weaken §13's hardware-provider possession
requirement in any way: `request_signature()` is still called exactly
once per ceremony attempt (HSCE-REQ-013's structure, unamended), still
requires a fresh, per-operation physical touch (`AuthenticatorData.FLAG.UP`,
unamended, `hatp_fido2_provider.py`'s own docstring), and the resulting
signature is still independently verified at consumption time against
the durable `HardwareCredentialRecord`'s public key (HATP-001 §21-22,
unamended) — a `DeploymentBinding` naming a `signer_key_id` grants no
authority by itself; only a verified hardware signature over that exact
`signer_key_id`'s registered public key does. The registry answers "who
is this deployment's authorized signer"; the hardware authenticator alone
answers "did that signer actually touch the device for this specific
operation." Neither answers the other's question.

**HSCE-REQ-083.** **[Revised, v1.3, §48 — cross-record/TOCTOU repair.]**
HSCE-REQ-069/070's TOCTOU post-sign recheck (§32, unamended in mechanism)
is extended to cover the complete signer-resolution authority state: because
`principal_id`/`signer_key_id` are now resolved from durable, mutable
registry state (HSCE-REQ-080) rather than from an immutable
per-invocation hardware response, the signing command SHALL re-run
HSCE-REQ-080's full resolution a second time, from the same live state,
immediately before the post-touch context comparison. The comparison SHALL
use an immutable semantic snapshot containing the repository identity,
canonical deployment root, resolved production provider profile, complete
`DeploymentBinding`, `SignerRecord`, `PrincipalRecord`, and
`HardwareCredentialRecord` values used by HSCE-REQ-080. Any failed
cross-record check or any difference in that authority state between the
pre-touch and post-touch resolutions SHALL be treated identically to any
other HSCE-REQ-070 mismatch: discard the freshly-produced provider
assertion, persist no evidence, fail `evidence_serialization_failure`.
Object identity is not a valid comparison; equal canonical field values
are. This includes same-principal/same-signer changes to authority-relevant
binding or credential fields that the former tuple-only comparison could
not observe.

**HSCE-REQ-084.** `credential_identity()` (or a future provider's
differently-named equivalent per HPSE-REQ-059) is not part of the
production signing-time resolution path as of this v1.2 revision
(HSCE-REQ-080 replaces it entirely), and is not part of the FIDO2
enrollment path either (`enroll_credential()`, HPSE-REQ-059's own
explicitly-anticipated distinct-method allowance, already serves
enrollment — unamended by this repair). This is not an unresolved dead
required method: `credential_identity()` remains a structural
`HATPHardwareSigner`/`HATPProofVerifierProvider`-adjacent method some
future provider profile (e.g. PIV, if it independently satisfies
HPSE-REQ-059/060) MAY implement meaningfully, but no current production
code path — enrollment or signing — calls it for FIDO2. Non-resident
FIDO2 credentials (BF-2) remain fully valid for the entire production
signing path under this disposition: signing never relies on resident-
credential discovery, so `enroll_credential()`'s non-resident output is
not a defect relative to this contract's actual (v1.2) resolution
mechanism. No ambiguous halfway state exists: FIDO2's `credential_identity()`
is cleanly and permanently out of the production path, not "sometimes
needed."

**Changed requirements:** `HSCE-REQ-018` (§9, table row revised),
`HSCE-REQ-024` (§11, revised), `HSCE-REQ-047` (§22, one table cell's
wording revised — no `error_type` or exit code added, removed, or
renumbered), `HSCE-REQ-078` (§39, count updated). New: `HSCE-REQ-080`
through `HSCE-REQ-084` (this section). No requirement was renumbered or
removed. §§1-8, §10, §12-21, §23, §25-45 (except HSCE-REQ-047's one
revised table cell and HSCE-REQ-078's count, both noted above) are
byte-identical to v1.1.

**Regression review:** independently reconfirmed unchanged by this
repair — the CLI grammar (§5-§8, byte-unchanged), the AG3/AG5 locators
(§6-§7, byte-unchanged), Decision/Binding (RAE) lookup (§10,
byte-unchanged), provider resolution's own unconditional-call requirement
(HSCE-REQ-022/023, byte-unchanged — the production provider factory and
trust-store factory are still always called), substrate-readiness
non-precondition (§12, byte-unchanged), human-presence/cancellation/
device-fault handling (§13, byte-unchanged — `request_signature()` itself
is untouched by this repair), the envelope's closed four-field schema
(§14-§16, byte-unchanged), evidence-ID formula and content-addressing
(§17-§18, byte-unchanged), exclusive-publish mechanism (§19/HSCE-REQ-052,
byte-unchanged, carried forward from §44), evidence-store root/layout
(§20, byte-unchanged), evidence lookup semantics (§21, byte-unchanged),
the closed error vocabulary's own member set and exit-code mapping
(HSCE-REQ-046/048, byte-unchanged — only one table cell's *wording*
changed under the unchanged `no_authorized_signer`/exit-4 pairing),
secret handling (§23, byte-unchanged), path validation (§25,
byte-unchanged), case sensitivity (§26, byte-unchanged), storage trust
classification (§27, byte-unchanged), envelope load-time validation
(§28, byte-unchanged), authority semantics (§29, byte-unchanged),
signing/execution separation (§30, byte-unchanged), timestamp generation
(§31, byte-unchanged), blind-touch defense (§33, byte-unchanged in
mechanism — HSCE-REQ-080 step ordering keeps every previewed field
resolvable before any touch), constructor/parser domain equivalence and
envelope immutability (§34-§35, byte-unchanged), `pcae remote rollback
approve` interoperability (§36, byte-unchanged), and eleven of twelve
security invariants SC-1 through SC-12 (§37) — unchanged verbatim; SC-3/
SC-4 (production-only provider/trust-store resolution paths) are
reaffirmed, not weakened, by HSCE-REQ-080 reading exclusively from
`HATPTrustStore.production()`/`HATPHardwareCredentialStore.production()`.

**Compatibility review:** independently confirmed. HATP-001 v1.0 and
RAE-001 v1.0 remain byte-unchanged. HPSE-001 v1.1 and HHCE-001 v1.1
remain byte-unchanged by this contract's own text (this repair touches
only HSCE-001). No new capability is introduced beyond making an already
HHCE-001/HPSE-001-enrolled FIDO2 signer actually reachable from
production signing — the exact, narrowly-scoped repair this phase's
governing prompt authorized. No `--signer`, `--force`, or other new CLI
flag is introduced (HSCE-REQ-026, unchanged).

**Migration effect:** None. No `pcae hatp sign rollback` implementation
exists in production as of this revision — `hatp_signing_ceremony.py`
implements the orchestrator (149O.12B) but no CLI wires it (149O.12C's
own module docstring, unamended, still states "No CLI is implemented by
this module"). This phase's implementation changes (§ below, tracked in
`hatp_signing_ceremony.py`, not in this contract file) are the first
production consumer of this v1.2 text.

No hardware was provisioned, no real credential was registered, no real
principal or signer was enrolled, no real `DeploymentBinding` was
created, and no runtime capability changed as a result of this contract
repair. Runtime remains State: Observed, Maximum Capability: observe,
Execution Availability: unavailable, unchanged before and after this
repair.

## 47. Post-repair next phase

The expected next phase is **149O.20L.7O.2F.3 — FIDO2 Signing-Time
Credential Resolution Repair Independent Verification**, narrowly scoped
to: independently re-deriving BF-1/BF-2 against the repaired source,
confirming HSCE-REQ-080's six-step resolution order is implemented
exactly, confirming HSCE-REQ-081's multiple-signer-is-structurally-moot
claim against the actual registry code, confirming HSCE-REQ-082's
authority-distinction claim (no code path substitutes registry trust for
a hardware touch), confirming HSCE-REQ-083's extended TOCTOU recheck is
implemented and actually detects a mid-ceremony `DeploymentBinding`
rotation, confirming HSCE-REQ-084's disposition against the actual
`Fido2HardwareProvider` source, running the full HATP signing/proof/
DeploymentBinding regression suite, and independently re-running the
adversarial attack matrix (§38, widened by this repair's implementation
phase). This recommendation does not authorize 149O.20L.7O.2F.3. HSCE-001
v1.2 is **REPAIRED AT CONTRACT LEVEL — READY FOR INDEPENDENT
RE-VERIFICATION**, not VERIFIED; HATP production remains NOT READY until
that re-verification, the still-pending 149O.10.2 HSCE-REQ-052
re-verification (§45), and the 149O.12-13 consumption wiring (§36) all
complete.

## 48. v1.3 Durable-Registry Cross-Record and Revalidation Repair

Phase 149O.20L.7O.2F.3 independently demonstrated two schema-valid
historical-state failures at the signing boundary:

- **B-149O.20L.7O.2F.3-1:** a `DeploymentBinding` principal differing
  from its `SignerRecord.principal_id` was accepted, touched hardware,
  and published an envelope;
- **B-149O.20L.7O.2F.3-2:** a `SignerRecord.provider_profile` differing
  from the binding, credential, and resolved production provider was
  accepted with the same consequences.

HSCE-REQ-018/024 already require the resolved durable records and
provider profile to be cross-checked and already require mismatches to
fail `no_authorized_signer`; HPSE-REQ-062 independently defines the
`SignerRecord` as the durable signer-key/principal/provider binding.
HSCE-REQ-080 steps 4-6 are revised only to state those existing
relationships mechanically and remove their prior omission from the
six-step algorithm. No new identity source, operation, error, or
capability is introduced.

HSCE-REQ-083's former text was genuinely ambiguous for same-identity
changes: it required the full resolution to run again but made only a
`(principal_id, signer_key_id)` difference dispositive. Its v1.3 text is
the minimum additive clarification needed to make the required
post-touch comparison cover the authority state actually resolved and
used. The implementation uses one frozen semantic snapshot containing
the complete resolved records and repository/root/provider context;
equality is by canonical field value. This detects record revocation,
relationship/profile change, binding rewrite, and credential-key or
metadata replacement without inventing record version fields or a new
subsystem.

**Contract delta:** version `1.2` → `1.3`; only HSCE-REQ-080 and
HSCE-REQ-083 are revised in place. Requirement identities remain exactly
`HSCE-REQ-001` through `HSCE-REQ-084`, sequential, with no addition,
removal, or renumbering. Model B, HSCE-REQ-084's non-required
`credential_identity()` disposition, non-resident FIDO2 enrollment,
provider possession proof, CLI grammar, error vocabulary, and evidence
publication mechanism are unchanged.

The two 2F.3 Blocking findings are **REPAIRED — INDEPENDENT VERIFICATION
PENDING — NOT CLOSED**. BF-1 and BF-2 retain their independently
confirmed-closed dispositions at the HATP trust-enrollment/signing
implementation boundary. The required next phase is
**149O.20L.7O.2F.5 — Durable-Registry Signer Cross-Record Consistency and
TOCTOU Repair Independent Verification**. This recommendation does not
authorize that phase, HMIC alignment, real provisioning, certification,
or activation.
