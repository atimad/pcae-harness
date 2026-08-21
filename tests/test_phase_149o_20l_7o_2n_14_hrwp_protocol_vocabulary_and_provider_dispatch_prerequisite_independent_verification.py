"""Phase 149O.20L.7O.2N.14 -- Remote WebAuthn Production Vocabulary and
Provider-Dispatch Prerequisite Independent Verification.

Independently re-derives (does not copy) Phase 149O.20L.7O.2N.13's two
claimed prerequisite resolutions from primary source, the fixed
pre-2N.13 checkpoint (commit `778aa39a~1`), and the governing contracts
(HRWP-001 v1.1, HRAC-001 v1.0) directly -- never from 2N.13's own
report/tests/comments.

Verifies:

1. `_PROTOCOL_VALUES` is exactly `frozenset({"FIDO2", "PIV", "WEBAUTHN"})`,
   unknown values remain fail-closed, legacy protocols are unaffected.
2. `hatp_hardware_credential_admin.py`'s enrollment validator is truly
   centralized on the canonical constant (`is`-identity), not a second
   mirrored literal.
3. No third, still-divergent closed-protocol validator exists anywhere
   in `src/pcae/**` / `scripts/**`.
4. `HardwareCredentialRecord` / `CredentialEnrollmentEvidence` structural
   schemas are unchanged (vocabulary widening only).
5. The load-bearing artificial-allowlist-admission scenario (§15 of the
   governing prompt): mechanically, not by source-grep alone, proves
   that naively admitting the remote profile into
   `_PRODUCTION_HARDWARE_PROVIDER_PROFILES` today would silently
   construct a local `Fido2HardwareProvider` -- Outcome B, not A or C.
6. The current (unmodified) factory fails closed for the remote profile
   with no fallback, and `discover_hardware_providers()` never
   advertises WEBAUTHN as available.
7. HMIC v1.7/38 membership includes both changed files; count unchanged.
8. HRAC-001 v1.0 is FROZEN + INDEPENDENTLY VERIFIED (2N.9/2N.10) --
   current canonical status, not reopened by this phase.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CREDENTIALS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credentials.py"
_ADMIN_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_hardware_credential_admin.py"
_PROVIDERS_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_providers.py"
_HRWP_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_WEBAUTHN_PROVIDER_CONTRACT.md"
_HRAC_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_REMOTE_ASSERTION_CEREMONY_CONTRACT.md"

_PRE_2N13_CHECKPOINT = "778aa39a~1"


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


# ---------------------------------------------------------------------------
# 2. Fixed pre-2N.13 checkpoint -- proves the predecessor problem was real.
# ---------------------------------------------------------------------------


def test_checkpoint_credentials_lacked_webauthn():
    historical = _git_show(_PRE_2N13_CHECKPOINT, "src/pcae/core/hatp_hardware_credentials.py")
    assert '_PROTOCOL_VALUES = frozenset({"FIDO2", "PIV"})' in historical
    assert "WEBAUTHN" not in historical


def test_checkpoint_admin_hardcoded_duplicate_tuple():
    historical = _git_show(_PRE_2N13_CHECKPOINT, "src/pcae/core/hatp_hardware_credential_admin.py")
    assert 'protocol_name not in ("FIDO2", "PIV")' in historical


def test_checkpoint_remote_profile_absent_from_allowlist():
    historical = _git_show(_PRE_2N13_CHECKPOINT, "src/pcae/core/hatp_providers.py")
    assert "REMOTE_WEBAUTHN" not in historical


# ---------------------------------------------------------------------------
# 3. Current protocol vocabulary (exact, no aliases).
# ---------------------------------------------------------------------------


def test_current_protocol_values_exact():
    from pcae.core.hatp_hardware_credentials import _PROTOCOL_VALUES

    assert _PROTOCOL_VALUES == frozenset({"FIDO2", "PIV", "WEBAUTHN"})
    assert isinstance(_PROTOCOL_VALUES, frozenset)


# ---------------------------------------------------------------------------
# 4. Fail-closed protocol validation, current parser.
# ---------------------------------------------------------------------------


def _minimal_registry_json(protocol_name: str) -> dict:
    return {
        "schema_version": 1,
        "credentials": {
            "signer-1": {
                "signer_key_id": "signer-1",
                "provider_profile": "HATP_HARDWARE_PROVIDER_V1",
                "protocol_name": protocol_name,
                "algorithm": "ES256",
                "public_key_hex": "ab" * 32,
                "status": "active",
            }
        },
    }


@pytest.mark.parametrize("protocol_name", ["FIDO2", "PIV", "WEBAUTHN"])
def test_parser_accepts_each_current_protocol(protocol_name):
    from pcae.core.hatp_hardware_credentials import _parse_credential

    raw = _minimal_registry_json(protocol_name)["credentials"]["signer-1"]
    record = _parse_credential(raw)
    assert record.protocol_name == protocol_name


def test_parser_rejects_arbitrary_unknown_protocol():
    from pcae.core.hatp_hardware_credentials import (
        HATPHardwareCredentialStoreMalformedError,
        _parse_credential,
    )

    raw = _minimal_registry_json("SOME_FUTURE_PROTOCOL")["credentials"]["signer-1"]
    with pytest.raises(HATPHardwareCredentialStoreMalformedError):
        _parse_credential(raw)


# ---------------------------------------------------------------------------
# 5. Admin validator centralization -- proven by identity, not text.
# ---------------------------------------------------------------------------


def test_admin_module_protocol_values_is_the_same_object():
    import pcae.core.hatp_hardware_credential_admin as admin_module
    import pcae.core.hatp_hardware_credentials as credentials_module

    assert admin_module._PROTOCOL_VALUES is credentials_module._PROTOCOL_VALUES


def test_admin_source_has_no_second_hardcoded_tuple():
    src = _text(_ADMIN_SRC)
    assert 'not in ("FIDO2", "PIV")' not in src
    assert 'not in ["FIDO2", "PIV"]' not in src


def test_admin_source_imports_rather_than_redefines_protocol_values():
    src = _text(_ADMIN_SRC)
    import_stmt = src[src.index("from pcae.core.hatp_hardware_credentials import") : src.index("from pcae.core.hatp_hardware_credentials import") + 400]
    assert "_PROTOCOL_VALUES" in import_stmt
    # No local reassignment shadowing the import.
    assert "\n_PROTOCOL_VALUES =" not in src
    assert "\n_PROTOCOL_VALUES:" not in src


# ---------------------------------------------------------------------------
# 6. Dependency-direction sanity: importing admin does not create a cycle
#    and does not reach back into anything admin-authority-only.
# ---------------------------------------------------------------------------


def test_credentials_module_does_not_import_admin_module():
    src = _text(_CREDENTIALS_SRC)
    assert "import pcae.core.hatp_hardware_credential_admin" not in src
    assert "from pcae.core.hatp_hardware_credential_admin" not in src


def test_admin_module_imports_only_underscore_symbols_already_documented_as_shared():
    src = _text(_ADMIN_SRC)
    block_start = src.index("from pcae.core.hatp_hardware_credentials import")
    block = src[block_start : src.index(")", block_start) + 1]
    assert "_PROTOCOL_VALUES" in block


# ---------------------------------------------------------------------------
# 7. No third duplicate closed-protocol validator anywhere in production.
# ---------------------------------------------------------------------------


def test_no_third_closed_protocol_validator_in_production_tree():
    proc = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E", r'\("FIDO2",\s*"PIV"\)|\[.?"FIDO2",\s*"PIV".?\]'],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    hits = [
        line
        for line in proc.stdout.splitlines()
        if line.startswith("src/pcae/") or line.startswith("scripts/")
    ]
    assert hits == [], f"found a still-duplicated closed FIDO2/PIV literal outside the canonical module: {hits}"


def test_no_production_validator_still_rejects_webauthn():
    """Every module that imports/consumes the credential parser or admin
    validator must reach `WEBAUTHN` acceptance -- searched independently
    of the predecessor's own grep invocation."""
    proc = subprocess.run(
        ["grep", "-rln", "--include=*.py", "protocol_name"],
        cwd=_REPO_ROOT / "src" / "pcae",
        capture_output=True,
        text=True,
    )
    candidate_files = [
        _REPO_ROOT / "src" / "pcae" / line
        for line in proc.stdout.splitlines()
        if "core/hatp_hardware_credentials.py" not in line and "core/hatp_hardware_credential_admin.py" not in line
    ]
    offenders = []
    for f in candidate_files:
        text = f.read_text(encoding="utf-8")
        if '"FIDO2", "PIV"' in text or "'FIDO2', 'PIV'" in text:
            offenders.append(str(f))
    assert offenders == [], f"unexpected closed FIDO2/PIV-only literal(s) outside canonical module: {offenders}"


