"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.4 — Gate-8 Process Containment
(Shell Gate) Coordinator Integration Implementation.

Focused defensive tests for
``runtime_dispatch_gate8.run_gate8_process_containment`` (the frozen Gate-8
owner), ``Gate8Result``, ``is_gate8_result``, ``Gate8EffectPlan`` and
``ResolvedExecutable``. Constructed from the primary contracts (RDGO-001
v3.0 §9 / §1 row 8 / §10 item 8 / §13 / §15 / §19, PBRD-001 v2.0 §6 / §14,
the mature 88P ``shell_gate`` classifier vocabulary, the ``.1R.13.1``
planning document §5 / §11 / §12 / §16 / §25) and current production
source — not from a report or from test names.

The deterministic HPAC mechanism is permanently NON-REAL and, per
``.1R.13.2`` / ``.1R.13.3``, Gate 7 always returns
``Gate7Result(decision="DENY")`` under the current runtime posture. **There
is no legitimate positive production Gate-8 path**: every real call fails
closed at the ``gate8_untrusted_gate7_result`` /
``gate8_gate7_decision_not_allow`` hard stop. To exercise the Gate-8
establishment envelope WITHOUT manufacturing real authority or a positive
``Gate7Result``, a small number of tests install a **test-boundary
substitution** for the provenance predicates only (``monkeypatch`` on
``runtime_dispatch_gate7.is_gate7_result`` /
``runtime_dispatch_gate5.is_gate5_result`` and, where the freshness
re-resolution is not under test, the projection-trust predicates in the
``runtime_dispatch_gate8`` namespace). This substitutes exactly the gates a
real FIDO2/UI ceremony + a real PB ALLOW + a real Gate-7 ALLOW would
satisfy; it manufactures no ``ValidatedAuthorityProjection``, no approval,
no runtime capability, and no positive ``Gate7Result``. The Shell Gate
classifier is the real one and is proven non-effecting for the inputs used.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import pickle
import subprocess
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5
from pcae.core import runtime_dispatch_gate7 as gate7

_REAL_IS_GATE7_RESULT = gate7.is_gate7_result
from pcae.core import runtime_dispatch_gate8 as g8
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri
from pcae.core import shell_gate as sg

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity

REPO_ROOT = Path(__file__).resolve().parents[1]
G8_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate8.py"
G8_SRC = G8_PATH.read_text()
PHASE_ENTRY_BASELINE = "6a9d650f54fb7a5c02652180f0bbcc3a41080198"
_1R15_4_SCOPE_END = "4d480553"  # end of .1R.15.3; .1R.15.4 (Contract Normalization) is the later authorized change
NOW = "2026-08-29T00:30:00Z"

_ECHO = "/bin/echo"


def _sha256_file(path: str) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            d.update(chunk)
    return d.hexdigest()


# ═══════════════════════════════════════════════════════════════════════
# Test-boundary fixtures — clearly labelled; no real authority, no
# real runtime capability, no positive Gate7Result (see module docstring).
# ═══════════════════════════════════════════════════════════════════════
class _SyntheticProjection:
    def __init__(self, *, subject_scope_binding_digest: str):
        self.subject_scope_binding_digest = subject_scope_binding_digest
        self.freshness_verdict_digest = "f" * 64

    def evidence_digest(self) -> str:
        return "e" * 64


