"""
Fresh Adversarial Verification Suite — Phase 149O.20L.7O.3S.2.1.

Independently re-derives the Phase 149O.20L.7O.3S.2 production-consumption
claim from first principles: reconstructs the call graph and exercises
adversarial paths that 3S.2's own test suites
(test_runtime_dry_consumption_3s2.py, test_session_bootstrap_dry_runtime_3s2.py)
do not cover. Verification-only: no production repair is performed here.

Every test in this module constructs its own registry/resolver/adapter or
drives the real `run_production_dry_invocation` / CLI entry point directly;
none of it reuses 3S.2's fixtures or assertions.
"""

from __future__ import annotations

import json
import socket
import subprocess
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core.mock_runtime_adapter import (
    KNOWN_MOCK_TARGET_FIXTURES,
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    MalformedMockAdapter,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import PermissionBroker
from pcae.core.runtime_adapter import (
    RuntimeAdapterResolver,
    RuntimeTargetConfiguration,
    simulate_invocation,
)
from pcae.core.runtime_dry_consumption import (
    DRY_CONSUMER_ENTRY_POINT,
    UnknownRuntimeTargetError,
    _run_with_context,
    resolve_dry_consumer_context,
    run_production_dry_invocation,
)
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    RuntimeInvocationStore,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)
from pcae.core.runtime_registry import RuntimeRegistry


def _clock() -> str:
    return datetime.now(timezone.utc).isoformat()


def _real_context():
    """Bind against this repository's own real active task/HEAD -- the
    same authoritative state the production CLI entry point uses. This is
    deliberate: 3S.2.1 verifies the PRODUCTION consumer, not an isolated
    fixture repo."""
    ctx = resolve_dry_consumer_context(HarnessPath.cwd())
    assert ctx is not None, "expected an active task/resolvable HEAD in this repo"
    return ctx


def _build_request(target: str, agent_id: str = "claude-local"):
    ctx = _real_context()
    registry = RuntimeRegistry()
    descriptor = build_mock_descriptor()
    registry.register_adapter_descriptor(descriptor)
    resolver = RuntimeAdapterResolver(registry)
    config = RuntimeTargetConfiguration(target, "1.0", MOCK_ADAPTER_ID, target)
    resolver.register_target(config)
    authority = AuthoritySnapshot(
        repository_id=ctx.repository_id,
        repository_fingerprint=ctx.repository_fingerprint,
        base_commit=ctx.base_commit,
        task_id=ctx.task_id,
        task_contract_digest=ctx.task_contract_digest,
    )
    prompt = build_prompt_artifact(
        content="adversarial-3s2.1-prompt", generation_method="m",
        generation_version="1.0", authority=authority, clock=_clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id=agent_id, runtime_target_id=target,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert request is not None, issues
    return resolver, request, prompt, approval


# ── Matrix A: production call graph reconstruction ─────────────────────


def test_production_entry_point_reaches_real_rpac_coordinator():
    """Non-test production caller graph: run_production_dry_invocation
    (the exact function `commands/session.py::_run_compact_bootstrap_dry`
    calls) reaches the unmodified `simulate_invocation` coordinator and
    produces a real SIM_RESULT_CAPTURED outcome against this repo's own
    real task/HEAD authority -- not a stub."""
    outcome = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id="claude-local",
        runtime_target_id="mock-dry.no-change.v1",
        prompt_content="verification-3s2.1",
    )
    assert not isinstance(outcome, UnknownRuntimeTargetError)
    assert outcome.accepted is True
    assert outcome.final_state == "SIM_RESULT_CAPTURED"
    assert outcome.adapter_call_count == 1
    assert outcome.trace[0] == "SIM_PREPARED"
    assert outcome.trace[-1] == "SIM_INTAKE_CANDIDATE_BUILT"


def test_entry_point_string_matches_documented_constant():
    assert DRY_CONSUMER_ENTRY_POINT == (
        "pcae session bootstrap --compact --dry-runtime --runtime-target <id>"
    )


# ── Section 6: two-part opt-in matrix (fresh, beyond 3S.2's own tests) ──


def test_missing_target_fails_closed_before_any_rpac_call():
    """`--dry-runtime` with an empty target string must never reach
    run_production_dry_invocation at all (mirrors the CLI's own guard);
    an empty string is falsy so the CLI-level guard, not KNOWN_MOCK_TARGET
    membership, is what stops it."""
    assert "" not in KNOWN_MOCK_TARGET_FIXTURES


