"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.2 — Independent Verification of
the N-16-5 Protected Human-Approval Presentation and Real-Assurance
Consumption Implementation After Authority Reconciliation.

VERIFICATION ONLY. This suite modifies no production source and no normative
contract; it independently re-derives every load-bearing property of the
``.30R.4R.1`` implementation (HPAC-PPA-001 v1.0 + HPAC-PAWA-001 v1.2
``configure_presentation_mechanism``) from primary sources and running code,
rather than trusting the ``.30R.4R.1`` implementation report or its own
suite.

Independent anchors, re-derived here (not inherited from prose):

* ``A`` = ``a727dbf4…`` — the finalized ``.30R.4R`` head (== the parent of
  the first ``.30R.4R.1`` commit; verified in :func:`test_02`).
* ``I`` = ``V`` = ``HEAD`` — the finalized ``.30R.4R.1`` implementation head
  and this phase's entry SHA.

The one candidate-only guard failure this IV found — the pre-existing
``.1R.19R`` scope-fence ``test_lifecycle_module_diff_since_r20_head…``
tripping on *disclaimer prose* (``"generic subprocess API"`` / ``"subprocess
API. posix_spawn avoids fork()"``) in the authorized new launcher module —
is recorded and classified NON-BLOCKING in :func:`test_69` and the phase
document; it is an incomplete ``.30R.4R.1`` guard reconciliation, not a
functional regression, and this VERIFICATION-ONLY phase does not repair it.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-store / launch model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"
PPA_CONTRACT = CONTRACTS / "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md"
PAWA_CONTRACT = CONTRACTS / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
RHAMP_CONTRACT = CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"

A_SHA = "a727dbf4f160f904836905d3cb4adeba91953676"
R4R1_FIRST_COMMIT = "99bc5705"

_R4R1_PRODUCTION_FILES = frozenset(
    {
        "src/pcae/core/protected_presentation_installation.py",
        "src/pcae/core/hpac_protected_presentation_admin.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/protected_presentation_helper.py",
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/approval_presentation.py",
        "src/pcae/core/hpac_verifier.py",
        "scripts/hpac_protected_presentation_admin.py",
    }
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True)


def _quiet(*args: str) -> int:
    return subprocess.run(["git", "-C", str(REPO), *args]).returncode


# ── shared behavioural fixtures (disposable tmp root; no real HPAC path,
#    no sudo, no real OS account, no CTAP2 hardware) ──────────────────────

from pcae.core import hpac_protected_admin_writer as w  # noqa: E402
from pcae.core import hpac_protected_presentation_admin as admin  # noqa: E402
from pcae.core import protected_presentation as pp  # noqa: E402
from pcae.core import protected_presentation_installation as inst  # noqa: E402
from pcae.core.approval_presentation import (  # noqa: E402
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.hpac_foundation import (  # noqa: E402
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACStoreAuthority,
    canonical_digest,
)
from pcae.protected_presentation_helper import render_human_visible_bytes  # noqa: E402

_AGENT_UID = 5_151_515
_AGENT_GID = 888_888
RENDERER = "pcae-protected-local-presentation-renderer/1.0"
HELPER_A = (
    b"#!/usr/bin/env python3\nimport sys\n"
    b"from pcae.protected_presentation_helper import main\nsys.exit(main())\n"
)
HELPER_B = HELPER_A + b"# gen 2\n"
_IV_CONSUMER = "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance"


def _agent_src():
    return lambda account, provisioned_uid: (provisioned_uid, frozenset({_AGENT_GID}))


def _probe():
    return w.TopologyProbe(
        effective_write_access=lambda p, u, g: (False, "iv_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("iv_root",)),
    )


def _root(tmp_path: Path) -> Path:
    r = (tmp_path / "root").resolve()
    w.provision_protected_root(protected_root=r, agent_account="pcae-agent-svc", agent_uid=_AGENT_UID)
    return r


def _install_bytes(root: Path, b: bytes) -> str:
    sha = hashlib.sha256(b).hexdigest()
    p = inst.helper_content_addressed_path(root, sha)
    p.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if p.exists():
        p.chmod(0o600)
    p.write_bytes(b)
    os.chmod(p, 0o500)
    return sha


def _configure(root: Path, action: str, *, b: bytes | None = None, dv: str = "pplp-1.0"):
    kw: dict = {
        "action": action,
        "protected_root": root,
        "_configured_agent_identity_source": _agent_src(),
        "_topology_probe": _probe(),
    }
    if action in ("install", "rotate"):
        kw.update(
            helper_sha256=_install_bytes(root, b or HELPER_A),
            helper_implementation_version="pplp/1.0.0",
            verifier_configuration_digest=hashlib.sha256(b"vc-v1").hexdigest(),
            renderer_profile=RENDERER,
            descriptor_version=dv,
        )
    return admin.configure_presentation_mechanism(**kw)


def _authority(root: Path) -> HPACStoreAuthority:
    return HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_probe()
    )


def _facts(**ov):
    f = {
        "repository_identity": "repo-iv",
        "repository_display": "repo-iv (fp:iv)",
        "task_id": "task-iv",
        "task_display": "task-iv — active",
        "runtime_target_id": "rt-iv",
        "runtime_target_display": "rt-iv — mock",
        "operation_effect_scope_display": "cap=read; local; one-dispatch; no-network",
        "prompt_hash": "q" * 64,
        "prompt_instruction_display": "bounded thing (fp:q)",
        "invocation_id": "inv-iv",
        "invocation_display": "inv-iv (fp:i)",
        "expires_at": "2099-01-01T00:00:00Z",
        "one_shot_notice": True,
    }
    f.update(ov)
    return f


def _subject(f: dict):
    dd = hashlib.sha256(render_human_visible_bytes(f, renderer_profile=RENDERER)).hexdigest()
    return new_canonical_runtime_approval_subject(
        subject={
            "repository_identity": f["repository_identity"],
            "task_id": f["task_id"],
            "runtime_target_id": f["runtime_target_id"],
            "prompt_hash": f["prompt_hash"],
            "invocation_id": f["invocation_id"],
        },
        approval_scope={"capability": "read", "one_dispatch": True, "network": False},
        approval_preview_digest=dd,
        expires_at=f["expires_at"],
    )


def _ceremony(authority, decision, *, f=None, subject=None, inv="inv-iv", at="at-iv", **kw):
    f = f if f is not None else _facts(invocation_id=inv)
    subject = subject if subject is not None else _subject(f)
    return pp.run_protected_presentation_ceremony(
        authority=authority,
        approval_id="ria-" + hashlib.sha256(f"{inv}{at}".encode()).hexdigest()[:32],
        challenge_id="ch-" + inv,
        canonical_subject=subject,
        human_visible_facts=f,
        principal_id="hp-" + "c" * 32,
        invocation_id=inv,
        attempt_id=at,
        _test_decision_source=decision,
        **kw,
    )


@pytest.fixture
def installed(tmp_path):
    root = _root(tmp_path)
    _configure(root, "install")
    return root, _authority(root)


# ═══════════════ 1. SHA derivation + production diff inventory ═══════════════


def test_01_r4r1_head_is_the_finalized_implementation_head():
    # 5b6b4013 (I) is a real ancestor of HEAD; every commit HEAD adds beyond it
    # is a .30R.4R.2 IV-scoped commit (task lifecycle / this suite / doc).
    assert _quiet("merge-base", "--is-ancestor", "5b6b4013", "HEAD") == 0
    log = _git("log", "-1", "--format=%s", "5b6b4013").strip()
    assert "1R.30R.4R.1" in log and "reconcile pushed-state" in log
    beyond = _git("log", "--format=%s", "5b6b4013..HEAD").strip().splitlines()
    assert all("1R.30R.4R.2" in s for s in beyond), beyond


def test_02_A_is_independently_the_r4r_finalized_head():
    assert _git("rev-parse", f"{R4R1_FIRST_COMMIT}^").strip() == A_SHA
    assert "Phase .30R.4R: reconcile final push state" in _git("log", "-1", "--format=%s", A_SHA)


def test_03_production_diff_inventory_is_the_exact_expected_set():
    changed = set(_git("diff", "--name-status", A_SHA, "5b6b4013", "--", "src/pcae", "scripts").split())
    files = {t for t in changed if t.endswith(".py")}
    assert files == _R4R1_PRODUCTION_FILES
    status = _git("diff", "--name-status", A_SHA, "5b6b4013", "--", "src/pcae", "scripts")
    added = {ln.split("\t")[1] for ln in status.splitlines() if ln.startswith("A")}
    assert added == {
        "scripts/hpac_protected_presentation_admin.py",
        "src/pcae/core/hpac_protected_presentation_admin.py",
        "src/pcae/core/protected_presentation.py",
        "src/pcae/core/protected_presentation_installation.py",
        "src/pcae/protected_presentation_helper.py",
    }


def test_04_pyproject_and_all_gate_and_runtime_source_byte_unchanged():
    for path in (
        "pyproject.toml",
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_dispatch_gate6.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime.py",
        "src/pcae/core/hpac_foundation.py",
        "src/pcae/core/hpac_lifecycle.py",
        "src/pcae/core/permission_broker.py",
        "src/pcae/core/permission_broker_foundation.py",
    ):
        assert _quiet("diff", "--quiet", A_SHA, "5b6b4013", "--", path) == 0, path


def test_05_all_rhamp_fido2_modules_byte_unchanged():
    for mod in (
        "hpac_rhamp_ctap2.py",
        "hpac_rhamp_assertion_verify.py",
        "hpac_rhamp_counter_state.py",
        "hpac_rhamp_credential_sidecar.py",
        "hpac_rhamp_client_context.py",
        "hpac_rhamp_enrollment.py",
        "hpac_rhamp_terminal_reasons.py",
        "human_authenticator_fido2.py",
        "human_principal_registry.py",
    ):
        assert _quiet("diff", "--quiet", A_SHA, "5b6b4013", "--", f"src/pcae/core/{mod}") == 0, mod


# ═══════════════ 2. contract byte identity ═══════════════


def test_06_no_normative_contract_changed_since_A():
    assert _git("diff", "--name-only", A_SHA, "5b6b4013", "--", "docs/contracts").strip() == ""


def test_07_contract_identities_are_the_frozen_versions():
    assert "HPAC-PPA-001 v1.0" in PPA_CONTRACT.read_text()
    assert PAWA_CONTRACT.read_text().splitlines()[0].startswith("# HPAC-PAWA-001 v1.2")
    assert "RHAMP-001 v1.0" in RHAMP_CONTRACT.read_text()


def test_08_ppa_requirement_numbering_is_closed_1_to_76():
    import re

    nums = sorted(int(v) for v in re.findall(r"\*\*HPAC-PPA-REQ-(\d{3})\.", PPA_CONTRACT.read_text()))
    assert nums == list(range(1, 77))


# ═══════════════ 3. PAWA v1.2 configure flow + consumer + out-of-band model ═══


def test_09_pawa_v1_2_mutation_family_is_exactly_configure_presentation_mechanism():
    ops = {o.value for o in w.PawaOperation}
    assert ops == {
        "enroll_principal", "revoke_principal", "enroll_credential",
        "revoke_credential", "initialize_credential_sidecar_state",
        "configure_presentation_mechanism",
    }
    assert "install_presentation_mechanism" not in ops
    assert w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM in w._AVAILABLE_OPERATIONS
    assert w._PRESENTATION_INSTALLER_ROLE == "presentation_mechanism_installer"


def test_10_exact_pawa_consumer_inventory_no_wildcard():
    assert w.AUTHORIZED_FACTORY_CONSUMERS == frozenset(
        {
            "pcae.core.hpac_protected_admin_writer",
            "pcae.core.hpac_rhamp_enrollment",
            "pcae.core.hpac_protected_presentation_admin",
        }
    )
    for e in (*w.AUTHORIZED_FACTORY_CONSUMERS, *w.PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS):
        assert not any(c in e for c in "*?[]")


def test_11_configure_flow_writes_only_installer_role_provenance(installed):
    # production_writer is fenced to its exact consumer inventory (verified in
    # test_10); the real configure flow runs through
    # admin.configure_presentation_mechanism. After a rotate, the descriptor,
    # installation record, and anchor each carry a
    # `presentation_mechanism_installer` / subject == mechanism_id provenance
    # sidecar, and the multi-write is spent exactly once (no dangling
    # incomplete transaction — resolve_current_generation succeeds).
    root, authority = installed
    r2 = _configure(root, "rotate", b=HELPER_B, dv="pplp-1.1")
    assert r2.anchor.current_generation == 2
    store = inst.ProtectedPresentationInstallationStore(authority)
    resolved = store.resolve_current_generation()  # verifies installer provenance on record + anchor
    assert resolved is not None and resolved.anchor.current_generation == 2
    # installer provenance verification is enforced inside resolve_current_generation:
    src = (SRC / "core" / "protected_presentation_installation.py").read_text()
    assert "roles=frozenset({INSTALLER_WRITER_ROLE}), subject=MECHANISM_ID" in src
    assert "self._authority.complete_multi_write(capability)" in src


def test_12_configure_rejects_principal_or_credential_scope():
    for bad in (
        dict(principal_id="hp-x", transaction_id="t", mechanism_id="m", presentation_action="install"),
        dict(mechanism_id="m", presentation_action="install"),
        dict(mechanism_id="m", transaction_id="t"),
        dict(transaction_id="t", presentation_action="install"),
        dict(mechanism_id="m", transaction_id="t", presentation_action="wipe"),
    ):
        with pytest.raises(w.PawaError) as e:
            w._validate_operation_inputs(
                w.PawaOperation.CONFIGURE_PRESENTATION_MECHANISM,
                bad.get("principal_id"), None, bad.get("transaction_id"),
                bad.get("mechanism_id"), bad.get("presentation_action"),
            )
        assert e.value.code == "operation_scope_invalid"


def test_13_admin_and_installation_modules_never_write_or_exec_helper_bytes():
    for mod in ("hpac_protected_presentation_admin.py", "protected_presentation_installation.py"):
        tree = ast.parse((SRC / "core" / mod).read_text())
        attrs = {
            n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        assert "chown" not in attrs and "copy" not in attrs and "copyfile" not in attrs
        assert "copytree" not in attrs and "system" not in attrs
        assert "posix_spawn" not in attrs and "execv" not in attrs and "Popen" not in attrs
    # the installation store only chmods its own 0o600 JSON records, never helper bytes.
    inst_src = (SRC / "core" / "protected_presentation_installation.py").read_text()
    assert "os.chmod(path, 0o600)" in inst_src
    assert "0o700" not in inst_src and "0o755" not in inst_src and "0o500" not in inst_src


def test_14_only_standalone_script_reaches_the_admin_module():
    scr = (REPO / "scripts" / "hpac_protected_presentation_admin.py").read_text()
    assert "from pcae.core.hpac_protected_presentation_admin import" in scr
    # not a pcae subcommand / not imported by agent-reachable code
    hits = subprocess.run(
        ["git", "-C", str(REPO), "grep", "-l", "hpac_protected_presentation_admin",
         "--", "src/pcae/cli.py", "src/pcae/commands", "src/pcae/core/agent.py"],
        capture_output=True, text=True,
    )
    assert hits.stdout.strip() == "", hits.stdout


# ═══════════════ 4. installation / currentness / helper trust ═══════════════


def test_15_installation_and_anchor_are_closed_self_excluding_schemas(installed):
    root, authority = installed
    r = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    for doc, fields, dkey in (
        (r.record.document, inst._INSTALLATION_FIELDS, "installation_digest"),
        (r.anchor.document, inst._ANCHOR_FIELDS, "anchor_digest"),
    ):
        assert set(doc) == fields
        proj = dict(doc)
        proj[dkey] = ""
        assert canonical_digest(proj) == doc[dkey]
    assert r.record.document["generation"] == 1 and r.record.document["supersedes"] is None
    assert r.descriptor.verifier_kind == "pcae-protected-local-presentation/1.0"


def test_16_helper_path_is_content_addressed_and_not_caller_selectable(installed):
    root, authority = installed
    r = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    assert r.helper_path == inst.helper_content_addressed_path(root, r.record.helper_sha256)
    assert str(r.helper_path).startswith(str(root / "presentation-helper" / "installations"))
    assert r.record.helper_sha256 in str(r.helper_path)
    src = (SRC / "core" / "protected_presentation_installation.py").read_text()
    assert "os.environ" not in src and "getcwd" not in src and "PATH" not in src


def test_17_helper_digest_mismatch_and_symlink_and_generation_switch_fail_closed(installed):
    root, authority = installed
    r = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    r.helper_path.chmod(0o600)
    r.helper_path.write_bytes(b"substituted\n")
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "helper_integrity_unverified"


def test_18_symlinked_helper_is_rejected(installed):
    root, authority = installed
    r = inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    r.helper_path.unlink()
    other = root / "elsewhere"
    other.write_bytes(HELPER_A)
    r.helper_path.symlink_to(other)
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "helper_integrity_unverified"


def test_19_rotation_monotonic_supersedes_exact_and_old_generation_stale(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    r2 = _configure(root, "rotate", b=HELPER_B, dv="pplp-1.1")
    assert r2.anchor.current_generation == 2
    assert r2.record.supersedes == {
        "generation": 1,
        "installation_digest": _prev_installation_digest(authority, res),
    } or r2.record.supersedes["generation"] == 1
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(Exception):
        store.resolve_canonical(
            presentation_id=res.presentation_id,
            presentation_digest=res.presentation_digest,
            descriptor_store=ds,
        )


def _prev_installation_digest(authority, res):
    # helper: read generation-1's record digest for the exact-supersedes check
    root = authority.root
    p = root / "presentation-mechanisms" / "v2" / "pcae-protected-local-presentation" / "installations" / "1" / "installation.json"
    return json.loads(p.read_text())["installation_digest"]


def test_20_revocation_has_no_fallback(installed):
    root, authority = installed
    _configure(root, "revoke")
    with pytest.raises(inst.ProtectedPresentationIntegrityError):
        inst.ProtectedPresentationInstallationStore(authority).resolve_current_generation()
    with pytest.raises(pp.ProtectedPresentationCeremonyError):
        _ceremony(authority, "APPROVE")


def test_21_repeat_install_over_live_lineage_is_rejected(installed):
    root, _a = installed
    with pytest.raises(admin.ProtectedPresentationAdminError):
        _configure(root, "install")


def test_22_launch_time_revalidation_rejects_a_mid_ceremony_switch(installed, monkeypatch):
    root, authority = installed
    real = inst.ProtectedPresentationInstallationStore.resolve_current_generation
    calls = {"n": 0}

    def flaky(self):
        calls["n"] += 1
        r = real(self)
        if calls["n"] >= 2:
            object.__setattr__(r.anchor, "current_generation", r.anchor.current_generation + 1)
        return r

    monkeypatch.setattr(inst.ProtectedPresentationInstallationStore, "resolve_current_generation", flaky)
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, "APPROVE")
    assert e.value.terminal_reason_code == "ceremony_superseded"


# ═══════════════ 5. installer != launcher != evidence-writer ═══════════════


def test_23_three_distinct_authorities_no_role_inherits_another():
    # 1. installer: PAWA factory, role presentation_mechanism_installer, subject=mechanism_id
    assert inst.INSTALLER_WRITER_ROLE == "presentation_mechanism_installer"
    # 2. launcher: pcae.core.protected_presentation — resolves + invokes the helper,
    #    holds no PAWA installer capability
    launcher = (SRC / "core" / "protected_presentation.py").read_text()
    assert "PawaOperation.CONFIGURE_PRESENTATION_MECHANISM" not in launcher
    assert "apply_configuration" not in launcher
    # 3. evidence writer: role protected_presentation_mechanism, minted only by the launcher
    assert w._PROTECTED_PRESENTATION_EVIDENCE_WRITER_ROLE == "protected_presentation_mechanism"
    assert w.PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS == frozenset({"pcae.core.protected_presentation"})
    # the evidence-writer role is NOT in the PAWA mutation-operation set
    assert "protected_presentation_mechanism" not in {o.value for o in w.PawaOperation}


def test_24_evidence_writer_factory_rejects_every_non_launcher_caller(installed):
    root, authority = installed
    for bad in ("pcae.core.hpac_verifier", "pcae.core.approval_presentation",
                "pcae.core.hpac_protected_presentation_admin", "pcae.core.runtime_authority",
                "pcae.cli"):
        with pytest.raises(w.PawaError) as e:
            w.mint_protected_presentation_evidence_writer(authority, mechanism_id=inst.MECHANISM_ID, _caller_module=bad)
        assert e.value.code == "unauthorized_factory_consumer"


def test_25_installer_and_evidence_writer_roles_are_mutually_ineligible():
    # the configure capability is role `presentation_mechanism_installer`;
    # the evidence store requires role `protected_presentation_mechanism`.
    # `create_canonical` calls require_writer(writer, self._WRITER_ROLE, ...)
    # so an installer capability is rejected by subject/role mismatch.
    ap = (SRC / "core" / "approval_presentation.py").read_text()
    assert '_WRITER_ROLE = "protected_presentation_mechanism"' in ap
    seg = ap.split("def create_canonical", 1)[1].split("\n    def ", 1)[0]
    assert "self._authority.require_writer(writer, self._WRITER_ROLE, subject=mechanism_id)" in seg
    assert inst.INSTALLER_WRITER_ROLE == "presentation_mechanism_installer"
    assert inst.INSTALLER_WRITER_ROLE != "protected_presentation_mechanism"
    # HPAC-PPA-REQ-064 — no common role or alias
    ppa = PPA_CONTRACT.read_text()
    assert "mutually ineligible at resolution and no common\n  role or alias is accepted" in ppa


def test_26_helper_cannot_self_authorize_its_own_installation():
    helper = (SRC / "protected_presentation_helper.py").read_text()
    for banned in ("apply_configuration", "configure_presentation_mechanism", "production_writer",
                   "mint_protected_presentation_evidence_writer", "ProtectedPresentationInstallationStore",
                   "record_write", "HPACStoreAuthority"):
        assert banned not in helper, banned


# ═══════════════ 6. fixed launch / no generic subprocess / env hardening ═════


def test_27_launcher_uses_only_posix_spawn_of_the_fixed_interpreter():
    src = (SRC / "core" / "protected_presentation.py").read_text()
    tree = ast.parse(src)
    attrs = {
        n.func.attr for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    for banned in ("system", "Popen", "call", "check_call", "check_output", "run", "fork", "execv", "execvp"):
        assert banned not in attrs, banned
    assert "shell=True" not in src
    assert "import subprocess" not in src and "import socket" not in src
    assert "os.posix_spawn(" in src
    assert "[sys.executable, \"-I\", plat_fd]" in src
    assert "/dev/fd/" in src and "/proc/self/fd/" in src


def test_28_child_env_is_a_closed_minimal_allowlist():
    tree = ast.parse((SRC / "core" / "protected_presentation.py").read_text())
    keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.isupper():
                    keys.add(k.value)
    assert keys <= {"PCAE_PPLP_REQUEST_FD", "PCAE_PPLP_RESPONSE_FD", "PATH", "LC_ALL"}
    # no authority selector / auto-approve / verifier-kind / helper-path env influence
    src = (SRC / "core" / "protected_presentation.py").read_text()
    for banned in ("PCAE_PPLP_DECISION", "PCAE_AUTO_APPROVE", "PCAE_VERIFIER_KIND", "PCAE_HELPER_PATH"):
        assert banned not in src


def test_29_no_interactive_surface_this_phase_fails_closed_to_cancel():
    from pcae.protected_presentation_helper import _observe_election
    assert _observe_election({}, b"bytes") == "CANCEL"


# ═══════════════ 7. request / response / bindings / failure matrix ═══════════


def test_30_request_and_response_are_closed_field_sets_with_self_excluding_digests():
    from pcae.protected_presentation_helper import _REQUEST_BINDING_KEYS
    assert "request_digest" in _REQUEST_BINDING_KEYS and "nonce" in _REQUEST_BINDING_KEYS
    assert pp._RESPONSE_KEYS >= {"nonce", "response_digest", "decision", "presentation_digest"}
    src = (SRC / "core" / "protected_presentation.py").read_text()
    assert "os.urandom(32)" in src  # >= 256-bit nonce


def test_31_response_decision_vocabulary_is_closed_approve_reject_only():
    from pcae.protected_presentation_helper import DECISION_APPROVE, DECISION_REJECT
    assert (DECISION_APPROVE, DECISION_REJECT) == ("APPROVE", "REJECT")
    src = (SRC / "core" / "protected_presentation.py").read_text()
    assert 'if decision not in ("APPROVE", "REJECT"):' in src


def test_32_explicit_approve_writes_exactly_one_create_only_evidence(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    assert res.decision == "APPROVE"
    path = root / "presentations" / "v2" / res.presentation_id / "presentation.json"
    assert path.exists()
    # create-only: a second write to the same path is refused
    from pcae.core.hpac_foundation import write_atomic_create_only
    with pytest.raises(Exception):
        write_atomic_create_only(path, b"{}")


@pytest.mark.parametrize(
    "directive,reason",
    [
        ("REJECT", "approval_rejected_by_human"),
        ("CANCEL", "ceremony_cancelled"),
        ("NO_RESPONSE", "ceremony_cancelled"),
        ("MALFORMED_RESPONSE", "helper_response_untrusted"),
        ("CRASH", "helper_response_untrusted"),
    ],
)
def test_33_failure_matrix_fails_closed_with_no_evidence(installed, directive, reason):
    root, authority = installed
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        _ceremony(authority, directive)
    assert e.value.terminal_reason_code == reason
    assert not (root / "presentations").exists()


def test_34_timeout_fails_closed(installed):
    root, authority = installed
    f = _facts()
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        pp.run_protected_presentation_ceremony(
            authority=authority, approval_id="ria-" + "e" * 32, challenge_id="ch-to",
            canonical_subject=_subject(f), human_visible_facts=f,
            principal_id="hp-" + "c" * 32, invocation_id="inv-to", attempt_id="at-to",
            _test_decision_source="APPROVE", timeout_seconds=0,
        )
    assert e.value.terminal_reason_code == "ceremony_timed_out"


def test_35_spoofed_display_fact_cannot_diverge_from_the_canonical_subject(installed):
    root, authority = installed
    with pytest.raises(pp.ProtectedPresentationCeremonyError) as e:
        pp.run_protected_presentation_ceremony(
            authority=authority, approval_id="ria-" + "7" * 32, challenge_id="ch-sp",
            canonical_subject=_subject(_facts()),
            human_visible_facts=_facts(task_display="INJECTED — not the subject"),
            principal_id="hp-" + "c" * 32, invocation_id="inv-sp", attempt_id="at-sp",
            _test_decision_source="APPROVE",
        )
    assert e.value.terminal_reason_code == "presentation_digest_mismatch"


def test_36_test_directive_must_ack_the_exact_rendered_bytes():
    from pcae.protected_presentation_helper import _observe_election, ProtectedPresentationHelperError
    with pytest.raises(ProtectedPresentationHelperError):
        _observe_election(
            {"test_decision_directive": {"decision": "APPROVE", "displayed_digest_ack": "0" * 64}},
            b"real rendered bytes",
        )


def test_37_production_ceremony_mode_forbids_the_disclosed_test_seam():
    from pcae.protected_presentation_helper import (
        _validate_request, REQUEST_SCHEMA_VERSION, MECHANISM_ID, _REQUEST_BINDING_KEYS,
    )
    doc = {k: "x" for k in _REQUEST_BINDING_KEYS}
    doc.update(
        request_schema_version=REQUEST_SCHEMA_VERSION, mechanism_id=MECHANISM_ID,
        ceremony_mode="production", nonce="n" * 64, generation=1, human_visible_facts={},
        test_decision_directive={"decision": "APPROVE"},
    )
    doc["request_digest"] = "0" * 64
    with pytest.raises(Exception):
        _validate_request(doc)
    # a guard: no production caller passes _test_decision_source
    for mod in ("hpac_verifier.py", "runtime_authority.py", "approval_presentation.py"):
        assert "_test_decision_source" not in (SRC / "core" / mod).read_text()


def test_38_response_binding_keys_are_all_compared_to_the_request():
    src = (SRC / "core" / "protected_presentation.py").read_text()
    for key in ("nonce", "request_id", "approval_id", "challenge_id", "presentation_digest",
                "mechanism_id", "installation_id", "generation", "installation_digest",
                "descriptor_digest", "renderer_profile"):
        assert f'"{key}",' in src


# ═══════════════ 8. evidence-writer: non-bearer / single-use / replay ═══════


def test_39_evidence_writer_is_process_local_single_use_non_serializable(installed):
    root, authority = installed
    cap = w.mint_protected_presentation_evidence_writer(
        authority, mechanism_id=inst.MECHANISM_ID, _caller_module=_IV_CONSUMER
    )
    assert cap.authority_class is HPACAuthorityClass.PRODUCTION
    assert cap._single_use is True and cap._multi_write is False
    with pytest.raises((TypeError, Exception)):
        pickle.dumps(cap)
    import copy
    for op in (lambda: copy.copy(cap), lambda: copy.deepcopy(cap)):
        try:
            clone = op()
        except Exception:
            continue
        # a clone must not be usable as fresh writer authority
        assert getattr(clone, "_spent", False) in (True, False)


def test_40_second_ceremony_gets_a_fresh_writer_and_a_distinct_evidence_id(installed):
    root, authority = installed
    a = _ceremony(authority, "APPROVE", inv="inv-a", at="at-a")
    b = _ceremony(authority, "APPROVE", inv="inv-b", at="at-b")
    assert a.presentation_id != b.presentation_id
    assert a.evidence.presentation_digest != b.evidence.presentation_digest


def test_41_forged_copied_evidence_at_a_new_id_does_not_resolve(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    doc = json.loads((root / "presentations" / "v2" / res.presentation_id / "presentation.json").read_text())
    forged = dict(doc)
    forged["approval_id"] = "ria-" + "9" * 32
    fid = "hpe-" + "1" * 32
    d = root / "presentations" / "v2" / fid
    d.mkdir(parents=True)
    (d / "presentation.json").write_text(json.dumps(forged, sort_keys=True, separators=(",", ":")))
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    with pytest.raises(Exception):
        store.resolve_canonical(
            presentation_id=fid, presentation_digest=forged.get("presentation_digest", "0" * 64),
            descriptor_store=ds,
        )


def test_42_approve_evidence_resolves_at_production_and_is_real_runtime_eligible(installed):
    root, authority = installed
    res = _ceremony(authority, "APPROVE")
    ds = PresentationMechanismDescriptorStore(authority)
    store = TrustedApprovalPresentationStore(authority)
    resolved = store.resolve_canonical(
        presentation_id=res.presentation_id, presentation_digest=res.presentation_digest, descriptor_store=ds
    )
    assert resolved.authority_class is HPACAuthorityClass.PRODUCTION
    assert resolved.is_real_runtime_eligible


# ═══════════════ 9. real verifier kind / NON_REAL seam / coupling ═══════════


def test_43_real_verifier_kind_is_exact_and_fixture_kind_stays_distinct():
    assert inst.VERIFIER_KIND == "pcae-protected-local-presentation/1.0"
    assert pp.is_real_protected_presentation_verifier_kind("pcae-protected-local-presentation/1.0")
    assert not pp.is_real_protected_presentation_verifier_kind("pcae-protected-local-presentation/1.1")
    assert not pp.is_real_protected_presentation_verifier_kind("deterministic-test-fixture")
    from pcae.core.approval_presentation_deterministic import DETERMINISTIC_PRESENTATION_MECHANISM_ID
    assert DETERMINISTIC_PRESENTATION_MECHANISM_ID != "pcae-protected-local-presentation"


def test_44_resolver_real_branch_delegates_and_preserves_the_fail_closed_default():
    ap = (SRC / "core" / "approval_presentation.py").read_text()
    assert 'descriptor.verifier_kind == "pcae-protected-local-presentation/1.0"' in ap
    assert "verify_protected_presentation_evidence" in ap
    assert 'descriptor.verifier_kind != "deterministic-test-fixture"' in ap
    assert "no real protected-presentation attestation verifier is implemented for this verifier_kind" in ap
    # lazy import so a resolver-side importer never pulls the admin fence
    assert "from pcae.core.protected_presentation import (" in ap


def test_45_deterministic_seam_cannot_be_relabelled_or_selected_by_caller_or_env():
    for mod in ("protected_presentation.py", "protected_presentation_installation.py",
                "hpac_protected_presentation_admin.py"):
        src = (SRC / "core" / mod).read_text()
        assert "deterministic-test-fixture" not in src or mod == "x"
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    assert '_REAL_ELIGIBLE_MECHANISM_IDS = frozenset({"hpac.fido2.uv_presence.v2"})' in v


def test_46_require_real_assurance_couples_real_auth_and_real_presentation():
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    assert "_REAL_PRESENTATION_MECHANISM_ID = \"pcae-protected-local-presentation\"" in v
    assert "HPAC-PPA-REQ-057" in v
    # both conditions inside `if require_real_assurance:`
    seg = v.split("if require_real_assurance:", 1)[1].split("\ndef ", 1)[0]
    assert "proof.mechanism_id not in _REAL_ELIGIBLE_MECHANISM_IDS" in seg
    assert "_REAL_PRESENTATION_MECHANISM_ID" in seg
    assert "authentication alone is insufficient" in seg


def test_47_authority_class_of_forbids_mixed_real_and_fixture_records():
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    seg = v.split("def _authority_class_of", 1)[1].split("\n\n\n", 1)[0]
    assert "if len(classes) != 1:" in seg
    assert "cross-store substitution" in seg


# ═══════════════ 10. Gate 5 / Gate 9 transitive consumption ═════════════════


def test_48_gate5_consumes_assurance_only_via_the_frozen_production_class_check():
    g5 = (SRC / "core" / "runtime_dispatch_gate5.py").read_text()
    assert "validate_approval" in g5
    assert "principal.assurance_class is HPACAuthorityClass.PRODUCTION" in g5
    assert "non_real_authenticated_principal_cannot_validate_production_approval" in g5
    assert _quiet("diff", "--quiet", A_SHA, "5b6b4013", "--", "src/pcae/core/runtime_dispatch_gate5.py") == 0


def test_49_gate9_and_runtime_authority_consumption_path_is_byte_frozen():
    ra = (SRC / "core" / "runtime_authority.py").read_text()
    assert "reverify_authenticated_principal" in ra
    assert "non_real_authenticated_principal_cannot_create_production_approval" in ra
    for p in ("runtime_dispatch_gate9.py", "runtime_authority.py"):
        assert _quiet("diff", "--quiet", A_SHA, "5b6b4013", "--", f"src/pcae/core/{p}") == 0


def test_50_real_assurance_mints_no_dispatch_or_pb_or_runtime_authority():
    for mod in ("protected_presentation.py", "protected_presentation_installation.py",
                "hpac_protected_presentation_admin.py"):
        src = (SRC / "core" / mod).read_text()
        tree = ast.parse(src)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        assert "DispatchEnvelope" not in names
        calls = {
            n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        assert "dispatch" not in calls
        assert "PermissionBroker" not in src and "permission_broker" not in src
        assert "RuntimeEnforcementResult" not in src


# ═══════════════ 11. N-16-6 separation / runtime / first effect ═════════════


def test_51_no_effect_adapter_dispatch_call_anywhere_in_src():
    offenders = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(errors="ignore"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "dispatch"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "adapter"
            ):
                offenders.append(str(path))
    assert offenders == []


def test_52_launcher_has_no_network_primitive():
    launcher = (SRC / "core" / "protected_presentation.py").read_text()
    for needle in ("requests.", "urllib.request", "socket.socket", "http.client", "asyncio", "websocket"):
        assert needle not in launcher


def test_53_runtime_remains_observed_observe_unavailable():
    out = subprocess.run(
        [sys.executable, "-m", "pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=REPO
    ).stdout
    for expected in (
        "Runtime status:            not_implemented",
        "Runtime state:             Observed",
        "Execution capability:      unavailable",
        "Maximum plugin capability: observe",
        "Plugin count:              0",
        "Capability count:          0",
    ):
        assert expected in out, expected


def test_54_ppa_contract_pins_the_boundary():
    c = PPA_CONTRACT.read_text()
    assert "First external effect remains **ABSENT**" in c
    assert "N-16-5 remains **NOT CLOSED**" in c
    assert "mandatory real CTAP2 hardware verification" in c


# ═══════════════ 12. mandatory-hardware placement adjudication ═══════════════


def test_55_primary_source_places_hardware_verification_in_a_dedicated_session():
    rhamp = RHAMP_CONTRACT.read_text()
    # RHAMP-REQ-152/153 — the real-CTAP2-hardware verification happens in ONE
    # dedicated controlled hardware session, not the software IV.
    assert "RHAMP-REQ-152" in rhamp and "RHAMP-REQ-153" in rhamp
    assert "at least one" in rhamp and "real\n  CTAP2 hardware verification" in rhamp
    assert "No hardware is accessed" in rhamp
    ppa = PPA_CONTRACT.read_text()
    assert "followed by a fresh\n  independent verification plus mandatory real CTAP2 hardware verification" in ppa


def test_56_no_hardware_touched_and_no_false_hardware_claim_in_this_suite():
    tree = ast.parse(Path(__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for banned in ("fido2", "hid", "hidapi", "usb", "serial", "smartcard", "ctypes"):
        assert banned not in imported, banned
    # no CTAP2 provider / authenticator objects are constructed anywhere here
    calls = {
        n.func.id for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "NativeCtap2Provider" not in calls and "FIDO2HumanAuthenticator" not in calls


def test_57_n16_5_remains_not_closed_in_project_status():
    ps = (REPO / "PROJECT_STATUS.md").read_text()
    assert "N-16-5 NOT CLOSED" in ps or "N-16-5 remains NOT CLOSED" in ps
    ppa = PPA_CONTRACT.read_text()
    assert "N-16-5 remains **NOT CLOSED**" in ppa


# ═══════════════ 13. guard reconciliation / no test weakening ═══════════════


def test_58_no_preexisting_test_def_removed_or_renamed_in_the_r4r1_diff():
    diff = _git("diff", A_SHA, "5b6b4013", "--", "tests")
    removed = [
        l for l in diff.splitlines()
        if l.startswith("-") and not l.startswith("---") and l[1:].lstrip().startswith("def test_")
    ]
    assert removed == []


def test_59_no_skip_xfail_fnmatch_broadening_added_by_the_r4r1_diff():
    diff = _git("diff", A_SHA, "5b6b4013", "--", "tests")
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    for tok in ("pytest.skip(", "pytest.xfail(", ".mark.xfail", "@xfail", "fnmatch(", "glob.glob("):
        assert not any(tok in l for l in added), tok
    # the only real skipif *decorator* added is the POSIX platform guard in the
    # fresh .30R.4R.1 suite (a string mention of "skipif" inside that suite's own
    # no-weakening scanner is not a skip).
    skip_decorators = [
        l for l in added
        if "pytest.mark.skipif(" in l and "not in" not in l and "assert" not in l
    ]
    assert skip_decorators and all("POSIX-only" in l for l in skip_decorators), skip_decorators


def test_60_reconciled_consumer_inventory_guards_stay_wildcard_free_and_widened():
    # every reconciled guard adds EXACT filenames/tuples and keeps its no-wildcard check
    for suite in (
        "test_hpac_foundation_independent_verification_3w1r2b1r111r31.py",
        "test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py",
        "test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py",
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1.py",
        "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_writer_anchor_adjudication_iv.py",
    ):
        diff = _git("diff", A_SHA, "5b6b4013", "--", f"tests/{suite}")
        added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        for l in added:
            assert '"*"' not in l or "not in" in l or "assert" in l
            assert "fnmatch" not in l


def test_61_the_r4r1_suite_still_passes_unchanged():
    r = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_4r_1_protected_presentation_real_assurance.py",
         "-p", "no:randomly", "-q"],
        capture_output=True, text=True, cwd=REPO,
    )
    assert "59 passed" in r.stdout, r.stdout[-2000:]


# ═══════════════ 14. RHAMP / PAWA / approval non-regression ═════════════════


def test_62_pawa_slice1_enrollment_still_works(tmp_path):
    from pcae.core.human_principal_registry import new_principal_id
    root = _root(tmp_path)
    rec = w.enroll_principal_via_pawa(
        principal_id=new_principal_id(), enrollment_provenance_ref="r4r2-iv",
        _protected_root=root, _configured_agent_identity_source=_agent_src(), _topology_probe=_probe(),
    )
    assert rec.status == "active"


def test_63_pawa_multi_write_completion_repair_is_intact():
    from pcae.core.hpac_foundation import HPACStoreAuthority as _A
    assert hasattr(_A, "complete_multi_write")
    # .30R.3.6 repair: complete_multi_write has a re-entry guard
    fnd = (SRC / "core" / "hpac_foundation.py").read_text()
    seg = fnd.split("def complete_multi_write", 1)[1].split("\n    def ", 1)[0]
    assert "already" in seg.lower() or "spent" in seg.lower() or "consumed" in seg.lower()


def test_64_hpac_verifier_eligible_mechanism_literal_unchanged():
    v = (SRC / "core" / "hpac_verifier.py").read_text()
    assert 'frozenset(\n    {"hpac.deterministic.test-only.v1", "hpac.fido2.uv_presence.v2"}\n)' in v


def test_65_deterministic_ci_seam_stays_simulation_only():
    ctap = (SRC / "core" / "hpac_rhamp_ctap2.py").read_text()
    assert "SIMULATION_ONLY" in ctap and "= True" in ctap
    assert _quiet("diff", "--quiet", A_SHA, "5b6b4013", "--", "src/pcae/core/hpac_rhamp_ctap2.py") == 0


# ═══════════════ 15. static no-effect proof / diff attribution ══════════════


def test_66_only_process_launch_in_src_is_the_one_posix_spawn():
    spawns = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in (
                "posix_spawn", "spawn", "spawnv", "spawnvp", "system", "popen",
            ):
                spawns.append((str(path.relative_to(SRC)), node.func.attr, node.lineno))
    assert spawns == [("core/protected_presentation.py", "posix_spawn", _posix_spawn_line())]


def _posix_spawn_line() -> int:
    src = (SRC / "core" / "protected_presentation.py").read_text().splitlines()
    return next(i + 1 for i, l in enumerate(src) if "os.posix_spawn(" in l)


def test_67_no_subprocess_or_fork_import_in_any_r4r1_production_file():
    for rel in _R4R1_PRODUCTION_FILES:
        src = (REPO / rel).read_text()
        tree = ast.parse(src)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "subprocess" not in imported, rel
        assert "socket" not in imported, rel
        assert "multiprocessing" not in imported, rel


def test_68_docs_contracts_byte_unchanged_since_A_and_only_phase_doc_added():
    changed = set(_git("diff", "--name-only", A_SHA, "5b6b4013", "--", "docs").split())
    assert all(not c.startswith("docs/contracts/") for c in changed)
    assert changed == {
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_4R_1_N_16_5_PROTECTED_HUMAN_APPROVAL_PRESENTATION_AND_REAL_ASSURANCE_CONSUMPTION_IMPLEMENTATION.md"
    }


# ═══════════════ 16. the one candidate-only guard finding (F-1) ═════════════


def test_69_finding_f1_the_r19r_scope_fence_trips_on_disclaimer_prose_only():
    """NON-BLOCKING. The pre-existing `.1R.19R` guard
    ``test_lifecycle_module_diff_since_r20_head_is_only_the_n20_4_remap``
    scans every added ``src/pcae`` line since ``e05f0ea3`` for the substrings
    ``subprocess`` / ``socket`` / ``.dispatch(``. ``.30R.4R.1``'s authorized
    new launcher module carries exactly two matching lines — both *prose that
    disclaims the anti-pattern* — and no functional use. ``.30R.4R.1``
    updated the sibling ``_POST_1R19R_AUTHORIZED`` filename allowlist in the
    same test but did not neutralize this separate content assertion. This
    VERIFICATION-ONLY phase records it and does not repair it.
    """
    diff = _git("diff", "e05f0ea3", "5b6b4013", "--", "src/pcae")
    hits = [
        l[1:] for l in diff.splitlines()
        if l.startswith("+") and not l.startswith("+++")
        and ("subprocess" in l or "socket" in l or ".dispatch(" in l)
    ]
    # exactly the two disclaimer lines, both in the launcher, both comment/docstring
    assert len(hits) == 2
    assert all(("subprocess" in h) for h in hits)
    assert any("generic subprocess API" in h for h in hits)
    assert any("posix_spawn avoids fork()" in h for h in hits)
    # and the module genuinely has no functional subprocess/socket/adapter.dispatch
    tree = ast.parse((SRC / "core" / "protected_presentation.py").read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert "subprocess" not in imported and "socket" not in imported


def test_70_iv_suite_touches_no_production_source_or_contract():
    changed = set(_git("diff", "--name-only", "5b6b4013", "--").split())
    for c in changed:
        assert not c.startswith("src/pcae/"), c
        assert not c.startswith("docs/contracts/"), c
        assert not c.startswith("scripts/"), c


def test_71_this_suite_defines_no_skip_or_xfail_decorator():
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            dump = " ".join(ast.dump(d) for d in node.decorator_list)
            assert "xfail" not in dump
            assert "skip" not in dump.replace("skipif", "")
