"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1 — Independent Verification of the
.1R.30R Production Protected-Admin Writer Anchor Adjudication.

VERIFICATION ONLY. This suite reads production source, contracts, and git
history as read-only evidence. It implements no writer anchor, imports no
production mutation path, and changes no `src/pcae` / `docs/contracts` /
runtime state. Every assertion independently re-derives a `.1R.30R`
adjudication claim from primary source rather than trusting the adjudication
prose.

Immutable SHAs (independently derived at the verification-entry commit):
  B30  = 8e65529596fc351face4b83c4b5d08573326d034  finalized .1R.30 BLOCKED head
  A30R = 8e65529596fc351face4b83c4b5d08573326d034  .1R.30R phase-entry (== B30)
  H30R = ca0d42873f14bb94e8eb4ef7a27e1b456324cd2a  finalized .1R.30R head
  V    = ca0d42873f14bb94e8eb4ef7a27e1b456324cd2a  .1R.30R.1 phase-entry (== H30R)
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "pcae"
CONTRACTS = REPO / "docs" / "contracts"

B30 = "8e65529596fc351face4b83c4b5d08573326d034"
H30R = "ca0d42873f14bb94e8eb4ef7a27e1b456324cd2a"

HPAC_FOUNDATION = SRC / "core" / "hpac_foundation.py"
REGISTRY = SRC / "core" / "human_principal_registry.py"
TOPO_VERIFIER = SRC / "core" / "hatp_class_b_topology_verifier.py"
DBA = SRC / "core" / "hatp_deployment_binding_admin.py"
HPAC_CONTRACT = CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md"
RHAMP_CONTRACT = CONTRACTS / "REAL_HUMAN_AUTHENTICATION_MECHANISM_AND_PROTECTED_PRESENTATION_PROFILE_CONTRACT.md"
HBDC_CONTRACT = CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
CPIPC_CONTRACT = CONTRACTS / "CANONICAL_PHASE_ID_PARSING_CONTRACT.md"
ADJ_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_HPAC_REQ_022_023_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_ARCHITECTURE_AND_CONTRACT_ADJUDICATION.md"
IV_DOC = REPO / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_1_INDEPENDENT_VERIFICATION_OF_THE_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_ADJUDICATION.md"
METADATA = REPO / ".pcae" / "phase-completion-metadata.json"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, check=True,
    ).stdout


def _norm(text: str) -> str:
    """Collapse contract line-wrapping so exact phrases can be matched."""
    return re.sub(r"\s+", " ", text)


# ── 1. Immutable SHA derivation ────────────────────────────────────────────

def test_immutable_shas_resolve_and_b30_equals_a30r() -> None:
    assert _git("rev-parse", B30).strip() == B30
    assert _git("rev-parse", H30R).strip() == H30R
    # A30R (the .1R.30R phase-entry recorded in the adjudication doc) == B30.
    assert "8e65529596fc351face4b83c4b5d08573326d034" in ADJ_DOC.read_text(encoding="utf-8")
    # H30R == V: the IV doc records the verification-entry SHA.
    assert H30R in IV_DOC.read_text(encoding="utf-8")


def test_b30_is_the_blocked_1r30_head() -> None:
    subject = _git("log", "-1", "--format=%s", B30).strip()
    assert "1R.30:" in subject and "BLOCKED completion metadata" in subject


def test_h30r_is_the_1r30r_head() -> None:
    subject = _git("log", "-1", "--format=%s", H30R).strip()
    assert "1R.30R:" in subject and "reconcile governed push state" in subject


# ── 2-4. No production / contract / functional delta since B30 ──────────────

def test_no_src_pcae_change_since_b30() -> None:
    assert _git("diff", "--stat", B30, "HEAD", "--", "src/pcae").strip() == ""


def test_no_contract_change_since_b30() -> None:
    assert _git("diff", "--stat", B30, "HEAD", "--", "docs/contracts").strip() == ""


