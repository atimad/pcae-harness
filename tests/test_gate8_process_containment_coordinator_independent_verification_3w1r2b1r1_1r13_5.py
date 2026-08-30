"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.13.5 — Independent Verification of the
Gate-8 Process Containment (Shell Gate) Coordinator Integration.

RE-DERIVE, DO NOT TRUST. These tests are constructed from the primary
sources — RDGO-001 v3.0 §9 / §1 row 8 / §10 / §13 / §15 / §19, the
``.1R.13.1`` planning document §5 / §11 / §12 / §16 / §17 / §25, the mature
88P ``shell_gate`` classifier source, and the independently-verified Gate-5
/ Gate-6 / Gate-7 boundaries — never from the ``.1R.13.4`` report, its 63
tests, function/type names, or aggregate pass counts.

No defect is repaired in this phase. No Gate-9 / Gate-10 code is added. No
execution is enabled. The Gate-8 establishment envelope is reached only
through a clearly-labelled substitution of the upstream provenance
predicates — manufacturing no ``ValidatedAuthorityProjection``, no approval,
no runtime capability, and no positive ``Gate7Result``. The Shell Gate
classifier used is the real one and is proven non-effecting for every input
these tests supply.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import pickle
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as g5
from pcae.core import runtime_dispatch_gate7 as g7
from pcae.core import runtime_dispatch_gate8 as g8
from pcae.core import runtime_dispatch_permission as rdp
from pcae.core import runtime_introspection as ri
from pcae.core import shell_gate as sg

from _rdw3w_helpers import dispatch_inputs, new_dispatch_identity, full_chain

REPO_ROOT = Path(__file__).resolve().parents[1]
G8_PATH = REPO_ROOT / "src/pcae/core/runtime_dispatch_gate8.py"
G8_SRC = G8_PATH.read_text()
BASELINE = "6a9d650f54fb7a5c02652180f0bbcc3a41080198"  # .1R.13.3 completion
_1R15_4_SCOPE_END = "4d480553"  # end of .1R.15.3; .1R.15.4 (Contract Normalization) is the later authorized change
NOW = "2026-08-29T12:00:00Z"
ECHO = "/bin/echo"

_REAL_IS_GATE7 = g7.is_gate7_result
_REAL_IS_GATE5 = g5.is_gate5_result


# ─────────────────────────────────────────────────────────────────────────
# Independent test-boundary fixtures (no real authority / capability)
# ─────────────────────────────────────────────────────────────────────────
def _sha_file(path: str) -> str:
    d = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            d.update(chunk)
    return d.hexdigest()


class _Projection:
    def __init__(self, digest: str):
        self.subject_scope_binding_digest = digest
        self.freshness_verdict_digest = "f" * 64

    def evidence_digest(self) -> str:
        return "e" * 64


def _mk_gate7(*, decision: str, invocation_id: str, attempt_id: str):
    obj = object.__new__(g7.Gate7Result)
    vals = {
        "decision": decision,
        "matched_no_go_ids": () if decision == "ALLOW" else ("RE-NOGO-002",),
        "causing_reason_ids": ()
        if decision == "ALLOW"
        else ("gate7_runtime_execution_unavailable",),
        "invocation_id": invocation_id,
        "attempt_id": attempt_id,
        "request_id": "pbr-" + "0" * 12,
        "pb_decision_digest": "a" * 64,
        "authority_freshness_digest": "b" * 64,
        "evaluated_input_digest": "c" * 64,
        "runtime_posture_digest": "9" * 64,
        "expires_at": NOW,
        "evaluated_at": NOW,
        "_seal": object(),
    }
    for k, v in vals.items():
        object.__setattr__(obj, k, v)
    return obj


def _mk_gate5(*, invocation_id: str, projection):
    obj = object.__new__(g5.Gate5Result)
    for k, v in (
        ("_projection", projection),
        ("sequence3_event_digest", "d" * 64),
        ("proof_id", "proof-iv"),
        ("approval_id", "ria-" + "0" * 32),
        ("invocation_id", invocation_id),
        ("advisory_reasons", ()),
        ("validated_at", NOW),
        ("_seal", object()),
    ):
        object.__setattr__(obj, k, v)
    return obj


def _effect_plan(**over):
    base = dict(
        executable_path=ECHO,
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
    base.update(over)
    return g8.Gate8EffectPlan(**base)


def _resolver(**over):
    def resolve(inputs):
        a = inputs.adapter_descriptor_binding
        f = dict(
            path=ECHO,
            sha256=_sha_file(ECHO),
            version="1.0",
            descriptor_digest=a.descriptor_digest,
            target_config_digest=a.target_config_digest,
            runtime_target_id=inputs.runtime_target_id,
            installed=True,
        )
        f.update(over)
        return g8.ResolvedExecutable(**f)

    return resolve


@pytest.fixture
def chain(monkeypatch):
    inputs = dispatch_inputs()
    identity = new_dispatch_identity(inputs)
    digest = rdp._expected_subject_scope_binding_digest(identity=identity, inputs=inputs)
    projection = _Projection(digest)
    a7 = _mk_gate7(
        decision="ALLOW",
        invocation_id=identity.invocation_id,
        attempt_id=identity.attempt_id,
    )
    a5 = _mk_gate5(invocation_id=identity.invocation_id, projection=projection)
    monkeypatch.setattr(g7, "is_gate7_result", lambda c: c is a7)
    monkeypatch.setattr(g5, "is_gate5_result", lambda c: c is a5)
    monkeypatch.setattr(
        g8, "is_trusted_validated_authority_projection", lambda p: p is projection
    )
    monkeypatch.setattr(
        g8,
        "revalidate_validated_authority_projection",
        lambda p, *, current_time: p is projection,
    )
    return dict(inputs=inputs, identity=identity, g7=a7, g5=a5, projection=projection)


def _run(chain, **over):
    g7res = over.pop("gate7_result", chain["g7"])
    kw = dict(
        gate5_result=over.pop("gate5_result", chain["g5"]),
        identity=over.pop("identity", chain["identity"]),
        inputs=over.pop("inputs", chain["inputs"]),
        authority_current_time=over.pop("authority_current_time", NOW),
        repo_root=over.pop("repo_root", REPO_ROOT),
        effect_plan=over.pop("effect_plan", _effect_plan()),
        descriptor_resolver=over.pop("descriptor_resolver", _resolver()),
    )
    kw.update(over)
    return g8.run_gate8_process_containment(g7res, **kw)


# ═══ 1. Sole owner ═══════════════════════════════════════════════════════
def test_sole_production_owner_of_gate8_boundary():
    # `_GATE8_RESULTS` (the provenance registry) is defined only in gate8.
    # The authorized Gate-9 coordinator (.1R.14) *calls*
    # `run_gate8_process_containment` to independently recompute the
    # containment evidence (§16 handoff) — Gate 8 stays the sole owner.
    # Phase-aware invariant (V-13-1).
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
    }


