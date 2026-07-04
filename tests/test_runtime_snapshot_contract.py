"""Tests for Phase 112F — Runtime Snapshot Contract Freeze.

This is a pure documentation-verification suite. Phase 112F is a
contract/freeze phase: it freezes the Runtime Snapshot schema, JSON
compatibility rules, versioning contract, human-output compatibility
rules, future-consumer model, security rules, and current capability
limits -- without implementing any new runtime behavior, execution
capability, or schema/version field. There is no new runtime code to
unit-test -- these tests verify the documents exist, contain the
required frozen content, make no implementation claims, and that the
frozen schema matches the real, already-shipped 112E implementation
(cross-checked directly, not merely asserted).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.core.runtime_snapshot import RuntimeSnapshot

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_SNAPSHOT_CONTRACT.md"
PHASE_DOC = REPO_ROOT / "docs" / "PHASE_112_RUNTIME_SNAPSHOT_CONTRACT_FREEZE.md"
ARCHITECTURE_DOC = REPO_ROOT / "docs" / "PCAE_RUNTIME_SNAPSHOT.md"


@pytest.fixture(scope="module")
def contract_text() -> str:
    return CONTRACT_DOC.read_text()


@pytest.fixture(scope="module")
def phase_doc_text() -> str:
    return PHASE_DOC.read_text()


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# ═══════════════════════════════════════════════════════════════════════
# Documents exist
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_snapshot_contract_document_exists():
    assert CONTRACT_DOC.exists()
    assert CONTRACT_DOC.stat().st_size > 0


def test_phase_112f_document_exists():
    assert PHASE_DOC.exists()
    assert PHASE_DOC.stat().st_size > 0


def test_architecture_doc_still_present_unmodified_reference():
    assert ARCHITECTURE_DOC.exists()


# ═══════════════════════════════════════════════════════════════════════
# New principle restated
# ═══════════════════════════════════════════════════════════════════════


def test_canonical_read_model_principle_restated(contract_text):
    text = _normalized(contract_text)
    assert "canonical read-only" in text.lower() or "canonical read model" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — canonical read-only interface
# ═══════════════════════════════════════════════════════════════════════


def test_section_1_exists(contract_text):
    assert "## 1. Runtime Snapshot as Canonical Read-Only Interface" in contract_text


CONSUMER_CLASSES = ("Humans", "CLI", "AI agents", "Telegram", "REST", "dashboard", "automation")


@pytest.mark.parametrize("consumer", CONSUMER_CLASSES)
def test_consumer_class_named(contract_text, consumer):
    assert consumer.lower() in contract_text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — required domains (cross-checked against real 112E shape)
# ═══════════════════════════════════════════════════════════════════════

REQUIRED_DOMAINS = (
    "runtime", "registry", "plugins", "capabilities",
    "health", "governance", "state", "version", "context",
)


def test_section_2_exists(contract_text):
    assert "## 2. Snapshot Schema" in contract_text


@pytest.mark.parametrize("domain", REQUIRED_DOMAINS)
def test_required_domain_documented(contract_text, domain):
    assert f"`{domain}`" in contract_text


def test_nine_domains_frozen(contract_text):
    assert len(REQUIRED_DOMAINS) == 9
    assert "Nine required top-level domains" in contract_text or "nine domains" in contract_text.lower()


def test_principles_correction_documented(contract_text):
    """This document must explicitly correct the phase brief's own
    suggested 'principles or maturity' domain against the real
    implementation -- not silently invent a tenth domain."""
    text = _normalized(contract_text)
    assert "principles" in text.lower()
    assert "runtime.principles" in text
    assert "not an independent top-level domain" in text or "not a tenth top-level domain" in text


def test_real_implementation_has_exactly_these_nine_top_level_keys(capsys):
    """Cross-checks the frozen schema against the actual, real CLI
    output -- not merely asserted in prose."""
    exit_code = main(["runtime", "inspect", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert set(data.keys()) == set(REQUIRED_DOMAINS)


def test_no_snapshot_schema_version_field_exists_in_real_output(capsys):
    """Confirms the versioning decision (objective 4: no field
    implemented this phase) matches real, current behavior."""
    exit_code = main(["runtime", "inspect", "--json"])
    output = capsys.readouterr().out
    assert exit_code == 0
    data = json.loads(output)
    assert "snapshot_schema_version" not in data


def test_runtime_snapshot_dataclass_fields_match_documented_domains():
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(RuntimeSnapshot)}
    assert field_names == set(REQUIRED_DOMAINS)


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — JSON compatibility
# ═══════════════════════════════════════════════════════════════════════


def test_section_3_exists(contract_text):
    assert "## 3. JSON Compatibility Rules" in contract_text


JSON_COMPATIBILITY_RULES = (
    "Stable top-level keys",
    "Additive-only changes",
    "requires a schema major version bump",
    "must ignore unknown keys",
    "No secrets or credentials",
    "No execution handles",
    "No mutable internal references",
)


@pytest.mark.parametrize("rule", JSON_COMPATIBILITY_RULES)
def test_json_compatibility_rule_documented(contract_text, rule):
    assert rule in contract_text


def test_json_compatibility_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "additive" in text
    assert "unknown keys" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — versioning
# ═══════════════════════════════════════════════════════════════════════


def test_section_4_exists(contract_text):
    assert "## 4. Snapshot Versioning" in contract_text


def test_versioning_decision_documented(contract_text):
    text = _normalized(contract_text)
    assert "no `snapshot_schema_version` field is added by this phase" in text.lower() or "no snapshot_schema_version field is added by this phase" in text.lower()


def test_versioning_field_contract_frozen(contract_text):
    text = contract_text
    assert "snapshot_schema_version" in text
    assert "major version" in text.lower()
    assert "Deprecation rule" in text
    assert "Migration expectation" in text


def test_versioning_summarized_in_phase_doc(phase_doc_text):
    text = phase_doc_text.lower()
    assert "snapshot_schema_version" in text
    assert "deliberate decision" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — human output compatibility
# ═══════════════════════════════════════════════════════════════════════


def test_section_5_exists(contract_text):
    assert "## 5. Human Output Compatibility" in contract_text


def test_json_is_machine_contract_documented(contract_text):
    text = _normalized(contract_text)
    assert "JSON is the machine contract" in text


def test_default_output_concise_documented(contract_text):
    text = _normalized(contract_text)
    assert "Default output remains concise" in text


def test_verbose_output_documented(contract_text):
    text = _normalized(contract_text)
    assert "Verbose output may expose more read-only metadata" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — future consumers
# ═══════════════════════════════════════════════════════════════════════


def test_section_6_exists(contract_text):
    assert "## 6. Future Consumers" in contract_text


@pytest.mark.parametrize("consumer", ("Telegram", "REST", "Web UI", "AI agents", "Advisory Runtime"))
def test_future_consumer_detailed(contract_text, consumer):
    assert consumer in contract_text


def test_advisory_runtime_named_as_read_only_consumer(contract_text):
    text = _normalized(contract_text)
    assert "read-only input" in text
    assert "never let a recommendation appear to be an authorization" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 7 — security rules
# ═══════════════════════════════════════════════════════════════════════


def test_section_7_exists(contract_text):
    assert "## 7. Security Rules" in contract_text


SECURITY_FORBIDDEN = (
    "Secrets", "Tokens", "Credentials", "Environment variables",
    "Execution handles", "Plugin instances", "Callable references",
    "Module/import paths", "Mutable internal objects", "Approval bypasses",
)


@pytest.mark.parametrize("forbidden", SECURITY_FORBIDDEN)
def test_security_forbidden_category_documented(contract_text, forbidden):
    assert forbidden in contract_text


def test_manifest_permanently_excluded_documented(contract_text):
    text = _normalized(contract_text)
    assert "permanently excluded" in text


# ═══════════════════════════════════════════════════════════════════════
# Objective 8 — current capability limits
# ═══════════════════════════════════════════════════════════════════════


def test_section_8_exists(contract_text):
    assert "## 8. Current Capability Limits" in contract_text


CAPABILITY_LIMITS = (
    "runtime state remains",
    "maximum plugin capability remains",
    "execution capability remains unavailable",
    "Advisory mode is not implemented",
    "Approval mode is not implemented",
    "Enforcement is not implemented",
)


@pytest.mark.parametrize("limit", CAPABILITY_LIMITS)
def test_capability_limit_documented(contract_text, limit):
    text = _normalized(contract_text)
    assert limit.lower() in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("doc_text_fixture", ["contract_text", "phase_doc_text"])
def test_execution_unavailable_documented(request, doc_text_fixture):
    text = _normalized(request.getfixturevalue(doc_text_fixture))
    assert "Execution unavailable" in text or "execution_unavailable" in text


def test_current_maximum_runtime_state_still_observed(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum runtime state" in normalized
        assert "Observed" in normalized


def test_current_maximum_plugin_capability_still_observe(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        normalized = _normalized(text)
        assert "Current maximum plugin capability" in normalized
        assert "`observe`" in normalized or "observe" in normalized


# ═══════════════════════════════════════════════════════════════════════
# No implementation claims
# ═══════════════════════════════════════════════════════════════════════

FORBIDDEN_IMPLEMENTATION_CLAIMS = (
    "runtime execution enabled",
    "advisory decision behavior implemented",
    "command authorization implemented",
    "command denial implemented",
    "permission broker enforcement implemented",
    "plugin loading implemented",
    "plugin instantiation implemented",
    "plugin invocation implemented",
    "dependency injection implemented",
    "shell mediation implemented",
    "backend invocation implemented",
    "adapter invocation implemented",
    "execution enablement implemented",
    "execution capability implemented",
    "audit persistence implemented",
    "rollback execution implemented",
    "emergency stop implemented",
    "telegram inbound implemented",
    "rest server implemented",
    "web ui implemented",
    "daemon implemented",
    "background worker implemented",
    "automatic apply implemented",
)


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
@pytest.mark.parametrize("claim", FORBIDDEN_IMPLEMENTATION_CLAIMS)
def test_no_forbidden_implementation_claims(doc_path, claim):
    text = doc_path.read_text().lower()
    assert claim not in text


@pytest.mark.parametrize("doc_path", [CONTRACT_DOC, PHASE_DOC])
def test_no_go_confirmations_section_present(doc_path):
    text = _normalized(doc_path.read_text())
    assert "No-Go Confirmations" in text
    assert "No runtime execution" in text


# ═══════════════════════════════════════════════════════════════════════
# Next phase recommendation exists
# ═══════════════════════════════════════════════════════════════════════


def test_recommended_next_phase_is_113a(contract_text, phase_doc_text):
    for text in (contract_text, phase_doc_text):
        assert "113A" in text
        assert "Advisory Runtime Architecture" in text


# ═══════════════════════════════════════════════════════════════════════
# No runtime implementation added anywhere in the source tree
# ═══════════════════════════════════════════════════════════════════════


def test_no_new_module_added_to_core():
    core_dir = REPO_ROOT / "src" / "pcae" / "core"
    existing = {p.name for p in core_dir.glob("*.py")}
    assert "runtime_snapshot_contract.py" not in existing


def test_runtime_snapshot_module_unchanged_by_this_phase():
    """This phase's task contract must not list src/pcae/core/runtime_snapshot.py
    as allowed -- confirming the freeze-only boundary was respected at
    the governance layer."""
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-112f-runtime-snapshot*"))
    if not matches:
        pytest.skip("112F task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text_ = matches[0].read_text()
    allowed_files_start = contract_text_.index("## Allowed Files")
    allowed_files_end = contract_text_.index("##", allowed_files_start + 1)
    allowed_files_section = contract_text_[allowed_files_start:allowed_files_end]
    assert "src/pcae/" not in allowed_files_section