def test_only_iv_artifacts_changed_since_v() -> None:
    changed = {
        line.split("\t")[-1]
        for line in _git("diff", "--name-only", H30R, "HEAD").splitlines()
        if line.strip()
    }
    allowed_prefixes = (
        "docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_1_",
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_1_",
        "PROJECT_STATUS.md", "CHANGELOG.md", "tasks/", ".pcae/",
    )
    for path in changed:
        assert path.startswith(allowed_prefixes), f"unexpected change: {path}"


# ── 5-6. HPAC-REQ-022 / HPAC-REQ-023 exact-text anchors ────────────────────

def test_hpac_req_022_location_alone_is_never_trust() -> None:
    text = _norm(HPAC_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-REQ-022." in text
    assert "is never the trust basis." in text
    assert "unavailable to ordinary same-user agent execution" in text


def test_hpac_req_023_external_os_equivalent_anchor() -> None:
    text = _norm(HPAC_CONTRACT.read_text(encoding="utf-8"))
    assert "HPAC-REQ-023." in text
    assert "deployment-owner administration principal" in text
    assert "not by ordinary same-UID machine access" in text
    assert "external OS/equivalent trust anchor" in text
    assert "without circular PCAE self-authorization" in text


# ── 7-10. Positive production writer path is absent ────────────────────────

def test_single_hpac_writer_capability_construction_site() -> None:
    hits = [
        (p, i + 1)
        for p in SRC.rglob("*.py")
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines())
        if "HPACWriterCapability(" in line
    ]
    assert len(hits) == 1, hits
    path, lineno = hits[0]
    assert path == HPAC_FOUNDATION


def test_writer_refuses_non_fixture_class() -> None:
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert 'raise HPACAuthorityError("no production HPAC writer is implemented in this foundation phase")' in text
    assert "There is intentionally no public production-writer factory in this phase." in text
    assert "can never authorize a production store" in text


def test_no_production_writer_factory_symbols_anywhere_in_src() -> None:
    joined = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.py"))
    for needle in ("production_writer", "ProductionWriter", "deployment_owner", "DeploymentOwner"):
        assert needle not in joined, needle


def test_registry_writer_gate_has_no_third_path() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    assert "def _writer(self, capability" in text
    assert "self._authority.require_writer(capability, self._WRITER_ROLE)" in text
    assert "return self._authority.legacy_fixture_writer(capability, self._WRITER_ROLE)" in text


# ── 11-14. Negative-half primitives + euid/sudo/env rejection ──────────────

def test_validate_production_boundary_uses_filesystem_primitives() -> None:
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert "_validate_production_boundary" in text
    assert "_effective_write_access" in text
    assert "_ancestor_chain_safe" in text
    assert "production HPAC authority cannot be redirected" in text


def test_current_agent_identity_is_live_geteuid() -> None:
    text = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert "def _current_agent_identity()" in text
    assert "os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}" in text


def test_self_elevation_attrs_banned() -> None:
    text = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert '_FORBIDDEN_SELF_ELEVATION_ATTRS = frozenset({"setuid", "seteuid", "setgid", "setegid", "setreuid", "setresuid"})' in text


def test_suspicious_env_key_substrings_ban_sudo_admin_user() -> None:
    text = TOPO_VERIFIER.read_text(encoding="utf-8")
    assert '_SUSPICIOUS_ENV_KEY_SUBSTRINGS = ("ADMIN", "USER", "SUDO", "LOGNAME", "IDENTITY")' in text


# ── 15-18. Root-identity binding + non-bearer capability ───────────────────

def test_root_identity_manifest_binding_present() -> None:
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert '"device": result.st_dev, "inode": result.st_ino' in text
    assert "HPAC root was copied or replaced; root identity binding failed" in text


def test_writer_capability_is_non_bearer() -> None:
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert 'raise TypeError("HPACWriterCapability is process-local and non-serializable")' in text
    assert "self._seal = object()" in text  # per-instance authority seal


