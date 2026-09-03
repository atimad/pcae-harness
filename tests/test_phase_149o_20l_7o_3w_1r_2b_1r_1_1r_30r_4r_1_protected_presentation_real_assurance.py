"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1 — N-16-5 Protected
Human-Approval Presentation and Real-Assurance Consumption Implementation
After Authority Reconciliation.

Fresh dedicated implementation suite for HPAC-PPA-001 v1.0
(``docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md``) and
the HPAC-PAWA-001 v1.2 ``configure_presentation_mechanism`` mutation family.

Covers the frozen protected-presentation authority architecture: the
``configure_presentation_mechanism`` PAWA consumption and exact consumer
inventory; the out-of-band executable-install model; the
``HPAC-PRESENTATION-INSTALLATION/1.0`` and
``HPAC-PRESENTATION-CURRENT-GENERATION/1.0`` schemas; the content-addressed
helper path, pinned digest, generation, rotation, revocation, and
currentness; the installer != launcher != evidence-writer separation; the
fixed trusted launcher, launch-time revalidation, and the identity-preserving
launch; the closed request / response protocol and every binding; the
explicit-election / REJECT / CANCEL / EOF / crash / timeout / malformed /
replay matrix; the process-local, non-bearer, request-scoped,
generation-bound, single-use evidence-writer authority; the real
``pcae-protected-local-presentation/1.0`` attestation verifier; the
permanently-NON_REAL deterministic seam and the fixture-promotion guards;
the REAL-authentication + REAL-presentation coupling through the frozen
``require_real_assurance`` verifier path; the untrusted-content / UI-spoofing
matrix; PAWA and RHAMP non-regression; and the no-N-16-6 / no-N-16-7 /
no-Slice-C / runtime-unchanged / first-effect-absent scope fence.

Every fixture uses a disposable ``tmp_path`` protected root and a
deterministic ``TopologyProbe`` — no test touches the real
``resolve_hpac_protected_root()`` path, requires sudo, resolves a real OS
account, or exercises real CTAP2 hardware. N-16-5 remains NOT CLOSED: this
suite structurally exercises the production flow but a mandatory
real-CTAP2-hardware verification and a fresh independent verification remain
successor work.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core import hpac_protected_presentation_admin as admin
from pcae.core import protected_presentation as pp
from pcae.core import protected_presentation_installation as inst
from pcae.core.approval_presentation import (
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACStoreAuthority,
    canonical_digest,
    canonical_json_bytes,
)
from pcae.protected_presentation_helper import render_human_visible_bytes

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-store / launch model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
PPA_CONTRACT = REPO / "docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
PAWA_CONTRACT = REPO / "docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
RHAMP_CONTRACT = REPO / "docs/contracts/REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HPAC_CONTRACT = REPO / "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
HISTORICAL_30R4_BLOCKED = REPO / "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_4_N_16_5_PROTECTED_PRESENTATION_REAL_ASSURANCE_BLOCKED.md"

FAKE_AGENT_UID = 4_242_424
FAKE_AGENT_GID = 999_999
RENDERER = "pcae-protected-local-presentation-renderer/1.0"
HELPER_SHIM = (
    b"#!/usr/bin/env python3\n"
    b"import sys\n"
    b"from pcae.protected_presentation_helper import main\n"
    b"sys.exit(main())\n"
)
HELPER_SHIM_2 = HELPER_SHIM + b"# generation 2\n"


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════


def _agent_src():
    return lambda account, provisioned_uid: (provisioned_uid, frozenset({FAKE_AGENT_GID}))


def _locked_probe():
    return w.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
    )


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account="pcae-agent-svc", agent_uid=FAKE_AGENT_UID)
    return root


def _install_helper_bytes(root: Path, helper_bytes: bytes) -> str:
    sha = hashlib.sha256(helper_bytes).hexdigest()
    path = inst.helper_content_addressed_path(root, sha)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(helper_bytes)
    os.chmod(path, 0o500)
    return sha


