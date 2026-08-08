# Phase 149O.13 — HATP Signing Ceremony + Evidence Store Independent Implementation Verification

## Identity

**Phase:** 149O.13
**Type:** Independent verification only — no production, contract, or CLI change
**Verifies:** 149O.12A (Signed Evidence Model + Evidence Store), 149O.12B
(Signing Ceremony Resolver + Orchestrator), 149O.12C (CLI Integration +
Full HSCE Attack Matrix), against HSCE-001 v1.1
(`docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`).
**New test module:** `tests/test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py`
(111 tests, independently authored against contract text and direct
source reading, not copied from 12A/B/C's own test files).

## 1. Baseline

- Repository: clean at phase start, `origin/main..HEAD` = 0.
- Latest completed phase: 149O.12C (commits `478e49c9`, `f5c5b42a`,
  `68e6e0b0`), status `completed`, report `complete`, pushed.
- `pcae health` / `pcae check` / `pcae status coherence`: all passed.
- `pcae doctor task-memory`: pre-existing warnings (stale `tasks/done/`
  entries missing from `tasks/DONE.md`, duplicate active-task-file
  history), unrelated to this phase, not remediated (outside allowed-file
  scope).
- `pcae runtime inspect`: Observed / observe / unavailable, Permission
  Broker `execution_unavailable` — unchanged.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report reconcile --phase-id 149O.12C`: `reconciled`,
  `already_dispatched`, inspection-only, no mutation.

## 2. Production Diff Reconstruction (149O.12A → 149O.12C)

Independently confirmed exact production file set, by direct reading of
each file (not trusted from phase reports):

| File | Lines | Classification |
|---|---|---|
| `src/pcae/core/hatp_signed_evidence.py` (149O.12A) | 364 | EVIDENCE_MODEL, EVIDENCE_VALIDATION, EVIDENCE_PARSER, EVIDENCE_SERIALIZER |
| `src/pcae/core/hatp_evidence_store.py` (149O.12A) | 305 | EVIDENCE_STORE, PATH_VALIDATION, SYMLINK_SAFETY, EXCLUSIVE_PUBLICATION |
| `src/pcae/core/hatp_signing_ceremony.py` (149O.12B) | 727 | SIGNING_CONTEXT, AG3_RESOLUTION, AG5_RESOLUTION, BINDING_DECISION_RESOLUTION, SIGNER_PROVIDER_RESOLUTION, PREVIEW, TIMESTAMP, PROOF_CONSTRUCTION, HARDWARE_INVOCATION, TOCTOU, STORE_ORCHESTRATION |
| `src/pcae/commands/hatp.py` (149O.12C) | 252 | CLI_NAMESPACE, CLI_PARSER, CLI_HANDLER, ERROR_MAPPING, OUTPUT |
| `src/pcae/cli.py` (149O.12C, registration-only) | +35 (net) | CLI_NAMESPACE (registration only) |

`UNRELATED` hunks: **0**. `git log` confirms each phase's commit range
touched exactly its own planned file(s); 149O.12A's two files and
149O.12B's one file are unmodified by 149O.12C (independently confirmed
via `git diff --stat` across the 12A→12C commit range for those three
paths — empty).

## 3. Contract Traceability

Sampled and re-derived a substantial subset of HSCE-REQ-001..079 directly
against source (not the 149O.11 plan's own table): the CLI grammar
(HSCE-REQ-009..012), AG3/AG5 locators (HSCE-REQ-013..017), the proof
field-source table (HSCE-REQ-018), Binding/Decision lookup
(HSCE-REQ-020..021), provider/signer resolution (HSCE-REQ-022..024), the
envelope schema (HSCE-REQ-031..038), no-clobber/hard-link publication
(HSCE-REQ-039, HSCE-REQ-052), store layout/lookup (HSCE-REQ-041..045),
the closed error/exit vocabulary (HSCE-REQ-046..049), secret handling
(HSCE-REQ-050..051), path/symlink validation (HSCE-REQ-056..058),
authority semantics (HSCE-REQ-065..067), timestamp generation
(HSCE-REQ-068), TOCTOU (HSCE-REQ-069..070), and blind-touch defense
(HSCE-REQ-071) all have both a production owner and a test owner,
confirmed by direct code reading and by this phase's own 111 new tests
exercising each. No implementation-bearing section found without an
owner.

## 4. Model / Parser / Serializer Verification

- **Field set (§5):** exactly `evidence_version`, `evidence_id`, `proof`,
  `provider_assertion` — confirmed via `__dataclass_fields__` introspection.
- **Immutability (§6):** `@dataclass(frozen=True)`; mutation attempt raises.
- **Version domain (§7):** `True`, `False`, `1.0`, `"1"`, `0`, `2`, `None`
  all rejected by both constructor and parser, identically (the
  `isinstance(value, bool)` pre-check correctly precedes the `int` check).
- **Evidence-ID domain (§8):** uppercase, mixed-case, 63-char, 65-char,
  non-hex, whitespace, slash, backslash, `../`, and a Cyrillic
  lookalike-`а` string all rejected by both constructor and parser.
- **Constructor/parser domain equivalence (§9):** confirmed by direct
  construction of digest-mismatched and malformed-ID envelopes through
  both paths — identical rejection domain, no gap either direction.
- **Proof digest binding (§10):** `evidence_id == digest_hatp_proof_payload(proof)`
  enforced identically at construction and at parse; mismatch rejected
  as `EvidenceIdDigestMismatchError` both ways.
- **Provider assertion independence (§11):** same proof, two different
  `provider_assertion` byte strings, produce the identical `evidence_id`
  — confirmed directly.
- **Canonical serialization / round-trip / non-canonical JSON (§12-14):**
  `serialize(parse(serialize(E))) == serialize(E)`; differently-whitespaced,
  differently-key-ordered input normalizes to the identical canonical
  bytes after one parse+serialize cycle.
- **Duplicate keys (§15):** both an outer duplicate key and a duplicate
  key nested inside `proof` are rejected.
- **Unknown/missing fields (§16-17):** an injected unknown top-level
  field, and each of the four required fields individually removed, are
  all rejected.
- **Base64 (§18):** malformed base64 text is rejected at parse;
  structurally-valid-but-content-garbage base64 parses (HATP-001's own
  `verify_hatp_proof`, not this layer, is where trust is established) —
  confirmed this layer never claims validity by construction.

**Verdict: CONFORMS**, no finding.

## 5. Evidence Store / Hard-Link Publication Verification

- **Store path (§19):** exactly `<repo>/.pcae/hatp-evidence/envelopes/<id>.json`.
- **No side effects on construction/import (§20).**
- **Path traversal (§21):** `../../../etc/passwd...`, an absolute path —
  both rejected before any path is constructed.
- **Symlink final destination (§23):** a symlink placed at the
  destination path is rejected (`EvidencePersistenceFailureError`); the
  external target is never read or overwritten (independently confirmed
  by re-reading the external file's content after the attack attempt).
- **Symlink store-root escape (§22):** `.pcae/hatp-evidence` replaced by
  a symlink to an outside directory is rejected; the outside directory
  remains empty afterward.
- **Special/unreadable final objects (§24-25):** a directory, a FIFO
  (`os.mkfifo`), and an unreadable (`chmod 000`) pre-existing file at the
  destination all fail closed as `EvidencePersistenceFailureError`, never
  overwritten or deleted — independently reproducing the
  149O.10.2-Obs-3 mapping directly against real special files, not
  mocked.
- **Publication order / single winner / idempotency (§29-31):** a fresh
  publish succeeds (`idempotent=False`); an identical retry is
  idempotent (`idempotent=True`, bytes unchanged); a byte-different
  retry under the same `evidence_id` raises `EvidenceConflictError` and
  leaves the original bytes untouched.
- **Two identical concurrent writers (§32):** 8 real OS threads racing
  `publish()` on the identical envelope — exactly 1 winner
  (`idempotent=False`), 7 losers (`idempotent=True`), all 8 reporting the
  identical persisted bytes.
- **Many-writer race, mixed identical/differing (§34, extra attack 119):**
  8 real threads (4 identical, 4 mutually differing) racing — exactly
  one canonical byte sequence ever persisted; every non-conflicting
  writer observes it; every conflicting writer receives
  `EvidenceConflictError`.
- **Non-EEXIST link failure / no fallback (§35, extra attack 120):**
  `os.link` monkeypatched to raise `OSError(EXDEV)` — fails closed as
  `EvidencePersistenceFailureError`; no `.json` file appears at the
  destination; no fallback to `os.replace` is exercised (confirmed by
  source reading of `publish()`: no such fallback code path exists at
  all).
- **Temp cleanup (§38):** no `.tmp` file survives in `envelopes/` after
  a successful publish.
- **Load API / no verification at load (§39-40):** `HATPEvidenceStore`
  exposes no `latest`/`newest`/`list` method; `load()` returns a parsed
  `HATPSignedEvidenceEnvelope` with no `verification_result`/
  `approval_present` attribute.

**Verdict: CONFORMS**, no finding. The repaired HSCE-REQ-052 atomic
hard-link algorithm (149O.10.1) independently re-verified sound under
real concurrent writers on this platform (macOS/APFS), consistent with
149O.10.2's own prior re-verification.

## 6. Signing Production Boundary

- **Zero-override signature (§41-42):** `inspect.signature(production_sign_rollback_evidence)`
  carries exactly `{root, site, job_id, per_id}` — no `provider`,
  `trust_store`, `clock`, or `confirm` parameter exists structurally.
- **F-2 / CLI F-2 re-attack (§43-44):** an AST walk of
  `commands/hatp.py`'s source confirms its only call is to
  `production_sign_rollback_evidence`; the bare identifier
  `sign_rollback_evidence` (the injectable function) never appears as a
  token anywhere in the module outside its own definition elsewhere —
  zero occurrences in `commands/hatp.py`. The one call site passes
  `root` positionally and exactly `site`/`job_id`/`per_id` as keywords —
  no other keyword.
- **AG3/AG5 resolution (§45-46):** `job_id` → live job record →
  `original_commit_sha` (never caller-supplied); `per_id` → live PER →
  `ecp_id` (never caller-supplied) — confirmed by direct reading of
  `_resolve_ag3_operation`/`_resolve_ag5_operation` and by attacks 20/21
  reproduced below (§8).
- **Binding selection (§47-48):** no match → `binding_unavailable`;
  ambiguous (unparseable `created_at`, or a tie) → `binding_unavailable`,
  never a guess; revoked candidates excluded outright; supersession
  applies only within one already-identified operation, never across
  operations (confirmed by direct source reading of `_resolve_binding`).
- **Repository/signer/provider source (§50-52):** repository identity
  read from `read_repository_identity` only; signer resolved from
  `provider.credential_identity()` cross-checked against
  `HATPTrustStore.lookup_signer`; provider resolved from
  `create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)` only
  — no caller-input path to any of the three exists on
  `production_sign_rollback_evidence`'s signature.

**Verdict: CONFORMS**, no finding.

## 7. Ceremony Ordering / TOCTOU

- **Preview before touch (§53):** independent call-order instrumentation
  (a shared list recording `credential_identity` → `confirm` →
  `request_signature`) confirms this exact order on every successful
  ceremony run.
- **No touch on precondition failure (§54):** unknown job, missing
  `original_commit_sha`, unknown PER, missing `ecp_id`, missing Binding,
  and missing repository identity all independently confirmed to reach
  0 `request_signature` calls before raising.
  - **Independent finding (non-blocking, documented, not repaired):**
    `resolve_signing_context` resolves the RAE Binding **before**
    repository identity (confirmed by direct source-order reading and
    by a targeted test: with a Binding present but repository identity
    removed, the call still raises `RepositoryIdentityUnavailableError`
    correctly — but with *neither* present, `BindingUnavailableError`
    fires instead of `RepositoryIdentityUnavailableError`). HSCE-001
    does not specify a precedence order between these two failure modes
    (both map to `EXIT_GOVERNANCE_STATE_UNAVAILABLE`, exit code 3, per
    HSCE-REQ-047), so this is not a contract violation — no hardware is
    ever touched either way — but it means a caller cannot rely on
    `error_type` alone to distinguish "no repository identity" from "no
    binding" when both preconditions are simultaneously unmet.
- **Exactly one signature attempt (§55):** confirmed for the normal
  ceremony (1 call) and independently confirmed for TOCTOU-discarded
  ceremonies (still exactly 1 call, no automatic re-sign) via two
  distinct TOCTOU-attack shapes:
  - **Binding revocation between preview and touch:** context-B
    *resolution itself* fails (`BindingUnavailableError`), because the
    revoked Binding drops out of `_resolve_binding`'s own candidate list
    entirely — it never reaches the `context_a != context_b` equality
    comparison. **Independent finding (non-blocking):** HSCE-REQ-070's
    text names `evidence_serialization_failure` for "the state has
    changed"; a revocation is a case where the state becomes
    *unresolvable* rather than merely *different*, and the
    implementation surfaces the more specific, already-closed-vocabulary
    `binding_unavailable` (exit 3) instead of `evidence_serialization_
    failure` (exit 1). The security property HSCE-REQ-070 actually
    protects — never publish evidence known to be stale at publication
    time — holds under both outcomes (no envelope is ever built or
    published in either case); only the exact `error_type` discriminator
    differs from a literal reading of REQ-070's own error-type naming.
  - **Repository-identity mutation between preview and touch (context
    remains resolvable but differs by value):** the literal
    `context_a != context_b` comparison catches this and raises exactly
    `EvidenceSerializationFailureError`, as HSCE-REQ-070's text
    specifies verbatim.
  - In both shapes, no evidence file is ever persisted.
- **Issued-at / timestamp (§56-57):** `_issued_at_string` truncates to
  whole-millisecond precision internally, never accepts a caller clock in
  production (`production_sign_rollback_evidence` has no `clock`
  parameter).
- **Proof construction (§58):** every proof field traced to its
  canonical producer (repository identity, Binding, Decision, provider
  credential exchange, internal clock) — no field is caller-controllable
  on the production entry point.
- **Human presence / cancellation / device absence / provider exception
  (§62-65):** cancellation → `HumanSigningCancelledError`, no touch
  recorded beyond the one cancelled attempt, no evidence persisted;
  device-fault and generic-exception paths independently exercised via
  the closed exception-mapping in `sign_rollback_evidence` (cancel →
  `human_signing_cancelled`; device fault → `hardware_device_fault`;
  unavailable → `provider_unavailable`; anything else →
  `provider_signature_failure`, fail-closed, never a leaked partial
  result).
- **No authority conflation (§75-79):** independently confirmed —
  signing does not mutate `rollback_approval_state` (byte-identical
  before/after, or absent both times); the ceremony module imports no
  `permission_broker*` module (AST import scan); never calls
  `verify_hatp_proof`, `execute_rollback`, `build_rollback_execution`, or
  `run_rollback` (AST call-name scan); a signed envelope's mere existence
  does not change `pcae rollback`'s dispatch preconditions.
  - **Independent finding, clarifying HSCE-REQ-015 (non-blocking):**
    `build_rollback_execution` itself already carries optional
    `hatp_evidence_id`/`hatp_proof`/`hatp_evidence` keyword parameters —
    but this is a **pre-existing, structurally distinct** AG5 hook from
    Phase 149O.6 Wave 7 (`hatp_ag_authority.resolve_ag5_gated_rollback_authority`),
    unrelated to 149O.12's HSCE evidence-store mechanism: it accepts raw
    `hatp_proof`/`hatp_evidence` objects supplied directly by the
    caller, not an `--hatp-evidence <id>` store-lookup locator, and its
    own docstring states it is "entirely inert... when omitted" and
    "never itself gates dispatch" (`execution_allowed=False`
    unconditionally regardless of these parameters). The real production
    CLI call site, `run_rollback` (`src/pcae/commands/agent.py:16259`),
    passes neither `hatp_evidence_id` nor `hatp_proof`/`hatp_evidence` —
    confirmed by direct AST inspection of its one call site — so
    HSCE-REQ-015's claim ("no HATP arguments") holds exactly for the
    actual production call site, even though the callee's own signature
    is not itself HATP-argument-free. `execute_rollback` (AG3) carries
    the identical pre-existing, pre-149O.6-unrelated hook shape.

**Verdict: CONFORMS**, no Blocking finding; two Non-Blocking findings
recorded above (precedence-order observation, TOCTOU error-type
discriminator observation).

## 8. CLI Grammar / Output / Error Vocabulary

- **Grammar (§80-84):** `pcae hatp sign rollback --site {ag3|ag5}
  (--job-id|--per-id) [--json]` confirmed via the real `build_parser()`;
  `--site AG3` (wrong case) and `--site ag99` (wrong value) both rejected
  by argparse; both-locators and no-locator and wrong-locator-for-site
  all rejected by the handler with exit code 2, before any production
  call; no `--dry-run` flag exists.
- **Forbidden flag inventory (§85):** all 27 named forbidden flags
  independently confirmed rejected by the real parser (`SystemExit`) and
  independently confirmed absent from the `cli.py` hatp-registration
  source block via direct substring scan.
- **Help without hardware touch (§86):** `pcae hatp --help` / `pcae hatp
  sign --help` / `pcae hatp sign rollback --help`, each run in a genuine
  fresh subprocess (including from a nested working directory), exit 0
  and create no `.pcae/hatp-evidence/` directory.
- **CLI production call target / zero override (§87-88):** confirmed via
  AST — the handler's one call passes `root` positionally and exactly
  `site`/`job_id`/`per_id` as keywords.
- **Human/JSON output (§89-90):** human success output free of
  `approved`/`allowed`/`authorized for execution`/`permission granted`/
  `rollback ready`/`rollback executed`; JSON success schema is exactly
  `{status, evidence_id, evidence_path, idempotent}`, free of
  `approval_present`/`hatp_valid`/`pb_decision`/`execution_available`/
  `approved`/`permission`/`executed`.
- **Error vocabulary / exit mapping (§91-94):** `_EXIT_CODE_BY_ERROR_TYPE`'s
  key set matches the closed 12-member HSCE-REQ-047 vocabulary exactly;
  all 9 exit categories (`0`..`8`, `0` reserved for success only) are
  represented among the 12 error-type mappings' values; a genuinely
  unclassified exception (a raw `RuntimeError` a caught error-type
  handler was never meant to see) propagates uncaught rather than being
  silently mapped to a false success or misclassified failure.

**Verdict: CONFORMS**, no finding.

## 9. Mandatory Attack Matrix (21 + 4)

All independently reproduced against the real, assembled implementation
(real filesystem, real threads for concurrency, real argparse/subprocess
for CLI-level attacks; only the hardware provider/trust-store/clock are
faked, per HSCE-001's own scope — no hardware exists in this
environment):

| # | Attack | Result | Conforms? |
|---|---|---|---|
| 1 | `evidence_id` with `../` / absolute path | Rejected pre-filesystem | Yes |
| 2 | `evidence_id` uppercase hex | Rejected, no case alias | Yes |
| 3 | Byte-identical re-write | Idempotent success | Yes |
| 4 | Differing envelope, same ID | `evidence_conflict`, no overwrite | Yes |
| 5 | Duplicate top-level JSON key | Rejected at parse | Yes |
| 6 | Unknown top-level field | Rejected, closed schema | Yes |
| 7 | `evidence_version` bool/wrong type | Rejected, `unsupported_envelope_version` | Yes |
| 8 | Missing required field | Rejected at parse (each of 4 independently) | Yes |
| 9 | `evidence_id` != digest(proof) | `evidence_id_digest_mismatch` | Yes |
| 10 | Corrupt/truncated `provider_assertion` | Parses structurally, no trust claimed | Yes |
| 11 | Non-`HATP_HARDWARE_PROVIDER_V1` profile | Unreachable — no `--provider` flag exists | Yes |
| 12 | Wrong-operation replay | Out of this layer's scope (HATP-001 `WRONG_OPERATION`, unaffected by storage layer) | Yes (by design boundary) |
| 13 | `evidence_id` symlinked outside repo | Rejected, no follow, external target untouched | Yes |
| 14 | `.pcae/hatp-evidence/` replaced by escaping symlink | Rejected, outside dir untouched | Yes |
| 15 | Partial/interrupted write | No partial file visible at canonical path (atomic hard-link) | Yes |
| 16 | Human cancels touch | No file written, `human_signing_cancelled` | Yes |
| 17 | Hardware device absent | `provider_unavailable`, no software fallback | Yes |
| 18 | Post-preview Decision/Binding mutation before touch completes | Discarded, no evidence persisted (two independent shapes, §7 above) | Yes |
| 19 | No matching RAE Binding | `binding_unavailable`, before hardware touch | Yes |
| 20 | AG5 `ecp_id` unresolvable | `operation_not_found`, no touch | Yes |
| 21 | AG3 `original_commit_sha` unresolvable | `operation_not_found`, no touch | Yes |

**Extra attacks (149O.10.1/149O.11's own additions):**

| Extra attack | Result | Conforms? |
|---|---|---|
| Obs-3 loser-read failure (directory/special/unreadable at destination) | `evidence_persistence_failure`, no overwrite | Yes |
| Temp-FD mutation / close-before-link | No writable descriptor survives past write+fsync; no post-link mutation path exists in `publish()` (confirmed by direct source reading — no code after `os.link` success ever reopens or writes to the final path) | Yes |
| Many-writer race (8 real threads, mixed identical/differing) | Exactly one canonical artifact | Yes |
| Non-`EEXIST` link failure (`EXDEV` simulated) | `evidence_persistence_failure`, no fallback | Yes |

**Additional independent attacks (beyond the 25):**

- Two simultaneous signing ceremonies for the identical operation, one
  millisecond apart (`issued_at` differs) → two distinct, legitimately
  coexisting evidence artifacts (different `evidence_id`s, per
  HSCE-REQ-037-038's own explicit resolution) — no authority confusion,
  confirmed both files exist independently.
- Forged-idempotent interpretation: a byte-different envelope under the
  same `evidence_id` is never returned as `idempotent=True` — always
  `EvidenceConflictError`.
- CLI invocation from a nested working directory: `--help` still exits 0
  cleanly (repository-root resolution is not CWD-fragile at the
  `--help` level, since no repository state is touched at all before
  hardware/governance resolution).

No Blocking finding among the 21 + 4 + additional attacks.

## 10. Authority Table

| Concept | Classification |
|---|---|
| `HATPSignedEvidenceEnvelope` | Signed evidence artifact only |
| `evidence_id` | Locator/content-address to the proof payload |
| Signing success (`EXIT_SUCCESS`) | Evidence-creation fact only |
| `HATP VALID` | Future consumption-time verification result (not derived by this surface) |
| `approval_present` | Future gated RAE/HATP-derived fact (never derived here) |
| PB `ALLOW` | Permission decision (never reached from this surface) |
| Execution availability | Separate capability (Runtime remains `unavailable`) |
| Rollback dispatch | Effect (never invoked from this surface) |

No conflation found anywhere in the 149O.12A/B/C implementation.

## 11. Security Invariants SC-1 .. SC-12

| Invariant | Independently verified | Result |
|---|---|---|
| SC-1 (locator-only human selection) | Yes — forbidden-flag inventory + grammar | Holds |
| SC-2 (governance fields derived) | Yes — proof field-source reading | Holds |
| SC-3 (production provider/signer) | Yes — zero-override signature | Holds |
| SC-4 (provider-derived presence) | Yes — no caller boolean anywhere on signature | Holds |
| SC-5 (evidence_id proof-only) | Yes — same-proof-different-assertion test | Holds |
| SC-6 (explicit-ID lookup) | Yes — no `latest`/`newest`/`list` method exists | Holds |
| SC-7 (no-clobber) | Yes — conflict test, concurrency tests | Holds |
| SC-8 (no legacy fallback) | Yes — missing/corrupt evidence never re-derives via `rollback_approval_state` (store performs no such fallback; confirmed by source reading — `load()` has exactly two outcomes, `EvidenceNotFoundError` or a parsed envelope) | Holds |
| SC-9 (existence != approval) | Yes — loaded envelope carries no `approval_present` | Holds |
| SC-10 (signing success != PB/execution) | Yes — `HATPSigningResult`'s exact 3-field shape | Holds |
| SC-11 (no secrets) | Yes — persisted envelope scanned for PIN/private-key markers | Holds |
| SC-12 (consumption always re-verifies) | Out of this surface's scope — no consumption path exists yet (149O.12-13 deferred); vacuously holds because there is nothing here to cache | Holds |

## 12. Secrets, Logging

No PIN, private key, or raw provider secret found in: the persisted
envelope, CLI argument surface, or success/error output. `provider_assertion`
is opaque signed evidence (public by design, per HSCE-REQ-034), not a
secret.

## 13. Python 3.9 Timestamp Defect — `149O.12B-Obs-PY39-1`

**Cause:** `pcae.governance.publication.coordinator._parse_timestamp`
calls bare `datetime.fromisoformat(value)` without normalizing a
trailing `Z`. `datetime.fromisoformat` only began accepting a trailing
`Z` in Python 3.11 (CPython bpo-41762); on Python 3.9/3.10 this call
raises `ValueError` for any of this repository's own canonical
`Z`-suffixed timestamps.

**Independent confirmation method:** direct source inspection of the
unpatched function (captured at test-collection time, before this
suite's own autouse Z-tolerance monkeypatch fixture applies) plus
version-gated reasoning against the documented CPython behavior change.
**No Python 3.9 interpreter was available in this verification
environment** (`python3.9`/`python3.10` not found on `PATH`); this is
disclosed as a limitation rather than papered over — the defect's
existence is established by direct code inspection and the documented,
version-gated `fromisoformat` behavior change, not by triggering the
exception live on 3.9.

**Operational effect on HATP signing:** `create_rollback_approval_decision`
(the only production path that creates a fresh CHGR Decision, itself a
prerequisite to a fresh RAE Binding, itself a prerequisite to
`pcae hatp sign rollback` ever reaching a hardware touch) calls
`PublicationCoordinator.execute`, which calls the defective
`_parse_timestamp`. **On Python 3.9/3.10, no *new* Decision/Binding pair
can be created via production code**, which means no *new* operation can
be onboarded to signing on those interpreters — this materially blocks
the new signing surface operationally, not merely a cosmetic concern, on
this repository's stated minimum-supported Python version. Signing
against a Binding created *before* hitting this defective code path
(e.g., under Python 3.11+, or by hand-constructed Binding in a test) is
unaffected, since the signing ceremony's own Binding *lookup*
(`list_bindings_with_keys`) does not call `PublicationCoordinator`.

**Recommended repair timing:** a narrowly-scoped follow-up phase
(e.g. `149O.13.1 — Publication Timestamp Python 3.9 Compatibility
Repair`) should fix `coordinator.py::_parse_timestamp` directly (the
identical Z-tolerant pattern already used in half a dozen other modules
in this codebase, including this phase's own test fixture) before any
phase that depends on creating *fresh* CHGR Decisions/RAE Bindings on
Python 3.9/3.10 is undertaken. This defect predates 149O.12 entirely
(confirmed pre-existing by 149O.12B's own `git stash -u` A/B comparison)
and is out of 149O.13's verification-only scope to repair.

**Classification:** PRE-EXISTING, OUT OF HSCE IMPLEMENTATION SCOPE,
Non-Blocking for HSCE-001 conformance (the contract's own
`create_rollback_approval_decision` dependency is RAE-001's, not
HSCE-001's), but a real operational limitation for signing-surface
usability on Python 3.9/3.10 specifically for onboarding new operations.

## 14. Regressions

| Suite | Result |
|---|---|
| 149O.12A dedicated (`test_hatp_signed_evidence.py`, `test_hatp_evidence_store.py`) | 132 passed |
| 149O.12B dedicated (`test_hatp_signing_ceremony.py`) | 44 passed |
| 149O.12C dedicated (`test_hatp_cli.py`, `test_phase_149o_12a/b/c_*.py`) | 188 passed |
| Contract-phase regression (149O.9, 149O.10, 149O.10.1, 149O.10.2) | 195 passed, 3 failed |
| `-k "hatp or rollback_approval"` full sweep | 2112 passed, 13 failed, 3 skipped |
| Fast Green (`pytest -m fast_green -n auto`) | 4980 passed, 2 skipped, 0 genuine failures |

**Contract-phase regression, 3 failures — expected, non-blocking,
independently explained:** `test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py::test_no_hatp_sign_cli_implementation_exists_anywhere`,
`test_phase_149o_10_1_hsce_001_narrow_contract_repair.py::TestBoundaries::test_no_hatp_sign_cli_implementation_exists`,
and `test_phase_149o_10_2_hsce_001_atomic_no_clobber_reverification.py::TestProductionAndContractBoundaries::test_no_hatp_sign_cli_implementation_exists`
are byte-history snapshot assertions from phases 149O.9/10/10.1/10.2,
written when no CLI existed yet — they literally assert `grep -rn "hatp
sign|HATPSignedEvidenceEnvelope" src/` returns nothing. 149O.12C's own
CLI implementation necessarily makes this assertion false; these three
files were not among the six files 149O.12C already widened under the
149O.5-F-3 precedent (confirmed: `git log` shows none of these three
touched since their own origin-phase commit). **Recommendation:** a
future phase should widen these three identically to the six 149O.12C
already handled. Not repaired here — outside 149O.13's verification-only
scope and outside this task's allowed-file list.