def _synthetic_gate5_result(*, invocation_id: str, projection) -> gate5.Gate5Result:
    obj = object.__new__(gate5.Gate5Result)
    for name, value in (
        ("_projection", projection),
        ("sequence3_event_digest", "d" * 64),
        ("proof_id", "proof-x"),
        ("approval_id", "ria-" + "0" * 32),
        ("invocation_id", invocation_id),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _synthetic_gate7_result(
    *, decision: str, invocation_id: str, attempt_id: str
) -> gate7.Gate7Result:
    obj = object.__new__(gate7.Gate7Result)
    for name, value in (
        ("decision", decision),
        ("matched_no_go_ids", () if decision == "ALLOW" else ("RE-NOGO-002",)),
        ("causing_reason_ids", () if decision == "ALLOW" else ("gate7_runtime_execution_unavailable",)),
        ("invocation_id", invocation_id),
        ("attempt_id", attempt_id),
        ("request_id", "pbr-" + "0" * 12),
        ("pb_decision_digest", "a" * 64),
        ("authority_freshness_digest", "b" * 64),
        ("evaluated_input_digest", "c" * 64),
        ("runtime_posture_digest", "9" * 64),
        ("expires_at", NOW),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, name, value)
    return obj


def _good_effect_plan(**overrides) -> g8.Gate8EffectPlan:
    base = dict(
        executable_path=_ECHO,
        argv=("runtime-dispatch-preflight",),
        cwd=str(REPO_ROOT),
        env_allowlist=("PATH", "HOME"),
        child_process_policy="prohibited",
        resource_limit_ref="budget-1",
        time_limit_ref="timeout-30s",
        supervision_ref="supervisor-1",
        network_denied=True,
        credentials_required=False,
    )
    base.update(overrides)
    return g8.Gate8EffectPlan(**base)


def _resolver(**overrides):
    def resolve(inputs):
        adapter = inputs.adapter_descriptor_binding
        fields = dict(
            path=_ECHO,
            sha256=_sha256_file(_ECHO),
            version="1.0",
            descriptor_digest=adapter.descriptor_digest,
            target_config_digest=adapter.target_config_digest,
            runtime_target_id=inputs.runtime_target_id,
            installed=True,
        )
        fields.update(overrides)
        return g8.ResolvedExecutable(**fields)

    return resolve


@pytest.fixture
def chain(monkeypatch):
    """A trusted (substituted-provenance) Gate-7 ALLOW + Gate-5 result bound
    to one real identity/inputs, with projection trust + revalidation also
    substituted (not under test in cases that use this fixture)."""
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    expected = rdp._expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    projection = _SyntheticProjection(subject_scope_binding_digest=expected)
    g7 = _synthetic_gate7_result(
        decision="ALLOW",
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
    )
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)

    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is g7)
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: c is g5)
    monkeypatch.setattr(g8, "is_trusted_validated_authority_projection", lambda p: p is projection)
    monkeypatch.setattr(
        g8, "revalidate_validated_authority_projection", lambda p, *, current_time: p is projection
    )
    return dict(inputs=inputs, identity=identity, g7=g7, g5=g5, projection=projection)


def _run(chain, **overrides):
    g7 = overrides.pop("gate7_result", chain["g7"])
    kw = dict(
        gate5_result=chain["g5"],
        identity=chain["identity"],
        inputs=chain["inputs"],
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=overrides.pop("effect_plan", _good_effect_plan()),
        descriptor_resolver=overrides.pop("descriptor_resolver", _resolver()),
    )
    kw.update(overrides)
    return g8.run_gate8_process_containment(g7, **kw)


# ═══════════════════════════════════════════════════════════════════════
# 1. Gate7Result provenance — only the exact registry object
# ═══════════════════════════════════════════════════════════════════════
def test_none_gate7_result_fails_closed():
    r, reasons = g8.run_gate8_process_containment(
        None,
        gate5_result=None,
        identity=object(),
        inputs=object(),
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(),
    )
    assert r is None and reasons == ("gate8_untrusted_gate7_result",)


def test_caller_constructed_gate7_result_rejected():
    forged = object.__new__(gate7.Gate7Result)
    for n in gate7.Gate7Result.__slots__:
        try:
            object.__setattr__(forged, n, "ALLOW" if n == "decision" else None)
        except AttributeError:
            pass
    r, reasons = _bare_run(forged)
    assert r is None and reasons == ("gate8_untrusted_gate7_result",)


