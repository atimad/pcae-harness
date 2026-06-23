# Multi-Agent Prompt Capture Storage Policy

## Purpose

Define where approved prompts, prompt hashes, invocation metadata, stdout/stderr captures, raw backend output, capture manifests, retention metadata, and review references are stored in a governed multi-agent lifecycle. The policy specifies what is allowed in git, what remains out-of-band or metadata-only, how hashes prove integrity, and how storage interacts with adoption review without inferring adoption authorization.

## Scope

Storage-policy documentation only. This artifact defines storage entities, location policies, retention rules, integrity checks, and naming conventions. It does not implement storage directories, create machine-readable manifests, modify `.gitignore`, or create executable files.

## Non-Goals

- Storage implementation in code.
- Filesystem layout implementation.
- Validator or parser implementation.
- CLI command implementation.
- Backend invocation or prompt sending.
- Output capture, intake, or adoption.
- Creation of `.pcae/captures/` directories.
- Creation of machine-readable manifest files.
- Creation of stdout/stderr files.
- Modification of `.gitignore`.
- Source code or test changes.

## Motivation from 83G, 84B, 84C, and 84H

### 83G — Capture Volatility

Phase 83G captured multi-agent outputs to `/tmp/pcae-83g-*`. These volatile paths are lost on reboot. The 83H intake phase verified the outputs existed but had no persistence guarantee. The 84A roadmap identified "PCAE-managed capture directory" (84I) as a MEDIUM priority to replace volatile `/tmp` storage.

### 84B — Prompt Package Schema

The prompt package schema (84B) defines `prompt_text_hash`, `prompt_text_storage_policy` (`inline`, `artifact_reference`, `external_file`), and `raw_output_storage_policy` (`external_volatile`, `pcae_managed`, `inline_artifact`). These fields need a concrete storage policy to bind to.

### 84C — Capture Metadata Schema

The capture metadata schema (84C) defines `stdout_path`, `stderr_path`, `stdout_storage_location`, `stderr_storage_location`, `raw_output_storage_policy`, `raw_output_repo_storage_allowed`, `raw_output_retention_policy`, and `metadata_only_in_repo`. These fields reference storage decisions that this policy defines.

### 84H — Guard Hardening

The guard hardening design (84H) requires `capture_metadata_required=true`, `mutation_guard_required=true`, and `metadata_only_repo_policy=true` as pre-invocation checks. The guard blocks invocation if no capture plan is configured, but does not define where captured output lives. This policy fills that gap.

---

## Storage Threat Model

| # | Threat | Risk | Mitigation |
|---|--------|------|-----------|
| T1 | Approved prompt text lost | Cannot verify what was sent | Store prompt hash in git-tracked metadata; prompt text in artifact or managed storage |
| T2 | Approved prompt modified after approval | Sent prompt differs from approved | SHA256 hash comparison at send time (84H guard); immutable-after-approval policy |
| T3 | Prompt hash mismatch | Integrity violation | Block invocation on mismatch; require reapproval |
| T4 | Raw backend output accidentally committed | Unapproved content enters repo | `raw_output_git_tracked_by_default=false`; raw output excluded from git add |
| T5 | stdout/stderr capture lost | Cannot verify what backend produced | PCAE-managed capture directory with retention policy; hash as fallback evidence |
| T6 | Capture metadata references missing file | Broken reference in manifest | Integrity check: metadata paths must resolve when status is `captured` |
| T7 | Capture metadata hash mismatch | Tampered or corrupted output | Re-hash file and compare; block intake on mismatch |
| T8 | Capture manifest overwritten | Loss of capture history | Append-safe or versioned manifests; overwrite blocked |
| T9 | Multiple backend outputs conflated | Wrong output attributed to wrong agent | Invocation-scoped paths: one directory per capture, one file per invocation |
| T10 | Adoption review uses wrong output | Adoption candidate references stale/wrong capture | Adoption references must include capture_id, invocation_id, and stdout_sha256 |
| T11 | Secret appears in backend output | Credential or sensitive data in stdout/stderr | Secret detection at intake; redaction before any git tracking; original preserved non-git |
| T12 | Sensitive raw output exposed in docs | Markdown artifact embeds raw output | Policy: raw output not embedded in docs by default; only metadata/hashes in docs |
| T13 | Retention undefined | Output accumulates indefinitely or is cleaned too early | Explicit retention classes with defined lifetimes |
| T14 | Failed capture evidence overwritten | Cannot audit what went wrong | Failed captures preserved with `failed_` prefix; overwrite blocked |
| T15 | Mutation evidence cleaned up too early | Cannot prove backend mutated repo | Quarantine evidence retained until lifecycle closure with human approval |

---

## Storage Design Principles

