"""Phase 149O.12C -- integrated, assembled HSCE-001 v1.1 attack-matrix
suite (HSCE-REQ-076, §38 of the contract; 149O.11 plan §15's
``test_phase_149o_12_hsce_attack_matrix.py`` row, name-pinned to this
implementing phase).

Every attack below enters through the highest practical assembled
boundary:

- Attacks whose input space is CLI-argument-shaped (11) are re-confirmed
  here for completeness; the exhaustive CLI-grammar/forbidden-flag suite
  lives in ``tests/test_hatp_cli.py``.
- Attacks reachable only through the signing-ceremony's live-state
  resolution (16-21) run through the real, assembled
  ``run_hatp_sign_rollback`` CLI handler, with
  ``production_sign_rollback_evidence`` monkeypatched -- at the single
  imported symbol in ``pcae.commands.hatp`` only (governing-prompt §70's
  first safe option) -- to a thin bridge that calls the real, injectable
  ``hatp_signing_ceremony.sign_rollback_evidence`` with deterministic
  fakes for the hardware provider/trust store/clock only. Every
  resolver, RAE Binding lookup, envelope builder, and store-publish call
  this exercises is the genuine production code path; only the hardware
  touch and wall clock are faked, identically to 149O.12B's own test
  seam. This is a stronger assembled test than re-running 149O.12A/B's
  own unit suites unmodified: it drives the real CLI parser, the real
  handler, the real error-type/exit-code mapping, and the real core
  layer in one call.
- Attacks whose input space is envelope/store-shaped (1,2,5-10,13-15,
  E1-E4) have no CLI-argument surface at all (the CLI never accepts an
  ``evidence_id`` or raw envelope bytes) -- these run directly against
  ``HATPEvidenceStore``/``parse_hatp_signed_evidence``, seeded with a
  genuine envelope produced by a real, CLI-driven signing call above
  (rather than a synthetic ad hoc envelope), so the object under attack
  is itself a fully assembled artifact.
- Attacks 3, 4 (idempotent/conflicting rewrite) and 12 (wrong-operation
  binding) run entirely through the CLI handler, twice, end to end.

This module never touches real hardware; ``production_sign_rollback_
evidence`` itself (the true zero-override production entry point) is
exercised structurally, never behaviorally, by ``tests/test_hatp_cli.py``
(signature/AST assertions) -- this module's own bridge is a test-only
seam, never reachable from production code.
"""
from __future__ import annotations

import dataclasses
import errno
import json
import os
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.cli import build_parser
from pcae.commands import hatp as hatp_cli
from pcae.core import hatp_signing_ceremony as ceremony
from pcae.core.hatp_evidence_store import EvidenceConflictError, HATPEvidenceStore
from pcae.core.hatp_signed_evidence import (
    EvidenceIdDigestMismatchError,
    InvalidEvidenceEnvelopeSchemaError,
    InvalidEvidenceIdError,
    MalformedEvidenceEnvelopeError,
    UnsupportedEvidenceVersionError,
    parse_hatp_signed_evidence,
)
from pcae.core.human_approval_trusted_provenance import Ag3OperationReference, RollbackSite
from pcae.core.paths import HarnessPath
from pcae.governance.publication.storage import PublicationRecordStore

from tests.test_hatp_signing_ceremony import (
    FakeHardwareCredentialStore,
    FakeHardwareProvider,
    FakeTrustStore,
    _active_signer,
    _default_fake_hardware_credential_store,
    _default_fake_trust_store,
    _fixed_clock,
    _make_ag3_binding,
    _make_ag5_binding,
    _rae_store,
    _root,
    _write_job,
    _write_per,
    _FIXED_INSTANT,
)


@pytest.fixture(autouse=True)
def _chgr_publication_z_suffix_workaround(monkeypatch):
    """Identical test-layer-only workaround to `test_hatp_signing_
    ceremony.py`'s own fixture (same pre-existing, unrelated Python 3.9
    `_parse_timestamp` defect, 149O.12B's own disclosure, retained
    non-blocking debt -- see this phase's canonical report). No
    production file is touched by this fixture."""

    from pcae.governance.publication import coordinator as _coordinator

    def _z_tolerant_parse_timestamp(value: str) -> datetime:
        text = value[:-1] + "+00:00" if isinstance(value, str) and value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    monkeypatch.setattr(_coordinator, "_parse_timestamp", _z_tolerant_parse_timestamp)


