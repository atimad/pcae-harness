# Phase 149O.20L.7O.2N.15 Completion Report

**Verdict:** COMPLETE — ARCHITECTURE SELECTED AT DESIGN LEVEL ONLY, NOT
IMPLEMENTED. NO DNS/TLS PROVISIONED. NO PRODUCTION SOURCE CHANGED. NO
HAC-DELL SESSION OPENED.

Architecture-only phase, following Phase 149O.20L.7O.2N.14 (Independent
Verification). Independently re-derives HRWP-001 v1.1 and HRAC-001
v1.0 in full, and reads fresh `hatp_fido2_provider.py`,
`hatp_providers.py`, `hatp_hardware_credentials.py`, `hatp_bootstrap.py`,
and `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` directly — never
from a prior phase's summary — to select, at architecture level only,
the literal-naming strategy HRWP-REQ-027/HRWP-REQ-029/HRWP-REQ-031 name
as an explicit open infrastructure requirement.

**Selected architecture** (`docs/PHASE_149O_20L_7O_2N_15_REMOTE_WEBAUTHN_RP_ID_ORIGIN_HTTPS_INFRASTRUCTURE_ARCHITECTURE.md`):

1. **RP-ID** — a dedicated, real, publicly-registrable subdomain of a
   human-controlled domain (e.g. `hatp.<controlled-domain>`), one value
   shared across every PCAE-governed repository this operator controls.
   Rejected: bare organization domain (WebAuthn RP-ID suffix-matching
   would over-scope credential validity to every subdomain), a
   per-repository domain as the default (multiplies enrollment
   ceremonies for no security benefit — repository identity is already
   enforced independently at the `repository_id`/`DeploymentBinding`
   layer), and an internal-only/private-CA domain as the default
   (requires a manual, ungoverned private-root-trust ceremony on the
   iPhone client). The internal/private-CA model is retained as a named,
   valid fallback, not forbidden.
2. **Origin** — exactly `https://hatp.<controlled-domain>`, serving both
   the ceremony-delivery page and the request/verification API from one
   fixed origin (HRAC-REQ-061 forbids a separate delivery domain).
3. **HTTPS/TLS** — hac-dell does not itself terminate public TLS; a thin
   reverse proxy in front of it terminates TLS and forwards over a
   private internal hop to a narrowly-scoped companion HTTP process.
   Certificate: publicly-trusted CA via ACME DNS-01 challenge (proves
   domain control without exposing an HTTP endpoint to the public
   internet, avoiding both the private-CA client-trust ceremony and full
   public HTTP exposure). Network reachability: a private VPN mesh only
   — named explicitly as defense-in-depth, not a substitute for
   WebAuthn's own origin/RP-ID phishing resistance (HRAC-REQ-061
   restated); full public reachability is named as an available,
   non-default alternative.
4. **Trusted-kernel/adapter boundary** — extends HRWP-REQ-062/
   HRAC-REQ-070's existing classification with this phase's own
   component list: the reverse proxy, ACME/certificate-lifecycle
   tooling, and VPN-mesh client software are thin adapters outside the
   trusted kernel; the companion process's request/challenge/
   verification logic is the trusted kernel, colocated with, but not
   equal to, hac-dell's own governance-authority files.

**Deliverables:** a security-boundary diagram (ASCII), a challenge/
assertion end-to-end flow diagram substituting this phase's literals
into HRAC-001's already-frozen sequence, a 7-category threat analysis
(phishing, origin confusion, replay, stale challenge, wrong repository
binding, wrong signer selection, credential substitution) each mapped to
the specific existing HRWP-001/HRAC-001 mechanism that mitigates it, and
a decision table (selected model vs. every rejected alternative, with
rationale).

**Compatibility confirmed, no singleton assumption introduced:**
multiple `HardwareCredentialRecord`s per `Principal`, multiple
`SignerRecord`s, and `DeploymentBinding`'s EXPLICIT_SIGNER selection
(HSCE-REQ-080, re-derived live at both request-creation and verification
time per HRAC-REQ-019/033) are all independently re-derived as unaffected
by this phase's RP-ID/origin/network selection — the shared RP-ID
carries no repository or signer identity; that remains the existing
`repository_id`/`DeploymentBinding` resolution's exclusive job.

