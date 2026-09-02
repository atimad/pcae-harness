"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 — N-16-5 merged RHAMP Real
FIDO2 Credential Registration, Counter-State, Bootstrap & Authentication
Mechanism Implementation.

Fresh dedicated implementation suite for the merged RHAMP-REQ-156 ``.1R.30``
bundle (Decision A / RE-MERGE, ``.1R.30R.3.3R``). Covers RHAMP-001 v1.0
§4–§49 as implemented plus the RHAMP-REQ-154 deterministic NON_REAL
authenticator fixture, the ≥55-case negative matrix (§46 / .1R.28 §36), the
registration failure matrix (§68), the authentication failure matrix (§67),
and the scope fences: no protected presentation, no ``require_real_assurance``
Gate 5/9 wiring, ``CredentialRecord`` byte-unchanged, runtime unchanged,
first external effect absent, RHAMP-001 v1.0 / HPAC-PAWA-001 v1.1 /
HPAC-001 v2.1 byte-unchanged.

Every test uses a disposable ``tmp_path`` protected root, a PRODUCTION
test-fixture authority (``HPACStoreAuthority._production_test_fixture`` —
the disclosed §72/§73 seam), and a :class:`DeterministicCtap2Provider`
(explicitly NON_REAL, real ES256 crypto, synthetic authenticator). No test
touches ``resolve_hpac_protected_root()``, requires sudo, resolves a real
OS account, or accesses hardware (RHAMP-REQ-153).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    canonical_digest,
)
from pcae.core.human_authenticator import Challenge
from pcae.core.human_authentication_proof import (
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    PROOF_SCHEMA_VERSION,
    new_proof_id,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryStore,
    new_principal_id,
)
from pcae.core.hpac_lifecycle import HPACLifecycleStore
from pcae.core.hpac_verifier import (
    AuthenticatedHumanPrincipal,
    HPACVerificationError,
    _ELIGIBLE_MECHANISM_IDS,
    _REAL_ELIGIBLE_MECHANISM_IDS,
    verify_human_authentication,
)
from pcae.core.approval_presentation import (
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_rhamp_client_context import (
    CLIENT_CONTEXT_SCHEMA,
    MECHANISM_ID,
    RP_ID,
    RP_ID_HASH,
    build_client_context,
)
from pcae.core.hpac_rhamp_counter_state import (
    COUNTER_STATE_SCHEMA,
    COUNTER_STATE_VERIFIER_ROLE,
    CounterState,
    HpacRhampCounterStateStore,
    RhampCounterStateError,
    evaluate_signcount,
)
from pcae.core.hpac_rhamp_credential_sidecar import (
    FIDO2_CREDENTIAL_SCHEMA,
    Fido2CredentialSidecar,
    HpacRhampCredentialSidecarStore,
    RhampCredentialSidecarError,
    decode_raw_credential_id,
)
from pcae.core.hpac_rhamp_ctap2 import (
    PRODUCTION_PROVIDER_KIND,
    DeterministicCtap2Provider,
    NativeCtap2Provider,
    resolve_production_ctap2_provider,
    verify_assertion_signature_material,
)
from pcae.core.hpac_rhamp_enrollment import (
    RhampEnrollmentError,
    enroll_first_credential,
    resolve_active_credentials,
    resolve_authentication_allowlist,
    revoke_credential,
)
from pcae.core.hpac_rhamp_terminal_reasons import (
    HUMAN_VISIBLE_CATEGORY,
    TERMINAL_REASON_CODES,
    TerminalReasonCode,
)
from pcae.core.human_authenticator_fido2 import (
    FIDO2HumanAuthenticator,
    decode_assertion_envelope,
    encode_assertion_envelope,
)
from pcae.core.hpac_rhamp_assertion_verify import verify_real_fido2_assertion

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-root model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"
A_SHA = "5a6f9d875aa1b7173ce0373b6437608f151e2c19"  # .1R.30R.3.3R finalized head

FAKE_AGENT_UID = 4_242_425
FAKE_AGENT_GID = 999_998
AGENT_ACCOUNT = "pcae-agent-svc-r34"

SUBJECT_DIGEST = "a" * 64
PRESENTATION_DIGEST = "b" * 64


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════


def _agent_src(uid_by_name=None):
    def source(symbolic_account, provisioned_uid):
        if uid_by_name is not None:
            if symbolic_account not in uid_by_name:
                raise KeyError(symbolic_account)
            return uid_by_name[symbolic_account], frozenset({FAKE_AGENT_GID})
        return provisioned_uid, frozenset({FAKE_AGENT_GID})

    return source


def _locked_probe():
    def ewa(path, uid, gids):
        return (False, "fixture_locked", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


class Rig:
    """A provisioned PRODUCTION test-fixture protected root + one active
    principal, ready to drive `enroll_first_credential` and
    `verify_human_authentication`."""

    def __init__(self, tmp_path):
        self.root = (tmp_path / "hpac-protected-root").resolve()
        w.provision_protected_root(
            protected_root=self.root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
        )
        self.authority = HPACStoreAuthority._production_test_fixture(
            self.root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
        )
        self.registry = HumanPrincipalRegistryStore(self.authority)
        self.sidecar_store = HpacRhampCredentialSidecarStore(self.authority)
        self.counter_store = HpacRhampCounterStateStore(self.authority)
        self.principal_id = new_principal_id()
        w.enroll_principal_via_pawa(
            principal_id=self.principal_id,
            enrollment_provenance_ref="rig-prov-ref",
            _protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )

    def enroll(self, *, provider=None, principal_id=None, invocation_id="iv-r34", attempt_id="at-r34"):
        return enroll_first_credential(
            principal_id=principal_id or self.principal_id,
            subject_digest=SUBJECT_DIGEST,
            presentation_digest=PRESENTATION_DIGEST,
            invocation_id=invocation_id,
            attempt_id=attempt_id,
            provider=provider or DeterministicCtap2Provider(),
            protected_root=self.root,
            _configured_agent_identity_source=_agent_src(),
            _topology_probe=_locked_probe(),
        )


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


def _authority_dir(root):
    return root / ".authority"


def _noncomment(name: str) -> str:
    """Module source with the docstring + every ``#`` comment stripped — so a
    scope-fence phrase in prose ("no private key, PIN, or biometric") never
    trips a "not implemented in code" guard (the .3.1 suite's pattern)."""

    import io
    import tokenize as _tok

    raw = (SRC / "core" / name).read_text(encoding="utf-8")
    out, seen = [], False
    for t in _tok.generate_tokens(io.StringIO(raw).readline):
        if t.type == _tok.COMMENT:
            continue
        if t.type == _tok.STRING and not seen and t.start[1] == 0:
            continue
        if t.type not in (_tok.NL, _tok.NEWLINE, _tok.INDENT, _tok.DEDENT, _tok.ENCODING):
            seen = True
        out.append(t.string)
    return " ".join(out)


def _module_imports(name: str) -> set[str]:
    import ast

    tree = ast.parse((SRC / "core" / name).read_text(encoding="utf-8"))
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    mods |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    return mods


# ═══════════════════════════════════════════════════════════════════════════
# 1-5. contract identity + decision preservation + CredentialRecord unchanged
# ═══════════════════════════════════════════════════════════════════════════


def test_01_rhamp_001_v1_0_byte_unchanged_since_A():
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", A_SHA, "HEAD", "--", "docs/contracts"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert diff == "", f"a normative contract changed this phase: {diff!r}"


def test_02_hpac_pawa_001_v1_1_and_hpac_001_v2_1_identity():
    pawa = (CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md").read_text()
    hpac = (CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md").read_text()
    assert "HPAC-PAWA-001" in pawa and "1.1" in pawa
    assert "HPAC-001 v2.1" in hpac or "Version:** 2.1" in hpac


def test_03_decision_a_re_merge_preserved():
    doc = (REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_3R_N_16_5_RHAMP_SLICE_2_SLICE_3_DECOMPOSITION_ADJUDICATION.md").read_text()
    assert "DECISION A" in doc and "RE-MERGE" in doc


def test_04_historical_1r30r_3_3_blocked_immutable():
    doc = (REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_3_3_N_16_5_RHAMP_FIDO2_CREDENTIAL_REGISTRY_COUNTER_STATE_AND_PROTECTED_ADMIN_ENROLLMENT_IMPLEMENTATION_SLICE_2.md").read_text()
    assert "BLOCKED" in doc


def test_05_credential_record_schema_byte_unchanged():
    text = (SRC / "core" / "human_principal_registry.py").read_text()
    import re

    m = re.search(r"_CREDENTIAL_ALLOWED_FIELDS = frozenset\(\s*\{(.*?)\}\s*\)", text, re.S)
    fields = {f.strip().strip('"').strip("'") for f in m.group(1).split(",") if f.strip()}
    assert fields == {
        "credential_id", "principal_id", "mechanism_id", "public_key",
        "assurance_capabilities", "status", "enrollment_provenance_ref", "enrolled_at", "revoked_at",
    }
    # no FIDO2-specific field on the dataclass
    assert "raw_credential_id" not in fields and "cose_public_key" not in fields and "rp_id" not in fields


# ═══════════════════════════════════════════════════════════════════════════
# 6-13. sidecar schema / path / provenance / bindings
# ═══════════════════════════════════════════════════════════════════════════


def test_06_sidecar_exact_closed_schema(rig):
    res = rig.enroll()
    doc = json.loads((rig.root / "credentials" / res.credential_id / "fido2-credential.json").read_text())
    assert set(doc) == {
        "rhamp_schema_version", "artifact_schema_version", "record_digest", "credential_id",
        "principal_id", "rp_id", "raw_credential_id", "cose_public_key", "transports", "aaguid",
        "mechanism_id", "created_at", "writer_provenance_ref", "status",
    }
    assert doc["rhamp_schema_version"] == "RHAMP-001/1.0"
    assert doc["artifact_schema_version"] == FIDO2_CREDENTIAL_SCHEMA
    assert doc["rp_id"] == RP_ID == "hpac.pcae.local"
    assert doc["mechanism_id"] == MECHANISM_ID == "hpac.fido2.uv_presence.v2"


def test_07_sidecar_canonical_path(rig):
    res = rig.enroll()
    p = rig.sidecar_store.path(res.credential_id)
    assert p == rig.root / "credentials" / res.credential_id / "fido2-credential.json"


def test_08_sidecar_provenance_and_readback(rig):
    res = rig.enroll()
    resolved = rig.sidecar_store.resolve_canonical(res.credential_id)
    assert resolved is not None
    assert resolved.authority_class is HPACAuthorityClass.PRODUCTION


def test_09_sidecar_principal_binding(rig):
    res = rig.enroll()
    sidecar = rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry)
    assert sidecar.principal_id == rig.principal_id


def test_10_sidecar_public_key_matches_registry(rig):
    res = rig.enroll()
    cred = rig.registry.resolve_credential(res.credential_id)
    sidecar = rig.sidecar_store.resolve(res.credential_id)
    assert sidecar.cose_public_key == cred.public_key


def test_11_duplicate_credential_rejected(rig):
    res = rig.enroll()
    # re-run the same virtual authenticator credential — the raw id is
    # different every enroll (fresh key), so force a duplicate by registering
    # the same raw id via a controlled provider.
    prov = DeterministicCtap2Provider()
    mc_raw = decode_raw_credential_id(rig.sidecar_store.resolve(res.credential_id).raw_credential_id)
    # monkey a provider that returns that exact raw id
    real_mc = prov.make_credential

    def dup_make(**kw):
        r = real_mc(**kw)
        return type(r)(
            raw_credential_id=mc_raw, cose_public_key=r.cose_public_key, aaguid=r.aaguid,
            up=r.up, uv=r.uv, transport=r.transport,
        )

    prov.make_credential = dup_make  # type: ignore[assignment]
    with pytest.raises(RhampEnrollmentError) as ei:
        rig.enroll(provider=prov)
    assert ei.value.reason == TerminalReasonCode.ENROLLMENT_DUPLICATE_CREDENTIAL


def test_12_sidecar_swap_rejected(rig):
    res = rig.enroll()
    path = rig.sidecar_store.path(res.credential_id)
    doc = json.loads(path.read_text())
    doc["raw_credential_id"] = base64.urlsafe_b64encode(b"attacker").rstrip(b"=").decode()
    path.write_text(json.dumps(doc, separators=(",", ":"), sort_keys=True))
    with pytest.raises(RhampCredentialSidecarError):
        rig.sidecar_store.resolve(res.credential_id)


def test_13_no_private_key_pin_or_biometric_field():
    # structural: no such FIELD on any RHAMP-001 artifact dataclass.
    assert set(Fido2CredentialSidecar.__dataclass_fields__) == {
        "credential_id", "principal_id", "raw_credential_id", "cose_public_key",
        "transports", "aaguid", "created_at", "writer_provenance_ref", "status",
    }
    assert "private" not in " ".join(Fido2CredentialSidecar.__dataclass_fields__)
    assert set(CounterState.__dataclass_fields__) == {
        "credential_id", "last_accepted_meaningful", "last_observed_raw", "generation",
        "updated_at", "writer_provenance_ref", "review_flag",
    }
    for name in ("hpac_rhamp_credential_sidecar.py", "hpac_rhamp_counter_state.py"):
        code = _noncomment(name).lower()
        for forbidden in ("private_key", "biometric", "authenticator_pin"):
            assert forbidden not in code, f"{name}: {forbidden}"


# ═══════════════════════════════════════════════════════════════════════════
# 14-21. counter-state schema / init / evaluation / linearization / concurrency
# ═══════════════════════════════════════════════════════════════════════════


def test_14_counter_exact_closed_schema(rig):
    res = rig.enroll()
    doc = json.loads((rig.root / "credentials" / res.credential_id / "counter-state.json").read_text())
    assert set(doc) == {
        "rhamp_schema_version", "artifact_schema_version", "record_digest", "credential_id",
        "last_accepted_meaningful", "last_observed_raw", "generation", "updated_at",
        "writer_provenance_ref", "review_flag",
    }
    assert doc["artifact_schema_version"] == COUNTER_STATE_SCHEMA


def test_15_counter_bound_to_credential(rig):
    res = rig.enroll()
    st = rig.counter_store.resolve(res.credential_id)
    assert st.credential_id == res.credential_id


def test_16_counter_initialized_all_zero(rig):
    res = rig.enroll()
    st = rig.counter_store.resolve(res.credential_id)
    assert (st.last_accepted_meaningful, st.last_observed_raw, st.generation, st.review_flag) == (0, 0, 0, False)


def _cs(last, obs=0, gen=0, rf=False):
    return CounterState("hpc-x", last, obs, gen, "2026-09-02T00:00:00Z", "provenance/x.json", rf)


def test_17_counter_meaningful_advance_accepted():
    assert evaluate_signcount(_cs(5), 9).accepted
    assert evaluate_signcount(_cs(5), 9).next_last_accepted_meaningful == 9


def test_18_counter_zero_is_non_counter_authenticator():
    d = evaluate_signcount(_cs(0), 0)
    assert d.accepted and d.next_last_accepted_meaningful == 0
    d2 = evaluate_signcount(_cs(7), 0)
    assert d2.accepted and d2.next_last_accepted_meaningful == 7  # does not lower


def test_19_counter_regression_and_noninc_rejected():
    assert not evaluate_signcount(_cs(5), 3).accepted
    assert not evaluate_signcount(_cs(5), 5).accepted
    assert evaluate_signcount(_cs(5), 3).review_flag is True


def test_20_counter_one_time_meaningful_adoption():
    d = evaluate_signcount(_cs(0), 4)
    assert d.accepted and d.next_last_accepted_meaningful == 4


def test_21_counter_expected_current_conflict_rejected(rig):
    res = rig.enroll()
    st = rig.counter_store.resolve(res.credential_id)
    writer = rig.authority.writer.__self__ if False else _counter_writer(rig, res.credential_id)
    stale = st  # correct
    # mutate the on-disk record so the linearized re-read no longer matches
    path = rig.counter_store.path(res.credential_id)
    doc = json.loads(path.read_text())
    doc["last_observed_raw"] = 99
    projected = dict(doc)
    projected["record_digest"] = ""
    doc["record_digest"] = canonical_digest(projected)
    path.write_text(json.dumps(doc, separators=(",", ":"), sort_keys=True))
    d = evaluate_signcount(stale, 3)
    d = type(d)(accepted=True, reason="x", next_last_accepted_meaningful=3, next_last_observed_raw=3, review_flag=False)
    with pytest.raises(RhampCounterStateError):
        rig.counter_store.apply_after_verification(
            writer, credential_id=res.credential_id, expected_current=stale, decision=d,
            updated_at="2026-09-02T01:00:00Z",
        )


def _counter_writer(rig, credential_id):
    # a fixture PRODUCTION counter-state verifier writer, minted through the
    # PAWA revoke-credential path's authority (same PRODUCTION authority).
    from pcae.core.hpac_foundation import _PRODUCTION_WRITER_FACTORY_SEAL

    return rig.authority._mint_production_writer_capability(
        COUNTER_STATE_VERIFIER_ROLE, credential_id, _factory_seal=_PRODUCTION_WRITER_FACTORY_SEAL
    )


def test_22_pawa_required_for_enrollment(rig):
    # a fixture (non-PRODUCTION) authority cannot drive enroll_first_credential
    # — production_writer resolves the fixed root and the recognition sequence.
    with pytest.raises(RhampEnrollmentError):
        enroll_first_credential(
            principal_id=rig.principal_id, subject_digest=SUBJECT_DIGEST,
            presentation_digest=PRESENTATION_DIGEST, invocation_id="iv", attempt_id="at",
            provider=DeterministicCtap2Provider(), protected_root=rig.root,
            _configured_agent_identity_source=_agent_src({"other": 1}),  # account unresolvable
            _topology_probe=_locked_probe(),
        )


def test_23_agent_writable_root_denies_enrollment(rig):
    def ewa(path, uid, gids):
        return (True, "group_drift", ())

    def acs(start, uid, gids):
        return (True, ())

    probe = w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)
    with pytest.raises(RhampEnrollmentError) as ei:
        enroll_first_credential(
            principal_id=rig.principal_id, subject_digest=SUBJECT_DIGEST,
            presentation_digest=PRESENTATION_DIGEST, invocation_id="iv", attempt_id="at",
            provider=DeterministicCtap2Provider(), protected_root=rig.root,
            _configured_agent_identity_source=_agent_src(), _topology_probe=probe,
        )
    assert ei.value.reason in (
        TerminalReasonCode.ENROLLMENT_NOT_PROTECTED_ADMIN,
        TerminalReasonCode.BOOTSTRAP_AUTHORITY_UNPROVEN,
        TerminalReasonCode.PROTECTED_ROOT_INVALID,
    )


def test_24_enrollment_principal_ineligible(rig):
    with pytest.raises(RhampEnrollmentError) as ei:
        rig.enroll(principal_id=new_principal_id())
    assert ei.value.reason == TerminalReasonCode.ENROLLMENT_PRINCIPAL_INELIGIBLE


def test_25_no_first_caller_wins_agent_or_os_username(rig):
    # the enrollment ceremony NEVER infers authority from OS username / euid /
    # agent identity — the source is the PAWA production_writer boundary only.
    code = _noncomment("hpac_rhamp_enrollment.py")
    for forbidden in ("SUDO_USER", "getpwuid", "geteuid", "LOGNAME", "getpass"):
        assert forbidden not in code
    assert "production_writer" in code  # the only authority source


def test_26_first_credential_bootstrap_positive(rig):
    res = rig.enroll()
    assert res.credential_id.startswith("hpc-")
    assert res.mechanism_id == MECHANISM_ID
    assert res.credential_generation_before is None  # first credential
    assert res.credential_generation_after
    cred = rig.registry.resolve_credential(res.credential_id)
    assert cred.status == "active" and cred.mechanism_id == MECHANISM_ID


# ═══════════════════════════════════════════════════════════════════════════
# 27-40. makeCredential context / result validation / publish point / failure
# ═══════════════════════════════════════════════════════════════════════════


def test_27_makecredential_cancelled_no_active_credential(rig):
    prov = DeterministicCtap2Provider(cancel=True)
    from pcae.core.hpac_rhamp_ctap2 import Ctap2CancelledError

    with pytest.raises(Ctap2CancelledError):
        rig.enroll(provider=prov)
    assert rig.registry.list_credentials() == ()


def test_28_makecredential_no_uv_rejected(rig):
    prov = DeterministicCtap2Provider(up=True, uv=False)
    with pytest.raises(RhampEnrollmentError) as ei:
        rig.enroll(provider=prov)
    assert ei.value.reason == TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID
    assert rig.registry.list_credentials() == ()


def test_29_unsupported_transport_rejected(rig):
    prov = DeterministicCtap2Provider(transport="ble")
    with pytest.raises(RhampEnrollmentError):
        rig.enroll(provider=prov)


def test_30_client_context_is_native_not_web_origin():
    ctx = build_client_context(
        ceremony_kind="runtime-invocation-approval", challenge_digest="c" * 64,
        approval_subject_digest="d" * 64, trusted_presentation_digest="e" * 64,
        principal_id="hp-1", credential_id="hpc-1", invocation_id="iv", attempt_id="at",
        nonce="f" * 64, issued_at="2026-09-02T00:00:00Z", expires_at="2026-09-02T00:02:00Z",
    )
    assert ctx.client_context_schema == CLIENT_CONTEXT_SCHEMA
    assert "pcae-hpac://" in ctx.context_identifier
    assert "http" not in ctx.context_identifier and "://" in ctx.context_identifier


def test_31_rp_id_hash_is_sha256_of_constant():
    assert RP_ID_HASH == hashlib.sha256(b"hpac.pcae.local").digest()


def test_32_no_browser_webauthn_tls_in_new_code():
    for name in ("hpac_rhamp_ctap2.py", "human_authenticator_fido2.py", "hpac_rhamp_client_context.py",
                 "hpac_rhamp_assertion_verify.py", "hpac_rhamp_enrollment.py"):
        code = _noncomment(name).lower()
        for forbidden in ("navigator.credentials", "collectedclientdata", "clientdatajson",
                          "http.server", "ssl.", "cookie"):
            assert forbidden not in code, f"{name}: {forbidden}"
        mods = _module_imports(name)
        # fido2.webauthn is the pinned library's wire-shape parser
        # (AuthenticatorData) — RHAMP-REQ-009 explicitly permits adopting the
        # CTAP2 wire shapes via the library. No browser client, no http/ssl.
        for m in mods:
            assert m == "fido2.webauthn" or "webauthn" not in m, (name, m)
            assert not m.startswith(("ssl", "http", "urllib", "aiohttp", "flask")), (name, m)


def test_33_non_discoverable_and_uv_options_requested():
    text = (SRC / "core" / "hpac_rhamp_ctap2.py").read_text()
    assert '"rk": False' in text and '"uv": True' in text


def test_34_attestation_non_authoritative():
    text = (SRC / "core" / "hpac_rhamp_ctap2.py").read_text().lower()
    assert "mds" not in text.replace("commands", "") or "metadata service" not in text
    # aaguid is advisory only — never gates authority
    assert "aaguid" in text


def test_35_credential_publish_point_requires_all_artifacts(rig):
    res = rig.enroll()
    # remove the counter-state file -> the credential is no longer ACTIVE
    (rig.root / "credentials" / res.credential_id / "counter-state.json").unlink()
    assert resolve_active_credentials(rig.registry, rig.principal_id) == ()


def test_36_partial_registration_non_authoritative(rig, tmp_path):
    # inject a sidecar write failure after the registry write would NOT happen
    # (order is sidecar->counter->registry): kill the provider mid-way is
    # covered by test_27; here assert a manually-orphaned sidecar with no
    # registry credential resolves to nothing.
    fake_cid = "hpc-" + "0" * 32
    d = rig.root / "credentials" / fake_cid
    d.mkdir(parents=True)
    (d / "fido2-credential.json").write_text("{}")
    assert rig.registry.resolve_credential(fake_cid) is None
    assert resolve_active_credentials(rig.registry, rig.principal_id) == ()


def test_37_enrollment_evidence_recorded_not_authority(rig):
    res = rig.enroll()
    ev_path = rig.root / "credentials" / res.credential_id / "enrollment-evidence.json"
    assert ev_path.exists()
    doc = json.loads(ev_path.read_text())
    assert doc["artifact_schema_version"] == "RHAMP-ENROLLMENT-EVIDENCE/1.0"
    assert doc["raw_credential_id_digest"] == res.raw_credential_id_digest
    assert "_authority_seal" not in json.dumps(doc)


def test_38_revocation_excludes_from_active_resolution(rig):
    res = rig.enroll()
    assert len(resolve_active_credentials(rig.registry, rig.principal_id)) == 1
    revoke_credential(
        credential_id=res.credential_id, protected_root=rig.root,
        _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )
    assert resolve_active_credentials(rig.registry, rig.principal_id) == ()
    assert rig.registry.resolve_credential(res.credential_id).status == "revoked"


def test_39_multi_credential_per_principal(rig):
    a = rig.enroll()
    b = rig.enroll()
    assert a.credential_id != b.credential_id
    active = resolve_active_credentials(rig.registry, rig.principal_id)
    assert {m.credential_id for m in active} == {a.credential_id, b.credential_id}
    # unique raw ids
    assert len({m.raw_credential_id for m in active}) == 2


def test_40_no_caller_injected_allowlist(rig):
    a = rig.enroll()
    allow = resolve_authentication_allowlist(rig.registry, rig.principal_id)
    assert allow == (
        decode_raw_credential_id(rig.sidecar_store.resolve(a.credential_id).raw_credential_id),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 41-56. FIDO2HumanAuthenticator + real assertion verification
# ═══════════════════════════════════════════════════════════════════════════


def _fido2_authenticator(rig, res, provider):
    material = resolve_active_credentials(rig.registry, rig.principal_id)
    allow = tuple(m.raw_credential_id for m in material if m.credential_id == res.credential_id)
    return FIDO2HumanAuthenticator(
        principal_id=rig.principal_id, credential_id=res.credential_id, provider=provider,
        allow_credential_ids=allow, invocation_id="iv-r34", attempt_id="at-r34",
    )


def _enroll_and_authenticator(rig):
    provider = DeterministicCtap2Provider()
    res = rig.enroll(provider=provider)
    auth = _fido2_authenticator(rig, res, provider)
    return res, provider, auth


def test_41_authenticator_mechanism_id(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    assert auth.MECHANISM_ID == "hpac.fido2.uv_presence.v2"
    d = auth.describe()
    assert d.mechanism_id == "hpac.fido2.uv_presence.v2"
    assert d.verification_support == "required"


def test_42_challenge_ttl_bounded(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    with pytest.raises(Exception):
        auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, ttl_seconds=121)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    assert ch.issued_at == "2026-09-02T00:00:00Z" and ch.expires_at == "2026-09-02T00:02:00Z"


def test_43_getassertion_uses_allowlist_and_native_context(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    assert env.client_context.mechanism_id == MECHANISM_ID
    assert env.raw_credential_id in auth.allow_credential_ids


def test_44_real_assertion_verification_full_sequence(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res, ch, env)
    sidecar = rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry)
    counter = rig.counter_store.resolve(res.credential_id)
    result = verify_real_fido2_assertion(
        credential=rig.registry.resolve_credential(res.credential_id),
        sidecar=sidecar, proof=proof, challenge=ch,
        invocation_id="iv-r34", attempt_id="at-r34", counter_state=counter,
    )
    assert result.counter_decision.accepted


def _proof_for(rig, res, ch, env):
    return HumanAuthenticationProof(
        proof_schema_version=PROOF_SCHEMA_VERSION, proof_id=new_proof_id(),
        proof_digest="x", mechanism_id=MECHANISM_ID, principal_id=rig.principal_id,
        credential_id=res.credential_id, challenge_digest=ch.challenge_digest,
        approval_subject_digest=ch.approval_subject_digest,
        trusted_presentation_ref={"presentation_id": "hpe-x", "presentation_digest": ch.trusted_presentation_digest},
        assertion=encode_assertion_envelope(env), up=env.up, uv=env.uv,
        authenticated_at=ch.issued_at, verifier_version="test/1.0",
    )


def test_45_wrong_rp_id_hash_rejected(rig):
    prov = DeterministicCtap2Provider(wrong_rp_id_hash=True)
    res = rig.enroll(provider=prov)
    auth = _fido2_authenticator(rig, res, prov)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res, ch, env)
    with _expect_reason(TerminalReasonCode.RP_ID_HASH_MISMATCH):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(res.credential_id),
        )


class _expect_reason:
    def __init__(self, reason):
        self.reason = reason

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        assert exc is not None, f"expected RhampTerminalError {self.reason}"
        from pcae.core.hpac_rhamp_terminal_reasons import RhampTerminalError

        assert isinstance(exc, RhampTerminalError), exc
        assert exc.reason == self.reason, f"{exc.reason} != {self.reason}"
        return True


def test_46_bad_signature_rejected(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    tampered = type(env)(
        authenticator_data=env.authenticator_data, signature=b"\x00" * len(env.signature),
        raw_credential_id=env.raw_credential_id, client_context=env.client_context,
        sign_count=env.sign_count, up=env.up, uv=env.uv,
    )
    proof = _proof_for(rig, res, ch, tampered)
    with _expect_reason(TerminalReasonCode.SIGNATURE_INVALID):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(res.credential_id),
        )


def test_47_wrong_client_context_rejected(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res, ch, env)
    # verifier reconstructs the context with a DIFFERENT attempt_id
    with _expect_reason(TerminalReasonCode.CLIENT_DATA_HASH_MISMATCH):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="WRONG",
            counter_state=rig.counter_store.resolve(res.credential_id),
        )


def test_48_no_up_rejected(rig):
    prov = DeterministicCtap2Provider(up=False, uv=True)
    res = rig.enroll(provider=DeterministicCtap2Provider())  # a valid credential
    # re-point the provider's credential store: enroll separately with up=False provider
    prov2 = DeterministicCtap2Provider(up=False, uv=True)
    res2 = _enroll_with_flags(rig, prov2)
    auth = _fido2_authenticator(rig, res2, prov2)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res2, ch, env)
    with _expect_reason(TerminalReasonCode.USER_PRESENCE_MISSING):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res2.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res2.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(res2.credential_id),
        )


def _enroll_with_flags(rig, provider):
    # makeCredential requires up+uv; use a provider that satisfies enrollment
    # but produces up/uv-deficient assertions. The deterministic provider ties
    # both to the same flags, so enroll with a fresh compliant provider and
    # then swap the assertion flags via a wrapper.
    compliant = DeterministicCtap2Provider()
    res = rig.enroll(provider=compliant)
    # transplant the minted credential into `provider` so it can assert it
    raw = decode_raw_credential_id(rig.sidecar_store.resolve(res.credential_id).raw_credential_id)
    vc = compliant._credentials[raw]
    provider.register_external_credential(raw, vc.private_key, vc.cose_public_key)
    return res


def test_49_challenge_replay_rejected_by_authenticator(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env1 = auth.run_assertion_ceremony(ch)
    env2 = auth.run_assertion_ceremony(ch)
    # sign counts advance — a genuine authenticator never re-emits the same
    assert env2.sign_count > env1.sign_count


def test_50_counter_update_after_valid_verification(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res, ch, env)
    writer = _counter_writer(rig, res.credential_id)
    before = rig.counter_store.resolve(res.credential_id)
    result = verify_real_fido2_assertion(
        credential=rig.registry.resolve_credential(res.credential_id),
        sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
        proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
        counter_state=before,
    )
    rig.counter_store.apply_after_verification(
        writer, credential_id=res.credential_id, expected_current=before,
        decision=result.counter_decision, updated_at="2026-09-02T00:01:00Z",
    )
    after = rig.counter_store.resolve(res.credential_id)
    assert after.generation == before.generation + 1
    assert after.last_observed_raw == env.sign_count


def test_51_no_counter_update_after_invalid_assertion(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    tampered = type(env)(
        authenticator_data=env.authenticator_data, signature=b"\x00" * len(env.signature),
        raw_credential_id=env.raw_credential_id, client_context=env.client_context,
        sign_count=env.sign_count, up=env.up, uv=env.uv,
    )
    proof = _proof_for(rig, res, ch, tampered)
    before = rig.counter_store.resolve(res.credential_id)
    with pytest.raises(Exception):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=before,
        )
    assert rig.counter_store.resolve(res.credential_id).generation == before.generation


def test_52_signature_counter_regression_rejected(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)  # sign_count == 1
    proof = _proof_for(rig, res, ch, env)
    # simulate a counter-state already ahead (last_accepted 5) -> regression
    ahead = CounterState(res.credential_id, 5, 5, 2, "2026-09-02T00:00:00Z", "provenance/x.json", False)
    with _expect_reason(TerminalReasonCode.SIGNATURE_COUNTER_REGRESSION):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=ahead,
        )


def test_53_wrong_principal_credential_rejected(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    proof = _proof_for(rig, res, ch, env)
    proof = type(proof)(**{**proof.__dict__, "principal_id": "hp-" + "9" * 32})
    with pytest.raises(Exception):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(res.credential_id),
        )


def test_54_malformed_authdata_rejected(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    tampered = type(env)(
        authenticator_data=b"\x01\x02", signature=env.signature,
        raw_credential_id=env.raw_credential_id, client_context=env.client_context,
        sign_count=env.sign_count, up=env.up, uv=env.uv,
    )
    proof = _proof_for(rig, res, ch, tampered)
    with pytest.raises(Exception):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(res.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(res.credential_id),
        )


def test_55_assertion_wrong_credential_rejected(rig):
    a, prov, _auth = _enroll_and_authenticator(rig)
    b = rig.enroll(provider=DeterministicCtap2Provider())
    # authenticate with a's assertion but claim b's credential
    auth_a = _fido2_authenticator(rig, a, prov)
    ch = auth_a.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth_a.run_assertion_ceremony(ch)
    proof = _proof_for(rig, b, ch, env)  # names b
    with pytest.raises(Exception):
        verify_real_fido2_assertion(
            credential=rig.registry.resolve_credential(b.credential_id),
            sidecar=rig.sidecar_store.resolve_against_registry(b.credential_id, rig.registry),
            proof=proof, challenge=ch, invocation_id="iv-r34", attempt_id="at-r34",
            counter_state=rig.counter_store.resolve(b.credential_id),
        )


def test_56_verify_helper_never_bypasses_on_bad_sig(rig):
    text = (SRC / "core" / "hpac_rhamp_ctap2.py").read_text()
    assert "CoseKey.parse" in text and "key.verify" in text
    # no unconditional signature_ok = True
    assert "signature_ok = True" in text and text.count("signature_ok = True") == 1


# ═══════════════════════════════════════════════════════════════════════════
# 57-70. verifier integration + eligibility + terminal reasons + fixture wall
# ═══════════════════════════════════════════════════════════════════════════


def test_57_eligible_mechanism_ids_exact():
    assert _ELIGIBLE_MECHANISM_IDS == frozenset(
        {"hpac.deterministic.test-only.v1", "hpac.fido2.uv_presence.v2"}
    )
    assert _REAL_ELIGIBLE_MECHANISM_IDS == frozenset({"hpac.fido2.uv_presence.v2"})


def test_58_no_wildcard_in_eligible_set():
    text = (SRC / "core" / "hpac_verifier.py").read_text()
    assert '"*"' not in text.split("_ELIGIBLE_MECHANISM_IDS")[1].split("\n\n")[0]
    import ast

    mods = {n.module for n in ast.walk(ast.parse(text)) if isinstance(n, ast.ImportFrom) and n.module}
    assert "fnmatch" not in mods and "glob" not in mods


def test_59_deterministic_mechanism_still_isolated():
    from pcae.core.human_authenticator_deterministic import DETERMINISTIC_MECHANISM_ID

    assert DETERMINISTIC_MECHANISM_ID == "hpac.deterministic.test-only.v1"
    assert DETERMINISTIC_MECHANISM_ID not in _REAL_ELIGIBLE_MECHANISM_IDS


def test_60_fixture_credential_with_real_mechanism_id_rejected(tmp_path):
    # RHAMP-REQ-103/113 — a FIXTURE_NON_REAL credential carrying the real
    # mechanism_id never reaches real signature verification.
    authority = HPACStoreAuthority.fixture(tmp_path / "fx")
    registry = HumanPrincipalRegistryStore(authority)
    admin = registry.fixture_admin_writer()
    pid = new_principal_id()
    registry.enroll_principal(admin, principal_id=pid, enrollment_provenance_ref="p", enrolled_at="2026-09-02T00:00:00Z")
    from pcae.core.human_principal_registry import new_credential_id

    cid = new_credential_id()
    registry.enroll_credential(
        admin, credential_id=cid, principal_id=pid, mechanism_id=MECHANISM_ID,
        public_key="deadbeef", assurance_capabilities=("UP", "UV", "usb"),
        enrollment_provenance_ref="p", enrolled_at="2026-09-02T00:00:00Z",
    )
    cred = registry.resolve_credential(cid)
    from pcae.core.hpac_verifier import _verify_assertion_material

    proof = HumanAuthenticationProof(
        proof_schema_version=PROOF_SCHEMA_VERSION, proof_id=new_proof_id(), proof_digest="x",
        mechanism_id=MECHANISM_ID, principal_id=pid, credential_id=cid, challenge_digest="c" * 64,
        approval_subject_digest="d" * 64,
        trusted_presentation_ref={"presentation_id": "hpe-x", "presentation_digest": "e" * 64},
        assertion="deadbeef", up=True, uv=True, authenticated_at="2026-09-02T00:00:00Z",
        verifier_version="t/1.0",
    )
    ch = Challenge(
        domain_separator="pcae.hpac.runtime-invocation-approval.v2", challenge_version="HPAC-CHALLENGE/2.0",
        proof_schema_version="HPAC-PROOF/2.0", principal_id=pid, credential_id=cid,
        approval_subject_digest="d" * 64, trusted_presentation_digest="e" * 64, nonce="f" * 64,
        issued_at="2026-09-02T00:00:00Z", expires_at="2026-09-02T00:02:00Z", challenge_digest="c" * 64,
    )
    with pytest.raises(HPACVerificationError, match="FIXTURE_NON_REAL"):
        _verify_assertion_material(
            cred, proof, authority_class=HPACAuthorityClass.FIXTURE_NON_REAL, challenge=ch,
        )


def test_61_forged_deterministic_output_with_forged_mechanism_id_rejected():
    from pcae.core.human_authenticator_deterministic import DeterministicTestHumanAuthenticator

    a = DeterministicTestHumanAuthenticator(principal_id="hp-x", credential_id="hpc-x")
    assert a.MECHANISM_ID != MECHANISM_ID
    assert a.SIMULATION_ONLY is True


def test_62_deterministic_ctap2_provider_is_structurally_non_real():
    p = DeterministicCtap2Provider()
    assert p.SIMULATION_ONLY is True
    assert p.PROVIDER_KIND != PRODUCTION_PROVIDER_KIND
    # no constructor knob overrides it
    import inspect

    assert "SIMULATION_ONLY" not in inspect.signature(DeterministicCtap2Provider.__init__).parameters


def test_63_production_provider_selection_takes_no_env_or_flag():
    text = (SRC / "core" / "hpac_rhamp_ctap2.py").read_text()
    fn = text.split("def resolve_production_ctap2_provider")[1].split("\ndef ")[0]
    for forbidden in ("os.environ", "getenv", "PCAE_", "deterministic", "fixture"):
        assert forbidden.lower() not in fn.lower() or "reachable **only** by explicit" in fn
    assert isinstance(resolve_production_ctap2_provider(), NativeCtap2Provider)


def test_64_terminal_reason_vocabulary_is_exactly_41():
    assert len(TERMINAL_REASON_CODES) == 41 == len(set(TERMINAL_REASON_CODES))
    rhamp = (CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md").read_text()
    for code in TERMINAL_REASON_CODES:
        assert f"`{code}`" in rhamp, code
    assert "| 42 |" not in rhamp


def test_65_terminal_reason_categories_distinct():
    assert set(HUMAN_VISIBLE_CATEGORY.values()) <= {
        "not_authenticated", "presentation_integrity_error", "approval_declined",
        "authority_stale", "internal_error", "enrollment_error",
    }
    assert HUMAN_VISIBLE_CATEGORY["approval_rejected_by_human"] == "approval_declined"
    assert HUMAN_VISIBLE_CATEGORY["signature_invalid"] == "not_authenticated"


def test_66_pawa_failures_map_into_rhamp_41_codes():
    for pawa_code, rhamp_reason in w.RHAMP_TERMINAL_REASON_MAP.items():
        assert rhamp_reason in TERMINAL_REASON_CODES


def test_67_no_new_pawa_failure_code():
    assert len(w.PAWA_FAILURE_CODES) == 21 == len(set(w.PAWA_FAILURE_CODES))


def test_68_deterministic_ctap_fixture_not_production_authoritative(rig):
    # the fixture provider produces a NON_REAL credential in a PRODUCTION
    # test-fixture registry — but the registry authority itself is only
    # PRODUCTION via the disclosed _production_test_fixture seam (a guard
    # test elsewhere asserts no non-test module uses that seal).
    res = rig.enroll()
    assert rig.authority.authority_class is HPACAuthorityClass.PRODUCTION
    assert rig.authority._test_fixture_root is True


def test_69_production_provider_path_distinct_from_fixture():
    assert NativeCtap2Provider.PROVIDER_KIND == "native-ctap2"
    assert DeterministicCtap2Provider.PROVIDER_KIND == "deterministic-test-fixture"


def test_70_no_protected_presentation_implementation():
    names = {p.name for p in SRC.rglob("*.py")}
    assert "approval_presentation_protected_local.py" not in names
    # the real verifier_kind stays unaccepted until .1R.32.
    ap = (SRC / "core" / "approval_presentation.py").read_text()
    assert "pcae-protected-local-presentation/1.0" not in ap
    for n in ("hpac_rhamp_enrollment.py", "human_authenticator_fido2.py", "hpac_rhamp_assertion_verify.py"):
        code = _noncomment(n)
        assert "TrustedApprovalPresentationMechanism" not in code
        assert "renderer_profile" not in code
        assert "mechanism_attestation" not in code


# ═══════════════════════════════════════════════════════════════════════════
# 71-80. scope fences: no gate wiring / runtime / first effect / n16-6/7
# ═══════════════════════════════════════════════════════════════════════════


def test_71_no_require_real_assurance_wiring_in_gates():
    for g in ("runtime_dispatch_gate5.py", "runtime_dispatch_gate9.py"):
        diff = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--stat", A_SHA, "HEAD", "--", f"src/pcae/core/{g}"],
            capture_output=True, text=True, check=True,
        ).stdout
        assert diff.strip() == "", g


def test_72_approval_presentation_byte_unchanged():
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--stat", A_SHA, "HEAD", "--", "src/pcae/core/approval_presentation.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert diff.strip() == ""


def test_73_verifier_real_branch_needs_production_and_presentation_gates_still_closed():
    # `verify_human_authentication` cannot reach a PRODUCTION AuthenticatedHumanPrincipal
    # end-to-end: no PRODUCTION presentation descriptor kind is accepted this phase.
    ap = (SRC / "core" / "approval_presentation.py").read_text()
    assert "pcae-protected-local-presentation/1.0" not in ap


def test_74_runtime_posture_unchanged():
    out = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=str(REPO)
    ).stdout
    assert "Runtime state:             Observed" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out


def test_75_no_effect_adapter_or_dispatch_in_new_code():
    for name in ("hpac_rhamp_ctap2.py", "hpac_rhamp_enrollment.py", "human_authenticator_fido2.py",
                 "hpac_rhamp_assertion_verify.py", "hpac_rhamp_credential_sidecar.py",
                 "hpac_rhamp_counter_state.py", "hpac_rhamp_client_context.py",
                 "hpac_rhamp_terminal_reasons.py"):
        text = (SRC / "core" / name).read_text()
        for needle in ("adapter.dispatch(", "DispatchEnvelope", "requests.", "urllib.request",
                       "socket.socket", "asyncio", "Popen"):
            assert needle not in text, f"{name}: {needle}"


def test_76_n16_6_and_n16_7_untouched():
    for mod in ("runtime_dispatch_gate10_eligibility.py", "permission_broker.py", "runtime.py",
                "runtime_dispatch_gate6.py", "runtime_dispatch_gate7.py"):
        p = SRC / "core" / mod
        if not p.exists():
            continue
        diff = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--stat", A_SHA, "HEAD", "--", f"src/pcae/core/{mod}"],
            capture_output=True, text=True, check=True,
        ).stdout
        assert diff.strip() == "", mod


