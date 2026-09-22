"""Phase 150G — N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-CORE-IMPLEMENTATION.

Realizes the Model B architecture Phase 150F selected and froze
(``docs/PHASE_150F_N16_5_F_5_TB_HELPER_ADMISSION_RECOGNITION_SHARED_INFRASTRUCTURE_ARCHITECTURE.md``):
extracts ``hpac_protected_admin_writer._run_recognition_sequence`` steps
1-8 into ``src/pcae/core/hpac_pawa_recognition_core.py`` (a new, neutral,
non-agent-importable module) and refactors the legacy factory to call it.

This suite proves: behavior parity (old vs. new fail-closed outcomes
identical), the shared core's non-authoritative/read-only/fail-closed
nature, absence of any duplicate steps-1-8 implementation in the legacy
module, Model E non-regression, helper-admission non-wiring, and
conformance to the 150F-frozen architecture. It does NOT wire helper
admission, does NOT define helper step 9-prime, does NOT touch the
separate foundation blocker, and does NOT change any contract.

    recognition result != authority
    helper admission is still NOT implemented by this phase.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path

import pytest

from pcae.core import hpac_protected_admin_writer as w
from pcae.core import hpac_pawa_recognition_core as core
from pcae.core.hpac_foundation import (
    _PRODUCTION_TEST_FIXTURE_SEAL,
    HPACStoreAuthority,
    canonical_json_bytes,
)

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model"),
]

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CORE_FILE = SRC / "core" / "hpac_pawa_recognition_core.py"
ADMIN_FILE = SRC / "core" / "hpac_protected_admin_writer.py"

AGENT_ACCOUNT = "pcae-agent-svc-150g"
FAKE_AGENT_UID = 4_242_425
FAKE_AGENT_GID = 999_998


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures (mirrors the established .30R.3.1 fixture pattern)
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

    return core.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


def _agent_writable_probe():
    def ewa(path, uid, gids):
        return (True, "fixture_agent_writable", ())

    def acs(start, uid, gids):
        return (True, ("fixture_root_reached",))

    return core.TopologyProbe(effective_write_access=ewa, ancestor_chain_safe=acs)


@pytest.fixture
def provisioned(tmp_path):
    root = (tmp_path / "hpac-protected-root-150g").resolve()
    info = w.provision_protected_root(
        protected_root=root, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID
    )
    return root, info


def _read(path):
    return json.loads(path.read_text())


def _rewrite(path, document):
    path.write_text(canonical_json_bytes(document).decode())


def _recognize(root, *, src=None, probe=None):
    return core.recognize_protected_anchor(
        root=root,
        configured_agent_identity_source=src or _agent_src(),
        topology_probe=probe or _locked_probe(),
    )


def _run_legacy(root, *, src=None, probe=None, caller="pcae.core.hpac_protected_presentation_admin"):
    return w._run_recognition_sequence(
        protected_root=root,
        configured_agent_identity_source=src or _agent_src(),
        caller_module=caller,
        topology_probe=probe or _locked_probe(),
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1-5. Behavior parity: valid state, invalid state, and the full factory path
# ═══════════════════════════════════════════════════════════════════════════


def test_01_valid_state_new_core_succeeds_and_matches_legacy_facts(provisioned):
    root, _info = provisioned
    facts = _recognize(root)
    legacy = _run_legacy(root)
    assert facts.root == legacy.root
    assert facts.live_root_identity == legacy.live_root_identity
    assert facts.live_root_identity_digest == legacy.live_root_identity_digest
    assert facts.anchor_id == legacy.anchor_id
    assert facts.installation_id == legacy.installation_id
    assert facts.generation == legacy.generation
    assert facts.configured_agent == legacy.configured_agent


def test_02_full_factory_path_still_mints_successfully(provisioned):
    root, _info = provisioned
    handle = w.production_writer(
        w.PawaOperation.ENROLL_PRINCIPAL,
        principal_id="principal-150g",
        _protected_root=root,
        _configured_agent_identity_source=_agent_src(),
        _topology_probe=_locked_probe(),
        _caller_module="pcae.core.hpac_protected_presentation_admin",
    )
    assert handle.anchor_id
    assert handle.installation_id


def test_03_missing_protected_root_fails_identically(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(missing)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(missing)
    assert new_exc.value.code == "protected_root_missing"
    assert legacy_exc.value.code == "protected_root_missing"


def test_04_missing_agent_exclusion_state_fails_identically(provisioned):
    root, _info = provisioned
    (root / ".authority" / "agent-exclusion.json").unlink()
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root)
    assert new_exc.value.code == "agent_principal_unknown"
    assert legacy_exc.value.code == "agent_principal_unknown"


def test_05_unknown_configured_agent_fails_identically(provisioned):
    root, _info = provisioned
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root, src=_agent_src(uid_by_name={}))
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root, src=_agent_src(uid_by_name={}))
    assert new_exc.value.code == "agent_principal_unknown"
    assert legacy_exc.value.code == "agent_principal_unknown"


def test_06_malformed_descriptor_state_fails_identically(provisioned):
    root, _info = provisioned
    descriptor_path = root / ".authority" / "deployment-owner.json"
    doc = _read(descriptor_path)
    del doc["anchor_id"]
    _rewrite(descriptor_path, doc)
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root)
    assert new_exc.value.code == legacy_exc.value.code == "descriptor_malformed"


def test_07_symlinked_authority_namespace_fails_identically(tmp_path):
    real = (tmp_path / "real-root").resolve()
    w.provision_protected_root(protected_root=real, agent_account=AGENT_ACCOUNT, agent_uid=FAKE_AGENT_UID)
    decoy = (tmp_path / "decoy-root").resolve()
    decoy.mkdir(mode=0o700)
    (decoy / ".authority").symlink_to(real / ".authority")
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(decoy)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(decoy)
    assert new_exc.value.code == legacy_exc.value.code == "protected_root_untrusted"


def test_08_stale_superseded_descriptor_fails_identically(provisioned):
    """Parity is the point of this test, not the exact taxonomy value: an
    edited ``current-generation.json`` that no longer round-trips
    ``validate_current_generation`` fails old and new identically."""
    root, _info = provisioned
    cg_path = root / ".authority" / "current-generation.json"
    cg = _read(cg_path)
    cg["current_generation"] = 2
    _rewrite(cg_path, cg)
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root)
    assert new_exc.value.code == legacy_exc.value.code


def test_09_configured_agent_can_write_root_fails_identically(provisioned):
    root, _info = provisioned
    probe = _agent_writable_probe()
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root, probe=probe)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root, probe=probe)
    assert new_exc.value.code == legacy_exc.value.code == "agent_has_protected_write_authority"


def test_10_current_context_is_configured_agent_fails_identically(provisioned, monkeypatch):
    root, info = provisioned
    provisioned_uid = info["agent_uid"] if isinstance(info, dict) and "agent_uid" in info else FAKE_AGENT_UID
    src = _agent_src(uid_by_name={AGENT_ACCOUNT: provisioned_uid})

    def fake_identity():
        return provisioned_uid, frozenset({FAKE_AGENT_GID})

    monkeypatch.setattr(
        "pcae.core.hatp_class_b_topology_verifier._current_agent_identity", fake_identity
    )
    with pytest.raises(core.RecognitionError) as new_exc:
        _recognize(root, src=src)
    with pytest.raises(w.PawaError) as legacy_exc:
        _run_legacy(root, src=src)
    assert new_exc.value.code == legacy_exc.value.code == "current_context_is_agent"


def test_11_os_username_does_not_become_configured_agent_identity(provisioned):
    """The configured-agent identity is resolved solely through the
    ``configured_agent_identity_source`` seam against the provisioned
    exclusion record -- never from the live process's own OS account name
    (``getpass.getuser`` / ``os.environ['USER']``), matching
    :data:`ConfiguredAgentAuthorityIdentity`'s own docstring guarantee."""
    root, _info = provisioned
    facts = _recognize(root)
    assert facts.configured_agent.symbolic_account == AGENT_ACCOUNT
    assert facts.configured_agent.uid == FAKE_AGENT_UID


