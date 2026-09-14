# Evidence Report — N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR-IV

**Author:** bounded delegated worker (no finalization authority — did not commit, push, or run
`pcae phase complete`/`pcae commit`/`pcae push`; no `src/pcae/**`, contract, or packaging file was
modified).

**Status of this document:** this worker's own independent-verification assessment, produced for
the primary operator to independently re-verify. It is evidence, not a finalization act.

**Repair commit under verification:** `43813b16832b2b5d3940163a8879f6808f8315f4` — "repair
same-file-object exec fd inheritance and real-store entrypoint wiring" (verified via
`git log --follow -- src/pcae/core/hpac_pawa_helper_os.py`; the phrase
"N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR" does not appear literally in any commit *subject* —
it appears in the commit *body* and in file/doc names — so a plain `git log --oneline | grep`
on the phrase alone finds nothing; `--follow` on the source file is what locates it).

**Predecessor lineage reconciliation:** already independently settled by
N16-5-F-5-TB-CPIPC-IDENTITY-RECONCILE (`fa9b342c`) as Disposition A (no lineage defect). This
report does not revisit that question.

**Host used for every Linux-dependent test:** `ssh hac-dell` — confirmed reachable,
`Linux atila-Latitude-E5470 7.0.0-28-generic #28~24.04.1-Ubuntu SMP ... x86_64`, Python 3.12.3.
All work performed under `/tmp/n16-5-tb-iv-work/` on that host (disposable venv + an rsync'd,
`.git`-free copy of the repo — see the "environment artifacts" note in §7 for the one
consequence of excluding `.git`). No live protected root, no real ceremony/FIDO2/certification,
no sudo mutation outside `/tmp`, was ever touched.

---

## 1. Repair A and Repair B, reconstructed independently from current source

**Repair A** — `src/pcae/core/hpac_pawa_helper_os.py::execute_verified`, lines 177–186:

```python
if sys.platform.startswith("linux"):
    pid = os.fork()
    if pid == 0:  # child
        try:
            os.set_inheritable(verified.fd, True)
            os.execve(f"/proc/self/fd/{verified.fd}", argv, env)
        finally:
            os._exit(127)
    os.close(verified.fd)
    return pid
```

Confirmed: `os.set_inheritable` is called only in the child branch, only on the exact fd that
`verify_helper_executable` (lines 92–132 of the same file) already fully verified (open with
`O_NOFOLLOW`, regular file, `nlink==1`, owner match, mode `0755`, full-byte SHA-256 match), and
only immediately before `execve` against `/proc/self/fd/<fd>` — i.e. the same file *description*,
never a fresh pathname lookup. The parent's own copy of the fd is closed unchanged, still
non-inheritable. This exactly matches the phase-authorization's description of Repair A.

**Repair B** — `src/pcae/core/hpac_pawa_helper_entrypoint.py`:
- `resolve_store_profile()` (lines 166–219) accepts `"real"` **only** when
  `Path(protected_root).absolute() == resolve_hpac_protected_root().absolute()` — a function
  whose own contract "accepts no override input" — and raises (fail-closed) for anything else.
  It takes no request-shaped input at all (`inspect.signature` has no `request` parameter,
  independently re-checked — see §8).
- `build_helper_context()` (lines 222–266): on `STORE_PROFILE_REAL` it constructs
  `RealCanonicalReadAdapter(HPACStoreAuthority.production())` — `production()` takes **no root
  argument**, so nothing caller-controlled can redirect it. `NON_REAL` is reachable **only**
  through the explicit keyword-only `_test_only_store` seam, never from env/argv/request.
- `main()` (lines 269–304): reads bootstrap coordinates from four fixed env vars the launcher
  sets, resolves the store profile, builds the context, and fails closed with distinct nonzero
  exit codes (`EXIT_STORE_PROFILE_UNESTABLISHED=4`, `EXIT_REAL_STORE_UNAVAILABLE=5`) on any
  failure — never degrading to `ProtectedStoreFoundation`.

This exactly matches the phase-authorization's description of Repair B. Both repairs are also
self-documented at length in the module docstrings and in `docs/PHASE_N16_5_F_5_TB_REAL_HELPER_BOUNDARY_REPAIR.md`, which I read and independently corroborated against the actual code rather than trusting.

