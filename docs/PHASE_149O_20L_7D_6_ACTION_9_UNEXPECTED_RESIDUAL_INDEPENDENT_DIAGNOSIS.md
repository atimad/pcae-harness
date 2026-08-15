# Phase 149O.20L.7D.6 — Action-9 Unexpected Residual Independent Diagnosis

## 1. Scope and disposition

**Diagnosis-only.** No production source, contract, Dell infrastructure,
credential, or proposition was modified. No CHGR was created. No repair
authorization was obtained. Action 9 was not rerun as a changed
experiment — only the exact, unchanged, already-authorized Action-9
command was rerun read-only, once, to establish determinism (§8 of the
governing instruction). No DeploymentBinding, certification, or
activation was created. This report is the defect/disposition map
required by the governing instruction, not a repair.

## 2. Phase-entry state

```
git status --short          → (clean)
git status --branch --short → ## main...origin/main
git log --oneline -1        → 4ff227dd Phase 149O.20L.7D.5: task lifecycle transitions (close to idle)
git rev-list --count origin/main..HEAD → 0
```

`pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
coherent. `pcae doctor task-memory`: warnings (pre-existing —
historical `tasks/active/`/`tasks/done/`↔`tasks/DONE.md` bookkeeping
gaps predating this phase; unrelated, not remediated here). `pcae push
check`: clean (`nothing_to_push`). `pcae runtime inspect`: Observed /
observe / unavailable. `pcae notify status`: Telegram configured,
enabled, ready. `pcae phase-report show --latest`: 149O.20L.7D.5
canonical report present, consistent, recommends exactly 149O.20L.7D.6.
`pcae phase-report reconcile --phase-id 149O.20L.7D.5`: read-only
inspection, `delivery_recorded_bookkeeping_incomplete` (pre-existing
receipt bookkeeping gap, no mutation performed by the reconcile call
itself).

## 3. Live Dell state preservation check (read-only, before any diagnosis)

Fresh SSH to `hac-dell` (`192.168.192.200`), sudo read-only:

| Property | Expected (7D.5 post-execution) | Observed | Match |
|---|---|---|---|
| `/etc/machine-id` | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` | yes |
| `pcae` identity | uid=1004 gid=1004 groups=1004 | uid=1004(pcae) gid=1004(pcae) groups=1004(pcae) | yes |
| Protected Root `/opt/pcae/runtime` | root:pcae 750 | root:pcae 750 | yes |
| Shared dir topology | `bin/`, `src/`, `venv/` under Protected Root | present, root:pcae 750 each | yes |
| Pinned source SHA | `7a3fa971304521cdcb44251e07ef1966baec686a` | `7a3fa971304521cdcb44251e07ef1966baec686a` | yes |
| Detached checkout | clean, no drift | `git status --short` empty, detached HEAD | yes |
| 4030-path mode mapping | 4024×`100644`, 6×`100755` | 4024×`100644`, 6×`100755`, 4030 total files | yes |
| venv identity | python3.12 symlinked to system interpreter | `venv/bin/python3` → `/usr/bin/python3` | yes |
| Editable install | `pcae-harness` 0.2.0, editable, `dist-info` at `venv/.../site-packages` | confirmed, `direct_url.json` `editable: true`, points to `/opt/pcae/runtime/src` | yes |
| Wrapper digest | `b3e969...c32` | `b3e969128ff48ecfae874a9348d889b43f7fc336bf170387b912b1cfc3753c32` | yes |
| Source credential metadata | `/root/.ssh/pcae_harness_deploy_ed25519` root:root 600 | root:root 600 | yes |

No drift. Actions 1–8 are exactly in the 7D.5 post-execution state.
Diagnosis proceeds against genuinely current state, not a stale
snapshot.

## 4. Exact Action-9 reconstruction (from the pinned proposition, not from 7D.5's summary)

Recovered verbatim from `docs/PHASE_149O_20L_7D_5_DELL_CLASS_B_PROVISIONING_CONTINUATION_EXECUTION.md`
§18 and independently cross-checked by rerunning it read-only on Dell:

- **Executable:** `/opt/pcae/runtime/venv/bin/python3` (invoked directly, not via a `pcae`/`pcae-launch` entry point).
- **Working directory:** `/opt/pcae/runtime/src`.
- **Effective identity:** `sudo -u pcae` (no further privilege).
- **Environment:** `env -i` (fully cleared) then `HOME=/home/pcae PATH=/usr/bin:/bin:/usr/sbin:/sbin PYTHONNOUSERSITE=1` — no `PYTHONPATH` set (absent, not merely empty).
- **Interpreter resolution:** absolute path, no PATH search for the interpreter itself.
- **Verifier entry point:** `pcae.core.hatp_class_b_conformance.verify_class_b_deployment_conformance()`, invoked via inline `python3 -c`.