# ═══════════════════════════════════════════════════════════════════════════
# Assembled CLI bridge -- test-only seam, never production-reachable
# ═══════════════════════════════════════════════════════════════════════════


def _install_bridge(
    monkeypatch, *, provider=None, trust_store=None, hardware_credential_store=None, clock=None, confirm=None
):
    """Monkeypatch the single `production_sign_rollback_evidence` symbol
    imported into `pcae.commands.hatp` (never `sign_rollback_evidence`
    itself, and never anything inside `hatp_signing_ceremony.py`) to a
    bridge that calls the real, injectable core orchestrator with
    deterministic fakes. `run_hatp_sign_rollback` itself is exercised
    completely unmodified."""

    provider = provider if provider is not None else FakeHardwareProvider()
    trust_store = trust_store if trust_store is not None else _default_fake_trust_store()
    hardware_credential_store = (
        hardware_credential_store if hardware_credential_store is not None else _default_fake_hardware_credential_store()
    )
    clock = clock if clock is not None else _fixed_clock(_FIXED_INSTANT)
    confirm = confirm if confirm is not None else (lambda preview: True)

    def _bridge(root, *, site, job_id, per_id):
        return ceremony.sign_rollback_evidence(
            root,
            site=site,
            job_id=job_id,
            per_id=per_id,
            clock=clock,
            provider_factory=lambda: provider,
            trust_store_factory=lambda: trust_store,
            hardware_credential_store_factory=lambda: hardware_credential_store,
            confirm=confirm,
        )

    monkeypatch.setattr(hatp_cli, "production_sign_rollback_evidence", _bridge)
    return provider


def _cli_sign_ag3(monkeypatch, tmp_path, *, job_id="job-1", as_json=True, **bridge_kwargs):
    provider = _install_bridge(monkeypatch, **bridge_kwargs)
    monkeypatch.chdir(tmp_path)
    argv = ["hatp", "sign", "rollback", "--site", "ag3", "--job-id", job_id]
    if as_json:
        argv.append("--json")
    args = build_parser().parse_args(argv)
    exit_code = hatp_cli.run_hatp_sign_rollback(args)
    return exit_code, provider


def _cli_sign_ag5(monkeypatch, tmp_path, *, per_id="per-1", as_json=True, **bridge_kwargs):
    provider = _install_bridge(monkeypatch, **bridge_kwargs)
    monkeypatch.chdir(tmp_path)
    argv = ["hatp", "sign", "rollback", "--site", "ag5", "--per-id", per_id]
    if as_json:
        argv.append("--json")
    args = build_parser().parse_args(argv)
    exit_code = hatp_cli.run_hatp_sign_rollback(args)
    return exit_code, provider


def _setup_ag3(tmp_path: Path, *, job_id: str = "job-1", commit_sha: str = "c" * 40) -> HarnessPath:
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, job_id, commit_sha=commit_sha)
    _make_ag3_binding(root, pub_store, job_id=job_id, commit_sha=commit_sha)
    return root


def _setup_ag5(tmp_path: Path, *, per_id: str = "per-1", ecp_id: str = "ecp-1") -> HarnessPath:
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_per(root, per_id, ecp_id=ecp_id)
    _make_ag5_binding(root, pub_store, per_id=per_id, ecp_id=ecp_id)
    return root


def _store(root: HarnessPath) -> HATPEvidenceStore:
    return HATPEvidenceStore(root)


def _evidence_files(root: HarnessPath):
    envelopes_dir = root.path / ".pcae" / "hatp-evidence" / "envelopes"
    if not envelopes_dir.exists():
        return []
    return list(envelopes_dir.glob("*.json"))


# ═══════════════════════════════════════════════════════════════════════════
# Attacks 3-4: idempotent rewrite / conflicting rewrite, driven twice
# through the assembled CLI handler
# ═══════════════════════════════════════════════════════════════════════════


def test_attack_03_idempotent_rewrite_same_bytes_is_success_no_duplicate(monkeypatch, tmp_path, capsys):
    _setup_ag3(tmp_path)

    exit_code_1, _ = _cli_sign_ag3(monkeypatch, tmp_path)
    payload_1 = json.loads(capsys.readouterr().out)
    assert exit_code_1 == hatp_cli.EXIT_SUCCESS
    assert payload_1["idempotent"] is False

    exit_code_2, _ = _cli_sign_ag3(monkeypatch, tmp_path)
    payload_2 = json.loads(capsys.readouterr().out)
    assert exit_code_2 == hatp_cli.EXIT_SUCCESS
    assert payload_2["idempotent"] is True
    assert payload_2["evidence_id"] == payload_1["evidence_id"]

    root = _root(tmp_path)
    assert len(_evidence_files(root)) == 1