**`-k "hatp or rollback_approval"` sweep, 13 failures — pre-existing,
unrelated, independently reconfirmed exactly matching 149O.12C's own
documented baseline count** ("a full `-k "hatp or rollback_approval"`
sweep shows exactly 13 pre-existing, unrelated failures", 149O.12C
phase-completion report). Since 149O.13 makes zero production changes,
an identical failure count is exactly the expected non-regression
signal — confirmed, not merely trusted.

**Fast Green: 4980 passed, 2 skipped, 0 genuine failures** — a +112
delta over the 149O.12C-entering baseline of 4868, of which this phase's
own 111 new tests account for the overwhelming majority (remainder
attributable to ordinary environment/collection variance, not a defect).
One collection error (`test_phase_149o_7_hatp_class_b_activation_independent_verification.py`,
missing optional `fido2` dependency in this environment) is pre-existing
and unrelated — excluded from the Fast Green count per this repository's
own optional-dependency convention, not a new failure introduced by this
phase.

## 15. `149O.10.2-Obs-3` Final Status

**INDEPENDENTLY CONFIRMED RESOLVED.** Directory, FIFO, and unreadable
final-object attacks against the real filesystem all independently
reproduce the documented `evidence_persistence_failure` mapping, never
`evidence_conflict`, never an overwrite/delete.