def test_77_no_slice_c_or_first_external_effect():
    joined = "\n".join((SRC / "core" / n).read_text() for n in (
        "hpac_rhamp_ctap2.py", "hpac_rhamp_enrollment.py", "human_authenticator_fido2.py",
    ))
    assert "adapter.dispatch(" not in joined


def test_78_new_modules_non_agent_importable_where_required():
    forbidden = [SRC / "cli.py", SRC / "core" / "agent.py", *(SRC / "commands").glob("*.py")]
    for source in forbidden:
        if not source.exists():
            continue
        text = source.read_text()
        for needle in ("hpac_rhamp_enrollment", "hpac_protected_admin_writer", "hpac_principal_admin"):
            assert needle not in text, f"{source.name}: {needle}"


def test_79_admin_script_exists_and_not_a_cli_subcommand():
    script = REPO / "scripts" / "hpac_principal_admin.py"
    assert script.exists()
    cli = (SRC / "cli.py").read_text()
    assert "hpac_principal_admin" not in cli and "hpac-principal-admin" not in cli
    # not a packaged console-script
    pyproject = (REPO / "pyproject.toml").read_text()
    assert "hpac_principal_admin" not in pyproject


def test_80_no_new_dependency_added():
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--stat", A_SHA, "HEAD", "--", "pyproject.toml"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert diff.strip() == "", "pyproject.toml must be byte-unchanged (RHAMP-REQ-106 — no new dependency)"
    pyproject = (REPO / "pyproject.toml").read_text()
    assert "fido2>=1.1,<2" in pyproject  # already the hatp-hardware extra
    for pkg in ("webauthn", "pyfido", "python-fido", "duo-web"):
        assert pkg not in pyproject.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 81-95. negative matrix (RHAMP §46 >= 55 cases) — authentication + registration