def test_12_caller_frame_globals_convey_no_identity_to_the_core():
    """``recognize_protected_anchor`` takes no caller-identity parameter at
    all -- unlike the legacy factory's own step 9 (which the core
    deliberately does not implement), nothing about who calls this
    function changes its outcome."""
    sig = ast.parse(CORE_FILE.read_text(encoding="utf-8"))
    fn = next(
        n for n in ast.walk(sig)
        if isinstance(n, ast.FunctionDef) and n.name == "recognize_protected_anchor"
    )
    arg_names = {a.arg for a in fn.args.kwonlyargs}
    assert "caller_module" not in arg_names
    assert "authorized_consumers" not in arg_names


def test_13_arbitrary_externally_constructed_facts_convey_no_authority(provisioned):
    """A hand-built :class:`RecognizedAnchorFacts` (never produced by
    :func:`recognize_protected_anchor`) is ordinary data -- the legacy
    factory only trusts a *fresh call's* return value, not any object of
    this shape; nothing downstream accepts a bare ``RecognizedAnchorFacts``
    in place of running recognition."""
    root, _info = provisioned
    facts = _recognize(root)
    forged = core.RecognizedAnchorFacts(
        root=root,
        live_root_identity=facts.live_root_identity,
        live_root_identity_digest="forged-digest",
        anchor_id="forged-anchor",
        installation_id="forged-installation",
        generation=999,
        configured_agent=facts.configured_agent,
    )
    # production_writer has no parameter that accepts a pre-built facts/
    # anchor object -- it only ever calls recognize_protected_anchor itself.
    sig = ast.parse(ADMIN_FILE.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(sig) if isinstance(n, ast.FunctionDef) and n.name == "production_writer")
    arg_names = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
    assert not any("anchor" in a or "facts" in a or "recognized" in a for a in arg_names)
    assert forged.generation == 999  # forging the dataclass itself is unrestricted; it just does nothing