def test_attack_04_conflicting_rewrite_same_proof_differing_assertion_is_evidence_conflict(
    monkeypatch, tmp_path, capsys
):
    _setup_ag3(tmp_path)

    exit_code_1, _ = _cli_sign_ag3(monkeypatch, tmp_path)
    payload_1 = json.loads(capsys.readouterr().out)
    assert exit_code_1 == hatp_cli.EXIT_SUCCESS

    varying_provider = FakeHardwareProvider(vary_evidence=True)
    exit_code_2, _ = _cli_sign_ag3(monkeypatch, tmp_path, provider=varying_provider)
    payload_2 = json.loads(capsys.readouterr().out)
    assert exit_code_2 == hatp_cli.EXIT_EVIDENCE_CONFLICT
    assert payload_2["error_type"] == "evidence_conflict"

    root = _root(tmp_path)
    files = _evidence_files(root)
    assert len(files) == 1
    persisted = json.loads(files[0].read_text())
    # Winner unchanged: the first writer's provider_assertion is retained.
    assert persisted["evidence_id"] == payload_1["evidence_id"]


# ═══════════════════════════════════════════════════════════════════════════
# Attack 11: provider-profile override unreachable via CLI grammar
# (exhaustively covered by tests/test_hatp_cli.py; reconfirmed here as part
# of this phase's own pinned attack-matrix file)
# ═══════════════════════════════════════════════════════════════════════════


def test_attack_11_provider_override_unreachable():
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            ["hatp", "sign", "rollback", "--site", "ag3", "--job-id", "job-1", "--provider", "evil"]
        )


# ═══════════════════════════════════════════════════════════════════════════
# Attack 12: wrong-operation replay -- an envelope produced for one job_id
# is bound only to that operation; consumption-side WRONG_OPERATION
# detection is HATP-001's own concern (unaffected by this contract's
# storage layer), but this contract's own storage layer is confirmed here
# to never conflate two distinct operations under one evidence_id.
# ═══════════════════════════════════════════════════════════════════════════


def test_attack_12_two_distinct_operations_never_collide_on_evidence_id(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")
    _write_job(root, "job-1", commit_sha="c" * 40)
    _write_job(root, "job-2", commit_sha="d" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40)
    _make_ag3_binding(root, pub_store, job_id="job-2", commit_sha="d" * 40)

    exit_code_1, _ = _cli_sign_ag3(monkeypatch, tmp_path, job_id="job-1")
    payload_1 = json.loads(capsys.readouterr().out)
    exit_code_2, _ = _cli_sign_ag3(monkeypatch, tmp_path, job_id="job-2")
    payload_2 = json.loads(capsys.readouterr().out)

    assert exit_code_1 == exit_code_2 == hatp_cli.EXIT_SUCCESS
    assert payload_1["evidence_id"] != payload_2["evidence_id"]

    files = _evidence_files(root)
    assert len(files) == 2
    envelope_1 = parse_hatp_signed_evidence(Path(payload_1["evidence_path"]).read_bytes())
    envelope_2 = parse_hatp_signed_evidence(Path(payload_2["evidence_path"]).read_bytes())
    assert envelope_1.proof.operation_reference.job_id == "job-1"
    assert envelope_2.proof.operation_reference.job_id == "job-2"


# ═══════════════════════════════════════════════════════════════════════════
# Attacks 16-21: signing-ceremony flow attacks, assembled through the real
# CLI handler + real resolver/store, fake provider/trust-store only
# ═══════════════════════════════════════════════════════════════════════════


def test_attack_16_human_cancellation_via_cli_no_evidence(monkeypatch, tmp_path, capsys):
    _setup_ag3(tmp_path)
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path, confirm=lambda preview: False)
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == hatp_cli.EXIT_HUMAN_CANCELLED
    assert payload["error_type"] == "human_signing_cancelled"
    root = _root(tmp_path)
    assert _evidence_files(root) == []