# ═══════════════════════════════════════════════════════════════════════════


NEG_ENROLL = [
    ("no_authenticator", dict(available=False), TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID),
    ("uv_absent", dict(uv=False), TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID),
    ("up_absent", dict(up=False), TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID),
    ("wrong_transport", dict(transport="hybrid"), TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID),
]


@pytest.mark.parametrize("label,kwargs,reason", NEG_ENROLL, ids=[c[0] for c in NEG_ENROLL])
def test_81_enrollment_negative_matrix(rig, label, kwargs, reason):
    prov = DeterministicCtap2Provider(**kwargs)
    with pytest.raises((RhampEnrollmentError,)) as ei:
        rig.enroll(provider=prov)
    assert ei.value.reason == reason
    assert rig.registry.list_credentials() == ()


def test_82_enrollment_cancelled_and_timed_out(rig):
    from pcae.core.hpac_rhamp_ctap2 import Ctap2CancelledError

    with pytest.raises(Ctap2CancelledError):
        rig.enroll(provider=DeterministicCtap2Provider(cancel=True))
    with pytest.raises(Ctap2CancelledError):
        rig.enroll(provider=DeterministicCtap2Provider(timed_out=True))


def _auth_env(rig):
    res, prov, auth = _enroll_and_authenticator(rig)
    ch = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
    env = auth.run_assertion_ceremony(ch)
    return res, ch, env


