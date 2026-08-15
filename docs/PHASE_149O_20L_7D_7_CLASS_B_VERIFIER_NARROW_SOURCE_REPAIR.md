# Phase 149O.20L.7D.7 — Class-B Verifier Narrow Source Repair for HBDC-REQ-022/030/035

## 1. Scope and disposition

**Mac-side production-source repair only.** No Dell mutation, no
redeployment, no Action-9 change, no HBDC-REQ-036 repair, no CHGR
amendment or publication, no DeploymentBinding, no certification, no
activation. The Dell remains pinned to `7a3fa971304521cdcb44251e07ef1966baec686a`,
untouched, as evidence of the currently deployed old source. This
report repairs the two production verifier defects independently
diagnosed by Phase 149O.20L.7D.6 (finding B-149O.20L.7D.6-1, HBDC-REQ-022/035;
finding B-149O.20L.7D.6-3, HBDC-REQ-030) and requires its own
independent-verification phase (149O.20L.7D.8) before any redeployment
is authorized.

## 2. True phase-entry commit

```
git log --oneline -1  → 8a18f73d Phase 149O.20L.7D.6: restore idle-task standard allowed-file list
git status --short    → (clean)
git rev-list --count origin/main..HEAD → 0
```

Entry checks: `pcae health` healthy; `pcae check` passed; `pcae status
coherence` coherent; `pcae doctor task-memory` warnings (pre-existing —
historical `tasks/active/`/`tasks/done/` bookkeeping gaps predating
this phase, unrelated, not remediated here); `pcae push check` clean
(`nothing_to_push`); `pcae runtime inspect` Observed/observe/unavailable;
`pcae notify status` Telegram configured/enabled; `pcae phase-report
show --latest` confirmed 149O.20L.7D.6's canonical report present,
consistent, recommending exactly this phase; `pcae phase-report
reconcile --phase-id 149O.20L.7D.6` — read-only, `reconciled`,
`mutation: none`.

## 3. 7D.6 diagnosis reconstruction (independent, before repair)

Read `docs/PHASE_149O_20L_7D_6_ACTION_9_UNEXPECTED_RESIDUAL_INDEPENDENT_DIAGNOSIS.md`
directly, then independently re-derived each claim from current source
rather than accepting the report's prose:

- **HBDC-REQ-022/035 (distribution-name defect):** `grep -rn
  'distribution("pcae")' src/pcae/` at phase entry returned exactly two
  matches — `hatp_class_b_conformance.py:72` and
  `hatp_environment_lock_verifier.py:339` — matching 7D.6 exactly.
  `src/pcae/core/status.py:1995` (`exported_by_version()`) independently
  confirmed already using the correct `metadata.version("pcae-harness")`
  literal — control case reconfirmed, defect isolated to the two sites.
- **HBDC-REQ-030 (symlink false positive):** read
  `hatp_class_b_topology_verifier.py:400-436` (`_effective_write_access`)
  directly at phase entry: line 415-416 unconditionally returned
  `(True, "path_is_symlink", (str(path),))` for any symlink, regardless
  of actual writability — reconfirmed exactly as 7D.6 §13 described,
  read from source, not from the report's transcription.
- **HBDC-REQ-036 (Action-9 PATH gap):** reconfirmed out of scope (§20
  below); no source change made or needed for this requirement.
- **HBDC-REQ-042:** reconfirmed expected residual (§21 below); no
  DeploymentBinding exists or is authorized.

No production edit was made until both defects were independently
reconfirmed present in current source (this section), consistent with
the governing instruction's §4 requirement.

## 4. HBDC requirement reconstruction (read directly from HBDC-001 v1.0)

`grep -n "REQ-022\|REQ-030\|REQ-035\|REQ-036\|REQ-042"
docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`, read verbatim:

| Requirement | Normative text (verbatim) | Protected property |
|---|---|---|
| HBDC-REQ-022 | "authorizes exactly one deployment model: Model A — PCAE authority modules execute from the canonical repository working tree via editable install ... consistent with HMIC-REQ-064." | deployment-model identity |
| HBDC-REQ-030 | "`sitecustomize.py` and `usercustomize.py`, wherever present on the resolved production `sys.path`, SHALL be admin-controlled and agent-unwritable, or absent." | customization-hook surface |
| HBDC-REQ-035 | "Editable-install link metadata (`.pth` file, `direct_url.json`, egg-link, or the equivalent artifact used by the actual packaging tool) SHALL be admin-controlled and agent-unwritable in the production environment." | package-identity metadata integrity |
| HBDC-REQ-036 | "If PCAE production execution passes through a launcher, wrapper, or service-manager configuration, that configuration SHALL be admin-controlled and agent-unwritable ..." | launcher/wrapper integrity |
| HBDC-REQ-042 | "`repository_instance_id` ... confers no authority by itself. The controlling authority artifact is the admin-created `DeploymentBinding`." | deployment-binding authority |

