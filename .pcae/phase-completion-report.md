# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R Complete — HPAC-REQ-022/023 Production Protected-Admin Writer Anchor: Architecture and Contract Adjudication

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R
**Type:** governed architecture / trust-boundary / contract-adjudication phase (adjudication only)
**Status:** COMPLETE — ADJUDICATED (not BLOCKED)
**Phase-entry SHA:** `8e65529596fc351face4b83c4b5d08573326d034` (`origin/main` synced; `origin/main..HEAD = 0` at entry)
**Production source changed:** none (`git diff 8e655295 HEAD -- src/pcae` empty)
**Normative contracts changed:** none (`git diff 8e655295 HEAD -- docs/contracts` empty); RHAMP-001 v1.0 byte-unchanged; HPAC-001 stays v2.1; `HPAC-AUTHORITY-CONSUMPTION` stays `/2.1`
**Tests changed:** none (`git diff 8e655295 HEAD -- tests` empty)
**Runtime:** `not_implemented / Observed / observe / unavailable`; 0 plugins / 0 capabilities; FIRST EXTERNAL EFFECT ABSENT; execution NOT enabled

## Summary

`.1R.30R` was authorized to adjudicate — architecture / trust-boundary /
contract only — the absent **positive** half of the HPAC-REQ-022/023
protected-admin writer anchor that the historical `.1R.30` implementation phase
correctly STOPPED at (BLOCKED, immutable, preserved). HPAC-001 v2.1 §7 froze
the anchor **policy** (HPAC-REQ-022/023/024/080) and the **negative** boundary
(`HPACStoreAuthority._validate_production_boundary` — the protected root is
validated as not agent-writable with safe ancestors), but deliberately
deferred the **mechanism**: how PCAE code recognises the external
deployment-owner administration principal and mints a `PRODUCTION`
`HPACWriterCapability` that `HumanPrincipalRegistryStore._writer()` accepts.

