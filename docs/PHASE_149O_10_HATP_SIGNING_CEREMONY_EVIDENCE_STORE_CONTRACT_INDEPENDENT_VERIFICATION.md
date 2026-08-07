# Phase 149O.10 — HATP Signing Ceremony + Evidence Store Contract Independent Verification

**Phase type:** independent contract verification only. No production
implementation, no HATP-001/RAE-001/HSCE-001 amendment, no CLI
implementation, no hardware provisioning, no signing execution, no
Permission Broker change, no rollback dispatch behavior change.

## 0. Baseline (confirmed at phase start)

- Repository clean at phase start except this phase's own task-lifecycle
  bootstrap transition (idle → 149O.10); `origin/main..HEAD` = 0.
- Latest completed phase: 149O.9 (HATP Signing Ceremony + Evidence Store
  Contract Freeze) — `status: completed`, `report completeness:
  complete`, pushed, report consistency `consistent`.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy /
  passed / coherent.
- `pcae doctor task-memory`: pre-existing warnings only (a stale
  duplicate `tasks/active/*post-149o-6*.md` file and several
  `tasks/done/` entries missing from `tasks/DONE.md`), unrelated to and
  not introduced by this phase; not remediated here (out of this
  phase's allowed-file scope, matching 149O.9's own disposition of the
  identical pre-existing warnings).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed / observe / unavailable`, Permission
  Broker `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.9`: confirmed 149O.9 completed/complete/pushed,
  reconciliation returned `reconciled` (inspection-only, no mutation).
- Separately, during this session's bootstrap, a pre-existing latent
  defect was found in `pcae session bootstrap`'s own readiness
  classifier (`src/pcae/commands/session.py`, see §12 below) and a
  narrow repair task was planned (not implemented) for a future phase.
  This is unrelated to HSCE-001 and does not affect this phase's
  verification scope.

## 1. Scope Recap

149O.9 froze HSCE-001 v1.0 and explicitly deferred independent
verification to this phase (HSCE-001 §43, HSCE-REQ-076/079). This phase
attacks HSCE-001's own §38 mandatory attack matrix (20 items),
re-derives the requirement inventory independently from the contract
text itself, re-confirms the AG5/AG3 CLI entry-point inventory against
the current source tree, cross-checks HATP-001/RAE-001 compatibility,
and determines a contract-verification verdict. It does not implement
`pcae hatp sign rollback`, does not touch `src/pcae/**`, and does not
modify HSCE-001, HATP-001, or RAE-001.

## 2. Requirement Inventory — Independent Re-Derivation

Independent regex extraction of every `HSCE-REQ-###` token in
`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`
(not trusting 149O.9's own summary) finds:

- **79 requirements**, `HSCE-REQ-001` through `HSCE-REQ-079`,
  sequential, no gaps, no duplicates.

**Finding F-1 (NON-BLOCKING, editorial).** HSCE-REQ-078 itself states:
*"This contract defines requirements `HSCE-REQ-001` through
`HSCE-REQ-078` inclusive (this requirement), sequential, no gaps, no
duplicates."* This is off by one: `HSCE-REQ-079` exists immediately
afterward, in §40 (Blocking-Condition Check). The contract's own
self-referential count is wrong by exactly one requirement. This does
not create any implementation ambiguity — the numbering itself remains
sequential, gapless, and duplicate-free 1..79 — it is a miscounted
closing statement only. Recommend a trivial future text correction
(change "078" to "079" and "this requirement" positioning) alongside
any other narrow contract touch-up; not itself worth a dedicated
repair phase.

## 3. HATP-001 Compatibility

Read HATP-001 v1.0 in full (979 lines). HSCE-001 §4 (HSCE-REQ-006-008)
claims: HATP-001 remains authoritative and unamended for proof shape,
canonical payload/digest, the 13-member closed verification-status
vocabulary, provider requirements, human presence, repository/
deployment binding, freshness, and RAE integration. Independently
confirmed:

- `HumanApprovalProvenanceProof` (`human_approval_trusted_provenance.py`
  lines 153-218) — unchanged shape, all fields match HATP-REQ-069.
- `HATPVerificationStatus` (lines 663-684) — exactly 13 members (`VALID,
  MISSING, MALFORMED, INVALID_SIGNATURE, UNKNOWN_SIGNER,
  UNAUTHORIZED_SIGNER, REVOKED_SIGNER, INVALID_ATTESTATION,
  USER_PRESENCE_NOT_PROVEN, WRONG_OPERATION, WRONG_REPOSITORY,
  WRONG_DEPLOYMENT, EXPIRED`), matching HATP-REQ-078 verbatim.
- `git diff HEAD~20 -- docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`
  is empty — unamended over the last 20 commits; the file's creation
  commit (`a278cd93`, Phase 149O.1B.3) is far back in a 4,156-commit
  history.
- No conflicting redefinition of proof shape, digest semantics,
  verification vocabulary, presence, binding, freshness, or provider
  trust anywhere in HSCE-001's text.

**Verdict: HATP-001 COMPATIBILITY — CONFIRMED, no conflict.**

## 4. RAE-001 Compatibility

HSCE-001 §4 (HSCE-REQ-007) claims RAE-001 remains authoritative,
unamended, for `RollbackApprovalBinding`'s shape/lifecycle, the RAE
evidence store, and the 24-hour freshness window (RAE-REQ-043).
Independently confirmed:

- `create_rollback_approval_binding` (`rollback_approval_evidence.py`)
  hard-rejects any `ttl_hours != 24` at runtime — the 24h window is not
  caller-overridable, matching RAE-REQ-043 exactly (also asserted by
  `tests/test_phase_149o_10_...py::
  test_rae_binding_ttl_is_frozen_at_24_hours_not_caller_overridable`).
- `git diff HEAD~20 -- docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`
  is empty — unamended (creation commit `ed0857f7`, Phase 149I).
- HSCE-001's evidence store (`.pcae/hatp-evidence/`) and RAE-001's
  evidence store (`.pcae/rollback-approval-evidence/`) are distinct,
  separately-rooted directories, never merged or cross-addressed (§16 of
  the governing prompt's own framing, HSCE-REQ-007 second sentence);
  confirmed by direct inspection — no code path in either module
  references the other's root.
- HSCE-001 derives Decision/Binding data from RAE via
  `list_bindings_with_keys()` (confirmed to exist,
  `RollbackApprovalEvidenceStore.list_bindings_with_keys`,
  `rollback_approval_evidence.py:708-735`) rather than redefining RAE
  semantics.

**Verdict: RAE-001 COMPATIBILITY — CONFIRMED, no conflict. HSCE-001 does
not make its own envelope authoritative over RAE Bindings.**

## 5. CLI Grammar Reconstruction

Independently reconstructed from HSCE-REQ-009-012: the entire command
surface is exactly

```
pcae hatp sign rollback --site {ag3|ag5} [--job-id <id> | --per-id <id>] [--json]
```

`--site` is a required, closed-choice flag (`ag3`|`ag5`, case-sensitive
lowercase); illegal combinations (ag3+`--per-id`, ag5+`--job-id`, both
IDs, neither ID, unknown site, duplicate flag) are all implicitly
rejected by the closed per-site locator requirement (HSCE-REQ-013,
HSCE-REQ-016) even though the contract does not enumerate every illegal
combination explicitly as a numbered table — a future implementation
following ordinary `argparse` mutually-exclusive-group conventions
closes this without ambiguity. No `--dry-run`, `--ecp-id`, `--provider`,
`--signer`, `--force`, `--overwrite`, `--output`,
`--decision-digest`, `--binding-digest`, `--repository-id`, or
`--signer-key-id` flag exists (HSCE-REQ-012, HSCE-REQ-016,
HSCE-REQ-017, HSCE-REQ-026) — independently confirmed absent from the
frozen grammar block itself
(`test_hsce_contract_defines_exactly_one_cli_command_family`).

**Verdict: CLI GRAMMAR — CONFIRMED, unambiguous.**

## 6. AG3 Operation Locator

HSCE-REQ-013: `--job-id` only; `original_commit_sha` read from the live
job record, never CLI-supplied. No production source contradicts this
(no `--original-commit-sha`-shaped flag exists anywhere in `cli.py`).

**Verdict: AG3 LOCATOR — CONFIRMED.**

## 7. AG5 Operation Locator and CLI Entry-Point Inventory (Independent Re-Confirmation)

Independent grep of `src/pcae/` (excluding `tests/`) for
`build_rollback_execution(` call sites, performed fresh this phase
(not reusing 149O.9's own inventory text), finds exactly **one**
production call site:

```
src/pcae/commands/agent.py:16259  run_rollback(args)
    -> build_rollback_execution(HarnessPath.cwd(), args.per_id, dry_run=args.dry_run)
```

registered as `pcae rollback --per-id <id> [--dry-run] [--json]`
(`src/pcae/cli.py:3035-3055`). No `hatp_evidence_id`/`hatp_proof`/
`hatp_evidence` argument is passed. `build_rollback_execution_pilot`
(`src/pcae/core/agent.py:27055`) is independently re-confirmed, by
reading its full body, to be a distinct function that does not call
`build_rollback_execution` — the name-collision false positive 149O.8
originally flagged and 149O.9 resolved remains correctly resolved.
HSCE-REQ-014/015's inventory table is **independently reconfirmed
accurate against the current source tree**, unchanged since 149O.9.

**Corrected framing beyond the contract's own text.** Independent
reading of `src/pcae/core/agent.py` finds that `build_rollback_execution`
(line 93952) and `execute_rollback` (line 5234) already carry optional,
keyword-only `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` parameters,
and a full `src/pcae/core/hatp_ag_authority.py` module (272 lines,
`resolve_ag3_gated_rollback_authority`/`resolve_ag5_gated_rollback_authority`)
already exists and is production-wired when those kwargs are supplied
(Phase 149O.6/Wave 7 work, predating this contract). HSCE-001's own
table (HSCE-REQ-014) already accounts for this precisely — its "HATP
params supplied?" column already anticipates such kwargs existing and
correctly states none are supplied by `run_rollback`. This is **not** a
contract defect; it is confirmation that HSCE-001's own inventory
language is precise enough to remain accurate even though more of the
gated-authority machinery exists than a casual "NOT IMPLEMENTED" gloss
might suggest. Independently reconfirmed dormant/unreachable from any
CLI command: zero string matches for `hatp sign`, `hatp_sign`,
`HATPSignedEvidenceEnvelope`, `hatp_evidence_id`, `hatp_proof`, or
`hatp_evidence` anywhere in `src/pcae/cli.py` or `src/pcae/commands/`.

`ecp_id` auto-derivation (HSCE-REQ-016): confirmed `ecp_id` is a field
already read from `PromotionExecutionRecord`-adjacent structures in
`core/agent.py` (e.g. lines 91374, 93174, 93988) — no CLI-level
`--ecp-id` flag exists anywhere.

**Verdict: AG5 LOCATOR / ENTRY-POINT INVENTORY — CONFIRMED, unchanged
and accurate against the current source tree.**

## 8. Proof Field-Source Table Verification

HSCE-REQ-018's closed table was independently checked field-by-field
against production source:

| Field | Contract claim | Independently confirmed |
|---|---|---|
| `proof_version` | Fixed `1`, no caller input | `_require_proof_version` rejects non-`1`/bool (`human_approval_trusted_provenance.py:384-396`) |
| `repository_id` | From `repository_identity.py`, no caller input | Confirmed no CLI flag; validated via `_require_repository_instance_id` |
| `decision_record_id/digest` | Live CHGR lookup via matched Binding | Confirmed no caller-digest flag exists |
| `binding_id/digest` | Live RAE Binding read | `list_bindings_with_keys()` confirmed to exist |
| `principal_id/signer_key_id` | Hardware credential exchange, cross-checked against `HATPTrustStore.production()` | `HATPTrustStore.production()` call confirmed at `hatp_ag_authority.py:124`; no `--signer` flag anywhere |
| `provider_profile` | Fixed to `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` resolution | Confirmed: function only resolves `HATP_HARDWARE_PROVIDER_V1`, never imports `TestHATPProofVerifierProvider` (`hatp_providers.py:353-391`) |
| `operation_reference` | Locator-only caller input; derived half always read live | Confirmed — `job_id`/`per_id` are the only locator inputs anywhere |
| `issued_at` | Internal clock only | `_canonical_timestamp_string` (millisecond UTC) confirmed as the sole rendering path |

**Observation (NON-BLOCKING).** `create_production_hardware_provider`'s
actual signature carries an additional `allow_piv_fallback: bool = False`
keyword parameter not mentioned by HSCE-REQ-022. This is a Python-level
implementation parameter, not a CLI flag or caller-facing input — no
security invariant is affected either way (PIV fallback, if invoked,
still resolves through the same production-only factory) — but the
contract does not say whether a `pcae hatp sign rollback`
implementation should pass `allow_piv_fallback=True`. Recorded as an
implementation-detail gap, not a security ambiguity.

**Verdict: PROOF FIELD-SOURCE TABLE — CONFIRMED, no user-typed security
field exists beyond the two closed-form locators.**

## 9. Envelope Schema, Version Domain, Provider-Assertion Encoding

- Closed 4-field schema (`evidence_version`, `evidence_id`, `proof`,
  `provider_assertion`) independently re-extracted from the contract's
  own fenced code block and asserted closed
  (`test_hsce_evidence_envelope_schema_is_closed_four_fields`).
- `evidence_version` bool-rejection: HSCE-REQ-033 claims the identical
  pattern `_require_proof_version` already uses. Independently
  confirmed: `_require_proof_version` checks
  `not isinstance(value, int) or isinstance(value, bool)` in one
  compound condition (`human_approval_trusted_provenance.py:392`) —
  functionally identical bool-exclusion-before-acceptance, though
  structured as one combined `if`, not two sequential checks as the
  contract's own prose ("independent... check") might imply to a
  literal reader. Not a defect — the combined condition achieves the
  same rejection for `True`/`False`, independently verified via
  `test_require_proof_version_rejects_bool_before_membership_check`.
- `provider_assertion` Base64 encoding: HSCE-REQ-034 specifies standard
  Base64 (`base64.b64encode`/`b64decode`) of `ProviderAssertion.evidence`
  (confirmed `evidence: bytes` field, `hatp_providers.py:266`) —
  precise, no ambiguity (RFC 4648 §4 named explicitly).
- Constructor/parser domain equivalence (HSCE-REQ-072) and immutability
  (HSCE-REQ-073) are stated as forward-looking SHALL requirements for a
  future typed-model implementation; nothing in the current source
  contradicts them since no such model exists yet.

**Verdict: ENVELOPE SCHEMA / VERSION DOMAIN / ENCODING — CONFIRMED.**

## 10. Evidence ID, Content-Addressing, Same-ID Collision Semantics

- `evidence_id = digest_hatp_proof_payload(proof)` — confirmed to exist
  exactly as named (`human_approval_trusted_provenance.py:604-610`),
  proof-payload-only, never the full envelope or `provider_assertion`
  (HSCE-REQ-036-038, independently re-asserted in the test suite).
- Same-`evidence_id`-different-`provider_assertion` case (HSCE-REQ-038):
  first-write-canonical, byte-compare, `evidence_conflict` on mismatch,
  never silent overwrite or "latest wins" — text is unambiguous on this
  point taken in isolation from the write-algorithm's actual
  concurrency safety (see §12 below, which is a distinct question: what
  the rule *says* versus whether the *frozen write algorithm* can
  actually guarantee it under concurrent writers).

**Verdict: CONTENT-ADDRESSING / SAME-ID SEMANTICS — the stated rule is
unambiguous prose; §12 below identifies a BLOCKING gap in whether the
frozen write algorithm can actually enforce it.**

## 11. Store Root, Path Validation, Symlink Analysis

- Store root frozen at `.pcae/hatp-evidence/`, layout
  `envelopes/{evidence_id}.json` — confirmed no such directory exists
  anywhere in the working tree today (`find` sweep, zero matches),
  confirming no evidence has ever been produced.
- Path traversal (HSCE-REQ-056): `evidence_id` validated as lowercase
  64-hex before any path construction — mirrors the existing
  `_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")`
  (`human_approval_trusted_provenance.py:86`), a real, already-used
  primitive — not a hypothetical reuse target. Rejects `../`, absolute
  paths, `\`, whitespace, uppercase, partial-length, and Unicode
  lookalikes by construction (a regex `fullmatch` against a closed
  character class admits none of these).
- Case aliasing (HSCE-REQ-059): lowercase-only, matches
  `hashlib.hexdigest()`'s own native lowercase convention — no
  case-insensitive lookup path exists anywhere to alias against.
- Destination-file symlink rejection (HSCE-REQ-057) and parent-directory
  symlink escape rejection (HSCE-REQ-058) are both explicitly, textually
  addressed — closing item 43 of the governing prompt (parent-directory
  symlink component), which many comparable contracts leave silent.

**Finding F-2 (NON-BLOCKING, precision gap).** HSCE-REQ-052 states
envelope persistence "SHALL use the identical temp-file-in-same-directory
+ fsync + `os.replace` technique
`rollback_approval_evidence.py::_write_atomic_json` already uses."
Independently reading that exact function
(`rollback_approval_evidence.py:561-580`) shows it contains **no
symlink check whatsoever** (`islink`/`O_NOFOLLOW`/`readlink` all
absent, confirmed by
`test_write_atomic_json_reused_by_hsce_has_no_symlink_check`). A future
implementation cannot literally reuse `_write_atomic_json` unmodified
and satisfy HSCE-REQ-057/058 — it must add symlink-rejection logic that
does not exist in the cited reuse target. HSCE-REQ-052's own "with one
addition" framing already anticipates *some* addition (the
compare-then-conditionally-accept logic, see §12), but does not name
the missing symlink check as a second necessary addition on top of the
literal reuse claim. Recommend the eventual implementation phase treat
"reuse `_write_atomic_json`" as reuse-in-spirit (same fsync/temp-file/
same-directory discipline), not reuse-by-direct-call, and recommend a
narrow future contract-text clarification alongside F-1/F-3.

**Verdict: STORE ROOT / PATH VALIDATION / SYMLINK — CONFIRMED for the
*rules stated*; F-2 recorded as a non-blocking reuse-precision gap.**

## 12. Atomic No-Clobber Write Algorithm — Concurrency Analysis (HIGH PRIORITY)

This is this phase's most significant independent finding.

**The frozen rule (HSCE-REQ-039, HSCE-REQ-052):** if
`envelopes/{evidence_id}.json` already exists at write time, compare
bytes; identical is idempotent success, different is `evidence_conflict`
— "the existence-and-compare check MUST happen first, and the atomic
rename is used only for the create-new-file case or the
verified-idempotent-identical case."

**Independent structural analysis of the literal algorithm this text
describes:**

1. Writer checks `path.exists()`.
2. If absent: writer builds a temp file in the same directory, writes,
   `fsync`s, then calls `os.replace(tmp, dest)`.
3. If present: writer reads the existing file, compares bytes against
   the freshly-canonicalized new envelope, and either no-ops
   (identical) or rejects (`evidence_conflict`, different).

This is a **check-then-act** pattern, not an atomically-exclusive
publish. `os.replace()` on POSIX (`rename(2)`) is **unconditional** — it
does not fail or no-op if the destination already exists; it silently
replaces it regardless of prior content. Consider two concurrent
writers, A and B, racing to persist envelopes for the same
`evidence_id` with **different** `provider_assertion` bytes (a
realistic scenario per HSCE-REQ-038's own example: two separate
hardware-touch attempts producing an identical proof payload but
distinct assertions):

- A calls `path.exists()` → `False`.
- B calls `path.exists()` → `False` (before A has written anything).
- A writes its temp file, `fsync`s, calls `os.replace()` → destination
  now holds A's envelope.
- B, having already observed "absent" in step 2 above, proceeds down
  the *same* "create-new-file" branch (§39/§52's own words: "the atomic
  rename is used only for the create-new-file case") and calls
  `os.replace()` unconditionally → **destination now silently holds
  B's envelope, with no comparison against A's, no `evidence_conflict`,
  no error.**

This directly violates **SC-7** ("Existing evidence can never be
silently overwritten... a same-ID conflicting write is always rejected,
never replaced") and contradicts HSCE-REQ-038/039(B)'s own stated
outcome for this exact scenario. The described "existence-and-compare
check MUST happen first" instruction does not, by itself, close the
race — a check followed by a separate unconditional replace is exactly
the TOCTOU pattern the check was meant to prevent, unless the
*replace itself* is conditioned atomically on the state the check
observed (which plain `os.replace` cannot do).

**This is not a hypothetical concern for this codebase specifically —
it is independently confirmed to already have surfaced as a real
design question once before, in the same file.**
`rollback_approval_evidence.py::_write_atomic_json` — the exact
function HSCE-REQ-052 says to reuse — has this identical
check-then-act shape (`path.exists()` raise-if-present, then
temp+fsync+`os.replace`) and is **only safe today because RAE-001's own
`create_rollback_approval_binding` additionally writes a *separate*,
genuinely atomic `creation-registry/{evidence_id}` marker file via
`os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)`
(`rollback_approval_evidence.py:664`,
`write_creation_registration`) — an exclusive-create primitive that
*does* fail atomically (`FileExistsError`) if a concurrent writer wins
the race. That second, genuinely-exclusive marker file is what RAE-001
actually relies on for collision-safety; `_write_atomic_json` alone
does not provide it.**

149O.8's own original architecture (§12, before HSCE-001 superseded it)
proposed exactly this same second guard for HATP evidence:
`creation-registry/{evidence_id}` marker file, `O_CREAT|O_EXCL`. HSCE-001
§20 (HSCE-REQ-042) explicitly *drops* this marker, reasoning: "no
equivalent bypass path exists for this store, because the envelope's
own identity IS the content it stores." That reasoning addresses a
different threat (an out-of-band write bypassing the normal creation
path entirely) — it does not address the concurrent-legitimate-writers
race this phase independently identified, which the dropped marker
happened to also close as a side effect.

**Finding F-3 (BLOCKING).** HSCE-REQ-052's frozen write algorithm, as
literally specified ("existence-and-compare check... atomic rename...
create-new-file case"), does not guarantee SC-7's no-clobber property
under concurrent writers with differing content for the same
`evidence_id`. This is exactly the class of gap §128 of the governing
prompt requires an explicit verdict on:

```
NO-CLOBBER PUBLICATION:
AMBIGUOUS / RACE-UNSAFE — BLOCKING
```

**Recommended narrow repair** (for a future 149O.10.1 contract-repair
phase, not performed here): amend HSCE-REQ-052 to require an
atomically-exclusive publish primitive for the create-new-file path —
either (a) write the temp file, then attempt `os.link(tmp, dest)`
(which itself atomically fails with `FileExistsError` if `dest` already
exists, closing the race the same way `write_creation_registration`
already does elsewhere in this repository) followed by unlinking the
temp name, or (b) reintroduce a `creation-registry/{evidence_id}`-style
`O_CREAT|O_EXCL` marker as the actual collision-detection mechanism,
with the envelope file itself written only after the marker succeeds.
Either closes the race using a primitive already proven, in production,
elsewhere in this exact codebase.

## 13. Closed-Schema Attacks (Duplicate Keys, Unknown Fields, Missing Fields, Wrong Types)

- Duplicate JSON keys (HSCE-REQ-053, §62): reuses
  `_reject_duplicate_keys`'s `object_pairs_hook` technique, confirmed to
  exist and actually be used via `json.loads(raw,
  object_pairs_hook=_reject_duplicate_keys)`
  (`human_approval_trusted_provenance.py:341-354`). Applies recursively
  at every JSON object nesting level (a property of
  `object_pairs_hook`, not something the contract needs to state
  separately) — closes both the outer envelope and the nested `proof`
  object in one pass.
- Unknown top-level field: closed-schema, four fields only, rejected
  (HSCE-REQ-032, §62).
- `evidence_version` other than integer `1` (including bool): rejected,
  `unsupported_envelope_version` (HSCE-REQ-033).
- Missing required field: rejected at parse (§62, implicit in any
  standard typed-model/dict-validation parse; the contract does not
  need to enumerate all four missing-field cases individually since the
  closed-field-set rule already covers it uniformly).
- Digest mismatch (`evidence_id` vs. recomputed
  `digest_hatp_proof_payload(proof)`): rejected,
  `evidence_id_digest_mismatch` (HSCE-REQ-062) — explicit, precise.

**Verdict: CLOSED-SCHEMA ATTACKS — CONFIRMED, all mandatory-matrix items
5-9 fully specified.**

## 14. Human Cancellation, Device Absence, TOCTOU, Missing Binding, ecp_id Resolution Failure

- Human cancellation (HSCE-REQ-029): `human_signing_cancelled`, exit 5,
  no evidence persisted, no approval/authority state mutated anywhere —
  explicit.
- Device absence (HSCE-REQ-028): `provider_unavailable`, exit 4, no
  software fallback — explicit.
- Missing Binding precondition (HSCE-REQ-021): `binding_unavailable`,
  exit 3, **before any hardware provider is invoked** — explicit
  ordering guarantee (precondition checked before touch), closing item
  72 of the governing prompt precisely.
- AG5 `ecp_id` resolution failure (HSCE-REQ-016, attack-matrix item 20):
  `operation_not_found`, exit 2 — explicit.
- TOCTOU / post-sign recheck (HSCE-REQ-069-070): Decision/Binding/
  operation state is captured once at proof-construction time and
  re-read before final persistence; any change discards the freshly
  produced assertion and persists nothing, failing
  `evidence_serialization_failure` — explicit, and correctly framed as
  a UX/audit-quality improvement layered on top of HATP-001's actual
  consumption-time re-verification security boundary (HSCE-REQ-070's
  own closing sentence), not a substitute for it.
- **Item 74 (AG3 `original_commit_sha` resolution failure) — OBSERVATION,
  NON-BLOCKING.** The mandatory 20-item attack matrix (§38) names the
  AG5 `ecp_id`-resolution-failure case explicitly (item 20) but has no
  literal AG3-analogous item for "job_id whose `original_commit_sha`
  cannot be resolved." The underlying semantics are not actually
  ambiguous — HSCE-REQ-018's field-source table already assigns
  `operation_not_found` uniformly to both sites' derived-half-lookup
  failures — so this is a matrix-completeness gap, not a semantic one.
  Recommend the same future narrow-repair phase add this as item 21 for
  matrix completeness, alongside F-1/F-2/F-3.
- **TOCTOU — signer/provider revocation during touch (item 78 of the
  governing prompt).** HSCE-001 does not require a pre-persist recheck
  of signer/provider revocation state; HSCE-REQ-070's own text
  explicitly defers this to HATP-001's consumption-time re-verification.
  This is a deliberate, correctly-classified deferral, not an omission —
  **NOT a finding.**

**Verdict: CANCELLATION / DEVICE-ABSENCE / TOCTOU / MISSING-BINDING /
ECP_ID-RESOLUTION — CONFIRMED fully specified, with one NON-BLOCKING
matrix-completeness observation (AG3 analogue of item 20).**

## 15. Error Vocabulary and Exit-Code Mapping

Independently re-extracted from HSCE-001 §22's own fenced blocks: 9
`EXIT_*` constants, 12 `error_type` table rows, each mapping to exactly
one exit code (no error_type maps to two codes, confirmed by table
construction — the mapping is a simple key→value table with 12 distinct
keys). Independently confirmed disjoint from `HATPVerificationStatus`'s
13-member vocabulary (zero string overlap) — the two closed vocabularies
are never conflated, matching HSCE-REQ-049. The exit-code-category
convention itself (many error types → few numeric exit classes) is
independently confirmed to be a real, already-used repository
convention: `decision_session.py::_EXIT_CODE_BY_ERROR_TYPE` maps 25
distinct `error_type` strings onto 7 exit-code constants
(`decision_session.py:156-183`), citing IWPC-001 §9/IWPC-REQ-050 in its
own source comment — HSCE-001's claim to be reusing this convention is
not fabricated precedent.

**Verdict: ERROR VOCABULARY / EXIT-CODE MAPPING — CONFIRMED, closed,
non-overlapping with HATP-001's vocabulary.**

## 16. Secret Handling, Authority Separation, Signing-vs-Execution

- No PIN/private-key material may appear in the envelope, CLI argument,
  environment variable, or logs (HSCE-REQ-050) — no code path exists
  today (no implementation) that could violate this; the constraint is
  correctly scoped as a forward SHALL for the future implementation.
- Signing success (exit 0) means exactly "envelope persisted," never
  approval/`ALLOW`/executed (HSCE-REQ-065-066) — explicit,
  unambiguous, and consistent with `pcae hatp sign rollback` never
  calling `execute_rollback`/`build_rollback_execution` (HSCE-REQ-067,
  reaffirming 149O.8 §14, not reopened).
- `pcae remote rollback approve` deprecation timeline (HSCE-REQ-074) is
  reaffirmed, not reopened, unmodified this phase.

**Verdict: SECRET HANDLING / AUTHORITY SEPARATION — CONFIRMED.**

## 17. Security Invariants SC-1 through SC-12

All twelve independently located in §37 by literal string match
(`test_hsce_security_invariants_sc1_through_sc12_present`), each backed
by a corresponding detailed section elsewhere in the contract (cross-
referenced in §5-§36 above). No invariant is asserted without
supporting detail; no invariant is contradicted by a detailed rule
elsewhere. **SC-7 in particular ("existing evidence can never be
silently overwritten") is the invariant F-3 (§12) shows the frozen
write algorithm does not yet mechanically guarantee** — the invariant
itself is correctly stated; the write algorithm meant to implement it
is not yet precise enough to deliver it under concurrency.

## 18. Mandatory 20-Item Attack Matrix — Independent Classification

| # | Attack | Contract disposition | Independent classification |
|---|---|---|---|
| 1 | `evidence_id` path traversal | Rejected before filesystem access (§25) | Fully specified |
| 2 | `evidence_id` uppercase hex | Rejected, no case-insensitive alias (§26) | Fully specified |
| 3 | Idempotent byte-identical re-write | Idempotent success (§19A) | Fully specified *for the stated rule*; see F-3 for write-path race |
| 4 | Conflicting re-write, differing bytes | `evidence_conflict`, no overwrite (§19B) | **Rule fully specified; enforcement mechanism is F-3 BLOCKING** |
| 5 | Duplicate top-level JSON key | Rejected at parse (§53, §62) | Fully specified |
| 6 | Unknown top-level field | Rejected, closed schema (§14, §62) | Fully specified |
| 7 | `evidence_version` non-`1` incl. bool | Rejected, `unsupported_envelope_version` (§15) | Fully specified |
| 8 | Missing required field | Rejected at parse (§62) | Fully specified |
| 9 | `evidence_id` digest mismatch | Rejected, `evidence_id_digest_mismatch` (§62) | Fully specified |
| 10 | Corrupt/truncated `provider_assertion` | Parses structurally, fails at `verify_hatp_proof` (§63) | Fully specified |
| 11 | Non-`HATP_HARDWARE_PROVIDER_V1` profile | Unreachable, no `--provider` flag (§11, §22) | Fully specified |
| 12 | Wrong-operation replay | Caught at consumption, `WRONG_OPERATION` (HATP-001) | Fully specified (correctly delegated to HATP-001) |
| 13 | Evidence-file symlink | Rejected, write refuses to follow (§25(2)) | Fully specified |
| 14 | Store-root symlink escape | Rejected, write refuses (§25(3)) | Fully specified |
| 15 | Partial/interrupted write | No partial file visible, atomic temp+rename (§24) | **Atomicity-of-visibility fully specified; F-3's race is orthogonal (about collision, not partial-write)** |
| 16 | Human cancellation | No evidence written, exit 5 (§13, §29) | Fully specified |
| 17 | Hardware device absent | `provider_unavailable`, exit 4 (§13) | Fully specified |
| 18 | Post-preview Decision/Binding mutation | Discarded, no evidence persisted (§32) | Fully specified |
| 19 | No matching RAE Binding | `binding_unavailable`, exit 3, before touch (§10, §21) | Fully specified |
| 20 | AG5 `ecp_id` unresolvable | `operation_not_found`, exit 2 (§7) | Fully specified |

**Additional attacks independently identified beyond the 20-item
matrix:** the concurrent-writer no-clobber race (F-3, elevated to
BLOCKING, arguably a sharper restatement of item 4's own enforcement
mechanism rather than a wholly new attack), and the AG3-analogue of
item 20 (§14 above, NON-BLOCKING matrix-completeness observation).

## 19. B-149O-1..4 and HATP Production Status

Unchanged by this phase, reaffirmed:

```
B-149O-1..4:  INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY
              -- SYSTEM EXECUTION CLOSURE DEFERRED
HATP PRODUCTION: NOT READY
Runtime: Observed / observe / unavailable
```

## 20. Regressions

- **149O.9's own suite** (`tests/test_phase_149o_9_hatp_signing_ceremony_evidence_store_contract_freeze.py`):
  60 passed, unchanged.
- **This phase's independent suite**
  (`tests/test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py`):
  27 passed — re-typing critical frozen expectations independently
  (CLI grammar, schema field set, error vocabulary, attack-matrix count,
  SC-1..12 presence, AG5 inventory, F-2/F-3's structural evidence)
  rather than importing 149O.9's own constants.
- **Fast Green** (`pytest -m fast_green -q`, serial, same
  `--ignore=tests/test_phase_149o_7_...` exclusion 149O.9 used):
  **4590 passed, 2 skipped, 0 failed** — byte-identical passed/skipped
  counts to 149O.9's own Fast Green baseline. 0 failures confirms no
  collateral regression from this phase's doc/test-only changes.
- **Targeted regression sweep**
  (`pytest -k "hatp or rollback or permission_broker or 149o_9 or 149o_10"`):
  independently re-run **twice** — once against this phase's own
  working tree, once against a `git stash -u`-clean checkout of the
  unmodified base commit (39ccfc11) to isolate whether any failure was
  introduced by this phase. **Both runs produced the identical result:
  2884 passed, 3 skipped, 10 failed**, same 10 test names in both runs.
  All 10 failures are independently reconfirmed pre-existing, present
  on the unmodified baseline, not introduced by this phase.
- **Observation (NON-BLOCKING, informational).** 149O.9's own report
  claimed this identical sweep produced "9 failed... identical to
  149O.8's own reconfirmed set." Independent re-run on the exact same
  base commit (39ccfc11, 149O.9's own final commit) produces **10**
  failures, not 9 — the same 10-item set is stable and reproducible
  across two independent runs in this phase. This is either a
  pre-existing test that has always failed and was undercounted by
  149O.9's own sweep, or mild flakiness in the broader suite unrelated
  to HSCE-001. Not connected to HSCE-001's own scope; not remediated
  here (this phase does not modify `src/pcae/**`); recorded for the
  benefit of whichever future phase next touches this test area.

## 21. Findings Summary

| ID | Severity | Summary |
|---|---|---|
| F-1 | NON-BLOCKING | HSCE-REQ-078's self-referential requirement count states 78; the contract actually defines 79 (HSCE-REQ-079 exists in §40). Numbering itself remains sequential/gapless/duplicate-free; editorial only. |
| F-2 | NON-BLOCKING | HSCE-REQ-052's claimed reuse of `_write_atomic_json` "as-is" is imprecise: that function has no symlink check, so HSCE-REQ-057/058 cannot be satisfied by literal unmodified reuse; must be reuse-in-spirit, not reuse-by-call. |
| F-3 | **BLOCKING** | HSCE-REQ-052's frozen "check-then-`os.replace`" write algorithm does not guarantee SC-7's no-clobber property under concurrent writers with differing content for the same `evidence_id` — `os.replace` is unconditional, not exclusive. RAE-001's own working precedent (`write_creation_registration`, `O_CREAT\|O_EXCL`) already demonstrates the fix this repository already knows how to apply. |
| Obs-1 | NON-BLOCKING | `create_production_hardware_provider`'s real signature has an `allow_piv_fallback` parameter HSCE-REQ-022 doesn't address. |
| Obs-2 | NON-BLOCKING | Mandatory attack matrix has no AG3-analogue of item 20 (original_commit_sha resolution failure); semantics already unambiguous via the shared `operation_not_found` error_type. |
| Obs-3 | NON-BLOCKING | Independent re-run of 149O.9's own targeted regression sweep, on 149O.9's own final commit, reproduces 10 pre-existing failures, not the 9 that phase's report claimed. Unconnected to HSCE-001. |

## 22. Contract Verdict

```
NOT VERIFIED
-- BLOCKING HSCE-001 CONTRACT FINDING (F-3)
```

Every other section of HSCE-001 — CLI grammar, locators, proof
field-sourcing, envelope schema, evidence-ID formula and content
addressing, path/symlink validation, closed-schema attacks, error
vocabulary, secret handling, authority separation, TOCTOU handling, and
11 of the 12 security invariants — is independently confirmed complete,
internally coherent, and sufficiently precise for implementation
without ambiguity. The sole blocking gap is narrow and mechanical: the
frozen write algorithm in §24 (HSCE-REQ-052) does not, as literally
specified, guarantee the no-clobber property §19/§37(SC-7) require
under concurrent writers. This is a single-section repair, not a
architectural reopening — the evidence-ID formula, envelope schema, CLI
surface, and every other frozen decision in HSCE-001 remain sound and
should not be reopened by the repair phase.

## 23. Implementation Readiness

```
HATP-001 contract:                     FROZEN (unchanged, unamended)
HSCE-001 contract:                     FROZEN v1.0 (unchanged, unamended by this phase)
HSCE-001 verification status:          NOT VERIFIED -- one BLOCKING finding (F-3)
Signing CLI implementation:            NOT IMPLEMENTED (blocked pending F-3 repair)
Evidence store implementation:         NOT IMPLEMENTED (blocked pending F-3 repair)
AG3/AG5 mandatory-consumption wiring:  NOT IMPLEMENTED (149O.12-13, unaffected)
HATP production:                       NOT READY
```

## 24. Recommended Next Phase

```
149O.10.1 -- HSCE-001 Narrow Contract Repair
```

Scope: amend HSCE-REQ-052 only, to require an atomically-exclusive
publish primitive for the no-clobber write (e.g. `os.link`-based
publish, or a reinstated `O_CREAT|O_EXCL` creation-registry marker,
either following this repository's own already-proven
`write_creation_registration` pattern), and fold in F-1 (count
correction), F-2 (reuse-in-spirit clarification), and Obs-2 (AG3
attack-matrix completeness) as small accompanying text corrections. Do
not reopen any other section of HSCE-001 — every other requirement
verified cleanly in this phase. Once repaired and re-verified,
implementation (149O.8's original "Signing Ceremony Implementation"
phase) may proceed.

## 25. Separately Planned (Not Implemented) — Bootstrap Readiness Classifier Repair

Independent of HSCE-001 and out of this phase's scope: during this
session's `pcae session bootstrap` invocation prior to starting 149O.10,
a latent defect was found in
`src/pcae/commands/session.py::_classify_bootstrap_readiness` (around
line 256). The "stale active task" check calls
`_phase_is_completed(report_phase, latest_report)` — passing the
**latest completed phase's own id** as the first argument instead of
the **active task's** phase id. Since a phase trivially "is completed"
relative to its own report, this check fires unconditionally after
every phase completion regardless of whether the active task actually
matches the just-completed phase or a fresh, correctly-transitioned
next phase — producing a permanent false "Active task appears stale"
block on every bootstrap immediately following any phase close. A
narrow repair task, `pcae-bootstrap-readiness-classifier-repair`, has
been planned (title and file-scope only; no `src/pcae/**` change made
in this phase) for a future session-tooling phase: pass the active
task's own phase id (extracted from `active_task["title"]`) into
`_phase_is_completed` instead of `report_phase`, add a regression test
asserting a freshly-transitioned active task for the *next*
recommended phase is never flagged stale, and re-run
`pcae session bootstrap` end-to-end to confirm `Readiness: ready`
(or `ready_with_warnings`) is achievable immediately after a correct
task transition. This repair is unrelated to HSCE-001/HATP-001/RAE-001
and does not block 149O.10's own contract-verification verdict.

## 26. No-Go Confirmations

No production source (`src/pcae/**`) was modified by Phase 149O.10 —
verification only, one new doc + one new independent test file. No byte
of HATP-001 v1.0 was touched (confirmed via `git diff --stat HEAD`). No
byte of RAE-001 v1.0 was touched. No byte of HSCE-001 v1.0 was touched.
No CLI command was implemented — independently re-confirmed (zero hits
for `hatp sign`/`HATPSignedEvidenceEnvelope` in `src/pcae/commands/` and
`src/pcae/cli.py`). No `.pcae/hatp-evidence/` directory was created. No
hardware was touched; no signing was executed. No Class-B host
provisioning occurred. No HATP production activation occurred. No
rollback dispatch behavior changed. No Permission Broker behavior
changed. No governance bypass, `--no-verify` flag, or force push was
used this phase. Signing remains distinct from verification, approval,
permission, capability, and execution. B-149O-1..4 remain independently
verified at the HATP-gated authority boundary with system execution
closure deferred. HATP production remains NOT READY. Runtime remains
Observed / observe / unavailable.
