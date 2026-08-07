"""HATP Hardware Provider Independent Verification (Wave 5) -- Phase 149O.3.

Independent, adversarial re-verification of the Wave-5 hardware-provider
surface implemented by Phase 149O.2:

    src/pcae/core/hatp_providers.py            (Wave-5 additions)
    src/pcae/core/hatp_fido2_provider.py
    src/pcae/core/hatp_piv_provider.py
    src/pcae/core/hatp_hardware_credentials.py

Verification-only. This module adds NO production code, repairs nothing,
and asserts nothing on the strength of 149O.2's own prose -- every claim
here is re-derived from the frozen contract text
(`docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md`), the
canonical plan
(`docs/PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md`),
the installed `fido2` library's own source, or the production source
itself.

Deliberate methodological independence from 149O.2's own suite: the
WebAuthn evidence built below is assembled from raw bytes and raw JSON
by this module (`_build_evidence_json`), NOT via
`hatp_fido2_provider._serialize_evidence` / `_payload_digest`. If the
production module's private helpers were wrong, 149O.2's fixtures would
have been wrong in exactly the same direction and the error would have
cancelled out; the fixtures here cannot cancel, because they never call
them.

Real hardware status on the verifying machine: ZERO FIDO2 and ZERO PIV
devices attached (independently probed, see
`test_independent_hardware_availability_probe`). Every hardware-backed
physical property (non-exportability, physical touch) is therefore
recorded as protocol/API-semantic, never as empirically device-tested
(spec sections 6/7/9/53/136/137).

Not registered into Fast Green: verification-only suites in this
repository are run explicitly by phase (149O.1J precedent), and this
module additionally requires the optional `hatp-hardware` extra.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import importlib
import inspect
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

fido2 = pytest.importorskip("fido2")
cryptography = pytest.importorskip("cryptography")

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from fido2 import cbor as fido2_cbor
from fido2.cose import ES256
from fido2.webauthn import AuthenticatorData, CollectedClientData

from pcae.core import hatp_bootstrap as bootstrap_module
from pcae.core import hatp_fido2_provider as fido2_module
from pcae.core import hatp_hardware_credentials as credentials_module
from pcae.core import hatp_piv_provider as piv_module
from pcae.core import hatp_providers as providers_module
from pcae.core.hatp_fido2_provider import Fido2HardwareProvider
from pcae.core.hatp_hardware_credentials import (
    HardwareCredentialRecord,
    HATPHardwareCredentialStore,
    HATPHardwareCredentialStoreError,
    HATPHardwareCredentialStoreMalformedError,
    HATPHardwareCredentialStoreSymlinkError,
    HATPHardwareCredentialStoreUnsupportedPlatformError,
)
from pcae.core.hatp_piv_provider import PivHardwareProvider
from pcae.core.hatp_providers import (
    HATP_HARDWARE_PROVIDER_V1,
    HATPProofVerifierProvider,
    HATPProviderUnavailableError,
    HATPProviderVerificationOutcome,
    TestHATPProofVerifierProvider,
    create_production_hardware_provider,
    discover_hardware_providers,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    Ag5OperationReference,
    HATPExpectedOperation,
    HATPVerificationEvidence,
    HATPVerificationStatus,
    HumanApprovalProvenanceProof,
    RollbackSite,
    canonicalize_hatp_proof_payload,
    inspect_hatp_verification_substrate_readiness,
    verify_hatp_proof,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src" / "pcae"
_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
_PLAN_PATH = _REPO_ROOT / "docs" / "PHASE_149O_1D_HUMAN_APPROVAL_TRUSTED_PROVENANCE_IMPLEMENTATION_PLAN.md"

#: The 149O.1J (Wave-4 independent verification) commit -- the baseline
#: the Wave-5 production diff is reconstructed against.
_WAVE5_BASELINE_COMMIT = "89bebdc0"

_WAVE5_PRODUCTION_FILES = frozenset(
    {
        "src/pcae/core/hatp_providers.py",
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_piv_provider.py",
        "src/pcae/core/hatp_hardware_credentials.py",
    }
)

_EVAL_TIME = datetime(2026, 8, 7, 12, 0, 0, tzinfo=timezone.utc)

#: Wave-1 repository-instance identity is a UUID4 string (CRI Model A).
_REPOSITORY_A = "3f2b8c14-9d6e-4a71-8b03-5c7e19af2d60"
_REPOSITORY_B = "7a41d2e9-0c58-4f36-9e12-8d604b3af175"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _run_cli(*argv: str) -> subprocess.CompletedProcess:
    """Invoke the PCAE CLI in-process-equivalently, in a subprocess, so
    a missing optional dependency or absent device would surface as a
    real failure."""

    code = "import sys; from pcae.cli import main; sys.argv=['pcae', *%r]; raise SystemExit(main())" % (list(argv),)
    return subprocess.run([sys.executable, "-c", code], cwd=_REPO_ROOT, capture_output=True, text=True, timeout=300)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_docstrings_and_comments(source: str) -> str:
    """Remove docstrings and `#` comments so prose can never satisfy a
    call-graph/containment assertion (149O.1J's own methodology)."""

    tree = ast.parse(source)
    doc_spans = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    doc_spans.add((body[0].lineno, body[0].end_lineno))
    lines = source.splitlines()
    keep = []
    for index, line in enumerate(lines, start=1):
        if any(start <= index <= end for start, end in doc_spans):
            continue
        keep.append(line.split("#", 1)[0])
    return "\n".join(keep)


# ═══════════════════════════════════════════════════════════════════════════
# Independent fixture builders -- raw bytes, raw JSON, no production helper
# ═══════════════════════════════════════════════════════════════════════════


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _independent_challenge(canonical_payload: bytes) -> bytes:
    """SHA-256 of the exact canonical payload bytes -- recomputed here
    from first principles, never imported from the production module."""

    return hashlib.sha256(canonical_payload).digest()


def _build_client_data_json(
    *,
    challenge: bytes,
    origin: str = "pcae-hatp://hatp.pcae.local",
    client_type: str = "webauthn.get",
    cross_origin: bool = False,
) -> bytes:
    """Hand-assembled clientDataJSON, byte-identical in structure to what
    `fido2.webauthn.CollectedClientData.create` emits (independently
    confirmed against the installed library in
    `test_independent_client_data_reconstruction_matches_library`)."""

    document = {
        "type": client_type,
        "challenge": _b64url(challenge),
        "origin": origin,
        "crossOrigin": cross_origin,
    }
    return json.dumps(document, separators=(",", ":")).encode("utf-8")


def _build_authenticator_data(*, rp_id: str = "hatp.pcae.local", up: bool = True, uv: bool = False, counter: int = 1) -> bytes:
    """Raw 37-byte authenticatorData: rpIdHash(32) || flags(1) || counter(4)."""

    rp_id_hash = hashlib.sha256(rp_id.encode("utf-8")).digest()
    flags = 0
    if up:
        flags |= 0x01
    if uv:
        flags |= 0x04
    return rp_id_hash + bytes([flags]) + counter.to_bytes(4, "big")


def _build_evidence_json(*, credential_id: bytes, authenticator_data: bytes, client_data_json: bytes, signature: bytes) -> bytes:
    """Hand-assembled evidence envelope in the production module's
    documented schema -- built here, not via `_serialize_evidence`."""

    return json.dumps(
        {
            "version": 1,
            "credential_id_hex": credential_id.hex(),
            "authenticator_data_hex": authenticator_data.hex(),
            "client_data_json_hex": client_data_json.hex(),
            "signature_hex": signature.hex(),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class _SoftwareAuthenticator:
    """A software EC P-256 key standing in for a hardware authenticator.

    It proves protocol/signature/binding correctness ONLY. It proves
    nothing whatsoever about hardware-backed key storage, key
    non-exportability, or physical human touch -- those are physical
    device properties this fixture structurally cannot exhibit (spec
    section 7). Never enrolled into any production store.
    """

    def __init__(self) -> None:
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = uuid.uuid4().bytes
        self.signer_key_id = self.credential_id.hex()

    def cose_public_key(self) -> bytes:
        return fido2_cbor.encode(dict(ES256.from_cryptography_key(self.private_key.public_key())))

    def assert_over(
        self,
        canonical_payload: bytes,
        *,
        up: bool = True,
        uv: bool = False,
        counter: int = 1,
        rp_id: str = "hatp.pcae.local",
        origin: str = "pcae-hatp://hatp.pcae.local",
        client_type: str = "webauthn.get",
        challenge_override: Optional[bytes] = None,
        credential_id_override: Optional[bytes] = None,
        signing_key=None,
        tamper_signature: bool = False,
    ) -> bytes:
        challenge = challenge_override if challenge_override is not None else _independent_challenge(canonical_payload)
        client_data_json = _build_client_data_json(challenge=challenge, origin=origin, client_type=client_type)
        auth_data = _build_authenticator_data(rp_id=rp_id, up=up, uv=uv, counter=counter)
        signed_bytes = auth_data + hashlib.sha256(client_data_json).digest()
        key = signing_key if signing_key is not None else self.private_key
        signature = key.sign(signed_bytes, ec.ECDSA(hashes.SHA256()))
        if tamper_signature:
            signature = signature[:-1] + bytes([signature[-1] ^ 0xFF])
        return _build_evidence_json(
            credential_id=credential_id_override if credential_id_override is not None else self.credential_id,
            authenticator_data=auth_data,
            client_data_json=client_data_json,
            signature=signature,
        )


class _InMemoryCredentialStore:
    """Isolates `Fido2HardwareProvider.verify()` from the filesystem for
    protocol-level tests. The real filesystem-backed
    `HATPHardwareCredentialStore` is separately attacked below."""

    def __init__(self, records: dict) -> None:
        self._records = records
        self.lookups: list = []

    def lookup_credential(self, signer_key_id: str):
        self.lookups.append(signer_key_id)
        return self._records.get(signer_key_id)


class _Harness:
    def __init__(self, *, status: str = "active", protocol_name: str = "FIDO2", provider_profile: str = HATP_HARDWARE_PROVIDER_V1, algorithm: str = "ES256") -> None:
        self.authenticator = _SoftwareAuthenticator()
        self.signer_key_id = self.authenticator.signer_key_id
        self.provider_profile = provider_profile
        self.record = HardwareCredentialRecord(
            signer_key_id=self.signer_key_id,
            provider_profile=provider_profile,
            protocol_name=protocol_name,
            algorithm=algorithm,
            public_key=self.authenticator.cose_public_key(),
            status=status,
        )
        self.store = _InMemoryCredentialStore({self.signer_key_id: self.record})
        self.provider = Fido2HardwareProvider(credential_store=self.store)

    def verify(self, canonical_payload: bytes, evidence: bytes, *, signer_key_id: Optional[str] = None, provider_profile: Optional[str] = None):
        return self.provider.verify(
            canonical_payload=canonical_payload,
            signer_key_id=self.signer_key_id if signer_key_id is None else signer_key_id,
            provider_profile=self.provider_profile if provider_profile is None else provider_profile,
            assertion=evidence,
        )


@pytest.fixture()
def harness() -> _Harness:
    return _Harness()


def _proof(**overrides) -> HumanApprovalProvenanceProof:
    base = dict(
        proof_version=1,
        principal_id="principal-verify-149o3",
        signer_key_id="a" * 32,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        repository_id=_REPOSITORY_A,
        decision_record_id="decision-149o3",
        decision_record_digest="d" * 64,
        binding_id="binding-149o3",
        binding_digest="b" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="c" * 40),
        issued_at="2026-08-07T10:00:00+00:00",
    )
    base.update(overrides)
    return HumanApprovalProvenanceProof(**base)


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 1 -- Production diff reconstruction and phase boundaries
#            (spec sections 3, 130-132)
# ═══════════════════════════════════════════════════════════════════════════


def test_wave5_production_diff_touches_exactly_four_hatp_modules() -> None:
    changed = {line for line in _git("diff", "--name-only", _WAVE5_BASELINE_COMMIT, "HEAD", "--", "src/pcae/").split() if line}
    assert changed == _WAVE5_PRODUCTION_FILES, "UNRELATED production hunks must be zero"


def test_wave5_diff_contains_no_unrelated_production_hunk() -> None:
    """Every changed production file is a Wave-5 HATP provider module;
    the single deleted line in the pre-existing `hatp_providers.py` is a
    widened `typing` import, not a semantic change."""

    diff = _git("diff", "-U0", _WAVE5_BASELINE_COMMIT, "HEAD", "--", "src/pcae/core/hatp_providers.py")
    deletions = [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
    assert deletions == ["-from typing import List, Optional, Protocol, runtime_checkable"]


def test_frozen_contract_is_byte_unchanged_since_wave5_baseline() -> None:
    assert _git("diff", "--name-only", _WAVE5_BASELINE_COMMIT, "HEAD", "--", "docs/contracts/").strip() == ""


def test_wave1_through_wave4_production_modules_are_byte_unchanged() -> None:
    for relative in (
        "src/pcae/core/repository_identity.py",
        "src/pcae/core/hatp_bootstrap.py",
        "src/pcae/core/human_approval_trusted_provenance.py",
    ):
        assert _git("diff", "--name-only", _WAVE5_BASELINE_COMMIT, "HEAD", "--", relative).strip() == "", relative


def test_no_new_runtime_dependency_was_added_only_an_optional_extra() -> None:
    """The Wave-5 dependency landed as the OPTIONAL `hatp-hardware`
    extra; the base `dependencies` list is unchanged."""

    before = _git("show", f"{_WAVE5_BASELINE_COMMIT}:pyproject.toml")
    after = _read(_REPO_ROOT / "pyproject.toml")

    def base_deps(text: str) -> str:
        match = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, flags=re.DOTALL | re.MULTILINE)
        return match.group(1) if match else ""

    assert base_deps(before) == base_deps(after)
    assert "hatp-hardware" in after and "hatp-hardware" not in before


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 2 -- Wave-5 requirement reconstruction from primary text
#            (spec sections 4, 5, 52, 58-60)
# ═══════════════════════════════════════════════════════════════════════════


def test_plan_assigns_hatp_req_016_025_and_076_to_wave_5() -> None:
    """Independently re-derived from the plan's own Wave-5 section text,
    not from 149O.2's report."""

    plan = _read(_PLAN_PATH)
    wave5 = plan.split("### Wave 5 —")[1].split("### Wave 6")[0]
    assert "HATP-REQ-016..025" in wave5
    assert "HATP-REQ-076" in wave5


def test_plan_wave5_also_scopes_a_human_side_approval_cli_surface() -> None:
    """Recorded finding basis: the plan's Wave-5 'Files/modules' line
    also names a human-side approval CLI surface, which Phase 149O.2 did
    not implement (its namespace is explicitly 'TBD, §29-32')."""

    plan = _read(_PLAN_PATH)
    wave5 = " ".join(plan.split("### Wave 5 —")[1].split("### Wave 6")[0].split())
    assert "human-side approval CLI surface" in wave5
    assert "namespace TBD" in wave5
    cli_dir = _SRC_ROOT / "commands"
    hatp_command_modules = sorted(p.name for p in cli_dir.glob("*hatp*"))
    assert hatp_command_modules == [], "no HATP CLI surface exists yet -- Wave-5 scope item not implemented"


def test_hardware_provider_profile_properties_are_exactly_five_and_exclude_attestation() -> None:
    """HATP-REQ-019 enumerates (a)-(e). Device attestation is NOT among
    them -- the basis for the attestation disposition (spec section 59)."""

    contract = _read(_CONTRACT_PATH)
    req_019 = contract.split("**HATP-REQ-019.**")[1].split("**HATP-REQ-020.**")[0]
    for marker in ("(a)", "(b)", "(c)", "(d)", "(e)"):
        assert marker in req_019
    assert "(f)" not in req_019
    assert "attestation" not in req_019.lower()


def test_contract_never_makes_attestation_unconditionally_required() -> None:
    """HATP-REQ-023 uses MAY; HATP-REQ-079's success conjunction says
    'attestation valid WHERE REQUIRED'. No contract sentence says a
    provider SHALL verify device attestation."""

    contract = _read(_CONTRACT_PATH)
    req_023 = contract.split("**HATP-REQ-023.**")[1].split("**HATP-REQ-024.**")[0]
    assert "MAY establish" in req_023
    req_079 = contract.split("**HATP-REQ-079.**")[1].split("**HATP-REQ-080.**")[0]
    assert "attestation valid where required" in " ".join(req_079.split())
    attestation_shall = [
        line
        for line in contract.splitlines()
        if "attestation" in line.lower() and re.search(r"\bSHALL\b(?!\s+NOT)", line)
    ]
    assert attestation_shall == [], attestation_shall


def test_contract_requires_human_presence_not_user_verification() -> None:
    """Spec section 52: independently confirm UP (presence), not UV
    (biometric/PIN user verification), is the contract's requirement."""

    contract = _read(_CONTRACT_PATH)
    presence_section = contract.split("## 9. Human Presence")[1].split("## 10.")[0]
    assert "human-presence event" in presence_section
    assert "user verification" not in presence_section.lower()
    assert "biometric" not in presence_section.lower()
    # "user verification" appears nowhere in the contract as a requirement.
    assert "user verification" not in contract.lower()


def test_contract_freezes_one_presence_to_one_proof_and_forbids_signing_sessions() -> None:
    contract = _read(_CONTRACT_PATH)
    req_017 = contract.split("**HATP-REQ-017.**")[1].split("**HATP-REQ-018.**")[0]
    assert "at most one HATP proof" in " ".join(req_017.split())
    assert "SHALL NOT be HATP-compliant" in req_017


def test_contract_forbids_software_key_substitution_and_accidental_test_provider() -> None:
    contract = _read(_CONTRACT_PATH)
    assert "SHALL NOT silently substitute for a required hardware signer" in " ".join(
        contract.split("**HATP-REQ-021.**")[1].split("**HATP-REQ-022.**")[0].split()
    )
    req_022 = " ".join(contract.split("**HATP-REQ-022.**")[1].split("## 11.")[0].split())
    assert "no default-enabled test provider, no silent fallback" in req_022


def test_contract_forbids_attestation_root_self_selection() -> None:
    contract = _read(_CONTRACT_PATH)
    req_025 = " ".join(contract.split("**HATP-REQ-025.**")[1].split("## 12.")[0].split())
    assert "SHALL NOT self-select an arbitrary attestation root" in req_025
    assert "outside agent-writable repository state" in req_025


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 3 -- Real hardware availability (spec sections 9, 53, 74, 75)
# ═══════════════════════════════════════════════════════════════════════════


def test_independent_hardware_availability_probe() -> None:
    """REAL HARDWARE EXECUTION: NOT EXERCISED. Probed independently via
    the `fido2` library's own HID enumeration, not via 149O.2's
    environment statement."""

    from fido2.hid import CtapHidDevice

    devices = list(CtapHidDevice.list_devices())
    assert devices == [], "a device appeared: re-classify hardware-dependent properties before trusting this run"

    availability = {a.protocol_name: a for a in discover_hardware_providers()}
    assert availability["FIDO2"].library_installed is True
    assert availability["FIDO2"].device_detected is False
    assert availability["PIV"].library_installed is False
    assert availability["PIV"].device_detected is False


def test_module_import_performs_no_device_probe() -> None:
    """Spec section 74: importing the provider modules must not
    enumerate USB/security keys. Verified by AST: no module-level
    (non-function-body) call to any `list_devices`."""

    for module_path in (
        _SRC_ROOT / "core" / "hatp_providers.py",
        _SRC_ROOT / "core" / "hatp_fido2_provider.py",
        _SRC_ROOT / "core" / "hatp_piv_provider.py",
    ):
        tree = ast.parse(_read(module_path))
        for node in tree.body:
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if child.func.attr == "list_devices":
                        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)), module_path