1. **Approved prompts are immutable after approval.** Once a prompt package is approved, the prompt text and its hash must not change. Any modification requires a new approval phase.
2. **Prompt hashes are canonical evidence.** The SHA256 hash of the approved prompt text is the primary integrity proof. If the text is lost but the hash survives, the integrity claim stands.
3. **Capture metadata is git-trackable when safe.** Metadata (hashes, line counts, byte counts, timestamps, return codes) may be committed to git. Raw output content must not be committed by default.
4. **Raw backend output is not automatically adopted.** Captured output is evidence, not approved content. It must go through intake, review, and approval before any adoption.
5. **Raw backend output should not be pasted into docs by default.** Docs may reference captures by hash and path, but must not embed raw output unless explicitly approved.
6. **stdout/stderr hashes are required.** Every captured output must have a SHA256 hash recorded at capture time.
7. **Capture manifests must be append-safe or versioned.** A manifest records capture history; overwriting a manifest loses history.
8. **Failed captures must be preserved.** Partial outputs, timeout outputs, and error outputs are evidence. They must not be deleted or overwritten.
9. **Metadata references must use repository-relative or policy-defined paths.** Absolute paths like `/tmp/pcae-83g-*` are fragile. Future storage should use policy-defined base paths.
10. **Storage policy must support offline audit.** An auditor with only the git repo and metadata should be able to verify what was approved, what was sent, and what was captured (via hashes, even if raw files are unavailable).
11. **Storage policy must not infer adoption authorization.** Storing output does not imply it is approved for adoption. Storage and adoption are independent governance domains.

---

## Storage Entity Model

| Entity | Description | Git-Tracked | Mutable |
|--------|-------------|-------------|---------|
| `prompt_package` | Approved prompt package artifact (84B schema) | yes (docs/) | immutable after approval |
| `approved_prompt` | Individual approved prompt text within a package | referenced in package artifact | immutable after approval |
| `prompt_hash` | SHA256 of approved prompt text | yes (in metadata) | immutable |
| `invocation_record` | Metadata about a single backend invocation | yes (in capture artifact or manifest) | append-only |
| `capture_manifest` | Index of all invocations and outputs for one capture | yes (metadata) | append-only or versioned |
| `stdout_capture` | Raw stdout file from backend invocation | no (external, PCAE-managed) | immutable after capture |
| `stderr_capture` | Raw stderr file from backend invocation | no (external, PCAE-managed) | immutable after capture |
| `raw_output_blob` | Any raw output file from a backend | no (external, PCAE-managed) | immutable after capture |
| `capture_metadata` | Structured metadata about captures (hashes, counts, timing) | yes (docs/ or .pcae/) | append-only |
| `intake_reference` | Reference from intake to specific capture and invocation | yes (in intake artifact) | immutable after intake |
| `adoption_candidate_reference` | Reference from adoption candidate to source output | yes (in adoption artifact) | immutable after approval |
| `retention_record` | Metadata about retention class, expiry, and cleanup | yes (in manifest or metadata) | updatable with audit trail |

---

## Prompt Storage Policy

| Field | Type | Description |
|-------|------|-------------|
| `prompt_id` | string | Unique prompt identifier within the package |
| `prompt_package_id` | string | Parent package identifier |
| `role_id` | string | Role this prompt targets |
| `agent_id` | string | Agent bound to this prompt |
| `approved_prompt_text_location` | string | Where the approved text lives: `artifact_reference` (markdown doc), `inline_package` (embedded in schema instance), `external_file` (managed file) |
| `approved_prompt_text_sha256` | string | SHA256 hash of the exact approved text |
| `approval_artifact` | string | Path to the approval artifact (e.g., 83F doc) |
| `approval_timestamp` | string | ISO timestamp when approval was granted |
| `prompt_status` | string | `draft`, `approved`, `sent`, `captured` |
| `prompt_mutability_policy` | string (always `immutable_after_approval`) | Prompt text must not change after approval |

### Prompt Text Location Options

| Location | Description | Pros | Cons |
|----------|-------------|------|------|
| `artifact_reference` | Prompt text lives in a markdown artifact (e.g., 83E dry-run doc) | Human-readable, git-tracked | Must extract text from markdown for hash comparison |
| `inline_package` | Prompt text embedded in a JSON/YAML schema instance | Machine-parseable, hashable directly | Large prompts make schema instances unwieldy |
| `external_file` | Prompt text in a PCAE-managed file (e.g., `.pcae/prompts/<id>.txt`) | Clean separation, easy to hash | Requires managed storage directory |

The current lifecycle (83A–83L) used `artifact_reference` (prompt text in `docs/MULTI_AGENT_PROMPT_PACKAGE_DRY_RUN.md`). Future lifecycles may use `external_file` once storage is implemented.