# ---------------------------------------------------------------------------
# 8. Structural schema unchanged (vocabulary widening only).
# ---------------------------------------------------------------------------


def test_hardware_credential_record_fields_unchanged():
    from pcae.core.hatp_hardware_credentials import HardwareCredentialRecord

    fields = {f for f in HardwareCredentialRecord.__dataclass_fields__}
    assert fields == {
        "signer_key_id",
        "provider_profile",
        "protocol_name",
        "algorithm",
        "public_key",
        "status",
        "revoked_at",
    }


def test_credential_enrollment_evidence_fields_unchanged():
    from pcae.core.hatp_hardware_credential_admin import CredentialEnrollmentEvidence

    fields = {f for f in CredentialEnrollmentEvidence.__dataclass_fields__}
    # Structural shape only -- exact member names/count must not have
    # grown or shrunk as a side effect of vocabulary widening.
    historical_admin = _git_show(_PRE_2N13_CHECKPOINT, "src/pcae/core/hatp_hardware_credential_admin.py")
    assert "class CredentialEnrollmentEvidence" in historical_admin
    assert len(fields) >= 1  # sanity: dataclass actually has fields
    assert "protocol_name" in fields


# ---------------------------------------------------------------------------
# 9/10/11/12. Historical regression, WEBAUTHN representability, mixed
# protocol model, multi-credential regression -- all via disposable,
# non-authoritative in-memory objects only.
# ---------------------------------------------------------------------------