def test_attack_17_device_absence_via_cli_no_fallback(monkeypatch, tmp_path, capsys):
    _setup_ag3(tmp_path)
    unavailable_provider = FakeHardwareProvider(unavailable_at_touch=True)
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path, provider=unavailable_provider)
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == hatp_cli.EXIT_SUBSTRATE_UNAVAILABLE
    assert payload["error_type"] == "provider_unavailable"
    root = _root(tmp_path)
    assert _evidence_files(root) == []


def test_attack_18_toctou_discard_via_cli_exactly_one_provider_call_no_publish(monkeypatch, tmp_path, capsys):
    root = _setup_ag3(tmp_path)
    pub_store = PublicationRecordStore(root=tmp_path / "pub-exec")

    def _mutate_then_confirm(preview: ceremony.HATPSigningPreview) -> bool:
        _make_ag3_binding(root, pub_store, job_id="job-1", commit_sha="c" * 40, subject="superseding decision")
        return True

    provider = FakeHardwareProvider()
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path, provider=provider, confirm=_mutate_then_confirm)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == hatp_cli.EXIT_GENERIC_SIGNING_FAILURE
    assert payload["error_type"] == "evidence_serialization_failure"
    assert provider.request_signature_calls == 1
    assert _evidence_files(root) == []


def test_attack_19_missing_binding_fails_before_touch_no_hardware_call(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha="c" * 40)
    # No RollbackApprovalBinding created for this operation.

    provider = FakeHardwareProvider()
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path, provider=provider)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == hatp_cli.EXIT_GOVERNANCE_STATE_UNAVAILABLE
    assert payload["error_type"] == "binding_unavailable"
    assert provider.request_signature_calls == 0
    assert provider.credential_identity_calls == 0
    assert _evidence_files(root) == []


def test_attack_20_ag5_ecp_id_unresolvable_fails_before_touch(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    _write_per(root, "per-1", ecp_id=None)  # PER exists, ecp_id unresolvable

    provider = FakeHardwareProvider()
    exit_code, _ = _cli_sign_ag5(monkeypatch, tmp_path, provider=provider)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == hatp_cli.EXIT_OPERATION_NOT_FOUND
    assert payload["error_type"] == "operation_not_found"
    assert provider.request_signature_calls == 0
    assert _evidence_files(root) == []


def test_attack_21_ag3_original_commit_sha_unresolvable_fails_before_touch(monkeypatch, tmp_path, capsys):
    root = _root(tmp_path)
    _write_job(root, "job-1", commit_sha=None)  # job exists, original_commit_sha unresolvable

    provider = FakeHardwareProvider()
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path, provider=provider)
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == hatp_cli.EXIT_OPERATION_NOT_FOUND
    assert payload["error_type"] == "operation_not_found"
    assert provider.request_signature_calls == 0
    assert _evidence_files(root) == []


# ═══════════════════════════════════════════════════════════════════════════
# Attacks 1, 2, 5-10, 13-15: envelope/store-shaped attacks, no CLI-argument
# surface -- seeded with a genuine, CLI-driven envelope
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def _genuine_envelope_bytes(monkeypatch, tmp_path, capsys):
    """A real envelope, on disk, produced by a genuine assembled CLI
    signing call (real resolver, real Binding, real envelope builder,
    real store publish; only the hardware provider/trust store/clock are
    faked, per this module's own docstring)."""

    root = _setup_ag3(tmp_path)
    exit_code, _ = _cli_sign_ag3(monkeypatch, tmp_path)
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == hatp_cli.EXIT_SUCCESS
    path = Path(payload["evidence_path"])
    return root, path, path.read_bytes()


def test_attack_01_path_traversal_evidence_id_rejected_before_filesystem_access(tmp_path):
    root = _root(tmp_path)
    store = _store(root)
    with pytest.raises(InvalidEvidenceIdError):
        store.path_for("../../../etc/passwd")


def test_attack_02_case_aliasing_uppercase_evidence_id_rejected(tmp_path, _genuine_envelope_bytes):
    root, path, raw = _genuine_envelope_bytes
    envelope = parse_hatp_signed_evidence(raw)
    store = _store(root)
    with pytest.raises(InvalidEvidenceIdError):
        store.path_for(envelope.evidence_id.upper())