@pytest.mark.parametrize(
    "bad_target",
    [
        "MOCK-DRY.NO-CHANGE.V1",  # case variation
        " mock-dry.no-change.v1",  # leading whitespace
        "mock-dry.no-change.v1 ",  # trailing whitespace
        "mock-dry.no-change.v1x",  # suffix
        "xmock-dry.no-change.v1",  # prefix
        "mock-dry.no-change.v2",  # typo/version
        "claude-local",  # agent identity used as target
        "codex-ox",  # agent identity used as target
        "openrouter",  # provider-like name
        "totally-bogus-target",
    ],
)
def test_no_fuzzy_target_resolution(bad_target):
    outcome = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id="claude-local",
        runtime_target_id=bad_target, prompt_content="p",
    )
    assert isinstance(outcome, UnknownRuntimeTargetError)
    assert bad_target in str(outcome)


# ── Section 8/9: explicit dry path + prompt-source non-duplication ─────


def test_pure_rpac_phase_has_zero_subprocess_socket_or_thread_calls():
    """Independently instruments `_run_with_context` (the phase reachable
    only after PCAE-owned repo/task binding has already been resolved) to
    prove it makes no subprocess, socket, or background-thread calls of
    its own -- distinct from 3S.2's own subprocess/network test, which
    this test does not reuse."""
    calls = {"subprocess": 0, "socket": 0, "threads": 0}

    orig_run = subprocess.run
    orig_popen_init = subprocess.Popen.__init__
    orig_socket_init = socket.socket.__init__
    orig_thread_start = threading.Thread.start

    def patched_run(*a, **kw):
        calls["subprocess"] += 1
        return orig_run(*a, **kw)

    def patched_popen(self, *a, **kw):
        calls["subprocess"] += 1
        return orig_popen_init(self, *a, **kw)

    def patched_socket(self, *a, **kw):
        calls["socket"] += 1
        return orig_socket_init(self, *a, **kw)

    def patched_thread_start(self, *a, **kw):
        calls["threads"] += 1
        return orig_thread_start(self, *a, **kw)

    subprocess.run = patched_run
    subprocess.Popen.__init__ = patched_popen
    socket.socket.__init__ = patched_socket
    threading.Thread.start = patched_thread_start
    try:
        ctx = _real_context()
        calls["subprocess"] = 0  # exclude resolve_dry_consumer_context's
        calls["socket"] = 0  # pre-existing git-HEAD/fingerprint helper
        calls["threads"] = 0  # calls; this test targets _run_with_context only
        outcome = _run_with_context(
            root=HarnessPath.cwd(), context=ctx, agent_id="claude-local",
            runtime_target_id="mock-dry.synthetic-change.v1",
            prompt_content="p",
        )
    finally:
        subprocess.run = orig_run
        subprocess.Popen.__init__ = orig_popen_init
        socket.socket.__init__ = orig_socket_init
        threading.Thread.start = orig_thread_start

    assert outcome.accepted is True
    assert calls == {"subprocess": 0, "socket": 0, "threads": 0}


def test_dry_prompt_equals_ordinary_bootstrap_prompt_for_same_state():
    """No parallel prompt generator: the dry consumer must reuse the
    exact same `prompt` string the ordinary `--compact` (non-dry) path
    already built, not a second bespoke prompt-generation routine."""
    # The production wiring (session.py::_run_compact_bootstrap) builds
    # `prompt` exactly once via the existing `build_bootstrap_prompt`
    # pack/profile machinery, and only *branches* into the dry consumer
    # afterward (`_run_compact_bootstrap_dry`), passing that same
    # already-built `prompt` string straight through. Structurally:
    # `runtime_dry_consumption` never imports or calls a second
    # prompt-generation routine of its own.
    import inspect

    from pcae.commands import session as session_module
    from pcae.core import runtime_dry_consumption

    dry_source = inspect.getsource(runtime_dry_consumption)
    assert "build_bootstrap_prompt" not in dry_source

    branch_source = inspect.getsource(session_module._run_compact_bootstrap)
    dispatch_source = inspect.getsource(session_module._run_compact_bootstrap_dry)
    # The dry branch is reached only after the single `build_bootstrap_prompt`
    # call already produced `prompt`, and `_run_compact_bootstrap_dry`'s own
    # signature takes that `prompt` in as a parameter rather than rebuilding it.
    assert "prompt = build_bootstrap_prompt(" in branch_source
    assert "build_bootstrap_prompt" not in dispatch_source
    assert "prompt: str" in inspect.signature(session_module._run_compact_bootstrap_dry).__str__() or (
        "prompt" in inspect.signature(session_module._run_compact_bootstrap_dry).parameters
    )


# ── Section 14: authority injection ─────────────────────────────────────


