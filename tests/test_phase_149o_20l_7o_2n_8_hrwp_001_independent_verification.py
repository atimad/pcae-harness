"""Phase 149O.20L.7O.2N.8 -- HRWP-001 Independent Verification.

Fresh, independently-derived verification tests -- deliberately NOT
copied from Phase 149O.20L.7O.2N.7's own test suite. These mechanically
re-check the load-bearing primary-source claims HRWP-001 v1.0 makes,
against current production source, not against the contract's own
prose.

VERIFICATION ONLY. No implementation. No hardware. No real credential,
provider, HTTP route, or protocol_name vocabulary change is created
here.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_PHASE_ENTRY_COMMIT = "c847f3a8"  # 149O.20L.7O.2N.7's final commit, immediately pre-2N.8


def _hrwp_text() -> str:
    return _HRWP_PATH.read_text(encoding="utf-8")


def _git_show(rev: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_hrwp_requirement_numbering_is_complete_sequential_no_gaps_no_duplicates():
    text = _hrwp_text()
    # Matches both an original heading ("**HRWP-REQ-019.**") and an
    # in-place-revised one ("**HRWP-REQ-019 (revised, v1.1 ...).**"),
    # mirroring HHCE-REQ-002 v1.1's identical in-place-revision heading
    # style -- a requirement's identity/number is unchanged by revision.
    numbers = [int(n) for n in re.findall(r"\*\*HRWP-REQ-(\d+)(?:\s*\([^)]*\))?\.\*\*", text)]
    assert numbers == list(range(1, 69)), "HRWP-REQ-001..068 must be sequential, gapless, unique"
    assert "68 normative requirements" in text or "HRWP-REQ-068" in text


def test_local_fido2_provider_signs_authenticatorData_concat_clientDataHash():
    """Independently re-derives HRWP-REQ-046's central cryptographic claim
    directly from source, not from the contract's own prose."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py").read_text(encoding="utf-8")
    assert "cose_key.verify(bytes(parsed.authenticator_data) + parsed.client_data.hash, parsed.signature)" in src
    # Challenge is bound to the exact canonical payload digest, not an
    # arbitrary/pre-digested caller value.
    assert "_payload_digest(canonical_payload)" in src or "_payload_digest(payload)" in src


def test_local_provider_rp_id_and_origin_are_non_web_constants_not_reusable_verbatim():
    """Independently confirms HRWP-REQ-026's claim: the local provider's
    RP-ID/origin constants are internal, non-HTTPS, and therefore not
    directly reusable for a browser-mediated remote WebAuthn RP ID."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py").read_text(encoding="utf-8")
    assert '_HATP_RP_ID = "hatp.pcae.local"' in src
    assert '_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"' in src
    assert not src.count('_HATP_ORIGIN = "https://')


def test_hardware_credential_record_provider_profile_is_open_string_field():
    """Confirms HRWP-REQ-008's premise: provider_profile on
    HardwareCredentialRecord is NOT validated against a closed
    allowlist at the registry-record layer (only non-empty-string), so
    a new provider_profile literal requires no registry-schema code
    change."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py").read_text(encoding="utf-8")
    assert "provider_profile must be a non-empty string" in src
    assert "_PROVIDER_PROFILE_VALUES" not in src


def test_hardware_credential_record_protocol_name_WAS_a_closed_enum_contradicting_HRWP_REQ_019_v1_0():
    """NON-BLOCKING FINDING (this phase's own, historically confirmed):
    HRWP-REQ-019 v1.0 claimed protocol_name = "WEBAUTHN" requires "no
    schema widening" because HHCE-REQ-002 describes it as "a plain
    string field, not a closed enum in code." Independent source
    inspection at this phase's own commit showed this was inaccurate:
    `_parse_credential` validated `protocol_name` against a closed
    `_PROTOCOL_VALUES` frozenset containing only {"FIDO2", "PIV"}.

    Disposition trail: HRWP-001 v1.1 (Phase 149O.20L.7O.2N.11, §45)
    repaired the CONTRACT TEXT to state this accurately
    (NBF-149O.20L.7O.2N.8-1, closed). Phase 149O.20L.7O.2N.13 then
    performed the PRODUCTION repair this finding's text names as the
    remaining work: `_PROTOCOL_VALUES` is now additively widened to
    include "WEBAUTHN" (see that phase's own dedicated test module).
    This test now asserts only the historical fact, re-derived from git
    history rather than current source."""
    src = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_hardware_credentials.py")
    match = re.search(r'_PROTOCOL_VALUES\s*=\s*frozenset\(\{([^}]*)\}\)', src)
    assert match is not None, "expected a closed _PROTOCOL_VALUES frozenset in hatp_hardware_credentials.py"
    values = {v.strip().strip('"') for v in match.group(1).split(",") if v.strip()}
    assert values == {"FIDO2", "PIV"}
    assert "WEBAUTHN" not in values