def test_copied_reconstructed_serialized_gate7_result_rejected():
    with pytest.raises(TypeError):
        pickle.dumps(object.__new__(gate7.Gate7Result))
    fake = object.__new__(gate7.Gate7Result)
    object.__setattr__(fake, "decision", "ALLOW")
    with pytest.raises(TypeError):
        copy.deepcopy(fake)
    r, reasons = _bare_run(fake)
    assert r is None and reasons == ("gate8_untrusted_gate7_result",)


def test_real_negative_gate7_result_is_not_trusted_by_shape(chain, monkeypatch):
    # A genuine registry Gate7Result(DENY) — produced by the real coordinator
    # under the current posture — is rejected at the decision gate, never by
    # is_gate7_result being fooled by shape.
    monkeypatch.setattr(gate7, "is_gate7_result", _REAL_IS_GATE7_RESULT)  # real predicate
    real_deny = _drive_real_negative_gate7(chain)
    assert _REAL_IS_GATE7_RESULT(real_deny) is True
    assert real_deny.decision == "DENY"
    r, reasons = _run(chain, gate7_result=real_deny)
    assert r is None and reasons == ("gate8_gate7_decision_not_allow",)


def _bare_run(g7):
    return g8.run_gate8_process_containment(
        g7,
        gate5_result=None,
        identity=object(),
        inputs=object(),
        authority_current_time=NOW,
        repo_root=REPO_ROOT,
        effect_plan=_good_effect_plan(),
        descriptor_resolver=_resolver(),
    )