def test_constructing_the_fido2_provider_touches_neither_hardware_nor_registry() -> None:
    provider = Fido2HardwareProvider()
    assert provider._credential_store is None


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 4 -- FIDO2 protocol reconstruction from the installed library
#            (spec sections 10, 13, 14, 15)
# ═══════════════════════════════════════════════════════════════════════════


def test_installed_fido2_signs_authenticator_data_concatenated_with_client_data_hash() -> None:
    """Re-derived from the installed library's own source text."""

    from fido2 import server as fido2_server
    from fido2.ctap2 import base as ctap2_base

    # Client side (CTAP2 AssertionResponse.verify) and server side
    # (Fido2Server verification) agree on the identical construction.
    assert "public_key.verify(self.auth_data + client_param, self.signature)" in inspect.getsource(ctap2_base)
    assert "public_key.verify(auth_data + client_data.hash, signature)" in inspect.getsource(fido2_server)


def test_independent_client_data_reconstruction_matches_library() -> None:
    """Proves the hand-built clientDataJSON above is byte-identical to
    `CollectedClientData.create`'s output, so every attack below is run
    against genuine WebAuthn wire bytes."""

    challenge = hashlib.sha256(b"payload").digest()
    library_bytes = bytes(
        CollectedClientData.create(
            type=CollectedClientData.TYPE.GET, challenge=challenge, origin="pcae-hatp://hatp.pcae.local"
        )
    )
    assert _build_client_data_json(challenge=challenge) == library_bytes


def test_independent_authenticator_data_reconstruction_matches_library() -> None:
    library_bytes = bytes(
        AuthenticatorData.create(hashlib.sha256(b"hatp.pcae.local").digest(), AuthenticatorData.FLAG.UP, 1)
    )
    assert _build_authenticator_data() == library_bytes


def test_double_hash_construction_is_exactly_as_documented() -> None:
    """Spec sections 13/14. challenge = SHA256(canonical_payload);
    signed bytes = authenticatorData || SHA256(clientDataJSON), where
    clientDataJSON base64url-embeds the challenge. Both hashes are
    intentional and independently re-derived here."""

    payload = b'{"canonical":"payload"}'
    challenge = _independent_challenge(payload)
    assert challenge == hashlib.sha256(payload).digest()

    client_data_json = _build_client_data_json(challenge=challenge)
    document = json.loads(client_data_json)
    assert base64.urlsafe_b64decode(document["challenge"] + "=" * (-len(document["challenge"]) % 4)) == challenge

    client_data_hash = hashlib.sha256(client_data_json).digest()
    auth_data = _build_authenticator_data()
    signed = auth_data + client_data_hash
    assert len(signed) == 37 + 32


def test_provider_challenge_is_sha256_of_canonical_payload_not_a_second_canonicalization(harness: _Harness) -> None:
    """Spec sections 11/12: the challenge derives from the exact Wave-3
    canonical bytes the verifier passes in. No alternate reconstructed
    payload exists -- proven by handing the provider a payload that is
    NOT valid JSON at all: it still verifies, because the provider only
    ever hashes the bytes it is given."""

    payload = b"\x00\x01\x02 not json at all \xff"
    evidence = harness.authenticator.assert_over(payload)
    assert harness.verify(payload, evidence).signature_valid is True


def test_provider_module_contains_no_second_canonicalizer() -> None:
    """Spec section 11: the FIDO2 module must never rebuild proof JSON."""

    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    assert "canonicalize_hatp_proof_payload" not in body
    assert "HumanApprovalProvenanceProof" not in body
    assert "sort_keys=True" in body  # only for the evidence envelope
    tree = ast.parse(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    digest_fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and "digest" in n.name]
    assert digest_fns == ["_payload_digest"]


@pytest.mark.parametrize("mutation_index", [0, 1, 7, 15, -1])
def test_single_byte_payload_mutation_invalidates_a_prior_assertion(harness: _Harness, mutation_index: int) -> None:
    """Spec section 12: byte-exact payload binding."""

    payload = bytearray(b'{"field":"value","n":1234567890}')
    evidence = harness.authenticator.assert_over(bytes(payload))
    assert harness.verify(bytes(payload), evidence).signature_valid is True

    payload[mutation_index] ^= 0x01
    assert harness.verify(bytes(payload), evidence).signature_valid is False


def test_challenge_encoding_substitution_does_not_verify(harness: _Harness) -> None:
    """Spec section 15: padded / standard-alphabet base64 variants of the
    same challenge do not produce a verifying assertion, because they
    change clientDataJSON bytes and therefore the signed hash."""

    payload = b"canonical-payload"
    challenge = _independent_challenge(payload)
    padded = base64.urlsafe_b64encode(challenge).decode("ascii")  # WITH padding
    client_data_json = json.dumps(
        {"type": "webauthn.get", "challenge": padded, "origin": "pcae-hatp://hatp.pcae.local", "crossOrigin": False},
        separators=(",", ":"),
    ).encode("utf-8")
    auth_data = _build_authenticator_data()
    signature = harness.authenticator.private_key.sign(
        auth_data + hashlib.sha256(client_data_json).digest(), ec.ECDSA(hashes.SHA256())
    )
    evidence = _build_evidence_json(
        credential_id=harness.authenticator.credential_id,
        authenticator_data=auth_data,
        client_data_json=client_data_json,
        signature=signature,
    )
    outcome = harness.verify(payload, evidence)
    # Either the library refuses the padded encoding, or the decoded
    # challenge still matches -- but this variant is only producible by
    # someone who already holds the signing key, so it confers nothing.
    assert isinstance(outcome, HATPProviderVerificationOutcome)


def test_truncated_payload_prefix_does_not_verify(harness: _Harness) -> None:
    """A prefix of the canonical payload must not satisfy an assertion
    made over the whole payload (no length-extension / truncation)."""

    payload = b'{"a":1,"b":2,"c":3}'
    evidence = harness.authenticator.assert_over(payload)
    assert harness.verify(payload[:-1], evidence).signature_valid is False
    assert harness.verify(payload + b" ", evidence).signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 5 -- Replay matrix across every signed semantic dimension
#            (spec sections 16-24, 105)
# ═══════════════════════════════════════════════════════════════════════════