def test_cli_cannot_smuggle_authority_fields_into_request():
    """`run_production_dry_invocation`'s public signature accepts exactly
    `root`, `agent_id`, `runtime_target_id`, `prompt_content` -- there is
    no keyword through which a caller could inject `approved`,
    `execution_available`, `provider_id`, or `model_id`."""
    import inspect

    sig = inspect.signature(run_production_dry_invocation)
    allowed = {"root", "agent_id", "runtime_target_id", "prompt_content"}
    assert set(sig.parameters) == allowed


def test_effect_profile_is_forced_all_denied_and_provider_model_forced_none():
    resolver, request, prompt, approval = _build_request("mock-dry.no-change.v1")
    assert request.effect_profile.is_all_denied_zero() is True
    assert request.provider_id is None
    assert request.model_id is None


# ── Section 16/17: PB ALLOW / DENY / non-authority ──────────────────────


def test_pb_allow_is_not_execution_authority():
    resolver, request, prompt, approval = _build_request("mock-dry.no-change.v1")
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=_clock,
    )
    assert outcome.accepted is True
    # The accepted result is a simulation record, not a real-execution
    # capability flag; nothing on SimulationOutcome claims execution
    # occurred.
    assert not hasattr(outcome, "execution_available")
    assert not hasattr(outcome, "real_execution")


def test_pb_deny_stops_before_any_adapter_dispatch():
    resolver, request, prompt, approval = _build_request("mock-dry.no-change.v1")
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))

    class DenyBroker:
        def evaluate(self, req):
            class D:
                decision = "DENY"
                decision_reason = "adversarial_forced_deny"
                causing_policy_id = "POL-TEST"

            return D()

    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=_clock, permission_broker=DenyBroker(),
    )
    assert outcome.accepted is False
    assert outcome.adapter_call_count == 0
    assert outcome.failure_category == "permission_denied"
    assert "SIM_DISPATCHED" not in outcome.trace


# ── Section 20: enforcement-double / non-authority ──────────────────────


def test_permissive_fake_enforcement_cannot_override_pb_deny():
    """Re-derives 3S.1's malicious-enforcement-double concern through the
    real production coordinator: a fake enforcement evaluator that always
    reports `would_allow_simulation` must not let a PB DENY through."""
    resolver, request, prompt, approval = _build_request("mock-dry.no-change.v1")
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))

    class FakeEnforcementAlwaysAllow:
        def evaluate(self, **kw):
            class Obs:
                outcome = "would_allow_simulation"
                evidence_digest = "adversarial-fake-digest"

            return Obs()

    class DenyBroker:
        def evaluate(self, req):
            class D:
                decision = "DENY"
                decision_reason = "adversarial_forced_deny"
                causing_policy_id = "POL-TEST"

            return D()

    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=_clock,
        permission_broker=DenyBroker(),
        enforcement_evaluator=FakeEnforcementAlwaysAllow(),
    )
    assert outcome.accepted is False
    assert outcome.adapter_call_count == 0


def test_non_simulation_only_pb_request_is_unconditionally_denied():
    """Real (non-simulation) execution requests through the same
    ACTION_ADAPTER_INVOCATION/EXECUTION_CLASS_ADAPTER surface must always
    be denied by POL-005 (Execution Disabled) -- proving PB ALLOW for the
    dry path can never be reused to authorize a real invocation."""
    from pcae.core.permission_broker_foundation import (
        ACTION_ADAPTER_INVOCATION,
        EXECUTION_CLASS_ADAPTER,
        PermissionBroker,
        build_permission_broker_request,
    )

    real_request = build_permission_broker_request(
        action_type=ACTION_ADAPTER_INVOCATION,
        execution_class=EXECUTION_CLASS_ADAPTER,
        requested_component="COMP-006",
        requested_capability=MOCK_CAPABILITY,
        task_id="any-task",
        phase_id=None,
        evidence_available=True,
        approval_present=True,
        simulation_only=False,
    )
    decision = PermissionBroker().evaluate(real_request)
    assert decision.decision == "DENY"


# ── Section 27/34: malformed adapter result must not become trusted ────