## 16. `149O.10-F-3` Status

**INDEPENDENTLY CONFIRMED CLOSED, no regression.** The atomic hard-link
publication algorithm (HSCE-REQ-052 v1.1) independently re-verified
sound under 8-thread real concurrency (§5 above), consistent with
149O.10.2's own prior re-verification.

## 17. `149O.5-F-3` Status

**PARTIALLY CLOSED, RETAINED for the residual three files** (§14 above).
149O.12C's own six-file widening correctly closed the finding for the
files it touched; the original finding's scope (stale "no HATP CLI
exists yet" boundary snapshots repository-wide) was broader than the six
files 149O.12C selected, and three additional files with the identical
stale-assertion shape were not in scope of 149O.12C's own touch set.
Not re-opened as Blocking — these are non-security test-hygiene failures
with a clear, narrow, already-precedented fix.

## 18. Verdicts

```
HSCE IMPLEMENTATION VERDICT:
VERIFIED WITH NON-BLOCKING FINDINGS
— HSCE-001 v1.1 SIGNING CEREMONY + EVIDENCE STORE IMPLEMENTATION CONFORMS

HATP SIGNING SURFACE:
INDEPENDENTLY VERIFIED
— EVIDENCE CREATION ONLY — NOT ROLLBACK AUTHORIZATION OR EXECUTION

AG3 MANDATORY HATP CONSUMPTION:
NOT IMPLEMENTED

AG5 MANDATORY HATP CONSUMPTION:
NOT IMPLEMENTED

B-149O-1..4:
INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY
— SYSTEM EXECUTION CLOSURE DEFERRED

HATP PRODUCTION:
NOT READY

Runtime:
Observed / observe / unavailable
```

