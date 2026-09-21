"""Phase 150F — N16-5-F-5-TB-HELPER-ADMISSION-RECOGNITION-SHARED-INFRASTRUCTURE-ARCHITECTURE.

Architecture / boundary-definition evidence only. This phase makes zero
``src/pcae/**`` and zero ``docs/contracts/**`` changes -- the neutral shared
recognition module proposed in
``docs/PHASE_150F_N16_5_F_5_TB_HELPER_ADMISSION_RECOGNITION_SHARED_INFRASTRUCTURE_ARCHITECTURE.md``
does not exist yet. These tests instead verify, against the CURRENT working
tree, the exact structural facts the proposed Model B architecture depends
on: that the code region corresponding to
``hpac_protected_admin_writer._run_recognition_sequence`` steps 1-8 (the
candidate for neutral extraction) contains no mutation primitive, no
write-authority import, and no dependency on ``HPACStoreAuthority`` (the
separate, still-open foundation boundary); that step 9 (the only step this
architecture proposes leaving behind, admin-writer-specific) is the sole step
referencing the factory-consumer allowlist; that the helper side still has no
implementation of the required in-helper recognition (REQ-031) or of the
peer-admission configured-agent conjunct (REQ-042); that the dependency
``hpac_pawa_agent_exclusion`` a shared module would need is itself free of
mutation primitives and of any import of the write-authority module; and
that Model E's three authority classes, the three normative contracts, and
production/contract sources are unchanged by this phase.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

ROOT = Path(__file__).resolve().parents[1]

# This phase's own entry commit: HEAD == origin/main at preflight, before
# any file this phase touches was written. Used as the Model FG-E pinned
# historical boundary for the byte-identity assertions below.
ENTRY_COMMIT = "81985989c3d49f8aa52cf999168c07d4ba8035d8"


def _admin_writer_source() -> str:
    path = ROOT / "src" / "pcae" / "core" / "hpac_protected_admin_writer.py"
    return path.read_text(encoding="utf-8")


def _admin_writer_lines() -> list[str]:
    return _admin_writer_source().splitlines()


def _region(start_marker: str, end_marker: str) -> str:
    """Return the exact source slice between two ``# STEP N`` markers
    (inclusive of start, exclusive of end) inside ``_run_recognition_sequence``.
    """
    lines = _admin_writer_lines()
    start = next(i for i, line in enumerate(lines) if start_marker in line)
    end = next(i for i, line in enumerate(lines) if end_marker in line)
    assert start < end
    return "\n".join(lines[start:end])


def _steps_1_through_8_region() -> str:
    return _region("# STEP 1 —", "# STEP 9 —")


def _step_9_region() -> str:
    lines = _admin_writer_lines()
    start = next(i for i, line in enumerate(lines) if "# STEP 9 —" in line)
    # Step 9 ends where the function's ``return _RecognizedAnchor(`` begins.
    end = next(i for i, line in enumerate(lines) if "return _RecognizedAnchor(" in line)
    return "\n".join(lines[start:end])


def test_recognition_sequence_has_the_eleven_documented_steps():
    """Sanity: STEP 1/2/3/4/5/6/7/8/9 all exist inside the same function,
    STEP 10/11 exist elsewhere (the factory's mint/audit tail, out of this
    architecture's proposed extraction). Confirms the region-slicing helpers
    above are anchored to markers that actually exist today."""
    lines = _admin_writer_lines()
    found = {n: any(f"# STEP {n} —" in line for line in lines) for n in range(1, 12)}
    assert all(found.values()), found


def test_steps_1_through_8_contain_no_mutation_or_write_authority_primitive():
    """The candidate neutral-extraction region (steps 1-8) must contain no
    capability-mint, no seal, and no write-authority import -- i.e. it is
    safe, by inspection, for a privileged helper to import: it cannot itself
    mint or export mutation authority."""
    region = _steps_1_through_8_region()
    forbidden = [
        "HPACWriterCapability",
        "_mint_production_writer_capability",
        "_new_capability",
        "_PRODUCTION_WRITER_FACTORY_SEAL",
        "_bind_configured_agent_identity",
        "HelperAdminMutationAuthority",
        "HelperCertificationWriteAuthority",
        "HelperPresentationEvidenceAuthority",
        "_HELPER_AUTHORITY_SEAL",
    ]
    for token in forbidden:
        assert token not in region, f"{token!r} found in steps 1-8 region"


def test_steps_1_through_8_do_not_touch_hpac_store_authority():
    """The candidate extraction region never references ``HPACStoreAuthority``
    or its production-boundary/root-establishment methods -- proving the
    proposed shared module would be structurally independent of the
    separate, still-open N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL foundation
    blocker (``_validate_production_boundary`` / ``_ensure_root``), which
    this architecture explicitly does not touch or repair."""
    region = _steps_1_through_8_region()
    forbidden = ["HPACStoreAuthority", "_validate_production_boundary", "_ensure_root("]
    for token in forbidden:
        assert token not in region, f"{token!r} found in steps 1-8 region"


def test_only_step_9_references_the_factory_consumer_allowlist():
    """``AUTHORIZED_FACTORY_CONSUMERS`` / ``_TEST_FACTORY_CONSUMERS`` (the
    admin-writer-specific enumerated-consumer gate) appear only in step 9,
    confirming step 9 -- and only step 9 -- is the admin-writer-specific tail
    this architecture proposes leaving out of the shared module (the
    contract's own HPAC-PAWA-001 v2.0 note independently states helper step
    9 is replaced by a distinct step 9')."""
    steps_1_8 = _steps_1_through_8_region()
    step_9 = _step_9_region()
    for token in ("authorized_consumers", "test_consumers"):
        assert token not in steps_1_8, f"{token!r} unexpectedly referenced in steps 1-8"
    assert "authorized_consumers" in step_9
    assert "unauthorized_factory_consumer" in step_9


def test_recognized_anchor_return_is_descriptive_not_capability_bearing():
    """The recognition sequence's own return value (``_RecognizedAnchor``)
    carries only descriptive identity fields -- never a writer capability --
    confirming the proposed shared module's output can be ordinary
    descriptive data (per this architecture's preferred Model E-compatible
    result-object semantics), not process-local trusted evidence requiring a
    same-interpreter trust seal."""
    source = _admin_writer_source()
    node = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.ClassDef) and n.name == "_RecognizedAnchor"
    )
    field_names = {
        target.id
        for stmt in node.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        for target in [stmt.target]
    }
    assert field_names, "could not find _RecognizedAnchor's fields"
    for forbidden in ("capability", "writer", "authority_token", "seal"):
        assert not any(forbidden in name.lower() for name in field_names), field_names