**Independent byproduct finding (not a phase dependency):** fresh reading
of `hatp_hardware_credentials.py` this phase reconfirms
`_PROTOCOL_VALUES == frozenset({"FIDO2", "PIV", "WEBAUTHN"})` — Phase
149O.20L.7O.2N.13's widening (independently verified by 2N.14) is
present in current source. This phase's own RP-ID/origin/HTTPS selection
has no dependency on that prerequisite (HRAC-REQ-066 already states
signer resolution never reads `protocol_name`), but the re-confirmation
is recorded here as a fresh, independent check, not carried forward from
2N.14's own claim.

**Provider-dispatch gap** (`create_production_hardware_provider()`
unconditionally attempting `Fido2HardwareProvider` first regardless of
requested profile, NBF-149O.20L.7O.2N.12-1 Outcome A) remains named,
open, and explicitly out of this phase's scope — an implementation-phase
routing decision (HRWP-REQ-006), orthogonal to RP-ID/origin/HTTPS
architecture.

**No production change:** `git diff --stat 53d78fce..HEAD -- src/pcae/
scripts/` is empty — this phase touches only one new `docs/` file,
`PROJECT_STATUS.md`, `CHANGELOG.md`, task-lifecycle files, and
`.pcae/phase-completion-*`.

**Fast Green, A/B-attributed** (git-worktree isolation at the fixed
phase-entry checkpoint `53d78fce`, identical `-n auto` parallelism,
invoked via `python -m pytest` per this repository's documented
invocation convention): baseline (phase-entry commit, clean worktree):
339 failed / 8688 passed / 4 skipped / 9 errors, 143.70s — byte-identical
to Phase 149O.20L.7O.2N.14's own recorded baseline. With this phase's
changes (current `HEAD`, working tree clean after commit): 341 failed /
8686 passed / 4 skipped / 9 errors, 134.34s. Diffing the FAILED/ERROR
node-ID sets: 3 node IDs failed only with-changes, 1 node ID failed only
at baseline. Each of the 4 differing node IDs was independently
re-run in isolation:
`test_backend_cli.py::TestBackendReviewReject::test_reject_cannot_approve_after_reject`
and
`test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`
each passed cleanly in isolation (confirmed `-n auto` parallel-worker
order/state-dependent flakiness, not phase-attributable);
`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli` is a
subprocess-CLI-invocation test with a 15-second timeout that flaked once
even in isolation under system load, then passed twice more in isolation
immediately after (confirmed timing-flaky, not content-dependent, not
phase-attributable — this phase touches no `shell_gate`-related source);
`test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main`
is the same self-resolving pending-push check named by Phase
149O.20L.7O.2N.14's own report (expected true until this phase's commits
are pushed). **Attributable regression count this phase: 0.** A
deselect-based clean re-run (the union of both runs' 351 distinct
FAILED/ERROR node IDs, deselected) confirms **8685 passed, 4 skipped, 0
failed** — the structured `fast_green` field value this report's
metadata records.

**No implementation.** No `RemoteWebAuthnProvider` class, no challenge/
session store, no HTTP route, no browser/mobile client code, no reverse
proxy, no ACME/DNS/TLS artifact. No `makeCredential`/`getAssertion`
invoked against real or simulated hardware. No `HardwareCredentialRecord`/
`Principal`/`Signer`/`DeploymentBinding` created in the real store. No
DNS/TLS provisioned. No HMIC-001 amendment. No hac-dell redeployment,
recertification, or SSH session opened this phase (unlike Phase
149O.20L.7O.2N.6's own read-only hac-dell inspection — this phase needed
no fresh hac-dell state, since RP-ID/origin/HTTPS selection depends only
on this repository's own frozen contract text and local source). No
HATP activation. No Permission Broker/runtime change.

Next phase: **independent verification of this architecture selection**
— re-derive HRWP-001/HRAC-001 dependency claims fresh, confirm every
rejected-alternative rationale holds, confirm the security-boundary and
challenge-flow diagrams introduce no contradiction with either frozen
contract, before any literal RP-ID/domain selection, real DNS-01
certificate issuance, reverse-proxy/VPN provisioning, or server/client
implementation begins.