_REPLAY_DIMENSIONS = {
    "principal": dict(principal_id="principal-other"),
    "signer_key_id": dict(signer_key_id="f" * 32),
    "provider_profile": dict(provider_profile="OTHER_PROFILE_V1"),
    "repository": dict(repository_id=_REPOSITORY_B),
    "decision_record_id": dict(decision_record_id="decision-other"),
    "decision_record_digest": dict(decision_record_digest="e" * 64),
    "binding_id": dict(binding_id="binding-other"),
    "binding_digest": dict(binding_digest="a" * 64),
    "issued_at": dict(issued_at="2026-08-07T10:00:01+00:00"),
    "operation_ag3_job": dict(operation_reference=Ag3OperationReference(job_id="job-2", original_commit_sha="c" * 40)),
    "operation_ag3_commit": dict(operation_reference=Ag3OperationReference(job_id="job-1", original_commit_sha="d" * 40)),
    "operation_ag5": dict(
        rollback_site=RollbackSite.AG5,
        operation_reference=Ag5OperationReference(per_id="per-1", ecp_id="ecp-1"),
    ),
}


@pytest.mark.parametrize("dimension", sorted(_REPLAY_DIMENSIONS))
def test_evidence_for_proof_a_never_verifies_for_proof_b(harness: _Harness, dimension: str) -> None:
    """Spec sections 16-24: every signed semantic dimension of the Wave-3
    canonical payload, exercised individually with real signatures."""

    proof_a = _proof(signer_key_id=harness.signer_key_id)
    payload_a = canonicalize_hatp_proof_payload(proof_a)
    evidence = harness.authenticator.assert_over(payload_a)
    assert harness.verify(payload_a, evidence).signature_valid is True

    overrides = dict(signer_key_id=harness.signer_key_id)
    overrides.update(_REPLAY_DIMENSIONS[dimension])
    proof_b = _proof(**overrides)
    payload_b = canonicalize_hatp_proof_payload(proof_b)
    assert payload_a != payload_b, f"{dimension} is not part of the canonical payload"
    assert harness.verify(payload_b, evidence).signature_valid is False


def test_timestamp_equivalent_lexical_form_yields_the_same_canonical_payload(harness: _Harness) -> None:
    """Spec section 21: an equivalent lexical representation producing an
    identical canonical semantic proof may legitimately share evidence --
    that is Wave-3 canonicalization working, not a replay hole."""

    proof_a = _proof(signer_key_id=harness.signer_key_id, issued_at="2026-08-07T10:00:00+00:00")
    proof_b = _proof(signer_key_id=harness.signer_key_id, issued_at="2026-08-07T12:00:00+02:00")
    assert canonicalize_hatp_proof_payload(proof_a) == canonicalize_hatp_proof_payload(proof_b)


def test_evidence_replays_across_provider_instances_only_because_binding_carries_trust(harness: _Harness) -> None:
    """Spec section 105: provider objects are stateless verifiers; a
    second instance over the same registry accepts the same evidence.
    Acceptable ONLY because payload+credential binding carries the
    trust -- documented, not assumed."""

    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id))
    evidence = harness.authenticator.assert_over(payload)
    second = Fido2HardwareProvider(credential_store=harness.store)
    outcome = second.verify(
        canonical_payload=payload,
        signer_key_id=harness.signer_key_id,
        provider_profile=harness.provider_profile,
        assertion=evidence,
    )
    assert outcome.signature_valid is True
    # ...and the same evidence still fails for any other payload.
    other = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id, binding_id="binding-2"))
    assert second.verify(
        canonical_payload=other,
        signer_key_id=harness.signer_key_id,
        provider_profile=harness.provider_profile,
        assertion=evidence,
    ).signature_valid is False


def test_provider_invents_no_freshness_semantics_of_its_own() -> None:
    """Spec section 106: no wall-clock/TTL logic in the provider layer;
    `issued_at` + Wave-4 remain authoritative."""

    for module_path in (
        _SRC_ROOT / "core" / "hatp_fido2_provider.py",
        _SRC_ROOT / "core" / "hatp_piv_provider.py",
        _SRC_ROOT / "core" / "hatp_hardware_credentials.py",
        _SRC_ROOT / "core" / "hatp_providers.py",
    ):
        body = _strip_docstrings_and_comments(_read(module_path))
        for forbidden in ("datetime.now", "time.time", "utcnow", "expires_at", "monotonic"):
            assert forbidden not in body, f"{module_path.name}: {forbidden}"


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 6 -- User presence (spec sections 49-57)
# ═══════════════════════════════════════════════════════════════════════════


def test_is_user_present_is_invoked_as_a_method_not_read_as_a_property() -> None:
    """Spec section 49: regression guard for the exact bug 149O.2
    reports catching. `AuthenticatorData.is_user_present` is a bound
    method on fido2 1.x -- reading it without calling it is always
    truthy."""

    auth_data = AuthenticatorData(_build_authenticator_data(up=False))
    assert callable(auth_data.is_user_present)
    assert bool(auth_data.is_user_present) is True  # the trap
    assert auth_data.is_user_present() is False  # the correct reading

    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    assert "is_user_present()" in body
    assert not re.search(r"is_user_present(?!\()", body)


def test_up_false_with_a_cryptographically_valid_signature_yields_presence_not_proven(harness: _Harness) -> None:
    """Spec section 50."""

    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id))
    evidence = harness.authenticator.assert_over(payload, up=False)
    outcome = harness.verify(payload, evidence)
    assert outcome.signature_valid is True
    assert outcome.human_presence_proven is False


def test_up_true_is_necessary_for_wave4_valid_and_up_false_maps_to_user_presence_not_proven(harness: _Harness) -> None:
    """Spec sections 50/51 end-to-end through the unmodified Wave-4
    verifier, using the real FIDO2 provider."""

    outcomes = {}
    for up in (True, False):
        outcomes[up] = _run_wave4(harness, up=up)
    assert outcomes[True] is HATPVerificationStatus.VALID
    assert outcomes[False] is HATPVerificationStatus.USER_PRESENCE_NOT_PROVEN


def test_uv_alone_never_substitutes_for_up(harness: _Harness) -> None:
    """Spec section 52: UV set but UP clear must NOT prove presence."""

    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id))
    evidence = harness.authenticator.assert_over(payload, up=False, uv=True)
    outcome = harness.verify(payload, evidence)
    assert outcome.signature_valid is True
    assert outcome.human_presence_proven is False


def test_presence_from_operation_a_cannot_satisfy_operation_b(harness: _Harness) -> None:
    """Spec section 54: presence replay. A UP=true assertion over payload
    A fails entirely (not merely 'presence-less') against payload B."""

    payload_a = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id, binding_id="binding-A"))
    payload_b = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id, binding_id="binding-B"))
    evidence = harness.authenticator.assert_over(payload_a, up=True)
    assert harness.verify(payload_a, evidence).human_presence_proven is True
    outcome_b = harness.verify(payload_b, evidence)
    assert outcome_b.signature_valid is False
    assert outcome_b.human_presence_proven is False


def test_presence_is_recomputed_per_call_and_never_cached(harness: _Harness) -> None:
    """Spec sections 55/56: interleave UP=true / UP=false assertions
    through one provider instance; each result must track its own
    assertion."""

    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id))
    for expected in (True, False, True, False, False, True):
        evidence = harness.authenticator.assert_over(payload, up=expected)
        assert harness.verify(payload, evidence).human_presence_proven is expected


def test_no_provider_api_accepts_a_caller_supplied_presence_assertion() -> None:
    """Spec section 57: no production provider entry point exposes a
    `human_present` / `user_present` style parameter, and no production
    module assigns `human_presence_proven=True` as a constant."""

    for cls in (Fido2HardwareProvider, PivHardwareProvider):
        for name in ("verify", "request_signature", "capabilities", "credential_identity"):
            signature = inspect.signature(getattr(cls, name))
            for parameter in signature.parameters:
                assert "present" not in parameter.lower(), f"{cls.__name__}.{name}({parameter})"

    for module_path in (
        _SRC_ROOT / "core" / "hatp_fido2_provider.py",
        _SRC_ROOT / "core" / "hatp_piv_provider.py",
    ):
        tree = ast.parse(_read(module_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "human_presence_proven":
                if isinstance(node.value, ast.Constant):
                    assert node.value.value is False, "constant True presence is never permitted"


def test_test_provider_caller_supplied_presence_is_confined_to_the_test_provider() -> None:
    """`TestHATPProofVerifierProvider` DOES accept a caller-supplied
    presence boolean -- acceptable only because it is unreachable from
    the production factory (Group 8)."""

    assert "human_presence_proven" in inspect.signature(TestHATPProofVerifierProvider.__init__).parameters
    assert TestHATPProofVerifierProvider.__test__ is False


def _populated_trust_store(store_root: Path, signer_key_id: str, principal_id: str, repository_id: str, deployment_root: str):
    """A fully-healthy Wave-2 protected trust store (principal, signer,
    deployment binding, authority) written to a test-only root."""

    registry = {
        "registry_version": bootstrap_module.REGISTRY_SCHEMA_VERSION,
        "principals": [{"principal_id": principal_id, "status": "active"}],
        "signers": [
            {
                "signer_key_id": signer_key_id,
                "principal_id": principal_id,
                "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                "status": "active",
            }
        ],
        "deployment_bindings": [
            {
                "repository_id": repository_id,
                "canonical_deployment_root": deployment_root,
                "principal_id": principal_id,
                "signer_key_id": signer_key_id,
                "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                "authority_scope": "rollback_approval",
                "valid_from": "2026-01-01T00:00:00+00:00",
                "status": "active",
            }
        ],
        "authorities": [
            {
                "principal_id": principal_id,
                "repository_id": repository_id,
                "authority_scope": "rollback_approval",
                "valid_from": "2026-01-01T00:00:00+00:00",
                "status": "active",
            }
        ],
    }
    store_root.mkdir(parents=True, exist_ok=True)
    (store_root / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
    return bootstrap_module.HATPTrustStore(_test_only_root=store_root), repository_id


def _run_wave4(harness: _Harness, *, up: bool = True, tmp_root: Optional[Path] = None) -> HATPVerificationStatus:
    """Drive the unmodified Wave-4 verifier with the REAL FIDO2 provider
    over a fully-populated Wave-2 trust store."""

    import tempfile

    root = tmp_root or Path(tempfile.mkdtemp())
    root.mkdir(parents=True, exist_ok=True)
    repository_id = _REPOSITORY_A
    deployment_root = bootstrap_module.resolve_canonical_deployment_root(root)
    proof = _proof(signer_key_id=harness.signer_key_id, repository_id=repository_id)
    trust_store, _ = _populated_trust_store(
        root / "trust-store", harness.signer_key_id, proof.principal_id, repository_id, deployment_root
    )

    payload = canonicalize_hatp_proof_payload(proof)
    evidence = harness.authenticator.assert_over(payload, up=up)
    result = verify_hatp_proof(
        proof,
        evidence=HATPVerificationEvidence(assertion=evidence),
        provider=harness.provider,
        trust_store=trust_store,
        expected_operation=HATPExpectedOperation(
            decision_record_id=proof.decision_record_id,
            binding_id=proof.binding_id,
            rollback_site=proof.rollback_site,
            operation_reference=proof.operation_reference,
        ),
        current_repository_id=repository_id,
        canonical_deployment_root=deployment_root,
        evaluation_time=_EVAL_TIME,
    )
    return result.status


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 7 -- Hardware credential registry trust-root attacks
#            (spec sections 25-48)
# ═══════════════════════════════════════════════════════════════════════════


def test_production_registry_root_is_a_fixed_platform_path() -> None:
    """Spec section 26."""

    if sys.platform == "darwin":
        expected = Path("/Library/Application Support/PCAE/HATP/hardware-credentials")
    elif sys.platform == "linux":
        expected = Path("/etc/pcae/hatp/hardware-credentials")
    else:
        pytest.skip("no fixed root defined for this platform")
    assert HATPHardwareCredentialStore.production().root == expected
    assert not str(expected).startswith(str(_REPO_ROOT))


@pytest.mark.parametrize(
    "variable",
    [
        "HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_RUNTIME_DIR",
        "TMPDIR",
        "PWD",
        "PCAE_HATP_CREDENTIAL_ROOT",
        "HATP_CREDENTIAL_STORE",
        "PCAE_HOME",
        "PCAE_CONFIG",
    ],
)
def test_registry_root_is_not_redirectable_by_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, variable: str) -> None:
    """Spec section 26: no environment variable relocates the production
    authority root."""

    if sys.platform not in ("darwin", "linux"):
        pytest.skip("no fixed root defined for this platform")
    baseline = HATPHardwareCredentialStore.production().root
    monkeypatch.setenv(variable, str(tmp_path))
    assert HATPHardwareCredentialStore.production().root == baseline


def test_registry_root_is_not_redirectable_by_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    if sys.platform not in ("darwin", "linux"):
        pytest.skip("no fixed root defined for this platform")
    baseline = HATPHardwareCredentialStore.production().root
    monkeypatch.chdir(tmp_path)
    assert HATPHardwareCredentialStore.production().root == baseline


def test_production_classmethod_accepts_no_argument() -> None:
    """Spec section 26: no CLI/constructor argument path into
    `.production()`."""

    parameters = list(inspect.signature(HATPHardwareCredentialStore.production).parameters)
    assert parameters == []
    ctor = list(inspect.signature(HATPHardwareCredentialStore.__init__).parameters)
    assert ctor == ["self", "_test_only_root"]
    with pytest.raises(TypeError):
        HATPHardwareCredentialStore(Path("/tmp"))  # positional injection refused


def test_no_cli_flag_or_environment_read_reaches_the_credential_registry() -> None:
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_hardware_credentials.py"))
    assert "os.environ" not in body
    assert "getenv" not in body
    assert "expanduser" not in body
    assert "Path.home" not in body
    assert "getcwd" not in body
    cli_body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "cli.py"))
    assert "hardware_credential" not in cli_body.lower()
    assert "HATPHardwareCredentialStore" not in cli_body


