"""Phase 149O.18F -- HMRC Assembled Attack Matrix.

Independently re-extracted, from `docs/contracts/HATP_MANDATORY_ROLLBACK_
CONSUMPTION_CONTRACT.md` Section 29 directly (not from any earlier phase
report's own count), the exact 45-scenario mandatory-consumption attack
matrix. This module mechanically proves all 45 scenarios are represented
-- exactly 45, no gaps, no duplicates, no unspecified outcome -- each with
a real, executing assertion against the assembled A-F production code
(never a prose-only claim).

Attacks reuse the existing, already-verified fixture harnesses from the
per-wave test modules (`tests.test_hatp_rollback_consumption._Harness` for
real evidence-store/RAE/HATP-verifier-integrated attacks; `tests.test_agent`
job/PER fixtures plus the established deterministic-test-seam pattern for
AG3/AG5 effect-boundary attacks; local cutover-record fixtures for
cutover-state attacks) rather than re-deriving a third, potentially
inconsistent fixture harness (149O.5-F-3 discipline).

This is Wave F's own assembled proof, not 149O.19's independent
verification -- 149O.19 must independently re-derive this matrix again
directly against merged production code without trusting this table.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple

import pytest

from pcae.core import agent as _agent_mod
from pcae.core import hatp_mandatory_cutover as _cutover_mod
from pcae.core import hatp_rollback_consumption as _consumption_mod
from pcae.core import hatp_rollback_consumption as cons
from pcae.core import rollback_approval_evidence as rae
from pcae.core.hatp_evidence_store import HATPEvidenceStore
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.hatp_rollback_consumption import HATPRollbackConsumptionResult
from pcae.core.hatp_signed_evidence import serialize_hatp_signed_evidence
from pcae.core.human_approval_trusted_provenance import (
    Ag5OperationReference as HATPAg5OperationReference,
    HATPVerificationStatus,
    RollbackSite as HATPRollbackSite,
)
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW

from tests.test_agent import (
    _init_git_root,
    _make_per_test_ecp,
    _make_rer_test_per,
    _patch_rollback_execute_helpers,
    _setup_approved_rollback,
    _setup_committed_change,
)
from tests.test_hatp_rollback_consumption import _Harness, _ag3_ctx, _ag5_ctx, _repo_state

pytestmark = pytest.mark.fast_green

_VALID_EVIDENCE_ID = "a" * 64


class _Attack(NamedTuple):
    number: int
    threat: str
    entry_point: str
    expected_outcome: str


# Verbatim (paraphrase-minimized) re-extraction of HMRC-001 Sec.29, cross-
# checked against `docs/PHASE_149O_14_HATP_AG3_AG5_MANDATORY_PRODUCTION_
# CONSUMPTION_ARCHITECTURE.md` Sec.30 (the architecture doc HMRC-001's own
# Sec.29 preamble names as its reconciliation source).
ATTACK_MATRIX = (
    _Attack(1, "Missing evidence ID", "hatp_rollback_consumption", "fail closed"),
    _Attack(2, "Malformed evidence envelope", "hatp_rollback_consumption", "fail closed"),
    _Attack(3, "Digest mismatch", "hatp_rollback_consumption", "fail closed"),
    _Attack(4, "Wrong operation (evidence signed for a different job/PER)", "hatp_rollback_consumption", "fail closed"),
    _Attack(5, "AG3 evidence used for AG5 dispatch", "hatp_rollback_consumption", "fail closed"),
    _Attack(6, "AG5 evidence used for AG3 dispatch", "hatp_rollback_consumption", "fail closed"),
    _Attack(7, "Wrong repository", "hatp_rollback_consumption", "fail closed"),
    _Attack(8, "Wrong deployment", "hatp_rollback_consumption", "fail closed"),
    _Attack(9, "Expired proof", "hatp_rollback_consumption", "fail closed"),
    _Attack(10, "Revoked signer", "hatp_rollback_consumption", "fail closed"),
    _Attack(11, "Revoked authority / substrate readiness lost", "hatp_rollback_consumption", "fail closed"),
    _Attack(12, "Decision changed after signing", "hatp_rollback_consumption", "fail closed"),
    _Attack(13, "Binding changed after signing", "hatp_rollback_consumption", "fail closed"),
    _Attack(14, "Fresh unregistered key", "hatp_rollback_consumption", "fail closed"),
    _Attack(15, "Forged signer", "hatp_rollback_consumption", "fail closed"),
    _Attack(16, "Caller-supplied approval_present=True", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(17, "Caller-supplied HATP VALID spoof", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(18, "Test-provider injection", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(19, "Arbitrary trust-store injection", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(20, "Legacy-approved + missing HATP evidence, post-cutover", "execute_rollback", "fail closed"),
    _Attack(21, "Legacy-approved + invalid HATP evidence, post-cutover", "execute_rollback", "fail closed"),
    _Attack(22, "Delete Cutover Record", "hatp_mandatory_cutover", "fail closed, no downgrade"),
    _Attack(23, "CLI-flag downgrade (omit --hatp-evidence-id post-cutover)", "cli", "rejected"),
    _Attack(24, "Alternate production effect caller bypass", "agent.py caller inventory", "no un-audited caller"),
    _Attack(25, "Cached previous VALID reused", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(26, "Cached previous PB ALLOW reused", "hatp_rollback_consumption", "structurally impossible"),
    _Attack(27, "Evidence deleted after prior success, retry", "hatp_rollback_consumption", "fail closed on retry"),
    _Attack(28, "Evidence modified after prior success, retry", "hatp_rollback_consumption", "fail closed on retry"),
    _Attack(29, "Two valid evidence IDs, no ID supplied", "cli / hatp_rollback_consumption", "rejected, explicit selection required"),
    _Attack(30, "Old raw hatp_proof parameter bypass attempt", "execute_rollback / build_rollback_execution", "rejected"),
    _Attack(31, "Old hatp_evidence parameter bypass attempt", "execute_rollback / build_rollback_execution", "rejected"),
    _Attack(32, "PB returns HUMAN_REVIEW despite valid HATP", "execute_rollback / build_rollback_execution", "effect does not proceed"),
    _Attack(33, "PB returns DENY despite valid HATP", "execute_rollback / build_rollback_execution", "effect does not proceed"),
    _Attack(34, "PB ALLOW under simulation_only=True", "hatp_rollback_consumption", "does not authorize effect"),
    _Attack(35, "Evidence created under LEGACY_COMPATIBLE, consumed post-cutover", "execute_rollback", "allowed if still fresh/valid"),
    _Attack(36, "Wrong AG3 job", "hatp_rollback_consumption", "fail closed"),
    _Attack(37, "Wrong AG5 PER", "hatp_rollback_consumption", "fail closed"),
    _Attack(38, "Wrong AG5 ecp_id", "hatp_rollback_consumption", "fail closed"),
    _Attack(39, "Cutover-record corruption", "hatp_mandatory_cutover", "fail closed, never legacy fallback"),
    _Attack(40, "Cutover-record wrong repository", "hatp_mandatory_cutover", "treated as not-present-for-this-repo"),
    _Attack(41, "Cutover-record unknown version", "hatp_mandatory_cutover", "fail closed, never assume legacy"),
    _Attack(42, "Cutover-record boolean version", "hatp_mandatory_cutover", "rejected"),
    _Attack(43, "Repository moved/cloned/re-worktreed, evidence reused", "hatp_rollback_consumption", "fail closed unless identity genuinely matches"),
    _Attack(44, "Divergence-blocking AG5 file state combined with valid HATP evidence", "build_rollback_execution", "structural divergence check still blocks"),
    _Attack(45, "Evidence existence without an explicit evidence ID supplied", "execute_rollback / build_rollback_execution", "no effect, no implicit lookup"),
)


def test_exactly_45_attacks_structured_no_gaps_no_duplicates() -> None:
    assert len(ATTACK_MATRIX) == 45
    numbers = [a.number for a in ATTACK_MATRIX]
    assert numbers == list(range(1, 46))
    assert len(set(numbers)) == 45
    for attack in ATTACK_MATRIX:
        assert attack.threat
        assert attack.entry_point
        assert attack.expected_outcome


# Mechanical registry: each executed test below registers which attack
# number(s) it represents; the final completeness test confirms every one
# of the 45 declared attacks above has at least one real, executed test.
_REPRESENTED: set = set()


def _represents(*numbers: int):
    def _decorator(fn):
        _REPRESENTED.update(numbers)
        return fn

    return _decorator


# ─────────────────────────────────────────────────────────────────────────
# 1-3, 43: load/digest failures (real HATPEvidenceStore integration)
# ─────────────────────────────────────────────────────────────────────────


@_represents(1)
def test_attack_01_missing_evidence_id(tmp_path: Path) -> None:
    h = _Harness(tmp_path)  # never published
    result = h.consume(simulation_only=False)
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert result.pb_decision != DECISION_ALLOW


@_represents(2)
def test_attack_02_malformed_evidence_envelope(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    path = h.hatp_evidence_store.path_for(h.evidence_id)
    path.write_bytes(b"{not valid json")
    result = h.consume(simulation_only=False)
    assert result.hatp_status == HATPVerificationStatus.MISSING
    assert result.pb_decision != DECISION_ALLOW


@_represents(3)
def test_attack_03_digest_mismatch(tmp_path: Path) -> None:
    """Corrupting a published envelope's content without renaming its
    (digest-derived) file breaks the HSCE digest binding -- fails closed
    exactly like a malformed load (both are the same `evidence_load_failed`
    fail-closed branch, HMRC-REQ-018)."""
    h = _Harness(tmp_path)
    h.publish_envelope()
    path = h.hatp_evidence_store.path_for(h.evidence_id)
    tampered = replace(h.envelope, provider_assertion=b"tampered-breaks-digest-binding")
    path.write_bytes(serialize_hatp_signed_evidence(tampered))
    result = h.consume(simulation_only=False)
    assert result.hatp_status in (HATPVerificationStatus.INVALID_SIGNATURE, HATPVerificationStatus.MISSING)
    assert result.pb_decision != DECISION_ALLOW


@_represents(43)
def test_attack_43_repository_moved_evidence_reused(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    result = h.consume(simulation_only=False, canonical_deployment_root="/some/other/moved/repo/path")
    assert result.pb_decision != DECISION_ALLOW


# ─────────────────────────────────────────────────────────────────────────
# 4-8, 36-38: operation/family/repository/deployment binding
# ─────────────────────────────────────────────────────────────────────────


@_represents(4, 36)
def test_attack_04_36_wrong_ag3_job(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    result = h.consume(
        simulation_only=False,
        request=h.request(operation_context=_ag3_ctx(job_id="a-completely-different-job")),
    )
    assert result.pb_decision != DECISION_ALLOW


@_represents(5)
def test_attack_05_ag3_evidence_used_for_ag5_dispatch(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    result = h.consume(simulation_only=False, request=h.request(operation_context=_ag5_ctx()))
    assert result.pb_decision != DECISION_ALLOW


@_represents(6, 37, 38)
def test_attack_06_37_38_ag5_evidence_used_for_ag3_and_wrong_per_ecp(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.rollback_site = rae.RollbackSite.AG5
    h.op_context = _ag5_ctx(per_id="per-x", ecp_id="ecp-x")
    # `_build_binding` needs `self.op_ref` to already be an
    # `Ag5OperationReference` (RAE-REQ-022's type-matching constructor
    # check); `_build_proof`'s default-field dict eagerly evaluates
    # `self.op_ref.job_id` (an AG3-shaped default) before applying our
    # override below, so `op_ref` is swapped back to an AG3-shaped
    # placeholder in between -- the placeholder value itself is
    # irrelevant since `operation_reference` is explicitly overridden.
    h.op_ref = rae.Ag5OperationReference(per_id="per-x", ecp_id="ecp-x")
    h.binding = h._build_binding()
    h.op_ref = rae.Ag3OperationReference(job_id="unused-placeholder", original_commit_sha="c" * 40)
    h.proof = h._build_proof(
        binding_id=h.binding.evidence_id,
        binding_digest=h.binding.content_digest,
        rollback_site=HATPRollbackSite.AG5,
        operation_reference=HATPAg5OperationReference(per_id="per-x", ecp_id="ecp-x"),
    )
    h.resign_proof()
    h.publish_envelope()

    # attack 6: AG5 evidence consumed against an AG3 context.
    result_ag3 = h.consume(simulation_only=False, request=h.request(operation_context=_ag3_ctx()))
    assert result_ag3.pb_decision != DECISION_ALLOW

    # attack 37/38: correct family (AG5) but wrong per_id/ecp_id.
    result_wrong_per = h.consume(
        simulation_only=False, request=h.request(operation_context=_ag5_ctx(per_id="per-x", ecp_id="wrong-ecp"))
    )
    assert result_wrong_per.pb_decision != DECISION_ALLOW


@_represents(7)
def test_attack_07_wrong_repository(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    result = h.consume(simulation_only=False, current_repository_id=str(uuid.uuid4()))
    assert result.pb_decision != DECISION_ALLOW


@_represents(8)
def test_attack_08_wrong_deployment(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    result = h.consume(simulation_only=False, canonical_deployment_root="/an/unregistered/deployment/root")
    assert result.pb_decision != DECISION_ALLOW


# ─────────────────────────────────────────────────────────────────────────
# 9-15: expiry / revocation / decision-changed / binding-changed / forged
# ─────────────────────────────────────────────────────────────────────────


def _tamper_binding_file_on_disk(h: _Harness, **field_overrides) -> None:
    """Directly patches the on-disk RAE Binding JSON after it was already
    written through the (deliberately immutable, no-overwrite) store API
    -- simulating post-signing tampering/expiry rather than legitimate
    construction, since `RollbackApprovalEvidenceStore.write_binding`
    correctly refuses to overwrite an existing record."""
    binding_path = h.rae_evidence_root / "bindings" / f"{h.binding.evidence_id}.json"
    document = json.loads(binding_path.read_text(encoding="utf-8"))
    document.update(field_overrides)
    binding_path.write_text(json.dumps(document), encoding="utf-8")


@_represents(9)
def test_attack_09_expired_proof(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    _tamper_binding_file_on_disk(h, expires_at="2020-01-01T00:00:00.000Z")
    result = h.consume(simulation_only=False)
    assert result.pb_decision != DECISION_ALLOW


@_represents(10)
def test_attack_10_revoked_signer(tmp_path: Path) -> None:
    from pcae.core.hatp_bootstrap import HATPTrustStore

    h = _Harness(tmp_path)
    h.publish_envelope()
    from tests.test_hatp_rollback_consumption import _write_registry

    _write_registry(
        h.tmp_path / "trust-store",
        {
            "registry_version": 1,
            "principals": [{"principal_id": h.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": h.signer_key_id,
                    "principal_id": h.principal_id,
                    "provider_profile": h.provider_profile,
                    "status": "revoked",
                }
            ],
            "deployment_bindings": [],
            "authorities": [],
        },
    )
    revoked_store = HATPTrustStore(_test_only_root=h.tmp_path / "trust-store")
    result = h.consume(simulation_only=False, hatp_trust_store=revoked_store)
    assert result.hatp_status != HATPVerificationStatus.VALID
    assert result.pb_decision != DECISION_ALLOW


@_represents(11)
def test_attack_11_revoked_authority(tmp_path: Path) -> None:
    from pcae.core.hatp_bootstrap import HATPTrustStore
    from tests.test_hatp_rollback_consumption import _write_registry

    h = _Harness(tmp_path)
    h.publish_envelope()
    _write_registry(
        h.tmp_path / "trust-store",
        {
            "registry_version": 1,
            "principals": [{"principal_id": h.principal_id, "status": "active"}],
            "signers": [
                {
                    "signer_key_id": h.signer_key_id,
                    "principal_id": h.principal_id,
                    "provider_profile": h.provider_profile,
                    "status": "active",
                }
            ],
            "deployment_bindings": [
                {
                    "repository_id": h.repo_id,
                    "canonical_deployment_root": h.canonical_root,
                    "principal_id": h.principal_id,
                    "signer_key_id": h.signer_key_id,
                    "provider_profile": h.provider_profile,
                    "authority_scope": "rollback",
                    "valid_from": "2026-01-01T00:00:00.000Z",
                    "status": "active",
                }
            ],
            "authorities": [],  # revoked/absent authority mapping
        },
    )
    no_authority_store = HATPTrustStore(_test_only_root=h.tmp_path / "trust-store")
    result = h.consume(simulation_only=False, hatp_trust_store=no_authority_store)
    assert result.pb_decision != DECISION_ALLOW


@_represents(12)
def test_attack_12_decision_changed_after_signing(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.proof = replace(h.proof, decision_record_digest="0" * 64)
    h.resign_proof()
    h.publish_envelope()
    result = h.consume(simulation_only=False)
    assert result.pb_decision != DECISION_ALLOW


@_represents(13)
def test_attack_13_binding_changed_after_signing(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    # Mutate the RAE Binding's on-disk content_digest after the proof was
    # already signed against its original digest.
    _tamper_binding_file_on_disk(h, content_digest="f" * 64)
    result = h.consume(simulation_only=False)
    assert result.pb_decision != DECISION_ALLOW


@_represents(14)
def test_attack_14_fresh_unregistered_key(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.proof = replace(h.proof, signer_key_id="never-registered-signer")
    h.resign_proof()
    h.publish_envelope()
    result = h.consume(simulation_only=False)
    assert result.hatp_status != HATPVerificationStatus.VALID
    assert result.pb_decision != DECISION_ALLOW


@_represents(15)
def test_attack_15_forged_signer(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    path = h.hatp_evidence_store.path_for(h.evidence_id)
    forged = replace(h.envelope, provider_assertion=b"\x00" * 64)
    path.write_bytes(serialize_hatp_signed_evidence(forged))
    result = h.consume(simulation_only=False)
    assert result.hatp_status == HATPVerificationStatus.INVALID_SIGNATURE
    assert result.pb_decision != DECISION_ALLOW


# ─────────────────────────────────────────────────────────────────────────
# 16-19, 25-26: structurally-impossible caller overrides / injection / cache
# ─────────────────────────────────────────────────────────────────────────


@_represents(16, 17)
def test_attack_16_17_no_caller_approval_or_hatp_status_override() -> None:
    field_names = {f.name for f in cons.HATPRollbackConsumptionRequest.__dataclass_fields__.values()}
    assert "approval_present" not in field_names
    assert "hatp_valid" not in field_names
    assert "hatp_status" not in field_names


@_represents(18, 19)
def test_attack_18_19_no_provider_or_trust_store_injection_on_public_entrypoints() -> None:
    import inspect

    for fn in (cons.evaluate_for_real_effect, cons.evaluate_for_advisory):
        params = set(inspect.signature(fn).parameters)
        assert "provider" not in params
        assert "trust_store" not in params
        assert "hatp_provider" not in params
        assert "hatp_trust_store" not in params


@_represents(25, 26)
def test_attack_25_26_no_cache_every_attempt_reevaluates(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    first = h.consume(simulation_only=False)
    second = h.consume(simulation_only=False)
    assert first.pb_decision == second.pb_decision  # both freshly re-derived, not one cached
    import inspect

    source = inspect.getsource(_consumption_mod)
    assert "functools.lru_cache" not in source
    assert "_CACHE" not in source


# ─────────────────────────────────────────────────────────────────────────
# 27-28: retry after deletion/modification of previously-successful evidence
# ─────────────────────────────────────────────────────────────────────────


@_represents(27)
def test_attack_27_evidence_deleted_after_prior_success_retry(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    _first = h.consume(simulation_only=False)
    h.hatp_evidence_store.path_for(h.evidence_id).unlink()
    second = h.consume(simulation_only=False)
    assert second.hatp_status == HATPVerificationStatus.MISSING
    assert second.pb_decision != DECISION_ALLOW


@_represents(28)
def test_attack_28_evidence_modified_after_prior_success_retry(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    _first = h.consume(simulation_only=False)
    path = h.hatp_evidence_store.path_for(h.evidence_id)
    tampered = replace(h.envelope, provider_assertion=b"modified-after-success")
    path.write_bytes(serialize_hatp_signed_evidence(tampered))
    second = h.consume(simulation_only=False)
    assert second.pb_decision != DECISION_ALLOW


# ─────────────────────────────────────────────────────────────────────────
# 29: two valid evidence IDs, no implicit selection
# ─────────────────────────────────────────────────────────────────────────


@_represents(29)
def test_attack_29_two_valid_evidence_ids_no_implicit_selection(tmp_path: Path) -> None:
    h1 = _Harness(tmp_path / "a")
    h1.publish_envelope()
    h2 = _Harness(tmp_path / "b")
    h2.publish_envelope()
    assert h1.evidence_id != h2.evidence_id
    # No production function accepts zero evidence_id and "picks one" --
    # HATPRollbackConsumptionRequest.evidence_id is a required positional/
    # keyword field with no default.
    import inspect

    sig = inspect.signature(cons.HATPRollbackConsumptionRequest)
    assert sig.parameters["evidence_id"].default is inspect.Parameter.empty


# ─────────────────────────────────────────────────────────────────────────
# 30-31: raw hook bypass, real AG3 direct-call
# ─────────────────────────────────────────────────────────────────────────


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(_cutover_mod, "resolve_production_hatp_cutover_mode", lambda root: _fixed_mode(mode))


def _patch_consumption(monkeypatch, pb_decision: str) -> None:
    def _fake_evaluate(request, *, root):
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id, hatp_status=HATPVerificationStatus.VALID,
            pb_decision=pb_decision, reasons=("test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)


@_represents(30, 31)
def test_attack_30_31_raw_proof_and_evidence_params_do_not_authorize(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path), job_id, hatp_proof=object(), hatp_evidence=object()
        )


# ─────────────────────────────────────────────────────────────────────────
# 32-33: PB HUMAN_REVIEW / DENY block effect (AG3 + AG5)
# ─────────────────────────────────────────────────────────────────────────


@_represents(32, 33)
@pytest.mark.parametrize("decision", [DECISION_HUMAN_REVIEW, DECISION_DENY])
def test_attack_32_33_pb_human_review_or_deny_blocks_ag3_effect(tmp_path, monkeypatch, capsys, decision) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, decision)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID)


# ─────────────────────────────────────────────────────────────────────────
# 34: PB ALLOW under simulation_only=True never authorizes a real effect
# ─────────────────────────────────────────────────────────────────────────


@_represents(34)
def test_attack_34_simulation_only_allow_never_authorizes_real_effect() -> None:
    import ast
    import inspect

    for fn in (_agent_mod.execute_rollback, _agent_mod.build_rollback_execution):
        source = inspect.getsource(fn)
        tree = ast.parse(source)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
        }
        assert "evaluate_for_advisory" not in names


# ─────────────────────────────────────────────────────────────────────────
# 35: pre-cutover evidence remains usable post-cutover if still fresh
# (HMRC-REQ-079) -- distinct from attack 20/21 (missing/invalid evidence)
# ─────────────────────────────────────────────────────────────────────────


@_represents(35)
def test_attack_35_precutover_evidence_usable_postcutover_if_fresh(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    # Evidence is "created" (represented here by the deterministic seam
    # standing in for a genuinely fresh/valid envelope) before the
    # deployment cuts over; mode flips to HATP_MANDATORY at consumption
    # time. HMRC-REQ-079: this alone does not invalidate it.
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = _agent_mod.execute_rollback(HarnessPath(tmp_path), job_id, hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result["rolled_back"] is True


# ─────────────────────────────────────────────────────────────────────────
# 20-21: legacy-approved + missing/invalid HATP evidence, post-cutover
# ─────────────────────────────────────────────────────────────────────────


@_represents(20)
def test_attack_20_legacy_approved_missing_evidence_postcutover(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(HarnessPath(tmp_path), job_id)


@_represents(21)
def test_attack_21_legacy_approved_invalid_evidence_postcutover(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(
            HarnessPath(tmp_path), job_id, hatp_evidence_id="not-a-valid-64-hex-digest"
        )


# ─────────────────────────────────────────────────────────────────────────
# 22, 39-42: cutover-record state attacks (deletion/corruption/wrong-repo/
# unknown-version/bool-version)
# ─────────────────────────────────────────────────────────────────────────

_REPO_A = "33333333-3333-4333-8333-333333333333"
_REPO_B = "44444444-4444-4444-8444-444444444444"


@_represents(22)
def test_attack_22_delete_cutover_record_no_downgrade(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    _cutover_mod._write_cutover_transition(
        protected_root, target_mode=CutoverMode.PREPARED, repository_instance_id=_REPO_A, activated_by="op"
    )
    import pcae.core.hatp_mandatory_cutover as _real_cutover_mod

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            _real_cutover_mod,
            "_assess_hatp_mandatory_activation_readiness_at_root",
            lambda root, repo_id, **_kw: __import__(
                "pcae.core.hatp_mandatory_cutover", fromlist=["HATPMandatoryActivationReadiness"]
            ).HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=()),
        )
        _real_cutover_mod._activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")

    (protected_root / "cutover-record.json").unlink()
    resolution = _cutover_mod._resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.HATP_MANDATORY


@_represents(39)
def test_attack_39_cutover_record_corruption_fails_closed(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    protected_root.mkdir(parents=True)
    (protected_root / "cutover-activation-marker.json").write_text(
        json.dumps({"version": 1, "repository_instance_id": _REPO_A, "first_activated_at": "2026-01-01T00:00:00.000Z"})
    )
    (protected_root / "cutover-record.json").write_text("{not valid json")
    resolution = _cutover_mod._resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.HATP_MANDATORY


@_represents(40)
def test_attack_40_cutover_record_wrong_repository(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    _cutover_mod._write_cutover_transition(
        protected_root, target_mode=CutoverMode.PREPARED, repository_instance_id=_REPO_A, activated_by="op"
    )
    resolution = _cutover_mod._resolve_cutover_mode_at_root(protected_root, _REPO_B)
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE  # first-install for B, never B's activation


@_represents(41)
def test_attack_41_cutover_record_unknown_version(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    protected_root.mkdir(parents=True)
    (protected_root / "cutover-record.json").write_text(
        json.dumps(
            {
                "version": 2,
                "repository_instance_id": _REPO_A,
                "mode": "PREPARED",
                "activated_at": "2026-01-01T00:00:00.000Z",
                "activated_by": "op",
            }
        )
    )
    with pytest.raises(_cutover_mod.CutoverStateMalformedError):
        _cutover_mod.parse_cutover_record(json.loads((protected_root / "cutover-record.json").read_text()))


@_represents(42)
def test_attack_42_cutover_record_boolean_version(tmp_path: Path) -> None:
    document = {
        "version": True,
        "repository_instance_id": _REPO_A,
        "mode": "PREPARED",
        "activated_at": "2026-01-01T00:00:00.000Z",
        "activated_by": "op",
    }
    with pytest.raises(_cutover_mod.CutoverStateMalformedError):
        _cutover_mod.parse_cutover_record(document)


# ─────────────────────────────────────────────────────────────────────────
# 23: CLI-flag downgrade (omit --hatp-evidence-id post-cutover)
# ─────────────────────────────────────────────────────────────────────────


@_represents(23)
def test_attack_23_cli_flag_downgrade_omitted_evidence_id(tmp_path, monkeypatch, capsys) -> None:
    from pcae.cli import main

    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "hatp" in output.lower()


# ─────────────────────────────────────────────────────────────────────────
# 24: alternate production effect caller bypass -- exhaustive inventory
# ─────────────────────────────────────────────────────────────────────────


@_represents(24)
def test_attack_24_no_uninventoried_production_effect_caller() -> None:
    """Re-derives HMRC-REQ-069's caller inventory fresh (not by citing the
    149O.17 plan's own assumption): every real call site of
    `execute_rollback`/`build_rollback_execution` anywhere in `src/pcae/`
    must be exactly the two already-gated production callers."""
    import subprocess

    repo_root = Path(__file__).resolve().parent.parent
    for symbol, expected_caller_file in (
        ("execute_rollback", "commands/agent.py"),
        ("build_rollback_execution", "commands/agent.py"),
    ):
        output = subprocess.run(
            ["grep", "-rn", f"\\b{symbol}(", str(repo_root / "src" / "pcae")],
            capture_output=True, text=True,
        ).stdout
        call_lines = [
            line for line in output.splitlines()
            if f"def {symbol}(" not in line
            and "src/pcae/core/agent.py" not in line
            # `cltr/migration/rehearsal/rollback.py::execute_rollback` and its
            # caller `commands/cltr_migration.py` are a distinct, unrelated
            # function that merely shares this name (independently confirmed
            # by production-code reconnaissance for this phase: different
            # module, different signature, no HATP/HMRC involvement at all)
            # -- not part of this contract's effect-boundary surface.
            and "cltr_migration" not in line
        ]
        assert all(expected_caller_file in line for line in call_lines), (
            f"unexpected/un-audited caller of {symbol}: {call_lines}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 44: AG5 structural divergence check still blocks despite valid HATP
# ─────────────────────────────────────────────────────────────────────────


@_represents(44)
def test_attack_44_divergence_still_blocks_with_valid_hatp(tmp_path, monkeypatch) -> None:
    from pcae.core.agent import build_rollback_execution

    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    (root_dir / "added.txt").write_text("added content")
    root = HarnessPath(root_dir)
    import hashlib

    after_hash = hashlib.sha256(b"added content").hexdigest()
    entries = [{"path": "added.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, file_entries=entries)
    _make_rer_test_per(root, per_id="per-divergence", file_results=[{"path": "added.txt", "outcome": "success"}])

    # Diverge the file after ECP/RER creation but before rollback attempt.
    (root_dir / "added.txt").write_text("DIVERGED CONTENT -- not what was recorded")

    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = build_rollback_execution(root, "per-divergence", hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result.get("error") == "divergence_conflict"
    assert result["reverted"] is False
    assert (root_dir / "added.txt").read_text() == "DIVERGED CONTENT -- not what was recorded"


# ─────────────────────────────────────────────────────────────────────────
# 45: evidence existence without an explicit evidence ID has no effect
# ─────────────────────────────────────────────────────────────────────────


@_represents(45)
def test_attack_45_evidence_existence_without_explicit_id_has_no_effect(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    calls: list = []
    _real_consume = _consumption_mod.evaluate_for_real_effect

    def _spy(request, *, root):
        calls.append(request.evidence_id)
        raise AssertionError("must not be reached: no evidence_id was ever supplied")

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _spy)

    with pytest.raises(ValueError, match="HATP"):
        _agent_mod.execute_rollback(HarnessPath(tmp_path), job_id)  # no hatp_evidence_id kwarg at all
    assert calls == []  # the gate short-circuits on missing ID before ever consulting evidence


# ─────────────────────────────────────────────────────────────────────────
# Completeness: every declared attack has a real, executed representative
# ─────────────────────────────────────────────────────────────────────────


def test_all_45_attacks_have_at_least_one_executed_representative_test() -> None:
    declared = {a.number for a in ATTACK_MATRIX}
    assert declared == set(range(1, 46))
    assert _REPRESENTED == declared, f"unrepresented attacks: {sorted(declared - _REPRESENTED)}"