---

## Prompt Hash Policy

| Field | Type | Description |
|-------|------|-------------|
| `hash_algorithm` | string (always `sha256`) | Hash algorithm for all prompt integrity checks |
| `canonical_text_normalization_policy` | string | `none` (hash exact bytes) or `utf8_strip_trailing_newline` |
| `approved_prompt_text_hash` | string | SHA256 recorded at approval time |
| `pre_send_extracted_prompt_hash` | string | SHA256 computed at send time from extracted text |
| `hash_match_required` | boolean (always true) | Whether hash match is enforced |
| `hash_mismatch_action` | string (always `block_invocation`) | Action when hashes differ |
| `prompt_change_requires_new_approval` | boolean (always true) | Any text change requires new approval phase |

### Normalization Recommendation

The recommended normalization policy is `none` — hash the exact bytes of the approved prompt text. This avoids ambiguity about which whitespace transformations are permitted. If a future phase requires normalization (e.g., stripping a trailing newline added by text editors), it must be explicitly documented and the normalized form must be the canonical hashed form.

---

## Invocation Metadata Storage Policy

| Field | Type | Description |
|-------|------|-------------|
| `invocation_id` | string | Unique invocation identifier |
| `contract_id` | string | Contract under which invocation occurs |
| `prompt_package_id` | string | Prompt package for this invocation |
| `prompt_id` | string | Specific prompt sent |
| `agent_id` | string | Agent that was invoked |
| `role_id` | string | Role the agent served |
| `backend_command` | string | Exact command invoked |
| `backend_args` | list[string] | Exact args passed |
| `wrapper_path` | string/null | Wrapper script path if applicable |
| `started_at` | string | ISO timestamp of invocation start |
| `completed_at` | string/null | ISO timestamp of completion |
| `duration_seconds` | number | Wall-clock duration |
| `return_code` | integer/null | Process return code |
| `timeout_status` | string | `completed`, `timed_out` |
| `guard_decision_id` | string/null | Reference to the guard decision that approved this invocation |

### Invocation Metadata Storage Location

Invocation metadata is git-trackable. It contains no raw output content — only identifiers, timestamps, and status codes. It may be stored in:

- A human-readable capture artifact in `docs/` (current approach, e.g., `docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md`).
- A machine-readable record in `.pcae/captures/<capture_id>/metadata.json` (proposed future approach).

Both locations are acceptable. The human-readable artifact is the primary record until machine-readable storage is implemented.

---

## stdout/stderr Capture Storage Policy

| Field | Type | Description |
|-------|------|-------------|
| `stdout_path` | string | Path to captured stdout file |
| `stderr_path` | string | Path to captured stderr file |
| `stdout_sha256` | string | SHA256 of stdout file content |
| `stderr_sha256` | string | SHA256 of stderr file content |
| `stdout_line_count` | integer | Line count of stdout |
| `stderr_line_count` | integer | Line count of stderr |
| `stdout_byte_count` | integer | Byte count of stdout |
| `stderr_byte_count` | integer | Byte count of stderr |
| `stdout_storage_class` | string | `external_volatile`, `pcae_managed`, `metadata_only` |
| `stderr_storage_class` | string | `external_volatile`, `pcae_managed`, `metadata_only` |
| `capture_required` | boolean (always true) | stdout/stderr capture is mandatory |

### Storage Classes

| Class | Description | Git-Tracked | Persistent | Used When |
|-------|-------------|-------------|------------|-----------|
| `external_volatile` | Raw files in `/tmp` or similar volatile path | no | no (lost on reboot) | Current approach (83G); legacy only |
| `pcae_managed` | Raw files in `.pcae/captures/<capture_id>/` | no (gitignored) | yes (until cleanup) | Proposed future approach |
| `metadata_only` | Only hashes/counts recorded; raw file not retained | metadata yes | raw file no | When raw output is no longer needed and hash suffices |

The recommended default for future lifecycles is `pcae_managed`. The `external_volatile` class remains valid for backward compatibility with the 83G lifecycle.

---

## Raw Backend Output Policy

| Field | Type | Description |
|-------|------|-------------|
| `raw_output_storage_allowed` | boolean (always true) | Raw output may be stored (but not in git by default) |
| `raw_output_git_tracked_by_default` | boolean (always false) | Raw output files are not committed to git |
| `raw_output_metadata_git_tracked` | boolean (always true) | Metadata about raw output (hashes, counts) is committed |
| `raw_output_adoption_forbidden_by_default` | boolean (always true) | Raw output is not adopted content until explicitly approved |
| `raw_output_review_reference_required` | boolean (always true) | Adoption review must reference raw output by capture_id and hash |
| `raw_output_redaction_policy` | string | `redact_secrets_before_any_tracking`, `preserve_original_non_git` |
| `raw_output_retention_policy` | string | Retention class from retention policy |