def _drive_real_negative_gate7(chain):
    """Reach the real Gate-7 coordinator's negative branch via the same
    labelled provenance substitution the .1R.13.2/.1R.13.3 suites use — it
    still returns DENY because the real runtime posture is unchanged."""
    inputs = chain["inputs"]
    identity = chain["identity"]
    projection = chain["projection"]
    g6 = object.__new__(rdp.Gate6Decision)

    class _PB:
        decision = "ALLOW"
        decision_reason = "would-allow"
        causing_policy_ids = ()
        matched_no_go_ids = ()
        requires_human = False
        simulation_only = False
        implementation_status = "execution_unavailable"

    for name, value in (
        ("_pb_decision", _PB()),
        ("decision", "ALLOW"),
        ("decision_reason", "synthetic"),
        ("approval_present", True),
        ("invocation_id", identity.invocation_id),
        ("attempt_id", identity.attempt_id),
        ("request_id", "pbr-" + "0" * 12),
        ("causing_policy_ids", ()),
        ("matched_no_go_ids", ()),
        ("requires_human", False),
        ("simulation_only", False),
        ("evaluated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(g6, name, value)
    g5 = _synthetic_gate5_result(invocation_id=identity.invocation_id, projection=projection)
    import unittest.mock as _m

    with _m.patch.object(rdp, "is_gate6_decision", lambda c: c is g6), _m.patch.object(
        gate5, "is_gate5_result", lambda c: c is g5
    ), _m.patch.object(
        gate7, "is_trusted_validated_authority_projection", lambda p: p is projection
    ), _m.patch.object(
        gate7, "revalidate_validated_authority_projection", lambda p, *, current_time: True
    ):
        result, _reasons = gate7.run_gate7_runtime_enforcement(
            g6, gate5_result=g5, identity=identity, inputs=inputs, authority_current_time=NOW
        )
    assert result is not None and result.decision == "DENY"
    return result


# ═══════════════════════════════════════════════════════════════════════
# 2. Trusted provenance is NOT enough — decision must be exactly "ALLOW"
# ═══════════════════════════════════════════════════════════════════════
def test_trusted_gate7_deny_rejected_before_shell_gate(chain, monkeypatch):
    called = []
    monkeypatch.setattr(sg, "build_shell_gate", lambda *a, **k: called.append(1) or {})
    deny = _synthetic_gate7_result(
        decision="DENY",
        invocation_id=chain["identity"].invocation_id,
        attempt_id=chain["identity"].attempt_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is deny)
    r, reasons = _run(chain, gate7_result=deny)
    assert r is None and reasons == ("gate8_gate7_decision_not_allow",)
    assert called == []  # Shell Gate never evaluated


def test_unknown_gate7_decision_value_fails_closed(chain, monkeypatch):
    weird = _synthetic_gate7_result(
        decision="MAYBE",
        invocation_id=chain["identity"].invocation_id,
        attempt_id=chain["identity"].attempt_id,
    )
    monkeypatch.setattr(gate7, "is_gate7_result", lambda c: c is weird)
    r, reasons = _run(chain, gate7_result=weird)
    assert r is None and reasons == ("gate8_gate7_decision_not_allow",)


def test_is_gate8_result_means_provenance_not_containment(chain):
    # A structural establishment that fails still returns a registry
    # Gate8Result; is_gate8_result -> True is provenance ONLY.
    r, reasons = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r is not None and g8.is_gate8_result(r) is True
    assert r.containment_established is False
    assert "gate8_executable_not_installed" in r.causing_reason_ids


# ═══════════════════════════════════════════════════════════════════════
# 3. Gate5Result provenance + exact invocation binding
# ═══════════════════════════════════════════════════════════════════════
def test_forged_gate5_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(gate5, "is_gate5_result", lambda c: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_untrusted_gate5_result",)


def test_invocation_id_substitution_rejected(chain):
    other_g7 = _synthetic_gate7_result(
        decision="ALLOW", invocation_id="inv-" + "9" * 32, attempt_id=chain["identity"].attempt_id
    )
    # need is_gate7_result to vouch for the substituted object
    import unittest.mock as _m

    with _m.patch.object(gate7, "is_gate7_result", lambda c: c is other_g7):
        r, reasons = _run(chain, gate7_result=other_g7)
    assert r is None and reasons == ("gate8_invocation_binding_mismatch",)


def test_attempt_id_substitution_rejected(chain):
    other_g7 = _synthetic_gate7_result(
        decision="ALLOW",
        invocation_id=chain["identity"].invocation_id,
        attempt_id="att-" + "9" * 32,
    )
    import unittest.mock as _m

    with _m.patch.object(gate7, "is_gate7_result", lambda c: c is other_g7):
        r, reasons = _run(chain, gate7_result=other_g7)
    assert r is None and reasons == ("gate8_invocation_binding_mismatch",)


# ═══════════════════════════════════════════════════════════════════════
# 4. Structural input guards + local-CLI-v1 representability
# ═══════════════════════════════════════════════════════════════════════
def test_wrong_identity_type_fails_closed(chain):
    r, reasons = _run(chain, identity=object())
    assert r is None and reasons == ("gate8_invalid_identity",)


def test_wrong_inputs_type_fails_closed(chain):
    r, reasons = _run(chain, inputs=object())
    assert r is None and reasons == ("gate8_invalid_construction_input",)


def test_bad_authority_current_time_fails_closed(chain):
    r, reasons = _run(chain, authority_current_time="  ")
    assert r is None and reasons == ("gate8_invalid_authority_current_time",)


def test_bad_repo_root_fails_closed(chain):
    r, reasons = _run(chain, repo_root=str(REPO_ROOT))
    assert r is None and reasons == ("gate8_invalid_repo_root",)


def test_bad_effect_plan_type_fails_closed(chain):
    r, reasons = _run(chain, effect_plan=object())
    assert r is None and reasons == ("gate8_invalid_effect_plan",)


def test_non_callable_descriptor_resolver_fails_closed(chain):
    r, reasons = _run(chain, descriptor_resolver=object())
    assert r is None and reasons == ("gate8_invalid_descriptor_resolver",)


def test_non_local_cli_effect_class_rejected(chain):
    from dataclasses import replace

    bad_inputs = replace(chain["inputs"], effect_class="unbounded_remote_dispatch")
    # the canonical construction re-check (_validate_construction_inputs)
    # rejects a non-local-CLI effect class first, fail-closed.
    r, reasons = _run(chain, inputs=bad_inputs)
    assert r is None
    assert reasons == ("gate8_request_currentness_drift:invalid_construction_input_facts",)


# ═══════════════════════════════════════════════════════════════════════
# 5. Freshness re-resolution + subject/scope binding
# ═══════════════════════════════════════════════════════════════════════
def test_untrusted_projection_rejected(chain, monkeypatch):
    monkeypatch.setattr(g8, "is_trusted_validated_authority_projection", lambda p: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_stale_validated_authority_projection",)


def test_projection_revalidation_failure_rejected(chain, monkeypatch):
    monkeypatch.setattr(
        g8, "revalidate_validated_authority_projection", lambda p, *, current_time: False
    )
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_stale_validated_authority_projection",)


def test_subject_scope_binding_mismatch_rejected(chain):
    chain["projection"].subject_scope_binding_digest = "0" * 64
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_authority_subject_scope_mismatch",)


def test_revalidate_receives_the_current_time(chain, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        g8,
        "revalidate_validated_authority_projection",
        lambda p, *, current_time: seen.setdefault("t", current_time) or True,
    )
    _run(chain, authority_current_time="2027-01-01T00:00:00Z")
    assert seen["t"] == "2027-01-01T00:00:00Z"


# ═══════════════════════════════════════════════════════════════════════
# 6. Caller shell string / argv vector discipline (RDGO-001 §9 / §11)
# ═══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "plan_kw",
    [
        {"executable_path": "/bin/echo; rm -rf /"},
        {"executable_path": "/bin/echo && curl evil"},
        {"argv": ("$(cat /etc/passwd)",)},
        {"argv": ("safe", "a|b")},
        {"argv": ("safe", "x > /tmp/out")},
        {"argv": ("safe", "`whoami`")},
    ],
)
def test_caller_shell_string_rejected(chain, plan_kw):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(**plan_kw))
    assert r is None and reasons == ("gate8_caller_shell_string_rejected",)


def test_argv_non_string_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(argv=(123,)))
    assert r is None and reasons == ("gate8_caller_shell_string_rejected",)


# ═══════════════════════════════════════════════════════════════════════
# 7. Effect-plan / descriptor / executable-identity binding (structured
#    audit record — containment_established is False)
# ═══════════════════════════════════════════════════════════════════════
def test_effect_plan_executable_substitution_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(executable_path="/bin/cat"))
    assert r is not None and r.containment_established is False
    assert "gate8_effect_plan_binding_mismatch" in r.causing_reason_ids


