# Phase 145G.3V — Decision-Session Identity-Bound Resumption Independent Verification

**Status:** Complete (Independent Verification phase only; no production
code modified; no runtime-capability change).
**Verdict:** **VERIFIED WITH NON-BLOCKING FINDINGS.**
**Mode:** Independent, adversarial verification of Phase 145G.3's repair
of F-145G.2V-1 (identity-bound decision-session resumption). Phase
145G.3's own report, implementation notes, and tests were treated as
evidence only, never as authority. Four independent research passes ran
in parallel — contract diff, historical reproduction/enforcement
coverage, adversarial CLI/idempotent-path execution, and
application-layer/regression verification — each re-deriving conclusions
from contract text, git history, direct source inspection, and live CLI
execution before consulting Phase 145G.3's own claims.
**Governing authority:** IWPC-001 v1.3, IWC-001 v1.2 (unchanged), PEC-001,
CHGR-001, PFR-001, PROJECT_STATUS.md.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Repair authority exercised:** None. No Blocking finding was identified;
this phase's own governing prompt authorizes repair only for a directly
demonstrated Blocking defect, and none exists. This phase adds only this
report and routine lifecycle/metadata bookkeeping; no file under `src/`
or `tests/` was touched.

---

## 0. Method Statement

Before inspecting Phase 145G.3's implementation, expectations were
independently derived from IWPC-001 §34 (added by 145G.3), IWC-REQ-022
and IWC-REQ-151 (the pre-existing IWC-001 requirements the repair
enforces), and Phase 145G.2V's own finding record (F-145G.2V-1, IWPC-001
findings register row C-11). Four passes were then run:

1. **Contract diff & identity model** — line-level `git diff` of the
   IWPC-001 v1.2→v1.3 commit; enumeration of every distinct "identity"
   concept in the codebase and whether any are conflated; identity-claim
   channel verification (including adversarial environment-variable
   injection); CLI/application/persistence import-boundary check.
2. **Historical reproduction & enforcement coverage** — direct read of
   `decision_session.py`, `session_service.py`, and
   `publication_service.py` **as they existed immediately before** the
   repair commit, to confirm the pre-repair gap as described; a
   command-by-command enforcement table for the current code; a search
   for every place an owner-vs-claim comparison exists, to rule out
   duplicated policy.
3. **Adversarial CLI execution** — a live, disposable `pcae init`
   scratch repository; real `decision-session` CLI invocations
   (happy path, wrong identity, missing identity, the specific
   idempotent/cache-hit replay attack described by F-145G.2V-1,
   malformed/edge-case claims, on-disk tampering, and restart safety).
4. **CLI/application boundary & regression** — verification that the CLI
   performs transport/syntax validation only and delegates the actual
   authority decision to the application layer; exit-code-mapping
   consistency; and an actual run of the identity-binding test files,
   the broader interactive-workflow/publication/decision-session test
   slice, and the project's `fast_green` regression gate.

Each pass's findings are reconciled below; no material disagreement was
found between the four passes, or between the passes and this report's
own spot-checks of the underlying source and contract text.

---

## Part I — Contract Verification (IWC-001 / IWPC-001 v1.2 → v1.3)