### Why Raw Output Must Not Be Git-Tracked by Default

1. **Size:** Backend outputs can be large (thousands of lines). Committing raw output bloats the repo.
2. **Secrets:** Backend output may contain secrets, credentials, or sensitive data despite prompt constraints.
3. **Adoption confusion:** Git-tracked raw output may be mistaken for adopted content.
4. **Immutability:** Once committed, raw output is in git history permanently (hard to redact).
5. **Governance boundary:** Raw output is evidence, not approved content. The governance boundary between "captured" and "adopted" must remain clear.

---

## Capture Manifest Policy

| Field | Type | Description |
|-------|------|-------------|
| `capture_manifest_id` | string | Unique manifest identifier |
| `capture_manifest_version` | string | Manifest format version |
| `contract_id` | string | Contract ID |
| `prompt_package_id` | string | Prompt package ID |
| `capture_id` | string | Capture session ID |
| `invocation_ids` | list[string] | All invocations in this capture |
| `capture_metadata_path` | string | Path to the capture metadata document |
| `raw_output_paths` | list[object] | List of `{invocation_id, stdout_path, stderr_path}` |
| `hashes` | list[object] | List of `{invocation_id, stdout_sha256, stderr_sha256}` |
| `retention_class` | string | Retention class for this capture |
| `created_at` | string | ISO timestamp |
| `status` | string | `active`, `intaked`, `closed`, `failed` |

### Manifest Mutability

- Manifests are **append-safe**: new invocation records may be appended, but existing records must not be modified.
- Manifests may be **versioned**: if a manifest needs correction, a new version is created alongside the original.
- **Overwrite is blocked**: replacing a manifest file without versioning is forbidden.

### Manifest Storage Location

- Human-readable manifests live in `docs/` (current approach: `docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md`).
- Machine-readable manifests are proposed at `.pcae/captures/<capture_id>/manifest.json` (future implementation).
- Both may coexist: the human-readable doc is the primary record; the machine-readable file enables automation.

---

## Git-Tracked Versus Non-Git Storage Policy

### Git-Tracked (docs/)

| Category | Examples | Rationale |
|----------|---------|-----------|
| Policy artifacts | This document, schema docs, guard design | Human-readable governance documentation |
| Capture metadata summaries | `docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md` | Hashes, counts, timestamps — no raw output |
| Intake artifacts | `docs/MULTI_AGENT_OUTPUT_INTAKE.md` | Classification results and finding summaries |
| Adoption artifacts | Review, approval, execution docs | Governance decision records |
| Lifecycle artifacts | State machine, command design, lessons | Design documentation |

### Git-Tracked (metadata in .pcae/)

| Category | Examples | Rationale |
|----------|---------|-----------|
| Capture manifests (metadata only) | `.pcae/captures/<id>/manifest.json` | Machine-readable index of captures; contains paths and hashes, not content |
| Invocation records | `.pcae/captures/<id>/metadata.json` | Invocation timing, return codes, guard decisions |
| Retention records | `.pcae/captures/<id>/retention.json` | Retention class, expiry, cleanup status |

### Non-Git (raw output, external)

| Category | Examples | Rationale |
|----------|---------|-----------|
| Raw stdout files | `.pcae/captures/<id>/stdout.txt` | Large, may contain secrets, not adopted content |
| Raw stderr files | `.pcae/captures/<id>/stderr.txt` | May contain error details or secrets |
| Failed capture partial output | `.pcae/captures/<id>/failed_stdout.txt` | Evidence of failure, not adopted content |
| Quarantine evidence | `.pcae/captures/<id>/quarantine/` | Mutation evidence, must be preserved non-git |

### Non-Git (sensitive)

| Category | Examples | Rationale |
|----------|---------|-----------|
| Secret-containing output | Any raw output flagged by secret detection | Must never be committed; redacted copy may be tracked |
| Pre-redaction originals | Original file before redaction | Preserved for audit but never committed |

### Gitignore Policy

Raw output files should be gitignored when PCAE-managed storage is implemented. Proposed gitignore entries (design only — do not modify `.gitignore` in this phase):

```
.pcae/captures/*/stdout.txt
.pcae/captures/*/stderr.txt
.pcae/captures/*/failed_*.txt
.pcae/captures/*/quarantine/
```

### Artifact Reference Policy

- Git-tracked documents may reference non-git files by path and hash.
- References must include `capture_id`, `invocation_id`, and hash.
- References must not embed raw output content unless explicitly approved.
- If a referenced file is unavailable, the hash serves as integrity evidence.

