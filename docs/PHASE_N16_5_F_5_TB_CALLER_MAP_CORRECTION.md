# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-CALLER-MAP-CORRECTION)

**Caller Reachability and Migration-Order Architecture Correction.**

Architecture-only. No production caller code, helper code, replay code,
contract, schema, or dependency changed. No macOS implementation. No
packaging/install/live-host mutation. No real ceremony.

## 0. Governance / phase identity

- Predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
  (alias `N16-5-F-5-TB-CERT-READ-CLIENT-IMPL`), **COMPLETE — BLOCKED**,
  final pushed commit `4557cb86`. Confirmed via `PROJECT_STATUS.md`
  (`## Current Phase` states `BLOCKED at Section 0 governance
  validation, before any production change`),
  `.pcae/phase-completion-metadata.json` (`"status": "completed"`, the
  BLOCKED verdict recorded in `phase_name`/`summary`), and governed task
  state, all agreeing. The predecessor's own metadata confirms it made
  **zero production source, contract, schema, or test changes** ("Only
  governance artifacts changed").
- Canonical blocker (as stated in the predecessor's BLOCKED disposition,
  independently re-derived below, not trusted as given): the
  authorization premise that `hpac_verifier.py` is a live
  `certification_read` consumer was false; the sole production
  import/call site of `recognized_certification_read_authority` is
  `hpac_certification_coordinator.py`, which itself has zero live
  production callers.
- CPIPC validation, independently re-derived via `pcae.core.phase_id`
  (`parse`/`is_valid`/`normalize`/`same_series`/`same_branch`/`compare`)
  in a live Python interpreter — not trusted from the authorization
  prompt's precomputed successor text:
  ```
  pred  = "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1"
  cand  = pred + ".1"
  is_valid(pred) == True
  is_valid(cand) == True
  same_series(parse(pred), parse(cand)) == True
  same_branch(parse(pred), parse(cand)) == True
  compare(parse(pred), parse(cand)) == "less"   # strict forward ordering
  normalize(cand) == cand                        # canonical form
  len(pred.split(".")) == 62; len(cand.split(".")) == 63
  ```
  `git log --all -F --grep "<cand>"` returned **zero** matches at entry
  (unique). No conflicting active governed phase (`pcae health`:
  healthy; agent lock held by `claude-local`; `.pcae/agent-locks/latest.json`
  shows no other in-flight phase).
- Entry state, independently checked: branch `main`, HEAD == `origin/main`
  == `293eb057` (`git rev-parse HEAD` / `origin/main`),
  `origin/main..HEAD` = 0, `HEAD..origin/main` = 0, `git status --short`
  empty (tree clean).
- Contract baseline captured before any work, unchanged this phase:
  HPAC-PAWA-001 v2.0
  (`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`),
  HPAC-PAWA-HELPER-001 v1.0
  (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`),
  HPAC-PPA-001 v2.0
  (`docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`).

## 1. Purpose

Correct the caller-integration architecture using **actual live
call-graph reachability**, not merely "which module imports a legacy
authority factory." Answers: which HPAC/PAWA/helper-related modules are
reachable from live production command/runtime paths today; which
modules only consume a legacy factory internally with zero live callers
of their own; which helper operation should be migrated first based on
actual reachability; and what `hpac_certification_coordinator.py`'s
disposition should be. Architecture only — no caller migration in this
phase.

## 2. Method

The primary operator (this session) independently derived every
load-bearing factual claim directly from source before writing this
report: full reads of `src/pcae/core/hpac_verifier.py` (908 lines) and
targeted reads of `src/pcae/core/hpac_certification_coordinator.py`,
`src/pcae/core/hpac_protected_admin_writer.py`,
`src/pcae/core/protected_presentation.py`, and
`src/pcae/core/approval_presentation.py`; exhaustive `grep -rn` call-site
searches across `src/` and `scripts/` for every legacy factory and every
candidate live-caller chain; direct inspection of `pyproject.toml`,
`src/pcae/cli.py`, and `src/pcae/commands/*`; and live execution of
`pcae.core.phase_id` for CPIPC. A bounded, read-only delegated research
worker (§56 of the authorization prompt: no repository mutation, no
commit/push/task authority) was used in parallel to independently
cross-check the same call graph and to extend coverage into the five
certification-role modules and dynamic-dispatch search; every one of its
claims used below was independently re-verified by the primary operator
against live source before being accepted — see §3.

## 3. Independent verification log (primary operator, direct source)

1. `grep -rn "production_writer(\|certification_writer(\|recognized_certification_read_authority(\|mint_protected_presentation_evidence_writer("
   src/ scripts/` (excluding each factory's own `def` line) — confirmed
   the exact call-site inventory in §8 below, including that
   `certification_writer` and `recognized_certification_read_authority`
   each have **exactly one** call site, both inside
   `hpac_certification_coordinator.py` (lines 187 and 218).
2. `grep -rn "hpac_certification_coordinator" src/ scripts/` restricted
   to non-self, non-docstring hits — found exactly two: the string
   literal in `CERTIFICATION_FACTORY_CONSUMERS`
   (`hpac_protected_admin_writer.py:1887`) and a prose mention (not an
   import) in `scripts/hpac_certification_admin.py`'s docstring.
   Independently confirmed `scripts/hpac_certification_admin.py` only
   defines `describe`/`status` (both read-only) and contains no import of
   `hpac_certification_coordinator` — **zero** live import/call edge into
   the coordinator from anywhere outside itself.
3. Read `src/pcae/core/hpac_verifier.py` in full (908 lines). Confirmed
   its only imports are from `hpac_foundation`, `human_authenticator`,
   `hpac_lifecycle`, `human_authentication_proof`,
   `human_principal_registry`, and `approval_presentation` (plus a
   function-local deferred import of
   `hpac_rhamp_assertion_verify.verify_real_fido2_assertion` for real
   FIDO2 signature math — unrelated to `certification_read`). Zero
   references to `certification_read`/`CertificationReadAuthority`/
   `ReadAuthority` anywhere in the file. The module's own docstring
   states explicitly, twice (lines 67–69 and 300–301): "this module still
   has zero production consumers, so no such call site exists yet."
   **This independently reconfirms the predecessor's BLOCKED finding —
   not re-litigated, only re-derived from fresh source reading.**
4. `grep -rln "hpac_rhamp_enrollment"` / `"hpac_protected_presentation_admin"`
   across `src/`, `scripts/` (excluding self) — confirmed
   `hpac_rhamp_enrollment.py`'s only non-self production caller is
   `scripts/hpac_principal_admin.py`, and
   `hpac_protected_presentation_admin.py`'s (the core module, not the
   script) only non-self production caller is
   `scripts/hpac_protected_presentation_admin.py`.
5. Traced `protected_presentation.py`'s `mint_protected_presentation_evidence_writer`
   call site (line 649) to its enclosing function
   `_build_and_persist_evidence`, which is called only by
   `run_protected_presentation_ceremony` (line 354). `grep -rn
   "run_protected_presentation_ceremony" src/ scripts/` (excluding self)
   found **exactly one** non-test caller:
   `hpac_protected_admin_writer.py:2543`, inside
   `CertificationReadAuthority.enter_ceremony` (the `§42D` `ceremony_entry`
   hand-off, HPAC-PAWA-REQ-285). `grep -rn "enter_ceremony("` (excluding
   the method's own definition) found **exactly one** caller:
   `hpac_certification_coordinator.py:300`. **This is a new fact beyond
   what the predecessor lineage established** (see §23, Table I): the
   predecessor ARCH phase's §4.4 classified `protected_presentation.py`'s
   evidence-write call site as an independently-live "Migration priority
   HIGH" target; direct re-tracing shows its only production caller is
   itself gated behind the same zero-live-caller
   `hpac_certification_coordinator.py`.
6. Read `pyproject.toml` lines 47–75 directly: the sole `[project.scripts]`
   console entry point is `pcae = "pcae.cli:main"`; `[tool.hatch.build.targets.wheel]`
   scopes `packages = ["src/pcae"]`; `[tool.hatch.build.targets.sdist]`
   `include` lists only `/src/pcae`, `/README.md`, `/LICENSE`,
   `/pyproject.toml` — `scripts/` is excluded from both build targets.
7. `grep -rliE "hpac|pawa|rhamp|gate5|certification" src/pcae/cli.py
   src/pcae/commands/` found five files; reading every matched line in
   each confirmed all "certification" hits are the unrelated
   `pcae.core.notification_certification` governance/notification-dedup
   mechanism (a completely different subsystem sharing only the English
   word "certification") — **zero** real CLI/commands-layer reachability
   into HPAC/PAWA/RHAMP/Gate5.
8. `grep -inE "hpac|pawa|rhamp|gate5|certification" src/pcae/core/agent.py`
   → zero matches. `grep -rn "entry_points\|iter_entry_points"
   src/pcae/` → zero matches. No dynamic-dispatch or plugin-registry path
   into the HPAC subsystem exists in source.
9. `grep -n "add_parser(" scripts/hpac_*.py` for all four admin
   launchers, confirming their exact subcommand sets (§12). `grep -rln
   "scripts/hpac_" --include="*.yml" --include="*.yaml" --include=Makefile .`
   → zero hits — no CI/automation invokes any of the four scripts; they
   are human-operator-invoked only.
10. `grep -rl "HpacCertificationCoordinator" tests/` → 22 test files
    construct/exercise the coordinator; none is a production module.
11. The delegated worker (§2 below) additionally reported two **real**
    (non-docstring) call edges into `hpac_verifier.py` that this
    operator's initial pass had characterized too loosely as "no
    callers": `runtime_authority.py:433-454,948-1097` and
    `runtime_dispatch_gate5.py:236-240` both genuinely import and call
    `is_verifier_authenticated_principal`/`reverify_authenticated_principal`.
    Independently re-verified with `grep -n "hpac_verifier\|is_verifier_authenticated_principal\|reverify_authenticated_principal"`
    on both files — confirmed real, not docstring. Then independently
    traced reachability of `runtime_authority.py` and
    `runtime_dispatch_gate5.py` themselves: their only importers,
    repo-wide excluding tests, are the sibling
    `runtime_dispatch_gate7/8/9/10_eligibility.py`/`runtime_dispatch_permission.py`
    modules and `runtime_invocation_approval_store.py` — a fully
    self-contained Gate5→7→8→9→10 dispatch cluster with **no** importer
    in `src/pcae/commands/**` or `src/pcae/cli.py`. `runtime_introspection.py`
    (line 222) — the module that describes this cluster's own adapter
    surface — states in its own source: `reachable_via="no
    production-reachable positive path (RDGO gate chain: real Gate 7
    DENY, POL-005 hard DENY, execution unavailable)"`. **Corrected
    statement**: `hpac_verifier.py` has two real production call edges,
    but both originate inside a cluster that is itself, by the
    cluster's own first-party self-documentation, not reachable from
    any live entry point today — the "zero production consumers" claim
    in §3.3/§8 refers to `certification_read`/HPAC-PAWA-subsystem
    consumption specifically (which is genuinely absent), not to every
    call edge into the module, which this section corrects with more
    precision than the module's own docstring states.

No discrepancy was found between the delegated worker's independently
submitted claims and this direct re-verification on any point used
below.

## 4. Live entry-point inventory (TABLE A)

| Entry module | Symbol | How invoked | Live/reachable? | Caller chain | Authority relevance |
|---|---|---|---|---|---|
| `pcae.cli` | `main` (console script `pcae`) | packaged CLI entry point | YES (the only live orchestration entry point in this repo) | — | Zero HPAC/PAWA/RHAMP/Gate5 relevance (§3.7) |
| `pcae.commands.*` | various subcommands | dispatched from `cli.py` | YES | — | Only unrelated `notification_certification` hits; zero HPAC relevance |
| `scripts/hpac_principal_admin.py` | `main` | manual `python scripts/...` invocation only | Script-live, NOT CLI/packaged-live | → `hpac_rhamp_enrollment.production_writer(...)` | `admin_mutation` |
| `scripts/hpac_protected_presentation_admin.py` | `main` | manual invocation only | Script-live, NOT packaged-live | → `hpac_protected_presentation_admin.production_writer(...)` | `admin_mutation` |
| `scripts/hpac_certification_admin.py` | `main` | manual invocation only | Script-live, read-only (`describe`/`status`); no factory call | none (no writer/reader factory call) | none today |
| `scripts/hpac_protected_root_admin.py` | `main` | manual invocation only | Script-live, root/anchor lifecycle only | operates on the protected root directly, not via the four factories under study | root provisioning, not a helper-operation caller |

No CLI command, runtime coordinator path, background/service entry
point, or packaged console script other than `pcae = pcae.cli:main`
exists. None of the four `scripts/hpac_*.py` launchers are packaged in
the wheel or sdist (§3.6) — they exist and are invocable only from a
source checkout, and only by a human operator running them directly;
no CI/Makefile/automation reaches them (§3.9).

## 5. Call-graph reconstruction (summary; full detail in §8–§11)

```
pcae.cli:main ──▶ pcae.commands.* ──✗── (no edge reaches core/hpac_*)

runtime_authority.py ◀─▶ runtime_dispatch_gate5/7/8/9/10.py ──▶ is_verifier_authenticated_principal()/
                          (self-contained cluster,               reverify_authenticated_principal()
                           no importer in cli.py/commands/**,     [hpac_verifier.py]
                           self-documented "no production-
                           reachable positive path")

scripts/hpac_principal_admin.py ──▶ hpac_rhamp_enrollment.py ──▶ production_writer()
scripts/hpac_protected_presentation_admin.py ──▶ hpac_protected_presentation_admin.py ──▶ production_writer()
scripts/hpac_protected_root_admin.py ──▶ enroll_principal_via_pawa()/revoke_principal_via_pawa() ──▶ production_writer()
scripts/hpac_certification_admin.py ──▶ (describe/status only; no factory call)

hpac_certification_coordinator.py ──▶ certification_writer()
                                   ──▶ recognized_certification_read_authority()
                                          └─▶ CertificationReadAuthority.enter_ceremony()
                                                 └─▶ protected_presentation.run_protected_presentation_ceremony()
                                                        └─▶ mint_protected_presentation_evidence_writer()
                                   ──▶ reach_gate5_assurance() ──▶ hpac_verifier.verify_human_authentication()

hpac_certification_coordinator.py ◀── (nothing; not even scripts/hpac_certification_admin.py,
                                        which names it only in a docstring — §3.2/§7 correction)
```

Static resolution was unambiguous for every edge above. The delegated
worker flagged, as an open ambiguity, whether
`CertificationReadAuthority.enter_ceremony`'s body actually resolves to
`run_protected_presentation_ceremony` rather than inferring it only from
caller counts; the primary operator had already read that method's full
body directly (`hpac_protected_admin_writer.py:2494-2543`) before this
report was drafted and confirmed its final statement is literally
`return _pp.run_protected_presentation_ceremony(**kwargs)` — this is
resolved, not an open ambiguity. No dynamic
dispatch, `getattr`, `importlib`, plugin registry, or entry-point
mechanism was found anywhere in `src/pcae/` that could reach any HPAC
module (§3.8; independently confirmed by both the primary operator and
the delegated worker, including a direct check that
`runtime_introspection.py`'s one prose mention of
`runtime_dispatch_gate10_eligibility` is descriptive text, not an
`import` statement).

## 6. Reachability classification (TABLE B)

| Module/symbol | Classification | Evidence |
|---|---|---|
| `pcae.cli`, `pcae.commands.*` | A. LIVE_PRODUCTION_REACHABLE | packaged console script; zero HPAC edges |
| `hpac_rhamp_enrollment.py` | B. PRODUCTION_MODULE_BUT_NO_LIVE_CALLER *(script-only)* | sole caller is `scripts/hpac_principal_admin.py`, not CLI/packaged (§3.4, §3.9) |
| `hpac_protected_presentation_admin.py` (core module) | B. PRODUCTION_MODULE_BUT_NO_LIVE_CALLER *(script-only)* | sole caller is `scripts/hpac_protected_presentation_admin.py` |
| `hpac_certification_coordinator.py` | F. DEAD/UNREFERENCED *(in production; extensively test-exercised)* | zero import/call edges anywhere outside itself (§3.2); 22 test files (§3.10) |
| `hpac_verifier.py` | B. PRODUCTION_MODULE_BUT_NO_LIVE_CALLER *(two real call edges exist, both inside a self-documented unreachable Gate5-10 dispatch cluster; zero `certification_read` relationship)* | §3.3, §3.11, §8 |
| `protected_presentation.run_protected_presentation_ceremony` | F. DEAD/UNREFERENCED *(in production; sole caller is the dead coordinator's `enter_ceremony`)* | §3.5 |
| `hpac_protected_admin_writer.py` (the 4 factories) | E. ARCHITECTURAL_FUTURE_SEAM | frame-pinning admission mechanism, superseded by HPAC-PAWA-001 v2.0 §33C; still the only current in-process authority mechanism |
| `scripts/hpac_*.py` (all four) | D. ADMIN_TOOL_ONLY | excluded from wheel/sdist (§3.6); no CI invocation (§3.9) |
| `HpacCertificationCoordinator` / `CertificationSession` (coordinator internals) | C. TEST_ONLY (in current production reality) | 22 test files exercise these; zero production callers |
| Five certification-role modules (`hpac_challenge_coordinator`, etc., dispatched inside the coordinator) | C. TEST_ONLY | reachable only via the dead coordinator or tests |

## 7. `hpac_certification_coordinator.py` (§9 of the authorization prompt)

- 553 lines. Defines `HpacCertificationCoordinator`, `CertificationSession`,
  and the five role-dispatch methods (`_CHALLENGE_ROLE`, `_ASSERTION_ROLE`,
  `_PROOF_VERIFIER_ROLE`, `_GATE5_BINDER_ROLE`, and the counter-state
  verifier role) internally. Its own module docstring (lines 12-18)
  self-declares scope: "This module is a non-agent-importable, local,
  out-of-band deployment-owner tool ... Ordinary agent / runtime / Gate /
  plugin / `pcae` CLI code SHALL NOT import it ... It is not a `pcae` CLI
  subcommand and is not in any dispatch table. It is reached only from
  the standalone `scripts/hpac_certification_admin.py` entry point" —
  this is the coordinator's own *design-intent* claim, independently
  re-read verbatim. **Correction to the delegated worker's report**: the
  delegated worker's draft stated `scripts/hpac_certification_admin.py`
  "drives" the coordinator; direct re-reading of that script's full
  import list (§3.2 — only `argparse`, `json`, `sys`, plus
  `from __future__ import annotations`) shows it does **not** actually
  import `hpac_certification_coordinator` at all — the name appears only
  in that script's own docstring (line 16), describing an intended
  future dependency, not a current import. The coordinator's docstring's
  "reached only from the standalone script" claim is therefore also
  currently aspirational, not yet true in source: **today the
  coordinator has zero callers anywhere, including its own designated
  script** — a stronger (not weaker) statement of dead-code status than
  either the coordinator's own docstring or the delegated worker's
  report independently claimed.
- Who imports it: **nobody**, outside itself, in `src/` or `scripts/`
  (§3.2). Its name appears exactly once elsewhere, as a string literal in
  `CERTIFICATION_FACTORY_CONSUMERS`.
- Who calls its public functions: only the 22 test files enumerated in
  §3.10.
- No CLI/runtime command reaches it (§3.7). No dynamic registry reaches
  it (§3.8, §11 below). No production orchestration reaches it.
- It is the sole authorized consumer of `certification_writer` and
  `recognized_certification_read_authority` (both allowlists name it and
  it alone), and is therefore the **sole production import/call site**
  of both factories — but that call site is itself unreachable in
  production today.
- Intent, from its own source and the contract lineage: it is future
  orchestration for the real certification ceremony deferred to the
  not-yet-begun N16-5-FINAL-CERT phase. This is design intent stated in
  the frozen contracts and prior phase docs, not a claim inferred from
  the filename alone (§40 of the authorization prompt).

## 8. `hpac_verifier.py` reachability (§10)

Re-derived directly from source (§3.3), not from the predecessor's
report alone:

- Imports: `hpac_foundation`, `human_authenticator`, `hpac_lifecycle`,
  `human_authentication_proof`, `human_principal_registry`,
  `approval_presentation`, plus a function-local deferred import of
  `hpac_rhamp_assertion_verify` for real FIDO2 signature verification
  (an entirely separate concern — mechanism-layer assertion math, not
  the `certification_read` authority path).
- Public functions: `verify_human_authentication`,
  `is_verifier_authenticated_principal`, `reverify_authenticated_principal`.
- Live callers: **two real call edges exist** (`runtime_authority.py`,
  `runtime_dispatch_gate5.py`, calling
  `is_verifier_authenticated_principal`/`reverify_authenticated_principal`
  — §3.11), but neither is reachable from any live entry point: both
  belong to a fully self-contained Gate5→7→8→9→10 dispatch cluster with
  no importer anywhere in `src/pcae/commands/**` or `src/pcae/cli.py`,
  and that cluster's own adapter-surface descriptor
  (`runtime_introspection.py:222`) self-documents "no
  production-reachable positive path." `protected_presentation.py` and
  `human_authenticator_fido2.py` reference `hpac_verifier` only in
  comments/docstrings (confirmed by direct grep — no import). It
  participates in **no** current *live-reachable* production flow, but
  it is not, more precisely, an entirely uncalled module — a correction
  to how loosely that could be read from its own docstring.
- The previous architecture's treatment of `hpac_verifier.py` was
  incorrect specifically and only for the `certification_read` claim —
  it has no `certification_read`/HPAC-PAWA-subsystem relationship at
  all, live or dead. Its broader zero-live-caller status (unrelated to
  `certification_read`) is a separate, already-true fact, restated here
  for completeness, not a new finding.

## 9. Legacy factory consumer inventory (TABLE C / TABLE D)

| Factory | Defining module | Consumer module(s) | Consumer symbol(s) | Live caller exists? | Production reachability? | Future seam? | Migration need? |
|---|---|---|---|---|---|---|---|
| `production_writer` | `hpac_protected_admin_writer.py` | `hpac_rhamp_enrollment.py`; `hpac_protected_presentation_admin.py` (core) | RHAMP enrollment; presentation install/rotate/revoke | Script-only (`scripts/hpac_principal_admin.py`, `scripts/hpac_protected_presentation_admin.py`) | NO CLI/packaged reachability; YES manual-script reachability | Partially — script layer itself is a future/manual seam until packaged | FUTURE_IF_ACTIVATED (packaging/launcher decision precedes real migration value) |
| `certification_writer` | same | `hpac_certification_coordinator.py` | 5-role dispatch | NO (coordinator itself uncalled) | NO | YES — deferred to N16-5-FINAL-CERT | RETIRE-CANDIDATE-EVALUATION or FUTURE_IF_ACTIVATED |
| `recognized_certification_read_authority` | same | `hpac_certification_coordinator.py` | read-set resolution + `enter_ceremony` hand-off | NO | NO | YES | FUTURE_IF_ACTIVATED |
| `mint_protected_presentation_evidence_writer` | same | `protected_presentation.py` (`_build_and_persist_evidence`, via `run_protected_presentation_ceremony`) | evidence-writer issuance | NO — sole caller is `enter_ceremony`, itself only called by the uncalled coordinator (§3.5) | NO | YES (contradicts predecessor ARCH's "HIGH priority" classification — see Table I) | FUTURE_IF_ACTIVATED |

No orphaned/undocumented legacy mechanism was found beyond these four
factories and their allowlists.

## 10. Live vs. dead authority path (§12/§26)

**No current live production path reaches ANY of the four legacy
in-process HPAC authority factories from a packaged CLI command,
runtime coordinator, or automated/CI process.** The only reachability at
all is:

- `admin_mutation` (`production_writer`): reachable, but only via a
  human operator manually running one of two unpackaged
  `scripts/hpac_*.py` launchers from a source checkout.
- `certification_write`, `certification_read`, `ceremony_entry`,
  `presentation_evidence_write`: **all four** trace to
  `hpac_certification_coordinator.py`, which has zero callers anywhere
  — these are dead/future seams, not live paths, by any reachability
  standard (script, CLI, or automated).

This is a stronger and more precise statement than the authorization
prompt's own framing (which addressed `certification_read` specifically
via `hpac_verifier.py`): **every one of the five helper operations
traces, at its current sole production call site, to either a
manual-script-only path (`admin_mutation`) or the same dead coordinator
(`certification_write`, `certification_read`, `ceremony_entry`,
`presentation_evidence_write`).** No legacy authority factory has a
CLI/runtime/orchestration-reachable live caller today. Per §12 of the
authorization prompt, this phase does **not** manufacture a migration to
satisfy the prior architecture's assumption.

## 11. Dynamic dispatch / reflection / plugin registry (§23/§25)

`grep -rn "getattr(\|importlib\|entry_points\|iter_entry_points"` across
`src/pcae/` restricted to any hit naming or reachable-to an HPAC/PAWA
module: zero. `pcae runtime-registry` reports `registry_status:
registry_required`, `registration_allowed: no`, `execution_allowed: no`
— no runtime is registered or discoverable. `pcae capability-registry`
lists agent-tooling capabilities (an unrelated subsystem — which
external coding agents are installed), not a plugin/effect registry;
independently confirmed it contains no HPAC-relevant entries. Plugins: 0.
Capabilities: 0 (runtime-registry / governance status, unchanged this
phase). No hidden production call edge exists by any dynamic mechanism.

## 12. Script reachability (TABLE — §20)

| Script | Subcommands | Effect | Packaged? | CI/automation-invoked? |
|---|---|---|---|---|
| `scripts/hpac_protected_root_admin.py` | `provision`, `set-agent-exclusion`, `rotate`, `revoke`, `enroll-principal`, `revoke-principal` | protected-root provisioning/rotation/revocation | NO | NO |
| `scripts/hpac_principal_admin.py` | enroll, revoke | RHAMP enrollment via `production_writer` | NO | NO |
| `scripts/hpac_protected_presentation_admin.py` | `install`, `rotate`, `revoke`, `status` | presentation-mechanism install/rotate/revoke via `production_writer` | NO | NO |
| `scripts/hpac_certification_admin.py` | `describe`, `status` | read-only today; no factory call | NO | NO |

All four are admin/deployment-only, invoked manually, package-excluded
from both wheel and sdist (§3.6), and not part of ordinary PCAE runtime.
None is falsely counted as a live orchestration caller in this report.

## 13. Import graph vs. call graph vs. reachable call graph (§21)

Two concrete, source-verified distinctions this phase turned up:

1. `approval_presentation.py` **imports** from `protected_presentation.py`
   (a deferred import inside `_verify_installed_attestation`, §3.5) —
   but it imports and calls `verify_protected_presentation_evidence`
   (a *verification read*), not `run_protected_presentation_ceremony`
   (the *evidence-write ceremony* containing the
   `mint_protected_presentation_evidence_writer` call). An import edge
   between two modules does not mean every function in the imported
   module is reachable — this is exactly the "module imported for
   types/constants" trap named in §21 of the authorization prompt,
   observed here for a real function-level split within the same module,
   not just a type import.
2. `hpac_certification_coordinator.py` importing `certification_writer`/
   `recognized_certification_read_authority` and being the sole entry in
   both consumer allowlists is a **factory-consumer relationship**; it
   does not by itself imply a **reachable call edge** from any live
   production entry point, since nothing calls the coordinator's own
   public surface outside tests (§7).

## 14. Test-only edges (§22)

22 test files construct/exercise `HpacCertificationCoordinator`/
`CertificationSession` (§3.10); 9 test files call
`run_protected_presentation_ceremony` directly. None of this is treated
as production reachability in Tables B/C/D/E/F above — a test
constructing the coordinator does not make it production-reachable, per
§22 of the authorization prompt.

## 15. Helper operation reachability (TABLE E, §17)

| Helper operation | Current legacy factory | Live caller exists? | Legacy-equivalent consumer | Future seam only? | Platform dependency | Migration priority (corrected) |
|---|---|---|---|---|---|---|
| `admin_mutation` | `production_writer` | Script-only (`scripts/hpac_principal_admin.py`, `scripts/hpac_protected_presentation_admin.py`) | `hpac_rhamp_enrollment.py`, `hpac_protected_presentation_admin.py` | Partially (packaging-gated) | None for slice work itself | Highest of the five — the only operation with ANY non-test caller today |
| `certification_write` | `certification_writer` | NO | `hpac_certification_coordinator.py` (uncalled) | YES | N16-5-FINAL-CERT dependency | FUTURE_IF_ACTIVATED |
| `certification_read` | `recognized_certification_read_authority` | NO | `hpac_certification_coordinator.py` (uncalled) | YES | N16-5-FINAL-CERT dependency | FUTURE_IF_ACTIVATED |
| `ceremony_entry` | (implicit hand-off) | NO | `hpac_certification_coordinator.py` (uncalled) via `enter_ceremony` | YES | N16-5-FINAL-CERT dependency | FUTURE_IF_ACTIVATED |
| `presentation_evidence_write` | `mint_protected_presentation_evidence_writer` | NO — corrected this phase (§3.5); its only caller is `enter_ceremony`, itself only called by the uncalled coordinator | `protected_presentation.py` | YES (newly established) | HPAC-PPA-001 v2.0 packaging/launcher question (unchanged, unresolved) | FUTURE_IF_ACTIVATED (downgraded from predecessor ARCH's "HIGH") |

## 16. Five certification roles (TABLE F, §18)

| Role | Current production implementation exists? | Live caller exists? | Helper-ready? | Future-only? | Dependency chain |
|---|---|---|---|---|---|
| `hpac_challenge_coordinator` | YES (dispatch inside coordinator) | NO | Architecturally, per predecessor ARCH §4.3/§8 | YES | Gated on coordinator activation |
| `hpac_assertion_recorder` | YES | NO | YES | YES | Gated on coordinator activation |
| `human_authentication_proof_verifier` | YES | NO (dispatch path only; `hpac_verifier.py` itself is a separate, also-uncalled module, §8) | YES | YES | Gated on coordinator activation |
| `hpac_gate5_binder` | YES | NO | YES | YES | Gated on coordinator activation; consumed conceptually by `runtime_dispatch_gate5.py`, which is itself not reachable from any live path today |
| `hpac_rhamp_counter_state_verifier` | YES | NO | YES | YES | Gated on coordinator activation |

All five roles exist as implemented dispatch targets inside the
coordinator; none has a live caller; all are future-only pending
coordinator activation. No role's implementation existence is conflated
with active production use.

## 17. CLI / command reachability (TABLE — §19)

Every `pcae` subcommand is dispatched from `src/pcae/commands/*` via
`cli.py`. Direct inspection (§3.7) of every file with an
HPAC/PAWA/RHAMP/Gate5/certification-shaped grep hit
(`phase.py`, `task.py`, `phase_reports.py`, `notifications.py`,
`push.py`) shows every hit is the unrelated
`pcae.core.notification_certification` governance-notification
mechanism. **Zero** CLI commands reach the HPAC subsystem, directly or
transitively, including push/rollback pathways.

## 18. Corrected migration necessity matrix (TABLE G, §27)

| Consumer | Necessity classification | Rationale |
|---|---|---|
| `hpac_rhamp_enrollment.py` → `production_writer` | FUTURE_IF_ACTIVATED | Only reachable via a manual, unpackaged script; migrating it now buys no live-production risk reduction until packaging/deployment is decided |
| `hpac_protected_presentation_admin.py` → `production_writer` | FUTURE_IF_ACTIVATED | Same reasoning |
| `hpac_certification_coordinator.py` → `certification_writer` / `recognized_certification_read_authority` | NO_ACTION (this phase); FUTURE_IF_ACTIVATED (structurally) | Zero live callers; migrating an uncalled consumer produces no verifiable production behavior change and cannot be validated against a real caller |
| `protected_presentation.py` → `mint_protected_presentation_evidence_writer` | NO_ACTION (this phase); FUTURE_IF_ACTIVATED | Corrected this phase (§3.5): only reachable via the uncalled coordinator, not independently live |
| `hpac_verifier.py` | NO_ACTION | Has no relationship to any of the four legacy factories at all (§8); nothing to migrate |

No consumer is classified REQUIRED_NOW or REQUIRED_BEFORE_F5_CERTIFICATION:
no live production path currently depends on any of the four legacy
factories being replaced before F-5 can even begin considering real
certification, since the coordinator that would drive real certification
has no live caller yet regardless of which side of the legacy/helper
boundary its internals use.

## 19. Dead-code retirement analysis (§15)

- `hpac_certification_coordinator.py`: **remain as future architecture
  seam.** It is deliberate, contract-anticipated future orchestration
  (§7) for N16-5-FINAL-CERT, not orphaned dead code — retiring it would
  discard designed-but-not-yet-activated architecture, not remove waste.
- `protected_presentation.run_protected_presentation_ceremony` /
  `_build_and_persist_evidence`: **remain**, same reasoning — it is the
  evidence-write half of the same future ceremony flow, gated behind the
  same coordinator.
- The four legacy factories in `hpac_protected_admin_writer.py`:
  **retain until every consumer is migrated** (unchanged from the
  predecessor ARCH's §10 retirement plan) — nothing in this phase's
  findings changes that plan, since `admin_mutation`'s script-only
  callers still exist and still use them.
- `hpac_verifier.py`: **remain, unrelated to this retirement analysis
  entirely** — it has no legacy-factory relationship to retire.

Nothing is removed in this phase.

## 20. Future certification coordinator activation requirements (§16)

If `hpac_certification_coordinator.py` is to become live orchestration,
activation requires, at minimum: a real live caller/entry point (a CLI
command or packaged launcher that does not exist today); the typed
helper client from the predecessor ARCH's §8.1 (not yet implemented);
a defined operation sequence across the five roles; real
`certification_read`/`certification_write` usage through that client,
not the legacy factories; one-shot helper invocation per HPAC-PAWA-HELPER-001;
durable replay semantics (already independently verified,
`hpac_pawa_helper_replay_state.py`); explicit real-vs-deterministic
classification at every step; no legacy fallback (§9 of the predecessor
ARCH); a resolved packaging/deployment dependency (§21 below); and an
explicit real-certification boundary decision (deferred to
N16-5-FINAL-CERT). No implementation is performed here.

## 21. Packaging dependency (§24/§35/§47)

Unchanged from the predecessor ARCH's §4.7/§12 finding, independently
reconfirmed (§3.6): `scripts/` is excluded from both the wheel
(`packages = ["src/pcae"]`) and the anchored sdist (`include` lists only
`/src/pcae`, `/README.md`, `/LICENSE`, `/pyproject.toml`). No helper
launcher exists in packaged form. Whether a real deployment runs from an
installed wheel (requiring a new packaged launcher entry point) or
always from a source checkout (status quo) remains an open,
un-decided question — this phase does not decide it, and does not
modify packaging.

## 22. Platform dependency (§34/§48)

macOS same-file-object helper execution remains FAIL-CLOSED / NOT
IMPLEMENTED, unchanged (`execute_verified` raises
`UnsupportedPlatformProfile` on any non-Linux platform — unchanged
source, not re-verified line-by-line this phase since no claim in this
report depends on it). This architecture correction does not elevate or
resolve macOS work; nothing in the corrected reachability analysis above
makes macOS the actual next blocker — the actual next blocker (§26
below) is upstream of any platform question.

## 23. Original incorrect assumption vs. corrected fact (TABLE I, §30)

| # | Original conclusion (predecessor lineage) | Evidence disproving it | Corrected conclusion |
|---|---|---|---|
| 1 | Authorization premise (N16-5-F-5-TB-CERT-READ-CLIENT-IMPL): `hpac_verifier.py` is a live `certification_read` consumer requiring a typed-client migration | `hpac_verifier.py` has zero `certification_read`/HPAC-PAWA imports or references (§3.3, §8) | `hpac_verifier.py` has no relationship to `certification_read` at all — **not applicable**, not merely "not yet migrated" (predecessor's own BLOCKED finding, independently re-confirmed, not re-litigated) |
| 2 | Predecessor ARCH §4.6: `hpac_verifier.py` "Reads resolved records to check `authority_class is PRODUCTION`; maps onto the `certification_read` enumerated set" | Same as above — direct re-read of the full 908-line module shows no such mapping exists | ARCH's own §4.6 characterization of `hpac_verifier.py` is corrected: it performs authority-class checks internal to its own HPAC-REQ-054 sequence, unrelated to the `certification_read` helper operation or its factory |
| 3 | Predecessor ARCH §4.4: `protected_presentation.py`'s `mint_protected_presentation_evidence_writer` call site has "Migration priority **HIGH**" as an independently-live target | Its sole caller, `enter_ceremony`, is itself called only by the uncalled `hpac_certification_coordinator.py` (§3.5, new fact this phase) | `presentation_evidence_write` is **not** independently live; it is gated behind the same dead coordinator as `certification_write`/`certification_read`/`ceremony_entry` — priority corrected to FUTURE_IF_ACTIVATED |
| 4 | Predecessor ARCH §11 migration order implicitly treated `certification_read` (via `hpac_verifier.py`) as a viable "safest first slice" | Both legs of that claim are false: no relationship exists (#1/#2), and even the correctly-identified sole consumer (the coordinator) has no live caller | The read-only-first heuristic itself was not wrong in principle, but had no valid live target to apply it to; the corrected first-live-target is `admin_mutation` (§25 below), which happens to be a **write** operation, not read |

## 24. Unchanged architecture conclusions (preserved, not rewritten)

- The five-helper-operation vocabulary, the four legacy factories, and
  the consumer-allowlist mechanism are exactly as the predecessor ARCH
  documented (§4.1, §5, §6 of that report) — unchanged.
- The client-side architecture design (typed request builders, one-shot
  transport, no-fallback rule, replay/reconciliation discipline,
  no-authority-export, threat matrix) in predecessor ARCH §8–§13 remains
  valid design content, independent of which caller is migrated first —
  none of it assumed `hpac_verifier.py` or presumed
  `presentation_evidence_write`'s liveness as a precondition of the
  design itself.
- The legacy-path retirement plan (§10 of predecessor ARCH) is unchanged.
- macOS FAIL-CLOSED / NOT IMPLEMENTED status: unchanged.
- Packaging exclusion of `scripts/`: unchanged, independently
  reconfirmed.

## 25. Corrected migration order (TABLE H, §28)

1. **Slice 1 (corrected)**: activation/packaging architecture for
   `admin_mutation` — the only helper operation with ANY non-test live
   caller today (script-invoked `hpac_rhamp_enrollment.py` /
   `hpac_protected_presentation_admin.py`). Before migrating these
   callers onto a typed client, the open packaging question (§21) —
   whether a real deployment ever runs from an installed wheel, which
   would need a packaged launcher entry point — should be resolved,
   since the migration's real-world value depends on how the migrated
   caller is actually invoked in deployment. This is an
   architecture/decision phase, not implementation.
2. **Slice 2**: if Slice 1 resolves toward "migrate the script-invoked
   callers as-is (source-checkout deployment status quo)," implement the
   typed `admin_mutation` client and migrate `hpac_rhamp_enrollment.py`'s
   `production_writer` call sites first (bootstrap path, already
   exercises real FIDO2 hardware) — matching predecessor ARCH's original
   Slice 3 priority ordering, now promoted to first because it is the
   only operation with a real caller at all.
3. **Slice 3**: migrate `hpac_protected_presentation_admin.py`'s
   `production_writer` call site (lower frequency, install-time-only).
4. **Slice 4 (deferred)**: `hpac_certification_coordinator.py` activation
   architecture — a live caller/entry point must exist before
   `certification_write`, `certification_read`, `ceremony_entry`, or
   `presentation_evidence_write` migration has any real-world caller to
   validate against. This is naturally gated on N16-5-FINAL-CERT's real
   ceremony design, unchanged from predecessor ARCH's reasoning, now
   generalized to all four coordinator-gated operations, not just two.
5. **Slice 5 (last)**: remove the four legacy factories and the
   frame-pinning machinery, once every consumer above is migrated and a
   guard test proves no remaining reachability — unchanged from
   predecessor ARCH §11 Slice 6.

### 25.1 Why this is the corrected order, not the previous one

The previous order picked `certification_read` first specifically
*because* it looked read-only and low-risk; direct reachability evidence
shows it (and its three coordinator-gated siblings) have **zero** live
callers of any kind, so "low risk" was never the deciding property —
"has no live caller to validate against" is. `admin_mutation` is
promoted to first not because it is safer in the abstract, but because
it is the **only** operation with a real, currently-exercised caller,
which is the actual precondition (§43 of the authorization prompt:
"real current blocker exists") for a migration to be independently
verifiable against real behavior rather than a synthetic/test-only
driver.

## 26. First concrete successor recommendation (§29)

**Exactly one** next governed phase is recommended: a narrow
**packaging/deployment-decision architecture phase** for `admin_mutation`
— resolving whether `scripts/hpac_principal_admin.py` and
`scripts/hpac_protected_presentation_admin.py` (or the typed client that
will replace their `production_writer` calls) are meant to run only from
a source checkout (status quo, no packaging change needed) or from an
installed wheel (requiring a new `[project.scripts]` entry point and
wheel/sdist inclusion decision). This is genuinely next because it is
the single open precondition standing between "we know which operation
has a real caller" (this phase's finding) and "we can specify a
concrete, verifiable first migration slice" (predecessor ARCH's original
Slice 3 intent, now correctly targeted). Scope: architecture/decision
only, no code; production files expected: none (a decision document);
independent verification should follow before implementation begins,
per this repository's established discipline; no macOS implication
(admin_mutation's script callers today never touch the same-file-object
helper-execution path); no-go boundaries: do not implement the typed
client, do not modify packaging, do not migrate any caller, in that
phase either — decide, then require a further fresh authorization to
implement. **Not begun.**

## 27. Files changed this phase

- `docs/PHASE_N16_5_F_5_TB_CALLER_MAP_CORRECTION.md` (new, this file)
- `PROJECT_STATUS.md` (Current Phase section updated)
- `CHANGELOG.md` (entry added)
- `.pcae/phase-completion-metadata.json`
- `.pcae/phase-completion-report.md`
- `.pcae/fast-green-attribution/*.json` (new evidence file)
- `tasks/active/*.md` / `tasks/done/*.md` (task lifecycle)

**Production source changes: NONE.** **Contracts changed: NONE.**
**Schemas changed: NONE.** **Dependencies changed: NONE.** **Live
protected-host writes: 0.** **Real ceremony: NOT PERFORMED.**

## 28. Runtime / effect wall (unchanged)

Runtime state: Observed. Maximum capability: observe. Execution
availability: unavailable. Plugins: 0. Capabilities: 0. First governed
runtime external effect: ABSENT / UNREACHABLE. No adapter.dispatch. No
Gate10 effect.

## 29. Status wall

- F-5-B2: BLOCKED PENDING THE CORRECTED NEXT DEPENDENCY (packaging/deployment
  decision for `admin_mutation`, §26).
- F-5: CERTIFICATION BLOCKED.
- N-16-5: NOT CLOSED.
- N-16-6: OPEN / UNTOUCHED.
- N-16-7: OPEN / UNTOUCHED — strictly last.

## 30. Historical governance integrity preserved

`N16-5-F-5-TB-HELPER-IV`: COMPLETE — NOT VERIFIED / BLOCKED (historical,
unchanged). `N16-5-F-5-TB-HELPER-IV-R`: COMPLETE / INDEPENDENTLY VERIFIED
(unchanged). `N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN`: COMPLETE
(unchanged). `N16-5-F-5-TB-CALLER-INTEGRATION-ARCH`: **COMPLETE**
(unchanged — it was completed architecture; only its
`hpac_verifier.py`/`certification_read` migration-target selection and
its `presentation_evidence_write` "HIGH priority" classification are
superseded here, per Table I; every other conclusion in that report
stands, per §24). `N16-5-F-5-TB-CERT-READ-CLIENT-IMPL`: **COMPLETE —
BLOCKED** (unchanged — it correctly stopped on a disproven premise; not
reinterpreted as failed execution). No retroactive reinterpretation
performed.

## 31. Verdict

**N16-5-F-5-TB-CALLER-MAP-CORRECTION: COMPLETE.** Previous first
implementation target (`certification_read` via `hpac_verifier.py`):
CORRECTED / SUPERSEDED — not applicable. `hpac_certification_coordinator.py`
reachability: CLASSIFIED FROM DIRECT SOURCE EVIDENCE — zero live
callers, future architecture seam. Current live HPAC/PAWA authority
consumer set: CANONICALLY RECONSTRUCTED — only `admin_mutation`'s two
script-invoked call sites have any non-test caller; all four other
operations trace to the same uncalled coordinator. Migration order:
CORRECTED (§25). F-5-B2: BLOCKED PENDING THE CORRECTED NEXT DEPENDENCY.
F-5: CERTIFICATION BLOCKED. N-16-5: NOT CLOSED. N-16-6 / N-16-7: OPEN /
UNTOUCHED. Recommended next: one source-backed governed
packaging/deployment-decision architecture phase for `admin_mutation`
(§26). **NOT BEGUN.**