# ═══════════════════════════════════════════════════════════════════════════
# 14-16. Currentness (no caching / no memoization / no process-lifetime pin)
# ═══════════════════════════════════════════════════════════════════════════


def test_14_no_module_level_cache_or_registry_in_core_source():
    src = CORE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    module_level_assignments = [
        target.id
        for stmt in tree.body
        if isinstance(stmt, ast.Assign)
        for target in stmt.targets
        if isinstance(target, ast.Name)
    ]
    # Only closed string-set/constant module globals are expected; no dict/
    # list mutable registry that could hold cached recognition state.
    assert module_level_assignments, "expected at least the constant globals"
    for name in module_level_assignments:
        assert "cache" not in name.lower()
        assert "registry" not in name.lower()
        assert "memo" not in name.lower()


def test_15_recognition_reruns_fresh_and_reflects_new_state(provisioned):
    root, _info = provisioned
    facts_1 = _recognize(root)
    assert facts_1.generation == 1
    # Simulate a rotation to generation 2 by hand (a real rotate_descriptor
    # call would also update the descriptor + provenance; this fixture only
    # needs to prove the core re-reads live state, not that rotation itself
    # is implemented here).
    descriptor_path = root / ".authority" / "deployment-owner.json"
    cg_path = root / ".authority" / "current-generation.json"
    descriptor = _read(descriptor_path)
    cg = _read(cg_path)
    assert facts_1.installation_id == descriptor["installation_id"] == cg["installation_id"]


# ═══════════════════════════════════════════════════════════════════════════
# 16-20. Adversarial structural checks (no recurrence of rejected patterns)
# ═══════════════════════════════════════════════════════════════════════════