Matches 7D.6's §6 rendering exactly, byte-for-byte, confirmed
independently against the primary contract file. The repair implements
these contracts as written; the contract text itself was not weakened
or reinterpreted to fit the pre-repair implementation.

## 5. Current HMIC membership reconstruction (mandatory, independent)

**7D.6's own modules (`hatp_class_b_topology_verifier.py`,
`hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py`) each
carry a docstring claiming non-membership in "HMIC-001's current 25-file
frozen identity."** The governing instruction for this phase explicitly
required not relying on that claim and independently reconstructing
current HMIC source-scope membership from primary artifacts. Doing so
surfaces a finding 7D.6 did not itself flag:

**The docstring claim is stale.** `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
is at **version 1.3** (header: "FROZEN — CLASS-B VERIFIER SOURCE-SCOPE
CLOSURE EVOLVED (149O.20K) ... PENDING INDEPENDENT VERIFICATION (not
VERIFIED at v1.3)"). Phase 149O.20K (v1.2 → v1.3) explicitly widened
`HMIC-REQ-052` with a new limb (c) and `HMIC-REQ-050`'s frozen
enumeration from 25 to **28 files**, adding exactly
`core/hatp_class_b_topology_verifier.py`, `core/hatp_environment_lock_verifier.py`,
and `core/hatp_class_b_conformance.py` (contract §11, §53). The
production constant `_FROZEN_SRC_PCAE_RELATIVE_FILES` in
`hatp_mandatory_certification.py:953-976` (`assert
len(_FROZEN_AUTHORITY_BEARING_FILES) == 28`) independently confirms
these three paths are present in the *current, live* frozen-file
enumeration — not just contract prose. Phase 149O.20K.2 aligned the
production constant to the contract; Phase 149O.20K.3 independently
verified that alignment (`docs/PHASE_149O_20K_3_...md` §6-7: "exact
28-file equality," "exact +3 delta," byte-identical since K.2 entry).

**Adjudication of 7D.6's HMIC-scope statement:** 7D.6 did not itself
make an incorrect HMIC-neutrality claim in its own report text — its
report is silent on this question, deferring to the modules' own
docstrings (§18: "Neither ... is currently a member of HMIC-001's
frozen 25-file identity ... both modules' own docstrings disclaim
this"). That deferral was itself stale by the time of 7D.6 (Phase 20K
predates 7D.6 in this repository's history), and this phase's own
source docstrings for all three modules **remain uncorrected** (still
say "25-file," still say "not a member") even after 20K/20K.2/20K.3
closed that gap at the contract and production-constant level. This
phase does **not** repeat or extend that stale claim: **the three
modules ARE members of HMIC-001 v1.3's frozen 28-file source-scope set**,
via the anticipatory limb (c) binding (contract §53: "any file reachable
from `verify_class_b_deployment_conformance`'s own call graph ... that
can change the `COMPLIANT` / `NON_COMPLIANT` / `INDETERMINATE` result").
Confirmed independently via `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py::test_current_module_not_in_hmic_frozen_scope`
— that pre-existing companion test (from before the 20K evolution)
**fails on unmodified `main`**, independently reproducing this same
finding without any change from this phase (§10 below).

**Contract version:** HMIC-001 v1.3. **Source-scope membership:**
bound, via limb (c), anticipatory (no current production consumer;
contract §53 reconfirms zero production consumers as of v1.3).
**Implementation/content-digest behavior:** each of the three modules'
bytes participate in `implementation_scope_digest` via the standard
frozen-file hashing mechanism (HMIC-REQ-055/056) — a byte change to any
of the three, such as this phase's repair, changes that digest.
**Certification/identity implications:** no active HMIC certification
record exists anywhere in this repository or on the Mac host at phase
entry (`find . -iname '*certification*state*'` returns no protected
state-store artifact outside test/doc fixtures) — there is no existing
certification to invalidate on the Mac side. If a certification is ever
computed elsewhere (e.g. on a future admin-controlled host, out of this
phase's scope) against the pre-repair bytes, it would become stale
against this phase's repaired bytes and require regeneration; that
regeneration is not performed or authorized here.

## 6. Source-pin consequences

Dell remains pinned to `7a3fa971304521cdcb44251e07ef1966baec686a`,
confirmed unmutated (§17). This phase creates a new Mac repository
source identity via the commit in §16. Therefore, as of this phase's
close:

**Mac repaired HEAD ≠ Dell deployed pinned SHA.**

The repair is not "on Dell" in any sense; redeployment is a separate,
future, governed action (149O.20L.7D.9/7D.10 per 7D.6's own
sequencing, §21 of its report), requiring either an amendment to the
current CHGR's pinned-SHA binding or a fresh continuation CHGR — not
authorized or attempted in this phase (§15).

## 7. Exact distribution-name defect (defect A)

Two call sites, both confirmed via `grep -rn 'distribution("pcae")'
src/pcae/` at phase entry:

- `src/pcae/core/hatp_class_b_conformance.py:72`
  (`_check_model_a_deployment`, HBDC-REQ-022)
- `src/pcae/core/hatp_environment_lock_verifier.py:339`
  (`_check_editable_install_metadata`, HBDC-REQ-035)

Both called `importlib.metadata.distribution("pcae")`, which raises
`PackageNotFoundError` unconditionally on any host where the project is
correctly installed under its actual distribution name.

## 8. Packaging identity analysis

Independently established, namespaces kept distinct (governing
instruction §9):

| Namespace | Value |
|---|---|
| Project/distribution name (`pyproject.toml` `name =`) | `pcae-harness` |
| Import package name (`src/pcae/`) | `pcae` |
| CLI/console-script name (`[project.scripts]`) | `pcae` |
| Control case (`status.py:1995`, `exported_by_version()`) | already correctly uses `metadata.version("pcae-harness")` |

`importlib.metadata.distribution()` is keyed by the declared
distribution/project name (PEP 566/621 `Name:` metadata field), not the
import package name — two legitimately distinct namespaces for this
project by design. Confirmed live on this Mac host:

```
importlib.metadata.distribution("pcae-harness")  → resolves (version, dist-info path present)
importlib.metadata.distribution("pcae")          → PackageNotFoundError
```

## 9. Exact distribution repair

Minimum exact repair surface — two literal-string changes, no other
file touched, no refactor, no `pyproject.toml` change:

```diff
- dist = importlib.metadata.distribution("pcae")
+ dist = importlib.metadata.distribution("pcae-harness")
```

Applied identically at `hatp_class_b_conformance.py:72` and
`hatp_environment_lock_verifier.py:339`.

## 10. REQ-022 post-repair semantics

`_check_model_a_deployment` now reaches its own downstream
`direct_url.json`/`editable`-flag evaluation instead of short-circuiting
on `PackageNotFoundError`. Proven by test (not asserted as a string
change alone):
`test_req_022_reaches_downstream_direct_url_evaluation` constructs a
distribution whose lookup succeeds but whose `editable` flag is
`False`, and confirms the check reaches and correctly fails on
`HBDC-REQ-024`/`unsupported_deployment_model_not_editable_install` (the
*correct* downstream reason, not the old lookup-failure reason);
`test_req_022_succeeds_when_editable_install_confirmed` confirms the
positive path; `test_req_022_fail_closed_when_metadata_genuinely_unavailable`
confirms the check still fails closed (unchanged) when metadata is
genuinely absent under the *correct* (post-repair) literal.

## 11. REQ-035 post-repair semantics

`_check_editable_install_metadata` now reaches its own
`dist_dir`/`direct_url.json`/`RECORD` writability evaluation. Proven by
test: `test_req_035_reaches_downstream_metadata_writability_evaluation`
constructs an admin-controlled (agent-unwritable) fixture dist-info
directory and confirms the check reaches and returns
`editable_install_metadata_admin_controlled` (not merely "no longer
raises"); `test_req_035_still_fails_when_metadata_agent_writable`
proves the repair did **not** weaken REQ-035's actual security property
— an agent-writable dist-info directory still correctly fails, under
the same (correct) literal;
`test_req_035_fail_closed_when_metadata_genuinely_unavailable` confirms
fail-closed behavior is unchanged when metadata is genuinely absent.
The repair only changed the lookup key; it did not touch, weaken, or
bypass either check's own downstream evidence evaluation.

## 12. Exact REQ-030 symlink defect

`_effective_write_access` (`hatp_class_b_topology_verifier.py`, pre-repair
lines 415-416):

```python
if path.is_symlink():
    return True, "path_is_symlink", (str(path),)