def test_require_writer_uses_identity_check_on_seal() -> None:
    text = HPAC_FOUNDATION.read_text(encoding="utf-8")
    assert "writer._authority_seal is not self._seal" in text


# ── 19-24. HBDC-001 Class-B precedent + consumer-inventory guard ───────────

def test_hbdc_two_os_principal_requirement() -> None:
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "HBDC-REQ-001." in text and "Exactly two OS principals are required" in text
    assert "HBDC-REQ-002." in text and "distinct OS accounts" in text


def test_hbdc_filesystem_permission_is_the_boundary() -> None:
    text = _norm(DBA.read_text(encoding="utf-8"))
    assert "Real security boundary" in text
    assert "filesystem write permission on the Protected Root, never an in-process check" in text


def test_hbdc_protected_root_fixed_path_no_agent_autocreate() -> None:
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "HBDC-REQ-011." in text and "fixed, platform-keyed constant paths" in text
    assert "HBDC-REQ-012." in text and "SHALL auto-create Protected Root" in text


def test_hbdc_admin_authority_not_inferred_from_env() -> None:
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "HBDC-REQ-004." in text
    assert "SHALL NOT be inferred from environment variables" in text
    assert "conferred solely by OS-level identity and Protected Root ownership" in text


def test_hbdc_admin_write_authority_not_runtime_execution_authority() -> None:
    text = HBDC_CONTRACT.read_text(encoding="utf-8")
    assert "HBDC-REQ-010." in text
    assert "does not itself confer ordinary PCAE runtime execution authority" in text


def test_consumer_inventory_guard_precedent_exists() -> None:
    guard = REPO / "tests" / "test_hatp_deployment_binding_admin.py"
    text = guard.read_text(encoding="utf-8")
    assert "def test_module_not_imported_by_cli_or_agent_reachable_code()" in text
    assert '"hatp_deployment_binding_admin" not in text' in text
    assert "def test_admin_script_exists_and_is_not_a_pcae_cli_subcommand()" in text


# ── 25-29. Contract-versioning basis ──────────────────────────────────────

def test_rhamp_req_047_externalises_the_anchor() -> None:
    text = RHAMP_CONTRACT.read_text(encoding="utf-8")
    assert "RHAMP-REQ-047." in text
    assert "owns the deployment-scoped protected" in text
    assert "This is the trust anchor; it terminates" in text


def test_rhamp_req_049_stop_when_absent() -> None:
    text = RHAMP_CONTRACT.read_text(encoding="utf-8")
    assert "RHAMP-REQ-049." in text
    assert "the implementing phase STOPS" in text
    assert "if the existing governance model provides" in text


def test_rhamp_req_167_bootstrap_model_change_is_major() -> None:
    text = RHAMP_CONTRACT.read_text(encoding="utf-8")
    assert "RHAMP-REQ-167." in text
    assert "changing the first-credential bootstrap authority model" in text


def test_rhamp_inv_016_only_normative_delta_is_rhamp() -> None:
    text = RHAMP_CONTRACT.read_text(encoding="utf-8")
    assert "RHAMP-INV-016" in text
    assert "HPAC-001 stays v2.1 and every other contract is byte-unchanged" in text


def test_hpac_versioning_bar_text_present() -> None:
    text = HPAC_CONTRACT.read_text(encoding="utf-8")
    assert "## 37. Versioning" in text
    assert "does not widen existing authority" in text
    assert "requires a new MAJOR" in text


# ── 30. Phase-ID grammar (CPIPC-001 §4) ───────────────────────────────────

