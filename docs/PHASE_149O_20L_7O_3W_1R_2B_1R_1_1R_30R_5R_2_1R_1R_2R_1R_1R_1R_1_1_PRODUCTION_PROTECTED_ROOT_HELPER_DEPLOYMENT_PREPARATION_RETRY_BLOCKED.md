# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1 — Production Protected-Root / Protected-Presentation Helper Deployment Preparation Retry

## Verdict

**BLOCKED — a newly discovered product defect in
`hatp_class_b_topology_verifier.py`'s ACL-based ancestor-chain trust check
structurally prevents the canonical, root-owned HPAC-PPA presentation-
mechanism registration from ever succeeding on this host.**

Phase-entry SHA `A` was `2e416e9bfe8e8711e4c4149b51e617d36e3ed463`, the
finalized `...1R.1R.1R.1` F-9 IV/moving-history-clearance/F-5-retry-ready
head. The entry tree was clean, `origin/main..HEAD = 0`, and runtime was
`Observed / observe / unavailable` with zero plugins and capabilities.

F-5 remains **incomplete / BLOCKED** (not DEPLOYED, not VERIFIED). N-16-5
remains **NOT CLOSED**. No product source, script, or normative contract was
modified in this phase; no repair was attempted.

## What this phase authorized and attempted

Per HPAC-PAWA-001 v1.2, HPAC-PPA-001 v1.0, RHAMP-001 v1.0, and HPAC-001 v2.1,
this phase attempted, as the real out-of-band deployment owner (local macOS
administrator via `sudo`):

1. provisioning the HPAC-PAWA production protected root at the frozen macOS
   path `/Library/Application Support/PCAE/HPAC/protected-root`
   (`resolve_hpac_protected_root()`, `hpac_foundation.py:169-183`), using the
   canonical, unmodified `scripts/hpac_protected_root_admin.py provision`
   tool with `--agent-account atilamadai` (the confirmed, sole real OS
   account under which PCAE runs on this host — no distinct launchd/service
   account exists; verified read-only before mutation);
2. installing the exact, immutable Git-sourced protected-presentation helper
   bytes (`src/pcae/protected_presentation_helper.py`, commit `2e416e9b`,
   blob `d80abf74`, 16295 bytes, SHA-256
   `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`) at
   their canonical content-addressed destination
   (`helper_content_addressed_path`, `protected_presentation_installation.py:465-471`);
3. registering HPAC-PPA-001 generation-1 metadata via the canonical,
   unmodified `scripts/hpac_protected_presentation_admin.py install` tool,
   using operator-approved generation-1 values:
   - `helper_version = pcae-protected-local-presentation-helper/1.0`
   - `renderer_profile = pcae-protected-local-presentation-renderer/1.0`
   - `descriptor_version = pcae-protected-local-presentation-descriptor/1.0`
   - `verifier_config_digest`: SHA-256 of the canonical bytes of
     `{"schema":"v1","verifier_kind":"pcae-protected-local-presentation/1.0"}`,
     serialized with the repository's own
     `pcae.core.hpac_foundation.canonical_json_bytes` convention (sort_keys,
     compact separators, UTF-8) —
     `951182f5e737068d286313903504e34cb3dc57b47a2a19f9031ac068c7992c85`.

Steps 1 and 2 succeeded. Step 3 failed and is the reason this phase is
BLOCKED.

## The newly discovered product defect

`_resolve_trusted_executable()`
(`src/pcae/core/hatp_class_b_topology_verifier.py:591-637`) resolves the
"agent identity" for its own `PATH`-precedence tool-trust walk by calling
`_current_agent_identity()` (`hatp_class_b_topology_verifier.py:143-155`),
which is hardcoded to `os.geteuid(), frozenset(os.getgroups()) |
{os.getegid()}` — the **live process identity** of whatever is currently
executing. This is a *different* identity source than the one the rest of
the production-boundary check correctly uses:
`HPACStoreAuthority._validate_production_boundary`
(`src/pcae/core/hpac_foundation.py:639-661`) resolves `agent_uid, agent_gids`
from the bound `_configured_agent_identity` (the excluded PCAE agent
principal, `atilamadai`/uid 501) when one has been bound via the §33
recognition sequence, falling back to `_current_agent_identity()` only when
none is bound.

`_resolve_trusted_executable` is reached transitively from
`_validate_production_boundary` → `_effective_write_access` →
`_acl_grants_agent_write` → `_acl_grants_agent_write_macos` → looking up a
trusted `ls` binary — but that inner call chain does **not** thread the
already-resolved configured-agent identity through; it independently calls
`_current_agent_identity()` again at `hatp_class_b_topology_verifier.py:602`.

## The semantic identity error

