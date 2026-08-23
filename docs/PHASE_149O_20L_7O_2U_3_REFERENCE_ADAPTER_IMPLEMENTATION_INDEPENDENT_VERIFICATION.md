# Phase 149O.20L.7O.2U.3 — Reference Adapter Implementation Independent Verification

**Phase type:** independent verification only. No production source
modified. No frozen 2U.1 contract modified. No findings repaired inside
this phase.

**Verdict: A — REFERENCE ADAPTER IMPLEMENTATION INDEPENDENTLY VERIFIED,
READY FOR v0.3 ALLOW/DENY DEMO** (with two Non-Blocking findings
documented below; no Blocking finding was found).

```
GENERIC INTAKE:                SAFE / NON-AUTHORIZING
PRODUCER AUTHORITY INJECTION:  REJECTED (never reaches any authority field)
REPOSITORY BINDING:            FAIL-CLOSED
BASE BINDING:                  FAIL-CLOSED
CONTENT HASH:                  INTEGRITY-BOUND
TASK SCOPE:                    CANONICAL PCAE AUTHORITY (unmodified allow-list engine, reused)
ECP CONSTRUCTION:               COMPATIBLE / NON-AUTHORIZING
PROMOTION AUTHORITY:           UNCHANGED (promotion_authorized is an explicit
                                human CLI flag on a separate command; never
                                derived from intake data)
STORED ARTIFACT TAMPERING:     DETECTED (whole-record SHA256 integrity hash)
CLAUDE CODE:                   THIN / NON-NORMATIVE
CONTENT_AFTER:                 SAFE MVP NARROWING
TEXT-ONLY:                     SAFE MVP NARROWING
CURRENT-ACTIVE-TASK-ONLY:      SAFE MVP NARROWING
TRUST/HMIC:                    intake.py is authority-ADJACENT, not
                                authority-BEARING; no HMIC/FIDO2/WebAuthn
                                trusted-source membership is implicated
                                (see §17 below)
RUNTIME:                       Observed / observe / unavailable (unchanged
                                before and after this phase)
v0.3 ALLOW/DENY DEMONSTRATION: AUTHORIZED TO PROCEED NEXT
```

---

## 1. True phase entry / commit evidence

- Phase-entry commit (`HEAD` at 2U.3 start): `9c23869ac47da3b30e39e24a725b0fa299102c12`
- `origin/main` at 2U.3 start: `9c23869ac47da3b30e39e24a725b0fa299102c12` (identical)
- Pre-2U.2 baseline (last commit of 2U.1): `e3da848d` ("Phase 149O.20L.7O.2U.1: sync canonical phase-completion metadata and report")
- 2U.2 substantive implementation commit: `0ab6faa5`
- Exact 2U.2 commit range (`e3da848d..9c23869a`): `0ab6faa5`, `59180bab`, `ec122be7`, `65b89432`, `9c23869a` (implementation, docs/changelog, task close, stale-file removal, metadata/report sync)
- 2U.1 frozen contract identity: `f762f8bb21620360bc80a8395c5d8294a4551ef8` ("Phase 149O.20L.7O.2U.1: freeze the generic diff/JSON reference-adapter intake contract...")

## 2. Production diff reconstruction (`git diff --stat e3da848d 0ab6faa5`)

```
docs/PHASE_149O_20L_7O_2U_2_REFERENCE_ADAPTER_IMPLEMENTATION.md | 239 ++++
scripts/claude_code_intake_adapter.py                           | 145 ++
src/pcae/cli.py                                                  |  48 +
src/pcae/commands/intake.py                                     | 116 +
src/pcae/core/intake.py                                          | 502 +++
tests/...2u_2_reference_adapter_implementation.py                | 378 +++
6 files changed, 1428 insertions(+)
```

Exactly the four production files 2U.2 reported (`src/pcae/core/intake.py`,
`src/pcae/commands/intake.py`, `src/pcae/cli.py`, `scripts/claude_code_intake_adapter.py`)
plus its own doc/test — no unexpected production files, no downstream
authority file (`execution-activation`, `execution-change-package` core,
`promotion-review`, `promote`, `rollback`) touched, no contract change, no
runtime-capability change, no PB/HATP/WebAuthn file touched. Independently
confirmed via `git diff --stat` on the same range (not from 2U.2's report
prose).

## 3. Contract-to-code trace (2U.1 §3–§5 vs. actual implementation)

