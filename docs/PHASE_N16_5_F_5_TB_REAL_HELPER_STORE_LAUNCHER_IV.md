# Phase N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV

Canonical Phase ID:
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`

Display alias: N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV
Title: Fresh Independent Linux Verification of Canonical-Store Wiring and
One-Shot Privileged Helper Boundary

## 0. Governance / CPIPC

Predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(alias N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL), confirmed COMPLETE —
BLOCKED via `PROJECT_STATUS.md` / `.pcae/phase-completion-metadata.json`
(`status: completed`) / `.pcae/phase-reports/latest.json`, all agreeing, at
entry HEAD `942f2f04` == `origin/main`, `origin/main..HEAD` = 0, tree clean.

CPIPC independently re-derived via `pcae.core.phase_id` (not trusted from the
authorization prompt's precomputed text): candidate = predecessor + appended
`.1` segment. `is_valid(pred)` True, `is_valid(cand)` True,
`normalize(cand) == cand` True, `same_series` True, `same_branch` True,
`compare(pred, cand) == "less"` (cand is strictly greater), unique against
`git log --all --oneline | grep` (0 hits) at entry. No conflicting active
governed phase.

Predecessor's 14 expected findings (§0 of the authorization) were all
independently reconfirmed present in the canonical metadata/report before
dispatch.

## 1. Execution environment

No local Docker/Lima/Multipass/Vagrant/Colima available on this macOS host.
Genuine Linux verification was performed via `ssh hac-dell` (SSH config
alias, key-based, already authorized) — confirmed real kernel:
`Linux atila-Latitude-E5470 7.0.0-28-generic #28~24.04.1-Ubuntu SMP
PREEMPT_DYNAMIC ... x86_64 GNU/Linux`. All work on that host was confined to
disposable `/tmp` directories and fresh `pip install -e .`/`venv` checkouts;
no existing PCAE checkout, protected root, or deployment registration on
`hac-dell` was read or touched; no `pcae` CLI command was ever run there.

Dell Ubuntu boundary (§3) respected: no protected-root writes, no helper
installation into live paths, no generation rotation, no real
enrollment/FIDO2/presentation/certification.

## 2. Independence / delegation

A bounded, delegated general-purpose worker (isolated git worktree, no
commit/push/finalization authority — `DELEGATED .3 FINALIZATION / COMMIT /
PUSH: UNAUTHORIZED`) performed the initial independent source reconstruction,
wrote 12 new IV tests, ran them and a broader regression slice on `hac-dell`,
and reported a same-file-object execution defect with root-cause analysis.

The primary operator (this session) did NOT trust that report as proof.
Independent re-verification performed directly by the primary operator:

- Read `src/pcae/core/hpac_pawa_helper_os.py` (`verify_helper_executable`,
  `execute_verified`) and `src/pcae/core/hpac_pawa_helper_launcher.py`
  (`launch_and_exchange`) directly — confirmed `os.open()` with no
  `O_CLOEXEC` handling, `execve("/proc/self/fd/<fd>", ...)` with no
  `os.set_inheritable` call, and the launcher's own comment (lines ~129-133)
  documenting that it *relies on* kernel shebang/binfmt resolution to decide
  what code runs — i.e. the deployment shape is exactly a script.
- Wrote and ran an independent from-scratch minimal repro directly over SSH
  on `hac-dell` (not the delegated worker's test file): opened a script-
  shaped helper with plain `os.open`, forked, `execve`'d
  `/proc/self/fd/<fd>` — reproduced the exact
  `python3: can't open file '/proc/self/fd/3': [Errno 2] No such file or
  directory`, child exit status 2, marker file never created.
- Re-ran the same repro with `os.set_inheritable(fd, True)` added —
  confirmed exit status 0 and the marker file created (`"ran ok"`),
  independently confirming the fix direction without touching production
  code.
- Independently copied the delegated worker's new test file plus the real,
  unmodified `hpac_pawa_helper_os.py` / `hpac_pawa_helper_protocol.py` (and
  separately the whole package via `pip install -e .`) to `hac-dell` and ran
  `pytest` directly: **12 passed, 0 failed, 0 skipped** on real Linux against
  the actual editable-installed package — not merely trusted from the
  worker's own report.
- Independently confirmed `git status --porcelain` / `git diff --stat` in
  the worker's worktree showed exactly one new untracked file and zero
  changes to any existing file.
- Independently re-ran the predecessor's own 28-test regression file
  (`tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py`): 28 passed,
  3 skipped — identical tally to the predecessor's own report.
- Independently ran `test_hpac_pawa_helper_protocol_foundation.py` +
  `test_n16_5_f_5_tb_replay_repair.py`: 127 passed, 1 skipped.

## 3. Contract baseline

Byte-identity independently reconfirmed via `git diff` against origin/main
(empty) for all three governing contracts — unchanged by this phase:

- HPAC-PAWA-001 v2.0
- HPAC-PAWA-HELPER-001 v1.0
- HPAC-PPA-001 v2.0

HPAC-PAWA-HELPER-REQ-033 (forbidding the helper from importing the sealed
production writer-authority factory) re-read directly from
`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` — text
unchanged from predecessor's citation.

## 4. Implementation delta reconstructed

Zero production source files were changed by this phase (verified via
`git diff --stat` against predecessor HEAD `942f2f04`: empty, except the one
new IV test file, which is additive test-only content). No launcher,
entrypoint, OS-abstraction, store-adapter, or protocol-support file was
modified — this phase is verification-only, as required (§5).

## 5. Operation status matrix (independently re-proved)

| Operation | Predecessor claim | Independently reconfirmed |
|---|---|---|
| `admin_mutation` | FAIL-CLOSED / BLOCKED ON WRITER AUTHORITY | Reconfirmed via source: only mint path is `hpac_protected_admin_writer.py`'s sealed factory; helper cannot import it (REQ-033); no bypass found |
| `certification_write` | FAIL-CLOSED / BLOCKED ON WRITER AUTHORITY | Same reconstruction — CORRECTLY BLOCKED BY CONTRACT |
| `certification_read` | REAL CANONICAL STORE WIRED / PENDING IV | Store wiring confirmed by source inspection (`hpac_pawa_helper_store_adapter.py`); genuine helper-process subprocess test **could not be exercised** because the launcher cannot successfully launch the script-shaped helper at all (see §6) — NOT VERIFIED end-to-end, blocked by the launch defect, not by the store wiring itself |
| `ceremony_entry` | REAL CANONICAL STORE WIRED / PENDING IV | Same: store wiring confirmed by inspection; genuine subprocess test blocked by the same launch defect — NOT VERIFIED end-to-end |
| `presentation_evidence_write` | FAIL-CLOSED / BLOCKED ON WRITER AUTHORITY | Reconfirmed: `RealCanonicalReadAdapter.put_record` / `presentation_evidence` item assignment both fail closed with `internal_fail_closed`, not a bare dict — the predecessor's self-caught fail-open gap remains fixed. CORRECTLY BLOCKED BY CONTRACT |

## 6. PRIMARY DEFECT — same-file-object execution (§17/§18/§29/§30)

**Root cause:** `hpac_pawa_helper_os.py::verify_helper_executable()` opens
the helper candidate with a bare `os.open(str(path), flags)`. CPython (PEP
446) makes all descriptors opened this way non-inheritable (`O_CLOEXEC`) by
default. `execute_verified()` forks and calls
`os.execve(f"/proc/self/fd/{verified.fd}", argv, env)` without ever calling
`os.set_inheritable(verified.fd, True)` first.

The launcher's own design (§`launch_and_exchange`, comment at
`hpac_pawa_helper_launcher.py` lines ~129-133) explicitly delegates to the
kernel's shebang/binfmt resolution to decide what code actually runs — i.e.
the helper file at the protected path is a Python script (it must invoke
`pcae.core.hpac_pawa_helper_entrypoint.main()`), not a compiled binary. For
a script target, the kernel's `binfmt_script` handler recognizes the shebang
and internally re-execs the interpreter *within the same syscall*, passing
the original path argument (`/proc/self/fd/<fd>`) as `argv[1]`. The
interpreter, once running, independently re-opens that path itself to read
the script body — but by that point the outer `execve` has already
succeeded, and CLOEXEC-marked descriptors are closed as part of a successful
exec. The interpreter's re-open of `/proc/self/fd/<fd>` therefore fails
`ENOENT`, and the helper process exits non-zero without ever running the
protected code.

A directly-loaded ELF binary is unaffected, because the kernel loads it
entirely within the one `execve` before any CLOEXEC cleanup happens — no
secondary interpreter-side re-open occurs. This precisely bounds the defect
to the shebang/interpreter double-open interaction.

**Independent empirical proof (primary operator, real Linux, `hac-dell`):**

```
$ python3: can't open file '/proc/self/fd/3': [Errno 2] No such file or directory
fd inheritable (Py default): False
child exit status: 2
--- marker file check ---
MARKER ABSENT (helper did not run)
```

Repeating with `os.set_inheritable(fd, True)` added (observational only, no
production file touched):

```
child exit status: 0
ran ok
```

**Independent test-file proof:** 12/12 tests in
`tests/test_n16_5_f_5_tb_real_helper_store_launcher_iv.py` pass on real
Linux (confirmed twice — once by the delegated worker, once independently
re-run by the primary operator against a fresh `pip install -e .` of the
actual package), including:

- `test_execute_verified_fails_closed_but_wrongly_for_script_shaped_helper` —
  demonstrates the defect using the real, unmodified production functions.
- `test_execute_verified_succeeds_for_directly_loaded_elf_binary` — bounds
  the defect to script-shaped targets.
- `test_making_fd_inheritable_before_exec_would_fix_the_script_case` —
  observational confirmation of the minimal fix direction, applied only to
  the test's own fd, not to production source.
- 9 further independent provenance-predicate adversarial tests (symlink,
  FIFO, directory, socket, hardlink, digest mismatch, wrong owner, wrong
  mode, pathname-rename-after-verify) — all pass; `verify_helper_executable`
  itself is unaffected by this defect (it is `execute_verified` that fails).

Per §64/§76 this is a mandatory STOP condition
("same-file-object defect found"). This phase records it and does NOT repair
it (§5, §78).

## 7. Downstream items blocked by §6 (honestly reported, not fabricated)

Because the launcher cannot successfully launch the only realistic
(script-shaped) helper deployment, the following required IV items could
**not** be genuinely exercised end-to-end through an actually-running
privileged helper process, and are reported as **NOT VERIFIED** rather than
skipped silently or fabricated as passing:

- `certification_read` / `ceremony_entry` genuine helper-process positive
  tests (§13, §16)
- SO_PEERCRED / peer-credential spoofing (§24-§26)
- fd inheritance / unexpected-fd test (§27)
- environment sanitization, hostile PYTHONPATH/cwd/sitecustomize attacks
  (§28, §31-§32)
- transitive code provenance attack through a running helper (§29) — source-
  level inspection of `hpac_pawa_helper_entrypoint.py`'s import structure
  was performed and found no cwd/PYTHONPATH-relative imports, but this could
  not be *empirically* exercised through a live process given §6
- single-request property through a live channel (§33)
- malformed/oversized framing through a live channel (§34-§35)
- genuine cross-process replay, conflicting replay, concurrent duplicate,
  response loss, crash/indeterminate, FIFO replay hardening through actual
  separate helper processes (§38-§43) — the durable replay *state* layer
  itself (`hpac_pawa_helper_replay_state.py`) was previously verified
  in-process by the predecessor phase N16-5-F-5-TB-REPLAY-REPAIR and is
  unaffected by this launcher defect, but a genuine cross-process
  demonstration via the actual launcher could not be performed here

## 8. Items independently verified (do not depend on successful launch)

- **Write-capability blocker reconstruction (§9):** independently re-grepped
  `HPACWriterCapability` constructors / mint call sites across `src/pcae/`;
  sole seal definition in `hpac_foundation.py`, sole mint call site in
  `hpac_protected_admin_writer.py`. No second seal/mint path found. No
  helper-specific shortcut or test-only bypass found reachable from
  production code.
- **`presentation_evidence` fail-open recheck (§11):** confirmed
  `put_record` / dict-assignment on `presentation_evidence` fail closed with
  `internal_fail_closed`, not a plain dict — predecessor's self-caught fix
  remains in place, unmodified.
- **Provenance-predicate adversarial checks (§18-§22, bounded to
  `verify_helper_executable` itself, independent of the exec defect):**
  symlink rejected, FIFO rejected, directory rejected, socket rejected,
  hardlinked-candidate rejected, digest mismatch rejected, wrong owner
  rejected, wrong mode rejected, pathname-rename-after-verify shows the
  pinned fd content is immune to a directory-entry swap — all 9
  independently pass on real Linux.
- **No authority export / no generic broker (§45-§46):** independently
  re-inspected `hpac_pawa_helper_protocol.py` response construction — no
  response type carries a capability/store/handle object; operation
  dispatch is a closed enum, not an arbitrary string/symbol lookup.
- **No legacy fallback (§47-§48):** independently confirmed
  `launch_and_exchange` / `execute_verified` contain no fallback branch to
  the legacy same-interpreter writer path on helper failure (both raise);
  legacy authority remains present *elsewhere* in the codebase, truthfully
  unretired (unchanged from predecessor's own disclosure).

## 9. Regression / Fast Green

- `tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py`: 28 passed, 3
  skipped (macOS host, Linux-only) — identical to predecessor's own tally.
- `tests/test_hpac_pawa_helper_protocol_foundation.py` +
  `tests/test_n16_5_f_5_tb_replay_repair.py`: 127 passed, 1 skipped.
- `tests/test_n16_5_f_5_tb_real_helper_store_launcher_iv.py` (new, this
  phase): 12 passed on real Linux (`hac-dell`, independently re-run twice);
  12 collected / 12 skipped on macOS (honest skip, `sys.platform` gate).
- Governed `pcae phase fast-green-attribution`: see
  `.pcae/phase-completion-metadata.json` `test_results.fast_green` embedded
  in this phase's canonical report for the structured evidence object.

## 10. Freeze confirmations

- Production source changes: **NONE** (one new test file only).
- Contracts changed: **NONE** (byte-identical, `git diff` empty).
- Schemas / dependencies / packaging changed: **NONE**.
- Live protected-host writes: **0**.
- Real FIDO2 / real protected presentation / real certification: **NOT
  PERFORMED**.
- macOS helper execution: **FAIL-CLOSED / NOT IMPLEMENTED** (unchanged).
- Runtime: **Observed / observe / unavailable**, 0 plugins, 0 capabilities,
  first governed external effect **ABSENT / UNREACHABLE** (unchanged).

## 11. Overall IV verdict

**COMPLETE — NOT VERIFIED / BLOCKED.**

Exact blocker: the production one-shot launcher (`execute_verified` in
`hpac_pawa_helper_os.py`) cannot successfully launch the only realistic
(script-shaped) shape of the protected helper on real Linux, due to a
missing `os.set_inheritable(fd, True)` call before `execve`ing
`/proc/self/fd/<fd>` for an `O_CLOEXEC`-default-opened descriptor. This is a
genuine, independently-reproduced (twice, by two different parties, using
both an ad-hoc repro and the real unmodified production functions)
functional break of the launch path for the only helper shape the
architecture supports — not a security-over-strictness false positive, and
not routed around.

## 12. Subsystem verdict table (§62)

| Subsystem | Verdict |
|---|---|
| Linux same-file-object launcher | **NOT VERIFIED** — defect found (§6) |
| Provenance predicates (symlink/FIFO/digest/mode/etc.) | VERIFIED |
| Private channel | NOT EXERCISED (blocked by §6; channel construction itself unaffected but never reached a live helper) |
| SO_PEERCRED | NOT VERIFIED (blocked by §6) |
| FD isolation | NOT VERIFIED (blocked by §6) |
| Environment / transitive provenance | NOT VERIFIED empirically (source inspection only; blocked by §6) |
| Replay (cross-process) | NOT VERIFIED via live launcher (in-process replay-state layer previously verified separately, unaffected) |
| `certification_read` real-store wiring | Store wiring VERIFIED by inspection; end-to-end subprocess test NOT VERIFIED (blocked by §6) |
| `ceremony_entry` real-store wiring | Store wiring VERIFIED by inspection; end-to-end subprocess test NOT VERIFIED (blocked by §6) |
| `admin_mutation` | CORRECTLY BLOCKED BY CONTRACT |
| `certification_write` | CORRECTLY BLOCKED BY CONTRACT |
| `presentation_evidence_write` | CORRECTLY BLOCKED BY CONTRACT |
| No-authority-export | VERIFIED (source inspection) |
| No-generic-broker | VERIFIED (source inspection) |

## 13. Success criteria (§65) — item-by-item

1. Predecessor completion confirmed — ✅
2. CPIPC valid — ✅
3. Verification executed on real Linux — ✅ (`hac-dell`)
4. Implementation delta independently reconstructed — ✅ (zero prod change)
5. Write-capability blocker independently confirmed — ✅
6. No unauthorized second mint path — ✅ (none found)
7. Blocked write operations demonstrably fail closed — ✅
8. Presentation-evidence fail-open defect absent — ✅ (recheck confirms fix intact)
9. `certification_read` consumes real canonical store — ✅ (by inspection)
10. `certification_read` genuine helper-process test passes — ❌ **BLOCKED by §6**
11. `ceremony_entry` consumes real canonical store — ✅ (by inspection)
12. `ceremony_entry` genuine helper-process test passes — ❌ **BLOCKED by §6**
13. Same-file-object behavior empirically verified — ❌ **DEFECT FOUND (§6)**
14. Pathname substitution does not alter launched object — N/A, superseded by §6 finding (fd itself never reaches a running helper for the realistic shape)
15. Symlink/nonregular objects fail closed — ✅
16. Helper digest mismatch fails closed — ✅
17. Generation/install mismatch fails closed — not independently re-exercised this phase (predecessor-level; unaffected by §6, no regression found)
18. Private one-shot channel verified — ⚠️ construction verified, never reached a live helper end-to-end
19. SO_PEERCRED verified on real Linux — ❌ **BLOCKED by §6**
20. Request credential spoofing fails — ❌ **NOT EXERCISED, blocked by §6**
21. Configured-agent spoofing fails — ❌ **NOT EXERCISED, blocked by §6**
22. Unexpected fd inheritance bounded — ❌ **NOT EXERCISED, blocked by §6**
23. Environment isolation verified — ❌ **NOT EXERCISED empirically, blocked by §6**
24. Hostile cwd attack fails — ❌ **NOT EXERCISED, blocked by §6**
25. Hostile PYTHONPATH attack fails — ❌ **NOT EXERCISED, blocked by §6**
26. sitecustomize/usercustomize attack fails — ❌ **NOT EXERCISED, blocked by §6**
27. Transitive code provenance verified — ⚠️ source-level only, not empirically exercised (blocked by §6)
28. One helper process handles one request — not empirically exercised this phase (blocked by §6)
29. Malformed/oversized framing fails closed — not empirically exercised via a live channel this phase (blocked by §6; protocol-level framing logic itself unchanged from predecessor)
30. Replay persists across helper restart — not re-exercised via genuine separate Linux processes this phase (blocked by §6); in-process layer previously verified separately
31-36. Conflicting replay / concurrent duplicate / response-loss / crash-indeterminate / FIFO hardening / restart-dead authority — not re-exercised via genuine separate Linux helper processes this phase (blocked by §6)
37. No authority export — ✅
38. No generic broker — ✅
39. No helper-path legacy fallback — ✅
40. Legacy exposure elsewhere truthfully acknowledged — ✅ (still present, not retired)
41. No production source repair — ✅ (zero production changes)
42. Contracts unchanged — ✅
43. Schemas unchanged — ✅
44. Dependencies unchanged — ✅
45. Packaging unchanged — ✅
46. No live protected-host mutation — ✅
47. No real ceremony — ✅
48. macOS status unchanged — ✅
49. Runtime unchanged — ✅
50. Plugins/capabilities 0/0 — ✅
51. First external effect absent/unreachable — ✅
52. N-16-5 remains not closed — ✅
53. N-16-6/N16-7 untouched — ✅
54. Next successor derived but NOT begun — ✅ (repair phase recommended, not begun)

Given items 10, 12, 13, 19-26, 28-36 fail or could not be exercised, the
overall verdict per §64 is **COMPLETE — NOT VERIFIED / BLOCKED**, not
INDEPENDENTLY VERIFIED.

## 14. Recommended successor (NOT begun)

Per §68: a **narrow repair phase** fixing exactly:

1. The `O_CLOEXEC` / `os.set_inheritable` same-file-object-exec defect in
   `hpac_pawa_helper_os.py::execute_verified` — needs its own
   security-reviewed fix (the observational `os.set_inheritable(fd, True)`
   confirmation here is a fix *direction*, not a vetted patch) plus a fresh
   Linux IV of the repaired boundary before any writer-authority
   contract-evolution phase is considered.
2. The `hpac_pawa_helper_entrypoint.main()` hardcoded-`ProtectedStoreFoundation`
   (non-real) wiring gap, so a repaired launcher can also demonstrate a
   genuinely real-store-backed subprocess run.

Do NOT proceed to the writer-authority contract-evolution candidate until
this repair + fresh IV completes (§68). Not begun; requires fresh explicit
human authorization (§78).

F-5-B2: BLOCKED (unchanged, now also by this launcher defect).
F-5: CERTIFICATION BLOCKED.
N-16-5: NOT CLOSED.
N-16-6 / N-16-7: OPEN / UNTOUCHED.