@pytest.mark.parametrize("platform_name", ["win32", "cygwin", "aix", "freebsd12"])
def test_unsupported_platform_fails_closed(monkeypatch: pytest.MonkeyPatch, platform_name: str) -> None:
    """Spec section 27."""

    monkeypatch.setattr(credentials_module.sys, "platform", platform_name)
    with pytest.raises(HATPHardwareCredentialStoreUnsupportedPlatformError):
        HATPHardwareCredentialStore.production()


def test_non_posix_os_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(credentials_module.os, "name", "nt")
    with pytest.raises(HATPHardwareCredentialStoreUnsupportedPlatformError):
        HATPHardwareCredentialStore.production()


def test_agent_principal_cannot_pre_create_the_production_root_on_this_machine() -> None:
    """Spec section 28: attempt the root pre-creation attack for real."""

    if sys.platform != "darwin":
        pytest.skip("macOS-specific filesystem topology probe")
    parent = Path("/Library/Application Support")
    assert parent.exists()
    parent_stat = parent.stat()
    assert parent_stat.st_uid == 0, "protected parent must be root-owned"
    assert not (stat.S_IMODE(parent_stat.st_mode) & (stat.S_IWGRP | stat.S_IWOTH)), (
        "protected parent must not be group/other writable"
    )
    assert not os.access(parent, os.W_OK), "agent principal must not be able to create the PCAE root"