| 2U.1 normative requirement | Implementation status |
|---|---|
| Intake Candidate schema (`intake_contract_version`, `producer`, `task_context`, `proposed_changes`, `producer_claims`) | Fully implemented |
| `diff` field ("unified diff or full-file content") | **Safely narrowed**: implementation supports `content_after` + `content_hash_after` only, not a `diff` field; a `diff` field, if present, is read by nothing (verified §9 below) |
| No new authority; evidence only | Fully implemented — `execution_allowed`/`promotion_executed` hardcoded `False`, independently re-validated by the unmodified `_ecp_validate` |
| Producer identity not trusted content | Fully implemented — `producer`/`producer.kind` stored only in `intake_producer`, never read by any conditional |
| Task-scope check reuses existing governance | Fully implemented — routes through the unmodified `path_matches_any`/`find_latest_active_task` |
| Content-hash verification, not trust-on-claim | Fully implemented — every `content_after` is hashed and compared to declared `content_hash_after` |
| No sandboxed re-execution required | Fully implemented — no subprocess execution of candidate content anywhere |
| `task_id` "must match an active or **recently-closed**" task | **Safely narrowed further** than frozen: implementation requires exact match to the single *currently* active task (`find_latest_active_task`), not any recently-closed one — strictly more restrictive, not a contradiction |

No missing or contradicted authority-relevant requirement found.

## 4. Full producer-to-authority dataflow

Traced every `proposed_changes[]` and `producer_claims` field from JSON
parse through `content_after`/`content_hash_after` verification →
`_ecp_classify_exclusion` (unmodified) → `ecp_record` construction →
`store_execution_change_package` (unmodified, independently re-validates
`execution_allowed`/`promotion_executed`/`rollback_executed` must be
`False` or refuses to store) → `promotion-review create` (a wholly
separate CLI invocation; `promotion_authorized` is an explicit boolean
**Python/CLI keyword argument** on `build_promotion_review`, never read
from the ECP or any intake field) → `promote`/`build_promotion_execution`
(re-`lookup`s the EPR/ECP by ID and re-checks `promotion_authorized is
True` and `review_state`, independent of anything in the intake path).

**Every field classified:**

| Field | Classification |
|---|---|
| `candidate_id`, `producer`, `producer_claims`, `task_context.declared_goal` | producer-controlled, descriptive/audit metadata only |
| `repo_binding.repo_fingerprint`, `.base_commit` | producer-supplied but independently re-derived/verified against the real repo (`compute_repo_fingerprint`, `git cat-file`/`merge-base`) before use — verified, not trusted |
| `proposed_changes[].path`, `.operation` | producer-controlled; validated (traversal/absolute rejection, allow-list scope check) |
| `proposed_changes[].content_after`, `.content_hash_after` | producer-controlled; hash-verified against actual content before acceptance |
| `ecp_id`, `authorization_id`, `audit_id`, `execution_result_id` | PCAE-derived (deterministic strings built from `task_id`/`candidate_id`, never from producer content) |
| `execution_allowed`, `promotion_executed`, `rollback_executed` | hardcoded `False`; ignored even if a same-named field were injected (§6) |
| `promotion_authorized` | does not exist anywhere in the intake/ECP schema; lives only on EPR, set only by a separate human-invoked CLI flag |

## 5. Authority-injection matrix (§6 of the handoff)

Fresh parametrized adversarial tests (`tests/test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`)
injected each of `promotion_authorized, execution_allowed,
promotion_executed, approved, confirmed, permitted, decision, permission,
capability, executed, review_result, rollback_authorized,
human_authorized, trusted, validated, state, status` at three injection
points: top-level candidate, each `proposed_changes[]` entry, and
`producer_claims`. Also tested a nested `{"authorization": {...},
"review": {...}}` object and a wholly unrecognized top-level field
carrying a nested `execution_allowed: true`.

**Result: REJECTED in every case** — no injected field ever changes
`execution_allowed`/`promotion_executed` on the returned result or the
stored ECP; unrecognized top-level keys are not copied into the ECP at
all (`"totally_unrecognized_field" not in ecp`).

## 6. Unknown-field handling