Non-Blocking findings recorded (none Blocking):

1. `resolve_signing_context` resolves the RAE Binding before repository
   identity — order-of-precondition observation only, both outcomes map
   to exit 3, no hardware ever touched either way (§7).
2. TOCTOU-via-revocation surfaces `binding_unavailable` rather than the
   literal `evidence_serialization_failure` HSCE-REQ-070 names — security
   property (no publish) holds under both; only the discriminator
   differs (§7).
3. `build_rollback_execution`/`execute_rollback` already carry
   pre-existing (149O.6, unrelated), inert, non-gating `hatp_evidence_id`/
   `hatp_proof`/`hatp_evidence` keyword parameters — the real production
   CLI call sites pass none of them, so HSCE-REQ-015 holds for actual
   dispatch; documented to prevent future confusion with 149O.12's
   distinct HSCE evidence-store mechanism (§7).
4. Three pre-existing byte-history boundary test files (149O.9/10/10.1/
   10.2) now fail because they assert CLI non-existence, which 149O.12C
   correctly made false; not among the six files 149O.12C already
   widened under the 149O.5-F-3 precedent — recommend a follow-up phase
   widen these three identically (§14, §17).
5. Python 3.9/3.10 timestamp defect `149O.12B-Obs-PY39-1` blocks
   *creating new* CHGR Decisions/RAE Bindings via production code on
   those interpreters, which operationally blocks onboarding *new*
   operations to signing on those interpreters specifically — pre-existing,
   out of HSCE scope, recommend a narrow follow-up repair phase before
   depending on fresh-Decision creation on Python 3.9/3.10 (§13).