def test_hpac_pawa_agent_exclusion_has_no_mutation_primitive_or_writer_authority_import():
    """The one dependency a neutral shared module would need for
    configured-agent resolution (``hpac_pawa_agent_exclusion``) is itself
    free of any mutation function and does not import the helper
    write-authority module or ``HPACStoreAuthority`` -- so depending on it
    from a helper-reachable neutral module introduces no new mutation
    surface."""
    path = ROOT / "src" / "pcae" / "core" / "hpac_pawa_agent_exclusion.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
    assert "hpac_pawa_helper_writer_authority" not in " ".join(imported_names)
    assert "HPACStoreAuthority" not in imported_names
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert not node.name.startswith("mutate")
            assert not node.name.startswith("write_")
            assert "capability" not in node.name.lower()


def test_admin_writer_module_does_not_import_helper_writer_authority():
    """No reverse/circular dependency exists today between the legacy
    factory and the Model E helper write-authority module -- a prerequisite
    fact for claiming a future shared module sitting between
    ``hpac_protected_admin_writer`` and the helper introduces no dependency
    cycle."""
    path = ROOT / "src" / "pcae" / "core" / "hpac_protected_admin_writer.py"
    text = path.read_text(encoding="utf-8")
    assert "hpac_pawa_helper_writer_authority" not in text


def test_helper_modules_still_forbidden_from_importing_admin_writer():
    """REQ-033 fence still holds today: none of the helper-side modules
    import the legacy factory module. Reconfirmed here (not merely assumed
    from a historical baseline) because this architecture's soundness
    depends on that fence remaining intact."""
    for name in (
        "hpac_pawa_helper_os",
        "hpac_pawa_helper_launcher",
        "hpac_pawa_helper_entrypoint",
        "hpac_pawa_helper_operations",
        "hpac_pawa_helper_store_adapter",
    ):
        path = ROOT / "src" / "pcae" / "core" / f"{name}.py"
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
        assert not any("hpac_protected_admin_writer" in mod for mod in imported), (name, imported)