`hpac_protected_presentation_admin.py install` legitimately requires the
**deployment owner** to run it as **root** (via `sudo`) — that is the entire
point of HPAC-PAWA-REQ-010's "only OS principal with real write access to
the protected root" boundary, and it is exactly what
`scripts/hpac_protected_root_admin.py`'s own docstring specifies. Under
`sudo`, `os.geteuid()` is `0`. Root owns essentially every `PATH` directory
on a stock macOS host (`/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`, ...) with
the owner-write bit set (`root:wheel drwxr-xr-x` → `S_IWUSR` set, `st_uid ==
0`). `_mode_and_group_write_access(candidate_dir, agent_uid=0, ...)`
therefore reports **every** `PATH` entry as "agent-writable" whenever the
"agent" being evaluated is literally root itself — which is true, but is the
wrong question: the check exists to ask whether the excluded, unprivileged
**configured PCAE agent principal** (`atilamadai`/uid 501) could tamper with
the resolved tool, not whether the deployment owner (who is *supposed* to
have write access, that being the entire security model) can. Consequently
`_resolve_trusted_executable("ls")` returns `None` (untrusted/indeterminate)
**unconditionally whenever the calling process's live euid is root**,
regardless of `PATH` content, which cascades to `_acl_grants_agent_write_macos`
returning `None`, `_effective_write_access` returning
`(None, "acl_inspection_unavailable", ...)` for every ancestor of the
protected root, and `_ancestor_chain_safe` returning `(None, ...)` (never
provably safe) — which `_validate_production_boundary` correctly treats as
fail-closed (`HPACAuthorityError: protected_root_untrusted`).

## Why this structurally prevents canonical root-owned registration

HPAC-PAWA-REQ-010, HPAC-PPA-REQ-021, and `scripts/hpac_protected_presentation_admin.py`'s
own docstring are unambiguous: the presentation-mechanism registration must
be run by "an operator logged in as the deployment owner — the only OS
principal with real write access to the protected root." On macOS, given the
protected root's ownership model (`root:admin drwx------`, established by
the canonical, unmodified `hpac_protected_root_admin.py provision`), that
operator can only be `root` via `sudo`. Because
`_resolve_trusted_executable`'s tool-trust check evaluates the *live* euid
rather than the *configured agent principal*, and because root's live euid
always satisfies "agent-writable" for ordinary system `PATH` directories,
the ACL-inspection branch of `_ancestor_chain_safe` can **never** return a
determinate result when invoked by the one principal the architecture
requires to invoke it. This is not a configuration or environment problem —
it reproduces identically regardless of `PATH` content (see below) and would
reproduce on any macOS host under this exact, frozen, unmodified tool
inventory.

## PATH/environment manipulation was ruled out as root cause

The failure was first observed under the operator's normal interactive
`PATH` (which has several user-writable directories, e.g.
`~/.kimi-code/bin`, `~/.local/bin`, `/opt/homebrew/bin`, `~/.cargo/bin`,
ahead of `/bin`) and was initially hypothesized to be a `sudo`
`PATH`-inheritance artifact. That hypothesis was independently disproven:

1. `sudo env | grep '^PATH='` confirmed `sudo` on this host does not reset
   `PATH` to a `secure_path` — it passes through the invoking shell's `PATH`
   verbatim.
2. Re-running the registration as
   `sudo env PATH=/usr/bin:/bin:/usr/sbin:/sbin /opt/homebrew/bin/python3
   scripts/hpac_protected_presentation_admin.py install ...` (using the
   absolute interpreter path, since the `pcae` package is only importable
   under Homebrew Python, not `/usr/bin/python3`) reproduced the **identical**
   error.
3. A direct diagnostic,
   `sudo env PATH=/usr/bin:/bin:/usr/sbin:/sbin /opt/homebrew/bin/python3 -c
   "import os; print(repr(os.environ.get('PATH')))"`, confirmed the
   restricted `PATH` genuinely reached the process
   (`'/usr/bin:/bin:/usr/sbin:/sbin'`) — and `_resolve_trusted_executable("ls")`
   still returned `None` under that minimal, non-agent-writable `PATH`.
4. Independent unprivileged reproduction (no `sudo` at all) of the same
   per-entry precedence walk against the operator's normal `PATH` showed the
   *unprivileged* case fails for a different, environmental reason (a
   user-writable directory genuinely precedes `/bin` in that `PATH`) —
   confirming the code's PATH-precedence logic itself behaves as documented
   for a non-root caller. The privileged (root) case fails for the distinct,
   root-cause reason above regardless of `PATH`.

This isolates the defect to the identity source used inside
`_resolve_trusted_executable`/`_current_agent_identity`, not to any `PATH`
or `sudo` configuration on this host.

## No workaround or production repair was attempted

Per this phase's explicit scope boundary ("Expected repository production
source change: NONE... If product source repair becomes necessary: BLOCK.
Do not repair product code inside deployment preparation"), no attempt was
made to:

- patch, monkeypatch, or otherwise alter `hatp_class_b_topology_verifier.py`,
  `hpac_foundation.py`, or any other production module;