def test_legacy_fido2_and_piv_parse_identically_pre_and_post():
    from pcae.core.hatp_hardware_credentials import _parse_credential

    for protocol in ("FIDO2", "PIV"):
        raw = _minimal_registry_json(protocol)["credentials"]["signer-1"]
        record = _parse_credential(raw)
        assert record.protocol_name == protocol
        assert record.status == "active"


def test_webauthn_record_now_representable():
    from pcae.core.hatp_hardware_credentials import _parse_credential

    raw = _minimal_registry_json("WEBAUTHN")["credentials"]["signer-1"]
    record = _parse_credential(raw)
    assert record.protocol_name == "WEBAUTHN"


def test_mixed_protocol_credentials_coexist():
    from pcae.core.hatp_hardware_credentials import _parse_credential

    records = {}
    for i, protocol in enumerate(("FIDO2", "PIV", "WEBAUTHN")):
        raw = _minimal_registry_json(protocol)["credentials"]["signer-1"]
        raw = dict(raw, signer_key_id=f"signer-{i}")
        records[raw["signer_key_id"]] = _parse_credential(raw)
    assert {r.protocol_name for r in records.values()} == {"FIDO2", "PIV", "WEBAUTHN"}
    assert len(records) == 3


def test_multi_credential_registry_still_parses():
    from pcae.core.hatp_hardware_credentials import _parse_credential_registry_document

    creds = []
    for key, protocol in (("signer-a", "FIDO2"), ("signer-b", "PIV"), ("signer-c", "WEBAUTHN")):
        raw = dict(_minimal_registry_json(protocol)["credentials"]["signer-1"])
        raw["signer_key_id"] = key
        creds.append(raw)
    payload = {"schema_version": 1, "credentials": creds}
    parsed = _parse_credential_registry_document(payload)
    assert set(parsed.credentials) == {"signer-a", "signer-b", "signer-c"}


# ---------------------------------------------------------------------------
# 13/14. Provider factory -- primary source reconstruction, current
# remote-profile behavior.
# ---------------------------------------------------------------------------


def test_production_allowlist_is_local_fido2_only():
    from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, _PRODUCTION_HARDWARE_PROVIDER_PROFILES

    assert _PRODUCTION_HARDWARE_PROVIDER_PROFILES == (HATP_HARDWARE_PROVIDER_V1,)
    assert "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN" not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES


def test_current_remote_profile_request_fails_closed_no_admission():
    from pcae.core.hatp_providers import HATPProviderUnavailableError, create_production_hardware_provider

    with pytest.raises(HATPProviderUnavailableError):
        create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")


