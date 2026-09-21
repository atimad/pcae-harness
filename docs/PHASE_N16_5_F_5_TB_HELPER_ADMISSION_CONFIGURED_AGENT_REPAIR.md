# Phase 150E — N16-5-F-5-TB-HELPER-ADMISSION-CONFIGURED-AGENT-REPAIR

## Phase ID

`150E` (alias **N16-5-F-5-TB-HELPER-ADMISSION-CONFIGURED-AGENT-REPAIR**), a fresh short top-level CPIPC number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), sibling to `150A`-`150D`. Immediate successor to Phase `150D` (N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV, COMPLETE — INDEPENDENTLY VERIFIED).

## Topology / worktree proof

Rooted at `origin/main` == `963f3f45` (150D's own final pushed commit), on local `main` after `git fetch origin && git reset --hard origin/main` (see Authoritative-state preflight below) — `origin/main..HEAD == 0` confirmed before opening this phase.

Historical held/recovery commits (`6c7f5cf4`, `2b8ad2aa`, `72cdba16`, `d0b2a75a`) confirmed absent from this branch's ancestry via `git merge-base --is-ancestor` for all four, before any work began. None touched, cherry-picked, merged, rebased, or published by this phase.

## Authoritative-state preflight (§ mandated by this phase's authorization)

Before this phase's mission work began, local `main` was found diverged from `origin/main`: HEAD was `2b8ad2aa` (2 commits ahead of the `c4c9f554` merge-base, 22 commits behind `origin/main`). The 2 local-only commits were exactly two of the four explicitly-disowned held-IV commits (`2b8ad2aa`, `6c7f5cf4`) — stale local state left over from an earlier, superseded episode; `origin/main` already contained the legitimate Phase 150D completion via an independent lineage (`fb1f0174` ... `963f3f45`).

Per operator authorization, `git fetch origin && git reset --hard origin/main` was run (worktree was clean; no uncommitted work lost). Post-reset: `HEAD == origin/main == 963f3f45`, `origin/main..HEAD == 0`, worktree clean, none of the four forbidden commits in ancestry, `pcae check`/`pcae health` passed/healthy, no active governed phase (only an idle post-150D placeholder task), and `PROJECT_STATUS.md` explicitly named this phase's intent as the recommended next work. All required preflight checks passed before opening `150E`.

## Mission

Reconstruct — from current primary source, not from Phase 150D's prose — the exact configured-agent admission requirement `hpac_pawa_helper_os.authenticate_peer` is contractually bound to, and repair the disclosed defect (`configured_agent` parameter defaults to `None`; the sole production caller never supplies it; the docstring's "defaults to a live resolution" claim is false) with the smallest contract-conformant repair (Model A or B), or STOP with a documented Blocking Finding if no such narrow repair exists.

## Contract state (read directly from `docs/contracts/`, not inferred from prose)