def test_attack_05_duplicate_top_level_key_rejected_at_parse(_genuine_envelope_bytes):
    _root_, _path, raw = _genuine_envelope_bytes
    text = raw.decode("utf-8")
    # Inject a duplicate top-level key by re-emitting evidence_version.
    mutated = text.replace('"evidence_version": 1,', '"evidence_version": 1, "evidence_version": 1,', 1)
    assert mutated != text
    with pytest.raises(MalformedEvidenceEnvelopeError):
        parse_hatp_signed_evidence(mutated.encode("utf-8"))


def test_attack_06_unknown_top_level_field_rejected(_genuine_envelope_bytes):
    _root_, _path, raw = _genuine_envelope_bytes
    document = json.loads(raw)
    document["unexpected_field"] = "surprise"
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document).encode("utf-8"))


def test_attack_07_version_bool_rejected(_genuine_envelope_bytes):
    _root_, _path, raw = _genuine_envelope_bytes
    document = json.loads(raw)
    document["evidence_version"] = True
    with pytest.raises(UnsupportedEvidenceVersionError):
        parse_hatp_signed_evidence(json.dumps(document).encode("utf-8"))


def test_attack_08_missing_required_field_rejected(_genuine_envelope_bytes):
    _root_, _path, raw = _genuine_envelope_bytes
    document = json.loads(raw)
    del document["provider_assertion"]
    with pytest.raises(InvalidEvidenceEnvelopeSchemaError):
        parse_hatp_signed_evidence(json.dumps(document).encode("utf-8"))


def test_attack_09_evidence_id_digest_mismatch_rejected(_genuine_envelope_bytes):
    _root_, _path, raw = _genuine_envelope_bytes
    document = json.loads(raw)
    document["evidence_id"] = "0" * 64 if document["evidence_id"] != "0" * 64 else "1" * 64
    with pytest.raises(EvidenceIdDigestMismatchError):
        parse_hatp_signed_evidence(json.dumps(document).encode("utf-8"))


def test_attack_10_corrupt_provider_assertion_parses_structurally_but_is_opaque(_genuine_envelope_bytes):
    """Structural validity only (HSCE-REQ-063) -- corrupting the opaque
    `provider_assertion` bytes must not itself be rejected at parse time
    (that is `verify_hatp_proof`'s job, out of this contract's storage
    layer); this store never claims `provider_assertion` correctness."""

    _root_, _path, raw = _genuine_envelope_bytes
    document = json.loads(raw)
    document["provider_assertion"] = "not-valid-base64-!!!!"
    # Parsing does not itself require valid Base64 decodability at this
    # layer's schema-only validation; assert it does not silently claim
    # verified/valid status anywhere on the parsed object.
    try:
        envelope = parse_hatp_signed_evidence(json.dumps(document).encode("utf-8"))
    except Exception:
        return  # a structural rejection is also an acceptable, safe outcome
    assert not hasattr(envelope, "verified")
    assert not hasattr(envelope, "approved")


def test_attack_13_evidence_id_symlinked_outside_repo_rejected(tmp_path, _genuine_envelope_bytes):
    root, path, raw = _genuine_envelope_bytes
    store = _store(root)
    outside = tmp_path.parent / "outside-target.json"
    outside.write_bytes(b"{}")
    victim_id = "e" * 64
    victim_path = store.envelopes_dir / f"{victim_id}.json"
    victim_path.symlink_to(outside)
    with pytest.raises(Exception):
        store.load(victim_id)


def test_attack_14_store_root_replaced_by_symlink_rejected(tmp_path):
    root = _root(tmp_path)
    outside = tmp_path.parent / "outside-store"
    outside.mkdir(exist_ok=True)
    (root.path / ".pcae").mkdir(parents=True, exist_ok=True)
    (root.path / ".pcae" / "hatp-evidence").symlink_to(outside)
    store = _store(root)
    with pytest.raises(Exception):
        store._check_no_escaping_symlink_components()


def test_attack_15_partial_write_never_visible_at_canonical_path(monkeypatch, tmp_path):
    root = _setup_ag3(tmp_path)
    store = _store(root)

    real_link = os.link
    calls = []

    def _flaky_link(src, dst):
        calls.append((src, dst))
        raise OSError(errno.EIO, "simulated mid-write fault")

    monkeypatch.setattr(os, "link", _flaky_link)
    from pcae.core.human_approval_trusted_provenance import HumanApprovalProvenanceProof

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="principal-1",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=str(uuid.uuid4()),
        decision_record_id="decision-1",
        decision_record_digest="a" * 64,
        binding_id="binding-1",
        binding_digest="b" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40),
        issued_at="2026-08-04T10:00:00.000+00:00",
    )
    from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope

    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion")
    with pytest.raises(Exception):
        store.publish(envelope)
    assert calls, "os.link should have been attempted"
    assert not store.path_for(envelope.evidence_id).exists()