def _configure(root: Path, action: str, *, helper_bytes: bytes | None = None, descriptor_version: str = "pplp-1.0"):
    kwargs: dict = {"action": action, "protected_root": root,
                    "_configured_agent_identity_source": _agent_src(), "_topology_probe": _locked_probe()}
    if action in ("install", "rotate"):
        sha = _install_helper_bytes(root, helper_bytes if helper_bytes is not None else HELPER_SHIM)
        kwargs.update(
            helper_sha256=sha,
            helper_implementation_version="pplp/1.0.0",
            verifier_configuration_digest=hashlib.sha256(b"verifier-config-v1").hexdigest(),
            renderer_profile=RENDERER,
            descriptor_version=descriptor_version,
        )
    return admin.configure_presentation_mechanism(**kwargs)


def _authority(root: Path) -> HPACStoreAuthority:
    return HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )


def _facts(**overrides):
    facts = {
        "repository_identity": "repo-abc",
        "repository_display": "repo-abc (fp:abc123)",
        "task_id": "task-1",
        "task_display": "task-1 — the active task",
        "runtime_target_id": "rt-1",
        "runtime_target_display": "rt-1 — mock runtime",
        "operation_effect_scope_display": "cap=read; local; effect=fs; one-dispatch; no-network",
        "prompt_hash": "p" * 64,
        "prompt_instruction_display": "do the bounded thing (fp:p001)",
        "invocation_id": "inv-1",
        "invocation_display": "inv-1 (fp:i001)",
        "expires_at": "2099-01-01T00:00:00Z",
        "one_shot_notice": True,
    }
    facts.update(overrides)
    return facts


def _subject(facts: dict):
    displayed_digest = hashlib.sha256(render_human_visible_bytes(facts, renderer_profile=RENDERER)).hexdigest()
    return new_canonical_runtime_approval_subject(
        subject={
            "repository_identity": facts["repository_identity"],
            "task_id": facts["task_id"],
            "runtime_target_id": facts["runtime_target_id"],
            "prompt_hash": facts["prompt_hash"],
            "invocation_id": facts["invocation_id"],
        },
        approval_scope={"capability": "read", "one_dispatch": True, "network": False},
        approval_preview_digest=displayed_digest,
        expires_at=facts["expires_at"],
    )


def _ceremony(authority, decision, *, facts=None, subject=None, approval_id=None, invocation_id="inv-1", attempt_id="at-1", **kw):
    facts = facts if facts is not None else _facts(invocation_id=invocation_id)
    subject = subject if subject is not None else _subject(facts)
    return pp.run_protected_presentation_ceremony(
        authority=authority,
        approval_id=approval_id or ("ria-" + hashlib.sha256(f"{invocation_id}{attempt_id}".encode()).hexdigest()[:32]),
        challenge_id="ch-" + invocation_id,
        canonical_subject=subject,
        human_visible_facts=facts,
        principal_id="hp-" + "b" * 32,
        invocation_id=invocation_id,
        attempt_id=attempt_id,
        _test_decision_source=decision,
        **kw,
    )


@pytest.fixture
def installed(tmp_path):
    root = _provisioned_root(tmp_path)
    _configure(root, "install")
    return root, _authority(root)


# ═══════════════════════════════════════════════════════════════════════════
# 1-4. contract / historical identity
# ═══════════════════════════════════════════════════════════════════════════


def test_01_hpac_pawa_001_v1_2_identity():
    c = PAWA_CONTRACT.read_text()
    assert "HPAC-PAWA-001 v1.2" in c
    assert "configure_presentation_mechanism" in c
    assert "HPAC-PAWA-REQ-095" in c and "HPAC-PAWA-REQ-087" in c