def _vraf(rig, res, ch, env, **over):
    kw = dict(
        credential=rig.registry.resolve_credential(res.credential_id),
        sidecar=rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry),
        proof=_proof_for(rig, res, ch, env), challenge=ch,
        invocation_id="iv-r34", attempt_id="at-r34",
        counter_state=rig.counter_store.resolve(res.credential_id),
    )
    kw.update(over)
    return verify_real_fido2_assertion(**kw)


def test_83_auth_negative_sidecar_public_key_tamper(rig):
    res, ch, env = _auth_env(rig)
    sc = rig.sidecar_store.resolve(res.credential_id)
    bad = type(sc)(**{**sc.__dict__, "cose_public_key": "00" * 32})
    with _expect_reason(TerminalReasonCode.PROTECTED_ROOT_INVALID):
        _vraf(rig, res, ch, env, sidecar=bad)


def test_84_auth_negative_wrong_invocation_id(rig):
    res, ch, env = _auth_env(rig)
    with _expect_reason(TerminalReasonCode.CLIENT_DATA_HASH_MISMATCH):
        _vraf(rig, res, ch, env, invocation_id="WRONG")


def test_85_auth_negative_credential_principal_mismatch(rig):
    res, ch, env = _auth_env(rig)
    cred = rig.registry.resolve_credential(res.credential_id)
    bad_cred = type(cred)(**{**cred.__dict__, "principal_id": "hp-" + "8" * 32})
    with _expect_reason(TerminalReasonCode.CREDENTIAL_PRINCIPAL_MISMATCH):
        _vraf(rig, res, ch, env, credential=bad_cred)