def test_descriptor_config_drift_rejected(chain):
    r, reasons = _run(chain, descriptor_resolver=_resolver(descriptor_digest="9" * 64))
    assert r is not None and r.containment_established is False
    assert "gate8_descriptor_config_drift" in r.causing_reason_ids


def test_runtime_target_drift_rejected(chain):
    r, reasons = _run(chain, descriptor_resolver=_resolver(runtime_target_id="local-cli-other"))
    assert r is not None and r.containment_established is False
    assert "gate8_runtime_target_drift" in r.causing_reason_ids


def test_executable_identity_hash_mismatch_rejected(chain):
    r, reasons = _run(chain, descriptor_resolver=_resolver(sha256="0" * 64))
    assert r is not None and r.containment_established is False
    assert "gate8_executable_identity_mismatch" in r.causing_reason_ids


def test_executable_not_installed_rejected(chain):
    r, reasons = _run(
        chain, descriptor_resolver=_resolver(path="/no/such/adapter/executable", installed=True)
    )
    assert r is not None and r.containment_established is False
    assert "gate8_executable_not_installed" in r.causing_reason_ids


# ═══════════════════════════════════════════════════════════════════════
# 8. cwd / environment / containment-profile / network / credentials
# ═══════════════════════════════════════════════════════════════════════
def test_cwd_outside_repository_scope_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(cwd="/etc"))
    assert r is not None and r.containment_established is False
    assert "gate8_cwd_outside_repository_scope" in r.causing_reason_ids