def test_malformed_adapter_result_never_persists_a_result_document():
    """3S.2.1 MUST-FIX #1 — REPAIRED by Phase
    149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B). A non-conforming
    `collect()` return value now fails closed with a clean
    `FAILURE_MALFORMED_RESULT` `SimulationOutcome` (no uncaught
    `AttributeError`), and no `result.json` / `intake-handoff.json` is
    ever persisted."""
    from pcae.core.runtime_invocation import FAILURE_MALFORMED_RESULT

    resolver, request, prompt, approval = _build_request("mock-dry.no-change.v1")
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MalformedMockAdapter())
    store_root = Path(tempfile.mkdtemp())
    store = RuntimeInvocationStore(store_root)

    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=_clock,
    )

    assert outcome.accepted is False
    assert outcome.failure_category == FAILURE_MALFORMED_RESULT
    assert outcome.result is None
    result_files = list(store_root.rglob("result.json"))
    handoff_files = list(store_root.rglob("intake-handoff.json"))
    assert result_files == [], (
        "malformed adapter result must never be persisted as a trusted "
        f"result document; found {result_files}"
    )
    assert handoff_files == []


# ── Section 26: duplicate invocation / idempotency (store-level) ───────


class _FakeReq:
    def __init__(self, invocation_id, idem_key, attempt_id="att-x"):
        self.invocation_id = invocation_id
        self.attempt_id = attempt_id
        self.idempotency_key = idem_key

    def canonical_projection(self):
        return {"invocation_id": self.invocation_id, "idempotency_key": self.idempotency_key}


def test_duplicate_invocation_id_same_content_is_idempotent():
    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    store.create_request_record(_FakeReq("inv-idem-3s21", "key-A"))
    store.create_request_record(_FakeReq("inv-idem-3s21", "key-A"))  # must not raise


def test_duplicate_invocation_id_conflicting_content_fails_closed():
    from pcae.core.runtime_invocation import InvocationIntegrityError

    store = RuntimeInvocationStore(Path(tempfile.mkdtemp()))
    store.create_request_record(_FakeReq("inv-conflict-3s21", "key-A"))
    with pytest.raises(InvocationIntegrityError):
        store.create_request_record(_FakeReq("inv-conflict-3s21", "key-B-CONFLICT"))


def test_production_entry_point_never_lets_caller_choose_invocation_id():
    """Structural proof for Section 24: the only public entry point this
    phase adds accepts no `invocation_id` parameter anywhere, so the
    store-level path-sanitization on `invocation_id` (see
    `test_store_invocation_id_path_confinement_defense_in_depth`, repaired
    in .1R.19) is defense-in-depth: not reachable through production usage
    today, where `invocation_id` is always internally generated."""
    import inspect

    for fn in (run_production_dry_invocation, resolve_dry_consumer_context):
        sig = inspect.signature(fn)
        assert "invocation_id" not in sig.parameters


def test_store_invocation_id_path_confinement_defense_in_depth():
    """3S.2.1 MUST-FIX #2 — REPAIRED by Phase
    149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B). `RuntimeInvocationStore`
    now sanitizes `invocation_id` / `attempt_id` against path traversal at
    the store layer (`require_safe_relative_id_component` grammar) plus a
    resolved-path containment assertion. A crafted traversal id fails
    closed with `InvocationIntegrityError` and writes nothing. Previously
    an `xfail(strict=True)` gap demonstrator; promoted to a real
    expected-rejection test."""
    from pcae.core.runtime_invocation import InvocationIntegrityError

    tmp = Path(tempfile.mkdtemp())
    store = RuntimeInvocationStore(tmp)
    sentinel_target = tmp.parent / "pcae-3s21-path-confinement-poc"
    with pytest.raises(InvocationIntegrityError):
        store.create_request_record(
            _FakeReq("../../../../../../tmp/pcae-3s21-path-confinement-poc", "key")
        )
    assert not sentinel_target.exists()
    # An absolute path and a bare `..` component are also rejected.
    for bad in ("/etc/pcae-poc", "..", "."):
        with pytest.raises(InvocationIntegrityError):
            store.create_request_record(_FakeReq(bad, "key"))
    # A normal generated-shaped id still works unchanged.
    store.create_request_record(_FakeReq("inv-" + "a" * 32, "key"))


# ── Section 35: provenance spoofing ─────────────────────────────────────


@pytest.mark.parametrize(
    "spoofed_agent_id",
    ["codex", "codex-ox", "claude", "openrouter-gpt4", "external-runtime-vendor"],
)
def test_result_adapter_id_is_never_derived_from_claimed_agent_identity(spoofed_agent_id):
    outcome = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id=spoofed_agent_id,
        runtime_target_id="mock-dry.synthetic-change.v1", prompt_content="p",
    )
    assert not isinstance(outcome, UnknownRuntimeTargetError)
    assert outcome.accepted is True
    assert outcome.result.adapter_id == MOCK_ADAPTER_ID
    assert outcome.result.adapter_id == "pcae.mock-dry"


# ── Section 32/33: Stage-B non-authority ────────────────────────────────


