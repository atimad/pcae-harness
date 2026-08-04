"""Phase 149L -- Rollback Approval Evidence Implementation: import-boundary
and RAE-001 traceability sanity tests (RAE-REQ-001, RAE-REQ-037,
RAE-REQ-039, RAE-REQ-066; 149K plan Sec.6, Sec.49-51, Sec.78-79, Sec.87).

Mechanically enforces -- not merely by convention -- that
`rollback_approval_evidence.py` never imports the Permission Broker, the
Wave-1 mutation-permission adapter, `pcae.core.agent`, or the Typed
Authority Model authority family, and that no "latest"/mtime-based
lookup selects which `evidence_id` to resolve.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "pcae" / "core" / "rollback_approval_evidence.py"
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "pcae.core.permission_broker_foundation",
    "pcae.core.mutation_permission",
    "pcae.core.agent",
    "pcae.cltr.authority",
    "pcae.cltr_cutover",
)


def _imported_module_names() -> list[str]:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_module_exists_and_parses():
    assert MODULE_PATH.exists()
    ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def test_no_import_of_permission_broker_foundation():
    imports = _imported_module_names()
    assert not any(name.startswith("pcae.core.permission_broker_foundation") for name in imports)


def test_no_import_of_mutation_permission():
    imports = _imported_module_names()
    assert not any(name.startswith("pcae.core.mutation_permission") for name in imports)


def test_no_import_of_agent_module():
    imports = _imported_module_names()
    assert not any(name == "pcae.core.agent" or name.startswith("pcae.core.agent.") for name in imports)


def test_no_import_of_typed_authority_model_or_cltr():
    imports = _imported_module_names()
    assert not any(name.startswith("pcae.cltr") for name in imports)


def test_no_forbidden_import_prefix_present_at_all():
    imports = _imported_module_names()
    for forbidden in _FORBIDDEN_IMPORT_PREFIXES:
        assert not any(name == forbidden or name.startswith(forbidden + ".") for name in imports), forbidden


def test_module_never_constructs_a_permission_broker_request_or_decision():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "PermissionBrokerRequest(" not in source
    assert "PermissionBrokerDecision(" not in source


# ─────────────────────────────────────────────────────────────────────────
# No "latest"/mtime-based evidence_id selection (RAE-REQ-041, item 75)
# ─────────────────────────────────────────────────────────────────────────


def test_no_latest_or_mtime_lookup_pattern_in_source():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "st_mtime" not in source
    assert "getmtime" not in source
    forbidden_patterns = [
        r"sorted\([^)]*\)\[-1\]",
        r"max\([^)]*timestamp",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, source), pattern


def test_resolve_and_derive_require_an_explicit_evidence_id_parameter():
    import inspect

    from pcae.core import rollback_approval_evidence as rae

    resolve_params = list(inspect.signature(rae.resolve_rollback_approval_evidence).parameters)
    derive_params = list(inspect.signature(rae.derive_rollback_approval_present).parameters)
    assert "evidence_id" in resolve_params
    assert "evidence_id" in derive_params


def test_derive_rollback_approval_present_has_no_caller_override_parameter():
    import inspect

    from pcae.core import rollback_approval_evidence as rae

    params = set(inspect.signature(rae.derive_rollback_approval_present).parameters)
    assert "approval_present" not in params
    assert "force" not in params
    assert "override" not in params


# ─────────────────────────────────────────────────────────────────────────
# TAM wall: dedicated record_type, no human_authorization reuse (item 45,
# RAE-REQ-016)
# ─────────────────────────────────────────────────────────────────────────


def test_binding_record_type_is_dedicated_not_human_authorization():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"human_authorization"' not in source
    assert "rollback_approval_binding" in source


def test_schema_files_live_outside_cltr_cutover_namespace():
    repo_root = MODULE_PATH.parents[3]
    schema_dir = repo_root / "src" / "pcae" / "schema_resources" / "rollback_approval"
    assert schema_dir.is_dir()
    binding_schema = schema_dir / "records" / "rollback_approval_binding.schema.json"
    assert binding_schema.exists()
    forbidden_dir = repo_root / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records" / "rollback_approval_binding.schema.json"
    assert not forbidden_dir.exists()


# ─────────────────────────────────────────────────────────────────────────
# 81-requirement traceability sanity (item 87): every RAE-REQ anchor still
# extracts cleanly from the frozen contract, matching 149J/149K's own
# independently-verified count. This does not re-verify contract content
# (149J's own suite does that); it only guards against silent contract
# drift during this implementation phase.
# ─────────────────────────────────────────────────────────────────────────


def test_contract_still_has_exactly_81_sequential_gap_free_requirements():
    repo_root = MODULE_PATH.parents[3]
    contract_path = repo_root / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"
    text = contract_path.read_text(encoding="utf-8")
    numbers = sorted({int(match) for match in re.findall(r"RAE-REQ-(\d+)", text)})
    assert numbers == list(range(1, 82))