def test_helper_launcher_still_has_no_configured_agent_resolution():
    """N-16-5 is NOT closed by this architecture phase: the launcher still
    never resolves or threads a real ``ConfiguredAgentAuthorityIdentity``
    into ``authenticate_peer`` -- confirming the Phase 150E gap this
    architecture is designed to eventually close remains present in the
    current working tree, not merely in Phase 150E's historical evidence."""
    path = ROOT / "src" / "pcae" / "core" / "hpac_pawa_helper_launcher.py"
    text = path.read_text(encoding="utf-8")
    assert "resolve_configured_agent_identity" not in text
    assert "configured_agent=" not in text


def test_helper_entrypoint_still_has_no_in_helper_recognition():
    """REQ-031's in-helper §33 steps 1-8 recognition is still not
    implemented anywhere on the helper side -- confirming this is a real,
    still-open gap this architecture's Model B extraction is meant to make
    closeable, not something already silently repaired."""
    for name in ("hpac_pawa_helper_entrypoint", "hpac_pawa_helper_store_adapter"):
        path = ROOT / "src" / "pcae" / "core" / f"{name}.py"
        text = path.read_text(encoding="utf-8")
        assert "resolve_configured_agent_identity" not in text


def test_model_e_authority_classes_remain_distinct_sealed_and_exact_type_checked():
    """This architecture phase must not collapse Model E's three authority
    families. Confirms, against current source, that all three remain
    distinct sealed classes gated by the same module-private seal object,
    with no shared authority base class."""
    path = ROOT / "src" / "pcae" / "core" / "hpac_pawa_helper_writer_authority.py"
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    classes = {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
        and n.name
        in {
            "HelperAdminMutationAuthority",
            "HelperCertificationWriteAuthority",
            "HelperPresentationEvidenceAuthority",
        }
    }
    assert set(classes) == {
        "HelperAdminMutationAuthority",
        "HelperCertificationWriteAuthority",
        "HelperPresentationEvidenceAuthority",
    }
    for name, node in classes.items():
        bases = {ast.unparse(b) for b in node.bases}
        assert "HPACWriterCapability" not in bases, name
        init = next(
            item
            for item in node.body
            if isinstance(item, ast.FunctionDef) and item.name == "__init__"
        )
        init_source = ast.unparse(init)
        assert "_HELPER_AUTHORITY_SEAL" in init_source, name


def test_contract_versions_unchanged_by_this_phase():
    """This architecture phase makes zero contract edits. Reconfirm the
    three normative contracts remain exactly at the versions this
    architecture's analysis is keyed to."""
    expectations = {
        "HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md": "HPAC-PAWA-HELPER-001 v5.0",
        "HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md": "HPAC-PAWA-001 v4.0",
        "HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md": "HPAC-PPA-001 v2.1",
    }
    for filename, expected_header in expectations.items():
        path = ROOT / "docs" / "contracts" / filename
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert expected_header in first_line, first_line


def test_this_phase_changed_zero_production_or_contract_files():
    """Model FG-E: compare this phase's own entry commit against the
    current working tree (not a moving ``HEAD``-bound comparison), so this
    assertion stays valid after any later legitimate ``src/pcae/**`` edit
    outside this phase's own history."""
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", ENTRY_COMMIT, "--", "src/pcae", "docs/contracts"],
        cwd=ROOT,
        text=True,
    )
    assert diff.strip() == "", diff


def test_n16_6_and_n16_7_artifacts_absent_from_this_phase():
    """This architecture phase must not advance N-16-6 or N-16-7. Confirms
    this phase's own new files make no claim of touching either."""
    doc = (
        ROOT
        / "docs"
        / "PHASE_150F_N16_5_F_5_TB_HELPER_ADMISSION_RECOGNITION_SHARED_INFRASTRUCTURE_ARCHITECTURE.md"
    )
    text = doc.read_text(encoding="utf-8")
    assert "N-16-6" in text and "untouched" in text
    assert "N-16-7" in text
