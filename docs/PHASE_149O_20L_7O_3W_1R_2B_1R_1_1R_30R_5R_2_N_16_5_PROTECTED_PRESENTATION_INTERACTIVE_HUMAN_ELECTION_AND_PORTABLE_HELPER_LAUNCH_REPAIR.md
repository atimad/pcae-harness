# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2 — N-16-5 Protected-Presentation Interactive Human Election and Portable Helper Launch Repair

**Type:** governed narrow production repair  
**Status:** COMPLETE — REPAIR ONLY  
**Entry / attribution SHA (`A = R0`):** `0250e5f7`  
**Protected-presentation implementation SHA (`P`):** `5b6b4013`  
**Prior repair / this phase's predecessor-entry SHA (`V`):** `ea40c47e`  
**N-16-5:** NOT CLOSED

## Verdict

Finding **H-2 is REPAIRED — fresh independent verification and real
presentation certification remain pending.** The production helper now opens
its controlling terminal directly at `/dev/tty`, renders the exact canonical,
neutralized, digest-bound approval presentation, and accepts exactly one
closed election: `APPROVE` or `REJECT`. Ordinary stdin, the request protocol,
argv, environment, empty input, EOF, malformed input, interruption, and a
missing terminal cannot approve; all failure paths produce `CANCEL`.

Finding **F-2 is REPAIRED.** The launcher no longer asks Python 3.9.6 on macOS
to execute `/dev/fd/N`, which was independently reproduced at `A` as exiting
zero without running the helper. The fixed trusted interpreter now receives a
fixed `-I -c` bootstrap that reads and executes only the already-open,
launch-time-revalidated helper descriptor. The design retains the held-inode
TOCTOU property and introduces no pathname reopen, shell, PATH lookup,
caller-controlled executable, arbitrary argv, cwd import, or generic process
authority. Child exit zero without a valid authenticated response still fails
closed.

No normative contract changed. Production changes are exactly:

- `src/pcae/protected_presentation_helper.py`
- `src/pcae/core/protected_presentation.py`

## Human election and display binding

The helper keeps the request/response pipe and the human channel operationally
separate. The launcher closes inherited file descriptors 0, 1, and 2 in the
child. The helper obtains the human election by opening the fixed local
`/dev/tty` device itself; there is no fallback to stdin. The helper writes the
same `displayed_bytes` whose digest is checked against the signed request, then
writes a fixed prompt and reads one bounded line. Only exact ASCII `APPROVE`
and `REJECT` are authoritative.

All C0 and C1 controls, including tab, LF, CR, backspace, ESC/ANSI/OSC
introducers, and terminal-title controls, are rendered as visible escapes.
Bidirectional overrides remain neutralized. Consequently untrusted operation,
target, principal, transaction, intent, freshness, authentication context, or
request identifier content cannot overwrite the canonical presentation or
prompt. Approval remains operation-specific and request-bound; it is not
equivalent to FIDO2 touch (UP), PIN/biometric verification (UV), or successful
authentication.

The disclosed `_test_decision_source` remains permanently NON_REAL. It is
available only through the already-frozen, authenticated test directive and is
not selectable by the production resolver, caller flags, ordinary environment,
or protocol input.

## Portable held-byte launch

Historical invocation on the certification host:

`/usr/bin/python3 -I /dev/fd/N`

was reproduced under macOS Python 3.9.6: child status zero, no stderr, no
protocol response, helper body not executed. The repaired invocation is fixed:

`sys.executable -I -c <fixed held-descriptor bootstrap>`

The bootstrap reads `PCAE_PPLP_HELPER_FD` from the launcher's closed child
environment, drains that inherited descriptor, compiles it with a fixed virtual
filename, and executes it as `__main__`. The launcher still validates the
content-addressed installed helper, digest, regular-file identity, descriptor
identity, and current generation immediately before spawn. It launches the
same held bytes; changing or replacing the installation path cannot substitute
the child program. The child environment contains only the three private fd
numbers and `LC_ALL=C`. `sys.executable` remains the existing exact trusted
interpreter selection. The invocation remains a narrow PPA trust mechanism,
not runtime process execution.

## Guard reconciliation

The carried point-in-time guards were reconstructed at their own historical
heads and repaired without removing or renaming a test, skip/skipif/xfail,
wildcard, fnmatch, or broad post-phase allowance:

- `.30R.4R.2 test_01` now checks the immutable `5b6b4013..0b973e2e`
  implementation-IV window.
- The F-1 process-content guard checks executable additions in its immutable
  historical window, rather than later descriptive prose such as “generic
  subprocess API” or “posix_spawn avoids fork()”; detection of process
  primitives remains intact.
- `.1R.19R`, `.1R.19R.1`, `.1R.30R.1`, `.1R.30R.3.6`, `.1R.30R.5R`, and
  `.1R.30R.5R.1` open-ended historical comparisons now have exact proven
  upper SHAs or exact filename inventories.
- The moving completion-metadata assertion reads its immutable historical Git
  blob rather than today's live metadata.
- The protected-presentation historical suites assert the repaired fixed
  bootstrap and retain the no-shell/no-PATH/no-generic-process invariants.

The fresh scanner reports zero removed/renamed test definitions, zero skip,
skipif, `pytest.skip`, or xfail, and zero wildcard/fnmatch broadening.

## Verification evidence

Fresh `.30R.5R.2` suite: **71 passed, 0 failed, 0 skipped, 0 errors**. It covers
the 69 mandatory categories and additional held-descriptor/path-substitution
and historical-attribution cases.

