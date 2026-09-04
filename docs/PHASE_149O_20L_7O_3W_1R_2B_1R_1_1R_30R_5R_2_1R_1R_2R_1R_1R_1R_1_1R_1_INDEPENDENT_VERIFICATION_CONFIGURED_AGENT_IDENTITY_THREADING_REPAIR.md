# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1 — Independent Verification of the Configured-Agent-Identity Threading Repair

## Scope

Verification-only. Independently adjudicates whether the predecessor
repair phase's (`...1.1R`, commits `8407dd24`/`8521b9c0`) fix to
`src/pcae/core/hatp_class_b_topology_verifier.py` correctly threads the
CONFIGURED PCAE agent principal — never the live process's ambient
identity — through the ACL-tool-trust sub-decision. No production
repair, no F-5 continuation, no host/protected-root mutation, no
human/YubiKey ceremony performed in this phase.

## Lineage

- IV entry SHA (`V`) = `67d542ef` (== predecessor repair phase's
  finalized endpoint, `R_FINAL`)
- Predecessor repair phase-entry SHA (`R_ENTRY`) = `9d04603e`
- Production repair commit (`R_CHANGE`) = `8407dd24`
- Test-only follow-up commit = `8521b9c0` (independently confirmed to
  touch no production file)
- Production diff scope, independently re-derived: exactly one file,
  `src/pcae/core/hatp_class_b_topology_verifier.py` (+104/-2 lines,
  net one new function `_resolve_trusted_executable_for_subject`; no
  other `def` added or removed)

## Independent consumer inventory