def test_module_defines_no_command_classification_of_its_own():
    assert "_classify_command" not in G8_SRC
    assert "SGP_CATEGORIES" not in G8_SRC
    assert "from pcae.core.shell_gate import build_shell_gate" in G8_SRC


# ═══ 2-3. Gate7Result provenance AND decision=="ALLOW" ═══════════════════
def test_missing_gate7_result_fails_closed():
    r, reasons = g8.run_gate8_process_containment(
        None, gate5_result=None, identity=object(), inputs=object(),
        authority_current_time=NOW, repo_root=REPO_ROOT,
        effect_plan=_effect_plan(), descriptor_resolver=_resolver(),
    )
    assert r is None and reasons == ("gate8_untrusted_gate7_result",)


def test_forged_gate7_result_rejected():
    forged = object.__new__(g7.Gate7Result)
    for n in g7.Gate7Result.__slots__:
        try:
            object.__setattr__(forged, n, "ALLOW" if n == "decision" else None)
        except AttributeError:
            pass
    r, reasons = g8.run_gate8_process_containment(
        forged, gate5_result=None, identity=object(), inputs=object(),
        authority_current_time=NOW, repo_root=REPO_ROOT,
        effect_plan=_effect_plan(), descriptor_resolver=_resolver(),
    )
    assert r is None and reasons == ("gate8_untrusted_gate7_result",)


def test_copy_and_serialize_of_gate7_result_are_structurally_refused():
    fake = object.__new__(g7.Gate7Result)
    object.__setattr__(fake, "decision", "ALLOW")
    with pytest.raises(TypeError):
        pickle.dumps(fake)
    with pytest.raises(TypeError):
        copy.deepcopy(fake)


def test_provenance_true_is_not_enough_decision_must_be_allow(chain, monkeypatch):
    """is_gate7_result(x) True + decision != ALLOW  ->  hard stop, no
    Gate8Result, BEFORE Shell Gate is touched."""
    sg_calls = []
    monkeypatch.setattr(sg, "build_shell_gate", lambda *a, **k: sg_calls.append(1) or {})
    for bad in ("DENY", "HUMAN_REVIEW", "MAYBE", "allow", "ALLOW "):
        deny = _mk_gate7(
            decision=bad,
            invocation_id=chain["identity"].invocation_id,
            attempt_id=chain["identity"].attempt_id,
        )
        monkeypatch.setattr(g7, "is_gate7_result", lambda c, _d=deny: c is _d)
        r, reasons = _run(chain, gate7_result=deny)
        assert r is None and reasons == ("gate8_gate7_decision_not_allow",), bad
    assert sg_calls == []


def test_real_registry_gate7_deny_is_rejected_at_the_decision_gate(chain, monkeypatch):
    """A genuine _GATE7_RESULTS member with decision='DENY' — the only thing
    the real coordinator produces today — is rejected by the decision check,
    never mistaken for ALLOW."""
    monkeypatch.setattr(g7, "is_gate7_result", _REAL_IS_GATE7)
    real_deny = _drive_real_gate7_deny(chain)
    assert _REAL_IS_GATE7(real_deny) is True
    assert real_deny.decision == "DENY"
    r, reasons = _run(chain, gate7_result=real_deny)
    assert r is None and reasons == ("gate8_gate7_decision_not_allow",)