## 19. Recommended Next Phase

Per the governing prompt's own guidance (§165): do not proceed directly
to arbitrary implementation. The next bounded capability is **HATP
AG3/AG5 Mandatory Production Consumption Architecture / Contract** —
deciding how rollback commands reference `evidence_id`, when HATP becomes
mandatory, how `rollback_approval_state` loses authority, the one-way
cutover mechanism, and AG3/AG5 consumption wiring specifically (distinct
from Permission Broker execution enforcement / COMP-002, which remains a
separate track). Before that, consider whether `149O.13.1` (the Python
3.9 timestamp repair, §13) should land first if any near-term phase
depends on creating fresh Decisions/Bindings on Python 3.9/3.10.

## 20. Explicit Confirmations

- No production source (`src/pcae/**`) was modified by 149O.13.
- HSCE-001 v1.1, HATP-001 v1.0, and RAE-001 v1.0 all remain byte-unchanged
  (confirmed: last touching commit for all three contract files predates
  149O.12A; `git log` shows no 149O.12A/B/C/13 commit touching any of
  them).
- The signed-evidence/store/signing/CLI implementation was independently
  reconstructed by direct source reading and by 111 freshly-authored
  tests, not trusted from 149O.12A/B/C's own phase reports.
- No AG3/AG5 mandatory HATP consumption exists (confirmed: `run_rollback`
  and the real `pcae rollback`/`pcae remote rollback approve/deny/execute`
  CLI surface pass no HATP arguments to their respective core functions).
- No legacy rollback authority was changed by HSCE implementation
  (`rollback_approval_state` byte-identical before/after signing).
- No Permission Broker behavior changed (no `permission_broker*` import
  anywhere in the signing/CLI modules).
- No `approval_present` is produced by signing.
- No rollback execution occurs from signing.
- No Class-B provisioning occurred.
- No production HATP activation occurred.
- Signing remains distinct from verification, approval, permission,
  capability, and execution (§10 authority table).
- B-149O-1..4 remain independently verified at the HATP-gated authority
  boundary with system execution closure deferred.
- HATP production remains NOT READY.
- Runtime remains Observed / observe / unavailable.