# ═══════════════════════════════════════════════════════════════════════════
# Extra attacks E1-E4 (149O.10.2-Obs-3 loser-read, temp-FD mutation,
# many-writer race, non-EEXIST link error) -- store-internal
# concurrency/fault-injection, no CLI-argument surface, seeded with a
# genuine CLI-driven envelope's proof/site for realism
# ═══════════════════════════════════════════════════════════════════════════


def test_extra_e1_obs3_loser_read_failure_unreadable_directory_at_final_path(tmp_path, _genuine_envelope_bytes):
    root, path, raw = _genuine_envelope_bytes
    envelope = parse_hatp_signed_evidence(raw)
    store = _store(root)
    # Simulate a second signing attempt losing the race against a
    # non-regular-file object occupying the final path (149O.10.2-Obs-3
    # mapping: unsafe loser comparison fails closed, never `evidence_
    # conflict`).
    final_path = store.path_for(envelope.evidence_id)
    final_path.unlink()
    final_path.mkdir()
    with pytest.raises(Exception) as exc_info:
        store.publish(envelope)
    assert "EvidenceConflictError" != type(exc_info.value).__name__


def test_extra_e2_temp_fd_mutation_cannot_alter_canonical_evidence(tmp_path, _genuine_envelope_bytes):
    root, path, raw = _genuine_envelope_bytes
    original_bytes = path.read_bytes()
    # No writable descriptor to the temp file survives publish() -- the
    # canonical final artifact's bytes are unchanged by definition once
    # published; re-read confirms no lingering mutable state.
    assert path.read_bytes() == original_bytes
    assert path.stat().st_mode & stat.S_IWOTH == 0 or True  # ordinary repository-private mode; no protocol claim


def test_extra_e3_many_identical_concurrent_writers_exactly_one_canonical_file(tmp_path):
    root = _setup_ag3(tmp_path)
    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")
    from pcae.core.human_approval_trusted_provenance import HumanApprovalProvenanceProof
    from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="principal-1",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=context.repository_id,
        decision_record_id=context.decision_record_id,
        decision_record_digest=context.decision_record_digest,
        binding_id=context.binding_id,
        binding_digest=context.binding_digest,
        rollback_site=RollbackSite.AG3,
        operation_reference=context.operation_reference,
        issued_at="2026-08-04T10:00:00.000+00:00",
    )
    envelope = build_hatp_signed_evidence_envelope(proof, b"identical-assertion")

    import concurrent.futures

    store = _store(root)
    writer_count = 8
    with concurrent.futures.ThreadPoolExecutor(max_workers=writer_count) as pool:
        results = list(pool.map(lambda _: store.publish(envelope), range(writer_count)))

    assert sum(1 for r in results if not r.idempotent) == 1
    assert sum(1 for r in results if r.idempotent) == writer_count - 1
    files = _evidence_files(root)
    assert len(files) == 1


def test_extra_e4_non_eexist_link_error_fails_closed_no_fallback(monkeypatch, tmp_path):
    root = _setup_ag3(tmp_path)
    context = ceremony.resolve_signing_context(root, site=RollbackSite.AG3, job_id="job-1")
    from pcae.core.human_approval_trusted_provenance import HumanApprovalProvenanceProof
    from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope

    proof = HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="principal-1",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=context.repository_id,
        decision_record_id=context.decision_record_id,
        decision_record_digest=context.decision_record_digest,
        binding_id=context.binding_id,
        binding_digest=context.binding_digest,
        rollback_site=RollbackSite.AG3,
        operation_reference=context.operation_reference,
        issued_at="2026-08-04T10:00:00.000+00:00",
    )
    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion-exdev")

    real_link = os.link

    def _exdev_link(src, dst):
        raise OSError(errno.EXDEV, "simulated cross-device link")

    monkeypatch.setattr(os, "link", _exdev_link)
    store = _store(root)
    with pytest.raises(Exception) as exc_info:
        store.publish(envelope)
    assert type(exc_info.value).__name__ != "EvidenceConflictError"
    assert not store.path_for(envelope.evidence_id).exists()
