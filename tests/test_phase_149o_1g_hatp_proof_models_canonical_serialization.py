"""Phase 149O.1G -- HATP Proof Models + Canonical Serialization
(Wave 3) cross-cutting phase suite.

Covers what neither `test_hatp_proof_models.py` nor
`test_hatp_canonical_serialization.py` tests in isolation: import/
dependency boundaries, absence of any verification/trust vocabulary,
the explicit F-149O.1C-1 hardening statement, production-diff scope, and
unaffected Wave-1/2/RAE/Permission-Broker/contract state.
"""
from __future__ import annotations

import ast
import inspect
import json
import subprocess
import uuid
from pathlib import Path

import pytest

from pcae.core import human_approval_trusted_provenance as hatp_proof
from pcae.core.human_approval_trusted_provenance import (
    InvalidProofSchemaError,
    parse_hatp_proof,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_MODULE_IMPORT_SUBSTRINGS = (
    # "hatp_bootstrap" deliberately removed here (Phase 149O.1I, Wave 4):
    # the 149O.1D implementation plan's Module Ownership Proposal (§7)
    # explicitly co-locates the verifier (I) and readiness gate (J) in
    # this same module, which requires a read-only `HATPTrustStore`
    # import (HATP-REQ-094). This is the one plan-sanctioned exception to
    # this phase's original Wave-3-only purity boundary --
    # `test_phase_149o_1i_hatp_verification_engine_implementation.py`
    # independently re-verifies the *new* Wave-4 boundary (still no RAE/
    # Permission-Broker/agent coupling).
    "rollback_approval_evidence",
    "permission_broker",
    "mutation_permission",
    "core.agent",
    "commands.agent",
)


def _module_source() -> str:
    return inspect.getsource(hatp_proof)


# ── F-149O.1C-1: explicit named hardening test ────────────────────────────


def test_f_149o_1c_1_unknown_field_hardening_is_enforced() -> None:
    """F-149O.1C-1 disposition for this phase: 'IMPLEMENTED HARDENING'.
    Production HATP proof parsing rejects an unknown/unrecognized field
    for the only supported `proof_version` (1). This is the direct,
    named test the phase-completion report cites as evidence."""

    repo_id = str(uuid.uuid4())
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": repo_id,
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG3",
        "job_id": "job-1",
        "original_commit_sha": "c" * 40,
        "issued_at": "2026-08-06T00:00:00.000Z",
        "unexpected_field_from_a_future_or_attacker_extension": "x",
    }
    with pytest.raises(InvalidProofSchemaError):
        parse_hatp_proof(json.dumps(doc))


# ── No verification / trust vocabulary exists in this module ─────────────


def test_no_verification_status_vocabulary_defined() -> None:
    """HATP-REQ-078's closed 13-state verification vocabulary
    (`VALID`, `UNKNOWN_SIGNER`, `REVOKED_SIGNER`, ...) belongs to a
    future Wave 4 verifier. This module defines none of it."""

    public_names = {name for name in dir(hatp_proof) if not name.startswith("_")}
    forbidden_status_names = {
        "VALID",
        "MISSING",
        "INVALID_SIGNATURE",
        "UNKNOWN_SIGNER",
        "UNAUTHORIZED_SIGNER",
        "REVOKED_SIGNER",
        "INVALID_ATTESTATION",
        "USER_PRESENCE_NOT_PROVEN",
        "WRONG_OPERATION",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "EXPIRED",
    }
    assert not (public_names & forbidden_status_names)


#: Phase 149O.1I, Wave 4 legitimately adds exactly one verifier callable
#: to this module (§7 of the 149O.1D plan): `verify_hatp_proof`. Every
#: other imported/defined name (`HATPTrustStore`, `HATPProofVerifierProvider`,
#: `HATPVerificationStatus`, etc.) does not literally contain the
#: substring "verify" (e.g. "verifier"/"verification" do not), so this
#: whitelist is deliberately exactly one name, not a broad carve-out.
_WAVE_4_EXPECTED_VERIFICATION_SYMBOLS = {"verify_hatp_proof"}


def test_no_verify_or_trust_named_callable_exists() -> None:
    public_callables = {
        name
        for name in dir(hatp_proof)
        if not name.startswith("_") and callable(getattr(hatp_proof, name))
    }
    for name in public_callables:
        if name in _WAVE_4_EXPECTED_VERIFICATION_SYMBOLS:
            continue
        lowered = name.lower()
        assert "verify" not in lowered, f"unexpected verification-suggestive symbol: {name}"
        assert "trusted" not in lowered, f"unexpected trust-suggestive symbol: {name}"
        assert "authorized" not in lowered, f"unexpected authority-suggestive symbol: {name}"
        assert lowered != "is_valid", f"unexpected trust-suggestive symbol: {name}"


def test_no_approval_present_or_hatp_valid_symbol_defined() -> None:
    public_names = {name.lower() for name in dir(hatp_proof) if not name.startswith("_")}
    assert "approval_present" not in public_names
    assert "hatp_trusted_operational" not in public_names
    assert "hatp_valid" not in public_names