**Correction to the initiating brief's premise:** only **IWPC-001** was
bumped v1.2 → v1.3 (commit `abeb0f68`). **IWC-001 remains at v1.2,
unchanged** (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md:6`). This
is not a defect: IWC-REQ-022 and IWC-REQ-151 already specified the
identity-bound-resumption requirement in IWC-001 v1.2 (confirmed present
at lines 1041 and 1496, unchanged); IWPC-001 is the CLI/transport
contract, so only it needed the additive enforcement revision. Phase
145G.3's own report discloses this accurately
(`docs/PHASE_145G3_..._REPAIR.md:77-80`).

`git show abeb0f68 -- docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`
confirms, independently:

- Version header: `1.2` → `1.3` only.
- `--as-identity` added as a required argument to the seven mutating
  requirements (evidence/select/clarify/preview/confirm/readiness/cancel,
  IWPC-REQ-016/017/018/020/023/025/192) via **additive** text insertion —
  no requirement renumbered.
- IWPC-REQ-195 kept its original number; its text was corrected in place
  (it previously only guaranteed identity was "never inferred," not that
  it was enforced) — a disclosed correction, not silent semantic drift.
- New exit code 6 (`identity_binding_mismatch`) added; IWPC-REQ-051
  amended in place to bound codes at 0–6 (previously 0–5).
- New §19.1 mapping row: `identity_binding_mismatch` → exit 6 →
  `SessionApplicationService._require_bound_identity`.
- New §34 defines the identity model, explicitly confirms `status`/
  `create` are unaffected, and explicitly addresses replay/idempotent
  behavior for `cancel` and `readiness`.
- Findings register gained row C-11 (Blocking → Repaired) additively.

**Verdict: additive-only, no renumbering, no broken references, no
unrelated semantic drift.** Identity model, claim semantics, mismatch
behavior, and exit code are all explicitly and unambiguously defined.

## Part II — Independent Reproduction of F-145G.2V-1

Repair commit `abeb0f68` ("Phase 145G.3: decision-session
identity-bound resumption enforcement"), parent `c4e2a7ac` (145G.2V's
last commit). Reading `git show abeb0f68~1:src/pcae/commands/decision_session.py`
directly (689 lines, pre-repair) confirms: every mutating handler
(`run_decision_session_evidence`, `_select`, `_clarify`, `_preview`,
`_confirm`, `_cancel`, `_readiness`) took only `session_id` plus
command-specific fields — **no identity/claim argument existed at all**,
and no `--as-identity`-shaped flag existed anywhere in the file.
`git show abeb0f68~1:src/pcae/interactive_workflow/application/session_service.py`
confirms no mutating method took a `caller_identity` parameter and no
owner-vs-caller comparison existed anywhere.

The readiness idempotent-cache gap specifically, `git show
abeb0f68~1:src/pcae/interactive_workflow/application/publication_service.py`
lines 158-177:

```python
def ensure_readiness_package(self, session_id: str) -> PendingReadinessRecord:
    existing = self.find_readiness_package_for_session(session_id)
    if existing is not None:
        return existing
    package = self._sessions.construct_readiness_package(session_id)
    return self.persist_readiness_package(package)
```

No identity parameter; the cache-hit branch (`existing is not None`)
returns success unconditionally. This is an exact match for
F-145G.2V-1's described readiness-cache gap. **The pre-repair defect is
independently confirmed, precisely as described, from git history —
not merely from Phase 145G.2V's or 145G.3's own narrative.**

## Part III — Identity Model Verification

Six distinct identity concepts were independently located and confirmed
not conflated:

| Concept | Definition site | Set | Compared against claim? |
|---|---|---|---|
| `owner_identity` (identity binding) | `models/session.py:86` | Once, at `create` (`session/coordinator.py:90,105`); copied unchanged by every state transition | Yes — sole comparison target |
| Identity claim (`--as-identity`) | `cli.py` (7 subparsers) | Per-invocation, caller-supplied | Compared, never stored as truth |
| Confirmation statement (`--statement`) | `commands/decision_session.py` → `session_service.py:965` | Free-text rationale in `metadata` | No — unrelated surface |
| Publication operator/authorizer (`--operator-id`) | `commands/governance_record.py:205,219` | Separate publication-authorization flow (`publication_service.py:273`) | No — never touches `owner_identity` |
| Runtime/agent-lock identity (`claude-local`) | PCAE session-lock subsystem | N/A to interactive_workflow | Zero references inside `interactive_workflow/` (grep-confirmed) |
| Session-verification identity (mismatch outcome) | `application/errors.py:80-87` | N/A | `SessionIdentityMismatchApplicationError`, a distinct typed error |

No code path reuses `operator_id`, the confirmation statement, or any
agent-lock/runtime identity as a substitute for the owner-identity
comparison, or vice versa. No inferred identity was found.

## Part IV — Identity Claim Channel

Exactly one production channel: the `--as-identity` CLI argument,
defined per-subcommand (`cli.py`, `required=True`, no environment/config
default). Grep across `interactive_workflow/` and `commands/
decision_session.py` for `getlogin`, `getuser`, `os.environ`, `getenv`,
`GIT_AUTHOR`, `claude-local`, `agent_lock`, `hostname` returned **zero
matches**. Adversarially confirmed: `tests/
test_phase_145g2v_independent_verification_partial.py:276-334` sets
`USER`, `USERNAME`, `GIT_AUTHOR_NAME`, `PCAE_IDENTITY`, and
`PCAE_AGENT_ID` to `"mallory"` and the mismatch is still correctly
rejected using only the `--as-identity` value (independently re-run,
57/57 passed). Transport syntax validation only: non-empty, ≤512 chars,
no control characters (`decision_session.py:289-316`) — no equality
comparison performed at this layer.

**Verdict: exactly one claim channel; no implicit/environmental identity
source of any kind.**

## Part V — Enforcement Coverage

Independently verified per command (file:line citations for both the
CLI structural gate and the application-layer enforcement call):

| Command | Enforced | CLI (structural gate) | Application (owner comparison) |
|---|---|---|---|
| evidence | Yes | `cli.py:10701-10706`, `decision_session.py:491` | `session_service.py:504` (`submit_evidence`) |
| select | Yes | `cli.py:10724-10729`, `decision_session.py:525` | `session_service.py:639` (`select_decision`) |
| clarify | Yes | `cli.py:10742-10747`, `decision_session.py:581` | `session_service.py:717` (`submit_clarification`) |
| preview | Yes | `cli.py:10756-10761`, `decision_session.py:612` | `session_service.py:801` (`generate_preview`) |
| confirm | Yes | `cli.py:10772-10777`, `decision_session.py:651` | `session_service.py:894` (`record_confirmation`) |
| readiness | Yes | `cli.py:10794-10799`, `decision_session.py:725` | `publication_service.py:180` → `session_service.py:428` (`require_bound_identity`) |
| cancel | Yes | `cli.py:10809-10814`, `decision_session.py:685` | `session_service.py:1031` (`cancel_session`) |
| status | **No (intentional)** | no `--as-identity` argparse flag (`cli.py` ~10784-10787) | none |

`status`'s exemption was independently judged, not assumed: reading
`run_decision_session_status` (`decision_session.py:433-481`) confirms
it only calls `load_session`/`find_readiness_package_for_session` — no
orchestration advance, no persistence write, no state mutation anywhere
in its body. It does return `owner_identity` in its payload
(`serialization/schema.py:37`), but that is the session's own
creation-time attribute already implicitly known to whoever holds the
`session_id` from `create` — not new information disclosed by
impersonation, and not an action a mismatched caller can use to affect
the session. **Judged a legitimate, non-blocking exemption**, not an
unexamined assumption.

## Part VI — Validation Ownership

Exactly **one** occurrence of the owner-vs-claim equality check exists
in the entire codebase:

```python
# src/pcae/interactive_workflow/application/session_service.py:397-426 (_require_bound_identity)
if not isinstance(caller_identity, str) or caller_identity != session.owner_identity:
    raise SessionIdentityMismatchApplicationError(...)
```

It is exposed for cross-service reuse via one public wrapper
(`require_bound_identity`, `session_service.py:428-443`), whose own
docstring states this exists specifically to avoid duplicating the
comparison. `PublicationApplicationService.ensure_readiness_package`
(the one method outside `SessionApplicationService` that needs the
check) calls this shared wrapper rather than reimplementing it. The
CLI's `_require_identity_claim` performs only structural validation and
contains no reference to `owner_identity` anywhere in its body (grep
confirmed). **Single ownership confirmed; no duplicated policy.**

CLI → Application → Domain → Persistence: the comparison lives in the
Application layer only; `Session` (domain) holds `owner_identity` as
inert data and performs no comparison itself; persistence performs no
authorization logic. No transport-layer (CLI) authorization exists.

## Part VII — Idempotent Paths (Critical Verification Area)

Live adversarial CLI execution against a disposable scratch repository
(`pcae init`), not merely source reading:

- **Readiness cache-hit replay — the exact F-145G.2V-1 scenario:**
  `readiness --as-identity alice` (constructs and persists a readiness
  package, exit 0) immediately followed by `readiness --as-identity
  mallory` against the now-cached package →
  **`identity_binding_mismatch`, exit 6.** Source confirms why:
  `publication_service.py:180` calls `require_bound_identity` **before**
  `find_readiness_package_for_session` (the cache lookup) on the
  following line — the check runs ahead of, not after, the idempotent
  branch. Re-running `readiness --as-identity alice` afterward confirmed
  the cached package (`package_id`, `persisted_at`) was untouched by the
  rejected attempt. **This specific regression could not be
  reproduced.**
- **Cancel idempotent replay:** correct identity against an
  already-`Cancelled` session succeeds (true idempotency preserved);
  wrong identity against the same already-`Cancelled` session is
  rejected (exit 6) — confirmed by source ordering
  (`cancel_session:1030-1033`: `_require_bound_identity` at line 1031
  precedes the idempotent early-return at 1032-1033) and by live replay.
- select/evidence/clarify/preview/confirm replay: all deterministically
  rejected under a wrong identity claim, live-tested; no partial state
  mutation observed via `status` before/after any rejected attempt.

**Verdict: no idempotent or cache-hit path allows a mismatched caller to
receive success because the operation was already complete.**

## Part VIII — Persistence

- `owner_identity` is written once, at session creation, and never
  re-derived or duplicated elsewhere (`session/coordinator.py:90,105`;
  every `with_state`/`with_decision_capture` transition copies it
  unchanged).
- Schema/serialization unchanged by this repair — `owner_identity` was
  already persisted before 145G.3; no new field, no migration needed.
- **Tampering tests (live):** editing the persisted `owner_identity`
  field to a new value causes the *original* owner's identity claim to
  now mismatch (exit 6) and the *tampered* value to succeed — this is
  the system operating exactly as designed (a value comparison against
  whatever is currently and legitimately persisted); it is **not** a
  cryptographic integrity guarantee against direct filesystem tampering,
  and none was ever claimed by IWPC-001 §34 or the 145G.3 report.
  Deleting the field, or setting it to an empty string, fails closed in
  every case tested (`persistence_corrupt`, exit 1) — no silent
  "allow" path for corrupted/missing owner data.
- **Restart safety (live, multi-process):** a workflow split across
  three separate CLI process invocations (evidence → select → preview,
  owner `carol`), followed by a fourth fresh-process `confirm` attempt
  under a wrong identity (`eve`), was rejected (exit 6) with the session
  state confirmed unadvanced by `status` afterward.

**Non-blocking observation:** the persisted `owner_identity` field has
no cryptographic tamper-evidence (no digest/HMAC over the session file
itself; only readiness *packages* carry binding digests). This is a
pre-existing trust-boundary characteristic of the filesystem-backed
persistence layer generally (filesystem write access is an implicit
trust boundary throughout this repository's design), not a regression
introduced by, or within the repair scope of, Phase 145G.3. Recommend
this be documented explicitly as an accepted trust-model assumption if
it is not already stated in a persistence-layer threat-model document —
Deferred, not this phase's to fix.

## Part IX — CLI Verification

All seven mutating commands: `--as-identity` is `required=True`
argparse, identical help text
(`"Identity claim resuming this session; must equal the identity bound at creation (IWC-REQ-022/151)."`).
The identity-mismatch exit code (6) is produced by exactly one shared
dict lookup (`_EXIT_CODE_BY_ERROR_TYPE["identity_binding_mismatch"]`,
`decision_session.py:137,177`) via `_handle_application_error`
(`decision_session.py:366-375`) — structurally impossible for any one
command to diverge from another. JSON mode (`--json`) and plain-text
modes both route through the same error-mapping path. Live testing
confirms: missing `--as-identity` is rejected by argparse itself before
any handler code runs (exit 2, `"the following arguments are
required"`) — no silent default.

**Non-blocking cosmetic finding:** `EXIT_IDENTITY_BINDING_MISMATCH` is
defined (`decision_session.py:137`) but omitted from the module's
`__all__` list (which stops at `EXIT_STALE_AUTHORIZATION`,
`decision_session.py:785-791`). No functional effect (the test suite
imports it by explicit name, not via `import *`); worth a one-line fix
in a future documentation/cleanup phase, not blocking.

## Part X — Application Verification

`SessionApplicationService._require_bound_identity`
(`session_service.py:397-426`): exact `!=` string comparison, no
`.lower()`/`.strip()` normalization (confirmed both by source and by
live case-sensitivity/whitespace adversarial tests — both correctly
rejected as mismatches, documented as intentional in the method's own
docstring). Fail-closed: mismatch raises before any `Session`/success
value is returned to the caller. No state mutation occurs before the
check in any of the seven enforced methods — verified by reading the
`load_session` → `_require_bound_identity` → body ordering in each
(`cancel_session`, `submit_evidence`, `select_decision`,
`submit_clarification`, `generate_preview`, `record_confirmation`,
`construct_readiness_package`). Errors are typed
(`SessionIdentityMismatchApplicationError`, a distinct
`ApplicationServiceError` subclass), mapped deterministically to exit
code 6 via a two-hop dict lookup with no branching logic. **No hidden
bypass found.**

## Part XI — End-to-End Verification

Live CLI-only reproduction, disposable scratch repository:
`create --owner-id alice` → `evidence` → `select` → `preview` →
`confirm` → `readiness`, all with `--as-identity alice` — every step
exit 0. The same chain repeated with `--as-identity mallory` at each
resumed step against the `alice`-owned session deterministically
rejected (exit 6) at every point, with no partial advance. Repeated
after a readiness package was already cached (Part VII) and after a
simulated multi-process restart (Part VIII) — both hold.

## Part XII — Adversarial Testing

Live-tested and all deterministic: empty/whitespace-only claim
(`invalid_request`, exit 1); case mismatch (`ALICE` vs `alice`,
mismatch, exit 6 — case-sensitive by design); Unicode
homoglyph/confusable substitution (mismatch, exit 6 — no normalization,
correct strict comparison); oversized string >512 chars
(`invalid_request`, exit 1); boundary 512-char valid-length-but-wrong
value (correctly falls through to a mismatch, not a length error);
leading/trailing whitespace (mismatch, exit 6 — no trimming); replay and
cache replay (Part VII); stale/corrupted/substituted persisted owner
(Part VIII); JSON mode (consistent error payloads); subprocess restart
(Part VIII); repeated commands; no CLI bypass path found in any test.

## Part XIII — Dependency Verification

`commands/decision_session.py`'s `build_application_context()` does
import persistence/domain internals directly
(`FilesystemPendingReadinessStore`, `FilesystemSessionRepository`,
`SessionCoordinator`) — but this is a **pre-existing, disclosed
composition-root exception** (module docstring, `.pcae/policy.toml:52-67`,
and a dedicated AST-based forbidden-import test), unrelated to and
unmodified by Phase 145G.3. Outside that one documented composition
root: zero reverse-direction imports found (`application` importing
`commands`, or `persistence`/`session`/`models` importing `application`,
all grep-confirmed absent). No new policy widening introduced by this
phase.

## Part XIV — Regression

Actually executed (not assumed):

```
pytest tests/test_phase_145g3_decision_session_identity_binding.py \
       tests/test_phase_145g2v_independent_verification.py \
       tests/test_phase_145g2v_independent_verification_partial.py \
       tests/test_phase_145g2_decision_selection_cli_repair.py \
       tests/test_phase_145g1_decision_session_cli_repair.py \
       tests/test_phase_145g_decision_session_cli.py
→ 185 passed in 14.15s

pytest tests -k "interactive_workflow or decision_session or publication" -q
→ 4 failed, 860 passed, 1 skipped
  (the 4 failures are pre-existing packaging tests, test_cltr_authority_136ah_publication.py /
   test_cltr_authority_136ai_publication_independent.py, that shell out to
   `python -m build --wheel`; environment/build-tooling failures unrelated
   to decision-session/identity logic, not a regression from this phase)

python -m pytest -m "fast_green" -n auto -q
→ 4391 passed in 103.02s (0 failed)
```

The `fast_green` result (4391/4391) matches exactly the baseline recorded
by Phase 145G.3 itself in `.pcae/phase-completion-metadata.json` and its
own phase report. **No divergence; inherited failures (the 4 packaging
tests) are pre-existing and out of this phase's and 145G.3's scope.**

---

## Findings Register

| ID | Severity | Description |
|---|---|---|
| N-145G.3V-1 | Non-Blocking | Persisted `owner_identity` has no cryptographic tamper-evidence; a caller with direct filesystem write access to the session store can rewrite ownership outright. Pre-existing filesystem-trust characteristic of the persistence layer generally, not a regression introduced by or within Phase 145G.3's repair scope. Recommend explicit documentation as an accepted trust-boundary assumption in a future phase. |
| N-145G.3V-2 | Non-Blocking | `EXIT_IDENTITY_BINDING_MISMATCH` omitted from `decision_session.py`'s `__all__` list. No functional effect; cosmetic completeness gap. |
| N-145G.3V-3 | Non-Blocking | `status`'s payload includes `owner_identity`, the session's own creation-time attribute; not a new disclosure enabled by impersonation and not actionable by a mismatched caller, but noted for completeness since `status` is the one command left unenforced. |

No Blocking finding was identified in any of the fourteen verification
parts above.

## Explicit Verdict on F-145G.2V-1 Closure

**F-145G.2V-1 is confirmed closed.** The pre-repair gap was
independently reproduced from git history exactly as described
(no identity channel existed; no owner comparison existed anywhere;
the readiness idempotent-cache branch returned success
unconditionally). The current implementation enforces a single,
non-duplicated owner-identity comparison ahead of every state-mutating
action and ahead of every idempotent/cache-hit early-return path across
all seven resumption-capable commands, via exactly one explicit,
non-inferrable claim channel (`--as-identity`), with a consistent,
deterministic exit code (6) and no CLI-layer authorization shortcut.
Live adversarial CLI execution — including the specific readiness
cache-hit bypass scenario F-145G.2V-1 itself described — could not
reproduce any bypass.

## Overall Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS.**

All eighteen exit criteria of this phase's governing prompt are met:
contracts independently verified (Part I); F-145G.2V-1 independently
reproduced pre-repair and confirmed closed post-repair (Parts II, and
above); identity model verified with no conflation (Part III); exactly
one identity claim channel (Part IV); all required commands enforce
identity, `status`'s exemption independently justified (Part V);
singular, correct validation ownership (Part VI); every idempotent path,
including the readiness cache-hit path specifically named by
F-145G.2V-1, enforces identity before returning (Part VII); persistence
remains compatible, with one disclosed non-cryptographic trust-boundary
observation (Part VIII); CLI remains a transport adapter only (Parts
IX, and the delegation confirmed in Part X); end-to-end CLI verification
succeeded under both correct and wrong identity (Part XI); dependency
boundaries intact, with the one pre-existing composition-root exception
correctly attributed as out of this phase's scope (Part XIII);
regression clean and `fast_green`-baseline-matched (Part XIV); runtime
remained Observed/observe/unavailable throughout, confirmed via `pcae
runtime inspect` before and after; no engineering execution capability
was added; no Blocking finding remains.

## Recommendation (not authorized to begin)

**145H — Interactive Workflow Chapter Independent Certification** is the
recommended next phase, given 145G.3's own repair, this phase's
independent confirmation of its closure, and no outstanding Blocking
finding across the 145A–145G.3V arc. This recommendation does not
authorize 145H, 145G.4, or any later phase to begin.