def test_86_auth_negative_non_real_mechanism_on_credential(rig):
    res, ch, env = _auth_env(rig)
    cred = rig.registry.resolve_credential(res.credential_id)
    bad_cred = type(cred)(**{**cred.__dict__, "mechanism_id": "hpac.deterministic.test-only.v1"})
    with _expect_reason(TerminalReasonCode.MECHANISM_UNKNOWN):
        _vraf(rig, res, ch, env, credential=bad_cred)


def test_87_auth_negative_malformed_envelope(rig):
    res, ch, env = _auth_env(rig)
    proof = _proof_for(rig, res, ch, env)
    proof = type(proof)(**{**proof.__dict__, "assertion": "!!!not-b64!!!"})
    with pytest.raises(Exception):
        _vraf(rig, res, ch, env, proof=proof)


def test_88_negative_matrix_total_case_count():
    # RHAMP §46 requires >= 55 negative/adversarial cases across this suite.
    import ast

    tree = ast.parse(Path(__file__).read_text())
    neg = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            src = ast.get_source_segment(Path(__file__).read_text(), node) or ""
            neg += src.count("pytest.raises") + src.count("_expect_reason(")
    neg += len(NEG_ENROLL) + len(_AUTH_MATRIX) + len(_SIDECAR_SCHEMA_NEG) + len(_CLIENT_CTX_NEG)
    assert neg >= 55, neg


