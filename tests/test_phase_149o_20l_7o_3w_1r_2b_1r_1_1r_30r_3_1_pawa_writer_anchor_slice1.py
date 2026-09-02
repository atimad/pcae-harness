"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 — N-16-5 PAWA Production
Protected-Admin Writer Anchor Implementation (Slice 1).

Fresh dedicated implementation suite for HPAC-PAWA-001 v1.1
(``docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md``).
FIDO2-free. Covers the §78 ≥94-case matrix: the closed
``HPAC-PAWA-AGENT-EXCLUSION/1.0`` schema and R1-HYBRID identity model, the
``HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`` + ``HPAC-PAWA-CURRENT-GENERATION/1.0``
(v1.1 7-field) schemas, the §33 11-step recognition sequence and every
conjunct, the ``O_EXCL|O_NOFOLLOW`` positive write probe, the three
distinct F-1 predicates, the two-principal rule, the exact 21-value
``pawa_failure_code`` taxonomy, the non-agent-importable factory fence +
exact consumer inventory, the process-local / non-bearer / restart-invalid
/ one-operation PRODUCTION capability, ``HumanPrincipalRegistryStore``
production consumption, provisioning / rotation / revocation, path /
symlink hardening, and the FIDO2-free / no-RHAMP / hpac_verifier-unchanged
/ Gate-unchanged / runtime-unchanged / first-effect-absent scope fence.