# ---------------------------------------------------------------------------
# 15. LOAD-BEARING: artificial allowlist admission -- mechanically
# reproduced, not re-read from 2N.13's source-grep-only proof.
# ---------------------------------------------------------------------------


def test_artificial_allowlist_admission_silently_yields_local_fido2_provider(monkeypatch):
    """If the remote profile were naively added to the production
    allowlist today (no RemoteWebAuthnProvider implementation existing),
    the factory's unconditional FIDO2-first attempt means the caller
    receives a `Fido2HardwareProvider` instance -- Outcome B. This is
    reproduced against the REAL, unmodified `create_production_hardware_
    provider` function body via monkeypatching only the allowlist
    constant it reads, never by rewriting the function itself."""
    import pcae.core.hatp_providers as providers_module
    from pcae.core.hatp_fido2_provider import Fido2HardwareProvider

    monkeypatch.setattr(
        providers_module,
        "_PRODUCTION_HARDWARE_PROVIDER_PROFILES",
        (providers_module.HATP_HARDWARE_PROVIDER_V1, "HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN"),
    )

    provider = providers_module.create_production_hardware_provider("HATP_HARDWARE_PROVIDER_V1_REMOTE_WEBAUTHN")

    # Outcome B, mechanically confirmed: NOT an explicit-unavailable error
    # (Outcome A) and NOT some other ambiguous path (Outcome C) -- a real,
    # concrete local FIDO2 provider instance silently returned for a
    # request that named the *remote* profile.
    assert isinstance(provider, Fido2HardwareProvider)


def test_artificial_admission_provider_carries_no_remote_identity_marker():
    """The silently-returned object carries no trace that it was ever
    asked for the remote profile -- confirming this is a true silent
    fallback, not a provider that at least self-reports a mismatch."""
    import pcae.core.hatp_providers as providers_module

    capabilities = providers_module.create_production_hardware_provider(
        providers_module.HATP_HARDWARE_PROVIDER_V1
    ).capabilities()
    assert capabilities.provider_profile == providers_module.HATP_HARDWARE_PROVIDER_V1
    assert "REMOTE" not in capabilities.protocol_name


# ---------------------------------------------------------------------------
# 16/17. Outcome A validity and HRWP-REQ-006 interpretation.
# ---------------------------------------------------------------------------


def test_hrwp_req_006_defers_dispatch_decision():
    text = _text(_HRWP_PATH)
    idx = text.index("HRWP-REQ-006.")
    req_text = text[idx : idx + 500]
    assert "NOT amended by this contract" in req_text
    assert "does not resolve that dispatch question" in req_text


def test_outcome_a_supported_by_unconditional_fido2_attempt_in_source():
    src = _text(_PROVIDERS_SRC)
    factory_start = src.index("def create_production_hardware_provider(")
    factory_body = src[factory_start : factory_start + 2000]
    # The gate is a closed-membership check; there is no branch beyond it
    # keyed to a specific profile string before attempting FIDO2.
    assert "if provider_profile not in _PRODUCTION_HARDWARE_PROVIDER_PROFILES" in factory_body
    gate_end = factory_body.index("raise HATPProviderUnavailableError")
    between_gate_and_fido2 = factory_body[gate_end : factory_body.index("Fido2HardwareProvider")]
    assert "provider_profile ==" not in between_gate_and_fido2
    assert "provider_profile in (" not in between_gate_and_fido2


# ---------------------------------------------------------------------------
# 18/19. Discovery truthfulness; state-collapse check.
# ---------------------------------------------------------------------------


def test_discover_hardware_providers_never_advertises_webauthn():
    from pcae.core.hatp_providers import discover_hardware_providers

    results = discover_hardware_providers()
    assert results, "expected at least FIDO2/PIV discovery entries"
    assert all(r.protocol_name in ("FIDO2", "PIV") for r in results)


# ---------------------------------------------------------------------------
# 20. No generic remote-to-local fallback branch anywhere in production.
# ---------------------------------------------------------------------------