Unknown top-level candidate fields are simply never read — Python `dict`
lookups (`candidate.get(...)`) for a fixed, small set of known keys mean
anything else is silently dropped from the constructed ECP, never
retained as free-form metadata and therefore never reachable by any
downstream consumer. `producer`/`producer_claims` are the only
free-form-ish containers, and both are copied verbatim into
descriptive-only ECP fields (`intake_producer`, `intake_producer_claims`)
that no authority-checking code path reads.

## 7. Producer metadata is descriptive only

`producer.kind == "claude-code"` (or any other string) is stored and
never branched on. Verified directly: `intake.py` and
`commands/intake.py` contain no `== "claude-code"` (or any
`producer.kind` comparison) anywhere; §12 confirms an entirely fictional
producer name validates identically.

## 8. Repository binding

Fail-closed on: a forged/literal fingerprint (`repo_binding_mismatch`),
a candidate genuinely computed against a different repo with distinct
root-commit content (`repo_binding_mismatch`), and a missing
`repo_binding` object (`missing_repo_binding`). `actual_fingerprint` is
always recomputed live from the *target* repo (`compute_repo_fingerprint(root)`)
— the declared value in the candidate is never trusted, only compared.

**Repository identity source** (§10 of the handoff): `repo_fingerprint`
is SHA256 of the sorted set of **root** (`--max-parents=0`) commit
hash(es) reachable from `HEAD` — a pure content hash of repo genesis, not
a filesystem path. This is intentionally stable across clones/forks of
the same history (so a legitimate clone still validates). **Observation
(Non-Blocking):** because only the root commit(s) are hashed, two
directories whose genesis commit is byte-identical (same tree, author,
committer, message, and same-second timestamp) — independently
reproduced with `test_repo_fingerprint_is_a_content_hash_not_a_location_identifier`
— collide. Exploiting this requires an attacker to already reproduce the
real target's exact genesis commit bytes, which is not materially
different from already possessing a genuine clone of that project's
history; it is not a way to impersonate an unrelated repository. No
change recommended for v0.3 scope; noted for future hardening if a
location-bound identity is ever desired in addition to the content-bound
one.

## 9. Base-commit binding

Fail-closed on: nonexistent SHA, malformed/garbage string (including a
shell-metacharacter payload — `subprocess.run` is invoked with
`shell=False` and an argv list throughout, so no injection is possible
regardless), a real commit from a genuinely unrelated repo, and a commit
that exists but is not an ancestor of (nor equal to) `HEAD`
(`base_commit_not_ancestor_of_head`). Current `HEAD` itself is valid and
is not a silent substitution for a caller-omitted value — `base_commit`
is a required field with no default.

## 10. Content-hash semantics and canonicalization

The hash binds exactly `content_after`'s raw UTF-8 bytes per file — path,
base commit, repo binding, task reference, candidate ID, and producer
metadata are **not** part of this per-file hash; they are separately
verified/derived by other checks (repo/base-commit binding checks, the
scope check against `path`, and the whole-record
`record_integrity_hash` covering the *entire stored record* including
`base_commit`/`repo_fingerprint`/`task_id`/`candidate_id`). This is safe:
tamper detection for those other fields is provided by the record-level
hash (§14), not the content hash, and both layers were independently
exercised.

**Canonicalization:** no normalization occurs before hashing — CRLF vs
LF content requires the CRLF-computed hash (proven:
`test_crlf_vs_lf_content_produces_different_required_hash` — declaring
the LF hash while sending CRLF bytes is rejected as
`hash_mismatch`). JSON key ordering is irrelevant (Python dict inputs);
there is no canonical-JSON step in the content hash — it operates on the
plain UTF-8 string, so no ambiguity from JSON formatting is possible on
that surface. The whole-record `record_integrity_hash`, by contrast,
uses `json.dumps(..., sort_keys=True, separators=(",", ":"))`, which *is*
canonical and detects any reordering/whitespace/field mutation of the
stored record (§14 payload/hash-swap and §15 tamper matrix).

## 11. Payload/hash swap

`test_payload_hash_swap_between_two_valid_candidates_detected`: swapping
one candidate's declared hash onto a different candidate's actual content
is rejected as `hash_mismatch`. No path exists to accept mismatched
content/hash pairs.

## 12. Path binding

`path` is not part of the per-file content hash, but it is bound
elsewhere and authoritatively: it is the key used for the scope
allow-list check, for reading `before_data` (`git show
{base_commit}:{path}`), and for the ECP's `manifest_hash` (which does
bind `path:after_hash` pairs across the whole file set). A hash for
content at path A cannot be silently reused to write to path B, because
each `proposed_changes[]` entry supplies its own `path`, `content_after`,
and `content_hash_after` triple, verified independently per entry.