This exact invocation — not a paraphrase — is the object of diagnosis
for HBDC-REQ-036 (§8 below).

## 5. Reproduction (determinism check)

Rerunning the exact, unchanged command above, read-only, once:

```
NON_COMPLIANT
... (39 checks total; unabridged output captured in this phase's working notes)
HBDC-REQ-030 False customization_module_agent_writable ('/usr/lib/python3.12/sitecustomize.py:path_is_symlink',)
HBDC-REQ-035 False pcae_distribution_metadata_not_found ()
HBDC-REQ-036 False no_configured_production_launcher_detected ()
HBDC-REQ-022 False pcae_distribution_metadata_not_found ()
HBDC-REQ-042 False no_repository_identity_present ('/opt/pcae/runtime/src',)
```

Failing set: `{HBDC-REQ-022, HBDC-REQ-030, HBDC-REQ-035, HBDC-REQ-036,
HBDC-REQ-042}` — identical to 7D.5's measurement. Deterministic; no
drift investigation required.

## 6. HBDC-001 v1.0 primary-contract reconstruction

Read directly from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
(not inferred from requirement IDs):

| Requirement | Normative text (verbatim, abridged) | Protected property | Category |
|---|---|---|---|
| HBDC-REQ-022 | "authorizes exactly one deployment model: Model A — PCAE authority modules execute from the canonical repository working tree via editable install ... consistent with HMIC-REQ-064." | deployment-model identity | deployment identity |
| HBDC-REQ-030 | "`sitecustomize.py` and `usercustomize.py`, wherever present on the resolved production `sys.path`, SHALL be admin-controlled and agent-unwritable, or absent." | customization-hook surface | environment lock |
| HBDC-REQ-035 | "Editable-install link metadata (`.pth` file, `direct_url.json`, egg-link, or equivalent) SHALL be admin-controlled and agent-unwritable in the production environment." | package-identity metadata integrity | environment lock |
| HBDC-REQ-036 | "If PCAE production execution passes through a launcher, wrapper, or service-manager configuration, that configuration SHALL be admin-controlled and agent-unwritable to the extent it affects module resolution, working directory, or [HBDC-REQ-028..033] environment variables." | launcher/wrapper integrity | environment lock |
| HBDC-REQ-042 | "`repository_instance_id` ... confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding`." | deployment-binding authority | deployment identity |

None of these five concerns raw filesystem/OS-principal topology
(§7–§11, already all-passing) — all five are either deployment-identity
checks (022, 042) or environment-lock checks (030, 035, 036), consistent
with 7D.5's own framing.

## 7. Verifier call-path mapping (read from the pinned SHA — confirmed byte-identical to `HEAD` via `git diff --stat`)

| Requirement | Function | File:line | Evidence source | Failure branch |
|---|---|---|---|---|
| HBDC-REQ-022 | `_check_model_a_deployment` | `hatp_class_b_conformance.py:64-92` | `importlib.metadata.distribution("pcae")` | `PackageNotFoundError` → `pcae_distribution_metadata_not_found` |
| HBDC-REQ-035 | `_check_editable_install_metadata` | `hatp_environment_lock_verifier.py:337-365` | `importlib.metadata.distribution("pcae")` | same `PackageNotFoundError` → `pcae_distribution_metadata_not_found` |
| HBDC-REQ-036 | `_check_launcher` | `hatp_environment_lock_verifier.py:368-382` | `shutil.which("pcae")` | returns `None` (not on `PATH`) → `no_configured_production_launcher_detected` |
| HBDC-REQ-030 | `_check_customization_modules` | `hatp_environment_lock_verifier.py:176-192`, using `_effective_write_access` at `hatp_class_b_topology_verifier.py:400-436` | `sys.path` scan for `sitecustomize.py`/`usercustomize.py` | `/usr/lib/python3.12/sitecustomize.py` found, `_effective_write_access` returns `(True, "path_is_symlink", ...)` unconditionally for any symlink |
| HBDC-REQ-042 | `_check_deployment_identity` | `hatp_class_b_conformance.py:94-...` | `repository_identity.read_repository_identity` | `identity is None` → `no_repository_identity_present` (expected — no `DeploymentBinding` exists or is authorized) |

## 8. HBDC-REQ-022 diagnosis

Independently verified, not accepted from 7D.5's hypothesis:

- **`pyproject.toml` line 6 at the pinned SHA:** `name = "pcae-harness"` (confirmed via `git show 7a3fa97...:pyproject.toml`; also unchanged at `HEAD`).
- **Installed distribution metadata on Dell:** `pip show pcae-harness` → `Name: pcae-harness, Version: 0.2.0, Editable project location: /opt/pcae/runtime/src`. `dist-info` directory: `pcae_harness-0.2.0.dist-info`, `root:pcae 0750`; `direct_url.json` and `RECORD` inside it: `root:pcae 0640`; not writable by `pcae` (`test -w` → false). No `__editable__*_finder.py` present (hatchling editable install uses `.pth` only).
- **Verifier lookup key:** literal `"pcae"` (§7 above), confirmed at both call sites.
- **`importlib.metadata` semantics:** distribution lookup is keyed by the *declared distribution/project name* (PEP 566/621 `Name:` metadata field), independent of any Python import package name. `pcae-harness`'s import package is `pcae` (`src/pcae/`), but its distribution name is `pcae-harness` — two distinct namespaces (confirmed by control case: `src/pcae/core/status.py:1996`, `exported_by_version()`, correctly calls `metadata.version("pcae-harness")`, not `"pcae"`).
- **Actual exception on Dell:** `importlib.metadata.PackageNotFoundError` for key `"pcae"`; a direct control lookup for `"pcae-harness"` on the same host resolves successfully (`FOUND 0.2.0 /opt/pcae/runtime/venv/.../pcae_harness-0.2.0.dist-info`, captured in 7D.5's own §20 and independently re-confirmed this phase).

**Disposition: A — production verifier implementation defect.** The
check's own literal lookup key (`"pcae"`) never matches this project's
declared distribution name (`"pcae-harness"`) under any installation
state; this is not an installation defect (Action 7 installed and
named the distribution correctly), not an Action-7 install-semantics
defect, and not an environment/invocation defect (the lookup key is a
hardcoded string in `hatp_class_b_conformance.py:72`, unaffected by any
Action-9 environment variable). The underlying Model-A property this
check exists to confirm (editable install, correctly named,
admin-controlled) is independently confirmed **true** on Dell — this is
a false negative, not a real deployment-model violation.

## 9. HBDC-REQ-035 diagnosis

Does **not** independently reach its own downstream evidence: `_check_editable_install_metadata`
calls the identical `importlib.metadata.distribution("pcae")` (§7) and
short-circuits on the same `PackageNotFoundError` before it ever
evaluates `dist_dir`/`direct_url.json`/`RECORD` writability. Proven,
not assumed, by reading the function body (`hatp_environment_lock_verifier.py:338-341`):
the `except PackageNotFoundError` branch returns `False` immediately,
identical in structure and literal string to REQ-022's own early-exit.

Independently confirmed the downstream property REQ-035 was designed
to check (`dist_dir`, `direct_url.json`, `RECORD` admin-controlled,
agent-unwritable) is **also independently true** on Dell (§8 evidence
above) — had the lookup key been correct, REQ-035 would have reached
its own body and returned `True`.

**Causal relation to REQ-022: proven, not assumed.** Both checks share
the exact same defective call (`importlib.metadata.distribution("pcae")`),
present verbatim in two different files. This is **one root defect**,
not two independent ones — REQ-035 does not measure a distinct
property that happens to also fail; it never gets the chance to
measure its own property at all.

**Disposition: A — production verifier implementation defect** (same
defect as REQ-022, distinct symptom ID).

## 10. Distribution-name source audit (isolation check)

```
grep -rn 'distribution("pcae")' src/pcae/
  → hatp_environment_lock_verifier.py:339
  → hatp_class_b_conformance.py:72
```

Exactly these two call sites, both already accounted for above. Control
case confirms the defect is **isolated, not repeated**: `src/pcae/core/status.py:1996`
(`exported_by_version()`) already uses the correct literal
`"pcae-harness"`. No other `importlib.metadata`/`PackageNotFoundError`
call site in `src/pcae/` references a distribution name at all (only
these two verifier functions and `status.py`'s version helper touch
`importlib.metadata`).

**Minimum exact repair surface:** two literal-string changes,
`hatp_class_b_conformance.py:72` and `hatp_environment_lock_verifier.py:339`,
`"pcae"` → `"pcae-harness"`. No other file requires a change for this
defect.

## 11. Packaging identity ground truth

Independently established, namespaces kept explicitly distinct:

| Namespace | Value |
|---|---|
| Project/distribution name (`pyproject.toml`) | `pcae-harness` |
| Import package name (`src/pcae/`) | `pcae` |
| CLI/console-script name (`[project.scripts]`, confirmed via `venv/bin/pcae` presence) | `pcae` |
| Installed metadata name (Dell `dist-info` directory) | `pcae_harness-0.2.0.dist-info` (normalized form of `pcae-harness`) |
| Editable-install metadata | `direct_url.json`: `{"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}` |
| Version | `0.2.0` |

The defect in §8–§10 is precisely this conflation: the verifier's
author used the *import package name* (`pcae`) as the
`importlib.metadata.distribution()` lookup key, where that API expects
the *distribution/project name* (`pcae-harness`). These are legitimately
different values for this project by design (a common, well-documented
Python packaging distinction) — not a bug in the project's naming, only
in the one call site's assumption that they'd be identical.

## 12. HBDC-REQ-036 diagnosis

**Normative property (§6):** launcher/wrapper configuration must be
admin-controlled and agent-unwritable, *if* production execution passes
through one.

**Verifier implementation:** `_check_launcher` resolves `shutil.which("pcae")`
against the *current process's* `PATH`, then checks the resolved
executable's effective write-access.

**Action-9's actual `PATH`:** `/usr/bin:/bin:/usr/sbin:/sbin` (§4) — does
not include `/opt/pcae/runtime/venv/bin`, the only directory on this
host containing anything named `pcae`.

**Whether HBDC-REQ-036 is actually violated:** independently checked —
**no.** Two candidate launcher artifacts exist on Dell, both
admin-controlled and agent-unwritable:

1. `/opt/pcae/runtime/bin/pcae-launch` (Action 8's wrapper): `root:pcae 750`, not writable by `pcae`.
2. `/opt/pcae/runtime/venv/bin/pcae` (the venv's own installed console-script entry point): `root:pcae 750`, not writable by `pcae`, `#!/opt/pcae/runtime/venv/bin/python3` shebang into `pcae.cli.main`.

**Diagnostic counterfactual — NOT an authorized Action-9 rerun,**
performed read-only to establish causality only: rerunning `which pcae`
as `pcae`, with `PATH` widened to
`/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`, resolves to
`/opt/pcae/runtime/venv/bin/pcae` — already admin-controlled and
agent-unwritable. Under this counterfactual `PATH`, `_check_launcher`
would return `True` (`launcher_agent_unwritable`) with **zero source
change**. This counterfactual establishes causality only; it is not
treated as a successful re-adjudication, and no Action-9 rerun using
this `PATH` was authorized or performed as an adjudication attempt.

**Whether an absolute-path executable should make `PATH` irrelevant:**
the verifier's own design (`shutil.which`) is inherently PATH-based —
it does not (and structurally cannot, as written) validate a launcher
invoked only by absolute path without ever appearing on any `PATH`.
This is a real, secondary gap in the check's generality (an
absolute-path-only launcher, which is in fact this project's Action-9
invocation's own pattern for the interpreter itself, is invisible to
`_check_launcher` under any `PATH`) — noted as a candidate future
hardening item (§16, finding B-149O.20L.7D.6-4), not the primary cause
of today's failure, since a `PATH`-discoverable, admin-controlled
launcher does exist and merely isn't exposed under Action-9's own
frozen `PATH`.

**Classification: A — proposition/Action-9 invocation defect
(primary).** The frozen Action-9 command's own `PATH` excludes the one
directory containing any discoverable, already-compliant launcher
artifact; widening it (a proposition-text change, not a source change)
resolves the check under the property that is already true today. A
secondary, non-blocking verifier-generality gap (`_check_launcher`
cannot recognize an admin-controlled launcher that is *never* placed on
any `PATH`, matching this project's own preferred absolute-path
invocation style) is recorded as a separate, lower-priority finding.

## 13. HBDC-REQ-030 diagnosis (mandatory)

**Implicated path:** `/usr/lib/python3.12/sitecustomize.py`.

**Provenance — why it enters the customization search surface:**
`_check_customization_modules` iterates `_effective_sys_path_dirs()`
(every existing directory on `sys.path`) and checks each for
`sitecustomize.py`/`usercustomize.py`. Reconstructed the actual Dell
`sys.path` under the exact Action-9 invocation: it includes
`/usr/lib/python3.12/` (the interpreter's own standard-library
directory, `/usr/bin/python3.12`'s default `sys.path` entry — present
regardless of venv, `PYTHONPATH` (unset), CWD, or user-site (disabled)
— this is the CPython stdlib's own default search path, not introduced
by any PCAE action).

**Evidence (read-only, live Dell):**

| Property | Value |
|---|---|
| Path | `/usr/lib/python3.12/sitecustomize.py` |
| Type | symlink |
| Symlink owner/mode | `root:root 0777` (standard Debian/Ubuntu symlink-mode convention — irrelevant to *symlink retargeting*, only to *following* it) |
| Symlink target | `/etc/python3.12/sitecustomize.py` |
| Target owner/mode | `root:root 0644` |
| Parent directory (`/usr/lib/python3.12/`) owner/mode | `root:root 0755` |
| ACL (symlink and parent) | none beyond standard POSIX bits (`getfacl` — no extended entries) |
| `pcae` write access — symlink itself | `test -w` → false |
| `pcae` write access — target | `test -w` → false |
| `pcae` write access — parent dir (would allow symlink replacement) | `test -w` → false |
| dpkg ownership | `libpython3.12-minimal:amd64` (stock Ubuntu package, not a PCAE artifact) |

**Effective writability — established, not assumed from mode strings
alone:** the only three channels by which `pcae` could ever control
this file's effective content — writing the symlink itself, writing its
target, or writing the parent directory to replace the symlink — are
all closed. Class-B effective-access semantics (`_effective_write_access`)
were consulted for methodology (mode/group/ACL layering) but its
symlink branch itself is exactly what's under diagnosis here, so the
manual channel-by-channel check above is the independent verification,
not a re-application of the same function under test.

**Root cause of the false failure:** `_effective_write_access` (`hatp_class_b_topology_verifier.py:415-416`)
returns `(True, "path_is_symlink", ...)` **unconditionally** for any
symlink, regardless of whether the symlink itself, its target, or its
parent directory is actually agent-writable. This is a deliberate
fail-closed design applied elsewhere in this codebase to symlink-swap
attack surfaces (e.g., Protected Root's own dedicated `_reject_symlink`/
ancestor-chain logic) — but here it is applied as a blunt, unconditional
rule rather than the more precise ancestor-chain-aware check used for
Protected Root itself, and it fires even where no writable channel
exists.

**Classification: F — false diagnosis / requirement actually
satisfied**, caused by a real but narrower verifier defect (overly
broad symlink handling) than REQ-022/035's literal-string bug.
HBDC-REQ-030's actual normative property — `sitecustomize.py`/
`usercustomize.py` admin-controlled and agent-unwritable — **is true**
on Dell today, independently confirmed via three separate write-access
channels, none open. No host mutation, no Action-9 change, and no
`src/pcae/**` change is required to make HBDC-REQ-030 *actually*
compliant, because it already is; a future verifier-hardening finding
(§16, B-149O.20L.7D.6-3) is recorded for the blunt symlink rule, but it
is not a blocking defect for HBDC compliance today, since the current
behavior is a safe-direction (over-flagging, not under-flagging) false
positive.

## 14. Cross-failure causal graph

```
[literal "pcae" lookup key]  →  HBDC-REQ-022  (hatp_class_b_conformance.py:72)
        │
        └───────────────────  →  HBDC-REQ-035  (hatp_environment_lock_verifier.py:339, identical call)
                                   (same root defect — one fix, two symptom IDs)

[Action-9 frozen PATH excludes venv/bin]  →  HBDC-REQ-036  (independent — invocation-level, not source-level)

[_effective_write_access unconditional symlink=True]  →  HBDC-REQ-030  (independent — different function,
                                                            different file, no relation to the other three)

[no DeploymentBinding exists or is authorized]  →  HBDC-REQ-042  (independent, expected, not a defect)
```

Four reason IDs, **two** independent root causes among the four
unexpected failures (022+035 share one; 030 and 036 are each their own),
plus the separately-expected REQ-042. Not four independent defects, and
not one single defect either.

## 15. HBDC-REQ-042 reconfirmation

`find .pcae -iname '*deploymentbinding*'` (local repo) and
`sudo find /opt/pcae /etc/pcae -iname '*deploymentbinding*'` (Dell):
both zero matches. No DeploymentBinding exists anywhere in either the
repository's governance state or on the live host. No authority exists
in this phase (or any prior phase) to create one. HBDC-REQ-042 failing
is the **expected, architecturally-mandated** state under the current
(no-DeploymentBinding) architecture — not attempted to be eliminated,
per the governing instruction §20.

## 16. Blocking findings

- **B-149O.20L.7D.6-1 — Distribution metadata lookup mismatch
  (HBDC-REQ-022/035).** `hatp_class_b_conformance.py:72` and
  `hatp_environment_lock_verifier.py:339` both call
  `importlib.metadata.distribution("pcae")`; the project's declared
  distribution name is `pcae-harness`. Causes both checks to report
  `NON_COMPLIANT` (`PackageNotFoundError`) even though the actual
  Model-A editable-install and editable-metadata properties they exist
  to verify are independently confirmed true. **Primary defect class:
  PRODUCTION VERIFIER DEFECT.**

- **B-149O.20L.7D.6-2 — Action-9 environment-lock invocation PATH gap
  (HBDC-REQ-036).** The frozen Action-9 command's `PATH`
  (`/usr/bin:/bin:/usr/sbin:/sbin`) excludes
  `/opt/pcae/runtime/venv/bin`, the only directory containing any
  `which`-discoverable, already-admin-controlled launcher artifact.
  Diagnostic counterfactual (§12) confirms widening `PATH` alone (no
  source change) resolves the check. **Primary defect class:
  PROPOSITION / ACTION-9 INVOCATION DEFECT.**

- **B-149O.20L.7D.6-3 — Overbroad symlink write-access heuristic
  (HBDC-REQ-030, currently a false positive only).**
  `_effective_write_access` (`hatp_class_b_topology_verifier.py:415-416`)
  treats every symlink as unconditionally agent-writable, without
  checking whether the symlink itself, its target, or its parent
  directory is actually agent-writable. Currently produces a false
  `NON_COMPLIANT` for the stock Ubuntu `sitecustomize.py` symlink, whose
  actual writability is independently confirmed closed on all three
  channels. **Primary defect class: FALSE DIAGNOSIS / REQUIREMENT
  ACTUALLY SATISFIED**, with a secondary, non-blocking verifier-hardening
  opportunity recorded (fail-closed direction, lower priority than
  B-149O.20L.7D.6-1/-2).

- **B-149O.20L.7D.6-4 — `_check_launcher`'s `which`-based resolution
  cannot recognize an absolute-path-only launcher (non-blocking,
  informational).** Recorded because Action-9's own invocation pattern
  (interpreter invoked by absolute path, deliberately narrow `PATH`) is
  itself an example of the pattern `_check_launcher` cannot validate.
  Not a blocking defect today (a `PATH`-discoverable launcher does
  exist and is already compliant) — recorded for a future verifier
  contract-evolution phase to consider, not for immediate repair.

## 17. Final diagnosis matrix

| Requirement | Failure reason | Verifier function | Dell evidence | Root cause | Primary defect class | Repair surface | Authority impact | Independent verification required | Status |
|---|---|---|---|---|---|---|---|---|---|
| HBDC-REQ-022 | `pcae_distribution_metadata_not_found` | `_check_model_a_deployment` | `distribution("pcae")` raises; `distribution("pcae-harness")` resolves | Literal lookup-key mismatch (import-vs-distribution-name conflation) | PRODUCTION VERIFIER DEFECT | `hatp_class_b_conformance.py:72` | Governed `src/pcae/**` repair + independent verification required before redeploy | Yes | Diagnosed, repair pending |
| HBDC-REQ-035 | `pcae_distribution_metadata_not_found` | `_check_editable_install_metadata` | Same lookup, short-circuits before own body | Same defect as REQ-022 (shared root cause) | PRODUCTION VERIFIER DEFECT | `hatp_environment_lock_verifier.py:339` | Same governed repair as REQ-022 (single phase can cover both) | Yes | Diagnosed, repair pending |
| HBDC-REQ-036 | `no_configured_production_launcher_detected` | `_check_launcher` | `which("pcae")` empty under frozen `PATH`; resolves under counterfactual `PATH` to an already-compliant launcher | Action-9's own frozen `PATH` excludes venv `bin/` | PROPOSITION / ACTION-9 INVOCATION DEFECT | Action-9 command text (proposition), not source | Requires proposition amendment + fresh CHGR (current CHGR binds the old command text) | Yes (re-adjudication) | Diagnosed, amendment pending |
| HBDC-REQ-030 | `customization_module_agent_writable` | `_check_customization_modules` via `_effective_write_access` | `/usr/lib/python3.12/sitecustomize.py`, symlink, all 3 write channels closed | Unconditional symlink=writable heuristic (false positive) | FALSE DIAGNOSIS / REQUIREMENT ACTUALLY SATISFIED | (none required for compliance; optional future verifier hardening) | None — no repair needed for HBDC compliance | No (property already satisfied) | Diagnosed, no action required |
| HBDC-REQ-042 | `no_repository_identity_present` | `_check_deployment_identity` | No DeploymentBinding anywhere (repo or Dell) | No DeploymentBinding exists/authorized (by design) | EXPECTED AUTHORIZED RESIDUAL (not a defect) | n/a | n/a | n/a | Reconfirmed expected |

## 18. Source-repair consequences (022/035, not implemented)

- Requires a new, narrow source commit in this repository:
  `"pcae"` → `"pcae-harness"` at the two call sites in §10.
- The Dell checkout is pinned to `7a3fa971...`; fixing this repository's
  `HEAD` does **not** change what's running on Dell. Redeployment
  (a new Action 6, at a new pinned SHA) is a separate, governed action.
- The current CHGR (`chgr-541cb08c313b4f8884970172d37c5a1d`) authorizes
  actions bound to the *current* pinned SHA; deploying a corrected SHA
  requires either an amendment to this CHGR's pinned-SHA binding
  (matching the 7D.3 Action-6 amendment pattern) or a fresh continuation
  CHGR.
- Neither `hatp_class_b_conformance.py` nor `hatp_environment_lock_verifier.py`
  is currently a member of HMIC-001's frozen 25-file identity (both
  modules' own docstrings disclaim this) — a fix here does not touch
  HMIC certification scope and does not itself require an HMIC contract
  evolution.
- Per this project's established pattern, a source repair phase must be
  followed by its own independent-verification phase before any
  redeployment/re-pin is authorized.
- The repaired verifier cannot simply be "copied onto Dell" — it must go
  through the same governed Action-6-equivalent redeployment sequence as
  any other source change, under a properly re-scoped authority.

## 19. Proposition-repair consequences (036, not implemented)

- **Old command environment:** `PATH=/usr/bin:/bin:/usr/sbin:/sbin` (§4).
- **Required changed environment:** `PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin`
  (confirmed sufficient by the diagnostic counterfactual in §12 — no
  other change needed for REQ-036 specifically).
- Actions 6–8 remain entirely untouched by this change — it is scoped
  to the Action-9 command text alone.
- Only Action 9 requires new approval; Actions 1–8's own postconditions
  are unaffected by an Action-9 `PATH` change.
- The current CHGR authorizes the *old* frozen Action-9 command text
  verbatim (consistent with this project's governance discipline of
  pinning commands, not just goals, in propositions); it becomes
  insufficient once that text changes, and a fresh CHGR (or an explicit
  amendment, per the 7D.3 precedent) is required before any changed
  Action-9 rerun can be treated as an authorized re-adjudication.

## 20. Host-prerequisite consequences (030)

None required. HBDC-REQ-030's underlying property is independently
confirmed already satisfied (§13); no host mutation, no Boundary-P
infrastructure change, and no separate admin-prerequisite authority is
needed for this requirement specifically. The only open item is an
optional, non-blocking verifier-hardening finding (B-149O.20L.7D.6-3)
for a future contract-and-implementation phase to consider.

## 21. Sequencing of future phases

Multiple defect classes are present (source defect + proposition defect
+ one false-positive-only finding); sequenced per the governing
instruction's preference to fix production semantics before
re-authorizing/re-running Action 9:

1. **149O.20L.7D.7 (recommended next phase)** — narrow `src/pcae/**`
   source repair: correct the two `importlib.metadata.distribution("pcae")`
   call sites to `"pcae-harness"` (B-149O.20L.7D.6-1). Diagnosis-driven,
   minimal-diff, no other file touched.
2. **149O.20L.7D.8** — independent verification of the 7D.7 repair
   (standard project pattern: every repair gets its own verification
   phase before it's trusted for redeployment).
3. **149O.20L.7D.9** — proposition amendment: widen the Action-9 `PATH`
   per §19 (B-149O.20L.7D.6-2), obtain a fresh CHGR (or amendment) that
   explicitly supersedes the old Action-9 command text and does not
   fall back to it, and — in the same or an immediately following
   phase — redeploy the 7D.7-repaired source to Dell (a new Action 6
   at a new pinned SHA, under the amended/fresh authority) before
   re-running Action 9.
4. **149O.20L.7D.10** — re-run the amended Action-9 command against the
   redeployed source and re-adjudicate. Expected result if all of the
   above lands cleanly: exactly `{HBDC-REQ-042}`.
5. Only after a clean 149O.20L.7D.10 adjudication does **149O.20L.7E**
   become recommendable, per the standing precondition already stated
   in 7D.5's own recommendation.

B-149O.20L.7D.6-3/-4 (verifier hardening) are non-blocking and can be
picked up opportunistically in a later contract-and-implementation wave
(not on the critical path to 7E).

## 22. No-Go confirmations

This phase performed exactly: entry-state reads, a live read-only
Dell state-preservation check, one unchanged read-only Action-9 rerun
(determinism only, not a re-adjudication), and read-only source/contract
reading and diagnostic PATH/write-access probes (also read-only —
`test -w`, `which`, `getfacl`, `stat`, none of which mutate). No
`chmod`/`chown`/`rm`/`mkdir`/venv-recreate/reinstall/wrapper-modify/
checkout-modify/user-group-change/ACL-change/system-Python-change/
customization-module-create-or-delete command was issued against Dell.
No `src/pcae/**`, `scripts/**`, or `docs/contracts/**` file was
modified (`git diff --stat 7a3fa97... HEAD -- src/pcae/ scripts/
docs/contracts/` — empty). No repair authorization was requested or
obtained. No amended Action 9 was run as an adjudication attempt — only
the unchanged command (determinism, §5) and a clearly-labeled,
non-authoritative diagnostic counterfactual (§12) were executed. No
DeploymentBinding, HMIC certification, `HATP_MANDATORY` activation, or
Cutover Record was created. Actions 6–8 were not rolled back — none
failed its own postcondition, and this phase's own live-state check
(§3) reconfirms them unchanged. No `--no-verify`, no force push, no raw
`git commit`/`git push` bypassing the governed CLI.

## 23. Test results

New, independently-authored companion test module
`tests/test_phase_149o_20l_7d_6_action_9_unexpected_residual_diagnosis.py`
(imports nothing from 7D.5's own test module as oracle): 21 tests,
re-run three consecutive times, 21 passed each run, no flake. Covers:
pinned-SHA/current-source identity, no-production-modification proof,
distribution-name literal-mismatch evidence, REQ-022/035 shared-root-cause
proof, `importlib.metadata` namespace-distinction control case,
REQ-030 live write-access evidence and false-diagnosis classification,
REQ-036 counterfactual-vs-authorized-PATH distinction, causal-graph
partition, REQ-042 reconfirmation, exact reproduced failing-set match,
Dell/wrapper identity constants, and a no-mutating-git-invocation proof
for this module's own git usage.

## 24. Governance results

- `pcae_health`: healthy
- `pcae_check`: passed
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — historical `tasks/active/`/`tasks/done/` bookkeeping gaps predating this phase; outside this phase's allowed-file scope)
- `pcae_push_check`: clean (`nothing_to_push`) at phase entry
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: Telegram configured/enabled
- `telegram_runtime`: loaded
- `fast_green` (targeted, this phase's own new companion test module, cited honestly as this phase touches zero other `src/pcae/**`/`tests/**` files): 21 passed, 0 failed, 3 consecutive runs, no flake
- `no_production_source_repair_this_phase`: confirmed (`git diff --stat` against pinned SHA for `src/pcae/`, `scripts/`, `docs/contracts/` — empty)
- `no_dell_mutation_this_phase`: confirmed (§22)
- `deploymentbinding_boundary_c_a_untouched`: confirmed (§15, §22)

## 25. Required final status

- **Actions 1–8:** PROVISIONED — CURRENT HOST STATE PRESERVED (independently re-verified this phase, §3; not upgraded to "independently verified provisioning," which is out of this phase's scope).
- **Action 9:** UNEXPECTED RESIDUAL DIAGNOSED / REPAIR PENDING.
- **Class-B:** INFRASTRUCTURE PRESENT — HBDC CONFORMANCE BLOCKED.
- **DeploymentBinding:** ABSENT / NOT AUTHORIZED.
- **Boundary C:** NOT AUTHORIZED.
- **Boundary A:** NOT AUTHORIZED.
- **HATP:** NOT READY.
- **Runtime:** Observed / observe / unavailable.

## 26. Recommended next phase

**149O.20L.7D.7 — Distribution-Name Verifier Narrow Source Repair
(HBDC-REQ-022/035).** Correct the two `importlib.metadata.distribution("pcae")`
call sites (`hatp_class_b_conformance.py:72`,
`hatp_environment_lock_verifier.py:339`) to `"pcae-harness"` —
B-149O.20L.7D.6-1's minimum exact repair surface (§10, §16, §17, §18).
Not 149O.20L.7E: per §21's sequencing, the source defect, the
proposition/PATH defect, and a fresh redeployment + re-adjudication
must all land cleanly first, with a clean re-adjudication measuring
exactly `{HBDC-REQ-042}` before 149O.20L.7E is recommendable.