def test_environment_not_allowlisted_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(env_allowlist=("PATH", "  ")))
    assert r is not None and r.containment_established is False
    assert "gate8_environment_not_allowlisted" in r.causing_reason_ids


def test_bad_child_process_policy_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(child_process_policy="unrestricted"))
    assert r is not None and r.containment_established is False
    assert "gate8_containment_profile_invalid" in r.causing_reason_ids


def test_network_not_deniable_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(network_denied=False))
    assert r is not None and r.containment_established is False
    assert "gate8_network_not_deniable" in r.causing_reason_ids


def test_credentials_required_rejected(chain):
    r, reasons = _run(chain, effect_plan=_good_effect_plan(credentials_required=True))
    assert r is not None and r.containment_established is False
    assert "gate8_credentials_required" in r.causing_reason_ids


# ═══════════════════════════════════════════════════════════════════════
# 9. Shell Gate classifier — canonical existing implementation, no effect
# ═══════════════════════════════════════════════════════════════════════
def test_shell_gate_classifier_is_the_canonical_existing_one(chain):
    assert "from pcae.core.shell_gate import build_shell_gate" in G8_SRC
    # Gate 8 does not re-implement classification — no category regex table.
    assert "_classify_command" not in G8_SRC and "SGP_CATEGORIES" not in G8_SRC


def test_shell_gate_call_has_no_external_effect(chain, monkeypatch):
    seen = {}
    real = sg.build_shell_gate

    def spy(repo_root, command_text):
        seen["command_text"] = command_text
        return real(repo_root, command_text)

    monkeypatch.setattr(sg, "build_shell_gate", spy)
    # forbid any subprocess from the shell_gate path during this call
    monkeypatch.setattr(
        sg, "_call_doctor_test_run", lambda *a, **k: pytest.fail("shell_gate spawned a subprocess")
    )
    _run(chain)
    assert seen["command_text"] == "/bin/echo runtime-dispatch-preflight"


def test_shell_gate_category_denied_fails_closed(chain):
    # `rm` classifies as destructive_filesystem -> hard block.
    r, reasons = _run(
        chain,
        descriptor_resolver=_resolver(path="/bin/rm", sha256=_sha256_file("/bin/rm")),
        effect_plan=_good_effect_plan(executable_path="/bin/rm", argv=("build-artifact",)),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_category_denied" in r.causing_reason_ids


def test_shell_gate_internal_error_fails_closed(chain, monkeypatch):
    monkeypatch.setattr(sg, "build_shell_gate", lambda *a, **k: (_ for _ in ()).throw(RuntimeError()))
    r, reasons = _run(chain)
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_internal_error" in r.causing_reason_ids


def test_pytest_effect_plan_refused_before_shell_gate(chain, monkeypatch):
    called = []
    monkeypatch.setattr(sg, "build_shell_gate", lambda *a, **k: called.append(1) or {})
    r, reasons = _run(
        chain,
        descriptor_resolver=_resolver(path="/usr/bin/pytest"),
        effect_plan=_good_effect_plan(executable_path="/usr/bin/pytest", argv=("-q",)),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_preflight_side_effect_refused" in r.causing_reason_ids
    assert called == []


# ═══════════════════════════════════════════════════════════════════════
# 10. Structural positive containment branch (test-only; clearly separate
#     from production reachability)
# ═══════════════════════════════════════════════════════════════════════
def test_structural_containment_can_be_established_via_test_boundary(chain):
    r, reasons = _run(chain)
    assert r is not None and g8.is_gate8_result(r) is True
    assert r.containment_established is True
    assert reasons == ()
    assert r.shell_gate_decision == "allow_read_only"
    assert r.containment_evidence_digest and r.live_preflight_digest
    assert r.invocation_id == chain["identity"].invocation_id


def test_production_path_never_reaches_containment_establishment():
    # The real chain: run_gate5 returns nothing on the deterministic fixture,
    # so no Gate5Result -> no Gate6Decision -> no Gate7Result exists to hand
    # to Gate 8. And a real Gate7Result is always DENY. Either way Gate 8
    # stops before containment.
    from _rdw3w_helpers import full_chain

    _approval, projection, _request, decision = full_chain(simulation_only=False)
    assert projection is None  # NON-REAL hard stop upstream


# ═══════════════════════════════════════════════════════════════════════
# 11. Gate8Result model — ephemeral, identity-only, non-serializable
# ═══════════════════════════════════════════════════════════════════════
def test_gate8_result_not_caller_constructable():
    with pytest.raises(TypeError):
        g8.Gate8Result(
            containment_established=False,
            causing_reason_ids=(),
            invocation_id="inv",
            attempt_id="att",
            request_id="req",
            gate7_result_digest="x",
            effect_plan_digest="x",
            containment_evidence_digest="x",
            live_preflight_digest="x",
            shell_gate_decision="x",
            shell_gate_category="x",
            expires_at=NOW,
            evaluated_at=NOW,
            _seal=object(),
        )


def test_gate8_result_non_transferable(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)
    assert g8.is_gate8_result(copy.copy(r)) is False if _safe_copy(r) else True
    clone = object.__new__(g8.Gate8Result)
    assert g8.is_gate8_result(clone) is False


def _safe_copy(r):
    try:
        copy.copy(r)
        return True
    except TypeError:
        return False


def test_gate8_result_identity_equality_only(chain):
    r1, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    r2, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r1 == r1 and r1 != r2 and hash(r1) == id(r1)


def test_gate8_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g8.Gate8Result,), {})