The gap was independently reconstructed from source (`hpac_foundation.py` and
`human_principal_registry.py` read in full; the `HPACWriterCapability` seal
discipline traced; every `PRODUCTION`-writer minting path proven absent). A
writer-anchor threat model was frozen. Five candidate trust mechanisms were
evaluated against same-UID-agent, repository/environment/cwd, and root/`sudo`
risks. The existing PCAE precedent — HBDC-001 v1.2's independently-verified
Class-B Protected-Root writer boundary (`hatp_deployment_binding_admin.py`:
*"Real security boundary: OS filesystem write permission on the Protected Root,
never an in-process check"*) — was found to be a direct match.

## Adjudication result

**Not BLOCKED.** The trust root is non-circular (OS filesystem write authority
on an out-of-band-provisioned protected root), same-UID-agent-safe, offline,
macOS+Linux portable, and directly precedented.

**Preferred anchor (Candidate E, composed):**

| Element | Frozen value |
|---|---|
| Trust root | OS filesystem write authority on `<HPAC_PROTECTED_ROOT>` (fixed macOS/Linux paths), agent principal provably excluded via `_effective_write_access` / `_current_agent_identity` |
| Positive recognition | root-identity-bound `.authority/` deployment-owner descriptor (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`) + `_validate_production_boundary` + a positive write probe (this invocation *can* write the root) + a not-agent-identity check — all four required |
| Capability issuer | a new `PRODUCTION` writer factory (recommended `HPACStoreAuthority.production_writer(operation, *, principal_id=None, credential_id=None)`) exported only from a **non-agent-importable** module (recommended `src/pcae/core/hpac_protected_admin_writer.py`), guarded by a `.1R.30R.*` consumer-inventory test (HBDC-REQ-056/066 precedent) |
| Capability scope | one operation; one target principal/credential; process-local; non-serializable (`__reduce__` raises); restart-invalid; not reusable for a second operation |
| Bootstrap | a one-time out-of-band `scripts/hpac_protected_root_admin.py provision` step by the admin OS principal — creates the `0700` root + store-identity manifest + deployment-owner descriptor + durable provenance entry; create-only; non-recurring; not agent-reachable (HBDC-REQ-011..021 precedent) |
| Revocation | admin filesystem replace/remove of the `.authority/` descriptor; the next `production_writer()` fails closed; root copy/replace caught by the `{device, inode}` root-identity manifest |
| Same-UID exclusion | no write access + no importability + per-instance seal identity + `__reduce__` raising + live re-probe |

**Rejected alternatives:** `sudo`/`euid` gate (OS privilege ≠ deployment-owner
identity; same-UID `sudo` NOPASSWD / `setuid` bypass; PCAE frozen precedent
`_FORBIDDEN_SELF_ELEVATION_ATTRS` / `_SUSPICIOUS_ENV_KEY_SUBSTRINGS` already
bans it); admin-signed record + pinned key (moves the trust root into an
unexplained persistent key; collapses to the descriptor case anyway); OS
keychain/keyring key (user-keyring items are same-UID-readable — the exact
threat; not portable); bare descriptor-by-path (path-only authority).

## Contract-adjudication verdict

**B — NEW COMPANION CONTRACT REQUIRED.** Recommended `HPAC-PAWA-001 v1.0` —
HPAC Production Protected Administration Writer Anchor Contract, independent
`HPAC-PAWA-REQ-###` namespace, authored by a dedicated contract-freeze
successor (REPRC-001 / PBNDE-001 / RHAMP-001 companion precedent — a companion
born to avoid a parent cascade). **HPAC-001 stays v2.1** (no bump — the
mechanism is additive and widens no authority; a MINOR would force
re-independent-verification of an actively-referenced frozen contract).
**RHAMP-001 stays v1.0, byte-unchanged** — RHAMP-REQ-047 already points to an
*external* anchor. Pure implementation rejected as the primary verdict (would
hide normative trust decisions in code — phase prompt §35). HPAC MINOR/MAJOR
rejected. BLOCKED rejected (no circularity; no MAJOR redesign; no remote
infrastructure; no reusable same-UID bearer secret; HBDC-001 is a direct
precedent).

## Phase-ID derivation

CPIPC-001 v1.0 §4: `.1R.30` = `numeric-segment` `30`, immutable BLOCKED, never
reused/resumed. `.1R.30R` = `numeric-segment` `30R` (digits + repair-letter
suffix). Repository precedent: `.1R.19R`→`.1R.19R.1`, `.1R.22R`→`.1R.22R.1`,
`.1R.27R`.

- **Fresh implementation successor:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2`
- **Dedicated IV of this adjudication:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1`
- **Re-derived downstream sequence** (IDs recommended, NOT reserved; each its
  own explicitly human-authorized phase): `.1R.30R.1` (adjudication IV) →
  `.1R.30R.2` (`HPAC-PAWA-001 v1.0` freeze) → `.1R.30R.3` (mechanism + registry
  + writer-anchor implementation — the old `.1R.30` scope) → `.1R.30R.4` (IV) →
  `.1R.30R.5` (protected presentation + `require_real_assurance` wiring — old
  `.1R.32`) → `.1R.30R.6` (IV + mandatory real-CTAP2 hardware + N-16-5 closure
  — old `.1R.33`) → N-16-6 → N-16-7 (strictly last). The stale RHAMP-REQ-156
  tail (`.1R.31`/`.1R.32`/`.1R.33`) is superseded.

## Scope discipline

No writer-anchor mechanism implemented. No contract authored (the verdict is a
recommendation to author `HPAC-PAWA-001 v1.0` in `.1R.30R.2`). `hpac_foundation.py`
not modified. No FIDO2, no `_ELIGIBLE_MECHANISM_IDS` change, no `verifier_kind`
addition, no `RHAMP-FIDO2-CREDENTIAL/1.0` sidecar, no `RHAMP-COUNTER-STATE/1.0`
store, no enrollment/bootstrap tool, no protected presentation helper, no
approval proof, no `PRODUCTION` `AuthenticatedHumanPrincipal`, no
`require_real_assurance` wiring, no hardware access, no test file, no guard
reconciliation. No N-16-6 / N-16-7 / Slice C work; no `adapter.dispatch()`; no
first external effect; no execution enablement. Historical `.1R.30` preserved
byte-unchanged and immutable BLOCKED.

## Carried findings

N-16-3 CLOSED. N-16-4 CLOSED. **N-16-5: BLOCKED IMPLEMENTATION PREREQUISITE
ADJUDICATED — IMPLEMENTATION NOT RESUMED — NOT CLOSED.** N-16-6 / N-16-7 OPEN,
not begun (N-16-7 strictly last). N-23-1 INFO; N-23-2 INFO / DEFERRED — carried
unchanged. `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` —
preserved.

## Governance

`pcae health` healthy · `pcae check` passed · `pcae status coherence` coherent
· `pcae doctor task-memory` warning-only historical `DONE.md` omissions
(pre-existing hygiene debt; no current-phase error) · `pcae runtime inspect`
`not_implemented / Observed / observe / unavailable`, 0/0. Governed `pcae`
lifecycle only — no raw `git commit`/`git push`, no `--no-verify`, no force
push, no history rewrite, no hook bypass. Only the primary human-authorized
operator holds `.1R.30R` lifecycle authority.

## Verdict

```
HPAC-REQ-022/023 PRODUCTION PROTECTED-ADMIN WRITER ANCHOR: ADJUDICATED — NOT BLOCKED
PREFERRED ANCHOR:              OS filesystem write authority on the protected root
                              + non-agent-importable PRODUCTION writer factory
                              (HBDC-001 Class-B precedent, composed)
CONTRACT VERDICT:             NEW COMPANION CONTRACT REQUIRED — recommended HPAC-PAWA-001 v1.0
HPAC-001:                     stays v2.1 (no bump)
RHAMP-001:                    stays v1.0 (byte-unchanged)
HISTORICAL .1R.30:            immutable BLOCKED — never reused, never resumed
FRESH IMPLEMENTATION:         149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2
ADJUDICATION IV:              149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1
N-16-5:                       NOT CLOSED
Runtime:                      Observed / observe / unavailable
First external effect:        ABSENT
```

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1` — Independent Verification of the
`.1R.30R` Production Protected-Admin Writer Anchor Adjudication** (ID
recommended, NOT reserved; requires its own separate explicit human
authorization). Independently re-derive the HPAC-REQ-022/023 gap from source,
the writer-anchor threat model, the candidate rejections, the preferred-anchor
verdict, the contract-versioning verdict (NEW COMPANION CONTRACT), and the
phase-ID derivation. Then `.1R.30R.2` (`HPAC-PAWA-001 v1.0` companion contract
freeze), then `.1R.30R.3` (mechanism + registry + writer-anchor implementation
— the historical `.1R.30` scope), then `.1R.30R.4` (IV) → `.1R.30R.5`
(protected presentation + real-assurance wiring) → `.1R.30R.6` (IV + mandatory
real-CTAP2 hardware + N-16-5 closure). Do not begin N-16-6 / N-16-7 / Slice C;
do not implement or call the first external effect; do not enable execution.

Full analysis:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_HPAC_REQ_022_023_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_ARCHITECTURE_AND_CONTRACT_ADJUDICATION.md`.