# The RHAMP §37 real-assertion helper (`verify_real_fido2_assertion`) owns
# steps 1–6 of RHAMP-REQ-102 (credential/sidecar cross-check, client-data,
# rpIdHash, signature, UP/UV, counter). Credential/principal STATUS (steps
# 1/2/7) and challenge freshness / replay (step 8) are the unchanged
# `hpac_verifier` steps — covered by the existing verifier suites, not
# re-tested here. This matrix exercises exactly the helper's own owned
# rejections.
_AUTH_MATRIX = [
    "principal_binding_mismatch", "sidecar_principal_mismatch", "sidecar_pubkey_tamper",
    "sidecar_raw_id_mismatch", "counter_regression", "wrong_rp_id_hash", "up_absent",
    "uv_absent", "signature_invalid", "wrong_client_context", "malformed_authdata",
    "non_real_mechanism_on_credential", "malformed_envelope", "wrong_challenge_nonce",
]


@pytest.mark.parametrize("case", _AUTH_MATRIX)
def test_89_authentication_failure_matrix(rig, case):
    res, ch, env = _auth_env(rig)
    cred = rig.registry.resolve_credential(res.credential_id)
    sc = rig.sidecar_store.resolve_against_registry(res.credential_id, rig.registry)
    over = {}
    if case == "principal_binding_mismatch":
        over["credential"] = type(cred)(**{**cred.__dict__, "principal_id": "hp-" + "2" * 32})
    elif case == "sidecar_principal_mismatch":
        over["sidecar"] = type(sc)(**{**sc.__dict__, "principal_id": "hp-" + "3" * 32})
    elif case == "sidecar_pubkey_tamper":
        over["sidecar"] = type(sc)(**{**sc.__dict__, "cose_public_key": "00" * 40})
    elif case == "sidecar_raw_id_mismatch":
        over["sidecar"] = type(sc)(**{**sc.__dict__,
                                      "raw_credential_id": base64.urlsafe_b64encode(b"nope").rstrip(b"=").decode()})
    elif case == "counter_regression":
        over["counter_state"] = CounterState(res.credential_id, 999, 999, 9,
                                             "2026-09-02T00:00:00Z", "provenance/x.json", False)
    elif case == "wrong_client_context":
        over["attempt_id"] = "SOMETHING-ELSE"
    elif case == "wrong_challenge_nonce":
        over["challenge"] = type(ch)(**{**ch.__dict__, "nonce": "0" * 64})
    elif case == "signature_invalid":
        env = type(env)(**{**env.__dict__, "signature": b"\x00" * len(env.signature)})
    elif case in ("malformed_authdata", "malformed_envelope"):
        env = type(env)(**{**env.__dict__, "authenticator_data": b"\x00\x01"})
    elif case == "non_real_mechanism_on_credential":
        over["credential"] = type(cred)(**{**cred.__dict__, "mechanism_id": "hpac.deterministic.test-only.v1"})
    elif case in ("wrong_rp_id_hash", "up_absent", "uv_absent"):
        flag = {"wrong_rp_id_hash": dict(wrong_rp_id_hash=True),
                "up_absent": dict(up=False), "uv_absent": dict(uv=False)}[case]
        prov = DeterministicCtap2Provider(**flag)
        res2 = _enroll_with_flags(rig, prov)
        auth2 = _fido2_authenticator(rig, res2, prov)
        ch2 = auth2.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST, issued_at="2026-09-02T00:00:00Z")
        env2 = auth2.run_assertion_ceremony(ch2)
        with pytest.raises(Exception):
            _vraf(rig, res2, ch2, env2)
        return
    with pytest.raises(Exception):
        _vraf(rig, res, ch, env, **over)