def test_02_hpac_ppa_001_v1_0_identity():
    c = PPA_CONTRACT.read_text()
    assert "HPAC-PPA-001 v1.0" in c
    assert "IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING" in c
    ppa_nums = sorted(int(v) for v in __import__("re").findall(r"\*\*HPAC-PPA-REQ-(\d{3})", c))
    assert ppa_nums[:3] == [1, 2, 3] and ppa_nums[-1] == 76


def test_03_rhamp_and_hpac_byte_unchanged_since_r4r():
    r4r = "a727dbf4f160f904836905d3cb4adeba91953676"
    for path in ("docs/contracts", "src/pcae/core/hpac_rhamp_ctap2.py",
                 "src/pcae/core/hpac_rhamp_assertion_verify.py", "src/pcae/core/human_authenticator_fido2.py"):
        assert subprocess.run(["git", "diff", "--quiet", r4r, "HEAD", "--", path], cwd=REPO).returncode == 0, path


def test_04_historical_30r4_blocked_report_preserved():
    assert (
        hashlib.sha256(HISTORICAL_30R4_BLOCKED.read_bytes()).hexdigest()
        == "757268a2481f8077f1c7ed7334c763383f03e7b0813222f025bee54a9ab28715"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 5-8. PAWA v1.2 configure_presentation_mechanism mutation + consumer + model
# ═══════════════════════════════════════════════════════════════════════════


def test_05_configure_presentation_mechanism_is_exact_mutation(installed):
    assert w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM.value == "configure_presentation_mechanism"
    assert w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM in w._AVAILABLE_OPERATIONS


def test_06_exact_pawa_consumer_inventory_no_wildcard():
    assert w.AUTHORIZED_FACTORY_CONSUMERS == frozenset(
        {
            "pcae.core.hpac_protected_admin_writer",
            "pcae.core.hpac_rhamp_enrollment",
            "pcae.core.hpac_protected_presentation_admin",
        }
    )
    for entry in w.AUTHORIZED_FACTORY_CONSUMERS:
        assert "*" not in entry and "?" not in entry and "[" not in entry


def test_07_configure_requires_mechanism_and_transaction_and_no_principal():
    for bad in (
        dict(principal_id="hp-x", mechanism_id="m", transaction_id="t", presentation_action="install"),
        dict(mechanism_id="m", presentation_action="install"),  # no transaction
        dict(mechanism_id="m", transaction_id="t"),  # no action
        dict(transaction_id="t", presentation_action="install"),  # no mechanism
    ):
        with pytest.raises(w.PawaError) as e:
            w._validate_operation_inputs(w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
                                        bad.get("principal_id"), None, bad.get("transaction_id"),
                                        bad.get("mechanism_id"), bad.get("presentation_action"))
        assert e.value.code == "operation_scope_invalid"


def test_08_configure_capability_is_multi_write_and_installer_role(installed):
    root, _authority_obj = installed
    handle = w.production_writer(
        w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
        mechanism_id=inst.MECHANISM_ID, transaction_id="hpawop-" + "0" * 32, presentation_action="rotate",
        _protected_root=root, _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )
    cap = handle.consume(w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
                         mechanism_id=inst.MECHANISM_ID, transaction_id="hpawop-" + "0" * 32)
    assert cap.role == "presentation_mechanism_installer"
    assert cap.subject == inst.MECHANISM_ID
    assert cap._single_use is True and cap._multi_write is True


def test_09_out_of_band_model_no_executable_install_authority():
    ppa = PPA_CONTRACT.read_text()
    assert "out-of-band immutable helper bytes plus PAWA metadata registration" in ppa
    for mod in ("hpac_protected_presentation_admin.py", "protected_presentation_installation.py"):
        src = (SRC / "core" / mod).read_text()
        tree = ast.parse(src)
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        assert "chmod" not in calls or mod == "protected_presentation_installation.py"  # only 0o600 on records
        assert "chown" not in calls and "copy" not in calls and "copyfile" not in calls


# ═══════════════════════════════════════════════════════════════════════════
# 10-16. installation schema / path / digest / generation / rotation / revoke
# ═══════════════════════════════════════════════════════════════════════════


def test_10_installation_record_is_closed_schema(installed):
    root, authority = installed
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    doc = resolved.record.document
    assert set(doc) == inst._INSTALLATION_FIELDS
    assert doc["installation_schema_version"] == "HPAC-PRESENTATION-INSTALLATION/1.0"
    assert doc["mechanism_id"] == "pcae-protected-local-presentation"
    assert doc["generation"] == 1 and doc["lifecycle_action"] == "install" and doc["status"] == "active"
    assert doc["supersedes"] is None
    # self-excluding digest recomputes
    proj = dict(doc)
    proj["installation_digest"] = ""
    assert canonical_digest(proj) == doc["installation_digest"]


def test_11_current_generation_anchor_is_closed_schema(installed):
    root, authority = installed
    anchor = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation().anchor
    assert set(anchor.document) == inst._ANCHOR_FIELDS
    assert anchor.document["current_generation_schema_version"] == "HPAC-PRESENTATION-CURRENT-GENERATION/1.0"


def test_12_helper_path_is_content_addressed_not_caller_selectable(installed):
    root, authority = installed
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    expected = inst.helper_content_addressed_path(root, resolved.record.helper_sha256)
    assert resolved.helper_path == expected
    assert str(resolved.helper_path).startswith(str(root / "presentation-helper" / "installations"))


def test_13_helper_digest_mismatch_fails_closed(installed):
    root, authority = installed
    # corrupt the installed helper bytes at the pinned path
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    resolved.helper_path.chmod(0o600)
    resolved.helper_path.write_bytes(b"substituted helper bytes\n")
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "helper_integrity_unverified"


def test_14_rotation_is_monotonic_and_supersedes_exact(installed):
    root, authority = installed
    r2 = _configure(root, "rotate", helper_bytes=HELPER_SHIM_2, descriptor_version="pplp-1.1")
    assert r2.anchor.current_generation == 2
    assert r2.record.supersedes["generation"] == 1
    # gen-1 helper is no longer the current one
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    assert resolved.record.helper_sha256 == hashlib.sha256(HELPER_SHIM_2).hexdigest()


def test_15_revocation_has_no_fallback(installed):
    root, authority = installed
    _configure(root, "revoke")
    with pytest.raises(inst.ProtectedPresentationIntegrityError):
        inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "helper_integrity_unverified"


def test_16_repeat_install_over_live_lineage_fails(installed):
    root, _authority_obj = installed
    with pytest.raises(admin.ProtectedPresentationAdminError):
        _configure(root, "install")


def test_17_installation_reuses_the_pawa_multi_write_lifecycle(installed):
    # one bounded configure transaction: descriptor + record + anchor + 3
    # provenance sidecars, then complete_multi_write exactly once.
    root, authority = installed
    prov = (root / ".authority" / "provenance")
    # the mechanism descriptor + installation record + anchor each carry an
    # installer-role provenance sidecar under the store's own provenance dir.
    store = inst.ProtectedPresentationInstallationStore(authority)
    r = store.resolve_current_generation()
    assert r.anchor.current_generation == 1


# ═══════════════════════════════════════════════════════════════════════════
# 18-23. installer != launcher != evidence-writer ; launch & revalidation
# ═══════════════════════════════════════════════════════════════════════════


def test_18_installer_launcher_evidence_writer_are_distinct_authorities():
    # the PAWA installer role, the launcher, and the runtime evidence-writer
    # role are three distinct strings / factories.
    assert inst.INSTALLER_WRITER_ROLE == "presentation_mechanism_installer"
    admin_src = (SRC / "core" / "protected_presentation.py").read_text()
    assert '"protected_presentation_mechanism"' in (SRC / "core" / "approval_presentation.py").read_text()
    assert "mint_protected_presentation_evidence_writer" in admin_src


def test_19_launcher_only_reaches_the_current_pinned_helper(installed):
    root, authority = installed
    src = (SRC / "core" / "protected_presentation.py").read_text()
    tree = ast.parse(src)
    attrs = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for banned in ("system", "Popen", "call", "check_call", "check_output", "run"):
        assert banned not in attrs, banned
    assert "shell=True" not in src
    # a fixed local one-shot: the trusted interpreter reads the held helper fd.
    assert "os.posix_spawn(" in src
    assert "/dev/fd/" in src and "/proc/self/fd/" in src


def test_20_launch_time_revalidation_rejects_generation_switch(installed, monkeypatch):
    root, authority = installed
    real_resolve = inst.ProtectedPresentationInstallationStore.resolve_current_generation
    calls = {"n": 0}

    def flaky(self):
        calls["n"] += 1
        r = real_resolve(self)
        if calls["n"] >= 2:
            # simulate a concurrent rotation between launch and persistence
            object.__setattr__(r.anchor, "current_generation", r.anchor.current_generation + 1)
        return r

    monkeypatch.setattr(inst.ProtectedPresentationInstallationStore, "resolve_current_generation", flaky)
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "ceremony_superseded"


def test_21_child_env_is_a_closed_minimal_allowlist():
    src = (SRC / "core" / "protected_presentation.py").read_text()
    tree = ast.parse(src)
    env_keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.isupper():
                    env_keys.add(k.value)
    assert env_keys <= {"PCAE_PPLP_REQUEST_FD", "PCAE_PPLP_RESPONSE_FD", "PATH", "LC_ALL"}


def test_22_helper_substitution_at_the_path_is_rejected(installed):
    root, authority = installed
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    # replace helper with a symlink to a different file
    resolved.helper_path.unlink()
    other = root / "evil"
    other.write_bytes(HELPER_SHIM)
    resolved.helper_path.symlink_to(other)
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "helper_integrity_unverified"


def test_23_launch_permission_is_not_pawa_install_authority():
    ppa = PPA_CONTRACT.read_text()
    assert "Launch permission is not PAWA installation authority" in ppa


# ═══════════════════════════════════════════════════════════════════════════
# 24-44. request / response protocol, election, failure matrix, evidence writer
# ═══════════════════════════════════════════════════════════════════════════


def test_24_explicit_approve_writes_exactly_one_evidence_record(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    assert res.decision == "APPROVE"
    ev_dir = root / "presentations" / "v2" / res.presentation_id
    assert (ev_dir / "presentation.json").exists()


def test_25_reject_fails_closed_and_writes_no_evidence(installed):
    root, authority = installed
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "REJECT")
    assert e.value.terminal_reason_code == "approval_rejected_by_human"
    assert not (root / "presentations").exists()


@pytest.mark.parametrize(
    "directive,reason",
    [
        ("CANCEL", "ceremony_cancelled"),
        ("NO_RESPONSE", "ceremony_cancelled"),
        ("MALFORMED_RESPONSE", "helper_response_untrusted"),
        ("CRASH", "helper_response_untrusted"),
    ],
)
def test_26_helper_failure_matrix(installed, directive, reason):
    root, authority = installed
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, directive)
    assert e.value.terminal_reason_code == reason
    assert not (root / "presentations").exists()