---

## Proposed Path Conventions

These are design proposals only. No directories are created in this phase.

| Entity | Proposed Path | Git-Tracked |
|--------|--------------|-------------|
| Policy/schema docs | `docs/MULTI_AGENT_*.md` | yes |
| Capture metadata (human) | `docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md` | yes |
| Capture manifest (machine) | `.pcae/captures/<capture_id>/manifest.json` | yes (metadata only) |
| Invocation metadata (machine) | `.pcae/captures/<capture_id>/metadata.json` | yes |
| Retention record | `.pcae/captures/<capture_id>/retention.json` | yes |
| Raw stdout | `.pcae/captures/<capture_id>/<invocation_id>-stdout.txt` | no (gitignored) |
| Raw stderr | `.pcae/captures/<capture_id>/<invocation_id>-stderr.txt` | no (gitignored) |
| Failed output | `.pcae/captures/<capture_id>/failed_<invocation_id>-stdout.txt` | no (gitignored) |
| Quarantine evidence | `.pcae/captures/<capture_id>/quarantine/<filename>` | no (gitignored) |
| Approved prompt text (future) | `.pcae/prompts/<prompt_package_id>/<prompt_id>.txt` | optional |

### Capture ID Convention

Proposed format: `CAPTURE-<CONTRACT_SHORT>-<PHASE>-<SEQ>`

Example: `CAPTURE-DRY-RUN-001-83G-001`

### Invocation ID Convention

Proposed format: `inv-<role>-<seq>`

Example: `inv-planner-001`, `inv-reviewer-001`

---

## Retention Policy

| Field | Type | Description |
|-------|------|-------------|
| `retention_class` | string | Category of retention |
| `retain_until` | string | Condition or date for retention end |
| `retain_reason` | string | Why this data is retained |
| `failed_capture_retention` | string | Policy for failed/partial captures |
| `quarantine_retention` | string | Policy for quarantine evidence |
| `deletion_requires_approval` | boolean (always true) | Deletion requires human approval |
| `redaction_requires_record` | boolean (always true) | Redaction must be recorded |
| `raw_output_cleanup_policy` | string | When and how raw output is cleaned up |

### Retention Classes

| Class | Retain Until | Applies To |
|-------|-------------|-----------|
| `lifecycle_active` | Lifecycle closure | Active capture output, manifests |
| `post_lifecycle_audit` | Explicit human cleanup approval | Closed lifecycle evidence |
| `failed_capture` | Human review and explicit cleanup | Failed/partial capture output |
| `quarantine` | Human review, quarantine resolution, and explicit cleanup | Mutation evidence, suspicious output |
| `secret_evidence` | Human review, redaction complete, explicit cleanup | Output containing detected secrets |
| `metadata_permanent` | Indefinite (in git) | Hashes, counts, timestamps in git-tracked metadata |

### Cleanup Rules

1. Raw output files may be cleaned up after lifecycle closure and explicit human approval.
2. Cleanup must record what was deleted, when, by whom, and the hash of the deleted file.
3. Metadata (hashes, counts) must not be deleted even when raw files are cleaned up.
4. Failed capture output must not be cleaned up until human review.
5. Quarantine evidence must not be cleaned up until quarantine resolution and human approval.
6. Secret-containing output must not be cleaned up until redaction is complete and recorded.

---

## Redaction and Secret-Handling Policy

| Field | Type | Description |
|-------|------|-------------|
| `secret_detection_required` | boolean (always true) | Secret scan must run at intake |
| `secret_found_action` | string | `block_git_tracking`, `redact_and_record`, `quarantine` |
| `redacted_copy_policy` | string | Redacted copy may be git-tracked if safe |
| `original_evidence_policy` | string | Original preserved non-git until human review |
| `human_review_required` | boolean (always true) | Human must review any secret detection |
| `do_not_commit_secret_output` | boolean (always true) | Raw output with secrets must never be committed |
| `hash_after_redaction_policy` | string | Record both pre-redaction hash (original) and post-redaction hash (redacted copy) |

### Secret Detection Scope

Secret detection should check for:

- API keys, tokens, passwords in stdout/stderr content.
- Credential file paths or content.
- Environment variable values that appear to be secrets.
- Private key material.
- Database connection strings with credentials.

### Redaction Workflow

1. Intake phase runs secret detection on captured output.
2. If secrets found: flag output, block git tracking of raw file.
3. Create redacted copy with secrets replaced by `[REDACTED]` markers.
4. Record pre-redaction hash (original file) and post-redaction hash (redacted file).
5. Original file preserved in non-git managed storage.
6. Redacted copy may be referenced in git-tracked metadata.
7. Human must review before any further processing.

---