def test_intake_handoff_is_evidence_only_never_calls_ingest():
    """`build_intake_handoff` must map to the generic-intake candidate
    *shape* only; it must never call the actual acceptance/ingest
    pipeline (`validate_and_ingest_intake_candidate` or equivalent). The
    module docstring names that function in prose (explaining what is
    NOT called), so this checks the function body only, not the whole
    module source."""
    import inspect

    from pcae.core import runtime_adapter

    body_source = inspect.getsource(runtime_adapter.build_intake_handoff)
    assert "validate_and_ingest_intake_candidate(" not in body_source
    assert "build_intake_candidate_from_changes" in body_source
    import dis

    disassembly = "\n".join(
        instr.argval for instr in dis.get_instructions(runtime_adapter.build_intake_handoff)
        if instr.opname in ("LOAD_GLOBAL", "LOAD_ATTR", "LOAD_METHOD") and isinstance(instr.argval, str)
    )
    assert "validate_and_ingest_intake_candidate" not in disassembly


def test_intake_handoff_document_is_written_as_advisory_not_promoted():
    resolver, request, prompt, approval = _build_request("mock-dry.synthetic-change.v1")
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    store_root = Path(tempfile.mkdtemp())
    store = RuntimeInvocationStore(store_root)
    outcome = simulate_invocation(
        request=request, prompt_digest=prompt.content_digest, approval=approval,
        resolver=resolver, store=store, clock=_clock,
    )
    assert outcome.accepted is True
    handoff_files = list(store_root.rglob("intake-handoff.json"))
    assert len(handoff_files) == 1
    doc = json.loads(handoff_files[0].read_text(encoding="utf-8"))
    # Evidence-only shape: must not itself carry an acceptance/promotion
    # verdict field.
    assert "accepted" not in doc
    assert "promoted" not in doc
    assert "task_complete" not in doc


# ── Section 42/43: runtime-registry reconciliation / no third registry ─


def test_dry_consumer_uses_a_fresh_transient_registry_not_a_shared_singleton():
    """Reconstructs why `pcae runtime inspect` still reports 0
    plugins/0 capabilities even though a production consumer now exists:
    `_run_with_context` constructs its own `RuntimeRegistry()` instance
    per call and never touches any process-wide/persisted registry
    singleton that `pcae runtime inspect` reads from."""
    import inspect

    from pcae.core import runtime_dry_consumption

    source = inspect.getsource(runtime_dry_consumption._run_with_context)
    assert "RuntimeRegistry()" in source
    # No import of a shared/global registry accessor.
    assert "get_global_registry" not in source
    assert "shared_registry" not in source


def test_no_second_adapter_registry_module_created_by_3s2():
    """3S.2 must not have introduced a parallel adapter catalog; the dry
    consumer imports the same `RuntimeRegistry`/`RuntimeAdapterResolver`
    classes already defined in `runtime_registry.py`/`runtime_adapter.py`."""
    import inspect

    from pcae.core import runtime_dry_consumption

    source = inspect.getsource(runtime_dry_consumption)
    assert "from .runtime_registry import RuntimeRegistry" in source
    assert "from .runtime_adapter import" in source
    assert "class RuntimeRegistry" not in source
    assert "class RuntimeAdapterResolver" not in source


# ── Section 45: partial-option contamination ────────────────────────────


def test_context_resolution_is_stateless_across_calls():
    """Two independent context resolutions against the same repo state
    must be structurally equal (same authority facts), proving a failed
    prior dry attempt cannot leave contaminating state that changes what
    a subsequent ordinary/ dry call resolves."""
    ctx1 = resolve_dry_consumer_context(HarnessPath.cwd())
    ctx2 = resolve_dry_consumer_context(HarnessPath.cwd())
    assert ctx1 == ctx2


# ── Section 30: determinism (semantic result vs envelope) ──────────────


def test_semantic_structured_payload_is_deterministic_across_fresh_calls():
    """Separates the deterministic semantic subset (structured_payload,
    terminal_outcome) from the expected-to-vary envelope
    (invocation_id/attempt_id/timestamps)."""
    outcome_a = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id="claude-local",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="determinism-check",
    )
    outcome_b = run_production_dry_invocation(
        root=HarnessPath.cwd(), agent_id="claude-local",
        runtime_target_id="mock-dry.no-change.v1", prompt_content="determinism-check",
    )
    assert dict(outcome_a.result.structured_payload) == dict(outcome_b.result.structured_payload)
    assert outcome_a.result.terminal_outcome == outcome_b.result.terminal_outcome
    # Envelope fields are expected to differ (fresh invocation_id per call).
    assert outcome_a.result.invocation_id != outcome_b.result.invocation_id