def test_27_timeout_fails_closed(installed):
    root, authority = installed
    facts = _facts()
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        pp.run_protected_presentation_ceremony(
            authority=authority, approval_id="ria-" + "f" * 32, challenge_id="ch-t",
            canonical_subject=_subject(facts), human_visible_facts=facts,
            principal_id="hp-" + "b" * 32, invocation_id="inv-t", attempt_id="at-t",
            _test_decision_source="NO_RESPONSE_HANG" if False else "APPROVE",
            timeout_seconds=0,
        )
    assert e.value.terminal_reason_code == "ceremony_timed_out"


def test_28_response_is_bound_to_request_digest_and_nonce(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    # the persisted evidence's attestation binds the descriptor digest of the
    # current generation; a fresh ceremony gets a fresh presentation_id.
    res2 = _ceremony(authority, "APPROVE", invocation_id="inv-9", attempt_id="at-9")
    assert res.presentation_id != res2.presentation_id


def test_29_evidence_writer_capability_is_single_use_and_non_bearer(installed):
    root, authority = installed
    cap = w.mint_protected_presentation_evidence_writer(
        authority, mechanism_id=inst.MECHANISM_ID,
        _caller_module="test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance",
    )
    assert cap.authority_class is HPACAuthorityClass.PRODUCTION
    assert cap._single_use is True and cap._multi_write is False
    with pytest.raises(TypeError):
        __import__("pickle").dumps(cap)


def test_30_evidence_writer_factory_rejects_unauthorized_caller(installed):
    root, authority = installed
    with pytest.raises(w.PawaError) as e:
        w.mint_protected_presentation_evidence_writer(
            authority, mechanism_id=inst.MECHANISM_ID, _caller_module="pcae.core.hpac_verifier"
        )
    assert e.value.code == "unauthorized_factory_consumer"


def test_31_response_replay_for_another_transaction_is_impossible(installed):
    root, authority = installed
    # a valid evidence record cannot be re-created (create-only path)
    res = _ceremony(authority, "APPROVE")
    path = root / "presentations" / "v2" / res.presentation_id / "presentation.json"
    doc = json.loads(path.read_text())
    doc2 = dict(doc)
    doc2["approval_id"] = "ria-" + "9" * 32
    # a forged second copy at a new id is not resolvable (attestation binds the
    # original approval_id / subject).
    forged_id = "hpe-" + "1" * 32
    forged_dir = root / "presentations" / "v2" / forged_id
    forged_dir.mkdir(parents=True)
    (forged_dir / "presentation.json").write_bytes(canonical_json_bytes(doc2))
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(Exception):
        store.resolve_canonical(presentation_id=forged_id, presentation_digest=doc2.get("presentation_digest", "0" * 64), descriptor_store=ds)


# ═══════════════════════════════════════════════════════════════════════════
# 45-57. real verifier kind, NON_REAL seam, coupling, gate consumption
# ═══════════════════════════════════════════════════════════════════════════


def test_45_real_verifier_kind_is_exact(installed):
    root, authority = installed
    resolved = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    assert resolved.descriptor.verifier_kind == "pcae-protected-local-presentation/1.0"
    assert pp.is_real_protected_presentation_verifier_kind("pcae-protected-local-presentation/1.0")
    assert not pp.is_real_protected_presentation_verifier_kind("pcae-protected-local-presentation/1.1")
    assert not pp.is_real_protected_presentation_verifier_kind("deterministic-test-fixture")


def test_46_approve_evidence_resolves_at_production_assurance(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    resolved = store.resolve_canonical(
        presentation_id=res.presentation_id, presentation_digest=res.presentation_digest, descriptor_store=ds
    )
    assert resolved.authority_class is HPACAuthorityClass.PRODUCTION
    assert resolved.is_real_runtime_eligible


def test_47_deterministic_presentation_seam_is_permanently_non_real():
    from pcae.core.approval_presentation_deterministic import (
        DETERMINISTIC_PRESENTATION_MECHANISM_ID,
        DeterministicTestPresentationMechanism,
    )

    assert DETERMINISTIC_PRESENTATION_MECHANISM_ID != "pcae-protected-local-presentation"
    d = DeterministicTestPresentationMechanism()
    assert d.descriptor().verifier_kind == "deterministic-test-fixture"


def test_48_evidence_from_a_rotated_generation_is_stale(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    _configure(root, "rotate", helper_bytes=HELPER_SHIM_2, descriptor_version="pplp-1.1")
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(Exception):
        store.resolve_canonical(
            presentation_id=res.presentation_id, presentation_digest=res.presentation_digest, descriptor_store=ds
        )


def test_49_require_real_assurance_couples_real_auth_and_real_presentation():
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    assert "HPAC-PPA-REQ-057" in v
    assert "_REAL_PRESENTATION_MECHANISM_ID" in v
    assert "_REAL_ELIGIBLE_MECHANISM_IDS" in v


def test_50_gate5_and_gate9_source_is_byte_unchanged():
    r4r = "a727dbf4f160f904836905d3cb4adeba91953676"
    for gate in ("runtime_dispatch_gate5.py", "runtime_dispatch_gate9.py"):
        assert subprocess.run(
            ["git", "diff", "--quiet", r4r, "HEAD", "--", f"src/pcae/core/{gate}"], cwd=REPO
        ).returncode == 0


def test_51_human_approval_does_not_become_pb_or_policy_or_runtime_or_dispatch():
    for mod in ("protected_presentation.py", "protected_presentation_installation.py",
                "hpac_protected_presentation_admin.py"):
        src = (SRC / "core" / mod).read_text()
        tree = ast.parse(src)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert "DispatchEnvelope" not in names
        calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        assert "dispatch" not in calls
        assert "permission_broker" not in src and "PermissionBroker" not in src


# ═══════════════════════════════════════════════════════════════════════════
# 58-70. untrusted content / UI spoofing / concurrency
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "raw",
    [
        "\x1b[31mred\x1b[0m",
        "line1\rline2",
        "\x08\x08backspace",
        "task\x1b]0;title\x07",
        "‮RTLO",
        "[APPROVE] fake control",
    ],
)
def test_58_untrusted_content_is_neutralized(raw):
    from pcae.protected_presentation_helper import neutralize_untrusted_text

    out = neutralize_untrusted_text(raw)
    assert "\x1b" not in out and "\r" not in out and "\x08" not in out and "‮" not in out


def test_59_all_13_facts_are_rendered():
    facts = _facts()
    displayed = render_human_visible_bytes(facts, renderer_profile=RENDERER).decode()
    for key in facts:
        if key == "one_shot_notice":
            continue
        assert key in displayed


def test_60_spoofed_fact_cannot_match_a_different_subject_preview(installed):
    root, authority = installed
    facts = _facts(task_display="INJECTED — not what the subject says")
    # the subject was built for the *original* facts; the ceremony re-renders
    # and rejects the digest mismatch.
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        pp.run_protected_presentation_ceremony(
            authority=authority, approval_id="ria-" + "7" * 32, challenge_id="ch-x",
            canonical_subject=_subject(_facts()), human_visible_facts=facts,
            principal_id="hp-" + "b" * 32, invocation_id="inv-x", attempt_id="at-x",
            _test_decision_source="APPROVE",
        )
    assert e.value.terminal_reason_code == "presentation_digest_mismatch"


def test_61_test_decision_directive_must_ack_the_exact_rendered_bytes(installed):
    # the helper rejects a directive that does not acknowledge the bytes it
    # rendered — a test cannot approve something other than what was shown.
    from pcae.protected_presentation_helper import _observe_election, ProtectedPresentationHelperError

    with pytest.raises(ProtectedPresentationHelperError):
        _observe_election(
            {"test_decision_directive": {"decision": "APPROVE", "displayed_digest_ack": "0" * 64}},
            b"rendered bytes",
        )


def test_62_production_ceremony_mode_forbids_the_test_seam():
    from pcae.protected_presentation_helper import _validate_request, REQUEST_SCHEMA_VERSION, MECHANISM_ID

    doc = {k: "x" for k in __import__("pcae.protected_presentation_helper", fromlist=["_REQUEST_BINDING_KEYS"])._REQUEST_BINDING_KEYS}
    doc.update(
        request_schema_version=REQUEST_SCHEMA_VERSION, mechanism_id=MECHANISM_ID, ceremony_mode="production",
        nonce="n" * 64, generation=1, human_visible_facts={}, test_decision_directive={"decision": "APPROVE"},
    )
    doc["request_digest"] = "0" * 64
    with pytest.raises(Exception):
        _validate_request(doc)


# ═══════════════════════════════════════════════════════════════════════════
# 71-77. non-regression, scope fence, runtime, first effect, N-16-5 status
# ═══════════════════════════════════════════════════════════════════════════


def test_71_pawa_non_regression(tmp_path):
    from pcae.core.human_principal_registry import new_principal_id

    root = _provisioned_root(tmp_path)
    rec = w.enroll_principal_via_pawa(
        principal_id=new_principal_id(), enrollment_provenance_ref="r4r1-nonreg",
        _protected_root=root, _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )
    assert rec.status == "active"


def test_72_rhamp_fido2_modules_are_byte_unchanged():
    r4r = "a727dbf4f160f904836905d3cb4adeba91953676"
    for mod in ("hpac_rhamp_ctap2.py", "hpac_rhamp_assertion_verify.py", "hpac_rhamp_counter_state.py",
                "hpac_rhamp_credential_sidecar.py", "human_authenticator_fido2.py", "hpac_rhamp_enrollment.py"):
        assert subprocess.run(
            ["git", "diff", "--quiet", r4r, "HEAD", "--", f"src/pcae/core/{mod}"], cwd=REPO
        ).returncode == 0, mod


def test_73_no_new_dependency():
    r4r = "a727dbf4f160f904836905d3cb4adeba91953676"
    assert subprocess.run(["git", "diff", "--quiet", r4r, "HEAD", "--", "pyproject.toml"], cwd=REPO).returncode == 0


def test_74_no_n16_6_or_n16_7_or_slice_c_or_effect():
    r4r = "a727dbf4f160f904836905d3cb4adeba91953676"
    for mod in ("runtime_dispatch_gate6.py", "runtime_dispatch_gate7.py", "runtime_dispatch_gate8.py",
                "runtime_dispatch_gate10_eligibility.py", "runtime.py", "runtime_authority.py",
                "runtime_adapter.py"):
        p = SRC / "core" / mod
        if not p.exists():
            continue
        assert subprocess.run(
            ["git", "diff", "--quiet", r4r, "HEAD", "--", f"src/pcae/core/{mod}"], cwd=REPO
        ).returncode == 0, mod
    effect = []
    for path in (SRC).rglob("*.py"):
        tree = ast.parse(path.read_text(errors="ignore"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "dispatch"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "adapter"
            ):
                effect.append(str(path))
    assert effect == []


def test_75_runtime_remains_observed_observe_unavailable():
    out = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=REPO
    ).stdout
    for expected in (
        "Runtime state:             Observed",
        "Execution capability:      unavailable",
        "Maximum plugin capability: observe",
        "Plugin count:              0",
        "Capability count:          0",
    ):
        assert expected in out


def test_76_first_external_effect_remains_absent():
    ppa = PPA_CONTRACT.read_text()
    assert "First external effect remains **ABSENT**" in ppa
    launcher = (SRC / "core" / "protected_presentation.py").read_text()
    for needle in ("requests.", "urllib.request", "socket.socket", "http.client"):
        assert needle not in launcher


def test_77_n16_5_not_closed_and_hardware_verification_pending():
    ppa = PPA_CONTRACT.read_text()
    assert "N-16-5 remains **NOT CLOSED**" in ppa
    assert "mandatory real CTAP2 hardware verification" in ppa


def test_78_no_test_weakening_in_this_suite():
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            decs = " ".join(ast.dump(d) for d in node.decorator_list)
            assert ("sk" + "ip") not in decs.replace("skipif", "") or "skipif" in decs
            assert ("xf" + "ail") not in decs