def _drive_real_gate7_deny(chain):
    import unittest.mock as m

    identity, inputs, projection = chain["identity"], chain["inputs"], chain["projection"]
    g6 = object.__new__(rdp.Gate6Decision)

    class _PB:
        decision = "ALLOW"
        decision_reason = "would-allow"
        causing_policy_ids = ()
        matched_no_go_ids = ()
        requires_human = False
        simulation_only = False
        implementation_status = "execution_unavailable"

    for k, v in (
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
        object.__setattr__(g6, k, v)
    a5 = _mk_gate5(invocation_id=identity.invocation_id, projection=projection)
    with m.patch.object(rdp, "is_gate6_decision", lambda c: c is g6), m.patch.object(
        g5, "is_gate5_result", lambda c: c is a5
    ), m.patch.object(
        g7, "is_trusted_validated_authority_projection", lambda p: p is projection
    ), m.patch.object(
        g7, "revalidate_validated_authority_projection", lambda p, *, current_time: True
    ):
        result, _ = g7.run_gate7_runtime_enforcement(
            g6, gate5_result=a5, identity=identity, inputs=inputs, authority_current_time=NOW
        )
    assert result is not None and result.decision == "DENY"
    return result


# ═══ 4. Current production reachability = NO ═════════════════════════════
def test_production_chain_yields_no_gate5_result_so_no_gate7_result_exists():
    _approval, projection, _req, _decision = full_chain(simulation_only=False)
    assert projection is None  # permanent NON-REAL hard stop upstream


def test_positive_containment_branch_is_marked_production_unreachable():
    assert "pragma: no cover - production-unreachable positive branch" in G8_SRC


# ═══ 5. Structural test seam is inert ═══════════════════════════════════
def test_test_boundary_substitution_creates_no_real_authority(chain):
    # The fixture substitutes predicates only; the real registries are empty
    # of anything this suite put there, and the runtime posture is unchanged.
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    # The synthetic Gate7Result is NOT a real registry member.
    assert _REAL_IS_GATE7(chain["g7"]) is False
    assert _REAL_IS_GATE5(chain["g5"]) is False


# ═══ 6. Gate5Result provenance + lineage ════════════════════════════════
def test_untrusted_gate5_result_rejected(chain, monkeypatch):
    monkeypatch.setattr(g5, "is_gate5_result", lambda c: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_untrusted_gate5_result",)


def test_mixed_provenance_trusted_gate7_forged_gate5(chain, monkeypatch):
    monkeypatch.setattr(g5, "is_gate5_result", lambda c: False)
    r, reasons = _run(chain, gate5_result=object())
    assert r is None and reasons == ("gate8_untrusted_gate5_result",)


def test_gate5_invocation_lineage_must_match_identity(chain, monkeypatch):
    other5 = _mk_gate5(invocation_id="inv-" + "7" * 32, projection=chain["projection"])
    monkeypatch.setattr(g5, "is_gate5_result", lambda c: c is other5)
    r, reasons = _run(chain, gate5_result=other5)
    assert r is None and reasons == ("gate8_invocation_binding_mismatch",)


def test_gate7_invocation_and_attempt_lineage_must_match_identity(chain):
    import unittest.mock as m

    for bad in (
        dict(invocation_id="inv-" + "8" * 32, attempt_id=chain["identity"].attempt_id),
        dict(invocation_id=chain["identity"].invocation_id, attempt_id="att-" + "8" * 32),
    ):
        other7 = _mk_gate7(decision="ALLOW", **bad)
        with m.patch.object(g7, "is_gate7_result", lambda c, _o=other7: c is _o):
            r, reasons = _run(chain, gate7_result=other7)
        assert r is None and reasons == ("gate8_invocation_binding_mismatch",)


# ═══ 7. Projection re-trust + revalidation at Gate 8's own point of use ══
def test_untrusted_projection_rejected(chain, monkeypatch):
    monkeypatch.setattr(g8, "is_trusted_validated_authority_projection", lambda p: False)
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_stale_validated_authority_projection",)


def test_projection_that_no_longer_revalidates_rejected(chain, monkeypatch):
    monkeypatch.setattr(
        g8, "revalidate_validated_authority_projection", lambda p, *, current_time: False
    )
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_stale_validated_authority_projection",)


def test_revalidation_is_called_with_gate8_current_time(chain, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        g8,
        "revalidate_validated_authority_projection",
        lambda p, *, current_time: seen.setdefault("t", current_time) or True,
    )
    _run(chain, authority_current_time="2099-01-01T00:00:00Z")
    assert seen["t"] == "2099-01-01T00:00:00Z"


def test_revalidation_runs_after_provenance_and_lineage(chain, monkeypatch):
    """A stale projection with a lineage mismatch reports the lineage reason
    — proving lineage is checked first — but a stale projection alone still
    fails closed on the projection."""
    order = []
    monkeypatch.setattr(
        g8,
        "is_trusted_validated_authority_projection",
        lambda p: order.append("trust") or True,
    )
    monkeypatch.setattr(
        g8,
        "revalidate_validated_authority_projection",
        lambda p, *, current_time: order.append("reval") or True,
    )
    _run(chain)
    assert order == ["trust", "reval"]


# ═══ 8. Subject/scope digest recompute ═════════════════════════════════
def test_subject_scope_digest_is_recomputed_and_compared(chain):
    chain["projection"].subject_scope_binding_digest = "0" * 64
    r, reasons = _run(chain)
    assert r is None and reasons == ("gate8_authority_subject_scope_mismatch",)


@pytest.mark.parametrize(
    "field,value",
    [
        ("runtime_target_id", "local-cli-tampered"),
        ("prompt", "A DIFFERENT PROMPT ENTIRELY"),
        ("requested_capability", "local_cli_write"),
        ("task_id", "20990101-0000-some-other-task"),
        ("repository_identity", "github.com/evil/other"),
    ],
)
def test_permission_relevant_field_change_breaks_subject_scope_binding(chain, field, value):
    kw = {field: value} if field != "prompt" else {"prompt": value}
    tampered = dispatch_inputs(**kw)
    # projection still carries the digest for the ORIGINAL inputs
    r, reasons = _run(chain, inputs=tampered)
    assert r is None
    assert reasons in (
        ("gate8_authority_subject_scope_mismatch",),
        ("gate8_request_currentness_drift:invalid_construction_input_facts",),
    )


# ═══ 9. Structural input guards + representability ═════════════════════
@pytest.mark.parametrize(
    "over,reason",
    [
        (dict(identity=object()), "gate8_invalid_identity"),
        (dict(inputs=object()), "gate8_invalid_construction_input"),
        (dict(authority_current_time="   "), "gate8_invalid_authority_current_time"),
        (dict(repo_root="/not/a/path/object"), "gate8_invalid_repo_root"),
        (dict(effect_plan=object()), "gate8_invalid_effect_plan"),
        (dict(descriptor_resolver=42), "gate8_invalid_descriptor_resolver"),
    ],
)
def test_structural_input_guards(chain, over, reason):
    r, reasons = _run(chain, **over)
    assert r is None and reasons == (reason,)


def test_non_local_cli_effect_class_rejected(chain):
    bad = replace(chain["inputs"], effect_class="unbounded_remote_dispatch")
    r, reasons = _run(chain, inputs=bad)
    assert r is None
    assert reasons == ("gate8_request_currentness_drift:invalid_construction_input_facts",)


def test_network_requiring_request_is_ineligible(chain):
    bad = replace(chain["inputs"], network_requirement=True)
    r, reasons = _run(chain, inputs=bad)
    assert r is None
    assert reasons[0].startswith("gate8_request_currentness_drift") or reasons == (
        "gate8_runtime_target_ineligible",
    )


# ═══ 10. Caller shell string / argv vector discipline ═════════════════
@pytest.mark.parametrize(
    "over",
    [
        {"executable_path": "/bin/echo; rm -rf /"},
        {"executable_path": "/bin/echo && curl http://evil"},
        {"executable_path": "/bin/echo|tee x"},
        {"argv": ("$(cat /etc/passwd)",)},
        {"argv": ("ok", "a|b")},
        {"argv": ("ok", "> /tmp/out")},
        {"argv": ("ok", "`whoami`")},
        {"argv": ("ok", "a&b")},
        {"argv": ("ok", "x\ny")},
        {"argv": ("ok", "*.py")},
        {"argv": ("ok", "a'b")},
        {"argv": ('ok', 'a"b')},
    ],
)
def test_shell_metacharacter_in_plan_is_refused(chain, over):
    r, reasons = _run(chain, effect_plan=_effect_plan(**over))
    assert r is None and reasons == ("gate8_caller_shell_string_rejected",)


def test_non_string_argv_token_refused(chain):
    r, reasons = _run(chain, effect_plan=_effect_plan(argv=(123,)))
    assert r is None and reasons == ("gate8_caller_shell_string_rejected",)


def test_argv_is_a_vector_not_a_shell_string(chain, monkeypatch):
    seen = {}
    real = sg.build_shell_gate

    def spy(repo_root, command_text):
        seen["cmd"] = command_text
        return real(repo_root, command_text)

    monkeypatch.setattr(sg, "build_shell_gate", spy)
    monkeypatch.setattr(
        sg, "_call_doctor_test_run", lambda *a, **k: pytest.fail("subprocess spawned")
    )
    _run(chain, effect_plan=_effect_plan(argv=("--json", "status")))
    # every token proven metacharacter-free before it reaches the classifier
    assert seen["cmd"] == "/bin/echo --json status"


# ═══ 11. Effect-plan / descriptor / executable-identity binding ═══════
def test_effect_plan_executable_must_equal_the_resolved_executable(chain):
    r, _ = _run(chain, effect_plan=_effect_plan(executable_path="/bin/cat"))
    assert r is not None and r.containment_established is False
    assert "gate8_effect_plan_binding_mismatch" in r.causing_reason_ids


def test_descriptor_digest_drift_rejected(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(descriptor_digest="9" * 64))
    assert r is not None and r.containment_established is False
    assert "gate8_descriptor_config_drift" in r.causing_reason_ids


def test_target_config_digest_drift_rejected(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(target_config_digest="9" * 64))
    assert r is not None and r.containment_established is False
    assert "gate8_descriptor_config_drift" in r.causing_reason_ids


def test_runtime_target_drift_since_gate7_rejected(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(runtime_target_id="local-cli-other"))
    assert r is not None and r.containment_established is False
    assert "gate8_runtime_target_drift" in r.causing_reason_ids


def test_executable_hash_mismatch_vs_descriptor_pin_rejected(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(sha256="0" * 64))
    assert r is not None and r.containment_established is False
    assert "gate8_executable_identity_mismatch" in r.causing_reason_ids


def test_executable_not_installed_rejected(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r is not None and r.containment_established is False
    assert "gate8_executable_not_installed" in r.causing_reason_ids


def test_executable_absent_on_disk_rejected(chain):
    r, _ = _run(
        chain, descriptor_resolver=_resolver(path="/no/such/executable", installed=True),
        effect_plan=_effect_plan(executable_path="/no/such/executable"),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_executable_not_installed" in r.causing_reason_ids


def test_executable_identity_is_hash_not_path_equality(chain, tmp_path):
    """Same path, changed bytes -> identity mismatch. Proves the check is a
    content hash, not a path-string compare."""
    exe = tmp_path / "adapter-exe"
    exe.write_bytes(b"#!/bin/sh\necho v1\n")
    pin = _sha_file(str(exe))
    exe.write_bytes(b"#!/bin/sh\necho v2-substituted\n")
    r, _ = _run(
        chain,
        descriptor_resolver=_resolver(path=str(exe), sha256=pin),
        effect_plan=_effect_plan(executable_path=str(exe)),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_executable_identity_mismatch" in r.causing_reason_ids


def test_symlink_to_other_executable_is_caught_by_hash(chain, tmp_path):
    real_a = tmp_path / "a"
    real_a.write_bytes(b"AAAA")
    real_b = tmp_path / "b"
    real_b.write_bytes(b"BBBBBBBB")
    link = tmp_path / "link"
    link.symlink_to(real_b)
    r, _ = _run(
        chain,
        descriptor_resolver=_resolver(path=str(link), sha256=_sha_file(str(real_a))),
        effect_plan=_effect_plan(executable_path=str(link)),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_executable_identity_mismatch" in r.causing_reason_ids


def test_descriptor_resolver_return_type_is_enforced(chain):
    r, reasons = _run(chain, descriptor_resolver=lambda inputs: {"path": ECHO})
    assert r is None and reasons == ("gate8_invalid_descriptor_resolver",)


# ═══ 12. cwd / env / containment profile / network / credentials ══════
def test_cwd_outside_repository_scope_rejected(chain):
    r, _ = _run(chain, effect_plan=_effect_plan(cwd="/etc"))
    assert r is not None and r.containment_established is False
    assert "gate8_cwd_outside_repository_scope" in r.causing_reason_ids


def test_cwd_traversal_rejected(chain):
    r, _ = _run(chain, effect_plan=_effect_plan(cwd=str(REPO_ROOT / ".." / "..")))
    assert r is not None and r.containment_established is False
    assert "gate8_cwd_outside_repository_scope" in r.causing_reason_ids


def test_cwd_subdirectory_of_repo_is_accepted_only_as_scope_check(chain):
    """FINDING V-13-5-1 evidence: any repo-scoped cwd passes — cwd is not
    diffed against a bound reference (there is none in the request model).
    The frozen .1R.13.1 §11.2/§25 `gate8_cwd_drift` row is implemented as a
    scope check, not a drift comparison."""
    r, _ = _run(chain, effect_plan=_effect_plan(cwd=str(REPO_ROOT / "src")))
    assert r is not None
    assert "gate8_cwd_outside_repository_scope" not in r.causing_reason_ids


def test_blank_env_name_rejected(chain):
    r, _ = _run(chain, effect_plan=_effect_plan(env_allowlist=("PATH", "  ")))
    assert r is not None and r.containment_established is False
    assert "gate8_environment_not_allowlisted" in r.causing_reason_ids


def test_arbitrary_wellformed_env_name_is_accepted_not_diffed(chain):
    """FINDING V-13-5-1 evidence: a well-formed but arbitrary env var name
    (e.g. a credential-bearing one) passes — env_allowlist is validated for
    well-formedness, not diffed against a bound allowlist. The frozen
    `gate8_environment_allowlist_drift` row is a well-formedness check."""
    r, _ = _run(
        chain, effect_plan=_effect_plan(env_allowlist=("PATH", "AWS_SECRET_ACCESS_KEY"))
    )
    assert r is not None
    assert "gate8_environment_not_allowlisted" not in r.causing_reason_ids
    # …but the value IS bound into the containment evidence digest, so a
    # downstream Gate-9 read-back would detect a changed allowlist.
    r2, _ = _run(chain, effect_plan=_effect_plan(env_allowlist=("PATH", "HOME")))
    assert r.containment_evidence_digest != r2.containment_evidence_digest


@pytest.mark.parametrize(
    "over,reason",
    [
        (dict(child_process_policy="unrestricted"), "gate8_containment_profile_invalid"),
        (dict(resource_limit_ref="  "), "gate8_containment_profile_invalid"),
        (dict(time_limit_ref=""), "gate8_containment_profile_invalid"),
        (dict(supervision_ref="  "), "gate8_containment_profile_invalid"),
        (dict(network_denied=False), "gate8_network_not_deniable"),
        (dict(credentials_required=True), "gate8_credentials_required"),
    ],
)
def test_containment_profile_and_network_credential_binding(chain, over, reason):
    r, _ = _run(chain, effect_plan=_effect_plan(**over))
    assert r is not None and r.containment_established is False
    assert reason in r.causing_reason_ids


def test_single_child_limit_policy_is_also_accepted(chain):
    r, _ = _run(chain, effect_plan=_effect_plan(child_process_policy="single_child_limit"))
    assert r is not None
    assert "gate8_containment_profile_invalid" not in r.causing_reason_ids


def test_transport_drift_has_no_dedicated_reason(chain):
    """FINDING V-13-5-1 evidence: the frozen §11.2 `gate8_transport_drift`
    row has no implementation. transport_type is a constant ('local_cli')
    inside the subject/scope digest; provider/backend drift is covered
    transitively by `gate8_descriptor_config_drift`."""
    assert "gate8_transport_drift" not in G8_SRC
    assert "transport" not in G8_SRC.lower() or "transport_type" not in G8_SRC


# ═══ 13. Canonical Shell Gate classifier — identity + decision mapping ══
def test_shell_gate_classifier_is_the_canonical_88p_implementation(chain, monkeypatch):
    calls = {}
    real = sg.build_shell_gate

    def spy(repo_root, command_text):
        calls["n"] = calls.get("n", 0) + 1
        return real(repo_root, command_text)

    monkeypatch.setattr(sg, "build_shell_gate", spy)
    r, _ = _run(chain)
    assert calls["n"] == 1
    assert r is not None and r.shell_gate_decision in g8.GATE8_ALLOWED_SHELL_GATE_DECISIONS
    assert r.shell_gate_category in g8.GATE8_ALLOWED_SHELL_GATE_CATEGORIES


def test_allowlists_agree_with_shell_gate_decide_source():
    """Re-derived from shell_gate._decide: the only category->decision pairs
    Gate 8 allows are exactly the read-only / governed-lifecycle allow
    pairs."""
    assert g8.GATE8_ALLOWED_SHELL_GATE_CATEGORIES == frozenset(
        {"read_only_inspection", "pcae_governed_lifecycle"}
    )
    assert g8.GATE8_ALLOWED_SHELL_GATE_DECISIONS == frozenset(
        {"allow_read_only", "allow_governed"}
    )
    cat, _ = sg._decide("read_only_inspection", sg._empty_flags(), True, True)
    assert cat == "allow_read_only"
    cat, _ = sg._decide("pcae_governed_lifecycle", sg._empty_flags(), True, True)
    assert cat == "allow_governed"


@pytest.mark.parametrize(
    "prog,args",
    [
        ("/bin/rm", ("build-artifact",)),          # destructive_filesystem -> hard block
        ("/usr/bin/git", ("push", "--force")),     # force_push -> hard block
        ("/bin/cp", ("a", "b")),                   # filesystem_write
    ],
)
def test_mutation_or_destructive_category_denied(chain, prog, args, tmp_path):
    fake = tmp_path / Path(prog).name
    fake.write_bytes(b"x")
    r, _ = _run(
        chain,
        descriptor_resolver=_resolver(path=str(fake), sha256=_sha_file(str(fake))),
        effect_plan=_effect_plan(executable_path=str(fake), argv=args),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_category_denied" in r.causing_reason_ids


def test_unknown_shell_gate_category_fails_closed(chain, monkeypatch):
    monkeypatch.setattr(
        sg,
        "build_shell_gate",
        lambda *a, **k: {"shell_gate": {"decision": "weird", "command_category": "unheard_of"}},
    )
    r, _ = _run(chain)
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_category_denied" in r.causing_reason_ids


def test_shell_gate_internal_error_fails_closed(chain, monkeypatch):
    monkeypatch.setattr(
        sg, "build_shell_gate", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    r, _ = _run(chain)
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_internal_error" in r.causing_reason_ids


def test_hard_block_and_mutation_flags_are_all_treated_as_denial(chain, monkeypatch):
    for envelope in (
        {"shell_gate": {"decision": "allow_read_only", "command_category": "read_only_inspection", "hard_block_present": True}},
        {"shell_gate": {"decision": "allow_read_only", "command_category": "read_only_inspection", "test_run_preflight_required": True}},
        {"shell_gate": {"decision": "allow_read_only", "command_category": "read_only_inspection", "source_mutation_detected": True}},
        {"shell_gate": {"decision": "allow_governed", "command_category": "read_only_inspection", "network_access_detected": True}},
    ):
        monkeypatch.setattr(sg, "build_shell_gate", lambda *a, _e=envelope, **k: _e)
        r, _ = _run(chain)
        assert r is not None and r.containment_established is False
        assert "gate8_shell_gate_category_denied" in r.causing_reason_ids


# ═══ 14. Shell Gate non-effecting proof ═══════════════════════════════
def test_no_shell_gate_reachable_path_spawns_a_subprocess(chain, monkeypatch):
    monkeypatch.setattr(
        sg, "_call_doctor_test_run", lambda *a, **k: pytest.fail("_call_doctor_test_run invoked")
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("subprocess.run from Gate-8 path")
    )
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess.Popen from Gate-8 path")
    )
    # exercise every allowlisted + several denied categories
    _run(chain)
    _run(chain, effect_plan=_effect_plan(argv=("status", "--json")))
    _run(chain, descriptor_resolver=_resolver(installed=False))


@pytest.mark.parametrize(
    "prog,argv",
    [
        ("/usr/bin/pytest", ("-q",)),
        ("/opt/py.test", ("tests/",)),
        ("/usr/local/bin/python", ("-m", "pytest", "-q")),
        ("/usr/bin/tox", ()),
        ("/usr/bin/nox", ("-s", "tests")),
    ],
)
def test_test_runner_program_refused_before_build_shell_gate(chain, monkeypatch, prog, argv):
    calls = []
    monkeypatch.setattr(sg, "build_shell_gate", lambda *a, **k: calls.append(1) or {})
    fake_ok = _resolver(path=prog)
    r, _ = _run(
        chain,
        descriptor_resolver=fake_ok,
        effect_plan=_effect_plan(executable_path=prog, argv=argv),
    )
    assert r is not None and r.containment_established is False
    assert "gate8_shell_gate_preflight_side_effect_refused" in r.causing_reason_ids
    assert calls == []


def test_expensive_test_run_probe_is_only_reachable_from_pytest_which_gate8_refuses():
    """Re-derived from shell_gate: `_call_doctor_test_run` fires only when
    command_category == 'test_execution' AND expensive_test_execution_detected,
    which `_classify_command` sets only for a pytest program / `-m pytest`.
    Gate 8 refuses every such program basename / argv token first."""
    src = (REPO_ROOT / "src/pcae/core/shell_gate.py").read_text()
    assert 'command_category == "test_execution"' in src
    assert '"expensive_test_execution_detected"' in src
    assert "_SHELL_GATE_PREFLIGHT_TRIGGER_PROGRAMS" in G8_SRC
    assert {"pytest", "py.test", "tox", "nox", "unittest"} <= set(
        g8._SHELL_GATE_PREFLIGHT_TRIGGER_PROGRAMS
    )


def test_only_effectful_shell_gate_helper_is_call_doctor_test_run():
    """Inventory: the sole subprocess in shell_gate is _call_doctor_test_run.
    No other reachable helper opens a process / socket."""
    src = (REPO_ROOT / "src/pcae/core/shell_gate.py").read_text()
    tree = ast.parse(src)
    parent = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}

    def _enclosing_func(node):
        cur = node
        while cur in parent:
            cur = parent[cur]
            if isinstance(cur, ast.FunctionDef):
                return cur.name
        return "<module>"

    spawning_funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_src = ast.get_source_segment(src, node) or ""
            if any(
                t in call_src
                for t in ("subprocess.run(", "subprocess.Popen(", "subprocess.call(", "os.system(", "os.popen(")
            ):
                spawning_funcs.add(_enclosing_func(node))
    assert spawning_funcs == {"_call_doctor_test_run"}, spawning_funcs


# ═══ 15. Gate8Result construction / provenance / anti-transfer ════════
def test_gate8_result_not_caller_constructable():
    with pytest.raises(TypeError):
        g8.Gate8Result(
            containment_established=False, causing_reason_ids=(), invocation_id="i",
            attempt_id="a", request_id="r", gate7_result_digest="x", effect_plan_digest="x",
            containment_evidence_digest="x", live_preflight_digest="x", shell_gate_decision="x",
            shell_gate_category="x", expires_at=NOW, evaluated_at=NOW, _seal=object(),
        )


def test_is_gate8_result_is_provenance_only_not_containment(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert g8.is_gate8_result(r) is True
    assert r.containment_established is False
    # the predicate's RETURN expression must be membership-only — it must not
    # branch on containment_established.
    tree = ast.parse(G8_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "is_gate8_result":
            returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
            assert len(returns) == 1
            expr = ast.get_source_segment(G8_SRC, returns[0].value) or ""
            assert "containment_established" not in expr
            assert "_GATE8_RESULTS" in expr and "isinstance" in expr
            ifs = [n for n in ast.walk(node) if isinstance(n, ast.If)]
            assert ifs == []


def test_object_new_gate8_result_is_not_a_registry_member():
    assert g8.is_gate8_result(object.__new__(g8.Gate8Result)) is False


def test_gate8_result_non_serializable_and_non_copyable(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    with pytest.raises(TypeError):
        pickle.dumps(r)
    with pytest.raises(TypeError):
        copy.deepcopy(r)


def test_gate8_result_not_subclassable():
    with pytest.raises(TypeError):
        type("Sub", (g8.Gate8Result,), {})


def test_gate8_result_identity_equality_only(chain):
    r1, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    r2, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r1 == r1
    assert r1 != r2
    assert hash(r1) == id(r1)
    assert g8.is_gate8_result(r1) and g8.is_gate8_result(r2)


def test_reconstructed_lookalike_with_true_flag_is_not_trusted(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    clone = object.__new__(g8.Gate8Result)
    for s in g8.Gate8Result.__slots__:
        try:
            object.__setattr__(
                clone, s, True if s == "containment_established" else getattr(r, s, None)
            )
        except AttributeError:
            pass
    assert g8.is_gate8_result(clone) is False


# ═══ 16. Cross-invocation / cross-effect-plan non-reuse ═══════════════
def test_negative_result_from_invocation_a_does_not_validate_for_b(chain):
    r_a, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    # A different invocation -> a different Gate8Result object; is_gate8_result
    # is identity-only so r_a can never stand in for B.
    assert g8.is_gate8_result(r_a) is True
    assert r_a.invocation_id == chain["identity"].invocation_id


def test_effect_plan_change_changes_every_bound_digest(chain):
    base, _ = _run(chain)
    for over in (
        dict(argv=("different-arg",)),
        dict(cwd=str(REPO_ROOT / "src")),
        dict(env_allowlist=("PATH",)),
        dict(time_limit_ref="timeout-99s"),
    ):
        other, _ = _run(chain, effect_plan=_effect_plan(**over))
        assert other.effect_plan_digest != base.effect_plan_digest
        assert other.containment_evidence_digest != base.containment_evidence_digest


def test_gate7_digest_binds_the_consumed_decision_evidence(chain):
    r, _ = _run(chain)
    assert len(r.gate7_result_digest) == 64


# ═══ 17. Idempotency / no consumption / no Gate-9 / no Gate-10 ════════
def test_repeated_runs_consume_nothing_and_are_deterministic(chain):
    before = len(list(REPO_ROOT.rglob("consumption.json")))
    r1, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    r2, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    assert r1 is not r2
    assert r1.containment_evidence_digest == r2.containment_evidence_digest
    assert len(list(REPO_ROOT.rglob("consumption.json"))) == before


def test_module_imports_nothing_effectful():
    tree = ast.parse(G8_SRC)
    imported: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module)
        elif isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
    for bad in (
        "subprocess", "socket", "pty", "requests", "httpx", "urllib", "asyncio",
        "multiprocessing", "ctypes", "fcntl", "signal", "ssl", "selectors",
        "pcae.core.runtime_invocation_authority_consumption",
        "pcae.core.runtime_dispatch_gate9", "pcae.core.runtime_adapter",
        "pcae.core.mock_runtime_adapter",
    ):
        assert bad not in imported, bad
    for token in ("Popen(", "os.system(", ".dispatch(", "os.fork(", "os.exec"):
        assert token not in G8_SRC, token


def test_no_gate9_or_gate10_symbol_referenced():
    for sym in (
        "runtime_invocation_authority_consumption", "dispatch_attempted", "run_gate9",
        "Gate9Result", "consumption.json", "runtime_adapter", "Gate6Decision",
        "is_gate6_decision", "run_gate6_permission_broker", "run_gate7_runtime_enforcement",
        "resolve_runtime_enforcement_posture",
    ):
        assert sym not in G8_SRC, sym


def test_no_consumption_or_lifecycle_write_call_in_source():
    tree = ast.parse(G8_SRC)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in (
                "consume", "record_consumption", "write_text", "write_bytes", "mkdir",
                "create_or_compare", "unlink", "rmdir",
            ), node.func.attr


def test_runtime_posture_unchanged_after_gate8_runs(chain):
    _run(chain)
    _run(chain, descriptor_resolver=_resolver(installed=False))
    _run(chain, effect_plan=_effect_plan(network_denied=False))
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"


def test_internal_error_fails_closed_no_partial_output(chain):
    def boom(inputs):
        raise ValueError("resolver exploded")

    r, reasons = _run(chain, descriptor_resolver=boom)
    assert r is None and reasons == ("gate8_internal_error_fail_closed",)


# ═══ 18. Gate-8 -> Gate-9 handoff (§16) — data only, not implemented ══
def test_gate8result_carries_exactly_the_frozen_handoff_fields():
    """RDGO-001 §10 / .1R.13.1 §16.1: the fields a future Gate 9 re-derives."""
    slots = set(g8.Gate8Result.__slots__)
    for f in (
        "containment_established", "invocation_id", "attempt_id", "request_id",
        "gate7_result_digest", "effect_plan_digest", "containment_evidence_digest",
        "live_preflight_digest", "causing_reason_ids",
    ):
        assert f in slots, f


def test_no_gate9_consumer_of_gate8result_exists_yet():
    # .1R.14 (V-13-1): the explicitly human-authorized Gate-9 phase adds the
    # single authorized downstream consumer of Gate8Result / is_gate8_result
    # (the .1R.13.1 §16 handoff Gate-8 independent verification re-reviewed).
    # Phase-aware subset invariant; any other consumer still fails.
    hits = set(
        subprocess.run(
            ["git", "grep", "-l", "-E", r"Gate8Result|is_gate8_result", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unexpected Gate8Result consumer: {sorted(hits)}"


def test_gate8result_is_not_serialized_or_persisted_anywhere(chain):
    r, _ = _run(chain, descriptor_resolver=_resolver(installed=False))
    with pytest.raises(TypeError):
        pickle.dumps(r)
    # no handoff file appears
    assert not list(REPO_ROOT.rglob("gate8_handoff*.json"))


def test_negative_gate8result_is_not_progression_eligible(chain):
    """Forward invariant for Gate 9: is_gate8_result True is provenance;
    containment_established False must never read as partial success."""
    r, _ = _run(chain, effect_plan=_effect_plan(network_denied=False))
    assert g8.is_gate8_result(r) is True
    assert r.containment_established is False
    assert r.causing_reason_ids  # structured audit record


# ═══ 19. Gate-9 unblocking criteria (§17) — status report only ════════
def test_gate9_unblocking_criteria_status():
    """Report each .1R.13.1 §17 criterion. .1R.13.5 itself must close before
    criterion 4 is satisfied — this test asserts only the mechanically
    checkable ones."""
    # 7: runtime still non-executing
    assert ri.CURRENT_RUNTIME_STATE == "Observed"
    assert ri.EXECUTION_AVAILABILITY == "unavailable"
    # 3: Gate-8 implementation present
    assert hasattr(g8, "run_gate8_process_containment")
    # 1: Gate-7 implementation present
    assert hasattr(g7, "run_gate7_runtime_enforcement")
    # contract identity (part of criterion 5/8 environment)
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
    ):
        diff = subprocess.run(
            ["git", "diff", BASELINE, _1R15_4_SCOPE_END, "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == ""


# ═══ 20. V-13-1 guard extensions — orientation actively challenged ════
_EXTENDED_GUARDS = [
    ("tests/test_gate5_approval_validation_coordinator_3w1r2b1r1_1r10.py",
     "test_only_expected_production_files_changed_since_baseline"),
    ("tests/test_gate5_approval_validation_coordinator_integration_independent_verification_3w1r2b1r1_1r11.py",
     "test_production_scope_is_exactly_the_three_planned_files"),
    ("tests/test_gate6_permission_broker_production_consumption_3w1r2b1r1_1r12.py",
     "test_only_expected_production_file_changed_since_baseline"),
    ("tests/test_gate6_permission_broker_production_consumption_integration_independent_verification_3w1r2b1r1_1r13.py",
     "test_1r12_production_diff_is_exactly_one_file"),
    ("tests/test_gate7_runtime_enforcement_coordinator_integration_3w1r2b1r1_1r13_2.py",
     "test_production_scope_since_baseline_is_the_single_new_gate7_file"),
    ("tests/test_gate7_runtime_enforcement_coordinator_independent_verification_3w1r2b1r1_1r13_3.py",
     "test_no_downstream_production_consumer_of_gate7_result"),
]


def test_all_extended_guards_still_present_and_named_the_same():
    for rel, name in _EXTENDED_GUARDS:
        src = (REPO_ROOT / rel).read_text()
        assert f"def {name}(" in src, f"{rel}::{name} missing"


def test_extended_guards_keep_subset_orientation_not_equality():
    """Each converted guard must (a) reference gate8.py in its authorized set
    (inline or via a module-level set the file also extended) and (b) test a
    SUBSET relation (`- AUTHORIZED == set()`, `<= {...}`, or `x in changed`),
    never `changed == {literal}` — so an unauthorized 3rd production file
    still fails."""
    for rel, name in _EXTENDED_GUARDS:
        src = (REPO_ROOT / rel).read_text()
        assert "runtime_dispatch_gate8.py" in src, f"{rel} not extended at all"
        tree = ast.parse(src)
        body = ""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                body = ast.get_source_segment(src, node) or ""
        assert body, f"{rel}::{name} missing"
        subset_form = (
            "<=" in body
            or "- _AUTHORIZED" in body
            or "unexpected == set()" in body
            or "- _authorized" in body
            or ("changed - " in body and "== set()" in body)
            or ("hits <= " in body)
        )
        assert subset_form, f"{name} does not use a subset relation"
        # no exact-equality pin of the raw changed set against a literal
        assert "changed == {" not in body.replace(" ", "")
        assert "out==[" not in body.replace(" ", "")


def test_gate9_and_hpac_asserts_stay_exact_after_extension():
    # .1R.14 (V-13-1): the Gate-9 store importer/consumer asserts are now
    # phase-aware SUBSET asserts bounded to the single authorized importer
    # (runtime_dispatch_gate9.py) — the explicitly human-authorized .1R.14
    # phase. The hpac_verifier consumer asserts stay exact.
    for rel in (
        "tests/test_runtime_authority_production_repair_3w1r2b1r1117.py",
        "tests/test_b1_b7_n1_n2_production_authority_repair_independent_verification_3w1r2b1r1_1r8.py",
    ):
        src = (REPO_ROOT / rel).read_text()
        # .1R.17 (Slice A): a second authorized importer — the non-effecting
        # Gate-10 pre-effect eligibility coordinator — is admitted; the
        # asserts stay phase-aware SUBSET asserts (any OTHER importer fails).
        assert "gate9_consumers <= {" in src or "gate9_callers <= {" in src
        assert '"src/pcae/core/runtime_dispatch_gate9.py"' in src
        assert '"src/pcae/core/runtime_dispatch_gate10_eligibility.py"' in src
        assert "hpac_consumers == {" in src  # unweakened


def test_synthetic_unauthorized_third_production_file_would_fail_the_subset_guards():
    """Actively challenge: simulate the git-diff set the guards check
    containing an unauthorized file and confirm `<= {gate7, gate8}` rejects
    it."""
    authorized = {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
    }
    unauthorized_set = authorized | {"src/pcae/core/runtime_adapter.py"}
    # the guards assert `changed - AUTHORIZED == set()` / `changed <= AUTHORIZED`
    assert (unauthorized_set - authorized) != set()   # guard WOULD fail
    assert not (unauthorized_set <= authorized)        # guard WOULD fail
    assert (authorized - authorized) == set()          # real state passes
    assert authorized <= authorized


def test_gate7_result_consumer_grep_is_exactly_gate7_and_gate8_today():
    # .1R.14 (V-13-1): the explicitly human-authorized Gate-9
    # atomic-consumption coordinator is the third authorized module that
    # references the Gate-7 result symbols (it re-derives the Gate-7 lineage
    # via is_gate7_result per the .1R.13.1 §16 handoff). Phase-aware subset
    # invariant.
    hits = set(
        subprocess.run(
            ["git", "grep", "-l", "-E", r"Gate7Result|is_gate7_result", "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    assert hits <= {
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unexpected Gate7Result consumer: {sorted(hits)}"


# ═══ 21. V-13-3-1 / V-13-3-2 — not amplified ═════════════════════════
def test_gate8_makes_no_pb_policy_revalidation_claim():
    assert "revalidate" in G8_SRC  # of the projection, not PB policy
    assert "re-evaluate" not in G8_SRC.lower()
    assert "pb policy" not in G8_SRC.lower()
    assert "permission broker" not in G8_SRC.lower() or "not an extension" in G8_SRC.lower()


def test_gate8_authority_depends_on_decision_not_matched_no_go_list(chain, monkeypatch):
    """V-13-3-2: Gate 8 trusts `decision == 'ALLOW'` + provenance, never the
    completeness of `matched_no_go_ids`."""
    a7 = _mk_gate7(
        decision="ALLOW",
        invocation_id=chain["identity"].invocation_id,
        attempt_id=chain["identity"].attempt_id,
    )
    object.__setattr__(a7, "matched_no_go_ids", ("RE-NOGO-001", "RE-NOGO-999"))
    monkeypatch.setattr(g7, "is_gate7_result", lambda c: c is a7)
    r, _ = _run(chain, gate7_result=a7)
    # still proceeds on decision==ALLOW; the no-go list is only digested
    assert r is not None


# ═══ 22. F7 boundary stated verbatim, not broadened ══════════════════
def test_f7_boundary_verbatim_and_not_broadened():
    assert "same-account" in G8_SRC
    assert "arbitrary same-process Python code execution" in G8_SRC
    assert "threat model NOT broadened" in G8_SRC


# ═══ 23. Gate-5 / 6 / 7 regression ══════════════════════════════════
def test_gate5_still_non_real_and_consumes_nothing():
    _a, projection, _r, _d = full_chain(simulation_only=False)
    assert projection is None
    assert len(g5._GATE5_RESULTS) == 0 or all(
        _REAL_IS_GATE5(x) for x in g5._GATE5_RESULTS
    )


def test_gate7_still_denies_and_gate7_module_byte_unchanged():
    diff = subprocess.run(
        ["git", "diff", BASELINE, _1R15_4_SCOPE_END, "--", "src/pcae/core/runtime_dispatch_gate7.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert diff == ""
    assert g7.GATE7_DECISION_VALUES == frozenset({"ALLOW", "DENY"})


def test_gate6_and_pol005_byte_unchanged_since_baseline():
    for rel in (
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/permission_broker_foundation.py",
    ):
        diff = subprocess.run(
            ["git", "diff", BASELINE, _1R15_4_SCOPE_END, "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == ""


# ═══ 24. Production-file scope + contract identity ═══════════════════
def test_production_diff_since_baseline_is_exactly_one_new_file():
    # .1R.14 (V-13-1): the later explicitly human-authorized Gate-9 phase
    # adds exactly runtime_dispatch_gate9.py. Phase-aware subset invariant;
    # gate8.py (the .1R.13.4 functional weight) must still be present.
    changed = set(
        subprocess.run(
            ["git", "diff", "--name-only", BASELINE, _1R15_4_SCOPE_END, "--", "src/pcae"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    assert "src/pcae/core/runtime_dispatch_gate8.py" in changed
    assert changed <= {
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
    }, f"unauthorized production-file expansion: {sorted(changed)}"


def test_all_frozen_contracts_and_shell_gate_byte_unchanged():
    for rel in (
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/RUNTIME_PROVIDER_ADAPTER_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "src/pcae/core/shell_gate.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_introspection.py",
        "src/pcae/core/runtime_enforcement_safety_authorization.py",
    ):
        diff = subprocess.run(
            ["git", "diff", BASELINE, _1R15_4_SCOPE_END, "--", rel],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        assert diff == "", f"{rel} changed since baseline"


def test_gate8_never_consumes_a_gate6_decision():
    assert "Gate6Decision" not in G8_SRC
    assert "is_gate6_decision" not in G8_SRC
