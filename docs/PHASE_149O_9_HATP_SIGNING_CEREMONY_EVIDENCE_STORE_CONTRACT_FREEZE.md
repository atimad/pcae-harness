# Phase 149O.9 — HATP Signing Ceremony + Evidence Store Contract Freeze

**Phase type:** architecture/contract freeze only. No production
implementation, no HATP-001 amendment, no CLI implementation, no
hardware provisioning, no signing execution, no Permission Broker
change, no rollback dispatch behavior change.

## 0. Baseline (confirmed at phase start)

- Repository clean, `origin/main..HEAD` = 0.
- Latest completed phase: 149O.8 (HATP AG3/AG5 Production Consumption +
  Signing-Ceremony Architecture) — `status: completed`, `report
  completeness: complete`, pushed, report consistency `consistent`.
- `pcae health` / `pcae check` / `pcae status coherence`: healthy /
  passed / coherent.
- `pcae doctor task-memory`: pre-existing warnings only (a stale
  duplicate `tasks/active/*post-149o-6*.md` file and several
  `tasks/done/` entries missing from `tasks/DONE.md`), unrelated to and
  not introduced by this phase; not remediated here (out of this
  phase's allowed-file scope, consistent with 149O.8's own disposition
  of the identical pre-existing warnings).
- `pcae push check`: clean (`nothing_to_push`).
- `pcae runtime inspect`: `Observed / observe / unavailable`,
  Permission Broker `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.8`: confirmed 149O.8 completed/complete/pushed,
  reconciliation returned `reconciled` (inspection-only, no mutation).

## 1. Scope Recap

149O.8 selected a complete architecture (signing-command family,
evidence-storage design, evidence-ID formula, migration strategy) but
explicitly deferred two things to this phase (149O.8 §33): the exact
frozen CLI/envelope/error-vocabulary contract text, and closing the
open AG5 CLI entry-point inventory question (149O.8 §17, §95, §97).
This phase does both, and does nothing else — it does not implement,
does not wire AG3/AG5 dispatch preconditions to this contract's
outputs (deferred to a future 149O.12-numbered contract per 149O.8
§27), and does not touch HATP-001, RAE-001, Permission Broker, or
rollback dispatch source.

## 2. New Contract