---

## 2. Genuine shebang-helper end-to-end exec through the unmodified production launcher

`tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py::test_repair_a_script_shaped_helper_executes_through_verified_fd` and the broader `test_repair_b_real_adapter_certification_read_through_a_genuine_helper` / `test_repair_b_real_adapter_ceremony_entry_through_a_genuine_helper` do exactly this: a real `#!/usr/bin/env python3`-shaped script is written to a disposable `tmp_path`, verified via `verify_helper_executable`, exec'd via the unmodified `execute_verified`/`launch_and_exchange` production path, and the response is read back from a genuinely separate OS process (`outcome.helper_pid != os.getpid()`). Rerun on hac-dell (see §17) — **PASS**.

**Verdict: VERIFIED.**

---

## 3. Fd inheritance isolation

`test_repair_a_unrelated_fds_remain_non_inheritable_in_the_child` opens a regular file, a pipe,
and an `AF_UNIX` socket in the parent before launch, execs a helper that dumps
`/proc/self/fd` in the child, and asserts none of the three bystander fds (nor any pipe:/socket:
target) appear in the child — only the verified fd (plus stdio) does. I read this test in full;
it is genuinely adversarial (not tautological — it positively enumerates the child's fd table via
`/proc/self/fd`, not just the fds it expects). Rerun on hac-dell — **PASS**.

**Verdict: VERIFIED.**

---

## 4. Forced exec-failure cleanup

`test_repair_a_forced_exec_failure_exits_127_and_closes_the_parent_fd` — a verified candidate
that is not a real executable image (no shebang, not ELF) makes `execve` fail; the child's
`finally: os._exit(127)` terminates the process image immediately, which the kernel guarantees
closes every fd that process held (including the just-marked-inheritable one) — there is no
window where a long-lived process retains it, because there is no long-lived process: `_exit`
is immediate and unconditional. Rerun on hac-dell — **PASS**.

**Verdict: VERIFIED.**

---

## 5. Path substitution attack

`test_repair_a_pathname_replacement_after_verification_executes_the_original` performs a real
`os.replace()` (atomic directory-entry swap, new inode) over the verified path after
verification, then execs the *already-verified* fd, and asserts the **original** script's
side effect ran and the **hostile** replacement's side effect did not. This is the correct way
to test directory-entry substitution (as opposed to in-place mutation — see §7's finding about
a different, pre-existing test that conflates the two). Rerun on hac-dell — **PASS**.

**Verdict: VERIFIED — anti-TOCTOU against path/directory-entry substitution holds.**

---

## 6. Symlink / FIFO / directory / digest-mismatch / stale-metadata / wrong-generation attacks

All of `test_repair_a_regression_symlink_candidate_rejected`,
`test_repair_a_regression_directory_candidate_rejected`,
`test_repair_a_regression_fifo_candidate_rejected`,
`test_repair_a_regression_socket_candidate_rejected`,
`test_repair_a_regression_digest_mismatch_rejected`,
`test_repair_a_regression_wrong_mode_and_owner_rejected`, plus (in the launcher-impl test file)
generation/stale-metadata rejections and (in the `_iv_r` replay suite) 13 malformed-record
variants + generation/installation-mismatch-as-conflicting — all fail closed via
`HelperProtocolError`/`ReplayStateCorruption` with the expected error codes. I read a sample of
each category to confirm the assertions check the *specific* fail-closed error code, not just
"raises something". Rerun on hac-dell — **PASS** (see §17 for the two environmental
pre-existing-not-caused-by-this-repair exceptions).

**Verdict: VERIFIED.**

---

## 7. Finding C — in-place same-inode content mutation

**Predecessor disclosure (not repaired, by design — a legitimate scope decision):**
`test_repair_a_in_place_content_mutation_after_verification_is_not_executed` already proved, as
the file's own OWNER, that truncating and rewriting the SAME inode after verification (not
swapping the directory entry) **does** change what the already-open fd reads and **does**
execute the hostile bytes — `/proc/self/fd` anchoring defends against directory-entry
substitution, not against a write to the same inode's bytes. This was correctly disclosed as an
out-of-scope finding by the repair commit itself.