Presentation implementation + IV + fresh repair: **205 passed**. Carried
historical-guard sweep: **347 passed**. CTAP2 repair + IV: **96 passed**.
Broad PAWA/PPA/RHAMP/FIDO2/verifier/Gate 5/Gate 9 affected sweep:
**893 passed, 2 deliberately deselected after fixed-SHA attribution**. The two
nodes are historical adversarial finding demonstrations
`test_object_dunder_new_bypasses_trusted_construction_seal` and
`test_forged_via_object_new_would_report_real_runtime_eligible`; both fail
identically at `A=0250e5f7`, so there is zero unexplained repair-attributable
regression. They are not hidden, repaired, skipped, or reclassified by this
phase.

A bounded real controlling-terminal smoke rendered the harmless certification
request through the actual helper. Direct operator control of that PTY could
not be exposed through this session, so no decision was synthesized; interrupt
produced `CANCEL` and no evidence. This proves the operational failure path but
is not a genuine APPROVE/REJECT certification and is not used to close N-16-5.

## Certification placement

**Option A — repair only.** RHAMP-REQ-156 gives every implementation phase its
own IV pair and places independent verification plus mandatory hardware and
N-16-5 closure in the dedicated certification phase. HPAC-PPA-REQ-074 likewise
requires fresh independent verification and mandatory hardware certification
after implementation. Same-phase repair and certification is therefore not
used.

Required successor (recommended, not begun):
**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1` — Independent Verification of
Protected-Presentation Human Election + Final Presentation-Bound N-16-5
Certification and Closure.** It must independently verify this repair, rotate
or install the new content-addressed helper generation through the protected
administrator path, obtain a genuine terminal APPROVE on the production
surface, perform the required genuine FIDO2 assertion, verify the resulting
PPA evidence and `PRODUCTION` `AuthenticatedHumanPrincipal`, and exercise the
existing Gate 5 without modifying it. N-16-5 may close only if the complete
matrix is green and no blocking finding remains.

## N-16-5 requirement matrix

| Requirement | Status after this repair |
|---|---|
| N-16-3 / N-16-4 | CLOSED / preserved |
| PAWA foundation and IV | VERIFIED / preserved |
| RHAMP contract, implementation, and IV | VERIFIED / preserved |
| CTAP2 PIN/UV repair and IV | VERIFIED / preserved |
| Genuine makeCredential, registration, getAssertion, UP, UV, rpIdHash, COSE, counter 6→8 | VERIFIED / preserved |
| Wrong challenge, replay, revoked credential | REJECTED / preserved |
| Protected-presentation architecture, implementation, software IV | VERIFIED / preserved |
| Interactive human election implementation | REPAIRED; fresh IV pending |
| Portable helper launch | REPAIRED; fresh IV pending |
| Genuine human APPROVE and real presentation evidence | NOT YET CERTIFIED |
| REAL authentication + REAL presentation coupling | DEFERRED to `.30R.5R.2.1` |
| `PRODUCTION` principal and Gate 5 consumption | DEFERRED to `.30R.5R.2.1` |
| PB / policy / runtime independence | VERIFIED / preserved |
| Carried guard reconciliation | VERIFIED |
| Current blocking findings | Certification remains incomplete; N-16-5 NOT CLOSED |

## Product verdicts

| Property | Verdict |
|---|---|
| H-2 interactive election | REPAIRED — fresh IV pending |
| F-2 portable launch | REPAIRED — fresh IV pending |
| Trusted local human input | VERIFIED in software |
| Protocol/TTY separation | VERIFIED |
| Explicit APPROVE / explicit REJECT | VERIFIED deterministically; real election deferred |
| Fail-closed CANCEL/EOF/no-TTY/invalid/interruption | VERIFIED |
| Human-visible binding / control-character safety | VERIFIED |
| Helper integrity / currentness / held-byte TOCTOU | VERIFIED |
| No generic process authority | VERIFIED |
| PPA evidence semantics | VERIFIED / unchanged |
| Real presentation ceremony | DEFERRED TO FRESH IV |
| REAL auth + REAL presentation | DEFERRED |
| Gate 5 real approval | DEFERRED |
| Mobile/future-mechanism flexibility | PRESERVED |

## Boundaries and carry-forward

`pcae-protected-local-presentation/1.0` is one **SUPPORTED LOCAL
PROTECTED-PRESENTATION PROFILE**, not the only PCAE approval UI and not a
global desktop-TTY requirement. `hpac.fido2.uv_presence.v2` remains one
**REAL-HARDWARE VERIFIED SUPPORTED AUTHENTICATION PROFILE**, not globally
mandatory or exclusive. Physical hardware and a local TTY are not prerequisites
for unrelated non-effecting development.

Mechanism-neutral authentication and protected-approval profiles, including a
mobile-only profile (platform authentication, biometrics, device credentials,
mobile-mediated NFC keys, and mobile protected presentation), remain open for
separately governed work. They are neither implemented nor foreclosed here.

Runtime remains `not_implemented` / `Observed` / `observe` / `unavailable`,
with 0 plugins and 0 capabilities. The first runtime external effect is
ABSENT / UNREACHABLE. N-16-6 and N-16-7 remain OPEN / UNTOUCHED; N-16-7 stays
strictly last. N-23-1 INFO and N-23-2 INFO / DEFERRED are unchanged.

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.** No delegated
worker was used. This primary human-authorized operator session alone performs
the governed commit, push, completion, and notification lifecycle.