**Identifier:** HSCE-001 ("HATP Signing Ceremony + Evidence Store
Contract"), following this repository's `<ACRONYM>-<sequence>`
contract-naming convention (mirrors `HATP-001`, `RAE-001`, `IWC-001`).
**Version:** 1.0, FROZEN.
**File:** `docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md`.
**Requirement count:** `HSCE-REQ-001` through `HSCE-REQ-079`, 43
sections, RFC-2119 normative language, mirroring HATP-001's own
`HATP-REQ-###` numbering discipline.

HSCE-001 depends on HATP-001 v1.0 and RAE-001 v1.0, both unamended by
this phase (independently re-confirmed: `git diff` against
`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md` and
`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md` is empty for
this phase).

## 3. AG5 CLI Entry-Point Inventory — Closed Finding

149O.8 left open "which CLI command(s), if any, currently reach
`build_rollback_execution` in production" (149O.8 §17, §95, §97, §33).
This phase closes it by direct grep of `src/pcae/` (excluding
`tests/`):

**A real production CLI entry point exists: `pcae rollback --per-id
<id> [--dry-run] [--json]`.**

```
src/pcae/cli.py:3035   subparsers.add_parser("rollback", ...)
src/pcae/cli.py:3055   rollback_parser.set_defaults(handler=run_rollback)
src/pcae/commands/agent.py:16258   def run_rollback(args) -> int:
src/pcae/commands/agent.py:16259     result = build_rollback_execution(
                                          HarnessPath.cwd(), args.per_id,
                                          dry_run=args.dry_run)
```

`run_rollback` calls `build_rollback_execution` with **no**
`hatp_evidence_id`/`hatp_proof`/`hatp_evidence` arguments — confirming
149O.8's gap-analysis conclusion (the gated adapter is unreached by
real AG5 dispatch) was correct in substance, even though 149O.8's own
text understated the finding as an open question rather than naming
`pcae rollback` explicitly. `pcae rollback` is distinct from `pcae
remote rollback approve/deny/execute` (AG3's job-approval commands) and
from `pcae rollback-execution show/list/mark-interrupted`
(inspection-only `RollbackExecutionRecord` commands, never dispatch).
The only other `build_rollback_execution`-named symbol,
`build_rollback_execution_pilot()` (`src/pcae/core/agent.py:27055`), is
a distinct function (Phase-69O design-preview pilot) that does not call
`build_rollback_execution` — confirmed by reading both definitions, a
false-positive name collision only. Full inventory table in HSCE-001
§7 (`HSCE-REQ-014`-`HSCE-REQ-015`).

## 4. CLI Surface (frozen, HSCE-001 §5-§8)

```
pcae hatp sign rollback --site {ag3|ag5} [locator] [--json]

  --site ag3 --job-id <id>              # original_commit_sha auto-derived
  --site ag5 --per-id <id>              # ecp_id auto-derived from PER record
```

No `--dry-run` (the mandatory preview-before-touch step already
provides preview; substrate readiness is not gated, see §5 below — a
separate dry-run mode adds surface with no distinct behavior to gate).
No `--ecp-id` flag (149O.8 §17 left this "TBD at contract-freeze time"
— resolved here in favor of full auto-derivation from the live PER
record's own `ecp_id` field, since a PER carries exactly one). No
`--provider`, `--signer`, `--force`, `--overwrite`, `--output`,
`--decision-digest`, `--binding-digest`, `--repository-id`,
`--signer-key-id`, or any other security-sensitive flag — the only
CLI-supplied identifiers are `--site` and the one non-security-
sensitive operation locator per site.

## 5. Substrate Readiness Is Not a Signing Precondition (reaffirmed)

149O.8 §21 already decided this; this phase carries it forward
unmodified rather than reopening it: `pcae hatp sign rollback` may
attempt to produce a cryptographic proof even when
`inspect_hatp_verification_substrate_readiness(...).operational ==
False`. Production approval remains unavailable regardless, because
`approval_present` is independently re-derived at consumption time.
Hardware-provider *availability* (a real device/library present) IS a
hard precondition — signing fails `provider_unavailable` if
`create_production_hardware_provider` cannot resolve a real provider —
but the broader substrate-readiness conjunction (trust-store ownership,
OS-principal separation) is not checked as a signing-time gate.

## 6. Envelope Format (frozen, HSCE-001 §14-§19)

```
HATPSignedEvidenceEnvelope = {
    evidence_version: 1,                 # int, bool explicitly rejected
    evidence_id: <64-char lowercase hex>, # = digest_hatp_proof_payload(proof)
    proof: <HumanApprovalProvenanceProof canonical document>,
                                          # hatp_proof_to_document(proof) --
                                          # HATP-001 schema, byte-unchanged
    provider_assertion: <base64 string>,  # ProviderAssertion.evidence bytes,
                                          # opaque, standard Base64 (RFC 4648 §4)
}
```

No new proof/verification schema is introduced — this reuses HATP-001's
existing proof shape and Wave-5's existing `ProviderAssertion.evidence`
bytes exactly, per 149O.8 §11's "no HATP v2 schema without contract
need" instruction.

**Evidence ID formula:** `evidence_id = digest_hatp_proof_payload(proof)`
— content-addresses the canonical **proof payload only**, never the
complete envelope and never `provider_assertion`. This precision
closes 149O.8's own flagged ambiguity (149O.8 §12's "multiple valid
proofs" bullet): two independently-valid provider assertions for an
identical proof payload are possible in principle, and are resolved by
a frozen first-write-canonical, byte-compare, conflict-on-mismatch rule
(HSCE-001 §18-§19) — never a silent overwrite, never an implicit
"latest wins."

**Storage:** `.pcae/hatp-evidence/envelopes/{evidence_id}.json`, atomic
temp-file + fsync + compare-then-replace write, CREATE-ONCE/NO-CLOBBER
semantics, explicit-`evidence_id`-only lookup (no "latest" mode
anywhere), lowercase-hex-only path validation, symlink writes refused.

## 7. Closed Error Vocabulary / Exit Codes (frozen, HSCE-001 §22)

Nine exit-code categories (`0` success through `8` persistence
failure), twelve closed `error_type` values, each mapped to exactly one
exit code — full table in HSCE-001 §22 (`HSCE-REQ-046`-`HSCE-REQ-049`).
Mirrors this repository's existing `decision_session.py`
(IWPC-001-style) small-closed-exit-code-category convention rather than
inventing a large numeric-code space.

## 8. Security Invariants (frozen, HSCE-001 §37)

SC-1 through SC-12, covering: only-the-locator-is-human-selected,
derived-not-supplied governance fields, production-only provider/signer
resolution, provider-derived human presence, proof-only content
addressing, explicit-ID-only lookup, no-clobber, no-legacy-fallback,
evidence-existence-is-not-approval, signing-success-is-not-authority,
no-secrets-in-evidence, and mandatory consumption-time re-verification.
Full text in HSCE-001 §37.

## 9. No-Go Confirmations

No production source (`src/pcae/**`) was modified by this phase —
contract-freeze only, two new docs, one new independent test file. No
byte of HATP-001 v1.0 (`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`)
was touched, independently re-confirmed by this phase's own test suite
(git-diff-empty check). No byte of RAE-001 v1.0
(`docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md`) was touched.
No `hatp_ag_authority.py`, `human_approval_trusted_provenance.py`,
`hatp_providers.py`, `hatp_fido2_provider.py`, `rollback_approval_evidence.py`,
`permission_broker_foundation.py`, or `agent.py` symbol was modified —
only read, for the field-source table and AG5 inventory in §3-§4 above.
No CLI command was implemented. No hardware was touched; no signing was
executed. No Class-B host provisioning occurred. No HATP production
activation occurred. No rollback dispatch behavior changed — `pcae
rollback`/`pcae remote rollback approve/execute` are unmodified. No
Permission Broker behavior changed. No governance bypass, `--no-verify`
flag, or force push was used this phase.

## 10. Retained Findings (unchanged by this phase)

- B-149O.3-1, B-149O.3-3, B-149O.3-8 — NON-BLOCKING (149O.7).
- F-3 — stale boundary-test debt, still open (carried since 149O.5).
- Python 3.9 `datetime.fromisoformat` portability debt (149O.7).
- xdist infrastructure debt (pre-existing).
- Real hardware not exercised (unchanged — no hardware touched this
  phase, contract-freeze only).
- B-149O-1..4 — remain `INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY
  BOUNDARY — SYSTEM EXECUTION CLOSURE DEFERRED` (unchanged; this phase
  does not close them, per its own explicit instruction not to).

## 11. HATP Production Readiness

Remains **NOT READY**. Runtime remains `Observed / observe /
unavailable`. Contract freeze is architectural/normative; it implies no
deployment-readiness change.

## 12. Verdict

```
HATP SIGNING CEREMONY + EVIDENCE STORE CONTRACT:
FROZEN v1.0
— READY FOR INDEPENDENT CONTRACT VERIFICATION
```

Not an implementation-readiness claim. B-149O-1..4 remain
`INDEPENDENTLY VERIFIED AT HATP-GATED AUTHORITY BOUNDARY — SYSTEM
EXECUTION CLOSURE DEFERRED`, unchanged by this phase.

## 13. Recommended Next Phase

**149O.10 — HATP Signing Ceremony + Evidence Store Contract Independent
Verification.** The independent verifier SHALL attack, at minimum,
every item in HSCE-001 §38's mandatory attack matrix (20 attacks:
path traversal, case aliasing, no-clobber/conflict, closed-schema
rejection, version-bool rejection, digest-mismatch rejection, symlink
handling, atomic-write partial-failure, cancellation, device absence,
TOCTOU discard, missing-Binding precondition, and PER `ecp_id`
resolution failure), re-confirm §3's AG5 CLI entry-point inventory
against the then-current source tree, and re-confirm no production
source or HATP-001/RAE-001 contract text was modified by this phase.
Signing-ceremony implementation should not begin before that
verification completes.