## Adoption Review Reference Policy

| Field | Type | Description |
|-------|------|-------------|
| `adoption_review_may_reference_capture_metadata` | boolean (always true) | Adoption review may cite capture metadata |
| `adoption_review_may_reference_hashes` | boolean (always true) | Adoption review may cite output hashes |
| `adoption_review_must_not_embed_raw_output_by_default` | boolean (always true) | Adoption review docs must not paste raw output |
| `adoption_candidate_must_reference_source_output_id` | boolean (always true) | Candidates must cite invocation_id and stdout_sha256 |
| `adoption_execution_must_not_copy_raw_output_without_approval` | boolean (always true) | Execution must not copy-paste raw output without explicit approval |

### Reference Chain

The adoption reference chain ensures traceability:

```
adoption_candidate → intake_finding → capture_invocation → prompt_package → approval
       ↓                    ↓                  ↓                  ↓            ↓
  candidate_id         finding_id        invocation_id      prompt_id    approval_artifact
  source_output_id     capture_id        stdout_sha256      prompt_hash
```

Every adoption candidate must trace back to a specific invocation and its captured output hash. This chain must be verifiable from git-tracked metadata alone (hashes), even if raw output files are unavailable.

---

## Integrity Verification Policy

| Field | Type | Description |
|-------|------|-------------|
| `prompt_hash_verified` | boolean | Approved prompt hash matches stored hash |
| `stdout_hash_verified` | boolean | stdout file hash matches metadata hash |
| `stderr_hash_verified` | boolean | stderr file hash matches metadata hash |
| `manifest_hash_verified` | boolean | Manifest content is consistent with invocation records |
| `metadata_references_resolvable` | boolean | All path references in metadata point to existing files |
| `capture_id_consistent` | boolean | Capture ID is consistent across all related records |
| `prompt_package_id_consistent` | boolean | Package ID is consistent across all related records |
| `contract_id_consistent` | boolean | Contract ID is consistent across all related records |
| `verification_failure_action` | string | `block_intake`, `block_adoption`, `require_human_review` |

### Verification Levels

| Level | When Run | What Is Checked |
|-------|----------|----------------|
| `pre_send` | Before prompt is sent | Prompt hash matches approved package |
| `post_capture` | After backend invocation | stdout/stderr hashes recorded, files exist |
| `pre_intake` | Before intake classification | All capture metadata present, hashes match files |
| `pre_adoption_review` | Before adoption review | Capture metadata references valid, hashes match |
| `audit` | On demand | Full chain: prompt → capture → intake → adoption references consistent |

### Offline Audit Capability

An auditor with only the git repository should be able to:

1. Read the approved prompt package and its prompt hashes.
2. Read the capture metadata with stdout/stderr hashes, line/byte counts, return codes.
3. Read the intake classification results.
4. Read the adoption review with candidate references.
5. Verify the hash chain: prompt_hash → capture_hash → intake_reference → adoption_reference.
6. Determine whether raw output files existed (from metadata), even if the files are no longer available.

---

## Failure and Recovery Policy

| # | Failure | Detection | Recovery |
|---|---------|-----------|----------|
| 1 | Missing prompt text | `approved_prompt_text_location` resolves to nothing | Reconstruct from artifact if possible; hash serves as evidence |
| 2 | Missing prompt hash | `approved_prompt_text_sha256` is null | Block invocation; prompt package is invalid without hash |
| 3 | Missing manifest | Capture manifest file does not exist | Reconstruct from capture artifact if available; flag incomplete |
| 4 | Missing stdout | `stdout_path` does not resolve | Hash in metadata serves as evidence; flag `capture_storage_missing` |
| 5 | Missing stderr | `stderr_path` does not resolve | Hash in metadata serves as evidence; flag `capture_storage_missing` |
| 6 | Hash mismatch (prompt) | Pre-send hash ≠ approved hash | Block invocation; require reapproval |
| 7 | Hash mismatch (stdout) | Re-hash of file ≠ metadata hash | Block intake; quarantine output |
| 8 | Hash mismatch (stderr) | Re-hash of file ≠ metadata hash | Block intake; quarantine output |
| 9 | Raw output missing at intake | Volatile storage lost before intake | Rely on metadata hashes; flag `capture_storage_missing`; intake proceeds with hash-only evidence if explicitly approved |
| 10 | Secret detected | Secret scan flags content | Block git tracking; create redacted copy; preserve original non-git |
| 11 | Capture storage corrupt | File exists but content corrupted | Hash mismatch detection; quarantine; require recapture or explicit closure |
| 12 | Failed capture preservation | Failed capture output at risk of deletion | `failed_capture_retention` class; overwrite blocked; human review required before cleanup |
| 13 | Recovery requires human review | Any unresolvable storage failure | Human must decide: recapture, close with evidence, or accept hash-only |