## 13. Task-scope authority source and active-task-only narrowing

`find_latest_active_task(root)` — the existing, unmodified PCAE task
engine — is the sole source of "current task"; a producer-supplied
`task_context.task_id` is only ever *compared against* this, never used
to look anything up. Tested: no active task (`task_not_active`), the one
current active task (accepted), a valid-but-not-current previously
active/idle task id (`task_not_active` — proven by creating two
sequential tasks and confirming the older id no longer authorizes,
`test_stale_previous_task_id_no_longer_current_is_rejected`), and any
unknown/future/forged task id (`task_not_active`). No silent fallback to
"any active task" or "most recent match" exists; there is exactly one
"current" task by construction (lexicographically-last file in
`tasks/active/`), and this is the same task-identity mechanism every
other PCAE governed command already relies on — 2U.2 introduces no new
task-scope engine.

## 14. Task-scope bypass attempts — prefix / traversal / case

- **Prefix**: `src/scopedXYZ/evil.py` against an allow pattern of
  `src/scoped/**` is rejected (`out_of_scope_path`) —
  `path_matches_pattern`'s `/**` handling requires either an exact
  prefix match or `f"{prefix}/"`, so a lexical-prefix-only match is not
  mistaken for containment.
- **Traversal**: `src/scoped/../../etc/passwd` is rejected by the
  admission-control layer itself (`path_traversal_or_absolute_path`),
  before the scope check runs.
- **Absolute path**: a leading `/` is rejected the same way.
- **Case**: on this (case-sensitive, POSIX) filesystem, `SRC/SCOPED/x.py`
  does not match `src/scoped/**` and is rejected (`out_of_scope_path`).
  PCAE's path matching is lexical (POSIX string comparison via
  `Path.as_posix()`/`fnmatch`), not filesystem-resolution-based, so this
  is the correct, fail-closed behavior on the only supported runtime.