Every fixture uses a disposable ``tmp_path`` protected root and a
deterministic :class:`TopologyProbe` — no test touches the real
``resolve_hpac_protected_root()`` path, requires sudo, or resolves a real
OS account for authority.
"""

from __future__ import annotations

import ast
import copy
import json
import os
import pickle
import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core import hpac_pawa_agent_exclusion as ax
from pcae.core import hpac_pawa_schemas as sch
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACAuthorityClass,
    HPACStoreAuthority,
    HPACWriterCapability,
    canonical_digest,
    canonical_json_bytes,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryError,
    HumanPrincipalRegistryStore,
)

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACT = REPO / "docs" / "contracts" / "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md"
THIS_MODULE = "test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_1_pawa_writer_anchor_slice1"

FAKE_AGENT_UID = 4_242_424
FAKE_AGENT_GID = 999_999
AGENT_ACCOUNT = "pcae-agent-svc"


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ═══════════════════════════════════════════════════════════════════════════


def _agent_src(uid_by_name=None):
    """A deterministic ``_configured_agent_identity_source``: resolves the
    provisioned account name to ``(provisioned_uid, {gid})``. Mirrors a
    live ``getpwnam`` + ``os.getgrouplist``."""

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


def _agent_writable_probe(reason="group_drift"):
    def ewa(path, uid, gids):
        return (True, reason, ())

    def acs(start, uid, gids):
        return (True, ())

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


def _indeterminate_probe():
    def ewa(path, uid, gids):
        return (None, "acl_inspection_unavailable", ())

    def acs(start, uid, gids):
        return (None, ("acl_inspection_unavailable",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


def _ancestor_writable_probe():
    def ewa(path, uid, gids):
        return (False, "fixture_locked", ())

    def acs(start, uid, gids):
        return (False, ("ancestor_writable:/tmp",))

    return w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


@pytest.fixture
def provisioned(tmp_path):
    root = (tmp_path / "hpac-protected-root").resolve()
    info = w.provision_protected_root(
        protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
    )
    return root, info


def _authority(root, probe=None):
    return HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=probe or _locked_probe()
    )


def _mint(root, operation=w.PawaOperation.ENROLL_PRINCIPAL, *, principal_id=None, credential_id=None,
          src=None, probe=None, caller=None):
    return w.production_writer(
        operation,
        principal_id=principal_id,
        credential_id=credential_id,
        _protected_root=root,
        _configured_agent_identity_source=src or _agent_src(),
        _topology_probe=probe or _locked_probe(),
        _caller_module=caller,
    )


def _authority_dir(root):
    return root / ".authority"


def _read(path):
    return json.loads(path.read_text())


def _rewrite(path, document):
    path.write_text(canonical_json_bytes(document).decode())


import io
import tokenize as _tok


def _noncomment_source(name: str) -> str:
    """Module source with the leading docstring and every ``#`` comment
    stripped — so a scope-fence phrase in prose ("no FIDO2HumanAuthenticator")
    never trips a "not implemented in code" guard, while real string
    constants (schema ids, error text) are preserved."""

    raw = (SRC / "core" / name).read_text(encoding="utf-8")
    out = []
    seen_code = False
    for t in _tok.generate_tokens(io.StringIO(raw).readline):
        if t.type == _tok.COMMENT:
            continue
        if t.type == _tok.STRING and not seen_code and t.start[1] == 0:
            continue  # module docstring
        if t.type not in (_tok.NL, _tok.NEWLINE, _tok.INDENT, _tok.DEDENT, _tok.ENCODING):
            seen_code = True
        out.append(t.string)
    return " ".join(out)


HP_A = "hp-" + "a" * 32
HP_B = "hp-" + "b" * 32
HPC_A = "hpc-" + "a" * 32
NORM = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731


# ═══════════════════════════════════════════════════════════════════════════
# 1-2. HPAC-PAWA v1.1 contract identity + historical .1R.30 immutable BLOCKED
# ═══════════════════════════════════════════════════════════════════════════


def test_01_contract_is_hpac_pawa_001_v1_1_frozen():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "HPAC-PAWA-001 v1.1" in text and "**Version:** 1.1" in text and "**Status:** FROZEN" in text


def test_02_historical_1r30_is_immutable_blocked_not_reused():
    subject = subprocess.run(
        ["git", "-C", str(REPO), "log", "-1", "--format=%s", "8e65529596fc351face4b83c4b5d08573326d034"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "1R.30:" in subject and "BLOCKED" in subject
    # This phase's own commits never reuse the bare .1R.30 token as an anchor.
    assert "PAWA-INV-11" in CONTRACT.read_text(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 3-11. AGENT-EXCLUSION exact closed schema + R1-HYBRID account resolution
# ═══════════════════════════════════════════════════════════════════════════


def test_03_agent_exclusion_schema_is_closed_12_fields(provisioned):
    root, _ = provisioned
    doc = _read(_authority_dir(root) / "agent-exclusion.json")
    assert set(doc) == ax.AGENT_EXCLUSION_FIELDS
    assert len(ax.AGENT_EXCLUSION_FIELDS) == 12
    assert doc["artifact_schema_version"] == "HPAC-PAWA-AGENT-EXCLUSION/1.0"


def test_04_agent_exclusion_canonical_path(provisioned):
    root, _ = provisioned
    assert (_authority_dir(root) / "agent-exclusion.json").exists()


def test_05_symbolic_account_not_env_or_caller_derived(provisioned):
    root, info = provisioned
    doc = _read(_authority_dir(root) / "agent-exclusion.json")
    assert doc["symbolic_account"] == AGENT_ACCOUNT
    # production_writer signature carries no account / uid / gid parameter.
    params = set(w.production_writer.__code__.co_varnames[: w.production_writer.__code__.co_argcount])
    for forbidden in ("configured_agent_uid", "configured_agent_gids", "symbolic_account", "agent_account"):
        assert forbidden not in params


def test_06_provisioned_uid_captured_at_provisioning(provisioned):
    root, _ = provisioned
    doc = _read(_authority_dir(root) / "agent-exclusion.json")
    assert doc["provisioned_uid"] == FAKE_AGENT_UID


def test_07_live_uid_equality_required_every_recognition(provisioned):
    root, _ = provisioned
    # live uid != provisioned_uid -> agent_principal_unknown
    src = _agent_src({AGENT_ACCOUNT: FAKE_AGENT_UID + 1})
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=src)
    assert ei.value.code == "agent_principal_unknown"


def test_08_account_deletion_fails_closed_no_uid_fallback(provisioned):
    root, _ = provisioned
    src = _agent_src({"some-other-account": FAKE_AGENT_UID})  # AGENT_ACCOUNT absent -> KeyError
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=src)
    assert ei.value.code == "agent_principal_unknown"


def test_09_account_recreation_under_new_uid_no_silent_rebind(provisioned):
    root, _ = provisioned
    src = _agent_src({AGENT_ACCOUNT: FAKE_AGENT_UID + 5000})
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=src)
    assert ei.value.code == "agent_principal_unknown"


def test_10_uid_reuse_has_no_reverse_uid_fallback(provisioned):
    root, _ = provisioned
    # a different account now holds the numeric uid; the frozen name is gone.
    src = _agent_src({"attacker-acct": FAKE_AGENT_UID})
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=src)
    assert ei.value.code == "agent_principal_unknown"


def test_11_account_rename_fails_closed(provisioned):
    root, _ = provisioned
    src = _agent_src({AGENT_ACCOUNT + "-renamed": FAKE_AGENT_UID})
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=src)
    assert ei.value.code == "agent_principal_unknown"


# ═══════════════════════════════════════════════════════════════════════════
# 12-16. live groups / drift / removal recovery / OS-DB TCB
# ═══════════════════════════════════════════════════════════════════════════


def test_12_live_primary_and_supplementary_groups_enumerated_live(provisioned):
    root, _ = provisioned
    captured = {}

    def source(name, puid):
        captured["called"] = captured.get("called", 0) + 1
        return puid, frozenset({FAKE_AGENT_GID, 12345})

    _mint(root, principal_id=HP_A, src=source).consume(
        w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A
    )
    _mint(root, principal_id=HP_B, src=source)
    assert captured["called"] == 2  # resolved fresh on every call, never cached


def test_13_live_supplementary_group_membership_feeds_effective_access(provisioned):
    root, _ = provisioned
    seen = {}

    def ewa(path, uid, gids):
        seen["gids"] = gids
        return (False, "locked", ())

    probe = w.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=lambda s, u, g: (True, ()))

    def source(name, puid):
        return puid, frozenset({FAKE_AGENT_GID, 55, 66})

    _mint(root, principal_id=HP_A, src=source, probe=probe)
    assert {55, 66}.issubset(seen["gids"])


def test_14_group_drift_denies_writer(provisioned):
    root, _ = provisioned
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, probe=_agent_writable_probe("group_drift"))
    assert ei.value.code == "agent_has_protected_write_authority"


def test_15_group_removal_recovers_without_reprovision(provisioned):
    root, _ = provisioned
    # first: agent has authority-granting group -> denied
    with pytest.raises(w.PawaError):
        _mint(root, principal_id=HP_A, probe=_agent_writable_probe())
    # then: group removed (live resolution reflects lower authority) -> eligible
    handle = _mint(root, principal_id=HP_A, probe=_locked_probe())
    assert handle.operation is w.PawaOperation.ENROLL_PRINCIPAL


def test_16_agent_exclusion_record_has_no_persisted_group_snapshot(provisioned):
    root, _ = provisioned
    doc = _read(_authority_dir(root) / "agent-exclusion.json")
    assert "gids" not in doc and "groups" not in doc and "supplementary_groups" not in doc
    c = CONTRACT.read_text(encoding="utf-8")
    assert "Group\n  membership SHALL NOT be persisted in the record as the " in c


# ═══════════════════════════════════════════════════════════════════════════
# 17-20. three distinct F-1 predicates + current-context + two-principal
# ═══════════════════════════════════════════════════════════════════════════


def test_17_three_f1_predicates_are_distinct_in_code():
    src_text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    # A: configured-agent protected-root authority (resolved identity)
    assert "agent_has_protected_write_authority" in src_text
    # B: current_context_is_agent (live vs configured)
    assert "current_context_is_agent" in src_text
    assert "_current_agent_identity()" in src_text
    # C: positive write probe (current administrative invocation)
    assert "_positive_write_probe" in src_text
    # No collapse into "current user is admin".
    assert "current user" not in src_text.lower()


def test_18_current_context_is_configured_agent_rejected(provisioned):
    root, _ = provisioned
    # make the live euid equal the configured-agent uid
    src = _agent_src({AGENT_ACCOUNT: os.geteuid()})
    # provisioned_uid in the record is FAKE_AGENT_UID; to isolate step 7 we
    # re-provision so provisioned_uid == live euid.
    root2 = root.parent / "root2"
    w.provision_protected_root(protected_root=root2, agent_account=AGENT_ACCOUNT, agent_uid=os.geteuid())
    with pytest.raises(w.PawaError) as ei:
        _mint(root2, principal_id=HP_A, src=_agent_src())
    assert ei.value.code == "current_context_is_agent"


def _attr_names(name: str) -> set:
    tree = ast.parse((SRC / "core" / name).read_text(encoding="utf-8"))
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
    }


def test_19_current_geteuid_is_not_the_configured_agent_source():
    attrs = _attr_names("hpac_pawa_agent_exclusion.py")
    assert "geteuid" not in attrs and "getuid" not in attrs
    assert "environ" not in attrs and "getenv" not in attrs
    assert "getpwnam" in attrs and "getgrouplist" in attrs


def test_20_two_principal_rule_single_account_host_fails_closed(provisioned):
    root, _ = provisioned
    # configured agent == deployment owner effective authority (agent can write)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, probe=_agent_writable_probe("single_account"))
    assert ei.value.code == "agent_has_protected_write_authority"


# ═══════════════════════════════════════════════════════════════════════════
# 21-28. protected root / .authority / descriptor / current-generation
# ═══════════════════════════════════════════════════════════════════════════


def test_21_protected_root_canonical_resolution_no_override():
    src_text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "HPACStoreAuthority.production()" in src_text  # production: no caller root
    assert "resolve_hpac_protected_root" in src_text


def test_22_authority_namespace_no_follow_symlink(provisioned, tmp_path):
    root, _ = provisioned
    ad = _authority_dir(root)
    # replace .authority with a symlink to an agent-writable dir
    victim = tmp_path / "evil"
    victim.mkdir()
    import shutil

    shutil.rmtree(ad)
    ad.symlink_to(victim)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code in {"protected_root_missing", "protected_root_untrusted"}


def test_23_descriptor_closed_schema_unchanged_13_fields(provisioned):
    root, _ = provisioned
    doc = _read(_authority_dir(root) / "deployment-owner.json")
    assert set(doc) == {
        "artifact_schema_version", "descriptor_digest", "anchor_id", "installation_id",
        "protected_root_identity", "authority_namespace", "deployment_owner_role",
        "configured_agent_exclusion_binding", "generation", "created_at", "supersedes",
        "provenance_ref", "state",
    }
    assert doc["configured_agent_exclusion_binding"] == {
        "excluded_principal_kind": "PCAE_CONFIGURED_AGENT_PRINCIPAL",
        "exclusion_basis": "OS_FILESYSTEM_WRITE_AUTHORITY",
    }
    # no account name / uid leaked into the descriptor
    assert AGENT_ACCOUNT not in json.dumps(doc)
    assert "uid" not in doc and "symbolic_account" not in doc


def test_24_current_generation_v1_1_seven_field_set(provisioned):
    root, _ = provisioned
    doc = _read(_authority_dir(root) / "current-generation.json")
    assert set(doc) == {
        "artifact_schema_version", "record_digest", "installation_id", "current_generation",
        "descriptor_digest", "agent_exclusion_digest", "updated_at",
    }
    assert doc["artifact_schema_version"] == "HPAC-PAWA-CURRENT-GENERATION/1.0"  # id NOT bumped


def test_25_agent_exclusion_digest_is_mandatory(provisioned):
    root, _ = provisioned
    cg_path = _authority_dir(root) / "current-generation.json"
    doc = _read(cg_path)
    del doc["agent_exclusion_digest"]
    doc["record_digest"] = ""
    doc["record_digest"] = sch.self_excluding_digest(doc, digest_field="record_digest")
    _rewrite(cg_path, doc)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code in {"descriptor_installation_mismatch", "agent_principal_unknown"}


def test_26_restored_stale_exclusion_record_rejected(provisioned):
    root, _ = provisioned
    ax_path = _authority_dir(root) / "agent-exclusion.json"
    original = _read(ax_path)
    # rotate the agent account -> new exclusion record + new anchor digest
    w.set_agent_exclusion(protected_root=root, agent_account="pcae-agent-v2", agent_uid=FAKE_AGENT_UID)
    # restore the old exclusion record bytes only
    _rewrite(ax_path, original)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=_agent_src())
    assert ei.value.code == "agent_principal_unknown"


def test_27_descriptor_rollback_rejected(provisioned):
    root, _ = provisioned
    d_path = _authority_dir(root) / "deployment-owner.json"
    gen1 = _read(d_path)
    w.rotate_descriptor(protected_root=root)  # now generation 2
    _rewrite(d_path, gen1)  # restore the superseded generation-1 descriptor
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, src=_agent_src())
    assert ei.value.code == "descriptor_generation_stale"


def test_28_installation_or_root_identity_mismatch(provisioned, tmp_path):
    root, _ = provisioned
    d_path = _authority_dir(root) / "deployment-owner.json"
    doc = _read(d_path)
    doc["protected_root_identity"] = {"device": 1, "inode": 2}
    doc["descriptor_digest"] = ""
    doc["descriptor_digest"] = sch.self_excluding_digest(doc, digest_field="descriptor_digest")
    _rewrite(d_path, doc)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code in {"descriptor_root_identity_mismatch", "descriptor_installation_mismatch", "descriptor_malformed"}


# ═══════════════════════════════════════════════════════════════════════════
# 29-35. positive write probe
# ═══════════════════════════════════════════════════════════════════════════


def test_29_probe_uses_o_excl_o_nofollow():
    src_text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "O_EXCL" in src_text and "O_NOFOLLOW" in src_text and "O_CREAT" in src_text


def test_30_probe_is_not_os_access():
    src_text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "os.access(" not in src_text


def test_31_probe_sentinel_is_random_and_removed(provisioned):
    root, _ = provisioned
    _mint(root, principal_id=HP_A).consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    leftover = list(_authority_dir(root).glob(".probe-*"))
    assert leftover == []


def test_32_probe_failure_when_authority_dir_unwritable(provisioned):
    root, _ = provisioned
    ad = _authority_dir(root)
    os.chmod(ad, 0o500)
    try:
        with pytest.raises(w.PawaError) as ei:
            _mint(root, principal_id=HP_A)
        assert ei.value.code in {"write_probe_failed", "protected_root_untrusted"}
    finally:
        os.chmod(ad, 0o700)


def test_33_probe_does_not_mutate_descriptor_or_generation(provisioned):
    root, _ = provisioned
    before_d = (_authority_dir(root) / "deployment-owner.json").read_bytes()
    before_g = (_authority_dir(root) / "current-generation.json").read_bytes()
    _mint(root, principal_id=HP_A)
    assert (_authority_dir(root) / "deployment-owner.json").read_bytes() == before_d
    assert (_authority_dir(root) / "current-generation.json").read_bytes() == before_g


def test_34_no_euid_zero_or_sudo_shortcut_in_source():
    for name in ("hpac_protected_admin_writer.py", "hpac_pawa_agent_exclusion.py", "hpac_pawa_schemas.py"):
        text = (SRC / "core" / name).read_text(encoding="utf-8")
        assert "geteuid() == 0" not in text and "getuid() == 0" not in text
        assert "SUDO_USER" not in text and "SUDO_UID" not in text


def test_35_indeterminate_permissions_fail_closed(provisioned):
    root, _ = provisioned
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, probe=_indeterminate_probe())
    assert ei.value.code == "protected_root_untrusted"


# ═══════════════════════════════════════════════════════════════════════════
# 36-39. §33 recognition sequence + no-conjunct-skip + consumer fence
# ═══════════════════════════════════════════════════════════════════════════


def test_36_full_recognition_success_mints_production_capability(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    assert isinstance(handle, w.ProductionWriterHandle)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert isinstance(cap, HPACWriterCapability)
    assert cap.authority_class is HPACAuthorityClass.PRODUCTION


def test_37_recognition_fails_if_descriptor_absent(provisioned):
    root, _ = provisioned
    (_authority_dir(root) / "deployment-owner.json").unlink()
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code == "descriptor_missing"


def test_38_recognition_is_atomic_with_the_mint():
    # No PRODUCTION capability object exists anywhere without the full
    # sequence having run: production_writer is the only public path and it
    # runs _run_recognition_sequence before _mint_production_writer_capability.
    src_text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    i_recog = src_text.index("_run_recognition_sequence(")
    i_mint = src_text.index("_mint_production_writer_capability(", src_text.index("def production_writer"))
    assert i_recog < i_mint


def test_39_admin_writer_module_not_imported_by_cli_or_agent_reachable_code():
    forbidden = [
        SRC / "cli.py",
        SRC / "core" / "agent.py",
        *(SRC / "commands").glob("*.py"),
    ]
    for source in forbidden:
        if not source.exists():
            continue
        text = source.read_text(encoding="utf-8")
        for needle in ("hpac_protected_admin_writer", "hpac_pawa_agent_exclusion", "production_writer"):
            assert needle not in text, f"{source} must not reference {needle}"


def test_40_exact_factory_consumer_inventory_no_wildcard():
    assert w.AUTHORIZED_FACTORY_CONSUMERS == frozenset({"pcae.core.hpac_protected_admin_writer"})
    for entry in (*w.AUTHORIZED_FACTORY_CONSUMERS, *w._TEST_FACTORY_CONSUMERS):
        assert "*" not in entry and "?" not in entry and "[" not in entry
    tree = ast.parse((SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            imported.add(n.module)
    assert "fnmatch" not in imported and "glob" not in imported
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "fnmatch" not in attrs and "glob" not in attrs and "fnmatchcase" not in attrs


def test_41_unauthorized_production_importer_rejected(provisioned):
    root, _ = provisioned
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A, caller="pcae.commands.agent")
    assert ei.value.code == "unauthorized_factory_consumer"


def test_42_no_agent_runtime_gate_plugin_consumer_of_the_factory():
    joined = "\n".join(
        p.read_text(encoding="utf-8")
        for p in SRC.rglob("*.py")
        if p.name not in {"hpac_protected_admin_writer.py"}
    )
    tree = ast.parse(joined) if False else None  # text scan is sufficient here
    assert "import hpac_protected_admin_writer" not in joined
    assert "from pcae.core.hpac_protected_admin_writer" not in joined


def test_43_admin_script_is_not_a_pcae_cli_subcommand():
    script = REPO / "scripts" / "hpac_protected_root_admin.py"
    assert script.exists()
    cli_source = (SRC / "cli.py").read_text(encoding="utf-8")
    assert "hpac_protected_root_admin" not in cli_source
    assert "hpac-protected-root" not in cli_source


# ═══════════════════════════════════════════════════════════════════════════
# 44-50. provisioning / duplicate bootstrap / rotation / revocation / migration
# ═══════════════════════════════════════════════════════════════════════════


def test_44_duplicate_bootstrap_rejected(provisioned):
    root, _ = provisioned
    with pytest.raises(w.ProvisioningError) as ei:
        w.provision_protected_root(protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    assert "duplicate_bootstrap" in str(ei.value)


def test_45_provision_creates_coherent_anchor_state(provisioned):
    root, info = provisioned
    ad = _authority_dir(root)
    for name in ("manifest.json", "deployment-owner.json", "current-generation.json", "agent-exclusion.json"):
        assert (ad / name).exists()
    assert (ad / "provenance").is_dir()
    d = sch.validate_authority_descriptor(_read(ad / "deployment-owner.json"))
    cg = sch.validate_current_generation(_read(ad / "current-generation.json"))
    assert d.generation == cg.current_generation == 1
    assert d.descriptor_digest == cg.descriptor_digest


def test_46_partial_provisioning_is_non_authoritative(tmp_path):
    root = (tmp_path / "partial").resolve()
    ad = root / ".authority"
    ad.mkdir(parents=True)
    (ad / "manifest.json").write_text(canonical_json_bytes({
        "schema_version": "HPAC-STORE-AUTHORITY/1.0", "store_id": "hpacs-x",
        "authority_class": "production", "root_identity": {"device": 1, "inode": 1},
    }).decode())
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code in {"descriptor_missing", "protected_root_untrusted", "protected_root_missing"}


def test_47_rotation_increments_generation(provisioned):
    root, _ = provisioned
    out = w.set_agent_exclusion(protected_root=root, agent_account="acct-2", agent_uid=FAKE_AGENT_UID)
    assert out["generation"] == 2
    cg = sch.validate_current_generation(_read(_authority_dir(root) / "current-generation.json"))
    assert cg.current_generation == 2


def test_48_old_exclusion_record_superseded_after_rotation(provisioned):
    root, _ = provisioned
    old = _read(_authority_dir(root) / "agent-exclusion.json")
    w.set_agent_exclusion(protected_root=root, agent_account="acct-2", agent_uid=77)
    new = _read(_authority_dir(root) / "agent-exclusion.json")
    assert new["generation"] == 2 and new["supersedes"]["previous_record_digest"] == old["record_digest"]
    # a mint now resolves the new account, not the old
    handle = _mint(root, principal_id=HP_A, src=_agent_src({"acct-2": 77}))
    assert handle.descriptor_generation == 2


def test_49_revoked_anchor_rejects_mint(provisioned):
    root, _ = provisioned
    w.revoke_anchor(protected_root=root)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code == "descriptor_revoked"


def test_50_migrated_or_cloned_state_rejected(provisioned, tmp_path):
    root, _ = provisioned
    clone = (tmp_path / "clone").resolve()
    import shutil

    shutil.copytree(root, clone)
    with pytest.raises(w.PawaError) as ei:
        _mint(clone, principal_id=HP_A)
    assert ei.value.code in {"protected_root_untrusted", "descriptor_root_identity_mismatch", "agent_principal_unknown"}


# ═══════════════════════════════════════════════════════════════════════════
# 51-52. exact 21-value pawa_failure_code taxonomy + RHAMP map
# ═══════════════════════════════════════════════════════════════════════════


def test_51_exact_21_pawa_failure_codes():
    assert len(w.PAWA_FAILURE_CODES) == 21 == len(set(w.PAWA_FAILURE_CODES))
    assert set(w.PAWA_FAILURE_CODES) == {
        "protected_root_missing", "protected_root_untrusted", "agent_principal_unknown",
        "agent_has_protected_write_authority", "descriptor_missing", "descriptor_malformed",
        "descriptor_wrong_owner", "descriptor_wrong_mode", "descriptor_root_identity_mismatch",
        "descriptor_installation_mismatch", "descriptor_generation_stale", "descriptor_revoked",
        "write_probe_failed", "current_context_is_agent", "unauthorized_factory_consumer",
        "operation_scope_invalid", "target_scope_invalid", "capability_stale",
        "duplicate_bootstrap", "reconstruction_attempt", "internal_fail_closed",
    }


def test_52_every_rejection_maps_to_a_vocabulary_code_and_rhamp_reason():
    assert set(w.RHAMP_TERMINAL_REASON_MAP) == set(w.PAWA_FAILURE_CODES)
    assert set(w.RHAMP_TERMINAL_REASON_MAP.values()) <= {
        "bootstrap_authority_unproven", "enrollment_not_protected_admin",
        "protected_root_invalid", "internal_verification_error",
    }
    with pytest.raises(AssertionError):
        w.PawaError("not_a_real_code")


# ═══════════════════════════════════════════════════════════════════════════
# 53-60. PRODUCTION capability: positive + non-bearer + copy + serialize + restart + one-op
# ═══════════════════════════════════════════════════════════════════════════


def test_53_production_factory_positive_fixture_success(provisioned):
    root, _ = provisioned
    rec = w.enroll_principal_via_pawa(
        principal_id=HP_A, enrollment_provenance_ref="pr-1",
        _protected_root=root, _configured_agent_identity_source=_agent_src(), _topology_probe=_locked_probe(),
    )
    assert rec.principal_id == HP_A and rec.status == "active"


def test_54_direct_constructor_rejected():
    with pytest.raises(Exception):
        HPACWriterCapability(object(), "role", None, HPACAuthorityClass.PRODUCTION, _seal=object())


def test_55_object_new_reconstruction_rejected(provisioned):
    root, _ = provisioned
    authority = _authority(root)
    forged = HPACWriterCapability.__new__(HPACWriterCapability)
    with pytest.raises(Exception):
        authority.require_writer(forged, "human_principal_registry_admin")


def test_55a_nonissued_capability_shell_is_rejected(provisioned):
    """Phase .1R.30R.3.2.1 (N-16-5 repair) — the exact adversary
    .1R.30R.3.2 independently found and reproduced: a caller who already
    legitimately holds one issued capability copies its *real*
    ``_authority_seal`` (and every other field) onto an
    ``object.__new__`` shell it constructs itself. Unlike ``test_55``,
    every field is populated with genuine values, so ``writer.
    _authority_seal is self._seal`` is genuinely true — the shell is
    rejected only because it was never returned by the canonical factory
    (HPAC-PAWA-REQ-102/106/107), independent of any field it carries."""

    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)

    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    shell._authority_seal = cap._authority_seal
    shell.role = cap.role
    shell.subject = cap.subject
    shell.authority_class = cap.authority_class
    shell._single_use = True
    shell._spent = False

    with pytest.raises(Exception):
        handle.authority.require_writer(shell, "human_principal_registry_admin", subject=HP_A)


def test_55b_writer_authority_requires_canonical_issuance_membership(provisioned):
    """The same adversary, driven through the real production consumption
    path (HumanPrincipalRegistryStore), not just require_writer in
    isolation -- matching .1R.30R.3.2 §5.3's live reproduction."""

    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())
    assert cap._spent is True

    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    shell._authority_seal = cap._authority_seal
    shell.role = cap.role
    shell.subject = cap.subject
    shell.authority_class = cap.authority_class
    shell._single_use = True
    shell._spent = False

    with pytest.raises(HumanPrincipalRegistryError):
        store.revoke_principal(shell, principal_id=HP_A, revoked_at=w._now())


