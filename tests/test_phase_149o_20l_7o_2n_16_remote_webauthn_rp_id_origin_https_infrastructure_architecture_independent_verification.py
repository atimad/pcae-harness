"""Phase 149O.20L.7O.2N.16 -- Remote WebAuthn RP-ID/Origin/HTTPS
Infrastructure Architecture Independent Verification.

Fresh, independently-derived verification tests -- deliberately NOT
copied from Phase 149O.20L.7O.2N.15's own architecture document or any
prior phase's test suite. These mechanically re-check the load-bearing
primary-source claims the 2N.15 architecture selection makes, against
current production source and current contract text, not against the
architecture document's own prose.

VERIFICATION ONLY. No provisioning. No implementation. No hardware. No
DNS/TLS/reverse-proxy/VPN artifact is created, installed, or configured
here. No literal hostname is selected here.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ARCH_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_15_REMOTE_WEBAUTHN_RP_ID_ORIGIN_HTTPS_INFRASTRUCTURE_ARCHITECTURE.md"
)
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HBDC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_PHASE_ENTRY_COMMIT = "6901ecc7"  # 149O.20L.7O.2N.15's final commit, immediately pre-2N.16


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git_show(rev: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_hrwp_requirement_numbering_still_complete_sequential_no_gaps():
    text = _text(_HRWP_PATH)
    numbers = [int(n) for n in re.findall(r"\*\*HRWP-REQ-(\d+)(?:\s*\([^)]*\))?\.\*\*", text)]
    assert numbers == list(range(1, 69)), "HRWP-REQ-001..068 must remain sequential, gapless, unique"


def test_hrac_requirement_numbering_still_complete_sequential_no_gaps():
    text = _text(_HRAC_PATH)
    numbers = [int(n) for n in re.findall(r"\*\*HRAC-REQ-(\d+)\.\*\*", text)]
    assert numbers == list(range(1, 77)), "HRAC-REQ-001..076 must remain sequential, gapless, unique"


def test_hrwp_027_029_031_open_infrastructure_requirements_present_and_unresolved_by_hrwp_itself():
    """Independently re-derives the exact requirement text the governing
    prompt named (HRWP-REQ-027/029/031) and confirms HRWP-001 itself
    still names these as open (does not select a literal hostname)."""
    text = _text(_HRWP_PATH)
    assert "**HRWP-REQ-027.**" in text
    assert "does NOT select a literal hostname value" in text
    assert "**HRWP-REQ-029.**" in text
    assert "never `http://`, never a wildcard" in text
    assert "**HRWP-REQ-031.**" in text
    assert "This contract does not select a certificate authority" in text


def test_hbdc_contract_defines_no_network_dns_vpn_topology_requirement():
    """Independently confirms 2N.15's §2 claim: HBDC-001 (deployment
    topology / OS-principal / Protected Root) defines no network
    reachability, DNS, or VPN requirement -- this architecture phase is
    free to select network topology without HBDC-001 conflict."""
    text = _text(_HBDC_PATH).lower()
    # HBDC-001 may still use the word "network" in an unrelated sense
    # (e.g. describing threat classes); the load-bearing claim is that no
    # normative HBDC-REQ-### sentence fixes DNS/VPN/reverse-proxy
    # topology. Confirm no requirement sentence contains any of these
    # infrastructure nouns.
    req_bodies = re.findall(r"\*\*hbdc-req-\d+\.\*\*([^\n]*)", text)
    assert req_bodies, "expected at least one HBDC-REQ-### sentence"
    forbidden = ("vpn", "reverse proxy", "dns record", "wireguard", "acme")
    for body in req_bodies:
        for word in forbidden:
            assert word not in body, f"HBDC-001 requirement unexpectedly constrains network topology: {word!r}"


def test_local_fido2_provider_rp_id_and_origin_constants_unchanged_by_this_phase():
    """Confirms this verification phase touches nothing in the local raw
    FIDO2 path -- the two providers remain disjoint by design."""
    src = _text(_REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py")
    assert '_HATP_RP_ID = "hatp.pcae.local"' in src
    assert '_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"' in src


def test_protocol_values_includes_webauthn_and_remains_closed():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert _PROTOCOL_VALUES == frozenset({"FIDO2", "PIV", "WEBAUTHN"})


def test_production_provider_dispatch_still_does_not_include_remote_webauthn():
    """Independently confirms 2N.15's own §1 finding is still true: adding
    a provider_profile string is a separate, still-unperformed dispatch
    decision this architecture phase does not touch or depend on."""
    src = _text(_REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py")
    assert "_PRODUCTION_HARDWARE_PROVIDER_PROFILES = (HATP_HARDWARE_PROVIDER_V1,)" in src
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in src


def test_no_remote_webauthn_or_infrastructure_implementation_source_exists():
    """VERIFICATION ONLY: confirms no reverse-proxy, ACME, VPN, or
    RemoteWebAuthnProvider server/client source exists anywhere in
    src/pcae/** as of this phase."""
    core_dir = _REPO_ROOT / "src" / "pcae"
    forbidden_name_fragments = (
        "remote_webauthn",
        "webauthn_provider",
        "webauthn_server",
        "reverse_proxy",
        "acme_client",
        "vpn_",
    )
    for path in core_dir.rglob("*.py"):
        lowered = path.name.lower()
        assert not any(frag in lowered for frag in forbidden_name_fragments), path


def test_no_dns_tls_reverse_proxy_or_vpn_configuration_files_exist_in_repository():
    """VERIFICATION ONLY: confirms no infrastructure artifact (Caddyfile,
    nginx.conf, wireguard config, ACME account state) has been
    provisioned anywhere under version control."""
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.lower().splitlines()
    forbidden_names = ("caddyfile", "nginx.conf", "wg0.conf", "wireguard", ".well-known/acme-challenge")
    for name in forbidden_names:
        assert not any(name in line for line in tracked), f"unexpected infrastructure artifact: {name}"


def test_architecture_document_does_not_freeze_a_literal_hostname():
    """Confirms 2N.15 selected the RP-ID/origin *model* only -- no real,
    literal domain/hostname string is frozen as the actual value.
    Every concrete example in the document uses an explicit placeholder
    form (<controlled-domain> or a documented illustrative example),
    never a bare registrable-looking literal presented as the selection
    itself."""
    text = _text(_ARCH_DOC)
    assert "<controlled-domain>" in text
    assert "NOT YET SELECTED" not in text  # that phrasing belongs to the governing prompt, not this doc
    # The selection lines must all carry the placeholder, not a concrete domain.
    selection_lines = [
        line for line in text.splitlines() if "Selected:" in line and "RP-ID" not in line
    ]
    for line in selection_lines:
        if "hatp." in line:
            assert "<controlled-domain>" in line, line


def test_architecture_document_selects_dns_01_not_http_01():
    text = _text(_ARCH_DOC)
    assert "DNS-01" in text
    assert "HTTP-01" not in text or "rather than HTTP-01" in text


def test_architecture_document_selects_vpn_mesh_reachability_not_public():
    text = _text(_ARCH_DOC)
    assert "VPN mesh" in text or "VPN-mesh" in text
    assert "reachable only over a private network path" in text


def test_architecture_document_names_reverse_proxy_and_companion_process_as_thin_adapter_not_trusted_kernel():
    text = _text(_ARCH_DOC)
    assert "TRUSTED KERNEL" in text
    assert "ADAPTER" in text
    # The reverse proxy box must be on the adapter side, not the trusted-kernel side.
    reverse_proxy_idx = text.index("Reverse proxy")
    trusted_kernel_idx = text.index("TRUSTED KERNEL")
    adapter_idx = text.index("ADAPTER")
    assert adapter_idx < trusted_kernel_idx
    assert reverse_proxy_idx < trusted_kernel_idx


def test_hrac_session_locator_is_not_authority_requirement_present():
    """Re-derives HRAC-REQ-027/HRWP-REQ-045: ceremony-link/session
    possession is never itself authority -- load-bearing for this
    phase's proxy/VPN-compromise threat-model analysis."""
    text = _text(_HRAC_PATH)
    assert "SHALL NOT itself constitute PCAE governance authority" in text
    hrwp_text = _text(_HRWP_PATH)
    assert "SHALL NOT itself constitute PCAE governance authority" in hrwp_text


def test_pre_2n16_checkpoint_had_no_remote_webauthn_source_either():
    """Historical re-derivation: confirms the fixed phase-entry commit
    (immediately pre-2N.16) already had no remote-WebAuthn source, so
    this phase's own "no implementation occurred" claim is meaningful
    against a real prior state, not vacuous."""
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", _PHASE_ENTRY_COMMIT, "--", "src/pcae/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.lower()
    for frag in ("remote_webauthn", "webauthn_provider", "webauthn_server", "reverse_proxy"):
        assert frag not in listing


def test_deployment_binding_still_carries_no_protocol_or_transport_field():
    src = _text(_REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py")
    m = re.search(r"class DeploymentBinding:\n((?:    \w[\w_]*: .+\n)+)", src)
    assert m is not None
    fields = {line.split(":")[0].strip() for line in m.group(1).strip().splitlines()}
    forbidden = {"protocol_name", "protocol", "transport", "transports", "network", "vpn"}
    assert not (fields & forbidden), f"unexpected field(s): {fields & forbidden}"