def test_object_new_gate8_result_not_a_registry_member():
    assert g8.is_gate8_result(object.__new__(g8.Gate8Result)) is False


# ═══════════════════════════════════════════════════════════════════════
# 12. Idempotency / no consumption / no Gate-9 / no Gate-10 effect
# ═══════════════════════════════════════════════════════════════════════
def test_repeated_run_consumes_nothing_and_is_deterministic(chain):
    before = _count_consumption_json()
    r1, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    r2, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r1 is not r2
    assert r1.containment_evidence_digest == r2.containment_evidence_digest
    assert r1.effect_plan_digest == r2.effect_plan_digest
    assert _count_consumption_json() == before


def _count_consumption_json():
    return len(list(REPO_ROOT.rglob("consumption.json")))


def test_module_imports_nothing_effectful():
    tree = ast.parse(G8_SRC)
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in (
        "subprocess", "socket", "pty", "os.system", "requests", "httpx", "urllib",
        "asyncio", "multiprocessing", "ctypes", "fcntl", "signal", "ssl", "selectors",
        "pcae.core.runtime_invocation_authority_consumption",
        "pcae.core.runtime_dispatch_gate9", "pcae.core.runtime_adapter",
        "pcae.core.mock_runtime_adapter",
    ):
        assert bad not in imported, bad
    assert "Popen(" not in G8_SRC and "os.system(" not in G8_SRC and ".dispatch(" not in G8_SRC


def test_no_gate9_or_gate10_symbol_referenced():
    for sym in (
        "runtime_invocation_authority_consumption", "dispatch_attempted", "run_gate9",
        "Gate9Result", "consumption.json", "runtime_adapter",
    ):
        assert sym not in G8_SRC, sym