---

## Example Storage Manifest

Based on the 83G capture (MULTI-AGENT-DRY-RUN-001), illustrative only:

```json
{
  "capture_manifest_id": "CAPTURE-DRY-RUN-001-83G-001",
  "capture_manifest_version": "0.1",
  "contract_id": "MULTI-AGENT-DRY-RUN-001",
  "prompt_package_id": "MULTI-AGENT-PROMPT-PACKAGE-DRY-RUN-001",
  "capture_id": "MULTI-AGENT-CAPTURE-83G-001",
  "capture_metadata_path": "docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md",
  "created_at": "2026-06-23T18:08:00Z",
  "status": "closed",
  "retention_class": "post_lifecycle_audit",
  "invocation_ids": ["inv-planner-001", "inv-reviewer-001"],
  "raw_output_paths": [
    {
      "invocation_id": "inv-planner-001",
      "stdout_path": "/tmp/pcae-83g-planner-stdout.txt",
      "stderr_path": "/tmp/pcae-83g-planner-stderr.txt",
      "storage_class": "external_volatile"
    },
    {
      "invocation_id": "inv-reviewer-001",
      "stdout_path": "/tmp/pcae-83g-reviewer-stdout.txt",
      "stderr_path": "/tmp/pcae-83g-reviewer-stderr.txt",
      "storage_class": "external_volatile"
    }
  ],
  "hashes": [
    {
      "invocation_id": "inv-planner-001",
      "stdout_sha256": "7eea6c4c41c5f6eb24ce3d543ec6aaa2741c36a038167507ede4734c53dea492",
      "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
      "stdout_line_count": 159,
      "stdout_byte_count": 11263,
      "stderr_line_count": 1,
      "stderr_byte_count": 157
    },
    {
      "invocation_id": "inv-reviewer-001",
      "stdout_sha256": "f821b0e3771cc7763eb7725cdca6d10a8c2665766dea26f2862d1391aab064c3",
      "stderr_sha256": "e705bbf8982385da2b1a03725921d0a6c6730bbaadd22c8f9168522573d067e0",
      "stdout_line_count": 330,
      "stdout_byte_count": 20491,
      "stderr_line_count": 1,
      "stderr_byte_count": 157
    }
  ]
}
```

This is an illustrative manifest only. No machine-readable manifest file is created in 84I.

---

## Validation Rules

| # | Rule ID | Description |
|---|---------|-------------|
| 1 | `STORE_PROMPT_LOCATION_RECORDED` | Approved prompt text location must be recorded in package |
| 2 | `STORE_PROMPT_HASH_RECORDED` | Approved prompt SHA256 hash must be recorded in package |
| 3 | `STORE_PROMPT_HASH_VERIFIED_PRE_SEND` | Prompt hash must be verified before send (84H guard) |
| 4 | `STORE_PROMPT_CHANGE_REAPPROVAL` | Any prompt text change requires new approval |
| 5 | `STORE_STDOUT_PATH_RECORDED` | stdout file path must be recorded in capture metadata |
| 6 | `STORE_STDERR_PATH_RECORDED` | stderr file path must be recorded in capture metadata |
| 7 | `STORE_STDOUT_HASH_RECORDED` | stdout SHA256 hash must be recorded at capture time |
| 8 | `STORE_STDERR_HASH_RECORDED` | stderr SHA256 hash must be recorded at capture time |
| 9 | `STORE_STDOUT_COUNTS_RECORDED` | stdout line count and byte count must be recorded |
| 10 | `STORE_STDERR_COUNTS_RECORDED` | stderr line count and byte count must be recorded |
| 11 | `STORE_MANIFEST_REFERENCES_ALL` | Capture manifest must reference all invocations in the capture |
| 12 | `STORE_MANIFEST_REFS_RESOLVE` | Manifest path references must resolve when status is `captured` or `active` |
| 13 | `STORE_RAW_NOT_ADOPTED_DEFAULT` | Raw backend output is not adopted content by default |
| 14 | `STORE_RAW_NOT_COMMITTED_DEFAULT` | Raw backend output files are not committed to git by default |
| 15 | `STORE_SECRET_NOT_COMMITTED` | Output containing detected secrets must never be committed to git |
| 16 | `STORE_FAILED_PRESERVED` | Failed capture output must be preserved until human review |
| 17 | `STORE_QUARANTINE_PRESERVED` | Quarantine evidence must be preserved until resolution and human approval |
| 18 | `STORE_RETENTION_CLASS_REQUIRED` | Every capture must have an assigned retention class |
| 19 | `STORE_REDACTION_RECORDED` | Redaction must record pre-redaction hash, post-redaction hash, and redaction reason |
| 20 | `STORE_ADOPTION_REF_HASHES` | Adoption review references must include capture_id, invocation_id, and stdout_sha256 |
| 21 | `STORE_ADOPTION_NO_RAW_COPY` | Adoption execution must not copy raw output without explicit approval |
| 22 | `STORE_METADATA_GIT_TRACKABLE` | Capture metadata (hashes, counts, timestamps) may be committed to git |
| 23 | `STORE_RAW_SENSITIVE_NON_GIT` | Raw output flagged as sensitive must remain outside git |
| 24 | `STORE_MISSING_HASH_BLOCKS` | Missing hash blocks verification at any downstream stage |
| 25 | `STORE_HASH_MISMATCH_BLOCKS` | Hash mismatch blocks intake and adoption |
| 26 | `STORE_NO_INVOCATION_AUTH` | Storage policy does not authorize backend invocation |
| 27 | `STORE_NO_ADOPTION_AUTH` | Storage policy does not authorize adoption |
| 28 | `STORE_NO_COMMIT_AUTH` | Storage policy does not authorize commits of adopted content |
| 29 | `STORE_NO_PUSH_AUTH` | Storage policy does not authorize pushes |
| 30 | `STORE_PATHS_PROPOSALS_ONLY` | Proposed storage paths are design proposals until implemented |
| 31 | `STORE_NO_STORAGE_CREATED` | No machine-readable storage is created in this policy phase |
| 32 | `STORE_MANIFEST_APPEND_SAFE` | Manifests must be append-safe or versioned; overwrite is blocked |
| 33 | `STORE_DELETION_REQUIRES_APPROVAL` | Deletion of any capture data requires human approval |
| 34 | `STORE_CLEANUP_RECORDS_HASH` | Cleanup must record the hash of the deleted file |
| 35 | `STORE_OFFLINE_AUDIT_POSSIBLE` | Git-tracked metadata must be sufficient for offline audit of integrity chain |