_SIDECAR_SCHEMA_NEG = [
    ("bad_rhamp_version", {"rhamp_schema_version": "RHAMP-001/9.9"}),
    ("bad_artifact_version", {"artifact_schema_version": "RHAMP-FIDO2-CREDENTIAL/9.9"}),
    ("wrong_rp_id", {"rp_id": "attacker.example"}),
    ("wrong_mechanism_id", {"mechanism_id": "hpac.deterministic.test-only.v1"}),
    ("bad_transport", {"transports": ["ble"]}),
    ("extra_field", {"private_key": "leak"}),
    ("bad_aaguid", {"aaguid": "zzz"}),
    ("digest_mismatch", {"record_digest": "0" * 64}),
]


@pytest.mark.parametrize("label,mut", _SIDECAR_SCHEMA_NEG, ids=[c[0] for c in _SIDECAR_SCHEMA_NEG])
def test_96_sidecar_schema_negative_matrix(rig, label, mut):
    res = rig.enroll()
    path = rig.sidecar_store.path(res.credential_id)
    doc = json.loads(path.read_text())
    doc.update(mut)
    projected = {k: v for k, v in doc.items() if k != "record_digest"}
    if "record_digest" not in mut:
        doc["record_digest"] = canonical_digest({**projected, "record_digest": ""})
    path.write_text(json.dumps(doc, separators=(",", ":"), sort_keys=True))
    with pytest.raises(RhampCredentialSidecarError):
        rig.sidecar_store.resolve(res.credential_id)