def test_no_consumption_or_lifecycle_write_call():
    tree = ast.parse(G8_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in (
                "consume", "record_consumption", "bind", "write_text", "mkdir",
                "create_or_compare", "run_gate5", "run_gate6_permission_broker",
                "run_gate7_runtime_enforcement",
            ), node.func.attr


def test_runtime_state_unchanged_after_gate8_runs(chain):
    _run(chain, descriptor_resolver=_resolver(installed=False))
    _run(chain)
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


# ═══════════════════════════════════════════════════════════════════════
# 13. Sole ownership + consumer inventory + production scope
# ═══════════════════════════════════════════════════════════════════════
def test_gate8_is_sole_production_owner_of_containment_boundary():
    # `_GATE8_RESULTS` (the provenance registry) is defined only in gate8.
    # `run_gate8_process_containment` is *called* by the authorized Gate-9
    # coordinator (.1R.14 §16 handoff — it re-runs Gate 8 to recompute the
    # containment evidence), but Gate 8 remains the sole owner. Phase-aware
    # invariant (V-13-1).
    owner_hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"_GATE8_RESULTS", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert owner_hits == {"src/pcae/core/runtime_dispatch_gate8.py"}
    caller_hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"run_gate8_process_containment", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert caller_hits <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        # .1R.17R: the non-effecting Gate-10 pre-effect eligibility coordinator
        # re-runs run_gate8_process_containment (RDGO-001 v3.1 §11 item 5 / §16;
        # .1R.16 §16). Every other caller still fails this guard.
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }


def test_gate8_is_the_only_new_gate7_result_consumer():
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate7Result|is_gate7_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",  # authorized Gate-9 consumer (.1R.14)
        # .1R.17R: authorized Gate-10 pre-effect eligibility consumer — re-derives
        # the Gate-7 lineage (RDGO-001 v3.1 §11 item 4). Every other importer still fails.
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }


def test_gate8_never_consumes_a_gate6_decision():
    assert "is_gate6_decision" not in G8_SRC
    assert "Gate6Decision" not in G8_SRC
    assert "run_gate6_permission_broker" not in G8_SRC


def test_gate8result_has_zero_downstream_production_consumers():
    # .1R.14 (V-13-1): the Gate-9 atomic-consumption coordinator is the
    # single authorized downstream consumer of Gate8Result / is_gate8_result
    # (the .1R.13.1 §16 handoff). Phase-aware subset invariant.
    hits = set(subprocess.run(
        ["git", "grep", "-l", "-E", r"Gate8Result|is_gate8_result", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        # .1R.17R: authorized Gate-10 pre-effect eligibility consumer — re-validates
        # the handed Gate8Result (RDGO-001 v3.1 §11 item 4 + §16). Every other importer still fails.
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
    }, f"unexpected Gate8Result consumer: {sorted(hits)}"


def test_production_scope_since_baseline_is_the_single_new_gate8_file():
    # .1R.14 (V-13-1): the later explicitly human-authorized Gate-9 phase
    # adds exactly runtime_dispatch_gate9.py. Phase-aware subset invariant;
    # gate8.py itself must still be present (the .1R.13.4 functional weight).
    changed = set(subprocess.run(
        ["git", "diff", "--name-only", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.split())
    assert "src/pcae/core/runtime_dispatch_gate8.py" in changed
    assert changed <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unauthorized production-file expansion: {sorted(changed)}"


def test_contracts_and_pol005_bytes_unchanged_since_baseline():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/shell_gate.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/runtime_introspection.py",
    ):
        diff = subprocess.run(
            ["git", "diff", PHASE_ENTRY_BASELINE, _1R15_4_SCOPE_END, "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
        assert diff == "", f"{rel} changed since baseline"


def test_internal_error_fails_closed_with_no_partial_output(chain, monkeypatch):
    def boom(inputs):
        raise ValueError("resolver blew up")

    r, reasons = _run(chain, descriptor_resolver=boom)
    assert r is None and reasons == ("gate8_internal_error_fail_closed",)


# ═══════════════════════════════════════════════════════════════════════
# 14. F7 boundary stated verbatim (threat model NOT broadened)
# ═══════════════════════════════════════════════════════════════════════
def test_f7_boundary_stated_verbatim():
    assert "same-account" in G8_SRC and "arbitrary same-process Python code execution" in G8_SRC
    assert "threat model NOT broadened" in G8_SRC