def test_hardware_credential_record_protocol_name_now_includes_webauthn():
    """Current production: the widening this finding named as required
    future work has since been performed (Phase 149O.20L.7O.2N.13)."""
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert {"FIDO2", "PIV", "WEBAUTHN"} <= _PROTOCOL_VALUES


def test_deployment_binding_schema_carries_no_protocol_or_transport_field():
    """Independently confirms HRWP-REQ-058's claim: DeploymentBinding has
    exactly repository_id/canonical_deployment_root/principal_id/
    signer_key_id/provider_profile/authority_scope -- no protocol or
    transport field, so remote-vs-local credential selection needs no
    DeploymentBinding schema change."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py").read_text(encoding="utf-8")
    m = re.search(r"class DeploymentBinding:\n((?:    \w[\w_]*: .+\n)+)", src)
    assert m is not None
    fields = {line.split(":")[0].strip() for line in m.group(1).strip().splitlines()}
    expected_minimum = {
        "repository_id",
        "canonical_deployment_root",
        "principal_id",
        "signer_key_id",
        "provider_profile",
        "authority_scope",
    }
    assert expected_minimum.issubset(fields)
    forbidden = {"protocol_name", "protocol", "transport", "transports"}
    assert not (fields & forbidden), f"unexpected protocol/transport field(s): {fields & forbidden}"


def test_signing_time_resolution_never_calls_provider_credential_identity():
    """Independently confirms HSCE-001 v1.3 Model B is what HRWP-001
    relies on: signing-time signer/principal resolution
    (`_resolve_deployment_binding_signer`) reads only the durable
    DeploymentBinding/SignerRecord/PrincipalRecord/HardwareCredentialRecord
    registries -- it never calls the hardware provider's own
    `credential_identity()`."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
    fn_match = re.search(
        r"def _resolve_deployment_binding_signer\(.*?\n(?=\ndef |\Z)", src, re.DOTALL
    )
    assert fn_match is not None
    body = fn_match.group(0)
    assert "credential_identity(" not in body
    assert "resolve_deployment_authorization" in body


def test_local_fido2_provider_reports_no_device_attestation_capability():
    """Independently confirms HRWP-REQ-024's parity premise: the local
    provider does not require/evaluate device attestation today."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py").read_text(encoding="utf-8")
    assert "device_attestation=False" in src
    assert "attestation_valid=None" in src


def test_production_provider_profile_allowlist_is_a_closed_one_member_tuple():
    """Independently confirms HRWP-REQ-006's premise: provider selection
    dispatch is a closed, compile-time allowlist -- adding remote WebAuthn
    requires an explicit future factory-dispatch decision, not automatic
    pickup."""
    src = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py").read_text(encoding="utf-8")
    assert "_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)" in src


def test_no_remote_webauthn_implementation_source_exists_yet():
    """VERIFICATION ONLY: confirms this and the predecessor phase did not
    implement any of the components HRWP-001 §36 names as future
    authority-bearing surfaces."""
    core_dir = _REPO_ROOT / "src" / "pcae" / "core"
    forbidden_name_fragments = ("remote_webauthn", "webauthn_provider", "webauthn_server")
    for path in core_dir.glob("*.py"):
        lowered = path.name.lower()
        assert not any(frag in lowered for frag in forbidden_name_fragments), path