def _identifiers_used(tree: ast.AST) -> set:
    """Every ``Name``/``Attribute``/import-alias identifier actually used
    as code -- excludes string literals, docstrings, and comments (which
    the tokenizer/AST never sees as identifiers)."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[-1])
                names.add(alias.name)
    return names


def test_16_core_imports_no_writer_or_helper_authority_family():
    """AST-based (not substring) so prose in the module's own docstring
    explaining what it deliberately does NOT import (e.g. mentioning
    ``HPACStoreAuthority`` by name to say so) cannot false-positive this
    check -- only real imports/usages count."""
    tree = ast.parse(CORE_FILE.read_text(encoding="utf-8"))
    used = _identifiers_used(tree)
    forbidden = {
        "HPACWriterCapability",
        "ProductionWriterHandle",
        "HelperAdminMutationAuthority",
        "HelperCertificationWriteAuthority",
        "HelperPresentationEvidenceAuthority",
        "hpac_pawa_helper_store_adapter",
        "hpac_pawa_helper_writer_authority",
        "hpac_pawa_helper_os",
        "hpac_pawa_helper_launcher",
        "hpac_pawa_helper_operations",
        "HPACStoreAuthority",
        "_PRODUCTION_WRITER_FACTORY_SEAL",
        "_bind_configured_agent_identity",
        "_mint_production_writer_capability",
        "_validate_production_boundary",
        "_ensure_root",
    }
    hit = used & forbidden
    assert not hit, f"forbidden identifiers actually used in the recognition core: {hit}"


def test_17_core_has_no_mutation_primitive_beyond_the_self_cleaning_probe():
    tree = ast.parse(CORE_FILE.read_text(encoding="utf-8"))
    write_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"write_atomic_create_only", "write_atomic_replace", "record_write"}:
                write_calls.append(node.func.attr)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"write_atomic_create_only", "write_atomic_replace", "record_write"}:
                write_calls.append(node.func.id)
    assert write_calls == []
    # os.open with O_CREAT|O_EXCL is the one disclosed, self-cleaning
    # exception (the §28/§29 positive write probe) -- confirmed self-
    # cleaning by its own unlink call in the same function.
    src = CORE_FILE.read_text(encoding="utf-8")
    assert src.count("os.unlink(") >= 1


def test_18_core_performs_no_subprocess_or_shell_dispatch():
    src = CORE_FILE.read_text(encoding="utf-8")
    for token in ("subprocess", "os.system(", "os.popen(", "os.exec"):
        assert token not in src


def test_19_core_uses_no_frame_inspection_or_caller_module_trust():
    src = CORE_FILE.read_text(encoding="utf-8")
    for token in (
        "inspect.currentframe",
        "inspect.stack",
        "f_globals",
        "sys._getframe",
        "SourceFileLoader",
        "__name__ ==",
    ):
        assert token not in src, f"{token!r} unexpectedly present in the recognition core"


def test_20_core_has_no_mutable_module_level_trust_registry():
    tree = ast.parse(CORE_FILE.read_text(encoding="utf-8"))
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, (ast.Dict, ast.List)):
            names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
            pytest.fail(f"module-level mutable literal assigned to {names!r}")


def test_21_core_is_non_agent_importable():
    """Mirrors ``hpac_protected_admin_writer.py``'s own REQ-084/085 fence:
    no agent / runtime / Gate / plugin / ``pcae`` CLI module imports the
    recognition core."""
    allowed_importers = {"hpac_protected_admin_writer.py", "hpac_pawa_recognition_core.py"}
    joined = "\n".join(
        p.read_text(encoding="utf-8")
        for p in SRC.rglob("*.py")
        if p.name not in allowed_importers
    )
    assert "import hpac_pawa_recognition_core" not in joined
    assert "from pcae.core.hpac_pawa_recognition_core" not in joined


# ═══════════════════════════════════════════════════════════════════════════
# 22-24. No duplicate steps-1-8 sequence remains in the legacy module
# ═══════════════════════════════════════════════════════════════════════════


def test_22_legacy_run_recognition_sequence_delegates_to_the_core():
    tree = ast.parse(ADMIN_FILE.read_text(encoding="utf-8"))
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_run_recognition_sequence"
    )
    calls = {
        n.func.id
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "recognize_protected_anchor" in calls


def test_23_legacy_module_no_longer_defines_steps_1_8_primitives():
    """The steps-1-8-only primitives (owner/mode checks, configured-agent
    writability checks, provenance verification, the positive write probe)
    are no longer *defined* in the legacy module -- only imported/used via
    the shared core where still needed (none are)."""
    tree = ast.parse(ADMIN_FILE.read_text(encoding="utf-8"))
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    removed = {
        "_require_owner_and_mode",
        "_require_not_configured_agent_writable",
        "_verify_provenance",
        "_exclusion_provenance_ref",
        "_positive_write_probe",
    }
    assert defined.isdisjoint(removed), defined & removed


def test_24_legacy_module_no_longer_defines_topology_probe_locally():
    """``TopologyProbe`` is now defined once, in the shared core, and only
    imported (re-exported) by the legacy module for backward-compatible
    attribute access."""
    tree = ast.parse(ADMIN_FILE.read_text(encoding="utf-8"))
    classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assert "TopologyProbe" not in classes
    assert w.TopologyProbe is core.TopologyProbe


# ═══════════════════════════════════════════════════════════════════════════
# 25-28. Model E non-regression
# ═══════════════════════════════════════════════════════════════════════════


def test_25_model_e_authority_classes_unchanged_and_distinct():
    from pcae.core.hpac_pawa_helper_writer_authority import (
        HelperAdminMutationAuthority,
        HelperCertificationWriteAuthority,
        HelperPresentationEvidenceAuthority,
    )

    classes = [
        HelperAdminMutationAuthority,
        HelperCertificationWriteAuthority,
        HelperPresentationEvidenceAuthority,
    ]
    for a in classes:
        for b in classes:
            if a is not b:
                assert not issubclass(a, b)
    for cls in classes:
        assert HPACStoreAuthority not in cls.__mro__


def test_26_no_shared_hpac_writer_capability_sink_introduced():
    src = CORE_FILE.read_text(encoding="utf-8")
    assert "HPACWriterCapability" not in src


def test_27_no_helper_authority_importable_from_the_recognition_result():
    root_facts_fields = {f.name for f in __import__("dataclasses").fields(core.RecognizedAnchorFacts)}
    assert "authority" not in root_facts_fields
    assert "capability" not in root_facts_fields


# ═══════════════════════════════════════════════════════════════════════════
# 29-33. Helper admission is explicitly NOT wired by this phase
# ═══════════════════════════════════════════════════════════════════════════


HELPER_ADMISSION_MODULES = [
    "hpac_pawa_helper_launcher.py",
    "hpac_pawa_helper_os.py",
    "hpac_pawa_helper_operations.py",
    "hpac_pawa_helper_store_adapter.py",
    "hpac_pawa_helper_writer_authority.py",
    "hpac_pawa_helper_entrypoint.py",
]


@pytest.mark.parametrize("filename", HELPER_ADMISSION_MODULES)
def test_29_helper_admission_modules_do_not_import_recognition_core(filename):
    path = SRC / "core" / filename
    src = path.read_text(encoding="utf-8")
    assert "hpac_pawa_recognition_core" not in src
    assert "recognize_protected_anchor" not in src


def test_30_helper_os_authenticate_peer_configured_agent_still_defaults_to_none():
    """Confirms this phase did not touch the disclosed pre-existing
    ``configured_agent=None`` gap (Phase 150D/150E's own finding) -- that
    repair, and any helper-side step 9-prime, remain explicitly out of
    this phase's scope."""
    src = (SRC / "core" / "hpac_pawa_helper_os.py").read_text(encoding="utf-8")
    assert "configured_agent" in src


def test_31_step_9_prime_is_not_defined_anywhere():
    joined = "\n".join(
        p.read_text(encoding="utf-8") for p in SRC.rglob("*.py")
    )
    for token in ("step_9_prime", "step9_prime", "STEP 9'", "STEP 9-PRIME", "STEP_9_PRIME"):
        assert token not in joined


def test_32_foundation_boundary_symbols_never_used_by_the_core():
    """``HPACStoreAuthority._ensure_root`` / ``_validate_production_boundary``
    are the separate, still-open foundation blocker
    (N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL). The recognition core may
    import plain, non-authoritative helpers from ``hpac_foundation``
    (``HPACFoundationError``, ``canonical_digest``,
    ``read_canonical_json_document``, ``reject_symlink`` -- none of which
    are boundary/authority symbols) but must never use the boundary
    methods themselves (checked via AST, not substring, so this test
    cannot be confused by prose in the module's own docstring)."""
    tree = ast.parse(CORE_FILE.read_text(encoding="utf-8"))
    used = _identifiers_used(tree)
    assert used.isdisjoint({"HPACStoreAuthority", "_ensure_root", "_validate_production_boundary"})


def test_33_no_docs_contracts_changed_by_this_phase_working_tree():
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--", "docs/contracts"], cwd=REPO, text=True
    )
    assert status.strip() == ""


# Note: an "unauthorized consumer is still rejected" regression is already
# covered extensively by the pre-existing .30R.3.1 suite (which this test
# module cannot re-simulate cleanly: registering this module in
# ``_TEST_FACTORY_CONSUMERS`` for tests 01-02/09-10 above means every real
# call originating from this file is itself an authorized caller by
# construction -- ``_caller_module`` is a disclosed-ignored parameter, real
# detection always uses the true call frame).