- bypass, disable, or relax the ACL-inspection/ancestor-chain check;
- construct an alternative protected-root layout, permission scheme, or
  registration path outside the two canonical, frozen admin scripts;
- retry the registration under a different, non-root identity (which would
  not have real write access to the 0700 protected root and would fail for
  an unrelated, expected reason).

## Exact durable host state at stop

- `/Library/Application Support/PCAE/HPAC/protected-root` — **exists**,
  `root:admin drwx------` (0700), provisioned by the canonical
  `hpac_protected_root_admin.py provision --agent-account atilamadai`:
  PAWA anchor `hpaw-f9661f401f204d828a4aec951855819a`, installation
  `hpawi-bfc91d001ac940b8bda0ed06566180eb`, generation 1,
  `symbolic_account=atilamadai provisioned_uid=501`.
- Protected helper bytes — **installed** at
  `<protected-root>/presentation-helper/installations/933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182/pcae-protected-local-presentation`,
  `root:admin -rw-r--r--` (0644), byte-identical to the immutable Git blob
  `d80abf74` (`src/pcae/protected_presentation_helper.py` at commit
  `2e416e9b`), 16295 bytes,
  SHA-256 `933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182`.
- HPAC-PPA presentation-mechanism installation/current-generation state —
  **absent**. `scripts/hpac_protected_presentation_admin.py status` reports
  "no presentation-mechanism installation" both before and after the
  blocked registration attempt.
- No repository production source, script, or normative contract file was
  modified.
- No `sudo` password, FIDO2 PIN, or other credential was recorded, logged,
  or persisted anywhere in this repository or its evidence.

## No ambiguous or partial PPA registration state exists

`configure_presentation_mechanism`'s registration transaction failed at its
own precondition check (`_validate_production_boundary`, raised before any
descriptor/installation/anchor write was attempted). `status` before and
after the attempt reports the identical "no presentation-mechanism
installation" result. The only durable writes this phase produced are the
PAWA foundation-root provisioning (step 1) and the out-of-band helper-byte
installation (step 2), both of which are idempotent, complete, and
independently reproducible/verifiable artifacts, not partial state.

## F-5 / N-16-5 / runtime status

- **F-5 DEPLOYMENT PREPARATION: BLOCKED** (not COMPLETE, not DEPLOYED).
- **F-5: OPEN / BLOCKED** (unchanged from "OPEN / ABSENT" only insofar as
  the protected-root anchor and helper bytes now durably exist; the
  presentation-mechanism registration that would make F-5 usable does not).
- **N-16-5: NOT CLOSED.**
- Runtime remains `Observed / observe / unavailable`; zero plugins, zero
  capabilities.
- First governed runtime external effect remains **ABSENT / UNREACHABLE**.
- N-16-6 and N-16-7 remain untouched.
- `hpac.fido2.uv_presence.v2` and `pcae-protected-local-presentation/1.0`
  remain supported-not-exclusive; no profile was made globally mandatory.
  The future mechanism-neutral mobile-only authentication/protected-approval
  path remains open, foreclosed by nothing in this phase.
- `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved.

## Scope and no-go proof

- No `src/pcae`, `scripts`, or `docs/contracts` change.
- No new PAWA operation, mutation class, or consumer was created or
  invoked beyond the two frozen, existing admin scripts.
- No protected human election, YubiKey touch, or FIDO2 PIN was requested.
- No presentation evidence, PRODUCTION `AuthenticatedHumanPrincipal`, PB
  permission, or Gate 5/Gate 9 certification was produced or attempted.
- No adapter, dispatch call, runtime capability, or external effect was
  created.

## Required successor adjudication

This phase does not begin a repair successor. The operator must decide,
before any repair phase is opened:

1. whether `_resolve_trusted_executable`/`_current_agent_identity` (and any
   other `hatp_class_b_topology_verifier.py` call sites with the same
   pattern) should accept an explicit, caller-supplied identity parameter
   — threading the already-resolved configured-agent identity down from
   `_validate_production_boundary` — rather than independently re-deriving
   live process identity;
2. the exact blast radius of that change across every other consumer of
   `_effective_write_access`/`_ancestor_chain_safe`/`_resolve_trusted_executable`
   in this module (HBDC/Class-B topology verification generally, not only
   HPAC-PPA), since several of those call sites may share the same
   root-invoked-as-deployment-owner pattern;
3. whether the fix is a MINOR-compatible internal repair (no contract
   surface change) or touches a frozen HBDC-REQ that itself needs
   adjudication;
4. a fresh, independent verification of the repair before any further F-5
   deployment-preparation retry reuses the already-provisioned protected
   root and installed helper bytes recorded above.

The already-provisioned generation-1 protected-root/PAWA-anchor state and
already-installed helper bytes are durable and are **not** to be removed or
reprovisioned merely to obtain a "clean" retry; per HPAC-PPA-REQ-024/027
they are lineage-durable and reusable inputs to a future successful
registration once the defect above is repaired.