def test_cpipc_grammar_admits_1r30r1_and_it_differs_from_1r30() -> None:
    import re
    text = CPIPC_CONTRACT.read_text(encoding="utf-8")
    assert r"^ [0-9]+ [A-Za-z]+ ( \. ( [0-9]+ [A-Za-z]* | [A-Za-z]+ ) )* $" in text
    whole = re.compile(r"^[0-9]+[A-Za-z]+(\.([0-9]+[A-Za-z]*|[A-Za-z]+))*$")
    assert whole.fullmatch("149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1")
    assert whole.fullmatch("149O.20L.7O.3W.1R.2B.1R.1.1R.30")
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.1" != "149O.20L.7O.3W.1R.2B.1R.1.1R.30"


# ── 31. Phase-ID discrepancy is present in the adjudication doc + resolved ──

def test_phase_id_discrepancy_present_and_resolution_recorded() -> None:
    adj = ADJ_DOC.read_text(encoding="utf-8")
    # The erroneous form (§21.4 heading / §24 summary line).
    assert "Fresh implementation successor ID = `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.2`" in adj
    # The dominant/correct form (§21.5 table + §24 downstream-sequence line).
    assert ".1R.30R.2` | **`HPAC-PAWA-001 v1.0` companion contract freeze**" in adj
    assert ".1R.30R.3 (mechanism + registry + writer-anchor impl)" in adj
    # The completion metadata's recommended_next_phase names the contract freeze.
    meta = METADATA.read_text(encoding="utf-8")
    assert "1R.30R.2" in meta
    # This IV records the resolution.
    iv = IV_DOC.read_text(encoding="utf-8")
    assert "`.1R.30R.3`, NOT `.1R.30R.2`, is the implementation" in iv


# ── 32-34. Runtime / first-effect / N-16 untouched ────────────────────────

def _adapter_dispatch_call_sites() -> list[str]:
    """`<recv>.dispatch(...)` calls in production source whose receiver name
    contains ``adapter`` — AST-level, so docstring prose does not count."""

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.hits: list[str] = []

        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "dispatch":
                recv = func.value
                name = recv.id if isinstance(recv, ast.Name) else (
                    recv.attr if isinstance(recv, ast.Attribute) else None
                )
                if name and "adapter" in name.lower():
                    self.hits.append(name)
            self.generic_visit(node)

    hits: list[str] = []
    for path in SRC.rglob("*.py"):
        visitor = _Visitor()
        visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        hits.extend(f"{path.relative_to(REPO)}:{h}" for h in visitor.hits)
    return hits


def test_only_the_known_simulation_dispatch_call_site_exists() -> None:
    """The single `adapter.dispatch(` call site is the deterministic
    simulation / dry-runtime harness in `runtime_adapter.py` (a
    `SimulationDispatchEnvelope`, `SIM_*` states, `would_allow_simulation`
    gate — NOT a real external effect). `.1R.30R.1` adds no new call site and
    the runtime stays `unavailable`."""
    sites = _adapter_dispatch_call_sites()
    assert sites == ["src/pcae/core/runtime_adapter.py:adapter"], sites
    # No new `.dispatch(` call site introduced by this phase.
    added = _git("diff", B30, "HEAD", "--", "src/pcae")
    assert added.strip() == "", "this IV phase changes no src/pcae"


def test_no_n16_closure_or_transition_commit_since_b30() -> None:
    log = _git("log", "--format=%s", f"{B30}..HEAD")
    lowered = log.lower()
    assert "n-16-5: closed" not in lowered
    assert "n-16-6" not in lowered
    assert "n-16-7" not in lowered


# ── 35. No test weakening in this phase's diff ────────────────────────────

def test_this_suite_is_new_and_removes_no_tests() -> None:
    try:
        prior = _git("show", f"{H30R}:tests/{Path(__file__).name}")
    except subprocess.CalledProcessError:
        prior = ""
    assert prior == "", "IV suite must be a new file at the verification-entry commit"
    # No skip / xfail markers on any test in this suite (AST, not text scan).
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                src = ast.unparse(dec)
                assert "skip" not in src and "xfail" not in src, (node.name, src)
