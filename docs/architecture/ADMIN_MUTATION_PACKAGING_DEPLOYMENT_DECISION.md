# admin_mutation Packaging / Deployment Topology Decision

**Canonical Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1
**Display alias:** N16-5-F-5-TB-ADMIN-MUTATION-PACKAGING-DECISION
**Predecessor Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1
**Predecessor alias:** N16-5-F-5-TB-CALLER-MAP-CORRECTION (COMPLETE)
**Type:** Architecture / decision only. No production source, packaging, contract, schema, or live-host mutation.

## 0. CPIPC identity validation

- Predecessor Phase ID independently confirmed via `.pcae/phase-reports/latest.json` (`phase_id`, `status: completed`) and `.pcae/phase-completion-metadata.json` (`phase_id`, `recommended_next_phase` matching this phase's scope).
- Successor derived as the predecessor's canonical text plus one appended numeric subphase segment (`.1`), following this repository's established convention of appending a numeric segment for the next governed phase in an unbroken chain. Validated parseable by `pcae.core.phase_id.parse` (CPIPC-001 v1.0 grammar). Checked against the full `git log --all` history: no prior commit or report references this exact successor string — unique, no collision.
- Predecessor terminal result: COMPLETE. No conflicting active governed phase existed at start (repo clean, `origin/main..HEAD` = 0, single lock held by `claude-local`).

## A. Current admin script reachability map

| Script | Subcommands | Production modules imported | Write authority path |
|---|---|---|---|
| `scripts/hpac_principal_admin.py` (116 lines) | `enroll-first-credential`, `revoke-credential` | `pcae.core.hpac_rhamp_enrollment` (`enroll_first_credential`, `revoke_credential`), `pcae.core.hpac_rhamp_ctap2` | `production_writer()` → `HPACStoreAuthority` (in-process), via `hpac_rhamp_enrollment.py:188/447` |
| `scripts/hpac_protected_presentation_admin.py` (126 lines) | `install`, `rotate`, `revoke`, `status` (read-only) | `pcae.core.hpac_protected_presentation_admin` (`configure_presentation_mechanism`, `resolve_current_presentation_generation`); `status` also imports `hpac_foundation.HPACStoreAuthority` | `production_writer()` → `HPACStoreAuthority` (in-process), via core module line 114 |
| `scripts/hpac_protected_root_admin.py` | `provision`, `set-agent-exclusion`, `rotate`, `revoke`, `enroll-principal`, `revoke-principal` | `pcae.core.hpac_protected_admin_writer` directly | Same `production_writer()` / `HPACStoreAuthority` path |
| `scripts/hpac_certification_admin.py` | `describe` (read-only), `status` (read-only) | `pcae.core.hpac_foundation.HPACStoreAuthority` (read-only use only) | No mutation — read-only; not an admin-mutation caller |

**Correction to the predecessor caller-map claim (material fact, independently verified):** the predecessor phase's "two scripts, the only helper-operation callers with live non-test callers" claim undercounts by at least one. `scripts/hpac_protected_root_admin.py` also performs real protected-state mutations (`provision`/`set-agent-exclusion`/`rotate`/`revoke`/`enroll-principal`/`revoke-principal`) through the identical `production_writer` factory, confirmed by direct grep and read. `scripts/hpac_certification_admin.py` also imports the same authority module but only for read-only `describe`/`status` — it is **not** a mutation caller and does not change the predecessor's substantive conclusion. Four additional `scripts/hatp_*_admin.py` scripts exist but import an unrelated subsystem (`pcae.core.hatp_*`, Hardware Attestation Trust Protocol) and do **not** touch `production_writer`/`HPACStoreAuthority` — out of scope for this decision.

This correction does not invalidate the predecessor's COMPLETE status or this phase's ability to proceed: it refines the reachability map (three live mutation-capable scripts, not two) without changing the packaging/topology question itself, since `hpac_protected_root_admin.py`'s operations are classified below under the same "installation/registration" bucket as `hpac_protected_presentation_admin.py`'s `install`/`rotate`/`revoke`.

## B. Protected admin mutations inventory

| Mutation | Script | Classification |
|---|---|---|
| Root provision / agent-exclusion / rotate / revoke | `hpac_protected_root_admin.py` | Deployment-owner bootstrap — inherently out-of-band |
| Principal enroll / revoke (via root admin script) | `hpac_protected_root_admin.py` | Bounded protected principal administration (§38 cat. 1) |
| First-credential enrollment / credential revocation (FIDO2 ceremony) | `hpac_principal_admin.py` | Enrollment — requires real hardware, no deterministic fixture path in production code |
| Presentation-helper metadata install / rotate / revoke (`helper_sha256`, version, digests) | `hpac_protected_presentation_admin.py` | Configuration / registration-only — never installs, copies, or executes helper bytes itself |

None of these are certification-prerequisite operations in the sense of performing certification; they are prerequisites **to** eventually performing certification (F-5).

## C. Packaging facts (re-derived directly from `pyproject.toml`)

- Wheel: `[tool.hatch.build.targets.wheel] packages = ["src/pcae"]` — only `src/pcae` ships.
- Console scripts: `[project.scripts] pcae = "pcae.cli:main"` — exactly one entry point; no admin/helper launcher entry point exists.
- Sdist: `[tool.hatch.build.targets.sdist] include = ["/src/pcae", "/README.md", "/LICENSE", "/pyproject.toml"]` (root-anchored).
- `scripts/` is excluded from **both** the wheel and the sdist. No admin/helper launcher or helper executable is packaged in either artifact today.
- Build backend pinned `hatchling==1.32.0` for byte-identical reproducibility.

## D. Wheel-only feasibility

A machine with only `pip install <wheel>` and no source checkout **cannot** run any of the three mutation-capable scripts — they are not present in the wheel at all. All F-5 prerequisite admin operations currently require a source checkout. This is an intentional design ("non-agent-importable" fence stated in `hpac_protected_admin_writer.py`'s own docstring), not an oversight.

## E. Sdist feasibility

Identical conclusion to D: `scripts/` is absent from the sdist include list, so an `sdist` install exposes no more than the wheel does for these operations — installing from source distribution does not implicitly install the scripts merely because they exist in the original repository.

## F. Editable-install gap analysis

An editable install (`pip install -e .`) exposes the full repository tree on `sys.path`, including `scripts/`, which a real wheel/sdist install never does. Today this creates no masking risk because no packaged admin command exists to be silently different — but it means a developer's local experience (scripts importable and runnable) diverges completely from what any real install provides, which must stay explicit in any future documentation.

## G. Actor / privilege matrix

| Actor | Root provision/rotate/revoke | Principal enroll/revoke (via root script) | Credential enroll/revoke (FIDO2) | Presentation metadata install/rotate/revoke |
|---|---|---|---|---|
| Deployment owner | Required — sole actor | Required — sole actor | Required — sole actor | Required — sole actor |
| Ordinary PCAE user | Never | Never | Never | Never |
| Configured agent | Never (fence: not importable from `cli.py`/`commands/**`/`core/agent.py`) | Never | Never | Never |
| Human principal (post-enrollment) | N/A | N/A | Subject of the enrollment, not the operator | N/A |
| CI / operator | Never | Never | Never | Never |

Real security boundary is OS filesystem write permission on `<HPAC_PROTECTED_ROOT>` (HPAC-PAWA-REQ-010), not any in-application check.

## H–K. Model evaluation

### Model A — Source-checkout-only (status quo)
Requires zero change; scripts already satisfy it. Smallest attack surface (trusted, single-operator, non-networked, non-packaged). No package-level provenance signal exists or is needed since nothing ships. Leaves the HPAC-PAWA-001 v2.0 contract-vs-implementation gap (see below) open indefinitely with no stated path forward — acceptable as an interim state, not a stable end state.

### Model B — Installed-package admin tools
Would require moving `production_writer`/`HPACStoreAuthority` logic into `src/pcae` and adding a real `pcae hpac ...` entry point. **Rejected.** This directly regresses the existing least-authority fence (`hpac_protected_admin_writer.py`'s own docstring frames its trust boundary as agent-non-importability, enforced by guard tests against `cli.py`/`commands/**`/`core/agent.py`) by shipping privileged same-interpreter write authority to every installer of the general-purpose package. It also moves directly against **HPAC-PAWA-001 v2.0** (already frozen, confirmed at `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` line 6-7, `Version: 2.0`, `Status: FROZEN`), which already requires privileged production operations to execute out-of-process, not packaged in-process.

### Model C — Typed admin client over the verified helper protocol
Strongest provenance (verify helper bytes' SHA-256 before exec) and least authority (calling process never holds `HPACStoreAuthority`; only the short-lived one-shot helper process does). Safely packageable in `src/pcae` because the client itself holds no authority object. Directly exposes the real macOS gap: `src/pcae/core/hpac_pawa_helper_os.py`, function `execute_verified` (confirmed by direct read, lines ~136-158), re-execs via `/proc/self/fd/<fd>` on Linux only; on any other platform (including macOS) it raises `UnsupportedPlatformProfile` — fails closed rather than weakening the guarantee, per `HPAC-PAWA-HELPER-REQ-029/104`. **Not yet buildable as a complete migration target**: `HPAC-PAWA-HELPER-001` v1.0 (confirmed FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING) is foundation-only; `hpac_pawa_helper_protocol.py`/`hpac_pawa_helper_operations.py` are not wired to the real canonical stores and no launcher exists. Model C alone is also incoherent for helper **installation** itself — there is nothing to verify a request against during install.

### Model D — Explicit split (selected)
See §L.

## L. Selected operational topology: Model D (explicit split)

- **Stays source-checkout-only, indefinitely** (Model A): helper/root installation and registration operations — `hpac_protected_root_admin.py`'s `provision`/`set-agent-exclusion`/`rotate`/`revoke`, and `hpac_protected_presentation_admin.py`'s `install`/`rotate`/`revoke` metadata-registration subcommands. These pin trust in bytes/state a deployment owner already placed out-of-band (HPAC-PPA-REQ-004/010 already require this to be an out-of-band act); there is no principled way to "package" an operation whose entire point is registering trust in something installed outside the package.
- **Migrates to a packaged typed client over the verified helper protocol** (Model C), once `HPAC-PAWA-HELPER-001` is implemented and wired to real stores: `hpac_principal_admin.py`'s `enroll-first-credential`/`revoke-credential`, and `hpac_protected_root_admin.py`'s `enroll-principal`/`revoke-principal`.

**Rationale:**
1. `HPAC-PAWA-001` is already v2.0 and already requires out-of-process execution for privileged production operations — Model B is rejected on this basis alone.
2. Model A alone never closes the contract-vs-implementation gap and states no path forward.
3. Model C alone is incoherent for the genuinely out-of-band installation step — some sliver of Model A is structurally permanent, not a temporary status quo. Model D names that sliver explicitly (an exact, testable boundary: "does this subcommand register/administer the helper's own existence, or does it request a bounded operation from an already-verified helper") rather than leaving the split vague.

**Rejected alternatives:** Model A alone (leaves the v2.0 contract-implementation gap unaddressed indefinitely); Model B (regresses least authority, ships privileged-authority code to every installer, contradicts HPAC-PAWA-001 v2.0's own frozen direction); Model C alone (incoherent for the installation step).

## M. Helper-byte provenance model

Package version is explicitly **not** the provenance signal. The pinned `helper_sha256` digest (registered via the presentation-admin script's metadata-only registration) is the provenance signal, verified by `hpac_pawa_helper_os.py` before any exec. Package version and helper provenance must never be conflated (see threat #15/#12 below).

## N. Launcher packaging model

Not yet designed in detail — deferred to the recommended next phase (§T), since no store-wired helper operations exist yet for a launcher to invoke. When built, it must remain a Linux-first, one-shot, verify-then-exec launcher per the existing `execute_verified` primitive; no permanent privileged daemon.

## O. Typed admin-client placement model

Deferred until after the helper-wiring/launcher phase (§T). When built: lives in `src/pcae` as an authority-free, closed-vocabulary (5 operations, 7 admin-mutation subtypes) typed request/response client; internal production API, not a generic broker; fails closed if the helper is unavailable or rejects, never falls back to `production_writer`.

## P. macOS implications

Real helper same-file-object execution remains **FAIL-CLOSED / NOT IMPLEMENTED** on macOS (code-confirmed, not inferred). Source-checkout admin tools may continue operating on macOS through the existing in-process `production_writer` path in the interim (Model D's permanent source-only sliver), but the Model C migration path is Linux-only until a substitution-free exec primitive exists for macOS — not designed or implemented here.

## Q. Linux/Dell implications

Dell Ubuntu remains the deployment target for real F-5 certification and is the only platform on which `execute_verified` currently succeeds. The recommended next phase (§T) should target Linux first. No live Dell mutation, SSH, or deployment action was performed in this phase.

## R. Legacy authority sunset plan

`production_writer`/`HPACStoreAuthority` in-process authority is retired **only** for the operations that migrate to the typed client (`enroll-first-credential`/`revoke-credential`, `enroll-principal`/`revoke-principal`), and only after the helper-wiring/launcher phase and the typed-client phase both land. The installation/registration sliver (`provision`/`set-agent-exclusion`/`rotate`/`revoke` on the root; `install`/`rotate`/`revoke` metadata on presentation) keeps using `production_writer` **permanently** — this is a deliberate, contract-consistent permanent state, not an indefinitely-deferred migration.

## S. F-5 dependency graph (corrected)

```
Helper foundation (HPAC-PAWA-HELPER-001 v1.0 frozen; protocol/operations/os
modules exist, store-unwired, no launcher — DONE)
        |
        v
Packaging / deployment decision  <-- THIS PHASE (Model D selected)
        |
        v
Helper store-wiring + out-of-process launcher (Linux-first)  <-- RECOMMENDED NEXT, not begun
        |
        v
Typed admin client implementation (Model C slice)
        |
        v
Migrate enroll-first-credential/revoke-credential (hpac_principal_admin.py)
and enroll-principal/revoke-principal (hpac_protected_root_admin.py) onto
the typed client
        |
        v
Legacy authority retirement for the migrated operations only
(installation/registration subcommands keep production_writer permanently)
        |
        v
Deployment verification (real Linux/Dell host, real helper subprocess,
real FIDO2 ceremony end-to-end)
        |
        v
Real certification (N-16-5 closure)
```

## T. Exact next governed slice

**Recommended next phase (not begun):** wire the foundation-only helper protocol (`hpac_pawa_helper_protocol.py`/`hpac_pawa_helper_operations.py`) to the real canonical stores (`HumanPrincipalRegistryStore`, RHAMP, `ProtectedPresentationInstallationStore`) and build the actual out-of-process one-shot launcher, Linux-first. This must precede any typed-client or packaging implementation, since there is currently nothing store-wired for a client to call. Must not touch `hpac_principal_admin.py` or `hpac_protected_presentation_admin.py` themselves — those migrate only in the phase after this one.

## Threat / failure matrix

| # | Threat/failure | Exposure under selected Model D |
|---|---|---|
| 1 | Wrong-commit source checkout used for an admin op | Applies only to the permanently source-only installation/registration sliver; no version pin beyond git |
| 2 | Editable install masking a missing packaged command | Applies only to the future packaged half once it exists; low risk (client is authority-free, typed version mismatch is detectable) |
| 3 | Wheel user unable to invoke a required admin op | By design for the bootstrap sliver; fixed for routine ops once the typed client lands |
| 4 | Packaged command silently falls back to legacy writer | Explicitly forbidden by design constraint carried into the packaged half |
| 5 | Generic admin client exposes arbitrary `admin_mutation` payload | Closed by design — `CLOSED_OPERATIONS` (5, asserted `len==5`) and `CLOSED_ADMIN_MUTATIONS` (7 named values) are asserted closed sets at import time in `hpac_pawa_helper_protocol.py` |
| 6 | Helper bytes differ from registered/pinned digest | Mitigated by verify-then-exec SHA-256 check in `hpac_pawa_helper_os.py`, packaged half only |
| 7 | Packaged launcher reopens helper pathname after verification (TOCTOU) | Mitigated on Linux via `/proc/self/fd/<fd>` re-exec of the verified descriptor; fails closed (not silently open) on macOS |
| 8 | Deployment-owner vs. configured-agent identity conflation | Mitigated today by the non-agent-importable fence; would be mitigated in the packaged half by the helper's own peer-credential authentication — never reintroduced by Model D since Model B was rejected |
| 9 | Ordinary user obtains deployment-owner authority | Mitigated by OS filesystem write-permission check (HPAC-PAWA-REQ-010), unchanged by this decision |
| 10 | macOS silently downgrades to a non-verified helper path | Explicitly not silent — `UnsupportedPlatformProfile` raised, fails closed |
| 11 | Source-only scripts persist indefinitely after a packaged model is chosen | Explicitly scoped: the bootstrap sliver is meant to persist forever (documented); routine-op scripts are meant to retire once the typed client lands, tracked via §S |
| 12 / 15 | Package version mistaken for helper provenance | Mitigated — `helper_sha256` is the provenance signal, not package version; not applicable to the source-only half (no package version claim made there) |
| 13 | Source-only scripts remain indefinitely after packaged model chosen | Same as #11 — deliberate for the bootstrap sliver, tracked (not accidental) for the routine-op scripts |
| 14 | sdist includes a file but installation doesn't expose an executable | N/A today — `scripts/` is excluded from the sdist include list entirely, not merely non-executable |
| 16 | Mutable source checkout used as a production trust root | Applies to the permanent bootstrap sliver; mitigated only by OS write-permission + operator discipline, unchanged from today |
| 17 | Admin tool performs real authentication without protected-presentation separation | Not applicable — `hpac_principal_admin.py`'s FIDO2 ceremony and presentation metadata registration remain architecturally separate scripts/modules, unchanged by this decision |
| 18 | FIDO2 mechanism accidentally made mandatory | Not made mandatory by this decision; mobile-friendly future authentication mechanisms remain unforeclosed since Model C's transport is mechanism-agnostic at the protocol layer |
| 19 | Recovery operation becomes a replay-reset capability | No recovery/reconciliation admin operation was found reachable through the two/three scripts examined; none introduced by this decision |
| 20 | Helper failure triggers the old in-process path | Explicitly forbidden — fail-closed is mandatory for any future migrated caller; no legacy fallback permitted |

## Contract scope (read-only confirmation, no changes made)

- **HPAC-PAWA-001** — v2.0, FROZEN (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`). Already requires out-of-process execution for privileged production operations.
- **HPAC-PAWA-HELPER-001** — v1.0, FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`). Foundation only; no live launcher, no store wiring.
- **HPAC-PPA-001** — v2.0, FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING (`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`). Already moved presentation-evidence writes into the helper process at the contract level; the current script/module reflects the pre-v2.0 metadata-only registration architecture.

No contract, schema, or dependency was modified in this phase.

## Compliance confirmation

- Production source changes: **NONE**.
- Packaging changes: **NONE**.
- Contracts changed: **NONE**.
- Schemas/dependencies changed: **NONE**.
- Live protected-host writes: **0**.
- Real ceremony: **NOT PERFORMED**.
- Runtime state: Observed / observe / unavailable (unchanged).
- Plugins/capabilities: 0/0 (unchanged).
- First governed runtime external effect: ABSENT/UNREACHABLE (unchanged).
- N-16-5: **NOT CLOSED**. N-16-6 / N-16-7: **OPEN / UNTOUCHED**.
- Successor (the helper store-wiring/launcher phase in §T): **NOT BEGUN**.