- **HPAC-PAWA-001** — unchanged by this phase (not touched).
- **HPAC-PAWA-HELPER-001 v5.0** (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`) — unchanged. §7 ("The helper's in-process recognition", REQ-031/032/033) and §10 ("Peer authentication", REQ-042-045) are the two normative sections governing this defect. Not modified by this phase (no Blocking contract contradiction was found; the contradiction found is between the contract's requirement and the current *implementation's* incompleteness, not within the contract itself — see Blocking Finding below).
- **HPAC-PPA-001** — unchanged by this phase (not touched).

No drift found between these and the versions cited by Phase 150D's `PROJECT_STATUS.md` entry.

## Reconstruction (primary-source, not docstring-trusting)

**§7 vs §10 — two distinct configured-agent checks exist in the contract, not one.**

- §7 (REQ-031, "the helper's in-process recognition") requires the **exec'd helper child**, in its own interpreter, to run HPAC-PAWA-001 §33 steps 1-8 verbatim — including step 2 (`HPAC-PAWA-AGENT-EXCLUSION/1.0` load, live account resolution, `live uid == provisioned_uid`, live group enumeration, yielding `ConfiguredAgentAuthorityIdentity`) — before it admits any operation. REQ-033 forbids the helper from importing the legacy PAWA factory (`hpac_protected_admin_writer`) for this; it "MAY share a small non-agent-reachable OS-primitives library with the installer scripts" instead.
- §10 (REQ-042, "peer authentication") is a **separate** check run by the **launcher** (the parent process) against the credential of the connecting peer (the exec'd helper), evaluated via `authenticate_peer`. Item 2 of REQ-042 requires "the peer `uid` is not the configured agent principal (`ConfiguredAgentAuthorityIdentity`, §7)" — i.e. §10 explicitly incorporates the **same** `ConfiguredAgentAuthorityIdentity` that §7's step 1-8 recognition establishes. REQ-042 item 4 additionally requires that, on a "topology absent" state (owner and configured agent are no longer distinct accounts), REAL issuance becomes ineligible and the launcher must fail closed — which itself requires knowing the *current* configured-agent identity to detect.

**The disclosed defect is real and is in §10's implementation** (`hpac_pawa_helper_os.authenticate_peer`, called from `hpac_pawa_helper_launcher.py:141` with no `configured_agent` argument): confirmed by direct source read, `configured_agent: Optional[ConfiguredAgentAuthorityIdentity] = None`, and when `None` the `if agent_identity is not None and credential.uid == agent_identity.uid` conjunct is unconditionally skipped — the docstring's claim of a live-resolution default is false; no such resolution is performed anywhere in this function or its caller.

**What identity `configured_agent` must contractually be:** the canonical `ConfiguredAgentAuthorityIdentity`, sourced only from a live, provenance-verified read of `HPAC-PAWA-AGENT-EXCLUSION/1.0` (`pcae.core.hpac_pawa_agent_exclusion.resolve_configured_agent_identity`) — never `os.getlogin()`/`USER`/`LOGNAME`/cwd/executable-basename/module-name/env vars/request-payload strings/filesystem-path labels, and never the launcher process's own `os.getuid()` (the contract's REQ-032 language for §7's steps 3/7 — "never `os.geteuid()`, an ambient root EUID, a `SUDO_*` variable, or a caller parameter" — reflects the same architectural principle that applies to §10's use of the identical `ConfiguredAgentAuthorityIdentity` type: an ambient process-identity shortcut is exactly the class of defect (F-1) this contract exists to prevent, and the launcher's own OS identity is not guaranteed by architecture to equal the *currently* configured agent principal — only the live-resolved record is).

`resolve_configured_agent_identity` (`hpac_pawa_agent_exclusion.py:324`) is **not** a zero-dependency call: it requires the parsed exclusion `document`, `installation_id`, `live_root_identity`, `manifest_root_identity`, and `anchor_agent_exclusion_digest` — all of which are produced today **only** by `hpac_protected_admin_writer._run_recognition_sequence`'s STEP 1 (canonical root resolution via `HPACStoreAuthority.production()`), STEP 4 (manifest read + `{device,inode}` binding), STEP 5 (descriptor read/validate/state check), and STEP 6 (current-generation anchor read/validate) — roughly 70 lines of trust-critical, provenance-checked filesystem reads, all currently private (`_`-prefixed) to that one module.

`hpac_pawa_helper_os.py` already `import`s `ConfiguredAgentAuthorityIdentity`/`resolve_configured_agent_identity` from `hpac_pawa_agent_exclusion` (the REQ-033-permitted "small non-agent-reachable OS-primitives library"), but that import is currently **dead code** — nothing in the module supplies the inputs `resolve_configured_agent_identity` needs. No equivalent read-only assembly of those inputs exists anywhere on the launcher/helper side of the codebase (confirmed: no call to `resolve_configured_agent_identity` exists outside `hpac_protected_admin_writer.py`; `hpac_pawa_helper_entrypoint.py` and `hpac_pawa_helper_store_adapter.py` implement no part of §33 steps 1-8 at all — that is a separate, larger, un-implemented requirement (REQ-031) outside this phase's authorized scope).

The read chain itself (`HPACStoreAuthority.production()` construction, `.root` attribute access, and the subsequent plain `stat()`/JSON reads) does **not** invoke `_ensure_root`/`_validate_production_boundary` — confirmed by direct source read of `HPACStoreAuthority.__init__` (no boundary call) and by the precedent recorded in `[[project_pcae_latest]]`'s N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL finding that read-only methods never call `_ensure_root`. So this is **not** the same blocked write-boundary defect as that phase — it is a distinct problem: the *read*-side recognition sequence that produces `ConfiguredAgentAuthorityIdentity` is real, working, provenance-verified code, but it exists in exactly one place (inside the forbidden legacy factory) and nowhere the helper/launcher is permitted to reach.

## Blocking Finding

A genuinely narrow, contract-conformant repair (Model A or Model B) is **not achievable within this phase's authorized scope**, for the following reason:

Both models require the launcher (or `authenticate_peer` itself) to obtain a live, provenance-verified `ConfiguredAgentAuthorityIdentity` before admission. The only existing implementation of that provenance-verified read chain is `hpac_protected_admin_writer._run_recognition_sequence`'s STEP 1/4/5/6, which:

1. **Cannot be imported** — `HPAC-PAWA-HELPER-REQ-033` forbids the helper from importing `hpac_protected_admin_writer` or any agent-reachable module, and this chain lives entirely inside that module, not inside the permitted `hpac_pawa_agent_exclusion` "small non-agent-reachable OS-primitives library."
2. **Cannot be safely duplicated** — re-implementing ~70 lines of trust-critical, provenance-checked manifest/descriptor/current-generation/exclusion-record reading logic as a second, independent copy inside `hpac_pawa_helper_os.py` would create exactly the "parallel identity truth source" / "two divergent [resolution] sources" pattern this phase's authorization explicitly forbids ("Do NOT add parallel identity truth sources") and that the codebase's own existing precedent explicitly guards against elsewhere (`resolve_launcher_deployment_metadata`'s docstring: "reusing the exact same read-only resolver ... one canonical source ... never two divergent ones"). A second, separately-maintained implementation of manifest/descriptor/anchor provenance validation is a structural trust-boundary risk, not a narrow bug fix.
3. **Cannot be resolved by refactoring the shared chain out into common infrastructure either** — extracting STEP 1/4/5/6 of `_run_recognition_sequence` into a module both the legacy factory and the helper could safely import is exactly the class of change this phase's authorization designates out of scope ("HPAC foundation/root-boundary repair", "general helper admission redesign") and that HPAC-PAWA-HELPER-REQ-033's own governance history (§30A.4/§30B.15, "Models A/B/C evaluated and not selected" at the module-boundary level) shows was already a considered and not-yet-authorized design question at the project level, not one this narrow phase is authorized to decide.
4. **Is not a case of "no verified value is available so trust something weaker instead"** — REQ-031 (the full §33 in-process recognition inside the exec'd helper child) is itself not implemented anywhere in the current codebase (confirmed: no call to `resolve_configured_agent_identity` in `hpac_pawa_helper_entrypoint.py` or `hpac_pawa_helper_store_adapter.py`). Implementing genuine live resolution for `authenticate_peer` alone, without REQ-031's own missing in-helper recognition, would produce two independently-evolving partial implementations of the same requirement rather than one authoritative one — worse, not better, trust architecture.

Per this phase's own STOP conditions ("the repair necessarily requires foundation/root-boundary changes"; "helper provisioning implementation becomes necessary" (REQ-031 is exactly this class of un-implemented provisioning-adjacent admission infrastructure)), this phase **STOPS** rather than implementing a repair that would either import the forbidden factory, fabricate a second trust-critical reading path, or silently reinterpret REQ-033's module-boundary disposition.

**Explicit answers required by this phase's authorization:**

- Can `configured_agent=None` still reach successful helper admission today? **Yes, unchanged by this phase.** `authenticate_peer`'s `None` default still causes the peer-≠-configured-agent conjunct to be silently skipped; production's sole caller (`hpac_pawa_helper_launcher.py:141`) still supplies nothing. This phase did not weaken or strengthen that behavior — it remains exactly as Phase 150D disclosed it, because no safe repair was available within scope.
- Is any caller-supplied `configured_agent` value trusted directly? **No.** No caller (in this phase or otherwise) is authorized to construct a `ConfiguredAgentAuthorityIdentity` from unverified input; the type still requires construction through `resolve_configured_agent_identity`'s validated dataclass, which no reachable caller does today.
- Is the configured-agent identity resolved live, verified, or merely descriptive today? **None of the above — it is simply absent.** No code path on the launcher/helper side computes it at all; `authenticate_peer`'s parameter is never populated by any production caller.

## No source changes

Zero `src/pcae/**` changes. Zero `docs/contracts/**` changes. This phase performed reconstruction and analysis only, per its own disposition of STOP. Confirmed by `git diff --stat` against this phase's entry commit (`963f3f45`, `origin/main`) restricted to those paths (empty).

## Runtime posture

Observed / observe / unavailable — unchanged throughout. No real production external effect was performed or authorized. `helper admission != human approval != PB ALLOW != runtime capability != external-effect permission` preserved; this phase changes none of those relationships (it changes nothing executable at all).

## Regression sweep / Fast Green

Not applicable in the ordinary attributable-failures sense: this phase makes zero `src/pcae/**` or `docs/contracts/**` changes, so there is no candidate diff for Fast Green to attribute failures against. `pcae check` and `pcae health` were re-run after finalizing this evidence doc and before commit; both passed / healthy.

## N-16 state

N-16-5 remains **NOT CLOSED**. The disclosed `authenticate_peer` `configured_agent=None` admission gap remains open and unrepaired (STOP, not fixed). N-16-6/N-16-7: untouched.

## Disposition

**STOP — HELPER CONFIGURED-AGENT ADMISSION REPAIR BLOCKED (no contract-conformant narrow repair available within this phase's authorized scope).**

Recommended next: this defect cannot be closed without one of (a) a dedicated phase authorized to implement REQ-031's currently-missing in-helper §33 step 1-8 recognition (the exec'd helper child performing its own live resolution, "in its own interpreter", as the contract already requires independently of `authenticate_peer`), which would then make a genuine `ConfiguredAgentAuthorityIdentity` available to thread into `authenticate_peer` as Model B describes; or (b) a dedicated, explicitly-authorized module-boundary/shared-infrastructure phase that extracts the read-only portion of `_run_recognition_sequence` (STEP 1/4/5/6) into a module both the legacy PAWA factory and the helper may safely import, resolving REQ-033's module-boundary question at the project level rather than inside a narrow implementation phase. Neither (a) nor (b) is begun by this phase. N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — this phase's reconstruction, analysis, and evidence authorship were performed directly by the primary operator; no delegated fork was used for this phase's central claims. All lifecycle mutation, finalization, commit, and push were performed directly by the primary operator.