**35 validation rules.**

---

## Failure Cases

| # | Failure | Detection | Handling |
|---|---------|-----------|----------|
| 1 | Approved prompt missing | Prompt text location resolves to nothing | Hash as evidence; reconstruct from artifact if possible |
| 2 | Approved prompt hash missing | `approved_prompt_text_sha256` is null | Block invocation; prompt package invalid |
| 3 | Prompt hash mismatch | Pre-send hash ≠ approved hash | Block invocation; require reapproval |
| 4 | Capture manifest missing | Manifest file does not exist | Reconstruct from capture artifact; flag incomplete |
| 5 | Capture manifest overwritten | Manifest replaced without versioning | Audit failure; require manifest recovery |
| 6 | stdout file missing | `stdout_path` does not resolve | Hash in metadata as evidence; flag `capture_storage_missing` |
| 7 | stderr file missing | `stderr_path` does not resolve | Hash in metadata as evidence; flag `capture_storage_missing` |
| 8 | stdout hash mismatch | Re-hash ≠ metadata hash | Block intake; quarantine output |
| 9 | stderr hash mismatch | Re-hash ≠ metadata hash | Block intake; quarantine output |
| 10 | Raw output accidentally committed | Raw output file appears in git diff | Revert commit; remove from git history if needed |
| 11 | Secret found in raw output | Secret scan detects credentials/keys | Block git tracking; redact and record; preserve original non-git |
| 12 | Capture metadata references missing path | Path in metadata does not resolve | Flag broken reference; hash as fallback evidence |
| 13 | Retention class missing | Capture has no retention class | Block cleanup; assign retention class |
| 14 | Redaction performed without record | Redacted file exists without pre/post hash record | Audit failure; require redaction record |
| 15 | Failed capture overwritten | Failed output file replaced | Evidence loss; require recovery or explicit closure |
| 16 | Quarantine evidence deleted | Quarantine files removed before resolution | Evidence loss; block quarantine closure |
| 17 | Adoption review references wrong output | Candidate references different invocation_id or hash | Block adoption; correct references |
| 18 | Adoption execution copies raw output without approval | Raw backend text pasted into target file without approval | Block commit; require explicit raw-output-copy approval |

**18 failure cases.**

---

## Storage Policy Status

| Field | Value |
|-------|-------|
| storage_policy_name | multi_agent_prompt_capture_storage_policy |
| storage_policy_version | 0.1 |
| storage_policy_status | draft_documented |
| storage_policy_implementation_status | not_started |

## Recommended Next Phase

**84J — Multi-Agent Deferred Item Tracker**

84J should document a deferred-item tracking policy for DF-* items, blocked automation work, future schema implementation, and unresolved governance improvements, still without implementing storage unless separately scoped.