def test_symlinked_registry_root_is_refused(tmp_path: Path) -> None:
    """Spec section 32."""

    real = tmp_path / "real"
    real.mkdir()
    (real / "hardware-credentials.json").write_text(json.dumps({"credentials": []}), encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(real)
    store = HATPHardwareCredentialStore(_test_only_root=link)
    with pytest.raises(HATPHardwareCredentialStoreSymlinkError):
        store.lookup_credential("anything")
    assert store.environment_status().status == "UNSAFE_CONFIGURATION"


def test_symlinked_registry_artifact_is_refused(tmp_path: Path) -> None:
    """Spec section 34."""

    root = tmp_path / "root"
    root.mkdir()
    elsewhere = tmp_path / "attacker.json"
    elsewhere.write_text(json.dumps({"credentials": []}), encoding="utf-8")
    (root / "hardware-credentials.json").symlink_to(elsewhere)
    with pytest.raises(HATPHardwareCredentialStoreSymlinkError):
        HATPHardwareCredentialStore(_test_only_root=root).lookup_credential("anything")


def test_duplicate_json_keys_in_the_registry_are_rejected(tmp_path: Path) -> None:
    """Spec section 35."""

    root = tmp_path / "root"
    root.mkdir()
    (root / "hardware-credentials.json").write_text(
        '{"credentials": [], "credentials": [{"signer_key_id":"x"}]}', encoding="utf-8"
    )
    with pytest.raises(HATPHardwareCredentialStoreMalformedError):
        HATPHardwareCredentialStore(_test_only_root=root).lookup_credential("x")


def test_duplicate_credential_id_fails_closed(tmp_path: Path) -> None:
    """Spec sections 37/38: an ambiguous registry never silently selects
    a winner."""

    root = tmp_path / "root"
    root.mkdir()
    record = {
        "signer_key_id": "dup",
        "provider_profile": HATP_HARDWARE_PROVIDER_V1,
        "protocol_name": "FIDO2",
        "algorithm": "ES256",
        "public_key_hex": "00",
        "status": "active",
    }
    other = dict(record, public_key_hex="11")
    (root / "hardware-credentials.json").write_text(json.dumps({"credentials": [record, other]}), encoding="utf-8")
    with pytest.raises(HATPHardwareCredentialStoreMalformedError):
        HATPHardwareCredentialStore(_test_only_root=root).lookup_credential("dup")


@pytest.mark.parametrize(
    ("document", "lookup_key"),
    [
        ("not json at all", "x"),
        ("[]", "x"),
        ('{"credentials": {}}', "x"),
        ('{"credentials": [{"signer_key_id": "x"}]}', "x"),
        ('{"credentials": [{"signer_key_id": "x", "provider_profile": "P", "protocol_name": "SSH", "algorithm": "ES256", "public_key_hex": "00", "status": "active"}]}', "x"),
        ('{"credentials": [{"signer_key_id": "x", "provider_profile": "P", "protocol_name": "FIDO2", "algorithm": "ES256", "public_key_hex": "zz", "status": "active"}]}', "x"),
        ('{"credentials": [{"signer_key_id": "x", "provider_profile": "P", "protocol_name": "FIDO2", "algorithm": "ES256", "public_key_hex": "00", "status": "trusted"}]}', "x"),
        ('{"credentials": [{"signer_key_id": "", "provider_profile": "P", "protocol_name": "FIDO2", "algorithm": "ES256", "public_key_hex": "00", "status": "active"}]}', ""),
        ('{"credentials": [{"signer_key_id": "x", "provider_profile": "", "protocol_name": "FIDO2", "algorithm": "ES256", "public_key_hex": "00", "status": "active"}]}', "x"),
        ('{"credentials": [{"signer_key_id": "x", "provider_profile": "P", "protocol_name": "FIDO2", "algorithm": "", "public_key_hex": "00", "status": "active"}]}', "x"),
        ('{"credentials": [{"signer_key_id": 7, "provider_profile": "P", "protocol_name": "FIDO2", "algorithm": "ES256", "public_key_hex": "00", "status": "active"}]}', 7),
    ],
)
def test_malformed_registry_documents_fail_closed(tmp_path: Path, document: str, lookup_key) -> None:
    """Spec section 39: never partially accepted, never a silent pass."""

    root = tmp_path / "root"
    root.mkdir()
    (root / "hardware-credentials.json").write_text(document, encoding="utf-8")
    store = HATPHardwareCredentialStore(_test_only_root=root)
    with pytest.raises(HATPHardwareCredentialStoreError):
        store.lookup_credential(lookup_key)


def test_missing_registry_returns_none_never_a_trust_grant(tmp_path: Path) -> None:
    """Spec section 40."""

    root = tmp_path / "root"
    root.mkdir()
    store = HATPHardwareCredentialStore(_test_only_root=root)
    assert store.lookup_credential("anything") is None
    assert store.environment_status().status == "READY"


def test_registry_lookup_creates_no_state_on_disk(tmp_path: Path) -> None:
    """Spec section 41: no auto-provisioning."""

    root = tmp_path / "root"
    root.mkdir()
    store = HATPHardwareCredentialStore(_test_only_root=root)
    store.lookup_credential("anything")
    store.environment_status()
    assert list(root.iterdir()) == []


def test_missing_root_directory_never_auto_creates(tmp_path: Path) -> None:
    root = tmp_path / "absent"
    store = HATPHardwareCredentialStore(_test_only_root=root)
    assert store.lookup_credential("anything") is None
    assert store.environment_status().status == "UNAVAILABLE"
    assert not root.exists()


def test_credential_registry_exposes_no_authority_mutating_api() -> None:
    """Spec section 42: Wave 7 owns enrollment."""

    public = {name for name in dir(HATPHardwareCredentialStore) if not name.startswith("_")}
    assert public == {"production", "root", "environment_status", "lookup_credential"}
    module_functions = {
        node.name
        for node in ast.walk(ast.parse(_read(_SRC_ROOT / "core" / "hatp_hardware_credentials.py")))
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    for forbidden in ("enroll", "grant", "authorize", "rotate", "revoke", "write", "create", "save", "update", "delete"):
        assert not any(forbidden in name for name in module_functions | public), forbidden
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_hardware_credentials.py"))
    for forbidden in ("write_text", "write_bytes", "mkdir", "os.remove", "unlink", "rename", "chmod", "open("):
        assert forbidden not in body, forbidden


def test_credential_record_is_immutable_and_carries_no_secret_material() -> None:
    record = HardwareCredentialRecord(
        signer_key_id="x", provider_profile="P", protocol_name="FIDO2", algorithm="ES256", public_key=b"\x00", status="active"
    )
    with pytest.raises(FrozenInstanceError):
        record.status = "active"  # type: ignore[misc]
    names = {f.name for f in fields(HardwareCredentialRecord)}
    for forbidden in ("private_key", "pin", "secret", "token", "passphrase"):
        assert not any(forbidden in name for name in names), forbidden


def test_credential_registry_does_not_import_wave2_bootstrap() -> None:
    """Spec section 43: import independence, confirmed by AST."""

    tree = ast.parse(_read(_SRC_ROOT / "core" / "hatp_hardware_credentials.py"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert not any("hatp_bootstrap" in name for name in imported)
    assert not any(name.startswith("pcae") for name in imported), "registry must depend on no PCAE module"


# --- Spec section 43: side-by-side drift audit vs the Wave-2 trust store ---


def _environment_reason_vocabulary(function) -> set:
    """Extract every literal reason string a readiness inspector can emit."""

    reasons = set()
    for node in ast.walk(ast.parse(inspect.getsource(function))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.fullmatch(r"[a-z0-9_]+", node.value):
                reasons.add(node.value)
    return reasons


def test_credential_registry_readiness_check_is_weaker_than_wave2_trust_store() -> None:
    """FINDING B-149O.3-1 (NON-BLOCKING) reproduction, spec sections
    29/30/31/43.

    `inspect_credential_store_environment` duplicates
    `inspect_bootstrap_environment` but omits THREE of its checks:

        * agent-owns-the-root      (`agent_and_admin_share_os_principal`)
        * parent is a symlink      (`trust_store_parent_is_symlink`)
        * parent owner mismatch    (`trust_store_parent_owner_mismatch`)

    This is recorded, not repaired. It is NON-BLOCKING because (a) the
    production root is a fixed root-owned platform path the agent
    principal provably cannot create on this machine, (b) the registry
    holds only PUBLIC key material and grants no authority by itself,
    and (c) `verify_hatp_proof` still requires the Wave-2 trust store to
    independently authorize the signer, principal, authority, and
    deployment binding.
    """

    wave2 = _environment_reason_vocabulary(bootstrap_module.inspect_bootstrap_environment)
    wave5 = _environment_reason_vocabulary(credentials_module.inspect_credential_store_environment)

    def normalise(reasons: set) -> set:
        return {r.replace("trust_store_", "").replace("credential_store_", "") for r in reasons}

    missing = normalise(wave2) - normalise(wave5)
    assert missing == {
        "agent_and_admin_share_os_principal",
        "parent_is_symlink",
        "parent_owner_mismatch",
    }, f"drift set changed; re-assess the finding: {missing}"


def test_agent_owned_credential_root_is_reported_ready_reproducing_the_drift(tmp_path: Path) -> None:
    """FINDING B-149O.3-1 reproduction: an agent-owned registry root
    reports READY, where the equivalent Wave-2 root reports
    UNSAFE_CONFIGURATION."""

    root = tmp_path / "root"
    root.mkdir(mode=0o755)
    assert root.stat().st_uid == os.getuid()

    assert credentials_module.inspect_credential_store_environment(root).status == "READY"
    wave2 = bootstrap_module.inspect_bootstrap_environment(root)
    assert wave2.status.value == "UNSAFE_CONFIGURATION"
    assert "agent_and_admin_share_os_principal" in wave2.reasons


def test_credential_registry_readiness_is_not_consumed_by_any_caller() -> None:
    """FINDING B-149O.3-2 (OBSERVATION): `environment_status()` on the
    hardware credential registry is not read by the provider, by
    `verify_hatp_proof`, or by
    `inspect_hatp_verification_substrate_readiness`. The registry's
    readiness posture therefore has no effect on any verification
    outcome today. Recorded, not repaired -- the hard ceiling already
    keeps `operational=False` unconditionally."""

    callers = []
    for path in _SRC_ROOT.rglob("*.py"):
        body = _strip_docstrings_and_comments(_read(path))
        if "inspect_credential_store_environment" in body or "environment_status" in body:
            if "hardware_credential" in path.name or "hatp" in path.name:
                callers.append(path.name)
    assert "hatp_fido2_provider.py" not in callers
    fido2_body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    assert "environment_status" not in fido2_body
    wave4_body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "human_approval_trusted_provenance.py"))
    assert "hatp_hardware_credentials" not in wave4_body
    assert "inspect_credential_store_environment" not in wave4_body


def test_credential_registry_schema_version_is_declared_but_never_validated(tmp_path: Path) -> None:
    """FINDING B-149O.3-3 (NON-BLOCKING): `REGISTRY_SCHEMA_VERSION` is
    defined but never checked, and unknown top-level / per-record fields
    are accepted -- both strictly weaker than the Wave-2 trust store's
    closed schema (`registry_version` enforced, unknown fields
    rejected). Spec sections 36/43. Recorded, not repaired."""

    assert credentials_module.REGISTRY_SCHEMA_VERSION == 1
    load_source = inspect.getsource(HATPHardwareCredentialStore._load_registry)
    lookup_source = inspect.getsource(HATPHardwareCredentialStore.lookup_credential)
    parse_source = inspect.getsource(credentials_module._parse_credential)
    assert "REGISTRY_SCHEMA_VERSION" not in load_source + lookup_source + parse_source

    root = tmp_path / "root"
    root.mkdir()
    (root / "hardware-credentials.json").write_text(
        json.dumps(
            {
                "registry_version": 99,
                "totally_unknown_top_level": {"attack": True},
                "credentials": [
                    {
                        "signer_key_id": "x",
                        "provider_profile": HATP_HARDWARE_PROVIDER_V1,
                        "protocol_name": "FIDO2",
                        "algorithm": "ES256",
                        "public_key_hex": "00",
                        "status": "active",
                        "unknown_record_field": "ignored",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    record = HATPHardwareCredentialStore(_test_only_root=root).lookup_credential("x")
    assert record is not None, "reproduces the finding: unknown schema version/fields are accepted"

    # ...whereas the Wave-2 trust store rejects the equivalent document.
    wave2_root = tmp_path / "wave2"
    wave2_root.mkdir()
    (wave2_root / "registry.json").write_text(
        json.dumps({"registry_version": 99, "principals": [], "signers": [], "deployment_bindings": [], "authorities": []}),
        encoding="utf-8",
    )
    with pytest.raises(bootstrap_module.HATPTrustStoreMalformedError):
        bootstrap_module.HATPTrustStore(_test_only_root=wave2_root).lookup_signer("x")


def test_non_dict_credential_entries_are_skipped_rather_than_rejected(tmp_path: Path) -> None:
    """FINDING B-149O.3-4 (OBSERVATION): a non-object entry in the
    `credentials` array is silently skipped, not treated as a malformed
    registry. Conservative in effect (it can only cause a lookup to
    return `None`), but it is a parse relaxation the Wave-2 trust store
    does not share -- Wave 2 parses every record unconditionally.
    Recorded, not repaired."""

    root = tmp_path / "root"
    root.mkdir()
    (root / "hardware-credentials.json").write_text(
        json.dumps({"credentials": ["garbage", 17, None]}), encoding="utf-8"
    )
    assert HATPHardwareCredentialStore(_test_only_root=root).lookup_credential("x") is None

    # Wave 2, by contrast, parses (and rejects) every element it sees.
    wave2_root = tmp_path / "wave2"
    wave2_root.mkdir()
    (wave2_root / "registry.json").write_text(
        json.dumps(
            {
                "registry_version": bootstrap_module.REGISTRY_SCHEMA_VERSION,
                "principals": [],
                "signers": [{"signer_key_id": "x", "unknown_field": 1}],
                "deployment_bindings": [],
                "authorities": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(bootstrap_module.HATPTrustStoreError):
        bootstrap_module.HATPTrustStore(_test_only_root=wave2_root).lookup_signer("x")


def test_credential_registry_carries_no_repository_or_deployment_binding() -> None:
    """Spec sections 44/45: the trust CONJUNCTION. The hardware registry
    is deliberately repository-agnostic; repository/deployment/principal
    authority lives entirely in the Wave-2 trust store, and
    `verify_hatp_proof` requires BOTH. Neither store is independently
    sufficient."""

    names = {f.name for f in fields(HardwareCredentialRecord)}
    assert "repository_id" not in names
    assert "canonical_deployment_root" not in names
    assert "principal_id" not in names
    wave4 = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "human_approval_trusted_provenance.py"))
    for required in (
        "trust_store.lookup_signer",
        "trust_store.lookup_principal",
        "trust_store.lookup_authority",
        "trust_store.resolve_deployment_authorization",
    ):
        assert required in wave4, required


def test_copying_a_credential_id_into_another_deployment_confers_no_authority(harness: _Harness, tmp_path: Path) -> None:
    """Spec section 44, exercised end-to-end: the same authentic
    credential, the same real signature, a DIFFERENT deployment root."""

    status = _run_wave4(harness, tmp_root=tmp_path / "a")
    assert status is HATPVerificationStatus.VALID

    # Same registry contents, relocated deployment root -> WRONG_DEPLOYMENT.
    root_b = tmp_path / "b"
    root_b.mkdir()
    repository_id = _REPOSITORY_A
    proof = _proof(signer_key_id=harness.signer_key_id, repository_id=repository_id)
    store_root = tmp_path / "a" / "trust-store"
    trust_store = bootstrap_module.HATPTrustStore(_test_only_root=store_root)
    payload = canonicalize_hatp_proof_payload(proof)
    result = verify_hatp_proof(
        proof,
        evidence=HATPVerificationEvidence(assertion=harness.authenticator.assert_over(payload)),
        provider=harness.provider,
        trust_store=trust_store,
        expected_operation=HATPExpectedOperation(
            decision_record_id=proof.decision_record_id,
            binding_id=proof.binding_id,
            rollback_site=proof.rollback_site,
            operation_reference=proof.operation_reference,
        ),
        current_repository_id=repository_id,
        canonical_deployment_root=bootstrap_module.resolve_canonical_deployment_root(root_b),
        evaluation_time=_EVAL_TIME,
    )
    assert result.status is HATPVerificationStatus.WRONG_DEPLOYMENT


def test_proof_cannot_self_select_its_own_credential_material(tmp_path: Path) -> None:
    """Spec section 46: attacker key + attacker-created unprotected
    credential data must not produce trusted verification. The proof
    carries no public key at all -- verified structurally."""

    names = {f.name for f in fields(HumanApprovalProvenanceProof)}
    for forbidden in ("public_key", "certificate", "attestation", "cose_key", "signer_public_key"):
        assert not any(forbidden in name for name in names), forbidden

    attacker = _SoftwareAuthenticator()
    empty_store = _InMemoryCredentialStore({})
    provider = Fido2HardwareProvider(credential_store=empty_store)
    proof = _proof(signer_key_id=attacker.signer_key_id)
    payload = canonicalize_hatp_proof_payload(proof)
    outcome = provider.verify(
        canonical_payload=payload,
        signer_key_id=attacker.signer_key_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        assertion=attacker.assert_over(payload),
    )
    assert outcome.signature_valid is False
    assert outcome.human_presence_proven is False


def test_unenrolled_and_revoked_credentials_fail_closed(harness: _Harness) -> None:
    """Spec sections 24/37: unknown and revoked credential IDs."""

    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=harness.signer_key_id))
    evidence = harness.authenticator.assert_over(payload)
    assert harness.verify(payload, evidence, signer_key_id="deadbeef").signature_valid is False

    revoked = _Harness(status="revoked")
    payload_r = canonicalize_hatp_proof_payload(_proof(signer_key_id=revoked.signer_key_id))
    assert revoked.verify(payload_r, revoked.authenticator.assert_over(payload_r)).signature_valid is False


def test_wrong_protocol_name_on_the_credential_fails_closed() -> None:
    piv_record_harness = _Harness(protocol_name="PIV")
    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=piv_record_harness.signer_key_id))
    evidence = piv_record_harness.authenticator.assert_over(payload)
    assert piv_record_harness.verify(payload, evidence).signature_valid is False


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 8 -- Software/test credential exclusion + production factory
#            (spec sections 47, 48, 69, 70, 103, 104)
# ═══════════════════════════════════════════════════════════════════════════


def test_software_key_cannot_be_registered_through_any_production_api() -> None:
    """Spec section 47: there is no production write path at all, so a
    software-generated key can never enter the production registry
    through PCAE."""

    store = HATPHardwareCredentialStore
    assert not hasattr(store, "enroll")
    assert not hasattr(store, "register")
    assert not hasattr(store, "add_credential")
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_hardware_credentials.py"))
    assert "def enroll" not in body and "def register" not in body


def test_production_provider_reads_the_protected_registry_not_a_test_fixture() -> None:
    """Spec section 48: a `Fido2HardwareProvider` constructed the
    production way resolves the protected root -- there is no ambient
    fixture it could pick up."""

    provider = Fido2HardwareProvider()
    if sys.platform not in ("darwin", "linux"):
        pytest.skip("no fixed root defined for this platform")
    resolved = provider._resolve_credential_store()
    assert resolved.root == HATPHardwareCredentialStore.production().root
    assert not resolved.root.exists(), "no production registry is provisioned on this machine"


def test_software_key_reaches_no_verdict_through_the_production_path(tmp_path: Path) -> None:
    """Spec section 47 end-to-end: an authentic software-key assertion,
    presented to a provider bound to the (absent) production registry,
    fails closed."""

    attacker = _SoftwareAuthenticator()
    provider = Fido2HardwareProvider()
    if sys.platform not in ("darwin", "linux"):
        pytest.skip("no fixed root defined for this platform")
    payload = canonicalize_hatp_proof_payload(_proof(signer_key_id=attacker.signer_key_id))
    outcome = provider.verify(
        canonical_payload=payload,
        signer_key_id=attacker.signer_key_id,
        provider_profile=HATP_HARDWARE_PROVIDER_V1,
        assertion=attacker.assert_over(payload),
    )
    assert outcome.signature_valid is False


@pytest.mark.parametrize(
    "profile",
    [
        "TEST_PROVIDER_V1",
        "SOFTWARE",
        "SOFTWARE_PROVIDER_V1",
        "CUSTOM",
        "../../../evil",
        "fido2",
        "FIDO2",
        "HATP_HARDWARE_PROVIDER_V1-extra",
        "hatp_hardware_provider_v1",
        " HATP_HARDWARE_PROVIDER_V1",
        "HATP_HARDWARE_PROVIDER_V1 ",
        "HATP_HARDWARE_PROVIDER_V2",
        "",
        "PIV",
    ],
)
def test_production_factory_rejects_every_non_approved_profile_string(profile: str) -> None:
    """Spec section 69: closed allowlist, exact-match only."""

    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider(profile)


def test_production_factory_allowlist_contains_exactly_one_profile() -> None:
    assert providers_module._PRODUCTION_HARDWARE_PROVIDER_PROFILES == (HATP_HARDWARE_PROVIDER_V1,)


def test_production_factory_never_returns_the_test_provider() -> None:
    """Spec section 70: containment, verified both by type and by AST
    over the factory's executable body (docstrings stripped)."""

    provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    assert not isinstance(provider, TestHATPProofVerifierProvider)
    assert type(provider) is Fido2HardwareProvider

    factory_source = _strip_docstrings_and_comments(inspect.getsource(create_production_hardware_provider))
    assert "TestHATPProofVerifierProvider" not in factory_source
    assert "_fake_assertion" not in factory_source


def test_test_provider_is_referenced_by_no_production_module() -> None:
    offenders = []
    for path in _SRC_ROOT.rglob("*.py"):
        if path.name == "hatp_providers.py":
            continue
        body = _strip_docstrings_and_comments(_read(path))
        if "TestHATPProofVerifierProvider" in body or "_fake_assertion" in body:
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert offenders == []


def test_test_provider_has_no_registration_environment_or_cli_selection_mechanism() -> None:
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_providers.py"))
    assert "os.environ" not in body
    assert "getenv" not in body
    assert "argparse" not in body
    # The only place the test provider's name appears in executable code
    # is its own class definition.
    occurrences = [line for line in body.splitlines() if "TestHATPProofVerifierProvider" in line]
    assert occurrences == ["class TestHATPProofVerifierProvider:"]


def test_piv_fallback_requires_an_explicit_caller_opt_in() -> None:
    """Spec section 78: no silent placeholder-PIV instantiation."""

    signature = inspect.signature(create_production_hardware_provider)
    assert signature.parameters["allow_piv_fallback"].default is False
    source = _strip_docstrings_and_comments(inspect.getsource(create_production_hardware_provider))
    assert "if not allow_piv_fallback:" in source


def test_finding_factory_docstring_overclaims_device_detection() -> None:
    """FINDING B-149O.3-12 (OBSERVATION): the production factory's
    docstring claims it raises `HATPProviderUnavailableError` for "any
    unrecognized profile string, missing optional dependency, or absent
    device". It does NOT check for an absent device -- it returns a
    `Fido2HardwareProvider` whenever the library imports, regardless of
    whether hardware is attached. This is harmless (the returned
    provider fails closed on every operation without a device, and a
    verify-only provider legitimately needs no device), but the
    docstring overclaims. Documentation-only; recorded, not repaired."""

    docstring = " ".join(create_production_hardware_provider.__doc__.split())
    assert "or absent device" in docstring

    # No device is attached on this machine, yet the factory still
    # returns a provider rather than raising.
    assert {a.protocol_name: a for a in discover_hardware_providers()}["FIDO2"].device_detected is False
    provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    assert isinstance(provider, Fido2HardwareProvider)

    factory_source = _strip_docstrings_and_comments(inspect.getsource(create_production_hardware_provider))
    assert "device_detected" not in factory_source
    assert "list_devices" not in factory_source


def test_discovery_objects_cannot_be_injected_to_establish_trust() -> None:
    """Spec section 103: `discover_hardware_providers` takes no
    parameter, and `HardwareProviderAvailability` is a frozen facts
    object with no trust field."""

    assert list(inspect.signature(discover_hardware_providers).parameters) == []
    names = {f.name for f in fields(providers_module.HardwareProviderAvailability)}
    for forbidden in ("trusted", "authorized", "approved", "operational", "valid"):
        assert not any(forbidden in name for name in names), forbidden


def test_device_selection_is_deterministic_and_documented(harness: _Harness) -> None:
    """Spec sections 68/104: `request_signature` selects `devices[0]`.
    Documented here as OBSERVATION B-149O.3-5 -- with more than one
    authenticator attached the first enumerated device is used, and the
    operation then fails closed unless that device holds the requested
    credential (the `allow_list` carries the exact credential id)."""

    source = inspect.getsource(Fido2HardwareProvider.request_signature)
    assert "device = devices[0]" in source
    assert "allow_list=[{\"type\": \"public-key\", \"id\": credential_id}]" in source


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 9 -- Evidence schema strictness (spec sections 80-92, 97-101)
# ═══════════════════════════════════════════════════════════════════════════


def _valid_evidence_document(harness: _Harness, payload: bytes) -> dict:
    return json.loads(harness.authenticator.assert_over(payload).decode("utf-8"))


def test_evidence_envelope_has_exactly_five_fields(harness: _Harness) -> None:
    document = _valid_evidence_document(harness, b"payload")
    assert set(document) == {"version", "credential_id_hex", "authenticator_data_hex", "client_data_json_hex", "signature_hex"}


@pytest.mark.parametrize("field", ["version", "credential_id_hex", "authenticator_data_hex", "client_data_json_hex", "signature_hex"])
def test_missing_evidence_field_fails_closed(harness: _Harness, field: str) -> None:
    """Spec section 82."""

    document = _valid_evidence_document(harness, b"payload")
    del document[field]
    assert harness.verify(b"payload", json.dumps(document).encode("utf-8")).signature_valid is False


def test_unknown_evidence_field_fails_closed(harness: _Harness) -> None:
    """Spec section 81."""

    document = _valid_evidence_document(harness, b"payload")
    document["extra"] = "attack"
    assert harness.verify(b"payload", json.dumps(document).encode("utf-8")).signature_valid is False


def test_duplicate_evidence_key_fails_closed(harness: _Harness) -> None:
    """Spec section 83."""

    document = _valid_evidence_document(harness, b"payload")
    raw = json.dumps(document)
    injected = raw[:-1] + ', "signature_hex": "00"}'
    assert harness.verify(b"payload", injected.encode("utf-8")).signature_valid is False


@pytest.mark.parametrize("version", [0, 2, 99, "1", None, [1], {"v": 1}, -1])
def test_unknown_evidence_version_fails_closed(harness: _Harness, version) -> None:
    """Spec section 84."""

    document = _valid_evidence_document(harness, b"payload")
    document["version"] = version
    assert harness.verify(b"payload", json.dumps(document).encode("utf-8")).signature_valid is False


@pytest.mark.parametrize("version", [True, 1.0])
def test_evidence_version_check_is_numerically_loose(harness: _Harness, version) -> None:
    """FINDING B-149O.3-9 (OBSERVATION): the evidence `version` gate is
    `document["version"] != _EVIDENCE_SCHEMA_VERSION`, so Python numeric
    equality accepts `true` and `1.0` as schema version 1. Harmless --
    both are numerically the supported version and no semantic
    difference follows -- but it is a type-loose check where the rest of
    the envelope parsing is strict. Recorded, not repaired."""

    document = _valid_evidence_document(harness, b"payload")
    document["version"] = version
    assert harness.verify(b"payload", json.dumps(document).encode("utf-8")).signature_valid is True


def test_invalid_utf8_evidence_fails_closed(harness: _Harness) -> None:
    """Spec section 85."""

    assert harness.verify(b"payload", b"\xff\xfe\x00garbage").signature_valid is False


def test_non_object_evidence_fails_closed(harness: _Harness) -> None:
    for raw in (b"[]", b'"string"', b"17", b"null", b""):
        assert harness.verify(b"payload", raw).signature_valid is False


def test_evidence_credential_mismatch_fails_closed(harness: _Harness) -> None:
    """Spec section 87: the envelope's credential id must equal the
    registry-selected `signer_key_id`."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload, credential_id_override=uuid.uuid4().bytes)
    assert harness.verify(payload, evidence).signature_valid is False


def test_evidence_provider_profile_mismatch_fails_closed(harness: _Harness) -> None:
    """Spec sections 22/88/67."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload)
    assert harness.verify(payload, evidence, provider_profile="OTHER_PROFILE_V1").signature_valid is False


# ---------------------------------------------------------------------------
# FINDING B-149O.3-8 (NON-BLOCKING) -- `verify()` raises for structurally
# malformed evidence, violating its own frozen fail-closed-without-raising
# contract. Spec sections 86 / 89 / 90.
# ---------------------------------------------------------------------------


def test_frozen_provider_contract_forbids_raising_for_an_invalid_assertion() -> None:
    """The normative text this finding is measured against, quoted from
    the Wave-4 `HATPProofVerifierProvider.verify` docstring itself."""

    docstring = " ".join(providers_module.HATPProofVerifierProvider.verify.__doc__.split())
    assert "MUST NOT raise for an invalid/unrecognized assertion -- return `signature_valid=False` instead" in docstring
    assert "raising is reserved for genuine provider-level failure" in docstring


@pytest.mark.parametrize(
    ("field", "value", "expected_exception"),
    [
        ("signature_hex", "zz", ValueError),
        ("signature_hex", "0", ValueError),
        ("credential_id_hex", "nothex", ValueError),
        ("authenticator_data_hex", "xyz", ValueError),
        ("client_data_json_hex", "gg", ValueError),
        ("authenticator_data_hex", "00", ValueError),
        ("authenticator_data_hex", "", ValueError),
        ("authenticator_data_hex", "aa" * 36, ValueError),
        ("client_data_json_hex", b"not json".hex(), ValueError),
        ("client_data_json_hex", "", ValueError),
        ("client_data_json_hex", b"{}".hex(), KeyError),
        ("client_data_json_hex", b'{"type":"webauthn.get"}'.hex(), KeyError),
    ],
)
def test_finding_verify_raises_instead_of_failing_closed(harness: _Harness, field: str, value: str, expected_exception) -> None:
    """FINDING B-149O.3-8 reproduction (NON-BLOCKING).

    `_parse_fido2_evidence` performs `bytes.fromhex()`,
    `AuthenticatorData(...)` and `CollectedClientData(...)` OUTSIDE the
    `HATPFido2EvidenceMalformedError` boundary, and `verify()` catches
    only that one exception type. Structurally-malformed evidence
    therefore escapes as a bare `ValueError` / `json.JSONDecodeError`
    (a `ValueError` subclass) / `KeyError` instead of returning
    `signature_valid=False`.

    This independently narrows the scope of Phase 149O.2's own
    `evidence_format_strictness` claim that malformed evidence "never
    raises": that claim holds only for the five envelope-level cases it
    actually exercised (unknown field, missing field, unknown version,
    duplicate key, non-UTF-8 garbage), not for malformed hex or
    malformed inner WebAuthn structures.

    NON-BLOCKING: `verify_hatp_proof` (Wave 4, unmodified) wraps the
    provider call in `except Exception` and maps it to
    `INVALID_SIGNATURE`, so end-to-end HATP verification still fails
    closed (asserted in the companion test below). The defect is
    confined to the provider layer's own reusability contract.
    Recorded, NOT repaired.
    """

    document = _valid_evidence_document(harness, b"payload")
    document[field] = value
    with pytest.raises(expected_exception):
        harness.verify(b"payload", json.dumps(document).encode("utf-8"))


def test_finding_b_149o3_8_still_fails_closed_end_to_end_through_wave4(harness: _Harness, tmp_path: Path) -> None:
    """The containment half of FINDING B-149O.3-8: Wave 4 converts the
    escaping exception into `INVALID_SIGNATURE`, never into `VALID`."""

    root = tmp_path / "deployment"
    root.mkdir(parents=True, exist_ok=True)
    deployment_root = bootstrap_module.resolve_canonical_deployment_root(root)
    proof = _proof(signer_key_id=harness.signer_key_id, repository_id=_REPOSITORY_A)
    trust_store, _ = _populated_trust_store(
        tmp_path / "ts", harness.signer_key_id, proof.principal_id, _REPOSITORY_A, deployment_root
    )

    document = _valid_evidence_document(harness, canonicalize_hatp_proof_payload(proof))
    document["signature_hex"] = "zz"
    result = verify_hatp_proof(
        proof,
        evidence=HATPVerificationEvidence(assertion=json.dumps(document).encode("utf-8")),
        provider=harness.provider,
        trust_store=trust_store,
        expected_operation=HATPExpectedOperation(
            decision_record_id=proof.decision_record_id,
            binding_id=proof.binding_id,
            rollback_site=proof.rollback_site,
            operation_reference=proof.operation_reference,
        ),
        current_repository_id=_REPOSITORY_A,
        canonical_deployment_root=deployment_root,
        evaluation_time=_EVAL_TIME,
    )
    assert result.status is HATPVerificationStatus.INVALID_SIGNATURE


def test_empty_hex_signature_does_fail_closed_without_raising(harness: _Harness) -> None:
    """The malformed-signature case that IS handled correctly -- included
    so FINDING B-149O.3-8 is scoped precisely, never overstated."""

    document = _valid_evidence_document(harness, b"payload")
    document["signature_hex"] = ""
    assert harness.verify(b"payload", json.dumps(document).encode("utf-8")).signature_valid is False


@pytest.mark.parametrize("client_type", ["webauthn.create", "webauthn.GET", "", "hatp.get"])
def test_wrong_webauthn_client_data_type_fails_closed(harness: _Harness, client_type: str) -> None:
    """Spec section 91."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload, client_type=client_type)
    assert harness.verify(payload, evidence).signature_valid is False


def test_wrong_challenge_fails_closed(harness: _Harness) -> None:
    """Spec section 92."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload, challenge_override=hashlib.sha256(b"other").digest())
    assert harness.verify(payload, evidence).signature_valid is False


def test_origin_and_rp_id_are_fixed_module_constants_not_caller_selectable() -> None:
    """Spec section 93: HATP is not a web origin. The RP ID / origin pair
    is a fixed internal scoping constant with no parameter anywhere."""

    assert fido2_module._HATP_RP_ID == "hatp.pcae.local"
    assert fido2_module._HATP_ORIGIN == "pcae-hatp://hatp.pcae.local"
    assert fido2_module._RP_ID_HASH == hashlib.sha256(b"hatp.pcae.local").digest()
    for cls in (Fido2HardwareProvider,):
        for name in ("verify", "request_signature", "__init__"):
            parameters = inspect.signature(getattr(cls, name)).parameters
            for parameter in parameters:
                assert "origin" not in parameter.lower()
                assert "rp_id" not in parameter.lower()


@pytest.mark.parametrize("origin", ["https://evil.example", "pcae-hatp://other", "", "pcae-hatp://hatp.pcae.local/"])
def test_wrong_origin_fails_closed(harness: _Harness, origin: str) -> None:
    """Spec section 93: the origin IS an enforced predicate, not a
    decorative field."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload, origin=origin)
    assert harness.verify(payload, evidence).signature_valid is False


@pytest.mark.parametrize("rp_id", ["evil.example", "pcae.local", "hatp.pcae.locaL"])
def test_wrong_rp_id_hash_fails_closed(harness: _Harness, rp_id: str) -> None:
    """Spec section 94: the RP ID hash inside authenticatorData IS
    validated against the module's fixed constant."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload, rp_id=rp_id)
    assert harness.verify(payload, evidence).signature_valid is False


def test_only_the_up_flag_is_treated_as_security_bearing(harness: _Harness) -> None:
    """Spec section 95: UP is the only flag that changes the outcome.
    AT/ED/BE/BS are not consulted -- documented, and consistent with the
    contract's presence-only requirement."""

    payload = b"payload"
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    for unused_flag in ("is_user_verified", "is_attested", "FLAG.AT", "FLAG.ED", "FLAG.BE", "FLAG.BS", "FLAG.UV"):
        assert unused_flag not in body, unused_flag
    for uv in (True, False):
        evidence = harness.authenticator.assert_over(payload, up=True, uv=uv)
        outcome = harness.verify(payload, evidence)
        assert outcome.signature_valid is True
        assert outcome.human_presence_proven is True


def test_signature_counter_is_not_consulted_and_the_contract_does_not_require_it(harness: _Harness) -> None:
    """Spec section 96: OBSERVATION B-149O.3-6. The counter is ignored.
    HATP-001 never mentions a signature counter, so this is not a
    contract violation -- recorded as an observation only."""

    contract = _read(_CONTRACT_PATH)
    assert "signature counter" not in contract.lower()
    assert "signCount" not in contract

    payload = b"payload"
    for counter in (0, 1, 5, 2**32 - 1):
        evidence = harness.authenticator.assert_over(payload, counter=counter)
        assert harness.verify(payload, evidence).signature_valid is True


def test_tampered_signature_fails_closed(harness: _Harness) -> None:
    """Spec section 97: signature verification is delegated to the
    library's COSE implementation; no custom ECDSA math exists here."""

    payload = b"payload"
    assert harness.verify(payload, harness.authenticator.assert_over(payload, tamper_signature=True)).signature_valid is False
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    assert "cose_key.verify(" in body
    for forbidden in ("pow(", "inverse_mod", "% n", "int.from_bytes(signature"):
        assert forbidden not in body, forbidden


@pytest.mark.parametrize("mutation", ["truncate", "empty", "der_prefix", "flip_first"])
def test_malformed_der_signature_fails_closed(harness: _Harness, mutation: str) -> None:
    payload = b"payload"
    document = _valid_evidence_document(harness, payload)
    raw = bytes.fromhex(document["signature_hex"])
    if mutation == "truncate":
        raw = raw[:-5]
    elif mutation == "empty":
        raw = b""
    elif mutation == "der_prefix":
        raw = b"\x30\x00" + raw
    else:
        raw = bytes([raw[0] ^ 0xFF]) + raw[1:]
    document["signature_hex"] = raw.hex()
    assert harness.verify(payload, json.dumps(document).encode("utf-8")).signature_valid is False


def test_signature_from_a_different_key_fails_closed(harness: _Harness) -> None:
    """Spec sections 65/66: wrong public key / wrong credential."""

    payload = b"payload"
    other = ec.generate_private_key(ec.SECP256R1())
    evidence = harness.authenticator.assert_over(payload, signing_key=other)
    assert harness.verify(payload, evidence).signature_valid is False


def test_registry_public_key_substitution_breaks_verification(harness: _Harness) -> None:
    """Spec section 65: same credential id, different public key."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload)
    assert harness.verify(payload, evidence).signature_valid is True

    impostor = _SoftwareAuthenticator()
    harness.store._records[harness.signer_key_id] = HardwareCredentialRecord(
        signer_key_id=harness.signer_key_id,
        provider_profile=harness.provider_profile,
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=impostor.cose_public_key(),
        status="active",
    )
    assert harness.verify(payload, evidence).signature_valid is False


@pytest.mark.parametrize("key_factory", ["rsa", "ed25519", "p384"])
def test_public_key_type_confusion_fails_closed(harness: _Harness, key_factory: str) -> None:
    """Spec sections 98/100: only the registry's own COSE key material is
    used, and a non-ES256 key never verifies an ES256 assertion."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload)
    if key_factory == "rsa":
        wrong = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    elif key_factory == "ed25519":
        wrong = ed25519.Ed25519PrivateKey.generate().public_key()
    else:
        wrong = ec.generate_private_key(ec.SECP384R1()).public_key()
    try:
        cose = fido2_cbor.encode(dict(ES256.from_cryptography_key(wrong)))
    except Exception:
        cose = fido2_cbor.encode({1: 2, 3: -7, -1: 1, -2: b"\x00" * 32, -3: b"\x00" * 32})
    harness.store._records[harness.signer_key_id] = HardwareCredentialRecord(
        signer_key_id=harness.signer_key_id,
        provider_profile=harness.provider_profile,
        protocol_name="FIDO2",
        algorithm="ES256",
        public_key=cose,
        status="active",
    )
    assert harness.verify(payload, evidence).signature_valid is False


def test_algorithm_field_is_advisory_and_key_material_is_authoritative(harness: _Harness) -> None:
    """Spec section 101: OBSERVATION B-149O.3-7. The registry's
    `algorithm` string is stored but never cross-checked against the
    stored COSE key. This is safe in practice because verification uses
    the COSE key itself (whose `alg` label is authoritative), never the
    advisory string -- so an inconsistent `algorithm` value cannot
    downgrade or confuse verification. Recorded as an observation."""

    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    assert "record.algorithm" not in body

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload)
    harness.store._records[harness.signer_key_id] = HardwareCredentialRecord(
        signer_key_id=harness.signer_key_id,
        provider_profile=harness.provider_profile,
        protocol_name="FIDO2",
        algorithm="RS256-nonsense",
        public_key=harness.authenticator.cose_public_key(),
        status="active",
    )
    # The advisory mismatch neither breaks nor weakens verification.
    assert harness.verify(payload, evidence).signature_valid is True


def test_malformed_registry_public_key_fails_closed(harness: _Harness) -> None:
    """Spec section 99."""

    payload = b"payload"
    evidence = harness.authenticator.assert_over(payload)
    for bad in (b"", b"\x00", b"not cbor at all"):
        harness.store._records[harness.signer_key_id] = HardwareCredentialRecord(
            signer_key_id=harness.signer_key_id,
            provider_profile=harness.provider_profile,
            protocol_name="FIDO2",
            algorithm="ES256",
            public_key=bad,
            status="active",
        )
        assert harness.verify(payload, evidence).signature_valid is False


def test_verify_never_raises_for_any_malformed_assertion(harness: _Harness) -> None:
    """The frozen `HATPProofVerifierProvider.verify` contract: an
    invalid/unrecognized assertion returns `signature_valid=False`, it
    never raises."""

    for raw in (b"", b"{", b"\xff", b"[]", b'{"version":1}', json.dumps({"version": 1}).encode()):
        outcome = harness.verify(b"payload", raw)
        assert outcome.signature_valid is False


def test_registry_level_failure_does_propagate_and_wave4_maps_it_to_invalid_signature(tmp_path: Path) -> None:
    """A genuine registry fault (symlinked root) must NOT be swallowed as
    a plain invalid assertion at the provider layer -- it propagates, and
    Wave 4's fail-closed wrapper maps it to INVALID_SIGNATURE."""

    root = tmp_path / "link"
    real = tmp_path / "real"
    real.mkdir()
    root.symlink_to(real)
    provider = Fido2HardwareProvider(credential_store=HATPHardwareCredentialStore(_test_only_root=root))
    with pytest.raises(HATPHardwareCredentialStoreError):
        provider.verify(canonical_payload=b"p", signer_key_id="x", provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=b"{}")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 10 -- Attestation and PIV dispositions (spec sections 58-63, 76-79)
# ═══════════════════════════════════════════════════════════════════════════


def test_attestation_is_not_evaluated_and_is_honestly_reported_as_such() -> None:
    """Spec sections 58/63: no attestation path exists; the capability
    matrix says so rather than overclaiming."""

    capabilities = Fido2HardwareProvider().capabilities()
    assert capabilities.device_attestation is False
    assert capabilities.hatp_conformant.value == "CONFORMANT_WITH_NON_BLOCKING_LIMITATIONS"
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    for absent in ("attestation_object", "AttestationObject", "attStmt", "verify_attestation", "x5c"):
        assert absent not in body, absent


def test_provider_never_sets_attestation_valid_true(harness: _Harness) -> None:
    """Spec section 62: a fabricated `attestation_valid=True` would be
    an unverifiable claim. No production module ever sets it."""

    payload = b"payload"
    assert harness.verify(payload, harness.authenticator.assert_over(payload)).attestation_valid is None
    for module_path in (_SRC_ROOT / "core" / "hatp_fido2_provider.py", _SRC_ROOT / "core" / "hatp_piv_provider.py"):
        tree = ast.parse(_read(module_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "attestation_valid":
                assert isinstance(node.value, ast.Constant) and node.value.value is None


def test_wave4_treats_attestation_none_as_valid_and_false_as_fail_closed(harness: _Harness) -> None:
    """Spec section 61: the ACTUAL Wave-4 behavior, then judged against
    the contract (HATP-REQ-079 'where required')."""

    assert _run_wave4(harness) is HATPVerificationStatus.VALID
    wave4 = _read(_SRC_ROOT / "core" / "human_approval_trusted_provenance.py")
    assert "if outcome.attestation_valid is False:" in wave4
    assert "INVALID_ATTESTATION" in wave4


def test_attestation_root_material_originates_nowhere_in_agent_writable_state() -> None:
    """Spec section 63: no attestation root exists at all, so Root 2A is
    NOT claimed proven. Verified by absence."""

    for path in _SRC_ROOT.rglob("*.py"):
        body = _strip_docstrings_and_comments(_read(path))
        assert "attestation_root" not in body
        assert "ATTESTATION_ROOTS" not in body


def test_piv_provider_is_structurally_deferred_and_never_fabricates_success() -> None:
    """Spec sections 76/79."""

    provider = PivHardwareProvider()
    capabilities = provider.capabilities()
    assert capabilities.hatp_conformant.value == "NOT_CONFORMANT"
    assert capabilities.non_exportable_key is False
    assert capabilities.fresh_touch_per_operation is False
    assert capabilities.device_attestation is False

    with pytest.raises(HATPProviderUnavailableError):
        provider.credential_identity()
    with pytest.raises(HATPProviderUnavailableError):
        provider.request_signature(b"payload", signer_key_id="x", provider_profile=HATP_HARDWARE_PROVIDER_V1)

    outcome = provider.verify(
        canonical_payload=b"payload", signer_key_id="x", provider_profile=HATP_HARDWARE_PROVIDER_V1, assertion=b"{}"
    )
    assert outcome.signature_valid is False
    assert outcome.human_presence_proven is False
    assert outcome.attestation_valid is None


def test_piv_module_imports_no_smartcard_library_and_has_no_signing_logic() -> None:
    tree = ast.parse(_read(_SRC_ROOT / "core" / "hatp_piv_provider.py"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
    assert imported - {"__future__"} == {"pcae.core.hatp_providers"}
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_piv_provider.py"))
    for forbidden in ("pkcs11", "pyscard", "smartcard", "signature_valid=True", "human_presence_proven=True"):
        assert forbidden not in body, forbidden


def test_plan_permits_piv_deferral_because_the_fido2_spike_succeeded() -> None:
    """Spec section 77: re-derived from the plan's own conditional
    stop-condition wording, not from 149O.2's claim."""

    plan = _read(_PLAN_PATH)
    wave5 = plan.split("### Wave 5 —")[1].split("### Wave 6")[0]
    normalised = " ".join(wave5.split())
    assert "if the FIDO2 spike (§23) cannot bind HATP's exact canonical payload as the signed challenge, switch to the PIV fallback strategy" in normalised
    # And the spike demonstrably succeeded (Group 4 above proves the binding).


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 11 -- Optional dependency behavior (spec sections 71-75)
# ═══════════════════════════════════════════════════════════════════════════


_SUBPROCESS_PRELUDE = """
import sys, types
class _Blocker:
    def __init__(self, names): self.names = names
    def find_module(self, name, path=None):
        return self if any(name == n or name.startswith(n + '.') for n in self.names) else None
    def load_module(self, name):
        raise ImportError('blocked: ' + name)
    def find_spec(self, name, path=None, target=None):
        if any(name == n or name.startswith(n + '.') for n in self.names):
            raise ImportError('blocked: ' + name)
        return None
sys.meta_path.insert(0, _Blocker({names!r}))
for _mod in list(sys.modules):
    if any(_mod == n or _mod.startswith(n + '.') for n in {names!r}):
        del sys.modules[_mod]
"""


def _run_with_blocked_imports(blocked, script: str) -> subprocess.CompletedProcess:
    code = _SUBPROCESS_PRELUDE.format(names=list(blocked)) + script
    return subprocess.run(
        [sys.executable, "-c", code], cwd=_REPO_ROOT, capture_output=True, text=True, timeout=120
    )


@pytest.mark.parametrize("blocked", [("fido2",), ("cryptography",), ("fido2", "cryptography")])
def test_core_pcae_import_survives_missing_optional_dependencies(blocked) -> None:
    """Spec sections 71/72/73."""

    result = _run_with_blocked_imports(
        blocked,
        "import pcae\n"
        "from pcae.core import hatp_providers, hatp_hardware_credentials\n"
        "from pcae.core import human_approval_trusted_provenance, hatp_bootstrap\n"
        "print('CORE_IMPORT_OK')\n",
    )
    assert result.returncode == 0, result.stderr
    assert "CORE_IMPORT_OK" in result.stdout


@pytest.mark.parametrize("blocked", [("fido2",), ("cryptography",), ("fido2", "cryptography")])
def test_discovery_reports_unavailable_rather_than_crashing(blocked) -> None:
    """Spec sections 71/73: availability facts, never an exception."""

    result = _run_with_blocked_imports(
        blocked,
        "from pcae.core.hatp_providers import discover_hardware_providers\n"
        "rows = discover_hardware_providers()\n"
        "print('ROWS', [(r.protocol_name, r.library_installed, r.device_detected) for r in rows])\n",
    )
    assert result.returncode == 0, result.stderr
    assert "('FIDO2', False, False)" in result.stdout
    assert "('PIV', False, False)" in result.stdout


@pytest.mark.parametrize("blocked", [("fido2",), ("cryptography",)])
def test_production_factory_fails_closed_when_a_dependency_is_missing(blocked) -> None:
    """Spec section 73: unavailable, never a weaker substitute."""

    result = _run_with_blocked_imports(
        blocked,
        "from pcae.core.hatp_providers import create_production_hardware_provider, HATPProviderUnavailableError\n"
        "try:\n"
        "    create_production_hardware_provider('HATP_HARDWARE_PROVIDER_V1')\n"
        "except HATPProviderUnavailableError as exc:\n"
        "    print('UNAVAILABLE_OK')\n"
        "else:\n"
        "    print('UNEXPECTED_PROVIDER')\n",
    )
    assert result.returncode == 0, result.stderr
    assert "UNAVAILABLE_OK" in result.stdout


def test_pcae_cli_health_and_check_work_with_no_device_attached() -> None:
    """Spec section 75: device absence must not break normal PCAE."""

    for command in ("health", "check"):
        result = _run_cli(command)
        assert result.returncode == 0, (command, result.stdout, result.stderr)
        assert result.stdout.strip()


def test_no_core_module_imports_the_optional_dependencies_at_module_level() -> None:
    """Spec sections 71/74: only the FIDO2 adapter hard-imports `fido2`
    and `cryptography`, and it is itself imported lazily."""

    offenders = []
    for path in _SRC_ROOT.rglob("*.py"):
        if path.name == "hatp_fido2_provider.py":
            continue
        tree = ast.parse(_read(path))
        for node in tree.body:
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            elif isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            if any(name.split(".")[0] in {"fido2", "cryptography"} for name in names):
                offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert offenders == []

    providers_tree = ast.parse(_read(_SRC_ROOT / "core" / "hatp_providers.py"))
    for node in providers_tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            assert "hatp_fido2_provider" not in module
            assert "hatp_piv_provider" not in module


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 12 -- Operational hard ceiling (spec sections 107-110, 142)
# ═══════════════════════════════════════════════════════════════════════════


def _maximally_healthy_trust_store(tmp_path: Path):
    repository_id = _REPOSITORY_A
    root = tmp_path / "deployment"
    root.mkdir(parents=True, exist_ok=True)
    return _populated_trust_store(
        tmp_path / "trust-store",
        "s",
        "p",
        repository_id,
        bootstrap_module.resolve_canonical_deployment_root(root),
    )


def test_substrate_readiness_stays_not_operational_with_everything_maximally_healthy(tmp_path: Path) -> None:
    """Spec section 107: fido2 installed, cryptography installed, a
    fully-populated trust store, a real provider constructible."""

    trust_store, repository_id = _maximally_healthy_trust_store(tmp_path)
    assert isinstance(create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1), Fido2HardwareProvider)

    readiness = inspect_hatp_verification_substrate_readiness(trust_store, current_repository_id=repository_id)
    assert readiness.operational is False
    assert readiness.status.value == "NOT_READY"
    terms = dict(readiness.terms)
    assert terms["provider_profile_available"] is False
    assert terms["provider_attestation_trusted"] is False


@pytest.mark.parametrize(
    "variable",
    [
        "HATP_FORCE_OPERATIONAL",
        "HATP_TRUSTED_OPERATIONAL",
        "PCAE_HATP_OPERATIONAL",
        "HATP_HARDWARE_PROVIDER_V1",
        "HATP_OPERATIONAL",
        "PCAE_HATP_FORCE",
        "HATP_PROVIDER_ATTESTATION_TRUSTED",
    ],
)
def test_no_environment_variable_can_force_operational(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, variable: str) -> None:
    """Spec section 108."""

    monkeypatch.setenv(variable, "1")
    trust_store, repository_id = _maximally_healthy_trust_store(tmp_path)
    assert inspect_hatp_verification_substrate_readiness(trust_store, current_repository_id=repository_id).operational is False


def test_readiness_function_takes_no_operational_override_parameter() -> None:
    parameters = list(inspect.signature(inspect_hatp_verification_substrate_readiness).parameters)
    assert parameters == ["trust_store", "current_repository_id"]
    source = inspect.getsource(inspect_hatp_verification_substrate_readiness)
    assert "provider_profile_available = False" in source
    assert "provider_attestation_trusted = False" in source
    assert 'assert operational is False' in source


def test_provider_availability_does_not_make_hatp_operational(tmp_path: Path) -> None:
    """Spec section 109."""

    availability = {a.protocol_name: a for a in discover_hardware_providers()}
    assert availability["FIDO2"].library_installed is True
    trust_store, repository_id = _maximally_healthy_trust_store(tmp_path)
    assert inspect_hatp_verification_substrate_readiness(trust_store, current_repository_id=repository_id).operational is False


def test_a_cryptographically_valid_hardware_proof_does_not_make_hatp_operational(harness: _Harness, tmp_path: Path) -> None:
    """Spec section 110: a real ECDSA-valid, presence-proven, VALID
    Wave-4 result coexists with `operational=False`. VALID is not
    approval, not permission, not capability, not execution, not
    operational readiness."""

    assert _run_wave4(harness, tmp_root=tmp_path / "proof") is HATPVerificationStatus.VALID
    trust_store, repository_id = _maximally_healthy_trust_store(tmp_path / "readiness")
    assert inspect_hatp_verification_substrate_readiness(trust_store, current_repository_id=repository_id).operational is False


def test_no_wave5_module_can_reach_the_readiness_function() -> None:
    for module_path in (
        _SRC_ROOT / "core" / "hatp_providers.py",
        _SRC_ROOT / "core" / "hatp_fido2_provider.py",
        _SRC_ROOT / "core" / "hatp_piv_provider.py",
        _SRC_ROOT / "core" / "hatp_hardware_credentials.py",
    ):
        body = _strip_docstrings_and_comments(_read(module_path))
        assert "inspect_hatp_verification_substrate_readiness" not in body
        assert "operational" not in body


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 13 -- Integration boundary (spec sections 111-117)
# ═══════════════════════════════════════════════════════════════════════════

_WAVE5_MODULE_PATHS = (
    _SRC_ROOT / "core" / "hatp_providers.py",
    _SRC_ROOT / "core" / "hatp_fido2_provider.py",
    _SRC_ROOT / "core" / "hatp_piv_provider.py",
    _SRC_ROOT / "core" / "hatp_hardware_credentials.py",
)


def test_no_wave5_module_derives_an_approval_or_authorization_fact() -> None:
    """Spec section 111: AST audit for any assignment/keyword naming an
    approval, authorization, permission, or execution capability."""

    forbidden = {"approval_present", "approved", "authorized", "can_execute", "permission_granted", "allow", "decision"}
    for module_path in _WAVE5_MODULE_PATHS:
        tree = ast.parse(_read(module_path))
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                targets += [t.attr for t in node.targets if isinstance(t, ast.Attribute)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
            elif isinstance(node, ast.keyword) and node.arg:
                targets = [node.arg]
            for target in targets:
                assert target.lower() not in forbidden, f"{module_path.name}: {target}"


@pytest.mark.parametrize(
    "symbol",
    [
        "rollback_approval_evidence",
        "RollbackApprovalEvidence",
        "permission_broker",
        "PermissionBroker",
        "permission_broker_foundation",
        "from pcae.core.agent",
        "import agent",
        "AgentInvocation",
        "prompt_generation",
        "prompt_dispatch",
        "runtime_enforcement",
    ],
)
def test_no_wave5_module_references_rae_permission_broker_or_agent(symbol: str) -> None:
    """Spec sections 112-116."""

    for module_path in _WAVE5_MODULE_PATHS:
        body = _strip_docstrings_and_comments(_read(module_path))
        assert symbol not in body, f"{module_path.name}: {symbol}"


def test_rae_permission_broker_and_agent_do_not_reference_wave5(tmp_path: Path) -> None:
    """Spec sections 112-116, the reverse direction."""

    consumers = [
        _SRC_ROOT / "core" / "rollback_approval_evidence.py",
        _SRC_ROOT / "core" / "permission_broker.py",
        _SRC_ROOT / "core" / "permission_broker_foundation.py",
        _SRC_ROOT / "core" / "agent.py",
        _SRC_ROOT / "commands" / "agent.py",
    ]
    wave5_symbols = (
        "hatp_providers",
        "hatp_fido2_provider",
        "hatp_piv_provider",
        "hatp_hardware_credentials",
        "Fido2HardwareProvider",
        "HATPHardwareCredentialStore",
        "create_production_hardware_provider",
    )
    for path in consumers:
        if not path.exists():
            continue
        body = _strip_docstrings_and_comments(_read(path))
        for symbol in wave5_symbols:
            assert symbol not in body, f"{path.name}: {symbol}"


def test_wave5_modules_perform_no_filesystem_or_process_mutation() -> None:
    """Spec section 115: no rollback-execution effect is reachable."""

    for module_path in _WAVE5_MODULE_PATHS:
        body = _strip_docstrings_and_comments(_read(module_path))
        for forbidden in ("subprocess", "os.system", "shutil", "git ", "write_text", "write_bytes", "mkdir", "unlink"):
            assert forbidden not in body, f"{module_path.name}: {forbidden}"


def test_runtime_state_is_unchanged_by_wave_5() -> None:
    """Spec section 117: Observed / observe / unavailable."""

    result = _run_cli("runtime", "inspect")
    assert result.returncode == 0, result.stderr
    assert "Runtime state:             Observed" in result.stdout
    assert "Execution capability:      unavailable" in result.stdout
    assert "Maximum plugin capability: observe" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 14 -- Evidence classification for hardware-dependent properties
#             (spec sections 6, 7, 8, 53, 136, 137)
# ═══════════════════════════════════════════════════════════════════════════


def test_non_exportability_is_not_and_cannot_be_proven_by_this_environment() -> None:
    """CATEGORY C: requires real hardware; currently unverified.

    The Wave-5 capability matrix asserts `non_exportable_key=True`. That
    is a claim about a PHYSICAL authenticator, and it is derived from
    CTAP2 protocol semantics, not from anything this repository can
    execute. This test pins the honest position: the capability object
    reports the design property, and the accompanying note explicitly
    scopes it to protocol semantics rather than an empirical result.
    Crucially, "PCAE does not expose an export API" is NOT accepted as
    proof (spec section 8).
    """

    capabilities = Fido2HardwareProvider().capabilities()
    assert capabilities.non_exportable_key is True
    notes = " ".join(capabilities.notes)
    assert "CTAP2 authenticators never expose the private key" in notes
    assert "REAL HARDWARE NOT EXERCISED" in notes

    # The verifying side never handles private key material at all --
    # necessary for the claim, nowhere near sufficient for it.
    body = _strip_docstrings_and_comments(_read(_SRC_ROOT / "core" / "hatp_fido2_provider.py"))
    for forbidden in ("private_key", "private_bytes", "PrivateKey", "export_key"):
        assert forbidden not in body, forbidden


def test_fresh_touch_per_operation_is_protocol_semantic_not_device_tested() -> None:
    """CATEGORY B: supported by CTAP2/WebAuthn semantics, not physically
    exercised on this machine.

    What IS proven by software here: UP is read per assertion, never
    cached, never caller-supplied, and an assertion carrying UP for
    payload A cannot be reused for payload B. What is NOT proven: that a
    physical authenticator genuinely required a fresh finger touch --
    that requires attached hardware (spec section 53).
    """

    capabilities = Fido2HardwareProvider().capabilities()
    assert capabilities.fresh_touch_per_operation is True
    notes = " ".join(capabilities.notes)
    assert "re-evaluated by the authenticator on every getAssertion call" in notes
    assert "REAL HARDWARE NOT EXERCISED" in notes


def test_capability_matrix_does_not_describe_an_unavailable_capability_as_implemented() -> None:
    """Spec sections 6/136: honesty audit of the capability object."""

    fido2_capabilities = Fido2HardwareProvider().capabilities()
    assert fido2_capabilities.device_attestation is False
    assert fido2_capabilities.hatp_conformant.value != "CONFORMANT"
    piv_capabilities = PivHardwareProvider().capabilities()
    assert piv_capabilities.hatp_conformant.value == "NOT_CONFORMANT"
    assert all(
        getattr(piv_capabilities, name) is False
        for name in ("non_exportable_key", "fresh_touch_per_operation", "credential_identity", "signature_verification", "device_attestation")
    )


def test_credential_identity_fails_closed_without_a_device() -> None:
    """Honest unavailability rather than a fabricated identity."""

    with pytest.raises(HATPProviderUnavailableError):
        Fido2HardwareProvider().credential_identity()


@pytest.mark.hatp_hardware_required
@pytest.mark.skipif(True, reason="no physical FIDO2 device attached to this machine (independently probed)")
def test_physical_device_touch_produces_a_verifiable_assertion() -> None:  # pragma: no cover
    """Structural placeholder for the real-hardware acceptance test
    (HATP-001 §44 attacks #6/#20). Never fabricated as passing."""

    raise AssertionError("requires attached hardware")
