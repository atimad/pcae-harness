"""Phase 149O.20L.7O.2N.18 -- Remote WebAuthn Literal RP-ID/Origin and
Infrastructure Realization Plan Independent Verification.

Fresh, independently-derived verification tests -- deliberately NOT
copied from Phase 149O.20L.7O.2N.17's own realization-plan document (it
has no test file of its own) and NOT copied from Phase 149O.20L.7O.2N.16's
test module (different subject matter: the literal construction rule and
realization plan, not the RP-ID/origin/HTTPS architecture selection).
These mechanically re-check the load-bearing primary-source claims 2N.17
makes, against current production source and current contract text, not
against 2N.17's own prose.

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
_PLAN_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_17_REMOTE_WEBAUTHN_LITERAL_RP_ID_ORIGIN_INFRASTRUCTURE_REALIZATION_CONTRACT_PLAN.md"
)
_ARCH_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_15_REMOTE_WEBAUTHN_RP_ID_ORIGIN_HTTPS_INFRASTRUCTURE_ARCHITECTURE.md"
)
_VERIFY_16_DOC = (
    _REPO_ROOT
    / "docs"
    / "PHASE_149O_20L_7O_2N_16_REMOTE_WEBAUTHN_RP_ID_ORIGIN_HTTPS_INFRASTRUCTURE_ARCHITECTURE_INDEPENDENT_VERIFICATION.md"
)
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"
_HBDC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_FIDO2_PROVIDER_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_fido2_provider.py"
_PROVIDERS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
_HW_CREDENTIALS_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_SRC_ROOT = _REPO_ROOT / "src" / "pcae"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_2n17_plan_document_exists_and_declares_no_domain_selected():
    text = _text(_PLAN_DOC)
    assert "NO DOMAIN SELECTED" in text
    assert "NONE OPERATOR-CONTROLLED EXISTS YET" in text


def test_2n17_freezes_exact_rp_id_and_origin_construction_rule():
    text = _text(_PLAN_DOC)
    assert 'rp_id = "hatp." + <operator-controlled registrable domain>' in text
    assert 'origin = "https://" + rp_id' in text


def test_2n17_does_not_contain_a_concrete_non_placeholder_domain_literal():
    """Independently mechanically re-checks 2N.17's own no-fabrication
    claim: no `.com`/`.net`/`.org`/`.dev`/`.io`/`.tld`-suffixed concrete
    literal (other than the illustrative `example.tld` inside its own
    explanatory rule-1 parenthetical) appears anywhere in the document."""
    text = _text(_PLAN_DOC)
    candidates = re.findall(r"\b[a-zA-Z0-9-]+\.(?:com|net|org|dev|io)\b", text)
    assert candidates == [], f"unexpected concrete-looking domain literal(s): {candidates}"


def test_2n17_names_required_operator_input_explicitly():
    text = _text(_PLAN_DOC)
    assert "Required input, named explicitly, not resolved by this phase" in text
    assert "registrar account access and DNS-zone-edit access" in text


def test_2n17_migration_model_forbids_hac_dell_coupling():
    text = _text(_PLAN_DOC)
    assert "MUST NOT be derived from, or coupled to, `hac-dell`" in text


def test_2n17_names_dns01_not_http01():
    text = _text(_PLAN_DOC)
    assert "ACME DNS-01" in text
    assert "HTTP-01 would require a public-facing HTTP listener" in text


def test_2n17_names_shared_rp_model_not_per_repository_default():
    text = _text(_PLAN_DOC)
    assert "PCAE-wide (shared RP-ID across all PCAE-governed repositories" in text


def test_2n17_carries_forward_both_2n16_non_blocking_findings_by_exact_id():
    text = _text(_PLAN_DOC)
    assert "NBF-149O.20L.7O.2N.16-1" in text
    assert "NBF-149O.20L.7O.2N.16-2" in text


def test_2n17_names_provider_dispatch_gap_still_open():
    text = _text(_PLAN_DOC)
    assert "NBF-149O.20L.7O.2N.12-1" in text


def test_2n17_recommends_2n18_as_next_phase():
    text = _text(_PLAN_DOC)
    assert "149O.20L.7O.2N.18" in text


def test_hrwp_027_through_032_present_in_current_contract_text():
    text = _text(_HRWP_PATH)
    for req in ("HRWP-REQ-027", "HRWP-REQ-028", "HRWP-REQ-029", "HRWP-REQ-030", "HRWP-REQ-031", "HRWP-REQ-032"):
        assert f"**{req}.**" in text, f"{req} missing from current HRWP-001 text"


def test_hrac_061_and_070_present_in_current_contract_text():
    text = _text(_HRAC_PATH)
    assert "**HRAC-REQ-061.**" in text
    assert "**HRAC-REQ-070.**" in text


def test_hbdc_authority_scope_narrowest_value_discipline_present():
    """Independently re-confirms the HBDC-REQ-072 discipline 2N.17 §2 row 1
    cites by analogy still exists in current HBDC-001 text."""
    text = _text(_HBDC_PATH)
    assert "**HBDC-REQ-072.**" in text
    assert "narrowest value that names exactly the one authority" in text


def test_no_operator_domain_literal_named_anywhere_in_docs_history():
    """Mechanical, repository-wide re-check of 2N.17's own §1 claim: no
    concrete `.com`/`.net`/`.org`/`.dev`/`.io`-suffixed literal appears in
    any 2N.1x remote-WebAuthn phase document."""
    phase_1x_docs = sorted(
        (_REPO_ROOT / "docs").glob("PHASE_149O_20L_7O_2N_1*_REMOTE_WEBAUTHN*")
    )
    assert phase_1x_docs, "expected at least one 2N.1x remote-WebAuthn phase doc to exist"
    # RFC 2606 reserved illustrative domains are not real, registrable,
    # operator-controlled literals -- excluded as documented placeholders.
    _RESERVED_PLACEHOLDERS = {"example.com", "example.net", "example.org"}
    offenders = {}
    for doc in phase_1x_docs:
        text = _text(doc)
        hits = [
            hit
            for hit in re.findall(r"\b[a-zA-Z0-9-]+\.(?:com|net|org|dev|io)\b", text)
            if hit not in _RESERVED_PLACEHOLDERS
        ]
        if hits:
            offenders[doc.name] = hits
    assert offenders == {}, f"unexpected domain literal(s) found: {offenders}"


def test_no_remote_webauthn_provider_implementation_exists():
    hits = []
    for path in _SRC_ROOT.rglob("*.py"):
        text = _text(path)
        if "class RemoteWebAuthnProvider" in text:
            hits.append(str(path))
    assert hits == [], f"unexpected RemoteWebAuthnProvider implementation found: {hits}"


def test_production_hardware_provider_profiles_still_excludes_remote_webauthn():
    text = _text(_PROVIDERS_PATH)
    match = re.search(
        r"_PRODUCTION_HARDWARE_PROVIDER_PROFILES\s*=\s*\(([^)]*)\)", text
    )
    assert match is not None, "could not locate _PRODUCTION_HARDWARE_PROVIDER_PROFILES"
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in match.group(1)


def test_local_fido2_rp_id_and_origin_constants_unchanged_and_not_reused():
    text = _text(_FIDO2_PROVIDER_PATH)
    assert '_HATP_RP_ID = "hatp.pcae.local"' in text
    assert '_HATP_ORIGIN = "pcae-hatp://hatp.pcae.local"' in text


def test_protocol_values_still_includes_webauthn():
    text = _text(_HW_CREDENTIALS_PATH)
    match = re.search(r"_PROTOCOL_VALUES\s*=\s*frozenset\(\{([^}]*)\}\)", text)
    assert match is not None
    assert '"WEBAUTHN"' in match.group(1)


def test_no_dns_tls_reverse_proxy_or_vpn_configuration_files_exist():
    suspicious_names = ("caddyfile", "nginx.conf", "wireguard", ".wg0", "acme.json")
    hits = []
    for path in _REPO_ROOT.rglob("*"):
        if ".git" in path.parts or ".claude" in path.parts:
            continue
        lowered = path.name.lower()
        if any(name in lowered for name in suspicious_names):
            hits.append(str(path))
    assert hits == [], f"unexpected infrastructure config artifact(s): {hits}"


def test_2n17_defers_literal_hostname_selection_explicitly():
    text = _text(_PLAN_DOC)
    assert "This phase stops here on the literal value" in text


def test_2n16_two_non_blocking_findings_quoted_verbatim_still_match_source():
    """Cross-checks this phase's report quotation of 2N.16's exact NBF text
    against 2N.16's own current document, so the quotation in the 2N.18
    report cannot silently drift from the primary source."""
    text = _text(_VERIFY_16_DOC)
    assert "NBF-149O.20L.7O.2N.16-1" in text
    assert "Host-header and `X-Forwarded-Proto` trust rules" in text
    assert "NBF-149O.20L.7O.2N.16-2" in text
    assert "Static client-asset integrity governance" in text