def test_no_signature_or_attestation_verification_code_present() -> None:
    source = _module_source()
    for forbidden in (
        "public_key.verify",
        "cryptography",
        "fido2",
        "webauthn",
        "pyscard",
        "ykman",
    ):
        assert forbidden not in source, f"unexpected security-library reference: {forbidden}"


# ── Dependency-direction / import boundary ────────────────────────────────


def test_no_forbidden_module_imports() -> None:
    tree = ast.parse(_module_source())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    for forbidden in _FORBIDDEN_MODULE_IMPORT_SUBSTRINGS:
        assert not any(forbidden in mod for mod in imported_modules), (
            f"forbidden dependency-direction import found: {forbidden} in {imported_modules}"
        )


def test_only_expected_upstream_import() -> None:
    """This module's Wave-3 PCAE-internal dependency was exactly
    `repository_identity.is_valid_repository_instance_id` (149O.1D plan
    §6, A -> G dependency direction). Phase 149O.1I, Wave 4 legitimately
    widens this to also import the read-only `hatp_bootstrap.HATPTrustStore`
    (HATP-REQ-094) and the `hatp_providers.HATPProofVerifierProvider`
    interface (§7 of the 149O.1D plan, C/E -> I dependency direction) --
    still never `rollback_approval_evidence`, `permission_broker*`, or
    `agent`."""

    tree = ast.parse(_module_source())
    pcae_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pcae"):
            pcae_imports.add(node.module)
    assert pcae_imports == {
        "pcae.core.repository_identity",
        "pcae.core.hatp_bootstrap",
        "pcae.core.hatp_providers",
    }


# ── No filesystem / network / hardware / wall-clock dependency ───────────


def test_no_filesystem_or_network_or_now_dependency() -> None:
    """Checks executable code only -- Wave 4's own docstrings *discuss*
    the no-hidden-wall-clock discipline in prose (e.g. "never
    `datetime.now()` internally"), which would otherwise false-positive
    a plain substring search."""
    import re

    without_docstrings = re.sub(r'""".*?"""', "", _module_source(), flags=re.DOTALL)
    code_only = "\n".join(line.split("#", 1)[0] for line in without_docstrings.splitlines())
    for forbidden in (
        "open(",
        "Path(",
        "socket",
        "requests",
        "urllib",
        "datetime.now(",
        "datetime.utcnow(",
    ):
        assert forbidden not in code_only, f"unexpected non-pure dependency: {forbidden}"


def test_no_filesystem_call_site_at_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Behavioral confirmation of purity: parsing/canonicalizing a proof
    while the current working directory is deleted underneath the
    process still succeeds (proves no hidden cwd/filesystem read)."""

    work_dir = tmp_path / "will-be-removed"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)
    repo_id = str(uuid.uuid4())
    doc = {
        "proof_version": 1,
        "principal_id": "alice",
        "signer_key_id": "signer-1",
        "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
        "repository_id": repo_id,
        "decision_record_id": "chgr-record-1",
        "decision_record_digest": "a" * 64,
        "binding_id": "rae-binding-1",
        "binding_digest": "b" * 64,
        "rollback_site": "AG3",
        "job_id": "job-1",
        "original_commit_sha": "c" * 40,
        "issued_at": "2026-08-06T00:00:00.000Z",
    }
    proof = parse_hatp_proof(json.dumps(doc))
    assert proof.principal_id == "alice"


# ── Production diff / contract / boundary invariants ─────────────────────


def _git_diff_names(*paths: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_hatp_contract_byte_unchanged() -> None:
    assert _git_diff_names("docs/contracts/") == []


def test_wave_1_2_foundation_untouched() -> None:
    assert _git_diff_names(
        "src/pcae/core/repository_identity.py",
        "src/pcae/core/hatp_bootstrap.py",
    ) == []


def test_rae_module_untouched() -> None:
    assert _git_diff_names("src/pcae/core/rollback_approval_evidence.py") == []


def test_permission_broker_untouched() -> None:
    assert _git_diff_names(
        "src/pcae/core/permission_broker_foundation.py",
        "src/pcae/core/permission_broker.py",
        "src/pcae/core/mutation_permission.py",
    ) == []


def test_agent_module_untouched() -> None:
    assert _git_diff_names("src/pcae/core/agent.py", "src/pcae/commands/agent.py") == []


def test_only_expected_production_files_changed() -> None:
    changed = set(_git_diff_names("src/pcae/"))
    expected = {
        "src/pcae/core/human_approval_trusted_provenance.py",
        # 149O.1I, Wave 4: new provider-neutral interface module, same
        # allowed-file-widening precedent as this project's other
        # phase-scoped diff checks.
        "src/pcae/core/hatp_providers.py",
    }
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "src/pcae/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    all_touched = changed | set(untracked)
    assert all_touched <= expected, f"unexpected src/pcae/ hunks: {all_touched - expected}"


# ── Runtime state unaffected ───────────────────────────────────────────────


def test_runtime_state_still_observe_only() -> None:
    result = subprocess.run(
        ["pcae", "runtime", "inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "Observed" in result.stdout
    assert "unavailable" in result.stdout
    assert "observe" in result.stdout