**What this worker added (new file `tests/test_n16_5_f_5_tb_real_helper_boundary_repair_iv.py`)**
is the adjudication the predecessor phase left open: *who* can actually reach that write.
`verify_helper_executable`'s conjunctive predicates require mode exactly `0755` (not
group/other-writable) and `st_uid == expected_owner_uid` before a candidate is even accepted.
Under ordinary POSIX permission semantics this should make the in-place write itself — not just
the directory-entry swap — unavailable to any OS principal other than the owning uid (or root).
I tested this empirically, not by reading the mode bits, using a genuine second, unprivileged
Linux principal (`nobody`, uid 65534, via passwordless `sudo -n -u nobody` on hac-dell — no
password/credential material was used or required):

- `test_finding_c_non_owner_cannot_open_verified_inode_for_writing` — `nobody` genuinely attempts
  `os.open(helper_path, os.O_WRONLY)` on the verified, owner-owned, mode-0755 file.
  **Result: `PermissionError` (EACCES) — DENIED.** The file's bytes are provably unchanged
  (`helper.read_bytes() != b"HOSTILE-FROM-NOBODY"`).
- `test_finding_c_owner_can_mutate_but_owner_is_the_maximal_trust_principal` — companion positive
  control reproducing the predecessor's own finding (the owner CAN mutate and the mutation DOES
  execute) and pinning the trust-model argument: `hpac_pawa_helper_os.authenticate_peer` requires
  the connecting peer's kernel-verified uid to equal `deployment_owner_uid` and explicitly rejects
  the configured *agent* principal — i.e. the deployment owner is already the single most-trusted
  principal this boundary's own peer-authentication exists to admit, and the *agent* (the actual
  adversary class in this contract's threat model, per HPAC-PAWA-HELPER-REQ-042) is a strictly
  lower-trust principal that this test shows cannot reach the mutation at all.
- `test_finding_c_channel_socket_directory_denies_a_different_uid` — defence-in-depth control:
  even setting Finding C aside, `nobody` cannot connect to the private one-shot channel socket at
  all (`0700` directory / `0600` socket — confirmed via `stat`, then empirically via a real
  connect attempt from `nobody`, which returns `PermissionError`).

All three ran genuinely on hac-dell — **PASS** (see §17).

**Disposition: C-A — not exploitable under governed deployment invariants.** Same-inode write
requires authority outside the attacker model this contract defends against (an ordinary
configured-agent principal, or any other non-owner uid): proven empirically via ownership
(`st_uid == expected_owner_uid`) and mode (`0755`, non-group/other-writable) rather than merely
asserted. This is my own assessment, not a finalization act — the primary operator should
re-run `tests/test_n16_5_f_5_tb_real_helper_boundary_repair_iv.py` independently before relying
on it. I did **not** attempt to determine whether the deployment owner's own account could ever
be tricked into performing the write (a social-engineering / supply-chain question), which is
out of scope for an OS-mechanism verification and is, in any case, already the same trust level
the whole PAWA architecture is rooted at.

---

## 8. REAL/NON_REAL profile selection — no caller-controlled trust

- `resolve_store_profile` takes only `protected_root: str`; `inspect.signature(resolve_store_profile).parameters` has no `request` parameter (independently re-checked; matches `test_repair_b_profile_decision_is_structurally_unreachable_from_a_request`).
- `HelperRequest.from_mapping` is a closed schema that rejects unknown fields (`CLOSED OPERATIONS`/closed dataclass fields) — a hostile `profile`/`real`/`backend`/`protected_root`/`mode` field in a request payload cannot reach parsing at all; `test_repair_b_hostile_request_fields_rejected_by_the_closed_schema` (parametrized) and `test_repair_b_hostile_operation_params_cannot_reach_store_selection` cover this. I grepped `HelperRequest`'s field list myself (§11 of the protocol module) and confirmed there is no profile/backend-shaped field to begin with.
- `test_repair_b_main_fails_closed_for_a_foreign_protected_root` runs `main()` as a genuine
  subprocess with `PAWA_HELPER_PROTECTED_ROOT` pointed at a disposable, non-canonical root and
  asserts `proc.returncode == EXIT_STORE_PROFILE_UNESTABLISHED` — i.e. direct invocation of the
  entrypoint outside the trusted launcher, even with attacker-chosen bootstrap env vars, cannot
  select `real` for anything but the one fixed canonical root, and there is no fallback.