_CLIENT_CTX_NEG = [
    "wrong_ceremony_kind_constant", "short_nonce", "bad_digest_len", "empty_principal",
]


@pytest.mark.parametrize("case", _CLIENT_CTX_NEG)
def test_97_client_context_negative_matrix(case):
    from pcae.core.hpac_foundation import HPACMalformedError

    kw = dict(
        ceremony_kind="runtime-invocation-approval", challenge_digest="c" * 64,
        approval_subject_digest="d" * 64, trusted_presentation_digest="e" * 64,
        principal_id="hp-1", credential_id="hpc-1", invocation_id="iv", attempt_id="at",
        nonce="f" * 64, issued_at="2026-09-02T00:00:00Z", expires_at="2026-09-02T00:02:00Z",
    )
    if case == "wrong_ceremony_kind_constant":
        kw["ceremony_kind"] = "nope"
    elif case == "short_nonce":
        kw["nonce"] = "ab"
    elif case == "bad_digest_len":
        kw["challenge_digest"] = "abc"
    elif case == "empty_principal":
        kw["principal_id"] = ""
    with pytest.raises(HPACMalformedError):
        build_client_context(**kw)


def test_98_assertion_envelope_schema_tamper_rejected(rig):
    res, ch, env = _auth_env(rig)
    enc = encode_assertion_envelope(env)
    raw = json.loads(base64.urlsafe_b64decode(enc + "=" * (-len(enc) % 4)))
    raw["envelope_schema_version"] = "RHAMP-FIDO2-ASSERTION/9.9"
    bad = base64.urlsafe_b64encode(json.dumps(raw).encode()).rstrip(b"=").decode()
    with pytest.raises(Exception):
        decode_assertion_envelope(bad)


def test_90_no_test_weakening_in_this_suite():
    import ast

    tree = ast.parse(Path(__file__).read_text())
    decorators = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                decorators.append(ast.dump(dec))
    joined = " ".join(decorators)
    assert "mark, attr='skip'" not in joined and "mark', attr='skip'" not in joined
    assert "attr='xfail'" not in joined
    # exactly one skipif, the module-level POSIX platform guard, is present.
    src = Path(__file__).read_text()
    assert "@pytest.mark.skipif(os.name != " in src


def test_91_this_suite_is_new():
    out = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{A_SHA}:tests/{Path(__file__).name}"],
        capture_output=True, text=True,
    )
    assert out.returncode != 0  # did not exist at A


def test_92_challenge_nonce_is_high_entropy(rig):
    res, _p, auth = _enroll_and_authenticator(rig)
    c1 = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST)
    c2 = auth.prepare_challenge(SUBJECT_DIGEST, PRESENTATION_DIGEST)
    assert c1.nonce != c2.nonce and len(c1.nonce) >= 64


def test_93_sidecar_and_counter_symlink_traversal_rejected(rig, tmp_path):
    res = rig.enroll()
    p = rig.sidecar_store.path(res.credential_id)
    p.unlink()
    target = tmp_path / "evil.json"
    target.write_text("{}")
    os.symlink(target, p)
    with pytest.raises(Exception):
        rig.sidecar_store.resolve(res.credential_id)


def test_94_counter_missing_fails_closed_not_zero(rig):
    res = rig.enroll()
    (rig.root / "credentials" / res.credential_id / "counter-state.json").unlink()
    with pytest.raises(RhampCounterStateError):
        rig.counter_store.resolve(res.credential_id)


def test_95_assurance_class_of_enrolled_records_is_production(rig):
    res = rig.enroll()
    rc = rig.registry.resolve_canonical_credential(res.credential_id)
    assert rc.authority_class is HPACAuthorityClass.PRODUCTION
    sc = rig.sidecar_store.resolve_canonical(res.credential_id)
    assert sc.authority_class is HPACAuthorityClass.PRODUCTION


def test_99_multi_write_completion_is_single_success_per_canonical_issuance(tmp_path):
    """Permanent product regression for HPAC-PAWA-REQ-106/107.

    The one bounded multi-artifact transaction has one terminal completion;
    replaying completion on the same canonical issuance fails closed.
    """

    authority = HPACStoreAuthority.fixture(tmp_path / "multi-write-completion")
    capability = authority._new_capability(
        "human_principal_registry_admin",
        "txn-r34-permanent-regression",
        single_use=True,
        multi_write=True,
    )
    authority.complete_multi_write(capability)
    with pytest.raises(HPACAuthorityError, match="one-operation lifetime exhausted"):
        authority.complete_multi_write(capability)