def test_55c_one_operation_capability_cannot_be_duplicated_via_field_copy(provisioned):
    """A shell built from a *not-yet-spent* legitimate capability's fields
    (rather than an already-spent one) is equally rejected -- membership,
    not spend state, is the decisive gate."""

    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert cap._spent is False

    shell = HPACWriterCapability.__new__(HPACWriterCapability)
    shell._authority_seal = cap._authority_seal
    shell.role = cap.role
    shell.subject = cap.subject
    shell.authority_class = cap.authority_class
    shell._single_use = True
    shell._spent = False

    with pytest.raises(Exception):
        handle.authority.require_writer(shell, "human_principal_registry_admin", subject=HP_A)
    # the genuine capability is unaffected and still usable exactly once.
    handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_A)


def test_55d_registry_bound_scope_dominates_mutated_object_fields(provisioned):
    """A legitimately-issued capability whose plain, mutable ``role`` /
    ``subject`` slots are reassigned after mint (attacker-reachable field
    mutation -- a distinct but related non-bearer gap) cannot thereby
    widen its authorized scope: the canonical, registry-bound scope
    frozen at mint time dominates."""

    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)

    # attacker-controlled in-process mutation of the object's own fields.
    cap.subject = HP_B

    with pytest.raises(Exception):
        handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_B)
    # the true, registry-bound scope (HP_A) still works.
    handle.authority.require_writer(cap, "human_principal_registry_admin", subject=HP_A)