- `test_repair_b_real_store_construction_failure_never_falls_back` (monkeypatched real-store
  construction to raise) asserts the exception path never substitutes `ProtectedStoreFoundation`.
- `test_repair_b_non_real_reachable_only_through_the_explicit_test_seam` confirms `NON_REAL` is
  unreachable any other way.

All rerun on hac-dell — **PASS**.

**Verdict: VERIFIED.**

---

## 9. `certification_read` / `ceremony_entry` against a real canonical-store adapter

`test_repair_b_real_adapter_certification_read_through_a_genuine_helper` and
`test_repair_b_real_adapter_ceremony_entry_through_a_genuine_helper` launch a genuine separate
process against `RealCanonicalReadAdapter` (over a `_production_test_fixture`-sealed disposable
authority — never the live protected root) and assert the returned payload matches genuine
canonical content (e.g. `payload["contents"]["mechanism_id"] == resolved.descriptor.mechanism_id`
— not an empty/fabricated record). Adversarial cases already present and rerun: missing record
(`test_pawa_anchor_record_is_a_reported_blocker_not_a_silent_fallback`,
`test_ceremony_entry_real_store_wiring_rejects_when_no_installation`), malformed/unknown record
type (`test_unknown_record_type_rejected`), wrong/partial selector
(`_read_trusted_approval_presentation_record`'s `":"`-format check, raising
`target_scope_invalid` on a bare id), stale generation
(`test_ceremony_entry_real_store_wiring_rejects_stale_generation`). Path traversal: the record
key is never treated as a filesystem path anywhere in `hpac_pawa_helper_store_adapter.py` (it is
always passed to a typed `.resolve(key)` on one of the six closed per-record-type stores, never
to `open`/`Path`) — I grepped the module for any `open(`/`Path(` call taking `key` directly and
found none, so a `"../"`-shaped key has no path-traversal meaning here at all; it is simply not
found by the corresponding store's own key lookup. All rerun — **PASS**.

**Verdict: VERIFIED.**

---

## 10. `admin_mutation` / `certification_write` / `presentation_evidence_write` remain fail-closed

`RealCanonicalReadAdapter.put_record` unconditionally raises `_no_writer_capability(record_type)`
for any of the three write operations; `presentation_evidence` is also backed by a
`_WriteBlockedEvidenceMap` whose `__setitem__` raises the same error, so there is no silent
in-memory fake-success path either. `test_repair_b_admin_mutation_still_blocked_under_the_real_profile`, `test_repair_b_certification_write_still_blocked_under_the_real_profile`, `test_repair_b_presentation_evidence_write_still_blocked_under_the_real_profile` exercise this through a genuine launched helper (not just a unit call) and assert the exact `internal_fail_closed` code. Rerun — **PASS**.

This is a pre-existing, disclosed, **architectural** blocker (not a bug this phase can or should
"fix" — doing so would require minting a new `HPACWriterCapability`, which is exactly the
contract-evolution decision the store adapter's own module docstring says is out of scope; per my
CONSTRAINTS I did not attempt it).

**Verdict: VERIFIED (fail-closed, as designed).**

---

## 11. Every `HPACWriterCapability` mint path — helper mints nothing new

`grep -rn "_factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL" src/pcae` finds every real mint call
site exclusively inside `src/pcae/core/hpac_protected_admin_writer.py` (lines 1186, 1205, 1208,
1855, 1858, 2175, 2180, 2183). None of the six helper modules
(`hpac_pawa_helper_os.py`, `hpac_pawa_helper_entrypoint.py`, `hpac_pawa_helper_launcher.py`,
`hpac_pawa_helper_store_adapter.py`, `hpac_pawa_helper_operations.py`,
`hpac_pawa_helper_protocol.py`) import `hpac_protected_admin_writer` or hold the seal object
`_PRODUCTION_WRITER_FACTORY_SEAL` — independently confirmed via grep. This is exactly
**HPAC-PAWA-HELPER-REQ-033** ("forbidding the helper from importing the sealed [factory]"),
found at `src/pcae/core/hpac_pawa_helper_os.py:14` and in
`docs/PHASE_N16_5_F_5_TB_REAL_HELPER_BOUNDARY_REPAIR.md:70/111`. `test_req_033_helper_modules_never_import_the_pawa_factory` (parametrized over all six modules) and `test_req_033_repair_b_imports_only_the_read_adapter_and_authority` both pass on rerun.

