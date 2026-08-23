# Phase 149O.20L.7O.2U.3 Complete — Reference Adapter Implementation Independent Verification

**Verdict: A — INDEPENDENTLY VERIFIED, READY FOR v0.3 ALLOW/DENY DEMO.**
No production source modified. No frozen 2U.1 contract modified. No
finding repaired inside this phase.

Independently re-derived the exact 2U.2 production diff via `git diff
--stat` between the 2U.1 close-out commit (`e3da848d`) and 2U.2's
implementation commit (`0ab6faa5`) — not from 2U.2's report prose —
confirming exactly the four expected production files changed, with
zero downstream authority-chain edits.

**Fresh, independent 116-test adversarial suite**
(`tests/test_phase_149o_20l_7o_2u_3_reference_adapter_independent_verification.py`,
sharing no helper functions or test bodies with 2U.2's own suite):
authority-field injection (17 field names × 3 injection points, plus a
nested-authority-object and unknown-field variant) — all rejected/
ignored; repository-fingerprint and base-commit binding — fail-closed on
forged/missing/foreign/non-ancestor values; content-hash canonicalization
(CRLF-vs-LF, payload/hash swap) — fail-closed; task-scope authority
source and bypass attempts (prefix, traversal, absolute path, case) —
fail-closed; `content_after`/text-only/delete/multi-file/duplicate-path
narrowings — all safe; ECP authority-field hardcoding — confirmed;
candidate-ID collision/idempotent-replay — correct; whole-record
tamper detection — every one of seven distinct fields individually
mutated and detected; CLI create/show/list/help — exercised end-to-end
via real subprocess, clean error handling, no traceback leaks, no
authorization language in help text; Claude Code adapter dataflow —
regex-verified no `promote`/`push` call site and no authority-field
assignment anywhere in the script, non-normativity confirmed (zero
`claude`/`anthropic` tokens in core/commands modules); an alternate
synthetic producer validates identically; downstream promotion-chain
preservation — `promotion_authorized` is reachable only via an explicit
human CLI flag on a separate command, never from any intake-candidate
field, confirmed even with a forged `self_reported_complete`/
`human_reviewed` claim.

**Result: 116/116 passed. No Blocking finding.**

**Two Non-Blocking findings** (documented, not repaired this phase):
1. `_path_is_safe_relative` does not actually catch a pure-backslash
   Windows absolute path, contrary to its own docstring — backstopped by
   the independent task-scope check, and not exploitable on POSIX (the
   only supported PCAE runtime).
2. `repo_fingerprint` is a pure content hash of root commit(s); two
   directories with byte-identical genesis commits collide by design
   (intentional, for clone/fork stability) — not a way to impersonate an
   unrelated real repository.

**Regression**: 2U.2's own 24-case suite re-runs clean (24/24). 2U.1's
contract-freeze suite: 30/31 (the one non-pass is a 2U.1-era guard
correctly now failing because 2U.2 legitimately implemented the CLI it
guarded against — not a regression). Downstream regression across every
test file exercising the promotion/ECP call sites (mutation-permission/
promotion integration, `test_agent.py`, RWMPC contract/wave-1
independent-verification suites, repository-wide mutation-inventory
guard): 4313/4314 passed — the one failure is a pre-existing
fixed-historical-baseline-drift assertion unrelated to intake by name or
mechanism. Repository-wide `fast_green` (9040 collected): 335 pre-existing
failures, mechanically grepped and confirmed none reference
intake/ECP/EPR/promotion by name.

**Trust-scope reassessment** (independently reconstructed, not
re-trusted from 2U.2's own claim): HMIC's actual scope is HATP
hardware-credential/FIDO2/WebAuthn certification specifically, not a
generic trusted-computing-base doctrine. `src/pcae/core/intake.py` is
authority-adjacent (constructs evidence a human reviews; cannot itself
grant authority, backstopped independently by the unmodified
`_ecp_validate`). `src/pcae/commands/intake.py` is a pure command/UI
wrapper (verified no direct `store_execution_change_package` call).
`scripts/claude_code_intake_adapter.py` is a non-authoritative producer
outside the trusted kernel by design (talks to PCAE only through the
`pcae intake create` CLI/JSON boundary).

No production code or frozen-contract file modified this phase. No
HATP/WebAuthn/FIDO2/DeepSeek/Codex work. No release tag. No raw/force
git push. Runtime posture unchanged
(`Observed`/`observe`/`execution_unavailable`).

Full text:
`docs/PHASE_149O_20L_7O_2U_3_REFERENCE_ADAPTER_IMPLEMENTATION_INDEPENDENT_VERIFICATION.md`.

Recommended next: **149O.20L.7O.2U.4 — Deny/Allow Demo and Quick-Start
Documentation** (already frozen by the 2U release plan).
