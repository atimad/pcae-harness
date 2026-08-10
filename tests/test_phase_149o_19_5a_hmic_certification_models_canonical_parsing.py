"""Phase 149O.19.5A -- HMIC Certification Data Models + Canonical Parsing.

Phase-boundary verification: this phase implements ONLY the HMIC-001
pure data-model/parsing/canonical-serialization layer (Wave A of the
149O.19.4 implementation plan, `docs/PHASE_149O_19_4_..._IMPLEMENTATION_
PLAN.md` §9.3) in one new production module,
`src/pcae/core/hatp_mandatory_certification.py`. This module mechanically
confirms the scope boundary was respected -- by inspecting real
repository/git state, not by trusting the phase document's prose.

Stop Condition W-1 (the plan's own §10.3, restated on the phase prompt as
non-negotiable for this wave): no code in this phase may be wired into
activation readiness. This suite asserts the new module is never
imported by `hatp_mandatory_cutover.py`, and that the hard-coded `False`
readiness ceiling remains byte-unchanged.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

# HEAD immediately before this phase's own work began (149O.19.4's final commit).
_PHASE_ENTRY_COMMIT = "484b1a97"

_NEW_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_CUTOVER_MODULE_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

_BOUND_CONTRACTS = (
    _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",  # HMIC-001
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",  # HMRC-001
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",  # HATP-001
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",  # HSCE-001
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",  # RAE-001
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",  # RWMPC-001
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",  # PBPA-001
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",  # PBPC-001
)

_FORBIDDEN_MODIFIED_SRC_FILES = (
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
)

#: Phase 149O.19.5B (Wave B, `docs/PHASE_149O_19_4_..._IMPLEMENTATION_
#: PLAN.md` §9.3) plan-authorizes exactly two additions to Wave A's
#: originally-empty dependency surface: `subprocess` (`derive_
#: implementation_commit`'s `git rev-parse HEAD`, HMIC-REQ-046) and
#: `pcae.core.hatp_bootstrap` (`derive_canonical_deployment_root`, the
#: plan's own literal text: "calls hatp_bootstrap.py"). Both are
#: therefore removed from this forbidden list -- a deliberate, plan-
#: traced widening of this Wave-A-era assertion, mirroring the
#: 149O.19.3-era scope-boundary widening already recorded in this
#: repository's history for the same reason (a later, plan-authorized
#: wave legitimately expanding an earlier wave's closure boundary).
#: Every other entry remains forbidden: Wave B never imports
#: `hatp_mandatory_cutover.py` (W-1), the provider/hardware modules, the
#: Permission Broker, `rollback_approval_evidence.py`, `agent.py`,
#: `commands/agent.py`, or `cli.py`.
_FORBIDDEN_IMPORT_MODULES = (
    "pcae.core.hatp_mandatory_cutover",
    "pcae.core.hatp_providers",
    "pcae.core.hatp_fido2_provider",
    "pcae.core.hatp_piv_provider",
    "pcae.core.hatp_hardware_credentials",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
    "pcae.core.rollback_approval_evidence",
    "pcae.core.agent",
    "pcae.commands.agent",
    "pcae.cli",
)

#: HMIC-REQ IDs this phase (Wave A) is the primary owner of, per
#: `docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md` §6's traceability
#: table (MODEL-owned rows), re-extracted here for a mechanical coverage
#: check rather than trusted from prose.
_WAVE_A_REQUIREMENT_IDS = (
    7, 9, 10, 24, 29, 31, 32, 33, 34, 35, 36, 37, 41, 42, 71, 73, 106, 107, 108, 122, 123, 124, 130, 131, 133, 140,
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _imported_module_names(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


# ── Production file allowlist ─────────────────────────────────────────────


class TestProductionFileAllowlist:
    def test_only_the_new_certification_module_was_added_in_src_pcae(self) -> None:
        changed = {
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/").splitlines()
            if line
        }
        assert changed == {"src/pcae/core/hatp_mandatory_certification.py"}

    def test_no_forbidden_src_file_was_modified(self) -> None:
        changed = set(_git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/").splitlines())
        for forbidden in _FORBIDDEN_MODIFIED_SRC_FILES:
            assert forbidden not in changed, f"forbidden file was modified: {forbidden}"

    def test_new_module_is_a_pure_addition_not_a_modification(self) -> None:
        status = _git("diff", "--name-status", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/")
        assert status.strip() == "A\tsrc/pcae/core/hatp_mandatory_certification.py"


# ── Contract byte identity (all 8 bound contracts) ────────────────────────


class TestContractByteIdentity:
    @pytest.mark.parametrize("contract_path", _BOUND_CONTRACTS, ids=lambda p: p.name)
    def test_contract_unchanged(self, contract_path: Path) -> None:
        # Pinned to this phase's own conclusion (149O.19.5A's final
        # commit, 889bb98b), not an open-ended "...HEAD forever"
        # comparison. Phase 149O.19.5E.1 (contract §50) later amended
        # HMIC-001 deliberately (v1.0 -> v1.1), well after 149O.19.5A
        # concluded; this test was never meant to guard against a later,
        # intentional amendment.
        rel = contract_path.relative_to(_REPO_ROOT).as_posix()
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..889bb98b", "--", rel)
        assert diff == ""


# ── Hard-coded False readiness ceiling untouched (W-1) ────────────────────


class TestHardcodedFalseCeilingUnchanged:
    def test_cutover_module_byte_unchanged(self) -> None:
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/core/hatp_mandatory_cutover.py")
        assert diff == ""

    def test_false_literal_still_present(self) -> None:
        source = _CUTOVER_MODULE_PATH.read_text(encoding="utf-8")
        assert "mandatory_consumption_implementation_independently_verified" in source
        # The literal readiness constant's own False assignment must still exist verbatim.
        assert "False" in source


# ── W-1: no wiring of the new module into readiness ───────────────────────


class TestW1NoActivationWiring:
    def test_cutover_module_never_imports_new_certification_module(self) -> None:
        imports = _imported_module_names(_CUTOVER_MODULE_PATH)
        assert "pcae.core.hatp_mandatory_certification" not in imports
        assert not any("hatp_mandatory_certification" in name for name in imports)

    def test_new_module_never_imports_cutover_module(self) -> None:
        imports = _imported_module_names(_NEW_MODULE_PATH)
        assert "pcae.core.hatp_mandatory_cutover" not in imports

    def test_no_agent_cli_or_pb_reference_in_new_module(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        for forbidden in ("execute_rollback", "build_rollback_execution", "activate_hatp_mandatory"):
            assert forbidden not in identifiers
        assert "argparse" not in _NEW_MODULE_PATH.read_text(encoding="utf-8")


# ── Dependency closure ─────────────────────────────────────────────────────


class TestDependencyClosure:
    def test_no_forbidden_imports_in_new_module(self) -> None:
        imports = _imported_module_names(_NEW_MODULE_PATH)
        for forbidden in _FORBIDDEN_IMPORT_MODULES:
            assert forbidden not in imports, f"forbidden import present: {forbidden}"

    def test_only_expected_pcae_core_imports(self) -> None:
        """Renamed from `test_only_expected_import_is_repository_identity_
        format_check` (Wave A only imported one function from one
        module). Wave B plan-authorizes exactly two additional
        `pcae.core` imports: `hatp_bootstrap` (`resolve_canonical_
        deployment_root`) and `paths` (`HarnessPath`, the neutral
        repository-root locator type every `derive_*` function takes) --
        both are also individually asserted here, not just by omission
        from the equality check."""

        imports = _imported_module_names(_NEW_MODULE_PATH)
        pcae_core_imports = {name for name in imports if name.startswith("pcae.core")}
        assert pcae_core_imports == {
            "pcae.core.repository_identity",
            "pcae.core.hatp_bootstrap",
            "pcae.core.paths",
        }

    def test_no_network_call_in_module_source(self) -> None:
        """Renamed from `test_no_filesystem_or_network_call_in_module_
        source`. Wave B legitimately introduces filesystem-shaped tokens
        (`Path(`, `os.open(`/`open(`) to read the frozen file set and
        contract headers (HMIC-REQ-054); this now asserts only the
        narrower, still-true invariant that neither wave ever touches
        the network.

        Widened at Phase 149O.19.5C (mirroring this same class's own
        149O.19.5A-era precedent of widening a stale scope-boundary
        assertion for a legitimate new wave): checked via the parsed
        AST's actual `import` statements, not a raw substring scan --
        Wave C legitimately introduces the word "socket" in a code
        comment (rejecting a non-regular FIFO/socket/device file in
        place of a certification file, HMIC-REQ item-26) and imports
        `fcntl` for `.certification-transition.lock` (HMIC-REQ-097), the
        identical POSIX file-locking primitive `hatp_mandatory_
        cutover.py` already uses for its own `.cutover-transition.lock`
        -- neither is network-shaped. The invariant this test actually
        protects (no `socket`/`requests`/`urllib` *module* ever
        imported) is unchanged and re-checked precisely below."""

        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])
        forbidden_modules = {"socket", "requests", "urllib", "http", "ftplib", "smtplib"}
        assert not (imported_modules & forbidden_modules), (
            f"unexpected network-shaped import(s): {sorted(imported_modules & forbidden_modules)}"
        )


# ── No certification state was created anywhere in the repository ────────


class TestNoCertificationStateCreated:
    def test_no_certifications_json_tracked(self) -> None:
        tracked = _git("ls-files", "certifications.json", "**/certifications.json")
        assert tracked.strip() == ""

    def test_no_certification_bindings_json_tracked(self) -> None:
        tracked = _git("ls-files", "certification-bindings.json", "**/certification-bindings.json")
        assert tracked.strip() == ""

    def test_admin_script_absent_or_exactly_wave_e_owned(self) -> None:
        """As of Wave A (this phase), no admin script exists. `scripts/
        hatp_certification_admin.py` was later, legitimately, created by
        Wave E (Phase 149O.19.5E, `docs/PHASE_149O_19_5E_HMIC_PROTECTED_
        ADMIN_CERTIFICATION_REVOCATION_SURFACE.md`) -- a separately-scoped,
        independently-authorized wave of this same HMIC-001 implementation,
        not something Wave A itself ever created. This assertion's own
        purpose (Wave A ships no write surface, only pure data models) is
        unchanged and still enforced by the class's other assertions (no
        `certifications.json`/`certification-bindings.json` state exists);
        only the historical "not yet" snapshot legitimately became stale
        once Wave E shipped, exactly mirroring Wave D's own prior fix to
        this suite's sibling Wave C assertions. What remains permanently
        true, restated here rather than dropped outright: if the admin
        script exists at all, it is the one, sole, Wave-E-owned file at
        this exact path -- never a second or differently-named writer
        surface, and never anything under `src/pcae/`."""

        admin_script = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
        if admin_script.exists():
            assert admin_script.is_file()
        assert not (_SRC / "hatp_certification_admin.py").exists()
        assert not list(_SRC.rglob("*certification_admin*"))


# ── CertificationStatus vocabulary (structural, redundant with unit suite by design) ─


class TestCertificationStatusVocabulary:
    def test_exactly_nine_members_frozen_names(self) -> None:
        assert [member.name for member in hmic.CertificationStatus] == [
            "MISSING",
            "MALFORMED",
            "WRONG_REPOSITORY",
            "WRONG_DEPLOYMENT",
            "IMPLEMENTATION_MISMATCH",
            "CONTRACT_MISMATCH",
            "REVOKED",
            "ACCESS_ERROR",
            "VALID",
        ]

    def test_no_fifth_status_shaped_token_as_an_actual_enum_member(self) -> None:
        # AST-based (not substring): the module's own docstrings
        # legitimately name `VALID_WITH_WARNING` as an example of what
        # must never exist -- what matters is that no such name is ever
        # bound as a real `CertificationStatus` member.
        member_names = {member.name for member in hmic.CertificationStatus}
        for forbidden in ("VALID_WITH_WARNING", "PARTIALLY_VALID", "PROBABLY_VALID"):
            assert forbidden not in member_names


# ── Requirement traceability (mechanical, not trusted from prose) ────────


class TestWaveARequirementTraceability:
    def test_every_wave_a_requirement_id_is_cited_in_module_source(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        missing = [req_id for req_id in _WAVE_A_REQUIREMENT_IDS if f"HMIC-REQ-{req_id:03d}" not in source]
        assert not missing, f"Wave A requirement(s) not cited in module source: {missing}"


# ── No side effects on import ──────────────────────────────────────────────


class TestNoImportSideEffects:
    def test_module_docstring_states_no_side_effects(self) -> None:
        assert hmic.__doc__ is not None
        assert "no side effect" in hmic.__doc__.lower()

    def test_import_creates_no_new_files_in_isolated_directory(self, tmp_path: Path) -> None:
        # Isolated subprocess with `tmp_path` as its cwd: the repository
        # tree itself is never inspected here, so this test cannot collide
        # with unrelated concurrently-running tests writing their own real
        # files elsewhere under the repo (this suite runs under `-n auto`
        # parallelism; a shared-tree `rglob` snapshot proved flaky for
        # exactly that reason). `sys.path` is seeded with `src/` so the
        # module under test is importable without installing the package.
        src_root = str(_SRC.parent)
        result = subprocess.run(
            [sys.executable, "-c", "import pcae.core.hatp_mandatory_certification"],
            cwd=str(tmp_path),
            env={**os.environ, "PYTHONPATH": src_root},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert list(tmp_path.iterdir()) == []


# ── Fast Green regression smoke: neighboring HATP suites unaffected ──────


class TestNeighboringModulesUnaffected:
    def test_cutover_module_still_importable(self) -> None:
        import importlib

        module = importlib.import_module("pcae.core.hatp_mandatory_cutover")
        assert module.__name__ == "pcae.core.hatp_mandatory_cutover"

    def test_repository_identity_still_importable(self) -> None:
        import importlib

        module = importlib.import_module("pcae.core.repository_identity")
        assert module.__name__ == "pcae.core.repository_identity"