**Verdict: VERIFIED — the helper boundary mints no new authority.**

---

## 12. SO_PEERCRED — kernel-verified identity cannot be overridden by request fields

`hpac_pawa_helper_os._peer_credential_linux` reads `SO_PEERCRED` via `getsockopt` directly off
the kernel socket structure — there is no code path from a request payload into
`PeerCredential`. `test_peer_credentials_come_from_kernel_not_request_payload` proves this at the
primitive level (a real `socketpair`, asserting the reported uid is the actual OS uid and is
unaffected by any claim). Independently, since `HelperRequest.from_mapping` is a closed schema
with no `uid`/`gid`/`pid`/`agent_id` field at all, there is no way for a request to even *carry*
such a claim to begin with (verified by reading the dataclass field list in
`hpac_pawa_helper_protocol.py` §11). New test
`test_finding_c_channel_socket_directory_denies_a_different_uid` (this worker's file) adds a
genuine second-principal empirical layer: `nobody` cannot even open a connection to attempt
sending a spoofed identity. Rerun — **PASS**.

**Verdict: VERIFIED.**

---

## 13. Transitive import attack

No existing test (grepped for `PYTHONPATH`/`sitecustomize`/`usercustomize` across all
`hpac_pawa_helper*` test files) exercised this against the real end-to-end launch path — this
was a genuine gap. New tests (this worker's file):

- `test_transitive_import_hostile_pythonpath_not_inherited_end_to_end` — plants a hostile `pcae`
  shadow package on `PYTHONPATH` in the **launcher process's own environment** (simulating a
  compromised/misconfigured invoking agent), then runs the real, unmodified
  `launch_and_exchange` for a genuine `certification_read`. The shadow package writes a marker
  file the instant anything imports it. **Result: marker never created; the real production
  `pcae.core` package answered the read with genuine canonical content.** This empirically
  confirms `hpac_pawa_helper_launcher._CLOSED_ENV_ALLOWLIST = ("LANG", "LC_ALL")` — `PYTHONPATH`
  is not in the allowlist and `_child_environment` builds the child's env from scratch, never
  from `os.environ` wholesale.
- `test_transitive_import_cwd_shadow_module_not_reachable` — same attack shape via a
  cwd-relative single-file `pcae.py` shadow module in the launcher process's cwd at launch time.
  **Result: marker never created**, confirming nothing in the production launch path puts cwd on
  the exec'd child's import search path in a way that reaches this shadow.

Both ran genuinely on hac-dell — **PASS**.

**Verdict: VERIFIED — the privileged helper does not import untrusted code via `PYTHONPATH` or cwd shadowing.**

---

## 14. Replay — durable cross-process state

The durable replay ledger (`src/pcae/core/hpac_pawa_helper_replay_state.py`, 913 lines,
implemented by the immediately-preceding N16-5-F-5-TB-REPLAY-REPAIR phase) has an existing,
genuinely thorough regression suite:

- `tests/test_n16_5_f_5_tb_replay_repair.py` — **76 tests**, all running real, separate OS
  processes (`subprocess`), including clean restart, response loss/crash-indeterminate via real
  `SIGKILL`, an 8-real-process concurrent-duplicate race
  (`test_concurrent_duplicate_race_admits_exactly_one_process` — exactly one process observes
  `FRESH`, every other observes `DUPLICATE_IN_FLIGHT`), and the same race through the full
  dispatch path (`test_concurrent_dispatch_race_performs_exactly_one_mutation`).
- `tests/test_n16_5_f_5_tb_helper_iv_r.py` — 13 malformed-record variants, FIFO-slot
  fail-fast (non-blocking open), generation/installation-mismatch-as-conflicting.

Rerun on hac-dell (umask-corrected — see §17): **353/365 passed in the combined run** (12 of
these 13 fell out only because of the umask artifact described in §17, and all 13 pass with a
sane umask — 76/76 and the full `_iv_r` file both fully green). I did not find any test in this
area that was tautological or mocked-away; every scenario spawns real `subprocess.Popen`
children.

**New independent test.** All of "clean restart", "duplicate request", "conflicting request",
"generation mismatch", "response loss/crash-indeterminate", and "concurrent-duplicate race" were
already covered by the existing suite to a standard I judged adequate on inspection, so rather
than duplicate an existing scenario I focused this phase's one new addition on the two genuinely
uncovered areas above (§7 Finding C, §13 transitive import) — both new tests below live in
`tests/test_n16_5_f_5_tb_real_helper_boundary_repair_iv.py` and are new, independent, and
adversarial rather than restatements of predecessor tests.

**Verdict: VERIFIED (regression); no new replay defect found.**

---

## 15. Framing robustness

`test_framing_truncated_length_prefix`, `test_framing_zero_length_frame`,
`test_framing_oversized_frame_rejected`, `test_framing_truncated_body`,
`test_malformed_json_request_yields_no_response_not_a_crash`,
`test_second_request_on_same_connection_is_not_processed` (duplicate/trailing-bytes-shaped) all
assert `handle_one_request` returns `None` (no response sent) rather than crashing or treating
the failure as a trust decision. I read `read_one_frame`/`_recv_exact` in
`hpac_pawa_helper_entrypoint.py` myself: the 4-byte big-endian length prefix, the `length == 0`
and `length > MAX_FRAME_BYTES` checks, and `_recv_exact`'s "connection closed early" check are
all present and match what the tests exercise. Rerun — **PASS**.

**Verdict: VERIFIED.**

---

## 16. Predecessor test-template change — disposition

`git show 43813b16 -- tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` shows the only
predecessor test file the repair commit modified (45 lines changed). The change replaces
`_HELPER_SCRIPT_TEMPLATE`'s body from calling
`hpac_pawa_helper_entrypoint.main()` directly to instead calling
`build_helper_context()` + `run_one_shot()` directly, injecting a `_test_only_store` seam.

**Reasoning:** Repair B makes the `real` store profile **non-redirectable** — `main()` accepts
it only for the one fixed canonical protected root (`resolve_hpac_protected_root()`), and
`HPACStoreAuthority.production()` takes no root argument at all. A disposable-`tmp_path`-rooted
test can therefore no longer exercise a *disposable-root* "real store" scenario through `main()`
without literally reintroducing the redirection the repair exists to prevent — that scenario is
now structurally impossible through `main()`, by design. The template was updated to keep
exercising the genuine production `build_helper_context`/`run_one_shot`/`RealCanonicalReadAdapter`
path against a disposable root via the already-disclosed, explicit `_test_only_store` seam
(HPAC-PAWA-REQ-166) instead.

**Coverage was not weakened — it was relocated and, empirically, expanded.** The new file the
same commit added (`test_n16_5_f_5_tb_real_helper_boundary_repair.py`) independently and
directly exercises `main()` end-to-end via genuine subprocesses that I confirmed by grep and
by reading:
`test_repair_b_main_fails_closed_for_a_foreign_protected_root`,
`test_repair_b_main_fails_closed_on_missing_bootstrap_coordinates`,
`test_repair_b_main_fails_closed_on_non_integer_generation`,
`test_repair_b_main_fail_closed_exit_codes_are_distinct_and_nonzero` — none of which existed
before this commit. So `main()`/`resolve_store_profile()` are tested *more* directly and more
adversarially after the change than before it (before, only the happy path through `main()` was
exercised at all — the old template asserted nothing about `main()`'s failure exit codes).

**Disposition: T-A — legitimate fixture update, no weakening (coverage was, if anything,
broadened by the accompanying new test file).**

---

## 17. Existing regression suites — exact tallies

Ran on hac-dell, in `/tmp/n16-5-tb-iv-work/repo` (rsync'd from the working tree, `.git`
excluded — see the artifact note below), Python 3.12.3, `pytest -q`:

```
tests/test_n16_5_f_5_tb_real_helper_boundary_repair.py
tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py
tests/test_n16_5_f_5_tb_real_helper_store_launcher_iv.py
tests/test_n16_5_f_5_tb_replay_repair.py
tests/test_n16_5_f_5_tb_helper_iv_r.py
tests/test_hpac_pawa_helper_protocol_foundation.py
```

- **First run (default hac-dell `umask 0002`): 13 failed, 353 passed, 2 skipped.**
  All 13 failures were the durable replay store's own **correct** fail-closed behavior
  (`ReplayStateCorruption: replay namespace is group/other-writable; refusing to use it`) firing
  against `pytest`'s `tmp_path`, which inherited the ambient group-writable (`0775`) directory
  creation mode from hac-dell's account default `umask 0002` — an **environment artifact**, not a
  source defect (the module is *correctly* rejecting an environment it was told not to trust).
- **Second run (`umask 0022`, same tests): 1 failed, 365 passed, 2 skipped.**
  The one remaining failure, `test_helper_substitution_after_verification_is_rejected` (in the
  **unmodified, pre-repair-vintage** `test_n16_5_f_5_tb_real_helper_store_launcher_impl.py`), is
  a genuine, deterministic, **pre-existing test-correctness bug I am disclosing as a new finding**:
  it is `@pytest.mark.skipif(not sys.platform.startswith("linux"), ...)`-gated so it has likely
  never actually executed on the usual macOS development host; on real Linux it calls
  `resolved.helper_path.write_bytes(...)` to "replace" the helper — but `Path.write_bytes` opens
  and truncates the **same** inode in place (it does not unlink+recreate), so it is actually
  testing **in-place same-inode mutation** (§7's Finding C), not directory-entry substitution as
  its docstring claims, and therefore fails for exactly the same underlying, already-disclosed
  reason `test_repair_a_in_place_content_mutation_after_verification_is_not_executed` documents.
  This is a **test-labeling/methodology bug**, not a security regression — the correct
  directory-entry-substitution test, `test_repair_a_pathname_replacement_after_verification_executes_the_original` (which genuinely uses `os.replace`), passes. I did not modify this
  file (out of scope per my constraints); I flag it here for the primary operator.
- `tests/test_n16_5_f_5_tb_replay_repair.py` alone: **76 passed** (umask-corrected).
- `tests/test_n16_5_f_5_tb_real_helper_boundary_repair_iv.py` (this worker's new file):
  **5 passed**.

**Broader PAWA/PPA/writer-area sweep** (`pytest -k "pawa or hpac_protected_admin_writer or fifo
or ppa"`, umask-corrected, excluding files that failed to *collect* for reasons unrelated to this
repair): **452 passed**, plus a large block of failures/errors that are **both environmental and
outside this repair's scope**, confirmed by reading representative tracebacks:
  - ~9 collection errors: `ModuleNotFoundError: No module named 'fido2'` — an optional dependency
    not installed in this disposable venv (FIDO2/CTAP2-area tests, unrelated to the helper
    boundary).
  - ~74 failures + remaining errors: `git show <fixed-commit-hash>:...` /
    `fatal: not a git repository` — these are the repo's known "fixed-commit `git diff`
    self-check" contract-baseline tests (see project memory: "fixed-commit `git diff` self-checks
    are permanently broken by any future contract file — repin-debt, not flaky"); they fail here
    specifically because I deliberately excluded `.git` from the rsync to this disposable host
    (to avoid copying full repository history to a throwaway `/tmp` checkout). **This is an
    artifact of my transfer method, not evidence about the repair.** The primary operator should
    re-run these (they already have `.git` locally) rather than treat this count as a regression
    signal.

None of the 13+74+~9 failures/errors touch `hpac_pawa_helper_*`, `hpac_pawa_helper_replay_state`,
or `hpac_pawa_helper_store_adapter` logic itself — every failure in the helper-boundary-specific
files traces to the two causes above (umask, and the one pre-existing mislabeled test).

**Verdict: regression suite is green for the boundary under verification once the two
environment artifacts are accounted for; one new, non-security, pre-existing test-correctness
finding disclosed (§17 above).**

---

## 18. Contract baseline capture (not modified)

| Contract | File | Version | Status | SHA-256 (as of this verification) |
|---|---|---|---|---|
| HPAC-PAWA-HELPER-001 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | 1.0 | FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING | `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815` |
| HPAC-PAWA-001 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | 2.0 | FROZEN | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| HPAC-PPA-001 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | 2.0 | FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

I did not edit any of these three files. `HPAC-PAWA-HELPER-001` is the canonical helper-protocol
contract (naming note: the phase-authorization's alias is `N16-5-F-5-TB-CONTRACT`); it names
`HPAC-PAWA-001 v2.0` as its "companion" and `HPAC-001 v2.1`/`RHAMP-001 v1.0` as parent semantics.
`HPAC-PPA-001 v2.0` is the protected-presentation-installation/evidence-authority contract the
store adapter's `ceremony_entry`/installation-record reads are ultimately anchored to.

---

## New files created (all under `tests/`, none elsewhere)

- `/Users/atilamadai/repos/pcae-harness/tests/test_n16_5_f_5_tb_real_helper_boundary_repair_iv.py`
  — 5 new tests: `test_finding_c_non_owner_cannot_open_verified_inode_for_writing`,
  `test_finding_c_owner_can_mutate_but_owner_is_the_maximal_trust_principal`,
  `test_finding_c_channel_socket_directory_denies_a_different_uid`,
  `test_transitive_import_hostile_pythonpath_not_inherited_end_to_end`,
  `test_transitive_import_cwd_shadow_module_not_reachable`.
- `/Users/atilamadai/repos/pcae-harness/tasks/active-evidence-N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR-IV.md`
  — this report.

No other file under this repo was created or modified. Nothing under `src/pcae/**`, no contract,
no schema, no packaging file was touched. Nothing was committed, pushed, or finalized.

---

## Subsystem verdict table (this worker's own assessment only)

| Subsystem | Verdict |
|---|---|
| Repair A — same-file-object exec fd inheritance | VERIFIED |
| Repair B — REAL/NON_REAL profile selection & entrypoint wiring | VERIFIED |
| Fd inheritance isolation | VERIFIED |
| Forced exec-failure cleanup | VERIFIED |
| Path substitution (directory-entry swap) | VERIFIED |
| Symlink/FIFO/directory/digest/mode/generation attacks | VERIFIED |
| `certification_read` / `ceremony_entry` real-store wiring | VERIFIED |
| `admin_mutation`/`certification_write`/`presentation_evidence_write` fail-closed | VERIFIED (disclosed architectural blocker, unchanged, not this phase's to fix) |
| REQ-033 (no new `HPACWriterCapability` mint path) | VERIFIED |
| SO_PEERCRED / kernel-sourced peer identity | VERIFIED |
| Transitive import attack (PYTHONPATH / cwd shadow) | VERIFIED (new tests; previously untested) |
| Replay — durable cross-process state | VERIFIED (regression; no new defect) |
| Framing robustness | VERIFIED |
| **Finding C** | **Disposition C-A** — not exploitable under governed deployment invariants (same-inode write requires the deployment-owner uid or root; empirically confirmed a non-owner principal cannot open the inode for writing, and cannot even reach the private channel) |
| **Predecessor test-template change** | **Disposition T-A** — legitimate fixture update; coverage relocated and, on inspection, broadened by the accompanying new `main()`-level tests |
| New finding (non-security) | `test_helper_substitution_after_verification_is_rejected` in the pre-existing `test_n16_5_f_5_tb_real_helper_store_launcher_impl.py` is mislabeled/methodologically incorrect (tests in-place mutation via `write_bytes`, not directory-entry substitution as its docstring claims) and fails deterministically on real Linux; likely never run before because it is Linux-`skipif`-gated. Not fixed (out of my file-touch scope) — flagged for the primary operator. |

**Overall recommendation: INDEPENDENTLY VERIFIED, subject to the primary operator's own
independent re-verification of everything above** (source re-read, re-run of both the existing
suites and the new `_iv_r` file on hac-dell or an equivalent Linux host, and their own judgment
on the C-A/T-A dispositions). I did not commit, push, or finalize anything. Recommended next
step: a narrow, human-authorized contract-evolution phase to close the REQ-033
`admin_mutation`/`certification_write`/`presentation_evidence_write` blocker if/when those
operations are actually needed in production — this was already the predecessor phase's own
recommendation and this verification found nothing that changes it.