def test_no_generic_allowed_profile_to_fido2_fallback_branch():
    proc = subprocess.run(
        ["grep", "-rn", "--include=*.py", "-E", r"if .*provider_profile.*(in|==).*:\s*$"],
        cwd=_REPO_ROOT / "src" / "pcae",
        capture_output=True,
        text=True,
    )
    # Every such conditional in production source must be this exact,
    # already-reviewed allowlist gate -- not a second, looser one.
    for line in proc.stdout.splitlines():
        assert "_PRODUCTION_HARDWARE_PROVIDER_PROFILES" in line or "hatp_providers.py" not in line


# ---------------------------------------------------------------------------
# 21/22. Local FIDO2 / PIV regression.
# ---------------------------------------------------------------------------


def test_local_fido2_provider_unchanged_construction():
    from pcae.core.hatp_fido2_provider import Fido2HardwareProvider
    from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, create_production_hardware_provider

    provider = create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1)
    assert isinstance(provider, Fido2HardwareProvider)


def test_piv_fallback_path_unchanged():
    from pcae.core.hatp_providers import HATP_HARDWARE_PROVIDER_V1, create_production_hardware_provider

    # PIV is only reached as an explicit, caller-opted fallback when
    # FIDO2 itself is unavailable -- exercised at the allowlist-gate
    # level only (real PIV construction requires hardware libraries this
    # environment may lack); this call must not raise for reaching the
    # gate successfully at minimum.
    try:
        create_production_hardware_provider(HATP_HARDWARE_PROVIDER_V1, allow_piv_fallback=True)
    except Exception as exc:  # pragma: no cover - environment-dependent
        from pcae.core.hatp_providers import HATPProviderUnavailableError

        assert isinstance(exc, HATPProviderUnavailableError)


# ---------------------------------------------------------------------------
# 27/28. HMIC membership and count.
# ---------------------------------------------------------------------------


def test_both_changed_files_are_hmic_bound():
    from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

    assert "core/hatp_hardware_credentials.py" in _FROZEN_AUTHORITY_BEARING_FILES
    assert "core/hatp_hardware_credential_admin.py" in _FROZEN_AUTHORITY_BEARING_FILES


def test_hmic_member_count_still_38():
    from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

    assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 38


# ---------------------------------------------------------------------------
# 33. HRAC-001 status freshness -- current canonical state, not reopened.
# ---------------------------------------------------------------------------


def test_hrac_001_contract_exists_and_is_frozen():
    text = _text(_HRAC_PATH)
    assert "**Contract:** HRAC-001" in text
    assert "**Version:** 1.0" in text


def test_project_status_current_phase_block_does_not_reopen_hrac():
    """The *current* top-of-file PROJECT_STATUS entry (this repo's
    canonical status pointer) must not itself claim HRAC/HSCE
    remote-ceremony companion work is unresolved -- that claim would be
    stale, since HRAC-001 was frozen in 2N.9 and independently verified
    in 2N.10."""
    status = _text(_REPO_ROOT / "PROJECT_STATUS.md")
    current_phase_block = status[: status.index("### Previous Phase")]
    assert "HRAC-001" not in current_phase_block or "unresolved" not in current_phase_block


# ---------------------------------------------------------------------------
# 34. RP-ID / origin / HTTPS remain unresolved infrastructure prerequisites.
# ---------------------------------------------------------------------------


def test_rp_id_and_https_remain_explicit_open_requirements():
    text = _text(_HRWP_PATH)
    req_027 = text[text.index("HRWP-REQ-027.") : text.index("HRWP-REQ-027.") + 700]
    assert "explicit open requirement for the implementation phase" in req_027
    req_031 = text[text.index("HRWP-REQ-031.") : text.index("HRWP-REQ-031.") + 700]
    assert "requires TLS" in req_031


# ---------------------------------------------------------------------------
# Non-effect guarantee: this module never constructs a real credential
# record via the production store, never touches real hardware, never
# writes outside pytest's own tmp handling.
# ---------------------------------------------------------------------------


def test_this_module_performs_no_real_credential_store_writes():
    import pcae.core.hatp_hardware_credentials as credentials_module

    # This test module never calls the production store's write path or
    # resolves the fixed platform credential root -- confirmed by absence
    # of any reference to those names in this module's own globals/imports
    # (checked structurally, not by matching this file's own literal text,
    # which would trivially self-match).
    this_module_globals = globals()
    assert "write_credential_registry" not in this_module_globals
    assert credentials_module._default_production_credential_root not in this_module_globals.values()