`_current_agent_identity()` (the ambient-identity primitive) has
exactly three call sites in the module, independently re-derived by
AST walk (not the predecessor's own inventory):

| Caller | Classification | Evidence |
|---|---|---|
| `_resolve_trusted_executable` | `LIVE_PROCESS_SUBJECT` | Frozen since 149O.20J.1/.2 (byte-diff-pickaxed); sole caller `_resolve_trusted_executable_with_effective_access` is consumed only by `hatp_environment_lock_verifier.py`'s own-environment `git` check, which has no configured-agent notion |
| `_resolve_trusted_executable_with_effective_access` | `LIVE_PROCESS_SUBJECT` | Byte-unchanged since repair entry (`git diff -G` pickaxe verified) |
| `verify_class_b_topology_conformance` (public entry) | `LIVE_PROCESS_SUBJECT` | Non-authoritative diagnostic by module/aggregator docstring; independently grepped repo-wide — imported only by `hatp_class_b_topology_verifier.py` itself and the equally non-authoritative `hatp_class_b_conformance.py` aggregator; never by `hpac_protected_admin_writer.py`, `hatp_mandatory_cutover.py`, or any certification path |

Zero relevant `AMBIGUOUS_REQUIRES_CONTRACT_DERIVATION` consumers remain.

The actually production-relevant, previously-defective subtree —
`_effective_write_access` → `_acl_grants_agent_write` →
`_acl_grants_agent_write_linux`/`_acl_grants_agent_write_macos` —
independently re-derived to now call `_resolve_trusted_executable_for_
subject(name, agent_uid, agent_gids)` exclusively; neither helper's
source references `_current_agent_identity` or the bare
`_resolve_trusted_executable` any longer (confirmed by
`inspect.getsource` substring scan in the fresh IV suite).

## Production call boundary (already correct, unchanged)

Independently re-derived from `hpac_protected_admin_writer.py`: the
canonical HPAC-PPA registration path passes
`configured_agent.uid`/`configured_agent.gids` — resolved by
`hpac_pawa_agent_exclusion.resolve_configured_agent_identity()` from
the protected `HPAC-PAWA-AGENT-EXCLUSION/1.0` record via a live
`pwd.getpwnam()` lookup that fails closed on any
`live_uid != provisioned_uid` mismatch — into `_effective_write_access`
/ `_ancestor_chain_safe`. This boundary was already correct before the
repair (item 8 of the governing prompt); the repair's only change was
closing the *internal* ACL-tool-resolution leak that silently
substituted ambient identity for one sub-decision. `resolve_
configured_agent_identity` never itself calls `os.geteuid()` (AST-walk
verified) and its only caller-controlled seam,
`_configured_agent_identity_source`, is a disclosed test-only fixture
(default `None` in production) that itself still enforces the
uid-match fail-closed invariant when used.

## Central repair proof

With the ambient identity monkeypatched to a poisoned root-like `(0,
{0})` and `PATH` pointed at `/usr/bin:/bin`, `_acl_grants_agent_write_
macos`/`_linux` for a distinct, explicitly-passed real subject resolve
deterministically (`False`, not `None`/indeterminate) — reproducing
the fix for the exact `acl_inspection_unavailable` symptom that blocked
the immediately preceding F-5 retry. The same poisoning applied to the
still-frozen, still-present *ambient-only* `_resolve_trusted_executable`
independently reproduces the historical defect on this host (`/usr/bin`
is root-owned and owner-writable here, so a root-like ambient subject
resolves `None`), confirming the defect was real, specific to identity
threading, and not a PATH/tooling artifact.

## Matrix coverage (fresh IV suite)

Owner/group/other write, direct-subject vs. non-owning-subject
resolution, unsafe-earlier-PATH-entry rejection, root-only-preceding-
directory non-rejection, tool-writable-by-agent rejection, no
`euid == 0` special case anywhere in the module (source scan), no
hardcoded system-directory allowlist (source scan), and preservation of
the two legitimate `LIVE_PROCESS_SUBJECT` callers — all independently
exercised; see the fresh suite for the full list (38 passed, 3
environment-conditional skips with disclosed skip reasons).

## Regression

- Fresh IV suite: 38 passed / 3 skipped
- Predecessor repair suite (unchanged, rerun as-is): 68 passed
- Full Class-B topology/environment-lock/conformance regression band
  (13 files): 37 pre-existing failures — independently reproduced
  byte-identical against the fixed `R_ENTRY` baseline in a disposable
  detached worktree (all "zero production consumers" / "not in HMIC
  frozen scope" point-in-time guards, stale since the topology module
  became a real PAWA consumer in an earlier, unrelated phase) — zero
  attributable to this repair or this IV
- PAWA/RHAMP/hpac_verifier/Gate 5/Gate 9 band: 2 pre-existing failures
  (`hpac_verifier` `object.__new__` trusted-construction-seal bypass,
  unrelated to this module) — independently reproduced byte-identical
  at `R_ENTRY` in the same disposable worktree; 672 passed
- Full repository suite: run to completion as part of this phase's
  regression gate; see governance results below for the final count

## Contracts / dependencies

`docs/contracts/` and `pyproject.toml`: byte-unchanged since
`R_ENTRY` (`git diff --stat`/`git diff`, both empty).

## Host state (read-only)

Protected root exists at the expected path, `stat`-confirmed
root-owned, mode `700` (no group/other access, uid 501 not owner) —
consistent with the expected generation-1 state and itself
demonstrating the trust boundary this repair concerns. Content-level
inspection (anchor JSON, helper digest, PPA installation/current-
generation descriptors) was attempted read-only and returned
`Permission denied` for this non-privileged uid — expected by design;
no elevated privileges were requested or used, and no mutation was
attempted. No PPA registration retry, protected-root provisioning, or
generation change was performed.

## Verdict

**CONFIGURED-AGENT-IDENTITY THREADING REPAIR: INDEPENDENTLY VERIFIED.**

All twenty verdict conditions of the governing prompt (§49) are
satisfied: full independent consumer inventory reconstructed; zero
relevant ambiguity; configured-agent subject proven to derive from
canonical protected-record authority, never ambient/env/CLI input;
arbitrary-subject substitution impossible (fail-closed on uid
mismatch); root-like ambient identity no longer poisons the
configured-agent ACL/trust decision while genuine configured-agent
write authority is still detected across owner/group/other/ACL;
trusted-executable resolution and PATH-precedence semantics correct
and unchanged in shape; no root bypass or system-path allowlist
introduced; the two legitimate live-process callers preserved
unperturbed; production diff narrowly bounded to the one file; no test
weakening; contracts/dependencies unchanged; existing generation-1 host
state untouched; no F-5 registration retry performed.

**F-5 CONTINUATION: READY** — meaning only that a fresh, separately
authorized continuation phase may retry the previously blocked PPA
registration step against the already-existing generation-1 state. It
does not mean F-5 verified, N-16-5 closed, or any human/YubiKey
certification complete.

**N-16-5: NOT CLOSED.** N-16-6/N-16-7: untouched.

## Derived (not begun) F-5 continuation successor

Conceptual next phase ID: a fresh CPIPC-valid successor under this same
branch (e.g. `...1R.1.1R.1.1`), titled *Production Protected-Root /
Protected-Presentation Registration Continuation Against Existing
Generation-1 Deployment State*. Not begun in this phase.

## Runtime / effect boundary

`pcae runtime inspect`: `not_implemented` / `Observed` / `observe` /
`unavailable`; 0 plugins; 0 capabilities. First governed runtime
external effect: absent / unreachable.