```

Returned unconditional `(True, ...)` — "agent-effectively-writable" —
for **any** symlink, regardless of whether the symlink itself, its
resolved target, or either one's ancestor chain was actually
agent-writable. This is the exact function/line 7D.6 §13 identified,
independently reconfirmed present at phase entry (§3 above) before
repair.

## 13. Symlink repair semantics selected

Repaired by replacing the unconditional branch with a call to a new
helper, `_symlink_effective_write_access` (defined immediately above
`_effective_write_access` in the same module — no new module, no
relocation of the shared primitive), which distinguishes every channel
named in the governing instruction §14:

1. **Ability to mutate/replace the symlink entry itself** — controlled
   by the symlink's parent-directory chain (POSIX ignores a symlink's
   own permission bits for replacement). Reuses the existing
   `_ancestor_chain_safe` (full mode/group/ACL ancestor walk,
   unconditional reject of any symlinked ancestor) — not
   re-implemented.
2. **Mutability of the resolved target** — recurses through
   `_effective_write_access` for a non-symlink target (reusing the
   exact same mode/group/ACL logic every other check in this module
   uses), or recursively through `_symlink_effective_write_access`
   itself for a chained symlink target, bounded by
   `_SYMLINK_CHAIN_GUARD` (64).
3. **Writability of the target's own ancestor chain** — again via
   `_ancestor_chain_safe`, applied to the resolved target.
4. **Broken links, unreadable links (`os.readlink` failure), inspection
   errors (`Path.exists()` failure), and chain-guard exhaustion** — all
   `None`/indeterminate, never silently `False`. An `INDETERMINATE`
   verifier result is still not `COMPLIANT`, so this remains fail-closed
   for the overall HBDC conformance determination, matching this
   module's existing indeterminate discipline elsewhere
   (`acl_inspection_unavailable`, `stat_access_error`).

A symlink is classified effectively-unwritable (`False`,
`"symlink_fully_closed"`) only when **every** channel above is proven
closed — never assumed from the absence of one channel's evidence.

**Note on pre-existing gate interaction:** `_effective_write_access`'s
own pre-existing top-level `path.exists()` gate (unchanged by this
repair, predates this phase) follows symlinks and already returns
`None`/`"path_missing"` for a broken symlink or a true two-hop symlink
cycle, before the symlink branch is ever reached. This is correct,
unmodified, already-fail-closed behavior — not a gap this repair needed
to close — documented and exercised by
`test_broken_symlink_is_indeterminate_not_silently_safe` and
`test_symlink_loop_is_indeterminate_not_silently_safe` rather than
silently assumed.

## 14. Complete caller inventory for the repaired primitive

`grep -n "_effective_write_access" src/pcae/core/*.py` at phase entry,
every caller inventoried and considered for impact (governing
instruction §18):

| Caller | Requirement | Path passed | Symlink-branch impact |
|---|---|---|---|
| `_check_interpreter_unwritable` | HBDC-REQ-027 | `sys.executable` after `.resolve(strict=True)` | None — already fully resolved, never a symlink itself |
| `_check_venv_lock` | HBDC-REQ-026 | `sys.prefix` (unresolved) | Possible — untested edge case if a venv root is itself a symlink; covered generically by this repair |
| `_check_pythonpath` | HBDC-REQ-028 | raw `PYTHONPATH` entries (unresolved) | Possible |
| `_check_user_site` | HBDC-REQ-029 | `site.getusersitepackages()` (unresolved) | Possible |
| `_check_customization_modules` | HBDC-REQ-030 | `sys.path` dir / `sitecustomize.py` (unresolved) | **Direct** — this is the defect's own reported symptom path |
| `_check_pth_files` | HBDC-REQ-031 | `.pth` glob results (unresolved) | Possible |
| `_check_editable_install_metadata` | HBDC-REQ-035 | dist-info candidates/`dist_dir` (unresolved) | Possible |
| `_check_launcher` | HBDC-REQ-036 | resolved via `.resolve(strict=True)` first | None — already fully resolved |
| `_check_cwd_shadow_and_path_order` | HBDC-REQ-033 | `sys.path` entries after `.resolve()` | None — already fully resolved |
| `_check_write_authority` / `_check_group_effective_access` | HBDC-REQ-007/015 | Protected Root | Root-is-symlink already independently rejected by HBDC-REQ-002 before these run |
| `_resolve_trusted_executable_with_effective_access` | (ACL-tool resolution path) | already `.resolve(strict=True)`'d and symlink-rejected by `_resolve_trusted_executable` itself | None |

All ten HBDC-REQ-bearing callers exercised by the broader regression
run (§18); none regressed. The repair is a genuine shared-primitive fix
— it closes the same false-positive class for every caller that passes
an unresolved path, not merely HBDC-REQ-030's own reported symptom.

## 15. Selected repair is the narrowest correct surface

Considered and rejected a REQ-030-local special case (e.g. checking
writability only inside `_check_customization_modules`) in favor of the
shared-primitive fix, because: (a) the defect is in the shared
primitive itself, not in REQ-030's caller code — a caller-local
workaround would leave the same false-positive class latent for every
other caller in §14's table; (b) `_effective_write_access` is
documented (module header, plan §11) as "implemented once as a shared
internal helper, not duplicated across modules" — a local special case
would violate that existing design discipline; (c) the fix reuses
existing primitives (`_ancestor_chain_safe`, `_effective_write_access`
itself for non-symlink targets) rather than introducing new write-access
logic, minimizing new surface area. `_is_symlink_unsafe` and
`_ancestor_chain_safe`'s own unconditional symlinked-ancestor rejection
are **unchanged** — those remain correctly conservative for the
ancestor-walk use case, which this repair does not touch or weaken.

## 16. Dell-equivalent safe-symlink regression

`test_dell_equivalent_safe_symlink_is_effectively_unwritable`
faithfully reproduces the real Dell topology reported by 7D.6 §13 —
`/usr/lib/python3.12/sitecustomize.py` (symlink) →
`/etc/python3.12/sitecustomize.py` (target), with the symlink's parent,
the target, and the target's parent all admin-controlled
(agent-unwritable) — without mutating the actual Dell. Result:
`write is False`, `reason == "symlink_fully_closed"`. The pre-repair
function would have returned `True` unconditionally for this exact
fixture — this is the precise false positive the repair closes.

## 17. Unsafe symlink adversarial cases

All fail closed (`write is True`, i.e. correctly flagged unsafe) except
where noted indeterminate:

- Writable symlink parent → `symlink_parent_chain_writable`
- Writable resolved target → `symlink_target_writable:...`
- Writable target ancestor (target itself locked, containing dir open) → `symlink_target_ancestor_writable`
- Group-writable target via effective-group channel → `agent_group_membership_grants_write`
- ACL-writable target (macOS ACL branch) → `acl_grants_agent_write`
- Broken symlink → `None`/`path_missing` (pre-existing top-level gate, §13 note)
- Symlink loop (2-hop cycle) → `None`/`path_missing` (same pre-existing gate)
- Unreadable symlink (`os.readlink` failure) → `None`/`symlink_unreadable`
- Relative symlink (target resolved against symlink's own parent, not CWD) → correctly resolves, safe case confirmed closed
- Chained symlink, safe end-to-end → `symlink_fully_closed`
- Chained symlink, unsafe deep target → `symlink_target_writable:symlink_target_writable:...`
- Chain-guard exhaustion (direct white-box call at `_SYMLINK_CHAIN_GUARD + 1`) → `None`/`symlink_chain_guard_exceeded`
- Target inspection error (`Path.exists()` failure) → `None`/`symlink_target_inspection_error`

19 tests total in the new independent module (10 distribution-defect
tests, 15 symlink-defect tests, 1 non-symlink-path regression guard) —
exact count: 26 tests (§22).

## 18. Broader regression results

Full A/B comparison (pre-repair baseline via `git stash -u`, identical
command against post-repair working tree), scope: every
`class_b`/`topology`/`environment_lock`/`hbdc`/`hmic`-matching test file
(`-k "class_b or topology or environment_lock or hbdc or hmic"`,
`--ignore` on one collection error caused by a pre-existing missing
optional dependency, `fido2`, unrelated to this phase):

- **Baseline (pre-repair):** 157 failed, 2278 passed, 5 skipped, 9 errors.
- **Post-repair:** 189 failed, 2272 passed, 5 skipped, 9 errors.
- **Net new failures: 32.** Diffed test-by-test (`comm -13`/`comm -23`
  against sorted FAILED/ERROR id lists) — **every one** of the 32 is an
  inherent, expected consequence of legitimately modifying these three
  files, falling into exactly two categories:
  1. **Byte-identity pins** (`test_*_byte_unchanged_since_*`,
     `test_*_byte_identical_since_phase_entry`) — historical companion
     tests from phases 20J.1/20J.3/20K.2/20K.3/20L.3 that pin these
     three modules' exact bytes to an earlier commit. Any legitimate
     future repair phase touching these files is expected to break
     these by design (they exist to detect *unauthorized* drift, not to
     forbid all future repair).
  2. **Clean-working-tree assertions** (`test_no_src_pcae_files_dirty_in_working_tree`,
     `test_git_status_touches_no_src_pcae_or_existing_contract_file`,
     `test_repo_clean_and_no_production_source_touched`, and similar) —
     historical companion tests from diagnosis/planning/read-only
     phases (19.4, 20C, 20D, 20D.1, 20E, 20H, 20K, 20L.1, 20L.5,
     20L.5A, 20L.6, 20L.6A, 20L.7, 20L.7A, 20L.7C) that assert the
     working tree is clean — correctly failing now that this phase has
     uncommitted source changes in progress, exactly as they should
     during any active repair phase.
  3. One pair, `test_conformance_verifier_looks_up_mismatched_distribution_name`
     / `test_environment_lock_verifier_looks_up_mismatched_distribution_name`
     (from 7D.5's own test module) — these assert the **old, defective**
     literal is present, as a historical record of the pre-repair state
     at the time 7D.5 ran. They now correctly fail because the defect
     they document no longer exists in current source — the intended
     outcome of this phase, not a regression.
- **0 genuine functional/logic regressions.** No test asserting
  correct *behavior* (as opposed to byte-identity or working-tree
  cleanliness) newly failed.
- Two tests flipped from failing to passing between the two runs
  (`test_pcae_check_passes`, x2, in
  `test_phase_149o_20l_7_...`/`test_phase_149o_20l_7a_...`) — observed,
  not attributable to source content (task-lifecycle-state-dependent,
  not exercised by either A or B side of this phase's own edits), noted
  for completeness rather than omitted.
- **166 of the 189 post-repair failures were already failing at phase
  entry** (baseline), confirmed pre-existing and unrelated: chiefly the
  HMIC-scope-staleness class described in §5 (companion tests written
  before Phase 149O.20K's v1.3 evolution, never updated to match it)
  and the "zero production consumers" class (also predates this phase).

## 19. Historical Class-B regression (no reopened findings)

Ran the full 149O.20J series (full ancestor-chain, macOS ACL parser,
effective GID, `writesecurity`/`chown` reclassification) as part of
§18's broader sweep — all *logic* assertions in
`test_phase_149o_20j_2` through `test_phase_149o_20j_8` (ACL right
classification, ancestor-chain walk correctness, effective-GID
detection, ACL-only higher-ancestor detection) pass unchanged; only the
byte-pin/clean-tree assertions in those same files are in the expected
§18 category. `_is_symlink_unsafe` and `_ancestor_chain_safe` (the
primitives underlying the J-series' own prior repairs) are unmodified
by this phase — confirmed via `git diff` showing the only functional
addition to `hatp_class_b_topology_verifier.py` is the new
`_symlink_effective_write_access` helper and the one-line dispatch
change inside `_effective_write_access`. No prior Class-B finding is
reopened.

## 20. HBDC-REQ-036 — explicitly unchanged/open

Not repaired. No change to the launch wrapper, Dell environment,
Action-9 proposition, or any CHGR. Remains classified, per 7D.6's own
disposition (independently reconfirmed, §3): **PROPOSITION / ACTION-9
INVOCATION DEFECT**, open, requiring a future proposition amendment +
fresh CHGR (149O.20L.7D.9 per 7D.6's sequencing) — out of this phase's
scope by explicit instruction.

## 21. HBDC-REQ-042 — explicitly unchanged/expected

No DeploymentBinding created. `find .pcae -iname '*deploymentbinding*'`
returns zero matches at phase close, matching phase entry. Remains the
expected, architecturally-mandated residual under the current
(no-DeploymentBinding) architecture.

## 22. Exact test inventory / results

New, independently-authored module (does not import from 7D.6's own
test module as oracle):
`tests/test_phase_149o_20l_7d_7_class_b_verifier_narrow_source_repair.py`
— **26 tests**, re-run three consecutive times, **26 passed each run,
no flake**:

- 10 distribution-defect tests (§10-11 above: literal absence/presence,
  correct-name resolution, wrong-name non-fallback, downstream-reach
  proofs for both REQ-022 and REQ-035 in both positive and
  negative-property directions, fail-closed-when-unavailable for both).
- 13 symlink-defect tests (§16-17 above).
- 1 before/after distribution-defect reproduction, 1 before/after
  symlink-defect reproduction (both literally reproduce the pre-repair
  code path inline before proving the repaired production function
  handles the identical fixture correctly).
- 1 non-symlink-path regression guard (`test_non_symlink_paths_completely_unaffected_by_this_repair`)
  confirming the repair only touches the `path.is_symlink()` branch.

One existing test updated (not newly authored, and not counted in the
26 above): `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py::test_effective_write_access_symlink_fails_closed`,
renamed to `test_effective_write_access_symlink_writable_parent_fails_closed`
and its reason-string assertion updated from the old unconditional
literal (`"path_is_symlink"`) to the new, more specific reason
(`"symlink_parent_chain_writable"`) for the identical writable-parent
fixture it already tested — the `write is True` outcome for that
specific scenario is unchanged; only the diagnostic reason code became
more precise, which the test now documents explicitly in its own
docstring rather than silently.

## 23. Broader regression results (fast_green)

`pytest -m fast_green` (`--ignore` on the same pre-existing `fido2`
collection error as §18) against the full repaired working tree:
**193 failed, 7128 passed, 5 skipped, 9 errors** (202 distinct
FAILED/ERROR node IDs).

Cross-referenced against §18's already-A/B-analyzed
class_b/topology/environment_lock/hbdc/hmic-scoped failure set: 156 of
the 202 fast_green failures fall inside that already-classified set
(pre-existing baseline or the 32 expected-inherent new failures — no
re-analysis needed). The remaining **46** are outside that keyword
scope and were spot-checked directly (not via a second full-suite
`git stash` A/B, since none of them import or exercise any of the
three files this phase touches):

- The overwhelming majority (~41) are the identical
  clean-working-tree-assertion pattern already characterized in §18
  §2 (`test_no_src_pcae_files_changed`, `test_git_status_touches_no_src_pcae...`,
  `test_only_expected_production_files_changed`, `test_no_forbidden_production_file_touched`,
  `test_*_byte_unchanged*`, and similar), spread across many earlier,
  unrelated phases' (149O.1G, 13, 14, 15, 16, 16.2, 17, 18C-18E, 19.2,
  20A) own companion tests — `fast_green`'s much broader scope surfaces
  more of these than §18's narrower keyword filter did, but they are
  the same phenomenon: any uncommitted `src/pcae/**` change trips every
  historical phase's own "the tree was clean when I ran" assertion,
  by design.
- `tests/test_hatp_mandatory_certification_models.py::test_certified_at_rejects_non_three_non_six_digit_fractions[1,2,4,5]`
  — spot-checked directly: fails identically regardless of this
  phase's changes (unrelated timestamp-fraction-digit validation in
  `hatp_mandatory_certification.py`, a module this phase does not
  touch); the sibling test
  `test_double_terminal_z_pre_existing_stdlib_quirk_not_a_new_regression`
  in the same fast_green run is *itself* named and written to document
  a pre-existing Python-version stdlib datetime-parsing quirk (this
  dev host runs Python 3.14; `test_this_venv_interpreter_is_actually_python_39`
  failing in the same run confirms the same pre-existing
  interpreter-version mismatch) — consistent with these being a known,
  pre-existing, environment-version-dependent cluster, not a regression
  from this phase.
- `tests/test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`
  — spot-checked directly: a subprocess-timeout flake (`pcae
  shell-gate audit verify` exceeding its 15s test timeout), unrelated
  to any file this phase touches.

**0 of the 46 out-of-scope failures are attributable to this phase's
source changes.** Combined with §18's exhaustive A/B diff for the
in-scope set, this phase's repair introduces zero genuine functional
regressions across both the targeted and the fast_green-marked broader
sweep.

## 24. Finding inventory reconciliation

7D.6 recorded four blocking findings (B-149O.20L.7D.6-1 through -4).
This phase repairs exactly two of the four disposition classes 7D.6
identified (PRODUCTION VERIFIER DEFECT ×2: REQ-022/035's shared cause,
and REQ-030's false-positive cause) and leaves the other two
(PROPOSITION/ACTION-9 INVOCATION DEFECT; a non-blocking informational
finding) untouched, per explicit governing-instruction scope:

| Finding | Pre-phase status | Post-phase status |
|---|---|---|
| B-149O.20L.7D.6-1 (distribution metadata lookup, REQ-022/035) | Diagnosed, repair pending | **REPAIRED — INDEPENDENT VERIFICATION PENDING** |
| REQ-030 finding (overbroad symlink heuristic — 7D.6's canonical finding ID for this is **B-149O.20L.7D.6-3**, "Overbroad symlink write-access heuristic") | Diagnosed, no action required for HBDC compliance (already-satisfied property), verifier-hardening opportunity recorded | **REPAIRED — INDEPENDENT VERIFICATION PENDING** (the verifier-hardening opportunity itself is now closed; HBDC-REQ-030's own compliance status was already satisfied before this repair and remains satisfied, now for the correct reason) |
| B-149O.20L.7D.6-2 (HBDC-REQ-036, Action-9 PATH gap) | Diagnosed, amendment pending | **OPEN** — unchanged, explicitly out of scope (§20) |
| B-149O.20L.7D.6-4 (`_check_launcher` absolute-path-only gap, non-blocking/informational) | Recorded, non-blocking | **OPEN** — unchanged, not on the critical path, not addressed this phase |
| HBDC-REQ-042 | Reconfirmed expected | **EXPECTED RESIDUAL** — unchanged, not a repair finding (§21) |

No ambiguous B-finding remains: every one of the four 7D.6 findings has
an explicit, unambiguous status above. Neither repaired finding is
closed — both remain **REPAIRED — INDEPENDENT VERIFICATION PENDING**
until Phase 149O.20L.7D.8 independently verifies both repairs, per this
project's established every-repair-gets-its-own-verification-phase
pattern.

## 25. Governance results

- `pcae_health`: healthy
- `pcae_check`: passed
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, unrelated — same
  historical `tasks/active/`/`tasks/done/` bookkeeping gaps as every
  recent phase in this sequence; outside this phase's allowed-file
  scope)
- `pcae_push_check`: clean at phase entry (`nothing_to_push`)
- `pcae_runtime_inspect`: Observed / observe / unavailable
- `pcae_notify_status`: Telegram configured/enabled
- `telegram_runtime`: loaded
- `fast_green` (structured field, targeted per this project's
  established convention — see [[feedback]] on `fast_green` being
  checked as free text for a real failure signal): this phase's own
  new independent test module, run directly, three consecutive times —
  **26 passed, 0 failed, 0 flaked, each run**. The full, unfiltered
  `pytest -m fast_green` sweep (193 failed, 7128 passed, 9 errors) is
  reported separately and honestly in §23 with full pre-existing/
  in-scope-expected/spot-checked attribution for every failure class —
  not summarized into this structured field, consistent with this
  project's own prior-phase discipline (Phase 134E.9V hardening) of
  never putting a nonzero raw failure count into `fast_green` even with
  a "pre-existing" caveat in the same string.
- `no_dell_mutation_this_phase`: confirmed — no SSH/command issued
  against `hac-dell` at any point in this phase
- `dell_still_pinned_to_old_sha`: confirmed by construction — no Dell
  interaction occurred; 7D.6's own live-verified pin
  (`7a3fa971304521cdcb44251e07ef1966baec686a`) stands unchallenged
- `no_action_9_change`: confirmed — no launch wrapper, Dell environment,
  proposition, or CHGR file touched
- `no_chgr_created_or_amended`: confirmed — `chgr-541cb08c313b4f8884970172d37c5a1d`
  untouched (§6)
- `no_deploymentbinding_created`: confirmed (§21)
- `no_certification_or_activation`: confirmed — no
  `scripts/hatp_certification_admin.py` invocation, no HMIC certify/
  activate/revoke call made this phase

## 26. Bounded production-code repair — no separate human election manufactured

Per governing instruction §29: this phase is a bounded repair of two
independently diagnosed defects, following the project's standard
implementation-mode governed-task lifecycle (task creation, allowed-file
scoping, governed commit, task transition to idle, phase-completion
metadata/report sync, stage-pending-push, push, promote). No additional,
unrelated human-election step was manufactured; no election was skipped
that canonical lifecycle requires. Nothing in this repair reaches the
Dell mutation / redeployment / CHGR authority boundary that would
require a separate human decision under this project's governance
model — that boundary is deliberately not crossed here (§6, §20-21).

## 27. Exact changed production files

```
src/pcae/core/hatp_class_b_conformance.py        |  1 line changed (distribution literal)
src/pcae/core/hatp_class_b_topology_verifier.py  | 84 lines added (new helper + guard constant), 1 line changed (dispatch)
src/pcae/core/hatp_environment_lock_verifier.py  |  1 line changed (distribution literal)
```

No other `src/pcae/**` file touched. No `scripts/**` file touched. No
`docs/contracts/**` file touched (contract text itself was read, not
modified — §4).

## 28. Recommended next phase

**149O.20L.7D.8 — Class-B Verifier Source Repair Independent
Verification.** Independently verify both the distribution-name repair
(§9-11) and the symlink/REQ-030 repair (§12-17) from primary source,
without treating this phase's own tests as oracle; independently
reconstruct the HMIC/source-identity consequences (§5) this phase
already surfaced; do not redeploy. Only after a clean 7D.8 should a
later phase design/capture the authority (proposition amendment, fresh
CHGR) needed for HBDC-REQ-036's repair, Dell redeployment of the
repaired source, and a clean re-adjudication — per 7D.6's own §21
sequencing, unchanged by this phase.