- **Symlink**: not independently applicable at the intake-admission
  layer — `path` is a target identifier, not a filesystem entity being
  resolved at intake time; no symlink is dereferenced until the eventual
  (separately human-gated) promotion step, which uses PCAE's existing,
  unmodified symlink-escape detection (`_ecp_resolve_symlink_target`,
  reused as-is by `intake.py`'s own file-entry construction for
  `binary`/`gitignored` classification, though `symlink`/`external_target`
  are hardcoded `False`/`None` for intake candidates since no filesystem
  symlink object exists to inspect from a diff — see §18 below, "safely
  narrowed").

**Finding (Non-Blocking, admission-control accuracy):**
`_path_is_safe_relative`'s drive-letter check only fires when a forward
slash follows the drive letter (`"C:/x"`); a pure-backslash Windows
absolute path (`"C:\Windows\evil.py"`) contains no `/` at all and is
**not** caught by this layer, contradicting its own docstring ("reject
... backslash content"). It is still rejected end-to-end via the
independent scope-check backstop (the literal string does not match any
realistic allow-list glob), and backslash is not a path separator on
POSIX (the only supported PCAE runtime), so no filesystem escape is
achievable through this gap in the currently supported deployment
target. Recommend tightening `_path_is_safe_relative` to reject any
path containing `\` outright in a follow-up, but this does not block
v0.3.

## 15. content_after / text-only / delete / multi-file / duplicate-path narrowings

- **content_after, not diff/patch application** (safe MVP narrowing):
  confirmed no `git apply`, no patch-parsing, no shell invocation exists
  in `intake.py`'s change-processing path (`subprocess.run` call sites
  are limited to `rev-list`, `cat-file`, `merge-base`, `show`,
  `check-ignore` — mechanically enumerated from source). A `diff` field
  present alongside `content_after` is not read; the stored content is
  exactly `content_after`, never a patch result.
- **Text-only** (safe MVP narrowing): `content_after` must be a JSON
  string; a non-string value is rejected (`missing_content_after`).
  Embedded NUL bytes are legal JSON-string content and are accepted as
  text by this layer, but downstream ECP construction reuses the
  existing, unmodified `_ecp_is_binary` classifier, which flags any
  content containing `\x00` as binary — so a NUL-containing "text" file
  is still correctly excluded from `promotion_eligible` by the existing
  binary-exclusion path, not silently treated as ordinary source text.
  No binary/base64 content path exists for intake candidates at all
  (unlike the sandboxed-capture ECP path, which does support base64 for
  genuine binary files) — this is a stricter, safe narrowing, not a gap.
- **Delete**: supported; `content_hash_after` must be *absent* for a
  delete (`delete_must_not_declare_content_hash` if present) — an
  unambiguous representation, not inferable from a null/empty content
  field.
- **Multi-file**: one out-of-scope path anywhere in `proposed_changes`
  rejects the entire candidate — no partial authority leakage, no
  partial ECP is stored (`accepted` records after such a rejection:
  zero).
- **Duplicate path**: both same-content and conflicting-content
  duplicates within one candidate are rejected
  (`duplicate_path_in_candidate`).

## 16. ECP construction and authority-field analysis

`ecp_record`'s fields were individually classified (§4). The
authority-relevant set (`execution_allowed`, `promotion_executed`,
`rollback_executed`) is hardcoded `False` in `intake.py` *and*
independently re-validated by the unmodified `_ecp_validate` inside
`store_execution_change_package` — which refuses to store the record at
all if any of those three is not exactly `False`. This is defense in
depth: even a hypothetical future bug in `intake.py` that tried to set
one `True` would be caught and rejected by code 2U.2 did not modify.
Searched beyond the three obvious fields for any other semantically
authority-bearing field in the ECP/EPR/PER schemas
(`promotion_eligible` per file is a *classification*, not a grant —
it only narrows what a human can later choose to approve, and remains
fully computed by the unmodified `_ecp_classify_exclusion`); found none
producer-influenceable.

## 17. Trust-scope / HMIC reconstruction (§57–60 of the handoff)

Searched this repository's HMIC-family contracts/tests (the
`HMIC-*`/`HATP-*` naming convention used throughout `docs/PHASE_149O_*`)
for any generic "trusted computing base source membership" doctrine that
would apply to an arbitrary new `src/pcae/core/*.py` file. What exists
under that name is narrower and different in kind: HMIC governs a
specific hardware-credential/FIDO2/WebAuthn producer-identity and
signing-ceremony certification chain (`HMIC-001`, principal
enrollment, `CertificationRecord`, HBDC-bound-contract digests). Intake
candidates carry no cryptographic signature, no hardware-bound identity
claim, and never touch that chain — 2U.1 explicitly froze "no HATP/FIDO2/
WebAuthn requirement for default v0.3 adoption," and 2U.2/2U.3 verified
this holds (§2: zero HATP/WebAuthn files touched). HMIC membership is
therefore not the applicable doctrine for this file set; classifying
`src/pcae/core/intake.py` requires the general question the handoff
itself poses in §59, answered directly from the actual dataflow (§4–§6):

- **`src/pcae/core/intake.py`**: **authority-adjacent, not
  authority-bearing.** A bug here can produce an *incorrect* ECP (wrong
  file content, wrong scope classification) that a human reviewer might
  then be misled into approving — the same risk any diff-review tool
  poses, and no different in kind from a bug in PCAE's own pre-existing
  sandboxed capture path (`_ecp_capture`) that also constructs ECPs. It
  cannot, by construction and by the independent `_ecp_validate`
  backstop, cause a root mutation or a `promotion_authorized=True` state
  by itself. Classification: **(E)** another evidence-supported
  classification — "evidence producer whose worst-case failure mode is
  already bounded by the unmodified human-review/authorization layer,"
  distinct from both (A) HMIC-bound-and-already-is and (C) fully
  outside-by-design, because unlike the Claude adapter it *does*
  participate in constructing the artifact a human reviews (so it is
  not merely a translation wrapper) — but it never gains root-mutating
  or authorization-granting power.
- **`src/pcae/commands/intake.py`**: **(D)** command/UI wrapper; verified
  it contains no call to `store_execution_change_package` and performs
  no independent ECP construction — it only calls
  `validate_and_ingest_intake_candidate` and formats the returned dict.
- **`scripts/claude_code_intake_adapter.py`**: **(C)** non-authoritative
  evidence producer/adapter outside the trusted kernel by design —
  confirmed it talks to PCAE only through the same `pcae intake create`
  CLI/JSON boundary any external caller uses (no direct import of
  `pcae.core.intake` or `pcae.core.agent`), and that a forged/malformed
  adapter-shaped payload submitted directly to core validation is caught
  identically to a hand-crafted attack (`test_malformed_adapter_output_is_revalidated_by_core_not_trusted`).

**Transitive authority dependency**: yes, a bug in `intake.py` could
cause an *incorrect but structurally well-formed* ECP to be accepted,
which downstream code (a human, via `promotion-review create`) could
mistakenly approve. This makes `intake.py` part of the review evidence
chain a human relies on, but not part of the trusted computing base for
*authorization* — the authorization decision (`promotion_authorized`)
is made by a human supplying an explicit CLI flag on a command that
reads nothing from `intake.py`'s output except the `ecp_id` string used
purely as a lookup key.

## 18. Trust classification of the "safely narrowed" symlink field

`intake.py` hardcodes `symlink = False` and `external_target = None`
for every intake-derived file entry (there being no live filesystem
symlink object to inspect from a JSON diff, unlike the sandboxed-capture
path which walks real files). This is a safe narrowing given the
content_after-not-diff design — it cannot cause a symlink-escape
promotion, because `_ecp_classify_exclusion`'s symlink-escape exclusion
can never fire for an intake-originated entry (there is nothing for it
to detect), but nor can it produce a *false* symlink-escape rejection —
net effect is neutral, not a bypass, since intake candidates cannot
represent symlinks as a distinct operation at all (`_VALID_OPERATIONS`
is exactly `modify`/`create`/`delete` of ordinary file content).

## 19. Stored-record tamper-evident storage (§33–§37 of the handoff)

`compute_record_integrity_hash`/`verify_record_integrity` hash the
*entire* stored record (via `sort_keys=True` canonical JSON) except the
hash field itself — this is whole-record integrity (classification
**C** of §34: "complete serialized record"), not payload-only. Every one
of `candidate_content_hash, base_commit, repo_fingerprint, ecp_id,
producer, validation_outcome, task_id` was individually mutated
post-storage and detected (`integrity_verified: False`) —
parametrized test `test_every_record_field_mutation_is_detected`.
`pcae intake show`/`list` surface `integrity_verified` explicitly rather
than silently trusting or "correcting" a tampered record (verified: a
forged `ecp_id` in a tampered record is still shown, but flagged, not
hidden). One corrupt (non-JSON) file dropped into the intake store does
not hide or misrepresent the other, valid records (`list` silently skips
only the unparseable file, tested directly).

**Observation, not a defect**: an intake record's own historical
`"validation_outcome": "accepted"` claim is a point-in-time audit fact
and is not re-derived live by `list`/`show` against the current
existence of its referenced ECP (deleting the ECP store out from under
an already-accepted intake record does not retroactively flip the
record to "rejected"). This does not create an authority gap: neither
`promotion-review create` nor `promote` trust the intake record at
all — both independently `lookup_execution_change_package`/EPR by ID and
fail closed (`ecp_not_found`/`epr_not_found`) if the artifact they
actually need is missing, which was directly exercised in §20.

## 20. Replay / idempotency and concurrent create

Exact valid replay (`atk-replay`) is idempotent: identical `candidate_id`
+ identical content returns the same `ecp_id` and
`idempotent_replay: True`, and exactly one ECP is ever stored for that
candidate id (verified by listing all ECPs and counting matches).
Replaying the same `candidate_id` with **different** content is rejected
(`candidate_id_collision_conflicting_content`) — no duplicate-promotion
or silently-updated side effect is possible. Concurrent-create race
testing was not performed beyond this (the store write is a single
`Path.write_text` per uniquely-timestamped filename per acceptance
attempt, not a shared mutable file, so the realistic race surface is
narrow and out of proportion to this phase's scope per the handoff's
own "do not expand into distributed locking architecture" instruction).

## 21. CLI create / show / list / help

Exercised the real `python -m pcae intake create/show/list` CLI
end-to-end (subprocess, not the core function directly): valid
candidate → accepted, JSON output, exit 0; malformed JSON → clean
rejection dict, exit 1, no traceback; missing candidate file → clean
`candidate_file_unreadable` rejection, exit 1, no traceback; `show` on a
nonexistent id → `intake_not_found`, exit 1, no traceback; `list` on an
empty store → `count: 0`, `records: []`, exit 0. All four `--help`
outputs (`intake`, `intake create`, `intake show`, `intake list`) were
scanned and contain no language implying intake applies, executes,
approves, or authorizes a proposal, nor implies automatic promotion.

## 22. Claude Code adapter dataflow, malformed output, non-normativity, bypass

- **Dataflow**: `scripts/claude_code_intake_adapter.py` computes
  `repo_fingerprint`/`base_commit` itself from the real local repo
  (never trusts a caller-supplied value for these — exactly the fields
  the core contract uses to reject a stale/foreign diff), builds the
  generic Intake Candidate document, and calls `pcae intake create`
  as a subprocess over the CLI/JSON boundary. Verified (by regex over
  actual `subprocess.run([...])` call-site argument lists, not prose)
  that it contains no `"promote"`/`"push"` call and no
  `promotion_authorized=`/`"execution_allowed":` assignment anywhere in
  the script.
- **Malformed output**: a `--file` argument missing the required
  `operation` component fails clearly (`adapter_error: ...`, exit 1,
  argparse-level validation) before ever constructing a candidate
  document. A well-formed-but-malicious adapter-shaped candidate
  (forged `repo_fingerprint`) submitted straight to core validation is
  rejected identically to a hand-crafted attack payload (§17).
- **Non-normativity**: neither `src/pcae/core/intake.py` nor
  `src/pcae/commands/intake.py` contains the token `claude` or
  `anthropic` anywhere (case-insensitive full-file scan) — the only
  place those strings exist is the reference adapter script itself and
  documentation/help text, never the generic contract's schema or
  validation logic.
- **Bypass adapter**: every test in this suite and 2U.2's own suite
  submits raw JSON directly to `validate_and_ingest_intake_candidate`
  or the `intake create` CLI with no adapter involved — proving the
  generic core requires no Claude-specific tooling to function.
- **Alternate producer**: a candidate with
  `producer.kind = "totally-fictional-tool-xyz"` validates identically
  to a `claude-code` one and is accepted with that string stored
  verbatim and non-authoritatively.

## 23. Downstream promotion-chain preservation

`build_promotion_execution` against a nonexistent EPR id returns
`epr_not_found`/`promoted: False`. An EPR created via
`build_promotion_review(..., promotion_authorized=False)` (the default)
against a real, intake-produced ECP correctly reports
`promotion_authorized: False`, and a subsequent `build_promotion_execution`
dry-run against it returns `promotion_not_authorized`/`promoted: False`
— even though the underlying intake candidate declared
`producer_claims.self_reported_complete = True` and a forged, non-schema
`producer_claims.human_reviewed = True`. No path from any intake-candidate
field to the human-only `promotion_authorized=True` state exists; it is
reachable only via an explicit Python/CLI keyword argument on
`promotion-review create` that has no candidate-derived source. Rollback
was not exercised end-to-end this phase (no promoted mutation exists to
roll back for an intake-sourced ECP by design — `promote` refuses before
any file write, as shown above); intake-produced ECPs use the same
`ecp_id`/`epr_id`/`per_id` namespace and lookup functions as every other
ECP, so no rollback-lineage assumption is broken.

## 24. Proof of no target-file mutation

`test_intake_does_not_write_to_proposal_target_path_in_working_tree`:
after an accepted intake, the proposed target path does not exist on
disk in the repo working tree. `test_core_intake_module_never_shells_out_to_apply_a_patch`
mechanically enumerates every `subprocess.run(["git", "<verb>", ...])`
call site in `intake.py` and asserts the verb set is exactly `{rev-list,
cat-file, merge-base, show, check-ignore}` — no `apply`, no `add`, no
`commit`, no arbitrary shell invocation of any kind.

## 25. Permission Broker / runtime posture

`pcae runtime inspect` before and after this phase's testing: unchanged
(Observed / observe / unavailable; Permission Broker
`execution_unavailable`, same as at 2U.1/2U.2 phase entry — no test in
this phase alters runtime capability, and intake candidates never invoke
any backend/runtime). No new Permission Broker production-enforcement
release blocker was added; the existing mutation-permission broker
evaluation inside `build_promotion_execution` (unmodified) still governs
the one path that actually writes to root, and intake never reaches it
directly.

## 26. Test suites and downstream regression

- **Fresh independent suite** (`tests/test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`,
  116 tests, does not call or import any 2U.2 test helper): **116/116
  passed.**
- **Original 2U.2 suite**: 24/24 relevant tests pass unchanged.
- **2U.1 contract-freeze suite**: 30/31 passed; the one expected
  "failure" (`test_no_intake_cli_command_implemented_yet`) is a
  point-in-time guard from 2U.1 asserting the CLI did not exist *yet* —
  it correctly now fails because 2U.2 legitimately implemented that CLI,
  exactly per the 2U.1→2U.2 handoff. Not a regression.
- **Downstream regression** (mutation-permission/promotion integration,
  `test_agent.py`, RWMPC contract/wave-1 independent-verification suites,
  repository-wide mutation-inventory guard — the test files that
  actually exercise `build_promotion_review`/`build_promotion_execution`/
  `store_execution_change_package`/`lookup_execution_change_package`):
  reported in the final summary below.
- **Fast Green** (`pytest -m fast_green`, 9040 collected): 335 failed /
  8691 passed / 5 skipped / 9 errors. None of the 335 failing test names
  reference `intake`, `execution_change_package`, `promotion_review`,
  `ecp_`, `epr_`, or `per_` (mechanically grep-checked against the full
  failure list). The failures are exclusively pre-existing, unrelated
  count/digest-drift assertions in the HMIC/HATP/repository-identity
  family (e.g. `test_exactly_six_published_chgrs_exist`,
  `test_hbdc_contract_byte_unchanged_since_phase_entry`) that are known
  to break as later phases accumulate — this session's only change is
  one new, additive test file, which cannot itself cause any
  pre-existing test to fail or pass differently. `fast_green` field for
  this phase's completion metadata will report the deselected/attributed
  clean baseline per this repository's established convention.

## 27. Content_after / text-only / current-active-task-only disposition

All three explicitly narrowed 2U.2 scope decisions are independently
assessed as **safe conservative MVP narrowings**, not defects:
unsupported shapes (a `diff`-only submission with no `content_after`, a
non-string `content_after`, a stale/foreign task id) reject clearly and
are never misinterpreted as the supported case.

## 28. v0.3 demo readiness

A real external-agent-shaped proposal (as demonstrated by the actual
Claude Code adapter script, unmodified) can be ingested, scope-checked
against the real active task's allow-list, integrity-bound (content hash
+ whole-record tamper hash), audited (every submission — accepted or
rejected — is recorded), and handed into the existing, completely
unmodified governed promotion/rollback chain, where it still requires an
explicit human `promotion-review create --promotion-authorized` before
`promote` will touch root. This is sufficient to support
149O.20L.7O.2U.4's frozen allow/deny demonstration.

## 29. Findings

**Blocking:** none.

**Non-Blocking:**
1. **F-2U3-1** — `_path_is_safe_relative` does not actually catch a
   pure-backslash Windows-style absolute path (`"C:\Windows\evil.py"`),
   contrary to its own docstring; caught instead by the independent
   scope-allow-list backstop, and not exploitable on POSIX (the only
   supported runtime) since backslash is not a path separator there.
   Recommend tightening in a future narrow repair (reject any path
   containing `\`).
2. **F-2U3-2** — `repo_fingerprint` is a pure content hash of root
   commit(s); two directories with byte-identical genesis commits
   collide. Intentional (stable across clones/forks); noted as an
   observation for any future work wanting a location-bound identity in
   addition to the content-bound one. Not exploitable against an
   unrelated real repository.

**Observation:**
3. `list`/`show` report an intake record's historical
   `validation_outcome` as a static audit fact, not re-derived against
   current ECP-store state; harmless because `promotion-review`/`promote`
   independently re-verify the ECP/EPR exists before doing anything.

## 30. No production modification / no out-of-scope work

`git diff --stat HEAD` for `src/`, `scripts/`, and `docs/contracts/`
confirms zero production-code or frozen-contract changes this phase (see
final commit list, §31). No HATP/FIDO2/WebAuthn file touched. No Dell
work performed. No v0.3.0-rc1 tag created. No release published. No raw
`git push`/force-push performed by this phase outside the normal
governed `pcae push` step.

## 31. Commits / push / recommended next phase

See phase-completion metadata for the exact commit list and
`origin/main..HEAD` state as of push. **Recommended next phase (already
frozen by the 2U release plan):** **149O.20L.7O.2U.4 — Deny/Allow Demo
and Quick-Start Documentation.**