def test_56_copy_does_not_create_a_second_usable_capability(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(TypeError):
        copy.copy(cap)
    with pytest.raises(TypeError):
        copy.deepcopy(cap)


def test_57_handle_is_non_serializable(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    with pytest.raises(TypeError):
        pickle.dumps(handle)


def test_58_capability_is_non_serializable(provisioned):
    root, _ = provisioned
    cap = _mint(root, principal_id=HP_A).consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(TypeError):
        pickle.dumps(cap)


def test_59_restart_invalidation_fresh_seal(provisioned):
    root, _ = provisioned
    cap = _mint(root, principal_id=HP_A).consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    # a NEW authority instance (simulating a process restart) has a fresh _seal
    other = _authority(root)
    with pytest.raises(Exception):
        other.require_writer(cap, "human_principal_registry_admin", subject=HP_A)


def test_60_one_operation_replay_rejected_at_both_layers(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())
    assert cap._spent is True
    # factory-layer replay
    with pytest.raises(w.PawaError) as ei:
        handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert ei.value.code == "capability_stale"
    # foundation-layer replay
    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="y", enrolled_at=w._now())


# ═══════════════════════════════════════════════════════════════════════════
# 61-69. scope / issuance evidence / registry consumption / bypass
# ═══════════════════════════════════════════════════════════════════════════


def test_61_wrong_mutation_class_rejected(provisioned):
    root, _ = provisioned
    handle = _mint(root, w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    with pytest.raises(w.PawaError) as ei:
        handle.consume(w.PawaOperation.REVOKE_PRINCIPAL, principal_id=HP_A)
    assert ei.value.code == "target_scope_invalid"


def test_62_wrong_principal_rejected_at_registry(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(cap, principal_id=HP_B, enrollment_provenance_ref="x", enrolled_at=w._now())


def test_63_slice2_operations_rejected(provisioned):
    root, _ = provisioned
    for op in ("enroll_credential", "initialize_credential_sidecar_state"):
        with pytest.raises(w.PawaError) as ei:
            _mint(root, op, principal_id=HP_A, credential_id=HPC_A)
        assert ei.value.code == "operation_scope_invalid"


def test_64_issuance_evidence_is_recorded_and_non_authoritative(provisioned):
    root, _ = provisioned
    _mint(root, principal_id=HP_A)
    ev_dir = _authority_dir(root) / "issuance-evidence"
    files = list(ev_dir.glob("*.json"))
    assert len(files) >= 1
    doc = _read(files[0])
    assert doc["event_schema_version"] == "HPAC-PAWA-ISSUANCE-EVIDENCE/1.0"
    assert "_authority_seal" not in json.dumps(doc)
    assert doc["result"] == "issued"


def test_65_direct_store_bypass_without_capability_rejected(provisioned):
    root, _ = provisioned
    store = HumanPrincipalRegistryStore(_authority(root))
    with pytest.raises((HumanPrincipalRegistryError, TypeError, AttributeError)):
        store.enroll_principal(object(), principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())


def test_66_structurally_forged_capability_rejected(provisioned):
    root, _ = provisioned
    authority = _authority(root)
    forged = HPACWriterCapability.__new__(HPACWriterCapability)
    for slot, val in (("_authority_seal", object()), ("role", "human_principal_registry_admin"),
                      ("subject", HP_A), ("authority_class", HPACAuthorityClass.PRODUCTION),
                      ("_single_use", True), ("_spent", False)):
        object.__setattr__(forged, slot, val)
    store = HumanPrincipalRegistryStore(authority)
    with pytest.raises(HumanPrincipalRegistryError):
        store.enroll_principal(forged, principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())


def test_67_fixture_capability_rejected_for_production_store(tmp_path, provisioned):
    root, _ = provisioned
    fixture_authority = HPACStoreAuthority.fixture((tmp_path / "fx").resolve())
    fx_writer = fixture_authority.writer("human_principal_registry_admin")
    prod_store = HumanPrincipalRegistryStore(_authority(root))
    with pytest.raises(HumanPrincipalRegistryError):
        prod_store.enroll_principal(fx_writer, principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())


def test_68_spent_capability_rejected(provisioned):
    root, _ = provisioned
    handle = _mint(root, principal_id=HP_A)
    cap = handle.consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    store = HumanPrincipalRegistryStore(handle.authority)
    store.enroll_principal(cap, principal_id=HP_A, enrollment_provenance_ref="x", enrolled_at=w._now())
    with pytest.raises(HumanPrincipalRegistryError):
        store.revoke_principal(cap, principal_id=HP_A, revoked_at=w._now())


def test_69_valid_capability_permits_exact_bounded_registry_mutation(provisioned):
    root, _ = provisioned
    w.enroll_principal_via_pawa(principal_id=HP_A, enrollment_provenance_ref="pr",
                               _protected_root=root, _configured_agent_identity_source=_agent_src(),
                               _topology_probe=_locked_probe())
    rec = w.revoke_principal_via_pawa(principal_id=HP_A, _protected_root=root,
                                      _configured_agent_identity_source=_agent_src(),
                                      _topology_probe=_locked_probe())
    assert rec.status == "revoked"
    store = HumanPrincipalRegistryStore(_authority(root))
    assert store.resolve_principal(HP_A).status == "revoked"


# ═══════════════════════════════════════════════════════════════════════════
# 70-72. CredentialRecord unchanged / registry transactions / provenance
# ═══════════════════════════════════════════════════════════════════════════


def test_70_credential_record_schema_unchanged():
    text = (SRC / "core" / "human_principal_registry.py").read_text(encoding="utf-8")
    m = re.search(r"_CREDENTIAL_ALLOWED_FIELDS = frozenset\(\s*\{(.*?)\}\s*\)", text, re.S)
    fields = {f.strip().strip('"').strip("'") for f in m.group(1).split(",") if f.strip()}
    assert fields == {
        "credential_id", "principal_id", "mechanism_id", "public_key",
        "assurance_capabilities", "status", "enrollment_provenance_ref", "enrolled_at", "revoked_at",
    }
    assert "fido2" not in text.lower().replace("fido2-free", "") or "RHAMP-FIDO2-CREDENTIAL" not in text


def test_71_registry_transaction_concurrency_semantics_preserved():
    text = (SRC / "core" / "human_principal_registry.py").read_text(encoding="utf-8")
    assert "writer_transaction" in text
    assert 'raise HumanPrincipalRegistryConflictError(\n                    "registry changed after read' in text
    assert "read-back verification failed after write" in text


def test_72_writer_provenance_preserved(provisioned):
    root, _ = provisioned
    w.enroll_principal_via_pawa(principal_id=HP_A, enrollment_provenance_ref="pr",
                               _protected_root=root, _configured_agent_identity_source=_agent_src(),
                               _topology_probe=_locked_probe())
    prov_dir = _authority_dir(root) / "provenance"
    assert any("HPAC-WRITER-PROVENANCE/1.0" in p.read_text() for p in prov_dir.glob("*.json"))


# ═══════════════════════════════════════════════════════════════════════════
# 73-77. writer inventories / path traversal / symlink escape / env override
# ═══════════════════════════════════════════════════════════════════════════


def test_73_exact_anchor_writer_inventory_in_source():
    text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    # every anchor record write goes through _atomic_create_record /
    # _atomic_replace_record / _write_anchor_provenance — no other writer.
    assert "_atomic_create_record" in text and "_atomic_replace_record" in text
    tree = ast.parse(text)
    write_calls = {
        n.func.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr in {"write_text", "write_bytes"}
    }
    assert write_calls == set()  # never a bare write_text/write_bytes on a protected record


def test_74_descriptor_and_generation_writer_inventory():
    text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert 'authority_dir / _DESCRIPTOR_NAME' in text
    assert 'authority_dir(protected_root) / _CURRENT_GENERATION_NAME' in text or "_CURRENT_GENERATION_NAME" in text


def test_75_path_traversal_and_symlinked_record_rejected(provisioned, tmp_path):
    root, _ = provisioned
    d_path = _authority_dir(root) / "deployment-owner.json"
    real = d_path.read_text()
    d_path.unlink()
    target = tmp_path / "evil-descriptor.json"
    target.write_text(real)
    d_path.symlink_to(target)
    with pytest.raises(w.PawaError) as ei:
        _mint(root, principal_id=HP_A)
    assert ei.value.code in {"descriptor_missing", "descriptor_malformed", "protected_root_untrusted"}


def test_76_cwd_repository_shadow_path_not_authority(provisioned, tmp_path, monkeypatch):
    root, _ = provisioned
    shadow = tmp_path / "shadow" / ".authority"
    shadow.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    # production_writer with the real fixture root still uses that root, not cwd
    handle = _mint(root, principal_id=HP_A)
    assert handle.installation_id  # resolved from the real fixture, unaffected by cwd


def test_77_environment_authority_override_rejected(provisioned, monkeypatch):
    root, _ = provisioned
    monkeypatch.setenv("PCAE_AGENT_PRINCIPAL", "root")
    monkeypatch.setenv("SUDO_USER", "root")
    monkeypatch.setenv("HPAC_PROTECTED_ROOT", "/tmp")
    handle = _mint(root, principal_id=HP_A)  # env is inert
    assert handle.operation is w.PawaOperation.ENROLL_PRINCIPAL


# ═══════════════════════════════════════════════════════════════════════════
# 78-94. scope fence: FIDO2-free / no RHAMP / hpac_verifier / gates / runtime
# ═══════════════════════════════════════════════════════════════════════════


def test_78_new_slice1_code_is_fido2_free():
    for name in ("hpac_protected_admin_writer.py", "hpac_pawa_agent_exclusion.py", "hpac_pawa_schemas.py"):
        text = (SRC / "core" / name).read_text(encoding="utf-8")
        for needle in ("import fido2", "from fido2", "Ctap2", "CtapHidDevice", "CoseKey", "AuthenticatorData"):
            assert needle not in text, f"{name}: {needle}"


def test_79_no_rhamp_sidecar_or_counter_state_files_introduced():
    names = {p.name for p in SRC.rglob("*.py")}
    assert "rhamp_fido2_credential.py" not in names
    assert "rhamp_counter_state.py" not in names
    for name in ("hpac_protected_admin_writer.py",):
        text = (SRC / "core" / name).read_text(encoding="utf-8")
        assert "RHAMP-FIDO2-CREDENTIAL/1.0" not in text
        assert "RHAMP-COUNTER-STATE/1.0" not in text


def test_80_no_enrollment_ceremony_or_fido2_authenticator():
    names = {p.name for p in SRC.rglob("*.py")}
    assert "fido2_human_authenticator.py" not in names
    code = _noncomment_source("hpac_protected_admin_writer.py")
    assert "FIDO2HumanAuthenticator" not in code
    assert "makeCredential" not in code and "getAssertion" not in code


def test_81_hpac_verifier_byte_unchanged_since_phase_entry():
    entry = "1793a75a73c54c6f6687bc830664caeac5aeaa66"
    diff = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--stat", entry, "HEAD", "--", "src/pcae/core/hpac_verifier.py"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert diff.strip() == ""


def test_82_eligible_mechanism_ids_unchanged():
    text = (SRC / "core" / "hpac_verifier.py").read_text(encoding="utf-8")
    assert "hpac.fido2.uv_presence.v2" not in text
    assert "_ELIGIBLE_MECHANISM_IDS" in text  # still present, just not widened here


def test_83_no_protected_presentation_implementation():
    text = "\n".join(
        (SRC / "core" / n).read_text(encoding="utf-8")
        for n in ("hpac_protected_admin_writer.py", "hpac_pawa_agent_exclusion.py", "hpac_pawa_schemas.py")
    )
    assert "pcae-protected-local-presentation/1.0" not in text
    assert "require_real_assurance" not in text


def test_84_gate5_and_gate9_byte_unchanged_since_phase_entry():
    entry = "1793a75a73c54c6f6687bc830664caeac5aeaa66"
    for g in ("runtime_dispatch_gate5.py", "runtime_dispatch_gate9.py"):
        diff = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--stat", entry, "HEAD", "--", f"src/pcae/core/{g}"],
            capture_output=True, text=True, check=True,
        ).stdout
        assert diff.strip() == "", g


def test_85_runtime_posture_unchanged():
    out = subprocess.run(
        ["python", "-m", "pcae", "runtime", "inspect"], capture_output=True, text=True, cwd=str(REPO)
    ).stdout
    assert "Runtime state:             Observed" in out
    assert "Execution capability:      unavailable" in out
    assert "Plugin count:              0" in out
    assert "Capability count:          0" in out


def test_86_no_effect_adapter_or_dispatch_call_in_slice1_source():
    for name in ("hpac_protected_admin_writer.py", "hpac_pawa_agent_exclusion.py", "hpac_pawa_schemas.py"):
        text = (SRC / "core" / name).read_text(encoding="utf-8")
        for needle in ("adapter.dispatch(", "DispatchEnvelope", "subprocess", "socket", "http", "Popen",
                       "os.system", "runtime plugin", "RPAC-REQ-095"):
            assert needle not in text, f"{name}: {needle}"


def test_87_contract_byte_identity_hpac_rhamp_hbdc_unchanged_since_entry():
    entry = "1793a75a73c54c6f6687bc830664caeac5aeaa66"
    changed = subprocess.run(
        ["git", "-C", str(REPO), "diff", "--name-only", entry, "HEAD", "--", "docs/contracts"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert changed == [], f"no contract file changes this phase: {changed}"


def test_88_no_src_pcae_writer_capability_second_construction_site():
    hits = [
        (p.name, i + 1)
        for p in SRC.rglob("*.py")
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines())
        if "HPACWriterCapability(" in line and "class HPACWriterCapability" not in line
    ]
    assert len(hits) == 1 and hits[0][0] == "hpac_foundation.py", hits


def test_89_writer_still_refuses_non_fixture_class_directly():
    text = (SRC / "core" / "hpac_foundation.py").read_text(encoding="utf-8")
    assert 'raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")' in text


def test_90_pawa_capability_is_not_runtime_approval(provisioned):
    root, _ = provisioned
    cap = _mint(root, principal_id=HP_A).consume(w.PawaOperation.ENROLL_PRINCIPAL, principal_id=HP_A)
    assert not hasattr(cap, "approval_id")
    assert not hasattr(cap, "dispatch_envelope")
    text = (SRC / "core" / "hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "AuthenticatedHumanPrincipal" not in text
    assert "PermissionBroker" not in text and "Gate7Result" not in text


def test_91_n16_6_and_n16_7_untouched():
    entry = "1793a75a73c54c6f6687bc830664caeac5aeaa66"
    for mod in ("runtime_dispatch_gate10_eligibility.py", "permission_broker.py", "runtime.py"):
        pth = SRC / "core" / mod
        if not pth.exists():
            continue
        diff = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--stat", entry, "HEAD", "--", f"src/pcae/core/{mod}"],
            capture_output=True, text=True, check=True,
        ).stdout
        assert diff.strip() == "", mod
    code = _noncomment_source("hpac_protected_admin_writer.py")
    assert "supply_chain" not in code and "RPAC_REQ_095" not in code


def test_92_first_external_effect_absent():
    joined = "\n".join(
        (SRC / "core" / n).read_text(encoding="utf-8")
        for n in ("hpac_protected_admin_writer.py", "hpac_pawa_agent_exclusion.py", "hpac_pawa_schemas.py")
    )
    # the only filesystem writes are bounded PAWA administrative state
    assert "requests." not in joined and "urllib" not in joined and "asyncio" not in joined


def test_93_agent_exclusion_digest_binds_into_the_monotonic_anchor(provisioned):
    root, _ = provisioned
    ax_doc = _read(_authority_dir(root) / "agent-exclusion.json")
    cg_doc = _read(_authority_dir(root) / "current-generation.json")
    assert cg_doc["agent_exclusion_digest"] == ax_doc["record_digest"]


def test_94_recognition_runs_fresh_every_call_not_cached(provisioned):
    root, _ = provisioned
    calls = []

    def source(name, puid):
        calls.append(name)
        return puid, frozenset({FAKE_AGENT_GID})

    _mint(root, principal_id=HP_A, src=source)
    _mint(root, principal_id=HP_B, src=source)
    _mint(root, principal_id="hp-" + "c" * 32, src=source)
    assert len(calls) == 3


def test_95_this_suite_is_new_and_adds_no_skip_or_xfail():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            dotted = getattr(node.func.value, "attr", "") + "." + node.func.attr
            if node.func.attr in {"skip", "xfail"} and "pytest" in ast.dump(node.func):
                bad.append(dotted)
        if isinstance(node, ast.Attribute) and node.attr == "skip":
            parent = ast.dump(node)
            if "mark" in parent:
                bad.append("mark.skip")
    assert bad == [], bad
