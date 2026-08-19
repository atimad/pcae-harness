# Phase 149O.20L.7O.2H.2 — HMIC-001 v1.6 Paths Source-Scope Closure and Seven-Contract Ceremony Consistency Repair

## Outcome

**PATHS SOURCE-SCOPE CLOSURE AND SEVEN-CONTRACT CEREMONY CONSISTENCY
REPAIRED — INDEPENDENT VERIFICATION PENDING.**

This narrow phase repairs only `B-149O.20L.7O.2H.1-1` and
`B-149O.20L.7O.2H.1-2` and their direct consequences. It does not independently
verify its own repair, close either finding, certify HMIC, provision trust
state, create a real DeploymentBinding, integrate readiness, or activate HATP.

## Fixed entry and primary evidence

- Phase-entry commit: `bb652aa4d18b5568e15feaf98c525ce0a6bd9a01`.
- Entry state: clean `main`, zero commits ahead of `origin/main`; health,
  check, and coherence passed; task-memory warnings were historical.
- Runtime: Observed / observe / unavailable; no active governed phase before
  transition; Telegram configured.
- HMIC entry identity: v1.5, 26 source-relative + 9 root-relative = 35 frozen
  members, seven contract identities, seven required record keys.

The exact AG3 authority chain is:

```text
production_sign_rollback_evidence
→ sign_rollback_evidence
→ resolve_signing_context
→ _resolve_ag3_operation
→ build_rollback_review
→ HarnessPath.join
→ .pcae/remote/jobs/<job_id>.json
→ original_commit_sha
```

The AG5 sibling is:

```text
resolve_signing_context
→ _resolve_ag5_operation
→ lookup_promotion_execution_record
→ HarnessPath.path
→ .pcae/promotion-executions/<per_id>.json
→ ecp_id
```

Disposable execution from 2H.1 was reproduced as a regression fixture:
changing only unbound `paths.py` redirects the real AG3 record and changes the
commit identity consumed by signing while the old 35-member digest remains
unchanged. A module-level “generic utility” label and import precedent were
therefore not valid substitutes for reached-symbol behavior. Binding a caller
does not bind a separately loaded dependency's bytes.

The remaining reviewed leaves stay excluded. The enrollment writers reach
`provenance.py` only after mutation and durable readback to append audit
evidence; its reached `git_status.py` and `tasks.py` helpers populate audit
metadata only. None selects, gates, or changes the credential, Principal,
Signer, signing context, provider, publication, or protected record.

## Repair

HMIC-001 evolves v1.5 → v1.6. `core/paths.py` is added unchanged to
HMIC-REQ-050 and `_FROZEN_SRC_PCAE_RELATIVE_FILES`. The exact identity is now:

| Bucket | v1.5 | v1.6 | Delta |
|---|---:|---:|---:|
| `src/pcae/`-relative | 26 | 27 | +1 (`core/paths.py`) |
| repository-root-relative | 9 | 9 | 0 |
| total frozen content/source | 35 | 36 | +1 |
| contract identities | 7 | 7 | 0 |
| required contract-version keys | 7 | 7 | 0 |

The change is additive: all v1.5 signing/enrollment, Class-B, and
DeploymentBinding members remain bound. A version evolution is required
because a new authority-bearing digest input changes normative certified
identity; this is not an editorial same-version correction.

Current HMIC-REQ-076 now requires deriving `contract_versions` by reading each
of the exact seven bound contracts' own live version headers. This matches
HMIC-REQ-067/069, `derive_contract_versions`, and the closed
`CertificationRecord` representation. No eighth identity or legacy
four/five/six-member record is admitted. An old 35-member certification fails
first as `IMPLEMENTATION_MISMATCH` at validation step 9, before the unchanged
seven-contract comparison at step 10.

The historical 7L.6 HMIC-REQ-145 byte guard was narrowed to HMIC-REQ-145's own
horizontal-rule section boundary. Its generic helper had required the next
requirement heading to contain a parenthesized subtitle; because HMIC-REQ-071
does not, the match overran into unrelated HMIC-REQ-076 prose. Mutation and
neighbor controls prove the intended HMIC-REQ-145 invariant remains effective.

## Verification evidence

- New phase suite: **28 passed** in 1.23 seconds.
- Focused current functional regression selection: **583 passed** in 17.31
  seconds.
- Broader historical selection: 456 passed, 34 expected exact prior-version /
  prior-count pins failed; no current functional failure was found.

Fast Green was run at the fixed phase-entry commit in an isolated worktree and
on the current tree:

| State | Passed | Failed | Errors | Skipped | Duration |
|---|---:|---:|---:|---:|---:|
| fixed entry, first run | 8272 | 304 | 9 | 4 | ~154 s |
| fixed entry, exact-cache rerun | 8271 | 305 | 9 | 4 | 149.77 s |
| current | 8255 | 349 | 9 | 4 | 138.79 s |

The exact fixed/current non-passing node comparison produced 45 current-only
and one fixed-only node. Forty-four current-only nodes are expected:

- 23 historical working-tree/no-production-change assertions, including one
  filename-only “no certification artifact” assertion triggered by this
  authorized phase's test/report names and not by certification state;
- 4 exact 2H.0 v1.5/35/stale-REQ-076 pins;
- 11 exact 2H.1 35-member/open-finding pins;
- 5 exact 2H v1.5/35-member pins;
- 1 20L.7K assertion that deliberately used `paths.py` as a non-member control,
  whose premise is the semantic invariant this repair changes.

The remaining current-only node was
`TestAuditPersistence::test_audit_verify_cli`, whose subprocess has a hard
15-second timeout. Isolation timed out at 15.01 seconds; its paired tamper
test passed in 17.83 seconds. A subsequent direct read-only audit completed in
9.39 seconds over 178353 records. The fixed-only delta was that paired tamper
test, confirming the pre-existing timing/state swap. This phase changes no
shell-gate, audit, or command implementation file. Fast Green is reported
honestly as non-green, with no phase-caused functional regression identified.

## Finding dispositions and boundaries

- `B-149O.20L.7O.2H.1-1`: **REPAIRED — PATHS AUTHORITY SOURCE BOUND —
  INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**
- `B-149O.20L.7O.2H.1-2`: **REPAIRED — SEVEN-CONTRACT CEREMONY CONSISTENCY
  RESTORED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**
- `B-149O.20L.7O.2G-1`: **REALIGNED — TRANSITIVE SOURCE CLOSURE REPAIRED —
  INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**
- `B-149O.20L.7O.2H-1` remains independently closed only at the exact
  seven-member CertificationRecord/contract-identity representation boundary.
- BF-1, BF-2, `B-149O.20L.7O.2F.3-1`, and
  `B-149O.20L.7O.2F.3-2` remain closed at their previously established
  implementation boundaries. CBV-S10 remains open and untouched.

No HMIC certification or activation was performed. No trust/FIDO2
provisioning, real Principal/Signer enrollment, real DeploymentBinding,
hac-dell/Protected Root write, readiness integration, execution permission, or
runtime capability change occurred. Runtime remains Observed / observe /
unavailable.

## Next phase

**149O.20L.7O.2H.3 — HMIC-001 v1.6 Paths Source-Scope Closure and
Seven-Contract Ceremony Consistency Repair Independent Verification.**

That phase must independently re-derive and test the 36/7 closure. This repair
does not authorize certification, provisioning, readiness integration,
activation, CBV-S10, PIV, or Stream-B work.
